#!/usr/bin/env python3
"""decode_bg.py — greyscale PNG для последующего тонирования в SDL3."""
import struct, zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SCRIPT_DIR.parent
ROM_DIR = REPO_DIR / "orig_rom"
OUT_DIR = SCRIPT_DIR / "assets" / "tiles"

# Индексы цвета → градации серого. SDL будет умножать на случайный цвет.
GREY_PALETTE = [
    (0, 0, 0, 0),           # 0 → прозрачный
    (64, 64, 64, 255),      # 1 → тёмный
    (128, 128, 128, 255),   # 2 → средний
    (255, 255, 255, 255),   # 3 → светлый
]

BGS = [("bg0", "mpe-1.3l"), ("bg1", "mpe-2.3k"), ("bg2", "mpe-3.3h")]


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


def decode_4px_msb(data, w, h):
    rgba = bytearray(w * h * 4)
    for y in range(h):
        row_off = y * (w // 4)
        for xb in range(w // 4):
            if row_off + xb >= len(data):
                return None
            byte = data[row_off + xb]
            for i in range(4):
                x = xb * 4 + i
                idx = (byte >> (6 - i * 2)) & 3
                r, g, b, a = GREY_PALETTE[idx]
                off = (y * w + x) * 4
                rgba[off], rgba[off+1], rgba[off+2], rgba[off+3] = r, g, b, a
    return make_png(w, h, rgba)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for region, fname in BGS:
        p = ROM_DIR / fname
        if not p.exists():
            print(f"[{fname}] MISSING"); continue
        data = p.read_bytes()
        png = decode_4px_msb(data, 256, 64)
        if not png:
            continue
        out = OUT_DIR / f"landscape_{region}.png"
        out.write_bytes(png)
        print(f"  {out.name}  (greyscale)")


if __name__ == "__main__":
    main()
