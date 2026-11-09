# Moon Patrol ND

A reimplementation of the arcade classic Moon Patrol (Irem, 1982) in C++ / SDL3.

Реимплементация аркадной игры Moon Patrol (Irem, 1982) на C++ / SDL3.

## Note / Примечание

Moon Patrol ND is a **creative authorial version** — not a 1:1 reproduction of the arcade original. It is a **test (hacker) version for macOS**. No official releases are planned — this is a testbed for development and emulation technologies.

Moon Patrol ND — **творческая авторская версия**, не 1:1-копия аркадного оригинала. Это **тестовая (хакерская) версия для macOS**. Официальных релизов не планируется — это площадка для обкатки технологий разработки и эмуляции.

## Main development / Основная разработка

The core of the project is the **SDL3 + C++** version of Moon Patrol ND — the primary target, developed for macOS.

Основная часть проекта — версия Moon Patrol ND на **SDL3 + C++**. Это главная цель разработки, ведущаяся под macOS.

## Research tracks / Исследовательские треки

Chats working on reverse-engineering of the original arcade and its ports to various platforms:

Чаты с реверс-инжинирингом оригинальной игры и её версий для различных платформ:

- Arcade (Irem M52) — original / оригинал
- Atari 2600
- Atari 5200
- Atari 8-bit (400/800/XL/XE)
- Atari ST
- MSX
- Commodore 64
- Commodore VIC-20
- IBM PC (DOS)
- Apple II
- Sord M5
- TI-99/4A
- ZX Spectrum

## Ports in plans / Планы по портам

Independent full-scale projects — Moon Patrol never existed on these platforms:

- **Moon Patrol Port (Dendy)** — Dendy / NES / Famicom, CPU 6502
- **Moon Patrol Port (УКНЦ)** — УКНЦ ("Электроника МС 0511"), PDP-11-compatible with two KM1801VM2 CPUs

Независимые полномасштабные проекты — Moon Patrol на этих платформах никогда не существовало:

- **Moon Patrol Port (Dendy)** — Dendy / NES / Famicom, процессор 6502
- **Moon Patrol Port (УКНЦ)** — УКНЦ («Электроника МС 0511»), PDP-11-совместимый с двумя процессорами КМ1801ВМ2

## Documentation / Документация

- [Новости проекта / Project news](https://darkthrone.mooo.com/mpnd/news.html)
- [Описание проекта / Project description](https://darkthrone.mooo.com/mpnd/README.html)
- [Технический отчёт (Arcade) / Reverse-engineering report (Arcade)](https://darkthrone.mooo.com/mpnd/report.html)

## Quick start / Быстрый старт

    brew install sdl3 sdl3_image cmake
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
    cmake --build build -j
    ./build/moon_patrol_nd.app/Contents/MacOS/moon_patrol_nd
