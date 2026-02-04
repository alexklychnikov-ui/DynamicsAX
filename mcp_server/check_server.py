#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностический скрипт для проверки сервера
"""
import sys
from pathlib import Path

print("=== Диагностика MCP сервера ===\n")

# Проверка импортов
print("1. Проверка импортов...")
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    print("   [OK] MCP импорты работают")
except Exception as e:
    print(f"   [ERROR] Ошибка импорта MCP: {e}")
    sys.exit(1)

try:
    from label_loader import LabelLoader
    from xpo_reader import XPOReader
    from parser_integration import ParserIntegration
    print("   [OK] Локальные импорты работают")
except Exception as e:
    print(f"   [ERROR] Ошибка импорта локальных модулей: {e}")
    sys.exit(1)

# Проверка путей
print("\n2. Проверка путей...")
_current_dir = Path(__file__).parent
if _current_dir.name == "mcp_server":
    PROJECT_ROOT = _current_dir.parent
else:
    PROJECT_ROOT = _current_dir

XPO_FILE = PROJECT_ROOT / "AOT_cus" / "PrivateProject_CUS_Layer_Export.xpo"
ALD_FILE = PROJECT_ROOT / "AOT_cus" / "AxMIKru.ald"
DB_FILE = PROJECT_ROOT / "indexXPO_cus" / "xpo_index.db"
PARSER_DIR = PROJECT_ROOT / "parserXPO"

print(f"   PROJECT_ROOT: {PROJECT_ROOT}")
print(f"   ALD_FILE: {ALD_FILE} (exists: {ALD_FILE.exists()})")
print(f"   XPO_FILE: {XPO_FILE} (exists: {XPO_FILE.exists()})")
print(f"   DB_FILE: {DB_FILE} (exists: {DB_FILE.exists()})")
print(f"   PARSER_DIR: {PARSER_DIR} (exists: {PARSER_DIR.exists()})")

# Проверка инициализации
print("\n3. Проверка инициализации компонентов...")
try:
    label_loader = LabelLoader(str(ALD_FILE))
    print(f"   [OK] LabelLoader: загружено {len(label_loader.get_all_labels())} меток")
except Exception as e:
    print(f"   [ERROR] LabelLoader: {e}")
    import traceback
    traceback.print_exc()

try:
    xpo_reader = XPOReader(str(XPO_FILE), str(DB_FILE))
    print("   [OK] XPOReader инициализирован")
    xpo_reader.close()
except Exception as e:
    print(f"   [ERROR] XPOReader: {e}")
    import traceback
    traceback.print_exc()

try:
    parser_integration = ParserIntegration(str(PARSER_DIR))
    print("   [OK] ParserIntegration инициализирован")
except Exception as e:
    print(f"   [ERROR] ParserIntegration: {e}")
    import traceback
    traceback.print_exc()

# Проверка создания сервера
print("\n4. Проверка создания MCP сервера...")
try:
    server = Server("dynamics-ax-mcp")
    print("   [OK] Сервер создан")
except Exception as e:
    print(f"   [ERROR] Создание сервера: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Диагностика завершена ===")

















