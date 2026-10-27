#!/usr/bin/env python3
"""patch_15a_intervals.py

1. obstacle_spawn_interval: 5.0f (Normal) → 3.0f
   Easy = 5.0f, Hard = 2.0f (заменить по желанию).
2. Максимум 3 активных obstacle (не считая NLO).
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()
changes = 0

# 1) Интервал 5.0f → 3.0f (Normal)
old = "float         obstacle_spawn_interval = 5.0f;"
new = "float         obstacle_spawn_interval = 3.0f;   // Normal; Hard=2.0f, Easy=5.0f"
if old in s:
    s = s.replace(old, new, 1); changes += 1
    print("OK: интервал 5.0f → 3.0f (Normal)")
else:
    print("!! не найдено 'obstacle_spawn_interval = 5.0f'")

# 2) MAX_OBSTACLES_ACTIVE = 3
if 'MAX_OBSTACLES_ACTIVE' not in s:
    old = "float         obstacle_spawn_interval = 3.0f;   // Normal; Hard=2.0f, Easy=5.0f"
    new = old + "\n    static constexpr int MAX_OBSTACLES_ACTIVE = 3;"
    if old in s:
        s = s.replace(old, new, 1); changes += 1
        print("OK: MAX_OBSTACLES_ACTIVE = 3")

# 3) Ограничение в спавне
old_spawn = """        s->obstacle_spawn_timer += dt;
        if (s->obstacle_spawn_timer >= s->obstacle_spawn_interval) {
            s->obstacle_spawn_timer = 0.0f;
            for (int i = 0; i < 8; ++i) {
                if (!s->obstacles[i].active) {
                    int r = rand() % 100;
                    int type = -1;
                    float w = 0.0f;
                    if      (r < 35) { type = -1; }
                    else if (r < 60) { type = 0; w = 48.0f; }
                    else if (r < 80) { type = 1; w = 24.0f; }
                    else             { type = 2; w = 64.0f; }

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
    }"""

new_spawn = """        s->obstacle_spawn_timer += dt;
        if (s->obstacle_spawn_timer >= s->obstacle_spawn_interval) {
            s->obstacle_spawn_timer = 0.0f;

            int active_count = 0;
            for (int i = 0; i < 8; ++i) if (s->obstacles[i].active) active_count++;

            if (active_count < AppState::MAX_OBSTACLES_ACTIVE) {
                for (int i = 0; i < 8; ++i) {
                    if (!s->obstacles[i].active) {
                        int r = rand() % 100;
                        int type = -1;
                        float w = 0.0f;
                        if      (r < 35) { type = -1; }
                        else if (r < 60) { type = 0; w = 48.0f; }
                        else if (r < 80) { type = 1; w = 24.0f; }
                        else             { type = 2; w = 64.0f; }

                        if (type >= 0) {
                            s->obstacles[i].world_x = s->world_x + 850.0f;
                            s->obstacles[i].width = w;
                            s->obstacles[i].type = type;
                            s->obstacles[i].active = true;
                            SDL_Log("Obstacle: type=%d width=%d active=%d",
                                    type, (int)w, active_count + 1);
                        }
                        break;
                    }
                }
            }
        }
    }"""

if old_spawn in s:
    s = s.replace(old_spawn, new_spawn, 1); changes += 1
    print("OK: спавн ограничен 3 активными")
else:
    # regex-вариант
    pattern = r's->obstacle_spawn_timer = 0\.0f;\s*\n\s*for \(int i = 0; i < 8; \+\+i\) \{\s*\n\s*if \(!s->obstacles\[i\]\.active\)'
    m = re.search(pattern, s)
    if m:
        print("[i] найден блок спавна, но якорь отличается — пришлите строки 380–420")

p.write_text(s)
print(f"\nИзменено: {changes}/3")
