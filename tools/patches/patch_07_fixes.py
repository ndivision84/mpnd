#!/usr/bin/env python3
"""patch_07_fixes.py

1. GAME OVER — одна строка "GAME OVER"
2. Бомбы: y=100 → y=150 (25% от 600)
3. Горизонтальная пуля: летит в небо (y = player.y - 200 = 220)
4. Тарелки: y = 200..260 (узкий диапазон)
5. Коллизия пуля×тарелка: бокс 40×40
6. P — пауза (AppState.paused, заморозка dt, overlay "PAUSE")
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) GAME OVER в одну строку
old = """    SDL_SetRenderDrawColor(r, 255, 50, 50, 255);
    draw_text(r, 260, 220, "GAME");
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
    draw_text(r, 260, 280, "OVER");
    SDL_SetRenderDrawColor(r, 200, 200, 200, 255);
    draw_text(r, 280, 380, "PRESS R");"""
new = """    SDL_SetRenderDrawColor(r, 255, 50, 50, 255);
    draw_text(r, 328, 250, "GAME OVER", 4.0f);

    SDL_SetRenderDrawColor(r, 200, 200, 200, 255);
    draw_text(r, 344, 340, "PRESS R", 4.0f);"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: GAME OVER — одна строка")

# 2) Бомбы: 100 → 150
old = "s->bombs[i].y = 100.0f;"
new = "s->bombs[i].y = 150.0f;"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: бомбы — y=150 (25% от 600)")

# 3) Пуля горизонтальная — в небо
old = """                s->bullets[i].x    = sx + 24;
                s->bullets[i].y    = sy - 24;"""
new = """                s->bullets[i].x    = sx + 24;
                s->bullets[i].y    = sy - 200;   // в небо, к тарелкам"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: горизонтальная пуля летит в небо (y = player.y - 200)")

# 4) Тарелки — узкий диапазон
old = "s->enemies[i].y = 120.0f + (float)(rand() % 80);"
new = "s->enemies[i].y = 200.0f + (float)(rand() % 60);"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: тарелки y = 200..260")

# 5) Бокс коллизии 40×40
old = """            if (fabs(s->bullets[b].x - s->enemies[e].x) < 35 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 35) {"""
new = """            if (fabs(s->bullets[b].x - s->enemies[e].x) < 40 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 40) {"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: коллизия пуля×тарелка 40×40")
else:
    # попробуем 30×22 от старой версии
    old2 = """            if (fabs(s->bullets[b].x - s->enemies[e].x) < 30 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 22) {"""
    new2 = """            if (fabs(s->bullets[b].x - s->enemies[e].x) < 40 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 40) {"""
    if old2 in s:
        s = s.replace(old2, new2, 1); changes += 1
        print("OK: коллизия 30×22 → 40×40")

# 6) paused в AppState
old = "    bool          game_over = false;"
new = """    bool          game_over = false;
    bool          paused = false;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: AppState.paused")

# 7) P — пауза
old = """    if (e->key.key == SDLK_G) {
        s->game_over = true;
        return SDL_APP_CONTINUE;
    }"""
new = """    if (e->key.key == SDLK_G) {
        s->game_over = true;
        return SDL_APP_CONTINUE;
    }
    if (e->key.key == SDLK_P) {
        s->paused = !s->paused;
        return SDL_APP_CONTINUE;
    }"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: P — переключение паузы")

# 8) Блокировка стрельбы на паузе
old = """    if (s->game_over) return SDL_APP_CONTINUE;
    if (e->key.key != SDLK_Z) return SDL_APP_CONTINUE;"""
new = """    if (s->game_over) return SDL_APP_CONTINUE;
    if (s->paused)   return SDL_APP_CONTINUE;
    if (e->key.key != SDLK_Z) return SDL_APP_CONTINUE;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: стрельба заблокирована на паузе")

# 9) dt = 0 при паузе
old = """    if (dt > 0.1f)   dt = 0.1f;
    if (dt < 0.001f) dt = 0.001f"""
new = """    if (dt > 0.1f)   dt = 0.1f;
    if (dt < 0.001f) dt = 0.001f;
    if (s->paused)   dt = 0.0f;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: dt = 0 при паузе")

# 10) PAUSE overlay перед SDL_RenderPresent
old = """    if (s->game_over) {
        draw_game_over(s->renderer);
    }

    SDL_RenderPresent(s->renderer);"""
new = """    if (s->game_over) {
        draw_game_over(s->renderer);
    }
    if (s->paused && !s->game_over) {
        SDL_SetRenderDrawBlendMode(s->renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 150);
        SDL_FRect pbg = { 0, 0, 800, 600 };
        SDL_RenderFillRect(s->renderer, &pbg);
        SDL_SetRenderDrawBlendMode(s->renderer, SDL_BLENDMODE_NONE);
        SDL_SetRenderDrawColor(s->renderer, 255, 255, 255, 255);
        draw_text(s->renderer, 344, 280, "PAUSE", 4.0f);
    }

    SDL_RenderPresent(s->renderer);"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: PAUSE overlay")

p.write_text(s)
print(f"\nИзменено: {changes}/10")
