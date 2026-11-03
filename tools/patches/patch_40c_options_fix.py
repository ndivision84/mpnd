#!/usr/bin/env python3
"""patch_40c — фикс render_options: 5 отдельных строк без неподдерживаемых символов."""
import re
from pathlib import Path

p = Path('src/menu.cpp')
s = p.read_text(encoding='utf-8')

old = re.search(
    r'static void render_options\(SDL_Renderer\* r, AppState\* s\) \{.*?\n\}',
    s, re.DOTALL)

if not old:
    print("FAIL: render_options не найден")
    raise SystemExit(1)

new = '''static void render_options(SDL_Renderer* r, AppState* s) {
    (void)s;
    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 80, "OPTIONS", 4.0f);

    draw_box(r, 150, 180, 500, 340, 0x00, 0x88, 0x44);

    SDL_SetRenderDrawColor(r, 0x00, 0x88, 0x44, 255);
    draw_text_centered(r, 220, "DIFFICULTY", 2.0f);
    draw_text_centered(r, 260, "NAME", 2.0f);
    draw_text_centered(r, 300, "LIVES", 2.0f);
    draw_text_centered(r, 340, "TOP SCORES", 2.0f);

    SDL_SetRenderDrawColor(r, 0x00, 0x66, 0x33, 255);
    draw_text_centered(r, 400, "PATCH 41 COMING SOON", 1.8f);

    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 460, "PRESS ESC", 2.5f);
}'''

s = s[:old.start()] + new + s[old.end():]
p.write_text(s, encoding='utf-8')
print("OK: render_options переписан (5 строк, без спецсимволов)")

# Быстрая проверка
s = p.read_text(encoding='utf-8')
checks = [
    ('DIFFICULTY отдельно',  'draw_text_centered(r, 220, "DIFFICULTY"' in s),
    ('NAME отдельно',        'draw_text_centered(r, 260, "NAME"' in s),
    ('LIVES отдельно',       'draw_text_centered(r, 300, "LIVES"' in s),
    ('TOP SCORES отдельно',  'draw_text_centered(r, 340, "TOP SCORES"' in s),
    ('без "(patch_41)"',     '(patch_41)' not in s),
    ('без слэшей в тексте',  'DIFFICULTY / NAME' not in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
