#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Все блоки SOURCE в FORM: корень формы, datasource, поля, контролы.
Ключи файлов: <method>.xpp | ds.<DataSource>.<method>.xpp | df.<DS>.<Field>.<method>.xpp | ctrl.<Ctrl>....<method>.xpp
"""

import re
from typing import Dict, List, Optional, Tuple, Union

FrmStemParse = Union[
    Tuple[str, str],
    Tuple[str, str, str],
    Tuple[str, str, str, str],
    Tuple[str, List[str], str],
]


def parse_frm_xpp_stem(stem: str) -> FrmStemParse:
    if "__dup" in stem:
        stem = stem.rsplit("__dup", 1)[0]
    parts = stem.split(".")
    if len(parts) == 1:
        return ("form", parts[0])
    if parts[0] == "ds" and len(parts) == 3:
        return ("ds", parts[1], parts[2])
    if parts[0] == "df" and len(parts) == 4:
        return ("df", parts[1], parts[2], parts[3])
    if parts[0] == "ctrl" and len(parts) >= 3:
        return ("ctrl", parts[1:-1], parts[-1])
    return ("form", stem)


def frm_xpo_method_name(stem_parse: FrmStemParse) -> str:
    if stem_parse[0] == "form":
        return stem_parse[1]
    if stem_parse[0] == "ds":
        return stem_parse[2]
    if stem_parse[0] == "df":
        return stem_parse[3]
    if stem_parse[0] == "ctrl":
        return stem_parse[2]
    return str(stem_parse[-1])


def _make_frm_file_key(stack: List[Tuple[str, str]], method_name: str) -> str:
    if len(stack) <= 1:
        return method_name
    tail = stack[1:]
    if tail[-1][0] == "field":
        ds = next((n for k, n in tail if k == "ds"), None)
        fld = tail[-1][1]
        if ds:
            return f"df.{ds}.{fld}.{method_name}"
        return f"df._.{fld}.{method_name}"
    if tail[-1][0] == "ds":
        return f"ds.{tail[-1][1]}.{method_name}"
    ctrls = [n for k, n in tail if k == "ctrl" and n]
    if ctrls:
        return "ctrl." + ".".join(ctrls) + "." + method_name
    return method_name


def extract_form_all_sources(form_content: str, _clean_code) -> Dict[str, str]:
    text = form_content.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    methods: Dict[str, str] = {}
    stack: List[Tuple[str, str]] = [("form", "")]

    i = 0
    in_methods = False
    capturing = False
    capture_lines: List[str] = []
    current_method: Optional[str] = None

    while i < len(lines):
        line = lines[i]
        st = line.strip()

        if capturing:
            if st == "ENDSOURCE":
                raw = "\n".join(capture_lines)
                cleaned = _clean_code(raw)
                if current_method:
                    key = _make_frm_file_key(stack, current_method)
                    if key in methods:
                        n = 2
                        while f"{key}__dup{n}" in methods:
                            n += 1
                        key = f"{key}__dup{n}"
                    methods[key] = cleaned
                capturing = False
                current_method = None
                i += 1
                continue
            capture_lines.append(line)
            i += 1
            continue

        if in_methods:
            m = re.match(r"^(\s*)SOURCE\s+#(\w+)\s*$", line, re.IGNORECASE)
            if m:
                current_method = m.group(2)
                capturing = True
                capture_lines = []
                i += 1
                continue
            if st == "ENDMETHODS":
                in_methods = False
            i += 1
            continue

        if st == "DATASOURCE":
            stack.append(("ds", ""))
        elif st == "ENDDATASOURCE":
            if stack and stack[-1][0] == "ds":
                stack.pop()
        elif re.match(r"^DATAFIELD\s+\w+", st) and not st.startswith("ENDDATAFIELD"):
            mf = re.match(r"^DATAFIELD\s+(\w+)", st, re.IGNORECASE)
            if mf:
                stack.append(("field", mf.group(1)))
        elif st == "ENDDATAFIELD":
            if stack and stack[-1][0] == "field":
                stack.pop()
        elif re.match(r"^CONTROL\s+\w", st):
            stack.append(("ctrl", ""))
        elif st == "ENDCONTROL":
            if stack and stack[-1][0] == "ctrl":
                stack.pop()
        elif st.startswith("Name ") and "#" in st:
            mm = re.search(r"Name\s+#(\w+)", st)
            if mm and stack:
                kind, _ = stack[-1]
                if kind in ("ds", "ctrl"):
                    stack[-1] = (kind, mm.group(1))
        elif st == "METHODS":
            in_methods = True
        elif st == "ENDMETHODS":
            in_methods = False

        i += 1

    return methods


def _tok_opens_line(s: str, tok: str) -> bool:
    su = s.strip().upper()
    tu = tok.upper()
    return su == tu or su.startswith(tu + " ")


def _take_lines_block(
    lines: List[str], start_i: int, open_tok: str, close_tok: str
) -> Tuple[Optional[List[str]], int]:
    depth = 0
    j = start_i
    c = close_tok.upper()
    while j < len(lines):
        s = lines[j].strip()
        su = s.upper()
        if _tok_opens_line(s, open_tok):
            depth += 1
        elif su == c:
            depth -= 1
            if depth == 0:
                return lines[start_i : j + 1], j
        j += 1
    return None, -1


def _slice_datasource_by_name(full: str, ds_name: str) -> Optional[str]:
    lines = full.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    while i < len(lines):
        if _tok_opens_line(lines[i], "DATASOURCE"):
            block_lines, end_i = _take_lines_block(lines, i, "DATASOURCE", "ENDDATASOURCE")
            if not block_lines:
                return None
            block = "\n".join(block_lines)
            if re.search(rf"Name\s+#{re.escape(ds_name)}\b", block):
                return block
            i = end_i + 1
            continue
        i += 1
    return None


def _slice_datafield(ds_block: str, field_name: str) -> Optional[str]:
    lines = ds_block.split("\n")
    i = 0
    pat = re.compile(rf"^DATAFIELD\s+{re.escape(field_name)}\s*$", re.IGNORECASE)
    while i < len(lines):
        if pat.match(lines[i].strip()):
            block_lines, _ = _take_lines_block(lines, i, "DATAFIELD", "ENDDATAFIELD")
            if block_lines:
                return "\n".join(block_lines)
        i += 1
    return None


def _extract_one_control_block(text: str, ctrl_match_start: int) -> Optional[str]:
    rest = text[ctrl_match_start:]
    lines = rest.split("\n")
    depth = 0
    acc: List[str] = []
    for line in lines:
        st = line.strip()
        acc.append(line)
        if re.match(r"^CONTROL\s+\w", st, re.IGNORECASE):
            depth += 1
        elif st.upper() == "ENDCONTROL":
            depth -= 1
            if depth == 0:
                return "\n".join(acc)
    return None


def _find_control_block_recursive(content: str, names: List[str]) -> Optional[str]:
    if not names:
        return None
    rx_ctrl = re.compile(r"^\s*CONTROL\s+\w+", re.MULTILINE | re.IGNORECASE)
    pos = 0
    while True:
        m = rx_ctrl.search(content, pos)
        if not m:
            return None
        block = _extract_one_control_block(content, m.start())
        if not block:
            pos = m.end()
            continue
        if re.search(rf"Name\s+#{re.escape(names[0])}\b", block):
            if len(names) == 1:
                return block
            nested = _find_control_block_recursive(block, names[1:])
            if nested:
                return nested
        pos = m.end()


def _find_source_block_naive(element_content: str, method_name: str) -> Optional[str]:
    source_pattern = (
        rf"^\s*SOURCE\s+#{re.escape(method_name)}\s*(?:\r?\n)(.*?)^\s*ENDSOURCE"
    )
    match = re.search(source_pattern, element_content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(0)
    lines = element_content.splitlines(keepends=True)
    name_lower = method_name.lower()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if "SOURCE #" in line and "#" in line:
            after_hash = line.split("#", 1)[-1].strip()
            if after_hash.strip().lower() == name_lower:
                start_i = idx
                idx += 1
                while idx < len(lines):
                    if lines[idx].strip() == "ENDSOURCE":
                        return "".join(lines[start_i : idx + 1])
                    idx += 1
                return None
        idx += 1
    return None


def find_frm_source_block(full_element: str, file_stem: str) -> Optional[str]:
    parsed = parse_frm_xpp_stem(file_stem)
    xpo_name = frm_xpo_method_name(parsed)

    if parsed[0] == "form":
        return _find_source_block_naive(full_element, xpo_name)

    if parsed[0] == "ds":
        _, ds_name, _ = parsed
        ds_block = _slice_datasource_by_name(full_element, ds_name)
        if not ds_block:
            return None
        return _find_source_block_naive(ds_block, xpo_name)

    if parsed[0] == "df":
        _, ds_name, field_name, _ = parsed
        ds_block = _slice_datasource_by_name(full_element, ds_name)
        if not ds_block:
            return None
        fld_block = _slice_datafield(ds_block, field_name)
        if not fld_block:
            return None
        return _find_source_block_naive(fld_block, xpo_name)

    if parsed[0] == "ctrl":
        _, path_list, _ = parsed
        ctrl_block = _find_control_block_recursive(full_element, list(path_list))
        if not ctrl_block:
            return None
        return _find_source_block_naive(ctrl_block, xpo_name)

    return _find_source_block_naive(full_element, xpo_name)
