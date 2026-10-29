#!/usr/bin/env python3
"""patch_35b_world_x_reset_fix.py — убрать ложную вставку world_x=0 в спавне бомб.

Причина: patch_35 использовал маркер 's->bomb_spawn_timer = 0.0f;',
который есть и в SDL_AppIterate (блок спавна бомб, каждые 3 сек).
Там сброс world_x недопустим — мир будет телепортироваться каждые 3 сек.

Оставляем сброс только в 3 точках старта:
  - ATTRACT → 1/2/3
  - ATTRACT/SCORE → SPACE
  - R
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

print("=== ДИАГНОСТИКА (до) ===\n")

n_world_reset = len(re.findall(r's->world_x\s+= 0\.0f;', s))
print(f"  s->world_x = 0.0f: {n_world_reset} (ожидается 3, после фикса)")

# Показать все вхождения с контекстом 3 строки до
lines = s.splitlines(keepends=True)
for i, line in enumerate(lines):
    if 's->world_x              = 0.0f;' in line and 'scroll=0' in line:
        print(f"\n  --- pos в файле, строка {i+1} ---")
        for k in range(max(0, i-4), min(len(lines), i+2)):
            marker = '>>>' if k == i else '   '
            print(f"  {marker} {lines[k].rstrip()}")

print("\n=== ПРИМЕНЕНИЕ ===\n")

# Стратегия: удалить world_x-reset ТОЛЬКО если в 3 предыдущих строках
# есть 'if (s->bomb_spawn_timer > 3.0f)'. Это однозначно блок спавна.
# В трёх точках старта if-блока с bomb_spawn_timer > 3.0f НЕТ
# (там просто последовательность reset'ов в SDL_AppEvent).

pat = re.compile(
    r'(if \(s->bomb_spawn_timer > 3\.0f\) \{\n'
    r'\s+s->bomb_spawn_timer\s+= 0\.0f;\n)'
    r'(\s+s->world_x\s+= 0\.0f;[^\n]*\n)',
    re.MULTILINE
)

s, n = pat.subn(r'\1', s)
print(f"{'OK' if n == 1 else 'WARN'}: удалено ложных вставок world_x в спавне бомб: {n}")

if n == 0:
    # Fallback: возможно, форматирование чуть иное. Ищем контекстно.
    print("Пробую fallback: контекстный поиск…")
    lines = s.splitlines(keepends=True)
    out = []
    removed = 0
    for i, line in enumerate(lines):
        if 's->world_x              = 0.0f;' in line and 'scroll=0' in line:
            # Смотрим 4 строки назад
            ctx = ''.join(lines[max(0, i-4):i])
            if 'if (s->bomb_spawn_timer > 3.0f)' in ctx:
                removed += 1
                print(f"  удаляю строку {i+1} (в контексте спавна бомб)")
                continue
        out.append(line)
    s = ''.join(out)
    n = removed
    print(f"fallback: удалено {n}")

p.write_text(s)

# ─────────────────────────────────────────────────────────────
# Верификация
# ─────────────────────────────────────────────────────────────
print("\n=== ВЕРИФИКАЦИЯ (после) ===\n")
s = p.read_text()
n_world_reset = len(re.findall(r's->world_x\s+= 0\.0f;', s))
print(f"  s->world_x = 0.0f: {n_world_reset} (ожидается 3)")

# Где остались
for m in re.finditer(r's->world_x\s+= 0\.0f;', s):
    line_start = s.rfind('\n', 0, m.start()) + 1
    line_end = s.find('\n', m.end())
    # Ближайший вышестоящий 'start' или 'restart'
    ctx = s[max(0, line_start - 200):line_start]
    tag = ('ATTRACT/SCORE' if 'SDLK_SPACE' in ctx[-400:] else
           'R-restart'     if 'SDLK_R' in ctx[-400:] else
           'start_diff'    if 'start_diff' in ctx[-400:] else
           '??? ПРОВЕРИТЬ')
    print(f"  остаток: {tag}")
