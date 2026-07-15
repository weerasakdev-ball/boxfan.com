#!/usr/bin/env python3
"""
แก้ Content-Security-Policy ในทุกไฟล์ HTML ให้รองรับ Umami

วิธีใช้:
  python fix_csp_umami.py .

script จะ:
  1. หาทุกไฟล์ .html ที่มี Content-Security-Policy
  2. เพิ่ม https://cloud.umami.is ใน script-src (โหลด script ได้)
  3. เพิ่ม connect-src https://cloud.umami.is (ส่งข้อมูล tracking ได้)
  4. ข้ามไฟล์ที่มี cloud.umami.is อยู่ใน CSP แล้ว
  5. backup ไฟล์เดิมเป็น .csp.bak
"""

import os
import sys
import re
import shutil

UMAMI_DOMAIN = 'https://cloud.umami.is'


def fix_csp(content):
    """แก้ CSP ใน HTML content ให้รองรับ Umami"""
    changed = False

    def patch_csp(match):
        nonlocal changed
        csp = match.group(0)

        # ข้ามถ้ามี cloud.umami.is อยู่แล้ว
        if 'cloud.umami.is' in csp:
            return csp

        # เพิ่ม https://cloud.umami.is ใน script-src
        csp = re.sub(
            r"(script-src\s[^;]*?)(\s*;)",
            r"\1 " + UMAMI_DOMAIN + r"\2",
            csp
        )

        # เพิ่ม connect-src (ถ้ามีอยู่แล้ว เพิ่ม domain / ถ้ายังไม่มี เพิ่มใหม่)
        if 'connect-src' in csp:
            if UMAMI_DOMAIN not in csp:
                csp = re.sub(
                    r"(connect-src\s[^;]*?)(\s*;)",
                    r"\1 " + UMAMI_DOMAIN + r"\2",
                    csp
                )
        else:
            # เพิ่ม connect-src ก่อน " ปิดท้าย
            csp = re.sub(
                r"(script-src\s[^;]*?;)",
                r"\1 connect-src 'self' " + UMAMI_DOMAIN + ";",
                csp
            )

        changed = True
        return csp

    new_content = re.sub(
        r'<meta\s+http-equiv=["\']Content-Security-Policy["\'][^>]*>',
        patch_csp,
        content,
        flags=re.IGNORECASE
    )

    return new_content, changed


def main():
    if len(sys.argv) < 2:
        print("วิธีใช้:")
        print("  แก้ CSP:      python fix_csp_umami.py /path/to/website")
        print("  ย้อนกลับ:     python fix_csp_umami.py --undo /path/to/website")
        sys.exit(1)

    if sys.argv[1] == '--undo':
        if len(sys.argv) < 3:
            print("ระบุโฟลเดอร์ด้วย: python fix_csp_umami.py --undo /path/to/website")
            sys.exit(1)
        undo(sys.argv[2])
        return

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"ERROR: '{directory}' ไม่ใช่โฟลเดอร์ที่ถูกต้อง")
        sys.exit(1)

    html_files = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(('.html', '.htm')):
                html_files.append(os.path.join(root, f))

    print(f"พบ {len(html_files)} ไฟล์ HTML\n")

    fixed = 0
    skipped_no_csp = 0
    skipped_already = 0
    errors = 0

    for filepath in html_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # ข้ามไฟล์ที่ไม่มี CSP
            if 'Content-Security-Policy' not in content:
                skipped_no_csp += 1
                continue

            # ข้ามถ้ามี umami ใน CSP แล้ว
            if 'cloud.umami.is' in content and 'script-src' in content:
                # เช็คว่า umami อยู่ใน CSP จริง ไม่ใช่แค่ใน script tag
                csp_match = re.search(
                    r'<meta\s+http-equiv=["\']Content-Security-Policy["\'][^>]*>',
                    content, re.IGNORECASE
                )
                if csp_match and 'cloud.umami.is' in csp_match.group(0):
                    skipped_already += 1
                    continue

            new_content, changed = fix_csp(content)

            if not changed:
                skipped_no_csp += 1
                continue

            # backup
            backup_path = filepath + '.csp.bak'
            if not os.path.exists(backup_path):
                shutil.copy2(filepath, backup_path)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            fixed += 1

        except Exception as e:
            print(f"  ERROR: {filepath} — {e}")
            errors += 1

    print(f"เสร็จแล้ว!")
    print(f"  แก้ CSP: {fixed} ไฟล์")
    print(f"  ไม่มี CSP (ข้าม): {skipped_no_csp} ไฟล์")
    print(f"  มี Umami ใน CSP แล้ว (ข้าม): {skipped_already} ไฟล์")
    if errors:
        print(f"  ผิดพลาด: {errors} ไฟล์")
    if fixed:
        print(f"\nbackup ไว้เป็น .csp.bak")
        print(f"ย้อนกลับ: python fix_csp_umami.py --undo {directory}")


def undo(directory):
    restored = 0
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.csp.bak'):
                bak_path = os.path.join(root, f)
                original = bak_path[:-8]  # ตัด .csp.bak
                shutil.copy2(bak_path, original)
                os.remove(bak_path)
                restored += 1
    print(f"คืนไฟล์เดิม {restored} ไฟล์")


if __name__ == '__main__':
    main()
