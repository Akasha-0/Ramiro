"""CLI entry point — Sistema de Clareza Simbólico-Estratégica."""

import argparse
import logging
import sys

from src.config import load_config
from src.input_processor import InputProcessor, ParseError
from src.analysis_engine import AnalysisEngine
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


def _get_effective_args(args: argparse.Namespace) -> argparse.Namespace:
    """Aplica valores default da configuração quando argumentos CLI não são fornecidos.

    A precedência é: argumento CLI > configuração > default

    Args:
        args: Namespace de argumentos parseados (com default=None para argumentos opcionais).

    Returns:
        Namespace com valores efetivos aplicados.
    """
    config = load_config()

    effective_format = args.format if args.format is not None else config.default_report_format

    return argparse.Namespace(
        format=effective_format,
        output=args.output,
    )


def main() -> None:
    """Orquestra a análise simbólico-estratégica via CLI."""
    parser = argparse.ArgumentParser(
        description="Sistema de Clareza Simbólico-Estratégica",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Exibir configuração atual do sistema",
    )

    # analyze subcommand
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

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

    args = parser.parse_args()

    if args.show_config:
        run_show_config()
        sys.exit(0)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "analyze":
        effective = _get_effective_args(args)
        run_analyze(args.input, effective.format, effective.output)


def run_show_config() -> None:
    """Exibe a configuração atual do sistema."""
    config = load_config()
    print(f"default_output_dir: {config.default_output_dir}")
    print(f"default_report_format: {config.default_report_format}")
    print(f"default_language: {config.default_language}")
    print(f"session_history_dir: {config.session_history_dir}")
    print(f"auto_save_sessions: {config.auto_save_sessions}")
    print(f"quiet_mode: {config.quiet_mode}")


def run_analyze(raw_input: str, format: str, output_path: str | None) -> None:
    """Executa o pipeline completo de análise.

    Pipeline: input_processor → analysis_engine → boundaries → report_generator

    Args:
        raw_input: Conteúdo bruto de entrada.
        format: Formato de entrada ("text", "spread", "symbols").
        output_path: Caminho opcional para salvar o relatório em .md.
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


if __name__ == "__main__":
    main()