"""Hook function signatures — Sistema de Clareza Simbólico-Estratégica.

Define os contratos de funções hook que plugins podem implementar
para estender a funcionalidade do sistema.

Hooks disponíveis:
- CardHook: procesa/reserva cartas do baralho
- AnalysisHook: procesa/adiciona regras de análise
- SectionHook: gera seções customizadas para o relatório
"""

from typing import Protocol, Optional, Any

from clareza.types import StructuredInput, AnalysisResult


class CardHook(Protocol):
    """Protocolo para hooks que processam cartas do baralho.

    Plugins que definem capability.type == "card_database"
    devem implementar uma função com esta assinatura.
    """

    def __call__(self, card_name: str, context: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Processa uma carta do baralho.

        Args:
            card_name: Nome da carta a processar.
            context: Contexto adicional opcional (ex: posição na tiragem).

        Returns:
            Dict com campos: name, interpretation, theme, etc.
            Retorna None se a carta não é reconhecida pelo plugin.
        """
        ...


class AnalysisHook(Protocol):
    """Protocolo para hooks que adicionam regras de análise.

    Plugins que definem capability.type == "analysis_rules"
    devem implementar uma função com esta assinatura.
    """

    def __call__(
        self,
        input_data: StructuredInput,
        current_result: AnalysisResult,
    ) -> AnalysisResult:
        """Executa regras de análise customizadas.

        Args:
            input_data: Input estruturado do usuário.
            current_result: Resultado atual da análise.

        Returns:
            AnalysisResult atualizado com novos insights, riscos ou decisões.
        """
        ...


class SectionHook(Protocol):
    """Protocolo para hooks que geram seções customizadas.

    Plugins que definem capability.type == "custom_section"
    devem implementar uma função com esta assinatura.
    """

    def __call__(
        self,
        analysis_result: AnalysisResult,
        config: Optional[dict[str, Any]] = None,
    ) -> str:
        """Gera uma seção customizada para o relatório.

        Args:
            analysis_result: Resultado da análise.
            config: Configurações opcionais definidas no capability.

        Returns:
            String com conteúdo Markdown da seção customizada.
        """
        ...
