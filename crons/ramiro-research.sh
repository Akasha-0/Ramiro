#!/bin/bash
# ============================================
# RAMIRO RESEARCH AGENT
# Papel: Pesquisa de mercado e concorrentes
# ============================================
set -e

export GITHUB_TOKEN="$GITHUB_TOKEN"
REPO_DIR="/home/gabriel/comunidade-ia"
TODAY=$(date +%Y-%m-%d)

echo "🔍 RAMIRO RESEARCH AGENT - $(date)"
echo "========================================"

# Criar diretório de pesquisa
mkdir -p "$REPO_DIR/research/concorrentes" "$REPO_DIR/research/tendencias"

# Verificar se já pesquisou hoje
if [ -f "$REPO_DIR/research/concorrentes/${TODAY}.md" ]; then
    echo "✅ Pesquisa de hoje já existe, pulando."
    exit 0
fi

# Buscar issues abertas no GitHub
ISSUES=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/Akasha-0/Ramiro/issues?state=open&per_page=5")

# Criar relatório de pesquisa
cat > "$REPO_DIR/research/estado_atual.md" << EOF
# Estado Atual do Ramiro - $TODAY

## Issues Abertas
$(echo "$ISSUES" | python3 -c "
import sys, json
issues = json.load(sys.stdin)
for i in issues:
    print(f'- #{i[\"number\"]} | {i[\"title\"]}')
    if 'labels' in i and i['labels']:
        print(f'  Labels: {[l[\"name\"] for l in i[\"labels\"]]}')
")

## Branches Ativas
$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/Akasha-0/Ramiro/branches" | python3 -c "
import sys, json
branches = json.load(sys.stdin)
for b in branches:
    print(f'- {b[\"name\"]}')
")

## PRs Abertos
$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/Akasha-0/Ramiro/pulls?state=open&per_page=5" | python3 -c "
import sys, json
prs = json.load(sys.stdin)
for p in prs:
    print(f'- PR #{p[\"number\"]}: {p[\"title\"]} ({p[\"head\"][\"ref\"]})')
")

## Última Versão Conhecida
$(cd "$REPO_DIR" && git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")

---
*Gerado automaticamente pelo Research Agent - $TODAY*
EOF

echo "✅ Estado atual documentado: $REPO_DIR/research/estado_atual.md"
echo "🎯 Pesquisa concluída. Próximo: Planner Agent."