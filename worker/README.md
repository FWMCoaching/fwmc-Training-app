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
to this file. The dashboard's own admin-token field (entered once, stored
only in the coach's browser) must match whatever value you set here.
