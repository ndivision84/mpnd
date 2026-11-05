# tools/ — скрипты извлечения данных из ROM Moon Patrol

ROM-скрипты (в отличие от `tools/patches/`) читают бинарные данные из
`../orig_rom/` и генерируют PNG/JSON. Исходники ROM вне репо (© Irem/Williams).
Сгенерированные файлы — в `assets/` (gitignored).

## Требования

- Python 3.8+
- **Pure stdlib, no dependencies** (`argparse`, `struct`, `pathlib`, `zlib`).
- ROM-сет `mpatrol` (Irem) распакован в `../orig_rom/`
  (17 файлов, `mpa-*`, `mpb-*`, `mpc-*`, `mpe-*`, `mp-*`).

## extract_patterns.py

Нарезает все `mpe-*.bin` (5 банков × 4096 байт = 256 тайлов на банк) на
8×8 2bpp тайлы и складывает в контактные листы для визуального поиска.

### Запуск (из корня репо)

    # Только 5 листов (быстро)
    python3 tools/extract_patterns.py

    # Плюс увеличенные карточки для интересных диапазонов
    # (0x20-0x30 кратер/камень, 0xD0-0xE0 анимации, 0xF0-0xFF земля)
    python3 tools/extract_patterns.py --cards

    # Один банк
    python3 tools/extract_patterns.py --bank 1 --cards

    # Принудительная перезапись
    python3 tools/extract_patterns.py --force

### Что генерит

    assets/patterns/
    ├── bank0_sheet.png          # ~832x1010, 16x16 тайлов, x6 зум, подписи 0x00…0xFF
    ├── bank1_sheet.png
    ├── bank2_sheet.png
    ├── bank3_sheet.png
    ├── bank4_sheet.png
    └── interesting/
        ├── bank0_tile_0x26.png  # x10, 1 тайл, подпись "bank0 0x26"
        ├── bank0_tile_0x27.png
        └── …

### Как читать листы

- Фон sheets — тёмно-серый (#282828), тайлы в градациях серого:
  0=чёрный, 1=тёмно-серый, 2=светло-серый, 3=белый.
- Номер под тайлом — 0xNN, это ключ для docs/sprites_manifest.md.
- Ищите глазами: кратер 0x26 (в grayscale — светлые «языки» по краям),
  камень 0x27 (неровный силуэт), земля 0xF3 (плотный повторяющийся
  паттерн), ямы и половинки больших кратеров — в окрестностях 0x20-0x30
  и 0xD0-0xE0.

### Формат тайла (для отладки)

    planar 2bpp, MAME m52.cpp tiles8x8_layout:
      byte  0..7  — bitplane 0 для строк 0..7 (MSB-first: bit 7 = левый пиксель)
      byte  8..15 — bitplane 1 для строк 0..7
      pixel(x,y) = (bit1 << 1) | bit0   -> 0..3

Если на листе «каша» вместо узнаваемых форм — пришлите скриншот, поправим
decode_tile().

### Связка с ND Dev

Этот скрипт — разведка. Результаты (номера тайлов) идут в
docs/sprites_manifest.md, который использует основной проект
moon_patrol_nd для patch_49_integrate_sprites.py. Итоговые PNG для
SDL3 лежат в assets/sprites/ (генерируются отдельным
tools/extract_sprites.py, см. ND Dev-чат).

### Правовая заметка

ROM — © Irem/Williams. orig_rom/, assets/patterns/, assets/sprites/ —
в .gitignore. В git попадает только код скриптов и документация.

## --pics-dir (опционально)

Если нужно копировать все сгенерированные PNG в отдельный каталог
(например, для удобной отправки в чат), используйте:

    python3 tools/extract_patterns.py --cards --pics-dir ../pics

Каталог `../pics/` создастся автоматически. Структура сохраняется:
`../pics/bank0_sheet.png`, `../pics/interesting/bank0_tile_0x26.png` и т.д.
Сам скрипт по-прежнему пишет в `assets/patterns/` (gitignored),
`pics/` — просто зеркало для работы.
