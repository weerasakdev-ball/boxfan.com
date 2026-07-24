"""
BOXFAN — generate_profiles.py v4
สร้าง static HTML โปรไฟล์ self-contained (CSS ในตัว ไม่พึ่งไฟล์นอก)
ดีไซน์เหมือน profile.html ต้นฉบับ 100%

v4: อ่านข้อมูลจากโฟลเดอร์ไฟล์ JSON โดยตรง (ไม่ใช้ fighters.db แล้ว)

วิธีรัน:
    python generate_profiles.py                 # อ่าน ./data
    python generate_profiles.py C:/path/to/data # ระบุโฟลเดอร์เอง
"""
import json, os, re, sys, html as H
from datetime import datetime, date
from urllib.parse import quote

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE) if os.path.basename(BASE) == 'data' else BASE
OUT  = os.path.join(ROOT, 'fighters')
SITE = 'https://www.boxingfandom.com'
CLOUD = 'dpvyl7nan'

# ไฟล์ข้อมูลรวม — ระบุทาง argument ได้ ถ้าไม่ระบุจะหาให้เอง
DATA_FILENAME = 'fighters_data.js'

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


SEARCH_FOLDERS = ('data', '.', '..', os.path.join('..', 'data'))


def _mtime_str(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
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
        found.sort(key=lambda x: os.path.getmtime(x), reverse=True)
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
    except Exception:
        return
    newer, folder_hit = 0, None
    for base in (ROOT, BASE, os.path.dirname(data_path)):
        for rel in ('data', '.'):
            folder = os.path.normpath(os.path.join(base, rel))
            if not os.path.isdir(folder):
                continue
            try:
                names = os.listdir(folder)
            except Exception:
                continue
            count = 0
            for n in names:
                if not n.lower().endswith('.json') or n.startswith('_') or n.endswith('.bak.json'):
                    continue
                try:
                    if os.path.getmtime(os.path.join(folder, n)) > data_mtime:
                        count += 1
                except Exception:
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

# ═══════════════════════════════════════════════════
# แปลงผลการแข่งภาษาไทย -> รหัสอังกฤษที่เทมเพลตใช้
# ═══════════════════════════════════════════════════
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

FLAGS = {
    'ไทย':'🇹🇭','ญี่ปุ่น':'🇯🇵','เกาหลีใต้':'🇰🇷','จีน':'🇨🇳',
    'บราซิล':'🇧🇷','ฟิลิปปินส์':'🇵🇭','รัสเซีย':'🇷🇺','อิตาลี':'🇮🇹',
    'ฝรั่งเศส':'🇫🇷','อังกฤษ':'🇬🇧','สหรัฐ':'🇺🇸','แคนาดา':'🇨🇦',
    'ออสเตรเลีย':'🇦🇺','เนเธอร์แลนด์':'🇳🇱','สเปน':'🇪🇸',
    'เมียนมาร์':'🇲🇲','กัมพูชา':'🇰🇭','มาเลเซีย':'🇲🇾',
    'อินโดนีเซีย':'🇮🇩','อินเดีย':'🇮🇳','มองโกเลีย':'🇲🇳',
    'คาซัคสถาน':'🇰🇿','จอร์เจีย':'🇬🇪','อุซเบกิสถาน':'🇺🇿',
    'ตุรกี':'🇹🇷','โมร็อกโก':'🇲🇦','แอลจีเรีย':'🇩🇿',
    'อาร์เจนตินา':'🇦🇷','เม็กซิโก':'🇲🇽','โคลอมเบีย':'🇨🇴',
    'เยอรมนี':'🇩🇪','โปแลนด์':'🇵🇱','ยูเครน':'🇺🇦',
    'เบลารุส':'🇧🇾','โรมาเนีย':'🇷🇴','เช็ก':'🇨🇿',
    'สวีเดน':'🇸🇪','นอร์เวย์':'🇳🇴','เดนมาร์ก':'🇩🇰',
    'ไอร์แลนด์':'🇮🇪','นิวซีแลนด์':'🇳🇿','แอฟริกาใต้':'🇿🇦',
    'ซาอุดีอาระเบีย':'🇸🇦','อิหร่าน':'🇮🇷','ปากีสถาน':'🇵🇰',
    'เวียดนาม':'🇻🇳','ลาว':'🇱🇦','สิงคโปร์':'🇸🇬',
    'เบลเยียม':'🇧🇪','ออสเตรีย':'🇦🇹','สวิตเซอร์แลนด์':'🇨🇭',
    'โปรตุเกส':'🇵🇹','กรีซ':'🇬🇷','ทาจิกิสถาน':'🇹🇯',
    'คีร์กีซสถาน':'🇰🇬','ฮ่องกง':'🇭🇰','ไต้หวัน':'🇹🇼',
}

def slug(f):
    """
    ชื่อไฟล์หน้าโปรไฟล์
    ถ้าข้อมูลมีช่อง slug มาให้แล้ว (จาก export_json.py) ให้ใช้ตัวนั้นเสมอ
    เพื่อให้ชื่อไฟล์ตรงกับลิงก์บนเว็บ 100%
    """
    if f.get('slug'):
        return f['slug']
    return _slug_fallback(f)


def _slug_fallback(f):
    """สร้าง slug จากชื่ออังกฤษ หรือชื่อไทยถ้าไม่มีอังกฤษ"""
    name = (f.get('name_en') or '').strip() or (f.get('name_th') or '').strip() or str(f.get('id') or 'fighter')
    s = name.strip()
    # English: lowercase
    if all(ord(c) < 128 or c in ' -' for c in s):
        s = s.lower()
    s = re.sub(r'[\s]+', '-', s)
    s = re.sub(r'[/\\:*?"<>|]', '', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

FLAGS.update({
    'สหรัฐอเมริกา':'🇺🇸','สหราชอาณาจักร':'🇬🇧','เมียนมา':'🇲🇲','ไอซ์แลนด์':'🇮🇸',
    'เช็กเกีย':'🇨🇿','สกอตแลนด์':'🏴󠁧󠁢󠁳󠁣󠁴󠁿','เวลส์':'🏴󠁧󠁢󠁷󠁬󠁳󠁿','ฟินแลนด์':'🇫🇮','ฮังการี':'🇭🇺',
    'บัลแกเรีย':'🇧🇬','โครเอเชีย':'🇭🇷','เซอร์เบีย':'🇷🇸','สโลวาเกีย':'🇸🇰','สโลวีเนีย':'🇸🇮',
    'บอสเนียและเฮอร์เซโกวีนา':'🇧🇦','อาเซอร์ไบจาน':'🇦🇿','อาร์เมเนีย':'🇦🇲',
    'อิสราเอล':'🇮🇱','อิรัก':'🇮🇶','ซีเรีย':'🇸🇾','เลบานอน':'🇱🇧','จอร์แดน':'🇯🇴',
    'คูเวต':'🇰🇼','สหรัฐอาหรับเอมิเรตส์':'🇦🇪','กาตาร์':'🇶🇦','บาห์เรน':'🇧🇭','โอมาน':'🇴🇲',
    'อียิปต์':'🇪🇬','ตูนิเซีย':'🇹🇳','ไนจีเรีย':'🇳🇬','เคนยา':'🇰🇪','แคเมอรูน':'🇨🇲',
    'เซเนกัล':'🇸🇳','กานา':'🇬🇭','ชิลี':'🇨🇱','เปรู':'🇵🇪','เวเนซุเอลา':'🇻🇪',
    'อุรุกวัย':'🇺🇾','คิวบา':'🇨🇺','จาเมกา':'🇯🇲','บรูไน':'🇧🇳','มาเก๊า':'🇲🇴',
    'เนปาล':'🇳🇵','บังกลาเทศ':'🇧🇩','ศรีลังกา':'🇱🇰','อัฟกานิสถาน':'🇦🇫',
    'มัลดีฟส์':'🇲🇻','เติร์กเมนิสถาน':'🇹🇲','มอลโดวา':'🇲🇩','ลิทัวเนีย':'🇱🇹',
    'ลัตเวีย':'🇱🇻','เอสโตเนีย':'🇪🇪','แอลเบเนีย':'🇦🇱','มอนเตเนโกร':'🇲🇪',
    'มาซิโดเนียเหนือ':'🇲🇰','โคโซโว':'🇽🇰','ไซปรัส':'🇨🇾','มอลตา':'🇲🇹',
})


def page_name(f):
    """ชื่อไฟล์ HTML ของนักมวยคนนี้ (ไม่รวม .html) ตาม FILENAME_MODE"""
    if FILENAME_MODE == 'id':
        return str(f.get('id') or slug(f))
    return f.get('slug') or slug(f)


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
def esc(s): return H.escape(str(s)) if s else ''

def derive_stats(fighter, history):
    """
    เติมสถิติที่เทมเพลตต้องใช้ (total_wins / total_losses / total_nc /
    total_fights / win_rate / ko_wins) โดยนับจากประวัติการชกจริง
    ไฟต์ที่ยัง "รอแข่งขัน" ไม่ถูกนับ
    """
    past = [h for h in history if h.get('result_type') != 'upcoming']
    wins   = sum(1 for h in past if h.get('result_type') == 'win')
    losses = sum(1 for h in past if h.get('result_type') == 'loss')
    draws  = sum(1 for h in past if h.get('result_type') == 'draw')
    nc     = sum(1 for h in past if h.get('result_type') == 'nc')
    total  = len(past)
    fighter['total_wins']   = wins
    fighter['total_losses'] = losses
    fighter['total_draws']  = draws
    fighter['total_nc']     = nc
    fighter['total_fights'] = total
    fighter['win_rate']     = round(wins / (wins + losses) * 100) if (wins + losses) else 0
    fighter['ko_wins']      = sum(1 for h in past if h.get('result_type') == 'win' and is_finish(h))
    return fighter


def fighters_count(fighters):
    return len(fighters)


def load_from_js(path):
    """
    อ่าน fighters_data.js แล้วคืน (fighters, history_map, meta)
    ใช้ข้อมูลชุดเดียวกับที่เว็บใช้ จึงไม่มีทางไม่ตรงกัน
    """
    with open(path, 'r', encoding='utf-8-sig') as fh:
        text = fh.read()

    fighters = extract_js_const(text, 'FIGHTERS')
    history  = extract_js_const(text, 'HISTORY')
    meta     = extract_js_const(text, 'META') or {}

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
    if not fn: return ''
    clean = re.sub(r'\.(jpg|jpeg|png|webp)$', '', fn, flags=re.IGNORECASE)
    d = {'sm':'w_80,h_80,g_face','md':'w_160,h_160,g_face','lg':'w_300,h_375,g_north'}
    return f'https://res.cloudinary.com/{CLOUD}/image/upload/c_fill,{d.get(size,d["lg"])},f_auto,q_auto/{clean}'

# ═══ ดึง CSS จาก profile.html ต้นฉบับ ═══
# อ่านจากไฟล์จริงเพื่อให้ตรง 100%
def load_profile_css():
    """อ่าน CSS ทั้งหมดจาก profile.html ต้นฉบับ"""
    profile_path = os.path.join(ROOT, 'profile.html')
    if not os.path.exists(profile_path):
        print(f'⚠️  ไม่พบ {profile_path} — ใช้ CSS fallback')
        return None
    with open(profile_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # ดึง <style>...</style> ทั้งหมด
    blocks = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
    return '\n'.join(blocks)

# ═══ ดึง CSS จาก style.css + boxfan-tokens.css ═══
def load_external_css():
    """อ่าน CSS จากไฟล์ภายนอกที่ profile.html อ้างถึง"""
    css = ''
    for fn in ['style.css', 'boxfan-tokens.css']:
        path = os.path.join(ROOT, fn)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                css += f'\n/* ── {fn} ── */\n' + f.read()
    return css


def generate(f, history, full_css, fighters_map):
    name_th = esc(f.get('name_th',''))
    name_en = esc(f.get('name_en',''))
    country = esc(f.get('country',''))
    division = esc(f.get('division',''))
    team = esc(f.get('team',''))
    wins = f.get('total_wins',0)
    losses = f.get('total_losses',0)
    nc = f.get('total_nc',0) or 0
    total = f.get('total_fights',0)
    wr = f.get('win_rate',0) or 0
    bio = esc(f.get('biography',''))
    age = f.get('age','')
    img = cimg(f.get('image_filename'),'lg')
    fid = quote(str(f['id']), safe='')   # id เป็นข้อความไทย ต้อง encode ก่อนใส่ URL
    s = quote(page_name(f), safe='')     # ชื่อไฟล์สำหรับ canonical URL

    title = f'{name_th} ({name_en}) สถิตินักมวย | Boxfan' if name_en else f'{name_th} สถิตินักมวย | Boxfan'
    desc = f'{name_th} นักมวย ONE Championship {division} สถิติ {wins}W {losses}L อัตราชนะ {wr}% | Boxfan'
    canonical = f'{SITE}/fighters/{s}.html'

    past = [h for h in history if h.get('result_type') != 'upcoming']
    past.sort(key=lambda x: x.get('date',''), reverse=True)
    up = [h for h in history if h.get('result_type') == 'upcoming']
    # คะแนน: ต้องใช้สูตรเดียวกับ score() ใน utils.js ไม่งั้นตัวเลขจะไม่ตรงกับหน้าอันดับ
    #   ชนะ +3 · ชนะน็อก/ซับมิชชันในยกแรก +1 · แพ้ -3
    sc = 0
    for h in past:
        if h.get('result_type') == 'win':
            sc += 3
            if str(h.get('round')) == '1' and is_finish(h):
                sc += 1
        elif h.get('result_type') == 'loss':
            sc -= 3

    # Days since last fight
    days_rest = ''
    if past:
        from datetime import datetime, date
        try:
            last_date = datetime.strptime(past[0].get('date',''), '%Y-%m-%d').date()
            delta = (date.today() - last_date).days
            days_rest = f'<span class="htag">พัก {delta} วัน</span>'
        except: pass

    # Form bar
    form = ''
    for h in reversed(past[:10]):
        r = h.get('result_type','')
        if r == 'win': form += '<div class="fseg win">W</div>'
        elif r == 'loss': form += '<div class="fseg loss">L</div>'
        else: form += '<div class="fseg nc">NC</div>'

    # Tags
    tags = ''
    if country: tags += f'<span class="htag">{fl(f.get("country",""))} {country}</span>'
    if team: tags += f'<span class="htag">{team}</span>'
    if age: tags += f'<span class="htag">อายุ {age} ปี</span>'
    tags += f'<span class="htag htag-pts">{sc} pts</span>'
    if days_rest: tags += f' {days_rest}'

    # Physical grid
    pg = ''
    if f.get('height_ft_in'): pg += f'<div class="pitem"><div class="pval">{f["height_ft_in"]}</div><div class="plbl">ส่วนสูง</div></div>'
    if f.get('height_cm'): pg += f'<div class="pitem"><div class="pval">{f["height_cm"]}</div><div class="plbl">ซม.</div></div>'
    if f.get('weight_lbs'): pg += f'<div class="pitem"><div class="pval">{f["weight_lbs"]}</div><div class="plbl">ปอนด์</div></div>'
    if f.get('weight_kg'): pg += f'<div class="pitem"><div class="pval">{f["weight_kg"]}</div><div class="plbl">กก.</div></div>'
    pg += f'<div class="pitem accent"><div class="pval">{sc}</div><div class="plbl">คะแนน</div></div>'
    pg += f'<div class="pitem"><div class="pval">{total}</div><div class="plbl">แมตช์รวม</div></div>'

    # NC record
    nc_html = ''
    if nc > 0:
        nc_html = f'<div class="rsep">–</div><div><div class="rn n">{nc}</div><div class="rl">NC</div></div>'

    # Fight table rows
    PH_IMG = 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2250%22 height=%2250%22><rect fill=%22%23232d3b%22 width=%2250%22 height=%2250%22 rx=%228%22/></svg>'
    rows = ''
    for h in (up + past[:10]):
        r = h.get('result_type','')
        if r == 'win': badge = '<span class="bw">ชนะ</span>'
        elif r == 'loss': badge = '<span class="bl">แพ้</span>'
        elif r == 'upcoming': badge = '<span class="bu">รอผล</span>'
        else: badge = '<span class="bn">NC</span>'
        opp_name = h.get('opponent','—')
        opp = esc(opp_name)
        date = esc(h.get('date','—'))
        event = esc(h.get('event','—'))
        decision = esc(h.get('decision',''))
        rules = esc(h.get('rules',''))
        rnd = h.get('round','')
        time = h.get('time','')
        opp_country = h.get('opponent_country','')
        method = f'<span class="deco-pill">{decision}</span>' if decision else '<span class="dash">—</span>'
        if rnd: method += f'<div style="font-size:11px;color:var(--tx-3);margin-top:3px">ยก {rnd}{" · "+time if time else ""}</div>'

        # Opponent image + link lookup
        opp_f = fighters_map.get(opp_name)
        if opp_f:
            opp_img = cimg(opp_f.get('image_filename'), 'sm') or PH_IMG
            opp_link = '../fighters/%s.html' % quote(page_name(opp_f), safe='')
            opp_td = f'''<td><div class="opp-row"><a href="{opp_link}"><img class="opp-av" src="{opp_img}" loading="lazy" alt="{opp}"></a><div><a href="{opp_link}" class="opp-name-link">{opp}</a>'''
        else:
            opp_td = f'''<td><div class="opp-row"><img class="opp-av no-link" src="{PH_IMG}" alt=""><div><span class="opp-name-nolink">{opp}</span>'''

        if opp_country and opp_country != '-':
            opp_td += f'<div style="font-size:11px;color:var(--tx-3)">{fl(opp_country)} {esc(opp_country)}</div>'
        opp_td += '</div></div></td>'

        rows += f'''<tr>
<td>{badge}</td>
{opp_td}
<td class="col-hide-sm">{method}</td>
<td class="col-hide-sm" style="color:var(--tx-3);font-size:12px">{rules or "—"}</td>
<td class="col-hide-sm" style="font-size:12px">{event}</td>
<td style="color:var(--tx-3);font-size:12px;white-space:nowrap">{date}</td>
</tr>'''

    jsonld = json.dumps({"@context":"https://schema.org","@type":"Person","name":f.get('name_th',''),"alternateName":f.get('name_en') or None,"description":f'{name_th} นักมวย ONE Championship {division}',"image":img,"url":canonical,"nationality":f.get('country') or None,"sport":"Muay Thai / Kickboxing / MMA","memberOf":{"@type":"SportsOrganization","name":"ONE Championship"}}, ensure_ascii=False)

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
    <a class="nav-tab" href="../Fighters.html">นักมวยทั้งหมด</a>
    <a class="nav-tab" href="../schedule.html">โปรแกรมชก</a>
    <a class="nav-tab" href="../results.html">ผลการแข่งขัน</a>
    <a class="nav-tab" href="../compare.html">เปรียบเทียบ</a>
    <a class="nav-tab" href="../blog/">บทความ</a>
    <a class="nav-tab" href="../tierlist.html">Tier List</a>
  </div>
</nav>

<div class="page">
  <a class="back" href="../Fighters.html">← นักมวยทั้งหมด</a>

  <!-- HERO -->
  <div class="hero">
    <div class="hav-wrap">
      <img class="hav" src="{img}" alt="{name_th}" loading="eager">
      {'<div class="hflag">' + fl(f.get("country","")) + '</div>' if country else ''}
    </div>
    <div class="hinfo">
      {'<div class="hdiv">' + division + '</div>' if division else ''}
      <h1 class="hname">{name_th}</h1>
      {'<div class="hname-en">' + name_en + '</div>' if name_en else ''}
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
  {('<div class="form-label">ฟอร์มล่าสุด ' + str(min(len(past),10)) + ' แมตช์</div><div class="fbar">' + form + '</div>') if form else ''}

  <!-- FIGHT HISTORY -->
  <div class="card" style="overflow:hidden">
    <table class="tbl"><thead><tr>
      <th>ผล</th><th>คู่ต่อสู้</th><th class="col-hide-sm">วิธี/ยก</th><th class="col-hide-sm">กติกา</th><th class="col-hide-sm">อีเวนต์</th><th>วันที่</th>
    </tr></thead><tbody>
    {rows if rows else '<tr><td colspan="6" style="padding:32px;text-align:center;color:var(--tx-3)">ยังไม่มีประวัติการชก</td></tr>'}
    </tbody></table>
  </div>

  {('<div style="margin-top:8px;font-size:12px;color:var(--tx-4);text-align:center">แสดง ' + str(min(len(past),10)+len(up)) + ' จาก ' + str(len(past)+len(up)) + ' แมตช์</div>') if len(past) > 10 else ''}

  <a class="back" href="../profile.html?id={fid}" style="margin-top:18px;background:var(--red);color:#fff;border-color:var(--red)">ดูข้อมูลเต็ม + เปรียบเทียบสถิติ →</a>

  {('<div style="margin-top:18px;padding:24px;background:var(--surf);border:1px solid var(--line-2);border-radius:11px;box-shadow:var(--sh-2)"><div style="font-family:var(--sans);font-size:15px;font-weight:800;color:var(--tx);margin-bottom:12px;display:flex;align-items:center;gap:8px;text-transform:uppercase"><span style="color:var(--gold)">★</span> ประวัตินักมวย</div><p style="line-height:1.9;color:var(--tx-2);font-size:14px;margin:0">' + bio + '</p></div>') if bio else ''}
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
        return

    print('📄  ไฟล์ข้อมูล : %s' % os.path.abspath(path))
    print('🕐  แก้ล่าสุด  : %s' % _mtime_str(path))
    try:
        fighters, hmap, meta = load_from_js(path)
    except Exception as err:
        print('❌  อ่านไฟล์ไม่สำเร็จ: %s' % err)
        return

    if not fighters:
        print('❌  ไม่มีข้อมูลนักมวยในไฟล์')
        return
    if meta.get('generated_at'):
        print('📊  export เมื่อ : %s  (%s คน)' % (meta['generated_at'], meta.get('fighter_count', len(fighters))))
    print('👤  อ่านได้    : %d คน / %d ไฟต์' % (fighters_count(fighters), sum(len(v) for v in hmap.values())))
    print()
    warn_if_stale(path)

    # โหลด CSS จาก profile.html + style.css + boxfan-tokens.css
    profile_css = load_profile_css() or ''
    external_css = load_external_css()
    full_css = external_css + '\n' + profile_css

    # แผนที่ ชื่อ -> นักมวย สำหรับหารูปและลิงก์ของคู่ต่อสู้
    fighters_map = {}
    for ff in fighters:
        for key in ('name_th', 'name_en'):
            if ff.get(key):
                fighters_map[ff[key]] = ff

    os.makedirs(OUT, exist_ok=True)
    old_files = set(x for x in os.listdir(OUT) if x.endswith('.html'))
    for x in old_files:
        os.remove(os.path.join(OUT, x))
    if old_files:
        print('🧹  ลบหน้าเก่า %d ไฟล์' % len(old_files))

    print('🏷️   โหมดตั้งชื่อไฟล์: %s' % FILENAME_MODE)
    count, used_slugs, made = 0, {}, []
    for f in fighters:
        s = page_name(f)
        # กันชื่อไฟล์ซ้ำ (นักมวยคนละคนแต่ชื่อไฟล์ตรงกัน)
        if s in used_slugs:
            used_slugs[s] += 1
            s = '%s-%d' % (s, used_slugs[s])
            print('⚠️   ชื่อไฟล์ซ้ำ: %s -> เปลี่ยนเป็น %s.html' % (f.get('name_th'), s))
        else:
            used_slugs[s] = 1
        fname = '%s.html' % s
        target = os.path.join(OUT, fname)
        content = generate(f, hmap.get(f['id'], []), full_css, fighters_map)
        with open(target, 'w', encoding='utf-8') as fh:
            fh.write(content)
        made.append((fname, f.get('name_th') or f.get('id')))
        count += 1

    total_fights = sum(len(v) for v in hmap.values())
    print()
    print('✅  สร้าง %d หน้านักมวย (%d ไฟต์) → %s' % (count, total_fights, OUT))

    # หน้าที่ไม่เคยมีมาก่อน (เทียบกับรอบก่อนหน้า)
    fresh = [n for n, _ in made if n not in old_files]
    if fresh and old_files:
        print('🆕  หน้าใหม่ %d คน:' % len(fresh))
        for fname in fresh[:20]:
            who = dict(made).get(fname, '')
            print('       %s  (%s)' % (fname, who))
        if len(fresh) > 20:
            print('       …และอีก %d คน' % (len(fresh) - 20))
    gone = [n for n in old_files if n not in set(x for x, _ in made)]
    if gone:
        print('🗑️   หน้าที่หายไป %d ไฟล์ (ไม่มีในข้อมูลแล้ว): %s' % (len(gone), ', '.join(sorted(gone)[:10])))


if __name__ == '__main__':
    main()