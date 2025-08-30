#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：查看 Agent 获取到的工具信息
"""

import json
from tools.csrr_tool import CREATE_CSRR
from tools.srr_tool import CREATE_SRR

def show_tool_function_info():
    """展示 Agent 获取到的工具 function 介绍"""
    
    print("\n" + "="*80)
    print("Agent 获取工具 Function 介绍的方式详解")
    print("="*80)
    
    tools = [CREATE_CSRR, CREATE_SRR]
    
    for i, tool in enumerate(tools, 1):
        print(f"\n{i}. 工具: {tool.__class__.__name__}")
        print("-" * 50)
        
        # 1. 工具名称 - Agent 用于识别工具
        print(f"🔧 工具名称 (name): {tool.name}")
        
        # 2. 工具描述 - Agent 理解工具功能的关键信息
        print(f"📝 工具描述 (description):\n{tool.description}")
        
        # 3. 参数 Schema - Agent 了解如何调用工具
        if hasattr(tool, 'args_schema') and tool.args_schema:
            print(f"\n📋 参数模型: {tool.args_schema.__name__}")
            
            # 获取参数字段信息
            if hasattr(tool.args_schema, 'model_fields'):
                print("\n📊 参数字段详情:")
                for field_name, field_info in tool.args_schema.model_fields.items():
                    required = "✅ 必需" if field_info.is_required() else "⚪ 可选"
                    default = f" (默认: {field_info.default})" if not field_info.is_required() else ""
                    desc = f" - {field_info.description}" if hasattr(field_info, 'description') and field_info.description else ""
                    print(f"  • {field_name}: {required}{default}{desc}")
        
        print("\n" + "-" * 50)
    
    print("\n" + "="*80)
    print("Agent 如何使用这些信息:")
    print("="*80)
    print("""
1. 🤖 Agent 通过 'name' 识别可用的工具
2. 📖 Agent 通过 'description' 理解工具的功能和使用场景
3. 🔍 Agent 通过 'args_schema' 了解需要什么参数
4. 🎯 Agent 根据用户需求选择合适的工具并传递正确的参数
5. ⚡ LangChain 框架自动处理工具调用和参数验证

关键点:
• description 是 Agent 理解工具功能的核心
• args_schema 定义了工具接受的参数结构
• Pydantic 模型提供参数验证和类型检查
• Agent 会根据 description 中的信息决定何时使用该工具
    """)

def show_langchain_integration():
    """展示 LangChain 集成方式"""
    print("\n" + "="*80)
    print("LangChain 工具集成方式")
    print("="*80)
    
    print("""
🔗 LangChain 工具定义方式:

1. StructuredTool.from_function() 方式 (CSRR工具):
   CREATE_CSRR = StructuredTool.from_function(
       name="create_csrr_hfss_project",
       description="使用 PyAEDT 创建 CSRR 结构...",
       func=lambda **kwargs: build_csrr_project(BuildCSRROptions(**kwargs)),
       args_schema=BuildCSRROptions,
   )

2. BaseTool 继承方式 (SRR工具):
   class CreateSRRTool(BaseTool):
       name: str = "CREATE_SRR"
       description: str = "创建SRR结构的HFSS项目..."
       
       def _run(self, **kwargs) -> str:
           # 工具执行逻辑
           pass

🎯 Agent 获取信息的流程:
1. LLM 接收到绑定的工具列表
2. 每个工具的 name 和 description 被发送给 LLM
3. LLM 根据用户输入选择合适的工具
4. LLM 生成工具调用请求 (tool_calls)
5. LangChain 框架执行工具并返回结果
    """)

if __name__ == "__main__":
    show_tool_function_info()
    show_langchain_integration()