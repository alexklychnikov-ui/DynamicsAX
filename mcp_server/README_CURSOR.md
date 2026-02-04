# Настройка MCP сервера в Cursor

## Конфигурация

Файл конфигурации находится в `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dynamics-ax-mcp": {
      "command": "python",
      "args": [
        "-u",
        "server.py"
      ],
      "cwd": "${workspaceFolder}/mcp_server",
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Проверка работы

1. Убедитесь, что Python доступен в PATH
2. Убедитесь, что все зависимости установлены: `pip install -r mcp_server/requirements.txt`
3. Перезагрузите Cursor
4. Откройте настройки Tools & MCP
5. Сервер должен появиться в списке "Installed MCP Servers"

## Диагностика проблем

Если сервер не запускается:

1. Проверьте логи в Cursor:
   - Откройте панель "Output" (Ctrl+Shift+U)
   - Выберите канал "MCP" или "dynamics-ax-mcp"
   - Проверьте сообщения об ошибках

2. Проверьте запуск сервера вручную:
   ```bash
   cd mcp_server
   python server.py
   ```
   Сервер должен запуститься и ждать ввода (не должно быть ошибок)

3. Проверьте конфигурацию:
   - Убедитесь, что файл `.cursor/mcp.json` существует
   - Проверьте, что пути указаны правильно
   - Убедитесь, что `cwd` указывает на папку `mcp_server`

4. Если используется абсолютный путь к Python:
   - Замените `"command": "python"` на полный путь, например:
     `"command": "C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python313\\python.exe"`

## Альтернативная конфигурация с абсолютными путями

Если переменная `${workspaceFolder}` не работает, используйте абсолютные пути:

```json
{
  "mcpServers": {
    "dynamics-ax-mcp": {
      "command": "C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": [
        "-u",
        "server.py"
      ],
      "cwd": "C:\\Python\\Projects\\DynamicsAX\\mcp_server",
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```
















