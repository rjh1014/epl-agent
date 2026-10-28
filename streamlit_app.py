import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOL_MAP, TOOLS_SCHEMA

st.set_page_config(page_title="五大联赛 AI 决策助手", page_icon="🏆", layout="wide")

load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY") or st.secrets.get("DEEPSEEK_API_KEY")
if not API_KEY:
    st.error("没有找到 DEEPSEEK_API_KEY。")
    st.stop()

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

with st.sidebar:
    st.title("🏆 关于本产品")
    st.markdown("""
    基于大模型与机器学习的**五大联赛决策助手**。
    
    **能力：**
    - 📊 数据洞察（积分榜/战绩/交锋）
    - 🤖 AI 概率预测（随机森林模型）
    - 📰 伤停情报检索（API-Football）
    - 🧠 综合推理与风险提示
    """)
    st.caption("Powered by Streamlit, DeepSeek & scikit-learn")

st.title("⚽ 五大联赛 AI 决策助手")
st.caption("你可以问：皇马下一场打谁？预测一下胜算 / 意甲前四是谁 / 曼城最近状态如何")

if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

def run_agent(user_input, history):
    messages = [
        {"role": "system", "content": 
            "你是一个顶级足球数据分析师。你可以调用工具查数据、预测比赛和检索伤停。"
            "【核心规则】："
            "1. 如果工具返回 `status: no_data`，说明该数据暂未收录。你绝不可以向用户抱怨'系统报错'或'接口故障'。"
            "2. 你应该用分析师的口吻说：'目前情报库尚未覆盖该球队的某些数据'，并主动提示用户：'由于数据缺失，预测存在较高不确定性'。"
            "3. 即使遇到升班马等数据缺失，你也要基于模型给出的兜底概率，给出带风险提示的专业结论。"
        }
    ]
    messages += history
    messages.append({"role": "user", "content": user_input})

    for _ in range(5):
        resp = client.chat.completions.create(model="deepseek-chat", messages=messages, tools=TOOLS_SCHEMA)
        msg = resp.choices[0].message
        
        if not msg.tool_calls:
            return msg.content
        
        messages.append(msg)
        for tc in msg.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)
            
            friendly_names = {
                "predict_match": "正在计算比赛概率", "query_standings": "正在查询积分榜",
                "query_recent_form": "正在查询近期战绩", "query_head_to_head": "正在查询历史交锋",
                "query_league_table": "正在查询联赛排名", "query_team_matches": "正在查询赛程",
                "predict_next_match": "正在预测下一场比赛", "query_team_news": "正在全网检索最新情报"
            }
            status_text = friendly_names.get(func_name, f"正在调用 {func_name}")
            
            with st.status(f"{status_text}...", expanded=False) as status:
                func = TOOL_MAP.get(func_name)
                result = func(**args) if func else {"error": "未知工具"}
                status.update(label=f"{status_text} 完成", state="complete")
            
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, ensure_ascii=False)})
            
    return "抱歉，这个问题我暂时处理不了。"

if user_input := st.chat_input("输入你的问题…"):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.history.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        answer = run_agent(user_input, st.session_state.history[:-1])
        st.markdown(answer)

    st.session_state.history.append({"role": "assistant", "content": answer})