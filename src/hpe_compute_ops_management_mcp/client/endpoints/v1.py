"""
HPE Compute Ops Management v1 API endpoints.

This module contains endpoint paths for the stable v1 APIs
used by the MCP server.

The paths are based on the HPE Compute Ops Management
OpenAPI specification.

Important:
    The regional HPE GreenLake API hostname is configured
    separately in Settings. This module only defines the
    API paths.
"""

from __future__ import annotations


# =============================================================
# API prefix
# =============================================================

API_PREFIX = "/compute-ops-mgmt/v1"


# =============================================================
# Servers
# =============================================================

SERVERS = f"{API_PREFIX}/servers"

SERVER_BY_ID = f"{SERVERS}/{{server_id}}"

SERVER_ALERTS = f"{SERVER_BY_ID}/alerts"


# =============================================================
# Alerts
# =============================================================

ALERTS = f"{API_PREFIX}/alerts"


# =============================================================
# Groups
# =============================================================

GROUPS = f"{API_PREFIX}/groups"

GROUP_BY_ID = f"{GROUPS}/{{group_id}}"

GROUP_COMPLIANCE = (
    f"{GROUP_BY_ID}/compliance"
)

GROUP_COMPLIANCE_BY_ID = (
    f"{GROUP_COMPLIANCE}/{{compliance_id}}"
)

GROUP_DEVICES = (
    f"{GROUP_BY_ID}/devices"
)


# =============================================================
# Firmware Bundles
# =============================================================

FIRMWARE_BUNDLES = (
    f"{API_PREFIX}/firmware-bundles"
)

FIRMWARE_BUNDLE_BY_ID = (
    f"{FIRMWARE_BUNDLES}/{{bundle_id}}"
)

FIRMWARE_BUNDLE_DETAILS = (
    f"{FIRMWARE_BUNDLE_BY_ID}/bundle-details"
)


# =============================================================
# Appliance Firmware Bundles
# =============================================================

APPLIANCE_FIRMWARE_BUNDLES = (
    f"{API_PREFIX}/appliance-firmware-bundles"
)

APPLIANCE_FIRMWARE_BUNDLE_BY_ID = (
    f"{APPLIANCE_FIRMWARE_BUNDLES}/{{bundle_id}}"
)


# =============================================================
# Jobs
# =============================================================

JOBS = f"{API_PREFIX}/jobs"

JOB_BY_ID = f"{JOBS}/{{job_id}}"


# =============================================================
# Async Operations
# =============================================================

ASYNC_OPERATIONS = (
    f"{API_PREFIX}/async-operations"
)

ASYNC_OPERATION_BY_ID = (
    f"{ASYNC_OPERATIONS}/{{operation_id}}"
)

ASYNC_OPERATION_CANCEL = (
    f"{ASYNC_OPERATION_BY_ID}/cancel"
)


# =============================================================
# Metrics Configurations
# =============================================================

METRICS_CONFIGURATIONS = (
    f"{API_PREFIX}/metrics-configurations"
)

METRICS_CONFIGURATION_BY_ID = (
    f"{METRICS_CONFIGURATIONS}/{{configuration_id}}"
)


# =============================================================
# Settings
# =============================================================

SETTINGS = f"{API_PREFIX}/settings"

SETTING_BY_ID = (
    f"{SETTINGS}/{{setting_id}}"
)


# =============================================================
# User Preferences
# =============================================================

USER_PREFERENCES = (
    f"{API_PREFIX}/user-preferences"
)

USER_PREFERENCE_BY_ID = (
    f"{USER_PREFERENCES}/{{preference_id}}"
)

USER_PREFERENCES_SUBSCRIBE = (
    f"{USER_PREFERENCES}/subscribe"
)

USER_PREFERENCES_UNSUBSCRIBE = (
    f"{USER_PREFERENCES}/unsubscribe"
)


# =============================================================
# Endpoint groups
# =============================================================

SERVER_ENDPOINTS = {
    "list": SERVERS,
    "create": SERVERS,
    "update_collection": SERVERS,
    "get": SERVER_BY_ID,
    "update": SERVER_BY_ID,
    "delete": SERVER_BY_ID,
    "alerts": SERVER_ALERTS,
}


ALERT_ENDPOINTS = {
    "list": ALERTS,
}


GROUP_ENDPOINTS = {
    "list": GROUPS,
    "create": GROUPS,
    "get": GROUP_BY_ID,
    "update": GROUP_BY_ID,
    "delete": GROUP_BY_ID,
    "compliance": GROUP_COMPLIANCE,
    "compliance_by_id": GROUP_COMPLIANCE_BY_ID,
    "devices": GROUP_DEVICES,
}


FIRMWARE_ENDPOINTS = {
    "list": FIRMWARE_BUNDLES,
    "get": FIRMWARE_BUNDLE_BY_ID,
    "details": FIRMWARE_BUNDLE_DETAILS,
}


JOB_ENDPOINTS = {
    "list": JOBS,
    "create": JOBS,
    "get": JOB_BY_ID,
    "update": JOB_BY_ID,
}


METRICS_CONFIGURATION_ENDPOINTS = {
    "list": METRICS_CONFIGURATIONS,
    "create": METRICS_CONFIGURATIONS,
    "get": METRICS_CONFIGURATION_BY_ID,
    "update": METRICS_CONFIGURATION_BY_ID,
    "delete": METRICS_CONFIGURATION_BY_ID,
}