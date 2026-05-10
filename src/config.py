"""Configuração do sistema — Sistema de Clareza Simbólico-Estratégica.

Define configurações default e tipos para o sistema de configuração
YAML com overrides via variáveis de ambiente.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


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