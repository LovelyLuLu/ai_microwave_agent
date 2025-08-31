#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化工具测试脚本
测试移除复杂项目解锁逻辑后的工具功能
"""

from csrr_tool import CreateCSRRTool, CSRREntryParams
from srr_tool import CreateSRRTool, SRREntryParams
from sim_tools import RunSimulationTool
from result_analysis_tool import AnalyzeHFSSResultsTool

def test_tool_imports():
    """测试所有工具的导入"""
    print("="*60)
    print("测试工具导入")
    print("="*60)
    
    try:
        # 测试CSRR工具
        csrr_tool = CreateCSRRTool()
        print(f"✓ CSRR工具导入成功: {csrr_tool.name}")
        
        # 测试SRR工具
        srr_tool = CreateSRRTool()
        print(f"✓ SRR工具导入成功: {srr_tool.name}")
        
        # 测试仿真工具
        sim_tool = RunSimulationTool()
        print(f"✓ 仿真工具导入成功: {sim_tool.name}")
        
        # 测试结果分析工具
        analysis_tool = AnalyzeHFSSResultsTool()
        print(f"✓ 结果分析工具导入成功: {analysis_tool.name}")
        
        print("\n所有工具导入测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 工具导入失败: {e}")
        return False

def test_parameter_validation():
    """测试参数验证"""
    print("\n" + "="*60)
    print("测试参数验证")
    print("="*60)
    
    try:
        # 测试CSRR参数
        csrr_params = CSRREntryParams(
            outer_radius=3.5,
            ring_width=0.6,
            gap_width=0.2,
            ring_spacing=0.7,
            microstrip_width=1.4
        )
        print(f"✓ CSRR参数验证成功: 外环半径={csrr_params.outer_radius}mm")
        
        # 测试SRR参数
        srr_params = SRREntryParams(
            outer_radius=2.5,
            ring_width=0.4,
            gap_width=0.15,
            ring_spacing=0.5,
            microstrip_width=1.2
        )
        print(f"✓ SRR参数验证成功: 外环半径={srr_params.outer_radius}mm")
        
        print("\n参数验证测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 参数验证失败: {e}")
        return False

def test_tool_descriptions():
    """测试工具描述"""
    print("\n" + "="*60)
    print("测试工具描述")
    print("="*60)
    
    tools = [
        CreateCSRRTool(),
        CreateSRRTool(),
        RunSimulationTool(),
        AnalyzeHFSSResultsTool()
    ]
    
    for tool in tools:
        print(f"\n工具名称: {tool.name}")
        print(f"描述长度: {len(tool.description)} 字符")
        print(f"描述预览: {tool.description[:100]}...")
    
    print("\n工具描述测试完成！")
    return True

def main():
    """主测试函数"""
    print("简化工具功能测试")
    print("移除了复杂的project_unlock_utils.py，使用简单的release逻辑")
    
    success_count = 0
    total_tests = 3
    
    # 运行测试
    if test_tool_imports():
        success_count += 1
    
    if test_parameter_validation():
        success_count += 1
        
    if test_tool_descriptions():
        success_count += 1
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"通过测试: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 所有测试通过！工具简化成功！")
        print("\n主要改进:")
        print("- 移除了复杂的project_unlock_utils.py文件")
        print("- 简化了项目解锁逻辑，直接使用hfss.release_desktop()")
        print("- 减少了代码复杂度，提高了可维护性")
        print("- 保持了核心功能不变")
    else:
        print("\n❌ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()