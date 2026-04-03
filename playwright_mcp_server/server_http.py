"""
Playwright MCP Server - HTTP 传输模式入口

通过 HTTP 运行 MCP 服务器
适用于远程调用和 Web 服务集成

默认地址: http://localhost:8000/mcp
"""

from mcp_server import mcp

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, path="/mcp")
