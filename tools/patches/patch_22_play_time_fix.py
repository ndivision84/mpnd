#!/usr/bin/env python3
"""patch_22_play_time_fix.py — сброс play_time при старте новой игры."""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) Space на ATTRACT/SCORE → PLAYING (сброс play_time)
old = """            s->obstacle_spawn_timer = 0.0f;
            s->state = STATE_PLAYING;"""
new = """            s->obstacle_spawn_timer = 0.0f;
            s->play_time = 0.0f;
            s->state = STATE_PLAYING;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: play_time = 0 при старте игры (Space)")
else:
    print("!! не найден блок 'obstacle_spawn_timer = 0; state = PLAYING'")

# 2) R — restart (сброс play_time)
old = """        s->state = STATE_PLAYING;
        s->score = 0;
        s->player.y = 420.0f;"""
new = """        s->state = STATE_PLAYING;
        s->score = 0;
        s->play_time = 0.0f;
        s->player.y = 420.0f;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: play_time = 0 при R (restart)")
else:
    print("!! не найден блок 'state = PLAYING; score = 0; player.y = 420'")

# 3) Лог при time_left == 0 (для диагностики)
old = """    if (time_left == 0) {
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
    }"""
new = """    if (time_left == 0) {
        SDL_Log("TIME UP! play_time=%.1f -> GAME_OVER", s->play_time);
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
    }"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: SDL_Log при time_left == 0")

p.write_text(s)
print(f"\nИзменено: {changes}/3")
