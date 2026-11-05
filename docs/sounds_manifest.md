# docs/sounds_manifest.md — Moon Patrol ND Sound Manifest

**Версия:** v20261105 · **Источник истины:** docs/audio_design.md
**Статус файлов:** физически отсутствуют (`assets/` в .gitignore).
В репо — только манифест; WAV/OGG кладутся локально пользователем.

---

## SFX (18) — `SfxId` enum

| SfxId | Файл (assets/sounds/sfx/) | Событие | MVP |
|---|---|---|---|
| SFX_SHOT_H | shot_h.wav | горизонтальный выстрел | ★ |
| SFX_SHOT_V | shot_v.wav | вертикальный выстрел | |
| SFX_JUMP | jump.wav | прыжок | ★ |
| SFX_LAND | land.wav | приземление | |
| SFX_NLO_EXPLODE | nlo_explode.wav | сбитый NLO | ★ |
| SFX_BOMB_EXPLODE | bomb_explode.wav | сбитая бомба | ★ |
| SFX_ROCK_HIT | rock_hit.wav | стрельба по камню | |
| SFX_DEATH_PIT | death_pit.wav | смерть в яму | ★ |
| SFX_DEATH_ROCK | death_rock.wav | смерть от камня | ★ |
| SFX_DEATH_CRATER | death_crater.wav | смерть в кратер | ★ |
| SFX_DEATH_NLO | death_nlo.wav | смерть от NLO | |
| SFX_DEATH_BOMB | death_bomb.wav | смерть от бомбы | |
| SFX_ZONE_CHANGE | zone_change.wav | смена зоны | |
| SFX_CHECKPOINT | checkpoint.wav | чек-поинт | |
| SFX_GAME_OVER | game_over.wav | game over (джингл) | ★ |
| SFX_VICTORY | victory.wav | победа (Z) | |
| SFX_PAUSE | pause.wav | пауза (P) | |
| SFX_MENU_MOVE | menu_move.wav | навигация в меню | ★ |
| SFX_MENU_SELECT | menu_select.wav | выбор в меню | ★ |

★ MVP = 10 файлов. Остальные — по мере рисования. Отсутствие файла → `audio_play_sfx` тихо игнорирует (лог DEBUG, один раз на файл).

---

## Music (4) — `MusicId` enum

| MusicId | Файл (assets/sounds/music/) | Когда | Loop | MVP |
|---|---|---|---|---|
| MUSIC_THEME | theme.ogg | ATTRACT / MENU | да | ★ |
| MUSIC_GAMEPLAY | gameplay.ogg | PLAYING | да | ★ |
| MUSIC_GAME_OVER | game_over.ogg | STATE_GAME_OVER | нет | |
| MUSIC_VICTORY | victory.ogg | победа (Z) | нет | |

---

## Форматы

| Тип | Формат | Sample rate | Channels | Bit depth |
|---|---|---|---|---|
| SFX | WAV | 22050 или 44100 | mono | 16-bit PCM |
| Music | OGG Vorbis | 44100 | stereo | VBR ~128 kbps |

---

## Соответствие `SfxId` → файл (для `patch_50`)

`audio.cpp` формирует путь по массивам `SFX_NAMES` / `MUSIC_NAMES`:

    assets/sounds/sfx/<name>.wav    // SFX_NAMES[id]
    assets/sounds/music/<name>.ogg  // MUSIC_NAMES[id]

Имена в enum (`SFX_SHOT_H`, …) не совпадают с именами файлов — маппинг задаётся массивами `SFX_NAMES` / `MUSIC_NAMES` в `audio.cpp` (уже в skeleton).

---

## Правовая заметка

ROM Moon Patrol © Irem / Williams. Сэмплы из ROM — производные, не коммитить.
`assets/` в `.gitignore`. В репо — только этот манифест и код.
Для публичного релиза — собственные звуки (Audacity/LMMS) или чистая PSG-реализация.
