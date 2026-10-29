import os
import json
import re
import streamlit as st
from openai import OpenAI
from tools import TOOL_MAP, TOOLS_SCHEMA

# ================= 页面配置 =================
st.set_page_config(page_title="五大联赛 AI 决策助手", page_icon="🏆", layout="wide")

# ================= API 密钥配置 =================
# 优先从云端 Secrets 读取，这里依然用 DEEPSEEK_API_KEY 作为变量名，里面填智谱的 Key
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
    st.title("🏆 五大联赛 AI 决策助手")
    st.markdown("""
    这是一个基于大模型和机器学习的**足球盘口与赛果分析助手**。
    
    **核心能力：**
    - 📊 **数据洞察**：查积分榜、近期战绩、历史交锋。
    - 🤖 **AI 预测**：随机森林模型预测胜平负。
    - 📰 **多源情报**：实时伤停与首发阵容检索。
    - 🎲 **盘口推演**：将市场赔率与模型概率深度对比，推演亚洲让球盘口。
    """)
    st.divider()
    st.caption("Powered by Streamlit, 智谱 GLM-4-Flash & scikit-learn")

# ================= 主界面 =================
st.title("⚽ 五大联赛 AI 决策助手")
st.caption("你可以问：曼城打阿森纳，查一下盘口并预测一下 / 阿森纳有哪些伤停？")

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
            "你是一个顶级足球操盘手和数据分析师。你可以调用工具查数据、预测比赛、检索伤停和查询赔率。"
            "【核心规则】："
            "1. 如果工具返回 `status: no_data`，说明缺失，提示不确定性。"
            "2. 当用户询问伤停时，优先调用 `query_team_intelligence` 获取多源情报。"
            "3. 如果 `predict_match` 返回'严重警告'，你必须在回答开头声明该模型概率失真，仅供参考。"
            "4. 【极重要-常识兜底】：如果模型概率因数据缺失而失真（如升班马打豪门），必须结合足球常识强势纠正它！"
            "5. 【盘口推演】：当你调用了 `query_match_odds` 后，你必须完成以下深度分析："
            "   - 对比【模型预测概率】与【市场真实概率】的分歧。"
            "   - 根据胜平负概率推演一个合理的【亚洲让球盘口】（例如：主胜概率>60%，推演为让0.5球或1球；双方接近，推演为平手或平半）。"
            "   - 结合伤停情报，分析这个盘口是否合理（例如：'机构似乎没有把主队核心伤停计入盘口，存在诱盘嫌疑'）。"
            "6. 【前端渲染要求】：如果你输出了比赛胜平负概率，请务必在回答的最末尾加上一段隐藏的注释，不要用代码块包起来。格式严格如下："
            "<!--PROBS: 主胜=52,平局=24,客胜=24--> （请填入实际的百分比数字，不要带百分号）。"
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
                "query_match_odds": "正在获取实时赔率与盘口数据"
            }
            status_text = friendly_names.get(func_name, f"正在调用 {func_name}")
            
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
            
    return "抱歉，这个问题我暂时处理不了（超过最大工具调用轮数）。"

# ================= 接收输入与前端渲染 =================
if user_input := st.chat_input("输入你的问题…"):
    # 显示用户输入
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.history.append({"role": "user", "content": user_input})

    # 显示 Agent 回复
    with st.chat_message("assistant"):
        answer = run_agent(user_input, st.session_state.history[:-1])
        
        # 1. 使用正则表达式提取大模型隐藏在末尾的概率数据
        prob_match = re.search(r"<!--PROBS:\s*(.*?)\s*-->", answer)
        
        if prob_match:
            probs_str = prob_match.group(1)
            # 从原文本中删掉这段注释，避免用户看到丑陋的代码
            answer_clean = answer.replace(prob_match.group(0), "")
            st.markdown(answer_clean)
            
            # 解析概率并画可视化进度条
            try:
                probs = dict(item.split("=") for item in probs_str.split(","))
                p_home = int(probs.get("主胜", 0))
                p_draw = int(probs.get("平局", 0))
                p_away = int(probs.get("客胜", 0))
                
                st.markdown("#### 📊 胜平负预测可视化")
                col1, col2, col3 = st.columns(3)
                col1.metric("主队胜率", f"{p_home}%")
                col2.metric("平局概率", f"{p_draw}%")
                col3.metric("客队胜率", f"{p_away}%")
                
                # 用进度条直观展示
                st.progress(p_home / 100, text="主胜")
                st.progress(p_draw / 100, text="平局")
                st.progress(p_away / 100, text="客胜")
            except Exception:
                pass
        else:
            # 如果没有预测数据，正常显示文本
            st.markdown(answer)

    # 保存 Agent 回复
    st.session_state.history.append({"role": "assistant", "content": answer})