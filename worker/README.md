# FWMC Online-Training - Worker

Source for the Cloudflare Worker `online-training` (serves
`https://online-training.fwmc.workers.dev`). Until now this Worker existed
only as deployed code with no repo - this folder is that repo.

## What it does

- `GET /program?code=...` - public, unauthenticated. Looks up a training
  code in D1 (`programs` table) and returns its config JSON. Called by the
  training app itself (`app.js`'s `CODE_API`).
- `GET/POST /admin/programs`, `/admin/program`, `/admin/client-history` -
  the coach dashboard's API. Requires `Authorization: Bearer <ADMIN_TOKEN>`.

## Data (D1 database `fwmc-training-codes`)

- `programs(code, active, config, created_at, updated_at)` - one row per
  training code. `config` is the same JSON shape as the app's own
  `PROGRAMS`/bundle definitions (a `blocks` array, or `{type:"bundle",
  programs:[...]}`).
- `client_history(id, client_code, program_code, note, created_at)` - a log
  of which client (Kürzel only, no names) received which code and when.
- `trainer_items(kind, id, data, updated_at)` - the Trainer-Dashboard's
  Bausätze, plans (by Kürzel), Stände and selected client (kp20, 2026-10-08),
  via `GET /admin/items?kind=`, `PUT/DELETE /admin/items/<kind>/<id>` (admin
  token). Code `src/items.js`, migration `migrations/0002_trainer_items.sql`
  (`npx wrangler d1 migrations apply fwmc-training-codes --remote`), deploy
  steps and smoke checks in `docs/notes/10-trainer-dashboard-worker-repo.md`.

## First-time deploy / setup

```sh
cd worker
npm install
npx wrangler login          # once, opens a browser to authorize
npx wrangler secret put ADMIN_TOKEN   # paste a long random token - this is
                                       # what the coach dashboard will need
npx wrangler deploy
```

After that, `npx wrangler deploy` from this folder ships any further changes
to this file.

## Erinnerungen (Web Push, 2026-10-05)

- `POST /reminders` `{subscription, reminders:[{at, title, body}]}` - public,
  rate limited (`REMINDER_LIMITER`, 20/min/IP). Upserts the push
  subscription and **replaces** all its pending reminders. Limits: 60
  reminders, `at` from now to 15 days ahead, title 80 / body 160 chars,
  endpoint only on real push services (Google, Mozilla, Apple, Microsoft).
- `DELETE /reminders` `{endpoint}` - removes the subscription and its reminders.
- Cron every 5 minutes (`scheduled`): sends due reminders (RFC 8291
  aes128gcm + VAPID ES256, WebCrypto only), deletes each after sending,
  drops unsent ones older than 2 h, removes subscriptions that answer
  404/410. Code: `src/reminders.js`. Tables: `push_subs`, `push_reminders`.
- Tests (plain node, no wrangler): `npm test`.

### Deploy steps (once)

```sh
cd worker
npm install
# 1. Tables in D1 (the Worker would also create them on first use)
npx wrangler d1 execute fwmc-training-codes --remote --file=migrations/0001_reminders.sql
# 2. VAPID key pair - generate ONCE (a new pair breaks all subscriptions)
node scripts/gen-vapid.mjs
# 3. Private key as a secret (paste the VAPID_PRIVATE_KEY line)
npx wrangler secret put VAPID_PRIVATE_KEY
# 4. Public key: put the VAPID_PUBLIC_KEY line into wrangler.toml [vars]
# 5. Deploy (also registers the 5-minute cron)
npx wrangler deploy
```

6. Paste the same public key into `app.js`:
   `const REMINDER_VAPID_PUBLIC_KEY = "<public key>";`, run `sh build.sh`,
   commit, push. Until then the app shows "Erinnerungen werden gerade
   eingerichtet" and the switch stays off.
7. Check: `curl -i -X OPTIONS https://online-training.fwmc.workers.dev/reminders`
   answers 204 with `DELETE` in `Access-Control-Allow-Methods`; in the
   Cloudflare dashboard the Worker shows the cron trigger. The dashboard's own admin-token field (entered once, stored
only in the coach's browser) must match whatever value you set here.
