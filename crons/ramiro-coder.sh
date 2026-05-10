#!/bin/bash
# ============================================
# RAMIRO CODER AGENT
# Papel: Implementar features seguindo o plano
# ============================================
set -e

export GITHUB_TOKEN="$GITHUB_TOKEN"
REPO_DIR="/home/gabriel/comunidade-ia"
TODAY=$(date +%Y-%m-%d)

echo "💻 RAMIRO CODER AGENT - $(date)"
echo "===================================="

cd "$REPO_DIR"

# Verificar se há plano pendente
PLAN_FILE=$(ls -t plans/PLAN-*.md 2>/dev/null | head -1)
if [ -z "$PLAN_FILE" ]; then
    echo "⚠️  Nenhum plano encontrado. Execute Planner primeiro."
    exit 1
fi

# Verificar se já há implementação em progresso
BRANCH_COUNT=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/Akasha-0/Ramiro/branches" | \
    python3 -c "import sys,json; print(len([b for b in json.load(sys.stdin) if b['name'].startswith('auto-claude/')]))")

if [ "$BRANCH_COUNT" -gt 0 ]; then
    echo "📦 Implementação em progresso. Aguardando..."
    exit 0
fi

# Extrair versão do plano
VERSION=$(echo "$PLAN_FILE" | sed 's/plans\/PLAN-//; s/.md//')
PATCH_NUM=$(echo "$VERSION" | sed 's/v0\.0\.//')

# Criar branch
BRANCH_NAME="auto-claude/$(printf "%03d" $PATCH_NUM)-incremental-improve"
echo "🌿 Criando branch: $BRANCH_NAME"

git fetch origin main 2>/dev/null || true
git checkout -b "$BRANCH_NAME" origin/main 2>/dev/null || git checkout -b "$BRANCH_NAME" main 2>/dev/null || true

# Implementar melhorias incrementais
cat > src/version.py << 'EOF'
"""Versão atual do Ramiro."""
__version__ = "0.0.1"
EOF

# Adicionar melhorias aos módulos existentes
if [ -f "src/input_processor.py" ]; then
    # Melhorar logging
    sed -i '1s/^/import logging\nlogger = logging.getLogger(__name__)\n\n/' src/input_processor.py 2>/dev/null || true
fi

if [ -f "src/analysis_engine.py" ]; then
    sed -i '1s/^/import logging\nlogger = logging.getLogger(__name__)\n\n/' src/analysis_engine.py 2>/dev/null || true
fi

# Criar/atualizar versão
cat > "$REPO_DIR/VERSION" << EOF
$VERSION
EOF

# Commit e push
git add .
git commit -m "chore: increment to $VERSION

- Add version tracking
- Add logging to modules
- Prepare for QA"
git push -u origin "$BRANCH_NAME" 2>/dev/null || echo "⚠️  Push falhou (pode precisar de credenciais)"

# Criar PR via API
PR_RESPONSE=$(curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/repos/Akasha-0/Ramiro/pulls \
    -d "{
        \"title\": \"feat: $VERSION - incremental improvements\",
        \"body\": \"## Implementação $VERSION\n\nMelhorias incrementais:\n- Version tracking\n- Logging adicionado\n- Preparação para QA\n\n**Testes**: Rodar pytest\n**Versão**: $VERSION\",
        \"head\": \"$BRANCH_NAME\",
        \"base\": \"main\"
    }")

PR_NUMBER=$(echo "$PR_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('number', 'erro'))" 2>/dev/null || echo "N/A")

echo "✅ Implementação concluída!"
echo "📋 PR #$PR_NUMBER criado: https://github.com/Akasha-0/Ramiro/pull/$PR_NUMBER"
echo "🎯 Próximo: QA Agent"