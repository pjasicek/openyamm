# HUD rendering: as cheap as possible, with little room for stale output (study, 2026-11-15)

The options study that came before the build. **What was built, the rules and the measurements are in
[HUD rendering](HUD_RENDERING.md); read that first.** This page is kept for the comparison of approaches.

## Outcome (same day)

Step 1 was built as the draw list, with solid colours redirected to the palette instead of an image atlas. The
measurements then corrected three things written below:

- The HUD was 89 draws of the party-HUD frame, not ~107, and is 65 now.
- The projection of 1650–1750 FPS was wrong. With every HUD draw skipped the frame is only about 50 µs shorter
  (1390 to 1500 FPS): once a HUD draw needs no program switch and no uniform it costs well under a microsecond,
  and the world's draws set the frame time. So the atlas (step 1b) and steps 3 and 4 were not built; their
  ceilings are in the other page's table.
- Step 2's revision counters were dropped for bounded-age readings (`HudReading`): inventory and actor state have
  too many writers for a counter to be trustworthy, and an age limit cannot be forgotten by a writer.

## The study

It answers how the gameplay HUD should be drawn so that it costs almost nothing per frame and still cannot show old
values. Nothing below was built except as the outcome above says.

## Recommendation in short

1. **One draw list for the whole HUD, one program, colour per vertex, small art in a shared atlas.** Every HUD
   primitive appends vertices to one list; consecutive vertices that share a texture page become one draw. This
   lives entirely inside `GameplayUiRuntime` (all seven HUD `bgfx::submit` calls are there), so no HUD code changes.
   It removes most of the HUD's draws, which is what limits the frame today, and it caches nothing, so it cannot
   be stale.
2. **Derived game facts come from revision counters at their source**, not from per-frame scans and not from
   timers: the party's inventory, a map's kill count.
3. **Text layout and layout lookups are cached by value** (font, scale, string; layout revision). A cache keyed by
   everything that determines its content cannot be stale.
4. **Only then, and only if the numbers still ask for it: memoized widgets.** A widget is a plain state struct and a
   pure function from that struct to vertices; the vertices are reused while the struct compares equal. The
   function cannot read anything but the struct, so there is nothing it can miss. A verify mode rebuilds every
   widget every frame and compares.
5. **No render-to-texture HUD cache and no hand-kept dirty flags.** Reasons below.

Steps 1 and 3 cannot be stale. Step 2 can only be if a function that changes the inventory or the actors forgets
its counter, which a unit test per counter checks. Step 4 has a real risk, and its design is what keeps it small.

## What the HUD costs today

New Sorpigal start pose, 1600 x 900, the user's Medium settings, RTX 3060 Ti, OpenGL, visible window
(method: [perf workflow](../tools/PERF_PROFILING.md#fastest-route-where-does-the-frame-time-go)).

| | Party HUD | Solo HUD (after today's pass) |
| --- | --- | --- |
| FPS | 1360–1395 | 1150–1230 |
| Frame (loop) | ~725 µs | ~830 µs |
| Main thread, whole frame | ~545 µs | ~600 µs |
| Main thread, HUD pass | 85–95 µs | ~140 µs |
| Draws in the frame | 326 | 378 |
| Of them HUD (estimated) | ~107 | ~152 |

The HUD draw counts are estimates: the share of main-thread samples in `bgfx::submit` that sit under the HUD pass,
times the frame's draw count.

Two facts decide everything else:

- **The render thread is the limit, not the game code and not the GPU's pixels.** The main thread finishes its frame
  and then waits 150–250 µs in `bgfx::frame` for the render thread (GL driver calls, uniform commits). Half the
  resolution gives the same FPS.
- **A HUD draw costs about 2 µs of render thread.** The solo HUD's 52 extra draws cost about 100 µs of frame. The HUD
  is a third of all draws in a frame whose world is 220 draws.

So the HUD's cost is first its draw count, second its main-thread time.

## Why the HUD makes so many draws

One quad is one draw unless its neighbour in submission order has the same texture and the same tint:

- Every image is its own texture (a button, an icon, a meter, a frame piece).
- Colour is a uniform of the tinted program, not a vertex attribute: two texts in different colours cannot share a
  draw, and neither can a tinted and an untinted quad.
- A text line is two draws: the font's shadow atlas, then its main atlas. A recoloured run uses a third atlas.
- An ellipse (portraits, rims, the solo HUD's ovals) is its own 96-triangle fan and its own draw; so is each arc.
- The plain `submitHudTexturedQuad` path never batches.

The HUD view is sequential (painter's order), which is right and must stay: batching may merge neighbours, never
reorder.

## Why it costs main-thread time

Measured in the party HUD's 85–95 µs: buttons 14 + 11 µs (`GameplayUiSkin::renderButton`, the formation button),
layout resolution 8, the map progress bar 6, arcs 5, nearest hostile distance 4, the basebar 4, the rest spread
thin. The mechanisms:

- **Names as keys.** Layout elements, textures and fonts are found by string each frame: a hash of the name, often a
  lowercased copy first.
- **Text is laid out every frame**, glyph by glyph through a `std::function`, for strings that change once a minute.
- **Game state is scanned to draw a number.** Before today: the map's kill count three times a frame (walking every
  actor, lowercasing the map name per actor), the party's whole inventory twice a frame to grey two buttons.
- **Small allocations**: vectors of quads, strings for labels, optionals holding a texture name.

## What "stale" would mean

A cached HUD shows something that is no longer true. The inputs that can change under it:

| Input | Examples |
| --- | --- |
| Game values | HP, SP, gold, food, time, buffs and their minutes, recovery, cooldowns, item counts, kill progress |
| Presentation state | hover, pressed, selected member, open popup, alert, HUD screen state |
| Layout | window size, HUD scale, the party-frame and other settings, runtime size overrides |
| Text | language, font fallback, a renamed character |
| Resources | a texture or font reloaded, the device reset, a world's art mounted |
| Time | pulses, sweeps, trails, fades |

A design is safe when each row is covered by construction, not by someone remembering it.

## Options

| | Draws | Main thread | Staleness risk | Effort | Notes |
| --- | --- | --- | --- | --- | --- |
| A. Immediate mode, one batched draw list | very low | as today, minus submit overhead | none | medium, contained in one class | the recommendation's step 1 |
| B. Retained widgets with dirty flags or events | very low with A | very low | high: every writer of every input must flag | high, touches gameplay code | rejected |
| C. Memoized widgets (state struct, pure build) | very low with A | very low | low: only what the build context hides | high, widget by widget | step 4, optional |
| D. Render the HUD to a texture, draw it as one quad | lowest | very low | as B or C, plus resource resets | high | rejected |

**B, rejected.** Dirty flags move the question "did anything change?" to every place that changes anything. HP
changes in combat rules, in spells, in events, in rest, in debug commands. One missed place is a stale HUD that
no test notices. It is also the opposite of the architecture rule that gameplay systems are shared and the HUD reads
them.

**D, rejected.** It needs C or B underneath anyway to know when to redraw the texture. On top of that it adds:
blending into a transparent target and compositing it, which is only correct with premultiplied alpha throughout
(the HUD's art and shaders are straight alpha); a full-resolution target per layer (33 MB at 4K); a full-screen
blended quad every frame, which on a phone's tile renderer costs more than the few draws it replaces; and one more
thing to rebuild on a device reset. After step 1 the HUD is a handful of draws, so D has nothing left to save.

**A plus C** is the shape modern immediate-mode UIs settle on: immediate submission for correctness, one batched
buffer for speed, value-keyed memoization where layout work is heavy.

## Step 1: one draw list (no cache, no staleness)

A `HudDrawList` owned by `GameplayUiRuntime`:

- **Vertex:** position, UV, colour (packed ABGR). One program: `texture * vertex colour`. The tinted program and
  its uniform go away; "untinted" is white.
- **Every primitive appends**: quads, nine-slices, lines, ellipses and arcs (as indexed triangles in the same
  buffers), glyphs. `submitHudTexturedQuad`, `submitHudQuadBatch`, `submitHudTexturedEllipse`, `submitHudTexturedArc`,
  the rotated quad and the font layers keep their signatures and write to the list.
- **A new draw starts only** when the texture page, the sampler class or the scissor differs from the previous
  primitive. Order is never changed.
- **Flush** at the end of the HUD pass and before anything else submits to the HUD view (the model previews have
  views of their own and are not affected). One `flush()` call, asserted empty at frame end.
- **Atlas pages for small art.** Icons, buttons, meters, frame pieces, buff art and the palette's solid colour (one
  white texel) go into shared pages, filled at load or on first use, each image padded so filtering cannot bleed.
  Large or dynamic images stay their own textures and their own draws: portraits, the minimap, the big panels.
- **Fonts: one page per font** holding shadow and main glyphs, so a text is one run of vertices whatever its
  colours. The separate tint atlas is no longer needed.

Sampler classes exist today (`Ui`, `UiIllustration`, `Text`, `SmoothText`); pages are per class.

**Expected.** The HUD's ~107 draws become roughly 10 to 25: one or two atlas pages, the fonts in use, each portrait,
the minimap, the large panels. At 2 µs a draw that is about 170–190 µs of render thread per frame. The render thread
then no longer limits the party-HUD frame; the main thread's ~545 µs does, so the frame would land near 1650–1750
FPS instead of 1380. This is a projection from the measured cost per draw, not a measurement. Android, where a
GLES draw costs more, should gain more; that is unmeasured.

**Staleness: none.** Nothing is kept between frames.

**Risks.** Atlas bleeding at scaled sizes (padding, and half-texel insets for nine-slice edges). Art that relies on
mip filtering when the HUD is scaled down: check which HUD textures have mips before choosing what goes in a page;
leave those out. The page budget on old phones.

## Step 2: derived facts from revision counters

The HUD should never walk the world or the bags to draw a number. Today's fix reads the kill progress ten times a
second and "carries any potion" four times a second. That is cheap and nearly always right, but it is a timer
standing in for knowledge: it can show a quarter second of the old value, and it recomputes forever when nothing
changes.

The durable form is a **counter at the source that the reader compares**:

- `Party` keeps an inventory revision, increased by the few functions that add, remove or change a carried item.
  Item counts, the quick-item lists and the two buttons recompute when the number differs from the one they saw.
- A map runtime keeps a revision for "an actor died, rose, was added or changed side". The progress reading
  recomputes on a new number or a new map.

Counters beat events: the reader pulls, so it cannot miss a notification, be subscribed too late or leak a
subscription. The writer's duty is one line in a handful of mutators, in shared gameplay code, and a unit test per
counter ("each mutator increases it") keeps that duty checked.

## Step 3: caches keyed by value

Safe by definition, because the key is everything the result depends on:

- **Text runs.** Laid-out glyph vertices keyed by (font, scale, string, colour runs), a small most-recently-used
  table, cleared when fonts reload. "82 / 82" is laid out when it changes, not 1400 times a second. This also
  serves the fullscreen screens.
- **Layout.** Elements addressed by a handle resolved once per layout revision, and resolved rectangles keyed by
  (handle, window size, scale, overrides revision). The resolution cache exists already; what remains is the string
  hash per call.
- **Textures and fonts by handle**, resolved once, not by name per draw.

Expected with step 2: the party HUD's main-thread time from ~90 µs to perhaps 40–50 µs. A projection.

## Step 4, optional: memoized widgets

Worth doing only if, after steps 1 to 3, the HUD's main-thread time still matters against the frame's ~500 µs.

A widget (the unit frame, a portrait, the top bar, the action bar, the minimap frame, a buff row) is:

```cpp
struct TopBarState          // plain values only, compared with operator==
{
    int gold;
    int food;
    uint8_t hoveredButton;
    uint8_t pressedButton;
    HudFrameKey frame;      // window size, HUD scale, layout / language / atlas / font revisions
};

void buildTopBar(const TopBarState &state, const HudBuildContext &context, HudDrawList &out);
```

Each frame the HUD **gathers** the state from live game data (reads of a few numbers), compares it with the
widget's last state, and either re-appends the stored vertices (a copy) or builds again.

What keeps it honest:

- **The build function cannot see the game.** It takes the state and a narrow context (fonts, atlas, layout
  metrics), no `GameplayScreenRuntime`, no `Party`. Whatever it draws, it draws from the struct. A value someone
  forgot to put in the struct cannot be drawn at all, cached or not: the bug is a missing number on screen that
  every capture shows, not an old number that shows up once in an hour.
- **Everything else the build can see is in `HudFrameKey`.** The context's content (layout, language, fonts, atlas
  placement) changes only with a revision, and the revisions are part of every state.
- **Verify mode.** `debug.hud_cache_verify`: every frame, also build every widget from its state and compare the
  vertices with the stored ones byte for byte; on a difference log the widget and fail. Turned on in the headless
  release scenarios and the playthrough runs, it proves on every frame of every test that a reused widget equals a
  fresh one. That closes the only hole the signature leaves (a build function that is not pure).
- **Time.** A value that moves every frame is put in the state at the precision the screen shows: a meter's fill in
  pixels, a sweep in pixels, a countdown in the unit its text shows. The widget rebuilds when a pixel or a digit
  changes, which is rarely every frame. Effects that really move every frame (the alert glow's pulse, the portrait
  effects, the damage trail while it runs) are their own small widgets that always rebuild; they are a few quads.
- **Texture content** (a new minimap image, a changed portrait) is not geometry: the vertices are reused, the
  texture is whatever it is now.

The cost of this step is that each widget is rewritten as gather plus build. It is done widget by widget, the most
expensive first, each one checked by the verify mode before the next.

## Coverage of the staleness table

| Input | Covered by |
| --- | --- |
| Game values | steps 1 to 3 read them every frame; step 4 compares them every frame |
| Derived facts (counts, progress) | revision counters at the source, a unit test per counter |
| Presentation state | read every frame; in step 4 part of the widget's state |
| Layout, text, fonts, atlas | value keys and revisions (`HudFrameKey`) |
| Resources reloaded, device reset | the revisions change; the draw list and caches are rebuilt from nothing |
| Time | drawn every frame, or quantized into the state, never a timer deciding when to look |

## Order of work, and how each step is judged

| Step | What | Expected | Judged by |
| --- | --- | --- | --- |
| 0 | Done today (below) | solo 1050 -> ~1200 FPS | measured |
| 1a | Draw list, vertex colour, one program | fewer draws wherever colours alternated | draws and FPS on both saves; captures pixel-equal |
| 1b | Atlas pages, merged font pages | HUD ~107 -> 10–25 draws | the same, plus Android and the scaled HUD sizes |
| 2 | Inventory and map revisions; remove the two timers | no scans, exact values | unit tests per counter |
| 3 | Text run cache, layout handles | HUD main thread roughly halved | profile |
| 4 | Memoized widgets, verify mode | HUD main thread to a few µs | profile; verify mode in scenarios |

Measure after each step with the two saves used here and decide whether the next is still worth its cost. Step 1
is the one that pays for certain. Captures before and after each step must match, as the solo HUD's did today.

## Already done (2026-11-15)

- GL uniform cache indexed by location (render thread, all draws).
- Solo HUD: fills and frames through the palette texture in one batch, slot backings / frames / key labels drawn
  per row, outlined text in four draws, repeated runs laid out once.
- Font lookup without a lowercased copy; the map progress and the two item buttons no longer scan every frame
  (by timers, to be replaced in step 2).

Record: [solo HUD performance](solo_action/HUD.md).

## Not known yet

- Android numbers for any of this.
- Which HUD textures carry mips and are shown scaled down, which decides the atlas's membership.
- How many atlas pages the gameplay HUD and the fullscreen screens need together.
- Whether the fullscreen screens (inventory, dialogue, journal) need more than step 1 gives them for free; the game
  is paused or nearly so while they are open, so probably not.
