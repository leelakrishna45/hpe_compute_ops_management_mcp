"""
Application configuration for the HPE Compute Ops Management MCP server.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Values can be provided through environment variables
    or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---------------------------------------------------------
    # HPE GreenLake / Compute Ops Management
    # ---------------------------------------------------------

    hpe_greenlake_api_base_url: str = Field(
        default="https://us-west.api.greenlake.hpe.com",
        description=(
            "Base URL for the HPE GreenLake API."
        ),
    )

    hpe_greenlake_access_token: str = Field(
        ...,
        description=(
            "HPE GreenLake API access token."
        ),
    )

    # ---------------------------------------------------------
    # HTTP client
    # ---------------------------------------------------------

    http_timeout: float = Field(
        default=60.0,
        description=(
            "HTTP request timeout in seconds."
        ),
    )

    http_max_retries: int = Field(
        default=3,
        description=(
            "Maximum number of retries for transient "
            "HTTP failures."
        ),
    )

    # ---------------------------------------------------------
    # API behavior
    # ---------------------------------------------------------

    default_page_size: int = Field(
        default=50,
        ge=1,
        le=500,
        description=(
            "Default page size for HPE API requests."
        ),
    )

    max_page_size: int = Field(
        default=500,
        ge=1,
        le=1000,
        description=(
            "Maximum page size allowed by the MCP."
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return the application settings.

    The settings object is cached so that environment
    configuration is loaded only once during the process
    lifetime.
    """

    return Settings()