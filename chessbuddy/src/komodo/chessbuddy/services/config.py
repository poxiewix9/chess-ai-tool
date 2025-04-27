import os
from enum import Enum
from typing import Type

import modal
from dotenv.main import DotEnv, find_dotenv


class ModalConfig:
    """
    Base configuration class that generates values based on environment name.
    Uses a template pattern to derive configuration values from the environment name.
    """

    # Environment name to be overridden by subclasses
    ENV_NAME = "dev"

    # Base domain for all services
    BASE_DOMAIN = "thechessbuddy.com"

    # Modal org name
    MODAL_ORG = "komodo"

    @classmethod
    def get_modal_org(cls):
        """Return the Modal organization name."""
        return cls.MODAL_ORG if cls.ENV_NAME == "main" else f"{cls.MODAL_ORG}-{cls.ENV_NAME.lower()}"

    @classmethod
    def get_modal_secret_base(cls):
        """Return the Modal secret name."""
        return {"ProdModalConfig": "prod", "StagingModalConfig": "staging"}.get(cls.__name__, "dev")

    @classmethod
    def get_modal_domain(cls, app: str, server: str):
        """Generate domain based on environment name and app name."""
        return f"{cls.get_modal_org()}--{app.lower()}-{server.lower()}-modal-app.modal.run"

    @classmethod
    def get_modal_function(cls, app: str, server: str):
        """Generate domain based on environment name and app name."""
        return f"{cls.get_modal_org()}--{app.lower()}-{server.lower()}.modal.run"


    @classmethod
    def dotenv_secret_dict(cls):
        """Generate secrets based on environment name."""
        env: dict[str, str | None] = DotEnv(find_dotenv()).dict()
        env["LOGFIRE_ENVIRONMENT"] = "modal"
        return env

    @classmethod
    def dotenv_secret(cls) -> modal.Secret:
        """Generate secrets based on environment name."""
        return modal.Secret.from_dict(cls.dotenv_secret_dict())


class ProdModalConfig(ModalConfig):
    """Production environment configuration."""

    ENV_NAME = "Prod"


class StagingModalConfig(ModalConfig):
    """Staging environment configuration."""

    ENV_NAME = "Staging"


class DevModalConfig(ModalConfig):
    """Developer environment configuration."""

    ENV_NAME = "Dev"


class MainConfig(ModalConfig):
    """Main environment configuration."""

    ENV_NAME = "main"


def get_relevant_modal_config() -> Type[ModalConfig]:
    modal_environment = os.getenv("MODAL_ENVIRONMENT", "dev")
    print(f"Getting config for MODAL_ENVIRONMENT: {modal_environment}")

    configs = [ProdModalConfig, StagingModalConfig, DevModalConfig, MainConfig]
    for config in configs:
        if config.ENV_NAME.lower() == modal_environment.lower():
            return config

    raise ValueError(f"Unknown MODAL_ENVIRONMENT: {modal_environment}")


def ensure_modal_env():
    """Set the default modal environment to 'dev' if not set."""
    if "MODAL_ENVIRONMENT" not in os.environ:
        os.environ["MODAL_ENVIRONMENT"] = "dev"
        print("Setting MODAL_ENVIRONMENT to 'dev'")




class ConexioModalApps(Enum):
    CHESSBUDDY = "ChessBuddy"
    TESTING = "Testing"

    def __str__(self):
        return self.value

    def get_domain(self, server: str = "server") -> str:
        return get_relevant_modal_config().get_modal_domain(self.name, server)

    def get_function(self, server: str = "server") -> str:
        return get_relevant_modal_config().get_modal_function(self.name, server)


LOCAL_PYTHON_SOURCES = ["komodo"]


def get_image_with_uv_install():
    return modal.Image.debian_slim().pip_install_from_pyproject("pyproject.toml")


def get_image_with_source_and_uv_install():
    return get_image_with_uv_install().add_local_python_source(*LOCAL_PYTHON_SOURCES, copy=True)


def get_workspaces_name():
    return "workspaces"


def get_workspaces_volume():
    return modal.Volume.from_name(get_workspaces_name(), create_if_missing=True)


def read_file_from_modal(volume: modal.Volume, path: str):
    data = b""
    for chunk in volume.read_file(path):
        data += chunk
    return data.decode("utf-8")
