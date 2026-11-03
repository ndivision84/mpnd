#!/usr/bin/env python3
"""patch_41 — генерация news.html из NEWS.txt."""
import re
import html as html_mod
from pathlib import Path

print("=== ДИАГНОСТИКА ===\n")

src = Path('NEWS.txt')
if not src.exists():
    print("FAIL: NEWS.txt не найден")
    raise SystemExit(1)

text = src.read_text(encoding='utf-8')
lines = text.split('\n')

print(f"  NEWS.txt: {len(lines)} строк")

# ─── Парсер ────────────────────────────────────────────────
def escape(s):
    return html_mod.escape(s)

articles = []
current = None

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    if not stripped or stripped.startswith('==='):
        i += 1; continue
    if 'Moon Patrol ND — NEWS' in line or stripped.startswith('Реимплементация'):
        i += 1; continue

    m = re.match(r'^\s*(2026-\d{2}-\d{2})\s*·\s*(v\d+)\s*·\s*«(.+)»\s*$', line)
    if m:
        if current: articles.append(current)
        current = {'date': m.group(1), 'version': m.group(2),
                   'title': m.group(3), 'items': []}
        i += 1; continue

    if current is None:
        i += 1; continue

    if stripped.startswith('▸'):
        current['items'].append(('section', stripped[1:].strip()))
        i += 1; continue

    if stripped.startswith('•'):
        content = stripped[1:].strip()
        i += 1
        # continuation lines starting with - 
        while i < len(lines) and lines[i].strip().startswith('- '):
            content += '\n- ' + lines[i].strip()[2:]
            i += 1
        current['items'].append(('bullet', content))
        continue

    if stripped and not stripped.startswith('- '):
        current['items'].append(('para', stripped))
        i += 1; continue

    i += 1

if current:
    articles.append(current)

print(f"  найдено статей: {len(articles)}")

# ─── Генератор HTML ───────────────────────────────────────
def gen_articles(arts):
    parts = []
    for art in arts:
        parts.append('<article class="news-entry">')
        parts.append(f'  <div class="news-date">{art["date"]}</div>')
        parts.append(f'  <div class="news-version">{art["version"]} · «{escape(art["title"])}»</div>')
        in_ul = False
        for kind, content in art['items']:
            if kind == 'section':
                if in_ul: parts.append('  </ul>'); in_ul = False
                parts.append(f'  <h2 class="news-section">▸ {escape(content)}</h2>')
            elif kind == 'bullet':
                if not in_ul: parts.append('  <ul>'); in_ul = True
                sub = content.split('\n')
                parts.append(f'    <li>{escape(sub[0])}')
                if len(sub) > 1:
                    parts.append('      <ul>')
                    for s in sub[1:]:
                        if s.startswith('- '):
                            parts.append(f'        <li>{escape(s[2:])}</li>')
                    parts.append('      </ul>')
                parts.append('    </li>')
            elif kind == 'para':
                if in_ul: parts.append('  </ul>'); in_ul = False
                parts.append(f'  <p>{escape(content)}</p>')
        if in_ul: parts.append('  </ul>')
        parts.append('</article>')
    return '\n'.join(parts)

CSS = '''
:root {
  --bg: #050505; --bg-soft: #0a120a;
  --text: #00dd44; --text-bright: #00ff88; --text-dim: #007744;
  --border: #0a3a0a; --accent: #33ff99; --code-bg: #061006;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 15px; line-height: 1.65;
}
header {
  background: linear-gradient(180deg, #030803 0%, #0a120a 100%);
  border-bottom: 2px solid var(--border);
  padding: 20px 30px; text-align: center;
}
header h1 {
  margin: 0 0 8px 0; color: var(--text-bright);
  font-family: Menlo, Monaco, 'Courier New', monospace;
  font-size: 26px; letter-spacing: 1px;
}
header .subtitle {
  color: var(--text-dim); font-size: 14px;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}
header .links {
  margin-top: 14px; display: flex; gap: 20px;
  justify-content: center; flex-wrap: wrap;
}
header .links a {
  color: var(--accent); text-decoration: none;
  border: 1px solid var(--border);
  padding: 6px 14px; border-radius: 4px; font-size: 13px;
  font-family: Menlo, Monaco, 'Courier New', monospace;
}
header .links a:hover {
  background: var(--bg-soft); border-color: var(--accent);
  color: var(--text-bright);
}
main { max-width: 900px; margin: 0 auto; padding: 40px 30px 60px; }
.news-entry {
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 4px;
  padding: 20px 24px; margin: 0 0 30px 0;
}
.news-date {
  color: var(--text-bright);
  font-family: Menlo, Monaco, 'Courier New', monospace;
  font-size: 14px; letter-spacing: 1px; margin-bottom: 4px;
}
.news-version {
  color: var(--accent);
  font-family: Menlo, Monaco, 'Courier New', monospace;
  font-size: 18px; font-weight: 600;
  margin-bottom: 20px; padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.news-section {
  color: var(--accent);
  font-family: Menlo, Monaco, 'Courier New', monospace;
  font-size: 15px; margin: 20px 0 8px 0;
  letter-spacing: 0.5px;
}
.news-entry ul { margin: 8px 0; padding-left: 24px; }
.news-entry li { margin: 4px 0; }
.news-entry li ul {
  margin: 4px 0; padding-left: 20px;
  list-style: circle;
}
.news-entry li li { color: var(--text-dim); }
.news-entry p { margin: 8px 0; }
code {
  font-family: Menlo, Monaco, 'Courier New', monospace;
  background: var(--code-bg); padding: 2px 6px;
  border-radius: 3px; color: var(--text-bright); font-size: 13px;
}
footer {
  text-align: center; padding: 30px 20px;
  color: var(--text-dim); font-size: 12px;
  font-family: Menlo, Monaco, 'Courier New', monospace;
  border-top: 2px solid var(--border);
}
@media (max-width: 700px) {
  main { padding: 20px 15px 40px; }
  header { padding: 15px; }
  header h1 { font-size: 20px; }
}
'''

HTML = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Moon Patrol ND — NEWS</title>
<style>{CSS}</style>
</head>
<body>

<header>
  <h1>📰 Moon Patrol ND — NEWS</h1>
  <div class="subtitle">Новости проекта по датам</div>
  <div class="links">
    <a href="README.html">📖 README</a>
    <a href="https://github.com/ndivision84/mpnd">📦 GitHub</a>
    <a href="docs/report.html">📊 Технический отчёт</a>
  </div>
</header>

<main>
{gen_articles(articles)}
</main>

<footer>
  Moon Patrol ND · v20261104 · Nordic Division · 2026
</footer>

</body>
</html>
'''

Path('news.html').write_text(HTML, encoding='utf-8')
print(f"\nOK: news.html создан ({len(HTML.splitlines())} строк, {len(articles)} статей)")

# verification
s = Path('news.html').read_text(encoding='utf-8')
checks = [
    ('2 статьи (2026-11-04 + 2026-10-30)', s.count('news-entry') >= 2),
    ('версия v20261104 присутствует',       'v20261104' in s),
    ('версия v20261030 присутствует',       'v20261030' in s),
    ('стили подключены',                    ':root' in s),
    ('ссылка на README.html',               'README.html' in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
