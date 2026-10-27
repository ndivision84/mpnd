#!/usr/bin/env python3
"""
patch_02_split_fire.py

Разделяет стрельбу на две кнопки:
  - Z → горизонтальная (слоты 0..4)
  - X → вертикальная (слоты 5..9)

Одно нажатие = одна пуля (не пара).

Применять ПОСЛЕ patch_01_bullets_extended.py.
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

old = """    if (e->type == SDL_EVENT_KEY_DOWN && e->key.key == SDLK_Z) {
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
    }"""

new = """    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;

    float sx = s->player.screen_x + s->player.offset_x;
    float sy = s->player.y;

    if (e->key.key == SDLK_Z) {
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
    }
    else if (e->key.key == SDLK_X) {
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
    }"""

if old in s:
    p.write_text(s.replace(old, new, 1))
    print("OK: Z → горизонтальная, X → вертикальная")
else:
    print("!! не найден блок — патч 02 ожидает результат патча 01")
