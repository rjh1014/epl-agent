import os
import json
import requests
import pandas as pd
from predict_v2 import predict

LEAGUE_NAMES = {"PL": "英超", "PD": "西甲", "BL1": "德甲", "SA": "意甲", "FL1": "法甲"}

# 球队中英文别名映射（供用户输入模糊匹配）
ALIAS = {
    "利物浦": "Liverpool FC", "红军": "Liverpool FC", "曼城": "Manchester City FC", "曼彻斯特城": "Manchester City FC", "蓝月亮": "Manchester City FC",
    "阿森纳": "Arsenal FC", "枪手": "Arsenal FC", "切尔西": "Chelsea FC", "蓝军": "Chelsea FC", "曼联": "Manchester United FC", "曼彻斯特联": "Manchester United FC", "红魔": "Manchester United FC",
    "热刺": "Tottenham Hotspur FC", "托特纳姆热刺": "Tottenham Hotspur FC", "纽卡斯尔": "Newcastle United FC", "维拉": "Aston Villa FC", "阿斯顿维拉": "Aston Villa FC", 
    "布莱顿": "Brighton & Hove Albion FC", "西汉姆": "West Ham United FC", "铁锤帮": "West Ham United FC", "狼队": "Wolverhampton Wanderers FC", "埃弗顿": "Everton FC", 
    "富勒姆": "Fulham FC", "水晶宫": "Crystal Palace FC", "布伦特福德": "Brentford FC", "莱斯特城": "Leicester City FC", "伊普斯维奇": "Ipswich Town FC", "诺丁汉森林": "Nottingham Forest FC",
    "皇马": "Real Madrid CF", "皇家马德里": "Real Madrid CF", "巴萨": "FC Barcelona", "巴塞罗那": "FC Barcelona", "马竞": "Club Atlético de Madrid", "马德里竞技": "Club Atlético de Madrid", 
    "比利亚雷亚尔": "Villarreal CF", "毕尔巴鄂": "Athletic Club", "皇家社会": "Real Sociedad", "贝蒂斯": "Real Betis", "塞维利亚": "Sevilla FC",
    "拜仁": "FC Bayern München", "拜仁慕尼黑": "FC Bayern München", "多特": "Borussia Dortmund", "多特蒙德": "Borussia Dortmund", "药厂": "Bayer 04 Leverkusen", 
    "勒沃库森": "Bayer 04 Leverkusen", "莱比锡": "RB Leipzig", "法兰克福": "Eintracht Frankfurt", "斯图加特": "VfB Stuttgart",
    "国米": "Inter Milan", "国际米兰": "Inter Milan", "AC米兰": "AC Milan", "尤文": "Juventus FC", "尤文图斯": "Juventus FC", "那不勒斯": "SSC Napoli", 
    "罗马": "AS Roma", "拉齐奥": "SS Lazio", "亚特兰大": "Atalanta BC",
    "巴黎": "Paris Saint-Germain FC", "大巴黎": "Paris Saint-Germain FC", "马赛": "Olympique de Marseille", "摩纳哥": "AS Monaco FC", "里昂": "Olympique Lyonnais", "里尔": "LOSC Lille",
}

# 专供竞彩网查询的标准官方中文名映射
STANDARD_CN = {
    "Liverpool FC": "利物浦", "Manchester City FC": "曼城", "Arsenal FC": "阿森纳", "Chelsea FC": "切尔西", "Manchester United FC": "曼联",
    "Tottenham Hotspur FC": "热刺", "Newcastle United FC": "纽卡斯尔", "Aston Villa FC": "维拉", "Brighton & Hove Albion FC": "布莱顿", 
    "West Ham United FC": "西汉姆", "Wolverhampton Wanderers FC": "狼队", "Everton FC": "埃弗顿", "Fulham FC": "富勒姆", 
    "Crystal Palace FC": "水晶宫", "Brentford FC": "布伦特福德", "Leicester City FC": "莱斯特城", "Ipswich Town FC": "伊普斯维奇", "Nottingham Forest FC": "诺丁汉森林",
    "Real Madrid CF": "皇马", "FC Barcelona": "巴萨", "Club Atlético de Madrid": "马竞", "Villarreal CF": "比利亚雷亚尔", 
    "Athletic Club": "毕尔巴鄂", "Real Sociedad": "皇家社会", "Real Betis": "贝蒂斯", "Sevilla FC": "塞维利亚",
    "FC Bayern München": "拜仁", "Borussia Dortmund": "多特", "Bayer 04 Leverkusen": "勒沃库森", "RB Leipzig": "莱比锡", 
    "Eintracht Frankfurt": "法兰克福", "VfB Stuttgart": "斯图加特",
    "Inter Milan": "国米", "AC Milan": "AC米兰", "Juventus FC": "尤文", "SSC Napoli": "那不勒斯", 
    "AS Roma": "罗马", "SS Lazio": "拉齐奥", "Atalanta BC": "亚特兰大",
    "Paris Saint-Germain FC": "巴黎", "Olympique de Marseille": "马赛", "AS Monaco FC": "摩纳哥", "Olympique Lyonnais": "里昂", "LOSC Lille": "里尔"
}

def resolve(name):
    name = name.strip()
    if name in ALIAS:
        return ALIAS[name]
    for code in LEAGUE_NAMES:
        s, _, _ = _load_league(code)
        if s is not None:
            for team in s['team'].values:
                if name.lower() in team.lower() or team.lower() in name.lower():
                    return team
    return name

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
    if code is None: return {"status": "no_data", "message": f"暂未收录 {team_name} 的积分榜数据。"}
    standings, _, _ = _load_league(code)
    row = standings[standings['team'] == team_en]
    r = row.iloc[0]
    return {"team": r['team'], "league": LEAGUE_NAMES.get(code, code), "rank": int(row.index[0] + 1),
            "played": int(r['MP']), "win": int(r['W']), "draw": int(r['D']), "loss": int(r['L']),
            "goals_for": int(r['GF']), "goals_against": int(r['GA']), "goal_diff": int(r['GD']), "points": int(r['PTS'])}

def query_recent_form(team_name, n=5):
    team_en = resolve(team_name); code = find_league(team_en)
    if code is None: return {"status": "no_data", "message": f"暂未收录 {team_name} 的近期战绩。"}
    _, matches, _ = _load_league(code)
    played = matches[(matches['home'] == team_en) | (matches['away'] == team_en)]
    if len(played) == 0: return {"status": "no_data", "message": f"暂未收录 {team_name} 的比赛记录。"}
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
    if not codes: return {"status": "no_data", "message": f"暂未收录 {team_a} 或 {team_b} 的数据，无法查阅交锋。"}
    h2h = pd.DataFrame()
    for code in set(codes):
        _, matches, _ = _load_league(code)
        if matches is None: continue
        part = matches[((matches['home'] == a) & (matches['away'] == b)) | ((matches['home'] == b) & (matches['away'] == a))]
        h2h = pd.concat([h2h, part], ignore_index=True)
    h2h = h2h.drop_duplicates(subset=['date', 'home', 'away'])
    if len(h2h) == 0: return {"status": "no_data", "message": f"两队近期暂无交锋记录。"}
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
    code = find_league(home) or find_league(away) or "PL"
    _, matches, _ = _load_league(code)
    try: 
        return predict(home, away, league_code=code, matches=matches)
    except Exception:
        X = pd.DataFrame([{"home_gf": 1.3, "home_ga": 1.3, "home_pts": 1.3, "home_recent": 1.3, "away_gf": 1.3, "away_ga": 1.3, "away_pts": 1.3, "away_recent": 1.3}])
        from predict_v2 import MODELS
        model = MODELS.get(code, MODELS.get("PL"))
        proba = model.predict_proba(X)[0]
        res = {cls: round(float(p), 2) for cls, p in zip(model.classes_, proba)}
        return {"home": home_team, "away": away_team, "league": code, "p_home": res.get("HOME_TEAM", 0.33), "p_draw": res.get("DRAW", 0.33), "p_away": res.get("AWAY_TEAM", 0.34), "note": "由于一方数据缺失，使用联赛平均水平进行估算。"}

def query_league_table(league_name, top_n=5):
    name_to_code = {v: k for k, v in LEAGUE_NAMES.items()}
    code = name_to_code.get(league_name.strip(), league_name.strip().upper())
    if code not in LEAGUE_NAMES: return {"status": "no_data", "message": f"不支持的联赛 {league_name}。"}
    standings, _, _ = _load_league(code)
    if standings is None: return {"status": "no_data", "message": f"找不到数据。"}
    result = [{"rank": i + 1, "team": r['team'], "points": int(r['PTS']), "played": int(r['MP']), "goal_diff": int(r['GD'])} for i, r in standings.head(top_n).iterrows()]
    return {"league": LEAGUE_NAMES[code], "top_n": top_n, "table": result}

def query_team_matches(team_name, limit=10):
    team_en = resolve(team_name); code = find_league(team_en)
    if code is None: return {"status": "no_data", "message": f"暂未收录 {team_name} 的赛程。"}
    _, matches, _ = _load_league(code)
    team_matches = matches[(matches['home'] == team_en) | (matches['away'] == team_en)]
    if len(team_matches) == 0: return {"status": "no_data", "message": f"暂未收录 {team_name} 的比赛记录。"}
    games = [{"date": str(r['date'].date()), "home": r['home'], "away": r['away'], "score": f"{int(r['hg'])}-{int(r['ag'])}"} for _, r in team_matches.tail(limit).iterrows()]
    return {"team": team_en, "recent_matches": games}

def predict_next_match(team_name):
    team_en = resolve(team_name); code = find_league(team_en)
    if code is None: return {"status": "no_data", "message": f"赛程库暂未收录 {team_name} 的未来赛程。"}
    _, matches, upcoming = _load_league(code)
    if upcoming is None: return {"status": "no_data", "message": f"暂无 {code} 的未来赛程数据。"}
    next_game = upcoming[(upcoming['home'] == team_en) | (upcoming['away'] == team_en)].head(1)
    if len(next_game) == 0: return {"status": "no_data", "message": f"赛程库里没有 {team_en} 接下来的比赛。"}
    r = next_game.iloc[0]
    h, a, date_val = r['home'], r['away'], str(r['date'].date())
    pred = predict_match(h, a)
    return {"match_date": date_val, "home": h, "away": a, "prediction": pred}

# ================= 接入真实 API 的 RAG 检索工具 =================
API_FOOTBALL_KEY = "a8b2fcc1bddf8cc9b3ddb234170da171"  # ⚠️ 记得换成你的真实Key

def query_team_news(team_name):
    team_en = resolve(team_name)
    try:
        with open("team_ids.json", "r", encoding="utf-8") as f:
            team_ids = json.load(f)
    except FileNotFoundError:
        return {"status": "no_data", "message": "伤停数据库加载失败。"}
    team_id = None
    for eng_name, tid in team_ids.items():
        if eng_name.lower() in team_en.lower() or team_en.lower() in eng_name.lower():
            team_id = tid; break
    if not team_id:
        return {"status": "no_data", "message": f"情报库暂未收录 {team_en} 的专项伤停数据。"}

    try:
        url = f"https://v3.football.api-sports.io/injuries?team={team_id}&season=2025"
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        resp = requests.get(url, headers=headers, timeout=5)
        data = resp.json()
        if data.get("results", 0) == 0:
            return {"status": "no_data", "message": f"当前没有 {team_en} 的最新伤停记录。"}
        news_items = [f"{i['player']['name']} ({i['player'].get('reason', '未知')})" for i in data["response"][:5]]
        return {"team": team_en, "news": "近期伤停名单：" + ", ".join(news_items)}
    except Exception:
        return {"status": "no_data", "message": "API 接口请求超时或异常。"}

# ================= 中国竞彩网官方赔率爬虫 =================
def query_match_odds(home_team, away_team):
    """查询中国竞彩网官方胜平负赔率，并计算去水公平概率"""
    home_en = resolve(home_team)
    away_en = resolve(away_team)
    
    # 使用标准中文名去匹配
    home_cn = STANDARD_CN.get(home_en, home_team)
    away_cn = STANDARD_CN.get(away_en, away_team)
    
    url = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry"
    params = {"channel": "c", "poolCode": "hhad,had"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.sporttery.cn/",
    }
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return {"status": "no_data", "message": f"竞彩接口请求失败，状态码：{resp.status_code}（云端服务器可能受IP限制）。"}
        
        data = resp.json()
        match_days = data.get("value", {}).get("matchInfoList", [])
        
        target_match = None
        for day in match_days:
            for m in day.get("subMatchList", []):
                h_name = m.get("homeTeamAllName", "")
                a_name = m.get("awayTeamAllName", "")
                
                # 使用标准中文名进行匹配
                if home_cn in h_name and away_cn in a_name:
                    target_match = m
                    break
            if target_match: break
            
        if not target_match:
            return {"status": "no_data", "message": f"今日竞彩列表中未找到 {home_cn} vs {away_cn} 的比赛（可能今日未开售此场）。"}
            
        had = target_match.get("had", {})
        if not had:
            return {"status": "no_data", "message": "该比赛暂无胜平负（had）赔率。"}
            
        odd_home = float(had.get("h"))
        odd_draw = float(had.get("d"))
        odd_away = float(had.get("a"))
        
        # 去水计算
        odds = [odd_home, odd_draw, odd_away]
        inv_sum = sum(1 / o for o in odds)
        fair_probs = [(1 / o) / inv_sum for o in odds]
        
        return {
            "match": f"{target_match.get('homeTeamAllName')} vs {target_match.get('awayTeamAllName')}",
            "source": "中国竞彩网官方",
            "raw_odds": {"home_win": odd_home, "draw": odd_draw, "away_win": odd_away},
            "fair_probabilities": {
                "home_win": round(fair_probs[0], 3),
                "draw": round(fair_probs[1], 3),
                "away_win": round(fair_probs[2], 3)
            },
            "note": "竞彩官方赔率，已去水。"
        }
        
    except Exception as e:
        return {"status": "no_data", "message": f"请求异常: {str(e)}"}

TOOL_MAP = {
    "predict_match": predict_match, "query_standings": query_standings,
    "query_recent_form": query_recent_form, "query_head_to_head": query_head_to_head,
    "query_league_table": query_league_table, "query_team_matches": query_team_matches,
    "predict_next_match": predict_next_match, "query_team_news": query_team_news,
    "query_match_odds": query_match_odds
}

TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "predict_match", "description": "预测两支球队比赛的胜平负概率。", "parameters": {"type": "object", "properties": {"home_team": {"type": "string"}, "away_team": {"type": "string"}}, "required": ["home_team", "away_team"]}}},
    {"type": "function", "function": {"name": "query_standings", "description": "查询单支球队的排名和积分。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "query_recent_form", "description": "查询某支球队最近几场的战绩。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}, "n": {"type": "integer"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "query_head_to_head", "description": "查询两支球队的历史交锋。", "parameters": {"type": "object", "properties": {"team_a": {"type": "string"}, "team_b": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["team_a", "team_b"]}}},
    {"type": "function", "function": {"name": "query_league_table", "description": "查询联赛前N名的积分榜。", "parameters": {"type": "object", "properties": {"league_name": {"type": "string"}, "top_n": {"type": "integer"}}, "required": ["league_name"]}}},
    {"type": "function", "function": {"name": "query_team_matches", "description": "查询某队最近的赛程比分。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "predict_next_match", "description": "预测某支球队下一场真实比赛的胜平负概率。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "query_team_news", "description": "检索某支球队的最新真实伤停情报。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "query_match_odds", "description": "查询中国竞彩网官方真实胜平负赔率，并计算去水后的市场公平概率。", "parameters": {"type": "object", "properties": {"home_team": {"type": "string"}, "away_team": {"type": "string"}}, "required": ["home_team", "away_team"]}}}
]