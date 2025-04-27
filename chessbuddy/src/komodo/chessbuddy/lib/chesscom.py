import logfire
from chessdotcom import ChessDotComClient
from datetime import datetime, timezone
import re
from typing import List, Tuple, Optional, Dict, Any

client = ChessDotComClient(user_agent="thechessbuddy/0.1.0 (https://github.com/ryanoberoi/thechessbuddy)")


@logfire.instrument(record_return=True)
def get_profile(username: str) -> Dict[str, Any]:
    """
    Fetch the public profile of a chess.com user.

    Args:
        username (str): The chess.com username.

    Returns:
        dict: The user's profile information.
    """
    response = client.get_player_profile(username)  # type: ignore[reportAttributeAccessIssue]
    return response.json['player']


@logfire.instrument
def get_latest_games(username: str, n: int = 10) -> Dict[str, Any]:
    """
    Fetch the last N games played by a chess.com user (across months if needed).

    Args:
        username (str): The chess.com username.
        n (int): Number of recent games to return (default 10).

    Returns:
        dict: The latest games data, with up to N most recent games.
    """
    # Get all archive URLs (sorted oldest to newest)
    archives_response = client.get_player_game_archives(username)  # type: ignore[reportAttributeAccessIssue]
    archive_urls = archives_response.json.get("archives", [])
    if not archive_urls:
        return {"games": []}
    # Process archives from newest to oldest
    all_games = []
    for archive_url in reversed(archive_urls):
        parts = archive_url.rstrip("/").split("/")
        year, month = parts[-2], parts[-1]
        games = _get_games_by_month(username, year, month).get("games", [])
        all_games.extend(games)
        if len(all_games) >= n:
            break
    # Sort games by end_time (descending), fallback to start_time if needed
    def get_game_time(game):
        return game.get("end_time") or game.get("start_time") or 0
    all_games.sort(key=get_game_time, reverse=True)
    return {"games": all_games[:n]}


@logfire.instrument
def download_pgn(username: str, game_url: str) -> str:
    """
    Download the PGN for a given chess.com game.

    Args:
        username (str): The chess.com username.
        game_url (str): The full URL of the chess.com game (from the 'url' field in game data).

    Returns:
        str: The PGN as a string.

    Raises:
        ValueError: If the PGN is not found for the given game URL and username.
    """
    game_id = _extract_game_id(game_url)
    for year, month in _recent_year_months(3):
        games = _get_games_by_month(username, year, month).get("games", [])
        for game in games:
            if "url" in game and game_id in game["url"]:
                return game.get("pgn", "")
    raise ValueError("PGN not found for this game URL and username")


@logfire.instrument
def _get_latest_archive_year_month(username: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get the year and month of the latest game archive for a user.

    Returns:
        (year, month) as strings, or (None, None) if not found.
    """
    archives_response = client.get_player_game_archives(username)  # type: ignore[reportAttributeAccessIssue]
    archive_urls = archives_response.json.get("archives", [])
    if not archive_urls:
        return None, None
    latest_archive_url = archive_urls[-1]
    parts = latest_archive_url.rstrip("/").split("/")
    return parts[-2], parts[-1]


@logfire.instrument
def _get_games_by_month(username: str, year: str, month: str) -> Dict[str, Any]:
    """
    Fetch games for a user for a specific year and month.
    """
    games_response = client.get_player_games_by_month(username, year, month)  # type: ignore[reportAttributeAccessIssue]
    return games_response.json


@logfire.instrument
def _extract_game_id(game_url: str) -> str:
    """
    Extract the game ID from a chess.com game URL.

    Raises:
        ValueError: If the URL format is invalid.
    """
    m = re.match(r"https://www\.chess\.com/game/\w+/(\d+)", game_url)
    if not m:
        raise ValueError("Invalid chess.com game URL format")
    return m.group(1)


@logfire.instrument
def _recent_year_months(n: int) -> List[Tuple[str, str]]:
    """
    Generate (year, month) tuples for the current and previous n-1 months, in UTC.

    Args:
        n (int): Number of months to generate.

    Returns:
        List of (year, month) tuples as strings.
    """
    now = datetime.now(timezone.utc)
    months = []
    year = now.year
    month = now.month
    for _ in range(n):
        months.append((str(year), str(month).zfill(2)))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return months
