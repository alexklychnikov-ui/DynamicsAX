#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP сервер для работы с Dynamics AX XPO файлами и метками
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from label_loader import LabelLoader
from xpo_reader import XPOReader
from parser_integration import ParserIntegration


# Пути к файлам (относительно корня проекта)
# Определяем корень проекта: если запускаем из mcp_server, то parent, иначе parent.parent
_current_dir = Path(__file__).parent
if _current_dir.name == "mcp_server":
    PROJECT_ROOT = _current_dir.parent
else:
    PROJECT_ROOT = _current_dir
XPO_FILE = PROJECT_ROOT / "AOT_cus" / "PrivateProject_CUS_Layer_Export.xpo"
ALD_FILE = PROJECT_ROOT / "AOT_cus" / "AxMIKru.ald"
DB_FILE = PROJECT_ROOT / "indexXPO_cus" / "xpo_index.db"
PARSER_DIR = PROJECT_ROOT / "parserXPO"


# Имя MCP сервера можно переопределить через переменную окружения
SERVER_NAME = os.getenv("MCP_SERVER_NAME", "dynamics-ax-mcp")

# Инициализация компонентов
label_loader = None
xpo_reader = None
parser_integration = None


def initialize_components():
    """Инициализирует все компоненты сервера"""
    global label_loader, xpo_reader, parser_integration
    
    # Проверяем существование файлов
    if not ALD_FILE.exists():
        raise FileNotFoundError(f"ALD файл не найден: {ALD_FILE}")
    if not XPO_FILE.exists():
        raise FileNotFoundError(f"XPO файл не найден: {XPO_FILE}")
    if not DB_FILE.exists():
        raise FileNotFoundError(f"База данных не найдена: {DB_FILE}")
    
    try:
        label_loader = LabelLoader(str(ALD_FILE))
        xpo_reader = XPOReader(str(XPO_FILE), str(DB_FILE))
        parser_integration = ParserIntegration(str(PARSER_DIR))
    except Exception as e:
        print(f"Ошибка инициализации: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


# Создаем MCP сервер
server = Server(SERVER_NAME)


@server.list_tools()
async def list_tools() -> List[Tool]:
    """Возвращает список доступных инструментов"""
    return [
        Tool(
            name="get_element_code",
            description="Получает код элемента (класс/таблица/форма) из XPO файла и сохраняет в parserXPO",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_name": {
                        "type": "string",
                        "description": "Имя элемента"
                    },
                    "element_type": {
                        "type": "string",
                        "description": "Тип элемента (CLS/TAB/FRM)",
                        "enum": ["CLS", "TAB", "FRM"]
                    }
                },
                "required": ["element_name"]
            }
        ),
        Tool(
            name="get_method_code",
            description="Получает код конкретного метода элемента и сохраняет/обновляет в parserXPO",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_name": {
                        "type": "string",
                        "description": "Имя элемента"
                    },
                    "method_name": {
                        "type": "string",
                        "description": "Имя метода"
                    },
                    "element_type": {
                        "type": "string",
                        "description": "Тип элемента (CLS/TAB/FRM)",
                        "enum": ["CLS", "TAB", "FRM"]
                    }
                },
                "required": ["element_name", "method_name"]
            }
        ),
        Tool(
            name="search_labels_in_code",
            description="Ищет метки @MIK в коде элемента/метода и расшифровывает их из ALD",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_name": {
                        "type": "string",
                        "description": "Имя элемента"
                    },
                    "method_name": {
                        "type": "string",
                        "description": "Имя метода (опционально)"
                    }
                },
                "required": ["element_name"]
            }
        ),
        Tool(
            name="replace_labels_in_parser",
            description="Заменяет метки @MIK на их расшифровки в файлах parserXPO",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_name": {
                        "type": "string",
                        "description": "Имя элемента"
                    },
                    "method_name": {
                        "type": "string",
                        "description": "Имя метода (опционально, если не указано - обрабатываются все методы)"
                    },
                    "replace_mode": {
                        "type": "string",
                        "description": "Режим замены: comments (добавляет комментарии) или inline (заменяет inline)",
                        "enum": ["comments", "inline"],
                        "default": "comments"
                    }
                },
                "required": ["element_name"]
            }
        ),
        Tool(
            name="fulltext_search",
            description="Полнотекстовый поиск по коду в XPO файле",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Текст для поиска"
                    },
                    "element_type": {
                        "type": "string",
                        "description": "Тип элемента для фильтрации (CLS/TAB/FRM)",
                        "enum": ["CLS", "TAB", "FRM"]
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="find_label_usage",
            description="Ищет все места использования конкретной метки в коде",
            inputSchema={
                "type": "object",
                "properties": {
                    "label_id": {
                        "type": "string",
                        "description": "ID метки (например, 'MIK4140' или '4140')"
                    }
                },
                "required": ["label_id"]
            }
        ),
        Tool(
            name="integrate_search_results",
            description="Интегрирует результаты поиска в parserXPO (создает/обновляет файлы)",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_results": {
                        "type": "array",
                        "description": "Результаты поиска (массив объектов с element_name и element_type)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "element_name": {"type": "string"},
                                "element_type": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["search_results"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Обрабатывает вызовы инструментов"""
    global label_loader, xpo_reader, parser_integration
    
    # Ленивая инициализация компонентов
    if label_loader is None or xpo_reader is None or parser_integration is None:
        try:
            initialize_components()
        except Exception as e:
            error_msg = f"Ошибка инициализации компонентов: {str(e)}"
            print(error_msg, file=sys.stderr)
            return [TextContent(
                type="text",
                text=error_msg
            )]
    
    try:
        if name == "get_element_code":
            element_name = arguments.get("element_name")
            element_type = arguments.get("element_type")
            
            element_data = xpo_reader.get_element_code(element_name, element_type)
            if not element_data:
                return [TextContent(
                    type="text",
                    text=f"Элемент '{element_name}' не найден"
                )]
            
            success = parser_integration.save_element(element_data, overwrite=True)
            if success:
                methods_count = len(element_data.get('methods', {}))
                return [TextContent(
                    type="text",
                    text=f"Элемент '{element_name}' успешно сохранен в parserXPO. Методов: {methods_count}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Ошибка при сохранении элемента '{element_name}'"
                )]
        
        elif name == "get_method_code":
            element_name = arguments.get("element_name")
            method_name = arguments.get("method_name")
            element_type = arguments.get("element_type")
            
            method_code = xpo_reader.get_method_code(element_name, method_name, element_type)
            if not method_code:
                return [TextContent(
                    type="text",
                    text=f"Метод '{method_name}' не найден в элементе '{element_name}'"
                )]
            
            success = parser_integration.save_method(element_name, method_name, method_code, overwrite=True)
            if success:
                return [TextContent(
                    type="text",
                    text=f"Метод '{method_name}' успешно сохранен в parserXPO/{element_name}/{method_name}.xpp"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Ошибка при сохранении метода '{method_name}'"
                )]
        
        elif name == "search_labels_in_code":
            element_name = arguments.get("element_name")
            method_name = arguments.get("method_name")
            
            # Получаем код элемента или метода
            if method_name:
                code = parser_integration.read_method(element_name, method_name)
                if not code:
                    # Пробуем получить из XPO
                    element_type = None
                    element_info = xpo_reader.find_element(element_name)
                    if element_info:
                        element_type = element_info['element_type']
                    code = xpo_reader.get_method_code(element_name, method_name, element_type)
            else:
                methods = parser_integration.read_element_methods(element_name)
                if not methods:
                    # Получаем из XPO
                    element_data = xpo_reader.get_element_code(element_name)
                    if element_data:
                        methods = element_data.get('methods', {})
                
                # Объединяем код всех методов для поиска меток
                code = "\n".join(methods.values()) if methods else ""
            
            if not code:
                return [TextContent(
                    type="text",
                    text=f"Код не найден для элемента '{element_name}'" + (f", метода '{method_name}'" if method_name else "")
                )]
            
            # Ищем метки
            found_labels = label_loader.find_labels_in_text(code)
            
            if not found_labels:
                return [TextContent(
                    type="text",
                    text="Метки @MIK не найдены в коде"
                )]
            
            # Формируем результат
            result_lines = ["Найденные метки:"]
            for label_id, description in found_labels.items():
                result_lines.append(f"\n{label_id}: {description}")
            
            return [TextContent(
                type="text",
                text="\n".join(result_lines)
            )]
        
        elif name == "replace_labels_in_parser":
            element_name = arguments.get("element_name")
            method_name = arguments.get("method_name")
            replace_mode = arguments.get("replace_mode", "comments")
            
            # Получаем методы для обработки
            if method_name:
                methods_to_process = {method_name: None}
            else:
                methods_to_process = parser_integration.read_element_methods(element_name)
                if not methods_to_process:
                    # Получаем из XPO
                    element_data = xpo_reader.get_element_code(element_name)
                    if element_data:
                        methods_to_process = element_data.get('methods', {})
            
            if not methods_to_process:
                return [TextContent(
                    type="text",
                    text=f"Методы не найдены для элемента '{element_name}'"
                )]
            
            replaced_count = 0
            for method_name_item, method_code in methods_to_process.items():
                if method_code is None:
                    method_code = parser_integration.read_method(element_name, method_name_item)
                    if not method_code:
                        continue
                
                # Заменяем метки
                new_code = label_loader.replace_labels_in_text(method_code, mode=replace_mode)
                
                if new_code != method_code:
                    parser_integration.update_method(element_name, method_name_item, new_code)
                    replaced_count += 1
            
            return [TextContent(
                type="text",
                text=f"Обработано методов: {replaced_count} из {len(methods_to_process)}"
            )]
        
        elif name == "fulltext_search":
            query = arguments.get("query")
            element_type = arguments.get("element_type")
            
            results = xpo_reader.fulltext_search(query, element_type, limit=50)
            
            if not results:
                return [TextContent(
                    type="text",
                    text=f"По запросу '{query}' ничего не найдено"
                )]
            
            result_lines = [f"Найдено элементов: {len(results)}"]
            for result in results[:20]:  # Показываем первые 20
                result_lines.append(f"\n{result['element_type']}: {result['element_name']}")
            
            if len(results) > 20:
                result_lines.append(f"\n... и еще {len(results) - 20} элементов")
            
            return [TextContent(
                type="text",
                text="\n".join(result_lines)
            )]
        
        elif name == "find_label_usage":
            label_id = arguments.get("label_id")
            
            results = xpo_reader.find_label_usage(label_id)
            
            if not results:
                return [TextContent(
                    type="text",
                    text=f"Метка '{label_id}' не найдена в коде"
                )]
            
            result_lines = [f"Использования метки '{label_id}':"]
            for result in results:
                methods_str = ", ".join(result['methods']) if result['methods'] else "нет методов"
                result_lines.append(f"\n{result['element_type']} {result['element_name']}: {methods_str}")
            
            return [TextContent(
                type="text",
                text="\n".join(result_lines)
            )]
        
        elif name == "integrate_search_results":
            search_results = arguments.get("search_results", [])
            
            if not search_results:
                return [TextContent(
                    type="text",
                    text="Нет результатов для интеграции"
                )]
            
            integrated_count = 0
            for result in search_results:
                element_name = result.get("element_name")
                element_type = result.get("element_type")
                
                if element_name:
                    element_data = xpo_reader.get_element_code(element_name, element_type)
                    if element_data:
                        if parser_integration.save_element(element_data, overwrite=True):
                            integrated_count += 1
            
            return [TextContent(
                type="text",
                text=f"Интегрировано элементов: {integrated_count} из {len(search_results)}"
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Неизвестный инструмент: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Ошибка: {str(e)}"
        )]


async def main():
    """Главная функция запуска сервера"""
    # Не инициализируем компоненты при запуске - используем ленивую инициализацию
    # Это позволяет серверу запуститься даже если файлы временно недоступны
    
    # Выводим сообщение в stderr для отладки (не в stdout, чтобы не нарушать протокол)
    print(f"{SERVER_NAME} starting...", file=sys.stderr)
    
    try:
        async with stdio_server() as streams:
            print(f"{SERVER_NAME} ready", file=sys.stderr)
            await server.run(streams[0], streams[1], server.create_initialization_options())
    except Exception as e:
        print(f"Критическая ошибка сервера: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Выводим информацию о запуске в stderr для диагностики
    print(f"Python version: {sys.version}", file=sys.stderr)
    print(f"Working directory: {Path.cwd()}", file=sys.stderr)
    print(f"Script location: {Path(__file__).absolute()}", file=sys.stderr)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
        pass
    except Exception as e:
        print(f"Ошибка запуска: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

