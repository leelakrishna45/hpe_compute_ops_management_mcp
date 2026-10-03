"""
HPE Compute Ops Management API client package.

This package contains the HTTP client, authentication handling,
exceptions, and HPE API endpoint definitions used by the MCP tools.
"""

from .client import HPEComputeOpsClient
from .exceptions import (
    HPEAPIError,
    HPEAuthenticationError,
    HPEAuthorizationError,
    HPEBadRequestError,
    HPENotFoundError,
    HPEServerError,
)
from .auth import HPEAuth


__all__ = [
    "HPEComputeOpsClient",
    "HPEAuth",
    "HPEAPIError",
    "HPEAuthenticationError",
    "HPEAuthorizationError",
    "HPEBadRequestError",
    "HPENotFoundError",
    "HPEServerError",
]