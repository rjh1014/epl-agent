# 🏆 五大联赛 AI 赛果决策助手

一个基于大模型（LLM）与机器学习（Random Forest）的足球数据分析 Agent。

你只需用自然语言提问，Agent 会自动调用工具查询五大联赛数据、预测比赛概率，并结合 **RAG（检索增强生成）** 技术，检索最新的球队伤停与状态新闻，最终给出带有场外因素综合判断的专业结论。

**在线试用：** https://你的应用名.streamlit.app

*(请将上面的链接替换为你的实际部署链接)*

## 🌟 核心功能

- **📊 数据洞察**：查询英超、西甲、德甲、意甲、法甲的积分榜、近期战绩、历史交锋。
- **🤖 AI 预测**：使用多联赛随机森林模型，预测任意两支球队交锋的胜平负概率。
- **🔮 赛程预测**：自动寻找某支球队的“下一场比赛”，并给出预测。
- **📰 情报检索 (RAG)**：在预测前，自动检索该球队的最新新闻、伤病名单与停赛情况。
- **🧠 综合推理**：结合数据概率与新闻情报，对模型结果进行人为修正（如：主力前锋受伤，胜率下调）。
- **💻 动态 UI**：侧边栏知识库展示，实时的工具调用状态提示。

## 🛠️ 技术栈

- **大模型 Agent**：DeepSeek API (Function Calling)
- **机器学习**：scikit-learn (随机森林 / 逻辑回归自动择优)
- **RAG 技术**：本地 JSON 知识库检索
- **数据处理**：Pandas
- **前端框架**：Streamlit
- **数据源**：football-data.org API

## 📁 项目结构

- `streamlit_app.py`：Web 聊天界面 + Agent 主循环 + UI 状态管理
- `tools.py`：核心工具函数（数据查询、预测、RAG 检索）及 Function Calling Schema
- `predict_v2.py`：加载多联赛模型，输出胜平负概率
- `train_multi_leagues.py`：多联赛模型训练脚本（按时间切分，无数据泄露）
- `fetch_multi_leagues.py`：从 API 获取五大联赛历史数据与未来赛程
- `news_db.json`：本地新闻知识库（RAG 检索源）
- `models_multi.pkl`：训练好的多联赛模型包
- `matches_*.csv` / `standings_*.csv` / `upcoming_*.csv`：数据文件

## 💻 本地运行

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
