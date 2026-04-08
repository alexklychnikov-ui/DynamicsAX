#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита нормализации отступов в X++ методах в папке parserXPO.

Идея:
- в каждом .xpp‑файле берётся минимальный ведущий отступ среди всех непустых строк;
- этот общий отступ вычитается из всех непустых строк, чтобы первая непустая строка
  начиналась с колонки 0, а относительная вложенность кода сохранялась.
"""

from pathlib import Path
from typing import List


def normalize_file(path: Path) -> bool:
    """
    Нормализует отступы в одном .xpp файле.

    Возвращает True, если файл был изменён.
    """
    original_text = path.read_text(encoding="utf-8")
    lines: List[str] = original_text.splitlines()

    # Собираем уровни отступов для всех непустых строк (только реальный пробельный префикс)
    indent_levels = []
    leading_ws_per_line = []
    for line in lines:
        if not line.strip():
            leading_ws_per_line.append(0)
            continue
        leading_ws_len = len(line) - len(line.lstrip(" \t"))
        leading_ws_per_line.append(leading_ws_len)
        if leading_ws_len > 0:
            indent_levels.append(leading_ws_len)

    if not indent_levels:
        return False

    min_indent = min(indent_levels)
    if min_indent == 0:
        return False

    new_lines: List[str] = []
    for line, leading_ws_len in zip(lines, leading_ws_per_line):
        if not line.strip():
            new_lines.append("")
        else:
            # Срезаем только пробельный префикс, не трогая символы кода
            cut = min(min_indent, leading_ws_len)
            new_lines.append(line[cut:])

    new_text = "\n".join(new_lines)

    if new_text != original_text:
        path.write_text(new_text, encoding="utf-8")
        return True

    return False


def main() -> None:
    import sys

    project_root = Path(__file__).parent.parent
    default_root = project_root / "parserXPO"
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else default_root
    if not root.exists():
        print(f"Папка не найдена: {root}")
        sys.exit(1)

    xpp_files = list(root.rglob("*.xpp"))
    if not xpp_files:
        print(f"В папке {root} не найдено .xpp файлов")
        return

    print(f"Найдено .xpp файлов: {len(xpp_files)}")

    changed = 0
    for path in xpp_files:
        if normalize_file(path):
            changed += 1
            print(f"  Нормализован: {path}")

    print(f"\nИзменено файлов: {changed} из {len(xpp_files)}")


if __name__ == "__main__":
    main()
