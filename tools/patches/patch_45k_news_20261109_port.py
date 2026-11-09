#!/usr/bin/env python3
"""patch_45k_news_20261109_port.py — новость про Port (Dendy/УКНЦ), финальный текст.

- 2026-11-09: Новое направление Port: Dendy/NES/Famicom и УКНЦ
- Port-треки — отдельные крупные проекты (не «часть обкатки»)
- ND — тестовая (хакерская) для macOS, без официальных релизов

Идемпотентно: повторный запуск — SKIP.
"""
from pathlib import Path
import sys

NEWS = Path("NEWS.txt")
TITLE = "Новое направление Port: Dendy/NES/Famicom и УКНЦ"

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

print("=== ПРИМЕНЕНИЕ ===")

ARTICLE = (
    "================================\n"
    " 2026-11-09 · v20261105 · «" + TITLE + "»\n"
    "================================\n"
    "\n"
    " Открыто новое направление в проекте — Port (разработка с нуля).\n"
    " В отличие от 13 Reversing-треков, где разбираются существующие\n"
    " версии Moon Patrol с разных платформ, Port — это создание\n"
    " собственной игры для целевой платформы с написанием всего\n"
    " кода, графики и звука заново.\n"
    "\n"
    " Два новых чата:\n"
    " • Moon Patrol Port (Dendy) — Dendy / NES / Famicom, CPU 6502\n"
    " • Moon Patrol Port (УКНЦ) — УКНЦ («Электроника МС 0511»),\n"
    "   советский PDP-11-совместимый компьютер с двумя процессорами\n"
    "   КМ1801ВМ2\n"
    "\n"
    " Moon Patrol ND — тестовая (хакерская) версия для macOS.\n"
    " Официальных релизов не будет. На её основе обкатываем\n"
    " технологии разработки и эмуляции: геймплей, рендер,\n"
    " звук, портирование под разное железо.\n"
    "\n"
    " Port-треки — отдельные и очень крупные проекты. До этого\n"
    " Moon Patrol на Dendy/NES/Famicom и УКНЦ не существовало.\n"
    " Наша задача — сделать эти игры, написав их с нуля под\n"
    " конкретное железо: 6502 (Dendy) и PDP-11 (УКНЦ).\n"
    "\n"
    " Первые сессии: ROM-каркас для Dendy и skeleton для УКНЦ,\n"
    " фиксация ограничений платформ в port_report.md. Приоритет —\n"
    " средний. Детали — в вводных для соответствующих чатов.\n"
    "\n"
)

marker = "================================\n"
idx = original.find(marker)
if idx == -1:
    new_content = ARTICLE + original
    print("OK: статья добавлена в начало")
else:
    new_content = original[:idx] + ARTICLE + original[idx:]
    print("OK: статья вставлена перед первой существующей")

NEWS.write_text(new_content, encoding="utf-8")
print("OK: NEWS.txt обновлён")

print("=== ВЕРИФИКАЦИЯ ===")
final = NEWS.read_text(encoding="utf-8")
print("Длина после:", len(final))

checks = {
    "TITLE": TITLE in final,
    "отдельные крупные": "отдельные и очень крупные проекты" in final,
    "не существовало": "не существовало" in final,
    "тестовая хакерская": "тестовая (хакерская) версия для macOS" in final,
    "без релизов": "Официальных релизов не будет" in final,
    "PDP-11": "PDP-11" in final,
    "6502": "6502 (Dendy)" in final,
}
ok = True
for k, v in checks.items():
    print(("OK  " if v else "FAIL"), k)
    if not v:
        ok = False

if ok:
    i_new = final.find(TITLE)
    i_readme = final.find("README и сайт: творческая версия ND")
    order_ok = i_readme == -1 or i_new < i_readme
    print("Порядок (Port выше README):", order_ok)
    if order_ok:
        print("OK: patch_45k применён успешно")
    else:
        print("FAIL: порядок нарушен")
        sys.exit(1)
else:
    print("FAIL: проверка не прошла")
    sys.exit(1)
