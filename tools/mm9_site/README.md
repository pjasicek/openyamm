# MM9 guide website

A static, multi-section player guide for the MM9 world ("MM9 Chedian Guide"): quests (main story, side, promotions),
interactive maps with points of interest, travel (schematic world map, schedules, route planner), teachers, shops,
bestiary and items. Everything is generated from the world package, so it follows the game data.

```sh
python3 tools/mm9_site/build_site.py              # about 10 s; writes output/mm9_site
python3 tools/mm9_site/capture_shots.py --jobs 3  # optional, about 5 min: in-game screenshots (isolated game runs)
python3 tools/mm9_site/capture_monsters.py --jobs 3  # optional, about 8 min: bestiary portraits
python3 tools/mm9_site/build_site.py --skip-images   # picks up the screenshots, reuses converted map images
```

Open `output/mm9_site/index.html` directly or serve the folder (`python3 -m http.server -d output/mm9_site`).
Public copy: https://jasicek.net/openyamm/mm9-guide/, updated with `tools/mm9_site/deploy.sh` (rsync to the server, then
sudo into `/var/www/html/openyamm/mm9-guide/`, beside the MAW guide).

## Files

- `build_site.py`: the generator. Writes `data/guide.js` (one `window.GUIDE` object), converts the MM9 map PCXs to WebP,
  packs the item icons into one atlas and copies the web files. `page.html` is the page body; the generator wraps it
  into `index.html` for local use (an artifact host adds its own document skeleton to `page.html`).
- `site_config.yml`: the hand-kept parts: regions and their place on the schematic world map, map kinds, story chapters
  by quest-note bit, the promotions table (promoter RUDE ids and task quests, from the promoters' scripts), and the
  marker types (legend order, colour, glyph, shown by default).
- `web/`: `page.html`, `style.css`, `app.js` (no libraries). Routes are plain hashes: `#quests-main`, `#quest-<id>`,
  `#map-<map>`, `#map-<map>-<poi>`, `#travel`, `#teachers`, `#shops`, `#bestiary`, `#monster-<id>`, `#items-<cat>`,
  `#item-<id>`, `#faq`.
- `story/`: the hand-written main-story walkthrough, one YAML file per part (`prologue_ch1a.yml`, `ch1b.yml`,
  `ch1c_ch2.yml`, `ch3_5.yml`), written to `story/BRIEF.md` (format, sources and their authority: the rework's map
  scripts first, online guides only where they agree). The Main story page renders it as a document with compact maps
  beside each quest; quests without a written entry fall back to the generated data. `build_site.py` checks every
  quest id, map, marker type and giver.
- `story/img/`: pictures a walkthrough entry shows under its steps (`figures: [{img, caption}]`, copied to
  `img/story/`). `story_figures.py` draws the annotated ones from the map data and the site's own map images (run
  `build_site.py` once first); its docstring says how the in-game captures beside them were made.
- `extra_pois.yml`: quest props and puzzle pieces the generator cannot find on its own (imp gates, bell ropes, book
  tables, the Thing's games), placed at their MM9 DAT objects, and renames of generated points.
- `faq/faq.yml`: the FAQ page's questions and answers (continent travel, promotions, where the skills MM9 lacks are
  learnt), with `[text](#route)` links; its skill table is built from the teachers data. `faq/img/`: its pictures,
  drawn by `faq_figures.py` (`--capture` takes the Sturmford City screenshots in one isolated game boot, then rings and
  labels the dimensional travel pedestal), copied to `img/faq/`.
- `capture_shots.py`: one isolated game boot per map with a screenshot tour: the arrival view at the map's first start
  point, and a framed view of each story quest giver, promoter and dock NPC. Output in `output/mm9_site_shots/`;
  `build_site.py` drops captures that missed the scene (flat frame, or open sky behind an NPC).

- `capture_monsters.py`: one isolated boot per bestiary monster: an AI arena on The Arena (every placed actor removed,
  the monster spawned alone and not hostile) and a one-shot tour in front of it, distance and pitch from the monster's
  collision size; the HUD is cropped away and the crosshair painted out. Output in `output/mm9_site_monsters/`.
  Monsters that start burrowed or hidden photograph as an empty pit: `site_config.yml` `monster_portrait_exclude`.

## Sources

| Data | Source |
| --- | --- |
| Map images, bounds, floors | `worlds/mm9/ui/maps/*.pcx` and `catalog.yml`; maps missing from the catalog use the MM9 DAT header bounds and floor bands of `tools/mm9_import_discovery/promote_mm9_map_images.py` |
| NPCs, monsters, chests, piles, breakables, ladders, doors | `worlds/mm9/maps/*.scene.yml` (rebuilt maps; positions in OpenYAMM units) |
| Door names (lever, secret, trap, door) | the `DOORS` table of `worlds/mm9/events/maps/<map>.lua` |
| Switches, hidden buttons, perception spots, teleporters, wells, cauldrons, stat barrels, traps | raw MM9 DAT objects, `assets_editor_dev/worlds/mm9/maps/*.raw_objects.yml`; well and cauldron effects from the `MM9.use*` calls in the map events |
| NPC roles | RUDE ids against `skill_trainers.txt`, `dialogue/racial_trainers.yml`, `vendors.txt`, `service_venues.txt`, `transport_routes.txt`, `hirelings.txt`, the promotions table |
| Teachers | `skill_trainers.txt` (Expert to Grandmaster), the `learn_skills` of the venues and shops (Learn: `service_venues.txt`, `vendors.txt`), `dialogue/racial_trainers.yml` (the racial abilities, names from `dialogue/rude/NPCNAME.rude`) |
| Shop stock | `state/vendor_stock_audit.yml` (JSON, written by `generate_mm9_vendors.py`): each shelf's treasure level, the item tiers and enchantments stocked, the restock lists; the Shops page's weapons and armour by town, its spells by school and mastery (each tier's shops, with their maps) and its spellbook list (every book, the shops that sell it, on every restock or on some of their lists, and its price there before Merchant) |
| Quests | `data_tables/english/quests_overlay.txt` (stages grouped by headline), givers and turn-ins from `state/quest_interactions.yml` |
| Quest steps | every handler of `worlds/mm9/events/maps/<map>.lua` that checks or gives quest keys or quest items, placed at the DAT object its comments or item provenance name; keys tied to quests through the journal's show/hide conditions (`state/quest_interactions.yml` `journal_stages`). Entry numbers share the key range, so they are not used as keys; keys gating more than three quests are ignored |
| Promotion class lines | `MM9.Promotions` in `worlds/mm9/events/common/mm9_common.lua` |
| Travel | `map_transitions.txt` (exits, days), `transport_routes.txt` (vessel, weekday, days, price) |
| Monsters | `worlds/mm9/data_tables/monster_data.txt`, placed non-civilian actors |
| Items, sets, enchantments | `worlds/mm9/data_tables/items.txt`, `item_effects.txt`, `item_sets.txt`, `icons_x2/`; engine `standard_item_enchants.txt`, `special_item_enchants.txt` |

## Known limits

- The world map is a schematic: regions placed by hand in `site_config.yml`, linked by the real exits and routes.
- Main story versus side quests is a quest-note bit cut (`main_story_below_qbit`); chapters are bit ranges.
- Quests whose notes come from events rather than a placed NPC show no giver.
- Shop stock is summarised, not listed item by item, except the spellbooks: equipment shops show their treasure levels,
  item tiers and enchanted share.
