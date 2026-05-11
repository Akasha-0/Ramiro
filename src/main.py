"""CLI entry point — Sistema de Clareza Simbólico-Estratégica."""

import argparse
import logging
import os
import sys

from src.input_processor import InputProcessor, ParseError
from src.analysis_engine import AnalysisEngine
from src.boundaries import apply_guardrails
from src.report_generator import ReportGenerator
from src.logging_utils import create_progress
from src.config import load_config
from src.exceptions import (
    ClarezaError,
    FileNotFoundClarezaError,
    ParseClarezaError,
    TemplateClarezaError,
    ValidationClarezaError,
)

# ----------------------------------------------------------------------
# Error messages — mensagens de erro em português com orientação
# ----------------------------------------------------------------------

ERROR_MESSAGES = {
    "no_command": (
        "Nenhum comando especificado. Use 'clareza analyze' para começar.\n"
        "Execute 'clareza --help' para ver os comandos disponíveis."
    ),
    "template_requires_spread": (
        "O argumento --template só é válido com --format spread.\n"
        "Solução: Use --format spread junto com --template, ou omita --template.\n"
        "Exemplo: clareza analyze -i 'trabalho família' -f spread -t 3-card"
    ),
    "file_not_found": (
        "Arquivo não encontrado. Verifique se o caminho está correto.\n"
        "Dica: Caminhos válidos devem ter extensão .csv ou .txt\n"
        "Exemplo: clareza analyze -i dados/tiragem.csv -f spread"
    ),
    "parse_error": (
        "Não foi possível processar a entrada. Verifique o formato.\n"
        "Para texto livre: clareza analyze -i 'sua pergunta aqui' -f text\n"
        "Para símbolos: clareza analyze -i 'Casa, Estrela, Sol' -f symbols\n"
        "Para tiragem CSV:clareza analyze -i arquivo.csv -f spread"
    ),
    "validation_error": (
        "A entrada contém dados inválidos que não puderam ser processados.\n"
        "Verifique se os símbolos ou formato estão corretos.\n"
        "Use --verbose para ver detalhes técnicos do erro."
    ),
    "unexpected_error": (
        "Ocorreu um erro inesperado durante a análise.\n"
        "Tente novamente com uma entrada diferente.\n"
        "Se o problema persistir, use --verbose para ver detalhes técnicos."
    ),
    "output_write_error": (
        "Não foi possível salvar o relatório no caminho especificado.\n"
        "Verifique se você tem permissão de escrita no diretório.\n"
        "Dica: Tente usar um caminho absoluto ou um diretório diferente."
    ),
}

# ----------------------------------------------------------------------
# Output styling — suporte a cores para mensagens de erro e output
# ----------------------------------------------------------------------

def _get_error_output() -> 'ColoredOutput':
    """Retorna instância de ColoredOutput para mensagens de erro.

    Returns:
        ColoredOutput configurado com base no ambiente atual.
    """
    from src.logging_utils import ColoredOutput
    return ColoredOutput()


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


# ----------------------------------------------------------------------
# CLI implementation
# ----------------------------------------------------------------------


def main() -> None:
    """Orquestra a análise simbólico-estratégica via CLI."""
    parser = argparse.ArgumentParser(
        description="Sistema de Clareza Simbólico-Estratégica",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Global flag for verbose mode - can be placed before or after subcommand
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ativa output detalhado de debug",
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
        choices=["text", "spread", "symbols", "verbose"],
        default="text",
        help="Formato da entrada (text, spread, symbols, verbose)",
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
    analyze_parser.add_argument(
        "--report-format",
        default=None,
        choices=["compact", "default"],
        help="Formato do relatório de saída (compact ou default). "
             "Se omitido, usa o padrão da configuração.",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        colored = _get_error_output()
        print(colored.error("Erro: " + ERROR_MESSAGES["no_command"]), file=sys.stderr)
        sys.exit(1)

    # Get verbose from main parser (allows --verbose before or after subcommand)
    verbose = getattr(args, 'verbose', False) or getattr(args, 'v', False)

    if args.command == "analyze":
        run_analyze(args.input, args.format, args.output, args.template, verbose, args.report_format)


def run_analyze(
    raw_input: str,
    format: str,
    output_path: str | None,
    template: str | None,
    verbose: bool = False,
    report_format: str | None = None,
) -> None:
    """Executa o pipeline completo de análise.

    Pipeline: input_processor → analysis_engine → boundaries → report_generator

    Args:
        raw_input: Conteúdo bruto de entrada.
        format: Formato de entrada ("text", "spread", "symbols").
        output_path: Caminho opcional para salvar o relatório em .md.
        template: Template de tiragem predefinido (apenas para format="spread").
        verbose: Se True, ativa logging detalhado (DEBUG level).
        report_format: Formato do relatório de saída ("compact" ou "default").
            Se None, usa config.default_report_format.
    """
    # Configure verbose logging if requested
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Carregar configuração e resolver formato do relatório
    config = load_config()
    if report_format is None:
        report_format = config.default_report_format

    # Validação: --template só é válido com --format spread
    if template is not None and format != "spread":
        logger.error("O argumento --template só é válido com --format spread")
        colored = _get_error_output()
        print(colored.error("Erro: " + ERROR_MESSAGES["template_requires_spread"]), file=sys.stderr)
        sys.exit(2)

    try:
        # Fase 1: Parse e estruturação do input
        logger.info("Processando entrada: format=%s, length=%d", format, len(raw_input))
        progress = create_progress(description="Processando entrada")
        progress.start()
        processor = InputProcessor()
        # Verificar se raw_input é um caminho de arquivo válido
        if _is_valid_file_path(raw_input):
            structured = processor.parse_from_file(raw_input, template)
            logger.info("Entrada lida de arquivo: %s", raw_input)
        else:
            structured = processor.parse(raw_input, format)
        progress.complete("Entrada processada")
        logger.info(
            "Input processado: keywords=%s, cards=%d",
            len(structured.keywords) if structured.keywords else 0,
            len(structured.cards) if structured.cards else 0,
        )

        # Fase 2: Análise simbólico-estratégica
        logger.info("Executando análise simbólica")
        progress = create_progress(description="Analisando símbolos")
        progress.start()
        engine = AnalysisEngine()
        analysis_result = engine.analyze(structured)
        progress.complete("Análise simbólica concluída")
        logger.info(
            "Análise concluída: %d temas, %d riscos, %d decisões",
            len(analysis_result.themes),
            len(analysis_result.risks),
            len(analysis_result.decisions),
        )

        # Fase 3: Geração do relatório Markdown
        logger.info("Gerando relatório")
        progress = create_progress(description="Gerando relatório")
        progress.start()
        generator = ReportGenerator()
        report_md = generator.generate(analysis_result, output_format=report_format)
        progress.complete("Relatório gerado")

        # Fase 4: Aplicação de guardrails éticos
        logger.info("Aplicando guardrails éticos")
        validated = apply_guardrails(report_md, analysis_result)

        if validated.disclaimer_flags:
            logger.warning(
                "Disclaimer ético aplicado — flags detectadas: %s",
                validated.disclaimer_flags,
            )

        # Fase 5: Output
        colored = _get_error_output()
        if output_path:
            _save_report(output_path, validated.content)
            print(colored.success(f"✓ Relatório salvo em: {output_path}"), file=sys.stderr)
            sys.exit(0)
        else:
            print(validated.content)
            sys.exit(0)

    except FileNotFoundClarezaError as e:
        logger.error("Arquivo não encontrado: %s", e.file_path)
        colored = _get_error_output()
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['file_not_found']}"), file=sys.stderr)
        if 'progress' in locals():
            progress.error("Erro no processamento")
        sys.exit(2)
    except ParseError as e:
        logger.error("Erro no parse da entrada: %s", e)
        colored = _get_error_output()
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['parse_error']}"), file=sys.stderr)
        if 'progress' in locals():
            progress.error("Erro no processamento")
        sys.exit(2)
    except TemplateClarezaError as e:
        logger.error("Template inválido: %s", e.template_name)
        colored = _get_error_output()
        available_hint = ""
        if e.available:
            available_hint = f"\nTemplates disponíveis: {', '.join(e.available)}"
        print(colored.error(f"✗ Erro: Template não encontrado: {e.template_name}{available_hint}"), file=sys.stderr)
        if 'progress' in locals():
            progress.error("Erro no processamento")
        sys.exit(2)
    except ValidationClarezaError as e:
        logger.error("Validação falhou: %s", e)
        colored = _get_error_output()
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['validation_error']}"), file=sys.stderr)
        if 'progress' in locals():
            progress.error("Erro no processamento")
        sys.exit(2)
    except ClarezaError as e:
        logger.error("Erro do sistema: %s", e)
        colored = _get_error_output()
        print(colored.error(f"✗ Erro: {e.message}"), file=sys.stderr)
        if 'progress' in locals():
            progress.error("Erro no processamento")
        sys.exit(2)
    except ValueError as e:
        logger.error("Valor inválido: %s", e)
        colored = _get_error_output()
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['validation_error']}"), file=sys.stderr)
        if 'progress' in locals():
            progress.error("Erro no processamento")
        sys.exit(2)
    except OSError as e:
        logger.error("Erro de sistema de arquivos: %s", e)
        colored = _get_error_output()
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['output_write_error']}"), file=sys.stderr)
        if 'progress' in locals():
            progress.error("Erro no processamento")
        sys.exit(2)
    except Exception as e:
        logger.exception("Erro inesperado durante análise")
        colored = _get_error_output()
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['unexpected_error']}"), file=sys.stderr)
        if 'progress' in locals():
            progress.error("Erro no processamento")
        sys.exit(1)


def _save_report(path: str, content: str) -> None:
    """Salva o relatório em um arquivo Markdown.

    Args:
        path: Caminho do arquivo de destino.
        content: Conteúdo Markdown a salvar.
    """
    import os

    colored = _get_error_output()

    # Verificar se o diretório existe ou pode ser criado
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
        except OSError as e:
            logger.error("Não foi possível criar o diretório %s: %s", dir_path, e)
            print(
                colored.error(f"✗ Erro: Não foi possível criar o diretório {dir_path!r}.\n"
                "Verifique se o caminho está correto e se você tem permissão."),
                file=sys.stderr,
            )
            raise

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Relatório salvo em %s (%d bytes)", path, len(content))
    except PermissionError as e:
        logger.error("Sem permissão para escrever em %s: %s", path, e)
        print(
            colored.error(f"✗ Erro: Sem permissão para salvar em {path!r}.\n"
            "Verifique as permissões do diretório."),
            file=sys.stderr,
        )
        raise
    except OSError as e:
        logger.error("Falha ao salvar relatório em %s: %s", path, e)
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['output_write_error']}"), file=sys.stderr)
        raise


if __name__ == "__main__":
    main()