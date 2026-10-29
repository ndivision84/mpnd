#!/usr/bin/env python3
"""patch_25_time_one_line.py — TIME и цифры на одной строке: "TIME: 51".

1. Добавить глиф ':' (code 36).
2. draw_text: обработка ':' → 36.
3. draw_hud: одна строка "TIME: XX" вместо двух.
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) Добавить глиф ':' (code 36) в конец таблицы glyphs
# ═══════════════════════════════════════════════════════════════
if '// : (36)' not in s and '//: (36)' not in s:
    old = "{0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F},  // Z (35)"
    new = """{0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F},  // Z (35)
        {0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00},  // : (36)"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: глиф ':' (36) добавлен")
    else:
        print("!! не найден конец таблицы glyphs (// Z (35))")

# ═══════════════════════════════════════════════════════════════
# 2) draw_text: обработка ':'
# ═══════════════════════════════════════════════════════════════
if "*p == ':') code = 36" not in s:
    old = "        else if (*p >= 'A' && *p <= 'Z') code = 10 + (*p - 'A');"
    new = """        else if (*p >= 'A' && *p <= 'Z') code = 10 + (*p - 'A');
        else if (*p == ':') code = 36;"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: draw_text + ':' (36)")

# ═══════════════════════════════════════════════════════════════
# 3) draw_glyph: bounds 25 → 36
# ═══════════════════════════════════════════════════════════════
n = s.count("if (code < 0 || code >= 36) return;")
if n == 0:
    # возможно, старая версия с <= 25
    for old, new in [
        ("if (code < 0 || code > 25) return;", "if (code < 0 || code > 36) return;"),
        ("if (code < 0 || code >= 36) return;", "if (code < 0 || code > 36) return;"),
    ]:
        if old in s:
            s = s.replace(old, new, 1); changes += 1
            print(f"OK: bounds → 36")
            break
else:
    # Уже >= 36, но должно быть > 36
    s = s.replace("if (code < 0 || code >= 36) return;", "if (code < 0 || code > 36) return;")
    changes += 1
    print("OK: bounds 36 → > 36")

# ═══════════════════════════════════════════════════════════════
# 4) draw_hud: одна строка "TIME: XX"
# ═══════════════════════════════════════════════════════════════
old = """    // TIME слева
    draw_text(r, 20, 20, "TIME", 4.0f);
    char tbuf[4];
    tbuf[0] = '0' + (time_left / 10) % 10;
    tbuf[1] = '0' + time_left % 10;
    tbuf[2] = 0;
    draw_text(r, 20, 54, tbuf, 4.0f);"""

new = """    // TIME: XX — одна строка слева
    char tbuf[9];
    tbuf[0] = 'T'; tbuf[1] = 'I'; tbuf[2] = 'M'; tbuf[3] = 'E';
    tbuf[4] = ':'; tbuf[5] = ' ';
    tbuf[6] = '0' + (time_left / 10) % 10;
    tbuf[7] = '0' + time_left % 10;
    tbuf[8] = 0;
    draw_text(r, 20, 20, tbuf, 4.0f);"""

if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: TIME и цифры на одной строке")
else:
    print("!! не найден блок TIME в draw_hud")

p.write_text(s)
print(f"\nИзменено: {changes}/4")
