import pickle
import pandas as pd

with open("model.pkl", "rb") as f:
    saved = pickle.load(f)
model = saved["model"]

def _team_stats_from_matches(matches, team):
    played = matches[(matches['home'] == team) | (matches['away'] == team)]
    if len(played) == 0:
        return 1.3, 1.3, 1.3
    gf = ga = pts = 0
    for _, r in played.iterrows():
        if r['home'] == team:
            gf += int(r['hg']); ga += int(r['ag'])
            pts += 3 if r['hg'] > r['ag'] else (1 if r['hg'] == r['ag'] else 0)
        else:
            gf += int(r['ag']); ga += int(r['hg'])
            pts += 3 if r['ag'] > r['hg'] else (1 if r['ag'] == r['hg'] else 0)
    n = len(played)
    return gf / n, ga / n, pts / n

def predict(home_team, away_team, matches=None):
    if matches is None:
        matches = pd.read_csv("epl_matches.csv")
        matches['date'] = pd.to_datetime(matches['date'])
        matches = matches.sort_values('date').reset_index(drop=True)

    h_gf, h_ga, h_pts = _team_stats_from_matches(matches, home_team)
    a_gf, a_ga, a_pts = _team_stats_from_matches(matches, away_team)

    X = pd.DataFrame([{
        "home_gf": h_gf, "home_ga": h_ga, "home_pts": h_pts,
        "away_gf": a_gf, "away_ga": a_ga, "away_pts": a_pts,
    }])
    proba = model.predict_proba(X)[0]

    result = {}
    for cls, p in zip(model.classes_, proba):
        result[cls] = round(float(p), 2)

    return {
        "home": home_team, "away": away_team,
        "p_home": result.get("HOME_TEAM", 0),
        "p_draw": result.get("DRAW", 0),
        "p_away": result.get("AWAY_TEAM", 0),
    }