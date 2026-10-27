#!/usr/bin/env python3
"""patch_12_nlo_heights.py — NLO на 3 фиксированных высотах (случайно)."""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# Ищем строку спавна NLO
old_pattern = r's->nlos\[i\]\.y\s*=\s*[0-9.]+f\s*\+\s*\(float\)\(rand\(\)\s*%\s*[0-9]+\);'
m = re.search(old_pattern, s)
if m:
    print(f"[i] текущий Y спавна NLO: {m.group(0)}")

# Замена: 3 фиксированные высоты
new_code = """{
                            static const float NLO_HEIGHTS[3] = { 195.0f, 235.0f, 275.0f };
                            s->nlos[i].y = NLO_HEIGHTS[rand() % 3];
                        }"""

# Попробуем найти и заменить через regex
new_s, n = re.subn(old_pattern, new_code.strip(), s, count=1)
if n > 0:
    s = new_s
    changes += 1
    print("OK: NLO на 3 фиксированных высотах (195 / 235 / 275)")
else:
    print("!! не найден шаблон спавна NLO 'nlos[i].y = ... + rand()%...'")
    # Диагностика: ищем любые NLO y=
    for line in s.split('\n'):
        if 'nlos[i].y' in line:
            print(f"   найдено: {line.strip()}")

p.write_text(s)
print(f"\nИзменено: {changes}/1")
