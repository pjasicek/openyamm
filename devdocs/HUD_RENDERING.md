# HUD rendering

How the gameplay HUD and the fullscreen gameplay screens (inventory, spellbook, journal, dialogue and the rest) get
onto the screen, and the few rules that keep it cheap and correct. Built on 2026-11-15; the options that were
weighed are in the [study](HUD_RENDERING_STUDY.md).

## The model

**Immediate mode over one draw list**, the arrangement Dear ImGui and most game HUDs use:

1. Every frame, HUD code draws everything again from live game state by calling the HUD functions
   (`submitHudTexturedQuad`, `submitHudQuadBatch`, the ellipse, arc and text functions, `GameplayObsidianPainter`).
   Nothing is remembered from the frame before, so nothing can show an old value.
2. Those functions do not draw. They append vertices to the frame's `HudDrawList` (`game/ui/HudDrawList.h`), in
   call order.
3. Before the frame is presented the list is drawn once (`GameplayUiRuntime::flushHudDrawList`): one vertex buffer,
   one program, one draw per run of neighbours that share a texture, a sampler and a clip rectangle.

Call order is paint order, always. The list merges neighbours; it never reorders.

```
HUD code (any file)                GameplayUiRuntime                      bgfx, HUD view (sequential)
  painter.fill / text / texture ─►   hudDrawTarget(): texture, sampler ─►   flushHudDrawList():
  submitHud*()                       HudDrawList.add(): vertices, order     one buffer, one program,
                                                                            a draw per texture run
```

## What a draw is made of

- **Vertex** (`HudVertex`, 24 bytes): position, UV, colour, alpha cut. Colour is per vertex, so a tint never breaks
  a batch and needs no uniform.
- **Program** `vs_hud` / `fs_hud`: texture times vertex colour.
- **Alpha cut**: untinted images drop texels at or below 10 % alpha, tinted ones none. That is what the two programs
  the HUD used before did (`fs_shadowmaps_texture` discarded, `fs_menu_tint` did not), and the art is tuned to it.
  It travels per vertex (in the position's unused z), so it does not break batches either.
- **Solid colours share one texture.** `ensureHudPaletteColor` gives a colour's texel in the 64 x 64 palette
  texture. A solid colour's own 1 x 1 texture (`ensureSolidHudTextureLoaded`, used widely) is redirected to the
  same texel when it is drawn (`m_hudDrawTextures`), so however a caller asks for a colour, all colours on the HUD
  are one texture.
- **What still starts a new draw:** a different texture (each HUD image is its own texture; a font's shadow and
  its glyphs are two), a different sampler (text filtering against image filtering), a clip rectangle.

## Rules for HUD code

1. **Draw through the HUD functions.** Never `bgfx::submit` into the HUD view yourself. If a draw must use another
   program, call `flushHudDrawList()` first, as `renderActorInspectPreview` does for its palette sprite; otherwise it
   would land under everything collected before it.
2. **Read the game when you draw.** Take values from `Party`, the world runtime and the UI state in the draw
   function. Do not store what you drew, do not add "changed" flags, and do not make gameplay code tell the HUD
   anything.
3. **No scan per frame.** A number that needs a walk over the map's actors or the party's bags goes through
   `HudReading` (below). Everything else is read directly.
4. **Group what repeats.** Draws are saved by putting things of one texture next to each other in call order:
   - fills and frames into a `GameplayObsidianPainter::Quads` list, then one `submit` (any colours, one draw);
   - lines of one font and colour in one `painter.texts` call (two draws for any number of lines);
   - a row of slots or tiles as passes (all backings, then the contents, then all frames, then all labels) when
     the items do not overlap. `GameplaySoloHud::renderHud` is the example.
5. **Caches are keyed by value, or they are not caches.** The layout resolution cache (element, window size) and the
   arc mesh cache (the arc's numbers) are fine: the key is everything the result depends on. A cache that needs
   someone to invalidate it is not.

That is all a HUD author has to know. The draw list, the palette redirection and the flush are inside
`GameplayUiRuntime`; no HUD file refers to them.

## Facts that are costly to work out

Two HUD elements need a walk: the MAW map progress (every actor of the map) and whether the party carries any
scroll or potion (every bag). They use `HudReading<Value, Subject>` (`game/ui/HudReading.h`):

```cpp
return context.interactionState().mapProgress.get(pWorld, SDL_GetTicks(), 100,
    [pParty, pWorld]() { return pParty->rules().monsters.mapProgress(*pWorld); });
```

The value is worked out again when the subject changes (another map, another party) or when it is older than the
age limit (100 ms and 250 ms here). The limit bounds how old a shown value can be **by construction**.

Why not a change counter or an event from the code that changes the fact: item and actor state are written from
many places (a public inventory vector, HP and hostility set across two 19,000-line world runtimes). One writer
that forgets its counter is a number that stays wrong until something else happens to refresh it, and no test
would notice. An age limit cannot be forgotten by anyone. Use a counter only for a fact with a single writer.

## Checking a HUD change

- **Draws per frame** are in every isolated run's log: `[GameFramePerf] ... avg_hud_draws=65 avg_hud_primitives=262`.
  A change that adds twenty draws is visible there without profiling.
- **Which draws:** add `--set debug.effect_stats_delay_seconds=4` to a run. The log gets one `[HudDraw]` line per
  draw with its texture name and vertex count. Two neighbours with different textures are a batch that broke.
- **Ordering faults:** run with `OPENYAMM_HUD_UNBATCHED=1`. Every HUD call is then drawn at once, as before the draw
  list. If a wrong overlap disappears, something draws into the HUD view outside the list (rule 1).
- **Same pixels:** capture before and after (`debug.screenshot_path`, or a `debug.menu_input_tour_path` tour that
  opens a screen and captures it) and compare. The fullscreen screens pause the game, so they compare exactly.
- Unit tests: `HudDrawListTests.cpp` (merging, order, clip, 16-bit split), `HudReadingTests.cpp`.
- Frame time: [perf workflow](../tools/PERF_PROFILING.md#fastest-route-where-does-the-frame-time-go).

## Measurements (2026-11-15)

New Sorpigal start, 1600 x 900, Medium settings, RTX 3060 Ti, OpenGL, visible window; median FPS over 12 s, two or
three runs each.

| | Party HUD | Solo HUD |
| --- | --- | --- |
| As reported in the morning | 1200–1250 | 1020–1085 |
| After the first pass (solo HUD batching, uniform cache) | 1360–1395 | 1150–1230 |
| With the draw list | 1410–1470 | 1285–1375 |
| HUD draws per frame, before the draw list | 89 (from the frame's draw count) | 138 |
| HUD draws per frame, now | 65 | 110 |
| Indoors (6d01, party HUD), now | 58 | |

The draw list changed two things: a HUD draw became cheaper (no program switch, no uniform, no vertex format
change between draws), and solid colours stopped breaking batches.

**The ceiling.** With the HUD's draws skipped altogether (a temporary switch) the frame got about 50 µs shorter,
1390 to 1500 FPS with the party HUD. So everything the HUD still draws costs about 7 % of this frame, at well
under a microsecond per draw, and the world's ~240 draws on the render thread set the frame time. The main thread
finishes about 150 µs before the render thread, so main-thread HUD time does not show in the FPS at all here.

The fullscreen screens were captured batched and unbatched (inventory, spellbook, map, history, quick reference,
rest, an inventory with RMB held): pixel-identical. The solo and party HUD captures match the ones taken before
the draw list except where the world moves behind translucent panels.

## Deliberately not built

Each would lower a number further. None is worth its cost while the ceiling above holds; the measurements that
would change that are named.

| Idea | Would save | Cost | Revisit when |
| --- | --- | --- | --- |
| Atlas pages for the small HUD images (frame pieces, buttons, plates, icons) | ~30 of 65 draws, ~20 µs | an atlas builder (decode cooked art, pad, pack), page memory, a redirection per image like the palette's | Android shows HUD draws costing several µs each (unmeasured) |
| A font's shadow and glyphs in one texture | 7 draws (party HUD), 17 (solo), ~5–10 µs | doubles the fonts' texture memory, or changes about 100 call sites that pass a font layer's texture | as above |
| Cached text layout | main-thread time only | a cache keyed by font, scale and string | the render thread stops being the limit |
| Widgets that keep their vertices while their state is unchanged | main-thread time only | every widget rewritten as state plus build; a verify mode | as above, and only then |
| The HUD rendered to a texture | nothing the draw list has not saved | premultiplied alpha throughout, a full-screen blend every frame, change detection underneath | not foreseen |

The palette redirection in `hudDrawTarget` is the place an image atlas would plug in: a texture handle maps to a
page and a UV rectangle when its primitive is added, and no caller changes.

## Files

| | |
| --- | --- |
| `game/ui/HudDrawList.{h,cpp}` | the list: vertices, indices, draw commands, merging |
| `game/ui/GameplayUiRuntime.cpp` | the HUD functions that fill it, `hudDrawTarget`, `flushHudDrawList`, the `[HudDraw]` log |
| `game/shaders/vs_hud.sc`, `fs_hud.sc` | the program (listed in `cmake/BgfxRuntime.cmake`) |
| `game/ui/HudReading.h` | bounded-age readings |
| `game/ui/GameplayObsidianPainter.h` | `Quads`, `addFill`, `addFrame`, `texts` for grouping |
| `game/app/GameApplication.cpp` | the flush before each `bgfx::frame`, the `avg_hud_draws` log fields |
| `game/outdoor/OutdoorRenderer.cpp`, `game/indoor/IndoorRenderer.cpp` | create and destroy the program |

`GameplayUiRuntime::submitWorldHudQuadBatch` (quads placed in the world, another view) still uses the two older
programs and is not part of the list. `IndoorRenderer::prepareHudView` and `submitHudTextureQuad` have no callers.
