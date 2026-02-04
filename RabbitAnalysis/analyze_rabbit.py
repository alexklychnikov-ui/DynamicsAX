#!/usr/bin/env python3
"""
Анализ классов RabbitMQ интеграции из базы данных xpo_index.db
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = "indexXPO_cus/xpo_index.db"

def get_db_connection():
    """Подключение к базе данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_tables(conn):
    """Получение списка всех таблиц в базе"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def search_class(conn, class_name):
    """Поиск класса по имени"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM classes 
        WHERE name LIKE ? OR name LIKE ?
    """, (f'%{class_name}%', f'{class_name}%'))
    return cursor.fetchall()

def search_method_in_class(conn, class_name, method_name):
    """Поиск метода в классе"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.* FROM methods m
        JOIN classes c ON m.class_id = c.id
        WHERE c.name = ? AND m.name = ?
    """, (class_name, method_name))
    return cursor.fetchall()

def get_class_methods(conn, class_name):
    """Получение всех методов класса"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.* FROM methods m
        JOIN classes c ON m.class_id = c.id
        WHERE c.name = ?
        ORDER BY m.name
    """, (class_name,))
    return cursor.fetchall()

def get_class_info(conn, class_name):
    """Получение полной информации о классе"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM classes WHERE name = ?
    """, (class_name,))
    return cursor.fetchone()

def get_method_code(conn, class_name, method_name):
    """Получение кода метода"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.code FROM methods m
        JOIN classes c ON m.class_id = c.id
        WHERE c.name = ? AND m.name = ?
    """, (class_name, method_name))
    result = cursor.fetchone()
    return result['code'] if result else None

def search_references_to_class(conn, class_name):
    """Поиск всех ссылок на класс в других классах"""
    cursor = conn.cursor()
    # Ищем упоминания класса в коде
    cursor.execute("""
        SELECT DISTINCT c.name as class_name, m.name as method_name, m.code
        FROM methods m
        JOIN classes c ON m.class_id = c.id
        WHERE m.code LIKE ? OR m.code LIKE ?
    """, (f'%{class_name}%', f'::{class_name}'))
    return cursor.fetchall()

def find_all_rabbit_classes(conn):
    """Поиск всех классов, связанных с RabbitMQ"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM classes 
        WHERE name LIKE '%Rabbit%' OR name LIKE '%rabbit%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]

def find_all_related_classes(conn):
    """Поиск всех связанных классов (не только Rabbit)"""
    # Классы, которые могут быть связаны с интеграцией
    related_keywords = ['Rabbit', 'rabbit', 'Output', 'Conn', 'Integration', 
                        'Message', 'Queue', 'Exchange', 'IntEngine', 'Batch']
    cursor = conn.cursor()
    
    placeholders = ' OR '.join([f"name LIKE '%{kw}%'" for kw in related_keywords])
    cursor.execute(f"SELECT name FROM classes WHERE {placeholders} ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def get_class_hierarchy(conn, class_name):
    """Получение иерархии наследования класса"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT extends FROM classes WHERE name = ?
    """, (class_name,))
    result = cursor.fetchone()
    if result and result['extends']:
        return result['extends']
    return None

def main():
    conn = get_db_connection()
    
    print("=" * 60)
    print("АНАЛИЗ КЛАССОВ RABBITMQ ИНТЕГРАЦИИ")
    print("=" * 60)
    
    # Поиск всех Rabbit классов
    rabbit_classes = find_all_rabbit_classes(conn)
    print(f"\nНайдено Rabbit классов: {len(rabbit_classes)}")
    for cls in rabbit_classes:
        print(f"  - {cls}")
    
    # Поиск связанных классов
    related_classes = find_all_related_classes(conn)
    print(f"\nВсего связанных классов: {len(related_classes)}")
    
    # Детальный анализ ключевых классов
    key_classes = [
        'RabbitConnection',
        'RabbitConn_Output', 
        'RabbitIntEngineExportBatch'
    ]
    
    print("\n" + "=" * 60)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ КЛЮЧЕВЫХ КЛАССОВ")
    print("=" * 60)
    
    for class_name in key_classes:
        print(f"\n--- {class_name} ---")
        info = get_class_info(conn, class_name)
        if info:
            print(f"  ID: {info['id']}")
            print(f"  Extends: {info['extends'] or 'Нет наследования'}")
            methods = get_class_methods(conn, class_name)
            print(f"  Методов: {len(methods)}")
            for m in methods:
                print(f"    - {m['name']}")
        else:
            print("  Класс не найден!")
    
    # Поиск runComplexExport метода
    print("\n" + "=" * 60)
    print("МЕТОД runComplexExport В RabbitIntEngineExportBatch")
    print("=" * 60)
    
    code = get_method_code(conn, 'RabbitIntEngineExportBatch', 'runComplexExport')
    if code:
        print(f"Код метода ({len(code)} символов):")
        print("-" * 40)
        print(code[:3000])
        if len(code) > 3000:
            print("\n... (код обрезан)")
    else:
        print("Метод не найден!")
    
    conn.close()

if __name__ == "__main__":
    main()