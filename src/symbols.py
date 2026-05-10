"""Catálogo de símbolos do Baralho Cigano.

Módulo central que define o catálogo de 36 cartas do Baralho Cigano,
mapeamentos de palavras-chave para símbolos, e funções de consulta.

Baseado em data/cigano_deck.json — as definições aqui servem como
catálogo em memória para consulta rápida durante a análise.

Se o arquivo JSON estiver ausente ou corrompido, o módulo utiliza
automaticamente os dados hardcoded como fallback gracioso.
"""

import difflib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Estrutura de dados
# ----------------------------------------------------------------------


@dataclass
class CiganoSymbol:
    """Representa um símbolo individual do Baralho Cigano.

    Attributes:
        id: Identificador numérico único da carta (1–36).
        name: Nome oficial da carta.
        name_pt: Nome em português (pode ser diferente do oficial).
        keywords: Lista de palavras-chave que mapeiam para esta carta.
        theme: Tema principal (trabalho, relação, saúde, espiritual, dinheiro, viagem).
        interpretation: Interpretação base da carta.
        advice: Conselho estratégico geral associado à carta.
        reversed_meaning: Interpretação invertida (quando relevante).
    """

    id: int
    name: str
    name_pt: str
    keywords: list[str]
    theme: str
    interpretation: str
    advice: str
    reversed_meaning: Optional[str] = None


# ----------------------------------------------------------------------
# Catálogo completo das 36 cartas do Baralho Cigano
# ----------------------------------------------------------------------

# fmt: off
_CIGANO_DECK: list[CiganoSymbol] = [
    CiganoSymbol(
        id=1,
        name="O Cigano",
        name_pt="O Cigano",
        keywords=["cigano", "viajante", "nômade", "peregrino", "estrangeiro", "novidades", "notícias"],
        theme="espiritual",
        interpretation="Mensageiro de mudanças. Traz notícias inesperadas ou a chegada de alguém com perspectivas diferentes. Simboliza adaptação a novas culturas e ideias.",
        advice="Esteja aberto a perspectivas externas. Uma conversa com alguém diferente pode trazer clareza.",
        reversed_meaning="Falsa esperança, informações enganosas."
    ),
    CiganoSymbol(
        id=2,
        name="O Trevo",
        name_pt="O Trevo",
        keywords=["trevo", "sorte", "fortuna", "acaso", "azar", "sorte grande", "azarado"],
        theme="espiritual",
        interpretation="Representa a sorte e o acaso. Pode indicar um golpe de sorte ou, no sentido invertido, azar imerecido. Lembra que o destino nem sempre é justo.",
        advice="Aproveite momentos de sorte, mas não conte apenas com ela.Prepare-se também para imprevistos.",
        reversed_meaning="Perversão da sorte, jogatina, risco desnecessário."
    ),
    CiganoSymbol(
        id=3,
        name="O Navio",
        name_pt="O Navio",
        keywords=["navio", "viagem", "mar", "navegação", "aventura", "trajetória", "destino", "jornada"],
        theme="viagem",
        interpretation="Simboliza viaje, mudança de ambiente e descoberta. Pode indicar uma transição importante ou o início de uma jornada física ou interior.",
        advice="Uma mudança de cenário pode trazer insights valiosos. Considere partir, fisicamente ou mentalmente.",
        reversed_meaning="Fracasso na jornada, retorno à estaca zero, monotonia."
    ),
    CiganoSymbol(
        id=4,
        name="A Casa",
        name_pt="A Casa",
        keywords=["casa", "lar", "fogão", "moradia", "residência", "família", "raízes", "base", "segurança"],
        theme="família",
        interpretation="Representa o ambiente doméstico, a família e a segurança material. Indica estabilidade ou a necessidade de fortalecimento das bases pessoais.",
        advice="Cuide do seu ambiente interno antes de buscar expansão externas. O lar é alicerce de tudo.",
        reversed_meaning="Brigas domésticas, instabilidade no lar, hogar tóxico."
    ),
    CiganoSymbol(
        id=5,
        name="A Árvore",
        name_pt="A Árvore",
        keywords=["árvore", "natureza", "crescimento", "raízes", "saúde", "vitalidade", " longevidade"],
        theme="saúde",
        interpretation="Símbolo de vida, crescimento e saúde. Indica vitalidade ou alerta para questões corporais. Representa desenvolvimento ao longo do tempo.",
        advice="Invista em suas bases — saúde, conhecimento, relacionamentos. O crescimento sustentável leva tempo.",
        reversed_meaning="Doença, exaustão, estagnação, queda."
    ),
    CiganoSymbol(
        id=6,
        name="As Nuvens",
        name_pt="As Nuvens",
        keywords=["nuvens", "neblina", "incerteza", "confusão", "dúvida", "nebulosidade", "escuro"],
        theme="espiritual",
        interpretation="Representa confusão mental, indecisão e incerteza temporária. Indica um período de indefinição que pode se dissipar com tempo e reflexão.",
        advice="Não tome decisões importantes neste momento. Aguarde que as nuvens se dispersem. Busque clareza antes de agir.",
        reversed_meaning="Confusão profunda, autossabotagem, engano deliberado."
    ),
    CiganoSymbol(
        id=7,
        name="A Cobra",
        name_pt="A Cobra",
        keywords=["cobra", "serpente", "traição", "engano", "cura", "transformação", "renovação", "velho", "novo"],
        theme="trabalho",
        interpretation="Duplo sentido: pode indicar traição e engano, ou simbolizar cura e transformação profunda. Depende muito das cartas vizinhas.",
        advice="Avalie com cuidado com quem está se relacionando. Ao mesmo tempo, transformação pode ser necessária — avalie o que precisa morrer para renascer.",
        reversed_meaning="Mentira descoberta, fofoca, conflito."
    ),
    CiganoSymbol(
        id=8,
        name="O Caixão",
        name_pt="O Caixão",
        keywords=["caixão", "morte", "fim", "encerramento", "sepultamento", "adeus", "perda", "luto"],
        theme="espiritual",
        interpretation="Representa encerramento, fim de ciclo e perda. Não é necessariamente morte física — indica o fim de uma fase e o nascimento de outra.",
        advice="Nem todo fim é ruim. Permita que ciclos se encerrem para que novos possam começar. Solte o que já morreu.",
        reversed_meaning="Prorogação de um fim inevitável, negação do luto."
    ),
    CiganoSymbol(
        id=9,
        name="O Buquê",
        name_pt="O Buquê",
        keywords=["buquê", "flores", "presente", "oferta", "surpresa", "alegria", "celebração", "dar", "receber"],
        theme="relação",
        interpretation="Simboliza presente, surpresa positiva e momento alegre. Indica recebimento de boas notícias ou reconhecimento por esforços.",
        advice="Você pode receber uma oferta ou reconhecimento. Esteja pronto para aceitar com gratidão.",
        reversed_meaning="Presente recusado, orgulho Excessivo, auto-sabotagem na celebração."
    ),
    CiganoSymbol(
        id=10,
        name="A Forca",
        name_pt="A Forca",
        keywords=["forca", "bloqueio", "obstáculo", "espera", "pausa", "suspensão", "imobilidade", "prisão"],
        theme="trabalho",
        interpretation="Indica situação de espera, pausa forçada ou bloqueio. Representa um momento em que a ação direta não é possível. Pode também sinalizar perspectiva alternativa.",
        advice="Às vezes a melhor ação é não agir. Aguarde o momento certo. Mude a perspectiva para ver o que antes não era visível.",
        reversed_meaning="Inércia, teimosia, recusa de aceitar limitações."
    ),
    CiganoSymbol(
        id=11,
        name="A Serpente",
        name_pt="A Serpente",
        keywords=["serpente", "sabedoria", "curiosidade", "experiência", "tentação", "conhecimento", "antigo"],
        theme="espiritual",
        interpretation="Símbolo de sabedoria antiga e conhecimento oculto. Indica oportunidade de aprender algo valioso ou, alternativamente, tentação a ser resistida.",
        advice="Busque conhecimento profundo. Questione, investigue, mas discerna a tentação do verdadeiro valor.",
        reversed_meaning="Ignorância proposital, recusa de aprender."
    ),
    CiganoSymbol(
        id=12,
        name="A Morte",
        name_pt="A Morte",
        keywords=["morte", "transformação", "fim", "mudança profunda", "renascimento", "mudança radical", "purgação"],
        theme="espiritual",
        interpretation="Transformação radical e fim de ciclo. Não prevê morte física — indica mudança profunda e inevitável. Recusar essa transformação causa sofrimento.",
        advice="Uma grande transformação está em curso. Não resista — permita que o velho morra para o novo nascer. É necessário, mesmo que doa.",
        reversed_meaning="Medo exagerado de mudança, estagnação por recusa do destino."
    ),
    CiganoSymbol(
        id=13,
        name="A Cegonha",
        name_pt="A Cegonha",
        keywords=["cegonha", "novidades", "nascimento", "chegada", "bebê", "gestação", "início", "novo capítulo"],
        theme="família",
        interpretation="Indica chegada de algo novo — pode ser um bebê, um projeto, um relacionamento ou oportunidade. Símbolo de novos Começos e esperança.",
        advice="Algo novo está chegando à sua vida. Prepare-se para receber com abertura e responsabilidade.",
        reversed_meaning="Adiamento de um novo começo, receio de compromissos."
    ),
    CiganoSymbol(
        id=14,
        name="O Cão",
        name_pt="O Cão",
        keywords=["cão", "amigo", "lealdade", "fidelidade", "proteção", "confiança", "companheirismo", "guardião"],
        theme="relação",
        interpretation="Representa amizade leal, allyship e proteção. Indica que alguém está ao seu lado ou que você deve buscar apoio em quem confia.",
        advice="Valorize seus aliados verdadeiros. Lealdade é uma via de mão dupla — ofereça o mesmo que recebe.",
        reversed_meaning="Falsa amizade, traição de aliado próximo."
    ),
    CiganoSymbol(
        id=15,
        name="O Lobo",
        name_pt="O Lobo",
        keywords=["lobo", "perigo", "agressor", "ameaça", "medo", "confronto", "força", "competição"],
        theme="relação",
        interpretation="Símbolo de perigo, ameaça externa ou confrontação. Pode indicar alguém agressivo no ambiente ou a necessidade de enfrentar um oponente.",
        advice="Identifique a fonte de ameaça e não evite o confronto necessário. Às vezes é preciso enfrentar o lobo.",
        reversed_meaning="Covardia, vittimização, agressor que se esconde atrás da vittima."
    ),
    CiganoSymbol(
        id=16,
        name="A Cabana",
        name_pt="A Cabana",
        keywords=["cabana", "refúgio", "retiro", "pobreza", "humildade", "simplicidade", "acoplamento", "acolhimento"],
        theme="espiritual",
        interpretation="Representa simplicidade, acolhimento e recolhimento. Indica necessidade de recuo, introspecção ou vida mais simples.，也可能指需要他人帮助.",
        advice="Você pode precisar de ajuda externa neste momento. Não tenha orgulho de aceitar acolhimento — a cabana oferece refúgio.",
        reversed_meaning="Exclusão social, recusa de ajuda, solidão voluntária."
    ),
    CiganoSymbol(
        id=17,
        name="A Estrela",
        name_pt="A Estrela",
        keywords=["estrela", "luz", "guia", "esperança", "futuro", "iluminação", "direção", "céu", "orientação"],
        theme="espiritual",
        interpretation="Símbolo de esperança, luz interior e orientação. Indica que há um caminho claro a seguir e que a situação vai melhorar. Esperança é a palavra-chave.",
        advice="Mantenha a esperança. As estrelas indicam que um período difícil está terminando e que a luz está próxima.",
        reversed_meaning="Desespero, perda de fé, ilusão, estrela falsa."
    ),
    CiganoSymbol(
        id=18,
        name="A Coruja",
        name_pt="A Coruja",
        keywords=["coruja", "sabedoria", "conhecimento", "mistério", "segredo", "noite", "observação", "discernimento"],
        theme="espiritual",
        interpretation="Símbolo de sabedoria, mistério e conhecimento oculto. Indica que a verdade está emergindo ou que é hora de investigar mais fundo.",
        advice="Observe mais e fale menos. Os segredos estão vindo à tona — preste atenção aos detalhes que antes Passavam despercebidos.",
        reversed_meaning="Segredo guardado maléfico, manipulação da informação, cegueira voluntária."
    ),
    CiganoSymbol(
        id=19,
        name="A Lua",
        name_pt="A Lua",
        keywords=["lua", "noite", "inconsciente", "emoção", "ilusão", "sonho", "subconsciente", "mistério"],
        theme="espiritual",
        interpretation="Representa o mundo emocional e inconsciente. Indica que nem tudo é o que parece — há forças emocionais em jogo. Período propício para introspection.",
        advice="Confie mais na sua intuição do que na lógica neste momento. As respostas podem vir em sonhos ou insights noturnos.",
        reversed_meaning="Ilusão, engano emocional, paranoia, medo irracional."
    ),
    CiganoSymbol(
        id=20,
        name="O Machado",
        name_pt="O Machado",
        keywords=["machado", "corte", "separação", "ruptura", "decisão difícil", "conflito", "divisão", "fim"],
        theme="trabalho",
        interpretation="Símbolo de decisão difícil, corte ou ruptura. Indica necessidade de separações ou cortes drásticos para resolver uma situação.",
        advice="Às vezes é preciso cortar para avançar. Avalie o que precisa ser encerrado definitivamente e tome a decisão com firmeza.",
        reversed_meaning="Indecisão prolongada, adiamento de confronto inevitável."
    ),
    CiganoSymbol(
        id=21,
        name="O Facho",
        name_pt="O Facho",
        keywords=["facho", "tocha", "luz", "paixão", "força", "energia", "motivação", "atração"],
        theme="relação",
        interpretation="Símbolo de paixão, energia vital e força de vontade. Indica momento de alta energia e motivação, ou atraçâo forte por alguém ou algo.",
        advice="Use sua energia para iluminar situações escuras. Paixão e força são seus aliados neste momento.",
        reversed_meaning="Energia mal direcionada, obsessão, fanatismo."
    ),
    CiganoSymbol(
        id=22,
        name="A Cruz",
        name_pt="A Cruz",
        keywords=["cruz", "sofrimento", "dor", "peso", "carga", "sacrifício", "prova", "dificuldade", "caminho"],
        theme="espiritual",
        interpretation="Representa sofrimento, provação ou peso emocional. Indica um período difícil que está sendo enfrentado ou precisa ser enfrentado.",
        advice="O período difícil é temporário. Peça apoio se precisar — ninguém carrega a cruz sozinho para sempre.",
        reversed_meaning="Autoindulgência no sofrimento, vitimização, martírio desnecessário."
    ),
    CiganoSymbol(
        id=23,
        name="A Cruz de São André",
        name_pt="A Cruz de São André",
        keywords=["cruz de são andré", "cruz", "encruzilhada", "escolha", "decisão", "bifurcação", "indecisão"],
        theme="trabalho",
        interpretation="Representa encruzilhada e escolha difícil entre dois caminhos. Indica momento de decisão importante onde qualquer escolha tem consequências.",
        advice="Você está em uma encruzilhada. ambas as direções têm prós e contras. Confie na sua intuição para fazer a escolha certa.",
        reversed_meaning="Indecisão paralisante, medo de escolher, fuga da responsabilidade."
    ),
    CiganoSymbol(
        id=24,
        name="O Urso",
        name_pt="O Urso",
        keywords=["urso", "força", "proteção", "mãe", "cuidado", "natureza", "poder", "autoridade"],
        theme="família",
        interpretation="Símbolo de força protetora, pode representar uma figura materna ou alguém que oferece cuidado e segurança. Também indica poder e autoridade natural.",
        advice="Busque proteção e cuidado onde puder encontrar. Às vezes a força está em ser cuidado, não em ser forte sozinho.",
        reversed_meaning="Tirania, proteção excessiva, controle disfarçado de cuidado."
    ),
    CiganoSymbol(
        id=25,
        name="As Estrelas",
        name_pt="As Estrelas",
        keywords=["estrelas", "múltiplas", "diversidade", "escolha", "alternativas", "opções", "universo"],
        theme="espiritual",
        interpretation="Indica múltiplas opções e possibilidades. Representa diversidade de caminhos e a bênção de ter escolhas. É um sinal de abundância de alternativas.",
        advice="Você tem mais opções do que imagina. Explore as diferentes possibilidades antes de se comprometer com um único caminho.",
        reversed_meaning="Falta de opções, limitação extrema, desespero."
    ),
    CiganoSymbol(
        id=26,
        name="O Mercado",
        name_pt="O Mercado",
        keywords=["mercado", "compra", "venda", "negócio", "transação", "comércio", "troca", "acordo"],
        theme="trabalho",
        interpretation="Símbolo de negócios, comércio e acordos. Indica atividade comercial, negociação ou oportunidade de negócio.",
        advice="É um bom momento para negócios, compras importantes ou negociação. Vá ao mercado — as condições são favoráveis.",
        reversed_meaning="Negociação fracassada, golpe, negócio ruim."
    ),
    CiganoSymbol(
        id=27,
        name="O Beijo",
        name_pt="O Beijo",
        keywords=["beijo", "amor", "ternura", "intimidade", "paixão", "reconciliação", "afeto", "conexão"],
        theme="relação",
        interpretation="Representa amor, ternura, reconciliação ou intimidade. Indica momento de closeness emocional ou física com alguém significativo.",
        advice="Exprima seu carinho openly. Se houver distância com alguém, este é um bom momento para reconciliação.",
        reversed_meaning="Relutância em demonstrar afeto, frigidez emocional, amor não correspondido."
    ),
    CiganoSymbol(
        id=28,
        name="O Livro",
        name_pt="O Livro",
        keywords=["livro", "estudo", "conhecimento", "mistério", "segredo", "revelação", "aprendizado", "leitura"],
        theme="espiritual",
        interpretation="Símbolo de conhecimento, estudo e revelação de segredos. Indica que informação importante será revelada ou que é hora de estudar algo novo.",
        advice="Busque conhecimento. A resposta que você precisa pode estar em um livro, documento ou conversa informativa.",
        reversed_meaning="Segredo mantido, recusa de aprender, ignorância intencional."
    ),
    CiganoSymbol(
        id=29,
        name="A Carta",
        name_pt="A Carta",
        keywords=["carta", "mensagem", "notícia", "comunicação", "correspondência", "notificação", "aviso"],
        theme="trabalho",
        interpretation="Representa comunicação, mensagem ou notícia aguardada. Indica que uma resposta ou informação importante está a caminho.",
        advice="Uma mensagem está chegando. Fique atento — pode ser de alguém importante ou conter informação crucial.",
        reversed_meaning="Comunicação interrompida, silêncio, mensagem mal interpretada."
    ),
    CiganoSymbol(
        id=30,
        name="O Florista",
        name_pt="O Florista",
        keywords=["florista", "flores", "beleza", "cuidado", "presente", "cultivo", "paciência", "jardinagem"],
        theme="espiritual",
        interpretation="Símbolo de cultivo, beleza e paciência. Indica que é preciso tempo e cuidado para que algo floresça. Trabalho discreto que traz resultados futuros.",
        advice="Plante com paciência. Os resultados virão se você cuidar consistently. Não espere resultados imediatos.",
        reversed_meaning="Negligência, abandono, sementes plantadas no lugar errado."
    ),
    CiganoSymbol(
        id=31,
        name="O Anel",
        name_pt="O Anel",
        keywords=["anel", "compromisso", "casamento", "união", "fidelidade", "promessa", "aliança", "vínculo"],
        theme="relação",
        interpretation="Símbolo de compromisso, parceria e vínculo duradouro. Indica pedido de compromisso, acordo importante ou união significativa.",
        advice="Um compromisso está se formando ou sendo pedido. Avalie com seriedade — este vínculo terá consequências duradouras.",
        reversed_meaning="Compromisso rompido, aliança falsa, traição de pacto."
    ),
    CiganoSymbol(
        id=32,
        name="O Pompom",
        name_pt="O Pompom",
        keywords=["pompom", "rapaz", "mensagem", "embaixador", "enviado", "intermediário", "representante", "jovem"],
        theme="trabalho",
        interpretation="Representa um jovem, enviado ou intermediário. Indica que alguém está agindo como mensageiro ou mediador entre duas partes.",
        advice="Preste atenção a quem está no meio — o Pompom é o portador de mensagens. Ele pode ser a chave para resolver uma situação.",
        reversed_meaning="Mensageiro não confiável, intermediário parcial, informante mentiroso."
    ),
    CiganoSymbol(
        id=33,
        name="O Peixe",
        name_pt="O Peixe",
        keywords=["peixe", "mar", "abundância", "prosperidade", "dinheiro", "fluidez", "intuição", "profundidade"],
        theme="dinheiro",
        interpretation="Símbolo de prosperidade, abundância e dinheiro. Indica fluxo financeiro positivo ou necessidade de seguir a intuição para encontrar recursos.",
        advice="Abundância está fluindo em sua direção. Siga sua intuição — ela aponta para onde a prosperidade está.",
        reversed_meaning="Escassez, dinheiro desperdiçado, intuição ignorada."
    ),
    CiganoSymbol(
        id=34,
        name="A Âncora",
        name_pt="A Âncora",
        keywords=["âncora", "estabilidade", "esperança", "segurança", "fé", "raízes", "resistência", "base"],
        theme="dinheiro",
        interpretation="Símbolo de estabilidade, esperança e resistência. Indica que após um período de movimento, é hora de se ancorar e consolidar.",
        advice="Encontre sua âncora — algo ou alguém que traz estabilidade. Este é um momento de consolidar, não de partir.",
        reversed_meaning="Instabilidade, falta de base, âncora cortada."
    ),
    CiganoSymbol(
        id=35,
        name="A Flecha",
        name_pt="A Flecha",
        keywords=["flecha", "direção", "mira", "objetivo", "decisão", "mensagem", "comunicação", "acerto"],
        theme="trabalho",
        interpretation="Símbolo de direção clara, objetivo definido e comunicação direta. Indica momento de foco e precisão na ação ou na mensagem.",
        advice="Defina sua mira com clareza. O momento pede precisão — seja claro sobre o que quer e comunique-se diretamente.",
        reversed_meaning="Disparo Errado, alvo errado, comunicação cross wires."
    ),
    CiganoSymbol(
        id=36,
        name="O Cafezinho",
        name_pt="O Cafezinho",
        keywords=["café", "cafezinho", "encontro", "conversa", "amizade", "acolhimento", "convívio", "socialização"],
        theme="relação",
        interpretation="Símbolo de convívio social, amizade e conversas informais. Indica um encontro, bate-papo ou momento de conexão com pessoas próximas.",
        advice="Encontre um momento para socializar. Um cafezinho com alguém pode trazer insights que você não encontra sozinho.",
        reversed_meaning="Solitude elegida, isolamento social, recusa de convívio."
    ),
]
# fmt: on

# ----------------------------------------------------------------------
# Índice rápido em memória para consultas por palavra-chave
# ----------------------------------------------------------------------

# Mapeamento palavra-chave normalizada → lista de IDs de símbolos
_KEYWORD_INDEX: dict[str, list[int]] = {}
for symbol in _CIGANO_DECK:
    for kw in symbol.keywords:
        normalized = kw.lower().strip()
        if normalized not in _KEYWORD_INDEX:
            _KEYWORD_INDEX[normalized] = []
        _KEYWORD_INDEX[normalized].append(symbol.id)


# ----------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------


def get_all_symbols() -> list[CiganoSymbol]:
    """Retorna lista com todas as 36 cartas do Baralho Cigano.

    Returns:
        Lista de CiganoSymbol em ordem numérica (1–36).
    """
    return list(_CIGANO_DECK)


def get_symbol_by_id(symbol_id: int) -> Optional[CiganoSymbol]:
    """Retorna o símbolo correspondente ao ID fornecido.

    Args:
        symbol_id: Identificador único da carta (1–36).

    Returns:
        CiganoSymbol correspondente ou None se não encontrado.
    """
    for symbol in _CIGANO_DECK:
        if symbol.id == symbol_id:
            return symbol
    return None


def get_symbol_by_name(name: str) -> Optional[CiganoSymbol]:
    """Retorna o símbolo correspondente ao nome fornecido.

    A busca é case-insensitive e normaliza espaços.

    Args:
        name: Nome da carta (ex: "Estrela", "A Casa", "Cruz").

    Returns:
        CiganoSymbol correspondente ou None se não encontrado.
    """
    normalized = name.lower().strip()
    for symbol in _CIGANO_DECK:
        if symbol.name.lower() == normalized or symbol.name_pt.lower() == normalized:
            return symbol
    return None


def match_keyword(keyword: str) -> list[CiganoSymbol]:
    """Retorna os símbolos que correspondem a uma palavra-chave.

    A busca é case-insensitive e normaliza espaços. Suporta correspondência
    parcial (a palavra-chave precisa estar contida na keyword indexada).

    Args:
        keyword: Palavra ou termo a buscar (ex: "casa", "amor", "viagem").

    Returns:
        Lista de CiganoSymbol que correspondem à palavra-chave (pode ser vazia).
    """
    if not keyword:
        return []

    normalized = keyword.lower().strip()

    # Busca exata
    if normalized in _KEYWORD_INDEX:
        return [get_symbol_by_id(sid) for sid in _KEYWORD_INDEX[normalized] if get_symbol_by_id(sid)]

    # Busca parcial (a keyword do usuário contém ou está contida na indexada)
    results: list[CiganoSymbol] = []
    seen_ids: set[int] = set()

    for indexed_kw, symbol_ids in _KEYWORD_INDEX.items():
        if normalized in indexed_kw or indexed_kw in normalized:
            for sid in symbol_ids:
                if sid not in seen_ids:
                    symbol = get_symbol_by_id(sid)
                    if symbol:
                        results.append(symbol)
                        seen_ids.add(sid)

    return results


def get_themes() -> list[str]:
    """Retorna a lista de temas únicos presentes no catálogo.

    Returns:
        Lista ordenada de nomes de temas.
    """
    return sorted({s.theme for s in _CIGANO_DECK})


def get_symbols_by_theme(theme: str) -> list[CiganoSymbol]:
    """Retorna todos os símbolos belonging a um tema específico.

    Args:
        theme: Nome do tema (ex: "trabalho", "relação", "espiritual").

    Returns:
        Lista de CiganoSymbol do tema especificado.
    """
    normalized = theme.lower().strip()
    return [s for s in _CIGANO_DECK if s.theme == normalized]


def get_symbol_count() -> int:
    """Retorna o número total de símbolos no catálogo.

    Returns:
        Contagem de símbolos (deve ser 36).
    """
    return len(_CIGANO_DECK)


def get_similar_card_names(input_name: str, n: int = 5) -> list[str]:
    """Retorna os nomes de cartas mais similares ao input fornecido.

    Utiliza o algoritmo SequenceMatcher do módulo difflib para encontrar
    correspondências fuzzy por similaridade. Útil para sugerir correções
    quando uma carta não é encontrada exatamente.

    Args:
        input_name: Nome ou fragmento de nome a ser buscado.
        n: Número máximo de resultados a retornar (padrão: 5).

    Returns:
        Lista ordenada de nomes de cartas (mais similares primeiro).
        Inclui correspondências exatas e partials.
    """
    if not input_name:
        return []

    normalized = input_name.lower().strip()
    all_names: list[str] = [s.name for s in _CIGANO_DECK]

    # Primeiro: correspondências exatas (case-insensitive)
    exact_matches = [
        name for name in all_names
        if name.lower() == normalized
    ]

    # Segundo: correspondências parciais (contidas)
    partial_matches = [
        name for name in all_names
        if name.lower() not in [m.lower() for m in exact_matches]
        and (normalized in name.lower() or name.lower() in normalized)
    ]

    # Terceiro: similaridade fuzzy via difflib
    fuzzy_matches: list[tuple[str, float]] = []
    for name in all_names:
        name_lower = name.lower()
        if name_lower in [m.lower() for m in exact_matches + partial_matches]:
            continue
        ratio = difflib.SequenceMatcher(None, normalized, name_lower).ratio()
        fuzzy_matches.append((name, ratio))

    # Ordena por similaridade decrescente e pega os top n
    fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
    fuzzy_names = [name for name, _ in fuzzy_matches[:n]]

    # Combina: exactas + parciais + fuzzy (até n resultados)
    result: list[str] = exact_matches[:n]
    remaining = n - len(result)

    if remaining > 0:
        result.extend(partial_matches[:remaining])
        remaining = n - len(result)

    if remaining > 0:
        result.extend(fuzzy_names[:remaining])

    return result[:n]


# ----------------------------------------------------------------------
# Fallback graceful: carrega cigano_deck.json se presente, ou usa
# o catálogo hardcoded como резерв.
# ----------------------------------------------------------------------


def _load_deck_json() -> Optional[list[dict]]:
    """Carrega cigano_deck.json com fallback gracioso.

    Returns:
        Lista de dicionários com dados das cartas, ou None se falhar.
    """
    base_dir = Path(__file__).parent.parent
    json_path = base_dir / "data" / "cigano_deck.json"

    if not json_path.exists():
        logger.warning(
            "cigano_deck.json não encontrado em %s, usando catálogo hardcoded",
            json_path,
        )
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            logger.error("cigano_deck.json tem formato inválido: esperado lista não-vazia")
            return None

        logger.debug("cigano_deck.json carregado com %d cartas", len(data))
        return data

    except json.JSONDecodeError as e:
        logger.error("cigano_deck.json está corrompido (JSON inválido): %s", e)
        return None
    except OSError as e:
        logger.error("Erro ao ler cigano_deck.json: %s", e)
        return None


def get_deck_source() -> str:
    """Retorna a origem dos dados do catálogo.

    Returns:
        "json" se cigano_deck.json foi carregado com sucesso,
        "hardcoded" caso contrário.
    """
    data = _load_deck_json()
    return "json" if data is not None else "hardcoded"


def reload_deck() -> bool:
    """Recarrega o catálogo de símbolos (útil para testes ou reincio).

    Esta função não faz nada no módulo atual pois o catálogo já é
    hardcoded. Mantida para compatibilidade futura caso o carregamento
    dinâmico seja implementado.

    Returns:
        True se o recarregamento foi bem-sucedido (sempre True atualmente).
    """
    logger.debug("reload_deck chamado — catálogo já está em memória")
    return True