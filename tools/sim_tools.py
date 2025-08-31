"""HFSS仿真工具
基于 pyaedt_scripts/simulation/solve.py 和 setup.py 的 LangChain 工具实现
用于对已创建的HFSS项目进行仿真求解
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from ansys.aedt.core import Hfss, Desktop
from ansys.aedt.core.generic.general_methods import pyaedt_function_handler
# 移除项目解锁工具导入


class SimulationParams(BaseModel):
    """HFSS仿真参数"""
    # 必需参数
    start_freq: float = Field(
        description="扫频起始频率 (GHz)",
        gt=0
    )
    stop_freq: float = Field(
        description="扫频截止频率 (GHz)",
        gt=0
    )
    step_freq: float = Field(
        description="频率步长 (GHz)",
        gt=0
    )
    
    # 可选参数（使用默认值）
    sweep_name: str = Field(
        default="BroadbandSweep",
        description="扫频名称"
    )
    sweep_type: str = Field(
        default="Interpolating",
        description="扫频类型 (Fast, Interpolating, Discrete)"
    )
    max_passes: int = Field(
        default=30,
        description="最大迭代次数",
        gt=0
    )
    delta_s: float = Field(
        default=0.02,
        description="收敛误差",
        gt=0
    )
    setup_name: str = Field(
        default="MainSetup",
        description="分析设置名称"
    )
    project_name_prefix: str = Field(
        default="CSRR_Project",
        description="项目名称前缀，用于查找最新项目"
    )
    non_graphical: bool = Field(
        default=False,
        description="是否以非图形模式运行"
    )


class SimulationOptions(BaseModel):
    """仿真选项配置"""
    monitor_interval: int = Field(
        default=10,
        description="监控间隔（秒）",
        gt=0
    )
    save_project: bool = Field(
        default=True,
        description="是否保存项目"
    )
    release_desktop: bool = Field(
        default=True,
        description="仿真完成后是否释放桌面并关闭HFSS程序"
    )


# =============================================================================
# HFSS仿真进度监控类
# =============================================================================

class HFSSProgressMonitor:
    """
    HFSS仿真进度监控器
    
    此类提供了监控HFSS仿真进度的功能，包括:
    - 连接到正在运行的AEDT实例
    - 监控仿真状态和进度
    - 实时输出详细的进度信息
    """
    
    def __init__(self, hfss_instance):
        """
        初始化监控器
        
        Args:
            hfss_instance: 已连接的HFSS实例
        """
        self.hfss = hfss_instance
        self.monitoring = False
        self.start_time = None
        self.monitor_thread = None
        
    def get_simulation_status(self) -> Dict[str, any]:
        """
        获取仿真状态信息
        
        Returns:
            Dict: 包含仿真状态的字典
        """
        status = {
            'is_solving': False,
            'setup_names': [],
            'active_setup': None,
            'solution_type': None,
            'mesh_info': {},
            'solving_info': ''
        }
        
        try:
            if self.hfss:
                # 获取设置信息
                status['setup_names'] = list(self.hfss.setups)
                status['solution_type'] = self.hfss.solution_type
                
                # 获取活动设置
                if self.hfss.setups:
                    active_setup = list(self.hfss.setups)[0]
                    status['active_setup'] = active_setup
                    
                    # 尝试获取网格信息
                    try:
                        mesh_stats = self.hfss.mesh.get_mesh_stats()
                        if mesh_stats:
                            status['mesh_info'] = mesh_stats
                    except:
                        pass
                
                # 检查是否正在求解
                if hasattr(self, 'simulation_thread') and self.simulation_thread and self.simulation_thread.is_alive():
                    status['is_solving'] = True
                    status['solving_info'] = '仿真线程正在运行'
                else:
                    # 检查设置的求解状态
                    try:
                        for setup_name in status['setup_names']:
                            try:
                                setup = self.hfss.setups[setup_name]
                                if hasattr(setup, 'is_solved'):
                                    if setup.is_solved:
                                        status['solving_info'] = f'设置 {setup_name} 已完成求解'
                                    else:
                                        status['solving_info'] = f'设置 {setup_name} 未完成求解'
                                        if hasattr(self, 'simulation_thread') and self.simulation_thread and self.simulation_thread.is_alive():
                                            status['is_solving'] = True
                            except:
                                pass
                    except:
                        pass
                    
        except Exception as e:
            print(f"获取仿真状态时出错: {e}")
            
        return status
    
    def print_detailed_status(self):
        """
        打印详细的状态信息
        """
        print("\n" + "="*80)
        print(f"HFSS仿真进度监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        if not self.hfss:
            print("错误: 未连接到HFSS实例")
            return
            
        # 基本信息
        print(f"项目名称: {self.hfss.project_name}")
        print(f"设计名称: {self.hfss.design_name}")
        print(f"求解类型: {self.hfss.solution_type}")
        
        # 获取仿真状态
        status = self.get_simulation_status()
        
        print(f"\n设置信息:")
        if status['setup_names']:
            for setup in status['setup_names']:
                print(f"  - {setup}")
        else:
            print("  无可用设置")
            
        print(f"\n仿真状态: {'正在求解' if status['is_solving'] else '未在求解'}")
        
        # 求解详细信息
        if status.get('solving_info'):
            print(f"求解信息: {status['solving_info']}")
        
        # 网格信息
        if status['mesh_info']:
            print(f"\n网格信息:")
            for key, value in status['mesh_info'].items():
                print(f"  {key}: {value}")
        
        # 运行时间
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"\n监控运行时间: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        else:
            print(f"\n监控运行时间: 未初始化")
        
        print("="*80)
    
    def monitor_loop(self, interval: int = 10):
        """
        监控循环
        
        Args:
            interval: 监控间隔（秒）
        """
        while self.monitoring:
            try:
                self.print_detailed_status()
                time.sleep(interval)
            except Exception as e:
                print(f"监控过程中出错: {e}")
                break
    
    def start_monitoring(self, interval: int = 10):
        """
        开始监控仿真进度
        
        Args:
            interval: 监控间隔（秒）
        """
        self.monitoring = True
        self.start_time = time.time()
        
        print(f"\n开始实时监控HFSS仿真进度，刷新间隔: {interval}秒")
        print("监控将在后台运行...")
        
        # 在后台线程中启动监控
        self.monitor_thread = threading.Thread(target=self.monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """
        停止监控
        """
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        print("\n监控已停止")


# =============================================================================
# 核心功能函数
# =============================================================================

@pyaedt_function_handler
def setup_hfss_analysis(hfss_app, setup_name="MainSetup", max_passes=30, delta_s=0.02):
    """
    为HFSS设计初始化或更新一个分析设置。

    参数:
    - hfss_app (pyaedt.Hfss): 一个有效的Hfss应用实例。
    - setup_name (str): 要创建或更新的分析设置的名称。
    - max_passes (int): 最大迭代次数。
    - delta_s (float): 收敛误差。

    返回:
    - pyaedt.modules.SolveSbr.SetupSbr: 创建或更新后的分析设置对象。
    """
    print(f"正在为设计 '{hfss_app.design_name}' 配置分析设置 '{setup_name}'...")

    # 检查是否存在同名设置，如果存在则更新，否则创建
    if setup_name in [s.name for s in hfss_app.setups]:
        print(f"分析设置 '{setup_name}' 已存在，将进行更新。")
        setup = hfss_app.get_setup(setup_name)
        setup.props["MaximumPasses"] = max_passes
        setup.props["MinimumConvergedPasses"] = 1
        setup.props["PercentRefinement"] = 30
        setup.props["DeltaS"] = delta_s
        setup.update()
    else:
        print(f"创建新的分析设置: '{setup_name}'")
        setup = hfss_app.create_setup(setupname=setup_name)
        setup.props["MaximumPasses"] = max_passes
        setup.props["MinimumConvergedPasses"] = 1
        setup.props["PercentRefinement"] = 30
        setup.props["DeltaS"] = delta_s

    print("分析设置配置完成:")
    print(f"  - 最大迭代次数 (Maximum Passes): {setup.props['MaximumPasses']}")
    print(f"  - 收敛标准 (Delta S): {setup.props['DeltaS']}")

    return setup


@pyaedt_function_handler
def setup_frequency_sweep(hfss_app, setup_name, sweep_name="BroadbandSweep", 
                         start_freq=1, stop_freq=10, step_freq=0.001, sweep_type="Interpolating"):
    """
    为指定的分析设置添加一个扫频。

    参数:
    - hfss_app (pyaedt.Hfss): 一个有效的Hfss应用实例。
    - setup_name (str): 关联的分析设置名称。
    - sweep_name (str): 要创建的扫频的名称。
    - start_freq (float): 起始频率 (GHz)。
    - stop_freq (float): 截止频率 (GHz)。
    - step_freq (float): 频率步长 (GHz)。
    - sweep_type (str): 扫频类型。

    返回:
    - pyaedt.modules.SolveSweeps.Sweep: 创建或更新后的扫频对象。
    """
    print(f"正在为设置 '{setup_name}' 配置扫频 '{sweep_name}'...")

    setup = hfss_app.get_setup(setup_name)
    if not setup:
        print(f"错误: 无法找到分析设置 '{setup_name}'。")
        return None

    # 检查是否存在同名扫频
    existing_sweep = None
    for sweep in setup.sweeps:
        if sweep.name == sweep_name:
            existing_sweep = sweep
            break

    if existing_sweep:
        print(f"扫频 '{sweep_name}' 已存在，将进行更新。")
        sweep = existing_sweep
        sweep.props["RangeStart"] = f"{start_freq}GHz"
        sweep.props["RangeEnd"] = f"{stop_freq}GHz"
        sweep.props["RangeStep"] = f"{step_freq}GHz"
        sweep.props["Type"] = sweep_type
        sweep.update()
    else:
        print(f"创建新的扫频: '{sweep_name}'")
        sweep = hfss_app.create_linear_step_sweep(
            setupname=setup_name,
            unit="GHz",
            freqstart=start_freq,
            freqstop=stop_freq,
            step_size=step_freq,
            sweepname=sweep_name,
            sweep_type=sweep_type,
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


def run_hfss_simulation(params: SimulationParams, options: SimulationOptions = None) -> Dict[str, Any]:
    """
    执行HFSS仿真求解流程
    
    Args:
        params: 仿真参数
        options: 仿真选项
        
    Returns:
        Dict: 包含仿真执行状态的字典
    """
    if options is None:
        options = SimulationOptions()
        
    result = {
        "success": False,
        "message": "",
        "project_name": "",
        "design_name": "",
        "setup_name": "",
        "sweep_name": "",
        "simulation_time": 0,
        "error": ""
    }
    
    start_time = time.time()
    hfss = None
    
    try:
        print("="*70)
        print("开始执行HFSS仿真求解流程...")
        print("="*70)

        # AEDT 项目文件路径
        aedt_projects_path = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
        
        # 查找最新项目
        latest_project_path = get_latest_project(aedt_projects_path, params.project_name_prefix)

        if not latest_project_path:
            result["error"] = "未能找到最新的项目文件"
            return result

        # 初始化HFSS，连接到现有项目
        print(f"正在连接到项目: {latest_project_path}")
        try:
            # 首先尝试连接到现有项目
            hfss = Hfss(
                project=latest_project_path,
                non_graphical=params.non_graphical,
                new_desktop=False,
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "locked" in error_msg or "project is locked" in error_msg:
                print("项目被锁定，尝试使用新的Desktop实例...")
                try:
                    # 如果项目被锁定，尝试使用新的Desktop实例
                    from ansys.aedt.core import Desktop
                    # 先尝试关闭现有Desktop
                    try:
                        desktop = Desktop()
                        desktop.close_desktop()
                    except:
                        pass
                    
                    # 使用新的Desktop实例
                    hfss = Hfss(
                        project=latest_project_path,
                        non_graphical=params.non_graphical,
                        new_desktop=True,
                    )
                    print("成功使用新Desktop实例连接到项目")
                except Exception as e2:
                    result["error"] = f"项目被锁定且无法创建新Desktop实例: {str(e2)}。请手动关闭AEDT后重试。"
                    return result
            else:
                result["error"] = f"连接HFSS项目时发生错误: {str(e)}"
                return result
        print(f"成功连接到项目: {hfss.project_name}")
        print(f"当前设计: {hfss.design_name}")
        
        result["project_name"] = hfss.project_name
        result["design_name"] = hfss.design_name

        # 1. 配置分析设置
        analysis_setup = setup_hfss_analysis(
            hfss, 
            setup_name=params.setup_name,
            max_passes=params.max_passes,
            delta_s=params.delta_s
        )
        if not analysis_setup:
            result["error"] = "分析设置配置失败"
            return result
            
        result["setup_name"] = analysis_setup.name

        # 2. 配置扫频
        frequency_sweep = setup_frequency_sweep(
            hfss, 
            setup_name=analysis_setup.name, 
            sweep_name=params.sweep_name,
            start_freq=params.start_freq,
            stop_freq=params.stop_freq,
            step_freq=params.step_freq,
            sweep_type=params.sweep_type
        )
        if not frequency_sweep:
            result["error"] = "扫频配置失败"
            return result
            
        result["sweep_name"] = frequency_sweep.name

        # 3. 保存项目
        if options.save_project:
            print("\n正在保存项目...")
            hfss.save_project()
            print("项目已保存。")

        # 4. 执行仿真
        print("\n开始执行仿真求解...")
        print(f"分析设置: {analysis_setup.name}")
        print(f"扫频: {frequency_sweep.name}")
        
        # 创建进度监控器
        monitor = HFSSProgressMonitor(hfss)
        
        try:
            # 启动监控器
            monitor.start_monitoring(interval=options.monitor_interval)
            
            # 执行仿真 - 使用非阻塞方式
            print("\n正在启动仿真求解...")
            
            # 启动仿真（非阻塞）
            simulation_thread = threading.Thread(target=lambda: hfss.analyze(setup=analysis_setup.name))
            
            # 将仿真线程引用保存到监控器中
            monitor.simulation_thread = simulation_thread
            
            simulation_thread.start()
            
            # 等待仿真完成
            print("\n仿真已启动，正在等待完成...")
            print("提示：您可以按 Ctrl+C 停止监控（不会停止仿真）")
            
            try:
                # 等待仿真线程完成
                simulation_thread.join()
                print("\n仿真线程已完成！")
                        
            except KeyboardInterrupt:
                print("\n用户中断监控，但仿真将继续在后台运行...")
                # 等待仿真线程完成
                simulation_thread.join()
                print("\n仿真线程已完成！")
                
            # 停止监控
            monitor.stop_monitoring()
            
            print("仿真求解已完成！")
            
            # 计算仿真时间
            simulation_time = time.time() - start_time
            result["simulation_time"] = simulation_time
            
            result["success"] = True
            result["message"] = f"仿真完成，用时 {simulation_time:.2f} 秒"
            
            print("\n仿真完成，准备清理资源...")
            
        except Exception as e:
            print(f"错误：仿真执行失败。{e}")
            result["error"] = f"仿真执行失败: {str(e)}"
            # 确保停止监控
            monitor.stop_monitoring()
            
            print("\n异常情况下准备清理资源...")

    except Exception as e:
        print(f"\n发生严重错误: {e}")
        result["error"] = f"严重错误: {str(e)}"
        
        print("\n严重错误情况下准备清理资源...")

    finally:
        # 最终的资源清理
        try:
            if hfss:
                print("\n最终资源清理...")
                # 保存项目
                if options.save_project:
                    print("正在保存项目...")
                    hfss.save_project()
                    print("项目已保存。")
                
                # 释放Desktop资源
                if options.release_desktop:
                    print("正在释放Desktop资源...")
                    hfss.close_desktop()
                    print("Desktop资源已释放")
                print("最终资源清理完成")
        except Exception as final_error:
            print(f"最终资源清理失败: {final_error}")

    print("="*70)
    print("HFSS仿真求解流程执行完毕。")
    print("="*70)
    
    return result


# =============================================================================
# LangChain 工具类
# =============================================================================

class RunSimulationTool(BaseTool):
    """运行HFSS仿真的LangChain工具"""
    
    name: str = "RUN_SIM"
    description: str = """该函数用于使用 PyAEDT 工具对已创建的 HFSS 项目进行仿真求解。
    适用于对已完成建模的微波器件（如SRR、CSRR等）进行频域仿真计算。
    
    **功能描述**：
    1. 自动查找并连接到最新创建的HFSS项目文件。
    2. 根据输入参数配置分析设置，包括最大迭代次数和收敛误差。
    3. 设置频率扫描参数，支持多种扫频类型（Fast、Interpolating、Discrete）。
    4. 启动仿真求解并提供实时进度监控。
    5. 自动保存项目。
    
    **应用场景**：
    - 对SRR/CSRR结构进行仿真求解
    - 微波器件的频域仿真计算
    - HFSS项目的自动化仿真执行
    
    **必需参数**：
    - start_freq: 扫频起始频率 (GHz)
    - stop_freq: 扫频截止频率 (GHz) 
    - step_freq: 频率步长 (GHz)
    
    **可选参数（有默认值）**：
    - sweep_name: 扫频名称（默认BroadbandSweep）
    - sweep_type: 扫频类型（默认Interpolating）
    - max_passes: 最大迭代次数（默认30）
    - delta_s: 收敛误差（默认0.02）
    - setup_name: 分析设置名称（默认MainSetup）
    - project_name_prefix: 项目名称前缀（默认CSRR_Project）
    - non_graphical: 是否以非图形模式运行（默认False）
    """
    
    def _run(self, **kwargs) -> str:
        """执行HFSS仿真"""
        try:
            # 处理LangChain传递的嵌套kwargs结构
            if 'kwargs' in kwargs:
                actual_kwargs = kwargs['kwargs']
            else:
                actual_kwargs = kwargs
            
            # 解析参数
            params = SimulationParams(**actual_kwargs)
            options = SimulationOptions()
            
            # 执行仿真
            result = run_hfss_simulation(params, options)
            
            if result["success"]:
                return f"""HFSS仿真求解完成！
项目名称: {result['project_name']}
设计名称: {result['design_name']}
分析设置: {result['setup_name']}
扫频设置: {result['sweep_name']}
仿真用时: {result['simulation_time']:.2f} 秒
状态: {result['message']}"""
            else:
                return f"HFSS仿真求解失败: {result['error']}"
                
        except Exception as e:
            return f"参数解析或执行错误: {str(e)}"
    
    async def _arun(self, **kwargs) -> str:
        """异步执行（调用同步方法）"""
        return self._run(**kwargs)


# 创建工具实例
RUN_SIM = RunSimulationTool()


if __name__ == "__main__":
    # 测试代码
    test_params = SimulationParams(
        start_freq=1.0,
        stop_freq=10.0,
        step_freq=0.01,
        sweep_name="TestSweep",
        max_passes=20
    )
    
    result = run_hfss_simulation(test_params)
    print(result)