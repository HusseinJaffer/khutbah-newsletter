"""Build newsletter pages from khutbah .docx files.

Usage: python build.py
Reads khutbahs/*.docx, writes YYYY-MM-DD.html in the repo root, then rebuilds index.html.
Expected layout of each .docx: title line, date line, then Introduction /
"Topic: ..." / Conclusion headings, short sub-headings, verses starting like "Q53:39".
The khutbah wording is copied exactly, never rewritten.
"""
import base64, html, re, sys
from datetime import datetime
from pathlib import Path
from docx import Document

ROOT = Path(__file__).parent
FONTS = ('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400'
         '&family=Figtree:wght@500;700&display=swap')
FOOTER = 'Al-Abbas Islamic Centre, KSIMC of Birmingham'
e = html.escape

CSS = """
:root { --bg:#fff; --fg:#1b1f22; --muted:#5d666c; --accent:#0a6a96; --warm:#d9871a; --rule:#dfe3e5; --plate:#fff;
 --display:"Figtree",system-ui,sans-serif; --serif:"Newsreader",Georgia,"Times New Roman",serif; color-scheme: light; }
html { background:var(--bg); }
body { background:var(--bg); color:var(--fg); font-family:var(--serif); font-size:1.1875rem; line-height:1.65; margin:0; padding-inline:16px; padding-block:0 4rem; }
.plate { background:var(--plate); margin-inline:-16px; padding:1.25rem 16px; display:flex; justify-content:center; }
.plate img { height:clamp(72px,16vw,120px); width:auto; }
main { max-width:42rem; margin-inline:auto; min-width:0; }
header { padding-block:2.5rem 1.5rem; border-bottom:2px solid var(--warm); margin-bottom:1rem; }
.kicker { font-family:var(--display); font-weight:700; letter-spacing:.14em; text-transform:uppercase; font-size:.78rem; color:var(--warm); margin:0 0 .6rem; }
h1 { font-family:var(--display); font-weight:700; font-size:clamp(1.9rem,6vw,2.7rem); line-height:1.12; margin:0 0 .6rem; text-wrap:balance; }
.date { font-family:var(--display); font-weight:500; color:var(--muted); margin:0; }
h2 { font-family:var(--display); font-weight:700; font-size:1.55rem; line-height:1.25; color:var(--accent); margin:2.6rem 0 .6rem; text-wrap:balance; }
h3 { font-family:var(--display); font-weight:700; font-size:1.1rem; margin:2rem 0 .3rem; text-wrap:balance; }
p { margin:0 0 1.05rem; }
blockquote { margin:1.2rem 0; padding:.1rem 0 .1rem 1.1rem; border-left:3px solid var(--accent); font-style:italic; color:#2c3338; }
footer { margin-top:3rem; padding-top:1rem; border-top:1px solid var(--rule); font-family:var(--display); font-size:.85rem; color:var(--muted); }
ul.list { list-style:none; padding:0; margin:1rem 0; }
ul.list li { padding:.9rem 0; border-bottom:1px solid var(--rule); }
ul.list a { font-family:var(--display); font-weight:700; color:var(--accent); text-decoration:none; }
ul.list a:hover { text-decoration:underline; }
ul.list span { display:block; color:var(--muted); font-family:var(--display); font-weight:500; font-size:.9rem; }
"""

def logo_tag():
    p = ROOT / 'assets' / 'Logo.png'
    if not p.exists():
        return ''
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (f'<div class="plate"><img alt="{e(FOOTER)}" src="data:image/png;base64,{b64}"></div>')

def document(title, body):
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{e(title)}</title>\n'
            f'<link rel="stylesheet" href="{FONTS}">\n<style>{CSS}</style>\n</head>\n<body>\n{logo_tag()}\n'
            f'<main>\n{body}\n<footer>{e(FOOTER)}</footer>\n</main>\n</body>\n</html>\n')

def parse_date(s):
    s = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', s.strip())
    return datetime.strptime(s, '%d %B %Y')

def build_khutbah(src):
    paras = []
    for p in Document(src).paragraphs:
        t = p.text.strip()
        if t:
            sn = p.style.name if p.style is not None else ''
            paras.append((t, sn))
    if len(paras) < 3:
        raise ValueError('too few paragraphs')
    title, date_text = paras[0][0], paras[1][0]
    dt = parse_date(date_text)
    body = [f'<header><p class="kicker">Friday sermon summary</p><h1>{e(title)}</h1><p class="date">{e(date_text)}</p></header>']
    for t, sn in paras[2:]:
        if t in ('Introduction', 'Conclusion') or t.startswith('Topic:') or sn == 'Heading 1':
            body.append(f'<h2>{e(t)}</h2>')
        elif re.match(r'^Q\d+:\d+', t):
            body.append(f'<blockquote>{e(t)}</blockquote>')
        elif sn in ('Heading 2', 'Heading 3') or len(t) < 60:
            body.append(f'<h3>{e(t)}</h3>')
        else:
            body.append(f'<p>{e(t)}</p>')
    name = dt.strftime('%Y-%m-%d') + '.html'
    (ROOT / name).write_text(document(f'{title} - {date_text}', '\n'.join(body)), encoding='utf-8')
    return name

def build_index():
    items = []
    for f in ROOT.glob('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].html'):
        txt = f.read_text(encoding='utf-8')
        t = re.search(r'<h1>(.*?)</h1>', txt)
        d = re.search(r'<p class="date">(.*?)</p>', txt)
        items.append((f.name, t.group(1) if t else f.stem, d.group(1) if d else f.stem))
    items.sort(reverse=True)
    lis = '\n'.join(f'<li><a href="{n}">{t}</a><span>{d}</span></li>' for n, t, d in items)
    body = (f'<header><p class="kicker">Friday sermon summaries</p><h1>Khutbah newsletters</h1></header>\n'
            f'<ul class="list">\n{lis}\n</ul>')
    (ROOT / 'index.html').write_text(document('Khutbah newsletters', body), encoding='utf-8')

def main():
    failed = []
    for src in sorted((ROOT / 'khutbahs').glob('*.docx')):
        if src.name.startswith('~$'):
            continue
        try:
            print('built', build_khutbah(src), 'from', src.name)
        except Exception as ex:
            failed.append(src.name)
            print(f'FAILED {src.name}: {ex}', file=sys.stderr)
    build_index()
    if failed:
        sys.exit(1)

if __name__ == '__main__':
    main()
