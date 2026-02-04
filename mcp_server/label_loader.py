#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для загрузки и работы с метками из ALD файла
"""
import re
from pathlib import Path
from typing import Dict, Optional


class LabelLoader:
    def __init__(self, ald_file_path: str):
        self.ald_file_path = Path(ald_file_path)
        self.labels: Dict[str, str] = {}
        self._load_labels()
    
    def _load_labels(self):
        """Загружает метки из ALD файла"""
        if not self.ald_file_path.exists():
            raise FileNotFoundError(f"ALD файл не найден: {self.ald_file_path}")
        
        current_label = None
        current_description = []
        
        with open(self.ald_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.rstrip()
                
                # Ищем строку с меткой вида @MIK<номер>
                label_match = re.match(r'^@MIK(\d+)\s*(.*)$', line)
                if label_match:
                    # Сохраняем предыдущую метку если была
                    if current_label is not None:
                        description = '\n'.join(current_description).strip()
                        self.labels[current_label] = description
                    
                    # Начинаем новую метку
                    label_id = label_match.group(1)
                    current_label = f"MIK{label_id}"
                    description_part = label_match.group(2).strip()
                    current_description = [description_part] if description_part else []
                elif current_label is not None:
                    # Продолжение описания метки (многострочное)
                    if line.strip():
                        current_description.append(line.strip())
                    else:
                        # Пустая строка - завершаем описание
                        description = '\n'.join(current_description).strip()
                        self.labels[current_label] = description
                        current_label = None
                        current_description = []
        
        # Сохраняем последнюю метку
        if current_label is not None:
            description = '\n'.join(current_description).strip()
            self.labels[current_label] = description
    
    def get_label(self, label_id: str) -> Optional[str]:
        """Получает описание метки по ID
        
        Args:
            label_id: ID метки (например, "MIK4140" или "4140")
        
        Returns:
            Описание метки или None если не найдена
        """
        # Нормализуем ID метки
        if not label_id.startswith('MIK'):
            label_id = f"MIK{label_id}"
        
        return self.labels.get(label_id)
    
    def find_labels_in_text(self, text: str) -> Dict[str, str]:
        """Находит все метки @MIK в тексте и возвращает их с расшифровками
        
        Args:
            text: Текст для поиска меток
        
        Returns:
            Словарь {label_id: description}
        """
        found_labels = {}
        
        # Ищем метки в формате @MIK<номер>
        pattern = r'@MIK(\d+)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            label_id = f"MIK{match}"
            if label_id not in found_labels:
                description = self.get_label(label_id)
                if description:
                    found_labels[label_id] = description
        
        # Также ищем в формате Label #@MIK<номер>
        pattern2 = r'Label\s+#@MIK(\d+)'
        matches2 = re.findall(pattern2, text)
        
        for match in matches2:
            label_id = f"MIK{match}"
            if label_id not in found_labels:
                description = self.get_label(label_id)
                if description:
                    found_labels[label_id] = description
        
        return found_labels
    
    def replace_labels_in_text(self, text: str, mode: str = "comments") -> str:
        """Заменяет метки @MIK на их расшифровки в тексте
        
        Args:
            text: Исходный текст
            mode: Режим замены - "comments" (добавляет комментарии) или "inline" (заменяет inline)
        
        Returns:
            Текст с замененными метками
        """
        if mode == "comments":
            # Добавляем комментарии после меток
            def replace_func(match):
                label_id = f"MIK{match.group(1)}"
                description = self.get_label(label_id)
                if description:
                    return f"{match.group(0)} // {description}"
                return match.group(0)
            
            text = re.sub(r'@MIK(\d+)', replace_func, text)
            text = re.sub(r'Label\s+#@MIK(\d+)', replace_func, text)
        
        elif mode == "inline":
            # Заменяем метки на их описания
            def replace_func(match):
                label_id = f"MIK{match.group(1)}"
                description = self.get_label(label_id)
                if description:
                    return f'"{description}"'
                return match.group(0)
            
            text = re.sub(r'@MIK(\d+)', replace_func, text)
            text = re.sub(r'Label\s+#@MIK(\d+)', replace_func, text)
        
        return text
    
    def get_all_labels(self) -> Dict[str, str]:
        """Возвращает все загруженные метки"""
        return self.labels.copy()

















