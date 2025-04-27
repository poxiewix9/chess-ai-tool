import logfire
from dotenv import load_dotenv
from smolagents import CodeAgent, OpenAIServerModel, ToolCollection
from komodo.chessbuddy.config.env import Settings
from .format_with_openai import format_with_openai

from contextlib import contextmanager

@contextmanager
def tool_collection_context():
    """
    Context manager for ToolCollection using MCP server URL from settings.
    """
    mcp_server_url = Settings.CHESSBUDDY_MCP_SERVER_URL
    mcp_sse_url = mcp_server_url.rstrip("/") + "/sse"
    server_parameters = {"url": mcp_sse_url}
    with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
        yield tool_collection


INSTRUCTIONS = (
    " Only use the mcp tools provided. and only use specific usernames. "
    "Only call the mcp tool once and return the values. "
    "Analyze the last 1 months of games by default when asking for a summary. "
)

def get_agent_model(model_id: str = "gpt-4o"):
    model = OpenAIServerModel(model_id=model_id)
    logfire.instrument_openai(model.client)
    return model

def build_prompt(user_input: str, instructions: str = INSTRUCTIONS) -> str:
    return f"{user_input}{instructions}"

def build_agent(
    tools,
    model,
    additional_authorized_imports=None,
):
    return CodeAgent(
        tools=tools,
        model=model,
        add_base_tools=True,
        additional_authorized_imports=additional_authorized_imports or [],
    )

def run_agent_and_format(
    user_input,
    tools,
    model_id: str = "gpt-4o",
    reset=False,
    additional_authorized_imports=None,
):
    model = get_agent_model(model_id=model_id)
    prompt = build_prompt(user_input, INSTRUCTIONS)
    agent = build_agent(
        tools=tools,
        model=model,
        additional_authorized_imports=additional_authorized_imports,
    )
    result = agent.run(prompt, reset=reset)
    formatted = format_with_openai(user_input, result)
    return formatted


def run_mcp_chat_generic(
    user_input: str,
    model_id: str = "gpt-4o",
    reset: bool = False,
    additional_authorized_imports=None,
) -> str:
    """
    Generic MCP chat runner for both single and multi-agent chat.
    """ 
    with tool_collection_context() as tool_collection:
        return run_agent_and_format(
            user_input=user_input,
            tools=[*tool_collection.tools],
            model_id=model_id,
            reset=reset,
            additional_authorized_imports=additional_authorized_imports,
        )
