# D6 The Forbidden Zone: L1 plan (MU-3, MU-4) for the phase 5 review

A6, 2026-11-20. A plan only: there is no geometry. Nothing is built until a decider has approved the board. The four
YAML files here are written by `level_generation/xeen_art/phase5/d6_brief.py` (edit the script, then run it,
`oymap fmt` and `oymap validate devdocs/xeen/briefs/d6/L1 --assets assets_dev`: no issues). Drawings, measures, the
edge matches and the board: `level_generation/xeen_art/phase5/` (`d6_render.py`, `d6_concepts.py`, `board_d6.py`;
outputs in `d6/`).

## What the plan holds

- **Middle: Castle Alamar** (source A1(10,4)) on a basalt mesa (cells 39-62, 36-62, to 2,300) in a **horseshoe moat
  of lava** (1,550, `lavtyl`) open to the south. The approach ramp climbs onto the mesa between the moat's arms past
  four energy-field pylons to the castle's double gate (51, 55): `m33.castle_door` ("Castle Alamar. Every window is
  lit, and every one of them is looking at you. Enter?"); DD-17's arrival hook refuses a party without the Soul Box
  and moves it back here. The castle about 10 x 10 cells: Ancient kit outside (`xahull` on `gn_mtl`, `xaenergy`
  pylons, `xafield` curtains), square towers, every window lit, no walkable roof (WORLD_DESIGN 3.4). **Two states**
  (set:alamar): whole until `m33.done`; then a smoking ruin (`xahullbn`, fallen towers, fields dark) with the sealed
  stair to FD-01 in the broken gatehouse's floor (`m39.depths_door`, the Cube of Power; one POI spot with the gate).
  Robot patrols (E2) on the mesa and the approach, off after M33.
- **The lava.** The moat spills over the north rim (the Northern Lava Falls, x 44), west along the Slag Run over the
  west rim (y 51), and south-east down the Burning Channel into **Corak's lava lake** (cells 61-80, 57-75, 1,450).
  **Escape Pod 1** (Corak's, DD-16) stands nose-up in it at (72, 67), half sunk, its hatch midship toward the
  south-east shore over a tongue of crust (74, 70): `m29.pod_door` (reads `m28.lava_cooled` 111564); before it the
  fail line, after it the lava round the hatch is black crust (set:pod_lava). D-47: the hatch names `arrival:
  entrance:d6_hatch` (DD-16's airlock about 192 inside); DD-16's way out lands on the crust about 384 before the
  hatch, facing away (south-east, toward the shore; measured at L3). A black islet in the lake carries a genie lamp
  (the lure). Lava dwellers (14 placed elementals) on the shores; none within 2,500 of the hatch.
- **North-east: the Ancient field.** Rock heaved by buried Ancient metal: plates, spars and broken pylons surfacing
  everywhere (WORLD_DESIGN 4). **Escape Pod 2** (Sheltem's, DD-22) upright in its own crater at (78, 38), its hatch
  sealed with a line until phase 6. The **Well of Warding** (source B1(14,13), +100 resistances rescaled: +20 to the
  four elemental resistances until rest, daily) by the north-east rim; an Ancient locker (chest). Gamma gazers (E1).
- **North-west: the volcanic waste.** Ash and basalt between the moat and the rims, quiet: the **hot spring** with
  the **Fountain of Super Resilience** (source A1(2,13), +2,500 HP rescaled: +100 HP until rest, daily) and a burned
  pilgrim's pack; a basalt pinnacle with a genie lamp.
- **West and south-west: the cinder plains** (source A2): the **obelisk** on Obelisk Knoll (30, 62) above the Slag
  Run's fall (`obelisks.d6`, PYRAMID); a cinder cone by the Alamar road; the **barbarian archers' camp** (34, 86) with
  12 placed archers and their strongbox.
- **South: the Forbidden Zone's southern border.** Peaks to 3,800 along y 94-104 with **Griffin Pass** (64, 96, 2,450)
  at the top of D1's long mountain road: **Ambrose's camp** (5512, a tent, a fire, a tethered griffin;
  `m25.flight` from his topic to DD-14's landing `entrance:d6_griffin`). West of the pass **DD-10C's north adit**
  (46, 97) facing north between two boarded mine mouths (dressing) and a dead prospector (chest); east of it the
  broken travel pyramid in a high valley (landmark, no click), a griffin's nest (chest), a genie lamp on a crag, and
  the Sardaj cliff down to D1's spring pool at the border. Griffins (E4a, E4b) on both sides; the pass is clear.
- **East: Necropolis** (cells 82-100, 74-90, terrace 1,650) under the east ridge, A4's d6.yml in full: one gate in
  the north wall (91, 74), two iron-bound leaves under a gatehouse; the pass (item 12336) opens it, else a line
  turns the living away (A3's hook, A6's event; from inside always open). Inside: the **Square of Mourning** with the
  Mirror (4756, qbit 119011) and the talking skull on its plinth (the two necromancers' story), the **Books of the
  Dead** at its west edge (three books: +3,000 experience and +8 years of age, once per character each: the map's
  permanent-effect device), the guild 4751 and the **Warm Barrel** 4755 (its barrel "Food for the dead, keep warm."
  beside the door, one spot) west, the Grave Market 4753 and the Embalmer 4754 east, the Temple of the Dead 4752
  south, six tombs and mausoleums 4757-4762 along the south lanes (the Necromancers' House is Master Morbius's,
  Q-D23), **DD-21's crypt stair** (98, 88) in the south-east corner. Arrival `necropolis_gate` inside the gate by the
  mirror. Darkside town kit in its darkest grade (t09 ashlar under `xlslate`, walls about 700 with square towers),
  tombs in MM7 Zokarr's Tomb stone (twb1, twb2, 7tws2), crypt doors in two leaves (gkp103a/gkp103b).
- **The Bone Road** from the **border pass** to D5 (105, 64; the source's sign "The Forbidden Zone." at its lip) down
  to Bone Fork and the gate; a pilgrim's coffin-cart turned back at the gate (chest); **Freeda the Mountaineer's
  camp** (100, 69; A4 has no row); a roofless watchtower of the dead on the ridge (landmark).
- **Roads:** the mountain road (D1) over Griffin Pass to Ash Fork; the Alamar road north-west to the approach; the
  Necropolis road east past the lake to Bone Fork; the pass road (D5); lanes to the hatch, the adit, the obelisk, the
  hot spring and through the Ancient field to Sheltem's pod and the well.

## Figures (`d6_render.py`, `level_generation/xeen_art/phase5/d6/measure.json`)

| Figure | Target (MAPS D6, §0 checklist) | Plan |
| --- | --- | --- |
| Hostiles at load | 110, few and strong | 110: markers 42 at [1, 3] (gazers 17, robots 9, griffins 16) = 84; placed 26 (14 elementals, 12 archers) |
| Kill XP per member | 71.1k (±15 %) | 73.4k (+3 %): MM7's tier odds (Dif 1 90/8/2, Dif 2 70/20/10, Dif 5 10/50/40), XP = L(L+10); gazers 21.1k, robots 14.3k, griffins 17.2k, placed 20.8k |
| Monster band | A 38-50, C 65 | Eyes 40/50/65 (Dif 2), Robots 50/62/75 (Dif 1: Autobot 75 at 2 %), Great birds 30/38/48 (Dif 5: Vulture Roc 30 at 10 %), Lesser Elemental 55 / Elemental 62 placed, Barbarian Archer 44 / Chief 50 placed (requested rows) |
| Encounter areas (4,096²) | 3-8 of 6-30; camps | E1 field 18.2, E2 Alamar 7.5, E4a 7.8, E4b 7.9; camps: E3 lake (placed, 1.8 of land), E6 archers 1.1 |
| Quiet land | at least 1/3 | 57 % of the land in the box (lava not counted) |
| POIs (D-15/D-20 census: chained merge within 400; service doors, mirror, gates, dungeon doors in; residences, talking NPCs, dressing, landmarks out) | trap band 22-28 | 27, with the town's 8 (5 service doors, the mirror with the skull, the books, the gate) and DD-21's stair; spacing median 4,050 (sparse, as X7's accepted 3,280) |
| Outdoor chests | 4-10, a reason each | 6 (archers' strongbox, griffin nest, prospector, Ancient locker, pilgrim's cart, spring pilgrim) |
| Dungeon entrances | 3-6 | 6: DD-17 gate, FD-01 stair (ruin state, same spot), DD-16 hatch, DD-22 hatch (sealed), DD-21 stair, DD-10C adit; plus Necropolis's pass-gate |
| Obelisk; devices | 1; >= 4 kinds, one permanent | 1; fountain, well, the Books of the Dead (permanent), genie lamps x3, the skull, the barrel, signposts x2, the mirror |
| Relief inside the box | >= 2,500 | 834-3,710 (2,875); without D1's spring pool at the border about 1,100-3,710 |
| First fight, edge arrivals | 2,000-6,000 | from D1 (64, 105): 2,820 (east griffins); from D5 (105, 64): 4,920 (gazers) |
| Town arrival (D-15) | buffer 2,500 | inside the gate 8,480; nearest fight to a Necropolis door 3,310 (the Quiet Tomb) |
| 6,000 rule; wild land (D-11.5) | none over 6,000; <= 0.16 | farthest 5,970 (the west rim at [24, 72]); 0.13 |
| Roads | 1-4 % | 1.7 % roads + 1.2 % lanes |
| Houses drawn / d6.yml | 4751-4762 | 11 doors + the mirror |
| Lava | D-40: lavtyl, never water | the lake 268 cells, the moat 267, three lava rivers; lava falls over both rims |
| Textures | phase 5 outdoor cap (<= 12 new beyond the kits) | ancient, darkside_town, crypt families (dungeon_families), MU-2's D6 row; none made; proposed below |

## Edges

- **South, D1 (installed):** the crossing at x 64 (D1's road 1,536 at its (64, 19); D6's arrival (64, 105) facing
  north). D6's y 109 row repeats D1's installed y 19 row cell for cell (the sketch carries it as height points every
  3 cells and every cell over the road and the Sardaj pool; `d6/edge_d1.json`: difference 0 on every span). D1's
  Sardaj spring pool (832, x 81-87) lies on the border: D6's peaks drop to it in a cliff (cliffs[1]). D6's south rim
  strip pictures D1's vale (1,100-1,600) and its Gemstone foothills; D1's own north strip pictures D6's peaks.
- **East, D5 (planned beside this):** D6's x 109 column carries `edge_d5_d6.json` exactly for y 0-105 (the pass at
  1,696 over y 62-66; `d6/edge_d5.json`). **The corner** (109, 106-109) cannot match both the file (2,816-2,912) and
  D1's installed row (2,176 at (109, 109)): the plan blends to D1's (2,636, 2,440, 2,260, 2,176). An open question.
- **North and west: the world rim** (cliffs at y 24 and x 24); lava falls over it at (44, 24) and (24, 51).

## Double doors and texture fit (the user's rules of 2026-11-20, for L3/L4)

Two leaves with mirrored wing pictures, opening apart: **Castle Alamar's gate** (teal steel, the Ancient kit's
`swdoora` pair or a new pair if none suits); **Necropolis's gate** (iron-bound: MM7 `chb1dl`/`chb1dr` or the towers
kit's `hkm1dl`/`hkm1dr`); **the guild's and the temple's doors** (MM8 `t09a03a`/`t09a03b`); **DD-21's crypt stair**
(grilles, MM8 `gkp103a`/`gkp103b`). The pods' hatches are single round hatches (one leaf, the Lincoln's `a2c`). DD-10C's
adit is an open timbered mouth (no leaves). Texture fit: Alamar's towers one lit window per storey face, `xaenergy`'s
conduit centred once per pylon face (u offset 64); the Necropolis gatehouse and towers one slit per storey; the
tombs' doors once per face.

## Textures (proposed, none made)

The kits cover nearly everything. Three proposals for L3, each with a reason (ODM cap 12):
- `xnpgate`: Necropolis's gatehouse crest (a skull under a closed eye), once over the gate: the town's sign.
- `xnpbook`: a lectern's open black book (picture) for the Books of the Dead: no shipped book-on-lectern face reads.
- `xcrust`: cooled black lava crust (tile, 128): the crust round the hatch after `m28.lava_cooled`, if A1 swaps the
  face (else MU-2's `ground_crust` as a BModel).

## MU-4 concepts

Two `codex exec` calls (`d6_concepts.py`), one per view; raw returns, prompts and logs in
`level_generation/xeen_art/phase5/d6/raw/`.

- **Arrival** from Griffin Pass (64, 96) looking north: the road down to Ash Fork, Corak's lake and pod right of
  centre (about 15,400), Castle Alamar left of centre on its mesa ringed by lava (about 26,500), the lava falls at the
  rim, the Ancient field's metal at the right. Against the plan: the painting brings the castle nearer and gives it
  grey Gothic stone; it lines the energy pylons along the road far in front of the castle (the plan has four on the
  approach ramp); L3 keeps the plan's distances and the Ancient kit's teal steel.
- **Signature** from the lake's east shore by the Necropolis road (82, 72), about 60 degrees, looking west: the pod
  nose-up left of centre (about 5,700), its hatch toward the shore, Castle Alamar's lit walls and energy fields beyond
  the moat right of centre (about 20,700), ash in the air. At L4 the castle must read at that distance (lit windows,
  fields), as D-36 asked of Blackfang; never move it nearer. Against the plan: the painting puts the castle at about
  half its distance and in grey stone, sets the islet's lamp beside the pod, and hides the moat behind the far shore;
  the pod's scorched hull, the round hatch toward the shore and the fields on the ramp read as planned.

## Quest hooks placed

m25.flight (Ambrose, Griffin Pass), m29.pod_door (the hatch; D-47 `arrival: entrance:d6_hatch`), m33.castle_door
(Alamar's gate), m39.depths_door (the ruin's stair, after m33.done), obelisks.d6 (Obelisk Knoll); A4's people:
Ambrose 5512 (camp), Master Morbius 5506 (the Necromancers' House, Q-D23), the Necropolis staff 5501-5511 in their
houses; DD-10C's `exit:d6_adit` (the adit; its return point at L3).

## Requests (via the orchestrator)

- A2: map_stats row 9113 (slots above); two placed barbarian tiers (Barbarian Archer 44, Archer Chief 50; 11104,
  11105; until then the sketch's actors carry 11102 for validation only); a lava-dweller row, or confirm Lesser
  Elemental 55 / Elemental 62 as the stand-in; the Act V recount (73.4k); the Books of the Dead in the ledger.
- A3: a Necropolis gate hook (item 12336, a refusal line); the skull's story, the books' text, the zone sign's
  warning and Sheltem's sealed-hatch line; three genie-lamp hooks (Q-D27 has no hooks yet); the robots' markers off
  after m33.done (or a refill rule); the archers' camp burn hook if wanted.
- A4: Freeda the Mountaineer (a teacher row; her camp at (100, 69)); confirm Ambrose at Griffin Pass on the south.
- A7/A8: DD-16's arrival is settled (D-47); DD-17's arrival and refusal return, DD-21's stair foot, DD-10C's
  `D6_ARRIVAL` (A6 measures the D6 sides at L3).
- S: a griffin figure for Ambrose's camp (MM7 griffin, placed, not counted); the pods' outer hulls and Alamar's whole
  and ruin exteriors only if they are not BModels; the lava-fall decoration preset shared with X7.
- A1: the cooled crust at the hatch: a BModel raised over the lava by qbit is the plan's default; a lava area's tile
  swap by qbit if A1 prefers.

## Open questions

In the board (`level_generation/xeen_art/phase5/d6/board_d6.png`) and the report's DECIDE list: Griffin Pass on the
south; the lava dwellers; the archers' levels; the cooled crust; the ruin's stair; the D5 corner; Lucio on D6; 42
spawn markers.

## D-49 and D-50 applied (A6 sub-agent, 2026-11-21)

`d6_brief.py` carries the decider's changes; where the text above differs, these lines win (and D-49 itself).

- No Freeda (change 1): her camp at (100, 69) is an empty climbers' camp (dressing, no click, no NPC).
- The D5 edge (Q6): D6's x 109 column carries `edge_d5_d6.json` cell for cell for y 0-109 (y 106-109 = 2,636 /
  2,440 / 2,260 / 2,176, D1's installed corner); the y 109 row still repeats D1's installed y 19 row.
- **Four-map corner:** the installed D1 and D2 disagree at the four-map point (2,176 against 2,496); there is no
  crossing there; it is left as is.
- DD-10C's adit (change 3) and the travel pyramid (D-50 Q9): keep-clear areas, no spawn marker within 2,000 of
  `entrance:dd10c_adit` (46, 97) or `entrance:xd17_pyramid` (54, 62); the hatch's way out 2,500 clear of every lava
  dweller's home and radius (change 4; the south-west Elemental moved to (65, 72)), measured at L3.
- POIs 28 with the D-50 travel pyramid (cap 28). **Spacing:** the median spacing of about 4,050 is accepted (as X7's
  3,280): 22-28 POIs on this much land cannot reach a 1,300-2,600 median.
- **42 spawn markers** (Q8) against MAPS's 45-70: the two placed camps (14 elementals, 12 archers) do the markers' work;
  110 at load.
- Rows: archers 11104 x9 / 11105 x3, the Tethered Griffin 11913 beside Ambrose (both hidden after m25.done), the lava
  dwellers 11620 x11 / 11621 x3. Music 11 (A2).
- Necropolis runs `town_feel --small` (change 8); its exception lines go in L4's NOTES.
