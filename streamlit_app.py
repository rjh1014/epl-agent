import os
import json
import streamlit as st
from openai import OpenAI
from tools import TOOL_MAP, TOOLS_SCHEMA

st.set_page_config(page_title="五大联赛 AI 决策助手", page_icon="🏆", layout="wide")

API_KEY = st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    st.error("没有找到 DEEPSEEK_API_KEY。请检查 Secrets 配置。")
    st.stop()

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

with st.sidebar:
    st.title("🏆 五大联赛 AI 决策助手")
    st.markdown("基于大模型与随机森林模型的分析工具。")

st.title("⚽ 五大联赛 AI 决策助手")
st.caption("你可以问：阿森纳有哪些伤停？/ 威尼斯打国米谁赢？/ 曼城下一场预测。")

if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

def run_agent(user_input, history):
    messages = [
        {"role": "system", "content": 
            "你是一个顶级足球数据分析师。你可以调用工具查数据、预测比赛、检索伤停和查询赔率。"
            "【核心规则】："
            "1. 如果工具返回 `status: no_data`，用分析师口吻说明'情报库暂未覆盖'，并提示不确定性。"
            "2. 当用户询问伤停或首发时，优先调用 `query_team_intelligence` 工具，它会自动按优先级尝试多个数据源。"
            "3. 如果 `predict_match` 返回的 `note` 中包含'严重警告'，你必须在回答开头声明：'该模型预测因数据缺失而失真，仅供参考'。"
            "4. 【极重要-常识兜底】：如果模型概率因数据缺失而严重失真，你必须结合你的足球常识强势纠正它。"
        }
    ]
    messages += history
    messages.append({"role": "user", "content": user_input})

    for _ in range(5):
        try:
            # 在这里捕获大模型报错
            resp = client.chat.completions.create(model="deepseek-chat", messages=messages, tools=TOOLS_SCHEMA)
        except Exception as e:
            # 如果是 400 错误，通常是 tools 的格式不对
            return f"⚠️ DeepSeek API 报错，详细信息：{str(e)}"
            
        msg = resp.choices[0].message
        
        if not msg.tool_calls:
            return msg.content
        
        messages.append(msg)
        
        for tc in msg.tool_calls:
            func_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except:
                args = {}
                
            status_text = f"正在调用 {func_name}"
            with st.status(f"{status_text}...", expanded=False) as status:
                func = TOOL_MAP.get(func_name)
                if func:
                    try:
                        result = func(**args)
                    except Exception as e:
                        result = {"status": "error", "message": f"工具执行报错: {str(e)}"}
                else:
                    result = {"status": "error", "message": "未知工具"}
                status.update(label=f"{status_text} 完成", state="complete")
            
            messages.append({
                "role": "tool", 
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)
            })
            
    return "抱歉，执行轮数过多。"

if user_input := st.chat_input("输入你的问题…"):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.history.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        answer = run_agent(user_input, st.session_state.history[:-1])
        st.markdown(answer)

    st.session_state.history.append({"role": "assistant", "content": answer})