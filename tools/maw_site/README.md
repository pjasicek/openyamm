# MAW guide website

A static player's guide for the MAW ruleset ("MAW Guide"), generated from the ruleset and world data like the
[MM9 guide](../mm9_site/README.md): locations of all four continents (Enroth, Antagarich, Jadame and MM9's Chedian)
with interactive maps, skill teachers, classes, promotions, progression, crafting and tips. The generated parts follow
the game data; the prose sections are hand-kept HTML fragments.

```sh
python3 tools/mm9_site/build_site.py --skip-images   # once: Chedian's maps and teachers come from the MM9 guide
python3 tools/maw_site/build_site.py                 # writes output/maw_site
```

Open `output/maw_site/index.html` directly or serve the folder (`python3 -m http.server -d output/maw_site`).
Public copy: https://jasicek.net/openyamm/maw-guide/, updated with `tools/maw_site/deploy.sh`.

## Layout

| Path | What |
| --- | --- |
| `build_site.py` | The generator: runs the modules below, joins teachers and promotion givers to their houses' markers, writes `data/guide.js` (one `window.GUIDE` object), the map images and the web files. About 3 minutes; `--skip-images` reuses the map images and plan bounds (`output/maw_site/work/plans/`) and takes about 12 s. |
| `world_maps.py` | MM6–MM8 maps by continent (`bolster_maps.txt`; MMMerge's "pending" placeholder rows left out): names, MAW level bands (Free, Horizontal, Beyond Madness), refill days, map images and markers. |
| `dungeon_plans.py` | Top-down floor plans of the 161 MM6–MM8 indoor maps, drawn from the BLV geometry, and the positions of their event faces and decorations for markers. `--out <dir> [--only ...] [--debug-events]` renders plans for review. |
| `teachers.py` | Every Expert, Master and Grandmaster lesson as the game's `TrainerDirectory` lists it under MAW (moved teachers included), with MAW's skill requirement and price per mode; Chedian's lessons from the MM9 guide. |
| `classes.py`, `class_notes.yml` | Every MAW class line: class columns with HP and SP per level (Elder and Ultimate on final classes), mastery caps, starting skills, races; `class_notes.yml` holds the hand-checked mechanics bullets. |
| `maw_tables.py` | Reads the engine tables with the MAW ruleset's patches applied, as the game does. |
| `promotions.yml` | Hand-kept: each line's promotion quests per continent (giver, house, map, task, path, whether MAW counts it), Chedian's included. |
| `content/*.html` | Hand-kept prose sections, one fragment per section (see below); `content/img/` holds their screenshots and the class icons. `content/RECAPTURE.md` lists screenshots that are stale or missing. |
| `web/` | `page.html`, `style.css`, `app.js` (no libraries). Hash routes: `#start`, `#locations`, `#continent-<id>`, `#map-<map>`, `#map-<map>-<poi>`, `#teachers`, `#classes`, `#class-<id>`, `#promotions`, `#progression`, `#crafting`, `#tips`, `#combat`, `#loot`, `#spells`, `#deviations`; `#<section>/<heading id>` jumps within a prose section. |
| `deploy.sh` | Publishes `output/maw_site` to the server, like the MM9 guide's. |

## Map data

| Data | Source |
| --- | --- |
| Outdoor map images | `worlds/<mm6-8>/icons_x2/<stem>`, spanning ±32768 world units with north up (`MapPresentation` defaults) |
| Indoor map images | `dungeon_plans.py`; markers placed through the plan's bounds |
| Houses (shops, guilds, temples, taverns, banks, training halls, boats, stables, castles, homes) | `house_data.txt` types; door positions from the map scripts' `EnterHouse` events and the faces and entities carrying them (as `tools/trainer_places.py`) |
| Dungeon entrances and exits | `MoveToMap` events (the seventh argument names the dungeon-entrance house whose Enter makes the move); map edges from `outdoor_travels.txt` |
| Wells, fountains, shrines, obelisks, pedestals | named map events; the detail is the event's autonote comment or status text |
| Levels | `rulesets/maw/data/map_levels.yml` (Chedian: `rulesets/maw/worlds/mm9/balance.yml`) through `MawMonsterLevels.cpp`'s formula for the native families' normal tier |
| Refills | `map_stats.txt`, with `MawMonsterRules::mapRespawnDays`'s never-refill ranges |
| Chedian | the MM9 guide's maps and markers (monsters, loot, traps and doors left out: their levels follow MM9, not MAW) |

## Known limits

- Chedian (MM9) became MAW's fourth continent on 2026-11-09; its bands come from `balance.yml`, whose first pass may
  still move. Its rules for the guide are in `devdocs/maw/MM9_BALANCE_DESIGN.md` section 9 (density, promotions:
  MAW's `promotions.yml` `mm9` and `mid` bits against MM9's done keys).
- Promotion givers and teachers in houses without a placed door (Poundlin Lotts in Erathia) have no marker.
- A few indoor plans draw small because the map has far-off areas reached by teleport (`mdt15`, `6d08`, `7d11`).

## Content fragments

`content/<section>.html` are plain HTML fragments (no `<html>`, `<head>` or scripts): `<h2 id>` per subsection,
`<h3>`, `<p>`, `<ul>`, `<ol>`, `<table>` (wrapped in `<div class="tbl">`), `<figure><img src="img/..."><figcaption>`,
and three boxes: `<div class="tip">` (advice), `<div class="note">` (where OpenYAMM differs from MAW) and
`<div class="warn">` (a permanent or costly choice). Numbers are wrapped in `<span class="num">` when they stand
alone. A fragment may contain `<div data-guide="<block>"></div>` placeholders that the app fills from generated data
(`map-levels`, `teachers`, `class-table`, `promotion-table`, `mitigation-calculator`). Style: short,
concrete, no flavour text; a worked example beats a paragraph.
