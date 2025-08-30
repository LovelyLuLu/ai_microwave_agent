#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示脚本：展示 Agent 如何获取和使用工具的 Function 介绍
"""

import os
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from tools.csrr_tool import CREATE_CSRR
from tools.srr_tool import CREATE_SRR

def demo_agent_tool_integration():
    """演示 Agent 与工具的集成过程"""
    
    print("\n" + "="*80)
    print("🤖 Agent 工具集成演示")
    print("="*80)
    
    # 1. 初始化 LLM
    print("\n1️⃣ 初始化 LLM...")
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY", "dummy-key"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    
    # 2. 准备工具列表
    print("\n2️⃣ 准备工具列表...")
    tools = [CREATE_CSRR, CREATE_SRR]
    
    print(f"   可用工具数量: {len(tools)}")
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool.name}: {tool.__class__.__name__}")
    
    # 3. 绑定工具到 LLM
    print("\n3️⃣ 绑定工具到 LLM...")
    llm_with_tools = llm.bind_tools(tools)
    
    # 4. 展示 LLM 接收到的工具信息
    print("\n4️⃣ LLM 接收到的工具信息:")
    print("-" * 60)
    
    for i, tool in enumerate(tools, 1):
        print(f"\n🔧 工具 {i}: {tool.name}")
        print(f"📝 描述: {tool.description[:100]}...")
        
        # 展示参数信息
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema.model_json_schema()
            required_fields = schema.get('required', [])
            properties = schema.get('properties', {})
            
            print(f"📋 必需参数: {', '.join(required_fields) if required_fields else '无'}")
            print(f"📊 总参数数: {len(properties)}")
    
    # 5. 模拟 Agent 处理用户请求
    print("\n" + "="*80)
    print("🎯 Agent 处理用户请求的流程")
    print("="*80)
    
    user_requests = [
        "我想创建一个CSRR结构，外环半径5mm，环宽0.5mm，开口宽0.2mm",
        "帮我建立SRR模型，外环半径3mm，环宽0.3mm，开口0.1mm"
    ]
    
    for i, request in enumerate(user_requests, 1):
        print(f"\n{i}️⃣ 用户请求: {request}")
        print("-" * 50)
        
        # 创建消息
        messages = [
            SystemMessage(content="你是HFSS建模助手，根据用户需求选择合适的工具创建模型。"),
            HumanMessage(content=request)
        ]
        
        print("🤖 Agent 分析过程:")
        print("   1. 解析用户需求")
        print("   2. 匹配可用工具")
        
        # 分析哪个工具更适合
        if "CSRR" in request.upper():
            selected_tool = "CREATE_CSRR (create_csrr_hfss_project)"
            reason = "用户明确提到CSRR结构"
        elif "SRR" in request.upper():
            selected_tool = "CREATE_SRR"
            reason = "用户明确提到SRR结构"
        else:
            # 根据描述判断
            if "刻蚀" in request or "减法" in request:
                selected_tool = "CREATE_CSRR (create_csrr_hfss_project)"
                reason = "涉及刻蚀操作，适合CSRR"
            else:
                selected_tool = "CREATE_SRR"
                reason = "金属环结构，适合SRR"
        
        print(f"   3. 选择工具: {selected_tool}")
        print(f"   4. 选择原因: {reason}")
        print(f"   5. 提取参数并调用工具")

def show_tool_call_format():
    """展示工具调用的格式"""
    
    print("\n" + "="*80)
    print("📞 工具调用格式示例")
    print("="*80)
    
    print("""
🔄 LLM 生成的工具调用请求格式:

{
  "tool_calls": [
    {
      "name": "create_csrr_hfss_project",
      "args": {
        "params": {
          "r_out_mm": 5.0,
          "ring_width_mm": 0.5,
          "gap_width_mm": 0.2,
          "ms_width_mm": 1.0
        }
      }
    }
  ]
}

📋 参数验证过程:
1. LangChain 接收工具调用请求
2. 使用 Pydantic 模型验证参数
3. 检查必需字段是否存在
4. 验证参数类型和范围
5. 应用默认值
6. 执行工具函数

✅ 成功执行后返回结果给 Agent
❌ 参数错误时返回验证错误信息
    """)

if __name__ == "__main__":
    demo_agent_tool_integration()
    show_tool_call_format()
    
    print("\n" + "="*80)
    print("📚 总结: Agent 获取 Function 介绍的关键点")
    print("="*80)
    print("""
🎯 核心要点:

1. 📝 工具描述 (description) 是 Agent 理解工具功能的关键
   • 描述越详细，Agent 选择越准确
   • 应包含使用场景、参数说明、注意事项

2. 🏷️ 工具名称 (name) 用于唯一标识工具
   • 名称应该清晰表达工具功能
   • Agent 通过名称调用具体工具

3. 📊 参数模式 (args_schema) 定义输入格式
   • Pydantic 模型提供类型验证
   • 字段描述帮助 Agent 理解参数含义
   • 默认值减少必需参数数量

4. 🔗 LangChain 集成方式
   • StructuredTool.from_function(): 函数式工具
   • BaseTool 继承: 类式工具
   • 两种方式都能被 Agent 正确识别和调用

5. ⚡ 自动化流程
   • Agent 自动解析用户需求
   • 根据工具描述选择合适工具
   • 提取参数并生成工具调用请求
   • LangChain 处理参数验证和工具执行
    """)