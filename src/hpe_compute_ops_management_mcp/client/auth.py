"""
Authentication support for HPE GreenLake / Compute Ops Management APIs.
"""

from __future__ import annotations

from ..config import Settings, get_settings


class HPEAuth:
    """
    Authentication helper for HPE GreenLake APIs.

    The access token is obtained from the application settings
    and converted into the Authorization header required by
    the HPE REST APIs.
    """

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        """
        Initialize the authentication helper.

        Args:
            settings:
                Optional application settings object.

                If omitted, the application-wide settings are
                loaded automatically.
        """

        self.settings = (
            settings
            if settings is not None
            else get_settings()
        )

        self._validate_token()

    # ---------------------------------------------------------
    # Token validation
    # ---------------------------------------------------------

    def _validate_token(self) -> None:
        """
        Validate that an HPE GreenLake access token is available.
        """

        token = (
            self.settings
            .hpe_greenlake_access_token
        )

        if not token:
            raise RuntimeError(
                "HPE_GREENLAKE_ACCESS_TOKEN is not configured."
            )

        if not token.strip():
            raise RuntimeError(
                "HPE_GREENLAKE_ACCESS_TOKEN is empty."
            )

    # ---------------------------------------------------------
    # Access token
    # ---------------------------------------------------------

    @property
    def access_token(self) -> str:
        """
        Return the configured HPE GreenLake access token.
        """

        return (
            self.settings
            .hpe_greenlake_access_token
        )

    # ---------------------------------------------------------
    # HTTP headers
    # ---------------------------------------------------------

    def get_auth_headers(self) -> dict[str, str]:
        """
        Return HTTP headers required for HPE API authentication.

        Returns:
            Dictionary containing the Authorization header.
        """

        return {
            "Authorization": (
                f"Bearer {self.access_token}"
            )
        }