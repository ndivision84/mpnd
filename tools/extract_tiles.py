#!/usr/bin/env python3
"""
extract_tiles.py — Extract Moon Patrol (mpe-*) tile graphics to PNG.

Tries several common Irem M52 bitplane layouts. Open the PNGs and pick
the layout that shows recognizable game graphics (buggy, aliens, rocks,
moon surface, ship, etc). Wrong layouts will look like diagonal noise.

Usage:
    python3 extract_tiles.py                  # default: current dir
    python3 extract_tiles.py /path/to/roms    # explicit rom dir
    python3 extract_tiles.py --layout NAME    # extract only one layout
    python3 extract_tiles.py --list           # show layouts

Output: <rom_dir>/tiles/<layout>_<file>.png

macOS 12+ and Linux. Python 3.6+ stdlib only. No PIL, no numpy.
"""

import sys
import zlib
import struct
from pathlib import Path


GFX_FILES = ['mpe-1.3l', 'mpe-2.3k', 'mpe-3.3h', 'mpe-4.3f', 'mpe-5.3e']

TILE_W = 8
TILE_H = 8
TILES_PER_ROW = 16

# 2-bit palette: bit0 = plane 0, bit1 = plane 1
PALETTE = [
    (0x00, 0x00, 0x00),   # 00 = both off
    (0xCC, 0x00, 0x00),   # 01 = plane 0 only (red)
    (0x00, 0xCC, 0x00),   # 10 = plane 1 only (green)
    (0xFF, 0xFF, 0x00),   # 11 = both on (yellow)
]


# ---------------------------------------------------------------------------
# PNG writer (no external dependencies)

def _png_chunk(typ, data):
    body = typ + data
    return (struct.pack('>I', len(data))
            + body
            + struct.pack('>I', zlib.crc32(body) & 0xffffffff))


def make_png(width, height, rgb):
    """rgb is bytearray of length width*height*3"""
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type = none
        raw.extend(rgb[y * width * 3:(y + 1) * width * 3])
    idat = zlib.compress(bytes(raw), 9)
    return (sig
            + _png_chunk(b'IHDR', ihdr)
            + _png_chunk(b'IDAT', idat)
            + _png_chunk(b'IEND', b''))


# ---------------------------------------------------------------------------
# Layout decoders
# Each takes (data, tile_index) and returns 8x8 list of color 0..3, or None.

def decode_interleaved_16(data, t):
    """
    16 bytes/tile. Byte 2*y+p = row y, plane p. Bit 7 = pixel 0 (MSB first).
    Byte layout:
      0=p0r0 1=p1r0 2=p0r1 3=p1r1 ... 14=p0r7 15=p1r7
    """
    base = t * 16
    if base + 16 > len(data):
        return None
    buf = data[base:base + 16]
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        p0, p1 = buf[2 * y], buf[2 * y + 1]
        for x in range(8):
            bit = 7 - x
            b0 = (p0 >> bit) & 1
            b1 = (p1 >> bit) & 1
            pixels[y][x] = (b1 << 1) | b0
    return pixels


def decode_planar_16(data, t):
    """
    16 bytes/tile. Bytes 0-7 = plane 0 rows 0-7, bytes 8-15 = plane 1.
    Bit 7 = pixel 0.
    """
    base = t * 16
    if base + 16 > len(data):
        return None
    buf = data[base:base + 16]
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        p0, p1 = buf[y], buf[8 + y]
        for x in range(8):
            bit = 7 - x
            b0 = (p0 >> bit) & 1
            b1 = (p1 >> bit) & 1
            pixels[y][x] = (b1 << 1) | b0
    return pixels


def decode_nibble_16(data, t):
    """
    16 bytes/tile. Byte 2*y = row y pixels 0-3 (low nibble = plane 0,
    high nibble = plane 1); byte 2*y+1 = row y pixels 4-7.
    """
    base = t * 16
    if base + 16 > len(data):
        return None
    buf = data[base:base + 16]
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        lo_byte, hi_byte = buf[2 * y], buf[2 * y + 1]
        for i in range(4):
            b0 = (lo_byte >> i) & 1
            b1 = (lo_byte >> (i + 4)) & 1
            pixels[y][i] = (b1 << 1) | b0

            b0 = (hi_byte >> i) & 1
            b1 = (hi_byte >> (i + 4)) & 1
            pixels[y][i + 4] = (b1 << 1) | b0
    return pixels


def decode_planar_32(data, t):
    """
    32 bytes/tile. First 16 = plane 0 (8 rows x 2 bytes per row),
    next 16 = plane 1. Within each plane, byte 2*y = row y pixels 0-3 (bits 4-7
    of the byte hold the pixels 0-3, bits 0-3 hold pixels 4-7). This is the
    Irem M52 planar variant used for many games.
    """
    base = t * 32
    if base + 32 > len(data):
        return None
    buf = data[base:base + 32]
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        for half in range(2):
            p0_byte = buf[y * 2 + half]
            p1_byte = buf[16 + y * 2 + half]
            for i in range(4):
                x = half * 4 + i
                b0 = (p0_byte >> (7 - i)) & 1
                b1 = (p1_byte >> (7 - i)) & 1
                pixels[y][x] = (b1 << 1) | b0
    return pixels


def decode_planar_32b(data, t):
    """
    32 bytes/tile. Interleaved 16 layout but with 32-byte stride
    (16 bytes used, 16 bytes padding - some dumps do this).
    """
    base = t * 32
    if base + 32 > len(data):
        return None
    buf = data[base:base + 16]
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        p0, p1 = buf[2 * y], buf[2 * y + 1]
        for x in range(8):
            bit = 7 - x
            b0 = (p0 >> bit) & 1
            b1 = (p1 >> bit) & 1
            pixels[y][x] = (b1 << 1) | b0
    return pixels


LAYOUTS = [
    ('interleaved_16', decode_interleaved_16, 16, 'byte 2y+p, MSB-first'),
    ('planar_16',      decode_planar_16,      16, 'plane0 rows 0-7, plane1 rows 0-7'),
    ('nibble_16',      decode_nibble_16,      16, 'nibbles: lo=plane0, hi=plane1'),
    ('planar_32',      decode_planar_32,      32, '32B: plane0 16B, plane1 16B'),
    ('planar_32b',     decode_planar_32b,     32, '32B stride, 16B used'),
]


# ---------------------------------------------------------------------------
# Rendering

def render_sheet(data, decode_fn, tile_size):
    n_tiles = len(data) // tile_size
    if n_tiles == 0:
        return None, 0
    n_rows = (n_tiles + TILES_PER_ROW - 1) // TILES_PER_ROW
    width = TILES_PER_ROW * TILE_W
    height = n_rows * TILE_H

    rgb = bytearray(width * height * 3)
    for t in range(n_tiles):
        tile = decode_fn(data, t)
        if tile is None:
            continue
        tr, tc = divmod(t, TILES_PER_ROW)
        bx, by = tc * TILE_W, tr * TILE_H
        for y in range(TILE_H):
            for x in range(TILE_W):
                r, g, b = PALETTE[tile[y][x]]
                idx = ((by + y) * width + (bx + x)) * 3
                rgb[idx] = r
                rgb[idx + 1] = g
                rgb[idx + 2] = b

    return make_png(width, height, rgb), n_tiles


def main():
    args = sys.argv[1:]
    if '--list' in args:
        print("Available layouts:")
        for name, _, size, desc in LAYOUTS:
            print(f"  {name:<16} {size:>2}B/tile  {desc}")
        return

    selected_layout = None
    if '--layout' in args:
        i = args.index('--layout')
        if i + 1 >= len(args):
            print("ERROR: --layout requires a name", file=sys.stderr)
            sys.exit(1)
        selected_layout = args[i + 1]
        args = args[:i] + args[i + 2:]
        if not any(name == selected_layout for name, _, _, _ in LAYOUTS):
            print(f"ERROR: unknown layout '{selected_layout}'", file=sys.stderr)
            print("Use --list to see available layouts.", file=sys.stderr)
            sys.exit(1)

    dirpath = Path(args[0]) if args else Path('.')
    if not dirpath.is_dir():
        print(f"ERROR: {dirpath} is not a directory", file=sys.stderr)
        sys.exit(1)

    outdir = dirpath / 'tiles'
    outdir.mkdir(exist_ok=True)

    print("=" * 74)
    print("  Moon Patrol tile extraction")
    print(f"  Source: {dirpath.resolve()}")
    print(f"  Output: {outdir.resolve()}")
    print("=" * 74)

    layouts_to_run = (LAYOUTS if selected_layout is None
                      else [L for L in LAYOUTS if L[0] == selected_layout])

    written = []
    for name, fn, size, desc in layouts_to_run:
        print(f"\n[{name}]  {size} bytes/tile  ({desc})")
        for fname in GFX_FILES:
            p = dirpath / fname
            if not p.exists():
                print(f"  {fname}: MISSING")
                continue
            data = p.read_bytes()
            png, n = render_sheet(data, fn, size)
            if png is None:
                print(f"  {fname}: file too small")
                continue
            out = outdir / f"{name}_{fname}.png"
            out.write_bytes(png)
            written.append(out.name)
            print(f"  {fname}: {n:>4} tiles -> {out.name}")

    print(f"\nWrote {len(written)} PNG files to {outdir}")
    print()
    print("How to identify the correct layout:")
    print("  Open each PNG in Preview (macOS) or any image viewer.")
    print()
    print("  CORRECT layout shows:")
    print("    - smooth curves, clean straight lines")
    print("    - recognizable objects: buggy, moon surface, rocks,")
    print("      aliens, flying saucers, ship, HUD digits")
    print("    - text that reads like letters")
    print()
    print("  WRONG layout shows:")
    print("    - diagonal stripes / checkerboards")
    print("    - vertical or horizontal streaks")
    print("    - 'static' noise without recognizable shapes")
    print("    - fragmented fragments of shapes rather than complete ones")
    print()
    print("Tip on macOS: open tiles/ in Finder with `open tiles/` to browse.")
    print("If nothing looks right, tell me which files you checked and what")
    print("you saw; I'll adjust the bit layout.")


if __name__ == '__main__':
    main()
