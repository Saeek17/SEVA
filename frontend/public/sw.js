// Service worker for the farmer PWA: shows the daily advice pushed by the server
// and opens /kisan when the notification is tapped.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { body: event.data ? event.data.text() : "" };
  }
  event.waitUntil(
    self.registration.showNotification(data.title || "किसान साथी", {
      body: data.body || "",
      icon: "/kisan-icon.svg",
      badge: "/kisan-icon.svg",
      data: { url: data.url || "/kisan" },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/kisan";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
      for (const w of windows) {
        if (w.url.includes("/kisan") && "focus" in w) return w.focus();
      }
      return self.clients.openWindow(url);
    })
  );
});
