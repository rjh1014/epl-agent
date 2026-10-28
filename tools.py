import os
import json
import pandas as pd
from predict_v2 import predict

LEAGUE_NAMES = {"PL": "英超", "PD": "西甲", "BL1": "德甲", "SA": "意甲", "FL1": "法甲"}

ALIAS = {
    "利物浦": "Liverpool FC", "曼城": "Manchester City FC", "阿森纳": "Arsenal FC", "切尔西": "Chelsea FC",
    "曼联": "Manchester United FC", "热刺": "Tottenham Hotspur FC", "南安普顿": "Southampton FC", "纽卡斯尔": "Newcastle United FC",
    "维拉": "Aston Villa FC", "布莱顿": "Brighton & Hove Albion FC", "伯恩茅斯": "AFC Bournemouth", "布伦特福德": "Brentford FC",
    "富勒姆": "Fulham FC", "水晶宫": "Crystal Palace FC", "埃弗顿": "Everton FC", "西汉姆": "West Ham United FC",
    "狼队": "Wolverhampton Wanderers FC", "莱斯特城": "Leicester City FC", "伊普斯维奇": "Ipswich Town FC", "诺丁汉森林": "Nottingham Forest FC",
    "皇马": "Real Madrid CF", "巴萨": "FC Barcelona", "马竞": "Club Atlético de Madrid", "比利亚雷亚尔": "Villarreal CF",
    "毕尔巴鄂": "Athletic Club", "皇家社会": "Real Sociedad", "贝蒂斯": "Real Betis", "塞维利亚": "Sevilla FC",
    "拜仁": "FC Bayern München", "多特": "Borussia Dortmund", "勒沃库森": "Bayer 04 Leverkusen", "莱比锡": "RB Leipzig",
    "法兰克福": "Eintracht Frankfurt", "斯图加特": "VfB Stuttgart",
    "国米": "Inter Milan", "AC米兰": "AC Milan", "尤文": "Juventus FC", "那不勒斯": "SSC Napoli",
    "罗马": "AS Roma", "拉齐奥": "SS Lazio", "亚特兰大": "Atalanta BC",
    "巴黎": "Paris Saint-Germain FC", "马赛": "Olympique de Marseille", "摩纳哥": "AS Monaco FC", "里昂": "Olympique Lyonnais", "里尔": "LOSC Lille",
}

def resolve(name):
    return ALIAS.get(name.strip(), name.strip())

_cache = {}

def _load_league(code):
    if code not in _cache:
        s_path, m_path, u_path = f"standings_{code}.csv", f"matches_{code}.csv", f"upcoming_{code}.csv"
        s = pd.read_csv(s_path).sort_values(['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True) if os.path.exists(s_path) else None
        m = pd.read_csv(m_path) if os.path.exists(m_path) else None
        if m is not None: m['date'] = pd.to_datetime(m['date']); m = m.sort_values('date').reset_index(drop=True)
        u = pd.read_csv(u_path) if os.path.exists(u_path) else None
        if u is not None: u['date'] = pd.to_datetime(u['date']); u = u.sort_values('date').reset_index(drop=True)
        _cache[code] = (s, m, u)
    return _cache[code]

def find_league(team_en):
    for code in LEAGUE_NAMES:
        s, _, _ = _load_league(code)
        if s is not None and team_en in s['team'].values:
            return code
    return None

def query_standings(team_name):
    team_en = resolve(team_name); code = find_league(team_en)
    if code is None: return {"error": f"没找到球队 {team_name}。"}
    standings, _, _ = _load_league(code)
    row = standings[standings['team'] == team_en]
    r = row.iloc[0]
    return {"team": r['team'], "league": LEAGUE_NAMES.get(code, code), "rank": int(row.index[0] + 1),
            "played": int(r['MP']), "win": int(r['W']), "draw": int(r['D']), "loss": int(r['L']),
            "goals_for": int(r['GF']), "goals_against": int(r['GA']), "goal_diff": int(r['GD']), "points": int(r['PTS'])}

def query_recent_form(team_name, n=5):
    team_en = resolve(team_name); code = find_league(team_en)
    if code is None: return {"error": f"没找到球队 {team_name}。"}
    _, matches, _ = _load_league(code)
    played = matches[(matches['home'] == team_en) | (matches['away'] == team_en)]
    games = []
    for _, r in played.tail(n).iterrows():
        if r['home'] == team_en: gf, ga, opp, venue = int(r['hg']), int(r['ag']), r['away'], "主场"
        else: gf, ga, opp, venue = int(r['ag']), int(r['hg']), r['home'], "客场"
        res = "胜" if gf > ga else ("平" if gf == ga else "负")
        games.append({"date": str(r['date'].date()), "opponent": opp, "venue": venue, "score": f"{gf}-{ga}", "result": res})
    return {"team": team_en, "league": LEAGUE_NAMES.get(code, code), "recent_matches": games}

def query_head_to_head(team_a, team_b, limit=5):
    a, b = resolve(team_a), resolve(team_b)
    code_a, code_b = find_league(a), find_league(b)
    codes = [c for c in [code_a, code_b] if c is not None]
    if not codes: return {"error": f"没找到 {team_a} 或 {team_b}。"}
    h2h = pd.DataFrame()
    for code in set(codes):
        _, matches, _ = _load_league(code)
        if matches is None: continue
        part = matches[((matches['home'] == a) & (matches['away'] == b)) | ((matches['home'] == b) & (matches['away'] == a))]
        h2h = pd.concat([h2h, part], ignore_index=True)
    h2h = h2h.drop_duplicates(subset=['date', 'home', 'away'])
    if len(h2h) == 0: return {"error": f"没找到交锋记录。"}
    a_wins = b_wins = draws = 0
    for _, r in h2h.iterrows():
        ag = int(r['hg']) if r['home'] == a else int(r['ag'])
        bg = int(r['ag']) if r['home'] == a else int(r['hg'])
        if ag > bg: a_wins += 1
        elif ag < bg: b_wins += 1
        else: draws += 1
    games = [{"date": str(r['date'].date()), "home": r['home'], "away": r['away'], "score": f"{int(r['hg'])}-{int(r['ag'])}", "winner": r['winner']} for _, r in h2h.tail(limit).iterrows()]
    return {"team_a": a, "team_b": b, "total_matches": len(h2h), "team_a_wins": a_wins, "team_b_wins": b_wins, "draws": draws, "recent_matches": games}

def predict_match(home_team, away_team):
    home, away = resolve(home_team), resolve(away_team)
    code = find_league(home) or find_league(away)
    if code is None: return {"error": f"没找到球队。"}
    _, matches, _ = _load_league(code)
    try: return predict(home, away, league_code=code, matches=matches)
    except IndexError: return {"error": f"没找到比赛数据。"}

def query_league_table(league_name, top_n=5):
    name_to_code = {v: k for k, v in LEAGUE_NAMES.items()}
    code = name_to_code.get(league_name.strip(), league_name.strip().upper())
    if code not in LEAGUE_NAMES: return {"error": f"不支持的联赛 {league_name}"}
    standings, _, _ = _load_league(code)
    if standings is None: return {"error": f"找不到数据。"}
    result = [{"rank": i + 1, "team": r['team'], "points": int(r['PTS']), "played": int(r['MP']), "goal_diff": int(r['GD'])} for i, r in standings.head(top_n).iterrows()]
    return {"league": LEAGUE_NAMES[code], "top_n": top_n, "table": result}

def query_team_matches(team_name, limit=10):
    team_en = resolve(team_name); code = find_league(team_en)
    if code is None: return {"error": f"没找到球队 {team_name}。"}
    _, matches, _ = _load_league(code)
    team_matches = matches[(matches['home'] == team_en) | (matches['away'] == team_en)]
    games = [{"date": str(r['date'].date()), "home": r['home'], "away": r['away'], "score": f"{int(r['hg'])}-{int(r['ag'])}"} for _, r in team_matches.tail(limit).iterrows()]
    return {"team": team_en, "recent_matches": games}

def predict_next_match(team_name):
    team_en = resolve(team_name); code = find_league(team_en)
    if code is None: return {"error": f"没找到球队 {team_name}。"}
    _, matches, upcoming = _load_league(code)
    if upcoming is None: return {"error": f"没有找到 {code} 的未来赛程数据。"}
    next_game = upcoming[(upcoming['home'] == team_en) | (upcoming['away'] == team_en)].head(1)
    if len(next_game) == 0: return {"error": f"赛程库里没有 {team_en} 接下来的比赛。"}
    r = next_game.iloc[0]
    h, a, date = r['home'], r['away'], str(r['date'].date())
    pred = predict(h, a, league_code=code, matches=matches)
    return {"match_date": date, "home": h, "away": a, "prediction": {"p_home": pred['p_home'], "p_draw": pred['p_draw'], "p_away": pred['p_away']}}

# ================= 新增 RAG 检索工具 =================
def query_team_news(team_name):
    """从本地知识库检索该球队的最新新闻动态"""
    team_en = resolve(team_name)
    try:
        with open("news_db.json", "r", encoding="utf-8") as f:
            news_data = json.load(f)
    except FileNotFoundError:
        return {"error": "新闻数据库文件 news_db.json 不存在"}
    
    # 简单搜索：看哪条新闻的 team 字段包含当前队名
    results = [item["news"] for item in news_data if team_en.lower() in item["team"].lower()]
    
    if not results:
        return {"team": team_en, "news": "近期没有查到这支球队的特殊新闻或伤停情况，状态正常。"}
    
    return {"team": team_en, "news": " | ".join(results)}

TOOL_MAP = {
    "predict_match": predict_match, "query_standings": query_standings,
    "query_recent_form": query_recent_form, "query_head_to_head": query_head_to_head,
    "query_league_table": query_league_table, "query_team_matches": query_team_matches,
    "predict_next_match": predict_next_match,
    "query_team_news": query_team_news  # 注册新工具
}

TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "predict_match", "description": "预测两支球队比赛的胜平负概率。", "parameters": {"type": "object", "properties": {"home_team": {"type": "string"}, "away_team": {"type": "string"}}, "required": ["home_team", "away_team"]}}},
    {"type": "function", "function": {"name": "query_standings", "description": "查询单支球队的排名和积分。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "query_recent_form", "description": "查询某支球队最近几场的战绩。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}, "n": {"type": "integer"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "query_head_to_head", "description": "查询两支球队的历史交锋。", "parameters": {"type": "object", "properties": {"team_a": {"type": "string"}, "team_b": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["team_a", "team_b"]}}},
    {"type": "function", "function": {"name": "query_league_table", "description": "查询联赛前N名的积分榜。", "parameters": {"type": "object", "properties": {"league_name": {"type": "string"}, "top_n": {"type": "integer"}}, "required": ["league_name"]}}},
    {"type": "function", "function": {"name": "query_team_matches", "description": "查询某队最近的赛程比分。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "predict_next_match", "description": "预测某支球队下一场真实比赛的胜平负概率。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}}, "required": ["team_name"]}}},
    # 告诉大模型，遇到需要查新闻时调用它
    {"type": "function", "function": {"name": "query_team_news", "description": "检索某支球队的最新新闻、伤病情况或突发状况。当需要了解场外因素、伤停情报时使用。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string", "description": "球队名称"}}, "required": ["team_name"]}}}
]