# Hesper D4: Labor Pens — map 9112

## Pickups placement — 2026-10-24

Built and staged **12 serum vats and 17 Kreegan scrap bundles** from `PICKUPS.md`.
Guard Room supply racks: 6 (701–706); Sorting Pens guard post: 3 (707–709); Collar Control post: 3 (710–712).
Bundle density is round(2,168 faces × 8 / 1,000), clamped to 6–20. Positions and stable event IDs are in
`author_d04_blender.py` and `source/hes_d04.semantic.json:pickups`; bundles use 751–767.
The 2 former fixed floor-gold piles are removed; chest/boss rewards and themed supplies remain.
This supersedes the older floor-gold counts below.

The authored handler uses the shared `HesperPickups.setup`, with treasure level **5** explicitly:
`evt.GetCurrentMapName()` returns the display title, while the shared helper's default lookup expects a filename.
No shared mechanic or engine change is needed for these placements. The stage installs
`hes_d04_pickups.lua` for the colour and empty-model swaps. All pickups use the accepted existing models;
there are no new stand-ins.

Validation: zero compiler warnings; native checks of every pickup's event/cog, floor contact, wall/furniture
clearance and exclusion from boss rooms pass. Geometry, doors, lights, actors and chests match the pre-pass build.
[`d04_pickups.yml`](d04_pickups.yml) passes **86 steps**, clicking every pickup at its actual placement;
vat empty states also survive save/load. The shared test room covers the random loot/stat mechanic.
Evidence: [`review/pickups/`](review/pickups/).

Final regression: **93/93 scenarios PASS**; decoration-id and actor-size audits report zero mismatches.
Existing map scenarios: `d04_main_path` 66/66, `d04_key_path` 17/17.
The shared sweep and audit logs are in [`D4 review/pickups`](../hesper_d04/review/pickups/).

**Capture pending:** [`review_tour_pickups.yml`](review_tour_pickups.yml) has the storeroom and two bundle spots.
The sandbox cannot capture screenshots; the integrator captures and reviews the tour:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  ./tools/run_game.sh --isolated d04_pickups --world hesper --map hes_d04.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d04/review_tour_pickups.yml" --seconds 0
```

## Brightness A (2026-10-23)

Main rooms use ambient 10–12, transit spaces 14, and the Sump 18. Nine permanent fixtures were added,
including F_sump, bringing the plan to 30 lights. Every room has a fixture of radius 704 or 864.
Map-specific fixture variants preserve the shared lamps used elsewhere.

The authorised changes live in this map's zone-plan entries and its author scripts. All three maps' plan checks
peak at three overlapping lights; native readback confirms the new ambient and light values. These values supersede
the earlier lighting/count records below. Evidence is in `review/brightness_a/`; shared-regression results are in
P2's dated brightness A report.

Both D4 scenarios pass after restaging. The final shared regression passes all 71 scenarios.

**Capture pending:** this sandbox cannot capture screenshots. Use `review_tour_brightness.yml` with the existing
locked capture command to write `review/build03/`, then measure it with `hesper_stage/brightness.py`. The acceptance
target is a mean of at least 40, with no shot under 20 except documented darkness. Existing build02 captures remain
the measured baseline; no improved pixel brightness is claimed before the integrator re-captures.

Built from [D4 BUILD-READY](../../../design/kreegan_world/zone2/dungeons/D4_LABOR_PENS.md#21-build-ready),
`plans_zone2.py` and the shared Hesper indoor kit. The 2026-10-23 fixes follow P1's integrator answer and the
38-shot native review in `review/build01/`. Installs only through the stage.

## Build and test

From the repository root, regenerate the D4 lever models, author the map, compile, then stage:

```sh
flock -s output/hesper_stage/locks/stage.lock /snap/blender/current/blender --background --factory-startup \
  --python level_generation/projects/hesper_d04/author_standins_blender.py \
  --python-expr 'import sys,os;sys.stdout.flush();sys.stderr.flush();os._exit(0)'
flock -s output/hesper_stage/locks/stage.lock /snap/blender/current/blender --background --factory-startup \
  --python level_generation/projects/hesper_d04/author_d04_blender.py \
  --python-expr 'import sys,os;sys.stdout.flush();sys.stderr.flush();os._exit(0)'
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  python3 level_generation/projects/hesper_d04/build_d04.py
python3 level_generation/projects/hesper_d04/check_geometry.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
OPENYAMM_START_MINIMIZED=1 flock -s output/hesper_stage/locks/stage.lock \
  flock -s output/hesper_stage/locks/engine_build.lock bash -c \
  'cd output/hesper_stage/scenario_run && ../../../build/game/openyamm --world hesper --headless-run-scenario ../../../level_generation/projects/hesper_d04/d04_main_path.yml --scenario-no-color'
python3 level_generation/projects/hesper_d04/check_freed_save.py
```

Run `d04_key_path.yml` with the same scenario command for the no-Hacking route. Both are registered in
`hesper_stage/rebuild_all.sh --scenarios-only`; never run the full rebuild while other builders work.
The save checker takes the engine lock exclusively, compiles only its project-local C++ reader against the existing
engine libraries, and checks the real before/after saves using the game's save loader. It requires QBit 100027 and
all 31 Kept in groups 31, 40–45, visible before reload and Invisible afterward; a missing group or wrong bit fails.
No engine source or build target is changed. Run it after the main scenario, outside any shared engine lock.

The Snap launcher is blocked here; `/snap/blender/current/blender` works. If needed set `SDL_AUDIODRIVER=dummy`,
`ALSOFT_DRIVERS=null`, `XDG_CACHE_HOME=/tmp/d04-cache`. Check Blender logs for tracebacks even when the exit is zero.

## Native review handoff

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  ./tools/run_game.sh --isolated d04-fixes --world hesper --map hes_d04.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d04/review_tour_01.yml" --seconds 0
python3 level_generation/projects/hesper_d04/make_review_sheet.py
```

The 38-shot integrator tour now writes `review/build02/`; its sheet assembler accepts every shot in the tour.
Build01 is preserved. This sandbox cannot capture screenshots, so build02, the Sump's chest readability, the east
cell soffits and both lever poses still need the integrator's native review. No new screenshot or visual acceptance
is claimed. Tour positions are party feet, 160 below the design's eye heights.

## Accepted Ghulkat binding (2026-10-24)

The build now uses the shared registry's accepted `Overseer Ghulkat` binding from
`level_generation/creatures/hes_overseer_codex/integration/actors.yml`. It no longer generates the retired D5
stand-in or requires that old binding. Collision height remains 293. This supersedes the older stand-in notes below.

## Built and revised

All 15 rooms, 22 occupied sectors plus empty sector zero, 53 combat actors plus Tamsin/Ilse, six chests, two exact
gold piles, the cache, and eleven movers (51–61). Edit the author/build scripts and `source/hes_d04.handlers.lua`,
never generated Lua. The main scenario covers stairs, rescues, resting-group aggression, the collar flip, Ghulkat's
rewards, both lift rides, the Sump and save/reload. The key scenario takes the actual dropped key using indexed
world-item activation after the small key's live ray missed. Five level-200 Knights make the main path a mechanics
test; the key route uses one level-75 Knight. Neither establishes combat balance.

The review fixes move F_hall3 400 west to (2500, -300), derive Ghulkat from the D5 Overseer stand-in at 1.5×
render scale (about 297 tall versus Kept at most 175; collision height stays 293), raise Sump ambient from 27 to 20 (lower native values are brighter), and inset
two dark `hkfloor` drag streaks without overlapping the mud floor. The low east-cell soffits caused the dark wedges;
their rectangular openings are closed above and now have `hkrib` soffits/jambs. All three fronts stay open, with four
Miners immediately outside them. Native readback checks these surfaces and actor positions.

D4's new lever models retain the accepted 336 height, with bone handles at 192/128 above the floor, extending toward
the player inside L3's radius. Separate `d04_cell_lever_*` exports leave the other dungeon's `d04_lever_*` line-lever
models intact. Both new GLBs pass winding checks. Tamsin's leaf and Ilse's opaque cage say “Someone moves behind the
bars.” on hover; events 56/57 do not open the cages. The wording is handed to P4; rescue controls remain 72/73.

Bunk tops use `hkfloor`, sides `hkrib`/`hktrim`; the `hmslag` trough retains 1200 × 200 × 128 with a recessed basin.
Both lift platforms have 32-unit `hktrim` borders and unchanged 768 travel. The cache shelf is bone with a resin top.
The accepted rack height 384, flat restraint frame, 1000-long bank, and 32-unit return stair with rib risers remain.
Ghulkat still pays exactly 10,000 gold directly and now says “Ghulkat's belt purse: 10 000 gold.” His key and maul
remain ground drops. Every freed Kept group was already in event 1's hide list; the real save/reload check proves it.

## Integration and stand-ins

Event 50 reads `hesper_out2/out2_build.json` → `arrivals.d04_return`: currently (3456, -10138, 896), facing north.
Without that record it says exactly “The Pit Stairs' door: the way is not yet open.” D4's arrival remains
`d04_pit_stairs: [2900, 5400, 0]`, facing south. The Scour's registered exit scenario covers the outdoor round trip.

K5/K6 and resin/bone masters exist. Stand-ins remain: fixture lights/braziers, baggage-cart ore sledges, colonist
corpses, villager Kept/Tamsin/Ilse, the scaled D5 Overseer body and native item models. The lever is our simple resin
post with two bone-handle poses. Dedicated room/collar audio and surgery flicker await the accepted handoff.
Brightness A adds F_sump on the Sump north wall at (8414, -800, -1020), with ambient 18.
Final chest readability remains pending the integrator's capture.

## Validation record (2026-10-23 fixes)

The build has 2168 faces, 23 sectors, 58 portal faces, 11 movers, 7 authored lights and 29 decorations, with zero
compiler warnings. Native geometry readback, winding, final Lua hover registration and design audit pass (0 findings).
Both D4 scenarios (70 and 17 steps) and the real save visibility check pass. The two proof saves and readback log
are retained in `review/fixes_save_proof/`. Final staging succeeded and the staged map/events, both lever exports,
Ghulkat's scale/cast binding and the unchanged line-lever models were checked against their sources.
`rebuild_all.sh --scenarios-only` finished with **68 PASS, 3 FAIL, exit 1**: `crown_entrances` step 44 (D16 door
interaction), `brood_nest` step 4 (topic 9726 unavailable), `d13_main_path` step 85 (interaction hits ground).
The failed logs are retained in `review/fixes_regression_failures/`; D4 passed in the full suite too.
Detailed logs are `review/fixes_*.log`. The initial stage attempt stopped on the Scour's missing terrain source;
after that source appeared, the clean restage succeeded without a workaround in another map's files.
See P1's dated D4 fixes report for the integrator handoff.

## Walkability (2026-10-24)

Built, staged and gated. The staged audit is zero, with the two sorting trestles allowlisted as furniture.
The entry and balcony stairs use 16-unit risers; the balcony door opens onto its bottom landing.
Review fix (2026-10-24): the arrival stair's sloped roof now starts at z 128, the Pens opening's soffit, rising to
640 at the exit door. It started at -64, which left an open slot above the 640-high opening that rendered black from
the pit (tour shots 03 and 04). `check_geometry.py` asserts the roof meets the soffit.
The pit escape has a 26.6-degree lower ramp, an open middle-terrace landing and eight 16-unit upper steps,
with the floor removed below and solid parapets. The north trestle and its two heaps move south by 200.
Three hauling Drudges move to the entry's bottom landing. Both stair lamps and the entry ore sledge follow the actual treads.
Nine of 22 rooms are non-orthogonal and nine have sloped ceilings; Surgery is the signature octagonal room.
Door/event/cog IDs, actor and pickup order, chests and arrivals are unchanged.

`d04_walkability.yml` passes five pursuits (300 steps): entry stairs, the balcony's side doorway and flight,
and both pit levels. `d04_main_path`, `d04_key_path` and `d04_pickups` also pass.
Audit/survey evidence: `review/walkability/`; logs: `output/hesper_stage/logs/walkability_batch_d/`.
`review_tour_walkability.yml` covers the repaired floors and room shapes. The integrator captures it;
this sandbox cannot capture screenshots. No new art or stand-ins.

Final batch-D sweep: `rebuild_all.sh --scenarios-only` **108/108 PASS, exit 0**. Decoration and actor-size
mismatches: zero. All five batch maps' staged walkability audits are zero and all five are gated.
Logs: `output/hesper_stage/logs/scenarios_174417_3622123/`; batch summary:
`output/hesper_stage/logs/walkability_batch_d/validation_summary.json`.

### Hellhound kennels (2026-10-26)

R5-1 appends seven Kennel Hounds (10300): group 50 has three in the western Waste Shafts,
group 51 four in the eastern shafts. Both stand on the flat z=-1280 floor south of the slag
trenches, beside the existing Drudges; the chests, corpse props and lift mouths remain clear.
The original 55 actor records keep their indices, positions and roles. The build now emits
60 combat actors plus Tamsin and Ilse. Placement assertions check pack spacing.

The pursuit scenario clears the seven new defenders and checks the newly spawned actor at index 62;
its five routes and all original actor indices remain unchanged.

The runner now removes temporary scenario saves. To use `check_freed_save.py`, retain the main-path saves
by prefixing its headless command with
`OPENYAMM_SCENARIO_SAVE_DIR=/tmp/openyamm_scenario_saves/hesper_d04_main_path`.
