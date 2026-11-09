#!/usr/bin/env python3
"""patch_45j_news_20261109.py — добавляет новость 2026-11-09 в NEWS.txt (prepend).

- 2026-11-09: README и сайт: творческая версия ND, 13 треков

Идемпотентно: повторный запуск — SKIP.
Формат совместим с patch_43_news_html_v2.py.
"""
from pathlib import Path
import sys

NEWS = Path("NEWS.txt")
TITLE = "README и сайт: творческая версия ND, 13 треков"

# === ДИАГНОСТИКА ===
print("=== ДИАГНОСТИКА (до) ===")
if not NEWS.exists():
    print("FAIL: NEWS.txt не найден")
    sys.exit(1)

original = NEWS.read_text(encoding="utf-8")
print("OK: NEWS.txt найден, длина:", len(original))
print("Новость уже есть:", TITLE in original)

if TITLE in original:
    print("SKIP: новость уже добавлена")
    sys.exit(0)

# === ПРИМЕНЕНИЕ ===
print("=== ПРИМЕНЕНИЕ ===")

ARTICLE = (
    "================================\n"
    " 2026-11-09 · v20261105 · «" + TITLE + "»\n"
    "================================\n"
    "\n"
    " README проекта обновлён и синхронизирован с сайтом. Уточнена\n"
    " природа проекта: это творческая авторская версия (ND), не\n"
    " претендующая на 1:1-воспроизведение — исследовательский и\n"
    " экспериментальный реим.\n"
    "\n"
    " В README добавлен раздел «Research tracks / Исследовательские\n"
    " треки»: 13 треков по реверс-инжинирингу — оригинальная аркада\n"
    " (Irem M52) и версии для 12 платформ:\n"
    " Atari 2600, Atari 5200, Atari 8-bit (400/800/XL/XE), Atari ST,\n"
    " MSX, Commodore 64, Commodore VIC-20, IBM PC (DOS), Apple II,\n"
    " Sord M5, TI-99/4A, ZX Spectrum.\n"
    "\n"
    " Ссылки на документацию перенесены на сайт проекта\n"
    " (darkthrone.mooo.com/mpnd/). Раздел «Links» временно убран\n"
    " для переработки. «Quick start» сохранён без изменений.\n"
    "\n"
)

marker = "================================\n"
idx = original.find(marker)
if idx == -1:
    new_content = ARTICLE + original
    print("OK: статья добавлена в начало (нет существующих статей)")
else:
    new_content = original[:idx] + ARTICLE + original[idx:]
    print("OK: статья вставлена перед первой существующей")

NEWS.write_text(new_content, encoding="utf-8")
print("OK: NEWS.txt обновлён")

# === ВЕРИФИКАЦИЯ ===
print("=== ВЕРИФИКАЦИЯ ===")
final = NEWS.read_text(encoding="utf-8")
print("Длина после:", len(final))

if TITLE in final:
    i_new = final.find(TITLE)
    i_prev = final.find("Расширение исследовательских треков")
    order_ok = i_prev == -1 or i_new < i_prev
    print("Порядок newest-first:", order_ok)
    if order_ok:
        print("OK: patch_45j применён успешно")
    else:
        print("FAIL: порядок нарушен")
        sys.exit(1)
else:
    print("FAIL: новость не найдена")
    sys.exit(1)
