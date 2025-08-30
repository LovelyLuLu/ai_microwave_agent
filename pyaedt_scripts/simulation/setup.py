"""
HFSS 仿真分析和求解设置脚本
作者：PyAEDT自动化脚本
"""

import os
from ansys.aedt.core import Hfss
from ansys.aedt.core.generic.general_methods import pyaedt_function_handler

# =============================================================================
# 仿真求解参数 (可灵活调整)
# =============================================================================

# 自适应网格剖分参数
MAX_PASSES = 30  # 最大迭代次数
DELTA_S = 0.02  # 收敛误差

# 扫频设置
START_FREQ = 1       # 起始频率 (GHz)
STOP_FREQ = 10       # 截止频率 (GHz)
STEP_FREQ = 0.001     # 频率步长 (GHz)
SWEEP_NAME = "BroadbandSweep"  # 扫频名称
SWEEP_TYPE = "Interpolating"  # 扫频类型 (可选: "Fast", "Interpolating", "Discrete")

# =============================================================================
# 核心功能函数
# =============================================================================

@pyaedt_function_handler
def setup_hfss_analysis(hfss_app, setup_name="MySetup"):
    """
    为HFSS设计初始化或更新一个分析设置。

    参数:
    - hfss_app (pyaedt.Hfss): 一个有效的Hfss应用实例。
    - setup_name (str): 要创建或更新的分析设置的名称。

    返回:
    - pyaedt.modules.SolveSbr.SetupSbr: 创建或更新后的分析设置对象。
    """
    print(f"正在为设计 '{hfss_app.design_name}' 配置分析设置 '{setup_name}'...")

    # 检查是否存在同名设置，如果存在则更新，否则创建
    if setup_name in [s.name for s in hfss_app.setups]:
        print(f"分析设置 '{setup_name}' 已存在，将进行更新。")
        setup = hfss_app.get_setup(setup_name)
        setup.props["MaximumPasses"] = MAX_PASSES
        setup.props["MinimumConvergedPasses"] = 1
        setup.props["PercentRefinement"] = 30
        setup.props["DeltaS"] = DELTA_S
        setup.update()
    else:
        print(f"创建新的分析设置: '{setup_name}'")
        setup = hfss_app.create_setup(setupname=setup_name)
        setup.props["MaximumPasses"] = MAX_PASSES
        setup.props["MinimumConvergedPasses"] = 1
        setup.props["PercentRefinement"] = 30
        setup.props["DeltaS"] = DELTA_S

    print("分析设置配置完成:")
    print(f"  - 最大迭代次数 (Maximum Passes): {setup.props['MaximumPasses']}")
    print(f"  - 收敛标准 (Delta S): {setup.props['DeltaS']}")

    return setup

@pyaedt_function_handler
def setup_frequency_sweep(hfss_app, setup_name, sweep_name=SWEEP_NAME):
    """
    为指定的分析设置添加一个扫频。

    参数:
    - hfss_app (pyaedt.Hfss): 一个有效的Hfss应用实例。
    - setup_name (str): 关联的分析设置名称。
    - sweep_name (str): 要创建的扫频的名称。

    返回:
    - pyaedt.modules.SolveSweeps.Sweep: 创建或更新后的扫频对象。
    """
    print(f"正在为设置 '{setup_name}' 配置扫频 '{sweep_name}'...")

    setup = hfss_app.get_setup(setup_name)
    if not setup:
        print(f"错误: 无法找到分析设置 '{setup_name}'。")
        return None

    # In recent PyAEDT versions, sweep objects are accessed via the setup object.
    existing_sweep = None
    for sweep in setup.sweeps:
        if sweep.name == sweep_name:
            existing_sweep = sweep
            break

    if existing_sweep:
        print(f"扫频 '{sweep_name}' 已存在，将进行更新。")
        sweep = existing_sweep
        sweep.props["RangeStart"] = f"{START_FREQ}GHz"
        sweep.props["RangeEnd"] = f"{STOP_FREQ}GHz"
        sweep.props["RangeStep"] = f"{STEP_FREQ}GHz"
        sweep.props["Type"] = SWEEP_TYPE
        sweep.update()
    else:
        print(f"创建新的扫频: '{sweep_name}'")
        sweep = hfss_app.create_linear_step_sweep(
            setupname=setup_name,
            unit="GHz",
            freqstart=START_FREQ,
            freqstop=STOP_FREQ,
            step_size=STEP_FREQ,
            sweepname=sweep_name,
            sweep_type=SWEEP_TYPE,
            save_fields=False,
        )

    if not sweep:
        print(f"错误: 未能创建或更新扫频 '{sweep_name}'。")
        return None

    print("扫频配置完成:")
    print(f"  - 类型 (Type): {sweep.props['Type']}")
    print(f"  - 起始频率 (Start): {sweep.props['RangeStart']}")
    print(f"  - 截止频率 (End): {sweep.props['RangeEnd']}")
    print(f"  - 步长 (Step): {sweep.props['RangeStep']}")

    return sweep

@pyaedt_function_handler
def get_latest_project(aedt_path, project_name_prefix="CSRR_Project"):
    """
    在指定路径下查找并返回最新创建的AEDT项目。

    参数:
    - aedt_path (str): AEDT项目的存储路径。
    - project_name_prefix (str): 项目名称的前缀，用于筛选。

    返回:
    - str: 最新项目的完整路径，如果找不到则返回None。
    """
    project_dir = os.path.join(aedt_path)
    if not os.path.exists(project_dir):
        print(f"错误: 路径 '{project_dir}' 不存在。")
        return None

    # 筛选出所有匹配前缀的.aedt文件夹
    project_folders = [
        d for d in os.listdir(project_dir)
        if d.startswith(project_name_prefix) and d.endswith(".aedt")
    ]

    if not project_folders:
        print(f"在 '{project_dir}' 中未找到任何以 '{project_name_prefix}' 开头的项目。")
        return None

    # 获取每个项目的创建时间
    latest_project = max(
        project_folders,
        key=lambda d: os.path.getmtime(os.path.join(project_dir, d))
    )

    latest_project_path = os.path.join(project_dir, latest_project)
    print(f"找到最新项目: {latest_project_path}")
    return latest_project_path