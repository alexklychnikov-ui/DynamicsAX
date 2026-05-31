#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собрать отдельный XPO для одного класса из parserXPO/Classes/<Name>."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from xpo_writer import XPOWriter  # noqa: E402


def export_class(class_name: str, template_xpo: Path, out_xpo: Path) -> Path:
    writer = XPOWriter(str(template_xpo), parser_dir=str(ROOT / "parserXPO"), force=True, no_input=False)
    raw = template_xpo.read_bytes()
    xpo_content, encoding, newline = writer._decode_xpo_content(raw)
    xpo_content = writer._normalize_newlines(xpo_content)

    element_dir = ROOT / "parserXPO" / "Classes" / class_name
    if not element_dir.is_dir():
        raise FileNotFoundError(element_dir)

    template_info = writer._find_any_element_of_type(xpo_content, "CLS")
    if not template_info:
        raise RuntimeError("В шаблоне XPO не найден элемент CLS")

    new_block = writer._build_new_element_block(
        template_info["content"], "CLS", class_name, element_dir
    )
    if not new_block:
        raise RuntimeError("Не удалось собрать блок класса")

    new_block = writer._ensure_cls_endclass(new_block)
    props = element_dir / "properties.txt"
    if props.exists():
        text = props.read_text(encoding="utf-8")
        if "Extends:" not in text:
            new_block = re.sub(r"\n\s*Extends\s+#\S+\s*\n", "\n", new_block, count=1)
    header = "Exportfile for AOT version 1.0 or later\nFormatversion: 1\n\n"
    full = header + new_block.rstrip() + "\n\n***Element: END\n"
    full = writer._apply_newline_style(full, newline)

    out_xpo.parent.mkdir(parents=True, exist_ok=True)
    with open(out_xpo, "w", encoding=encoding, newline="") as f:
        f.write(full)

    if not writer._validate_xpo(out_xpo):
        print("ПРЕДУПРЕЖДЕНИЕ: validate_xpo не прошёл", file=sys.stderr)
    return out_xpo


def main():
    class_name = sys.argv[1] if len(sys.argv) > 1 else "MRC_MERK_JobPreviewVetisUtdRequest"
    template = ROOT / "XPO" / "SharedProject_MRC_MERK_000002479_01.xpo"
    if len(sys.argv) > 2:
        template = Path(sys.argv[2])
    out = ROOT / "XPO" / ("Class_" + class_name + ".xpo")
    path = export_class(class_name, template, out)
    print("OK:", path)


if __name__ == "__main__":
    main()
