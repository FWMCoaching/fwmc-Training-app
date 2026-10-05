// Plain-node check of the Erinnerungen endpoints and the cron sender (no
// wrangler needed): a mock D1, a fake push service that DECRYPTS what the
// Worker sends (RFC 8291, as a browser would) and verifies the VAPID JWT.
//   node test/reminders.mjs   -> every line must end in "True"
import worker from "../src/index.js";
import { encryptPayload, b64urlEncode, b64urlDecode, sendDueReminders, LIMITS } from "../src/reminders.js";

const { subtle } = globalThis.crypto;
const enc = new TextEncoder(), dec = new TextDecoder();
const out = (label, v) => console.log(label + ":", v ? "True" : "False");

// ---- mock D1 (only the statements reminders.js uses) ----
const subs = new Map(); // id -> row
let rems = []; let nextId = 1;
function stmt(sql) {
  const s = {
    args: [],
    bind(...a) { s.args = a; return s; },
    async first() {
      if (sql.startsWith("SELECT id FROM push_subs")) return subs.has(s.args[0]) ? { id: s.args[0] } : null;
      if (sql.startsWith("SELECT COUNT(*) AS n FROM push_subs")) return { n: subs.size };
      return null;
    },
    async all() {
      if (sql.includes("FROM push_reminders r JOIN push_subs")) {
        const [until, limit] = s.args;
        const res = rems.filter((r) => r.at <= until && subs.has(r.sub_id)).sort((a, b) => a.at.localeCompare(b.at)).slice(0, limit)
          .map((r) => ({ ...r, ...(({ endpoint, p256dh, auth }) => ({ endpoint, p256dh, auth }))(subs.get(r.sub_id)) }));
        return { results: res };
      }
      return { results: [] };
    },
    async run() {
      const a = s.args;
      if (sql.startsWith("CREATE")) return {};
      if (sql.startsWith("INSERT INTO push_subs")) subs.set(a[0], { id: a[0], endpoint: a[1], p256dh: a[2], auth: a[3], created_at: a[4], updated_at: a[5] });
      else if (sql.startsWith("UPDATE push_subs")) Object.assign(subs.get(a[4]), { endpoint: a[0], p256dh: a[1], auth: a[2], updated_at: a[3] });
      else if (sql.startsWith("DELETE FROM push_reminders WHERE sub_id")) rems = rems.filter((r) => r.sub_id !== a[0]);
      else if (sql.startsWith("DELETE FROM push_reminders WHERE id")) rems = rems.filter((r) => r.id !== a[0]);
      else if (sql.startsWith("DELETE FROM push_subs WHERE id")) subs.delete(a[0]);
      else if (sql.startsWith("DELETE FROM push_subs WHERE updated_at")) { for (const [id, r] of [...subs]) if (r.updated_at < a[0] && !rems.some((x) => x.sub_id === id)) subs.delete(id); }
      else if (sql.startsWith("INSERT INTO push_reminders")) rems.push({ id: nextId++, sub_id: a[0], at: a[1], title: a[2], body: a[3] });
      else throw new Error("unexpected SQL: " + sql);
      return {};
    },
  };
  return s;
}
const DB = { prepare: stmt, async batch(list) { for (const s of list) await s.run(); return []; } };

// ---- a "browser": its push key pair and auth secret ----
const ua = await subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
const uaPublic = new Uint8Array(await subtle.exportKey("raw", ua.publicKey));
const authSecret = crypto.getRandomValues(new Uint8Array(16));
const subscription = { endpoint: "https://fcm.googleapis.com/fcm/send/abc123", keys: { p256dh: b64urlEncode(uaPublic), auth: b64urlEncode(authSecret) } };

// ---- VAPID keys like gen-vapid.mjs makes them ----
const vk = await subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
const vapidPub = b64urlEncode(new Uint8Array(await subtle.exportKey("raw", vk.publicKey)));
const vapidD = (await subtle.exportKey("jwk", vk.privateKey)).d;

let limitCalls = 0;
const env = { DB, VAPID_PUBLIC_KEY: vapidPub, VAPID_PRIVATE_KEY: vapidD, REMINDER_LIMITER: { async limit() { limitCalls++; return { success: limitCalls <= 50 }; } } };
const call = (method, body) => worker.fetch(new Request("https://w.example/reminders", { method, headers: { "Content-Type": "application/json", Origin: "https://fwmcoaching.github.io" }, body: body == null ? undefined : JSON.stringify(body) }), env);

// RFC 8291 decryption as the browser does it.
async function hkdf(salt, ikm, info, n) {
  const k = await subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, k, n * 8));
}
async function decrypt(body) {
  const u8 = new Uint8Array(body);
  const salt = u8.slice(0, 16), rs = new DataView(u8.buffer).getUint32(16), idlen = u8[20];
  const asPublic = u8.slice(21, 21 + idlen), ct = u8.slice(21 + idlen);
  const asKey = await subtle.importKey("raw", asPublic, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const ecdh = new Uint8Array(await subtle.deriveBits({ name: "ECDH", public: asKey }, ua.privateKey, 256));
  const info = new Uint8Array([...enc.encode("WebPush: info\0"), ...uaPublic, ...asPublic]);
  const ikm = await hkdf(authSecret, ecdh, info, 32);
  const cek = await hkdf(salt, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, enc.encode("Content-Encoding: nonce\0"), 12);
  const key = await subtle.importKey("raw", cek, "AES-GCM", false, ["decrypt"]);
  const pt = new Uint8Array(await subtle.decrypt({ name: "AES-GCM", iv: nonce }, key, ct));
  if (rs !== 4096 || pt[pt.length - 1] !== 2) throw new Error("bad record");
  return dec.decode(pt.slice(0, -1));
}
async function verifyJwt(auth) {
  const m = /^vapid t=([^,]+), k=(.+)$/.exec(auth || "");
  if (!m) return null;
  const [h, c, sig] = m[1].split(".");
  const pub = await subtle.importKey("raw", b64urlDecode(m[2]), { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
  const ok = await subtle.verify({ name: "ECDSA", hash: "SHA-256" }, pub, b64urlDecode(sig), enc.encode(h + "." + c));
  return ok ? { claims: JSON.parse(dec.decode(b64urlDecode(c))), k: m[2] } : null;
}

// ---- fake push service ----
const pushed = []; let pushStatus = 201;
globalThis.fetch = async (url, init) => { pushed.push({ url, init }); return new Response(null, { status: pushStatus }); };

const now = Date.now();
const iso = (ms) => new Date(now + ms).toISOString();

// Validation
let r = await call("POST", { subscription, reminders: [{ at: iso(3600e3), title: "Training um 18:00 Uhr", body: "In 10 Minuten: Cardio · 20 Min." }] });
out("POST stores a subscription + reminder", r.status === 200 && subs.size === 1 && rems.length === 1);
out("CORS open like the lookup", r.headers.get("Access-Control-Allow-Origin") === "*");
r = await worker.fetch(new Request("https://w.example/reminders", { method: "OPTIONS" }), env);
out("preflight allows DELETE", r.status === 204 && /DELETE/.test(r.headers.get("Access-Control-Allow-Methods")));
r = await call("POST", { subscription, reminders: [{ at: iso(7200e3), title: "A", body: "x" }, { at: iso(10800e3), title: "B", body: "y" }] });
out("POST replaces the pending reminders", r.status === 200 && rems.length === 2 && rems.every((x) => x.title !== "Training um 18:00 Uhr"));
r = await call("POST", { subscription: { ...subscription, endpoint: "https://evil.example/push" }, reminders: [] });
out("foreign push host refused", r.status === 400);
r = await call("POST", { subscription: { ...subscription, keys: { p256dh: "abc", auth: subscription.keys.auth } }, reminders: [] });
out("bad key refused", r.status === 400);
r = await call("POST", { subscription, reminders: Array.from({ length: LIMITS.maxReminders + 1 }, (_, i) => ({ at: iso(3600e3 + i * 60e3), title: "T", body: "B" })) });
out("more than 60 reminders refused", r.status === 400);
r = await call("POST", { subscription, reminders: [{ at: iso(16 * 86400e3), title: "T", body: "B" }] });
out("reminder beyond 15 days refused", r.status === 400);
r = await call("POST", { subscription, reminders: [{ at: iso(-3600e3), title: "T", body: "B" }] });
out("reminder in the past refused", r.status === 400);
r = await call("POST", { subscription, reminders: [{ at: "morgen", title: "T", body: "B" }] });
out("invalid time refused", r.status === 400);
r = await call("POST", { subscription, reminders: [{ at: iso(3600e3), title: "x".repeat(500), body: "<b>y</b>\u0007" + "z".repeat(500) }] });
out("long texts are cut, markup/control chars removed", r.status === 200 && rems[0].title.length === LIMITS.maxTitle && rems[0].body.length <= LIMITS.maxBody && !/[<>\u0007]/.test(rems[0].body));
r = await worker.fetch(new Request("https://w.example/reminders", { method: "POST", body: "{nope" }), env);
out("invalid JSON 400", r.status === 400);
r = await worker.fetch(new Request("https://w.example/reminders", { method: "GET" }), env);
out("GET not allowed", r.status === 405);

// Cron: send what is due, keep what is not.
await call("POST", { subscription, reminders: [{ at: iso(30e3), title: "Training um 18:00 Uhr", body: "In 10 Minuten: Cardio · 20 Min." }, { at: iso(3 * 3600e3), title: "Später", body: "noch nicht" }] });
let stats = await sendDueReminders(env, now);
out("cron sends exactly the due reminder", stats.sent === 1 && pushed.length === 1 && rems.length === 1 && rems[0].title === "Später");
const p = pushed[0];
out("push goes to the subscription endpoint", p.url === subscription.endpoint);
out("aes128gcm headers", p.init.headers["Content-Encoding"] === "aes128gcm" && p.init.headers.TTL === "3600");
const payload = JSON.parse(await decrypt(p.init.body));
out("browser can decrypt the payload (RFC 8291)", payload.title === "Training um 18:00 Uhr" && payload.body === "In 10 Minuten: Cardio · 20 Min.");
const jwt = await verifyJwt(p.init.headers.Authorization);
out("VAPID JWT signature valid", !!jwt && jwt.k === vapidPub);
out("VAPID aud/exp/sub", jwt && jwt.claims.aud === "https://fcm.googleapis.com" && jwt.claims.exp > now / 1000 && jwt.claims.exp <= now / 1000 + 24 * 3600 && /^https:|^mailto:/.test(jwt.claims.sub));

// JWK private key form works too.
const env2 = { ...env, VAPID_PRIVATE_KEY: JSON.stringify(await subtle.exportKey("jwk", vk.privateKey)) };
await call("POST", { subscription, reminders: [{ at: iso(10e3), title: "JWK", body: "b" }] });
pushed.length = 0;
stats = await sendDueReminders(env2, now);
out("private key as JWK works", stats.sent === 1 && !!(await verifyJwt(pushed[0].init.headers.Authorization)));

// Temporary failure: kept for the next run.
await call("POST", { subscription, reminders: [{ at: iso(10e3), title: "Retry", body: "b" }] });
pushStatus = 503;
stats = await sendDueReminders(env, now);
out("503 keeps the reminder for a retry", stats.failed === 1 && rems.length === 1);
// Old, unsent: dropped.
stats = await sendDueReminders(env, now + 3 * 3600e3);
out("reminder older than 2 h is dropped unsent", stats.expired === 1 && rems.length === 0);

// Gone subscription: removed with everything.
await call("POST", { subscription, reminders: [{ at: iso(10e3), title: "Gone", body: "b" }, { at: iso(20e3), title: "Gone2", body: "b" }] });
pushStatus = 410;
stats = await sendDueReminders(env, now);
out("410 removes the subscription and its reminders", stats.gone === 1 && subs.size === 0 && rems.length === 0);

// DELETE unsubscribes.
pushStatus = 201;
await call("POST", { subscription, reminders: [{ at: iso(3600e3), title: "T", body: "B" }] });
r = await call("DELETE", { endpoint: subscription.endpoint });
out("DELETE removes subscription + reminders", r.status === 200 && subs.size === 0 && rems.length === 0);

// No VAPID key configured: nothing is sent, nothing lost.
await call("POST", { subscription, reminders: [{ at: iso(10e3), title: "T", body: "B" }] });
pushed.length = 0;
stats = await sendDueReminders({ ...env, VAPID_PRIVATE_KEY: "" }, now);
out("without VAPID secret nothing is sent or lost", pushed.length === 0 && rems.length === 1);

// Rate limit.
limitCalls = 1000;
r = await call("POST", { subscription, reminders: [] });
out("rate limited with CORS", r.status === 429 && r.headers.get("Retry-After") === "60" && r.headers.get("Access-Control-Allow-Origin") === "*");

// Known-answer sanity: same inputs, same ciphertext length (header 86 + data + 1 + 16 tag).
const ct = await encryptPayload({ p256dh: subscription.keys.p256dh, auth: subscription.keys.auth }, "hallo");
out("ciphertext layout", ct.length === 86 + 5 + 1 + 16);
