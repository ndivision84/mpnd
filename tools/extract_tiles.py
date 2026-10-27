#!/usr/bin/env python3
"""
extract_tiles.py — попарное декодирование тайлов Moon Patrol.

Гипотеза: mpe-1+mpe-2 = 2 плана тайлсета 1; mpe-3+mpe-4 = тайлсет 2;
mpe-5 — отдельный тайлсет (или фон).

Каждый файл = 512 тайлов по 8 байт (8x8, 1 байт = 1 строка).
"""

import struct
import zlib
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR   = SCRIPT_DIR.parent
ROM_DIR    = REPO_DIR / "orig_rom"
OUT_DIR    = SCRIPT_DIR / "assets" / "tiles"

TILE_W = 8
TILE_H = 8
TILES_PER_ROW = 32
BYTES_PER_TILE = 8         # 8 rows × 1 byte

# Палитра Moon Patrol: чёрный / оранжевый / белый / тёмно-оранжевый
PALETTE = [
    (0x00, 0x00, 0x00),
    (0xCC, 0x66, 0x00),
    (0xFF, 0xFF, 0xFF),
    (0x88, 0x44, 0x00),
]

PAIRS = [
    ("charset1_1+2",   "mpe-1.3l", "mpe-2.3k"),
    ("charset1_1+3",   "mpe-1.3l", "mpe-3.3h"),
    ("charset2_3+4",   "mpe-3.3h", "mpe-4.3f"),
    ("charset2_4+5",   "mpe-4.3f", "mpe-5.3e"),
    ("charset3_5+1",   "mpe-5.3e", "mpe-1.3l"),
]

# Одиночные (2 плана внутри одного файла)
SINGLES = ["mpe-1.3l", "mpe-2.3k", "mpe-3.3h", "mpe-4.3f", "mpe-5.3e"]


def _png_chunk(typ, data):
    body = typ + data
    return (struct.pack('>I', len(data))
            + body
            + struct.pack('>I', zlib.crc32(body) & 0xffffffff))


def make_png(width, height, rgb):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(rgb[y * width * 3:(y + 1) * width * 3])
    idat = zlib.compress(bytes(raw), 9)
    return (sig + _png_chunk(b'IHDR', ihdr)
            + _png_chunk(b'IDAT', idat)
            + _png_chunk(b'IEND', b''))


def decode_pair(plane0, plane1, tile_idx, msb_first=True):
    """Тайл из двух файлов-плоскостей (по 1 байту на строку)."""
    px = [[0] * 8 for _ in range(8)]
    base = tile_idx * BYTES_PER_TILE
    if base + 8 > len(plane0) or base + 8 > len(plane1):
        return None
    for y in range(8):
        p0 = plane0[base + y]
        p1 = plane1[base + y]
        for x in range(8):
            bit = (7 - x) if msb_first else x
            b0 = (p0 >> bit) & 1
            b1 = (p1 >> bit) & 1
            px[y][x] = (b1 << 1) | b0
    return px


def decode_single_8(data, tile_idx, msb_first=True):
    """Тайл из одного файла: 8 байт = 8 строк, 8 пикселей каждого."""
    px = [[0] * 8 for _ in range(8)]
    base = tile_idx * BYTES_PER_TILE
    if base + 8 > len(data):
        return None
    for y in range(8):
        byte = data[base + y]
        for x in range(8):
            bit = (7 - x) if msb_first else x
            px[y][x] = (byte >> bit) & 1
    return px


def render_sheet(decode_fn, n_tiles):
    n_rows = (n_tiles + TILES_PER_ROW - 1) // TILES_PER_ROW
    w = TILES_PER_ROW * TILE_W
    h = n_rows * TILE_H
    rgb = bytearray(w * h * 3)
    for t in range(n_tiles):
        tile = decode_fn(t)
        if tile is None:
            continue
        tr, tc = divmod(t, TILES_PER_ROW)
        bx, by = tc * TILE_W, tr * TILE_H
        for y in range(TILE_H):
            for x in range(TILE_W):
                r, g, b = PALETTE[tile[y][x] & 0x03]
                idx = ((by + y) * w + (bx + x)) * 3
                rgb[idx], rgb[idx + 1], rgb[idx + 2] = r, g, b
    return make_png(w, h, rgb)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[i] OUT: {OUT_DIR}\n")

    # 1. Попарное декодирование (MSB и LSB)
    for name, f1, f2 in PAIRS:
        p1, p2 = ROM_DIR / f1, ROM_DIR / f2
        if not p1.exists() or not p2.exists():
            print(f"[{name}] MISSING {f1} / {f2}")
            continue
        d0, d1 = p1.read_bytes(), p2.read_bytes()
        n_tiles = min(len(d0), len(d1)) // BYTES_PER_TILE
        for order, msb in [("msb", True), ("lsb", False)]:
            out_name = f"pair_{name}_{order}.png"
            png = render_sheet(
                lambda t, d0=d0, d1=d1, msb=msb: decode_pair(d0, d1, t, msb),
                n_tiles)
            (OUT_DIR / out_name).write_bytes(png)
            print(f"  {out_name}  ({n_tiles} tiles)")

    # 2. Одиночные файлы (2 плана внутри, 1-битный режим)
    print()
    for fname in SINGLES:
        p = ROM_DIR / fname
        if not p.exists():
            continue
        data = p.read_bytes()
        n_tiles = len(data) // BYTES_PER_TILE
        for order, msb in [("msb", True), ("lsb", False)]:
            out_name = f"single_{fname}_{order}.png"
            png = render_sheet(
                lambda t, d=data, msb=msb: decode_single_8(d, t, msb),
                n_tiles)
            (OUT_DIR / out_name).write_bytes(png)
            print(f"  {out_name}  ({n_tiles} tiles)")


if __name__ == "__main__":
    main()
