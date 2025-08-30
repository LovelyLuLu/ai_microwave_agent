"""
SRR (Split Ring Resonator) 结构建模脚本
使用PyAEDT自动化ANSYS EDT 2024.2中的建模过程
作者：PyAEDT自动化脚本

与CSRR不同：
- SRR为金属开口双环结构，不需要在接地板上进行刻蚀减法布尔运算。
- 本脚本直接在基板上方生成两个开口金属环（铜），作为独立金属谐振体。
"""

from datetime import datetime
from ansys.aedt.core import Hfss
from ansys.aedt.core import constants

# ==============================================================================
# 初始化设置
# ==============================================================================

# 根据当前时间生成项目和设计名称
current_time = datetime.now()
project_name = f"SRR_Project_{current_time.strftime('%Y%m%d_%H%M%S')}"
design_name = f"SRR_Design_{current_time.strftime('%Y%m%d_%H%M%S')}"

# 设置AEDT版本
aedt_version = "2024.2"

# 创建HFSS应用实例
hfss = Hfss(
    project=project_name,
    design=design_name,
    version=aedt_version,
    non_graphical=False,
    new_desktop=False,
)

print(f"创建项目: {project_name}")
print(f"创建设计: {design_name}")

# ==============================================================================
# 定义参数化变量（SRR为金属双环，不再在地平面上刻蚀）
# ==============================================================================

# 基板参数
hfss["Sub_L"] = "40mm"       # 基板长度
hfss["Sub_W"] = "25mm"       # 基板宽度
hfss["Sub_H"] = "1.6mm"      # 基板厚度（FR-4）

# SRR结构参数
hfss["R_out"] = "5mm"        # 外环外半径
hfss["Ring_W"] = "0.8mm"     # 环宽度
hfss["Gap_W"] = "0.3mm"      # 开口宽度
hfss["S"] = "1mm"            # 内外环间距
hfss["R_in"] = "R_out - Ring_W - S"  # 内环外半径
hfss["t"] = "0.035mm"        # 铜层厚度（标准PCB铜厚）

# 微带线参数
hfss["MS_W"] = "1.8mm"          # 微带线宽度
hfss["MS_L"] = "Sub_L"        # 微带线长度（基板长度）

# 空气盒子参数（基于波长设计）
hfss["AirBox_L"] = "MS_L"  # 空气盒长度：微带线长度
hfss["AirBox_W"] = "MS_W + 360mm"  # 空气盒宽度：微带线宽度 + 360mm
hfss["AirBox_H"] = "Sub_H + 125mm"     # 空气盒高度：基板厚度 + λ

print("参数化变量定义完成")

# ==============================================================================
# 第一步：创建介质基板 (Substrate)
# ==============================================================================

print("\n开始创建介质基板...")
substrate = hfss.modeler.create_box(
    origin=["-Sub_L/2", "-Sub_W/2", "0mm"],
    sizes=["Sub_L", "Sub_W", "Sub_H"],
    name="Substrate",
    material="FR4_epoxy",
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
    material="copper"
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
    material="copper",
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
    material="copper",
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

print("\n正在保存项目...")
hfss.save_project()
print(f"项目已保存: {hfss.project_file}")

print("\n" + "="*70)
print("SRR结构建模完成！")
print(f"项目名称: {project_name}")
print(f"设计名称: {design_name}")
print("您可以在HFSS中查看生成的3D模型（SRR金属双环，无地平面刻蚀）")
print("="*70)

# 如需关闭AEDT，请取消注释
# hfss.release_desktop()