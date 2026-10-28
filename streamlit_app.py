import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOL_MAP, TOOLS_SCHEMA

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY") or st.secrets.get("DEEPSEEK_API_KEY")
if not API_KEY:
    st.error("没有找到 DEEPSEEK_API_KEY。本地请检查 .env，云端请在 Settings → Secrets 中配置。")
    st.stop()

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def run_agent(user_input, history):
    messages = [
        {"role": "system", "content": 
            "你是一个五大联赛足球数据分析助手。"
            "你可以调用工具查询积分榜、近期战绩、历史交锋、未来赛程，还可以检索球队最新新闻。"
            "重要规则：1. 直接提取用户问题中的球队名称作为参数，不要擅自修改。"
            "2. 如果你要进行比赛预测（特别是下一场比赛），必须同时调用 query_team_news 查看是否有伤病或突发新闻。"
            "3. 在最终回答中，必须结合新闻情报对模型给出的数据预测进行分析（例如：指出某队因伤病可能降低胜算），然后给出你的综合判断。"
        }
    ]
    messages += history
    messages.append({"role": "user", "content": user_input})

    for _ in range(5):
        resp = client.chat.completions.create(
            model="deepseek-chat", 
            messages=messages, 
            tools=TOOLS_SCHEMA
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content
        
        messages.append(msg)
        for tc in msg.tool_calls:
            func = TOOL_MAP.get(tc.function.name)
            args = json.loads(tc.function.arguments)
            result = func(**args) if func else {"error": "未知工具"}
            messages.append({
                "role": "tool", 
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)
            })
    return "抱歉，这个问题我暂时处理不了。"

st.set_page_config(page_title="五大联赛赛果决策 Agent", page_icon="⚽")
st.title("⚽ 五大联赛赛果决策 Agent")
st.caption("可以问：曼城下一场打谁 / 拜仁最近状态如何 / 巴萨和皇马交锋谁占优 / 意甲前四是谁")

if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if user_input := st.chat_input("输入你的问题…"):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.history.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Agent 正在查阅数据与新闻情报…"):
            answer = run_agent(user_input, st.session_state.history[:-1])
        st.write(answer)

    st.session_state.history.append({"role": "assistant", "content": answer})
