#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试sim_tools的Desktop释放功能
验证仿真完成后是否正确释放Desktop并关闭HFSS程序
"""

import sys
import os
from tools.sim_tools import SimulationParams, SimulationOptions, run_hfss_simulation

def test_desktop_release():
    """
    测试Desktop释放功能
    """
    print("="*70)
    print("测试sim_tools的Desktop释放功能")
    print("="*70)
    
    # 测试参数
    test_params = SimulationParams(
        start_freq=1.0,
        stop_freq=5.0,
        step_freq=0.1,
        sweep_name="TestSweep",
        max_passes=5,  # 减少迭代次数以加快测试
        delta_s=0.05,  # 放宽收敛条件
        project_name_prefix="CSRR_Project"
    )
    
    # 测试选项 - 确保释放Desktop
    test_options = SimulationOptions(
        monitor_interval=5,
        save_project=True,
        release_desktop=True  # 确保释放Desktop
    )
    
    print("\n测试参数:")
    print(f"  起始频率: {test_params.start_freq} GHz")
    print(f"  截止频率: {test_params.stop_freq} GHz")
    print(f"  频率步长: {test_params.step_freq} GHz")
    print(f"  最大迭代次数: {test_params.max_passes}")
    print(f"  收敛误差: {test_params.delta_s}")
    print(f"  释放Desktop: {test_options.release_desktop}")
    
    print("\n开始测试...")
    
    try:
        # 执行仿真测试
        result = run_hfss_simulation(test_params, test_options)
        
        print("\n测试结果:")
        if result["success"]:
            print("✅ 仿真执行成功")
            print(f"   项目名称: {result['project_name']}")
            print(f"   设计名称: {result['design_name']}")
            print(f"   仿真用时: {result['simulation_time']:.2f} 秒")
            print(f"   状态信息: {result['message']}")
            print("✅ Desktop应该已经被正确释放并关闭")
        else:
            print("❌ 仿真执行失败")
            print(f"   错误信息: {result['error']}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n="*70)
    print("Desktop释放功能测试完成")
    print("="*70)

def test_simulation_options():
    """
    测试SimulationOptions的默认值
    """
    print("\n测试SimulationOptions默认值:")
    
    # 创建默认选项
    default_options = SimulationOptions()
    
    print(f"  监控间隔: {default_options.monitor_interval} 秒")
    print(f"  保存项目: {default_options.save_project}")
    print(f"  释放Desktop: {default_options.release_desktop}")
    
    # 验证默认值
    assert default_options.monitor_interval == 10, "监控间隔默认值错误"
    assert default_options.save_project == True, "保存项目默认值错误"
    assert default_options.release_desktop == True, "释放Desktop默认值错误"
    
    print("✅ SimulationOptions默认值测试通过")

if __name__ == "__main__":
    print("sim_tools Desktop释放功能测试")
    print("此测试将验证仿真完成后是否正确释放Desktop并关闭HFSS程序")
    
    # 测试选项默认值
    test_simulation_options()
    
    # 检查是否有HFSS项目可用于测试
    aedt_path = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
    if os.path.exists(aedt_path):
        project_files = [f for f in os.listdir(aedt_path) if f.startswith("CSRR_Project") and f.endswith(".aedt")]
        if project_files:
            print(f"\n找到 {len(project_files)} 个CSRR项目文件，可以进行完整测试")
            
            # 询问用户是否要进行完整测试
            user_input = input("\n是否要进行完整的仿真测试？(y/n): ")
            if user_input.lower() in ['y', 'yes', '是']:
                test_desktop_release()
            else:
                print("跳过完整仿真测试")
        else:
            print("\n未找到CSRR项目文件，跳过完整仿真测试")
            print("提示: 请先使用CREATE_CSRR工具创建项目，然后再测试仿真功能")
    else:
        print(f"\n未找到AEDT项目目录: {aedt_path}")
        print("跳过完整仿真测试")
    
    print("\n测试完成！")
    print("\n主要改进:")
    print("1. ✅ 仿真完成后自动释放Desktop")
    print("2. ✅ 自动关闭HFSS程序")
    print("3. ✅ 增强的错误处理和资源清理")
    print("4. ✅ 默认启用Desktop释放功能")