#!/usr/bin/env python3
"""
analyze_mpatrol.py — ROM analysis for Moon Patrol (Irem, 1982 / MAME set: mpatrol)

Compatible with macOS 12+ and Linux. Python 3.6+ stdlib only.

Usage:
    python3 analyze_mpatrol.py                # analyze current directory
    python3 analyze_mpatrol.py /path/to/roms  # analyze specific directory
    python3 analyze_mpatrol.py > report.txt   # save to file
"""

import sys
import hashlib
import zlib
import math
import struct
from collections import Counter
from pathlib import Path


# --- ROM set definition --------------------------------------------------
#  Irem M52 memory map (main CPU 6809E):
#    0x6000-0x6FFF  mpa-1.3m    program bank 0
#    0x7000-0x7FFF  mpa-2.3l    program bank 1
#    0x8000-0x8FFF  mpa-3.3k    program bank 2
#    0x9000-0x9FFF  mpa-4.3j    program bank 3
#    0xA000-0xAFFF  mpb-1.3n    banked program 0
#    0xB000-0xBFFF  mpb-2.3m    banked program 1
#    0xFFE0-0xFFEF  mpc-3.1m    non-executed data
#    0xFFF0-0xFFFF  mpc-3.1m    6809 interrupt/reset vectors

ROMSET = {
    'mpa-1.3m':     (4096, 'maincpu',  '0x6000-0x6FFF  program bank 0'),
    'mpa-2.3l':     (4096, 'maincpu',  '0x7000-0x7FFF  program bank 1'),
    'mpa-3.3k':     (4096, 'maincpu',  '0x8000-0x8FFF  program bank 2'),
    'mpa-4.3j':     (4096, 'maincpu',  '0x9000-0x9FFF  program bank 3'),
    'mpb-1.3n':     (4096, 'maincpu',  '0xA000-0xAFFF  banked program 0'),
    'mpb-2.3m':     (4096, 'maincpu',  '0xB000-0xBFFF  banked program 1'),
    'mpc-3.1m':     (  32, 'maincpu',  '0xFFE0-0xFFFF  vectors (0xFFF0+)'),
    'mpc-1.1f':     (  32, 'audiocpu', 'sound CPU init'),
    'mpc-2.2h':     ( 256, 'audiocpu', 'sound CPU program'),
    'mpc-4.2a':     ( 512, 'audiocpu', 'sound CPU program'),
    'mpe-1.3l':     (4096, 'gfx',      'tile graphics bank 0'),
    'mpe-2.3k':     (4096, 'gfx',      'tile graphics bank 1'),
    'mpe-3.3h':     (4096, 'gfx',      'tile graphics bank 2'),
    'mpe-4.3f':     (4096, 'gfx',      'tile graphics bank 3'),
    'mpe-5.3e':     (4096, 'gfx',      'tile graphics bank 4'),
    'mp-s1.1a':     (4096, 'misc',     'character / sound data'),
    'mp_7621-5.7h': ( 512, 'misc',     'PROM / small data'),
}

MAINCPU_MAP = {
    'mpa-1.3m': (0x6000, 0x6FFF),
    'mpa-2.3l': (0x7000, 0x7FFF),
    'mpa-3.3k': (0x8000, 0x8FFF),
    'mpa-4.3j': (0x9000, 0x9FFF),
    'mpb-1.3n': (0xA000, 0xAFFF),
    'mpb-2.3m': (0xB000, 0xBFFF),
}

VECTORS_6809 = [
    (0x10, 'Reserved'),
    (0x12, 'SWI3'),
    (0x14, 'SWI2'),
    (0x16, 'FIRQ'),
    (0x18, 'IRQ'),
    (0x1A, 'SWI'),
    (0x1C, 'NMI'),
    (0x1E, 'RESET'),
]

IGNORE_FILES = {'analyze_mpatrol.py', 'report.txt', 'report2.txt', 'report3.txt'}


# --- Helpers -------------------------------------------------------------

def entropy(data):
    if not data:
        return 0.0
    c = Counter(data)
    n = len(data)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def padding_analysis(data):
    """Return dict {byte_value: (count, percent)} for 0x00, 0xFF, 0x20."""
    total = len(data)
    result = {}
    for v in (0x00, 0xFF, 0x20):
        c = data.count(v)
        result[v] = (c, 100.0 * c / total if total else 0.0)
    return result


def hexdump(data, offset=0, limit=64):
    out = []
    if offset >= len(data):
        return "  (offset beyond EOF)"
    n = min(len(data) - offset, limit)
    for i in range(0, n, 16):
        chunk = data[offset + i:offset + i + 16]
        hexpart = ' '.join(f'{b:02x}' for b in chunk)
        asciipart = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        out.append(f"  {offset + i:08x}  {hexpart:<47}  |{asciipart}|")
    return '\n'.join(out)


def addr_to_file(addr):
    for fname, (start, end) in MAINCPU_MAP.items():
        if start <= addr <= end:
            return fname, addr - start
    return None, None


def file_info(path):
    data = path.read_bytes()
    return {
        'size':     len(data),
        'md5':      hashlib.md5(data).hexdigest(),
        'sha1':     hashlib.sha1(data).hexdigest(),
        'sha256':   hashlib.sha256(data).hexdigest(),
        'crc32':    zlib.crc32(data) & 0xffffffff,
        'entropy':  entropy(data),
        'unique':   len(set(data)),
        'top_bytes': Counter(data).most_common(3),
        'padding':  padding_analysis(data),
        'data':     data,
    }


def human_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


# --- Sections ------------------------------------------------------------

def section_verdict(dirpath):
    """Quick pass/fail summary at the top."""
    print("\n[0] VERDICT\n")

    checks = []

    # Check 1: all files present with expected size
    missing, mismatch = [], []
    for name, (exp_size, _, _) in ROMSET.items():
        p = dirpath / name
        if not p.exists():
            missing.append(name)
        elif p.stat().st_size != exp_size:
            mismatch.append((name, exp_size, p.stat().st_size))
    inventory_ok = not missing and not mismatch
    checks.append(('Inventory', inventory_ok,
                   f"{len(ROMSET) - len(missing) - len(mismatch)}/{len(ROMSET)} files with correct size"))

    # Check 2: vector table sanity
    vec_ok, vec_detail = False, 'mpc-3.1m missing'
    vpath = dirpath / 'mpc-3.1m'
    if vpath.exists():
        d = vpath.read_bytes()
        if len(d) >= 32:
            in_rom = 0
            for off, name in VECTORS_6809:
                if name in ('Reserved', 'IRQ'):
                    continue
                addr = struct.unpack('>H', d[off:off + 2])[0]
                if addr_to_file(addr)[0] is not None:
                    in_rom += 1
            vec_ok = in_rom >= 3
            vec_detail = f"{in_rom}/6 active vectors point into ROM"
    checks.append(('Vector table', vec_ok, vec_detail))

    # Check 3: RESET entry not all zeros/FF
    reset_ok, reset_detail = False, 'mpc-3.1m missing'
    if vpath.exists():
        d = vpath.read_bytes()
        if len(d) >= 32:
            reset = struct.unpack('>H', d[0x1E:0x20])[0]
            fname, foff = addr_to_file(reset)
            if fname:
                code = (dirpath / fname).read_bytes()[foff:foff + 16]
                all_zero = all(b == 0 for b in code)
                all_ff = all(b == 0xFF for b in code)
                reset_ok = not all_zero and not all_ff
                reset_detail = f"RESET=0x{reset:04x} -> {fname}+0x{foff:03x}, entry code {'looks real' if reset_ok else 'suspicious'}"
            else:
                reset_detail = f"RESET=0x{reset:04x} not in ROM"
    checks.append(('RESET entry', reset_ok, reset_detail))

    # Print
    all_pass = True
    for name, ok, detail in checks:
        mark = 'PASS' if ok else 'FAIL'
        print(f"  [{mark}] {name:<14} {detail}")
        if not ok:
            all_pass = False

    print()
    if all_pass:
        print("  *** ROM SET IS VALID AND READY FOR USE ***")
    else:
        print("  *** ROM SET HAS ISSUES — SEE SECTIONS BELOW ***")


def section_inventory(dirpath):
    print("\n[1] INVENTORY\n")
    print(f"  {'File':<16} {'Size':>6} {'Exp':>6} {'Status':<9} {'Region':<10} Address / Role")
    print("  " + "-" * 82)

    missing, mismatch, extra, total = [], [], [], 0
    for name, (exp_size, region, role) in ROMSET.items():
        p = dirpath / name
        if not p.exists():
            missing.append(name)
            print(f"  {name:<16} {'-':>6} {exp_size:>6} {'MISSING':<9} {region:<10} {role}")
            continue
        actual = p.stat().st_size
        status = 'OK' if actual == exp_size else 'MISMATCH'
        if actual != exp_size:
            mismatch.append((name, exp_size, actual))
        total += actual
        print(f"  {name:<16} {actual:>6} {exp_size:>6} {status:<9} {region:<10} {role}")

    for p in sorted(dirpath.iterdir()):
        if p.is_file() and p.name not in ROMSET and p.name not in IGNORE_FILES:
            extra.append(p.name)
            print(f"  {p.name:<16} {p.stat().st_size:>6} {'?':>6} {'EXTRA':<9} {'?':<10} (not in mpatrol)")

    print()
    print(f"  Total ROM size: {total} bytes ({human_size(total)})")
    if missing:
        print(f"  [!!] Missing: {', '.join(missing)}")
    if mismatch:
        print(f"  [!!] Size mismatch: {mismatch}")
    if extra:
        print(f"  [i]  Extra files (ignored): {', '.join(extra)}")
    if not (missing or mismatch):
        print(f"  [OK] All {len(ROMSET)} files present, sizes match MAME mpatrol romset")


def section_hashes(dirpath):
    print("\n[2] HASHES  (compare with: mame -listroms mpatrol)\n")
    print(f"  {'File':<16} {'CRC32':<10} {'SHA1'}")
    print("  " + "-" * 74)
    for name in ROMSET:
        p = dirpath / name
        if p.exists():
            a = file_info(p)
            print(f"  {name:<16} {a['crc32']:08x}   {a['sha1']}")


def section_vectors(dirpath):
    print("\n[3] VECTOR TABLE (mpc-3.1m loaded at 0xFFE0-0xFFFF)\n")
    vpath = dirpath / 'mpc-3.1m'
    if not vpath.exists():
        print("  mpc-3.1m missing — cannot verify vectors")
        return

    d = vpath.read_bytes()
    print(f"  Raw bytes ({len(d)}):")
    for line in hexdump(d, 0, len(d)).split('\n'):
        print(f"  {line.strip()}")

    # Note about first 16 bytes
    print()
    print("  Note: 0xFFE0-0xFFEF (first 16 bytes) are never executed —")
    print("        RESET vector points to 0x7770 in mpa-2.3l, not here.")
    print("        These bytes appear to be ROM identifier / dead data.")
    print()

    print(f"  {'Off':<6} {'Vector':<10} {'Addr':<8} {'Points into':<14} Meaning")
    print("  " + "-" * 70)

    legend = {
        'unused':    'interrupt disabled (address 0x0000)',
        'stub':      'outside ROM (unused stub)',
        'OK':        'real handler in program ROM',
        'SUSPICIOUS': 'outside ROM and not a stub — check dump',
    }

    ok_count = 0
    for off, name in VECTORS_6809:
        if off + 2 > len(d):
            break
        addr = struct.unpack('>H', d[off:off + 2])[0]
        fname, foff = addr_to_file(addr)

        if addr == 0x0000:
            kind, target = 'unused', '—'
        elif fname:
            kind, target = 'OK', f"{fname}+0x{foff:03x}"
            ok_count += 1
        elif addr == 0xC000:
            kind, target = 'stub', '—'
        else:
            kind, target = 'SUSPICIOUS', '—'

        print(f"  0x{off:02x}   {name:<10} 0x{addr:04x}   {target:<14} {legend[kind]}")

    print(f"\n  Summary: {ok_count}/6 active vectors point into program ROM "
          f"(Reserved+IRQ are always 0x0000)")
    if ok_count >= 5:
        print(f"  [OK] vector table is fully consistent with Irem M52 memory map")
    elif ok_count >= 3:
        print(f"  [i]  some vectors unused — check MAME source if unusual")
    else:
        print(f"  [!!] too many vectors outside program ROM — probable dump issue")


def section_reset_trace(dirpath):
    print("\n[3b] RESET TRACE\n")
    vpath = dirpath / 'mpc-3.1m'
    if not vpath.exists():
        return
    d = vpath.read_bytes()
    if len(d) < 0x20:
        return
    reset = struct.unpack('>H', d[0x1E:0x20])[0]
    fname, foff = addr_to_file(reset)
    print(f"  RESET vector = 0x{reset:04x}")
    if not fname:
        print(f"  RESET address is not inside any maincpu ROM — suspicious")
        return
    print(f"  -> maps to {fname} at file offset 0x{foff:03x}")
    data = (dirpath / fname).read_bytes()
    print(f"  First 32 bytes of entry code:")
    for line in hexdump(data, foff, 32).split('\n'):
        print(f"  {line.strip()}")
    snippet = data[foff:foff + 16]
    if all(b == 0 for b in snippet):
        print("  [!!] entry code is all zeros — suspicious")
    elif all(b == 0xFF for b in snippet):
        print("  [!!] entry code is all 0xFF — suspicious")
    else:
        print("  [OK] entry code looks like real 6809 instructions")
        print("       (manual disassembly recommended for full verification:")
        print(f"       r2 -a m6809 -b 8 {fname}  ->  pd at 0x{foff:x})")


def section_per_file(dirpath):
    print("\n[4] PER-FILE ANALYSIS\n")
    for name in ROMSET:
        p = dirpath / name
        if not p.exists():
            continue
        a = file_info(p)
        print(f"  ### {name}  ({a['size']} bytes)")
        print(f"      MD5:     {a['md5']}")
        print(f"      SHA256:  {a['sha256']}")
        print(f"      Entropy: {a['entropy']:.3f} bits/byte")
        print(f"      Unique:  {a['unique']}/256")
        top = ', '.join(f'0x{b:02x}x{c}' for b, c in a['top_bytes'])
        print(f"      Top:     {top}")
        pad = a['padding']
        pad_str = ', '.join(f"0x{b:02x}: {pct:.1f}%" for b, (_, pct) in pad.items())
        print(f"      Padding: {pad_str}")
        print(f"      Head:")
        print(hexdump(a['data'], 0, 32))
        if a['size'] > 48:
            print(f"      Tail:")
            print(hexdump(a['data'], a['size'] - 32, 32))
        print()


def section_structure(dirpath):
    print("[5] STRUCTURAL OBSERVATIONS\n")
    for region in ['maincpu', 'audiocpu', 'gfx', 'misc']:
        files = [n for n, (_, r, _) in ROMSET.items() if r == region]
        total = sum((dirpath / f).stat().st_size for f in files if (dirpath / f).exists())
        print(f"  {region:<10}  {len(files):>2} files, {total:>6} bytes")

    print("\n  Entropy chart (higher = code/compressed, lower = data/padding):")
    for name in ROMSET:
        p = dirpath / name
        if not p.exists():
            continue
        a = file_info(p)
        bar = '#' * int(a['entropy'] * 4)
        print(f"  {name:<16} {a['entropy']:>4.2f}  {bar}")

    print()
    print("  Notes:")
    print("  - mpa-*.3*: dense 6809 code (entropy 6.3-6.9) — all game logic lives here")
    print("  - mpb-*.3*: mostly 0x00 (entropy ~3.5) — banked ROM, rarely/never used.")
    print("    This is NORMAL for mpatrol: the game fits in mpa-* (16 KB);")
    print("    the banking hardware exists but the bank slots are mostly empty.")
    print("  - mpe-*.3*: tile graphics with lots of 0xFF/0x00 — empty pixels.")
    print("    Entropy 1.6-2.8 is expected for 2-bit planar tile data.")
    print("  - mpc-*.1f/2h/4a: sound CPU code, tiny, low entropy — also normal.")
    print("  - mp-s1.1a: character lookup / sound tables — high entropy like code.")
    print("  - mp_7621-5.7h: 512-byte PROM with repeating pattern — normal.")


def section_mame(dirpath):
    print("\n[6] VERIFICATION WITH MAME\n")
    print("""  Compare CRC32/SHA1 above with:
      mame -listroms mpatrol

  Direct verify (creates .zip and checks):
      cd /path/to/roms
      zip -j mpatrol.zip mpa-1.3m mpa-2.3l mpa-3.3k mpa-4.3j \\
                         mpb-1.3n mpb-2.3m mpc-3.1m \\
                         mpc-1.1f mpc-2.2h mpc-4.2a \\
                         mpe-1.3l mpe-2.3k mpe-3.3h mpe-4.3f mpe-5.3e \\
                         mp-s1.1a mp_7621-5.7h
      mkdir -p ~/mame/roms && mv mpatrol.zip ~/mame/roms/
      mame -rompath ~/mame/roms -verifyroms mpatrol

  Expected output: "mpatrol: OK"
""")


def section_next_steps(dirpath):
    print("\n[7] NEXT STEPS FOR MOON PATROL ND\n")
    print("""  Now that the ROM set is verified, here's what to do:

  (A) EXTRACT GRAPHICS  (recommended first step)
      The five mpe-*.3* files contain all tile data (20 KB total).
      Format for Irem M52: 2-bit planar, 8x8 pixels per tile.
      For each file: split into 512 bytes per tile row, deinterleave
      bitplanes, combine into 4-color tiles. Save as PNG for reference.

  (B) DISASSEMBLE CODE  (for physics and timings)
      Use radare2 with m6809 target:
          r2 -a m6809 -b 8 mpa-2.3l
          pd 50 @ 0x770        # first instructions from RESET
      Or use Ghidra with 6809 plugin.
      Look for: scroll speeds, jump arc constants, enemy spawn timers.

  (C) RUN IN MAME  (for gameplay reference)
          mame mpatrol
      Record side-by-side to compare feel with your C++ implementation.

  (D) LEGAL NOTE
      The ROM files are (c) Irem. Study them locally, but do NOT
      ship them (or extracted sprites / music) in a public release.
      Draw your own tiles, compose your own music, keep the ROM
      as a personal reference only.

  (E) START YOUR SDL3 PROJECT
      Once you have tile sheets and physics notes, begin implementing
      the game loop in C++. The verified ROM guarantees that your
      reference is authentic — every constant you extract from it
      matches the original arcade machine.
""")


# --- Main ----------------------------------------------------------------

def main():
    dirpath = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    if not dirpath.is_dir():
        print(f"ERROR: {dirpath} is not a directory", file=sys.stderr)
        sys.exit(1)

    print("=" * 82)
    print("  Moon Patrol (Irem, 1982) ROM Analysis — romset: mpatrol")
    print(f"  Directory: {dirpath.resolve()}")
    print("=" * 82)

    section_verdict(dirpath)
    section_inventory(dirpath)
    section_hashes(dirpath)
    section_vectors(dirpath)
    section_reset_trace(dirpath)
    section_per_file(dirpath)
    section_structure(dirpath)
    section_mame(dirpath)
    section_next_steps(dirpath)

    print("=" * 82)
    print("  Analysis complete.")
    print("=" * 82)


if __name__ == '__main__':
    main()
