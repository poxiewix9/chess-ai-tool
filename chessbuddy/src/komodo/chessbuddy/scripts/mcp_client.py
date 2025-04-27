import openai
from dotenv import load_dotenv

load_dotenv()

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


def build_full_prompt(chat_history):
    # Build a prompt from the full chat history (user and bot turns)
    prompt = ""
    for entry in chat_history:
        if entry["role"] == "user":
            prompt += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            prompt += f"Bot: {entry['content']}\n"
    prompt += "Bot:"
    return prompt

def main():
    print("Chess Buddy Chat (type 'exit' to quit)")
    chat_history = []
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting chat.")
                break
            chat_history.append({"role": "user", "content": user_input})
            # Build prompt from full history
            full_prompt = build_full_prompt(chat_history)
            response = run_mcp_chat_generic(
                user_input=full_prompt,
                reset=False,
                additional_authorized_imports=["*"],
            )
            print(f"Bot: {response}")
            chat_history.append({"role": "assistant", "content": response})
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat.")
            break

if __name__ == "__main__":
    main()
