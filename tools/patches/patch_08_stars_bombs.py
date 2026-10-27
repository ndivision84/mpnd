#!/usr/bin/env python3
"""patch_08_stars_bombs.py

1. Бомбы: y = 100 → y = -10 (падают с самого верха экрана).
2. Звёздное небо: 120 случайных точек в верхней зоне (0..220 px),
   с параллаксом 0.05 (двигаются в 20x медленнее мира).
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) Бомбы: y = 100 → -10
# ═══════════════════════════════════════════════════════════════
pattern = r's->bombs\[i\]\.y\s*=\s*[0-9.]+f;'
new = 's->bombs[i].y = -10.0f;'
s, n = re.subn(pattern, new, s, count=1)
if n > 0:
    changes += 1
    print("OK: бомбы y = -10 (падают с самого верха)")

# ═══════════════════════════════════════════════════════════════
# 2) struct Star — после struct Bomb
# ═══════════════════════════════════════════════════════════════
if 'struct Star {' not in s:
    anchor = """struct Bomb {
    float x = 0.0f;
    float y = 0.0f;
    float dy = 200.0f;
    bool active = false;
};"""
    insert = anchor + """

struct Star {
    float x = 0.0f;
    float y = 0.0f;
    uint8_t brightness = 200;
};"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: struct Star добавлен")

# ═══════════════════════════════════════════════════════════════
# 3) AppState: stars[120]
# ═══════════════════════════════════════════════════════════════
if 'Star          stars[' not in s:
    anchor = "    Bomb          bombs[5];"
    insert = """    Bomb          bombs[5];
    Star          stars[120];"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: AppState.stars[120]")

# ═══════════════════════════════════════════════════════════════
# 4) Инициализация звёзд в SDL_AppInit (после загрузки текстур)
# ═══════════════════════════════════════════════════════════════
if 'stars[i].brightness' not in s:
    # Найдём блок, где rng уже создан (после палитры)
    anchor = """    SDL_Log("Palette #%d:", palette_idx);"""
    insert = """    // ── Инициализация звёзд ──
    {
        std::uniform_real_distribution<float> star_x(0.0f, 800.0f);
        std::uniform_real_distribution<float> star_y(0.0f, 220.0f);
        std::uniform_int_distribution<int>   star_b(120, 255);
        for (int i = 0; i < 120; ++i) {
            s->stars[i].x = star_x(rng);
            s->stars[i].y = star_y(rng);
            s->stars[i].brightness = (uint8_t)star_b(rng);
        }
        SDL_Log("Stars initialized: 120");
    }

    SDL_Log("Palette #%d:", palette_idx);"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: инициализация 120 звёзд")
    else:
        print("!! не найден якорь 'Palette #%d'")

# ═══════════════════════════════════════════════════════════════
# 5) Отрисовка звёзд (перед параллаксом ландшафта)
# ═══════════════════════════════════════════════════════════════
if 'star parallax' not in s.lower() and 'stars[i].brightness' in s:
    # Найдём начало отрисовки параллакса: "for (int i = 0; i < 3; ++i)"
    anchor = """    for (int i = 0; i < 3; ++i) {
        if (!s->layers[i].tex) continue;"""
    insert = """    // ── Отрисовка звёзд (параллакс 0.05) ──
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
    }

    for (int i = 0; i < 3; ++i) {
        if (!s->layers[i].tex) continue;"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: отрисовка звёзд (параллакс 0.05)")

p.write_text(s)
print(f"\nИзменено: {changes}/5")
