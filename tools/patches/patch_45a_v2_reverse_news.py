#!/usr/bin/env python3
"""patch_45a_v2 — перевернуть NEWS.txt: новые сверху.

Стратегия:
  1. Убрать trailing empty (если файл заканчивается на \\n).
  2. Найти все даты (DATE_RE).
  3. Для каждой даты — «верхняя граница» = ближайший -/= разделитель выше.
  4. Блок i = lines[ups[i] : ups[i+1]] (или до конца для последнего).
  5. header = lines[:ups[0]].
  6. Развернуть блоки [art1, art2, art3] → [art3, art2, art1].
  7. Собрать: header + art3 + '' + art2 + '' + art1.
  8. Восстановить trailing \\n.

Работает с разнородными разделителями (---- и ====).
"""
import re
from pathlib import Path

DATE_RE = re.compile(r'^\s*\d{4}-\d{2}-\d{2}\s*·\s*v\d+\s*·')
SEP_RE  = re.compile(r'^[-=]{40,}$')

def is_sep(line):
    return bool(SEP_RE.match(line.strip()))

def reverse_news(text):
    lines = text.split('\n')
    trailing_nl = bool(lines) and lines[-1] == ''
    if trailing_nl:
        lines = lines[:-1]

    dates = [i for i, ln in enumerate(lines) if DATE_RE.match(ln)]
    if len(dates) < 2:
        return text, 0, len(dates), "SKIP (меньше 2 статей)"

    def find_up(idx):
        i = idx - 1
        while i >= 0:
            if is_sep(lines[i]):
                return i
            i -= 1
        return 0

    ups = [find_up(d) for d in dates]

    header = lines[:ups[0]] if ups[0] > 0 else []

    blocks = []
    for i in range(len(dates)):
        start = ups[i]
        end = ups[i+1] if i+1 < len(dates) else len(lines)
        blocks.append(lines[start:end])

    def strip_trail(blk):
        while blk and blk[-1].strip() == '':
            blk = blk[:-1]
        return blk

    blocks_rev = [strip_trail(b) for b in reversed(blocks)]

    result = list(header)
    for i, blk in enumerate(blocks_rev):
        if i > 0:
            result.append('')
        result.extend(blk)

    output = '\n'.join(result)
    if trailing_nl:
        output += '\n'

    return output, len(blocks), len(dates), "OK"

p = Path('NEWS.txt')
text = p.read_text(encoding='utf-8')

print("=== ДИАГНОСТИКА ===\n")
lines_before = text.split('\n')
dates_before = [ln.strip()[:10] for ln in lines_before if DATE_RE.match(ln)]
print(f"  строк (split): {len(lines_before)}")
print(f"  дат найдено:   {len(dates_before)}")
print(f"  порядок:       {dates_before}")

if dates_before == sorted(dates_before, reverse=True):
    print("\nSKIP: уже в порядке «новые сверху»")
    raise SystemExit(0)

output, n_blocks, n_dates, status = reverse_news(text)

if n_blocks < 2:
    print(f"\nFAIL: {status}")
    raise SystemExit(1)

p.write_text(output, encoding='utf-8')
print(f"\nOK: {n_blocks} статей перевёрнуты")

print("\n=== ВЕРИФИКАЦИЯ ===\n")
lines_after = output.split('\n')
dates_after = [ln.strip()[:10] for ln in lines_after if DATE_RE.match(ln)]
print(f"  строк (split): {len(lines_after)} (было {len(lines_before)})")
print(f"  дат найдено:   {len(dates_after)}")
print(f"  порядок:       {dates_after}")

checks = [
    ('3 даты',                       len(dates_after) == 3),
    ('порядок 11-05, 11-04, 10-30',  dates_after == ['2026-11-05', '2026-11-04', '2026-10-30']),
    ('строк столько же',             len(lines_after) == len(lines_before)),
    ('первая ==== после header',     lines_after[0].startswith('=')),
    ('финал =====',                  lines_after[-1].strip() == '' or lines_after[-2].startswith('=')),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
