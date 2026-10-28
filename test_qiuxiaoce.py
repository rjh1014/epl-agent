from qiuxiaoce import QiuXiaoCeClient
import json

API_KEY = "qxz_v4xUbSpe5oOUK3yYVeieV6Cs"
client = QiuXiaoCeClient(api_key=API_KEY)
team_id = 42

# 拿 2024 赛季的最后一场比赛 ID
fixtures = client.get_fixtures(team_id=team_id, season=2024)
target_id = fixtures[-1]['fixture_id']

print(f"正在查询 fixture_id={target_id} 的 Match Pack 完整结构...")
pack = client.get_match_pack(fixture_id=target_id)

# 打印所有的键名（看看里面到底有啥）
print("\n包含的字段名：", list(pack.keys()))

# 打印完整内容（可能很长，我们只看前2000个字符）
print("\n完整数据预览：")
print(json.dumps(pack, indent=2, ensure_ascii=False)[:2000])