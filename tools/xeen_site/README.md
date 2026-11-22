# Xeen guide website

A static player guide for the World of Xeen ("Xeen Guide"), in the MM9 guide's format: quests (the main story by act,
side quests, promotions with their class lines and Light/Dark paths), interactive maps of all 82 maps with their points
of interest, travel (schematic world map of Cloudside, Darkside, the sky and the planes; coaches and boats; mirrors,
pyramids, Town Portal; route planner), teachers, shops and guilds, bestiary, items and FAQ. Everything except the
walkthroughs and the FAQ is generated from the world package, so it follows the game data.

```sh
python3 tools/xeen_site/build_site.py               # about 70 s (plans of 69 indoor maps); writes output/xeen_site
python3 tools/xeen_site/build_site.py --skip-images # about 10 s: reuses the map images and output/xeen_site_work/plans
python3 tools/xeen_site/capture_monsters.py --jobs 2 [--missing]  # optional, about 90 min: bestiary portraits
python3 tools/xeen_site/capture_shots.py --jobs 2    # optional, about 40 min: arrival views, outdoor quest givers
tools/xeen_site/deploy.sh                            # publish to https://jasicek.net/openyamm/xeen-guide/
```

Open `output/xeen_site/index.html` directly or serve the folder (`python3 -m http.server -d output/xeen_site`).
The capture scripts run isolated, minimised game boots of the Xeen build (`build-xeen/game/openyamm`, or
`$OPENYAMM_GAME_BINARY`), at most two at once; rebuild with `--skip-images` afterwards to pick their pictures up.

## Shared code

The Xeen guide is a second world on the MM9 guide's code, not a copy of it:

- **Front end**: `tools/mm9_site/web/app.js` and `style.css` serve both guides. A world's texts (title, leads,
  defaults, hidden shop columns, item notes) come in `GUIDE.site` (`site_config.yml` `site`); without it the page is
  the MM9 guide. Generic additions used only by Xeen data: `travel.extras` (mirrors, pyramids, Town Portal tables),
  `travel.worldLinks` (the world map's lines), a quest's `giverText` and `reward`, a teacher's `when`, a promotion's
  `path` chip, a map's `defaultFloor`, house markers' `people` (also matched by the story loader). Only `page.html` is
  Xeen's own (`web/page.html`: title and brand).
- **Generator**: `build_site.py` loads `tools/mm9_site/build_site.py` as a module and uses its readers, monster table
  reader (`load_monsters(world, "Xeen")`), items and icon atlas (`build_items(..., world, icon_dirs)`), story and FAQ
  loaders, quest levels, screenshot and portrait attachment. Indoor plans come from `tools/maw_site/dungeon_plans.py`
  and outdoor event positions from `tools/trainer_places.py` (both pointed at the `xeen` world); teacher prices and
  extra requirements from `tools/maw_site/teachers.py`.
- **Captures**: `capture_monsters.py` and `capture_shots.py` reuse the MM9 scripts' crosshair removal, crop and tour
  layout.

The MM9 guide's output is unchanged by the sharing: `data/guide.js`, `index.html` and the rendered DOM of its pages
were compared before and after (2026-11-21).

## Files

- `build_site.py`: the generator. Writes `data/guide.js` (`window.GUIDE`), the map images (`img/maps/`), item atlas,
  shots and portraits, and copies the shared web files.
- `site_config.yml`: the hand-kept parts: site texts, regions and their place on the schematic world map (dungeons
  join the region whose map leads into them, `region_of` for the rest), the promotions' paths and quests, the acts'
  names, the marker types, capture exclusions.
- `story/`: the hand-written walkthroughs: `act1.yml` ... `act6.yml` (the main story, chapters 1-6) and the flat
  `side_cloudside.yml`, `side_darkside.yml`, `promotions.yml`, written to `story/BRIEF.md` (sources and their
  authority: the playthroughs, the quest files, the map scripts, lane A3's records). Quests without an entry show the
  generated data (giver, reward, journal notes, quest points).
- `extra_pois.yml`: hand-kept map points: renames of generic points (DD-17's four Heads, XD-06's pool buttons,
  XD-11's lift gates) and puzzle pieces the scripts cannot place (`add`). Puzzle pieces of the common script (genie
  lamps, the pyramid's niches, the vowelless books, merchants, tolls) and other named clickables (dials, talking
  skulls, gongs, safes) are found by the generator.
- `story_figures.py`: annotated figures for the puzzle walkthroughs (`story/img/`: Asp's pedestals, the Bark dials,
  the Great Pyramid's niches, the Shrines of Evil and the gong hall), drawn on the guide's own plans from the built
  points (`python3 tools/xeen_site/story_figures.py` after a build; rebuild to copy them).
- `faq/faq.yml`: the FAQ (two sides, Darkside, fast travel, Fly, Newcastle, Castle Kalindra, promotions, wells,
  cursed towns, gems, obelisks, teachers), `[text](#route)` links.
- `capture_monsters.py`: one boot per monster in the great hall of the Tower of High Magic (XD-11) as an AI arena.
  The camera stands back by the larger of the monster's collision box and its 3D model's drawn size (the model's
  bounds at its `actors.yml` scale: the swamp things' treant is about 1,150 tall on a 199-high box), measured to the
  model's front, and looks down by the crop's offset so the monster sits in the middle of the cropped portrait.
  The dragons' models (`CLOSER`) stand at 0.72 to 0.85 of that distance: their bounds hold the bind pose's outspread wings.
  The Warzone (XD-20) cannot host it: a map that forbids saving cannot start an isolated run.
- `capture_shots.py`: one boot per map: the arrival view and the people placed outdoors that give story quests or
  promote (`FAR_NPCS` sets a farther camera for people too big for the close-up: Leafpoint the Elder Tree). XD-20
  forbids saving and gets no shots (an isolated run cannot start there).
- `deploy.sh`: rsync to the server's `~/xeen-guide-upload`, then `sudo -n rsync` into
  `/var/www/html/openyamm/xeen-guide/` (beside `mm9-guide/` and `maw-guide/`, which it does not touch).

## Sources

| Data | Source |
| --- | --- |
| Maps, names, acts, regions | `source/maps.yml`; regions in `site_config.yml` |
| Map images | Surface maps: the journal maps `icons_x2/<map>.png` (±32,768 units, north up). Every other map: floor plans drawn from the BLV, one per storey where storeys lie over one another (levels carrying 4 % of the floor area, 320 or more apart, covering each other), named from the arrival's storey (Entry, Up 1, Down 1) |
| Houses, people, teachers, shops, guilds, services, coaches and boats | `source/towns/*.yml` (A4's town files, with `teachers_plan.yml` for each lesson's place, act and gate); doors located by the map scripts' `EnterHouse` events and the faces and decorations carrying them; shop quality from `house_data.txt` and the engine's `house_rules.txt`; fares from `house_data` Val (25 or 50 gold times Val, as `PriceCalculator::transportPrice`) |
| People placed outdoors and in dungeons | scene actors with an `npc_id` |
| Quest steps, wells, fountains, shrines | the map scripts' `XeenQuests.hook(...)` calls with `data_tables/quest_hooks.yml` (quest, where) and the hooks' player texts in `source/quests/*.yml` and `source/npcs/*.yml`; once-a-day ones by `Xeen.usedToday`/`markToday` |
| Exits, teleporters, chests, levers, doors, signs, obelisks | the map scripts' events (`MoveToMap`, `OpenChest`, `SetDoorState`, texts) and their Map Studio tags; dungeon chests from the scenes' `loot_containers` (treasure level, gold, `fixed_items`: a chest holding a quest item a hook lists in `map_gives` is merged into the quest point on the same spot); surface edges from `maps.yml` `neighbours` and `outdoor_travels.txt` |
| Items on the ground | the scenes' `initial_state.sprite_objects` carrying an item (D-90): a quest item a hook lists in `map_gives` is a quest objective named after the item, other loot a "Chest / loose item" point |
| Monsters | `data_tables/monster_data.txt` (family and tier from the picture "Xeen <Family> <A-C>"); placed actors, and outdoor spawn points through `map_stats.txt`'s three monster slots |
| Quests | `source/quests/*.yml`: title, act, kind, giver, journal lines, rewards, NPCs with topics; promotions from the `{promote: key}` steps and `Xeen.Promotions` in `events/common/xeen_common.lua` |
| Travel | coach and boat routes (town files), `data_tables/mirrors.yml`, `Xeen.Pyramids` and `Xeen.PyramidArrivals` (`xeen_common.lua`), `source/towns/town_portal.yml` |
| Items | `data_tables/items.txt`, `item_effects.txt`, `item_sets.txt` (Xeen's own items; icons from the Xeen, engine and MM6-MM8 `icons_x2`) |

## Player text (D-76)

The guide states the built world as fact, in player words. Map point details are what the player reads on the click (the
hook's text when the click always shows it, else the first clause of the hook's place, cleaned) and the prompt a point
asks; a point never carries a typed answer: the answer of its own prompt, nor (five letters or more) one of its map's
prompts spelled out by a clue, which keeps its text up to that clause. The answers stay in the walkthroughs, which are
closed by default. The build stops on developer wording (hooks, identifiers, "the source", "the map's", qbits, event
numbers, decision ids) or an answer in any point name or detail, and on developer wording in a generated reward;
`extra_pois.yml` is the place to fix a point by hand. D-79: a point says what a thing is, what it asks and what it does
when used, never how to solve it (no value, order, combination, pairing, route, word or pieces of one, whether a clue or
the guide says it), so a clue is quoted up to that clause and its solution phrases go in `extra_pois.yml` `solutions`
(map-wide, or per point for short pieces such as rune syllables), which the build refuses in any point. Walkthroughs
name quests by their titles and do not mention the playthroughs, scenarios or quest files. Arrival shots of indoor maps
face the longest clear view when the arrival faces a wall or door close by, and step back to the wall behind in a small
entry room.

## Known limits

- The world map is a schematic: regions placed by hand; dashed lines are passages through dungeons, the sky or the
  pyramids (only pyramids are labelled), solid lines walking edges with their days.
- Spawn points place a family's group, not a tier: the bestiary counts a group under each of the family's tiers.
- Outdoor chests have no treasure level in the data the guide reads (the level is in the map's chest records).
- People in houses have no in-game picture (the house screen is not a 3D view).
