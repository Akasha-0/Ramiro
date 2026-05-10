# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Sistema de Clareza Simbólico-Estratégica

CLI em Python que transforma relatos复杂os do usuário (dúvidas pessoais, símbolos, tiragens de Baralho Cigano) em análises estruturadas em Markdown.

## Commands

```bash
# Executar CLI
python -m src.main --help
python -m src.main analyze -i "texto" -f text
python -m src.main analyze -i "casa,estrela" -f symbols -o report.md

# Testes
pytest tests/ -v
pytest tests/test_input_processor.py -v
pytest tests/test_input_processor.py::test_parse_free_text -v
```

## Architecture

O projeto é um **pipeline linear de módulos** em `src/`. Cada módulo tem responsabilidade única e se comunica via tipos definidos em `types.py` — nunca dicionários soltos.

```
User Input → input_processor.py → analysis_engine.py → boundaries.py → report_generator.py → Markdown
```

- **`src/types.py`** — Definições centrais (StructuredInput, AnalysisResult, ValidatedOutput). Todos os módulos importam daqui.
- **`src/main.py`** — Entry point argparse; ancora `clareza` via `[project.scripts]` em `pyproject.toml`.
- **`src/input_processor.py`** — Parseia texto livre, CSV (tiragens), e símbolos separados por vírgula.
- **`src/analysis_engine.py`** — Mapeamento simbólico, detecção de temas, identificação de riscos e decisões.
- **`src/boundaries.py`** — Filtro ético: `BLOCKED_KEYWORDS`, `validate_output()`, `inject_disclaimer()`. Aplicado **antes** da geração do relatório.
- **`src/report_generator.py`** — Template `REPORT_TEMPLATE` com 5 seções fixas: Diagnóstico, Interpretação Simbólica, Riscos Identificados, Caminhos de Decisão, Plano Prático.
- **`data/cigano_deck.json`** — 36 cartas estruturadas (lidas por `symbols.py`).

## Important Patterns

**Comunicacao entre módulos**: Sempre via dataclasses de `types.py`, não dicts.

**Guardrails**: `boundaries.py` é Called after `analysis_engine.py`, antes de `report_generator.py`. A validação é case-insensitive e normaliza caracteres especiais.

**CLI subcommand**: O comando `analyze` é o único subparser. Args: `-i/--input` (required), `-f/--format` (choices: text|spread|symbols, default text), `-o/--output` (opcional, salva .md).

**Encoding**: Todos os arquivos Python usam UTF-8; todo output preserva acentos do português.

## Development Notes

- Dependências em `pyproject.toml` (setuptools, sem dependências externas para análise — padrão-based only no MVP).
- `pytest` em `dev` optional-dependencies; `click` em `dependencies`.
- Não usar `print` para debug em produção — usar `logging`.
- Não fazer afirmações deterministas no output (guardrails devem atuar).
