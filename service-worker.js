/* ═══════════════════════════════════════════════════════════════
   BOXFAN — Service Worker
   กลยุทธ์:
     - HTML       → network-first (ให้ user เห็นเวอร์ชันใหม่เสมอ)
     - CSS/JS/img → cache-first (เร็วสุด)
     - fighters_data.js / fighters_index.js → stale-while-revalidate
                    (แสดงเวอร์ชัน cache ทันที + อัปเดตพื้นหลัง)
   ═══════════════════════════════════════════════════════════════ */
const VERSION = 'boxfan-v1';
const STATIC_CACHE = VERSION + '-static';
const DATA_CACHE   = VERSION + '-data';

const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/utils.js',
    '/manifest.webmanifest',
    '/icons/icon-192.png'
];

/* ── Install: pre-cache หน้าหลัก ── */
self.addEventListener('install', function(evt) {
    self.skipWaiting();
    evt.waitUntil(
        caches.open(STATIC_CACHE).then(function(cache) {
            return cache.addAll(STATIC_ASSETS).catch(function() {
                /* ถ้า pre-cache ล้มเหลว ไม่ต้อง fail install */
            });
        })
    );
});

/* ── Activate: ลบ cache เก่า ── */
self.addEventListener('activate', function(evt) {
    evt.waitUntil(
        caches.keys().then(function(keys) {
            return Promise.all(keys.map(function(k) {
                if (k.indexOf(VERSION) !== 0) return caches.delete(k);
            }));
        }).then(function() { return self.clients.claim(); })
    );
});

/* ── Fetch: routing strategy ── */
self.addEventListener('fetch', function(evt) {
    const req = evt.request;
    if (req.method !== 'GET') return;

    const url = new URL(req.url);
    if (url.origin !== location.origin) return; /* ไม่แคชข้าม origin */

    /* HTML → network-first */
    if (req.mode === 'navigate' || req.destination === 'document') {
        evt.respondWith(networkFirst(req));
        return;
    }

    /* data files → stale-while-revalidate */
    if (/fighters_(data|index)\.js$/.test(url.pathname)) {
        evt.respondWith(staleWhileRevalidate(req, DATA_CACHE));
        return;
    }

    /* CSS/JS/รูป/font → cache-first */
    if (['script','style','image','font'].indexOf(req.destination) !== -1) {
        evt.respondWith(cacheFirst(req, STATIC_CACHE));
        return;
    }
});

function cacheFirst(req, cacheName) {
    return caches.match(req).then(function(cached) {
        if (cached) return cached;
        return fetch(req).then(function(res) {
            if (res && res.status === 200) {
                const clone = res.clone();
                caches.open(cacheName).then(function(c) { c.put(req, clone); });
            }
            return res;
        });
    });
}

function networkFirst(req) {
    return fetch(req).then(function(res) {
        if (res && res.status === 200) {
            const clone = res.clone();
            caches.open(STATIC_CACHE).then(function(c) { c.put(req, clone); });
        }
        return res;
    }).catch(function() {
        return caches.match(req).then(function(cached) {
            return cached || caches.match('/index.html');
        });
    });
}

function staleWhileRevalidate(req, cacheName) {
    return caches.open(cacheName).then(function(cache) {
        return cache.match(req).then(function(cached) {
            const fetchPromise = fetch(req).then(function(res) {
                if (res && res.status === 200) cache.put(req, res.clone());
                return res;
            }).catch(function() { return cached; });
            return cached || fetchPromise;
        });
    });
}
