# Audio Design — Moon Patrol ND

**Версия:** v20261105 · **Дата:** 2026-11-05
**Роль:** источник истины для MPND_SOUND. Согласовано между ND Dev и Sound.

---

## 1. Решения (D1–D9)

| # | Решение | Значение |
|---|---|---|
| D1 | Расположение кода | `src/audio.cpp` + `src/audio.h` (плоско) |
| D2 | Структура assets | `assets/sounds/sfx/*.wav` + `assets/sounds/music/*.ogg` |
| D3 | Список SFX | 18 (детальный), enum на все, MVP — 8–10 |
| D4 | Стратегия MVP | Нарисовать 8–10 SFX вручную + MAME reference. Реверс — отдельно |
| D5 | `mp-s1.1a` | Только один звуковой ROM. `mp-s1.2a` — ошибка Handoff 1 |
| D6 | CPU звука | Known unknown, не блокирует MVP |
| D7 | MAME на macOS 12.7.6 Intel | Known issue, обход `-video bgfx` / `-video opengl` / MAME 0.279 |
| D8 | assets/sounds/ в .gitignore | Да (уже покрыто `assets/`) |
| D9 | Библиотека | SDL3_mixer (первый), miniaudio.h (fallback), no-op (последний) |

---

## 2. API (`src/audio.h`)

    #pragma once
    #include "app.h"

    enum SfxId {
        SFX_SHOT_H, SFX_SHOT_V, SFX_JUMP, SFX_LAND,
        SFX_NLO_EXPLODE, SFX_BOMB_EXPLODE, SFX_ROCK_HIT,
        SFX_DEATH_PIT, SFX_DEATH_ROCK, SFX_DEATH_CRATER,
        SFX_DEATH_NLO, SFX_DEATH_BOMB,
        SFX_ZONE_CHANGE, SFX_CHECKPOINT,
        SFX_GAME_OVER, SFX_VICTORY, SFX_PAUSE,
        SFX_MENU_MOVE, SFX_MENU_SELECT,
        SFX_COUNT
    };

    enum MusicId {
        MUSIC_THEME, MUSIC_GAMEPLAY, MUSIC_GAME_OVER, MUSIC_VICTORY,
        MUSIC_COUNT
    };

    void audio_init(AppState* s);
    void audio_update(AppState* s, float dt);
    void audio_quit(AppState* s);
    void audio_play_sfx(AppState* s, SfxId id);
    void audio_play_music(AppState* s, MusicId id, bool loop = true);
    void audio_stop_music(AppState* s, float fade_sec = 0.0f);
    void audio_pause_music(AppState* s);
    void audio_resume_music(AppState* s);
    void audio_set_music_volume(AppState* s, int volume_0_100);
    void audio_set_sfx_volume(AppState* s, int volume_0_100);
    void audio_set_muted(AppState* s, bool muted);

---

## 3. Формат файлов

| Тип | Формат | Sample rate | Channels | Bit depth |
|---|---|---|---|---|
| SFX | WAV | 22050 или 44100 | mono | 16-bit PCM |
| Music | OGG Vorbis | 44100 | stereo | VBR ~128 kbps |

Причина: SFX — короткие, WAV без сжатия (минимум задержки). Music — длинная, OGG сжимает.

---

## 4. Список SFX (18)

| SfxId | Файл | Событие | Описание |
|---|---|---|---|
| SFX_SHOT_H | shot_h.wav | горизонтальный выстрел | короткий «пиу» |
| SFX_SHOT_V | shot_v.wav | вертикальный выстрел | отличается тоном |
| SFX_JUMP | jump.wav | прыжок | свист вверх |
| SFX_LAND | land.wav | приземление | глухой удар |
| SFX_NLO_EXPLODE | nlo_explode.wav | сбитый NLO | взрыв |
| SFX_BOMB_EXPLODE | bomb_explode.wav | сбитая бомба | взрыв |
| SFX_ROCK_HIT | rock_hit.wav | стрельба по камню | крошка |
| SFX_DEATH_PIT | death_pit.wav | смерть в яму | падение |
| SFX_DEATH_ROCK | death_rock.wav | смерть от камня | удар |
| SFX_DEATH_CRATER | death_crater.wav | смерть в кратер | взрыв |
| SFX_DEATH_NLO | death_nlo.wav | смерть от NLO | взрыв |
| SFX_DEATH_BOMB | death_bomb.wav | смерть от бомбы | взрыв |
| SFX_ZONE_CHANGE | zone_change.wav | смена зоны | короткий сигнал |
| SFX_CHECKPOINT | checkpoint.wav | чек-поинт | восходящий аккорд |
| SFX_GAME_OVER | game_over.wav | game over | нисходящая гамма |
| SFX_VICTORY | victory.wav | победа (Z) | фанфары |
| SFX_PAUSE | pause.wav | пауза (P) | короткий «клик» |
| SFX_MENU_MOVE | menu_move.wav | навигация в меню | тихий «тик» |
| SFX_MENU_SELECT | menu_select.wav | выбор в меню | «подтверждение» |

**MVP (8–10):** shot_h, jump, nlo_explode, bomb_explode, death_pit, death_rock, death_crater, game_over, menu_move, menu_select.

---

## 5. Список музыки (4)

| MusicId | Файл | Когда | Loop | Длительность |
|---|---|---|---|---|
| MUSIC_THEME | theme.ogg | ATTRACT / MENU | да | 30–60 сек |
| MUSIC_GAMEPLAY | gameplay.ogg | PLAYING | да | 60–120 сек |
| MUSIC_GAME_OVER | game_over.ogg | STATE_GAME_OVER | нет | 3–5 сек |
| MUSIC_VICTORY | victory.ogg | победа (Z) | нет | 5–10 сек |

**MVP (1–2):** theme + gameplay. Остальные — по мере рисования.

---

## 6. Fade-политика

| Переход | Fade out | Fade in | Пауза |
|---|---|---|---|
| MENU → PLAYING | 0.3 сек | 0.3 сек | 0 |
| PLAYING → GAME_OVER | 0.3 сек | 0.3 сек | 0.1 сек |
| GAME_OVER → SCORE → MENU | 0.3 сек | 0.3 сек | 0 |
| Первый старт | — | 0.3 сек | 0 |

---

## 7. Пауза

- Музыка ставится на паузу (`audio_pause_music` / `audio_resume_music`)
- SFX при паузе не играют (кроме самого «клика» паузы)

---

## 8. Громкость

- `Settings` в `app.h` расширяется (patch_45d):
    - `music_volume` (0–100), default 100
    - `sfx_volume` (0–100), default 100
    - `muted` (0/1), default 0
- UI для громкости в OPTIONS — отдельная задача (не блокирует аудио)
- `audio_init` читает `s->settings.music_volume` / `sfx_volume` / `muted`

---

## 9. Логирование

- `SDL_Log` — как везде в проекте
- Префиксы:
    - `Audio: init (SDL3_mixer, 44100 Hz, 8 channels)` — INFO
    - `Audio: music <name> (loop=true)` — INFO
    - `Audio: sfx <name>` — DEBUG
    - `Audio: shutdown` — INFO
    - `Audio: disabled (no SDL3_mixer)` — WARNING
    - `Audio: sfx <name> missing (file not found)` — DEBUG (один раз)

---

## 10. Точки вызова SFX/Music (для patch_50_audio_integration)

| Где | Что | SFX/Music |
|---|---|---|
| SDL_AppInit (после menu_init) | audio_init(s) | — |
| SDL_AppIterate (early-return MENU/OPTIONS) | audio_update(s, menu_dt) | — |
| SDL_AppIterate (PLAYING) | audio_update(s, dt) | — |
| Space (shoot) | audio_play_sfx(SFX_SHOT_H) | SFX |
| Up (jump) | audio_play_sfx(SFX_JUMP) | SFX |
| on_ground = true (после прыжка) | audio_play_sfx(SFX_LAND) | SFX |
| player_died(s, "PIT") | SFX_DEATH_PIT | SFX |
| player_died(s, "ROCK") | SFX_DEATH_ROCK | SFX |
| player_died(s, "CRATER") | SFX_DEATH_CRATER | SFX |
| player_died(s, "NLO") | SFX_DEATH_NLO | SFX |
| player_died(s, "BOMB") | SFX_DEATH_BOMB | SFX |
| пуля × NLO | SFX_NLO_EXPLODE | SFX |
| пуля × BOMBA | SFX_BOMB_EXPLODE | SFX |
| пуля × ROCK | SFX_ROCK_HIT | SFX |
| new_zone > zone_index | SFX_ZONE_CHANGE | SFX |
| checkpoint_zone обновился | SFX_CHECKPOINT | SFX |
| lives == 0 (в player_died) | MUSIC_GAME_OVER (loop=false) | Music |
| state = STATE_MENU | MUSIC_THEME (loop=true) | Music |
| state = STATE_PLAYING (NEW GAME) | MUSIC_GAMEPLAY (loop=true) | Music |
| победа (Z) | MUSIC_VICTORY (loop=false) | Music |
| P (пауза) | SFX_PAUSE + audio_pause_music | SFX+Music |
| menu_cursor изменился | SFX_MENU_MOVE | SFX |
| SPACE на пункте меню | SFX_MENU_SELECT | SFX |
| SDL_AppQuit | audio_quit(s) | — |

Итого: **24 точки вызова.** Реализуется в `patch_50_audio_integration.py` (ND Dev).

---

## 11. Known issues / open questions

| # | Вопрос | Статус |
|---|---|---|
| 1 | CPU звука: M6802 / M6809 / Z80? | Открыт. Reversing Arcade, если пойдём в Вариант 1 |
| 2 | `mp-s1.1a` (4096 B, энтропия 6.54) — звуковой ROM? | Не проверен. Reversing Arcade |
| 3 | MAME на macOS 12.7.6 Intel падает | Обход: `-video bgfx` / `-video opengl` / MAME 0.279 |
| 4 | SDL3_mixer на macOS 12.7.6 Intel | Проверить `brew search sdl3_mixer`. Если нет — miniaudio fallback |
| 5 | Слайдеры громкости в OPTIONS | Отложено (отдельная задача, не блокирует аудио) |

---

## 12. Правовая заметка

ROM-файлы Moon Patrol © Irem / Williams.
Сэмплы, извлечённые из ROM, — производные (© Irem / Williams).
**Не коммитить в git.** `assets/` в `.gitignore`.
Для публичного релиза — **собственные звуки** (Вариант 3, Audacity/LMMS) или **чистая реализация PSG** (Вариант 1, без копирования ROM-данных).

---

## 13. План первой сессии (Sound-чат)

1. Финализировать этот документ
2. `patch_49_audio_skeleton.py` — создаёт `src/audio.cpp` / `src/audio.h` с API (no-op)
3. `#include "audio.h"` + `audio_init/update/quit` в `main.cpp` (4 якоря)
4. `CMakeLists.txt` — 2 якоря (find_package SDL3_mixer + link)
5. Проверить `brew search sdl3_mixer` → если есть, `brew install`
6. Нарисовать 3–5 SFX в Audacity (proof of concept)
7. Проверить, что `audio_play_sfx(SFX_SHOT_H)` реально играет

---

**Конец docs/audio_design.md.**
