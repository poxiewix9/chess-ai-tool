from datetime import datetime

from mcp.server.fastmcp import FastMCP

from komodo.chessbuddy.lib.welcome import welcome
from komodo.chessbuddy.lib.chesscom import (
    get_profile as chesscom_get_profile,
    get_latest_games as chesscom_get_latest_games,
    download_pgn as chesscom_download_pgn,
)
from komodo.chessbuddy.lib.pgnanalytics import (
    get_user_games_df,
    summarize_user_stats,
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
    """
    return chesscom_get_profile(username)

@mcp.tool()
def chesscom_latest_games(username: str, n: int = 10) -> dict:
    """
    Retrieve the latest games played by a chess.com user.
    """
    return chesscom_get_latest_games(username, n)

@mcp.tool()
def chesscom_download_pgn(username: str, game_url: str) -> str:
    """
    Download the PGN for a given chess.com game.
    """
    return chesscom_download_pgn(username, game_url)

@mcp.tool()
def chesscom_analytics_games(username: str, max_months: int = 3) -> list:
    """
    Get recent games for a user as a list of dicts (DataFrame records).
    """
    df = get_user_games_df(username, max_months=max_months)
    return df.to_dict(orient="records")

@mcp.tool()
def chesscom_analytics_stats(username: str, max_months: int = 3) -> dict:
    """
    Get summary stats for a user.
    """
    df = get_user_games_df(username, max_months=max_months)
    return summarize_user_stats(df, username)


mcp_native = mcp

# Entry point to run the server
if __name__ == "__main__":
    mcp.run(transport="sse")
