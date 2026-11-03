/* ═══════════════════════════════════════════════════════════════
   BOXFAN — site.js  (การทำงานของเมนูบนแบบใหม่ ทุกหน้า)
   ─ HTML ของเมนู/ท้ายเว็บ ใส่ไว้ในไฟล์ .html แล้ว (build_chrome.py) ไฟล์นี้แค่ทำให้กดได้
   ─ ใช้ธีมสว่างเสมอ (หน้าเก่ามีโหมดมืดคนละแบบ จึงปิดไว้ก่อนเพื่อให้ทุกหน้าเหมือนกัน)
   ═══════════════════════════════════════════════════════════════ */
(function () {
    var root = document.documentElement;
    root.classList.add('bf');

    /* ── ธีมสว่างเสมอ ── */
    function forceLight() {
        if (root.getAttribute('data-theme') !== 'light') root.setAttribute('data-theme', 'light');
    }
    forceLight();
    try { localStorage.setItem('boxfan-theme', 'light'); } catch (e) {}
    try {
        new MutationObserver(forceLight).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    } catch (e) {}

    /* ลิงก์หน้าศึก — ต้องตรงกับ event_slug() ใน data/generate_profiles.py (build_events.py สร้างหน้า) */
    window.bfEventHref = function (name, date) {
        var s = String(name || '').trim().replace(/[<>:"\/\\|?*#%&\x00-\x1f]/g, '');
        s = s.replace(/\s+/g, '-').replace(/^[-.]+|[-.]+$/g, '') || 'event';
        /* Array.from นับอีโมจิเป็น 1 ตัวเหมือน Python (s[:80]) */
        return '/events/' + encodeURIComponent(Array.from(s).slice(0, 80).join('') + '-' + String(date || '').slice(0, 10)) + '.html';
    };

    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    ready(function () {
        var hdr = document.getElementById('bf-hdr');
        if (!hdr) return;

        /* ── ไฮไลต์เมนูของหน้าปัจจุบัน ── */
        var path = location.pathname.replace(/index\.html$/, '');
        if (path === '') path = '/';
        var group = /^\/fighters\//.test(path) || /^\/profile\.html/.test(path) ? 'fighters'
                  : /^\/rankings-/.test(path) ? 'rank'
                  : /^\/blog\//.test(path) ? 'blog' : '';
        document.querySelectorAll('.bf-hdr a[href], .bf-drawer a[href]').forEach(function (a) {
            var h = a.getAttribute('href');
            if (h === path || (h !== '/' && h.replace(/index\.html$/, '') === path)) a.setAttribute('aria-current', 'page');
        });
        document.querySelectorAll('.bf-dd').forEach(function (dd) {
            if (dd.querySelector('[aria-current="page"]') || dd.getAttribute('data-g') === group) dd.classList.add('cur');
        });
        if (group === 'blog') {
            var b = hdr.querySelector('.bf-nav > a[href="/blog/"]');
            if (b) b.setAttribute('aria-current', 'page');
        }

        /* ── เมนูย่อย (กดเปิด/ปิด) ── */
        function closeAll(except) {
            document.querySelectorAll('.bf-dd.open').forEach(function (d) {
                if (d !== except) { d.classList.remove('open'); d.querySelector('.bf-dd-btn').setAttribute('aria-expanded', 'false'); }
            });
        }
        document.querySelectorAll('.bf-dd-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                var dd = btn.parentNode, open = !dd.classList.contains('open');
                closeAll(dd);
                dd.classList.toggle('open', open);
                btn.setAttribute('aria-expanded', open ? 'true' : 'false');
            });
        });
        document.addEventListener('click', function (e) {
            if (!e.target.closest('.bf-dd')) closeAll();
            if (!e.target.closest('.bf-search')) hideDrop();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') { closeAll(); hideDrop(); closeDrawer(); }
        });

        /* ── เมนูมือถือ ── */
        var drawer = document.getElementById('bf-drawer');
        function openDrawer() { if (drawer) { drawer.classList.add('open'); root.classList.add('bf-lock'); } }
        function closeDrawer() { if (drawer) { drawer.classList.remove('open'); root.classList.remove('bf-lock'); } }
        var mb = document.getElementById('bf-menu-btn');
        if (mb) mb.addEventListener('click', openDrawer);
        document.querySelectorAll('[data-bf-close]').forEach(function (el) { el.addEventListener('click', closeDrawer); });

        /* ── ค้นหานักมวย ──
           หน้าที่โหลดข้อมูลนักมวยไว้แล้ว → แสดงรายชื่อทันที
           หน้าอื่น (เช่น หน้านักมวย) → กด Enter ไปหน้ารายชื่อพร้อมคำค้น */
        var form = hdr.querySelector('.bf-search');
        var input = form && form.querySelector('input');
        var drop = form && form.querySelector('.bf-sdrop');
        var openBtn = form && form.querySelector('.bf-search-open');
        function hideDrop() { if (drop) drop.classList.remove('show'); }
        if (openBtn) openBtn.addEventListener('click', function (e) {
            e.preventDefault();
            form.classList.add('open');
            input.focus();
        });
        if (input) input.addEventListener('blur', function () {
            setTimeout(function () { if (!input.value) form.classList.remove('open'); }, 200);
        });

        function esc(s) {
            return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
                return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
            });
        }
        function list() {
            try { return (typeof FIGHTERS !== 'undefined' && FIGHTERS && FIGHTERS.length) ? FIGHTERS : null; }
            catch (e) { return null; }
        }
        function url(f) {
            if (typeof fighterUrl === 'function') return '/' + fighterUrl(f, '');
            return f.slug ? '/fighters/' + encodeURIComponent(f.slug) + '.html'
                          : '/profile.html?id=' + encodeURIComponent(f.id);
        }
        function img(f) {
            try { if (typeof cImg === 'function') return cImg(f.image_filename, 'sm'); } catch (e) {}
            return '/images/noname1.png';
        }
        var sel = -1;
        if (input) input.addEventListener('input', function () {
            var q = input.value.trim().toLowerCase(), F = list();
            sel = -1;
            if (!q || !F || !drop) { hideDrop(); return; }
            var hits = [];
            for (var i = 0; i < F.length && hits.length < 40; i++) {
                var f = F[i];
                var s = ((f.name_th || '') + ' ' + (f.name_en || '') + ' ' + (f.nickname || '') + ' ' + (f.team || '')).toLowerCase();
                if (s.indexOf(q) >= 0) hits.push(f);
            }
            /* นักมวยที่มีไฟต์มากขึ้นก่อน */
            hits.sort(function (a, b) { return (b.fight_count || 0) - (a.fight_count || 0); });
            hits = hits.slice(0, 8);
            var html = hits.map(function (f) {
                var r = f.record || {};
                var meta = [f.division, f.country, (r.total ? (r.win || 0) + '-' + (r.loss || 0) + '-' + (r.draw || 0) : '')]
                    .filter(Boolean).join(' · ');
                return '<a href="' + url(f) + '"><img src="' + esc(img(f)) + '" alt="" loading="lazy" onerror="this.src=\'/images/noname1.png\'">' +
                       '<div><div class="n">' + esc(f.name_th || f.name_en) + '</div><div class="m">' + esc(meta) + '</div></div></a>';
            }).join('');
            html += '<a class="all" href="/fighters.html?q=' + encodeURIComponent(input.value.trim()) + '">ดูผลค้นหาทั้งหมด</a>';
            drop.innerHTML = html;
            drop.classList.add('show');
        });
        if (input) input.addEventListener('keydown', function (e) {
            if (!drop || !drop.classList.contains('show')) return;
            var items = drop.querySelectorAll('a');
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
                items.forEach(function (a, i) { a.classList.toggle('sel', i === sel); });
            } else if (e.key === 'Enter' && sel >= 0) {
                e.preventDefault();
                location.href = items[sel].getAttribute('href');
            }
        });
    });
})();
