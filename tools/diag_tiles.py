#!/usr/bin/env python3
"""Diagnostic: try several gfx decode layouts for Moon Patrol (M52)."""
import struct, zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SCRIPT_DIR.parent
ROM_DIR = REPO_DIR / "orig_rom"
OUT_DIR = SCRIPT_DIR / "assets" / "tiles"

TILE_W = TILE_H = 8
TILES_PER_ROW = 32
FILES = ["mpe-1.3l", "mpe-2.3k", "mpe-3.3h", "mpe-4.3f", "mpe-5.3e"]
PALETTE = [(0,0,0), (0xCC,0x66,0), (0xFF,0xFF,0xFF), (0x88,0x44,0)]

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

def decode_planes(data, n_tiles, plane_size, msb):
    """Tile N: plane0 bytes at [N*8, N*8+8), plane1 at [plane_size+N*8, plane_size+N*8+8)."""
    out = []
    for t in range(n_tiles):
        b0 = t * 8
        b1 = plane_size + t * 8
        if b1 + 8 > len(data):
            break
        px = [[0]*8 for _ in range(8)]
        for y in range(8):
            p0, p1 = data[b0 + y], data[b1 + y]
            for x in range(8):
                bit = (7 - x) if msb else x
                px[y][x] = (((p1 >> bit) & 1) << 1) | ((p0 >> bit) & 1)
        out.append(px)
    return out

def render(px_list):
    n = len(px_list)
    if n == 0:
        return None
    rows = (n + TILES_PER_ROW - 1) // TILES_PER_ROW
    w, h = TILES_PER_ROW * TILE_W, rows * TILE_H
    rgb = bytearray(w * h * 3)
    for t, px in enumerate(px_list):
        tr, tc = divmod(t, TILES_PER_ROW)
        bx, by = tc * 8, tr * 8
        for y in range(8):
            for x in range(8):
                r, g, b = PALETTE[px[y][x] & 3]
                idx = ((by + y) * w + (bx + x)) * 3
                rgb[idx], rgb[idx+1], rgb[idx+2] = r, g, b
    return make_png(w, h, rgb)

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = [(ROM_DIR / f).read_bytes() for f in FILES]
    concat = b''.join(files)
    print(f"[i] concat = {len(concat)} bytes\n")

    # (name, data, plane_size, msb_first)
    variants = [
        # Per-file split: plane 0 = first 2K, plane 1 = second 2K
        ("A_m1_split2K_msb",      files[0], 2048,  True),
        ("B_m1_split2K_lsb",      files[0], 2048,  False),
        ("C_m3_split2K_msb",      files[2], 2048,  True),

        # Concat 20K, plane 0 = 0..0x13FF (5120), plane 1 = 0x1400..0x27FF → 640 tiles
        ("D_concat_640_msb",      concat,   5120,  True),
        ("E_concat_640_lsb",      concat,   5120,  False),

        # Concat 20K, plane 0 = 0..0x27FF (10240), plane 1 = 0x2800..0x4FFF → 1280 tiles
        ("F_concat_1280_msb",     concat,   10240, True),
        ("G_concat_1280_lsb",     concat,   10240, False),

        # First 4 files (16K), plane 0 = 0..0x1FFF (8192), plane 1 = 0x2000..0x3FFF → 1024 tiles
        ("H_concat4_1024_msb",    files[0]+files[1]+files[2]+files[3], 8192, True),

        # Pair 2K: plane 0 = first 2K of mpe-1, plane 1 = first 2K of mpe-2
        ("I_pair2K_12_msb",       files[0] + files[1][:2048], 2048, True),

        # Pair 2K: plane 0 = first 2K of mpe-3, plane 1 = first 2K of mpe-4
        ("J_pair2K_34_msb",       files[2] + files[3][:2048], 2048, True),
    ]

    for name, data, ps, msb in variants:
        n_tiles = min(ps // 8, 1280)
        px = decode_planes(data, n_tiles, ps, msb)
        png = render(px)
        if png is None:
            print(f"  {name}: SKIP")
            continue
        out = OUT_DIR / f"diag_{name}.png"
        out.write_bytes(png)
        print(f"  {out.name}  ({len(px)} tiles)")

if __name__ == "__main__":
    main()
