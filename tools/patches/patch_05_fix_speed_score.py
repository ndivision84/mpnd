#!/usr/bin/env python3
"""patch_05_fix_speed_score.py"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) Включить vsync (60 FPS)
old = """        SDL_Log("CreateWindowAndRenderer failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }"""
new = """        SDL_Log("CreateWindowAndRenderer failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }
    if (!SDL_SetRenderVSync(s->renderer, 1)) {
        SDL_Log("SDL_SetRenderVSync failed: %s", SDL_GetError());
    }"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: vsync включён")

# 2) Реальный dt из SDL_GetTicks (вместо 1/60)
old = "    const float dt = 1.0f / 60.0f;"
new = """    static Uint64 last_tick = 0;
    Uint64 now_tick = SDL_GetTicks();
    if (last_tick == 0) last_tick = now_tick;
    float dt = (now_tick - last_tick) / 1000.0f;
    last_tick = now_tick;
    if (dt > 0.1f)   dt = 0.1f;   // защита от зависаний
    if (dt < 0.001f) dt = 0.001f; // защита от div-by-zero"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: реальный dt (SDL_GetTicks)")

# 3) Пиксель глифа без -0.5f (для Retina)
old = "SDL_FRect p = { x + col * scale, y + row * scale, scale - 0.5f, scale - 0.5f };"
new = "SDL_FRect p = { x + col * scale, y + row * scale, scale, scale };"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: размер пикселя глифа (без -0.5f)")

# 4) draw_text: параметр scale вместо int code_offset
old = "static void draw_text(SDL_Renderer* r, float x, float y, const char* s, int code_offset = 0) {"
new = "static void draw_text(SDL_Renderer* r, float x, float y, const char* s, float scale = 4.0f) {"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: draw_text signature (scale)")

# 5) draw_text: правильный шаг + scale в draw_glyph
old = """        draw_glyph(r, cx, y, code);
        cx += 10;"""
new = """        draw_glyph(r, cx, y, code, scale);
        cx += 4.0f * scale;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: draw_text — шаг 4*scale, scale в draw_glyph")

# 6) Счёт — позиция (660, 15), scale 4.0
old = "    draw_text(r, 700, 15, buf);"
new = "    draw_text(r, 660, 15, buf, 4.0f);"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: счёт — позиция (660, 15)")

p.write_text(s)
print(f"\nИзменено: {changes}/6")
