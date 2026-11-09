#!/usr/bin/env python3
"""patch_45m_news_final.py — универсальный фикс новостей 2026-11-09.

Сценарии:
A. Есть старая длинная Port-новость → заменяет на 3 короткие (правильный ZX).
B. Есть 3 короткие, но ZX со старым текстом → правит только ZX.
C. Всё уже правильно → SKIP.

3 новости:
1. Порты: Dendy (Famicom/NES) + УКНЦ
2. ZX: инструменты ПЛАНИРУЮТСЯ к внедрению, реверс Atarisoft
3. Wiki-сайт — наш реестр всех версий
"""
from pathlib import Path
import re
import sys

NEWS = Path("NEWS.txt")
OLD_TITLE = "Новое направление Port: Dendy/NES/Famicom и УКНЦ"
T1 = "Порты: Dendy (Famicom/NES) и УКНЦ"
T2 = "ZX: новые инструменты, версия в работе"
T3 = "Запущен wiki-сайт со списком всех версий"

OLD_ZX = (
    " Развёрнуты новые инструменты реверса (Unreal-NG\n"
    " с time-travel debugging, профилировщиком и трассировкой памяти).\n"
)
NEW_ZX = (
    " Планируются к внедрению в проект новые инструменты реверса\n"
    " (Unreal-NG: time-travel debugging, профилировщик, трассировка памяти).\n"
)

print("=== ДИАГНОСТИКА ===")
if not NEWS.exists():
    print("FAIL: NEWS.txt не найден")
    sys.exit(1)
c = NEWS.read_text(encoding="utf-8")
print("Длина:", len(c))
print("Старая длинная:", OLD_TITLE in c)
print("Короткие T1/T2/T3:", T1 in c, T2 in c, T3 in c)
print("Старый ZX-текст:", OLD_ZX in c)

# === СЦЕНАРИЙ A: заменить длинную на 3 короткие ===
if OLD_TITLE in c:
    print("=== СЦЕНАРИЙ A: замена длинной новости ===")
    BLOCK = (
        "================================\n"
        " 2026-11-09 · v20261105 · «" + T1 + "»\n"
        "================================\n"
        "\n"
        " Открыты два направления портирования Moon Patrol: Dendy (Famicom/NES,\n"
        " CPU 6502) и УКНЦ («Электроника МС 0511», PDP-11). На этих платформах\n"
        " игры ранее не существовало — разработка с нуля.\n"
        "\n"
        "================================\n"
        " 2026-11-09 · v20261105 · «" + T2 + "»\n"
        "================================\n"
        "\n"
        " ZX-трек в работе. Планируются к внедрению в проект новые\n"
        " инструменты реверса (Unreal-NG: time-travel debugging,\n"
        " профилировщик, трассировка памяти). Для реверса взята\n"
        " оригинальная версия для ZX Spectrum (Atarisoft, 1984).\n"
        " Полный список версий — в нашем wiki:\n"
        " https://moonpatrol.mooo.com/doku.php?id=start\n"
        "\n"
        "================================\n"
        " 2026-11-09 · v20261105 · «" + T3 + "»\n"
        "================================\n"
        "\n"
        " Запущен наш wiki-сайт Moon Patrol — реестр всех версий игры:\n"
        " https://moonpatrol.mooo.com/doku.php?id=start\n"
        " Список будет активно пополняться по мере готовности треков.\n"
        "\n"
    )
    pat = re.compile(
        r'={32}\n 2026-11-09 · v20261105 · «' + re.escape(OLD_TITLE) + r'»\n={32}\n.*?={32}\n',
        re.DOTALL,
    )
    m = pat.search(c)
    if not m:
        print("FAIL: не нашли блок замены")
        sys.exit(1)
    c = c[:m.start()] + BLOCK + c[m.end():]
    NEWS.write_text(c, encoding="utf-8")
    print("OK: 3 короткие новости вставлены")

# === СЦЕНАРИЙ B: короткие есть, но ZX старый ===
elif OLD_ZX in c:
    print("=== СЦЕНАРИЙ B: фикс ZX-текста ===")
    c = c.replace(OLD_ZX, NEW_ZX, 1)
    NEWS.write_text(c, encoding="utf-8")
    print("OK: ZX-текст исправлен на «Планируются к внедрению»")

# === СЦЕНАРИЙ C: всё уже правильно ===
elif T1 in c and T2 in c and T3 in c and "Планируются к внедрению" in c:
    print("SKIP: всё уже правильно")
    sys.exit(0)
else:
    print("FAIL: не распознали состояние NEWS.txt")
    sys.exit(1)

print("=== ВЕРИФИКАЦИЯ ===")
final = NEWS.read_text(encoding="utf-8")
checks = {
    "T1": T1 in final,
    "T2": T2 in final,
    "T3": T3 in final,
    "Нет длинной": OLD_TITLE not in final,
    "«Планируются»": "Планируются к внедрению" in final,
    "Нет «Развёрнуты»": "Развёрнуты новые инструменты" not in final,
    "Atarisoft": "Atarisoft" in final,
    "Wiki URL x2": final.count("https://moonpatrol.mooo.com/doku.php?id=start") >= 2,
    "README-новость цела": "README и сайт: творческая версия ND" in final,
}
ok = True
for k, v in checks.items():
    print(("OK  " if v else "FAIL"), k)
    if not v:
        ok = False
if ok:
    print("OK: patch_45m_news_final применён")
else:
    sys.exit(1)
