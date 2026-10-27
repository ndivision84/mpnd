#!/usr/bin/env python3
"""extract_known.py — mpe-4 (charset), mpe-5 (HUD+спрайты), mp-s1. Split 2K + MSB."""
import struct, zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SCRIPT_DIR.parent
ROM_DIR = REPO_DIR / "orig_rom"
OUT_DIR = SCRIPT_DIR / "assets" / "tiles"

TILE_W = TILE_H = 8
TILES_PER_ROW = 16
PALETTE = [(0,0,0), (0xCC,0x66,0), (0xFF,0xFF,0xFF), (0x88,0x44,0)]

FILES = ["mpe-4.3f", "mpe-5.3e", "mp-s1.1a"]

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

def decode_split(rom, tile_idx):
    ps = 2048
    if tile_idx >= 256: return None
    b0, b1 = tile_idx*8, ps + tile_idx*8
    if b1 + 8 > len(rom): return None
    px = [[0]*8 for _ in range(8)]
    for y in range(8):
        p0, p1 = rom[b0+y], rom[b1+y]
        for x in range(8):
            bit = 7 - x
            px[y][x] = (((p1>>bit)&1)<<1) | ((p0>>bit)&1)
    return px

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for fname in FILES:
        p = ROM_DIR / fname
        if not p.exists():
            print(f"[{fname}] MISSING"); continue
        rom = p.read_bytes()
        n = 256
        rows = (n + TILES_PER_ROW - 1) // TILES_PER_ROW
        w, h = TILES_PER_ROW*TILE_W, rows*TILE_H
        rgb = bytearray(w*h*3)
        for t in range(n):
            px = decode_split(rom, t)
            if not px: continue
            tr, tc = divmod(t, TILES_PER_ROW)
            bx, by = tc*8, tr*8
            for y in range(8):
                for x in range(8):
                    r,g,b = PALETTE[px[y][x] & 3]
                    idx = ((by+y)*w+(bx+x))*3
                    rgb[idx], rgb[idx+1], rgb[idx+2] = r,g,b
        out = OUT_DIR / f"tiles_{fname.replace('.', '_')}.png"
        out.write_bytes(make_png(w, h, rgb))
        print(f"  {out.name}  (256 tiles)")

if __name__ == "__main__":
    main()
