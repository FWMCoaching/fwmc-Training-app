// Plain-node check of the Trainer-Dashboard storage (kp20, /admin/items):
// a real SQLite (node:sqlite) behind a tiny D1-shaped wrapper, real Request
// objects through the exported fetch(). Every line must end in "True".
//   node --no-warnings test/items.mjs
import { DatabaseSync } from "node:sqlite";
import worker from "../src/index.js";
import { MAX_ITEM_BYTES } from "../src/items.js";

const db = new DatabaseSync(":memory:");
db.exec("CREATE TABLE programs (code TEXT PRIMARY KEY, active INTEGER, config TEXT, created_at TEXT, updated_at TEXT)");
const DB = {
  prepare(sql) {
    const st = { args: [] };
    st.bind = (...a) => { st.args = a; return st; };
    st.first = async () => db.prepare(sql).get(...st.args) || null;
    st.all = async () => ({ results: db.prepare(sql).all(...st.args) });
    st.run = async () => { const r = db.prepare(sql).run(...st.args); return { meta: { changes: Number(r.changes) } }; };
    return st;
  },
};
const env = { DB, ADMIN_TOKEN: "secret-token-123" };
const ORIGIN = "https://fwmcoaching.github.io";
const auth = { Authorization: "Bearer secret-token-123", Origin: ORIGIN };
const call = (path, init = {}) => worker.fetch(new Request("https://w.example" + path, init), env);
const put = (kind, id, body, headers = auth) => call(`/admin/items/${encodeURIComponent(kind)}/${encodeURIComponent(id)}`, {
  method: "PUT", headers: { ...headers, "Content-Type": "application/json" }, body: typeof body === "string" ? body : JSON.stringify(body) });
const list = async (kind) => (await (await call("/admin/items" + (kind ? "?kind=" + kind : ""), { headers: auth })).json()).items;
const out = (label, v) => console.log(label + ":", v ? "True" : "False");

// ---- auth ----
let r = await call("/admin/items?kind=plans");
out("list without token 401", r.status === 401);
r = await call("/admin/items?kind=plans", { headers: { Authorization: "Bearer wrong-token-123", Origin: ORIGIN } });
out("list with wrong token 401", r.status === 401);
r = await put("plans", "TS-07", { data: { kuerzel: "TS-07" } }, { Origin: ORIGIN });
out("put without token 401", r.status === 401);
r = await call("/admin/items/plans/TS-07", { method: "DELETE" });
out("delete without token 401", r.status === 401);
r = await call("/admin/items?kind=plans", { headers: { Authorization: "Bearer secret-token-123", Origin: "https://evil.example" } });
out("foreign origin refused", r.status === 403);
r = await call("/admin/items/plans/TS-07", { method: "OPTIONS", headers: { Origin: ORIGIN } });
out("preflight allows PUT and DELETE for the dashboard", r.status === 204 && /PUT/.test(r.headers.get("Access-Control-Allow-Methods")) && /DELETE/.test(r.headers.get("Access-Control-Allow-Methods")) && r.headers.get("Access-Control-Allow-Origin") === ORIGIN);

// ---- empty, upsert, list ----
out("empty list at start", (await list("plans")).length === 0);
const t1 = Date.UTC(2026, 9, 8, 10, 0, 0);
r = await put("plans", "TS-07", { data: { kuerzel: "TS-07", phases: [] }, updatedAt: t1 });
let j = await r.json();
out("upsert creates", r.status === 200 && j.ok && j.updatedAt === t1);
out("admin CORS on PUT echoes the dashboard origin", r.headers.get("Access-Control-Allow-Origin") === ORIGIN);
await put("plans", "TS-07", { data: { kuerzel: "TS-07", phases: [{ id: "a" }] }, updatedAt: t1 + 5000 });
let items = await list("plans");
out("upsert replaces (one row, new data, new time)", items.length === 1 && items[0].data.phases.length === 1 && items[0].updatedAt === t1 + 5000);
await put("bausaetze", "abc123", { data: { id: "abc123", kind: "kombi", name: "Kopf wach" } });
await put("plan-versions", "TS-07", { data: [{ at: "2026-10-08T10:00:00Z", plan: {} }] });
await put("current", "current", { data: { kuerzel: "TS-07" } });
await put("plans", "ÄB-1", { data: { kuerzel: "ÄB-1" } });
out("Kürzel with umlaut accepted", (await list("plans")).some((x) => x.id === "ÄB-1"));
out("list filters by kind", (await list("bausaetze")).length === 1 && (await list("bausaetze"))[0].data.name === "Kopf wach");
out("versions keep an array", Array.isArray((await list("plan-versions"))[0].data));
const all = await list("");
out("list without kind returns every kind", new Set(all.map((x) => x.kind)).size === 4 && all.length === 5);
r = await put("plans", "TS-08", { data: { kuerzel: "TS-08" }, updatedAt: 12 });
j = await r.json();
out("absurd client time becomes server time", Math.abs(j.updatedAt - Date.now()) < 5000);

// ---- validation ----
r = await put("secrets", "x", { data: {} });
out("bad kind on PUT 400", r.status === 400 && (await r.json()).error === "bad_kind");
r = await call("/admin/items?kind=secrets", { headers: auth });
out("bad kind on list 400", r.status === 400);
r = await put("plans", "a b<script>", { data: {} });
out("bad id 400", r.status === 400 && (await r.json()).error === "bad_id");
r = await put("plans", "x".repeat(81), { data: {} });
out("id longer than 80 refused", r.status === 400);
r = await put("current", "other", { data: {} });
out("current only under id 'current'", r.status === 400);
r = await put("plans", "TS-09", "{not json");
out("invalid JSON 400", r.status === 400 && (await r.json()).error === "invalid_json");
r = await put("plans", "TS-09", { nodata: 1 });
out("missing data 400", r.status === 400 && (await r.json()).error === "missing_data");
r = await put("plans", "TS-09", { data: "just a string" });
out("data must be an object or array", r.status === 400 && (await r.json()).error === "bad_data");
r = await put("plans", "TS-09", { data: { big: "x".repeat(MAX_ITEM_BYTES) } });
out("item over the size limit 413", r.status === 413 && (await r.json()).error === "too_large");
r = await put("plans", "TS-09", { data: { big: "x".repeat(MAX_ITEM_BYTES - 100) } });
out("item just under the limit stored", r.status === 200);
r = await call("/admin/items/plans", { method: "PUT", headers: auth, body: "{}" });
out("path without id 404", r.status === 404);
r = await call("/admin/items", { method: "POST", headers: auth, body: "{}" });
out("POST on the list 405", r.status === 405);
r = await call("/admin/items/plans/TS-07", { method: "PATCH", headers: auth, body: "{}" });
out("other method on an item 405", r.status === 405);

// ---- delete ----
r = await call("/admin/items/plans/TS-07", { method: "DELETE", headers: auth });
j = await r.json();
out("delete removes", r.status === 200 && j.deleted === true && !(await list("plans")).some((x) => x.id === "TS-07"));
r = await call("/admin/items/plans/TS-07", { method: "DELETE", headers: auth });
out("delete again is fine (deleted false)", r.status === 200 && (await r.json()).deleted === false);
out("other kinds untouched by the delete", (await list("plan-versions")).length === 1);
r = await call("/admin/items/plans", { method: "DELETE", headers: auth });
out("delete needs kind and id", r.status === 404);

// ---- the old routes still work next to it ----
r = await call("/program?code=nope");
out("public lookup unaffected", r.status === 404);
