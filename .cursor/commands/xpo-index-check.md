# XPO: health-check индекса CUS (SQLite)

Проверка целостности и актуальности `indexXPO_cus/xpo_index.db` перед поиском AOT.

**Рабочая директория:** корень репозитория `DynamicsAX`.

```text
python indexXPO_cus/check_xpo_index_health.py
```

Что проверяется:
- существует ли `AOT_cus/PrivateProject_CUS_Layer_Export.xpo`
- существует ли `indexXPO_cus/xpo_index.db`
- не старее ли БД, чем XPO
- доступна ли SQLite (без lock)
- есть ли таблицы `elements` и `methods`
- есть ли элементы ключевых типов: `CLS`, `DBT`, `FRM`

Если check возвращает `FAIL`:
1. Закрой фоновые процессы, которые держат SQLite (`python`, MCP).
2. Выполни переиндексацию: `/xpo-index-cus`.
3. Повтори `/xpo-index-check`.

