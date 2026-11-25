# Xeen town files

Owner: lane A4. One file per surface map or town BLV in `assets_dev/worlds/xeen/source/towns/<key>.yml` (`x1.yml`,
`x2.yml`, …), plus the world's teacher plan `teachers_plan.yml`. `tools/xeen/gen_towns.py` turns them into table rows;
`tools/xeen/towns.py` checks them. Topic texts are not here: A3 writes them in `source/npcs/<key>.yml`, keyed by the NPC
ids of these files.

## 1. What a town file holds

```yaml
key: X1                      # the map's key in source/maps.yml (its map_id goes into house_data's Map column)
stem: xeen_x1.odm
town: Vertigo
face: cloudside
blocks: {houses: [4001, 4050], npcs: [4001, 4100]}   # this map's id blocks (section 2); a full block takes more ids
                             # from the rest block as a second range: houses: [[4451, 4500], [4901, 4901]]
arrivals:                    # where coaches, boats, mirrors and Town Portal set the party down on this map
  vertigo_stables: {at: [768, 9400, 640], direction: 512}   # world units; direction 0 E, 512 N, 1024 W, 1536 S
  # optional `place: "the Isle of Lost Souls"`: the travel line's destination instead of the map's name (a route
  # within one map); written to transport_locations' trailing Name column once the engine header has one (A1)
houses:
  - id: 4001                 # Xeen house id, inside the block
    door: building:weapon_shop   # the map project's building id (`#n` = its index, outdoor maps only: an indoor
                                 # door is named by its own id, towns.py refuses `#` in a .blv file, D-50); what the
                                 # map lane binds
    also_doors: [thing:nystor_ship]   # optional: further doors that enter the same house (Nystor's dock and ship)
    was: 9                   # the MM7 row the built map opened before (optional; prices and video are copied from it)
    kind: weapon_shop        # section 3
    name: Norman's Ironworks
    town: Castle Burlock     # optional: the town the house belongs to when a file holds several (default: the file's)
    owner: 4001              # the proprietor: name, title and portrait on the house screen (an NPC of any file; one
                             # who is a resident elsewhere keeps that house: Lucio owns the jetties, lives in Olympus)
    residents: [4030]        # further NPCs in the house (1 usually, 2-3 where the story has them)
    hours: [6, 18]           # optional; the kind's default otherwise (equal = always open; 5-2 wraps midnight)
    price: 1.5               # optional; house_data Val (shops: price factor, tavern: room and food, temple: healing)
    shop: {quality: 1, kinds: [sword, bow, axe, any]}   # shops: stock quality and, optionally, the first item kinds
    guild: {spells: 4}       # guilds: the highest spell sold in each of the guild's schools
    training: {cap: 10, price: 10}   # training halls: the level cap and Val (price = level x Val x class tier)
    routes:                  # stables and boats
      - {id: 401, to: rivercity_stables, days: [mon, wed, fri], travel_days: 2, qbit: 0}
      - {id: 404, to: burlock_stables, days: [tue, sat], travel_days: 4, after: X4 built}   # not written yet
      - {id: 426, to: olympus_dock, days: [wed, sat], travel_days: 1, qbit: m30.done}   # qbit: a number or A3's name
                             # a route waits by itself while its landing's file is planned; `after:` holds it for
                             # anything else. A stable or boat with `opens:`, or whose every route waits, has no
                             # row yet (towns.py lists the second as a wait: Kramer's caravans before D3)
    mirror: {face: cloudside, town: Vertigo, arrival: vertigo_square, qbit: 119001}      # kind mirror only
                             # the mirror's map is its arrival's (a castle's mirror may stand in its BLV's file)
    alternate_of: 4009       # a second row for the same door (a renamed house after a quest); the door picks by qbit
    after: m2.done           # with alternate_of: the qbit after which the door enters this row (below)
    opens: m3.done           # the door enters the house only once this qbit is set; closed_text before
    open_before: true        # a cursed town's house that is open before the town's quest by design (WORLD_DESIGN
                             # 5.1: the edge services, the joke house, the ferry; D-73 4c): towns.py lists it no more
    hook: m3.dwarf_shop      # A3's quest hook the house answers
    enter_sound: xeen_fortune    # optional: a sound name of the world's audio/sounds.txt (lane AU) played on entering
                             # (house_animations' Enter Sound column; the fortune tellers' reading). The engine does
                             # not read that column yet (A1)
    new_door: "..."          # the map lane must make this door enter the house (today a message or an event)
npcs:
  - id: 4001
    name: Norman
    title: Blacksmith        # D-21: a capitalised noun phrase naming a person, no leading "The" (Fisherman, Faery
                             # King, Plague Cultist); none where the name carries one (a rank or form of address
                             # first, Princess Roxanne, Brother Cael; or a word of the title in the name, Miller Dunn).
                             # npc.txt's Title column (the talk reads "{name}, {title}") and house_data's Title
    sex: male                # male or female; required on every house owner: the house greets in a stock MM6-MM8
                             # voice of that sex, silent where the kind has none (D-165; gen_towns VOICES)
    profession: Smith        # a name from engine npc_professions.txt: the person's role; the npc row carries it only
    hireling: false          # with `hireling: true` (else the engine offers Join and titles the talk "<name> the
                             # <profession>"); named people are no hirelings, the talk's title is the name
    teaches: [{skill: Sword, mastery: expert}]   # mastery teacher offers: expert, master, grandmaster; an offer may
                             # say `opens: <qbit>` (shown only once the qbit is set: Gem's and Errol's Grandmaster
                             # at Kalindra's stage 4); A3's gen_quests hides it through gen_towns.teacher_gates()
    engine_topics: [704]     # optional: engine service topics the engine's code answers, in free topic slots after A3's
                             # (704 Arena: the arena's tier choice and reward, the XD-20 Arena Master; gen_towns
                             # ENGINE_TOPICS lists the allowed ids)
    greet: ["first meeting", "later meetings"]   # npc_greet; one or two short lines
    greet_after:             # optional: greetings that replace `greet` once a qbit is set (the impostor Roland's
                             # become the real one's at m35.done): an id of the NPC's block that is no NPC id, written
                             # as its own npc_greet row; A3's quest step that sets the qbit calls
                             # evt.SetNPCGreeting(npc, id) (towns.py waits until xeen_quests.lua does;
                             # gen_towns.greeting_gates() lists them)
      - {id: 4406, after: m35.done, greet: ["first meeting after", "later meetings after"]}
    house: none              # only for NPCs placed outdoors or moved in later by A3; `place:` says where
    actors:                  # optional: further placements a map lane makes of this NPC (data for that lane; the
                             # generator ignores it): map, at, shown (qbit), peaceful, click (the event's contract)
      - {map: DD-14, at: "the landing, beside his griffin", shown: m25.done, click: "AskQuestion ...; Yes: hook, move"}
    source: "xeen/aaze0028:1"    # the original line quoted, when one is
```

An NPC's house is the house that names it as owner or resident; one NPC lives in at most one house.

A file marked `planned: true` belongs to a map that is not built yet. Its NPC ids and house ids are fixed (A3 writes
the topics, the map lane draws the doors), its arrivals are named with `at: null`, and its door ids are proposals the
map lane may rename. The generator writes the NPC rows only; the houses, arrivals, routes and mirrors come into the
tables when the map is built (`planned` removed, arrival coordinates filled in). The checks treat its houses and
teachers like any other file's; only the door check waits for the map's sketch.

**A door that picks its house by quest bit.** Qbits are named as A3 names them (`<quest>.<qbit>`, e.g. `m2.done`);
the map's door event asks A3's `Xeen.isSet(name)` (`events/common/xeen_common.lua`). `hook:` names A3's quest hook the
house answers.

- A house renamed after a quest is a second row on the same door: `alternate_of: 4009`, `after: m2.done`. The door:
  `if Xeen.isSet("m2.done") then evt.EnterHouse(4010) else evt.EnterHouse(4009) end`.
- A house that opens after a quest: `opens: m3.done` and `closed_text`. The door:
  `if Xeen.isSet("m3.done") then evt.EnterHouse(4851) else evt.SimpleMessage(closed_text) end`.
- A cursed town's closed house (`opens:`) shows `closed_text` until its town's quest; a mirror with `opens:` is
  dark until then: `data_tables/mirrors.yml` carries the mirror's `opens` and `closed_text` for A3's mirror helper.
  Every house of a cursed town without `opens:` is open from day one; towns.py prints it as a wait unless it has
  `open_before: true` (open by design).
- A person who moves in or out after a quest (Tam home, Joe gone) is A3's: `evt.MoveNPC` in the quest's step; the
  town file lists where the NPC lives at the start (`house: none` for nowhere yet).

## 2. Ids

| Domain | Range | Rule |
| --- | --- | --- |
| Houses | 4001-4999 | 50 per map block |
| NPCs | 4001-5999 | 100 per map block; an NPC's greeting id is its NPC id; a later greeting (`greet_after`) takes a free id of the block (4406 Roland's) |
| NPC portraits | 14001-15999 | `npc<10000 + NPC id>.png` in `worlds/xeen/icons_x2/` (engine portraits end at 9124) |
| Transport locations | 401-499 | explicit per route (`routes[].id`), never reused |
| Roster | 401-499 | `roster.yml` ids |
| Qbits for travel | 119000-119099 (requested) | mirror touched = that town's Town Portal unlock; roster unlocks |

Map blocks, in order (houses / NPCs): X1 4001 / 4001; X2 4051 / 4101; X3 (Nightshadow, Newcastle) 4101 / 4201
(Newcastle's keep XD-13, `xd13.yml`, takes 4141-4150 / 4281-4300 of it);
X4 (Asp, Burlock village) 4151 / 4301; XD-07 Castle Burlock 4201 / 4401; X5 Winterkill 4251 / 4501; X6 4301 / 4601;
X7 and XD-17 Shangri-La 4351 / 4701; X8, X9 4401 / 4801; D1 Castleview 4451 / 4901; DD-03 Castle Kalindra 4501 / 5001;
D2 4551 / 5101; D3 Sandcaster 4601 / 5201; D4 Lakeside 4651 / 5301; D5 and DD-25 Bosco's Hall 4701 / 5401;
D6 Necropolis 4751 / 5501; D7 Olympus 4801 / 5601; dungeons and planes 4851 / 5701; roster, hirelings and the rest
4901 / 5801. Files sharing a block (D5 and DD-25; XD-02, XD-18 and FD-04 in the dungeons' block) keep their ids
apart by hand; the checks refuse an id used twice. Ids are never renumbered once a map lane uses them. A map whose
block is full takes further house ids from the rest block (4901+) as a second range of its `blocks` (D1's Lucio's
Jetty, 4901). Retired ids are not reused: NPC 5451 (Sablewing moved to X7 as 4720), routes 421-423 (Lucio's boats
down from Olympus, dropped by D-5.3).

## 3. Kinds

| kind | house_data Type | Default hours | What decides the service |
| --- | --- | --- | --- |
| weapon_shop, armor_shop, magic_shop, alchemist | Weapon Shop, Armor Shop, Magic Shop, Alchemist | 6-18 | `shop`: an engine `house_rules` row of that quality (and kinds) |
| fire_guild … dark_guild (nine) | Fire Guild … Dark Guild | 6-18 | `guild.spells`: the engine "Spellbook shops" row selling that many spells per school |
| training | Training | 6-18 | `training.cap`: the engine "Training halls" row with that cap; with none (cap 10), typeIndex 0 and the cap in column 17 (A1 reads it) |
| stables, boats | Stables, Boats | 6-18 | `routes`: a `transport_index` row (house id, up to three `transport_locations` ids; A1 reads it for a world house) |
| temple, tavern, bank, town_hall | Temple, Tavern, Bank, Town Hall | 1-24, 5-2, 6-18, 6-18 | price only |
| inn | The Adventurer's Inn | always | the roster (the house name must stay "The Adventurer's Inn") |
| residence | House | always | its residents |
| throne | Throne | always | its residents (a castle's throne room, e.g. Castle Burlock's) |
| mirror | (no house row) | — | `mirror`: written to `data_tables/mirrors.yml` for the world's Lua (A3's mirror list) |

Teacher offers are the engine's mastery topics 300-416 (`teacher_topics.txt`), placed in the NPC's topic slots before
A3's topics; an NPC has six slots in all. Guild membership is not used: houses of a world other than MM6/MM7 need no
membership (`HouseInteraction.cpp`, `magicGuildMembershipType`), so Vern and Vatawna keep their lines only.

## 4. What the generator writes

`gen_towns.build(ctx)` is a module of A2's `tools/xeen/build_world.py` (runs after `gen_quests`, whose
`ctx.shared['npc_topics']` keeps its slots; teacher offers take the free ones). Into the world's `data_tables/`, in the
columns of `devdocs/xeen/lanes/TABLES.md` (the engine's), the world's rows only:

| File | Rows |
| --- | --- |
| `house_data.txt` | one per house (not mirrors); typeIndex column 1 = the engine house_rules row (shops, guilds, training) or 0; Map = the map's map_id; Picture = the video stem; proprietor portrait = 10000 + owner id; column 17 the training cap |
| `house_animations.txt` | one per house: residents (comma list), video, `enter_sound` (Enter Sound), the sound base of the kind's voice of the owner's `sex` (D-165: `VOICES`, each a pair of the engine's house_animations whose proprietor portrait gives the voice's sex; 0 where the kind has none), proprietor portrait |
| `house_movies.txt`, `house_exits.txt` | header only (the video stem is given directly; no extra exits yet) |
| `npc.txt` | one per NPC: portrait, house (a proprietor lives in the house only when he teaches, has topics or `talks: true`; that resident has the proprietor's portrait, and the engine shows the two as one person once A1's F1 change lands: until then the house screen lists him twice, feedback F1 2026-11-21), profession (hirelings only), greeting id, topic slots, the map key in Notes, the title in the trailing Title column (written once the engine header has it, D-21) |
| `npc_greet.txt` | one per NPC with a greeting |
| `transport_index.txt` | one per stable or boat: its open routes |
| `transport_locations.txt` | one per open route |
| `roster.txt` | `roster.yml` |
| `continent_settings.txt` | `continents.yml`: one row per face (6 Cloudside, 7 Darkside): death map 1 = the face's start, death map 2 = its home temple (arrivals; each with a `before` place written while its map is unbuilt), followers, saturation, skies clear to storm, loading pages |
| `new_game_continents.yml` | `continents.yml` `new_game`: the new-game entry (one, "World of Xeen", continent 6) with its `card:` (order 1, title "Xeen (alpha)", `short_title: Xeen` (the journal tabs and sentences; must equal the quests' owner), subtitle, caption, picture; TABLES.md), the engine `character_selection.yml` shape |
| `town_portal_switch.txt` | `town_portal.yml`: groups `TPCloudside`, `TPDarkside` (continents 6 and 7), the destinations whose arrival exists; a plain file until A1's W4 reads it |
| `mirrors.yml` | per face: mirror id, town, qbit, map, arrival (for the world's mirror Lua) |

`teacher_topics` gets no rows (the engine's mastery topics are used). `trainer_places.txt` (the journal's trainer
finder, the engine table's columns) gets one row per teacher's house on an installed map: a door on an outdoor map at
the centre of the faces carrying the event that enters it (from `events/maps/<stem>.lua` and the map's scene), or an
entrance on the outdoor map whose event moves the party into the dungeon holding the house.
`python3 -I tools/xeen/gen_towns.py --out <dir>` writes the same tables into a scratch folder.

## 5. Checks (`tools/xeen/towns.py`)

- every id inside its map's block and the world range, none twice; every NPC in at most one house;
- every door of the map's project (`devdocs/xeen/briefs/<key>/L4/sketch.yml`, buildings with a `house:`; an indoor
  map without a sketch: the `source` of each event in its L4 `wiring.yml` that calls `evt.EnterHouse`, which must be
  the house this file gives that door) has a house, and every house names a door of the project or is marked
  `new_door` (a mirror: its event in the installed map's script, `-- evt:<door>`);
- a built file's houses against the installed map script (`events/maps/<stem>.lua`): every house but a mirror is
  entered by some event, and each event entering a house with `opens:` tests that qbit first and shows the file's
  `closed_text`;
- every route lands at an arrival some file names; a route's qbit name is registered in A3's quest file (a wait);
- every title follows D-21 (section 1, `title:`);
- every tavern off X1 fills packs to at least 14 days (its Val: `price:`, else its `was` row's; D-29);
- every house greets in a voice of its owner's sex (D-165; `gen_towns.voice_errors()` on the installed
  house_animations, also `gen_towns.py --check-voices`), and every `VOICES` pair is an engine house_animations row
  with a greeting sound file;
- every named resident has a portrait file (`npc<10000 + id>.png`) and a profession, a teacher offer or a greeting;
- residences per town against WORLD_DESIGN §5; services per town against its role;
- teacher offers against `teachers_plan.yml` (every offer in the plan is in a town file and the other way round; the
  plan's `extra:` list holds second offers of a mastery, e.g. Gem's and Errol's Master); an offer that opens by qbit
  must be the only Xeen teacher of that skill and mastery (the engine topic id is shared);
- a warning (`WARN`) when a Master place's plan level is below its Expert place's: the engine sells Master only to
  an Expert (D-73). A Grandmaster before its Master is no fault (the user, U-2) and is not checked;
- every house of a built town map hangs the sign of its kind (`tools/xeen/house_signs.py`, run by `towns.py` and on
  its own): the L4 sketch's `parts[].signs[].texture` of each building with a `house:` against the kind's boards,
  MM6-MM8's convention measured on the shipped outdoor maps plus Xeen's own boards of that kind. The Adventurer's Inn
  (`inn`) hangs only the key and heart `sginn` (Ravenshore, Dagger Wound, Tatalia, MM6), never a tavern's mug;
  a tavern `7sgtvrn`/`sgtvrn`; a guild its school's sign on both faces, never MM8's `sgspell` (D-92 (b)); a temple
  `sgtempl` (MM8's temples hang none); a dock `sgdock`; a town hall none. A wrong sign is an error, and so is a
  service of a signed kind with no sign (D-92 (a)), unless `house_signs.py` `NO_WALL` names the house and why it has
  no wall to hang one on (the 2026-11-22 kit fix: a `cottage` hangs the sign it is given; a `round_hut` refuses one;
  a treehouse hangs its board on the trunk's foot, a stepped tower on its lowest tier);
- every settlement's street villagers (D-96, `tools/xeen/villagers.py`): see section 6;
- the generator runs without error.

## 6. Street villagers (`villagers.yml`, D-96)

`source/towns/villagers.yml` lists every settlement of the town files (by `map` and `town` name): its palette of 3-5
townsfolk kinds (monster rows; a kind is a picture family, its tiers are one kind; each with an installed 3D model),
its `count` (about 0.7 per house door, hamlets 2 per door) and its monster `group`; or an `exempt:` reason (a lone
house in the wild, a castle interior, a shop in a dungeon). `villagers.py --place <map>` writes the start spots of a
map's settlements into the generated `villagers_spots.yml` from the built map (streets first, at least 640 from every
house door and 900 from every talking NPC, never inside a model or a decoration); the map's generator adds
`villagers.sketch_actors(<map>)` (peaceful, wandering, kinds in turn) and `villagers.relations(<map>)`. After a map's
houses move, run `--place` again before its rebuild. `villagers.py` (and `towns.py`) fail a built settlement with no
villagers, fewer than its floor (0.45 per door, at least 3; hamlets 2) or one kind, a palette outside 3-5 kinds or
with a row that is not townsfolk or has no model, neighbours (`neighbours:`) sharing two kinds, and a villager
starting hostile or by a door or giver. An indoor town whose lane has not placed its villagers yet (`placed_by:`) is a
warning.
