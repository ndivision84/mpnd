#!/usr/bin/env python3
"""patch_33_misc_fixes.py — сборка мелких фиксов #4, #5, #6, #9.

Зависит от: patch_32_ground_520.py (gy=520, player.y=520).

Фиксы:
  #4 — закомментировать мёртвый код (draw_score, draw_game_over) через #if 0
  #5 — сброс enemy_spawn_timer / bomb_spawn_timer при старте и R
  #6 — отрисовка препятствий ДО лунохода (луноход поверх)
  #9 — проверка TIME UP в update, а не в рендере (без кадра «TIME:00»)
  (+ бонус) — закомментировать неиспользуемый int score
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

print("=== ДИАГНОСТИКА (до) ===\n")

# #4
print(f"  draw_score:      {'найден' if 'static void draw_score' in s else 'НЕ НАЙДЕН'}")
print(f"  draw_game_over:  {'найден' if 'static void draw_game_over' in s else 'НЕ НАЙДЕН'}")
print(f"  #if 0:           {'УЖЕ ЕСТЬ' if '#if 0' in s else 'нет'}")

# #5
n_enemy = len(re.findall(r's->enemy_spawn_timer\s+= 0\.0f;', s))
n_bomb  = len(re.findall(r's->bomb_spawn_timer\s+= 0\.0f;', s))
print(f"  s->enemy_spawn_timer = 0.0f: {n_enemy} (ожидается 0)")
print(f"  s->bomb_spawn_timer  = 0.0f: {n_bomb} (ожидается 0)")

# #6
i_obs = s.find('// ── Отрисовка препятствий')
i_buggy = s.find('draw_buggy(s->renderer,')
print(f"  препятствия@pos: {i_obs}")
print(f"  draw_buggy@pos:  {i_buggy}")
if i_obs > 0 and i_buggy > 0:
    order = 'ПРЕПЯТСТВИЯ ПОСЛЕ (нужен фикс)' if i_obs > i_buggy else 'OK (уже до)'
    print(f"  порядок: {order}")

# #9
print(f"  if (time_left == 0) в рендере: {'есть' if 'if (time_left == 0)' in s else 'нет'}")
print(f"  проверка в update:             {'есть' if 's->play_time >= 60.0f' in s else 'нет'}")

print("\n=== ПРИМЕНЕНИЕ ===\n")
changes = 0

# ─────────────────────────────────────────────────────────────
# #4: #if 0 вокруг draw_score и draw_game_over
# ─────────────────────────────────────────────────────────────
if '#if 0' not in s:
    s, n = re.subn(
        r'(static void draw_score\(.*?\n\}\n\n)(SDL_AppResult SDL_AppIterate)',
        r'#if 0\n\g<1>#endif\n\n\g<2>',
        s, flags=re.DOTALL)
    if n:
        changes += 1
        print(f"OK: #if 0 … #endif вокруг draw_score/draw_game_over ({n})")
    else:
        print("FAIL: не удалось обернуть draw_score/draw_game_over")
else:
    print("SKIP: #if 0 уже есть")

# ─────────────────────────────────────────────────────────────
# #5: сброс enemy_spawn_timer / bomb_spawn_timer
# ─────────────────────────────────────────────────────────────
# Случай 1 и 2: ATTRACT/SCORE → play_time рядом (12 отступ)
s, n1 = re.subn(
    r'(            s->obstacle_spawn_timer = 0\.0f;\n)(            s->play_time = 0\.0f;)',
    r'\g<1>            s->enemy_spawn_timer    = 0.0f;\n'
    r'            s->bomb_spawn_timer     = 0.0f;\n'
    r'\g<2>',
    s)
# Случай 3: R-restart → return рядом (8 отступ)
s, n3 = re.subn(
    r'(        s->obstacle_spawn_timer = 0\.0f;\n)(        return SDL_APP_CONTINUE;)',
    r'\g<1>        s->enemy_spawn_timer    = 0.0f;\n'
    r'        s->bomb_spawn_timer     = 0.0f;\n'
    r'\g<2>',
    s)
if n1 + n3 == 3:
    changes += 1
    print(f"OK: сброс таймеров спавна ({n1} в start, {n3} в R = {n1+n3}/3)")
elif n1 + n3 == 0 and len(re.findall(r's->enemy_spawn_timer\s+= 0\.0f;', s)) >= 3:
    print("SKIP: сброс таймеров спавна уже сделан")
else:
    print(f"WARN: сброс таймеров спавна: {n1+n3}/3 (ожидалось 3)")

# ─────────────────────────────────────────────────────────────
# #6: перенести отрисовку препятствий ПЕРЕД draw_buggy
# ─────────────────────────────────────────────────────────────
START_OBS = '    // ── Отрисовка препятствий (выровнено по колёсам: gy=460) ──'
END_OBS   = '    // ── Отрисовка тарелок (56×36, белый + чёрная обводка) ──'
DRAW_BUGGY = '    draw_buggy(s->renderer,\n'

i_start = s.find(START_OBS)
i_end   = s.find(END_OBS, i_start) if i_start >= 0 else -1
i_buggy = s.find(DRAW_BUGGY)

if i_start >= 0 and i_end > i_start and i_buggy >= 0:
    if i_buggy < i_start:
        # Извлекаем блок препятствий (включая trailing \n\n)
        block = s[i_start:i_end]
        # Убираем из старого места
        s = s[:i_start] + s[i_end:]
        # Обновляем устаревший комментарий (gy=460 → актуальный)
        block = block.replace(
            START_OBS,
            '    // ── Отрисовка препятствий ДО лунохода (луноход поверх) ──')
        # Вставляем ПЕРЕД draw_buggy
        i_buggy_new = s.find(DRAW_BUGGY)
        if i_buggy_new >= 0:
            s = s[:i_buggy_new] + block + s[i_buggy_new:]
            changes += 1
            print("OK: препятствия перенесены до draw_buggy")
        else:
            print("FAIL: не найден draw_buggy для вставки")
    else:
        print("SKIP: препятствия уже перед draw_buggy")
elif i_start < 0:
    print("SKIP: блок препятствий не найден (уже перенесён?)")
else:
    print("WARN: порядок draw_buggy/препятствий нестандартный")

# ─────────────────────────────────────────────────────────────
# #9: TIME UP — в update, без кадра «TIME:00»
# ─────────────────────────────────────────────────────────────
# Шаг 1: добавить проверку после world_x update
old_update = '    s->world_x += s->auto_speed * dt;'
new_update = '''    s->world_x += s->auto_speed * dt;

    // ★ Проверка окончания времени — ДО рендера (без кадра «TIME:00»)
    if (s->state == STATE_PLAYING && s->play_time >= 60.0f) {
        SDL_Log("TIME UP! play_time=%.1f -> GAME_OVER", s->play_time);
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
    }'''
if 's->play_time >= 60.0f' not in s:
    if old_update in s:
        s = s.replace(old_update, new_update, 1)
        changes += 1
        print("OK: проверка TIME UP добавлена в update")
    else:
        print("FAIL: не найден world_x update")
else:
    print("SKIP: проверка TIME UP уже в update")

# Шаг 2: удалить старую проверку из HUD
old_hud = '''    int time_left = 60 - (int)s->play_time;
    if (time_left < 0) time_left = 0;
    if (time_left == 0) {
        SDL_Log("TIME UP! play_time=%.1f -> GAME_OVER", s->play_time);
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
    }
    draw_hud(s->renderer, s->score, time_left, s->world_x, s->difficulty);'''
new_hud = '''    int time_left = 60 - (int)s->play_time;
    if (time_left < 0) time_left = 0;
    draw_hud(s->renderer, s->score, time_left, s->world_x, s->difficulty);'''
if old_hud in s:
    s = s.replace(old_hud, new_hud, 1)
    changes += 1
    print("OK: старая проверка TIME UP удалена из HUD")
else:
    print("SKIP: старая проверка TIME UP уже удалена")

# Бонус: закомментировать неиспользуемый int score
old_score = '    int score = (int)(s->world_x * 10);\n'
new_score = '    // int score = (int)(s->world_x * 10);   // не используется\n'
if old_score in s:
    s = s.replace(old_score, new_score, 1)
    changes += 1
    print("OK: неиспользуемый int score закомментирован")

p.write_text(s)
print(f"\nИзменено: {changes}/5")

# ─────────────────────────────────────────────────────────────
# Верификация
# ─────────────────────────────────────────────────────────────
print("\n=== ВЕРИФИКАЦИЯ (после) ===\n")
s = p.read_text()

n_enemy = len(re.findall(r's->enemy_spawn_timer\s+= 0\.0f;', s))
n_bomb  = len(re.findall(r's->bomb_spawn_timer\s+= 0\.0f;', s))
print(f"  сброс enemy_spawn_timer: {n_enemy}/3 {'OK' if n_enemy >= 3 else 'FAIL'}")
print(f"  сброс bomb_spawn_timer:  {n_bomb}/3 {'OK' if n_bomb >= 3 else 'FAIL'}")

i_obs = s.find('// ── Отрисовка препятствий')
i_buggy = s.find('draw_buggy(s->renderer,')
if i_obs > 0 and i_buggy > 0:
    print(f"  порядок препятствий/draw_buggy: {'OK' if i_obs < i_buggy else 'FAIL'}")

print(f"  #if 0 присутствует:   {'да' if '#if 0' in s else 'НЕТ'}")
print(f"  TIME UP в update:     {'да' if 's->play_time >= 60.0f' in s else 'НЕТ'}")
