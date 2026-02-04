#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест MCP протокола - проверка инициализации
"""
import json
import sys
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("test-dynamics-ax")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="test",
            description="Тест",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    return [TextContent(type="text", text="OK")]

async def main():
    print("Starting MCP server...", file=sys.stderr)
    try:
        async with stdio_server() as streams:
            print("Server started, waiting for requests...", file=sys.stderr)
            await server.run(streams[0], streams[1], server.create_initialization_options())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
















