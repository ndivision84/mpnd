#!/usr/bin/env python3
"""patch_31_lower_field.py — опустить игровое поле: земля 50% от низа.

Целевые значения:
  player.y = 300, gy = 300, lane_y = 108 (=300-192)
  порог камня = 260, hitbox камня = 282
  NLO heights = 70/110/150, star_y = 0/140

Сначала печатает текущие значения (диагностика), потом меняет.
Regex рассчитан на ЛЮБОЕ текущее значение (не на одно фиксированное).
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

print("=== ДИАГНОСТИКА (до правки) ===\n")

m = re.search(r'struct Player\s*\{[^}]*?float y = ([\d.]+f);', s, re.DOTALL)
print(f"  Player.y (default): {m.group(1) if m else 'NOT FOUND'}")

for mm in re.finditer(r's->player\.y = ([\d.]+f);', s):
    print(f"  player.y = {mm.group(1)}  (offset {mm.start()})")

m = re.search(r's->player\.y >= ([\d.]+f)', s)
print(f"  landing: >= {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r'const float lane_y = ([^;]+);', s)
print(f"  lane_y: {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r'const float gy = ([\d.]+f)', s)
print(f"  gy: {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r's->player\.y > ([\d.]+f)', s)
print(f"  rock threshold: > {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r's->bullets\[b\]\.y - ([\d.]+f)', s)
print(f"  bullet hitbox: - {m.group(1) if m else 'NOT FOUND'}")

m = re.search(r'NLO_HEIGHTS\[3\] = \{[^}]*\}', s)
print(f"  NLO: {m.group(0) if m else 'NOT FOUND'}")

m = re.search(r'star_y\(([\d.]+f), ([\d.]+f)\)', s)
print(f"  star_y: ({m.group(1) if m else '?'}, {m.group(2) if m else '?'})")

print("\n=== ПРИМЕНЕНИЕ ===\n")
changes = 0

# 1) struct Player: float y = XX → 300.0f
s, n = re.subn(
    r'(struct Player\s*\{[^}]*?float y = )[\d.]+f;',
    r'\g<1>300.0f;',
    s, flags=re.DOTALL)
if n: changes += 1; print(f"OK: Player.y default → 300.0f")

# 2) Все s->player.y = XX → 300.0f
s, n = re.subn(r's->player\.y = [\d.]+f;', 's->player.y = 300.0f;', s)
if n: changes += 1; print(f"OK: player.y = → 300.0f ({n} мест)")

# 3) s->player.y >= XX → >= 300.0f
s, n = re.subn(r's->player\.y >= [\d.]+f', 's->player.y >= 300.0f', s)
if n: changes += 1; print(f"OK: landing >= 300.0f ({n})")

# 4) lane_y: любое выражение → 108.0f
s, n = re.subn(r'const float lane_y = [^;]+;', 'const float lane_y = 108.0f;', s)
if n: changes += 1; print(f"OK: lane_y = 108.0f ({n})")

# 5) gy
s, n = re.subn(r'const float gy = [\d.]+f', 'const float gy = 300.0f', s)
if n: changes += 1; print(f"OK: gy = 300.0f ({n})")

# 6) Порог камня (s->player.y > X) — единственное вхождение с `>`
s, n = re.subn(r's->player\.y > [\d.]+f', 's->player.y > 260.0f', s)
if n: changes += 1; print(f"OK: rock threshold > 260.0f ({n})")

# 7) Hitbox камня (bullet.y - X)
s, n = re.subn(r's->bullets\[b\]\.y - [\d.]+f', 's->bullets[b].y - 282.0f', s)
if n: changes += 1; print(f"OK: bullet hitbox - 282.0f ({n})")

# 8) NLO heights — якорь на NLO_HEIGHTS[3]
s, n = re.subn(
    r'(NLO_HEIGHTS\[3\] = \{)[^}]*\}',
    r'\g<1> 70.0f, 110.0f, 150.0f }',
    s)
if n: changes += 1; print(f"OK: NLO heights → 70/110/150 ({n})")

# 9) star_y
s, n = re.subn(r'star_y\([\d.]+f, [\d.]+f\)', 'star_y(0.0f, 140.0f)', s)
if n: changes += 1; print(f"OK: star_y → 0.0/140.0 ({n})")

p.write_text(s)
print(f"\nИзменено: {changes}/9")
