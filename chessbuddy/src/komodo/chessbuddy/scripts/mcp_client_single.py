import logfire
import openai
import sys
from dotenv import load_dotenv
from smolagents import CodeAgent, OpenAIServerModel, ToolCollection

from komodo.chessbuddy.config.logging import init_logfire
from komodo.chessbuddy.config.env import Settings
init_logfire("mcp_client_single")
openai.api_key = Settings.OPENAI_API_KEY

INSTRUCTIONS = (
    " Only use the mcp tools provided. and only use specific usernames. "
    "Only call the mcp tool once and return the values. "
)


@logfire.instrument(record_return=True)
def format_with_openai(question, result, max_result_chars=10000):
    if isinstance(result, str) and len(result) > max_result_chars:
        truncated_result = result[:max_result_chars] + "\n\n[Result truncated due to length]"
    else:
        truncated_result = result
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "Format the following tool result into a detailed, complete, and user-friendly answer to the user's question. "
                    "List all available fields and their values from the tool result. "
                    "Do not summarize, omit, or refer the user elsewhere; include all raw details in your response. "
                    "Output will be displayed on streamlit, format images and tables with markdown. "
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\nResult: {truncated_result}\n\n"
                           f"Format this result as a detailed, readable response for the user."
            }
        ],
        max_tokens=2048,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def run_mcp_chat(user_input: str) -> str:
    load_dotenv()
    model = OpenAIServerModel(model_id="gpt-4o")
    mcp_sse_url = Settings.CHESSBUDDY_MCP_SERVER_URL.rstrip("/") + "/sse"
    server_parameters = {"url": mcp_sse_url}
    if not user_input:
        return "No input provided."
    prompt = f"{user_input}{INSTRUCTIONS}"
    with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
        agent = CodeAgent(tools=[*tool_collection.tools], model=model, add_base_tools=True)
        result = agent.run(prompt, reset=True)
        formatted = format_with_openai(user_input, result)
        return formatted

def main():
    # CLI entry point
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:]).strip()
    else:
        user_input = sys.stdin.read().strip()
    print(run_mcp_chat(user_input))

if __name__ == "__main__":
    main()
