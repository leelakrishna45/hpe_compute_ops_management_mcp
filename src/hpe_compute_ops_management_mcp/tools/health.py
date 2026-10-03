"""
MCP tools for HPE Compute Ops Management health monitoring.

This module contains MCP-facing tools for:

- Individual server health
- Overall server-environment health

All HTTP communication is delegated to HPEComputeOpsClient.

No MCP server registration is performed here. The register_tools()
function is intentionally kept available so server.py can register
all tool modules together later.
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
# Generic helpers
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
) -> list[dict[str, Any]]:
    """
    Extract a list of server objects from an HPE API response.

    HPE collection responses may contain the resources inside
    a collection property. This helper also supports a direct
    list response.

    The function intentionally avoids assuming one single
    response envelope.
    """

    if isinstance(response, list):
        return [
            item
            for item in response
            if isinstance(item, dict)
        ]

    if not isinstance(response, dict):
        return []

    # Common collection property names.
    for key in (
        "items",
        "members",
        "servers",
        "data",
        "results",
    ):
        value = response.get(key)

        if isinstance(value, list):
            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    # A single resource is not a collection.
    return []


def _get_field(
    resource: dict[str, Any],
    *names: str,
) -> Any:
    """
    Return the first available field from a resource.

    This allows the normalization layer to tolerate minor
    differences in API response naming without changing the
    MCP interface.
    """

    for name in names:

        if name in resource:
            return resource[name]

    return None


def _normalize_server_health(
    server: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize the health-related information available in
    an HPE server resource.

    We preserve the original server object under `raw` so that
    no information returned by HPE is lost.
    """

    server_id = _get_field(
        server,
        "id",
        "serverId",
    )

    hostname = _get_field(
        server,
        "hostname",
        "hostName",
        "name",
    )

    health = _get_field(
        server,
        "health",
        "healthStatus",
        "status",
    )

    connection_status = _get_field(
        server,
        "connectionStatus",
        "connectionState",
    )

    power_state = _get_field(
        server,
        "powerState",
        "power",
    )

    return {
        "server_id": server_id,
        "hostname": hostname,
        "health": health,
        "connection_status": connection_status,
        "power_state": power_state,
        "raw": server,
    }


def _health_distribution(
    servers: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Calculate a simple health-status distribution.
    """

    distribution: dict[str, int] = {}

    for server in servers:

        health = server.get("health")

        if health is None:
            health = "UNKNOWN"

        health_key = str(
            health
        ).upper()

        distribution[health_key] = (
            distribution.get(
                health_key,
                0,
            )
            + 1
        )

    return distribution


def _connection_distribution(
    servers: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Calculate a connection-status distribution.
    """

    distribution: dict[str, int] = {}

    for server in servers:

        status = server.get(
            "connection_status"
        )

        if status is None:
            status = "UNKNOWN"

        status_key = str(
            status
        ).upper()

        distribution[status_key] = (
            distribution.get(
                status_key,
                0,
            )
            + 1
        )

    return distribution


def _is_critical(
    value: Any,
) -> bool:
    """
    Determine whether a health/status value represents a
    critical state.

    This is intentionally conservative.
    """

    if value is None:
        return False

    return str(
        value
    ).upper() in {
        "CRITICAL",
        "CRIT",
        "FAILED",
        "FAILURE",
        "UNHEALTHY",
    }


# ------------------------------------------------------------------
# MCP Tool: get_server_health
# ------------------------------------------------------------------

def register_tools(mcp) -> None:
    """
    Register health-related MCP tools with a FastMCP instance.

    server.py will call this function when all tool modules are
    registered together.
    """

    @mcp.tool()
    async def get_server_health(
        server_id: str | None = None,
        include_details: bool = False,
    ) -> dict:
        """
        Get the health and operational status of HPE servers.

        If server_id is provided, return the health information
        for that server.

        If server_id is omitted, return a health summary for
        the managed server environment.

        Args:
            server_id:
                Optional HPE Compute Ops Management server
                identifier.

            include_details:
                Include the complete server response in the
                result.

        Returns:
            Server health, connection state, power state and
            relevant health information.
        """

        try:

            client = _get_client()

            # --------------------------------------------------
            # Individual server
            # --------------------------------------------------

            if server_id:

                server_id = server_id.strip()

                if not server_id:
                    return {
                        "success": False,
                        "error": (
                            "server_id cannot be empty."
                        ),
                    }

                endpoint = (
                    v1.SERVER_BY_ID.format(
                        server_id=server_id,
                    )
                )

                response = await client.get(
                    endpoint,
                )

                if not isinstance(
                    response,
                    dict,
                ):
                    return {
                        "success": False,
                        "error": (
                            "Unexpected response received "
                            "from the HPE server API."
                        ),
                    }

                health = _normalize_server_health(
                    response
                )

                result: dict[str, Any] = {
                    "success": True,
                    "server": health,
                }

                if not include_details:
                    health.pop(
                        "raw",
                        None,
                    )

                return result

            # --------------------------------------------------
            # Environment summary
            # --------------------------------------------------

            response = await client.get(
                v1.SERVERS,
                params={
                    "limit": 1000,
                    "offset": 0,
                },
            )

            servers = _extract_items(
                response
            )

            normalized_servers = [
                _normalize_server_health(
                    server
                )
                for server in servers
            ]

            result = {
                "success": True,
                "summary": {
                    "total_servers": len(
                        normalized_servers
                    ),
                    "health_distribution":
                        _health_distribution(
                            normalized_servers
                        ),
                    "connection_distribution":
                        _connection_distribution(
                            normalized_servers
                        ),
                },
            }

            if include_details:
                result["servers"] = (
                    normalized_servers
                )

            return result

        except HPEAPIError as exc:

            return _api_error_response(
                exc
            )

    # ------------------------------------------------------------------
    # MCP Tool: get_environment_health
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_environment_health() -> dict:
        """
        Get an operational health summary of the HPE server
        environment.

        Returns:

        - Total server count
        - Health distribution
        - Connection distribution
        - Critical servers

        Active alerts can be added to this summary when the
        alerts tool is integrated.
        """

        try:

            client = _get_client()

            # --------------------------------------------------
            # Get managed servers
            # --------------------------------------------------

            response = await client.get(
                v1.SERVERS,
                params={
                    "limit": 1000,
                    "offset": 0,
                },
            )

            servers = _extract_items(
                response
            )

            normalized_servers = [
                _normalize_server_health(
                    server
                )
                for server in servers
            ]

            # --------------------------------------------------
            # Calculate health distribution
            # --------------------------------------------------

            health_distribution = (
                _health_distribution(
                    normalized_servers
                )
            )

            # --------------------------------------------------
            # Calculate connection distribution
            # --------------------------------------------------

            connection_distribution = (
                _connection_distribution(
                    normalized_servers
                )
            )

            # --------------------------------------------------
            # Identify critical servers
            # --------------------------------------------------

            critical_servers: list[
                dict[str, Any]
            ] = []

            for server in normalized_servers:

                if _is_critical(
                    server.get("health")
                ):
                    critical_servers.append(
                        {
                            "server_id":
                                server.get(
                                    "server_id"
                                ),
                            "hostname":
                                server.get(
                                    "hostname"
                                ),
                            "health":
                                server.get(
                                    "health"
                                ),
                            "connection_status":
                                server.get(
                                    "connection_status"
                                ),
                            "power_state":
                                server.get(
                                    "power_state"
                                ),
                        }
                    )

            # --------------------------------------------------
            # Build result
            # --------------------------------------------------

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
                    "critical_server_count":
                        len(
                            critical_servers
                        ),
                    "critical_servers":
                        critical_servers,
                },
            }

        except HPEAPIError as exc:

            return _api_error_response(
                exc
            )