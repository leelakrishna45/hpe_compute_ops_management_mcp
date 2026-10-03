"""
Exceptions used by the HPE Compute Ops Management API client.
"""

from __future__ import annotations

from typing import Any


class HPEAPIError(Exception):
    """
    Base exception for HPE Compute Ops Management API errors.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: Any | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        """
        Return a human-readable error message.
        """

        if self.status_code is not None:
            return (
                f"{self.message} "
                f"(HTTP {self.status_code})"
            )

        return self.message


class HPEAuthenticationError(HPEAPIError):
    """
    Raised when authentication with HPE GreenLake fails.

    Typically corresponds to HTTP 401.
    """

    pass


class HPEAuthorizationError(HPEAPIError):
    """
    Raised when the authenticated user does not have
    permission to access the requested resource.

    Typically corresponds to HTTP 403.
    """

    pass


class HPEBadRequestError(HPEAPIError):
    """
    Raised when HPE rejects a request because the request
    parameters or payload are invalid.

    Typically corresponds to HTTP 400.
    """

    pass


class HPENotFoundError(HPEAPIError):
    """
    Raised when the requested HPE resource cannot be found.

    Typically corresponds to HTTP 404.
    """

    pass


class HPEServerError(HPEAPIError):
    """
    Raised when HPE Compute Ops Management returns a
    server-side error.

    Typically corresponds to HTTP 5xx.
    """

    pass


class HPERateLimitError(HPEAPIError):
    """
    Raised when the HPE API rate limit has been exceeded.

    Typically corresponds to HTTP 429.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = 429,
        response: Any | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            response=response,
        )

        self.retry_after = retry_after


class HPETimeoutError(HPEAPIError):
    """
    Raised when a request to HPE Compute Ops Management
    exceeds the configured timeout.
    """

    pass


class HPEConnectionError(HPEAPIError):
    """
    Raised when the MCP server cannot connect to the
    HPE Compute Ops Management API.
    """

    pass