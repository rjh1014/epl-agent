import requests
import json

url = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry"
params = {"channel": "c", "poolCode": "hhad,had"}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://m.sporttery.cn/",
}

resp = requests.get(url, params=params, headers=headers, timeout=10)
if resp.status_code == 200:
    data = resp.json()
    match_days = data.get("value", {}).get("matchInfoList", [])
    
    total_matches = 0
    for day in match_days:
        # 真正的比赛在 subMatchList 里
        sub_matches = day.get("subMatchList", [])
        for m in sub_matches:
            total_matches += 1
            home = m.get("homeTeamAllName")
            away = m.get("awayTeamAllName")
            
            # 查找胜平负（had）和让球（hhad）赔率
            had = m.get("had", {})
            hhad = m.get("hhad", {})
            
            print(f"[{day.get('businessDate')}] {home} vs {away}")
            if had:
                print(f"  -> 胜平负: 主胜 {had.get('h')} | 平 {had.get('d')} | 客胜 {had.get('a')}")
            if hhad:
                print(f"  -> 让球盘: 让球数 {hhad.get('goalLine')} | 主胜 {hhad.get('h')} | 平 {hhad.get('d')} | 客胜 {hhad.get('a')}")
            
            if not had and not hhad:
                print("  -> 这行没有赔率字段，所有字段名如下：")
                print("     ", list(m.keys()))
            print("-" * 20)

    print(f"总共解析到 {total_matches} 场比赛。")