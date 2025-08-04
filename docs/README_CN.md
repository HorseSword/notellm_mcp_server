# NoteLLM_MCP_Server

NoteLLM_MCP_Server 是一个开源软件，
主要用于以 API 的形式，为 Joplin 插件 [NoteLLM](https://github.com/HorseSword/joplin-plugin-notellm) 提供MCP服务;
此外也可以提供通用 API 模式的 MCP 服务； 
或通过 stdio、sse 或 streamableHTTP 的形式提供标准 MCP 接入服务。

![image-20250804125837846](./_img/image-20250804125837846.png)

## 特点

- **兼容各类MCP工具接入**：支持通过标准的JSON文件添加MCP工具，使得工具的集成变得简单直观。
- **提供API调用MCP的服务模式**：基于FastAPI框架，提供API接口以调用MCP服务，使得服务的集成和调用更加高效和便捷。
- **提供多种MCP对外服务模式**：通过设置参数`mode`，可以启用不同的运行模式，包括`stdio`、`sse`和`streamableHTTP`模式。这些模式的组合允许实现多种MCP工具接入，并提供统一的MCP服务出口，支持作为MCP提供方接入如CherryStudio等工具。


## 技术栈

NoteLLM_MCP_Server 是主要基于以下技术构建的：

- **FastMCP**：用于处理MCP协议的核心逻辑。
- **FastAPI**：用于构建高性能的API服务器，提供 RESTful API 以调用MCP服务。

## 使用场景

NoteLLM_MCP_Server 可以应用于需要集成和提供MCP服务的各种场景，例如：

- 为 Joplin笔记的插件 [NoteLLM](https://github.com/HorseSword/joplin-plugin-notellm) 提供 MCP 功能。
- 作为MCP提供方接入到CherryStudio等工具。
- 在本地或云环境中部署，提供统一的MCP服务接口。
- 通过API接口，实现对MCP服务的远程调用和管理。

## 安装与使用

克隆源代码之后，启动指令：
```
uv run mcp_server.py --mode api
```

## 升级记录

Version | Date | Detail
--|--|--
v0.1.0 | 2025-08-03 | 实现基础功能
