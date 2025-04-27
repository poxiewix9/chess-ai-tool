import openai

from komodo.chessbuddy.config.env import Settings
from komodo.chessbuddy.config.logging import init_logfire
from komodo.chessbuddy.scripts.mcp_chat_utils import run_mcp_chat_generic

init_logfire("mcp_client_multi")
openai.api_key = Settings.OPENAI_API_KEY

INSTRUCTIONS = (
    " Only use the mcp tools provided. and only use specific usernames. "
    "Only call the mcp tool once and return the values. "
    "Analyze the last 1 months of games by default when asking for a summary. "
)


def run_mcp_multi_chat(user_input: str) -> str:
    return run_mcp_chat_generic(
        user_input=user_input,
        reset=False,
        additional_authorized_imports=["*"],
    )

def main():
    print("Chess Buddy Chat (type 'exit' to quit)")
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting chat.")
                break
            response = run_mcp_multi_chat(user_input)
            print(f"Bot: {response}")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat.")
            break

if __name__ == "__main__":
    main()
