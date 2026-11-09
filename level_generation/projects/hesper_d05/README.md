# Hesper D5: Relay Spire (`hes_d05.blv`, map 9121)

## Walkability and room shapes — 2026-10-24

Desktop review follow-up (2026-10-24, item 4): the original Root landing camera is valid. The open stair
well now owns its upper shell and has vertical side portals into the gallery, replacing the floor-height
portal that culled the view. Geometry checks confirm the same pose sees a ceiling and the gallery portal.
The map was restaged under the exclusive lock; its audit and all map scenarios pass. Tour poses are unchanged.
Evidence: `review/walkability/desktop_fix/`; logs: `output/hesper_stage/logs/walkability_review_c_20261024/`.
Native recapture is blocked by this sandbox’s “SDL_Init failed: No available video device”; desktop visual
confirmation remains with the integrator. The full shared sweep below predates this focused follow-up.

The Root Stair, Storm Ledge and Storm Stair now have 64 risers of 16. The Storm Stair uses 20.75-deep treads,
ending at y4464 before its upper doorway. Flat door landings and sloped ceilings keep the existing route. The Root well opens at y1760,
with its east exit level at y2400–2686 and a 45-degree parapet return into the Gallery. Both lifts have matching floor apertures, preserved doorway-reveal floors,
and glow strips below the upper lip. Each lift well and its two landings form one connected sector, so a carried
actor retains its route to the upper floor. The short Cradle stair has side rails and a floor cut beneath it.

The coolant workers, Heart tenders, Barracks guards and Loom pack stand on clear floor. Their actor indices,
monster IDs and groups are unchanged. All 20 pickup positions and their events/cogs remain unchanged.
Vhorrax's glyph plate (event 14) moves along the north wall to (1950,4700); the two eastern perches move 50 west.

The chamfered, domed Crown is the signature hall. Outer corners are clipped without changing internal sector
splits or doorway positions; five rooms gain hipped ceilings. The native survey records 30/38 non-orthogonal
rooms, 89% axis-aligned wall area and 12 sloped ceilings (before: 7/40, 95%, 4).
The author checks event faces, movers, fixtures and pickup markers against every new diagonal wall.
No kit changes or new stand-ins.

Validation evidence lives in `review/walkability/`: local and staged audits both have zero findings, with no
allow-list entries. The staged payload matches the runtime byte for byte. `relay_spire_climb` (74 steps),
`d05_pickups` (44 steps) and `d05_walkability` (216 steps, 13 fights) pass on the shared stage. The fights cover the
flights, Root exit, both lift rides and exits, Cradle approach and cleared actor spots. D5 is in `WALKABILITY_GATED`.
`review_tour_walkability.yml` is ready for the integrator; this sandbox cannot capture the desktop.
This section supersedes the older stair and room-shape descriptions below.

Final shared regression: `rebuild_all.sh --scenarios-only` passes **103/103** (exit 0). Actor-size and
decoration-ID audits have zero mismatches; the design audit has zero findings. Logs:
`output/hesper_stage/logs/scenarios_141329_8/`; batch summary:
`output/hesper_stage/logs/walkability_batch_c_20261024/validation_summary.json`.

## Pickups placement — 2026-10-24

Built and staged **0 serum vats and 20 Kreegan scrap bundles** from `PICKUPS.md`.
No stat containers. The Armoury is the review tour's storeroom; bundles span the roots and Rings 1–3, below the boss's Crown.
Bundle density is round(6,414 faces × 8 / 1,000), clamped to 6–20. Positions and stable event IDs are in
`author_d05_blender.py` and `source/hes_d05.semantic.json:pickups`; bundles use 751–770.
The 3 former fixed floor-gold piles are removed; chest/boss rewards and themed supplies remain.
This supersedes the older floor-gold counts below.

The authored handler uses the shared `HesperPickups.setup`, with treasure level **5** explicitly:
`evt.GetCurrentMapName()` returns the display title, while the shared helper's default lookup expects a filename.
No shared mechanic or engine change is needed for these placements. The stage installs
`hes_d05_pickups.lua` for the colour and empty-model swaps. All pickups use the accepted existing models;
there are no new stand-ins.

Validation: zero compiler warnings; native checks of every pickup's event/cog, floor contact, wall/furniture
clearance and exclusion from boss rooms pass. Geometry, doors, lights, actors and chests match the pre-pass build.
[`d05_pickups.yml`](d05_pickups.yml) passes **44 steps**, clicking every pickup at its actual placement;
vat empty states also survive save/load. The shared test room covers the random loot/stat mechanic.
Evidence: [`review/pickups/`](review/pickups/).

Final regression: **93/93 scenarios PASS**; decoration-id and actor-size audits report zero mismatches.
Existing map scenarios: `relay_spire_climb` 74/74.
The shared sweep and audit logs are in [`D4 review/pickups`](../hesper_d04/review/pickups/).

**Capture pending:** [`review_tour_pickups.yml`](review_tour_pickups.yml) has the storeroom and two bundle spots.
The sandbox cannot capture screenshots; the integrator captures and reviews the tour:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  ./tools/run_game.sh --isolated d05_pickups --world hesper --map hes_d05.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d05/review_tour_pickups.yml" --seconds 0
```

## Brightness A (2026-10-23)

Main rooms use ambient 10–12 and all transit/connector sectors 14. Eighteen permanent route fixtures
bring the plan to 59 lights; fixture radii are 704/864. The six 900-radius timed shaft pulses are unchanged.
The cradle stalk and its pod shell use K8 `hsrib`/`hsfloor` instead of the teal bone/chitin pair.

The authorised changes live in this map's zone-plan entries and its author scripts. All three maps' plan checks
peak at three overlapping lights; native readback confirms the new ambient and light values. These values supersede
the earlier lighting/count records below. Evidence is in `review/brightness_a/`; shared-regression results are in
P2's dated brightness A report.

The climb scenario and the outdoor round-trip scenario pass after restaging. The final shared regression passes all 71 scenarios.

**Capture pending:** this sandbox cannot capture screenshots. Use `review_tour_brightness.yml` with the existing
locked capture command to write `review/build03/`, then measure it with `hesper_stage/brightness.py`. The acceptance
target is a mean of at least 40, with no shot under 20 except documented darkness. Existing build02 captures remain
the measured baseline; no improved pixel brightness is claimed before the integrator re-captures.

Revised and staged on 2026-10-23 to the [P2 integrator rulings](../../../design/kreegan_world/WORK_PACKAGES/requests/P2.md#integrator-answer-to-the-d5-builder-2026-10-23).
The 74-step `relay_spire_climb.yml` passes three consecutive runs. Native visual approval remains with the integrator.
The design is read through `plan.py`; brightness A changes only D5's authorised plan ambient/light values.
The shared geometry kit is unchanged.

## Build and test

From the repository root:

```sh
flock -s output/hesper_stage/locks/stage.lock blender --background --factory-startup \
  --python level_generation/projects/hesper_d05/author_d05_blender.py
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  python3 level_generation/projects/hesper_d05/build_d05.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  bash -c 'cd output/hesper_stage/scenario_run && OPENYAMM_START_MINIMIZED=1 ../../../build/game/openyamm --world hesper --headless-run-scenario ../../../level_generation/projects/hesper_d05/relay_spire_climb.yml --scenario-no-color'
bash level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

The regression script takes both shared locks for every minimized game run. Never run its full rebuild while other
builders work. No engine build is needed; any future engine/tool build must hold the engine lock exclusively.
The snap launcher cannot start in this sandbox. This session used `/snap/blender/current/blender -noaudio` with
`--python-exit-code 1` and a final flush/exit expression to avoid its shutdown hang. Blender's thumbnail-cache
permission warning does not affect the exported map.

## Implemented fixes

- All three main flights have 32 treads of 32 units. Root treads are 62.5 deep; the first fourteen have 448 headroom.
  Vertical `hkceil` faces close the stepped ceilings. The Root doorway's floor through the 64-thick wall is retained
  when replacing the flat stair floor; an actual entry walk found and now covers this missing-floor defect.
- Storm Ledge landings are y3000–3450 at z1024 and y4800–5400 at z2048. Storm Stair landings are y2800–3200 at z3072
  and y4400–5200 at z4096. Doors 210/211/219/220, the cache and group 19 keep their positions.
- The 300 × 300 × 256 bone cradle stands at (3200,5500), with its chitin top and chest C at z4480. The floor fallback
  was unnecessary. Its short +128 approach also has 32-unit treads. Chest C is clicked from (3200,5250,4224).
- Lift 54, its cuts and shaft are centred at (1700,3200); plates 73/74 are beside it at (1444,3450)/(1444,2950).
  Lift 53 stays at (1300,3200). Two separate connector sectors contain the shafts between the landing ceilings and
  upper floors, keeping each landing within its own room. Glow strips mark the lift heads.
- Armoury racks are 1200 × 200 × 448 with bone frames and grafted backs; the master loom is 1000 × 300 × 448;
  targets are 576 high and spools 448. The north-wall loom console is 400 × 200 × 576, centred at x3300; its middle
  window is shifted 600 east. The accepted eight 480-wide bunks remain; four posts move inward beneath their ledges
  to clear the two fire bowls. Light positions, radii and colours are unchanged.
- Pulse P1–P3 explicitly belong to the lower shaft sector and P4–P6 to the upper sector. The compiler output is
  checked for these assignments, groups 21–26, radius 900 and RGB (120,230,255). The existing west/east `hkglow`
  strips at 448 above each shaft floor are retained. Visible pulse progression still needs the integrator's capture.
- Chest pods have local faceted resin shells (radius 110, height 144) using their existing chest events, making the
  small shared models readable. No shared decoration model was altered.
- Vhorrax stands at (4500,4000,4096). His native ranged AI retains its cadence; the eight-second pulse is an effect
  only and no longer interrupts attacks with a fidget. No `castNext`, lowest-health targeting or flying stand-in.
  Group 8 is awake and posted. Actor sector ids now match the compiler's alphabetical room ordering.

Accepted workarounds remain: click-only membranes, the clipped Root foot opening, waist-high shaft parapets, the
coarse ribbed dome, primitive nest cups/ring, and H2 pods using native tier 4 plus 4000 gold. Vhorrax's winged body,
saber, landing/departure animation and charge tone remain art/audio work; no engine workaround was added.

## Validation and exit contract

The native map has 6414 faces, 4592 vertices, 44 occupied sectors plus sector zero, 128 portal faces, 24 movers,
69 actors in 21 groups, eight chests and six ground objects. All 44 interaction ids bind. The 41 planned lights are
28 fixtures plus 13 BLV lights. Compile: **zero warnings**; plan checks pass; design audit: **zero findings**.
Evidence is under [`review/fixes01/`](review/fixes01/).

`relay_spire_climb.yml` walks into and up the Root Stair and up both storm flights, operates the lifts and main doors,
checks Hacking refusal, defeats Vhorrax, opens the seal, collects the real Jammer, and completes Aster's M7 hand-in
(QBit 100007 set, 100207 cleared) before exercising the repaired ring. It no longer grants the completion QBit as a
shortcut. Three consecutive runs pass all 74 steps; D5 has been removed from `WIP_SCENARIOS`.

`rebuild_all.sh --scenarios-only`: **67 PASS, 4 FAIL, no WIP**, exit 1. D5 passes. Logs:
`output/hesper_stage/logs/scenarios_153907_4/`, summary `review/fixes01/regression_retry.log`.
The remaining failures are outside D5:

| Scenario | Failure |
|---|---|
| `crown_entrances` | Step 44 picks the distant D16 blast door instead of activating the intended exit |
| `crown_edges` | Step 6 records no Crown-to-Brood-Spire transition |
| `brood_round_trips` | Step 16 remains in the Crown on its return edge, before reaching D5 |
| `d12_round_trips` | Step 11 picks the same distant D16 blast door |

The isolated D5 section of the outdoor round trip passes **9/9** on the current binary; its fixture and log are
`review/fixes01/d05_round_trip.{yml,log}`. The first full suite encountered 20 process-launch permission errors
while the binary changed; a second run held the shared engine lock throughout and completed without those errors.
One stage attempt encountered a temporarily absent Scour terrain source; the file returned and staging succeeded.
No other builder's sources were changed to work around either issue.

The Brood Spires build record now exists. `build_d05.py` continues to read `arrivals.d05_root_door.position` and
`direction_degrees`; the working exit is preserved. Its missing-record message is exactly
“The blast door: the way is not yet open.” The requested local scenario ends asserting `hes_d05.blv` without
activating the outdoor exit; `hesper_out3/brood_round_trips.yml` covers event 50 and the return. This supersedes the
ruling's obsolete assumption that Brood Spires is absent, without breaking its now-built connection.

## Stand-ins and review

All K5 texture masters exist; no texture substitutions were needed. Existing stage stand-ins remain:

| Missing art | Stand-in |
|---|---|
| K5 vent/graft lights and fire bowls | Amber/white wall lights and brazier, exact planned light specifications |
| Overseer | Bare Hesper Kreegan with its cast clip; no wings |
| Vhorrax | Gilded Trooper at 1.4 scale, carbine instead of saber |
| Drudge/Lancer caste art | Existing native Drudge and Trooper-derived Lancer bindings |
| D5 item models | Stage aliases raygun2, 7item024, item048, gem5 and amulet4 |

The integrator's 43-shot `review_tour_01.yml` and `review/build01/sheet.jpg` are preserved. Updated cameras are in
`review_tour_02.yml`; `make_sheet.py` targets the complete new tour. The integrator can capture with:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  ./tools/run_game.sh --isolated d05-fixes --world hesper --map hes_d05.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d05/review_tour_02.yml" --seconds 0
python3 level_generation/projects/hesper_d05/make_sheet.py
```

**No screenshots were captured: this sandbox cannot capture them.** Cyan pulse visibility, bowl/post brightness,
pod appearance, Wizard Eye/automap and native desktop rendering remain the integrator's checks. Headless checks do
not establish visual approval or continuous player-controlled lift riding. No Vulkan, performance runs, engine
changes, `assets_dev` writes or git staging were used.
