import openai
from dotenv import load_dotenv
from smolagents import CodeAgent, OpenAIServerModel, ToolCollection


def main():
    load_dotenv()
    model = OpenAIServerModel(model_id="gpt-4o")

    # dont forget to install mcp:  uv add "smolagents[mcp]"
    # If a dict is provided, it is assumed to be the parameters of `mcp.client.sse.sse_client`.
    server_parameters = {"url": "https://conexio-dev--sample-mcpserver-app.modal.run/sse"}
    server_parameters = {"url": "http://0.0.0.0:8000/sse"}

    question = "Show me the last 5 games by ryanoberoi."


    with (ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection):
        print(*tool_collection.tools)
        agent = CodeAgent(tools=[*tool_collection.tools], model=model, add_base_tools=True)
        result = agent.run(f"{question} "
                  "Only use the mcp tools provided. and only use specific usernames. "
                  "Only call the mcp tool once and return the values.")

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

        formatted = format_with_openai(question, result)
        print(formatted)


if __name__ == "__main__":
    main()
