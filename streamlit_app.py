import os
import json
import streamlit as st
from openai import OpenAI
from tools import TOOL_MAP, TOOLS_SCHEMA

# 页面配置
st.set_page_config(page_title="五大联赛 AI 决策助手", page_icon="🏆", layout="wide")

# 从 Streamlit Secrets 读取 Key
# 注意：变量名依然叫 DEEPSEEK_API_KEY，但里面填的是智谱的 Key
API_KEY = st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    st.error("没有找到 API_KEY。请在 Streamlit Secrets 中配置 DEEPSEEK_API_KEY（填入智谱 Key）。")
    st.stop()

# ================= 更换为智谱 GLM-4-Flash 接口 =================
client = OpenAI(
    api_key=API_KEY, 
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# ================= 侧边栏 =================
with st.sidebar:
    st.title("🏆 关于本产品")
    st.markdown("""
    这是一个基于大模型和机器学习的**五大联赛决策助手**。
    
    **它具备什么能力？**
    - 📊 **数据洞察**：查积分榜、近期战绩、历史交锋。
    - 🤖 **AI 预测**：使用多联赛随机森林模型预测胜平负。
    - 📰 **情报检索**：多源伤停情报（球小策/Live Football）。
    - 🎲 **盘口对比**：海外实时赔率与模型对比。
    - 🧠 **综合推理**：结合常识，强势纠正残缺数据。
    """)
    st.divider()
    st.caption("Powered by Streamlit, 智谱 GLM-4-Flash & scikit-learn")

# ================= 主界面 =================
st.title("⚽ 五大联赛 AI 决策助手")
st.caption("你可以直接问我：阿森纳有哪些伤停？/ 威尼斯打国米谁赢？/ 曼城下一场预测。")

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
            "1. 如果工具返回 `status: no_data`，用分析师口吻说明'情报库暂未覆盖'，并提示不确定性。"
            "2. 当用户询问伤停或首发时，优先调用 `query_team_intelligence` 工具，它会自动按优先级尝试多个数据源。"
            "3. 如果 `query_team_intelligence` 返回了 `source` 字段，请在回答中注明数据来源（如'据球小策数据'、'据Live Football API'）。"
            "4. 如果 `predict_match` 返回的 `note` 中包含'严重警告'，你必须在回答开头声明：'该模型预测因数据缺失而失真，仅供参考'。"
            "5. 如果赔率获取失败，如实告知用户。"
            "6. 【极重要-常识兜底】：如果模型概率因数据缺失而严重失真（比如升班马打豪门），你必须结合你的足球常识强势纠正它！告诉用户实际豪门胜算极大，模型概率不可信。"
        }
    ]
    messages += history
    messages.append({"role": "user", "content": user_input})

    for _ in range(5):
        try:
            # 使用智谱的 glm-4-flash 免费模型
            resp = client.chat.completions.create(
                model="glm-4-flash", 
                messages=messages, 
                tools=TOOLS_SCHEMA
            )
        except Exception as e:
            # 捕获大模型报错
            return f"⚠️ 大模型 API 报错，详细信息：{str(e)}"
            
        msg = resp.choices[0].message
        
        # 如果不需要调用工具，直接返回最终结果
        if not msg.tool_calls:
            return msg.content
        
        # 如果需要调用工具，把工具加入历史
        messages.append(msg)
        
        # 在界面上动态展示工具调用过程
        for tc in msg.tool_calls:
            func_name = tc.function.name
            
            try:
                args = json.loads(tc.function.arguments)
            except:
                args = {}
                
            friendly_names = {
                "predict_match": "正在计算比赛概率",
                "query_standings": "正在查询积分榜",
                "query_recent_form": "正在查询近期战绩",
                "query_head_to_head": "正在查询历史交锋",
                "query_league_table": "正在查询联赛排名",
                "query_team_matches": "正在查询赛程",
                "predict_next_match": "正在预测下一场比赛",
                "query_team_intelligence": "正在多源检索最新伤停情报",
                "query_match_odds": "正在获取实时赔率数据"
            }
            status_text = friendly_names.get(func_name, f"正在调用 {func_name}")
            
            with st.status(f"{status_text}...", expanded=False) as status:
                func = TOOL_MAP.get(func_name)
                if func:
                    try:
                        # 执行具体的 Python 函数
                        result = func(**args)
                    except Exception as e:
                        result = {"status": "error", "message": f"工具执行报错: {str(e)}"}
                else:
                    result = {"status": "error", "message": "未知工具"}
                status.update(label=f"{status_text} 完成", state="complete")
            
            # 将结果回传给大模型
            messages.append({
                "role": "tool", 
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)
            })
            
    return "抱歉，这个问题我暂时处理不了（超过最大工具调用轮数）。"

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