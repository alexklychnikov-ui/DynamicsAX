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
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def _no_input_env() -> bool:
    ci = os.environ.get("CI", "").strip().lower()
    if ci in ("1", "true", "yes"):
        return True
    v = os.environ.get("XPO_NO_INPUT", "").strip().lower()
    return v in ("1", "true", "yes")


class XPOWriter:
    """Записывает изменения из XPP‑файлов обратно в XPO."""

    def __init__(
        self,
        xpo_file_path: str,
        parser_dir: str = "parserXPO",
        xpo_encoding: str = "cp1251",
        force: bool = False,
        no_input: bool = False,
    ):
        """
        Args:
            xpo_file_path: путь к исходному XPO‑файлу.
            parser_dir: каталог `parserXPO` с разобранными XPP‑файлами.
            xpo_encoding: кодировка XPO (обычно cp1251 для русской AX).
            force: если True, не проверять даты — считать все XPP новее XPO.
            no_input: без интерактивных запросов (пропуск добавления элемента по шаблону).
        """
        self.xpo_file_path = Path(xpo_file_path).resolve()
        self.parser_dir = Path(parser_dir).resolve()
        self.xpo_encoding = xpo_encoding
        self.xpo_newline = "\n"
        self.force = force
        self.no_input = no_input
        
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
        
        raw = self.xpo_file_path.read_bytes()
        xpo_content, self.xpo_encoding, self.xpo_newline = self._decode_xpo_content(raw)
        xpo_content = self._normalize_newlines(xpo_content)
        
        # Здесь будем накапливать новые версии элементов XPO
        element_replacements = {}  # element_key -> (element_info, updated_content)
        new_elements_to_add = []  # блоки новых элементов для вставки в шаблон

        # Обходим подкаталоги в parserXPO (по одному на элемент)
        for element_dir in self.parser_dir.iterdir():
            if not element_dir.is_dir():
                continue
            
            element_name = element_dir.name
            
            props_file = element_dir / "properties.txt"
            if props_file.exists():
                element_type = self._get_element_type(props_file)
            else:
                element_type = self._infer_element_type_from_xpo(xpo_content, element_name)
                if not element_type and list(element_dir.glob("*.xpp")):
                    print("ВНИМАНИЕ: в каталоге {} нет properties.txt и элемент не найден в XPO — пропуск.".format(element_name))
            if not element_type:
                continue

            # Класс/таблица и т.д. лежат в своём XPO: Class_<Name>.xpo, если такой файл есть.
            # Если ожидаемого XPO нет (один общий SharedProject.xpo) — ищем элемент в текущем файле.
            expected_xpo = self._expected_xpo_for_element(element_type, element_name)
            if expected_xpo is not None and expected_xpo.exists() and self.xpo_file_path.resolve() != expected_xpo.resolve():
                continue

            # Ищем соответствующий элемент в XPO по типу и имени
            element_info = self._find_element_in_xpo(xpo_content, element_name, element_type)
            if not element_info:
                print("ВНИМАНИЕ: элемент {}:{} не найден в XPO.".format(element_type, element_name))
                if self.no_input:
                    print("no-input: пропуск добавления по шаблону.")
                    continue
                try:
                    ans = input("Найден элемент {}:{}. Добавить его в шаблон? (0 = нет, иначе да): ".format(element_type, element_name)).strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nПропуск.")
                    continue
                if ans == "0":
                    continue
                if element_type not in self._TEMPLATE_TYPES:
                    print("Тип {} не поддерживается для добавления по шаблону. Пропуск.".format(element_type))
                    continue
                template_info = self._find_any_element_of_type(xpo_content, element_type)
                if not template_info:
                    print("В шаблоне XPO не найден элемент типа {} для копирования. Пропуск.".format(element_type))
                    continue
                new_block = self._build_new_element_block(
                    template_info['content'], element_type, element_name, element_dir
                )
                if not new_block:
                    print("Не удалось собрать блок для {}:{}. Пропуск.".format(element_type, element_name))
                    continue
                new_elements_to_add.append(new_block)
                print("Элемент {}:{} будет добавлен в XPO по шаблону {}.".format(element_type, element_name, template_info['name']))
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
                
                if not self.force and not self._is_method_modified(xpp_file, xpo_mtime):
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
                    print("Ошибка чтения XPP-файла {}: {}".format(xpp_file, e))
                    continue
                
                existing_block = self._get_existing_source_block(
                    element_replacements[element_key]['content'], method_name)
                if existing_block and self._method_codes_equal(existing_block, method_code):
                    continue
                
                new_content = self._replace_source_in_content(
                    element_replacements[element_key]['content'],
                    method_name,
                    method_code
                )
                if not new_content and element_type in ('CLS', 'TAB', 'DBT'):
                    new_content = self._insert_new_source_block(
                        element_replacements[element_key]['content'],
                        method_name,
                        method_code
                    )
                if new_content:
                    element_replacements[element_key]['content'] = new_content
                    element_replacements[element_key]['methods'].append(method_name)
                else:
                    print("Не удалось обновить метод {} в элементе {}:{}.".format(method_name, element_type, element_name))
        
        # Оставляем только элементы, для которых есть изменённые методы
        elements_with_updates = {
            k: v for k, v in element_replacements.items()
            if v['methods']
        }

        if not elements_with_updates and not new_elements_to_add:
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
                print("Обновлен метод {} в элементе {}:{}.".format(method_name, element_info['type'], element_info['name']))

        for new_block in new_elements_to_add:
            end_marker = '***Element: END'
            pos = xpo_content.find(end_marker)
            if pos >= 0:
                xpo_content = xpo_content[:pos] + new_block + '\n\n' + end_marker + xpo_content[pos + len(end_marker):]
            else:
                xpo_content = xpo_content.rstrip() + '\n\n' + new_block + '\n'

        xpo_content = self._ensure_cls_endclass(xpo_content)

        # Имя выходного файла: <оригинал>_WR.xpo в том же каталоге
        output_file = self.xpo_file_path.parent / f"{self.xpo_file_path.stem}_WR.xpo"
        
        # Сохраняем XPO в исходной кодировке и с исходными переносами
        output_content = self._apply_newline_style(xpo_content, self.xpo_newline)
        with open(output_file, 'w', encoding=self.xpo_encoding, newline='') as f:
            f.write(output_content)
        
        # Быстрая валидация структуры XPO
        if self._validate_xpo(output_file):
            print("\n" + "=" * 60)
            print("OK: файл сохранён: {}".format(output_file.name))
            print("  Полный путь: {}".format(output_file))
            print("  Обновлено методов: {}".format(updated_count))
            if new_elements_to_add:
                print("  Добавлено новых элементов: {}".format(len(new_elements_to_add)))
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
            try:
                with open(props_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('Type:'):
                            return line.split(':', 1)[1].strip()
            except UnicodeDecodeError:
                with open(props_file, 'r', encoding='cp1251') as f:
                    for line in f:
                        if line.startswith('Type:'):
                            return line.split(':', 1)[1].strip()
        except Exception:
            pass
        return None

    def _infer_element_type_from_xpo(self, content: str, element_name: str) -> Optional[str]:
        """Если properties.txt нет — определяет тип по наличию элемента в XPO (TAB/DBT, CLS, FRM, JOB)."""
        for try_type in ('TAB', 'DBT', 'CLS', 'FRM', 'JOB'):
            if self._find_element_in_xpo(content, element_name, try_type):
                return try_type
        return None
    
    def _expected_xpo_for_element(self, element_type: str, element_name: str) -> Optional[Path]:
        """
        Путь к XPO-файлу, где должен лежать элемент (по соглашению об именах в XPO/).
        Если элемент не привязан к одному файлу — возвращает None (ищем в текущем XPO).
        """
        if element_type == "CLS":
            return (self.xpo_file_path.parent / ("Class_" + element_name + ".xpo")).resolve()
        if element_type in ("TAB", "DBT"):
            return (self.xpo_file_path.parent / ("Table_" + element_name + ".xpo")).resolve()
        if element_type == "FRM":
            return (self.xpo_file_path.parent / ("Form_" + element_name + ".xpo")).resolve()
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
                if re.search(rf'^\s*CLASS\s+#{re.escape(element_name)}\s*$', element_content, re.MULTILINE | re.IGNORECASE):
                    return {
                        'start': start_pos,
                        'end': end_pos,
                        'content': element_content,
                        'type': element_type,
                        'name': element_name
                    }
            elif element_type in ('TAB', 'DBT'):
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

    # Типы элементов, для которых можно взять шаблон из XPO (дублировать блок)
    _TEMPLATE_TYPES = ('LS', 'TAB', 'DBT', 'FRM', 'JOB', 'MCR', 'ENU', 'EDT', 'SPV', 'MAP', 'QTY', 'CLS')

    def _find_any_element_of_type(self, content: str, element_type: str) -> Optional[Dict]:
        """
        Находит в XPO первый элемент указанного типа (любое имя).
        Returns: словарь {start, end, content, type, name} или None.
        """
        element_pattern = rf'\*\*\*Element:\s*{re.escape(element_type)}\s'
        match = re.search(element_pattern, content)
        if not match:
            return None
        start_pos = match.start()
        end_match = re.search(r'\*\*\*Element:', content[start_pos + 1:])
        end_pos = start_pos + end_match.start() if end_match else len(content)
        element_content = content[start_pos:end_pos]
        template_name = None
        if element_type == 'CLS':
            m = re.search(r'CLASS\s+#(\S+)', element_content)
            if m:
                template_name = m.group(1)
        elif element_type == 'JOB':
            m = re.search(r'SOURCE\s+#(\S+)', element_content)
            if m:
                template_name = m.group(1)
        elif element_type == 'TAB':
            m = re.search(r'TABLE\s+#(\S+)', element_content)
            if m:
                template_name = m.group(1)
        elif element_type == 'FRM':
            m = re.search(r'FORM\s+#(\S+)', element_content)
            if m:
                template_name = m.group(1)
        else:
            for prefix in ('SOURCE #', 'NAME #', 'ENUM #', 'EDT #', 'MAP #'):
                m = re.search(rf'{re.escape(prefix)}(\S+)', element_content)
                if m:
                    template_name = m.group(1)
                    break
        if not template_name:
            return None
        return {
            'start': start_pos, 'end': end_pos, 'content': element_content,
            'type': element_type, 'name': template_name
        }

    def _read_xpp_content(self, xpp_file: Path) -> str:
        try:
            try:
                with open(xpp_file, 'r', encoding='utf-8') as f:
                    return self._normalize_newlines(f.read())
            except UnicodeDecodeError:
                with open(xpp_file, 'r', encoding='cp1251') as f:
                    return self._normalize_newlines(f.read())
        except Exception:
            return ''

    def _decode_xpo_content(self, raw: bytes) -> Tuple[str, str, str]:
        """Декодирует XPO и возвращает (text, encoding, newline_style)."""
        newline_style = '\r\n' if b'\r\n' in raw else ('\r' if b'\r' in raw else '\n')

        if raw.startswith(b'\xef\xbb\xbf'):
            return raw.decode('utf-8-sig'), 'utf-8-sig', newline_style
        if raw.startswith(b'\xff\xfe'):
            return raw.decode('utf-16-le'), 'utf-16-le', newline_style
        if raw.startswith(b'\xfe\xff'):
            return raw.decode('utf-16-be'), 'utf-16-be', newline_style

        try:
            return raw.decode('utf-8'), 'utf-8', newline_style
        except UnicodeDecodeError:
            pass

        try:
            return raw.decode('cp1251'), 'cp1251', newline_style
        except UnicodeDecodeError:
            return raw.decode('utf-8', errors='replace'), 'utf-8', newline_style

    def _ensure_cls_endclass(self, content: str) -> str:
        """В элементе CLS после ENDMETHODS AX ожидает ENDCLASS до следующего ***Element:"""
        pos = 0
        chunks = []
        while True:
            m = re.search(r'\*\*\*Element:\s*CLS\s', content[pos:])
            if not m:
                chunks.append(content[pos:])
                return ''.join(chunks)
            abs_start = pos + m.start()
            chunks.append(content[pos:abs_start])
            tail = content[abs_start:]
            next_el = re.search(r'\n\*\*\*Element:\s*', tail)
            if not next_el:
                block = tail
                pos = len(content)
            else:
                block = tail[: next_el.start() + 1]
                pos = abs_start + next_el.start() + 1
            if re.search(r'^\s*ENDMETHODS\s*$', block, re.MULTILINE) and not re.search(
                r'^\s*ENDCLASS\s*$', block, re.MULTILINE
            ):
                block = re.sub(
                    r'^(\s*ENDMETHODS)(\s*\n)',
                    r'\1\2  ENDCLASS\2',
                    block,
                    count=1,
                    flags=re.MULTILINE,
                )
            chunks.append(block)

    def _normalize_newlines(self, text: str) -> str:
        return text.replace('\r\n', '\n').replace('\r', '\n')

    def _apply_newline_style(self, text: str, newline_style: str) -> str:
        if newline_style == '\n':
            return text
        return text.replace('\n', newline_style)

    def _build_new_element_block(self, template_content: str, element_type: str,
                                  element_name: str, element_dir: Path) -> Optional[str]:
        """
        Строит блок нового элемента по шаблону: подмена имени и тела из XPP.
        """
        if element_type in ('CLS', 'TAB', 'FRM'):
            methods_match = re.search(r'(\s*METHODS\s*\n)(.*?)(\s*ENDMETHODS)', template_content, re.DOTALL)
            if not methods_match:
                return None
            new_methods_body = []
            for xpp_file in sorted(element_dir.glob('*.xpp')):
                method_name = xpp_file.stem
                code = self._read_xpp_content(xpp_file)
                if not code:
                    continue
                formatted = self._format_code_for_xpo(code, '        #')
                new_methods_body.append('      SOURCE #{}\n{}\n      ENDSOURCE'.format(method_name, formatted))
            new_methods = methods_match.group(1) + '\n'.join(new_methods_body) + '\n' + methods_match.group(3)
            new_content = template_content[:methods_match.start(0)] + new_methods + template_content[methods_match.end(0):]
        elif element_type == 'JOB':
            main_xpp = element_dir / 'main.xpp'
            if not main_xpp.exists():
                main_xpp = next(element_dir.glob('*.xpp'), None)
            if not main_xpp or not main_xpp.exists():
                return None
            code = self._read_xpp_content(main_xpp)
            formatted = self._format_code_for_xpo(code, '    #')
            new_source = '  SOURCE #{}\n{}\n  ENDSOURCE'.format(element_name, formatted)
            new_content = re.sub(
                r'SOURCE\s+#\S+.*?ENDSOURCE',
                new_source,
                template_content,
                count=1,
                flags=re.DOTALL
            )
        else:
            new_content = template_content
        template_name = None
        if element_type == 'CLS':
            m = re.search(r'CLASS\s+#(\S+)', template_content)
            template_name = m.group(1) if m else ''
        elif element_type == 'JOB':
            m = re.search(r'SOURCE\s+#(\S+)', template_content)
            template_name = m.group(1) if m else ''
        elif element_type in ('TAB', 'FRM'):
            m = re.search(r'(TABLE|FORM)\s+#(\S+)', template_content)
            template_name = m.group(2) if m else ''
        if template_name:
            new_content = new_content.replace('#' + template_name, '#' + element_name)
        if element_type == 'CLS':
            new_content = re.sub(
                r';\s*Microsoft Dynamics AX Class:\s*[^\n]+',
                '; Microsoft Dynamics AX Class: ' + element_name + ' выгружен',
                new_content,
                count=1
            )
        elif element_type in ('TAB', 'FRM'):
            new_content = re.sub(
                r';\s*Microsoft Dynamics AX (Table|Form)\s*:[^\n]+',
                '; Microsoft Dynamics AX \\1 : ' + element_name + ' выгружен',
                new_content,
                count=1
            )
        if element_type == 'JOB':
            new_content = re.sub(
                r';\s*Microsoft Dynamics AX Job:\s*[^\n]+',
                '; Microsoft Dynamics AX Job: ' + element_name + ' выгружен',
                new_content,
                count=1
            )
        origin_match = re.search(r'(Origin\s+)#\{[^}]+\}', new_content)
        if origin_match:
            new_guid = '{' + str(uuid.uuid4()).upper() + '}'
            new_content = re.sub(
                r'(Origin\s+)#\{[^}]+\}',
                r'\1#' + new_guid,
                new_content,
                count=1
            )
        return new_content
    
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
    
    def _get_code_line_indent(self, source_block_content: str) -> str:
        """Возвращает отступ первой строки кода в блоке SOURCE (пробелы до #). По умолчанию 8 пробелов."""
        lines = source_block_content.splitlines()
        for line in lines[1:]:  # пропускаем строку SOURCE #methodName
            stripped = line.lstrip()
            if stripped.startswith('#'):
                indent = line[:len(line) - len(stripped)]
                if indent:
                    return indent
            elif stripped:
                break
        return '        '  # 8 пробелов, как в эталонном XPO

    def _format_code_for_xpo(self, code: str, line_prefix: str = '        #') -> str:
        """
        Форматирует код XPP для вставки в блок SOURCE XPO:
        каждая строка превращается в строку комментария (line_prefix + код).
        
        Args:
            code: исходный текст метода из XPP.
            line_prefix: отступ и решётка перед кодом (по умолчанию "        #" — 8 пробелов).
            
        Returns:
            Строка, готовая для вставки внутрь блока SOURCE.
        """
        lines = code.split('\n')
        formatted_lines = []
        empty_prefix = line_prefix.rstrip('#').rstrip() + '#' if '#' in line_prefix else '    #'
        for line in lines:
            if not line.strip():
                formatted_lines.append(empty_prefix)
            else:
                formatted_lines.append(f'{line_prefix}{line}')
        return '\n'.join(formatted_lines)
    
    def _get_existing_source_block(self, element_content: str, method_name: str) -> Optional[str]:
        """Возвращает блок SOURCE #methodName ... ENDSOURCE из элемента или None."""
        source_pattern = rf'^\s*SOURCE\s+#{re.escape(method_name)}\s*(?:\r?\n)(.*?)^\s*ENDSOURCE'
        match = re.search(source_pattern, element_content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(0)
        block = self._find_source_block_by_lines(element_content, method_name)
        if not block and method_name == 'checkMPCode':
            block = self._find_source_block_literal(element_content, 'SOURCE #checkMPcode')
        return block

    def _source_block_to_raw_code(self, source_block: str) -> str:
        """Из блока SOURCE ... ENDSOURCE извлекает код: убирается только префикс до # включительно, отступ кода сохраняется."""
        lines = source_block.splitlines()
        code_lines = []
        started = False
        for line in lines:
            if line.strip().startswith('ENDSOURCE'):
                break
            if re.match(r'^\s*SOURCE\s+#', line, re.IGNORECASE):
                started = True
                continue
            if not started:
                continue
            stripped = line.lstrip()
            if stripped.startswith('#'):
                code_lines.append(stripped[1:].rstrip() if len(stripped) > 1 else '')
            else:
                code_lines.append(line.rstrip())
        return '\n'.join(code_lines).rstrip('\n')

    def _method_codes_equal(self, xpo_source_block: str, xpp_code: str) -> bool:
        """Сравнивает код из XPO (блок SOURCE) и код из XPP (нормализация пробелов и окончаний строк)."""
        xpo_code = self._source_block_to_raw_code(xpo_source_block)
        xpp_normalized = xpp_code.replace('\r\n', '\n').replace('\r', '\n').rstrip('\n')
        return xpo_code == xpp_normalized

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
        old_source_content = self._get_existing_source_block(element_content, method_name)
        if not old_source_content:
            return None
        
        # Отступ строк кода в XPO берём из исходного блока (чтобы не плодить лишние табы)
        code_line_indent = self._get_code_line_indent(old_source_content)
        line_prefix = code_line_indent + '#'
        formatted_code = self._format_code_for_xpo(method_code, line_prefix)
        
        # Сохраняем исходные отступы перед SOURCE/ENDSOURCE
        source_indent = self._get_indent_before(old_source_content, 'SOURCE')
        endsource_indent = self._get_indent_before(old_source_content, 'ENDSOURCE')
        new_source_content = f'{source_indent}SOURCE #{method_name}\n{formatted_code}\n{endsource_indent}ENDSOURCE'
        
        # Подменяем старый блок SOURCE на новый
        new_element_content = element_content.replace(old_source_content, new_source_content)
        
        return new_element_content
    
    def _insert_new_source_block(self, element_content: str, method_name: str, method_code: str) -> Optional[str]:
        """
        Вставляет новый блок SOURCE #methodName ... ENDSOURCE перед ENDMETHODS (для методов, которых ещё нет в XPO).
        """
        marker = '    ENDMETHODS'
        idx = element_content.rfind(marker)
        if idx < 0:
            return None
        formatted_code = self._format_code_for_xpo(method_code, '        #')
        new_block = '      SOURCE #{}\n{}\n      ENDSOURCE\n'.format(method_name, formatted_code)
        return element_content[:idx] + new_block + element_content[idx:]

    def _find_source_block_literal(self, element_content: str, source_marker: str) -> Optional[str]:
        """Ищет блок по точной строке SOURCE #method (напр. SOURCE #checkMPcode) до следующего ENDSOURCE."""
        idx = element_content.find(source_marker)
        if idx < 0:
            return None
        end_idx = element_content.find('ENDSOURCE', idx)
        if end_idx < 0:
            return None
        end_line = element_content.find('\n', end_idx)
        if end_line < 0:
            end_line = len(element_content)
        else:
            end_line += 1
        return element_content[idx:end_line]

    def _find_source_block_by_lines(self, element_content: str, method_name: str) -> Optional[str]:
        """Ищет блок SOURCE #methodName ... ENDSOURCE по строкам (запасной вариант при сбое regex)."""
        lines = element_content.splitlines(keepends=True)
        if not lines:
            return None
        name_lower = method_name.lower()
        i = 0
        while i < len(lines):
            line = lines[i]
            if 'SOURCE #' in line and '#' in line:
                after_hash = line.split('#', 1)[-1].strip()
                if after_hash.strip().lower() == name_lower:
                    start_i = i
                    i += 1
                    while i < len(lines):
                        if lines[i].strip() == 'ENDSOURCE':
                            return ''.join(lines[start_i:i + 1])
                        i += 1
                    return None
            i += 1
        return None
    
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
            content = content.lstrip('\ufeff')
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

    raw_argv = sys.argv[1:]
    force = "--force" in raw_argv
    no_input = "--no-input" in raw_argv or _no_input_env()
    args = [a for a in raw_argv if a not in ("--force", "--no-input")]

    def process_one(xpo_file: str, parser_dir: str, force: bool, no_input: bool) -> None:
        try:
            writer = XPOWriter(xpo_file, parser_dir, force=force, no_input=no_input)

            print(
                "Запуск записи изменений XPP обратно в XPO."
                + (" (--force: проверка дат отключена)" if force else "")
                + (" (--no-input)" if no_input else "")
            )
            print(f"Исходный XPO: {xpo_file}")
            print(f"Каталог parserXPO: {parser_dir}")
            print("-" * 60)
            
            output_file = writer.write_back()
            
            if output_file:
                print("\nГотово: XPO-файл успешно обновлен.")
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

    # Если XPO‑файл не передан в аргументах, пытаемся найти его в каталоге XPO
    if len(args) < 1:
        xpo_dir = Path("XPO")
        if xpo_dir.exists():
            xpo_files = [p for p in xpo_dir.glob("*.xpo") if not p.name.endswith("_WR.xpo")]
            if xpo_files:
                print("Найдено XPO-файлов в каталоге XPO: {}".format(len(xpo_files)))
                for i, xpo_file in enumerate(xpo_files, 1):
                    print(f"  {i}. {xpo_file.name}")

                if len(xpo_files) == 1:
                    xpo_file = str(xpo_files[0])
                    print("Используется XPO-файл: {}".format(xpo_file))
                    selected_files = [xpo_file]
                elif no_input:
                    selected_files = [str(p) for p in xpo_files]
                    print("\n--no-input / CI: обрабатываются все XPO-файлы.")
                else:
                    print("\n0. Все файлы")
                    while True:
                        try:
                            choice = input("\nУкажите номер XPO-файла (0 - все файлы): ").strip()
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
                        print("\nБудут обработаны все XPO-файлы.")
                    else:
                        xpo_file = str(xpo_files[choice_num - 1])
                        print("Используется XPO-файл: {}".format(xpo_file))
                        selected_files = [xpo_file]
            else:
                print("В каталоге XPO не найдено файлов с расширением .xpo.")
                print("Использование: python xpo_writer.py <имя_файла.xpo> [каталог_parserXPO] [--force] [--no-input]")
                print("Текущий каталог XPO: {}".format(xpo_dir.resolve()))
                sys.exit(1)
        else:
            print("Каталог XPO не найден.")
            print("Использование: python xpo_writer.py <имя_файла.xpo> [каталог_parserXPO] [--force] [--no-input]")
            sys.exit(1)
    else:
        xpo_file = args[0]
        selected_files = [xpo_file]

    parser_dir = args[1] if len(args) > 1 else "parserXPO"

    for xpo_file in selected_files:
        process_one(xpo_file, parser_dir, force, no_input)


if __name__ == "__main__":
    main()
