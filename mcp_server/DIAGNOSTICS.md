# Диагностика проблем MCP сервера

## Сервер "висит" и ничего не происходит

Это **нормальное поведение** для MCP сервера, работающего через stdio протокол. Сервер ждет команды через stdin и не выводит ничего в консоль.

## Если Cursor показывает ошибку

1. **Откройте панель Output в Cursor:**
   - Нажмите `Ctrl+Shift+U` или `View > Output`
   - В выпадающем списке выберите "MCP" или "dynamics-ax-mcp"
   - Скопируйте текст ошибки

2. **Проверьте логи запуска:**
   - В панели Output должны быть сообщения:
     - "Dynamics AX MCP Server starting..."
     - "Dynamics AX MCP Server ready"
   - Если их нет, значит сервер не запускается

3. **Проверьте конфигурацию:**
   - Файл `.cursor/mcp.json` должен существовать
   - Путь `cwd` должен указывать на папку `mcp_server`
   - Команда `python` должна быть доступна в PATH

4. **Проверьте зависимости:**
   ```bash
   cd mcp_server
   pip install -r requirements.txt
   ```

5. **Проверьте запуск вручную:**
   ```bash
   cd C:\Python\Projects\DynamicsAX\mcp_server
   python -u server.py
   ```
   - Сервер должен запуститься без ошибок
   - Он будет "висеть" - это нормально
   - Нажмите `Ctrl+C` для остановки

## Частые проблемы

### Проблема: "ModuleNotFoundError"
**Решение:** Убедитесь, что все зависимости установлены:
```bash
pip install -r mcp_server/requirements.txt
```

### Проблема: "FileNotFoundError"
**Решение:** Проверьте, что файлы существуют:
- `AOT_cus/AxMIKru.ald`
- `AOT_cus/PrivateProject_CUS_Layer_Export.xpo`
- `indexXPO_cus/xpo_index.db`

### Проблема: Переменная `${workspaceFolder}` не работает
**Решение:** Используйте абсолютные пути в `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "dynamics-ax-mcp": {
      "command": "C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": ["-u", "server.py"],
      "cwd": "C:\\Python\\Projects\\DynamicsAX\\mcp_server",
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Проблема: Сервер запускается, но инструменты не работают
**Решение:** Проверьте логи в панели Output - там должны быть детали ошибок при вызове инструментов.







