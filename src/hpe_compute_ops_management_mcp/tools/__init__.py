"""
MCP tools for HPE Compute Ops Management.

All functions exposed to the MCP client using @mcp.tool()
belong in this package.

Tool modules:

    servers.py
        Server discovery and server inventory tools.

    health.py
        Server and environment health monitoring tools.

    alerts.py
        HPE Compute Ops Management alert tools.

    utilization.py
        Server utilization and performance tools.

    environment.py
        Overall HPE server environment monitoring tools.

The tools use the client package for communication with
the HPE Compute Ops Management REST APIs.
"""