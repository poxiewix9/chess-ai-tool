import logfire
import streamlit as st

from komodo.chessbuddy.config.logging import init_logfire

init_logfire("streamlit_chessbuddy")

st.set_page_config(page_title="Chess Buddy Chat", page_icon="♟️", layout="centered")

st.title("♟️ Chess Buddy Chat")
st.write("Chat with your Chess Buddy! Type your message below and press Enter.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


from komodo.chessbuddy.scripts.mcp_client_single import run_mcp_chat

@logfire.instrument(record_return=True)
def call_mcp_client(user_message):
    """
    Call the MCP client chat function directly and return the response.
    """
    return run_mcp_chat(user_message)

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
            bot_response = call_mcp_client(user_input)

        st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
        with st.chat_message("assistant"):
            st.markdown(bot_response)
