#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлекает методы классов RabbitIntEngineImp_Infor, _Shipped, _ShippedPart из XPO
и сохраняет в parserXPO/<ClassFolder>/*.xpp (очищенный от префикса # код).
"""
import re
from pathlib import Path

# границы классов в XPO (строки 1-based)
CLASS_RANGES = {
    'RabbitIntEngineImp_Infor': (4653, 7246),
    'RabbitIntEngineImp_Infor_Shipped': (7247, 9049),
    'RabbitIntEngineImp_Infor_ShippedPart': (9050, 11288),
}

OUTPUT_DIRS = {
    'RabbitIntEngineImp_Infor': 'RabbitIntEngineImp_Infor',
    'RabbitIntEngineImp_Infor_Shipped': 'RabbitIntEngineImp_Infor_Shipped',
    'RabbitIntEngineImp_Infor_ShippedPart': 'RabbitIntEngineImp_Infor_ShippedPart',
}

XPO_PATH = Path(__file__).resolve().parent.parent / 'XPO' / 'SharedProject_X5SHP_INT_1_000002338_01.xpo'
PARSER_BASE = Path(__file__).resolve().parent


def clean_xpo_code(code: str) -> str:
    """Удаляет префикс пробелы + # в начале каждой строки."""
    lines = code.split('\n')
    cleaned = []
    for line in lines:
        cleaned.append(re.sub(r'^\s*#', '', line))
    return '\n'.join(cleaned).strip()


def extract_methods_from_range(lines: list, start: int, end: int) -> dict:
    """Из диапазона строк извлекает SOURCE #name ... ENDSOURCE, возвращает {name: code}."""
    methods = {}
    i = start
    while i <= end:
        line = lines[i]
        if re.match(r'\s*SOURCE\s+#(\w+)', line):
            m = re.match(r'\s*SOURCE\s+#(\w+)', line)
            name = m.group(1)
            i += 1
            code_lines = []
            while i <= end:
                l = lines[i]
                if re.match(r'\s*ENDSOURCE', l):
                    break
                code_lines.append(l)
                i += 1
            code = '\n'.join(code_lines)
            methods[name] = clean_xpo_code(code)
        i += 1
    return methods


def main():
    text = XPO_PATH.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    for class_name, (lo, hi) in CLASS_RANGES.items():
        out_dir = PARSER_BASE / OUTPUT_DIRS[class_name]
        out_dir.mkdir(parents=True, exist_ok=True)
        methods = extract_methods_from_range(lines, lo - 1, hi - 1)
        for method_name, code in methods.items():
            path = out_dir / f'{method_name}.xpp'
            path.write_text(code, encoding='utf-8')
        print(f'{class_name}: {len(methods)} methods -> {out_dir}')
    print('Done.')


if __name__ == '__main__':
    main()
