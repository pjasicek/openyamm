# Hesper D3: Quarry Outpost

Map **9111**, `hes_d03.blv`, built from the [BUILD-READY handoff](../../../design/kreegan_world/zone2/dungeons/D3_QUARRY_OUTPOST.md)
and its `plans_zone2.py` plan, using `hesper_stage/blv_kit.py` and `blv_build.py`.

The staged build has 25 occupied sectors plus empty sector 0, three elevations, 64-unit wall reveals, both
24-step stairs, the eight-beam lattice Yard, tapered cover heaps, P2, barracks bunks, pod racks, crusher throat,
lab benches, quarry steps, the Roost/perch/pens and Signal Room. Doors 51–55/58 and lifts 56/57 are native linear
movers. The roster is 45 initial actors plus 14 hidden reinforcements; six chests, eight serum vats, twenty scrap
bundles and the once-only stair cache are installed. Events implement the cover/alarm timers, two waves, hacking/charge routes,
turret stand-down, the three pens, Krav's telegraphed Fireball, shield-link death and the Ion Coil reward.

## Walkability and room shapes — 2026-10-24

The second pilot for `hesper_stage/check_walkability.py` and the kit's shapes, against the user's play
(`hesper_stage/review/user_play_20261024/user_71`, `user_72`). The map audits clean; the Mess Hall's trestles are
allowlisted (`hesper_stage/walkability_allow.yml`).

- **The crusher's throat (user_71):** one 32 step deep (it was 64: the Drudges feeding the crusher stepped in and
  never climbed out).
- **Lower Storage (user_72):** the three plain blocks are ore bins: crate-sided hoppers on a rib frame with corner
  posts, heaped with ore.
- **Found by the audit:** the gate turrets' pedestals stood 72 into the Gatehouse's west wall (now x 7060); one
  mess trooper stood at a trestle's edge.
- **Shapes:** a chamfered Crusher Hall under a hipped ceiling (the signature hall round the crusher), chamfered
  corners in the Quarry Face (its rock tiers cut to them), Gatehouse (hipped), Emitter Lab, Mess Hall and Signal Room,
  an irregular Cave-in pocket (`poly_room`), and sloped ceilings over both stairs. Survey: non-orthogonal rooms 1 → 9
  of 25 (36 %), sloped ceilings 0 → 5.
- **Checks:** `d03_main_path` 104/104, `pickups` 28/28, and the new [`d03_walkability.yml`](d03_walkability.yml): a
  Drudge leaves the throat for the party, another walks round the ore bins. Captures:
  [`review_tour_walkability.yml`](review_tour_walkability.yml) (`review/walkability/`); the desktop run stopped on the
  staged `hes_overseer.glb` texture cook ("prepared for another use"), so the integrator captures it after a re-cook.

## Build and stage

From the repository root:

```sh
flock -s output/hesper_stage/locks/stage.lock timeout 1800 blender --background --factory-startup \
    --python-exit-code 1 --python level_generation/projects/hesper_d03/author_d03_blender.py
flock -s output/hesper_stage/locks/stage.lock \
    python3 level_generation/projects/hesper_d03/build_d03.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
```

The author writes the GLB, Blender source, geometry and semantic metadata. The second command compiles the BLV,
checks events/light counts/movers, writes the scene/Lua and synthesizes six own PCM sound cues. Only
`runtime/worlds/hesper/` is installed, through the stage. No engine build or lighting bake is required.
`source/actor_standins.yml` supplies Krav's temporary binding; `behaviors.yml` registers his map-owned behaviour.

This host's Snap launcher cannot run in the sandbox. The verified executable is
`/snap/blender/current/blender`. The author now flushes its outputs and calls `os._exit(0)` after export, as the
builder guide requires, avoiding the sandbox hang on Blender shutdown. Run it under `timeout` as above.

`build_d03.py` reads the Scour's `hesper_out2/out2_build.json`, `arrivals.d03_return`, when it exists. The outdoor
builder must read `source/hes_d03.semantic.json` → `arrivals.d03_outer_gate` for its entry. Rebuild and stage both
maps after connecting them. No outdoor destination coordinates are fabricated.

## Play, test and capture

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
    ./tools/run_game.sh --isolated d03 \
    --world hesper --map hes_d03.blv --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d03/review_tour_01.yml" --seconds 0

(cd output/hesper_stage/scenario_run && flock -s ../locks/stage.lock flock -s ../locks/engine_build.lock \
    env OPENYAMM_START_MINIMIZED=1 ../../../build/game/openyamm --world hesper \
    --headless-run-scenario ../../../level_generation/projects/hesper_d03/d03_main_path.yml --scenario-no-color)

flock -s output/hesper_stage/locks/engine_build.lock \
    level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

All game runs remain minimized. Use only `--scenarios-only` while other builders work. The existing integrator's
37-shot sheet in `review/build01/sheet.jpg` is preserved, and builds now leave an existing `review_tour_01.yml` alone.
The integrator captures the revision and assembles its sheet; the original fixed-count sheet helper is not used.

## Integrator fixes (2026-10-23)

Applied A–F and all rulings from [P1's D3 review](../../../design/kreegan_world/WORK_PACKAGES/requests/P1.md):

- Krav's stand-in has `animation.cast: Carbine_Attack`; the staged binding and that clip in the staged GLB agree.
- Four octagonal turret plinths are 220 × 220 × 160, with `hoaresin` sides and `hochitin` tops at the turret feet.
- The eight alarm pods sit on 128-high cradles, below eye height, within the sightlines through the Yard mouth.
- The cracked face has a tapered 400 × 200 × 160 rubble heap, with `hkrock` sides and an `hkore` top. Yard ore
  heaps also have `hkrock` sides. The secret's north approach stays open.
- Nine packs use stable, irregular offsets; the Mess and work groups face their fire/trestles, ore, crusher or
  working face. Actor indices and group sizes are unchanged. Actor and ground-item sector IDs follow native order.
- Event 50's unbound message is exactly “The Outer Gate: the way is not yet open.” The current Scour record binds
  the exit. Event 70 already omitted “(the selected character)”; its stale implementation comment is corrected.
- L4 is at `(3800,700,-420)` inside the Pod Bay. Work fires are at `(1700,-2500,-1536)` and `(3700,-2500,-1536)`.
  The dead Kept and 1,000 gold are on the lane at `(2600,1150,-768)`. The chute remains 500 × 572.
- Krav's accepted direct 10,000-gold payment now has a status message. The scenario uses the relocated gold and
  the clear approach beside the larger rubble heap.

Revision evidence is under `review/fixes01/`. **No new screenshots or desktop run were attempted: this sandbox
cannot capture them.** The integrator must confirm the map stays loaded and re-capture the requested views.

## Validation and remaining gates (2026-10-23)

- Compiler: **zero warnings**, 2,510 faces, 1,708 vertices, 26 sectors, 72 portal triangles, 8 movers,
  7 standalone lights and 46 decorations; every interaction is bound. See `review/fixes01/build.log`.
- Plan with the reviewed light positions: light overlap maximum **4**, ceiling checks pass.
  Native plinths, staged cast clip, pod height/mouth sightlines, corrected placements and pack spacing also pass;
  `review/fixes01/static_checks.json`.
- Design audit: **0 findings**, `review/fixes01/design_audit.txt`. Ran the unchanged audit with its report destination
  redirected here so it did not rewrite a design document.
- **D3 scenario: all 110 steps pass**, including physical stair/lift travel, exact gold pickup after save/load,
  both alarm waves and cancellation, hacking and a genuine Breach Charge, timed pens, Krav/shield-link death,
  Saber/Core, Ion Coil collection, lab, shelf cache, secret face and both Master turret consoles.
  See `review/fixes01/d03_main_path.log`.
- **Shared regression: exit 1; 43 pass, 11 fail, one known WIP failure.** D3 passes again. The 11 failures concern
  missing dialogue actions or an inactive dialogue in the Crown market, Brood Spires nest, D0, D2, three Undervault
  scenarios, two Starport Reach scenarios and the two shared dialogue/teacher scenarios. D5 remains the existing
  non-gating WIP failure. No other map or shared dialogue source was edited. See `review/fixes01/scenarios_only.log`
  and `review/fixes01/regression_result.json`; individual failing logs are retained alongside them.
- The Scour now supplies `arrivals.d03_return`, so the Outer Gate is bound. `hesper_out2/scour_exits.yml` checks
  its round trip and **passes** in the shared regression suite (`review/fixes01/scour_exits.log`).
- The integrator's first native review required these revisions. Fresh visual acceptance, desktop loading,
  Wizard Eye Master and automap review remain with the integrator; no new visual acceptance is claimed.

## Stand-ins and deviations for the integrator

| Requirement | Current build / reason |
|---|---|
| Closed/open drop pods | Existing `hes_kreegan_pod_chest` / `hes_creep_pod`, collision radius 70; exact new pod models absent. |
| Ore carts / crates / dead Kept | `hes_baggage_cart` / `hes_ashrunner_crate` / `hes_corpse_colonist`, with handed-over radii 80 / 120 / 0. |
| K5/K6 fixtures | Shared staged colony wall lamps and brazier aliases; plan light colours/radii retained. Fire-bowl collision radius is the existing shared alias's 0 rather than the document's 40. |
| Drudges / Krav | Shared Drudge native Demon A sprite stand-in; Krav uses Trooper body ×1.3 and its existing equipment until the winged Overseer/pistol/hip-saber is produced. |
| Plasma Saber / Buckler ground art | Native sword `item001` / shield `item099` geometry; Hesper inventory icons and item data are staged. |
| Surface textures | All named masters exist; no missing-texture substitution. |
| Shelf cache | Reuses D1's native cache-container pattern (container 0), preserving untaken contents; map variable 3 records first opening. |
| Hacking | Party-wide `CheckSkill`, accepted by the integrator. The charge route is tested with no hacker in the party. |
| H2 random containers | Exact 4,000 gold plus native tier-4 random generation pending P4's Hesper-only weighted item/enchantment/salvage pool. This is not the final H2 loot implementation. |
| Krav's 10,000 gold | Direct payment with a status message, accepted as interim. `evt.SummonItem` accepts no gold amount; Saber and Core remain proper ground drops. |
| Ore Chute | The integrator ruled the 500 × 572 plan authoritative; retained with its specified travel/speed. |
| Alarm light L4 | Reviewed z −420, beneath the Pod Bay ceiling; original XY, radius and colour. |
| Quarry work fires | Reviewed floor positions `(1700/3700,-2500,-1536)`, with original radius and colour. |
| Yard corpse/gold | Reviewed lane-floor position `(2600,1150,-768)`, beside the heap. |
| Sound/music | Six own synthesized cues are temporary art. No Krav voice, cave draught or Kreegan music master exists; the shared music manifest lists that track as ungenerated. |

The integrator accepted the stand-ins and interim loot/payment rules and schedules their replacements. Re-capture
the revision, confirm desktop loading and review the changed geometry before sign-off. Sprite atlases and final
fire-bowl art remain integrator-owned; this revision does not change shared sprite or decoration assets.

## Brightness B — 2026-10-23

Rebuilt and staged, zero warnings; **main scenario 110/110 PASS**. Ambient: Yard 10, main rooms 12,
circulation/stairs 15, the explicitly dark Cave-in 20. Every occupied room now has a fixture with radius at
least 640: map-only graft/vent aliases use 704 and fire bowls 864. Six fixtures cover the Yard, East Stair,
both lift levels, Crusher Hall and Cave-in; the latter represents the locker's status lamp. Plan checks:
**31 lights, maximum overlap 4**, valid ceilings and fixture bindings. Geometry, mechanics and shared fixture
values remain unchanged. Evidence: `review/brightness_b/`.

Builds must hold `flock -s output/hesper_stage/locks/stage.lock`, including Blender authoring; game runs also
hold the shared engine lock. Brightness before this pass: mean **34.1**, darkest **16.8**. No new captures;
the integrator re-measures the existing tour against mean ≥40 and no ordinary shot <20.

## Pickups placement (2026-10-24)

8 serum vats; **20 scrap bundles**, from 2,510 built faces (8 per 1,000, rounded and clamped to 6–20). Four vats in Lower Storage, two in the Barracks' quartermaster area and two in the rear Signal Room. Bundles occupy supply corners, cover lanes and body/locker spots; none in Krav's Roost. The Yard and Crusher bundles replace both old fixed floor-gold piles (PICKUPS.md); chest gold and Krav's direct reward are unchanged.

The author keeps the placements as `(room, event, x, y, z, facing)` rows and exports them in `semantic.json`
under `pickups`. Events equal cogs: containers 701–708, satchels/bundles 751–770. The stage installs the map's
`_pickups.lua` sprite overlay automatically. All models and full/empty variants already exist; no stand-ins.

The map passes `treasure = 5` to the shared helper (H2). Its default lookup expects a filename,
but `GetCurrentMapName()` returns the display title; the explicit tier avoids that failed lookup without engine changes.

[`pickups.yml`](pickups.yml) checks native clicks, each stat supply group where present, two separated satchel
spots, save/reload and a repeat click. Item-roll state is covered headlessly; delivery to the hand remains the
shared mechanic's desktop check. [`review_tour_pickups.yml`](review_tour_pickups.yml) has the supply store and two
satchel views, writing to `review/pickups/`. This sandbox cannot capture; the integrator runs the tour.

All four batch-A authors flush outputs and use `os._exit(0)` after export; run them under `timeout 1800` and the
shared stage lock. On this sandbox use `/snap/blender/current/blender` in place of the Snap `blender` launcher.

Focused checks passed: `pickups.yml` (28 steps), native event/cog/model bindings and floor placement;
geometry, actors, chests, doors and arrivals preserved. Logs: `output/hesper_stage/logs/pickups_batch_a/`.

Shared sweep: **92/93 pass**; only the other batch's `hesper_d04/d04_key_path` fails at step 12, also on
focused retry. All Batch A scenarios and both audits pass (zero decoration-id or actor-size mismatches).
Integrator handoff: `design/kreegan_world/WORK_PACKAGES/requests/P4.md`, pickups placement, batch A.

## R5 Ashkites (2026-10-26)

Two flocks of four Ashkites (10310), groups 150/151, occupy the tall Quarry Face at floor Z -1536,
centred on (2000, -2300) and (3100, -2300). Actors 0–58 retain their indices; the eight additions are 59–66.
The author and build actor-count gates now expect 67. `d03_walkability.yml` uses `actor_index: last` for its
explicitly spawned Drudge, so appended map actors do not change the test's target. Rebuild through
`author_d03_blender.py` then `build_d03.py` as above. Flyer clips reach 154 world units at A scale, well within
the Quarry Face clearance. No original actor was removed.
