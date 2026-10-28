import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

LEAGUES = ["PL", "PD", "BL1", "SA", "FL1"]
LEAGUE_NAMES = {"PL": "英超", "PD": "西甲", "BL1": "德甲", "SA": "意甲", "FL1": "法甲"}

def build_features(matches):
    """按时间顺序，用赛前滚动统计构造特征"""
    team_stats = {}

    def get_pre_stats(team):
        if team not in team_stats or len(team_stats[team]['gf']) == 0:
            return 1.3, 1.3, 1.3
        s = team_stats[team]
        n = len(s['gf'])
        return sum(s['gf']) / n, sum(s['ga']) / n, sum(s['pts']) / n

    def update(team, gf, ga):
        if team not in team_stats:
            team_stats[team] = {'gf': [], 'ga': [], 'pts': []}
        team_stats[team]['gf'].append(gf)
        team_stats[team]['ga'].append(ga)
        team_stats[team]['pts'].append(3 if gf > ga else (1 if gf == ga else 0))

    rows = []
    for _, row in matches.iterrows():
        h_gf, h_ga, h_pts = get_pre_stats(row['home'])
        a_gf, a_ga, a_pts = get_pre_stats(row['away'])
        rows.append({
            'home_gf': h_gf, 'home_ga': h_ga, 'home_pts': h_pts,
            'away_gf': a_gf, 'away_ga': a_ga, 'away_pts': a_pts,
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
        print(f"{LEAGUE_NAMES[code]}: 找不到 {path}，跳过")
        continue

    matches['date'] = pd.to_datetime(matches['date'])
    matches = matches.sort_values('date').reset_index(drop=True)

    df = build_features(matches)
    X = df.drop('winner', axis=1)
    y = df['winner']

    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)

    print(f"{LEAGUE_NAMES[code]}: 准确率 {acc:.3f}，训练 {len(X_train)} 场，测试 {len(X_test)} 场")

    models[code] = model

with open("models_multi.pkl", "wb") as f:
    pickle.dump(models, f)

print("\n模型已保存到 models_multi.pkl")