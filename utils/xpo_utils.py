#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Общие утилиты для работы с XPO файлами Dynamics AX
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Регулярные выражения для типов элементов
ELEMENT_PATTERNS = {
    'CLS': r'CLASS\s+#(\w+)',
    'TAB': r'TABLE\s+#(\w+)',
    'FRM': r'FORM\s+#(\w+)',
    'MCR': r'MACRO\s+#(\w+)',
    'ENU': r'ENUM\s+#(\w+)',
    'EDT': r'EDT\s+#(\w+)',
    'SPV': r'PRIVILEGE\s+#(\w+)',
    'JOB': r'SOURCE\s+#(\w+)',
    'MAP': r'MAP\s+#(\w+)',
    'QTY': r'QUERY\s+#(\w+)',
}

# Паттерн для поиска элементов в XPO файле
XPO_ELEMENT_PATTERN = re.compile(r'^\*\*\*Element:\s*(\w+)', re.MULTILINE)

# Паттерн для поиска SOURCE блоков
SOURCE_PATTERN = re.compile(r'SOURCE\s+#(\w+)(.*?)ENDSOURCE', re.DOTALL)

# Паттерн для извлечения свойств
PROPERTIES_PATTERN = re.compile(r'PROPERTIES(.*?)ENDPROPERTIES', re.DOTALL)

# Паттерн для извлечения Extends
EXTENDS_PATTERN = re.compile(r'Extends\s+#(\w+)')

# Паттерн для поиска меток @MIK
LABEL_PATTERN = re.compile(r'@MIK(\d+)')

# Паттерн для поиска Label #@MIK
LABEL_PATTERN2 = re.compile(r'Label\s+#@MIK(\d+)')


def clean_xpo_code(code: str) -> str:
    """
    Очищает код XPO: удаляет префикс "пробелы/табы + #" в начале каждой строки.
    Отступы после # (пробелы или табы) сохраняются — структура вложенности не меняется.
    """
    lines = code.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned = re.sub(r'^\s*#', '', line)
        cleaned_lines.append(cleaned)
    return '\n'.join(cleaned_lines).strip()


def format_code_for_xpo(code: str, indent: str = '    ') -> str:
    """
    Форматирует код для записи в XPO (добавляет префиксы #)
    
    Args:
        code: Исходный код метода
        indent: Отступ для каждой строки
        
    Returns:
        Код с префиксами для XPO
    """
    lines = code.split('\n')
    formatted_lines = []
    
    for line in lines:
        if not line.strip():
            formatted_lines.append(f'{indent}#')
        else:
            formatted_lines.append(f'{indent}#{line}')
    
    return '\n'.join(formatted_lines)


def extract_element_name(element_type: str, content: str) -> Optional[str]:
    """
    Извлекает имя элемента из его содержимого
    
    Args:
        element_type: Тип элемента (CLS, TAB, FRM, JOB и т.д.)
        content: Содержимое элемента
        
    Returns:
        Имя элемента или None
    """
    pattern = ELEMENT_PATTERNS.get(element_type)
    if pattern:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    return None


def extract_methods(content: str) -> Dict[str, str]:
    """
    Извлекает все методы из содержимого элемента
    
    Args:
        content: Содержимое элемента
        
    Returns:
        Словарь {имя_метода: код_метода}
    """
    methods = {}
    
    # Сначала ищем в блоке METHODS...ENDMETHODS
    methods_block_match = PROPERTIES_PATTERN.search(content)
    if methods_block_match:
        methods_content = methods_block_match.group(1)
        for method_match in SOURCE_PATTERN.finditer(methods_content):
            method_name = method_match.group(1)
            method_code = method_match.group(2)
            cleaned_code = clean_xpo_code(method_code)
            methods[method_name] = cleaned_code
    
    # Если методы не найдены в METHODS блоке, ищем по всему содержимому (для JOB)
    if not methods:
        for method_match in SOURCE_PATTERN.finditer(content):
            method_name = method_match.group(1)
            method_code = method_match.group(2)
            cleaned_code = clean_xpo_code(method_code)
            methods[method_name] = cleaned_code
    
    return methods


def extract_properties(content: str) -> Dict[str, str]:
    """
    Извлекает свойства элемента
    
    Args:
        content: Содержимое элемента
        
    Returns:
        Словарь {свойство: значение}
    """
    properties = {}
    
    props_match = PROPERTIES_PATTERN.search(content)
    if props_match:
        props_text = props_match.group(1)
        
        # Извлекаем Extends
        extends_match = EXTENDS_PATTERN.search(props_text)
        if extends_match:
            properties['extends'] = extends_match.group(1)
    
    return properties


def find_labels_in_text(text: str) -> List[str]:
    """
    Находит все метки @MIK в тексте
    
    Args:
        text: Текст для поиска
        
    Returns:
        Список найденных ID меток (без префикса MIK)
    """
    labels = set()
    
    # Ищем @MIK<номер>
    for match in LABEL_PATTERN.finditer(text):
        labels.add(match.group(1))
    
    # Ищем Label #@MIK<номер>
    for match in LABEL_PATTERN2.finditer(text):
        labels.add(match.group(1))
    
    return sorted(labels)


def parse_xpo_element(content: str, element_type: str) -> Optional[Dict]:
    """
    Парсит элемент XPO и возвращает его структурированное представление
    
    Args:
        content: Содержимое элемента
        element_type: Тип элемента
        
    Returns:
        Словарь с данными элемента или None
    """
    element_name = extract_element_name(element_type, content)
    if not element_name:
        return None
    
    return {
        'type': element_type,
        'name': element_name,
        'properties': extract_properties(content),
        'methods': extract_methods(content)
    }


def find_xpo_elements(content: str) -> List[Tuple[int, int, str]]:
    """
    Находит все элементы в XPO контенте
    
    Args:
        content: Содержимое XPO файла
        
    Returns:
        Список кортежей (позиция_начала, позиция_конца, тип_элемента)
    """
    elements = []
    matches = list(XPO_ELEMENT_PATTERN.finditer(content))
    
    for i, match in enumerate(matches):
        element_type = match.group(1)
        start_pos = match.start()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        elements.append((start_pos, end_pos, element_type))
    
    return elements


def get_element_content(content: str, element_match) -> str:
    """
    Извлекает содержимое элемента из XPO
    
    Args:
        content: Полное содержимое XPO файла
        element_match: Результат поиска элемента
        
    Returns:
        Содержимое элемента
    """
    return content[element_match.start():element_match.end()]