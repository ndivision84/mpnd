#!/usr/bin/env python3
"""
patch_01_bullets_extended.py

Расширяет стрельбу:
  - Bullet: добавлены dx, dy, life
  - bullets[3] → bullets[10] (0-4 горизонтальные, 5-9 вертикальные)
  - Z спавнит ПАРУ: одна горизонтальная (вправо) + одна вертикальная (вверх)
  - Пули ограничены life=0.9s + границы x>750, y<40

Применять к clean main.cpp, где была базовая стрельба (Z, bullets[3]).
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) Bullet: расширить
old = """struct Bullet {
    float x = 0.0f;
    float y = 0.0f;
    bool active = false;
};"""
new = """struct Bullet {
    float x = 0.0f;
    float y = 0.0f;
    float dx = 0.0f;
    float dy = 0.0f;
    float life = 0.0f;
    bool active = false;
};"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: Bullet расширен (dx, dy, life)")

# 2) Массив 3 → 10
old = "    Bullet        bullets[3];"
new = "    Bullet        bullets[10];   // 0-4: горизонтальные, 5-9: вертикальные"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: bullets[3] → bullets[10]")

# 3) SDL_AppEvent: Z спавнит пару
old = """SDL_AppResult SDL_AppEvent(void* appstate, SDL_Event* e) {
    auto* s = static_cast<AppState*>(appstate);
    if (e->type == SDL_EVENT_QUIT) return SDL_APP_SUCCESS;
    if (e->type == SDL_EVENT_KEY_DOWN && e->key.key == SDLK_Z) {
        float sx = s->player.screen_x + s->player.offset_x;
        float sy = s->player.y;

        for (int i = 0; i < 3; ++i) {
            if (!s->bullets[i].active) {
                s->bullets[i].x = sx + 24;
                s->bullets[i].y = sy - 24;
                s->bullets[i].active = true;
                break;
            }
        }
    }
    return SDL_APP_CONTINUE;
}"""
new = """SDL_AppResult SDL_AppEvent(void* appstate, SDL_Event* e) {
    auto* s = static_cast<AppState*>(appstate);
    if (e->type == SDL_EVENT_QUIT) return SDL_APP_SUCCESS;
    if (e->type == SDL_EVENT_KEY_DOWN && e->key.key == SDLK_Z) {
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
    }
    return SDL_APP_CONTINUE;
}"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: Z → пара (горизонтальная + вертикальная)")

# 4) Обновление пуль
old = """    for (int i = 0; i < 3; ++i) {
        if (s->bullets[i].active) {
            s->bullets[i].x += 600.0f * dt;
            if (s->bullets[i].x > 820) s->bullets[i].active = false;
        }
    }"""
new = """    for (int i = 0; i < 10; ++i) {
        if (s->bullets[i].active) {
            s->bullets[i].x += s->bullets[i].dx * dt;
            s->bullets[i].y += s->bullets[i].dy * dt;
            s->bullets[i].life -= dt;
            if (s->bullets[i].life <= 0.0f
                || s->bullets[i].x > 750.0f
                || s->bullets[i].y < 40.0f) {
                s->bullets[i].active = false;
            }
        }
    }"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: обновление 10 пуль (dx/dy/life)")

# 5) Отрисовка
old = """    SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0x00, 255);
    for (int i = 0; i < 3; ++i) {
        if (s->bullets[i].active) {
            SDL_FRect b = { s->bullets[i].x, s->bullets[i].y, 8, 3 };
            SDL_RenderFillRect(s->renderer, &b);
        }
    }"""
new = """    SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0x00, 255);
    for (int i = 0; i < 10; ++i) {
        if (s->bullets[i].active) {
            float w = (i < 5) ? 8.0f : 3.0f;
            float h = (i < 5) ? 3.0f : 8.0f;
            SDL_FRect b = { s->bullets[i].x, s->bullets[i].y, w, h };
            SDL_RenderFillRect(s->renderer, &b);
        }
    }"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: отрисовка 8x3 (гор) и 3x8 (верт)")

p.write_text(s)
print(f"\nИзменено: {changes}/5")
