import requests
import json
import time

# 换成你自己的 API-Football Key
API_KEY = "a8b2fcc1bddf8cc9b3ddb234170da171" 
headers = {"x-apisports-key": API_KEY}

# 我们项目里五大联赛的常见球队
teams_to_find = [
    # 英超
    "Manchester City", "Liverpool", "Arsenal", "Chelsea", "Manchester United",
    "Tottenham", "Newcastle", "Aston Villa", "Brighton", "West Ham",
    "Wolves", "Everton", "Fulham", "Crystal Palace", "Brentford",
    # 西甲
    "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Real Sociedad",
    "Villarreal", "Real Betis", "Athletic Club",
    # 德甲
    "Bayern Munich", "Borussia Dortmund", "Bayer Leverkusen", "RB Leipzig",
    "Eintracht Frankfurt", "Stuttgart",
    # 意甲
    "Inter", "AC Milan", "Juventus", "Napoli", "Roma", "Lazio", "Atalanta",
    # 法甲
    "Paris Saint-Germain", "Marseille", "Monaco", "Lyon", "Lille"
]

team_ids = {}

for name in teams_to_find:
    # 请求 API 搜索球队
    url = f"https://v3.football.api-sports.io/teams?search={name}"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    
    if data["results"] > 0:
        # 取搜索结果的第一个（通常是最匹配的）
        team = data["response"][0]
        team_id = team["team"]["id"]
        official_name = team["team"]["name"]
        team_ids[name] = team_id
        print(f"✅ {name} -> ID: {team_id} (官方名: {official_name})")
    else:
        print(f"❌ {name} -> 未找到")
    
    # API 免费版限制每分钟 10 次请求，每次停 7 秒防报错
    time.sleep(7)

# 保存为 JSON 文件
with open("team_ids.json", "w", encoding="utf-8") as f:
    json.dump(team_ids, f, ensure_ascii=False, indent=4)

print("\n球队 ID 映射已保存到 team_ids.json")