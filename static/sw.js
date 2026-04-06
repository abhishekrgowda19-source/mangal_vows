const CACHE_NAME = "mangal-vows-v2";

const STATIC_ASSETS = [
  "/",
  "/login",
  "/static/style.css",
  "/static/icon-192.png",
  "/static/icon-512.png",
  "/static/manifest.json",
  "/offline"
];

// ── INSTALL ──
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// ── ACTIVATE (clear old caches) ──
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ── FETCH ──
self.addEventListener("fetch", event => {
  // Skip non-GET and chrome-extension requests
  if (event.request.method !== "GET") return;
  if (event.request.url.startsWith("chrome-extension")) return;

  // API calls — network first, no cache
  if (event.request.url.includes("/api/")) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({ error: "You are offline" }), {
          headers: { "Content-Type": "application/json" }
        })
      )
    );
    return;
  }

  // Everything else — cache first, fallback to network
  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request)
        .then(response => {
          // Cache new pages dynamically
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, response.clone());
            return response;
          });
        })
        .catch(() => caches.match("/offline"));
    })
  );
});