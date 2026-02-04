#!/usr/bin/env python3
"""
Исследование структуры базы данных xpo_index.db
"""

import sqlite3
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
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def get_table_schema(conn, table_name):
    """Получение схемы таблицы"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def get_element_sample(conn, element_type=None, limit=10):
    """Получение примеров элементов"""
    cursor = conn.cursor()
    if element_type:
        cursor.execute(f"SELECT * FROM elements WHERE element_type = ? LIMIT {limit}", (element_type,))
    else:
        cursor.execute(f"SELECT * FROM elements LIMIT {limit}")
    return cursor.fetchall()

def get_methods_for_element(conn, element_id):
    """Получение методов для элемента"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM methods WHERE element_id = ?", (element_id,))
    return cursor.fetchall()

def find_elements_by_name(conn, name_pattern, element_type=None):
    """Поиск элементов по имени"""
    cursor = conn.cursor()
    if element_type:
        cursor.execute(
            "SELECT * FROM elements WHERE element_name LIKE ? AND element_type = ?",
            (f'%{name_pattern}%', element_type)
        )
    else:
        cursor.execute(
            "SELECT * FROM elements WHERE element_name LIKE ?",
            (f'%{name_pattern}%',)
        )
    return cursor.fetchall()

def find_methods_by_name(conn, method_name):
    """Поиск методов по имени"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM methods WHERE name LIKE ?", (f'%{method_name}%',))
    return cursor.fetchall()

def main():
    conn = get_db_connection()
    
    print("=" * 60)
    print("ИССЛЕДОВАНИЕ СТРУКТУРЫ XPO_INDEX.DB")
    print("=" * 60)
    
    # Типы элементов
    print("\n--- ТИПЫ ЭЛЕМЕНТОВ ---")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT element_type FROM elements ORDER BY element_type")
    for row in cursor.fetchall():
        print(f"  {row['element_type']}")
    
    # Статистика по типам
    print("\n--- СТАТИСТИКА ---")
    cursor.execute("SELECT element_type, COUNT(*) as cnt FROM elements GROUP BY element_type ORDER BY cnt DESC")
    for row in cursor.fetchall():
        print(f"  {row['element_type']}: {row['cnt']}")
    
    # Поиск Rabbit классов
    print("\n--- ПОИСК RABBIT КЛАССОВ ---")
    rabbit_elements = find_elements_by_name(conn, 'Rabbit', 'Class')
    print(f"Найдено классов с 'Rabbit': {len(rabbit_elements)}")
    for elem in rabbit_elements:
        print(f"  ID={elem['id']}: {elem['element_name']} ({elem['element_type']})")
    
    # Поиск по разным паттернам
    print("\n--- РАСШИРЕННЫЙ ПОИСК ---")
    patterns = ['Rabbit', 'rabbit', 'Output', 'Conn', 'Message', 'Queue', 'Exchange', 'IntEngine', 'Integration']
    
    for pattern in patterns:
        elements = find_elements_by_name(conn, pattern, 'Class')
        if elements:
            print(f"\n'{pattern}': найдено {len(elements)} классов")
            for elem in elements[:10]:
                print(f"  - {elem['element_name']} (ID={elem['id']})")
            if len(elements) > 10:
                print(f"  ... и ещё {len(elements) - 10}")
    
    # Поиск ключевых классов
    print("\n--- ПОИСК КЛЮЧЕВЫХ КЛАССОВ ---")
    key_classes = ['RabbitConnection', 'RabbitConn_Output', 'RabbitIntEngineExportBatch']
    for cls in key_classes:
        elements = find_elements_by_name(conn, cls, 'Class')
        if elements:
            elem = elements[0]
            print(f"\n{cls}:")
            print(f"  ID: {elem['id']}")
            print(f"  Position: {elem['file_position']}, Size: {elem['size']}")
            
            # Методы
            methods = get_methods_for_element(conn, elem['id'])
            print(f"  Методов: {len(methods)}")
            for m in methods[:20]:  # Первые 20
                print(f"    - {m['name']}")
            if len(methods) > 20:
                print(f"    ... и ещё {len(methods) - 20}")
        else:
            print(f"\n{cls}: НЕ НАЙДЕН")
    
    conn.close()

if __name__ == "__main__":
    main()