#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для интеграции кода в структуру parserXPO
"""
from pathlib import Path
from typing import Dict, Optional


class ParserIntegration:
    def __init__(self, parser_dir: str = "parserXPO"):
        self.parser_dir = Path(parser_dir)
        self.parser_dir.mkdir(parents=True, exist_ok=True)
    
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
        
        # Создаем директорию для элемента
        element_dir = self.parser_dir / element_name
        element_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем свойства
        properties = element_data.get('properties', {})
        if properties:
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
        
        # Создаем директорию для элемента
        element_dir = self.parser_dir / element_name
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
        method_file = self.parser_dir / element_name / f"{method_name}.xpp"
        
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
        element_dir = self.parser_dir / element_name
        
        if not element_dir.exists():
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
        element_dir = self.parser_dir / element_name
        if not element_dir.exists():
            return False
        
        # Проверяем, что есть хотя бы один файл метода
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
        method_file = self.parser_dir / element_name / f"{method_name}.xpp"
        return method_file.exists()

















