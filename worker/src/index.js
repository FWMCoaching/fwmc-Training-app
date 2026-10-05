// FWMC Online-Training - Cloudflare Worker
//
// Serves training-code lookups for the public app (GET /program, unchanged,
// no auth - the app itself calls this) and a small admin API (GET/POST
// /admin/...) for the coach dashboard to create/edit codes and log which
// client (Kürzel) received which code. Admin routes require
// `Authorization: Bearer <ADMIN_TOKEN>`, set once via
// `wrangler secret put ADMIN_TOKEN` - never stored in this repo.
//
// D1 schema (database: fwmc-training-codes):
//   programs(code TEXT PRIMARY KEY, active INTEGER, config TEXT, created_at TEXT, updated_at TEXT)
//   client_history(id INTEGER PRIMARY KEY, client_code TEXT, program_code TEXT, note TEXT, created_at TEXT)
//   code_devices(code TEXT, device TEXT, first_seen TEXT, PRIMARY KEY (code, device))
//
// Codes with a run time and seats (2026-10-03), all optional fields of the
// code's config: validFrom / validUntil ("YYYY-MM-DD", Berlin date,
// inclusive) and seats (group code: how many devices may use it). The app
// sends a random device id (no personal data) with every lookup; a new
// device takes a seat until the seats are full. code_devices is created on
// first use (CREATE TABLE IF NOT EXISTS).
//
// Hardening (Fabian, 2026-10-02 - nothing changes for clients):
// - Admin routes answer CORS only for the dashboard's own origin
//   (ADMIN_ORIGINS); the public lookup stays open to any origin.
// - The admin token is compared in constant time.
// - GET /program is rate limited per IP through the LOOKUP_LIMITER binding
//   (wrangler.toml, [[ratelimits]]): 30 lookups per minute is far above what
//   a client typing a code ever needs, but makes guessing codes impractical.
//   If the binding is missing (old wrangler, local dev) the lookup still works.
//
// Erinnerungen (2026-10-05): POST/DELETE /reminders (public, rate limited
// through REMINDER_LIMITER) and a cron trigger every 5 minutes that sends
// due reminders via Web Push - see reminders.js and README.md.

import { handleReminders, sendDueReminders } from "./reminders.js";

const ADMIN_ORIGINS = [
  "https://fwmcoaching.github.io",
  "http://localhost:8845",
];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const isAdmin = url.pathname.startsWith("/admin/");
    const origin = request.headers.get("Origin") || "";
    const cors = isAdmin ? adminCorsHeaders(origin) : corsHeaders();

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }
    // A browser on a foreign site may not use the admin API at all.
    if (isAdmin && origin && !ADMIN_ORIGINS.includes(origin)) {
      return json({ error: "forbidden_origin" }, 403, cors);
    }

    let res;
    if (url.pathname === "/program") {
      res = await handleProgramLookup(request, env);
    } else if (url.pathname === "/reminders") {
      res = await handleReminders(request, env, (data, status, extra) => json(data, status, { ...corsHeaders(), ...(extra || {}) }));
    } else if (url.pathname === "/admin/programs") {
      res = await withAuth(request, env, () => handleAdminPrograms(request, env));
    } else if (url.pathname === "/admin/program") {
      res = await withAuth(request, env, () => handleAdminProgramUpsert(request, env));
    } else if (url.pathname === "/admin/code-seats-reset") {
      res = await withAuth(request, env, () => handleSeatsReset(request, env));
    } else if (url.pathname === "/admin/client-history") {
      res = request.method === "POST"
        ? await withAuth(request, env, () => handleClientHistoryCreate(request, env))
        : await withAuth(request, env, () => handleClientHistoryList(request, env));
    } else {
      res = json({ error: "not_found" }, 404);
    }
    // Admin responses carry the narrowed CORS headers instead of "*".
    if (isAdmin) {
      const headers = new Headers(res.headers);
      headers.delete("Access-Control-Allow-Origin");
      for (const [k, v] of Object.entries(cors)) headers.set(k, v);
      res = new Response(res.body, { status: res.status, headers });
    }
    return res;
  },

  // Cron trigger (wrangler.toml [triggers]): send due reminders.
  async scheduled(event, env, ctx) {
    ctx.waitUntil(sendDueReminders(env).catch((e) => console.error("reminders", e && e.message)));
  },
};

// ---- public: code lookup (used by the training app itself) ----

async function handleProgramLookup(request, env) {
  const url = new URL(request.url);
  const code = (url.searchParams.get("code") || "").trim().toLowerCase();
  if (!code) return json({ error: "missing_code" }, 400);
  if (code.length > 64) return json({ error: "not_found" }, 404);

  if (env.LOOKUP_LIMITER) {
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const { success } = await env.LOOKUP_LIMITER.limit({ key: ip });
    if (!success) return json({ error: "rate_limited" }, 429, { ...corsHeaders(), "Retry-After": "60" });
  }

  const row = await env.DB.prepare("SELECT active, config FROM programs WHERE code = ?").bind(code).first();
  if (!row || row.active !== 1) return json({ error: "not_found" }, 404);
  const config = JSON.parse(row.config);

  const today = berlinToday();
  const from = isoDay(config.validFrom), until = isoDay(config.validUntil);
  if (until && today > until) return json({ error: "expired", validUntil: until }, 410);
  if (from && today < from) return json({ error: "not_yet", validFrom: from }, 403);

  const seats = seatCount(config);
  if (seats) {
    const device = (url.searchParams.get("device") || "").trim().toLowerCase();
    if (!/^[a-z0-9]{16,40}$/.test(device)) return json({ error: "full" }, 403);
    await ensureDeviceTable(env);
    const known = await env.DB.prepare("SELECT 1 AS x FROM code_devices WHERE code = ? AND device = ?").bind(code, device).first();
    if (!known) {
      const used = await env.DB.prepare("SELECT COUNT(*) AS n FROM code_devices WHERE code = ?").bind(code).first();
      if ((used && used.n) >= seats) return json({ error: "full" }, 403);
      await env.DB.prepare("INSERT OR IGNORE INTO code_devices (code, device, first_seen) VALUES (?, ?, ?)")
        .bind(code, device, new Date().toISOString()).run();
    }
  }
  return json(config, 200);
}

function isoDay(v) { return typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : ""; }
function seatCount(config) {
  const n = Math.floor(Number(config.seats));
  return config.codeKind === "gruppe" && n >= 1 ? Math.min(n, 1000) : 0;
}
function berlinToday() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
}
async function ensureDeviceTable(env) {
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS code_devices (code TEXT NOT NULL, device TEXT NOT NULL, first_seen TEXT NOT NULL, PRIMARY KEY (code, device))").run();
}

// ---- admin: free all seats of a group code (e.g. new group, same code) ----

async function handleSeatsReset(request, env) {
  if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
  let body;
  try { body = await request.json(); } catch (e) { return json({ error: "invalid_json" }, 400); }
  const code = String(body.code || "").trim().toLowerCase();
  if (!code) return json({ error: "missing_code" }, 400);
  await ensureDeviceTable(env);
  await env.DB.prepare("DELETE FROM code_devices WHERE code = ?").bind(code).run();
  return json({ ok: true }, 200);
}

// ---- admin: auth guard ----

async function withAuth(request, env, handler) {
  const header = request.headers.get("Authorization") || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (!env.ADMIN_TOKEN || !token || !timingSafeEqual(token, env.ADMIN_TOKEN)) {
    return json({ error: "unauthorized" }, 401);
  }
  return handler();
}

// ---- admin: manage training codes ----

async function handleAdminPrograms(request, env) {
  if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
  const { results } = await env.DB
    .prepare("SELECT code, active, config, created_at, updated_at FROM programs ORDER BY updated_at DESC")
    .all();
  await ensureDeviceTable(env);
  const seatRows = (await env.DB.prepare("SELECT code, COUNT(*) AS n FROM code_devices GROUP BY code").all()).results || [];
  const seatsUsed = Object.fromEntries(seatRows.map((r) => [r.code, r.n]));
  const rows = results.map((r) => {
    let config = {};
    try { config = JSON.parse(r.config); } catch (e) {}
    return {
      code: r.code, active: r.active === 1, name: config.name || r.code, config,
      createdAt: r.created_at, updatedAt: r.updated_at, seatsUsed: seatsUsed[r.code] || 0,
    };
  });
  return json({ programs: rows }, 200);
}

async function handleAdminProgramUpsert(request, env) {
  if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
  let body;
  try { body = await request.json(); } catch (e) { return json({ error: "invalid_json" }, 400); }

  const code = String(body.code || "").trim().toLowerCase().replace(/\s+/g, "-");
  if (!code) return json({ error: "missing_code" }, 400);
  if (!body.config || typeof body.config !== "object") return json({ error: "missing_config" }, 400);

  const active = body.active === false ? 0 : 1;
  const configText = JSON.stringify(body.config);
  const now = new Date().toISOString();

  const existing = await env.DB.prepare("SELECT code FROM programs WHERE code = ?").bind(code).first();
  if (existing) {
    await env.DB
      .prepare("UPDATE programs SET active = ?, config = ?, updated_at = ? WHERE code = ?")
      .bind(active, configText, now, code)
      .run();
  } else {
    await env.DB
      .prepare("INSERT INTO programs (code, active, config, created_at, updated_at) VALUES (?, ?, ?, ?, ?)")
      .bind(code, active, configText, now, now)
      .run();
  }
  return json({ ok: true, code, created: !existing }, 200);
}

// ---- admin: client history (which Kürzel got which code, and when) ----

async function handleClientHistoryList(request, env) {
  const url = new URL(request.url);
  const client = (url.searchParams.get("client") || "").trim();
  const stmt = client
    ? env.DB.prepare("SELECT * FROM client_history WHERE client_code = ? ORDER BY created_at DESC").bind(client)
    : env.DB.prepare("SELECT * FROM client_history ORDER BY created_at DESC LIMIT 500");
  const { results } = await stmt.all();
  return json({ entries: results }, 200);
}

async function handleClientHistoryCreate(request, env) {
  if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
  let body;
  try { body = await request.json(); } catch (e) { return json({ error: "invalid_json" }, 400); }

  const clientCode = String(body.clientCode || "").trim();
  const programCode = String(body.programCode || "").trim().toLowerCase();
  const note = body.note ? String(body.note).slice(0, 500) : null;
  if (!clientCode || !programCode) return json({ error: "missing_fields" }, 400);

  const now = new Date().toISOString();
  await env.DB
    .prepare("INSERT INTO client_history (client_code, program_code, note, created_at) VALUES (?, ?, ?, ?)")
    .bind(clientCode, programCode, note, now)
    .run();
  return json({ ok: true }, 200);
}

// ---- helpers ----

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
  };
}

function adminCorsHeaders(origin) {
  const headers = {
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Vary": "Origin",
  };
  if (ADMIN_ORIGINS.includes(origin)) headers["Access-Control-Allow-Origin"] = origin;
  return headers;
}

// Constant-time string compare, so response timing never hints at how many
// leading characters of a guessed token were right.
function timingSafeEqual(a, b) {
  const enc = new TextEncoder();
  const x = enc.encode(String(a));
  const y = enc.encode(String(b));
  let diff = x.length ^ y.length;
  const len = Math.max(x.length, y.length);
  for (let i = 0; i < len; i++) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}

function json(data, status, headers) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...(headers || corsHeaders()) },
  });
}
