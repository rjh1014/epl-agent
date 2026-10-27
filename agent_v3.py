import json
import pandas as pd
from openai import OpenAI
from predict_v2 import predict

API_KEY = 'sk-9daba59e4a44475fb1439c20c4ca7132'
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

ALIAS = {
    "利物浦": "Liverpool FC", "曼城": "Manchester City FC",
    "阿森纳": "Arsenal FC", "切尔西": "Chelsea FC",
    "曼联": "Manchester United FC", "热刺": "Tottenham Hotspur FC",
    "南安普顿": "Southampton FC", "纽卡斯尔": "Newcastle United FC",
    "维拉": "Aston Villa FC", "布莱顿": "Brighton & Hove Albion FC",
    "伯恩茅斯": "AFC Bournemouth", "布伦特福德": "Brentford FC",
    "富勒姆": "Fulham FC", "水晶宫": "Crystal Palace FC",
    "埃弗顿": "Everton FC", "西汉姆": "West Ham United FC",
    "狼队": "Wolverhampton Wanderers FC", "莱斯特城": "Leicester City FC",
    "伊普斯维奇": "Ipswich Town FC", "诺丁汉森林": "Nottingham Forest FC",
}

def resolve(name):
    name = name.strip()
    return ALIAS.get(name, name)

standings = pd.read_csv("standings.csv")
standings = standings.sort_values(['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)

matches = pd.read_csv("epl_matches.csv")
matches['date'] = pd.to_datetime(matches['date'])
matches = matches.sort_values('date').reset_index(drop=True)

def query_standings(team_name):
    team_en = resolve(team_name)
    row = standings[standings['team'] == team_en]
    if len(row) == 0:
        return {"error": f"没找到球队 {team_name}"}
    r = row.iloc[0]
    rank = row.index[0] + 1
    return {
        "team": r['team'], "rank": int(rank),
        "played": int(r['MP']), "win": int(r['W']), "draw": int(r['D']), "loss": int(r['L']),
        "goals_for": int(r['GF']), "goals_against": int(r['GA']),
        "goal_diff": int(r['GD']), "points": int(r['PTS']),
    }

def query_recent_form(team_name, n=5):
    team_en = resolve(team_name)
    played = matches[(matches['home'] == team_en) | (matches['away'] == team_en)]
    recent = played.tail(n)
    if len(recent) == 0:
        return {"error": f"没找到 {team_name} 的比赛记录"}

    games = []
    for _, r in recent.iterrows():
        if r['home'] == team_en:
            gf, ga, opponent, venue = int(r['hg']), int(r['ag']), r['away'], "主场"
        else:
            gf, ga, opponent, venue = int(r['ag']), int(r['hg']), r['home'], "客场"

        if gf > ga:
            res = "胜"
        elif gf == ga:
            res = "平"
        else:
            res = "负"

        games.append({
            "date": str(r['date'].date()),
            "opponent": opponent,
            "venue": venue,
            "score": f"{gf}-{ga}",
            "result": res,
        })

    return {"team": team_en, "recent_matches": games}

def query_head_to_head(team_a, team_b, limit=5):
    a = resolve(team_a)
    b = resolve(team_b)
    h2h = matches[
        ((matches['home'] == a) & (matches['away'] == b)) |
        ((matches['home'] == b) & (matches['away'] == a))
    ]
    if len(h2h) == 0:
        return {"error": f"没找到 {team_a} 和 {team_b} 的交锋记录"}

    a_wins = b_wins = draws = 0
    for _, r in h2h.iterrows():
        if r['home'] == a:
            a_goals, b_goals = int(r['hg']), int(r['ag'])
        else:
            a_goals, b_goals = int(r['ag']), int(r['hg'])
        if a_goals > b_goals:
            a_wins += 1
        elif a_goals < b_goals:
            b_wins += 1
        else:
            draws += 1

    games = []
    for _, r in h2h.tail(limit).iterrows():
        games.append({
            "date": str(r['date'].date()),
            "home": r['home'],
            "away": r['away'],
            "score": f"{int(r['hg'])}-{int(r['ag'])}",
            "winner": r['winner'],
        })

    return {
        "team_a": a, "team_b": b,
        "total_matches": len(h2h),
        "team_a_wins": a_wins, "team_b_wins": b_wins, "draws": draws,
        "recent_matches": games,
    }

def predict_match(home_team, away_team):
    try:
        return predict(resolve(home_team), resolve(away_team))
    except IndexError:
        return {"error": f"没找到球队 {home_team} 或 {away_team}"}

tools = [
    {
        "type": "function",
        "function": {
            "name": "predict_match",
            "description": "预测两支球队比赛的胜平负概率。当用户问谁赢、胜算、比赛预测时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "home_team": {"type": "string", "description": "主队名称，中文或英文均可"},
                    "away_team": {"type": "string", "description": "客队名称，中文或英文均可"},
                },
                "required": ["home_team", "away_team"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_standings",
            "description": "查询某支球队在英超积分榜上的排名、积分、胜平负、进失球。当用户问排名、积分、战绩时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_name": {"type": "string", "description": "球队名称，中文或英文均可"},
                },
                "required": ["team_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_recent_form",
            "description": "查询某支球队最近几场比赛的对手、比分和胜平负。当用户问近期状态、最近表现、连胜连败时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_name": {"type": "string", "description": "球队名称，中文或英文均可"},
                    "n": {"type": "integer", "description": "查询最近几场，默认5场"},
                },
                "required": ["team_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_head_to_head",
            "description": "查询两支球队的历史交锋记录，包括总交锋场次、各自胜场、平局和最近几场比分。当用户问两队历史交锋、过往战绩对比时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_a": {"type": "string", "description": "第一支球队，中文或英文均可"},
                    "team_b": {"type": "string", "description": "第二支球队，中文或英文均可"},
                    "limit": {"type": "integer", "description": "返回最近几场交锋记录，默认5场"},
                },
                "required": ["team_a", "team_b"],
            },
        },
    },
]

TOOL_MAP = {
    "predict_match": predict_match,
    "query_standings": query_standings,
    "query_recent_form": query_recent_form,
    "query_head_to_head": query_head_to_head,
}

def run_agent(user_input):
    messages = [
        {"role": "system", "content":
    "你是一个五大联赛足球数据分析助手，支持英超、西甲、德甲、意甲、法甲。"
    "你可以调用工具查询积分榜、近期战绩、历史交锋、预测比赛。"
    "用中文回答，简洁准确。不要编造工具没有返回的数据。"
    "如果用户问的球队不在五大联赛范围内，如实告知。"}
    ]

    for _ in range(5):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        messages.append(msg)

        for tc in msg.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)
            func = TOOL_MAP.get(func_name)
            if func is None:
                result = {"error": f"未知工具 {func_name}"}
            else:
                result = func(**args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    return "抱歉，这个问题我暂时处理不了。"

print("足球赛果决策 Agent v3（输入 '退出' 结束）")
print("可以问：利物浦现在第几 / 曼城打阿森纳谁赢 / 阿森纳最近5场战绩 / 利物浦和曼城历史交锋谁占优")
print()

while True:
    user_input = input("你：").strip()
    if user_input in ("退出", "quit", "exit"):
        print("Agent：再见。")
        break
    if not user_input:
        continue
    print("Agent：", run_agent(user_input))
    print()