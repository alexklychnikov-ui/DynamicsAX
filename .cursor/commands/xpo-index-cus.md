# XPO: переиндексировать CUS-экспорт (SQLite)

После того как обновлён файл **`AOT_cus/PrivateProject_CUS_Layer_Export.xpo`** (например экспортом из AX через `ExportCUSLayerBatch` или копированием с диска), пересобери индекс для MCP/точечного парсинга.

**Рабочая директория:** корень репозитория `DynamicsAX`.

```text
python indexXPO_cus/xpo_indexer_sqlite.py
```

По умолчанию скрипт берёт `../AOT_cus/PrivateProject_CUS_Layer_Export.xpo` относительно `indexXPO_cus/` — это и есть `AOT_cus/PrivateProject_CUS_Layer_Export.xpo` в корне проекта.

Явный путь (если нужен другой файл):

```text
python indexXPO_cus/xpo_indexer_sqlite.py ../AOT_cus/PrivateProject_CUS_Layer_Export.xpo
```

Второй аргумент — имя файла БД внутри `indexXPO_cus/` (по умолчанию `xpo_index.db`).

- **Результат:** `indexXPO_cus/xpo_index.db` пересоздаётся (старая БД удаляется).
- **Неинтерактивно:** дополнительных флагов не требуется.
- Связка с кодом: после выгрузки XPO скопируй/синхронизируй файл в `AOT_cus/`, затем выполни команду выше.

Кратко сообщи: путь к XPO, число элементов из статистики скрипта, размер `xpo_index.db`.
