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
async def chesscom_pgn(game_url: str = Query(..., description="Full chess.com game URL")):
    return await run_in_threadpool(download_pgn, game_url)
