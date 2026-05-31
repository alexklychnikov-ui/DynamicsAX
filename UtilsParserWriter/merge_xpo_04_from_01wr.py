#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вставляет элементы из SharedProject_X5SHP_INT_1_000002338_01_WR.xpo в базовый 04.xpo
перед классом RabbitIntEngineImp_Infor_Shipped. PRN и дубликат InventItemGTIN из 01 не копируются.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_04 = ROOT / "XPO" / "SharedProject_X5SHP_INT_1_000002338_04.xpo"
SOURCE_01WR = ROOT / "XPO" / "SharedProject_X5SHP_INT_1_000002338_01_WR.xpo"
OUT_MERGED = ROOT / "XPO" / "SharedProject_X5SHP_INT_1_000002338_04_full.xpo"

INSERT_BEFORE = re.compile(
    r"(?=\*\*\*Element:\s*CLS\s*\r?\n\s*\r?\n;\s*Microsoft Dynamics AX Class:\s*RabbitIntEngineImp_Infor_Shipped)",
    re.IGNORECASE,
)


def _decode(raw: bytes) -> tuple[str, str]:
    for enc in ("cp1251", "utf-8-sig", "utf-8"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("cp1251", errors="replace"), "cp1251"


def _name_for_element(etype: str, chunk: str) -> str | None:
    if etype == "CLS":
        m = re.search(r"^\s*CLASS\s+#(\w+)", chunk, re.MULTILINE | re.IGNORECASE)
        return m.group(1) if m else None
    if etype in ("DBT", "TAB"):
        m = re.search(r"^\s*TABLE\s+#(\w+)", chunk, re.MULTILINE | re.IGNORECASE)
        return m.group(1) if m else None
    if etype == "FRM":
        m = re.search(r"^\s*FORM\s+#(\w+)", chunk, re.MULTILINE | re.IGNORECASE)
        return m.group(1) if m else None
    if etype == "PRN":
        m = re.search(r"PROJECT\s+#(\w+)", chunk)
        return m.group(1) if m else None
    return None


def split_elements(text: str) -> list[tuple[str, str | None, str]]:
    parts = re.split(r"(?=\*\*\*Element:\s*\w+)", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p or p.startswith("Exportfile"):
            continue
        m = re.match(r"\*\*\*Element:\s*(\w+)", p)
        if not m:
            continue
        etype = m.group(1)
        if etype == "END":
            continue
        name = _name_for_element(etype, p)
        out.append((etype, name, p))
    return out


def main() -> None:
    if not SOURCE_01WR.is_file():
        raise SystemExit(f"Нет файла: {SOURCE_01WR}")
    raw = SOURCE_01WR.read_bytes()
    text, enc = _decode(raw)
    elems = split_elements(text)

    skip_pairs = {
        ("PRN", "X5SHP_INT_1_000002338_01"),
        ("DBT", "InventItemGTIN"),
    }
    blocks: list[str] = []
    for etype, name, chunk in elems:
        if etype == "PRN":
            continue
        if name and (etype, name) in skip_pairs:
            continue
        blocks.append(chunk)

    base_raw = BASE_04.read_bytes()
    base_text, base_enc = _decode(base_raw)
    enc_out = base_enc if base_enc == enc else "cp1251"

    m = INSERT_BEFORE.search(base_text)
    if not m:
        raise SystemExit("Маркер вставки (RabbitIntEngineImp_Infor_Shipped) не найден в 04.xpo")

    insert = "\n\n".join(blocks) + "\n\n"
    merged = base_text[: m.start()] + insert + base_text[m.start() :]

    OUT_MERGED.write_text(merged, encoding=enc_out, newline="")
    print(f"OK: {OUT_MERGED.name} — вставлено элементов из 01_WR: {len(blocks)}")


if __name__ == "__main__":
    main()
