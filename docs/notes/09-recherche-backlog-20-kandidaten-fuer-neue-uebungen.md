# Recherche-Backlog: 20 Kandidaten für neue Übungen (2026-09-27, unbaut)

**Diese Liste ist reine Recherche, kein Build-Log.** Der Kunde bat explizit
darum, über mehrere Stunden 20 WEITERE Übungen zu recherchieren, sie
erklären zu können und ggf. leicht zu skizzieren, ausdrücklich OHNE sie zu
bauen ("ohne sie zu bauen... herausfinden, erklären können, ggf leicht
skizzieren"). Nichts hier ist implementiert - keine neue Route, kein
`EXERCISES`/`WORKOUT_EXERCISES`-Eintrag, kein Test existiert für irgendeinen
der 20 Kandidaten unten. Every candidate was checked against the full
existing inventory first (VT's 12 `EXERCISES`, Atemtraining's breathing
patterns, Movement's Life-Kinetik-style limb cueing, Workout's 14-exercise
catalog, NAT's Remember/Blitz-Raster/Flash Speicher Test/MOT-Fähigkeit, and
all 18 Test-Bereich entries below) and against the "Wortfarben-Test
overlaps with VT's Stroop" blind spot flagged in Offene Fragen, specifically
to avoid repeating that mistake. Every paradigm below was verified via a
live web search at write time (not recalled from memory alone) - a real,
named researcher/study or well-established protocol, with at least one
citation. **A future Test-Bereich session should treat this list as a
first-look starting point, not research from scratch again - but should
still re-verify grounding itself before committing to building one**
(a paradigm name or year can be misremembered even after being written down
once, and this list was assembled in one sitting rather than reviewed by
the client).

1. **Iconic-Speicher-Test** (Partial-Report-Aufgabe). *Grounding*: Sperling
   (1960) - the classic partial-report paradigm establishing iconic
   (sensory) visual memory: a grid of characters flashes for ~50ms, then a
   post-stimulus tone (high/mid/low) cues which ROW to report, at a
   variable delay; partial-report accuracy at zero delay (~75%) hugely
   exceeds whole-report accuracy (~35%), revealing a large-capacity but
   fast-decaying visual store. *Mechanic sketch*: a 3×3 or 3×4 grid of
   letters/digits flashes for a short, fixed duration; immediately after
   (delay 0/300/700/1000ms, stepped across trials) a single row is marked
   (e.g. an arrow beside it); the client taps that row's characters back
   via an on-screen keypad (reusing Flash Speicher Test's `.flash-key`
   keypad convention). Reports per-delay accuracy, the actual curve this
   paradigm exists to show (accuracy dropping as delay grows). *Warum
   eigenständig*: Merkspanne-Test (Luck & Vogel change-detection) asks one
   global same/different judgment over an unmasked array shown at normal
   speed; Flash Speicher Test recalls a SEQUENTIAL stream of individually-
   shown characters; this is the only one flashing a whole array at once
   for a near-subliminal duration and probing raw sensory-store DECAY via a
   post-hoc cue - a genuinely different memory stage (iconic, pre-attentive)
   from anything built so far. *Zuhause*: Test.

2. **Sofortmengen-Test** (Subitizing-Aufgabe). *Grounding*: Kaufman, Lord,
   Reese & Volkmann (1949) coined "subitizing" - instant, accurate
   enumeration of up to ~4 items with flat reaction time, versus slower,
   roughly linear-rising RT when serially counting beyond that; Trick &
   Pylyshyn (1994) tie the small-number/large-number RT break to a
   limited-capacity preattentive individuation mechanism (their "FINST"
   theory - the same visual-indexing idea underlying MOT itself).
   *Mechanic sketch*: a scatter of 1-9 identical dots flashes briefly
   (e.g. 300-600ms, backward-masked), then the client taps the matching
   count on a 1-9 keypad. Trials span the full 1-9 range repeatedly; the
   done-panel plots RT against count and reports where the slope visibly
   steepens (the subitizing/counting break, roughly around 4). *Warum
   eigenständig*: no existing exercise measures a QUANTITY judgment at all
   - Merkspanne judges a colour change, Suchtest judges presence/absence of
   one target, Corsi/Remember/Blitz-Raster judge WHICH positions - this is
   the only one whose entire point is "how many," with a distinctive
   two-regime RT signature as its outcome measure. *Zuhause*: Test.

3. **Linienhalbierungs-Test**. *Grounding*: the line bisection test
   (Schenkenberg, Bradford & Ajax, 1980) - a standard neuropsychological
   measure of visuospatial attention: the client marks the perceived
   midpoint of a horizontal line; a systematic left/right deviation
   reveals an attentional bias toward one side of space (used clinically to
   detect neglect, but the underlying leftward "pseudoneglect" bias exists
   in healthy people too and is sensitive to attentional load). *Mechanic
   sketch*: a plain horizontal line of varying length/position appears on
   the stage; the client taps where they judge its centre to be; the app
   measures the deviation in px (converted to % of line length) from the
   true centre. Repeated across several line lengths/positions (reusing
   Trail Making's anti-overlap random placement for line position),
   reporting mean deviation and its direction as "Aufmerksamkeits-Tendenz."
   *Warum eigenständig*: this is the only exercise whose outcome measure is
   a spatial BIAS (a signed deviation from a physical fact) rather than a
   reaction time, an accuracy%, or a recalled set - no RT is even
   collected. *Zuhause*: Test.

4. **Kippbild-Test** (Necker-Würfel-Aufgabe). *Grounding*: the Necker cube
   (Necker, 1832) and the broader multistable-perception literature - an
   ambiguous wireframe cube that spontaneously flips between two
   equally-valid 3D interpretations under continuous, UNCHANGED visual
   input; reversal rates vary widely between individuals (roughly 4-60
   flips/minute in the literature) and are modestly under some volitional
   control. *Mechanic sketch*: a wireframe cube (or a simpler Necker-style
   ambiguous shape) is displayed continuously for a fixed duration (e.g.
   60-90s); the client taps once every time their perceived orientation
   flips. Reports total reversals and reversals/minute as the tracked best
   score; optionally a second run instructs "versuche die Wechsel bewusst
   zu verlangsamen" to probe voluntary control, mirroring the literature's
   own manipulation. *Warum eigenständig*: the only exercise on the whole
   tab (Test or NAT) where the physical stimulus literally never changes -
   every other exercise's "event" is something appearing, moving, or
   changing on screen; here the event being counted is a purely internal
   perceptual switch. *Zuhause*: Test.

5. **Bewegungskohärenz-Test** (Random-Dot-Kinematogramm). *Grounding*: the
   random-dot kinematogram / motion-coherence paradigm (Newsome & Paré,
   1988, tying coherence-detection thresholds to visual area MT) - a field
   of dots where some fraction move together in one direction (signal) and
   the rest move randomly (noise); the coherence % needed to judge the
   direction reliably is a well-established, adaptively-measurable
   threshold of motion-perception sensitivity. *Mechanic sketch*: a field
   of ~100-200 dots animates for 1-2s per trial; the client taps one of
   four/eight direction arrows for where the coherent dots moved. Coherence
   % starts high (easy) and steps down via a 3-down/1-up staircase (same
   staircase shape UFOV already uses) toward a threshold; done-panel
   reports the converged coherence-threshold %, lower = better (same
   "lower-is-better" shape as UFOV/Hick/Antizip). *Warum eigenständig*: MOT
   tracks discrete, individuated objects that stay put relative to each
   other; Rotationstest judges a STATIC orientation; this is the only
   exercise asking for a judgment about GLOBAL, INTEGRATED motion pooled
   across many simultaneously-moving dots, a genuinely different visual
   computation (motion-energy pooling vs. object individuation/tracking).
   *Zuhause*: Test.

6. **Stopp-Signal-Test**. *Grounding*: the stop-signal paradigm (Logan,
   Cowan & Davis, 1984, JEP:HPP - the independent race-model method for
   estimating Stop-Signal Reaction Time, SSRT; Verbruggen & Logan, 2008,
   review its use as a purer measure of response inhibition than simple
   go/no-go). *Mechanic sketch*: most trials are a simple choice-RT task
   (tap left/right arrow as fast as possible); on a minority of trials
   (~25%), a stop signal (e.g. the stimulus turns red, or a tone plays)
   appears AFTER a short, adaptively-tracked delay (stop-signal delay,
   SSD) - the client must try to withhold the already-initiated tap. SSD
   goes up after a successful stop (harder next time) and down after a
   failed one (easier next time), staircasing toward ~50% stopping
   success; SSRT is estimated as mean go-RT minus the converged SSD.
   *Warum eigenständig*: Go/No-Go decides whether to respond BEFORE any
   motor programme starts (the stimulus itself signals "don't go"); the
   Stop-Signal task's whole point is CANCELLING a response already in
   flight after commitment, a distinct and, per the inhibition literature,
   more sensitive construct (SSRT) than Go/No-Go's simple accuracy% -
   genuinely not a redundant "Go/No-Go v2." *Zuhause*: Test.

7. **Kartensortier-Test** (Regel-Lern-Aufgabe). *Grounding*: the Wisconsin
   Card Sorting Test (Grant & Berg, 1948; Milner, 1963, tying perseverative
   errors to dorsolateral-prefrontal damage) - cards vary on several
   dimensions (colour/shape/count); the client sorts by matching to
   reference cards, the correct RULE is never stated and must be inferred
   purely from right/wrong feedback, and the rule changes without warning
   once several correct matches accumulate. *Mechanic sketch*: reference
   cards (e.g. 4 coloured shapes with 1-4 count) sit fixed on screen; each
   trial a new card appears and the client taps which reference card it
   "matches" (by whichever rule is currently active, unknown to them);
   only right/wrong feedback is given. After N consecutive correct
   matches the active rule silently switches. Reports categories completed
   plus perseverative errors (continuing the OLD rule immediately after a
   switch) as the key outcome measure. *Warum eigenständig*: Regelwechsel-
   Test explicitly CUES which rule applies every trial (a switch-cost
   paradigm); this is the only exercise where the rule is never told at
   all and must be discovered/re-discovered from feedback alone - a
   genuinely different construct (rule learning + perseveration) from
   cued switching. *Zuhause*: Test.

8. **Konzentrations-Scan-Test** (d2-Prinzip). *Grounding*: the d2 Test of
   Attention (Brickenkamp, first published 1962/1981 in Germany;
   Brickenkamp & Zillmer, 1998, English edition) - one of the most-used
   concentration/selective-attention tests in German-language sport and
   occupational psychology specifically (originally built partly for
   driving-fitness assessment): rows of "d" and "p" letters, each with 1-4
   small dashes, are scanned under time pressure and every "d" with
   exactly two dashes is marked. *Mechanic sketch*: rows of small
   look-alike characters (d/p with varying dash counts) scroll or tile
   across the stage; the client taps every valid target within a strict
   per-row time limit before the next row appears (or before time runs
   out); highly similar distractors (p with 2 dashes, d with 1 or 3
   dashes) make this a genuine, sustained visual-scanning-under-pressure
   task rather than a single-target search. Reports total processed,
   omission errors (missed target) and commission errors (wrong tap)
   separately - the d2's own two-error-type convention. *Warum
   eigenständig*: Suchtest is discrete-trial (one target, then the next
   trial); this is a single CONTINUOUS scanning task across many rows of
   near-identical items with no trial boundaries, explicitly modelling
   sustained concentration under time pressure rather than a single search
   decision - and it's the one candidate here most directly rooted in
   German-language sport-psychology practice, a strong cultural fit.
   *Zuhause*: Test.

9. **Zeichen-Zuordnungs-Test**. *Grounding*: the Digit Symbol Substitution
   Test (DSST, the "Coding" subtest of the Wechsler Adult Intelligence
   Scale) - a widely-used general processing-speed measure: a key maps
   each digit 1-9 to an abstract symbol; the client converts as many
   digits to symbols as possible within a fixed time (classically 90-120s).
   *Mechanic sketch*: a fixed key row (digit → symbol) stays visible at the
   top of the stage; below it, a sequence of bare digits appears one at a
   time (or a short visible row), and the client taps the matching symbol
   from an on-screen symbol keypad. Runs for a fixed duration (e.g. 90s);
   reports correct substitutions completed, the DSST's own standard
   scoring. *Warum eigenständig*: nothing else on this tab is a
   translation/coding task using an arbitrary lookup key - Hick-Test varies
   the NUMBER of response alternatives with a spatially-compatible mapping
   (the lit box IS the target), this instead demands constantly consulting
   an arbitrary key and re-mapping symbol identity, a different (coding/
   psychomotor) facet of processing speed. *Zuhause*: Test.

10. **Gleichzeitigkeits-Test**. *Grounding*: the temporal-order-judgment
    (TOJ) paradigm (Sternberg & Knoll, 1973, and the broader audiovisual-
    simultaneity-window literature) - two stimuli in different modalities
    (e.g. a flash and a beep) are presented at varying stimulus-onset
    asynchronies (SOA); the client judges which came first, revealing the
    "point of subjective simultaneity" and the width of the temporal
    window within which asynchronous events are still perceived as
    simultaneous. *Mechanic sketch*: on each trial a brief flash and a
    short tone play with an SOA that varies (e.g. -300ms to +300ms,
    flash-first to tone-first, an adaptive or fixed set of SOAs); the
    client taps "Bild zuerst" or "Ton zuerst" immediately after. Reports a
    fitted psychometric curve's 50%-point (point of subjective
    simultaneity, ideally ~0ms but often shifted) and the simultaneity
    window's width. *Warum eigenständig*: the app's existing "Sehen &
    Hören" (VT `cross-modal`) exercise reacts to combined/conflicting
    visual+auditory CUES with a rule mapping; this instead asks a pure
    "which came first" TIMING judgment with no response-rule at all - a
    genuinely different multisensory question (temporal binding, not
    stimulus-response mapping) and a response TYPE ("earlier/later") no
    other exercise uses. *Zuhause*: Test.

11. **Takt-Tipp-Test**. *Grounding*: sensorimotor synchronization / the
    finger-tapping-to-a-metronome paradigm (Repp, 2005, review) - taps to
    a steady beat typically PRECEDE the beat by 20-100ms ("negative mean
    asynchrony"), and both the mean asynchrony and its variability are
    standard, well-studied outcome measures of rhythmic motor timing.
    *Mechanic sketch*: a metronome beat (audio click and/or a pulsing
    on-screen dot) plays at a chosen tempo (e.g. 90-120 BPM); the client
    taps anywhere on screen in time with each beat for a fixed number of
    beats/duration. Reports mean asynchrony (ms, signed - negative means
    "ahead of the beat," matching the literature's own convention) and
    asynchrony SD (consistency) per tempo. *Warum eigenständig*: nothing
    built so far measures RHYTHMIC MOTOR TIMING to a steady, predictable
    beat - Antizipationstest judges a single one-off timing prediction for
    an approaching object, this is repeated, PACED motor synchronization
    over many beats, the classic "keeping time" skill relevant to
    movement-based/rhythmic sport contexts. *Zuhause*: Movement (a
    "bewegungsnahes" motor-timing skill fits Movement's own framing better
    than a purely visual/cognitive Test entry, though it could equally sit
    in Test if the client prefers keeping all researched exercises there).

12. **Verfolgungs-Test** (Pursuit-Rotor-Prinzip). *Grounding*: the pursuit
    rotor task, one of the oldest and most-studied apparatus-based motor-
    learning paradigms (originating with a rotating-disc/stylus device
    studied since the 1930s-50s, e.g. Ammons, 1955's survey of the rotary-
    pursuit literature) - the classic outcome measure is simply "time on
    target" (% of trial duration spent successfully tracking a
    continuously-moving target). *Mechanic sketch*: a small target moves
    continuously along a path (circular, figure-eight, or randomised) on
    the stage; the client keeps a finger pressed on/near it, dragging to
    follow it in real time (a NEW continuous-drag interaction, unlike any
    existing tap-based mechanic). Speed/path complexity scale with
    difficulty; reports "Zeit auf Ziel" (% time within a tolerance radius
    of the target) over the run, the field's own standard score. *Warum
    eigenständig*: MOT is a WATCH-then-tap-at-the-end task (no continuous
    input during tracking); this is the only exercise requiring
    CONTINUOUS manual tracking input the whole time, a distinct
    visual-motor coordination skill (closed-loop tracking) rather than
    covert attention-tracking. *Zuhause*: Test (flagged as needing a new
    continuous-drag input primitive, unlike this tab's existing discrete-
    tap convention - worth scoping that cost before committing to build).

13. **Handlungsvorhersage-Test** (Okklusions-Paradigma). *Grounding*: the
    temporal-occlusion paradigm from sport-expertise research (Abernethy,
    1990, on anticipation in squash; Farrow & Abernethy's tennis-serve
    occlusion work) - a filmed or animated action sequence is cut off
    (occluded) at a defined point BEFORE the outcome is visible (e.g.
    before a struck ball leaves the racket), and skilled performers reliably
    predict the outcome (direction/type) from early postural/kinematic cues
    that novices can't yet use. *Mechanic sketch*: a short animated
    sequence (a simple schematic figure winding up to throw/kick/serve in
    one of several directions) plays and cuts off at one of several
    occlusion points (early/mid/late, i.e. progressively more information
    shown); the client then taps which outcome direction they predict from
    a small set of options. Reports accuracy per occlusion point - the
    actual outcome curve this paradigm exists to reveal (accuracy rising
    the later the occlusion point is, and HOW MUCH it rises from early to
    late is the real signal of anticipatory skill). *Warum eigenständig*:
    Antizipationstest (Coincidence-Anticipation Timing/Bassin) requires a
    precisely-TIMED MOTOR response to a continuously-visible moving
    object; this is a pure perceptual PREDICTION/JUDGMENT from
    incomplete, truncated visual information with a delayed multiple-
    choice answer, no motor timing at all - a completely different
    facet of "anticipation," and explicitly sport-context-flavoured
    (matches FWMC's actual coaching material, e.g. serve/throw direction).
    *Zuhause*: Test (this is also the strongest VT/"bewegungsnahes"
    conceptual fit of the batch if the client would rather see it grouped
    with Visual Training instead - flag and ask rather than assume).

14. **Daueraufmerksamkeits-Test** (PVT-Prinzip). *Grounding*: the
    Psychomotor Vigilance Task (Dinges & Powell, 1985) - the "gold
    standard" sustained-attention/fatigue measure: a simple visual cue
    appears at pseudo-random 2-10s intervals over a SUSTAINED run
    (classically 10 minutes); the client taps as fast as possible each
    time; "lapses" (RT > 500ms) accumulate measurably as time-on-task and
    fatigue increase, famously sensitive to sleep loss. *Mechanic sketch*:
    a plain stimulus (dot/digit counter) appears at random 2-10s intervals
    for a genuinely long run (e.g. 5 or 10 minutes, a client-chosen
    length); the client taps as fast as possible each time it appears - no
    categorisation, no conflict, the simplest possible response. Reports
    mean RT, RT variability, and lapse count/rate (RT > 500ms) plotted
    across the run's timeline (early vs. late segment), surfacing a
    vigilance-DECREMENT curve rather than a single average. *Warum
    eigenständig*: every existing RT-based exercise here is a short,
    fixed-trial block (24-48 trials, a few minutes) explicitly measuring a
    momentary cognitive facet (inhibition/conflict/switching); this is the
    only one whose entire point is a SUSTAINED, MANY-MINUTE run measuring
    attentional DECAY over time-on-task itself, directly relevant to
    fatigue/overtraining monitoring in a coaching context. *Zuhause*: Test.

15. **Start-Reaktionstest**. *Grounding*: sprint-start reaction-time
    research underlying track & field's false-start rule - the IAAF's
    100ms minimum-reaction-time threshold and the research questioning it
    (e.g. work reporting individual auditory RTs as low as 80ms and
    recommending the limit be lowered to 80-85ms) - a well-documented,
    sport-specific application of simple auditory reaction time where
    responding TOO EARLY (a false start) is itself the critical, penalised
    outcome, not just being slow. *Mechanic sketch*: the client holds
    still (a "Fertig"/set-position prompt), then a start signal (a sharp
    tone, like a starting pistol) fires after a randomised, unpredictable
    delay; a tap before the tone counts as a false start (reported
    separately, mirroring the real sport's binary disqualification logic),
    a tap after reports raw auditory RT in ms. Reports mean RT (excluding
    false starts) plus false-start RATE as a second, equally important
    outcome. *Warum eigenständig*: the only exercise using a PURE AUDIO
    stimulus with literally nothing shown on screen during the actual
    trial (every other RT exercise is visual, or visual+audio combined),
    and the only one whose main outcome partly measures RESPONDING TOO
    SOON as a failure mode rather than too slow - directly modelled on a
    real, well-known competitive-sport rule rather than a lab paradigm.
    *Zuhause*: Test (also a plausible Movement warm-up drill before
    explosive-start work, if the client would rather it live there).

16. **Standfestigkeits-Test** (Romberg-Prinzip). *Grounding*: the Romberg
    test, a classical neurological balance assessment, now commonly
    digitised via a phone's own accelerometer/gyroscope (recent work
    validates smartphone-based postural-sway measurement against
    force-plate gold standards, and sport-science studies use exactly this
    kind of sway data to compare balance between athlete groups, e.g.
    ankle-instability research in soccer/volleyball players). *Mechanic
    sketch*: the client holds the phone (or has it in a pocket/armband)
    and stands still for a fixed duration (e.g. 20-30s) in two conditions -
    eyes open, then eyes closed - while the app reads the device's motion
    sensors (`DeviceMotionEvent`) and computes a sway metric (e.g. total
    path length or RMS acceleration in the horizontal plane). Reports sway
    for each condition and the eyes-closed/eyes-open RATIO - the classic
    Romberg-quotient idea (closing the eyes removes visual balance input,
    revealing how much the client relies on it). *Warum eigenständig*: the
    only candidate here (and the only exercise in the whole app) using
    device motion sensors instead of taps at all, and the only one testing
    physical postural/balance control rather than any screen-based
    perceptual or motor-response skill. *Zuhause*: Movement (a natural fit
    given Movement is already the app's one non-VT-canvas physical/postural
    domain; would need a `DeviceMotionEvent` permission prompt on iOS
    Safari, worth scoping before committing to build). Note: this pairs
    naturally with the camera-based "Balance-Halten unter Ablenkung" idea
    in the Kamera-basierte-Bewegungserkennung research just above, which
    independently arrived at the same conclusion (accelerometer/IMU, not
    camera, is the right sensor for sway) from the opposite direction.

17. **Alarmierungs-Test** (Alerting-Netzwerk). *Grounding*: the Attention
    Network Test framework (Fan et al., 2002; building on Posner &
    Petersen's 1990 theory of three separable attentional networks -
    alerting, orienting, executive) - specifically isolating the ALERTING
    network: a purely non-spatial warning cue (no location information at
    all, unlike Posner's own cue) that simply signals "something is about
    to happen," measured by how much it speeds simple/choice RT relative
    to no warning at all. *Mechanic sketch*: on half the trials, a plain,
    centred, non-directional warning flash/tone plays a fixed interval
    before a left/right target; on the other half, no warning at all
    precedes the same target. The client responds to the target's
    direction as fast as possible either way. Reports the "Alarmierungs-
    Effekt" (RT with warning minus RT without) as the outcome measure -
    the network's efficiency, a bigger effect meaning a bigger benefit from
    a plain readiness cue. *Warum eigenständig*: Posner-Cueing's cue is
    spatially INFORMATIVE (predicts WHERE, testing orienting); this cue
    carries zero location information and only tests WHETHER a generic
    warning speeds readiness at all - the two are explicitly designed in
    the source literature to be separable, independent networks, so this
    fills a real gap rather than duplicating Posner-Cueing. *Zuhause*:
    Test.

18. **Vorlaufzeit-Test** (Foreperiod-Effekt). *Grounding*: the foreperiod
    effect in simple reaction time (Niemi & Näätänen, 1981, Psychological
    Bulletin, "Foreperiod and simple reaction time" - the "expectancy
    hypothesis": participants build a moment-by-moment expectancy of WHEN
    a stimulus will arrive across a variable interval, and RT typically
    drops as the foreperiod stretches on without the stimulus yet
    appearing, since the conditional probability of "it's about to happen
    NOW" keeps rising). *Mechanic sketch*: a single visible warning cue
    (e.g. a fixation dot turning steady) is followed by a target after a
    foreperiod that varies randomly trial-to-trial across a wide range
    (e.g. 500ms to 4000ms, several discrete steps); the client responds to
    the target as fast as possible each time, no categorisation. Reports
    mean RT PLOTTED AGAINST foreperiod duration - the actual expectancy
    curve this paradigm exists to surface (RT typically fastest at the
    longest foreperiods within a block). *Warum eigenständig*: distinct
    from Alarmierungs-Test's binary cued-vs-uncued contrast and from every
    other exercise's fixed or difficulty-bucketed ISI - this is the only
    one whose independent variable is a continuously-varying TIME INTERVAL
    itself, reported as a continuous RT-vs-interval curve rather than a
    single difference score. *Zuhause*: Test.

19. **Vibrations-Konflikt-Test**. *Grounding*: the crossmodal congruency
    task (Spence, Pavani & Driver, first introduced 1998/2004) - vibro-
    tactile stimulators and visual LEDs are placed at matching upper/lower
    locations; the client judges the ELEVATION (up/down) of a felt
    vibration while trying to ignore a simultaneous, independently-placed
    visual distractor light - responses are reliably slower/less accurate
    when the seen and felt locations disagree, a well-studied measure of
    visual-tactile spatial-attention integration. *Mechanic sketch*: the
    phone vibrates briefly at a "felt" location conceptually mapped to
    up/down (e.g. two quick pulses = "oben," one long pulse = "unten," or
    simply always vibrating while a visual dot flashes at a screen
    position); the client taps "oben" or "unten" for what they FELT, while
    a visual dot simultaneously flashes at the same or the OPPOSITE
    screen position as a to-be-ignored distractor. Reports accuracy/RT for
    congruent vs. incongruent trials and their difference as the
    crossmodal-conflict cost, the same "effect size" reporting convention
    as Simon/Stroop/Flanker. *Warum eigenständig*: the only exercise using
    the phone's vibration motor as a genuine stimulus channel at all -
    every existing conflict paradigm (Simon/Flanker/Stroop) is a purely
    visual, within-modality conflict; this is the app's first ever
    CROSS-MODALITY (felt vs. seen) conflict test. *Zuhause*: Test (a novel
    input channel for this app - `navigator.vibrate` support/reliability
    across devices is worth checking before committing to build).

20. **Ganzheit-Detail-Test** (Navon-Aufgabe). *Grounding*: the Navon task
    (Navon, 1977, "Forest before the trees") - large ("global") letters
    built out of many small ("local") letters; when cued to attend one
    level, responses are faster/more accurate to the GLOBAL level, and an
    incongruent local letter (different from the global one) slows global
    responses less than an incongruent global letter slows local
    responses - the classic "global precedence" effect. *Mechanic sketch*:
    a large letter, itself made of many copies of a (possibly different)
    small letter, appears; a cue (shown before or alongside it) says
    "Groß" or "Klein" for which level to judge that trial; the client taps
    one of two response buttons for the letter's identity at THAT level,
    ignoring the other level, as fast as possible. Reports accuracy/RT
    split by congruent vs. incongruent trials (global letter matches vs.
    doesn't match the local letters) AND by which level was cued, showing
    the classic asymmetric interference pattern (global interferes with
    local more than the reverse) as the outcome measure. *Warum
    eigenständig*: Suchtest varies feature vs. conjunction search across
    SEPARATE items on a display; Regelwechsel-Test switches between two
    semantic classification RULES on one bivalent digit; this is the only
    exercise where a SINGLE object simultaneously carries the SAME kind of
    information (a letter identity) at two different perceptual SCALES at
    once, testing which scale gets processed first/more automatically - a
    genuinely different "level of processing" question, not a rule or a
    search. *Zuhause*: Test.

