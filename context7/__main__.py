import os
import asyncio

# Устанавливаем имя MCP-сервера до импорта, чтобы server.py подхватил его
os.environ.setdefault("MCP_SERVER_NAME", "context7")

from mcp_server import server as ax_server


def main():
    asyncio.run(ax_server.main())


if __name__ == "__main__":
    main()

