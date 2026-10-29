#!/usr/bin/env python3
"""patch_29_hud_mode_start.py

A) HUD: CAUTION → "MODE: EASY/NORMAL/HARD" (right-aligned, scale 4).
B) ATTRACT: клавиши 1/2/3 стартуют игру немедленно. Space → NORMAL.
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# A) Заменить CAUTION на MODE в draw_hud
# ═══════════════════════════════════════════════════════════════
old = """    // CAUTION справа — статично, right-aligned (не вылезает за край)
    const float cw = 7 * 6.0f * 4.0f;   // width of "CAUTION" at scale 4
    draw_text(r, 800.0f - cw - 20.0f, 20, "CAUTION", 4.0f);"""

new = """    // MODE: <name> справа — right-aligned (вместо CAUTION)
    const char* mode_str = (difficulty == 0) ? "MODE: EASY" :
                           (difficulty == 2) ? "MODE: HARD" : "MODE: NORMAL";
    int nlen = 0;
    while (mode_str[nlen]) nlen++;
    const float cw = nlen * 6.0f * 4.0f;
    draw_text(r, 800.0f - cw - 20.0f, 20, mode_str, 4.0f);"""

if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK (A): CAUTION → MODE: EASY/NORMAL/HARD")
else:
    print("!! (A): не найден блок CAUTION")

# ═══════════════════════════════════════════════════════════════
# B1) 1/2/3 — старт немедленно на ATTRACT
# ═══════════════════════════════════════════════════════════════
old_diff = """    // ── Выбор сложности: 1/2/3 (в любом состоянии) ──
    if (e->key.key == SDLK_1) {
        s->difficulty = 0;
        s->obstacle_spawn_interval = 5.0f;
        SDL_Log("Difficulty: EASY (5s)");
        return SDL_APP_CONTINUE;
    }
    if (e->key.key == SDLK_2) {
        s->difficulty = 1;
        s->obstacle_spawn_interval = 3.0f;
        SDL_Log("Difficulty: NORMAL (3s)");
        return SDL_APP_CONTINUE;
    }
    if (e->key.key == SDLK_3) {
        s->difficulty = 2;
        s->obstacle_spawn_interval = 2.0f;
        SDL_Log("Difficulty: HARD (2s)");
        return SDL_APP_CONTINUE;
    }"""

new_diff = """    // ── Выбор сложности: 1/2/3 ──
    // На ATTRACT: старт игры немедленно. В PLAYING: только смена сложности.
    int start_diff = -1;
    float start_interval = 0.0f;
    if (e->key.key == SDLK_1) { start_diff = 0; start_interval = 5.0f; }
    else if (e->key.key == SDLK_2) { start_diff = 1; start_interval = 3.0f; }
    else if (e->key.key == SDLK_3) { start_diff = 2; start_interval = 2.0f; }

    if (start_diff >= 0) {
        s->difficulty = start_diff;
        s->obstacle_spawn_interval = start_interval;
        const char* nm[3] = { "EASY", "NORMAL", "HARD" };
        SDL_Log("Difficulty: %s (%.1fs)", nm[start_diff], start_interval);

        if (s->state == STATE_ATTRACT) {
            s->score = 0;
            s->player.y = 420.0f;
            s->player.vy = 0.0f;
            s->player.offset_x = 0.0f;
            s->player.on_ground = true;
            for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
            for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
            for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
            s->obstacle_spawn_timer = 0.0f;
            s->play_time = 0.0f;
            s->state = STATE_PLAYING;
            SDL_Log("START: %s (immediate)", nm[start_diff]);
        }
        return SDL_APP_CONTINUE;
    }"""

if old_diff in s:
    s = s.replace(old_diff, new_diff, 1); changes += 1
    print("OK (B1): 1/2/3 стартуют игру немедленно на ATTRACT")
else:
    print("!! (B1): не найден блок 'Выбор сложности: 1/2/3'")

# ═══════════════════════════════════════════════════════════════
# B2) Space на ATTRACT → force NORMAL
# ═══════════════════════════════════════════════════════════════
old_space = """            // ATTRACT или SCORE → старт игры
            s->score = 0;
            s->player.y = 420.0f;
            s->player.vy = 0.0f;
            s->player.offset_x = 0.0f;
            s->player.on_ground = true;
            for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
            for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
            for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
            s->obstacle_spawn_timer = 0.0f;
            s->play_time = 0.0f;
            s->state = STATE_PLAYING;
            return SDL_APP_CONTINUE;"""

new_space = """            // ATTRACT: force NORMAL. SCORE: продолжить с последней сложности.
            if (s->state == STATE_ATTRACT) {
                s->difficulty = 1;
                s->obstacle_spawn_interval = 3.0f;
                SDL_Log("START: NORMAL (Space)");
            }
            s->score = 0;
            s->player.y = 420.0f;
            s->player.vy = 0.0f;
            s->player.offset_x = 0.0f;
            s->player.on_ground = true;
            for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
            for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
            for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
            s->obstacle_spawn_timer = 0.0f;
            s->play_time = 0.0f;
            s->state = STATE_PLAYING;
            return SDL_APP_CONTINUE;"""

if old_space in s:
    s = s.replace(old_space, new_space, 1); changes += 1
    print("OK (B2): Space на ATTRACT → force NORMAL")
else:
    print("!! (B2): не найден блок 'ATTRACT или SCORE → старт игры'")

p.write_text(s)
print(f"\nИзменено: {changes}/3")
