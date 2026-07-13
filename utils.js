/* ═══════════════════════════════════════════════════════════════
   BOXFAN — utils.js
   Helper functions: nav, footer, SEO, image, scoring, data
   ═══════════════════════════════════════════════════════════════ */

/* ── Constants ───────────────────────────────────────────────────────────── */
var BRAND = 'Boxfan';
var SITE  = 'https://boxingfandom.com';
var CLOUD = 'dpvyl7nan'; /* ← Cloudinary cloud name */
var PH    = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'%3E%3Crect width='80' height='80' fill='%23f1f3f4'/%3E%3Ctext x='50%25' y='55%25' text-anchor='middle' dominant-baseline='middle' font-size='36'%3E%F0%9F%A5%8A%3C/text%3E%3C/svg%3E";

/* ── Image helpers ───────────────────────────────────────────────────────── */
var IMG_SIZES = { sm: 'w_80,h_80', md: 'w_160,h_160', lg: 'w_600,h_400', xl: 'w_800,h_600' };

function cImg(filename, sz) {
    if (!filename) return PH;
    var d = IMG_SIZES[sz] || IMG_SIZES.sm;
    var clean = filename.replace(/\.(jpg|jpeg|png|webp)$/i, '');
    /* lg ใช้ g_north เพื่อโชวตั้งแต่หัวลงมา, sm/md ใช้ g_face crop หน้า */
    var gravity = (sz === 'lg') ? 'g_north' : 'g_face';
    return 'https://res.cloudinary.com/' + CLOUD + '/image/upload/c_fill,' + gravity + ',' + d + ',f_auto,q_auto/' + encodeURIComponent(clean);
}

function oppImg(name, sz) {
    if (!name) return PH;
    var f = FIGHTERS.find(function(x) { return x.name_th === name || x.name_en === name; });
    return (f && f.image_filename) ? cImg(f.image_filename, sz || 'sm') : PH;
}

/* ── Stars ───────────────────────────────────────────────────────────────── */
function stars(val) {
    var v = parseFloat(val) || 0;
    var full = Math.floor(v);
    var half = (v - full) >= 0.5 ? 1 : 0;
    var empty = 5 - full - half;
    var s = '<span class="stars">';
    for (var i = 0; i < full; i++) s += '★';
    if (half) s += '½';
    s += '<span class="stars-empty">';
    for (var j = 0; j < empty; j++) s += '★';
    s += '</span></span>';
    return s;
}

/* ── Flag map ────────────────────────────────────────────────────────────── */
var FL = {
    'ไทย':          '🇹🇭',
    'ญี่ปุ่น':       '🇯🇵',
    'เกาหลีใต้':    '🇰🇷',
    'จีน':           '🇨🇳',
    'รัสเซีย':       '🇷🇺',
    'บราซิล':        '🇧🇷',
    'เวเนซุเอลา':   '🇻🇪',
    'ฝรั่งเศส':      '🇫🇷',
    'ฝรั่งเศส/ไทย': '🇫🇷',
    'สหราชอาณาจักร':'🇬🇧',
    'โมร็อกโก':     '🇲🇦',
    'เวียดนาม':     '🇻🇳',
    'เมียนมา':      '🇲🇲',
    'ตุรกี':         '🇹🇷'
};
function fl(c) { return FL[c] || '🏳'; }

/* ── HTML escape (ป้องกัน XSS / โครงสร้างพัง เวลาแสดงชื่อ-ข้อมูลที่มาจาก data) ── */
var ESC_MAP = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function(c) { return ESC_MAP[c]; });
}

/* ── Division shortname ─────────────────────────────────────────────────── */
function ds(d) {
    var k = divKey(d);
    if (!k) return d || '';
    for (var i = 0; i < DIV_MAP.length; i++) if (DIV_MAP[i].key === k) return DIV_MAP[i].en;
    return d;
}

/* ── Score / History (อัปเดตระบบคะแนนใหม่ล่าสุด 100%) ───────────────────── */
function score(h) {
    var s = 0;
    (h || []).forEach(function(x) {
        if (x.result_type === 'win') {
            // เช็คว่าชนะน็อค (KO/TKO)
            if (x.decision && /ko|tko/i.test(x.decision)) {
                s += 3; 
            } else {
                s += 2; // ชนะคะแนน 
            }
        } else if (x.result_type === 'loss') {
            // เช็คว่าแพ้น็อค (KO/TKO)
            if (x.decision && /ko|tko/i.test(x.decision)) {
                s -= 3; 
            } else {
                s -= 2; // แพ้คะแนน
            }
        }
        // ถ้าเป็น Draw หรือ NC จะไม่เข้าเงื่อนไข (บวก 0 คะแนน)
    });
    return s;
}

function hist(fid) { return HISTORY.filter(function(h) { return h.fighter_id === fid; }); }

/* ══════════════════════════════════════════════════════════════
   RANKING CORE — ใช้ร่วมกันทุกหน้า (index / rankings / weight-classes)
   เพื่อให้ "เงื่อนไขเดียวกัน = อันดับเดียวกัน" รับประกันด้วยโค้ดชุดเดียว
   ══════════════════════════════════════════════════════════════ */

/* ปีอ้างอิงของการจัดอันดับ ("ฤดูกาลปัจจุบัน")
   - ถ้ามีผลการแข่งในปีปฏิทินนี้ → ใช้ปีนี้
   - ถ้ายังไม่มี (ข้อมูลตามหลังปฏิทิน) → ถอยไปใช้ "ปีล่าสุดที่มีข้อมูลจริง"
   เดิม index/weight-classes ฮาร์ดโค้ด new Date().getFullYear() ทำให้พอขึ้นปีใหม่
   ที่ยังไม่มีไฟต์ ตารางจะว่าง ในขณะที่ rankings ถอยไปปีล่าสุดอยู่แล้ว → ไม่ตรงกัน */
function rankingYear() {
    var cur = String(new Date().getFullYear());
    if (typeof HISTORY === 'undefined') return cur;
    var years = {};
    HISTORY.forEach(function(h) {
        if (h.date && h.result_type !== 'upcoming') years[String(h.date).substr(0, 4)] = 1;
    });
    if (years[cur]) return cur;
    var arr = Object.keys(years).sort();
    return arr.length ? arr[arr.length - 1] : cur;
}

/* คำนวณสถิติของนักมวย 1 คน ตาม "หน้าต่าง" ที่กำหนด (ปี / กติกา)
   คืนค่าคีย์มาตรฐานที่ทุกหน้าใช้เหมือนกัน:
   _w _l _total _s _wr _ko(%) _koCount _form _streak _lastDate _divKey _windowCount
   opts = { year:'YYYY'|'all', rules:'มวยไทย'|'คิกบ็อกซิง'|'MMA'|'all' } */
function computeStats(f, opts) {
    opts = opts || {};
    var year  = opts.year  || 'all';
    var rules = opts.rules || 'all';

    var all = (typeof hist !== 'undefined' ? hist(f.id) : [])
        .filter(function(x) { return x.result_type !== 'upcoming'; });

    var h = all.filter(function(x) {
        if (year !== 'all' && !(x.date && String(x.date).startsWith(year))) return false;
        if (rules !== 'all' && x.rules !== rules) return false;
        return true;
    });

    var w  = h.filter(function(x) { return x.result_type === 'win'; }).length;
    var l  = h.filter(function(x) { return x.result_type === 'loss'; }).length;
    var koWins = h.filter(function(x) {
        return x.result_type === 'win' && x.decision && /ko|tko/i.test(x.decision);
    }).length;

    /* form = 5 ไฟต์ล่าสุด (เรียงตามวันที่แน่นอน ไม่พึ่งลำดับใน data) เก่า→ใหม่ */
    var byDate = h.slice().sort(function(a, b) {
        return String(b.date || '').localeCompare(String(a.date || ''));
    });
    var form = byDate.slice(0, 5).reverse();

    var sd = (typeof fightStreak !== 'undefined') ? fightStreak(h) : { streak: 0, lastDate: '' };

    return Object.assign({}, f, {
        _w: w, _l: l, _total: w + l,
        _s: (typeof score !== 'undefined') ? score(h) : 0,
        _wr: (w + l) > 0 ? Math.round(w / (w + l) * 100) : 0,
        _ko: w > 0 ? Math.round(koWins / w * 100) : 0,  /* KO% */
        _koCount: koWins,                               /* จำนวน KO (สำหรับคอลัมน์ "KO สูงสุด") */
        _form: form,
        _streak: sd.streak, _lastDate: sd.lastDate,
        _divKey: (typeof divKey !== 'undefined') ? divKey(f.division) : null,
        _windowCount: h.length                          /* จำนวนไฟต์ (รวม draw/nc) ในหน้าต่างนี้ */
    });
}

/* ตัวเปรียบเทียบมาตรฐานสำหรับจัดอันดับ (ต้องเหมือนกันทุกหน้า)
   คะแนน → ชนะรวด → วันชกล่าสุด → จำนวนชนะ */
function rankSort(a, b) {
    return (b._s - a._s)
        || (b._streak - a._streak)
        || (String(b._lastDate || '').localeCompare(String(a._lastDate || '')))
        || (b._w - a._w);
}

/* รวมทุกอย่าง: กรอง → คำนวณ → คัดเฉพาะคนที่มีผลชนะ/แพ้ในหน้าต่าง → เรียง
   opts เพิ่มเติม: division = divKey|'all', requirePlayed = true (ค่าเริ่มต้น) */
function rankFighters(opts) {
    if (typeof FIGHTERS === 'undefined') return [];
    opts = opts || {};
    var division = opts.division || 'all';
    var requirePlayed = (opts.requirePlayed !== false);
    var list = FIGHTERS.map(function(f) { return computeStats(f, opts); });
    list = list.filter(function(f) {
        if (division !== 'all' && f._divKey !== division) return false;
        if (requirePlayed && f._total === 0) return false;
        return true;
    });
    list.sort(rankSort);
    return opts.max ? list.slice(0, opts.max) : list;
}

/* ── Streak & last fight date (สำหรับ tie-break อันดับ) ─────────────────── */
function fightStreak(h) {
    var past = (h || []).filter(function(x) { return x.result_type !== 'upcoming' && x.date; });
    past.sort(function(a, b) { return b.date.localeCompare(a.date); }); // ล่าสุดก่อน
    var streak = 0;
    for (var i = 0; i < past.length; i++) {
        if (past[i].result_type === 'win') streak++;
        else break;
    }
    var lastDate = past.length ? past[0].date : '';
    return { streak: streak, lastDate: lastDate };
}

/* ── Division taxonomy (SINGLE SOURCE OF TRUTH ใช้ร่วมกันทุกหน้า) ──────────────
   เดิม index/rankings ใช้ 7 รุ่น ส่วน weight-classes สร้างชุด 10 รุ่นของตัวเอง
   ทำให้นักมวยคนเดียวกันถูกจัดคนละรุ่น → ย้ายมารวมไว้ที่เดียว พร้อม meta (SEO)
   เรียงจากรุ่นใหญ่ → เล็ก (ใช้เป็นลำดับแสดงเมนูได้เลย) ───────────────────────── */
var DIV_MAP = [
    { key: 'heavy',      label: 'เฮฟวีเวต',      en: 'Heavyweight',        kw: 'เฮฟวี',    weight: '225 - 265', desc: 'พิกัดน้ำหนักยักษ์ใหญ่ พลังทำลายล้างสูงสุด' },
    { key: 'lightheavy', label: 'ไลต์เฮฟวีเวต',  en: 'Light Heavyweight',  kw: 'ไลต์เฮฟ',  weight: '205 - 225', desc: 'การผสมผสานระหว่างความเร็วและพละกำลังมหาศาล' },
    { key: 'middle',     label: 'มิดเดิลเวต',    en: 'Middleweight',       kw: 'มิดเดิล',  weight: '185 - 205', desc: 'รุ่นน้ำหนักกลางที่เต็มไปด้วยนักชกเชิงสูง' },
    { key: 'welter',     label: 'เวลเตอร์เวต',   en: 'Welterweight',       kw: 'เวลเตอร์', weight: '170 - 185', desc: 'พิกัดยอดฮิตที่มีการแข่งขันสูงที่สุดรุ่นหนึ่ง' },
    { key: 'light',      label: 'ไลต์เวต',       en: 'Lightweight',        kw: 'ไลต์',     weight: '155 - 170', desc: 'รุ่นที่มีนักชกซูเปอร์สตาร์มากมาย' },
    { key: 'feather',    label: 'เฟเธอร์เวต',    en: 'Featherweight',      kw: 'เฟเธอร์',  weight: '145 - 155', desc: 'ความรวดเร็วและเทคนิคแพรวพราว' },
    { key: 'bantam',     label: 'แบนตัมเวต',     en: 'Bantamweight',       kw: 'แบนตัม',   weight: '135 - 145', desc: 'การออกอาวุธที่ว่องไวและแม่นยำ' },
    { key: 'fly',        label: 'ฟลายเวต',       en: 'Flyweight',          kw: 'ฟลาย',     weight: '125 - 135', desc: 'พิกัดน้ำหนักที่เน้นความคล่องตัวระดับสูงสุด' },
    { key: 'straw',      label: 'สตรอว์เวต',     en: 'Strawweight',        kw: 'สตรอว์',   weight: '115 - 125', desc: 'รุ่นเล็กที่เต็มไปด้วยพลังและความดุดัน' },
    { key: 'atom',       label: 'อะตอมเวต',      en: 'Atomweight',         kw: 'อะตอม',    weight: '105 - 115', desc: 'พิกัดน้ำหนักเล็กที่สุด รวดเร็วดุจสายฟ้า' }
];
/* keyword lookup ที่ derive จาก DIV_MAP (กันหลุด/พิมพ์ซ้ำ) */
var DIV_KW = {};
DIV_MAP.forEach(function(d) { DIV_KW[d.key] = d.kw; });
/* ลำดับการ "จับคู่" ต้องเช็ครุ่นที่ชื่อจำเพาะก่อนรุ่นที่ชื่อสั้นกว่า
   เช่น "ไลต์เฮฟวีเวต" มีทั้งคำว่า "ไลต์" และ "เฮฟวี" → ต้องจับ lightheavy ก่อน
   ไม่งั้นจะถูกจัดผิดไปเป็น light หรือ heavy (บั๊กเดิมของ divKey) */
var DIV_MATCH_ORDER = ['lightheavy', 'middle', 'welter', 'atom', 'straw', 'fly', 'bantam', 'feather', 'light', 'heavy'];
function divKey(d) {
    if (!d) return null;
    for (var i = 0; i < DIV_MATCH_ORDER.length; i++) {
        var k = DIV_MATCH_ORDER[i];
        if (DIV_KW[k] && d.indexOf(DIV_KW[k]) !== -1) return k;
    }
    return null;
}
function divLabel(key) {
    for (var i = 0; i < DIV_MAP.length; i++) if (DIV_MAP[i].key === key) return DIV_MAP[i].label;
    return key;
}
function divMeta(key) {
    for (var i = 0; i < DIV_MAP.length; i++) if (DIV_MAP[i].key === key) return DIV_MAP[i];
    return null;
}

function rClass(rt)  { return rt === 'win' ? 'bw' : rt === 'loss' ? 'bl' : rt === 'upcoming' ? 'bu' : 'bn'; }
function rLabel(rt)  { return rt === 'win' ? 'ชนะ' : rt === 'loss' ? 'แพ้' : rt === 'upcoming' ? 'รอแข่ง' : 'NC'; }

/* ── Date formatter (Thai Buddhist Era) ─────────────────────────────────── */
function fDate(d) {
    if (!d) return '--';
    var m = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.',
             'ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'];
    var p = d.split('-');
    return parseInt(p[2]) + ' ' + m[parseInt(p[1]) - 1] + ' ' + (parseInt(p[0]) + 543);
}

/* ── SEO / Meta ──────────────────────────────────────────────────────────── */
function setMeta(opts) {
    var title   = (opts.title   || BRAND) + ' | ' + BRAND;
    var titleEn = (opts.titleEn || BRAND) + ' | ' + BRAND;
    var desc    = opts.desc    || 'สถิตินักมวย ONE Championship ครบทุกรุ่น | ' + BRAND;
    var descEn  = opts.descEn  || 'ONE Championship Muay Thai & MMA Fighter Stats | ' + BRAND;
    var url     = opts.url     || SITE;
    var image   = opts.image   || SITE + '/og-default.jpg';
    var type    = opts.type    || 'website';
    var kw      = opts.keywords || 'นักมวย,ONE Championship,Muay Thai,สถิติ,' + BRAND;

    document.title = title;

    function setTag(sel, attr, val) {
        var el = document.querySelector(sel);
        if (!el) {
            el = document.createElement(sel.startsWith('link') ? 'link' : 'meta');
            var clean = sel.replace(/[\[\]]/g, '').split('=');
            if (clean.length >= 2) {
                var k = clean[0], v = clean[1].replace(/"/g, '');
                el.setAttribute(k, v);
            }
            document.head.appendChild(el);
        }
        el.setAttribute(attr, val);
    }

    setTag('meta[name="description"]',       'content', desc);
    setTag('meta[name="keywords"]',           'content', kw);
    setTag('meta[name="robots"]',             'content', 'index,follow');
    setTag('meta[name="author"]',             'content', BRAND);
    setTag('link[rel="canonical"]',           'href',    url);
    setTag('meta[property="og:title"]',       'content', title);
    setTag('meta[property="og:description"]', 'content', desc);
    setTag('meta[property="og:image"]',       'content', image);
    setTag('meta[property="og:url"]',         'content', url);
    setTag('meta[property="og:type"]',        'content', type);
    setTag('meta[property="og:site_name"]',   'content', BRAND);
    setTag('meta[property="og:locale"]',      'content', 'th_TH');
    setTag('meta[name="twitter:card"]',       'content', 'summary_large_image');
    setTag('meta[name="twitter:title"]',      'content', titleEn);
    setTag('meta[name="twitter:description"]','content', descEn);
    setTag('meta[name="twitter:image"]',      'content', image);

    if (opts.jsonld) {
        var ex = document.getElementById('jsonld-main');
        if (ex) ex.remove();
        var sc = document.createElement('script');
        sc.id   = 'jsonld-main';
        sc.type = 'application/ld+json';
        sc.text = JSON.stringify(opts.jsonld);
        document.head.appendChild(sc);
    }
}

/* ── Ad Slots ────────────────────────────────────────────────────────────── */
var ADSENSE_ID = 'ca-pub-XXXXXXXXXXXXXXXXX';
var AD_SLOTS = {
    banner_top    : '',
    banner_mid    : '',
    banner_bottom : '',
    rectangle     : '',
    direct_top    : '',
    direct_mid    : '',
    direct_bottom : '',
};

function adSlot(type) {
    var directKey = 'direct_' + type.replace('banner_', '');
    if (AD_SLOTS[directKey]) {
        return '<div class="ad-direct">' + AD_SLOTS[directKey] + '</div>';
    }
    if (!AD_SLOTS[type] || !ADSENSE_ID || ADSENSE_ID === 'ca-pub-XXXXXXXXXXXXXXXXX') return '';
    return '<ins class="adsbygoogle" style="display:block;text-align:center"' +
        ' data-ad-client="' + ADSENSE_ID + '"' +
        ' data-ad-slot="'   + AD_SLOTS[type] + '"' +
        ' data-ad-format="auto"' +
        ' data-full-width-responsive="true"></ins>' +
        '<script>(adsbygoogle=window.adsbygoogle||[]).push({});<\/script>';
}

/* ══════════════════════════════════════════════════════════════
   NAV — Bold Editorial style
══════════════════════════════════════════════════════════════ */
function nav(active, basePath) {
    var base = basePath || '';
    var tabs = [
        { id: 'ranking',  label: 'อันดับ',        href: base + 'index.html',    icon: '🏆' },
        { id: 'rankings', label: 'ตารางคะแนน',    href: base + 'rankings.html', icon: '📊' },
        { id: 'weight',   label: 'แยกตามรุ่น',    href: base + 'weight-classes.html', icon: '⚖️' },
        { id: 'stats',    label: 'สถิติ',          href: base + 'stats.html',    icon: '📈' },
        { id: 'fighters', label: 'นักมวยทั้งหมด', href: base + 'Fighters.html', icon: '🥋' },
        { id: 'schedule', label: 'โปรแกรมชก',     href: base + 'schedule.html', icon: '📅' },
        { id: 'results',  label: 'ผลการแข่งขัน',  href: base + 'results.html',  icon: '🥊' },
        { id: 'compare',  label: 'เปรียบเทียบ',   href: base + 'compare.html',  icon: '⚖️' },
        { id: 'blog',     label: 'บทความ',         href: base + 'blog/',         icon: '📖' },
        { id: 'tierlist', label: 'Tier List',       href: base + 'tierlist.html', icon: '🏅' },
    ];
    var html = '<nav class="nav">';
    html += '<a class="nav-brand" href="' + base + 'index.html">';
    html += '<span class="nav-brand-r">Box</span><span class="nav-brand-b">fan</span></a>';
    html += '<div class="nav-tabs">';
    tabs.forEach(function(t) {
        var isActive = active === t.id;
        html += '<a class="nav-tab' + (isActive ? ' active' : '') + '" href="' + t.href + '">' + t.label + '</a>';
    });
    html += '</div>';
    html += '<div class="nav-search-wrap"><div class="nav-search">';
    html += '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>';
    html += '<input type="text" id="sinput" placeholder="ค้นหานักมวย…" autocomplete="off"></div><div class="sdrop" id="sdrop"></div></div></nav>';
    return html;
}

/* ══════════════════════════════════════════════════════════════
   FOOTER — Dark editorial bar
══════════════════════════════════════════════════════════════ */
function renderFooter(extraText) {
    var el = document.getElementById('ft');
    if (!el) return;
    var yr = new Date().getFullYear();
    var links = [
        { href: 'about.html', label: 'เกี่ยวกับเรา' }, { href: 'contact.html', label: 'ติดต่อเรา' },
        { href: 'privacy.html', label: 'นโยบายความเป็นส่วนตัว' }, { href: 'disclaimer.html', label: 'ข้อจำกัดความรับผิด' },
    ];
    var linksHtml = links.map(function(l) { return '<a href="' + l.href + '">' + l.label + '</a>'; }).join(' &nbsp;·&nbsp; ');
    var extra = extraText ? '<span style="opacity:.4"> &nbsp;·&nbsp; </span>' + extraText : '';

    el.innerHTML =
        '<div style="max-width:1200px;margin:0 auto;padding:0 20px">' +
            '<div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:12px">' +
                '<span style="font-size:18px;font-weight:900;color:#fff;letter-spacing:-1px;font-style:italic;"><span style="color:#ef4444">Box</span>fan</span>' +
                '<span style="color:rgba(255,255,255,.2);font-size:20px">|</span>' +
                '<span style="font-size:11px;color:rgba(255,255,255,.45);letter-spacing:.1em;text-transform:uppercase;font-weight:700">ONE Championship Fighter Stats</span>' +
            '</div>' +
            '<div style="margin-bottom:8px">' + linksHtml + '</div>' +
            '<div style="font-size:10px;color:rgba(255,255,255,.3);letter-spacing:.04em">© ' + yr + ' Boxfan — ข้อมูลรวบรวมโดยแฟนกีฬา ไม่ใช่เว็บทางการของ ONE Championship' + extra + '</div>' +
        '</div>';
}

/* ══════════════════════════════════════════════════════════════
   SEARCH DROPDOWN
══════════════════════════════════════════════════════════════ */
function initSearch() {
    var inp = document.getElementById('sinput'), drop = document.getElementById('sdrop');
    if (!inp || !drop) return;
    inp.addEventListener('input', function() {
        var q = inp.value.trim().toLowerCase();
        if (!q) { drop.classList.remove('open'); return; }
        var hits = FIGHTERS.filter(function(f) {
            return (f.name_th || '').toLowerCase().indexOf(q) !== -1 || (f.name_en || '').toLowerCase().indexOf(q) !== -1;
        }).slice(0, 8);
        if (hits.length) {
            drop.innerHTML = hits.map(function(f) {
                return '<a class="si" href="profile.html?id=' + f.id + '"><img src="' + cImg(f.image_filename, 'sm') + '" loading="lazy" onerror="this.src=PH" alt=""><div><div class="si-nm">' + f.name_th + '</div><div class="si-mt">' + fl(f.country) + ' ' + ds(f.division) + ' &nbsp;·&nbsp; ' + f.total_wins + 'W ' + f.total_losses + 'L</div></div></a>';
            }).join('');
        } else {
            drop.innerHTML = '<div class="s-empty">ไม่พบ "' + inp.value + '"</div>';
        }
        drop.classList.add('open');
    });
    document.addEventListener('click', function(e) { if (!e.target.closest('.nav-search-wrap')) drop.classList.remove('open'); });
}

/* ── URL SEO Helper ─────────────────────────────────────────── */
function getFighterUrl(f) {
    if (!f) return '#';
    var name = f.name_en || f.name_th || String(f.id);
    var s = name.trim();
    /* English: lowercase */
    if (/^[\x00-\x7F\s-]*$/.test(s)) s = s.toLowerCase();
    s = s.replace(/\s+/g, '-').replace(/[/\\:*?"<>|]/g, '').replace(/-+/g, '-').replace(/^-|-$/g, '');
    return 'fighters/' + encodeURIComponent(s) + '.html';
}