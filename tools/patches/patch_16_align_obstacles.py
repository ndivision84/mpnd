#!/usr/bin/env python3
"""patch_16_align_obstacles.py — выравнивание препятствий по колёсам лунохода."""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) Питы: y=420 → gy (460)
# ═══════════════════════════════════════════════════════════════
if 'float gy = 460.0f' not in s:
    old = "    // ── Отрисовка препятствий ──"
    new = "    // ── Отрисовка препятствий (выровнено по колёсам: gy=460) ──\n    const float gy = 460.0f;  // player.y(420) + 40 = уровень колёс"
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: gy = 460 добавлен")

# Пит: SDL_FRect pit = { sx, 420.0f, w, 40.0f };
old = "SDL_FRect pit = { sx, 420.0f, w, 40.0f };"
new = "SDL_FRect pit = { sx, gy, w, 40.0f };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: яма → y=gy (460)")

# Пит top: { sx, 420.0f, w, 2.0f }
old = "SDL_FRect top = { sx, 420.0f, w, 2.0f };"
new = "SDL_FRect top = { sx, gy, w, 2.0f };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: яма top → y=gy")

# ═══════════════════════════════════════════════════════════════
# 2) Камень: 400 → gy-35 (425), высота 22 → 35
# ═══════════════════════════════════════════════════════════════
# Tex
old = "SDL_FRect dst = { sx - 4, 392.0f, w + 8, 32 };"
new = "SDL_FRect dst = { sx - 4, gy - 35, w + 8, 35 };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: rock_tex → y=gy-35, h=35")

# Rock
old = "SDL_FRect rock = { sx, 400.0f, w, 20.0f };"
new = "SDL_FRect rock = { sx, gy - 35, w, 35.0f };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: камень → y=gy-35, h=35")

# Rock top
old = "SDL_FRect rock_top = { sx, 400.0f, w, 2.0f };"
new = "SDL_FRect rock_top = { sx, gy - 35, w, 2.0f };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: камень top → y=gy-35")

# ═══════════════════════════════════════════════════════════════
# 3) Кратер: rims и rim_top
# ═══════════════════════════════════════════════════════════════
old = "SDL_FRect left_rim  = { sx - 4, 410.0f, 6, 12 };"
new = "SDL_FRect left_rim  = { sx - 4, gy - 12, 6, 12 };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: crater left_rim → y=gy-12")

old = "SDL_FRect right_rim = { sx + w - 2, 410.0f, 6, 12 };"
new = "SDL_FRect right_rim = { sx + w - 2, gy - 12, 6, 12 };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: crater right_rim → y=gy-12")

old = "SDL_FRect rim_top = { sx - 2, 418.0f, w + 4, 3.0f };"
new = "SDL_FRect rim_top = { sx - 2, gy - 4, w + 4, 3.0f };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: crater rim_top → y=gy-4")

old = "float row_y = 421.0f + row * 3.4f;"
new = "float row_y = gy - 2 + row * 3.4f;"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: crater V-воронка → y=gy-2")

# ═══════════════════════════════════════════════════════════════
# 4) Пуля из пушки на уровень пушки (было sy-24 = 396, стало sy+6 = 426)
# ═══════════════════════════════════════════════════════════════
old = "s->bullets[i].y    = sy - 24;"
new = "s->bullets[i].y    = sy + 6;   // на уровне пушки (426)"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: горизонтальная пуля из пушки (y=426)")
else:
    print("!! не найдено 'sy - 24' (пуля)")

# ═══════════════════════════════════════════════════════════════
# 5) Hitbox камня: 410 → 442
# ═══════════════════════════════════════════════════════════════
old = "if (fabs(s->bullets[b].x - rock_cx) < s->obstacles[i].width / 2.0f + 10 &&\n                fabs(s->bullets[b].y - 410.0f) < 25) {"
new = "if (fabs(s->bullets[b].x - rock_cx) < s->obstacles[i].width / 2.0f + 10 &&\n                fabs(s->bullets[b].y - 442.0f) < 30) {"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: hitbox камня 410±25 → 442±30")

p.write_text(s)
print(f"\nИзменено: {changes}/9")
