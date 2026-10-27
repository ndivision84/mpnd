#!/usr/bin/env python3
"""patch_19_ui_states.py

Три экрана:
- ATTRACT: звёзды + "MOON PATROL ND" зелёным, Space → PLAYING
- GAME_OVER: звёзды + "GAME OVER" красным, Space/3s → SCORE
- SCORE: звёзды + "SCORE" + счёт крупным (scale 10), Space → PLAYING

Заменяет bool game_over на enum GameState.
Добавляет глифы L (24) и D (25) для "MOON PATROL ND".
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) enum GameState перед struct AppState
# ═══════════════════════════════════════════════════════════════
if 'enum GameState' not in s:
    old = "struct AppState {"
    new = """enum GameState {
    STATE_ATTRACT   = 0,
    STATE_PLAYING   = 1,
    STATE_GAME_OVER = 2,
    STATE_SCORE     = 3
};

struct AppState {"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: enum GameState")

# ═══════════════════════════════════════════════════════════════
# 2) bool game_over → GameState state + state_timer
# ═══════════════════════════════════════════════════════════════
old = "    bool          game_over = false;"
new = """    GameState     state = STATE_ATTRACT;
    float         state_timer = 0.0f;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: state = STATE_ATTRACT")

# ═══════════════════════════════════════════════════════════════
# 3) Глифы L (24) и D (25) после R (22)
# ═══════════════════════════════════════════════════════════════
if "// P (23)" in s and "// L (24)" not in s:
    old = "{0x7,0x4,0x7,0x4,0x4}, // P (23)"
    new = """{0x7,0x4,0x7,0x4,0x4}, // P (23)
        {0x4,0x4,0x4,0x4,0x7}, // L (24)
        {0x6,0x5,0x5,0x5,0x6}, // D (25)"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: глифы L (24), D (25)")

# ═══════════════════════════════════════════════════════════════
# 4) draw_text: добавить 'L' и 'D'
# ═══════════════════════════════════════════════════════════════
if "*p == 'P') code = 23" in s and "*p == 'L') code = 24" not in s:
    old = "else if (*p == 'P') code = 23;"
    new = """else if (*p == 'P') code = 23;
        else if (*p == 'L') code = 24;
        else if (*p == 'D') code = 25;"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: draw_text + L (24), D (25)")

# ═══════════════════════════════════════════════════════════════
# 5) bounds 23 → 25
# ═══════════════════════════════════════════════════════════════
n = s.count("if (code < 0 || code > 23) return;")
if n:
    s = s.replace("if (code < 0 || code > 23) return;", "if (code < 0 || code > 25) return;")
    changes += 1
    print(f"OK: bounds 23 → 25 ({n} мест)")

# ═══════════════════════════════════════════════════════════════
# 6) SDL_AppEvent: добавить обработку Space по state
# ═══════════════════════════════════════════════════════════════
if 'STATE_ATTRACT && e->key.key == SDLK_SPACE' not in s:
    old = """    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;

    // R — restart"""
    new = """    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;

    // ── Space на экранах ATTRACT / GAME_OVER / SCORE ──
    if (e->key.key == SDLK_SPACE) {
        if (s->state == STATE_ATTRACT || s->state == STATE_GAME_OVER || s->state == STATE_SCORE) {
            if (s->state == STATE_GAME_OVER) {
                s->state = STATE_SCORE;
                s->state_timer = 0.0f;
                return SDL_APP_CONTINUE;
            }
            // ATTRACT или SCORE → старт игры
            s->score = 0;
            s->player.y = 420.0f;
            s->player.vy = 0.0f;
            s->player.offset_x = 0.0f;
            s->player.on_ground = true;
            for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
            for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
            for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
            s->obstacle_spawn_timer = 0.0f;
            s->state = STATE_PLAYING;
            return SDL_APP_CONTINUE;
        }
        // PLAYING → стрельба (ниже, существующая логика)
    }

    // R — restart"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: Space по state в SDL_AppEvent")
    else:
        print("!! не найден 'R — restart' в SDL_AppEvent")

# ═══════════════════════════════════════════════════════════════
# 7) Заменить все s->game_over на проверки state (если остались)
# ═══════════════════════════════════════════════════════════════
n = s.count('s->game_over')
if n:
    s = s.replace('s->game_over = true;', 's->state = STATE_GAME_OVER; s->state_timer = 0.0f;')
    s = s.replace('s->game_over = false;', 's->state = STATE_PLAYING;')
    s = s.replace('if (!s->game_over)', 'if (s->state == STATE_PLAYING)')
    s = s.replace('if (s->game_over)', 'if (s->state == STATE_GAME_OVER)')
    s = s.replace('s->game_over', '(s->state == STATE_GAME_OVER)')
    changes += 1
    print(f"OK: s->game_over → state-проверки ({n} мест)")

# ═══════════════════════════════════════════════════════════════
# 8) SDL_AppIterate: рендер 3 экранов + переход GAME_OVER → SCORE
# ═══════════════════════════════════════════════════════════════
if 'if (s->state != STATE_PLAYING)' not in s:
    old = """    SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
    SDL_RenderClear(s->renderer);"""

    new = """    SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
    SDL_RenderClear(s->renderer);

    // ── Переход GAME_OVER → SCORE по таймеру (3 сек) ──
    if (s->state == STATE_GAME_OVER) {
        s->state_timer += dt;
        if (s->state_timer >= 3.0f) {
            s->state = STATE_SCORE;
            s->state_timer = 0.0f;
        }
    }

    // ── Экраны ATTRACT / GAME_OVER / SCORE ──
    if (s->state != STATE_PLAYING) {
        // Звёзды
        {
            constexpr float STAR_PARALLAX = 0.05f;
            float star_scroll = std::fmod(s->world_x * STAR_PARALLAX, 800.0f);
            for (int i = 0; i < 120; ++i) {
                float sx = s->stars[i].x - star_scroll;
                if (sx < 0) sx += 800.0f;
                SDL_SetRenderDrawColor(s->renderer,
                                       s->stars[i].brightness,
                                       s->stars[i].brightness,
                                       s->stars[i].brightness,
                                       255);
                SDL_FRect r = { sx, s->stars[i].y, 2, 2 };
                SDL_RenderFillRect(s->renderer, &r);
            }
        }

        if (s->state == STATE_ATTRACT) {
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
            draw_text(s->renderer, 44, 250, "MOON PATROL ND", 8.0f);
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 180);
            draw_text(s->renderer, 280, 400, "PRESS SPACE", 3.0f);
        } else if (s->state == STATE_GAME_OVER) {
            SDL_SetRenderDrawColor(s->renderer, 0xff, 0x30, 0x30, 255);
            draw_text(s->renderer, 200, 260, "GAME OVER", 7.0f);
            SDL_SetRenderDrawColor(s->renderer, 0xff, 0xff, 0xff, 180);
            draw_text(s->renderer, 280, 420, "PRESS SPACE", 3.0f);
        } else if (s->state == STATE_SCORE) {
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
            draw_text(s->renderer, 300, 160, "SCORE", 5.0f);

            char score_buf[8];
            int sc = s->score > 99999 ? 99999 : s->score;
            for (int i = 0; i < 5; ++i) {
                score_buf[4 - i] = '0' + ((sc / (int)std::pow(10, i)) % 10);
            }
            score_buf[5] = 0;
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
            draw_text(s->renderer, 240, 300, score_buf, 10.0f);

            SDL_SetRenderDrawColor(s->renderer, 0xff, 0xff, 0xff, 180);
            draw_text(s->renderer, 280, 500, "PRESS SPACE", 3.0f);
        }

        SDL_RenderPresent(s->renderer);
        return SDL_APP_CONTINUE;
    }"""

    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: рендер трёх экранов + timer")
    else:
        print("!! не найден SDL_RenderClear в Iterate")

# ═══════════════════════════════════════════════════════════════
# 9) Убрать старый вызов draw_game_over (если остался)
# ═══════════════════════════════════════════════════════════════
if 'draw_game_over(s->renderer);' in s:
    s = s.replace('        draw_game_over(s->renderer);', '        // GAME OVER рендер вынесен выше')
    changes += 1
    print("OK: старый draw_game_over отключён")

p.write_text(s)
print(f"\nИзменено блоков: {changes}")
