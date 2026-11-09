#!/usr/bin/env python3
"""patch_45h_readme_update.py — обновляет README.md (2026-11-09).

- Добавляет Note / Примечание: не 1:1, творческая ND, исследовательская
- Добавляет раздел Research tracks (13 треков)
- Убирает Version / Версия: 20261105
- Меняет ссылки Documentation на site URLs (darkthrone.mooo.com/mpnd/)
- Оставляет Quick start (через 4-пробельный отступ, без backticks)
- Убирает раздел Links / Ссылки

Идемпотентно: если README уже содержит маркер "Research tracks" — SKIP.
Defensive: если README.md не найден — FAIL, exit 1.
"""
from pathlib import Path
import sys

README = Path("README.md")
MARKER = "## Research tracks / Исследовательские треки"

NEW_CONTENT = """# Moon Patrol ND

A reimplementation of the arcade classic Moon Patrol (Irem, 1982) in C++ / SDL3.

Реимплементация аркадной игры Moon Patrol (Irem, 1982) на C++ / SDL3.

## Note / Примечание

This is **not an exact reproduction** of the arcade original. It is a **creative authorial version (ND)** — a research and experimental reimagining, with no claim to 1:1 fidelity. There will be no traditional final version — only a final release.

Это **не точная копия** оригинальной аркады, а **творческая авторская версия (ND)** — исследовательская и экспериментальная. Проект не претендует на 1:1-воспроизведение. Конечной версии как таковой не будет — будет финальный релиз.

## Research tracks / Исследовательские треки

Chats working on reverse-engineering of the original arcade and its ports to various platforms:

Чаты с реверс-инжинирингом оригинальной игры и её версий для различных платформ:

- Arcade (Irem M52) — original / оригинал
- Atari 2600
- Atari 5200
- Atari 8-bit (400/800/XL/XE)
- Atari ST
- MSX
- Commodore 64
- Commodore VIC-20
- IBM PC (DOS)
- Apple II
- Sord M5
- TI-99/4A
- ZX Spectrum

## Documentation / Документация

- [Новости проекта / Project news](https://darkthrone.mooo.com/mpnd/news.html)
- [Описание проекта / Project description](https://darkthrone.mooo.com/mpnd/README.html)
- [Технический отчёт (Arcade) / Reverse-engineering report (Arcade)](https://darkthrone.mooo.com/mpnd/report.html)

## Quick start / Быстрый старт

    brew install sdl3 sdl3_image cmake
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
    cmake --build build -j
    ./build/moon_patrol_nd.app/Contents/MacOS/moon_patrol_nd
"""

print("=== ДИАГНОСТИКА (до) ===")
if not README.exists():
    print("FAIL: README.md не найден")
    sys.exit(1)

old = README.read_text(encoding="utf-8")
print("OK: README.md найден, длина:", len(old), "символов")
print("Уже обновлён:", MARKER in old)

if MARKER in old:
    print("SKIP: README.md уже обновлён")
    sys.exit(0)

backup = Path("/tmp/README.md.bak")
if not backup.exists():
    backup.write_text(old, encoding="utf-8")
    print("OK: бэкап сохранён в", backup)

print("=== ПРИМЕНЕНИЕ ===")
README.write_text(NEW_CONTENT, encoding="utf-8")
print("OK: README.md обновлён")

print("=== ВЕРИФИКАЦИЯ ===")
final = README.read_text(encoding="utf-8")
print("Длина после:", len(final))

checks = {
    "Note section": "## Note / Примечание" in final,
    "Not 1:1": "not an exact reproduction" in final,
    "Creative ND": "creative authorial version (ND)" in final,
    "Research tracks": MARKER in final,
    "Arcade listed": "Arcade (Irem M52)" in final,
    "Atari ST": "Atari ST" in final,
    "ZX Spectrum": "ZX Spectrum" in final,
    "TI-99/4A": "TI-99/4A" in final,
    "No version line": "Version / Версия" not in final,
    "Site link news": "darkthrone.mooo.com/mpnd/news.html" in final,
    "Site link readme": "darkthrone.mooo.com/mpnd/README.html" in final,
    "Site link report": "darkthrone.mooo.com/mpnd/report.html" in final,
    "Quick start kept": "brew install sdl3" in final,
    "Links removed": "## Links" not in final and "## Ссылки" not in final,
}
ok = True
for k, v in checks.items():
    print(("OK  " if v else "FAIL"), k)
    if not v:
        ok = False

if ok:
    print("OK: patch_45h применён успешно")
else:
    print("FAIL: проверка не прошла")
    sys.exit(1)
