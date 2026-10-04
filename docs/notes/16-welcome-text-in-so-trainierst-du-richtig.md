# Welcome text in "So trainierst du richtig" (added 2026-09-29)

Last piece of the same "go through everything independently" follow-up.
The client's ask (from an earlier message, pre-dating this session's
visible window): a dismissible-but-recallable onboarding text explaining
how to start, that Master-Einstellungen exist, that a Kombi-Baukasten
exists, plus a recommendation to book time with a trainer.

**The right home for this already existed, unused for the purpose.**
`#tipsSheet` ("So trainierst du richtig", opened via `openTips()`/
`#tipsBtn`) already auto-opens exactly once, on a genuinely first visit
(`if (!readJSON(TIPS_KEY, false)) openTips();`, `TIPS_KEY =
"fwmc-tips-seen"`, set the moment it's dismissed) and stays reachable
afterwards forever via the same "So trainierst du richtig →" link on the
Visual Training home hero - i.e. it already WAS the "dismissible but
recallable" mechanism the client described, just filled with device-setup
tips (Platz & Ruhe, Gerät stabil, Ton, App-Installation) rather than an
actual app-usage welcome. No new JS needed at all - purely additive
content in `_body.html`:
- A new intro paragraph (`#tipsWelcome`, styled like every other sheet's
  `.group-help` intro) right after the heading, before the existing
  practical-tips list: no account needed, pick a section and start
  directly, the gear icon's Einstellungen apply to every exercise at
  once, and the Kombi-Baukasten combines exercises (including across
  domains) into one session.
- The 4 existing practical tips (unchanged, same order, same ids -
  `tipInstall`'s platform-detection logic in `app.js` wasn't touched).
- A closing `#tipsCoachHint` paragraph after the list, before the "Los
  geht's" button: if unsure what's right for you, talk to your coach, or
  book a slot via the same "Website & Kontakt" link the footer and the
  FAQ's own "who do I contact" answer already use
  (`https://www.fabian-westermann.de/`) - reusing that URL rather than
  inventing a new contact path.

Test: `tests/tips_welcome_test.py` - confirms the sheet still auto-opens
on a genuine first visit with the new welcome/coach paragraphs both
present and containing the right key phrases, confirms the practical
tips list is untouched (still 4 items), confirms dismissing it persists
`fwmc-tips-seen` and stops the auto-open on a later reload, and confirms
the exact same content is still there when recalled later via `#tipsBtn`.

