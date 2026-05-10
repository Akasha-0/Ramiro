"""Processador de entrada — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por parsear e normalizar entradas do usuário em três formatos:
- text: texto livre em português
- spread: tiragem CSV com posição e nome da carta
- symbols: lista de símbolos/keywords separados por vírgula

Toda saída é um StructuredInput (types.py) — nenhum dicionário solto.
"""

import csv
import io
import logging
import re
from typing import Optional

from src.types import CardPosition, StructuredInput

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Exceções
# ----------------------------------------------------------------------


class ParseError(Exception):
    """Exceção lançada quando o parse de entrada falha.

    Attributes:
        message: Descrição legível do erro.
        line: Número da linha onde ocorreu o erro (para CSV, opcional).
        details: Detalhes adicionais sobre a natureza do erro.
    """

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        details: Optional[str] = None,
    ) -> None:
        self.message = message
        self.line = line
        self.details = details
        full = message
        if line is not None:
            full = f"{message} (linha {line})"
        if details:
            full = f"{full}: {details}"
        super().__init__(full)


# ----------------------------------------------------------------------
# Stop words em português (usadas para filtrar keywords irrelevantes)
# ----------------------------------------------------------------------

_PORTUGUESE_STOP_WORDS: set[str] = {
    "eu", "tu", "ele", "ela", "nós", "vós", "eles", "elas",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas",
    "seu", "sua", "seus", "suas", "nosso", "nossa", "nossos", "nossas",
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "para", "por", "com", "sem", "sobre", "sob", "ante", "após", "até",
    "e", "ou", "mas", "nem", "que", "qual", "quais", "quem", "onde",
    "como", "quando", "por quê", "porque", "porque", "porquê",
    "muito", "mais", "menos", "muita", "muitos", "pouco", "pouca",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas", "isto", "isso", "aquilo",
    "já", "ainda", "agora", "sempre", "nunca", "hoje", "amanhã", "ontem",
    "aqui", "ali", "lá", "onde", "aí",
    "ter", "terei", "tenho", "tinha", "teria", "há", "há", "houve",
    "ser", "serei", "sou", "era", "seria", "estar", "estou", "estava",
    "estaria", "há", "haver", "haverá", "ver", "vi",
    "fazer", "faço", "fiz", "fez", "ir", "vou", "fui", "foi",
    "poder", "posso", "podem", "poderia", "pude",
    "querer", "quero", "quiser", "quer", "querem",
    "verdade", "sim", "não", "nada", "ninguém", "todo", "toda",
    "todos", "todas", "outro", "outra", "outros", "outras",
    "próprio", "própria", "mesmo", "mesma", "certo", "certa",
    "sentir", "sinto", "sente", "sentindo", "sentir", "sinto",
    "ficar", "fico", "fica", "ficou", "ficar", "estou", "estava",
    "achar", "acho", "acha", "achou", "achava",
    "pensar", "penso", "pensa", "pensou", "pensava",
    "ver", "vejo", "vê", "viu", "via", "veja",
    "saber", "sei", "sabe", "soube", "sabia",
    "falar", "falo", "fala", "falou", "falava",
    "verdade", "real", "coisa", "coisas", "pessoa", "pessoas",
    "vida", "vez", "vezes", "dia", "dias", "ano", "anos",
    "tempo", "lado", "lugar", "coisa", "jeito", "forma", "maneira",
    "parte", "caso", "negócio", "situação", "assunto",
}

# Padrão regex para extrair palavras significativas em português
_WORD_PATTERN = re.compile(r"[a-záàâãéèêíìóòôõúùûç-]+", re.IGNORECASE)

# Limite máximo de caracteres para input
MAX_INPUT_LENGTH = 5000


# ----------------------------------------------------------------------
# Processador principal
# ----------------------------------------------------------------------


class InputProcessor:
    """Parser de entrada para múltiplos formatos.

    Suporta três formatos de entrada:
    - "text": texto livre — extrai keywords significativas
    - "spread": CSV com posição e carta — parseia tiragem do Baralho Cigano
    - "symbols": lista separada por vírgula — normaliza símbolos/keywords

    Attributes:
        max_length: Limite máximo de caracteres da entrada (default 5000).
    """

    VALID_FORMATS: list[str] = ["text", "spread", "symbols"]

    def __init__(self, max_length: int = MAX_INPUT_LENGTH) -> None:
        self.max_length = max_length

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def parse(self, content: str, format: str) -> StructuredInput:
        """Parseia conteúdo de acordo com o formato especificado.

        Args:
            content: Texto bruto de entrada.
            format: Um de "text", "spread" ou "symbols".

        Returns:
            StructuredInput com dados parseados e normalizados.

        Raises:
            ParseError: Se o formato for desconhecido ou o conteúdo inválido.
            ValueError: Se o formato não for um dos valores válidos.
        """
        if format not in self.VALID_FORMATS:
            raise ValueError(
                f"Formato desconhecido: {format!r}. "
                f"Valores válidos: {self.VALID_FORMATS}"
            )

        logger.debug("Parseando input format=%r, length=%d", format, len(content))

        # Truncar se necessário
        truncated, was_truncated = self._truncate(content)
        if was_truncated:
            logger.warning(
                "Input excede limite de %d caracteres, truncando", self.max_length
            )

        if format == "text":
            return self._parse_free_text(truncated)
        elif format == "spread":
            return self._parse_csv_spread(truncated)
        elif format == "symbols":
            return self._parse_symbols(truncated)
        else:
            # Impossível chegar aqui por causa da validação acima, mas
            # mantemos segurança caso um novo formato seja adicionado
            raise ValueError(f"Formato não suportado: {format!r}")

    # ------------------------------------------------------------------
    # Parsers por formato
    # ------------------------------------------------------------------

    def _parse_free_text(self, content: str) -> StructuredInput:
        """Extrai keywords de um texto livre em português.

        Filtra stop words e retorna apenas palavras significativas
        que podem ser usadas para mapeamento simbólico.

        Args:
            content: Texto em português para análise.

        Returns:
            StructuredInput com format="text" e keywords extraídas.
        """
        words = _WORD_PATTERN.findall(content.lower())
        keywords = [
            w for w in words
            if len(w) >= 3 and w not in _PORTUGUESE_STOP_WORDS
        ]
        # Remover duplicatas preservando ordem
        seen: set[str] = set()
        unique_keywords: list[str] = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return StructuredInput(
            format="text",
            raw_content=content,
            cards=None,
            keywords=unique_keywords,
        )

    def _parse_csv_spread(self, content: str) -> StructuredInput:
        """Parseia conteúdo CSV de tiragem do Baralho Cigano.

        Espera formato com colunas "pos" (posição) e "card" (nome da carta).
        Suporta tanto CSV com cabeçalho quanto sem.

        Args:
            content: Conteúdo CSV brut.

        Returns:
            StructuredInput com format="spread" e lista de CardPosition.

        Raises:
            ParseError: Se o CSV estiver mal formatado ou vazio.
        """
        if not content.strip():
            raise ParseError("Conteúdo CSV vazio", details="Nenhuma linha para parsear")

        # Detectar se tem cabeçalho
        lines = content.strip().splitlines()
        reader_kwargs: dict = {"lineterminator": "\n"}

        # Tentar detectar cabeçalho pela primeira linha
        sample = lines[0].strip().lower()
        has_header = any(
            sample.startswith(prefix)
            for prefix in ["pos", "position", "carta", "card"]
        )

        if has_header:
            # Pula a primeira linha (cabeçalho)
            data_lines = lines[1:]
        else:
            data_lines = lines

        if not data_lines:
            raise ParseError(
                "CSV sem dados após cabeçalho",
                details="O arquivo contém apenas o cabeçalho",
            )

        cards: list[CardPosition] = []

        # Criar reader CSV com suporte a separadores comuns
        for line_no, line in enumerate(data_lines, start=2 if has_header else 1):
            raw_line = line.strip()
            if not raw_line:
                continue

            # Tentar múltiplos separadores
            parsed = self._parse_csv_line(raw_line)
            if parsed is None:
                raise ParseError(
                    "Linha com formato CSV inválido",
                    line=line_no,
                    details=f"Não foi possível interpretar: {raw_line!r}",
                )

            try:
                position = int(parsed[0])
            except ValueError:
                raise ParseError(
                    "Posição inválida",
                    line=line_no,
                    details=f"Esperado número, encontrado: {parsed[0]!r}",
                )

            if position < 1:
                raise ParseError(
                    "Posição deve ser maior que zero",
                    line=line_no,
                    details=f"Posição: {position}",
                )

            card_name = " ".join(parsed[1:]).strip()
            if not card_name:
                raise ParseError(
                    "Nome da carta ausente",
                    line=line_no,
                    details="A posição existe mas o nome da carta está vazio",
                )

            cards.append(CardPosition(position=position, card_name=card_name))

        if not cards:
            raise ParseError(
                "Nenhuma carta válida encontrada no CSV",
                details="Verifique o formato: pos,carta (uma carta por linha)",
            )

        return StructuredInput(
            format="spread",
            raw_content=content,
            cards=cards,
            keywords=None,
        )

    def _parse_csv_line(self, line: str) -> Optional[list[str]]:
        """Tenta parsear uma linha CSV com separadores comuns.

        Suporta vírgula, ponto-e-vírgula e tabulação.

        Args:
            line: Linha CSV a parsear.

        Returns:
            Lista de campos ou None se todos os separadores falharem.
        """
        for sep in (",", ";", "\t"):
            if sep in line:
                reader = csv.reader(io.StringIO(line), delimiter=sep)
                result = list(reader)
                if result:
                    return result[0]
        # Fallback: retorna a linha inteira como campo único
        return [line]

    def _parse_symbols(self, content: str) -> StructuredInput:
        """Normaliza lista de símbolos separados por vírgula.

        Cada símbolo é trimado e lowercased para consistência.
        Símbolos vazios são filtrados.

        Args:
            content: Lista de símbolos separados por vírgula.

        Returns:
            StructuredInput com format="symbols" e keywords normalizadas.
        """
        tokens = [t.strip().lower() for t in content.split(",")]
        keywords = [t for t in tokens if t]

        return StructuredInput(
            format="symbols",
            raw_content=content,
            cards=None,
            keywords=keywords if keywords else None,
        )

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def _truncate(self, content: str) -> tuple[str, bool]:
        """Trunca conteúdo que exceda o limite máximo.

        Args:
            content: Texto a verificar.

        Returns:
            Tupla (conteúdo ou truncado, booleano indicando se foi truncado).
        """
        if len(content) <= self.max_length:
            return content, False
        return content[: self.max_length], True
