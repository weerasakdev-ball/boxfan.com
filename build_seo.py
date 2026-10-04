#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOXFAN — build_seo.py
════════════════════════════════════════════════════════════════════
ทำให้ Google / Facebook / LINE "เห็น" เนื้อหาที่หน้าเว็บสร้างด้วย JavaScript

ปัญหาเดิม: ตารางอันดับ ผลมวย โปรแกรมชก ฯลฯ ถูกสร้างด้วย JS หลังโหลด
fighters_data.js — บอตที่ไม่รัน JS (หรือรันช้า) จึงเห็นหน้าว่าง "พบ 0 คน"

วิธีแก้ (prerender):
  1) เปิดแต่ละหน้าด้วย Chrome หรือ Edge ที่มีในเครื่องอยู่แล้ว แบบไม่แสดงหน้าจอ (headless)
  2) รอให้ JavaScript ของหน้านั้นทำงานจนเสร็จ
  3) คัดลอก HTML ที่ได้ เฉพาะกล่องเนื้อหาที่กำหนดไว้ใน PAGES ด้านล่าง
     กลับไปเขียนลงไฟล์ .html ต้นฉบับ
  → ใช้โค้ด JS เดิมของหน้าเว็บคำนวณ ตัวเลขจึงตรงกับที่ผู้ใช้เห็น 100%
  → เวลาคนเปิดเว็บ JS ยังทำงานทับเหมือนเดิม (ตัวกรอง ค้นหา สลับธีม ใช้ได้ครบ)

นอกจากนั้นยัง:
  • สร้างหน้าอันดับแยกรุ่นน้ำหนัก rankings-<รุ่น>.html (จากแม่แบบ weight-classes.html)
  • สร้าง sitemap.xml ใหม่ (หน้าหลัก + รุ่นน้ำหนัก + บทความ + โปรไฟล์นักมวยทุกคน)
  • สร้าง robots.txt

วิธีใช้ — รันที่โฟลเดอร์รากของเว็บ (ที่มี index.html):
    python build_seo.py
รันทุกครั้งหลังอัปเดตข้อมูลนักมวย (หลัง generate_profiles.py) แล้วค่อย push ขึ้นเว็บ

ไม่ต้องติดตั้งอะไรเพิ่ม: ใช้ Python 3.8+ และ Chrome หรือ Microsoft Edge
(Windows 10/11 มี Edge มาให้อยู่แล้ว) — ถ้าหาไม่เจอ ตั้งตัวแปร BOXFAN_BROWSER
ให้ชี้ไปที่ไฟล์ chrome.exe / msedge.exe ได้
════════════════════════════════════════════════════════════════════
"""
import html as H
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

try:  # หน้าจอ Windows บางเครื่องพิมพ์ภาษาไทยไม่ได้
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
SITE = 'https://www.boxingfandom.com'
DATA = ROOT / 'data' / 'fighters_data.js'
WAIT_MS = 20000          # เวลาที่ให้ JS ทำงานสูงสุดต่อหน้า (มิลลิวินาที)
PARALLEL = 3             # เปิดเบราว์เซอร์พร้อมกันกี่หน้า

# ═══════════════════════════════════════════════════════════════════
# หน้าที่จะ prerender และกล่องที่ต้องคัดลอก
#   ids  = id ของกล่องใน <body> ที่ JS เขียนเนื้อหาลงไป (คัดลอกเนื้อหาข้างใน)
#          ⚠ ห้ามใส่กล่องที่ JS "ต่อท้าย" (appendChild) โดยไม่ล้างก่อน เช่น <select>
#             ที่เติม <option> ทีละอัน — ไม่งั้นตัวเลือกจะซ้ำสองชุด
#   head = id ของ <script type="application/ld+json"> ที่ JS สร้าง
#   marks= ช่วงที่ครอบด้วย <!--PR:ชื่อ--> … <!--/PR:ชื่อ--> (เมนู/ท้ายเว็บจาก boxfan-shared.js)
# ═══════════════════════════════════════════════════════════════════
PAGES = {
    'index.html': dict(
        ids=['dtabs', 'gc-m', 'gc-f', 'rk-scope', 'rk-count', 'rank-body', 'featured-card',
             'pred-wrap', 'upcoming-grid', 'news-grid', 'seo-answer-top', 'stat-fighters',
             'stat-divisions', 'stat-fights', 'stat-updated', 'f-year', 'rank-menu', 'drawer-rank-sub'],
        head=['jsonld-rank', 'jsonld-faq']),
    'rankings.html': dict(
        ids=['g-cnt-m', 'g-cnt-f', 'fp-count', 'fp-badge', 'fp-scope-note', 'tbl-body', 'pager'],
        head=['jsonld-rankings'], marks=['chrome', 'foot']),
    'weight-classes.html': dict(
        ids=['crumb', 'wc-title', 'wc-sub', 'wc-content', 'f-year'], head=['jsonld-div']),
    'fighters.html': dict(
        ids=['alpha', 'grid', 'fd-count', 'fd-directory', 'fd-dir-n'],
        head=['jsonld-fighters'], marks=['chrome', 'foot']),
    'results.html': dict(
        ids=['st-fi', 'st-ko', 'st-ev', 'st-last', 'promo-tabs', 'area', 'found-count', 'found-ev'],
        head=['jsonld-results'], marks=['chrome', 'foot']),
    'schedule.html': dict(
        ids=['st-matches', 'st-next', 'st-fighters', 'st-events', 'schedule'],
        head=['jsonld-schedule'], marks=['chrome', 'foot']),
    'blog/index.html': dict(ids=['count-bar', 'article-grid', 'yr-ft']),
    'about.html': dict(ids=['ab-fighters', 'ab-matches', 'ab-countries', 'yr-ft']),
}
DIV_PAGE_SPEC = dict(ids=['crumb', 'wc-title', 'wc-sub', 'wc-content', 'f-year'], head=['jsonld-div'])

# รุ่นน้ำหนัก — ต้องตรงกับ DIV_MAP / divKey() ใน utils.js
DIV_MAP = [
    ('atom', 'อะตอมเวท', 'Atomweight', 'ต่ำกว่า 115 ปอนด์'),
    ('straw', 'สตรอว์เวท', 'Strawweight', '115–125 ปอนด์'),
    ('fly', 'ฟลายเวท', 'Flyweight', '125–135 ปอนด์'),
    ('bantam', 'แบนตัมเวท', 'Bantamweight', '135–145 ปอนด์'),
    ('feather', 'เฟเธอร์เวท', 'Featherweight', '145–155 ปอนด์'),
    ('light', 'ไลท์เวท', 'Lightweight', '155–170 ปอนด์'),
    ('welter', 'เวลเทอร์เวท', 'Welterweight', '170–185 ปอนด์'),
    ('middle', 'มิดเดิลเวท', 'Middleweight', '185–205 ปอนด์'),
    ('lightheavy', 'ไลท์เฮฟวีเวท', 'Light Heavyweight', '205–225 ปอนด์'),
    ('heavy', 'เฮฟวีเวท', 'Heavyweight', '225 ปอนด์ขึ้นไป'),
    ('catch', 'แคชเวท', 'Catchweight', ''),
]
DIV_KW = [('atom', 'อะตอม'), ('straw', 'สตรอว์'), ('fly', 'ฟลาย'), ('bantam', 'แบนตัม'),
          ('feather', 'เฟเธอร์'), ('welter', 'เวลเทอร์'), ('middle', 'มิดเดิล'), ('catch', 'แคช'),
          ('light', 'ไล'), ('heavy', 'เฮฟวี')]


def div_key(d):
    s = str(d or '')
    if not s:
        return None
    if 'เฮฟวี' in s and ('ไลท์เฮฟวี' in s or 'ไลต์เฮฟวี' in s):
        return 'lightheavy'
    for k, kw in DIV_KW:
        if kw in s:
            return k
    return None


def div_file(en):
    return 'rankings-%s.html' % en.lower().replace(' ', '-')


# ═══════════════════════════════════════════════════════════════════
# อ่านข้อมูล (fighters_data.js) — ใช้ทำ sitemap และหาว่ามีรุ่นไหนบ้าง
# ═══════════════════════════════════════════════════════════════════
def extract_js_const(text, name):
    m = re.search(r'(?:const|var|let)\s+' + re.escape(name) + r'\s*=\s*', text)
    if not m:
        return None
    i = m.end()
    while i < len(text) and text[i].isspace():
        i += 1
    if i >= len(text) or text[i] not in '[{':
        return None
    open_ch = text[i]
    close_ch = ']' if open_ch == '[' else '}'
    start, depth, in_str, escaped = i, 0, False, False
    while i < len(text):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
        i += 1
    return None


def load_data():
    if not DATA.exists():
        sys.exit('✗ ไม่พบ %s — วาง build_seo.py ไว้ที่โฟลเดอร์รากของเว็บ (ที่มี index.html)' % DATA)
    text = DATA.read_text(encoding='utf-8-sig')
    fighters = extract_js_const(text, 'FIGHTERS') or []
    history = extract_js_const(text, 'HISTORY') or []
    meta = extract_js_const(text, 'META') or {}
    return fighters, history, meta


# ═══════════════════════════════════════════════════════════════════
# ตัวอ่าน HTML แบบง่าย — หา element ตาม id โดยข้ามเนื้อหาใน <script>/<style>
# (โค้ด JS ในหน้ามีสตริงอย่าง '<tr ...>' '</tbody>' เยอะ จึงต้องข้ามให้ถูก)
# ═══════════════════════════════════════════════════════════════════
_TAG = re.compile(r'<!--.*?-->|<(/?)([a-zA-Z][a-zA-Z0-9-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>', re.S)
_RAW = {'script', 'style', 'textarea', 'title', 'noscript'}
_VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source',
         'track', 'wbr', 'param'}


def _tokens(doc):
    """คืน list ของ (start, end, is_close, tagname, attrs) — ข้ามคอมเมนต์และเนื้อหา raw"""
    out, pos = [], 0
    while True:
        m = _TAG.search(doc, pos)
        if not m:
            return out
        if m.group(0).startswith('<!--'):
            pos = m.end()
            continue
        close, name, attrs = m.group(1) == '/', m.group(2).lower(), m.group(3)
        out.append((m.start(), m.end(), close, name, attrs))
        pos = m.end()
        if not close and name in _RAW and not attrs.rstrip().endswith('/'):
            end = re.compile(r'</%s\s*>' % name, re.I).search(doc, pos)
            if not end:
                return out
            out.append((end.start(), end.end(), True, name, ''))
            pos = end.end()


def inner_span(doc, elid):
    """ตำแหน่ง (เริ่ม, จบ) ของเนื้อหาข้างใน element ที่มี id=elid หรือ None"""
    toks = _tokens(doc)
    idre = re.compile(r'\bid\s*=\s*(["\'])%s\1' % re.escape(elid))
    for i, (s, e, close, name, attrs) in enumerate(toks):
        if close or not idre.search(attrs):
            continue
        if name in _VOID:
            return None
        depth = 1
        for s2, e2, close2, name2, _ in toks[i + 1:]:
            if name2 != name:
                continue
            if close2:
                depth -= 1
                if depth == 0:
                    return (e, s2)
            elif name not in _RAW:
                depth += 1
        return None
    return None


def mark_span(doc, name):
    a, b = '<!--PR:%s-->' % name, '<!--/PR:%s-->' % name
    i = doc.find(a)
    if i < 0:
        return None
    j = doc.find(b, i)
    return (i + len(a), j) if j >= 0 else None


# ═══════════════════════════════════════════════════════════════════
# เบราว์เซอร์ headless
# ═══════════════════════════════════════════════════════════════════
def find_browser():
    env = os.environ.get('BOXFAN_BROWSER')
    if env and Path(env).exists():
        return env
    cands = []
    for base in (os.environ.get('PROGRAMFILES'), os.environ.get('PROGRAMFILES(X86)'), os.environ.get('LOCALAPPDATA')):
        if base:
            cands += [Path(base) / 'Google/Chrome/Application/chrome.exe',
                      Path(base) / 'Microsoft/Edge/Application/msedge.exe',
                      Path(base) / 'Chromium/Application/chrome.exe']
    cands += [Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
              Path('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge')]
    for c in cands:
        if c.exists():
            return str(c)
    for n in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome', 'msedge',
              'microsoft-edge'):
        p = shutil.which(n)
        if p:
            return p
    return None


def dump_dom(browser, page_path):
    """เปิดหน้าใน headless browser แล้วคืน HTML หลัง JS ทำงานเสร็จ"""
    url = page_path.resolve().as_uri()
    prof = tempfile.mkdtemp(prefix='boxfan-pr-')   # โปรไฟล์ชั่วคราว — ไม่ชนกับ Chrome ที่เปิดอยู่
    cmd = [browser, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
           '--disable-extensions', '--hide-scrollbars', '--mute-audio', '--user-data-dir=' + prof,
           '--virtual-time-budget=%d' % WAIT_MS, '--dump-dom', url]
    if os.name != 'nt' and hasattr(os, 'geteuid') and os.geteuid() == 0:
        cmd.insert(1, '--no-sandbox')
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        return r.stdout.decode('utf-8', errors='replace')
    finally:
        shutil.rmtree(prof, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════
# อ่าน/เขียนไฟล์ — คงรูปแบบขึ้นบรรทัด (CRLF ของ Windows) ตามไฟล์เดิม
# ═══════════════════════════════════════════════════════════════════
def read(p):
    raw = p.read_bytes().decode('utf-8-sig')
    crlf = raw.count('\r\n') > raw.count('\n') / 2
    return raw.replace('\r\n', '\n'), crlf


def write(p, text, crlf):
    if crlf:
        text = text.replace('\n', '\r\n')
    p.write_bytes(text.encode('utf-8'))


# ═══════════════════════════════════════════════════════════════════
# หน้าอันดับแยกรุ่นน้ำหนัก (สร้างจากแม่แบบ weight-classes.html)
# ═══════════════════════════════════════════════════════════════════
def set_head(doc, title=None, desc=None, url=None, keywords=None):
    """เปลี่ยนค่าใน <head> ของแม่แบบให้เป็นของหน้านี้"""
    def sub_attr(d, pat, val):
        return re.sub(pat, lambda m: m.group(1) + H.escape(val, quote=True) + m.group(2), d, count=1)
    if title:
        doc = re.sub(r'<title>.*?</title>', '<title>%s</title>' % H.escape(title, quote=False), doc, count=1, flags=re.S)
        doc = sub_attr(doc, r'(<meta property="og:title" content=")[^"]*(">)', title)
        doc = sub_attr(doc, r'(<meta name="twitter:title" content=")[^"]*(">)', title)
    if desc:
        doc = sub_attr(doc, r'(<meta name="description" content=")[^"]*(">)', desc)
        doc = sub_attr(doc, r'(<meta property="og:description" content=")[^"]*(">)', desc)
        doc = sub_attr(doc, r'(<meta name="twitter:description" content=")[^"]*(">)', desc)
    if url:
        doc = sub_attr(doc, r'(<link rel="canonical" href=")[^"]*(">)', url)
        doc = sub_attr(doc, r'(<meta property="og:url" content=")[^"]*(">)', url)
    if keywords:
        doc = sub_attr(doc, r'(<meta name="keywords" content=")[^"]*(">)', keywords)
    return doc


def make_division_pages(fighters):
    tpl_path = ROOT / 'weight-classes.html'
    tpl, crlf = read(tpl_path)
    counts = {}
    for f in fighters:
        k = div_key(f.get('division'))
        if k:
            counts[k] = counts.get(k, 0) + 1
    made = []
    for key, th, en, rng in DIV_MAP:
        if not counts.get(key):
            continue
        fn = div_file(en)
        url = '%s/%s' % (SITE, fn)
        short = th[:-3] if th.endswith('เวท') else th
        title = 'อันดับนักมวย%s (%s) — จัดอันดับรุ่น%s ONE มวยไทย ล่าสุด | Boxfan' % (th, en, short)
        desc = ('อันดับนักมวยรุ่น%s (%s%s) คำนวณจากผลการแข่งขันจริง ชนะ +3 เสมอ 0 แพ้ -3 นับเฉพาะไฟต์ในรุ่นนี้ '
                'กรองตามศึก ปี ประเทศ และค่ายมวยได้ อัปเดตหลังทุกไฟต์' % (th, en, (' ' + rng) if rng else ''))
        kw = 'อันดับนักมวย%s,นักมวย%s,%s,รุ่น%s ONE,%s Muay Thai rankings,จัดอันดับนักมวย,Boxfan' % (th, th, th, th, en)
        doc = set_head(tpl, title, desc, url, kw)
        # breadcrumb ใน JSON-LD: หน้าแรก › รุ่นน้ำหนัก › รุ่นนี้
        doc = doc.replace(
            '{"@type":"ListItem","position":2,"name":"รุ่นน้ำหนัก","item":"%s/weight-classes.html"}]}' % SITE,
            '{"@type":"ListItem","position":2,"name":"รุ่นน้ำหนัก","item":"%s/weight-classes.html"},'
            '{"@type":"ListItem","position":3,"name":"%s","item":"%s"}]}' % (SITE, th, url), 1)
        doc = doc.replace('"@type":"CollectionPage","name":"รุ่นน้ำหนัก ONE มวยไทย","url":"%s/weight-classes.html"' % SITE,
                          '"@type":"CollectionPage","name":"อันดับนักมวย%s","url":"%s"' % (th, url), 1)
        # บอก JS ของหน้าว่าเป็นรุ่นไหน (แทน ?div=)
        mk = re.search(r'<script src="data/fighters_(?:data|lite)\.js"></script>', doc)
        if not mk:
            sys.exit('✗ weight-classes.html ไม่มี <script src="data/fighters_data.js"> — สร้างหน้าแยกรุ่นไม่ได้')
        doc = doc[:mk.start()] + '<script>window.BF_DIV=%s;</script>\n' % json.dumps(key) + doc[mk.start():]
        out = ROOT / fn
        old_crlf = read(out)[1] if out.exists() else crlf
        write(out, doc, old_crlf)
        made.append((fn, key, th, en))
    return made


# ═══════════════════════════════════════════════════════════════════
# prerender หนึ่งหน้า
# ═══════════════════════════════════════════════════════════════════
def prerender(browser, rel, spec):
    path = ROOT / rel
    if not path.exists():
        return rel, None, ['ไม่พบไฟล์']
    src, crlf = read(path)
    # ครั้งแรก: ครอบช่องเมนู/ท้ายเว็บด้วยคอมเมนต์ PR (boxfan-shared.js จะเติม marker ให้เองตอนรัน)
    dom = dump_dom(browser, path)
    if '</html>' not in dom or len(dom) < 1000:
        return rel, None, ['เบราว์เซอร์ไม่ส่งผลลัพธ์กลับมา']
    warn, filled = [], 0

    for name in spec.get('marks', []):
        got = mark_span(dom, name)
        if not got:
            warn.append('ไม่พบช่วง PR:%s ในหน้าที่รันแล้ว' % name)
            continue
        content = dom[got[0]:got[1]]
        mine = mark_span(src, name)
        if mine:
            src = src[:mine[0]] + content + src[mine[1]:]
        else:
            slot = {'chrome': '<div id="bf-chrome"></div>', 'foot': '<div id="bf-foot"></div>'}.get(name)
            if slot and slot in src:
                src = src.replace(slot, '<!--PR:%s-->%s<!--/PR:%s-->' % (name, content, name), 1)
            else:
                warn.append('ไม่พบที่วาง PR:%s ในไฟล์ต้นฉบับ' % name)
                continue
        filled += 1

    for elid in spec.get('ids', []) + spec.get('head', []):
        got = inner_span(dom, elid)
        if not got:
            warn.append('ไม่พบ #%s ในหน้าที่รันแล้ว' % elid)
            continue
        content = dom[got[0]:got[1]]
        mine = inner_span(src, elid)
        if not mine and elid in spec.get('head', []) and '</head>' in src:
            # ยังไม่มีที่วาง JSON-LD ในไฟล์ → เพิ่มก่อน </head>
            i = src.index('</head>')
            src = src[:i] + '<script type="application/ld+json" id="%s"></script>\n' % elid + src[i:]
            mine = inner_span(src, elid)
        if not mine:
            warn.append('ไม่พบ #%s ในไฟล์ต้นฉบับ' % elid)
            continue
        if elid in spec.get('head', []):
            content = content.strip()
            if content:
                try:
                    json.loads(content)
                except ValueError:
                    warn.append('JSON-LD #%s อ่านไม่ได้ — ข้าม' % elid)
                    continue
        elif not content.strip():
            warn.append('#%s ว่างเปล่า' % elid)
        src = src[:mine[0]] + content + src[mine[1]:]
        filled += 1

    # ช่อง JSON-LD ที่ยังว่าง (เช่น ไม่มีข้อมูล) → ลบทิ้ง กัน Search Console แจ้ง error
    src = re.sub(r'<script type="application/ld\+json" id="[^"]+"></script>\n?', '', src)
    write(path, src, crlf)
    return rel, (src, dom), warn


# ═══════════════════════════════════════════════════════════════════
# sitemap.xml + robots.txt
# ═══════════════════════════════════════════════════════════════════
MAIN_PAGES = ['', 'rankings.html', 'weight-classes.html', 'fighters.html', 'schedule.html', 'results.html',
              'compare.html', 'stats.html', 'tierlist.html', 'ranking.html', 'my-ranking.html', 'bracket.html',
              'RankingMuay.html', 'blog/', 'about.html', 'contact.html', 'privacy.html', 'disclaimer.html']


def is_noindex(p):
    try:
        head = p.read_text(encoding='utf-8-sig', errors='replace')[:20000]
    except OSError:
        return True
    return bool(re.search(r'<meta name="robots" content="[^"]*noindex', head))


def build_sitemap(fighters, history, meta, div_pages):
    gen = str(meta.get('generated_at') or date.today().isoformat())[:10]
    today = date.today().isoformat()
    gen = min(gen, today)
    urls = []

    def add(loc, lastmod):
        urls.append('  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (H.escape(loc), lastmod))

    for rel in MAIN_PAGES:
        p = ROOT / (rel or 'index.html') if not rel.endswith('/') else ROOT / rel / 'index.html'
        if p.exists() and not is_noindex(p):
            add('%s/%s' % (SITE, rel), gen)
    for fn, *_ in div_pages:
        add('%s/%s' % (SITE, fn), gen)

    # บทความ: เอาวันที่จาก blog/articles.js ถ้ามี
    art_dates = {}
    aj = ROOT / 'blog' / 'articles.js'
    if aj.exists():
        t = aj.read_text(encoding='utf-8-sig')
        for m in re.finditer(r"file\s*:\s*'([^']+)'[^}]*?date\s*:\s*'(\d{4}-\d{2}-\d{2})'", t, re.S):
            art_dates[m.group(1)] = m.group(2)
    adir = ROOT / 'blog' / 'articles'
    n_art = 0
    if adir.exists():
        for p in sorted(adir.rglob('*.html')):
            rel = p.relative_to(ROOT / 'blog').as_posix()
            if is_noindex(p):
                continue
            add('%s/blog/%s' % (SITE, rel), min(art_dates.get(rel, gen), today))
            n_art += 1

    # โปรไฟล์นักมวย: lastmod = วันที่ไฟต์ล่าสุดของคนนั้น (ไม่เกินวันที่อัปเดตข้อมูล)
    last = {}
    for h in history:
        d = str(h.get('date') or '')[:10]
        fid = h.get('fighter_id')
        if d and fid and d > last.get(fid, ''):
            last[fid] = d
    fdir = ROOT / 'fighters'
    n_f = 0
    from urllib.parse import quote
    for f in sorted(fighters, key=lambda x: x.get('slug') or ''):
        slug = f.get('slug')
        if not slug or not (fdir / (slug + '.html')).exists():
            continue
        lm = min(last.get(f.get('id'), gen) or gen, gen)
        add('%s/fighters/%s.html' % (SITE, quote(slug, safe='-._~')), lm)
        n_f += 1

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % '\n'.join(urls))
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')
    return len(urls), n_art, n_f


ROBOTS = """User-agent: *
Allow: /

# เครื่องมือภายใน / ไฟล์แม่แบบ — ไม่ต้องให้ค้นหาเจอ
Disallow: /db-extractor.html
Disallow: /generate-sitemap.html
Disallow: /blog/TEMPLATE.html
Disallow: /blog/index-blog.html
Disallow: /data/fighters.db
Disallow: /*.py$
Disallow: /*.bat$

Sitemap: %s/sitemap.xml
""" % SITE


# ═══════════════════════════════════════════════════════════════════
def main():
    os.chdir(ROOT)
    print('BOXFAN — build_seo.py')
    browser = find_browser()
    if not browser:
        sys.exit('✗ ไม่พบ Chrome หรือ Microsoft Edge\n'
                 '  ติดตั้ง Chrome หรือกำหนดตัวแปร BOXFAN_BROWSER ให้ชี้ไปที่ chrome.exe / msedge.exe')
    print('  เบราว์เซอร์:', browser)

    fighters, history, meta = load_data()
    print('  ข้อมูล: %d นักมวย · %d ไฟต์ · อัปเดต %s' % (len(fighters), len(history), meta.get('generated_at', '?')))

    divs = make_division_pages(fighters)
    print('  สร้างหน้าแยกรุ่น %d หน้า: %s' % (len(divs), ', '.join(d[0] for d in divs)))

    jobs = dict(PAGES)
    for fn, *_ in divs:
        jobs[fn] = DIV_PAGE_SPEC
    print('  กำลัง prerender %d หน้า (ประมาณ %d วินาที)...' % (len(jobs), len(jobs) * 4 // PARALLEL + 5))
    ok = True
    with ThreadPoolExecutor(max_workers=PARALLEL) as ex:
        results = list(ex.map(lambda kv: prerender(browser, kv[0], kv[1]), jobs.items()))
    for rel, res, warn in results:
        if res is None:
            ok = False
            print('  ✗ %-28s %s' % (rel, '; '.join(warn)))
        else:
            src = res[0]
            words = len(re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', src, flags=re.S)).split())
            print('  ✓ %-28s เนื้อหาในไฟล์ ~%d คำ%s' % (rel, words, ('  ⚠ ' + '; '.join(warn)) if warn else ''))

    # คำอธิบายหน้าแยกรุ่น: ใส่ชื่อ 3 อันดับแรก (ช่วยให้คนคลิกจากผลค้นหา)
    for fn, key, th, en in divs:
        p = ROOT / fn
        doc, crlf = read(p)
        sp = inner_span(doc, 'wc-rows')
        names = re.findall(r'class="fighter-name"><a [^>]*>([^<]+)</a>', doc[sp[0]:sp[1]])[:3] if sp else []
        if names:
            m = re.search(r'<meta name="description" content="([^"]*)">', doc)
            base = H.unescape(m.group(1)).split(' · อันดับ 1–3:')[0]
            desc = '%s · อันดับ 1–3: %s' % (base, ', '.join(H.unescape(n) for n in names))
            write(p, set_head(doc, desc=desc), crlf)

    n, n_art, n_f = build_sitemap(fighters, history, meta, divs)
    print('  ✓ sitemap.xml — %d URL (บทความ %d · โปรไฟล์นักมวย %d)' % (n, n_art, n_f))
    (ROOT / 'robots.txt').write_text(ROBOTS, encoding='utf-8')
    print('  ✓ robots.txt')
    if not ok:
        sys.exit('\n✗ มีบางหน้าทำไม่สำเร็จ — ดูข้อความด้านบน')
    print('\nเสร็จแล้ว ✓  ตรวจหน้าเว็บในเครื่องแล้ว push ขึ้นเว็บได้เลย')


if __name__ == '__main__':
    main()
