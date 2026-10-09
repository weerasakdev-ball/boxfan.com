# BOXFAN — โน้ตการทำงาน (สำหรับ AI และคนที่มาทำต่อ)

> ไฟล์นี้ไม่ขึ้นเว็บ (อยู่ใน .vercelignore) — อ่านก่อนแก้อะไรในโปรเจกต์ทุกครั้ง
> อัปเดตล่าสุด: 4 ต.ค. 2569

---

## ⛔ กฎเหล็ก (ห้ามละเมิด)

1. **ห้ามตัด ย่อ ลบ หรือแก้ข้อมูลนักมวยเด็ดขาด** — `data/fighters_data.js` เป็นของเจ้าของเว็บ
   ห้ามสร้างไฟล์ข้อมูลฉบับย่อ/ตัดช่อง (เคยทำ `fighters_lite.js` แล้วเจ้าของไม่อนุญาต — ยกเลิกแล้ว)
   ถ้าจะทำอะไรที่เกี่ยวกับข้อมูล **ต้องถามก่อนทุกครั้ง**
2. เจ้าของแก้ข้อมูลเองที่ไฟล์ data (ไฟล์มาจาก `export_json.py` ที่อยู่นอกโฟลเดอร์นี้ — `C:\Users\Weera\Desktop\data\data`)
3. หน้าตาเว็บต้องเหมือนเดิม — งาน SEO/แก้บั๊ก ห้ามเปลี่ยนดีไซน์โดยไม่ได้ขอ
4. คุยกับเจ้าของเป็นภาษาไทย สั้น ง่าย ไม่ใช้ศัพท์เทคนิค

---

## โครงสร้างระบบ (ภาพรวม)

```
export_json.py (นอกโฟลเดอร์)  →  data/fighters_data.js   (FIGHTERS / HISTORY / META)
                                        │
          generate_profiles.bat  ───────┤
            [1] data/generate_profiles.py → fighters/<slug>.html  (หน้านักมวย static 2,000+ หน้า)
            [2] build_seo.py              → ฝังเนื้อหาที่ JS สร้างลงไฟล์ .html (prerender)
                                            + rankings-<รุ่น>.html 11 หน้า + sitemap.xml + robots.txt
                                        │
          VS Code → commit → push GitHub (weerasakdev-ball/boxfan.com)  →  Vercel deploy อัตโนมัติ
```

- โฮสต์: **Vercel** (ไม่ใช่ Netlify/Cloudflare) → ไฟล์ `_redirects` **ใช้ไม่ได้** ต้องใช้ `vercel.json`
- โดเมน: `https://www.boxingfandom.com` (ใช้ www เสมอ — canonical / og / sitemap)
- ไม่มีระบบ build บน Vercel: deploy ไฟล์ในโฟลเดอร์ตรง ๆ (ยกเว้นที่อยู่ใน `.vercelignore`)

## รอบอัปเดตปกติ (บอกเจ้าของแบบนี้)

แก้ data → ดับเบิลคลิก `generate_profiles.bat` → VS Code: Commit + Push → จบ
(ไม่ต้องส่ง sitemap ใน Search Console ซ้ำ ส่งครั้งเดียวพอ)

---

## build_seo.py ทำอะไร

- เปิดแต่ละหน้าด้วย Chrome/Edge แบบ headless (`--dump-dom`) ให้ JS ของหน้าคำนวณเอง
  แล้วคัดลอก HTML ของกล่องที่กำหนด (ตาม id) กลับไปเขียนลงไฟล์ต้นฉบับ
  → ใช้โค้ดหน้าเว็บเดิม ตัวเลขจึงตรงกับที่ผู้ใช้เห็น / ไม่ต้องเขียนตรรกะซ้ำใน Python
- รายการหน้า + กล่องอยู่ในตัวแปร `PAGES` บนสุดของไฟล์
  - `ids`  = กล่องใน body ที่ JS ใช้ `innerHTML =` (ห้ามใส่กล่องที่ JS `appendChild` ต่อท้าย เช่น `<select>` เติม option → จะซ้ำ)
  - `head` = `<script type="application/ld+json" id="...">` ที่ JS สร้าง (ไม่มีในไฟล์จะเพิ่มก่อน `</head>` ให้เอง)
  - `marks`= ช่วง `<!--PR:chrome-->…<!--/PR:chrome-->` / `PR:foot` (เมนู/ท้ายเว็บจาก boxfan-shared.js)
- หน้าแยกรุ่น `rankings-<en>.html` สร้างจากแม่แบบ `weight-classes.html` ทุกครั้ง + ใส่ `window.BF_DIV='fly'`
  → **แก้ดีไซน์หน้ารุ่น ให้แก้ที่ weight-classes.html เท่านั้น** (หน้า rankings-*.html ถูกเขียนทับทุกครั้ง)
- รันซ้ำได้ไม่จำกัด (idempotent) / คงรูปแบบขึ้นบรรทัด CRLF ตามไฟล์เดิม
- หาเบราว์เซอร์ไม่เจอ → ตั้งตัวแปร `BOXFAN_BROWSER` ให้ชี้ chrome.exe / msedge.exe
- **ไม่ prerender `stats.html`** — ตัวเลขเป็นแอนิเมชันนับขึ้น ถ้าจับ DOM จะได้ค่าค้างครึ่งทาง

## เพิ่มหน้าใหม่ให้ Google เห็นเนื้อหา

1. ให้กล่องที่ JS เขียนเนื้อหามี `id` และ JS เขียนด้วย `innerHTML =` (แทนที่ ไม่ต่อท้าย)
2. ลิงก์ไปนักมวยต้องเป็น `<a href="...">` จริง (ไม่ใช่ `onclick="location.href=..."`)
3. เพิ่มชื่อหน้า + id ลง `PAGES` ใน build_seo.py และเพิ่ม URL ใน `MAIN_PAGES` (sitemap)
4. รัน build แล้วเปิดดูหน้าแบบปิด JavaScript ว่าเนื้อหาขึ้น

---

## ไฟล์สำคัญ

| ไฟล์ | หน้าที่ |
|---|---|
| `utils.js` | ฟังก์ชันกลาง: `normalizeData`, `resultTypeOf`, `score`, `fighterUrl`, `divUrl`, `setMeta`, `ldItemList`, `esc` |
| `boxfan-shared.js` | เมนู/ท้ายเว็บ (`bfMount`) ของหน้าแบบเก่า (rankings, fighters, results, schedule) |
| `index.html`, `weight-classes.html` | ดีไซน์ใหม่ (มีเมนู/ท้ายเว็บในไฟล์เอง) |
| `board-kit.js` | ใช้ใน bracket.html / ranking.html |
| `service-worker.js` | แคช — HTML network-first, JS/CSS stale-while-revalidate, รูป cache-first |
| `data/generate_profiles.py` | สร้าง fighters/*.html (ประวัติการชกครบทุกไฟต์ + breadcrumb JSON-LD) |
| `build_seo.py` | prerender + หน้าแยกรุ่น + sitemap + robots |

## จุดที่ต้องจำ

- **สูตรคะแนนกลาง:** ชนะ +3 · เสมอ 0 · แพ้ -3 (ไม่มีโบนัส) — ต้องตรงกันใน `utils.js score()`,
  `calcScore()` ใน index/rankings/weight-classes, `stats.html (o._s)`, `generate_profiles.py build_score()`
- **ผลการชก:** `resultTypeOf()` (JS) = `result_type_of()` (Python) — "แพ้น็อก" = loss, "ยกเลิก…" = cancelled
- **ชื่อไฟล์หน้านักมวย** มาจากช่อง `slug` ในข้อมูล — slug เปลี่ยน = URL เปลี่ยน, หน้าเก่าถูกลบอัตโนมัติ
- **เปลี่ยน utils.js / boxfan-shared.js / board-kit.js** → เพิ่มเลขเวอร์ชันใน `<script src="utils.js?v=2">`
  ทุกหน้า (ไม่งั้นผู้ใช้เก่าค้างไฟล์เดิมในแคช) และเปลี่ยน `VERSION` ใน service-worker.js
- `setMeta()` ไม่เขียนทับ meta ที่มีในไฟล์แล้ว (ยกเว้น `force:true`) และไม่แตะ robots
- `profile.html?id=` = noindex + canonical ไป fighters/<slug>.html (หน้า static คือหน้าหลัก)
- `build.js` / `generate.js` = สคริปต์เก่า เลิกใช้ (build.js หยุดตัวเองทันที)
- ไฟล์ส่วนใหญ่เป็น CRLF (Windows) — ตอนแก้ให้คงรูปแบบเดิม

## เครื่องมือ / การเชื่อมต่อของ AI

- เครื่องเจ้าของ: Windows, โฟลเดอร์ `C:\Users\Weera\Desktop\boxfan`, มี Python + Chrome
- AI เข้าถึงผ่าน device bridge (อ่าน/เขียนไฟล์) — ไม่มี shell บนเครื่อง ลบไฟล์เองไม่ได้ → ขอให้เจ้าของลบ
- ทดสอบใน cloud: คัดลอกโฟลเดอร์ → `python3 -m http.server` → Playwright + Chromium
  เทียบภาพหน้าจอก่อน/หลัง และเช็ก pageerror ทุกหน้าก่อนส่งคืน

## เรื่องค้าง / ไอเดียต่อไป

- ข้อมูลซ้ำ 13 คู่ (เจ้าของแก้เองที่ data) — ดู duplicate_fighters.csv ที่ส่งให้
- ทุกหน้าโหลด fighters_data.js (~6.8 MB) — ถ้าจะทำให้เบาลง **ต้องถามเจ้าของก่อน** (ห้ามตัดข้อมูล)
- redirect URL เก่าของนักมวยที่เปลี่ยน slug (เช่น พันพะกาฬ-ศ.ศศิวัฒน์ → arthorn-nontakod) ต้องทำใน vercel.json
- GitHub repo ยังเป็น public — แนะนำให้เปลี่ยนเป็น private (Vercel ยัง deploy ได้)
