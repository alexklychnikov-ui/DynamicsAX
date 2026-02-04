# MCP сервер для Dynamics AX 2012

MCP сервер для работы с индексированным XPO файлом (CUS слой) Microsoft Dynamics AX 2012, метками из ALD файла и интеграцией результатов в папку parserXPO.

## Установка

```bash
cd mcp_server
pip install -r requirements.txt
```

Или из корня проекта:

```bash
pip install -r mcp_server/requirements.txt
```

## Использование

Запуск MCP сервера:

```bash
cd mcp_server
python server.py
```

Или из корня проекта:

```bash
python mcp_server/server.py
```

Сервер работает через stdio протокол и может быть подключен к MCP клиенту.

## Доступные инструменты

### 1. get_element_code
Получает код элемента (класс/таблица/форма) из XPO файла и сохраняет в parserXPO.

**Параметры:**
- `element_name` (обязательный) - имя элемента
- `element_type` (опционально) - тип элемента (CLS/TAB/FRM)

### 2. get_method_code
Получает код конкретного метода элемента и сохраняет/обновляет в parserXPO.

**Параметры:**
- `element_name` (обязательный) - имя элемента
- `method_name` (обязательный) - имя метода
- `element_type` (опционально) - тип элемента (CLS/TAB/FRM)

### 3. search_labels_in_code
Ищет метки @MIK в коде элемента/метода и расшифровывает их из ALD.

**Параметры:**
- `element_name` (обязательный) - имя элемента
- `method_name` (опционально) - имя метода

### 4. replace_labels_in_parser
Заменяет метки @MIK на их расшифровки в файлах parserXPO.

**Параметры:**
- `element_name` (обязательный) - имя элемента
- `method_name` (опционально) - имя метода (если не указано - обрабатываются все методы)
- `replace_mode` (опционально) - режим замены: "comments" (добавляет комментарии) или "inline" (заменяет inline), по умолчанию "comments"

### 5. fulltext_search
Полнотекстовый поиск по коду в XPO файле.

**Параметры:**
- `query` (обязательный) - текст для поиска
- `element_type` (опционально) - тип элемента для фильтрации (CLS/TAB/FRM)

### 6. find_label_usage
Ищет все места использования конкретной метки в коде.

**Параметры:**
- `label_id` (обязательный) - ID метки (например, "MIK4140" или "4140")

### 7. integrate_search_results
Интегрирует результаты поиска в parserXPO (создает/обновляет файлы).

**Параметры:**
- `search_results` (обязательный) - массив результатов поиска с полями element_name и element_type

## Структура файлов

- `server.py` - основной MCP сервер
- `label_loader.py` - загрузка меток из ALD файла
- `xpo_reader.py` - чтение XPO файла с использованием SQLite индекса
- `parser_integration.py` - интеграция кода в структуру parserXPO
- `test_modules.py` - тестовый скрипт для проверки модулей
- `work_log.md` - версионный лог работы

## Зависимости

- `mcp` - библиотека для MCP протокола
- `sqlite3` - встроенная библиотека Python для работы с SQLite

## Пути к файлам

Сервер использует следующие пути (относительно корня проекта):
- XPO файл: `AOT_cus/PrivateProject_CUS_Layer_Export.xpo`
- ALD файл: `AOT_cus/AxMIKru.ald`
- SQLite индекс: `indexXPO_cus/xpo_index.db`
- Выходная папка: `parserXPO/`

## Тестирование

Для проверки работы модулей:

```bash
cd mcp_server
python test_modules.py
```

Или из корня проекта:

```bash
python mcp_server/test_modules.py
```

## Примечания

- Сервер использует SQLite базу данных для быстрого поиска элементов
- XPO файл используется для получения актуального кода
- ALD файл используется для расшифровки меток
- Код сохраняется в структуру `parserXPO/<element_name>/<method_name>.xpp`

