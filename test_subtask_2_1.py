#!/usr/bin/env python3
"""Test script to verify ReportGenerator has generate_with_diagram method."""

import sys
sys.path.insert(0, '.')

from src.report_generator import ReportGenerator
from src.types import CardPosition

rg = ReportGenerator()

# Check if generate_with_diagram exists
if hasattr(rg, 'generate_with_diagram'):
    print("True")
    sys.exit(0)
else:
    print("False")
    sys.exit(1)