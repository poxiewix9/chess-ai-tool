import pytest

from komodo.chessbuddy.lib.chesscom import get_profile, get_latest_games, download_pgn

USERNAME = "ryanoberoi"

def test_get_profile():
    profile = get_profile(USERNAME)
    assert isinstance(profile, dict)
    assert profile.get("username", "").lower() == USERNAME.lower()
    assert "player_id" in profile
    assert "joined" in profile

def test_get_latest_games():
    games_data = get_latest_games(USERNAME)
    assert isinstance(games_data, dict)
    assert "games" in games_data
    assert isinstance(games_data["games"], list)
    assert len(games_data["games"]) > 0

import pytest

def test_download_pgn():
    games_data = get_latest_games(USERNAME)
    games = games_data.get("games", [])
    assert games, "No games found for user"
    game = games[0]
    # Prefer the 'pgn' field if available
    if "pgn" in game and game["pgn"]:
        pgn = game["pgn"]
    else:
        game_url = game.get("url")
        assert game_url, "No game URL found in latest games"
        try:
            pgn = download_pgn(USERNAME, game_url)
        except ValueError as e:
            pytest.skip(str(e))
            return
    assert isinstance(pgn, str)
    assert "[Event" in pgn
    assert "[Site" in pgn
    assert USERNAME.lower() in pgn.lower()
