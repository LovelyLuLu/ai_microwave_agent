#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果分析工具测试脚本
用于验证新创建的HFSS结果分析工具的功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.result_analysis_tool import ANALYZE_RESULTS, ResultAnalysisParams

def test_tool_import():
    """测试工具导入"""
    print("=== 测试工具导入 ===")
    print(f"工具名称: {ANALYZE_RESULTS.name}")
    print(f"工具描述: {ANALYZE_RESULTS.description[:100]}...")
    print("✅ 工具导入成功\n")

def test_parameters():
    """测试参数验证"""
    print("=== 测试参数验证 ===")
    
    # 测试默认参数
    try:
        params = ResultAnalysisParams()
        print("✅ 默认参数创建成功")
        print(f"  - setup_name: {params.setup_name}")
        print(f"  - sweep_name: {params.sweep_name}")
        print(f"  - s_parameters: {params.s_parameters}")
        print(f"  - generate_plots: {params.generate_plots}")
    except Exception as e:
        print(f"❌ 默认参数创建失败: {e}")
    
    # 测试自定义参数
    try:
        custom_params = ResultAnalysisParams(
            setup_name="CustomSetup",
            sweep_name="CustomSweep",
            s_parameters=["S(1,1)", "S(2,1)"],
            generate_plots=True,
            calculate_vswr=True
        )
        print("✅ 自定义参数创建成功")
        print(f"  - setup_name: {custom_params.setup_name}")
        print(f"  - s_parameters: {custom_params.s_parameters}")
    except Exception as e:
        print(f"❌ 自定义参数创建失败: {e}")
    
    print()

def test_tool_call_format():
    """测试工具调用格式"""
    print("=== 测试工具调用格式 ===")
    
    # 模拟LangChain工具调用
    test_kwargs = {
        "setup_name": "MainSetup",
        "sweep_name": "BroadbandSweep",
        "s_parameters": ["S(1,1)", "S(2,1)"],
        "generate_plots": True,
        "project_path": None  # 将自动查找项目
    }
    
    try:
        # 注意：这里只测试参数解析，不执行实际的HFSS操作
        print("测试参数格式:")
        for key, value in test_kwargs.items():
            print(f"  - {key}: {value}")
        
        # 验证参数可以被正确解析
        params = ResultAnalysisParams(**test_kwargs)
        print("✅ 参数格式验证成功")
        
    except Exception as e:
        print(f"❌ 参数格式验证失败: {e}")
    
    print()

def test_output_directory():
    """测试输出目录设置"""
    print("=== 测试输出目录 ===")
    
    # 检查results目录
    results_dir = project_root / "results"
    if results_dir.exists():
        print(f"✅ Results目录存在: {results_dir}")
    else:
        print(f"⚠️ Results目录不存在，将自动创建: {results_dir}")
        results_dir.mkdir(exist_ok=True)
        print("✅ Results目录创建成功")
    
    # 测试写入权限
    test_file = results_dir / "test_write.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("测试写入权限")
        test_file.unlink()  # 删除测试文件
        print("✅ Results目录写入权限正常")
    except Exception as e:
        print(f"❌ Results目录写入权限异常: {e}")
    
    print()

def show_usage_examples():
    """显示使用示例"""
    print("=== 使用示例 ===")
    
    print("1. 通过Agent调用（推荐）:")
    print('   python app/agent_build.py --input "分析最新的HFSS仿真结果"')
    print()
    
    print("2. 通过Agent调用（指定参数）:")
    print('   python app/agent_build.py --input "分析HFSS结果，只需要S11和S21参数"')
    print()
    
    print("3. 通过Agent调用（自定义设置）:")
    print('   python app/agent_build.py --input "分析MainSetup的BroadbandSweep结果，生成VSWR图"')
    print()
    
    print("4. 交互模式:")
    print('   python app/agent_build.py --interactive')
    print('   然后输入: "请分析刚才仿真的结果"')
    print()

def main():
    """主测试函数"""
    print("🔬 HFSS结果分析工具测试")
    print("=" * 50)
    
    test_tool_import()
    test_parameters()
    test_tool_call_format()
    test_output_directory()
    show_usage_examples()
    
    print("=" * 50)
    print("✅ 所有测试完成！")
    print()
    print("📋 工具功能摘要:")
    print("  • S参数分析和可视化（幅度、相位图）")
    print("  • VSWR（电压驻波比）计算和绘图")
    print("  • 关键性能指标计算（回波损耗、插入损耗、谐振频率等）")
    print("  • 数据导出（CSV、JSON格式）")
    print("  • 自动生成分析报告和图表")
    print()
    print("📁 输出文件将保存在: results/ 文件夹")
    print("📊 支持的图表格式: PNG (高分辨率)")
    print("📄 支持的数据格式: CSV, JSON")
    print()
    print("🚀 现在可以通过Agent使用该工具进行HFSS结果分析！")

if __name__ == "__main__":
    main()