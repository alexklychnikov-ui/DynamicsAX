#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест для проверки работы stdio сервера
"""
import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("test-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="test_tool",
            description="Тестовый инструмент",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    return [TextContent(
        type="text",
        text=f"Тест работает: {arguments.get('message', 'OK')}"
    )]

async def main():
    print("Запуск тестового сервера...", file=sys.stderr)
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
















