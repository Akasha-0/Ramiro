#!/bin/bash
# ============================================
# RAMIRO PLANNER AGENT
# Papel: Criar planos de implementação detalhados
# ============================================
set -e

export GITHUB_TOKEN="$GITHUB_TOKEN"
REPO_DIR="/home/gabriel/comunidade-ia"
TODAY=$(date +%Y-%m-%d)

echo "📋 RAMIRO PLANNER AGENT - $(date)"
echo "====================================="

mkdir -p "$REPO_DIR/plans"

# Verificar se existe estado atual (do research)
if [ ! -f "$REPO_DIR/research/estado_atual.md" ]; then
    echo "⚠️  Execute research primeiro!"
    exit 1
fi

# Verificar PRs abertos
PR_COUNT=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/Akasha-0/Ramiro/pulls?state=open" | \
    python3 -c "import sys,json; print(len(json.load(sys.stdin)))")

# Se há PRs abertos, não criar novo plano
if [ "$PR_COUNT" -gt 0 ]; then
    echo "📦 Já existe $PR_COUNT PR(s) aberto(s). Aguardando QA."
    exit 0
fi

# Buscar próxima versão
cd "$REPO_DIR"
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
# Extrair patch number e incrementar
PATCH_NUM=$(echo "$CURRENT_VERSION" | sed 's/v0\.0\.//')
NEXT_PATCH=$((PATCH_NUM + 1))
NEXT_VERSION="v0.0.$NEXT_PATCH"

# Analisar estado do projeto
echo "📊 Analisando estado do projeto..."

# Criar plano de implementação
cat > "$REPO_DIR/plans/PLAN-$NEXT_VERSION.md" << EOF
# Plano de Implementação - $NEXT_VERSION

## Versão: $NEXT_VERSION
**Data**: $TODAY
**Status**: 🟡 Pronto para Implementação

---

## Objetivo do Projeto (Contexto)

**Ramiro**: CLI em Python para análise de Baralho Cigano e símbolos esotéricos.
Pipeline: Input → Processing → Boundaries → Output (Markdown)

**Stack**: Python, types.py (dataclasses), argparse, pytest

---

## Análise de Estado Atual

\`\`\`
$(cat $REPO_DIR/research/estado_atual.md 2>/dev/null | head -30 || echo "Estado não disponível")
\`\`\`

---

## Feature Planejada: Melhorias Iterativas

### Prioridades para $NEXT_VERSION:

1. **Documentação**: Melhorar README e CLAUDE.md
2. **Testes**: Aumentar cobertura de testes
3. **UX**: Melhorar mensagens de erro
4. **Performance**: Otimizar parsing

---

## Tarefas Atômicas (1 por vez)

### Tarefa 1: Incrementar Documentação
- **Arquivo**: docs/
- **Teste**: verifica_leitura.py
- **Branch**: auto-claude/$(printf "%03d" $NEXT_PATCH)-docs-improve

### Tarefa 2: Adicionar Testes
- **Arquivo**: tests/
- **Teste**: pytest passa
- **Branch**: auto-claude/$(printf "%03d" $NEXT_PATCH)-add-tests

### Tarefa 3: Melhorar CLI
- **Arquivo**: src/main.py
- **Teste**: python -m src.main --help
- **Branch**: auto-claude/$(printf "%03d" $NEXT_PATCH)-cli-improve

---

## Critérios de Aceitação

- [ ] Testes passam (pytest -v)
- [ ] CLI funciona (python -m src.main --help)
- [ ] Output em UTF-8 correto
- [ ] Sem dependências quebradas

---

## Próximo Agente: CODER

Quando este plano for aprovado, o Coder Agent deve:
1. Criar branch $NEXT_VERSION
2. Implementar tarefas listadas
3. Abrir PR para review

---
*Gerado pelo Planner Agent - $TODAY*
EOF

echo "✅ Plano criado: $REPO_DIR/plans/PLAN-$NEXT_VERSION.md"
echo "🎯 Versão $NEXT_VERSION pronta para implementação."