"""
CSRR (Complementary Split Ring Resonator) 结构建模脚本
使用PyAEDT自动化ANSYS EDT 2024.2中的建模过程
作者：PyAEDT自动化脚本
"""

import os
from datetime import datetime
from ansys.aedt.core import Hfss
from ansys.aedt.core import constants
# ==============================================================================
# 初始化设置
# ==============================================================================

# 根据当前时间生成项目和设计名称
current_time = datetime.now()
project_name = f"CSRR_Project_{current_time.strftime('%Y%m%d_%H%M%S')}"
design_name = f"CSRR_Design_{current_time.strftime('%Y%m%d_%H%M%S')}"

# 设置AEDT版本
aedt_version = "2024.2"

# 创建HFSS应用实例
# non_graphical=False 表示以图形界面模式运行
# new_desktop=True 表示创建新的AEDT会话
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
# 定义参数化变量
# ==============================================================================

# 基板参数
hfss["Sub_L"] = "40mm"        # 基板长度
hfss["Sub_W"] = "25mm"        # 基板宽度
hfss["Sub_H"] = "1.6mm"       # 基板厚度（标准FR-4厚度）

# CSRR结构参数
hfss["R_out"] = "5mm"         # 外环外半径
hfss["Ring_W"] = "0.8mm"      # 环宽度
hfss["Gap_W"] = "0.3mm"       # 开口宽度
hfss["S"] = "1mm"           # 内外环间距
hfss["R_in"] = "R_out - Ring_W - S"  # 内环外半径（通过表达式定义）
hfss["Etch_H"] = "Sub_H/10"   # 刻蚀高度（仅用于布尔运算）
hfss["t"] = "0.035mm"         # 铜层厚度（标准PCB铜厚）

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

# 创建基板长方体
# 使用参数化的起始点，使基板中心位于原点
substrate = hfss.modeler.create_box(
    origin=["-Sub_L/2", "-Sub_W/2", "0mm"],
    sizes=["Sub_L", "Sub_W", "Sub_H"],
    name="Substrate",
    material="FR4_epoxy"
)

print("介质基板创建完成")

# ==============================================================================
# 第二步：创建接地板 (Ground Plane) - 作为实体铜层
# ==============================================================================

print("\n开始创建接地板...")

# 创建接地板实体（薄铜层）
# 位于基板上表面
ground_plane = hfss.modeler.create_box(
    origin=["-Sub_L/2", "-Sub_W/2", "Sub_H"],
    sizes=["Sub_L", "Sub_W", "t"],
    name="GND_Solid",
    material="copper"
)

print("接地板实体创建完成")

# ==============================================================================
# 第二步补充：创建微带线 (Microstrip Line)
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
# 第三步：创建CSRR的刻蚀图案 (Etching Pattern)
# ==============================================================================

print("\n开始创建CSRR刻蚀图案...")

# -----------------------------------------------------------------------------
# 3.1 创建外层圆环 (Outer Ring)
# -----------------------------------------------------------------------------

print("  创建外层圆环...")

# 创建外环的外圆柱
outer_cylinder_large = hfss.modeler.create_cylinder(
    origin=["0mm", "0mm", "Sub_H"],
    radius="R_out",
    height="Etch_H",
    name="OuterCyl_Large",
    orientation="Z"
)

# 创建外环的内圆柱（用于挖空）
outer_cylinder_small = hfss.modeler.create_cylinder(
    origin=["0mm", "0mm", "Sub_H"],
    radius="R_out - Ring_W",
    height="Etch_H",
    name="OuterCyl_Small",
    orientation="Z"
)

# 布尔运算：大圆柱减去小圆柱，得到圆环
hfss.modeler.subtract(
    blank_list=[outer_cylinder_large],
    tool_list=[outer_cylinder_small],
    keep_originals=False # 不保留原始对象，只保留布尔运算结果
)
# subtract操作会修改第一个对象，所以outer_ring就是outer_cylinder_large
outer_ring = outer_cylinder_large

print("  外层圆环基础形状完成")

# -----------------------------------------------------------------------------
# 3.2 为外层圆环创建开口 (Outer Split Gap)
# -----------------------------------------------------------------------------

print("  创建外层圆环开口...")

# 创建用于切割开口的长方体
# 开口位于+X方向
# 考虑到弧度，修正切口盒子的尺寸和位置
outer_gap_box = hfss.modeler.create_box(
    origin=["R_out - (Ring_W+(R_out-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_out-Ring_W)))))", "-Gap_W/2", "Sub_H"],
    sizes=["Ring_W+(R_out-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_out-Ring_W))))", "Gap_W", "Etch_H"],
    name="OuterGapBox"
)

# 从外环减去开口长方体
hfss.modeler.subtract(
    blank_list=[outer_ring],
    tool_list=[outer_gap_box],
    keep_originals=False
)
# subtract操作会修改第一个对象，所以outer_ring_split就是outer_ring
outer_ring_split = outer_ring

print("  外层开口圆环创建完成")

# -----------------------------------------------------------------------------
# 3.3 创建内层圆环 (Inner Ring)
# -----------------------------------------------------------------------------

print("  创建内层圆环...")

# 创建内环的外圆柱
inner_cylinder_large = hfss.modeler.create_cylinder(
    origin=["0mm", "0mm", "Sub_H"],
    radius="R_in",
    height="Etch_H",
    name="InnerCyl_Large",
    orientation="Z"
)

# 创建内环的内圆柱（用于挖空）
inner_cylinder_small = hfss.modeler.create_cylinder(
    origin=["0mm", "0mm", "Sub_H"],
    radius="R_in - Ring_W",
    height="Etch_H",
    name="InnerCyl_Small",
    orientation="Z"
)

# 布尔运算：大圆柱减去小圆柱，得到圆环
hfss.modeler.subtract(
    blank_list=[inner_cylinder_large],
    tool_list=[inner_cylinder_small],
    keep_originals=False
)
# subtract操作会修改第一个对象，所以inner_ring就是inner_cylinder_large
inner_ring = inner_cylinder_large

print("  内层圆环基础形状完成")

# -----------------------------------------------------------------------------
# 3.4 为内层圆环创建反向开口 (Inner Split Gap)
# -----------------------------------------------------------------------------

print("  创建内层圆环开口...")

# 创建用于切割开口的长方体
# 开口位于-X方向（与外环相反）
# 考虑到弧度，修正切口盒子的尺寸
inner_gap_box = hfss.modeler.create_box(
    origin=["-R_in", "-Gap_W/2", "Sub_H"],
    sizes=["Ring_W+(R_in-Ring_W)*(1-cos(asin(0.5*Gap_W/(R_in-Ring_W))))", "Gap_W", "Etch_H"],
    name="InnerGapBox"
)

# 从内环减去开口长方体
hfss.modeler.subtract(
    blank_list=[inner_ring],
    tool_list=[inner_gap_box],
    keep_originals=False
)
# subtract操作会修改第一个对象，所以inner_ring_split就是inner_ring
inner_ring_split = inner_ring

print("  内层开口圆环创建完成")

# ==============================================================================
# 第四步：完成最终的CSRR结构
# ==============================================================================

print("\n开始合并CSRR结构...")

# -----------------------------------------------------------------------------
# 4.1 合并内外环 (Unite Rings)
# -----------------------------------------------------------------------------

print("  合并内外环...")

# 直接使用对象引用进行合并，不需要通过名称查找
# 因为我们已经有了outer_ring_split和inner_ring_split的对象引用

# 合并内外环成为单一的CSRR图案
if outer_ring_split and inner_ring_split:
    hfss.modeler.unite(
        assignment=[outer_ring_split, inner_ring_split],
        keep_originals=False
    )
    # unite操作会修改第一个对象，所以csrr_pattern就是第一个对象
    csrr_pattern = outer_ring_split
    print("  内外环合并完成")
else:
    print("  警告：无法找到内外环对象，请检查对象引用")

# -----------------------------------------------------------------------------
# 4.2 从接地板上刻蚀 (Subtract from Ground)
# -----------------------------------------------------------------------------

print("  从接地板刻蚀CSRR图案...")

# 找到CSRR图案的对象名称
csrr_pattern_name = None
for obj_name in hfss.modeler.object_names:
    if "OuterCyl_Large" in obj_name:  # 合并后通常保留第一个对象的名称
        csrr_pattern_name = obj_name
        break

# 从接地板减去CSRR图案
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
# 第五步：设置仿真环境
# ==============================================================================

print("\n开始设置仿真环境...")

# -----------------------------------------------------------------------------
# 5.1 创建空气盒子 (Airbox)
# -----------------------------------------------------------------------------

print("  创建空气盒子...")

# 创建包围整个结构的空气盒
airbox = hfss.modeler.create_box(
    origin=["-AirBox_L/2", "-AirBox_W/2", "-AirBox_H/2"],
    sizes=["AirBox_L", "AirBox_W", "AirBox_H"],
    name="AirBox",
    material="air"
)

print("  空气盒子创建完成")

# -----------------------------------------------------------------------------
# 5.2 设置辐射边界条件
# -----------------------------------------------------------------------------

print("  设置辐射边界...")

# 获取空气盒的所有面
airbox_faces = hfss.modeler.get_object_faces("AirBox")

# 为空气盒的所有外表面设置辐射边界
radiation_boundary = hfss.assign_radiation_boundary_to_objects(
    assignment="AirBox",
    name="Radiation_Boundary"
)

print("  辐射边界设置完成")

# -----------------------------------------------------------------------------
# 5.3 创建波端口（微带线端口）
# -----------------------------------------------------------------------------

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



# ==============================================================================
# 保存项目
# ==============================================================================

print(f"\n正在保存项目...")
hfss.save_project()
print(f"项目已保存: {hfss.project_file}")

print("\n" + "="*70)
print("CSRR结构建模完成！")
print(f"项目名称: {project_name}")
print(f"设计名称: {design_name}")
print("您可以在HFSS中查看生成的3D模型")
print("="*70)

# 保持AEDT界面打开以便查看结果
# 如需关闭，取消下面的注释
# hfss.release_desktop()