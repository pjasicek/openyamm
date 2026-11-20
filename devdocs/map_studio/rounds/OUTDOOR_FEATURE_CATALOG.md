# Outdoor feature catalog: what the 42 shipped outdoor maps need from the studio

Written 2026-11-13 from the ten surveyors' `output/studio_survey/*/SURVEY.md` (38 maps) and
`output/studio_survey/rebuilt/SURVEY.md` (New Sorpigal, Harmondale, Ravenshore, Shadowspire). Their brief:
`output/studio_survey/BRIEF.md`. Pictures and exports are in each map's folder there; this catalog names the
folder (`<map>` or `<map>.odm`) and the surveyor's picture where one shows the thing best.

Checked against `openyamm-studio/schema/sketch.schema.json` (the working tree, with outdoor batch ten's `fence` and
`waterfall` kinds) and `oymap schema atmosphere`, and against `rounds/NEXT_CODE_BATCH.md`. Merged already (batches
eight and nine): `tile_sets`, `mist`, `sky_theme`, `same_event_as`, `signs[].offset`, `plinth`, well `frame`.
Finishing (batch ten): `kind: fence`, battlements on `kind: wall`, `kind: waterfall`, `doors[].same_event_as`, porch
`floor`, posts on chosen walls, the outdoor coplanar check.

Class: **b** a studio word (sketch shape and lowering), **c** engine work. "Covered" says whether a merged word, batch
ten or a NEXT_CODE_BATCH item already takes it.

Map names: MM6 outa1-3, outb1-3, outc1-3, outd1-3, oute1-3 (oute3 New Sorpigal); MM7 7out01-06, 7out13, 7out15,
out09-12, out14 (7out02 Harmondale); MM8 out01-08, out13, out15, elema, elemf, elemw, pbp (out02 Ravenshore, out06
Shadowspire).

## 1. Ranked words

Ranked by the number of distinct maps that need the word (class b at one or more places), then by how much a player
sees it. "Also" lists maps where a surveyor judged the place sayable today but the word would say it better.

| # | Word (merged family) | Class | Maps | Which | Seen in play | Covered |
|---|---|---|---|---|---|---|
| 1 | `events[].trigger: leave` outdoors | b | 16 | out01-08, out13, out15, elema, elemf, elemw, pbp, 7out03, 7out06 | not seen; story rewards (Heart of Fire 100000 xp), griffin checks | no (indoor item 5 has the same word) |
| 2 | `fountain.outline` (+ `sides: 3`, `pillar_shape: box`, `tiers`, running water on the pillar; trough = rectangle) | b | 15 | outa1, outa2, outa3, outb2, outb3, outc1, outc3, outd1, outd2, outd3, oute1, oute2, 7out03, out02, out06 | town squares, clicked | no (round four "fountains and wells" only in general) |
| 3 | `kind: cave_mouth` (mound, `skin: ground`, `rock_shell`, cave mounds, free-standing barrow) | b | 15 | 7out01, 7out02, 7out04, 7out05, 7out06, 7out13, out02, out04, out05, out06, out07, out08, out10, out12, out13; related out03 (wasp nest), out14 (grass hood, a) | every dungeon way in | NEXT item 14 (not merged) |
| 4 | Arched heads: `arch: round\|pointed` on doors, doorways, windows, gates | b | 10 | out04, out05, out06, out10, out12, outc3, outd2, oute2, elemw, 7out02 | dungeon fronts, belfries | NEXT items 8 (cave mouth arch) and 13 (pointed arches), as one word |
| 5 | Invisible faces: `invisible: true` (step plate, lid), `kind: barrier`, bridge `kerb_invisible`, `ethereal` | b | 10 | 7out01, 7out02, 7out04, 7out05, outa2, outa3, outb1, outc3, outd1, outd3 | not seen (that is the point); traps, ambushes, teleports, the tutorial | no (batch ten's fence already writes an undrawn barrier: reuse) |
| 6 | `bridge.arches` (level deck on arches, viaducts, solid arch spans; sag with `rise` below 0) | b | 10 (+1) | 7out01, 7out03, 7out04, out09, outa1, outb1, outc1, outc2, outd1, outd3; sag: 7out02 | high: crossings on main roads | NEXT item 4 "a bridge that arches" (one hump only today) |
| 7 | `atmosphere.flags` (+ outdoor `ceiling`, `atmosphere.footsteps[]`) | b | 10 | flags: 7out15, out15, elema, elemf, elemw, out04; footsteps: outa2, outa3, outb3, out04, out06 | whole map (underwater, sky map, red fog) | no |
| 8 | `parts[].batter` (per-side lean in map units, doors upright in the slope; `buttresses`) | b | 9 | out04, out08, out14, 7out05, elemf, outc1, outb2, outd1, out02 | castles and dungeon fronts | NEXT item 11 for `kind: wall` runs; parts' `taper` says the plain case today |
| 9 | Scatter extras: `scatter[].group` (season swaps), `event`, `on: water`, `height` | b | 8 | group: 7out02, 7out03, 7out04, out11, out14; event: out09; water: oute1; height: elema | whole forests change by season | no |
| 10 | `roof: dome` (and a domed cap with overhang) | b | 7 | out02, elemf, 7out04, 7out15, out09, out10, pbp | landmarks | no |
| 11 | `kind: portal` (ring gate on a dais with a liquid membrane) | b | 7 | elema, elemf, elemw, out01, out04, out07, out08; pbp's crystal prisons are another form | each plane's way home | no (model import works) |
| 12 | `events[].when_flying` (levitate trap: the dragon towers) | b | 7 | oute2, oute3, outb2, outc1, outc2, outd1, 7out01 | fireballs at a flying party | no |
| 13 | Arcade, `portico`, round columns (`posts_shape: round`, pediment; `doorway.roof: gable`) | b | 7 | oute3, 7out04, outc3, outb1, out09, out11, oute2 | temples, keep loggia | NEXT item 4 "an arcade" |
| 14 | Roof to the ground: `tent`, A-frame, cone hut | b | 7 | 7out02, 7out03, 7out04, out03, out05, out14, elemf | camps, huts | NEXT item 9 (A-frame only) |
| 15 | `heights.spires[]` / `heights.peaks[]` (one-node needles, fields of them) | b | 6 | out06, out10, out14, elemw, out15, pbp | skylines | NEXT item 13 "a sheer rock column" |
| 16 | `ruin` (ragged wall tops, bare roof frame; wall pieces of their own height) | b | 5 | out04, outa1, out09, outd1, 7out02 | burnt villages, ruined circles | no |
| 17 | Raised decks: `kind: walkway` (polyline deck on posts), deck outline, `stilts` | b | 5 | 7out04, out11, 7out13, out14, outd3 | Pierpont, Barrow Downs walkways | NEXT item 13 (non-convex outlines) in part |
| 18 | Stepped masses: building `steps`, `platform.tiers`, stepped plinth | b | 5 | out01, outb3, 7out06, out04, out09 | pyramids, teleport pads | no |
| 19 | Built against a slope: `against: slope`, ground skirt on walls | b | 5 | out03, out06, out10, out11, out13 | castle fronts in cliffs | no |
| 20 | Liquid faces on parts: `textures.<role>: {liquid, flow}` | b | 5 | elemf, outa3, out02, out06, elemw | lava falls, fountain pillars | no (indoor has `liquid`) |
| 21 | `kind: hatch` (wedge lid or pit rim, into a map) | b | 4 | 7out05, out04, out08, out02 | dungeon ways in | NEXT item 8 "a hole in a part" in part |
| 22 | `heights.cuts[]` (pockets and trenches, nested terraces with `ramps`) | b | 4 | outb2, outc1, outc2, outd3 | dungeon slots, the obelisk pit | no |
| 23 | Door dressing: `doors[].leaves: 2`, `doors[].hood`, `doors[].frame` (nested), door picture on a platform face | b | 4 | oute3, out05, outc1, out04 | dungeon doors | NEXT item 8 "recessed porch doors", "a door canopy" in part |
| 24 | `platform.sides` (round or n-gon platform) | b | 3 | out01, pbp, 7out06 | pads, the giant shield | no |
| 25 | `ridges[].closed` (a crater rim) | b | 3 | oute3, out01, outa3 | crater obelisks | no |
| 26 | `stone_ring` / `trilithon` | b | 3 | out09, 7out13, out14 | quest stones | no |
| 27 | `kind: arch` free-standing (with `ribs`), walkway end frames | b | 4 | 7out06, elemf, elemw, out11 | teleporter, coral shrine | no |
| 28 | `culvert` (pipe or covered channel mouth with outflow; stepped cascade) | b | 3 | 7out03, out14, 7out01 | sewer ways in | no (batch ten waterfall is the sheet only) |
| 29 | Model import face roles: door faces, hint on the rest, one event over several models | b | 3 | out02, elemw, out13 | ships, wreck homes | NEXT item 5 |
| 30 | `lean` / `tilt` on parts and platforms | b | 3 | out02, out07, 7out15 | wrecks, pylons | no (indoor item 6 has leaning walls) |
| 31 | Crown and horn ornaments: `crown`, `sweep` | b | 2 | outa1, outa3 (7out15's crown is the overhang case) | spires | no |
| 32 | `kind: hive` | b | 2 | out12, out03 | model import says it | no, low |
| 33 | One-map words | b | 1 each | `hang_between` (oute3), `kind: plate` (outc2), `crate.stack` (out08), `rock` (pbp), `wall.top: follow` (outc1), `floating` with rock base (elema), `sequence` puzzle and a `sound` effect (7out03), a `movie` effect (outb2) | — | no |

Already sayable or batch ten (surveyors' "b" that is not new): fences (outb2 circus, out08 pens, oute3), battlements on
walls (7out03, 7out06, out01, out05, out08, outc1, outd3), waterfall (out03 Alvar; 7out01's stepped channel is the
culvert word), posts on chosen walls (7out02 stable), ships and wagons as `kind: model` (19 maps), open pavilion
shrines (NEXT item 8: 7out04, 7out05, out12, oute1, outd1), more than three ground kinds (NEXT item 11: outb2).

## 2. Definitions (one per word)

Each: the sketch shape (best-specified proposal), the lowering, how the originals build it.

1. **`events[].trigger: leave`.** An event that runs when the party leaves the map (`effects`, `condition`, `lua` as
   any event). Lowering: the event's number goes into the script's `onLeave` list (`SetMapMetadata`). Originals:
   `onLeave` filled in 16 outdoor scripts (elemf/elemw event 6: the Heart of Fire/Water; 7out03 event 2: the griffin
   kill check). Same word as indoor item 5.
2. **`fountain.outline`.** `outline`: the basin's plan as a polygon in map units about `at` (a rectangle by `size:
   [w, d]`), instead of `sides`/`radius`; `sides: 3` allowed; `rim` height and thickness; `steps: [[in, up], ...]` for a
   basin stepping in (the HF family's 96/160/192/208 rings); `tiers` for a lower wide step under the basin;
   `pillar: 0` or `pillar_shape: box` with `flow: down` (water running down its faces). Lowering: rim walls in and out
   along the outline, rim tops, one water face per convex piece (fluid bit, animated water). Originals: MM6 `HF*`
   (58 faces: 17 rim tops, 6 water; every MM6 map), outd1 `pond` (640 x 128, 17 faces), oute2 `Pond`/`PondE`
   (17-18), 7out03 `Plaza2_N_2/3` trough, MM8 `Fountain` (96 faces, octagonal basin on a step, square middle block with
   water falling; out02, out06).
3. **`kind: cave_mouth`.** As NEXT item 14 (`at`, `turn`, `size`, `crest`, mouth `width/height/depth`, arch `sides`,
   `textures` shell = ground tile or rock, door `solid01`, `into`/`hint`, `roughness`/`seed`), plus what the survey
   adds: `free: true` (a mound standing on level land, closed all round: out07 d43, out08 d26, 7out06 red4, out13
   d34/d47), `mouth.form: arch | door` (open dark arch, or a flat front with a carved door slab: out08 Crypt of Korbu,
   7out06's `Red` frame), and a water strip over the shell (7out01). Lowering as item 14. Originals: 40-60 large
   triangles in the ground tile (`7dirttyl`, `Grastyl`, `wastetile`, `7snow`, `PlnTyl`), no floor or back; e.g.
   `DragonCave_E*` 164 faces, `tulCaveEntrance` 64 (52 ground), `ThePit_S` 54, `red4` 40, `DC_S*` 151, `d43out_E`
   63+63, `d26entranceAS/BS` 42+64, `d34entrance_N` 60, `d47out_W` 63, `d48ent_S` 50+62, `d17entrance` 40+56,
   `Out12Tunnel` 64, `Maze*` 136.
4. **`arch: round | pointed`** on `doors[]`, `doorway`, window bays and `gates[]`: the opening's head as a half n-gon
   (`sides` 4-8) or two arcs meeting. Lowering: the head's faces cut from the wall panel, jambs upright. Originals:
   out04 `D14_N`, outc3 `DunEntC3` (4 sloped head faces), elemw `ElemWhouse2`, oute2 `archesN` (59 faces), 7out02
   `Temple3_N` belfry.
5. **Invisible faces.** `invisible: true` on `platform` (only its top face, attribute 0x2000; with `trigger: step` also
   0x04000000: a pressure plate nobody sees) and a lid (`platform` with `invisible` at a height); `kind: barrier`:
   `line`, `height`, `bottom` (one invisible upright face per segment, blocks, no event); `kerb_invisible: <height>`
   on `bridge` (an invisible upright face each side instead of a kerb); `ethereal: true` (faces drawn, walked through,
   FACE_ETHEREAL 0x20000000). Originals: 7out01 `Tut02*` (17 one-face 512 quads), 7out05 `512plate` x4,
   `Invis1024x512` x2, 7out04 `512invis`, outa2 `InvisN/S*` + `InvistopN*` (12 one-face models), outb1 `TewS` faces and
   `DunEntB1` (4 ethereal), outc3 `Invis` (896 x 384) and 13 bridges with 2 invisible faces each, outd1 `DruDi_*` (26
   one-face models, 19 plates), outd3 `Bridge Trigger`.
6. **`bridge.arches`.** `arches: {count, rise, form: round | segment, pier_width}`: a level (or `rise`) deck carried on
   `count` arched openings, piers standing to the land or water below; `count: 1` is the solid arched span the MM6
   `bridge2*`/`volc_bridge` family draws. `rise` below zero sags (with `piers: 0`, `railing: rope`, `towers: [w, d, h]`
   at the ends: 7out02 `NewOut2Bridge_`). Lowering: deck slab and kerbs; per arch two pier faces and a soffit of n
   segments; spandrel walls flush with the kerbs. Originals: 7out04 `LongTest_E*` (5 models, 56 faces, 7 arches each),
   7out03 `Bridge_E_1` (43 faces, 1280-high piers), out09 `Out9Bridgeprt*` (107), 7out01 `Bridge1_S` (56), MM6
   `bridge2ns/ew`, `Bridge2`, `volc_bridge`, `bridgeN` (50-62 faces, 18 sloping).
7. **`atmosphere.flags`** `{underwater, no_terrain, always_foggy, red_fog, always_dark, always_light}`, `ceiling`
   (outdoor, elemw's 2000) and `footsteps: [{tile, walk, run}]`. Lowering: the scene's environment flags (the build
   writes them all false today, `core/OutdoorBuild.cpp` ~232), its ceiling, its `footstep_sound_overrides`. Originals
   (scene files): underwater 7out15_1, elemw, out15; no_terrain and always_light elema; always_foggy 7out15, elemf,
   elemw, out15, out04_1; red_fog elemf; always_dark 7out15; footsteps outa2_1, outa3_1, outb3_1, out04_1, out06_1.
   Open question for elema: what the hidden height field must hold (party collision, fall height).
8. **`parts[].batter`** (map units the walls draw in from foot to top; `batter_sides` for some sides only; negative
   flares) and **`buttresses`** (`count` per wall, `width`, `depth`, `height`, tapered top; arched between when asked).
   Differs from `taper` (exists on parts, scales about the middle, plain faces without bays): doors and windows stay
   upright, set into the slope. Originals: out04 `D14_N` (64 faces), out08 `08bar_fort_A..H` towers (1152 square, about
   200 in), out14 `Titan_W*`, 7out05 `WT_*` foot, elemf War Camp (45 degrees), outc1 `Wc_*` bastions (20 slopes), outb2
   `D17` wedge, outd1 `D13S` frame, out02 `Out02Temple_N` round tower.
9. **Scatter extras.** `group: n` (the decoration group `set_sprite` and season load events address: MM7's groups
   5/6/7/10), `to: none` in `set_sprite`; `event: n` (every decoration of the entry clickable with one event: out09's 69
   flowers); `on: water` (buoys, sea rocks on a water body); `height: [lo, hi]` above the land (elema's 428 clouds).
   Originals: `SetSprite(5..10, 1, ...)` 9 calls each in 7out02/03/04, out11, out14.
10. **`roof: dome`** on round and box parts: `rings` (3-6) of a quarter circle, `squash`, `overhang` (a cap wider than
    the shaft: out02 d28's mushroom cap). Lowering: rings of `sides` quads to a point. Originals: 7out15 `CDprt*` (166
    faces), elemf `d29entrance*` halls, 7out04 `ECastle*`, out09 `TS*` rotunda, out10 `TF_N*`, pbp `14_helmet_AN/BN`
    (61+42, a frustum with a dome top).
11. **`kind: portal`.** `at`, `turn`, `radius` (192), `ring` (32), `sides` (8), `dais: [radius, height]` or stepped
    base `steps`, `frame` texture, `membrane` texture with `flow` (none/up/down), event on every face (`into`,
    travel). Lowering: a ring of box segments round a two-sided disc, dais rings. Originals: `gw_fire_N/W`,
    `gw_water_N/E`, `gw_air_N/S`, `gw_earth_N`: 58 faces each (gn_mtl01-03; membrane LavTyl, hWTRTYL, PLANSKY1).
    pbp's elemental prisons (`*prison_a/b/c`, three crossed slabs floating) would be `form: crystal`; model import is
    honest for them.
12. **`events[].when_flying: true`** with `trigger: timer`: the event runs only while the party flies. Lowering: its
    number into `levitateTrapEvents` (read by `ScriptedEventProgram.cpp`). Originals: 7 outdoor scripts have the list
    (event 209/210 Fireball from `AntiFly*`, until the Dragon Tower qbit). Surveyors of outb2/outc1/outc2 wrote it as a
    `lua` IsFlying condition: that runs the timer always and differs from the original.
13. **Arcade / portico / round columns.** `posts_shape: round` (`sides`, base and capital rings) on an open part;
    `porches[].form: portico` (`columns: {count, radius}`, flat ceiling, entablature band, `pediment: gable`);
    `arcade: {bays, arch}` on a wall of a part (open bays under arches). `doorway.roof: gable` is the portico over a
    door in a slope (oute3's Abandoned Temple). Originals: outb1 `PT07BackW/FrontW` (60+64), out09 `TS*` rotunda,
    7out04 Navan (7 arches), oute3 `SmKeepFrnt` loggia, outc3 `CatwalkE` gallery (61), out11 `H*` portico, oute2
    `archesN`.
14. **Roof to the ground.** `kind: tent`: `size`, ridge `height`, low `walls` (0-128), `open` end, `awning` on two
    posts, canvas/inner/pole textures (out05 `Tents5and6_E`, 64 faces). The A-frame (NEXT item 9) is the same with a
    door; `roof: cone` with `wall_height: 0` and a door cut in the slope is the round case (elemf `ElemFhouse1`, 74
    faces). Lowering: sloped quads, gable triangles (one open), awning, poles.
15. **`heights.spires[]`** (`at`, `height`, `radius` 1-2 nodes, sheer; neighbours untouched) and **`heights.peaks[]`**
    (a `polygon` filled with `count` peaks, height range, base radius range, profile, `seed`). Lowering: node heights,
    the cells marked too steep. Originals: terrain only (elemw: 438 tops over 2000; out10 steps of 8000 between nodes).
16. **`ruin`** on a building or part: `{height: [low, high], gaps, roof: none | frame, seed}`; on `kind: wall`
    `segments: [{to, height}]`. Lowering: bay panels cut at their own top, left-out bays, roof as bare trusses
    (`trim`), rubble optional. Originals: out04 `04ogre_burnt*` (9 models, 36-62 faces), outa1 `burnt*` + `tavburntW`
    (33 WOOD013 rafters), out09 `Broken House*` (7 models), outd1 `StoneH1` (62 faces, pieces 0-352 high).
17. **Raised decks.** `kind: walkway`: `line` with a height per point, `width`, `piers` every n and at bends,
    `ends: frame` (a timber gate frame with steps); a deck `outline` (non-convex) at `height` with posts; `stilts`
    on a plot (`height`, `count`, section) instead of a solid plinth. Originals: out11 `BP/BS/BC/BDC-*` (62 models,
    about 2900 faces), 7out04 `Dock*` (26 models), 7out13 `h_*_stilth*`, out14 `Shrine4_E`, outd3 `See'r BaseS` star
    deck.
18. **Stepped masses.** `steps: [[in, up], ...]` on a part or platform: level terraces with upright risers, the last
    ring takes the roof or a part. Originals: outb3 `pyramidbase` (58 faces, 25 up, 33 upright), out01 `d05entrance`,
    7out06 `Platformb*` (45 faces, three tiers, 16 pads), out04 `D13_N` cap, out09 stylobate.
19. **Built against a slope.** `against: slope` on a building (back wall left out, sides run into the land) and
    `skirt: ground` on a part (walls carried down to the land in the ground texture). Originals: out10 `TF_N*` (11
    models), `kFirGuild`/`kMagic_*` (`7dirttyl` skirts), out11 `D0E/D01E` (13 models), out03 `d12entrance`, out13
    `d32out_S*`, out06 d20out (the Lab).
20. **Liquid faces.** `textures.<role>: {name, liquid: lava | water, flow: up | down | left | right}`: writes the fluid
    bit and flow bits (0x2001a08, 0x4200110c ...). Originals: elemf `ElemFhouse2` lava falls, outa3 `baaS` (LAVATYL,
    0x110), MM8 `Fountain` pillar, elemw wreck faces.
21. **`kind: hatch`.** `form: wedge` (a sloping lid to `height` 192, mouth facing `turn`) or `pit` (a rim `size`,
    64 high, a dark shaft), `into`, lid in the ground's tile. Originals: out04 `CoFent_S/N` (24 faces), out08
    `d24entranceA` (13), 7out05 `SecondEntrance_S` (25), out02 `Vot` hatch.
22. **`heights.cuts[]`.** `polygon`, `floor`; outline nodes keep the land's height so the walls are one-node cliffs;
    `open` edges slope out; nested cuts with `ramps: [[from, to], ...]` graded across the steps make terraces (outd3's
    pit: 1856, 1248, 640, 0). Originals: terrain only (outb2 Wolf Lair trench, outc1 Shadow Guild, outc2 three slots).
23. **Door dressing.** `doors[].leaves: 2`, `doors[].hood` (the doorway's hood on a building door: outc1 `D15Base`),
    `doors[].frame: {steps, step, texture, portcullis}` (out05 `05dh_keep_N` third model, 22 faces), a door picture on
    one face of a platform (out04 `D13_N`).
24. **`platform.sides`** (n-gon or round platform, `radius`). Originals: out01 `01tel_nc*` (60 faces) and
    `gw_earth_N`, pbp `LargeShield_N` (34), 7out06 `heavenTele_S` pad.
25. **`ridges[].closed`**: a ring ridge (crater rim) with a point in the hollow. Terrain only.
26. **`stone_ring` / `trilithon`.** `count` trilithons on a circle (`radius`, stone `size`, `lintel`, `lean`), or
    one free-standing. Originals: out09 `CircleRocks_` (109) and `Stone_` (101), 7out13 `Stone_*`, out14 `Stone_`
    (40+61).
27. **`kind: arch`.** A curved beam from foot to foot along `line`, rising to `height`, section `width` x `depth`,
    `segments` 6-8; `ribs: n` repeats it round a centre. Originals: 7out06 `heavenTele_S`, elemf's flying arch,
    elemw `ElemHreatShrin` (160 faces), out11 `TestendPiece*`/`MainEndPiece*` frames.
28. **`culvert`.** A round or arched mouth set into a bank (`section`, `width`, `depth`), a liquid floor and an
    outflow strip to the river; `cascade` (a stepped channel cut into the land with animated water) as its form.
    Originals: 7out03 `Sewer_*`/`MTSewer_*` (42-64), out14 `Outlet_W`, `InletA/B_S`, 7out01 `CaveFall*`.
29. **Model import face roles.** `kind: model` with `doors: [{faces, house, title}]` and `hint` on the rest, and one
    entry taking several models with one event (out13's 50 ships). NEXT item 5.
30. **`lean`** (the top moved along `turn`) and **`tilt: {axis, degrees}`** on parts and platforms. Originals: out02
    d07 block, out07 `TmplSun_E` pylons, 7out15 `CBS` wreck.

## 3. Where the surveyors disagreed or were unsure

- `mist` outdoors: oute2's surveyor thought it missing; it exists (`atmosphere.yml` `mist`, batch nine).
- `cast` effect: out13's surveyor asked for it; it exists (`{cast: {spell, from, to, mastery, level}}`).
- `set_sprite` on a decoration structure (out07's statues) and a `{season: ...}` condition (7out04) exist.
- A part wider at its top (Shadowspire d19, the rebuilt survey): parts' `taper` above 1 flares already ("1.5: a cap
  wider than its neck"); only the overhanging cap ring is new.
- Signposts with several boards: outd1-3's surveyor wrote "a sign has one board"; `arms` gives each board its own
  `title` (7out13, out14, outc1 used it). Whether each arm gets its own event number needs a check.
- The MM6 `HF` fountain's shape: outb3 says three-sided, outc3 a 12-sided pointed shield, outa1 and oute1 rectangular
  (448 x 576). The 58-face family differs per map; `fountain.outline` takes all of them. outa2/outa3 judged theirs
  sayable with `sides: 4`, which makes a square of a rectangle.
- Tents: 7out04's surveyor marked them model imports (a), out03/out05/out14 a new word (b).
- Batch ten's waterfall text cites "Dagger Wound's WaterfallC1test"; out03's survey finds `WaterfallC1test` in Alvar.
- Checks the surveyors asked for, not words: `ridges` at about 40 lines (7out03 maze), a 5000 cliff as one step
  (elemf), `piers: 0` over a chasm (out10), scatter on steep peaks (elemw), a doorway against a model (outa1's Hive
  door), a plot over water (out09 Water Guild), 1800 trees in one scatter (out07).
- Lighthouse lanterns (outc2, outd1, oute2): no outdoor light word in the sketch; whether the originals carry a light
  was not checked.

## 4. Engine needs and data defects

1. **SetFacetBit-shown models stay unclickable outdoors** (c, known, NEXT "Not studio work"). Shipped cases: out02
   (the wind), out08 Balthazar Lair B after QBit 23, out13 the cannon `BFG_S`, 7out03 the Ninja tomb door; outc3's
   hidden bridge (`Bridge2N`, all faces 0x2000, shown by the tree's event 220) must also be checked for collision.
2. **outd3 events 90 and 91: not a defect.** `assets_dev/worlds/mm6/events/maps/outd3.lua` lines 354-360 hold
   `RegisterEvent(90 ...)` MoveToMap 6d03.blv and `RegisterEvent(91 ...)` MoveToMap 6d05.blv, matching the original's
   `evt.map[90]`/`[91]` (`reference/mmext-scripts/Decompiled_Scripts/mm6orig/OUTD3.lua` 170-176). The file is not plain
   ASCII, so a plain `grep` treats it as binary and prints nothing (use `grep -a`).
3. **outd3 event 210 ("garbled"): the original's own data, dead in play.** The original runs two Armageddon casts, the
   message "All Hit points restored.", "Chest", a question "Refreshing!" with the answers "The prince has been
   kidnapped!..." and "Crate", a summon and a 100-gold toll: unrelated strings. It begins `if evt.Cmp("MapVar4", 0)
   then return` (Cmp is "at least", so always true): it never runs past its first line. The export does the same
   (`IsAtLeast(MapVar(6), 0)`; map variables are consistently +2 in the export), with a harmless duplicated step-9
   block; `outd3_mmmerge.lua` replaces it. Not an exporter defect; a rebuild leaves the plate's event out.
4. **7out04 event 504: a real data defect.** `assets_dev/worlds/mm7/maps/7out04_1.scene.yml` binds event 504 on all
   faces of `ClL1_W` (taken from MMerge's `Scripts/Maps/7out04.lua`, which binds it at load and runs
   `TownPortalControls.DimDoorEvent()`), but neither `7out04.lua` nor `7out04_mmmerge.lua` has a handler. The engine
   has `evt.OpenDimensionDoor()` (used by 7out02, out02, oute3 overlays). Fix: a 504 handler calling it in
   `7out04_mmmerge.lua` (hand-written), or drop the binding. MMerge also opens it from tile (84, 94) by
   `TileSound`. The surveyor's export does not show it because `oymap export` reads the ODM, not the overlay.
5. **Tatalia's water in the first tile-set slot: not an engine need.** The game resolves each tile through the lookup
   by its id range (`game/maps/TerrainTileData.cpp` 83-85); no slot is fixed as water. The studio writes its own
   order; only `compare` differs. The same holds for a row used twice (out15, outc1) and lava in the ground slot (pbp).
6. **elema's hidden terrain** (decision): with `no_terrain` the land is not drawn but still holds the party; the
   sketch must say what it is (an invisible floor or a fall height).
7. Dead events in the shipped maps: elemf 451-454, elemw 451 (no face, decoration or model calls them).
8. outd1 `Poor 2W`: a house with every face invisible and untouchable and no event: `compare` should not count it.
9. out07's five `dec01` elf statues did not show in any picture (trees in the way): unconfirmed, one look with trees
   hidden.

## 5. Proposed code batches

Each a coherent group one agent can do in one batch, most maps first.

1. **Batch O-A: map-wide plumbing (ready to start).** `events[].trigger: leave` (16 maps), `atmosphere.flags`
   + outdoor `ceiling` + `footsteps` (10), `events[].when_flying` (7), invisible faces (`invisible`, `kind: barrier`,
   `kerb_invisible`, `ethereal`: 10), scatter extras (`group`, `to: none`, `event`, `on: water`, `height`: 8). Mostly
   writes to the scene and script metadata the engine already reads; the barrier reuses batch ten's undrawn fence
   barrier. Plus the 7out04 504 handler (data, not studio).
2. **Batch O-B: ways in.** `kind: cave_mouth` (NEXT item 14, 15 maps) with `free` and `mouth.form`, `kind: hatch`
   (4), `arch: round | pointed` on doors, doorways, windows and gates (10), door dressing (`leaves: 2`, `hood`,
   nested `frame`, `doorway.roof: gable`: 4).
3. **Batch O-C: fountains and bridges.** `fountain.outline` with `steps`, `tiers`, `pillar_shape: box`, `flow` (15),
   `bridge.arches` with sag and rope railing (11), liquid faces on parts (5), `culvert` (3).
4. **Batch O-D: masses and roofs.** `roof: dome` (7), `parts[].batter` + `buttresses` (9), roof to the ground
   (`tent`, A-frame, cone hut: 7), stepped masses (`steps`, `platform.tiers`, `platform.sides`: 5 + 3), `ruin` (5).
5. **Batch O-E: land.** `heights.spires[]`/`peaks[]` (6), `heights.cuts[]` with ramps (4), `ridges[].closed` (3),
   `against: slope` and `skirt: ground` (5).
6. **Batch O-F: open structures and landmarks.** Arcade/portico/round columns (7), `kind: portal` (7), raised decks
   (`walkway`, deck outline, `stilts`: 5), `kind: arch` with `ribs` (4), `stone_ring`/`trilithon` (3).
7. **Batch O-G: one-map words, when a map needs them.** Model import face roles (NEXT item 5), `lean`/`tilt`,
   `crown`/`sweep`, `hang_between`, `kind: plate`, `crate.stack`, `rock`, `wall.top: follow`, `floating`, `hive`,
   `sequence`, `sound` and `movie` effects.
