// ─────────────────────────────────────────────────────────────
// menu.cpp — главное меню (NEW GAME / OPTIONS / QUIT).
// patch_40: основное меню + OPTIONS заглушка.
// ─────────────────────────────────────────────────────────────
#include "menu.h"
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
    (void)s;
    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 80, "OPTIONS", 4.0f);

    draw_box(r, 150, 180, 500, 340, 0x00, 0x88, 0x44);

    SDL_SetRenderDrawColor(r, 0x00, 0x88, 0x44, 255);
    draw_text_centered(r, 220, "DIFFICULTY", 2.0f);
    draw_text_centered(r, 260, "NAME", 2.0f);
    draw_text_centered(r, 300, "LIVES", 2.0f);
    draw_text_centered(r, 340, "TOP SCORES", 2.0f);

    SDL_SetRenderDrawColor(r, 0x00, 0x66, 0x33, 255);
    draw_text_centered(r, 400, "PATCH 41 COMING SOON", 1.8f);

    SDL_SetRenderDrawColor(r, 0x00, 0xff, 0x00, 255);
    draw_text_centered(r, 460, "PRESS ESC", 2.5f);
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
    if (e->key.key == SDLK_ESCAPE) {
        s->state = STATE_MENU;
        SDL_Log("OPTIONS -> MENU");
        return true;
    }
    return true;
}

bool menu_handle_event(AppState* s, SDL_Event* e) {
    if (s->state == STATE_MENU)    return handle_main_menu_event(s, e);
    if (s->state == STATE_OPTIONS) return handle_options_event(s, e);
    return false;
}
