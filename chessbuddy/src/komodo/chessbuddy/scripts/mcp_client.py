import openai
from dotenv import load_dotenv
from smolagents import CodeAgent, OpenAIServerModel, ToolCollection

INSTRUCTIONS = (
    " Only use the mcp tools provided. and only use specific usernames. "
    "Only call the mcp tool once and return the values. "
    "Analyze the last 1 months of games by default when asking for a summary. "
)

def format_with_openai(question, result, max_result_chars=10000):
    """
    Format the MCP tool result into a nice, user-friendly response using OpenAI.
    Truncates the result if it is too long for the model context window.
    """
    if isinstance(result, str) and len(result) > max_result_chars:
        truncated_result = result[:max_result_chars] + "\n\n[Result truncated due to length]"
    else:
        truncated_result = result
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Format the following tool result into a clear, user-friendly answer to the user's question."},
            {"role": "user", "content": f"Question: {question}\nResult: {truncated_result}\n\nFormat this result as a nice, readable response for the user."}
        ],
        max_tokens=512,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def main():
    load_dotenv()
    model = OpenAIServerModel(model_id="gpt-4o")
    server_parameters = {"url": "http://0.0.0.0:8000/sse"}

    with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
        agent = CodeAgent(tools=[*tool_collection.tools], model=model, add_base_tools=True, 
                          additional_authorized_imports=["*"])
        print("Chess Buddy Chat (type 'exit' to quit)")
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    print("Exiting chat.")
                    break
                prompt = f"{user_input}{INSTRUCTIONS}"
                result = agent.run(prompt, reset=False)
                formatted = format_with_openai(user_input, result)
                print(f"Bot: {formatted}")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting chat.")
                break

if __name__ == "__main__":
    main()
