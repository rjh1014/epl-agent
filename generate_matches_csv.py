import requests
import pandas as pd

API_KEY ='1dc08e4439d3449e817abd9dd1750bc0'
headers = {'X-Auth-Token': API_KEY}
url = "https://api.football-data.org/v4/competitions/PL/matches?season=2024"
data = requests.get(url, headers=headers).json()

df = pd.DataFrame(data['matches'])
df = df[df['status'] == 'FINISHED'].copy()

df['home'] = df['homeTeam'].apply(lambda x: x['name'])
df['away'] = df['awayTeam'].apply(lambda x: x['name'])
df['hg'] = df['score'].apply(lambda x: x['fullTime']['home'])
df['ag'] = df['score'].apply(lambda x: x['fullTime']['away'])
df['winner'] = df['score'].apply(lambda x: x['winner'])

df['date'] = df['utcDate']
df[['date', 'home', 'away', 'hg', 'ag', 'winner']].to_csv("epl_matches.csv", index=False)

print("已生成 epl_matches.csv，共", len(df), "场比赛")