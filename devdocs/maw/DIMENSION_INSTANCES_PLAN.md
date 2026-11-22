# Dimension maps as rifts (map instances)

Status: built on 2026-11-17 for single-player play (steps 1 to 3 below). The server groundwork of step 4 waits for a
multiplayer decision. It is ours, not MAW's: MAW overwrites the real map with the run. DEVIATIONS 197 and 198.

## What the user asked for

- A dimension map opens an **instance** of its map. The real map is not changed in any way; the dimension lies beside
  it.
- The party can leave the instance and come back.
- **Lloyd's Beacon is disabled** inside an instance.
- The party holds a **quest item**, the Dimensional Portal: inspecting it shows what the open dimension is, using it
  takes the party to the instance's start point.
- **One instance at a time.**

The decisions that followed (the user, 2026-11-17):

| Question | Decision |
|---|---|
| A quest map lost before use | It cannot be lost: while the quest runs, a dimension map is neither dropped nor sold. No second map is handed out, so there is nothing to cheese |
| The dungeon's own door | Leaving leads back to where the party entered the rift from. Travel between outdoor maps and from the rift's dungeon into another dungeon is closed |
| Quest chests and event items in a rift | Kept as they are (a chest may hold a key the dungeon needs) |
| A cleared rift | Stays open through the portal until the next map is used |
| Nightmare's revival on leaving | Rifts are exempt |
| Giving a rift up | While the Dimensional Maps quest runs, only its giver closes an unfinished rift (the 80 % repeat). Once the quest is done, using the next map gives the open rift up |

## How it works

### The engine: a second state of the same map file

A map's saved state is found by a key (`GameSession::mapStateKey`). The session carries an **instance id** beside the
current map's file name (`GameSession::mapInstanceId`, empty on the map itself); an instance's state lies under
`<map key>#<instance id>` in the same two state tables. Nothing else about a map is doubled: its file, events,
geometry and layout identity are the map's.

| Where | What |
|---|---|
| `EventRuntimeState::PendingMapMove::instanceId` | set: the move names its instance (a travel item). Unset, an ordinary move: it stays in the instance for the instance's own map, and from inside an instance the rules say where any other leads |
| `GameApplication::processPendingMapMove` | asks `MonsterRules::mapInstanceExit` (stay, leave to the named map, redirect, refuse with a status line), switches the instance with the map, and drops the states of instances the rules ended (`GameSession::discardEndedMapInstances`, `MonsterRules::liveMapInstances`) |
| `findSavedOutdoorWorldState`, `findSavedIndoorSceneState` (`GameApplication.cpp`) | the current map's state is its instance's when the party is in one; an instance never refills by time |
| `GameApplication::loadCurrentSessionMap` | a map file already loaded is loaded anew when the rules would set it up another way (`MonsterRules::mapAssetVariant`: the map itself against its rift, whose monster families differ) |
| Defeat, a debug map jump, a scenario's `load_map` | lead to the map itself, out of any instance |
| `GameSaveData::mapInstanceId` | saved (version 195) |
| `GameSession::discardMapState` | in an instance, resets the instance's state only (a rebuilt map resets the rift like any state) |

Standard games and worlds without MAW never set an instance id; every lookup then takes the path it took before.

### MAW: the rift

`MawGameState::dimensionRuns` holds the one open rift by its map's file name (`MawRules::rift`); the instance id is
`MawRiftInstanceId`. `MawRules::dimensionRun(file)` answers only while the party is in the rift on that map, so every
rule that asks it (families, affixes, density, level, the HUD's run tab) holds in the rift and never on the map itself.

- **The map's records are the map's:** `completedMaps`, `clearedSinceRefill`, `mapVisits`, `mapsDropped`, the reset
  count and offer, the bounty gate, the Progress tab's row. The rift keeps its own on its run: `completed`, `slain` and
  `counted` as the party last left it, `mapsDropped`. Used barrels stay shared with the map (or every rift on a map
  with barrels would be a free stat raise), and quest state is global, so the map's events re-arm in a rift as they did
  in a run.
- **Opening** (`MawItemRules::useTravelItem`): the map item creates the rift, remembers where the party stood, gives
  the Dimensional Portal (item 1071, one, never dropped or sold) and moves the party to the rift's start. A cleared
  rift gives way; an unfinished one is given up once the quest is done and refuses the new map while the quest runs.
- **The portal:** outside, into the rift, remembering where from; inside, back to that place. Its popup reads the
  rift: map level, "Slain N of M" or "Cleared", the affixes in force.
- **Ways out** (`MawMonsterRules::mapInstanceExit`): the portal; Town Portal, where it says; a dungeon's way outdoors,
  which leads back to where the party entered from. Closed: a way into another dungeon, a map's edge
  (`mapTravelRefusal` in `OutdoorSceneRuntime`), stables, ships and coaches (`HouseInteraction`). A teleporter inside
  the rift's own map stays in the rift.
- **Lloyd's Beacon** is refused in a rift (`lloydsBeaconRefusal`, `PartySpellSystem.cpp`); a beacon set on the map
  itself leads to the map itself.
- **Clearing** (`MawExperienceRules::rewardMapProgress`): at the clear, as before: it counts for the quest and, once
  the quest is done, gives the next map. A rift never pays its map's first completion reward or marks the map
  completed (before, a quest map rolled onto a never-completed dungeon did both).
- **The quest's repeat** (DEVIATIONS 197) closes the rift: the party must have left it, and no refill of the map is
  involved any more. A rift never entered closes for the asking.
- **Crafting** is on the map item, before it is used (it lies in the Crafting pouch, where the Workbench lists it); an
  open rift is not changed by anything.
- **The autosave** of a map's use holds the map unused (the user, 2026-11-17). Using a travel item is two steps:
  `ItemRules::planTravelItem` queues the move and changes nothing, the item staying in hand; `useTravelItem` opens the
  rift and spends the map as the party sets off, after the autosave of the map being left
  (`PendingMapMove::travelItem`, `GameplayItemService::useTravelItemForMove`: from the player's hand or the bag it
  went back to). At first the map was spent
  at once and that autosave held it gone with the rift never entered.
- **Leaving** records the rift's progress on its run; Nightmare's revival does not touch a rift.

### Saves made before (version 194 and older)

A run lay in its map's own state and several could be open. On load (`GameSession::migrateDimensionRunsToInstances`,
`MawGameState::keepOneRift`): one run is kept (the one the party stands in, else an unfinished one), its map's state
becomes the rift's, its map's records of it go onto the run, and the party gets the portal. The map itself starts from
its own beginning. The other runs' maps are marked to refill as themselves. Such a rift does not know where the party
entered from: its dungeon door leads where it says, and the portal says it does not know the way back.

## Checks

- `tests/MawDimensionMapTests.cpp`: the rift beside its map and its ways out; a bound map and portal; the repeat, the
  portal in and out, one rift at a time; `keepOneRift`. `tests/RulesetTests.cpp`: the save round trip.
- `tests/scenarios/rulesets/maw_dimension_rift.yml`: a rift opened inside its own dungeon; the dungeon as it was left;
  a teleporter that stays inside; the Exit Door back to where the map was used; a save in the rift; the portal in and
  out; the cleared rift kept. `maw_dimension_map_repeat.yml` and `mm9/maw_hag_repeats_dimension_map.yml`: the repeat.
  `maw_dimension_maps.yml`: the quest and the drops, unchanged.

Not checked in a running game window: the portal's popup, the status lines of a refused way out, Lloyd's Beacon's
refusal.

## Known rough edges

- A dungeon's exit dialog still names the place its door leads to on the map itself, though in a rift it leads back
  to where the party entered from.
- A map's edge in an outdoor rift offers nothing and says nothing.
- The rift keeps the map file's name everywhere (HUD, journal, autosave names).
- The Progress tab's row of the rift's map shows the rift's level while the party stands in the rift
  (`MawRules::mapLevelSummary` asks `dimensionRun`).

## For a hosted server (not decided)

There is no multiplayer code (OY-287 is the request). On 2026-11-19 the user chose the shape: one solo run character
per player on a host's world, the host's game as the server; see the
[co-op design](../plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md), which proposes one open rift per world and how
`MawGameState` splits between the world and the characters. A dedicated server is a later step there. What was said
before that (Discord, relayed by the user 2026-11-17):

- One character per player, parties formed among players; in effect solo play together, without a solo run's free
  scrolls and alchemy. Sharing skills and auras inside a party would be welcome.
- A lobby to prepare characters before a new world, and joining a running world with a character from the
  Adventurer's Inn or a new one near the players' level.
- Open: Town Portal and Lloyd's Beacon for a group (a doorway that stays for a while, or an invitation each member may
  decline); time, which travel and training skip (let it run and skip nothing, or rest by vote); a dedicated server
  rather than two clients hosting each other. MAW's own online mode shows what must be shared: monster deaths and
  ownership, short-lived projectiles, per-monster stacks, and buffs that must not follow a player across maps.

What the rift design leaves ready for it, and what it still assumes:

- Ready: a map state is addressed by (map, instance id), never by the file name alone, so a server can give each
  party's rift its own id beside a shared map.
- Still single-player: one rift in `MawGameState`, the constant instance id, `MawRules::currentMap()` (33 uses) and
  the session's one current map; a rift's rolls keyed by the map name and a per-session refill seed
  (`MawMonsterRules::m_refillSeeds`) instead of a seed the rift owns; the portal as an inventory item rather than a
  view of server state.

## Steps

1. Done. Instance id through the session, map moves and saves.
2. Done. The rift replaces the runs; portal item; old saves migrate.
3. Done. Rules of the rift: ways out, Lloyd's Beacon, one at a time, the cleared rift kept, the repeat.
4. Open, with multiplayer: a seed per rift, the map context instead of `currentMap()`, rifts per party.
