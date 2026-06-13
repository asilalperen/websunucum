const CACHE_NAME = 'mementos-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  // HTML sayfaları ve navigate istekleri için (Network-First)
  if (event.request.mode === 'navigate' || (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html'))) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Ağı dene, başarılıysa cache'i de güncelle (isteğe bağlı, şimdilik sadece ağı döndür)
          return response;
        })
        .catch(() => {
          // İnternet yoksa cache'ten döndür
          return caches.match(event.request);
        })
    );
  } else {
    // Statik dosyalar (CSS, JS, Resimler) için (Cache-First)
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          return response || fetch(event.request);
        })
    );
  }
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
