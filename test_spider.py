import requests
from bs4 import BeautifulSoup

# 我们用 500 彩票网的赔率页面做测试
url = "https://odds.500.com/fenxi/oupei-1088411.shtml" # 这是一场示例比赛页面
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    resp.encoding = 'gbk' # 500彩票网通常是gbk编码
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 抓取网页标题看看
    title = soup.title.text.strip()
    print("✅ 成功访问网页，标题是：", title)
    
    # 找一下赔率表格的行
    rows = soup.select("table#datatb tr")
    print(f"找到了 {len(rows)} 行赔率数据。")
    
    if len(rows) > 1:
        # 打印第一行博彩公司数据看看
        first_row = rows[1].text.strip().replace("\n", " ").replace("\t", "")
        print("第一行博彩公司数据：", first_row)
        
except Exception as e:
    print("❌ 抓取失败，报错：", e)