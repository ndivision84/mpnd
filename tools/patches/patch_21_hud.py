#!/usr/bin/env python3
"""patch_21_hud.py

Включает HUD (TIME / счёт / CAUTION) в PLAYING.
- Добавляет float play_time в AppState
- TIME считается от play_time, а не от world_x
- play_time == 60 → STATE_GAME_OVER
- draw_hud включён (вместо '// draw_hud отключён')
- draw_score (отдельный) убран
- HUD: счёт 6 цифр → 5
"""
from pathlib import Path
import re

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) AppState: float play_time
# ═══════════════════════════════════════════════════════════════
if 'float         play_time' not in s and 'float play_time' not in s:
    # Найдём "float state_timer = 0.0f;" в AppState
    old = "    float         state_timer = 0.0f;"
    new = """    float         state_timer = 0.0f;
    float         play_time   = 0.0f;   // секунды в PLAYING (для TIME)"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: AppState.play_time")
    else:
        print("!! не найден 'float state_timer = 0.0f;' в AppState")

# ═══════════════════════════════════════════════════════════════
# 2) play_time += dt (в начале PLAYING-блока)
# ═══════════════════════════════════════════════════════════════
if 's->play_time += dt' not in s:
    # Найдём строку, где обновляется world_x (это в PLAYING, потому что ATTRACT раньше делает return)
    old = "    s->world_x += s->auto_speed * dt;"
    new = """    s->play_time += dt;
    s->world_x += s->auto_speed * dt;"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: play_time += dt")
    else:
        print("!! не найден 's->world_x += s->auto_speed * dt;'")

# ═══════════════════════════════════════════════════════════════
# 3) time_left: от world_x/100 → от play_time
# ═══════════════════════════════════════════════════════════════
old = "    int time_left = 60 - (int)(s->world_x / 100);"
new = "    int time_left = 60 - (int)s->play_time;"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: time_left от play_time")
else:
    print("!! не найден 'int time_left = 60 - (int)(s->world_x / 100);'")

# ═══════════════════════════════════════════════════════════════
# 4) time_left == 0 → GAME_OVER
# ═══════════════════════════════════════════════════════════════
if 's->play_time >= 60.0f' not in s and 'time_left <= 0' not in s:
    old = """    int time_left = 60 - (int)s->play_time;
    if (time_left < 0) time_left = 0;"""
    new = """    int time_left = 60 - (int)s->play_time;
    if (time_left < 0) time_left = 0;
    if (time_left == 0) {
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
    }"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: time_left == 0 → GAME_OVER")
    else:
        # fallback — вставим после time_left
        old2 = "    if (time_left < 0) time_left = 0;"
        new2 = """    if (time_left < 0) time_left = 0;
    if (time_left == 0) {
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
    }"""
        if old2 in s:
            s = s.replace(old2, new2, 1); changes += 1
            print("OK: time_left == 0 → GAME_OVER (fallback)")

# ═══════════════════════════════════════════════════════════════
# 5) Включить draw_hud (заменить комментарий)
# ═══════════════════════════════════════════════════════════════
old = "    // draw_hud отключён - HUD вернём позже"
new = "    draw_hud(s->renderer, s->score, time_left, s->world_x);"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: draw_hud включён")
else:
    print("!! не найден '// draw_hud отключён - HUD вернём позже'")

# ═══════════════════════════════════════════════════════════════
# 6) Убрать отдельный draw_score (перенесён в draw_hud)
# ═══════════════════════════════════════════════════════════════
old = "    draw_score(s->renderer, s->score);"
new = "    // draw_score вызывается внутри draw_hud"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: draw_score убран (перенесён в draw_hud)")
else:
    print("!! не найден 'draw_score(s->renderer, s->score);'")

# ═══════════════════════════════════════════════════════════════
# 7) draw_hud: счёт 6 цифр → 5, и добавить вызов draw_score внутри
# ═══════════════════════════════════════════════════════════════
old = """    // Счёт в центре — 6 цифр
    char sbuf[8];
    for (int i = 0; i < 6; ++i) {
        sbuf[5 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    sbuf[6] = 0;
    draw_text(r, 340, 20, sbuf);"""

new = """    // Счёт в центре — 5 цифр
    char sbuf[8];
    for (int i = 0; i < 5; ++i) {
        sbuf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    sbuf[5] = 0;
    draw_text(r, 340, 20, sbuf);"""

if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: счёт 6 цифр → 5")
else:
    print("!! не найден блок 'Счёт в центре — 6 цифр'")

p.write_text(s)
print(f"\nИзменено блоков: {changes}")
