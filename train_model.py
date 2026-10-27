import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

matches = pd.read_csv("epl_matches.csv")
table = pd.read_csv("standings.csv")

table['GF_per_game'] = table['GF'] / table['MP']
table['GA_per_game'] = table['GA'] / table['MP']
table['PTS_per_game'] = table['PTS'] / table['MP']

stats = table.set_index('team')[['GF_per_game', 'GA_per_game', 'PTS_per_game']]

features = pd.DataFrame({
    'home_gf': matches['home'].map(stats['GF_per_game']),
    'home_ga': matches['home'].map(stats['GA_per_game']),
    'home_pts': matches['home'].map(stats['PTS_per_game']),
    'away_gf': matches['away'].map(stats['GF_per_game']),
    'away_ga': matches['away'].map(stats['GA_per_game']),
    'away_pts': matches['away'].map(stats['PTS_per_game']),
})

labels = matches['winner']

X_train, X_test, y_train, y_test = train_test_split(
    features, labels, test_size=0.2, random_state=42
)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

pred = model.predict(X_test)

print("准确率:", round(accuracy_score(y_test, pred), 3))
print()

order = ['HOME_TEAM', 'DRAW', 'AWAY_TEAM']
cm = confusion_matrix(y_test, pred, labels=order)
print("混淆矩阵（行=真实，列=预测）:")
print(pd.DataFrame(cm, index=order, columns=order))