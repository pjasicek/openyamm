# Hesper D11: The Seedship

Map **9123**, `hes_d11.blv`, from the [BUILD-READY handoff](../../../design/kreegan_world/zone3/dungeons/D11_SEEDSHIP.md)
and `plans_zone3.py`, using the shared `blv_kit.py` and `blv_build.py` pipeline.

Built: all three decks, 52 occupied sectors plus empty sector 0, the six-volume brain cathedral and open gangway,
Noble quarters, trophies, cradles, sensorium, duelling ring and Seed Vault. There are 27 native movers, 68
lights (52 from the plan and 16 spine nerve fixtures added by the integrator’s fix list), 81 initial actors
(two hidden Vhorrax forms represent one boss), seven native chests, two event caches and 8 themed ground items. Events cover spores and both sealed helms, four ganglia and their hatchlings, persistent sabotage,
brain/nerve shutdown, both terms, the refused reinforcements, once-only rewards, journals, membranes and return hatch.

## Build and stage

From the repository root:

```sh
(cd level_generation/projects/hesper_d11 && flock -s ../../../output/hesper_stage/locks/stage.lock \
    timeout 1800 blender --background --factory-startup --python-exit-code 1 --python author_d11_blender.py \
    --python-expr 'import os,sys;sys.stdout.flush();sys.stderr.flush();os._exit(0)')
flock -s output/hesper_stage/locks/engine_build.lock \
    flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d11/build_d11.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
```

The author exports the Blender/GLB sources, geometry and semantic records. The compiler verifies native event
bindings, movers and lights, creates the scene and Lua, and assembles `runtime/worlds/hesper/` for the stage.
`behaviors.yml` adds the three map-owned behaviours; `sound_cues.py` generates seven original temporary PCM cues.
No engine build or lighting bake was needed. No files were installed into `assets_dev`.

On this sandbox the Snap launcher is unavailable. Validation used `/snap/blender/current/blender` directly with `-noaudio`, `--python-exit-code 1` and a flushed Python process exit after export to avoid the
sandbox's audio shutdown hang. This is an environment workaround, not an author-script dependency.

The outdoor builder reads `source/hes_d11.semantic.json` → `arrivals.from_hes_out3`. This build reads
`hesper_out3/out3_build.json` → `arrivals.d11_breach` (`position`, `direction_degrees`). The Brood Spires build
now supplies that record. Event 50 exits to the gantry; the scenario confirms the transition, returns through
outdoor event 52 and checks that sabotage, the honoured duel and the open reward door persist.

## Test and review

```sh
(cd output/hesper_stage/scenario_run && flock -s ../locks/stage.lock \
    flock -s ../locks/engine_build.lock env OPENYAMM_START_MINIMIZED=1 ../../../build/game/openyamm \
    --world hesper --headless-run-scenario ../../../level_generation/projects/hesper_d11/seedship_sabotage.yml \
    --scenario-no-color)
python3 level_generation/projects/hesper_d11/check_scripts.py
python3 level_generation/projects/hesper_d11/verify_saved_state.py
flock -s output/hesper_stage/locks/engine_build.lock \
    level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only

flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
    ./tools/run_game.sh --isolated d11 --world hesper --map hes_d11.blv \
    --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d11/review_tour_01.yml" --seconds 0
```

All game runs stay minimized. The main tour keeps eleven live-ship shots; poses 02, 03, 05 and 10 now stand in
clear space in the fitted rooms. Names contain only letters, digits and underscores. The build validates both tours
without overwriting their reviewed poses. Shots 07 and 08 and the approved rooms remain unchanged.
Both tours target `review/build02/`; the integrator's original `review/build01/sheet.jpg` is preserved.

`verify_saved_state.py` checks the scenario's sabotaged snapshot and copies it to **`review/hes_d11_blind.oysav`**.
Use that save for shot 12, at the same pose as live-brain shot 05:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
    ./tools/run_game.sh --isolated d11_blind --world hesper \
    --save "$PWD/level_generation/projects/hesper_d11/review/hes_d11_blind.oysav" \
    --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d11/review_tour_blind.yml" --seconds 0
```

**No new screenshots were captured: this sandbox cannot capture them.** The integrator captures both tours;
visual acceptance, Wizard Eye Master/automap and desktop reward presentation remain for that review.

## Fixes and validation (2026-10-23)

Applied the integrator's D11 fix list in `WORK_PACKAGES/requests/P2.md`:

- Arrival and both Rib Corridors use `hsfloor` floors, a bounded truss/rib wall band, bone trim and dark membrane
  above and below the band and on the ceiling. The arrival event stays on its retextured floor.
- Both Spine Galleries have eleven bone arches, normally 512 apart; the Core's seal has a wider clear bay.
  Six existing spine lamps retain their positions, with sixteen added `hes_nerve_node` fixtures between ribs.
  They use the existing radius/colour and groups 21/22, so sabotage extinguishes them with the ship's other nerves.
- The four obstructed tour poses are corrected and the blind save is supplied as described above.

Compiler: **zero warnings**, 6,986 faces, 5,166 vertices, 53 sectors, 210 portal triangles, 27 movers,
12 standalone lights and 62 decorations (46 light fixtures). Maximum nonportal faces per sector: **264**.
Native texture/readback checks pass; the four revised camera rays have **2,003–2,313 units** of unobstructed
forward space. See `review/fixes_build.log` and `review/fixes_geometry_checks.json`.
The updated light plan samples at most **2 lights** on any room-floor point (`review/plan_checks.json`).
The design audit has **0 findings** (`review/fixes_design_audit.txt`).

**`seedship_sabotage.yml`: 132/132 steps pass.** Staging, Lua self-checks and native saved-state checks pass.
Evidence: `review/fixes_scenario.log`, `review/fixes_stage.log`, `review/fixes_scripts.log` and
`review/fixes_saved_state.log`.

**`rebuild_all.sh --scenarios-only`: exit 1, 66 PASS, 4 FAIL, 1 declared WIP-FAIL.** D11 passes in the shared
run too. The failures are outside this revision:

- D15 `d15_side_paths`, step 43: interaction hits an unbound face.
- Scour `scour_edges`, step 22: expects source 1 / Scour; receives source 0 / Crown.
- Shared `tech_skills_landfall`, step 6: no active dialogue when selecting the house service.
- Shared `talk_topics`, step 4: NPC 9001 has zero dialogue actions instead of four.
- D5 `relay_spire_climb`, step 3: movement drift; explicitly WIP and non-gating.

See `review/fixes_rebuild_scenarios.log`, `review/fixes_regression_summary.json` and the copied
`review/fixes_<scenario>.log` failure logs (`fixes_d05_wip.log` for D5). No other map or shared entry was
edited to work around those failures. The full shared rebuild was not run.

The scenario covers sealed/unsealed spores, each ganglion's four-hatchling burst, saved sabotage, the ramp and stairs,
both duel answers, refused adds, rewards, the vault/hatch and the Brood Spires exit/return. Lua self-checks cover the
chosen boss's timers, saved door countdowns, once-only rewards and summon caps. Native save checks cover all four
light states, `hsbraind`, nerve shutdown, the blind-tour snapshot and the hatch arrival at `(600,600,0)`.
`evt.GiveItem` reward assertions count the native pending-delivery queue. The high-health fixture party tests
mechanics and collision; it does not establish combat balance.

## Stand-ins and integration decisions

| Requirement | Current build / reason |
|---|---|
| Nerve nodes and collapsed state | Existing colony wall-light/on-off models, radius 0; exact planned light radius 512 and colour retained. |
| Gilded fire bowls | Existing brazier, radius 0; planned light radius 640 and colour retained. The greybox uses its shared shape, not a new gilded model. |
| Trophy relics / bones | Existing salvage heap / skull-and-ribs models, radius 0; final props absent. |
| Ganglia and egg clusters | Native `3egg` sprite bindings; a scaled egg stands in for each ganglion on its 200-high plinth. Final magenta ganglion art is absent. |
| Nobles / Vhorrax | Existing Trooper C body and D5's existing enlarged Vhorrax binding. IDs 10041 and 10106 map `cast` to the installed `Carbine_Attack` clip. Final Noble clothing, saber and boss body remain art work. |
| Hatchlings / Overseers | Shared native Demon A / flying-demon stand-ins pending Hesper models. |
| New loot ground art | Existing item 127 / helm 109 / sword 001 / amulet 4 / scroll 2 shapes for the new bindings; Hesper icons and data, including the full Noble's Letter, are staged. |
| Surface textures | All 22 required K8/K10 masters exist and are installed; no surface texture substitution. |
| Vhorrax's lunge | Supported 1.5 s `perform` effect/sound followed by `castNext` Incinerate, at the specified 6/8 s cadence; no physical dash or new saber-glow art. |
| Refused adds | Four capped 30 s summons through native `self:summon`; that API chooses nearby positions, so placement specifically on the ledge is not guaranteed. |
| H3 random loot | Native tier-6 pool plus 9,000 gold until P4 installs the Hesper weighted pool. |
| Sabotaged ambient | Brain light and nerve fixtures switch off and the brain texture changes. The requested sector ambient change to 27 has no Lua API; original sector ambient remains. |
| Audio | Original synthesized heartbeat, stepped neural hum, convulsion and lunge warning; shared membrane cue. Recorded voices, scratching and final ambience are absent. Music track 104 is registered by the shared manifest. |

Geometry reconciliations accepted by the integrator (2026-10-23):

- The prescribed 64-unit stair risers exceed the engine's 50-unit step limit. Both bone stairs, gilded stair and
  duelling stair have **40 × 32** risers with the original widths, endpoints and total runs. Stairwell headspace is
  owned by the stair sector up to the upper ceiling, with real vertical landing portals and rail openings.
- The 600-wide torn ramp keeps its 2,000 run and 1,280 rise but uses **40 shallow torn-plate treads**. The continuous
  GLB slope's diagonal triangle seam deflected the native party sideways; this data-only version passes ascent.
- Door 51's centre moves from x 1,800 to **1,960**, fitting its 256 width within the Dormitory/Chamber connection.
  Doors 220/221 are **256 wide at x 472/3,128**, fitting the shared flanks; the drawn 384-wide leaves overhang the ring.
- Ring ledges have gaps for the entrances, stair landing and planned fire bowls. The vault dais has seven shallow
  steps; chest B is raised to its top at z 1,480. Ganglia likewise stand on, rather than inside, their plinths.
- Four Dormitory cradles are shallow **100 × 400 × 700** gilded frames on the east wall, fitting its length and keeping
  the bone stair clear. The Chamber's 1,000-high rack is **560** high beneath its 640 ceiling.
- The Nerve Galleries keep **two 800 × 700 windows each**; the integrator accepted two, with no third window.
- The Sensorium's three 900-wide windows wrap onto the two flanks because they cannot fit its 2,400-wide bow wall.
  The Core's central nerve trunk is at y 9,300 to clear the planned actor pack.

The integrator also accepted fixture-only darkening, free summon placement, the Incinerate lunge and H3 fallback.
Those remain until the shared engine/art tasks land. No new design questions. Integrator follow-up: capture both ready
tours and review lighting, stand-ins, Wizard Eye/automap and reward presentation.

## Brightness B — 2026-10-23

Recompiled with zero warnings; **sabotage 132/132 PASS**, Lua and saved-state checks pass, and the supplied
blind save is refreshed. Ambient is 10 in the Brain, 12 in other main rooms and 15 in passages/stairs.
All 24 occupied rooms now have a ≥640-radius fixture. Map-only nerve nodes use 704 and bowls 864; ten new
fixtures fill the rooms previously lit only by organs/storm light. The sixteen spine lamps inherit the larger
radius; **68 lights total, sampled overlap 3**. New nerves retain the pulse/sabotage groups and dark bindings.
The updated ambient is static; the accepted fixture-only sabotage darkening remains. Before: mean **33.2**,
darkest **22.3**. No new capture; integrator re-measurement is required. Evidence: `review/brightness_b/`.

The initial brightness restage failed on an unrelated stale Yara portrait; final stage/regression status is
in the Brightness B report in `WORK_PACKAGES/requests/P3.md`.

The following D12 stage run completed successfully and installed this D11 payload too; the temporary portrait
blocker has cleared (`hesper_d12/review/brightness_b/stage.log`).


## Pickup placement — 2026-10-24

28 serum vats: 14 in the Seed Vault serum hold, 5 by the armour cradles, 5 in the dormitory and 4 in the
attendants’ room. 20 scrap bundles. All positions are authored in `author_d11_blender.py` and exported under
`pickups` in the semantic record. Stat containers occupy wall-side storage groups; satchels avoid boss rooms
and central routes.

The authored handlers call `HesperPickups.setup` with explicit treasure level **6 (H3)**. The shared automatic
map-name lookup failed at the first satchel click; the documented treasure override gives the correct dungeon
loot level. Stage installation supplies `hes_d11_pickups.lua` with every colour/empty model. No new art or
stand-ins were needed.

Removed 4 fixed floor-gold piles, as PICKUPS.md requires. Chest/event rewards and themed supply items remain.

`d11_pickups.yml` clicks every placed pickup; all stat containers reach the empty state and survive save/load.
`review_tour_pickups.yml` contains the storeroom and two satchel views for the integrator; captures were not
run in this sandbox.

Placement checks (counts, boss-room exclusion, floor support, furniture/actor clearance, native event/cog IDs,
stage equality and swap overlays):

```sh
flock -s output/hesper_stage/locks/stage.lock python3 -B level_generation/projects/hesper_d11/check_pickups_batch_d.py
```

Author, compiler and pickup-scenario logs are in `review/pickups/`. The batch regression record is
`hesper_d11/review/pickups/regression.log`.

Validation: all pickup clicks and existing map scenarios pass; `rebuild_all.sh --scenarios-only` passed
93/93 (exit 0), with decoration-ID and actor-size audits clean. Run logs: `output/hesper_stage/logs/scenarios_082229_4/`.

## Walkability and room shapes — 2026-10-24

Seedship retains its three decks and brain cathedral. All five interdeck flights now have 80 × 16 treads,
continuous side skirts and rails, and floor/ceiling openings. The vault hatch landing rails are 128 high;
the seven-step vault dais has side rails. Moving the Core nerve trunk aft opens the Sensorium route. Chamfered
compartments, hipped membrane ceilings and the starboard gallery's diagonal shoulders meet the organic-room
shape target. The aft ganglion plinths and their existing actors sit inside the new cathedral corners.
The two supply shelves remain allowlisted furniture. The sabotage scenario's dais approach now starts on the
correct first tread, clear of the adjacent stair enclosure.

Final compile: 8,998 faces, 53 sectors including the empty sector, 27 movers and 120 decorations, with no compiler warnings.

Local runtime audit: **zero findings, two furniture exceptions**. Shape survey: 36/52 nonorthogonal rooms, 89% axis-aligned wall area, 29 sloped ceilings, 0.3% ramp area. Actor order, pickup order, event/cog bindings and door IDs are preserved.

Evidence is in `review/walkability/`: baseline/current audits, shape surveys, identity checks and private-stage scenario logs. `d11_walkability.yml` adds melee pursuit across the repaired spots. `review_tour_walkability.yml` covers the repairs and reshaped rooms; the integrator captures it on the desktop. No screenshot was attempted in this sandbox.

Built and installed in the shared stage after the Noble weapon export blocker was repaired by its owner. This map is now in `WALKABILITY_GATED`; its new fight scenario is included in `rebuild_all.sh --scenarios-only`. Initial tests used a private stage copy while installation was blocked. Final shared-stage regression results are recorded in the batch B report at the end of `design/kreegan_world/WORK_PACKAGES/requests/P3.md`.

Final regression: all 12 batch B scenarios pass. The full scenario inventory is **102/102 passing** after binary-startup retries and the concurrent D15 fixes, including its newly added fight scenario. Global decoration IDs, actor sizes and every walkability gate pass. The P3 batch B report distinguishes the original driver exit from the successful reruns and links the evidence.
