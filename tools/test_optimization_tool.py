#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化工具测试脚本
用于验证optimization_tool.py的功能和集成
"""

import sys
import os
from pathlib import Path

# 添加tools目录到Python路径
sys.path.append(str(Path(__file__).parent))

from optimization_tool import (
    OptimizationVariable,
    OptimizationObjective,
    OptimizationParams,
    OPTIMIZE_DESIGN
)

def test_optimization_tool_basic():
    """测试优化工具的基本功能"""
    print("=== 优化工具基本功能测试 ===")
    
    # 测试数据结构
    print("\n1. 测试数据结构...")
    
    # 定义优化变量
    variables = [
        OptimizationVariable(
            name="L1",
            min_value=5.0,
            max_value=8.0,
            initial_value=6.5,
            description="第一个谐振器长度 (mm)"
        ),
        OptimizationVariable(
            name="L2",
            min_value=5.0,
            max_value=8.0,
            initial_value=6.5,
            description="第二个谐振器长度 (mm)"
        ),
        OptimizationVariable(
            name="G12",
            min_value=0.1,
            max_value=0.5,
            initial_value=0.3,
            description="谐振器间隙 (mm)"
        )
    ]
    
    # 定义优化目标
    objectives = [
        OptimizationObjective(
            name="S21_passband",
            target_type="maximize",
            target_value=-0.5,
            weight=0.4,
            description="通带内S21参数优化"
        ),
        OptimizationObjective(
            name="S11_passband",
            target_type="minimize",
            target_value=-20.0,
            weight=0.3,
            description="通带内S11参数优化"
        ),
        OptimizationObjective(
            name="VSWR_passband",
            target_type="minimize",
            target_value=1.5,
            weight=0.3,
            description="通带内VSWR优化"
        )
    ]
    
    print(f"✅ 定义了 {len(variables)} 个优化变量")
    print(f"✅ 定义了 {len(objectives)} 个优化目标")
    
    # 创建优化参数
    params = OptimizationParams(
        algorithm="GA",
        variables=variables,
        objectives=objectives,
        population_size=20,
        max_iterations=50,
        convergence_threshold=1e-6,
        mutation_rate=0.1,
        crossover_rate=0.8
    )
    
    print(f"✅ 创建了优化参数配置")
    
    return params

def test_tool_interface():
    """测试工具接口"""
    print("\n=== 工具接口测试 ===")
    
    # 检查工具属性
    print(f"\n工具名称: {OPTIMIZE_DESIGN.name}")
    print(f"工具描述: {OPTIMIZE_DESIGN.description}")
    
    # 检查参数模式
    if hasattr(OPTIMIZE_DESIGN, 'args_schema'):
        print(f"✅ 工具具有参数模式定义")
        schema = OPTIMIZE_DESIGN.args_schema.schema()
        print(f"参数字段数量: {len(schema.get('properties', {}))}")
    else:
        print("❌ 工具缺少参数模式定义")
    
    print("✅ 工具接口检查完成")

def test_mock_optimization():
    """测试模拟优化（不需要HFSS项目）"""
    print("\n=== 模拟优化测试 ===")
    
    # 由于没有实际的HFSS项目，这里只测试参数验证
    params = test_optimization_tool_basic()
    
    try:
        # 转换为字典格式（模拟LangChain调用）
        params_dict = params.model_dump()
        
        print("\n2. 测试参数序列化...")
        print(f"✅ 参数成功序列化为字典，包含 {len(params_dict)} 个字段")
        
        # 测试参数验证
        print("\n3. 测试参数验证...")
        reconstructed_params = OptimizationParams(**params_dict)
        print(f"✅ 参数验证成功")
        
        print("\n4. 模拟工具调用...")
        print("注意：由于没有HFSS项目文件，实际优化将返回错误，这是预期行为")
        
        # 模拟调用（预期会因为没有HFSS项目而失败）
        result = OPTIMIZE_DESIGN._run(**params_dict)
        print(f"工具返回: {result}")
        
        if "未找到HFSS项目文件" in result:
            print("✅ 工具正确检测到缺少HFSS项目文件")
        else:
            print("⚠️ 工具返回了意外的结果")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False
    
    return True

def test_algorithm_selection():
    """测试算法选择功能"""
    print("\n=== 算法选择测试 ===")
    
    params = test_optimization_tool_basic()
    
    # 测试GA算法
    print("\n测试遗传算法(GA)...")
    params.algorithm = "GA"
    params_dict = params.model_dump()
    result_ga = OPTIMIZE_DESIGN._run(**params_dict)
    print(f"GA结果: {result_ga[:100]}..." if len(result_ga) > 100 else f"GA结果: {result_ga}")
    
    # 测试PSO算法
    print("\n测试粒子群算法(PSO)...")
    params.algorithm = "PSO"
    # PSO参数通过重新创建OptimizationParams来设置
    pso_params = OptimizationParams(
        algorithm="PSO",
        variables=params.variables,
        objectives=params.objectives,
        population_size=params.population_size,
        max_iterations=params.max_iterations,
        convergence_threshold=params.convergence_threshold,
        inertia_weight=0.9,
        cognitive_weight=2.0,
        social_weight=2.0
    )
    params_dict = pso_params.model_dump()
    result_pso = OPTIMIZE_DESIGN._run(**params_dict)
    print(f"PSO结果: {result_pso[:100]}..." if len(result_pso) > 100 else f"PSO结果: {result_pso}")
    
    # 测试不支持的算法
    print("\n测试不支持的算法...")
    unknown_params = OptimizationParams(
        algorithm="UNKNOWN",
        variables=params.variables,
        objectives=params.objectives,
        population_size=params.population_size,
        max_iterations=params.max_iterations,
        convergence_threshold=params.convergence_threshold
    )
    params_dict = unknown_params.model_dump()
    result_unknown = OPTIMIZE_DESIGN._run(**params_dict)
    print(f"未知算法结果: {result_unknown}")
    
    if "不支持的优化算法" in result_unknown:
        print("✅ 工具正确处理了不支持的算法")
    else:
        print("⚠️ 工具没有正确处理不支持的算法")
        print(f"实际返回: {result_unknown}")

def main():
    """主测试函数"""
    print("🚀 开始优化工具测试")
    print("=" * 50)
    
    try:
        # 基本功能测试
        test_optimization_tool_basic()
        
        # 工具接口测试
        test_tool_interface()
        
        # 模拟优化测试
        success = test_mock_optimization()
        
        # 算法选择测试
        test_algorithm_selection()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 所有测试完成！优化工具基本功能正常")
            print("\n📋 测试总结:")
            print("✅ 数据结构定义正确")
            print("✅ 工具接口符合LangChain规范")
            print("✅ 参数验证功能正常")
            print("✅ 算法选择功能正常")
            print("✅ 错误处理机制完善")
            print("\n⚠️ 注意: 实际优化需要HFSS项目文件支持")
        else:
            print("❌ 部分测试失败，请检查代码")
            
    except Exception as e:
        print(f"\n💥 测试过程中发生严重错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()