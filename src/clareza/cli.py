"""Command-line interface for Clareza."""

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="clareza", message="%(prog)s %(version)s\n")
def cli() -> None:
    """Clareza - Ferramenta CLI para Baralho Cigano."""
    pass


if __name__ == "__main__":
    cli()
