#!/usr/bin/env python3
"""probe_v2.py — column-major и 16x16 для m1/m2/m3 (исправленная версия)."""
import struct, zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SCRIPT_DIR.parent
ROM_DIR = REPO_DIR / "orig_rom"
OUT_DIR = SCRIPT_DIR / "assets" / "tiles"

PALETTE = [(0,0,0), (0xCC,0x66,0), (0xFF,0xFF,0xFF), (0x88,0x44,0)]

FILES = {"m1": "mpe-1.3l", "m2": "mpe-2.3k", "m3": "mpe-3.3h"}


def _chunk(t, d):
    b = t + d
    return struct.pack('>I', len(d)) + b + struct.pack('>I', zlib.crc32(b) & 0xFFFFFFFF)


def make_png(w, h, rgb):
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(rgb[y*w*3:(y+1)*w*3])
    return sig + _chunk(b'IHDR', ihdr) + _chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + _chunk(b'IEND', b'')


def render(px_list, tw, th, per_row):
    n = len(px_list)
    if n == 0: return None
    rows = (n + per_row - 1) // per_row
    w, h = per_row*tw, rows*th
    rgb = bytearray(w*h*3)
    for t, px in enumerate(px_list):
        tr, tc = divmod(t, per_row)
        bx, by = tc*tw, tr*th
        for y in range(th):
            for x in range(tw):
                r,g,b = PALETTE[px[y][x] & 3]
                idx = ((by+y)*w+(bx+x))*3
                rgb[idx], rgb[idx+1], rgb[idx+2] = r,g,b
    return make_png(w, h, rgb)


def decode_pair_rowmajor(d0, d1, tw, th):
    """Row-major: строка y — tw/8 байт; pixel x → байт x//8, bit 7-(x%8)."""
    bytes_per_tile = (tw * th) // 8
    bytes_per_row = tw // 8
    n_tiles = len(d0) // bytes_per_tile
    out = []
    for t in range(n_tiles):
        b = t * bytes_per_tile
        px = [[0]*tw for _ in range(th)]
        for y in range(th):
            for xb in range(bytes_per_row):
                p0 = d0[b + y*bytes_per_row + xb]
                p1 = d1[b + y*bytes_per_row + xb]
                for i in range(8):
                    x = xb * 8 + i
                    bit = 7 - i
                    px[y][x] = (((p1>>bit)&1)<<1) | ((p0>>bit)&1)
        out.append(px)
    return out


def decode_pair_colmajor(d0, d1, tw, th):
    """Column-major: колонка x — th/8 байт; pixel y → байт y//8, bit 7-(y%8)."""
    bytes_per_tile = (tw * th) // 8
    bytes_per_col = th // 8
    n_tiles = len(d0) // bytes_per_tile
    out = []
    for t in range(n_tiles):
        b = t * bytes_per_tile
        px = [[0]*tw for _ in range(th)]
        for x in range(tw):
            for yb in range(bytes_per_col):
                p0 = d0[b + x*bytes_per_col + yb]
                p1 = d1[b + x*bytes_per_col + yb]
                for i in range(8):
                    y = yb * 8 + i
                    bit = 7 - i
                    px[y][x] = (((p1>>bit)&1)<<1) | ((p0>>bit)&1)
        out.append(px)
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    roms = {k: (ROM_DIR/v).read_bytes() for k,v in FILES.items()}

    variants = [
        ("row8_m1+m2",  decode_pair_rowmajor(roms["m1"], roms["m2"], 8, 8),   8, 8),
        ("col8_m1+m2",  decode_pair_colmajor(roms["m1"], roms["m2"], 8, 8),   8, 8),
        ("row16_m1+m2", decode_pair_rowmajor(roms["m1"], roms["m2"], 16, 16), 16, 16),
        ("col16_m1+m2", decode_pair_colmajor(roms["m1"], roms["m2"], 16, 16), 16, 16),

        ("row8_m2+m3",  decode_pair_rowmajor(roms["m2"], roms["m3"], 8, 8),   8, 8),
        ("col8_m2+m3",  decode_pair_colmajor(roms["m2"], roms["m3"], 8, 8),   8, 8),
        ("row16_m2+m3", decode_pair_rowmajor(roms["m2"], roms["m3"], 16, 16), 16, 16),
        ("col16_m2+m3", decode_pair_colmajor(roms["m2"], roms["m3"], 16, 16), 16, 16),

        ("row8_m1+m3",  decode_pair_rowmajor(roms["m1"], roms["m3"], 8, 8),   8, 8),
        ("col8_m1+m3",  decode_pair_colmajor(roms["m1"], roms["m3"], 8, 8),   8, 8),
        ("row16_m1+m3", decode_pair_rowmajor(roms["m1"], roms["m3"], 16, 16), 16, 16),
        ("col16_m1+m3", decode_pair_colmajor(roms["m1"], roms["m3"], 16, 16), 16, 16),
    ]

    for name, px, tw, th in variants:
        per_row = 16 if tw == 8 else 8
        png = render(px, tw, th, per_row)
        if not png:
            print(f"  {name}: skip"); continue
        out = OUT_DIR / f"v2_{name}.png"
        out.write_bytes(png)
        print(f"  {out.name}  ({len(px)} tiles {tw}x{th})")


if __name__ == "__main__":
    main()
