#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Минимальный MCP сервер для тестирования
"""
import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("dynamics-ax-mcp")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="test",
            description="Тестовый инструмент",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    return [TextContent(type="text", text="OK")]

async def main():
    print("Starting server...", file=sys.stderr)
    try:
        async with stdio_server() as streams:
            print("Server ready", file=sys.stderr)
            await server.run(streams[0], streams[1], server.create_initialization_options())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())















