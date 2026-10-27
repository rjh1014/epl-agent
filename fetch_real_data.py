import requests
import pandas as pd

# 1. 你的 API 密钥（记得替换成你自己的）
API_KEY ='1dc08e4439d3449e817abd9dd1750bc0'

# 2. 设置请求头，API 通过这个来识别你的身份
headers = {'X-Auth-Token': API_KEY}

# 3. 构建请求 URL：获取英超(PL) 2024赛季的比赛数据
url = "https://api.football-data.org/v4/competitions/PL/matches?season=2024"

# 4. 发送请求并获取数据
response = requests.get(url, headers=headers)
data = response.json()  # 将返回的 JSON 数据转换为 Python 字典

# 5. 将比赛数据列表转换成一个 Pandas DataFrame
matches = pd.DataFrame(data['matches'])

# 6. 简单的数据清洗：把嵌套的队名和胜者信息提取出来
matches['homeTeam'] = matches['homeTeam'].apply(lambda x: x['name'])
matches['awayTeam'] = matches['awayTeam'].apply(lambda x: x['name'])
matches['winner'] = matches['score'].apply(lambda x: x['winner'])

# 7. 打印结果
print("一共获取到", len(matches), "场比赛数据")
print(matches[['homeTeam', 'awayTeam', 'winner']].head(10))  # 只看前10行