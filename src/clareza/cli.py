"""Command-line interface for Clareza."""

import click


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Clareza - Ferramenta CLI para Baralho Cigano."""
    pass


if __name__ == "__main__":
    cli()
