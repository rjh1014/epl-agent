import pandas as pd

df = pd.read_csv("matches.csv")

print(df)
print("---")
print("总进球数:", df["home_goals"].sum() + df["away_goals"].sum())
def get_result(row):
    if row["home_goals"] > row["away_goals"]:
        return "主胜"
    elif row["home_goals"] < row["away_goals"]:
        return "客胜"
    else:
        return "平局"

df["result"] = df.apply(get_result, axis=1)

print("---")
print(df[["home", "away", "result"]])
print("---")
print(df["result"].value_counts())