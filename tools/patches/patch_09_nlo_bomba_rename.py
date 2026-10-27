#!/usr/bin/env python3
"""patch_09_nlo_bomba_rename.py

1. Горизонтальная пуля: y = sy - 200 → sy - 24 (из пушки).
2. Rename: Enemy → NLO, enemies[] → nlos[], Bomb → BOMBA, bombs[] → bombas[].
3. Добавить коллизию вертикальная пуля × NLO (b=5..9, NLO).
4. SDL_Log "HIT plate!" → "HIT NLO!".
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) Горизонтальная пуля из пушки (не в воздухе)
# ═══════════════════════════════════════════════════════════════
old = "s->bullets[i].y    = sy - 200;"
new = "s->bullets[i].y    = sy - 24;"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: горизонтальная пуля из пушки (y-24)")
else:
    print("!! не найдено 'sy - 200'")

# ═══════════════════════════════════════════════════════════════
# 2) Rename Enemy → NLO
# ═══════════════════════════════════════════════════════════════
renames_enemy = [
    ("struct Enemy {", "struct NLO {"),
    ("Enemy         enemies[5];", "NLO           nlos[5];"),
    ("s->enemies[", "s->nlos["),
    ("AppState::MAX_ENEMIES", "AppState::MAX_NLOS"),
    ("static constexpr int MAX_ENEMIES", "static constexpr int MAX_NLOS"),
    ("HIT plate! score=%d", "HIT NLO! score=%d"),
]
for old, new in renames_enemy:
    n = s.count(old)
    if n > 0:
        s = s.replace(old, new)
        changes += 1
        print(f"OK: {old[:28]}... → ({n}x)")

# ═══════════════════════════════════════════════════════════════
# 3) Rename Bomb → BOMBA
# ═══════════════════════════════════════════════════════════════
renames_bomb = [
    ("struct Bomb {", "struct BOMBA {"),
    ("Bomb          bombs[5];", "BOMBA         bombas[5];"),
    ("s->bombs[", "s->bombas["),
    ("AppState::MAX_BOMBS", "AppState::MAX_BOMBAS"),
    ("static constexpr int MAX_BOMBS", "static constexpr int MAX_BOMBAS"),
    ('SDL_Log("bomb spawned', 'SDL_Log("BOMBA spawned'),
]
for old, new in renames_bomb:
    n = s.count(old)
    if n > 0:
        s = s.replace(old, new)
        changes += 1
        print(f"OK: {old[:28]}... → ({n}x)")

# ═══════════════════════════════════════════════════════════════
# 4) Добавить коллизию: вертикальная пуля × NLO
#    Вставить после блока "гориз. пули × NLO"
# ═══════════════════════════════════════════════════════════════
# Найдём блок коллизии горизонтальная × NLO
anchor = """    // ── Коллизии: верт. пули × бомбы ──"""
insert = """    // ── Коллизии: верт. пули × NLO ──
    for (int b = 5; b < 10; ++b) {
        if (!s->bullets[b].active) continue;
        for (int e = 0; e < 5; ++e) {
            if (!s->nlos[e].active) continue;
            if (fabs(s->bullets[b].x - s->nlos[e].x) < 30 &&
                fabs(s->bullets[b].y - s->nlos[e].y) < 30) {
                s->nlos[e].active = false;
                s->bullets[b].active = false;
                s->score += 100;
                if (s->score > 99999) s->score = 99999;
                SDL_Log("HIT NLO (vertical)! score=%d", s->score);
                break;
            }
        }
    }

    // ── Коллизии: верт. пули × BOMBA ──"""
if anchor in s:
    s = s.replace(anchor, insert, 1); changes += 1
    print("OK: добавлена коллизия верт. пуля × NLO")
else:
    print("!! не найден блок 'Коллизии: верт. пули × бомбы'")

p.write_text(s)
print(f"\nИзменено блоков: {changes}")
