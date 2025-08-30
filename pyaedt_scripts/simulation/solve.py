import os
import sys
import time
import threading
from datetime import datetime
from typing import Optional, Dict, List
from ansys.aedt.core import Hfss, Desktop

# 将 simulation 目录添加到 Python 路径，以便导入 setup 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from setup import setup_hfss_analysis, setup_frequency_sweep, get_latest_project

# =============================================================================
# HFSS仿真进度监控类
# =============================================================================

class HFSSProgressMonitor:
    """
    HFSS仿真进度监控器 - 集成版本
    
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
                
                # 检查是否正在求解 - 使用线程标记
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
                                        # 如果有未完成的设置且仿真线程还在运行，则认为正在求解
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
# 脚本主要执行逻辑
# =============================================================================

def main():
    """
    主函数，执行HFSS仿真求解流程。
    """
    print("="*70)
    print("开始执行HFSS仿真求解流程...")
    print("="*70)

    # AEDT 项目文件路径 (根据实际情况修改)
    # 通常是 "C:\\Users\\YourUser\\Documents\\Ansoft"
    aedt_projects_path = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
    
    # 查找最新的CSRR项目
    latest_project_path = get_latest_project(aedt_projects_path, project_name_prefix="CSRR_Project")

    if not latest_project_path:
        print("未能找到最新的项目文件，脚本终止。")
        return

    # 初始化HFSS，连接到现有项目
    hfss = None
    try:
        print(f"正在连接到项目: {latest_project_path}")
        # 以非图形化模式连接到现有会话
        hfss = Hfss(
            project=latest_project_path,
            non_graphical=False,  # 设置为False以观察GUI，调试时有用
            new_desktop=False,    # 连接到现有桌面会话
        )
        print(f"成功连接到项目: {hfss.project_name}")
        print(f"当前设计: {hfss.design_name}")

        # 1. 配置分析设置
        analysis_setup = setup_hfss_analysis(hfss, setup_name="MainSetup")
        if not analysis_setup:
            raise RuntimeError("分析设置配置失败。")

        # 2. 配置扫频
        frequency_sweep = setup_frequency_sweep(hfss, setup_name=analysis_setup.name, sweep_name="BroadbandSweep")
        if not frequency_sweep:
            raise RuntimeError("扫频配置失败。")

        # 3. 保存项目
        print("\n正在保存项目...")
        hfss.save_project()
        print("项目已保存。")

        # 4. 执行仿真
        print("\n开始执行仿真分析...")
        print(f"分析设置: {analysis_setup.name}")
        print(f"扫频: {frequency_sweep.name}")
        
        # 创建进度监控器
        monitor = HFSSProgressMonitor(hfss)
        
        # 直接执行仿真分析
        try:
            # 启动监控器
            monitor.start_monitoring(interval=5)  # 每5秒更新一次
            
            # 执行仿真 - 使用非阻塞方式
            print("\n正在启动仿真分析...")
            
            # 启动仿真（非阻塞）
            import threading
            simulation_thread = threading.Thread(target=lambda: hfss.analyze(setup=analysis_setup.name))
            
            # 将仿真线程引用保存到监控器中
            monitor.simulation_thread = simulation_thread
            
            simulation_thread.start()
            
            # 等待仿真完成
            print("\n仿真已启动，正在等待完成...")
            print("提示：您可以按 Ctrl+C 停止监控（不会停止仿真）")
            
            try:
                # 等待仿真线程完成，不进行额外的状态检查
                # 让监控线程独立处理状态更新
                simulation_thread.join()
                print("\n仿真线程已完成！")
                        
            except KeyboardInterrupt:
                print("\n用户中断监控，但仿真将继续在后台运行...")
                # 等待仿真线程完成
                simulation_thread.join()
                print("\n仿真线程已完成！")
                
            # 停止监控
            monitor.stop_monitoring()
            
            print("仿真分析已完成！请在HFSS中查看结果。")
            
        except Exception as e:
            print(f"错误：仿真执行失败。{e}")
            # 确保停止监控
            monitor.stop_monitoring()
            # 可以在这里添加更详细的错误处理逻辑

    except Exception as e:
        print(f"\n发生严重错误: {e}")
        print("请检查AEDT环境是否正确配置，以及项目文件是否存在。")

    finally:
        # 5. 释放桌面 (根据需要决定是否关闭AEDT)
        if hfss:
            # 如果你希望脚本执行完毕后保持AEDT打开，请注释掉下面这行
            # hfss.release_desktop()
            # print("\n已断开与AEDT的连接。")
            pass

    print("="*70)
    print("HFSS仿真求解流程执行完毕。")
    print("="*70)

if __name__ == "__main__":
    main()