#!/usr/bin/env python3
"""Verify custom template override in report generation."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, './src')

from src.template_loader import TemplateLoader, TemplateClarezaError
from src.template_engine import TemplateEngine
from src.report_generator import ReportGenerator
from src.types import AnalysisResult


def main():
    all_passed = True

    # Test 1: Custom template sections appear in correct order
    print("=== Test 1: Custom template section ordering ===")
    custom_yaml = """
template_id: test-ordered
name: Teste Ordenação
description: Template para testar ordenação
sections:
  - id: plano
    title: Plano Prático
    order: 5
    content_template: "{practical_plan}"
  - id: diagnostico
    title: Diagnóstico
    order: 1
    content_template: "{diagnosis}"
  - id: interpretacao
    title: Interpretação Simbólica
    order: 2
    content_template: "{symbolic_interpretation}"
  - id: riscos
    title: Riscos Identificados
    order: 3
    content_template: "{risks}"
  - id: decisoes
    title: Caminhos de Decisão
    order: 4
    content_template: "{decisions}"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(custom_yaml)
        temp_path = f.name

    try:
        loader = TemplateLoader()
        template = loader.load_from_file(Path(temp_path))

        # Check sections are in correct order
        expected_order = [1, 2, 3, 4, 5]
        actual_order = [s.order for s in template.sections]

        t1a_pass = actual_order == expected_order
        print(f"  Sections sorted by order: {'PASS' if t1a_pass else 'FAIL'}")
        if not t1a_pass:
            all_passed = False
            print(f"    Expected: {expected_order}")
            print(f"    Actual: {actual_order}")

        # Check section IDs match expected
        expected_ids = ["diagnostico", "interpretacao", "riscos", "decisoes", "plano"]
        actual_ids = [s.id for s in template.sections]
        t1b_pass = actual_ids == expected_ids
        print(f"  Section IDs in correct order: {'PASS' if t1b_pass else 'FAIL'}")
        if not t1b_pass:
            all_passed = False
            print(f"    Expected: {expected_ids}")
            print(f"    Actual: {actual_ids}")

    finally:
        Path(temp_path).unlink()

    # Test 2: Report generated with custom template has correct section order
    print("\n=== Test 2: Report generation with custom template ===")
    analysis = AnalysisResult(
        diagnosis="Teste de diagnóstico",
        themes=["trabalho"],
        risks=["Risco 1"],
        decisions=["Decisão 1"],
        practical_plan="Plano de ação",
    )

    custom_yaml2 = """
template_id: test-order
name: Teste Order
sections:
  - id: plano
    title: Primeiro Plano
    order: 1
    content_template: "PLANO: {practical_plan}"
  - id: diagnostico
    title: Segundo Diagnóstico
    order: 2
    content_template: "DIAG: {diagnosis}"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(custom_yaml2)
        temp_path2 = f.name

    try:
        loader2 = TemplateLoader()
        template2 = loader2.load_from_file(Path(temp_path2))

        generator = ReportGenerator()
        report = generator.generate(analysis, custom_template=template2)

        # Find positions of section markers in report
        plano_pos = report.find("## Primeiro Plano")
        diag_pos = report.find("## Segundo Diagnóstico")

        t2_pass = plano_pos != -1 and diag_pos != -1 and plano_pos < diag_pos
        print(f"  Custom template sections in report: {'PASS' if t2_pass else 'FAIL'}")
        if not t2_pass:
            all_passed = False
            print(f"    Plano pos: {plano_pos}, Diag pos: {diag_pos}")
        else:
            print(f"  Section order correct (Plano before Diagnóstico): {'PASS' if t2_pass else 'FAIL'}")

    finally:
        Path(temp_path2).unlink()

    # Test 3: Reordered sections appear in report in correct order
    print("\n=== Test 3: Reordered sections in report ===")
    analysis3 = AnalysisResult(
        diagnosis="Diagnóstico padrão",
        themes=["teste"],
        practical_plan="Plano padrão",
        risks=["Risco padrão"],
        decisions=["Decisão padrão"],
    )

    # Create template with Plano first, Diagnóstico second
    custom_yaml3 = """
template_id: reversed
name: Reversed Order
sections:
  - id: plano
    title: PLANO FIRST
    order: 1
    content_template: "{practical_plan}"
  - id: diagnostico
    title: DIAG SECOND
    order: 2
    content_template: "{diagnosis}"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(custom_yaml3)
        temp_path3 = f.name

    try:
        loader3 = TemplateLoader()
        template3 = loader3.load_from_file(Path(temp_path3))

        generator3 = ReportGenerator()
        report3 = generator3.generate(analysis3, custom_template=template3)

        plano_first_pos = report3.find("## PLANO FIRST")
        diag_second_pos = report3.find("## DIAG SECOND")

        t3_pass = plano_first_pos != -1 and diag_second_pos != -1 and plano_first_pos < diag_second_pos
        print(f"  Reordered sections (Plano before Diag): {'PASS' if t3_pass else 'FAIL'}")
        if not t3_pass:
            all_passed = False
            print(f"    PLANO FIRST pos: {plano_first_pos}")
            print(f"    DIAG SECOND pos: {diag_second_pos}")

    finally:
        Path(temp_path3).unlink()

    # Test 4: Custom sections with custom content
    print("\n=== Test 4: Custom section content ===")
    custom_yaml4 = """
template_id: custom-content
name: Custom Content
sections:
  - id: custom1
    title: Seção Personalizada
    order: 1
    content_template: "CONTEÚDO: {diagnosis}"
  - id: custom2
    title: Outra Seção
    order: 2
    content_template: "TEMAS: {symbolic_interpretation}"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(custom_yaml4)
        temp_path4 = f.name

    try:
        loader4 = TemplateLoader()
        template4 = loader4.load_from_file(Path(temp_path4))

        generator4 = ReportGenerator()
        report4 = generator4.generate(analysis, custom_template=template4)

        t4a_pass = "Seção Personalizada" in report4
        print(f"  Custom section title appears: {'PASS' if t4a_pass else 'FAIL'}")
        if not t4a_pass:
            all_passed = False

        t4b_pass = "CONTEÚDO:" in report4
        print(f"  Custom content template renders: {'PASS' if t4b_pass else 'FAIL'}")
        if not t4b_pass:
            all_passed = False

    finally:
        Path(temp_path4).unlink()

    # Test 5: Invalid template syntax produces clear error
    print("\n=== Test 5: Invalid template syntax error ===")
    invalid_yaml = """
template_id: invalid
name: Invalid Template
sections: not_a_list
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(invalid_yaml)
        temp_path5 = f.name

    try:
        loader5 = TemplateLoader()
        try:
            template5 = loader5.load_from_file(Path(temp_path5))
            print(f"  Invalid template raises error: FAIL (no exception raised)")
            all_passed = False
        except TemplateClarezaError as e:
            print(f"  Invalid template raises error: PASS")
            # Check for clear error message
            error_str = str(e)
            t5b_pass = len(error_str) > 0
            print(f"  Error message is clear: {'PASS' if t5b_pass else 'FAIL'}")
            if not t5b_pass:
                all_passed = False
    finally:
        Path(temp_path5).unlink()

    # Test 6: Default template behavior unchanged
    print("\n=== Test 6: Default template behavior ===")
    generator6 = ReportGenerator()
    report6 = generator6.generate(analysis, custom_template=None)

    t6a_pass = "# Relatório de Análise" in report6
    print(f"  Default report header: {'PASS' if t6a_pass else 'FAIL'}")
    if not t6a_pass:
        all_passed = False

    t6b_pass = "## Diagnóstico" in report6
    print(f"  Default section appears: {'PASS' if t6b_pass else 'FAIL'}")
    if not t6b_pass:
        all_passed = False

    t6c_pass = "Clareza Simbólico-Estratégica" in report6
    print(f"  Default footer present: {'PASS' if t6c_pass else 'FAIL'}")
    if not t6c_pass:
        all_passed = False

    # Summary
    print("\n" + "="*50)
    if all_passed:
        print("ALL TEMPLATE VERIFICATION TESTS: PASS")
        return 0
    else:
        print("SOME TESTS FAILED: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())