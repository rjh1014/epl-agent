import requests
import pandas as pd

API_KEY ='1dc08e4439d3449e817abd9dd1750bc0'
headers = {'X-Auth-Token': API_KEY}
url = "https://api.football-data.org/v4/competitions/PL/matches?season=2024"
data = requests.get(url, headers=headers).json()

df = pd.DataFrame(data['matches'])

# 只保留已经踢完的比赛
df = df[df['status'] == 'FINISHED'].copy()

# 提取队名
df['home'] = df['homeTeam'].apply(lambda x: x['name'])
df['away'] = df['awayTeam'].apply(lambda x: x['name'])

# 从 score.fullTime 里挖出主客队进球数
df['hg'] = df['score'].apply(lambda x: x['fullTime']['home'])
df['ag'] = df['score'].apply(lambda x: x['fullTime']['away'])

# 主队视角的一张表
home = df[['home', 'away', 'hg', 'ag']].copy()
home.columns = ['team', 'opponent', 'gf', 'ga']
home['points'] = home.apply(lambda r: 3 if r['gf'] > r['ga'] else (1 if r['gf'] == r['ga'] else 0), axis=1)

# 客队视角的一张表
away = df[['away', 'home', 'ag', 'hg']].copy()
away.columns = ['team', 'opponent', 'gf', 'ga']
away['points'] = away.apply(lambda r: 3 if r['gf'] > r['ga'] else (1 if r['gf'] == r['ga'] else 0), axis=1)

# 把两张表上下拼起来，每场比赛就变成了两行：主队一行、客队一行
long = pd.concat([home, away], ignore_index=True)

# 按球队汇总
table = long.groupby('team').agg(
    MP=('gf', 'size'),
    W=('points', lambda x: (x == 3).sum()),
    D=('points', lambda x: (x == 1).sum()),
    L=('points', lambda x: (x == 0).sum()),
    GF=('gf', 'sum'),
    GA=('ga', 'sum'),
).reset_index()

table['GD'] = table['GF'] - table['GA']
table['PTS'] = table['W'] * 3 + table['D']

# 按积分、净胜球、进球数排序
table = table.sort_values(['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)
table.index = table.index + 1
table.index.name = 'Rank'

print(table[['team', 'MP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'PTS']].to_string())
table.to_csv("standings.csv", index=False)
df[['home', 'away', 'hg', 'ag', 'winner']].to_csv("epl_matches.csv", index=False)