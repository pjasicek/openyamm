# D4 Lakeside and Blackfang: L1 plan (MU-3, MU-4) for the phase 4 review

A6, 2026-11-20. A plan only: there is no geometry. Nothing is built until a decider has approved the board. The three
YAML files here are written by `level_generation/xeen_art/phase4/d4_brief.py` (edit the script, then run it, `oymap fmt`
and `oymap validate devdocs/xeen/briefs/d4/L1 --assets assets_dev`: no issues). Drawings, measures and the board:
`level_generation/xeen_art/phase4/` (`d4_render.py`, `d4_concepts.py`, `board_d4.py`; outputs in `d4/`).

## What the plan holds

- **Centre: Octopod Lake** (level 1,056, about 980 cells). Shallows and reeds by the shores, deep water in a west and an
  east basin. The **Isle of Lost Souls** (cells 67-78, 64-74) lies 5 cells off Lakeside's jetty: a landing jetty with
  the source's sign, dead trees and graves, a ruined round tower over **DD-12's door** (two leaves, `lost_souls_key`,
  M20; D-12.1: the Isle's only gate). Two skerries in the deep basins carry lures (a drowned smuggler's strongbox, a
  genie lamp), reached only by water walking or flight past the octopods. The lake drains east in a short race and
  falls over the east rim at (104, 67), the **Octopod Falls** (D-23: water rises and falls inside the map).
- **South shore: Lakeside** (cells 60-86, 82-97, 1,090-1,200). A4's d4.yml in full: the guild 4651 on the square's
  west side (t09 ashlar, two storeys, its carved double door east onto the square: q-d22.guild_door, the riddle; right
  answer: the guild and its back stair to DD-20; wrong: the trapdoor to DD-20's sewer half), the smithy 4653 east, the
  tavern 4652 and the temple 4654 south, Lakeside Yachts 4655 on the waterfront with the ferry jetty at x 72 (route 420
  daily from day one, Lucio's route 426 after m30.done), ten houses 4657-4666 on the waterfront and the edges, the
  mirror 4656 and Naomi (5318) in the stocks on the square facing the guild's door. Skiff's beached boat lies on the
  shingle east of his Boathouse with the source's events (aaze0033:18, 21, 22: the sign, "Search the boat?", the boat
  sinks with its treasure). A grated shaft by the jetty's foot is the source's "Climb down to the sewer?" (aaze0033:3).
  No walls; timber gate arches on the two roads. Darkside town kit (MU-5): t06 boulder stone under mossy slate on the
  waterfront, t09 ashlar under xlslate for the guild and the temple.
- **North shore: Castle Blackfang** on a black crag (cells 77-98, 38-60, top 3,100) whose south face drops into the
  lake. The castle sits on the top (about 8 x 6.5 cells, four towers and a keep) in a storm of bats. The **gate** is a
  squat gatehouse at the crag's west foot on the north shore (78, 53), walkable along the north-shore track:
  m25.blackfang_gate, "There seems to be no way in." (aaze0021:3). It never opens; DD-14 is entered by the griffin from
  D6 (m25.flight). Towers kit, Darkside: hkm3 slate-blue coursed stone under the skull frieze, hkm2 black rubble,
  xtslate cones.
- **North: the Snow River uplands.** A snowfield along the north rim; the Snow Springs' tarn (61, 30) at 2,270; the
  Snow River's rapids down a rocky cut to the lake's north-west bay (59, 56) at 1,056 (D-23); a timber bridge at
  (60, 52) where the west-shore track, the north-shore track and the snow track meet. Vulture rocs over the uplands
  and the rim corner behind the crag, where the Fountain of Great Resilience (the source's F1 fountain) stands by the
  rim at (100, 38).
- **North-west: Magic Mountain** (to 4,100 at (30, 36); its north face falls over the rim). Xanthus and Slibo's camp
  on a shelf at 2,300 (tents, a fire, the Fountain of Great Magic: +SP, aaze0017:4-6; Slibo 5317); the Wizard's Seat
  ledge with a genie lamp; the gargoyles' perches and **DD-23's cave mouth** (46, 42) under them (q-d15.lair_door; an
  open cave mouth, no door leaves); **Ector's woodpile** (48, 51) in the woodcutters' clearing on the south-east slope
  (q-d21.woodpile).
- **West: the Forest of Peril** (1,200-1,700): Leafpoint's grove (42, 61), Ector's cabin (34, 72), two animal traps
  (aaze0017:10, aaze0018:17), an old hunters' hide; the desert road from D5 at y 80 runs through it to Lakeside.
- **South: the desert edge** (D3's dunes running on, 1,300-2,000): vulture rocs, the Witches' Circle by the forest
  road (placed coven, the three recipe skulls aaze0033:12-14, the coven's offering chest), a lost Sandcaster wagon,
  Gallows Knoll with the coven's gibbet above Lakeside's south road; **Lakeside Brow** (2,300) where the D3 road tops
  the heath and the lake country opens below.
- **East: the east shore and the Rimward crags.** The shore path from Well Fork (the Fountain of Magic Resistance,
  aaze0022:2-4, the map's permanent device) past the five-stone cairn (q-c24.cairn) to **Mirabeth Point** (the mermaid's
  statue and the source's sign, aaze0022:1); the Rimward crags (D3's Wrath shoulder running on north) with rocs and a
  fallen roc-hunter; the falls' lip with a fisherman's chest.

## Figures (`d4_render.py`, `level_generation/xeen_art/phase4/d4/measure.json`)

| Figure | Target (MAPS D4, §0 checklist) | Plan |
| --- | --- | --- |
| Hostiles at load | 120 | 119.5: markers 47 (gargoyles 13 x 2.5, rocs 34 x 2 at [1, 3]) = 100.5; placed 19 (14 coven witches, 5 octopods) |
| Kill XP per member | 43.0k (±15 %) | 43.7k (+2 %): MM7's tier odds (Dif 1 90/8/2, Dif 2 70/20/10), XP = L(L+10) |
| Monster band | A 26-35, C 50; octopods 60 | gargoyles 30/38/45 (Dif 2), rocs 30/38/48 (Dif 1), coven 32/40/50 (placed), Octopod 50, Great Octopod 60 |
| Encounter areas (4,096²) | 3-8 of 6-30; at most 3 camps | gargoyles 10.7, uplands rocs 14.1, desert-edge rocs 9.8, Rimward rocs 4.2; camps: Witches' Circle 1.1, reed witches 0.7; octopods in the two deep basins (water) |
| Quiet land | at least 1/3 | 59 % of the land in the box (the lake not counted) |
| POIs (D-20 census: chained merge within 400; service doors, mirror, gates, dungeon doors in; residences, talking NPCs, hazards, landmarks out) | lake band 30-35 | 35 (named 13 + generic 22); spacing median 4,100 |
| Outdoor chests | 4-10, a reason each | 10 |
| Dungeon entrances | 3-6 | 4 doors to 3 dungeons (DD-12, DD-20 x2, DD-23) + Blackfang's sealed gate (DD-14 by griffin) |
| Obelisk; devices | 1; >= 4 kinds, one permanent | 1 (Gull Knoll by Lakeside, A3's "Obelisk by Lakeside"); fountains x3, the magic-resistance well (permanent +5 Mind/Body), woodpile, cairn, statue, cauldron, recipe skulls, genie lamps x2 |
| Relief inside the box | >= 2,500 | 1,097-4,187 (3,090) on land |
| First fight, edge arrivals | 2,000-6,000 | from D3 (88, 105): 2,560 (Rimward rocs); from D5 (23, 80): 4,600 (desert-edge rocs) |
| Town arrivals (D-15) | buffer 2,500 | square 8,000; dock 6,800; Isle landing 4,600; nearest fight to a Lakeside door 2,700 (the Tannery) |
| 6,000 rule; wild land (D-11.5) | none over 6,000; <= 0.16 | farthest 4,830 (forest's north-west at [19, 56]); 0.07 |
| Roads | 1-4 % | 1.2 % roads + 1.5 % lanes |
| Houses drawn / d4.yml | 4651-4666 | 15 doors + the mirror |
| Textures | phase 4 outdoor cap | darkside_town, towers kits and MU-2's D4 row only; no new textures named |

## Edges

- **South, D3 (D-28 (6)):** the crossing at x 88 (D3's road bed 1,760 at its y 19; D4's south arrival (88, 105)). D4's
  south rim repeats D3's north-edge spans and heights cell for cell: [0, 24] ridge 2,600-3,400, [24, 82] ridge
  1,500-2,000, [82, 94] level 1,750, [94, 104] ridge 1,900-2,400, [104, 128] level 0. Inside the square the plan's
  height points along y 104-108 follow D3's installed border row (y 19 of `xeen_d3.odm`): 1,200-1,300 at x 19-30,
  1,350-1,600 at x 30-60, 1,600-1,760 at x 60-88, 1,880-1,980 at x 94-100. Measured on the drawing's land model
  (`d4/edge_d3.json`): mean difference on the border row 195 at x 24-82, 103 at the road span, 114 at x 94-104. The
  studio's build sets the road bed (the rim's level 1,750, the point 1,760 at (88, 108)).
- **West, D5 (not planned; A6, phase 5):** proposed crossing y 80, a level valley at 1,500 (west rim [72, 88]); the
  rest of the west rim: Magic Mountain's flank, forested hills, dunes, the last Gemstone crags at the south-west corner.
- **North and east: the world rim** (cliffs at y 24 and x 104). The bright face's glow above the north-east rim is
  concept art only; no plan element depends on it (a horizon-ring texture is a separate engine question).

## Double doors and texture fit (the user's rules of 2026-11-20, for L3/L4)

Build these as **two leaves** with mirrored wing pictures, opening apart:

- **Castle Blackfang's gate** in the gatehouse at the crag's foot (never opens, but it is a double gate): an arched
  oak or iron pair, e.g. MM7 `chb1dl`/`chb1dr`, or the Darkside towers' `hkm1dl`/`hkm1dr` if its width suits.
- **The Lakeside Guild's doors** (the coven's front, DD-20's way in): MM8 `t09a03a`/`t09a03b`, the Darkside kit's carved
  double door halves.
- **DD-12's door** in the Isle's ruined tower: `hkm2d1`/`hkm2d2` or `hkm1dl`/`hkm1dr`.
- **DD-20's sewer shaft** is a grate, not a door; DD-20's hall doors inside are A8's.
- **DD-23** is an open cave mouth (no leaves); if A7/A8 give it a door, two leaves.
- The temple (4654, nailed-shut doors) if it is drawn as a wide double door: two leaves.

Texture fit: Blackfang's towers and keep (one window per storey, `hkm3elw`/`hkm2bw` placed once per storey face, the
skull frieze only along its seamless axis), the guild's two storeys (one t09 window per storey and bay), the temple,
the Isle's tower (one window or slit per storey), and the gatehouse (one arrow slit per storey).

## MU-4 concepts

Two `codex exec` calls (`d4_concepts.py`), one per view; raw returns, prompts and logs in
`level_generation/xeen_art/phase4/d4/raw/`.

- **Arrival** from Lakeside Brow (88, 102) looking north: the road down to Lakeside at the left, the lake opening up
  with the Isle, Castle Blackfang on its crag across the water, the falls at the east rim, Magic Mountain far left.
- **Signature** from the ferry jetty's end (72, 80), about 60 degrees, looking north-north-east: the Isle with its
  ruined tower ahead-left, Castle Blackfang on its crag in the storm of bats beyond, its sealed gatehouse at the foot.

## Quest hooks placed

m25.blackfang_gate (the gatehouse), obelisks.d4 (Gull Knoll), q-c24.cairn (east shore), q-d15.lair_door (DD-23),
q-d21.woodpile (the clearing), q-d22.guild_door / guild_right / guild_wrong (the guild's door); A4's people: Naomi
5318 (stocks), Slibo 5317 (camp), Leafpoint 5319 (grove; see the open question), Ector 5320 (cabin).

## Requests (via the orchestrator)

- A4: a line for the ferry's return at the Isle's jetty ("Back to Lakeside?", the mate of Ferris Gull), or say the
  ferry is one-way (then Town Portal, the mirror or water walking bring the party back).
- A3: a hook to hide the two placed coven groups at load once q-d22.done (and A2's relation: peaceful to members,
  q-d22.joined), unless the decider picks otherwise.
- A2: the octopods as swimmers that never leave deep water (MM9 AI movement `swim` in `modifiers.yml`), and the map's
  row 9111 with the slots above.
- A8: DD-12's, DD-20's (guild stair, trapdoor, shaft) and DD-23's inside arrival points when their projects exist.

## Open questions

In the board (`level_generation/xeen_art/phase4/d4/board_d4.png`) and the report's DECIDE list.
