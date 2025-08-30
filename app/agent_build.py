\
from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv()

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

    chain = RunnableWithMessageHistory(
        llm,
        lambda session_id: get_history(session_id),
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    resp = chain.invoke(
        {"input": args.input, "chat_history": [system]},
        config={"configurable": {"session_id": args.session}},
    )
    # print tool invocations or final text
    try:
        print(json.dumps(resp.dict(), ensure_ascii=False, indent=2))
    except Exception:
        print(str(resp))

if __name__ == "__main__":
    main()
