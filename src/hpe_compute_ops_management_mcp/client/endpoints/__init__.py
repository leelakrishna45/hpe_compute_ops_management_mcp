"""
HPE Compute Ops Management API endpoint definitions.

Endpoint paths are kept separate from the HTTP client so that
API version changes can be managed independently from the MCP
tools and HTTP transport layer.

Current API versions used by this project:

- v1
- v1beta1
"""

from . import v1
from . import v1beta1


__all__ = [
    "v1",
    "v1beta1",
]