#!/usr/bin/env python3
"""extract_patterns.py — нарезка 8×8 2bpp тайлов из ROM Moon Patrol (Irem mpatrol).

Читает mpe-1.3l … mpe-5.3e (5 банков × 4096 байт = 256 тайлов на банк).
Формат тайла: planar 2bpp (MAME m52.cpp, tiles8x8_layout):
  byte 0..7   — bitplane 0 для строк 0..7 (MSB-first: bit 7 = левый пиксель)
  byte 8..15  — bitplane 1 для строк 0..7
  pixel(x,y) = (bit1 << 1) | bit0

Генерирует в --out-dir (по умолчанию assets/patterns, gitignored):
  bank<N>_sheet.png                    — контактный лист 16×16 тайлов, x6 зум, с номерами 0xNN
  interesting/bank<N>_tile_0x<NN>.png  — увеличенные карточки (x10) для тайлов из
                                         0x20-0x30 (кратер/камень), 0xD0-0xE0 (анимации),
                                         0xF0-0xFF (земля)

Идемпотентность: если PNG новее ROM — SKIP (перезапись через --force).
Pure stdlib: argparse, struct, pathlib, zlib, sys.

Запуск (из корня репо ~/Downloads/mpng/mpng_src):
    python3 tools/extract_patterns.py
    python3 tools/extract_patterns.py --cards
    python3 tools/extract_patterns.py --bank 1 --cards
"""

from __future__ import annotations

import argparse
import struct
import sys
import shutil
import zlib
from pathlib import Path

# ---------- Конфигурация ----------

BANKS = [
    ("mpe-1.3l", 0),
    ("mpe-2.3k", 1),
    ("mpe-3.3h", 2),
    ("mpe-4.3f", 3),
    ("mpe-5.3e", 4),
]
TILE_W = TILE_H = 8
BYTES_PER_TILE = 16
TILES_PER_BANK = 256

GRAY = [(0x00, 0x00, 0x00), (0x55, 0x55, 0x55), (0xAA, 0xAA, 0xAA), (0xFF, 0xFF, 0xFF)]
BG_COLOR = (0x28, 0x28, 0x28)

SHEET_COLS = 16
SHEET_ROWS = 16
SHEET_ZOOM = 6
CARD_ZOOM = 10
LABEL_ZOOM = 2
CELL_PAD = 2

INTERESTING_RANGES = [(0x20, 0x30), (0xD0, 0xE0), (0xF0, 0xFF)]

# Минимальный 3x5 шрифт (hex-цифры и 'x') — чтобы подписать каждый тайл.
FONT_3x5 = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "001", "001", "001"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "A": ("111", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("111", "100", "100", "100", "111"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "111", "100", "111"),
    "F": ("111", "100", "111", "100", "100"),
    "x": ("000", "101", "010", "101", "000"),
    " ": ("000", "000", "000", "000", "000"),
}

# ---------- Декодирование ----------

def decode_tile(buf, offset):
    """Planar 2bpp -> 8x8 индексов цвета 0..3."""
    p0 = buf[offset:offset + 8]
    p1 = buf[offset + 8:offset + 16]
    rows = []
    for y in range(8):
        row = []
        for x in range(8):
            b0 = (p0[y] >> (7 - x)) & 1
            b1 = (p1[y] >> (7 - x)) & 1
            row.append((b1 << 1) | b0)
        rows.append(row)
    return rows

# ---------- PNG-эмиттер (RGB, 8-bit, type 2) ----------

def _png_chunk(tag, data):
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_png(path, width, height, rows):
    """rows — список bytearray по width*3 байт (RGB)."""
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with path.open("wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_png_chunk(b"IHDR", ihdr))
        f.write(_png_chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(_png_chunk(b"IEND", b""))

# ---------- Рисование ----------

def fill_rect(canvas, x0, y0, w, h, rgb):
    color = bytes(rgb) * w
    for y in range(max(0, y0), min(y0 + h, len(canvas))):
        if x0 < 0:
            continue
        canvas[y][x0 * 3:(x0 + w) * 3] = color


def draw_tile_zoomed(canvas, x0, y0, tile, zoom):
    for ty, trow in enumerate(tile):
        for tx, v in enumerate(trow):
            fill_rect(canvas, x0 + tx * zoom, y0 + ty * zoom, zoom, zoom, GRAY[v])


def _text_px_width(text, zoom):
    return len(text) * (3 + 1) * zoom - zoom if text else 0


def draw_text(canvas, x0, y0, text, zoom, rgb=(0xEE, 0xEE, 0xEE)):
    cx = x0
    for ch in text:
        glyph = FONT_3x5.get(ch, FONT_3x5[" "])
        for gy, line in enumerate(glyph):
            for gx, bit in enumerate(line):
                if bit == "1":
                    fill_rect(canvas, cx + gx * zoom, y0 + gy * zoom, zoom, zoom, rgb)
        cx += (3 + 1) * zoom

# ---------- Сборка листов ----------

def make_sheet(bank_idx, rom_name, tiles):
    tile_px = TILE_W * SHEET_ZOOM
    label_px_h = 5 * LABEL_ZOOM
    cell_w = tile_px + CELL_PAD * 2
    cell_h = tile_px + CELL_PAD + label_px_h + CELL_PAD
    header_h = label_px_h + 8

    W = SHEET_COLS * cell_w
    H = header_h + SHEET_ROWS * cell_h
    canvas = [bytearray(bytes(BG_COLOR) * W) for _ in range(H)]

    header = f"bank{bank_idx}  {rom_name}  ({TILES_PER_BANK} tiles, x{SHEET_ZOOM})"
    draw_text(canvas, 8, 4, header, LABEL_ZOOM, rgb=(0x88, 0xFF, 0xCC))

    for i, tile in enumerate(tiles):
        col, row = i % SHEET_COLS, i // SHEET_COLS
        x0 = col * cell_w + CELL_PAD
        y0 = header_h + row * cell_h + CELL_PAD
        draw_tile_zoomed(canvas, x0, y0, tile, SHEET_ZOOM)
        label = f"0x{i:02X}"
        lw = _text_px_width(label, LABEL_ZOOM)
        lx = x0 + (tile_px - lw) // 2
        ly = y0 + tile_px + CELL_PAD
        draw_text(canvas, lx, ly, label, LABEL_ZOOM)
    return W, H, canvas


def make_card(tile, bank_idx, tile_id):
    tile_px = TILE_W * CARD_ZOOM
    label = f"bank{bank_idx}  0x{tile_id:02X}"
    label_px_h = 5 * LABEL_ZOOM
    W = max(tile_px, _text_px_width(label, LABEL_ZOOM)) + 8
    H = 4 + tile_px + 4 + label_px_h + 4
    canvas = [bytearray(bytes(BG_COLOR) * W) for _ in range(H)]
    draw_tile_zoomed(canvas, 4, 4, tile, CARD_ZOOM)
    draw_text(canvas, 4, 4 + tile_px + 4, label, LABEL_ZOOM, rgb=(0x88, 0xFF, 0xCC))
    return W, H, canvas

# ---------- CLI / main ----------

def is_interesting(tile_id):
    return any(a <= tile_id <= b for a, b in INTERESTING_RANGES)


def main():
    ap = argparse.ArgumentParser(
        description="Нарезка 8x8 2bpp тайлов из ROM Moon Patrol (Irem mpatrol).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--rom-dir", default="../orig_rom", help="папка с ROM-файлами")
    ap.add_argument("--out-dir", default="assets/patterns", help="куда писать PNG")
    ap.add_argument("--bank", type=int, choices=[b[1] for b in BANKS], default=None,
                    help="обработать только один банк (0..4)")
    ap.add_argument("--cards", action="store_true",
                    help="сгенерировать увеличенные карточки для интересных тайлов")
    ap.add_argument("--force", action="store_true",
                    help="перезаписать даже если PNG новее ROM")
    ap.add_argument("--pics-dir", default=None,
                    help="если задано — копировать все PNG сюда (для отправки)")
    args = ap.parse_args()

    rom_dir = Path(args.rom_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    interesting_dir = out_dir / "interesting"
    pics_dir = Path(args.pics_dir).resolve() if args.pics_dir else None

    # ===== ДИАГНОСТИКА (до) =====
    print("=== ДИАГНОСТИКА (до) ===")
    print(f"  ROM:  {rom_dir}")
    print(f"  OUT:  {out_dir}")

    if not rom_dir.is_dir():
        print(f"FAIL: ROM-папка не найдена: {rom_dir}")
        print("      Запустите из корня репо, либо укажите --rom-dir /абс/путь")
        return 1

    selected = [b for b in BANKS if args.bank is None or b[1] == args.bank]
    for name, idx in selected:
        p = rom_dir / name
        if not p.is_file():
            print(f"FAIL: нет файла {p}")
            return 1
        size = p.stat().st_size
        expect = TILES_PER_BANK * BYTES_PER_TILE
        ok = "OK" if size == expect else f"FAIL (ожидалось {expect})"
        print(f"  bank{idx} {name}: {size} B  [{ok}]")
        if size != expect:
            return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    interesting_dir.mkdir(exist_ok=True)

    # ===== ПРИМЕНЕНИЕ =====
    print("=== ПРИМЕНЕНИЕ ===")
    for name, idx in selected:
        rom_path = rom_dir / name
        sheet_path = out_dir / f"bank{idx}_sheet.png"
        rom_mtime = rom_path.stat().st_mtime

        buf = rom_path.read_bytes()
        tiles = [decode_tile(buf, i * BYTES_PER_TILE) for i in range(TILES_PER_BANK)]

        if not args.force and sheet_path.is_file() and sheet_path.stat().st_mtime >= rom_mtime:
            print(f"  SKIP: {sheet_path.name} (свежее ROM)")
        else:
            W, H, canvas = make_sheet(idx, name, tiles)
            write_png(sheet_path, W, H, canvas)
            print(f"  OK: {sheet_path.name}  {W}x{H}  ({len(tiles)} тайлов)")

        if args.cards:
            for i in range(TILES_PER_BANK):
                if not is_interesting(i):
                    continue
                card_path = interesting_dir / f"bank{idx}_tile_0x{i:02X}.png"
                if not args.force and card_path.is_file() and card_path.stat().st_mtime >= rom_mtime:
                    continue
                W, H, canvas = make_card(tiles[i], idx, i)
                write_png(card_path, W, H, canvas)
            n = sum(1 for i in range(TILES_PER_BANK) if is_interesting(i))
            print(f"  OK: interesting/bank{idx}_tile_*.png ({n} карточек)")

    # ===== ВЕРИФИКАЦИЯ =====
    print("=== ВЕРИФИКАЦИЯ ===")
    ok_sheets = 0
    for name, idx in selected:
        p = out_dir / f"bank{idx}_sheet.png"
        if p.is_file():
            print(f"  OK: {p.name}  {p.stat().st_size} B")
            ok_sheets += 1
        else:
            print(f"  FAIL: {p.name} отсутствует")

    cards_count = 0
    if args.cards:
        cards_count = len(list(interesting_dir.glob("bank*_tile_*.png")))
        print(f"  OK: interesting/ — {cards_count} карточек")

    if pics_dir is not None:
        pics_dir.mkdir(parents=True, exist_ok=True)
        mirrored = 0
        for png in out_dir.rglob("*.png"):
            rel = png.relative_to(out_dir)
            dst = pics_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(png, dst)
            mirrored += 1
        print(f"  OK: mirrored {mirrored} PNG -> {pics_dir}")

    suffix = f", карточек: {cards_count}" if args.cards else ""
    print(f"Готово. Сгенерировано листов: {ok_sheets}/{len(selected)}{suffix}.")
    return 0 if ok_sheets == len(selected) else 1


if __name__ == "__main__":
    sys.exit(main())
