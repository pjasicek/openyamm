# D3 Sandcaster and the Aging Forest: L4 (built, installed)

A5, 2026-11-20 (seventh and eighth sessions). This is the approved L1 (D-28) built as L2-L4 and installed with its lighting bake.
The generator is `output/studio_cal/d3/tools/gen.py`. It runs `gen_l1.py` and reads `land.py`, `places.py` and
`scatter.py`. Run it with `output/studio_cal/d3/vw.sh`, which generates, formats, validates, builds into `build_w`,
measures and runs the dressing check. Install only through `output/studio_cal/a5/install_baked.sh xeen_d3
devdocs/xeen/briefs/d3/L4 output/studio_cal/d3/build_w output/studio_cal/d3/present/bake_profile.json`. The doors and
arrivals are in [DOORS.md](DOORS.md).

## State

- **Twenty-fourth A5 session (2026-11-21, 13:00-): the guild gate into DD-19.** `places.INSIDE['dd19'] =
  'entrance:d3_guild_gate'` (A8's (0, 384, 0) facing north); `places.asked_dungeon_way()` (D-72, D4 74's shape): event
  124 runs A3's `q-d14.quarter_gate` (its line ends on "Enter?"), then Yes/No buttons; Yes moves, No and Escape stay.
  `door:dd19` is no longer `listed_only`. Rebuilt with the 12:43 oymap (merge point 31's room steps: D3 has no rooms):
  the ODM and scene byte-identical, so a Lua-only install (`output/studio_cal/a5/s24/`), bake still fresh. The walk
  answers No (still on D3), then Yes into DD-19 at its arrival, and out by DD-19's gate (the leave window) to
  `entrance:dd19_gate` (-10752, 22016, 1728). D3 has no other typed prompt (D-72 item 3). Installed 13:05:42 (Lua
  and studio.yml); audit 0 errors (the 4 kept coplanar falls warnings); walk 712 and hostility 44 **2 of 2** from
  assets_dev (`output/studio_cal/a5/s24/q.log`); 0 stale bakes. Still open: D-42 (4)'s
  return point (-10496, 22150) facing south (`places.DD19_RETURN`, kept clear) is not the installed
  `entrance:dd19_gate`; moving it needs DD-19's exit rebuilt with it (A8).
- **Eighteenth A5 session (2026-11-21, 06:10-): rebuilt with oymap 06:06.** L4, the ODM and the Lua are unchanged
  (D3 has no peaceful groups for merge point 27). Only `entrance:dd18_shaft` moves: 1,504 -> 1,552 (merge point 25).
  That is the shaft lid (7solid01) inside its 32-unit curb, rim 1,568, on flat ground at 1,504. +48 is right: the
  party stands on the lid, not inside geometry; 1,504 was under the lid. The lift is under 64, so no warning; the
  build's one warning there is the hatch's corners between nodes (harmless on flat ground). DD-18's own way out
  still lands at the raw (-17408, 15872, 1504) facing south, on the street 512 south of the lid. A3's
  `Xeen.SkyFalls.d7_ef34` already holds z 1,312, so no request. Audit 0 errors, the 4 kept waterfall coplanar
  warnings (`run/s18/audit.txt`). Installed with its bake 06:20:31; 0 stale bakes. From assets_dev, game 05:26
  (merge point 26): walk 696, hostility 44 and d7 fall 23 steps, each **2 of 2** (`run/s18/`). The fall's HP
  is unchanged at 197/89/126/83 (`fall_pre.log`), so `playtest_d7_fall.yml` was not regenerated
  (`gen_fall.py` comment only, `.pre_s18`).

- **Eleventh A5 session: DD-07 open; installed with its bake 22:39:45** (`output/studio_cal/d3/run/s11/`). The
  Eastern Tower's door (A3's q-d18.tower_door, the key kept) leads to DD-07's `entrance:d3_door` (-2496, 0, 0) facing
  east (`places.INSIDE['dd07']`); DD-07's tower door brings the party out at (15360, 9216, 1889). L4 diffed against the
  tenth session's: only this door. Audit 0 errors, the 4 kept waterfall warnings. Walk (696 steps) **2 of 2** from
  assets_dev (`run/s11_walk1.log`, `s11_walk2.log`): with the key into DD-07 (asserts 113360), out by its `evt:exit`;
  hostility **2 of 2** (`s11_host*`). POIs 50. DD-19 stays sealed (A8).
- **Tenth A5 session, second step: installed 21:37:29** with its bake (`run/install_s10c.log`): the **north
  edge to D4 is open**. D4 is installed (A6, 21:09/21:29) and A2's travel rows exist (D3 north -> D4 `down`, D4
  south -> D3 `up`, 7 days each way), so `places.D4_LIVE` follows the installed file again (the `D3_D4_LIVE=0`
  override is gone). Built and audited with merge point 17's oymap (21:33:52; D-41's storey
  severities wired): 0 errors, no texture warning (`run/audit_mp17.txt`). The L4 against the texture-fit install differs only in the edge (`edge:north` live, 7 days),
  `entrance:north_road`'s text and the sign `thing:north_road_end` gone. Audit 0 errors, 4 warnings (the waterfalls).
  - Arrivals: D3's north edge -> D4's south start `entrance:south_road` (12288, -20992, 2112) facing north (512);
    D4's south edge -> D3's north start `entrance:north_road` (12288, 22528, 1760) facing south (1536).
  - The shared edge (`oymap export` of both maps, `scratch/fit/d3_export.json`, `d4_export.json`; D3 rows 1-6 against D4 rows 126-121): D4 continues D3's spans; the border rows
    agree within 96 (the road bed at x 88: D3 1,696-1,760, D4 1,632-1,760), the dunes, crest and rim within 64.
    D-28's "ridge 2,600-3,400" for x 0-24 is not at the edge itself on either side (both about 1,480 within 3
    cells; D4 climbs to 2,600 six cells in): consistent, nothing to fix.
  - Walk (689 steps: north up the Lakeside road over the edge into D4, assert D4's south start, south over D4's
    south edge, assert D3's north start) **2 of 2**, hostility **2 of 2**, from assets_dev (`run/s10c_*.log`). The land did
    not change: no new minimap.
- **Tenth A5 session: installed 21:27:00** with its bake (`run/install_s10b.log`), texture fit (merge point 16's
  oymap 20:45:55) and D-42's guild precinct. Audit (default and `--textures`): **208 errors / 183 warnings -> 0 / 4**
  (the 4 are the waterfalls' own coplanar faces, kept below; `run/audit_fit.txt`, baseline
  `output/studio_cal/a5/fit/base/d3.txt`). What changed (`tools/places.py`):
  - T07B and T07C (D-41): the rows above the lowest of every box part over 256 are plain `t07a01` (`plain_upper`,
    `upper_walls`), with the ochre window `t07a02c` in every other bay on parts 512 high or more; parapets and gables
    `t07a01`. The t07b footing panels and the t07a01b / t07c04c / t07c07 corbel course now show once, at the foot.
  - Vespar's ruin in the ochre grade (a ruin's broken walls lay their panels full height).
  - The Eastern Tower: shafts of seamless dark `gtrlwal1` (as X5's Darkstone Tower), the `hkm3b` skull frieze once
    a storey under each tier's top, `hkm3elw` windows only in the top band (was hkm3b stacked 3.5 times up).
  - `hcwindo` laid once per bay with `fit: true` (128 x 256), the rows above plain `hcwall` (guilds, quarter towers).
  - Signs at their pictures' size: `sgspell` 64 x 64, `xscaravan` 128 x 64.
  - The gate leaves' tops plain timber `7trimda` (they showed a 24 % sliver of the wing picture); still two leaves.
  - D-42: the guild precinct north of the quarter's wall (x 40.45-46.65, y 15.2-19.85): a court wall in `hcwall`,
    two gabled halls in pink hc ashlar under `desrf2a` (640 walls, `hcwindo` fitted) and a covered bridge between them
    over the court's middle wall; no door, nothing that enters; the plot levels its ground at 1,424.
  - D4 (installed by A6 at 21:09) is live by `places.D4_LIVE`; this rebuild kept the north edge sealed with
    `D3_D4_LIVE=0` (a new override) so only textures and the precinct changed (the L4 diffed against
    `output/studio_cal/a5/fit/l4_before/d3/`: only those, plus five new event ids). Opening the D4 edge is its own step.
  - Walk 679 steps **2 of 2**, hostility **2 of 2**, from assets_dev (`run/s10b_walk*.log`, `run/s10b_host*.log`).
    Minimap made again (`present/redo.sh minimap`, 21:30). Tour `tour/fit10b/` (the houses, guilds, tower, gates, sign, ruin, precinct and DD-19's return point).
- **DD-19** open since the twenty-fourth session (above). Before: sealed until A8 installed it. A8 gave its named arrival `entrance:d3_guild_gate` facing north (512),
  the way out about 300 south of the gate facing south (1536): DD-19's return point on D3 is (-10496, 22150, 1728)
  = cell (43.5, 20.74) on the quarter terrace, kept clear (no prop, no spawn marker; `places.DD19_RETURN`). A8 proposed
  the guild-hall roofs north of the wall (x 40-47): built as the precinct above (D-42).
- **DD-07** open since the eleventh session (above).
- **Ninth A5 session: installed 20:12:35** with its bake (`run/install_s9.log`), oymap merge point 15: DD-18's street shaft open (`places.INSIDE['dd18'] = 'entrance:d3_shaft'`, `into: {map: xeen_dd18.blv, arrival: entrance:d3_shaft}`: A8's ladder foot (0, 128, 0) facing south; DD-18's own exit lands at (-17408, 15872, 1504)). Audit 0 errors (door check included, `run/audit_s9.txt`); POIs 51. Walk (679 steps, now goes down the shaft into DD-18 and loads back; `gen_walk.HAVE` = the dungeons with a row and a map) **2 of 2** (`run/s9_walk1.log`, `s9_walk2.log`), hostility **2 of 2**. DD-19 and DD-07 stay sealed (A8 phase 4, A7).
- **Installed** 19:39:05 (ninth pass, after the lane review of `sheet4`) with its bake in the same step
  (`install_baked.sh`); `stale_bakes.py` lists nothing for D3 (its two stale entries are xeen_dd09 and xeen_dd18,
  other lanes' dungeons). Terrain weights went through `terrain_swap.sh`; the minimap `icons_x2/xeen_d3.png` was made again
  (`present/redo.sh minimap`). Built with oymap of merge point 13.
- **From assets_dev** (`--world xeen`, `walk.sh`): A2's map_stats row 9110 (continent 7), A2's D2-D3 edge spans and
  A4's 48 house rows are in. project.yml says `continent: 7`.
  - walk (`playtest.yml`, 678 steps): 2 of 2 (`run/walk_b1.log`, `walk_b2.log`). Every house door opens its house screen (or, for a residence, its
    person's talk; closed houses their closed texts); both fruit huts give +2 to the base stat and the condition once
    and nothing the second time; out of the west edge to D2's east start (21504, 10240) and back over D2's east edge
    to D3's west start (-22528, 10240).
  - hostility (`playtest_hostility.yml`): 2 of 2 (`run/host_b1.log`, `host_b2.log`).
- The scratch root `output/studio_cal/d3/root` is removed (`root.sh` makes it again; iterations before an install can
  tour it with `tour.sh <name> <root>` after `refresh_root.sh`).

## What was built

- **Sandcaster** stands on its terrace at 1,504 inside a t30 sandstone wall (288 high with battlements; four walls,
  the quarter's side 320; fix 4 below).
  - Houses use the sandcaster kit: MM8 t07 in three grades (flat roofs behind parapets, terracotta hip roofs on the
    rich ones), MM6 hc for the guilds and the quarter, and A6's xs* shop signs.
  - All 40 city doors of A4's `d3.yml` are drawn. The mirror is on the paved square, with Omid's well beside it.
  - The streets are sandstone setts (`road_flagstone`): the gate street, the bazaar street, the west lane and the
    guild row.
  - **Wizard quarter (D-28)**: a terrace 224 above the city. It has a retaining wall of hc ashlar with a parapet, and a
    stair up its south face between houses 4637 and 4638. Five doors stand round an open court, shut with A4's closed
    texts until `q-d14.done`. The three round towers have cones about a storey above the guild row's ridges. The
    guild gate (DD-19) is in the north wall; behind it, north of the wall, the guild precinct (D-42) shows its two
    gabled halls and their covered bridge over the wall.
  - **Sky Stair**: a stepped sandstone stair-tower of four tiers, 1,536 high (fix 3 below). Lucio's Jetty is a timber
    deck on its top with six mooring posts. The deck reaches out north over the wall into thin air. Its door is house
    4649 (closed text until `m30.done`). The jetty only departs.
  - **Two gates (Q-D8)**:
    - South gate: a gatehouse wall between two square gate towers, with a round-arched opening of 256.
    - East gate: a round arch of 256 in the wall, between two gate towers.
    - Each gate has two leaves side by side, outside and inside (the double-door rule, below). The outer pair runs
      `q-d8.sandcaster_gate` (the pass), and the inner pair opens from inside.
  - **Caravan yard (D-28)**: a fenced pocket outside the south gate. It holds the stables (4611, door west), a water
    trough, hay and a barrel pair. The arrival is inside it, and the gate is in sight; the tour picture checks this.
- **The Crossroads**:
  - six MM6 striped tents with A6's stall boards round the ring, and a well in the middle;
  - Celia and Derek's cottage (4647) at [64, 46] on the Venom road, about 1,400 from the ring's edge. Its door faces
    south toward Venom Pond and runs `q-c22.cottage`.
- **Relief (D-28)**:
  - the broken **Wrath crest** (x 90-103, y 21-39): knobs to 3,392, with crags, needles, shelves and rock faces
    (fix 1 below);
  - the **Lakeside saddle** at 1,856 on the D4 road (x 88);
  - the **gorge**: the River of Wrath leaves a fall from the rock face at the gorge head (81, 21) and runs between
    sheer walls 400-800 high from y 21 to 38 (fix 2 below);
  - the **west-bank hills** at 2,400;
  - the **Howling ridge** at 1,900-2,200, falling west to D2's edge heights (1,312 at the road).
- **The River of Wrath** runs under Wrath Bridge (t30, two arches) and through the meadows to the **Wrath Falls** at
  the east rim, a waterfall into the stars. Its banks east of x 80 are kept free of trees for the signature view.
- **The Eastern Tower** stands on its knoll at (97, 46), its planned place: dark gtrlwal1 stone with the hkm3b skull
  frieze once under each tier's top, three tiers and a slate cone. The door faces west and runs `q-d18.tower_door`, then shows a sealed line.
- **The Aging Forest** uses MM7's autumn twins (7tree14, 17, 20, 08, tree26), red and gold.
  - The great oak (7tree08) stands at (53, 65), about 2,900 east of the forest road, with the oak lane (D-28). Its
    hornet nest is beside it.
  - Cornelius (NPC 5247) is in his glade.
  - The fig hut stands at the forest's east edge (60, 72), where it closes the 6,000 rule.
- **Venom Pond (864)**: Thaddeus's hut (4648) and the Fountain of Youth (`q-d18.fountain`; Poisoned before done). The
  fen is to the rims' corner with the Fountain of Great Protection.
- **The pear hut** stands on the river's south bank: a whitewashed round hut with a pear tree and a basket.
- **The fruit huts' boons (D-28 (4))**: each basket runs A3's player bit once per character (`fruit_pear` 11320,
  `fruit_fig` 11321 in `source/npcs/d3.yml`). The first time, it gives +2 to the base stat (Might or Intellect), sets
  the condition (Weak or Insane) and shows the hut's line. The same character again gets "You have had your share.
  The rest look far less tempting now." This is D1's Well of Might mechanism (`condition: {not: {player_bit}}`,
  `{player_bit}` effect).
- **Sounds**: Snd_Brook at the gorge head and at the falls, Snd_Howl at the howling stone. Music 39. Sky `xeendark1`,
  with `evt:sky` running `Xeen.applyDarksideSky()` on load.

## Measurements (`run/vw_last.txt`, `tools/measure.py`, the D-20 census)

| Figure | Target | D3 |
| --- | --- | --- |
| POIs (D-20 census, D-28 cap) | 35-55, cap 55 | **51** (no click had to be taken off) |
| Hostiles at load | 135 | 135.5: 47 markers (mantis 24, cobras 12, sand worms 11) x 2.5 + 18 placed hornets |
| Kill XP per member | 34.8k ±15 % | 37.4k, ratio 1.07 (L1 render's count; the same markers, rows and tiers) |
| First fight, map-edge arrivals | 2,000-6,000 | D2 road 4,769; D4 road (sealed) 3,807 |
| Town buffer (D-15) | 2,500 | nearest hostile to a town door 4,287; square 9,285; caravan yard 7,474 |
| 6,000 rule | none over 6,000 | farthest 5,904 at (80, 57); 0 tiles over 6,000 |
| Wild land, 3 cells from anything (D-11.5) | <= 0.16 | 0.034 |
| Roads | 1-4 % | 1.8 % road tiles |
| Chests | 4-10 | 8 |
| Height range inside the box | >= 2,500 | 864 (Venom Pond's water) to 3,392 (Wrathtop) = 2,528; the driest low ground (the fen shore) 896, so 2,496 on dry land; the crest's crags 2,880-3,328 |
| Textures | 120 | 79 distinct face textures, 0 new (all shipped or A6's installed xs* signs, xdbark, xtslate) |
| Spawn markers on walkable ground (D-28) | tiles <= 512 | worst marker tile 352; markers kept 3.2 cells off the knobs and needles, 2 off the shelves |
| Lakeside saddle (D-28) | <= 1,900 at x 88 | 1,856 |
| The gorge's depth (L1) | 300-700 | walls 600-800 at the head, 400-600 below y 31, sheer; floor 960 under the river at 992 |
| Audit (`--reach --solve`, dressing) | no errors | 0 errors; 4 coplanar warnings (below); 973 props, 48 doors, 50 walking lines checked |
| `fmt --check` | | L1-L4 clean |

## Texture fit exceptions

None: the texture-fit check reports no error and no warning (tenth session). D-41's option for `t07c04c` and `t07c07`
was not needed: their upper storeys are plain `t07a01` with `t07a02c` windows, so the corbel course shows once and
reads as a string course between storeys.

## Dressing exceptions

- `geometry.coplanar` x 4: inside the studio's own waterfall structures (`thing:spring_fall`, `thing:wrath_falls`). The
  sheet's top meets its own bank face, overlapping 61-84 square units. This is the waterfall word's geometry, not a prop.

## Town feel exceptions (D-20)

**Sandcaster** (`town_feel.py` of merge point 13 on the installed map with A4's house rows, `run/tf_sandcaster.txt`;
town box -19456,9728,-8192,23040). The three figures outside the shipped range are unchanged:
- Straight road run median 4,096 (shipped 1,024-3,072): the walled city's gate and bazaar streets run straight from the
  gates to the square.
- Stables rank 1.0 (shipped up to 0.81): the caravan yard is outside the south gate by D-28 (3), so the pass check stays.
- Wells and fountains 10 (shipped 3-8): the checker matches titles. Only 5 are wells or fountains: Omid's well, the
  Crossroads' well, the caravan well, the Fountain of Youth and the Fountain of Great Protection. The rest are A4's
  house names "Well House" and "The Fountain Keeper's Hut", and the yard's water trough.

**The Crossroads** (`--small` of merge point 13, the real tool, `run/tf_crossroads.txt`; the stall-only spread figures
show n/a). All 14 out figures follow from a market of six stalls in a ring with no homes, as L1 and D-28 approved:
- most-common shape 0.83, distinct shapes 0.33, mirror partners 1.0;
- road or dirt share 1.0, roads on axes 0.47, turns of 80-100° 0 and turn median 135 (six radial roads);
- longest straight run 2,896;
- enterable residences 1 (Caleb's Workshop);
- wells 10 (see above);
- flat share 1.0;
- footprint covered 0.1, extent per building 664, open circle 0 (the ring's middle holds the well).

## Words the studio lacked, and workarounds

- No gate in a wall at a line's end: the south gate is a short gatehouse wall with a gate between its towers.
- A wall's top is level over its highest ground, so a wall ring over uneven ground is several walls.
- The gorge is a `cut` (sheer one-node walls as high as the rims). Cliff lines whose corners meet the river's corners
  raised a node in the river's middle, and floor points over the water's level dried its edge into pools.
- No turning gate leaves: the gates' leaves hide when opened (A1's paired-leaf word is coming). No texture scale on a
  wall face: a gate leaf must be the picture's own size (128 x 256), so the gates are 256 wide.
- No rock-face word that follows the land: the gorge's and crest's rock is walls and obelisks in cwb1, their heights
  read from a build (a wall's top is level at its highest ground). Slope rock is per world (`world.yml`, A6).
- `xeendark1` has no directional band: the bright face's glow above the east rim is asked of A6.

## Gaps and blocks (no stand-ins)

- DD-18, DD-19 and DD-07 are all open (ninth, twenty-fourth, eleventh sessions). They stay sealed by
  `places.INSIDE` and the installed check until their dungeons are installed and their points given.
- **D4**: open since the tenth session's second step (above); the spans and heights are in DOORS.md.
- **A6**: the bright face's glow band above the east rim through the sky preset (not possible with `xeendark1` today).
- **A1**: a word for paired leaves that open apart (the gates' leaves hide for now); a rock-face or outcrop word that
  follows the land (cliff faces and crags of faceted rock, as the waterfall's `rocks`).
- **A6**: the Darkside's steep grass reads as bark mulch (the slope layer tinted from the soil, `grass: cliff_from:
  dirt` in `terrain_materials/world.yml`); a rock tint of its own for the slope layer (for example from a grey stone
  reference, not the soil) would make every Xeen crest and gorge read as rock.

## Original lines (`aaze` references)

- "Special today! Vulture Repellant, only 25,000 gold!" (dark/aaze0031:19) and "Vulture Repellant doesn't work."
  (dark/aaze0031:25): on the board by the alchemist's door (`thing:repellant_board`).
- "The wizards in this town are sensitive to insults. Watch what you say!" (dark/aaze0031:29): the notice at the
  quarter stair's foot (`thing:quarter_notice`).

## What the user should look at

- The Wrath crest from the Lakeside saddle and from the river meadows: rock pinnacles along the ridge over dry grass,
  the steep slopes still soil-coloured (the world's slope layer, A6).
- The gorge from its mouth (79.5, 41): rock faces either side of the river; the spring's fall in its gap in the
  head's rock face from the east lip.
- The Sky Stair's tiers from the square, and its jetty deck from above.
- Sandcaster from the caravan road and the dunes: the roofs, the guilds, the quarter's towers and the Sky Stair over
  the lowered wall.
- The south and east gates' paired leaves.
- The signature view along the east rim: the falls over the rim, the meadows, the Eastern Tower. With A6's
  `xeen_bright_rim` and merge point 20 (the glow lights the horizon cloud banks), 13th session: the signature looks
  north-north-west and the glow is centred due east (75 wide), so it stays out of that frame
  (`output/studio_cal/d3/tour/s13/sheet_signature_mp20.jpg`: day, dusk, night, south bank). Looking east from the rim
  it reads: a warm band at dusk, a bright band behind the cloud bank at night (`sheet_rim_east.jpg`; `04` frames the
  falls on the left and the glow on the right). Again after A6's `below_deg` 1.5 (`sheet_below15.jpg`): the night glow
  reads strongly looking east, still only at the frame's edge in the signature. Turning the signature toward the
  north-east is a camera choice (asked as a design question).
  **D-50:** the signature stays north-north-west (yaw 2.0344 from (22272, -4096, 1300)). The glow has its own named
  view, `rim_glow` in `gen_tour.py`: from (19456, 2560, 1344), cell (102, 59), at 23:00, looking east (yaw 0.2187).
  The rim's grass fills the lower-left, the falls' lip sits at the right edge, and the glow band is central
  (`output/studio_cal/d3/tour/s14_rim_glow.png`). The framings that were tried are on
  `tour/s14_rimtry_sheet.jpg` and `s14_rimtry2_sheet.jpg`. From south of the falls, the falls' south rock cheek
  fills the foreground.
- The Aging Forest's red and gold, and the oak's lane.

Tour pictures: `output/studio_cal/d3/tour/shots5/` (26, from assets_dev, ninth pass), with contact sheets
`tour/sheet5_*.jpg`; the eighth session's `shots4/` and `sheet4_*.jpg` beside them.
The tour file is `tour/tour_d3.yml`, written by `tools/gen_tour.py` and run by `../tour.sh <name> [root]`.

## The lane review's five fixes (eighth session)

The review of the seventh session's tour (`tour/sheet2_*.jpg`) asked for five changes. Each is now in the generator:

1. **The Wrath crest** (`land.py`, `places.py` `crest_rock()`, ninth pass after the review of `sheet4`):
   - The knobs keep their heights (Wrathtop 3,392; the others 3,100-3,232). The crest is broken by a field of 14
     terrain crags (`peaks`, 2,880-3,328), 17 needles (`spires`) and three shelf cliffs (`CREST_SHELVES`); rough 24.
   - Rock geometry along the ridge: 13 rock pinnacles (`thing:crag_*`, obelisks in the world's rock cwb1: a broad
     tapering shaft, a low tip), each topping out at 3,360-3,392, never over Wrathtop (heights from each one's foot
     read from the build, `places.GROUND`); big rocks (rock65, rock68, 7rock08, rock12) along the ridge line.
   - Ground: the crest's bare dirt only where a cell rises more than 800 (`steeper_than`); dry grass and scrub
     (`scatter:crest_scrub`) between.
   - The eighth session's D3 entry in the terrain materials' `world.yml` (a gentler slope band, desert-tinted rock)
     drew glossy streaks; it is removed, so the shared file is as it was.
   - What is left: the steep grass slopes take the world's slope layer, rock tinted from the soil (`grass:
     cliff_from: dirt` in `world.yml`), which reads as bark mulch from the meadows and the saddle. That is A6's file
     and every Xeen map's look.
   - The Lakeside saddle stays at 1,856 (x 88, y 24); spawn markers stay on tiles of at most 352 and 3.2 cells off the
     needles and 2 off the shelves.
2. **The gorge** (`land.py` `gorge_cut()`, `places.py` `gorge_rock()`):
   - The gorge is a `cut` from the spring (y 21) to y 38. Its outline is the two walls and the head, it is open to
     the south, and its floor (960) lies under the river (992). Its terrain walls are sheer, one node each: 600-800
     at the head and 400-600 where it opens. The river runs unbroken between them, 2 cells wide (`width_cells: 2`):
     the old floor points at the bank's height had dried its edge into pools.
   - Rock faces (ninth pass): six walls of the world's rock (cwb1), 384 thick, stand in the cells between the rims and
     the floor (`GORGE_FACES`). Their faces are sheer on the river from the floor (about 1,000) to about 100 under the
     rims (1,500-1,730). Each one's height is read from the build, because a wall's top is level at its highest ground.
   - The head is two rock walls with a gap for the spring's fall. The fall's own slabs are off (`rocks: false`), so
     the fall comes out of the rock face; the land over the head stands at 1,800-1,860.
   - From the gorge's mouth they read as rock walls with the river between, but as blocks: a wall's top is flat and
     its ends square.
3. **The Sky Stair** (`places.py`, `sky_stair`):
   - A stepped stair-tower in the city's sandstone (MM8 t07a): four tiers of 448, 384, 384 and 320, each set back from
     the square with a parapet round its terrace. The top tier stands against the north side, 1,536 over the terrace.
   - Lucio's Jetty is a timber deck (7trimda) on the top. It has no posts down to the land, which had read as a
     crane's legs. It reaches out north over the wall, with a kerb and six mooring posts (decks 224 high).
   - The tour shot `06-sky_stair_deck` looks down on the deck.
4. **The city from outside** (`places.py`): the outer wall is **lowered** from 512 to 288 (battlements on it).
   - Why lower the wall, not raise the terrace: every door point, A4's arrivals (`sandcaster_square` Z 1520) and the
     walk stay as they are, and the 192 step of the terrace outside the wall keeps it a city wall from the valley.
   - The ring is now four walls (west, north, quarter, east), because a wall's top is level. As one ring it stood at
     the quarter's and the dunes' ground: 600 over the terrace in the south.
   - The terrace's flat roofs and parapets, the guild roofs, the quarter's towers and the Sky Stair now show over it
     (`01-arrival_from_d2`, `city_from_road`, `city_from_dunes`, `valley_over`).
   - The quarter's side is 32 higher than the rest: at 288 its walk lay in the plane of the guild gate's frame top.
5. **The signature view** (`gen_tour.py`): `signature` looks along the east rim from over the stars south of the falls
   (107.5, 72), 1,100 up. The river's fall goes over the rim in the foreground, with the river meadows and the Eastern
   Tower on its knoll behind. `south_bank` keeps the old framing from the south bank (86, 66), raised 500. The glow
   band still waits on A6.

**The lanes' new rules** (README, 2026-11-20):

- **Double doors.**
  - Sandcaster's two gates are now 256-wide round-arched openings. The south gate's opening is a gatehouse wall
    between its towers.
  - Each gate is closed by two leaves side by side, outside and inside, with MM8's paired gate wings (t30a03b1 left,
    t30a03b2 right, 128 x 256: one picture each, untiled). A click hides all four leaves. Before this, one leaf of
    512 tiled a single-door picture four times.
  - The leaves hide rather than swing apart: the studio's wall leaves cannot turn. **Waiting on A1's paired-leaf word.**
  - The guild gate (DD-19) is 256 x 256, so MM6's hclgdr (one picture of a double door, made for 256) fits once.
  - The Eastern Tower's door (hkm1d) and the quarter's and guilds' doors (hcsmdr) are single doors.
- **Texture fit.** In the tours, the gates' tiled single-door picture was the one tiled motif, and it is fixed. The
  windows on the Sky Stair's tiers, the gate towers and the guild halls are one per bay, from the kits. The city walls
  (t30c01) and the quarter's wall (hcwall) are seamless stone. A1's tiling check has not shipped yet.
- **Light fixtures.** D3 has no interiors.


## Twenty-first session (A5, 2026-11-21): D-70, the temporary sources once a day

- Wayside shrine of the desert sun, Omid's deep well, the Wrath Spring, Fountain of Great Protection, the great oak,
  Pilgrims' cairn and the caravan well go through `places.daily()` (`Xeen.usedToday("d3_<thing>")`, every member);
  refusals: water "The water is cool and refreshing.", the shrine "No one seems to be listening.", the oak and the
  cairn their own lines; gains "until you rest". Backup `d3/tools/places.py.pre_s21`.
- odm and scene byte-identical: Lua and studio.yml installed 08:26:23, bake fresh; walk 696 and hostility 44 2/2 from
  assets_dev; audit 0 errors (4 kept).

## Twenty-fifth session (A5, 2026-11-21): the cottage opens on every knock (event 93)

- A3's Q-C22 answer: `q-c22.cottage` is `once` with no else line, so after the first visit the hook answered false
  and the door did nothing. The door's condition is now `any: [qbit 112443 (q-c22.moved), the hook]`
  (`places.py`, backup `.pre_s25`): the first knock after Q-C22 runs the hook (Celia's greeting, both moved in), every
  later knock enters house 4647. Before Q-C22 is done the hook's refusal as before.
- The walk (`gen_walk.py`, backup `.pre_s25`) knocks a second time and asserts the dialog. odm and scene
  byte-identical: Lua and studio.yml installed 16:32:57, bake fresh, audit 0 errors (4 kept); walk 722 and hostility
  2/2 from assets_dev, 1/1 in the stage first (`output/studio_cal/a5/s25/q.log`).

## Twenty-sixth session (A5, 2026-11-21): D-85

- D-85 (no hostile marker within 5,888 of an outdoor talking quest giver): Cornelius (5247, (-12186, -4198)) had two
  Howling Woods mantis groups at 3,799 and 4,195. `gen.py` (backup `.pre_s26`) now moves any `pop:howling_woods`
  marker nearer than 12.5 cells (5,888 + the circle's 512) to Cornelius to the nearest free walkable candidate beyond
  (`clear_givers`); the area's other ten markers and every other area keep their places. Marker 3 (34, 76) ->
  (30, 80): spawn 25 (-15136, -6592) -> (-17696, -8448), 6,959 from Cornelius; marker 11 (32, 75) -> (28, 75): spawn
  33 (-16128, -5632) -> (-18592, -5376), 6,513. Nearest hostile to Cornelius 3,799 -> 6,509 (spawn 27, unmoved); no
  warnings left. Same 47 markers, slots, groups and 18 placed actors; only these two spawns and circles changed; odm
  byte-identical; scatter "no place" count unchanged.
- `check_d85.py` at 5,888 passes (`output/studio_cal/a5/s26/d3_d85.txt`); `d54_check.py`: no ranged hostile within
  5,888 of the D7 fall. Measure: first fights D2 road 4,769, D4 road 3,807; nearest hostile to a town door 4,287.
- Installed with its bake 19:30:32; audit 0 errors (4 kept); walk 722, hostility and `playtest_d7_fall.yml` 2/2 from
  assets_dev (`output/studio_cal/a5/s26/d3_walk_{1,2}.log`, `d3_host_{1,2}.log`, `d3_extra_{1,2}.log`).

## Twenty-ninth session (A5 s29, 2026-11-22, merge point 41 rebuild; run files output/studio_cal/a5/s29/)
- Rebuilt and installed with its bake. F16: trans 5035/5051/5053; the guild gate (124) no longer asks Yes/No nor calls
  q-d14.quarter_gate (its window line is trans 5053; A3: the hook's SimpleMessage is now unused). D-89: the Eastern Tower
  opens without the key (walk). Left: F10 zone at the north-west corner, tile [20, 20], 16,804 deep, 765 tiles (outside
  Sandcaster's walls; needs a new population, NEXT).

## Thirtieth session (A5 s30, 2026-11-22; run files output/studio_cal/a5/s30/)
- F10 (the orchestrator's decision: a population outside the walls): `gen_l1.AREAS` `pop:outside_walls` (slot 3, sand
  burrowers; fixed cells (21, 24) under the west wall and (46, 49) in the caravan valley south of the city; population
  on `zone:caravan_valley`) and `pop:forest_edge` (slot 1, mantis ants; (70, 63) between the Aging Forest's east edge
  and the river meadows; on `zone:crossroads_plain`); `gen.py FIXED_SPOTS`; backups `*.pre_s30`. The meadows and the
  forest stay open polygons. A first try at (34, 47) was 3,100 from the D7 fall landing (34, 41): `playtest_d7_fall`
  lost Brokk in the 20 s (D-54); moved to (46, 49), 7,370 off.
- Empty zones: [20, 20] 765 tiles / 16,804 -> largest 149 tiles, deepest 7,980; land > 6,000 13 % -> 5 %; road
  median 5,943 -> 2,763. 50 markers, 143 at load; kill XP 1.07 -> 1.13, Act III 1.03. D-85/D-87 0 errors, audit 0.
- Installed with its bake 01:45; walk, hostility and d7_fall pass from assets_dev.

## Rim rebuild (2026-11-23, agent xeen-rimmap-c: U-12, D-106, D-109, D-112, D-113)

- The rim sea is the void (`terrain.void [[104, 0, 127, 103], [0, 104, 127, 127]]`), 55 hull pieces with the corner at
  (104, 104), 18 rescue return points; the rim event, the wayside shrine's altar (D-103) and the studio's F30/F31 come
  with the regeneration.
- **Wrath Falls** on the river's mouth: `places.py` line [[103.2, 64], [104.6, 64]] (it was written along the edge for
  the sea; the kit had put its lip at (104, 62.9)); lip (104, 64), spillway (D-112), foot -2,400.
- **Gorge faces** (`town_fit_pending`, F26): looked at first (`cap/d3_gorge_before/`): e1 and the head's two slabs
  hung 45-88 over the gorge floor (the head's underside showed), and the east rim's turf rose 56-58 over e1-e3 (check
  limit 48). `places.py` `GORGE_FIT`: e1 and both head slabs `raise: -128` (same top), e1-e3 24 higher: the turf's lip
  still shows about 32 over the rock. `town_fit_check` 0; the pending entries are dropped.
- The grey bar seen by rim4 over the falls from the void was terrain water quads at the river's level drawn over void
  cells (engine; fixed by the orchestrator in `OutdoorTerrainMaterials.cpp` createMesh, `build-xeen` rebuilt;
  recaptured from assets_dev: gone, `output/xeen_rimmap_c/cap/d3_final/`).
- Checks: audit 0 errors (6 warnings, the known south gatehouse back-to-back x3, spring_fall coplanar x2,
  `chest.title` tower_cart), `void.occupied` 0, door 0, wall 0, town_fit 0, empty zones, props, check_wild clean,
  check_faces (the same 5 kept-as-known findings), D-85 (X2's check) 0, house signs 0, `stale_bakes --check` 0.
  Build warning (kept): `raise: -128` on the three fitted faces ("stands 128 under the land"), by design.
- Tests: walk x2 and hostility (root and assets_dev); story 55-69 pass; side quests obelisks_darkside, q-c22, q-d8,
  q-d14, q-d15, q-d18, q-d19, q-d20 pass.
- Generated twice (the rescue's return points from the first build's land, `XEEN_WILD_MAPS`), built, villagers placed, recorded (`agent:xeen-rimmap-c`), checked in a private hard-link root, installed with its bake, terrain weights, the minimap re-rendered and its void painted (`tools/xeen/void_minimap.py`). Scripts `output/xeen_rimmap_c/build.sh`, `install.sh`, `tests.sh`, `tours.py`; logs `output/xeen_rimmap_c/run_<key>/`; captures `output/xeen_rimmap_c/cap/<key>_after/` (day and night, against `output/xeen_rim/before/<key>/`).
