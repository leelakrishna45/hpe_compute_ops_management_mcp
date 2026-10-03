"""
HPE Compute Ops Management v1beta1 API endpoints.

This module contains endpoint paths for the v1beta1 APIs
used by the HPE Compute Ops Management MCP server.

The regional HPE GreenLake API hostname is configured
separately in Settings.

This module only defines API paths. HTTP communication,
authentication, retries, and error handling are implemented
by client.py.
"""

from __future__ import annotations


# =============================================================
# API prefix
# =============================================================

API_PREFIX = "/compute-ops-mgmt/v1beta1"


# =============================================================
# Utilization
# =============================================================

UTILIZATION_OVER_TIME = (
    f"{API_PREFIX}/utilization-over-time"
)

UTILIZATION_AVERAGES = (
    f"{API_PREFIX}/utilization-averages"
)

UTILIZATION_BY_ENTITY = (
    f"{API_PREFIX}/utilization-by-entity"
)


# =============================================================
# Endpoint groups
# =============================================================

UTILIZATION_ENDPOINTS = {
    "over_time": UTILIZATION_OVER_TIME,
    "averages": UTILIZATION_AVERAGES,
    "by_entity": UTILIZATION_BY_ENTITY,
}


# =============================================================
# All v1beta1 endpoints used by this MCP
# =============================================================

ENDPOINTS = {
    "utilization": UTILIZATION_ENDPOINTS,
}


__all__ = [
    "API_PREFIX",
    "UTILIZATION_OVER_TIME",
    "UTILIZATION_AVERAGES",
    "UTILIZATION_BY_ENTITY",
    "UTILIZATION_ENDPOINTS",
    "ENDPOINTS",
]