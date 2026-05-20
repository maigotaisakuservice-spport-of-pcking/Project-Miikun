const CACHE_NAME = 'miikun-v2'; // Increment to force cache refresh
const ASSETS = [
  '/',
  '/index.html',
  '/css/style.css',
  '/js/main.js',
  '/js/state.js',
  '/js/api.js',
  '/js/audio_io.js',
  '/js/vrm_loader.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

self.addEventListener('fetch', (event) => {
  // Never cache API requests
  if (event.request.url.includes('/api/')) {
    return event.respondWith(fetch(event.request));
  }

  // Network-First strategy for critical JS/CSS assets
  // This ensures updates to api.js are picked up immediately
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        // If network succeeds, update cache
        return caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, networkResponse.clone());
          return networkResponse;
        });
      })
      .catch(() => {
        // If network fails, serve from cache
        return caches.match(event.request);
      })
  );
});

// Activate event: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
