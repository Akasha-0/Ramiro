"""Gerador de diagramas visuais de tiragens — Sistema de Clareza Simbólico-Estratégica.

Módulo responsável por gerar representações visuais em ASCII das tiragens
do Baralho Cigano usando caracteres UTF-8 de box-drawing.

O diagrama mostra as posições da tiragem com seus rótulos contextuais
(e.g., 'Passado', 'Presente', 'Futuro') e o nome da carta quando disponível.

Attributes:
    SpreadDiagramGenerator: Classe principal para gerar diagramas de tiragens.
"""

import logging
from typing import Optional

from src.spread_templates import SpreadPosition, SpreadTemplate, get_template

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Caracteres UTF-8 para box-drawing
# ----------------------------------------------------------------------

BOX_HORIZONTAL = "─"
BOX_VERTICAL = "│"
BOX_CROSS = "┼"
BOX_T_DOWN = "┬"
BOX_T_UP = "┴"
BOX_T_RIGHT = "├"
BOX_T_LEFT = "┤"
BOX_DOWN_RIGHT = "┌"
BOX_DOWN_LEFT = "┐"
BOX_UP_RIGHT = "└"
BOX_UP_LEFT = "┘"


# ----------------------------------------------------------------------
# Formatadores de posição
# ----------------------------------------------------------------------


def _format_context_label(context: str) -> str:
    """Formata o contexto da posição para exibição.

    Args:
        context: Contexto original (e.g., "passado", "presente", "futuro").

    Returns:
        Contexto capitalizado para exibição (e.g., "Passado", "Presente").
    """
    context_map: dict[str, str] = {
        "passado": "Passado",
        "presente": "Presente",
        "futuro": "Futuro",
        "futuro-proximo": "Futuro Próximo",
        "futuro-distante": "Futuro Distante",
        "desafio": "Desafio",
        "base": "Base",
        "possivel": "Possível",
        "voz-interna": "Voz Interna",
        "ambiente": "Ambiente",
        "esperanca": "Esperança",
        "resultado": "Resultado",
        "situacao": "Situação",
        "opcao-a": "Opção A",
        "opcao-b": "Opção B",
        "fator-escondido": "Fator Escondido",
        "resposta": "Resposta",
        "voce": "Você",
        "ele-ela": "Ele/Ela",
        "relacao": "Relação",
        "passado-recente": "Passado Recente",
    }
    return context_map.get(context, context.replace("-", " ").title())


def _format_card_label(card_name: Optional[str], position: int) -> str:
    """Formata o rótulo da carta para exibição.

    Args:
        card_name: Nome da carta (ou None se vazia).
        position: Número da posição.

    Returns:
        Rótulo formatado da carta.
    """
    if card_name:
        return card_name
    return f"[Posição {position}]"


# ----------------------------------------------------------------------
# Gerador de diagramas
# ----------------------------------------------------------------------


class SpreadDiagramGenerator:
    """Gerador de diagramas visuais ASCII para tiragens do Baralho Cigano.

    Gera representações visuais das posições da tiragem usando caracteres
    UTF-8 de box-drawing. Suporta múltiplos layouts de templates.

    Attributes:
        include_context: Se True, inclui o contexto da posição (default True).
    """

    # Largura de cada célula do diagrama
    CELL_WIDTH = 16

    def __init__(self, include_context: bool = True) -> None:
        self.include_context = include_context
        logger.debug("SpreadDiagramGenerator inicializado, include_context=%s", include_context)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def generate(self, template: SpreadTemplate) -> str:
        """Gera o diagrama ASCII para um template de tiragem.

        Args:
            template: SpreadTemplate com as posições da tiragem.

        Returns:
            String contendo o diagrama visual em ASCII.
        """
        logger.info("Gerando diagrama para template '%s' com %d posições",
                    template.name, len(template.positions))

        # Selecionar o formatador apropriado baseado no número de posições
        num_positions = len(template.positions)

        if num_positions <= 1:
            diagram = self._generate_single_card_diagram(template)
        elif num_positions == 3:
            diagram = self._generate_tres_cartas_diagram(template)
        elif num_positions == 5:
            diagram = self._generate_cinco_cartas_diagram(template)
        elif num_positions == 7:
            diagram = self._generate_ferradura_diagram(template)
        elif num_positions == 10:
            diagram = self._generate_cruz_celtas_diagram(template)
        else:
            # Fallback: diagrama linear genérico
            diagram = self._generate_linear_diagram(template)

        logger.debug("Diagrama gerado com %d caracteres", len(diagram))
        return diagram

    def generate_from_positions(self, positions: list[SpreadPosition]) -> str:
        """Gera o diagrama a partir de uma lista de posições.

        Args:
            positions: Lista de SpreadPosition com cartas atribuídas.

        Returns:
            String contendo o diagrama visual em ASCII.
        """
        # Criar um template temporário para usar o generator
        template = SpreadTemplate(
            name="custom",
            display_name="Tiragem Personalizada",
            description="Tiragem com posições personalizadas",
            positions=positions,
        )
        return self.generate(template)

    def generate_linear(self, cards: list[tuple[str, str, str]]) -> str:
        """Gera diagrama linear para lista simples de cartas.

        Método utilitário que aceita uma lista de tuplas com (posição, contexto, nome_da_carta)
        e gera um diagrama visual linear sem necessidade de criar um SpreadTemplate.

        Args:
            cards: Lista de tuplas (position, context, card_name).
                   Ex: [('1', 'Passado', 'Estrela'), ('2', 'Presente', 'Cruz')]

        Returns:
            String contendo o diagrama visual em ASCII.
        """
        if not cards:
            logger.warning("generate_linear chamado com lista vazia")
            return "## Disposição\n\n[Nenhuma carta disponível]\n"

        logger.debug("Gerando diagrama linear para %d cartas", len(cards))

        lines = ["## Disposição", ""]

        # Calcular largura máxima do conteúdo
        max_card_len = max(len(card[2]) for card in cards)
        max_context_len = max(len(card[1]) for card in cards)
        cell_width = max(max_card_len + 2, max_context_len + 2, 10)

        # Cabeçalho com contextos (se habilitado)
        if self.include_context:
            context_parts = [f"[{card[1]:^{cell_width - 2}}]" for card in cards]
            # Usar mesmo padrão de conector: ├──┼──┘
            connector = "─" * 3
            if len(context_parts) == 1:
                header_line = "   " + connector + "   "
            else:
                header_line = "   " + connector + "┼" + connector.join([""] * (len(context_parts) - 1)) + "   "
            lines.append(header_line)
            lines.append("   " + "  ".join(context_parts))
            lines.append("")

        # Construir boxes horizontais conectados
        # Primeira célula: ├──
        # Células intermediárias: ├── (para n > 2)
        # Última célula: ┘
        if len(cards) == 1:
            top_line = "   " + BOX_DOWN_RIGHT + BOX_HORIZONTAL * (cell_width - 2) + BOX_DOWN_LEFT
            bottom_line = "   " + BOX_UP_RIGHT + BOX_HORIZONTAL * (cell_width - 2) + BOX_UP_LEFT
        else:
            # Primeira parte: ├── (T_DOWN na junção)
            top_parts = [BOX_T_RIGHT + BOX_HORIZONTAL * (cell_width - 2)]
            # Partes do meio: +── (para n > 2)
            for _ in range(len(cards) - 2):
                top_parts.append(BOX_CROSS + BOX_HORIZONTAL * (cell_width - 2))
            # Última parte: ┘
            top_parts.append(BOX_DOWN_LEFT)
            top_line = "   " + "".join(top_parts)

            # Linha inferior
            bottom_parts = [BOX_T_RIGHT + BOX_HORIZONTAL * (cell_width - 2)]
            for _ in range(len(cards) - 2):
                bottom_parts.append(BOX_CROSS + BOX_HORIZONTAL * (cell_width - 2))
            bottom_parts.append(BOX_UP_LEFT)
            bottom_line = "   " + "".join(bottom_parts)

        lines.append(top_line)

        # Linhas de conteúdo (nome da carta)
        content_line = "   " + BOX_VERTICAL
        for card in cards:
            # Usar card_name completo com padding para alinhar
            card_label = card[2]
            # Garantir alinhamento: padding para a largura máxima da carta
            card_padded = f" {card_label:<{max_card_len}} "
            content_line += card_padded + BOX_VERTICAL
        lines.append(content_line)

        lines.append(bottom_line)
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Diagramas específicos por template
    # ------------------------------------------------------------------

    def _generate_single_card_diagram(self, template: SpreadTemplate) -> str:
        """Gera diagrama para tiragem de uma carta."""
        pos = template.positions[0]
        card_label = _format_card_label(pos.card_name, pos.position)

        lines = [
            "## Disposição",
            "",
            f"     {BOX_DOWN_RIGHT}{BOX_HORIZONTAL * 16}{BOX_DOWN_LEFT}",
            f"     {BOX_VERTICAL}                {BOX_VERTICAL}",
            f"     {BOX_VERTICAL}     {card_label:<12} {BOX_VERTICAL}",
            f"     {BOX_VERTICAL}                {BOX_VERTICAL}",
        ]

        if self.include_context:
            context_label = _format_context_label(pos.context)
            lines.append(f"     {BOX_VERTICAL}   [{context_label}]     {BOX_VERTICAL}")
        else:
            lines.append(f"     {BOX_VERTICAL}                {BOX_VERTICAL}")

        lines.extend([
            f"     {BOX_UP_RIGHT}{BOX_HORIZONTAL * 16}{BOX_UP_LEFT}",
            "",
        ])

        return "\n".join(lines)

    def _generate_tres_cartas_diagram(self, template: SpreadTemplate) -> str:
        """Gera diagrama para tiragem de três cartas (passado-presente-futuro)."""
        # Formatar células: posição + carta ou posição vazia
        cells: list[tuple[str, str]] = []
        for p in template.positions:
            context_label = _format_context_label(p.context) if self.include_context else ""
            card_label = _format_card_label(p.card_name, p.position)
            cells.append((context_label, card_label))

        # Calcular largura máxima do conteúdo
        max_card_len = max(len(card) for _, card in cells)
        max_context_len = max(len(ctx) for ctx, _ in cells) if self.include_context else 0
        cell_width = max(max_card_len + 2, max_context_len + 2, 10)

        def make_cell(context: str, card: str) -> list[str]:
            """Cria uma célula box com contexto e carta."""
            card_padded = f" {card:<{cell_width - 2}} "
            if self.include_context and context:
                context_line = f"  [{context:<{cell_width - 4}}]  "
            else:
                context_line = " " * (cell_width + 4)
            return [card_padded, context_line]

        # Construir diagrama linha por linha
        lines = ["## Disposição", ""]

        # Linha superior com contextos (se habilitado)
        if self.include_context:
            header_parts = [f"[{cells[i][0]:^{cell_width - 2}}]" for i in range(3)]
            lines.append("   " + "─" * 3 + "─┼─" * (len(header_parts) - 1) + "─" * 3 + "   ")
            lines.append("   " + "  ".join(header_parts))
            lines.append("")

        # Desenhar boxes horizontais conectados
        h_line = BOX_DOWN_RIGHT + (BOX_HORIZONTAL * (cell_width - 2) + BOX_T_DOWN + BOX_HORIZONTAL * (cell_width - 2) + BOX_T_DOWN + BOX_HORIZONTAL * (cell_width - 2)) + BOX_DOWN_LEFT
        lines.append("   " + h_line)

        # Linhas de conteúdo
        for row_idx in range(2):  # card + contexto
            row_line = "   " + BOX_VERTICAL
            for i, (_, card) in enumerate(cells):
                cell_lines = make_cell(cells[i][0], card)
                content = cell_lines[row_idx] if row_idx < len(cell_lines) else " " * (cell_width)
                row_line += content + BOX_VERTICAL
            lines.append(row_line)

        # Linha inferior
        bottom_line = "   " + BOX_UP_RIGHT + (BOX_HORIZONTAL * (cell_width - 2) + BOX_T_UP + BOX_HORIZONTAL * (cell_width - 2) + BOX_T_UP + BOX_HORIZONTAL * (cell_width - 2)) + BOX_UP_LEFT
        lines.append(bottom_line)
        lines.append("")

        return "\n".join(lines)

    def _generate_cinco_cartas_diagram(self, template: SpreadTemplate) -> str:
        """Gera diagrama para tiragem de cinco cartas (decisão/escolha)."""
        lines = ["## Disposição", ""]

        if self.include_context:
            contexts = [_format_context_label(p.context) for p in template.positions]
            lines.append("   " + "  ".join(f"[{c}]" for c in contexts))
            lines.append("")

        # Diagrama em linha horizontal para 5 cartas
        cells = []
        for pos in template.positions:
            card_label = _format_card_label(pos.card_name, pos.position)
            cells.append(f"[{card_label}]")

        # Construir linha com conexões
        separator = f"  {BOX_HORIZONTAL * 3}  "
        line = "  " + separator.join(cells)
        lines.append(line)
        lines.append("")

        return "\n".join(lines)

    def _generate_ferradura_diagram(self, template: SpreadTemplate) -> str:
        """Gera diagrama para tiragem ferradura (7 posições em arco)."""
        lines = ["## Disposição", ""]

        if self.include_context:
            # Posições do arco: 1-2-3 no topo, 4-5-6-7 embaixo
            # Primeiro arco: posições 1, 2, 3
            top_contexts = [_format_context_label(p.context) for p in template.positions[:3]]
            bottom_contexts = [_format_context_label(p.context) for p in template.positions[3:]]

            lines.append("      " + "  ".join(f"[{c}]" for c in top_contexts))
            lines.append("")

        # Desenho da ferradura
        # Posição 1 (topo esquerdo)
        pos1 = template.positions[0]
        pos2 = template.positions[1]
        pos3 = template.positions[2]
        pos4 = template.positions[3]
        pos5 = template.positions[4]
        pos6 = template.positions[5]
        pos7 = template.positions[6]

        # Linha superior do arco
        lines.append("     " + BOX_DOWN_RIGHT + BOX_HORIZONTAL * 5 + BOX_T_DOWN + BOX_HORIZONTAL * 5 + BOX_T_DOWN + BOX_HORIZONTAL * 5 + BOX_DOWN_LEFT)
        lines.append("     " + BOX_VERTICAL + " " * 5 + BOX_VERTICAL + " " * 5 + BOX_VERTICAL + " " * 5 + BOX_VERTICAL)

        # Cartas do topo
        label1 = _format_card_label(pos1.card_name, pos1.position)
        label2 = _format_card_label(pos2.card_name, pos2.position)
        label3 = _format_card_label(pos3.card_name, pos3.position)
        lines.append(f"     {BOX_VERTICAL} {label1:<4} {BOX_VERTICAL} {label2:<4} {BOX_VERTICAL} {label3:<4} {BOX_VERTICAL}")

        # Linha do meio com conexão para baixo
        lines.append("     " + BOX_UP_RIGHT + BOX_HORIZONTAL * 5 + BOX_T_UP + BOX_HORIZONTAL * 5 + BOX_T_UP + BOX_HORIZONTAL * 5 + BOX_UP_LEFT)
        lines.append(" " * 14 + BOX_VERTICAL + " " * 13 + BOX_VERTICAL)

        # Posição 4 (meio-direita)
        label4 = _format_card_label(pos4.card_name, pos4.position)
        lines.append(" " * 14 + BOX_VERTICAL + " " + label4 + " " * 7 + BOX_VERTICAL)
        lines.append(" " * 14 + BOX_VERTICAL + " " * 13 + BOX_VERTICAL)

        # Posição 5 (baixo-direita)
        label5 = _format_card_label(pos5.card_name, pos5.position)
        lines.append(" " * 14 + BOX_UP_RIGHT + BOX_HORIZONTAL * 5 + BOX_T_UP + BOX_HORIZONTAL * 5 + BOX_UP_LEFT)
        lines.append(" " * 14 + BOX_VERTICAL + " " * 5 + BOX_VERTICAL + " " * 5 + BOX_VERTICAL)

        # Posições 6 e 7
        label6 = _format_card_label(pos6.card_name, pos6.position)
        label7 = _format_card_label(pos7.card_name, pos7.position)
        lines.append(" " * 14 + BOX_VERTICAL + " " + label6 + " " * 5 + BOX_VERTICAL + " " + label7 + " " + BOX_VERTICAL)
        lines.append(" " * 14 + BOX_UP_RIGHT + BOX_HORIZONTAL * 5 + BOX_UP_LEFT + " " * 5 + BOX_UP_RIGHT + BOX_HORIZONTAL * 5 + BOX_UP_LEFT)
        lines.append("")

        return "\n".join(lines)

    def _generate_cruz_celtas_diagram(self, template: SpreadTemplate) -> str:
        """Gera diagrama para Cruz Celta (10 posições).

        Layout:
          4   3   2
             10
          5   1   9
             8
          6   7

        Posições de baixo: 6, 7
        Posição central: 8
        Posição direita: 9
        Posição esquerda: 5
        Posição superior: 4, 3, 2 (cima)
        Centro: 1
        Posição cruzando centro: 10
        """
        lines = ["## Disposição", ""]

        if self.include_context:
            contexts = [_format_context_label(p.context) for p in template.positions]
            # Exibir contextos em formato compacto
            lines.append("   " + "  ".join(f"[{c}]" for c in contexts))
            lines.append("")

        # Mapear posições
        pos = {p.position: p for p in template.positions}

        def card_short(pos_idx: int) -> str:
            if pos_idx in pos:
                label = _format_card_label(pos[pos_idx].card_name, pos_idx)
                return label[:10]  # Curta para caber
            return f"Pos.{pos_idx}"

        # Desenho da Cruz Celta
        # Linha superior: 4 - 3 - 2
        top_line = f"        {BOX_DOWN_RIGHT}{BOX_HORIZONTAL * 9}{BOX_T_DOWN}{BOX_HORIZONTAL * 9}{BOX_T_DOWN}{BOX_HORIZONTAL * 9}{BOX_DOWN_LEFT}"
        lines.append(top_line)
        lines.append(f"        {BOX_VERTICAL} {card_short(4):<8} {BOX_VERTICAL} {card_short(3):<8} {BOX_VERTICAL} {card_short(2):<8} {BOX_VERTICAL}")

        # Posição 10 cruzando
        lines.append(f"        {BOX_UP_RIGHT}{BOX_HORIZONTAL * 9}{BOX_CROSS}{BOX_HORIZONTAL * 9}{BOX_CROSS}{BOX_HORIZONTAL * 9}{BOX_UP_LEFT}")
        lines.append(f"                  {BOX_VERTICAL} {card_short(10):<8} {BOX_VERTICAL}")
        lines.append(f"        {BOX_DOWN_RIGHT}{BOX_HORIZONTAL * 9}{BOX_T_DOWN}{BOX_HORIZONTAL * 9}{BOX_T_DOWN}{BOX_HORIZONTAL * 9}{BOX_DOWN_LEFT}")

        # Linha do meio: 5 - 1 - 9
        lines.append(f"        {BOX_VERTICAL} {card_short(5):<8} {BOX_VERTICAL} {card_short(1):<8} {BOX_VERTICAL} {card_short(9):<8} {BOX_VERTICAL}")
        lines.append(f"        {BOX_UP_RIGHT}{BOX_HORIZONTAL * 9}{BOX_T_UP}{BOX_HORIZONTAL * 9}{BOX_T_UP}{BOX_HORIZONTAL * 9}{BOX_UP_LEFT}")

        # Posição 8
        lines.append(f"                  {BOX_VERTICAL} {card_short(8):<8} {BOX_VERTICAL}")
        lines.append(f"        {BOX_DOWN_RIGHT}{BOX_HORIZONTAL * 9}{BOX_T_DOWN}{BOX_HORIZONTAL * 9}{BOX_T_DOWN}{BOX_HORIZONTAL * 9}{BOX_DOWN_LEFT}")

        # Posições 6 e 7
        lines.append(f"        {BOX_VERTICAL} {card_short(6):<8} {BOX_VERTICAL} {card_short(7):<8} {BOX_VERTICAL}")
        lines.append(f"        {BOX_UP_RIGHT}{BOX_HORIZONTAL * 9}{BOX_UP_LEFT} {BOX_UP_RIGHT}{BOX_HORIZONTAL * 9}{BOX_UP_LEFT}")
        lines.append("")

        return "\n".join(lines)

    def generate_celtic_cross(self, cards: list[tuple[str, str, str]]) -> str:
        """Gera diagrama visual para tiragem Celtic Cross (10 posições).

        Layout da Cruz Celta:
            [4]   [3]   [2]
                   [10]
            [5]   [1]    [9]
                   [8]
            [6]   [7]

        Args:
            cards: Lista de tuplas (position, context, card_name).
                   Ex: [('1', 'Presente', 'Estrela'), ('2', 'Desafio', 'Cruz'), ...]

        Returns:
            String contendo o diagrama visual em ASCII.
        """
        if not cards:
            logger.warning("generate_celtic_cross chamado com lista vazia")
            return "## Disposição\n\n[Nenhuma carta disponível]\n"

        logger.debug("Gerando diagrama Celtic Cross para %d cartas", len(cards))

        # Mapear cartas por posição
        card_map: dict[int, tuple[str, str]] = {}
        for card in cards:
            try:
                pos_idx = int(card[0])
                card_map[pos_idx] = (card[1], card[2])  # (context, card_name)
            except (ValueError, IndexError):
                logger.warning(" carta com posição inválida: %s", card)

        lines = ["## Disposição", ""]

        # Células de tamanho fixo para as 10 posições do Celtic Cross
        # Layout: posições de cima (4,3,2), posição 10 central, meio (5,1,9), posição 8, baixo (6,7)
        cell_width = 16

        def get_card(pos_idx: int) -> str:
            """Obtém o nome da carta para uma posição."""
            if pos_idx in card_map:
                name = card_map[pos_idx][1]
                # Se a carta é um nome real, mostrar "Posição X: Nome"
                if name:
                    return f"Posição {pos_idx}: {name}"
            return f"Posição {pos_idx}"

        def get_context(pos_idx: int) -> str:
            """Obtém o contexto para uma posição."""
            if pos_idx in card_map:
                return _format_context_label(card_map[pos_idx][0])
            return ""

        # Linhas horizontais reutilizáveis
        h_border = BOX_HORIZONTAL * (cell_width - 2)
        top_border = BOX_DOWN_RIGHT + h_border
        mid_border = BOX_UP_RIGHT + h_border
        sep_cross = BOX_CROSS + h_border
        sep_t_down = BOX_T_DOWN + h_border
        sep_t_up = BOX_T_UP + h_border

        # Linha superior: 4 - 3 - 2
        lines.append(f"       {top_border}{BOX_T_DOWN}{h_border}{BOX_T_DOWN}{h_border}{BOX_DOWN_LEFT}")

        # Nomes das cartas do topo
        lines.append(f"       {BOX_VERTICAL} {get_card(4):<{cell_width - 2}} {BOX_VERTICAL} {get_card(3):<{cell_width - 2}} {BOX_VERTICAL} {get_card(2):<{cell_width - 2}} {BOX_VERTICAL}")

        # Posição 10 (cruzando acima da posição 1)
        lines.append(f"       {mid_border}{BOX_CROSS}{h_border}{BOX_CROSS}{h_border}{BOX_UP_LEFT}")

        # Nome da posição 10 (centralizado) - alinhado com as células do meio
        lines.append(f"              {BOX_VERTICAL} {get_card(10):<{cell_width - 2}} {BOX_VERTICAL}")

        # Linha divisória inferior da posição 10
        lines.append(f"       {top_border}{BOX_T_DOWN}{h_border}{BOX_T_DOWN}{h_border}{BOX_DOWN_LEFT}")

        # Linha do meio: 5 - 1 - 9
        lines.append(f"       {BOX_VERTICAL} {get_card(5):<{cell_width - 2}} {BOX_VERTICAL} {get_card(1):<{cell_width - 2}} {BOX_VERTICAL} {get_card(9):<{cell_width - 2}} {BOX_VERTICAL}")

        # Linha inferior das posições do meio
        lines.append(f"       {mid_border}{BOX_T_UP}{h_border}{BOX_T_UP}{h_border}{BOX_UP_LEFT}")

        # Posição 8 (centralizado)
        lines.append(f"              {BOX_VERTICAL} {get_card(8):<{cell_width - 2}} {BOX_VERTICAL}")

        # Linha divisória para posição 8
        lines.append(f"       {top_border}{BOX_T_DOWN}{h_border}{BOX_T_DOWN}{h_border}{BOX_DOWN_LEFT}")

        # Posições 6 e 7 (inferior esquerdo)
        lines.append(f"       {BOX_VERTICAL} {get_card(6):<{cell_width - 2}} {BOX_VERTICAL} {get_card(7):<{cell_width - 2}} {BOX_VERTICAL}")

        # Linha final
        lines.append(f"       {mid_border}{BOX_UP_LEFT}   {mid_border}{BOX_UP_LEFT}")
        lines.append("")

        return "\n".join(lines)

    def _generate_linear_diagram(self, template: SpreadTemplate) -> str:
        """Gera diagrama linear genérico para templates não específicos."""
        lines = ["## Disposição", ""]

        if self.include_context:
            contexts = [_format_context_label(p.context) for p in template.positions]
            header = "  " + "  ".join(f"[{c}]" for c in contexts)
            lines.append(header)
            lines.append("")

        # Diagrama em linha horizontal
        cells = []
        for pos in template.positions:
            card_label = _format_card_label(pos.card_name, pos.position)
            # Truncar se muito longo
            short_label = card_label[:12]
            cells.append(f"[{short_label}]")

        # Construir linha com conexões usando box-drawing
        connector = f" {BOX_HORIZONTAL * 3} "
        line = "  " + connector.join(cells)
        lines.append(line)
        lines.append("")

        return "\n".join(lines)
