#!/usr/bin/env python3
"""patch_34b_star_parallax_field.py — добавить float parallax в struct Star.

Причина: patch_34 пропустил шаг из-за ложноположительной проверки
('float parallax' есть в struct Layer, но не в struct Star).
"""
import re
from pathlib import Path

p = Path('src/main.cpp')
s = p.read_text()

print("=== ДИАГНОСТИКА ===\n")

# Точная проверка: parallax внутри struct Star
m = re.search(r'struct Star\s*\{[^}]*\}', s, re.DOTALL)
if not m:
    print("FAIL: struct Star не найден")
    raise SystemExit(1)
star_body = m.group(0)
print("struct Star:")
for line in star_body.splitlines():
    print(f"  {line}")
print(f"\n  поле parallax в Star: {'ЕСТЬ' if 'parallax' in star_body else 'НЕТ (нужен патч)'}")

# Проверим, что код действительно использует stars[i].parallax
print(f"  stars[i].parallax используется: {s.count('.parallax')} раз(а) всего")

if 'parallax' not in star_body:
    old = '''struct Star {
    float x = 0.0f;
    float y = 0.0f;
    uint8_t brightness = 200;
};'''
    new = '''struct Star {
    float x = 0.0f;
    float y = 0.0f;
    uint8_t brightness = 200;
    float parallax = 0.15f;   // 0.06 slow / 0.15 normal / 0.30 fast
};'''
    if old in s:
        s = s.replace(old, new, 1)
        p.write_text(s)
        print("\nOK: поле float parallax добавлено в struct Star")
    else:
        print("\nFAIL: struct Star не совпал с ожидаемым шаблоном")
        raise SystemExit(1)
else:
    print("\nSKIP: поле уже есть")

# Верификация
print("\n=== ВЕРИФИКАЦИЯ ===\n")
m = re.search(r'struct Star\s*\{[^}]*\}', s, re.DOTALL)
if m and 'parallax' in m.group(0):
    print("OK: struct Star содержит float parallax")
else:
    print("FAIL: поля всё ещё нет")
