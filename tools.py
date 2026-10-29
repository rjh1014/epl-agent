import os
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from qiuxiaoce import QiuXiaoCeClient
from predict_v2 import predict

# ================= API 密钥配置 =================
# 优先从云端 Secrets 读取，读不到则使用备用 Key（注意字符串必须带引号）
QIUXIAOCE_API_KEY = os.getenv("a8b2fcc1bddf8cc9b3ddb234170da171", "填入你的球小策Key备用")
PINNWIRE_API_KEY = os.getenv("PINNWIRE_API_KEY", "demo")
LIVE_FOOTBALL_API_KEY = os.getenv("a69c07b21ede3b3c84fbb57d2394d1c36fb62d5839312afc77ff2fd980e11fd6", "填入你的LiveFootballAPI_Key")

qxc_client = QiuXiaoCeClient(api_key=QIUXIAOCE_API_KEY)

LEAGUE_NAMES = {"PL": "英超", "PD": "西甲", "BL1": "德甲", "SA": "意甲", "FL1": "法甲"}

# ================= 球队中英文映射 =================
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
    "国米": "Inter Milan", "国际米兰": "Inter Milan", "Inter": "Inter Milan", "Inter Milan": "Inter Milan", 
    "AC米兰": "AC Milan", "尤文": "Juventus FC", "尤文图斯": "Juventus FC", "那不勒斯": "SSC Napoli", 
    "罗马": "AS Roma", "拉齐奥": "SS Lazio", "亚特兰大": "Atalanta BC", "威尼斯": "Venezia FC",
    "巴黎": "Paris Saint-Germain FC", "大巴黎": "Paris Saint-Germain FC", "马赛": "Olympique de Marseille", "摩纳哥": "AS Monaco FC", "里昂": "Olympique Lyonnais", "里尔": "LOSC Lille",
}

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
    "AS Roma": "罗马", "SS Lazio": "拉齐奥", "Atalanta BC": "亚特兰大", "Venezia FC": "威尼斯",
    "Paris Saint-Germain FC": "巴黎", "Olympique de Marseille": "马赛", "AS Monaco FC": "摩纳哥", "Olympique Lyonnais": "里昂", "LOSC Lille": "里尔"
}

def resolve(name):
    name = name.strip()
    if name in ALIAS: return ALIAS[name]
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
    if len(row) == 0: return {"status": "no_data", "message": f"积分榜中未找到 {team_en}。"}
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
    if not codes: return {"status": "no_data", "message": f"暂未收录 {team_a} 或 {team_b} 的数据。"}
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
    code = find_league(home) or find_league(away)
    if not code:
        serie_a_teams = ["Inter Milan", "AC Milan", "Juventus FC", "SSC Napoli", "AS Roma", "SS Lazio", "Atalanta BC", "Venezia FC"]
        if home in serie_a_teams or away in serie_a_teams: code = "SA"
        else: code = "PL"

    _, matches, _ = _load_league(code)
    try: 
        return predict(home, away, league_code=code, matches=matches)
    except Exception:
        X = pd.DataFrame([{"home_gf": 1.3, "home_ga": 1.3, "home_pts": 1.3, "home_recent": 1.3, "away_gf": 1.3, "away_ga": 1.3, "away_pts": 1.3, "away_recent": 1.3}])
        from predict_v2 import MODELS
        model = MODELS.get(code, MODELS.get("PL"))
        proba = model.predict_proba(X)[0]
        res = {cls: round(float(p), 2) for cls, p in zip(model.classes_, proba)}
        return {"home": home, "away": away, "league": code, "p_home": res.get("HOME_TEAM", 0.33), "p_draw": res.get("DRAW", 0.33), "p_away": res.get("AWAY_TEAM", 0.34), "note": f"⚠️ 严重警告：{home} 或 {away} 缺乏历史数据，模型使用了 {LEAGUE_NAMES[code]} 的基准保底数据进行强行估算，该概率严重失真，不具备参考价值。"}

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

# ================= 多源情报查询工具 =================
def query_team_intelligence(team_name):
    """
    多源情报查询（优先级：球小策 -> Live Football API -> 雷速体育）
    返回格式：{"source": "...", "injuries": [...], "lineups": [...]}
    """
    team_en = resolve(team_name)
    
    # -------- 优先级 1: 球小策 --------
    try:
        search_name = team_en.replace("FC", "").replace("CF", "").strip()
        teams = qxc_client.search_teams(search_name)
        if teams:
            qxc_team_id = teams[0]["team_id"]
            fixtures = qxc_client.get_fixtures(team_id=qxc_team_id, season=2026)
            if not fixtures:
                fixtures = qxc_client.get_fixtures(team_id=qxc_team_id, season=2024)
            
            if fixtures:
                upcoming = [f for f in fixtures if f.get("status") in ("NS", "TBD", "未开始")]
                target_match = upcoming[0] if upcoming else fixtures[-1]
                fixture_id = target_match["fixture_id"]
                
                pack_data = qxc_client.get_match_pack(fixture_id=fixture_id)
                pack = pack_data.get("pack", {})
                injuries = pack.get("injuries") or pack.get("missing_players") or pack.get("lineups_injuries")
                
                if injuries:
                    if isinstance(injuries, list):
                        inj_list = [f"{i.get('player_name', '未知')} ({i.get('reason', '未知')})" for i in injuries[:8]]
                    elif isinstance(injuries, dict):
                        inj_list = [f"主队：{injuries.get('home', [])}", f"客队：{injuries.get('away', [])}"]
                    else:
                        inj_list = [str(injuries)]
                    return {"source": "球小策", "injuries": inj_list, "lineups": []}
    except Exception:
        pass  # 静默失败，尝试下一个源

    # -------- 优先级 2: Live Football API --------
    try:
        from datetime import date
        today = date.today().isoformat()
        match_url = f"https://live-football-api.com/api/v1/matches?api_key={LIVE_FOOTBALL_API_KEY}&date={today}&lang=en"
        match_resp = requests.get(match_url, timeout=10)
        
        match_id = None
        if match_resp.status_code == 200:
            matches = match_resp.json().get("data", {}).get("matches", [])
            for m in matches:
                h_name = m.get("home_team", "").lower()
                a_name = m.get("away_team", "").lower()
                h_word = team_en.split()[0].lower()
                if h_word in h_name or h_word in a_name:
                    match_id = m.get("id")
                    break
        
        if match_id:
            inj_url = f"https://live-football-api.com/api/v1/injuries?api_key={LIVE_FOOTBALL_API_KEY}&match_id={match_id}&lang=en"
            inj_resp = requests.get(inj_url, timeout=10)
            inj_list = []
            if inj_resp.status_code == 200:
                inj_data = inj_resp.json().get("data", {})
                for side in ["home", "away"]:
                    for p in inj_data.get(side, []):
                        inj_list.append(f"{p.get('player')} — {p.get('reason')} ({p.get('status')})")
            
            lin_url = f"https://live-football-api.com/api/v1/lineups?api_key={LIVE_FOOTBALL_API_KEY}&match_id={match_id}&lang=en"
            lin_resp = requests.get(lin_url, timeout=10)
            lin_list = []
            if lin_resp.status_code == 200:
                lin_data = lin_resp.json().get("data", {})
                home_xi = [p.get('name') for p in lin_data.get('home', {}).get('starting_xi', [])]
                away_xi = [p.get('name') for p in lin_data.get('away', {}).get('starting_xi', [])]
                if home_xi or away_xi:
                    lin_list = [f"主队首发：{', '.join(home_xi)}", f"客队首发：{', '.join(away_xi)}"]
            
            if inj_list or lin_list:
                return {"source": "Live Football API", "injuries": inj_list, "lineups": lin_list}
    except Exception:
        pass

    # -------- 优先级 3: 雷速体育（示意框架） --------
    # 因为雷速反爬严，这里暂留空。未来如果前两个接口都失效，可以在此引入 Playwright。
    try:
        pass
    except Exception:
        pass

    # -------- 全部失败 --------
    return {"status": "no_data", "message": "所有情报源均未返回有效数据。"}

# ================= 真实赔率查询（InferSports + pinnwire） =================
def query_match_odds(home_team, away_team):
    home_en = resolve(home_team)
    away_en = resolve(away_team)
    
    # ---------- 尝试方案一：InferSports ----------
    try:
        find_url = "https://api.infersports.dev/v1/mcp/find_match"
        find_payload = {"query": f"{home_en} {away_en}"}
        resp = requests.post(find_url, json=find_payload, timeout=10)
        
        if resp.status_code == 200:
            find_data = resp.json()
            event_id = find_data.get("event_id")
            
            if event_id:
                odds_url = f"https://api.infersports.dev/v1/events/{event_id}/odds?format=decimal"
                resp_odds = requests.get(odds_url, timeout=10)
                
                if resp_odds.status_code == 200:
                    odds_data = resp_odds.json()
                    fair_probs = odds_data.get("fair_probabilities", {})
                    if fair_probs and all(k in fair_probs for k in ["home", "draw", "away"]):
                        return {
                            "match": f"{home_en} vs {away_en}",
                            "source": "InferSports (免注册)",
                            "fair_probabilities": {
                                "home_win": round(fair_probs["home"], 3),
                                "draw": round(fair_probs["draw"], 3),
                                "away_win": round(fair_probs["away"], 3)
                            },
                            "note": "数据来自 InferSports 实时市场，已去水。"
                        }
    except Exception:
        pass

    # ---------- 尝试方案二：pinnwire ----------
    try:
        fixture_url = f"https://pinnwire.com/api/v1/prematch/fixtures?sport_id=1&key={PINNWIRE_API_KEY}"
        resp_fix = requests.get(fixture_url, timeout=10)
        
        if resp_fix.status_code == 200:
            fixtures = resp_fix.json().get("fixtures", [])
            
            for fx in fixtures:
                home_name = fx.get("home_team", "").lower()
                away_name = fx.get("away_team", "").lower()
                
                h_word = home_en.split()[0].lower()
                a_word = away_en.split()[0].lower()
                
                if (h_word in home_name or home_name in home_en.lower()) and \
                   (a_word in away_name or away_name in away_en.lower()):
                    
                    event_id = fx.get("event_id")
                    if event_id:
                        odds_url = f"https://pinnwire.com/api/v1/prematch/lines/{event_id}?key={PINNWIRE_API_KEY}"
                        resp_odds = requests.get(odds_url, timeout=10)
                        
                        if resp_odds.status_code == 200:
                            odds_data = resp_odds.json()
                            fair_probs = odds_data.get("no_vig_probabilities", {})
                            if fair_probs and all(k in fair_probs for k in ["home", "draw", "away"]):
                                return {
                                    "match": f"{fx.get('home_team')} vs {fx.get('away_team')}",
                                    "source": "pinnwire (Pinnacle 去水赔率)",
                                    "fair_probabilities": {
                                        "home_win": round(fair_probs["home"], 3),
                                        "draw": round(fair_probs["draw"], 3),
                                        "away_win": round(fair_probs["away"], 3)
                                    },
                                    "note": "数据来自 pinnwire 实时 Pinnacle 市场，已去水。"
                                }
    except Exception:
        pass

    return {"status": "no_data", "message": "当前未能从 InferSports 或 pinnwire 获取到该场比赛的实时赔率，请稍后重试。"}

TOOL_MAP = {
    "predict_match": predict_match, "query_standings": query_standings,
    "query_recent_form": query_recent_form, "query_head_to_head": query_head_to_head,
    "query_league_table": query_league_table, "query_team_matches": query_team_matches,
    "predict_next_match": predict_next_match, "query_team_intelligence": query_team_intelligence,
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
    {"type": "function", "function": {"name": "query_team_intelligence", "description": "查询某支球队的最新伤停情报和预测首发阵容（多源容错）。", "parameters": {"type": "object", "properties": {"team_name": {"type": "string", "description": "球队名称，中文或英文均可"}}, "required": ["team_name"]}}},
    {"type": "function", "function": {"name": "query_match_odds", "description": "查询海外真实博彩赔率（InferSports / pinnwire）。", "parameters": {"type": "object", "properties": {"home_team": {"type": "string"}, "away_team": {"type": "string"}}, "required": ["home_team", "away_team"]}}}
]