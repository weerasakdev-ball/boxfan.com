/* ═══════════════════════════════════════════════════════════════
   BOXFAN · BOARD KIT
   ชุดเครื่องมือกลางสำหรับ bracket.html (จัดสายมวย) และ ranking.html (จัดอันดับ)
   ใช้ข้อมูลเดียวกับ tierlist.html: FIGHTERS จาก data/fighters_data.js
   และฟังก์ชัน cImg / fl / ds จาก utils.js

   ต้องโหลดตามลำดับนี้:
     <script src="data/fighters_data.js"></script>
     <script src="utils.js"></script>
     <script src="board-kit.js"></script>
   ═══════════════════════════════════════════════════════════════ */
(function () {
'use strict';

/* ── 0. ตั้งค่าแบรนด์ (แก้ตรงนี้ที่เดียว มีผลทุกหน้า) ── */
var BRAND = {
  domain:  'boxingfandom.com',
  channel: 'YouTube แฟนมวย'
};

var PH = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 88 88'%3E%3Crect width='88' height='88' fill='%231c2430'/%3E%3Ccircle cx='44' cy='36' r='14' fill='%23232d3b'/%3E%3Crect x='28' y='54' width='32' height='20' rx='8' fill='%23232d3b'/%3E%3C/svg%3E";

/* ── 1. helper ปลอดภัย (ไม่ชนกับฟังก์ชันใน utils.js) ── */
function h(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}
function divName(d) { try { return (typeof ds === 'function' && d) ? ds(d) : (d || ''); } catch (e) { return d || ''; } }
function flagHTML(c) { try { return (typeof fl === 'function' && c) ? fl(c) : ''; } catch (e) { return ''; } }

/* ── 2. รูปคมชัด ─────────────────────────────────────────────
   สาเหตุที่รูปเบลอมี 2 อย่าง:
   (1) ดึงรูปเล็กกว่าขนาดที่แสดงจริงบนจอ retina
   (2) ตอนเซฟ PNG html2canvas ขยายภาพ 3 เท่า รูปต้นทางเลยไม่พอ
   ตรงนี้จึงขอรูปจาก Cloudinary ที่ขนาด = ขนาดที่แสดง × 3 (รองรับทั้ง
   จอ retina และตอน export) ครอปจัตุรัสแบบหาหน้าอัตโนมัติ และลับคมเล็กน้อย */
function hiRes(url, px) {
  if (typeof url !== 'string') return url;
  var marker = '/image/upload/';
  var i = url.indexOf(marker);
  if (i === -1) return url;
  var head = url.slice(0, i + marker.length);
  var parts = url.slice(i + marker.length).split('/');
  if (parts.length > 1 &&
      /(^|,)(c_|w_|h_|g_|q_|f_|e_|ar_|dpr_|r_|b_|fl_|t_|x_|y_|z_)/.test(parts[0]) &&
      !/\.\w{2,4}$/.test(parts[0])) parts.shift();
  var tx = 'c_fill,g_auto,w_' + px + ',h_' + px + ',q_auto:best,f_auto,e_sharpen:50';
  return head + tx + '/' + parts.join('/');
}
/* displayPx = ขนาดกล่องรูปบนจอ (px) */
function imgURL(filename, displayPx) {
  if (!filename) return PH;
  var base = (typeof cImg === 'function') ? cImg(filename, 'sm') : filename;
  var px = Math.min(900, Math.max(120, Math.round((displayPx || 88) * 3)));
  return hiRes(base, px);
}

/* ── 3. ฐานข้อมูลนักมวย (FIGHTERS + รูปที่ผู้ใช้อัปโหลดเอง) ── */
var DB = (typeof FIGHTERS !== 'undefined' && Array.isArray(FIGHTERS)) ? FIGHTERS : [];
var byKey = {};
DB.forEach(function (f) {
  var key = 'db:' + f.id;
  byKey[key] = {
    key: key, id: f.id, custom: false,
    name: f.name_th || f.name_en || 'ไม่ระบุชื่อ',
    nameEn: (f.name_th && f.name_en) ? f.name_en : '',
    division: f.division || '', country: f.country || '',
    age: parseInt(f.age, 10) || 0, file: f.image_filename || ''
  };
});

var CUSTOM_KEY = 'boxfan-custom-fighters-v1';   // ใช้ร่วมกันทุกหน้า
var custom = load(CUSTOM_KEY, []);
custom.forEach(function (c) { byKey[c.key] = mkCustom(c); });
function mkCustom(c) {
  return { key: c.key, custom: true, name: c.name || 'นักมวยใหม่', nameEn: '', division: '', country: '', age: 0, img: c.img };
}
function saveCustom() {
  save(CUSTOM_KEY, custom.map(function (c) { return { key: c.key, name: byKey[c.key].name, img: c.img }; }));
}
function get(key) { return key ? (byKey[key] || null) : null; }
function photo(f, displayPx) { return !f ? PH : (f.custom ? f.img : imgURL(f.file, displayPx)); }
/* ใส่ crossorigin ให้รูป Cloudinary เพื่อให้ html2canvas วาดลง PNG ได้ */
function imgTag(f, displayPx, alt) {
  var src = photo(f, displayPx);
  var co = /^https?:/.test(src) ? ' crossorigin="anonymous"' : '';
  return '<img src="' + h(src) + '"' + co + ' alt="' + h(alt || '') + '" draggable="false" loading="lazy" decoding="async" onerror="this.onerror=null;this.src=\'' + PH + '\'">';
}

/* อัปโหลดรูปเอง: ครอปจัตุรัส 600px คุณภาพสูง */
function readImage(file) {
  return new Promise(function (res, rej) {
    var fr = new FileReader();
    fr.onerror = rej;
    fr.onload = function () {
      var img = new Image();
      img.onerror = rej;
      img.onload = function () {
        var side = Math.min(img.width, img.height);
        var sx = (img.width - side) / 2;
        var sy = Math.max(0, (img.height - side) * 0.15);   // เผื่อหัวภาพแนวตั้ง
        var out = Math.min(600, side);
        var c = document.createElement('canvas');
        c.width = c.height = out;
        var x = c.getContext('2d');
        x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
        x.fillStyle = '#1c2430'; x.fillRect(0, 0, out, out);
        x.drawImage(img, sx, sy, side, side, 0, 0, out, out);
        res(c.toDataURL('image/jpeg', 0.9));
      };
      img.src = fr.result;
    };
    fr.readAsDataURL(file);
  });
}
function addUploads(files) {
  var list = Array.prototype.filter.call(files || [], function (f) { return /^image\//.test(f.type); });
  return list.reduce(function (p, file) {
    return p.then(function (keys) {
      return readImage(file).then(function (img) {
        var key = 'up:' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
        var nm = (file.name || '').replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ').trim();
        var rec = { key: key, name: (!nm || /^image$/i.test(nm)) ? 'นักมวยใหม่' : nm, img: img };
        custom.unshift(rec); byKey[key] = mkCustom(rec);
        keys.push(key); return keys;
      }, function () { toast('เปิดไฟล์ ' + file.name + ' ไม่ได้'); return keys; });
    });
  }, Promise.resolve([])).then(function (keys) {
    if (keys.length) { saveCustom(); toast('เพิ่มนักมวย ' + keys.length + ' คน แตะชื่อใต้รูปเพื่อแก้ไข'); }
    return keys;
  });
}
function removeCustom(key) {
  custom = custom.filter(function (c) { return c.key !== key; });
  delete byKey[key]; saveCustom();
}

/* ── 4. localStorage ── */
function load(k, def) {
  try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : def; } catch (e) { return def; }
}
var saveTimers = {};
function save(k, v) {
  clearTimeout(saveTimers[k]);
  saveTimers[k] = setTimeout(function () {
    try { localStorage.setItem(k, JSON.stringify(v)); }
    catch (e) { toast('บันทึกไม่ได้ พื้นที่เก็บในเบราว์เซอร์เต็ม ลองลบรูปที่อัปโหลดเองที่ไม่ใช้ออก'); }
  }, 150);
}

/* ── 5. toast ── */
var toastEl, toastT;
function toast(msg) {
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.className = 'bk-toast'; toastEl.setAttribute('role', 'status'); toastEl.setAttribute('aria-live', 'polite');
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = msg; toastEl.classList.add('show');
  clearTimeout(toastT); toastT = setTimeout(function () { toastEl.classList.remove('show'); }, 2400);
}

/* ── 6. คลังนักมวย (ตัวกรองแบบเดียวกับหน้า Tier List) ──
   opts = { root, used: fn()->Set ของ key ที่ถูกใช้, onChange: fn() เรียกเมื่อผู้ใช้เพิ่ม/ลบ/แก้ชื่อ } */
function Pool(opts) {
  var root = opts.root, limit = 24, PAGE = 24;
  root.innerHTML =
    '<div class="filter-bar bk">' +
      '<div style="position:relative;display:flex;align-items:center"><span class="ic" style="position:absolute;left:11px;font-size:14px;color:var(--tx-4);pointer-events:none"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg></span>' +
      '<input type="text" class="filter-input" data-f="q" style="padding-left:34px" placeholder="ค้นหาชื่อนักมวย (ไทย/อังกฤษ)..." aria-label="ค้นหาชื่อนักมวย"></div>' +
      '<select class="filter-input" data-f="div" aria-label="รุ่น"><option value="all">ทุกรุ่น</option></select>' +
      '<select class="filter-input" data-f="cty" aria-label="สัญชาติ"><option value="all">ทุกสัญชาติ</option></select>' +
      '<select class="filter-input" data-f="age" aria-label="อายุ"><option value="all">ทุกอายุ</option><option value="under20">ต่ำกว่า 20 ปี</option><option value="20-25">20 - 25 ปี</option><option value="26-30">26 - 30 ปี</option><option value="over30">มากกว่า 30 ปี</option></select>' +
      '<span class="bk-count" data-f="count"></span>' +
    '</div>' +
    '<div class="boxer-pool" data-drop="pool" aria-label="คลังนักมวย"></div>' +
    '<div class="load-more-wrap hidden"><button class="btn btn-ghost" type="button" style="margin-top:12px">โหลดนักมวยเพิ่มเติม</button></div>';

  var q = root.querySelector('[data-f="q"]'), sDiv = root.querySelector('[data-f="div"]'),
      sCty = root.querySelector('[data-f="cty"]'), sAge = root.querySelector('[data-f="age"]'),
      cnt = root.querySelector('[data-f="count"]'), box = root.querySelector('.boxer-pool'),
      more = root.querySelector('.load-more-wrap');

  var divs = {}, ctys = {};
  DB.forEach(function (f) { if (f.division) divs[f.division] = 1; if (f.country) ctys[f.country] = 1; });
  Object.keys(divs).sort().forEach(function (d) { sDiv.insertAdjacentHTML('beforeend', '<option value="' + h(d) + '">' + h(divName(d)) + '</option>'); });
  Object.keys(ctys).sort().forEach(function (c) { sCty.insertAdjacentHTML('beforeend', '<option value="' + h(c) + '">' + h(c) + '</option>'); });

  function matches(f) {
    var s = q.value.trim().toLowerCase();
    if (s && (f.name + ' ' + f.nameEn).toLowerCase().indexOf(s) === -1) return false;
    if (f.custom) return sDiv.value === 'all' && sCty.value === 'all' && sAge.value === 'all';
    if (sDiv.value !== 'all' && f.division !== sDiv.value) return false;
    if (sCty.value !== 'all' && f.country !== sCty.value) return false;
    var a = f.age, g = sAge.value;
    if (g === 'under20') return a > 0 && a < 20;
    if (g === '20-25') return a >= 20 && a <= 25;
    if (g === '26-30') return a >= 26 && a <= 30;
    if (g === 'over30') return a > 30;
    return true;
  }
  function card(f, used) {
    var tip = f.name + (f.division ? ' · ' + divName(f.division) : '');
    return '<div class="boxer-card' + (used ? ' is-used' : '') + (f.custom ? ' is-custom' : '') + '" data-key="' + h(f.key) + '" data-src="pool" data-tooltip="' + h(tip) + '">' +
      '<div class="boxer-card-img">' + imgTag(f, 88, '') + '</div>' +
      (f.custom
        ? '<div class="boxer-card-name bk-edit" contenteditable="true" spellcheck="false" data-rename="' + h(f.key) + '" aria-label="ชื่อนักมวย">' + h(f.name) + '</div>' +
          '<button class="bk-del" type="button" data-delcustom="' + h(f.key) + '" aria-label="ลบ ' + h(f.name) + '">×</button>'
        : '<div class="boxer-card-name">' + h(f.name) + '</div>') +
      '</div>';
  }
  function render() {
    var used = opts.used ? opts.used() : {};
    var list = custom.map(function (c) { return byKey[c.key]; }).concat(DB.map(function (f) { return byKey['db:' + f.id]; }))
      .filter(function (f) { return f && matches(f); });
    var html = '<label class="bk-upload" title="เพิ่มรูปนักมวยจากเครื่อง">+ เพิ่มรูป<br>นักมวยเอง<input type="file" accept="image/*" multiple></label>';
    html += list.slice(0, limit).map(function (f) { return card(f, used[f.key]); }).join('');
    if (!list.length) html += '<div class="bk-pool-empty">' + (DB.length ? 'ไม่พบนักมวยที่ตรงกับตัวกรอง' : 'ไม่พบข้อมูลนักมวย ตรวจสอบ data/fighters_data.js') + '</div>';
    box.innerHTML = html;
    cnt.textContent = list.length + ' คน';
    more.classList.toggle('hidden', list.length <= limit);
  }
  function reset() { limit = PAGE; render(); }
  [q, sDiv, sCty, sAge].forEach(function (el) { el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', reset); });
  more.querySelector('button').addEventListener('click', function () { limit += PAGE; render(); });

  root.addEventListener('change', function (e) {
    if (e.target.type === 'file' && e.target.files.length) {
      addUploads(e.target.files).then(function () { render(); opts.onChange && opts.onChange(); });
    }
  });
  root.addEventListener('click', function (e) {
    var d = e.target.closest('[data-delcustom]');
    if (d) { removeCustom(d.dataset.delcustom); render(); opts.onChange && opts.onChange(d.dataset.delcustom); }
  });
  root.addEventListener('input', function (e) {
    var r = e.target.closest('[data-rename]'); if (!r) return;
    var f = byKey[r.dataset.rename]; if (!f) return;
    f.name = r.textContent.trim() || 'ไม่มีชื่อ'; saveCustom();
    opts.onRename && opts.onRename(f);
  });
  root.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.closest('[data-rename]')) { e.preventDefault(); e.target.blur(); }
  });
  /* ลากไฟล์รูปจากเครื่องมาวางในคลัง */
  box.addEventListener('dragover', function (e) { if (hasFiles(e)) { e.preventDefault(); box.classList.add('drop-over'); } });
  box.addEventListener('dragleave', function () { box.classList.remove('drop-over'); });
  box.addEventListener('drop', function (e) {
    if (!hasFiles(e)) return; e.preventDefault(); box.classList.remove('drop-over');
    addUploads(e.dataTransfer.files).then(function () { render(); opts.onChange && opts.onChange(); });
  });

  render();
  return { render: render, el: box };
}
function hasFiles(e) { return e.dataTransfer && Array.prototype.indexOf.call(e.dataTransfer.types || [], 'Files') !== -1; }

/* วาง Ctrl+V รูปที่คัดลอกไว้ */
function onPaste(cb) {
  document.addEventListener('paste', function (e) {
    if (e.target.closest && e.target.closest('[contenteditable],input,textarea')) return;
    var files = e.clipboardData && e.clipboardData.files;
    if (!files || !files.length) return;
    e.preventDefault(); addUploads(files).then(cb);
  });
}

/* ── 7. ระบบลากวาง (Pointer Events) ──
   ใช้ได้ทั้งเมาส์และนิ้ว (ของเดิม HTML5 drag ใช้บนมือถือไม่ได้)
   เมาส์: กดแล้วลาก | มือถือ: แตะค้างครู่หนึ่งแล้วลาก, ปัดปกติ = เลื่อนจอ
   ของที่ลากได้: [data-key][data-src]   ที่วางได้: [data-drop]
   opts = { onDrop(src, target), onTap(src), accept(src, target) } */
function Drag(opts) {
  var D = null, ghost = null, over = null, raf = 0;
  var HOLD = 220, SLOP = 8;

  function setOver(t) {
    if (over === t) return;
    if (over) over.classList.remove('drop-over');
    over = t; if (over) over.classList.add('drop-over');
  }
  function targetAt(x, y) {
    var el = document.elementFromPoint(x, y);
    var t = el && el.closest('[data-drop]');
    if (t && opts.accept && !opts.accept(D, t)) t = null;
    return t;
  }
  function activate() {
    D.active = true;
    var img = D.el.querySelector('img');
    ghost = document.createElement('div'); ghost.className = 'bk-ghost';
    ghost.innerHTML = img ? '<img src="' + h(img.currentSrc || img.src) + '" alt="">' : '';
    document.body.appendChild(ghost); document.body.classList.add('bk-dragging');
    try { window.getSelection().removeAllRanges(); } catch (e) {}
    place(); loop();
  }
  function place() {
    if (!ghost) return;
    ghost.style.transform = 'translate(' + (D.x - 36) + 'px,' + (D.y - 36) + 'px)';
    setOver(targetAt(D.x, D.y));
  }
  /* เลื่อนหน้าจออัตโนมัติเมื่อลากไปชิดขอบ */
  function loop() {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(function step() {
      if (!D || !D.active) return;
      var e = 80, v = 0, H = window.innerHeight;
      if (D.y < e) v = -Math.ceil((e - D.y) / 4);
      else if (D.y > H - e) v = Math.ceil((D.y - (H - e)) / 4);
      if (v) { window.scrollBy(0, v); setOver(targetAt(D.x, D.y)); }
      var hs = document.elementFromPoint(D.x, D.y);
      hs = hs && hs.closest('[data-hscroll]');
      if (hs) {
        var r = hs.getBoundingClientRect(), hv = 0;
        if (D.x < r.left + 60) hv = -8; else if (D.x > r.right - 60) hv = 8;
        if (hv) { hs.scrollLeft += hv; setOver(targetAt(D.x, D.y)); }
      }
      raf = requestAnimationFrame(step);
    });
  }
  function end(drop) {
    var d = D; D = null;
    if (!d) return;
    clearTimeout(d.timer); cancelAnimationFrame(raf);
    if (ghost) { ghost.remove(); ghost = null; }
    document.body.classList.remove('bk-dragging');
    var t = over; setOver(null);
    if (!drop) return;
    if (d.active) { if (t) opts.onDrop(d, t); }
    else if (opts.onTap) opts.onTap(d);
  }

  document.addEventListener('pointerdown', function (e) {
    if (D || e.button > 0) return;
    if (e.target.closest('[contenteditable],button,input,select,textarea,a,label')) return;
    var el = e.target.closest('[data-key][data-src]'); if (!el) return;
    D = { el: el, key: el.dataset.key, src: el.dataset.src, data: el.dataset, x0: e.clientX, y0: e.clientY, x: e.clientX, y: e.clientY,
          active: false, touch: e.pointerType !== 'mouse', pid: e.pointerId, timer: 0 };
    if (D.touch) D.timer = setTimeout(function () { if (D && !D.active) { activate(); if (navigator.vibrate) navigator.vibrate(10); } }, HOLD);
    else e.preventDefault();
  });
  document.addEventListener('pointermove', function (e) {
    if (!D || e.pointerId !== D.pid) return;
    D.x = e.clientX; D.y = e.clientY;
    if (!D.active) {
      var dist = Math.hypot(D.x - D.x0, D.y - D.y0);
      if (D.touch) { if (dist > SLOP) { clearTimeout(D.timer); D = null; } return; }   // นิ้วปัด = เลื่อนจอ
      if (dist > 5) activate();
      return;
    }
    place();
  });
  /* กันการลากแล้วไปคลุมข้อความทั้งหน้า */
  document.addEventListener('mousedown', function (e) {
    if (e.target.closest('[data-key][data-src]') && !e.target.closest('[contenteditable],button,input,select,textarea,a,label')) e.preventDefault();
  });
  document.addEventListener('pointerup', function (e) { if (D && e.pointerId === D.pid) end(true); });
  document.addEventListener('pointercancel', function (e) { if (D && e.pointerId === D.pid) end(false); });
  document.addEventListener('touchmove', function (e) { if (D && D.active) e.preventDefault(); }, { passive: false });
  document.addEventListener('contextmenu', function (e) { if (D || (e.target.closest && e.target.closest('[data-src]'))) e.preventDefault(); });
  window.addEventListener('blur', function () { end(false); });
}

/* ── 8. บันทึกเป็น PNG (html2canvas ตัวเดียวกับหน้า Tier List) ──
   ระหว่างสร้างภาพ จะใส่ class bk-exporting ที่ body (ซ่อนปุ่ม/ของที่ไม่ต้องการในภาพ)
   opts = { filename, bg, measure() -> {width,height}, prepare(cloneDoc) } */
var busy = false;
function exportPNG(el, opts) {
  opts = opts || {};
  if (busy) return;
  if (typeof html2canvas !== 'function') { toast('โหลดตัวสร้างภาพไม่สำเร็จ ลองรีเฟรชหน้าอีกครั้ง'); return; }
  busy = true;
  var ov = document.createElement('div');
  ov.className = 'dl-overlay show';
  ov.innerHTML = '<div class="dl-modal"><div class="dl-spinner" style="display:block"></div><div class="dl-modal-title">กำลังสร้างภาพ...</div><div class="dl-modal-sub">รอโหลดรูปนักมวยความละเอียดสูงสักครู่</div></div>';
  document.body.appendChild(ov);

  /* ช่องข้อความที่ว่างอยู่ ไม่ต้องโชว์ข้อความตัวอย่างในภาพ */
  var hidden = Array.prototype.filter.call(el.querySelectorAll('.bk-edit[data-ph]'), function (e) { return !e.textContent.trim(); });
  hidden.forEach(function (e) { e.style.display = 'none'; });
  document.body.classList.add('bk-exporting');
  function restore() {
    document.body.classList.remove('bk-exporting');
    hidden.forEach(function (e) { e.style.display = ''; });
  }

  /* รอรูปทุกใบโหลดเสร็จ (รูป lazy ที่ยังไม่โหลดจะว่างใน PNG) */
  var imgs = Array.prototype.slice.call(el.querySelectorAll('img'));
  imgs.forEach(function (i) { i.loading = 'eager'; });
  var wait = Promise.all(imgs.map(function (i) {
    return (i.complete && i.naturalWidth) ? 0 : new Promise(function (r) { i.addEventListener('load', r, { once: true }); i.addEventListener('error', r, { once: true }); setTimeout(r, 8000); });
  }));

  wait.then(function () {
    return new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
  }).then(function () {
    var m = opts.measure ? opts.measure() : {};
    var w = Math.ceil(m.width || el.scrollWidth), hgt = Math.ceil(m.height || el.scrollHeight);
    var scale = Math.max(2, Math.min(3, 9000 / Math.max(w, hgt)));   // คมชัดแต่ไม่ใหญ่จนมือถือค้าง
    return html2canvas(el, {
      backgroundColor: opts.bg || '#161c24', scale: scale, useCORS: true, imageTimeout: 15000, logging: false,
      width: w, height: hgt, windowWidth: Math.max(document.documentElement.clientWidth, w + 80),
      onclone: function (doc) {
        doc.body.classList.add('bk-exporting');
        if (opts.prepare) opts.prepare(doc, w);
      }
    });
  }).then(function (canvas) {
    restore();
    return new Promise(function (res) { canvas.toBlob(res, 'image/png'); });
  }).then(function (blob) {
    var name = (opts.filename || 'boxfan') + '-' + new Date().toISOString().slice(0, 10) + '.png';
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a'); a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    toast('บันทึกภาพแล้ว');
  }).catch(function (err) {
    restore(); console.error(err); toast('สร้างภาพไม่สำเร็จ ลองใหม่อีกครั้ง');
  }).then(function () { ov.remove(); busy = false; });
}

/* ── 9. เครดิตท้ายภาพ ── */
function creditHTML() {
  return '<div class="bk-credit"><span class="lg">BOX<span>FAN</span></span><span>' + h(BRAND.domain) + '</span>' +
         '<span class="yt"><i aria-hidden="true"></i>' + h(BRAND.channel) + '</span></div>';
}

/* ── 10. ช่องค้นหาบน nav (เหมือน tierlist.html) ── */
function initNav() {
  var tog = document.getElementById('search-toggle'), panel = document.getElementById('search-panel');
  var inp = document.getElementById('sinput'), drop = document.getElementById('sdrop');
  if (tog && panel) {
    tog.addEventListener('click', function () {
      panel.classList.toggle('open');
      if (panel.classList.contains('open') && inp) setTimeout(function () { inp.focus(); }, 50);
    });
    panel.addEventListener('click', function (e) { e.stopPropagation(); });
    document.addEventListener('click', function (e) { if (!e.target.closest('#search-toggle')) panel.classList.remove('open'); });
  }
  if (inp && drop) inp.addEventListener('input', function () {
    var s = inp.value.trim().toLowerCase();
    if (!s) { drop.innerHTML = ''; return; }
    var hits = DB.filter(function (f) { return (f.name_th || '').toLowerCase().indexOf(s) !== -1 || (f.name_en || '').toLowerCase().indexOf(s) !== -1; }).slice(0, 7);
    drop.innerHTML = hits.length ? hits.map(function (f) {
      var k = byKey['db:' + f.id];
      return '<a class="si" href="profile.html?id=' + encodeURIComponent(f.id) + '">' + imgTag(k, 36, '') +
        '<div><div class="si-nm">' + h(f.name_th || f.name_en) + '</div><div class="si-mt">' + flagHTML(f.country) + ' ' + h(divName(f.division)) + '</div></div></a>';
    }).join('') : '<div class="s-empty">ไม่พบ "' + h(inp.value) + '"</div>';
  });
  var yr = document.getElementById('yr-ft'); if (yr) yr.textContent = new Date().getFullYear();
}

window.BoardKit = {
  BRAND: BRAND, PH: PH, h: h, divName: divName, flagHTML: flagHTML,
  get: get, photo: photo, imgTag: imgTag, imgURL: imgURL, addUploads: addUploads,
  load: load, save: save, toast: toast, Pool: Pool, Drag: Drag, onPaste: onPaste, hasFiles: hasFiles,
  exportPNG: exportPNG, creditHTML: creditHTML, initNav: initNav
};
})();
