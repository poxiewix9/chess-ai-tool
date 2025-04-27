import modal

from .config import get_relevant_modal_config, get_image_with_uv_install

config = get_relevant_modal_config()
image = get_image_with_uv_install()
app = modal.App(name="ChessBuddy", image=image)


@app.cls(
    image=image,
    secrets=[config.dotenv_secret()],
    min_containers=1,
    max_containers=3,
    memory=512,
    scaledown_window=300,
    enable_memory_snapshot=False,
)
@modal.concurrent(max_inputs=100)
class McpServer:
    @modal.asgi_app()
    def app(self):
        from komodo.chessbuddy.servers.mcp_server import mcp_native
        return mcp_native.sse_app()


@app.cls(
    image=image,
    secrets=[config.dotenv_secret()],
    min_containers=1,
    max_containers=3,
    memory=512,
    scaledown_window=300,
    enable_memory_snapshot=False,
)
@modal.concurrent(max_inputs=100)
class FastApiServer:
    @modal.asgi_app()
    def app(self):
        from komodo.chessbuddy.servers.fastapi_server import chess_buddy_app
        return chess_buddy_app
