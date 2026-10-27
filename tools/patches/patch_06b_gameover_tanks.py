#!/usr/bin/env python3
"""patch_06b_gameover_tanks.py

Исправляет:
1. glyphs: ВСЕ буквы заново (M, O, G, V, R, P — читаемые)
2. bounds: 19 → 23 (P)
3. draw_text: добавлен 'P'
4. Тарелки: 56×36, белый корпус + чёрная обводка
5. Высота тарелок: y = 120..200 (выше)
6. Коллизия: 30×22 (под новый размер)
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ──────────────────────────────────────────────────────────
# 1) Заменить ВСЮ таблицу glyphs (24 глифа)
# ──────────────────────────────────────────────────────────
new_glyphs = """    static const uint8_t glyphs[][5] = {
        {0x7,0x5,0x5,0x5,0x7}, // 0
        {0x2,0x6,0x2,0x2,0x7}, // 1
        {0x7,0x1,0x7,0x4,0x7}, // 2
        {0x7,0x1,0x7,0x1,0x7}, // 3
        {0x5,0x5,0x7,0x1,0x1}, // 4
        {0x7,0x4,0x7,0x1,0x7}, // 5
        {0x7,0x4,0x7,0x5,0x7}, // 6
        {0x7,0x1,0x1,0x1,0x1}, // 7
        {0x7,0x5,0x7,0x5,0x7}, // 8
        {0x7,0x5,0x7,0x1,0x7}, // 9
        {0x7,0x2,0x2,0x2,0x2}, // T (10)
        {0x7,0x2,0x2,0x2,0x7}, // I (11)
        {0x7,0x7,0x5,0x5,0x5}, // M (12) - полная+полная+2 вертикали
        {0x7,0x4,0x6,0x4,0x7}, // E (13)
        {0x3,0x4,0x4,0x4,0x3}, // C (14)
        {0x2,0x5,0x7,0x5,0x5}, // A (15)
        {0x5,0x5,0x5,0x5,0x7}, // U (16)
        {0x5,0x7,0x7,0x5,0x5}, // N (17)
        {0x3,0x4,0x2,0x1,0x6}, // S (18)
        {0x7,0x5,0x5,0x5,0x7}, // O (19) - полная+2 верт+полная
        {0x7,0x4,0x7,0x5,0x7}, // G (20) - с полной серединой
        {0x5,0x5,0x5,0x5,0x2}, // V (21) - 4 верт + точка внизу
        {0x6,0x5,0x6,0x5,0x5}, // R (22) - OK
        {0x7,0x4,0x7,0x4,0x4}, // P (23) - верх+лев+середина+лев+лев
    };"""

# Найдём блок `static const uint8_t glyphs[][5] = { ... };`
pattern = r'    static const uint8_t glyphs\[\]\[5\] = \{.*?\n    \};'
new_s, n = re.subn(pattern, new_glyphs, s, count=1, flags=re.DOTALL)
if n == 1:
    s = new_s; changes += 1
    print("OK: glyphs — все 24 глифа переписаны")
else:
    print("!! не найден блок glyphs")

# ──────────────────────────────────────────────────────────
# 2) bounds 19 → 23
# ──────────────────────────────────────────────────────────
for old, new in [
    ("if (code < 0 || code > 19) return;", "if (code < 0 || code > 23) return;"),
    ("if (code < 0 || code > 22) return;", "if (code < 0 || code > 23) return;"),
]:
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print(f"OK: bounds → 23 ({old})")
        break
else:
    print("!! не найден bounds")

# ──────────────────────────────────────────────────────────
# 3) draw_text: добавить 'P' → 23
# ──────────────────────────────────────────────────────────
if "*p == 'P'" not in s:
    old = "        else if (*p == 'R') code = 22;"
    new = """        else if (*p == 'R') code = 22;
        else if (*p == 'P') code = 23;"""
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: draw_text + P (23)")
    else:
        print("!! не найден '*p == R'")
else:
    print("[i] P уже есть")

# ──────────────────────────────────────────────────────────
# 4) Высота тарелок 150..240 → 120..200
# ──────────────────────────────────────────────────────────
old = "s->enemies[i].y = 150.0f + (float)(rand() % 90);"
new = "s->enemies[i].y = 120.0f + (float)(rand() % 80);"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: тарелки выше (y = 120–200)")

# ──────────────────────────────────────────────────────────
# 5) Тарелки 56×36, белый + чёрная обводка (заменяем весь блок)
# ──────────────────────────────────────────────────────────
old_pattern = r"    // ── Отрисовка тарелок.*?\n    \}"
# Найдём в новом блоке отрисовки тарелок. Он мог быть 52×32 из патча 06 — заменим на новый 56×36.
# Но если патч 06 не применялся (тарелки 36×18) — тоже заменим.
# Используем якорь на начало блока
anchor = "    // ── Отрисовка тарелок"
idx = s.find(anchor)
if idx >= 0:
    # Найдём закрывающую } после блока
    depth = 0
    end_idx = idx
    for i in range(idx, min(idx + 2000, len(s))):
        if s[i] == '{': depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth < 0 or (depth == 0 and s[i] == '}' and 'for' not in s[i-1: i-5:-1]):
                pass
        if depth == 0 and i > idx + 50 and s[i] == '}':
            end_idx = i + 1
            break
    # Простой подход: до второго `}` после начала цикла for
    # Найдём `\n    }\n` от начала блока
    end_marker = s.find("\n    }\n", idx)
    if end_marker > 0:
        end_idx = end_marker + len("\n    }")
    old_block = s[idx:end_idx]
    new_block = """    // ── Отрисовка тарелок (56×36, белый + чёрная обводка) ──
    for (int e = 0; e < 5; ++e) {
        if (!s->enemies[e].active) continue;
        float ex = s->enemies[e].x, ey = s->enemies[e].y;

        // Чёрная обводка корпуса
        SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
        SDL_FRect out_body = { ex - 28, ey - 8, 56, 22 };
        SDL_RenderFillRect(s->renderer, &out_body);

        // Белый корпус
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0xFF, 255);
        SDL_FRect body = { ex - 24, ey - 4, 48, 14 };
        SDL_RenderFillRect(s->renderer, &body);

        // Чёрная обводка купола
        SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
        SDL_FRect out_dome = { ex - 16, ey - 22, 32, 16 };
        SDL_RenderFillRect(s->renderer, &out_dome);

        // Белый купол
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0xFF, 255);
        SDL_FRect dome = { ex - 12, ey - 20, 24, 12 };
        SDL_RenderFillRect(s->renderer, &dome);

        // Чёрная кабина
        SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
        SDL_FRect cockpit = { ex - 8, ey - 18, 16, 8 };
        SDL_RenderFillRect(s->renderer, &cockpit);

        // Антенна
        SDL_FRect antenna = { ex - 1, ey - 30, 2, 8 };
        SDL_RenderFillRect(s->renderer, &antenna);
    }"""
    s = s[:idx] + new_block + s[end_idx:]
    changes += 1
    print("OK: тарелки 56×36, белый корпус + чёрная обводка")
else:
    print("!! не найден блок 'Отрисовка тарелок'")

# ──────────────────────────────────────────────────────────
# 6) Коллизия под новый размер
# ──────────────────────────────────────────────────────────
for old, new in [
    ("""            if (fabs(s->bullets[b].x - s->enemies[e].x) < 24 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 16) {""",
     """            if (fabs(s->bullets[b].x - s->enemies[e].x) < 30 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 22) {"""),
    ("""            if (fabs(s->bullets[b].x - s->enemies[e].x) < 28 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 20) {""",
     """            if (fabs(s->bullets[b].x - s->enemies[e].x) < 30 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 22) {"""),
]:
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: коллизия пуля×тарелка — 30×22")
        break

# ──────────────────────────────────────────────────────────
# 7) Убрать SDL_RenderDebugText (артефакт «0 1 0»)
# ──────────────────────────────────────────────────────────
if "SDL_RenderDebugText" in s:
    s = re.sub(r'[^\n]*SDL_RenderDebugText[^\n]*\n', '', s)
    changes += 1
    print("OK: SDL_RenderDebugText удалён (артефакт 0/1/0)")
else:
    print("[i] SDL_RenderDebugText нет")

p.write_text(s)
print(f"\nИзменено: {changes}/7")
