#!/usr/bin/env python3
"""patch_44b — глиф '<' (код 58) — левая стрелка для OPTIONS."""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text(encoding='utf-8')

print("=== ДИАГНОСТИКА ===\n")
print(f"  глиф < (58):  {'есть' if '< (58)' in s else 'НЕТ'}")
print(f"  bound 57:     {'да' if 'code > 57' in s else 'нет'}")
print(f"  bound 58:     {'да' if 'code > 58' in s else 'нет'}")

changes = 0

# 1) глиф '<' (58)
old_tail = '''        {0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08},  // ) (57)
    };'''
new_tail = '''        {0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08},  // ) (57)
        {0x10, 0x08, 0x04, 0x02, 0x04, 0x08, 0x10},  // < (58) left arrow
    };'''
if '< (58)' not in s:
    if old_tail in s:
        s = s.replace(old_tail, new_tail, 1)
        changes += 1
        print("OK: +глиф '<' (58)")
    else:
        print("FAIL: хвост glyphs не совпал")

# 2) bound 57 → 58
if 'code > 57' in s and 'code > 58' not in s:
    s = s.replace('code < 0 || code > 57', 'code < 0 || code > 58', 1)
    changes += 1
    print("OK: bound 57 → 58")

# 3) draw_text: обработка '<'
anchor = "        else if (b0 == ')') { code = 57; p++; }\n"
new_anchor = anchor + "        else if (b0 == '<') { code = 58; p++; }\n"
if "b0 == '<'" not in s:
    if anchor in s:
        s = s.replace(anchor, new_anchor, 1)
        changes += 1
        print("OK: draw_text + '<'")
    else:
        print("FAIL: anchor ')' не найден")

p.write_text(s, encoding='utf-8')
print(f"\nВсего изменений: {changes}")

s = p.read_text(encoding='utf-8')
checks = [
    ('глиф < (58)',    '< (58)' in s),
    ('bound 58',       'code > 58' in s),
    ("draw_text '<'",  "b0 == '<'" in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
