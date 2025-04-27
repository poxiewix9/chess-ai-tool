import sys

import openai

from komodo.chessbuddy.config.env import Settings
from komodo.chessbuddy.config.logging import init_logfire
from komodo.chessbuddy.scripts.mcp_chat_utils import run_mcp_chat_generic

init_logfire("mcp_client_single")
openai.api_key = Settings.OPENAI_API_KEY

INSTRUCTIONS = (
    " Only use the mcp tools provided. and only use specific usernames. "
    "Only call the mcp tool once and return the values. "
)

def run_mcp_chat(user_input: str) -> str:
    if not user_input:
        return "No input provided."

    return run_mcp_chat_generic(
        user_input=user_input,
        reset=True,
        additional_authorized_imports=[],
    )

def main():
    # CLI entry point
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:]).strip()
    else:
        user_input = sys.stdin.read().strip()
    print(run_mcp_chat(user_input))

if __name__ == "__main__":
    main()
