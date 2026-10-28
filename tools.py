import os
import pandas as pd
from predict_v2 import predict

# 联赛代码 → 中文名，用于提示词和展示
LEAGUE_NAMES = {
    "PL": "英超", "PD": "西甲", "BL1": "德甲", "SA": "意甲", "FL1": "法甲",
}

# 球队中文别名 → 英文全名（扩充了五大联赛球队）
ALIAS = {
    # 英超
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
    # 西甲
    "皇马": "Real Madrid CF", "巴萨": "FC Barcelona",
    "马竞": "Club Atlético de Madrid", "比利亚雷亚尔": "Villarreal CF",
    "毕尔巴鄂": "Athletic Club", "皇家社会": "Real Sociedad",
    "贝蒂斯": "Real Betis", "塞维利亚": "Sevilla FC",
    # 德甲
    "拜仁": "FC Bayern München", "多特": "Borussia Dortmund",
    "勒沃库森": "Bayer 04 Leverkusen", "莱比锡": "RB Leipzig",
    "法兰克福": "Eintracht Frankfurt", "斯图加特": "VfB Stuttgart",
    # 意甲
    "国米": "Inter Milan", "AC米兰": "AC Milan",
    "尤文": "Juventus FC", "那不勒斯": "SSC Napoli",
    "罗马": "AS Roma", "拉齐奥": "SS Lazio", "亚特兰大": "Atalanta BC",
    # 法甲
    "巴黎": "Paris Saint-Germain FC", "马赛": "Olympique de Marseille",
    "摩纳哥": "AS Monaco FC", "里昂": "Olympique Lyonnais",
    "里尔": "LOSC Lille",
}

def resolve(name):
    return ALIAS.get(name.strip(), name.strip())

# 缓存：联赛代码 → (standings_df, matches_df)
_cache = {}

def _load_league(code):
    if code not in _cache:
        s_path = f"standings_{code}.csv"
        m_path = f"matches_{code}.csv"
        if not os.path.exists(s_path) or not os.path.exists(m_path):
            _cache[code] = (None, None)
        else:
            s = pd.read_csv(s_path).sort_values(['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)
            m = pd.read_csv(m_path)
            m['date'] = pd.to_datetime(m['date'])
            m = m.sort_values('date').reset_index(drop=True)
            _cache[code] = (s, m)
    return _cache[code]

def find_league(team_en):
    """根据英文队名，查找它出现在哪个联赛的数据里"""
    for code in LEAGUE_NAMES:
        s, _ = _load_league(code)
        if s is not None and team_en in s['team'].values:
            return code
    return None

def query_standings(team_name):
    team_en = resolve(team_name)
    code = find_league(team_en)
    if code is None:
        return {"error": f"没找到球队 {team_name}，它可能不在当前支持的五大联赛数据中。"}
    standings, _ = _load_league(code)
    row = standings[standings['team'] == team_en]
    r = row.iloc[0]
    return {
        "team": r['team'], "league": LEAGUE_NAMES.get(code, code),
        "rank": int(row.index[0] + 1),
        "played": int(r['MP']), "win": int(r['W']), "draw": int(r['D']), "loss": int(r['L']),
        "goals_for": int(r['GF']), "goals_against": int(r['GA']),
        "goal_diff": int(r['GD']), "points": int(r['PTS']),
    }

def query_recent_form(team_name, n=5):
    team_en = resolve(team_name)
    code = find_league(team_en)
    if code is None:
        return {"error": f"没找到球队 {team_name} 的比赛记录。"}
    _, matches = _load_league(code)
    played = matches[(matches['home'] == team_en) | (matches['away'] == team_en)]
    recent = played.tail(n)
    games = []
    for _, r in recent.iterrows():
        if r['home'] == team_en:
            gf, ga, opponent, venue = int(r['hg']), int(r['ag']), r['away'], "主场"
        else:
            gf, ga, opponent, venue = int(r['ag']), int(r['hg']), r['home'], "客场"
        res = "胜" if gf > ga else ("平" if gf == ga else "负")
        games.append({"date": str(r['date'].date()), "opponent": opponent,
                      "venue": venue, "score": f"{gf}-{ga}", "result": res})
    return {"team": team_en, "league": LEAGUE_NAMES.get(code, code), "recent_matches": games}

def query_head_to_head(team_a, team_b, limit=5):
    a, b = resolve(team_a), resolve(team_b)
    code_a = find_league(a)
    code_b = find_league(b)
    codes = [c for c in [code_a, code_b] if c is not None]
    if not codes:
        return {"error": f"没找到 {team_a} 或 {team_b} 的记录。"}
    h2h = pd.DataFrame()
    for code in set(codes):
        _, matches = _load_league(code)
        if matches is None:
            continue
        part = matches[
            ((matches['home'] == a) & (matches['away'] == b)) |
            ((matches['home'] == b) & (matches['away'] == a))
        ]
        h2h = pd.concat([h2h, part], ignore_index=True)
    h2h = h2h.drop_duplicates(subset=['date', 'home', 'away'])
    if len(h2h) == 0:
        return {"error": f"没找到 {team_a} 和 {team_b} 的交锋记录（可能不在同一联赛，或历史数据未覆盖）。"}
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
    home = resolve(home_team)
    away = resolve(away_team)
    code = find_league(home) or find_league(away)
    if code is None:
        return {"error": f"没找到球队 {home_team} 或 {away_team}。"}
    _, matches = _load_league(code)
    try:
        # 这里修复了传参错误，加上了 league_code=code
        return predict(home, away, league_code=code, matches=matches)
    except IndexError:
        return {"error": f"没找到球队 {home_team} 或 {away_team} 的比赛数据。"}

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
            "home_team": {"type": "string", "description": "主队名称，中文或英文均可"},
            "away_team": {"type": "string", "description": "客队名称，中文或英文均可"},
        }, "required": ["home_team", "away_team"]}}},
    {"type": "function", "function": {
        "name": "query_standings",
        "description": "查询球队在联赛积分榜上的排名、积分、胜平负、进失球。支持英超、西甲、德甲、意甲、法甲。",
        "parameters": {"type": "object", "properties": {
            "team_name": {"type": "string", "description": "球队名称，中文或英文均可"},
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