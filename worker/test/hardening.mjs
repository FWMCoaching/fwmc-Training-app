// Plain-node check of the Worker's hardening (no wrangler needed): a mock D1
// and rate limiter, then real Request objects through the exported fetch().
import worker from "../src/index.js";

const rows = {
  "dig01": { active: 1, config: JSON.stringify({ name: "Test", blocks: [] }) },
  "alt": { active: 1, config: JSON.stringify({ name: "Alt", blocks: [], validUntil: "2020-01-01" }) },
  "neu": { active: 1, config: JSON.stringify({ name: "Neu", blocks: [], validFrom: "2099-01-01" }) },
  "gruppe1": { active: 1, config: JSON.stringify({ name: "Gruppe", blocks: [], codeKind: "gruppe", seats: 1 }) },
};
const seats = new Set(); // "code|device"
const DB = {
  prepare(sql) {
    return {
      bind(...args) { this.args = args; return this; },
      async first() {
        const a = this.args || [];
        if (sql.includes("SELECT 1 AS x FROM code_devices")) return seats.has(a[0] + "|" + a[1]) ? { x: 1 } : null;
        if (sql.includes("COUNT(*) AS n FROM code_devices WHERE")) return { n: [...seats].filter((k) => k.startsWith(a[0] + "|")).length };
        return rows[a[0]] || null;
      },
      async all() {
        if (sql.includes("GROUP BY code")) {
          const m = {};
          for (const k of seats) { const c = k.split("|")[0]; m[c] = (m[c] || 0) + 1; }
          return { results: Object.entries(m).map(([code, n]) => ({ code, n })) };
        }
        if (sql.includes("ORDER BY updated_at")) return { results: Object.entries(rows).map(([code, r]) => ({ code, ...r })) };
        return { results: [] };
      },
      async run() {
        const a = this.args || [];
        if (sql.includes("INSERT OR IGNORE INTO code_devices")) seats.add(a[0] + "|" + a[1]);
        if (sql.includes("DELETE FROM code_devices")) for (const k of [...seats]) if (k.startsWith(a[0] + "|")) seats.delete(k);
        return {};
      },
    };
  },
};
let calls = 0;
const LOOKUP_LIMITER = { async limit() { calls++; return { success: calls <= 2 }; } };
const env = { DB, ADMIN_TOKEN: "secret-token-123", LOOKUP_LIMITER };
const call = (path, init = {}) => worker.fetch(new Request("https://w.example" + path, init), env);
const out = (label, v) => console.log(label + ":", v ? "True" : "False");

let r = await call("/program?code=dig01", { headers: { Origin: "https://any.site" } });
out("public lookup still works", r.status === 200 && (await r.json()).name === "Test");
out("public lookup stays open to every origin", r.headers.get("Access-Control-Allow-Origin") === "*");
r = await call("/program?code=nope");
out("unknown code 404", r.status === 404);
r = await call("/program?code=dig01");
out("third lookup over the (test) limit is rate limited", r.status === 429);
out("rate limit says when to retry", r.headers.get("Retry-After") === "60");

r = await call("/admin/programs", { headers: { Origin: "https://fwmcoaching.github.io", Authorization: "Bearer secret-token-123" } });
out("admin works from the dashboard origin", r.status === 200);
out("admin CORS echoes only the dashboard origin", r.headers.get("Access-Control-Allow-Origin") === "https://fwmcoaching.github.io");
r = await call("/admin/programs", { headers: { Origin: "https://evil.example", Authorization: "Bearer secret-token-123" } });
out("admin refuses a foreign origin", r.status === 403 && !r.headers.get("Access-Control-Allow-Origin"));
r = await call("/admin/programs", { method: "OPTIONS", headers: { Origin: "https://evil.example" } });
out("preflight from a foreign origin gets no allow-origin", !r.headers.get("Access-Control-Allow-Origin"));
r = await call("/admin/programs", { headers: { Origin: "https://fwmcoaching.github.io", Authorization: "Bearer secret-token-12X" } });
out("wrong token of equal length rejected", r.status === 401);
r = await call("/admin/programs", { headers: { Authorization: "Bearer secret" } });
out("short token rejected (no Origin, e.g. curl)", r.status === 401);
r = await call("/admin/programs", { headers: { Authorization: "Bearer secret-token-123" } });
out("correct token works without Origin (curl/scripts)", r.status === 200);

const env2 = { DB, ADMIN_TOKEN: "x" };
r = await worker.fetch(new Request("https://w.example/program?code=dig01"), env2);
out("lookup works without the limiter binding", r.status === 200);

// ---- codes with run time and seats ----
const env3 = { DB, ADMIN_TOKEN: "secret-token-123" };
const look = (q) => worker.fetch(new Request("https://w.example/program?" + q), env3);
const devA = "aaaaaaaaaaaaaaaaaaaa", devB = "bbbbbbbbbbbbbbbbbbbb";
r = await look("code=alt");
let j = await r.json();
out("expired code 410 with date", r.status === 410 && j.error === "expired" && j.validUntil === "2020-01-01");
r = await look("code=neu");
j = await r.json();
out("not-yet code 403 with date", r.status === 403 && j.error === "not_yet" && j.validFrom === "2099-01-01");
r = await look("code=gruppe1&device=" + devA);
out("group code: first device gets in", r.status === 200);
r = await look("code=gruppe1&device=" + devB);
j = await r.json();
out("group code: second device full", r.status === 403 && j.error === "full");
r = await look("code=gruppe1&device=" + devA);
out("group code: first device again still works", r.status === 200);
r = await look("code=gruppe1");
out("group code without device id refused", r.status === 403);
r = await look("code=dig01");
out("personal code needs no device id", r.status === 200);
r = await worker.fetch(new Request("https://w.example/admin/programs", { headers: { Authorization: "Bearer secret-token-123" } }), env3);
j = await r.json();
out("admin list shows seats used", (j.programs.find((x) => x.code === "gruppe1") || {}).seatsUsed === 1);
r = await worker.fetch(new Request("https://w.example/admin/code-seats-reset", { method: "POST", body: JSON.stringify({ code: "gruppe1" }), headers: { Authorization: "Bearer secret-token-123", "Content-Type": "application/json" } }), env3);
out("seat reset ok", r.status === 200);
r = await look("code=gruppe1&device=" + devB);
out("after reset a new device gets in", r.status === 200);
r = await worker.fetch(new Request("https://w.example/admin/code-seats-reset", { method: "POST", body: "{}" }), env3);
out("seat reset needs the token", r.status === 401);
