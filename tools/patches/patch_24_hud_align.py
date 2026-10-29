#!/usr/bin/env python3
"""patch_24_hud_align.py — CAUTION: убрать мерцание + right-align, TIME: y-отступ."""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) Заменить весь блок draw_hud (TIME + счёт + CAUTION)
old = """static void draw_hud(SDL_Renderer* r, int score, int time_left, float world_x) {
    // Цвет HUD — ярко-белый
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);

    // TIME слева
    draw_text(r, 20, 20, "TIME");
    char tbuf[4];
    tbuf[0] = '0' + (time_left / 10) % 10;
    tbuf[1] = '0' + time_left % 10;
    tbuf[2] = 0;
    draw_text(r, 20, 40, tbuf);

    // Счёт в центре — 5 цифр
    char sbuf[8];
    for (int i = 0; i < 5; ++i) {
        sbuf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    sbuf[5] = 0;
    draw_text(r, 340, 20, sbuf);

    // CAUTION справа — мигает раз в полсекунды
    if (((int)(world_x * 2) / 1) % 2 == 0) {
        draw_text(r, 640, 20, "CAUTION");
    }
}"""

new = """static void draw_hud(SDL_Renderer* r, int score, int time_left, float world_x) {
    (void)world_x;   // не используется (CAUTION теперь статичен)
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);

    // TIME слева
    draw_text(r, 20, 20, "TIME", 4.0f);
    char tbuf[4];
    tbuf[0] = '0' + (time_left / 10) % 10;
    tbuf[1] = '0' + time_left % 10;
    tbuf[2] = 0;
    draw_text(r, 20, 54, tbuf, 4.0f);

    // Счёт в центре — 5 цифр
    char sbuf[8];
    for (int i = 0; i < 5; ++i) {
        sbuf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    sbuf[5] = 0;
    draw_text(r, 340, 20, sbuf, 4.0f);

    // CAUTION справа — статично, right-aligned (не вылезает за край)
    const float cw = 7 * 6.0f * 4.0f;   // width of "CAUTION" at scale 4
    draw_text(r, 800.0f - cw - 20.0f, 20, "CAUTION", 4.0f);
}"""

if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: draw_hud — статичный CAUTION + right-align + TIME y=54")
else:
    print("!! не найден блок draw_hud (проверьте сигнатуру и содержимое)")

p.write_text(s)
print(f"\nИзменено: {changes}/1")
