# Настройка виртуального окружения

## Активация venv

### Windows (PowerShell)
```powershell
.\venv\Scripts\Activate.ps1
```

### Windows (CMD)
```cmd
venv\Scripts\activate.bat
```

## Установка зависимостей

После активации venv:

```bash
pip install -r requirements.txt
```

Или для MCP сервера отдельно:

```bash
pip install -r mcp_server/requirements.txt
```

## Использование

После активации venv все команды Python будут использовать окружение из `venv/`.

### Запуск MCP сервера вручную

```bash
# Активируйте venv
.\venv\Scripts\Activate.ps1

# Запустите сервер
cd mcp_server
python -u server.py
```

### Запуск тестов

```bash
# Активируйте venv
.\venv\Scripts\Activate.ps1

# Запустите тесты
cd mcp_server
python test_modules.py
```

## Деактивация

```bash
deactivate
```

## Примечания

- MCP сервер в Cursor автоматически использует Python из venv (настроено в `.cursor/mcp.json`)
- Все зависимости изолированы в `venv/`
- Не коммитьте папку `venv/` в Git (уже добавлена в `.gitignore`)





