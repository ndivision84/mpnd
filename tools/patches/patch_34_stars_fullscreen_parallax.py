#!/usr/bin/env python3
"""patch_34_stars_fullscreen_parallax.py — звёзды на весь экран + 3 слоя параллакса.

Фиксы:
  1. Звёзды на весь экран: star_y range 0..300 → 0..600
  2. 3 скорости (случайно): slow=0.06, normal=0.15, fast=0.30
     (было 0.05 для всех — теперь средняя ~13.6 px/с vs 4 px/с)
  3. Рефакторинг: draw_stars() helper вместо двух копий inline-цикла

Зависит от: patch_33 (уже применим).
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

print("=== ДИАГНОСТИКА (до) ===\n")

m = re.search(r'std::uniform_real_distribution<float> star_y\(([\d.]+f), ([\d.]+f)\)', s)
print(f"  star_y range:       ({m.group(1) if m else '?'}, {m.group(2) if m else '?'})")
print(f"  STAR_PARALLAX=0.05f: {s.count('STAR_PARALLAX = 0.05f')} вхождений (ожидается 2)")
print(f"  struct Star:        {'найден' if 'struct Star {' in s else 'НЕ НАЙДЕН'}")
print(f"  parallax field:     {'есть' if 'float parallax' in s else 'нет'}")
print(f"  draw_stars helper:  {'есть' if 'static void draw_stars' in s else 'нет'}")

print("\n=== ПРИМЕНЕНИЕ ===\n")
changes = 0

# 1) struct Star: добавить float parallax
if 'float parallax' not in s:
    old = '''struct Star {
    float x = 0.0f;
    float y = 0.0f;
    uint8_t brightness = 200;
};'''
    new = '''struct Star {
    float x = 0.0f;
    float y = 0.0f;
    uint8_t brightness = 200;
    float parallax = 0.15f;   // 0.06 slow / 0.15 normal / 0.30 fast
};'''
    if old in s:
        s = s.replace(old, new, 1)
        changes += 1
        print("OK: struct Star + float parallax")
    else:
        print("FAIL: struct Star не найден в ожидаемом виде")
else:
    print("SKIP: struct Star уже расширен")

# 2) init звёзд: y 0..600 + случайный parallax из 3 скоростей
old_init = '''        std::uniform_real_distribution<float> star_x(0.0f, 800.0f);
        std::uniform_real_distribution<float> star_y(0.0f, 300.0f);
        std::uniform_int_distribution<int>   star_b(120, 255);
        for (int i = 0; i < 120; ++i) {
            s->stars[i].x = star_x(rng);
            s->stars[i].y = star_y(rng);
            s->stars[i].brightness = (uint8_t)star_b(rng);
        }
        SDL_Log("Stars initialized: 120");'''
new_init = '''        std::uniform_real_distribution<float> star_x(0.0f, 800.0f);
        std::uniform_real_distribution<float> star_y(0.0f, 600.0f);
        std::uniform_int_distribution<int>   star_b(120, 255);
        std::uniform_int_distribution<int>   star_layer(0, 2);
        static const float STAR_SPEEDS[3] = { 0.06f, 0.15f, 0.30f };  // slow / normal / fast
        int layer_count[3] = { 0, 0, 0 };
        for (int i = 0; i < 120; ++i) {
            s->stars[i].x = star_x(rng);
            s->stars[i].y = star_y(rng);
            s->stars[i].brightness = (uint8_t)star_b(rng);
            int l = star_layer(rng);
            s->stars[i].parallax = STAR_SPEEDS[l];
            layer_count[l]++;
        }
        SDL_Log("Stars initialized: 120 (slow=%d, normal=%d, fast=%d)",
                layer_count[0], layer_count[1], layer_count[2]);'''
if 'star_y(0.0f, 600.0f)' not in s:
    if old_init in s:
        s = s.replace(old_init, new_init, 1)
        changes += 1
        print("OK: init — y 0..600, 3 слоя параллакса")
    else:
        print("FAIL: init звёзд не найден в ожидаемом виде")
else:
    print("SKIP: init звёзд уже обновлён")

# 3) helper draw_stars — вставить после draw_text_centered
anchor = '''static void draw_text_centered(SDL_Renderer* r, float y, const char* s, float scale) {
    float x = (800.0f - text_width(s, scale)) / 2.0f;
    draw_text(r, x, y, s, scale);
}
'''
helper = '''
// ─────────────────────────────────────────────────────────────
// Отрисовка звёзд с 3 слоями параллакса (per-star скорость)
// ─────────────────────────────────────────────────────────────
static void draw_stars(SDL_Renderer* r, const Star* stars, int count, float world_x) {
    for (int i = 0; i < count; ++i) {
        float scroll = std::fmod(world_x * stars[i].parallax, 800.0f);
        float sx = stars[i].x - scroll;
        if (sx < 0) sx += 800.0f;
        SDL_SetRenderDrawColor(r,
                               stars[i].brightness,
                               stars[i].brightness,
                               stars[i].brightness,
                               255);
        SDL_FRect rect = { sx, stars[i].y, 2, 2 };
        SDL_RenderFillRect(r, &rect);
    }
}
'''
if 'static void draw_stars' not in s:
    if anchor in s:
        s = s.replace(anchor, anchor + helper, 1)
        changes += 1
        print("OK: draw_stars helper добавлен")
    else:
        print("FAIL: anchor draw_text_centered не найден")
else:
    print("SKIP: draw_stars уже есть")

# 4) заменить первый inline-цикл (ATTRACT/GAME_OVER/SCORE)
old_loop1 = '''    // ── Экраны ATTRACT / GAME_OVER / SCORE ──
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
        }'''
new_loop1 = '''    // ── Экраны ATTRACT / GAME_OVER / SCORE ──
    if (s->state != STATE_PLAYING) {
        // Звёзды (3 слоя параллакса)
        draw_stars(s->renderer, s->stars, 120, s->world_x);'''
if 'constexpr float STAR_PARALLAX = 0.05f' in s and old_loop1 in s:
    s = s.replace(old_loop1, new_loop1, 1)
    changes += 1
    print("OK: inline-цикл #1 заменён на draw_stars()")
else:
    if 'constexpr float STAR_PARALLAX = 0.05f' not in s:
        print("SKIP: inline-цикл #1 уже заменён")
    else:
        print("FAIL: inline-цикл #1 не совпал")

# 5) заменить второй inline-цикл (PLAYING)
old_loop2 = '''    // ── Отрисовка звёзд (параллакс 0.05) ──
    {
        constexpr float STAR_PARALLAX = 0.05f;
        float star_scroll = fmod(s->world_x * STAR_PARALLAX, 800.0f);
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
    }'''
new_loop2 = '''    // ── Отрисовка звёзд (3 слоя параллакса) ──
    draw_stars(s->renderer, s->stars, 120, s->world_x);'''
if 'constexpr float STAR_PARALLAX = 0.05f' in s and old_loop2 in s:
    s = s.replace(old_loop2, new_loop2, 1)
    changes += 1
    print("OK: inline-цикл #2 заменён на draw_stars()")
else:
    if 'constexpr float STAR_PARALLAX = 0.05f' not in s:
        print("SKIP: inline-цикл #2 уже заменён")
    else:
        print("FAIL: inline-цикл #2 не совпал")

p.write_text(s)
print(f"\nИзменено: {changes}/5")

# ─────────────────────────────────────────────────────────────
# Верификация
# ─────────────────────────────────────────────────────────────
print("\n=== ВЕРИФИКАЦИЯ (после) ===\n")
s = p.read_text()
print(f"  star_y 0..600:       {'да' if 'star_y(0.0f, 600.0f)' in s else 'НЕТ'}")
print(f"  STAR_SPEEDS[3]:      {'да' if 'STAR_SPEEDS[3]' in s else 'НЕТ'}")
print(f"  struct parallax:     {'да' if 'float parallax = 0.15f' in s else 'НЕТ'}")
print(f"  draw_stars helper:   {'да' if 'static void draw_stars' in s else 'НЕТ'}")
print(f"  STAR_PARALLAX=0.05f: {'есть (плохо)' if 'STAR_PARALLAX = 0.05f' in s else 'нет (хорошо)'}")
print(f"  вызовов draw_stars(): {s.count('draw_stars(s->renderer')} (ожидается 2)")
