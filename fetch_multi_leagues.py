import requests
import pandas as pd
import time

API_KEY = '1dc08e4439d3449e817abd9dd1750bc0'
headers = {'X-Auth-Token': API_KEY}

LEAGUES = {
    "PL": "英超",
    "PD": "西甲",
    "BL1": "德甲",
    "SA": "意甲",
    "FL1": "法甲",
}

for code, name in LEAGUES.items():
    print(f"正在获取 {name} ({code}) 数据…")
    url = f"https://api.football-data.org/v4/competitions/{code}/matches?season=2024"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"  失败: {resp.status_code} {resp.text[:100]}")
        continue

    data = resp.json()
    df = pd.DataFrame(data['matches'])
    df = df[df['status'] == 'FINISHED'].copy()
    if len(df) == 0:
        print(f"  {name} 没有已完成的比赛，跳过")
        continue

    df['date'] = df['utcDate']
    df['home'] = df['homeTeam'].apply(lambda x: x['name'])
    df['away'] = df['awayTeam'].apply(lambda x: x['name'])
    df['hg'] = df['score'].apply(lambda x: x['fullTime']['home'])
    df['ag'] = df['score'].apply(lambda x: x['fullTime']['away'])
    df['winner'] = df['score'].apply(lambda x: x['winner'])

    out = df[['date', 'home', 'away', 'hg', 'ag', 'winner']]
    out.to_csv(f"matches_{code}.csv", index=False)
    print(f"  已保存 matches_{code}.csv，共 {len(out)} 场")

    # 生成积分榜
    home_df = df[['home', 'away', 'hg', 'ag']].copy()
    home_df.columns = ['team', 'opponent', 'gf', 'ga']
    home_df['points'] = home_df.apply(lambda r: 3 if r['gf'] > r['ga'] else (1 if r['gf'] == r['ga'] else 0), axis=1)

    away_df = df[['away', 'home', 'ag', 'hg']].copy()
    away_df.columns = ['team', 'opponent', 'gf', 'ga']
    away_df['points'] = away_df.apply(lambda r: 3 if r['gf'] > r['ga'] else (1 if r['gf'] == r['ga'] else 0), axis=1)

    long_df = pd.concat([home_df, away_df], ignore_index=True)
    table = long_df.groupby('team').agg(
        MP=('gf', 'size'),
        W=('points', lambda x: (x == 3).sum()),
        D=('points', lambda x: (x == 1).sum()),
        L=('points', lambda x: (x == 0).sum()),
        GF=('gf', 'sum'),
        GA=('ga', 'sum'),
    ).reset_index()
    table['GD'] = table['GF'] - table['GA']
    table['PTS'] = table['W'] * 3 + table['D']
    table = table.sort_values(['PTS', 'GD', 'GF'], ascending=False).reset_index(drop=True)
    table.to_csv(f"standings_{code}.csv", index=False)
    print(f"  已保存 standings_{code}.csv")

    time.sleep(7)  # 免费层每分钟10次请求，留足间隔

print("全部完成。")