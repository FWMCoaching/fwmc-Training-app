// Generates a VAPID key pair for the Erinnerungen (Web Push).
//   node scripts/gen-vapid.mjs
// Prints the PUBLIC key (wrangler.toml [vars] VAPID_PUBLIC_KEY and app.js
// REMINDER_VAPID_PUBLIC_KEY) and the PRIVATE key (paste it into
// `npx wrangler secret put VAPID_PRIVATE_KEY`, never commit it).
// Generate once: a new pair invalidates every existing subscription.
const { subtle } = globalThis.crypto;
const kp = await subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
const raw = new Uint8Array(await subtle.exportKey("raw", kp.publicKey));
const jwk = await subtle.exportKey("jwk", kp.privateKey);
const b64url = (u8) => Buffer.from(u8).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
console.log("VAPID_PUBLIC_KEY (wrangler.toml + app.js):");
console.log(b64url(raw));
console.log("");
console.log("VAPID_PRIVATE_KEY (wrangler secret put VAPID_PRIVATE_KEY):");
console.log(jwk.d);
