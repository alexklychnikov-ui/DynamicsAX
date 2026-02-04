#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ XPO файла в формате Microsoft Dynamics AX
"""

import re
import sys
import codecs

XPO_PATH = "templates/PrivateProject_CUS_Layer_Export.xpo"

def safe_print(text):
    """Безопасный вывод с заменой непечатаемых символов"""
    try:
        # Заменяем непечатаемые символы
        clean_text = ''.join(c if c.isprintable() or c in '\n\r\t' else '?' for c in text)
        print(clean_text)
    except:
        print("?")

def extract_class_xpo(xpo_content, class_name):
    """Извлечение класса из XPO файла (формат AX)"""
    # Ищем начало класса - формат: CLASS #ClassName
    pattern = rf'CLASS #{re.escape(class_name)}\b'
    match = re.search(pattern, xpo_content)
    if not match:
        return None
    
    start = match.start()
    
    # Ищем конец класса - следующий CLASS # или конец файла
    # Ищем по ключевым словам - начало нового элемента
    end_pattern = r'^  CLASS #\w+'
    end_match = re.search(end_pattern, xpo_content[start:], re.MULTILINE)
    
    if end_match:
        end = start + end_match.start()
    else:
        end = len(xpo_content)
    
    return xpo_content[start:end]

def get_class_methods_xpo(class_content):
    """Получение списка методов из класса XPO"""
    methods = []
    
    # Паттерны для поиска методов - формат: METHOD #MethodName
    pattern = r'^    METHOD #(\w+)\s*$'
    matches = re.findall(pattern, class_content, re.MULTILINE)
    methods.extend(matches)
    
    return sorted(set(methods))

def extract_method_xpo(class_content, method_name):
    """Извлечение метода из класса XPO"""
    # Ищем начало метода - формат: METHOD #MethodName
    pattern = rf'^    METHOD #{re.escape(method_name)}\s*$'
    match = re.search(pattern, class_content, re.MULTILINE)
    if not match:
        return None
    
    start = match.start()
    
    # Ищем конец метода - следующий METHOD # или конец класса
    end_pattern = r'^    METHOD #\w+'
    end_match = re.search(end_pattern, class_content[start:], re.MULTILINE)
    
    if end_match:
        end = start + end_match.start()
    else:
        end = len(class_content)
    
    return class_content[start:end]

def get_method_source_code(method_content):
    """Извлечение исходного кода метода из XPO формата"""
    # Ищем блок SOURCE внутри метода
    source_pattern = r'      SOURCE(.*?)      END_SOURCE'
    match = re.search(source_pattern, method_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def main():
    safe_print("=" * 70)
    safe_print("ПОЛНЫЙ АНАЛИЗ RABBITMQ ИНТЕГРАЦИИ")
    safe_print("=" * 70)
    
    safe_print(f"\nЧтение файла: {XPO_PATH}")
    with open(XPO_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    safe_print(f"Размер файла: {len(content):,} символов")
    
    # === RABBITCONNECTION ===
    safe_print("\n" + "=" * 70)
    safe_print("1. RABBITCONNECTION (БАЗОВЫЙ КЛАСС)")
    safe_print("=" * 70)
    
    rabbit_conn = extract_class_xpo(content, 'RabbitConnection')
    if rabbit_conn:
        safe_print(f"\nРазмер: {len(rabbit_conn):,} символов")
        
        methods = get_class_methods_xpo(rabbit_conn)
        safe_print(f"Методов: {len(methods)}")
        for m in methods:
            safe_print(f"  - {m}")
        
        # Показать код методов
        for method_name in methods[:5]:  # Первые 5 методов
            method = extract_method_xpo(rabbit_conn, method_name)
            if method:
                source = get_method_source_code(method)
                if source:
                    safe_print(f"\n--- Метод {method_name} ---")
                    safe_print(source[:500])
    else:
        safe_print("Класс RabbitConnection НЕ НАЙДЕН!")
    
    # === RABBITCONN_OUTPUT ===
    safe_print("\n" + "=" * 70)
    safe_print("2. RABBITCONN_OUTPUT (НАСЛЕДНИК RabbitConnection)")
    safe_print("=" * 70)
    
    rabbit_output = extract_class_xpo(content, 'RabbitConn_Output')
    if rabbit_output:
        safe_print(f"\nРазмер: {len(rabbit_output):,} символов")
        
        methods = get_class_methods_xpo(rabbit_output)
        safe_print(f"Методов: {len(methods)}")
        for m in methods:
            safe_print(f"  - {m}")
        
        # Показать код методов
        for method_name in methods:
            method = extract_method_xpo(rabbit_output, method_name)
            if method:
                source = get_method_source_code(method)
                if source:
                    safe_print(f"\n--- Метод {method_name} ---")
                    safe_print(source[:500])
    else:
        safe_print("Класс RabbitConn_Output НЕ НАЙДЕН!")
    
    # === RABBITINTENGINEEXPORTBATCH ===
    safe_print("\n" + "=" * 70)
    safe_print("3. RABBITINTENGINEEXPORTBATCH")
    safe_print("=" * 70)
    
    rabbit_batch = extract_class_xpo(content, 'RabbitIntEngineExportBatch')
    if rabbit_batch:
        safe_print(f"\nРазмер: {len(rabbit_batch):,} символов")
        
        methods = get_class_methods_xpo(rabbit_batch)
        safe_print(f"Методов: {len(methods)}")
        for m in methods:
            safe_print(f"  - {m}")
        
        # Показать код методов
        for method_name in methods:
            method = extract_method_xpo(rabbit_batch, method_name)
            if method:
                source = get_method_source_code(method)
                if source:
                    safe_print(f"\n--- Метод {method_name} ---")
                    safe_print(source[:800])
    else:
        safe_print("Класс RabbitIntEngineExportBatch НЕ НАЙДЕН!")

if __name__ == "__main__":
    main()