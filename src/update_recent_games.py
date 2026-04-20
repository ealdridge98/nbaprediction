import pandas as pd
from datetime import datetime, timedelta
from nba_api.stats.endpoints import leaguegamelog

# ----------------------------------------------------------
# Helper: auto-detect correct NBA season string (e.g. "2025-26")
# ----------------------------------------------------------
def current_nba_season_str(today=None):
    today = today or datetime.today()
    year = today.year

    # NBA season starts ~October
    if today.month >= 8:
        start = year
        end = (year + 1) % 100
    else:
        start = year - 1
        end = year % 100

    return f"{start}-{end:02d}"


# ----------------------------------------------------------
# Pull last 6 months of NBA TEAM GAME LOGS
# ----------------------------------------------------------
def get_last_six_month_games():
    today = datetime.today()
    six_months_back = today - timedelta(days=182)

    # NBA API requires MM/DD/YYYY (not ISO)
    date_from = six_months_back.strftime("%m/%d/%Y")
    date_to = today.strftime("%m/%d/%Y")

    season_str = current_nba_season_str(today)

    logs = leaguegamelog.LeagueGameLog(
        season=season_str,
        season_type_all_star='Regular Season',
        date_from_nullable=date_from,
        date_to_nullable=date_to,
        player_or_team_abbreviation='T',  # team logs
        sorter='DATE',
        direction='ASC'
    )

    df = logs.get_data_frames()[0]
    return df


# ----------------------------------------------------------
# Load previous cleaned dataset + append new data + dedupe
# ----------------------------------------------------------
def update_cleaned_dataset():
    # Fetch 6‑month window
    df_new = get_last_six_month_games()
    print(f"Pulled rows from API (last 6 months): {len(df_new)}")

    # Load your existing cleaned dataset
    cleaned_path = r"D:\nba-win-prediction\data\clean\clean_game_nba.csv"
    cleaned_df = pd.read_csv(cleaned_path)
    print(f"Existing cleaned dataset rows: {len(cleaned_df)}")

    # Align columns if needed
    missing_cols = [c for c in cleaned_df.columns if c not in df_new.columns]
    extra_cols   = [c for c in df_new.columns if c not in cleaned_df.columns]

    if extra_cols:
        print("New columns in fresh data:", extra_cols)

    # Reindex new df to match cleaned_df columns (prevents merge issues)
    df_new = df_new.reindex(columns=cleaned_df.columns)

    # Combine
    combined = pd.concat([cleaned_df, df_new], ignore_index=True)
    print(f"Combined rows before dedupe: {len(combined)}")

    # Deduplicate by GAME_ID + TEAM_ID (team logs are two rows per game)
    if "GAME_ID" in combined.columns and "TEAM_ID" in combined.columns:
        combined = combined.drop_duplicates(subset=["GAME_ID", "TEAM_ID"], keep="last")
    else:
        print("⚠️ WARNING: Missing GAME_ID or TEAM_ID for dedupe")

    print(f"Final rows after dedupe: {len(combined)}")

    out_path = r"D:\nba-win-prediction\data\clean\clean_game_nba_updated.csv"
    combined.to_csv(out_path, index=False)
    print(f"\nUpdated dataset saved to:\n{out_path}")


if __name__ == "__main__":
    update_cleaned_dataset()
``