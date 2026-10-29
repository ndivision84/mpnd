#!/usr/bin/env python3
"""patch_28_difficulty_combined.py — полный выбор сложности (1/2/3).

Объединяет patch_26 и patch_27:
- AppState.difficulty = 1 (Normal)
- Клавиши 1/2/3 → difficulty + obstacle_spawn_interval (5/3/2 сек)
- ATTRACT: вертикальное меню "1. EASY / 2. NORMAL / 3. HARD"
- HUD (PLAYING): "DIFF: <name>" под TIME
- Space стартует с текущей выбранной сложности
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) AppState: int difficulty = 1
# ═══════════════════════════════════════════════════════════════
if 'difficulty' not in s:
    old = "    static constexpr int MAX_OBSTACLES_ACTIVE = 3;"
    new = """    static constexpr int MAX_OBSTACLES_ACTIVE = 3;
    int           difficulty = 1;   // 0=EASY, 1=NORMAL, 2=HARD"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: AppState.difficulty = 1 (Normal)")
    else:
        print("!! не найден 'MAX_OBSTACLES_ACTIVE = 3'")

# ═══════════════════════════════════════════════════════════════
# 2) SDL_AppEvent: SDLK_1/2/3
# ═══════════════════════════════════════════════════════════════
if 'SDLK_1' not in s:
    old = "    // ── Space на экранах ATTRACT / GAME_OVER / SCORE ──"
    new = """    // ── Выбор сложности: 1/2/3 (в любом состоянии) ──
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
    }

    // ── Space на экранах ATTRACT / GAME_OVER / SCORE ──"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: SDL_AppEvent + 1/2/3 (Easy/Normal/Hard)")
    else:
        print("!! не найден якорь 'Space на экранах ATTRACT'")

# ═══════════════════════════════════════════════════════════════
# 3) draw_hud: сигнатура + DIFF под TIME
# ═══════════════════════════════════════════════════════════════
old_sig = "static void draw_hud(SDL_Renderer* r, int score, int time_left, float world_x) {"
new_sig = "static void draw_hud(SDL_Renderer* r, int score, int time_left, float world_x, int difficulty) {"
if old_sig in s:
    s = s.replace(old_sig, new_sig, 1); changes += 1
    print("OK: draw_hud сигнатура (+ difficulty)")

if 'DIFF:' not in s:
    old = """    // TIME: XX — одна строка слева
    char tbuf[9];"""
    new = """    // DIFF под TIME
    {
        const char* diff_names[3] = { "EASY", "NORMAL", "HARD" };
        draw_text(r, 20, 100, "DIFF:", 3.0f);
        draw_text(r, 20, 128, diff_names[difficulty], 3.0f);
    }

    // TIME: XX — одна строка слева
    char tbuf[9];"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: draw_hud — DIFF под TIME")
    else:
        print("!! не найден блок 'TIME: XX' в draw_hud")

# ═══════════════════════════════════════════════════════════════
# 4) Вызов draw_hud с difficulty
# ═══════════════════════════════════════════════════════════════
old = "draw_hud(s->renderer, s->score, time_left, s->world_x);"
new = "draw_hud(s->renderer, s->score, time_left, s->world_x, s->difficulty);"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: вызов draw_hud (+ s->difficulty)")

# ═══════════════════════════════════════════════════════════════
# 5) ATTRACT: вертикальное меню
# ═══════════════════════════════════════════════════════════════
if '1. EASY' not in s:
    old = """            draw_text_centered(s->renderer, 420, "PRESS SPACE", 3.0f);
        } else if (s->state == STATE_GAME_OVER) {"""
    new = """            draw_text_centered(s->renderer, 420, "PRESS SPACE", 3.0f);

            // Меню выбора сложности — вертикально
            {
                const SDL_Color gc = { 0x00, 0xff, 0x00, 255 };
                const SDL_Color wc = { 0xff, 0xff, 0xff, 180 };
                const float menu_x = 320.0f;
                const float menu_y = 470.0f;
                const float step_y = 34.0f;

                SDL_Color c1 = (s->difficulty == 0) ? gc : wc;
                SDL_SetRenderDrawColor(s->renderer, c1.r, c1.g, c1.b, 255);
                draw_text(s->renderer, menu_x, menu_y, "1. EASY", 3.0f);

                SDL_Color c2 = (s->difficulty == 1) ? gc : wc;
                SDL_SetRenderDrawColor(s->renderer, c2.r, c2.g, c2.b, 255);
                draw_text(s->renderer, menu_x, menu_y + step_y, "2. NORMAL", 3.0f);

                SDL_Color c3 = (s->difficulty == 2) ? gc : wc;
                SDL_SetRenderDrawColor(s->renderer, c3.r, c3.g, c3.b, 255);
                draw_text(s->renderer, menu_x, menu_y + 2.0f * step_y, "3. HARD", 3.0f);
            }
        } else if (s->state == STATE_GAME_OVER) {"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: ATTRACT — вертикальное меню (1. EASY / 2. NORMAL / 3. HARD)")
    else:
        print("!! не найден 'PRESS SPACE' в ATTRACT")

p.write_text(s)
print(f"\nИзменено: {changes}/5")
