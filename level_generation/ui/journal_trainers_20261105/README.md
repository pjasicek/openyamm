# Journal trainer finder — study (2026-11-05, not approved)

The journal's Notes › Trainers page redesigned as a trainer finder for Standard MMMerge and MAW, in the approved
[Carved Obsidian journal](../obsidian_journal_20260928/README.md) frame, fonts and buttons.
Open `index.html` through a local web server (it fetches `data/finder.json`); published as
<https://claude.ai/artifact/NeowCQ9nfceB1moMnoapLh>.

## What it shows

- One list per continent (Jadame, Antagarich, Enroth), opening on the party's continent; every skill is one block with
  its Expert, Master and Grand Master teachers in the party creation screen's mastery colours.
- A search field (skill, mastery, trainer, town; matches highlighted) and E / M / G toggles; Previous and Next on the
  rail turn pages, the wheel too.
- Hovering a row names the house, map and requirement in the status strip; a click shows the trainer's outdoor map
  with a pulsing marker on the house door, or on the entrance of the dungeon or castle the trainer teaches in.
  Close or Escape returns to the list.
- **Ledger of Teachers**, one per continent (user, 2026-11-05): without it the finder lists only the trainers whose
  teacher autonotes the party has found (the review fixture marks about a third), with a line saying how many exist
  and where to buy the ledger. Each continent's taverns sell that continent's ledger as an extra topic with a
  sub-topic to buy it (2000 gold in the mockup); buying fills every trainer of the continent and the topic goes away.
  The skill-tooltip trainer hints are to follow the same knowledge.
- MAW: its extra houses (`rulesets/maw/data/npc_extra_houses.yml`) add rows on the other continents; Cover, Mana
  Shield, Enlightenment and Retaliation read "learned at skill N" with no map.

## Data

`data/trainers.json` (362 rows, every one with a marker) is built by `data/scripts/build_trainers.py` from
`teacher_topics.txt`, `npc.txt`, `house_data.txt`, `map_stats.txt`, the map scripts' `EnterHouse` and `MoveToMap`
events and the ODM faces and entities that carry them. Marker pixels use the game's minimap transform
(`pixel = ((x + 32768) / 65536 · width, (32768 − y) / 65536 · height)`). `data/scripts/build_finder.py` turns it into
`data/finder.json` (plus MAW rows) and `data/maps_web/*.jpg`. Run both from the repository root with `python3 -I`.
`data/maps/` holds the lossless map images (about 49 MB) and is only a build input.

Gaps the extraction found: Poundlin Lotts (Expert Shield, Erathia) has no reachable door; 11 NPCs carry a lesson topic
but stand in no house; Enroth has no Master Axe teacher.
