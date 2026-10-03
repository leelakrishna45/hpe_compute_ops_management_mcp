"""
MCP tools for HPE Compute Ops Management servers.

This module contains MCP-facing tools for discovering servers
and retrieving detailed server information.

The tools in this module do not perform HTTP requests directly.
They use HPEComputeOpsClient, which is responsible for:

- Authentication
- HTTP communication
- Retries
- Timeout handling
- API error handling
"""

from __future__ import annotations

from typing import Any

from ..client.client import HPEComputeOpsClient
from ..client.endpoints import v1
from ..client.exceptions import HPEAPIError


# ------------------------------------------------------------------
# Shared client
# ------------------------------------------------------------------

_client: HPEComputeOpsClient | None = None


def _get_client() -> HPEComputeOpsClient:
    """
    Return the shared HPE Compute Ops Management API client.

    A shared client allows HTTP connections to be reused across
    multiple MCP tool calls.
    """

    global _client

    if _client is None:
        _client = HPEComputeOpsClient()

    return _client


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _validate_limit(limit: int) -> int:
    """
    Validate the requested page size.
    """

    if limit < 1:
        raise ValueError(
            "limit must be greater than or equal to 1."
        )

    if limit > 1000:
        raise ValueError(
            "limit must not exceed 1000."
        )

    return limit


def _validate_offset(offset: int) -> int:
    """
    Validate the pagination offset.
    """

    if offset < 0:
        raise ValueError(
            "offset must be greater than or equal to 0."
        )

    return offset


def _clean_select(
    select: list[str] | None,
) -> str | None:
    """
    Convert a list of selected fields into the format expected
    by the HPE API.

    Example:

        ["name", "health", "powerState"]

    becomes:

        "name,health,powerState"
    """

    if not select:
        return None

    cleaned = [
        field.strip()
        for field in select
        if field and field.strip()
    ]

    if not cleaned:
        return None

    return ",".join(cleaned)


def _api_error_response(
    exc: HPEAPIError,
) -> dict[str, Any]:
    """
    Convert an HPE API exception into a consistent MCP response.

    The raw exception object is intentionally not returned.
    """

    result: dict[str, Any] = {
        "success": False,
        "error": str(exc),
    }

    if exc.status_code is not None:
        result["status_code"] = exc.status_code

    return result


# ------------------------------------------------------------------
# MCP Tool: get_servers
# ------------------------------------------------------------------

@mcp.tool()
async def get_servers(
    filter: str | None = None,
    select: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """
    Get HPE servers managed by Compute Ops Management.

    Use this tool to discover servers and obtain their high-level
    health, connection, power, and inventory information.

    Args:
        filter:
            Optional HPE/OData filter expression.

        select:
            Optional list of fields to return.

        limit:
            Maximum number of servers to return.

        offset:
            Pagination offset.

    Returns:
        Server collection and pagination information.
    """

    try:
        limit = _validate_limit(limit)
        offset = _validate_offset(offset)

        select_value = _clean_select(select)

        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if filter:
            params["filter"] = filter

        if select_value:
            params["select"] = select_value

        client = _get_client()

        response = await client.get(
            v1.SERVERS,
            params=params,
        )

        return {
            "success": True,
            "data": response,
        }

    except HPEAPIError as exc:
        return _api_error_response(exc)

    except ValueError as exc:
        return {
            "success": False,
            "error": str(exc),
        }


# ------------------------------------------------------------------
# MCP Tool: get_server
# ------------------------------------------------------------------

@mcp.tool()
async def get_server(
    server_id: str,
) -> dict:
    """
    Get detailed information about an HPE server.

    Args:
        server_id:
            HPE Compute Ops Management server identifier.

    Returns:
        Detailed server information including health,
        connection, power state, hardware and available
        inventory information.
    """

    if not server_id or not server_id.strip():
        return {
            "success": False,
            "error": "server_id is required.",
        }

    server_id = server_id.strip()

    try:
        client = _get_client()

        endpoint = v1.SERVER_BY_ID.format(
            server_id=server_id,
        )

        response = await client.get(
            endpoint,
        )

        return {
            "success": True,
            "data": response,
        }

    except HPEAPIError as exc:
        return _api_error_response(exc)