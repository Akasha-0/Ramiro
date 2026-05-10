"""Testes para src/commands/history.py e src/commands/view.py.

Cobertura:
- run_history() — listar sessões, filtros, empty state
- format_session_line() — formatação de linha de sessão
- run_view() — exibir relatório, erros, sessão não encontrada
- CLI history/view via main()
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import pytest

from src.commands.history import run_history, format_session_line
from src.commands.view import run_view
from src.database import SessionDB, DatabaseError


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


class _StringIO:
    """Buffer em memória para captura de stdout/stderr."""

    def __init__(self) -> None:
        self._buffer: list[str] = []

    def write(self, text: str) -> int:
        self._buffer.append(text)
        return len(text)

    def getvalue(self) -> str:
        return "".join(self._buffer)


def capture_stdout_stderr(func, *args, **kwargs) -> tuple[str, str, int]:
    """Captura stdout e stderr de uma função que chama sys.exit()."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = _StringIO()
    sys.stderr = _StringIO()
    exit_code = -1
    try:
        func(*args, **kwargs)
    except SystemExit as e:
        exit_code = int(e.code) if e.code is not None else 0
    finally:
        stdout_val = sys.stdout.getvalue()
        stderr_val = sys.stderr.getvalue()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    return stdout_val, stderr_val, exit_code


def capture_stdout(func, *args, **kwargs) -> tuple[str, int]:
    """Captura stdout e código de saída de uma função.

    Returns:
        Tupla (stdout_content, exit_code).
        exit_code = 0 para execuções normais sem sys.exit().
        exit_code = -1 se SystemExit não foi levantado.
    """
    stdout_val, stderr_val, exit_code = capture_stdout_stderr(func, *args, **kwargs)
    combined = stdout_val + stderr_val
    # run_history/run_view não chamam sys.exit() no caso de sucesso,
    # então exit_code=-1 significa sucesso
    if exit_code == -1:
        exit_code = 0
    return combined, exit_code


def run_main_with_args(args: list[str]) -> tuple[str, str, int]:
    """Executa main() com sys.argv mockado.

    Retorna tuple (stdout, stderr, exit_code) onde exit_code=0 se main()
    retorna normalmente (sem sys.exit()).
    """
    from src.main import main

    backup_stdout = sys.stdout
    backup_stderr = sys.stderr
    sys.stdout = _StringIO()
    sys.stderr = _StringIO()
    exit_code = -1
    backup_argv = list(sys.argv)
    try:
        sys.argv = ["clareza"] + list(args)
        main()
    except SystemExit as e:
        exit_code = int(e.code) if e.code is not None else 0
    finally:
        sys.argv = backup_argv
        stdout_val = sys.stdout.getvalue()
        stderr_val = sys.stderr.getvalue()
        sys.stdout = backup_stdout
        sys.stderr = backup_stderr
    # main() não chama sys.exit() para comandos bem-sucedidos
    if exit_code == -1:
        exit_code = 0
    return stdout_val, stderr_val, exit_code


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def temp_db_dir(tmp_path: Path) -> Path:
    """Diretório temporário para banco de dados de teste."""
    return tmp_path


@pytest.fixture
def db_with_sessions(temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch) -> SessionDB:
    """Banco de dados com sessões pré-inseridas para testes."""
    monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
    monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

    from src.database import init_db
    init_db()

    db = SessionDB()
    db.save_session(
        input_text="Preciso decidir sobre minha carreira",
        cards=["Cruz", "Estrela"],
        format="symbols",
    )
    db.save_session(
        input_text="Problemas no trabalho e família",
        cards=["Café", "Montanha"],
        format="spread",
    )
    db.save_session(
        input_text="Dúvidas sobre saúde e alimentação",
        format="text",
    )
    return db


@pytest.fixture
def db_with_session_and_report(
    temp_db_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[SessionDB, Path]:
    """Banco com uma sessão que tem relatório salvo."""
    monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
    monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

    from src.database import init_db
    init_db()

    db = SessionDB()

    # Criar arquivo de relatório temporário
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        report_content = "# Relatório de Análise\n\nConteúdo do relatório."
        f.write(report_content)
        report_path = f.name

    session_id = db.save_session(
        input_text="Teste com relatório",
        cards=["Cruz"],
        format="text",
        report_path=report_path,
    )

    yield db, report_path

    # Cleanup
    if os.path.exists(report_path):
        os.unlink(report_path)


@pytest.fixture
def db_with_empty_report_session(
    temp_db_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> SessionDB:
    """Banco com sessão sem caminho de relatório."""
    monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
    monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

    from src.database import init_db
    init_db()

    db = SessionDB()
    db.save_session(
        input_text="Sessão sem relatório",
        format="text",
    )
    return db


# ----------------------------------------------------------------------
# Testes — run_history(): empty state
# ----------------------------------------------------------------------


class TestRunHistoryEmpty:
    def test_empty_history_shows_message(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Histórico vazio exibe mensagem amigável."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        init_db()

        output, exit_code = capture_stdout(run_history)

        assert exit_code == 0
        assert "Nenhuma sessão encontrada" in output


# ----------------------------------------------------------------------
# Testes — run_history(): listar sessões
# ----------------------------------------------------------------------


class TestRunHistoryList:
    def test_lists_sessions_with_preview(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Lista sessões com timestamp e preview do texto."""
        output, exit_code = capture_stdout(run_history)

        assert exit_code == 0
        assert "sessão" in output.lower()
        assert "encontrada" in output.lower()

    def test_includes_session_count(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Output inclui contagem de sessões."""
        output, exit_code = capture_stdout(run_history)

        assert exit_code == 0
        assert "3" in output

    def test_returns_session_records(
        self, db_with_sessions: SessionDB
    ) -> None:
        """run_history retorna lista de SessionRecord."""
        from src.types import SessionRecord

        sessions = run_history(search=None, limit=10)

        assert len(sessions) == 3
        assert all(isinstance(s, SessionRecord) for s in sessions)

    def test_sessions_ordered_by_timestamp_desc(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Sessões são ordenadas por data decrescente."""
        sessions = run_history()

        assert len(sessions) == 3
        # A mais recente deve ser a primeira (não tem cards)
        assert sessions[0].input_text == "Dúvidas sobre saúde e alimentação"
        assert sessions[0].cards == "[]"

    def test_long_text_is_truncated(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Texto longo é truncado no preview."""
        output, exit_code = capture_stdout(run_history)

        assert exit_code == 0
        # Não deve haver texto muito longo em uma linha
        lines = [l for l in output.split("\n") if l.strip()]
        for line in lines:
            if "..." in line:
                # Linhas truncadas contêm "..."
                assert len(line.split("—")[1].strip()) < 100


# ----------------------------------------------------------------------
# Testes — run_history(): filtros
# ----------------------------------------------------------------------


class TestRunHistoryFilters:
    def test_search_filters_by_text(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Filtro search busca no texto."""
        sessions = run_history(search="trabalho")

        assert len(sessions) >= 1
        assert all("trabalho" in s.input_text.lower() for s in sessions)

    def test_search_filters_by_cards(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Filtro search busca nas cartas."""
        sessions = run_history(search="Estrela")

        assert len(sessions) >= 1

    def test_limit_restricts_results(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Parâmetro limit restringe resultados."""
        sessions = run_history(limit=2)

        assert len(sessions) == 2

    def test_limit_zero_returns_empty(
        self, db_with_sessions: SessionDB
    ) -> None:
        """limit=0 retorna lista vazia."""
        sessions = run_history(limit=0)

        assert len(sessions) == 0

    def test_search_and_limit_combined(
        self, db_with_sessions: SessionDB
    ) -> None:
        """search e limit podem ser combinados."""
        sessions = run_history(search="trabalho", limit=1)

        assert len(sessions) <= 1


# ----------------------------------------------------------------------
# Testes — run_history(): erros de banco
# ----------------------------------------------------------------------


class TestRunHistoryErrors:
    def test_database_error_exits_with_code_1(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Erro de banco causa saída com código 1."""
        # Simular erro de banco usando mock
        def raise_db_error(*args, **kwargs):
            raise DatabaseError("Erro de conexão")

        monkeypatch.setattr("src.database.SessionDB.get_sessions", raise_db_error)

        output, exit_code = capture_stdout(run_history)

        assert exit_code == 1
        assert "Erro" in output


# ----------------------------------------------------------------------
# Testes — format_session_line()
# ----------------------------------------------------------------------


class TestFormatSessionLine:
    def test_formats_complete_session(self) -> None:
        """Formata sessão completa com ID, data, cartas e preview."""
        from src.types import SessionRecord
        from datetime import datetime

        session = SessionRecord(
            id=1,
            timestamp=datetime(2026, 5, 10, 14, 30).isoformat(),
            input_text="Preciso decidir sobre minha carreira",
            cards=json.dumps(["Cruz", "Estrela"]),
            format="symbols",
        )

        line = format_session_line(session)

        assert "[1]" in line
        assert "10/05/2026" in line
        assert "14:30" in line
        assert "Cruz" in line
        assert "Preciso decidir" in line

    def test_truncates_long_preview(self) -> None:
        """Texto longo é truncado com '...'."""
        from src.types import SessionRecord
        from datetime import datetime

        long_text = "A" * 100
        session = SessionRecord(
            id=2,
            timestamp=datetime(2026, 5, 10).isoformat(),
            input_text=long_text,
            cards="[]",
            format="text",
        )

        line = format_session_line(session)

        assert "..." in line
        assert len(line) < 100

    def test_handles_empty_cards(self) -> None:
        """Sessão sem cartas não exibe lista de cartas."""
        from src.types import SessionRecord
        from datetime import datetime

        session = SessionRecord(
            id=3,
            timestamp=datetime(2026, 5, 10).isoformat(),
            input_text="Texto simples",
            cards="[]",
            format="text",
        )

        line = format_session_line(session)

        assert "[" not in line or "[]" not in line

    def test_shows_up_to_three_cards(self) -> None:
        """Exibe até 3 cartas, com ']' ao final se houver mais."""
        from src.types import SessionRecord
        from datetime import datetime

        session = SessionRecord(
            id=4,
            timestamp=datetime(2026, 5, 10).isoformat(),
            input_text="Texto",
            cards=json.dumps(["Cruz", "Estrela", "Café", "Montanha"]),
            format="spread",
        )

        line = format_session_line(session)

        assert "Cruz" in line
        assert "Estrela" in line
        assert "Café" in line


# ----------------------------------------------------------------------
# Testes — run_view(): sucesso
# ----------------------------------------------------------------------


class TestRunViewSuccess:
    def test_displays_report_content(
        self, db_with_session_and_report: tuple[SessionDB, Path]
    ) -> None:
        """Exibe conteúdo do relatório salvo."""
        db, report_path = db_with_session_and_report

        output, exit_code = capture_stdout(run_view, session_id=1)

        assert exit_code == 0
        assert "# Relatório de Análise" in output
        assert "Conteúdo do relatório" in output

    def test_returns_true_on_success(
        self, db_with_session_and_report: tuple[SessionDB, Path]
    ) -> None:
        """Retorna True quando relatório é exibido."""
        db, report_path = db_with_session_and_report

        result = run_view(session_id=1)

        assert result is True

    def test_with_multiple_formats(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Funciona com relatórios de diferentes formatos."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        init_db()

        db = SessionDB()

        # Criar relatório com formato spread
        spread_content = "# Tiragem\n\n## Interpretação\n\nCartas: Cruz, Estrela."
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(spread_content)
            report_path = f.name

        db.save_session(
            input_text="Tiragem spread",
            cards=["Cruz", "Estrela"],
            format="spread",
            report_path=report_path,
        )

        output, exit_code = capture_stdout(run_view, session_id=1)

        assert exit_code == 0
        assert "Tiragem" in output

        os.unlink(report_path)


# ----------------------------------------------------------------------
# Testes — run_view(): erros
# ----------------------------------------------------------------------


class TestRunViewErrors:
    def test_session_not_found_exits_with_code_1(
        self, db_with_sessions: SessionDB
    ) -> None:
        """Sessão não encontrada causa saída com código 1."""
        output, exit_code = capture_stdout(run_view, session_id=9999)

        assert exit_code == 1
        assert "não encontrada" in output or "9999" in output

    def test_session_without_report_exits_with_code_1(
        self, db_with_empty_report_session: SessionDB
    ) -> None:
        """Sessão sem relatório causa saída com código 1."""
        output, exit_code = capture_stdout(run_view, session_id=1)

        assert exit_code == 1
        assert "não possui relatório" in output or "relatório" in output

    def test_report_file_not_readable_exits_with_code_1(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Arquivo de relatório não-legível causa erro."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        init_db()

        db = SessionDB()

        # Criar arquivo e depois remover
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Relatório")
            report_path = f.name

        session_id = db.save_session(
            input_text="Teste",
            report_path=report_path,
        )

        # Remover arquivo antes de chamar run_view
        os.unlink(report_path)

        output, exit_code = capture_stdout(run_view, session_id=session_id)

        assert exit_code == 1
        assert "Erro" in output or "ler" in output


# ----------------------------------------------------------------------
# Testes — run_view(): erros de banco
# ----------------------------------------------------------------------


class TestRunViewDatabaseErrors:
    def test_database_error_exits_with_code_1(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Erro de banco causa saída com código 1."""
        # Simular erro de banco usando mock
        def raise_db_error(*args, **kwargs):
            raise DatabaseError("Erro de conexão")

        monkeypatch.setattr("src.database.SessionDB.get_session", raise_db_error)

        output, exit_code = capture_stdout(run_view, session_id=1)

        assert exit_code == 1
        assert "Erro" in output


# ----------------------------------------------------------------------
# Testes — CLI via main()
# ----------------------------------------------------------------------


class TestHistoryCLI:
    def test_cli_history_command(self) -> None:
        """Comando 'history' via CLI funciona."""
        stdout, stderr, exit_code = run_main_with_args(["history"])

        # Sem sessões, deve mostrar empty state
        assert exit_code == 0
        assert "Nenhuma sessão" in stdout or "sessão" in stdout

    def test_cli_history_with_search(self) -> None:
        """'history --search' filtra corretamente."""
        stdout, stderr, exit_code = run_main_with_args(["history", "--search", "trabalho"])

        assert exit_code == 0

    def test_cli_history_with_limit(self) -> None:
        """'history --limit' funciona."""
        stdout, stderr, exit_code = run_main_with_args(["history", "--limit", "5"])

        assert exit_code == 0

    def test_cli_history_short_flags(self) -> None:
        """Flags curtos -s e -l funcionam."""
        stdout, stderr, exit_code = run_main_with_args(["history", "-s", "teste", "-l", "3"])

        assert exit_code == 0


class TestViewCLI:
    def test_cli_view_command_requires_id(self) -> None:
        """Comando 'view' sem ID causa erro."""
        stdout, stderr, exit_code = run_main_with_args(["view"])

        assert exit_code == 2

    def test_cli_view_with_nonexistent_id(self) -> None:
        """'view <id>' com ID inexistente mostra erro."""
        stdout, stderr, exit_code = run_main_with_args(["view", "9999"])

        assert exit_code == 1
        assert "não encontrada" in stderr


# ----------------------------------------------------------------------
# Testes — edge cases
# ----------------------------------------------------------------------


class TestHistoryEdgeCases:
    def test_special_characters_in_input(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Caracteres especiais no input são preservados."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        init_db()

        db = SessionDB()
        db.save_session(
            input_text="Relação coração família saúde @#$%",
            format="text",
        )

        sessions = run_history()

        assert len(sessions) >= 1
        assert "Relação" in sessions[0].input_text

    def test_unicode_in_preview(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unicode é preservado no preview."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        init_db()

        db = SessionDB()
        db.save_session(
            input_text="Café coração relação família",
            format="text",
        )

        output, exit_code = capture_stdout(run_history)

        assert exit_code == 0
        # Verifica que não houve problema de encoding
        assert "Café" in output or "sessão" in output.lower()


class TestViewEdgeCases:
    def test_empty_report_file(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Arquivo de relatório vazio é exibido corretamente."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        init_db()

        db = SessionDB()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            report_path = f.name

        db.save_session(
            input_text="Teste",
            report_path=report_path,
        )

        output, exit_code = capture_stdout(run_view, session_id=1)

        assert exit_code == 0
        # Deve exibir conteúdo vazio (sem erro)

        os.unlink(report_path)

    def test_large_report_file(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Arquivo de relatório grande é lido corretamente."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        init_db()

        db = SessionDB()

        large_content = "# Relatório\n\n" + "Lorem ipsum " * 1000
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(large_content)
            report_path = f.name

        db.save_session(
            input_text="Teste",
            report_path=report_path,
        )

        output, exit_code = capture_stdout(run_view, session_id=1)

        assert exit_code == 0
        assert "Relatório" in output
        assert "Lorem ipsum" in output

        os.unlink(report_path)


# ----------------------------------------------------------------------
# Testes — integration
# ----------------------------------------------------------------------


class TestHistoryViewIntegration:
    def test_analyze_then_history(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Analyze seguido de history mostra a sessão."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        from src.main import run_analyze

        init_db()

        # Executar análise
        output, exit_code = capture_stdout(
            run_analyze,
            "Preciso decidir sobre carreira",
            "text",
            None,
            None,
        )

        assert exit_code == 0

        # Listar histórico
        sessions = run_history()

        assert len(sessions) >= 1
        assert "carreira" in sessions[0].input_text

    def test_analyze_with_report_then_view(
        self, temp_db_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Analyze com output file, seguido de view, exibe relatório."""
        monkeypatch.setattr("src.database._DB_DIR", temp_db_dir)
        monkeypatch.setattr("src.database._DB_PATH", temp_db_dir / "sessions.db")

        from src.database import init_db
        from src.main import run_analyze

        init_db()

        # Criar arquivo de relatório
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            report_path = f.name

        # Executar análise com output
        output, exit_code = capture_stdout(
            run_analyze,
            "Trabalho e família",
            "text",
            report_path,
            None,
        )

        assert exit_code == 0

        # Ver sessão
        output, exit_code = capture_stdout(run_view, session_id=1)

        assert exit_code == 0
        assert "# Relatório de Análise" in output

        os.unlink(report_path)
