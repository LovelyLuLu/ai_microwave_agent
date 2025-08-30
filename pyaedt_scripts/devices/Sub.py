import os
from datetime import datetime
from ansys.aedt.core import Hfss

h_sub = "0.762mm" # 基板厚度
Sub_Material = "Rogers RO4350B (lossy)"  # 基板材料
Sub_X = "40mm"  # 基板长度
Sub_Y = "30mm"  # 基板宽度



# 获取当前时间作为项目名称后缀
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
project_name = f"Sub_Project_{current_time}"
design_name = f"Sub_Design_{current_time}"    # 自动生成设计名
# 初始化HFSS (非阻塞模式，保持HFSS打开)
hfss = Hfss(projectname=project_name, specified_version="2024.2", non_graphical=False, new_desktop_session=True)
# 定义设计
hfss.create_design(design_name)
# 创建矩形基板
sub_rectangle = hfss.modeler.create_box(
    position=[-0.5*Sub_X, -0.5*Sub_Y, "0mm"],
    dimensions_list=[Sub_X, Sub_Y, h_sub],
    name="Substrate"
)

# 设置基板材料为Sub_Material
hfss.modeler.assign_material(sub_rectangle, Sub_Material)

# 保存项目
hfss.save_project()
# 关闭HFSS
hfss.close_desktop()
