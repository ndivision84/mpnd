#!/usr/bin/env python3
"""patch_43 — news.html v2: сортировка (новые сверху), фильтр ---, sub-bullets по отступу."""
import re
import html as html_mod
from pathlib import Path

src = Path('NEWS.txt')
if not src.exists():
    print("FAIL: NEWS.txt не найден"); raise SystemExit(1)

lines = src.read_text(encoding='utf-8').split('\n')
print(f"=== ДИАГНОСТИКА ===\n  NEWS.txt: {len(lines)} строк")

def escape(s):
    return html_mod.escape(s)

def is_header(stripped):
    """ALL-CAPS короткая строка (без ▸/•/-)."""
    if not stripped or len(stripped) > 50: return False
    if stripped[0] in '▸•-=': return False
    if not stripped[0].isalpha(): return False
    return all(c.isupper() or not c.isalpha() for c in stripped)

articles = []
current = None
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())

    # Skip separators and empty
    if not stripped or stripped.startswith('===') or stripped.startswith('---'):
        i += 1; continue
    if 'Moon Patrol ND — NEWS' in line or stripped.startswith('Реимплементация'):
        i += 1; continue

    # Article header
    m = re.match(r'^\s*(2026-\d{2}-\d{2})\s*·\s*([vV]\d+)\s*·\s*«(.+)»\s*$', line)
    if m:
        if current: articles.append(current)
        current = {'date': m.group(1), 'version': m.group(2),
                   'title': m.group(3), 'items': []}
        i += 1; continue
    if current is None:
        i += 1; continue

    # Section ▸
    if stripped.startswith('▸'):
        current['items'].append(('section', stripped[1:].strip(), []))
        i += 1; continue

    # Bullet •
    if stripped.startswith('•'):
        content = stripped[1:].strip()
        subs = []
        bullet_indent = indent
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if not nxt.strip(): break
            nxt_s = nxt.strip()
            nxt_indent = len(nxt) - len(nxt.lstrip())
            if nxt_indent <= bullet_indent: break
            if nxt_s[0] in '▸•=-': break
            sub = nxt_s[2:] if nxt_s.startswith('- ') else nxt_s
            subs.append(sub)
            i += 1
        current['items'].append(('bullet', content, subs))
        continue

    # ALL-CAPS header
    if is_header(stripped):
        current['items'].append(('header', stripped, []))
        i += 1; continue

    # Paragraph
    current['items'].append(('para', stripped, []))
    i += 1

if current: articles.append(current)

# ── Сортировка: новые сверху ──
articles.sort(key=lambda a: a['date'], reverse=True)
print(f"  найдено статей: {len(articles)}")
if articles:
    print(f"  порядок: {[a['date'] for a in articles]}")

def gen_items(items):
    parts = []
    in_ul = False
    for kind, content, subs in items:
        if kind == 'section':
            if in_ul: parts.append('  </ul>'); in_ul = False
            parts.append(f'  <h2 class="news-section">▸ {escape(content)}</h2>')
        elif kind == 'header':
            if in_ul: parts.append('  </ul>'); in_ul = False
            parts.append(f'  <h3 class="news-subsection">{escape(content)}</h3>')
        elif kind == 'bullet':
            if not in_ul: parts.append('  <ul>'); in_ul = True
            if subs:
                parts.append(f'    <li>{escape(content)}')
                parts.append('      <ul class="news-sublist">')
                for s in subs:
                    parts.append(f'        <li>{escape(s)}</li>')
                parts.append('      </ul></li>')
            else:
                parts.append(f'    <li>{escape(content)}</li>')
        elif kind == 'para':
            if in_ul: parts.append('  </ul>'); in_ul = False
            parts.append(f'  <p class="news-para">{escape(content)}</p>')
    if in_ul: parts.append('  </ul>')
    return '\n'.join(parts)

def gen_articles(arts):
    out = []
    for art in arts:
        out.append('<article class="news-entry">')
        out.append(f'  <div class="news-date">{art["date"]}</div>')
        out.append(f'  <div class="news-version">{escape(art["version"])} · «{escape(art["title"])}»</div>')
        out.append(gen_items(art['items']))
        out.append('</article>')
    return '\n'.join(out)

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
.news-subsection {
  color: var(--text-bright);
  font-family: Menlo, Monaco, 'Courier New', monospace;
  font-size: 14px; margin: 16px 0 6px 0;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.news-para { margin: 8px 0; color: var(--text); }
.news-entry ul { margin: 8px 0; padding-left: 24px; }
.news-entry li { margin: 4px 0; }
.news-sublist { margin: 4px 0; padding-left: 20px; list-style: circle; }
.news-sublist li { color: var(--text-dim); }
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
print(f"\nOK: news.html пересоздан ({len(HTML.splitlines())} строк)")

# verification
s = Path('news.html').read_text(encoding='utf-8')
first_date_m = re.search(r'<div class="news-date">(\d{4}-\d{2}-\d{2})</div>', s)
first_date = first_date_m.group(1) if first_date_m else '?'
checks = [
    ('первая статья = 2026-11-04',   first_date == '2026-11-04'),
    ('2 статьи',                     s.count('news-entry') >= 2),
    ('нет линии "-----"',            '-----' not in s),
    ('sub-bullets (Группа)',         'news-sublist' in s),
    ('стили',                        ':root' in s),
    ('ссылка на README.html',        'README.html' in s),
]
ok = 0
for name, cond in checks:
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    if cond: ok += 1
print(f"\nИтог: {ok}/{len(checks)}")
