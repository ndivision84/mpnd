# Moon Patrol ND

A reimplementation of the arcade classic **Moon Patrol** (Irem, 1982) in C++ / SDL3.

Реимплементация аркадной игры **Moon Patrol** (Irem, 1982) на C++ / SDL3.

**Version / Версия:** [20261105](VERSION)

---

## Documentation / Документация

- **[README.html](README.html)** — full project description / полное описание проекта
- **[news.html](news.html)** — release notes and changelog / новости и история версий
- **[docs/report.html](docs/report.html)** — ROM reverse-engineering report / технический отчёт по реверс-инжинирингу ROM

---

## Quick start / Быстрый старт
brew install sdl3 sdl3_image cmake
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j
./build/moon_patrol_nd.app/Contents/MacOS/moon_patrol_nd

---

## Links / Ссылки

- **Repository / Репозиторий:** https://github.com/ndivision84/mpnd
- **Releases / Релизы:** https://github.com/ndivision84/mpnd/releases
- **License / Лицензия:** ROM assets (c) Irem / Williams (not included, not distributed)
