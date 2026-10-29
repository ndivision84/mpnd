#define SDL_MAIN_USE_CALLBACKS 1
#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>
#include <SDL3_image/SDL_image.h>

#include <string>
#include <cmath>
#include <random>
#include <chrono>

struct Layer {
    SDL_Texture* tex = nullptr;
    int w = 0, h = 0;
    float parallax = 1.0f;
    SDL_Color tint = {255, 255, 255, 255};
};

struct Bullet {
    float x = 0.0f;
    float y = 0.0f;
    float dx = 0.0f;
    float dy = 0.0f;
    float life = 0.0f;
    bool active = false;
};

struct NLO {
    float x = 0.0f;
    float y = 0.0f;
    float dx = -120.0f;
    bool active = false;
};

struct BOMBA {
    float x = 0.0f;
    float y = 0.0f;
    float dy = 200.0f;
    bool active = false;
};

struct Obstacle {
    float world_x = 0.0f;
    float width = 48.0f;
    int   type = 0;       // 0 = яма, 1 = камень, 2 = кратер
    bool  active = false;
};

struct Star {
    float x = 0.0f;
    float y = 0.0f;
    uint8_t brightness = 200;
    float parallax = 0.15f;   // 0.06 slow / 0.15 normal / 0.30 fast
};

struct Player {
    float y = 520.0f;
    float vy = 0.0f;
    float gravity = 800.0f;
    float jump_force = -400.0f;
    bool on_ground = true;
    float screen_x = 120.0f;
    float offset_x = 0.0f;
};

enum GameState {
    STATE_ATTRACT   = 0,
    STATE_PLAYING   = 1,
    STATE_GAME_OVER = 2,
    STATE_SCORE     = 3
};

struct AppState {
    SDL_Window*   window   = nullptr;
    SDL_Renderer* renderer = nullptr;
    Layer         layers[3];
    Player        player;
    Bullet        bullets[10];
    NLO           nlos[5];
    BOMBA         bombas[5];
    Star          stars[120];
    Obstacle      obstacles[8];
    float         obstacle_spawn_timer = 0.0f;
    float         obstacle_spawn_interval = 3.0f;   // Normal; Hard=2.0f, Easy=5.0f
    static constexpr int MAX_OBSTACLES_ACTIVE = 3;
    int           difficulty = 1;   // 0=EASY, 1=NORMAL, 2=HARD   // Normal; Hard=3, Easy=7
    int           score = 0;
    GameState     state = STATE_ATTRACT;
    float         state_timer = 0.0f;
    float         play_time   = 0.0f;   // секунды в PLAYING (для TIME)
    bool          paused = false;
    float         enemy_spawn_timer = 0.0f;
    float         bomb_spawn_timer = 0.0f;
    static constexpr int MAX_NLOS = 2;   // Normal
    static constexpr int MAX_BOMBAS   = 3;   // Normal   // 0-4: горизонтальные, 5-9: вертикальные
    float         world_x = 0.0f;
    float         auto_speed = 80.0f;
};

// 6 базовых цветов: 0=Brown, 1=Purple, 2=Green, 3=Blue, 4=Yellow, 5=Red
static const SDL_Color BASE_COLORS[6] = {
    {0x8e, 0x5a, 0x1e, 255},  // 0 brown
    {0x8e, 0x2a, 0x8e, 255},  // 1 purple
    {0x2d, 0x8e, 0x3d, 255},  // 2 green
    {0x3c, 0x78, 0xc8, 255},  // 3 blue
    {0xf0, 0xc8, 0x3c, 255},  // 4 yellow
    {0xc8, 0x32, 0x32, 255},  // 5 red
};

// 12 допустимых палитр: 3 цвета, без запрещённых пар
// Запрещено: purple+blue (1+3), yellow+brown (4+0)
static const uint8_t VALID_PALETTES[12][3] = {
    {0, 1, 2}, {0, 1, 5}, {0, 2, 3}, {0, 2, 5},
    {0, 3, 5}, {1, 2, 4}, {1, 2, 5}, {1, 4, 5},
    {2, 3, 4}, {2, 3, 5}, {2, 4, 5}, {3, 4, 5},
};

static const char* COLOR_NAMES[6] = {
    "brown", "purple", "green", "blue", "yellow", "red"
};

static SDL_Texture* load_texture(SDL_Renderer* r, const char* path, int& w, int& h) {
    SDL_Surface* s = IMG_Load(path);
    if (!s) return nullptr;
    SDL_Texture* t = SDL_CreateTextureFromSurface(r, s);
    w = s->w; h = s->h;
    SDL_DestroySurface(s);
    if (t) SDL_SetTextureBlendMode(t, SDL_BLENDMODE_BLEND);
    return t;
}

static bool try_load(SDL_Renderer* r, const std::string& base,
                     const char* name, Layer& L) {
    std::string p = base + name;
    L.tex = load_texture(r, p.c_str(), L.w, L.h);
    if (L.tex) {
        SDL_Log("Loaded: %s (%dx%d)", p.c_str(), L.w, L.h);
        return true;
    }
    return false;
}

SDL_AppResult SDL_AppInit(void** appstate, int, char**) {
    if (!SDL_Init(SDL_INIT_VIDEO)) return SDL_APP_FAILURE;
    auto* s = new AppState();
    *appstate = s;
    if (!SDL_CreateWindowAndRenderer("Moon Patrol ND", 800, 600, 0,
                                     &s->window, &s->renderer))
        return SDL_APP_FAILURE;

    if (!SDL_SetRenderVSync(s->renderer, 1)) {
        SDL_Log("VSync failed: %s", SDL_GetError());
    }

    const char* basePath = SDL_GetBasePath();
    std::string bases[] = {
        "assets/tiles/", "../assets/tiles/",
        std::string(basePath ? basePath : "") + "assets/tiles/",
    };
    const char* names[] = {
        "landscape_bg0.png",
        "landscape_bg1.png",
        "landscape_bg2.png",
    };
    const float parallax[] = { 0.15f, 0.45f, 1.0f };
    for (int i = 0; i < 3; ++i) {
        s->layers[i].parallax = parallax[i];
        for (const auto& b : bases) {
            if (try_load(s->renderer, b, names[i], s->layers[i])) break;
        }
    }

    // ★ Случайный выбор одной из 12 валидных палитр
    std::mt19937 rng((unsigned)std::chrono::system_clock::now()
                         .time_since_epoch().count());
    std::uniform_int_distribution<int> palette_dist(0, 11);
    int palette_idx = palette_dist(rng);

    for (int i = 0; i < 3; ++i) {
        int c = VALID_PALETTES[palette_idx][i];
        s->layers[i].tint = BASE_COLORS[c];
    }

    // ── Инициализация звёзд ──
    {
        std::uniform_real_distribution<float> star_x(0.0f, 800.0f);
        std::uniform_real_distribution<float> star_y(0.0f, 600.0f);
        std::uniform_int_distribution<int>   star_b(120, 255);
        std::uniform_int_distribution<int>   star_layer(0, 2);
        static const float STAR_SPEEDS[3] = { 0.06f, 0.15f, 0.30f };  // slow / normal / fast
        int layer_count[3] = { 0, 0, 0 };
        for (int i = 0; i < 120; ++i) {
            s->stars[i].x = star_x(rng);
            s->stars[i].y = star_y(rng);
            s->stars[i].brightness = (uint8_t)star_b(rng);
            int l = star_layer(rng);
            s->stars[i].parallax = STAR_SPEEDS[l];
            layer_count[l]++;
        }
        SDL_Log("Stars initialized: 120 (slow=%d, normal=%d, fast=%d)",
                layer_count[0], layer_count[1], layer_count[2]);
    }

    SDL_Log("Palette #%d:", palette_idx);
    for (int i = 0; i < 3; ++i) {
        int c = VALID_PALETTES[palette_idx][i];
        SDL_Log("  layer %d: %-7s rgb=(%3d,%3d,%3d)",
                i, COLOR_NAMES[c],
                s->layers[i].tint.r,
                s->layers[i].tint.g,
                s->layers[i].tint.b);
    }
    return SDL_APP_CONTINUE;
}

SDL_AppResult SDL_AppEvent(void* appstate, SDL_Event* e) {
    auto* s = static_cast<AppState*>(appstate);
    if (e->type == SDL_EVENT_QUIT) return SDL_APP_SUCCESS;
    if (e->type != SDL_EVENT_KEY_DOWN) return SDL_APP_CONTINUE;

    // ── Выбор сложности: 1/2/3 ──
    // На ATTRACT: старт игры немедленно. В PLAYING: только смена сложности.
    int start_diff = -1;
    float start_interval = 0.0f;
    if (e->key.key == SDLK_1) { start_diff = 0; start_interval = 5.0f; }
    else if (e->key.key == SDLK_2) { start_diff = 1; start_interval = 3.0f; }
    else if (e->key.key == SDLK_3) { start_diff = 2; start_interval = 2.0f; }

    if (start_diff >= 0) {
        s->difficulty = start_diff;
        s->obstacle_spawn_interval = start_interval;
        const char* nm[3] = { "EASY", "NORMAL", "HARD" };
        SDL_Log("Difficulty: %s (%.1fs)", nm[start_diff], start_interval);

        if (s->state == STATE_ATTRACT) {
            s->score = 0;
            s->player.y = 520.0f;
            s->player.vy = 0.0f;
            s->player.offset_x = 0.0f;
            s->player.on_ground = true;
            for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
            for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
            for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
            s->obstacle_spawn_timer = 0.0f;
            s->enemy_spawn_timer    = 0.0f;
            s->bomb_spawn_timer     = 0.0f;
            s->play_time = 0.0f;
            s->state = STATE_PLAYING;
            SDL_Log("START: %s (immediate)", nm[start_diff]);
        }
        return SDL_APP_CONTINUE;
    }

    // ── Space на экранах ATTRACT / GAME_OVER / SCORE ──
    if (e->key.key == SDLK_SPACE) {
        if (s->state == STATE_ATTRACT || s->state == STATE_GAME_OVER || s->state == STATE_SCORE) {
            if (s->state == STATE_GAME_OVER) {
                s->state = STATE_SCORE;
                s->state_timer = 0.0f;
                return SDL_APP_CONTINUE;
            }
            // ATTRACT: force NORMAL. SCORE: продолжить с последней сложности.
            if (s->state == STATE_ATTRACT) {
                s->difficulty = 1;
                s->obstacle_spawn_interval = 3.0f;
                SDL_Log("START: NORMAL (Space)");
            }
            s->score = 0;
            s->player.y = 520.0f;
            s->player.vy = 0.0f;
            s->player.offset_x = 0.0f;
            s->player.on_ground = true;
            for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
            for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
            for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
            s->obstacle_spawn_timer = 0.0f;
            s->enemy_spawn_timer    = 0.0f;
            s->bomb_spawn_timer     = 0.0f;
            s->play_time = 0.0f;
            s->state = STATE_PLAYING;
            return SDL_APP_CONTINUE;
        }
        // PLAYING → стрельба (ниже, существующая логика)
    }

    // R — restart
    if (e->key.key == SDLK_R) {
        s->state = STATE_PLAYING;
        s->score = 0;
        s->play_time = 0.0f;
        s->player.y = 520.0f;
        s->player.vy = 0.0f;
        s->player.offset_x = 0.0f;
        s->player.on_ground = true;
        for (int i = 0; i < 10; ++i) s->bullets[i].active = false;
        for (int i = 0; i < 5; ++i) { s->nlos[i].active = false; s->bombas[i].active = false; }
        for (int i = 0; i < 8; ++i) s->obstacles[i].active = false;
        s->obstacle_spawn_timer = 0.0f;
        s->enemy_spawn_timer    = 0.0f;
        s->bomb_spawn_timer     = 0.0f;
        return SDL_APP_CONTINUE;
    }
    // G — game over (отладка)
    if (e->key.key == SDLK_G) {
        s->state = STATE_GAME_OVER; s->state_timer = 0.0f;
        return SDL_APP_CONTINUE;
    }
    if (e->key.key == SDLK_P) {
        s->paused = !s->paused;
        return SDL_APP_CONTINUE;
    }
    if (s->state == STATE_GAME_OVER) return SDL_APP_CONTINUE;
    if (s->paused)   return SDL_APP_CONTINUE;
    if (e->key.key != SDLK_SPACE) return SDL_APP_CONTINUE;

    float sx = s->player.screen_x + s->player.offset_x;
    float sy = s->player.y;

    for (int i = 0; i < 5; ++i) {
        if (!s->bullets[i].active) {
            s->bullets[i].x    = sx + 24;
            s->bullets[i].y    = sy - 34;  // из ствола пушки (386)
            s->bullets[i].dx   = 600.0f;
            s->bullets[i].dy   = 0.0f;
            s->bullets[i].life = 1.2f;
            s->bullets[i].active = true;
            break;
        }
    }
    for (int i = 5; i < 10; ++i) {
        if (!s->bullets[i].active) {
            s->bullets[i].x    = sx + 16;
            s->bullets[i].y    = sy - 40;
            s->bullets[i].dx   = 0.0f;
            s->bullets[i].dy   = -500.0f;
            s->bullets[i].life = 0.9f;
            s->bullets[i].active = true;
            break;
        }
    }
    return SDL_APP_CONTINUE;
}

static void draw_buggy(SDL_Renderer* r, float cx, float cy) {
    SDL_SetRenderDrawColor(r, 0xCC, 0x66, 0x00, 255);
    SDL_FRect body = { cx - 24, cy - 20, 48, 20 };
    SDL_RenderFillRect(r, &body);

    SDL_SetRenderDrawColor(r, 0xFF, 0xFF, 0xFF, 255);
    SDL_FRect top = { cx - 16, cy - 32, 24, 12 };
    SDL_RenderFillRect(r, &top);
    SDL_FRect gun = { cx + 8, cy - 28, 16, 4 };
    SDL_RenderFillRect(r, &gun);

    SDL_SetRenderDrawColor(r, 0, 0, 0, 255);
    SDL_FRect w1 = { cx - 22, cy - 6, 14, 14 };
    SDL_FRect w2 = { cx + 8,  cy - 6, 14, 14 };
    SDL_RenderFillRect(r, &w1);
    SDL_RenderFillRect(r, &w2);

    SDL_SetRenderDrawColor(r, 0xFF, 0xFF, 0xFF, 255);
    SDL_RenderRect(r, &w1);
    SDL_RenderRect(r, &w2);

    SDL_SetRenderDrawColor(r, 0x88, 0x44, 0x00, 255);
    SDL_FRect w1h = { cx - 18, cy - 2, 6, 6 };
    SDL_FRect w2h = { cx + 12, cy - 2, 6, 6 };
    SDL_RenderFillRect(r, &w1h);
    SDL_RenderFillRect(r, &w2h);
}

// ─────────────────────────────────────────────────────────────
// Мини-шрифт 3×5 для цифр и букв HUD
// ─────────────────────────────────────────────────────────────
static void draw_glyph(SDL_Renderer* r, float x, float y, int code, float scale = 4.0f) {
    // code: 0..9 = цифры, 10='T', 11='I', 12='M', 13='E', 14='C', 15='A', 16='U', 17='N', 18='S', 19='O'
    static const uint8_t glyphs[][7] = {
        {0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E},  // 0
        {0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E},  // 1
        {0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F},  // 2
        {0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E},  // 3
        {0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02},  // 4
        {0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E},  // 5
        {0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E},  // 6
        {0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08},  // 7
        {0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E},  // 8
        {0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C},  // 9
        {0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11},  // A (10)
        {0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E},  // B
        {0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E},  // C
        {0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E},  // D
        {0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F},  // E
        {0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10},  // F
        {0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F},  // G
        {0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11},  // H
        {0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E},  // I
        {0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C},  // J
        {0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11},  // K
        {0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F},  // L
        {0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11},  // M
        {0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11},  // N
        {0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E},  // O
        {0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10},  // P
        {0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D},  // Q
        {0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11},  // R
        {0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E},  // S
        {0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04},  // T
        {0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E},  // U
        {0x11, 0x11, 0x11, 0x11, 0x0A, 0x0A, 0x04},  // V
        {0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11},  // W
        {0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11},  // X
        {0x11, 0x11, 0x11, 0x0A, 0x04, 0x04, 0x04},  // Y
        {0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F},  // Z (35)
        {0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00},  // : (36)
    };
    if (code < 0 || code > 36) return;
    for (int row = 0; row < 7; ++row) {
        uint8_t bits = glyphs[code][row];
        for (int col = 0; col < 5; ++col) {
            if (bits & (0x10 >> col)) {
                SDL_FRect p = { x + col * scale, y + row * scale, scale, scale };
                SDL_RenderFillRect(r, &p);
            }
        }
    }
}

static void draw_text(SDL_Renderer* r, float x, float y, const char* s, float scale = 4.0f) {
    float cx = x;
    for (const char* p = s; *p; ++p) {
        int code;
        if (*p >= '0' && *p <= '9') code = *p - '0';
        else if (*p >= 'A' && *p <= 'Z') code = 10 + (*p - 'A');
        else if (*p == ':') code = 36;
        else if (*p == ' ') { cx += 6.0f * scale; continue; }
        else { cx += 8; continue; }
        draw_glyph(r, cx, y, code, scale);
        cx += 6.0f * scale;
    }
}

static float text_width(const char* s, float scale) {
    int n = 0;
    for (const char* p = s; *p; ++p) n++;
    return n * 6.0f * scale;
}

static void draw_text_centered(SDL_Renderer* r, float y, const char* s, float scale) {
    float x = (800.0f - text_width(s, scale)) / 2.0f;
    draw_text(r, x, y, s, scale);
}

// ─────────────────────────────────────────────────────────────
// Отрисовка звёзд с 3 слоями параллакса (per-star скорость)
// ─────────────────────────────────────────────────────────────
static void draw_stars(SDL_Renderer* r, const Star* stars, int count, float world_x) {
    for (int i = 0; i < count; ++i) {
        float scroll = std::fmod(world_x * stars[i].parallax, 800.0f);
        float sx = stars[i].x - scroll;
        if (sx < 0) sx += 800.0f;
        SDL_SetRenderDrawColor(r,
                               stars[i].brightness,
                               stars[i].brightness,
                               stars[i].brightness,
                               255);
        SDL_FRect rect = { sx, stars[i].y, 2, 2 };
        SDL_RenderFillRect(r, &rect);
    }
}

static void draw_hud(SDL_Renderer* r, int score, int time_left, float world_x, int difficulty) {
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
}

#if 0
static void draw_score(SDL_Renderer* r, int score) {
    SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
    char buf[6];
    if (score > 99999) score = 99999;
    for (int i = 0; i < 5; ++i) {
        buf[4 - i] = '0' + ((score / (int)pow(10, i)) % 10);
    }
    buf[5] = 0;
    draw_text(r, 660, 15, buf, 4.0f);
}

static void draw_game_over(SDL_Renderer* r) {
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(r, 0, 0, 0, 200);
    SDL_FRect bg = { 0, 0, 800, 600 };
    SDL_RenderFillRect(r, &bg);
    SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_NONE);

    SDL_SetRenderDrawColor(r, 255, 50, 50, 255);
    draw_text_centered(r, 250, "GAME OVER", 4.0f);

    SDL_SetRenderDrawColor(r, 200, 200, 200, 255);
    draw_text_centered(r, 340, "PRESS R", 4.0f);
}

#endif

SDL_AppResult SDL_AppIterate(void* appstate) {
    auto* s = static_cast<AppState*>(appstate);
    static Uint64 last_tick = 0;
    Uint64 now_tick = SDL_GetTicks();
    if (last_tick == 0) last_tick = now_tick;
    float dt = (now_tick - last_tick) / 1000.0f;
    last_tick = now_tick;
    if (dt > 0.1f)   dt = 0.1f;   // защита от зависаний
    if (dt < 0.001f) dt = 0.001f; // защита от div-by-zero
    if (s->paused)   dt = 0.0f;

    s->play_time += dt;
    s->world_x += s->auto_speed * dt;

    // ★ Проверка окончания времени — ДО рендера (без кадра «TIME:00»)
    if (s->state == STATE_PLAYING && s->play_time >= 60.0f) {
        SDL_Log("TIME UP! play_time=%.1f -> GAME_OVER", s->play_time);
        s->state = STATE_GAME_OVER;
        s->state_timer = 0.0f;
    }

    const bool* keys = SDL_GetKeyboardState(nullptr);
    if (keys[SDL_SCANCODE_LEFT])  s->player.offset_x -= 200.0f * dt;
    if (keys[SDL_SCANCODE_RIGHT]) s->player.offset_x += 200.0f * dt;
    if (s->player.offset_x < -40) s->player.offset_x = -40;
    if (s->player.offset_x >  600) s->player.offset_x =  600;

    if (keys[SDL_SCANCODE_UP] && s->player.on_ground) {
        s->player.vy = s->player.jump_force;
        s->player.on_ground = false;
    }
    s->player.vy += s->player.gravity * dt;
    s->player.y  += s->player.vy * dt;
    if (s->player.y >= 520.0f) {
        s->player.y = 520.0f;
        s->player.vy = 0.0f;
        s->player.on_ground = true;
    }

    // Обновление пуль
    for (int i = 0; i < 10; ++i) {
        if (s->bullets[i].active) {
            s->bullets[i].x += s->bullets[i].dx * dt;
            s->bullets[i].y += s->bullets[i].dy * dt;
            s->bullets[i].life -= dt;
            if (s->bullets[i].life <= 0.0f
                || s->bullets[i].x > 750.0f
                || s->bullets[i].y < 40.0f) {
                s->bullets[i].active = false;
            }
        }
    }

    // ── Спавн препятствий (каждые obstacle_spawn_interval сек) ──
    if (!(s->state == STATE_GAME_OVER) && !s->paused) {
        s->obstacle_spawn_timer += dt;
        if (s->obstacle_spawn_timer >= s->obstacle_spawn_interval) {
            s->obstacle_spawn_timer = 0.0f;
            int active_count = 0;
            for (int k = 0; k < 8; ++k) if (s->obstacles[k].active) active_count++;
            for (int i = 0; i < 8; ++i) {
                if (!s->obstacles[i].active) {
                    if (active_count >= AppState::MAX_OBSTACLES_ACTIVE) break;
                    int r = rand() % 100;
                    int type = -1;
                    float w = 0.0f;
                    if      (r < 35) { type = -1; }                  // 35% ничего
                    else if (r < 60) { type = 0; w = 48.0f; }        // 25% яма
                    else if (r < 80) { type = 1; w = 24.0f; }        // 20% камень
                    else             { type = 2; w = 64.0f; }        // 20% кратер

                    if (type >= 0) {
                        s->obstacles[i].world_x = s->world_x + 850.0f;
                        s->obstacles[i].width = w;
                        s->obstacles[i].type = type;
                        s->obstacles[i].active = true;
                        SDL_Log("Obstacle: type=%d width=%d", type, (int)w);
                    }
                    break;
                }
            }
        }
    }

    // ── Спавн тарелок (макс 2) ──
    if (s->state == STATE_PLAYING) {
        s->enemy_spawn_timer += dt;
        if (s->enemy_spawn_timer > 2.5f) {
            s->enemy_spawn_timer = 0.0f;
            int cnt = 0;
            for (int i = 0; i < 5; ++i) if (s->nlos[i].active) cnt++;
            if (cnt < AppState::MAX_NLOS) {
                for (int i = 0; i < 5; ++i) {
                    if (!s->nlos[i].active) {
                        s->nlos[i].x = 830.0f;
                        {
                            static const float NLO_HEIGHTS[3] = { 150.0f, 250.0f, 350.0f };
                            s->nlos[i].y = NLO_HEIGHTS[rand() % 3];
                        }
                        s->nlos[i].dx = -120.0f;
                        s->nlos[i].active = true;
                        break;
                    }
                }
            }
        }
        // ── Спавн бомб (макс 3) ──
        s->bomb_spawn_timer += dt;
        if (s->bomb_spawn_timer > 3.0f) {
            s->bomb_spawn_timer = 0.0f;
            int cnt = 0;
            for (int i = 0; i < 5; ++i) if (s->bombas[i].active) cnt++;
            if (cnt < AppState::MAX_BOMBAS) {
                for (int i = 0; i < 5; ++i) {
                    if (!s->bombas[i].active) {
                        s->bombas[i].x = s->player.screen_x + s->player.offset_x
                                        + (float)(rand() % 400 - 200);
                        if (s->bombas[i].x < 40)  s->bombas[i].x = 40;
                        if (s->bombas[i].x > 760) s->bombas[i].x = 760;
                        s->bombas[i].y = -10.0f;
                        s->bombas[i].dy = 200.0f;
                        s->bombas[i].active = true;
                        break;
                    }
                }
            }
        }
    }

    // ── Обновление/удаление препятствий + коллизии ──
    for (int i = 0; i < 8; ++i) {
        if (!s->obstacles[i].active) continue;
        float sx = s->obstacles[i].world_x - s->world_x;
        if (sx < -100) { s->obstacles[i].active = false; continue; }

        if (s->state == STATE_PLAYING) {
            float px = s->player.screen_x + s->player.offset_x;
            float left  = sx;
            float right = sx + s->obstacles[i].width;
            bool h_overlap = (px + 24 > left) && (px - 24 < right);

            if (h_overlap) {
                if (s->obstacles[i].type == 0 && s->player.on_ground) {
                    s->state = STATE_GAME_OVER; s->state_timer = 0.0f;
                    SDL_Log("Fell into PIT!");
                } else if (s->obstacles[i].type == 1 && s->player.y > 480.0f) {
                    s->state = STATE_GAME_OVER; s->state_timer = 0.0f;
                    SDL_Log("Hit ROCK!");
                } else if (s->obstacles[i].type == 2 && s->player.on_ground) {
                    s->state = STATE_GAME_OVER; s->state_timer = 0.0f;
                    SDL_Log("Fell into CRATER!");
                }
            }
        }
    }

    // ── Обновление тарелок ──
    for (int i = 0; i < 5; ++i) {
        if (s->nlos[i].active) {
            s->nlos[i].x += s->nlos[i].dx * dt;
            if (s->nlos[i].x < -40) s->nlos[i].active = false;
        }
    }
    // ── Обновление бомб ──
    for (int i = 0; i < 5; ++i) {
        if (s->bombas[i].active) {
            s->bombas[i].y += s->bombas[i].dy * dt;
            if (s->bombas[i].y > 620) s->bombas[i].active = false;
        }
    }
    // ── Коллизии: гориз. пули × тарелки ──
    for (int b = 0; b < 5; ++b) {
        if (!s->bullets[b].active) continue;
        for (int e = 0; e < 5; ++e) {
            if (!s->nlos[e].active) continue;
            if (fabs(s->bullets[b].x - s->nlos[e].x) < 45 &&
                fabs(s->bullets[b].y - s->nlos[e].y) < 45) {
                s->nlos[e].active = false;
                s->bullets[b].active = false;
                s->score += 100;
                if (s->score > 99999) s->score = 99999;
                SDL_Log("HIT NLO! score=%d", s->score);
                break;
            }
        }
    }
    // ── Коллизии: гориз. пули × камни (обстрел камня) ──
    for (int b = 0; b < 5; ++b) {
        if (!s->bullets[b].active) continue;
        for (int i = 0; i < 8; ++i) {
            if (!s->obstacles[i].active) continue;
            if (s->obstacles[i].type != 1) continue;  // только камень
            float sx = s->obstacles[i].world_x - s->world_x;
            float rock_cx = sx + s->obstacles[i].width / 2.0f;
            if (fabs(s->bullets[b].x - rock_cx) < s->obstacles[i].width / 2.0f + 10 &&
                fabs(s->bullets[b].y - 502.0f) < 30) {
                s->obstacles[i].active = false;
                s->bullets[b].active = false;
                s->score += 50;
                if (s->score > 99999) s->score = 99999;
                SDL_Log("SHOT ROCK! score=%d", s->score);
                break;
            }
        }
    }

    // ── Коллизии: верт. пули × NLO ──
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

    // ── Коллизии: верт. пули × BOMBA ──
    for (int b = 5; b < 10; ++b) {
        if (!s->bullets[b].active) continue;
        for (int bo = 0; bo < 5; ++bo) {
            if (!s->bombas[bo].active) continue;
            if (fabs(s->bullets[b].x - s->bombas[bo].x) < 16 &&
                fabs(s->bullets[b].y - s->bombas[bo].y) < 20) {
                s->bombas[bo].active = false;
                s->bullets[b].active = false;
                s->score += 50;
                if (s->score > 99999) s->score = 99999;
                break;
            }
        }
    }
    // ── Коллизии: враги/бомбы × луноход → game over ──
    if (s->state == STATE_PLAYING) {
        float px = s->player.screen_x + s->player.offset_x;
        float py = s->player.y;
        for (int e = 0; e < 5; ++e) {
            if (s->nlos[e].active &&
                fabs(px - s->nlos[e].x) < 32 &&
                fabs(py - s->nlos[e].y) < 32) {
                s->state = STATE_GAME_OVER; s->state_timer = 0.0f;
            }
        }
        for (int bo = 0; bo < 5; ++bo) {
            if (s->bombas[bo].active &&
                fabs(px - s->bombas[bo].x) < 28 &&
                fabs(py - s->bombas[bo].y) < 32) {
                s->state = STATE_GAME_OVER; s->state_timer = 0.0f;
            }
        }
    }

    SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
    SDL_RenderClear(s->renderer);

    // ── Переход GAME_OVER → SCORE по таймеру (3 сек) ──
    if (s->state == STATE_GAME_OVER) {
        s->state_timer += dt;
        if (s->state_timer >= 3.0f) {
            s->state = STATE_SCORE;
            s->state_timer = 0.0f;
        }
    }

    // ── Экраны ATTRACT / GAME_OVER / SCORE ──
    if (s->state != STATE_PLAYING) {
        // Звёзды (3 слоя параллакса)
        draw_stars(s->renderer, s->stars, 120, s->world_x);

        if (s->state == STATE_ATTRACT) {
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
            draw_text_centered(s->renderer, 220, "MOON PATROL ND", 8.0f);
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 180);
            draw_text_centered(s->renderer, 420, "PRESS SPACE", 3.0f);

            // Меню выбора сложности — вертикально
            {
                const SDL_Color gc = { 0x00, 0xff, 0x00, 255 };
                const SDL_Color wc = { 0xff, 0xff, 0xff, 180 };
                const float menu_x = 320.0f;
                const float menu_y = 470.0f;
                const float step_y = 34.0f;

                SDL_Color c1 = (s->difficulty == 0) ? gc : wc;
                SDL_SetRenderDrawColor(s->renderer, c1.r, c1.g, c1.b, 255);
                draw_text(s->renderer, menu_x, menu_y, "1. EASY", 3.0f);

                SDL_Color c2 = (s->difficulty == 1) ? gc : wc;
                SDL_SetRenderDrawColor(s->renderer, c2.r, c2.g, c2.b, 255);
                draw_text(s->renderer, menu_x, menu_y + step_y, "2. NORMAL", 3.0f);

                SDL_Color c3 = (s->difficulty == 2) ? gc : wc;
                SDL_SetRenderDrawColor(s->renderer, c3.r, c3.g, c3.b, 255);
                draw_text(s->renderer, menu_x, menu_y + 2.0f * step_y, "3. HARD", 3.0f);
            }
        } else if (s->state == STATE_GAME_OVER) {
            SDL_SetRenderDrawColor(s->renderer, 0xff, 0x30, 0x30, 255);
            draw_text_centered(s->renderer, 260, "GAME OVER", 7.0f);
            SDL_SetRenderDrawColor(s->renderer, 0xff, 0xff, 0xff, 180);
            draw_text_centered(s->renderer, 420, "PRESS SPACE", 3.0f);
        } else if (s->state == STATE_SCORE) {
            SDL_SetRenderDrawColor(s->renderer, 0x00, 0xff, 0x00, 255);
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
            draw_text_centered(s->renderer, 500, "PRESS SPACE", 3.0f);
        }

        SDL_RenderPresent(s->renderer);
        return SDL_APP_CONTINUE;
    }

    const float SCALE = 3.0f;
    const float lane_h = 64.0f * SCALE;
    const float lane_y = 328.0f;

    // ── Отрисовка звёзд (3 слоя параллакса) ──
    draw_stars(s->renderer, s->stars, 120, s->world_x);

    for (int i = 0; i < 3; ++i) {
        if (!s->layers[i].tex) continue;
        SDL_SetTextureColorMod(s->layers[i].tex,
                               s->layers[i].tint.r,
                               s->layers[i].tint.g,
                               s->layers[i].tint.b);
        const float tile_w = s->layers[i].w * SCALE;
        const float scroll = std::fmod(s->world_x * s->layers[i].parallax, tile_w);
        for (int k = 0; k < 3; ++k) {
            SDL_FRect dst = { k * tile_w - scroll, lane_y, tile_w, lane_h };
            SDL_RenderTexture(s->renderer, s->layers[i].tex, nullptr, &dst);
        }
    }

    SDL_Color gc = s->layers[2].tint;
    SDL_SetRenderDrawColor(s->renderer, gc.r/4, gc.g/4, gc.b/4, 255);
    SDL_FRect ground = { 0, lane_y + lane_h, 800, 600 - (lane_y + lane_h) };
    SDL_RenderFillRect(s->renderer, &ground);
    SDL_SetRenderDrawColor(s->renderer, gc.r, gc.g, gc.b, 255);
    SDL_FRect ground_line = { 0, lane_y + lane_h, 800, 2 };
    SDL_RenderFillRect(s->renderer, &ground_line);

    // ── Отрисовка препятствий ДО лунохода (луноход поверх) ──
    const float gy = 520.0f;  // = player.y
    for (int i = 0; i < 8; ++i) {
        if (!s->obstacles[i].active) continue;
        float sx = s->obstacles[i].world_x - s->world_x;
        if (sx < -100 || sx > 900) continue;
        float w = s->obstacles[i].width;

        if (s->obstacles[i].type == 0) {
            // ЯМА — чёрный прямоугольник на земле
            SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
            SDL_FRect pit = { sx, gy, w, 40.0f };
            SDL_RenderFillRect(s->renderer, &pit);
            SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0xFF, 255);
            SDL_FRect top = { sx, gy, w, 2.0f };
            SDL_RenderFillRect(s->renderer, &top);
        } else if (s->obstacles[i].type == 1) {
            // КАМЕНЬ — серый + чёрный верх
            SDL_SetRenderDrawColor(s->renderer, 0x80, 0x80, 0x80, 255);
            SDL_FRect rock = { sx, gy - 35, w, 35.0f };
            SDL_RenderFillRect(s->renderer, &rock);
            SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
            SDL_FRect rock_top = { sx, gy - 35, w, 2.0f };
            SDL_RenderFillRect(s->renderer, &rock_top);
        } else {
            // КРАТЕР — V-образная воронка с оранжевыми обломками
            // 1) Оранжевые обломки по бокам (типа выброс породы)
            SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x60, 0x00, 255);
            SDL_FRect left_rim  = { sx - 4, gy - 12, 6, 12 };
            SDL_FRect right_rim = { sx + w - 2, gy - 12, 6, 12 };
            SDL_RenderFillRect(s->renderer, &left_rim);
            SDL_RenderFillRect(s->renderer, &right_rim);

            // 2) Оранжевый гребень сверху
            SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x80, 0x00, 255);
            SDL_FRect rim_top = { sx - 2, gy - 4, w + 4, 3.0f };
            SDL_RenderFillRect(s->renderer, &rim_top);

            // 3) Чёрная воронка в форме трапеции (широкая сверху, узкая снизу)
            SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
            for (int row = 0; row < 14; ++row) {
                float row_y = gy - 2 + row * 3.4f;
                float shrink = row * 2.0f;
                SDL_FRect rr = { sx + 2 + shrink, row_y, w - 4 - shrink * 2, 3.4f };
                SDL_RenderFillRect(s->renderer, &rr);
            }
        }
    }

    draw_buggy(s->renderer,
               s->player.screen_x + s->player.offset_x,
               s->player.y - 8);

    // Пули — жёлтые
    SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0x00, 255);
    for (int i = 0; i < 10; ++i) {
        if (s->bullets[i].active) {
            float w = (i < 5) ? 8.0f : 3.0f;
            float h = (i < 5) ? 3.0f : 8.0f;
            SDL_FRect b = { s->bullets[i].x, s->bullets[i].y, w, h };
            SDL_RenderFillRect(s->renderer, &b);
        }
    }

    // HUD поверх
    // int score = (int)(s->world_x * 10);   // не используется
    int time_left = 60 - (int)s->play_time;
    if (time_left < 0) time_left = 0;
    draw_hud(s->renderer, s->score, time_left, s->world_x, s->difficulty);

    // ── Отрисовка тарелок (56×36, белый + чёрная обводка) ──
    for (int e = 0; e < 5; ++e) {
        if (!s->nlos[e].active) continue;
        float ex = s->nlos[e].x, ey = s->nlos[e].y;

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
    }
    // ── Отрисовка бомб (красная + белая обводка) ──
    for (int bo = 0; bo < 5; ++bo) {
        if (!s->bombas[bo].active) continue;
        float bx = s->bombas[bo].x, by = s->bombas[bo].y;

        // Белая обводка — 3 прямоугольника побольше
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0xFF, 0xFF, 255);
        SDL_FRect o1 = { bx - 6, by - 6, 12, 12 };  SDL_RenderFillRect(s->renderer, &o1);
        SDL_FRect o2 = { bx - 8, by - 3, 16, 6  };  SDL_RenderFillRect(s->renderer, &o2);
        SDL_FRect o3 = { bx - 3, by - 8, 6, 16  };  SDL_RenderFillRect(s->renderer, &o3);

        // Красная бомба — 3 прямоугольника поменьше
        SDL_SetRenderDrawColor(s->renderer, 0xFF, 0x30, 0x30, 255);
        SDL_FRect c1 = { bx - 4, by - 4, 8, 8  };   SDL_RenderFillRect(s->renderer, &c1);
        SDL_FRect c2 = { bx - 6, by - 2, 12, 4 };   SDL_RenderFillRect(s->renderer, &c2);
        SDL_FRect c3 = { bx - 2, by - 6, 4, 12 };   SDL_RenderFillRect(s->renderer, &c3);

        // Чёрный центр — «глаз» бомбы
        SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 255);
        SDL_FRect center = { bx - 1, by - 1, 2, 2 };
        SDL_RenderFillRect(s->renderer, &center);
    }
    // ── Счёт ──
    // draw_score вызывается внутри draw_hud
    // ── GAME OVER ──
    if (s->state == STATE_GAME_OVER) {
        // GAME OVER рендер вынесен выше
    }
    if (s->paused && !(s->state == STATE_GAME_OVER)) {
        SDL_SetRenderDrawBlendMode(s->renderer, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(s->renderer, 0, 0, 0, 150);
        SDL_FRect pbg = { 0, 0, 800, 600 };
        SDL_RenderFillRect(s->renderer, &pbg);
        SDL_SetRenderDrawBlendMode(s->renderer, SDL_BLENDMODE_NONE);
        SDL_SetRenderDrawColor(s->renderer, 255, 255, 255, 255);
        draw_text(s->renderer, 344, 280, "PAUSE", 4.0f);
    }

    SDL_RenderPresent(s->renderer);
    return SDL_APP_CONTINUE;
}

void SDL_AppQuit(void* appstate, SDL_AppResult) {
    auto* s = static_cast<AppState*>(appstate);
    for (int i = 0; i < 3; ++i) if (s->layers[i].tex) SDL_DestroyTexture(s->layers[i].tex);
    delete s;
    SDL_Quit();
}
