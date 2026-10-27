#!/usr/bin/env python3
"""patch_20_center_text.py

1. draw_text: пробел → cx += 4*scale (не 8).
2. Добавить text_width() и draw_text_centered().
3. Заменить вызовы в ATTRACT / GAME_OVER / SCORE на центрированные.
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) Пробел в draw_text → 4*scale
# ═══════════════════════════════════════════════════════════════
old = """        else if (*p == 'D') code = 25;
        else { cx += 8; continue; }"""
new = """        else if (*p == 'D') code = 25;
        else if (*p == ' ') { cx += 4.0f * scale; continue; }
        else { cx += 8; continue; }"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: пробел в draw_text → 4*scale")
else:
    print("!! не найден конец draw_text (после 'D')")

# ═══════════════════════════════════════════════════════════════
# 2) text_width + draw_text_centered после draw_text
# ═══════════════════════════════════════════════════════════════
if 'draw_text_centered' not in s:
    # Найдём закрытие draw_text — по строке '        cx += 4.0f * scale;\n    }\n}'
    # Проще: найдём конец функции draw_text по паттерну `\n}` после `cx += 4.0f * scale;`
    # Вставим после закрывающей скобки функции

    # Ищем "static void draw_text(...)" и его закрывающую скобку
    idx = s.find('static void draw_text(')
    if idx < 0:
        print("!! не найден draw_text")
    else:
        # Найдём "{" после объявления
        brace = s.find('{', idx)
        depth = 0
        end = brace
        for i in range(brace, len(s)):
            if s[i] == '{': depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        # Вставим после `end` + 1 (после закрывающей `}`)
        insert = """

static float text_width(const char* s, float scale) {
    int n = 0;
    for (const char* p = s; *p; ++p) n++;
    return n * 4.0f * scale;
}

static void draw_text_centered(SDL_Renderer* r, float y, const char* s, float scale) {
    float x = (800.0f - text_width(s, scale)) / 2.0f;
    draw_text(r, x, y, s, scale);
}"""
        s = s[:end+1] + insert + s[end+1:]
        changes += 1
        print("OK: draw_text_centered + text_width добавлены")

# ═══════════════════════════════════════════════════════════════
# 3) Заменить вызовы в ATTRACT
# ═══════════════════════════════════════════════════════════════
repl_attract = [
    ('draw_text(s->renderer, 44, 250, "MOON PATROL ND", 8.0f);',
     'draw_text_centered(s->renderer, 220, "MOON PATROL ND", 8.0f);'),
    ('draw_text(s->renderer, 280, 400, "PRESS SPACE", 3.0f);',
     'draw_text_centered(s->renderer, 420, "PRESS SPACE", 3.0f);'),
]
for old, new in repl_attract:
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print(f"OK: {old[:50]}... → центрировано")

# ═══════════════════════════════════════════════════════════════
# 4) Заменить вызовы в GAME_OVER
# ═══════════════════════════════════════════════════════════════
repl_gameover = [
    ('draw_text(s->renderer, 200, 260, "GAME OVER", 7.0f);',
     'draw_text_centered(s->renderer, 260, "GAME OVER", 7.0f);'),
    ('draw_text(s->renderer, 280, 420, "PRESS SPACE", 3.0f);',
     'draw_text_centered(s->renderer, 420, "PRESS SPACE", 3.0f);'),
]
for old, new in repl_gameover:
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print(f"OK: {old[:50]}... → центрировано")

# ═══════════════════════════════════════════════════════════════
# 5) Заменить вызовы в SCORE
# ═══════════════════════════════════════════════════════════════
repl_score = [
    ('draw_text(s->renderer, 300, 160, "SCORE", 5.0f);',
     'draw_text_centered(s->renderer, 160, "SCORE", 5.0f);'),
    ('draw_text(s->renderer, 240, 300, score_buf, 10.0f);',
     'draw_text_centered(s->renderer, 300, score_buf, 10.0f);'),
    ('draw_text(s->renderer, 280, 500, "PRESS SPACE", 3.0f);',
     'draw_text_centered(s->renderer, 500, "PRESS SPACE", 3.0f);'),
]
for old, new in repl_score:
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print(f"OK: {old[:50]}... → центрировано")

# ═══════════════════════════════════════════════════════════════
# 6) Старый draw_game_over (не используется) — тоже центрируем
# ═══════════════════════════════════════════════════════════════
repl_old = [
    ('draw_text(r, 328, 250, "GAME OVER", 4.0f);',
     'draw_text_centered(r, 250, "GAME OVER", 4.0f);'),
    ('draw_text(r, 344, 340, "PRESS R", 4.0f);',
     'draw_text_centered(r, 340, "PRESS R", 4.0f);'),
]
for old, new in repl_old:
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print(f"OK: {old[:50]}... → центрировано (старый draw_game_over)")

p.write_text(s)
print(f"\nИзменено блоков: {changes}")
