\
from __future__ import annotations
import os

# Optional dotenv loading
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # If python-dotenv isn't installed or .env can't be loaded, continue without crashing
    pass

# Ensure project root is on sys.path when running this file directly
import sys
from pathlib import Path
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from langchain_openai import ChatOpenAI
from langchain.tools.render import render_text_description
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# Tools
from tools.csrr_tool import CREATE_CSRR
from tools.srr_tool import CREATE_SRR
from tools.sim_tools import RUN_SIM


def make_agent():
    # 读取环境变量
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY")

    # 初始化 LLM（会自动使用 base_url 和 api_key）
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        api_key=api_key,
        base_url=base_url
    )

    # 绑定工具
    tools = [CREATE_CSRR, CREATE_SRR, RUN_SIM]
    llm = llm.bind_tools(tools)

    system = SystemMessage(
        content=(
            "你是一名资深的微波工程专家AI助手。你的目标是引导用户完成微波器件的设计、仿真和分析的全过程。\n\n"
            "**你的行为准则:**\n\n"
            "1. **遵循流程**: 严格按照'设计 -> 仿真 -> 分析'的顺序引导用户。不要试图一次性完成所有步骤。\n"
            "2. **主动询问**: 在每个阶段完成后，清晰地向用户报告结果，并用提问的方式引导用户进入下一个步骤。例如，在设计完成后，你应该问：'模型已创建，需要现在开始仿真吗？'\n"
            "3. **记忆上下文**: 你必须记住之前步骤产生的重要信息，比如design_name、project_file等，以便在后续的工具调用中使用。\n"
            "4. **精确调用工具**: 根据用户的意图，选择最合适的工具进行调用。仔细阅读工具的描述，确保提供了所有必需的参数。\n"
            "5. **用户确认**: 对于需要花费较长时间或计算资源的操作（如run_simulation），必须得到用户的明确确认后才能执行。\n"
            "6. **简洁输出**: 当总结工具执行结果时，直接输出总结内容，不要包含'AI总结'等标题。除非用户特别要求详细解释，否则以简洁结构化结果为主。"
        )
    )
    return llm, tools, system


# provide a tiny in-memory history for quick test
_sessions = {}

def get_history(session_id: str):
    if session_id not in _sessions:
        _sessions[session_id] = ChatMessageHistory()
    return _sessions[session_id]


def process_user_input(user_input, session_id, llm, tools_map, system):
    """处理单次用户输入"""
    import json
    
    # 获取历史记录并添加系统消息
    history = get_history(session_id)
    if not history.messages or not any(isinstance(msg, SystemMessage) for msg in history.messages):
        history.add_message(system)
    
    # 添加用户消息
    history.add_message(HumanMessage(content=user_input))
    
    # 调用 LLM
    resp = llm.invoke(history.messages)
    history.add_message(resp)
    
    # 检查是否有工具调用
    if resp.tool_calls:
        print(f"AI决定调用 {len(resp.tool_calls)} 个工具:")
        
        for tool_call in resp.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            print(f"\n正在执行工具: {tool_name}")
            print(f"参数: {json.dumps(tool_args, ensure_ascii=False, indent=2)}")
            
            try:
                # 执行工具
                if tool_name in tools_map:
                    tool = tools_map[tool_name]
                    result = tool.invoke(tool_args)
                    print(f"\n工具执行成功!")
                    print(f"结果: {result}")
                    
                    # 添加工具结果到历史
                    tool_message = ToolMessage(
                        content=json.dumps(result, ensure_ascii=False),
                        tool_call_id=tool_id
                    )
                    history.add_message(tool_message)
                else:
                    error_msg = f"未找到工具: {tool_name}"
                    print(f"\n错误: {error_msg}")
                    tool_message = ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_id
                    )
                    history.add_message(tool_message)
                    
            except Exception as e:
                error_msg = f"工具执行失败: {str(e)}"
                print(f"\n错误: {error_msg}")
                tool_message = ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_id
                )
                history.add_message(tool_message)
        
        # 让AI总结工具执行结果
        final_resp = llm.invoke(history.messages)
        print(f"\n=== AI总结 ===")
        print(final_resp.content)
        
    else:
        # 没有工具调用，直接输出AI回复
        print(resp.content)


def interactive_mode(session_id="default"):
    """交互式模式"""
    llm, tools, system = make_agent()
    tools_map = {tool.name: tool for tool in tools}
    
    print("="*60)
    print("🤖 微波工程AI助手 - 交互模式")
    print("="*60)
    print("欢迎使用微波工程AI助手！")
    print("我可以帮助您进行CSRR/SRR结构的设计、仿真和分析。")
    print("\n可用命令:")
    print("  - 输入您的需求进行对话")
    print("  - 输入 'exit' 或 'quit' 退出")
    print("  - 输入 'clear' 清除当前会话历史")
    print("  - 输入 'help' 查看帮助信息")
    print("-"*60)
    
    while True:
        try:
            user_input = input("\n👤 您: ").strip()
            
            if not user_input:
                continue
                
            # 处理特殊命令
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("\n👋 感谢使用微波工程AI助手，再见！")
                break
            elif user_input.lower() in ['clear', '清除']:
                if session_id in _sessions:
                    del _sessions[session_id]
                print("\n✅ 会话历史已清除")
                continue
            elif user_input.lower() in ['help', '帮助']:
                print("\n📖 帮助信息:")
                print("1. 创建CSRR结构: '请创建一个CSRR结构，外环外半径3.5mm...'")
                print("2. 创建SRR结构: '请创建一个SRR结构，外环外半径3.5mm...'")
                print("3. 运行仿真: '请对刚创建的结构进行仿真，频率范围1-10GHz...'")
                print("4. 查看工具信息: '有哪些可用的工具？'")
                continue
            
            print("\n🤖 AI助手:")
            print("-"*40)
            
            # 处理用户输入
            process_user_input(user_input, session_id, llm, tools_map, system)
            
        except KeyboardInterrupt:
            print("\n\n👋 检测到中断信号，正在退出...")
            break
        except EOFError:
            print("\n\n👋 检测到EOF，正在退出...")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            print("请重试或输入 'exit' 退出")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="微波工程AI助手")
    ap.add_argument("--input", help="用户输入的自然语言指令（如果不提供则进入交互模式）")
    ap.add_argument("--session", default="default", help="会话ID")
    ap.add_argument("--interactive", "-i", action="store_true", help="强制进入交互模式")
    args = ap.parse_args()

    # 如果没有提供input参数或者指定了interactive参数，进入交互模式
    if not args.input or args.interactive:
        interactive_mode(args.session)
    else:
        # 单次命令模式（保持原有功能）
        llm, tools, system = make_agent()
        tools_map = {tool.name: tool for tool in tools}
        process_user_input(args.input, args.session, llm, tools_map, system)


if __name__ == "__main__":
    main()
