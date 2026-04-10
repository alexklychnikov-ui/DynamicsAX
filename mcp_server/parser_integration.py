#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для интеграции кода в структуру parserXPO
"""
import sys
from pathlib import Path
from typing import Dict, Optional

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from xpo_parser import AOT_CATEGORY_DIRS


class ParserIntegration:
    def __init__(self, parser_dir: str = "parserXPO"):
        self.parser_dir = Path(parser_dir)
        self.parser_dir.mkdir(parents=True, exist_ok=True)

    def _element_dir(self, element_name: str) -> Optional[Path]:
        for cat in AOT_CATEGORY_DIRS:
            p = self.parser_dir / cat / element_name
            if p.is_dir():
                return p
        legacy = self.parser_dir / element_name
        if legacy.is_dir():
            return legacy
        return None
    
    def save_element(self, element_data: Dict, overwrite: bool = True) -> bool:
        """Сохраняет элемент в структуру parserXPO
        
        Args:
            element_data: Словарь с данными элемента (type, name, properties, methods)
            overwrite: Перезаписывать существующие файлы
        
        Returns:
            True если успешно сохранено
        """
        element_name = element_data.get('name')
        if not element_name:
            return False
        
        aot = element_data.get("aot_folder", "Classes")
        if AOT_CATEGORY_DIRS and aot not in AOT_CATEGORY_DIRS:
            aot = "Misc"
        element_dir = self.parser_dir / aot / element_name
        element_dir.mkdir(parents=True, exist_ok=True)
        
        properties = element_data.get('properties', {})
        props_file = element_dir / "properties.txt"
        with open(props_file, 'w', encoding='utf-8') as f:
            f.write(f"Type: {element_data.get('type', 'UNKNOWN')}\n")
            for key, value in properties.items():
                f.write(f"{key}: {value}\n")
        
        # Сохраняем методы
        methods = element_data.get('methods', {})
        saved_count = 0
        
        for method_name, method_code in methods.items():
            if method_code.strip():  # Сохраняем только непустые методы
                method_file = element_dir / f"{method_name}.xpp"
                
                # Пропускаем существующие файлы если не перезаписываем
                if not overwrite and method_file.exists():
                    continue
                
                with open(method_file, 'w', encoding='utf-8') as f:
                    f.write(method_code)
                saved_count += 1
        
        return saved_count > 0
    
    def save_method(self, element_name: str, method_name: str, method_code: str, overwrite: bool = True) -> bool:
        """Сохраняет отдельный метод элемента
        
        Args:
            element_name: Имя элемента
            method_name: Имя метода
            method_code: Код метода
            overwrite: Перезаписывать существующий файл
        
        Returns:
            True если успешно сохранено
        """
        if not method_code.strip():
            return False
        
        element_dir = self._element_dir(element_name)
        if element_dir is None:
            element_dir = self.parser_dir / "Classes" / element_name
            element_dir.mkdir(parents=True, exist_ok=True)
        
        method_file = element_dir / f"{method_name}.xpp"
        
        # Пропускаем существующий файл если не перезаписываем
        if not overwrite and method_file.exists():
            return False
        
        with open(method_file, 'w', encoding='utf-8') as f:
            f.write(method_code)
        
        return True
    
    def read_method(self, element_name: str, method_name: str) -> Optional[str]:
        """Читает код метода из parserXPO
        
        Args:
            element_name: Имя элемента
            method_name: Имя метода
        
        Returns:
            Код метода или None
        """
        element_dir = self._element_dir(element_name)
        if element_dir is None:
            return None
        method_file = element_dir / f"{method_name}.xpp"
        if not method_file.exists():
            return None
        with open(method_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def read_element_methods(self, element_name: str) -> Dict[str, str]:
        """Читает все методы элемента из parserXPO
        
        Args:
            element_name: Имя элемента
        
        Returns:
            Словарь {method_name: method_code}
        """
        element_dir = self._element_dir(element_name)
        if element_dir is None:
            return {}
        
        methods = {}
        for method_file in element_dir.glob("*.xpp"):
            method_name = method_file.stem
            with open(method_file, 'r', encoding='utf-8') as f:
                methods[method_name] = f.read()
        
        return methods
    
    def update_method(self, element_name: str, method_name: str, new_code: str) -> bool:
        """Обновляет код метода в parserXPO
        
        Args:
            element_name: Имя элемента
            method_name: Имя метода
            new_code: Новый код метода
        
        Returns:
            True если успешно обновлено
        """
        return self.save_method(element_name, method_name, new_code, overwrite=True)
    
    def element_exists(self, element_name: str) -> bool:
        """Проверяет, существует ли элемент в parserXPO
        
        Args:
            element_name: Имя элемента
        
        Returns:
            True если элемент существует
        """
        element_dir = self._element_dir(element_name)
        if element_dir is None:
            return False
        method_files = list(element_dir.glob("*.xpp"))
        return len(method_files) > 0
    
    def method_exists(self, element_name: str, method_name: str) -> bool:
        """Проверяет, существует ли метод в parserXPO
        
        Args:
            element_name: Имя элемента
            method_name: Имя метода
        
        Returns:
            True если метод существует
        """
        element_dir = self._element_dir(element_name)
        if element_dir is None:
            return False
        return (element_dir / f"{method_name}.xpp").exists()

















