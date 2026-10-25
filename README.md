# Moon Patrol ND

Реимплементация аркадной игры **Moon Patrol** (Irem, 1982) на C++ с SDL3.

## Сборка

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
    cmake --build build -j
    ./build/moon_patrol_nd

## Структура

- src/      — C++ код
- assets/   — тайлы, уровни, спрайты
- tools/    — Python-скрипты
- docs/     — отчёт, документация

## Статус

- [x] Реверс-инжиниринг архитектуры (docs/REPORT.md)
- [ ] Извлечение тайлов из mpe-*
- [ ] Извлечение уровней из 0x2D44
- [ ] Скелет SDL3
- [ ] Player + физика
- [ ] Враги, пули, коллизии
- [ ] HUD, score, звук

## Лицензия

Код — MIT. ROM-файлы — © Irem/Williams, только для личного реверсинжиниринга.
