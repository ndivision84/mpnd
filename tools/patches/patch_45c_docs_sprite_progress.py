#!/usr/bin/env python3
"""patch_45c_docs_sprite_progress.py — NEWS + README для MPND_ART_ROM.

Добавляет в NEWS.txt статью про инфраструктуру извлечения спрайтов из ROM
(работа велась в чате "Moon Patrol Reversing (Arcade)").

Обновляет README.html:
  - "Что в планах": спрайты → MPND_ART_ROM + "инфраструктура готова"
  - "Структура": +extract_patterns.py, +README.md
"""
import sys
from pathlib import Path

NEWS_ARTICLE = """================================================================================
 2026-11-05 · v20261105 · «SPRITE EXTRACTION (MPND_ART_ROM)»
================================================================================

▸ КОНТЕКСТ

• Работа велась в чате «Moon Patrol Reversing (Arcade)»
• Цель: извлечь PNG-спрайты (луноход, НЛО, кратер, яма, камень) из ROM
• Итог сессии 1: инфраструктура экстракции готова, идентификация тайлов — в работе

▸ ИНСТРУМЕНТ (tools/extract_patterns.py)

• ~300 строк, pure stdlib (argparse, struct, pathlib, zlib) — без зависимостей
• Читает 5 графических банков mpe-1.3l … mpe-5.3e (5 × 4096 байт = 1280 тайлов 8×8)
• Формат: planar 2bpp 8×8 (MAME m52.cpp tiles8x8_layout), MSB-first
• CLI: --bank N, --cards, --force, --rom-dir, --out-dir, --pics-dir
• Декодер проверен: шрифт A-Z и цифры 1-9 видны без искажений

▸ ДОКУМЕНТАЦИЯ И ИНФРАСТРУКТУРА

• tools/README.md — запуск, формат тайла, связка с ND Dev, правовая заметка
• tools/patches/patch_01_pics_mirror.py — идемпотентный патч (--pics-dir)
• .gitignore: +assets/patterns/, +__pycache__/, +*.pyc
• PNG-зеркало для чата: ~/Downloads/mpng/pics/ (255 PNG, вне git)

▸ ЧТО ВЫЯСНЕНО (визуальный анализ 5 банков)

• 0xF3 (bank 2) = дорога/земля (подтверждено)
• Шрифт A-Z — bank 3 (0x20-0x2F), цифры 1-9 — bank 4 (0x10-0x1F)
• Параллакс (горы) — bank 3/4 (0x40-0x6F)
• НЛО — гипотеза: bank 4 (0xC0-0xFF), круглые купола
• Луноход — гипотеза: bank 0 (0x40-0x4F), силуэты деталей
• Кратер (0x26) и камень (0x27) из отчёта 23.4 — НЕ подтверждены
  - 0x26 в bank 2 = фрагмент, 0x27 = пусто
  - вывод: 0x26/0x27 — это Screen RAM ID, а не gfx-номер
  - при экстракции нужна визуальная идентификация по банкам

▸ КОММИТЫ (Reversing Arcade)

• 5277a02  tools: extract_patterns --pics-dir + patch_01_pics_mirror
• 76b9bf9  chore: dedupe assets/patterns rule in .gitignore

▸ ЧТО ДАЛЬШЕ (в чате Reversing Arcade)

• [1] Идентифицировать кратер/камень/яму (bank 0/1/3/4 + mp-s1.1a)
• [2] Подтвердить НЛО (bank 4) и луноход (bank 0)
• [3] docs/sprites_manifest.md — таблица: файл, размер, origin, кадры, палитра
• [4] tools/extract_sprites.py — сборка 8×8 тайлов в цельные PNG объектов
• [5] assets/sprites/*.png — buggy, nlo, crater, pit, rock (ND Dev ждёт)

▸ ДЛЯ ND DEV

• После готовности PNG — patch_49_integrate_sprites.py:
  - draw_buggy() → SDL_RenderTexture
  - render.cpp с IMG_Load
  - z-order/позиции по sprites_map
• Интеграция не блокирует текущую работу (patch_45/46/47/48)

================================================================================
"""

print("=== ДИАГНОСТИКА ===\n")

# ─── NEWS.txt ───
p_news = Path('NEWS.txt')
if not p_news.exists():
    print("FAIL: NEWS.txt не найден")
    sys.exit(1)
s_news = p_news.read_text(encoding='utf-8')

if 'SPRITE EXTRACTION (MPND_ART_ROM)' in s_news:
    print("SKIP: NEWS.txt — статья уже добавлена")
else:
    date_marker = ' 2026-11-05 · v20261105 · «OPTIONS READY»'
    date_pos = s_news.find(date_marker)
    if date_pos < 0:
        print("FAIL: маркер OPTIONS READY не найден в NEWS.txt")
        sys.exit(1)
    line_before = s_news.rfind('\n', 0, date_pos) + 1
    s_news = s_news[:line_before] + NEWS_ARTICLE.rstrip() + '\n\n' + s_news[line_before:]
    p_news.write_text(s_news, encoding='utf-8')
    print("OK: NEWS.txt — статья добавлена (prepend)")

# ─── README.html ───
p_readme = Path('README.html')
if not p_readme.exists():
    print("FAIL: README.html не найден")
    sys.exit(1)
s_readme = p_readme.read_text(encoding='utf-8')

changes_readme = 0

# 1) Планы: спрайты → MPND_ART_ROM
old_plan = ('<tr><td>5</td><td>Спрайты: луноход, NLO, препятствия, бомба</td>'
            '<td><strong>MPND_ART</strong></td></tr>\n'
            '    <tr><td>6</td><td>Заставки START и GAME OVER</td>'
            '<td><strong>MPND_ART</strong></td></tr>')
new_plan = ('<tr><td>5</td><td>Спрайты из ROM '
            '(инфраструктура готова: <code>tools/extract_patterns.py</code>)</td>'
            '<td><strong>MPND_ART_ROM</strong></td></tr>\n'
            '    <tr><td>6</td><td>Заставки START и GAME OVER (рисование с нуля)</td>'
            '<td><strong>MPND_ART</strong></td></tr>')

if 'MPND_ART_ROM' in s_readme:
    print("SKIP: README.html — планы уже обновлены (MPND_ART_ROM)")
elif old_plan in s_readme:
    s_readme = s_readme.replace(old_plan, new_plan, 1)
    changes_readme += 1
    print("OK: README.html — планы обновлены (MPND_ART_ROM)")
else:
    print("WARN: README.html — старая строка планов не совпала")

# 2) Структура: +extract_patterns.py, +README.md
old_struct = ('│   ├── extract_level.py      # распаковка RLE-уровня\n'
              '│   ├── extract_known.py      # charset + HUD')
new_struct = ('│   ├── extract_level.py      # распаковка RLE-уровня\n'
              '│   ├── extract_known.py      # charset + HUD\n'
              '│   ├── extract_patterns.py   # ROM → PNG (5 gfx-банков, 1280 тайлов)\n'
              '│   ├── README.md             # документация инструментов')

if '# ROM → PNG' in s_readme and 'extract_patterns.py' in s_readme:
    print("SKIP: README.html — структура уже обновлена")
elif old_struct in s_readme:
    s_readme = s_readme.replace(old_struct, new_struct, 1)
    changes_readme += 1
    print("OK: README.html — структура обновлена (+extract_patterns.py, +README.md)")
else:
    print("WARN: README.html — старая структура не совпала")

if changes_readme > 0:
    p_readme.write_text(s_readme, encoding='utf-8')

# ─── Верификация ───
print("\n=== ВЕРИФИКАЦИЯ ===\n")

s_news = p_news.read_text(encoding='utf-8')
s_readme = p_readme.read_text(encoding='utf-8')

pos_sprite = s_news.find('SPRITE EXTRACTION (MPND_ART_ROM)')
pos_options = s_news.find('OPTIONS READY')

checks = [
    ('NEWS: статья SPRITE EXTRACTION',  pos_sprite > 0),
    ('NEWS: SPRITE выше OPTIONS',       pos_sprite > 0 and pos_sprite < pos_options),
    ('README: MPND_ART_ROM',            'MPND_ART_ROM' in s_readme),
    ('README: extract_patterns.py',     'extract_patterns.py' in s_readme),
    ('README: ROM → PNG комментарий',   '# ROM → PNG' in s_readme),
]

ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
