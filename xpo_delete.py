#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Удаляет все файлы (рекурсивно) в каталогах parserXPO и XPO относительно корня репозитория.
Пустые подкаталоги после удаления файлов тоже убираются; сами parserXPO и XPO остаются.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_DEFAULT_DIRS = ("parserXPO", "XPO")


def _no_confirm_env() -> bool:
    v = os.environ.get("XPO_DELETE_NO_CONFIRM", "").strip().lower()
    return v in ("1", "true", "yes")


def clear_tree(root: Path) -> tuple[int, int]:
    """Удалить все файлы под root и пустые подпапки. Возвращает (число файлов, число удалённых каталогов)."""
    if not root.is_dir():
        return 0, 0
    files_removed = 0
    dirs_removed = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        base = Path(dirpath)
        for name in filenames:
            p = base / name
            try:
                p.unlink()
                files_removed += 1
            except OSError as e:
                print(f"Ошибка удаления файла {p}: {e}", file=sys.stderr)
                raise
        for name in dirnames:
            p = base / name
            try:
                p.rmdir()
                dirs_removed += 1
            except OSError as e:
                print(f"Ошибка удаления каталога {p}: {e}", file=sys.stderr)
                raise
    return files_removed, dirs_removed


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Удалить все файлы в parserXPO и XPO (рекурсивно)."
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Не спрашивать подтверждение (для CI/агентов).",
    )
    args = parser.parse_args()
    yes = args.yes or _no_confirm_env()

    targets = [repo_root / d for d in _DEFAULT_DIRS]
    existing = [p for p in targets if p.is_dir()]

    if not existing:
        print("Каталоги parserXPO и XPO не найдены или пусты по пути — нечего удалять.")
        return 0

    if not yes:
        if sys.stdin.isatty():
            print("Будут удалены ВСЕ файлы в:")
            for p in existing:
                print(f"  {p}")
            reply = input("Продолжить? [y/N] ").strip().lower()
            if reply not in ("y", "yes"):
                print("Отменено.")
                return 1
        else:
            print(
                "Неинтерактивный режим: укажите --yes или XPO_DELETE_NO_CONFIRM=1",
                file=sys.stderr,
            )
            return 2

    total_files = 0
    total_dirs = 0
    for p in existing:
        f, d = clear_tree(p)
        total_files += f
        total_dirs += d
        print(f"{p.name}: удалено файлов {f}, подкаталогов {d}")

    print(f"Итого: файлов {total_files}, подкаталогов {total_dirs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
