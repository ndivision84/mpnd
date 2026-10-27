#!/usr/bin/env python3
"""patch_10_jump_up.py — прыжок на стрелку «вверх» вместо пробела."""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) Заменить SDL_SCANCODE_SPACE → SDL_SCANCODE_UP
n = s.count("SDL_SCANCODE_SPACE")
if n > 0:
    s = s.replace("SDL_SCANCODE_SPACE", "SDL_SCANCODE_UP")
    changes += 1
    print(f"OK: SDL_SCANCODE_SPACE → SDL_SCANCODE_UP ({n} вхождений)")
else:
    print("[i] SDL_SCANCODE_SPACE не найден")

# 2) Проверить, что UP не используется где-то ещё (стрелки для движения)
# Смотрим, есть ли UP в блоке движения — если есть, это конфликт
up_lines = [i+1 for i, line in enumerate(s.split('\n'))
            if 'SDL_SCANCODE_UP' in line]
print(f"[i] SDL_SCANCODE_UP используется на строках: {up_lines}")

p.write_text(s)
print(f"\nИзменено: {changes}/1")
