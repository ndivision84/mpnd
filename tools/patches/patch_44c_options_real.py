#!/usr/bin/env python3
"""patch_44c — реальный OPTIONS: DIFFICULTY + LIVES со стрелками.

Изменяет menu.cpp:
  - render_options: 5 строк с курсором, значениями, < >
  - handle_options_event: ↑↓ навигация, ←→ изменение, SPACE вход, ESC назад
"""
import re
from pathlib import Path

p = Path('src/menu.cpp')
s = p.read_text(encoding='utf-8')

print("=== ДИАГНОСТИКА ===\n")
print(f"  render_options:          {'есть' if 'render_options' in s else 'НЕТ'}")
print(f"  handle_options_event:    {'есть' if 'handle_options_event' in s else 'НЕТ'}")
print(f"  нов. render (DIFFICULTY:):{'есть' if 'DIFFICULTY:' in s else 'нет'}")
print(f"  <string>:                {'есть' if '#include <string>' in s else 'нет'}")

changes = 0

# 1) #include <string> (для std::to_string)
if '#include <string>' not in s:
    s = s.replace('#include "menu.h"', '#include "menu.h"\n#include <string>', 1)
    changes += 1
    print("OK: +<string>")

# 2) заменить render_options
old_render = re.search(
    r'static void render_options\(SDL_Renderer\* r, AppState\* s\) \{.*?\n\}',
    s, re.DOTALL)
if not old_render:
    print("FAIL: render_options не найден")
    raise SystemExit(1)

new_render = '''static void render_options(SDL_Renderer* r, AppState* s) {
    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 80, "OPTIONS", 4.0f);

    draw_box(r, 100, 170, 600, 360, 0x00, 0x88, 0x44);

    constexpr float scale    = 2.5f;
    constexpr float x_cursor = 130.0f;
    constexpr float x_label  = 160.0f;
    constexpr float x_value  = 420.0f;

    static const char* diff_names[3] = { "EASY", "NORMAL", "HARD" };
    const char* diff_name = diff_names[s->settings.difficulty];
    std::string lives_str = std::to_string(s->settings.attempts);

    const char* labels[5] = {
        "DIFFICULTY:", "NAME:", "LIVES:", "TOP SCORES", "BACK"
    };
    const char* values[5] = {
        diff_name,
        s->settings.player_name.c_str(),
        lives_str.c_str(),
        "", ""
    };

    for (int i = 0; i < 5; ++i) {
        float y = 220.0f + i * 50.0f;
        bool selected = (i == s->options_cursor);

        // Курсор
        if (selected) {
            SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
            draw_text(r, x_cursor, y, ">", scale);
        }

        // Цвет строки
        if (selected) SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
        else          SDL_SetRenderDrawColor(r, 0x00, 0x88, 0x44, 255);

        // Метка
        draw_text(r, x_label, y, labels[i], scale);

        // Значение
        if (values[i][0] != 0) {
            bool has_arrows = (i == 0 || i == 2);  // DIFFICULTY или LIVES
            if (has_arrows) {
                float vw = text_width(values[i], scale);
                draw_text(r, x_value, y, "<", scale);
                draw_text(r, x_value + 20.0f, y, values[i], scale);
                draw_text(r, x_value + 20.0f + vw + 10.0f, y, ">", scale);
            } else {
                draw_text(r, x_value, y, values[i], scale);
            }
        }
    }

    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 520, "PRESS ESC", 2.5f);
}'''

s = s[:old_render.start()] + new_render + s[old_render.end():]
changes += 1
print("OK: render_options переписан (5 строк со значениями)")

# 3) заменить handle_options_event
old_ev = re.search(
    r'static bool handle_options_event\(AppState\* s, SDL_Event\* e\) \{.*?\n\}',
    s, re.DOTALL)
if not old_ev:
    print("FAIL: handle_options_event не найден")
    raise SystemExit(1)

new_ev = '''static bool handle_options_event(AppState* s, SDL_Event* e) {
    constexpr int ITEMS = 5;
    constexpr int VALS_LIVES[3] = { 1, 3, 7 };

    if (e->key.key == SDLK_UP) {
        s->options_cursor = (s->options_cursor + ITEMS - 1) % ITEMS;
        return true;
    }
    if (e->key.key == SDLK_DOWN) {
        s->options_cursor = (s->options_cursor + 1) % ITEMS;
        return true;
    }
    if (e->key.key == SDLK_LEFT || e->key.key == SDLK_RIGHT) {
        int dir = (e->key.key == SDLK_RIGHT) ? 1 : -1;
        if (s->options_cursor == 0) {  // DIFFICULTY
            s->settings.difficulty = (s->settings.difficulty + dir + 3) % 3;
            SDL_Log("DIFFICULTY: %d (EASY/NORMAL/HARD)", s->settings.difficulty);
        } else if (s->options_cursor == 2) {  // LIVES
            int idx = 1;
            for (int i = 0; i < 3; ++i) {
                if (VALS_LIVES[i] == s->settings.attempts) { idx = i; break; }
            }
            idx = (idx + dir + 3) % 3;
            s->settings.attempts = VALS_LIVES[idx];
            SDL_Log("LIVES: %d", s->settings.attempts);
        }
        return true;
    }
    if (e->key.key == SDLK_SPACE) {
        if (s->options_cursor == 1) {
            SDL_Log("OPTIONS -> NAME (patch_45 TODO)");
        } else if (s->options_cursor == 3) {
            SDL_Log("OPTIONS -> TOP SCORES (patch_46 TODO)");
        } else if (s->options_cursor == 4) {
            s->state = STATE_MENU;
            SDL_Log("OPTIONS -> MENU (BACK)");
        }
        return true;
    }
    if (e->key.key == SDLK_ESCAPE) {
        s->state = STATE_MENU;
        SDL_Log("OPTIONS -> MENU (ESC)");
        return true;
    }
    return true;
}'''

s = s[:old_ev.start()] + new_ev + s[old_ev.end():]
changes += 1
print("OK: handle_options_event переписан")

p.write_text(s, encoding='utf-8')
print(f"\nВсего изменений: {changes}")

# verification
s = p.read_text(encoding='utf-8')
checks = [
    ('render_options с DIFFICULTY:', 'DIFFICULTY:' in s),
    ('render_options с < >',         '"<"' in s and '">"' in s),
    ('handle ↑↓',                    'SDLK_UP' in s and 'SDLK_DOWN' in s),
    ('handle ←→',                    'SDLK_LEFT' in s and 'SDLK_RIGHT' in s),
    ('handle SPACE',                 'SDLK_SPACE' in s),
    ('handle ESC',                   'SDLK_ESCAPE' in s),
    ('difficulty изменяется',        'settings.difficulty = (s->settings.difficulty' in s),
    ('lives изменяется',             'settings.attempts = VALS_LIVES' in s),
    ('<string>',                     '#include <string>' in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
