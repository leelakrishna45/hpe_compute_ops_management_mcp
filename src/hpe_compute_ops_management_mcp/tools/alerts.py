"""
MCP tools for HPE Compute Ops Management alerts.

This module contains MCP-facing tools for:

- Retrieving alerts across the managed environment
- Retrieving alerts for a specific server
- Filtering alerts by severity and category

All HTTP communication is delegated to HPEComputeOpsClient.

MCP registration is intentionally deferred to server.py.
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
# Validation helpers
# ------------------------------------------------------------------

def _validate_limit(limit: int) -> int:
    """
    Validate alert result limit.
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


def _clean_value(
    value: str | None,
) -> str | None:
    """
    Strip whitespace from an optional string.
    """

    if value is None:
        return None

    value = value.strip()

    return value or None


# ------------------------------------------------------------------
# Response helpers
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


def _extract_alerts(
    response: Any,
) -> list[dict[str, Any]]:
    """
    Extract alert objects from an HPE API response.

    The helper supports several common collection envelopes
    without modifying the raw API response.
    """

    if isinstance(response, list):
        return [
            item
            for item in response
            if isinstance(item, dict)
        ]

    if not isinstance(response, dict):
        return []

    for key in (
        "items",
        "members",
        "alerts",
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

    return []


def _normalize_alert(
    alert: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize commonly useful alert fields.

    The original API response is preserved under `raw`.
    """

    alert_id = (
        alert.get("id")
        or alert.get("alertId")
    )

    severity = (
        alert.get("severity")
        or alert.get("priority")
    )

    category = (
        alert.get("category")
        or alert.get("type")
        or alert.get("alertType")
    )

    message = (
        alert.get("message")
        or alert.get("description")
        or alert.get("summary")
    )

    server_id = (
        alert.get("serverId")
        or alert.get("resourceId")
    )

    server_name = (
        alert.get("serverName")
        or alert.get("hostname")
        or alert.get("hostName")
    )

    created_at = (
        alert.get("createdAt")
        or alert.get("created")
        or alert.get("timestamp")
    )

    state = (
        alert.get("state")
        or alert.get("status")
    )

    return {
        "alert_id": alert_id,
        "severity": severity,
        "category": category,
        "message": message,
        "server_id": server_id,
        "server_name": server_name,
        "created_at": created_at,
        "state": state,
        "raw": alert,
    }


# ------------------------------------------------------------------
# MCP tool registration
# ------------------------------------------------------------------

def register_tools(mcp) -> None:
    """
    Register alert-related MCP tools with a FastMCP instance.

    server.py will call this function when all tool modules are
    registered together.
    """

    # ==============================================================
    # get_alerts
    # ==============================================================

    @mcp.tool()
    async def get_alerts(
        severity: str | None = None,
        category: str | None = None,
        server_id: str | None = None,
        limit: int = 50,
    ) -> dict:
        """
        Get alerts from HPE Compute Ops Management.

        Use this tool to identify current or recent server
        problems.

        Args:
            severity:
                Optional severity filter, such as CRITICAL
                or WARNING.

            category:
                Optional alert category.

            server_id:
                Optional server identifier.

            limit:
                Maximum number of alerts.

        Returns:
            Alerts matching the requested criteria.
        """

        try:
            limit = _validate_limit(limit)

            severity = _clean_value(
                severity
            )

            category = _clean_value(
                category
            )

            server_id = _clean_value(
                server_id
            )

            params: dict[str, Any] = {
                "limit": limit,
            }

            # ------------------------------------------------------
            # Optional filters
            #
            # These are kept separate so the MCP interface remains
            # stable even if the HPE API parameter handling changes.
            # ------------------------------------------------------

            if severity:
                params["severity"] = severity

            if category:
                params["category"] = category

            if server_id:
                params["serverId"] = server_id

            client = _get_client()

            response = await client.get(
                v1.ALERTS,
                params=params,
            )

            alerts = _extract_alerts(
                response
            )

            normalized_alerts = [
                _normalize_alert(alert)
                for alert in alerts
            ]

            return {
                "success": True,
                "count": len(
                    normalized_alerts
                ),
                "filters": {
                    "severity": severity,
                    "category": category,
                    "server_id": server_id,
                },
                "alerts": normalized_alerts,
            }

        except HPEAPIError as exc:

            return _api_error_response(
                exc
            )

        except ValueError as exc:

            return {
                "success": False,
                "error": str(exc),
            }

    # ==============================================================
    # get_server_alerts
    # ==============================================================

    @mcp.tool()
    async def get_server_alerts(
        server_id: str,
        severity: str | None = None,
        limit: int = 50,
    ) -> dict:
        """
        Get alerts associated with a specific HPE server.

        Args:
            server_id:
                HPE Compute Ops Management server identifier.

            severity:
                Optional severity filter.

            limit:
                Maximum number of alerts.

        Returns:
            Alerts associated with the server.
        """

        if not server_id or not server_id.strip():
            return {
                "success": False,
                "error": (
                    "server_id is required."
                ),
            }

        try:
            limit = _validate_limit(limit)

            server_id = server_id.strip()

            severity = _clean_value(
                severity
            )

            # ------------------------------------------------------
            # Server-specific alert endpoint
            # ------------------------------------------------------

            endpoint = (
                v1.SERVER_ALERTS.format(
                    server_id=server_id,
                )
            )

            params: dict[str, Any] = {
                "limit": limit,
            }

            if severity:
                params["severity"] = severity

            client = _get_client()

            response = await client.get(
                endpoint,
                params=params,
            )

            alerts = _extract_alerts(
                response
            )

            normalized_alerts = [
                _normalize_alert(alert)
                for alert in alerts
            ]

            return {
                "success": True,
                "server_id": server_id,
                "count": len(
                    normalized_alerts
                ),
                "filters": {
                    "severity": severity,
                },
                "alerts": normalized_alerts,
            }

        except HPEAPIError as exc:

            return _api_error_response(
                exc
            )

        except ValueError as exc:

            return {
                "success": False,
                "error": str(exc),
            }