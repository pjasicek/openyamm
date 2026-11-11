# MM9 rework: Isle of Ashes as a BLV (`isleofashes.blv`), pilot

The question (user, 2026-11-01): convert MM9's outdoor maps the way the cities are, as BLVs open to the sky, instead
of resampling their terrain onto an ODM height grid ([ODM pilot](../mm9r_isleofashes/README.md),
[outdoor playbook](../mm9r_common/OUTDOOR_PLAYBOOK.md))? This pilot builds the isle that way and measures it against
the ODM pilot. **Status: built, measured; the decision is the user's.**

## Build and run

```sh
cp -al output/mm9_rework/assets_dev output/mm9_rework/isleofashes_blv_root     # once: this pilot's own review root
cp output/mm9_rework/owned.txt output/mm9_rework/isleofashes_blv_owned.txt
python3 level_generation/projects/mm9r_isleofashes_blv/convert.py              # 6 min, 1.3 GB; installs, boat
                                                                                # arrivals, indoor decoration bindings
./tools/run_game.sh --isolated isle_blv --world mm9 --map isleofashes.blv \
    --assets "$PWD/output/mm9_rework/isleofashes_blv_root" \
    --position 2214 -15596 368 --yaw-radians 0.947 --pitch-degrees 0 --visible --seconds 0
```

The ODM pilot stays in `output/mm9_rework/assets_dev`; both maps use the same frame (x + 7 168, y + 512, the sea at
0), so a position from one is the same place in the other.

## What it is

- Frame `native = LT * 2.56 - (-7 168, -512, -164)`; the land spans x -24 944..20 930, y -29 634..24 760.
- Frosgard City's route (one open-air room, ../mm9r_frosgardcity/README.md): the voxel pass covers every island from
  under the sea surface to over the highest peak at 32 LT (18 M air voxels); the sea beyond is far scenery of the same
  room, clipped to int16. Under the sea surface nothing is kept (sea floor, the terrain's skirts).
- **1 sector, 9 994 vertices (15 % of 16-bit), 12 389 faces**, 3 doors (the bunker pair, Yrsa's hut), 21 lights,
  59 decorations (the ODM pilot's props.json), 8 sky faces, 938 sea tiles (the liquid shader, Dook's Castle's opaque
  ocean entry).
- Sky: our cloudy preset with the time of day; daylight on the open air (no StaticSunLight: the sky's sun). MM9 has no
  fog here (EnableFog 0, FarZ 100 000).
- The shared part lives in `../mm9r_common/outdoor_blv.py` (2026-11-02): near box and far sea, one open-air room,
  footstep sounds by floor texture, `party_movement: {steep_slopes: block}`, boat arrivals (`rewrite_transport`: the
  three boats arrive at StartPoint0) and indoor model bindings for the isle's outdoor props (`bind_indoor_decorations`).
  Sturmford is the second map on it ([`../mm9r_sturmford_blv/`](../mm9r_sturmford_blv/README.md)).

## Results (2026-11-01)

**Fidelity.** MM9's own geometry, so the ODM pilot's problems do not arise: the tunnel is open end to end, the trail
from Yrsa's hut up the valley is MM9's, the castle stands on its own floors. Headless walk (`../../..` scratch
`blv_walk.yml`): the party walks the tunnel west to east and up the hut trail, every segment its full length.

**Performance**, 14 views at the same poses in both maps (the user's six review spots, the castle, eye level, aerials),
desktop, visible window, one session each, `logging.performance_trace`:

| Median per view | BLV | ODM pilot |
| --- | --: | --: |
| Draw calls | 117 (91-142) | 131 (92-178) |
| Triangles | 30 400 (25 800-62 900) | 72 600 (39 200-111 800) |
| CPU frame, p50 | 0.38 ms | 0.65 ms |
| GPU frame, p50 | 0.34 ms | 0.60 ms |
| GPU p95, worst view | 0.88 ms | 2.34 ms |
| Texture memory | 310 MB | 492 MB |
| Map load (3 runs) | 1.11-1.30 s | 1.46-1.60 s |

Both are far under a frame budget on this machine; the BLV is cheaper on every count. Its cost is flat: one sector
draws the whole map every frame (about 26 000 triangles plus what the decorations add), where the ODM's terrain,
terrain materials, grass and its bigger textures vary with the view. The ODM pilot has 19 actors and the BLV (when measured) none
(a few draw calls).

**Scaling.** The isle is small: 10 472 terrain + 2 658 PhysicsBSP polygons. The big MM9 regions (Sturmford,
Drangheim, Frosgard, Guberland, Lindisfarne, Thjorgard, Thronheim, Yorwick) have 20 000-23 000 terrain and 2 000-8 500
PhysicsBSP polygons, 2-2.5 times the isle, and span about 51 200 native: inside the BLV's 65 535 if centred. Expect
roughly 25 000 vertices (under 16-bit) and 60 000-80 000 triangles drawn every frame in one open-air sector. Frosgard
City carries 11 787 faces in one sector without cost; a big region's 30 000 should be measured on one (collision and
monster paths in one large sector, 100-180 monsters).

## Terrain (2026-11-02)

The ground faces are drawn from blended library materials (devdocs/INDOOR_OPEN_SKY.md "Terrain"): `overrides.yml
terrain` maps ashcliff and NWROCK to `cliff_layered`, ashrock and MainGrass to grass, ashrock2 to grass patches and
ashdirt3 to dirt; `convert.py` runs `mm9r_common/terrain_blend.py` after the install (or alone:
`python3 level_generation/projects/mm9r_common/terrain_blend.py level_generation/projects/mm9r_isleofashes_blv
--root output/mm9_rework/isleofashes_blv_root`, 4 s). User review of MM9's textures (native and x4) at three spots:
hard grass/rock borders, cliff patterns breaking at polygon edges, brightness steps between polygons; all three were
MM9's own (per-polygon mapping, flat light) and are gone with the terrain path. 9 787 faces, 6 textures.

## What a BLV gives up (visible in `review` shots)

- Terrain: blended library materials on MM9's mesh since 2026-11-02 (above), but no grass decorations, meadow field,
  3D bushes or sun shadows yet.
- The castle's inner wall faces are very dark from outside (unlit by the daylight; open).
- The far sea is a wading surface to the horizon; the sea round the island (the near box) is swimmable since
  2026-11-02 (`map: {swim: true}`: seabed, BlueWater0, swimming spores and the Sea Monster: "Swimmers"), drawn as the deep
  outdoor sea (`sea_mm9`) with the sky in its reflections.

## User review 2026-11-02 and fixes

- **Head bob and a rapid up-down on uneven ground**: two indoor movement rules made for MM6-MM8 treads misread sloped
  faces (a step at the face's first vertex, 40 over the contact; early stepping onto the face ahead at its height a
  radius away). Fixed in the engine for every BLV (devdocs/INDOOR_OPEN_SKY.md "Party movement"); headless: the party
  follows the ground at 3-4 units a frame along the user's line, no spike.
- **Walking through cliffs** (6 078, -8 996): MM9's floors run on under its terrain; the steep-slope sweep exemption
  let the body through and the party's any-slope rule climbed the cliff's plane. Fixed: a body under a steep face's
  surface collides, and `party_movement: {steep_slopes: block}` (headless: the party stops at the cliff's foot).
- **Footsteps**: grass, rough ground, wood, stone, water, dirt by floor texture (`footstep_sounds`).
- Slope limit of MM9's player (RE) and the sea: left as they are (user).

## The finished map (2026-11-02)

- **Story**: Forad Darre, Yrsa (RUDE dialogues 2 and 1), the dragonflies' key, the bunker (its two leaves are this
  BLV's doors 1-2, their click the scripts' DoorLock Use), Yrsa's hut door (door 3), the book and lectern, the cinema
  (the fort walls are faces with their DAT index as cog, hidden by `evt.SetFacetBit`), the departure to
  `sturmford.blv` and Annud Redeye's passage; hand-ported since 2026-11-06 ("Map Lua" below). Check:
  `make_story_scenario.py` writes `story.yml` (96 steps since 2026-11-06: the cinematic plays on runtime, and Forad's
  "Welcome Aboard." ends his dialogue by itself).
- **Chests**: the three MM9 chests as `mm9_chest1` decorations on loot containers 0-2 (`props.json`: the ODM pilot's
  decorations plus the chests). Check: `chests.yml` (passes; headless runs do not pick 3D decorations, so each chest's
  event runs directly).
- **Actors**: MM9's 36 land monsters, the story's three NPCs and the Lich King (40); the test population is gone.
- **Trees**: MM9's spruces as MM8's gnarled gorge pine `tree16` (Tree06, 15) and its dead tree `tree28` (Tree05, 10):
  `outdoor: {decoration_swaps}`. The MM8 pines read lime and flat, MM7's `tree33` snowy and `tree60` lime. Models in
  the open air still come out brighter and more saturated than on MM6-MM8's outdoor maps (the daylight's model light).
- **Lighting test** (`lighting_test.py`, one-off, not a pipeline step): a Cycles base (`bake`, 32 units a texel, one
  page, 1 min) and MM9's own DAT lightmaps on it (`transfer`, 20 min). MM9 lightmaps only 3 289 of the isle's
  polygons (64 LT a texel); the 14 043 unlit ones (mostly terrain) keep the bake, scaled to the transferred texels
  around them (x1.8-4). Lightmapped faces take no daylight: MM9's noon at every hour. `lighting_test.py remove`
  restores the unbaked look; any rebuild makes the game ignore the sidecar until `transfer` runs again.

## Swimmers (2026-11-04)

- MM9's ten Jellyspores and the Sea Monster Male (`SeaMonsterMale` added to `monster_classes`) swim in the sea
  (rows Fly `YS` / `S`; models on the swimmer rule, `../../creatures/mm9_jelly_claude/README.md`,
  `../../creatures/mm9_seamon_claude/README.md`). `outdoor_blv.py` `swimmer_foot` puts each body box's centre at the
  MM9 position, under the surface and over the seabed: the spores' feet at -169 (their MM9 spots 40 LT under the sea),
  the Sea Monster at its MM9 spot (-16 973, 4 549), foot -187: MM9 has it 33 LT over the sea, treading water, so it is
  lowered until its box is under the surface (head and sail out). JellySpore3, 4 and 9 (in the far sea, no seabed)
  move to the nearest point of the near box, 160 LT inside its walls: 1 730, 706 and 2 181 LT
  (`actors_moved_into_near_sea_lt`). Actors 25 and 38-46 are the spores, 48 the Sea Monster.
- The review root's tables predated the swimmer tags (spores Fly `Y`, Sea Monster `N`); refreshed
  (`review_root.refresh()` with the isle root) before the rebuild.
- Checks: `story.yml` (161 steps) and `chests.yml` pass. Headless (scratch scenario, party in the water): a spore
  follows a sinking party down to the bed (-169 to -885) and attacks there; the Sea Monster rises to the surface
  (centre 1 under it) and attacks a party floating there every 3 s from 490 units. In game (isolated, minimized):
  `work/swimmers_20261104/` tour shots (frozen world: from the surface, under it) and `fight/live_*.png` (live: the
  spore attacking the party on the bed, the Sea Monster at the surface attacking a floating party, "Ariel evades
  damage" in both logs).
- Seen from above the spores stay hidden: the deep sea is opaque. Under water near the near box's west wall the empty
  far side shows as flat fog colour (`work/swimmers_20261104/07-seamonster_under.png`).

## Open issues

- The sea under the outdoor view: fixed 2026-11-02 (the water renderer kept the fog of the frame it was built in,
  black before the sky's haze; it now takes each frame's). The outdoor view is on by default for outdoor maps
  (`outdoor_blv.py`, full view distance).
- Monsters for the pathing check only (2026-11-02, overrides.yml `outdoor: {test_population: 150}`, placed by
  outdoor_blv.py): MM9's 36 land monsters (bone thrashers, skeletoids, dragonflies, mites, skull throwers; the 10
  jelly spores float over the sea, the lich king and the sea monster are left out) plus copies near them. First run
  near the bone thrashers at (-2300, -10900): per second about 900 blocked moves, 1 500 path stops (failed, cooling
  down or deferred) and 800 crowd overrides out of 3 800 moves, where Sturmford's flat spot shows none.
- Monster barriers (2026-11-02): skeletons crowding the party on the bridges were pushed into the sea and could not
  climb out. MM9 lines its bridges and ledges with AIBarrier brushes that block only its AI; outdoor_blv.py now carries
  the 62 brushes over (716 invisible, untouchable faces in the scene's `actor_barriers`, monster-only walls:
  devdocs/INDOOR_OPEN_SKY.md "Monster barriers"). Headless check, eight skeletons spawned on the deck of the bridge at
  (3 900, -2 160): with the party at its south end four ended in the water before and none after (they wait at the
  deck's end); with the party mid-bridge all eight stay on the deck round it. A monster that starts outside the
  barrier line (on the side beam) can still step off, and one already in the water still cannot climb out.
- Terrain3, the islet the cinema sinks (a Door in MM9: 1 000 LT down in 20 s), stays static: as a BLV door its 836
  faces would join every collision query of the map (the sector face grid lists a mover's faces in every cell). The
  story logs it as `[MM9Unsupported]`, with the cinema's cameras, fades and the sailing boat.
- The far west exit to Sturmford (ExitTrigger0, at sea about 43 000 west) lies outside the int16 frame.

## Cinematic (2026-11-06)

The book's cinema (IsleAshesBook.scr) is the in-engine cinematic `book_sinking`: `../mm9r_isleofashes/story.py`
`Story.cinematics()` builds it from the DAT cameras with the shared emitter `../mm9r_common/cinematics.py`, and
`convert.py` installs it as `worlds/mm9/maps/isleofashes.cinematics.yml`; the map Lua (`regionlua.py`) keeps its
gameplay steps as map events 31010-31015 (done event 31019) and starts it from the book's Use with `evt.PlayCinematic`
([MM9_CUTSCENES.md](../../../devdocs/mm9_rework/MM9_CUTSCENES.md) section 8). Scenarios: `cinematic_play.yml`,
`cinematic_skip.yml` (run against a root holding the converted map and its cinematics file).

## User play-test 2026-11-06 (the 19:44 promotion)

- **Forad and Yrsa faced a quarter turn off**: `convert.py` copied the old ODM import's `initial_yaw_units` (-ry) over
  the shared actor builder's facing (90 - ry, `dungeon/source.py` `facing_degrees`): Forad 342 -> 854, Yrsa 538 ->
  1050 (Annud Redeye 0 -> 512). Fixed by keeping the builder's.
- **No dialogue, only the quest effect** (Forad, Yrsa): not the map. Their compiled DoRudeUse (53061, 53046) runs (the
  key, 800 experience, quest.wav), then `MM9.openRude` finds no RUDE dialogue: the user's game runs with
  `start_world=mm6`, and `GameDataLoader::loadMm9RudeDialogueTable` (and the other MM9 tables: skill trainers,
  hirelings, transport routes, quest interactions, map transitions, teacher schedules) loads only when the active world
  is mm9. Headless: `world: mm6` reproduces it (`actor_dialog_rejected kind=mm9_rude rude_id=2 has_dialogue=false`),
  `world: mm9` opens Forad's three topics. Engine work, left for the user's decision.
- **The floating chest** (TreasureChest1, -5 451, -17 034): the isle's props.json has its three chests at their DAT
  height (MoveToFloor 1; Chest1.ABC's origin is mid-height), 30-66 units over the floor; the other regions' props
  projects already set theirs on the floor. Shared fix: `dungeon/content.py` `chest_on_floor`. Contents: MM9's
  TreasureChest1 is an ordinary random chest (Random 1, Item1-5 empty, TreasureLevel 0), so the balance's 3 records at
  level 1 are right; headless it holds 5 items (mm9) or 7 (mm6 world), not one letter.
- **Light and dark triangles on the cliffs**: the static lights' front-only rule (`static_lights: {sides: front}`, for
  the cities' house walls): MM9's Light 7 (radius 2 560 over the cliff top at -696, -18 493) lit the cliff facets
  tilted toward it and none of their neighbours. Not the lightmaps (terrain faces take none), the blend or the normals.
  Shared fix: `outdoor_blv.py` writes `sides: both` (all 12 regions, on their next conversion).
- **Light strips across the tunnel floor**: two ashdirt3 strips of the PhysicsBSP (36 and 20 units wide, faces 2386
  and 2387) drawn as terrain because of their texture: the blend took the mountain top's rock from the weights over
  them and the daylight lit them. Shared fix: `terrain_blend.py` excludes terrain-textured floors 128 units or more
  under the terrain on a polygon MM9 lightmapped (`terrain: {exclude_faces}`, engine `IndoorTerrain::excludedFaces`),
  and `dungeon/lighting.py` charts them (`bake_indoor.py --keep-faces`) so they take MM9's lightmap. Isle 8 faces
  (the strips, a tunnel floor piece, five nwrock floors at the tunnel's west end), Sturmford 1, Guberland 53, the other
  regions none.
- **Skeletoids rising again and again**: not the summons. MM9's chain (Isle_Summoner.scr, Isle_SpawnCreature.scr)
  caps at six and ours holds (headless: six summons, then none after 2 days, a save/load, a re-entry after 30 days;
  only the 600-day refill, MM9's own MAPSTATS Respawn 600, starts it over). The cause was the shared MM9 AI's
  resurrection: a resurrecter corpse (Skeletoid, Bone Thrasher: MONSTERS Resurrect 1) raised itself after every
  death. MM9 raises a monster once per script start (AICOMMON.inc :OnDeathDone clears g_bCanBeResurrected, which only
  BaseInit sets again). Fixed in `GameplayActorAiSystem.cpp` `AI_Mm9Corpse` (`ActorMm9State::risen`), every MM9 map.
  Also: the Lich's death now ends the summons (`story.lua`, Isle_Summoner.scr's OnDeath), not only the islet's fall.
- **The compiled RUDE hooks** (`mm9_scr_to_lua.py`) carried each script's whole variable table (YRSA.scr's
  baseMelee.inc globals, about 100 `MM9.scrValue` lines); they now declare only what their routines use. RUDE ids
  checked: Yrsa 1 and Forad 2 (DAT NPCNbr, scene `mm9_rude_id`, NPC1/NPC2.rude, NPCNAME.rude) agree.

## Map Lua: hand-ported like the other regions (2026-11-06)

The isle's map Lua is a hand port, as every region's: `regionlua.py`, loaded by `../mm9r_common/outdoor_blv.py`
`map_script` after the shared parts (the door groups' clicks, the chests, ForadWorld.scr's location key 1024 and the
shops' night key 5017, the stat stone, the shared objects). It replaces the generic story runtime (`story.py`'s
generated `Isle.*` tables, `mm9_scr_to_lua.py`'s compiled RUDE hooks and `story.lua`'s `on`/`send` message
dispatcher). Its structure, in `worlds/mm9/events/maps/isleofashes.lua`:

- named locals resolved by the converter from the built scene and the DAT: the story actors (`YRSA`, `FORAD`,
  `ANNUD`, `LICH`, `BONE_THRASHER0..3`, `STORY_ACTORS`), the doors (`BUNKER_DOOR1/2`, `HUT_DOOR`, `ISLET`), the cogs
  (`FORT_WALL`, `FORT_WALL0`, `BOAT`) and the points (the book, the summons' markers, the explosions, the shooters);
- one handler or local function per MM9 script entry point, each citing its .scr and lines: TM_Hardrock.scr's
  KillControl count, AutoResurrect.scr's `resurrect`, Isle_Summoner.scr / Isle_SpawnCreature.scr's `lichSpawn`,
  `updateSkeletoids`, `skeletoidKilled`, Isle_IslandExplosion.scr's `explode`, TriggerEffects, the fort walls,
  shooters, IS_Boat.scr's glide, Terrain3, ExitTrigger1, IsleAshesBook.scr's cinema steps (events 31010-31015, done
  31019) and Use (Book 30495, lectern 30496, PropTrigger.scr), DoorLock.scr's bunker (30498) and the hut door (30769);
- Yrsa's and Forad's OnUse (53046, 53061: their rewards, then `MM9.openRude`) and OnRudeExit (50046, 50061: the
  Turret Key, the dragonfly and mainline rewards; Forad's join XP and his removal once key 29 is held);
- the DAT triggers the party walks into (Trigger1, Trigger2, TriggerStarters) as functions built from their DAT
  messages, polled by the story tick (event 31000, 0.25 s), the monster-killed hook (31003), the leave event (31002,
  FORADWORLD.scr's TakeKey) and `handlers.regionLoad` (the on-load rules).

A message to an actor goes through the shared dead-receiver rule (`MM9.receives`, mm9_common.lua): a dead or removed
Lich takes no `spawn`, a dead Bone Thrasher no `RESURRECT`. Map vars keep the old names (`Isle.SummonCount`,
`Isle.TriggerCount.<trigger>`, `Isle.CinemaStep.<step>`, `Isle.BunkerOpen`, `MM9.SCR.483.count` ...). `Terrain3` takes
no click (`overrides.yml` `click: false`). `story.py` stays for the story actors (`convert.py actors()` places them
first, so their indices 0-19 hold) and the cinematic; the ODM pilot no longer builds.

## User play-test 2026-11-07: Forad Darre does not talk when walked up to, faces wrong

Captures and logs: `output/mm9_rework/isle_forad_20261107/`. Scenario: `forad_talk.yml` (passes against `assets_dev`
and the review root).

- **MM9 has no approach talk on the isle.** FORAD.scr arms `OnFoundPlayer OnTarget 256` -> `OnTargetWithinDist 16
  Talk` (DoRude 2) only in `:OnAppear`, the handler of an `Appear` message, and only Frosgard City's BattleMan.scr sends
  it (Forad's "HATE" copy there is hidden until the battle). On the isle he talks on Use only: OnUse gives key 480 and
  800 experience, stops and faces the player and bows (its own `DoRude 2` and voice are commented out); MM9's native
  NPC use plays the DAT `GreetingSound` (voices\NPC\NPC_002.wav), turns him to the player at 540 deg/s and opens
  RUDE 2 (devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md 2.4). No DAT trigger on the isle targets him.
  The other MM9 approach talks (OnFoundPlayer -> DoRude: Grandpa NPC436, Skraelos NPC336, Ivsar NPC90's Drangheim
  copies) have their 56000 + index handlers. Frosgard City's Forad (after BattleMan's Appear) and Thorolf
  (NPC378.scr, six cities: OnFoundPlayer -> RunTo 16 -> Talk) had none; ported 2026-11-07 as approach talks
  (`../mm9r_common/dungeon/lua.py` `approach_talk`, `thorolf_approaches`; ../mm9r_frosgardcity/README.md).
- **E / Space work** from the user's pose (headless and in the desktop game, `live_before/02-after_E_at_user_pose.png`):
  RUDE 2 opens with its topics and he turns to the party. Left click opens it only with Smart left click, as designed
  (modern scheme: left click attacks). Walking forward the party passes **through** him: OpenYAMM's party collides
  only with hostile actors, indoors and outdoors (`actorMovementCollidersForPartyMovement`, the outdoor regression
  `party_movement_ignores_friendly_actor_3_collision`), where MM9's NPCs are Solid. A shared rule for every world,
  left for the user's decision.
- **Facing is MM9's.** He stands at 150.2 deg (DAT ry 299.8 deg, native 90 - ry; `facing/02-from_his_front_150deg.png`
  is taken from that direction and shows his face), and keeps it (headless: unchanged after 60 s). The convention
  holds on the isle's other placements: Yrsa faces her hut door (11 deg off), Annud Redeye his ship (16 deg off); the
  old -ry would be 78 and 74 deg off. A talk turns him to the party and a save keeps that: the user's `save84`
  (07:21) has him at -91 deg after the talk, and hired (key 29), so hidden.
- **Fixed: the greeting voices.** `regionlua.py`: Forad's Use (53061) plays his GreetingSound before his dialogue, and
  Annud Redeye gets a Use handler (53747) that plays his (NPC_138) and opens RUDE 138, as MM9's NPC use does.

## User play-test 2026-11-09: too many monsters, rising again; chests too rich

- **Fewer grown copies**: `overrides.yml` `density_scale: 0.8` (shared `dungeon/density.py` `scale_adds`): 26 copies
  instead of 32 (the 3-copy pack adds 2, five 2-copy packs add 1).
- **Resurrection kept**: every Skeletoid and Bone Thrasher keeps its one rise (34 after the cut). A cap to 4
  (`resurrections: 4`) was built and installed, then withdrawn the same day at the user's call: the fewer copies should
  be enough.
- **Chests at T1**: `mm9_chest_balance.py` `TIERS` isleofashes (1, 1): the three chests roll record level 1 (T1 only)
  instead of 2 (T1-T2). The floor treasure follows the map's chest tiers: 7 markers T1, the bonus one T2.
- Rebuilt and installed 12:44 and again without the cap; the scene differs from the morning's by actors, `spawns` and
  `loot_containers` only (BLV, Lua and cinematics identical). `scenario_lifecycle.yml` passes.

## The Lich's Skeletoids reach the shore (2026-11-09)

MarkerTo, where each summoned Skeletoid teleports (Isle_SpawnCreature.scr Teleport), hung 23 units over the rebuilt
shore. The game places a teleported actor only on a floor within 16 units (`IndoorWorldRuntime::placeMapActorAt`),
so every Skeletoid stayed on the Lich's islet, marked as fighting, and the map's progress stopped short of 100 %.
`regionlua.py` now writes MarkerTo on the floor under it (`on_floor`), marks a Skeletoid fighting only once the move
took, and moves the ones older saves left stranded at MarkerFrom. Scenario:
`tests/scenarios/mm9/isle_lich_skeletoids_reach_shore.yml`.

## The Lich's summoning gesture (2026-11-11)

`Isle_Summoner.scr :SpawnCreature` plays `hattack1` at each spawn; `regionlua.py` plays the Lich King's `attack_melee`
(MM9's Hattack1) in `lichSpawn`. Checked headless: TriggerStarters' two spawns set the clip.
