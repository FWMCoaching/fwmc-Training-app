# Erinnerungen (Push vor geplanten Trainings, 2026-10-05)

Fabian approved: a push notification on the phone before every planned
training of the Wochenplan (Heute). Decided with him: lead time "Zur Zeit",
5, 10, 15, 30 Minuten (default 10); entries without a time get one morning
reminder at a time the client sets (default 08:00); on iPhone/iPad only for
the app on the home screen (iOS 16.4+), explained in plain German.

## App (app.js, block "Erinnerungen" just before the install hint)
- Grundeinstellungen section `#reminderGroup`: switch `#reminderOnCheck`,
  status `#reminderStatus` (role=status), lead row `[data-reminder-lead]`
  (`.choice-row`), morning time `#reminderMorningInput` (`.plan-input`),
  help text with a link to Datenschutz.
- Prefs `fwmc-reminders-v1` `{on, lead, morning}` - in `BACKUP_EXCLUDE`,
  because "on" belongs to this device's push subscription.
- States (`support()`): `setup` (no VAPID key yet: switch disabled, "werden
  gerade eingerichtet"), `ios-install` (iPhone/iPad in Safari), `unsupported`,
  `denied` (explains the device settings), `ok`.
- Enable: `Notification.requestPermission()` -> `pushManager.subscribe({
  userVisibleOnly, applicationServerKey: REMINDER_VAPID_PUBLIC_KEY})` -> sync.
  Disable: `DELETE /reminders {endpoint}` + `unsubscribe()`.
- `computeReminders(now)` (exposed as `window.__fwmcComputeReminders` for the
  test): today + 13 days from `occurrencesOn()` (phases, extras, skips; done
  entries left out), local time -> UTC via `Date` (DST-safe), lead applied,
  past ones dropped, one morning reminder per day for untimed entries, sorted,
  max 60. Texts: title "Training um 18:00 Uhr", body "In 10 Minuten: Cardio ·
  20 Min." / "Jetzt: …"; morning "Heute steht Training an" / "Heute geplant: …".
  Area labels only - never a free-text title, name or history.
- Sync (`POST /reminders {subscription, reminders}`): on start (2 s), 1.5 s
  after every `savePlan()` and `addHistory()` (`reminderPlanChanged()`), on
  lead/morning change, and when the app becomes visible after >= 6 h.
  Eigene Termine (`fwmc-events-v1`) are NOT reminded (free-text titles; ask
  Fabian before adding).
- `REMINDER_VAPID_PUBLIC_KEY` holds the deployed key (Worker deployed 2026-10-05 19:10 UTC, version 6c507a9d; previous version 3a75e714 for rollback). Without a key the switch is disabled;
  tests set a key via `fwmc-test-reminder-key`.

## sw.js
`push` shows the notification (icon-192.png), `notificationclick` focuses an
open app window or opens `index.html?bereich=heute`. Caching unchanged.

## Worker (worker/src/reminders.js)
`POST/DELETE /reminders` (CORS `*`, `REMINDER_LIMITER` 20/min/IP, only real
push-service hosts, 60 reminders, 15 days, 80/160 chars), cron `*/5` sends
due reminders (up to 1 min early, so at most ~4 min late), RFC 8291 + VAPID
ES256 with WebCrypto, deletes after sending, drops unsent > 2 h, removes
404/410 subscriptions and idle ones after 30 days. Tables `push_subs`,
`push_reminders` (`worker/migrations/0001_reminders.sql`). Deploy steps:
worker/README.md. Tests: `cd worker && npm test` (decrypts the payload like
a browser; cross-checked once against the reference `http_ece` library).

## Open
- Needs deploy (D1 migration, VAPID keys, secret, `wrangler deploy`) and the
  public key in app.js - see worker/README.md.
- Check on a real iPhone (home-screen app, iOS 16.4+) and Android: permission
  prompt, notification look, tap opens Heute. Chromium tests fake the push stack.
- The window is 14 days: a client who never opens the app gets no reminders
  after that (the help text says "Öffne die App ab und zu").

Test: `tests/reminders_1005_test.py`.
