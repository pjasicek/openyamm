# MM6, MM7 and MM8 guide websites

Three player guides in the MM9 guide's format, one per continent: "MM6 Enroth Guide", "MM7 Antagarich Guide" and "MM8
Jadame Guide". Each has quests (main story by chapter, side quests, promotions), interactive maps of every outdoor map,
dungeon, castle and temple with their points of interest, travel (schematic world map, walking borders, coaches and
boats by weekday, route planner), teachers, shops and guilds, bestiary and items. They describe the game as OpenYAMM
plays it under the Standard (MMMerge) ruleset: the merged engine tables, the world packages' maps and Lua events, the
MMMerge overlays included. MAW's differences stay in the MAW guide. Everything but the walkthroughs, the FAQ and a short
list of hand-kept map points is generated; a quest without a written walkthrough shows its generated data.

```sh
tools/heavy.sh 16 python3 tools/mm678_site/build_site.py     # about 5 min the first time: storey plans of the dungeons
python3 tools/mm678_site/build_site.py --skip-images         # about 30 s for the three books: reuses plans and images
python3 tools/mm678_site/build_site.py --world mm7 --skip-images   # one book
```

Writes `output/mm6_site`, `output/mm7_site` and `output/mm8_site` (plans cached in `output/<world>_site_work/plans`).
Open `output/<world>_site/index.html` directly or serve the folder (`python3 -m http.server -d output/mm7_site`).
`tools/oy_guide/build.py` assembles the books into the one OpenYAMM guide.

## Shared code

The three books are worlds on the MM9 guide's code, like the Xeen guide, not copies of it:

- **Front end**: `tools/mm9_site/web/app.js` and `style.css`, copied into each output with a `page.html` that carries
  the book's title and brand (written from the MM9 page). A book's texts (title, leads, hidden shop columns, item
  notes) come in `GUIDE.site` (`site_config.yml` `books.<world>.site`). The data uses the generic fields the Xeen guide
  added: a quest's `giverText` and `reward`, a teacher's `when`, a promotion's `path` (MM7's Light and Dark),
  `travel.worldLinks`, house markers' `people`.
- **Generator**: `build_site.py` loads `tools/mm9_site/build_site.py` as a module (monster table reader, quest levels,
  bestiary filter, portraits and screenshots, icon atlas, enchantments, item categories) and
  `tools/xeen_site/build_site.py` (storey split of indoor plans, point placement, the player-text check); map lists,
  outdoor images, edges and dungeon plans come from `tools/maw_site/world_maps.py` and `dungeon_plans.py` (the MAW
  guide's single-storey plans in `output/maw_site/work/plans` are reused when present), event positions from
  `tools/trainer_places.py`, teacher topics, prices and extra requirements from `tools/maw_site/teachers.py`
  (Standard's 4/7/10 and the topic's price; no MAW table patches), promotions from `tools/maw_site/promotions.yml`
  (MAW-only fields not read; its `also` field, which MAW does not read, files a further journal quest under a
  promotion: MM7's Heart of the Forest under Ranger Lord). The story and FAQ loaders are the MM9 generator's.

## Files

- `build_site.py`: the generator. Writes `data/guide.js` (`window.GUIDE`), the map images (`img/maps/`), the item icon
  atlas and the web files, and stops on developer wording in a point, quest title, reward or giver text and on a
  reference that does not resolve (a quest's giver, hand-off or step, a teacher's, shop's, service's or promotion's
  place, a schedule, a region's map, a main quest's chapter).
- `site_config.yml`: the hand-kept parts per book: site texts, regions and their place on the schematic world map (one
  per outdoor map, cells following `outdoor_travels.txt`; dungeons join the region whose map leads into them), the main
  story's chapters as quest bits (MM7's Light and Dark paths are chapters V and VI), journal lines shown as stages of
  another quest, journal lines that are not quests, who starts a quest no person gives (`giver_text`) and route or
  lesson conditions in words (`gate_text`), side quests only one of MM7's paths offers (`paths`); the marker types.
- `extra_pois.yml`: the hand-kept map points per book, for what no rule finds or names: renames of generated points
  (`rename`: map, point id, new name, detail, type or quests: the Oracle's memory module altars, MM8's lettered levers
  of the Balthazar Lair, Xenofex, Dyson's hidden button) and points no event or scene places (`add`).
- `story/<world>/*.yml`: the hand-written walkthroughs (main story, side quests, promotions) in the MM9 guide's story
  format, written to `story/BRIEF.md`, read in file-name order; `story/<world>/img/` holds their pictures (copied to
  `img/story/`). The build checks every quest, map, marker type and named point; a map's `focus` is a point name
  substring and `show` its marker types, so renaming a point means checking the entries that focus on it.
- `faq/<world>/faq.yml`: the FAQ page's questions and answers, `[text](#route)` links; `faq/<world>/img/` their
  pictures (copied to `img/faq/`).

## Sources

| Data | Source |
| --- | --- |
| Maps, names, continents | `map_stats.txt` and `bolster_maps.txt` through `world_maps.load_maps` (MMMerge's placeholder rows left out) |
| Map images | Outdoor: the journal maps `worlds/<mm6-8>/icons_x2/<stem>` (±32,768 units, north up). Indoor: floor plans drawn from the BLV, one per storey where storeys lie over one another (the Xeen guide's split), named from the arrival's storey (Entry, Up 1, Down 1; the arrival is the `evt.MoveToMap` into the map, an outdoor map's first), and the map opens on it |
| Map events | `worlds/<world>/events/maps/<stem>.lua` and its overlays (`<stem>_mmmerge.lua`, numbered variants): `RegisterEvent`, `ReplaceMapEvent`, `AppendMapEvent`, the metadata's context actions (well, fountain, shrine, obelisk, lever, door, teleport, read) and learned effects; positions from the faces and entities carrying the event (`trainer_places.outdoor_event_points`, `dungeon_plans.indoor_event_points`) |
| Houses | `house_data.txt` types (shops, guilds, temples, taverns, banks, training halls, town halls, stables, boats, throne rooms, homes, dungeon and castle entrances); the people inside from `npc.txt`'s 2D location and the scripts' `evt.MoveNPC` |
| Exits | `evt.MoveToMap` to another map (a dungeon-entrance house's move by its seventh argument), map edges from `outdoor_travels.txt`; a move within the map is a teleporter |
| Wells, fountains, shrines, barrels | the learned-effect line, else the event's autonote, else its texts ("Refreshing!" left out) |
| Chests | `evt.OpenChest` events with the scene's chest contents: fixed items by name, random items by treasure level; a chest holding a quest's item carries the item in its name ("Chest L6 (Lord Kilburn's Shield)") |
| Items on the floor | the scene's `initial_state.sprite_objects` carrying an item: an item a quest's closing topic asks for is that quest's objective, named after the item (an item a topic takes for several quests goes to the quest whose journal line names it); other gear and letters are loot; reagents, potions, ore, gems, scrolls and gold are pickups (hidden by default) |
| Scene overlays | `<stem>_*.scene.yml` (MMMerge): their entities and face overrides place events the base map lacks, such as the dimensional travel pedestals (an event named "Dimensional travel" is a transport point) |
| Other script events | an event that asks for an item (`HasItem`, `RemoveItem`: a locked door, an altar, a Dragon Tower) is a door or lever with "Needs ...", or the objective of the quest that wants the item; any other named event with a message (a panel, a terminal, a riddle tree, a burial niche) is a lever or a sign. Levers and doors sharing a name on a map are numbered in reading order (storey, north to south, west to east); one event carried by faces far apart (2,048 units) gets a point at each place |
| People | NPCs in houses, scene actors with an `npc_id`, NPCs spoken to through a map object (`evt.SpeakNPC`) |
| Roles | an NPC's topics: its `npc.txt` slots, every `evt.SetNPCTopic` of the global and map scripts, MMMerge's Enroth grandmaster topics; teacher topics as `TrainerDirectory` resolves them (`teacher_topics.txt`, MM8's 300-416); promoters from `promotions.yml` |
| Monsters | `monster_data.txt` (family and tier from the picture "Lizardmen Warrior A", the family named after its first tier); scene actors and spawn points through `map_stats.txt`'s three encounter slots (peasants left out) |
| Quests | `english/quests.txt` rows owned by the continent with a journal text that some script sets (MM8's 5, 132 and 172 are set by none and left out); givers are the placed NPCs whose topic events set the bit, hand-offs those that clear it or check it (NPCs that check quests but never set or close one, such as seers, and those checking more than six, left out); without a placed giver, the map point or the person of the unplaced event that sets it (a messenger who finds the party), else `giver_text`; reward from the clearing topic (experience, gold) |
| Quest steps | map events that set, clear or check the bit; the map points that give or hold an item the turn-in asks for (events, chests, carrying monsters, the floor; items found in more than four places left out) and that set a helper bit the turn-in checks (a rescued person joining the party, Stanley's treasure chests; bits set in more than eight places left out) |
| Teachers | each teacher NPC's lessons at its places, Standard requirements (4/7/10 or the topic's own), the topic's price or the engine's default, MMMerge's held-back grandmaster topics; "Learn" lessons from `house_data.txt`'s skill column or `HouseTable.cpp`'s defaults by house type (weapon and armour shops by the item types they stock) |
| Shops and guilds | `house_rules.txt` by `HouseTable.cpp`'s rule id (type index, else map id): standard and special treasure levels, stocked item types, guild spell ranks; spellbooks are the continent's own books (`items.txt` `World:<world>`) |
| Services | temples, taverns, banks, training halls (max level from `house_rules.txt` or `house_data.txt`), town halls, inns, circuses, stables, boats, thieves' and mercenary guilds |
| Travel | stables and boats: `house_rules.txt` Stables/Boats rows, else `transport_index.txt`, with `transport_locations.txt` (weekdays, days, quest condition); fares 25 (coach) or 50 (boat) gold times the house's multiplier, before Merchant |
| Items | the engine's `items.txt` (one catalogue of MM6, MM7 and MM8 items for every book; placeholders and gold piles left out), icons from `engine/icons_x2` and the worlds' `icons_x2`; the MM9 guide's categories plus spell scrolls, potions and reagents, gems and ore; the atlas is redrawn whenever its icon list changes (`output/<world>_site_work/items_atlas.json`) |

## Player text

As the Xeen guide's: the guide states the built world in player words. Point names and details are what the player
sees (the event's name, the effect it gives, the chest's contents, the people in a house); obelisks say what they are,
not their message. Quest titles are the journal line's first sentence without its way back ("... and return to Lord
Newton in Mist"); the quest table's designer notes are used only for a giver ("Given by Dadeross in Dagger Wound")
when they read as player text. The build stops on developer wording (`xeen_site/build_site.py` `DEV_WORDING_RE`).

## Front-end wishes

Data these books emit that `app.js` does not show yet:

- An exit to another continent's map (MMMerge's links between the worlds) carries `xmap: {book, map}` instead of
  `map` (the shell could link `#<book>/map-<map>`); its detail names the continent.
- `sets` is empty (the merged table has no item sets): the Items page's "Set bonuses" tab could hide when it is.
- A quest's `path` (MM7's Light or Dark, also on its promotion) could show as the promotions' path chip.

## Known limits

- The world map is a schematic: regions placed by hand on cells that follow the walking edges.
- Main story versus side quests is the hand-kept chapter list; MM6-MM8 quest bits carry no story order.
- Each journal line is one quest with one stage (MM6's stable price notes are the one merge); multi-part quests that
  set several journal lines show as several quests.
- Quest steps come from the scripts' bits and items: a quest whose work is done through a bit only the map's own
  timers or kills set shows no step.
- Spawn points place a family's group, not a tier: the bestiary counts a group under each of the family's tiers.
- Shop stock is summarised (treasure levels, stocked weapon and armour types), not rolled.
- No monster portraits or in-game shots yet (phase 4).
- A lever's or button's number is its place in reading order, not a name the game shows.
- MMMerge's cross-continent routes (a coach or boat to another continent) are left out of a book's schedules.
