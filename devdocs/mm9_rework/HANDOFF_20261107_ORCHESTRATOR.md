# MM9 rework: orchestrator handoff (2026-11-07, 16:30)

For the Claude session taking over the MM9 rework from the orchestrator session of 2026-11-06/07. Read this first, then
[README.md](README.md) (plan, decisions, which `devdocs/mm9/` records are current) and AGENTS.md / CLAUDE.md.

The user plays the rebuilt MM9 maps and reports problems with a screenshot, a position line (`map="..." position=(x,
y, z) ... yaw_radians=... pitch_degrees=...`) and sometimes a save name. The orchestrator routes each report to a
sub-agent, checks the result, rebuilds all maps once per batch of fixes, promotes into `assets_dev` and tells the user.
The user's quota is tight (3 % left on 2026-11-07): finish existing work, avoid new sweeps or broad audits unless asked.

## 1. Where things stand

- **`assets_dev` holds R7** (promoted 2026-11-07 ~17:10): all 44 MM9 maps rebuilt with every fix of 2026-11-07,
  including the three in-flight items of section 2, which are all finished (results in section 8). R7 converted the 44
  maps in 9 minutes; 174/174 map scenarios passed; the exit check is clean (section 3); the user-pose tours (section 5)
  were captured from `assets_dev` after R7 and checked. Backups: `output/mm9_rework/promotion_r7_20261107/backup/`.
- **Nothing is committed or staged.** The user reviews and commits. Never `git add/commit/stash/reset/restore --staged`.
- `assets_dev/worlds/mm9/` is git-ignored as a whole (including `world.yml`); MM9 content ships through its packaging,
  not git.
- The user's `settings.ini` had `smart_click=true` from 09:46 to ~16:15; the user removed it. Headless scenarios read
  the repo-root `settings.ini`, so with smart click on, `press_action: attack` does nothing (maw_bow_disabled,
  turn_based/single_press_one_member, mm9/destructibles/sturmford_chain_crosshair fail). Not a code bug.

## 2. In flight on the afternoon of 2026-11-07 (all three finished and promoted in R7; kept for the record)

If the orchestrator session has ended, these agents ended with it. Check their output and the working tree; redo what
is missing. None of them was allowed to promote.

1. **Converter speed (top priority, the user's request).** Profile `convert.py` (Lindisfarne ~27 min; Sturmford City;
   a dungeon) plus the layout and lightmap-transfer steps, then speed up the hot spots (numpy, spatial indexes instead
   of all-pairs loops, per-process caching, multiprocessing inside a map, maybe stage caching keyed on input hashes)
   with **byte-identical output** (proved on Lindisfarne, Sturmford City, Boot Camp and two dungeons, plus their
   scenarios). Its scratch runs: `<scratchpad>/runs/v1`, `runs/v2prof`, queue scripts `q.sh`, `qp.sh`.
2. **The last six wrong-sector props + low lightmap coverage.** Props: two wall lanterns, a tapestry, a lamppost
   (floor belongs to a lower room) and Sturmford City's anvil and hammer (the doorway-floor pass gives them to the
   street); audit `level_generation/projects/mm9r_common/sector_audit.py` (two false alarms: an axe, a gate fire).
   Lightmap `coverage_core`: Drangheim City 0.23, Mountain Pass 0.0 (both unchanged since R4/R5; others 0.84-0.99):
   find what it means in game, fix or justify. Captures: `output/mm9_rework/sector_props_20261107/`.
3. **Thorolf in five more cities + friendly NPCs in doorways.** Thorolf (NPC378.scr: runs up to the party and talks,
   key 83 gate in Frosgard City) was ported through one shared converter helper into six cities' Lua; only Frosgard
   City is tested. Add a scenario per city through each `make_scenarios.py`. Doorways: friendly MM9 NPCs now block the
   party (user decision below); measure whether town NPCs idle in doorways/narrow passages and, if so, make them
   MM9-faithful (step aside / do not idle in portals). MM6-MM8 keep walk-through.

When all three are done: **one** full rebuild (R7), scenarios, promotion, then the user-pose tours (section 5). Do not
let each agent rebuild every map on its own (that is what made 2026-11-07 slow).

## 3. How to rebuild and promote

- **Review roots**: A = `output/mm9_rework/assets_dev` (dungeons and cities), B =
  `output/mm9_rework/isleofashes_blv_root` (the 12 regions `*_blv`, Afterworld, Isle of Ashes). Each has an owned
  list (`output/mm9_rework/owned.txt`, `isleofashes_blv_owned.txt`); `level_generation/projects/mm9r_common/
  review_root.py` `refresh()` relinks everything not owned from `assets_dev`.
- **Full rebuild script**: `output/mm9_rework/final_r7_20261107/r7.sh` (copy to `final_r8_<date>/r8.sh`, replace the
  `r7`/`R7` names; it also builds `mm9_compile_indoor_source`). It builds `openyamm openyamm_unit_tests openyamm-editor`, runs the unit suite, refreshes both
  roots, runs `convert_one` for all 44 maps in parallel through the map lanes (`convert.py`, then
  `mm9r_common/dungeon/lighting.py <project> --layout-only --no-install`, then `mm9r_common/lightmap_transfer.py
  <project> --install`; regions add `--root output/mm9_rework/isleofashes_blv_root`), then every
  `level_generation/projects/mm9r_*/scenario_*.yml` (12 in flight). Summary lines: `DONE <map> <time> coverage`,
  `CONVERT|LAYOUT|TRANSFER FAILED <map>`, `conversions done`, `scenarios: X of Y passed`, `FAIL <name> | ...`, `R6_DONE`.
  Run it detached (`setsid nohup bash r8.sh > r8.log 2>&1 < /dev/null &`) and watch the log. ~15 min in all.
- **Promotion**: `output/mm9_rework/promotion_r7_20261107/promote.py` (copy into a new `promotion_r8_<date>/` folder
  and change its `BACKUP` line so backups don't mix). Plan first (`python3 promote.py`, writes `plan.txt`, `merged/`,
  `promote_list.txt`, `delete_list.txt`), read the plan, then `--write`. It merges the MM9 tables per owner
  (map_transitions, transport_routes, map_stats, texture_frame_data, liquids, painted-map catalog) and deletes
  unreferenced old MM9 textures. Backups: `promotion_r*/backup/`.
- **Exit check**: `promotion_r7_20261107/check_exits.py` (copy alongside): expect "transitions: 105, arrivals checked:
  92, problems: 13". The 13 name MM9 start points the scenes do not list; the engine places the party by the arrival
  coordinates, so they are known and harmless.
- **After promotion**: run a few scenarios against `assets_dev` (the changed maps', `tests/scenarios/mm9/*`,
  `tests/scenarios/release/rebuilt_map_save.yml`) and the non-MM9 regression set (all of `tests/scenarios` except
  `mm9/`; `final_r5_20261107/regress.sh`). Expected non-MM9 failures: the 11 stale MM6 drafts (`main_story_draft`,
  `mm6_main_story_full_recorded_playthrough`, `probe*`), which fail on the last commit too.
- **Unit tests**: expected failures belong to other sessions: MAW skill popup text (`MawAuditCombatSpellTests`) and the
  staged Hesper missiles (`WorldMissileTests`).

## 4. Tools and rules that cost time to learn

- **Job lanes**: `output/mm9_rework/tools/heavy.sh` (`build <cmd>` one build at a time; `map <stem> <cmd>` one job per
  map, maps in parallel; `job <cmd>` other heavy work; at most 6 heavy jobs). Lock dir `HEAVY_LOCK_DIR` or
  `output/mm9_rework/tools/locks`; every agent of one orchestrator must use the same one. Brief agents with the exact
  path. (The 2026-11-07 agents used the orchestrator's scratchpad copy.)
- **Stuck check**: `output/mm9_rework/tools/stuck_check.py` (set `STUCK_SESSION_DIR` to your session's folder): finds
  wait loops that can never end. Never wait with `pgrep -f <text>`: the waiting shell's own command line matches. Wait
  on a PID (`kill -0`) or a file the job writes.
- **Old-import inputs** come from `assets_editor_dev/worlds/mm9/maps` and
  `level_generation/projects/mm9r_common/original_tables/`, never from `assets_dev` (which holds the rebuilt maps).
- Hard-linked files (review roots, tables): write a temp file and rename it into place.
- Game runs by agents: `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated <unique> ...`; `--visible` only for FPS.
  Desktop input tours exist (`debug.menu_input_tour_path`, tools/RUN_GAME.md): agents can press keys and click.
- Load a user save headlessly: a scenario with `new_game_flow: {}` then `load_game: {name: x, path: saves/saveNN.oysav}`.
  A save's name is in its first 4 KB (`head -c 4096 saves/saveNN.oysav | strings`). To read a Lua state value, a
  `lua_event` that calls `error('PROBE ' .. tostring(...))` prints it in the failure line; `evt.Debug` prints nothing
  headless. Quest keys: MM9 raw key k = QBit 90000 + k (`assert: {qbit_set: [9xxxx]}`).
- Never edit generated Lua (`assets_dev/worlds/mm9/events/maps/*.lua` comes from the converters, including the
  hand-ported Isle of Ashes `regionlua.py`); fix the generator. Scenario YAMLs are generated by each project's
  `make_scenarios.py`; change the generator, not the YAML.
- After a converter change, other maps change too: regenerate the affected maps' scenarios when door ids shift.
- No Vulkan builds. Install models only via `tools/install_model.py`. MM6-MM8 must not regress: check them after any
  engine change.

## 5. Verify at the user's poses before saying "fixed"

`output/mm9_rework/user_report_poses/`: one screenshot tour per map built from every pose the user reported
(`bootcamp`, `isleofashes`, `sturmfordcity`; README has the command). After each promotion capture them all from
`assets_dev`, look at every image, and add each new report's pose. On 2026-11-07 a sub-agent reported the Ravensford
hall windows fixed while its "after" captures showed a door and a pillar; reject such reports. User saves named so far:
RF-1 = `saves/save85.oysav` (Ravensford at night), IOS_1 = save84, IOS_FRAMES = save89 (the 9 FPS skeleton fight),
DC_PORTAL, AK_DOOR_NOT_OPEN, KLUSO_1, SF_DIALOGUE, BOB_1/BOB_2 (older).

## 6. User decisions (keep them)

- Windows exactly as MM9: see-through only where MM9 flags the surface Translucent (0x8, x texture alpha x brush
  Alpha); everything else opaque with nothing behind it; per-texture `glass:` lists only tune flagged faces
  (devdocs/INDOOR_TRANSLUCENT_FACES.md). This replaced the earlier "dirty glass" choice.
- Walking townsfolk keep the indoor AI activation range (10,240 units from the party, as original MM9): walkers placed
  or heading beyond it wait until the party comes near (user decision 2026-11-07, keep it).
- Friendly MM9 NPCs and animals block the party (`friendlyActorsBlockParty: true` in MM9 `world.yml`); MM6-MM8 walk
  through them.
- MM9 has no MMerge street-NPC talk (`streetNpcs: false`): unscripted actors (dogs, cats) are silent.
- Dialogue opens with E and Space; LMB only with the "smart dynamic" LMB setting.
- Rain on all outdoor regions and cities with roof masking; thunder only with rain. New Sorpigal's meadow settings for
  the regions' grass. MM9 sounds for all MM9 actors.
- Saves of a rebuilt map reset that map's state deterministically (devdocs/SAVED_MAP_STATE_IDENTITY.md).
- MM9-faithful script behaviour wins over convenience (e.g. Dragon Stadium spawns continue after the dragon dies; the
  Isle needs two trips to Yrsa because her door topic needs key 29 from Forad).

## 7. Fixed on 2026-11-07 (all generic: shared converter or engine, all maps)

Faces given to the wrong room (sky through wall bases, cracks, window frames, missing walls, floor strips; `rooms.py`
`back_room`); double-door pairing; windows by MM9 flags, opaque `OPQ` texture copies without alpha holes, Clouds1
glass found through invisible shells and its own alpha not applied twice; region nights (MM9's huge open-air lights
fade with the sun; engine `indoorOpenAirLights` + `lightmap_transfer.py`); wrong-sector props (81 → 8; floors take
the room of the air above them, props lifted onto their floor, decoration sector found 32 units above the base);
region props' DAT names (pose, base, drop to floor); the bridge-deck floor rule (`IndoorMovementController.cpp`,
skips trigger plates and movers); dogs silent; friendly NPCs solid; Forad's greeting voice, his walk-up talk in
Frosgard City and Thorolf's (`evt.OpenMm9Rude(rude, actor)`); the sector face grid listing sliding movers only along
their travel (Isle of Ashes 9 → ~840 FPS); window breaks no longer rebuilding all face batches (98-219 ms → 4 ms);
editor links again; vendor-stock test at generation version 4; Ruined Temple and Hall of the Gods scenario generators.

## 8. Still open (beyond section 2)

- Item 2 of section 2 finished (2026-11-07 ~17:00): the "six props" were audit false alarms (`sector_audit.py` now
  copies the engine rule: 0 real cases); a new engine rule in `MapAssetLoader.cpp` lets a fully listed decoration keep
  its listed room when the found sector has no floor under it (no MM6-MM8 change). Drangheim City's patches are
  vertex-lit like their neighbours (coverage 0.945); Mountain Pass has no lightmapped faces (null). Captures:
  `output/mm9_rework/sector_props_20261107/`. Found then fixed (promoted ~17:40 as "R7b",
  `promotion_r7b_20261107/`): the sunk bookcases were Bookcase models missing from `prop_pose.py` `BASE_AT_POS` (four
  in Thjorgard City, one floating 222 units in Thronheim City; listed props now settle onto a floor or prop top at most
  24 units below, `BASE_SETTLE`); bright decorations and creatures at night in every region came from sampling the huge
  open-air lights at full strength, now dimmed in the lighting frame by the faces' factor (engine; MM6-MM8 unchanged).
  Captures: `output/mm9_rework/last_two_20261107/`. `worlds/mm9/textures/YANM7QVOPQ.bmp` is an unused leftover in the
  review roots' owned lists: each promotion adds or deletes it; harmless, drop it from the owned lists when convenient.
- The hand-kept `BASE_AT_POS` model list is gone (promoted ~18:30 as "R7c", `promotion_r7c_20261107/`): a generic
  rule, `prop_pose.stands_by_base`, stands every upright MoveToFloor-0 prop on the surface its DAT Pos lies on (4 units
  under to 24 over) by its base, else keeps its height; the old list's 506 instances are identical, 417 other props
  on 27 maps changed (317 audit flags removed, 1 added: Dark Passageway's Prop18 bush on a slope). Not fixed: Frosgard
  City's Spikes2 is invisible in MM9 but drawn by us (in the throne-hall fire). Verhoffin Ruins' scripted scenario is
  flaky since another session changed its Zombie into a Terror (fails with or without the rule).
- Item 3 of section 2 finished: Thorolf works in all six cities (the five untested ones showed him on key 106 alone;
  MM9 shows him with 83 until 84 there, `citylua.py`), each city has a generated `scenario_thorolf.yml` (33/33 city
  scenarios pass; those five cities are reconverted into the review root, not promoted yet). Friendly NPCs never block
  a doorway: all townsfolk are placed immobile, Sturmford's wandering dogs and cats never stood in a passage over 15
  minutes, and the one closed nook (Tymon the Nord, Thjorgard) is MM9's own placement. No engine change.
- Item 1 of section 2 finished: the converter is 7-15x faster on the regions with byte-identical output (Lindisfarne
  1297 s → 88 s, Frosgard City 758 → ~105 s, dungeons/cities under a minute; transfer Isle 157 → 20 s): array filters
  and indexes for the water/liquid bed checks, cached portal boxes, parallel solid voxels, the camera gate's ray terms,
  and an early exit in the compiler's BSP partition search (`mm9_compile_indoor_source`, now built by the rebuild
  script). Details: DUNGEON_PLAYBOOK.md "Build speed". R7 (`final_r7_20261107/`) is the first full rebuild with it.
- The review roots' `worlds/mm9/world.yml` was an owned stale copy (old guberland.odm start, no `streetNpcs` /
  `friendlyActorsBlockParty`); it is no longer owned and both roots link `assets_dev`'s file (2026-11-07 ~17:30).

- Kluso's House shelf items and weapons cabinet: they match MM9's placement data; needs an MM9 screenshot to judge.
- Fires lit only by a map's own script keep their starting sound; once-per-switch sounds; reverb.
- Dark Passageway tube swim-out; Frosgard City sea and the regions' far seas have no seabed.
- Small floor overhangs left: Drangheim City 18, Boot Camp 4. Yanmir Bench0 duplicate DAT name.
- Dragon smoke snout position not visually checked; battle music uses the yellow-alert track as a stand-in.
- Boot Camp frame rate dropped from ~1,400-1,800 to ~950-1,300 FPS (VSync off) because the hall windows now show the
  rooms behind them; acceptable so far.
- Bridge-trap sweep: 83 static candidates on 19 maps, 59 crossed by a walk probe, 24 unconfirmed.
- openyamm-95 (another session) owns the MM9 balance gate (`mm9_balance_report.py --gate --mm9-source scenes`); ping
  it after a promotion.

## 8b. Next tasks (the user's priorities, 2026-11-07 evening)

1. **Reverse-engineer MM9's real prop placement** (Rizin + rz-ghidra, see re_mm8/RIZIN_GUIDE.md for the workflow; MM9's
   executable and LithTech's Prop/model code): how the engine turns a Prop's DAT Pos, Rotation, Scale, MoveToFloor and
   the ABC model (origin, dims box) into the drawn mesh position. MM9 shows its props correctly with no per-model or
   per-map fixups, so one rule exists. Today's `prop_pose.stands_by_base` (4 under to 24 over a surface) and
   `BASE_SETTLE` were **inferred from data, not from the engine**; replace them with the engine's rule and diff all 44
   maps (the old list's 506 instances must stay identical). The same applies to the open-air light cut-off (radius
   1900, `indoorOpenAirLights`): find how MM9 itself treats those lights, if at all.
   **Answered 2026-11-07 evening: see [MM9_PROP_PLACEMENT_RE.md](MM9_PROP_PLACEMENT_RE.md)** (the engine pushes a
   `Prop`'s dims box out of the world when it gets its dims; the base lands on the floor; non-Prop classes are not
   pushed). **Corrected later that evening:** the push-out was the wrong mechanism. MM9 lifts every non-AI ModelObject
   (the Prop family, items, chests) by its model's first-animation dims y minus 1 LT unit at its initial update, with no
   collision (object.lto `0x100beb20`); the same document now holds the full trace. Implemented (`prop_pose.lift`,
   `lifted`), built as R8b into the review roots (171/174, the three failures pre-existing), checked against a real
   MM9 screenshot. **Promoted ~22:20 as "R8b"** (`promotion_r8b_20261107/`, backups there) together with the balance
   session's (openyamm-83) reconversions of 11 maps for new density targets: exits 105/92/13 as expected; user-pose
   tours captured from assets_dev and checked (`user_report_poses/*_sheet_r8b.jpg`). Scenarios against assets_dev:
   `mm9/ai/jellyspore.yml` now fails (Isle of Ashes has 83 map actors instead of 70 after the density change, so the
   arena Jellyspore's roll gives taunt_detect, not detect; openyamm-83 fixed it ~22:25: `ai_trace` `decision:` takes a
   list, the test accepts both, 3/3 passes on assets_dev); `perception_placed_yaw` and
   `spell_conditions` fail on R7c's assets too. **R8c, promoted ~23:40** (`promotion_r8c_20261107/`, 27 files of 9
   maps): Sturmford City's posed people (RUDEProps) at the height MM9 draws them (`rude_props.mm9_foot`: lift, then
   MoveToFloor onto the physics world incl. invisible brushes and earlier solid boxes, `prop_pose.mm9_centres`; the
   Jarl no longer sinks into his throne) and the AI session's villager walkers (`mm9_ai_placement.townsperson_walks`) on
   thjorgardcity, arslegardcity, guberlandcity, frosgardcity, drangheimcity, thronheimcity, lindisfarne, guberland.
   47/47 of their scenarios; the walkers traced 150 s (their double-door loop fixed in the engine by the AI session;
   walkers beyond the 10,240-unit indoor activation range wait by design). **R9, promoted 2026-11-08**
   (`promotion_r9_20261108/`, 240 files of all 44 maps, one unreferenced texture `YANM7QVOPQ.bmp` deleted, backups
   there): the portal-clipping reconversion (DUNGEON_PLAYBOOK "Package change: portal clipping"; engine key
   `portal_visibility.near_reach`, devdocs/INDOOR_OPEN_SKY.md "Portals beside the camera"). Exits 105/92/13 as
   expected. 169/174 scenarios; open: `mm9r_arslegardcity/scenario_njam.yml` step 10 (Njam hostile, not targeting the
   party) since the AI session's 09:38 edits, handed to that session (openyamm-9e). **R9b, promoted ~12:30**
   (`promotion_r9b_20261108/`): Arslegard City only. The cause was converter Lua: the chase lifted Njam's immobile
   flag but never opened the locked Njamdoor, as MM9's NjamChase.scr does; `citylua.py` njamChase() now opens it, and
   scenario_njam waits 6 s for the door. 7/7 Arslegard scenarios on assets_dev, exits 105/92/13. The orphan
   `YANM7QVOPQ.bmp` (still in the A root's owned list) is skipped so it is not added back. Open (flagged to the user by
   openyamm-9e): 129 doors on 20 maps are both AITriggerable and Locked, and ai_open_doors() excludes them all, so
   monsters never open one even after it is unlocked. **R9c, promoted ~15:30**
   (`promotion_r9c_20261108/`, 16 files of Thjorgard City, Frosgard City and Dark Passageway): sky-flagged polygons
   (LithTech 0x10) are sky faces whatever their texture (shared `Source.sky_flagged_as_sky`; CITY_PLAYBOOK). It came
   from a player report: Thjorgard City's hillside showed a 5 000-unit wall. **R9d, promoted ~16:00**
   (`promotion_r9d_20261108/`, 34 files of Guberland City, Hall of the Gods, Dark Passageway, Frosgard City, Thjora
   Mine and Guberland): no MM9 actor stands on a pre-MM9 (MM6-MM8 stand-in) row any more (12 before). The DAT classes
   MM9 places them as are now `mm9_npc_legacy_replacements.tsv` `object_class_override`s (rows 9, 50, 63, 252,
   263-265; several classes per row with `|`). Dark Passageway's adventurer is on 9111, as the same class on
   Guberland and Inventa. Scenarios 26/27 (darkpassageway swim as before). Both runs left out another session's new
   `textures_x2/thjo*.png` (A root, 14:58) for its owner to promote. **R10, promoted ~16:45**
   (`promotion_r10_20261108/`, the per-map files of all 44 maps, the shared tables unchanged): three converter
   changes, each from a player report:
   - the floor split between any two rooms, joined by a portal or not (`build.split_floors_between_rooms`; Drangheim
     City's tower passage). Faces +0.1 % to +15.6 % (Dark Passageway); Chasm of the Dead keeps `without_portal`
     (7 000-outline limit);
   - flat movers owned by the room over their top (`movers.flat_mover_owner`; Chasm's pit hatch), plus Chasm's
     PivotWallTrap1 `owner_lt`;
   - untextured liquid volume faces drawn with their surface sprite (`water.untextured_volume_faces`; Frosgard's
     teleporter gate showed the placeholder).

   Scenarios 170/174 with the known failures; Verhoffin's scripted scenario passes alone.

   **R10b, promoted ~17:15** (`promotion_r10b_20261108/`: Thronheim City, Guberland City, Sturmford City, Isle of
   Ashes). Seated people:
   - Thronheim City's six council Jarls: actors on their HD models looping Sit (`rude_props.py`), no longer MM9's posed
     prop models. Sven has a chair of his own (his Sven_ARG model carried one). The war council cinematic uses them,
     with only Kira on a stage actor.
   - `rude_props` keeps a posed body off the floor under it (Sven sat 5 units under the hall's floor and the game put
     him in the room below).
   - The shared `lua.init_poses` plays the clip an MM9 script loops from its :Init (Markel, Tryggva, Yrsa).
   - Markel sits on Guberland City's throne (`seat_markel`).

   Frosgard City carries the same changes in openyamm-a2's harbour build. Scenarios 22/22. Engine quirk: a posed actor
   hidden at load and shown later in the same visit is not drawn; Thronheim shows its council only at load. The notes
   below are the earlier steps.

   **R11, promoted ~21:45** (`promotion_r11_20261108/`, run `placed_items_20261108/`): MM9's pickable props as world
   items ([PLACED_ITEMS_PLAN.md](PLACED_ITEMS_PLAN.md)). 19 maps rebuilt: 1000 Terrors, Afterworld, Arslegard City,
   Beethoven, Boot Camp, Chasm, Dark Passageway, Drangheim, Guberland, Inventastorca, Klusos's House, Lich Lab, Ruined
   Temple, Ta'Sar, Temple of Honk, Thronheim City, Verhoffin, Wizard's Lab, Yanmir's Fort (61 world items).
   - Engine: the scene's `world_items` (simpler schema) are picked up as any ground item, then recorded as taken
     (`MapDeltaData::takenWorldItems`, save version 165), their `set_qbits` set and their `pickup_event` run; their
     quest-bit gates are evaluated only when the party's quest bits change.
   - Converter: `dungeon/pickups.py` (rules per script; `REVEALED_BY` for the Afterworld's swords, keyed by the DAT
     name: a region's props are `obj_<name>`). Each map's own pickup Lua keeps only the side effects.
   - Hjordisa the Hag (RUDE 132) gives back a lost quest item (`dialogue/lost_items.yml`, `MM9.takeItem` records the
     hand-in as `evt.SetGlobalVar("MM9.HandedIn.<raw>")`; `tests/scenarios/mm9/lost_items_hjordisa.yml`).
   - Scenarios 77/83 with the known failures, which fail the same on the maps before R11: Beethoven, Ta'Sar and 1000
     Terrors doors/mechanisms, Dark Passageway's swim replay; Klusos's doors are flaky (pass/fail on the same build).
   - R11b (~22:30, Thronheim City re-promoted): a world item's optional `pickup_qbits` (shown, taken only with them, no
     sparkle before) and `pose` (yaw, pitch, roll: drawn and picked turned so, resting on its lowest point), set per
     map in `overrides.yml` `pickups:`. Kira's Shield always leans on its wall (`pose: [180, -75, 0]`, `offset: [0, -14, 0]`: the wall is north of it) and is taken
     only on the quest (key 214), as in MM9. The pickup locks are runtime-only: `IndoorWorldRuntime::restoreSnapshot`
     re-evaluates them.
   - Open: Ta'Sar's Book of Rules lies flat on the tilted lectern and clips into it (a `pose` for it would fix it).
   Earlier notes:
   - The first-animation pose does not move these props: for all 30 old-list models (altar1 ... weaponscabinet02,
     plus barrel and crate), `prop_pose.bind_and_pose` gives posed z extents equal to the bind mesh's. So "LithTech
     draws a Static_Model in its first animation's first key" (prop_pose.py docstring) explains the NS/EW quarter
     turns but not the height.
   - The ABC origins are at the vertical centre of the mesh for symmetric models (anvil -39.9..39.9 native, dresser
     -70.8..70.8, bookcase01 -121.8..121.8); asymmetric meshes keep a centred origin of a taller box (chair
     -71.6..47.7, bookcase02 -121.8..89.4, bed -37.2..65.1, pew2 -61.5..50.2); table01ns has its origin at its base
     (-0.2..83.9). Yet MM9 shows all of them standing with the DAT Pos on the floor, so the engine raises the model.
   - Each ABC's `anim_bindings[0]` holds an `extents`/`origin` dims box (LT units; chair extents (13, 11, 13) origin
     (0, 17, -2); table01ns (20, 17, 80) / (0, -16.5, 0); bookcase02ew (33, 41, 16) / (0, 6, 0); anvil (16, 14, 16) /
     0; bed (41, 15, 41) / 0; pew2 (48, 11, 13) / (0, 11, -2)). These do not simply equal the mesh's half-height
     ("raise by half dims" fails on the chair); the engine's use of them is the open question. Native = LT x ~2.85.
   - object.lto (mm9/game/data/object.lto): string "MoveToFloor" at 0x1019b108, "Dims" at 0x1019b164; 0x10075189 is a
     static property-table initializer (not logic). Code that pushes "MoveToFloor" for runtime reads: 0x10076ce0, and
     /v4 hits 0x1007981f, 0x100966c3, 0x10070bba, 0x100707dc, 0x10072803 (check each for a GetPropBool call, then follow
     the Prop class's InitialUpdate: how it sets the object position/dims from Pos and the model, via the server
     interface at *0x102babe8 vtable). The model draw offset may also live in the engine (lithtech.exe / server.dll
     model instance: root node vs the dims), not object.lto.
   - Next: decompile the Prop InitialUpdate path (rz-ghidra `pdg`), derive the rule, then test it numerically on the
     old-list models (base must land on the DAT Pos floor) and on table01ns and the hanging props (claw lamps).
2. **Audit the 44 per-map `overrides.yml`** (~3,900 entries, read-only first): classify each entry as a copy of MM9
   data, a user decision, or a workaround for a converter gap; replace the workarounds with shared rules, most maps
   first.

## 9. Where the details are

Per-topic records written this week: `scr_audit/` (every MM9 .scr vs our handling), TABLE_CONSISTENCY_20261106.md,
MM9_AMBIENT_AUDIO_RE.md, MM9_MONSTER_SOUNDS.md, PROP_PLACEMENT_AUDIT.md, MM9_BONUS_PROPS_RE.md,
MM9_VISUAL_PROPERTIES.md, OUTDOOR_BLV_ALL.md, `level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md` and
CITY_PLAYBOOK.md, devdocs/INDOOR_OPEN_SKY.md, INDOOR_TRANSLUCENT_FACES.md, INDOOR_DESTRUCTIBLES.md,
SAVED_MAP_STATE_IDENTITY.md. Captures of each fix: `output/mm9_rework/*_20261107/`. Run logs: `final_r4..r6_*`,
`promotion_r4..r6_*`.
