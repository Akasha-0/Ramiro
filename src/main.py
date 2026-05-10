"""CLI entry point — Sistema de Clareza Simbólico-Estratégica."""

import argparse
import logging
import sys

from src.input_processor import InputProcessor, ParseError
from src.analysis_engine import AnalysisEngine
from src.arc_manager import ArcManager
from src.boundaries import apply_guardrails
from src.report_generator import ReportGenerator

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# CLI implementation
# ----------------------------------------------------------------------


def main() -> None:
    """Orquestra a análise simbólico-estratégica via CLI."""
    parser = argparse.ArgumentParser(
        description="Sistema de Clareza Simbólico-Estratégica",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # subcommand: analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analisar entrada e gerar relatório")
    analyze_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Texto, caminho para CSV, ou lista de símbolos separados por vírgula",
    )
    analyze_parser.add_argument(
        "--format", "-f",
        choices=["text", "spread", "symbols"],
        default="text",
        help="Formato da entrada (text, spread, symbols)",
    )
    analyze_parser.add_argument(
        "--output", "-o",
        default=None,
        help="Caminho do arquivo .md para salvar o relatório",
    )
    analyze_parser.add_argument(
        "--arc", "-a",
        default=None,
        help="Identificador do arco/trajetória para rastreamento de milestones",
    )

    # subcommand: arcs
    arcs_parser = subparsers.add_parser("arcs", help="Listar todos os arcos de reflexão")

    # subcommand: arc
    arc_parser = subparsers.add_parser("arc", help="Operações em um arco específico")
    arc_subparsers = arc_parser.add_subparsers(dest="subcommand", help="Subcomandos do arco")

    # arc summary
    arc_summary_parser = arc_subparsers.add_parser("summary", help="Mostrar sumário de um arco")
    arc_summary_parser.add_argument(
        "name",
        help="Nome do arco",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "analyze":
        run_analyze(args.input, args.format, args.output, args.arc)
    elif args.command == "arcs":
        run_arcs_list()
    elif args.command == "arc":
        if args.subcommand == "summary":
            run_arc_summary(args.name)
        else:
            arc_parser.print_help()
            sys.exit(1)


def run_analyze(raw_input: str, format: str, output_path: str | None, arc: str | None = None) -> None:
    """Executa o pipeline completo de análise.

    Pipeline: input_processor → analysis_engine → boundaries → report_generator

    Args:
        raw_input: Conteúdo bruto de entrada.
        format: Formato de entrada ("text", "spread", "symbols").
        output_path: Caminho opcional para salvar o relatório em .md.
        arc: Identificador opcional do arco/trajetória para rastreamento de milestones.
    """
    try:
        # Fase 1: Parse e estruturação do input
        logger.info("Processando entrada: format=%s, length=%d", format, len(raw_input))
        processor = InputProcessor()
        structured = processor.parse(raw_input, format)
        logger.info(
            "Input processado: keywords=%s, cards=%d",
            len(structured.keywords) if structured.keywords else 0,
            len(structured.cards) if structured.cards else 0,
        )

        # Fase 2: Análise simbólico-estratégica
        logger.info("Executando análise simbólica")
        engine = AnalysisEngine()
        analysis_result = engine.analyze(structured)
        logger.info(
            "Análise concluída: %d temas, %d riscos, %d decisões",
            len(analysis_result.themes),
            len(analysis_result.risks),
            len(analysis_result.decisions),
        )

        # Fase 3: Geração do relatório Markdown
        logger.info("Gerando relatório")
        generator = ReportGenerator()
        report_md = generator.generate(analysis_result)

        # Fase 4: Aplicação de guardrails éticos
        logger.info("Aplicando guardrails éticos")
        validated = apply_guardrails(report_md, analysis_result)

        if validated.disclaimer_flags:
            logger.warning(
                "Disclaimer ético aplicado — flags detectadas: %s",
                validated.disclaimer_flags,
            )

        # Fase 5: Output
        if output_path:
            _save_report(output_path, validated.content)
            print(f"Relatório salvo em: {output_path}", file=sys.stderr)
            sys.exit(0)
        else:
            print(validated.content)
            sys.exit(0)

    except ParseError as e:
        logger.error("Erro no parse da entrada: %s", e)
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        logger.error("Valor inválido: %s", e)
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        logger.exception("Erro inesperado durante análise")
        print(f"Erro interno: {e}", file=sys.stderr)
        sys.exit(1)


def _save_report(path: str, content: str) -> None:
    """Salva o relatório em um arquivo Markdown.

    Args:
        path: Caminho do arquivo de destino.
        content: Conteúdo Markdown a salvar.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Relatório salvo em %s (%d bytes)", path, len(content))
    except OSError as e:
        logger.error("Falha ao salvar relatório em %s: %s", path, e)
        raise


def run_arcs_list() -> None:
    """Lista todos os arcos de reflexão armazenados."""
    try:
        manager = ArcManager()
        arcs = manager.list_arcs()

        if not arcs:
            print("Nenhum arco encontrado. Use 'clar.za analyze --arc <nome>' para criar um.")
            sys.exit(0)

        print(f"# Arcos de Reflexão ({len(arcs)} total)\n")
        for arc in arcs:
            session_count = len(arc.sessions)
            print(f"## {arc.name}")
            if arc.description:
                print(f"   {arc.description}")
            print(f"   Sessões: {session_count}")
            print(f"   Atualizado em: {arc.updated_at.strftime('%Y-%m-%d %H:%M')}")
            print()

    except Exception as e:
        logger.exception("Erro ao listar arcos")
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


def run_arc_summary(name: str) -> None:
    """Mostra o sumário de um arco de reflexão específico."""
    try:
        manager = ArcManager()
        summary = manager.generate_arc_summary(name)

        if summary is None:
            print(f"Arco não encontrado: {name}", file=sys.stderr)
            sys.exit(1)

        print(f"# Sumário do Arco: {name}\n")
        print(f"Total de sessões: {summary.total_sessions}")

        if summary.date_range:
            start = summary.date_range[0].strftime("%Y-%m-%d")
            end = summary.date_range[1].strftime("%Y-%m-%d")
            print(f"Período: {start} a {end}")

        if summary.top_themes:
            print(f"\nTemas principais: {', '.join(summary.top_themes)}")

        if summary.top_cards:
            print(f"Cartas principais: {', '.join(summary.top_cards)}")

    except Exception as e:
        logger.exception("Erro ao gerar sumário do arco")
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()