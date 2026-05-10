#!/usr/bin/env python3
"""Script para descobrir os IDs das cartas no baralho."""

from src.symbols import get_all_symbols

symbols = get_all_symbols()

# Find cards with same last digit
by_digit = {}
for s in symbols:
    digit = s.id % 10
    if digit not in by_digit:
        by_digit[digit] = []
    by_digit[digit].append((s.id, s.name))

print("=== Cartas com o mesmo dígito final ===")
for d in sorted(by_digit.keys()):
    if len(by_digit[d]) >= 2:
        print("Digit", d, ":", by_digit[d])

print("\n=== Cartas consecutivas ===")
sorted_symbols = sorted(symbols, key=lambda s: s.id)
for i in range(len(sorted_symbols) - 1):
    if sorted_symbols[i+1].id == sorted_symbols[i].id + 1:
        print(f"  {sorted_symbols[i].id}: {sorted_symbols[i].name} -> {sorted_symbols[i+1].id}: {sorted_symbols[i+1].name}")

print("\n=== Cartas por tema ===")
by_theme = {}
for s in symbols:
    if s.theme not in by_theme:
        by_theme[s.theme] = []
    by_theme[s.theme].append((s.id, s.name))

for theme in sorted(by_theme.keys()):
    cards = by_theme[theme]
    if len(cards) >= 2:
        print("Tema", theme, ":", cards)

print("\n=== Teste de busca por nome ===")
test_names = ["A Estrela", "O Mercado", "A Floresta", "A Cruz", "A Casa", "A Cesta", "O Cemitério", "A Cegonha", "Os Livros", "O Cofre"]
for name in test_names:
    from src.symbols import get_symbol_by_name
    s = get_symbol_by_name(name)
    if s:
        print(f"{name}: ID={s.id}, Tema={s.theme}")
    else:
        print(f"{name}: NÃO ENCONTRADO")
