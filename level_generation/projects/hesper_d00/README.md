# Hesper D0 Hangar Nine (`hes_d00.blv`)

The derelict lander the party repairs: an optional S dungeon under the crash crater's rim, quest M4 (Hangar Nine),
built to its [build document](../../../design/kreegan_world/zone1/dungeons/D0_HANGAR_NINE.md) with the shared Hesper
indoor kit (`../hesper_stage/blv_kit.py`, `../hesper_stage/blv_build.py`, as D1 and D2). Rooms, links, markers and
lights are the `d0` plan of `design/kreegan_world/zone1/dungeons/make_dungeon_plans.py` (the redesign of 2026-10-22).

## Rebuild

From the repository root, using the existing plans and socket models:

```sh
flock -s output/hesper_stage/locks/stage.lock timeout 1800 blender --background --factory-startup \
    --python-exit-code 1 --python level_generation/projects/hesper_d00/author_d00_blender.py
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d00/build_d00.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
```

- `author_d00_blender.py` writes `source/`: the rooms with 64-thick walls and a reveal through every opening; the
  Crew Ramp's slope and its cracked surface door; the aisle's crate stacks and the jammed cargo-door leaf; the Hangar
  Bay's bands, its shut roof doors (two movers in a shaft above the ceiling) and furniture; **the derelict lander**
  (a hull lofted from a ten-sided section with canopy and side windows, a lifted wedge nose, stub wings, a tail fin,
  drive pods, nozzles, a ventral shield band, cradle clamps, all in a 32-high cradle) and **its flight deck**, a room
  inside the hull through the side hatch; the five **sockets** (decorations on the hull, see below); the reactor core
  (eight `hcgener` ports), its breakers, terminal and the drones' charging cradles; the Control Stair (20 steps) and
  Hangar Control's gallery windows; the Fuel Depot's tanks and its acid pool (lava faces); the light fixtures and the
  monsters (the semantic record's `actors`).
- `build_d00.py` compiles the BLV, writes the scene (the actors from the Hesper monster rows, four chests) and the
  Lua (handlers in `source/hes_d00.handlers.lua`; the surface door leads to Starport Reach's `arrival` from
  `out1_build.json`). The `surface_door` arrival (7 600, 3 650, 482, facing south) is what `hes_out1`'s Crew Ramp door
  reads: keep it.
- The sockets' models: `level_generation/props/hesper_decorations/scripts/build_lander_sockets.py` (the hard-surface
  kit) writes `hes_sock_<cockpit|coil|nav|engine|ring>_<dead|ready|lit>` and `hes_light_pylon_off` into
  `work/hard_surface/`; bound in `../hesper_stage/decorations.yml`.

**The sockets** (MM6's Oracle alcoves): events 20–24, cogs 31–35, light groups 11–15, QBits 100004 (M4, the Pilot's
core) and 100040–100043 (the parts). The map's load event redraws them from the QBits and the power (map variable 1).
The power: breakers A and B (events 27, 28) or the reactor terminal for a technician (event 29). The practice
terminal and the reactor terminal check Hacking (`evt.CheckSkill`, Novice).

**Stage additions this map needed** (`../hesper_stage/`): `monsters.yml` 10054 (the Old Starport Turret on the Ward
Turret's model), `decorations.yml` the 16 socket and pylon models, `items.yml` (new) with `stage.py`'s Items section:
the five lander parts and the Engram as the world's items contribution, with stand-in icons. The drones (10050) and
crawlers (10090) were staged already. `blv_build.build` takes the map's `actors`.

## Look and test

```sh
./tools/run_game.sh --isolated d0 --world hesper --map hes_d00.blv \
    --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d00/review_tour_01.yml" --seconds 0
cd output/hesper_stage/scenario_run && ../../../build/game/openyamm --world hesper --headless-run-scenario \
    ../../../level_generation/projects/hesper_d00/d00_mechanisms.yml
```

- `review_tour_01.yml` (writes `review/build03/`, contact sheets `sheet_1.jpg` and `sheet_2.jpg`): every room
  unpowered, then the power on (console `mapvar set 1 1`, `event 1`), the Pilot's core and the parts fitted (their
  QBits), and last the Ion Coil fitted for real (`item add 11474`, `event 21`: the message and the Engram).
- `d00_mechanisms.yml`: the doors, the practice terminal refusing a party without Hacking, the range lever, the
  breakers opening Hangar Control, the sockets answering their clicks, the Pilot aboard (event 19 opens his talk from
  M4 done; The Harvester, a topic past his sixth slot, gives M8; since 2026-10-23 his list after M4 is exactly Black
  box, The stash, The repair list, The Harvester and Re-entry: no Planetfall and no Below the rim, so no second Pilot's
  Core, follow-up 32) and the cell charger's clicks. It passes. The charger's cells and its amber "Charging; come back
  tomorrow." the same day are checked in the game (console `qbit set 100004`, `qbit set
  100233`, `event 70` twice; 2026-10-23).
- `../hesper_out1/crew_ramp_round_trip.yml`: out through the surface door and back. It passes.

## Status (2026-10-22)

Rebuilt to the redesign: 12 rooms (16 sectors and the empty 0), 18 portals, 9 doors, 2 290 faces, 11 BLV lights and 65
decorations (28 of them light fixtures), 22 monsters, 4 chests, every interaction bound, no compiler warnings. The
training consoles of the first build are gone.

Since 2026-10-23 (P4's CR-P4-15, the integrator's follow-ups 13-15): from M4 done the flight deck console (event 19)
and Hangar Control's link (event 34) open the Pilot's talk (NPC 9001; his The repair list counts the parts); the
cockpit socket clears 100204 (M4 given); the cell charger (event 70, a machine panel on the flight deck's south wall
beside the hatch) gives one Shield Cell per character once a game day from the black box (100233) and M4, the day kept
in map variables 5 and 6. The socket lines are unchanged. Its lines are P4's since 2026-10-23 (follow-up 38): "The
lander's charger clicks open: a fresh Shield Cell for each of you." and "The charger's lamp is amber. Charging; come
back tomorrow." The gift plays the stage's `cell_charger` sound (the Hesper audio job); "Charging" is silent.

Not yet: the fixed chest items
(the Hesper weapons and the other engrams are not staged: random H1 for now), the Engram's use, a weathered skin for
the old turrets, the roof doors' launch (the finale), sounds. The headless runner's `grant_item` items are invisible
to the map's Lua, so the fitting is checked in the game, not headless.

## Lessons

- **Five floors at most.** The engine finds a point's sector from the first five floor-type faces under it
  (`findIndoorSectorForPoint`), sector by sector. The bay's floor, the cradle, the hull's roof and the roof doors'
  tops crowded out the flight deck inside the hull, so the party standing in it rendered as if in the bay. The roof
  doors have no top faces now; keep any room nested inside another sector's footprint under four floors of the outer
  one.
- **Headless items.** A scenario's `grant_item` does not reach `HasItem` in the map script; test item-keyed events in
  the game with the console (`item add`, `event <id>`).
- **Wait on the exact process.** A wait loop on `pgrep -f "cmake --build"` matched its own launcher's command line.

## Pickups placement (2026-10-24)

No stat containers; **18 colony satchels**, from 2,300 built faces (8 per 1,000, rounded and clamped to 6–20). Parts Store, office, militia post, firing range, aisle edges, bay perimeter, reactor, Fuel Depot, Hangar Control and ramp foot.

The author keeps the placements as `(room, event, x, y, z, facing)` rows and exports them in `semantic.json`
under `pickups`. Events equal cogs: satchels/bundles 751–768. The stage installs the map's
`_pickups.lua` sprite overlay automatically. All models and full/empty variants already exist; no stand-ins.

The map passes `treasure = 3` to the shared helper (H1). Its default lookup expects a filename,
but `GetCurrentMapName()` returns the display title; the explicit tier avoids that failed lookup without engine changes.

[`pickups.yml`](pickups.yml) checks native clicks, each stat supply group where present, two separated satchel
spots, save/reload and a repeat click. Item-roll state is covered headlessly; delivery to the hand remains the
shared mechanic's desktop check. [`review_tour_pickups.yml`](review_tour_pickups.yml) has the supply store and two
satchel views, writing to `review/pickups/`. This sandbox cannot capture; the integrator runs the tour.

All four batch-A authors flush outputs and use `os._exit(0)` after export; run them under `timeout 1800` and the
shared stage lock. On this sandbox use `/snap/blender/current/blender` in place of the Snap `blender` launcher.

Focused checks passed: `pickups.yml` (16 steps), native event/cog/model bindings and floor placement;
geometry, actors, chests, doors and arrivals preserved. Logs: `output/hesper_stage/logs/pickups_batch_a/`.

Shared sweep: **92/93 pass**; only the other batch's `hesper_d04/d04_key_path` fails at step 12, also on
focused retry. All Batch A scenarios and both audits pass (zero decoration-id or actor-size mismatches).
Integrator handoff: `design/kreegan_world/WORK_PACKAGES/requests/P4.md`, pickups placement, batch A.

## Walkability and room shapes — 2026-10-24

Hangar Nine's reactor plinth and pilot seat are 32 high. The Control Stair has 40 × 16 treads and a pitched
ceiling with 448 clearance. Four clipped bay corners form an octagonal hangar; the side compartments, reactor,
fuel depot and control gallery have clipped corners, and five rooms have hipped ceilings. The ramp foot has a
diagonal bend; the existing Crew Ramp retains its floor cut and pitched roof. The stair lamp and three Control
ceiling panels follow their new surfaces. The workbench and duty desk remain allowlisted furniture.

Final compile: 2,639 faces, 17 sectors including the empty sector, 9 movers and 83 decorations, with no compiler warnings.

Local runtime audit: **zero findings, two furniture exceptions**. Shape survey: 10/16 nonorthogonal rooms, 89% axis-aligned wall area, 8 sloped ceilings, 11.5% ramp area. Actor order, pickup order, event/cog bindings and door IDs are preserved.

Evidence is in `review/walkability/`: baseline/current audits, shape surveys, identity checks and private-stage scenario logs. `d00_walkability.yml` adds melee pursuit across the repaired spots. `review_tour_walkability.yml` covers the repairs and reshaped rooms; the integrator captures it on the desktop. No screenshot was attempted in this sandbox.

Built and installed in the shared stage after the Noble weapon export blocker was repaired by its owner. This map is now in `WALKABILITY_GATED`; its new fight scenario is included in `rebuild_all.sh --scenarios-only`. Initial tests used a private stage copy while installation was blocked. Final shared-stage regression results are recorded in the batch B report at the end of `design/kreegan_world/WORK_PACKAGES/requests/P3.md`.

Final regression: all 12 batch B scenarios pass. The full scenario inventory is **102/102 passing** after binary-startup retries and the concurrent D15 fixes, including its newly added fight scenario. Global decoration IDs, actor sizes and every walkability gate pass. The P3 batch B report distinguishes the original driver exit from the successful reruns and links the evidence.
