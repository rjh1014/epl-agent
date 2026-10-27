# ⚽ 英超赛果决策 Agent

一个用自然语言提问的英超数据分析 Agent。你问"利物浦现在第几""曼城打阿森纳谁赢"，它会自动调用对应的工具查询数据、训练好的模型预测概率，并用中文回答。

**🔗 在线试用：** https://你的应用名.streamlit.app

> 把上面这行换成你实际的 Streamlit Cloud 地址。

## 它能回答什么

| 问题类型 | 示例 |
|---|---|
| 积分榜 | "利物浦现在积分榜第几" |
| 近期战绩 | "阿森纳最近5场战绩如何" |
| 历史交锋 | "利物浦和曼城历史交锋谁占优" |
| 比赛预测 | "曼城打阿森纳谁赢" |
| 复合问题 | "南安普顿最近状态怎么样，打曼联有戏吗" |

## 技术栈

- **数据**：football-data.org API（英超 2024 赛季 380 场比赛）
- **分析**：Pandas
- **模型**：scikit-learn 逻辑回归（按时间切分，无数据泄露）
- **Agent**：DeepSeek API Function Calling，四个工具自动分发
- **界面**：Streamlit
- **部署**：Streamlit Community Cloud

## 项目结构
├── tools.py # 四个工具函数 + Function Calling schema
├── predict_v2.py # 加载模型，输出胜平负概率
├── train_model_v2.py # 训练模型（按时间切分，避免数据泄露）
├── streamlit_app.py # 网页界面 + Agent 主循环
├── agent_v3.py # 命令行版 Agent（开发调试用）
├── standings.csv # 赛季积分榜
├── epl_matches.csv # 380 场比赛原始数据
├── model.pkl # 训练好的逻辑回归模型
└── requirements.txt # 依赖清单