#!/usr/bin/env python3
"""patch_35_world_x_reset.py — сброс world_x = 0 при старте/R.

Обоснование из ROM-анализа:
  scroll (0xE1E2) инициализируется в 0 при загрузке уровня
  (level init 0x0BB7). Наш аналог — s->world_x.

  Без сброса после GAME_OVER/R параллакс, препятствия и счётчик
  «продолжают» уехавшую вселенную вместо чистого старта.

Точки применения:
  1. ATTRACT → 1/2/3  (s->state == STATE_ATTRACT)
  2. ATTRACT/SCORE → SPACE (STATE_PLAYING)
  3. R — restart

Зависит от: patch_33 (строки s->bomb_spawn_timer = 0.0f; есть везде).
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

print("=== ДИАГНОСТИКА (до) ===\n")

n_bomb_reset = len(re.findall(r's->bomb_spawn_timer\s+= 0\.0f;', s))
n_world_reset = len(re.findall(r's->world_x\s+= 0\.0f;', s))
n_world_any   = len(re.findall(r's->world_x', s))

print(f"  s->bomb_spawn_timer = 0.0f: {n_bomb_reset} (маркер от patch_33)")
print(f"  s->world_x = 0.0f:          {n_world_reset} (ожидается 0)")
print(f"  s->world_x (всего):         {n_world_any}")
print(f"  auto_speed update:          "
      f"{'есть' if 's->auto_speed * dt' in s else 'НЕТ'}")

# Дополнительно: диагностика, где обнуляются таймеры (для отчёта)
for m in re.finditer(r'(s->obstacle_spawn_timer = 0\.0f;)', s):
    line_start = s.rfind('\n', 0, m.start()) + 1
    line = s[line_start:m.start()].strip()
    print(f"  обнуление таймеров @ pos {m.start()} (indent={len(s[line_start:m.start()])}):")
    print(f"    …{line}")

print("\n=== ПРИМЕНЕНИЕ ===\n")

if n_world_reset >= 3:
    print("SKIP: s->world_x = 0.0f уже установлено в ≥3 местах")
    raise SystemExit(0)

# Стратегия: после КАЖДОГО s->bomb_spawn_timer = 0.0f;
# (который patch_33 поставил ровно в 3 точки старта/R) добавить
# s->world_x = 0.0f; с той же индентацией.
pat = re.compile(
    r'^(?P<indent>[ \t]*)s->bomb_spawn_timer\s+= 0\.0f;[ \t]*\n',
    re.MULTILINE)

inserted = 0
def repl(m):
    global inserted
    indent = m.group('indent')
    inserted += 1
    return (f"{indent}s->bomb_spawn_timer     = 0.0f;\n"
            f"{indent}s->world_x              = 0.0f;   // ROM: scroll=0 на init уровня\n")

s, n = pat.subn(repl, s)
print(f"OK: вставлено s->world_x = 0.0f после bomb_spawn_timer ({n} мест)")

if n == 0:
    print("FAIL: маркер bomb_spawn_timer не найден — применяйте patch_33 сначала")
    raise SystemExit(1)
if n < 3:
    print(f"WARN: ожидалось 3 места, найдено {n}. Проверьте вручную.")

p.write_text(s)

# ─────────────────────────────────────────────────────────────
# Верификация
# ─────────────────────────────────────────────────────────────
print("\n=== ВЕРИФИКАЦИЯ (после) ===\n")
s = p.read_text()
n_world_reset = len(re.findall(r's->world_x\s+= 0\.0f;', s))
print(f"  s->world_x = 0.0f: {n_world_reset} (ожидается 3)")
print(f"  суммарно s->world_x: {s.count('s->world_x')}")

# Показать контекст каждого вхождения
for i, m in enumerate(re.finditer(r's->world_x\s+= 0\.0f;', s), 1):
    line_start = s.rfind('\n', 0, m.start()) + 1
    line_end = s.find('\n', m.end())
    ctx_before = s[max(0, line_start - 60):line_start].split('\n')[-1].strip()
    print(f"  #{i}: …{ctx_before}")
    print(f"      {s[line_start:line_end].strip()}")
