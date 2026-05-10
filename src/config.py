"""Configuração do sistema — Sistema de Clareza Simbólico-Estratégica.

Define configurações default e tipos para o sistema de configuração
YAML com overrides via variáveis de ambiente.
"""

import logging
import os
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


def _load_env_overrides() -> dict:
    """Carrega overrides de configuração a partir de variáveis de ambiente.

    Variáveis de ambiente seguem o padrão CLAREZA_* e sobrescrevem
    tanto valores default quanto valores do YAML.

    Variáveis suportadas:
        CLAREZA_OUTPUT_DIR: Diretório de saída para relatórios.
        CLAREZA_FORMAT: Formato de relatório ("compact" ou "verbose").
        CLAREZA_LANGUAGE: Idioma padrão ("pt", "en", "es").
        CLAREZA_HISTORY_DIR: Diretório para histórico de sessões.
        CLAREZA_AUTO_SAVE: Se "1" ou "true", ativa auto-save.
        CLAREZA_QUIET: Se "1" ou "true", ativa modo silencioso.

    Returns:
        Dicionário com campos que devem sobrescrever a configuração.
    """
    overrides: dict = {}

    # CLAREZA_OUTPUT_DIR
    env_output_dir = os.environ.get("CLAREZA_OUTPUT_DIR")
    if env_output_dir:
        parsed = _parse_path(env_output_dir)
        if parsed is not None:
            overrides["default_output_dir"] = parsed

    # CLAREZA_FORMAT
    env_format = os.environ.get("CLAREZA_FORMAT")
    if env_format and env_format in VALID_REPORT_FORMATS:
        overrides["default_report_format"] = env_format

    # CLAREZA_LANGUAGE
    env_lang = os.environ.get("CLAREZA_LANGUAGE")
    if env_lang and env_lang in VALID_LANGUAGES:
        overrides["default_language"] = env_lang

    # CLAREZA_HISTORY_DIR
    env_history_dir = os.environ.get("CLAREZA_HISTORY_DIR")
    if env_history_dir:
        parsed = _parse_path(env_history_dir)
        if parsed is not None:
            overrides["session_history_dir"] = parsed

    # CLAREZA_AUTO_SAVE
    env_auto_save = os.environ.get("CLAREZA_AUTO_SAVE")
    if env_auto_save:
        overrides["auto_save_sessions"] = env_auto_save.lower() in ("1", "true", "yes")

    # CLAREZA_QUIET
    env_quiet = os.environ.get("CLAREZA_QUIET")
    if env_quiet:
        overrides["quiet_mode"] = env_quiet.lower() in ("1", "true", "yes")

    if overrides:
        logger.debug("Overrides de ambiente aplicados: %s", list(overrides.keys()))

    return overrides


def load_config() -> ClarezaConfig:
    """Carrega configuração do usuário a partir do arquivo YAML padrão.

    Lê ~/.config/clareza/config.yaml e sobrescreve valores default
    com valores encontrados no arquivo. Em seguida, aplica overrides
    de variáveis de ambiente (CLAREZA_*) que sempre têm precedence.

    A precedência é: defaults < YAML < ambiente

    Returns:
        ClarezaConfig com valores mesclados (ambiente tem maior precedência).
    """
    config_data = _load_yaml_config(DEFAULT_CONFIG_PATH)
    env_overrides = _load_env_overrides()

    if config_data is None and not env_overrides:
        logger.debug("Usando configuração padrão (nenhum arquivo YAML ou env encontrado)")
        return DEFAULT_CONFIG

    # Construir kwargs apenas com campos presentes no YAML
    kwargs: dict = {}

    # Tratar config_data None como dict vazio
    if config_data is None:
        config_data = {}

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

    # Aplicar overrides de ambiente (maior precedência)
    kwargs.update(env_overrides)

    config = ClarezaConfig(**kwargs)
    logger.debug("Configuração carregada com sucesso: %s", config)
    return config