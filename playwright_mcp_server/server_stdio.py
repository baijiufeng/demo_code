"""
Playwright MCP Server - STDIO 传输模式入口

通过标准输入/输出运行 MCP 服务器
适用于命令行工具和本地集成
"""

from mcp_server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
