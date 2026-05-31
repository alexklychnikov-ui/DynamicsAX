#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для загрузки и работы с метками из одного или нескольких ALD файлов.
Поддерживаются префиксы вида @MIK123, @KOR1985, @SYS333411 и т.п.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union


PathLike = Union[str, Path]
PathsArg = Union[PathLike, Sequence[PathLike]]


class LabelLoader:
    def __init__(self, ald_paths: PathsArg):
        paths = self._normalize_paths(ald_paths)
        if not paths:
            raise ValueError("Не указан ни один ALD файл")
        self.ald_file_paths: List[Path] = paths
        self.labels: Dict[str, str] = {}
        for p in self.ald_file_paths:
            self._load_from_file(p)

    @staticmethod
    def _normalize_paths(ald_paths: PathsArg) -> List[Path]:
        if isinstance(ald_paths, (str, Path)):
            return [Path(ald_paths)]
        return [Path(p) for p in ald_paths]

    def _load_from_file(self, ald_file_path: Path) -> None:
        if not ald_file_path.exists():
            raise FileNotFoundError(f"ALD файл не найден: {ald_file_path}")

        current_label: Optional[str] = None
        current_description: List[str] = []

        with open(ald_file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.rstrip()
                label_match = re.match(r"^@([A-Za-z]+)(\d+)\s*(.*)$", line)
                if label_match:
                    if current_label is not None:
                        description = "\n".join(current_description).strip()
                        self.labels[current_label] = description

                    prefix = label_match.group(1).upper()
                    num = label_match.group(2)
                    current_label = f"{prefix}{num}"
                    description_part = label_match.group(3).strip()
                    current_description = [description_part] if description_part else []
                elif current_label is not None:
                    if line.strip():
                        current_description.append(line.strip())
                    else:
                        description = "\n".join(current_description).strip()
                        self.labels[current_label] = description
                        current_label = None
                        current_description = []

        if current_label is not None:
            description = "\n".join(current_description).strip()
            self.labels[current_label] = description

    def _normalize_label_key(self, label_id: str) -> str:
        s = label_id.strip().lstrip("@")
        if re.fullmatch(r"\d+", s):
            return f"MIK{s}"
        m = re.match(r"^([A-Za-z]+)(\d+)$", s)
        if m:
            return f"{m.group(1).upper()}{m.group(2)}"
        return s.upper()

    def get_label(self, label_id: str) -> Optional[str]:
        """Получает описание метки по ID (например, \"MIK4140\", \"4140\" -> MIK4140, \"KOR1985\")."""
        key = self._normalize_label_key(label_id)
        return self.labels.get(key)

    def find_labels_in_text(self, text: str) -> Dict[str, str]:
        """Находит все метки @PREFIXnnnn в тексте и возвращает их с расшифровками."""
        found_labels: Dict[str, str] = {}

        for prefix, num in re.findall(r"(?:Label\s+#)?@([A-Za-z]+)(\d+)", text):
            label_key = f"{prefix.upper()}{num}"
            if label_key not in found_labels:
                description = self.get_label(label_key)
                if description:
                    found_labels[label_key] = description

        return found_labels

    def replace_labels_in_text(self, text: str, mode: str = "comments") -> str:
        """Заменяет метки @PREFIXnnnn (и вариант Label #@...) на их расшифровки в тексте."""
        pattern = r"(?:Label\s+#)?@([A-Za-z]+)(\d+)"

        if mode == "comments":

            def replace_func(match: re.Match) -> str:
                label_key = f"{match.group(1).upper()}{match.group(2)}"
                description = self.get_label(label_key)
                if description:
                    return f"{match.group(0)} // {description}"
                return match.group(0)

            text = re.sub(pattern, replace_func, text)

        elif mode == "inline":

            def replace_func_inline(match: re.Match) -> str:
                label_key = f"{match.group(1).upper()}{match.group(2)}"
                description = self.get_label(label_key)
                if description:
                    return f'"{description}"'
                return match.group(0)

            text = re.sub(pattern, replace_func_inline, text)

        return text

    def get_all_labels(self) -> Dict[str, str]:
        """Возвращает все загруженные метки."""
        return self.labels.copy()
