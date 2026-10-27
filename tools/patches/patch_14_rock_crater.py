#!/usr/bin/env python3
"""patch_14_rock_crater.py

1. Кратер: V-образная воронка с оранжевыми обломками (не похож на яму).
2. Обстрел камня: горизонтальная пуля × камень → +50 очков, камень исчезает.
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) Кратер — визуально отличается от ямы (V-воронка + обломки)
# ═══════════════════════════════════════════════════════════════
old_crater = """        } else {
            // КРАТЕР — чёрный + огненная окантовка
            SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
            SDL_FRect crater = { sx, 420.0f, w, 50.0f };
            SDL_RenderFillRect(s->renderer, &crater);
            SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x30, 0x00, 255);
            SDL_FRect t =  { sx, 420.0f, w, 3.0f };             SDL_RenderFillRect(s->renderer, &t);
            SDL_FRect b2 = { sx, 467.0f, w, 3.0f };             SDL_RenderFillRect(s->renderer, &b2);
            SDL_FRect l  = { sx, 420.0f, 3.0f, 50.0f };         SDL_RenderFillRect(s->renderer, &l);
            SDL_FRect r  = { sx + w - 3, 420.0f, 3.0f, 50.0f }; SDL_RenderFillRect(s->renderer, &r);
        }"""

new_crater = """        } else {
            // КРАТЕР — V-образная воронка с оранжевыми обломками
            // 1) Оранжевые обломки по бокам (типа выброс породы)
            SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x60, 0x00, 255);
            SDL_FRect left_rim  = { sx - 4, 410.0f, 6, 12 };
            SDL_FRect right_rim = { sx + w - 2, 410.0f, 6, 12 };
            SDL_RenderFillRect(s->renderer, &left_rim);
            SDL_RenderFillRect(s->renderer, &right_rim);

            // 2) Оранжевый гребень сверху
            SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x80, 0x00, 255);
            SDL_FRect rim_top = { sx - 2, 418.0f, w + 4, 3.0f };
            SDL_RenderFillRect(s->renderer, &rim_top);

            // 3) Чёрная воронка в форме трапеции (широкая сверху, узкая снизу)
            SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
            for (int row = 0; row < 14; ++row) {
                float row_y = 421.0f + row * 3.4f;
                float shrink = row * 2.0f;
                SDL_FRect rr = { sx + 2 + shrink, row_y, w - 4 - shrink * 2, 3.4f };
                SDL_RenderFillRect(s->renderer, &rr);
            }
        }"""

if old_crater in s:
    s = s.replace(old_crater, new_crater, 1); changes += 1
    print("OK: кратер — V-воронка с оранжевыми обломками")
else:
    print("!! не найден старый блок отрисовки кратера")

# ═══════════════════════════════════════════════════════════════
# 2) Горизонтальная пуля × камень → +50 очков
# ═══════════════════════════════════════════════════════════════
if 'SHOT ROCK' not in s:
    anchor = "    // ── Коллизии: верт. пули × NLO ──"
    insert = """    // ── Коллизии: гориз. пули × камни (обстрел камня) ──
    for (int b = 0; b < 5; ++b) {
        if (!s->bullets[b].active) continue;
        for (int i = 0; i < 8; ++i) {
            if (!s->obstacles[i].active) continue;
            if (s->obstacles[i].type != 1) continue;  // только камень
            float sx = s->obstacles[i].world_x - s->world_x;
            float rock_cx = sx + s->obstacles[i].width / 2.0f;
            if (fabs(s->bullets[b].x - rock_cx) < s->obstacles[i].width / 2.0f + 10 &&
                fabs(s->bullets[b].y - 410.0f) < 25) {
                s->obstacles[i].active = false;
                s->bullets[b].active = false;
                s->score += 50;
                if (s->score > 99999) s->score = 99999;
                SDL_Log("SHOT ROCK! score=%d", s->score);
                break;
            }
        }
    }

    // ── Коллизии: верт. пули × NLO ──"""
    if anchor in s:
        s = s.replace(anchor, insert, 1); changes += 1
        print("OK: горизонтальная пуля × камень (обстрел)")
    else:
        print("!! не найден якорь 'Коллизии: верт. пули × NLO'")

p.write_text(s)
print(f"\nИзменено: {changes}/2")
