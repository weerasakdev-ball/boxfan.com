#!/usr/bin/env python3
"""
build_articles.py — แปลงบทความ Markdown (blog/source/*.md) เป็นหน้าบทความบนเว็บ

วิธีใช้ของเจ้าของ: วางไฟล์ .md ไว้ใน blog/source แล้วกด generate_profiles.bat
  - หัวไฟล์ (ไม่ใส่ก็ได้) ระหว่าง --- … ---  เช่น
        title: ชื่อบทความ
        excerpt: คำโปรย 1–2 บรรทัด
        cat: news | technique | gear
        author: ชื่อผู้เขียน
        date: 2026-11-04
        slug: ชื่อไฟล์ภาษาอังกฤษ (ไม่ใส่ = ใช้ชื่อไฟล์ .md)
        image: ลิงก์รูปปก (ไม่ใส่ = สร้างภาพปก Boxfan ให้เอง)
  - ได้หน้า blog/articles/th/<slug>.html (ธีมเดียวกับทั้งเว็บ) + สารบัญ + เวลาอ่าน + ข้อมูลให้ Google (Article)
  - ใส่ลงรายการบทความ blog/articles.js ให้เอง (ระหว่าง AUTO-ARTICLES) → ขึ้นหน้ารวมบทความ/หน้าแรก/sitemap
  - ตัวเลขอ้างอิงท้ายประโยค (เช่น …สิ้นเชิง1) กลายเป็นลิงก์ [1] ไปหาแหล่งอ้างอิงท้ายบท
เขียนเฉพาะไฟล์ที่เปลี่ยน
"""

import html as H
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import markdown  # pip install markdown

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import build_chrome  # noqa: E402

SRC = ROOT / 'blog' / 'source'
OUT = ROOT / 'blog' / 'articles' / 'th'
COVERS = ROOT / 'images' / 'blog'
SITE = 'https://www.boxingfandom.com'
CATS = {'news': 'ข่าวสาร / วิเคราะห์', 'technique': 'วิเคราะห์แทคติก', 'gear': 'รีวิวอุปกรณ์'}
TH_MONTHS = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']


def th_date(d):
    try:
        y, m, dd = [int(x) for x in str(d)[:10].split('-')]
        return '%d %s %d' % (dd, TH_MONTHS[m - 1], y + 543)
    except (ValueError, IndexError):
        return str(d)


def parse(path):
    text = path.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
    meta = {}
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip().lower()] = v.strip()
        text = text[m.end():]
    return meta, text


REF_HEAD = re.compile(r'^#{1,6}\s*\**\s*(ผลงานที่อ้างอิง|เอกสารอ้างอิง|แหล่งอ้างอิง|References)\s*\**\s*$', re.M)


def plain_line(s):
    s = s.strip()
    return bool(s) and not re.match(r'^([-*+]\s|\d+\.\s|\||>|#|!\[|\[(youtube|ยูทูป|คลิป)|https?://\S+$|---)', s, re.I)


def editor_paragraphs(text):
    """เครื่องมือเขียนบทความ: คนพิมพ์กด Enter ครั้งเดียวแล้วขึ้นย่อหน้าใหม่ → เติมบรรทัดว่างให้ Markdown เข้าใจ"""
    lines, out = text.split('\n'), []
    for i, ln in enumerate(lines):
        out.append(ln)
        if i + 1 < len(lines) and plain_line(ln) and plain_line(lines[i + 1]):
            out.append('')
    return '\n'.join(out)


def clean_md(text, meta):
    """เก็บกวาด Markdown ที่ส่งออกจาก Google Docs / เครื่องมือวิจัย"""
    if meta.get('editor') == '1':
        text = editor_paragraphs(text)
    lines = text.split('\n')
    out, h1_seen, sub = [], 0, ''
    for ln in lines:
        mh = re.match(r'^(#{1,6})\s+(.*)$', ln)
        if mh:
            level, title = mh.group(1), re.sub(r'\*\*|__', '', mh.group(2)).strip()
            if level == '#':
                h1_seen += 1
                if h1_seen == 2 and not sub:        # หัวข้อภาษาอังกฤษใต้ชื่อเรื่อง → คำบรรยายรอง
                    sub = title
                continue                           # ชื่อเรื่องใช้จาก meta (มี h1 เดียวต่อหน้า)
            if level == '####' and REF_HEAD.match('## ' + title):
                level = '##'
            ln = '%s %s' % (level, title)
        out.append(ln)
    text = '\n'.join(out)
    # ผู้วิจัย/ปีที่เผยแพร่ ซ้ำกับหัวบทความ → ตัดออก
    text = re.sub(r'^\*\*ผู้วิจัย:\*\*.*\n(\*\*ปีที่เผยแพร่:\*\*.*\n)?', '', text, flags=re.M)
    return text, sub


def link_footnotes(body_html, n_refs):
    """…สิ้นเชิง1  →  …สิ้นเชิง<sup><a href="#ref-1">1</a></sup> (เฉพาะเลขที่มีในรายการอ้างอิง)"""
    if not n_refs:
        return body_html

    def fix(m):
        nums = m.group(2).split(',')
        if not all(n.isdigit() and 1 <= int(n) <= n_refs for n in nums):
            return m.group(0)
        sup = ','.join('<a href="#ref-%s">%s</a>' % (n, n) for n in nums)
        return '%s<sup class="fn">%s</sup>' % (m.group(1), sup)
    parts = re.split(r'(<[^>]+>)', body_html)
    for i, p in enumerate(parts):
        if p.startswith('<'):
            continue
        parts[i] = re.sub(r'([\u0E00-\u0E7Fa-zA-Z\)”"%]|(?<!\d)\.)(\d{1,2}(?:,\d{1,2})*)(?=[\s:;,.\)]|$)', fix, p)
    return ''.join(parts)


YT_ID = re.compile(r'(?:youtu\.be/|youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/))([A-Za-z0-9_-]{11})')


def embed_media(md_text):
    """[youtube: ลิงก์]  หรือ ลิงก์ YouTube อยู่บรรทัดเดียว → คลิปฝัง (ภาพปก + กดแล้วเล่น)
    ![คำบรรยาย](ลิงก์รูป)  อยู่บรรทัดเดียว → รูป + คำบรรยายใต้รูป"""
    out = []
    for ln in md_text.split('\n'):
        s = ln.strip()
        m = re.match(r'^\[(?:youtube|ยูทูป|คลิป)\s*:\s*(\S+)\s*\]$', s, re.I) or \
            (re.match(r'^(https?://(?:www\.|m\.)?(?:youtube\.com|youtu\.be)/\S+)$', s))
        if m and YT_ID.search(m.group(1)):
            vid = YT_ID.search(m.group(1)).group(1)
            out.append('\n<figure class="ar-vid"><a class="ar-yt" href="https://www.youtube.com/watch?v=%s" data-yt="%s" '
                       'target="_blank" rel="noopener" aria-label="เล่นวิดีโอ"><img src="https://i.ytimg.com/vi/%s/hqdefault.jpg" '
                       'alt="วิดีโอ YouTube" loading="lazy"><span class="ar-play"></span></a>'
                       '<figcaption>วิดีโอจาก YouTube · ลิขสิทธิ์เป็นของเจ้าของคลิป · '
                       '<a href="https://www.youtube.com/watch?v=%s" target="_blank" rel="noopener">ดูบน YouTube</a></figcaption></figure>\n'
                       % (vid, vid, vid, vid))
            continue
        mi = re.match(r'^!\[([^\]]*)\]\((https?://[^)\s]+|/[^)\s]+)\)$', s)
        if mi:
            cap, src = mi.group(1).strip(), mi.group(2)
            out.append('\n<figure class="ar-img"><img src="%s" alt="%s" loading="lazy">%s</figure>\n'
                       % (H.escape(src, quote=True), H.escape(cap, quote=True),
                          ('<figcaption>%s</figcaption>' % H.escape(cap)) if cap else ''))
            continue
        out.append(ln)
    return '\n'.join(out)


VIDEO_JS = ('<script>document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest(".ar-yt");'
            'if(!a)return;e.preventDefault();var f=document.createElement("iframe");'
            'f.src="https://www.youtube-nocookie.com/embed/"+a.getAttribute("data-yt")+"?autoplay=1&rel=0";'
            'f.allow="autoplay; encrypted-media; picture-in-picture; fullscreen";f.allowFullscreen=true;'
            'f.className="ar-ifr";f.title="YouTube";a.replaceWith(f);});</script>')


def render(meta, text):
    md_text, subtitle = clean_md(text, meta)
    # แยกส่วนอ้างอิง (ท้ายบท)
    refs_md = ''
    mref = REF_HEAD.search(md_text)
    if mref:
        refs_md = md_text[mref.end():]
        md_text = md_text[:mref.start()]
    md_text = embed_media(md_text)
    md = markdown.Markdown(extensions=['tables', 'sane_lists'])
    body = md.convert(md_text)
    refs_html, n_refs = '', 0
    if refs_md.strip():
        items = re.findall(r'^>?\s*(\d+)\.\s+(.*)$', refs_md, re.M)
        if items:                                   # แบบมีเลข 1. 2. 3.
            n_refs = len(items)
            li = []
            for num, txt in items:
                txt = re.sub(r'\\([\\`*_{}\[\]()#+\-.!:|$])', r'\1', txt)   # ตัดเครื่องหมาย \ ที่ใช้ escape
                li.append('<li id="ref-%s">%s</li>' % (num, markdown.markdown(txt.strip()).replace('<p>', '').replace('</p>', '')))
            refs_html = '<ol class="refs">%s</ol>' % ''.join(li)
        else:                                       # แบบบรรณานุกรม (หัวข้อย่อย + รายการ)
            refs_html = '<div class="refs">%s</div>' % markdown.markdown(refs_md, extensions=['sane_lists'])
        refs_html = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="nofollow noopener"', refs_html)
    body = link_footnotes(body, n_refs)
    body = body.replace('**', '')                    # ตัวหนาที่ต้นฉบับเปิดไว้แต่ไม่ได้ปิด
    body = body.replace('\\~', '~').replace('\\&amp;', '&amp;')   # escape ที่ Markdown ไม่รู้จัก
    # หัวข้อ h2 ใส่ id + ทำสารบัญ
    toc = []

    def h2(m):
        i = len(toc) + 1
        title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        toc.append((i, title))
        return '<h2 id="s%d">%s</h2>' % (i, m.group(1))
    body = re.sub(r'<h2>(.*?)</h2>', h2, body, flags=re.S)
    body = re.sub(r'<table>', '<div class="tbl"><table>', body).replace('</table>', '</table></div>')
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    if refs_html:
        toc.append((len(toc) + 1, 'แหล่งอ้างอิง'))
        body += '<h2 id="s%d">แหล่งอ้างอิง</h2>%s' % (len(toc), refs_html)
    body = body.replace('\\&amp;', '&amp;')         # ลิงก์ในแหล่งอ้างอิงที่มี \& ค้าง
    plain = re.sub(r'<[^>]+>', ' ', body)
    minutes = max(1, round(len(re.sub(r'\s+', '', plain)) / 900))
    return body, toc, subtitle, minutes


def make_cover(slug, title, cat):
    """ภาพปก 1200x630 แบรนด์ Boxfan (ใช้เป็นรูปหน้าปก + ภาพตอนแชร์)"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return '/og-default.jpg'
    COVERS.mkdir(parents=True, exist_ok=True)
    out = COVERS / (slug + '.jpg')
    W, Hh = 1200, 630
    im = Image.new('RGB', (W, Hh), (15, 23, 42))
    d = ImageDraw.Draw(im)
    for y in range(Hh):                                     # ไล่สีจากเข้มไปแดงจาง ๆ
        r = int(15 + (227 - 15) * max(0, (y - 300)) / 330 * 0.35)
        d.line([(0, y), (W, y)], fill=(r, 23, 42))
    d.rectangle([0, 0, 14, Hh], fill=(227, 27, 35))
    fonts = [r'C:\Windows\Fonts\LeelaUIb.ttf', r'C:\Windows\Fonts\LeelawUI.ttf', r'C:\Windows\Fonts\tahomabd.ttf']
    fpath = next((f for f in fonts if Path(f).exists()), None)
    big = ImageFont.truetype(fpath, 58) if fpath else ImageFont.load_default()
    small = ImageFont.truetype(fpath, 30) if fpath else ImageFont.load_default()
    # ตัดบรรทัดชื่อเรื่องให้พอดีกว้าง
    words = re.split(r'(\s+)', title)
    lines, cur = [], ''
    for w in words:
        test = cur + w
        if d.textlength(test, font=big) > W - 160 and cur.strip():
            lines.append(cur.strip())
            cur = w.lstrip()
        else:
            cur = test
    if cur.strip():
        lines.append(cur.strip())
    lines = lines[:4]
    y = 120
    d.text((80, 70), CATS.get(cat, 'บทความ').upper(), font=small, fill=(255, 90, 95))
    for ln in lines:
        d.text((80, y), ln, font=big, fill=(255, 255, 255))
        y += 82
    logo = ROOT / 'images' / 'logo-192.png'
    if logo.exists():
        lg = Image.open(logo).convert('RGB').resize((84, 84))
        im.paste(lg, (80, Hh - 130))
    d.text((184, Hh - 112), 'BOXFAN · boxingfandom.com', font=small, fill=(203, 213, 225))
    im.save(out, quality=86, optimize=True)
    return '/images/blog/%s.jpg' % slug


CSS = '''
.ar-wrap{max-width:780px;margin:0 auto;padding:20px 18px 40px}
.ar-crumb{font-size:12.5px;color:var(--bf-text-3);margin-bottom:12px}
.ar-crumb a{color:var(--bf-text-2);text-decoration:none}
.ar-cat{display:inline-block;font-size:12px;font-weight:700;color:var(--bf-accent);background:var(--bf-accent-soft);padding:3px 10px;border-radius:999px}
.ar-wrap h1{font-size:clamp(26px,4.6vw,38px);line-height:1.3;margin:12px 0 8px;color:var(--bf-ink)}
.ar-sub{font-size:15px;color:var(--bf-text-3);margin:0 0 10px;font-style:italic}
.ar-meta{font-size:13px;color:var(--bf-text-3);display:flex;flex-wrap:wrap;gap:6px 14px;margin-bottom:18px}
.ar-meta b{color:var(--bf-text-2)}
.ar-cover{width:100%;height:auto;aspect-ratio:1200/630;object-fit:cover;border-radius:var(--bf-r-lg);display:block;background:var(--bf-ink)}
.ar-toc{background:#fff;border:1px solid var(--bf-line);border-radius:var(--bf-r);padding:14px 18px;margin:20px 0}
.ar-toc b{font-size:14px}
.ar-toc ol{margin:8px 0 0;padding-left:20px}
.ar-toc li{margin:4px 0;font-size:14px;line-height:1.5}
.ar-toc a{color:var(--bf-text);text-decoration:none}
.ar-toc a:hover{color:var(--bf-accent)}
.ar-body{font-size:16.5px;line-height:1.9;color:var(--bf-text)}
.ar-body h2{font-size:23px;line-height:1.4;margin:36px 0 12px;color:var(--bf-ink);scroll-margin-top:80px}
.ar-body h3{font-size:18.5px;line-height:1.45;margin:26px 0 8px;color:var(--bf-ink)}
.ar-body h4{font-size:16.5px;margin:20px 0 6px}
.ar-body p{margin:0 0 16px}
.ar-body ul,.ar-body ol{padding-left:22px;margin:0 0 16px}
.ar-body li{margin:4px 0}
.ar-body blockquote{margin:0 0 16px;padding:10px 16px;border-left:4px solid var(--bf-accent);background:#fff;border-radius:0 8px 8px 0;color:var(--bf-text-2)}
.ar-body hr{border:0;border-top:1px solid var(--bf-line);margin:26px 0}
.ar-body a{color:var(--bf-accent)}
.ar-body sup.fn{font-size:11px;line-height:0;margin-left:1px}
.ar-body sup.fn a{text-decoration:none;font-weight:700}
.ar-body .tbl{overflow-x:auto;margin:0 0 18px;border:1px solid var(--bf-line);border-radius:10px;background:#fff}
.ar-body table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.55;min-width:560px}
.ar-body th{background:var(--bf-surface-2);text-align:left;font-weight:700;color:var(--bf-ink)}
.ar-body th,.ar-body td{padding:9px 12px;border-bottom:1px solid var(--bf-line);vertical-align:top}
.ar-body tr:last-child td{border-bottom:0}
.ar-body .refs{font-size:13px;line-height:1.7;color:var(--bf-text-2);word-break:break-word}
.ar-body ol.refs{padding-left:24px}
.ar-body .refs li{margin:6px 0}
.ar-note{margin-top:28px;padding:14px 16px;background:var(--bf-surface-2);border-radius:10px;font-size:13.5px;color:var(--bf-text-2);line-height:1.7}
.ar-more{margin-top:28px}
.ar-more h2{font-size:18px;margin:0 0 10px}
.ar-more-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.ar-more a{display:block;background:#fff;border:1px solid var(--bf-line);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--bf-text);font-size:14px;font-weight:600;line-height:1.45}
.ar-more a:hover{border-color:var(--bf-accent)}
@media(max-width:560px){.ar-body{font-size:16px}.ar-body h2{font-size:21px}}
.ar-body figure{margin:6px 0 20px}
.ar-body .ar-img img{width:100%;height:auto;border-radius:10px;display:block;background:var(--bf-surface-2)}
.ar-body figcaption{font-size:12.5px;color:var(--bf-text-3);margin-top:6px;line-height:1.5}
.ar-yt,.ar-ifr{position:relative;display:block;width:100%;aspect-ratio:16/9;border:0;border-radius:10px;overflow:hidden;background:#000}
.ar-yt img{width:100%;height:100%;object-fit:cover;display:block;opacity:.92}
.ar-play{position:absolute;left:50%;top:50%;width:68px;height:48px;margin:-24px 0 0 -34px;border-radius:12px;background:var(--bf-accent)}
.ar-play::after{content:"";position:absolute;left:28px;top:14px;border-style:solid;border-width:10px 0 10px 16px;border-color:transparent transparent transparent #fff}
'''


def article_html(meta, slug, body, toc, subtitle, minutes, image, others):
    title = meta['title']
    desc = meta.get('excerpt', '')
    url = '%s/blog/articles/th/%s.html' % (SITE, slug)
    img_abs = image if image.startswith('http') else SITE + image
    author = meta.get('author') or 'Boxfan Editorial'
    cat = meta.get('cat', 'news')
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': title[:110], 'description': desc, 'image': img_abs,
         'datePublished': meta['date'], 'dateModified': meta.get('updated', meta['date']),
         'author': ({'@type': 'Organization', 'name': 'Boxfan'} if author == 'Boxfan Editorial'
                    else {'@type': 'Person', 'name': author}),
         'publisher': {'@type': 'Organization', 'name': 'Boxfan',
                       'logo': {'@type': 'ImageObject', 'url': SITE + '/images/logo-192.png'}},
         'mainEntityOfPage': url, 'inLanguage': 'th-TH'},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'หน้าแรก', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'บทความ', 'item': SITE + '/blog/'},
            {'@type': 'ListItem', 'position': 3, 'name': title, 'item': url}]},
    ]}
    e = lambda s: H.escape(str(s), quote=True)
    toc_html = ('<nav class="ar-toc" aria-label="สารบัญ"><b>สารบัญ</b><ol>%s</ol></nav>'
                % ''.join('<li><a href="#s%d">%s</a></li>' % (i, e(t)) for i, t in toc)) if len(toc) >= 3 else ''
    more = ''
    if others:
        more = ('<section class="ar-more"><h2>อ่านต่อ</h2><div class="ar-more-grid">%s</div></section>'
                % ''.join('<a href="/blog/%s">%s</a>' % (e(o['file']), e(o['title'])) for o in others[:4]))
    return (
        '<!DOCTYPE html>\n<html lang="th" data-theme="light" class="bf">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>%s | Boxfan</title>\n<meta name="description" content="%s">\n<meta name="robots" content="index,follow">\n'
        '<link rel="canonical" href="%s">\n<meta property="og:type" content="article">\n'
        '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
        '<meta property="og:image" content="%s">\n<meta property="og:url" content="%s">\n'
        '<meta property="og:site_name" content="Boxfan">\n<meta property="og:locale" content="th_TH">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<meta property="article:published_time" content="%s">\n'
        '<link rel="icon" type="image/png" href="/images/logo-192.png">\n<meta name="generator" content="boxfan-build-articles">\n'
        '<script type="application/ld+json">%s</script>\n<style>%s</style>\n%s\n</head>\n<body>\n%s\n'
        '<main class="ar-wrap"><article>'
        '<div class="ar-crumb"><a href="/">หน้าแรก</a> › <a href="/blog/">บทความ</a> › %s</div>'
        '<span class="ar-cat">%s</span><h1>%s</h1>%s'
        '<div class="ar-meta"><span>โดย <b>%s</b></span><span>%s</span><span>อ่านประมาณ %d นาที</span></div>'
        '<img class="ar-cover" src="%s" alt="%s" width="1200" height="630">%s'
        '<div class="ar-body">%s</div>'
        '<p class="ar-note">ข้อมูลในบทความรวบรวมจากแหล่งอ้างอิงที่ระบุไว้ ณ วันที่เผยแพร่ ตัวเลขรายได้และค่าตัวบางส่วนเป็นการประมาณการ '
        'ดูสถิตินักมวยล่าสุดได้ที่ <a href="/rankings.html">อันดับนักมวย</a> และ <a href="/events/">รวมศึกทั้งหมด</a></p>'
        '%s</article></main>\n%s\n%s</body>\n</html>\n'
        % (e(title), e(desc), url, e(title), e(desc), e(img_abs), url, meta['date'],
           json.dumps(ld, ensure_ascii=False).replace('</', '<\\/'), CSS,
           build_chrome.block('head', build_chrome.head_html()), build_chrome.block('header', build_chrome.header_html()),
           e(title), e(CATS.get(cat, 'บทความ')), e(title),
           ('<p class="ar-sub">%s</p>' % e(subtitle)) if subtitle else '',
           e(author), th_date(meta['date']), minutes, e(image), e(title), toc_html, body, more,
           build_chrome.block('footer', build_chrome.footer_html()), VIDEO_JS if 'ar-yt' in body else '')
    )


def update_articles_js(entries):
    """ใส่รายการบทความที่สร้างอัตโนมัติไว้บนสุดของ blog/articles.js (ระหว่าง AUTO-ARTICLES)"""
    p = ROOT / 'blog' / 'articles.js'
    t = p.read_bytes().decode('utf-8-sig')
    crlf = '\r\n' in t
    t = t.replace('\r\n', '\n')
    block = '    // AUTO-ARTICLES:start — สร้างโดย build_articles.py จาก blog/source/*.md (อย่าแก้ตรงนี้)\n'
    for en in entries:
        block += ('    {\n        cat     : %s,\n        image   : %s,\n        title   : %s,\n'
                  '        excerpt : %s,\n        file    : %s,\n        date    : %s\n    },\n'
                  % tuple("'" + str(en[k]).replace('\\', '\\\\').replace("'", "\\'") + "'"
                          for k in ('cat', 'image', 'title', 'excerpt', 'file', 'date')))
    block += '    // AUTO-ARTICLES:end\n'
    if '// AUTO-ARTICLES:start' in t:
        t = re.sub(r'    // AUTO-ARTICLES:start.*?// AUTO-ARTICLES:end\n', lambda m: block, t, flags=re.S)
    else:
        i = t.index('var ARTICLES = [') + len('var ARTICLES = [')
        t = t[:i] + '\n' + block + t[i:]
    if crlf:
        t = t.replace('\n', '\r\n')
    data = t.encode('utf-8')
    if p.read_bytes() != data:
        build_chrome.write_file(p, data)


def existing_articles():
    """บทความทั้งหมดใน articles.js (ไว้ทำ 'อ่านต่อ')"""
    t = (ROOT / 'blog' / 'articles.js').read_text(encoding='utf-8-sig')
    out = []
    for m in re.finditer(r"title\s*:\s*'((?:[^'\\]|\\.)*)'.*?file\s*:\s*'([^']+)'", t, re.S):
        out.append({'title': m.group(1).replace("\\'", "'"), 'file': m.group(2)})
    return out


def main():
    if not SRC.exists():
        print('  · ไม่มีโฟลเดอร์ blog/source')
        return
    OUT.mkdir(parents=True, exist_ok=True)
    entries, changed = [], 0
    srcs = sorted(SRC.glob('*.md'))
    metas = []
    for p in srcs:
        meta, text = parse(p)
        slug = re.sub(r'[^a-z0-9-]+', '-', (meta.get('slug') or p.stem).lower()).strip('-') or 'article'
        if not meta.get('title'):
            mt = re.search(r'^#\s+(.+)$', text, re.M)
            meta['title'] = re.sub(r'\*\*', '', mt.group(1)).strip() if mt else slug
        meta.setdefault('date', '2026-01-01')
        meta.setdefault('cat', 'news')
        metas.append((p, meta, text, slug))
    metas.sort(key=lambda x: x[1]['date'], reverse=True)
    for p, meta, text, slug in metas:
        body, toc, subtitle, minutes = render(meta, text)
        if not meta.get('excerpt'):
            first = re.sub(r'<[^>]+>', '', (re.search(r'<p>(.*?)</p>', body, re.S) or [None, ''])[1])
            meta['excerpt'] = first[:150]
        image = meta.get('image') or make_cover(slug, meta['title'], meta['cat'])
        entries.append({'cat': meta['cat'], 'image': image, 'title': meta['title'], 'excerpt': meta['excerpt'],
                        'file': 'articles/th/%s.html' % slug, 'date': meta['date']})
    update_articles_js(entries)
    allart = existing_articles()
    for (p, meta, text, slug), en in zip(metas, entries):
        body, toc, subtitle, minutes = render(meta, text)
        others = [a for a in allart if a['file'] != en['file']]
        html = article_html(meta, slug, body, toc, subtitle, minutes, en['image'], others)
        out = OUT / (slug + '.html')
        data = html.encode('utf-8')
        if not out.exists() or out.read_bytes() != data:
            build_chrome.write_file(out, data)
            changed += 1
    # หน้าที่เคยสร้างจาก blog/source แต่ไฟล์ .md ถูกลบไปแล้ว → ลบหน้านั้น (ไม่แตะบทความเก่าที่เขียนเป็น HTML เอง)
    keep = set(en['file'].split('/')[-1] for en in entries)
    removed = 0
    for h in OUT.glob('*.html'):
        if h.name in keep:
            continue
        try:
            head = h.read_bytes()[:3000]
        except OSError:
            continue
        if b'boxfan-build-articles' in head:
            h.unlink()
            cover = COVERS / (h.stem + '.jpg')           # ภาพปกที่สคริปต์สร้างให้บทความนั้น
            if cover.exists():
                cover.unlink()
            removed += 1
    print('  ✓ บทความจาก blog/source: %d เรื่อง (เปลี่ยนจริง %d ไฟล์%s)'
          % (len(entries), changed, (' · ลบบทความที่ถูกลบ %d' % removed) if removed else ''))
    return entries


if __name__ == '__main__':
    main()
