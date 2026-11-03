#!/usr/bin/env python3
"""patch_40b — главное меню (безопасная версия).

Стратегия: НЕ удаляем большие блоки, только добавляем + маленькие замены.
Старый ATTRACT-рендер становится "мёртвым кодом" (до него не доходит
выполнение из-за early-return в начале SDL_AppIterate).
"""
import re
from pathlib import Path

print("=== ДИАГНОСТИКА (до) ===\n")

p_app = Path('src/app.h')
s_app = p_app.read_text(encoding='utf-8')

p_main = Path('src/main.cpp')
s_main = p_main.read_text(encoding='utf-8')

print(f"  main.cpp: {len(s_main.splitlines())} строк")
print(f"  app.h should_quit: {'есть' if 'should_quit' in s_app else 'НЕТ'}")
print(f"  app.h extern decls: {'есть' if 'void draw_text' in s_app else 'НЕТ'}")
print(f"  main.cpp #include menu.h: {'есть' if '#include \"menu.h\"' in s_main else 'НЕТ'}")
print(f"  main.cpp static draw_text: {'есть' if 'static void draw_text(' in s_main else 'НЕТ'}")
print(f"  main.cpp start_diff: {'есть' if 'start_diff' in s_main else 'НЕТ'}")
print(f"  main.cpp menu_early_return: {'есть' if 'menu_early_return' in s_main else 'НЕТ'}")

if 'SDL_AppIterate' not in s_main:
    print("\nABORT: SDL_AppIterate отсутствует — файл сломан")
    raise SystemExit(1)

changes = 0

# ─── app.h ─────────────────────────────────────────────────
if 'should_quit' not in s_app:
    old = '    bool  menu_initialized = false;'
    new = old + '\n    bool  should_quit      = false;'
    if old in s_app:
        s_app = s_app.replace(old, new, 1)
        changes += 1
        print("OK: app.h +should_quit")

if 'void draw_text' not in s_app:
    decls = '''
// ─── Extern из main.cpp (patch_40b) ─────────────────────────
void draw_text(SDL_Renderer* r, float x, float y, const char* s, float scale = 4.0f);
float text_width(const char* s, float scale);
void draw_text_centered(SDL_Renderer* r, float y, const char* s, float scale);
'''
    s_app = s_app.rstrip() + '\n' + decls
    changes += 1
    print("OK: app.h +extern decls")

p_app.write_text(s_app, encoding='utf-8')

# ─── main.cpp ──────────────────────────────────────────────

if '#include "menu.h"' not in s_main:
    old = '#include "app.h"'
    new = '#include "app.h"\n#include "menu.h"'
    if old in s_main:
        s_main = s_main.replace(old, new, 1)
        changes += 1
        print('OK: main.cpp #include "menu.h"')

s2 = s_main.replace(
    'static void draw_text(SDL_Renderer* r, float x, float y, const char* s, float scale = 4.0f) {',
    'void draw_text(SDL_Renderer* r, float x, float y, const char* s, float scale) {', 1)
if s2 != s_main:
    s_main = s2; changes += 1; print("OK: draw_text — static/default removed")

s2 = s_main.replace(
    'static float text_width(const char* s, float scale) {',
    'float text_width(const char* s, float scale) {', 1)
if s2 != s_main:
    s_main = s2; changes += 1; print("OK: text_width — static removed")

s2 = s_main.replace(
    'static void draw_text_centered(SDL_Renderer* r, float y, const char* s, float scale) {',
    'void draw_text_centered(SDL_Renderer* r, float y, const char* s, float scale) {', 1)
if s2 != s_main:
    s_main = s2; changes += 1; print("OK: draw_text_centered — static removed")

old_init = '''    SDL_Log("Palette #%d:", palette_idx);
    for (int i = 0; i < 3; ++i) {
        int c = VALID_PALETTES[palette_idx][i];
        SDL_Log("  layer %d: %-7s rgb=(%3d,%3d,%3d)",
                i, COLOR_NAMES[c],
                s->layers[i].tint.r,
                s->layers[i].tint.g,
                s->layers[i].tint.b);
    }
    return SDL_APP_CONTINUE;
}'''
new_init = '''    SDL_Log("Palette #%d:", palette_idx);
    for (int i = 0; i < 3; ++i) {
        int c = VALID_PALETTES[palette_idx][i];
        SDL_Log("  layer %d: %-7s rgb=(%3d,%3d,%3d)",
                i, COLOR_NAMES[c],
                s->layers[i].tint.r,
                s->layers[i].tint.g,
                s->layers[i].tint.b);
    }

    menu_init(s);

    return SDL_APP_CONTINUE;
}'''
if 'menu_init(s)' not in s_main and old_init in s_main:
    s_main = s_main.replace(old_init, new_init, 1)
    changes += 1
    print("OK: menu_init в SDL_AppInit")

old_ev = '    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;\n'
new_ev = '''    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;

    // ── Меню (patch_40b) ──
    if (s->state == STATE_MENU || s->state == STATE_OPTIONS
        || s->state == STATE_NAME_INPUT || s->state == STATE_LEADERBOARD) {
        if (menu_handle_event(s, e)) {
            if (s->should_quit) return SDL_APP_SUCCESS;
        }
        return SDL_APP_CONTINUE;
    }
'''
if 'menu_handle_event' not in s_main and old_ev in s_main:
    s_main = s_main.replace(old_ev, new_ev, 1)
    changes += 1
    print("OK: menu_handle_event в SDL_AppEvent")

pat_123 = re.compile(
    r'    // ── Выбор сложности: 1/2/3 ──.*?'
    r'    if \(start_diff >= 0\) \{.*?return SDL_APP_CONTINUE;\s*\}\s*\n',
    re.DOTALL)
s2, n123 = pat_123.subn('    // (1/2/3 handlers removed in patch_40b — use OPTIONS)\n\n',
                        s_main, count=1)
if n123:
    s_main = s2; changes += 1; print("OK: 1/2/3 handlers removed")

old_space = 'if (s->state == STATE_MENU || s->state == STATE_GAME_OVER || s->state == STATE_SCORE) {'
new_space = 'if (s->state == STATE_GAME_OVER || s->state == STATE_SCORE) {'
s2 = s_main.replace(old_space, new_space, 1)
if s2 != s_main:
    s_main = s2; changes += 1
    print("OK: SPACE handler — STATE_MENU removed")

pat_iter = re.compile(
    r'(SDL_AppResult SDL_AppIterate\(void\* appstate\) \{\s*\n'
    r'\s*auto\* s = static_cast<AppState\*>\(appstate\);\s*\n)',
    re.MULTILINE)
early_block = '''
    // ── Меню (patch_40b): early-return для MENU/OPTIONS ──
    if (s->state == STATE_MENU || s->state == STATE_OPTIONS) {
        static Uint64 last_menu_tick = 0;
        Uint64 now_menu = SDL_GetTicks();
        if (last_menu_tick == 0) last_menu_tick = now_menu;
        float menu_dt = (now_menu - last_menu_tick) / 1000.0f;
        last_menu_tick = now_menu;
        if (menu_dt > 0.1f) menu_dt = 0.1f;

        menu_update(s, menu_dt);
        SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
        SDL_RenderClear(s->renderer);
        menu_render(s->renderer, s);
        SDL_RenderPresent(s->renderer);
        return SDL_APP_CONTINUE;
    }

'''
if 'menu_early_return' not in s_main:
    s2, n = pat_iter.subn(r'\1' + early_block, s_main, count=1)
    if n:
        s_main = s2; changes += 1
        print("OK: menu early-return в SDL_AppIterate")
    else:
        print("FAIL: не нашли 'SDL_AppIterate(void* appstate) { auto* s = ...'")

p_main.write_text(s_main, encoding='utf-8')
print(f"\nВсего изменений: {changes}")

print("\n=== ВЕРИФИКАЦИЯ ===\n")
s_app = p_app.read_text(encoding='utf-8')
s_main = p_main.read_text(encoding='utf-8')
curr_lines = len(s_main.splitlines())
print(f"  строк в main.cpp: {curr_lines} (было 1057)")
if curr_lines < 1000:
    print("  !!! WARNING: файл подозрительно мал — возможно, сломан !!!")

checks = [
    ('app.h should_quit',           'should_quit' in s_app),
    ('app.h extern draw_text',      'void draw_text' in s_app),
    ('main.cpp #include menu.h',    '#include "menu.h"' in s_main),
    ('main.cpp menu_init',          'menu_init(s)' in s_main),
    ('main.cpp menu_render',        'menu_render(s->renderer' in s_main),
    ('main.cpp menu_update',        'menu_update(s, menu_dt)' in s_main),
    ('main.cpp menu_handle_event',  'menu_handle_event' in s_main),
    ('main.cpp без static draw_text', 'static void draw_text(' not in s_main),
    ('main.cpp без start_diff',     'start_diff' not in s_main),
    ('main.cpp SDL_AppIterate на месте', 'SDL_AppIterate' in s_main),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
