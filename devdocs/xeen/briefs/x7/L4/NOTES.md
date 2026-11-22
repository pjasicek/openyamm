# X7 Mount Firestone: L4 (built, installed)

A5, 2026-11-20 (a sub-agent of lane A5's lead). The L1 plan approved with changes by D-40
(`../L1/D40_DECISION.md`), built as L2-L4 and installed with its lighting bake. The generator is
`output/studio_cal/x7/tools/gen.py`; it reads `gen_l1.py` (L1 itself is not rewritten), `land.py`, `places.py` and
`scatter.py`. Run it with `output/studio_cal/x7/vw.sh`: generate, fmt, validate, build into `build_w`, measure
(`tools/measure.py`), dressing check, audit (`--reach --solve --textures`). Install only through
`bash output/studio_cal/a5/install_baked.sh xeen_x7 devdocs/xeen/briefs/x7/L4 output/studio_cal/x7/build_w
output/studio_cal/x7/present/bake_profile.json`; the minimap with `output/studio_cal/x7/present/redo.sh minimap`.
Walk and hostility: `tools/gen_walk.py <L4> <build> <root>`, `tools/gen_hostility_x7.py`, then `walk.sh <scenario>
<log> [root]`; tours `tour.sh <name> [root]` (`tools/gen_tour.py`, `TOUR_ONLY=a,b`).

## State

- **F10 (2026-11-21, the user: "ultra empty, no mobs in radius" at (12816, -9160)).** The south slopes' middle and
  east held no monster within 12,000 (`tools/xeen/empty_zones.py`: one empty zone of 2,043 tiles, deepest 13,451; road
  tiles a median 7,762 from a monster, the worst in the world). The south's orcs are now 13 markers of 1-2
  (map_rows.yml X7 orcs `count: [1, 2]`, was 8 markers of 2-3: 19.5 orcs against 20, Act I 1.1468, a 14th marker
  gives 1.1504) in six areas (`gen_l1.AREAS`): west slopes 4 (to the X1 edge), red river 3 (the basin's south
  half), and new east range 3, gap south 1, south hills 1, pony ridge 1; `gen.py` spreads slot-1 markers one by one
  (no pairs); the Red Dwarf Range's plan text no longer says "quiet by design". Sablewing's 5,888 (D-85) and the
  watch stay clear (`tools/xeen/empty_zones.yml`). After: largest zone 239 tiles (8,519, beside the watch), land
  > 6,000 11 %, road median ~6,000; first fights X1 4,845, X4 5,485; Sablewing's nearest 8,930; D-85/D-87 0 errors.
  The 6,000 rule (D-11.5): 3 tiles over at the rim corner (103, 108), 6,614 (was 0); left.

- **Twelfth session: installed with its bake 23:13:29.** A6's basalt (`terrain_materials/world.yml`, X7's `maps:`
  block) needs ash tiles on steep ground: the tower path's dirt lane climbed the Dragon Tower crag's south flank and
  laid red dirt there. `land.PAINTED_POINTS` ends the lane's dirt at the crag foot (21, 38) (the profile still cuts
  the climb), so rows 32-37 round the crag are `7wastetile` / `7wstdrt*`; only the lava shore's `lvdr*` stay. Figures
  and audit unchanged (0/0). Walk 373 2/2, hostility 2/2 from assets_dev (`run/s12_*`). The in-game look of the crag
  is still to be shot (A6's `x7mat` tour).
- **Eleventh session: installed with its bake 22:35:59** (`output/studio_cal/x7/run/s11/`; L4 diffed against the
  tenth session's: only these changes).
  - **POIs 20 -> 22**, inside the trap band 22-28: the fork and slope signposts name their roads when clicked again
    (`places.gap`), as L1 counted them. D-40 asked only for the two merges (24 -> 22) and took a signpost's click off
    only past 28; the tenth session had taken both clicks off, which left 20.
  - **XD-05's back gate open** (A7: XD-05 names `entrance:x7_gate` (2176, 13184, 320)): barred until 110051, then in;
    XD-05's back gate brings the party out at (11776, -18432, 2017).
  - Audit (default and `--reach --solve --textures`): 0 errors, 0 warnings. Walk (373 steps) **2 of 2** from
    assets_dev (`run/s11_spans1.log`, `s11_spans2.log`): sets 110051, into XD-05 and back by its gate; both new
    signposts; the edges now assert the orchestrator's edge_spans points (X1 (2560, 22016), X7 (2560, -22016), X4
    (22016, -1280), X7 (-22016, -1024), radius 200). Hostility **2 of 2** (`s11_host*`).
- **Installed 21:58:04** with its bake in the same step (merge point 17's oymap 21:33:52, game 21:33:20); terrain
  weights through `terrain_swap.sh` (lava rules of Xeen's `terrain_materials/world.yml` picked up); not in
  `STALE_LIGHTING_BAKES.txt`; minimap `icons_x2/xeen_x7.png`. Earlier installs 21:39 and 21:44 (same session).
- **Lava is lava** (D-40 change 3): the lake, the crater and both rivers are `tile_set: lavtyl` (A1's set in the MM7
  table, rows 450+); no water on the map but the stars below the rims. The party cannot swim to the island.
- **Ash** (D-40 question 9): `ash: 40` in atmosphere.yml (A1's word, merge point 17); the scene's weather carries
  `ash_chance: 40`. Sky: the world default (Cloudside's fair preset) with A6's `ashen` theme.
- Walk (`playtest.yml`, every device, hook and sealed door, the north and the island) and hostility: see "Checks".
- `terrain_swap.sh` (lane tool) now hard-links `world.yml` into its private root: without it `terrain_materials.py`
  read MM8's tile names and stopped on X7's lava rows ("No terrain material rule matches tile dirttyl", 21:39).

## What was built

- **The south slopes** (1,650 at X1's edge to 2,300 under the range): the north road (pebble road, 1 tile, about 4 m
  of pebbles in the classic road set) from the X1 edge past the slope fork to the Gap.
  - **The abandoned dwarves' watch** (D-40 question 8): a fieldstone stockade 256 high, its gate west on the road, the
    signal tower (cone roof), the roofless barracks, a barrel pair against the north wall, a cold brazier; the pay
    chest (level 2) by the south wall with A3's `x7.watch_note`. The pony shed, roof fallen in, under the range.
  - **Sablewing** (NPC 4720, D-5.2) at his cave mouth under the red crag at [75.6, 90.1], a small fire and a pot; his
    nearest fight 7,661 away.
  - **The Shrine of Fire** on its knoll (daily, +10 Fire resistance, player bit 11339 cleared by `evt:daily`), **the
    Well of Speed** (+2 Speed once per character, player bit 11338), **the hot spring** (+150 hit points to every
    member, once a day), **the cairn of the unreturned** (+10 Luck to every member, once a day).
  - **The orc outpost** (source E2): three hide shelters round a fire; "You have found an Orc Outpost.  Put it to the
    torch?" calls A3's `x7.orc_outpost` (500 experience, outpost_burned 116160) and hides the shelters; burnt on every
    load after (`evt:outpost_state`). Its chest (level 1) is one spot with it. Two placed Orcs (11030); no Orc Guard
    (A2's Act I count).
  - **XD-05's back gate** at (88, 100) in the hillside, facing west: two leaves (chb1dl mirrored), torches; barred
    until x1-tam.back_gate (110051), then sealed (rubble) until XD-05 names `entrance:x7_gate`; the gate opens to it
    on its own once XD-05's installed studio.yml has it (`places.has_arrival`). The orcs' den beside it (chest level 1,
    "Crude furnishings ... Pillage?", xeen/aaze0022:1).
  - Landmarks: slag heaps, charcoal pits, an overturned ore cart, a broken ore wagon in the Red River Basin (6,000
    rule), the east lookout (roofless), a dragon's bones on the range's east end.
- **The Red Dwarf Range**: ridges and peaks 2,700-3,200, bare and broken; the Firestone road up its valley from X4
  (1,312) to **the Firestone Gap** (2,300), a saddle between a 2,950 and a 3,050 peak. The Gap's signpost warns
  ("North: Mount Firestone. Dragons. Turn back.", D-40 change 4: its north arm and its click); the obelisk on the
  north lip (`obelisks.x7`). The cairn and the miner's adit (cache level 3) on the Firestone road.
- **The north** (wasteland ground; MM6's volcanic rock and lane S's basalt boulders `xeen_basalt1-3`):
  - The lava river from the crater's notch down the west flank to the lake; **the black bridge** carries the north
    track over it; the knight's remains (level 5) on the tax road.
  - **The lava lake** (1,500) with the cooled-flow island and its causeway: **the Ever-Hot Lava Rock** (A3's
    `q-c14.lava_rock`), 8 placed Lava Golems (11593): 6 on the island, 2 on the causeway, movement Short (about 1,024)
    from where they stand, and lava all round: they stay on the island. The hydras' wallow (level 5) on the south
    shore.
  - **XD-16 the Volcano Cave** at [66, 45] facing west (A7's 384 x 384 mouth in a black rock face), "Enter the Volcano
    Cave?", the demon and devil idols flanking it (A3's `x7.idols`, one spot with the door, D-40 change 5). Since the
    13th session lane S's idol models (`xeen_idol_demon` list id 4007, `xeen_idol_devil` 4008; `places.IDOLS`) in place
    of L3's studio masses: [65.5, 44.3] and [65.5, 45.95], facing 90 (west), on the mouth's flat pad (2,240, no sink),
    256 before the rock face and symmetric about the mouth's axis: the demon's centre 305 from the opening's edge, the
    devil's 390 (its wings, +-282, end 204 off the axis, outside the 384 opening). The cleft path now starts south of
    the devil at [64.2, 46.3] (`land.CLEFT_PATH`), 472 from its centre; the volcano path ends on the axis. Each idol
    clicks for `x7.idols`; the walk clicks both.
    XD-16 is open since 00:37 (13th session): the mouth leads to XD-16's `entrance:x7_mouth`; XD-16's way out lands
    at (512, 9728, 2241) between the idols, clear of both; the walk goes in and back.
  - **XD-17's cleft** at [74, 48] facing west (D-40 question 3): A3's `xd17.cleft` (closed: "Fallen rock chokes the
    cleft. Cool air, and a smell of grass, seeps between the stones."); the rock shows closed or cleared by cleft_open
    (116140, `evt:cleft_state`). No marker within 2,569 of its arrival, no dragon within 4,484.
  - **XD-18 the Dragon Cave** at [56.5, 29] facing south in its crag at the rim (A7's 768 x 640 mouth, footprint
    1,536 x 1,024), "The Dragon Cave smells pretty bad. Are you sure you wish to enter?".
  - **FD-04 the Dragon Tower** on its crag (2,600) over the lake: a black round tower 1,024 across, 2,048 high, a cone
    roof; its gate a doorway of two leaves 384 x 448 on the crag top facing south (A7). Small at its planned distance.
  - **Mount Firestone**: a cone to 4,900, the crater's lava pool at 4,600, the firestone path round its south shoulder
    to the dragon's hoard (level 6) and **the Fire Reflector** on the Fire corner (`m37.reflector_fire`).
  - **The lava cove** (x 68-79, five cells into the north rim): lane S's three `xeen_lavafall` on its south wall at
    x 70.5, 73.5, 76.5 (1,536 apart), pouring north into the stars, each turned 25 toward the signature camera at
    [67, 25] (facing 25 in the scene); the river's north arm feeds them. The near lip does not hide them
    (`output/studio_cal/x7/tour/t3/03-signature.png`).
- **Monsters**: 45 markers (orcs 8 in the south, hydras 19, dragons 18), placed 10; see the figures.

## Figures (`tools/measure.py`, the census of the lane's X6/D3; `run/vw_last.txt`)

| Figure | Target | X7 |
| --- | --- | --- |
| Hostiles at load | trap band 90-110 | **95**: orcs 8 x 2.5, hydras 19 x 2, dragons 18 x 1.5 = 85; placed 10 (8 golems, 2 orcs) |
| Kill XP per member | 76.4k | **75.8k**: Act I 0.44k (the south's orcs, D-40 change 2); Act V 75.3k (hydras 31.2k, dragons 37.0k, golems 7.2k) |
| Markers | 45-70 | 45 (south trimmed 10 -> 8, `X7_SOUTH_MARKERS`) |
| First fight, X1 arrival (69, 107) | 2,000-6,000 | **5,314** |
| First fight, X4 arrival (21, 66) | 2,000-6,000 | **5,485** |
| Cleft's arrival (71.8, 48) | marker >= 2,000; dragon >= 4,000 | 2,569; 4,484 |
| Dragons from the Dragon Cave track / tax office mouth | >= 6,000 | 9,951 / 10,305 (Volcano Cave 7,241) |
| Sablewing's nearest fight | 2,500 | 7,661 |
| POIs (D-40 <= 28) | 22-28 | **22** (eleventh session; chests 7, the two merges) |
| POI spacing | — | nearest-neighbour median 4,099 (1,295-10,363). D-40 accepts it (L1 3,280): the north is sparse by design; the 6,000 rule and the wild-land figure both hold |
| Quiet land | >= 1/3 | 0.60 |
| 6,000 rule | none over 6,000 | farthest 5,931 at (57, 108); 0 tiles over |
| Wild land (D-11.5) | <= 0.16 | 0.106 |
| Relief inside the box | >= 2,500 | 1,408 (the lake shore) to 4,896 (the crater rim) = **3,488** |
| Roads | 1-4 % | 1.9 % |
| Textures (ROADMAP 5.2) | <= 120 | **17/120** distinct BModel face textures, 0 new (MM7 chb/hh, MM6 vlc, cwb) |
| Decorations | — | 1,526 entities: the scatter, lane S's basalt boulders 94 and lava falls 3, the dressing |

POIs by the census (22): XD-16 with both idols; XD-17's cleft; XD-18; FD-04's gate (the tower); XD-05's gate; the
obelisk; the Gap's signpost; the Shrine of Fire; the Well of Speed; the hot spring; the cairn; the Fire Reflector; the
lava rock; the orc outpost with its chest; the orcs' den; the pay chest; the miner's cache; the knight's remains; the
hydras' wallow; the dragon's hoard; the lava fork's signpost; the slope fork's signpost.

## Checks

- `oymap validate` L2, L3, L4: no issues (L4 with `tile_set: lavtyl` and `ash: 40`, merge point 17).
- `oymap build`: built; warnings kept (none an error): the two lava rivers follow the land (no `level`: they run down
  the mountain, as wanted); 1 terrace node in water (a pad corner by a liquid edge, harmless); 8 road cells out of
  squares where roads meet; 5 track cells under the black bridge carry no road (the bridge's deck is the crossing);
  38 of 1,413 scatter decorations found no place (steep ground).
- `oymap audit` (default: dressing, doors, lights) and `--reach --solve --textures`: **0 errors, 0 warnings**
  (`run/audit_default.txt`, `run/audit_w.txt`; 1,082 props checked).
- Dressing check (`x1/tools/dress_check.py`): no door with something before it; barrels in 1 pair.
- Walk (313 steps) and hostility from assets_dev, `--world xeen`: **2 of 2 each** on the 21:58 install
  (`output/studio_cal/x7/run/s3_walk1/2.log`, `s3_host1/2.log`), as on the 21:44 install (`ad_*`). Both passed in a
  scratch root on the lava build before the first install (root deleted).
- **Edges** (A1's travel rows, 2026-11-20; X4 reinstalled 22:15:39 with its east edge open): the walk (346 steps)
  now also crosses the south edge to X1 and back and the west edge to X4 and back, 2 of 2
  (`output/studio_cal/x7/run/e_walk1/2.log`); hostility 2 of 2 (`e_host1/2.log`). X7 has no edge_spans rows, so the
  arrivals are the travel rows' defaults and the walk asserts the map only (`gen_walk.SPANS` asserts the points once
  rows exist). X1's entry window is closed on arrival.

## Texture fit exceptions

None: the audit's texture-fit check reports nothing. Walls are plain tiles (chb1 fieldstone, vlcwl3a black stone,
cwb1 red rock); no storey panel, window or sign texture is laid on a wall; the two-leaf doors are chb1dl wings.

## Dressing exceptions

None: the audit and the dressing check report nothing. (The cleft's fallen rocks stand in its mouth on purpose: the
closed rockfall; they are rocks, not containers, and hide once cleft_open is set.)

## Requests

- **A2**: south trimmed to 8 markers, no placed Orc Guard: recount Act I. X7's `map_rows.yml` comment still says 10
  orc markers and 1 Orc Guard 11032; the placed rows are now 11593 x8 and 11030 x2 (no 11032). Row 9105 is used as
  written (slots 21/40/39, perception 5, MOUNTAINS). Act I: the south's orcs 0.44k (8 markers + 2 placed Orcs); Act V
  75.3k. The Well of Speed goes in the permanent-stat ledger under Act I (D-40 change 8).
- **A3**: every hook the map calls, by name (all already in `quest_hooks.yml`): `obelisks.x7` (the obelisk, Gap),
  `q-c14.lava_rock` (the island's rock), `m37.reflector_fire` (the Fire corner, after "Reflector. Activate?" Yes),
  `x7.orc_outpost` (the outpost's fire after "Put it to the torch?" Yes; also its else text when burnt),
  `x7.shrine_fire` / `x7.shrine_fire_again` (player bit 11339, cleared daily by `evt:daily`), `x7.well_speed` /
  `x7.well_speed_again` (player bit 11338), `x7.watch_note` (the pay chest), `x7.idols` (both idols, one spot with
  XD-16), `xd17.cleft` (the cleft; the map reads cleft_open 116140 and outpost_burned 116160 for the load states).
  Q-C14's `where` ("on the cooled-flow island in the lava lake under the north rim") is already in q-c14.yml. The hot
  spring's and the cairn's lines are the map's own (L1's); give them hooks if they should be yours.
- **A7**: door sites (X east, Y north, Z; facing in MoveToMap units: east 0, north 512, west 1024, south 1536):
  - XD-16 mouth front (1024, 9728, 2250) facing west; X7's arrival from XD-16 (65, 45) = (512, 9728, 2250) facing
    west (1024). Proposed inside name `entrance:x7_mouth`.
  - XD-18 mouth front (-3840, 17408, 2150) facing south; X7's arrival (56, 31) = (-4096, 16896, 2150) facing south
    (1536). Proposed `entrance:x7_mouth`.
  - FD-04 gate (-17920, 16578, 2600) facing south; X7's arrival (29, 32) = (-17920, 16384, 2592) facing south.
    Proposed `entrance:x7_gate`.
  - (Done, eleventh session: XD-05 names `entrance:x7_gate`, the gate is open.) XD-05 back gate (12288, -18432, 2000) facing west; XD-05's exit should arrive at (87, 100) = (11776, -18432, 2000)
    facing west (1024). X7's door names `entrance:x7_gate` (A7's (2176, 13184), floor 320, facing south) and opens on
    its own once XD-05's installed studio.yml has that arrival; until then sealed.
- **A5 (XD-17, the lane)**: XD-17's back passage exits to X7 at (71.8, 48) = (3994, 8192, 2500) facing west (1024);
  the cleft door enters XD-17 at `entrance:x7_cleft` once XD-17 is installed with it.
- **A1**: (Done: the orchestrator's edge_spans of 22:38, asserted by the walk.) X7's edge_spans and outdoor_travels rows (generated): the whole south edge (span -32768..32768) to
  `xeen_x1.odm` at X1's entrance:north_road (2560, 22016, 1824) facing south (1536), 5 days; the whole west edge to
  `xeen_x4.odm` at X4's entrance:east_road (22016, -1280, 1056) facing west (1024), 5 days (L1's days; X6 uses 7).
  X1's north edge arrives at X7's entrance:south_road (69, 107) = (2560, -22016, 1856) facing north (512); X4's east
  edge at entrance:west_road (21, 66) = (-22016, -1024, 1408) facing east (0). Also: the studio's scatter reads only
  the engine's decoration table, so world decorations (`xeen_basalt1-3`) are placed one by one as structures; a
  scatter that reads the world's `models/decoration_data.txt` would let them scatter.
- **A6**: a `maps:` block for xeen_x7.odm in `terrain_materials/world.yml` if wanted: the road pale pebbles (D-40: 3-4
  m of pebbles; today the classic dark road set), the dirt red-brown stony, the wasteland grey ash.
- **S / A6**: an optional warm light at each lava fall's foot (the falls cast no light; none placed). (The idol models
  are in, 13th session.)
- **A6**: the crag's south cliff over the lava lake still reads red-brown (A6's tour `a6/x7mat/sheet_s12.jpg`, shots
  01-02): the lava shore's transition tiles (`lvdr*`) climb the whole cliff because it rises inside one cell of the
  lava. The east flank and the top are basalt. A `maps:` rule giving `lvdr*` on steep slopes the basalt layer would
  finish it without a terrain change.

## Words the studio lacked, and notes

- The view distance's haze fades land beyond about 15,000: from the X1 edge (69, 107) the range (22,000 away) does not
  show; the Gap's saddle reads from the road above the watch (`tour/t3/02-gap_saddle.png`). Mount Firestone shows
  from the cove, the flats and the island, hazy from farther.
- The world rim's void is water at 0 (as every Xeen rim map).
- The scenario Lua has no `PlayerBit`: the walk clicks the shrine and the well twice each instead.

## Original lines (`aaze` references)

- "Enter the Volcano Cave?" (xeen/aaze0017:1): XD-16's question.
- "The Dragon Cave smells pretty bad. Are you sure you wish to enter?" (xeen/aaze0017:0): XD-18's question.
- "You have found an Orc Outpost.  Put it to the torch?" (xeen/aaze0018:3): the outpost; "The Outpost burns well."
  (:4) in A3's hook.
- "Crude furnishings and filthy bedding tell you that orcs have been living in this cave.  Pillage?" (aaze0022:1).
- "Reflector. Activate?" (aaze0021:0): the Fire Reflector.

## What the user should look at (tours `output/studio_cal/x7/tour/t2`, `t3`)

- The signature: the lava cove from its west lip, three lava falls pouring into the stars, the lava river above
  (`t3/03-signature.png`).
- The lava lake with its island and golems; the Dragon Tower on its crag behind (`t3/06-lava_island.png`).
- The Gap's saddle from the X1 road (`t3/02-gap_saddle.png`); the abandoned watch (`t2/03-watch.png`).
- The idols at the Volcano Cave, lane S's models (13th session tour `output/studio_cal/x7/tour/s13/`, sheet
  `sheet_idols.jpg`: front, three-quarter, each close, from the path, dusk).

## Fourteenth session (2026-11-21, A5): XD-17's cleft open, the lava falls' sound

- XD-17 is installed (01:36), so `places.INSIDE['xd17']` is `entrance:x7_cleft`. Once `xd17.cleft` answers yes
  (cleft_open 116140), `thing:xd17_cleft` moves the party to XD-17 at (-7296, 4224, 0), facing east. XD-17's rockfall
  (evt:cleft, the exit preset's window) lands at `entrance:xd17_cleft` (4096, 8192, 2496), facing west.
- AU: one looping `xeen_lavafall_loop` (62525) point source over the three lava falls (`gen.py`, panned, D-48).
- Installed with its bake at 01:38:41 (install_baked.sh). The terrain swap first failed on XD-17's `_blv` ground
  file; it was fixed in `a5/terrain_swap.sh`, rerun with 0 files changed, and leaves 0 stale bakes.
- Audit 0/0. Walk 400 steps 2/2 from assets_dev: the cleft is refused before cleft_open, then with the bit the party
  goes into XD-17 and back by its rockfall (`gen_walk.py`, logs `run/s14_walk1/2.log`; again 2/2 after XD-17's 01:45 reinstall, `run/s14b_walk1/2.log`). Hostility 2/2
  (`run/s14_host1/2.log`).
- Doors still sealed: XD-18, FD-04.

## XD-18 and FD-04 open (2026-11-21, A5 18th session)

- Rebuilt with oymap 06:06; `places.py` wires both now that A7 installed them: the Dragon Cave's mouth (event 40, after
  its question) to XD-18's `entrance:x7_mouth` (384, -3072, 0) facing east; the Dragon Tower's gate (event 66) on A3's
  `q-f1.tower_door` (the Key, 12376; the fail text without it) to FD-04's `entrance:x7_gate` (0, -1280, 0) facing north.
  XD-18's `evt:exit` comes back to `entrance:xd18_mouth` (-4096, 16896, 2144), FD-04's `evt:way_out` to
  `entrance:fd04_door` (-17920, 16384, 2592) facing south, 146 before the gate's face: the walk steps 384 south and back
  from it (the leaves do not catch the party); tour `x7/tour/s18/sheet.jpg`.
- The key's line ("The black key turns ...") is not seen: the hook's SimpleMessage and the MoveToMap run in one click and
  the move wins (told A3). The walk asserts the move, not the line.
- Installed with bake 06:14:59 (`run/install_s18.log`), audit 0/0, 0 stale bakes. Walk 430 steps 2/2 (`run/s18/walk3.log`,
  `walk4.log`: into XD-18 and back, the gate refused, the key, into FD-04 and back), hostility 2/2 (`run/s18/host1/2`).
- X7's doors are all open now.

## Nineteenth session (A5, 2026-11-21)

- The Reflector is one Yes/No prompt with buttons (D-65 B1: a message before a question drops the question's text; D-66 item 6): the look and "Reflector. Activate?" joined, `AskChoiceWithAnswerSteps` written as `lua` effects (the studio's `question` word has only typed answers); Yes calls the hook, No does nothing. Only the Lua changed (odm and scene byte-identical, the bake stays fresh); the walk asserts the joined prompt. Lua installed 07:45:53 (`tools/places.py` `reflector()`, `places.py.pre_s19`). Audit 0/0. Walk 432 2/2,
  hostility 2/2 from assets_dev (`output/studio_cal/a5/s19/x7_*.log`).

## Twenty-first session (A5, 2026-11-21): D-70, the temporary sources once a day

- The Shrine of Fire (player bit 11339) and the cairn of the unreturned (map variable `cairn_used`) go through
  `places.daily()` (`Xeen.usedToday("x7_<thing>")`, every member); the cairn says "(+10 Luck until you rest)"; the
  shrine keeps A3's hooks (x7.shrine_fire still says "until tomorrow": asked of A3). `evt:daily` now resets only the
  hot spring (HP, exempt). Backup `x7/tools/places.py.pre_s21`.
- odm and scene byte-identical: Lua and studio.yml installed 08:26:17, bake fresh; walk 432 and hostility 33 2/2 from
  assets_dev; audit 0/0.

## Twenty-second session (A5, 2026-11-21): D-72, the entrance questions shown

- The Volcano Cave (event 38) and the Dragon Cave (40) asked with `SetMessage` + `AskQuestion`, so the question's own
  text was dropped (D-65 B1). Each is now one Yes/No prompt with buttons (`places.asked_way()`: the `into` under the
  condition `continueStep == 1`, the prompt in `else_effects`), its text the look followed by the source question: "A
  cave mouth breathing heat between a demon and a devil carved in black rock. Enter the Volcano Cave?" and "Scorched
  rock, gnawed bones, and a smell of sulphur. The Dragon Cave smells pretty bad. Are you sure you wish to enter?". Yes
  moves as before, No and Escape stay. The walk (`gen_walk.py` `asked()`) asserts the question in the dialog, answers
  No (still on X7, no dialog), then Yes. Backups `places.py.pre_s22`, `gen_walk.py.pre_s22`.
- The orc outpost (event 22) had the same fault; the orchestrator applied D-72 item 3 to every such prompt. It is now
  one Yes/No prompt with buttons (`places.asked_first()`: the outpost_burned condition and A3's else stay, the effects
  open with the prompt): "Hides stretched on poles round a fire pit, bones and filth everywhere. You have found an Orc
  Outpost. Put it to the torch?". The walk answers No first (116160 still clear), then Yes. Lua and studio.yml installed 08:59:54, audit 0/0, walk 460 and hostility 2/2 from assets_dev (`output/studio_cal/a5/s22/r2/`).
- odm and scene byte-identical: Lua and studio.yml installed 08:55:07, bake fresh; audit 0/0; walk 450 and hostility
  2/2 from assets_dev (`output/studio_cal/a5/s22/`).

## Twenty-third session (A5, 2026-11-21): AU's volcano bed

- AU's session 5 block (`level_generation/sounds/xeen_20261120/review/beds/x7.yml`) copied into
  `output/studio_cal/a5/beds/x7.yml`; `tools/gen.py` `dump()` merges it (`a5/beds/beds.py`; X7's own
  `sound:lavafalls` wins by id, unchanged). Four `xeen_amb_volcano` beds over the hot north strip (volume 0.4) and seven
  `xeen_amb_tundra` range-wind beds (0.25), all `pan: false`, day and night. Sketch diff only `sounds` (1 -> 12); audit
  0/0. Installed with its bake (`output/studio_cal/a5/s23/pipeline.sh`); 0 stale.
- Walk 460 and hostility 33, each 2/2 from assets_dev (`output/studio_cal/a5/s23/x7_*.log`).

## Twenty-ninth session (A5 s29, 2026-11-22, merge point 41 rebuild; run files output/studio_cal/a5/s29/)
- Rebuilt on MP41 and installed with its bake (01:04-01:08). D-91: Sablewing's cave and the pickets' den are
  `form: shelter` (rock back, no 7solid01 door face; depth 256), Sablewing (76.35, 90.05), his fire, pot and bones and the
  den's fire and "The orcs' stash" (83.15, 103.3) under the overhangs; the miner's adit `form: blocked` with "The adit
  has fallen in."; mouths buried (house_doors.bury_mouths_sketch: 1024 -> 384-896 wide). F16: XD-16/XD-17/XD-18/FD-04
  show the entrance window with trans 5016/5017/5018/5065 (`places.asked_way` no longer asks Yes/No), XD-05's back gate
  the standard window. Walk (gen_walk.py: `asked()` = Close then OK, `window()`, touch texts status line or window)
  and hostility pass from assets_dev; audit 0 errors; door_check 0.
- Not done: Q-C14's lava rock (12314) as a ground item: outdoor sketches have no ground-item kind (A1 request); the
  click hook stays. Chests still 9 faces of 7gt002a/b in `oymap things` (A1 asked).

## Thirtieth session (A5 s30, 2026-11-22, merge point 42 oymap; run files output/studio_cal/a5/s30/)
- D-90: the Ever-Hot Lava Rock (12314) is a 3D ground item at LAVA_ROCK (-14848, 10240, 1568) (sketch `items`,
  `gen.py`); the 7rock08 decoration and its `q-c14.lava_rock` click are gone (`places.py`; A3 makes the hook
  `map_gives`). Walk: round to the rock's north-west side (the six lava golems' corpses took the first click), then
  `pick_up`, `has_item`. Backups `*.pre_s30`.
- Installed with its bake 02:03; audit 0; hostility pass; the walk passes on its second run (`s30/x7/playtest2.log`).
- Captures of the D-91 shelters (Sablewing's, the pickets' den, day and night) and the den chest:
  `output/studio_cal/a5/s30/x7_shelters/sheet.jpg`. The den chest still asks a typed "Pillage?" (a chest `question`;
  the studio has no Yes/No buttons for it).
- 2026-11-22 A5 (thirty-first session, orchestrator's decision): the den chest ("The orcs' stash") no longer asks the
  typed "Pillage?". It opens at once like any chest. The source's look is now its status line: "Crude furnishings and
  filthy bedding: orcs have been living under this overhang." (`places.py` `effects`). The walk asserts the chest
  screen and that line (`gen_walk.py`). Installed with its bake 02:43; audit 0, D-85/D-87 0 errors, largest empty
  zone 239 tiles (unchanged); walk and hostility pass from assets_dev. Backups `*.pre_s31`; run files
  `output/studio_cal/a5/s31/`.
