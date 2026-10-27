import csv

with open("matches.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

total_goals = 0
home_wins = 0
away_wins = 0
draws = 0

print("一共读到了", len(rows), "场比赛")

for row in rows:
    home = row["home"]
    away = row["away"]
    hg = int(row["home_goals"])
    ag = int(row["away_goals"])

    total_goals = total_goals + hg + ag

    if hg > ag:
        result = home + " 赢"
        home_wins = home_wins + 1
    elif hg < ag:
        result = away + " 赢"
        away_wins = away_wins + 1
    else:
        result = "平局"
        draws = draws + 1

    print(home, "vs", away, "比分", hg, ":", ag, "->", result)

print("---")
print("总进球数:", total_goals)
print("主队胜:", home_wins, "场")
print("客队胜:", away_wins, "场")
print("平局:", draws, "场")