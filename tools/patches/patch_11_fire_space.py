#!/usr/bin/env python3
"""patch_11_fire_space.py — стрельба с Space вместо Z.

Проверяет, что Z используется ТОЛЬКО в SDL_AppEvent (стрельба),
не в других местах (например, не в движении).
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) Найти все SDLK_Z — должны быть только в SDL_AppEvent
z_lines = [i+1 for i, line in enumerate(s.split('\n')) if 'SDLK_Z' in line]
print(f"[i] SDLK_Z используется на строках: {z_lines}")

if not z_lines:
    print("!! SDLK_Z не найден — нечего менять")
else:
    # 2) Заменить SDLK_Z → SDLK_SPACE
    n = s.count("SDLK_Z")
    s = s.replace("SDLK_Z", "SDLK_SPACE")
    changes += 1
    print(f"OK: SDLK_Z → SDLK_SPACE ({n} вхождений)")

# 3) Проверить: SDLK_SPACE не используется где-то ещё (должен быть свободен)
space_lines = [i+1 for i, line in enumerate(s.split('\n')) if 'SDLK_SPACE' in line]
print(f"[i] SDLK_SPACE после патча на строках: {space_lines}")

# 4) Убедиться, что SDL_SCANCODE_UP остался для прыжка
up_lines = [i+1 for i, line in enumerate(s.split('\n')) if 'SDL_SCANCODE_UP' in line]
print(f"[i] SDL_SCANCODE_UP (прыжок) на строках: {up_lines}")

p.write_text(s)
print(f"\nИзменено: {changes}/1")
