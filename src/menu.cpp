// ─────────────────────────────────────────────────────────────
// menu.cpp — главное меню (NEW GAME / OPTIONS / QUIT).
// patch_40: основное меню + OPTIONS заглушка.
// ─────────────────────────────────────────────────────────────
#include "menu.h"
#include <string>
#include <SDL3/SDL.h>

// ─── Вспомогательные ────────────────────────────────────────

static void draw_box(SDL_Renderer* r, float x, float y, float w, float h,
                     Uint8 cr, Uint8 cg, Uint8 cb) {
    SDL_SetRenderDrawColor(r, cr, cg, cb, 255);
    SDL_FRect rect = { x, y, w, h };
    SDL_RenderRect(r, &rect);
}

static void draw_menu_item(SDL_Renderer* r, float cx, float y,
                           const char* text, float scale, bool selected) {
    float w = text_width(text, scale);
    float x = cx - w / 2.0f;
    if (selected) SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    else          SDL_SetRenderDrawColor(r, 0x00, 0x88, 0x44, 255);
    draw_text(r, x, y, text, scale);
    if (selected) {
        draw_text(r, x - 6.0f * scale - 8.0f, y, ">", scale);
    }
}

// ─── Render ─────────────────────────────────────────────────

static void render_main_menu(SDL_Renderer* r, AppState* s) {
    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 80, "MOON PATROL ND", 4.0f);

    draw_box(r, 200, 180, 400, 280, 0x00, 0x88, 0x44);

    const char* items[3] = { "NEW GAME", "OPTIONS", "QUIT" };
    constexpr float item_scale = 3.0f;
    constexpr float item_y0    = 220.0f;
    constexpr float item_step  = 80.0f;
    for (int i = 0; i < 3; ++i) {
        draw_menu_item(r, 400.0f, item_y0 + i * item_step,
                       items[i], item_scale, i == s->menu_cursor);
    }
}

static void render_options(SDL_Renderer* r, AppState* s) {
    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 80, "OPTIONS", 4.0f);

    draw_box(r, 100, 170, 600, 360, 0x00, 0x88, 0x44);

    constexpr float scale    = 2.5f;
    constexpr float x_cursor = 130.0f;
    constexpr float x_label  = 160.0f;
    constexpr float x_value  = 420.0f;

    static const char* diff_names[3] = { "EASY", "NORMAL", "HARD" };
    const char* diff_name = diff_names[s->settings.difficulty];
    std::string lives_str = std::to_string(s->settings.attempts);

    const char* labels[5] = {
        "DIFFICULTY:", "NAME:", "LIVES:", "TOP SCORES", "BACK"
    };
    const char* values[5] = {
        diff_name,
        s->settings.player_name.c_str(),
        lives_str.c_str(),
        "", ""
    };

    for (int i = 0; i < 5; ++i) {
        float y = 220.0f + i * 50.0f;
        bool selected = (i == s->options_cursor);

        // Курсор
        if (selected) {
            SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
            draw_text(r, x_cursor, y, ">", scale);
        }

        // Цвет строки
        if (selected) SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
        else          SDL_SetRenderDrawColor(r, 0x00, 0x88, 0x44, 255);

        // Метка
        draw_text(r, x_label, y, labels[i], scale);

        // Значение
        if (values[i][0] != 0) {
            bool has_arrows = (i == 0 || i == 2);  // DIFFICULTY или LIVES
            if (has_arrows) {
                float vw = text_width(values[i], scale);
                draw_text(r, x_value, y, "<", scale);
                draw_text(r, x_value + 20.0f, y, values[i], scale);
                draw_text(r, x_value + 20.0f + vw + 10.0f, y, ">", scale);
            } else {
                draw_text(r, x_value, y, values[i], scale);
            }
        }
    }

    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 520, "PRESS ESC", 2.5f);
}

void menu_render(SDL_Renderer* r, AppState* s) {
    if (s->state == STATE_MENU) {
        render_main_menu(r, s);
    } else if (s->state == STATE_OPTIONS) {
        render_options(r, s);
    }
}

// ─── Update / Init ──────────────────────────────────────────

void menu_update(AppState* s, float dt) {
    (void)s; (void)dt;
}

void menu_init(AppState* s) {
    s->menu_cursor      = 0;
    s->options_cursor   = 0;
    s->name_input[0]    = '\0';
    s->menu_initialized = true;
    SDL_Log("MENU: initialized");
}

// ─── Events ─────────────────────────────────────────────────

static bool handle_main_menu_event(AppState* s, SDL_Event* e) {
    if (e->key.key == SDLK_UP) {
        s->menu_cursor = (s->menu_cursor + 2) % 3;
        SDL_Log("MENU: cursor=%d", s->menu_cursor);
        return true;
    }
    if (e->key.key == SDLK_DOWN) {
        s->menu_cursor = (s->menu_cursor + 1) % 3;
        SDL_Log("MENU: cursor=%d", s->menu_cursor);
        return true;
    }
    if (e->key.key == SDLK_SPACE) {
        switch (s->menu_cursor) {
            case 0: {
                s->score           = 0;
                s->zone_index      = 0;
                s->checkpoint_zone = 0;
                s->zone_time       = 0.0f;
                s->lives           = s->settings.attempts;
                s->difficulty      = s->settings.difficulty;
                s->obstacle_spawn_interval =
                    (s->settings.difficulty == 0) ? 5.0f :
                    (s->settings.difficulty == 2) ? 2.0f : 3.0f;
                s->player.y         = 520.0f;
                s->player.vy        = 0.0f;
                s->player.offset_x  = 0.0f;
                s->player.on_ground = true;
                s->world_x          = 0.0f;
                for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
                for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
                for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
                s->obstacle_spawn_timer = 0.0f;
                s->enemy_spawn_timer    = 0.0f;
                s->bomb_spawn_timer     = 0.0f;
                s->paused               = false;
                s->state                = STATE_PLAYING;
                SDL_Log("NEW GAME (lives=%d, diff=%d)", s->lives, s->difficulty);
                return true;
            }
            case 1:
                s->options_cursor = 0;
                s->state = STATE_OPTIONS;
                SDL_Log("MENU -> OPTIONS");
                return true;
            case 2:
                SDL_Log("QUIT");
                s->should_quit = true;
                return true;
        }
    }
    return true;
}

static bool handle_options_event(AppState* s, SDL_Event* e) {
    constexpr int ITEMS = 5;
    constexpr int VALS_LIVES[3] = { 1, 3, 7 };

    if (e->key.key == SDLK_UP) {
        s->options_cursor = (s->options_cursor + ITEMS - 1) % ITEMS;
        return true;
    }
    if (e->key.key == SDLK_DOWN) {
        s->options_cursor = (s->options_cursor + 1) % ITEMS;
        return true;
    }
    if (e->key.key == SDLK_LEFT || e->key.key == SDLK_RIGHT) {
        int dir = (e->key.key == SDLK_RIGHT) ? 1 : -1;
        if (s->options_cursor == 0) {  // DIFFICULTY
            s->settings.difficulty = (s->settings.difficulty + dir + 3) % 3;
            SDL_Log("DIFFICULTY: %d (EASY/NORMAL/HARD)", s->settings.difficulty);
        } else if (s->options_cursor == 2) {  // LIVES
            int idx = 1;
            for (int i = 0; i < 3; ++i) {
                if (VALS_LIVES[i] == s->settings.attempts) { idx = i; break; }
            }
            idx = (idx + dir + 3) % 3;
            s->settings.attempts = VALS_LIVES[idx];
            SDL_Log("LIVES: %d", s->settings.attempts);
        }
        return true;
    }
    if (e->key.key == SDLK_SPACE) {
        if (s->options_cursor == 1) {
            SDL_Log("OPTIONS -> NAME (patch_45 TODO)");
        } else if (s->options_cursor == 3) {
            SDL_Log("OPTIONS -> TOP SCORES (patch_46 TODO)");
        } else if (s->options_cursor == 4) {
            s->state = STATE_MENU;
            SDL_Log("OPTIONS -> MENU (BACK)");
        }
        return true;
    }
    if (e->key.key == SDLK_ESCAPE) {
        s->state = STATE_MENU;
        SDL_Log("OPTIONS -> MENU (ESC)");
        return true;
    }
    return true;
}

bool menu_handle_event(AppState* s, SDL_Event* e) {
    if (s->state == STATE_MENU)    return handle_main_menu_event(s, e);
    if (s->state == STATE_OPTIONS) return handle_options_event(s, e);
    return false;
}
