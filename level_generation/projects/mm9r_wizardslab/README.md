# MM9 rework: Wizard's Lab (`wizardslab.blv`)

MM9's Wizard's Lab (Yorwick's floating laboratory: the lab floor with the halls, bedrooms and the cauldron room, the
cell block and the sea monsters' pool under it, the cloud room with Robinssen's prison, the super eye's chamber, and
the summoning tower whose top is open to the sky; six colour teleporters link them) converted from its DAT world into
a native **indoor map (BLV) open to the sky**, built like the MM9 cities (the user, 2026-11-04,
[REGIONS_FINISH.md](../../../devdocs/mm9_rework/REGIONS_FINISH.md) step 3). It replaces the old ODM import
(`assets_dev/worlds/mm9/maps/wizardslab.odm`, a terrain-less outdoor map). Shared route:
[CITY_PLAYBOOK.md](../mm9r_common/CITY_PLAYBOOK.md) on top of [DUNGEON_PLAYBOOK.md](../mm9r_common/DUNGEON_PLAYBOOK.md).

Status 2026-11-05: **converted with its props, MM9's lightmaps transferred (98.7 %), teleporters and summoning
proved.** Props: [mm9_wizardslab_claude](../../props/mm9_wizardslab_claude/README.md) (243 placements). Scenarios
(`make_scenarios.py`, rerun after convert.py): `scenario_teleporters.yml` (all 30 crystals, the six stations, the six
destinations stand, both closets send the party on) and `scenario_ritual.yml` (arrival, the chain, the master, the
Greater Demon, six apprentices dead, the banishing): both pass. Desktop views: `review/walkthrough_v01*/`
(`review_tour_walkthrough_v01*.yml`). Fixed on the way: the TouchNotify volumes (stations, closets, the ritual
trigger) are grown by the party's radius (`citylua.touch_box`): Teleporter2's box lies behind its closet's back panel
reach, so the party's centre never entered it; the relic is found by its script (props.json names it barrel_877).

## Build

One heavy job at a time: no map conversion beside a game build or another conversion (out of memory, 2026-11-04).
Check first: `pgrep -f "^cmake --build build"` and other `convert.py` runs.

```sh
python3 level_generation/projects/mm9r_wizardslab/convert.py --plan     # rooms only: work/rooms*.png, stats
python3 level_generation/projects/mm9r_wizardslab/convert.py            # build, compile, install (review root
                                                                        #   output/mm9_rework/assets_dev)
python3 level_generation/projects/mm9r_wizardslab/convert.py --scratch /tmp/wl   # build into a directory only
```

The voxel grid at 16 LT is about 675 x 183 x 440 = 54 M cells (Thronheim City: 62 M, 3.6 GB, 19 minutes): expect a
similar run. After the first build: `work/build_report.json` (`stats.sky_faces` should be 5, `stats.sky_flagged_retextured`
5 or more, `scripted.left_out` empty, `stats.water_room_mismatches` 0), `work/floor_holes.json`, the plans
`work/rooms_{cells,main,upper}.png`; then tours (`make_tour.py`, from a city's) against the old ODM and scenarios
(doors and the exit, chests, the teleporters, the summoning).

Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame: the transition rows and the painted map's
bounds stay valid); native x -22 077..5 578, y -717..17 323, z -3 400..4 096.

## The sky, daylight and no terrain

Wizard's Lab has no terrain and no streets. MM9 draws its sky box (`Greenhills-Lake`, a DemoSkyWorldModel of
`starfield.dtx`) through **five sky faces** only (surface flags 0x111: solid + sky portal, texture `Default`): the
four walls and the lid of the summoning tower's top (LT x -3 712..-2 432, z 4 992..6 272, y 576..1 600). Everything
else is enclosed rooms. So the map is a dungeon with the cities' sky:

- **CityHooks** (`../mm9r_common/city/hooks.py`): the sky faces get `IndoorSky` and the scene `sky: {mode: open,
  preset: cloudy}`: our Enhanced outdoor sky with the time of day behind the tower top, as the cities.
- **Sky faces by flag** (the shared `Source.sky_flagged_as_sky`, since 2026-11-08; was this map's `sky_faces`): MM9 marks a sky portal by the surface flag 0x10; the cities' sky
  faces also carry `skymarker.dtx`, which CityHooks looks for. Here the five carry `Default`, as 18 ordinary solid
  slivers do (a 2 LT post at the tower's corner and a few pieces at its foot), so the converter retextures the
  flagged polygons to the sky marker (overrides.yml `textures`: alias `sky04`) before CityHooks runs. No alias of
  `Default` itself (it would turn the slivers into sky).
- **Daylight** (`city: {daylight: true}`): the sun and sky light on the sectors open to the sky, which the engine
  finds by their sky faces (`indoorOpenSkySectors`): the tower top's room (its lid alone is 1.07e7 native units
  squared, over the 1e7 threshold). MM9's data: WorldInfo `AmbientLight 35 35 35` (dark shade), no StaticSunLight (the
  sky's own sun direction), LightScale and NightLightScale white. Interiors are unchanged.
- **No street structure**: `extra_portals` returns none. `city/structure.py` needs a roof line (`street_top_lt`) and
  divides streets under a sky lid; the tower's open air is one room behind its doorways like any dungeon room.
- **No outdoor view, no weather, no fog**: the lab is seen as a dungeon (the scene's own view distance), MM9 has no
  fog here (WorldProperties EnableFog 0, no Fog object), and the open sky is a few hundred units square, so
  `outdoor_view` (map-wide sky haze) and weather are left off. No half steps (`half_steps` is for city plinths; the
  dungeon audit lists raised floors).
- No terrain block anywhere (it is a BLV); the old ODM's `no_terrain` environment flag goes with the old import.

## Content

- **Models** (overrides.yml `models`, every DAT world model ruled; `model_patterns` skips the 88 AITrack rails): the
  ten sliding double doors (`Lift` pairs DoubleDoor8-12, 17, 18, 21, 25, 27) are doorway movers behind their VisBSP
  UserPortals; the 14 cells (88 up, `click: false`) and their 14 levers (rotating, 30 degrees); the drawers, the closets
  and one dresser (rotating, clickable: `all_doors_click`); the super eye's force field (256 down, translucent:
  `glass: perception.spr`, the brush's Alpha 0.35, `click: false`); the 30 teleporter crystals as nudge movers
  (pressed 8 LT while lit); the energy shells, shimmers and invisible collision brushes static; the water volumes
  (DirtyWater0-3, the power waters) and the sky box skipped as geometry. **DresserDoorR1/L1 are static**: their
  RotationPoint (-5 152, 28, 5 440) is 6 500 LT from the dresser (copied from elsewhere); MM9 would swing them through
  the map. 89 movers in all.
- **Water** (`swim: true`): DirtyWater0 (the pool under the cell block, LT y -736..-360, the two sea monsters' home),
  DirtyWater1-3 (the cauldron room's basins) and the seven 2 LT "power waters" in the cloud room become
  `water_volumes`.
- **Lights**: 244 `Light` objects through the shared writer with `bright_scale_lights` (the cities' setting); the 37
  GlowingLights as `pulsing_lights` (automatic, `dungeon/lights.py`: key 40000 + DAT index; GlowingLight0 is the super
  eye's red light, Light<Colour><k> the crystals' lights, StartOn 0); the 34 AmbientSounds automatic
  (`dungeon/ambient.py`). DirLight0 and the ObjectLights are not converted (model-only lights in MM9).
- **Monsters** (overrides.yml `monster_classes`, 57 placed, MM9 bodies): Winged Aberration 6, Winged Oddity 2, Sea
  Monster Male and Female, Evil Apprentice 11, Evil Grand Sorcerer 4, Evil Sorcerer 1, Skeleton 10, Eye 20 (six
  "evil eyes" carry the sorcerer model in MM9; the class decides), Oculus 1. The seven summoners (SummoningGuy0-6) are
  friendly (WizardSummoner.scr `AddFriend Player`) with their row's engagement type kept, each apprentice in a group
  of its own (21-26, the master 27). GreaterDemonCACHEONLY is MM9's preload only; the ritual summons row 9242.
- **Robinssen** (ReverendMonk0, NPC55.scr): ReverendMonk resolves to the Reverend Monk monster row 9125, so the class
  is left out of `monster_classes` (OUTDOOR_BLV_ALL.md "NPC classes that resolve to monster rows") and `convert.py`
  places him as a friendly, immobile dialogue actor (RUDE 55, his NPCNAME.rude name) on the old import's record.
- **Starts and exits**: StartPoint0 by the exit portal (Yorwick's ExitTrigger6 arrives there,
  `mm9:transition/yorwick/7`); ExitTrigger0 to Yorwick's WizardLabExit (`mm9:transition/wizardslab/870`, AskPlayer).
  The shared table writer moves both rows to `wizardslab.blv` and keeps the old frame; map_stats.txt row 9071 names
  the BLV. The painted minimap (catalog entry `wizardslab`) is kept, and unlike the cities the lab has its
  outlines (no `painted_minimap`, 2026-11-10), so the Map style setting chooses the line map or the painted one.

## Props

The city route does **not** make `props.json`: it comes from a props project, as every city and dungeon has one
(`level_generation/props/mm9_<map>_claude/`, the Drangheim City route: MM9's own meshes and skins x4, `blib` build,
`finish.py --install`, rows in `worlds/mm9/data_tables/decoration_data.txt` under
`mm9r_common/locks/mm9_decorations.lock`, then `scripts/placements.py` writes `props.json` here). Needed:
`level_generation/props/mm9_wizardslab_claude/` for the DAT's 156 Props, 82 CandleProps, 2 Barrels (stat barrels),
4 BonePiles, the Cauldron and the two WellMMIX cauldrons, and the 3 TreasureChests (`kind: chest`: without props.json
the chests are not placed, though their loot records and click events are written). Many meshes are already built
for other maps (scrolls, bookcases, herb racks, tables, shelves, chests: `props_table._OWNERS` reuses them). Each
entry must keep `script` and `script_params`: `citylua.py` wires Book.scr, BookLetter.scr and Relic.scr props by them.
Watch: the relic pickup's DAT name is `barrel` (Relic.scr), which `content.entity` refuses if a decoration has that
name; placements.py writes it as `barrel_877` and `citylua.prop_events` finds it by its script (done
2026-11-05).

## Scripted objects

Native Lua in `citylua.py` (written into the map Lua by the converter; never edit the generated file), each handler
citing its .scr; the behaviour of every script: [work/scr_spec.md](work/scr_spec.md).

| Script / wiring | Objects | Native |
| --- | --- | --- |
| TeleporterSwitch.scr | 30 crystals | done: a click sets the station's next destination, lights its colour 4 s |
| TeleporterMulti.scr | TeleporterAt* (6) | done: the 4 Hz poll sends the party once per click, facing the arrival |
| plain Teleporters | Teleporter1/2 (closets) | done: always on, facing kept |
| WizardLabCamera.scr | CameraSummon | done: the cinematic `summoning` (README "Cinematics") at the first arrival |
| WizardSummoner.scr, WizardEffect.scr | 6 apprentices, 7 shooters | done: the chain, effects, betrayal, deaths |
| WizardMaster.scr, WizardDemon.scr | SummoningGuy3, the demon | done: the summon, relations, banishing at six deaths |
| super eye triggers (DAT) | EvilGrandSorcerer1, Oculus0 | done: force field down, red light off, pairs locked |
| cell levers (DAT) | Switch15-28, Cell15-28 | done: a lever opens its cell, closing toggles it |
| NPC55.scr | Robinssen | done: voice, RUDE 55, the Black Orb sale (keys 312, 313, item 250, 2 000 gold) |
| BookLetter.scr | Prop7, Prop8 | done: letters 498, 499 (when props.json lists them) |
| Book.scr | Prop148, Prop149 | done: a page sound (no animation from Lua) |
| Relic.scr | barrel | done: the Saint's Relic (item 368, keys 338-340), a world item (`dungeon/pickups.py`); its pickup sets the key |
| givetake.scr | Prop26 | **skipped**: item 386 does not exist in MM9's item list (MM9 only removes the prop) |

Deviations, all in the spec: the master "passing out" hides him (no Lua call
kills an actor); after the demon is up any hit on an apprentice counts as the demon's (the damage hook does not name
the attacker); an Oculus killed before the sorcerer leaves the pairs unlocked; the crystals' and summoners' sounds
partly not imported (`magic/teleport.wav`, `magic/wizardeyeloop.wav`, `magic/cast01.wav`, `magic/cast03.wav`,
`animsounds/dragon/fidget2.wav`, `animsounds/evilsorcerer/wince2.wav`: in `mm9/extracted/SOUNDS/SOUNDS/`, not in
`assets_dev/worlds/mm9/audio`); the PC "no gold" voice
is a status line; MM9's AI rails (AITrack on/off) and the perception hint (PerceptionBrush0) are not carried.

Events: map load 1, chests 41-43, door groups 101-114, locked pair 200, super-eye pairs 201-202, levers 210-223,
crystals 230-259, poll timer 262, crystal lights 263-268, ritual 270 (old saves), banishing 271, kill hook 280, damage
hook 281, scripted props 330+, the cinematic 36000-36008, Robinssen 50044 / 53044, SetSprite keys 400+.

## Cinematics

`summoning` (worlds/mm9/maps/wizardslab.cinematics.yml, built by `citylua.cinematic_scenes`, installed by convert.py;
devdocs/mm9_rework/MM9_CUTSCENES.md): WizardLabCamera.scr + CutScene.inc on CameraSummon, started where MM9's
DestinationPurple sends 'next' (the poll's `startRitual()` calls `MM9Cinematic.start("summoning")`). 21.5 s:

- fade out at once, 2 s (:SoftExit), fade in over 2 s; shots MarkerLocation0 (0-10 s, from the start behind the
  black), MarkerLocation1 (10-15 s), MarkerLocation3 (15-21.5 s), each looking at its MarkerTarget (CutScene.inc
  AlignCamera's FaceObject snap; a level camera would leave the targets below the picture), fov 73.7. The cuts are
  TriggerNotify<k> -> TriggerSwitchTo<k+1> SendDelay 8, 5, 0: MarkerLocation2's scene lasts no frame and is left out.
  The end is the master's :EndScene: :Summon at 19.5 s, taunt (EVILSORCERER.abc, 1.0 s), Wait 1.
- Steps (event 36000 done, 36001-36008): the ritual's eight ticks, `ritualAdvance(k)` = `ritualStep` when RitualStep is
  k (the six apprentices at 2 s and every 2.5 s: sparklies on the apprentice (MM9.actorFx) and green dots at its
  shooter above it, then 2.5 s later at the next tick their lightning, MM9's Sparks explosion (mm9:explosion_sparks)
  and bugs at SummonLocation; the master at 17 s: meteor, town portal,
  column of fire; the Greater Demon at 19.5 s). A dead apprentice still stops the chain. A skip runs the remaining
  ticks at once (the demon appears).
- Cues: the scripts' sounds (thunderlong per apprentice, cast03 at the master's :CastSpell 18.5 s, the demon's
  fidget2), the apprentices turned to SummonLocation (FaceObject at :Main), their clips (MM9's fidget2 = the GLB's
  Fidget at :ConjureSpell, AttackRanged at :CastSpell), the master's Fidget loop, AttackRanged and Taunt
  (mm9_evilsorcerer.glb). The clips' actors.yml events put MM9's DoFX hand effects on both palms: Fidget redyeldots
  0.6-1.933 s, AttackRanged greenyeldots 0.133-1.266 s (2026-11-10). A dying apprentice's bluedots are on its palms.
- Timer 270 still runs a ritual an old save left half-way (`ritualStep(true)`: with its sounds and the next tick).

Test without a conversion: `python3 cinematics_pilot.py` (writes the scene and the installed Lua, changed as
citylua.py now writes it, into output/mm9_rework/cinematics_pilot_root), then from
output/mm9_rework/cinematics_pilot_run `build/game/openyamm --world mm9 --headless-run-scenario <abs>
--scenario-no-color` with `cinematic_summoning_play.yml` (started by the volume, no save during it, ticks at 2 s and
19.5 s, the demon) and `cinematic_summoning_skip.yml` (skipped at 1 s: all ticks, one demon); both pass, and so does
scenario_ritual.yml (2026-11-06). Captures: output/mm9_rework/cinematics_pilot_run/captures_summoning/ (tour.yml,
sheet.jpg).

## Checks done (no conversion)

- `python3 -c "import convert, citylua"` in this directory; overrides.yml loads; `classify_models` finds a rule for
  every DAT world model.
- `citylua.map_script` run on a mock build (the real project, DAT and overrides; movers from the rules, floors faked,
  every DAT object as an actor index) and the Lua compiled with `luac -p` (Lua 5.4.8): it compiles. The real build's
  door ids, floors and actor indices differ; the scenarios must still prove the handlers.
- Lines within 120 columns.

## Open questions

- **The sky.** MM9 shows a starfield box at every hour (the lab "in the sky" is a night under the stars); the
  cities' cloudy sky with the time of day and daylight is used, as approved. `sky_preset: always_dark` (a starry
  overcast night) with `daylight: false` would be closer to MM9: the user's call after the first tour.
- **Robinssen's cage.** He stands inside the `firethrough` invisible brush (556 x 352 x 1 790 LT) under the cloud room;
  check in the first tour that the party can click him (talk range) and cannot walk into the energy shells.
- **The `Default` slivers.** 18 solid faces (the tower's corner post, small pieces at its foot) draw MM9's missing
  `Default` texture (the old import's placeholder `DEFAR33VFJ`); MM9 itself had no texture there. Drop or retexture
  them after looking at the plan (a map hook), not by aliasing `Default`.
- **The pool.** DirtyWater0's brush is invisible in MM9 (Visible 0); whether a water surface shows over it, and
  whether the party reaches the pool, the first build's views and `water_room_mismatches` tell.
- **Lighting.** `bright_scale_lights` follows the cities; CITY_PLAYBOOK warns that dungeons on the shared writer
  (Klusos House) matched MM9 better at full colour. Compare the old import's views before keeping it.
- **Doors.** 89 movers (30 crystals, 14 levers, 14 cells, 20 sliding leaves, furniture): check the click picking of
  the crystals over their invisible consoles (InvisibleBrush0-5) and the sliding pairs' auto-close (MM9
  CloseWaitTime 4, not carried for linear doors).

## Shared code (mm9r_common) that could change (not changed here)

- `city/hooks.py` `CityHooks.extra_portals` calls `structure.city_portals`, which needs `city: {street_top_lt}`
  (KeyError without it). A map with an open sky but no streets has to override it (as `convert.py` does). Proposal:
  `structure.city_portals` returns no portals when `street_top_lt` is absent.
- `CityHooks.scene` finds the sky faces only by their texture alias (`sky_alias`, default `sky04`). MM9's own mark is
  the surface flag 0x10 (`skymarker.dtx` is a convention of the cities); maps whose sky faces carry another texture
  (Wizard's Lab's `Default`) need a hook like `sky_faces`. Proposal: `Source.polygons` (or CityHooks) tags polygons
  with the flag and the scene takes those, keeping the alias as a fallback.
- MM9 `Teleporter` objects (TeleportDestination, TouchNotify, UseRotation) are re-implemented per map (Dark
  Passageway, here, Yanmir's Fort's doors): a shared helper in `dungeon/lua.py` (boxes reaching to the floor,
  arrivals on the floor facing the destination, the poll) would remove the copies.
- `lua.Script.finish` inserts the map metadata after `self.lines[:11]`, which assumes the header's exact length; maps
  that add a helper line to the header (Connecting Tunnels, here) shift it. An `add_helper` method would keep it right.
- Engine, not mm9r_common: no Lua call kills an actor (MM9's `Die`), and the monster damage hook does not name the
  attacker (MM9 tells the party's hits from the demon's). Both would make the summoning exact.

## Sky decision (user, 2026-11-05)

MM9's starfield at every hour: `city: {daylight: false, sky_preset: night_stars}` (`night_stars` in
`assets_dev/engine/rendering/sky/sky.yml`: `always_dark` with full stars). The open question on the sky is closed.
