#!/usr/bin/env python3
"""
วาง Umami tracking script ในทุกไฟล์ .html อัตโนมัติ

วิธีใช้:
  python inject_umami.py /path/to/your/website

script จะ:
  1. หาทุกไฟล์ .html และ .htm ในโฟลเดอร์ (รวม subfolder)
  2. เช็คว่ามี tracking code อยู่แล้วหรือยัง (ข้ามถ้ามีแล้ว)
  3. วาง script ก่อน </head> ในทุกไฟล์ที่ยังไม่มี
  4. backup ไฟล์เดิมเป็น .html.bak ก่อนแก้
"""

import os
import sys
import shutil

TRACKING_CODE = '<script defer src="https://cloud.umami.is/script.js" data-website-id="40ec0b51-4f08-45be-801d-9cf01fc79260"></script>'

ALREADY_HAS_MARKER = '40ec0b51-4f08-45be-801d-9cf01fc79260'


def inject_tracking(directory):
    if not os.path.isdir(directory):
        print(f"ERROR: '{directory}' ไม่ใช่โฟลเดอร์ที่ถูกต้อง")
        sys.exit(1)

    html_files = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(('.html', '.htm')):
                html_files.append(os.path.join(root, f))

    if not html_files:
        print("ไม่พบไฟล์ .html ในโฟลเดอร์นี้")
        return

    print(f"พบ {len(html_files)} ไฟล์ HTML\n")

    injected = 0
    skipped = 0
    no_head = 0

    for filepath in html_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # ข้ามถ้ามี tracking code อยู่แล้ว
            if ALREADY_HAS_MARKER in content:
                skipped += 1
                continue

            # หา </head> แล้ววาง script ก่อน
            head_lower = content.lower()
            head_pos = head_lower.find('</head>')

            if head_pos == -1:
                # ไม่มี </head> — ลองหา <body> แทน
                body_pos = head_lower.find('<body')
                if body_pos == -1:
                    no_head += 1
                    print(f"  SKIP (ไม่มี <head> หรือ <body>): {filepath}")
                    continue
                insert_pos = body_pos
                insert_text = f'  {TRACKING_CODE}\n'
            else:
                insert_pos = head_pos
                insert_text = f'  {TRACKING_CODE}\n'

            # backup ไฟล์เดิม
            backup_path = filepath + '.bak'
            if not os.path.exists(backup_path):
                shutil.copy2(filepath, backup_path)

            # ฝัง tracking code
            new_content = content[:insert_pos] + insert_text + content[insert_pos:]

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            injected += 1

        except Exception as e:
            print(f"  ERROR: {filepath} — {e}")

    print(f"\nเสร็จแล้ว!")
    print(f"  ฝัง tracking code: {injected} ไฟล์")
    print(f"  มีอยู่แล้ว (ข้าม): {skipped} ไฟล์")
    if no_head:
        print(f"  ไม่มี <head>/<body> (ข้าม): {no_head} ไฟล์")
    print(f"\nไฟล์เดิม backup ไว้เป็น .bak")
    print(f"ถ้าต้องการย้อนกลับ รัน: python inject_umami.py --undo {directory}")


def undo_tracking(directory):
    """คืนไฟล์จาก .bak กลับเป็นต้นฉบับ"""
    restored = 0
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.bak'):
                bak_path = os.path.join(root, f)
                original = bak_path[:-4]  # ตัด .bak ออก
                shutil.copy2(bak_path, original)
                os.remove(bak_path)
                restored += 1

    print(f"คืนไฟล์เดิม {restored} ไฟล์ เรียบร้อย")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("วิธีใช้:")
        print("  ฝัง tracking:    python inject_umami.py /path/to/website")
        print("  ย้อนกลับ:        python inject_umami.py --undo /path/to/website")
        sys.exit(1)

    if sys.argv[1] == '--undo':
        if len(sys.argv) < 3:
            print("ระบุโฟลเดอร์ด้วย: python inject_umami.py --undo /path/to/website")
            sys.exit(1)
        undo_tracking(sys.argv[2])
    else:
        inject_tracking(sys.argv[1])
