const CACHE_NAME = 'medassist-cache-v2';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/medical-logo.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pre-caching offline asset bundle');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[Service Worker] Deleting legacy cache', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Cache first with network fallback for assets; authentication and API calls stay network-only.
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);

  // Handle API and Firebase Auth network requests
  if (
    requestUrl.pathname.startsWith('/ask') || 
    requestUrl.pathname.startsWith('/history') || 
    event.request.url.includes('firebase')
  ) {
    if (requestUrl.pathname.includes('/ask')) {
      event.respondWith(
        fetch(event.request).catch(() => {
          // Return offline assistant response
          return new Response(
            JSON.stringify({
              response: "⚠️ You are currently offline. Clinical retrieval (RAG) is paused, but your active medication alarms and reminders continue running in the background! Please reconnect to resume consultation.",
              role: "assistant"
            }),
            { headers: { 'Content-Type': 'application/json' } }
          );
        })
      );
    }
    return;
  }

  // Cache-first strategy for static resources
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return fetch(event.request).then((networkResponse) => {
        if (
          networkResponse.status === 200 &&
          (requestUrl.origin === location.origin || 
           requestUrl.pathname.includes('googleapis') || 
           requestUrl.pathname.includes('gstatic'))
        ) {
          const cacheCopy = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, cacheCopy);
          });
        }
        return networkResponse;
      }).catch((err) => {
        // SPA navigation fallback to index.html
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html') || caches.match('/');
        }
        return new Response('Network Connection Offline', { status: 503, statusText: 'Service Unavailable' });
      });
    })
  );
});
