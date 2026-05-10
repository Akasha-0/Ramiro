"""Templates de tiragens — Sistema de Clareza Simbólico-Estratégica.

Módulo que define layouts predefinidos para tiragens do Baralho Cigano.
Cada template contém posições com seus contextos temporais e descrições.

Attributes:
    TEMPLATES: Dicionário com todos os templates disponíveis.
    get_template: Função para recuperar um template pelo nome.
    SpreadTemplate: Dataclass que define a estrutura de um template.
    SpreadPosition: Dataclass que define uma posição individual.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SpreadPosition:
    """Representa uma posição individual em uma tiragem.

    Attributes:
        position: Índice da posição (1-based).
        context: Contexto temporal ou temática (ex: "passado", "presente", "futuro").
        description: Descrição textual da posição.
        card_name: Nome da carta ou None se é uma posição vazia.
    """

    position: int
    context: str
    description: str
    card_name: Optional[str] = None


@dataclass
class SpreadTemplate:
    """Template de tiragem predefinido.

    Attributes:
        name: Nome interno do template (ex: "tres-cartas").
        display_name: Nome para exibição (ex: "Três Cartas").
        description: Descrição curta da tiragem.
        positions: Lista de SpreadPosition que definem o layout.
    """

    name: str
    display_name: str
    description: str
    positions: list[SpreadPosition]


# ----------------------------------------------------------------------
# Templates predefinidos
# ----------------------------------------------------------------------


def _build_tres_cartas() -> SpreadTemplate:
    """Constroi o template 'tres-cartas' (passado, presente, futuro)."""
    return SpreadTemplate(
        name="tres-cartas",
        display_name="Três Cartas",
        description="Tiragem simples que revela passado, presente e futuro.",
        positions=[
            SpreadPosition(
                position=1,
                context="passado",
                description="Situação ou evento que influenciou o momento atual",
            ),
            SpreadPosition(
                position=2,
                context="presente",
                description="Desafio ou oportunidade no momento atual",
            ),
            SpreadPosition(
                position=3,
                context="futuro",
                description="Possível desdobramento ou caminho recomendado",
            ),
        ],
    )


def _build_cruz_celtas() -> SpreadTemplate:
    """Constroi o template 'cruz-celtas' (Celtic Cross simplificado)."""
    return SpreadTemplate(
        name="cruz-celtas",
        display_name="Cruz Celta",
        description="Tiragem clássica em formato de cruz para análise profunda.",
        positions=[
            SpreadPosition(
                position=1,
                context="presente",
                description="Situação atual ou tema central",
            ),
            SpreadPosition(
                position=2,
                context="desafio",
                description="Obstáculo ou desafio imediato",
            ),
            SpreadPosition(
                position=3,
                context="base",
                description="Fundação ou raiz da questão",
            ),
            SpreadPosition(
                position=4,
                context="passado",
                description="Influição do passado",
            ),
            SpreadPosition(
                position=5,
                context="possivel",
                description="Possível futuro sem intervenção",
            ),
            SpreadPosition(
                position=6,
                context="futuro",
                description="Futuro próximo ou caminho provável",
            ),
            SpreadPosition(
                position=7,
                context="voz-interna",
                description="Conselho interior ou perspectiva sua",
            ),
            SpreadPosition(
                position=8,
                context="ambiente",
                description="Circunstâncias externas ou influência do ambiente",
            ),
            SpreadPosition(
                position=9,
                context="esperanca",
                description="Esperanças, medos ou desejos ocultos",
            ),
            SpreadPosition(
                position=10,
                context="resultado",
                description="Resultado final ou desfecho provável",
            ),
        ],
    )


def _buildFerradura() -> SpreadTemplate:
    """Constroi o template 'ferradura' (Horseshoe - 7 posições em arco)."""
    return SpreadTemplate(
        name="ferradura",
        display_name="Ferradura",
        description="Tiragem em arco com 7 posições para visão ampla.",
        positions=[
            SpreadPosition(
                position=1,
                context="presente",
                description="O tema ou situação atual",
            ),
            SpreadPosition(
                position=2,
                context="passado",
                description="Causa raiz ou origem",
            ),
            SpreadPosition(
                position=3,
                context="passado-recente",
                description="Eventos recentes que influenciam",
            ),
            SpreadPosition(
                position=4,
                context="presente",
                description="O desafio central",
            ),
            SpreadPosition(
                position=5,
                context="futuro-proximo",
                description="O que está se desenvolvendo",
            ),
            SpreadPosition(
                position=6,
                context="futuro",
                description="Inclusão ou caminho alternativo",
            ),
            SpreadPosition(
                position=7,
                context="resultado",
                description="Resultado final ou síntese",
            ),
        ],
    )


def _build_cinco_cartas() -> SpreadTemplate:
    """Constroi o template 'cinco-cartas' (decisão ou escolha)."""
    return SpreadTemplate(
        name="cinco-cartas",
        display_name="Cinco Cartas",
        description="Tiragem para analisar decisões ou escolhas.",
        positions=[
            SpreadPosition(
                position=1,
                context="situacao",
                description="A situação atual",
            ),
            SpreadPosition(
                position=2,
                context="opcao-a",
                description="Opção ou caminho A",
            ),
            SpreadPosition(
                position=3,
                context="opcao-b",
                description="Opção ou caminho B",
            ),
            SpreadPosition(
                position=4,
                context="fator-escondido",
                description="Fator oculto ou desconhecido",
            ),
            SpreadPosition(
                position=5,
                context="resultado",
                description="Resultado provável",
            ),
        ],
    )


def _build_uma_carta() -> SpreadTemplate:
    """Constroi o template 'uma-carta' (resposta rápida)."""
    return SpreadTemplate(
        name="uma-carta",
        display_name="Uma Carta",
        description="Tiragem simples para uma questão direta.",
        positions=[
            SpreadPosition(
                position=1,
                context="resposta",
                description="Resposta ou orientação única",
            ),
        ],
    )


def _build_relacionamento() -> SpreadTemplate:
    """Constroi o template 'relacionamento' (análise de relações)."""
    return SpreadTemplate(
        name="relacionamento",
        display_name="Relacionamento",
        description="Tiragem específica para questões de relação interpessoal.",
        positions=[
            SpreadPosition(
                position=1,
                context="voce",
                description="Sua perspectiva ou papel",
            ),
            SpreadPosition(
                position=2,
                context="ele-ela",
                description="Perspectiva ou energia da outra pessoa",
            ),
            SpreadPosition(
                position=3,
                context="relacao",
                description="A relação em si ou o que existe entre vocês",
            ),
            SpreadPosition(
                position=4,
                context="passado",
                description="O que foi ou a história",
            ),
            SpreadPosition(
                position=5,
                context="futuro",
                description="Possível desdobramento da relação",
            ),
        ],
    )


# ----------------------------------------------------------------------
# Catálogo de templates
# ----------------------------------------------------------------------


def _build_all_templates() -> dict[str, SpreadTemplate]:
    """Constrói o dicionário com todos os templates disponíveis."""
    return {
        "tres-cartas": _build_tres_cartas(),
        "cruz-celtas": _build_cruz_celtas(),
        "ferradura": _buildFerradura(),
        "cinco-cartas": _build_cinco_cartas(),
        "uma-carta": _build_uma_carta(),
        "relacionamento": _build_relacionamento(),
    }


TEMPLATES: dict[str, SpreadTemplate] = _build_all_templates()


def get_template(name: str) -> Optional[SpreadTemplate]:
    """Recupera um template pelo seu nome.

    Args:
        name: Nome interno do template (ex: "tres-cartas").

    Returns:
        SpreadTemplate correspondente ou None se não existir.
    """
    return TEMPLATES.get(name)


def list_templates() -> list[str]:
    """Lista todos os nomes de templates disponíveis.

    Returns:
        Lista de nomes internos dos templates.
    """
    return list(TEMPLATES.keys())
