from fastapi import APIRouter, Body, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse

from komodo.chessbuddy.lib.welcome import welcome
from komodo.chessbuddy.lib.chesscom import (
    get_profile,
    get_latest_games,
    download_pgn,
)

router = APIRouter(prefix="/chessbuddy", tags=["chessbuddy"])


@router.post("/welcome", response_model=str, description="Respond with a special welcome message")
async def welcome_api(name: str = Body(...)):
    return welcome(name)


@router.get("/chesscom/profile/{username}", description="Get chess.com profile for a user")
async def chesscom_profile(username: str):
    return await run_in_threadpool(get_profile, username)


@router.get("/chesscom/latest-games/{username}", description="Get latest chess.com games for a user")
async def chesscom_latest_games(username: str):
    return await run_in_threadpool(get_latest_games, username)


@router.get("/chesscom/pgn", response_class=PlainTextResponse, description="Download PGN for a chess.com game")
async def chesscom_pgn(
    username: str = Query(..., description="Chess.com username"),
    game_url: str = Query(..., description="Full chess.com game URL")
):
    return await run_in_threadpool(download_pgn, username, game_url)


# --- PGN Analytics Endpoints ---
from komodo.chessbuddy.lib.pgnanalytics import get_user_games_df, summarize_user_stats

@router.get("/chesscom/analytics/games/{username}", description="Get recent games for a user as DataFrame (JSON)")
async def chesscom_analytics_games(username: str, max_months: int = 3):
    def get_df_dict():
        df = get_user_games_df(username, max_months=max_months)
        return df.to_dict(orient="records")
    return await run_in_threadpool(get_df_dict)

@router.get("/chesscom/analytics/stats/{username}", description="Get summary stats for a user")
async def chesscom_analytics_stats(username: str, max_months: int = 3):
    def get_stats():
        df = get_user_games_df(username, max_months=max_months)
        return summarize_user_stats(df, username)
    return await run_in_threadpool(get_stats)
