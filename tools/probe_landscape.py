#!/usr/bin/env python3
"""probe_landscape.py — 12 вариантов декодирования для mpe-1/mpe-2/mpe-3."""
import struct, zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SCRIPT_DIR.parent
ROM_DIR = REPO_DIR / "orig_rom"
OUT_DIR = SCRIPT_DIR / "assets" / "tiles"

TILE_W = TILE_H = 8
TILES_PER_ROW = 16
PALETTE = [(0,0,0), (0xCC,0x66,0), (0xFF,0xFF,0xFF), (0x88,0x44,0)]

M1 = "mpe-1.3l"
M2 = "mpe-2.3k"
M3 = "mpe-3.3h"

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

def render_tiles(px_list):
    n = len(px_list)
    if n == 0: return None
    rows = (n + TILES_PER_ROW - 1) // TILES_PER_ROW
    w, h = TILES_PER_ROW*8, rows*8
    rgb = bytearray(w*h*3)
    for t, px in enumerate(px_list):
        tr, tc = divmod(t, TILES_PER_ROW)
        bx, by = tc*8, tr*8
        for y in range(8):
            for x in range(8):
                r,g,b = PALETTE[px[y][x] & 3]
                idx = ((by+y)*w+(bx+x))*3
                rgb[idx], rgb[idx+1], rgb[idx+2] = r,g,b
    return make_png(w, h, rgb)

def decode_planes_pair(d0, d1, n_tiles, msb):
    """pair: plane0 = d0, plane1 = d1."""
    out = []
    for t in range(n_tiles):
        b = t*8
        if b+8 > len(d0) or b+8 > len(d1): break
        px = [[0]*8 for _ in range(8)]
        for y in range(8):
            p0, p1 = d0[b+y], d1[b+y]
            for x in range(8):
                bit = (7-x) if msb else x
                px[y][x] = (((p1>>bit)&1)<<1) | ((p0>>bit)&1)
        out.append(px)
    return out

def decode_split(d, msb, plane_size=2048):
    """split: plane0 = first half, plane1 = second half."""
    n = plane_size // 8
    out = []
    for t in range(n):
        b0, b1 = t*8, plane_size + t*8
        if b1+8 > len(d): break
        px = [[0]*8 for _ in range(8)]
        for y in range(8):
            p0, p1 = d[b0+y], d[b1+y]
            for x in range(8):
                bit = (7-x) if msb else x
                px[y][x] = (((p1>>bit)&1)<<1) | ((p0>>bit)&1)
        out.append(px)
    return out

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    roms = {f: (ROM_DIR / f).read_bytes() for f in [M1, M2, M3]}
    print(f"mpe-1: {len(roms[M1])}b, mpe-2: {len(roms[M2])}b, mpe-3: {len(roms[M3])}b\n")

    variants = []

    # 1-2: mpe-1 split 2K (MSB/LSB)
    variants.append(("P1_m1_split2K_msb", decode_split(roms[M1], True, 2048)))
    variants.append(("P2_m1_split2K_lsb", decode_split(roms[M1], False, 2048)))

    # 3-4: mpe-2 split 2K
    variants.append(("P3_m2_split2K_msb", decode_split(roms[M2], True, 2048)))
    variants.append(("P4_m2_split2K_lsb", decode_split(roms[M2], False, 2048)))

    # 5-6: mpe-3 split 2K
    variants.append(("P5_m3_split2K_msb", decode_split(roms[M3], True, 2048)))
    variants.append(("P6_m3_split2K_lsb", decode_split(roms[M3], False, 2048)))

    # 7-8: pair m1 (plane0) + m2 (plane1)
    variants.append(("P7_pair_m1+m2_msb", decode_planes_pair(roms[M1], roms[M2], 512, True)))
    variants.append(("P8_pair_m1+m2_lsb", decode_planes_pair(roms[M1], roms[M2], 512, False)))

    # 9-10: pair m2 (plane0) + m3 (plane1)
    variants.append(("P9_pair_m2+m3_msb", decode_planes_pair(roms[M2], roms[M3], 512, True)))
    variants.append(("P10_pair_m2+m3_lsb", decode_planes_pair(roms[M2], roms[M3], 512, False)))

    # 11-12: pair m1 (plane0) + m3 (plane1)
    variants.append(("P11_pair_m1+m3_msb", decode_planes_pair(roms[M1], roms[M3], 512, True)))
    variants.append(("P12_pair_m1+m3_lsb", decode_planes_pair(roms[M1], roms[M3], 512, False)))

    for name, px in variants:
        png = render_tiles(px)
        if not png:
            print(f"  {name}: skip"); continue
        out = OUT_DIR / f"probe_{name}.png"
        out.write_bytes(png)
        print(f"  {out.name}  ({len(px)} tiles)")

if __name__ == "__main__":
    main()
