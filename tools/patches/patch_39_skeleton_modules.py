#!/usr/bin/env python3
"""patch_39_skeleton_modules.py — скелет menu/scores/settings.

app.h:
  +ScoreEntry, +Settings
  GameState: STATE_ATTRACT → STATE_MENU (0), +OPTIONS(4), +NAME_INPUT(5), +LEADERBOARD(6)
  AppState: +menu_cursor, +options_cursor, +name_input[11], +settings,
            +top_scores, +leaderboard_return_state,
            +new_high_score, +menu_initialized
  +<string>, +<vector>

main.cpp:
  STATE_ATTRACT → STATE_MENU (переименование, логика та же)
"""
import re
from pathlib import Path

print("=== ДИАГНОСТИКА ===\n")

p_app = Path('src/app.h')
if not p_app.exists():
    print("FAIL: src/app.h не найден — примените patch_38 сначала")
    raise SystemExit(1)
s = p_app.read_text(encoding='utf-8')

if 'STATE_MENU' in s and 'ScoreEntry' in s:
    print("SKIP: app.h уже расширен")
else:
    print("OK: применяем к app.h")

    pre_enum = '''// ─── Меню, настройки, TOP-10 ────────────────────────────

struct ScoreEntry {
    std::string name;
    int         score = 0;
    char        zone = 'A';
    int         attempts = 3;
    std::string date;
};

struct Settings {
    std::string player_name = "PLAYER1";
    int         difficulty = 1;
    int         attempts   = 3;
};

enum GameState {'''
    if 'struct ScoreEntry' not in s:
        if 'enum GameState {' in s:
            s = s.replace('enum GameState {', pre_enum, 1)
            print("OK: +ScoreEntry, Settings")
        else:
            print("FAIL: enum GameState не найден")
            raise SystemExit(1)
    else:
        print("SKIP: ScoreEntry уже есть")

    old_enum = re.search(r'enum GameState\s*\{[^}]*\}', s, re.DOTALL)
    if old_enum:
        new_enum = '''enum GameState {
    STATE_MENU         = 0,
    STATE_PLAYING      = 1,
    STATE_GAME_OVER    = 2,
    STATE_SCORE        = 3,
    STATE_OPTIONS      = 4,
    STATE_NAME_INPUT   = 5,
    STATE_LEADERBOARD  = 6
};'''
        s = s[:old_enum.start()] + new_enum + s[old_enum.end():]
        print("OK: GameState — STATE_MENU, +3 состояния")
    else:
        print("FAIL: enum GameState не найден")
        raise SystemExit(1)

    old_tail = '''    float         world_x = 0.0f;
    float         auto_speed = 80.0f;
};'''
    new_tail = '''    float         world_x = 0.0f;
    float         auto_speed = 80.0f;

    int   menu_cursor    = 0;
    int   options_cursor = 0;
    char  name_input[11] = {0};

    Settings settings;

    std::vector<ScoreEntry> top_scores;
    GameState leaderboard_return_state = STATE_MENU;

    bool  new_high_score   = false;
    bool  menu_initialized = false;
};'''
    if 'menu_cursor' not in s and old_tail in s:
        s = s.replace(old_tail, new_tail, 1)
        print("OK: AppState +меню/settings/top_scores")
    elif 'menu_cursor' in s:
        print("SKIP: AppState уже расширен")
    else:
        print("WARN: хвост AppState не совпал")

    if '#include <string>' not in s:
        s = s.replace('#include <cstdint>',
                      '#include <cstdint>\n#include <string>\n#include <vector>', 1)
        print("OK: +<string>, +<vector>")

    p_app.write_text(s, encoding='utf-8')

p_main = Path('src/main.cpp')
s2 = p_main.read_text(encoding='utf-8')
n = len(re.findall(r'\bSTATE_ATTRACT\b', s2))
print(f"\n  STATE_ATTRACT в main.cpp: {n}")
if n > 0:
    s2 = re.sub(r'\bSTATE_ATTRACT\b', 'STATE_MENU', s2)
    p_main.write_text(s2, encoding='utf-8')
    print(f"OK: переименовано ({n} мест)")
else:
    print("SKIP: уже переименован")

print("\n=== ВЕРИФИКАЦИЯ ===\n")
s_app = p_app.read_text(encoding='utf-8')
s_main = p_main.read_text(encoding='utf-8')
checks = [
    ('ScoreEntry',           'struct ScoreEntry' in s_app),
    ('Settings',             'struct Settings' in s_app),
    ('STATE_MENU',           'STATE_MENU' in s_app),
    ('STATE_OPTIONS',        'STATE_OPTIONS' in s_app),
    ('STATE_NAME_INPUT',     'STATE_NAME_INPUT' in s_app),
    ('STATE_LEADERBOARD',    'STATE_LEADERBOARD' in s_app),
    ('menu_cursor',          'menu_cursor' in s_app),
    ('top_scores',           'top_scores' in s_app),
    ('<vector>',             '#include <vector>' in s_app),
    ('main.cpp без ATTRACT', 'STATE_ATTRACT' not in s_main),
    ('main.cpp с MENU',      'STATE_MENU' in s_main),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
