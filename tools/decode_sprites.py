#!/usr/bin/env python3
"""decode_sprites.py — спрайты mpb-1/mpb-2. Бит 0 всегда 0 → colors = {0,2,4,6}."""
import struct, zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SCRIPT_DIR.parent
ROM_DIR = REPO_DIR / "orig_rom"
OUT_DIR = SCRIPT_DIR / "assets" / "tiles"

# Палитра по значениям цвета 0, 2, 4, 6
PALETTE = [
    (0, 0, 0, 0),              # 0 → прозрачный
    (0, 0, 0, 0),              # 1 (не используется)
    (0xFF, 0xFF, 0xFF, 255),   # 2 → белый (mpb-2)
    (0, 0, 0, 0),              # 3 (не используется)
    (0xCC, 0x66, 0x00, 255),   # 4 → оранжевый (mpb-1)
    (0, 0, 0, 0),              # 5 (не используется)
    (0x88, 0x44, 0x00, 255),   # 6 → тёмно-оранжевый (оба)
    (0, 0, 0, 0),              # 7 (не используется)
]

TILE_W, TILE_H = 16, 16
TILES_PER_ROW = 8


def _chunk(t, d):
    b = t + d
    return struct.pack('>I', len(d)) + b + struct.pack('>I', zlib.crc32(b) & 0xFFFFFFFF)


def make_png(w, h, rgba):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(rgba[y * w * 4:(y + 1) * w * 4])
    return sig + _chunk(b'IHDR', ihdr) + _chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + _chunk(b'IEND', b'')


def decode_sprite(region, tile_idx):
    """MAME: plane_offsets = {2/3, 0/3, 1/3} → [0x2000, 0x0000, 0x1000]."""
    plane_offsets = [0x2000, 0x0000, 0x1000]
    # xoffset = STEP8(0,1), STEP8(128,1) → [0..7, 128..135]
    xoffs = [i for i in range(8)] + [128 + i for i in range(8)]
    # yoffset = STEP16(0,8) → [0, 8, 16, ..., 120]
    yoffs = [i * 8 for i in range(16)]

    rgba = bytearray(TILE_W * TILE_H * 4)
    base = tile_idx * 256

    for y in range(16):
        for x in range(16):
            idx = base + xoffs[x] + yoffs[y]
            if idx >= 0x1000:
                continue
            color = 0
            for plane in range(3):
                b = region[plane_offsets[plane] + idx]
                bit = 7 - (x % 8)   # MSB first
                color |= ((b >> bit) & 1) << plane
            # Прямой индекс 0..7 — палитра содержит прозрачные для 1,3,5,7
            r, g, bb, a = PALETTE[color]
            off = (y * 16 + x) * 4
            rgba[off], rgba[off+1], rgba[off+2], rgba[off+3] = r, g, bb, a
    return rgba


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mpb1 = (ROM_DIR / "mpb-1.3n").read_bytes()
    mpb2 = (ROM_DIR / "mpb-2.3m").read_bytes()
    region = mpb2 + mpb1 + b'\x00' * 4096   # 12 KB
    print(f"region = {len(region)} bytes")

    n_tiles = 16
    rows = (n_tiles + TILES_PER_ROW - 1) // TILES_PER_ROW
    w, h = TILES_PER_ROW * TILE_W, rows * TILE_H
    rgba = bytearray(w * h * 4)

    for t in range(n_tiles):
        spr = decode_sprite(region, t)
        tr, tc = divmod(t, TILES_PER_ROW)
        bx, by = tc * TILE_W, tr * TILE_H
        for y in range(TILE_H):
            for x in range(TILE_W):
                src = (y * 16 + x) * 4
                dst = ((by + y) * w + (bx + x)) * 4
                rgba[dst:dst+4] = spr[src:src+4]

    out = OUT_DIR / "sprites_mpb.png"
    out.write_bytes(make_png(w, h, rgba))
    print(f"  {out.name}  ({n_tiles} sprites)")


if __name__ == "__main__":
    main()
