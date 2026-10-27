import pandas as pd
from predict_v2 import predict

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
    return ALIAS.get(name.strip(), name.strip())

_standings = None
_matches = None

def _load():
    global _standings, _matches
    if _standings is None:
        _standings = pd.read_csv("standings.csv")
        _standings = _standings.sort_values(['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)
    if _matches is None:
        _matches = pd.read_csv("epl_matches.csv")
        _matches['date'] = pd.to_datetime(_matches['date'])
        _matches = _matches.sort_values('date').reset_index(drop=True)
    return _standings, _matches

def query_standings(team_name):
    standings, _ = _load()
    team_en = resolve(team_name)
    row = standings[standings['team'] == team_en]
    if len(row) == 0:
        return {"error": f"没找到球队 {team_name}"}
    r = row.iloc[0]
    return {
        "team": r['team'], "rank": int(row.index[0] + 1),
        "played": int(r['MP']), "win": int(r['W']), "draw": int(r['D']), "loss": int(r['L']),
        "goals_for": int(r['GF']), "goals_against": int(r['GA']),
        "goal_diff": int(r['GD']), "points": int(r['PTS']),
    }

def query_recent_form(team_name, n=5):
    _, matches = _load()
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
        res = "胜" if gf > ga else ("平" if gf == ga else "负")
        games.append({"date": str(r['date'].date()), "opponent": opponent,
                      "venue": venue, "score": f"{gf}-{ga}", "result": res})
    return {"team": team_en, "recent_matches": games}

def query_head_to_head(team_a, team_b, limit=5):
    _, matches = _load()
    a, b = resolve(team_a), resolve(team_b)
    h2h = matches[
        ((matches['home'] == a) & (matches['away'] == b)) |
        ((matches['home'] == b) & (matches['away'] == a))
    ]
    if len(h2h) == 0:
        return {"error": f"没找到 {team_a} 和 {team_b} 的交锋记录"}
    a_wins = b_wins = draws = 0
    for _, r in h2h.iterrows():
        a_goals = int(r['hg']) if r['home'] == a else int(r['ag'])
        b_goals = int(r['ag']) if r['home'] == a else int(r['hg'])
        if a_goals > b_goals: a_wins += 1
        elif a_goals < b_goals: b_wins += 1
        else: draws += 1
    games = [{"date": str(r['date'].date()), "home": r['home'], "away": r['away'],
              "score": f"{int(r['hg'])}-{int(r['ag'])}", "winner": r['winner']}
             for _, r in h2h.tail(limit).iterrows()]
    return {"team_a": a, "team_b": b, "total_matches": len(h2h),
            "team_a_wins": a_wins, "team_b_wins": b_wins, "draws": draws,
            "recent_matches": games}

def predict_match(home_team, away_team):
    try:
        return predict(resolve(home_team), resolve(away_team))
    except IndexError:
        return {"error": f"没找到球队 {home_team} 或 {away_team}"}

TOOL_MAP = {
    "predict_match": predict_match,
    "query_standings": query_standings,
    "query_recent_form": query_recent_form,
    "query_head_to_head": query_head_to_head,
}

TOOLS_SCHEMA = [
    {"type": "function", "function": {
        "name": "predict_match",
        "description": "预测两支球队比赛的胜平负概率。当用户问谁赢、胜算、比赛预测时使用。",
        "parameters": {"type": "object", "properties": {
            "home_team": {"type": "string", "description": "主队名称"},
            "away_team": {"type": "string", "description": "客队名称"},
        }, "required": ["home_team", "away_team"]}}},
    {"type": "function", "function": {
        "name": "query_standings",
        "description": "查询球队在英超积分榜上的排名、积分、胜平负、进失球。",
        "parameters": {"type": "object", "properties": {
            "team_name": {"type": "string", "description": "球队名称"},
        }, "required": ["team_name"]}}},
    {"type": "function", "function": {
        "name": "query_recent_form",
        "description": "查询球队最近几场比赛的对手、比分和胜平负。",
        "parameters": {"type": "object", "properties": {
            "team_name": {"type": "string", "description": "球队名称"},
            "n": {"type": "integer", "description": "最近几场，默认5"},
        }, "required": ["team_name"]}}},
    {"type": "function", "function": {
        "name": "query_head_to_head",
        "description": "查询两支球队的历史交锋记录和最近比分。",
        "parameters": {"type": "object", "properties": {
            "team_a": {"type": "string", "description": "第一支球队"},
            "team_b": {"type": "string", "description": "第二支球队"},
            "limit": {"type": "integer", "description": "返回最近几场，默认5"},
        }, "required": ["team_a", "team_b"]}}},
]