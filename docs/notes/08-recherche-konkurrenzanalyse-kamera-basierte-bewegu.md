# Recherche: Konkurrenzanalyse & Kamera-basierte Bewegungserkennung (2026-09-27, unbaut)

**This whole section is research and proposal only — nothing built, no
app code touched.** Client asked two things in one message: (1) "Kannst
du Apps wie Switched On analysieren und schauen was uns insgesamt noch
fehlt, insbesondere bei 'Visual Training'?"; (2) "Können wir auch was
bauen, wo die Kamera des Handys oder iPads Bewegungen des Nutzers
während der Übung wahrnehmen und interpretieren muss?". Both answered
below via web research; no follow-up build has been scoped or started.

### Teil 1: Konkurrenzanalyse

**"Switched On" identified**: verified rather than assumed — this is
**SwitchedOn®** (switchedon.com; iOS/Android app "SwitchedOn - Reaction
Training"), a patented "Cognitive-Motor Training" (CMT) app used by pro
athletes, US military and healthcare/fitness clients. Mechanic: 100+
randomized visual/audio stimuli (colours, numbers, arrows) that the
client associates with a real physical action (sprint, shuffle, jump,
touch a target) and must execute as fast as possible; its **"SO
Vision"** feature is AI-powered motion tracking through the device's
own front camera that automatically times and scores the physical
reaction/movement, no separate hardware. Vendor-cited research claims
+5.4% reaction time and +25.8% decision-accuracy vs. traditional drills
(treat as marketing-sourced, not independently verified here). No other
plausible match for the name turned up — generic "vision training/eye
exercise" apps of similar-sounding names exist (Google/App Store) but
are unrelated single-eye-exercise apps, not a serious candidate.

Four to five other well-known systems checked for a broader comparison
(all confirmed real/relevant, not assumed from memory):
- **Senaptec Sensory Station** — a hardware+software assessment battery
  (large touchscreen + specialised attachments), not primarily a
  training app: in under 25 minutes it scores 10 visual/sensorimotor
  skills (visual clarity, contrast sensitivity, depth perception,
  near-far quickness, perception span, multiple object tracking,
  reaction time, target capture, eye-hand coordination, go/no-go) as a
  standardised profile. Its value proposition is the **standardised,
  numeric, comparable profile** across many skills in one sitting —
  something this app has no equivalent of anywhere (see gaps below).
- **NeuroTracker** — Prof. Jocelyn Faubert's (Université de Montréal)
  3D-Multiple-Object-Tracking (3D-MOT) training, delivered with
  stereoscopic 3D glasses for true depth. This app already has a direct
  conceptual sibling — **MOT-Fähigkeit** (NAT, 5th sub-tab, already
  cites NeuroTracker/Pylyshyn in this file) — but flat/2D on a phone
  screen, not stereoscopic. Research on NeuroTracker itself is honestly
  mixed (a 2021 systematic review found real training-measure gains but
  inconsistent transfer to real executive-function/game performance) —
  worth knowing before overselling MOT-Fähigkeit's real-world payoff to
  clients either.
- **Dynavision D2** — a physical wall-mounted board, 64 lights across
  five concentric rings/four quadrants, hit by full-arm reach (not a
  fingertip tap), with four modes (up to combining patterned-light
  memory with cognitive number/letter recognition on top of the light
  hits). This app's own Test-Bereich **Reaktionsfeld-Test** already
  names Dynavision explicitly and mirrors its Mode A/B distinction — but
  as a fingertip tap on a handheld screen, which is a fundamentally
  smaller motor task than reaching across a life-size board (no
  whole-arm proprioceptive/reach-accuracy component at all). Not a gap
  to "fix" so much as an honest ceiling of the handheld-screen medium.
- **RightEye** — dedicated eye-tracking hardware (a real gaze-tracking
  camera, not a generic selfie cam) measuring actual oculomotor
  behaviour: saccades, smooth pursuit, fixation stability. This is a
  capability tier this app cannot reach on a phone/iPad's front camera —
  consumer selfie cameras are not accurate/calibrated enough for
  clinical-grade gaze tracking at arm's length. Relevant honesty point:
  VT's own **Periphere Wahrnehmung** *asks* the client to keep fixating
  centre while judging the periphery, but has no way at all to verify
  they actually did — RightEye-class hardware could catch that, this
  app structurally can't, cheaply or otherwise.
- **Vizual Edge Performance Trainer** — binocular/stereopsis (3D-glasses
  hardware required) vision training for fusion/convergence/depth-cue
  skills, "My Plan" personalised programming, "Open-Gym"/"Game Day"
  modes. Like NeuroTracker, true stereoscopic depth training is out of
  reach on a single flat screen without extra hardware — a boundary of
  the medium, not a missing feature to add.

**Gap analysis — Visual Training (VT) specifically**, from reading its
`EXERCISES` table and `drawScene`/`buildScheduleFor` in `app.js`: VT
today is a shared canvas-based **stimulus-pacing engine** — arrows
(`type:"arrows"`, dirset 4/8/diag, colour-coded direct/reverse rules),
colour+arrow (`vt-color`, `vrw-original`), Stroop (`stroop-classic`/
`stroop-bg`), cross-modal audio+visual (`cross-modal`), and two
cone-based drills (`cone-tap`/`cone-compass`) — dispatched per
`data-exercise` id, all driven by one `buildScheduleFor`/`tick()`
render loop.
- **The single biggest structural gap, and it's the same thing Part 2
  is about**: with the sole exception of "Hütchen sortieren"
  (`type:"color-tap"`, which counts screen taps), **every VT exercise
  is a pure stimulus timer that captures no response at all** — no
  reaction time, no correct/incorrect, no hit rate, nothing. The
  client's physical reaction (say a colour aloud, step a direction,
  touch a cone) is judged live by the human coach watching, not by the
  app. Every competitor reviewed above — SwitchedOn, Senaptec,
  NeuroTracker, Dynavision, RightEye, Vizual Edge — centres its whole
  value proposition on the device/software **objectively measuring**
  that reaction (a number, a score, a report). Meanwhile this app's own
  **Test-Bereich** (18 exercises, all newer/autonomous-built) already
  has the tap-capture/RT-timing infrastructure VT itself never got —
  it's just never been pointed at VT's own arrow/colour drills. A
  real, scoped-later idea: an **optional** "digital erfassen" response
  mode for VT's arrow/colour exercises (tap a direction/colour instead
  of a coach watching), for solo practice without a coach present —
  explicitly optional, since the coached/observed workflow is the
  product today and must not be disturbed by default.
- **No standardised, comparable score or profile** anywhere in VT (or
  the app generally) the way Senaptec's 10-skill battery or RightEye's
  INsight reports give a coach — Test-Bereich exercises do track a
  personal best (`addHistory()`, various `*_BEST_KEY`s) but that's
  self-referential progress, never a norm-referenced or cross-skill
  profile. Building real norms responsibly would need a research base
  this app doesn't have — flagging as a gap, not proposing to fake one.
  Also NAT-level nuance to name specifically: the client's own
  "Farb-Häufigkeit"/Dominanz-Verteilung work in progress (see the
  Ziel-/Signalfarbe section above) is exactly this app's own version of
  "personalise the training", just per-setting rather than a full
  adaptive-difficulty algorithm the way SwitchedOn/Vizual Edge programs
  auto-adjust.
- **Sport-/drill-specific content libraries**: SwitchedOn explicitly
  sells "100+ stimuli" and sport-tailored drill libraries (soccer,
  basketball, tennis, hockey); Vizual Edge has a personalised "My Plan".
  VT's roster is a small, fixed, hand-authored set (~11 entries) with no
  sport-specific variants or client-tailored programme generation beyond
  the existing coach-authored `PROGRAMS`/Cloudflare-code programmes.
  Genuinely more content, not more mechanics, would close this one.
- **A visual angle honesty point, not a gap to add exercises for**: a
  phone/tablet screen at arm's length subtends a much smaller visual
  angle than Dynavision's ~1.2m board or Senaptec's large-format
  station — "peripheral" stimuli on VT/Periph are real but modest in
  scale compared to hardware-scale competitors. Worth being upfront
  about with clients rather than implying screen-based peripheral
  training matches board-scale training 1:1.
- **A genuine relative strength worth naming, not just gaps**: VT's
  `cross-modal` ("Sehen & Hören") exercise, with its Regelwechsel/
  conflict-resolution rule set, is more elaborate than any single
  audio+visual mapping seen in the competitors reviewed above (SwitchedOn
  mixes audio+visual cues but as separate simple 1:1 mappings, not a
  conflict-resolution rule layered on top) — this app is already ahead
  here, not behind.

**Broader gaps beyond VT** (surfaced by the same competitor read, kept
short since VT was the client's specific ask):
- **No coach-facing remote dashboard/report**: every credible competitor
  reviewed gives some kind of report a professional reviews (Senaptec's
  profile, RightEye's INsight platform). This app's own history/best-
  tracking is local-only per device (no backend, per Architecture at the
  top of this file) — Fabian can't see a client's Test-Bereich/VT trend
  data remotely today. A real gap, but a much bigger lift (needs a
  backend) than anything else in this file — flagging, not proposing to
  build.
- **No adaptive/auto-scaling difficulty across a whole session or
  programme** the way SwitchedOn/Vizual Edge market it — individual
  exercises here do have their own progression modes (climb/training/
  etc., see NAT), but nothing spans a whole coach-authored programme.

### Teil 2: Kamera-basierte Bewegungserkennung — Machbarkeit

This would be the app's **first on-device computer-vision exercise, and
its first-ever third-party runtime dependency of any kind** — today
`app.js` is one hand-written IIFE with zero external code (see
Architecture at the top). A hard, non-negotiable constraint carried
into every option below: **camera video must never leave the device** —
everything here is a client-side-only, in-browser approach; nothing
sends a frame anywhere.

**Three technical approaches, compared honestly:**
- **MediaPipe Tasks Vision (Pose Landmarker / Hand Landmarker)** — runs
  fully in-browser via WebAssembly, Google-maintained, ships lite/full/
  heavy model variants (roughly single-digit MB up to ~30MB for
  "heavy", plus ~1-2MB of WASM runtime — approximate, verify exact
  bytes before committing to a variant). Google's own docs quote
  30+fps on mid-range Android/Chrome, **but a filed GitHub issue
  (google/mediapipe#3303) documents real-world iOS Safari performance
  as low as 6-7fps** on iPhone 11/12 Pro Max/13 Pro for the Hands task —
  a serious, documented gap between vendor benchmark and this app's own
  actual constituency (client explicitly said "Handy oder iPad", and
  this app's own testing convention already targets iPad/iPhone Safari
  specifically). Self-hosting both the WASM binaries and the `.task`
  model file (rather than pulling from Google's CDN) is documented and
  supported (`FilesetResolver.forVisionTasks` and the model loader both
  accept local paths/an `ArrayBuffer`) — matching this app's own
  "no external runtime dependency" philosophy, at the real cost of
  committing tens of MB of binary assets into what is today a small,
  all-text repo, and carrying that weight through every deploy target
  (GitHub Pages **and** the separate Claude Artifact publish).
- **TensorFlow.js (MoveNet Lightning/Thunder, or PoseNet)** — a similar
  browser/WASM/WebGL story, comparable iOS-Safari performance risk (this
  is a browser/OS-level constraint, not specific to one vendor's
  library), but a heavier integration (separate `tfjs-core` + backend +
  `pose-detection` script layers vs. MediaPipe Tasks' single bundled
  API) for no obvious upside here. MediaPipe is the more likely pick of
  the two ML options if one is needed at all.
- **Frame-differencing / motion-region detection on a plain `<canvas>`
  (no model, no download at all)** — draw each video frame to a canvas,
  diff its pixel data against the previous frame, threshold the luma
  difference per region. Minified reference implementations run to a
  few hundred bytes; runs at full frame rate on essentially any device
  since it's plain pixel math, not a neural net — no perf risk, no new
  binary assets, closest fit to this app's existing philosophy. Ceiling:
  it can only tell **that** motion happened somewhere/in some region
  (a rectangle, a screen-half, a quadrant), never **what** moved or a
  skeleton/landmark position — but several of the concrete ideas below
  only ever needed that much anyway.

**Camera-permission UX (iOS Safari specifics, since that's this app's
real audience)**: `getUserMedia` requires a secure context (HTTPS —
already true for GitHub Pages) and, on Safari specifically, should be
called from a direct user-gesture handler (a Start-button tap, which
every exercise here already has) rather than on page load, or it
prompts on every load instead of persisting the grant. A sharper,
counter-intuitive wrinkle for this app specifically: iOS treats an
add-to-home-screen'd PWA's camera grant as **less** persistent than a
normal Safari tab's (re-prompts more often in standalone/installed
mode) — and this app's own FAQ actively encourages adding it to the
home screen, so exactly the most-invested users could see the most
friction here. Needs a clear, calm, explicit consent screen before ever
calling `getUserMedia` at all (reusing the existing `.sheet` modal
pattern already used for FAQ/tips), stating plainly that video is
processed on-device in real time and never recorded, stored, or
uploaded — shown at minimum once, arguably briefly re-affirmed every
session start given how much client trust matters in a coaching tool.

**Concrete exercise ideas** (same structure as the Test-Bereich roster;
biased toward coarse motion/region detection over full skeletal pose
where it would train the same thing just as well, per the brief):
- **Start-Reaktionstest (Ganzkörper-Losreagieren)** — grounded in
  whole-body-reaction-time paradigms from sport science (e.g. the 2024
  study on whole-body RT/jump height using a mat switch + light
  stimulus, and sprinter block-start RT research measuring reaction to
  a starting signal). Mechanic: device propped up with the client's
  whole body in frame a few steps back; after a random delay a GO
  signal fires (reusing VT's own colour-flash convention); the client
  explodes into a coach-defined movement (sprint away, jump, lateral
  shuffle — same "coach defines the mapping" spirit as VT's own colour-
  to-action rule) the instant they perceive it. Measured: time from
  stimulus-onset to the first frame where global pixel-difference
  magnitude crosses a threshold = reaction time; a false start (motion
  before GO) flags the same way Go/No-Go's anticipatory taps already do.
  Needs only **frame-differencing** (global, no regions even) — a good
  first candidate to actually build, technically lowest-risk of all
  five.
- **Seitenrichtungs-Reaktionstest** — a whole-body response to VT's own
  existing arrow stimuli (`4-straight`/`8-solo`-style direction cues,
  same rendering reused as-is) instead of a coach-observed step or a
  tap: client stands centred in frame, an arrow points left/right/etc.,
  client steps/shuffles that way. Measured: which half (or which of N
  regions, for more than left/right) of the camera frame shows rising
  pixel-difference activity first, and how fast — a **coarse two-or-
  more-region frame-difference split**, still no pose model, directly
  reusing VT's own existing arrow-stimulus code with camera-region-
  motion swapped in for a tap/coach-judgement as the response channel.
- **Reaktions-Sprungtest** — grounded in reactive/countermovement-jump-
  on-cue testing used in return-to-play/concussion protocols and the
  same whole-body-RT/jump-height literature as the first idea above.
  Device low/propped so the whole body is in frame; on a random-delay
  GO cue the client jumps as explosively as possible. Measured: reaction
  latency via global frame-difference onset (as above), and optionally
  a crude "big-motion duration" as a rough jump-height **proxy** —
  explicitly labelled in-app as a rough proxy, not a validated jump-
  height measurement (real jump-height testing uses a force plate or
  mat switch for a reason). A real v2-only upgrade path exists (a hip-
  keypoint vertical-displacement measurement via Pose Landmarker) but
  is explicitly not needed to ship v1.
- **Bewegungs-Simon (Ganzkörper-Simon-Says)** — grounded in the classic
  "Simon Says" motor-inhibition paradigm (a named, real go/no-go-style
  paradigm, just with whole-body postures instead of button presses),
  and loosely continuous with this app's own `Movement` section's
  existing limb vocabulary (arms/legs heben/strecken). App shows a
  target posture, sometimes prefixed with a verbal "Simon sagt" cue and
  sometimes not (only move on the prefixed version — the inhibition
  twist); client attempts it. This is the one idea that benefits from
  slightly more than pure global differencing — a coarse **quadrant
  split** (upper-left/upper-right/lower-body, say) to check "did motion
  happen roughly where expected", still well short of full skeletal
  landmark tracking, and the recommended thing to try first before
  reaching for a real pose model if quadrant-differencing proves too
  unreliable in testing.
- **Balance-Halten unter Ablenkung** (flagged as the most speculative of
  the five — include only if the others land well): loosely grounded in
  postural-sway/quiet-stance balance research and dual-task-interference
  findings (divided attention measurably degrading postural control is
  well studied), combined with VT's own Stroop/Periph-style distractor
  stimuli running concurrently. But real postural-sway research
  instruments are near-universally **accelerometer/IMU-based** (phone
  held against the chest) or force-plate-based, precisely because a 2D
  camera view can't reliably separate true sway direction/amplitude,
  especially sway toward/away from the camera — so this idea is a
  repurposing, not a validated method, and any resulting "wobble" number
  would need to be presented as rough training feedback only, never as
  a real balance/fall-risk measurement.

**Honest downsides/open questions** — a real technical decision for the
client to weigh in on, not oversold:
- Ship frame-differencing-only exercises first regardless of which ML
  library gets evaluated later — the documented iOS-Safari pose-model
  slowdown (6-7fps in a real filed issue) means a v1 exercise should
  never assume a pose model will feel responsive on the client's actual
  oldest supported device without dedicated hands-on testing on that
  exact hardware first.
- Self-hosting any pose model is a one-way architectural door: once
  shipped, both deploy targets (GitHub Pages **and** the Claude Artifact
  publish) permanently carry tens of MB of binary model/WASM assets that
  today's repo has none of.
- This is the app's first-ever third-party runtime code of any kind,
  even self-hosted with no build step added — a philosophy change, not
  just a feature, and worth the client explicitly signing off on rather
  than discovering after the fact.
- Frame-differencing is lighting/background sensitive (shadows, someone
  walking past the camera, a moving background) and needs real testing
  in an actual training-room/gym environment, not just a quiet room,
  before it can be trusted to not false-trigger.
- Nothing camera-based here is a validated biomechanical measurement —
  every number these exercises would produce (a jump-height proxy, a
  wobble score) is rough training feedback, unlike, say, a touch-event
  reaction time (which has small, consistent, well-understood latency)
  — client-facing copy should say so plainly, the same honest framing
  this file already uses elsewhere for known approximations.
- Every idea above needs the device propped up with the whole body in
  frame from a few steps back — a genuinely different physical setup
  than every existing exercise (all handheld, at arm's length, tap-to-
  respond) and will need its own setup explainer, more friction than
  anything shipped in this app so far.

