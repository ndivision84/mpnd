#!/usr/bin/env python3
"""patch_07b_collision.py

1. Пуля life 0.9s → 1.2s — долетает до дальней тарелки.
2. Тарелки y = 215..245 (было 200..260) — пуля на y=220 визуально попадает.
3. Бокс коллизии 40×40 → 45×45.
4. SDL_Log при попадании в тарелку (для отладки в терминале).
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) life 0.9 → 1.2 (горизонтальная пуля, слот 0..4)
old = """                s->bullets[i].x    = sx + 24;
                s->bullets[i].y    = sy - 200;   // в небо, к тарелкам
                s->bullets[i].dx   = 600.0f;
                s->bullets[i].dy   = 0.0f;
                s->bullets[i].life = 0.9f;"""
new = """                s->bullets[i].x    = sx + 24;
                s->bullets[i].y    = sy - 200;
                s->bullets[i].dx   = 600.0f;
                s->bullets[i].dy   = 0.0f;
                s->bullets[i].life = 1.2f;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: life 0.9 → 1.2 (пуля летит дальше)")
else:
    # попробуем без комментария
    old2 = """                s->bullets[i].life = 0.9f;
                s->bullets[i].active = true;
                break;
            }
        }
        for (int i = 5; i < 10; ++i) {"""
    new2 = """                s->bullets[i].life = 1.2f;
                s->bullets[i].active = true;
                break;
            }
        }
        for (int i = 5; i < 10; ++i) {"""
    if old2 in s:
        s = s.replace(old2, new2, 1); changes += 1
        print("OK: life 0.9 → 1.2 (через второй якорь)")

# 2) Тарелки y = 215..245
old = "s->enemies[i].y = 200.0f + (float)(rand() % 60);"
new = "s->enemies[i].y = 215.0f + (float)(rand() % 30);"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: тарелки y = 215..245 (визуально совпадают с пулей)")

# 3) Бокс 40×40 → 45×45
old = """            if (fabs(s->bullets[b].x - s->enemies[e].x) < 40 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 40) {"""
new = """            if (fabs(s->bullets[b].x - s->enemies[e].x) < 45 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 45) {"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: бокс коллизии 45×45")

# 4) SDL_Log при попадании (для отладки)
old = """                s->enemies[e].active = false;
                s->bullets[b].active = false;
                s->score += 100;
                if (s->score > 99999) s->score = 99999;
                break;"""
new = """                s->enemies[e].active = false;
                s->bullets[b].active = false;
                s->score += 100;
                if (s->score > 99999) s->score = 99999;
                SDL_Log("HIT plate! score=%d", s->score);
                break;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: SDL_Log на попадании в тарелку")

p.write_text(s)
print(f"\nИзменено: {changes}/4")
