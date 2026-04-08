---
name: dynamics-ax-xpo-roundtrip
description: Пайплайн XPO ↔ XPP в репозитории DynamicsAX (парсер, writer, кодировки, флаги CI).
---

# Dynamics AX XPO roundtrip

## Источник правды

- Редактируемый X++ только в `parserXPO/**/*.xpp` (и при необходимости `properties.txt` в каталоге объекта).
- Не выгружать и не вставлять «весь AOT» из огромного CUS-экспорта без индекса или MCP.

## Скрипты

- Разбор XPO → дерево: `xpo_parser.py` → `parserXPO/<Object>/<Method>.xpp`, UTF-8.
- Сборка обратно: `xpo_writer.py` → рядом с исходным XPO файл `<stem>_WR.xpo`.
- Точечное извлечение по SQLite: `parse_object_from_index(...)` в `xpo_parser.py`, БД `indexXPO_cus/xpo_index.db`, таблица `elements`.

## Флаги

- `--force` (parser): перезапись существующих `.xpp`. (writer): игнорировать сравнение по mtime/равенству текста.
- `--no-input` или `CI=1` / `XPO_NO_INPUT=1`: без диалогов; при нескольких `.xpo` в каталоге `XPO` без явного пути — обработать все; writer не спрашивает про добавление элемента по шаблону.

## Кодировки

- Импорт в AOT: XPO в **Windows-1251 (cp1251)**; `xpo_writer` сохраняет в кодировке исходного файла.
- `parserXPO`: UTF-8.

## После правок

После изменения `.xpp` предложи запуск `xpo_writer.py` и укажи ожидаемый путь `*_WR.xpo`.
