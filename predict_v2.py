import pickle
import pandas as pd

with open("models_multi.pkl", "rb") as f:
    MODELS = pickle.load(f)

def _team_stats_from_matches(matches, team):
    played = matches[(matches['home'] == team) | (matches['away'] == team)]
    if len(played) == 0:
        return 1.3, 1.3, 1.3, 1.3
    
    gf = ga = pts = 0
    history = []
    
    for _, r in played.iterrows():
        if r['home'] == team:
            t_gf, t_ga = int(r['hg']), int(r['ag'])
        else:
            t_gf, t_ga = int(r['ag']), int(r['hg'])
            
        t_pts = 3 if t_gf > t_ga else (1 if t_gf == t_ga else 0)
        gf += t_gf
        ga += t_ga
        pts += t_pts
        history.append(t_pts)
        
    n = len(played)
    avg_gf, avg_ga, avg_pts = gf / n, ga / n, pts / n
    
    recent = history[-5:]
    recent_pts = sum(recent) / len(recent)
    
    return avg_gf, avg_ga, avg_pts, recent_pts

def predict(home_team, away_team, league_code="PL", matches=None):
    if league_code not in MODELS:
        return {"error": f"联赛 {league_code} 还没有训练好的模型"}
    model = MODELS[league_code]

    if matches is None:
        matches = pd.read_csv(f"matches_{league_code}.csv")
        matches['date'] = pd.to_datetime(matches['date'])
        matches = matches.sort_values('date').reset_index(drop=True)

    h_gf, h_ga, h_pts, h_recent = _team_stats_from_matches(matches, home_team)
    a_gf, a_ga, a_pts, a_recent = _team_stats_from_matches(matches, away_team)

    # 特征列名和顺序必须和 train_multi_leagues.py 里完全一致
    X = pd.DataFrame([{
        "home_gf": h_gf, "home_ga": h_ga, "home_pts": h_pts, "home_recent": h_recent,
        "away_gf": a_gf, "away_ga": a_ga, "away_pts": a_pts, "away_recent": a_recent,
    }])
    proba = model.predict_proba(X)[0]

    result = {}
    for cls, p in zip(model.classes_, proba):
        result[cls] = round(float(p), 2)

    return {
        "home": home_team, "away": away_team, "league": league_code,
        "p_home": result.get("HOME_TEAM", 0),
        "p_draw": result.get("DRAW", 0),
        "p_away": result.get("AWAY_TEAM", 0),
    }