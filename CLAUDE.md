# BOXFAN — โน้ตการทำงาน (สำหรับ AI และคนที่มาทำต่อ)

> ไฟล์นี้ไม่ขึ้นเว็บ (อยู่ใน .vercelignore) — อ่านก่อนแก้อะไรในโปรเจกต์ทุกครั้ง
> อัปเดตล่าสุด: 3 พ.ย. 2569

---

## ⛔ กฎเหล็ก (ห้ามละเมิด)

1. **ห้ามตัด ย่อ ลบ หรือแก้ข้อมูลนักมวยเด็ดขาด** — `data/fighters_data.js` เป็นของเจ้าของเว็บ
   ห้ามสร้างไฟล์ข้อมูลฉบับย่อ/ตัดช่อง (เคยทำ `fighters_lite.js` แล้วเจ้าของไม่อนุญาต — ยกเลิกแล้ว)
   ถ้าจะทำอะไรที่เกี่ยวกับข้อมูล **ต้องถามก่อนทุกครั้ง**
   ข้อยกเว้นที่เจ้าของอนุญาตแล้ว (3 พ.ย. 2569): `data/fighters_index.js` = สารบัญที่ `build_index.py`
   สร้างจากไฟล์เต็มอัตโนมัติ (ไฟล์เต็มไม่ถูกแตะ) — ดูหัวข้อ "สารบัญนักมวย" ด้านล่าง
2. เจ้าของแก้ข้อมูลเองด้วยโปรแกรม **Boxfan Studio** (`D:\โปรแกรมจัดการข้อมูลv1`, เปิดด้วย run_studio.bat)
   ข้อมูลดิบ = ไฟล์ JSON นักมวยละไฟล์ที่ `D:\data\data` → หน้า "ส่งออกข้อมูล" (export_json.py) เขียน `data/fighters_data.js`
3. หน้าตาเว็บต้องเหมือนเดิม — งาน SEO/แก้บั๊ก ห้ามเปลี่ยนดีไซน์โดยไม่ได้ขอ
   (3 พ.ย. 2569 เจ้าของขอธีมใหม่ "สะอาด อ่านง่าย ทันสมัย" ทั้งเว็บ + โลโก้เวทีมวย — ดูหัวข้อ "ธีมกลาง")
4. คุยกับเจ้าของเป็นภาษาไทย สั้น ง่าย ไม่ใช้ศัพท์เทคนิค

---

## โครงสร้างระบบ (ภาพรวม)

```
export_json.py (นอกโฟลเดอร์)  →  data/fighters_data.js   (FIGHTERS / HISTORY / META)
                                        │
          generate_profiles.bat  ───────┤
            [1] build_index.py            → data/fighters_index.js (สารบัญ ให้หน้าเบาโหลดแทนไฟล์เต็ม)
            [2] build_chrome.py           → เมนูบน/ท้ายเว็บ/ธีม แบบเดียวกันใส่ทุกหน้า
            [3] data/generate_profiles.py → fighters/<slug>.html  (หน้านักมวย static 21,000+ หน้า)
            [4] build_seo.py              → ฝังเนื้อหาที่ JS สร้างลงไฟล์ .html (prerender)
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

## ธีมกลาง (site.css / site.js / build_chrome.py)

- **แก้เมนูบน / เมนูมือถือ / ท้ายเว็บ → แก้ `build_chrome.py` ที่เดียว** (MENU, FOOT_COLS, FOOT_TAGS)
  แล้วรัน .bat — สคริปต์ใส่ HTML ระหว่าง `<!--BF:head|header|footer-->…<!--/BF:…-->` ทุกหน้า
  (หน้านักมวยใช้ฟังก์ชันเดียวกันผ่าน `generate_profiles.py`) ลิงก์ขึ้นต้นด้วย `/` ทั้งหมด
- **สี/ฟอนต์ → แก้ `:root` ใน `site.css`** (สีหลัก `--bf-accent` แดง, พื้น `--bf-bg`, ฟอนต์ Inter + Noto Sans Thai)
  หน้าเก่ามีตัวแปรสีคนละชุด (index/boxfan-theme/boxfan-tokens/board-kit/style.css) → บล็อก `html.bf{…}`
  ชี้ทุกชื่อเก่ามาที่สีใหม่ / หน้าที่มี `--gold-light` (แบบหน้าแรก) ได้ `data-skin="a"` = ทองกลายเป็นสีหลัก
- เมนู/ท้ายเว็บเก่าของแต่ละหน้า **ยังอยู่ในไฟล์แต่ถูกซ่อนด้วย CSS** (JS เดิมอ้างถึงอยู่ ลบแล้วจะพัง)
- **ธีมสว่างอย่างเดียว** — site.js บังคับ `data-theme="light"` (โหมดมืดของหน้าเก่าคนละแบบ ปิดไว้ก่อน)
- แก้ site.css / site.js → เพิ่ม `VER` ใน build_chrome.py + เปลี่ยน `VERSION` ใน service-worker.js
- build_chrome.py แก้ CSP ให้ Umami ส่งข้อมูลได้ (เดิมบล็อก gateway.umami.is → นับคนเข้าไม่ได้) และเติม Umami ให้หน้าที่ไม่มี
- โลโก้ = `images/logo-96.png` / `logo-192.png` (ย่อจาก `logoboxingfandom.png` ของเจ้าของ)
- หน้าใหม่: เพิ่มชื่อไฟล์ใน `pages()` ของ build_chrome.py (บทความใน blog/articles/ ได้เองอัตโนมัติ)

## สารบัญนักมวย (data/fighters_index.js)

- ไฟล์เต็ม ~36 MB มือถืออ่านช้า → `build_index.py` สร้างสารบัญ ~9 MB ทุกครั้งที่รัน .bat
  - ตัดเฉพาะช่องใน `DROP` (thboxing_url, strike_stats, fight_purse, market_value, biography ฯลฯ)
  - ไม่เขียนค่า null และ slug/image_filename ที่เท่ากับ id → โค้ดท้ายไฟล์เติมกลับตอนโหลด
  - ใช้ชื่อตัวแปรเดิม `FIGHTERS / HISTORY / META` → โค้ดหน้าเว็บไม่ต้องแก้
  - ตรวจซ้ำทุกแถวเทียบกับไฟล์เต็มก่อนเขียน ไม่ตรง = หยุด (ไฟล์เดิมไม่ถูกแก้)
- **หน้าที่โหลดสารบัญ:** index, fighters, rankings, weight-classes (+rankings-*), results, schedule,
  tierlist, bracket, ranking, my-ranking, about, contact, privacy, disclaimer
- **หน้าที่ยังโหลดไฟล์เต็ม:** stats, compare, profile, RankingMuay (ใช้ strike_stats / ค่าตัว / ฯลฯ)
- หน้าเบาจะใช้ช่องที่อยู่ใน DROP → เอาออกจาก DROP หรือให้หน้านั้นโหลด fighters_data.js
- ห้ามโหลดสองไฟล์ในหน้าเดียว (ทั้งคู่ประกาศ `const FIGHTERS` → error)
- คู่มือสำหรับเจ้าของ: `คู่มืออัปเดตข้อมูล.md`

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
- แปลง `\r` จาก DOM เป็น `\n` + ยุบบรรทัดว่างก่อนคัดลอก (เดิมทำให้ index.html มีบรรทัดว่างเพิ่มเท่าตัวทุกรอบ — แก้แล้ว 3 พ.ย. 2569)
- `write()` ลองเขียนซ้ำสูงสุด 10 ครั้ง — Windows ล็อกไฟล์ชั่วคราวได้ (Errno 22)
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
- หน้าเบาโหลดสารบัญแล้ว (3 พ.ย. 2569) — ยังเบาลงได้อีก เช่น แยก HISTORY / โหลดเฉพาะส่วน (ถามเจ้าของก่อน)
- นักมวย ~19,400 คนยังไม่มีประวัติการชก (ไม่มีตั้งแต่ไฟล์ดิบ) → ตั้งแต่ 3 พ.ย. 2569
  `generate_profiles.py` ใส่ `noindex,follow` ให้หน้าที่ไม่มีไฟต์เลย (ชกแล้ว/รอชก) และไม่มี biography
  และ `build_seo.py` ตัดหน้า noindex ออกจาก sitemap (อ่านจาก meta robots ในไฟล์) — เติมข้อมูลแล้วกลับมาเอง
- ยังไม่ได้ติดตั้ง AdSense (ไม่มี ads.txt, CSP ของ index.html ยังบล็อกสคริปต์ภายนอก, หน้าแรกไม่มี Umami)
- **URL เก่า → หน้าใหม่ (ทำแล้ว 3 พ.ย. 2569):**
  - `vercel.json` redirects: `weight-classes.html?div=<key>` → `rankings-<รุ่น>.html` (11 รุ่น),
    `profile.html?…&name=<slug>` → `fighters/<slug>.html`
  - `generate_profiles.py write_alias_pages()` สร้างหน้าส่งต่อ `fighters/<id เดิม>.html` (meta refresh + canonical)
    ให้นักมวยทุกคนที่ id ≠ slug (เช่น พันพะกาฬ-ศ.ศศิวัฒน์ → arthorn-nontakod) + ชื่อไฟล์เก่าใน `OLD_PAGES`
    ทุกสัปดาห์อัตโนมัติ / ไม่ทับหน้าจริง (เช็กตัวพิมพ์เล็ก-ใหญ่) / ไม่อยู่ใน sitemap
  - `profile.html` หาได้จาก `?id= / ?slug= / ?f= / ?name=` แล้วส่งไปหน้า static
- GitHub repo ยังเป็น public — แนะนำให้เปลี่ยนเป็น private (Vercel ยัง deploy ได้)
