#!/usr/bin/env node
/* ═══════════════════════════════════════════════════════════════
   BOXFAN — build.js
   สร้าง SEO assets จากข้อมูลจริง (data/fighters_data.js)

   วิธีใช้ (รันที่ root ของเว็บ ที่มีโฟลเดอร์ data/):
       node build.js

   จะสร้าง:
     1) sitemap.xml      — รวมหน้าหลัก + โปรไฟล์นักมวยทุกคน
     2) p/<id>.html      — หน้า "OG snapshot" ต่อนักมวย (สำหรับ Facebook/Line/
                           Twitter ที่ไม่รัน JS) มี meta/OG/JSON-LD ครบ
                           แล้ว redirect คนจริงไป profile.html?id=<id>

   ไม่ต้องติดตั้ง dependency ใด ๆ (ใช้ Node มาตรฐาน)
   ═══════════════════════════════════════════════════════════════ */
'use strict';

const fs   = require('fs');
const path = require('path');
const vm   = require('vm');

const SITE = 'https://boxingfandom.com';
const ROOT = process.cwd();
const DATA = path.join(ROOT, 'data', 'fighters_data.js');

/* ── โหลดข้อมูลแบบปลอดภัยใน sandbox ── */
function loadData() {
  if (!fs.existsSync(DATA)) {
    console.error('✗ ไม่พบ ' + DATA + ' — รัน build.js ที่ root ของเว็บ');
    process.exit(1);
  }
  const code = fs.readFileSync(DATA, 'utf8');
  const sandbox = { window: {}, FIGHTERS: [], HISTORY: [] };
  vm.createContext(sandbox);
  try { vm.runInContext(code, sandbox, { timeout: 5000 }); }
  catch (e) { console.error('✗ อ่าน fighters_data.js ไม่ได้:', e.message); process.exit(1); }
  const F = sandbox.FIGHTERS || (sandbox.window && sandbox.window.FIGHTERS) || [];
  const H = sandbox.HISTORY  || (sandbox.window && sandbox.window.HISTORY)  || [];
  return { FIGHTERS: F, HISTORY: H };
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function today() { return new Date().toISOString().slice(0, 10); }

/* ── 1) sitemap.xml ── */
function buildSitemap(FIGHTERS) {
  const d = today();
  const statics = [
    ['/', '1.0', 'daily'], ['/rankings.html', '0.9', 'daily'],
    ['/schedule.html', '0.9', 'daily'], ['/results.html', '0.8', 'daily'],
    ['/compare.html', '0.7', 'weekly'], ['/tierlist.html', '0.7', 'weekly'],
    ['/blog/', '0.6', 'weekly'], ['/about.html', '0.3', 'monthly'],
    ['/contact.html', '0.3', 'monthly'], ['/privacy.html', '0.2', 'yearly'],
    ['/disclaimer.html', '0.2', 'yearly'],
  ];
  let u = statics.map(([loc, p, c]) =>
    `  <url><loc>${SITE}${loc}</loc><lastmod>${d}</lastmod><changefreq>${c}</changefreq><priority>${p}</priority></url>`);
  FIGHTERS.forEach(f => {
    u.push(`  <url><loc>${SITE}/profile.html?id=${f.id}</loc><lastmod>${d}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>`);
  });
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${u.join('\n')}\n</urlset>\n`;
  fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), xml);
  console.log(`✓ sitemap.xml — ${statics.length} หน้าหลัก + ${FIGHTERS.length} โปรไฟล์`);
}

/* ── 2) OG snapshot ต่อนักมวย (สำหรับ crawler ที่ไม่รัน JS) ── */
function buildSnapshots(FIGHTERS) {
  const dir = path.join(ROOT, 'p');
  if (!fs.existsSync(dir)) fs.mkdirSync(dir);
  let n = 0;
  FIGHTERS.forEach(f => {
    const id   = f.id;
    const name = f.name_th || f.name_en || ('นักมวย #' + id);
    const en   = f.name_en || '';
    const div  = f.division || '';
    const rec  = `${f.total_wins || 0}W ${f.total_losses || 0}L`;
    const wr   = (f.win_rate != null) ? (' WR ' + f.win_rate + '%') : '';
    const title = `${name}${en ? ' (' + en + ')' : ''} — สถิตินักมวย | Boxfan`;
    const desc  = `${name} นักมวย ${div} ${rec}${wr} · สถิติและประวัติการชกครบทุกรายการ | Boxfan`;
    const img   = f.image_filename
      ? `https://res.cloudinary.com/dpvyl7nan/image/upload/c_fill,g_face,w_800,h_600,f_auto,q_auto/${encodeURIComponent(String(f.image_filename).replace(/\.(jpg|jpeg|png|webp)$/i, ''))}`
      : `${SITE}/og-default.jpg`;
    const canonical = `${SITE}/profile.html?id=${id}`;
    const jsonld = {
      '@context': 'https://schema.org', '@type': 'Person',
      name: name, alternateName: en || undefined,
      image: img, url: canonical, nationality: f.country || undefined,
      description: desc, sport: 'Muay Thai / Kickboxing / MMA',
    };
    const html =
`<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<link rel="canonical" href="${canonical}">
<meta property="og:type" content="profile">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:image" content="${esc(img)}">
<meta property="og:url" content="${canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(desc)}">
<meta name="twitter:image" content="${esc(img)}">
<script type="application/ld+json">${JSON.stringify(jsonld)}</script>
<meta http-equiv="refresh" content="0; url=${canonical}">
<link rel="canonical" href="${canonical}">
</head>
<body>
<h1>${esc(name)}</h1>
<p>${esc(div)} · ${esc(rec)}${esc(wr)}</p>
<p><a href="${canonical}">ดูสถิติและประวัติการชกฉบับเต็มของ ${esc(name)} ›</a></p>
<script>location.replace(${JSON.stringify(canonical)});</script>
</body>
</html>
`;
    fs.writeFileSync(path.join(dir, id + '.html'), html);
    n++;
  });
  console.log(`✓ p/<id>.html — ${n} หน้า OG snapshot`);
  console.log('  (แชร์โปรไฟล์ใช้ลิงก์ ' + SITE + '/p/<id>.html เพื่อให้ social preview ถูกต้อง)');
}

/* ── run ── */
const { FIGHTERS } = loadData();
console.log(`โหลดข้อมูล: ${FIGHTERS.length} นักมวย`);
buildSitemap(FIGHTERS);
buildSnapshots(FIGHTERS);
console.log('เสร็จสิ้น ✓');
