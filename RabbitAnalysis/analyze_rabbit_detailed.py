#!/usr/bin/env python3
"""
Детальный анализ классов RabbitMQ интеграции
"""

import re
from pathlib import Path

XPO_PATH = "templates/PrivateProject_CUS_Layer_Export.xpo"

def extract_class(xpo_content, class_name):
    """Извлечение полного класса из XPO"""
    # Паттерн для поиска класса с учетом возможных пробелов
    pattern = rf'class\s+{re.escape(class_name)}(?:\s+extends\s+\w+)?\s*\{{'
    match = re.search(pattern, xpo_content)
    if not match:
        return None
    
    start = match.start()
    brace_count = 0
    in_string = False
    i = start
    
    while i < len(xpo_content):
        char = xpo_content[i]
        if char == '"' and (i == 0 or xpo_content[i-1] != '\\'):
            in_string = not in_string
        elif not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return xpo_content[start:i+1]
        i += 1
    return None

def extract_method(class_content, method_name):
    """Извлечение метода из класса"""
    # Ищем начало метода
    pattern = rf'(?:public|private|protected)\s+(?:void|str|int|real|boolean|container|utcdatetime|int64|var|\\\\w+)\s+{re.escape(method_name)}\s*\([^)]*\)\s*\{{'
    
    matches = list(re.finditer(pattern, class_content))
    if not matches:
        # Попробуем без модификаторов доступа
        pattern = rf'{re.escape(method_name)}\s*\([^)]*\)\s*\{{'
        matches = list(re.finditer(pattern, class_content))
    
    if not matches:
        return None
    
    # Берем первый найденный метод (они обычно в порядке объявления)
    start = matches[0].start()
    
    # Находим тело метода
    brace_count = 0
    in_string = False
    i = start
    
    while i < len(class_content):
        char = class_content[i]
        if char == '"' and (i == 0 or class_content[i-1] != '\\'):
            in_string = not in_string
        elif not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return class_content[start:i+1]
        i += 1
    return None

def get_all_methods(class_content):
    """Получение списка всех методов класса"""
    pattern = r'(?:public|private|protected)\s+(?:void|str|int|real|boolean|container|utcdatetime|int64|var|\w+)\s+(\w+)\s*\([^)]*\)'
    matches = re.findall(pattern, class_content)
    return sorted(set(matches))

def find_method_calls(method_content):
    """Поиск вызовов методов в коде"""
    calls = []
    
    # Паттерны для вызовов методов
    patterns = [
        r'(\w+)\s*=\s*new\s+(\w+)',  # Создание объектов
        r'(\w+)\.(\w+)\s*\(',         # Вызов методов
        r'(\w+)\s*::(\w+)\s*\(',      # Статические вызовы
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, method_content)
        calls.extend(matches)
    
    return calls

def find_class_hierarchy(xpo_content, class_name):
    """Поиск наследования класса"""
    pattern = rf'class\s+{re.escape(class_name)}\s+extends\s+(\w+)'
    match = re.search(pattern, xpo_content)
    if match:
        return match.group(1)
    return None

def main():
    print("=" * 70)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ RABBITMQ ИНТЕГРАЦИИ")
    print("=" * 70)
    
    print(f"\nЧтение файла: {XPO_PATH}")
    with open(XPO_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ключевые классы для анализа
    key_classes = [
        'RabbitConnection',
        'RabbitConn_Output',
        'RabbitIntEngineExportBatch'
    ]
    
    print("\n" + "=" * 70)
    print("1. ИЕРАРХИЯ НАСЛЕДОВАНИЯ")
    print("=" * 70)
    
    for cls in key_classes:
        parent = find_class_hierarchy(content, cls)
        print(f"\n{cls}")
        print(f"  Родитель: {parent or 'Нет (базовый класс)'}")
    
    print("\n" + "=" * 70)
    print("2. МЕТОДЫ КЛАССОВ")
    print("=" * 70)
    
    for cls in key_classes:
        print(f"\n--- {cls} ---")
        class_block = extract_class(content, cls)
        if class_block:
            methods = get_all_methods(class_block)
            print(f"  Методов: {len(methods)}")
            for m in methods:
                print(f"    - {m}")
        else:
            print("  Класс не найден!")
    
    print("\n" + "=" * 70)
    print("3. МЕТОД runComplexExport")
    print("=" * 70)
    
    cls = 'RabbitIntEngineExportBatch'
    class_block = extract_class(content, cls)
    if class_block:
        method = extract_method(class_block, 'runComplexExport')
        if method:
            print(f"\nМетод найден! Размер: {len(method):,} символов")
            print("\n" + "-" * 50)
            print(method[:3000])
            if len(method) > 3000:
                print(f"\n... (обрезано, всего {len(method)} символов)")
            
            # Поиск вызовов в методе
            print("\n" + "=" * 70)
            print("4. ВЫЗОВЫ ВНУТРИ runComplexExport")
            print("=" * 70)
            
            calls = find_method_calls(method)
            print(f"\nНайдено вызовов: {len(calls)}")
            unique_calls = set(calls)
            for call in sorted(unique_calls)[:50]:
                print(f"  {call}")
        else:
            print("Метод runComplexExport не найден!")
            # Поищем похожие методы
            methods = get_all_methods(class_block)
            export_methods = [m for m in methods if 'export' in m.lower() or 'run' in m.lower()]
            print(f"\nПохожие методы: {export_methods}")
    else:
        print(f"Класс {cls} не найден!")
    
    print("\n" + "=" * 70)
    print("5. КЛАСС RabbitConn_Output")
    print("=" * 70)
    
    cls = 'RabbitConn_Output'
    class_block = extract_class(content, cls)
    if class_block:
        methods = get_all_methods(class_block)
        print(f"\nМетоды RabbitConn_Output ({len(methods)}):")
        for m in methods:
            print(f"  - {m}")
        
        # Ищем метод init
        init_method = extract_method(class_block, 'init')
        if init_method:
            print(f"\nМетод init найден! Размер: {len(init_method):,} символов")
            print("-" * 50)
            print(init_method[:1500])
            if len(init_method) > 1500:
                print(f"\n... (обрезано, всего {len(init_method)} символов)")
    else:
        print("Класс RabbitConn_Output не найден!")

if __name__ == "__main__":
    main()