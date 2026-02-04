#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Метаданные комментариев для Dynamics AX Development Assistant
"""
import json
from pathlib import Path


def get_comment_metadata() -> dict:
    """
    Возвращает метаданные комментариев
    
    Returns:
        Словарь с developer, date, project
    """
    meta_path = Path(__file__).parent.parent / "commentmeta.json"
    
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "developer": "unknown",
            "date": "unknown",
            "project": "unknown"
        }
    except Exception:
        return {
            "developer": "unknown", 
            "date": "unknown",
            "project": "unknown"
        }


def format_comment(code: str) -> str:
    """
    Форматирует комментарий для кода
    
    Args:
        code: Код для комментирования
        
    Returns:
        Код с добавленным комментарием
    """
    meta = get_comment_metadata()
    
    if '\n' in code:
        # Многострочный комментарий
        return f"// + {meta['date']} {meta['developer']} {meta['project']}\n{code}\n// - {meta['date']} {meta['developer']} {meta['project']}"
    else:
        # Однострочный комментарий
        return f"{code} // {meta['date']} {meta['developer']} {meta['project']}"


if __name__ == "__main__":
    print(get_comment_metadata())