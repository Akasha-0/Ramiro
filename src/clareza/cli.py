"""Command-line interface for Clareza."""

import click


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


if __name__ == "__main__":
    cli()
