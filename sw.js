const CACHE_NAME = "digimon-vpet-v20";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  const isHtml =
    e.request.mode === "navigate" ||
    url.pathname.endsWith(".html") ||
    url.pathname === "/";

  // HTML 走 network-first：每次都拿最新代碼，拿不到才回退緩存
  if(isHtml){
    e.respondWith(
      fetch(e.request).then((res) => {
        if(res && res.ok){
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, clone));
        }
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // 其它資源（圖片/音效）維持 cache-first
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const fetched = fetch(e.request).then((res) => {
        if(res && res.ok){
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, clone));
        }
        return res;
      }).catch(() => cached);
      return cached || fetched;
    })
  );
});
