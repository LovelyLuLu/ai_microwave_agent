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
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# Tools
from tools.csrr_tool import CREATE_CSRR
from tools.srr_tool import CREATE_SRR
from tools.sim_tools import RUN_SIM
from tools.result_tool import ANALYZE_RESULTS


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
    tools = [CREATE_CSRR, CREATE_SRR, RUN_SIM, ANALYZE_RESULTS]
    llm = llm.bind_tools(tools)

    system = SystemMessage(
        content=(
            "你是一个HFSS自动化协同设计Agent。"
            "当用户提出建模/仿真/结果需求时，必须调用合适的工具返回JSON，包含文件路径、setup、sweep、图表与关键数值。"
            "除非用户特别要求长篇解释，否则以简洁结构化结果为主。"
        )
    )
    return llm, tools, system


# provide a tiny in-memory history for quick test
_sessions = {}

def get_history(session_id: str):
    if session_id not in _sessions:
        _sessions[session_id] = ChatMessageHistory()
    return _sessions[session_id]


def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="用户输入的自然语言指令")
    ap.add_argument("--session", default="default")
    args = ap.parse_args()

    llm, tools, system = make_agent()

    # 获取历史记录并添加系统消息
    history = get_history(args.session)
    if not history.messages or not any(isinstance(msg, SystemMessage) for msg in history.messages):
        history.add_message(system)
    
    # 添加用户消息
    history.add_message(HumanMessage(content=args.input))
    
    # 直接调用 LLM
    resp = llm.invoke(history.messages)
    # print tool invocations or final text
    try:
        print(json.dumps(resp.model_dump(), ensure_ascii=False, indent=2))
    except Exception:
        print(str(resp))


if __name__ == "__main__":
    main()
