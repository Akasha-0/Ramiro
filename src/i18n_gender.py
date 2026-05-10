"""Módulo de internacionalização com suporte a gênero gramatical em Português.

Fornece ferramentas para seleção de texto baseada em gênero gramatical,
essencial para outputs que se referem ao usuário de forma personalizada.

Portuguese grammatical gender handling:
- GENDER_MASCULINE: seleção de formas masculinas
- GENDER_FEMININE: seleção de formas femininas
- pgettext(): seleção de texto baseada no gênero do usuário
"""

from enum import Enum
from typing import Optional


class GrammaticalGender(Enum):
    """Enumeração para gêneros gramaticais em Português.

    Attributes:
        MASCULINE: gênero masculino (o, os, -o, -os)
        FEMININE: gênero feminino (a, as, -a, -as)
    """

    MASCULINE = "masculine"
    FEMININE = "feminine"


# Constantes de conveniência para uso em todo o código
GENDER_MASCULINE = GrammaticalGender.MASCULINE
GENDER_FEMININE = GrammaticalGender.FEMININE


def pgettext(
    masculine: str,
    feminine: str,
    gender: Optional[GrammaticalGender] = None,
) -> str:
    """Seleciona a forma gramatical correta baseada no gênero.

    Args:
        masculine: Forma masculina do texto (ex: "caro usuário").
        feminine: Forma feminina do texto (ex: "cara usuária").
        gender: Gênero gramatical do destinatário. Se None,
            retorna masculine por padrão.

    Returns:
        Forma gramatical apropriada do texto.

    Examples:
        >>> pgettext("caro usuário", "cara usuária", GENDER_MASCULINE)
        'caro usuário'
        >>> pgettext("caro usuário", "cara usuária", GENDER_FEMININE)
        'cara usuária'
        >>> pgettext("bom", "boa", GENDER_FEMININE)
        'boa'
    """
    if gender is None:
        return masculine

    if gender == GrammaticalGender.FEMININE:
        return feminine

    return masculine


def pgettext_key(
    key: str,
    masculine_suffix: str = "-m",
    feminine_suffix: str = "-f",
    gender: Optional[GrammaticalGender] = None,
) -> str:
    """Retorna chave composta para lookup em dicionário de traduções.

    Útil quando as traduções são armazenadas em dicionários
    com sufixos de gênero (ex: {"greeting-m": "...", "greeting-f": "..."}).

    Args:
        key: Chave base da tradução.
        masculine_suffix: Sufixo para forma masculina.
        feminine_suffix: Sufixo para forma feminina.
        gender: Gênero gramatical do destinatário.

    Returns:
        Chave composta com sufixo de gênero apropriado.

    Examples:
        >>> pgettext_key("greeting", gender=GENDER_MASCULINE)
        'greeting-m'
        >>> pgettext_key("greeting", gender=GENDER_FEMININE)
        'greeting-f'
    """
    if gender == GrammaticalGender.FEMININE:
        return f"{key}{feminine_suffix}"
    return f"{key}{masculine_suffix}"


def _normalize_gender(gender: Optional[str]) -> Optional[GrammaticalGender]:
    """Normaliza uma string de gênero para enum GrammaticalGender.

    Aceita variações comuns: "m", "masculino", "male" para masculino
    e "f", "feminino", "female" para feminino.

    Args:
        gender: String representando o gênero.

    Returns:
        GrammaticalGender correspondente ou None se inválido.
    """
    if gender is None:
        return None

    normalized = gender.lower().strip()

    if normalized in ("m", "masculino", "male"):
        return GrammaticalGender.MASCULINE

    if normalized in ("f", "feminino", "female"):
        return GrammaticalGender.FEMININE

    return None


def gettext_gendered(
    translations: dict[str, str],
    key: str,
    gender: Optional[str] = None,
) -> str:
    """Busca tradução genderizada em dicionário.

    Espera chaves no formato: {key}-m e {key}-f no dicionário.

    Args:
        translations: Dicionário de traduções genderizadas.
        key: Chave base da tradução.
        gender: Gênero como string ("m", "f", "masculine", etc).

    Returns:
        Tradução apropriada ou key original se não encontrada.
    """
    gender_enum = _normalize_gender(gender)

    if gender_enum == GrammaticalGender.FEMININE:
        lookup_key = f"{key}-f"
    else:
        lookup_key = f"{key}-m"

    return translations.get(lookup_key, key)