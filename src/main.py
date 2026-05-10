"""CLI entry point — Sistema de Clareza Simbólico-Estratégica."""

import argparse
import logging
import sys

from src.input_processor import InputProcessor, ParseError
from src.analysis_engine import AnalysisEngine
from src.boundaries import apply_guardrails
from src.report_generator import ReportGenerator
from src.database import SessionDB, DatabaseError
from src.commands.history import run_history as history_run
from src.commands.view import run_view as view_run

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _is_valid_file_path(path: str) -> bool:
    """Verifica se uma string parece ser um caminho de arquivo válido.

    Considera caminho válido se:
    - O arquivo existe no filesystem
    - A extensão é .csv ou .txt

    Args:
        path: String a verificar.

    Returns:
        True se parece ser um caminho de arquivo CSV/TXT válido.
    """
    import os

    if not path:
        return False

    # Verificar se o arquivo existe
    if os.path.isfile(path):
        return True

    # Verificar extensões comuns para arquivos de entrada
    valid_extensions = (".csv", ".txt")
    return any(path.lower().endswith(ext) for ext in valid_extensions)


def _extract_card_names(structured) -> list[str]:
    """Extrai lista de nomes de cartas de um StructuredInput.

    Args:
        structured: Input processado do InputProcessor.

    Returns:
        Lista de nomes de cartas (vazia se não houver cartas).
    """
    if not structured.cards:
        return []
    return [card.card_name for card in structured.cards]


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
        "--template", "-t",
        default=None,
        help="Template de tiragem predefinido (3-card, celtic-cross). "
             "Disponível apenas para --format spread.",
    )

    # subcommand: history
    history_parser = subparsers.add_parser("history", help="Listar sessões anteriores")
    history_parser.add_argument(
        "--search", "-s",
        default=None,
        help="Filtrar sessões por palavra-chave no texto ou cartas",
    )
    history_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="Número máximo de sessões a exibir (padrão: 10)",
    )

    # subcommand: view
    view_parser = subparsers.add_parser("view", help="Exibir relatório de uma sessão salva")
    view_parser.add_argument(
        "session_id",
        type=int,
        help="ID da sessão cujo relatório será exibido",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "analyze":
        run_analyze(args.input, args.format, args.output, args.template)

    if args.command == "history":
        history_run(args.search, args.limit)

    if args.command == "view":
        view_run(args.session_id)


def run_analyze(
    raw_input: str,
    format: str,
    output_path: str | None,
    template: str | None,
) -> None:
    """Executa o pipeline completo de análise.

    Pipeline: input_processor → analysis_engine → boundaries → report_generator

    Args:
        raw_input: Conteúdo bruto de entrada.
        format: Formato de entrada ("text", "spread", "symbols").
        output_path: Caminho opcional para salvar o relatório em .md.
        template: Template de tiragem predefinido (apenas para format="spread").
    """
    # Validação: --template só é válido com --format spread
    if template is not None and format != "spread":
        logger.error("O argumento --template só é válido com --format spread")
        print(
            "Erro: --template requer --format spread",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        # Fase 1: Parse e estruturação do input
        logger.info("Processando entrada: format=%s, length=%d", format, len(raw_input))
        processor = InputProcessor()
        # Verificar se raw_input é um caminho de arquivo válido
        if _is_valid_file_path(raw_input):
            structured = processor.parse_from_file(raw_input, template)
            logger.info("Entrada lida de arquivo: %s", raw_input)
        else:
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

        # Salvar sessão no banco de dados
        try:
            db = SessionDB()
            card_names = _extract_card_names(structured)
            session_id = db.save_session(
                input_text=raw_input,
                cards=card_names,
                format=format,
                report_path=output_path,
            )
            logger.info("Sessão %d salva no banco de dados", session_id)
        except DatabaseError as e:
            logger.warning("Falha ao salvar sessão no banco: %s", e)

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