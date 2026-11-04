#!/usr/bin/env python3
"""
article_editor.py — เครื่องมือเขียนบทความ (ใช้ในเครื่องเจ้าของเท่านั้น ไม่ขึ้นเว็บ)

เปิดด้วย: ดับเบิลคลิก เขียนบทความ.bat  → เบราว์เซอร์เปิด http://127.0.0.1:8800/editor/
  - เขียนบทความ / แก้บทความเดิม / ดูตัวอย่างหน้าตาจริง
  - กด "อัปบทความ" → บันทึกเป็น blog/source/<ชื่อ>.md → สร้างหน้าบทความ + รายการบทความ + sitemap
  - จากนั้นเจ้าของตรวจในเว็บในเครื่อง แล้ว Commit + Push เอง
เปิดได้เฉพาะเครื่องนี้ (127.0.0.1) — คนอื่นในเน็ตเข้าไม่ได้
"""

import json
import os
import re
import shutil
import sys
import threading
import webbrowser
from datetime import date, datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
import build_articles as A  # noqa: E402

SRC = A.SRC
TRASH = SRC / '_ลบแล้ว'
PORT = 8800
LOCK = threading.Lock()
FIELDS = ['title', 'excerpt', 'cat', 'author', 'date', 'slug', 'image', 'editor']


def one_line(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def safe_slug(s):
    return re.sub(r'[^a-z0-9-]+', '-', str(s or '').lower()).strip('-')[:80]


def list_articles():
    out = []
    for p in sorted(SRC.glob('*.md')):
        meta, _ = A.parse(p)
        out.append({'slug': p.stem, 'title': meta.get('title') or p.stem, 'date': meta.get('date', ''),
                    'url': '/blog/articles/th/%s.html' % safe_slug(meta.get('slug') or p.stem)})
    out.sort(key=lambda x: x['date'], reverse=True)
    return out


def load_article(slug):
    p = SRC / (safe_slug(slug) + '.md')
    if not p.exists():
        return None
    meta, text = A.parse(p)
    meta['slug'] = p.stem
    return {'meta': meta, 'body': text.strip('\n')}


def preview(meta, body):
    m = {k: one_line(v) for k, v in meta.items()}
    m['editor'] = '1'
    m.setdefault('date', date.today().isoformat())
    html, toc, subtitle, minutes = A.render(m, body)
    return {'html': html, 'minutes': minutes, 'toc': [t for _, t in toc]}


def save_article(meta, body, old_slug=''):
    title = one_line(meta.get('title'))
    if not title:
        raise ValueError('ใส่ชื่อบทความก่อน')
    if not body.strip():
        raise ValueError('ยังไม่มีเนื้อหา')
    slug = safe_slug(meta.get('slug')) or safe_slug(old_slug) or ('article-' + datetime.now().strftime('%Y%m%d-%H%M'))
    m = {'title': title, 'excerpt': one_line(meta.get('excerpt')), 'cat': one_line(meta.get('cat')) or 'news',
         'author': one_line(meta.get('author')) or 'Boxfan Editorial',
         'date': one_line(meta.get('date')) or date.today().isoformat(), 'slug': slug, 'editor': '1'}
    img = one_line(meta.get('image'))
    if img:
        if not re.match(r'^(https?://|/)', img):
            raise ValueError('ลิงก์รูปปกต้องขึ้นต้นด้วย https://')
        m['image'] = img
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', m['date']):
        raise ValueError('วันที่ต้องเป็นแบบ 2026-11-04')
    head = '---\n' + ''.join('%s: %s\n' % (k, m[k]) for k in FIELDS if m.get(k)) + '---\n\n'
    data = (head + body.replace('\r\n', '\n').strip('\n') + '\n').encode('utf-8')
    with LOCK:
        SRC.mkdir(parents=True, exist_ok=True)
        # เปลี่ยนชื่อลิงก์ของบทความเดิม → ย้ายไฟล์เก่าไปถังขยะ (หน้าเก่าจะถูกลบตอนสร้างใหม่)
        if old_slug and safe_slug(old_slug) != slug and (SRC / (safe_slug(old_slug) + '.md')).exists():
            TRASH.mkdir(exist_ok=True)
            shutil.move(str(SRC / (safe_slug(old_slug) + '.md')), str(TRASH / (safe_slug(old_slug) + '.md')))
        A.build_chrome.write_file(SRC / (slug + '.md'), data)
        rebuild()
    return {'slug': slug, 'url': '/blog/articles/th/%s.html' % slug}


def delete_article(slug):
    p = SRC / (safe_slug(slug) + '.md')
    if not p.exists():
        raise ValueError('ไม่พบบทความ')
    with LOCK:
        TRASH.mkdir(exist_ok=True)
        shutil.move(str(p), str(TRASH / p.name))      # ไม่ลบทิ้งจริง เก็บไว้ในถังขยะ กู้คืนได้
        rebuild()
    return {'ok': True}


def rebuild():
    A.main()
    try:
        import build_seo
        build_seo.sitemap_only()
    except Exception as err:                          # noqa: BLE001 — sitemap พลาดไม่ควรทำให้บันทึกบทความไม่ได้
        print('  ⚠ อัปเดต sitemap ไม่สำเร็จ:', err)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):            # ไม่พิมพ์ทุกคำขอให้รก
        pass

    def send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')    # ตัวอย่างหน้าเว็บต้องเห็นของใหม่เสมอ
        super().end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ('/', '/editor'):
            self.send_response(302)
            self.send_header('Location', '/editor/')
            self.end_headers()
            return
        if u.path == '/api/list':
            return self.send_json(list_articles())
        if u.path == '/api/load':
            a = load_article(parse_qs(u.query).get('slug', [''])[0])
            return self.send_json(a or {'error': 'ไม่พบบทความ'}, 200 if a else 404)
        if u.path == '/api/article-css':
            data = A.CSS.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/css; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def do_POST(self):
        u = urlparse(self.path)
        try:
            n = int(self.headers.get('Content-Length') or 0)
            req = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            if u.path == '/api/preview':
                return self.send_json(preview(req.get('meta') or {}, req.get('body') or ''))
            if u.path == '/api/save':
                return self.send_json(save_article(req.get('meta') or {}, req.get('body') or '', req.get('old_slug') or ''))
            if u.path == '/api/delete':
                return self.send_json(delete_article(req.get('slug') or ''))
            return self.send_json({'error': 'ไม่รู้จักคำสั่ง'}, 404)
        except ValueError as err:
            return self.send_json({'error': str(err)}, 400)
        except Exception as err:                       # noqa: BLE001
            return self.send_json({'error': 'เกิดข้อผิดพลาด: %s' % err}, 500)


def main():
    handler = partial(Handler, directory=str(ROOT))
    try:
        srv = ThreadingHTTPServer(('127.0.0.1', PORT), handler)
    except OSError:
        print('เครื่องมือเขียนบทความเปิดอยู่แล้ว — เปิดเบราว์เซอร์ให้')
        webbrowser.open('http://127.0.0.1:%d/editor/' % PORT)
        return
    url = 'http://127.0.0.1:%d/editor/' % PORT
    print('════════════════════════════════════════')
    print('  เครื่องมือเขียนบทความ Boxfan')
    print('  เปิดที่: %s' % url)
    print('  ปิดเครื่องมือ: ปิดหน้าต่างนี้')
    print('════════════════════════════════════════')
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
