#!/usr/bin/env python3
"""patch_37c_cstdio.py — добавить #include <cstdio> для snprintf."""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text(encoding='utf-8')

print("=== ДИАГНОСТИКА ===\n")
print(f"  <cstdio>:      {'есть' if '#include <cstdio>' in s else 'НЕТ'}")
print(f"  <chrono>:      {'есть' if '#include <chrono>' in s else 'НЕТ'}")
print(f"  snprintf refs: {s.count('snprintf')}")

if '#include <cstdio>' in s:
    print("\nSKIP: <cstdio> уже есть")
    raise SystemExit(0)

if '#include <chrono>' in s:
    s = s.replace('#include <chrono>', '#include <chrono>\n#include <cstdio>', 1)
    p.write_text(s, encoding='utf-8')
    print("\nOK: <cstdio> добавлен после <chrono>")
else:
    # fallback: после любого include
    import re
    m = re.search(r'(#include <[^>]+>\n)(?!.*#include)', s)
    if m:
        pos = m.end()
        s = s[:pos] + '#include <cstdio>\n' + s[pos:]
        p.write_text(s, encoding='utf-8')
        print("\nOK: <cstdio> добавлен (fallback)")
    else:
        print("\nFAIL: не нашли куда вставить")
        raise SystemExit(1)

# Верификация
s = p.read_text(encoding='utf-8')
print("\n=== ВЕРИФИКАЦИЯ ===\n")
print(f"  <cstdio>:      {'OK' if '#include <cstdio>' in s else 'FAIL'}")
