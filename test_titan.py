import requests
import json
import re

# 随便找一场比赛，把网址里的数字填进来
MATCH_ID = "2990354" 

def get_real_odds():
    # 1. 获取欧赔数据 (js格式)
    url_1x2 = f"http://1x2d.titan007.com/{MATCH_ID}.js"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://live.titan007.com/"
    }
    
    try:
        resp = requests.get(url_1x2, headers=headers, timeout=10)
        resp.encoding = 'gbk'
        text = resp.text
        
        # 2. 提取 JS 中包裹的数据
        # 球探网常见的结构是：var game=Array("1|公司名|初胜|初平|初负|即时胜|即时平|即时负|...",...)
        match = re.search(r'var game=Array\((.*?)\);', text, re.DOTALL)
        if not match:
            return {"error": "未找到赔率数据变量"}
            
        raw_data = match.group(1)
        # 简单清理引号并分割每条数据
        items = raw_data.split('","')
        if not items:
            return {"error": "数据为空"}

        # 以第一家公司数据为例解析
        first_company = items[0].replace('"', '').split('|')
        
        # 典型结构：0:ID, 1:公司名, 2:初胜, 3:初平, 4:初负, 5:即时胜, 6:即时平, 7:即时负
        company_name = first_company[1]
        init_odds = {"home": first_company[2], "draw": first_company[3], "away": first_company[4]}
        live_odds = {"home": first_company[5], "draw": first_company[6], "away": first_company[7]}

        return {
            "company": company_name,
            "init_odds": init_odds,
            "live_odds": live_odds
        }

    except Exception as e:
        return {"error": str(e)}

print(get_real_odds())