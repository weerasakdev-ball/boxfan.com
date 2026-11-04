#!/usr/bin/env python3
"""
build_chrome.py — ใส่ "เมนูบน + ท้ายเว็บ + ธีม" แบบเดียวกันให้ทุกหน้า

แก้เมนู/ท้ายเว็บ ให้แก้ที่ไฟล์นี้ที่เดียว แล้วรัน generate_profiles.bat (เรียกให้เอง)
  - HEAD   = ฟอนต์ + site.css + site.js          → ใส่ก่อน </head>
  - HEADER = เมนูบน + เมนูมือถือ                 → ใส่ต่อจาก <body ...>
  - FOOTER = ท้ายเว็บ                             → ใส่ก่อน </body>
ครอบด้วย <!--BF:ชื่อ--> … <!--/BF:ชื่อ--> รันซ้ำได้ไม่จำกัด (แทนที่ของเดิม)
หน้านักมวย (fighters/*.html) ใช้ฟังก์ชันในไฟล์นี้ผ่าน data/generate_profiles.py
ลิงก์ทั้งหมดขึ้นต้นด้วย / (ใช้ได้ทุกระดับโฟลเดอร์)
"""

import re
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
VER = '3'   # เปลี่ยนเลขเมื่อแก้ site.css / site.js (ให้ผู้ใช้เก่าโหลดไฟล์ใหม่)


# ═══ โฆษณา Google AdSense ═══
# เจ้าของวางรหัส (ca-pub-ตัวเลข 16 หลัก) ในไฟล์ adsense.txt แล้วกด generate_profiles.bat
#  → ใส่โค้ดโฆษณาอัตโนมัติ (Auto ads) ทุกหน้า + สร้าง ads.txt + เปิด CSP ให้โฆษณาแสดงได้
#  ไม่มีรหัส/ไฟล์ว่าง = ไม่ใส่โฆษณา (เว็บทำงานปกติ)
def read_adsense():
    try:
        txt = (ROOT / 'adsense.txt').read_text(encoding='utf-8-sig')
    except OSError:
        return ''
    txt = '\n'.join(l for l in txt.splitlines() if not l.strip().startswith('#'))   # ข้ามหมายเหตุ
    m = re.search(r'ca-pub-(\d{16})', txt) or re.search(r'pub-(\d{16})', txt)
    return ('ca-pub-' + m.group(1)) if m else ''


ADSENSE = read_adsense()
AD_HOSTS = {
    'script-src': ['https://pagead2.googlesyndication.com', 'https://*.googlesyndication.com', 'https://*.google.com',
                   'https://*.googleadservices.com', 'https://*.doubleclick.net', 'https://*.gstatic.com',
                   'https://fundingchoicesmessages.google.com'],
    'connect-src': ['https://*.googlesyndication.com', 'https://*.google.com', 'https://*.doubleclick.net',
                    'https://*.googleadservices.com', 'https://fundingchoicesmessages.google.com'],
    'frame-src': ['https://*.googlesyndication.com', 'https://*.doubleclick.net', 'https://*.google.com',
                  'https://www.youtube-nocookie.com'],
    'img-src': ['https:'],
}

# รุ่นน้ำหนัก — ต้องตรงกับ DIV_MAP ใน build_seo.py / utils.js
DIVS = [
    ('อะตอมเวท', 'atomweight'), ('สตรอว์เวท', 'strawweight'), ('ฟลายเวท', 'flyweight'),
    ('แบนตัมเวท', 'bantamweight'), ('เฟเธอร์เวท', 'featherweight'), ('ไลท์เวท', 'lightweight'),
    ('เวลเทอร์เวท', 'welterweight'), ('มิดเดิลเวท', 'middleweight'), ('ไลท์เฮฟวีเวท', 'light-heavyweight'),
    ('เฮฟวีเวท', 'heavyweight'), ('แคชเวท', 'catchweight'),
]

# เมนู: (หัวข้อ, กลุ่ม, [(ลิงก์, ชื่อ, คำอธิบาย)])
MENU = [
    ('อันดับ', 'rank', [
        ('/rankings.html', 'อันดับรวมทุกรุ่น', 'ตารางคะแนนสะสม pound for pound'),
        ('/weight-classes.html', 'อันดับแยกรุ่นน้ำหนัก', 'แชมป์และท็อปของแต่ละรุ่น'),
        ('/RankingMuay.html', 'อันดับแบบกำหนดเอง', 'กรองตามศึก ปี รุ่น อายุ'),
    ]),
    ('นักมวย', 'fighters', [
        ('/fighters.html', 'รายชื่อนักมวย', 'ค้นหาประวัติและสถิติทุกคน'),
        ('/stats.html', 'สถิตินักมวย', 'จัดอันดับได้ทุกสถิติ'),
        ('/compare.html', 'เปรียบเทียบนักมวย', 'เทียบตัวต่อตัวก่อนชก'),
    ]),
    ('ไฟต์', 'fights', [
        ('/schedule.html', 'วิเคราะห์มวยวันนี้', 'โปรแกรมชกและวิเคราะห์คู่มวย'),
        ('/results.html', 'ผลมวยล่าสุด', 'ผลการแข่งขันทุกไฟต์'),
        ('/events/', 'รวมศึกทั้งหมด', 'ผลมวยและคู่ชกครบทุกศึก'),
    ]),
    ('เล่นสนุก', 'play', [
        ('/tierlist.html', 'Tier List นักมวย', 'จัดระดับนักมวยในดวงใจ แชร์ได้'),
        ('/bracket.html', 'จัดสายมวย ทายผล', 'สร้างสายน็อกเอาท์ของคุณเอง'),
        ('/ranking.html', 'ทำตารางอันดับเอง', 'ลากวางเรียงอันดับ แคปแชร์'),
        ('/my-ranking.html', 'อันดับของฉัน', 'เลือกนักมวยแล้วจัดอันดับด้วยคะแนนจริง'),
    ]),
]

FOOT_COLS = [
    ('อันดับ', [('/rankings.html', 'อันดับรวมทุกรุ่น'), ('/weight-classes.html', 'อันดับแยกรุ่น'),
                ('/RankingMuay.html', 'อันดับแบบกำหนดเอง'), ('/tierlist.html', 'Tier List')]),
    ('นักมวยและไฟต์', [('/fighters.html', 'รายชื่อนักมวย'), ('/stats.html', 'สถิตินักมวย'),
                      ('/compare.html', 'เปรียบเทียบนักมวย'), ('/schedule.html', 'วิเคราะห์มวยวันนี้'),
                      ('/results.html', 'ผลมวยล่าสุด'), ('/events/', 'รวมศึกทั้งหมด')]),
    ('อ่านเพิ่ม', [('/blog/', 'บทความ'), ('/bracket.html', 'จัดสายมวย'), ('/my-ranking.html', 'อันดับของฉัน')]),
    ('เกี่ยวกับ', [('/about.html', 'เกี่ยวกับเรา'), ('/contact.html', 'ติดต่อเรา'),
                   ('/privacy.html', 'นโยบายความเป็นส่วนตัว'), ('/disclaimer.html', 'ข้อจำกัดความรับผิด')]),
]

# ลิงก์คำค้นยอดนิยม (ช่วย SEO ภายในเว็บ)
FOOT_TAGS = [
    ('/schedule.html', 'วิเคราะห์มวยวันนี้'), ('/schedule.html', 'โปรแกรมมวยวันนี้'),
    ('/results.html', 'ผลมวยล่าสุด'), ('/events/', 'ผลมวย ONE ลุมพินี'),
    ('/rankings.html', 'อันดับนักมวย ONE'), ('/rankings.html', 'pound for pound มวยไทย'),
    ('/weight-classes.html', 'แชมป์โลก ONE มวยไทย'), ('/fighters.html', 'ประวัตินักมวย'),
    ('/stats.html', 'สถิตินักมวยไทย'), ('/compare.html', 'เปรียบเทียบนักมวย'),
    ('/', 'จัดอันดับนักมวยไทย'), ('/blog/', 'บทความมวยไทย'),
]

CARET = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
ICON_SEARCH = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>'
ICON_MENU = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>'
ICON_X = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>'

LOGO = ('<a class="bf-logo" href="/" aria-label="Boxfan หน้าแรก">'
        '<img class="bf-logo-mark" src="/images/logo-96.png" width="36" height="36" alt="Boxfan">'
        '<span class="bf-logo-txt"><b>BOX<i>FAN</i></b><small>สถิติ · อันดับ · ผลมวย</small></span></a>')


def head_html():
    return ('<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800'
            '&family=Noto+Sans+Thai:wght@400;500;600;700;800&display=swap">'
            '<link rel="stylesheet" href="/site.css?v=%s">'
            '<script src="/site.js?v=%s"></script>' % (VER, VER)
            + (('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=%s" '
                'crossorigin="anonymous"></script>' % ADSENSE) if ADSENSE else ''))


def header_html():
    nav = ['<a href="/">หน้าแรก</a>']
    for title, g, items in MENU:
        links = ''.join('<a href="%s"><b>%s</b><span>%s</span></a>' % it for it in items)
        if g == 'rank':
            links += ('<div class="bf-dd-sep"></div><div class="bf-dd-hd">แยกตามรุ่น</div><div class="bf-dd-grid">'
                      + ''.join('<a href="/rankings-%s.html">%s</a>' % (en, th) for th, en in DIVS) + '</div>')
        nav.append('<div class="bf-dd" data-g="%s"><button type="button" class="bf-dd-btn" aria-expanded="false">%s%s</button>'
                   '<div class="bf-dd-menu%s">%s</div></div>' % (g, title, CARET, ' wide' if g == 'rank' else '', links))
    nav.append('<a href="/blog/">บทความ</a>')

    drawer = ['<div class="bf-drawer-sec"><a href="/">หน้าแรก</a><a href="/blog/">บทความ</a></div>']
    for title, g, items in MENU:
        body = ''.join('<a href="%s">%s</a>' % (h, n) for h, n, _ in items)
        if g == 'rank':
            body += ('<h4 style="margin-top:8px">แยกตามรุ่น</h4><div class="bf-drawer-divs">'
                     + ''.join('<a href="/rankings-%s.html">%s</a>' % (en, th) for th, en in DIVS) + '</div>')
        drawer.append('<div class="bf-drawer-sec"><h4>%s</h4>%s</div>' % (title, body))
    drawer.append('<div class="bf-drawer-sec"><h4>เกี่ยวกับ</h4><a href="/about.html">เกี่ยวกับเรา</a>'
                  '<a href="/contact.html">ติดต่อเรา</a></div>')

    return (
        '<a class="bf-skip" href="#bf-main">ข้ามไปเนื้อหา</a>'
        '<header class="bf-hdr" id="bf-hdr"><div class="bf-hdr-in">' + LOGO +
        '<nav class="bf-nav" aria-label="เมนูหลัก">' + ''.join(nav) + '</nav>'
        '<form class="bf-search" action="/fighters.html" method="get" role="search">' + ICON_SEARCH +
        '<input type="search" name="q" placeholder="ค้นหานักมวย…" autocomplete="off" aria-label="ค้นหานักมวย">'
        '<button type="button" class="bf-icon-btn bf-search-open" aria-label="ค้นหา">' + ICON_SEARCH + '</button>'
        '<div class="bf-sdrop"></div></form>'
        '<button type="button" class="bf-icon-btn" id="bf-menu-btn" aria-label="เปิดเมนู">' + ICON_MENU + '</button>'
        '</div></header>'
        '<div class="bf-drawer" id="bf-drawer"><div class="bf-drawer-bg" data-bf-close></div>'
        '<div class="bf-drawer-panel" role="dialog" aria-label="เมนู"><div class="bf-drawer-hd">' + LOGO +
        '<button type="button" class="bf-icon-btn" style="display:flex" data-bf-close aria-label="ปิดเมนู">' + ICON_X + '</button></div>'
        + ''.join(drawer) + '</div></div>'
        '<span id="bf-main"></span>'
    )


def footer_html():
    cols = ''.join('<div><h5>%s</h5><ul>%s</ul></div>' % (t, ''.join('<li><a href="%s">%s</a></li>' % l for l in links))
                   for t, links in FOOT_COLS)
    tags = ''.join('<a href="%s">%s</a>' % t for t in FOOT_TAGS)
    return (
        '<footer class="bf-foot"><div class="bf-foot-in"><div class="bf-foot-grid">'
        '<div class="bf-foot-brand">' + LOGO +
        '<p>ฐานข้อมูลนักมวยไทย ONE Championship และ MMA — อันดับ สถิติ ผลมวย และวิเคราะห์คู่มวย '
        'คำนวณจากผลการแข่งขันจริง อัปเดตทุกสัปดาห์</p></div>' + cols + '</div>'
        '<nav class="bf-foot-tags" aria-label="หัวข้อยอดนิยม">' + tags + '</nav>'
        '<div class="bf-foot-bot"><span>© %d Boxfan · boxingfandom.com</span>'
        '<span>ข้อมูลเพื่อความบันเทิงและการศึกษา ไม่ใช่การพนัน</span></div>'
        '</div></footer>' % date.today().year
    )


UMAMI = ('<script defer src="https://cloud.umami.is/script.js" '
         'data-website-id="40ec0b51-4f08-45be-801d-9cf01fc79260"></script>')
UMAMI_HOSTS = ['https://cloud.umami.is', 'https://gateway.umami.is', 'https://api-gateway.umami.dev']


def block(name, html):
    return '<!--BF:%s-->%s<!--/BF:%s-->' % (name, html, name)


def fix_csp(text):
    """ให้ CSP ของหน้าอนุญาตตัวนับผู้เข้าชม (Umami) — เดิมบล็อกการส่งข้อมูล ทำให้นับคนเข้าไม่ได้"""
    def fix(m):
        pol = m.group(2)
        ds = [d.strip() for d in pol.split(';') if d.strip()]
        out, seen = [], set()
        for d in ds:
            name = d.split()[0]
            seen.add(name)
            if name in ('script-src', 'connect-src'):
                need = UMAMI_HOSTS[:1] if name == 'script-src' else UMAMI_HOSTS
                for h in need:
                    if h not in d.split():
                        d += ' ' + h
            if ADSENSE and name in AD_HOSTS:
                for h in AD_HOSTS[name]:
                    if h not in d.split():
                        d += ' ' + h
            out.append(d)
        if 'connect-src' not in seen:
            out.append("connect-src 'self' " + ' '.join(UMAMI_HOSTS + (AD_HOSTS['connect-src'] if ADSENSE else [])))
        if ADSENSE and 'frame-src' not in seen:
            out.append("frame-src 'self' " + ' '.join(AD_HOSTS['frame-src']))
        return m.group(1) + '; '.join(out) + ';' + m.group(3)
    return re.sub(r'(<meta http-equiv="Content-Security-Policy" content=")([^"]*)(")', fix, text, count=1)


def apply(text):
    """ใส่/แทนที่ HEAD, HEADER, FOOTER และเติม class="bf" ที่ <html> — คืนข้อความใหม่"""
    # หน้าแบบหน้าแรก (สีทองเป็นสีหลัก) → เปลี่ยนสีทองเป็นสีหลักของธีมใหม่
    skin = 'a' if '--gold-light' in re.sub(r'<!--BF:.*?<!--/BF:[a-z]+-->', '', text, flags=re.S) else ''
    outside = re.sub(r'<!--BF:head-->.*?<!--/BF:head-->', '', text, flags=re.S)
    head = head_html() + ('' if 'cloud.umami.is/script.js' in outside else UMAMI)
    text = fix_csp(text)
    parts = {'head': head, 'header': header_html(), 'footer': footer_html()}
    for name, html in parts.items():
        pat = re.compile(r'<!--BF:%s-->.*?<!--/BF:%s-->' % (name, name), re.S)
        if pat.search(text):
            text = pat.sub(lambda m: block(name, html), text, count=1)
            continue
        if name == 'head':
            i = text.lower().find('</head>')
        elif name == 'header':
            m = re.search(r'<body\b[^>]*>', text, re.I)
            i = m.end() if m else -1
        else:
            i = text.lower().rfind('</body>')
        if i < 0:
            raise ValueError('ไม่พบตำแหน่งใส่ %s' % name)
        text = text[:i] + block(name, html) + text[i:]
    # class="bf" ที่ <html> (กันหน้ากระพริบก่อน site.js ทำงาน)
    m = re.search(r'<html\b[^>]*>', text, re.I)
    if m and not re.search(r'\bclass="[^"]*\bbf\b', m.group(0)):
        tag = m.group(0)
        if 'class="' in tag:
            new = tag.replace('class="', 'class="bf ', 1)
        else:
            new = tag[:-1] + ' class="bf">'
        text = text[:m.start()] + new + text[m.end():]
    if skin:
        m = re.search(r'<html\b[^>]*>', text, re.I)
        if m and 'data-skin=' not in m.group(0):
            text = text[:m.end() - 1] + ' data-skin="%s">' % skin + text[m.end():]
    return text


def write_file(p, data):
    """เขียนไฟล์ — Windows บางครั้งล็อกไฟล์ชั่วคราว (สแกนไวรัส/เปิดดูอยู่) → รอแล้วลองใหม่"""
    import time
    for attempt in range(10):
        try:
            Path(p).write_bytes(data)
            return
        except OSError:
            if attempt == 9:
                raise
            time.sleep(1)


def pages():
    names = ['index.html', 'weight-classes.html', 'rankings.html', 'fighters.html', 'results.html', 'schedule.html',
             'compare.html', 'stats.html', 'tierlist.html', 'ranking.html', 'my-ranking.html', 'bracket.html',
             'RankingMuay.html', 'profile.html', 'about.html', 'contact.html', 'privacy.html', 'disclaimer.html',
             '404.html', 'blog/index.html', 'blog/TEMPLATE.html']
    out = [ROOT / n for n in names]
    out += sorted(ROOT.glob('rankings-*.html'))
    out += sorted((ROOT / 'blog' / 'articles').rglob('*.html'))
    return [p for p in out if p.exists()]


def main():
    n = 0
    for p in pages():
        raw = p.read_bytes().decode('utf-8-sig')
        crlf = raw.count('\r\n') > raw.count('\n') / 2
        text = raw.replace('\r\n', '\n')
        new = apply(text)
        if crlf:
            new = new.replace('\n', '\r\n')
        if new != raw:
            write_file(p, new.encode('utf-8'))
        n += 1
    print('  ✓ ใส่เมนู/ท้ายเว็บ/ธีมแบบเดียวกันให้ %d หน้า' % n)
    if ADSENSE:
        # ads.txt — Google ใช้ยืนยันว่าเว็บนี้อนุญาตให้บัญชีนี้ขายโฆษณา
        line = 'google.com, %s, DIRECT, f08c47fec0942fa0' % ADSENSE.replace('ca-', '') + chr(10)
        write_file(ROOT / 'ads.txt', line.encode('utf-8'))
        print('  ✓ โฆษณา AdSense เปิดแล้ว (%s) + ads.txt' % ADSENSE)
    else:
        print('  · ยังไม่ใส่โฆษณา (ยังไม่มีรหัสใน adsense.txt)')


if __name__ == '__main__':
    main()
