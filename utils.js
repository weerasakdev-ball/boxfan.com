/* ═══════════════════════════════════════════════════════════════
   BOXFAN — utils.js
   Helper functions: nav, footer, SEO, image, scoring, data
   ═══════════════════════════════════════════════════════════════ */

/* ── Constants ───────────────────────────────────────────────────────────── */
var BRAND = 'Boxfan';
var SITE  = 'https://boxingfandom.com';
var CLOUD = 'dpvyl7nan'; /* ← Cloudinary cloud name */
var PH    = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'%3E%3Crect width='80' height='80' fill='%23f1f3f4'/%3E%3Ctext x='50%25' y='55%25' text-anchor='middle' dominant-baseline='middle' font-size='36'%3E%F0%9F%A5%8A%3C/text%3E%3C/svg%3E";

/* ── Security: HTML escape (กัน XSS เมื่อ build HTML ด้วยการต่อสตริง) ──────── */
/* ใช้หุ้มค่าข้อความอิสระทุกตัวก่อนยัดเข้า innerHTML เช่น esc(f.name_th) */
function esc(s) {
    if (s == null) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

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

/* ── Division shortname ─────────────────────────────────────────────────── */
function ds(d) {
    if (!d) return '';
    if (d.indexOf('อะตอมเวต')  !== -1) return 'Atomweight';
    if (d.indexOf('สตรอว์เวต') !== -1) return 'Strawweight';
    if (d.indexOf('ฟลายเวต')   !== -1) return 'Flyweight';
    if (d.indexOf('แบนตัมเวต') !== -1) return 'Bantamweight';
    if (d.indexOf('เฟเธอร์เวต')!== -1) return 'Featherweight';
    if (d.indexOf('ไลต์เวต')   !== -1) return 'Lightweight';
    return d;
}

/* ── Score / History ─────────────────────────────────────────────────────── */
function score(h) {
    var s = 0;
    (h || []).forEach(function(x) {
        if (x.result_type === 'win') {
            s += 3;
            if (x.round === 1 && x.decision && /ko|tko/i.test(x.decision)) s += 1;
        } else if (x.result_type === 'loss') {
            s -= 1;
        }
    });
    return s;
}

function hist(fid) { return HISTORY.filter(function(h) { return h.fighter_id === fid; }); }

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
   ทุกหน้าเรียก: document.getElementById('nw').innerHTML = nav('ranking');
══════════════════════════════════════════════════════════════ */
function nav(active, basePath) {
    var base = basePath || '';

    var tabs = [
        { id: 'ranking',  label: 'อันดับ',        href: base + 'index.html',    icon: '🏆' },
        { id: 'rankings', label: 'ตารางคะแนน',    href: base + 'rankings.html', icon: '📊' },
        { id: 'schedule', label: 'โปรแกรมชก',     href: base + 'schedule.html', icon: '📅' },
        { id: 'results',  label: 'ผลการแข่งขัน',  href: base + 'results.html',  icon: '🥊' },
        { id: 'compare',  label: 'เปรียบเทียบ',   href: base + 'compare.html',  icon: '⚖️' },
        { id: 'blog',     label: 'บทความ',         href: base + 'blog/',         icon: '📖' },
        { id: 'tierlist', label: 'Tier List',       href: base + 'tierlist.html', icon: '🏅' },
    ];

    var html = '<nav class="nav">';

    /* ── Brand ── */
    html += '<a class="nav-brand" href="' + base + 'index.html">';
    html += '<span class="nav-brand-r">Box</span>';
    html += '<span class="nav-brand-b">fan</span>';
    html += '</a>';

    /* ── Tabs ── */
    html += '<div class="nav-tabs">';
    tabs.forEach(function(t) {
        var isActive = active === t.id;
        html += '<a class="nav-tab' + (isActive ? ' active' : '') + '" href="' + t.href + '">';
        html += t.label;
        html += '</a>';
    });
    html += '</div>';

    /* ── Search ── */
    html += '<div class="nav-search-wrap">';
    html += '<div class="nav-search">';
    html += '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">';
    html += '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>';
    html += '</svg>';
    html += '<input type="text" id="sinput" placeholder="ค้นหานักมวย…" autocomplete="off">';
    html += '</div>';
    html += '<div class="sdrop" id="sdrop"></div>';
    html += '</div>';

    html += '</nav>';
    return html;
}

/* ══════════════════════════════════════════════════════════════
   FOOTER — Dark editorial bar
   เรียก: renderFooter('text เพิ่มเติม');
══════════════════════════════════════════════════════════════ */
function renderFooter(extraText) {
    var el = document.getElementById('ft');
    if (!el) return;

    var yr = new Date().getFullYear();
    var links = [
        { href: 'about.html',      label: 'เกี่ยวกับเรา' },
        { href: 'contact.html',    label: 'ติดต่อเรา' },
        { href: 'privacy.html',    label: 'นโยบายความเป็นส่วนตัว' },
        { href: 'disclaimer.html', label: 'ข้อจำกัดความรับผิด' },
    ];

    var linksHtml = links.map(function(l) {
        return '<a href="' + l.href + '">' + l.label + '</a>';
    }).join(' &nbsp;·&nbsp; ');

    var extra = extraText ? '<span style="opacity:.4"> &nbsp;·&nbsp; </span>' + extraText : '';

    el.innerHTML =
        '<div style="max-width:1200px;margin:0 auto;padding:0 20px">' +
            /* Brand line */
            '<div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:12px">' +
                '<span style="font-size:18px;font-weight:900;color:#fff;letter-spacing:-1px;font-style:italic;">' +
                    '<span style="color:#ef4444">Box</span>fan' +
                '</span>' +
                '<span style="color:rgba(255,255,255,.2);font-size:20px">|</span>' +
                '<span style="font-size:11px;color:rgba(255,255,255,.45);letter-spacing:.1em;text-transform:uppercase;font-weight:700">' +
                    'ONE Championship Fighter Stats' +
                '</span>' +
            '</div>' +
            /* Links */
            '<div style="margin-bottom:8px">' + linksHtml + '</div>' +
            /* Copyright */
            '<div style="font-size:10px;color:rgba(255,255,255,.3);letter-spacing:.04em">' +
                '© ' + yr + ' Boxfan — ข้อมูลรวบรวมโดยแฟนกีฬา ไม่ใช่เว็บทางการของ ONE Championship' +
                extra +
            '</div>' +
        '</div>';
}

/* ══════════════════════════════════════════════════════════════
   SEARCH DROPDOWN — ใช้งาน initSearch() หลัง nav() render แล้ว
══════════════════════════════════════════════════════════════ */
function initSearch() {
    var inp  = document.getElementById('sinput');
    var drop = document.getElementById('sdrop');
    if (!inp || !drop) return;

    inp.addEventListener('input', function() {
        var q = inp.value.trim().toLowerCase();
        if (!q) { drop.classList.remove('open'); return; }

        var hits = FIGHTERS.filter(function(f) {
            return (f.name_th || '').toLowerCase().indexOf(q) !== -1 ||
                   (f.name_en || '').toLowerCase().indexOf(q) !== -1;
        }).slice(0, 8);

        if (hits.length) {
            drop.innerHTML = hits.map(function(f) {
                return '<a class="si" href="profile.html?id=' + f.id + '">' +
                    '<img src="' + cImg(f.image_filename, 'sm') + '" loading="lazy" onerror="this.src=PH" alt="">' +
                    '<div>' +
                        '<div class="si-nm">' + esc(f.name_th) + '</div>' +
                        '<div class="si-mt">' + fl(f.country) + ' ' + ds(f.division) + ' &nbsp;·&nbsp; ' + f.total_wins + 'W ' + f.total_losses + 'L</div>' +
                    '</div>' +
                    '</a>';
            }).join('');
        } else {
            drop.innerHTML = '<div class="s-empty">ไม่พบ "' + esc(inp.value) + '"</div>';
        }
        drop.classList.add('open');
    });

    document.addEventListener('click', function(e) {
        if (!e.target.closest('.nav-search-wrap')) drop.classList.remove('open');
    });
}
/* ══════════════════════════════════════════════════════════════
   ACCESSIBILITY LAYER (กลาง — ทำงานทุกหน้าโดยไม่ต้องแก้ราย element)
   • ทำให้ทุก element ที่มี onclick ใช้คีย์บอร์ดได้ (Enter / Space)
   • ใส่ focus ring ที่มองเห็นชัด (focus-visible)
   • เพิ่ม "ข้ามไปเนื้อหา" (skip link) สำหรับ screen reader / keyboard
══════════════════════════════════════════════════════════════ */
(function () {
    /* 1) ฉีด CSS สำหรับ focus ring + skip link + sr-only */
    function injectA11yCSS() {
        if (document.getElementById('a11y-css')) return;
        var css =
            ':where(a,button,[role="button"],[role="tab"],input,select,textarea,[tabindex]):focus-visible{' +
                'outline:2px solid var(--gold,#f4b740);outline-offset:2px;border-radius:4px}' +
            '.skip-link{position:absolute;left:8px;top:-48px;z-index:9999;' +
                'background:var(--red,#e8412e);color:#fff;padding:9px 16px;border-radius:8px;' +
                'font-weight:700;font-size:14px;transition:top .15s;box-shadow:0 6px 20px -6px rgba(0,0,0,.5)}' +
            '.skip-link:focus{top:8px}' +
            '.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;' +
                'overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}';
        var st = document.createElement('style');
        st.id = 'a11y-css';
        st.textContent = css;
        (document.head || document.documentElement).appendChild(st);
    }
    injectA11yCSS();

    /* 2) ทำให้ element ที่มี onclick กดด้วยคีย์บอร์ดได้ */
    var NATIVE = /^(A|BUTTON|INPUT|SELECT|TEXTAREA|SUMMARY)$/;
    function upgrade(el) {
        if (!el || el.nodeType !== 1) return;
        if (!el.hasAttribute('onclick')) return;
        if (NATIVE.test(el.tagName)) return;
        if (el.getAttribute('data-a11y') === '1') return;
        el.setAttribute('data-a11y', '1');
        if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
        if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
    }
    function scan(root) {
        if (!root || root.nodeType !== 1) return;
        upgrade(root);
        if (root.querySelectorAll) {
            var list = root.querySelectorAll('[onclick]');
            for (var i = 0; i < list.length; i++) upgrade(list[i]);
        }
    }
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.key !== ' ' && e.key !== 'Spacebar') return;
        var t = e.target;
        if (t && t.getAttribute && t.getAttribute('data-a11y') === '1') {
            e.preventDefault();
            t.click();
        }
    });

    /* 3) Skip link → เนื้อหาหลัก */
    function addSkipLink() {
        if (document.getElementById('skip-link')) return;
        var main = document.querySelector('main, #root, [role="main"], .page-w, .wrap, .container');
        if (main && !main.id) main.id = 'main-content';
        var targetId = main ? main.id : '';
        if (main) main.setAttribute('tabindex', '-1');
        var a = document.createElement('a');
        a.id = 'skip-link';
        a.className = 'skip-link';
        a.href = '#' + (targetId || '');
        a.textContent = 'ข้ามไปยังเนื้อหาหลัก';
        if (document.body) document.body.insertBefore(a, document.body.firstChild);
    }

    /* 4) เริ่มทำงาน + เฝ้าดู DOM ที่ render เพิ่มทีหลัง (ปุ่ม/แถวที่สร้างด้วย JS) */
    function boot() {
        injectA11yCSS();
        scan(document.body);
        addSkipLink();
        if (window.MutationObserver) {
            var mo = new MutationObserver(function (muts) {
                for (var i = 0; i < muts.length; i++) {
                    var nodes = muts[i].addedNodes;
                    for (var j = 0; j < nodes.length; j++) scan(nodes[j]);
                }
            });
            mo.observe(document.body, { childList: true, subtree: true });
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
