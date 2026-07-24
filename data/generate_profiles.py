"""
BOXFAN — generate_profiles.py  v5
สร้าง static HTML โปรไฟล์นักมวย แบบ self-contained (ฝัง CSS ในตัว ไม่พึ่งไฟล์นอก)
ดีไซน์ยึดตาม profile.html ต้นฉบับ 100%

อ่านข้อมูลจาก fighters_data.js (ผลลัพธ์จาก export_json.py) — ไม่ใช้ fighters.db แล้ว

วิธีรัน:
    python generate_profiles.py                        # หาไฟล์ข้อมูลให้เอง
    python generate_profiles.py C:/path/to/data        # ระบุโฟลเดอร์
    python generate_profiles.py C:/path/fighters_data.js   # ระบุไฟล์ตรง ๆ

─── สิ่งที่แก้ใน v5 ────────────────────────────────────────────────
 1. ลิงก์กลับหน้ารวมนักมวยเป็น ../fighters.html (เดิม ../Fighters.html
    ตัว F ใหญ่ → 404 บนโฮสต์ Linux/GitHub Pages ที่แยกตัวพิมพ์)
 2. ชื่อไฟล์ที่โดนกันซ้ำ (เติม -2) ถูกนำไปใช้ทำลิงก์คู่ต่อสู้ด้วย
    (เดิมลิงก์ชี้ชื่อเดิมที่ไม่มีไฟล์อยู่จริง)
 3. ไม่ลบหน้าเก่าทิ้งก่อนเจน — เจนเสร็จค่อยเก็บกวาดหน้าที่ตกค้าง
    (เดิมถ้าสคริปต์พังกลางทาง หน้าเก่าหายหมดทั้งโฟลเดอร์)
 4. JSON-LD ใช้ข้อความดิบ ไม่ใช่ข้อความที่ escape HTML แล้ว
    และตัดคีย์ที่เป็น null ทิ้ง
 5. เขียนไฟล์ด้วย newline='\\n' เสมอ — ไฟล์ผลลัพธ์ไม่ปนขึ้นบรรทัดแบบ CRLF
 6. เตือนเมื่อชื่อไฟล์มีตัวพิมพ์ใหญ่ปน (เสี่ยง 404 แบบเดียวกับข้อ 1)
 7. เก็บกวาดโค้ด: ตัด import ซ้ำซ้อนในฟังก์ชัน, เลิกใช้ except เปล่า,
    เลิกใช้ตัวแปรชื่อ date ทับชื่อชนิดข้อมูล, กัน KeyError จาก f['id']
──────────────────────────────────────────────────────────────────
"""
import html as H
import json
import os
import re
import sys
from datetime import date, datetime
from urllib.parse import quote

# ═══════════════════════════════════════════════════════════
# ค่าตั้งต้น
# ═══════════════════════════════════════════════════════════
BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE) if os.path.basename(BASE) == 'data' else BASE
OUT = os.path.join(ROOT, 'fighters')
SITE = 'https://www.boxingfandom.com'
CLOUD = 'dpvyl7nan'

DATA_FILENAME = 'fighters_data.js'
SEARCH_FOLDERS = ('data', '.', '..', os.path.join('..', 'data'))

# ─── หน้ารวมนักมวย ────────────────────────────────────────────
# ต้องสะกดตรงกับชื่อไฟล์จริงบนดิสก์แบบเป๊ะ ๆ รวมถึงตัวพิมพ์ใหญ่-เล็ก
# โฮสต์ Linux (GitHub Pages / Netlify / Vercel) แยกตัวพิมพ์
# ส่วน Windows ไม่แยก — จึงเป็นบั๊กที่ทดสอบบนเครื่องแล้วไม่เจอ
FIGHTERS_PAGE = 'fighters.html'

# ═══════════════════════════════════════════════════════════
# โหมดตั้งชื่อไฟล์ HTML  (สำคัญมาก — ต้องตรงกับที่เว็บใช้ลิงก์)
#
#   'id'   ->  fighters/ริวจิน-นาสึกาวา.html
#             ใช้ id เดียวกับที่ทั้งเว็บอ้างถึง (f.id ในหน้าอื่น ๆ)
#             ลิงก์จากหน้าเว็บ:  'fighters/' + encodeURIComponent(f.id) + '.html'
#
#   'slug' ->  fighters/ryujin-nasukawa.html
#             ชื่ออังกฤษ อ่านง่ายกว่าใน URL แต่หน้าเว็บต้องลิงก์ด้วย f.slug
#             ลิงก์จากหน้าเว็บ:  'fighters/' + f.slug + '.html'
#
# ค่าเริ่มต้นคือ 'slug' — ตรงกับฟังก์ชัน fighterUrl() ใน utils.js
# ถ้าอยากเปลี่ยนเป็นชื่อไทย ให้แก้เป็น 'id' แล้วแก้ fighterUrl() ใน utils.js ให้ตรงกัน
# ═══════════════════════════════════════════════════════════
FILENAME_MODE = 'slug'


# ═══════════════════════════════════════════════════════════
# หาไฟล์ข้อมูล
# ═══════════════════════════════════════════════════════════
def _mtime_str(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
    except OSError:
        return '?'


def find_all_data_files():
    """หา fighters_data.js ทุกตัวที่เจอ (เพื่อเตือนถ้ามีหลายสำเนา)"""
    found, seen = [], set()
    for base in (ROOT, BASE):
        for rel in SEARCH_FOLDERS:
            cand = os.path.normpath(os.path.join(base, rel, DATA_FILENAME))
            if cand not in seen and os.path.isfile(cand):
                seen.add(cand)
                found.append(cand)
    return found


def find_data_file():
    """
    หาไฟล์ข้อมูล — ถ้าเจอหลายสำเนาจะเลือกตัวที่ใหม่ที่สุด และเตือนให้ทราบ
    ระบุทาง argument ได้เสมอ (ชนะทุกกรณี)
    """
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isfile(arg):
            return arg
        if os.path.isdir(arg):
            cand = os.path.join(arg, DATA_FILENAME)
            if os.path.isfile(cand):
                return cand
        print('⚠️   ไม่พบไฟล์ตามที่ระบุ: %s' % arg)

    found = find_all_data_files()
    if not found:
        return None
    if len(found) > 1:
        found.sort(key=os.path.getmtime, reverse=True)
        print('⚠️   เจอ %s หลายสำเนา — จะใช้ตัวที่ใหม่ที่สุด' % DATA_FILENAME)
        for i, f in enumerate(found):
            mark = '  <-- ใช้ตัวนี้' if i == 0 else ''
            print('       %s  (แก้ล่าสุด %s)%s' % (f, _mtime_str(f), mark))
        print('       ถ้าไม่ใช่ตัวที่ต้องการ ให้ระบุเอง:')
        print('       python generate_profiles.py "<ทางไปยังไฟล์>"')
        print()
    return found[0]


def warn_if_stale(data_path):
    """เตือนถ้ามีไฟล์ JSON นักมวยที่ใหม่กว่าไฟล์ข้อมูลรวม (แปลว่ายังไม่ได้ export)"""
    try:
        data_mtime = os.path.getmtime(data_path)
    except OSError:
        return

    newer, folder_hit = 0, None
    for base in (ROOT, BASE, os.path.dirname(data_path)):
        for rel in ('data', '.'):
            folder = os.path.normpath(os.path.join(base, rel))
            if not os.path.isdir(folder):
                continue
            try:
                names = os.listdir(folder)
            except OSError:
                continue
            count = 0
            for n in names:
                if not n.lower().endswith('.json') or n.startswith('_') or n.endswith('.bak.json'):
                    continue
                try:
                    if os.path.getmtime(os.path.join(folder, n)) > data_mtime:
                        count += 1
                except OSError:
                    pass
            if count > newer:
                newer, folder_hit = count, folder

    if newer:
        print('⚠️   มีไฟล์ JSON ใหม่กว่าไฟล์ข้อมูลรวม %d ไฟล์' % newer)
        print('       ที่: %s' % folder_hit)
        print('       แปลว่ายังไม่ได้ export — รัน export_json.py ก่อน แล้วค่อยรันตัวนี้อีกที')
        print()


def extract_js_const(text, name):
    """
    ดึงค่าของ const/var ชื่อ name ออกจากไฟล์ .js แล้วแปลงเป็นออบเจกต์ Python
    ใช้การนับวงเล็บโดยข้ามข้อความในเครื่องหมายคำพูด จึงรองรับทั้งแบบบีบอัดและแบบจัดรูปแบบ
    """
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
        else:
            if ch == '"':
                in_str = True
            elif ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
        i += 1
    return None


# ═══════════════════════════════════════════════════════════
# แปลงผลการแข่งภาษาไทย -> รหัสอังกฤษที่เทมเพลตใช้
# ═══════════════════════════════════════════════════════════
RESULT_TYPE_MAP = {
    'ชนะ': 'win', 'แพ้': 'loss', 'เสมอ': 'draw',
    'ไม่มีผล': 'nc', 'ไม่มีผลการแข่งขัน': 'nc',
    'รอแข่งขัน': 'upcoming',
}

FINISH_RE = re.compile(r'เคโอ|ทีเคโอ|น็อก|น๊อก|ซับมิชชัน|ซับมิส|\bko\b|\btko\b|submission', re.I)


def result_type_of(result):
    return RESULT_TYPE_MAP.get(str(result or '').strip(), 'other')


def is_finish(fight):
    return bool(FINISH_RE.search(str(fight.get('decision') or '')))


# ═══════════════════════════════════════════════════════════
# ธงชาติ
# ═══════════════════════════════════════════════════════════
FLAGS = {
    'ไทย': '🇹🇭', 'ญี่ปุ่น': '🇯🇵', 'เกาหลีใต้': '🇰🇷', 'จีน': '🇨🇳',
    'บราซิล': '🇧🇷', 'ฟิลิปปินส์': '🇵🇭', 'รัสเซีย': '🇷🇺', 'อิตาลี': '🇮🇹',
    'ฝรั่งเศส': '🇫🇷', 'อังกฤษ': '🇬🇧', 'สหรัฐ': '🇺🇸', 'แคนาดา': '🇨🇦',
    'ออสเตรเลีย': '🇦🇺', 'เนเธอร์แลนด์': '🇳🇱', 'สเปน': '🇪🇸',
    'เมียนมาร์': '🇲🇲', 'กัมพูชา': '🇰🇭', 'มาเลเซีย': '🇲🇾',
    'อินโดนีเซีย': '🇮🇩', 'อินเดีย': '🇮🇳', 'มองโกเลีย': '🇲🇳',
    'คาซัคสถาน': '🇰🇿', 'จอร์เจีย': '🇬🇪', 'อุซเบกิสถาน': '🇺🇿',
    'ตุรกี': '🇹🇷', 'โมร็อกโก': '🇲🇦', 'แอลจีเรีย': '🇩🇿',
    'อาร์เจนตินา': '🇦🇷', 'เม็กซิโก': '🇲🇽', 'โคลอมเบีย': '🇨🇴',
    'เยอรมนี': '🇩🇪', 'โปแลนด์': '🇵🇱', 'ยูเครน': '🇺🇦',
    'เบลารุส': '🇧🇾', 'โรมาเนีย': '🇷🇴', 'เช็ก': '🇨🇿',
    'สวีเดน': '🇸🇪', 'นอร์เวย์': '🇳🇴', 'เดนมาร์ก': '🇩🇰',
    'ไอร์แลนด์': '🇮🇪', 'นิวซีแลนด์': '🇳🇿', 'แอฟริกาใต้': '🇿🇦',
    'ซาอุดีอาระเบีย': '🇸🇦', 'อิหร่าน': '🇮🇷', 'ปากีสถาน': '🇵🇰',
    'เวียดนาม': '🇻🇳', 'ลาว': '🇱🇦', 'สิงคโปร์': '🇸🇬',
    'เบลเยียม': '🇧🇪', 'ออสเตรีย': '🇦🇹', 'สวิตเซอร์แลนด์': '🇨🇭',
    'โปรตุเกส': '🇵🇹', 'กรีซ': '🇬🇷', 'ทาจิกิสถาน': '🇹🇯',
    'คีร์กีซสถาน': '🇰🇬', 'ฮ่องกง': '🇭🇰', 'ไต้หวัน': '🇹🇼',
    'สหรัฐอเมริกา': '🇺🇸', 'สหราชอาณาจักร': '🇬🇧', 'เมียนมา': '🇲🇲',
    'ไอซ์แลนด์': '🇮🇸', 'เช็กเกีย': '🇨🇿', 'สกอตแลนด์': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'เวลส์': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
    'ฟินแลนด์': '🇫🇮', 'ฮังการี': '🇭🇺', 'บัลแกเรีย': '🇧🇬', 'โครเอเชีย': '🇭🇷',
    'เซอร์เบีย': '🇷🇸', 'สโลวาเกีย': '🇸🇰', 'สโลวีเนีย': '🇸🇮',
    'บอสเนียและเฮอร์เซโกวีนา': '🇧🇦', 'อาเซอร์ไบจาน': '🇦🇿', 'อาร์เมเนีย': '🇦🇲',
    'อิสราเอล': '🇮🇱', 'อิรัก': '🇮🇶', 'ซีเรีย': '🇸🇾', 'เลบานอน': '🇱🇧',
    'จอร์แดน': '🇯🇴', 'คูเวต': '🇰🇼', 'สหรัฐอาหรับเอมิเรตส์': '🇦🇪',
    'กาตาร์': '🇶🇦', 'บาห์เรน': '🇧🇭', 'โอมาน': '🇴🇲',
    'อียิปต์': '🇪🇬', 'ตูนิเซีย': '🇹🇳', 'ไนจีเรีย': '🇳🇬', 'เคนยา': '🇰🇪',
    'แคเมอรูน': '🇨🇲', 'เซเนกัล': '🇸🇳', 'กานา': '🇬🇭',
    'ชิลี': '🇨🇱', 'เปรู': '🇵🇪', 'เวเนซุเอลา': '🇻🇪', 'อุรุกวัย': '🇺🇾',
    'คิวบา': '🇨🇺', 'จาเมกา': '🇯🇲', 'บรูไน': '🇧🇳', 'มาเก๊า': '🇲🇴',
    'เนปาล': '🇳🇵', 'บังกลาเทศ': '🇧🇩', 'ศรีลังกา': '🇱🇰', 'อัฟกานิสถาน': '🇦🇫',
    'มัลดีฟส์': '🇲🇻', 'เติร์กเมนิสถาน': '🇹🇲', 'มอลโดวา': '🇲🇩',
    'ลิทัวเนีย': '🇱🇹', 'ลัตเวีย': '🇱🇻', 'เอสโตเนีย': '🇪🇪',
    'แอลเบเนีย': '🇦🇱', 'มอนเตเนโกร': '🇲🇪', 'มาซิโดเนียเหนือ': '🇲🇰',
    'โคโซโว': '🇽🇰', 'ไซปรัส': '🇨🇾', 'มอลตา': '🇲🇹',
}


def fl(c):
    """ธงชาติ — ไม่มีข้อมูลคืนค่าว่าง / รองรับหลายสัญชาติที่คั่นด้วย /"""
    if not c:
        return ''
    if c in FLAGS:
        return FLAGS[c]
    parts = [x.strip() for x in str(c).split('/') if x.strip()]
    if len(parts) > 1:
        out = [FLAGS[x] for x in parts if x in FLAGS]
        if out:
            return ' '.join(out)
    return '🏳️'


def esc(s):
    """escape HTML — None / ค่าว่าง คืนสตริงว่าง"""
    return H.escape(str(s)) if s not in (None, '') else ''


# ═══════════════════════════════════════════════════════════
# ชื่อไฟล์หน้าโปรไฟล์
# ═══════════════════════════════════════════════════════════
def _slug_fallback(f):
    """สร้าง slug จากชื่ออังกฤษ หรือชื่อไทยถ้าไม่มีอังกฤษ"""
    name = ((f.get('name_en') or '').strip()
            or (f.get('name_th') or '').strip()
            or str(f.get('id') or 'fighter'))
    s = name.strip()
    # ชื่ออังกฤษล้วน -> ตัวพิมพ์เล็กทั้งหมด (กันปัญหาโฮสต์แยกตัวพิมพ์)
    if all(ord(c) < 128 or c in ' -' for c in s):
        s = s.lower()
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'[/\\:*?"<>|]', '', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or 'fighter'


def slug(f):
    """
    ถ้าข้อมูลมีช่อง slug มาให้แล้ว (จาก export_json.py) ให้ใช้ตัวนั้นเสมอ
    เพื่อให้ชื่อไฟล์ตรงกับลิงก์บนเว็บ 100%
    """
    return f.get('slug') or _slug_fallback(f)


def base_page_name(f):
    """ชื่อไฟล์ตั้งต้น (ยังไม่ผ่านการกันซ้ำ) ตาม FILENAME_MODE"""
    if FILENAME_MODE == 'id':
        return str(f.get('id') or slug(f))
    return f.get('slug') or slug(f)


def assign_page_names(fighters):
    """
    กำหนดชื่อไฟล์สุดท้ายให้นักมวยทุกคนล่วงหน้า แล้วเก็บไว้ใน f['_page']

    ต้องทำก่อนเจนหน้าใด ๆ เพราะลิงก์คู่ต่อสู้ต้องใช้ชื่อไฟล์ "ตัวจริง"
    ถ้าคนไหนโดนกันซ้ำจนได้ชื่อ -2 แล้วลิงก์ยังชี้ชื่อเดิม ลิงก์นั้นจะ 404
    """
    used, dups = {}, []
    for f in fighters:
        name = base_page_name(f)
        key = name.lower()          # กันซ้ำแบบไม่สนตัวพิมพ์ — โฮสต์บางเจ้าไม่แยก
        if key in used:
            used[key] += 1
            new_name = '%s-%d' % (name, used[key])
            dups.append((f.get('name_th') or f.get('id'), name, new_name))
            name = new_name
            used[name.lower()] = 1
        else:
            used[key] = 1
        f['_page'] = name
    return dups


def page_name(f):
    """ชื่อไฟล์ HTML ของนักมวยคนนี้ (ไม่รวม .html)"""
    return f.get('_page') or base_page_name(f)


def page_href(f):
    """ทางไปหน้าโปรไฟล์ของนักมวย เมื่อเรียกจากในโฟลเดอร์ fighters/"""
    return '%s.html' % quote(page_name(f), safe='')


# ═══════════════════════════════════════════════════════════
# อ่าน / ประมวลผลข้อมูล
# ═══════════════════════════════════════════════════════════
def derive_stats(fighter, history):
    """
    เติมสถิติที่เทมเพลตต้องใช้ (total_wins / total_losses / total_nc /
    total_fights / win_rate / ko_wins) โดยนับจากประวัติการชกจริง
    ไฟต์ที่ยัง "รอแข่งขัน" ไม่ถูกนับ
    """
    past = [h for h in history if h.get('result_type') != 'upcoming']
    wins = sum(1 for h in past if h.get('result_type') == 'win')
    losses = sum(1 for h in past if h.get('result_type') == 'loss')
    draws = sum(1 for h in past if h.get('result_type') == 'draw')
    nc = sum(1 for h in past if h.get('result_type') == 'nc')

    fighter['total_wins'] = wins
    fighter['total_losses'] = losses
    fighter['total_draws'] = draws
    fighter['total_nc'] = nc
    fighter['total_fights'] = len(past)
    fighter['win_rate'] = round(wins / (wins + losses) * 100) if (wins + losses) else 0
    fighter['ko_wins'] = sum(1 for h in past if h.get('result_type') == 'win' and is_finish(h))
    return fighter


def load_from_js(path):
    """
    อ่าน fighters_data.js แล้วคืน (fighters, history_map, meta)
    ใช้ข้อมูลชุดเดียวกับที่เว็บใช้ จึงไม่มีทางไม่ตรงกัน
    """
    with open(path, 'r', encoding='utf-8-sig') as fh:
        text = fh.read()

    fighters = extract_js_const(text, 'FIGHTERS')
    history = extract_js_const(text, 'HISTORY')
    meta = extract_js_const(text, 'META') or {}

    if fighters is None:
        raise ValueError('ไม่พบ FIGHTERS ในไฟล์ — ไฟล์อาจไม่ใช่ผลลัพธ์จาก export_json.py')
    if history is None:
        history = []

    hmap = {}
    for row in history:
        fight = dict(row)
        fight['result_type'] = result_type_of(fight.get('result'))
        hmap.setdefault(fight.get('fighter_id'), []).append(fight)

    for fights in hmap.values():
        fights.sort(key=lambda x: x.get('date') or '', reverse=True)

    for fighter in fighters:
        derive_stats(fighter, hmap.get(fighter.get('id'), []))

    fighters.sort(key=lambda x: x.get('name_th') or x.get('id') or '')
    return fighters, hmap, meta


def cimg(fn, size='lg'):
    """URL รูปจาก Cloudinary"""
    if not fn:
        return ''
    clean = re.sub(r'\.(jpg|jpeg|png|webp)$', '', str(fn), flags=re.IGNORECASE)
    d = {'sm': 'w_80,h_80,g_face', 'md': 'w_160,h_160,g_face', 'lg': 'w_300,h_375,g_north'}
    return ('https://res.cloudinary.com/%s/image/upload/c_fill,%s,f_auto,q_auto/%s'
            % (CLOUD, d.get(size, d['lg']), clean))


# ═══════════════════════════════════════════════════════════
# CSS — ดึงจากไฟล์จริงเพื่อให้หน้าตาตรงกับ profile.html 100%
# ═══════════════════════════════════════════════════════════
def load_profile_css():
    """อ่าน CSS ทั้งหมดจาก profile.html ต้นฉบับ"""
    profile_path = os.path.join(ROOT, 'profile.html')
    if not os.path.isfile(profile_path):
        print('⚠️   ไม่พบ %s — หน้าที่เจนจะไม่มี CSS ของ profile.html' % profile_path)
        return ''
    with open(profile_path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    return '\n'.join(blocks)


def load_external_css():
    """อ่าน CSS จากไฟล์ภายนอกที่ profile.html อ้างถึง"""
    css = ''
    for fn in ('style.css', 'boxfan-tokens.css'):
        path = os.path.join(ROOT, fn)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as fh:
                css += '\n/* ── %s ── */\n' % fn + fh.read()
        else:
            print('⚠️   ไม่พบ %s' % path)
    return css


# ═══════════════════════════════════════════════════════════
# เจนหน้า HTML
# ═══════════════════════════════════════════════════════════
PH_IMG = ('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 '
          'width=%2250%22 height=%2250%22><rect fill=%22%23232d3b%22 '
          'width=%2250%22 height=%2250%22 rx=%228%22/></svg>')


def build_score(past):
    """
    คะแนน: ต้องใช้สูตรเดียวกับ score() ใน utils.js ไม่งั้นตัวเลขจะไม่ตรงกับหน้าอันดับ
      ชนะ +3 · ชนะน็อก/ซับมิชชันในยกแรก +1 · แพ้ -3
    """
    sc = 0
    for h in past:
        if h.get('result_type') == 'win':
            sc += 3
            if str(h.get('round')) == '1' and is_finish(h):
                sc += 1
        elif h.get('result_type') == 'loss':
            sc -= 3
    return sc


def build_rows(fights, fighters_map):
    """แถวตารางประวัติการชก"""
    rows = ''
    for h in fights:
        r = h.get('result_type', '')
        if r == 'win':
            badge = '<span class="bw">ชนะ</span>'
        elif r == 'loss':
            badge = '<span class="bl">แพ้</span>'
        elif r == 'upcoming':
            badge = '<span class="bu">รอผล</span>'
        else:
            badge = '<span class="bn">NC</span>'

        opp_name = h.get('opponent') or ''
        opp = esc(opp_name) or '—'
        fight_date = esc(h.get('date')) or '—'
        event = esc(h.get('event')) or '—'
        decision = esc(h.get('decision'))
        rules = esc(h.get('rules'))
        rnd = h.get('round') or ''
        tm = h.get('time') or ''
        opp_country = h.get('opponent_country') or ''

        method = ('<span class="deco-pill">%s</span>' % decision) if decision else '<span class="dash">—</span>'
        if rnd:
            method += ('<div style="font-size:11px;color:var(--tx-3);margin-top:3px">ยก %s%s</div>'
                       % (rnd, ' · ' + esc(tm) if tm else ''))

        # รูป + ลิงก์คู่ต่อสู้ (ใช้ชื่อไฟล์ตัวจริงที่ผ่านการกันซ้ำแล้ว)
        opp_f = fighters_map.get(opp_name)
        if opp_f:
            opp_img = cimg(opp_f.get('image_filename'), 'sm') or PH_IMG
            opp_link = '../fighters/%s' % page_href(opp_f)
            opp_td = ('<td><div class="opp-row"><a href="%s"><img class="opp-av" src="%s" '
                      'loading="lazy" alt="%s"></a><div><a href="%s" class="opp-name-link">%s</a>'
                      % (opp_link, opp_img, opp, opp_link, opp))
        else:
            opp_td = ('<td><div class="opp-row"><img class="opp-av no-link" src="%s" alt="">'
                      '<div><span class="opp-name-nolink">%s</span>' % (PH_IMG, opp))

        if opp_country and opp_country != '-':
            opp_td += ('<div style="font-size:11px;color:var(--tx-3)">%s %s</div>'
                       % (fl(opp_country), esc(opp_country)))
        opp_td += '</div></div></td>'

        rows += f'''<tr>
<td>{badge}</td>
{opp_td}
<td class="col-hide-sm">{method}</td>
<td class="col-hide-sm" style="color:var(--tx-3);font-size:12px">{rules or "—"}</td>
<td class="col-hide-sm" style="font-size:12px">{event}</td>
<td style="color:var(--tx-3);font-size:12px;white-space:nowrap">{fight_date}</td>
</tr>'''
    return rows


def generate(f, history, full_css, fighters_map):
    name_th = esc(f.get('name_th'))
    name_en = esc(f.get('name_en'))
    country = esc(f.get('country'))
    division = esc(f.get('division'))
    team = esc(f.get('team'))
    bio = esc(f.get('biography'))
    age = f.get('age') or ''

    wins = f.get('total_wins', 0) or 0
    losses = f.get('total_losses', 0) or 0
    nc = f.get('total_nc', 0) or 0
    total = f.get('total_fights', 0) or 0
    wr = float(f.get('win_rate') or 0)

    img = cimg(f.get('image_filename'), 'lg')
    fid = quote(str(f.get('id') or ''), safe='')     # id เป็นข้อความไทย ต้อง encode ก่อนใส่ URL
    s = quote(page_name(f), safe='')                 # ชื่อไฟล์สำหรับ canonical URL

    title = (f'{name_th} ({name_en}) สถิตินักมวย | Boxfan' if name_en
             else f'{name_th} สถิตินักมวย | Boxfan')
    desc = f'{name_th} นักมวย ONE Championship {division} สถิติ {wins}W {losses}L อัตราชนะ {wr:.0f}% | Boxfan'
    canonical = f'{SITE}/fighters/{s}.html'

    past = [h for h in history if h.get('result_type') != 'upcoming']
    past.sort(key=lambda x: x.get('date') or '', reverse=True)
    up = [h for h in history if h.get('result_type') == 'upcoming']
    up.sort(key=lambda x: x.get('date') or '')       # ไฟต์ที่จะถึง เรียงใกล้ -> ไกล

    sc = build_score(past)

    # จำนวนวันนับจากไฟต์ล่าสุด
    days_rest = ''
    if past:
        try:
            last_date = datetime.strptime(str(past[0].get('date') or ''), '%Y-%m-%d').date()
            days_rest = '<span class="htag">พัก %d วัน</span>' % (date.today() - last_date).days
        except (ValueError, TypeError):
            pass

    # แถบฟอร์มล่าสุด
    form = ''
    for h in reversed(past[:10]):
        r = h.get('result_type', '')
        if r == 'win':
            form += '<div class="fseg win">W</div>'
        elif r == 'loss':
            form += '<div class="fseg loss">L</div>'
        else:
            form += '<div class="fseg nc">NC</div>'

    # ป้ายกำกับ
    tags = ''
    if country:
        tags += f'<span class="htag">{fl(f.get("country"))} {country}</span>'
    if team:
        tags += f'<span class="htag">{team}</span>'
    if age:
        tags += f'<span class="htag">อายุ {esc(age)} ปี</span>'
    tags += f'<span class="htag htag-pts">{sc} pts</span>'
    if days_rest:
        tags += f' {days_rest}'

    # ตารางข้อมูลร่างกาย
    pg = ''
    for key, label in (('height_ft_in', 'ส่วนสูง'), ('height_cm', 'ซม.'),
                       ('weight_lbs', 'ปอนด์'), ('weight_kg', 'กก.')):
        if f.get(key):
            pg += f'<div class="pitem"><div class="pval">{esc(f[key])}</div><div class="plbl">{label}</div></div>'
    pg += f'<div class="pitem accent"><div class="pval">{sc}</div><div class="plbl">คะแนน</div></div>'
    pg += f'<div class="pitem"><div class="pval">{total}</div><div class="plbl">แมตช์รวม</div></div>'

    nc_html = ''
    if nc > 0:
        nc_html = f'<div class="rsep">–</div><div><div class="rn n">{nc}</div><div class="rl">NC</div></div>'

    rows = build_rows(up + past[:10], fighters_map)

    # JSON-LD — ใช้ข้อความดิบ (json.dumps จะ escape ให้เอง) และตัดคีย์ที่ว่างทิ้ง
    ld = {
        '@context': 'https://schema.org',
        '@type': 'Person',
        'name': f.get('name_th') or '',
        'alternateName': f.get('name_en') or None,
        'description': ('%s นักมวย ONE Championship %s'
                        % (f.get('name_th') or '', f.get('division') or '')).strip(),
        'image': img or None,
        'url': canonical,
        'nationality': f.get('country') or None,
        'sport': 'Muay Thai / Kickboxing / MMA',
        'memberOf': {'@type': 'SportsOrganization', 'name': 'ONE Championship'},
    }
    jsonld = json.dumps({k: v for k, v in ld.items() if v is not None}, ensure_ascii=False)

    form_html = (('<div class="form-label">ฟอร์มล่าสุด %d แมตช์</div><div class="fbar">%s</div>'
                  % (min(len(past), 10), form)) if form else '')
    empty_row = ('<tr><td colspan="6" style="padding:32px;text-align:center;'
                 'color:var(--tx-3)">ยังไม่มีประวัติการชก</td></tr>')
    more_html = (('<div style="margin-top:8px;font-size:12px;color:var(--tx-4);text-align:center">'
                  'แสดง %d จาก %d แมตช์</div>'
                  % (min(len(past), 10) + len(up), len(past) + len(up))) if len(past) > 10 else '')
    bio_html = (('<div style="margin-top:18px;padding:24px;background:var(--surf);'
                 'border:1px solid var(--line-2);border-radius:11px;box-shadow:var(--sh-2)">'
                 '<div style="font-family:var(--sans);font-size:15px;font-weight:800;color:var(--tx);'
                 'margin-bottom:12px;display:flex;align-items:center;gap:8px;text-transform:uppercase">'
                 '<span style="color:var(--gold)">★</span> ประวัตินักมวย</div>'
                 '<p style="line-height:1.9;color:var(--tx-2);font-size:14px;margin:0">%s</p></div>'
                 % bio) if bio else '')
    flag_html = ('<div class="hflag">%s</div>' % fl(f.get('country'))) if country else ''
    div_html = ('<div class="hdiv">%s</div>' % division) if division else ''
    name_en_html = ('<div class="hname-en">%s</div>' % name_en) if name_en else ''

    return f'''<!DOCTYPE html>
<html lang="th" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{name_th},{name_en},ONE Championship,{division},มวยไทย,Boxfan">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{img}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="Boxfan">
<meta property="og:locale" content="th_TH">
<meta name="twitter:card" content="summary_large_image">
<script defer src="https://cloud.umami.is/script.js" data-website-id="40ec0b51-4f08-45be-801d-9cf01fc79260"></script>
<script type="application/ld+json">{jsonld}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
{full_css}
</style>
</head>
<body>

<!-- UTIL BAR -->
<div class="util-bar">
  <a href="../about.html">เกี่ยวกับเรา</a>
  <a href="../contact.html">ติดต่อเรา</a>
  <a href="../blog/">บทความ</a>
  <a href="../disclaimer.html">ข้อจำกัดความรับผิด</a>
  <span class="util-bar-right">ข้อมูลโดยแฟนกีฬา · ไม่ใช่เว็บทางการ ONE Championship</span>
</div>

<!-- NAV -->
<nav class="nav">
  <a class="nav-logo" href="../index.html">
    <img src="https://res.cloudinary.com/dia2yts2f/image/upload/v1779892068/ChatGPT_Image_22_%E0%B8%A1.%E0%B8%84._2569_19_38_45.png" alt="Boxfan" onerror="this.style.display='none'">
    <div class="nav-logo-text">
      <span class="logo-main"><span>BOX</span>FAN</span>
      <span class="logo-sub">ผลมวยทุกสังเวียน</span>
    </div>
  </a>
  <div class="nav-tabs">
    <a class="nav-tab" href="../index.html">อันดับ</a>
    <a class="nav-tab" href="../rankings.html">ตารางคะแนน</a>
    <a class="nav-tab" href="../weight-classes.html">แยกตามรุ่น</a>
    <a class="nav-tab" href="../{FIGHTERS_PAGE}">นักมวยทั้งหมด</a>
    <a class="nav-tab" href="../schedule.html">โปรแกรมชก</a>
    <a class="nav-tab" href="../results.html">ผลการแข่งขัน</a>
    <a class="nav-tab" href="../compare.html">เปรียบเทียบ</a>
    <a class="nav-tab" href="../blog/">บทความ</a>
    <a class="nav-tab" href="../tierlist.html">Tier List</a>
  </div>
</nav>

<div class="page">
  <a class="back" href="../{FIGHTERS_PAGE}">← นักมวยทั้งหมด</a>

  <!-- HERO -->
  <div class="hero">
    <div class="hav-wrap">
      <img class="hav" src="{img}" alt="{name_th}" loading="eager">
      {flag_html}
    </div>
    <div class="hinfo">
      {div_html}
      <h1 class="hname">{name_th}</h1>
      {name_en_html}
      <div class="htags">{tags}</div>
      <div class="hrec">
        <div><div class="rn w">{wins}</div><div class="rl">ชนะ</div></div>
        <div class="rsep">–</div>
        <div><div class="rn l">{losses}</div><div class="rl">แพ้</div></div>
        {nc_html}
        <div class="wr-box">
          <div class="wr-bar" style="width:96px"><div class="wr-fill" style="width:{wr}%"></div></div>
          <div style="font-size:11px;color:var(--tx-3);margin-top:5px;font-weight:600">WR {wr:.1f}%</div>
        </div>
      </div>
    </div>
  </div>

  <!-- PHYSICAL -->
  <div class="pgrid">{pg}</div>

  <!-- FORM BAR -->
  {form_html}

  <!-- FIGHT HISTORY -->
  <div class="card" style="overflow:hidden">
    <table class="tbl"><thead><tr>
      <th>ผล</th><th>คู่ต่อสู้</th><th class="col-hide-sm">วิธี/ยก</th><th class="col-hide-sm">กติกา</th><th class="col-hide-sm">อีเวนต์</th><th>วันที่</th>
    </tr></thead><tbody>
    {rows if rows else empty_row}
    </tbody></table>
  </div>

  {more_html}

  <a class="back" href="../profile.html?id={fid}" style="margin-top:18px;background:var(--red);color:#fff;border-color:var(--red)">ดูข้อมูลเต็ม + เปรียบเทียบสถิติ →</a>

  {bio_html}
</div>

<!-- FOOTER -->
<footer style="border-top:1px solid var(--line);background:var(--footer-bg);margin-top:30px">
  <div style="max-width:1100px;margin:0 auto;padding:30px 26px;text-align:center">
    <div style="font-family:var(--sans);font-weight:800;font-size:24px;color:var(--tx);text-transform:uppercase">BOX<span style="color:var(--red)">FAN</span></div>
    <div style="font-size:10px;color:var(--tx-4);font-weight:700;letter-spacing:.26em;text-transform:uppercase;margin-top:2px">ผลมวยทุกสังเวียน</div>
    <div style="margin:16px 0 10px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px 18px">
      <a href="../about.html" style="font-size:13px;color:var(--tx-2);font-weight:500">เกี่ยวกับเรา</a>
      <a href="../contact.html" style="font-size:13px;color:var(--tx-2);font-weight:500">ติดต่อเรา</a>
      <a href="../privacy.html" style="font-size:13px;color:var(--tx-2);font-weight:500">นโยบายความเป็นส่วนตัว</a>
      <a href="../disclaimer.html" style="font-size:13px;color:var(--tx-2);font-weight:500">ข้อจำกัดความรับผิด</a>
    </div>
    <div style="font-size:11.5px;color:var(--tx-4)">© 2025 Boxfan · รวมผลมวยจากทุกรายการ บันทึกโดยแฟนมวย</div>
  </div>
</footer>

<script>
(function(){{try{{var s=localStorage.getItem('boxfan-theme');if(s==='dark')document.documentElement.setAttribute('data-theme','dark');}}catch(e){{}}}})();
</script>
</body>
</html>'''


# ═══════════════════════════════════════════════════════════
# ตรวจความเรียบร้อยก่อน/หลังเจน
# ═══════════════════════════════════════════════════════════
def check_fighters_page():
    """เตือนถ้าหน้ารวมนักมวยที่ลิงก์ไปหาไม่มีอยู่จริง หรือสะกดตัวพิมพ์ไม่ตรง"""
    target = os.path.join(ROOT, FIGHTERS_PAGE)
    if os.path.isfile(target):
        # เทียบชื่อจริงบนดิสก์ เพื่อจับกรณี Windows เปิดผ่านแต่ Linux 404
        try:
            actual = [n for n in os.listdir(ROOT) if n.lower() == FIGHTERS_PAGE.lower()]
        except OSError:
            return
        if actual and actual[0] != FIGHTERS_PAGE:
            print('⚠️   ลิงก์ชี้ไป "%s" แต่ไฟล์จริงชื่อ "%s"' % (FIGHTERS_PAGE, actual[0]))
            print('       ตัวพิมพ์ไม่ตรง = 404 บน GitHub Pages / Netlify / เซิร์ฟเวอร์ Linux')
            print('       แก้ชื่อไฟล์ให้เป็น %s หรือแก้ค่า FIGHTERS_PAGE ในสคริปต์' % FIGHTERS_PAGE)
            print()
    else:
        print('⚠️   ไม่พบ %s — ปุ่ม "← นักมวยทั้งหมด" จะกดไม่ติด' % target)
        print()


def check_uppercase(fighters):
    """เตือนถ้าชื่อไฟล์มีตัวพิมพ์ใหญ่ปน (เสี่ยง 404 บนโฮสต์ที่แยกตัวพิมพ์)"""
    ups = [f['_page'] for f in fighters if f['_page'] != f['_page'].lower()]
    if ups:
        print('⚠️   ชื่อไฟล์ %d หน้ามีตัวพิมพ์ใหญ่ปน — ต้องแน่ใจว่าลิงก์ในเว็บสะกดตรงกันเป๊ะ' % len(ups))
        for name in ups[:5]:
            print('       %s.html' % name)
        if len(ups) > 5:
            print('       …และอีก %d หน้า' % (len(ups) - 5))
        print()


# ═══════════════════════════════════════════════════════════
def main():
    path = find_data_file()
    if not path:
        print('❌  ไม่พบ %s' % DATA_FILENAME)
        print()
        print('    หาไว้ที่:')
        for folder in (os.path.join(ROOT, 'data'), os.path.join(BASE, 'data'), BASE, ROOT):
            print('      ' + os.path.join(folder, DATA_FILENAME))
        print()
        print('    วิธีแก้: รัน export_json.py ก่อน หรือระบุทางเอง')
        print('      python generate_profiles.py C:/path/to/fighters_data.js')
        return 1

    print('📄  ไฟล์ข้อมูล : %s' % os.path.abspath(path))
    print('🕐  แก้ล่าสุด  : %s' % _mtime_str(path))
    try:
        fighters, hmap, meta = load_from_js(path)
    except (OSError, ValueError, json.JSONDecodeError) as err:
        print('❌  อ่านไฟล์ไม่สำเร็จ: %s' % err)
        return 1

    if not fighters:
        print('❌  ไม่มีข้อมูลนักมวยในไฟล์')
        return 1

    total_fights = sum(len(v) for v in hmap.values())
    if meta.get('generated_at'):
        print('📊  export เมื่อ : %s  (%s คน)'
              % (meta['generated_at'], meta.get('fighter_count', len(fighters))))
    print('👤  อ่านได้    : %d คน / %d ไฟต์' % (len(fighters), total_fights))
    print()

    warn_if_stale(path)
    check_fighters_page()

    full_css = load_external_css() + '\n' + load_profile_css()

    # ── ขั้นที่ 1: กำหนดชื่อไฟล์ให้ครบทุกคนก่อน ──
    # ต้องทำก่อนเจน เพราะลิงก์คู่ต่อสู้ต้องรู้ชื่อไฟล์ตัวจริงของอีกฝ่าย
    dups = assign_page_names(fighters)
    for who, old, new in dups:
        print('⚠️   ชื่อไฟล์ซ้ำ: %s (%s) -> เปลี่ยนเป็น %s.html' % (who, old, new))
    if dups:
        print()
    check_uppercase(fighters)

    # แผนที่ ชื่อ -> นักมวย สำหรับหารูปและลิงก์ของคู่ต่อสู้
    fighters_map = {}
    for ff in fighters:
        for key in ('name_th', 'name_en'):
            if ff.get(key):
                fighters_map[ff[key]] = ff

    os.makedirs(OUT, exist_ok=True)
    before = set(n for n in os.listdir(OUT) if n.lower().endswith('.html'))

    # ── ขั้นที่ 2: เจนทุกหน้า (ยังไม่ลบอะไรทั้งนั้น) ──
    print('🏷️   โหมดตั้งชื่อไฟล์: %s' % FILENAME_MODE)
    written, failed = [], []
    for f in fighters:
        fname = '%s.html' % f['_page']
        try:
            content = generate(f, hmap.get(f.get('id'), []), full_css, fighters_map)
            with open(os.path.join(OUT, fname), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(content)
            written.append((fname, f.get('name_th') or f.get('id')))
        except Exception as err:                       # noqa: BLE001 — คนเดียวพังไม่ควรล้มทั้งชุด
            failed.append((f.get('name_th') or f.get('id'), err))

    print()
    print('✅  สร้าง %d หน้านักมวย (%d ไฟต์) → %s' % (len(written), total_fights, OUT))

    if failed:
        print('❌  เจนไม่สำเร็จ %d คน:' % len(failed))
        for who, err in failed[:10]:
            print('       %s — %s' % (who, err))

    # ── ขั้นที่ 3: เจนครบแล้วค่อยเก็บกวาดหน้าที่ตกค้าง ──
    # (ถ้าลบก่อนแล้วสคริปต์พังกลางทาง หน้าเก่าจะหายเกลี้ยงโฟลเดอร์)
    current = set(n for n, _ in written)
    stale = sorted(before - current)
    if stale and not failed:
        for n in stale:
            try:
                os.remove(os.path.join(OUT, n))
            except OSError as err:
                print('⚠️   ลบ %s ไม่ได้: %s' % (n, err))
        print('🧹  ลบหน้าที่ไม่มีในข้อมูลแล้ว %d ไฟล์: %s'
              % (len(stale), ', '.join(stale[:10]) + ('…' if len(stale) > 10 else '')))
    elif stale and failed:
        print('⏸️   ข้ามการลบหน้าเก่า %d ไฟล์ เพราะมีหน้าที่เจนไม่สำเร็จ' % len(stale))

    fresh = [n for n, _ in written if n not in before]
    if fresh and before:
        who_of = dict(written)
        print('🆕  หน้าใหม่ %d คน:' % len(fresh))
        for fname in fresh[:20]:
            print('       %s  (%s)' % (fname, who_of.get(fname, '')))
        if len(fresh) > 20:
            print('       …และอีก %d คน' % (len(fresh) - 20))

    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
