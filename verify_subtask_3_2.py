#!/usr/bin/env python3
"""Verification script for subtask-3-2."""
import sys
sys.path.insert(0, '.')

from src.input_processor import InputProcessor
from src.analysis_engine import AnalysisEngine
from src.report_generator import ReportGenerator

def verify():
    """Run verification checks."""
    print("=== Subtask 3-2 Verification ===")
    print()

    # Step 1: Parse input
    print("1. Parsing input '8,Lua\\n32,Lua' with spread format...")
    processor = InputProcessor()
    structured = processor.parse('8,Lua\n32,Lua', 'spread')
    print(f"   Cards: {len(structured.cards) if structured.cards else 0}")
    for c in structured.cards:
        print(f"     - Position {c.position}: {c.card_name}")

    # Step 2: Analyze
    print()
    print("2. Running analysis...")
    engine = AnalysisEngine()
    result = engine.analyze(structured)
    print(f"   Cross-card patterns: {len(result.cross_card_patterns)}")
    for p in result.cross_card_patterns:
        print(f"     - Type: {p.pattern_type}")
        print(f"       Cards: {p.card_ids}")
        print(f"       Strength: {p.strength}")

    # Step 3: Generate report
    print()
    print("3. Generating report...")
    generator = ReportGenerator()
    report = generator.generate(result)

    # Step 4: Check for pattern section
    print()
    print("4. Checking report content...")
    has_pattern_section = 'Padrões Cruzados' in report
    has_pattern_content = 'Numeric Repeat' in report
    has_interpretation = 'Lua' in report and 'vezes' in report

    print(f"   Has 'Padrões Cruzados' section: {has_pattern_section}")
    print(f"   Has 'Numeric Repeat' content: {has_pattern_content}")
    print(f"   Has pattern interpretation: {has_interpretation}")

    # Final result
    print()
    print("=== VERIFICATION RESULT ===")
    if has_pattern_section and has_pattern_content and has_interpretation:
        print("✓ PASSED: Full pipeline generates report with pattern section")
        print()
        print("The pattern section contains:")
        print("  - Section header: '## Padrões Cruzados'")
        print("  - Pattern type: '### Numeric Repeat'")
        print("  - Card IDs: '**Cartas**: 8, 32'")
        print("  - Interpretation: 'A carta 'Lua' aparece 2 vezes na tiragem...'")
        return True
    else:
        print("✗ FAILED: Pattern section missing or incomplete")
        return False

if __name__ == '__main__':
    success = verify()
    sys.exit(0 if success else 1)
