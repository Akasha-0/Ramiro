"""Configuração do sistema — Sistema de Clareza Simbólico-Estratégica.

Define configurações default e tipos para o sistema de configuração
YAML com overrides via variáveis de ambiente.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# Caminho padrão para o arquivo de configuração YAML do usuário
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "clareza" / "config.yaml"

# Caminho padrão para o diretório de dados do usuário
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "clareza"

# Diretório de saída default para relatórios
DEFAULT_OUTPUT_DIR = Path.cwd()

# Formatos de relatório válidos
VALID_REPORT_FORMATS = ["compact", "verbose"]

# Idiomas suportados
VALID_LANGUAGES = ["pt", "en", "es"]


@dataclass
class ClarezaConfig:
    """Configuração do sistema Clareza.

    Attributes:
        default_output_dir: Diretório padrão para salvar relatórios.
        default_report_format: Formato padrão do relatório ("compact" ou "verbose").
        default_language: Idioma padrão para relatórios ("pt", "en", "es").
        session_history_dir: Diretório para histórico de sessões.
        auto_save_sessions: Se True, salva sessões automaticamente.
        quiet_mode: Se True, reduz output verbose.
    """

    default_output_dir: Path = field(default_factory=lambda: Path.cwd())
    default_report_format: str = "compact"
    default_language: str = "pt"
    session_history_dir: Path = field(default_factory=lambda: DEFAULT_DATA_DIR / "sessions")
    auto_save_sessions: bool = False
    quiet_mode: bool = False


# Configuração padrão global (singleton em memória)
DEFAULT_CONFIG = ClarezaConfig()


# ----------------------------------------------------------------------
# Funções de carga de configuração YAML
# ----------------------------------------------------------------------


def _load_yaml_config(config_path: Path) -> Optional[dict]:
    """Carrega configuração YAML do arquivo especificado.

    Args:
        config_path: Caminho para o arquivo YAML de configuração.

    Returns:
        Dicionário com dados do YAML, ou None se o arquivo não existir.
    Raises:
        yaml.YAMLError: Se o arquivo existir mas não puder ser parseado.
    """
    import yaml  # Lazy import para permitir uso sem PyYAML quando não necessário

    if not config_path.exists():
        logger.debug("Arquivo de configuração não encontrado: %s", config_path)
        return None

    logger.debug("Carregando configuração de: %s", config_path)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.warning("Erro ao ler YAML de %s: %s", config_path, e)
        raise


def _parse_path(value: Optional[str]) -> Optional[Path]:
    """Converte string de caminho em Path, ou retorna None.

    Args:
        value: String de caminho ou None.

    Returns:
        Path se value for string válida, None caso contrário.
    """
    if value is None:
        return None
    try:
        return Path(value)
    except (ValueError, OSError):
        return None


def load_config() -> ClarezaConfig:
    """Carrega configuração do usuário a partir do arquivo YAML padrão.

    Lê ~/.config/clareza/config.yaml e sobrescreve valores default
    com valores encontrados no arquivo. Campos ausentes no YAML
    mantêm os valores default de ClarezaConfig.

    Returns:
        ClarezaConfig com valores do YAML (parciais) mesclados aos defaults.
    """
    config_data = _load_yaml_config(DEFAULT_CONFIG_PATH)

    if config_data is None:
        logger.debug("Usando configuração padrão (nenhum arquivo YAML encontrado)")
        return DEFAULT_CONFIG

    # Construir kwargs apenas com campos presentes no YAML
    kwargs: dict = {}

    if "default_output_dir" in config_data:
        parsed = _parse_path(config_data["default_output_dir"])
        if parsed is not None:
            kwargs["default_output_dir"] = parsed

    if "default_report_format" in config_data:
        fmt = config_data["default_report_format"]
        if fmt in VALID_REPORT_FORMATS:
            kwargs["default_report_format"] = fmt

    if "default_language" in config_data:
        lang = config_data["default_language"]
        if lang in VALID_LANGUAGES:
            kwargs["default_language"] = lang

    if "session_history_dir" in config_data:
        parsed = _parse_path(config_data["session_history_dir"])
        if parsed is not None:
            kwargs["session_history_dir"] = parsed

    if "auto_save_sessions" in config_data:
        kwargs["auto_save_sessions"] = bool(config_data["auto_save_sessions"])

    if "quiet_mode" in config_data:
        kwargs["quiet_mode"] = bool(config_data["quiet_mode"])

    config = ClarezaConfig(**kwargs)
    logger.debug("Configuração carregada com sucesso: %s", config)
    return config