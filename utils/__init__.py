#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils модуль для Dynamics AX X++ Development Assistant
"""

from .xpo_utils import (
    clean_xpo_code,
    format_code_for_xpo,
    extract_element_name,
    extract_methods,
    extract_properties,
    find_labels_in_text,
    parse_xpo_element,
    find_xpo_elements,
    get_element_content,
    ELEMENT_PATTERNS,
    XPO_ELEMENT_PATTERN,
    SOURCE_PATTERN,
    PROPERTIES_PATTERN,
    LABEL_PATTERN,
    LABEL_PATTERN2,
)

__all__ = [
    'clean_xpo_code',
    'format_code_for_xpo',
    'extract_element_name',
    'extract_methods',
    'extract_properties',
    'find_labels_in_text',
    'parse_xpo_element',
    'find_xpo_elements',
    'get_element_content',
    'ELEMENT_PATTERNS',
    'XPO_ELEMENT_PATTERN',
    'SOURCE_PATTERN',
    'PROPERTIES_PATTERN',
    'LABEL_PATTERN',
    'LABEL_PATTERN2',
]
