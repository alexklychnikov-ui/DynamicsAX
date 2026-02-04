#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный анализ XPO файла - извлечение методов из блоков SOURCE
"""

import re
import sys

XPO_PATH = "templates/PrivateProject_CUS_Layer_Export.xpo"

def safe_print(text):
    """Безопасный вывод"""
    try:
        clean_text = ''.join(c if c.isprintable() or c in '\n\r\t' else '?' for c in text)
        print(clean_text)
    except:
        print("?")

def extract_class_xpo(xpo_content, class_name):
    """Извлечение класса"""
    pattern = rf'CLASS #{class_name}\b'
    match = re.search(pattern, xpo_content)
    if not match:
        return None
    start = match.start()
    end_pattern = r'^  CLASS #\w+'
    end_match = re.search(end_pattern, xpo_content[start:], re.MULTILINE)
    if end_match:
        end = start + end_match.start()
    else:
        end = len(xpo_content)
    return xpo_content[start:end]

def get_source_methods(class_content):
    """Извлечение методов из блоков SOURCE"""
    methods = {}
    
    # Паттерн для SOURCE блоков
    pattern = r'      SOURCE #(\w+)\s*(.*?)      ENDSOURCE'
    matches = re.findall(pattern, class_content, re.DOTALL)
    
    for method_name, source_code in matches:
        methods[method_name] = source_code.strip()
    
    return methods

def find_all_calls_in_code(code):
    """Поиск вызовов методов в коде"""
    calls = []
    
    # Паттерны вызовов
    patterns = [
        (r'(\w+)\s*=\s*new\s+(\w+)', 'Создание объекта'),
        (r'(\w+)\.(\w+)\s*\(', 'Вызов метода'),
        (r'(\w+)\s*::(\w+)\s*\(', 'Статический вызов'),
    ]
    
    for pattern, desc in patterns:
        matches = re.findall(pattern, code)
        for m in matches:
            calls.append((desc, m))
    
    return calls

def main():
    safe_print("=" * 70)
    safe_print("ПОЛНЫЙ АНАЛИЗ RABBITMQ ИНТЕГРАЦИИ")
    safe_print("=" * 70)
    
    with open(XPO_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # === RABBITCONNECTION ===
    safe_print("\n" + "=" * 70)
    safe_print("1. RABBITCONNECTION (БАЗОВЫЙ КЛАСС)")
    safe_print("=" * 70)
    
    rabbit_conn = extract_class_xpo(content, 'RabbitConnection')
    if rabbit_conn:
        safe_print(f"\nРазмер: {len(rabbit_conn)} символов")
        methods = get_source_methods(rabbit_conn)
        safe_print(f"Методов/блоков SOURCE: {len(methods)}")
        for name in methods:
            safe_print(f"  - {name}")
    else:
        safe_print("НЕ НАЙДЕН!")

    # === RABBITCONN_OUTPUT ===
    safe_print("\n" + "=" * 70)
    safe_print("2. RABBITCONN_OUTPUT")
    safe_print("=" * 70)
    
    rabbit_output = extract_class_xpo(content, 'RabbitConn_Output')
    if rabbit_output:
        safe_print(f"\nРазмер: {len(rabbit_output)} символов")
        methods = get_source_methods(rabbit_output)
        safe_print(f"Методов/блоков SOURCE: {len(methods)}")
        
        for method_name, code in methods.items():
            safe_print(f"\n--- {method_name} ---")
            safe_print(code[:600])
    else:
        safe_print("НЕ НАЙДЕН!")

    # === RABBITINTENGINEEXPORTBATCH ===
    safe_print("\n" + "=" * 70)
    safe_print("3. RABBITINTENGINEEXPORTBATCH")
    safe_print("=" * 70)
    
    rabbit_batch = extract_class_xpo(content, 'RabbitIntEngineExportBatch')
    if rabbit_batch:
        safe_print(f"\nРазмер: {len(rabbit_batch)} символов")
        methods = get_source_methods(rabbit_batch)
        safe_print(f"Методов/блоков SOURCE: {len(methods)}")
        
        for method_name, code in sorted(methods.items()):
            safe_print(f"\n=== МЕТОД: {method_name} ===")
            safe_print(code)
    else:
        safe_print("НЕ НАЙДЕН!")

if __name__ == "__main__":
    main()