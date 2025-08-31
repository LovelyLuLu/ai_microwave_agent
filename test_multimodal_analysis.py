#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态分析功能测试脚本

该脚本用于独立测试多模态分析工具的功能，无需通过Agent对话。
可以直接运行查看多模态分析的工作效果和报告质量。

使用方法:
    python test_multimodal_analysis.py

作者: AI-Microwave-Agent
日期: 2025-01-31
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 确保项目根目录在sys.path中
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入多模态分析工具
try:
    from tools.multimodal_analysis_tool import MULTIMODAL_ANALYSIS
except ImportError as e:
    print(f"❌ 导入多模态分析工具失败: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

def print_header():
    """打印测试脚本头部信息"""
    print("="*80)
    print("🧪 多模态分析功能测试脚本")
    print("="*80)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 项目路径: {project_root}")
    print("="*80)
    print()

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查.env文件
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  警告: 未找到.env文件")
        print("   请创建.env文件并配置API密钥")
    else:
        print("✅ 找到.env文件")
    
    # 检查API密钥
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if dashscope_key:
        print(f"✅ DASHSCOPE_API_KEY: {dashscope_key[:10]}...")
    else:
        print("❌ 未找到DASHSCOPE_API_KEY")
    
    if gemini_key:
        print(f"✅ GEMINI_API_KEY: {gemini_key[:10]}...")
    else:
        print("⚠️  未找到GEMINI_API_KEY")
    
    print()

def check_image_files():
    """检查仿真结果图像文件"""
    print("🖼️  检查仿真结果图像文件...")
    
    results_dir = project_root / "results"
    if not results_dir.exists():
        print(f"❌ 结果目录不存在: {results_dir}")
        return False
    
    # 检查S参数图像
    s_param_files = [
        "S_1_1.png", "S_2_1.png", "S_1_2.png", "S_2_2.png"
    ]
    
    found_s_params = []
    for file in s_param_files:
        file_path = results_dir / file
        if file_path.exists():
            found_s_params.append(file)
            print(f"✅ 找到S参数图像: {file}")
        else:
            print(f"❌ 未找到S参数图像: {file}")
    
    # 检查VSWR图像
    vswr_file = results_dir / "VSWR.png"
    if vswr_file.exists():
        print(f"✅ 找到VSWR图像: VSWR.png")
        found_vswr = True
    else:
        print(f"❌ 未找到VSWR图像: VSWR.png")
        found_vswr = False
    
    total_images = len(found_s_params) + (1 if found_vswr else 0)
    print(f"📊 图像文件统计: S参数({len(found_s_params)}/4), VSWR({1 if found_vswr else 0}/1), 总计({total_images}/5)")
    
    if total_images == 0:
        print("❌ 未找到任何可分析的图像文件")
        return False
    
    print()
    return True

def test_basic_analysis():
    """测试基本分析功能"""
    print("🚀 开始基本多模态分析测试...")
    print("-" * 60)
    
    try:
        # 使用默认参数进行分析
        result = MULTIMODAL_ANALYSIS.run({})
        
        print("✅ 多模态分析执行成功!")
        print("📋 分析结果:")
        print(result)
        print("-" * 60)
        return True
        
    except Exception as e:
        print(f"❌ 多模态分析执行失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        print("详细错误信息:")
        traceback.print_exc()
        print("-" * 60)
        return False

def test_custom_analysis():
    """测试自定义参数分析"""
    print("🎯 开始自定义参数分析测试...")
    print("-" * 60)
    
    try:
        # 使用自定义参数进行分析
        custom_params = {
            "results_dir": "results",
            "include_s_parameters": True,
            "include_vswr": True,
            "output_format": "markdown",
            "save_report": True,
            "report_filename": f"test_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        }
        
        print(f"📝 使用参数: {custom_params}")
        result = MULTIMODAL_ANALYSIS.run(custom_params)
        
        print("✅ 自定义参数分析执行成功!")
        print("📋 分析结果:")
        print(result)
        print("-" * 60)
        return True
        
    except Exception as e:
        print(f"❌ 自定义参数分析执行失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        print("详细错误信息:")
        traceback.print_exc()
        print("-" * 60)
        return False

def test_json_output():
    """测试JSON格式输出"""
    print("📄 开始JSON格式输出测试...")
    print("-" * 60)
    
    try:
        # 测试JSON格式输出
        json_params = {
            "results_dir": "results",
            "output_format": "json",
            "save_report": True,
            "report_filename": f"test_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
        
        print(f"📝 使用参数: {json_params}")
        result = MULTIMODAL_ANALYSIS.run(json_params)
        
        print("✅ JSON格式输出测试成功!")
        print("📋 分析结果:")
        print(result)
        print("-" * 60)
        return True
        
    except Exception as e:
        print(f"❌ JSON格式输出测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        print("详细错误信息:")
        traceback.print_exc()
        print("-" * 60)
        return False

def check_generated_reports():
    """检查生成的报告文件"""
    print("📁 检查生成的报告文件...")
    
    results_dir = project_root / "results"
    if not results_dir.exists():
        print("❌ 结果目录不存在")
        return
    
    # 查找分析报告文件
    report_files = list(results_dir.glob("*analysis_report*.md")) + list(results_dir.glob("*analysis_report*.json"))
    
    if not report_files:
        print("❌ 未找到生成的分析报告文件")
        return
    
    print(f"✅ 找到 {len(report_files)} 个分析报告文件:")
    for report_file in sorted(report_files, key=lambda x: x.stat().st_mtime, reverse=True):
        file_size = report_file.stat().st_size
        mod_time = datetime.fromtimestamp(report_file.stat().st_mtime)
        print(f"   📄 {report_file.name} ({file_size} bytes, {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    # 显示最新报告的部分内容
    if report_files:
        latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
        print(f"\n📖 最新报告预览 ({latest_report.name}):")
        print("-" * 40)
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                content = f.read()
                # 显示前500个字符
                preview = content[:500]
                if len(content) > 500:
                    preview += "\n... (内容已截断)"
                print(preview)
        except Exception as e:
            print(f"❌ 读取报告文件失败: {e}")
        print("-" * 40)
    
    print()

def print_summary(test_results):
    """打印测试总结"""
    print("="*80)
    print("📊 测试总结")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    failed_tests = total_tests - passed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests} ✅")
    print(f"失败测试: {failed_tests} ❌")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过! 多模态分析功能工作正常。")
    else:
        print("\n⚠️  部分测试失败，请检查配置和环境。")
    
    print("="*80)

def main():
    """主函数"""
    print_header()
    
    # 环境检查
    check_environment()
    
    # 检查图像文件
    if not check_image_files():
        print("❌ 图像文件检查失败，无法进行分析测试")
        print("请确保results目录中包含仿真结果图像文件")
        return
    
    # 执行测试
    test_results = {}
    
    print("🧪 开始执行多模态分析功能测试...")
    print()
    
    # 基本分析测试
    test_results["基本分析功能"] = test_basic_analysis()
    
    # 自定义参数测试
    test_results["自定义参数分析"] = test_custom_analysis()
    
    # JSON输出测试
    test_results["JSON格式输出"] = test_json_output()
    
    # 检查生成的报告
    check_generated_reports()
    
    # 打印测试总结
    print_summary(test_results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试脚本执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 测试脚本执行完毕")