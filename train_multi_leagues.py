import pandas as pd
import joblib
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

LEAGUES = ["PL", "PD", "BL1", "SA", "FL1"]
LEAGUE_NAMES = {"PL": "英超", "PD": "西甲", "BL1": "德甲", "SA": "意甲", "FL1": "法甲"}

def build_features(matches):
    team_history = {}

    def get_pre_stats(team):
        if team not in team_history or len(team_history[team]) == 0:
            return 1.3, 1.3, 1.3, 1.3
        history = team_history[team]
        n = len(history)
        avg_gf = sum(h[0] for h in history) / n
        avg_ga = sum(h[1] for h in history) / n
        avg_pts = sum(h[2] for h in history) / n
        recent = history[-5:]
        recent_pts = sum(h[2] for h in recent) / len(recent)
        return avg_gf, avg_ga, avg_pts, recent_pts

    def update(team, gf, ga):
        if team not in team_history:
            team_history[team] = []
        pts = 3 if gf > ga else (1 if gf == ga else 0)
        team_history[team].append((gf, ga, pts))

    rows = []
    for _, row in matches.iterrows():
        h_gf, h_ga, h_pts, h_recent = get_pre_stats(row['home'])
        a_gf, a_ga, a_pts, a_recent = get_pre_stats(row['away'])
        rows.append({
            'home_gf': h_gf, 'home_ga': h_ga, 'home_pts': h_pts, 'home_recent': h_recent,
            'away_gf': a_gf, 'away_ga': a_ga, 'away_pts': a_pts, 'away_recent': a_recent,
            'winner': row['winner'],
        })
        update(row['home'], row['hg'], row['ag'])
        update(row['away'], row['ag'], row['hg'])

    return pd.DataFrame(rows)

models = {}

for code in LEAGUES:
    path = f"matches_{code}.csv"
    try:
        matches = pd.read_csv(path)
    except FileNotFoundError:
        continue

    matches['date'] = pd.to_datetime(matches['date'])
    matches = matches.sort_values('date').reset_index(drop=True)

    df = build_features(matches)
    X = df.drop('winner', axis=1)
    y = df['winner']

    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    lr_model = LogisticRegression(max_iter=1000)
    lr_model.fit(X_train, y_train)
    lr_acc = accuracy_score(y_test, lr_model.predict(X_test))

    rf_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf_model.predict(X_test))

    # 择优录取：哪个准确率高，就保存哪个模型
    if lr_acc >= rf_acc:
        print(f"{LEAGUE_NAMES[code]}: 逻辑回归 {lr_acc:.3f} | 随机森林 {rf_acc:.3f} -> 保存逻辑回归")
        models[code] = lr_model
    else:
        print(f"{LEAGUE_NAMES[code]}: 逻辑回归 {lr_acc:.3f} | 随机森林 {rf_acc:.3f} -> 保存随机森林")
        models[code] = rf_model

joblib.dump(models, "models_multi.joblib")
print("\n全明星模型组合已保存到 models_multi.joblib")