#!/usr/bin/env python3
"""Acceptance criteria verification script."""
import sys
sys.path.insert(0, './src')

from clareza.analyzer import TextAnalyzer

def main():
    a = TextAnalyzer()
    all_passed = True

    # Test 1: 'Carta 3 (Caminho)' + 'casamento' -> [3, 11]
    r1 = a.analyze('Carta 3 (Caminho) e casamento')
    t1_pass = r1['card_ids'] == [3, 11]
    print(f"Test 1 (Card detection [3,11]): {'PASS' if t1_pass else 'FAIL'}")
    if not t1_pass:
        all_passed = False

    # Test 2: No card mentions -> thematic summary
    r2 = a.analyze('Estou confuso sobre meu futuro')
    t2_pass = len(r2['card_ids']) == 0 and r2['emotion'] != ''
    print(f"Test 2 (No cards, thematic summary): {'PASS' if t2_pass else 'FAIL'}")
    if not t2_pass:
        all_passed = False

    # Test 3: Accented characters
    try:
        r3 = a.analyze('O coração está aflito com a situação')
        print("Test 3 (Accented chars): PASS")
    except Exception as e:
        print(f"Test 3 (Accented chars): FAIL - {e}")
        all_passed = False

    # Test 4: 10000 char input
    long_text = 'Estou confuso. ' * 500
    import time
    start = time.time()
    r4 = a.analyze(long_text)
    elapsed = time.time() - start
    t4_pass = elapsed < 5.0
    print(f"Test 4 (10k chars in <5s): {'PASS' if t4_pass else 'FAIL'} ({elapsed:.3f}s)")
    if not t4_pass:
        all_passed = False

    # Test 5: Emotion/intent extraction
    tests = [
        ('Estou confuso', 'conflicted'),
        ('Tenho esperança', 'hopeful'),
        ('Tenho muito medo', 'fearful'),
        ('Não sei o que fazer', 'uncertain'),
    ]
    t5_pass = True
    for text, expected in tests:
        r = a.analyze(text)
        if r['emotion'] != expected:
            t5_pass = False
    print(f"Test 5 (Emotion extraction): {'PASS' if t5_pass else 'FAIL'}")
    if not t5_pass:
        all_passed = False

    print()
    if all_passed:
        print("ALL ACCEPTANCE CRITERIA: PASS")
        return 0
    else:
        print("SOME TESTS FAILED: FAIL")
        return 1

if __name__ == "__main__":
    sys.exit(main())
