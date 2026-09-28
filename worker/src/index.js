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

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    const url = new URL(request.url);

    if (url.pathname === "/program") {
      return handleProgramLookup(request, env);
    }
    if (url.pathname === "/admin/programs") {
      return withAuth(request, env, () => handleAdminPrograms(request, env));
    }
    if (url.pathname === "/admin/program") {
      return withAuth(request, env, () => handleAdminProgramUpsert(request, env));
    }
    if (url.pathname === "/admin/client-history") {
      return request.method === "POST"
        ? withAuth(request, env, () => handleClientHistoryCreate(request, env))
        : withAuth(request, env, () => handleClientHistoryList(request, env));
    }

    return json({ error: "not_found" }, 404);
  },
};

// ---- public: code lookup (used by the training app itself) ----

async function handleProgramLookup(request, env) {
  const url = new URL(request.url);
  const code = (url.searchParams.get("code") || "").trim().toLowerCase();
  if (!code) return json({ error: "missing_code" }, 400);

  const row = await env.DB.prepare("SELECT active, config FROM programs WHERE code = ?").bind(code).first();
  if (!row || row.active !== 1) return json({ error: "not_found" }, 404);
  return json(JSON.parse(row.config), 200);
}

// ---- admin: auth guard ----

async function withAuth(request, env, handler) {
  const header = request.headers.get("Authorization") || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (!env.ADMIN_TOKEN || !token || token !== env.ADMIN_TOKEN) {
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
  const rows = results.map((r) => {
    let config = {};
    try { config = JSON.parse(r.config); } catch (e) {}
    return {
      code: r.code, active: r.active === 1, name: config.name || r.code, config,
      createdAt: r.created_at, updatedAt: r.updated_at,
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
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
  };
}

function json(data, status) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders() },
  });
}
