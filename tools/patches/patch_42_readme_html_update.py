#!/usr/bin/env python3
"""patch_42 — обновление README.html до v20261104."""
from pathlib import Path

p = Path('README.html')
if not p.exists():
    print("FAIL: README.html не найден")
    raise SystemExit(1)

s = p.read_text(encoding='utf-8')
print(f"  README.html: {len(s.splitlines())} строк")
print(f"  v20261030: {'есть' if 'v20261030' in s else 'НЕТ'}")

changes = 0

if 'v20261030' in s:
    s = s.replace('v20261030', 'v20261104')
    changes += 1
    print("OK: v20261030 → v20261104")

old_sub = '<span style="margin-left: 10px; color: var(--text-dim); font-family: Menlo, monospace; font-size: 13px;">Zones &amp; Lives</span>'
new_sub = '<span style="margin-left: 10px; color: var(--text-dim); font-family: Menlo, monospace; font-size: 13px;">Refactor + Menu</span>'
if old_sub in s:
    s = s.replace(old_sub, new_sub, 1)
    changes += 1
    print("OK: subtitle → Refactor + Menu")

old_gp = '<li>Смешанный счёт: дистанция-зоны + очки за убийства</li>'
new_gp = old_gp + '''
    <li><strong>Главное меню</strong>: NEW GAME / OPTIONS / QUIT (v20261104)</li>
    <li><strong>Навигация</strong>: ↑/↓, курсор ▶ (v20261104)</li>'''
if old_gp in s and 'Главное меню' not in s:
    s = s.replace(old_gp, new_gp, 1)
    changes += 1
    print("OK: +меню в раздел Геймплей")

old_tech = '<li>Полный реверс-инжиниринг ROM (<code>docs/report.html</code>)</li>\n  </ul>'
new_tech = old_tech + '''

  <h3>Архитектура (v20261104)</h3>
  <ul>
    <li><code>src/app.h</code> — все structs (189 строк)</li>
    <li><code>src/menu.cpp/.h</code> — главное меню</li>
    <li><code>src/scores.cpp/.h</code> — TOP-10 (скелет)</li>
    <li><code>src/settings.cpp/.h</code> — настройки (скелет)</li>
    <li>Early-return в <code>SDL_AppIterate</code> для MENU/OPTIONS</li>
  </ul>'''
if old_tech in s and 'Архитектура (v20261104)' not in s:
    s = s.replace(old_tech, new_tech, 1)
    changes += 1
    print("OK: +раздел Архитектура")

old_plans = '''    <tr><td>1</td><td>Рефакторинг <code>main.cpp</code> → модули</td><td>—</td></tr>
    <tr><td>2</td><td>TOP-10 игроков (ввод имени + <code>saves/scores.json</code>)</td><td>—</td></tr>
    <tr><td>3</td><td>Новое стартовое меню</td><td>—</td></tr>
    <tr><td>4</td><td>Спрайты: луноход, NLO, препятствия, бомба</td><td><strong>MPND_ART</strong></td></tr>
    <tr><td>5</td><td>Заставки START и GAME OVER</td><td><strong>MPND_ART</strong></td></tr>
    <tr><td>6</td><td>Движок музыки и звука</td><td><strong>MPND_SOUND</strong></td></tr>'''
new_plans = '''    <tr><td>1</td><td>OPTIONS: DIFFICULTY + LIVES со стрелками</td><td>patch_44</td></tr>
    <tr><td>2</td><td>NAME: ввод до 10 символов</td><td>patch_45</td></tr>
    <tr><td>3</td><td>TOP SCORES: просмотр таблицы</td><td>patch_46</td></tr>
    <tr><td>4</td><td>JSON: сохранение/загрузка</td><td>patch_47</td></tr>
    <tr><td>5</td><td>Интеграция: GAME_OVER → TOP SCORES</td><td>patch_48</td></tr>
    <tr><td>6</td><td>Спрайты: луноход, NLO, препятствия, бомба</td><td><strong>MPND_ART</strong></td></tr>
    <tr><td>7</td><td>Заставки START и GAME OVER</td><td><strong>MPND_ART</strong></td></tr>
    <tr><td>8</td><td>Движок музыки и звука</td><td><strong>MPND_SOUND</strong></td></tr>'''
if old_plans in s:
    s = s.replace(old_plans, new_plans, 1)
    changes += 1
    print("OK: обновлён раздел Что в планах")

old_links = '<a href="NEWS.txt">📰 NEWS.txt</a>'
new_links = '<a href="news.html">📰 NEWS</a>'
if old_links in s:
    s = s.replace(old_links, new_links, 1)
    changes += 1
    print("OK: ссылка NEWS.txt → news.html")

p.write_text(s, encoding='utf-8')
print(f"\nВсего изменений: {changes}")

s = p.read_text(encoding='utf-8')
checks = [
    ('v20261104 присутствует',      'v20261104' in s),
    ('v20261030 отсутствует',       'v20261030' not in s),
    ('Главное меню в Геймплей',     'Главное меню' in s),
    ('Архитектура раздел',          'Архитектура' in s),
    ('patch_44 в планах',           'patch_44' in s),
    ('ссылка на news.html',         'news.html' in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
