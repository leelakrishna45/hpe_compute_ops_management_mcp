"""
MCP tools for HPE Compute Ops Management environment monitoring.

This module contains MCP-facing tools for environment-level
operational information.

Server-specific functionality belongs in:

    tools/servers.py
    tools/health.py
    tools/alerts.py
    tools/utilization.py

The environment tools combine information from those areas when
an environment-wide view is required.

MCP server registration is intentionally deferred until all tool
modules have been created.
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
    """

    global _client

    if _client is None:
        _client = HPEComputeOpsClient()

    return _client


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _api_error_response(
    exc: HPEAPIError,
) -> dict[str, Any]:
    """
    Convert an HPE API exception into an MCP-friendly response.
    """

    result: dict[str, Any] = {
        "success": False,
        "error": str(exc),
    }

    if exc.status_code is not None:
        result["status_code"] = exc.status_code

    return result


def _extract_items(
    response: Any,
    resource_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    Extract collection items from an HPE API response.

    The helper supports several common collection envelope
    formats while preserving the raw response elsewhere.
    """

    if isinstance(response, list):
        return [
            item
            for item in response
            if isinstance(item, dict)
        ]

    if not isinstance(response, dict):
        return []

    candidate_keys: list[str] = [
        "items",
        "members",
        "data",
        "results",
    ]

    if resource_name:
        candidate_keys.insert(
            0,
            resource_name,
        )

    for key in candidate_keys:

        value = response.get(key)

        if isinstance(value, list):
            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    return []


def _field(
    resource: dict[str, Any],
    *names: str,
) -> Any:
    """
    Return the first available value for a set of possible
    field names.
    """

    for name in names:

        if name in resource:
            return resource[name]

    return None


def _normalize_server(
    server: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract the environment-level information needed for the
    summary.
    """

    return {
        "server_id": _field(
            server,
            "id",
            "serverId",
        ),
        "hostname": _field(
            server,
            "hostname",
            "hostName",
            "name",
        ),
        "health": _field(
            server,
            "health",
            "healthStatus",
            "status",
        ),
        "connection_status": _field(
            server,
            "connectionStatus",
            "connectionState",
        ),
        "power_state": _field(
            server,
            "powerState",
            "power",
        ),
    }


def _status_key(
    value: Any,
) -> str:
    """
    Convert a status value into a consistent dictionary key.
    """

    if value is None:
        return "UNKNOWN"

    value = str(value).strip()

    if not value:
        return "UNKNOWN"

    return value.upper()


def _distribution(
    servers: list[dict[str, Any]],
    field_name: str,
) -> dict[str, int]:
    """
    Build a status distribution for the requested server field.
    """

    result: dict[str, int] = {}

    for server in servers:

        key = _status_key(
            server.get(field_name)
        )

        result[key] = (
            result.get(key, 0)
            + 1
        )

    return result


def _is_critical(
    value: Any,
) -> bool:
    """
    Determine whether a status represents a critical state.

    This helper intentionally uses a small set of explicit
    values rather than making assumptions about unknown states.
    """

    if value is None:
        return False

    return _status_key(value) in {
        "CRITICAL",
        "CRIT",
        "FAILED",
        "FAILURE",
        "UNHEALTHY",
    }


# ------------------------------------------------------------------
# MCP tool registration
# ------------------------------------------------------------------

def register_tools(mcp) -> None:
    """
    Register environment-level MCP tools with FastMCP.

    server.py will call this function when all tool modules
    are registered together.
    """

    # ==============================================================
    # get_environment_summary
    # ==============================================================

    @mcp.tool()
    async def get_environment_summary() -> dict:
        """
        Get a high-level operational summary of the HPE Compute
        Ops Management server environment.

        This tool is intended for dashboard-style questions such
        as:

            "How is my server environment doing?"

            "How many servers do I have?"

            "How many servers are critical?"

            "Show me the health distribution of my servers."

        Returns:
            Server count, health distribution, connection
            distribution, power-state distribution, and critical
            server information.
        """

        try:

            client = _get_client()

            response = await client.get(
                v1.SERVERS,
                params={
                    "limit": 1000,
                    "offset": 0,
                },
            )

            servers = _extract_items(
                response,
                "servers",
            )

            normalized_servers = [
                _normalize_server(server)
                for server in servers
            ]

            health_distribution = _distribution(
                normalized_servers,
                "health",
            )

            connection_distribution = _distribution(
                normalized_servers,
                "connection_status",
            )

            power_distribution = _distribution(
                normalized_servers,
                "power_state",
            )

            critical_servers = [
                {
                    "server_id": server.get(
                        "server_id"
                    ),
                    "hostname": server.get(
                        "hostname"
                    ),
                    "health": server.get(
                        "health"
                    ),
                    "connection_status": server.get(
                        "connection_status"
                    ),
                    "power_state": server.get(
                        "power_state"
                    ),
                }
                for server in normalized_servers
                if _is_critical(
                    server.get("health")
                )
            ]

            return {
                "success": True,
                "summary": {
                    "total_servers": len(
                        normalized_servers
                    ),
                    "health_distribution":
                        health_distribution,
                    "connection_distribution":
                        connection_distribution,
                    "power_state_distribution":
                        power_distribution,
                    "critical_server_count":
                        len(
                            critical_servers
                        ),
                },
                "critical_servers":
                    critical_servers,
            }

        except HPEAPIError as exc:

            return _api_error_response(
                exc
            )

    # ==============================================================
    # get_server_counts
    # ==============================================================

    @mcp.tool()
    async def get_server_counts() -> dict:
        """
        Get basic server counts for the HPE Compute Ops Management
        environment.

        Returns:

        - Total number of managed servers
        - Number of servers in each health state
        - Number of servers in each connection state
        """

        try:

            client = _get_client()

            response = await client.get(
                v1.SERVERS,
                params={
                    "limit": 1000,
                    "offset": 0,
                },
            )

            servers = _extract_items(
                response,
                "servers",
            )

            normalized_servers = [
                _normalize_server(server)
                for server in servers
            ]

            return {
                "success": True,
                "total_servers": len(
                    normalized_servers
                ),
                "health_distribution":
                    _distribution(
                        normalized_servers,
                        "health",
                    ),
                "connection_distribution":
                    _distribution(
                        normalized_servers,
                        "connection_status",
                    ),
            }

        except HPEAPIError as exc:

            return _api_error_response(
                exc
            )

    # ==============================================================
    # get_critical_servers
    # ==============================================================

    @mcp.tool()
    async def get_critical_servers() -> dict:
        """
        Get servers that are currently reporting a critical
        or explicitly unhealthy state.

        This tool is useful for operational triage.

        Returns:
            List of servers whose reported health state is
            explicitly critical or unhealthy.
        """

        try:

            client = _get_client()

            response = await client.get(
                v1.SERVERS,
                params={
                    "limit": 1000,
                    "offset": 0,
                },
            )

            servers = _extract_items(
                response,
                "servers",
            )

            critical_servers: list[
                dict[str, Any]
            ] = []

            for server in servers:

                normalized = _normalize_server(
                    server
                )

                if _is_critical(
                    normalized.get("health")
                ):
                    critical_servers.append(
                        normalized
                    )

            return {
                "success": True,
                "count": len(
                    critical_servers
                ),
                "servers": critical_servers,
            }

        except HPEAPIError as exc:

            return _api_error_response(
                exc
            )