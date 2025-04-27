import logfire
import streamlit as st

from komodo.chessbuddy.config.logging import init_logfire

init_logfire("streamlit_chessbuddy")

st.set_page_config(page_title="Chess Buddy Chat", page_icon="♟️", layout="centered")

st.title("♟️ Chess Buddy Chat")
st.write("Chat with your Chess Buddy! Type your message below and press Enter.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

from komodo.chessbuddy.scripts.mcp_chat_utils import (
    tool_collection_context,
    build_agent,
    get_agent_model,
    build_prompt,
    format_with_openai,
)

class ToolAgentSession:
    def __init__(self):
        self.ctx = tool_collection_context()
        self.tool_collection = self.ctx.__enter__()
        self.model = get_agent_model()
        self.agent = build_agent(
            tools=[*self.tool_collection.tools],
            model=self.model,
            additional_authorized_imports=["*"],
        )

    def close(self):
        if self.ctx:
            self.ctx.__exit__(None, None, None)
            self.ctx = None

# Initialize ToolAgentSession if not already in session state
if "tool_agent_session" not in st.session_state:
    st.session_state.tool_agent_session = ToolAgentSession()

# Display chat history
for entry in st.session_state.chat_history:
    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get bot response
    with logfire.span("Thinking..."):
        with st.spinner("Thinking..."):
            prompt = build_prompt(user_input)
            agent = st.session_state.tool_agent_session.agent
            result = agent.run(prompt, reset=False)
            bot_response = format_with_openai(user_input, result)

        st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
        with st.chat_message("assistant"):
            st.markdown(bot_response)

# Optionally, add a cleanup callback to close the context when the Streamlit session ends
# (Streamlit does not provide a direct session end hook, but you could add a button to manually close)
