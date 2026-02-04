#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для чтения XPO файла и извлечения кода элементов/методов
Использует SQLite индекс для быстрого поиска позиций
"""
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from utils.xpo_utils import (
    clean_xpo_code,
    extract_methods,
    extract_properties,
    find_labels_in_text,
)


class XPOReader:
    def __init__(self, xpo_file_path: str, db_file_path: str):
        self.xpo_file_path = Path(xpo_file_path)
        self.db_file_path = Path(db_file_path)
        self.conn = None
        self._connect_db()
    
    def _connect_db(self):
        """Подключается к SQLite базе данных"""
        if not self.db_file_path.exists():
            raise FileNotFoundError(f"База данных не найдена: {self.db_file_path}")
        
        self.conn = sqlite3.connect(str(self.db_file_path))
        self.conn.row_factory = sqlite3.Row
    
    def find_element(self, element_name: str, element_type: Optional[str] = None) -> Optional[Dict]:
        """Находит элемент в базе данных
        
        Args:
            element_name: Имя элемента
            element_type: Тип элемента (CLS/TAB/FRM) или None для поиска по всем типам
        
        Returns:
            # [removed corrupted text]
        """
        cursor = self.conn.cursor()
        
        if element_type:
            cursor.execute("""
                SELECT id, element_type, element_name, file_position, size, method_count
                FROM elements
                WHERE element_name = ? AND element_type = ?
            """, (element_name, element_type))
        else:
            cursor.execute("""
                SELECT id, element_type, element_name, file_position, size, method_count
                FROM elements
                WHERE element_name = ?
                LIMIT 1
            """, (element_name,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_element_methods(self, element_id: int) -> List[str]:
        """Получает список методов элемента
        
        Args:
            element_id: ID элемента в базе данных
        
        Returns:
            # [removed corrupted text]
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT method_name
            FROM methods
            WHERE element_id = ?
            ORDER BY method_name
        """, (element_id,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def _read_xpo_segment(self, start_pos: int, size: int) -> str:
        """Читает сегмент из XPO файла
        
        Args:
            start_pos: Начальная позиция
            # [removed corrupted text]
        
        Returns:
            # [removed corrupted text]
        """
        with open(self.xpo_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(start_pos)
            return f.read(size)
    
    def get_element_code(self, element_name: str, element_type: Optional[str] = None) -> Optional[Dict]:
        """Получает полный код элемента из XPO файла
        
        Args:
            element_name: Имя элемента
            element_type: Тип элемента (CLS/TAB/FRM) или None
        
        Returns:
            # [removed corrupted text]
        """
        element_info = self.find_element(element_name, element_type)
        if not element_info:
            return None
        
        # Читаем содержимое элемента из XPO
        element_content = self._read_xpo_segment(
            element_info['file_position'],
            element_info['size']
        )
        
        # Парсим элемент с использованием утилит
        return {
            'type': element_info['element_type'],
            'name': element_info['element_name'],
            'properties': extract_properties(element_content),
            'methods': extract_methods(element_content)
        }
        
    def get_method_code(self, element_name: str, method_name: str, element_type: Optional[str] = None) -> Optional[str]:
        """Получает код конкретного метода элемента
        
        Args:
            element_name: Имя элемента
            method_name: Имя метода
            element_type: Тип элемента (CLS/TAB/FRM) или None
        
        Returns:
            Код метода или None
        """
        element_data = self.get_element_code(element_name, element_type)
        if not element_data:
            return None
        
        return element_data['methods'].get(method_name)
    
    def fulltext_search(self, query: str, element_type: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Выполняет полнотекстовый поиск по коду
        
        Args:
            query: Текст для поиска
            element_type: Тип элемента для фильтрации или None
            limit: Максимальное количество результатов
        
        Returns:
            # [removed corrupted text]
        """
        cursor = self.conn.cursor()
        
        # Проверяем наличие FTS5
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='elements_fts'")
        has_fts5 = cursor.fetchone() is not None
        
        if has_fts5:
            # Используем FTS5 для поиска
            if element_type:
                cursor.execute("""
                    SELECT e.id, e.element_type, e.element_name, e.file_position, e.size
                    FROM elements_fts fts
                    JOIN elements e ON e.id = fts.rowid
                    WHERE elements_fts MATCH ? AND e.element_type = ?
                    LIMIT ?
                """, (query, element_type, limit))
            else:
                cursor.execute("""
                    SELECT e.id, e.element_type, e.element_name, e.file_position, e.size
                    FROM elements_fts fts
                    JOIN elements e ON e.id = fts.rowid
                    WHERE elements_fts MATCH ?
                    LIMIT ?
                """, (query, limit))
        else:
            # Простой поиск по имени и типу
            search_pattern = f"%{query}%"
            if element_type:
                cursor.execute("""
                    SELECT id, element_type, element_name, file_position, size
                    FROM elements
                    WHERE element_name LIKE ? AND element_type = ?
                    LIMIT ?
                """, (search_pattern, element_type, limit))
            else:
                cursor.execute("""
                    SELECT id, element_type, element_name, file_position, size
                    FROM elements
                    WHERE element_name LIKE ?
                    LIMIT ?
                """, (search_pattern, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        return results
    
    def find_label_usage(self, label_id: str) -> List[Dict]:
        """Ищет все места использования метки в коде
        
        Args:
            label_id: ID метки (например, "MIK4140" или "4140")
        
        Returns:
            # [removed corrupted text]
        """
        # Нормализуем ID метки
        if not label_id.startswith('MIK'):
            label_id = f"MIK{label_id}"
        
        label_pattern = f"@MIK{label_id[3:]}"  # Убираем MIK из начала
        label_pattern2 = f"Label #@MIK{label_id[3:]}"
        
        results = []
        
        # Читаем весь XPO файл для поиска (это может быть медленно для больших файлов)
        # В реальности лучше было бы создать индекс меток, но для MVP используем простой поиск
        with open(self.xpo_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Находим все элементы
        element_pattern = re.compile(r'^\*\*\*Element:\s*(\w+)', re.MULTILINE)
        elements = list(element_pattern.finditer(content))
        
        for i, element_match in enumerate(elements):
            element_type = element_match.group(1)
            start_pos = element_match.start()
            end_pos = elements[i + 1].start() if i + 1 < len(elements) else len(content)
            element_content = content[start_pos:end_pos]
            
            # Ищем метку в содержимом элемента
            if label_pattern in element_content or label_pattern2 in element_content:
                # Извлекаем имя элемента
                element_name = None
                if element_type == 'CLS':
                    match = re.search(r'CLASS\s+#(\w+)', element_content)
                    if match:
                        element_name = match.group(1)
                elif element_type == 'TAB':
                    match = re.search(r'TABLE\s+#(\w+)', element_content)
                    if match:
                        element_name = match.group(1)
                elif element_type == 'FRM':
                    match = re.search(r'FORM\s+#(\w+)', element_content)
                    if match:
                        element_name = match.group(1)
                
                if element_name:
                    # Ищем в каких методах используется метка
                    methods_with_label = []
                    source_pattern = r'SOURCE\s+#(\w+)(.*?)ENDSOURCE'
                    for method_match in re.finditer(source_pattern, element_content, re.DOTALL):
                        method_name = method_match.group(1)
                        method_code = method_match.group(2)
                        if label_pattern in method_code or label_pattern2 in method_code:
                            methods_with_label.append(method_name)
                    
                    results.append({
                        'element_type': element_type,
                        'element_name': element_name,
                        'methods': methods_with_label
                    })
        
        return results
    
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()

