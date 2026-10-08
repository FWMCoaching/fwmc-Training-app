// Network-first for the app itself so every visit gets the latest version;
// the cache is only a fallback for offline use. Requests to other origins
// (e.g. the programme-code API) are never cached, so a revoked code stops
// working immediately.
const CACHE = "fwmc-visual-training-v7";
const ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.json",
  "./logo-full.png",
  "./logo-white.png",
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
  // Network-first, but offline (Fabian, 2026-10-05: "läuft auch im Studio
  // ohne Netz"): with no or a very slow connection the cached copy answers
  // after at most 3 s, and the network answer still refreshes the cache in
  // the background for the next start. "no-store" so a browser HTTP cache
  // never quietly answers this fetch with a stale response right after a
  // deploy - it must be an actual round trip.
  const net = fetch(req, { cache: "no-store" }).then((res) => {
    if (res.ok) {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
    }
    return res;
  });
  event.respondWith(
    new Promise((resolve) => {
      let settled = false;
      const fromCache = () => caches.match(req, { ignoreSearch: true });
      const timer = setTimeout(() => {
        fromCache().then((hit) => { if (hit && !settled) { settled = true; resolve(hit); } });
      }, 3000);
      net.then((res) => {
        if (settled) return;
        if (res.ok) { settled = true; clearTimeout(timer); resolve(res); return; }
        // A server error: the cached copy is better than a broken page.
        fromCache().then((hit) => { if (!settled) { settled = true; clearTimeout(timer); resolve(hit || res); } });
      }).catch(() => {
        fromCache().then((hit) => { if (!settled) { settled = true; clearTimeout(timer); resolve(hit || Response.error()); } });
      });
    })
  );
  event.waitUntil(net.catch(() => {}));
});

// Erinnerungen (2026-10-05): the Worker's cron sends a Web Push with
// {title, body} shortly before a planned training. Tapping it focuses an
// open app window, or opens the app on "Heute".
self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = { body: event.data ? event.data.text() : "" }; }
  const title = data.title || "FWMC Online-Training";
  // Atempausen-Erinnerung (2026-10-07): the Worker only stores {title, body},
  // so the fixed title picks the target - the Nichtraucher-Pause on Heute.
  const isBreak = title === "Zeit für eine Atempause";
  event.waitUntil(self.registration.showNotification(title, {
    body: data.body || "",
    icon: "./icon-192.png",
    badge: "./icon-192.png",
    tag: data.tag || undefined,
    data: { url: isBreak ? "./index.html?bereich=atempause" : "./index.html?bereich=heute", open: isBreak ? "atempause" : "" },
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const nd = event.notification.data || {};
  const target = new URL(nd.url || "./index.html?bereich=heute", self.registration.scope).href;
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const c of list) {
        if (c.url.startsWith(self.registration.scope) && "focus" in c) {
          if (nd.open) { try { c.postMessage({ fwmcOpen: nd.open }); } catch (e) {} }
          return c.focus();
        }
      }
      return self.clients.openWindow ? self.clients.openWindow(target) : undefined;
    })
  );
});
