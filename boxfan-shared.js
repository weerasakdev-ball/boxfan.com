/* ═══════════════════════════════════════════════════════
   BOXFAN — SHARED UI (TM redesign)
   ต้องโหลด "หลัง" utils.js เพราะ override บางฟังก์ชัน
   ═══════════════════════════════════════════════════════ */

/* ── PLACEHOLDER: ใช้ noname1.png แทน emoji ─────────── */
(function(){
  var NONAME = 'images/noname1.png';
  // อัปเดต PH ให้ทุกที่ที่ใช้ fallback เป็น noname1.png
  window.PH = NONAME;
  // override cImg: ถ้าไม่มี filename → noname1.png
  if(typeof window.cImg === 'function'){
    var origCImg = window.cImg;
    window.cImg = function(filename, sz){
      if(!filename) return NONAME;
      return origCImg(filename, sz);
    };
  }
})();

/* ── SVG DEFS: symbol library เรียกด้วย <use href="#i-..."> ─ */
(function(){
  var defs = document.createElement('div');
  defs.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden';
  defs.setAttribute('aria-hidden','true');
  defs.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg"><defs>' +
    '<symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></symbol>' +
    '<symbol id="i-close" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></symbol>' +
    '<symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 5l7 7-7 7"/></symbol>' +
    '<symbol id="i-arrow-left" viewBox="0 0 24 24"><path d="M19 12H5M11 5l-7 7 7 7"/></symbol>' +
    '<symbol id="i-chev-down" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></symbol>' +
    '<symbol id="i-chev-up" viewBox="0 0 24 24"><path d="m6 15 6-6 6 6"/></symbol>' +
    '<symbol id="i-calendar" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></symbol>' +
    '<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></symbol>' +
    '<symbol id="i-trophy" viewBox="0 0 24 24"><path d="M6 9a6 6 0 0 0 12 0V3H6z"/><path d="M6 3H2v3a4 4 0 0 0 4 4M18 3h4v3a4 4 0 0 1-4 4M8 21h8M12 15v6"/></symbol>' +
    '<symbol id="i-chart" viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="M7 14l4-4 4 4 5-5"/></symbol>' +
    '<symbol id="i-users" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></symbol>' +
    '<symbol id="i-user" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></symbol>' +
    '<symbol id="i-scale" viewBox="0 0 24 24"><path d="M12 3v18M5 8h14l-3 8H8zM3 8h18"/></symbol>' +
    '<symbol id="i-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20z"/></symbol>' +
    '<symbol id="i-glove" viewBox="0 0 24 24"><path d="M7 4h8a3 3 0 0 1 3 3v6a4 4 0 0 1-4 4H8a2 2 0 0 1-2-2V6a2 2 0 0 1 1-2z"/><path d="M6 12h12M9 17v3h6v-3"/></symbol>' +
    '<symbol id="i-check" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></symbol>' +
    '<symbol id="i-fire" viewBox="0 0 24 24"><path d="M12 2s3 4 3 8a3 3 0 0 1-6 0c0-1 .5-2 1-3-2 1-4 3-4 7a6 6 0 0 0 12 0c0-6-6-12-6-12z"/></symbol>' +
    '<symbol id="i-star" viewBox="0 0 24 24"><path d="M12 2 15 8l6 1-4.5 4.5 1 6.5-5.5-3-5.5 3 1-6.5L3 9l6-1z"/></symbol>' +
    '<symbol id="i-bolt" viewBox="0 0 24 24"><path d="M13 2 3 14h9l-1 8 10-12h-9z"/></symbol>' +
    '<symbol id="i-alert" viewBox="0 0 24 24"><path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></symbol>' +
    '<symbol id="i-filter" viewBox="0 0 24 24"><path d="M22 3H2l8 9.46V19l4 2v-8.54z"/></symbol>' +
    '<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></symbol>' +
    '<symbol id="i-moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></symbol>' +
    '<symbol id="i-youtube" viewBox="0 0 24 24"><path d="M23 7 s0-3-3-3H4S1 4 1 7v10s0 3 3 3h16s3 0 3-3z"/><polygon points="10,9 16,12 10,15" fill="currentColor"/></symbol>' +
    '<symbol id="i-play" viewBox="0 0 24 24"><polygon points="6,4 20,12 6,20" fill="currentColor" stroke="none"/></symbol>' +
    '<symbol id="i-external" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14 21 3"/></symbol>' +
    '</defs></svg>';
  document.body ? document.body.appendChild(defs) : document.addEventListener('DOMContentLoaded', function(){ document.body.appendChild(defs); });
})();

/* ── Utility: SVG icon shorthand ─────────────────────── */
function ic(id, sz){
  return '<span class="ic" style="font-size:'+(sz||14)+'px"><svg viewBox="0 0 24 24"><use href="#'+id+'"/></svg></span>';
}

/* ── UTIL BAR (top thin bar) ─────────────────────────── */
function bfUtil(basePath){
  var base = basePath || '';
  return '<div class="util"><div class="util-in">' +
    '<a href="'+base+'about.html">เกี่ยวกับ</a>' +
    '<a href="'+base+'contact.html">ติดต่อ</a>' +
    '<a href="'+base+'blog/">บทความ</a>' +
    '<a href="'+base+'disclaimer.html">ข้อจำกัดความรับผิด</a>' +
    '<div class="util-right"><span class="util-date" id="bf-today"></span></div>' +
  '</div></div>';
}

/* ── HEADER (logo + search + theme toggle) ───────────── */
function bfHeader(basePath){
  var base = basePath || '';
  return '<header class="hdr"><div class="hdr-in">' +
    '<a class="logo" href="'+base+'index.html"><span class="logo-b">BOX</span>FAN</a>' +
    '<div class="search nav-search-wrap">' +
      ic('i-search',16).replace('class="ic"','class="ic search-ic"') +
      '<input type="text" id="sinput" placeholder="ค้นหานักมวย..." autocomplete="off">' +
      '<div class="sdrop" id="sdrop"></div>' +
    '</div>' +
    '<div class="hdr-right">' +
      '<button class="hdr-btn" onclick="bfToggleTheme()" aria-label="เปลี่ยนโหมด" title="เปลี่ยนโหมด">' +
        '<svg class="ic-sun" viewBox="0 0 24 24"><use href="#i-sun"/></svg>' +
        '<svg class="ic-moon" viewBox="0 0 24 24"><use href="#i-moon"/></svg>' +
      '</button>' +
    '</div>' +
  '</div></header>';
}

/* ── NAV — override utils.js nav() ────────────────────── */
window.nav = function(active, basePath){
  var base = basePath || '';
  var tabs = [
    {id:'ranking',  label:'หน้าแรก',        href:base+'index.html'},
    {id:'rankings', label:'อันดับ',         href:base+'rankings.html'},
    {id:'fighters', label:'นักมวย',         href:base+'fighters.html'},
    {id:'schedule', label:'โปรแกรมชก',     href:base+'schedule.html'},
    {id:'results',  label:'ผลการแข่งขัน',  href:base+'results.html'},
    {id:'compare',  label:'เปรียบเทียบ',   href:base+'compare.html'},
    {id:'weight',   label:'รุ่นน้ำหนัก',   href:base+'weight-classes.html'},
    {id:'tierlist', label:'Tier List',       href:base+'tierlist.html'},
    {id:'blog',     label:'บทความ',         href:base+'blog/'}
  ];
  var html = '<nav class="nav"><div class="nav-in">';
  tabs.forEach(function(t){
    html += '<a class="'+(active===t.id?'active':'')+'" href="'+t.href+'">'+t.label+'</a>';
  });
  html += '</div></nav>';
  return html;
};

/* ── BREADCRUMB ──────────────────────────────────────── */
function bfCrumb(items, basePath){
  var base = basePath || '';
  var html = '<div class="crumb">';
  items.forEach(function(it, i){
    if(i>0) html += '<span class="sep">›</span>';
    if(it.href) html += '<a href="'+(it.href.indexOf('http')===0?it.href:base+it.href)+'">'+it.label+'</a>';
    else html += '<span>'+it.label+'</span>';
  });
  html += '</div>';
  return html;
}

/* ── FOOTER — override utils.js renderFooter() ───────── */
window.renderFooter = function(extraText, basePath){
  var base = basePath || '';
  var el = document.getElementById('ft');
  if(!el) return;
  el.outerHTML = bfFooter(extraText, base);
};
function bfFooter(extraText, basePath){
  var base = basePath || '';
  var yr = new Date().getFullYear();
  return '<footer class="foot"><div class="foot-in">' +
    '<div class="foot-top">' +
      '<div>' +
        '<div class="foot-brand-l"><span class="r">BOX</span>FAN</div>' +
        '<div class="foot-brand-t">แหล่งรวมสถิติ อันดับ และผลการแข่งขันนักมวยไทย คิกบ็อกซิง และ MMA จากทุกรายการทั่วโลก บันทึกโดยแฟนกีฬา</div>' +
      '</div>' +
      '<div class="foot-col"><h4>เนื้อหา</h4>' +
        '<a href="'+base+'rankings.html">อันดับ</a>' +
        '<a href="'+base+'fighters.html">นักมวย</a>' +
        '<a href="'+base+'schedule.html">โปรแกรมชก</a>' +
        '<a href="'+base+'weight-classes.html">รุ่นน้ำหนัก</a>' +
      '</div>' +
      '<div class="foot-col"><h4>เกี่ยวกับ</h4>' +
        '<a href="'+base+'about.html">เกี่ยวกับเรา</a>' +
        '<a href="'+base+'contact.html">ติดต่อ</a>' +
        '<a href="'+base+'blog/">บทความ</a>' +
      '</div>' +
      '<div class="foot-col"><h4>กฎหมาย</h4>' +
        '<a href="'+base+'privacy.html">นโยบายความเป็นส่วนตัว</a>' +
        '<a href="'+base+'disclaimer.html">ข้อจำกัดความรับผิด</a>' +
      '</div>' +
    '</div>' +
    '<div class="foot-copy">© '+yr+' Boxfan · รวมผลมวยจากทุกรายการ บันทึกโดยแฟนมวย'+
    (extraText?' · '+extraText:'')+'</div>' +
  '</div></footer>';
}

/* ── HELPER: mount full page chrome (util + hdr + nav) ─ */
function bfMount(activeTab, opts){
  opts = opts || {};
  var base = opts.basePath || '';
  var slot = document.getElementById('bf-chrome');
  if(slot){
    slot.outerHTML = bfUtil(base) + bfHeader(base) + nav(activeTab, base);
  }
  var footSlot = document.getElementById('bf-foot');
  if(footSlot){
    footSlot.outerHTML = bfFooter(opts.footerExtra||'', base);
  }
  // set today date
  var td = document.getElementById('bf-today');
  if(td){
    try{ td.textContent = new Date().toLocaleDateString('th-TH',{weekday:'long',day:'numeric',month:'long',year:'numeric'}); }catch(e){}
  }
  // wire theme
  bfLoadTheme();
  // wire search
  if(typeof initSearch === 'function') initSearch();
}

/* ── THEME TOGGLE ─────────────────────────────────────── */
function bfToggleTheme(){
  var html = document.documentElement;
  var cur = html.getAttribute('data-theme') || 'light';
  var next = cur === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', next);
  try{ localStorage.setItem('boxfan-theme', next); }catch(e){}
  // update meta theme-color
  var meta = document.querySelector('meta[name="theme-color"]');
  if(meta) meta.setAttribute('content', next === 'dark' ? '#0f1520' : '#1a3661');
}
function bfLoadTheme(){
  try{
    var s = localStorage.getItem('boxfan-theme');
    if(s === 'dark' || s === 'light') document.documentElement.setAttribute('data-theme', s);
  }catch(e){}
}
// legacy alias
window.toggleTheme = bfToggleTheme;

/* run on load in case pages didn't call bfMount */
document.addEventListener('DOMContentLoaded', bfLoadTheme);

/* ── HELPER: build fighter cell (used in tables) ─────── */
function bfFxCell(f, opts){
  opts = opts || {};
  if(!f) return '<div class="fx"><div class="fx-img"><img src="'+PH+'" alt=""></div><div class="fx-info"><div class="fx-name">—</div></div></div>';
  var badge = opts.badge || '';
  var meta = opts.meta;
  if(meta === undefined) meta = '<span class="fx-flag">'+fl(f.country)+'</span> '+esc(f.division||'—');
  return '<div class="fx">' +
    '<div class="fx-img"><img src="'+cImg(f.image_filename,'sm')+'" loading="lazy" onerror="this.onerror=null;this.src=PH" alt=""></div>' +
    '<div class="fx-info">' +
      '<div class="fx-name">'+esc(f.name_th)+(badge?' '+badge:'')+'</div>' +
      (meta?'<div class="fx-meta">'+meta+'</div>':'') +
    '</div>' +
  '</div>';
}

/* ── HELPER: normalized result_type → icon class/text ── */
function bfResIcon(rt){
  var m = {win:['w','W'],loss:['l','L'],draw:['d','D'],nc:['n','N'],upcoming:['u','?']};
  return m[rt] || ['n','—'];
}
