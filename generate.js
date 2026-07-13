/*
 * Boxfan — ตัวสร้างหน้านักมวยแบบ Static (SSG)
 * ------------------------------------------------
 * แก้ปัญหา profile.html?id=N -> สร้างหน้า HTML จริง 1 ไฟล์ต่อคน
 * เนื้อหา + SEO ฝังใน HTML ตั้งแต่โหลด (Google อ่านได้ทันที ไม่ต้องรัน JS)
 *
 * วิธีใช้จริง:
 *   1) วางไฟล์นี้ไว้โฟลเดอร์เดียวกับ fighters_data.js (ตัวเต็ม 2057 คน)
 *   2) node generate.js
 *   3) ได้โฟลเดอร์ site/ -> เอา fighter/ + sitemap.xml ไปวางบนเว็บ
 *   4) รันซ้ำหลังทุกอีเวนต์ ONE เพื่ออัปเดต
 */

const fs = require("fs");
const path = require("path");

// ---------- โหลดดาต้า (ไฟล์เดียวกับที่เว็บใช้อยู่แล้ว) ----------
const src = fs.readFileSync("fighters_data.js", "utf8");
const FIGHTERS = grabArray(src, "FIGHTERS");
const HISTORY  = grabArray(src, "HISTORY");

const SITE = "https://boxingfandom.com";
const OUT  = "site";
const TODAY = new Date().toISOString().slice(0, 10);

// ---------- helper: ดึง array ออกจากไฟล์ .js ----------
function grabArray(text, name) {
  const i = text.indexOf("const " + name);
  const s = text.indexOf("[", i);
  let depth = 0;
  for (let j = s; j < text.length; j++) {
    if (text[j] === "[") depth++;
    else if (text[j] === "]" && --depth === 0)
      return JSON.parse(text.slice(s, j + 1));
  }
  throw new Error("ไม่พบ array: " + name);
}

// ---------- helper: สร้าง slug (ให้ URL มีชื่อนักมวย) ----------
const usedSlugs = new Set();
function makeSlug(f) {
  let base = (f.name_en || "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  if (!base) // ไม่มีชื่ออังกฤษ -> ใช้ชื่อไทย (URL ไทยใช้ได้ปกติ)
    base = (f.name_th || ("fighter-" + f.id)).trim()
      .replace(/\s+/g, "-").replace(/[?#/\\'"]/g, "");
  let slug = base;
  if (usedSlugs.has(slug)) slug = base + "-" + f.id; // กันชื่อซ้ำ
  usedSlugs.add(slug);
  return slug;
}

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// จับคู่ประวัติชกเข้ากับนักมวย + แยก "อดีต" กับ "กำลังจะมา"
const historyByFighter = {};
for (const h of HISTORY) (historyByFighter[h.fighter_id] ||= []).push(h);

// ---------- Template หน้านักมวย (1 template ใช้กับทุกคน) ----------
function renderFighter(f, slug, allFighters) {
  const url = `${SITE}/fighter/${encodeURIComponent(slug)}/`;
  const img = f.image_filename
    ? `${SITE}/images/${encodeURIComponent(f.image_filename)}.jpg`
    : `${SITE}/og-default.jpg`;

  const fights = (historyByFighter[f.id] || [])
    .slice().sort((a, b) => (b.date || "").localeCompare(a.date || ""));
  const upcoming = fights.filter(h => h.date > TODAY);
  const past     = fights.filter(h => h.date <= TODAY);

  const wr = (f.win_rate || 0);
  const title = `${f.name_th}${f.name_en ? ` (${f.name_en})` : ""} สถิตินักมวย ONE Championship | Boxfan`;
  const desc = `${f.name_th} นักมวย ONE Championship ${f.division || ""} `
    + `${f.total_wins}W ${f.total_losses}L อัตราชนะ ${wr}% ดูสถิติและประวัติการชกทั้งหมดที่ Boxfan`;
  const keywords = [f.name_th, f.name_en, "ONE Championship", f.division,
    "มวยไทย", "Muay Thai", "สถิตินักมวย", "Boxfan"].filter(Boolean).join(",");

  // Schema.org Person (เหมือนที่ profile.html เดิมสร้าง แต่ฝังใน HTML)
  const ld = {
    "@context": "https://schema.org", "@type": "Person",
    name: f.name_th, alternateName: f.name_en || undefined,
    nationality: f.country || undefined, url,
    image: img, jobTitle: "นักกีฬาต่อสู้ (Muay Thai / Kickboxing / MMA)",
    height: f.height_cm ? `${f.height_cm} cm` : undefined,
    weight: f.weight_kg ? `${f.weight_kg} kg` : undefined,
    memberOf: { "@type": "SportsOrganization", name: "ONE Championship" },
    description: f.biography || `${f.name_th} นักมวย ONE Championship`
  };

  // แถวประวัติชก
  const rows = past.map(h => {
    const c = h.result_type === "win" ? "#2ecc71"
            : h.result_type === "loss" ? "#e74c3c" : "#95a5a6";
    const detail = [h.round ? `ยก ${h.round}` : "", h.time || "", h.decision || ""]
      .filter(Boolean).join(" · ");
    return `<tr><td>${esc(h.date)}</td>`
      + `<td><b style="color:${c}">${esc(h.result)}</b></td>`
      + `<td>${esc(h.opponent)}</td>`
      + `<td>${esc(h.rules)}</td>`
      + `<td>${esc(detail)}</td>`
      + `<td>${esc(h.event)}</td></tr>`;
  }).join("\n");

  const upHtml = upcoming.length
    ? `<div class="up"><span class="pulse"></span> แมตช์ถัดไป: `
      + upcoming.map(u => `<b>${esc(u.opponent)}</b> — ${esc(u.event)} (${esc(u.date)})`).join(" · ")
      + `</div>` : "";

  // physical + striking (แสดงเฉพาะที่มีข้อมูล = ไม่โชว์ 0 เปล่าๆ)
  const meta = [];
  if (f.height_cm) meta.push(["ส่วนสูง", `${f.height_cm} ซม. (${f.height_ft_in || ""})`]);
  if (f.weight_kg) meta.push(["น้ำหนัก", `${f.weight_kg} กก. (${f.weight_lbs || ""} ปอนด์)`]);
  if (f.age)       meta.push(["อายุ", `${f.age} ปี`]);
  if (f.team)      meta.push(["ค่าย", f.team]);
  if (f.country)   meta.push(["ประเทศ", f.country]);
  const metaHtml = meta.map(([k, v]) =>
    `<div class="mrow"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join("");

  const bio = f.biography
    ? `<h2>ประวัติ</h2><p class="bio">${esc(f.biography)}</p>` : "";

  // ลิงก์ไปนักมวยอื่น (internal link -> Google ไล่เก็บครบ)
  const others = allFighters.filter(x => x.id !== f.id).slice(0, 12)
    .map(x => `<a href="/fighter/${encodeURIComponent(x._slug)}/">${esc(x.name_th)}</a>`).join(" ");

  return `<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<meta name="keywords" content="${esc(keywords)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="${url}">
<meta property="og:type" content="profile">
<meta property="og:title" content="${esc(f.name_th)} — สถิติและประวัติการชก">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:image" content="${esc(img)}">
<meta property="og:url" content="${url}">
<meta property="og:site_name" content="Boxfan">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">${JSON.stringify(ld)}</script>
<style>
 :root{--bg:#0d1014;--card:#161b22;--line:#232b36;--tx:#e8eaed;--mut:#9aa2ad;--gold:#ffd233}
 *{box-sizing:border-box}
 body{margin:0;font-family:'Segoe UI',system-ui,'Noto Sans Thai',sans-serif;background:var(--bg);color:var(--tx);line-height:1.55}
 .wrap{max-width:860px;margin:0 auto;padding:20px}
 a{color:var(--gold);text-decoration:none} a:hover{text-decoration:underline}
 nav{font-size:13px;color:var(--mut);margin-bottom:18px}
 .hero{display:flex;gap:18px;align-items:center;background:var(--card);border-radius:14px;padding:20px;margin-bottom:8px}
 .hero img{width:96px;height:96px;border-radius:12px;object-fit:cover;background:#222}
 h1{margin:0;font-size:26px}
 .en{color:var(--mut);font-size:15px;margin-top:2px}
 .div{display:inline-block;background:rgba(255,210,51,.14);color:var(--gold);font-size:12px;padding:3px 10px;border-radius:20px;margin-top:8px}
 .rec{display:flex;gap:22px;margin:18px 0}
 .rec div{text-align:center}
 .rec b{display:block;font-size:30px;line-height:1}
 .rec .w{color:#2ecc71}.rec .l{color:#e74c3c}.rec .r{color:var(--mut)}
 .rec span{font-size:12px;color:var(--mut)}
 .wrbar{flex:1;min-width:120px;align-self:center}
 .wrbar .bar{height:8px;background:#222b36;border-radius:6px;overflow:hidden}
 .wrbar .fill{height:100%;background:var(--gold)}
 .up{background:var(--card);border-left:3px solid var(--gold);padding:12px 16px;border-radius:8px;margin:14px 0;font-size:14px}
 .pulse{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--gold);margin-right:6px}
 h2{font-size:17px;margin:26px 0 8px;border-bottom:2px solid var(--gold);display:inline-block;padding-bottom:4px}
 .mrow{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--line);font-size:14px}
 .mrow span{color:var(--mut)}
 .bio{color:#cfd4da;font-size:14px}
 table{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
 th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line)}
 th{color:var(--mut);font-weight:600;font-size:12px}
 .others{margin-top:32px;font-size:14px;line-height:2}
 .others a{margin-right:12px;white-space:nowrap}
 .note{color:#66707c;font-size:11px;margin-top:22px}
 @media(max-width:560px){.hero{flex-wrap:wrap}.rec{flex-wrap:wrap;gap:16px}}
</style>
</head>
<body>
<div class="wrap">
  <nav><a href="/">หน้าแรก</a> › <a href="/fighters.html">นักมวยทั้งหมด</a> › ${esc(f.name_th)}</nav>

  <div class="hero">
    <img src="${esc(img)}" alt="${esc(f.name_th)}" onerror="this.style.visibility='hidden'">
    <div>
      <h1>${esc(f.name_th)}</h1>
      ${f.name_en ? `<div class="en">${esc(f.name_en)}</div>` : ""}
      ${f.division ? `<div class="div">${esc(f.division)}</div>` : ""}
    </div>
  </div>

  <div class="rec">
    <div><b class="w">${f.total_wins}</b><span>ชนะ</span></div>
    <div><b class="l">${f.total_losses}</b><span>แพ้</span></div>
    ${f.total_nc ? `<div><b class="r">${f.total_nc}</b><span>ไม่ตัดสิน</span></div>` : ""}
    <div class="wrbar">
      <div class="bar"><div class="fill" style="width:${wr}%"></div></div>
      <div style="font-size:12px;color:var(--mut);margin-top:5px">อัตราชนะ ${wr}%</div>
    </div>
  </div>
  ${upHtml}

  <h2>ข้อมูลนักมวย</h2>
  ${metaHtml}
  ${bio}

  <h2>ประวัติการชก (${past.length} ไฟต์)</h2>
  <table>
    <thead><tr><th>วันที่</th><th>ผล</th><th>คู่ชก</th><th>กติกา</th><th>รายละเอียด</th><th>รายการ</th></tr></thead>
    <tbody>${rows || '<tr><td colspan="6" style="color:var(--mut)">ยังไม่มีข้อมูล</td></tr>'}</tbody>
  </table>

  <div class="others"><h2>นักมวยอื่น</h2><br>${others}</div>
  <p class="note">อัปเดตล่าสุด ${esc(f.updated_at || TODAY)} · ที่มา: ${f.profile_url ? esc(f.profile_url) : "Boxfan"}</p>
</div>
</body>
</html>`;
}

// ---------- รันปั๊มทุกหน้า ----------
function main() {
  // เตรียม slug ให้ทุกคนก่อน (เพื่อทำ internal link ข้ามกันได้)
  for (const f of FIGHTERS) f._slug = makeSlug(f);

  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(path.join(OUT, "fighter"), { recursive: true });

  const sitemap = [`${SITE}/`, `${SITE}/fighters.html`, `${SITE}/rankings.html`,
                   `${SITE}/schedule.html`, `${SITE}/results.html`,
                   `${SITE}/compare.html`, `${SITE}/tierlist.html`];
  const redirects = [];

  for (const f of FIGHTERS) {
    const dir = path.join(OUT, "fighter", f._slug);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, "index.html"),
      renderFighter(f, f._slug, FIGHTERS));
    sitemap.push(`${SITE}/fighter/${encodeURIComponent(f._slug)}/`);
    // แผนที่ redirect: URL เดิม -> ใหม่ (สำหรับ .htaccess / _redirects)
    redirects.push({ id: f.id, from: `/profile.html?id=${f.id}`,
                     to: `/fighter/${f._slug}/` });
  }

  // sitemap.xml
  const xml = ['<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...sitemap.map(u =>
      `  <url><loc>${u}</loc><lastmod>${TODAY}</lastmod><changefreq>weekly</changefreq></url>`),
    '</urlset>'].join("\n");
  fs.writeFileSync(path.join(OUT, "sitemap.xml"), xml);

  // ไฟล์ช่วย redirect (เลือกใช้ตามโฮสต์)
  fs.writeFileSync(path.join(OUT, "redirects.json"),
    JSON.stringify(redirects, null, 2));
  // Netlify style
  fs.writeFileSync(path.join(OUT, "_redirects"),
    redirects.map(r => `${r.from}  ${r.to}  301`).join("\n"));

  console.log(`สร้างเสร็จ ${FIGHTERS.length} หน้า`);
  console.log(`ประวัติชกที่ผูกเข้าไป ${HISTORY.length} แถว`);
  console.log(`sitemap: ${sitemap.length} URL`);
  console.log("\nตัวอย่าง URL ใหม่:");
  FIGHTERS.slice(0, 6).forEach(f =>
    console.log(`  profile.html?id=${f.id}  ->  /fighter/${f._slug}/`));
}

main();
