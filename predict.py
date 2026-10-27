import pandas as pd

table = pd.read_csv("standings.csv")

table['GF_per_game'] = table['GF'] / table['MP']
table['GA_per_game'] = table['GA'] / table['MP']

def predict(home_team, away_team):
    home = table[table['team'] == home_team].iloc[0]
    away = table[table['team'] == away_team].iloc[0]

    # 预期进球：自己进攻 × 0.6 + 对方防守 × 0.4，主队加 0.3 主场优势
    home_xg = home['GF_per_game'] * 0.6 + away['GA_per_game'] * 0.4 + 0.3
    away_xg = away['GF_per_game'] * 0.6 + home['GA_per_game'] * 0.4

    # 用预期进球差映射到概率（最粗糙的规则，后面会换成模型）
    diff = home_xg - away_xg
    p_home = 0.40 + diff * 0.18
    p_home = max(0.10, min(0.80, p_home))
    p_draw = 0.25
    p_away = 1 - p_home - p_draw

    print(f"{home_team} vs {away_team}")
    print(f"  预期进球: {home_xg:.2f} : {away_xg:.2f}")
    print(f"  主胜: {p_home:.0%}   平局: {p_draw:.0%}   客胜: {p_away:.0%}")
    print()

def predict(home_team, away_team):
    home = table[table['team'] == home_team].iloc[0]
    away = table[table['team'] == away_team].iloc[0]

    home_xg = home['GF_per_game'] * 0.6 + away['GA_per_game'] * 0.4 + 0.3
    away_xg = away['GF_per_game'] * 0.6 + home['GA_per_game'] * 0.4

    diff = home_xg - away_xg
    p_home = max(0.10, min(0.80, 0.40 + diff * 0.18))
    p_draw = 0.25
    p_away = 1 - p_home - p_draw

    return {
        "home": home_team,
        "away": away_team,
        "home_xg": round(home_xg, 2),
        "away_xg": round(away_xg, 2),
        "p_home": round(p_home, 2),
        "p_draw": round(p_draw, 2),
        "p_away": round(p_away, 2),
    }