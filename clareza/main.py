"""CLI entry point — Sistema de Clareza Simbólico-Estratégica."""

import argparse
import logging
import os
import sys

from clareza.input_processor import InputProcessor, ParseError
from clareza.analysis_engine import AnalysisEngine
from clareza.boundaries import apply_guardrails
from clareza.report_generator import ReportGenerator
from clareza.session_store import SessionStore
from clareza.arc_generator import ArcGenerator
from clareza.logging_utils import create_progress
from clareza.exceptions import (
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
    from clareza.logging_utils import ColoredOutput
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

    # Reject very short strings that cannot be file paths
    if len(path) < 5:
        return False

    # Reject strings that look like natural language text (have spaces + lowercase letters)
    # File paths typically don't have spaces mixed with lowercase words
    if " " in path and any(c.islower() for c in path):
        # Check if it looks like a sentence rather than a path
        words = path.split()
        if len(words) >= 2 and all(any(c.isalpha() for c in w) for w in words[:3]):
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
    analyze_parser.add_argument(
        "--tag", "-g",
        default=None,
        help="Tag para categorizar a sessão (ex: carreira, relacionamento). "
             "A sessão será armazenada para visualização futura do arco narrativo.",
    )
    analyze_parser.add_argument(
        "--save-session",
        action="store_true",
        help="Salvar esta sessão no histórico para consulta posterior.",
    )
    analyze_parser.add_argument(
        "--report-format", "-r",
        choices=["default", "compact", "verbose", "json"],
        default="default",
        help="Formato do relatório de saída (default, compact, verbose, json)",
    )

    # subcommand: arc
    arc_parser = subparsers.add_parser("arc", help="Visualizar arco narrativo entre sessões")
    arc_parser.add_argument(
        "--sessions", "-s",
        default=None,
        help="Lista de caminhos de arquivos de relatório separados por vírgula",
    )
    arc_parser.add_argument(
        "--tag", "-t",
        default=None,
        help="Tag para filtrar sessões (ex: carreira, relacionamento)",
    )
    arc_parser.add_argument(
        "--output", "-o",
        default=None,
        help="Caminho do arquivo .md para salvar a visualização",
    )
    arc_parser.add_argument(
        "--format", "-f",
        choices=["text", "chart"],
        default="text",
        help="Formato de saída (text, chart)",
    )

    # subcommand: history
    history_parser = subparsers.add_parser("history", help="Listar sessões salvas no histórico")
    history_parser.add_argument(
        "--tag", "-t",
        default=None,
        help="Filtrar por tag (ex: carreira, relacionamento)",
    )
    history_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=20,
        help="Número máximo de sessões a exibir (padrão: 20)",
    )

    # subcommand: session
    session_parser = subparsers.add_parser("session", help="Recuperar uma sessão pelo ID")
    session_parser.add_argument(
        "session_id",
        help="ID da sessão a recuperar",
    )

    # subcommand: compare
    compare_parser = subparsers.add_parser("compare", help="Comparar duas sessões")
    compare_parser.add_argument(
        "session_id_1",
        help="ID da primeira sessão",
    )
    compare_parser.add_argument(
        "session_id_2",
        help="ID da segunda sessão",
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
        run_analyze(args.input, args.format, args.output, args.template, verbose, args.tag, args.report_format, args.save_session)
    elif args.command == "arc":
        run_arc(args.sessions, args.output, args.format, verbose, args.tag)
    elif args.command == "history":
        run_history(args.tag, args.limit)
    elif args.command == "session":
        run_session(args.session_id)
    elif args.command == "compare":
        run_compare(args.session_id_1, args.session_id_2)


def run_history(tag: str | None, limit: int) -> None:
    """Lista sessões salvas no histórico."""
    store = SessionStore()
    if tag:
        sessions = store.get_sessions_by_tag(tag)
    else:
        sessions = store.list_sessions()

    sessions = sessions[-limit:]  # most recent

    if not sessions:
        print("Nenhuma sessão encontrada.")
        return

    print(f"## Histórico de Sessões")
    print(f"Total: {len(sessions)} sessão(ões)")
    if tag:
        print(f"Tag: {tag}")
    print()
    print("| # | Data | Formato | Tags | ID |")
    print("|---|------|---------|------|----|")
    for i, s in enumerate(sessions, 1):
        date = s.timestamp[:19].replace("T", " ")
        tags_str = ", ".join(t for t in s.tags if t) if s.tags else "—"
        print(f"| {i} | {date} | {s.input_format} | {tags_str} | `{s.session_id[:8]}` |")


def run_session(session_id: str) -> None:
    """Recupera e exibe uma sessão pelo ID."""
    store = SessionStore()
    session = store.get_session(session_id)

    if not session:
        print(f"Erro: Sessão '{session_id}' não encontrada.")
        sys.exit(1)

    print(f"## Sessão {session_id[:8]}")
    print(f"**Data:** {session.timestamp[:19].replace('T', ' ')}")
    print(f"**Formato:** {session.input_format}")
    print(f"**Tags:** {', '.join(t for t in session.tags if t) if session.tags else '—'}")
    print()
    print("### Input Original")
    print(session.raw_content)
    print()

    if session.analysis_result:
        ar = session.analysis_result
        print("### Diagnóstico")
        print(ar.diagnosis)
        print()
        print("### Temas")
        print(", ".join(ar.themes))
        print()
        print("### Riscos")
        for r in ar.risks:
            print(f"- {r}")
        print()
        print("### Padrões Cruzados")
        for p in ar.cross_card_patterns:
            print(f"- **[{p.pattern_type}]** ({p.strength}): {p.interpretation[:100]}...")
        print()
        print("### Plano Prático")
        print(ar.practical_plan)
    else:
        print("_(Análise não disponível)_")


def run_compare(session_id_1: str, session_id_2: str) -> None:
    """Compara duas sessões e gera relatório de diferenças."""
    store = SessionStore()
    s1 = store.get_session(session_id_1)
    s2 = store.get_session(session_id_2)

    if not s1:
        print(f"Erro: Sessão '{session_id_1}' não encontrada.")
        sys.exit(1)
    if not s2:
        print(f"Erro: Sessão '{session_id_2}' não encontrada.")
        sys.exit(1)

    print(f"## Comparação de Sessões")
    print()
    print(f"| | **Sessão {session_id_1[:8]}** | **Sessão {session_id_2[:8]}** |")
    print(f"|---|---|---|")
    print(f"| **Data** | {s1.timestamp[:19].replace('T',' ')} | {s2.timestamp[:19].replace('T',' ')} |")
    print(f"| **Formato** | {s1.input_format} | {s2.input_format} |")
    print(f"| **Tags** | {', '.join(t for t in s1.tags if t) if s1.tags else '—'} | {', '.join(t for t in s2.tags if t) if s2.tags else '—'} |")
    print()

    ar1, ar2 = s1.analysis_result, s2.analysis_result

    if ar1 and ar2:
        # Temas
        themes1, themes2 = set(ar1.themes), set(ar2.themes)
        common_themes = themes1 & themes2
        new_in_2 = themes2 - themes1
        dropped_from_1 = themes1 - themes2
        print("### Temas")
        if common_themes:
            print(f"**Mantidos:** {', '.join(common_themes)}")
        if new_in_2:
            print(f"**Novos:** {', '.join(new_in_2)}")
        if dropped_from_1:
            print(f"**Abandonados:** {', '.join(dropped_from_1)}")
        print()

        # Riscos
        risks1, risks2 = set(ar1.risks), set(ar2.risks)
        print("### Riscos")
        if risks1 != risks2:
            added = risks2 - risks1
            removed = risks1 - risks2
            if added:
                print(f"**Adicionados:** {', '.join(added)}")
            if removed:
                print(f"**Removidos:** {', '.join(removed)}")
        else:
            print("_(Sem mudança)_")
        print()

        # Padrões
        patterns1 = {p.pattern_type for p in ar1.cross_card_patterns}
        patterns2 = {p.pattern_type for p in ar2.cross_card_patterns}
        print("### Padrões Cruzados")
        print(f"**Antes:** {', '.join(sorted(patterns1)) or 'nenhum'}")
        print(f"**Depois:** {', '.join(sorted(patterns2)) or 'nenhum'}")
        print()

        # Cross-session insight
        print("### Insight Entre Sessões")
        date1 = s1.timestamp[:10]
        date2 = s2.timestamp[:10]
        print(
            f"Entre {date1} e {date2}, "
            f"{'os temas se mantiveram estáveis' if not new_in_2 and not dropped_from_1 else 'houve evolução nos temas'}. "
            f"{'O cenário de riscos permanece similar.' if risks1 == risks2 else 'O cenário de riscos mudou.'} "
            f"Foram detectados {len(ar2.cross_card_patterns)} padrões na sessão mais recente."
        )
    else:
        print("_(Análise completa não disponível para comparação)_")


def run_analyze(
    raw_input: str,
    format: str,
    output_path: str | None,
    template: str | None = None,
    verbose: bool = False,
    tag: str | None = None,
    report_format: str = "default",
    save_session: bool = False,
) -> None:
    """Executa o pipeline completo de análise.

    Pipeline: input_processor → analysis_engine → boundaries → report_generator

    Args:
        raw_input: Conteúdo bruto de entrada.
        format: Formato de entrada ("text", "spread", "symbols").
        output_path: Caminho opcional para salvar o relatório em .md.
        template: Template de tiragem predefinido (apenas para format="spread").
        verbose: Se True, ativa logging detalhado (DEBUG level).
        tag: Tag opcional para categorizar a sessão.
        save_session: Se True, salva a sessão no histórico.
    """
    # Configure verbose logging if requested
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

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

        # Fase 5: Salvar sessão se --save-session foi especificado
        if save_session:
            logger.info("Salvando sessão com tag: %s", tag)
            store = SessionStore()
            session = store.create_session(
                raw_content=raw_input,
                input_format=format,
            )
            # Atualizar sessão com análise e tags
            from clareza.types import Session as SessionType
            updated_session = SessionType(
                session_id=session.session_id,
                timestamp=session.timestamp,
                input_format=session.input_format,
                raw_content=session.raw_content,
                analysis_result=analysis_result,
                unresolved_threads=[],
                tags=[tag],
            )
            store.save_session(updated_session)
            logger.info("Sessão '%s' salva com tag '%s'", session.session_id[:8], tag)

        # Fase 6: Output
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
        if 'progress' in locals():
            progress.error("Erro no processamento")
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['file_not_found']}"), file=sys.stderr)
        sys.exit(2)
    except ParseError as e:
        logger.error("Erro no parse da entrada: %s", e)
        colored = _get_error_output()
        if 'progress' in locals():
            progress.error("Erro no processamento")
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['parse_error']}"), file=sys.stderr)
        sys.exit(2)
    except TemplateClarezaError as e:
        logger.error("Template inválido: %s", e.template_name)
        colored = _get_error_output()
        if 'progress' in locals():
            progress.error("Erro no processamento")
        available_hint = ""
        if e.available:
            available_hint = f"\nTemplates disponíveis: {', '.join(e.available)}"
        print(colored.error(f"✗ Erro: Template não encontrado: {e.template_name}{available_hint}"), file=sys.stderr)
        sys.exit(2)
    except ValidationClarezaError as e:
        logger.error("Validação falhou: %s", e)
        colored = _get_error_output()
        if 'progress' in locals():
            progress.error("Erro no processamento")
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['validation_error']}"), file=sys.stderr)
        sys.exit(2)
    except ClarezaError as e:
        logger.error("Erro do sistema: %s", e)
        colored = _get_error_output()
        if 'progress' in locals():
            progress.error("Erro no processamento")
        print(colored.error(f"✗ Erro: {e.message}"), file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        logger.error("Valor inválido: %s", e)
        colored = _get_error_output()
        if 'progress' in locals():
            progress.error("Erro no processamento")
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['validation_error']}"), file=sys.stderr)
        sys.exit(2)
    except OSError as e:
        logger.error("Erro de sistema de arquivos: %s", e)
        colored = _get_error_output()
        if 'progress' in locals():
            progress.error("Erro no processamento")
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['output_write_error']}"), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        logger.exception("Erro inesperado durante análise")
        colored = _get_error_output()
        if 'progress' in locals():
            progress.error("Erro no processamento")
        print(colored.error(f"✗ Erro: {ERROR_MESSAGES['unexpected_error']}"), file=sys.stderr)
        sys.exit(1)


def run_arc(
    sessions: str | None,
    output_path: str | None,
    format: str,
    verbose: bool = False,
    tag: str | None = None,
) -> None:
    """Exibe o arco narrativo entre sessões de análise.

    Args:
        sessions: Lista separada por vírgula de caminhos de arquivos de relatório.
        output_path: Caminho opcional para salvar a visualização em .md.
        format: Formato de saída ("text" ou "chart").
        verbose: Se True, ativa logging detalhado (DEBUG level).
        tag: Tag para filtrar sessões do storage.
    """
    # Configure verbose logging if requested
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    colored = _get_error_output()

    # Carregar sessões do storage se tag foi especificada
    if tag:
        logger.info("Filtrando sessões por tag: %s", tag)
        store = SessionStore()
        tagged_sessions = store.get_sessions_by_tag(tag)

        if not tagged_sessions:
            empty_msg = (
                f"# Arco Narrativo — Tag: {tag}\n\n"
                f"*Nenhuma sessão encontrada com a tag '{tag}'.\n"
                "Continue suas reflexões para construir um arco narrativo ao longo do tempo.*\n\n"
                "--- generated by Sistema de Clareza Simbólico-Estratégica v0.0.1.*"
            )
            if output_path:
                _save_report(output_path, empty_msg)
                print(colored.success(f"✓ Arco salvo em: {output_path}"), file=sys.stderr)
            else:
                print(empty_msg)
            return

        # Gerar arco usando ArcGenerator
        arc_gen = ArcGenerator()
        arc_content = arc_gen.generate(tagged_sessions, arc_name=f"Tag: {tag}")

        if output_path:
            _save_report(output_path, arc_content)
            print(colored.success(f"✓ Arco salvo em: {output_path}"), file=sys.stderr)
        else:
            print(arc_content)
        return

    # Fallback: usar arquivos de relatório se --sessions foi especificado
    if not sessions:
        print(
            colored.error("Erro: --sessions ou --tag é obrigatório para o comando arc."),
            file=sys.stderr,
        )
        sys.exit(2)

    # Parse session paths
    session_paths = [s.strip() for s in sessions.split(",") if s.strip()]

    if len(session_paths) < 2:
        print(
            colored.error("Erro: Mínimo de 2 sessões necessárias para visualizar o arco narrativo."),
            file=sys.stderr,
        )
        sys.exit(2)

    logger.info("Processando %d sessões para visualização do arco narrativo", len(session_paths))

    # Placeholder - actual implementation will be in arc_visualizer.py
    if format == "chart":
        output_content = f"## Arco Narrativo\n\nVisualização em formato chart para {len(session_paths)} sessões."
    else:
        output_content = f"## Arco Narrativo\n\nAnálise textual do arco entre {len(session_paths)} sessões."

    if output_path:
        _save_report(output_path, output_content)
        print(colored.success(f"✓ Visualização salva em: {output_path}"), file=sys.stderr)
    else:
        print(output_content)


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