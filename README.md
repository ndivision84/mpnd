# Moon Patrol ND

Реимплементация аркадной игры **Moon Patrol** (Irem, 1982) на **C++ / SDL3**.

Версия: **20261027**

## Быстрый старт

Шаги:

1. Установить зависимости (macOS):

    brew install sdl3 sdl3_image cmake

2. Сгенерировать ассеты из ROM (нужны легально приобретённые ROM-файлы).
   Положить ROM в orig_rom/ рядом с mpng_src/:

    python3 tools/decode_bg.py
    python3 tools/extract_level.py
    python3 tools/extract_known.py

3. Сборка:

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
    cmake --build build -j

4. Запуск:

    ./build/moon_patrol_nd.app/Contents/MacOS/moon_patrol_nd

## Управление

| Клавиша | Действие |
|---|---|
| ← → | движение |
| ↑ | прыжок |
| Space | стрельба (горизонтальная + вертикальная пуля) |
| P | пауза |
| G | game over (отладка) |
| R | restart |

## Структура

    mpng_src/
    ├── src/main.cpp              # вся игра (один файл, ~1200 строк)
    ├── CMakeLists.txt
    ├── tools/
    │   ├── analyze_mpatrol.py    # проверка CRC/энтропии ROM
    │   ├── decode_bg.py          # распаковка фонов
    │   ├── extract_level.py      # распаковка RLE-уровня
    │   ├── extract_known.py      # charset + HUD
    │   └── patches/              # история патчей (Python)
    ├── docs/
    │   ├── report.html           # полный технический отчёт
    │   └── analysis_report_v*.txt
    ├── assets/
    │   ├── tiles/                # генерируется (PNG)
    │   ├── levels/               # генерируется (JSON)
    │   └── sprites/              # опционально (ROM-спрайты)
    ├── third_party/nlohmann/     # json.hpp (header-only)
    ├── CHANGELOG.md
    └── VERSION

## Что готово

- 3 слоя параллакса + случайные палитры
- Звёздное небо (120 точек, параллакс)
- Луноход: движение, прыжок, стрельба
- NLO (тарелки), BOMBA (бомбы), препятствия (яма/камень/кратер)
- Счёт, пауза, game over, restart
- Полный реверс-инжиниринг (см. docs/report.html)

## Что в планах

- ROM-спрайты NLO/камней (MAME-скриншоты или декодирование mpb-*)
- HUD: TIME, CAUTION
- Уровни сложности (Easy/Normal/Hard)
- 3 жизни + game over loop

## Правовая заметка

ROM-файлы Moon Patrol © Irem / Williams. Они не входят в репозиторий и должны
быть приобретены/найдены пользователем отдельно. assets/* — производные
(декодированные) из ROM — не коммитятся в git (см. .gitignore), генерируются
локально. Код игры — независимая реимплементация, не содержит оригинальных ROM.

## Ссылки

- Репозиторий: https://github.com/ndivision84/mpnd
- Технический отчёт: docs/report.html
