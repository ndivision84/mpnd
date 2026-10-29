#!/usr/bin/env python3
"""patch_30_hud_clean.py — убрать DIFF, уменьшить шрифт HUD (TIME, счёт, MODE) до scale 3."""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

start_marker = 'static void draw_hud(SDL_Renderer* r, int score, int time_left, float world_x, int difficulty) {'
idx = s.find(start_marker)
if idx < 0:
    print("!! draw_hud не найден (сигнатура может отличаться)")
    print("   пришлите: grep -n 'draw_hud(' src/main.cpp")
    exit(1)

# Найти закрывающую скобку функции
brace_start = idx + len(start_marker) - 1  # позиция '{'
depth = 0
end = brace_start
for i in range(brace_start, len(s)):
    if s[i] == '{': depth += 1
    elif s[i] == '}':
        depth -= 1
        if depth == 0:
            end = i
            break

new_func = '''static void draw_hud(SDL_Renderer* r, int score, int time_left, float world_x, int difficulty) {
    (void)world_x;
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);

    constexpr float HUD_SCALE = 3.0f;
    constexpr float HUD_Y     = 20.0f;

    // TIME: XX — слева
    char tbuf[9];
    tbuf[0]='T'; tbuf[1]='I'; tbuf[2]='M'; tbuf[3]='E';
    tbuf[4]=':'; tbuf[5]=' ';
    tbuf[6]='0' + (time_left / 10) % 10;
    tbuf[7]='0' + time_left % 10;
    tbuf[8]=0;
    draw_text(r, 20.0f, HUD_Y, tbuf, HUD_SCALE);

    // Счёт — 5 цифр по центру
    char sbuf[8];
    for (int i = 0; i < 5; ++i) {
        sbuf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    sbuf[5] = 0;
    {
        const float sw = 5 * 6.0f * HUD_SCALE;
        draw_text(r, (800.0f - sw) / 2.0f, HUD_Y, sbuf, HUD_SCALE);
    }

    // MODE: <name> — справа (вместо CAUTION/DIFF)
    const char* mode_str = (difficulty == 0) ? "MODE: EASY" :
                           (difficulty == 2) ? "MODE: HARD" : "MODE: NORMAL";
    int nlen = 0;
    while (mode_str[nlen]) nlen++;
    const float cw = nlen * 6.0f * HUD_SCALE;
    draw_text(r, 800.0f - cw - 20.0f, HUD_Y, mode_str, HUD_SCALE);
}'''

s = s[:idx] + new_func + s[end+1:]
p.write_text(s)
print("OK: draw_hud переписан — MODE вместо DIFF, scale 3 для всех")
