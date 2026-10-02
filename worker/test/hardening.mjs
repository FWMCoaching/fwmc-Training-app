// Plain-node check of the Worker's hardening (no wrangler needed): a mock D1
// and rate limiter, then real Request objects through the exported fetch().
import worker from "../src/index.js";

const rows = { "dig01": { active: 1, config: JSON.stringify({ name: "Test", blocks: [] }) } };
const DB = {
  prepare(sql) {
    return {
      bind(...args) { this.args = args; return this; },
      async first() { return rows[this.args && this.args[0]] || null; },
      async all() { return { results: [] }; },
      async run() { return {}; },
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
