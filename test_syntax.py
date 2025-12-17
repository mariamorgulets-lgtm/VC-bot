#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to check syntax of financial_model.py"""

import sys

try:
    with open('financial_model.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    compile(code, 'financial_model.py', 'exec')
    print("✓ Синтаксис файла корректен!")
    print("✓ Файл готов к запуску")
except SyntaxError as e:
    print(f"✗ Синтаксическая ошибка на строке {e.lineno}:")
    print(f"  {e.text}")
    print(f"  {e.msg}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Ошибка: {e}")
    sys.exit(1)



