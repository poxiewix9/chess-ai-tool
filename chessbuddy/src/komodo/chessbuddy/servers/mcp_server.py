from datetime import datetime

from mcp.server.fastmcp import FastMCP

from komodo.chessbuddy.lib.welcome import welcome
from komodo.chessbuddy.lib.chesscom import (
    get_profile as chesscom_get_profile,
    get_latest_games as chesscom_get_latest_games,
    download_pgn as chesscom_download_pgn,
)

# This is the shared MCP server instance
mcp = FastMCP(name="Chess Buddy MCP Server")


@mcp.tool()
def welcome_tool(name: str) -> str:
    """
    Respond with welcome message
    Args:
        name: name of the user
    Returns:
        A string with a welcome message
    """
    return welcome(name)


@mcp.resource("sys://current_time")
def get_current_time():
    """
    Get current time that the user wants to see
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def chesscom_profile(username: str) -> dict:
    """
    Retrieve the public profile information for a chess.com user.

    Args:
        username (str): The chess.com username.

    Returns:
        dict: The user's profile information as returned by the chess.com public API.
    """
    return chesscom_get_profile(username)


@mcp.tool()
def chesscom_latest_games(username: str, n: int = 10) -> dict:
    """
    Retrieve the latest games played by a chess.com user.

    Args:
        username (str): The chess.com username.
        n (int, optional): Number of recent games to return (default 10).

    Returns:
        dict: The latest games data as returned by the chess.com public API.
    """
    return chesscom_get_latest_games(username, n)


@mcp.tool()
def chesscom_download_pgn(game_url: str) -> str:
    """
    Download the PGN for a given chess.com game.

    Args:
        game_url (str): The full URL of the chess.com game (from the 'url' field in game data).

    Returns:
        str: The PGN as a string.
    """
    return chesscom_download_pgn(game_url)


mcp_native = mcp

# Entry point to run the server
if __name__ == "__main__":
    mcp.run(transport="sse")
