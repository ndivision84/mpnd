#!/usr/bin/env python3
"""patch_37_hud_russian.py — HUD на русском, одна строка, динамическая раскладка.

Layout (scale 2.8, y=20):
  ЗОНА:A   ВРЕМЯ:12   ОЧКИ:00050   ЖИЗНИ:3   РЕЖИМ:HARD

Добавлено 13 глифов 5x7 (коды 37..49): З О Н А В Р Е М Я Ч К И Ж
UTF-8 декодер в draw_text (U+0410..U+042F).
text_width теперь корректно считает UTF-8 chars (для центрирования).

Переменные в draw_hud: X_zone, X_time, X_score, X_lives, X_difficulty.

Зависит от: patch_36.
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text(encoding='utf-8')

print("=== ДИАГНОСТИКА (до) ===\n")

if 'ЗОНА:' in s:
    print("  УЖЕ ПРИМЕНЁН — выход.")
    raise SystemExit(0)

print(f"  draw_glyph bound:    {'code > 36' if 'code > 36' in s else '?'}")
print(f"  draw_hud sig:        {'zone_index' if 'draw_hud(SDL_Renderer* r, int score, int zone_index' in s else '?'}")

print("\n=== ПРИМЕНЕНИЕ ===\n")
changes = 0

# 0. <cstdio> для snprintf
if '#include <cstdio>' not in s:
    if '#include <chrono>' in s:
        s = s.replace('#include <chrono>', '#include <chrono>\n#include <cstdio>', 1)
        changes += 1
        print("OK: <cstdio>")

# 1. +13 кириллических глифов
old_glyphs = '''    {0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F},  // Z (35)
    {0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00},  // : (36)
};'''
new_glyphs = '''    {0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F},  // Z (35)
    {0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00},  // : (36)
    // Кириллица (37..49) — для русского HUD
    {0x0E, 0x11, 0x01, 0x06, 0x01, 0x11, 0x0E},  // З (37)
    {0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E},  // О (38)
    {0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11},  // Н (39)
    {0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11},  // А (40)
    {0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E},  // В (41)
    {0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10},  // Р (42)
    {0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F},  // Е (43)
    {0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11},  // М (44)
    {0x0F, 0x11, 0x11, 0x0F, 0x05, 0x09, 0x11},  // Я (45)
    {0x11, 0x11, 0x11, 0x0F, 0x01, 0x01, 0x01},  // Ч (46)
    {0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11},  // К (47)
    {0x11, 0x11, 0x13, 0x15, 0x19, 0x11, 0x11},  // И (48)
    {0x15, 0x15, 0x15, 0x1F, 0x15, 0x15, 0x15},  // Ж (49)
};'''
if old_glyphs in s:
    s = s.replace(old_glyphs, new_glyphs, 1); changes += 1
    print("OK: +13 кириллических глифов (37..49)")
else:
    print("FAIL: хвост таблицы glyphs не найден"); raise SystemExit(1)

# 2. draw_glyph: расширить bound
if 'code > 36' in s:
    s = s.replace('code > 36', 'code > 49', 1); changes += 1
    print("OK: draw_glyph bound 36 → 49")

# 3. draw_text: UTF-8 декодер
old_draw = '''static void draw_text(SDL_Renderer* r, float x, float y, const char* s, float scale = 4.0f) {
    float cx = x;
    for (const char* p = s; *p; ++p) {
        int code;
        if (*p >= '0' && *p <= '9') code = *p - '0';
        else if (*p >= 'A' && *p <= 'Z') code = 10 + (*p - 'A');
        else if (*p == ':') code = 36;
        else if (*p == ' ') { cx += 6.0f * scale; continue; }
        else { cx += 8; continue; }
        draw_glyph(r, cx, y, code, scale);
        cx += 6.0f * scale;
    }
}'''
new_draw = '''static void draw_text(SDL_Renderer* r, float x, float y, const char* s, float scale = 4.0f) {
    float cx = x;
    for (const char* p = s; *p; ) {
        unsigned char b0 = (unsigned char)*p;
        int code = -1;
        if (b0 >= 0x80) {
            // 2-byte UTF-8 (кириллица, U+0410..U+042F)
            if (b0 == 0xD0 && *(p+1)) {
                unsigned char b1 = (unsigned char)*(p+1);
                switch (b1) {
                    case 0x97: code = 37; break; // З
                    case 0x9E: code = 38; break; // О
                    case 0x9D: code = 39; break; // Н
                    case 0x90: code = 40; break; // А
                    case 0x92: code = 41; break; // В
                    case 0xA0: code = 42; break; // Р
                    case 0x95: code = 43; break; // Е
                    case 0x9C: code = 44; break; // М
                    case 0xAF: code = 45; break; // Я
                    case 0xA7: code = 46; break; // Ч
                    case 0x9A: code = 47; break; // К
                    case 0x98: code = 48; break; // И
                    case 0x96: code = 49; break; // Ж
                }
                p += 2;
            } else { p += 1; continue; }
        } else if (b0 >= '0' && b0 <= '9') { code = b0 - '0'; p++; }
        else if (b0 >= 'A' && b0 <= 'Z') { code = 10 + (b0 - 'A'); p++; }
        else if (b0 == ':') { code = 36; p++; }
        else if (b0 == ' ') { cx += 6.0f * scale; p++; continue; }
        else { cx += 8; p++; continue; }
        if (code >= 0) draw_glyph(r, cx, y, code, scale);
        cx += 6.0f * scale;
    }
}'''
if old_draw in s:
    s = s.replace(old_draw, new_draw, 1); changes += 1
    print("OK: draw_text — UTF-8 декодер")
else:
    print("FAIL: draw_text не найден"); raise SystemExit(1)

# 4. text_width: считать UTF-8 chars
old_width = '''static float text_width(const char* s, float scale) {
    int n = 0;
    for (const char* p = s; *p; ++p) n++;
    return n * 6.0f * scale;
}'''
new_width = '''static float text_width(const char* s, float scale) {
    int n = 0;
    for (const char* p = s; *p; ) {
        unsigned char b0 = (unsigned char)*p;
        p += (b0 >= 0x80) ? 2 : 1;
        n++;
    }
    return n * 6.0f * scale;
}'''
if old_width in s:
    s = s.replace(old_width, new_width, 1); changes += 1
    print("OK: text_width — UTF-8 chars")
else:
    print("FAIL: text_width не найден"); raise SystemExit(1)

# 5. draw_hud — русский, одна строка, динамика
old_hud = '''static void draw_hud(SDL_Renderer* r, int score, int zone_index, float zone_time, int lives, int difficulty) {
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);

    constexpr float HUD_SCALE = 3.0f;
    constexpr float HUD_Y     = 20.0f;

    // Слева: "A 12" — зона + секунды в ней
    char zbuf[8];
    zbuf[0] = zone_letter(zone_index);
    zbuf[1] = ' ';
    int sec = (int)zone_time;
    if (sec < 0)  sec = 0;
    if (sec > 99) sec = 99;
    zbuf[2] = '0' + (sec / 10) % 10;
    zbuf[3] = '0' + sec % 10;
    zbuf[4] = 0;
    draw_text(r, 20.0f, HUD_Y, zbuf, HUD_SCALE);

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

    // Справа: "L3 EASY" / "L3 NORMAL" / "L3 HARD"
    const char* mode_str = (difficulty == 0) ? "EASY" :
                           (difficulty == 2) ? "HARD" : "NORMAL";
    char rbuf[16];
    rbuf[0] = 'L';
    int lv = (lives < 0) ? 0 : ((lives > 9) ? 9 : lives);
    rbuf[1] = '0' + lv;
    rbuf[2] = ' ';
    int ri = 3;
    for (const char* q = mode_str; *q && ri < 15; ++q) rbuf[ri++] = *q;
    rbuf[ri] = 0;
    const float cw = ri * 6.0f * HUD_SCALE;
    draw_text(r, 800.0f - cw - 20.0f, HUD_Y, rbuf, HUD_SCALE);
}'''
new_hud = '''static void draw_hud(SDL_Renderer* r, int score, int zone_index, float zone_time, int lives, int difficulty) {
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);

    constexpr float HUD_SCALE = 2.8f;
    constexpr float HUD_Y     = 20.0f;
    constexpr float MARGIN    = 20.0f;

    int sec = (int)zone_time;  if (sec < 0) sec = 0;  if (sec > 99)    sec = 99;
    int sc  = score;           if (sc  < 0) sc  = 0;  if (sc  > 99999) sc  = 99999;
    int lv  = lives;           if (lv  < 0) lv  = 0;  if (lv  > 9)     lv  = 9;
    const char* mode = (difficulty == 0) ? "EASY" :
                       (difficulty == 2) ? "HARD" : "NORMAL";

    char X_zone[32], X_time[32], X_score[32], X_lives[32], X_difficulty[32];
    snprintf(X_zone,       sizeof(X_zone),       "ЗОНА:%c",    zone_letter(zone_index));
    snprintf(X_time,       sizeof(X_time),       "ВРЕМЯ:%02d", sec);
    snprintf(X_score,      sizeof(X_score),      "ОЧКИ:%05d",  sc);
    snprintf(X_lives,      sizeof(X_lives),      "ЖИЗНИ:%d",   lv);
    snprintf(X_difficulty, sizeof(X_difficulty), "РЕЖИМ:%s",   mode);

    const char* parts[5] = { X_zone, X_time, X_score, X_lives, X_difficulty };
    float widths[5];
    float total = 0.0f;
    for (int i = 0; i < 5; ++i) {
        widths[i] = text_width(parts[i], HUD_SCALE);
        total += widths[i];
    }
    float gap = (800.0f - total - 2.0f * MARGIN) / 4.0f;
    if (gap < 4.0f) gap = 4.0f;

    float x = MARGIN;
    for (int i = 0; i < 5; ++i) {
        draw_text(r, x, HUD_Y, parts[i], HUD_SCALE);
        x += widths[i] + gap;
    }
}'''
if old_hud in s:
    s = s.replace(old_hud, new_hud, 1); changes += 1
    print("OK: draw_hud — русский, 1 строка, динамика (scale 2.8)")
else:
    print("FAIL: draw_hud не найден"); raise SystemExit(1)

p.write_text(s, encoding='utf-8')
print(f"\nВсего изменений: {changes}")

# ─────────────────────────────────────────────────────────────
# ВЕРИФИКАЦИЯ
# ─────────────────────────────────────────────────────────────
print("\n=== ВЕРИФИКАЦИЯ (после) ===\n")
s = p.read_text(encoding='utf-8')
print(f"  «ЗОНА:» в файле:   {'да' if 'ЗОНА:' in s else 'НЕТ'}")
print(f"  «РЕЖИМ:» в файле:  {'да' if 'РЕЖИМ:' in s else 'НЕТ'}")
print(f"  «СЛОЖНОСТЬ»:       {'осталось (плохо)' if 'СЛОЖНОСТЬ' in s else 'нет (хорошо)'}")
print(f"  glyphs rows:        {s.count(' // ')} (было ~36 + 13 = ~49)")
print(f"  code > 49:          {'да' if 'code > 49' in s else 'НЕТ'}")
print(f"  X_difficulty:       {'да' if 'X_difficulty' in s else 'НЕТ'}")
print(f"  <cstdio>:           {'да' if '#include <cstdio>' in s else 'НЕТ'}")
