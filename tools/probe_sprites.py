#!/usr/bin/env python3
"""probe_sprites.py — перебор вариантов декодирования спрайтов mpb-1/mpb-2."""
import struct, zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SCRIPT_DIR.parent
ROM_DIR = REPO_DIR / "orig_rom"
OUT_DIR = SCRIPT_DIR / "assets" / "tiles"

PALETTE = [
    (0, 0, 0, 0),
    (0xFF, 0xFF, 0xFF, 255),
    (0xCC, 0x66, 0x00, 255),
    (0x88, 0x44, 0x00, 255),
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


def make_sheet(region, n_tiles, decode_fn, name):
    rows = (n_tiles + TILES_PER_ROW - 1) // TILES_PER_ROW
    w, h = TILES_PER_ROW * TILE_W, rows * TILE_H
    rgba = bytearray(w * h * 4)
    for t in range(n_tiles):
        spr = decode_fn(region, t)
        if spr is None:
            continue
        tr, tc = divmod(t, TILES_PER_ROW)
        bx, by = tc * TILE_W, tr * TILE_H
        for y in range(TILE_H):
            for x in range(TILE_W):
                src = (y * TILE_W + x) * 4
                dst = ((by + y) * w + (bx + x)) * 4
                rgba[dst:dst + 4] = spr[src:src + 4]
    out = OUT_DIR / f"probe_{name}.png"
    out.write_bytes(make_png(w, h, rgba))
    print(f"  {out.name}  ({n_tiles} sprites)")


def make_decoder(plane_offsets, plane_size, bytes_per_tile, bit_msb, xoffs, yoffs):
    def decode(region, tile_idx):
        rgba = bytearray(TILE_W * TILE_H * 4)
        base = tile_idx * bytes_per_tile
        for y in range(TILE_H):
            for x in range(TILE_W):
                idx = base + xoffs[x] + yoffs[y]
                if idx >= plane_size:
                    continue
                color = 0
                for p in range(3):
                    pos = plane_offsets[p] + idx
                    if pos >= len(region):
                        continue
                    b = region[pos]
                    bit = (7 - (x % 8)) if bit_msb else (x % 8)
                    color |= ((b >> bit) & 1) << p
                r, g, bb, a = PALETTE[color & 3]
                off = (y * TILE_W + x) * 4
                rgba[off], rgba[off+1], rgba[off+2], rgba[off+3] = r, g, bb, a
        return rgba
    return decode


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mpb1 = (ROM_DIR / "mpb-1.3n").read_bytes()   # 4096
    mpb2 = (ROM_DIR / "mpb-2.3m").read_bytes()   # 4096

    regions = {
        "21_0fill": (mpb2 + mpb1 + b'\x00' * 4096),   # plane2=fill, plane1=mpb2, plane0=mpb1
        "12_0fill": (mpb1 + mpb2 + b'\x00' * 4096),   # plane2=fill, plane1=mpb1, plane0=mpb2
        "2_1_0":    (mpb2 + mpb1),                     # только mpb2+mpb1, 2 плоскости
    }

    # Варианты xoffs/yoffs:
    # A: xoffs = [0..7, 128..135], yoffs = [0,8,...,120]   (MAME STEP8/STEP16)
    # B: xoffs = [0..15],           yoffs = [0,1,...,15]    (прямой по строкам)
    # C: xoffs = [0..7, 16..23],    yoffs = [0,1,...,15]    (второй байт строки = +16)
    # D: xoffs = [0..7, 8..15],     yoffs = [0,1,...,15]    (второй байт = +8)
    A_x = [i for i in range(8)] + [128 + i for i in range(8)]
    A_y = [i * 8 for i in range(16)]
    B_x = list(range(16))
    B_y = list(range(16))
    C_x = [i for i in range(8)] + [16 + i for i in range(8)]
    C_y = list(range(16))
    D_x = list(range(16))
    D_y = list(range(16))

    # bytes_per_tile: 256 (MAME charincrement), 96 (16*16*3/8), 32 (плоскость 16*16/8)
    # n_tiles: 16 (region/256), 128 (region/96 по plane)
    # plane_offsets: [0x2000, 0, 0x1000] (MAME) или [0, 0x1000, 0x2000]

    combos = []
    # region "21_0fill" (mpb2+mpb1+zeros), plane_size=4096
    for xname, xs, ys in [("A", A_x, A_y), ("B", B_x, B_y), ("C", C_x, C_y), ("D", D_x, D_y)]:
        for msb in [True, False]:
            # MAME offsets
            combos.append((f"21_0fill_{xname}_{'msb' if msb else 'lsb'}_pl_2000_0_1000_bpt256_n16",
                          "21_0fill", 4096, 256, [0x2000, 0, 0x1000], msb, xs, ys, 16))
            combos.append((f"21_0fill_{xname}_{'msb' if msb else 'lsb'}_pl_0_1000_2000_bpt256_n16",
                          "21_0fill", 4096, 256, [0, 0x1000, 0x2000], msb, xs, ys, 16))

    # region "2_1_0" (2 planes, mpb2+mpb1), plane_size=4096
    for xname, xs, ys in [("A", A_x, A_y), ("C", C_x, C_y)]:
        for msb in [True, False]:
            combos.append((f"21_{xname}_{'msb' if msb else 'lsb'}_pl_0_1000_bpt256_n16",
                          "21_0fill", 4096, 256, [0, 0x1000, 0x2000], msb, xs, ys, 16))

    for name, rk, ps, bpt, po, msb, xs, ys, n in combos:
        region = regions[rk]
        dec = make_decoder(po, ps, bpt, msb, xs, ys)
        make_sheet(region, n, dec, name)

    print(f"\n[i] Всего {len(combos)} вариантов")


if __name__ == "__main__":
    main()
