"""SRR (Split Ring Resonator) 工具
基于 scripts/SRR.py 的 LangChain 工具实现
与CSRR不同：SRR为金属开口双环结构，不需要在接地板上进行刻蚀减法布尔运算
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from ansys.aedt.core import Hfss
from ansys.aedt.core import constants


class SRREntryParams(BaseModel):
    """SRR结构输入参数"""
    # 必需参数
    outer_radius: float = Field(
        description="外环外半径 (mm)",
        gt=0
    )
    ring_width: float = Field(
        description="环宽度 (mm)", 
        gt=0
    )
    gap_width: float = Field(
        description="开口宽度 (mm)",
        gt=0
    )
    ring_spacing: float = Field(
        description="内外环间距 (mm)",
        gt=0
    )
    microstrip_width: float = Field(
        description="微带线宽度 (mm)",
        gt=0
    )
    
    # 可选参数（使用默认值）
    substrate_length: float = Field(
        default=40.0,
        description="基板长度 (mm)",
        gt=0
    )
    substrate_width: float = Field(
        default=25.0,
        description="基板宽度 (mm)",
        gt=0
    )
    substrate_thickness: float = Field(
        default=0.8,
        description="基板厚度 (mm)",
        gt=0
    )
    substrate_material: str = Field(
        default="FR4_epoxy",
        description="基板材料"
    )
    metal_material: str = Field(
        default="copper",
        description="金属材料"
    )
    metal_thickness: float = Field(
        default=0.035,
        description="铜层厚度 (mm)",
        gt=0
    )


class BuildSRROptions(BaseModel):
    """SRR构建选项"""
    project_name: Optional[str] = Field(
        default=None,
        description="项目名称，如果为None则自动生成"
    )
    design_name: Optional[str] = Field(
        default=None,
        description="设计名称，如果为None则自动生成"
    )
    aedt_version: str = Field(
        default="2024.2",
        description="AEDT版本"
    )
    non_graphical: bool = Field(
        default=False,
        description="是否以非图形模式运行"
    )
    new_desktop: bool = Field(
        default=False,
        description="是否创建新的桌面会话"
    )
    save_project: bool = Field(
        default=True,
        description="是否保存项目"
    )


def build_srr_project(params: SRREntryParams, options: BuildSRROptions = None) -> dict:
    """构建SRR HFSS项目
    
    Args:
        params: SRR结构参数
        options: 构建选项
        
    Returns:
        包含项目信息的字典
    """
    if options is None:
        options = BuildSRROptions()
    
    try:
        # 生成项目和设计名称
        current_time = datetime.now()
        project_name = options.project_name or f"SRR_Project_{current_time.strftime('%Y%m%d_%H%M%S')}"
        design_name = options.design_name or f"SRR_Design_{current_time.strftime('%Y%m%d_%H%M%S')}"
        
        print(f"创建项目: {project_name}")
        print(f"创建设计: {design_name}")
        
        # 创建HFSS应用实例
        hfss = Hfss(
            project=project_name,
            design=design_name,
            version=options.aedt_version,
            non_graphical=options.non_graphical,
            new_desktop=options.new_desktop,
        )
        
        # ==============================================================================
        # 定义参数化变量（SRR为金属双环，不再在地平面上刻蚀）
        # ==============================================================================
        
        # 基板参数
        hfss["Sub_L"] = f"{params.substrate_length}mm"       # 基板长度
        hfss["Sub_W"] = f"{params.substrate_width}mm"        # 基板宽度
        hfss["Sub_H"] = f"{params.substrate_thickness}mm"    # 基板厚度
        
        # SRR结构参数
        hfss["R_out"] = f"{params.outer_radius}mm"           # 外环外半径
        hfss["Ring_W"] = f"{params.ring_width}mm"            # 环宽度
        hfss["Gap_W"] = f"{params.gap_width}mm"              # 开口宽度
        hfss["S"] = f"{params.ring_spacing}mm"               # 内外环间距
        hfss["R_in"] = "R_out - Ring_W - S"                  # 内环外半径
        hfss["t"] = f"{params.metal_thickness}mm"            # 铜层厚度
        
        # 微带线参数
        hfss["MS_W"] = f"{params.microstrip_width}mm"        # 微带线宽度
        hfss["MS_L"] = "Sub_L"                               # 微带线长度（基板长度）
        
        # 空气盒子参数（基于波长设计）
        hfss["AirBox_L"] = "MS_L"                            # 空气盒长度：微带线长度
        hfss["AirBox_W"] = "MS_W + 360mm"                    # 空气盒宽度：微带线宽度 + 360mm
        hfss["AirBox_H"] = "Sub_H + 125mm"                   # 空气盒高度：基板厚度 + λ
        
        print("参数化变量定义完成")
        
        # ==============================================================================
        # 第一步：创建介质基板 (Substrate)
        # ==============================================================================
        
        print("\n开始创建介质基板...")
        substrate = hfss.modeler.create_box(
            origin=["-Sub_L/2", "-Sub_W/2", "0mm"],
            sizes=["Sub_L", "Sub_W", "Sub_H"],
            name="Substrate",
            material=params.substrate_material,
        )
        print("介质基板创建完成")
        
        # ==============================================================================
        # 第二步：创建微带线 (Microstrip Line)
        # ==============================================================================
        
        print("\n开始创建微带线...")
        
        # 创建微带线实体（薄铜层）
        # 位于基板底面（-z面），沿x方向居中放置
        microstrip_line = hfss.modeler.create_box(
            origin=["-MS_L/2", "-MS_W/2", "-t"],  # 起始点：微带线居中，位于基板底面下方
            sizes=["MS_L", "MS_W", "t"],           # 尺寸：长度、宽度、厚度
            name="Microstrip_Line",
            material=params.metal_material
        )
        
        print("微带线创建完成")
        
        # ==============================================================================
        # 第三步：创建SRR金属环（位于基板上表面）
        # ==============================================================================
        
        print("\n开始创建SRR金属开口双环...")
        
        # 2.1 外层圆环（铜）
        print("  创建外层圆环...")
        outer_cylinder_large = hfss.modeler.create_cylinder(
            origin=["0mm", "0mm", "Sub_H"],
            radius="R_out",
            height="t",
            name="SRR_Outer_Large",
            orientation="Z",
            material=params.metal_material,
        )
        outer_cylinder_small = hfss.modeler.create_cylinder(
            origin=["0mm", "0mm", "Sub_H"],
            radius="R_out - Ring_W",
            height="t",
            name="SRR_Outer_Small",
            orientation="Z",
        )
        # 减去内部小圆柱得到环形金属
        hfss.modeler.subtract([
            outer_cylinder_large
        ], [
            outer_cylinder_small
        ], keep_originals=False)
        outer_ring = outer_cylinder_large
        
        # 2.2 外环开口（+X方向），使用长方体切割
        print("  为外环创建开口...")
        # 考虑到弧度，修正切口盒子的尺寸和位置
        outer_gap_box = hfss.modeler.create_box(
            origin=["R_out - (Ring_W+(R_out-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_out-Ring_W)))))", "-Gap_W/2", "Sub_H"],
            sizes=["Ring_W+(R_out-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_out-Ring_W))))", "Gap_W", "t"],
            name="SRR_Outer_Gap",
        )
        hfss.modeler.subtract([outer_ring], [outer_gap_box], keep_originals=False)
        
        # 2.3 内层圆环（铜）
        print("  创建内层圆环...")
        inner_cylinder_large = hfss.modeler.create_cylinder(
            origin=["0mm", "0mm", "Sub_H"],
            radius="R_in",
            height="t",
            name="SRR_Inner_Large",
            orientation="Z",
            material=params.metal_material,
        )
        inner_cylinder_small = hfss.modeler.create_cylinder(
            origin=["0mm", "0mm", "Sub_H"],
            radius="R_in - Ring_W",
            height="t",
            name="SRR_Inner_Small",
            orientation="Z",
        )
        # 减去内部小圆柱得到环形金属
        hfss.modeler.subtract([
            inner_cylinder_large
        ], [
            inner_cylinder_small
        ], keep_originals=False)
        inner_ring = inner_cylinder_large
        
        # 2.4 内环开口（-X方向），使用长方体切割
        print("  为内环创建开口...")
        # 考虑到弧度，修正切口盒子的尺寸和位置
        inner_gap_box = hfss.modeler.create_box(
            origin=["-R_in", "-Gap_W/2", "Sub_H"],
            sizes=["Ring_W+(R_in-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_in-Ring_W))))", "Gap_W", "t"],
            name="SRR_Inner_Gap",
        )
        hfss.modeler.subtract([inner_ring], [inner_gap_box], keep_originals=False)
        
        print("SRR金属双环创建完成")
        
        # 注意：与CSRR不同，这里不再对接地板进行布尔相减；SRR本身即为金属结构。
        
        # ==============================================================================
        # 第四步：创建波端口（微带线端口）
        # ==============================================================================
        
        print("\n创建微带线波端口...")
        
        # 创建端口1 - 位于微带线左端（-X方向）
        port_face_1 = hfss.modeler.create_rectangle(
            orientation=constants.Plane.YZ,  # 法向量沿X轴
            origin=["-MS_L/2", "-0.5*max(11*MS_W, 6*Sub_H+MS_W)", "Sub_H+t"],  # 位于微带线左端
            sizes=["max(11*MS_W, 6*Sub_H+MS_W)", "-8*Sub_H"],            # 宽度=Max(11*MS_W, 6*Sub_H+MS_W)，高度=8*Sub_H
            name="Port_Face_1",
        )
        
        # 创建端口2 - 位于微带线右端（+X方向）
        port_face_2 = hfss.modeler.create_rectangle(
            orientation=constants.Plane.YZ,  # 法向量沿X轴
            origin=["MS_L/2", "-0.5*max(11*MS_W, 6*Sub_H+MS_W)", "Sub_H+t"],   # 位于微带线右端
            sizes=["max(11*MS_W, 6*Sub_H+MS_W)", "-8*Sub_H"],            # 宽度=Max(11*MS_W, 6*Sub_H+MS_W)，高度=8*Sub_H
            name="Port_Face_2",
        )
        
        # 创建积分线1/2：改用方向枚举，避免坐标表达式解析导致零长度
        integration_line_1 = hfss.AxisDir.ZPos  # 沿Z轴方向（自下而上）
        
        integration_line_2 = hfss.AxisDir.ZPos  # 沿Z轴方向（自下而上）
        
        # 分配波端口1
        try:
            wave_port_1 = hfss.wave_port(
                assignment=port_face_1,
                name="WavePort1",
                impedance=50,  # 50欧姆阻抗
                modes=1,       # 模式数量
                is_microstrip=True,  # 微带线端口
                integration_line=integration_line_1  # 自定义积分线
            )
            print("  波端口1创建完成（含自定义积分线）")
        except Exception as e:
            print(f"  波端口1创建失败: {e}")
        
        # 分配波端口2
        try:
            wave_port_2 = hfss.wave_port(
                assignment=port_face_2,
                name="WavePort2",
                impedance=50,  # 50欧姆阻抗
                modes=1,       # 模式数量
                is_microstrip=True,  # 微带线端口
                integration_line=integration_line_2  # 自定义积分线
            )
            print("  波端口2创建完成（含自定义积分线）")
        except Exception as e:
            print(f"  波端口2创建失败: {e}")
        
        print("微带线波端口创建完成")
        
        # ==============================================================================
        # 第五步：设置仿真环境（空气盒 + 辐射边界）
        # ==============================================================================
        
        print("\n开始设置仿真环境...")
        
        # 3.1 创建空气盒
        print("  创建空气盒子...")
        airbox = hfss.modeler.create_box(
            origin=["-AirBox_L/2", "-AirBox_W/2", "-AirBox_H/2"],
            sizes=["AirBox_L", "AirBox_W", "AirBox_H"],
            name="AirBox",
            material="air",
        )
        print("  空气盒子创建完成")
        
        # 3.2 设置辐射边界（整盒指定即可）
        print("  设置辐射边界...")
        radiation_boundary = hfss.assign_radiation_boundary_to_objects(
            assignment="AirBox",
            name="Radiation_Boundary",
        )
        print("  辐射边界设置完成")
        
        # ==============================================================================
        # 保存项目
        # ==============================================================================
        
        if options.save_project:
            print("\n正在保存项目...")
            hfss.save_project()
            print(f"项目已保存: {hfss.project_file}")
        
        print("\nSRR结构建模完成！")
        
        return {
            "success": True,
            "message": "SRR project created successfully",
            "project_file": hfss.project_file if options.save_project else None,
            "project_name": project_name,
            "design_name": design_name,
            "params": params.model_dump(),
        }
        
    except Exception as e:
        error_msg = f"SRR项目创建失败: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "message": f"SRR project creation failed: {str(e)}",
            "project_file": None,
            "project_name": project_name if 'project_name' in locals() else None,
            "design_name": design_name if 'design_name' in locals() else None,
            "params": params.model_dump() if 'params' in locals() else None,
            "error": str(e)
        }


class CreateSRRTool(BaseTool):
    """创建SRR结构的LangChain工具"""
    
    name: str = "CREATE_SRR"
    description: str = """该函数用于使用 PyAEDT 工具直接在 Ansys HFSS 中创建一个 **SRR (Split-Ring Resonator) 结构**。
    SRR 是一种用于微波和无线通信系统的常见电磁元件，通常用于设计传感器、滤波器等。
    
    **功能描述**：
    1. 根据输入参数，自动在 HFSS 中创建一个符合指定尺寸的 SRR 结构。
    2. 支持环的外径、环宽、开口宽度、环间隙和微带线的宽度等重要设计参数。
    3. 自动生成相应的空气盒和辐射边界，并在微带线两端添加波端口。
    4. 可以指定基板材质（如 FR4_epoxy），自动进行材料分配。
    
    **结构特点**：
    SRR为金属开口双环结构，不需要在接地板上进行刻蚀减法布尔运算。
    本工具直接在基板上方生成两个开口金属环（铜），作为独立金属谐振体。
    
    **必需参数**：
    - outer_radius: 外环外半径 (mm)
    - ring_width: 环宽度 (mm) 
    - gap_width: 开口宽度 (mm)
    - ring_spacing: 内外环间距 (mm)
    - microstrip_width: 微带线宽度 (mm)
    
    **可选参数（有默认值）**：
    - substrate_length: 基板长度 (mm，默认40)
    - substrate_width: 基板宽度 (mm，默认25)
    - substrate_thickness: 基板厚度 (mm，默认0.8)
    - substrate_material: 基板材料（默认FR4_epoxy）
    - metal_material: 金属材料（默认copper）
    - metal_thickness: 铜层厚度 (mm，默认0.035)
    """
    
    def _run(self, **kwargs) -> str:
        """执行SRR创建"""
        try:
            # 处理LangChain传递的嵌套kwargs结构
            if 'kwargs' in kwargs:
                actual_kwargs = kwargs['kwargs']
            else:
                actual_kwargs = kwargs
            
            # 解析参数
            params = SRREntryParams(**actual_kwargs)
            options = BuildSRROptions()
            
            # 构建项目
            result = build_srr_project(params, options)
            
            if result["success"]:
                return f"""SRR项目创建成功！
项目名称: {result['project_name']}
设计名称: {result['design_name']}
项目文件: {result.get('project_file', 'N/A')}"""
            else:
                return f"SRR项目创建失败: {result['error']}"
                
        except Exception as e:
            return f"参数解析或执行错误: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """异步执行（调用同步方法）"""
        return self._run(**kwargs)


# 创建工具实例
CREATE_SRR = CreateSRRTool()


if __name__ == "__main__":
    # 测试代码
    test_params = SRREntryParams(
        outer_radius=5.0,
        ring_width=0.8,
        gap_width=0.3,
        ring_spacing=1.0,
        microstrip_width=1.8
    )
    
    result = build_srr_project(test_params)
    print(result)