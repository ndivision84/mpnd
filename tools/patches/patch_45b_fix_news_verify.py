#!/usr/bin/env python3
"""patch_45b — fix hard-coded verify в patch_43 (динамическая проверка)."""
from pathlib import Path
import ast

p = Path('tools/patches/patch_43_news_html_v2.py')
if not p.exists():
    print("FAIL: patch_43_news_html_v2.py не найден")
    raise SystemExit(1)

s = p.read_text(encoding='utf-8')
print("  patch_43: %d строк" % len(s.splitlines()))

has_old = "first_date == '2026-11-04'" in s
has_new = "max(art['date'] for art in articles)" in s

print("  hard-coded check: %s" % ("есть" if has_old else "нет"))
print("  dynamic check:    %s" % ("есть" if has_new else "нет"))

changes = 0

old_line = "    ('первая статья = 2026-11-04',   first_date == '2026-11-04'),"
new_line = "    ('первая статья = самая новая',  first_date == max(art['date'] for art in articles)),"

if has_old:
    if old_line in s:
        s = s.replace(old_line, new_line, 1)
        changes += 1
        print("OK: hard-coded → max(dates)")
    else:
        print("WARN: точная строка не найдена — ищем вариант...")
        import re
        pat = re.compile(r"\('первая статья = 2026-11-04',\s*first_date == '2026-11-04'\),")
        s2, n = pat.subn(new_line, s, count=1)
        if n:
            s = s2
            changes += 1
            print("OK: hard-coded → max(dates) (regex)")
elif has_new:
    print("SKIP: уже динамическая")
else:
    print("WARN: не нашли ни old, ни new — проверьте вручную")

p.write_text(s, encoding='utf-8')
print("\nВсего изменений: %d" % changes)

# Верификация
s = p.read_text(encoding='utf-8')
print("\n=== ВЕРИФИКАЦИЯ ===\n")
checks = [
    ("hard-coded убран",       "first_date == '2026-11-04'" not in s),
    ("динамическая проверка",  "max(art['date'] for art in articles)" in s),
]
ok = 0
for name, cond in checks:
    print("  [%s] %s" % ("OK " if cond else "FAIL", name))
    if cond: ok += 1
print("\nИтог: %d/%d" % (ok, len(checks)))

try:
    ast.parse(s)
    print("\nSYNTAX OK")
except SyntaxError as e:
    print("\nSYNTAX ERROR: %s" % e)
