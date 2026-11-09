# Hesper D9: Brood Pits (`hes_d09.blv`, map 9122)

## Pickups placement — 2026-10-24

Built and staged **8 serum vats and 20 Kreegan scrap bundles** from `PICKUPS.md`.
Brood Barracks keeper cache: 4 (701–704); Brood Larder: 2 (705–706); North Ledge feeding supplies: 2 (707–708).
Bundle density is round(6,604 faces × 8 / 1,000), clamped to 6–20. Positions and stable event IDs are in
`author_d09_blender.py` and `source/hes_d09.semantic.json:pickups`; bundles use 751–770.
The 3 former fixed floor-gold piles are removed; chest/boss rewards and themed supplies remain.
This supersedes the older floor-gold counts below.

The authored handler uses the shared `HesperPickups.setup`, with treasure level **6** explicitly:
`evt.GetCurrentMapName()` returns the display title, while the shared helper's default lookup expects a filename.
No shared mechanic or engine change is needed for these placements. The stage installs
`hes_d09_pickups.lua` for the colour and empty-model swaps. All pickups use the accepted existing models;
there are no new stand-ins.

Validation: zero compiler warnings; native checks of every pickup's event/cog, floor contact, wall/furniture
clearance and exclusion from boss rooms pass. Geometry, doors, lights, actors and chests match the pre-pass build.
[`d09_pickups.yml`](d09_pickups.yml) passes **76 steps**, clicking every pickup at its actual placement;
vat empty states also survive save/load. The shared test room covers the random loot/stat mechanic.
Evidence: [`review/pickups/`](review/pickups/).

Final regression: **93/93 scenarios PASS**; decoration-id and actor-size audits report zero mismatches.
Existing map scenarios: `brood_pits_descent` 85/85.
The shared sweep and audit logs are in [`D4 review/pickups`](../hesper_d04/review/pickups/).

**Capture pending:** [`review_tour_pickups.yml`](review_tour_pickups.yml) has the storeroom and two bundle spots.
The sandbox cannot capture screenshots; the integrator captures and reviews the tour:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  ./tools/run_game.sh --isolated d09_pickups --world hesper --map hes_d09.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d09/review_tour_pickups.yml" --seconds 0
```

## Brightness A (2026-10-23)

Main rooms use ambient 10–12, galleries and transit spaces 14, and the Birth Pits 18. Sixteen permanent
glow-sac stand-ins bring the plan to 57 native lights. Fixture radii are 640, or 864 in large rooms.
The Royal stair light height is now recorded in the plan itself.

The authorised changes live in this map's zone-plan entries and its author scripts. All three maps' plan checks
peak at three overlapping lights; native readback confirms the new ambient and light values. These values supersede
the earlier lighting/count records below. Evidence is in `review/brightness_a/`; shared-regression results are in
P2's dated brightness A report.

The 85-step descent scenario passes after restaging. The final shared regression passes all 71 scenarios.

**Capture pending:** this sandbox cannot capture screenshots. Use `review_tour_brightness.yml` with the existing
locked capture command to write `review/build03/`, then measure it with `hesper_stage/brightness.py`. The acceptance
target is a mean of at least 40, with no shot under 20 except documented darkness. Existing build02 captures remain
the measured baseline; no improved pixel brightness is claimed before the integrator re-captures.

Built from the [D9 BUILD-READY contract](../../../design/kreegan_world/zone3/dungeons/D9_BROOD_PITS.md) and
`plans_zone3.py:d9`, using the shared Hesper BLV kit and compiler. Everything installs into the isolated Hesper
stage; this project never installs into `assets_dev`.

## Build and test

From the repository root:

```sh
flock -s output/hesper_stage/locks/stage.lock blender --background --factory-startup \
    --python level_generation/projects/hesper_d09/author_d09_blender.py
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
    python3 level_generation/projects/hesper_d09/build_d09.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
python3 level_generation/projects/hesper_d09/check_geometry.py
python3 level_generation/projects/hesper_d09/check_scripts.py
(cd output/hesper_stage/scenario_run && OPENYAMM_START_MINIMIZED=1 flock -s ../locks/stage.lock \
    flock -s ../locks/engine_build.lock \
    ../../../build/game/openyamm --world hesper --headless-run-scenario \
    ../../../level_generation/projects/hesper_d09/brood_pits_descent.yml --scenario-no-color)
level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

On this host the sandbox cannot launch the Snap wrapper; `/snap/blender/current/blender` runs the same installed
Blender directly. `source/` holds the authored GLB, geometry/door/semantic manifests, blend and Lua handler inputs;
`runtime/worlds/hesper/` is the stage's install source. Edit the author/build scripts, never generated Lua.

## Review

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
    ./tools/run_game.sh --isolated d09 --world hesper \
    --map hes_d09.blv --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d09/review_tour_01.yml" --seconds 0
```

The integrator's tour has 40 shots covering every room. `review/build01/sheet.jpg` is the original review that
requested these fixes; it is preserved and does not show the revised build. This sandbox cannot capture native
screenshots; the integrator captures the revision. The ordinary launcher starts minimized. No performance run,
Vulkan build or engine change belongs to this project.

## Built

- All 26 plan rooms across four floors, the open two-level well, roof cut, three descending flights and Royal
  Tunnels, 64-unit reveals, specified sector splits, acid recesses/causeways, spawning pool, vats, cribs, shed
  carapaces, wall bays, cradle, three birth pits and the return lift. 42 occupied sectors plus empty sector 0.
- All 17 movers, 41 plan lights, eight chest decorations and all interaction faces. The compiler reports zero
  warnings; build assertions check bindings, light/entity counts and mover IDs. `d09_build.json` lists counts and
  actor indices by group.
- All 96 initial actors in groups 1–30, including 16 stationary clusters and three hidden four-actor waves. Egg
  hatching uses persistent behavior state and stops after two hatchlings per cluster. Native summoning is disabled
  on the scripted egg and Mother rows. The sacs share the Kreegan faction and drop the Mother's shield on death.
- The null field captures every member's actual SP, drains on load and each second, preserves that snapshot across
  reloads, and restores/clamps on leave. QBits, autonotes, vat bursting, fixed rewards, membrane timers, one-shot
  birth waves, Mother completion and egg lift are authored map Lua.
- Four fixed chests, four provisional random chests, three gold piles (1,400/2,200/2,800) and the four ground
  consumables at the Root Throat cache. The cache items occupy a 40-unit square around the design's position.

## Stand-ins and differences requiring integrator review

- The build retains the accepted `hes_glow_sac` and `hes_bones_litter` greyboxes: small egg-textured sac prisms
  with the plan's exact light radii/colours and six bone-beam heaps against the specified rooms' walls. Final art
  installation remains with the integrator. All required K7 textures exist.
- Drudges, Hatchlings, Overseer Primes and the Mother use the roster's native Demon/DemonFly/Demon Queen
  sprite stand-ins. Clusters and Brood Sacs use the native egg sprite. Hellhounds use the R5-1 hound model; Brutes retain D8's staged Trooper B stand-in. The Mother is the 450-unit native stand-in; her finished body/sacs, animation and sounds await art.
- The Mother's `never_staggers` modifier is an explicit stage supplement: the BUILD-READY contract requires it,
  but the design's generated roster omits `NoStagger`. The roster is left untouched. The two sleeping Barracks
  The former sleeping pack is now a mobile Hellhound kennel on the Royal Tunnels’ flat lower landing.
- The boss API's `castNext` accepts spells, not the roster's attack1. The behavior supplies the six-second swell and
  1.2-second hold, then native acid shooting resumes; it cannot enforce the specified exact attack cadence through
  the existing API. No gurgle, wet-crack, hatch or heartbeat audio is installed. Ask the integrator for an attack
  request hook and sound assets; no engine changes were made here.
- Vat splash specifies `Damage.Body`, but the current `evt.DamagePlayer` implementation ignores the damage-type
  argument. Its 2D6 proximity damage works; Body resistance handling needs an integrator-owned engine fix.
- Random pods use native treasure tier 6 and the H3 midpoint of 9,000 gold. Hesper's H3 equipment pool and weighted
  consumable/salvage/Engram rolls are not installed. These four chests remain provisional.
- The design's 64-unit stair risers exceed the engine's 50-unit step limit. Each is split into two 32-unit treads,
  preserving the endpoints and run. The Royal Tunnels' F12 light is raised to 260 above its actual tread.
- The 900-unit vat sac specification exceeds its 640-unit room ceiling. Sac bodies run from 128 to 600, with
  supports reaching 640. The upper lift control's stated position lies over the well: both controls mount on
  its west lip/wall at x=6800, y=3500. The lift deck remains inside the planned shaft.
- The plan module has 41 lights (25 fixtures, 16 glows), a 9,300 × 6,100 footprint and 70.9 million square units;
  the document's old totals differ. The geometry follows the executable plan. Two explicit air sectors join
  the vertically stacked well; they are necessary in addition to its 40 room sectors.
- Integrator-approved deviation from design §10: ambient is **20** for the upper ring, both well sectors,
  lower tiers and Nursery Ponds; **22** for the Descent and side rooms; **21** for the Royal Tunnels, Root Throat,
  Royal Gallery and Ovipositor Passage; **19** for the Mother's Chamber and Birth Pits; **22** for the shaft.
  All 41 plan lights, including the accepted F12 adjustment, remain unchanged.
- `hesper_out3/out3_build.json` now supplies `d09_mouth`, so the rebuilt exit goes to its recorded position
  (-8830, 6600, 0), facing 315 degrees. If that record is absent in a future build, event 50 says exactly
  "The membrane mouth: the way is not yet open." No guessed destination is authored.

## Integrator fixes and validation (2026-10-23)

The D9 fixes preserve the accepted deviations above. Sector splitting now clips only at internal split planes,
retaining the 64-unit floor, jamb and ceiling reveals previously removed at outer room boundaries. This closes the
ledge-floor/roof strips and doorway slivers in shots 04–06, 09, 10, 28 and 37. The inner well has its exposed
64-unit ledge-slab edge closed, with the stair opening preserved. All 22 vertical Royal Tunnels ceiling soffits
are now faced in `hbceil`, matching the horizontal ceiling panels (shot 30).

Native readback (`check_geometry.py`) verifies the repaired surfaces, all sector ambient values and 41 lights.
The four Crèche cribs measure 400 × 400 × **200**, with `hbfloor` tops and `hbvatrim` sides; no resizing was needed.
All three Birth Pits retain their 600-unit width, 256-unit depth and half-step exits. Their chamber-side reveals
now survive splitting, and ambient 19 improves both rooms; visual readability still needs the integrator's recapture.
The 600 × 600 lift deck retains its 32-unit thickness and `hbvatrim` on all four sides.

The shared sprite fix was already present: both staged monster descriptor rows **10045** and **10130** have eight
`3egg` entries in columns 11–18 and `InspectYOffset = 0`. No shared stage input was edited for this revision.

The map compiles with **zero warnings**: 6,156 faces, 42 occupied sectors plus empty sector 0, 17 movers, 41 lights,
8 decorations and 96 actors. `check_scripts.py` passes the exit fallback, SP capture/restore/clamp and reentry,
vat gating, one-shot waves, completion and bounded hatching. **`brood_pits_descent.yml` passes all 85 steps**,
including the descents, boss/sac/wave mechanics, the full lift ride, event 50's actual outdoor arrival and native
onLeave restoration of all four characters' SP to 388. This replaces the old deferred leave-callback check.

Evidence for this revision is in [`review/fixes01/`](review/fixes01/): author/compiler, native geometry readback,
Lua checks, stage and scenario logs. The original integrator sheet remains in `review/build01/`; the earlier
Blender preview is supplementary historical evidence only. No new screenshots were attempted or captured in
this sandbox. Native appearance, birth-pit readability and Wizard Eye review await the integrator.

Staging completed successfully on retry (`stage_retry.log`). The first attempt stopped on another builder's
D16 item 11113 (`ground: belt1`); the shared binding was subsequently corrected to `item121` while this revision
was being verified. D9 did not edit that entry. The five installed D9 runtime files match the project byte-for-byte
(`staged_files.json`). The complete stage also activates the real Brood Spires round-trip.

The final **`rebuild_all.sh --scenarios-only` returns 1: 51 PASS, 3 FAIL, 1 declared WIP-FAIL** (55 scenarios).
D9 and `hesper_out3/brood_round_trips` both pass against the complete stage. Remaining failures belong to other maps:

- `hesper_out4/crown_entrances`, step 15: expected Crown after leaving D7, still in D7.
- `hesper_out4/crown_edges`, step 22: requested Scour/source 1 instead of Crown/source 0.
- `hesper_d08/d08_main_path`, step 96: outdoor Foundry event 53 activation fails.
- Declared WIP: `hesper_d05/relay_spire_climb`, step 45: unbound face 848.

The final queue is `review/fixes01/rebuild_scenarios_retry.log`; individual failure logs are copied there as
`shared_*.log`. The earlier queue ran across the incomplete stage and is retained only as diagnostic history.
No full shared rebuild, engine changes, `assets_dev` writes, Vulkan runs or Git staging were performed for this revision.

## Walkability and room shapes — 2026-10-24

The local native audit is clean with no allow-list entries. The three root descents use 32 × 24-unit risers,
starting past the doorway reveals; their thin sloped undersides preserve the lower-ring underpasses. The Royal
Tunnels use 88 × 16-unit risers beneath a continuous sloping ceiling. Resin lips and root rails close the sheer
sides. The nursery, spawning, cistern and Mother's pools are 32 deep. The Sump keeps its 200-unit depth with a
railed escape ramp and no floor beneath it; each 256-deep Birth Pit has a 16-step western exit and bottom landing.
Low bone litter stays below the climb limit. Nearby packs now stand clear of vats, channels and stairs; the three
Brood Sacs retain their sockets, supported by small cradle stalks inside the boss/cradle silhouette.

Eighteen authored footprints have corner cuts, including the Molt Hall's signature octagon. Eleven rooms have
hipped roofs, and the stairs have sloped ceilings/undersides. The native survey counts **29/40 non-orthogonal
rooms**, **17 sloped ceilings**, **93% axis-aligned wall area** and **0.9% ramp area**. The route, 42 occupied sectors,
17 movers, 96 actor identities/order and all 28 pickup positions/order remain unchanged. The rebuilt map has
8,282 faces and zero compiler warnings. No new art stand-ins or shared kit/audit changes were needed.

`make_walkability.py` writes `d09_walkability.yml` (24 pursuit fights) and `review_tour_walkability.yml`
(29 desktop poses). Evidence is in `review/walkability/`: before/after surveys, audit, native geometry checks,
Lua checks and contract comparisons. Shared-stage validation is pending the exclusive stage lock.
The integrator captures the tour; this sandbox cannot capture screenshots.

### Hellhound placement (2026-10-26)

R5-1 replaces all 12 Veteran Trooper records with Hellhounds (10301), preserving actor
indices and event groups. Group 1 is a three-hound Sinkhole Descent pack. Group 20's four
hounds move from the barracks to the Royal Tunnels' flat lower landing (z=-2944, y<0),
clear of the royal stair. The two Root Throat guards and three Royal Gallery hounds stay
with their Brute keepers. Every hound is mobile, including the former stationary guards.
Source events, behaviours and scenarios have no old monster-id references to replace.

Native R5 review widened the hound spacing to clear their full 2.8–3.2 m bodies, while retaining all actor indices and trigger groups. The royal landing uses x=155/445.

The pursuit cases also give the spawned test defender one physical damage to establish party aggro;
without that provocation the west-root Drudge remained idle despite a traversable stair.
