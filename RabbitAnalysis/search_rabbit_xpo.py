#!/usr/bin/env python3
"""
Поиск классов RabbitMQ в XPO файле
"""

import re
from pathlib import Path

XPO_PATH = "templates/PrivateProject_CUS_Layer_Export.xpo"

def find_class_block(text, class_name):
    """Поиск блока класса в XPO файле"""
    # Ищем начало класса
    pattern = rf'class {class_name}(?:\s+extends\s+\w+)?(?:\s+\{{\s*)'
    match = re.search(pattern, text)
    if match:
        start = match.start()
        # Находим закрывающую скобку
        brace_count = 0
        in_string = False
        i = start
        while i < len(text):
            char = text[i]
            if char == '"' and (i == 0 or text[i-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return text[start:i+1]
            i += 1
    return None

def search_rabbit_classes(xpo_content):
    """Поиск всех классов связанных с RabbitMQ"""
    rabbit_classes = []
    
    # Паттерны для поиска
    patterns = [
        r'class\s+(\w*Rabbit\w*)',
        r'class\s+(\w*RabbitConnection\w*)',
        r'class\s+(\w*RabbitConn\w*)',
        r'class\s+(\w*IntEngine\w*)',
        r'class\s+(\w*ExportBatch\w*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, xpo_content, re.IGNORECASE)
        for m in matches:
            if m not in rabbit_classes:
                rabbit_classes.append(m)
    
    return sorted(set(rabbit_classes))

def find_method_in_xpo(xpo_content, class_name, method_name):
    """Поиск метода в классе"""
    class_block = find_class_block(xpo_content, class_name)
    if not class_block:
        return None
    
    # Ищем метод
    pattern = rf'{method_name}\s*\([^)]*\)\s*\{{'
    match = re.search(pattern, class_block)
    if match:
        start = match.start()
        brace_count = 0
        in_string = False
        i = start
        while i < len(class_block):
            char = class_block[i]
            if char == '"' and (i == 0 or class_block[i-1] != '\\'):
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return class_block[start:i+1]
            i += 1
    return None

def main():
    print("=" * 60)
    print("ПОИСК RABBITMQ КЛАССОВ В XPO ФАЙЛЕ")
    print("=" * 60)
    
    print(f"\nЧтение файла: {XPO_PATH}")
    with open(XPO_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Размер файла: {len(content):,} символов")
    
    # Поиск всех классов
    print("\n--- ПОИСК ВСЕХ RABBITMQ СВЯЗАННЫХ КЛАССОВ ---")
    classes = search_rabbit_classes(content)
    print(f"Найдено: {len(classes)}")
    for cls in classes:
        print(f"  - {cls}")
    
    # Поиск конкретных классов
    target_classes = ['RabbitConnection', 'RabbitConn_Output', 'RabbitIntEngineExportBatch']
    print("\n--- ПОИСК КОНКРЕТНЫХ КЛАССОВ ---")
    
    for cls_name in target_classes:
        print(f"\n{cls_name}:")
        class_block = find_class_block(content, cls_name)
        if class_block:
            print(f"  Найден! Размер блока: {len(class_block):,} символов")
            # Показать первые 500 символов
            print(f"  Начало: {class_block[:500]}...")
        else:
            print("  НЕ НАЙДЕН")
    
    # Поиск метода runComplexExport
    print("\n--- ПОИСК МЕТОДА runComplexExport ---")
    method = find_method_in_xpo(content, 'RabbitIntEngineExportBatch', 'runComplexExport')
    if method:
        print(f"Метод найден! Размер: {len(method):,} символов")
        print("-" * 40)
        print(method[:2000])
        if len(method) > 2000:
            print("...")
    else:
        print("Метод НЕ НАЙДЕН")

if __name__ == "__main__":
    main()