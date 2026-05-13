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

from clareza.types import CardPosition, StructuredInput
from clareza.spread_templates import get_template, SpreadTemplate

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
        recovery: Orientação de recuperação em português (opcional).
    """

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        details: Optional[str] = None,
        recovery: Optional[str] = None,
    ) -> None:
        self.message = message
        self.line = line
        self.details = details
        self.recovery = recovery
        full = message
        if line is not None:
            full = f"{message} (linha {line})"
        if details:
            full = f"{full}: {details}"
        if recovery:
            full = f"{full}\nDica: {recovery}"
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
            raise ParseError(
                "Conteúdo CSV vazio",
                details="Nenhuma linha para parsear",
                recovery="Verifique se o arquivo contém dados. Use formato: pos,carta (uma carta por linha)",
            )

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
                recovery="Remova a linha de cabeçalho ou adicione linhas de dados no formato: pos,carta",
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
                    recovery="Use vírgula, ponto-e-vírgula ou tabulação para separar posição e nome da carta. Exemplo: 1,estrela",
                )

            try:
                position = int(parsed[0])
            except ValueError:
                raise ParseError(
                    "Posição inválida",
                    line=line_no,
                    details=f"Esperado número, encontrado: {parsed[0]!r}",
                    recovery="Use apenas números inteiros para a posição. Exemplo: 1,estrela ou 2,casa",
                )

            if position < 1:
                raise ParseError(
                    "Posição deve ser maior que zero",
                    line=line_no,
                    details=f"Posição: {position}",
                    recovery="Posições válidas começam em 1. Use números positivos: 1, 2, 3, etc.",
                )

            card_name = " ".join(parsed[1:]).strip()
            if not card_name:
                raise ParseError(
                    "Nome da carta ausente",
                    line=line_no,
                    details="A posição existe mas o nome da carta está vazio",
                    recovery="Informe o nome da carta após a posição. Exemplo: 1,estrela",
                )

            # Validar se a carta existe no catálogo (com backward compat para prefixos 'A ' e 'O ')
            from clareza.symbols import get_symbol_by_name as _get_by_name, get_similar_card_names as _get_similar, get_all_symbols as _get_all

            resolved_name = None
            for name_to_try in [card_name, f"A {card_name}", f"O {card_name}"]:
                symbol = _get_by_name(name_to_try)
                if symbol is not None:
                    resolved_name = symbol.name
                    break

            if resolved_name is None:
                similar = _get_similar(card_name, n=3)
                details = f"'{card_name}' não encontrada no catálogo do Baralho Cigano"
                if similar:
                    cards_list = ", ".join(similar)
                    recovery = f"Cartão desconhecido: '{card_name}'. Cards válidos: {cards_list}"
                else:
                    all_card_names = [s.name for s in _get_all()]
                    all_names_str = ", ".join(all_card_names[:10]) + "..."
                    recovery = f"Cartão desconhecido: '{card_name}'. Cards válidos: {all_names_str}"
                raise ParseError(
                    "Cartão desconhecido",
                    line=line_no,
                    details=details,
                    recovery=recovery,
                )

            card_name = resolved_name
            cards.append(CardPosition(position=position, card_name=card_name))

        if not cards:
            raise ParseError(
                "Nenhuma carta válida encontrada no CSV",
                details="Verifique o formato: pos,carta (uma carta por linha)",
                recovery="Use o formato: posição,nome_da_carta (uma carta por linha). Exemplo: 1,estrela\\n2,casa",
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

    # ------------------------------------------------------------------
    # File path e template support
    # ------------------------------------------------------------------

    def parse_from_file(
        self,
        file_path: str,
        template_name: Optional[str] = None,
    ) -> StructuredInput:
        """Lê e parseia conteúdo de um arquivo CSV.

        Suporta leitura de arquivos com caminho absoluto ou relativo.
        Opcionalmente aplica um template de tiragem para inferir contexto.

        Args:
            file_path: Caminho para o arquivo CSV.
            template_name: Nome do template opcional para contexto de posições.

        Returns:
            StructuredInput com dados parseados do arquivo.

        Raises:
            ParseError: Se o arquivo não puder ser lido ou parseado.
            FileNotFoundError: Se o arquivo não existir.
        """
        logger.debug("Lendo arquivo CSV: %s", file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            raise ParseError(
                "Arquivo não encontrado",
                details=f"Caminho: {file_path!r}",
                recovery="Verifique se o caminho está correto e se o arquivo existe. Caminhos válidos devem ter extensão .csv ou .txt",
            )
        except PermissionError:
            raise ParseError(
                "Sem permissão para ler o arquivo",
                details=f"Caminho: {file_path!r}",
                recovery="Verifique as permissões do arquivo. Tente executar com permissões adequadas.",
            )
        except OSError as e:
            raise ParseError(
                "Erro ao ler arquivo",
                details=str(e),
                recovery="Verifique se o arquivo não está corrompido ou em uso por outro processo.",
            )

        result = self.parse(content, "spread")

        # Se template foi fornecido, aplicar contexto às posições
        if template_name and result.cards:
            result = self._apply_template_context(result, template_name)

        return result

    def _apply_template_context(
        self,
        structured_input: StructuredInput,
        template_name: str,
    ) -> StructuredInput:
        """Aplica contexto de um template às posições de uma tiragem.

        Usa o template para determinar o position_context de cada carta
        baseada na sua posição.

        Args:
            structured_input: StructuredInput com cartas parseadas.
            template_name: Nome do template a aplicar.

        Returns:
            StructuredInput com position_context preenchido em cada carta.

        Raises:
            ParseError: Se o template não existir.
        """
        if not structured_input.cards:
            return structured_input

        template = get_template(template_name)
        if template is None:
            raise ParseError(
                "Template não encontrado",
                details=f"Template: {template_name!r}",
                recovery="Verifique se o nome do template está correto. Use --template com valores como: 3-card, celtic-cross, simple",
            )

        # Mapear contextos do template para as posições
        context_by_position: dict[int, str] = {}
        for pos in template.positions:
            context_by_position[pos.position] = pos.context

        # Aplicar contexto às cartas
        updated_cards: list[CardPosition] = []
        for card in structured_input.cards:
            context = context_by_position.get(card.position)
            if context:
                updated_cards.append(
                    CardPosition(
                        position=card.position,
                        card_name=card.card_name,
                        interpretation=card.interpretation,
                        position_context=context,
                    )
                )
            else:
                updated_cards.append(card)

        return StructuredInput(
            format=structured_input.format,
            raw_content=structured_input.raw_content,
            cards=updated_cards,
            keywords=structured_input.keywords,
        )

    def parse_with_context(
        self,
        content: str,
        template_name: Optional[str] = None,
    ) -> StructuredInput:
        """Parseia conteúdo CSV com contexto de template opcional.

        Wrapper conveniente que combina parse() e _apply_template_context().

        Args:
            content: Conteúdo CSV ou texto.
            template_name: Nome do template opcional.

        Returns:
            StructuredInput com contexto de template aplicado se fornecido.
        """
        result = self.parse(content, "spread")
        if template_name:
            result = self._apply_template_context(result, template_name)
        return result
