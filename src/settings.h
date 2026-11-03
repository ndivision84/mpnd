#pragma once
// ─────────────────────────────────────────────────────────────
// settings.h — persistent settings (saves/settings.json).
// ─────────────────────────────────────────────────────────────
#include <string>
#include "app.h"

void settings_load(Settings& out);
void settings_save(const Settings& in);

