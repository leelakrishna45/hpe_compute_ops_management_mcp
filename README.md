# HPE Compute Ops Management MCP Server

An MCP (Model Context Protocol) server for interacting with HPE Compute Ops Management through REST APIs.

This MCP server exposes HPE server management and monitoring capabilities as tools that can be used by an AI assistant.

The goal is to make common HPE server administration and monitoring tasks accessible through natural-language questions instead of requiring an administrator to manually navigate the HPE Compute Ops Management console.

---

## Overview

The HPE Compute Ops Management MCP provides access to information such as:

- Managed HPE servers
- Server health
- Server connection status
- Server power state
- Server inventory
- Server alerts
- Critical alerts
- Server utilization
- Historical utilization
- Average utilization
- Environment-wide health
- Critical servers

The architecture is designed around the HPE Compute Ops Management REST APIs.

```text
AI Assistant
     │
     │ MCP
     ▼
HPE Compute Ops Management MCP
     │
     │ REST API
     ▼
HPE GreenLake
     │
     ▼
Compute Ops Management
     │
     ▼
HPE Servers