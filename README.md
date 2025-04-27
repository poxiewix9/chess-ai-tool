# The Chess Buddy Project

A modular chess analysis and chat assistant platform, featuring:
- A Streamlit-based chat interface for interactive chess analysis and conversation.
- An MCP (Model Context Protocol) server for advanced API-based chess operations.
- Extensible Python backend with support for chess.com integration, PGN analytics, and more.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Streamlit Chat App](#running-the-streamlit-chat-app)
- [MCP Server & Client](#mcp-server--client)
  - [Running the MCP Server](#running-the-mcp-server)
  - [Testing with MCP Client](#testing-with-mcp-client)
- [Development Workflow](#development-workflow)
- [Running Tests](#running-tests)
- [License](#license)

---

## Project Structure

```
.
├── main.py
├── streamlit_chat.py
├── pyproject.toml
├── uv.lock
├── chessbuddy/
│   ├── pyproject.toml
│   ├── README.md
│   └── src/
│       └── komodo/
│           └── chessbuddy/
│               ├── servers/
│               │   └── mcp_server.py
│               ├── scripts/
│               │   ├── mcp_client.py
│               │   ├── mcp_client_single.py
│               │   └── mcp_chat_utils.py
│               ├── tests/
│               │   └── test_chesscom.py
│               └── ...
```

---

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. **Install uv** (if not already installed):

   ```bash
   pip install uv
   ```

2. **Sync all dependencies and extras:**

   ```bash
   uv sync --all-packages --all-extras
   ```

---

## Running the Streamlit Chat App

The main chat interface is built with Streamlit.

To launch the chat app:

```bash
streamlit run streamlit_chat.py
```

This will start a local Streamlit server. Open the provided URL in your browser to interact with the Chess Buddy chat interface.

---

## MCP Server & Client

### Running the MCP Server

The MCP server provides an API for chess operations and can be run using the configured script:

```bash
uv run chessbuddy
```

This will start the MCP server, typically on `localhost:8000` (or as configured in the server script).


### Testing with MCP Client

There are two client scripts for interacting with the MCP server:

- **mcp_client.py**: For general client-server interaction.
- **mcp_client_single.py**: For single-request testing.

To test the MCP server, open a new terminal and run:

```bash
uv run chessbuddy_mcp_client
```

Or, for a single request, you can still use:

```bash
python chessbuddy/src/komodo/chessbuddy/scripts/mcp_client_single.py
```

You may need to adjust arguments or configuration as needed; see the script source for details.

---

## Development Workflow

- All dependencies are managed with `uv` and specified in `pyproject.toml`.
- The backend code is organized under `chessbuddy/src/komodo/chessbuddy/`.
- Scripts for formatting, client/server interaction, and utilities are in the `scripts/` directory.
- The MCP server and client scripts are configured in `chessbuddy/pyproject.toml` under `[project.scripts]` for convenient execution with `uv run -p chessbuddy ...`.
- Configuration and service logic are modularized for easy extension.

**Recommended steps for development:**
1. Sync dependencies: `uv sync --all-packages --all-extras`
2. Run the Streamlit app or MCP server as needed using the provided scripts.
3. Use the client scripts to test server endpoints.
4. Add or run tests as described below.

---

## Running Tests

Tests are located in `chessbuddy/src/komodo/chessbuddy/tests/`.

To run all tests, use:

```bash
uv run pytest chessbuddy/src/komodo/chessbuddy/tests/
```

Or, to run a specific test file:

```bash
uv run pytest chessbuddy/src/komodo/chessbuddy/tests/test_chesscom.py
```

This ensures tests are run in the correct environment with all dependencies managed by uv.

---

## License

This project is provided under the MIT License. See [LICENSE](LICENSE) for details.
