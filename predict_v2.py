import pandas as pd
import pickle

with open("model.pkl", "rb") as f:
    saved = pickle.load(f)
model = saved["model"]
team_stats = saved["team_stats"]

def get_pre_match_stats(team):
    if team not in team_stats or len(team_stats[team]['gf']) == 0:
        return 1.3, 1.3, 1.3
    s = team_stats[team]
    n = len(s['gf'])
    return sum(s['gf']) / n, sum(s['ga']) / n, sum(s['pts']) / n

def predict(home_team, away_team):
    h_gf, h_ga, h_pts = get_pre_match_stats(home_team)
    a_gf, a_ga, a_pts = get_pre_match_stats(away_team)

    X = pd.DataFrame([{
        "home_gf": h_gf, "home_ga": h_ga, "home_pts": h_pts,
        "away_gf": a_gf, "away_ga": a_ga, "away_pts": a_pts,
    }])
    proba = model.predict_proba(X)[0]

    result = {}
    for cls, p in zip(model.classes_, proba):
        result[cls] = round(float(p), 2)

    return {
        "home": home_team,
        "away": away_team,
        "p_home": result.get("HOME_TEAM", 0),
        "p_draw": result.get("DRAW", 0),
        "p_away": result.get("AWAY_TEAM", 0),
    }