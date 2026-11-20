# Runtime integration handoff

Visuals are approved; this directory is **staged and unmounted**. The eleven layout files are concrete drafts in the
existing `UiLayoutManager` schema, retaining existing IDs and actions. They are not a claim that swapping YAML alone
implements the design. Rebase against `reference_layouts/` before integration; never overwrite newer live layouts blindly.

## Assets and packaging

`engine/` mirrors the intended shared base-content destination, `assets_dev/engine/`. New skin names start with
`obsidian_`; no legacy icon is overwritten. PNGs use straight alpha and lowercase names, mode 0644. The manifest records
dimensions, transparency, hashes, provenance and intended targets. Original PCs, dolls, equipment, NPC video, animated
hourglass/sky frames and live strings remain runtime content. The earlier Source fonts and vellum are excluded.

The six page skins contain background texture and static divisions only. Skills group underlines are deliberately
left to the renderer because their positions follow the live number of rows. Buttons are separate, label-free plates in
five states. Inventory's skin is exactly 936×692 pixels for a 468×346 logical page; its 64-pixel grid cadence represents
32 logical pixels. The grid element remains `(7,8,448,288)` under the page at `(0,24)`. Do not stretch that page texture
to a different logical rectangle or resize item footprints. The 1.875× review-to-native conversion is recorded in
`review_geometry.json`; review numbers and names are geometry fixtures, never game data or localization sources.

The shared frame retains original high-resolution alpha slices. Its surface is separate. Use the recipes in
`design/frame.yml`: fixed corners, repeating edges with clipped end tiles, and cropped grain at fixed density.
The whole transparent master and exact source crop coordinates are included for re-export. Dynamic windows must
not use the generic full-image stretch draw for either frame edges or the reading surface.

## Renderer changes required

| Owner | Required work |
| --- | --- |
| Gameplay font loading/settings | Reuse `Engine::loadTrueTypeFontAtlas` and the existing independent Fondamento descriptor, already called by `MenuScreenBase`. `GameplayHudCommon::loadHudFont` still follows legacy FNT lookup, so connect the existing path there; do not write a second atlas builder. The staged descriptor uses height 32 and baseline 25, with label scale = requested logical size / 32. Keep recreated MM faces in their original roles. See `design/font_registration.yml`. |
| `game/ui/UiLayoutManager.*` / shared drawing helpers | Current schema has asset states and text but no repeat/crop/nine-slice parameters or per-state text colours. Add a small shared frame/surface drawing path and button treatment, or explicitly implement these in existing shared UI rendering. `design/*.yml` are specifications, not unsupported layout keys. |
| `game/ui/GameplayPartyOverlayRenderer.cpp` | Wire the page skins, geometry and original dynamic fields; use semantic colour runs. Many values/positions/colours currently override YAML. Retain current/base formatting, actual award priorities and identification gates. Draw the name and class on one baseline, measuring the name before class placement. |
| Same, skills | Lucida 17 logical, pitch 14; eligible whole row blue, brighter on hover. Preserve point cost, mastery restrictions, row-click action and held-RMB inspect. No `+` controls. The 16px comparison is not the default. Group counts remain dynamic; do not freeze the sample skill list. |
| Same, rest | Three blocks are in the background. Preserve all five action rectangles; wire live labels and food-cost icon/count. Keep the sky/hourglass animation and clock/calendar logic. No standalone carried-food count. |
| Same, quick reference | Use the five added column regions and fourteen label rows, including Name, and the added Reputation/Fame fields; suppress the old hard-coded duplicate footer draw. Arrus 19 with bounded per-cell fit to 14 only for long cells; numeric HP/SP, no bars. |
| Same, inspectors | Use the shared frame and retain original inspector-specific font roles/layout/content. Title centred; Type/details preserved. Item Value and divider anchored below a separately scrollable body. Recompute edge bounds after final height. Keep monster square preview, effects, HP bar, main fields and all ten resistance rows. |
| `game/ui/GameplayDialogueRenderer.cpp` | Body-only dynamic sheet with open bottom. Measure Arrus 19→18, then Create 18→17 before bounded scrolling; preserve engine formatting and action conditions. No extra topic/speaker heading or Continue control. House title/NPC identity and the fixed video rectangle still belong to the sidebar. |
| `game/ui/GameplayHudRenderer.cpp` and shared party drawing | Apply the approved portrait selection/diamond, horizontal HP/SP treatment, plain coloured aggro diamonds and personal-buff medallion. New fullscreen `gameplay.yml` changes only shared basebar/empty-slot art; its other branches remain the existing reference. The full responsive gameplay HUD is still an implementation task using the separately approved r04 mockup. |
| Shared buff/input paths | Twenty-two uniform illustrations; four earliest expiries plus count overflow by default, optional two-row presentation. Keep duration and effect data live. Held RMB inspection closes on release outside the target or focus loss; no LMB inspect. Remove ordinary inventory hover overlay/footer, preserving explicit spell/item-targeting feedback. |

The full-screen portrait shift is **(+1.6,+2.666667) logical**, corresponding to the approved **(+3,+5) review pixels**.
PC names remain visible in the approved gameplay design; they are hidden in the focused fullscreen portrait view.
Numbering, extra ready text, skull/doll widgets, WARD/SIGHT labels and the horizontal selection strip are absent.
Preserve current portraits, party selection, followers, resources, books,
options, rest, minimap controls and combat-state functionality. HP/SP defaults to shaded static fill with short value
transitions; pulse was a comparison mode, not a requirement for constant animation. Consult the preserved r04 mockup
for responsive geometry rather than extending the 640×480 overlay coordinates across the viewport.

The draft preserves original gold/food resource bindings; splitting their combined legacy sprite into the approved
individual icons is a runtime wiring step. The draft's original equipment panel, magnifier, scroll controls and conditional
OK action remain live dependencies. Resolve those against the existing base asset packages; they are not replaced by
review screenshots. Adapt labels through the existing localization system instead of treating English drafts as final strings.

## Validation before installing

This handoff checks actual YAML parsing, unique/preserved IDs, staged references, dimensions, alpha, all 22 buff exports,
font files, exact inventory geometry, rest targets, layout/source hashes and absence of changes to live source layouts.
It does not claim game rendering or input integration has been tested. After runtime changes, check native screenshots
at representative UI scales, long/localized strings, 1/5 party members, all skill eligibility states, inspect release
outside/focus loss, long item footers, dynamic dialogue and ten monster resistances. Build only the normal game target;
no Vulkan build is needed for this work.

## Reproduce

From the repository root, with Node, Chrome, Python, Pillow and PyYAML available:

```sh
node level_generation/ui/obsidian_overlays_20260928/staging/export_graphics.mjs
python3 level_generation/ui/obsidian_overlays_20260928/staging/prepare_stage.py
python3 level_generation/ui/obsidian_overlays_20260928/staging/validate_stage.py
```

Chrome may need the already-authorized browser execution outside the filesystem sandbox. Export captures enclosing
pixel bounds and preparation only crops excess pixels; it never rescales the inventory. Preparation refuses a changed
source layout once pinned. Check source CSS hashes in the manifest before reproducing a historical approved version.
