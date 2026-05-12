#!/usr/bin/env python3
"""Test script to verify SessionAnnotation dataclass."""
import sys
sys.path.insert(0, '.')

try:
    from src.types import SessionAnnotation
    print("OK")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)