"""Command-line interface for Clareza."""

import json
from pathlib import Path

import click


def get_cards_data() -> list[dict]:
    """Load cards data from the JSON file."""
    cards_path = Path(__file__).parent / "data" / "cards.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_portuguese_help(ctx: click.Context, formatter: click.HelpFormatter) -> None:
    """Format help output in Portuguese."""
    click.echo("Uso:")
    click.echo(f"  {ctx.command_path} [OPÇÕES] COMANDO [ARGUMENTOS]")
    click.echo()
    click.echo("Opções globais:")
    click.echo("  -h, --help  Mostrar esta mensagem de ajuda e sair")
    click.echo("  --version   Mostrar a versão do programa")


class PortugueseHelpGroup(click.Group):
    """Custom Click group with Portuguese help text."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Format help output in Portuguese."""
        format_portuguese_help(ctx, formatter)


@click.group(cls=PortugueseHelpGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="0.1.0", prog_name="clareza", message="%(prog)s %(version)s\n")
def cli() -> None:
    """Clareza - Ferramenta CLI para Baralho Cigano."""
    pass


@cli.command("list")
def list_command() -> None:
    """Listar todas as 36 cartas do Baralho Cigano."""
    cards = get_cards_data()
    for card in cards:
        click.echo(f"{card['id']:2d}. {card['name']} - {card['meaning']}")


@cli.command("analyze")
@click.argument("card_id", type=int)
def analyze_command(card_id: int) -> None:
    """Analisar uma carta específica do Baralho Cigano.

    Args:
        card_id: ID numérico da carta (1-36).
    """
    cards = get_cards_data()
    card = next((c for c in cards if c["id"] == card_id), None)
    if card is None:
        click.echo(f"Erro: Carta com ID {card_id} não encontrado.", err=True)
        click.echo("Use 'clareza list' para ver todas as cartas disponíveis.", err=True)
        raise SystemExit(1)
    click.echo(f"Carta #{card['id']}: {card['name']}")
    click.echo(f"Palavras-chave: {', '.join(card['keywords'])}")
    click.echo(f"Significado: {card['meaning']}")


if __name__ == "__main__":
    cli()
