#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для парсинга XPO файлов Microsoft Dynamics AX
Создает структурированное представление объектов AOT в папке parserXPO
"""

import re
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


class XPOParser:
    def __init__(self, xpo_file_path: str, output_dir: str = "parserXPO"):
        self.xpo_file_path = Path(xpo_file_path)
        self.output_dir = Path(output_dir)
        self.objects = {}  # Хранит все объекты (классы, таблицы, формы)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def is_object_parsed(self, object_name: str) -> bool:
        """Проверяет, распарсен ли уже объект (существует ли его директория)"""
        object_dir = self.output_dir / object_name
        if not object_dir.exists():
            return False
        
        # Проверяем, что в директории есть хотя бы один файл метода
        method_files = list(object_dir.glob("*.xpp"))
        return len(method_files) > 0
    
    def clear_output_dir(self):
        """Очищает папку parserXPO перед парсингом (используется только при явном вызове)"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            print(f"Очищена папка: {self.output_dir}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def parse(self):
        """Парсит XPO файл и извлекает все элементы. При сохранении новые методы добавляются в папки объектов."""
        # XPO из русской AX обычно в CP1251, поэтому сначала пробуем её,
        # а при неудаче откатываемся на UTF‑8.
        try:
            try:
                with open(self.xpo_file_path, 'r', encoding='cp1251') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(self.xpo_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
        except FileNotFoundError:
            raise
        
        # Находим все элементы
        element_pattern = r'\*\*\*Element:\s*(\w+)'
        elements = list(re.finditer(element_pattern, content))
        
        parsed_count = 0
        
        for i, element_match in enumerate(elements):
            element_type = element_match.group(1)
            start_pos = element_match.start()
            end_pos = elements[i + 1].start() if i + 1 < len(elements) else len(content)
            element_content = content[start_pos:end_pos]
            
            # Парсим элемент (всегда); при сохранении новые методы добавятся, существующие не перезапишутся
            if element_type == 'CLS':
                self._parse_class(element_content)
                parsed_count += 1
            elif element_type in ('TAB', 'DBT'):
                self._parse_table(element_content, element_type)
                parsed_count += 1
            elif element_type == 'FRM':
                self._parse_form(element_content)
                parsed_count += 1
            elif element_type == 'JOB':
                self._parse_job(element_content)
                parsed_count += 1
        
        if parsed_count > 0:
            print(f"Распарсено объектов: {parsed_count}")
    
    def _parse_class(self, content: str):
        """Парсит класс из XPO"""
        # Извлекаем имя класса
        class_match = re.search(r'CLASS\s+#(\w+)', content)
        if not class_match:
            return
        
        object_name = class_match.group(1)
        
        # Извлекаем свойства класса
        properties = {}
        props_match = re.search(r'PROPERTIES(.*?)ENDPROPERTIES', content, re.DOTALL)
        if props_match:
            props_text = props_match.group(1)
            # Извлекаем Extends если есть
            extends_match = re.search(r'Extends\s+#(\w+)', props_text)
            if extends_match:
                properties['extends'] = extends_match.group(1)
        
        # Извлекаем все методы только из блока METHODS...ENDMETHODS
        methods = {}
        methods_block_match = re.search(r'METHODS(.*?)ENDMETHODS', content, re.DOTALL)
        if methods_block_match:
            methods_content = methods_block_match.group(1)
            source_pattern = r'SOURCE\s+#(\w+)(.*?)ENDSOURCE'
            for method_match in re.finditer(source_pattern, methods_content, re.DOTALL):
                method_name = method_match.group(1)
                method_code = method_match.group(2)
                # Убираем префикс # из каждой строки кода
                cleaned_code = self._clean_code(method_code)
                methods[method_name] = cleaned_code
        
        self.objects[object_name] = {
            'type': 'CLS',
            'properties': properties,
            'methods': methods
        }
    
    def _parse_table(self, content: str, element_type: str = 'TAB'):
        """Парсит таблицу из XPO (element_type: TAB или DBT)."""
        table_match = re.search(r'TABLE\s+#(\w+)', content)
        if not table_match:
            return
        
        object_name = table_match.group(1)
        
        properties = {}
        props_match = re.search(r'PROPERTIES(.*?)ENDPROPERTIES', content, re.DOTALL)
        if props_match:
            props_text = props_match.group(1)
        
        methods = {}
        methods_block_match = re.search(r'METHODS(.*?)ENDMETHODS', content, re.DOTALL)
        if methods_block_match:
            methods_content = methods_block_match.group(1)
            source_pattern = r'SOURCE\s+#(\w+)(.*?)ENDSOURCE'
            for method_match in re.finditer(source_pattern, methods_content, re.DOTALL):
                method_name = method_match.group(1)
                method_code = method_match.group(2)
                cleaned_code = self._clean_code(method_code)
                methods[method_name] = cleaned_code
        
        self.objects[object_name] = {
            'type': element_type,
            'properties': properties,
            'methods': methods
        }
    
    def _parse_form(self, content: str):
        """Парсит форму из XPO"""
        # Извлекаем имя формы
        form_match = re.search(r'FORM\s+#(\w+)', content)
        if not form_match:
            return
        
        object_name = form_match.group(1)
        
        # Извлекаем свойства формы
        properties = {}
        props_match = re.search(r'PROPERTIES(.*?)ENDPROPERTIES', content, re.DOTALL)
        if props_match:
            props_text = props_match.group(1)
        
        # Извлекаем все методы только из блока METHODS...ENDMETHODS
        methods = {}
        methods_block_match = re.search(r'METHODS(.*?)ENDMETHODS', content, re.DOTALL)
        if methods_block_match:
            methods_content = methods_block_match.group(1)
            source_pattern = r'SOURCE\s+#(\w+)(.*?)ENDSOURCE'
            for method_match in re.finditer(source_pattern, methods_content, re.DOTALL):
                method_name = method_match.group(1)
                method_code = method_match.group(2)
                cleaned_code = self._clean_code(method_code)
                methods[method_name] = cleaned_code
        
        self.objects[object_name] = {
            'type': 'FRM',
            'properties': properties,
            'methods': methods
        }
    
    def _parse_job(self, content: str):
        """Парсит Job из XPO"""
        # Извлекаем имя Job из первого SOURCE
        source_match = re.search(r'SOURCE\s+#(\w+)', content)
        if not source_match:
            return
        
        object_name = source_match.group(1)
        
        # Извлекаем свойства Job
        properties = {}
        props_match = re.search(r'PROPERTIES(.*?)ENDPROPERTIES', content, re.DOTALL)
        if props_match:
            props_text = props_match.group(1)
            # Извлекаем Origin если есть
            origin_match = re.search(r'Origin\s+#\{([^}]+)\}', props_text)
            if origin_match:
                properties['origin'] = origin_match.group(1)
        
        # Извлекаем все методы
        methods = {}
        source_pattern = r'SOURCE\s+#(\w+)(.*?)ENDSOURCE'
        for method_match in re.finditer(source_pattern, content, re.DOTALL):
            method_name = method_match.group(1)
            method_code = method_match.group(2)
            cleaned_code = self._clean_code(method_code)
            methods[method_name] = cleaned_code
        
        self.objects[object_name] = {
            'type': 'JOB',
            'properties': properties,
            'methods': methods
        }
    
    def _clean_code(self, code: str) -> str:
        """Убирает префикс # из начала строк и нормализует ведущие отступы
        
        Делает так, чтобы первая непустая строка метода начиналась с колонки 0,
        а относительная вложенность остальных строк сохранялась.
        """
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Убираем префикс # если есть
            if line.strip().startswith('#'):
                line = line.replace('#', '', 1)
            cleaned_lines.append(line)
        
        # Определяем минимальный общий отступ среди непустых строк
        indent_levels = []
        for line in cleaned_lines:
            if not line.strip():
                continue
            leading_ws_len = len(line) - len(line.lstrip(' \t'))
            if leading_ws_len > 0:
                indent_levels.append(leading_ws_len)
        
        min_indent = min(indent_levels) if indent_levels else 0
        
        # Сдвигаем все строки влево на общий минимальный отступ
        if min_indent > 0:
            normalized_lines = []
            for line in cleaned_lines:
                if not line.strip():
                    normalized_lines.append('')
                else:
                    normalized_lines.append(line[min_indent:])
        else:
            normalized_lines = cleaned_lines
        
        result = '\n'.join(normalized_lines)
        return result.strip()
    
    def save_structured(self, overwrite: bool = False):
        """Сохраняет объекты в структурированном виде: директория для каждого объекта, файл для каждого метода
        
        Args:
            overwrite: Если True, перезаписывает существующие файлы методов
        """
        saved_count = 0
        skipped_count = 0
        
        for object_name, object_data in self.objects.items():
            # Создаем директорию для объекта
            object_dir = self.output_dir / object_name
            object_dir.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем свойства объекта (если есть)
            if object_data['properties']:
                props_file = object_dir / "properties.txt"
                # Перезаписываем properties.txt всегда, так как они могут измениться
                with open(props_file, 'w', encoding='utf-8') as f:
                    f.write(f"Type: {object_data['type']}\n")
                    for key, value in object_data['properties'].items():
                        f.write(f"{key}: {value}\n")
            
            # Сохраняем каждый метод в отдельный файл
            methods = object_data['methods']
            methods_saved = 0
            methods_skipped = 0
            
            for method_name, method_code in methods.items():
                if method_code.strip():  # Сохраняем только непустые методы
                    method_file = object_dir / f"{method_name}.xpp"
                    
                    # Пропускаем существующие файлы если не перезаписываем
                    if not overwrite and method_file.exists():
                        methods_skipped += 1
                        continue
                    
                    with open(method_file, 'w', encoding='utf-8') as f:
                        f.write(method_code)
                    methods_saved += 1
            
            if methods_saved > 0:
                print(f"Сохранен объект {object_data['type']}: {object_name} ({methods_saved} методов сохранено" + 
                      (f", {methods_skipped} пропущено" if methods_skipped > 0 else "") + ")")
                saved_count += 1
            elif methods_skipped > 0:
                skipped_count += 1
        
        if skipped_count > 0:
            print(f"Пропущено объектов (уже существуют): {skipped_count}")


def main():
    """Основная функция для запуска парсера"""
    import sys
    
    def process_file(xpo_file: str, output_dir: str, force: bool):
        parser = XPOParser(xpo_file, output_dir)
        
        print(f"Парсинг файла: {xpo_file}")
        print(f"Выходная папка: {output_dir}")
        if force:
            print("Режим: перезапись всех файлов методов")
        else:
            print("Режим: добавление только новых методов (существующие .xpp не перезаписываются)")
        print("-" * 60)
        
        parser.parse()
        
        print(f"\nОбработано объектов: {len(parser.objects)}")
        for obj_name, obj_data in parser.objects.items():
            print(f"  - {obj_data['type']}: {obj_name} ({len(obj_data['methods'])} методов)")
        
        if parser.objects:
            parser.save_structured(overwrite=force)
        
        print("\nПарсинг завершен!")
    
    # Извлекаем флаги из аргументов
    force = '--force' in sys.argv
    args_without_flags = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    # Если аргументы не указаны, ищем XPO файлы в папке XPO
    if len(args_without_flags) == 0:
        xpo_dir = Path("XPO")
        if xpo_dir.exists():
            xpo_files = [p for p in xpo_dir.glob("*.xpo") if not p.name.endswith("_WR.xpo")]
            if xpo_files:
                print(f"Найдено XPO файлов в папке XPO: {len(xpo_files)}")
                for i, xpo_file in enumerate(xpo_files, 1):
                    print(f"  {i}. {xpo_file.name}")
                
                if len(xpo_files) == 1:
                    xpo_file = str(xpo_files[0])
                    print(f"\nИспользуется файл: {xpo_file}")
                    selected_files = [xpo_file]
                else:
                    print("\n0. Все файлы")
                    while True:
                        try:
                            choice = input("\nУкажите номер файла для обработки (0 - все файлы): ").strip()
                        except (EOFError, KeyboardInterrupt):
                            print("\nОперация отменена.")
                            sys.exit(1)
                        
                        if not choice.isdigit():
                            print("Введите число от 0 до", len(xpo_files))
                            continue
                        
                        choice_num = int(choice)
                        if choice_num < 0 or choice_num > len(xpo_files):
                            print("Введите число от 0 до", len(xpo_files))
                            continue
                        
                        break
                    
                    if choice_num == 0:
                        selected_files = [str(p) for p in xpo_files]
                        print("\nБудут обработаны все файлы.")
                    else:
                        xpo_file = str(xpo_files[choice_num - 1])
                        print(f"\nИспользуется файл: {xpo_file}")
                        selected_files = [xpo_file]
            else:
                print("Использование: python xpo_parser.py <путь_к_xpo_файлу> [папка_вывода] [--force]")
                print("По умолчанию используется папка: parserXPO")
                print("Опции:")
                print("  --force  Перезаписывает существующие объекты")
                print(f"\nВ папке XPO не найдено .xpo файлов")
                sys.exit(1)
        else:
            print("Использование: python xpo_parser.py <путь_к_xpo_файлу> [папка_вывода] [--force]")
            print("По умолчанию используется папка: parserXPO")
            print("Опции:")
            print("  --force  Перезаписывает существующие объекты")
            sys.exit(1)
    else:
        xpo_file = args_without_flags[0]
        selected_files = [xpo_file]
    
    output_dir = args_without_flags[1] if len(args_without_flags) > 1 else "parserXPO"
    
    for xpo_file in selected_files:
        process_file(xpo_file, output_dir, force)


if __name__ == "__main__":
    main()

