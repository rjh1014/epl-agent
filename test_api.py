import requests

# 这里换成你真实的 Key
API_KEY = "a8b2fcc1bddf8cc9b3ddb234170da171" 
url = "https://v3.football.api-sports.io/status"
headers = {"x-apisports-key": API_KEY}

resp = requests.get(url, headers=headers)
print(resp.json())