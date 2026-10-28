import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

LEAGUES = ["PL", "PD", "BL1", "SA", "FL1"]
LEAGUE_NAMES = {"PL": "英超", "PD": "西甲", "BL1": "德甲", "SA": "意甲", "FL1": "法甲"}

def build_features(matches):
    """按时间顺序，用赛前滚动统计构造特征（包含整体平均和近5场状态）"""
    team_history = {}

    def get_pre_stats(team):
        # 默认值：没数据时用 1.3 球、1.3 分兜底
        if team not in team_history or len(team_history[team]) == 0:
            return 1.3, 1.3, 1.3, 1.3
        
        history = team_history[team]
        n = len(history)
        
        # 1. 赛季整体场均
        avg_gf = sum(h[0] for h in history) / n
        avg_ga = sum(h[1] for h in history) / n
        avg_pts = sum(h[2] for h in history) / n
        
        # 2. 最近5场场均（如果不足5场，就用现有场次）
        recent = history[-5:]
        r_n = len(recent)
        recent_pts = sum(h[2] for h in recent) / r_n
        
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

    # 对比两个模型：逻辑回归 vs 随机森林
    lr_model = LogisticRegression(max_iter=1000)
    lr_model.fit(X_train, y_train)
    lr_acc = accuracy_score(y_test, lr_model.predict(X_test))

    # 随机森林（100棵树，最大深度5，防止过拟合）
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf_model.predict(X_test))

    print(f"{LEAGUE_NAMES[code]}: 逻辑回归 {lr_acc:.3f} | 随机森林 {rf_acc:.3f}")

    # 我们统一保存随机森林模型（它通常表现更好）
    models[code] = rf_model

with open("models_multi.pkl", "wb") as f:
    pickle.dump(models, f)

print("\n全新升级版模型已保存到 models_multi.pkl")