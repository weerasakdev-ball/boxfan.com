# Boxfan — แพ็กเกจอัปเกรดเวอร์ชันสมบูรณ์

อัปเกรดความปลอดภัย + บั๊ก + accessibility + SEO + ระบบ design token แบบรวมศูนย์
โครงสร้างและดีไซน์เดิมคงไว้ทั้งหมด — เปลี่ยนเฉพาะส่วนที่ระบุด้านล่าง

---

## ไฟล์ในแพ็กเกจ

ไฟล์ที่ต้องเอาไป **ทับของเดิม**
- `utils.js` — เพิ่ม `esc()` กัน XSS, ระบบ accessibility กลาง (คีย์บอร์ด + focus + skip link)
- `index.html`, `profile.html`, `compare.html`, `rankings.html` — escape ข้อมูล, แก้ฟอนต์ compare, security meta, ลิงก์ token กลาง, noscript, PWA meta

ไฟล์ **ใหม่** ที่ต้องเพิ่มเข้าเว็บ
- `boxfan-tokens.css` — แหล่งความจริงเดียวของ design token (สี/ฟอนต์/เงา) แก้ทีเดียวมีผลทั้งเว็บ + contrast ผ่าน WCAG AA
- `robots.txt`, `sitemap.xml`, `manifest.webmanifest`
- `build.js` — สร้าง sitemap เต็ม + หน้า OG snapshot จากข้อมูลจริง

---

## ขั้นตอนติดตั้ง

1. อัปโหลด 5 ไฟล์แรกทับของเดิม และวางไฟล์ใหม่ทั้งหมดไว้ที่ root เดียวกับ `index.html`
   > **สำคัญ:** ต้องอัปเดต `utils.js` ด้วยเสมอ เพราะ `esc()` และระบบ a11y อยู่ในนั้น — ถ้าใช้ HTML ใหม่กับ utils.js เก่า หน้าจะหา `esc` ไม่เจอ
2. สร้างโฟลเดอร์ `/icons/` แล้วใส่ไอคอน PNG 3 ไฟล์ (สำหรับ PWA): `icon-192.png`, `icon-512.png`, `icon-maskable-512.png`
3. รัน `node build.js` ที่ root (ต้องมีโฟลเดอร์ `data/` ที่มี `fighters_data.js`)
   - จะอัปเดต `sitemap.xml` ให้รวมโปรไฟล์นักมวยทุกคน
   - จะสร้างโฟลเดอร์ `p/` ที่มีหน้า OG snapshot ต่อนักมวย
   - รันซ้ำทุกครั้งที่เพิ่ม/แก้ข้อมูลนักมวย
4. ส่ง `sitemap.xml` เข้า Google Search Console

---

## สรุปสิ่งที่แก้

**ความปลอดภัย (ปิดช่องโหว่ XSS)**
- เพิ่ม `esc()` แล้วหุ้มข้อความอิสระทุกจุดที่ต่อสตริงเข้า `innerHTML` (ชื่อ, คู่ต่อสู้, อีเวนต์, ประวัติ, คำค้น ฯลฯ) ครบทุกหน้า + ใน `build.js`
- เพิ่ม Content-Security-Policy + referrer policy ในทุกหน้า
- ใส่ `rel="noopener noreferrer"` ให้ลิงก์เปิดแท็บใหม่ทุกอัน

**บั๊ก**
- `compare.html` เดิมโหลดแค่ฟอนต์ Sarabun ทำให้หัวข้อเพี้ยน → โหลดชุดเดียวกับหน้าอื่นแล้ว

**Accessibility (WCAG)**
- ทุก `<div onclick>` กดด้วย Enter/Space ได้ (อัตโนมัติผ่าน MutationObserver — รวมที่ render ด้วย JS)
- focus ring มองเห็นชัด + ลิงก์ "ข้ามไปยังเนื้อหาหลัก"
- ปรับสีตัวอักษรรอง `--tx-3 / --tx-4` ให้ contrast ผ่าน AA (≥4.5:1) ทั้งโหมดมืดและสว่าง
- เคารพ `prefers-reduced-motion` (ปิดอนิเมชันให้ผู้ที่ตั้งค่าไว้)

**SEO**
- `robots.txt` + `sitemap.xml` (รวมทุกโปรไฟล์ผ่าน build.js)
- หน้า OG snapshot (`/p/<id>.html`) ให้ Facebook/Line/Twitter ที่ไม่รัน JS เห็น meta/รูป/JSON-LD ถูกต้อง — แชร์โปรไฟล์ให้ใช้ลิงก์นี้
- `<noscript>` fallback ทุกหน้า

**โครงสร้าง CSS**
- รวม design token ทั้งหมด (66 dark / 58 light) จาก 4 หน้าที่เคยซ้ำกัน มาไว้ที่ `boxfan-tokens.css` ที่เดียว — ตรวจแล้วว่า token ที่ใช้จริงครบ 100%
- หมายเหตุ: `--loss` ปรับเป็นโทนแดงนุ่ม `#e8694e` ให้ทุกหน้าตรงกัน (เดิมหน้า profile ใช้แดงเข้มกว่าเล็กน้อย)

---

## ต้องตั้งค่าฝั่งเซิร์ฟเวอร์เพิ่ม (กัน clickjacking)

CSP ผ่าน `<meta>` ไม่รองรับ `frame-ancestors` — ให้เพิ่ม HTTP header ที่เซิร์ฟเวอร์/host:
```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Content-Security-Policy: frame-ancestors 'self';
```

---

## ยังไม่ได้ทำ (ทำต่อได้)

- Server-Side Rendering เต็มรูป (ตอนนี้ใช้ OG snapshot ทดแทนสำหรับ social)
- Service worker สำหรับ offline (มี manifest แล้ว แต่ยังไม่ใส่ SW)
- รวม inline `<style>` ที่เหลือของแต่ละหน้าเข้า `style.css` (ทำได้หลัง QA)
