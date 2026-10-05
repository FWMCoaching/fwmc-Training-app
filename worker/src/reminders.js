// Erinnerungen (2026-10-05): push reminders before planned trainings.
//
// The app computes its own reminder times (next 14 days of the Wochenplan)
// and replaces them here with POST /reminders {subscription, reminders:[{at,
// title, body}]}. A cron trigger (wrangler.toml, every 5 minutes) sends the
// due ones via Web Push and deletes them. DELETE /reminders {endpoint}
// removes the subscription and everything pending for it.
//
// Stored (D1, see migrations/0001_reminders.sql): the push subscription
// (endpoint + its two public keys, no name, no device id) and the pending
// reminders (time + short text). Nothing else, nothing after sending.
//
// Web Push is implemented with WebCrypto only (no npm runtime deps):
// - VAPID (RFC 8292): ES256 JWT, private key from the secret
//   VAPID_PRIVATE_KEY (JWK JSON, or the base64url "d" value together with
//   the var VAPID_PUBLIC_KEY), public key in the var VAPID_PUBLIC_KEY.
// - Payload encryption (RFC 8291, Content-Encoding aes128gcm).

export const LIMITS = {
  maxReminders: 60,
  maxTitle: 80,
  maxBody: 160,
  maxEndpoint: 1024,
  horizonMs: 15 * 24 * 3600 * 1000,
  maxSubscriptions: 5000,
  sendBatch: 200,
};

// Only real push services - the Worker never posts to an arbitrary URL.
const PUSH_HOSTS = /(^|\.)(fcm\.googleapis\.com|android\.googleapis\.com|push\.services\.mozilla\.com|push\.apple\.com|notify\.windows\.com)$/;

// ---------------------------------------------------------------- helpers

const enc = new TextEncoder();

export function b64urlEncode(bytes) {
  const u8 = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let bin = "";
  for (let i = 0; i < u8.length; i++) bin += String.fromCharCode(u8[i]);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64urlDecode(s) {
  if (typeof s !== "string" || !/^[A-Za-z0-9_\-+/]*=*$/.test(s)) throw new Error("bad_b64");
  const clean = s.replace(/=+$/, "").replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(clean + "=".repeat((4 - (clean.length % 4)) % 4));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function concat(...parts) {
  const len = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(len);
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}

async function sha256Hex(text) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(text)));
  return [...d].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function cleanText(v, max) {
  // No control characters, no markup worth speaking of - plain short text.
  return String(v == null ? "" : v).replace(/[\u0000-\u001f\u007f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}

// ---------------------------------------------------------------- validation

export function validateSubscription(sub) {
  if (!sub || typeof sub !== "object") return null;
  const endpoint = String(sub.endpoint || "");
  if (!endpoint || endpoint.length > LIMITS.maxEndpoint) return null;
  let url;
  try { url = new URL(endpoint); } catch (e) { return null; }
  if (url.protocol !== "https:" || !PUSH_HOSTS.test(url.hostname)) return null;
  const keys = sub.keys || {};
  try {
    const p256dh = b64urlDecode(String(keys.p256dh || ""));
    const auth = b64urlDecode(String(keys.auth || ""));
    if (p256dh.length !== 65 || p256dh[0] !== 4 || auth.length !== 16) return null;
    return { endpoint, p256dh: b64urlEncode(p256dh), auth: b64urlEncode(auth) };
  } catch (e) { return null; }
}

export function validateReminders(list, now) {
  if (!Array.isArray(list)) return null;
  if (list.length > LIMITS.maxReminders) return null;
  const out = [];
  for (const r of list) {
    if (!r || typeof r !== "object") return null;
    const t = Date.parse(r.at);
    if (!Number.isFinite(t)) return null;
    if (t < now - 10 * 60000 || t > now + LIMITS.horizonMs) return null;
    const title = cleanText(r.title, LIMITS.maxTitle);
    const body = cleanText(r.body, LIMITS.maxBody);
    if (!title) return null;
    out.push({ at: new Date(t).toISOString(), title, body });
  }
  return out;
}

// ---------------------------------------------------------------- storage

export async function ensureReminderTables(env) {
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS push_subs (id TEXT PRIMARY KEY, endpoint TEXT NOT NULL, p256dh TEXT NOT NULL, auth TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)").run();
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS push_reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, sub_id TEXT NOT NULL, at TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL)").run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS push_reminders_at ON push_reminders (at)").run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS push_reminders_sub ON push_reminders (sub_id)").run();
}

async function runAll(env, stmts) {
  if (typeof env.DB.batch === "function") return env.DB.batch(stmts);
  for (const s of stmts) await s.run();
}

// ---------------------------------------------------------------- HTTP

export async function handleReminders(request, env, json) {
  if (request.method !== "POST" && request.method !== "DELETE") return json({ error: "method_not_allowed" }, 405);
  if (env.REMINDER_LIMITER) {
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const { success } = await env.REMINDER_LIMITER.limit({ key: ip });
    if (!success) return json({ error: "rate_limited" }, 429, { "Retry-After": "60" });
  }
  const len = Number(request.headers.get("Content-Length") || 0);
  if (len > 32 * 1024) return json({ error: "too_large" }, 413);
  let body;
  try {
    const text = await request.text();
    if (text.length > 32 * 1024) return json({ error: "too_large" }, 413);
    body = JSON.parse(text);
  } catch (e) { return json({ error: "invalid_json" }, 400); }
  if (!body || typeof body !== "object") return json({ error: "invalid_json" }, 400);
  await ensureReminderTables(env);

  if (request.method === "DELETE") {
    const endpoint = String(body.endpoint || (body.subscription && body.subscription.endpoint) || "");
    if (!endpoint || endpoint.length > LIMITS.maxEndpoint) return json({ error: "missing_endpoint" }, 400);
    const id = await sha256Hex(endpoint);
    await runAll(env, [
      env.DB.prepare("DELETE FROM push_reminders WHERE sub_id = ?").bind(id),
      env.DB.prepare("DELETE FROM push_subs WHERE id = ?").bind(id),
    ]);
    return json({ ok: true }, 200);
  }

  const sub = validateSubscription(body.subscription);
  if (!sub) return json({ error: "invalid_subscription" }, 400);
  const now = Date.now();
  const reminders = validateReminders(body.reminders, now);
  if (!reminders) return json({ error: "invalid_reminders" }, 400);
  const id = await sha256Hex(sub.endpoint);
  const iso = new Date(now).toISOString();
  const known = await env.DB.prepare("SELECT id FROM push_subs WHERE id = ?").bind(id).first();
  if (!known) {
    const n = await env.DB.prepare("SELECT COUNT(*) AS n FROM push_subs").first();
    if (n && n.n >= LIMITS.maxSubscriptions) return json({ error: "full" }, 503);
  }
  const stmts = [
    known
      ? env.DB.prepare("UPDATE push_subs SET endpoint = ?, p256dh = ?, auth = ?, updated_at = ? WHERE id = ?").bind(sub.endpoint, sub.p256dh, sub.auth, iso, id)
      : env.DB.prepare("INSERT INTO push_subs (id, endpoint, p256dh, auth, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)").bind(id, sub.endpoint, sub.p256dh, sub.auth, iso, iso),
    env.DB.prepare("DELETE FROM push_reminders WHERE sub_id = ?").bind(id),
    ...reminders.map((r) => env.DB.prepare("INSERT INTO push_reminders (sub_id, at, title, body) VALUES (?, ?, ?, ?)").bind(id, r.at, r.title, r.body)),
  ];
  await runAll(env, stmts);
  return json({ ok: true, count: reminders.length }, 200);
}

// ---------------------------------------------------------------- cron

// Sends everything due (up to one minute early, so a 5-minute cron is never
// more than ~4 minutes late), drops reminders older than 2 hours unsent,
// removes subscriptions the push service reports as gone (404/410) and
// subscriptions with no reminders that were not refreshed for 30 days.
export async function sendDueReminders(env, now = Date.now()) {
  await ensureReminderTables(env);
  const until = new Date(now + 60000).toISOString();
  const stale = new Date(now - 2 * 3600000).toISOString();
  const { results } = await env.DB.prepare(
    "SELECT r.id, r.sub_id, r.at, r.title, r.body, s.endpoint, s.p256dh, s.auth FROM push_reminders r JOIN push_subs s ON s.id = r.sub_id WHERE r.at <= ? ORDER BY r.at LIMIT ?"
  ).bind(until, LIMITS.sendBatch).all();
  const stats = { sent: 0, expired: 0, gone: 0, failed: 0 };
  const vapid = await loadVapid(env);
  const goneSubs = new Set();
  for (const r of results || []) {
    if (goneSubs.has(r.sub_id)) continue;
    if (r.at < stale || !vapid) {
      if (r.at < stale) stats.expired++;
      if (r.at < stale) await env.DB.prepare("DELETE FROM push_reminders WHERE id = ?").bind(r.id).run();
      continue;
    }
    let status = 0;
    try {
      const res = await sendWebPush({ endpoint: r.endpoint, p256dh: r.p256dh, auth: r.auth }, JSON.stringify({ title: r.title, body: r.body }), vapid, { ttl: 3600 });
      status = res.status;
    } catch (e) { status = 0; }
    if (status === 404 || status === 410) {
      goneSubs.add(r.sub_id); stats.gone++;
      await runAll(env, [
        env.DB.prepare("DELETE FROM push_reminders WHERE sub_id = ?").bind(r.sub_id),
        env.DB.prepare("DELETE FROM push_subs WHERE id = ?").bind(r.sub_id),
      ]);
      continue;
    }
    if (status >= 200 && status < 300) stats.sent++;
    else stats.failed++;
    // Retry a temporary failure (429/5xx/network) on the next run; anything
    // else (sent, or a permanent 4xx) is done.
    const retry = status === 0 || status === 429 || status >= 500;
    if (!retry) await env.DB.prepare("DELETE FROM push_reminders WHERE id = ?").bind(r.id).run();
  }
  const old = new Date(now - 30 * 24 * 3600000).toISOString();
  await env.DB.prepare("DELETE FROM push_subs WHERE updated_at < ? AND id NOT IN (SELECT sub_id FROM push_reminders)").bind(old).run();
  return stats;
}

// ---------------------------------------------------------------- VAPID

export async function loadVapid(env) {
  const pub = String(env.VAPID_PUBLIC_KEY || "").trim();
  const raw = String(env.VAPID_PRIVATE_KEY || "").trim();
  if (!pub || !raw) return null;
  const pubBytes = b64urlDecode(pub);
  if (pubBytes.length !== 65 || pubBytes[0] !== 4) throw new Error("bad_vapid_public_key");
  let jwk;
  if (raw.startsWith("{")) jwk = JSON.parse(raw);
  else jwk = { kty: "EC", crv: "P-256", d: raw, x: b64urlEncode(pubBytes.slice(1, 33)), y: b64urlEncode(pubBytes.slice(33, 65)) };
  const key = await crypto.subtle.importKey("jwk", { kty: "EC", crv: "P-256", d: jwk.d, x: jwk.x, y: jwk.y, ext: true }, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const subject = String(env.VAPID_SUBJECT || "https://fwmcoaching.github.io/fwmc-Training-app/");
  return { key, publicKey: pub, subject };
}

export async function vapidJwt(vapid, audience, nowSec = Math.floor(Date.now() / 1000)) {
  const header = b64urlEncode(enc.encode(JSON.stringify({ typ: "JWT", alg: "ES256" })));
  const claims = b64urlEncode(enc.encode(JSON.stringify({ aud: audience, exp: nowSec + 12 * 3600, sub: vapid.subject })));
  const input = `${header}.${claims}`;
  // WebCrypto's ECDSA signature is already the raw r||s form JWS wants.
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, vapid.key, enc.encode(input));
  return `${input}.${b64urlEncode(sig)}`;
}

// ---------------------------------------------------------------- RFC 8291

async function hkdf(salt, ikm, info, bytes) {
  const key = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, key, bytes * 8));
}

// Encrypts one payload for one subscription (single record, aes128gcm).
// `opts.salt` / `opts.serverKeys` exist only so tests can pin the inputs.
export async function encryptPayload(sub, plaintext, opts = {}) {
  const uaPublic = b64urlDecode(sub.p256dh);
  const authSecret = b64urlDecode(sub.auth);
  const serverKeys = opts.serverKeys || await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const asPublic = new Uint8Array(await crypto.subtle.exportKey("raw", serverKeys.publicKey));
  const uaKey = await crypto.subtle.importKey("raw", uaPublic, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const ecdhSecret = new Uint8Array(await crypto.subtle.deriveBits({ name: "ECDH", public: uaKey }, serverKeys.privateKey, 256));
  const keyInfo = concat(enc.encode("WebPush: info\0"), uaPublic, asPublic);
  const ikm = await hkdf(authSecret, ecdhSecret, keyInfo, 32);
  const salt = opts.salt || crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, enc.encode("Content-Encoding: nonce\0"), 12);
  const data = concat(typeof plaintext === "string" ? enc.encode(plaintext) : plaintext, new Uint8Array([2]));
  const aesKey = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce }, aesKey, data));
  const rs = 4096;
  const header = new Uint8Array(16 + 4 + 1 + asPublic.length);
  header.set(salt, 0);
  new DataView(header.buffer).setUint32(16, rs, false);
  header[20] = asPublic.length;
  header.set(asPublic, 21);
  return concat(header, ct);
}

export async function sendWebPush(sub, payload, vapid, opts = {}) {
  const body = await encryptPayload(sub, payload);
  const aud = new URL(sub.endpoint).origin;
  const jwt = await vapidJwt(vapid, aud);
  return fetch(sub.endpoint, {
    method: "POST",
    headers: {
      "Content-Encoding": "aes128gcm",
      "Content-Type": "application/octet-stream",
      TTL: String(opts.ttl || 3600),
      Urgency: "normal",
      Authorization: `vapid t=${jwt}, k=${vapid.publicKey}`,
    },
    body,
  });
}
