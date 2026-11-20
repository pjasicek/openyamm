# Hesper: D2 Pumping Station (`hes_d02.blv`)

The canyon's pumping station and side quest S2 (Pressure), built to its
[build document](../../../design/kreegan_world/zone1/dungeons/D2_PUMPING_STATION.md) with the shared Hesper indoor
kit (`../hesper_stage/blv_kit.py`, `../hesper_stage/blv_build.py`; see [D1](../hesper_d01/README.md)). Rooms,
links, markers and lights are the `d2` plan of `design/kreegan_world/zone1/dungeons/make_dungeon_plans.py`.

## Build

```sh
(cd level_generation/projects/hesper_d02 && flock -s ../../../output/hesper_stage/locks/stage.lock \
 timeout 1800 blender --background --factory-startup --python author_d02_blender.py)
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d02/build_d02.py              # compile, scene, Lua -> runtime/worlds/hesper
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_undervault/build_undervault.py      # its Water Works door reads D2's arrival
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py                # install into the shared Hesper stage (id 9104)
```

- `author_d02_blender.py` writes `source/`: the Canyon Gate behind its valve-wheel hatch, the ring of four grated
  galleries round the open cistern (one sector from −768 to the galleries' ceiling, four pillars, the intake sump,
  a ceramic balustrade), the 24-step stair down its west wall, the three brine planes, the three 3D valves, the Pump
  Hall down 8 steps with its three pumps, their pipes and the manifold (prisms, `blv_kit.prism` and `pipe`), the tool
  wall, the Filter Beds, the Water Works passage, the decorations and the light fixtures. Textures: the industrial set
  (design/kreegan_world/art/textures_interiors/masters, `hi*`).
- Each valve is two wall-mounted decorations: `hes_valve_body` (cog 30 + valve, its lamp red, then green as
  `hes_valve_body_open`) and `hes_valve_wheel` (clicked through events 3–5, its cog the same number), swapped to
  `hes_valve_wheel_turned`, whose binding turns it a quarter turn into place (`turn_in`, an engine binding option).
- The brine planes (z −256, −512, −640) carry the lava attribute and cog numbers 201–203; each valve hides the
  topmost one left with `evt.SetFacetBit`, and map load (event 1) re-hides the drained stages.
- `build_d02.py` compiles the BLV and writes the scene and Lua (handlers in `source/hes_d02.handlers.lua`; the
  hatch leads to Starport Reach's `station_arrival` from `out1_build.json`, the Water Works door to the Undervault's
  `water_works` arrival).

## Look and test

```sh
flock -s output/hesper_stage/locks/stage.lock \
 flock -s output/hesper_stage/locks/engine_build.lock ./tools/run_game.sh --isolated d2 --world hesper --map hes_d02.blv \
    --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d02/review_tour_01.yml" --seconds 0
```

`review/build02/sheet.jpg` is the latest tour. `drain_and_water_works.yml` (run from
`output/hesper_stage/scenario_run`) turns the three valves, walks down to the drained cistern floor, sets S2 (QBit
100102, S2 done by QBITS's formula; 100010 until 2026-10-23) at the filter console, goes through the Water Works door to the Undervault and back (the Undervault door's Pumping Station way, CR-P1-5). It passes (2026-10-23).
The filter console also clears 100222 (S2 given) and sets autonote 10414 (follow-up 25). `chests_and_cache.yml`
(2026-10-23, follow-ups 28 and 29): the drowned worker on the drained cistern floor (event 13, chest 3) holds the
Rebreather Helm (11106; worn, its stand-in icon is drawn whole over the doll until its paperdoll art), the sunken
locker an Engram and 10 000 gold (P4's ITEM_PLACEMENT), and the new cache in the Pump Hall's north-east corner before
the Filter Beds (event 14, chest 4) two Shield Cells and a Stim. It passes.

## Status (2026-10-23)

Built: the whole plan, the drain, the S2 console and the Undervault link, five chests (three fixed since 2026-10-23,
two random H1). Monsters and draining crawlers are installed (below); dedicated mechanism sounds remain pending.

## Monsters (2026-10-23)

The build places **20 actors**, following the explicit pack table rather than the outdated "22 and the boss"
headline: eleven Acid Crawlers (four initially hidden in the sump), three Brood Crawlers, two maintenance Seeker
Drones, three Glassback Pups and the Glassback Queen. No Kreegans. Slots 1/2 identify Crawlers/Drones with zero
random counts; the authored packs provide the population. `d02_build.json` records their groups, native sectors
and positions, including the Queen and two pups standing on the 32-unit filter beds.

Groups follow the seven plan marks. The **second distinct valve** reveals group 7's four sump crawlers; repeating
a valve does nothing, and later valves/reloads never respawn dead crawlers. Group 6 is the Queen (7,000 HP,
Energy/Light immune, unshielded). Her death sets map variable 4 and extinguishes L8. The Filter console refuses S2
while she lives, then retains the existing quest/autonote and Water Works progression. Load restores the dimmed
growth light and the drain state. L8 uses its negative individual light index, avoiding MM8 light-group semantics.

`d02_main_path.yml` kills the Queen, completes S2 and checks both exits; `d02_drain_crawlers.yml` checks repeated and
distinct valves, saves before/after release, kills the four crawlers and verifies that the third valve/reload keeps
them dead. The existing drain scenario now kills the Queen before its console. All focused checks, the existing
chest scenario and D1's supplemental `check_monsters.py` pass. That shared check verifies actual saved visibility
bits, native floor/ceiling clearance and staged boss rules. Geometry and arrivals were preserved.

All monsters use their approved staged models, including the Queen's crown/crest attachments. No new stand-ins.
Her staged row is melee-only: the prose's glass spit and charge are not defined in the current combat data and
were not invented here. The three pups use native room AI; there is no per-placement follow-the-Queen command.
No creature bindings, global monster tactics or engine code changed.

The required minimized, locked desktop smoke stopped before loading the map with
`SDL_Init failed: No available video device` (`/tmp/openyamm-desktop-d02_monsters_smoke-g5no2j7z/game.log`). Model
loading and visual/combat review therefore remain unverified in this sandbox. The integrator captures the ready
`review_tour_monsters.yml`; its final shot turns all three valves to expose the sump pack:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
 ./tools/run_game.sh --isolated d02_monsters --world hesper --map hes_d02.blv \
 --assets "$PWD/output/hesper_stage/assets_editor_dev" \
 --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d02/review_tour_monsters.yml" --seconds 0
```

Run headless checks minimized with shared stage and engine locks from `output/hesper_stage/scenario_run`.
Regression command: `level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only`.

The completed shared regression passed **76/76 scenarios**, exit 0, with no WIP failures. Summary: `output/hesper_stage/logs/d01d02_monsters_regression.log`. The final extended front-door round trips also pass in the focused logs (`monsters_hesper_d01_d01_main_path.log` and `monsters_hesper_d02_d02_main_path.log`). Design audit: zero findings; `assets_dev` status unchanged. Fixtures and scripted damage verify mechanics, not combat balance.

## Pickups placement (2026-10-24)

No stat containers; **10 colony satchels**, from 1,242 built faces (8 per 1,000, rounded and clamped to 6–20). Satchels at the Canyon Gate, outer edges of the gallery ring and Pump Hall supplies; none in the Queen's Filter Beds, cistern water or Water Works passage.

The author keeps the placements as `(room, event, x, y, z, facing)` rows and exports them in `semantic.json`
under `pickups`. Events equal cogs: satchels/bundles 751–760. The stage installs the map's
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

## R5 Gloamers — 2026-10-26

Added five Gloamlings (10320, actor indices 20–24, group 8) at the deep sump floor, z=-768. They share the
existing crawler group's visibility rule: hidden until two distinct valves drain the sump, then restored across
save/load. The Queen and every earlier actor are unchanged. The local build appends its own pack to the semantic
plan without editing the design generator.

`d02_gloamers.yml` drains the sump, saves/reloads and advances one minute with the party far away; all five remain
at their den with full HP and no target. The native-floor/saved-visibility check in the creature project verifies
all 25 actor floors and ceilings and group 8 before/after draining. Standard D2 scenarios pass.

The static walkability checker still reports six pre-existing step findings and nine apparent actor-floor failures:
four crawlers and these five Gloamlings beneath the initial brine plane. The drained native floor and runtime
check pass; no allowlist or checker rule was changed. `review_tour_gloamers.yml` captures the drained pack in [native OpenGL](review/gloamers/01-drained_sump.png).
The direct desktop wrapper succeeds; the earlier shell-wrapped attempt failed SDL initialization. Evidence and
resume details: [creature project](../../creatures/hes_gloamer_codex/README.md).
