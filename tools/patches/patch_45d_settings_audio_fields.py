#!/usr/bin/env python3
"""patch_45d — добавить audio-поля в struct Settings (app.h).

Для MPND_SOUND (см. docs/audio_design.md).
"""
import sys
from pathlib import Path

p = Path('src/app.h')
if not p.exists():
    print("FAIL: src/app.h не найден")
    sys.exit(1)
s = p.read_text(encoding='utf-8')

print("=== ДИАГНОСТИКА (до) ===\n")
print("  music_volume: %s" % ("есть" if 'music_volume' in s else "НЕТ"))
print("  sfx_volume:   %s" % ("есть" if 'sfx_volume' in s else "НЕТ"))
print("  muted:        %s" % ("есть" if 'muted' in s else "НЕТ"))

if 'music_volume' in s:
    print("\nSKIP: audio-поля уже добавлены")
    sys.exit(0)

old = """struct Settings {
    std::string player_name = "PLAYER1";
    int         difficulty = 1;   // 0=EASY, 1=NORMAL, 2=HARD
    int         attempts   = 3;   // 1, 3, 7
};"""

new = """struct Settings {
    std::string player_name = "PLAYER1";
    int         difficulty = 1;   // 0=EASY, 1=NORMAL, 2=HARD
    int         attempts   = 3;   // 1, 3, 7

    // Audio (patch_45d, для MPND_SOUND)
    int         music_volume = 100;  // 0-100
    int         sfx_volume   = 100;  // 0-100
    int         muted        = 0;    // 0/1
};"""

print("\n=== ПРИМЕНЕНИЕ ===\n")

if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding='utf-8')
    print("OK: audio-поля добавлены в struct Settings")
else:
    old2 = """struct Settings {
    std::string player_name = "PLAYER1";
    int         difficulty = 1;
    int         attempts   = 3;
};"""
    if old2 in s:
        new2 = """struct Settings {
    std::string player_name = "PLAYER1";
    int         difficulty = 1;
    int         attempts   = 3;

    // Audio (patch_45d, для MPND_SOUND)
    int         music_volume = 100;
    int         sfx_volume   = 100;
    int         muted        = 0;
};"""
        s = s.replace(old2, new2, 1)
        p.write_text(s, encoding='utf-8')
        print("OK: audio-поля добавлены (fallback)")
    else:
        print("FAIL: struct Settings не совпал")
        print("Пришлите: grep -A8 'struct Settings' src/app.h")
        sys.exit(1)

print("\n=== ВЕРИФИКАЦИЯ (после) ===\n")
s = p.read_text(encoding='utf-8')
checks = [
    ('music_volume',       'music_volume' in s),
    ('sfx_volume',         'sfx_volume' in s),
    ('muted',              'muted' in s),
    ('default music 100',  'music_volume = 100' in s),
    ('default sfx 100',    'sfx_volume   = 100' in s),
    ('default muted 0',    'muted        = 0' in s),
]
ok = 0
for name, cond in checks:
    print("  [%s] %s" % ("OK " if cond else "FAIL", name))
    if cond: ok += 1
print("\nИтог: %d/%d" % (ok, len(checks)))
