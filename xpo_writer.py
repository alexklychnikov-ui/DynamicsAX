#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для обновления XPO‑файлов по изменённым XPP‑методам.

Исходные XPO берутся из каталога `XPO/`, изменённый код методов
извлекается из файлов в каталоге `parserXPO/` и аккуратно
подставляется в блоки SOURCE/ENDSOURCE, не ломая структуру XPO.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class XPOWriter:
    """Записывает изменения из XPP‑файлов обратно в XPO."""

    def __init__(self, xpo_file_path: str, parser_dir: str = "parserXPO", xpo_encoding: str = "cp1251"):
        """
        Args:
            xpo_file_path: путь к исходному XPO‑файлу.
            parser_dir: каталог `parserXPO` с разобранными XPP‑файлами.
            xpo_encoding: кодировка XPO (обычно cp1251 для русской AX).
        """
        self.xpo_file_path = Path(xpo_file_path)
        self.parser_dir = Path(parser_dir)
        self.xpo_encoding = xpo_encoding
        
        if not self.xpo_file_path.exists():
            raise FileNotFoundError(f"XPO file not found: {xpo_file_path}")
        
        if not self.parser_dir.exists():
            raise FileNotFoundError(f"Parser directory not found: {parser_dir}")
    
    def write_back(self) -> Optional[Path]:
        """
        Обновляет XPO‑файл по изменённым XPP‑методам из каталога parserXPO.
        
        Returns:
            Путь к созданному файлу `<имя>_WR.xpo` или None, если изменений нет.
        """
        # Время модификации исходного XPO
        xpo_mtime = self.xpo_file_path.stat().st_mtime
        
        # Определяем фактическую кодировку XPO:
        # сначала пробуем UTF‑8, при ошибке откатываемся на CP1251.
        try:
            try:
                with open(self.xpo_file_path, 'r', encoding='utf-8') as f:
                    xpo_content = f.read()
                self.xpo_encoding = 'utf-8'
            except UnicodeDecodeError:
                with open(self.xpo_file_path, 'r', encoding='cp1251') as f:
                    xpo_content = f.read()
                self.xpo_encoding = 'cp1251'
        except FileNotFoundError:
            raise
        
        # Здесь будем накапливать новые версии элементов XPO
        element_replacements = {}  # element_key -> (element_info, updated_content)
        
        # Обходим подкаталоги в parserXPO (по одному на элемент)
        for element_dir in self.parser_dir.iterdir():
            if not element_dir.is_dir():
                continue
            
            element_name = element_dir.name
            
            # В каждом каталоге должен быть properties.txt с типом элемента
            props_file = element_dir / "properties.txt"
            if not props_file.exists():
                continue
            
            element_type = self._get_element_type(props_file)
            if not element_type:
                continue
            
            # Ищем соответствующий элемент в XPO по типу и имени
            element_info = self._find_element_in_xpo(xpo_content, element_name, element_type)
            if not element_info:
                print(f"ВНИМАНИЕ: элемент {element_type}:{element_name} не найден в XPO.")
                continue
            
            # Ключом делаем диапазон [start, end) элемента в XPO
            element_key = (element_info['start'], element_info['end'])
            
            # В одном элементе может быть несколько изменённых методов
            if element_key not in element_replacements:
                element_replacements[element_key] = {
                    'info': element_info,
                    'content': element_info['content'],
                    'methods': []
                }
            
            # [removed corrupted comment]
            for xpp_file in element_dir.glob("*.xpp"):
                method_name = xpp_file.stem
                
                # Пропускаем методы, которые не новее исходного XPO
                if not self._is_method_modified(xpp_file, xpo_mtime):
                    continue
                
                # Читаем XPP‑код метода: сначала пробуем UTF‑8, затем CP1251
                try:
                    try:
                        with open(xpp_file, 'r', encoding='utf-8') as f:
                            method_code = f.read()
                    except UnicodeDecodeError:
                        with open(xpp_file, 'r', encoding='cp1251') as f:
                            method_code = f.read()
                except Exception as e:
                    print(f"Ошибка чтения XPP‑файла {xpp_file}: {e}")
                    continue
                
                # Пытаемся заменить блок SOURCE/ENDSOURCE на новый код
                new_content = self._replace_source_in_content(
                    element_replacements[element_key]['content'],
                    method_name,
                    method_code
                )
                
                if new_content:
                    element_replacements[element_key]['content'] = new_content
                    element_replacements[element_key]['methods'].append(method_name)
                else:
                    # SOURCE для этого метода не найден в XPO
                    print(f"Не удалось обновить метод {method_name} в элементе {element_type}:{element_name}.")
        
        # Оставляем только элементы, для которых есть изменённые методы
        elements_with_updates = {
            k: v for k, v in element_replacements.items() 
            if v['methods']
        }
        
        if not elements_with_updates:
            print("Изменённых методов новее исходного XPO не найдено.")
            return None
        
        # Применяем замены с конца файла, чтобы не сдвигать позиции
        sorted_replacements = sorted(elements_with_updates.items(), 
                                     key=lambda x: x[0][0], reverse=True)
        
        updated_count = 0
        
        for element_key, replacement_data in sorted_replacements:
            element_info = replacement_data['info']
            new_content = replacement_data['content']
            methods = replacement_data['methods']
            
            start = element_info['start']
            end = element_info['end']
            
            # Вставляем обновлённый текст элемента в исходный контент
            xpo_content = xpo_content[:start] + new_content + xpo_content[end:]
            
            updated_count += len(methods)
            for method_name in methods:
                print(f"Обновлён метод {method_name} в элементе {element_info['type']}:{element_info['name']}.")
        
        # Имя выходного файла: <оригинал>_WR.xpo в том же каталоге
        output_file = self.xpo_file_path.parent / f"{self.xpo_file_path.stem}_WR.xpo"
        
        # Сохраняем XPO в той же кодировке, что и исходный
        with open(output_file, 'w', encoding=self.xpo_encoding, errors='ignore') as f:
            f.write(xpo_content)
        
        # Быстрая валидация структуры XPO
        if self._validate_xpo(output_file):
            print("\n" + "=" * 60)
            print("OK: файл сохранён: {}".format(output_file.name))
            print("  Полный путь: {}".format(output_file))
            print("  Обновлено методов: {}".format(updated_count))
            print("=" * 60)
            return output_file
        else:
            print("\n" + "=" * 60)
            print("ПРЕДУПРЕЖДЕНИЕ: структура XPO может быть некорректной.")
            print("  Файл сохранён: {}".format(output_file.name))
            print("  Полный путь: {}".format(output_file))
            print("=" * 60)
            return output_file
    
    def _get_element_type(self, props_file: Path) -> Optional[str]:
        """Возвращает тип элемента (CLS/TAB/JOB/FRM) из properties.txt."""
        try:
            with open(props_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('Type:'):
                        return line.split(':', 1)[1].strip()
        except Exception:
            pass
        return None
    
    def _find_element_in_xpo(self, content: str, element_name: str, element_type: str) -> Optional[Dict]:
        """
        Ищет фрагмент текста элемента в содержимом XPO.
        
        Returns:
            Словарь с данными элемента или None, если элемент не найден.
        """
        # Находим все ***Element: нужного типа
        element_pattern = rf'\*\*\*Element:\s*{element_type}'
        
        # [removed corrupted comment]
        for match in re.finditer(element_pattern, content):
            start_pos = match.start()
            # Берём содержимое элемента до следующего ***Element: или конца файла
            end_match = re.search(r'\*\*\*Element:', content[start_pos + 1:])
            if end_match:
                end_pos = start_pos + end_match.start()
            else:
                end_pos = len(content)
            
            element_content = content[start_pos:end_pos]
            
            # Внутри элемента проверяем, что это действительно нужный объект
            if element_type == 'JOB':
                # [removed corrupted comment]
                if re.search(rf'SOURCE\s+#{re.escape(element_name)}', element_content):
                    return {
                        'start': start_pos,
                        'end': end_pos,
                        'content': element_content,
                        'type': element_type,
                        'name': element_name
                    }
            elif element_type == 'CLS':
                if re.search(rf'CLASS\s+#{re.escape(element_name)}', element_content):
                    return {
                        'start': start_pos,
                        'end': end_pos,
                        'content': element_content,
                        'type': element_type,
                        'name': element_name
                    }
            elif element_type == 'TAB':
                if re.search(rf'TABLE\s+#{re.escape(element_name)}', element_content):
                    return {
                        'start': start_pos,
                        'end': end_pos,
                        'content': element_content,
                        'type': element_type,
                        'name': element_name
                    }
            elif element_type == 'FRM':
                if re.search(rf'FORM\s+#{re.escape(element_name)}', element_content):
                    return {
                        'start': start_pos,
                        'end': end_pos,
                        'content': element_content,
                        'type': element_type,
                        'name': element_name
                    }
        
        return None
    
    def _is_method_modified(self, xpp_file: Path, xpo_mtime: float) -> bool:
        """
        Проверяет, что XPP‑файл изменён позже, чем исходный XPO.
        
        Args:
            xpp_file: путь к файлу XPP.
            xpo_mtime: время модификации исходного XPO.
            
        Returns:
            True, если XPP новее XPO, иначе False.
        """
        xpp_mtime = xpp_file.stat().st_mtime
        return xpp_mtime > xpo_mtime
    
    def _format_code_for_xpo(self, code: str) -> str:
        """
        Форматирует код XPP для вставки в блок SOURCE XPO:
        каждая строка превращается в строку комментария, как ожидает AX.
        
        Args:
            code: исходный текст метода из XPP.
            
        Returns:
            Строка, готовая для вставки внутрь блока SOURCE.
        """
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Пустые строки заменяем на одиночный комментарий
            if not line.strip():
                formatted_lines.append('    #')
            else:
                # Непустые строки пишем как "    #<код>"
                formatted_lines.append(f'    #{line}')
        
        return '\n'.join(formatted_lines)
    
    def _replace_source_in_content(self, element_content: str, 
                                   method_name: str, method_code: str) -> Optional[str]:
        """
        Заменяет содержимое блока SOURCE/ENDSOURCE для указанного метода.
        
        Args:
            element_content: текст элемента XPO.
            method_name: имя метода (имя XPP‑файла без расширения).
            method_code: исходный код метода из XPP.
            
        Returns:
            Обновлённый текст элемента или None, если блок SOURCE не найден.
        """
        # Ищем блок SOURCE нужного метода
        source_pattern = rf'SOURCE\s+#{re.escape(method_name)}(.*?)ENDSOURCE'
        
        match = re.search(source_pattern, element_content, re.DOTALL)
        if not match:
            return None
        
        # Форматируем код под структуру XPO
        formatted_code = self._format_code_for_xpo(method_code)
        
        # Сохраняем исходные отступы перед SOURCE/ENDSOURCE
        old_source_content = match.group(0)
        source_indent = self._get_indent_before(old_source_content, 'SOURCE')
        endsource_indent = self._get_indent_before(old_source_content, 'ENDSOURCE')
        
        new_source_content = f'{source_indent}SOURCE #{method_name}\n{formatted_code}\n{endsource_indent}ENDSOURCE'
        
        # Подменяем старый блок SOURCE на новый
        new_element_content = element_content.replace(old_source_content, new_source_content)
        
        return new_element_content
    
    def _get_indent_before(self, text: str, marker: str) -> str:
        """
        Находит отступ (пробелы) перед строкой, содержащей marker.
        
        Args:
            text: исходный многострочный текст.
            marker: строка‑маркер (например, 'SOURCE').
            
        Returns:
            Строку с пробельным отступом (может быть пустой).
        """
        match = re.search(rf'^(\s*){re.escape(marker)}', text, re.MULTILINE)
        if match:
            return match.group(1)
        return '  '  # запасной отступ по умолчанию
    
    def _validate_xpo(self, xpo_file: Path) -> bool:
        """
        Простая проверка целостности получившегося XPO‑файла.
        
        Args:
            xpo_file: путь к XPO‑файлу.
            
        Returns:
            True, если структура выглядит корректной.
        """
        try:
            with open(xpo_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # [removed corrupted comment]
            if not content.startswith('Exportfile for AOT'):
                return False
            
            # [removed corrupted comment]
            if '***Element: END' not in content:
                return False
            
            # [removed corrupted comment]
            source_count = len(re.findall(r'SOURCE\s+#', content))
            endsource_count = len(re.findall(r'ENDSOURCE', content))
            if source_count != endsource_count:
                return False
            
            return True
        except Exception:
            return False


def main():
    """CLI‑обёртка для запуска XPOWriter из консоли."""
    import sys
    
    # Если XPO‑файл не передан в аргументах, пытаемся найти его в каталоге XPO
    if len(sys.argv) < 2:
        xpo_dir = Path("XPO")
        if xpo_dir.exists():
            xpo_files = list(xpo_dir.glob("*.xpo"))
            if xpo_files:
                print(f"Найдено XPO‑файлов в каталоге XPO: {len(xpo_files)}")
                for i, xpo_file in enumerate(xpo_files, 1):
                    print(f"  {i}. {xpo_file.name}")
                
                if len(xpo_files) == 1:
                    # Если файл один — берём его автоматически
                    xpo_file = str(xpo_files[0])
                    print(f"Используется XPO‑файл: {xpo_file}")
                else:
                    print("Укажите XPO‑файл явно: python xpo_writer.py <имя_файла.xpo> [каталог_parserXPO]")
                    print("Доступно несколько файлов в каталоге XPO.")
                    sys.exit(1)
            else:
                print("В каталоге XPO не найдено файлов с расширением .xpo.")
                print("Использование: python xpo_writer.py <имя_файла.xpo> [каталог_parserXPO]")
                print(f"Текущий каталог XPO: {xpo_dir.resolve()}")
                sys.exit(1)
        else:
            print("Каталог XPO не найден.")
            print("Использование: python xpo_writer.py <имя_файла.xpo> [каталог_parserXPO]")
            sys.exit(1)
    else:
        xpo_file = sys.argv[1]
    
    parser_dir = sys.argv[2] if len(sys.argv) > 2 else "parserXPO"
    
    try:
        writer = XPOWriter(xpo_file, parser_dir)
        
        print("Запуск записи изменений XPP обратно в XPO.")
        print(f"Исходный XPO: {xpo_file}")
        print(f"Каталог parserXPO: {parser_dir}")
        print("-" * 60)
        
        output_file = writer.write_back()
        
        if output_file:
            print(f"\nГотово: XPO‑файл успешно обновлён.")
        else:
            print(f"\nНет изменений для записи в XPO.")
            
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка при обновлении XPO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
