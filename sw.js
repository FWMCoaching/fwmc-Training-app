// Network-first for the app itself so every visit gets the latest version;
// the cache is only a fallback for offline use. Requests to other origins
// (e.g. the programme-code API) are never cached, so a revoked code stops
// working immediately.
const CACHE = "fwmc-visual-training-v5";
const ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.json",
  "./logo-full.png",
  "./icon-192.png",
  "./icon-512.png",
  "./fonts/magra-400.woff2",
  "./fonts/magra-700.woff2",
  "./fonts/public-sans.woff2",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  if (new URL(req.url).origin !== self.location.origin) return;
  // Images and fonts rarely change: answer from the cache at once and refresh
  // it in the background. Network-first for them left the logo as an empty
  // white box on a slow iPad connection (Fabian, 2026-10-04).
  if (/\.(png|jpe?g|svg|webp|woff2)$/i.test(new URL(req.url).pathname)) {
    event.respondWith(
      caches.match(req, { ignoreSearch: true }).then((hit) => {
        const net = fetch(req).then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
          return res;
        });
        if (hit) { net.catch(() => {}); return hit; }
        return net;
      })
    );
    return;
  }
  event.respondWith(
    // "no-store" so a browser HTTP cache never quietly answers this network-
    // first fetch with a stale response right after a deploy - it must be an
    // actual round trip, or the whole point of "network-first" is defeated.
    fetch(req, { cache: "no-store" })
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        }
        // A server error: the cached copy is better than a broken page.
        return caches.match(req, { ignoreSearch: true }).then((hit) => hit || res);
      })
      .catch(() => caches.match(req, { ignoreSearch: true }))
  );
});
