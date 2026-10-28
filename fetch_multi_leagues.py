import requests
import pandas as pd
import time

API_KEY = '1dc08e4439d3449e817abd9dd1750bc0'  # 换成你自己的真实 Key
headers = {'X-Auth-Token': API_KEY}

LEAGUES = {"PL": "英超", "PD": "西甲", "BL1": "德甲", "SA": "意甲", "FL1": "法甲"}

for code, name in LEAGUES.items():
    print(f"正在获取 {name} ({code}) 数据…")
    
    # 1. 先拉取 2024 历史数据（用于训练模型和查积分榜）
    url_hist = f"https://api.football-data.org/v4/competitions/{code}/matches?season=2024"
    resp = requests.get(url_hist, headers=headers)
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json()['matches'])
        df['date'] = df['utcDate']
        df['home'] = df['homeTeam'].apply(lambda x: x['name'])
        df['away'] = df['awayTeam'].apply(lambda x: x['name'])
        
        finished = df[df['status'] == 'FINISHED'].copy()
        if len(finished) > 0:
            finished['hg'] = finished['score'].apply(lambda x: x['fullTime']['home'])
            finished['ag'] = finished['score'].apply(lambda x: x['fullTime']['away'])
            finished['winner'] = finished['score'].apply(lambda x: x['winner'])
            finished[['date', 'home', 'away', 'hg', 'ag', 'winner']].to_csv(f"matches_{code}.csv", index=False)
            print(f"  已保存 matches_{code}.csv (已结束)，共 {len(finished)} 场")
    
    time.sleep(7)

    # 2. 拉取当前最新赛季数据，专门找接下来的比赛
    print(f"  正在获取 {name} 的未来赛程…")
    url_curr = f"https://api.football-data.org/v4/competitions/{code}/matches"  # 不加 season 默认拉最新
    resp_curr = requests.get(url_curr, headers=headers)
    if resp_curr.status_code == 200:
        df_curr = pd.DataFrame(resp_curr.json()['matches'])
        df_curr['date'] = df_curr['utcDate']
        df_curr['home'] = df_curr['homeTeam'].apply(lambda x: x['name'])
        df_curr['away'] = df_curr['awayTeam'].apply(lambda x: x['name'])
        
        upcoming_curr = df_curr[df_curr['status'].isin(['SCHEDULED', 'TIMED'])].copy()
        if len(upcoming_curr) > 0:
            upcoming_curr[['date', 'home', 'away', 'status']].to_csv(f"upcoming_{code}.csv", index=False)
            print(f"  已保存 upcoming_{code}.csv (未来赛程)，共 {len(upcoming_curr)} 场")
        else:
            print(f"  当前没有未开始的比赛。")

    time.sleep(7)

print("全部完成。")