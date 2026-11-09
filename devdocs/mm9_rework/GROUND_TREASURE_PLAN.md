# Ground treasure in the MM9 maps (plan)

Status: **implemented** (2026-11-08): `tools/mm9_import_discovery/mm9_ground_treasure.py` (counts and tiers),
`level_generation/projects/mm9r_common/dungeon/treasure.py` (placement, run by every conversion)
and each map's `overrides.yml` `treasure` hints. Markers roll as MM6–MM8: 20% nothing, 40% gold, 40% an item.

MM6–MM8 dungeons have treasure markers: spawn points of type 2 whose index is a treasure level. On the map's first
visit (and after a refill) each one rolls a random item of that level and lays it on the floor. MM9 had nothing like
that: its loot was in chests, bags, bone piles and monsters. The user wants the rebuilt MM9 maps to use the markers,
placed with intent (mainly in dungeons, some in the outdoor regions, none in the cities) and at the location's
treasure level. The same session set MM9's chest tiers (`mm9_chest_balance.py` `TIERS`), kill gold (×2.2) and item
drop chances (×2); see [BALANCE_PLAN.md](BALANCE_PLAN.md) 3.3 and 3.8.

## 0. Decisions

The draft's open questions, settled here with the reason; the user can overturn any of them.

| Question | Decision | Why |
| --- | --- | --- |
| How many | About 390 markers over 28 maps (section 4), MM7's density adjusted per map | MM7's medians, minus what MM9's maps cannot use (friendly or trap-only areas) |
| Small change (MM7: a third of its markers roll 2+ tiers below the map) | **None**. Every marker rolls the map's chest tiers or one below; 15% roll one above | A visible pickup that is junk feels worse than a chest roll; the user's complaint that started this was junk |
| Regions | **6–10 each** (MM7's outdoor maps: 12), none in or beside towns | Regions already have chests, bags and searchable props; their playable area is mostly open slopes |
| Refill | As MM7: markers roll again when the map refills (`Refil Days` in map_stats) | The engine already does this; no MM9 exception |
| Artifacts | No artifact markers | The black chests give MM9's artifacts and relics (`chestArtifactsOnly`) |
| Gold or item | **As MM6–MM8: 20% nothing, 40% a gold heap, 40% an item** (the user, 2026-11-09). The first build gave MM9 items only (`treasureMarkersItemsOnly`, 2026-11-08, now removed) | With items only, no gold heap was ever found on the floor |
| Saves | Markers change each map's layout identity: a saved map state resets on its next entry (the party is kept) | Accepted (the user, 2026-11-08): the alternative is markers only on new games |

## 1. What MM6–MM8 did (measured)

Measured from the installed BLV and ODM spawn tables (`tools/export_indoor_scene_yml.py` and
`export_outdoor_scene_yml.py` readers): 161 MM6–MM8 indoor maps, 1,741 item markers. Floor area is half the
horizontal face area (floors and ceilings).

| | MM6 dungeons | MM7 dungeons | MM8 dungeons |
| --- | --- | --- | --- |
| Maps (floor > 2M units²) | 48 | 63 (54 with markers) | 46 (mostly none) |
| Markers per map, median (mean, max) | 4 (8.6, 42) | **14** (18.7, 81) | 0 (3.2, 25) |
| Markers per 1M units² of floor, median | 0.14 | 0.58 (quartiles 0.20 / 1.13) | 0 |
| Markers per monster spawn point, median | 0.16 | 0.93 | 0 |

MM7 is the model, and the reference the MM9 balance already follows. MM8 relied on chests; MM6 used markers sparingly.

- **By size** (MM7 medians): under 15M units² floor 8.5; 15–40M 22.5; 40–80M 22; over 80M 28.5. The largest are
  Tunnels to Eeofol (81), the Maze (73), Nighon Tunnels (50), Temple of the Light (45), Thunderfist Mountain and the
  Titans' Stronghold (44 each). The Barrows (5–9M units², 4–5 monsters) hold 23–36 each: crypts are treasure rooms.
- **Outdoors**: MM7's 13 maps, median 12 (Emerald Island 0, Harmondale 6, Shoals 28). MM6 and MM8: none.
- **Levels**, rolled tier against the map's: one above 3%, the map's own 47%, one below 16%, two below 16%, three or
  more below 18%. Artifact markers: 14 in all three games.
- **Guarded**: 71% within 1,000 units of a monster spawn point (median 577); 3% over 3,000.
- **Piled**: 34% have another marker within 300 units, 74% within 1,000: stashes of two or three.
- Every MM7 marker has radius 32 and attributes 0.

## 2. The engine side (exists, no change needed)

- An indoor scene's `spawns` list replaces the BLV's spawn table (`IndoorSceneYml.cpp`, `hasSpawns`). The MM9 BLVs
  have no spawns and their scenes no `spawns` key, so the converters write the markers into the scene: no BLV
  recompile. Entry: `{spawn_index, position: {x, y, z}, radius: 32, type_id: 2, index: <1-6>, attributes: 0,
  group: 0}`. The outdoor regions are BLVs open to the sky (`outdoor_blv.py`): the same path.
- `IndoorWorldRuntime::materializeInitialMonsterSpawns` rolls every type-2 spawn through `generateTreasureSpawnItem`
  on the map's first entry and after a refill (`lastRespawnDay == 0`), seeded per session, map and spawn index. The
  index is remapped against the map's treasure level as a chest record is (`remapTreasureLevelRange`), and the item
  comes from the shared generator and pool, as every chest and drop.
- MM9's own items have ground models (`worlds/mm9/world_items/items.yml`), as monster drops already need.
- **Saves**: spawns are part of a map's layout identity
  ([SAVED_MAP_STATE_IDENTITY.md](../SAVED_MAP_STATE_IDENTITY.md)): installing markers resets the saved state of each
  changed map on its next entry (the party is kept). Its chests reroll and its monsters return. Say so in the
  release notes.

## 3. Rules

### 3.1 Tiers

Each map's markers take three classes, from the map's chest tiers (`TIERS`) and treasure level:

| Class | Share | Tier | Where |
| --- | --- | --- | --- |
| Bonus | 15% (at least 1 where the map has secrets or a boss) | one above the chests' top where the map's treasure level reaches it, else the chests' top | secrets and boss rooms only (3.2, kinds 1–2) |
| Main | 55% | the chests' tiers | anywhere allowed |
| Lower | 30% | one below the chests' bottom (at least T1) | anywhere allowed; preferably the first rooms from the entrance |

A marker's index is the lowest one the engine remaps to exactly that tier range on the map's treasure level
(`record_level_for_tiers`). The class tiers per map are in section 4.

### 3.2 Where

The converter scores candidate floor spots and fills a map's count in this order:

1. **Secrets**: behind secret doors, switch-opened and pivot walls, rotating bookcases, breakable walls and boards
   (`destructibles`), inside PerceptionBrush areas, in rooms reached only through those. Bonus markers go here first.
2. **Boss and lieutenant rooms**: the room of a boss or unique actor (mm9_ai `boss`, unique rows, the scripted
   set-piece monsters the map's hints name) takes a stash of 2–3, one of them Bonus.
3. **Dead ends**: rooms with one doorway portal (rooms.py's portal graph), alcoves, the far end of side branches,
   ledges and platforms reachable on foot or by ladder.
4. **Guarded rooms**: rooms with a hostile pack, on the far side of the pack from the room's entrance. Target: about
   70% of markers within 1,000 units of a hostile actor, as MM7.
5. **Themed rooms**: treasuries, armouries, barracks, libraries, storerooms, crypts and tombs, altars (section 4
   names them per map); beside bone piles, corpses, crates and tables, so an item reads as dropped or stored.

Shape rules:
- About a third of markers in stashes of 2–3 within 300 units; the rest single.
- At most 3 markers in a room (5 in a boss room or a treasury); a room with a chest takes at most 1.
- At least 1,000 units between stashes in the same room.

Never:
- on the main route's floor (the shortest floor path from the start to each exit), within 1,000 units of a start
  or exit;
- in water, lava, slime or acid, on a pool bed or seabed, in a pit, on an event face (pads, traps, shooter plates,
  exits), in a doorway or a door's or mover's sweep, on a ladder, in a crusher's or pendulum's reach;
- in peaceful areas: rooms whose actors are all friendly (Dook's audience room, the dwarves' halls, the Honks'
  temple), shops, NPC rooms, cinematic and set-piece areas, puzzle boards;
- on a spot not reachable on foot or by ladder from the start: swimming-only and script-only spots are out
  (the floor graph decides, not the docs);
- in the cities, or within 3,000 units of a region's town exit, dock or building cluster.

### 3.3 Outdoor regions

Same rules over the near box only (`outdoor_blv.py`: the far scenery is a sea surface with no floor):
- Anchors: dungeon and cave mouths (a stash a little aside from the arrival point, never on it), monster
  concentrations and their bosses, cliff tops and ledges reached by a path or ladder, ruins, cottages and huts
  away from towns.
- Never on the beach line under sea level, on quest props or beside quest NPCs, in fairgrounds, docks, the
  battlefield tableau or other cinematic areas, or on slopes the party cannot climb (`steep_slopes: block`).

## 4. Per map

Counts start from MM7's density (size class capped at 0.35 per hostile actor) and are adjusted for what each map's hints
exclude. Tiers: Bonus / Main / Lower, computed by `mm9_ground_treasure.marker_tiers` (bonus: one above the chests'
top where the map's treasure level reaches it, else the best it gives up to that). Hints come from
the map projects' READMEs, convert.py and overrides.yml; the converter finds the actual rooms and spots.

### Act 1 (map treasure level 1: nothing above T2)

| Map | Markers | Bonus / Main / Lower | Hints |
| --- | --- | --- | --- |
| Beethoven (sewers) | 24 | T2 / T2 / T1 | Bonus: behind `HedgeDoor1-3` (the maze's false walls), past `SDoor11/12` (Lever5/6). Anchors: the catacombs (coffins, mummies `PetrifiedMummy0-7`), the maze, the ledges up `Ladder2/4/7/8`, `Ladder0`'s shaft under the hub, the lower sewers past `Ladder1`. Clear: slime channels (`WaterTop1/10`), the baths' pools, the Grand Entrance cavern, the end of the bottle's path (Ludwig's manuscript). |
| Anskram Keep | 18 | T2 / T2 / T1 | Bonus: the pivot niche (`PivotWallTrap1`), the PerceptionBrush spots on the west diagonal and in the airlock side rooms. Boss: the Giant Imp's arrival at the central shaft's top. Anchors: the barracks (beds, dressers, weapon cabinets), the bookcases. Clear: the pivot-trap pits, crusher plates, shooter plates, the airlock between `Outerdoor` and `Innerdoor`, the shaft over `Floordoor1-4`, the sealed Imp gate alcoves. |
| Isle of Ashes (region) | 8 | T2 / T1–T2 / T1–T2 | Anchors: the bone thrashers' ground near (-2300, -10900), the cliff top near (-696, -18493), the tunnel's ends, the trail up the valley. Clear: the sea and Terrain3 islet, the fort walls (cinematic), the bunker and lectern, Yrsa's hut. |
| Sturmford (region) | 8 | T2 / T1–T2 / T1–T2 | Anchors: the abandoned fort's tower tops (Ladder0/1), the Weakwall, the thrall and basilisk grounds. Clear: the city exit and docks, the sea, the keep's scripted doors. |

### Act 2

| Map | Markers | Bonus / Main / Lower | Hints |
| --- | --- | --- | --- |
| Drangheim (region) | 8 | T4 / T2–T3 / T1 | Anchors: the bandit and burglar ground, the rope ladder `Ladder5`'s top by DPSecretExit, the cottage, the dungeon mouths (prison, Chasm). Clear: the city exit, the sea, the quest props (Plow, Herbs, Dolly), Ivsar outside the prison. |
| Drangheim Prison | 14 | T4 / T2–T3 / T1 | Bonus: behind `SecretDoor0` and the cook's door `Door2`, the PerceptionBrush panels, the secret well (`Lid1`, `Ladder1`). Anchors: the lower levels past `Ladder5`, the guard station, the barracks. Clear: the cells and their levers, the interrogation room, the forge and lava, the animal pens, the quest NPCs. |
| Guberland (region) | 6 | T4 / T2–T3 / T1 | Needs `TIERS` (2, 3) and `MAP_TREASURE_LEVEL` 2. Anchors: the bandit route between SpawnMarker and Atlimarker0, the second landmass (Terrain1), the dungeon mouths (Dook's Castle, Temple of Honk). Clear: the fairground, the dock and the guard's post, the far sea, the town exit. |
| Thjorad Mine | 18 | T4 / T3 / T2 | Needs `TIERS` (3, 3). Bonus: behind the hard rock `db12-db23` (Ebora's chamber: not near her and the cats while the cinematic area is live; place at the chamber's sides), behind `CaveWall0-4`, the gnoll cages (`BustOutBrush0-2`), the slag hatch `RotatingDoor0`. Anchors: the boarded abandoned mine and its west room (`AB_Troglodyte2-5`), the refinery's edges. Clear: the dwarves' halls (10 friendly), the lava crucible, the exploding-barrel run, the flooded cavern under the cave-in. |
| Ta'Sar Academy | 8 | T4 / T3–T4 / T2 | Bonus: the store room behind `SecretDoor0` (the crate Dagrell), behind `RotatingBookcase1`, the pit tunnel past the cracked wall, the library behind `LibraryDoor`. Bosses: `GuardCaptain0`, the two `HalfOrcCaptain`s. Anchors: the tower tops (`Ladder0/1`), the skill-book and chalice tables. Clear: the spike pit and its trap doors, the arena's sparring floor, the animal pens. |
| Dook's Castle | 12 | T4 / T3 / T2 | Bonus: the caverns behind `doorslide` (the shield `Sheild0`), the bridge platform up `Ladder0`. Anchors: the north caves (winged mutants, basilisks, Trellborgs), the throne room. Clear: Dook's audience room and the friendly militia's rooms, the lake and its bed. |
| Training Hall | 10 | T4 / T3 / T2 | Bonus: the debris room and Ghoul caves behind the wooden wall (`upperbreak`/`lowerbreak`), the crate room. Bosses: the Mean Trellborg (joust hall), the TrainingCommander's podium, the lobby ghouls' perch. Anchors: the west crow's nest. Clear: the roof arrival room, the lobby pool, the pole room's water and its pole-only ledge, the joust lanes, the archery targets. |
| Thjorgard (region) | 8 | T4 / T3 / T2 | Anchors: the jumper and robber ambush grounds, the Magreeb ambush (Magreeb0's ground), the mine and Training Hall mouths, the cottage. Clear: the city exits (dock, terrain), the fair, the refinery machine, the sea. |
| Thronheim (region) | 8 | T4 / T3 / T2 | Bonus: the King Basilisk's ground. Anchors: the basilisk and gezzampt grounds, the Connecting Tunnels and Inventastorca mouths. Clear: the town and dock exits, Bikki, the sea. |
| Lindisfarne (region) | 6 | T4 / T3 / T2 | Anchors: the Magreeb and sorcerer grounds, the upper floor up Ladder0/1 if outside the building cluster, the Ta'Sar and Dragon Stadium mouths. Clear: the building cluster and the monastery, the arrival bridge, the sea. |
| Frosgard (region) | 8 | T4–T5 / T3–T4 / T2 | Anchors: the yetis' cliffs (Yeti6-9 jump from them: the tops if reachable), the wolf packs, the gezzampt elder, the dungeon mouths (Dungeon of Secrets, Yanmir's Fort, Ruined Temple). Clear: the city exit, the Green Man's wander area, WavySurface4, the sea. |
| Mountain Pass (region) | 10 | T4–T5 / T3–T4 / T2 | Bonus: the Bigfoot's ground, the Imply's. Anchors: the imp markers (ImpMarker1/2), side ledges off the pass path. Clear: the path itself and both ends (ThronheimStart, ThjorgardStart, Trigger0/1). |
| Yanmir's Fort | 20 | T4–T5 / T4 / T3 | Bonus: behind `Secretdoor` (PerceptionBrush0), the east wing's north room (Yanmir's key), the trap hall basement. Bosses: Yanmir's hall (native -3277, -2294), the Forest Giants' and ThrallMasters' rooms. Clear: the children's cages, the trap hall floor and shaft (native ~(863, -7460)), the teleporter room, the west cave pool, the west gate. |
| Chasm of the Dead | 28 | T4–T5 / T4 / T3 | Bonus: the pivot alcove (`PivotWallTrap1`), Crona Kiga's crypt (`PetrifiedMummy16`). Anchors: the tombs (`Door1-35`), the dais under `Shooter0` (beside, not on, the plates), the mummy coffins, the buried zombies' ground. Clear: shooter plates and hidden shooters, the closing walls, the spike-wave stair, crushers, pendulums, the acid grate pit, the spike pit, the water channel. |
| Ruined Temple | 8 | T4–T5 / T4 / T3 | Bonus: past `HiddenDoor`, `HiddenDoor2`, `HiddenDoor3`, the spiral room and the chest room, the crypt under `DB_Crypt0`. Anchors: the crypt's skeletons and spectre Dagrells, the altar room, the Tree of Life's cell. Clear: the entrance hall's upper floor (arrival), the prison corridor, the cave-ins, the elevator shaft, the genie's sunken floor. |
| Inventastorca | 10 | T4–T5 / T3–T4 / T2 | Bonus: the wall niches (`SecretPanel`, `SecretPanel0`), behind the breakable walls `DestructableBrush0-3`, the Lich King's room. Anchors: the dead adventurers' party, the dressers and drawers, the Orbs of Linking's rooms. Clear: the flooded cavern and its bone piles, the well, the trapdoor over `Ladder5`. |
| Klusos's House | 5 | T4 / T3 / T2 | Needs `TIERS` (3, 3) and `MAP_TREASURE_LEVEL` 2. Bonus: the master bedroom. Anchors: the upper floor's sleepers' rooms, the kitchen. Clear: the dining room mantel (the Blackheart dirk's trigger), the front door and window starts. |
| Dungeon of Secrets | 3 | T4 / T3 / T2 | Needs `TIERS` (3, 3). No monsters: the 3 markers are prizes at the ends of the hardest trap sections (beyond the gauntlet, the double axes), never on their floors or plates. Clear: the hub, the lever room, the submerged tunnel. |
| Verhoffin Ruins | 14 | T5 / T4–T5 / T3 | Bonus: the torture chamber (pentagram puzzle), past `PrisonDoor2`'s bolt, behind `Door5` (key 559). Bosses: the Terrors' room behind DD14, the banshees. Anchors: the prison cells, the crevasse ledges (not the bed). Clear: the water trap room (native (596, -2241)), the saw corridor, the electrified pit and paddle, sector 19's unreachable pocket, the first chest's room (TreasureChest3 stays the easy early find). |
| Lich Lab | 24 | T5 / T4–T5 / T3 | Bonus: the explosion lab's cages (`DB1/DB2`, `breakwindow1/2`), the east lab (Oculus10's wall). Boss: the LichSummoner's ramp foot and the ghost pools' rim (not in the pools). Anchors: the skeleton transformer chambers' antechambers, the shooting range, the elixir rooms (herb bags, jars). Clear: the engine pods (`PromoVol1`), the transformer chambers, the pools. |

### Act 3

| Map | Markers | Bonus / Main / Lower | Hints |
| --- | --- | --- | --- |
| Yorwick (region) | 8 | T4–T5 / T4–T5 / T3 | Bonus: the Evil Grand Sorcerer's ground. Anchors: the vampires', specters' and sorcerers' grounds, the Wizard's Lab and Lich Lab mouths, the board gate's far side (`board0-4`). Clear: the town exits and stores, the battlefield tableau, Mary and her ewe, the sea. |
| Wizard's Lab | 22 | T5 / T5 / T4 | Bonus: the super eye chamber (EvilGrandSorcerer1, Oculus0), the master's room, the cell block's cells. Anchors: the bedrooms, the cauldron room's edges. Clear: the summoning tower top (ritual), Robinssen's prison, the pool under the cell block, the cauldron basins, the teleporter stations. |
| Connecting Tunnels | 8 | T5 / T5 / T4 | Bonus: the coffin hall (not inside the grave). Anchors: the vampire groups, the north-east chamber, the rock fall's far side. Clear: the three starts and their tunnel mouths. |
| Bathhouse | 12 | T5–T6 / T5 / T4 | Bonus: the room behind `Door6/7` (the Lesser Demon). Bosses: the Concubines' rooms. Clear: the boiling pools and their shafts, the steam vents, the furnace room, Ebora's tub room, the great hall's pool, the flooded tunnels and the swim-only chamber. |
| Dark Passageway | 24 | T5–T6 / T5–T6 / T4 | Bonus: the painting room (`DoubleDoorL40/R40`, 3 chests: 1 marker), the Colloidal Warrior's forest, the desert Terrors' room after the mirror puzzle. Anchors: the canyon statue ledge, the ocean hall's island (if reachable on foot), the pillared room's side platforms, one stash per sub-world. Clear: the bridge lake, the tube room and ocean, the canyon pit, the spike corridor, the Wyrde's room, the start room. |

### Act 4

| Map | Markers | Bonus / Main / Lower | Hints |
| --- | --- | --- | --- |
| Temple of Honk | 5 | T5–T6 / T5–T6 / T4 | Bonus: the treasury behind the HONK door (4 markers), the accountant's office (1). Clear: the temple and pulpit (friendly Honks), the pool. |
| 1000 Terrors | 28 | T6 / T6 / T5 (lower 60%: 17 T5, 11 T6; `LOWER_SHARES`, the user, 2026-11-09) | Bonus: behind `TreasureDoor`/`TreasureDoor0` (`HiddenButton1`), `SecretDoor2`, the three puzzle walls, the lower tombs past the tomb gate. Bosses: the end hall (Greater Demon), the upper hall's demon statues, `LesserDemon13/14`. Clear: the chess board, the water hall, the sea monster pool, the chess and entrance pools, the trap doors over the water pit, the sorceress-statue halls, Njam's hall and its win switch. |

### No markers

The cities (Sturmford City, Drangheim City, Guberland City, Thjorgard City, Thronheim City, Frosgard City, Arslegard
City, Boot Camp), the Arena, Dragon Stadium, Hall of the Gods, the Afterworld, Lindisfarne Monastery.

**About 390 markers**: act 1 58, act 2 228, act 3 74, act 4 33. A marker rolls once (`generateTreasureSpawnItem`);
each gives nothing (20%), a gold heap (40%) or an item (40%), so the campaign gains about 160 gold heaps and 160 floor items.

## 5. Implementation

### 5.1 Data

`tools/mm9_import_discovery/mm9_ground_treasure.py` (beside `mm9_chest_balance.py`, sharing its `REMAP`, `TIERS`,
`MAP_TREASURE_LEVEL` and `record_level_for_tiers`):
- `COUNTS`: section 4's counts.
- `CLASS_SHARES`: Bonus 15% (at least 1 where a map has kind-1 or kind-2 spots), Main 55%, Lower 30%.
- `marker_tiers(stem)`: the three classes' tier ranges, computed as section 4's columns.
- `marker_index(stem, tiers)`: the index to write (`record_level_for_tiers`).
- The new `TIERS` rows for Guberland (2, 3), Thjorad Mine (3, 3), Klusos's House (3, 3), the Dungeon of Secrets
  (3, 3), and `MAP_TREASURE_LEVEL` 2 for Guberland and Klusos's House (their chests, where they have random ones,
  follow too).
- Tests in `test_mm9_balance_profiles.py`: every map's classes reachable on its treasure level, the shares summing to
  the count.

Per map, `overrides.yml` takes a `treasure` block for the hints that are not visible in data:
- `bonus_rooms` / `bonus_near`: DAT object names (movers, destructibles, PerceptionBrushes, actors) whose rooms count
  as kind 1 or 2;
- `themed_near`: DAT object names of kind-5 anchors (bookcases, beds, weapon cabinets, coffins);
- `avoid_near`: DAT object names and positions with a radius (quest props, NPCs, cinematic areas, fairs);
- `place: [{at: [x, y, z], class: bonus|main|lower}]` for a hand-picked spot (counts toward the total);
- `count` replacing `COUNTS`.

### 5.2 Converter

`level_generation/projects/mm9r_common/dungeon/treasure.py`, run by `build.py` after pack growth (it needs the
final actors) and before the scene is written; regions go through the same `dungeon.main`:
- **Candidate spots**: density.py's spot test on the compiled BLV (on a floor, clear of walls, doors and movers
  along their travel, ladders, event faces, water volumes and liquid faces, other actors), sampled on a 128-unit
  grid per room. Reachable from the party start over the floor graph with ladders; a swimming-only or script-only
  spot is dropped.
- **Room features**: portal count (dead end), reached only through a secret (a mover with a secret trigger, a
  destructible, a PerceptionBrush, a `bonus_rooms` name), boss room, hostile actors and their side of the room from
  its entrance, chests, peaceful (all actors friendly), on the main route (shortest floor path from each start to
  each exit, widened by 256 units).
- **Selection**: Bonus markers into kinds 1–2 first, then stashes and singles by kind 3–5 score, the shape rules of
  3.2, deterministic from the map stem and spot order (a reconversion places the same markers, as density.py does).
  Lower markers prefer the rooms nearest the start. A map that finds fewer good spots than its count places fewer and
  reports the shortfall rather than forcing bad spots.
- **Output**: the scene's `spawns` in placement order; `work/treasure.png`, a top-down plan with markers coloured by
  class, stashes circled, actors, chests, secrets and the main route drawn; a build report line (count by class,
  guarded share, stash share, secrets used, shortfall).

As built (2026-11-08), beyond the draft above:
- Reachability also starts from where the map's mobile hostile monsters and its chests stand: the walk graph does not
  follow teleporters (Dark Passageway's sub-worlds, Wizard's Lab's stations), scripted lifts and some ladders, and
  without these seeds those maps placed 3 of 22-24 markers.
- Bonus places with no spot behind a secret or by a boss become main markers (the Chasm has one bonus spot).
- A stash anchor's score drops 1.5 per marker already in its sector (outdoors: within 4,000), so markers spread over
  the map instead of crowding its best-scoring rooms.
- Destructibles count as secrets only when they are walls, boards or lids, not `DestructableProp` barrels and crates.
- The regions skip the main-route rule (one open sector); their starts and towns keep clear instead.
- First run: 393 markers on 31 maps, no shortfall; 82-100% guarded (Temple of Honk and the Dungeon of Secrets have no
  hostile monsters), 20-50% in stashes. Checked in the game: Ta'Sar Academy's hidden bookcase room holds its stash.

Installing follows the MM9 rules: build into a scratch folder, check that the scene differs from the installed one
by `spawns` alone, install into `assets_dev` and the map's review root (`isleofashes_blv_root` for the regions).

### 5.3 Checks

- `treasure.png` and the report per map, reviewed before installing; the user reviews the pilot maps'.
- A headless scenario per pilot map: enter, count the floor items materialised against the markers, check each is
  on a floor (z against the floor below) and reachable.
- An engine screenshot tour of a few stashes per pilot map: the 3D ground items in place and readable.
- The balance report (`mm9_balance_report.py`) gains the markers' items per act against MM7's stages.

### 5.4 Rollout

1. The data module and the converter step, then the pilot: Ta'Sar Academy and Yanmir's Fort (played this session,
   good docs), then the user's review of `treasure.png`, the tour and a playthrough.
2. The remaining act 2 dungeons; then acts 1, 3 and 4.
3. The regions last: they need the near-box restriction, town radii and `avoid_near` lists (their docs are thin:
   check each `treasure.png` by eye).
