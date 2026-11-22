# Xeen table contributions: what the loader reads

Owner: A1. For A2 (the generator `tools/xeen/build_world.py`), A3 and A4 (their modules). Written 2026-11-20 with the
engine change W1 (merge point 1). This file says which tables the Xeen world can add rows to, the file each one is
read from, its key column and the id range the key must lie in. The other columns are the engine table's: copy them
from the file named in the "Columns as" column of the table below, in the same order.

## How a contribution is read

- **One file per table** under `assets_dev/worlds/xeen/data_tables/`, listed in `world.yml` `tableContributions`
  (A1 adds the entries; block below). A listed file that is missing stops the game for every world (the Xeen folder is
  mounted in every development run), so the entry is added only once the generator writes the file. Write every file
  of the block, header-only where there are no rows yet, then tell A1 (through O) which ones exist.
- **Format:** tab-separated, UTF-8, LF line ends. Keep the engine table's header rows: a row whose key cell is not a
  number (or, for the map-keyed tables, not a `.odm`/`.blv` name) is skipped.
- **Text with line breaks, tabs or a leading quote:** one cell in double quotes, inner quotes doubled
  (`"He said ""Go."" and left."`). No continuation rows.
- **Keys:** a row's key must lie in the Xeen range of its id domain (`world.yml` `idRanges`) and must be new: a key that
  the engine table or another world already has stops the game with the colliding id in the log
  (`Failed to compose <table>: row id ... collides with package ...`).
- **Map-keyed tables** (`outdoor_travels`, `map_navigation`, `house_exits`): the key is a map file name, which must
  have a `map_stats` row in the Xeen `maps` range (9101–9199). Compared without case.
- **When it applies:** the rows are added whatever world the game was started in (as MM9's are), so a Xeen house,
  NPC or qbit is known to an MM7 game too; that is what keeps ids out of each other's way.
- **map_stats `world_id` (column 34):** filled with `xeen` where the row leaves it empty. Leave it empty.

## The tables

| Table (`tableContributions` `table`) | File | Columns as | Key column | idDomain (Xeen range) |
| --- | --- | --- | --- | --- |
| `house_data` | `house_data.txt` | `engine/data_tables/house_data.txt` | 0 `#` house id | `houses` (4001–4999) |
| `house_animations` | `house_animations.txt` | `engine/data_tables/house_animations.txt` | 0 house id | `houses` |
| `house_movies` | `house_movies.txt` | `engine/data_tables/house_movies.txt` | 0 animation id | `houses` |
| `house_exits` | `house_exits.txt` | rows 4+ of `engine/data_tables/house_exits.txt` | 0 map file | `maps` (9101–9199) |
| `npc` | `npc.txt` | `engine/data_tables/npc.txt` | 0 NPC id | `npcs` (4001–5999) |
| `npc_greet` | `npc_greet.txt` | `engine/data_tables/npc_greet.txt` | 0 greeting id | `npcs` |
| `npc_topic` | `npc_topic.txt` | `engine/data_tables/npc_topic.txt` | 0 topic id | `npc_topics` (40000–49999) |
| `npc_topic_text` | `npc_topic_text.txt` | `engine/data_tables/npc_topic_text.txt` | 0 text id | `npc_topics` |
| `npc_news` | `npc_news.txt` | `engine/data_tables/npc_news.txt` | 0 news id | `npc_topics` |
| `teacher_topics` | `teacher_topics.txt` | `engine/data_tables/teacher_topics.txt` | 0 topic id | `npc_topics` |
| `roster` | `roster.txt` | `engine/data_tables/roster.txt` | 0 roster id | `roster` (requested: 401–499) |
| `quests` | `english/quests.txt` | `engine/data_tables/english/quests.txt` | 0 qbit | `qbits` (110000–119999) |
| `autonote` | `english/autonote.txt` | `engine/data_tables/english/autonote.txt` | 0 note bit | `autonotes` (4001–4999) |
| `awards` | `english/awards.txt` | `engine/data_tables/english/awards.txt` | 0 award bit | `awards` (401–499) |
| `award_texts` (mode `override`) | `english/award_texts.txt` | `engine/data_tables/english/awards.txt` (`A Bit`, `Awards`, `Sort` optional, `Notes`) | 0 award bit of the engine table | none: each row rewords an engine award row (it must exist) while the party is in the world; another world, or a switch away, shows the engine's text (merge point 18; XD-20's arena awards 46–49, D-39) |
| `map_stats` | `map_stats.txt` | `engine/data_tables/map_stats.txt` | 0 map id | `maps` (9101–9199) |
| `bolster_maps` | `bolster_maps.txt` | `engine/data_tables/bolster_maps.txt` | 0 map id | `maps` |
| `bolster_monsters` | `bolster_monsters.txt` | `engine/data_tables/bolster_monsters.txt` | 0 monster id | `monsters` (merge point 17: NoArena and the MMerge monster types, D-39) |
| `place_mon` | `english/place_mon.txt` | `engine/data_tables/english/place_mon.txt` (`#`, `Name`) | 0 name id | `placed_monster_names` (requested: 401–499; an indoor placed monster's `name:` takes the row of that name) |
| `trans` | `english/trans.txt` | `engine/data_tables/english/trans.txt` (`2D#`, `Transition Description`, `Note`) | 0 transition id | `transitions` (requested 5001–5999, merge point 40; D-90: the line the entrance window shows in place of "Do you wish to enter X?" when a move's `screen: {text: <id>}` names the row; localized by `tools/l10n.py`) |
| `outdoor_travels` | `outdoor_travels.txt` | `engine/data_tables/outdoor_travels.txt` | 0 key map file | `maps` |
| `map_navigation` | `map_navigation.txt` | `engine/data_tables/map_navigation.txt` | 0 map file | `maps` |
| `transport_index` | `transport_index.txt` | `engine/data_tables/transport_index.txt` | 0 house id | `houses` |
| `transport_locations` | `transport_locations.txt` | `engine/data_tables/transport_locations.txt` | 0 route id | `transport` (401–499) |
| `continent_settings` | `continent_settings.txt` | `engine/data_tables/continent_settings.txt` | 0 continent id | `continents` (requested: 6) |
| `town_portal_switch` | `town_portal_switch.txt` | `engine/data_tables/town_portal_switch.txt` | whole groups | `continents` (6–7) |
| `new_game_continents` | `new_game_continents.yml` | `new_game_continents` of `engine/data_tables/character_selection.yml` | `id` | `continents` |
| `dimension_doors` | `dimension_doors.yml` | `engine/data_tables/dimension_doors.yml` | door `key` and `place` | `continents` (not checked) |
| `trainer_places` | `trainer_places.txt` | `engine/data_tables/trainer_places.txt` | 0 house id | `houses` |
| `complex_item_pictures` | `complex_item_pictures.txt` | `engine/data_tables/complex_item_pictures.txt` | 1 item id | `items` |
| `edge_spans` | `edge_spans.yml` | below (merge point 9) | `map` and `edge` | `maps` (the world's own maps) |

**Town Portal groups** (merge point 2): a group is its `@` row and the destination rows under it. The `@` row is
`@ <group name> <topic id> <label> <continent id>`: the label is the page's button (English), the continent the page
belongs to (Cloudside 6, Darkside 7); the party's map's continent (`bolster_maps` column 2) picks the home page. A
group name must be new. The engine groups now carry the same two columns. The Town Portal screen shows as many
continent buttons as `ui/gameplay/town_portal.yml` has `TownPortalContinentButtonN` elements (six since 2026-11-20,
the fifth and sixth for Cloudside and Darkside). A page's picture is the icon named after its group (`TPCloudside`:
`icons_x2/tpcloudside.png`); a destination's lit town is its `IconName` row (`tpvertigo`). A page whose towns are
all missing (no map installed) gets no button unless it is the party's home page.

**New-game continents** (merge point 2; cards merge point 3): a YAML file with a `new_game_continents:` list in the
engine table's shape (`id`, `key`, `name`, `available_class_ids`, `available_race_ids`, `portrait_exceptions`); id in
`continents` and key new. An entry with a `card:` block gets a card on the new-game screen; without one it gets none.
The screen places the cards from one template (`ContinentSelectionCard*` in `ui/gameplay/continent_selection.yml`),
left to right by `order`, shrinking them alike when five or more do not fit:

```yaml
  card:
    order: 1                     # first (the user, 2026-11-21): Xeen 1, Enroth 2, Antagarich 3, Jadame 4, Chedian 5
    title: Xeen (alpha)          # the card's name (English; translated where shown)
    short_title: Xeen            # optional: the name everywhere but the card (default: the title)
    subtitle: Might and Magic IV and V
    caption: Begin in Vertigo
    picture: worlds/xeen/ui/hud_x2/menus/omenu_continent_xeen.png   # a package path, as here
```

The card can be chosen when `continent_settings` has the continent's row with its start map (death map 1) and that map
is installed. The card itself shows `title`; everything else names the continent by `short_title` (the title when it is
not given; merge point 46, the user, 2026-11-22: "Xeen (alpha)" on the card): the journal's Quests, Notes, Trainers
and Arcomage tabs, the Ledger of Teachers ("ask for it in any tavern on Xeen"), MAW's trainer hints and the party
creation's portrait filter, which names a world after the card whose start map is in it. A tab shows the quests and
notes whose `Owner` equals it, so `short_title` must be the Owner of the world's `quests`/`autonote` rows (a runtime
test fails when a tab has no owner or an owner no tab). Save and load summaries name the continent by its `name`.

**Dimension Door** (merge point 3): `engine/data_tables/dimension_doors.yml` (its header says the format): one door per
continent, left to right, each with its landings (the first whose QBit the party has, the last without one), and one
screen per door count (a backdrop and, per place, the lit door's rect and its hover column). A world adds its door
(`doors:` with a new `key` and `place`, `pictures` by door count) and, while the engine has none, the screen for the
new count (`screens:`), through the `dimension_doors` entry. Since merge point 45 (the user, 2026-11-22: "the same
order as in the new game screen") `place` is the door's rank left to right, its continent's new-game `card.order`
(engine Enroth 2, Antagarich 3, Jadame 4, Chedian 5; Xeen 1), not a slot: the doors, sorted by `place`, take the
screen's places in that order, and the screen is the one with the fewest places that has one for every door. So Xeen's
door is the leftmost of the five-door screen (a backdrop `tpglobal5` and the five lit doors, A4's art), and without
Xeen the four-door screen shows Enroth, Antagarich, Jadame, Chedian. A unit test checks each engine door's `place`
against its card's order; a new world gives its door its card's order (unique among the mounted worlds).
An entry with an engine door's key and only `pictures` gives that door its lit picture on the world's new screen
(merge point 4). Every picture and backdrop is a package path (`worlds/xeen/ui/...`, as the new-game card's): an
unqualified `ui/...` is looked up only in the active world and the engine, so an MM7 game would draw the screen blank
(merge point 5). Xeen's file, `data_tables/dimension_doors.yml` (A2's generator writes it; A1 then lists it in
world.yml), with A4's art and rects (`level_generation/ui/xeen_dimension_door_20261120/README.md`). Since merge point 38
(the user, 2026-11-21, "globes + labels") a place may have `label` (the rect the door's name is printed in at all
times, under its portal), but since merge point 45 no screen has one (the user removed the names, U-8; the hovered
door's name stays on the status line), and the lit pictures are the continents' card globes inside the portals, written by
`tools/ui/dimension_door_globes.py` from the backdrop and each door key's `card.picture`; a new door's lit picture is
made by that tool too (its continent needs a card; rerun it whenever the order or a screen changes, since each
picture is a crop of the backdrop at the door's place):

```yaml
screens:
  - backdrop: worlds/xeen/ui/gameplay/dimensional_travel/tpglobal5
    places:
      - {picture: [17, 100, 107, 136], hover: [0, 0, 128, 480]}
      - {picture: [146, 99, 107, 136], hover: [128, 0, 128, 480]}
      - {picture: [266, 99, 107, 136], hover: [256, 0, 128, 480]}
      - {picture: [386, 99, 107, 136], hover: [384, 0, 128, 480]}
      - {picture: [516, 99, 107, 136], hover: [512, 0, 128, 480]}
doors:
  - key: xeen
    label: Xeen
    place: 1                   # Xeen's new-game card order: the leftmost door (the engine's are 2-5)
    pictures: {5: worlds/xeen/ui/gameplay/dimensional_travel/tpxeen5}
    landings:
      - {map: xeen_x1.odm}     # Vertigo, at the map's start (A5 may give `at` and `direction`)
  - {key: enroth, pictures: {5: worlds/xeen/ui/gameplay/dimensional_travel/tpenroth5}}
  - {key: antagarich, pictures: {5: worlds/xeen/ui/gameplay/dimensional_travel/tpantagarich5}}
  - {key: jadame, pictures: {5: worlds/xeen/ui/gameplay/dimensional_travel/tpjadame5}}
  - {key: chedian, pictures: {5: worlds/xeen/ui/gameplay/dimensional_travel/tpchedian5}}
```

**Edge spans** (merge point 9, decision D-11.6): one map edge that leads to more than one map. A2's generator writes
`data_tables/edge_spans.yml` from `source/maps.yml`:

```yaml
edge_spans:
  - {map: xeen_x4.odm, edge: south, from: -32768, to: 0, to_map: xeen_x3.odm, side: up, days: 5,
     at: [-7168, 22016, 1120], facing: 1536}
  - {map: xeen_x4.odm, edge: south, from: 0, to: 32768, to_map: xeen_x2.odm, side: up, days: 5}
```

`from`/`to` are game units along the edge (x for north and south, y for east and west); the party meets the span with
`from <= x < to`. `side` (up, down, left, right as in `outdoor_travels`) is the arrival start point when there is no
`at`; `at` [x, y, z] and `facing` (2048 a turn) the arrival otherwise. `days` as the travel rows. Where no span covers
the point, the edge's own `outdoor_travels` (or `map_navigation`) way applies, so an edge needs no travel row when its
spans cover it (X3's north). Refused (the game stops with the reason): a map of another world, overlapping spans on
one edge, an unknown `to_map`, `from >= to`, neither `at` nor a `side`. The game: `MapStatsEntry::edgeSpans`,
`edgeTransitionAt` (game/tables/MapStats.h); the travel dialogue's source id is edge + 4 × (span + 1). Scenario
`tests/scenarios/xeen/edge_spans.yml`. In a project, an edge neighbour's `span: [from, to]` says the same for the
studio (no travel row is written for it).

**Route names** (merge point 23, A4): `transport_locations.txt` takes an optional 16th column "Name" after QBit
(column 15, 0-based): the place a route's button and travel line name ("1 day to {Name} for 250 gold"); empty, the
destination map's map_stats name, as before. The engine's file has the header only; `tools/l10n.py` extracts the
column. Two routes into one map (D4's Isle of Lost Souls and Lakeside) need it.

**NPC titles** (merge point 9, decision D-21): `npc.txt` takes an optional 18th column "Title" after Notes (column 17,
0-based). A talk with a titled NPC reads "{name}, {title}" (the house screen's `tr()` key); an empty title keeps
"{name} the {profession}" or the name. The engine's npc.txt has the header only; `tools/l10n.py` extracts the column.
A 44-character "Medin, Ferryman and Fisherman of Lake Darzog" wraps to three lines under the portrait and clears the
topics (`output/xeen_a1/d21_title_capture.png`).

**Sky** (merge point 2): `worlds/xeen/rendering/sky/sky.yml`, in the engine sky file's schema with `version: 1` and only
`aliases`, `presets`, `themes` and `maps`, is added to the engine library whenever the world is mounted; every name
must be new (presets may inherit the engine's). No `tableContributions` entry: the file's presence is enough.

**Common scripts** (merge point 2): a map's world's own `events/common/` scripts run before its map script:
`world_common.lua`, `common.lua`, `<world>_common.lua`, then every other `<world>_*.lua` by name (`xeen_quests.lua`).
Another world's files are never included.

The tables that already took world rows before W1 (items, monsters, sounds, decorations, vendors, service venues,
trainer places and the rest) keep the shapes their files already have; MM9's `world.yml` shows each entry.

### The columns that link tables

| Table | Column | Refers to |
| --- | --- | --- |
| `house_data` | 3 `Map` | `map_stats` id of the map the house stands on |
| `house_data` | 4 `Picture` | `house_movies` animation id (an engine one unless Xeen adds its own) |
| `house_data` | 8 `Picture` (proprietor) | NPC portrait number |
| `house_animations` | 1 animation id; 3 `NPC List` | animation id as above; the residents, NPC ids separated by commas |
| `house_animations` | 4 `Video Name` | the video stem; empty takes the animation id's `house_movies` row |
| `npc` | 6 `2D Location` | `house_data` id of the NPC's house (0 on the street) |
| `npc` | 8 `Greet` | `npc_greet` id (use the NPC's own id) |
| `npc` | 10–15 `Event A`–`F` | `npc_topic` ids (40000–49999, or a teacher topic id) |
| `npc_topic` | 4 `Text #` | `npc_topic_text` id (its leading number is read) |
| `teacher_topics` | 4 `TextId` | `npc_topic_text` id |
| `transport_index` | 1–3 | `transport_locations` ids; `-1` for none |
| `bolster_maps` | 2 `Continent` | `continent_settings` id (Xeen: 6, once the range is declared) |

## The `world.yml` block

A1 adds these entries as the files appear (an entry whose file is missing stops the game):

```yaml
tableContributions:
  - {table: house_data, idDomain: houses, mode: append, path: data_tables/house_data.txt}
  - {table: house_animations, idDomain: houses, mode: append, path: data_tables/house_animations.txt}
  - {table: house_movies, idDomain: houses, mode: append, path: data_tables/house_movies.txt}
  - {table: house_exits, idDomain: maps, mode: append, path: data_tables/house_exits.txt}
  - {table: npc, idDomain: npcs, mode: append, path: data_tables/npc.txt}
  - {table: npc_greet, idDomain: npcs, mode: append, path: data_tables/npc_greet.txt}
  - {table: npc_topic, idDomain: npc_topics, mode: append, path: data_tables/npc_topic.txt}
  - {table: npc_topic_text, idDomain: npc_topics, mode: append, path: data_tables/npc_topic_text.txt}
  - {table: npc_news, idDomain: npc_topics, mode: append, path: data_tables/npc_news.txt}
  - {table: teacher_topics, idDomain: npc_topics, mode: append, path: data_tables/teacher_topics.txt}
  - {table: roster, idDomain: roster, mode: append, path: data_tables/roster.txt}
  - {table: quests, idDomain: qbits, mode: append, path: data_tables/english/quests.txt}
  - {table: autonote, idDomain: autonotes, mode: append, path: data_tables/english/autonote.txt}
  - {table: awards, idDomain: awards, mode: append, path: data_tables/english/awards.txt}
  - {table: award_texts, idDomain: awards, mode: override, path: data_tables/english/award_texts.txt}
  - {table: map_stats, idDomain: maps, mode: append, path: data_tables/map_stats.txt}
  - {table: bolster_maps, idDomain: maps, mode: append, path: data_tables/bolster_maps.txt}
  - {table: outdoor_travels, idDomain: maps, mode: append, path: data_tables/outdoor_travels.txt}
  - {table: map_navigation, idDomain: maps, mode: append, path: data_tables/map_navigation.txt}
  - {table: transport_index, idDomain: houses, mode: append, path: data_tables/transport_index.txt}
  - {table: transport_locations, idDomain: transport, mode: append, path: data_tables/transport_locations.txt}
  - {table: continent_settings, idDomain: continents, mode: append, path: data_tables/continent_settings.txt}
```

## Limits worth knowing

- **Roster join topics:** an NPC's "Join" topic is MM8's numbering (a topic id tied to a roster id), which covers only
  the engine roster. Xeen roster rows join through the Adventurer's Inn; a recruitable NPC in Xeen needs A1 first.
- **Quest notes:** the quest log reads `quests` rows; MM9 still uses its older `english/quests_overlay.txt`, which
  Xeen should not copy.
- **No overrides:** a world adds rows; it cannot change an engine row. A change to an MM6–MM8 house or NPC is not a
  Xeen change.
