import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

matches = pd.read_csv("epl_matches.csv")
matches['date'] = pd.to_datetime(matches['date'])
matches = matches.sort_values('date').reset_index(drop=True)

# 每支球队的历史记录：进球、失球、积分
team_stats = {}

def get_pre_match_stats(team):
    """返回该队在此之前的场均进球、场均失球、场均积分"""
    if team not in team_stats or len(team_stats[team]['gf']) == 0:
        return 1.3, 1.3, 1.3  # 新球队默认值：场均1.3球、1.3分
    s = team_stats[team]
    n = len(s['gf'])
    return sum(s['gf']) / n, sum(s['ga']) / n, sum(s['pts']) / n

def update_stats(team, gf, ga):
    if team not in team_stats:
        team_stats[team] = {'gf': [], 'ga': [], 'pts': []}
    team_stats[team]['gf'].append(gf)
    team_stats[team]['ga'].append(ga)
    team_stats[team]['pts'].append(3 if gf > ga else (1 if gf == ga else 0))

rows = []
for _, row in matches.iterrows():
    home, away = row['home'], row['away']
    h_gf, h_ga, h_pts = get_pre_match_stats(home)
    a_gf, a_ga, a_pts = get_pre_match_stats(away)

    rows.append({
        'home_gf': h_gf, 'home_ga': h_ga, 'home_pts': h_pts,
        'away_gf': a_gf, 'away_ga': a_ga, 'away_pts': a_pts,
        'winner': row['winner'],
    })

    update_stats(home, row['hg'], row['ag'])
    update_stats(away, row['ag'], row['hg'])

features_df = pd.DataFrame(rows)
X = features_df.drop('winner', axis=1)
y = features_df['winner']

# 关键：按时间顺序切分，前 80% 训练，后 20% 测试。不能随机打乱。
split = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
pred = model.predict(X_test)

print("修复数据泄露后的准确率:", round(accuracy_score(y_test, pred), 3))
print()

order = ['HOME_TEAM', 'DRAW', 'AWAY_TEAM']
cm = confusion_matrix(y_test, pred, labels=order)
print("混淆矩阵（行=真实，列=预测）:")
print(pd.DataFrame(cm, index=order, columns=order))
import pickle
with open("model.pkl", "wb") as f:
    pickle.dump({"model": model, "team_stats": team_stats}, f)
print("\n模型已保存到 model.pkl")