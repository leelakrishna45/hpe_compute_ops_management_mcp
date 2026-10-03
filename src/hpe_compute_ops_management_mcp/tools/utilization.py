"""
MCP tools for HPE Compute Ops Management utilization data.

This module contains MCP-facing tools for:

- Utilization measurements over time
- Average utilization
- Entity-based utilization

The tools delegate HTTP communication to HPEComputeOpsClient.

MCP server registration is intentionally deferred until all
tool modules have been created.
"""

from __future__ import annotations

from typing import Any

from ..client.client import HPEComputeOpsClient
from ..client.endpoints import v1beta1
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

def _validate_server_id(
    server_id: str,
) -> str:
    """
    Validate and normalize a server identifier.
    """

    if not server_id or not server_id.strip():
        raise ValueError(
            "server_id is required."
        )

    return server_id.strip()


def _validate_time_range(
    start_time: str | None,
    end_time: str | None,
) -> tuple[str | None, str | None]:
    """
    Validate an optional time range.

    We intentionally do not parse the timestamp here because
    HPE may accept more than one valid timestamp representation.
    The API remains responsible for validating the exact format.
    """

    if start_time is not None:
        start_time = start_time.strip()

        if not start_time:
            start_time = None

    if end_time is not None:
        end_time = end_time.strip()

        if not end_time:
            end_time = None

    if (
        start_time is not None
        and end_time is not None
        and start_time > end_time
    ):
        raise ValueError(
            "start_time must be earlier than end_time."
        )

    return start_time, end_time


def _clean_metric(
    metric: str | None,
) -> str | None:
    """
    Normalize an optional utilization metric.
    """

    if metric is None:
        return None

    metric = metric.strip()

    return metric or None


def _clean_entity_type(
    entity_type: str,
) -> str:
    """
    Validate and normalize an entity type.
    """

    if not entity_type or not entity_type.strip():
        raise ValueError(
            "entity_type is required."
        )

    return entity_type.strip()


def _clean_entity_id(
    entity_id: str | None,
) -> str | None:
    """
    Normalize an optional entity identifier.
    """

    if entity_id is None:
        return None

    entity_id = entity_id.strip()

    return entity_id or None


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


def _extract_data(
    response: Any,
) -> Any:
    """
    Extract useful utilization data from a common HPE API
    response envelope.

    The original response is returned when no known envelope
    is detected.
    """

    if not isinstance(response, dict):
        return response

    for key in (
        "data",
        "items",
        "members",
        "results",
        "measurements",
        "utilization",
    ):
        if key in response:
            return response[key]

    return response


# ------------------------------------------------------------------
# MCP tool registration
# ------------------------------------------------------------------

def register_tools(mcp) -> None:
    """
    Register utilization-related MCP tools with a FastMCP
    instance.

    server.py will call this function after all tool modules
    have been created.
    """

    # ==============================================================
    # get_utilization_over_time
    # ==============================================================

    @mcp.tool()
    async def get_utilization_over_time(
        server_id: str,
        start_time: str,
        end_time: str,
        metric: str | None = None,
    ) -> dict:
        """
        Get server utilization measurements over a time period.

        This tool is useful for investigating how server resource
        utilization changed over time.

        Args:
            server_id:
                HPE Compute Ops Management server identifier.

            start_time:
                Beginning of the measurement interval.

            end_time:
                End of the measurement interval.

            metric:
                Optional utilization metric.

        Returns:
            Utilization measurements for the requested period.
        """

        try:
            server_id = _validate_server_id(
                server_id
            )

            start_time, end_time = (
                _validate_time_range(
                    start_time,
                    end_time,
                )
            )

            if start_time is None:
                raise ValueError(
                    "start_time is required."
                )

            if end_time is None:
                raise ValueError(
                    "end_time is required."
                )

            metric = _clean_metric(
                metric
            )

            # ------------------------------------------------------
            # Build API parameters
            #
            # The endpoint and parameter names are kept isolated
            # here so they can be aligned directly with the HPE
            # OpenAPI specification.
            # ------------------------------------------------------

            params: dict[str, Any] = {
                "server_id": server_id,
                "start_time": start_time,
                "end_time": end_time,
            }

            if metric is not None:
                params["metric"] = metric

            client = _get_client()

            response = await client.get(
                v1beta1.UTILIZATION_OVER_TIME,
                params=params,
            )

            return {
                "success": True,
                "server_id": server_id,
                "start_time": start_time,
                "end_time": end_time,
                "metric": metric,
                "data": _extract_data(
                    response
                ),
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
    # get_utilization_averages
    # ==============================================================

    @mcp.tool()
    async def get_utilization_averages(
        server_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        metric: str | None = None,
    ) -> dict:
        """
        Get average server utilization for a specified period.

        If server_id is omitted, the API may return aggregate
        utilization information for the managed environment,
        depending on the capabilities of the HPE API.

        Args:
            server_id:
                Optional HPE Compute Ops Management server
                identifier.

            start_time:
                Beginning of the measurement period.

            end_time:
                End of the measurement period.

            metric:
                Optional utilization metric.

        Returns:
            Average utilization information.
        """

        try:
            if server_id is not None:
                server_id = server_id.strip()

                if not server_id:
                    server_id = None

            start_time, end_time = (
                _validate_time_range(
                    start_time,
                    end_time,
                )
            )

            metric = _clean_metric(
                metric
            )

            params: dict[str, Any] = {}

            if server_id is not None:
                params["server_id"] = server_id

            if start_time is not None:
                params["start_time"] = start_time

            if end_time is not None:
                params["end_time"] = end_time

            if metric is not None:
                params["metric"] = metric

            client = _get_client()

            response = await client.get(
                v1beta1.UTILIZATION_AVERAGES,
                params=params,
            )

            return {
                "success": True,
                "server_id": server_id,
                "start_time": start_time,
                "end_time": end_time,
                "metric": metric,
                "data": _extract_data(
                    response
                ),
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
    # get_utilization_by_entity
    # ==============================================================

    @mcp.tool()
    async def get_utilization_by_entity(
        entity_type: str,
        entity_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """
        Get utilization information associated with an HPE
        Compute Ops Management entity.

        Args:
            entity_type:
                Type of entity being queried.

            entity_id:
                Optional entity identifier.

            start_time:
                Optional beginning of the measurement period.

            end_time:
                Optional end of the measurement period.

        Returns:
            Utilization information for the requested entity.
        """

        try:
            entity_type = _clean_entity_type(
                entity_type
            )

            entity_id = _clean_entity_id(
                entity_id
            )

            start_time, end_time = (
                _validate_time_range(
                    start_time,
                    end_time,
                )
            )

            params: dict[str, Any] = {
                "entity_type": entity_type,
            }

            if entity_id is not None:
                params["entity_id"] = entity_id

            if start_time is not None:
                params["start_time"] = start_time

            if end_time is not None:
                params["end_time"] = end_time

            client = _get_client()

            response = await client.get(
                v1beta1.UTILIZATION_BY_ENTITY,
                params=params,
            )

            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "start_time": start_time,
                "end_time": end_time,
                "data": _extract_data(
                    response
                ),
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