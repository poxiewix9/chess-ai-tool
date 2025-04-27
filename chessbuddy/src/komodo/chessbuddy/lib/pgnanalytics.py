import logfire
import pandas as pd
import numpy as np
import chess.pgn
import io
from typing import List, Dict, Any
from chessdotcom import ChessDotComClient

client = ChessDotComClient(user_agent="thechessbuddy/0.1.0 (https://github.com/ryanoberoi/thechessbuddy)")

@logfire.instrument
def fetch_archives(username: str) -> List[str]:
    """
    Fetch the list of archive URLs for a given Chess.com username using chess.com package.
    """
    resp = client.get_player_game_archives(username)  # pyright: ignore [reportAttributeAccessIssue]
    return resp.json.get("archives", [])

@logfire.instrument
def fetch_games_pgn(username: str, year: int, month: int) -> List[str]:
    """
    Fetch all PGNs for a given user, year, and month using chess.com package.
    Returns a list of PGN strings.
    """
    resp = client.get_player_games_by_month_pgn(username, year, month)  # pyright: ignore [reportAttributeAccessIssue]
    if not hasattr(resp, "text") or not resp.text:
        return []
    pgn_text = resp.text
    # Split PGN text into individual games
    games = pgn_text.strip().split("\n\n\n")
    return [g for g in games if g.strip()]

@logfire.instrument
def parse_pgns(pgn_list: List[str]) -> List[Dict[str, Any]]:
    """
    Parse a list of PGN strings into game data dictionaries.
    """
    games_data = []
    for pgn in pgn_list:
        game_io = io.StringIO(pgn)
        game = chess.pgn.read_game(game_io)
        if not game:
            continue
        headers = game.headers
        moves = [move.uci() for move in game.mainline_moves()]
        result = headers.get("Result", "")
        eco = headers.get("ECO", "")
        opening = headers.get("Opening", "")
        white = headers.get("White", "")
        black = headers.get("Black", "")
        date = headers.get("Date", "")
        games_data.append({
            "white": white,
            "black": black,
            "result": result,
            "eco": eco,
            "opening": opening,
            "date": date,
            "num_moves": len(moves),
            "moves": moves,
        })
    return games_data


@logfire.instrument(record_return=True)
def get_user_games_df(username: str, max_months: int = 3) -> pd.DataFrame:
    """
    Fetch and analyze recent games for a user, returning a DataFrame.
    By default, analyzes up to the last 3 months of games.
    """
    archives = fetch_archives(username)
    # Get up to max_months most recent archives
    recent_archives = archives[-max_months:]
    all_games = []
    for archive_url in recent_archives:
        parts = archive_url.rstrip("/").split("/")
        year, month = int(parts[-2]), int(parts[-1])
        pgns = fetch_games_pgn(username, year, month)
        all_games.extend(parse_pgns(pgns))
    if not all_games:
        return pd.DataFrame()
    df = pd.DataFrame(all_games)
    # Parse the date and sort by latest first
    if "date" in df.columns:
        df["parsed_date"] = pd.to_datetime(df["date"], errors="coerce", format="%Y.%m.%d")
        df = df.sort_values("parsed_date", ascending=False).reset_index(drop=True)
    return df

@logfire.instrument(record_return=True)
def summarize_user_stats(df: pd.DataFrame, username: str) -> Dict[str, Any]:
    """
    Given a DataFrame of games, return summary statistics for the user.
    """
    if df.empty:
        return {"total_games": 0}
    # Determine if user was white or black in each game
    df["is_white"] = df["white"].str.lower() == username.lower()
    df["is_black"] = df["black"].str.lower() == username.lower()
    # Compute results from user's perspective
    def user_result(row):
        if row["is_white"]:
            if row["result"] == "1-0":
                return "win"
            elif row["result"] == "0-1":
                return "loss"
            elif row["result"] == "1/2-1/2":
                return "draw"
        elif row["is_black"]:
            if row["result"] == "0-1":
                return "win"
            elif row["result"] == "1-0":
                return "loss"
            elif row["result"] == "1/2-1/2":
                return "draw"
        return "other"
    df["user_result"] = df.apply(user_result, axis=1)
    stats = {
        "total_games": len(df),
        "wins": int(np.sum(df["user_result"] == "win")),
        "losses": int(np.sum(df["user_result"] == "loss")),
        "draws": int(np.sum(df["user_result"] == "draw")),
        "win_rate": float(np.sum(df["user_result"] == "win")) / len(df) if len(df) else 0.0,
        "most_common_openings": df["opening"].value_counts().head(5).to_dict(),
        "average_num_moves": float(df["num_moves"].mean()),
    }
    return stats

if __name__ == "__main__":
    username = "ryanoberoi"
    df = get_user_games_df(username)
    print(df.head())
    stats = summarize_user_stats(df, username)
    print(stats)
