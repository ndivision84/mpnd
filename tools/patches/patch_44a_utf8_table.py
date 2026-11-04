#!/usr/bin/env python3
"""patch_44a — гибрид UTF-8: CYR_MAP[] + 7 ASCII-символов (коды 51-57).

1. switch (b1) → цикл по CYR_MAP[] (−8 строк, +гибкость)
2. +7 глифов в glyphs: + - . _ / ( )  (коды 51-57)
3. draw_glyph bound: 50 → 57
4. draw_text: обработка 7 новых ASCII-символов
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text(encoding='utf-8')

print("=== ДИАГНОСТИКА ===\n")
print(f"  draw_text switch (b1): {'есть' if 'switch (b1)' in s else 'НЕТ'}")
print(f"  CYR_MAP уже есть:      {'да' if 'CYR_MAP' in s else 'нет'}")
print(f"  глиф + (51):           {'есть' if '+ (51)' in s else 'нет'}")
print(f"  bound 50:              {'да' if 'code > 50' in s else 'нет'}")
print(f"  bound 57:              {'да' if 'code > 57' in s else 'нет'}")

changes = 0

# ─── 1. glyphs: +7 символов после "> (50) cursor" ─────
old_tail = '''        {0x18, 0x1C, 0x1E, 0x1F, 0x1E, 0x1C, 0x18},  // > (50) cursor
    };'''
new_tail = '''        {0x18, 0x1C, 0x1E, 0x1F, 0x1E, 0x1C, 0x18},  // > (50) cursor
        {0x04, 0x04, 0x1F, 0x04, 0x04, 0x00, 0x00},  // + (51)
        {0x00, 0x00, 0x1F, 0x00, 0x00, 0x00, 0x00},  // - (52)
        {0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C},  // . (53)
        {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F},  // _ (54)
        {0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10},  // / (55)
        {0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02},  // ( (56)
        {0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08},  // ) (57)
    };'''
if '+ (51)' not in s:
    if old_tail in s:
        s = s.replace(old_tail, new_tail, 1)
        changes += 1
        print("OK: +7 глифов (51-57)")
    else:
        print("FAIL: хвост glyphs не совпал")
else:
    print("SKIP: глифы уже есть")

# ─── 2. draw_glyph bound: 50 → 57 ────────────────────
if 'code > 50' in s and 'code > 57' not in s:
    s = s.replace('code < 0 || code > 50', 'code < 0 || code > 57', 1)
    changes += 1
    print("OK: draw_glyph bound 50 → 57")

# ─── 3. CYR_MAP перед draw_text ──────────────────────
if 'CYR_MAP' not in s:
    # Ищем "void draw_text(SDL_Renderer*" (без static, после patch_40)
    m = re.search(r'^void draw_text\(SDL_Renderer\*', s, re.MULTILINE)
    if m:
        cyr_map = '''// UTF-8 кириллица → код глифа (U+0410..U+042F)
static const struct { uint8_t b1; int code; } CYR_MAP[] = {
    {0x90, 40}, {0x92, 41}, {0x95, 43}, {0x96, 49}, {0x97, 37},
    {0x98, 48}, {0x9A, 47}, {0x9C, 44}, {0x9D, 39}, {0x9E, 38},
    {0xA0, 42}, {0xA7, 46}, {0xAF, 45},
};

'''
        s = s[:m.start()] + cyr_map + s[m.start():]
        changes += 1
        print("OK: +CYR_MAP (13 пар)")
    else:
        print("FAIL: draw_text не найден (без static)")

# ─── 4. switch (b1) → цикл по CYR_MAP ────────────────
pat_switch = re.compile(
    r'(unsigned char b1 = \(unsigned char\)\*\(p\+1\);\n)'
    r'(\s+)switch \(b1\) \{.*?\n\s*\}\n',
    re.DOTALL)
def repl_switch(m):
    head = m.group(1)
    ind = m.group(2)
    body = (ind + 'for (auto& entry : CYR_MAP) {\n'
            + ind + '    if (entry.b1 == b1) { code = entry.code; break; }\n'
            + ind + '}\n')
    return head + body

if 'switch (b1)' in s:
    s2, n = pat_switch.subn(repl_switch, s, count=1)
    if n:
        s = s2; changes += 1
        print("OK: switch (b1) → цикл по CYR_MAP")
    else:
        print("FAIL: switch (b1) не совпал по паттерну")

# ─── 5. draw_text: +7 ASCII-символов ─────────────────
anchor = "        else if (b0 == '>') { code = 50; p++; }\n"
add_ascii = anchor + '''        else if (b0 == '+') { code = 51; p++; }
        else if (b0 == '-') { code = 52; p++; }
        else if (b0 == '.') { code = 53; p++; }
        else if (b0 == '_') { code = 54; p++; }
        else if (b0 == '/') { code = 55; p++; }
        else if (b0 == '(') { code = 56; p++; }
        else if (b0 == ')') { code = 57; p++; }
'''
if "b0 == '+'" not in s:
    if anchor in s:
        s = s.replace(anchor, add_ascii, 1)
        changes += 1
        print("OK: +7 ASCII-символов в draw_text")
    else:
        print("FAIL: anchor '>' не найден")

p.write_text(s, encoding='utf-8')
print(f"\nВсего изменений: {changes}")

# ─── Верификация ─────────────────────────────────────
print("\n=== ВЕРИФИКАЦИЯ ===\n")
s = p.read_text(encoding='utf-8')
checks = [
    ('CYR_MAP[] есть',            'CYR_MAP[]' in s),
    ('switch (b1) удалён',        'switch (b1)' not in s),
    ('for по CYR_MAP',            'for (auto& entry : CYR_MAP)' in s),
    ('глиф + (51)',               '+ (51)' in s),
    ('глиф ) (57)',               ') (57)' in s),
    ('bound 57',                  'code > 57' in s),
    ("draw_text '+'",             "b0 == '+'" in s),
    ("draw_text ')'",             "b0 == ')'" in s),
    ('кириллица работает',        "b0 == 0xD0" in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
