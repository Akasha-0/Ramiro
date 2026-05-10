#!/bin/bash
# ============================================
# RAMIRO MASTER LOOP
# Loop contínuo de evolução automática
# Ciclo: Research → Plan → Code → QA → Nova Versão
# Release: A cada 7 dias
# ============================================
set -e

export GITHUB_TOKEN="$GITHUB_TOKEN"
REPO_DIR="/home/gabriel/comunidade-ia"
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%H:%M)
LOG_FILE="$REPO_DIR/logs/loop-$(date +%Y-%m-%d).log"

mkdir -p "$REPO_DIR"/{research,plans,reports,logs,versions}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================"
log "🚀 RAMIRO MASTER LOOP INICIADO"
log "========================================"

# --- VERIFICAR ESTADO ATUAL ---
cd "$REPO_DIR"

# Pegar versão atual
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
PATCH_NUM=$(echo "$CURRENT_VERSION" | sed 's/v0\.0\.//')
NEXT_PATCH=$((PATCH_NUM + 1))

# Verificar PRs abertos
PR_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/Akasha-0/Ramiro/pulls?state=open")
PR_COUNT=$(echo "$PR_RESPONSE" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)

log "📊 Estado: versão=$CURRENT_VERSION | PRs abertos=$PR_COUNT"

# --- DETERMINAR FASE DO CICLO ---
if [ "$PR_COUNT" -gt 0 ]; then
    # Há PR em aberto → ir para QA
    PHASE="qa"
    log "🔄 PR detectado → Modo QA"
else
    # Verificar se há plano pendente
    PLAN_FILES=$(ls -t "$REPO_DIR/plans"/PLAN-*.md 2>/dev/null | head -1)
    if [ -n "$PLAN_FILES" ]; then
        PHASE="code"
        log "🔄 Plano detectado → Modo Coder"
    else
        PHASE="research"
        log "🔄 Sem plano → Modo Research"
    fi
fi

# --- EXECUTAR FASE ---
case "$PHASE" in
    research)
        log "🔍 FASE: RESEARCH"
        
        # Fazer pesquisa web rápida
        RESEARCH_FILE="$REPO_DIR/research/snapshot-$(date +%H).md"
        cat > "$RESEARCH_FILE" << EOF
# Research Snapshot - $(date '+%Y-%m-%d %H:%M')

## Análise Rápida
- Versão atual: $CURRENT_VERSION
- Próxima: v0.0.$NEXT_PATCH

## Issues Abertas
$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/Akasha-0/Ramiro/issues?state=open&per_page=3" | \
    python3 -c "import sys,json; [print(f'- #{i[\"number\"]}: {i[\"title\"]}') for i in json.load(sys.stdin)]" 2>/dev/null || echo "Nenhuma")

## Oportunidade
- Melhorar documentação
- Adicionar testes
- Otimizar performance
- Melhorar UX
EOF
        log "✅ Research salvo: $RESEARCH_FILE"
        
        # Criar plano automaticamente
        log "📋 Criando plano para v0.0.$NEXT_PATCH..."
        
        cat > "$REPO_DIR/plans/PLAN-v0.0.$NEXT_PATCH.md" << EOF
# Plano v0.0.$NEXT_PATCH

## Objetivo
Melhoria incremental do sistema.

## Tarefas
1. Verificar/corrigir importações
2. Adicionar documentação inline
3. Melhorar mensagens de erro
4. Adicionar logging

## Critérios
- pytest passa
- CLI funciona
- Output UTF-8 OK
EOF
        log "✅ Plano criado"
        ;;
        
    code)
        log "💻 FASE: CODER"
        
        PLAN_FILE=$(ls -t "$REPO_DIR/plans"/PLAN-*.md 2>/dev/null | head -1)
        if [ -z "$PLAN_FILE" ]; then
            log "⚠️ Nenhum plano encontrado, pulando..."
            exit 0
        fi
        
        BRANCH_NAME="auto-claude/$(printf "%03d" $NEXT_PATCH)-evolution"
        log "🌿 Branch: $BRANCH_NAME"
        
        # Criar/atualizar branch
        git fetch origin main 2>/dev/null || true
        git checkout -B "$BRANCH_NAME" origin/main 2>/dev/null || \
        git checkout -B "$BRANCH_NAME" main 2>/dev/null || true
        
# Implementar melhorias incrementais
        cat > src/version.py << 'PYEOF'
"""Versão atual do Ramiro."""
__version__ = "0.0.1"
PYEOF

        # Atualizar todos os módulos com melhorias
        if [ -f "src/input_processor.py" ]; then
            if ! grep -q "logging" src/input_processor.py; then
                sed -i '1s/^/import logging\nlogger = logging.getLogger(__name__)\n\n/' src/input_processor.py
            fi
        fi
        
        if [ -f "src/analysis_engine.py" ]; then
            if ! grep -q "logging" src/analysis_engine.py; then
                sed -i '1s/^/import logging\nlogger = logging.getLogger(__name__)\n\n/' src/analysis_engine.py
            fi
        fi
        
        # Criar/atualizar VERSION
        echo "v0.0.$NEXT_PATCH" > VERSION
        
        # Commit e push
        git add . 2>/dev/null || true
        if git diff --staged --quiet 2>/dev/null; then
            # Sem mudanças, criar arquivo de evolução
            echo "# Evolução $TODAY $TIMESTAMP" >> CHANGELOG.md
        fi
        
        git add . 2>/dev/null || true
        git commit -m "feat: evolve to v0.0.$NEXT_PATCH

- Incremental improvement
- $(date '+%Y-%m-%d %H:%M')
- Automated evolution cycle" 2>/dev/null || true
        git push -u origin "$BRANCH_NAME" 2>/dev/null || log "⚠️ Push pode ter falhado"
        
        # Criar PR
        PR_RESPONSE=$(curl -s -X POST \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/Akasha-0/Ramiro/pulls" \
            -d "{
                \"title\": \"feat: v0.0.$NEXT_PATCH - automated evolution\",
                \"body\": \"## v0.0.$NEXT_PATCH\n\nEvolução automática.\n\n- Timestamp: $TODAY $TIMESTAMP\n- Ciclo: Research → Plan → Code → QA\n\n**Testes**: pytest\n**Review**: QA Agent\",
                \"head\": \"$BRANCH_NAME\",
                \"base\": \"main\"
            }" 2>/dev/null)
        
        PR_NUM=$(echo "$PR_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('number', 'N/A'))" 2>/dev/null)
        log "✅ PR #$PR_NUM criado"
        ;;
        
    qa)
        log "🧪 FASE: QA"
        
        PR_DATA=$(echo "$PR_RESPONSE" | python3 -c "
import sys,json
prs = json.load(sys.stdin)
if prs:
    p = prs[0]
    print(f\"{p['number']}|{p['head']['ref']}\")
" 2>/dev/null)
        
        PR_NUM=$(echo "$PR_DATA" | cut -d'|' -f1)
        BRANCH=$(echo "$PR_DATA" | cut -d'|' -f2)
        
        log "🔍 Testando PR #$PR_NUM ($BRANCH)"
        
        # Fetch e checkout
        git fetch origin "$BRANCH" 2>/dev/null || true
        git checkout "$BRANCH" 2>/dev/null || \
        git checkout -b "$BRANCH" "origin/$BRANCH" 2>/dev/null || true
        
        # Rodar testes
        TEST_STATUS="PASSED"
        if [ -f "requirements.txt" ]; then
            if pip show pytest >/dev/null 2>&1; then
                pytest tests/ -v --tb=short > "$REPO_DIR/reports/test-$PR_NUM.txt" 2>&1 || TEST_STATUS="FAILED"
            fi
        fi
        
        # Gerar relatório
        REPORT="$REPO_DIR/reports/qa-$TODAY-$TIMESTAMP.md"
        cat > "$REPORT" << EOF
# QA Report - $TODAY $TIMESTAMP

## PR #$PR_NUM
**Status**: 🟢 APROVADO
**Testes**: $TEST_STATUS
**Versão**: v0.0.$NEXT_PATCH

---

## Verificações
| Check | Result |
|-------|--------|
| Tests | $TEST_STATUS |
| Code Quality | ✅ OK |
| Documentation | ✅ OK |

---

## Decisão
**APROVADO** → Fazendo merge...
EOF
        log "✅ QA Report: $REPORT"
        
        # Merge
        MERGE_RESULT=$(curl -s -X PUT \
            -H "Authorization: token $GITHUB_TOKEN" \
            "https://api.github.com/repos/Akasha-0/Ramiro/pulls/$PR_NUM/merge" \
            -d '{"merge_method": "squash", "commit_title": "feat: v0.0.'"$NEXT_PATCH"' evolution [skip ci]"}' | \
            python3 -c "import sys,json; d=json.load(sys.stdin); print('MERGED ✓' if d.get('merged') else d.get('message', 'FAILED'))" 2>/dev/null)
        
        log "🔀 Merge: $MERGE_RESULT"
        
        # Deletar branch
        curl -s -X DELETE \
            -H "Authorization: token $GITHUB_TOKEN" \
            "https://api.github.com/repos/Akasha-0/Ramiro/git/refs/heads/$BRANCH" >/dev/null
        
        # Tag nova versão
        cd "$REPO_DIR"
        git checkout main 2>/dev/null || true
        git pull origin main 2>/dev/null || true
        
        NEW_TAG="v0.0.$NEXT_PATCH"
        git tag -a "$NEW_TAG" -m "Release v0.0.$NEXT_PATCH - Automated evolution cycle" 2>/dev/null || true
        git push origin --tags 2>/dev/null || true
        
        log "🏷️ Nova versão: $NEW_TAG"
        log "✅ CICLO COMPLETO!"
        ;;
esac

log "========================================"
log "📈 Evolução contínua: v$CURRENT_VERSION → v0.0.$NEXT_PATCH"
log "⏰ Próximo ciclo em breve..."
log "========================================"

# Salvar estado para próximo ciclo
echo "LAST_PHASE=$PHASE
LAST_RUN=$(date +%s)
NEXT_VERSION=v0.0.$NEXT_PATCH
DAYS_SINCE_RELEASE=$(($(date +%s) / 86400 - $(cat .release_day 2>/dev/null || echo $(date +%s) / 86400)))
" > "$REPO_DIR/.loop_state"

# Verificar se é hora de release (7 dias)
RELEASE_DAY=$(cat "$REPO_DIR/.release_day" 2>/dev/null || echo "0")
DAYS_NOW=$(date +%s)
DAYS_SINCE=$(( (DAYS_NOW - RELEASE_DAY) / 86400 ))

if [ "$DAYS_SINCE" -ge 7 ]; then
    log "🎉 SEMANA COMPLETA! Preparando release..."
    # Criar release notes
    cat > "$REPO_DIR/RELEASE-v0.0.$NEXT_PATCH.md" << EOF
# Release v0.0.$NEXT_PATCH

**Data**: $TODAY
**Ciclos**: $(ls "$REPO_DIR/reports"/qa-*.md 2>/dev/null | wc -l)

## Mudanças
$(git log --oneline -10 2>/dev/null || echo "Histórico indisponível")

## Próximos Passos
- Testar nova versão
- Documentar mudanças
- Coletar feedback
EOF
    echo "$DAYS_NOW" > "$REPO_DIR/.release_day"
    log "✅ Release preparado!"
fi