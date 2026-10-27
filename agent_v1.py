from predict import predict
from predict_v2 import predict

# 中文名 → CSV 里的英文全名
ALIAS = {
    "利物浦": "Liverpool FC",
    "曼城": "Manchester City FC",
    "阿森纳": "Arsenal FC",
    "切尔西": "Chelsea FC",
    "曼联": "Manchester United FC",
    "热刺": "Tottenham Hotspur FC",
    "南安普顿": "Southampton FC",
    "纽卡斯尔": "Newcastle United FC",
    "维拉": "Aston Villa FC",
    "布莱顿": "Brighton & Hove Albion FC",
}

def resolve(name):
    name = name.strip()
    if name in ALIAS:
        return ALIAS[name]
    return name  # 如果用户直接输入英文全名，原样返回

print("足球赛果决策 Agent v1（输入 '退出' 结束）")
print("示例：利物浦 对 曼城")
print()

while True:
    user_input = input("你：").strip()

    if user_input in ("退出", "quit", "exit"):
        print("Agent：再见。")
        break

    # 支持 "对" 和 "vs" 两种分隔
    if "对" in user_input:
        parts = user_input.split("对")
    elif "vs" in user_input.lower():
        parts = user_input.lower().split("vs")
    else:
        print("Agent：请用 'A 对 B' 的格式输入两支球队。")
        continue

    if len(parts) != 2:
        print("Agent：没看懂，请只输入两支球队。")
        continue

    home_raw, away_raw = parts[0].strip(), parts[1].strip()
    home = resolve(home_raw)
    away = resolve(away_raw)

    try:
        result = predict(home, away)
    except IndexError:
        print(f"Agent：没找到球队 '{home_raw}' 或 '{away_raw}'，请检查队名。")
        continue

    print(f"Agent：{result['home']} vs {result['away']}")
    print(f"  主胜 {result['p_home']:.0%} | 平局 {result['p_draw']:.0%} | 客胜 {result['p_away']:.0%}")
    print()