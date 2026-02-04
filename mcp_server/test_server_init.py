#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки инициализации сервера
"""
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from server import PROJECT_ROOT, ALD_FILE, XPO_FILE, DB_FILE, PARSER_DIR, initialize_components

print("Проверка путей:")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"ALD_FILE: {ALD_FILE} (exists: {ALD_FILE.exists()})")
print(f"XPO_FILE: {XPO_FILE} (exists: {XPO_FILE.exists()})")
print(f"DB_FILE: {DB_FILE} (exists: {DB_FILE.exists()})")
print(f"PARSER_DIR: {PARSER_DIR} (exists: {PARSER_DIR.exists()})")
print()

print("Инициализация компонентов...")
try:
    initialize_components()
    print("[OK] Инициализация успешна!")
except Exception as e:
    print(f"[ERROR] Ошибка: {e}")
    import traceback
    traceback.print_exc()

