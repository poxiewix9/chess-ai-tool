from pydantic_settings import BaseSettings

class SettingsClass(BaseSettings):
    OPENAI_API_KEY: str = ""
    LOGFIRE_TOKEN: str = ""
    LOGFIRE_ENVIRONMENT: str = "development"
    CHESSBUDDY_MCP_SERVER_URL: str = "http://localhost:8000"

Settings = SettingsClass()
