from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool, BaseTool
from datetime import datetime
from ansys.aedt.core import Hfss
from ansys.aedt.core import constants

# ---------- 参数 Schema ----------
class CSRREntryParams(BaseModel):
    """CSRR结构输入参数"""
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


class BuildCSRROptions(BaseModel):
    """CSRR构建选项"""
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

# ---------- 功能实现 ----------
def build_csrr_project(params: CSRREntryParams, options: BuildCSRROptions = None) -> Dict[str, Any]:
    """构建CSRR项目
    
    严格按照scripts/CSRR.py的实现方式和流程
    """
    if options is None:
        options = BuildCSRROptions()
    
    # 生成项目和设计名称
    current_time = datetime.now()
    if options.project_name is None:
        project_name = f"CSRR_Project_{current_time.strftime('%Y%m%d_%H%M%S')}"
    else:
        project_name = options.project_name
        
    if options.design_name is None:
        design_name = f"CSRR_Design_{current_time.strftime('%Y%m%d_%H%M%S')}"
    else:
        design_name = options.design_name
    
    # 创建HFSS应用实例
    hfss = Hfss(
        project=project_name,
        design=design_name,
        version=options.aedt_version,
        non_graphical=options.non_graphical,
        new_desktop=False,
    )
    
    try:
        print(f"创建项目: {project_name}")
        print(f"创建设计: {design_name}")
        
        # ==============================================================================
        # 定义参数化变量（严格按照原脚本）
        # ==============================================================================
        
        # 基板参数
        hfss["Sub_L"] = f"{params.substrate_length}mm"        # 基板长度
        hfss["Sub_W"] = f"{params.substrate_width}mm"        # 基板宽度
        hfss["Sub_H"] = f"{params.substrate_thickness}mm"    # 基板厚度
        
        # CSRR结构参数
        hfss["R_out"] = f"{params.outer_radius}mm"            # 外环外半径
        hfss["Ring_W"] = f"{params.ring_width}mm"      # 环宽度
        hfss["Gap_W"] = f"{params.gap_width}mm"        # 开口宽度
        hfss["S"] = f"{params.ring_spacing}mm"              # 内外环间距
        hfss["R_in"] = "R_out - Ring_W - S"          # 内环外半径（通过表达式定义）
        hfss["Etch_H"] = "Sub_H/10"                  # 刻蚀高度（仅用于布尔运算）
        hfss["t"] = f"{params.metal_thickness}mm"      # 铜层厚度
        
        # 微带线参数
        hfss["MS_W"] = f"{params.microstrip_width}mm"          # 微带线宽度
        hfss["MS_L"] = "Sub_L"                       # 微带线长度（基板长度）
        
        # 空气盒子参数（基于波长设计）
        hfss["AirBox_L"] = "MS_L"                    # 空气盒长度：微带线长度
        hfss["AirBox_W"] = "MS_W + 360mm"            # 空气盒宽度：微带线宽度 + 360mm
        hfss["AirBox_H"] = "Sub_H + 125mm"           # 空气盒高度：基板厚度 + λ
        
        print("参数化变量定义完成")
        
        # ==============================================================================
        # 第一步：创建介质基板 (Substrate)
        # ==============================================================================
        
        print("\n开始创建介质基板...")
        
        # 创建基板长方体
        substrate = hfss.modeler.create_box(
            origin=["-Sub_L/2", "-Sub_W/2", "0mm"],
            sizes=["Sub_L", "Sub_W", "Sub_H"],
            name="Substrate",
            material=params.substrate_material
        )
        
        print("介质基板创建完成")
        
        # ==============================================================================
        # 第二步：创建接地板 (Ground Plane) - 作为实体铜层
        # ==============================================================================
        
        print("\n开始创建接地板...")
        
        # 创建接地板实体（薄铜层）
        ground_plane = hfss.modeler.create_box(
            origin=["-Sub_L/2", "-Sub_W/2", "Sub_H"],
            sizes=["Sub_L", "Sub_W", "t"],
            name="GND_Solid",
            material=params.metal_material
        )
        
        print("接地板实体创建完成")
        
        # ==============================================================================
        # 第三步：创建微带线 (Microstrip Line)
        # ==============================================================================
        
        print("\n开始创建微带线...")
        
        # 创建微带线实体（薄铜层）
        microstrip_line = hfss.modeler.create_box(
            origin=["-MS_L/2", "-MS_W/2", "-t"],  # 起始点：微带线居中，位于基板底面下方
            sizes=["MS_L", "MS_W", "t"],           # 尺寸：长度、宽度、厚度
            name="Microstrip_Line",
            material=params.metal_material
        )
        
        print("微带线创建完成")
        
        # ==============================================================================
        # 第四步：创建CSRR刻蚀图案
        # ==============================================================================
        
        print("\n开始创建CSRR刻蚀图案...")
        
        # 4.1 创建外层圆环
        print("  创建外层圆环...")
        
        # 创建外层大圆柱
        outer_cylinder_large = hfss.modeler.create_cylinder(
            origin=["0mm", "0mm", "Sub_H"],
            radius="R_out",
            height="Etch_H",
            name="OuterCyl_Large",
            orientation="Z"
        )
        
        # 创建外层小圆柱
        outer_cylinder_small = hfss.modeler.create_cylinder(
            origin=["0mm", "0mm", "Sub_H"],
            radius="R_out - Ring_W",
            height="Etch_H",
            name="OuterCyl_Small",
            orientation="Z"
        )
        
        # 布尔运算：大圆柱减去小圆柱得到环形
        hfss.modeler.subtract(
            blank_list=[outer_cylinder_large],
            tool_list=[outer_cylinder_small],
            keep_originals=False  # 不保留原始对象，只保留布尔运算结果
        )
        
        outer_ring = outer_cylinder_large
        
        print("  外层圆环基础形状完成")
        
        # 4.2 创建外层圆环开口
        print("  创建外层圆环开口...")
        
        # 创建开口矩形盒子（精确计算位置和尺寸）
        outer_gap_box = hfss.modeler.create_box(
            origin=["R_out - (Ring_W+(R_out-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_out-Ring_W)))))", "-Gap_W/2", "Sub_H"],
            sizes=["Ring_W+(R_out-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_out-Ring_W))))", "Gap_W", "Etch_H"],
            name="OuterGapBox"
        )
        
        # 从外环中减去开口盒子
        hfss.modeler.subtract(
            blank_list=[outer_ring],
            tool_list=[outer_gap_box],
            keep_originals=False
        )
        
        outer_ring_split = outer_ring
        
        print("  外层开口圆环创建完成")
        
        # 4.3 创建内层圆环
        print("  创建内层圆环...")
        
        # 创建内层大圆柱
        inner_cylinder_large = hfss.modeler.create_cylinder(
            origin=["0mm", "0mm", "Sub_H"],
            radius="R_in",
            height="Etch_H",
            name="InnerCyl_Large",
            orientation="Z"
        )
        
        # 创建内层小圆柱
        inner_cylinder_small = hfss.modeler.create_cylinder(
            origin=["0mm", "0mm", "Sub_H"],
            radius="R_in - Ring_W",
            height="Etch_H",
            name="InnerCyl_Small",
            orientation="Z"
        )
        
        # 布尔运算：大圆柱减去小圆柱得到环形
        hfss.modeler.subtract(
            blank_list=[inner_cylinder_large],
            tool_list=[inner_cylinder_small],
            keep_originals=False
        )
        
        inner_ring = inner_cylinder_large
        
        print("  内层圆环基础形状完成")
        
        # 4.4 创建内层圆环开口
        print("  创建内层圆环开口...")
        
        # 创建内层开口矩形盒子（精确计算位置和尺寸）
        inner_gap_box = hfss.modeler.create_box(
            origin=["-R_in", "-Gap_W/2", "Sub_H"],
            sizes=["Ring_W+(R_in-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_in-Ring_W))))", "Gap_W", "Etch_H"],
            name="InnerGapBox"
        )
        
        # 从内环中减去开口盒子
        hfss.modeler.subtract(
            blank_list=[inner_ring],
            tool_list=[inner_gap_box],
            keep_originals=False
        )
        
        inner_ring_split = inner_ring
        
        print("  内层开口圆环创建完成")
        
        # ==============================================================================
        # 第五步：合并CSRR结构并从接地板刻蚀
        # ==============================================================================
        
        print("\n开始合并CSRR结构...")
        
        # 5.1 合并内外环
        print("  合并内外环...")
        
        # 合并内外环为一个整体
        if outer_ring_split and inner_ring_split:
            hfss.modeler.unite(
                assignment=[outer_ring_split, inner_ring_split],
                keep_originals=False
            )
            
            csrr_pattern = outer_ring_split
            print("  内外环合并完成")
        else:
            print("  警告：无法找到内外环对象，请检查对象引用")
        
        # 5.2 从接地板刻蚀CSRR图案
        print("  从接地板刻蚀CSRR图案...")
        
        # 查找合并后的CSRR图案对象名称
        csrr_pattern_name = None
        for obj_name in hfss.modeler.object_names:
            if "OuterCyl_Large" in obj_name:  # 合并后通常保留第一个对象的名称
                csrr_pattern_name = obj_name
                break
        
        # 从接地板中减去CSRR图案
        if csrr_pattern_name:
            final_ground = hfss.modeler.subtract(
                blank_list=["GND_Solid"],
                tool_list=[csrr_pattern_name],
                keep_originals=False
            )
            print("  CSRR结构刻蚀完成")
        else:
            print("  警告：无法找到CSRR图案对象")
        
        # ==============================================================================
        # 第六步：设置仿真环境
        # ==============================================================================
        
        print("\n开始设置仿真环境...")
        
        # 6.1 创建空气盒子
        print("  创建空气盒子...")
        
        # 创建空气盒子
        airbox = hfss.modeler.create_box(
            origin=["-AirBox_L/2", "-AirBox_W/2", "-AirBox_H/2"],
            sizes=["AirBox_L", "AirBox_W", "AirBox_H"],
            name="AirBox",
            material="air"
        )
        
        print("  空气盒子创建完成")
        
        # 6.2 设置辐射边界
        print("  设置辐射边界...")
        
        # 获取空气盒子的所有面
        airbox_faces = hfss.modeler.get_object_faces("AirBox")
        
        # 设置辐射边界
        radiation_boundary = hfss.assign_radiation_boundary_to_objects(
            assignment="AirBox",
            name="Radiation_Boundary"
        )
        
        print("  辐射边界设置完成")
        
        # ==============================================================================
        # 第七步：创建微带线波端口
        # ==============================================================================
        
        print("\n创建微带线波端口...")
        
        # 创建端口面1（微带线左端）
        port_face_1 = hfss.modeler.create_rectangle(
            orientation=constants.Plane.YZ,  # 法向量沿X轴
            origin=["-MS_L/2", "-0.5*max(11*MS_W, 6*Sub_H+MS_W)", "Sub_H+t"],  # 位于微带线左端
            sizes=["max(11*MS_W, 6*Sub_H+MS_W)", "-8*Sub_H"],            # 宽度=Max(11*MS_W, 6*Sub_H+MS_W)，高度=8*Sub_H
            name="Port_Face_1",
        )
        
        # 创建端口面2（微带线右端）
        port_face_2 = hfss.modeler.create_rectangle(
            orientation=constants.Plane.YZ,  # 法向量沿X轴
            origin=["MS_L/2", "-0.5*max(11*MS_W, 6*Sub_H+MS_W)", "Sub_H+t"],   # 位于微带线右端
            sizes=["max(11*MS_W, 6*Sub_H+MS_W)", "-8*Sub_H"],            # 宽度=Max(11*MS_W, 6*Sub_H+MS_W)，高度=8*Sub_H
            name="Port_Face_2",
        )
        
        # 定义积分线方向
        integration_line_1 = hfss.AxisDir.ZPos  # 沿Z轴方向（自下而上）
        
        integration_line_2 = hfss.AxisDir.ZPos  # 沿Z轴方向（自下而上）
        
        # 创建波端口1
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
        
        # 创建波端口2
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
        
        # ==============================================================================
        # 第八步：保存项目
        # ==============================================================================
        
        print(f"\n正在保存项目...")
        hfss.save_project()
        print(f"项目已保存: {hfss.project_file}")
        
        print("\nCSRR结构建模完成！")
        
        # 返回结果
        return {
            "success": True,
            "message": "CSRR project created successfully",
            "project_file": hfss.project_file,
            "project_name": project_name,
            "design_name": design_name,
            "params": params.model_dump(),
        }
        
    except Exception as e:
        print(f"创建CSRR项目时发生错误: {e}")
        return {
            "success": False,
            "message": f"CSRR project creation failed: {str(e)}",
            "project_file": None,
            "project_name": project_name if 'project_name' in locals() else None,
            "design_name": design_name if 'design_name' in locals() else None,
            "params": params.model_dump() if 'params' in locals() else None,
            "error": str(e)
        }
    
    finally:
        # 释放HFSS资源（但不关闭项目和桌面）
        try:
            hfss.release_desktop(close_projects=False, close_desktop=False)
        except:
            pass

# ---------- LangChain工具定义 ----------
class CreateCSRRTool(BaseTool):
    """创建CSRR结构的LangChain工具"""
    
    name: str = "CREATE_CSRR"
    description: str = """该函数用于使用 PyAEDT 工具直接在 Ansys HFSS 中创建一个 **CSRR (Complementary Split-Ring Resonator) 结构**。
    CSRR 是一种用于微波和无线通信系统的常见电磁元件，通常用于设计传感器、滤波器、天线等。
    
    **功能描述**：
    1. 根据输入参数，自动在 HFSS 中创建一个符合指定尺寸的 CSRR 结构。
    2. 支持环的外径、环宽、开口宽度、环间隙和微带线的宽度等重要设计参数。
    3. 自动生成相应的空气盒和辐射边界，并在微带线两端添加波端口。
    4. 可以指定基板材质（如 FR4_epoxy），自动进行材料分配。
    
    **结构特点**：
    CSRR为互补开口环谐振器，通过在接地板上刻蚀开口环图案实现。
    本工具在接地板上进行减法布尔运算，刻蚀出双环开口结构。
    
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
        """执行CSRR创建"""
        try:
            # 处理LangChain传递的嵌套kwargs结构
            if 'kwargs' in kwargs:
                actual_kwargs = kwargs['kwargs']
            else:
                actual_kwargs = kwargs
            
            # 解析参数
            params = CSRREntryParams(**actual_kwargs)
            options = BuildCSRROptions()
            
            # 构建项目
            result = build_csrr_project(params, options)
            
            if result["success"]:
                return f"""CSRR项目创建成功！
项目名称: {result['project_name']}
设计名称: {result['design_name']}
项目文件: {result.get('project_file', 'N/A')}"""
            else:
                return f"CSRR项目创建失败: {result['error']}"
                
        except Exception as e:
            return f"参数解析或执行错误: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """异步执行（调用同步方法）"""
        return self._run(**kwargs)


# 创建工具实例
CREATE_CSRR = CreateCSRRTool()
