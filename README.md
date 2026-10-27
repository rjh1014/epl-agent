# EPL Prediction Agent

一个英超赛果分析与预测的 AI Agent。用自然语言提问，Agent 自动调用工具查询数据、预测比赛。

## 功能

- 查积分榜排名、积分、胜平负
- 查球队最近 N 场战绩
- 查两队历史交锋记录
- 预测比赛胜平负概率（逻辑回归模型）

## 技术栈

- Python / Pandas / scikit-learn
- DeepSeek API（Function Calling）
- Streamlit（网页界面）

## 运行方式

1. 安装依赖：`pip install -r requirements.txt`
2. 在 `.env` 里填入 `DEEPSEEK_API_KEY=sk-...`
3. 启动：`python -m streamlit run streamlit_app.py`

## 项目结构

- `tools.py` — 四个工具函数 + Function Calling schema
- `predict_v2.py` — 加载模型并输出概率
- `train_model_v2.py` — 训练模型（无数据泄露版）
- `streamlit_app.py` — 网页界面
- `standings.csv` / `epl_matches.csv` — 赛季数据