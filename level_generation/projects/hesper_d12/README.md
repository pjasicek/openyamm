# Hesper D12: Crownspire — map 9134

Built from [D12 Crownspire](../../../design/kreegan_world/zone4/dungeons/D12_CROWNSPIRE.md), its BUILD-READY
section and `zone4/dungeons/plans_zone4.py`, using the shared Hesper indoor kit. Sources and runtime content
remain in this project; installation is exclusively through `hesper_stage`.

## Status — 2026-10-23

All four levels are built and staged: Ancient Core −1536, Palace 0, Court 768 and Crown 2304. There are 28 rooms,
54 occupied sectors plus empty sector 0, 26 movers, 5,190 compiled faces, 64 lights (59 fixtures and five explicit
lights), eight chests and 123 actor records: the plan's 121 actors plus two hidden Hierarch replacement forms.
The source includes the press, grafting frames, firing range, trophies, barracks, 32-step stair, sunken ring,
gilded ribs, two working lifts, Voice core and cables, throne dais, conduits, turrets and Ancient machinery.

The second-round fixes spread all 121 placed actors outward from their plan marks on free floor: minimum spacing
400, at most three actors in any 300-unit radius (the limit is four). The two hidden replacement Hierarch forms
retain their shared dais position. Actors and ground items now use the compiler's sorted native sector order.
Pressure-plate cutouts preserve the surrounding floor material, and Ancient Core doorway thresholds use `hcfloor`.
The document's palette is retained: `hcfloor` in the Core, `hpfloor` in the Palace/Crown and Court surrounds,
and fitted `hpring` in the Court's sunken ring. The accepted Court, Voice and Throne geometry/views are retained.
The founder-head stand-in has a 52-unit collision radius enclosing its model footprint; the main-path scenario
walks onto the plinth and verifies that it cannot walk through the head. Trophy/lift tour poses are clear of actors.

The main path passes: gate refusal/control, walking the stair and ring, guarded duel start, three duels and drops,
Court Seal, both-direction lift rides, three Voice speeches, conduits, Hierarch phases, allied turret damage,
all three endings, every member's seven stat rewards, shaft prerequisites and save/load. The backdoor passes:
actual D15 arrival without damage, Core speech, Expert Hacking, Grid flags/reward, persistence and Core Lift ride.
The Crown's gate and pad lift and D15's service lift each pass an actual click-driven round trip.

The Hierarch uses **10145 → 10120 → 10146**. The latter two each have 30,000 HP: defeating 10120 crosses 50% of
the combined combat health. The seated ward is removed when its form is hidden. With 100023, the fourth conduit
sets **100608**, using the stage's existing `aster_turrets` relations; the scenario verifies friendly turrets and
actual damage to 10120's shield. The final unshielded form dies from one unabsorbed test hit.

D13 is now built. Exit 53 reads its published `shaft_bottom` arrival `[400,1000,0]`, facing east;
Deepwell's return reads D12's `shaft_head` at `[1600,19300,2304]`, facing south. The D13 follow-up rebuilt
D12 and strengthened `d12_round_trips.yml` to click event 50 directly from the `spire_gate` arrival
at `[0,400,0]` after opening door 1. The reported gate interception does not recur in this build.

## Build and test

Run from the repository root. The first build was performed level by level in this order, compiling after each
export. Each export runs `max_light_overlap`, `ceiling_problems` and `stacking_problems` directly, without calling
the plan module's document-rewriting `main()`. Retained results are `review/checks_{core,palace,court,crown}.json`.

```sh
for level in core palace court crown; do
    (cd level_generation/projects/hesper_d12 && flock -s ../../../output/hesper_stage/locks/stage.lock \
        blender --background --factory-startup \
        --python author_d12_blender.py -- --through "$level")
    flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
        build/tools/mm9_compile_indoor_source \
        level_generation/projects/hesper_d12/source/hes_d12.glb \
        level_generation/projects/hesper_d12/source/hes_d12.geometry.yml \
        "level_generation/projects/hesper_d12/review/$level.blv" \
        level_generation/projects/hesper_d12/source/hes_d12.doors.yml \
        level_generation/projects/hesper_d12/source/hes_d12.faces.yml
done
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
    python3 level_generation/projects/hesper_d12/build_d12.py
python3 level_generation/projects/hesper_d12/make_scenarios.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
```

`make_scenarios.py` reads compiled face ids for the lift-ride checks, actual actor indices and the Crown's published
door poses. Regenerate the YAML after a geometry change. `build_d12.py` verifies bindings, doors, fixture data,
actor counts and the final plan checks. No engine compilation or outdoor bake is needed for this indoor map.

```sh
cd output/hesper_stage/scenario_run
for scenario in d12_smoke d12_main_path d12_backdoor d12_round_trips; do
    OPENYAMM_START_MINIMIZED=1 flock -s ../locks/stage.lock flock -s ../locks/engine_build.lock \
        ../../../build/game/openyamm --world hesper --headless-run-scenario \
        "../../../level_generation/projects/hesper_d12/$scenario.yml" --scenario-no-color
done
```

The four scenarios are registered in `hesper_stage/rebuild_all.sh`; D12 is not a WIP exception. Initial-build
results remain in `review/verification.json`; this fix round is recorded in `review/fixes/verification.json`.
D12 passes **5/5, 414/414, 51/51 and 26/26** steps. The shared `--scenarios-only` run finished **70 PASS / 1 FAIL**:
`hesper_out1/arrival` lacked dialog action 9001 at step 8. Its unchanged, locked retry passed all 49 steps;
the complete run remains failed. All four D12 scenarios also passed in that shared run. No other map was patched.
The design audit has zero findings.

Run `flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d12/verify_fixes.py`
after staging to check density, free floor, native floor materials/sectors, the trophy collision binding,
camera clearance, D13's link, the unchanged original review sheet and staged payloads. No engine rebuild or outdoor
rebuild is part of this fix.

## Integrator's visual review

The requested 13 poses are in `review_tour_01.yml`; the engine adds eye height to their floor positions. The Court
and throne retain +10° pitch. Trophy west moves to `[-3650,6450,0]`, looking toward the head; the lift moves onto
its platform at `[0,12120,768]`, looking north and up 15°. The tour writes `review/build02/`, preserving the
integrator's `review/build01/sheet.jpg`. No new screenshots were captured: the user excluded capture in this
sandbox. The integrator captures the revised sheet and reviews appearance and Wizard Eye/automap readability.

```sh
flock -s output/hesper_stage/locks/engine_build.lock flock -s output/hesper_stage/locks/stage.lock \
    ./tools/run_game.sh --isolated d12 \
    --world hesper --map hes_d12.blv --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d12/review_tour_01.yml" --seconds 0
```

## Stand-ins and recorded differences

| Requested art or behavior | Current staged representation / follow-up |
|---|---|
| Gilded bowls and coils | Existing Hesper brazier and light-pylon bodies, with exactly the planned light radii/colors; dedicated gilded bodies remain art work. |
| Shaft alarm beacon | Existing amber wall-lamp body with the planned red light and dark off state. Group 4 stays off in D12. |
| Founder's head | Existing crystal-relic stand-in, clickable and removed once item 11511 is taken. Replace with the founder's actual head mesh. |
| Palace coffers | Existing Kreegan pod-chest body; chest ids and locks are implemented. |
| Membrane banners and graft loads | Textured membrane/pole and Ancient-housing geometry instead of separate decoration models. |
| Lords, Gatekeeper and Hierarch gear/poses | Existing Trooper bodies. The Hierarch binding is enlarged to its 430-unit design height; seated/sleeping poses use standing/rest fallbacks, and unavailable boss telegraph clips use attack fallbacks. Conduits and throne turrets use the existing Ward Turret body. |
| Firing-lane `hpinlay` | No master exists; narrow `hptrim` floor inlays mark the six lanes. |
| Dedicated ambience and boss cues | Existing combat/effect sounds and written dialogue; bespoke court murmur, Voice chord and lift hum remain audio work. |
| H3 loot | Native T6 random treasure and the authored gold amounts until the Hesper H3 pool exists. Fixed Engrams, supplies, Seal, head and ending relics use their actual item ids; new icons/ground shapes use staged native stand-ins. |
| Hum / indoor Meteor Shower / blink | Documented workarounds: Hum message, Lightning Bolt and Ssekh's six-second dive request (attack animation fallback on the current body). |
| 10120 → 10146 placement | The second form appears on the authored dais. Map Lua cannot read the first form's death position, so exact in-place replacement awaits an actor-position query. |

The 900-high Grid cabinet would intersect its 640-high room: its footprint is unchanged and its height is 560.
F40's planned z=2904 exceeds the shaft ceiling at 2752; the beacon is at 2688. The dais retains three visible
terraces and adds eight 32-unit treads along its east edge for ordinary walking. Rim plates extend 128 units onto
the upper rim so a walking party cannot skip them while dropping over the 32-unit intermediate tread; the ring
still drops 64. Sector-split openings share one complete reveal, avoiding an artificial jamb through their centre.
The gate leaf carries exit 50, while the southwest pillar carries control 72, so the exit remains clickable after
the mover opens. The explicit door table's 26 movers wins over the plan budget summary's 25.

The integrator's corrected cast/stride bindings and 10057's 90°/s traverse are preserved. Per-placement tactics
remain the integrator's queued engine work; no additional workaround was introduced here.
No engine code, `assets_dev`, Vulkan build, performance run or Git staging operation belongs to this build.

## Brightness B — 2026-10-23

Main rooms now use ambient 12; corridors and stairs use 15. D12-only wall/bowl/coil fixtures have radius 864,
ceiling lamps 1056. Four added fixtures cover the gate, shaft and both previously unlit lift landings; the shaft's
existing switched alarm beacon remains separate. All 28 occupied rooms have a lit fixture of radius at least 640.
The 68-light plan passes ceiling/stacking checks and peaks at four overlapping lights on a 32-unit floor grid.

The full map was re-authored and compiled under the shared stage lock: 5,190 faces, 55 sectors, 26 movers,
74 decorations, five explicit lights and zero compiler warnings. YAML parse checks and the exclusive stage run
pass. All four scenarios pass: smoke **5/5**, main **414/414**, backdoor **51/51**, round trips **26/26**.
The existing actor, material, native-sector, collision and staged-payload checks pass too.
Evidence is in `review/brightness_b/`. The D12 fix round had a completed builder report before this pass began.

The original 13-shot sheet remains unchanged (mean 39.3, darkest 15.4). No new captures were attempted;
the integrator re-measures the revised lighting. The final shared regression is recorded in P3's brightness B report.


## Pickup placement — 2026-10-24

14 serum vats: 7 in the west graft stores, 4 in the noble gallery and 3 in the house gallery. 14 palace scrap
bundles and 6 colony satchels in the Ancient Core. All positions are authored in `author_d12_blender.py` and
exported under `pickups` in the semantic record. Stat containers occupy wall-side storage groups; satchels
avoid boss rooms and central routes.

The authored handlers call `HesperPickups.setup` with explicit treasure level **6 (H3)**. The shared automatic
map-name lookup failed at the first satchel click; the documented treasure override gives the correct dungeon
loot level. Stage installation supplies `hes_d12_pickups.lua` with every colour/empty model. No new art or
stand-ins were needed.

Removed 4 fixed floor-gold piles, as PICKUPS.md requires. Chest/event rewards and themed supply items remain.
The Court Seal scenario now derives its dropped-item index from the initial scene item count.

`d12_pickups.yml` clicks every placed pickup; all stat containers reach the empty state and survive save/load.
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

Crownspire now uses a 32 × 24 grand stair with a shallow cache shelf, a four-step sunken Court ring,
a 16 × 16 throne approach and 32-high turret bases. Both lift platforms fill their shafts and meet their landings;
shaft bottoms sit 32 below the lower landings. The Court and Throne have clipped corners and hipped roofs,
other rooms gain chamfers and pitched ceilings, and the Core connector has a diagonal dogleg. Actor/fixture
placements follow the changed floors; the throne forms keep their original indices. The Core dogleg placement
check uses its actual concave polygon and segment clearances, including the current larger Sentinel bodies. The two remaining high
surfaces are the trophy plinth and Voice supply shelf, both explicitly allowlisted furniture.

Final compile: 6,600 faces, 55 sectors including the empty sector, 26 movers and 108 decorations, with no compiler warnings.

Local runtime audit: **zero findings, two furniture exceptions**. Shape survey: 38/53 nonorthogonal rooms, 87% axis-aligned wall area, 34 sloped ceilings, 1.2% ramp area. Actor order, pickup order, event/cog bindings and door IDs are preserved.

Evidence is in `review/walkability/`: baseline/current audits, shape surveys, identity checks and private-stage scenario logs. `d12_walkability.yml` adds melee pursuit across the repaired spots. `review_tour_walkability.yml` covers the repairs and reshaped rooms; the integrator captures it on the desktop. No screenshot was attempted in this sandbox.

Built and installed in the shared stage after the Noble weapon export blocker was repaired by its owner. This map is now in `WALKABILITY_GATED`; its new fight scenario is included in `rebuild_all.sh --scenarios-only`. Initial tests used a private stage copy while installation was blocked. Final shared-stage regression results are recorded in the batch B report at the end of `design/kreegan_world/WORK_PACKAGES/requests/P3.md`.

Final regression: all 12 batch B scenarios pass. The full scenario inventory is **102/102 passing** after binary-startup retries and the concurrent D15 fixes, including its newly added fight scenario. Global decoration IDs, actor sizes and every walkability gate pass. The P3 batch B report distinguishes the original driver exit from the successful reruns and links the evidence.
