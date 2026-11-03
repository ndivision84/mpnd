#!/usr/bin/env python3
"""patch_38b — убрать structs из main.cpp (они уже в app.h)."""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text(encoding='utf-8')

print("=== ДИАГНОСТИКА (до) ===\n")
print(f"  struct Layer:    {'есть' if 'struct Layer {' in s else 'НЕТ'}")
print(f"  struct Player:   {'есть' if 'struct Player {' in s else 'НЕТ'}")
print(f"  enum GameState:  {'есть' if 'enum GameState {' in s else 'НЕТ'}")
print(f"  struct AppState: {'есть' if 'struct AppState {' in s else 'НЕТ'}")
print(f"  #include app.h:  {'есть' if '#include \"app.h\"' in s else 'НЕТ'}")

changes = 0

# 1) #include "app.h"
if '#include "app.h"' not in s:
    lines = s.split('\n')
    last_inc = -1
    for i, ln in enumerate(lines):
        if ln.startswith('#include'):
            last_inc = i
    if last_inc >= 0:
        lines.insert(last_inc + 1, '#include "app.h"')
        s = '\n'.join(lines)
        changes += 1
        print('OK: #include "app.h"')

# 2) struct Layer … Player (до enum GameState)
pat_a = re.compile(r'struct Layer \{.*?(?=enum GameState)', re.DOTALL)
if 'struct Layer {' in s and 'enum GameState' in s:
    s, n = pat_a.subn('// (structs вынесены в app.h)\n\n', s, count=1)
    if n:
        changes += 1
        print("OK: удалены structs Layer…Player")
    else:
        print("WARN: блок Layer…Player не совпал")

# 3) enum GameState … AppState (до // 6 базовых цветов)
pat_b = re.compile(r'enum GameState \{.*?(?=// 6 базовых цветов)', re.DOTALL)
if 'enum GameState {' in s and '// 6 базовых цветов' in s:
    s, n = pat_b.subn('// (GameState и AppState вынесены в app.h)\n\n', s, count=1)
    if n:
        changes += 1
        print("OK: удалены enum GameState + struct AppState")
    else:
        print("WARN: блок GameState…AppState не совпал")

p.write_text(s, encoding='utf-8')
print(f"\nВсего изменений: {changes}")

print("\n=== ВЕРИФИКАЦИЯ ===\n")
s = p.read_text(encoding='utf-8')
checks = [
    ('без struct Layer',     'struct Layer {' not in s),
    ('без struct Player',    'struct Player {' not in s),
    ('без enum GameState',   'enum GameState {' not in s),
    ('без struct AppState',  'struct AppState {' not in s),
    ('с #include "app.h"',   '#include "app.h"' in s),
    ('BASE_COLORS на месте', 'BASE_COLORS' in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
