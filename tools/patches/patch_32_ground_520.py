#!/usr/bin/env python3
"""patch_32_ground_520.py — линия земли на 520 (5% резерв внизу).

Layout (800×600):
  0-328    небо + звёзды
  328-520  параллакс (lane_h=192)
  520-600  земля: луноход на 520, кратер до ~566, резерв 566-600
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

print("=== ДИАГНОСТИКА (до) ===\n")

m = re.search(r'struct Player\s*\{[^}]*?float y = ([\d.]+f);', s, re.DOTALL)
print(f"  Player.y default: {m.group(1) if m else 'NOT FOUND'}")

for mm in re.finditer(r's->player\.y = ([\d.]+f);', s):
    print(f"  player.y = {mm.group(1)}")

m = re.search(r's->player\.y >= ([\d.]+f)', s)
print(f"  landing: >= {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r's->player\.y > ([\d.]+f)', s)
print(f"  rock threshold: > {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r'const float lane_y = ([^;]+);', s)
print(f"  lane_y: {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r'const float gy = ([\d.]+f)', s)
print(f"  gy: {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r's->bullets\[b\]\.y - ([\d.]+f)', s)
print(f"  bullet hitbox: - {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r'NLO_HEIGHTS\[3\] = \{[^}]*\}', s)
print(f"  NLO: {m.group(0) if m else 'NOT FOUND'}")

m = re.search(r'star_y\(([\d.]+f), ([\d.]+f)\)', s)
print(f"  star_y: ({m.group(1) if m else '?'}, {m.group(2) if m else '?'})")

print("\n=== ПРИМЕНЕНИЕ ===\n")
changes = 0

# 1) struct Player: float y = XX → 520
s, n = re.subn(
    r'(struct Player\s*\{[^}]*?float y = )[\d.]+f;',
    r'\g<1>520.0f;',
    s, flags=re.DOTALL)
if n: changes += 1; print(f"OK: Player.y default → 520.0f")

# 2) все s->player.y = XX → 520
s, n = re.subn(r's->player\.y = [\d.]+f;', 's->player.y = 520.0f;', s)
if n: changes += 1; print(f"OK: player.y = 520.0f ({n} мест)")

# 3) landing: s->player.y >= XX → 520
s, n = re.subn(r's->player\.y >= [\d.]+f', 's->player.y >= 520.0f', s)
if n: changes += 1; print(f"OK: landing >= 520.0f ({n})")

# 4) rock threshold: s->player.y > XX → 480
s, n = re.subn(r's->player\.y > [\d.]+f', 's->player.y > 480.0f', s)
if n: changes += 1; print(f"OK: rock threshold > 480.0f ({n})")

# 5) lane_y → 328
s, n = re.subn(r'const float lane_y = [^;]+;', 'const float lane_y = 328.0f;', s)
if n: changes += 1; print(f"OK: lane_y = 328.0f ({n})")

# 6) gy → 520 (с новым комментарием)
s, n = re.subn(r'const float gy = [\d.]+f[^;]*;', 'const float gy = 520.0f;  // = player.y', s)
if n: changes += 1; print(f"OK: gy = 520.0f ({n})")

# 7) bullet hitbox камня: - XX → 502
s, n = re.subn(r's->bullets\[b\]\.y - [\d.]+f', 's->bullets[b].y - 502.0f', s)
if n: changes += 1; print(f"OK: bullet hitbox - 502.0f ({n})")

# 8) NLO heights → 150/250/350
s, n = re.subn(
    r'(NLO_HEIGHTS\[3\] = \{)[^}]*\}',
    r'\g<1> 150.0f, 250.0f, 350.0f }',
    s)
if n: changes += 1; print(f"OK: NLO heights → 150/250/350 ({n})")

# 9) star_y → 0/300
s, n = re.subn(r'star_y\([\d.]+f, [\d.]+f\)', 'star_y(0.0f, 300.0f)', s)
if n: changes += 1; print(f"OK: star_y → 0/300 ({n})")

p.write_text(s)
print(f"\nИзменено: {changes}/9")
