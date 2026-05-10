"""Gerenciador de sessão interativa — Sistema de Clareza Simbólico-Estratégica.

Módulo que conduz o usuário através de uma leitura guiada por perguntas.
Cada passo da sessão coleta informações necessárias para construir
um StructuredInput válido.

Attributes:
    InteractiveSession: Classe principal que gerencia o fluxo de perguntas.
    SessionError: Exceção lançada quando ocorre erro durante a sessão.
    SessionAborted: Exceção lançada quando o usuário aborta a sessão.
"""

import logging
from typing import Optional, Protocol

from src.types import CardPosition, StructuredInput
from src.spread_templates import TEMPLATES, get_template, SpreadTemplate

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Exceções
# ----------------------------------------------------------------------


class SessionError(Exception):
    """Exceção lançada quando ocorre um erro durante a sessão interativa.

    Attributes:
        message: Descrição legível do erro.
        step: Nome do passo onde ocorreu o erro (opcional).
    """

    def __init__(
        self,
        message: str,
        step: Optional[str] = None,
    ) -> None:
        self.message = message
        self.step = step
        full = message
        if step:
            full = f"[{step}] {message}"
        super().__init__(full)


class SessionAborted(Exception):
    """Exceção lançada quando o usuário aborta a sessão interativa."""

    def __init__(self) -> None:
        super().__init__("Sessão interrompida pelo usuário")


# ----------------------------------------------------------------------
# Protocolo para input do usuário (permite injeção de dependência para testes)
# ----------------------------------------------------------------------


class InputProvider(Protocol):
    """Protocolo para provedores de input do usuário.

    Permite injetar diferentes mecanismos de input (CLI, testes, etc.)
    sem acoplar a lógica da sessão a uma implementação específica.
    """

    def prompt(self, message: str) -> str:
        """Exibe uma mensagem e retorna a entrada do usuário.

        Args:
            message: Mensagem a ser exibida ao usuário.

        Returns:
            Entrada do usuário como string.
        """
        ...


class CLInputProvider:
    """Provedor de input via linha de comando.

    Implementação padrão que usa input() nativo.
    """

    def prompt(self, message: str) -> str:
        """Exibe mensagem e lê entrada do terminal.

        Args:
            message: Mensagem a ser exibida.

        Returns:
            Entrada do usuário.
        """
        return input(message)

    def confirm(self, message: str) -> bool:
        """Solicita confirmação do usuário.

        Args:
            message: Mensagem de confirmação.

        Returns:
            True se o usuário confirmou, False caso contrário.
        """
        response = input(f"{message} (s/n): ").strip().lower()
        return response in ("s", "sim", "y", "yes")


# ----------------------------------------------------------------------
# Constantes de sessão
# ----------------------------------------------------------------------

ABORT_COMMANDS: set[str] = {"sair", "quit", "q", "exit", "cancelar", "c"}
HELP_COMMANDS: set[str] = {"ajuda", "help", "h", "?"}


# ----------------------------------------------------------------------
# Gerenciador de sessão
# ----------------------------------------------------------------------


class InteractiveSession:
    """Gerenciador de sessão interativa para leituras do Baralho Cigano.

    Conduz o usuário através de perguntas guiadas para coletar:
    1. A pergunta ou situação que deseja explorar
    2. O tipo de tiragem a ser utilizada
    3. As cartas sorteadas

    Ao final, constrói um StructuredInput válido para o pipeline de análise.

    Attributes:
        input_provider: Provedor de input (padrão: CLInputProvider).
        max_question_length: Comprimento máximo da pergunta (default 500).
    """

    def __init__(
        self,
        input_provider: Optional[InputProvider] = None,
        max_question_length: int = 500,
    ) -> None:
        self.input_provider = input_provider or CLInputProvider()
        self.max_question_length = max_question_length

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def run(self) -> StructuredInput:
        """Executa a sessão interativa completa.

        Retorna ao usuário ao início se preferir recomeçar.

        Returns:
            StructuredInput construído a partir das respostas收集.

        Raises:
            SessionAborted: Se o usuário interromper a sessão.
        """
        self._print_welcome()

        # Loop para permitir recomeçar
        while True:
            try:
                return self._run_session()
            except SessionAborted:
                raise
            except SessionError as e:
                logger.warning("Erro na sessão: %s", e.message)
                self._print_error(str(e))
                if not self._ask_restart():
                    raise SessionAborted()

    # ------------------------------------------------------------------
    # Passos da sessão
    # ------------------------------------------------------------------

    def _run_session(self) -> StructuredInput:
        """Executa os passos da sessão em sequência.

        Returns:
            StructuredInput construído.

        Raises:
            SessionAborted: Se o usuário interromper durante algum passo.
        """
        # Passo 1: Coletar pergunta
        question = self.collect_question()
        logger.debug("Questão coletada: %r", question[:50])

        # Passo 2: Selecionar tiragem
        spread = self.select_spread()
        logger.debug("Tiragem selecionada: %s", spread.name)

        # Passo 3: Coletar cartas
        cards = self.collect_cards(spread)
        logger.debug("Cartas coletadas: %d", len(cards))

        # Passo 4: Construir StructuredInput
        return self.build_structured_input(question, spread.name, [
            card.card_name for card in cards
        ])

    def collect_question(self) -> str:
        """Coleta a pergunta ou situação do usuário.

        Permite abortar digitando 'sair' ou 'quit'.

        Returns:
            A pergunta ou situação do usuário.

        Raises:
            SessionAborted: Se o usuário interromper.
        """
        self._print_step_header("Sua Pergunta")

        print(
            "Descreva a situação ou pergunta que deseja explorar.\n"
            " Pode ser algo como:\n"
            "   - 'Estou confuso sobre meu trabalho'\n"
            "   - 'O que devo fazer sobre meu relacionamento?'\n"
            "   - 'Como será meu futuro profissional?'\n"
        )

        while True:
            try:
                response = self.input_provider.prompt(">>> ")
            except (KeyboardInterrupt, EOFError):
                raise SessionAborted()

            # Verificar comandos de abort
            if self._is_abort_command(response):
                raise SessionAborted()

            # Verificar comandos de ajuda
            if self._is_help_command(response):
                self._print_help_question()
                continue

            # Validar resposta
            question = response.strip()
            if not question:
                self._print_error("Por favor, descreva sua situação ou pergunta.")
                continue

            if len(question) > self.max_question_length:
                self._print_error(
                    f"Sua pergunta é muito longa (máximo {self.max_question_length} caracteres). "
                    "Tente ser mais objetivo."
                )
                continue

            return question

    def select_spread(self) -> SpreadTemplate:
        """Coleta a seleção de tiragem do usuário.

        Exibe os templates disponíveis e permite seleção por número
        ou nome.

        Returns:
            SpreadTemplate selecionado.

        Raises:
            SessionAborted: Se o usuário interromper.
        """
        self._print_step_header("Escolha da Tiragem")

        # Listar templates disponíveis
        print("Tiragens disponíveis:\n")
        for i, (name, template) in enumerate(TEMPLATES.items(), start=1):
            print(f"  {i}. {template.display_name}")
            print(f"     {template.description}")
            print()

        print("Digite o número ou nome da tiragem desejada.")
        print("(Digite 'ajuda' para mais informações)\n")

        while True:
            try:
                response = self.input_provider.prompt(">>> ")
            except (KeyboardInterrupt, EOFError):
                raise SessionAborted()

            # Verificar comandos de abort
            if self._is_abort_command(response):
                raise SessionAborted()

            # Verificar comandos de ajuda
            if self._is_help_command(response):
                self._print_help_spread()
                continue

            # Tentar interpretar como seleção
            selection = response.strip()
            if not selection:
                self._print_error("Por favor, escolha uma tiragem.")
                continue

            # Tentar por número
            if selection.isdigit():
                index = int(selection) - 1
                template_names = list(TEMPLATES.keys())
                if 0 <= index < len(template_names):
                    return TEMPLATES[template_names[index]]

            # Tentar por nome
            template = get_template(selection.lower())
            if template is not None:
                return template

            # Tentar correspondência parcial
            matches = [
                (name, t) for name, t in TEMPLATES.items()
                if selection.lower() in name.lower()
                or selection.lower() in t.display_name.lower()
            ]
            if len(matches) == 1:
                return matches[0][1]
            elif len(matches) > 1:
                self._print_error(
                    f"Múltiplas tiragens encontradas: {', '.join(t.display_name for _, t in matches)}. "
                    "Seja mais específico."
                )
                continue

            self._print_error(
                f"Tiragem '{selection}' não encontrada. "
                f"Tente um número de 1 a {len(TEMPLATES)} ou o nome da tiragem."
            )

    def collect_cards(self, spread: SpreadTemplate) -> list[CardPosition]:
        """Coleta as cartas sorteadas para a tiragem.

        Percorre cada posição da tiragem solicitando o nome da carta.

        Args:
            spread: Template da tiragem selecionada.

        Returns:
            Lista de CardPosition com as cartas sorteadas.

        Raises:
            SessionAborted: Se o usuário interromper.
        """
        self._print_step_header(f"Cartas - {spread.display_name}")

        print(f"Você utilizará a tiragem '{spread.display_name}'.")
        print(f"Serão {len(spread.positions)} cartas.\n")

        cards: list[CardPosition] = []

        for position in spread.positions:
            print(f"[Posição {position.position}] {position.context}")
            print(f"  {position.description}\n")

            while True:
                try:
                    response = self.input_provider.prompt(f"  Carta {position.position}: ")
                except (KeyboardInterrupt, EOFError):
                    raise SessionAborted()

                # Verificar comandos
                if self._is_abort_command(response):
                    raise SessionAborted()

                if self._is_help_command(response):
                    self._print_help_card(position)
                    continue

                card_name = response.strip()
                if not card_name:
                    self._print_error("Por favor, informe o nome da carta.")
                    continue

                cards.append(
                    CardPosition(
                        position=position.position,
                        card_name=card_name,
                        position_context=position.context,
                    )
                )
                break

        return cards

    # ------------------------------------------------------------------
    # Construção do StructuredInput
    # ------------------------------------------------------------------

    def build_structured_input(
        self,
        question: str,
        spread_name: str,
        card_names: list[str],
    ) -> StructuredInput:
        """Constrói um StructuredInput a partir dos dados coletados.

        Args:
            question: A pergunta ou situação do usuário.
            spread_name: Nome do template de tiragem utilizado.
            card_names: Lista de nomes das cartas sorteadas.

        Returns:
            StructuredInput pronto para o pipeline de análise.
        """
        template = get_template(spread_name)
        if template is None:
            raise SessionError(
                f"Template '{spread_name}' não encontrado",
                step="build_input",
            )

        cards: list[CardPosition] = [
            CardPosition(
                position=i + 1,
                card_name=name,
                position_context=template.positions[i].context if i < len(template.positions) else None,
            )
            for i, name in enumerate(card_names)
        ]

        return StructuredInput(
            format="spread",
            raw_content=question,
            cards=cards,
            keywords=None,
        )

    # ------------------------------------------------------------------
    # Utilitários de comando
    # ------------------------------------------------------------------

    def _is_abort_command(self, response: str) -> bool:
        """Verifica se a resposta é um comando de abort.

        Args:
            response: Resposta do usuário.

        Returns:
            True se for comando de abort.
        """
        return response.strip().lower() in ABORT_COMMANDS

    def _is_help_command(self, response: str) -> bool:
        """Verifica se a resposta é um comando de ajuda.

        Args:
            response: Resposta do usuário.

        Returns:
            True se for comando de ajuda.
        """
        return response.strip().lower() in HELP_COMMANDS

    def _ask_restart(self) -> bool:
        """Pergunta se o usuário deseja recomeçar.

        Returns:
            True se o usuário quiser recomeçar.
        """
        try:
            return self.input_provider.confirm("Deseja recomeçar a sessão?")
        except (KeyboardInterrupt, EOFError):
            return False

    # ------------------------------------------------------------------
    # Mensagens formatadas
    # ------------------------------------------------------------------

    def _print_welcome(self) -> None:
        """Exibe mensagem de boas-vindas."""
        print("\n" + "=" * 60)
        print("       Clareza — Modo Interativo de Leitura")
        print("=" * 60)
        print()
        print("Vou guiá-lo(a) através de uma leitura do Baralho Cigano.")
        print("A qualquer momento, digite 'sair' para interromper.")
        print()

    def _print_step_header(self, title: str) -> None:
        """Exibe cabeçalho de passo.

        Args:
            title: Título do passo.
        """
        print("\n" + "-" * 40)
        print(f"  {title}")
        print("-" * 40)

    def _print_error(self, message: str) -> None:
        """Exibe mensagem de erro formatada.

        Args:
            message: Mensagem de erro.
        """
        print(f"\n⚠️  {message}\n")

    def _print_help_question(self) -> None:
        """Exibe ajuda sobre como formular a pergunta."""
        print(
            "\n📝 Dicas para sua pergunta:\n"
            "   - Seja específico sobre a situação que te preocupa\n"
            "   - Mencione áreas importantes: trabalho, amor, saúde, família\n"
            "   - Pergunte sobre o que você gostaria de entender melhor\n"
            "   - Não há resposta certa ou errada — confie sua intuição\n"
        )

    def _print_help_spread(self) -> None:
        """Exibe ajuda sobre as tiragens disponíveis."""
        print("\n📋 Tipos de Tiragem:\n")
        for name, template in TEMPLATES.items():
            print(f"   {template.display_name}: {template.description}")
            print(f"     Exemplo de uso: {template.positions[0].description}")
            print()

    def _print_help_card(self, position: SpreadPosition) -> None:
        """Exibe ajuda sobre como informar a carta.

        Args:
            position: Posição atual da tiragem.
        """
        print(
            f"\n📇 Dica: Para a posição '{position.context}':\n"
            f"   {position.description}\n"
            "   Informe o nome da carta que você sorteou\n"
            "   (ex: 'Cruz', 'Estrela', 'Café', 'Casa', 'Mar')\n"
        )