#!/usr/bin/env python3
"""patch_07e_bomb_visual.py

1. Высота спавна бомб: y = 150 → 100 (17% от верха).
2. Белая обводка вокруг красной бомбы (видна на чёрном небе).
"""
import re
from pathlib import Path

BOMB_Y = 100.0   # 17% от 600

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ── 1) Y спавна 150 → 100 ──
pattern = r's->bombs\[i\]\.y\s*=\s*[0-9.]+f;'
new = f's->bombs[i].y = {BOMB_Y}f;'
s, n = re.subn(pattern, new, s, count=1)
if n > 0:
    changes += 1
    print(f"OK: y спавна бомбы → {BOMB_Y}f (17% от 600)")
else:
    print("!! не найден блок 'bombs[i].y = ...'")

# ── 2) Отрисовка бомб: белая обводка ──
old_block = """    // ── Отрисовка бомб ──
    for (int bo = 0; bo < 5; ++bo) {
        if (!s->bombs[bo].active) continue;
        float bx = s->bombs[bo].x, by = s->bombs[bo].y;
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x30, 0x30, 255);
        SDL_FRect c1 = { bx - 4, by - 4, 8, 8 };   SDL_RenderFillRect(s->renderer, &c1);
        SDL_FRect c2 = { bx - 6, by - 2, 12, 4 };  SDL_RenderFillRect(s->renderer, &c2);
        SDL_FRect c3 = { bx - 2, by - 6, 4, 12 };  SDL_RenderFillRect(s->renderer, &c3);
    }"""

new_block = """    // ── Отрисовка бомб (красная + белая обводка) ──
    for (int bo = 0; bo < 5; ++bo) {
        if (!s->bombs[bo].active) continue;
        float bx = s->bombs[bo].x, by = s->bombs[bo].y;

        // Белая обводка — 3 прямоугольника побольше
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0xFF, 255);
        SDL_FRect o1 = { bx - 6, by - 6, 12, 12 };  SDL_RenderFillRect(s->renderer, &o1);
        SDL_FRect o2 = { bx - 8, by - 3, 16, 6  };  SDL_RenderFillRect(s->renderer, &o2);
        SDL_FRect o3 = { bx - 3, by - 8, 6, 16  };  SDL_RenderFillRect(s->renderer, &o3);

        // Красная бомба — 3 прямоугольника поменьше
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x30, 0x30, 255);
        SDL_FRect c1 = { bx - 4, by - 4, 8, 8  };   SDL_RenderFillRect(s->renderer, &c1);
        SDL_FRect c2 = { bx - 6, by - 2, 12, 4 };   SDL_RenderFillRect(s->renderer, &c2);
        SDL_FRect c3 = { bx - 2, by - 6, 4, 12 };   SDL_RenderFillRect(s->renderer, &c3);

        // Чёрный центр — «глаз» бомбы
        SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
        SDL_FRect center = { bx - 1, by - 1, 2, 2 };
        SDL_RenderFillRect(s->renderer, &center);
    }"""

if old_block in s:
    s = s.replace(old_block, new_block, 1); changes += 1
    print("OK: бомбы с белой обводкой и чёрным центром")
else:
    print("!! не найден старый блок отрисовки бомб")

p.write_text(s)
print(f"\nИзменено: {changes}/2")
