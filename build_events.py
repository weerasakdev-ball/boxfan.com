#!/usr/bin/env python3
"""
build_events.py — สร้างหน้ารวมของแต่ละศึก  events/<ชื่อศึก>-<วันที่>.html  + หน้ารวมทุกศึก events/index.html

ทำไมต้องมี: คนค้น "ผลมวย ONE ลุมพินี 172", "โปรแกรมมวย ONE ลุมพินี 177" เยอะ
แต่เว็บไม่มีหน้าที่ตอบตรง ๆ — สคริปต์นี้สร้างจากประวัติการชกใน fighters_data.js อัตโนมัติ

  - ศึกเดียวกัน = ชื่อศึก + วันที่ (ชื่อซ้ำได้ เช่น ศึกประจำสัปดาห์)
  - คู่เดียวกันที่บันทึกไว้ทั้งสองฝั่ง (A พบ B / B พบ A) นับเป็นคู่เดียว
  - ศึกที่มีไม่ถึง MIN_FIGHTS คู่ = noindex (หน้ายังเปิดได้ แต่ไม่ส่งให้ Google)
  - เขียนเฉพาะไฟล์ที่เปลี่ยน / ลบหน้าศึกที่ไม่มีในข้อมูลแล้ว (เฉพาะในโฟลเดอร์ events/)
  - เมนู/ท้ายเว็บ/ธีม มาจาก build_chrome.py เหมือนทุกหน้า
ไม่แตะไฟล์ข้อมูล (อ่านอย่างเดียว)
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'data'))
import build_chrome  # noqa: E402
import generate_profiles as G  # noqa: E402

OUT = ROOT / 'events'
SITE = G.SITE
MIN_FIGHTS = 3
# ชื่อไฟล์หน้าศึก — ใช้ฟังก์ชันเดียวกับหน้านักมวย (ลิงก์ชื่อศึกในประวัติการชก) จะได้ตรงกันเสมอ
event_slug = G.event_slug
event_href = G.event_href


def series_of(name):
    """ชื่อรายการแบบไม่มีเลขครั้ง เช่น 'ONE ลุมพินี 172 & The Inner Circle 32' -> 'ONE ลุมพินี'"""
    s = re.split(r'\s*[&:(]', str(name or ''))[0]
    return re.sub(r'\s*\d+\s*$', '', s).strip()


RES_TH = {'win': 'ชนะ', 'loss': 'แพ้', 'draw': 'เสมอ', 'nc': 'ไม่มีผล', 'cancelled': 'ยกเลิก', 'upcoming': 'รอชก'}


# ═══════════════ ไฮไลท์ (highlights.txt) ═══════════════
YT_ID = re.compile(r'(?:youtu\.be/|youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/))([A-Za-z0-9_-]{11})')


def read_highlights():
    """อ่าน highlights.txt → [(บรรทัดที่, ชื่อศึก, วันที่หรือ None, video id, ชื่อนักมวยหรือ '')]"""
    p = ROOT / 'highlights.txt'
    out, bad = [], []
    if not p.exists():
        return out, bad
    for n, line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [x.strip() for x in line.split('|')]
        if len(parts) < 2:
            bad.append((n, 'ต้องมี | คั่นระหว่างชื่อศึกกับลิงก์'))
            continue
        m = YT_ID.search(parts[1])
        if not m:
            bad.append((n, 'ไม่ใช่ลิงก์ YouTube'))
            continue
        ev, d = parts[0], None
        md = re.search(r'\s(\d{4}-\d{2}-\d{2})$', ev)
        if md:
            ev, d = ev[:md.start()].strip(), md.group(1)
        out.append((n, ev, d, m.group(1), parts[2] if len(parts) > 2 else ''))
    return out, bad


def attach_highlights(events):
    """ผูกคลิปเข้ากับศึก (และคู่ถ้าใส่ชื่อนักมวย) — คืนรายการบรรทัดที่หาศึก/คู่ไม่เจอ"""
    rows, bad = read_highlights()
    by_name = {}
    for e in events.values():
        by_name.setdefault(e['name'].strip().lower(), []).append(e)
    for n, ev, d, vid, who in rows:
        cands = by_name.get(ev.lower(), [])
        if d:
            cands = [e for e in cands if e['date'] == d]
        if not cands:
            bad.append((n, 'ไม่พบศึก "%s"%s' % (ev, (' วันที่ ' + d) if d else '')))
            continue
        e = max(cands, key=lambda x: x['date'])      # ชื่อซ้ำหลายวัน → ใช้ครั้งล่าสุด
        if who:
            w = who.lower()
            hit = next((x for x in e['fights'] if w in (x['a'] or '').lower() or w in (x['b'] or '').lower()), None)
            if not hit:
                bad.append((n, 'ไม่พบนักมวย "%s" ในศึก %s' % (who, e['name'])))
                continue
            hit.setdefault('videos', []).append(vid)
        else:
            e.setdefault('videos', []).append(vid)
    return bad


def video_html(vid, label, small=False):
    """ภาพปก + ปุ่มเล่น (กดแล้วค่อยโหลดคลิป — หน้าเว็บไม่ช้า) / ไม่มี JS = ลิงก์ไป YouTube"""
    return ('<figure class="ev-vid%s"><a class="ev-yt" href="https://www.youtube.com/watch?v=%s" data-yt="%s" '
            'target="_blank" rel="noopener" aria-label="เล่นวิดีโอ %s">'
            '<img src="https://i.ytimg.com/vi/%s/hqdefault.jpg" alt="%s" loading="lazy" width="480" height="360">'
            '<span class="ev-play" aria-hidden="true"></span></a>'
            '<figcaption>%s · วิดีโอจาก YouTube · ลิขสิทธิ์เป็นของเจ้าของคลิป · '
            '<a href="https://www.youtube.com/watch?v=%s" target="_blank" rel="noopener">ดูบน YouTube</a></figcaption></figure>'
            % (' sm' if small else '', vid, vid, G.esc(label), vid, G.esc(label), G.esc(label), vid))


VIDEO_JS = ('<script>document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest(".ev-yt");'
            'if(!a)return;e.preventDefault();var f=document.createElement("iframe");'
            'f.src="https://www.youtube-nocookie.com/embed/"+a.getAttribute("data-yt")+"?autoplay=1&rel=0";'
            'f.title=a.getAttribute("aria-label")||"YouTube";f.allow="autoplay; encrypted-media; picture-in-picture; fullscreen";'
            'f.allowFullscreen=true;f.className="ev-ifr";a.replaceWith(f);});</script>')


def collect():
    path = str(ROOT / 'data' / 'fighters_data.js')
    if not os.path.exists(path):
        sys.exit('✗ ไม่พบ data/fighters_data.js')
    fighters, hmap, meta = G.load_from_js(path)
    G.assign_page_names(fighters)
    by_id = {f.get('id'): f for f in fighters}
    by_name = {}
    for f in fighters:
        for k in ('name_th', 'name_en'):
            if f.get(k):
                by_name.setdefault(f[k], f)

    events = {}
    for fid, rows in hmap.items():
        me = by_id.get(fid)
        if not me:
            continue
        for h in rows:
            ev = str(h.get('event') or '').strip()
            d = str(h.get('date') or '')[:10]
            if not ev or not d:
                continue
            opp = by_name.get(h.get('opponent'))
            me_name = me.get('name_th') or me.get('name_en') or ''
            opp_name = (opp.get('name_th') if opp else None) or h.get('opponent') or ''
            key = (ev, d)
            e = events.setdefault(key, {'name': ev, 'date': d, 'fights': {}, 'promo': None})
            e['promo'] = e['promo'] or h.get('promotion')
            pair = tuple(sorted([me_name, opp_name]))
            if pair in e['fights']:
                continue
            rt = h.get('result_type')
            # ให้ผู้ชนะอยู่ฝั่งซ้ายเสมอ
            if rt == 'loss' and opp_name:
                a, a_f, b, b_f, rt2 = opp_name, opp, me_name, me, 'win'
            else:
                a, a_f, b, b_f, rt2 = me_name, me, opp_name, opp, rt
            e['fights'][pair] = {
                'a': a, 'a_f': a_f, 'b': b, 'b_f': b_f, 'rt': rt2,
                'decision': h.get('decision') or '', 'round': h.get('round'), 'time': h.get('time') or '',
                'division': h.get('division') or '', 'rules': h.get('rules') or '',
                'finish': G.is_finish(h), 'order': len(e['fights']),
            }
    for e in events.values():
        e['fights'] = sorted(e['fights'].values(), key=lambda x: x['order'])
        e['n'] = len(e['fights'])
        e['upcoming'] = all(x['rt'] == 'upcoming' for x in e['fights'])
        e['slug'] = event_slug(e['name'], e['date'])
        e['series'] = series_of(e['name'])
    return events, meta


def fighter_link(name, f):
    nm = G.esc(name)
    if f and f.get('_page'):
        return '<a href="/fighters/%s.html">%s</a>' % (quote(f['_page'], safe=''), nm)
    return nm


def avatar(f):
    src = G.cimg(f.get('image_filename'), 'sm') if f else '/images/noname1.png'
    if src.startswith('../'):
        src = src[2:]
    return '<img class="ev-av" src="%s" alt="" loading="lazy" onerror="this.onerror=null;this.src=\'/images/noname1.png\'">' % G.esc(src)


def fight_row(x, upcoming):
    meta = [x['division'], x['rules']]
    how = ''
    if not upcoming:
        bits = []
        if x['decision']:
            bits.append(x['decision'])
        if x['round']:
            bits.append('ยก %s' % x['round'])
        if x['time']:
            bits.append(str(x['time']))
        how = ' · '.join(G.esc(b) for b in bits)
    rt = x['rt']
    if upcoming or rt == 'upcoming':
        mid = '<span class="ev-vs">VS</span>'
        cta = ''
        if x['a_f'] and x['b_f']:
            cta = ('<a class="ev-cmp" href="/compare.html?a=%s&amp;b=%s">เทียบสถิติ →</a>'
                   % (quote(str(x['a_f']['id']), safe=''), quote(str(x['b_f']['id']), safe='')))
    else:
        label = {'win': 'ชนะ' + (' น็อก' if x['finish'] else ''), 'draw': 'เสมอ', 'nc': 'ไม่มีผล',
                 'cancelled': 'ยกเลิก'}.get(rt, RES_TH.get(rt, ''))
        mid = '<span class="ev-res r-%s">%s</span>' % (rt or 'x', G.esc(label))
        cta = ''
    win_cls = ' win' if rt == 'win' else ''
    return (
        '<div class="ev-row">'
        '<div class="ev-side%s">%s<div><div class="ev-nm">%s</div></div></div>'
        '<div class="ev-mid">%s</div>'
        '<div class="ev-side r">%s<div><div class="ev-nm">%s</div></div></div>'
        '<div class="ev-meta">%s%s%s</div>%s'
        '</div>'
        % (win_cls, avatar(x['a_f']), fighter_link(x['a'], x['a_f']), mid,
           avatar(x['b_f']), fighter_link(x['b'], x['b_f']),
           G.esc(' · '.join(m for m in meta if m)), (' · ' + how) if how else '', cta,
           ''.join('<div class="ev-bvid">%s</div>' % video_html(v, 'ไฮไลท์ %s vs %s' % (x['a'], x['b']), True)
                   for v in x.get('videos', [])))
    )


CSS = '''
.ev-wrap{max-width:900px;margin:0 auto;padding:20px 16px 40px}
.ev-crumb{font-size:12.5px;color:var(--bf-text-3);margin-bottom:12px}
.ev-crumb a{color:var(--bf-text-2);text-decoration:none}
.ev-hd{background:#fff;border:1px solid var(--bf-line);border-radius:var(--bf-r-lg);padding:22px 22px 18px;box-shadow:var(--bf-sh-1)}
.ev-kick{font-size:12px;font-weight:700;color:var(--bf-accent);letter-spacing:.3px}
.ev-hd h1{margin:6px 0 8px;font-size:clamp(22px,4vw,30px);line-height:1.3;color:var(--bf-ink)}
.ev-hd p{margin:0;color:var(--bf-text-2);font-size:14px;line-height:1.7}
.ev-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.ev-chip{font-size:12px;font-weight:600;background:var(--bf-surface-2);color:var(--bf-text-2);padding:4px 10px;border-radius:999px}
.ev-list{margin-top:16px;background:#fff;border:1px solid var(--bf-line);border-radius:var(--bf-r-lg);overflow:hidden}
.ev-row{display:grid;grid-template-columns:1fr auto 1fr;gap:6px 12px;align-items:center;padding:14px 16px;border-bottom:1px solid var(--bf-line)}
.ev-row:last-child{border-bottom:0}
.ev-side{display:flex;align-items:center;gap:10px;min-width:0}
.ev-side.r{flex-direction:row-reverse;text-align:right}
.ev-av{width:40px;height:40px;border-radius:50%;object-fit:cover;background:var(--bf-surface-2);flex-shrink:0}
.ev-nm{font-size:14.5px;font-weight:700;line-height:1.35;color:var(--bf-ink);word-break:break-word}
.ev-nm a{color:inherit;text-decoration:none}
.ev-nm a:hover{color:var(--bf-accent)}
.ev-side.win .ev-nm::after{content:" ✓";color:var(--bf-win)}
.ev-mid{text-align:center}
.ev-vs{font-weight:800;color:var(--bf-text-4);font-size:13px}
.ev-res{display:inline-block;font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;white-space:nowrap}
.r-win{background:var(--bf-win-soft);color:var(--bf-win)}
.r-draw,.r-nc,.r-cancelled,.r-x{background:var(--bf-surface-2);color:var(--bf-text-3)}
.ev-meta{grid-column:1/-1;font-size:12px;color:var(--bf-text-3);text-align:center}
.ev-cmp{display:inline-block;margin-left:8px;font-weight:700;color:var(--bf-accent);text-decoration:none}
.ev-nav{display:flex;justify-content:space-between;gap:10px;margin-top:16px}
.ev-nav a{flex:1;background:#fff;border:1px solid var(--bf-line);border-radius:var(--bf-r);padding:12px 14px;text-decoration:none;color:var(--bf-text)}
.ev-nav a small{display:block;font-size:11.5px;color:var(--bf-text-3)}
.ev-nav a b{font-size:13.5px}
.ev-nav a.nx{text-align:right}
.ev-more{margin-top:16px;font-size:13.5px;color:var(--bf-text-2);line-height:1.8}
.ev-more a{color:var(--bf-accent);font-weight:600}
.ev-year{margin:26px 0 8px;font-size:18px;color:var(--bf-ink)}
.ev-idx{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}
.ev-idx a{display:block;background:#fff;border:1px solid var(--bf-line);border-radius:10px;padding:10px 12px;text-decoration:none;color:var(--bf-text)}
.ev-idx a:hover{border-color:var(--bf-accent)}
.ev-idx b{display:block;font-size:14px;line-height:1.35}
.ev-idx small{font-size:12px;color:var(--bf-text-3)}
.ev-idx .up{color:var(--bf-accent);font-weight:700}
.ev-vids{margin-top:16px;background:#fff;border:1px solid var(--bf-line);border-radius:var(--bf-r-lg);padding:16px}
.ev-vids h2{margin:0 0 12px;font-size:17px;color:var(--bf-ink)}
.ev-vid{margin:0 0 14px}
.ev-vid:last-child{margin-bottom:0}
.ev-yt,.ev-ifr{position:relative;display:block;width:100%;aspect-ratio:16/9;border:0;border-radius:10px;overflow:hidden;background:#000}
.ev-yt img{width:100%;height:100%;object-fit:cover;display:block;opacity:.92}
.ev-play{position:absolute;left:50%;top:50%;width:68px;height:48px;margin:-24px 0 0 -34px;border-radius:12px;background:var(--bf-accent);box-shadow:0 6px 20px rgba(0,0,0,.35)}
.ev-play::after{content:"";position:absolute;left:28px;top:14px;border-style:solid;border-width:10px 0 10px 16px;border-color:transparent transparent transparent #fff}
.ev-yt:hover .ev-play{transform:scale(1.06)}
.ev-vid figcaption{font-size:12px;color:var(--bf-text-3);margin-top:6px}
.ev-vid figcaption a{color:var(--bf-accent);font-weight:600}
.ev-bvid{grid-column:1/-1;max-width:420px;margin:4px auto 0;width:100%}
.ev-filter{width:100%;height:42px;border:1px solid var(--bf-line);border-radius:999px;padding:0 16px;font-size:14px;margin-top:14px;background:#fff}
@media(max-width:560px){
  .ev-row{grid-template-columns:1fr;gap:8px}
  .ev-side.r{flex-direction:row;text-align:left}
  .ev-mid{text-align:left;padding-left:50px}
  .ev-meta{text-align:left}
}
'''


def page(title, desc, canonical, robots, body, jsonld):
    return (
        '<!DOCTYPE html>\n<html lang="th" data-theme="light" class="bf">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>%s</title>\n<meta name="description" content="%s">\n<meta name="robots" content="%s">\n'
        '<link rel="canonical" href="%s">\n'
        '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
        '<meta property="og:url" content="%s">\n<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="Boxfan">\n<meta property="og:locale" content="th_TH">\n'
        '<meta property="og:image" content="%s/og-default.jpg">\n'
        '<link rel="icon" type="image/png" href="/images/logo-192.png">\n'
        '<script type="application/ld+json">%s</script>\n<style>%s</style>\n%s\n</head>\n<body>\n%s\n'
        '<main class="ev-wrap">%s</main>\n%s\n</body>\n</html>\n'
        % (title, desc, robots, canonical, title, desc, canonical, SITE,
           json.dumps(jsonld, ensure_ascii=False).replace('</', '<\\/'), CSS,
           build_chrome.head_html(), build_chrome.header_html(), body, build_chrome.footer_html())
    )


def event_page(e, prev_e, next_e):
    th_d = G.th_date(e['date'])
    up = e['upcoming']
    name = G.esc(e['name'])
    url = SITE + event_href(e['name'], e['date'])
    if up:
        title = '%s (%s) โปรแกรมมวย วิเคราะห์ %d คู่ | Boxfan' % (name, th_d, e['n'])
        h1 = 'โปรแกรมมวย %s' % name
        kick = 'ไฟต์ที่กำลังจะมาถึง · %s' % th_d
    else:
        title = 'ผลมวย %s (%s) ครบ %d คู่ | Boxfan' % (name, th_d, e['n'])
        h1 = 'ผลมวย %s' % name
        kick = 'ผลการแข่งขัน · %s' % th_d

    winners = [x['a'] for x in e['fights'] if x['rt'] == 'win'][:3]
    if up:
        pairs = ['%s vs %s' % (x['a'], x['b']) for x in e['fights'][:3]]
        desc = '%s %s รวม %d คู่ — %s เทียบสถิติทุกคู่ก่อนชกที่ Boxfan' % (
            'โปรแกรมมวย', e['name'], e['n'], ', '.join(pairs))
    else:
        desc = 'ผลมวย %s วันที่ %s ครบทุกคู่ %d คู่%s พร้อมวิธีชนะ ยก และลิงก์ประวัตินักมวยทุกคน' % (
            e['name'], th_d, e['n'], (' — ผู้ชนะ ' + ', '.join(winners)) if winners else '')
    desc = G.esc(desc[:300])

    lead = ('%s วันที่ %s มีทั้งหมด %d คู่ — %s' % (
        name, th_d, e['n'],
        'กด "เทียบสถิติ" เพื่อวิเคราะห์ก่อนชก ดูอัตราชนะ ฟอร์มล่าสุด และข้อมูลร่างกายของทั้งสองฝั่ง' if up
        else 'ผู้ชนะอยู่ฝั่งซ้าย (✓) กดชื่อนักมวยเพื่อดูประวัติการชกทั้งหมด'))
    chips = [th_d, '%d คู่' % e['n']]
    if e['promo']:
        chips.append(G.esc(e['promo']))
    divs = sorted(set(x['division'] for x in e['fights'] if x['division']))
    chips += [G.esc(d) for d in divs[:4]]

    nav = ''
    if prev_e or next_e:
        nav = '<nav class="ev-nav" aria-label="ศึกก่อนหน้าและถัดไป">'
        if prev_e:
            nav += '<a href="%s"><small>← ครั้งก่อน</small><b>%s</b></a>' % (
                event_href(prev_e['name'], prev_e['date']), G.esc(prev_e['name']))
        if next_e:
            nav += '<a class="nx" href="%s"><small>ครั้งถัดไป →</small><b>%s</b></a>' % (
                event_href(next_e['name'], next_e['date']), G.esc(next_e['name']))
        nav += '</nav>'

    body = (
        '<div class="ev-crumb"><a href="/">หน้าแรก</a> › <a href="/events/">รวมศึกทั้งหมด</a> › %s</div>'
        '<section class="ev-hd"><div class="ev-kick">%s</div><h1>%s</h1><p>%s</p>'
        '<div class="ev-chips">%s</div></section>'
        '%s<section class="ev-list" aria-label="รายการคู่ชก">%s</section>%s'
        '<p class="ev-more">ดูศึกอื่น ๆ ได้ที่ <a href="/events/">รวมศึกทั้งหมด</a> · '
        '<a href="/schedule.html">วิเคราะห์มวยวันนี้</a> · <a href="/results.html">ผลมวยล่าสุด</a></p>'
        % (name, kick, h1, lead, ''.join('<span class="ev-chip">%s</span>' % c for c in chips),
           ('<section class="ev-vids" aria-label="ไฮไลท์"><h2>ไฮไลท์ %s</h2>%s</section>'
            % (name, ''.join(video_html(v, 'ไฮไลท์ ' + e['name']) for v in e.get('videos', []))))
           if e.get('videos') else '',
           ''.join(fight_row(x, up) for x in e['fights']), nav)
    )
    if e.get('videos') or any(x.get('videos') for x in e['fights']):
        body += VIDEO_JS
    competitors = []
    for x in e['fights']:
        for nm, f in ((x['a'], x['a_f']), (x['b'], x['b_f'])):
            p = {'@type': 'Person', 'name': nm}
            if f and f.get('_page'):
                p['url'] = '%s/fighters/%s.html' % (SITE, quote(f['_page'], safe=''))
            competitors.append(p)
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'SportsEvent', 'name': e['name'], 'startDate': e['date'], 'url': url,
         'sport': 'Muay Thai / Kickboxing / MMA',
         'eventStatus': 'https://schema.org/EventScheduled',
         'location': {'@type': 'Place', 'name': e['promo'] or e['name']},
         'organizer': {'@type': 'Organization', 'name': e['promo'] or e['series'] or e['name']},
         'competitor': competitors[:40]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'หน้าแรก', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'รวมศึกทั้งหมด', 'item': SITE + '/events/'},
            {'@type': 'ListItem', 'position': 3, 'name': e['name'], 'item': url}]},
    ]}
    vids = [(v, 'ไฮไลท์ ' + e['name']) for v in e.get('videos', [])]
    vids += [(v, 'ไฮไลท์ %s vs %s — %s' % (x['a'], x['b'], e['name'])) for x in e['fights'] for v in x.get('videos', [])]
    for v, label in vids:
        ld['@graph'].append({'@type': 'VideoObject', 'name': label,
                             'description': '%s วันที่ %s (วิดีโอจาก YouTube)' % (label, th_d),
                             'thumbnailUrl': 'https://i.ytimg.com/vi/%s/hqdefault.jpg' % v,
                             'uploadDate': e['date'], 'embedUrl': 'https://www.youtube.com/embed/' + v,
                             'contentUrl': 'https://www.youtube.com/watch?v=' + v})
    robots = 'index,follow' if e['n'] >= MIN_FIGHTS else 'noindex,follow'
    return page(title, desc, url, robots, body, ld)


def index_page(events):
    today = date.today().isoformat()
    show = sorted((e for e in events if e['n'] >= MIN_FIGHTS), key=lambda e: e['date'], reverse=True)
    up = [e for e in show if e['date'] >= today]
    past = [e for e in show if e['date'] < today]

    def card(e):
        hl = e.get('videos') or any(x.get('videos') for x in e['fights'])
        return ('<a href="%s" data-q="%s"><b>%s</b><small>%s · %d คู่%s%s</small></a>'
                % (event_href(e['name'], e['date']), G.esc(e['name'].lower()), G.esc(e['name']),
                   G.th_date(e['date']), e['n'], ' · <span class="up">กำลังจะมาถึง</span>' if e['date'] >= today else '',
                   ' · <span class="up">▶ มีไฮไลท์</span>' if hl else ''))

    body = ['<div class="ev-crumb"><a href="/">หน้าแรก</a> › รวมศึกทั้งหมด</div>',
            '<section class="ev-hd"><div class="ev-kick">ผลมวย · โปรแกรมมวย · ทุกรายการ</div>'
            '<h1>รวมศึกมวยทั้งหมด — ผลมวยและโปรแกรมชกทุกศึก</h1>'
            '<p>รวม %d ศึก ตั้งแต่ ONE ลุมพินี, ONE Championship, The Inner Circle ไปจนถึงศึกมวยไทยในประเทศ '
            'ทุกศึกมีรายชื่อคู่ชกครบ ผลการแข่งขัน วิธีชนะ และลิงก์ไปประวัตินักมวยทุกคน</p>'
            '<input class="ev-filter" id="ev-q" type="search" placeholder="ค้นหาชื่อศึก เช่น ONE ลุมพินี 172" '
            'aria-label="ค้นหาชื่อศึก"></section>' % len(show)]
    if up:
        body.append('<h2 class="ev-year">ศึกที่กำลังจะมาถึง</h2><div class="ev-idx">%s</div>'
                    % ''.join(card(e) for e in sorted(up, key=lambda e: e['date'])))
    year = None
    chunk = []
    for e in past:
        y = int(e['date'][:4]) + 543
        if y != year:
            if chunk:
                body.append('<div class="ev-idx">%s</div>' % ''.join(chunk))
            body.append('<h2 class="ev-year">ปี %d</h2>' % y)
            chunk, year = [], y
        chunk.append(card(e))
    if chunk:
        body.append('<div class="ev-idx">%s</div>' % ''.join(chunk))
    body.append('<script>(function(){var q=document.getElementById("ev-q");if(!q)return;'
                'q.addEventListener("input",function(){var v=q.value.trim().toLowerCase();'
                'document.querySelectorAll(".ev-idx a").forEach(function(a){'
                'a.style.display=!v||a.getAttribute("data-q").indexOf(v)>=0?"":"none";});'
                'document.querySelectorAll(".ev-idx").forEach(function(g){var any=[].some.call(g.children,function(a){return a.style.display!=="none";});'
                'g.style.display=any?"":"none";var h=g.previousElementSibling;if(h&&h.classList.contains("ev-year"))h.style.display=any?"":"none";});});})();</script>')
    url = SITE + '/events/'
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'รวมศึกมวยทั้งหมด', 'url': url,
          'hasPart': [{'@type': 'SportsEvent', 'name': e['name'], 'startDate': e['date'],
                       'url': SITE + event_href(e['name'], e['date'])} for e in show[:50]]}
    title = 'รวมศึกมวยทั้งหมด — ผลมวย โปรแกรมมวย ONE ลุมพินี ทุกศึก | Boxfan'
    desc = 'รวมผลมวยและโปรแกรมชกทุกศึก %d รายการ ONE ลุมพินี ONE Championship The Inner Circle และศึกมวยไทย ครบทุกคู่ พร้อมประวัตินักมวย' % len(show)
    return page(title, desc, url, 'index,follow', ''.join(body), ld)


def main():
    events, meta = collect()
    bad = attach_highlights(events)
    n_vid = sum(len(e.get('videos', [])) + sum(len(x.get('videos', [])) for x in e['fights']) for e in events.values())
    evs = list(events.values())
    # ครั้งก่อน/ถัดไปของรายการเดียวกัน (series)
    by_series = {}
    for e in evs:
        by_series.setdefault(e['series'], []).append(e)
    for lst in by_series.values():
        lst.sort(key=lambda e: e['date'])
    OUT.mkdir(exist_ok=True)
    before = set(p.name for p in OUT.glob('*.html'))
    wanted, changed = set(), 0
    # ลายนิ้วมือของแต่ละหน้า (รอบก่อน) — เทียบจากตรงนี้แทนการเปิดอ่านไฟล์ (Windows ตรวจไฟล์ทุกครั้งที่เปิด = ช้า)
    import hashlib
    hash_path = ROOT / 'data' / 'event_hashes.json'
    try:
        old_hashes = json.loads(hash_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        old_hashes = {}
    new_hashes = {}

    def put(fname, html):
        nonlocal changed
        path = OUT / fname
        data = html.encode('utf-8')
        h = hashlib.sha1(data).hexdigest()
        wanted.add(fname)
        if fname in before and old_hashes.get(fname) == h:
            new_hashes[fname] = h
            return
        if fname in before and fname not in old_hashes:
            try:                                       # ยังไม่มีลายนิ้วมือ (รอบแรก) → เทียบกับไฟล์จริงครั้งเดียว
                if path.read_bytes() == data:
                    new_hashes[fname] = h
                    return
            except OSError:
                pass
        build_chrome.write_file(path, data)
        new_hashes[fname] = h
        changed += 1

    for lst in by_series.values():
        for i, e in enumerate(lst):
            prev_e = lst[i - 1] if i > 0 else None
            next_e = lst[i + 1] if i + 1 < len(lst) else None
            put(e['slug'] + '.html', event_page(e, prev_e, next_e))
    put('index.html', index_page(evs))

    try:
        build_chrome.write_file(hash_path, json.dumps(new_hashes, ensure_ascii=False).encode('utf-8'))
        # รายชื่อหน้าศึกที่ส่งให้ Google — build_seo ใช้ทำ sitemap โดยไม่ต้องเปิดไฟล์ทีละไฟล์
        build_chrome.write_file(ROOT / 'data' / 'indexable_events.json', json.dumps(
            sorted(e['slug'] + '.html' for e in evs if e['n'] >= MIN_FIGHTS), ensure_ascii=False).encode('utf-8'))
    except OSError:
        pass
    stale = sorted(before - wanted)
    for n in stale:
        try:
            (OUT / n).unlink()
        except OSError as err:
            print('  ⚠ ลบ events/%s ไม่ได้: %s' % (n, err))
    n_index = sum(1 for e in evs if e['n'] >= MIN_FIGHTS)
    if n_vid or bad:
        print('  ▶ ไฮไลท์ %d คลิป จาก highlights.txt' % n_vid)
    for n, why in bad:
        print('  ⚠ highlights.txt บรรทัด %d: %s (ข้ามบรรทัดนี้)' % (n, why))
    print('  ✓ หน้าศึก %d ศึก (ส่งให้ Google %d ศึกที่มีตั้งแต่ %d คู่) — เปลี่ยนจริง %d ไฟล์%s'
          % (len(evs), n_index, MIN_FIGHTS, changed, (' · ลบศึกที่ไม่มีแล้ว %d' % len(stale)) if stale else ''))


if __name__ == '__main__':
    main()
