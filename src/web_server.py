"""Servidor web leve — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por servir uma interface web simples para análise
simbólico-estratégica. Fornece endpoints REST para processar análises.

Endpoints:
    GET /: Página principal com interface web.
    GET /health: Health check do servidor.
    POST /api/analyze: Endpoint para processar análise.

Recebe parâmetros via JSON e retorna relatório em Markdown.
"""

import json
import logging
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

from src.input_processor import InputProcessor
from src.analysis_engine import AnalysisEngine
from src.boundaries import apply_guardrails
from src.report_generator import ReportGenerator
from src.exceptions import (
    ClarezaError,
    FileNotFoundClarezaError,
    ParseClarezaError,
    ValidationClarezaError,
)

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Diretórios e caminhos
# ----------------------------------------------------------------------


def _get_static_dir() -> Path:
    """Retorna o diretório de arquivos estáticos.

    Returns:
        Path para o diretório web_static.
    """
    return Path(__file__).parent / "web_static"


# ----------------------------------------------------------------------
# Handler de requisições
# ----------------------------------------------------------------------


class ClarezaRequestHandler(SimpleHTTPRequestHandler):
    """Handler customizado para API de análise simbólica.

    Define o comportamento para cada endpoint:
    - GET /: Serve index.html
    - GET /health: Retorna status OK
    - POST /api/analyze: Processa análise e retorna relatório

    Attributes:
        static_dir: Diretório de arquivos estáticos.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.static_dir = _get_static_dir()
        super().__init__(*args, directory=str(self.static_dir), **kwargs)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _send_json_response(
        self,
        status_code: int,
        data: dict[str, object],
    ) -> None:
        """Envia resposta JSON.

        Args:
            status_code: Código HTTP de status.
            data: Dados a serem serializados como JSON.
        """
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_error_response(
        self,
        status_code: int,
        message: str,
        details: Optional[str] = None,
    ) -> None:
        """Envia resposta de erro JSON.

        Args:
            status_code: Código HTTP de status.
            message: Mensagem de erro legível.
            details: Detalhes adicionais (opcional).
        """
        data: dict[str, object] = {"error": message}
        if details:
            data["details"] = details
        self._send_json_response(status_code, data)

    def _read_json_body(self) -> Optional[dict[str, object]]:
        """Lê e parseia o corpo da requisição como JSON.

        Returns:
            Dict com dados do corpo, ou None se não houver corpo.
        """
        content_length = self.headers.get("Content-Length")
        if not content_length:
            return None

        try:
            length = int(content_length)
            body = self.rfile.read(length)
            return json.loads(body.decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning("Falha ao parsear JSON: %s", e)
            return None

    def _run_analysis(
        self,
        raw_input: str,
        format: str,
    ) -> str:
        """Executa o pipeline completo de análise.

        Pipeline: input_processor → analysis_engine → boundaries → report_generator

        Args:
            raw_input: Conteúdo bruto de entrada.
            format: Formato de entrada ("text", "spread", "symbols").

        Returns:
            String com relatório em Markdown.

        Raises:
            ClarezaError: Se qualquer etapa do pipeline falhar.
        """
        # Fase 1: Parse e estruturação do input
        logger.info("Processando entrada via web: format=%s", format)
        processor = InputProcessor()
        structured = processor.parse(raw_input, format)

        # Fase 2: Análise simbólico-estratégica
        logger.info("Executando análise simbólica via web")
        engine = AnalysisEngine()
        analysis_result = engine.analyze(structured)

        # Fase 3: Geração do relatório Markdown
        logger.info("Gerando relatório via web")
        generator = ReportGenerator()
        report_md = generator.generate(analysis_result)

        # Fase 4: Aplicação de guardrails éticos
        logger.info("Aplicando guardrails éticos via web")
        validated = apply_guardrails(report_md, analysis_result)

        return validated.content

    # ------------------------------------------------------------------
    # Override: roteamento
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        """Trata requisições GET.

        Rota /health retorna status OK.
        Outras rotas servem arquivos estáticos.
        """
        if self.path == "/health":
            self._send_json_response(200, {"status": "ok"})
            return
        super().do_GET()

    def do_OPTIONS(self) -> None:
        """Trata requisições OPTIONS para CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        """Trata requisições POST.

        Rota /api/analyze processa análise e retorna relatório.
        """
        if self.path == "/api/analyze":
            self._handle_analyze()
            return
        self._send_error_response(404, "Endpoint não encontrado")

    def _handle_analyze(self) -> None:
        """Processa requisição de análise."""
        body = self._read_json_body()
        if body is None:
            self._send_error_response(400, "Corpo da requisição inválido")
            return

        raw_input = body.get("input")
        if not raw_input or not isinstance(raw_input, str):
            self._send_error_response(400, "Parâmetro 'input' é obrigatório")
            return

        format = body.get("format", "text")
        if format not in {"text", "spread", "symbols"}:
            self._send_error_response(
                400,
                "Parâmetro 'format' deve ser 'text', 'spread' ou 'symbols'",
            )
            return

        try:
            report = self._run_analysis(raw_input, format)
            self._send_json_response(200, {"report": report})
        except FileNotFoundClarezaError as e:
            logger.error("Arquivo não encontrado: %s", e.file_path)
            self._send_error_response(404, "Arquivo não encontrado", e.file_path)
        except ParseClarezaError as e:
            logger.error("Erro no parse: %s", e)
            self._send_error_response(400, "Erro ao processar entrada", str(e))
        except ValidationClarezaError as e:
            logger.error("Validação falhou: %s", e)
            self._send_error_response(400, "Validação falhou", str(e))
        except ClarezaError as e:
            logger.error("Erro do sistema: %s", e)
            self._send_error_response(500, "Erro interno do sistema", e.message)
        except Exception as e:
            logger.exception("Erro inesperado durante análise via web")
            self._send_error_response(500, "Erro inesperado", str(e))

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log_message(self, format: str, *args: object) -> None:
        """Sobrescreve logging para usar o logger do sistema.

        Args:
            format: Formato da mensagem.
            args: Argumentos para o formato.
        """
        logger.info("%s %s", self.address_string(), format % args)


# ----------------------------------------------------------------------
# Servidor web
# ----------------------------------------------------------------------


class WebServer:
    """Servidor web leve para análise simbólico-estratégica.

    Fornece interface HTTP para processar análises sem linha de comando.

    Attributes:
        host: Endereço host do servidor.
        port: Porta do servidor.
        server: Instância do servidor HTTP (lazy).
    """

    def __init__(self, host: str = "localhost", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        logger.debug("WebServer inicializado, host=%s, port=%d", host, port)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Inicia o servidor web.

        Raises:
            OSError: Se a porta estiver em uso ou sem permissão.
        """
        if self.server is not None:
            logger.warning("Servidor já está iniciado")
            return

        try:
            self.server = HTTPServer((self.host, self.port), ClarezaRequestHandler)
            logger.info(
                "Servidor iniciado em http://%s:%d",
                self.host,
                self.port,
            )
            self.server.serve_forever()
        except OSError as e:
            logger.error("Falha ao iniciar servidor: %s", e)
            self.server = None
            raise

    def stop(self) -> None:
        """Para o servidor web."""
        if self.server is None:
            logger.warning("Servidor não está ativo")
            return

        logger.info("Parando servidor em http://%s:%d", self.host, self.port)
        self.server.shutdown()
        self.server = None

    def is_running(self) -> bool:
        """Verifica se o servidor está em execução.

        Returns:
            True se o servidor está ativo.
        """
        return self.server is not None


# ----------------------------------------------------------------------
# CLI para servidor
# ----------------------------------------------------------------------


def run_server(host: str = "localhost", port: int = 8080) -> None:
    """Inicia o servidor web com as configurações fornecidas.

    Args:
        host: Endereço host (default localhost).
        port: Porta (default 8080).
    """
    server = WebServer(host=host, port=port)
    print(f"Iniciando servidor em http://{host}:{port}")
    print("Pressione Ctrl+C para parar")
    server.start()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Servidor web Clareza")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Endereço host (default: localhost)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Porta (default: 8080)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    run_server(host=args.host, port=args.port)
