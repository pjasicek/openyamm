# X4 Burlock Savannah: L1 plan (MU-3, MU-4) for gate G1

A5, 2026-11-20. No geometry: nothing is built until the user has seen the board. The three YAML files here are
written by `output/studio_cal/x4/tools/gen_l1.py`; edit the script, then run `output/studio_cal/x4/tools/run.sh`
(generate, `oymap fmt`, `oymap validate --assets assets_dev`, drawings, board). Validation: no issues.

## What the plan holds

- **North**: the Gargoyle Range, bare peaks to 3,900 (Gargoyle Peak), ending in the world rim: a cliff at y 24
  above water at 0. The Gargoyle Eyrie (XD-26) in Gargoyle Peak's south face at 1,900; its sky-crack ledge at about
  3,300 above it. The King's beacon on the crest over the castle.
- **North-centre**: Castle Burlock on a rise (1,900; XD-07's gate), its walled village below the gate (1,300;
  14 x 12 cells, 15 doors), the jousting lists south of the village (tilt barrier north-south). The Great River falls
  out of the range beside the castle (the Olympian Fountain on a terrace by the pool) and runs south past the lists,
  under the King's Bridge, past Joe's caravan and Nystor's landing, out at x 79 to X2.
- **South-west**: Asp (17 x 13 cells, 17 doors): the Travel Pit and the Roadside Shrine on the Asp road at the east
  edge, outside the curse; the square with the well, eight pedestals round it, the rule stone by the XD-25 stair,
  Adam and Eve, the mirror. The Autumn Druid's grove and the barbarian camp to the north-west; the west downs.
- **South**: the jousting fields (renegade knights, quintain field, champions' barrow).
- **South-east**: the red dwarf hills (XD-02's west adit, the ogres' camp). **North-east**: the lava fields
  (Shrine of Fire, burned caravan, rim lookout), Falagar's hut on a lava shoulder.

## Figures (render_x4.py, `output/studio_cal/x4/mockups/figures.json`)

| Figure | MAPS | Plan |
| --- | --- | --- |
| Obelisk; device kinds | 1; >= 4, one permanent | 1; wells, fountain, stat challenge, shrine, quintain, pedestals (permanent: Olympian Fountain, lists, Shrine of Fire) |
| POIs | 30-40 | 38 (5 signposts) |
| POI spacing | 1,300-2,600 | nearest-neighbour median 5,480: not met (question 1) |
| Dungeon entrances | 3-6 | 4 (XD-07, XD-25, XD-26 + sky-crack exit, XD-02 adit) |
| Outdoor chests | 4-10 | 10, each with a reason |
| Spawn markers; hostiles at load | 45-70; 135 | 45; 135.5 expected (121.5 from markers + 14 placed) |
| Kill XP per member | 14.0k | 15.3k (+9 %) |
| Encounter areas (4,096² cells) | 3-8 of 6-30 | 5: 7.5, 10.0, 7.2, 12.1, 7.2 |
| Quiet land | >= 1/3 | 62 % |
| First fight | 2,000-6,000 | X2 2,600, X3 3,100, X6 3,300, X7 4,900, landing 3,500, Travel Pit 2,700 |
| Roads | 1-4 % | 2.6 % road tiles, 1.9 % lanes |
| Height range | >= 2,500 | 650-3,900 (3,250) |
| Farthest land from a place or fight | 6,000 | 5,100 |
| Towns | compact | Burlock 7.2k x 6.1k, 8.3 houses per 100 cells; Asp 8.7k x 6.7k, 7.2 (shipped 3.6-11.2) |

Monsters: slot 1 Xeen Knight Dif 1 [2,3] (jousting fields, 12 markers), slot 2 Xeen Ogre Dif 0 [2,3] (red hills 8,
west downs 7), slot 3 Xeen Gargoyle Dif 1 [2,4] (range west 9, range east and lava 9). Placed: barbarian camp 6
(11100-11102), ogres' camp 4 (11060-11061), renegade knights' camp 4 (11140-11141). The King's Guard stays in XD-07.

## Choices

- **Edges**: south x 36 (west half) to X3, level span 30-42 at 1,050; the river out at x 79 (X2's north_river at its
  x 30); south x 96 (east half) to X2's north road, level span 90-102 at 1,150 (X2's span is 1,150); west y 60 to X6
  (7 days); east y 66 to X7 (5 days). North is the rim.
- **Signature view**: from the lists' south end [69, 74] north to the castle, the range behind (sketch `views`).
  Arrival view: from X2's road [96, 107] north-west up the river valley.
- **Kits**: `royal_castle` (hc cream ashlar, cs grey footings and town wall, xtslate cones, Burlock crest) for the
  castle and the village wall; `cloudside_town` middle and rich grades for the village, poor and middle for Asp;
  chb1 fieldstone for guilds and the chapel. Ground per MU-2 (MM8 out03: grass_patchy tinted savannah, soil,
  dirt_cracked, rock_red, rock_layered; X7's gravel_volcanic for the lava).
- **D-4** (act2_dungeon_decisions.md): the eight pedestals in the cells round Asp's well (index 1 the south-west one,
  clockwise), the rule stone beside the XD-25 stair, Adam and Eve off the ring and off the door lines; XD-07's throne
  fall lands at ground + 1,000 (about 2,900) beside the west tower outside the walls (`entrance:throne_landing`,
  neighbour `fall:xd07_throne`); XD-26's sky-crack ledge at [49, 35].
- Quest hooks placed: Q-C5 (pedestals, rule stone, Adam, Eve, XD-25), Q-C10 and T1-C (Carlawna, the eyrie), Q-C11
  (Falagar), Q-C1 and T1-C (the Autumn Druid), M3 (the adit, qbit 110020), M5 (the castle gate), Q-C23 (Nystor's
  landing, qbit 112461).

## MU-4 concepts

Two `codex exec` calls (`tools/paint_x4.py`, A6's route), one each, no retry: `mockups/raw/x4_arrival_v1.png` and
`x4_signature_v1.png`, prompts and logs beside them. Both follow their blockouts and carry no text. The arrival
painting brings Nystor's boathouse nearer than the plan (it stands about 8 cells off); the signature painting shows
the castle, the village wall, the north-south tilt barrier, the stands and the falls where the plan puts them.

## What to look at

The board `output/studio_cal/x4/mockups/board_x4.png`: the castle and village size against the lists, Asp's square,
the spread of places over the savannah, the edges.

## Open questions

1. POI spacing: 30-40 POIs on a 90-cell square sit about 5,000 apart, not 1,300-2,600. Add about 20 small devices
   (X1 went to 52), or keep 38 and judge by the 6,000 rule (met)?
2. Signature view: the castle over the lists, or the falls, or the rim from the sky-crack ledge?
3. The castle rise at 1,900, 600 over the village behind a 450 step: right for XD-07's gate (A7)?
4. Hostile renegade knights in the jousting fields beside the friendly village: keep, or another family?
5. The lava fields are only 9 cells inside the playable bounds: enough, or widen the box east?

## Files

- Brief: `devdocs/xeen/briefs/x4/L1/{project,plan,sketch}.yml` (this folder).
- Scripts: `output/studio_cal/x4/tools/` (`gen_l1.py`, `render_x4.py`, `paint_x4.py`, `board_x4.py`, `run.sh`).
- Drawings: `output/studio_cal/x4/mockups/` (`plan_x4.svg`, `plan_x4.png`, `blockout_arrival.png`,
  `blockout_signature.png`, `board_x4.png`, `figures.json`); Codex raw returns in `mockups/raw/`.
