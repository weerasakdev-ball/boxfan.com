#!/usr/bin/env python3
"""
build_index.py — สร้างไฟล์สารบัญ data/fighters_index.js จาก data/fighters_data.js

ทำไมต้องมี:
  fighters_data.js ใหญ่มาก (30+ MB) มือถือต้องอ่านทั้งก้อนก่อนหน้าเว็บจะขึ้น
  หน้าแรก/รายชื่อ/อันดับ/ผลมวย/โปรแกรมชก ใช้ข้อมูลแค่บางช่อง จึงให้หน้าพวกนี้โหลดสารบัญแทน

กติกา:
  - ไม่แตะ fighters_data.js เลย (อ่านอย่างเดียว) — ข้อมูลเต็มยังอยู่ครบทุกช่อง
  - สารบัญสร้างใหม่ทั้งไฟล์ทุกครั้งจากข้อมูลล่าสุด (generate_profiles.bat เรียกให้เอง)
  - ช่องที่ไม่ใส่ในสารบัญ = DROP ด้านล่าง (หน้าที่ใช้สารบัญไม่ได้ใช้ช่องพวกนี้)
    ช่องใหม่ที่เพิ่มในอนาคตจะติดมาในสารบัญเองอัตโนมัติ
  - ย่อขนาด: ไม่เขียนค่า null และไม่เขียน slug/image_filename ที่ซ้ำกับ id
    แล้วมีโค้ดเล็ก ๆ ท้ายไฟล์เติมกลับตอนเปิดหน้า → หน้าเว็บเห็นข้อมูลเหมือนไฟล์เต็ม
  - ตรวจซ้ำทุกครั้ง: อ่านไฟล์ที่เขียนเสร็จกลับมา เติมค่ากลับแบบเดียวกับหน้าเว็บ
    แล้วเทียบกับข้อมูลเต็มทีละคนทีละไฟต์ ถ้าไม่ตรงแม้แต่ช่องเดียว → หยุด ไม่เขียนทับไฟล์เดิม

ถ้าหน้าไหนที่ใช้สารบัญต้องการช่องใน DROP → เอาชื่อช่องออกจาก DROP แล้วรันใหม่
"""

import json
import os
import re
import sys
from pathlib import Path

try:  # หน้าจอ Windows บางเครื่องพิมพ์ภาษาไทยไม่ได้
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'data' / 'fighters_data.js'
OUT = ROOT / 'data' / 'fighters_index.js'

# ช่องที่ไม่ใส่ในสารบัญ (หน้าที่ใช้ข้อมูลพวกนี้ เช่น stats/compare/profile ยังโหลดไฟล์เต็ม)
DROP = {
    'thboxing_url', 'profile_url', 'strike_stats', 'market_value', 'fight_purse',
    'biography', 'last_updated', 'level', 'height_ft_in', 'weight_lbs',
}
# ช่องที่ส่วนใหญ่มีค่าเท่ากับ id — ไม่เขียนซ้ำ เติมกลับจาก id
SAME_AS_ID = ['slug', 'image_filename']


def fail(msg):
    print()
    print('  ✗ สร้างสารบัญไม่สำเร็จ: ' + msg)
    print('    ไฟล์สารบัญเดิมไม่ถูกแก้ — อย่าเพิ่ง push ขึ้นเว็บ ส่งข้อความนี้ให้คนดูแลเว็บ')
    sys.exit(1)


def extract_js_const(text, name):
    """ดึงค่า const NAME = [...] / {...} ออกมาเป็น Python (แบบเดียวกับ build_seo.py)"""
    m = re.search(r'(?:const|var|let)\s+' + re.escape(name) + r'\s*=\s*', text)
    if not m:
        return None
    i = m.end()
    open_ch = text[i]
    if open_ch not in '[{':
        return None
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


def common_keys(rows):
    """ช่องที่มีในทุกแถว — เฉพาะช่องพวกนี้ที่ละ null ได้ (เติมกลับได้แน่นอน)"""
    keys = None
    for r in rows:
        keys = set(r) if keys is None else keys & set(r)
    return keys or set()


def pack(row, nullable, same_as_id):
    out = {}
    for k, v in row.items():
        if k in same_as_id and v is not None and v == row.get('id'):
            continue
        if v is None and k in nullable:
            continue
        out[k] = v
    return out


def unpack(row, nullable, same_as_id):
    """ทำแบบเดียวกับโค้ด JS ท้ายไฟล์สารบัญ (ใช้ตรวจผล)"""
    r = dict(row)
    for k in same_as_id:
        if k not in r:
            r[k] = r.get('id')
    for k in nullable:
        if k not in r:
            r[k] = None
    return r


def dumps(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'))


def main():
    if not SRC.exists():
        fail('ไม่พบ %s' % SRC)
    text = SRC.read_text(encoding='utf-8-sig')
    fighters = extract_js_const(text, 'FIGHTERS')
    history = extract_js_const(text, 'HISTORY')
    meta = extract_js_const(text, 'META')
    if not fighters:
        fail('อ่านรายชื่อนักมวย (FIGHTERS) ใน fighters_data.js ไม่ได้')
    if history is None:
        fail('อ่านประวัติการชก (HISTORY) ใน fighters_data.js ไม่ได้')
    meta = meta or {}

    # ตรวจว่าไฟล์ข้อมูลเต็มครบตามที่โปรแกรมส่งออกบอกไว้
    if meta.get('fighter_count') is not None and meta['fighter_count'] != len(fighters):
        fail('จำนวนนักมวยในไฟล์ (%d) ไม่ตรงกับที่ระบุไว้ (%d) — ไฟล์ข้อมูลอาจส่งออกไม่ครบ'
             % (len(fighters), meta['fighter_count']))
    if meta.get('fight_count') is not None and meta['fight_count'] != len(history):
        fail('จำนวนไฟต์ในไฟล์ (%d) ไม่ตรงกับที่ระบุไว้ (%d) — ไฟล์ข้อมูลอาจส่งออกไม่ครบ'
             % (len(history), meta['fight_count']))

    # ข้อมูลที่หน้าเว็บควรเห็นหลังเติมค่ากลับ
    want_f = [{k: v for k, v in f.items() if k not in DROP} for f in fighters]
    want_h = history

    f_null = sorted(common_keys(want_f) - set(SAME_AS_ID) - {'id'})
    h_null = sorted(common_keys(want_h))
    f_same = [k for k in SAME_AS_ID if k in common_keys(want_f)] if want_f and 'id' in common_keys(want_f) else []

    packed_f = [pack(f, set(f_null), f_same) for f in want_f]
    packed_h = [pack(h, set(h_null), []) for h in want_h]

    restore = (
        '/* เติมค่าที่ย่อไว้กลับ ให้หน้าเว็บเห็นข้อมูลเหมือนไฟล์เต็ม */\n'
        '(function(){var i,j,o,'
        'FN=' + dumps(f_null) + ',FS=' + dumps(f_same) + ',HN=' + dumps(h_null) + ';\n'
        'for(i=0;i<FIGHTERS.length;i++){o=FIGHTERS[i];'
        'for(j=0;j<FS.length;j++)if(!(FS[j] in o))o[FS[j]]=o.id;'
        'for(j=0;j<FN.length;j++)if(!(FN[j] in o))o[FN[j]]=null;}\n'
        'for(i=0;i<HISTORY.length;i++){o=HISTORY[i];'
        'for(j=0;j<HN.length;j++)if(!(HN[j] in o))o[HN[j]]=null;}\n'
        '})();\n'
    )

    lines = [
        '// สารบัญนักมวย — สร้างอัตโนมัติโดย build_index.py จาก fighters_data.js',
        '// ⚠ อย่าแก้ไฟล์นี้ด้วยมือ (ถูกเขียนทับทุกครั้งที่รัน generate_profiles.bat)',
        '// ไม่มีช่อง: ' + ', '.join(sorted(DROP)) + ' — หน้าที่ต้องใช้ให้โหลด fighters_data.js',
        '',
        'const META = ' + dumps(meta) + ';',
        'const FIGHTERS = [',
        ',\n'.join(dumps(f) for f in packed_f),
        '];',
        'const HISTORY = [',
        ',\n'.join(dumps(h) for h in packed_h),
        '];',
        restore,
    ]
    out_text = '\n'.join(lines)

    # ตรวจซ้ำ: อ่านสิ่งที่จะเขียนกลับมา เติมค่ากลับ แล้วเทียบกับข้อมูลเต็มทีละแถว
    got_f = [unpack(f, f_null, f_same) for f in extract_js_const(out_text, 'FIGHTERS')]
    got_h = [unpack(h, h_null, []) for h in extract_js_const(out_text, 'HISTORY')]
    if len(got_f) != len(want_f) or len(got_h) != len(want_h):
        fail('จำนวนนักมวย/ไฟต์ในสารบัญไม่ตรงกับไฟล์เต็ม')
    for a, b in zip(got_f, want_f):
        if a != b:
            fail('ข้อมูลนักมวย "%s" ในสารบัญไม่ตรงกับไฟล์เต็ม' % b.get('id'))
    for n, (a, b) in enumerate(zip(got_h, want_h)):
        if a != b:
            fail('ประวัติการชกแถวที่ %d (%s) ในสารบัญไม่ตรงกับไฟล์เต็ม' % (n + 1, b.get('fighter_id')))

    # เขียนไฟล์ใหม่ก่อน แล้วค่อยสลับแทนไฟล์เดิม (ถ้าค้างกลางทาง ไฟล์เดิมยังอยู่)
    tmp = OUT.with_suffix('.js.tmp')
    tmp.write_bytes(out_text.encode('utf-8'))
    os.replace(tmp, OUT)

    full_mb = SRC.stat().st_size / 1e6
    idx_mb = OUT.stat().st_size / 1e6
    print('  ✓ สารบัญ: นักมวย %s คน / ไฟต์ %s ไฟต์ — ตรงกับข้อมูลเต็มทุกแถว'
          % (format(len(fighters), ','), format(len(history), ',')))
    print('    ขนาด %.1f MB (ไฟล์เต็ม %.1f MB — ยังอยู่ครบ ไม่ถูกแก้)' % (idx_mb, full_mb))


if __name__ == '__main__':
    main()
