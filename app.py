import os

# ================= 强制安装云端缺失的依赖包 =================
os.system("pip install qiuxiaoce requests pandas scikit-learn joblib")

import json
import streamlit as st
from openai import OpenAI
from tools import TOOL_MAP, TOOLS_SCHEMA

# 页面配置（必须放在最前面）
st.set_page_config(page_title="五大联赛 AI 决策助手", page_icon="🏆", layout="wide")

# ================= 获取 DeepSeek API Key =================
# ⚠️ 直接把下面引号里的字换成你真实的 DeepSeek 密钥（不要漏掉 sk-）
API_KEY = "sk-9daba59e4a44475fb1439c20c4ca7132" 

# 检查是否填对了
if "填入你真实的" in API_KEY:
    st.error("⚠️ 请先在代码中填入你真实的 DeepSeek API Key！")
    st.stop()

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# ================= 侧边栏 =================
with st.sidebar:
    st.title("🏆 关于本产品")
    st.markdown("""
    这是一个基于大模型和机器学习的**五大联赛决策助手**。
    
    **它具备什么能力？**
    - 📊 **数据洞察**：查积分榜、近期战绩、历史交锋。
    - 🤖 **AI 预测**：使用多联赛随机森林模型预测胜平负。
    - 📰 **情报检索**：自动分析球队最新伤停与状态新闻。
    - 🎲 **盘口对比**：抓取竞彩官方赔率并计算去水真实概率。
    """)
    st.divider()
    st.caption("Powered by ModelScope, DeepSeek & scikit-learn")

# ================= 主界面 =================
st.title("⚽ 五大联赛 AI 决策助手")
st.caption("你可以直接问我：曼城下一场打谁？结合新闻预测一下 / 意甲前四是谁 / 拜仁最近战绩如何")

# 初始化聊天记录
if "history" not in st.session_state:
    st.session_state.history = []

# 渲染历史记录
for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ================= Agent 核心循环 =================
def run_agent(user_input, history):
    messages = [
        {"role": "system", "content": 
            "你是一个顶级足球数据分析师。你可以调用工具查数据、预测比赛、检索伤停和查询赔率。"
            "【核心规则】："
            "1. 如果工具返回 `status: no_data`，说明该数据暂未收录。用分析师口吻说明缺失，并提示不确定性。"
            "2. 如果 `predict_match` 返回的 `note` 中包含'严重警告'或'缺乏历史数据'，你必须在回答开头声明：'该模型预测因数据缺失而失真，仅供参考'。"
            "3. 如果赔率获取失败，如实告知用户'由于服务器网络限制，未能获取实时赔率'。"
            "4. 【极重要 - 常识兜底】：如果模型概率因数据缺失而严重失真（比如升班马打豪门，模型给出50%对50%），你绝不能只念模型的数据！你必须结合你的足球常识（如球队真实实力、底蕴、联赛排名形势）去强势纠正它。告诉用户：'虽然模型因为缺乏数据给出了五五开，但实际上A队作为顶级豪门，实力绝对碾压B队，这个概率不可信，综合来看A队胜算极大'。""
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
        
        # 如果不需要调用工具，直接返回最终结果
        if not msg.tool_calls:
            return msg.content
        
        # 如果需要调用工具，把工具加入历史
        messages.append(msg)
        
        # 在界面上动态展示工具调用过程
        for tc in msg.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)
            
            friendly_names = {
                "predict_match": "正在计算比赛概率",
                "query_standings": "正在查询积分榜",
                "query_recent_form": "正在查询近期战绩",
                "query_head_to_head": "正在查询历史交锋",
                "query_league_table": "正在查询联赛排名",
                "query_team_matches": "正在查询赛程",
                "predict_next_match": "正在预测下一场比赛",
                "query_team_news": "正在检索最新伤停情报",
                "query_match_odds": "正在获取竞彩盘口数据"
            }
            status_text = friendly_names.get(func_name, f"正在调用 {func_name}")
            
            with st.status(f"{status_text}...", expanded=False) as status:
                func = TOOL_MAP.get(func_name)
                result = func(**args) if func else {"error": "未知工具"}
                status.update(label=f"{status_text} 完成", state="complete")
            
            messages.append({
                "role": "tool", 
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)
            })
            
    return "抱歉，这个问题我暂时处理不了。"

# ================= 接收输入 =================
if user_input := st.chat_input("输入你的问题…"):
    # 显示用户输入
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.history.append({"role": "user", "content": user_input})

    # 显示 Agent 回复
    with st.chat_message("assistant"):
        answer = run_agent(user_input, st.session_state.history[:-1])
        st.markdown(answer)

    # 保存 Agent 回复
    st.session_state.history.append({"role": "assistant", "content": answer})