#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite индексатор для полнотекстового поиска в XPO файлах
Создает базу данных с индексацией всех элементов из XPO файла
"""
import re
import sqlite3
from pathlib import Path
from typing import Dict, List


class XPOSQLiteIndexer:
    def __init__(self, xpo_file_path: str, db_file: str = "xpo_index.db"):
        self.xpo_file_path = Path(xpo_file_path)
        self.db_file = Path(db_file)
        self.conn = None
    
    def create_database(self):
        """Создает структуру базы данных"""
        if self.db_file.exists():
            print(f"Удаление существующей базы данных: {self.db_file}")
            self.db_file.unlink()
        
        self.conn = sqlite3.connect(self.db_file)
        cursor = self.conn.cursor()
        
        # Таблица элементов
        cursor.execute("""
            CREATE TABLE elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_type TEXT NOT NULL,
                element_name TEXT NOT NULL,
                file_position INTEGER,
                size INTEGER,
                method_count INTEGER DEFAULT 0,
                UNIQUE(element_type, element_name)
            )
        """)
        
        # Таблица методов
        cursor.execute("""
            CREATE TABLE methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_id INTEGER,
                method_name TEXT NOT NULL,
                FOREIGN KEY (element_id) REFERENCES elements(id)
            )
        """)
        
        # Индексы для быстрого поиска
        cursor.execute("CREATE INDEX idx_element_type ON elements(element_type)")
        cursor.execute("CREATE INDEX idx_element_name ON elements(element_name)")
        cursor.execute("CREATE INDEX idx_method_name ON methods(method_name)")
        cursor.execute("CREATE INDEX idx_element_id ON methods(element_id)")
        
        # Полнотекстовый поиск (FTS5)
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE elements_fts USING fts5(
                    element_name,
                    element_type,
                    methods,
                    content='elements',
                    content_rowid='id'
                )
            """)
        except sqlite3.OperationalError as e:
            if "fts5" in str(e).lower():
                print("Внимание: FTS5 не доступен, создаю без полнотекстового поиска")
            else:
                raise
        
        self.conn.commit()
        print(f"База данных создана: {self.db_file}")
    
    def index_file(self):
        """Индексирует XPO файл"""
        print(f"Индексация файла: {self.xpo_file_path}")
        
        if not self.xpo_file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {self.xpo_file_path}")
        
        element_pattern = re.compile(r'^\*\*\*Element:\s*(\w+)', re.MULTILINE)
        
        print("Чтение файла...")
        with open(self.xpo_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        file_size_mb = len(content) / 1024 / 1024
        print(f"Размер файла: {file_size_mb:.2f} MB")
        
        elements = list(element_pattern.finditer(content))
        total = len(elements)
        print(f"Найдено элементов: {total}")
        
        cursor = self.conn.cursor()
        
        # Проверяем наличие FTS5
        has_fts5 = False
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='elements_fts'")
            has_fts5 = cursor.fetchone() is not None
        except:
            pass
        
        processed = 0
        skipped = 0
        
        for i, element_match in enumerate(elements):
            if i % 100 == 0 and i > 0:
                progress = (i / total) * 100
                print(f"Обработано: {i}/{total} ({progress:.1f}%)")
                self.conn.commit()
            
            element_type = element_match.group(1)
            start_pos = element_match.start()
            end_pos = elements[i + 1].start() if i + 1 < len(elements) else len(content)
            
            # Извлекаем контекст элемента (первые 10000 символов для анализа)
            element_content = content[start_pos:min(start_pos + 10000, end_pos)]
            element_name = self._extract_element_name(element_type, element_content)
            
            if not element_name:
                skipped += 1
                continue
            
            methods = []
            if element_type in ['CLS', 'TAB', 'FRM']:
                methods = self._extract_methods(element_content)
            
            try:
                # Вставляем элемент
                cursor.execute("""
                    INSERT INTO elements (element_type, element_name, file_position, size, method_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (element_type, element_name, start_pos, end_pos - start_pos, len(methods)))
                
                element_id = cursor.lastrowid
                
                # Вставляем методы
                for method_name in methods:
                    cursor.execute("""
                        INSERT INTO methods (element_id, method_name)
                        VALUES (?, ?)
                    """, (element_id, method_name))
                
                # Обновляем FTS индекс если доступен
                if has_fts5:
                    methods_str = " ".join(methods)
                    cursor.execute("""
                        INSERT INTO elements_fts (rowid, element_name, element_type, methods)
                        VALUES (?, ?, ?, ?)
                    """, (element_id, element_name, element_type, methods_str))
                
                processed += 1
                
            except sqlite3.IntegrityError:
                # Пропускаем дубликаты
                skipped += 1
                continue
        
        self.conn.commit()
        print(f"\nИндексация завершена!")
        print(f"Обработано элементов: {processed}")
        print(f"Пропущено: {skipped}")
    
    def _extract_element_name(self, element_type: str, content: str) -> str:
        """Извлекает имя элемента в зависимости от типа"""
        patterns = {
            'CLS': r'CLASS\s+#(\w+)',
            'TAB': r'TABLE\s+#(\w+)',
            'FRM': r'FORM\s+#(\w+)',
            'MCR': r'MACRO\s+#(\w+)',
            'ENU': r'ENUM\s+#(\w+)',
            'EDT': r'EDT\s+#(\w+)',
            'SPV': r'PRIVILEGE\s+#(\w+)',
            'JOB': r'JOB\s+#(\w+)',
            'MAP': r'MAP\s+#(\w+)',
            'QTY': r'QUERY\s+#(\w+)',
        }
        
        pattern = patterns.get(element_type)
        if pattern:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # Для других типов пробуем найти имя в PROPERTIES
        name_match = re.search(r'Name\s+#(\w+)', content)
        if name_match:
            return name_match.group(1)
        
        # Пробуем найти в первой строке после Element
        first_line_match = re.search(r'^\s*(\w+)\s+#(\w+)', content, re.MULTILINE)
        if first_line_match:
            return first_line_match.group(2)
        
        return None
    
    def _extract_methods(self, content: str) -> List[str]:
        """Извлекает список методов из элемента"""
        # Ищем SOURCE #MethodName
        methods = re.findall(r'SOURCE\s+#(\w+)', content)
        return sorted(list(set(methods)))  # Убираем дубликаты и сортируем
    
    def get_statistics(self) -> dict:
        """Возвращает статистику по индексу"""
        if not self.conn:
            return {}
        
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Общее количество элементов
        cursor.execute("SELECT COUNT(*) FROM elements")
        stats["total_elements"] = cursor.fetchone()[0]
        
        # По типам
        cursor.execute("""
            SELECT element_type, COUNT(*) 
            FROM elements 
            GROUP BY element_type 
            ORDER BY COUNT(*) DESC
        """)
        stats["by_type"] = dict(cursor.fetchall())
        
        # Общее количество методов
        cursor.execute("SELECT COUNT(*) FROM methods")
        stats["total_methods"] = cursor.fetchone()[0]
        
        # Элементы с методами
        cursor.execute("""
            SELECT COUNT(*) 
            FROM elements 
            WHERE method_count > 0
        """)
        stats["elements_with_methods"] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Закрывает соединение"""
        if self.conn:
            self.conn.close()
            print("Соединение с базой данных закрыто")


def main():
    import sys
    
    # Путь к XPO файлу относительно корня проекта
    xpo_file = "../AOT_cus/PrivateProject_CUS_Layer_Export.xpo"
    if len(sys.argv) > 1:
        xpo_file = sys.argv[1]
    
    # База данных в текущей папке
    db_file = "xpo_index.db"
    if len(sys.argv) > 2:
        db_file = sys.argv[2]
    
    # Преобразуем в абсолютные пути
    script_dir = Path(__file__).parent
    xpo_path = (script_dir / xpo_file).resolve()
    db_path = script_dir / db_file
    
    print(f"Скрипт индексации XPO файла")
    print(f"XPO файл: {xpo_path}")
    print(f"База данных: {db_path}")
    print("-" * 60)
    
    indexer = XPOSQLiteIndexer(str(xpo_path), str(db_path))
    
    try:
        indexer.create_database()
        indexer.index_file()
        
        # Выводим статистику
        stats = indexer.get_statistics()
        print("\n" + "=" * 60)
        print("СТАТИСТИКА ИНДЕКСА:")
        print("=" * 60)
        print(f"Всего элементов: {stats.get('total_elements', 0)}")
        print(f"Всего методов: {stats.get('total_methods', 0)}")
        print(f"Элементов с методами: {stats.get('elements_with_methods', 0)}")
        print("\nПо типам:")
        for elem_type, count in sorted(stats.get('by_type', {}).items(), key=lambda x: x[1], reverse=True):
            print(f"  {elem_type}: {count}")
        
        db_size_mb = db_path.stat().st_size / 1024 / 1024
        print(f"\nРазмер базы данных: {db_size_mb:.2f} MB")
        
    except Exception as e:
        print(f"\nОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    finally:
        indexer.close()


if __name__ == "__main__":
    main()

