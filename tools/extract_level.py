#!/usr/bin/env python3
"""
extract_level.py — распаковка RLE-уровня Moon Patrol в JSON.

Семантика RLE (из handler #11 0x1218):

    byte == 3  — установить позицию экрана: 2 байта LE = адрес в Screen RAM.
                 Запоминаем базовую позицию (base) этой серии колонок.
    byte == 2  — переход к следующей колонке: base += 1, screen_pos = base.
                 Y сбрасывается к базовому (вершина колонки).
    byte == 1  — конец данных.
    byte == 0  — тайл 0x00 (пусто).
    byte >= 4  — тайл, записать в текущую позицию экрана.

Каждый записанный тайл сдвигает screen_pos на +32 (вниз по колонке).
"""

import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR   = SCRIPT_DIR.parent
ROM_FILE   = REPO_DIR / "orig_rom" / "mpa-3.3k"
OUT_FILE   = SCRIPT_DIR / "assets" / "levels" / "level1.json"

ROM_BASE     = 0x2000
LEVEL_START  = 0x2D44
SCREEN_START = 0x8000
SCREEN_END   = 0x8400
GRID_W       = 32
GRID_H       = 32
MAX_STEPS    = 20000


def extract(rom):
    offset = LEVEL_START - ROM_BASE
    grid = [[0] * GRID_W for _ in range(GRID_H)]
    screen_pos = None
    base = None
    stats = {"tiles": 0, "columns": 0, "positions": 0, "end": None, "end_off": None,
             "unique": set(), "out_of_grid": 0}
    steps = 0

    while True:
        if offset >= len(rom):
            stats["end"] = "EOF"; stats["end_off"] = offset; break
        if steps > MAX_STEPS:
            stats["end"] = "max steps"; stats["end_off"] = offset; break
        steps += 1

        b = rom[offset]
        offset += 1

        if b == 1:
            stats["end"] = "end marker 0x01"
            stats["end_off"] = offset - 1
            break

        if b == 2:
            stats["columns"] += 1
            if base is not None:
                base += 1
                screen_pos = base
            continue

        if b == 3:
            if offset + 2 > len(rom):
                stats["end"] = "truncated pointer"; stats["end_off"] = offset; break
            screen_pos = rom[offset] | (rom[offset + 1] << 8)
            base = screen_pos
            offset += 2
            stats["positions"] += 1
            if not (SCREEN_START <= screen_pos < SCREEN_END):
                stats["end"] = f"invalid start 0x{screen_pos:04X}"
                stats["end_off"] = offset - 2
                break
            continue

        # тайл
        if screen_pos is None or not (SCREEN_START <= screen_pos < SCREEN_END):
            stats["end"] = f"tile at bad pos 0x{screen_pos:04X}" if screen_pos else "tile before position"
            stats["end_off"] = offset - 1
            break

        off = screen_pos - SCREEN_START
        row, col = off // GRID_W, off % GRID_W
        if 0 <= row < GRID_H and 0 <= col < GRID_W:
            grid[row][col] = b
        else:
            stats["out_of_grid"] += 1
        stats["tiles"] += 1
        stats["unique"].add(b)
        screen_pos += GRID_W

    return grid, stats


def render_preview(grid):
    lines = []
    for row in range(GRID_H):
        line = ""
        for col in range(GRID_W):
            v = grid[row][col]
            if v == 0:
                line += " "
            elif v < 0x10:
                line += "."
            elif v < 0x30:
                line += "o"
            elif v < 0x80:
                line += "x"
            elif v < 0xC0:
                line += "+"
            else:
                line += "#"
        lines.append(f"{row:2d}| {line}")
    return "\n".join(lines)


def main():
    print(f"[i] ROM: {ROM_FILE}")
    if not ROM_FILE.exists():
        print(f"[!] Нет файла: {ROM_FILE}"); return 1

    rom = ROM_FILE.read_bytes()
    print(f"[i] Размер: {len(rom)} байт")
    print(f"[i] Уровень: 0x{LEVEL_START:04X} (offset 0x{LEVEL_START-ROM_BASE:04X})\n")

    grid, stats = extract(rom)

    print(f"[i] Тайлов записано:  {stats['tiles']}")
    print(f"[i] Колонок (02):     {stats['columns']}")
    print(f"[i] Позиций (03):     {stats['positions']}")
    print(f"[i] Вне сетки:        {stats['out_of_grid']}")
    print(f"[i] Уникальных тайлов: {len(stats['unique'])}")
    if stats["unique"]:
        print(f"[i] Диапазон:         0x{min(stats['unique']):02X} – 0x{max(stats['unique']):02X}")
    print(f"[i] Конец:            {stats['end']} (offset 0x{stats['end_off']:04X})")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"width": GRID_W, "height": GRID_H, "count": stats["tiles"], "grid": grid}
    OUT_FILE.write_text(json.dumps(data, indent=2))
    print(f"\n[i] Записано: {OUT_FILE} ({OUT_FILE.stat().st_size} байт)")

    print("\n[preview 32x32]")
    print(render_preview(grid))
    return 0


if __name__ == "__main__":
    sys.exit(main())
