#pragma once
// ─────────────────────────────────────────────────────────────
// menu.h — главное меню, OPTIONS, NAME input, TOP SCORES.
// Создано в patch_39 (скелет). Логика будет в patch_40+.
// ─────────────────────────────────────────────────────────────
#include <SDL3/SDL.h>
#include "app.h"

void menu_init(AppState* s);
void menu_update(AppState* s, float dt);
void menu_render(SDL_Renderer* r, AppState* s);
// true = событие обработано (не передавать дальше)
bool menu_handle_event(AppState* s, SDL_Event* e);

