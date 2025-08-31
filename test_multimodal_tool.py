#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态图像分析工具测试脚本
测试工具的基本功能、参数验证和LangChain兼容性
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.multimodal_analysis_tool import (
    MultimodalAnalysisParams,
    MultimodalAnalysisTool,
    find_simulation_images,
    encode_image_to_base64,
    generate_analysis_prompt,
    MULTIMODAL_ANALYSIS
)

def test_parameter_validation():
    """测试参数验证功能"""
    print("\n=== 测试参数验证 ===")
    
    try:
        # 测试默认参数
        params = MultimodalAnalysisParams()
        print(f"✅ 默认参数创建成功:")
        print(f"   - results_dir: {params.results_dir}")
        print(f"   - include_s_parameters: {params.include_s_parameters}")
        print(f"   - include_vswr: {params.include_vswr}")
        print(f"   - output_format: {params.output_format}")
        print(f"   - save_report: {params.save_report}")
        
        # 测试自定义参数
        custom_params = MultimodalAnalysisParams(
            results_dir="custom_results",
            include_s_parameters=False,
            output_format="json",
            report_filename="test_report.json"
        )
        print(f"✅ 自定义参数创建成功")
        
    except Exception as e:
        print(f"❌ 参数验证测试失败: {str(e)}")
        return False
    
    return True

def test_image_finding():
    """测试图像文件查找功能"""
    print("\n=== 测试图像文件查找 ===")
    
    try:
        # 测试查找results文件夹中的图像
        results_dir = "results"
        if not os.path.exists(results_dir):
            print(f"⚠️  结果文件夹不存在: {results_dir}")
            return True  # 不算失败，只是没有测试数据
        
        found_images = find_simulation_images(results_dir)
        print(f"✅ 图像查找成功:")
        print(f"   - S参数图像: {len(found_images['s_parameters'])} 个")
        for img in found_images['s_parameters']:
            print(f"     * {os.path.basename(img)}")
        print(f"   - VSWR图像: {len(found_images['vswr'])} 个")
        for img in found_images['vswr']:
            print(f"     * {os.path.basename(img)}")
        
        # 测试不存在的文件夹
        try:
            find_simulation_images("nonexistent_folder")
            print(f"❌ 应该抛出FileNotFoundError异常")
            return False
        except FileNotFoundError:
            print(f"✅ 正确处理不存在的文件夹")
        
    except Exception as e:
        print(f"❌ 图像查找测试失败: {str(e)}")
        return False
    
    return True

def test_image_encoding():
    """测试图像编码功能"""
    print("\n=== 测试图像编码 ===")
    
    try:
        # 查找一个测试图像
        results_dir = "results"
        if not os.path.exists(results_dir):
            print(f"⚠️  跳过图像编码测试，结果文件夹不存在")
            return True
        
        found_images = find_simulation_images(results_dir)
        all_images = found_images['s_parameters'] + found_images['vswr']
        
        if not all_images:
            print(f"⚠️  跳过图像编码测试，没有找到图像文件")
            return True
        
        # 测试编码第一个图像
        test_image = all_images[0]
        encoded = encode_image_to_base64(test_image)
        
        if encoded and len(encoded) > 100:  # 基本的长度检查
            print(f"✅ 图像编码成功: {os.path.basename(test_image)}")
            print(f"   - 编码长度: {len(encoded)} 字符")
        else:
            print(f"❌ 图像编码结果异常")
            return False
        
        # 测试不存在的图像
        try:
            encode_image_to_base64("nonexistent_image.png")
            print(f"❌ 应该抛出异常")
            return False
        except Exception:
            print(f"✅ 正确处理不存在的图像文件")
        
    except Exception as e:
        print(f"❌ 图像编码测试失败: {str(e)}")
        return False
    
    return True

def test_prompt_generation():
    """测试提示词生成功能"""
    print("\n=== 测试提示词生成 ===")
    
    try:
        prompt = generate_analysis_prompt()
        
        if prompt and len(prompt) > 500:  # 基本的长度检查
            print(f"✅ 提示词生成成功")
            print(f"   - 提示词长度: {len(prompt)} 字符")
            print(f"   - 包含关键词检查:")
            
            keywords = ["S参数", "VSWR", "回波损耗", "插入损耗", "频率", "分析"]
            for keyword in keywords:
                if keyword in prompt:
                    print(f"     ✅ 包含: {keyword}")
                else:
                    print(f"     ⚠️  缺少: {keyword}")
        else:
            print(f"❌ 提示词生成异常")
            return False
        
    except Exception as e:
        print(f"❌ 提示词生成测试失败: {str(e)}")
        return False
    
    return True

def test_tool_instantiation():
    """测试工具实例化和基本属性"""
    print("\n=== 测试工具实例化 ===")
    
    try:
        # 测试工具实例
        tool = MultimodalAnalysisTool()
        
        print(f"✅ 工具实例化成功")
        print(f"   - 工具名称: {tool.name}")
        print(f"   - 描述长度: {len(tool.description)} 字符")
        
        # 检查是否是BaseTool的实例
        from langchain.tools import BaseTool
        if isinstance(tool, BaseTool):
            print(f"✅ 正确继承BaseTool")
        else:
            print(f"❌ 未正确继承BaseTool")
            return False
        
        # 测试全局实例
        if MULTIMODAL_ANALYSIS and hasattr(MULTIMODAL_ANALYSIS, 'name'):
            print(f"✅ 全局工具实例创建成功: {MULTIMODAL_ANALYSIS.name}")
        else:
            print(f"❌ 全局工具实例创建失败")
            return False
        
    except Exception as e:
        print(f"❌ 工具实例化测试失败: {str(e)}")
        return False
    
    return True

def test_tool_description():
    """测试工具描述的完整性"""
    print("\n=== 测试工具描述 ===")
    
    try:
        tool = MultimodalAnalysisTool()
        description = tool.description
        
        # 检查描述中的关键信息
        required_info = [
            "多模态", "qwen_vl_max", "HFSS", "S参数", "VSWR",
            "必需参数", "可选参数", "输出"
        ]
        
        missing_info = []
        for info in required_info:
            if info not in description:
                missing_info.append(info)
        
        if not missing_info:
            print(f"✅ 工具描述完整")
            print(f"   - 描述长度: {len(description)} 字符")
        else:
            print(f"⚠️  工具描述缺少信息: {missing_info}")
        
    except Exception as e:
        print(f"❌ 工具描述测试失败: {str(e)}")
        return False
    
    return True

def main():
    """运行所有测试"""
    print("🚀 开始多模态图像分析工具测试")
    print("=" * 50)
    
    tests = [
        ("参数验证", test_parameter_validation),
        ("图像文件查找", test_image_finding),
        ("图像编码", test_image_encoding),
        ("提示词生成", test_prompt_generation),
        ("工具实例化", test_tool_instantiation),
        ("工具描述", test_tool_description),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！工具已准备就绪")
        return True
    else:
        print(f"⚠️  {total - passed} 个测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)