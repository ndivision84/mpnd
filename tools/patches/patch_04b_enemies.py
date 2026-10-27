#!/usr/bin/env python3
"""
patch_04b_enemies.py — враги, бомбы, счёт, game over (устойчивые якоря).

Применять к main.cpp после патчей 01 + 01b (Bullet расширен,
bullets[10], SDL_AppEvent — пара Z).

Добавляет:
  - struct Enemy, struct Bomb
  - AppState: enemies[5], bombs[5], score, game_over, таймеры, MAX_ENEMIES/BOMBS
  - glyphs + G, V, R
  - draw_text + G, V, R
  - draw_score, draw_game_over
  - SDL_AppEvent: R (restart), G (game over)
  - Спавн/движение/коллизии в SDL_AppIterate
  - Отрисовка тарелок, бомб, счёта, GAME OVER
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) struct Enemy + struct Bomb (перед struct Player)
# ═══════════════════════════════════════════════════════════════
if 'struct Enemy {' not in s:
    anchor = "struct Player {"
    insert = """struct Enemy {
    float x = 0.0f;
    float y = 0.0f;
    float dx = -120.0f;
    bool active = false;
};

struct Bomb {
    float x = 0.0f;
    float y = 0.0f;
    float dy = 200.0f;
    bool active = false;
};

struct Player {"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: struct Enemy + struct Bomb добавлены")
else:
    print("[i] struct Enemy уже есть, пропускаем")

# ═══════════════════════════════════════════════════════════════
# 2) AppState: enemies/bombs/score/game_over
# ═══════════════════════════════════════════════════════════════
if 'Enemy         enemies[' not in s:
    anchor = "    Bullet        bullets[10];"
    insert = """    Bullet        bullets[10];
    Enemy         enemies[5];
    Bomb          bombs[5];
    int           score = 0;
    bool          game_over = false;
    float         enemy_spawn_timer = 0.0f;
    float         bomb_spawn_timer = 0.0f;
    static constexpr int MAX_ENEMIES = 2;   // Normal
    static constexpr int MAX_BOMBS   = 3;   // Normal"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: AppState расширен (enemies, bombs, score, game_over)")
    else:
        print("!! не найден 'Bullet        bullets[10];' в AppState")
else:
    print("[i] AppState уже расширен")

# ═══════════════════════════════════════════════════════════════
# 3) glyphs + G, V, R (после '// O' и перед `};`)
# ═══════════════════════════════════════════════════════════════
if '20' not in s or '// G' not in s:
    anchor = """        {0x7,0x5,0x7,0x5,0x7}, // O
    };"""
    insert = """        {0x7,0x5,0x7,0x5,0x7}, // O
        {0x7,0x4,0x5,0x5,0x7}, // G
        {0x5,0x5,0x5,0x2,0x0}, // V
        {0x6,0x5,0x6,0x5,0x5}, // R
    };"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: glyphs + G, V, R")
    else:
        print("!! не найден конец glyphs")
else:
    print("[i] glyphs уже расширены")

# ═══════════════════════════════════════════════════════════════
# 4) draw_text + G, V, R
# ═══════════════════════════════════════════════════════════════
if "*p == 'G'" not in s:
    anchor = "        else if (*p == 'O') code = 19;"
    insert = """        else if (*p == 'O') code = 19;
        else if (*p == 'G') code = 20;
        else if (*p == 'V') code = 21;
        else if (*p == 'R') code = 22;"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: draw_text + G, V, R")
    else:
        print("!! не найден 'else if (*p == 'O') code = 19;'")
else:
    print("[i] draw_text уже расширен")

# ═══════════════════════════════════════════════════════════════
# 5) draw_score + draw_game_over (после закрывающей } draw_hud)
# ═══════════════════════════════════════════════════════════════
if 'draw_score' not in s:
    anchor = """    if (((int)(world_x * 2) / 1) % 2 == 0) {
        draw_text(r, 640, 20, "CAUTION");
    }
}"""
    insert = anchor + """

static void draw_score(SDL_Renderer* r, int score) {
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
    char buf[6];
    if (score > 99999) score = 99999;
    for (int i = 0; i < 5; ++i) {
        buf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    buf[5] = 0;
    draw_text(r, 700, 15, buf);
}

static void draw_game_over(SDL_Renderer* r) {
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(r, 0, 0, 0, 200);
    SDL_FRect bg = { 0, 0, 800, 600 };
    SDL_RenderFillRect(r, &bg);
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_NONE);

    SDL_SetRenderDrawColor(r, 255, 50, 50, 255);
    draw_text(r, 260, 220, "GAME");
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
    draw_text(r, 260, 280, "OVER");
    SDL_SetRenderDrawColor(r, 200, 200, 200, 255);
    draw_text(r, 280, 380, "PRESS R");
}"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: draw_score + draw_game_over добавлены")
    else:
        print("!! не найден конец draw_hud")
else:
    print("[i] draw_score уже есть")

# ═══════════════════════════════════════════════════════════════
# 6) SDL_AppEvent — полная замена через regex (R, G, Z=пара)
# ═══════════════════════════════════════════════════════════════
pattern = r'SDL_AppResult SDL_AppEvent\(void\* appstate, SDL_Event\* e\) \{.*?\n\}'
new_func = '''SDL_AppResult SDL_AppEvent(void* appstate, SDL_Event* e) {
    auto* s = static_cast<AppState*>(appstate);
    if (e->type == SDL_EVENT_QUIT) return SDL_APP_SUCCESS;
    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;

    // R — restart
    if (e->key.key == SDLK_R) {
        s->game_over = false;
        s->score = 0;
        s->player.y = 420.0f;
        s->player.vy = 0.0f;
        s->player.offset_x = 0.0f;
        s->player.on_ground = true;
        for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
        for (int i = 0; i < 5; ++i) { s->enemies[i].active = false; s->bombs[i].active = false; }
        return SDL_APP_CONTINUE;
    }
    // G — game over (отладка)
    if (e->key.key == SDLK_G) {
        s->game_over = true;
        return SDL_APP_CONTINUE;
    }
    if (s->game_over) return SDL_APP_CONTINUE;
    if (e->key.key != SDLK_Z) return SDL_APP_CONTINUE;

    float sx = s->player.screen_x + s->player.offset_x;
    float sy = s->player.y;

    for (int i = 0; i < 5; ++i) {
        if (!s->bullets[i].active) {
            s->bullets[i].x    = sx + 24;
            s->bullets[i].y    = sy - 24;
            s->bullets[i].dx   = 600.0f;
            s->bullets[i].dy   = 0.0f;
            s->bullets[i].life = 0.9f;
            s->bullets[i].active = true;
            break;
        }
    }
    for (int i = 5; i < 10; ++i) {
        if (!s->bullets[i].active) {
            s->bullets[i].x    = sx + 16;
            s->bullets[i].y    = sy - 40;
            s->bullets[i].dx   = 0.0f;
            s->bullets[i].dy   = -500.0f;
            s->bullets[i].life = 0.9f;
            s->bullets[i].active = true;
            break;
        }
    }
    return SDL_APP_CONTINUE;
}'''

new_s, n = re.subn(pattern, new_func, s, count=1, flags=re.DOTALL)
if n == 1:
    s = new_s; changes += 1
    print("OK: SDL_AppEvent перезаписан (R, G, Z=пара)")
else:
    print("!! SDL_AppEvent не найден через regex")

# ═══════════════════════════════════════════════════════════════
# 7) Спавн/движение/коллизии перед SDL_SetRenderDrawColor (в SDL_AppIterate)
# ═══════════════════════════════════════════════════════════════
if 'enemy_spawn_timer +=' not in s:
    anchor = "    SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);"
    insert = """    // ── Спавн тарелок (макс 2) ──
    if (!s->game_over) {
        s->enemy_spawn_timer += dt;
        if (s->enemy_spawn_timer > 2.5f) {
            s->enemy_spawn_timer = 0.0f;
            int cnt = 0;
            for (int i = 0; i < 5; ++i) if (s->enemies[i].active) cnt++;
            if (cnt < AppState::MAX_ENEMIES) {
                for (int i = 0; i < 5; ++i) {
                    if (!s->enemies[i].active) {
                        s->enemies[i].x = 830.0f;
                        s->enemies[i].y = 260.0f + (float)(rand() % 120);
                        s->enemies[i].dx = -120.0f;
                        s->enemies[i].active = true;
                        break;
                    }
                }
            }
        }
        // ── Спавн бомб (макс 3) ──
        s->bomb_spawn_timer += dt;
        if (s->bomb_spawn_timer > 3.0f) {
            s->bomb_spawn_timer = 0.0f;
            int cnt = 0;
            for (int i = 0; i < 5; ++i) if (s->bombs[i].active) cnt++;
            if (cnt < AppState::MAX_BOMBS) {
                for (int i = 0; i < 5; ++i) {
                    if (!s->bombs[i].active) {
                        s->bombs[i].x = s->player.screen_x + s->player.offset_x
                                        + (float)(rand() % 400 - 200);
                        if (s->bombs[i].x < 40)  s->bombs[i].x = 40;
                        if (s->bombs[i].x > 760) s->bombs[i].x = 760;
                        s->bombs[i].y = 100.0f;
                        s->bombs[i].dy = 200.0f;
                        s->bombs[i].active = true;
                        break;
                    }
                }
            }
        }
    }

    // ── Обновление тарелок ──
    for (int i = 0; i < 5; ++i) {
        if (s->enemies[i].active) {
            s->enemies[i].x += s->enemies[i].dx * dt;
            if (s->enemies[i].x < -40) s->enemies[i].active = false;
        }
    }
    // ── Обновление бомб ──
    for (int i = 0; i < 5; ++i) {
        if (s->bombs[i].active) {
            s->bombs[i].y += s->bombs[i].dy * dt;
            if (s->bombs[i].y > 620) s->bombs[i].active = false;
        }
    }
    // ── Коллизии: гориз. пули × тарелки ──
    for (int b = 0; b < 5; ++b) {
        if (!s->bullets[b].active) continue;
        for (int e = 0; e < 5; ++e) {
            if (!s->enemies[e].active) continue;
            if (fabs(s->bullets[b].x - s->enemies[e].x) < 24 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 16) {
                s->enemies[e].active = false;
                s->bullets[b].active = false;
                s->score += 100;
                if (s->score > 99999) s->score = 99999;
                break;
            }
        }
    }
    // ── Коллизии: верт. пули × бомбы ──
    for (int b = 5; b < 10; ++b) {
        if (!s->bullets[b].active) continue;
        for (int bo = 0; bo < 5; ++bo) {
            if (!s->bombs[bo].active) continue;
            if (fabs(s->bullets[b].x - s->bombs[bo].x) < 16 &&
                fabs(s->bullets[b].y - s->bombs[bo].y) < 20) {
                s->bombs[bo].active = false;
                s->bullets[b].active = false;
                s->score += 50;
                if (s->score > 99999) s->score = 99999;
                break;
            }
        }
    }
    // ── Коллизии: враги/бомбы × луноход → game over ──
    if (!s->game_over) {
        float px = s->player.screen_x + s->player.offset_x;
        float py = s->player.y;
        for (int e = 0; e < 5; ++e) {
            if (s->enemies[e].active &&
                fabs(px - s->enemies[e].x) < 32 &&
                fabs(py - s->enemies[e].y) < 32) {
                s->game_over = true;
            }
        }
        for (int bo = 0; bo < 5; ++bo) {
            if (s->bombs[bo].active &&
                fabs(px - s->bombs[bo].x) < 28 &&
                fabs(py - s->bombs[bo].y) < 32) {
                s->game_over = true;
            }
        }
    }

    SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: спавн + движение + коллизии")
    else:
        print("!! не найден якорь SDL_SetRenderDrawColor в Iterate")
else:
    print("[i] спавн уже есть")

# ═══════════════════════════════════════════════════════════════
# 8) Отрисовка тарелок/бомб/счёта/game_over перед SDL_RenderPresent
# ═══════════════════════════════════════════════════════════════
if 'draw_score(s->renderer' not in s:
    anchor = "    SDL_RenderPresent(s->renderer);"
    insert = """    // ── Отрисовка тарелок ──
    for (int e = 0; e < 5; ++e) {
        if (!s->enemies[e].active) continue;
        float ex = s->enemies[e].x, ey = s->enemies[e].y;
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xD7, 0x00, 255);
        SDL_FRect body = { ex - 16, ey - 4, 32, 8 };
        SDL_RenderFillRect(s->renderer, &body);
        SDL_FRect dome = { ex - 8, ey - 10, 16, 6 };
        SDL_RenderFillRect(s->renderer, &dome);
        SDL_SetRenderDrawColor(s->renderer, 0xCC, 0x66, 0x00, 255);
        SDL_FRect rim = { ex - 18, ey + 2, 36, 3 };
        SDL_RenderFillRect(s->renderer, &rim);
    }
    // ── Отрисовка бомб ──
    for (int bo = 0; bo < 5; ++bo) {
        if (!s->bombs[bo].active) continue;
        float bx = s->bombs[bo].x, by = s->bombs[bo].y;
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x30, 0x30, 255);
        SDL_FRect c1 = { bx - 4, by - 4, 8, 8 };   SDL_RenderFillRect(s->renderer, &c1);
        SDL_FRect c2 = { bx - 6, by - 2, 12, 4 };  SDL_RenderFillRect(s->renderer, &c2);
        SDL_FRect c3 = { bx - 2, by - 6, 4, 12 };  SDL_RenderFillRect(s->renderer, &c3);
    }
    // ── Счёт ──
    draw_score(s->renderer, s->score);
    // ── GAME OVER ──
    if (s->game_over) {
        draw_game_over(s->renderer);
    }

    SDL_RenderPresent(s->renderer);"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: отрисовка тарелок, бомб, счёта, GAME OVER")
    else:
        print("!! не найден SDL_RenderPresent")

p.write_text(s)
print(f"\nИзменено: {changes}/8")
