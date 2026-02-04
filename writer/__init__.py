#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для обратной записи XPP файлов в XPO
"""

import sys
from pathlib import Path

# Импортируем из корня проекта
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from xpo_writer import XPOWriter

__all__ = ['XPOWriter']

