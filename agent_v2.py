import json
from openai import OpenAI
from predict_v2 import predict

API_KEY = 'sk-9daba59e4a44475fb1439c20c4ca7132'
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

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
    "伯恩茅斯": "AFC Bournemouth",
    "布伦特福德": "Brentford FC",
    "富勒姆": "Fulham FC",
    "水晶宫": "Crystal Palace FC",
    "埃弗顿": "Everton FC",
    "西汉姆": "West Ham United FC",
    "狼队": "Wolverhampton Wanderers FC",
    "莱斯特城": "Leicester City FC",
    "伊普斯维奇": "Ipswich Town FC",
    "诺丁汉森林": "Nottingham Forest FC",
}

def parse_match(user_input):
    """让大模型从自然语言里提取主队和客队"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content":
                "你是一个足球比赛解析器。从用户输入中提取主队和客队。"
                "只返回JSON，格式：{\"home\": \"主队中文名\", \"away\": \"客队中文名\"}。"
                "如果用户没说清是哪两支球队，返回 {\"error\": \"原因\"}。"
                "不要返回任何其他文字。"},
            {"role": "user", "content": user_input},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

def resolve(name):
    name = name.strip()
    if name in ALIAS:
        return ALIAS[name]
    return name

print("足球赛果决策 Agent v2（输入 '退出' 结束）")
print("你现在可以随便问，比如：'曼城下一场打利物浦胜算大吗'")
print()

while True:
    user_input = input("你：").strip()

    if user_input in ("退出", "quit", "exit"):
        print("Agent：再见。")
        break

    parsed = parse_match(user_input)

    if "error" in parsed:
        print(f"Agent：{parsed['error']}")
        continue

    home = resolve(parsed.get("home", ""))
    away = resolve(parsed.get("away", ""))

    try:
        result = predict(home, away)
    except IndexError:
        print(f"Agent：数据库里没找到 '{parsed.get('home')}' 或 '{parsed.get('away')}'，请换个说法。")
        continue

    # 让大模型把概率翻译成一句自然语言解释
    explanation = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个足球分析助手。根据给定的概率，用一句简洁的中文告诉用户哪队更可能赢。不要编造额外信息。"},
            {"role": "user", "content":
                f"{result['home']} 对 {result['away']}，"
                f"主胜 {result['p_home']:.0%}，平局 {result['p_draw']:.0%}，客胜 {result['p_away']:.0%}。"
                f"请用一句话总结。"},
        ],
    ).choices[0].message.content

    print(f"Agent：{result['home']} vs {result['away']}")
    print(f"  主胜 {result['p_home']:.0%} | 平局 {result['p_draw']:.0%} | 客胜 {result['p_away']:.0%}")
    print(f"  {explanation}")
    print()