#!/usr/bin/env python3
"""patch_36_zones_system.py — 26 зон A-Z, 8 групп, чек-поинты, жизни.

Модель:
  - world_x → zone_index = world_x / ZONE_DISTANCE (cap на 25/Z)
  - zone_time — секунды в текущей зоне (растёт, сбрасывается при переходе)
  - checkpoint_zone = первая буква текущей группы
  - При смерти: lives--, respawn с checkpoint_zone; lives==0 → GAME_OVER
  - HUD: "A 12" | "001400" | "L3 NORMAL"
  - play_time (60-сек countdown) полностью удалён

Группы (8): A(0) | B-E(1-4) | F-I(5-8) | J-M(9-12) | N-Q(13-16) | R-U(17-20) | V-Y(21-24) | Z(25)

Зависит от: patch_33, patch_35b.
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

print("=== ДИАГНОСТИКА (до) ===\n")

if 'ZONES_TOTAL' in s or 'zone_index' in s:
    print("  УЖЕ ПРИМЕНЁН — выход.")
    raise SystemExit(0)

print(f"  play_time refs:      {len(re.findall(r'play_time', s))}")
print(f"  TIME UP check:       {'есть' if 's->play_time >= 60.0f' in s else 'нет'}")
print(f"  player_died:         {'есть' if 'player_died' in s else 'нет'}")
print(f"  reset (play_time):   {len(re.findall(r's->play_time = 0\\.0f;', s))}")

print("\n=== ПРИМЕНЕНИЕ ===\n")
changes = 0

# ─────────────────────────────────────────────────────────────
# 1. AppState: play_time → zone-поля
# ─────────────────────────────────────────────────────────────
old = '''    GameState     state = STATE_ATTRACT;
    float         state_timer = 0.0f;
    float         play_time   = 0.0f;   // секунды в PLAYING (для TIME)'''
new = '''    GameState     state = STATE_ATTRACT;
    float         state_timer = 0.0f;

    // ── Zones system (A..Z, 8 groups) ──
    static constexpr int   ZONES_TOTAL   = 26;      // A..Z
    static constexpr float ZONE_DISTANCE = 2000.0f; // px per zone
    static constexpr int   LIVES_START   = 3;
    int   zone_index      = 0;              // 0=A, 25=Z
    int   checkpoint_zone = 0;              // first letter of current group
    float zone_time       = 0.0f;           // seconds in current zone
    int   lives           = LIVES_START;'''
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: AppState — play_time → zone-поля")
else:
    print("FAIL: AppState блок не найден"); raise SystemExit(1)

# ─────────────────────────────────────────────────────────────
# 2. Helpers перед struct Player
# ─────────────────────────────────────────────────────────────
anchor = 'struct Player {'
helpers = '''
// ─────────────────────────────────────────────────────────────
// Zones helpers
// ─────────────────────────────────────────────────────────────
static char zone_letter(int idx) {
    if (idx < 0)  idx = 0;
    if (idx > 25) idx = 25;
    return (char)('A' + idx);
}

// Groups: A(0) | B-E(1-4) | F-I(5-8) | J-M(9-12) | N-Q(13-16) | R-U(17-20) | V-Y(21-24) | Z(25)
static int zone_group_first(int idx) {
    if (idx <= 0)  return 0;
    if (idx >= 25) return 25;
    return ((idx - 1) / 4) * 4 + 1;
}

static int zone_group_num(int idx) {
    if (idx <= 0)  return 1;
    if (idx >= 25) return 8;
    return ((idx - 1) / 4) + 2;
}

struct Player {'''
if helpers not in s and anchor in s:
    s = s.replace(anchor, helpers, 1); changes += 1
    print("OK: helpers zone_letter/zone_group_first/zone_group_num")

# ─────────────────────────────────────────────────────────────
# 3. player_died() перед SDL_AppIterate
# ─────────────────────────────────────────────────────────────
anchor2 = 'SDL_AppResult SDL_AppIterate(void* appstate) {'
died_fn = '''static void player_died(AppState* s, const char* reason) {
    SDL_Log("DEATH: %s (zone %c, lives: %d)",
            reason, zone_letter(s->zone_index), s->lives);
    s->lives--;
    if (s->lives <= 0) {
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
        SDL_Log("GAME OVER (out of lives)");
        return;
    }
    // Respawn at checkpoint
    s->zone_index    = s->checkpoint_zone;
    s->zone_time     = 0.0f;
    s->world_x       = s->checkpoint_zone * AppState::ZONE_DISTANCE + 50.0f;
    s->player.y      = 520.0f;
    s->player.vy     = 0.0f;
    s->player.offset_x = 0.0f;
    s->player.on_ground = true;
    for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
    for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
    for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
    s->obstacle_spawn_timer = 0.0f;
    s->enemy_spawn_timer    = 0.0f;
    s->bomb_spawn_timer     = 0.0f;
    SDL_Log("RESPAWN: zone %c (group %d), lives: %d",
            zone_letter(s->zone_index), zone_group_num(s->zone_index), s->lives);
}

SDL_AppResult SDL_AppIterate(void* appstate) {'''
if died_fn not in s and anchor2 in s:
    s = s.replace(anchor2, died_fn, 1); changes += 1
    print("OK: player_died() helper")

# ─────────────────────────────────────────────────────────────
# 4. Замена state = STATE_GAME_OVER на player_died() — 5 мест
# ─────────────────────────────────────────────────────────────
# PIT / ROCK / CRATER
for log_msg, reason in [('Fell into PIT!', 'PIT'),
                        ('Hit ROCK!', 'ROCK'),
                        ('Fell into CRATER!', 'CRATER')]:
    old = f's->state = STATE_GAME_OVER; s->state_timer = 0.0f;\n'
    # Найти контекст: log_msg сразу после
    pattern = re.compile(
        r's->state = STATE_GAME_OVER; s->state_timer = 0\.0f;\s*\n\s*'
        + re.escape(f'SDL_Log("{log_msg}");'))
    new = f'player_died(s, "{reason}");'
    s, n = pattern.subn(new, s, count=1)
    print(f"  {reason}: {n}")
    changes += n

# NLO death
old_nlo = '''        for (int e = 0; e < 5; ++e) {
            if (s->nlos[e].active &&
                fabs(px - s->nlos[e].x) < 32 &&
                fabs(py - s->nlos[e].y) < 32) {
                s->state = STATE_GAME_OVER; s->state_timer = 0.0f;
            }
        }'''
new_nlo = old_nlo.replace('s->state = STATE_GAME_OVER; s->state_timer = 0.0f;',
                          'player_died(s, "NLO");')
if old_nlo in s:
    s = s.replace(old_nlo, new_nlo, 1); changes += 1; print("  NLO: 1")

# BOMB death
old_bomb = '''        for (int bo = 0; bo < 5; ++bo) {
            if (s->bombas[bo].active &&
                fabs(px - s->bombas[bo].x) < 28 &&
                fabs(py - s->bombas[bo].y) < 32) {
                s->state = STATE_GAME_OVER; s->state_timer = 0.0f;
            }
        }'''
new_bomb = old_bomb.replace('s->state = STATE_GAME_OVER; s->state_timer = 0.0f;',
                            'player_died(s, "BOMB");')
if old_bomb in s:
    s = s.replace(old_bomb, new_bomb, 1); changes += 1; print("  BOMB: 1")

# ─────────────────────────────────────────────────────────────
# 5. Update loop: убрать TIME UP, добавить zone progression
# ─────────────────────────────────────────────────────────────
old_update = '''    s->play_time += dt;
    s->world_x += s->auto_speed * dt;

    // ★ Проверка окончания времени — ДО рендера (без кадра «TIME:00»)
    if (s->state == STATE_PLAYING && s->play_time >= 60.0f) {
        SDL_Log("TIME UP! play_time=%.1f -> GAME_OVER", s->play_time);
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
    }
'''
new_update = '''    s->world_x += s->auto_speed * dt;

    // ── Zone progression (только в PLAYING) ──
    if (s->state == STATE_PLAYING) {
        s->zone_time += dt;
        int new_zone = (int)(s->world_x / AppState::ZONE_DISTANCE);
        if (new_zone > AppState::ZONES_TOTAL - 1) new_zone = AppState::ZONES_TOTAL - 1;
        if (new_zone > s->zone_index) {
            int old_group = zone_group_num(s->zone_index);
            s->zone_index = new_zone;
            s->zone_time  = 0.0f;
            int new_group = zone_group_num(new_zone);
            if (new_group != old_group) {
                s->checkpoint_zone = zone_group_first(new_zone);
                SDL_Log("CHECKPOINT: zone %c (group %d)",
                        zone_letter(s->checkpoint_zone), new_group);
            }
            SDL_Log("ZONE: %c (group %d)",
                    zone_letter(new_zone), new_group);
        }
    }
'''
if old_update in s:
    s = s.replace(old_update, new_update, 1); changes += 1
    print("OK: update — zone progression, TIME UP removed")
else:
    print("FAIL: update блок не совпал")

# ─────────────────────────────────────────────────────────────
# 6. draw_hud: новая сигнатура
# ─────────────────────────────────────────────────────────────
old_hud = '''static void draw_hud(SDL_Renderer* r, int score, int time_left, float world_x, int difficulty) {
    (void)world_x;
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);

    constexpr float HUD_SCALE = 3.0f;
    constexpr float HUD_Y     = 20.0f;

    // TIME: XX — слева
    char tbuf[9];
    tbuf[0]='T'; tbuf[1]='I'; tbuf[2]='M'; tbuf[3]='E';
    tbuf[4]=':'; tbuf[5]=' ';
    tbuf[6]='0' + (time_left / 10) % 10;
    tbuf[7]='0' + time_left % 10;
    tbuf[8]=0;
    draw_text(r, 20.0f, HUD_Y, tbuf, HUD_SCALE);

    // Счёт — 5 цифр по центру
    char sbuf[8];
    for (int i = 0; i < 5; ++i) {
        sbuf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    sbuf[5] = 0;
    {
        const float sw = 5 * 6.0f * HUD_SCALE;
        draw_text(r, (800.0f - sw) / 2.0f, HUD_Y, sbuf, HUD_SCALE);
    }

    // MODE: <name> — справа (вместо CAUTION/DIFF)
    const char* mode_str = (difficulty == 0) ? "MODE: EASY" :
                           (difficulty == 2) ? "MODE: HARD" : "MODE: NORMAL";
    int nlen = 0;
    while (mode_str[nlen]) nlen++;
    const float cw = nlen * 6.0f * HUD_SCALE;
    draw_text(r, 800.0f - cw - 20.0f, HUD_Y, mode_str, HUD_SCALE);
}'''
new_hud = '''static void draw_hud(SDL_Renderer* r, int score, int zone_index, float zone_time, int lives, int difficulty) {
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);

    constexpr float HUD_SCALE = 3.0f;
    constexpr float HUD_Y     = 20.0f;

    // Слева: "A 12" — зона + секунды в ней
    char zbuf[8];
    zbuf[0] = zone_letter(zone_index);
    zbuf[1] = ' ';
    int sec = (int)zone_time;
    if (sec < 0)  sec = 0;
    if (sec > 99) sec = 99;
    zbuf[2] = '0' + (sec / 10) % 10;
    zbuf[3] = '0' + sec % 10;
    zbuf[4] = 0;
    draw_text(r, 20.0f, HUD_Y, zbuf, HUD_SCALE);

    // Счёт — 5 цифр по центру
    char sbuf[8];
    for (int i = 0; i < 5; ++i) {
        sbuf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    sbuf[5] = 0;
    {
        const float sw = 5 * 6.0f * HUD_SCALE;
        draw_text(r, (800.0f - sw) / 2.0f, HUD_Y, sbuf, HUD_SCALE);
    }

    // Справа: "L3 EASY" / "L3 NORMAL" / "L3 HARD"
    const char* mode_str = (difficulty == 0) ? "EASY" :
                           (difficulty == 2) ? "HARD" : "NORMAL";
    char rbuf[16];
    rbuf[0] = 'L';
    int lv = (lives < 0) ? 0 : ((lives > 9) ? 9 : lives);
    rbuf[1] = '0' + lv;
    rbuf[2] = ' ';
    int ri = 3;
    for (const char* q = mode_str; *q && ri < 15; ++q) rbuf[ri++] = *q;
    rbuf[ri] = 0;
    const float cw = ri * 6.0f * HUD_SCALE;
    draw_text(r, 800.0f - cw - 20.0f, HUD_Y, rbuf, HUD_SCALE);
}'''
if old_hud in s:
    s = s.replace(old_hud, new_hud, 1); changes += 1
    print("OK: draw_hud — новая сигнатура")

# ─────────────────────────────────────────────────────────────
# 7. Call site draw_hud
# ─────────────────────────────────────────────────────────────
old_call = '''    // HUD поверх
    // int score = (int)(s->world_x * 10);   // не используется
    int time_left = 60 - (int)s->play_time;
    if (time_left < 0) time_left = 0;
    draw_hud(s->renderer, s->score, time_left, s->world_x, s->difficulty);'''
new_call = '''    // HUD поверх
    draw_hud(s->renderer, s->score, s->zone_index, s->zone_time,
             s->lives, s->difficulty);'''
if old_call in s:
    s = s.replace(old_call, new_call, 1); changes += 1
    print("OK: draw_hud call site")

# ─────────────────────────────────────────────────────────────
# 8. Reset blocks: play_time → zone/lives (2 в старте + 1 в R)
# ─────────────────────────────────────────────────────────────
# Шаг A: ATTRACT и SPACE (имеют 'play_time = 0.0f;' + 'state = PLAYING;' подряд)
pat_a = re.compile(
    r'(?P<ind>[ \t]*)s->play_time = 0\.0f;\n'
    r'(?P<ind2>[ \t]*)s->state = STATE_PLAYING;'
)
def repl_a(m):
    i, i2 = m.group('ind'), m.group('ind2')
    return (f"{i}s->zone_index      = 0;\n"
            f"{i}s->checkpoint_zone = 0;\n"
            f"{i}s->zone_time       = 0.0f;\n"
            f"{i}s->lives           = AppState::LIVES_START;\n"
            f"{i2}s->state = STATE_PLAYING;")
s, n = pat_a.subn(repl_a, s)
print(f"  Reset (ATTRACT/SPACE): {n}")
changes += n

# Шаг B: R-restart (score = 0; play_time = 0.0f — подряд, без state=PLAYING)
pat_b = re.compile(
    r'(?P<ind>[ \t]*)s->score = 0;\n'
    r'(?P<ind2>[ \t]*)s->play_time = 0\.0f;\n'
)
def repl_b(m):
    i, i2 = m.group('ind'), m.group('ind2')
    return (f"{i}s->score = 0;\n"
            f"{i2}s->zone_index      = 0;\n"
            f"{i2}s->checkpoint_zone = 0;\n"
            f"{i2}s->zone_time       = 0.0f;\n"
            f"{i2}s->lives           = AppState::LIVES_START;\n")
s, n = pat_b.subn(repl_b, s)
print(f"  Reset (R): {n}")
changes += n

# ─────────────────────────────────────────────────────────────
# 9. SCORE screen: добавить "REACHED: X"
# ─────────────────────────────────────────────────────────────
old_score_screen = '''            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
            draw_text_centered(s->renderer, 160, "SCORE", 5.0f);

            char score_buf[8];
            int sc = s->score > 99999 ? 99999 : s->score;
            for (int i = 0; i < 5; ++i) {
                score_buf[4 - i] = '0' + ((sc / (int)std::pow(10, i)) % 10);
            }
            score_buf[5] = 0;
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
            draw_text_centered(s->renderer, 300, score_buf, 10.0f);

            SDL_SetRenderDrawColor(s->renderer, 0xff, 0xff, 0xff, 180);
            draw_text_centered(s->renderer, 500, "PRESS SPACE", 3.0f);'''
new_score_screen = '''            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
            draw_text_centered(s->renderer, 140, "SCORE", 5.0f);

            char score_buf[8];
            int sc = s->score > 99999 ? 99999 : s->score;
            for (int i = 0; i < 5; ++i) {
                score_buf[4 - i] = '0' + ((sc / (int)std::pow(10, i)) % 10);
            }
            score_buf[5] = 0;
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
            draw_text_centered(s->renderer, 260, score_buf, 10.0f);

            // REACHED: X
            {
                char rbuf[16];
                const char* prefix = "REACHED: ";
                int ri = 0;
                for (const char* q = prefix; *q; ++q) rbuf[ri++] = *q;
                rbuf[ri++] = zone_letter(s->zone_index);
                rbuf[ri] = 0;
                SDL_SetRenderDrawColor(s->renderer, 0xff, 0xff, 0xff, 220);
                draw_text_centered(s->renderer, 420, rbuf, 3.0f);
            }

            SDL_SetRenderDrawColor(s->renderer, 0xff, 0xff, 0xff, 180);
            draw_text_centered(s->renderer, 500, "PRESS SPACE", 3.0f);'''
if old_score_screen in s:
    s = s.replace(old_score_screen, new_score_screen, 1); changes += 1
    print("OK: SCORE screen — REACHED: X")

# ─────────────────────────────────────────────────────────────
# ФИНАЛЬНАЯ ПРОВЕРКА: play_time не должен остаться
# ─────────────────────────────────────────────────────────────
residual = len(re.findall(r'play_time', s))
if residual > 0:
    print(f"\nABORT: осталось {residual} упоминаний play_time — файл НЕ записан")
    for m in re.finditer(r'.*play_time.*', s):
        print(f"  {m.group(0).strip()}")
    raise SystemExit(1)

p.write_text(s)
print(f"\nВсего изменений: {changes}")

# ─────────────────────────────────────────────────────────────
# ВЕРИФИКАЦИЯ
# ─────────────────────────────────────────────────────────────
print("\n=== ВЕРИФИКАЦИЯ (после) ===\n")
s = p.read_text()
print(f"  play_time:          {len(re.findall(r'play_time', s))} (должно быть 0)")
print(f"  zone_index:         {s.count('zone_index')}")
print(f"  checkpoint_zone:    {s.count('checkpoint_zone')}")
print(f"  zone_time:          {s.count('zone_time')}")
print(f"  LIVES_START:        {s.count('LIVES_START')}")
print(f"  player_died:        {s.count('player_died')}")
print(f"  ZONES_TOTAL:        {s.count('ZONES_TOTAL')}")
print(f"  ZONE_DISTANCE:      {s.count('ZONE_DISTANCE')}")
print(f"  zone_letter():      {s.count('zone_letter')}")
print(f"  zone_group_num():   {s.count('zone_group_num')}")
print(f"  zone_group_first(): {s.count('zone_group_first')}")
