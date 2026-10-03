"""
HPE Compute Ops Management MCP Server.

This module creates the FastMCP server and registers all HPE
Compute Ops Management tools.

Tool implementations live under:

    hpe_compute_ops_mcp.tools

The server module is intentionally kept thin. It is responsible
primarily for:

    1. Creating the MCP server.
    2. Registering tool modules.
    3. Starting the MCP server when executed directly.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .tools import alerts
from .tools import environment
from .tools import health
from .tools import servers
from .tools import utilization


# ------------------------------------------------------------------
# MCP server
# ------------------------------------------------------------------

mcp = FastMCP(
    "HPE Compute Ops Management"
)


# ------------------------------------------------------------------
# Register MCP tools
# ------------------------------------------------------------------

servers.register_tools(mcp)
health.register_tools(mcp)
alerts.register_tools(mcp)
utilization.register_tools(mcp)
environment.register_tools(mcp)


# ------------------------------------------------------------------
# Application entry point
# ------------------------------------------------------------------

def main() -> None:
    """
    Start the HPE Compute Ops Management MCP server.

    The MCP server uses stdio transport by default, which makes
    it suitable for MCP clients such as Claude Desktop, Cursor,
    VS Code integrations, and other MCP-compatible clients.
    """

    mcp.run()


if __name__ == "__main__":
    main()