import logfire
from fastapi import FastAPI

from komodo.chessbuddy.config.logging import init_logfire
from komodo.chessbuddy.router.routes import router

init_logfire("fastapi_chessbuddy")
app = FastAPI(
    description="Chess Buddy FastAPI Server",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/openapi.json",
)

logfire.instrument_fastapi(app)
app.include_router(router)

chess_buddy_app = app

if __name__ == "__main__":
    port = 8500  # int(os.getenv("PORT", "3000"))

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port)
