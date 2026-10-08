# Ton-Sequenz (Test-Bereich, 2026-10-08)

A tool, not a test: tones on the left, right or both ears as a sequence of
steps, for exercises with the trainer. Spec = section 5 "Empfehlung" of
/mnt/project-files/app/recherche/ton-sequenzen-2026-10-08.md. Stays in the
Test-Bereich until Fabian promotes it (then the "works everywhere" rule
applies: Kombi-Baustein, Wochenplan, trainer code ...).

## Screens
Featured card `#tonOpenBtn` in `#testHome` → `#tonReady` (in `SCREENS`) →
`#tonPlayer` (`.player.calm`, `tonBackBtn` "✕ Beenden", `tonPauseBtn`
"Pause", `#tonProgressEl`). One app.js block `==== Ton-Sequenz ====` right
after "Jedes Auge zählt"; outside it only `SCREENS`, `els.tonReady/
tonPlayer` and one line in `hideAllPlayers()` (`tonHaltSilently()`).

## Data
- Working sequence `fwmc-ton-current-v1`, saved sequences `fwmc-ton-seq-v1`
  (`makePresetStore`/`renderPresetList`/`wirePresetSaveForm`, max 20),
  Kanal-Test done `fwmc-ton-chantest-v1`, last run `fwmc-ton-last-v1`.
- Sequence `{name, repeat 1-10, steps[≤12]}`; step `{freq 20-2000, wave
  sine|triangle|square, ear left|right|both|alt, altS 0.5-10, pattern
  steady|pulse|glide, pulseUnit ms|bpm, onMs/offMs 50-2000, bpm 20-240,
  glideTo 20-2000, dur 5-300 s, pause 0-180 s (5 s steps), vol 5-100 %}`.
- History `kind: "tonseq"` (→ area test), note "<Name> · <Hz> Hz · Vorher:
  …", `before`/`after` fields; "Nachher speichern" on the done panel adds
  " · Nachher: …" to the same entry.

## Audio
Per tone one voice: Oscillator → pulse gain → fade gain → L gain / R gain →
ChannelMerger(2) (input 0 left, 1 right; merger instead of StereoPanner:
"Links" is strictly channel 0) → master gain → destination, on the shared
`workoutAudioCtx` (`unlockCueAudio` on every start tap,
`applyCueAudioSession`).
- Master = step vol/100 × 0.5 × wave factor (sine 1, triangle 0.85, square
  0.45) × `cueVolume()` → 🔊 off = gain 0 (player says so, Probehören does
  nothing). Default step volume 20 %.
- Always starts quiet: exponential fade-in 1.5 s on a fresh step, 0.3 s on
  resume, 60 ms fade-out at the end; pulse edges 8 ms ramps; Wechsel
  switches via `setTargetAtTime` (5 ms); glide = exponential ramp.
- A run is cut at 10 min (`TON_MAX_S`), trailing pause dropped.
- Pause stops the voice; the pause sheet has a live "Lautstärke dieses
  Schritts" (this run only); resume rebuilds the voice from the offset
  (glide/pulse/Wechsel continue where they were).
- `requestWakeLock` while running, `silentSwitchHint()` on first use (iOS).
- Leaving the ready screen or the page going hidden stops Probehören /
  Suchlauf / Kanal-Test; autoPauseOnLeave pauses a run.

## Helpers on the ready screen
- Kanal-Test: 600 Hz pulses "Jetzt links …" then "Jetzt rechts …", end text
  mentions Mono-Audio. The first start of a sequence with one-sided steps
  asks once (confirmDialog "Erst den Kanal-Test?").
- Frequenz-Suchlauf: 100 → 1000 Hz in 60 s (exponential), live Hz,
  "Merken" writes the current Hz into the step being edited.
- Probehören: the selected step for up to 10 s.
- Vorlagen only: Referenz 500 Hz, Referenz 100 Hz (labelled
  "Diagnostik-Referenz", help says no training effect is implied), Links /
  Rechts (Seitenvergleich L/R). No Sacculus/Utriculus wording, no dB.
- Safety note `#tonSafety` (`details.advanced.balance-safety`, collapsed):
  "Training, keine Therapie", stop on dizziness/nausea/pressure/ear noise,
  ask a doctor first with vestibular/ear conditions, tinnitus, epilepsy.

## For Fabian to check on iPhone/iPad (Chromium can't)
Silent switch on/off (+ "Töne auch bei Stummschalter"), L/R separation with
his bone-conduction headphones (always some cross-talk), 100 Hz vs 500 Hz
loudness, Mono-Audio off, screen lock during a sequence, AirPods latency.

## Open questions (from the research)
Which protocol from his training (frequencies, duration, ear, test)? Tone
alone or alongside Gleichgewicht/eye exercises? May clients edit
frequencies or only play trainer sequences (trainer code)?

Test: `tests/ton_sequenz_1008_test.py` (fake AudioContext, node graph).
