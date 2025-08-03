# NoteLLM_MCP_Server

[中文](docs/README_CN.md)

NoteLLM_MCP_Server is an open-source software designed to provide MCP services via API for the Joplin plugin [NoteLLM](https://github.com/HorseSword/joplin-plugin-notellm).  
It can also serve as a general-purpose MCP service provider through API, or offer standard MCP access via stdio, SSE, or streamableHTTP.

## Features

- **Compatible with Various MCP Tool Integrations**: Supports adding MCP tools through standard JSON files, making tool integration straightforward and intuitive.
- **API-Based MCP Service Mode**: Built on the FastAPI framework, it provides API endpoints for invoking MCP services, enabling efficient and convenient integration and usage.
- **Multiple MCP Service Modes**: By configuring the `mode` parameter, you can enable different running modes, including `stdio`, `sse`, and `streamableHTTP`. These modes can be combined to support various MCP tool integrations and provide a unified MCP service endpoint, making it possible to integrate with tools like CherryStudio as an MCP provider.

## Tech Stack

NoteLLM_MCP_Server is primarily built with the following technologies:

- **FastMCP**: Handles the core logic of the MCP protocol.
- **FastAPI**: Builds a high-performance API server, offering RESTful APIs for MCP service invocation.

## Use Cases

NoteLLM_MCP_Server can be used in various scenarios where MCP service integration and provision are required, such as:

- Providing MCP functionality for the Joplin plugin [NoteLLM](https://github.com/HorseSword/joplin-plugin-notellm).
- Acting as an MCP provider for tools like CherryStudio.
- Deploying locally or in the cloud to offer a unified MCP service interface.
- Remotely invoking and managing MCP services via API endpoints.

## Installation & Usage

After cloning the source code, start the server with:
```
uv run mcp_server.py --mode api
```

## Changelog

Version | Date | Detail
--|--|--
v0.1.0 | 2025-08-03 | Initial implementation of basic features