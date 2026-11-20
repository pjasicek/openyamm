# Hesper D8: The Foundry (`hes_d08.blv`, map 9113)

## Walkability and room shapes — 2026-10-24

The pilot for `hesper_stage/check_walkability.py` and the kit's shapes (DUNGEON_PLAYBOOK, "The kit's shapes"),
against the user's play (`hesper_stage/review/user_play_20261024/user_65`-`70`). The map audits clean; its three
Fab Line A conveyor tops are allowlisted (`hesper_stage/walkability_allow.yml`).

- **Bridges (user_65):** the three smelting-floor bridges are flush gantry decks with rails, no longer 64-high boxes
  on 2-step flights of 32-deep treads. The channels' escape stairs (24-deep treads under 32 risers: monsters' 40-unit
  path steps skipped them) are 160 sloped banks (39°), lava like the beds; the Lancers stand on the decks (they stood
  inside the boxes).
- **Belts (user_66):** the belts start 192 further east so each railed stair climbs from open floor (its foot was
  against the wall, reached only from its sheer sides). The belt guards stand on belt 2 and in the gaps, the jam's
  Lancers in the gap north of belt 1 (four of them stood inside the belt boxes).
- **Forgemaster's Hall (user_67):** two railed ramps (cut into the floor) climb the raised west edge between the
  channels; its south flight (foot against the wall) is gone. The raised east edge is gone: the seal opens onto a
  floor-level grate plate (event 150) and a grate walkway the stoking never reaches leads to the Plate Stores (whose
  door opened behind a 128 edge). The channels end 400 short of the east wall behind a rail; valve E1 stands at the
  walkway's floor, E2 at y 12200 (it stood in the Plate Stores' doorway).
- **The jam (user_68-70):** the main belt's mouth lies at belt level (896; a 768 reveal left a 128 hole between the
  belt and Fab Line A's stair). The crates are belt-wide and drop into holes cut in belt 1's top, ending flush.
- **Found by the audit:** the Mould Shop's middle rack hung across the Arming Bay's door (32 of headroom: the whole
  back half was cut off for monsters); the Coolant Gallery's door opened half over the Plant Stair's top treads (the
  flight now ends at y 2680 on 42-deep treads); chest plinths are 32, not 64; pack spots clear channels, the pumps,
  Fab Line A's production row and Fab Line B's bench.
- **Shapes:** the Smelting Floor is a chamfered octagon (560) under a hipped tray ceiling springing at 1280; the
  Forgemaster's Hall a barrel vault from 768 to its 1024 crown; chamfered corners in the Slag Gate Hall, Coolant Plant,
  Mould Shop and Slag Niche; sloped ceilings over the four stairs. Survey (`research/room_shapes/survey.py`):
  non-orthogonal rooms 0 → 9 of 36, sloped or vaulted ceilings 0 → 12, walkable ramp area 0.5 % → 8.7 %.
- **Checks:** `d08_main_path` 98/98, `d08_hazards` 31/31 (its east-edge poses now stand on the walkway at z 0),
  `d08_pickups` 84/84, and the new [`d08_walkability.yml`](d08_walkability.yml): a Drudge spawned where the old
  geometry stopped monsters reaches the party at each spot (bridge, belt, west edge up its ramp, mouth over the
  lowered crates). Captures: [`review_tour_walkability.yml`](review_tour_walkability.yml) →
  [`review/walkability/`](review/walkability/contact_sheet.jpg).

## Pickups placement — 2026-10-24

Built and staged **10 serum vats and 20 Kreegan scrap bundles** from `PICKUPS.md`.
Arming Bay crew stores: 5 (701–705); Coolant Gallery: 3 (706–708); Coolant Plant: 2 (709–710).
Bundle density is round(3,668 faces × 8 / 1,000), clamped to 6–20. Positions and stable event IDs are in
`author_d08_blender.py` and `source/hes_d08.semantic.json:pickups`; bundles use 751–770.
The 3 former fixed floor-gold piles are removed; chest/boss rewards and themed supplies remain.
This supersedes the older floor-gold counts below.

The authored handler uses the shared `HesperPickups.setup`, with treasure level **6** explicitly:
`evt.GetCurrentMapName()` returns the display title, while the shared helper's default lookup expects a filename.
No shared mechanic or engine change is needed for these placements. The stage installs
`hes_d08_pickups.lua` for the colour and empty-model swaps. All pickups use the accepted existing models;
there are no new stand-ins.

Validation: zero compiler warnings; native checks of every pickup's event/cog, floor contact, wall/furniture
clearance and exclusion from boss rooms pass. Geometry, doors, lights, actors and chests match the pre-pass build.
[`d08_pickups.yml`](d08_pickups.yml) passes **84 steps**, clicking every pickup at its actual placement;
vat empty states also survive save/load. The shared test room covers the random loot/stat mechanic.
Evidence: [`review/pickups/`](review/pickups/).

Final regression: **93/93 scenarios PASS**; decoration-id and actor-size audits report zero mismatches.
Existing map scenarios: `d08_main_path` 98/98, `d08_hazards` 31/31.
The shared sweep and audit logs are in [`D4 review/pickups`](../hesper_d04/review/pickups/).

**Capture pending:** [`review_tour_pickups.yml`](review_tour_pickups.yml) has the storeroom and two bundle spots.
The sandbox cannot capture screenshots; the integrator captures and reviews the tour:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  ./tools/run_game.sh --isolated d08_pickups --world hesper --map hes_d08.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d08/review_tour_pickups.yml" --seconds 0
```

Built from the [BUILD-READY specification](../../../design/kreegan_world/zone2/dungeons/D8_FOUNDRY.md#21-build-ready)
and `plans_zone2.py:d8`, using D1/D2's shared indoor kit and D0's linear mechanisms.
All installation goes through `output/hesper_stage`; this project does not install into `assets_dev`.

## Status — 2026-10-23

Revised for the integrator's 2026-10-23 fix list, built and staged. Both local scenarios pass, including the
Scour round trip. Native visual acceptance remains with the integrator; this sandbox cannot capture the revision.

- 19 rooms, three levels, 36 occupied sectors plus empty sector 0; 3,668 faces, 37 portals, 16 movers, 72 actors,
  eight usable chests, two caches and three gold piles. Compilation reports zero warnings.
- All five channel beds use `hmchan` with the literal Lava bit, independently switchable cogs 180–184 and
  light groups 11–15. Seven valve wheels use D2's animated swap. Freeze lasts 20 seconds with the 17-second warning.
- Three diverters drop three crates and set 100451. Named map variables `d8.diverter1`–`3` preserve which partial
  switches were thrown; the design's count alone cannot do that. Save/load after the first switch is tested.
- Four stair flights, the three bridges, raised hall edges, presses, gantries, mould/rack walls, finishing bench,
  range gallery/cover/targets, pumps and slag pools are geometry. Fixtures supply 21 lights, plus 31 explicit lights;
  the revised floor/raised-surface check finds at most three overlapping lights at 32-unit sample spacing. All specified K6/K5 textures exist; none uses a texture stand-in.
- Landing 153 opens the seal and pauses stoking; entrance 150 resumes it. The hall telegraphs, burns for six seconds,
  then repeats every 30 seconds. The Forgemaster behavior is mounted through this project's `behaviors.yml`.
  Death sets 100450, drops the Hammer/Core at the design position and opens Plate Stores. Fixed chest contents,
  Work Order text and autonotes 10130–10132 are installed.

## Review fixes — 2026-10-23

- Both spellcasters, 10040 and 10110, bind `cast: Carbine_Attack`; the clip exists in the installed GLB.
  The Forgemaster has descriptor/actor height **327** and a map-owned Trooper C binding at **1.5 scale** in
  `source/actor_standins.yml`. Descriptor height alone does not enlarge the rendered model.
- Fixed chests A/B/C stand on 320 × 320 × 64 plinths in open floor space: `(8764,6428,832)`,
  `(8764,7892,832)` and `(7764,11764,64)`. A clears the presses; B/C clear the racks. Their existing graft lights
  move to the east walls, about **358 units** from each chest origin. Native chest-open and contents checks pass.
- All four main flights use `hmplate` treads and `hmgantry` risers. The three Smelting Floor bridges and their
  approach steps use the dark `hmgantry` lattice on top, removing `hmgrate`'s painted molten gaps.
- All five furnace eyes are **384 × 256 ports recessed 32 units**, faced `hmglow` with `hmgantry` reveals/sills.
  Their original 768-radius lights sit at the ports; the wall-lamp stand-ins were removed from those five spots.
- Belt rooms and the Coolant Gallery are six ambient levels brighter: fab lines/Range 16, Maze/Coolant 17,
  Mould Shop/Arming Bay 18. Seven valve lamps, three diverter lamps and the console lamp provide local control light.
  A lit `hmglow` lip sits under the inner blast shutter. The channels retain their original switchable lights.
- The jam keeps its centres and mover travel, with **168-wide bodies and 32-unit gaps**; each crate has an ore-glow
  face/top lit by L2. The accepted 448-high pumps and 320-east belt-guard shift remain.
- Event 50 uses “Beyond the Slag Gate the way is not yet open.” when the outdoor record is missing. The record
  now exists, so the compiled event travels to the Scour's actual arrival instead.

The original design files were not changed. `review/fixes_checks.json` records the approved placement/lighting
adjustments; the author script checks the revised light overlap and each fixed chest's light distance.

## Build and run

Run from the repository root, with the existing development compiler and game binary:

```sh
(cd level_generation/projects/hesper_d08 && blender --background --factory-startup --python-exit-code 1 --python author_d08_blender.py)
flock -s output/hesper_stage/locks/engine_build.lock \
  flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d08/build_d08.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
flock -s output/hesper_stage/locks/engine_build.lock \
  level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

`source/` contains the Blender scene, GLB, geometry/doors metadata, semantic record and authored handlers.
`build_d08.py` uses `blv_build.build`, writes the scene/Lua/runtime package and `d08_build.json`.
Edit `source/hes_d08.handlers.lua`, never its generated runtime copy.

The Scour must read `source/hes_d08.semantic.json:arrivals.d08_slag_gate` (4900, 300, 0; north).
D8 reads `hesper_out2/out2_build.json:arrivals.d08_return`. The main-path scenario exits to that arrival, walks
back within reach of outdoor event 53, re-enters D8 and confirms the jam/boss flags and Plate Stores seal persist.
Only D8 was rebuilt for this revision; the outdoor arrival contract is unchanged.

```sh
flock -s output/hesper_stage/locks/engine_build.lock \
  flock -s output/hesper_stage/locks/stage.lock env OPENYAMM_START_MINIMIZED=1 bash -c '
  cd output/hesper_stage/scenario_run &&
  ../../../build/game/openyamm --world hesper --headless-run-scenario \
    ../../../level_generation/projects/hesper_d08/d08_main_path.yml --scenario-no-color'
```

Run `d08_hazards.yml` the same way. Both are registered in `rebuild_all.sh`.

```sh
flock -s output/hesper_stage/locks/engine_build.lock \
  flock -s output/hesper_stage/locks/stage.lock ./tools/run_game.sh --isolated hesper_d08_review \
  --world hesper --map hes_d08.blv --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d08/review_tour_02.yml" --seconds 0
```

`review_tour_02.yml` preserves the integrator's 45-shot coverage with updated A/B/C chest viewpoints and writes
`review/build02/`. Positions are party-foot coordinates. `review_tour_01.yml` and the original native sheet remain
unchanged. The integrator captures the revised tour and assembles its sheet; the old twelve-shot assembler is not
used for this tour. All game runs remain minimized.

## Validation and review

- [Main path](review/fixes_d08_main_path.log): 98 steps pass, including actual movement over the bridge, up the Belt Stair,
  through the cleared jam and Fab/Range doors, down the Hall Stair and across the seal; three diverters, partial
  save/load, fixed chests, Sentinel stand-down, pause/resume, boss death, drops, held Emitter and the native Scour exit/return.
  The test clears the belt guards with `damage_actor` to prevent their interaction targets intercepting lever clicks.
  Its high-level party and geometry-only traversal segments test mechanics, not combat balance.
- [Hazards](review/fixes_d08_hazards.log): 31 steps pass. A lit bed deals exactly 504/5040 HP per second; freezing stops it
  and expiration restores it. During stoking a raised edge preserves full HP, the central floor burns, and a frozen
  hall channel remains safe. AI is disabled during exposure to isolate surface damage; the map timers still run.
- Plan ceiling/light checks pass; [design audit](review/fixes_design_audit.log) reports zero findings.
- [`rebuild_all.sh --scenarios-only`](review/fixes_regression.log): **53 pass, one unrelated gating failure,
  one known WIP failure; exit 1**. `hesper_out4/crown_entrances` step 15 expects to remain on the Crown after clicking
  D7's door, but the newly connected door enters `hes_d07.blv`. D5's `relay_spire_climb` is the existing non-gating
  WIP failure. Both failure logs are preserved as `review/fixes_regression_*.log`; neither project/test was edited.
  D8 and `scour_exits` pass. No full shared rebuild was run for these fixes.
- [Binding checks](review/fixes_binding_checks.json): both cast clips exist in the staged GLB; the Forgemaster's
  actor height is 327 and his rendered binding scale is 1.5 times the Noble's. D8's runtime matches the stage.
- **Revised native captures were skipped as requested:** the sandbox has no working desktop renderer.
  The existing [native build01 sheet](review/build01/sheet.jpg) is the integrator's pre-fix review, inspected for
  this work. New lighting, chest readability, Wizard Eye/automap and desktop-load acceptance await the integrator.
- The [Blender geometry preview](review/blender01/sheet.jpg) is archived pre-revision evidence: twelve CPU renders without
  native lighting, actors, decoration models, HUD or culling. It caught target/door and camera-placement conflicts.
  Recreate with `blender --background --factory-startup --python level_generation/projects/hesper_d08/preview_blender.py`,
  then run `make_contact_sheet.py` on `review/blender01`.

In this sandbox the Snap Blender launcher exits immediately, and the direct Blender executable hangs in audio
shutdown after saving. The recorded build used `/snap/blender/current/blender` with an appended Python expression
that flushes output and calls `os._exit(0)` after the author script. Export/save success and compile checks were
verified; `rebuild_all.sh` also rejects Blender tracebacks. This is an environment workaround, not a project dependency.

## Stand-ins and integrator decisions

| Requested asset | Current staged stand-in |
|---|---|
| Sooted valves | D2 body/wheel and turned variants; existing 90-degree `turn_in`, without a new soot skin |
| Diverter levers | D2 valve body/open body; functional swap, no lever animation |
| Vent glow / graft light | Existing amber/white colony wall lights; design radii and colors retained |
| Fire bowl | Existing brazier; its unused off variant shares the body |
| Ore sledge / slag heap / armour plate | Baggage cart / salvage heap / fallen plates |
| Drudges, Lancers, Nobles, Forgemaster | Existing Hesper Trooper B/C/A/B/C/C bindings, with the design gameplay rows |
| Heavy Sentinel | Existing Ward Turret model with the Sentinel row and traverse tactic |
| New fixed-item ground art | Existing `7item065`, `item134`, `item100`, `item104`, `item073`, `scroll2`; Hesper inventory icons |

The Forgemaster now uses a 1.5-scale Trooper; his armored maul/apron body is still missing.
Press/belt/heat loops, steam hiss, boss roar, secret knock and steam particles are not supplied. No new audio or
decoration models were fabricated. Native H3 item pools and 80% salvage are not wired by the existing indoor helper:
the five random containers currently use native T6 treasure and 9,000 gold, explicitly marked as a shortcut in code.

The plan lacks exact furnishing coordinates. Placement was derived from the room descriptions and was accepted by the integrator, with the fixes above: the Fab A row sits 300 units south of its centre to keep the route clear; press beds sit beside
the bridge exits; targets occupy wall intervals outside the doors; the finishing bench faces the north mould wall.
The pump specification is 640 high under a 512 ceiling: stacks were compressed to 448, retaining their 600-wide base.
The group-29 marker coincides with diverter 2, so its four guards are shifted 320 east, keeping their corpses clear of
the lever. Channel and raised-edge steps were added at 32-unit rises so their specified height changes are walkable.

Remaining integration: re-capture the revised tour and approve its chest/step/control readability; supply the
missing Foundry art/audio and H3 pool integration; review Wizard Eye and the automap on an accessible display.
No engine code, Vulkan build, performance run or `assets_dev` write was made by this build. Concurrent unrelated
settings and MM6 event edits changed the workspace's pre-existing `assets_dev` diff during the session; they were
left untouched. The staging area was not changed.

## Brightness B — 2026-10-23

Rebuilt and staged with zero warnings; **main path 98/98 and hazards 31/31 PASS**. Ambient is 10 in the
Smelting Floor/Hall, 12 in main rooms, 14 in Coolant/Sump/Niche and 15 on the stairs. Map-only fixtures use
704-radius graft/vent lights, 864-radius bowls and 1,024-radius furnace ports. Added fixtures in Smelting,
Sump and Niche give every room a ≥640-radius source; channels and control glows keep their switchable values.
**55 lights; maximum overlap 3**, including raised surfaces sampled every 32 units. Shared fixture values and
all mechanics are preserved. Evidence: `review/brightness_b/`.

Author and build scripts must hold `flock -s output/hesper_stage/locks/stage.lock`; game runs also hold the
shared engine lock. Before this pass: mean **27.5**, darkest **9.6**. No new screenshots; integrator re-measurement
must establish the ≥40 mean and ≥20 ordinary-shot target.
