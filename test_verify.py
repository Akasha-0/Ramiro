#!/usr/bin/env python3
"""Verification script for _format_plugin_sections()"""
from src.report_generator import ReportGenerator

rg = ReportGenerator()
sections = rg._format_plugin_sections([])
print("OK" if sections == "" else f"FAIL: {repr(sections)}")

# Test with plugins enabled
rg_with_plugins = ReportGenerator(include_plugin_sections=True)
sections2 = rg_with_plugins._format_plugin_sections([])
print("OK" if sections2 == "" else f"FAIL: {repr(sections2)}")

# Test with plugin sections
plugin_data = [{"title": "Teste", "content": "Conteúdo de teste"}]
result = rg_with_plugins._format_plugin_sections(plugin_data)
print("OK" if "## Teste" in result and "Conteúdo de teste" in result else f"FAIL: {repr(result)}")
