#pragma once
// ─────────────────────────────────────────────────────────────
// app.h — все структуры данных Moon Patrol ND.
// Создан вручную (объединяет patch_38 + patch_39).
// ─────────────────────────────────────────────────────────────
#include <SDL3/SDL.h>
#include <cstdint>
#include <string>
#include <vector>

// ─── Игровые примитивы ──────────────────────────────────────

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
    int   type = 0;
    bool  active = false;
};

struct Star {
    float x = 0.0f;
    float y = 0.0f;
    uint8_t brightness = 200;
    float parallax = 0.15f;
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

// ─── Меню, настройки, TOP-10 ────────────────────────────────

struct ScoreEntry {
    std::string name;
    int         score = 0;
    char        zone = 'A';
    int         attempts = 3;
    std::string date;
};

struct Settings {
    std::string player_name = "PLAYER1";
    int         difficulty = 1;
    int         attempts   = 3;
};

// ─── Состояния ──────────────────────────────────────────────

enum GameState {
    STATE_MENU         = 0,
    STATE_PLAYING      = 1,
    STATE_GAME_OVER    = 2,
    STATE_SCORE        = 3,
    STATE_OPTIONS      = 4,
    STATE_NAME_INPUT   = 5,
    STATE_LEADERBOARD  = 6
};

// ─── Общее состояние приложения ─────────────────────────────

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
    float         obstacle_spawn_interval = 3.0f;
    static constexpr int MAX_OBSTACLES_ACTIVE = 3;
    int           difficulty = 1;
    int           score = 0;
    GameState     state = STATE_MENU;
    float         state_timer = 0.0f;

    static constexpr int   ZONES_TOTAL   = 26;
    static constexpr float ZONE_DISTANCE = 2000.0f;
    static constexpr int   LIVES_START   = 3;
    int   zone_index      = 0;
    int   checkpoint_zone = 0;
    float zone_time       = 0.0f;
    int   lives           = LIVES_START;

    bool          paused = false;
    float         enemy_spawn_timer = 0.0f;
    float         bomb_spawn_timer = 0.0f;
    static constexpr int MAX_NLOS   = 2;
    static constexpr int MAX_BOMBAS = 3;
    float         world_x = 0.0f;
    float         auto_speed = 80.0f;

    // ── Меню ──
    int   menu_cursor    = 0;
    int   options_cursor = 0;
    char  name_input[11] = {0};

    // ── Настройки ──
    Settings settings;

    // ── TOP-10 ──
    std::vector<ScoreEntry> top_scores;
    GameState leaderboard_return_state = STATE_MENU;

    // ── Флаги ──
    bool  new_high_score   = false;
    bool  menu_initialized = false;
};

// ─── Zones helpers (inline, используются в main.cpp) ────────

// Groups: A(0) | B-E(1-4) | F-I(5-8) | J-M(9-12) | N-Q(13-16) | R-U(17-20) | V-Y(21-24) | Z(25)

inline char zone_letter(int idx) {
    if (idx < 0)  idx = 0;
    if (idx > 25) idx = 25;
    return (char)('A' + idx);
}

inline int zone_group_first(int idx) {
    if (idx <= 0)  return 0;
    if (idx >= 25) return 25;
    return ((idx - 1) / 4) * 4 + 1;
}

inline int zone_group_num(int idx) {
    if (idx <= 0)  return 1;
    if (idx >= 25) return 8;
    return ((idx - 1) / 4) + 2;
}
