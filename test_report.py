#!/usr/bin/env python3
"""Test script for report generation."""
import sys
sys.path.insert(0, 'src')

from clareza.report import generate_report
result = generate_report([1, 7], 'Career change')
print(result)
