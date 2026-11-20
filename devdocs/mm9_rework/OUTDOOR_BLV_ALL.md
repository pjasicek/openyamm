# All MM9 outdoor maps as open-air BLVs (task file)

Task from the user, 2026-11-03 22:50. This file is the durable state: an agent resuming the task (a scheduled
"resume check" prompt fires hourly in the session that started it) reads it first and keeps it current. Do not rely
on /tmp or the scratchpad (a reboot wipes them).

## The request

1. Build every MM9 outdoor region as an open-air BLV, the way the Isle of Ashes pilot was built
   (`level_generation/projects/mm9r_isleofashes_blv/README.md`, shared converter `mm9r_common/outdoor_blv.py`,
   second map `mm9r_sturmford_blv/`): sky, fog/haze, weather, daylight, footsteps, boat/transport arrivals, decorations,
   and the outdoor water swimmable as on the isle (`map: {swim: true}`, seabed, water volume, deep sea liquid).
2. Then examine the ground textures each map uses and give every map the blended terrain materials, as on the isle
   (devdocs/INDOOR_OPEN_SKY.md "Terrain"; `overrides.yml terrain: {materials, slope}`;
   `mm9r_common/terrain_blend.py`; world materials in `mm9r_common/terrain_materials_world.yml`), so the old MM9
   ground textures are gone. Add world materials where a map needs one (e.g. snow; library: assets_dev/engine/
   terrain_materials/library.yml).
3. Investigate how MM9 bounds flying AI: fly volumes, bounds, rails, height limits or similar in MM9's data
   (world files, AI/scripts, LithTech objects). Report findings and what our runtime should do with them.

## Rules

- **Never run a game build (`cmake --build ... -j25`) and a map conversion at the same time**: on 2026-11-04 the
  pair ran the machine out of memory and killed the session. One heavy job at a time.

- Follow AGENTS.md/CLAUDE.md (no git add/commit/stash; isolated game runs; no Vulkan builds; safe deletes).
- Each map gets its own project `level_generation/projects/mm9r_<map>_blv/` and review root under
  `output/mm9_rework/` as the pilots did (check how the isle and Sturmford roots relate before choosing).
- Keep a short record per map (README in its project) and the progress table below up to date after each step.
- Report to the user at the end; anything needing their decision goes under "Open questions" and work continues on
  the rest.

## Maps (fill in from MM9's level list before building)

| Map | Project | BLV built | Swim water | Terrain blend | Checked in game | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Isle of Ashes | mm9r_isleofashes_blv | yes (rebuilt 2026-11-04) | yes | yes | loads, rain | pilot; story, props, chests |
| Sturmford | mm9r_sturmford_blv | yes (2 s, 22 001 v, 27 057 f, 11 doors) | yes | yes | loads, rain, sky follows | sky-flagged grass quad fixed; test_population off |
| Thjorgard | mm9r_thjorgard_blv | yes (3 s, 17 722 v, 24 602 f, 6 doors) | yes | yes | loads, rain | excl. Magreeb, HalfOrcSoldier |
| Thronheim | mm9r_thronheim_blv | yes (2 s, 15 738 v, 23 491 f) | yes | yes | loads, rain | |
| Drangheim | mm9r_drangheim_blv | yes (2 s, 21 300 v, 27 068 f, 3 doors) | yes | yes | loads, rain | |
| Guberland | mm9r_guberland_blv | yes (2 s, 17 584 v, 24 647 f, 3 doors) | yes | yes | loads, rain | |
| Frosgard | mm9r_frosgard_blv | yes (2 s, 17 229 v, 24 226 f) | yes | yes (snow) | loads, snow | weather: snow; sky-flagged quad fixed |
| Lindisfarne | mm9r_lindisfarne_blv | yes (2 s, 27 157 v, 30 335 f, 13 doors) | yes | yes | loads, rain | excl. Monk (dorude.scr) |
| Yorwick | mm9r_yorwick_blv | yes (3 s, 19 632 v, 23 062 f, 8 doors) | yes | yes | loads, rain | |
| Mountain Pass | mm9r_mountainpass_blv | yes (2 s, 12 520 v, 21 983 f) | yes | yes | loads, rain | terrain models by class |
| Bootcamp | mm9r_bootcamp_blv | yes (20 s, 18 687 v, 13 425 f, 23 doors) | yes | yes | loads; start inside a hall | only Lobber Pods as monsters |
| Afterworld | mm9r_afterworld_blv | yes (2 s, 5 759 v, 6 313 f) | yes | yes | loads, rain | no monsters |
| Wizard's Lab | | | | | | no terrain (a structure in the sky): not this route; open question |

Verified 2026-11-04 against mm9/extracted/WORLDS/WORLDS/*.dat: 11 wilderness regions (above) plus the Afterworld and
Wizard's Lab exteriors (PLAN.md: 20 exteriors = 11 regions, 7 cities, Afterworld, Wizard's Lab).

## Progress log

- 2026-11-03 22:55: task file and hourly resume schedule created; nothing built yet.
- Found: the BLV route is the user's decision (OUTDOOR_PLAYBOOK.md, 2026-11-02; the ODM route is superseded).
  Sturmford's `convert.py` installs into the shared review root `output/mm9_rework/isleofashes_blv_root` (4 min run);
  the isle's into the same root. Next: read `outdoor_blv.py`, `mm9r_sturmford_blv/convert.py` and README in full,
  check Sturmford's swim water and weather, then template the next region from Sturmford.

- 2026-11-04 05:10: map list verified (11 regions + Afterworld, Wizard's Lab); start orders read from the old
  scenes; monster classes resolved per map (scratch list in `outdoor_blv_drafts.txt` beside this file). New tools:
  `mm9r_common/outdoor_blv_draft.py <MAP> [--overrides "<Name>" --exclude A,B]` (offset, monsters, doors; writes a
  first overrides.yml) and `outdoor_blv.convert_region()` (a region's whole convert.py). Thjorgard project created
  and building. Mountain Pass and Wizard's Lab have no `Terrain*` model: check their model names before drafting.
  NPC classes that resolve to monster rows must be excluded per map (Thjorgard: Magreeb, HalfOrcSoldier; Wizard's
  Lab: ReverendMonk; check Lindisfarne's Monk and Bootcamp's ReverendMonk).

- 2026-11-04 06:05: Thjorgard built and checked in game. Fixes on the way: liquids.py SEE_THROUGH oc4 0.95
  (Thjorgard's WorldObject1 water); dungeon/tables.py transitions_text now also rewrites rows another conversion added
  (Arslegard City's row 638 still named thjorgard.odm, and the game refused the whole table); outdoor_blv.py Layout
  takes terrain models by class `Terrain` too (Mountain Pass: CliffsTerrain0, PathTerrain1). The other nine regions
  are queued (`mm9r_common/outdoor_blv_queue.sh <stems...>`, one at a time: they share the review root's tables).
- 2026-11-04 06:40: liquids.py SEE_THROUGH completed for every region from a scan of their DATs (oc4 0.8/0.85/0.95,
  w123 0.4). Terrain: `mm9r_common/terrain_textures.py <MAP> [--sheet]` lists a region's ground textures (area share,
  up share, MM9 bitmap); every region's overrides.yml now has a `terrain` block chosen from the sheets (comments give
  the shares); new world material `snow` (MM6's) for Frosgard. Sturmford: `swim: true`, terrain block,
  `test_population` 0, convert.py installs the terrain. Queue: Thronheim failed on oc4 0.85 (fixed after it ran:
  rerun), Drangheim built (terrain still to install: `terrain_blend.py <project> --root <root>`).
- 2026-11-04 07:05: queue 1: Drangheim, Guberland, Frosgard, Yorwick built (the last three with terrain). Fixes:
  `PortalZone` models (Tavernzone, Storezone: helper volumes with greenscreen.dtx) are skipped; maps whose old import
  lists no `misc\invisible.dtx` (Mountain Pass, Afterworld) get its alias in overrides `textures` (the AIBarriers'
  faces need it); outdoor_blv_draft.py writes both. Queue 2 running: Thronheim, Lindisfarne, Mountain Pass,
  Bootcamp, Afterworld, Sturmford. Then: terrain installs for Thjorgard and Drangheim, game checks of every region.
- 2026-11-04 07:05: session killed (out of memory: a -j25 game build beside a conversion). Thronheim built with
  terrain; Lindisfarne was cut off mid-build; Mountain Pass, Bootcamp, Afterworld, Sturmford not rerun yet. Weather
  engine code written but not yet compiled (IndoorOpenSkyWeather, scene `sky: {weather}`, GameDataLoader
  applyOpenSkyWeatherToSelectedMap, IndoorRenderer hooks, GameApplication setOpenSkyWeather).
- 2026-11-04 09:00: all 12 regions rebuilt and loaded in game with weather forced (screenshots in the session
  scratch). Weather engine done: scene `sky: {weather}`, GameDataLoader profile, IndoorOpenSkyWeather (rolls, fades,
  sky, rain rings, sounds, rain/snow), console `weather rain|snow <0-1>|clear|auto` on such maps, unit tests (30 cases
  pass); devdocs/INDOOR_OPEN_SKY.md "Weather". The sky follows the rain over its normal cross-fade (about 30 s).
  Fixes: liquids.py keeps an empty face_attribute_overrides (Afterworld would not load); outdoor_blv.py makes visible
  sky-flagged polygons (LithTech 0x10) sky faces (Sturmford's giant grass quad over the map, Frosgard's).
  Next: Bootcamp's start is inside a hall (check that rain does not show indoors), a user review of the terrain
  material choices per region.
- 2026-11-04 09:40: **status: built and checked; waiting on the user's review.** Sturmford and Frosgard rebuilt with
  the sky-flag fix (Sturmford's green dome over the map is gone). Swimming checked headless (walk off the arrival
  dock, `water: state surface`) on Sturmford, Thronheim, Guberland; Drangheim's arrival walks down a shore and
  Lindisfarne's crosses a bridge (not water tests). Not done in this task: props, scripts, NPCs and the encounter plan
  of the new regions (they carry MM9's own monsters only, as Sturmford did), weather splashes, wet faces and ladder fog
  indoors, per-map weather chances in weather.yml (the global ones apply).

## Open questions

- Review the terrain material choice per region (overrides.yml `terrain`, from terrain_textures.py sheets).
- ~~Bootcamp's white strip at the hall door threshold (start view)~~ (2026-11-07): wall-base faces in the outdoor
  room; faces two rooms see now draw in both (DUNGEON_PLAYBOOK.md "Package changes from Bootcamp's play-test"),
  and every map takes its glass per face from MM9's Translucent flag.
- Wizard's Lab has no terrain (a structure in the sky): build it the dungeon/city way, or leave it?
- ~~Bootcamp's Evil Grand Sorcerer, Reverend Monk and Oculus~~ (2026-11-04): `EvilGrandSorcererCACHEONLY`,
  `ReverendMonkCACHEONLY`, `OrbusCACHEONLY`, all `CacheOnly 1` at one point: LithTech preloads their models and never
  spawns them. The converter now leaves out every CacheOnly object by rule (dungeon/content.py `monster_bases`).

## Flying AI findings

Data (all 45 DATs, 2026-11-04):
- **No fly volumes or bounds in the maps.** Only one `VolumeBrush` and one `Rain` object exist in all of MM9; no class
  names a fly zone, ceiling or altitude band.
- **AIRail** (8 133 objects: the AITrk brushes linked by `RailLink0-3`, `OneWayOnly 0`, `IsLadder 0` everywhere) is the
  walkers' navigation graph (DUNGEON_PLAYBOOK, `rail_check.py`). **Flyers do not use it**: every flying placement
  (`Gravity 0`: dragonflies, ickies, eyes, oculi, spores, winged oddities, apparitions, shadows, specters) has
  `FlyerUsesRails 0` (the property only exists on flyer classes); their `UsesRails 1` applies only while walking.
- **AIBarrier** (294 brushes, monster-only walls, already built by the shared converter): **flyers ignore them**,
  `CheckForAIBarrier 0` on every flyer (7 Imp Elders, gravity walkers, have 1).
- `WanderLeash 0.0` and `WanderON` mostly 0 on every flyer: no leash from the data.
- Imps, Imp Elders, Implies and Bloodsuckers have `Gravity 1` (they walk), some with `TerrainMode 1`.

Scripts (the flyers' AI is script: `mm9/extracted/SCRIPTS/SCRIPTS/BASEFLY.inc`, 2001, over the engine commands
RunTo, Strafe, FaceDir, OnObstacle). **No altitude limit, band or ceiling anywhere**; the height follows from the moves:
- idle: hovers where placed (WanderON 0 on almost every flyer); wander (BASEWANDER.inc) is level at the height where
  wandering began (`wanderStartY`), its leash measured from there;
- chase (`BaseFlyGetHim`): `RunTo` the target, straight at it in 3D, so it comes down to a walking party;
- attack (`AttackStrafe`): strafes level (dir Y = 0) at 45 degrees round the target; flyVel 80 % (at most 200) while
  the target stands still;
- after an attack (`BackOff`): turns away from the target and strafes away **climbing** (dir Y = `g_backOffYVal` 0.6)
  for `g_backOffTime` 1 s, level instead when the target itself flies; then `SwoopIn`: level, 30-50 degrees off the
  line to the target, for a second; then the chase again;
- obstacles: `OnObstacle` stops it (attack strafe) or turns it (wander); nothing else bounds it (no AIBarrier, rails).
So MM9 bounds flyers only by the level geometry (in our BLVs also the near box's walls).

Code (object.lto, the server game DLL; RE setup in MM9_MONSTER_JUMP_RE.md, re_mm8/work/mm9_jump): flyer classes read
`FlyerUsesRails` into the same field as `UsesRails` (+0xb30, ReadProp 0x1001ccf0), so a flyer never uses rails; speed
by state +0xacc run, +0xad0 walk, +0xad4 fly (0x1000dc10); `GetAltitude` and `IsFlying` are script conditions
(`GetStat ... IsFlying`); `AISwimFly` objects are exempt from volume brushes' physics (0x1008fdb0).
Compared with ours (IndoorWorldRuntime flyers, 2026-11-04): our flyers already aim at the target's height
(`flyingAimFootZ`), fit under ceilings (`flyingFootZUnderCeiling`), keep clear of the floor and stop at the near box's
walls, and ignore AIBarriers like MM9's. **Nothing to import**: MM9 has no fly volumes, rails or height limits. What
MM9 does that ours does not is behaviour, not bounds: the climb away after each attack (up 0.6 for a second, level
against a flying target) and the angled swoop back in. Optional later work, if the user wants MM9's feel.

## How a region is built (found 2026-11-04)

- A project is `convert.py` (subclass `outdoor_blv.OutdoorBlvHooks`, redirect `review_root` to
  `isleofashes_blv_root`, run `dungeon.main`, then `rewrite_transport`, `bind_indoor_decorations` when it has props,
  `terrain_blend.install`) plus `overrides.yml`; the build reads `mm9/extracted/WORLDS/WORLDS/<MAP>.dat` itself and
  writes `source/`. Template: Sturmford (`mm9r_sturmford_blv/`), plus the isle's `swim: true`, `terrain` block.
- Survey first: `python3 level_generation/projects/mm9r_common/dungeon/survey.py <MAP>.dat [--rules]` (classes,
  models with suggested rules, textures with counts: the terrain materials come from its texture list).
- `offset`: centre the terrain model's LT extent (native = LT * 2.56 - offset within +-25 600 / int16).
- Sturmford settings for big regions: `generate_bsp: false`, `city: {half_steps: false}`, `voxel: 32`.
- Props: only the isle has a props.json (from its ODM pilot). Other regions: check whether the old MM9 import
  (`output/mm9_rework/assets_dev/worlds/mm9/maps/<stem>.odm` decorations) can give one; otherwise note it.

## Weather (gap found 2026-11-04)

The isle has no weather: open-air BLVs are weatherless today (WEATHER_PLAN.md: "Indoor BLV maps stay weatherless.
MM9 is out of scope"; INDOOR_OPEN_SKY.md "Not covered yet"). The design exists: CITY_PLAYBOOK.md "Weather in
open-sky sectors" (rain/snow over open sectors' floors, sky follows the weather ladder, wet surfaces on open faces,
scene opt-in `sky: {weather: <map's weather table>}`). This is engine work, planned after the maps are built: shared
gameplay/render code, no cost for maps without the opt-in, MM6-MM8 unchanged.

Plan (2026-11-04, from the code): the parts are world-independent already: `WeatherModel` (rules, day rolls; per-map
chances in `engine/rendering/weather/weather.yml` `maps:` by map file), `WeatherPresentation` (fades, lightning),
`WeatherRenderer` (rain/snow particles), `WeatherAudio`. The outdoor glue is `OutdoorWorldRuntime::currentWeatherSample`
/ `AtmosphereState` and `OutdoorRenderer::updateWeather` / `renderWeather` (about 240 references in outdoor code).
1. Scene opt-in: `sky: {mode: open, weather: true}` (IndoorSceneYml parseOpenSkyNode, IndoorOpenSky) and the MM9
   regions' `weather.yml` `maps:` rows (`<stem>.blv`: Frosgard snow; others rain), written by outdoor_blv.py.
2. IndoorWorldRuntime: the same sample/rolls as the outdoor runtime (move the shared part out of OutdoorWorldRuntime
   rather than copy it), saved like the outdoor state.
3. IndoorRenderer: update the presentation, draw WeatherRenderer and feed SkyInputs (precipitation, lightning) when
   the camera's sector is open to the sky (v1: the open-air sector; the outdoor weather has no roof map either), the
   ladder fog into the outdoor-view haze, rain rings on the sea, weather audio; a fixed `preset` gives way to weather.
4. Checks: unit tests for the opt-in parsing and the sample; screenshots of rain and snow on two regions; MM6-MM8
   outdoor and an MM8 BLV unchanged (no weather objects created without the opt-in).
