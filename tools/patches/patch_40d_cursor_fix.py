#!/usr/bin/env python3
"""patch_40d — курсор в меню: глиф '>' (код 50) в шрифте 5x7."""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text(encoding='utf-8')

has_gt = "b0 == '>'" in s
print("=== ДИАГНОСТИКА ===\n")
print(f"  глиф '>' (50) в glyphs: {'есть' if '> (50)' in s else 'НЕТ'}")
print(f"  draw_glyph bound 50:    {'да' if 'code > 50' in s else 'нет'}")
print(f"  обработка '>' в text:   {'есть' if has_gt else 'НЕТ'}")

changes = 0

# 1) glyphs — добавить '>' (код 50)
old_glyph_tail = '''    {0x15, 0x15, 0x15, 0x1F, 0x15, 0x15, 0x15},  // Ж (49)
};'''
new_glyph_tail = '''    {0x15, 0x15, 0x15, 0x1F, 0x15, 0x15, 0x15},  // Ж (49)
    {0x18, 0x1C, 0x1E, 0x1F, 0x1E, 0x1C, 0x18},  // > (50) cursor
};'''
if '> (50)' not in s:
    if old_glyph_tail in s:
        s = s.replace(old_glyph_tail, new_glyph_tail, 1)
        changes += 1
        print("OK: +глиф '>' (50) в glyphs")
    else:
        print("FAIL: хвост glyphs не совпал")

# 2) draw_glyph bound: > 49 → > 50
if 'code > 49' in s and 'code > 50' not in s:
    s = s.replace('code < 0 || code > 49', 'code < 0 || code > 50', 1)
    changes += 1
    print("OK: draw_glyph bound 49 → 50")

# 3) draw_text — обработка '>'
old_txt = "else if (b0 == ':') { code = 36; p++; }\n        else if (b0 == ' ')"
new_txt = "else if (b0 == ':') { code = 36; p++; }\n        else if (b0 == '>') { code = 50; p++; }\n        else if (b0 == ' ')"
if not has_gt:
    if old_txt in s:
        s = s.replace(old_txt, new_txt, 1)
        changes += 1
        print("OK: draw_text +обработка '>'")
    else:
        print("FAIL: фрагмент draw_text не совпал")

p.write_text(s, encoding='utf-8')
print(f"\nВсего изменений: {changes}")

print("\n=== ВЕРИФИКАЦИЯ ===\n")
s = p.read_text(encoding='utf-8')
checks = [
    ('глиф > (50) в glyphs',   '> (50)' in s),
    ('draw_glyph bound 50',    'code > 50' in s),
    ("draw_text + '>'",        "b0 == '>'" in s),
    ('старые глифы целы',      '(49)' in s and '(37)' in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
