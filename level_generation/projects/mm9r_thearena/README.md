# MM9 rework: The Arena (`thearena.blv`)

MM9's arena in Thjorgard City (`THEARENA.dat`, its front door from Thjorgard City) converted from its DAT world into a
native indoor map (BLV: sectors, portals, rotating and linear movers, lights, an exit volume) on the shared dungeon
converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review
root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the two new prop
models ([props project](../../props/mm9_thearena_claude/README.md)). No x4 textures yet.

Status 2026-10-31 (overnight run): geometry, 4 rooms, 6 movers, 16 lights, 22 decorations, the Arena Master, Sven's
double, two clan soldiers and Byri the Scarred, MM9's arena fights, bouts and bets and Jarl Sven's plot as native Lua, and
baked lighting. The NPCs have no MM9 3D models yet (stand-in peasant and guard rows).

## Build and review

```sh
python3 level_generation/projects/mm9r_thearena/convert.py --plan   # rooms only: work/rooms_<storey>.png
python3 level_generation/projects/mm9r_thearena/convert.py          # build, compile, install
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_thearena/bake.py
python3 level_generation/projects/mm9r_thearena/make_scenarios.py
for s in doors_exits fight lord bout sven; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_thearena/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_thearena
python3 level_generation/projects/mm9r_thearena/make_tour.py v04 [--original]
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated thearena_v04 --world mm9 --map thearena.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --position 0 -3686 1 --yaw-radians 1.5708 --pitch-degrees 0 \
    --warmup 3 --seconds 150 --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_thearena/review_tour_v04.yml
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated thearena_v04orig --world mm9 --map thearena.odm \
    --assets "$PWD/output/mm9_rework/assets_original" ... --set video.view_distance=unlimited \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_thearena/review_tour_v04_original.yml
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_thearena
```

## Files

- `overrides.yml`: every DAT world model's rule, the stair cut, the glass (crowd cards, the box's canopy), sky and
  sound-only texture substitutes, model lighting on.
- `convert.py`: the sky mapping, the counter's bars, the population (props, betting slips, NPCs) and every script (a
  `dungeon.Hooks` subclass). `pickmon.py`: MM9's arena monster table (`PICKMON.inc`) parsed and resolved to runtime rows.
- `bake.py` (the bake with MM9's sun, ObjectLights and stand fills), `make_scenarios.py`, `make_tour.py`, `hue_zones.py` (lightmap zones), `work/views_brightness.py`, `work/dump_dat.py` (DAT objects to
  `work/dat_objects.json`), `work/floors.py`, `work/blv_faces.py` (polygon and BLV face listings in a box).
- Profile: `tools/lighting/baked_indoors/profiles/mm9_thearena.yml`.

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). Floors: the hall and the arena 0 LT; the
  stands' tiers 192-400; Sven's box 192-224; the counter 48.
- 1 402 source polygons (PhysicsBSP and the static world models) -> 1 299 merged -> **1 222 native polygons** (41
  triangulated), 1 421 BLV faces, 2 096 vertices; 104 faces with no air in front dropped (`work/dropped_faces.json`:
  Invisible shells 44, the top ring's outer faces 28, stair sides 18, sound-only boxes 11: faces between brushes or facing
  out of the map; no thin partition among them, and `thin_walls` is on).
- **4 rooms** (+ sector 0): the hall with the Arena Master's booth (one room since the bars are a cut-out), the arena with
  the stands and Sven's box (one open bowl: no cut can close it), the west and east pens. One sealed air component, no
  leak. The stands and the floor cannot be split: the bowl joins them all round.
- **4 portal faces**: the arena door and the two pens (doorway portals from the leaves; no UserPortal in this map) and
  the archway cut in the stair from the hall up to the south stand. Every portal joins two rooms (`portals without two
  rooms` 0). Floor check: 0 LT2 of floor under another room's air. 8 mixed faces (`work/mixed_faces.json`): the pens' sill
  and door jambs and the stair's side walls across the cut.
- **6 movers**: `RotatingDoor0/1` (`rotate`, the arena door), `RotatingDoor2-5` (`dat`, the pens).
- **16 lights** (14 torches and Light14/15 in the hall), none over the four-per-point cap; `model_lighting: true`.
- **22 decorations** (14 torches, 4 banners, the throne, the chair, 2 betting slips), **0 chests**, **5 actors** (NPCs),
  **0 pads** (PlayerInTheHouse is a polled box), **70 translucent faces** (crowd cards, canopy; the 3 bar faces).

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP`, `WorldObject0` (top ring), `WorldObject1` (the box's canopy, arenafabric1), `WorldObject3` (the painted crowd, arenapeople1-3), `InvisibleBrush0/1` | static world, invisible collision; the crowd cards and the canopy translucent faces (cut-out by their alpha); `VisBSP` (no UserPortals here) not built |
| `WorldObject2` | the bars of the Arena Master's counter: an untouchable cut-out (the party talks to him through them; Deviations) |
| `RotatingDoor0/1` | the arena's double door: `rotate` movers (90 degrees, MM9's pivots and speed), one click, doorway portal from the leaves; locks in the map Lua |
| `RotatingDoor2/3`, `RotatingDoor4/5` (`Door`) | the west and east pens: `dat` movers (MoveDir along z, 76 LT apart), doorway portals |
| `ExitTrigger0` | MM9 positioned transition volume to Thjorgard City (start `ArenaExit`) |
| `StartPoint0` | start 0, facing into the hall |
| `Prop` (throne, chair, four banners), `Torch` (14) | 3D decorations (props project); each torch's `Light` is its BLV light |
| `ShopkeeperElfMaleB0`, `CommonerHuman2MaleB0`, `SvenArena`, `ClanSoldier0/1` | placed NPC actors (RUDE 430, 245, 428), friendly and immobile, MM9's bodies; Sven's party and Byri hidden until the plot |
| `Light` (16) | BLV point lights (none over the four-per-point cap) |
| `ScriptObject ArenaFight`, `Marker0-6`, `Soldier0/1`, `Sven0`, `Trigger PlayerInTheHouse` | the map Lua (markers as spawn and move points, the trigger a polled box) |
| `Fog0` (StartOn) | the scene's fog (grey 127, 64-11 520 native) |
| `skymarker` faces | `sky04` stretched (0.2 texel/LT), the bake's sky emitter |
| `RUDEProp Spectator0-10` | static decorations: MM9's seated peasant meshes in their PropAnim.scr pose (listen, conv1), mm9_thearena_claude "Spectators" (2026-11-05) |
| `WinCheerTrigger0`, `LooseBooTrigger0`, `AmbientSound` (30), `ObjectLight` (2), `AIRail`, `AITrk`, `OutsideDef0`, `StaticSunLight0`, `WeatherMan0`, `Fog1`, sky objects | not built (relays the Lua replaces with the cheer sound; ambient sound is a later pass; the rest AI, sky and bake helpers) |

## Scripted objects (`worlds/mm9/events/maps/thearena.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **The Arena Master** (`Arena.scr` :OnRude, RUDE 430) | event 50012 (his `OnRudeExit`), in MM9's order: with Sven's plan (key 230) and without 231, :Reset (no fights that day); 1018 (bet won): :GiveWin; 1009: nothing more today; 1011 (a bout or fight on): :FightWin once 1020 is held; 1010: :OnWatch; 1017: :OnBet2; else :FightCheck on 1004-1007 |
| **Fights** (`ArenaFight.scr` :OnPage/:OnSquire/:OnKnight/:OnLord, :GetCharLevel, `ArenaFightPlayer.scr`, `PICKMON.inc`) | the party's mean level L; levels [0.8L, 1.3L] / [0.8L, 1.5L] / [L, 1.7L] / [L, 2.5L] (89 cap over level 89, 4 under level 4); 1-2 / 1-3 / 1-4 / 1-5 opponents from MM9's table (a draw outside the range is drawn again, 400 tries, then the nearest); purse opponents x L x 20 / 30 / 50 / 100; key 1011; the party awaited |
| **Into the arena** (`Trigger PlayerInTheHouse`, :OnPlayerInTheHouse, :Startup) | a polled box past the doors: the doors shut and lock behind the party, the opponents appear in the pens (the first at Marker0, east; the rest at Marker1, west; HP x 0.7-1.5, no treasure: `GaveTreasure`), both pens open, they come out hostile |
| **The win** (:OnDead, :FightWin) | the kill hook: the fight's group all dead -> key 1020, the door unlocked, a cheer; "We won!" (430 slot 6) pays the purse, gives 1009 (no more fights this visit), takes 1020 |
| **The third labor** (`Arena.scr` :OnLord with key 214) | a Lord fight won with key 214 gives key 217 (no purse, as MM9) and ends the day |
| **Bouts** (`Arena.scr` :Init, :pick, :OnWatch, :OnMonsterDead, :BeVictorious; `ArenaCreature.scr`, `ArenaVictory.scr`) | each visit draws a pair: A at a random level 1-89, B within 4 levels (not the same level), three bouts a visit then 1009; "watch a fight" (1010) or a placed bet spawns them non-hostile to the party, set on each other (`SetMonsterRelation`), the doors lock; the first death decides, the winner leaves 20 s later (hidden), the next pair is drawn, the doors unlock |
| **Bets** (`Arena.scr` :OnBet2, :OnMonsterA/B, :OnMonsterA/BWin, :GiveWin; `ArenaMini.scr`) | the wager (50-1000, rows 430/10) is taken, or "not enough gold" and the talk undone (`NoGold.inc`); the betting slips on the counter (where MM9's figurines stand, Marker3/4) name each contestant on a click, and with a wager placed a click bets on it (1019); MM9's odds: x1.5 on the stronger, x2 on one 6+ levels weaker, else the stake; the bout starts 3 s later; a win gives 1018 and the status line says so, "We won!" (430 slot 5) pays |
| **Doors** (`Arena.scr` :LockDoors/:UnLockDoors, `ArenaCreature.scr` :Init/:OnHate) | clicks toggle the arena door and the pens; locked doors say "The door is locked." |
| **Sven's double** (`SvenArena.scr` :OnWalk, :OnWave, :OnStart, :Boo, :OnUse, :OnRude; RUDE 428) | with key 230 and without 231, opening the arena door the first time: Sven's double and his two clan soldiers appear in the box (Sven0, Soldier0/1), trumpets, the crowd cheers, the east pen opens and Byri comes out to the middle, the crowd boos; a click on the double gives 1034 and opens RUDE 428, its end takes 1034 |
| **Byri the Scarred** (`NPC245.scr` :OnRude, :Run, :OnVanish; RUDE 245) | his rows (the letter: key 231 at node 202); after the talk with 231 he opens the arena door and runs off (moved to Marker6, then hidden) |
| **Map load** (`Arena.scr` :Main, :OnPostStartWorld; `ArenaFight.scr` :Main; :Init of SvenArena/NPC245) | each visit starts afresh: 1009 and the day's keys taken, the doors unlocked, Sven's party and Byri hidden, what an earlier visit left standing in the arena hidden, the first bout drawn |
| `PropAnim.scr` (11 spectators) | the pose as a static model (no loop; no seated 3D peasant exists) |

## Why not ArenaRuntime

OpenYAMM's `ArenaRuntime` (`game/gameplay/ArenaRuntime.cpp`) is the MM6-MM8 arena: an NPC topic (704) offers four
difficulties, 6-20 opponents are drawn from a monster id range by `arenaDrawLevel`, the party is teleported onto the
floor, and a win pays level x 50-500 gold, MM8's arena award (45 + difficulty) and the arena-win variables. MM9's arena
shares only the four difficulty names: the Arena Master is a RUDE dialogue (430) whose rows set keys, his `OnRudeExit`
(Arena.scr) reads them; 1-2 / 1-3 / 1-4 / 1-5 opponents come from MM9's own table (`PICKMON.inc`, MM9 monster classes by
level) at levels relative to the party's mean, out of two pens behind sliding doors, while the party walks in through a
door that locks behind it; the purse is opponents x level x 20 / 30 / 50 / 100; a Lord win pays the third labor's key
instead; and the arena also runs bouts between two monsters that the party watches and bets on. Reusing `ArenaRuntime`
would put MM8's rules, awards and teleport into MM9 and still need the bouts, bets, pens and keys. The port is map Lua
over the existing calls (`SummonMonstersById`, monster groups, `SetMonsterRelation`, the kill hook, `CheckMonstersKilled`,
door states, quest keys): no engine change.

## Baked lighting and brightness

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`bake.py` (the shared `dungeon/lighting.py` plus three kinds of bake-only lights) with
`tools/lighting/baked_indoors/profiles/mm9_thearena.yml`: one 4096 x 913 page, 64 samples, 3 bounces, direct 0.85,
bounce 1, ambient 0.55 (sector level 20), sky 0.1 (the `sky04` faces an emitter, display 1.1), `max_lighting: 1`, the
crowd cards (`arenapeople1-3`, MM9 FullyBright) floored at x1 through the profile's `glass` level. About 2 minutes of Cycles.

MM9 lit the open bowl with `StaticSunLight0` (pitch 60, yaw 60, white, BrightScale 1): its lightmaps put the pens (no sun,
no light) exactly at the world's AmbientLight 60/255 = 0.22 and the sunny stands and Sven's box at 0.6-0.78. The runtime
has no sun, so `bake.py` adds it as a bake-only point light 20 000 units out along MM9's sun direction (a flat window: a
parallel light), at 0.7 of a map light; MM9's two `ObjectLight`s (over the arena's middle and at the counter) at 0.7 x
their BrightScale; and nine white fills (radius 520 LT, 1.6) under the stands' gallery roofs and in the box, where the sun
cannot reach in our bake but MM9's lightmaps are bright. With the first bake (sky only) the stands and the box came out at
0.52-0.75 of MM9 and the hall at 0.70.

**Lightmap texel luminance, ours / MM9's DAT lightmaps** (`hue_zones.py`, `../mm9r_common/hue_vs_lightmaps.py`,
`work/zone_ratio_final.txt`): hall 0.39 / 0.46 = **x0.85**, arena floor 0.66 / 0.57 = **x1.16**, east pen x1.04, west pen
x1.07, south stand x1.11, east stand 0.48 / 0.62 = **x0.77**, Sven's box 0.67 / 0.78 = **x0.86**. Hue: MM9's lightmaps are
neutral everywhere (B/R 0.94-1.00); ours 0.88-0.99 (the torches' 255/255/191 in the hall). Off by more than 10 %: the
arena floor (+16 %, the sun and the middle ObjectLight on open sand), the east stand (-23 %) and the box (-14 %) (the roofs
over the back tiers; more fill would brighten the floor under them too), the hall (-15 %).

Screen means of the 26 tour views (centre crop, `review/brightness_v04.txt`; the original captured at
`view_distance=unlimited`, information only: the old import drawn by our outdoor renderer is no brightness reference):
capture 89.6, native unbaked 101.1, **baked 74.7**. The pens are MM9's darkest place (lightmap 0.22, luma 18.6 at the pen
doors): above the no-pitch-black floor of 10-12 without any lift. The hall views 45-64, the arena 64-90, the stands 85-96.
No real MM9 screenshot of this map exists (`devdocs/mm9_rework/overnight/real_mm9/`).

Sheets: `review/v04_compare.jpg` (26 views, MM9 original | native baked), `review/lighting_v04_compare.jpg` (original |
unbaked | baked), `review/lighting_v04_detail.jpg` (six views large). `stale_bakes.py --check` does not list the map.
Rebake after any `convert.py` that changes the BLV.

## Checks

- **Scenarios** (all pass on the final build, real clicks on the Arena Master, the doors, the pens, the betting slip, Byri
  and Sven's double): `scenario_doors_exits.yml` (the front door raises ExitTrigger0, object 7; the shut arena door stops
  the party, opens on a click, the party walks into the arena; both pens open on clicks), `scenario_fight.yml` (Page by
  RUDE 430's rows: key 1004, the party awaited; past PlayerInTheHouse the doors shut and lock, a hostile opponent comes out
  of the east pen, the locked door does not open on a click; the last kill gives 1020 and unlocks it; "We won!" pays the
  purse (200 gold that run) and gives 1009), `scenario_lord.yml` (with key 214 a Lord fight won gives 217),
  `scenario_bout.yml` (a 50-gold wager taken, the slip's click bets on A, the contestants spawn non-hostile at the pens'
  mouths, meet in the middle and fight (HP dropping), B falls: key 1018, the winner leaves, the second bout is drawn,
  "We won!" pays 75 = 50 x 1.5 on the stronger), `scenario_sven.yml` (with 230 the master's fight is undone; the arena door
  brings Sven to Sven0 and Byri to the middle, the east pen opens; Byri's rows give 231, he opens the door and is gone;
  the double's click gives 1034 and opens RUDE 428, its end takes 1034).
- **Walkability** (`work/walkability.json`): 29 steps, all the stands' tiers (40-41 the 16 LT tiers, 61 and 81 the diagonal
  stands' 24 and 32 LT tiers, Deviations) and one 33 lip at the stair's foot; no flight, no pit, no mover or actor notes. Its
  four "unreachable" regions (0.32-0.42 M units² each) are the upper tiers of the four diagonal stands, 41 over their open
  floor: real for the party and for monsters, MM9's player climbs them; nobody fights there (spectator seating).
- **Starts**: StartPoint0 on the hall's floor facing north into the map (tour view h01).
- **Compiler unit tests** (`openyamm_indoor_source_tests`): 21 cases pass.
- **Lights**: no floor point under more than four (`content.json` `light_coverage`); the bake current.
- **Model lighting** on (no light over the cap): the throne, banners and torches read as in MM9's capture in the baked views.
- **Not checked**: the contestants' and opponents' fights beyond the probes (who wins, monster AI in the pens with several
  opponents at Knight/Lord); the native arena's crowd and ambient sounds (none built); the party jumping the counter into
  the booth; a save and load in the middle of a bout (documented as a reset); actor models (stand-ins); x4 textures.

## Deviations from MM9 and why

- **No walking NPCs or monsters on markers.** MM9 walks Sven, his soldiers and Byri to their markers and runs the
  contestants to the arena's middle (Marker2) before setting them on each other; native actors do not follow markers:
  the NPCs are moved while hidden (Sven's party) or moved in one step (Byri to the middle, Byri out to Marker6), and the
  bout's contestants appear at the mouths of the open pens (two monsters left in a pen do not wake while the party is in
  another room). Fight opponents appear inside the pens and come out on their own (they sense the party).
- **The spawn at the party's entry.** MM9 spawns a fight's opponents when the talk ends and holds them in the pens until
  the party passes PlayerInTheHouse; here they appear when it passes (the pens are shut until then: the same to see).
- **The figurines are betting slips.** MM9 shows the next bout's two monsters as figurines at 0.3 scale on the counter
  (`ArenaMini.scr`, Spawn2 with Scale .30); native actors have no per-actor scale, so two `mm9_scroll` slips stand there,
  name their contestant (east gate / west gate, class and level) on a click and take the bet.
- **ArenaFight.scr's typo fixed.** :OnPage/:OnSquire/:OnKnight/:OnLord draw `nNumberMonsters` (1-n) and pay for that many,
  but spawn the extra opponents under `nMonsterNumber`, a variable no script declares: MM9 spawned one opponent and
  waited for n deaths, so any fight drawn with more than one could never be won. The native fight spawns the number it
  pays for.
- **A Lord draw that cannot be met.** MM9 draws again until a monster's level lies in the range; at Lord over party level
  about 80 no table entry does (the table ends at 80) and MM9's script would loop for ever. Here 400 draws, then the
  nearest.
- **The third labor ends the day.** MM9's :FightWin with key 214 gives 217 and keeps 1020 and 1011 (the same "We won!"
  again, no new fight that visit); here it also takes 1020 and gives 1009, as the purse branch does.
- **Classes without a runtime row** (the clan soldier ranks, the poor town guards of groups 7, 13, 16, 18) are drawn
  again, as an out-of-range draw is.
- **No saving in the Arena** (the user, 2026-11-09), as in MM6-MM8's arenas: the scene's `runtime_restrictions`
  forbid saving and Lloyd's Beacon (not `arena: true`, MM6-MM8's ArenaRuntime). MM9 allowed it, but the map Lua's
  waits are not saved and its map-load handler starts every visit afresh, so a game saved in here lost a won Lord
  fight's purse and key 217, and Sven's staging (`tests/scenarios/mm9/no_save_maps.yml`).
- **The stands' diagonal tiers** step 24-32 LT (61-81 native): MM9's player climbs them, the party (50) does not; the
  straight stands (16 LT tiers), Sven's box and the south stand are reachable (audit, Checks).
- **The counter's bars** are an untouchable cut-out (MM9 solid): the party talks to the Arena Master through them; the
  48 LT counter keeps it out of the booth.
- **Crowd**: the 11 spectators sit in their MM9 poses (static seated meshes, mm9_thearena_claude); the painted crowd
  cards (`arenapeople1-3`) are built.
  `WinCheerTrigger0`/`LooseBooTrigger0` switch MM9's crowd AmbientSounds on; here the Lua plays the cheer.
- **Sky**: `sky04` instead of MM9's SnowMtns sky box; MM9's time-of-day sky (`TOD_Sky0`) is not carried.

## Open items

- MM9 3D models for the Arena Master (ShopkeeperElfMaleB, PeasantMale.abc), Byri, Sven (Sven.abc) and the clan
  soldiers (ClanSoldier.abc; the MM9 Guard row's model stands in): the creature work. The spectators' loops (MM9 plays
  listen/conv1) wait for seated 3D peasants.
- Ambient sound (30 `AmbientSound` objects: the crowd's loop, cheers, boos): a later pass.
- Invisible ramps over the diagonal stands' tiers if the party should climb them (Dook's Castle's route).
- A density and pack pass (PLAN.md: later); x4 textures last.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:02:17 (convert.py from the current shared converter, end 15:02:25): 54 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 1367 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_bout.yml` pass, `scenario_doors_exits.yml` pass, `scenario_fight.yml` pass, `scenario_lord.yml` pass, `scenario_sven.yml` pass.
Blocker probes: 8 walks into helper brushes resting on the floor stop short of them, 8 identical before and after (their sides still block).

## Sven's wave (2026-11-11)

`SvenArena.scr :OnArrive` waits 2 s, then `:OnWave` cheers and plays `Bless`; `convert.py` plays the double's `bless`
there (his soldiers' bodies, MM9's ClanSoldier too, have none). `scenario_sven.yml`, `scenario_fight.yml` and
`scenario_bout.yml` pass; desktop captures `output/held_items_check/b3_arena/close5.png`. In the desktop game the wave
comes about 8 s after the door opens, not 2 s: the map's 0.25 s poll (`after`) ticks about once a second there
(headless it keeps 0.25 s), so all its waits stretch alike.
