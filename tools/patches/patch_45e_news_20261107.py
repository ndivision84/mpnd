#!/usr/bin/env python3
"""patch_45e_news_20261107.py — добавляет две новости в NEWS.txt (prepend).

- 2026-11-07: Расширение исследовательских треков (+11 платформ)
- 2026-11-05: Открытие чата Moon Patrol Sound

Идемпотентно: повторный запуск — SKIP для уже добавленных статей.
Формат совместим с patch_43_news_html_v2.py.
"""
from pathlib import Path
import sys

NEWS_PATH = Path("NEWS.txt")
TITLE_1 = "Расширение исследовательских треков: +11 платформ"
TITLE_2 = "Открытие чата Moon Patrol Sound"

# === ДИАГНОСТИКА (до) ===
print("=== ДИАГНОСТИКА (до) ===")
if not NEWS_PATH.exists():
    print("FAIL: NEWS.txt не найден")
    sys.exit(1)

original = NEWS_PATH.read_text(encoding="utf-8")
print("OK: NEWS.txt найден, длина:", len(original), "символов")

has_tracks = TITLE_1 in original
has_sound = TITLE_2 in original
print("Статья 'Треки' уже есть:", has_tracks)
print("Статья 'Sound' уже есть:", has_sound)

# === ПРИМЕНЕНИЕ ===
print("=== ПРИМЕНЕНИЕ ===")

articles_text = ""

if not has_tracks:
    articles_text += (
        "================================\n"
        " 2026-11-07 · v20261105 · «" + TITLE_1 + "»\n"
        "================================\n"
        "\n"
        " За последние два дня проект Moon Patrol ND подключил 11 новых\n"
        " исследовательских чатов, посвящённых реверс-инжинирингу версий\n"
        " Moon Patrol для классических платформ. Это расширяет базу\n"
        " знаний о том, как аркадная игра адаптировалась на разном\n"
        " железе.\n"
        "\n"
        " Новые треки:\n"
        " • Atari 5200 (MP-5200) — 6502C, ANTIC/GTIA, POKEY\n"
        " • MSX (MP-MSX) — Z80, TMS9918, AY-3-8910\n"
        " • Commodore 64 (MP-C64) — 6510, VIC-II, SID\n"
        " • Commodore VIC-20 (MP-VIC20) — 6502, VIC-I\n"
        " • IBM PC DOS (MP-DOS) — 8088, CGA, PC Speaker\n"
        " • Apple II (MP-APPLEII) — 6502, HGR, спикер (+ исходник)\n"
        " • Atari 8-bit (MP-A8B) — 6502C, ANTIC/GTIA, POKEY\n"
        " • Atari ST (MP-ST) — 68000, Shifter, YM2149\n"
        " • Sord M5 (MP-SORDM5) — Z80, TMS9918, SN76489\n"
        " • TI-99/4A (MP-TI99) — TMS9900, TMS9918, SN76489\n"
        " • ZX Spectrum (MP-ZX) — Z80, ULA, 1-битный beeper\n"
        "\n"
        " Каждый трек получил вводную документацию, регламент работ\n"
        " и план первой сессии (ROM recon).\n"
        "\n"
    )
    print("OK: подготовлена статья 1 (треки)")

if not has_sound:
    articles_text += (
        "================================\n"
        " 2026-11-05 · v20261105 · «" + TITLE_2 + "»\n"
        "================================\n"
        "\n"
        " Открыт рабочий чат Moon Patrol Sound (MP-SND), посвящённый\n"
        " музыке и звуковым эффектам игры. Подтверждена работа\n"
        " SDL3_mixer 3.2.4_1 (Homebrew). В origin/main добавлен\n"
        " docs/sounds_manifest.md (18 SFX + 4 музыкальных трека).\n"
        "\n"
        " Подготовлен skeleton audio.cpp/h и патч patch_49 для\n"
        " запуска. Зафиксированы границы зон: app.h — зона MP-DEV,\n"
        " audio.* — зона MP-SND. Следующие шаги: patch_50 (wiring),\n"
        " patch_51 (интеграция).\n"
        "\n"
    )
    print("OK: подготовлена статья 2 (Sound)")

if articles_text == "":
    print("SKIP: обе статьи уже присутствуют")
    sys.exit(0)

marker = "================================\n"
idx = original.find(marker)
if idx == -1:
    new_content = articles_text + original
    print("OK: статьи добавлены в начало (нет существующих статей)")
else:
    new_content = original[:idx] + articles_text + original[idx:]
    print("OK: статьи вставлены перед первой существующей")

NEWS_PATH.write_text(new_content, encoding="utf-8")
print("OK: NEWS.txt обновлён")

# === ВЕРИФИКАЦИЯ ===
print("=== ВЕРИФИКАЦИЯ ===")
final = NEWS_PATH.read_text(encoding="utf-8")
print("Длина после:", len(final))

ok1 = TITLE_1 in final
ok2 = TITLE_2 in final
print("Статья 1 присутствует:", ok1)
print("Статья 2 присутствует:", ok2)

i1 = final.find(TITLE_1)
i2 = final.find(TITLE_2)
found1 = (i1 == abs(i1))
found2 = (i2 == abs(i2))
order_ok = found1 and found2 and (i1 == min(i1, i2)) and (i1 != i2)
print("Порядок (2026-11-07 до 2026-11-05):", order_ok)

if ok1 and ok2 and order_ok:
    print("OK: patch_45e применён успешно")
else:
    print("FAIL: проверка не прошла")
    sys.exit(1)
