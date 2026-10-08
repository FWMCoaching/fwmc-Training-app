// Trainer-Dashboard storage (kp20, 2026-10-08): Fabian's Bausätze, plans,
// Stände and the selected client, the same on every device. Admin-only
// (index.js wraps every call in withAuth, so ADMIN_TOKEN is checked first).
//
//   GET    /admin/items?kind=<kind>      -> {items:[{kind, id, data, updatedAt}]}
//          (without kind: all kinds)
//   PUT    /admin/items/<kind>/<id>      body {data, updatedAt?} -> {ok, kind, id, updatedAt}
//   DELETE /admin/items/<kind>/<id>      -> {ok, deleted}
//
// Kinds mirror the dashboard's local stores (localStorage fwmc-dash-*-v1):
//   bausaetze      one row per Bausatz (id = Bausatz id)
//   plans          one row per client plan (id = Kürzel, never a name)
//   plan-versions  the saved Stände of one client (id = Kürzel)
//   current        the selected client (id = "current")
// No personal data: the dashboard stores Kürzel only.
//
// updated_at is the dashboard's own clock (ms) so "newer wins" compares like
// with like across devices; a missing or absurd value becomes the server time.

export const ITEM_KINDS = ["bausaetze", "plans", "plan-versions", "current"];
export const MAX_ITEM_BYTES = 256 * 1024;
export const MAX_ITEMS_PER_KIND = 2000;
const ID_RE = /^[\p{L}\p{N}._-]{1,80}$/u;

const tableReady = new WeakSet(); // per D1 binding, once per isolate
async function ensureItemsTable(env) {
  if (tableReady.has(env.DB)) return;
  await env.DB.prepare(
    "CREATE TABLE IF NOT EXISTS trainer_items (kind TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at INTEGER NOT NULL, PRIMARY KEY (kind, id))"
  ).run();
  tableReady.add(env.DB);
}

export async function handleItems(request, env, json) {
  const url = new URL(request.url);
  const rest = url.pathname.slice("/admin/items".length); // "" or "/kind/id"
  await ensureItemsTable(env);

  if (rest === "" || rest === "/") {
    if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
    const kind = (url.searchParams.get("kind") || "").trim();
    if (kind && !ITEM_KINDS.includes(kind)) return json({ error: "bad_kind" }, 400);
    const stmt = kind
      ? env.DB.prepare("SELECT kind, id, data, updated_at FROM trainer_items WHERE kind = ? ORDER BY id LIMIT ?").bind(kind, MAX_ITEMS_PER_KIND)
      : env.DB.prepare("SELECT kind, id, data, updated_at FROM trainer_items ORDER BY kind, id LIMIT ?").bind(MAX_ITEMS_PER_KIND * ITEM_KINDS.length);
    const { results } = await stmt.all();
    const items = (results || []).map((r) => {
      let data = null;
      try { data = JSON.parse(r.data); } catch (e) {}
      return { kind: r.kind, id: r.id, data, updatedAt: Number(r.updated_at) || 0 };
    });
    return json({ items }, 200);
  }

  const parts = rest.split("/").filter(Boolean);
  if (parts.length !== 2) return json({ error: "not_found" }, 404);
  let kind, id;
  try { kind = decodeURIComponent(parts[0]); id = decodeURIComponent(parts[1]); }
  catch (e) { return json({ error: "bad_id" }, 400); }
  if (!ITEM_KINDS.includes(kind)) return json({ error: "bad_kind" }, 400);
  if (!ID_RE.test(id)) return json({ error: "bad_id" }, 400);

  if (request.method === "DELETE") {
    const res = await env.DB.prepare("DELETE FROM trainer_items WHERE kind = ? AND id = ?").bind(kind, id).run();
    const changes = res && res.meta ? res.meta.changes : undefined;
    return json({ ok: true, deleted: changes === undefined ? true : changes > 0 }, 200);
  }
  if (request.method !== "PUT") return json({ error: "method_not_allowed" }, 405);

  const declared = Number(request.headers.get("Content-Length") || 0);
  if (declared > MAX_ITEM_BYTES + 1024) return json({ error: "too_large", max: MAX_ITEM_BYTES }, 413);
  const text = await request.text();
  let body;
  try { body = JSON.parse(text); } catch (e) { return json({ error: "invalid_json" }, 400); }
  if (!body || typeof body !== "object" || Array.isArray(body) || !("data" in body)) return json({ error: "missing_data" }, 400);
  const data = body.data;
  if (!data || typeof data !== "object") return json({ error: "bad_data" }, 400);
  const dataText = JSON.stringify(data);
  if (new TextEncoder().encode(dataText).length > MAX_ITEM_BYTES) return json({ error: "too_large", max: MAX_ITEM_BYTES }, 413);

  const now = Date.now();
  let updatedAt = Math.round(Number(body.updatedAt));
  // Dashboard clock, but never before 2026 or more than a day in the future.
  if (!Number.isFinite(updatedAt) || updatedAt < Date.UTC(2026, 0, 1) || updatedAt > now + 864e5) updatedAt = now;

  if (kind !== "current") {
    const have = await env.DB.prepare("SELECT 1 AS x FROM trainer_items WHERE kind = ? AND id = ?").bind(kind, id).first();
    if (!have) {
      const cnt = await env.DB.prepare("SELECT COUNT(*) AS n FROM trainer_items WHERE kind = ?").bind(kind).first();
      if (((cnt && cnt.n) || 0) >= MAX_ITEMS_PER_KIND) return json({ error: "too_many", max: MAX_ITEMS_PER_KIND }, 409);
    }
  } else if (id !== "current") {
    return json({ error: "bad_id" }, 400);
  }

  await env.DB.prepare(
    "INSERT INTO trainer_items (kind, id, data, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT (kind, id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at"
  ).bind(kind, id, dataText, updatedAt).run();
  return json({ ok: true, kind, id, updatedAt }, 200);
}
