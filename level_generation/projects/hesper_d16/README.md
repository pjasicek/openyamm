# D16 — Lattice Node North

Built and staged as map **9133**, `hes_d16.blv`, on 2026-10-23 from D16 BUILD-READY and `plans_zone4.py`.
The [shared node module](../hesper_nodes_common/README.md) supplies the sixteen common sectors. D16 adds the
Capacitor Hall, the Graft split at y=7500, T2, the sixteen-facet creep mound, four grafted columns and three hollow
capacitor columns with exposed, breakable living cells.

The native map contains **20 playable sectors** plus empty sector 0, **2,512 faces**, 1,717 vertices, 48 portal
faces, seven doors, 38 actors (35 including the boss plus three cells), four chests, six loose cache items,
13 colony satchels and seven scrap bundles. The plan supplies **39 lights**: 29 fixtures and ten explicit lights. Compilation has zero warnings;
event faces, door ids, texture names and fixture light values pass the shared compiler's checks.

The quiet path, charge and cell-destruction paths, timed arc crossings, alarm waves, west shortcut, Conductor's
four ward stages, column darkening, heart shutdown, exact quest rewards, quiet-only vault and service tunnel are
wired. Completion requires all three columns shorted and the Conductor dead. It sets QBit 100014, clears 100214
and grants 40,000 experience per character once. The boss drops 11424/11332; the vault contains 11331/11113.
Incidental floor gold was removed in the pickups pass below.

## Build and stage

From the repository root. This sandbox requires the actual Blender binary rather than its snap launcher.
The author exits after export to avoid the host's Blender shutdown crash; inspect `review/author.log` for a
traceback and the saved outputs before compiling.

```sh
mkdir -p output/hesper_stage/locks level_generation/projects/hesper_d16/review
SDL_AUDIODRIVER=dummy ALSOFT_DRIVERS=null XDG_CACHE_HOME=/tmp/d16-cache \
 flock -s output/hesper_stage/locks/stage.lock /snap/blender/current/blender --background --factory-startup \
 --python level_generation/projects/hesper_d16/author_d16_blender.py \
 > level_generation/projects/hesper_d16/review/author.log 2>&1
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
 python3 level_generation/projects/hesper_d16/build_d16.py
flock output/hesper_stage/locks/stage.lock \
 python3 level_generation/projects/hesper_stage/stage.py
```

The project writes its Blender/GLB/geometry/doors/semantic sources, compiled native map, scene, generated Lua,
four behavior variants from `source/conductor.lua`, effect library and `d16_build.json`. Edit authored sources,
never the generated runtime Lua. Shared registrations add map 9133, monsters 10109/10142, items 11113/11424 and
this map's rebuild/scenario entries. Existing decoration bindings and textures are reused.

Reread shared files immediately before small additive edits, preserving other builders' entries. Stage writes
hold `stage.lock` exclusively; every game run holds `engine_build.lock` shared, and also takes `stage.lock`
shared to prevent installation during loading. No engine build or lighting bake was needed.

## Tests

```sh
(cd output/hesper_stage/scenario_run && \
 for scenario in d16_main_path d16_columns d16_hazards d16_pickups; do
   OPENYAMM_START_MINIMIZED=1 \
   flock -s ../locks/stage.lock flock -s ../locks/engine_build.lock \
   ../../../build/game/openyamm --world hesper --headless-run-scenario \
     "../../../level_generation/projects/hesper_d16/$scenario.yml" --scenario-no-color || exit 1
 done)
python3 level_generation/projects/hesper_d16/verify_d16.py --saves
python3 design/kreegan_world/data/audit.py
level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

All three D16 scenarios pass:

- `d16_main_path.yml`: 101 steps. Pylon, physical route through the clean hall/Graft/T2/T3, walk across the mound,
  quiet column shutdowns, actual indoor Meteor Shower projectile, live/dead save/load, boss drops, experience,
  quest bits, vault items, initial supply states, west shortcut and service tunnel. Both exits return from the Crown.
- `d16_columns.yml`: 63 steps. Actual charge pickup and consumption, mixed terminal/charge/cell destruction,
  rejected unskilled/no-charge controls, all three cells killed without Hacking, boss-first completion gate,
  fused vault, service opening, alarm wave and persistence.
- `d16_hazards.yml`: ten steps. Native walking across the same arc during live and safe phases; only the live
  crossing damages the party.

`verify_d16.py --saves` checks the compiled/staged contract and the actual serialized actor behavior, ward radius,
duration/timer, spell/chance and individual column light states from all four quiet stages and both mixed stages.
It intentionally recognizes the current version-100 save layout and fails if that format changes. The plan's
ceiling/light-overlap checks pass; design audit reports zero findings. Review logs are in `review/`.

The scenario-only regression completed with **62 PASS, one FAIL and one existing WIP-FAIL** (exit 1).
The blocking failure is `hesper_out2/scour_edges`, step 22: the Crown return-boundary check expected source 1
and `hes_out2.odm`, but received source 0 and `hes_out4.odm`. D5's `relay_spire_climb` fails at step 45 under
its existing non-gating WIP classification. These other-map tests were not edited. See `review/regression.log`
and `output/hesper_stage/logs/scenarios_150826_3/`. An immediate isolated, locked rerun of `scour_edges`
**passes all 24 steps without changes** (`review/scour_edges_recheck.log`). Thus every gating scenario has a passing
result, but the complete suite exited 1 and the intermittent boundary failure remains for the integrator to investigate.
The shared option `common_contents(..., coupling_geometry=False)` suppresses only the default coupling stems and
clickable collars so D16 can supply hollow columns. Its default is unchanged. Every D6 project file still matches
the pre-build SHA-256 inventory; D6 is not rebuilt. All three D6 scenarios pass in that regression run.

These mechanics tests use high-level fixture parties, direct scripted boss/cell damage and disabled actor AI on
some movement segments. They do not establish encounter balance, visual quality or fair targeting of the cells.

## Arrivals and state

`blast_door` is (4800, 300, 0), facing 90°; `service_tunnel` is (3424, 12200, -512), facing 270°.
Exit events 50/57 read `d16_door`/`d16_hatch` from `hesper_out4/out4_build.json`; no destination coordinates are
invented. This builder did not edit or rebuild the Crown. Its independently updated staged links became available
during testing, and both D16 → Crown → D16 trips pass using the Crown's generated door poses.

| Variables | Meaning |
|---|---|
| 1–3 | Column state: 0 live, 1 terminal shut, 2 charge/cell blown |
| 4 / 5 | Pylon silenced / alarm raised |
| 6 / 7 | Boss dead / heart dead and reward granted |
| 8 / 9 | Arc phase / reinforcement seconds |
| 14 / 15 | First-entry text / west shortcut unlatched |

Timers 3–5 tick once per real second (30 game seconds). Light groups 21–23 belong to individual columns; 1 and 3
switch off with the heart, group 2 switches on. The mound/vent orange lights persist. Door ids 1–6 and common
events follow the skeleton; D16 adds door 7/event 58 to T2 and event 153 polls cell death. The four Conductor
behaviors implement radius-500 wards for 10/10, 6/12 and 4/16 seconds, then no ward. Casting remains native indoor
Meteor Shower, Master 14, chance 30% in stages 3–1 and 45% in stage 0; no Lightning Bolt fallback was needed.

## Stand-ins, deviations and integrator decisions

- No texture stand-in was needed: K9, K3 and the referenced K4/K5 masters exist. Existing shared greybox coils and
  the dark pylon are reused; amber colonial wall lights stand in for tunnel lamps and resin vent glows.
- Existing Trooper C models stand in for Hulks/Nobles, D5's Overseer model for Court Overseers, Ward turrets for
  Sentinels and the three living cells, and a native winged DemonFly C sprite for the Conductor at 1.3 scale.
  The conducting staff/body and cell art remain outstanding. The Belt/Baton use native ground shapes item121/item083
  with their Hesper icons and gameplay ids.
- No resin-strand model exists. Three simple resin prisms on each of the four specified grafted columns stand in
  for drips/strands. Eight existing static creep pods use provisional outer-wall positions clear of doors and mound.
  The design supplies no pod/strand placement marks; approval of these anchors was requested, with no reply before
  handoff. Please confirm or replace the provisional placements recorded in the author script and semantic file.
- The staff/warning effect uses violet native spark particles. Column-to-staff connecting arcs are absent: the
  current actor `effect` call has no moving beam endpoints, and the sprite stand-in has no staff attachment.
  Dedicated grafting/hum sounds are also absent; existing charge, shield, impact and machine sounds stand in.
- The Conductor has the specified `immobile` placement and 1,400 post leash, stage AI types, no flee, 5,000 shield,
  four-second shield regeneration and no Blink. Native post behavior may move to fight even at stage 3;
  `setAiType` changes aggression, not immobility or speed. Strict stage-3 stillness and progressively faster movement
  cannot be promised by this data-only build. An integrator decision is needed before adding engine support.
- Existing shared tactics were preserved: 10041 and 10032 lack the requested post tactics, and 10042 uses 1,536
  rather than the Graft's 1,500 leash. The two different Hulk wander radii also lack per-placement overrides.
  Sentinel traverse is now 90°/s in the integrator's shared row. Hacking checks the current character; the event
  API does not charge the specified console recovery time.
- H3's consumable/salvage pool is not staged. The three random containers use native T6 with average design gold:
  18,000 in T1, 12,000 in the galleries and Graft. The pod's salvage-heavy distribution awaits the pool.
- The specified 640-high hall banks exceed their 512-high room: banks are 448 high and omitted where they would
  block doorways (five remain). Common consoles stop 64 below the ceiling rather than at the impossible height 900.
  Ramp fixtures follow the slope. The generated light table contains 39 lights, despite prose saying 36; the build
  follows the table. Eight simple common sectors are below the 100-face target (16–98); none exceeds 300, and no
  decorative subdivision was added just to raise the count.

## Review handoff

**Screenshots, `review/build01/sheet.jpg`, Wizard Eye/automap inspection and visual sign-off are deferred to the
integrator because this sandbox cannot capture.** `review_tour_01.yml` contains ten poses, including the clean
hall, Graft and columns. Run it minimized against a fresh map, then repeat the core/vault/tunnel after loading
`d16_dead_node` from the main scenario to inspect shutdown lighting and the quiet vault.

```sh
flock -s output/hesper_stage/locks/stage.lock \
 flock -s output/hesper_stage/locks/engine_build.lock \
 ./tools/run_game.sh --isolated d16 --world hesper --map hes_d16.blv \
   --assets "$PWD/output/hesper_stage/assets_editor_dev" \
   --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d16/review_tour_01.yml" --seconds 0
```

No new decoration GLB was created; reused models retain their existing checks. Final art, encounter balance,
the provisional dressing, behavior/tactics limits and loot pool require integrator review.

## Pickups placement (2026-10-24)

13 colony satchels and seven Kreegan scrap bundles (2,512 faces; total density capped at 20), no stat containers.
Colony supplies occupy the vestibule, clean Guard Hall/galleries, T1/T3 and service tunnel. Bundles sit by the
grafted Guard Hall wall, east gallery creep and Graft edges; the Core has none.

[`pickups.json`](pickups.json) records every position and event/cog id; the author exports them into the map.
The shared pickup mechanic supplies colours, opening, rewards and refill. All four batch-C maps are H3 and pass
`treasure = 6`: `evt.GetCurrentMapName()` currently returns the display name, while the shared automatic lookup
expects the filename. No shared mechanic or engine change is needed for this explicit setting.

The two incidental fixed floor-gold piles were removed under PICKUPS.md. The six themed cache items, chest contents and boss rewards remain.
No pickup models or textures needed stand-ins.

[`d16_pickups.yml`](d16_pickups.yml) tests actual clicks at the placed models and their resulting map variables. [`review_tour_pickups.yml`](review_tour_pickups.yml) supplies the storeroom and two supply views for the
integrator; captures remain with the integrator. `review/pickups/placement_checks.json` records floor support,
clear footprints and unchanged compiled geometry. Build and scenario logs are in
`output/hesper_stage/logs/pickups_batch_c_20261024/`.

Validation: the four builds and stage passed; all **17 batch-C scenarios** and the complete
`rebuild_all.sh --scenarios-only` sweep (**93/93**, exit 0) passed. Both decoration-id and actor-size audits
report zero mismatches across 22 maps; the design audit has zero findings. Final suite logs:
`output/hesper_stage/logs/scenarios_082633_7/`; summary: `pickups_batch_c_20261024/validation_summary.json`.

## Walkability (2026-10-24)

Authored and compiled with zero warnings. The local runtime audit is zero, with no exceptions.
The shared node shell now has chamfered vestibule/hall/terminals/core and hipped ceilings; the guard dais
uses 16-unit stairs with solid side parapets. D16's T2 creep floor follows the trimmed footprint; the three
capacitor columns meet the raised roof while their cell positions and gaps stay unchanged. Seven actor
positions clear the stairs, pipes, arc posts and console. Identities/order, events, doors, cogs, pickups and
arrivals are preserved. Survey: 10/18 non-orthogonal rooms and 11/18 sloped ceilings. Light overlap: at most three.

Built, staged and audit-gated. All five focused scenarios pass: six pursuits in `d16_walkability.yml` (216 steps),
main path, columns, hazards and pickups. The final staged audit remains zero. Evidence: `review/walkability/`; logs: `output/hesper_stage/logs/walkability_batch_d/`.
`review_tour_walkability.yml` covers the repaired floors, rooms, mound and column gaps. Screenshots remain
with the integrator. No new art or stand-ins.

Final batch-D sweep: `rebuild_all.sh --scenarios-only` **108/108 PASS, exit 0**. Decoration and actor-size
mismatches: zero. All five batch maps' staged walkability audits are zero and all five are gated.
Logs: `output/hesper_stage/logs/scenarios_174417_3622123/`; batch summary:
`output/hesper_stage/logs/walkability_batch_d/validation_summary.json`.
