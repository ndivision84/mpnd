#!/usr/bin/env python3
"""patch_01_pics_mirror.py — добавить опцию --pics-dir в tools/extract_patterns.py.

Если задана: после генерации все PNG (включая interesting/) копируются
в указанный каталог, сохраняя структуру. Оригиналы остаются в
assets/patterns/ (gitignored). Нужно для удобной отправки картинок в чат.

Идемпотентно: при повторном запуске — SKIP для уже применённых шагов.
"""

from pathlib import Path
import sys

TARGET = Path("tools/extract_patterns.py")

# ===== ДИАГНОСТИКА (до) =====
print("=== ДИАГНОСТИКА (до) ===")
if not TARGET.is_file():
    print(f"FAIL: нет файла {TARGET}")
    sys.exit(1)
s = TARGET.read_text(encoding="utf-8")
orig = s
print(f"  {TARGET}: {len(s.splitlines())} строк")

# ===== ПРИМЕНЕНИЕ =====
print("=== ПРИМЕНЕНИЕ ===")

# 1. import shutil
if "import shutil" in s:
    print("SKIP: import shutil уже есть")
else:
    if "import zlib\n" not in s:
        print("FAIL: не нашёл 'import zlib' — файл изменён?")
        sys.exit(1)
    s = s.replace("import zlib\n", "import shutil\nimport zlib\n", 1)
    print("OK: добавлен import shutil")

# 2. аргумент --pics-dir
if '"--pics-dir"' in s:
    print("SKIP: --pics-dir уже есть")
else:
    needle = "    args = ap.parse_args()\n"
    if needle not in s:
        print("FAIL: не нашёл 'args = ap.parse_args()'")
        sys.exit(1)
    repl = (
        '    ap.add_argument("--pics-dir", default=None,\n'
        '                    help="если задано — копировать все PNG сюда (для отправки)")\n'
        '    args = ap.parse_args()\n'
    )
    s = s.replace(needle, repl, 1)
    print("OK: добавлен аргумент --pics-dir")

# 3. переменная pics_dir
if "pics_dir = Path(args.pics_dir)" in s:
    print("SKIP: pics_dir уже объявлен")
else:
    needle = '    interesting_dir = out_dir / "interesting"\n'
    if needle not in s:
        print('FAIL: не нашёл строку с interesting_dir')
        sys.exit(1)
    s = s.replace(
        needle,
        needle + '    pics_dir = Path(args.pics_dir).resolve() if args.pics_dir else None\n',
        1,
    )
    print("OK: добавлен pics_dir")

# 4. финальный проход зеркалирования (перед итоговым print)
if "mirrored = 0" in s:
    print("SKIP: блок зеркалирования уже есть")
else:
    needle = '    suffix = f", карточек: {cards_count}" if args.cards else ""\n'
    if needle not in s:
        print("FAIL: не нашёл 'suffix = ...'")
        sys.exit(1)
    block = (
        '    if pics_dir is not None:\n'
        '        pics_dir.mkdir(parents=True, exist_ok=True)\n'
        '        mirrored = 0\n'
        '        for png in out_dir.rglob("*.png"):\n'
        '            rel = png.relative_to(out_dir)\n'
        '            dst = pics_dir / rel\n'
        '            dst.parent.mkdir(parents=True, exist_ok=True)\n'
        '            shutil.copy2(png, dst)\n'
        '            mirrored += 1\n'
        '        print(f"  OK: mirrored {mirrored} PNG -> {pics_dir}")\n'
        '\n'
    )
    s = s.replace(needle, block + needle, 1)
    print("OK: добавлен блок зеркалирования")

# ===== ВЕРИФИКАЦИЯ =====
print("=== ВЕРИФИКАЦИЯ ===")
if s == orig:
    print("OK: файл не изменён (всё уже было)")
    sys.exit(0)

TARGET.write_text(s, encoding="utf-8")
delta = len(s.splitlines()) - len(orig.splitlines())
print(f"OK: {TARGET} обновлён (+{delta} строк, теперь {len(s.splitlines())})")
