#!/usr/bin/env python3
"""
patch_04_enemies.py

Добавляет:
  - struct Enemy (тарелка) — до 2 на экране, движется влево
  - struct Bomb (бомба)   — до 3 на экране, падает вниз
  - Коллизии:
      горизонтальная пуля × тарелка → +100 очков, тарелка исчезает
      вертикальная пуля × бомба    → +50 очков, бомба исчезает
      тарелка/бомба × луноход      → game over
  - Счёт 5-значный в правом верхнем углу
  - Клавиша G — принудительный game over
  - Клавиша R — рестарт
  - В glyphs добавлены буквы G, V, R (для «GAME OVER»)

Применять к main.cpp после патчей 01-03.
"""
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1) struct Enemy и struct Bomb (после struct Bullet)
# ═══════════════════════════════════════════════════════════════
old = """struct Player {"""
new = """struct Enemy {
    float x = 0.0f;
    float y = 0.0f;
    float dx = -120.0f;
    bool active = false;
};

struct Bomb {
    float x = 0.0f;
    float y = 0.0f;
    float dy = 200.0f;
    bool active = false;
};

struct Player {"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: struct Enemy + struct Bomb добавлены")

# ═══════════════════════════════════════════════════════════════
# 2) AppState: enemies, bombs, score, game_over, таймеры
# ═══════════════════════════════════════════════════════════════
old = """    Bullet        bullets[10];   // 0-4: горизонтальные, 5-9: вертикальные
    Player        player;"""
new = """    Bullet        bullets[10];
    Enemy         enemies[5];
    Bomb          bombs[5];
    Player        player;
    int           score = 0;
    bool          game_over = false;
    float         enemy_spawn_timer = 0.0f;
    float         bomb_spawn_timer = 0.0f;
    // Normal: 2 тарелки + 3 бомбы
    static constexpr int MAX_ENEMIES = 2;
    static constexpr int MAX_BOMBS   = 3;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: AppState расширен (enemies, bombs, score, game_over, таймеры)")

# ═══════════════════════════════════════════════════════════════
# 3) glyphs: добавить G, V, R (индексы 20, 21, 22)
# ═══════════════════════════════════════════════════════════════
old = """        {0x3,0x4,0x2,0x1,0x6}, // S
        {0x7,0x5,0x7,0x5,0x7}, // O
    };"""
new = """        {0x3,0x4,0x2,0x1,0x6}, // S
        {0x7,0x5,0x7,0x5,0x7}, // O
        {0x7,0x4,0x5,0x5,0x7}, // G
        {0x5,0x5,0x5,0x2,0x0}, // V
        {0x6,0x5,0x6,0x5,0x5}, // R
    };"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: glyphs + G, V, R (20, 21, 22)")

# ═══════════════════════════════════════════════════════════════
# 4) draw_text: добавить G, V, R
# ═══════════════════════════════════════════════════════════════
old = """        else if (*p == 'O') code = 19;
        else { cx += 8; continue; }"""
new = """        else if (*p == 'O') code = 19;
        else if (*p == 'G') code = 20;
        else if (*p == 'V') code = 21;
        else if (*p == 'R') code = 22;
        else { cx += 8; continue; }"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: draw_text + G, V, R")

# ═══════════════════════════════════════════════════════════════
# 5) draw_score + draw_game_over — новые функции
#    Вставляем после draw_hud (который закомментирован при вызове)
# ═══════════════════════════════════════════════════════════════
# Найдём конец draw_hud: `draw_text(r, 640, 20, "CAUTION");` + }
old = """    if (((int)(world_x * 2) / 1) % 2 == 0) {
        draw_text(r, 640, 20, "CAUTION");
    }
}"""
new = """    if (((int)(world_x * 2) / 1) % 2 == 0) {
        draw_text(r, 640, 20, "CAUTION");
    }
}

// ─────────────────────────────────────────────────────────────
// Счёт (5 цифр) в правом верхнем углу
// ─────────────────────────────────────────────────────────────
static void draw_score(SDL_Renderer* r, int score) {
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
    char buf[6];
    if (score > 99999) score = 99999;
    for (int i = 0; i < 5; ++i) {
        buf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    buf[5] = 0;
    // 5 символов × 3 px × scale 3 = 45 px, + пробелы. Правый верх: x = 800-100
    draw_text(r, 700, 15, buf);
}

// ─────────────────────────────────────────────────────────────
// GAME OVER — крупный текст по центру
// ─────────────────────────────────────────────────────────────
static void draw_game_over(SDL_Renderer* r) {
    // Затемнение фона
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(r, 0, 0, 0, 200);
    SDL_FRect bg = { 0, 0, 800, 600 };
    SDL_RenderFillRect(r, &bg);
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_NONE);

    // Красный «GAME»
    SDL_SetRenderDrawColor(r, 255, 50, 50, 255);
    draw_text(r, 260, 220, "GAME");
    // Белый «OVER»
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
    draw_text(r, 260, 280, "OVER");

    // Подсказка «PRESS R» мелким
    SDL_SetRenderDrawColor(r, 200, 200, 200, 255);
    draw_text(r, 280, 380, "PRESS R");
}"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: draw_score + draw_game_over добавлены")

# ═══════════════════════════════════════════════════════════════
# 6) SDL_AppEvent: R — restart, G — game over
# ═══════════════════════════════════════════════════════════════
# Найдём блок с SDLK_Z (наш предыдущий патч)
old = """    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;
    if (e->key.key != SDLK_Z) return SDL_APP_CONTINUE;

    float sx = s->player.screen_x + s->player.offset_x;
    float sy = s->player.y;"""
new = """    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;

    // R — restart
    if (e->key.key == SDLK_R) {
        s->game_over = false;
        s->score = 0;
        s->player.y = 420.0f;
        s->player.vy = 0.0f;
        s->player.offset_x = 0.0f;
        s->player.on_ground = true;
        for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
        for (int i = 0; i < 5;  ++i) { s->enemies[i].active = false; s->bombs[i].active = false; }
        return SDL_APP_CONTINUE;
    }

    // G — принудительный game over (для отладки)
    if (e->key.key == SDLK_G) {
        s->game_over = true;
        return SDL_APP_CONTINUE;
    }

    // Если game over — стрельба и движение отключены
    if (s->game_over) return SDL_APP_CONTINUE;

    if (e->key.key != SDLK_Z) return SDL_APP_CONTINUE;

    float sx = s->player.screen_x + s->player.offset_x;
    float sy = s->player.y;"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: SDL_AppEvent + R (restart) + G (game over)")

# ═══════════════════════════════════════════════════════════════
# 7) SDL_AppIterate: спавн, движение, коллизии
#    Вставляем сразу после обновления пуль
# ═══════════════════════════════════════════════════════════════
old = """    SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
    SDL_RenderClear(s->renderer);"""
new = """    // ── Спавн тарелок (макс 2, раз в 2.5 сек) ──
    if (!s->game_over) {
        s->enemy_spawn_timer += dt;
        if (s->enemy_spawn_timer > 2.5f) {
            s->enemy_spawn_timer = 0.0f;
            int active_count = 0;
            for (int i = 0; i < 5; ++i) if (s->enemies[i].active) active_count++;
            if (active_count < AppState::MAX_ENEMIES) {
                for (int i = 0; i < 5; ++i) {
                    if (!s->enemies[i].active) {
                        s->enemies[i].x = 830.0f;
                        s->enemies[i].y = 260.0f + (float)(rand() % 120);
                        s->enemies[i].dx = -120.0f;
                        s->enemies[i].active = true;
                        break;
                    }
                }
            }
        }

        // ── Спавн бомб (макс 3, раз в 3.0 сек) ──
        s->bomb_spawn_timer += dt;
        if (s->bomb_spawn_timer > 3.0f) {
            s->bomb_spawn_timer = 0.0f;
            int active_count = 0;
            for (int i = 0; i < 5; ++i) if (s->bombs[i].active) active_count++;
            if (active_count < AppState::MAX_BOMBS) {
                for (int i = 0; i < 5; ++i) {
                    if (!s->bombs[i].active) {
                        s->bombs[i].x = s->player.screen_x + s->player.offset_x
                                        + (float)(rand() % 400 - 200);
                        if (s->bombs[i].x < 40)  s->bombs[i].x = 40;
                        if (s->bombs[i].x > 760) s->bombs[i].x = 760;
                        s->bombs[i].y = 100.0f;
                        s->bombs[i].dy = 200.0f;
                        s->bombs[i].active = true;
                        break;
                    }
                }
            }
        }
    }

    // ── Обновление тарелок ──
    for (int i = 0; i < 5; ++i) {
        if (s->enemies[i].active) {
            s->enemies[i].x += s->enemies[i].dx * dt;
            if (s->enemies[i].x < -40) s->enemies[i].active = false;
        }
    }

    // ── Обновление бомб ──
    for (int i = 0; i < 5; ++i) {
        if (s->bombs[i].active) {
            s->bombs[i].y += s->bombs[i].dy * dt;
            if (s->bombs[i].y > 620) s->bombs[i].active = false;
        }
    }

    // ── Коллизии: горизонтальные пули × тарелки ──
    for (int b = 0; b < 5; ++b) {
        if (!s->bullets[b].active) continue;
        for (int e = 0; e < 5; ++e) {
            if (!s->enemies[e].active) continue;
            if (fabs(s->bullets[b].x - s->enemies[e].x) < 24 &&
                fabs(s->bullets[b].y - s->enemies[e].y) < 16) {
                s->enemies[e].active = false;
                s->bullets[b].active = false;
                s->score += 100;
                if (s->score > 99999) s->score = 99999;
                break;
            }
        }
    }

    // ── Коллизии: вертикальные пули × бомбы ──
    for (int b = 5; b < 10; ++b) {
        if (!s->bullets[b].active) continue;
        for (int bo = 0; bo < 5; ++bo) {
            if (!s->bombs[bo].active) continue;
            if (fabs(s->bullets[b].x - s->bombs[bo].x) < 16 &&
                fabs(s->bullets[b].y - s->bombs[bo].y) < 20) {
                s->bombs[bo].active = false;
                s->bullets[b].active = false;
                s->score += 50;
                if (s->score > 99999) s->score = 99999;
                break;
            }
        }
    }

    // ── Коллизии: тарелки/бомбы × луноход → game over ──
    if (!s->game_over) {
        float px = s->player.screen_x + s->player.offset_x;
        float py = s->player.y;
        for (int e = 0; e < 5; ++e) {
            if (s->enemies[e].active &&
                fabs(px - s->enemies[e].x) < 32 &&
                fabs(py - s->enemies[e].y) < 32) {
                s->game_over = true;
            }
        }
        for (int bo = 0; bo < 5; ++bo) {
            if (s->bombs[bo].active &&
                fabs(px - s->bombs[bo].x) < 28 &&
                fabs(py - s->bombs[bo].y) < 32) {
                s->game_over = true;
            }
        }
    }

    SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
    SDL_RenderClear(s->renderer);"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: спавн + движение + коллизии")

# ═══════════════════════════════════════════════════════════════
# 8) Отрисовка: тарелки, бомбы, счёт, game over
#    Вставляем после отрисовки пуль, перед SDL_RenderPresent
# ═══════════════════════════════════════════════════════════════
old = """    SDL_RenderPresent(s->renderer);"""
new = """    // ── Отрисовка тарелок ──
    for (int e = 0; e < 5; ++e) {
        if (!s->enemies[e].active) continue;
        float ex = s->enemies[e].x;
        float ey = s->enemies[e].y;
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xD7, 0x00, 255);   // жёлтый
        SDL_FRect body = { ex - 16, ey - 4, 32, 8 };
        SDL_RenderFillRect(s->renderer, &body);
        SDL_FRect dome = { ex - 8, ey - 10, 16, 6 };
        SDL_RenderFillRect(s->renderer, &dome);
        SDL_SetRenderDrawColor(s->renderer, 0xCC, 0x66, 0x00, 255);
        SDL_FRect rim = { ex - 18, ey + 2, 36, 3 };
        SDL_RenderFillRect(s->renderer, &rim);
    }

    // ── Отрисовка бомб ──
    for (int bo = 0; bo < 5; ++bo) {
        if (!s->bombs[bo].active) continue;
        float bx = s->bombs[bo].x;
        float by = s->bombs[bo].y;
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x30, 0x30, 255);   // красный
        SDL_FRect c1 = { bx - 4, by - 4, 8, 8 };
        SDL_RenderFillRect(s->renderer, &c1);
        SDL_FRect c2 = { bx - 6, by - 2, 12, 4 };
        SDL_RenderFillRect(s->renderer, &c2);
        SDL_FRect c3 = { bx - 2, by - 6, 4, 12 };
        SDL_RenderFillRect(s->renderer, &c3);
    }

    // ── Счёт в правом верхнем углу ──
    draw_score(s->renderer, s->score);

    // ── GAME OVER поверх всего ──
    if (s->game_over) {
        draw_game_over(s->renderer);
    }

    SDL_RenderPresent(s->renderer);"""
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: отрисовка тарелок, бомб, счёта, GAME OVER")

p.write_text(s)
print(f"\nИзменено: {changes}/8")
