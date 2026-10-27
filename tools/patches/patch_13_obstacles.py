#!/usr/bin/env python3
"""patch_13_obstacles.py

Процедурные препятствия: яма / камень / кратер / ничего.
- Интервал спавна: 5.0f (Normal); для Easy=7.0f, Hard=3.0f — менять эту константу.
- Ширина: яма 48, камень 24, кратер 64 (макс < 80 = прыжок).
- 35% «ничего», 25% яма, 20% камень, 20% кратер.
- Спавн: world_x + 850 (за правым краем).
- Удаление: sx < -100.
- Коллизия: яма/кратер → on_ground = смерть; камень → y > 380 = смерть.
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) struct Obstacle — после struct BOMBA
# ═══════════════════════════════════════════════════════════════
if 'struct Obstacle {' not in s:
    old = """struct BOMBA {
    float x = 0.0f;
    float y = 0.0f;
    float dy = 200.0f;
    bool active = false;
};"""
    new = old + """

struct Obstacle {
    float world_x = 0.0f;
    float width = 48.0f;
    int   type = 0;       // 0 = яма, 1 = камень, 2 = кратер
    bool  active = false;
};"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: struct Obstacle добавлен")

# ═══════════════════════════════════════════════════════════════
# 2) AppState: obstacles[8] + таймер + интервал
# ═══════════════════════════════════════════════════════════════
if 'Obstacle      obstacles[' not in s:
    old = "    Star          stars[120];"
    new = """    Star          stars[120];
    Obstacle      obstacles[8];
    float         obstacle_spawn_timer = 0.0f;
    float         obstacle_spawn_interval = 5.0f;   // Normal; Hard=3, Easy=7"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: AppState — obstacles + таймер + интервал")

# ═══════════════════════════════════════════════════════════════
# 3) Restart (R) — очистка obstacles
# ═══════════════════════════════════════════════════════════════
old = "        for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }"
new = """        for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
        for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
        s->obstacle_spawn_timer = 0.0f;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: R — очистка obstacles")

# ═══════════════════════════════════════════════════════════════
# 4) Spawn — перед блоком «Спавн тарелок (макс 2)»
# ═══════════════════════════════════════════════════════════════
anchor_spawn = "    // ── Спавн тарелок (макс 2) ──"
if anchor_spawn in s:
    insert = """    // ── Спавн препятствий (каждые obstacle_spawn_interval сек) ──
    if (!s->game_over && !s->paused) {
        s->obstacle_spawn_timer += dt;
        if (s->obstacle_spawn_timer >= s->obstacle_spawn_interval) {
            s->obstacle_spawn_timer = 0.0f;
            for (int i = 0; i < 8; ++i) {
                if (!s->obstacles[i].active) {
                    int r = rand() % 100;
                    int type = -1;
                    float w = 0.0f;
                    if      (r < 35) { type = -1; }                  // 35% ничего
                    else if (r < 60) { type = 0; w = 48.0f; }        // 25% яма
                    else if (r < 80) { type = 1; w = 24.0f; }        // 20% камень
                    else             { type = 2; w = 64.0f; }        // 20% кратер

                    if (type >= 0) {
                        s->obstacles[i].world_x = s->world_x + 850.0f;
                        s->obstacles[i].width = w;
                        s->obstacles[i].type = type;
                        s->obstacles[i].active = true;
                        SDL_Log("Obstacle: type=%d width=%d", type, (int)w);
                    }
                    break;
                }
            }
        }
    }

    // ── Спавн тарелок (макс 2) ──"""
    s = s.replace(anchor_spawn, insert, 1); changes += 1
    print("OK: spawn obstacles")
else:
    print("!! не найден '// ── Спавн тарелок (макс 2) ──'")

# ═══════════════════════════════════════════════════════════════
# 5) Update + collision — перед «Обновление тарелок»
# ═══════════════════════════════════════════════════════════════
anchor_update = "    // ── Обновление тарелок ──"
if anchor_update in s:
    insert = """    // ── Обновление/удаление препятствий + коллизии ──
    for (int i = 0; i < 8; ++i) {
        if (!s->obstacles[i].active) continue;
        float sx = s->obstacles[i].world_x - s->world_x;
        if (sx < -100) { s->obstacles[i].active = false; continue; }

        if (!s->game_over) {
            float px = s->player.screen_x + s->player.offset_x;
            float left  = sx;
            float right = sx + s->obstacles[i].width;
            bool h_overlap = (px + 24 > left) && (px - 24 < right);

            if (h_overlap) {
                if (s->obstacles[i].type == 0 && s->player.on_ground) {
                    s->game_over = true;
                    SDL_Log("Fell into PIT!");
                } else if (s->obstacles[i].type == 1 && s->player.y > 380.0f) {
                    s->game_over = true;
                    SDL_Log("Hit ROCK!");
                } else if (s->obstacles[i].type == 2 && s->player.on_ground) {
                    s->game_over = true;
                    SDL_Log("Fell into CRATER!");
                }
            }
        }
    }

    // ── Обновление тарелок ──"""
    s = s.replace(anchor_update, insert, 1); changes += 1
    print("OK: update + collision obstacles")
else:
    print("!! не найден '// ── Обновление тарелок ──'")

# ═══════════════════════════════════════════════════════════════
# 6) Render obstacles — перед «Отрисовка тарелок»
# ═══════════════════════════════════════════════════════════════
anchor_render = "    // ── Отрисовка тарелок"
if anchor_render in s:
    insert = """    // ── Отрисовка препятствий ──
    for (int i = 0; i < 8; ++i) {
        if (!s->obstacles[i].active) continue;
        float sx = s->obstacles[i].world_x - s->world_x;
        if (sx < -100 || sx > 900) continue;
        float w = s->obstacles[i].width;

        if (s->obstacles[i].type == 0) {
            // ЯМА — чёрный прямоугольник на земле
            SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
            SDL_FRect pit = { sx, 420.0f, w, 40.0f };
            SDL_RenderFillRect(s->renderer, &pit);
            SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0xFF, 255);
            SDL_FRect top = { sx, 420.0f, w, 2.0f };
            SDL_RenderFillRect(s->renderer, &top);
        } else if (s->obstacles[i].type == 1) {
            // КАМЕНЬ — серый + чёрный верх
            SDL_SetRenderDrawColor(s->renderer, 0x80, 0x80, 0x80, 255);
            SDL_FRect rock = { sx, 400.0f, w, 20.0f };
            SDL_RenderFillRect(s->renderer, &rock);
            SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
            SDL_FRect rock_top = { sx, 400.0f, w, 2.0f };
            SDL_RenderFillRect(s->renderer, &rock_top);
        } else {
            // КРАТЕР — чёрный + огненная окантовка
            SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
            SDL_FRect crater = { sx, 420.0f, w, 50.0f };
            SDL_RenderFillRect(s->renderer, &crater);
            SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x30, 0x00, 255);
            SDL_FRect t =  { sx, 420.0f, w, 3.0f };             SDL_RenderFillRect(s->renderer, &t);
            SDL_FRect b2 = { sx, 467.0f, w, 3.0f };             SDL_RenderFillRect(s->renderer, &b2);
            SDL_FRect l  = { sx, 420.0f, 3.0f, 50.0f };         SDL_RenderFillRect(s->renderer, &l);
            SDL_FRect r  = { sx + w - 3, 420.0f, 3.0f, 50.0f }; SDL_RenderFillRect(s->renderer, &r);
        }
    }

    // ── Отрисовка тарелок"""
    s = s.replace(anchor_render, insert, 1); changes += 1
    print("OK: render obstacles")
else:
    print("!! не найден '// ── Отрисовка тарелок'")

p.write_text(s)
print(f"\nИзменено: {changes}/6")
