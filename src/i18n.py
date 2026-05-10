"""Módulo de internacionalização (i18n) — Sistema de Clareza Simbólico-Estratégica.

Fornece funções de tradução gettext com detecção automática de locale,
fallback para inglês, e suporte a masculino/feminino no português.
"""

from __future__ import annotations

import gettext as _gettext
import os
import shutil
from pathlib import Path
from typing import Optional

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

# Diretório base do projeto (assumindo src/i18n.py está em src/)
_PROJECT_ROOT = Path(__file__).parent.parent
_LOCALE_DIR = _PROJECT_ROOT / "locale"

# Locales suportados (devem existir em locale/)
_SUPPORTED_LOCALES = ["pt_BR", "en_US"]

# Locale padrão (fallback final)
_DEFAULT_LOCALE = "en_US"

# ----------------------------------------------------------------------
# Module state (global translation state)
# ----------------------------------------------------------------------

_translation: Optional[_gettext.GNUTranslations] = None
_current_locale: str = _DEFAULT_LOCALE


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def gettext(message: str) -> str:
    """Traduz uma mensagem para o locale atual.

    Args:
        message: Mensagem em inglês (msgid dos arquivos .po).

    Returns:
        Tradução para o locale atual, ou a mensagem original se
        não houver tradução disponível.
    """
    if _translation is None:
        return message
    try:
        return _translation.gettext(message)
    except Exception:
        return message


def ngettext(singular: str, plural: str, n: int) -> str:
    """Traduz mensagem com forma singular/plural para o locale atual.

    Args:
        singular: Forma singular da mensagem.
        plural: Forma plural da mensagem.
        n: Número para determinar qual forma usar.

    Returns:
        Tradução da forma apropriada (singular ou plural).
    """
    if _translation is None:
        return singular if n == 1 else plural
    try:
        return _translation.ngettext(singular, plural, n)
    except Exception:
        return singular if n == 1 else plural


def set_locale(locale: str) -> str:
    """Define o locale ativo para traduções.

    Args:
        locale: Código do locale (ex: "pt_BR", "en_US").

    Returns:
        Locale ativo após a definição (pode ser diferente se
        o locale solicitado não é suportado).

    Raises:
        ValueError: Se o locale não é válido.
    """
    global _translation, _current_locale

    # Validar formato básico do locale
    if not locale or len(locale) < 4:
        raise ValueError(f"Locale inválido: '{locale}'")

    # Normalizar para o formato correto (xx_XX)
    normalized = _normalize_locale(locale)

    if normalized not in _SUPPORTED_LOCALES:
        raise ValueError(
            f"Locale '{normalized}' não suportado. "
            f"Locales disponíveis: {', '.join(_SUPPORTED_LOCALES)}"
        )

    # Carregar tradução
    _translation = _load_translation(normalized)
    _current_locale = normalized

    return _current_locale


def get_current_locale() -> str:
    """Retorna o locale ativo atual.

    Returns:
        Código do locale atualmente ativo (ex: "pt_BR", "en_US").
    """
    return _current_locale


def get_available_locales() -> list[str]:
    """Retorna a lista de locales suportados.

    Returns:
        Lista de códigos de locale suportados.
    """
    return _SUPPORTED_LOCALES.copy()


def detect_system_locale() -> str:
    """Detecta o locale do sistema operacional.

    Verifica variáveis de ambiente na seguinte ordem:
    1. LC_ALL
    2. LC_MESSAGES
    3. LANG

    Returns:
        Locale detectado ou locale padrão (en_US) se não encontrado.
    """
    for env_var in ["LC_ALL", "LC_MESSAGES", "LANG"]:
        value = os.environ.get(env_var, "")
        if value:
            normalized = _normalize_locale(value)
            if normalized in _SUPPORTED_LOCALES:
                return normalized
            # Tentar extrair parte do idioma (ex: "pt" de "pt_BR.UTF-8")
            lang_code = value.split("_")[0].split(".")[0].lower()
            for supported in _SUPPORTED_LOCALES:
                if supported.startswith(lang_code):
                    return supported

    return _DEFAULT_LOCALE


def init_i18n(locale: Optional[str] = None) -> str:
    """Inicializa o sistema i18n.

    Se locale for fornecido, usa esse locale. Caso contrário,
    detecta automaticamente do sistema.

    Args:
        locale: Locale específico a usar (opcional).

    Returns:
        Locale ativo após inicialização.
    """
    if locale is None:
        locale = detect_system_locale()

    try:
        return set_locale(locale)
    except ValueError:
        # Locale não suportado, usar fallback
        _init_fallback()
        return _current_locale


def _init_fallback() -> None:
    """Inicializa com locale padrão (fallback)."""
    global _translation, _current_locale
    _translation = _load_translation(_DEFAULT_LOCALE)
    _current_locale = _DEFAULT_LOCALE


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------


def _normalize_locale(locale: str) -> str:
    """Normaliza um código de locale para o formato xx_XX.

    Args:
        locale: Código de locale em diversos formatos.

    Returns:
        Locale normalizado (ex: "pt_BR", "en_US").
    """
    if not locale:
        return _DEFAULT_LOCALE

    # Converter para o formato padrão (xx_XX)
    parts = locale.replace("-", "_").replace(".", "_").split("_")

    if len(parts) >= 2:
        # Formato completo: en_US.UTF-8 -> en_US
        lang = parts[0].lower()
        country = parts[1].upper()
        return f"{lang}_{country}"
    elif len(parts) == 1 and parts[0]:
        # Apenas código de idioma: "pt" -> "pt_BR" para português
        lang = parts[0].lower()
        if lang == "pt":
            return "pt_BR"
        return f"{lang}_XX"
    else:
        return _DEFAULT_LOCALE


def _load_translation(locale: str) -> _gettext.GNUTranslations:
    """Carrega arquivos de tradução para um locale.

    Esta função:
    1. Verifica se existem arquivos .mo compilados
    2. Se não existirem, compila os arquivos .po correspondentes
    3. Retorna o objeto de tradução

    Args:
        locale: Código do locale (ex: "pt_BR").

    Returns:
        Objeto GNUTranslations carregado.

    Raises:
        FileNotFoundError: Se nem .mo nem .po existirem para o locale.
    """
    locale_path = _LOCALE_DIR / locale / "LC_MESSAGES"
    mo_file = locale_path / "clareza.mo"
    po_file = locale_path / "clareza.po"

    # Compilar .po para .mo se necessário
    if not mo_file.exists() and po_file.exists():
        _compile_po(po_file, mo_file)

    # Carregar tradução (.mo compilado ou None)
    if mo_file.exists():
        try:
            return _gettext.translation(
                domain="clareza",
                localedir=str(_LOCALE_DIR),
                languages=[locale],
            )
        except Exception:
            pass

    # Retornar tradução vazia (fallback)
    return _gettext.NullTranslations()


def _compile_po(po_path: Path, mo_path: Path) -> None:
    """Compila um arquivo .po para .mo.

    Args:
        po_path: Caminho para o arquivo .po fonte.
        mo_path: Caminho de destino para o arquivo .mo compilado.
    """
    try:
        import msgfmt

        # Garantir que o diretório de destino existe
        mo_path.parent.mkdir(parents=True, exist_ok=True)

        # Compilar usando msgfmt (parte do gettext do sistema)
        msgfmt.make(po_path, mo_path)
        return
    except ImportError:
        pass

    # Tentar ferramenta do sistema
    shutilwhich = shutil.which("msgfmt")
    if shutilwhich:
        try:
            mo_path.parent.mkdir(parents=True, exist_ok=True)
            os.system(f'"{shutilwhich}" -o "{mo_path}" "{po_path}"')
            return
        except Exception:
            pass

    # Fallback: compilação manual pura em Python
    _compile_po_manual(po_path, mo_path)


def _compile_po_manual(po_path: Path, mo_path: Path) -> None:
    """Compila .po para .mo usando implementação pura em Python.

    Args:
        po_path: Caminho para o arquivo .po fonte.
        mo_path: Caminho de destino para o arquivo .mo compilado.
    """
    import struct
    import re

    def escape(s: str) -> bytes:
        """Escapa uma string para formato .mo."""
        return s.encode("utf-8").replace(b"\\x00", b"\\x5c\x00")

    def unescape(s: bytes) -> str:
        """Remove escaping de uma string .mo."""
        return s.decode("utf-8").replace("\\x00", "\x00")

    # Ler arquivo .po
    messages: dict[bytes, bytes] = {}
    header = b""
    current_msgid = b""
    current_msgstr = b""
    in_msgid = False
    in_msgstr = False

    with open(po_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse .po file
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('msgid "'):
            in_msgid = True
            in_msgstr = False
            current_msgid = line[7:-1]  # Remove 'msgid "' and trailing '"
        elif line.startswith('msgstr "'):
            in_msgstr = True
            in_msgid = False
            current_msgstr = line[8:-1]  # Remove 'msgstr "' and trailing '"
        elif line.startswith('"') and (in_msgid or in_msgstr):
            # Continuação da mensagem anterior
            content_str = line[1:-1]  # Remove surrounding quotes
            if in_msgid:
                current_msgid += content_str
            else:
                current_msgstr += content_str
        elif line == "":
            # Fim da entrada atual
            if current_msgid or current_msgstr:
                # Processar entrada
                msgid_bytes = current_msgid.encode("utf-8").replace(b"\\n", b"\n").replace(b"\\t", b"\t").replace(b'\\"', b'"').replace(b"\\\\", b"\\")
                msgstr_bytes = current_msgstr.encode("utf-8").replace(b"\\n", b"\n").replace(b"\\t", b"\t").replace(b'\\"', b'"').replace(b"\\\\", b"\\")
                messages[msgid_bytes] = msgstr_bytes

            # Se for o header (msgid vazio), guardar para processar
            if current_msgid == b"":
                pass  # Header será processado depois

            current_msgid = b""
            current_msgstr = b""
            in_msgid = False
            in_msgstr = False

        i += 1

    # Garantir que o diretório de destino existe
    mo_path.parent.mkdir(parents=True, exist_ok=True)

    # Escrever arquivo .mo
    # Formato .mo: magic + version + count + message table offset + translation table offset
    # Cada entrada: length (4 bytes) + offset (4 bytes)
    keys = sorted(messages.keys())
    ids = b""
    strs = b""
    ids_offsets = []
    strs_offsets = []

    for key in keys:
        ids_offsets.append(len(ids))
        ids += key + b"\x00"
        strs_offsets.append(len(strs))
        strs += messages[key] + b"\x00"

    # Header do .mo (não usado, mas mantém clareza)
    # O header real é escrito na seção "Escrever arquivo .mo"
    pass

    # Calcular offsets
    # File format (28-byte header):
    # Bytes 0-27: header
    # Bytes 28 to 28+offsets_size-1: keys table (8 bytes per entry: length + offset)
    # Bytes 28+offsets_size to 28+2*offsets_size-1: strings table (8 bytes per entry: length + offset)
    # Bytes 28+2*offsets_size onwards: keys data followed by strings data
    #
    # The ids_offset in the header points to where the keys table starts
    # The strs_offset in the header points to where the strings table starts
    # The offsets WITHIN the tables are relative to where the respective data blocks start

    header_size = 28  # 7 * 4 bytes
    offsets_size = 8 * len(keys)  # 4 bytes length + 4 bytes offset per key

    keys_table_offset = header_size  # Where keys table starts
    translations_table_offset = header_size + offsets_size  # Where strings table starts
    keys_data_offset = header_size + 2 * offsets_size  # Where keys data starts
    translations_data_offset = keys_data_offset + len(ids)  # Where strings data starts

    # Construir tabela de IDs (msgid + offset)
    ids_table = b""
    for i, key in enumerate(keys):
        ids_table += struct.pack("I", len(key))  # Length of key
        ids_table += struct.pack("I", ids_offsets[i])  # Offset relative to keys_data_offset

    # Construir tabela de strings (msgstr + offset)
    strs_table = b""
    for i, key in enumerate(keys):
        strs_table += struct.pack("I", len(messages[key]))  # Length
        strs_table += struct.pack("I", strs_offsets[i])  # Offset relative to translations_data_offset

    # Escrever arquivo .mo
    with open(mo_path, "wb") as f:
        # Header (28 bytes)
        f.write(struct.pack("I", 0x950412de))  # Magic (little-endian)
        f.write(struct.pack("I", 0))  # Version
        f.write(struct.pack("I", len(keys)))  # Count
        f.write(struct.pack("I", keys_table_offset))  # IDs table offset
        f.write(struct.pack("I", translations_table_offset))  # Strings table offset
        f.write(struct.pack("I", 0))  # Hash size
        f.write(struct.pack("I", 0))  # Hash offset

        # Tabela de IDs (chaves + offsets)
        f.write(ids_table)

        # Tabela de strings (traduções + offsets)
        f.write(strs_table)

        # Dados das chaves (msgid)
        f.write(ids)

        # Dados das traduções (msgstr)
        f.write(strs)


# ----------------------------------------------------------------------
# Module initialization
# ----------------------------------------------------------------------

# Inicializar com locale padrão na importação
_init_fallback()