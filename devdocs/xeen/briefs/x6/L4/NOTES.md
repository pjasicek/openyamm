# X6 Desert of the Sphinx: L4 (built, installed)

A5, 2026-11-20 (a sub-agent of lane A5's lead; second pass after the lead's review of tour t4). This is the L1 plan
approved by D-31, built as L2-L4 and installed with its lighting bake. The generator is
`output/studio_cal/x6/tools/gen.py`. It reads `gen_l1.py` (L1 itself is not rewritten), `land.py`, `places.py` and
`scatter.py`. Run it with `output/studio_cal/x6/vw.sh`, which generates, formats, validates, builds into `build_w`,
measures (`tools/measure.py`) and runs the dressing check. Install only through `bash
output/studio_cal/a5/install_baked.sh xeen_x6 devdocs/xeen/briefs/x6/L4 output/studio_cal/x6/build_w
output/studio_cal/x6/present/bake_profile.json`; the minimap with `output/studio_cal/x6/present/redo.sh minimap`. The
doors and arrivals are in [DOORS.md](DOORS.md).

## State

**Eighteenth session (2026-11-21, 06:10-): FD-02 open.** A7's FD-02 installed, so `places.dungeon_way('fd02', ...)`
wires `door:fd02`: event 82 runs A3's m40.sphinx_door (item 12372), then `MoveToMap` into xeen_fd02.blv at
`entrance:x6_door` (-256, 0, 0) facing 1024 (west). `entrance:fd02_door` stays (-12288, -10240, 1536) facing 0.
A7's FD-02 exits (06:15) now land there too. Only the door changed (L4 diffed with `run/s18/L4_pre`); `places.py`
notes text (`.pre_s18`). Built with oymap 06:06; audit 0 errors, 0 warnings (`run/s18/audit.txt`). Installed with
its bake 06:16:42; 0 stale bakes. Walk (`gen_walk.py`, `.pre_s18`): the refusal, then with the amulet into FD-02 and
out by `evt:exit_l` and `evt:exit_r`, both arrival points asserted. 351 steps **2 of 2**, hostility **2 of 2**
from assets_dev, game 05:26 (`run/s18/`).

**Sixteenth session (2026-11-21): lane S's sphinx models.** `places.py` `SPHINX_MODELS_LIVE` (on when
`xeen_sphinx_north` and `xeen_sphinx_south` are bound; `X6_SPHINX_MODELS=0|1` overrides) swaps the masses of both
sphinxes for lane S's decorations at the origins of `level_generation/decorations/xeen_sphinx_claude/integration/
sphinx_collision.yml`: north (82.0, 44.0) on the forecourt, facing 180 (`turn: 180`); south (39.5, 84.0), facing 270
(`turn: 90`; the studio writes facing = -turn, merge point 15, so no new word was needed). Each keeps a carrier block
for its two leaves, front in the door plane: north 576 x 200, 612 high; south 200 x 512, 520 high (the narrowest the
door's 96-unit side bays allow, so no carrier wall shows beside the model's frame). Closed barriers on S's body rings
(from -64 to the model's top + 50) and head rings (from 1,200 north / 550 south) keep the party out of the meshes;
the paws' gap and the hoard mound stay open. Audit 0 errors, 0 warnings (the 16 kept Sphinx warnings are gone with
the masses). Installed with its bake 02:51:58 (`install_baked.sh`); walk 326 steps 2/2 and hostility 2/2 from
assets_dev (`run/s16b_*`); tours `tour/s16/` and `tour/s16b/sheet_s16b.jpg` (both sphinxes, both doors; the carrier
reads as the stone infill above the leaves inside the frame, which stays until A1's paired leaves go 512 high).
`stale_bakes.py` lists only `xeen_dd16` (A8's; not X6).

- **13th session: XD-20 open and the sand-falls' sound; installed with its bake 23:39:43, then 23:43:43** (merge
  point 20's oymap and game, 23:40:17). The arena gate leads to XD-20's `entrance:x6_yard` (256, 0, 0) facing east
  (A2's row 9121; `places.INSIDE['xd20']`); XD-20's yard door brings the party back to (12288, -15872, 1504). A1's E9:
  sketch.yml `sounds` holds one `xeen_sandfall_loop` (AU, 62505) in the middle of the three falls (28.5, 84),
  radius 4,500, inner 1,800 (the row's ends inside it), volume 0.6, looping: one source, so three copies of one noise
  loop never comb (`gen.py`). Checked in a window run with `OPENYAMM_AUDIO_TRACE=1` from (35, 86):
  `play source=assetInstance ... xeen_sandfall_loop.wav result=started positional=1` (`run/s13_audio/trace.txt`).
  Audit 0 errors (the 16 kept Sphinx warnings). Walk 326 steps **2 of 2** (into XD-20 and out by `evt:yard_l`) and
  hostility **2 of 2**, from assets_dev on merge point 20 (`run/s13b_*`). The sand worms (11440-11442, now with
  lane S's model) come from the map's slot 1 markers (20); nothing is placed by hand. FD-02 stays sealed.
  A7: XD-20's ways out `evt:victors_r`, `evt:yard_l`, `evt:yard_r` set facing 0 (east, into the gate); only
  `evt:victors_l` faces west (1024).

- **Eleventh session: XD-14 and XD-15 open; installed with its bake 22:29:19** (`output/studio_cal/x6/run/s11/`).
  Castle Basenji's gate ("Castle Basenji.  Enter?" Yes) leads to XD-14's `entrance:x6_gate` (0, -1280, 0); the
  Sphinx's door to XD-15's `entrance:x6_paws` (0, 256, 0) with `xeen_sphinx_stir`. A3's q-c9.door has `once`
  (112180) and answers false after the first time, so the door's condition is `any: [qbit 112180, the hook]`
  (`places.dungeon_way`): the first click with the amulet runs the hook, every later click goes straight in. Only
  these two doors changed (L4 diffed against the tenth session's). Audit 0 errors, the 16 kept Sphinx warnings.
  Walk (320 steps) **2 of 2** from assets_dev (`run/s11_walk1.log`, `s11_walk2.log`): into XD-15 with the amulet, out
  by `evt:exit_e` to (9216, 9728, 1409), in again without a second hook run, out by `evt:exit_w`; into XD-14 and out by
  its gate (`evt:exit_left`) to (-13312, 15104, 2593). Hostility **2 of 2** (`s11_host*`). The headless runs cannot
  hear the stir; it is in the installed Lua after the move. XD-20 (`entrance:x6_yard`) and FD-02 stay sealed.
- **Re-baked 21:24:38** (the same build reinstalled with a new bake: A1's lava rows changed the tile table at 21:05:55,
  which made the 21:00 bake stale). **Installed 21:00:59** (A5 tenth session, texture fit, merge point 16's oymap 20:45:55) with its bake in the same
  step; `stale_bakes.py` 0. The adobe panels t07b01/t07b04a/t07b06/t07b07 carry a footing band (D-41 `edge`): the
  rows above the lowest are plain t07a01 (`places.plain_upper`, `upper_walls` per box part over 256), and the POOR and
  RICH grades' `parapet` and `gable` are t07a01 (seamless both ways); Saul's hermitage is the ochre grade (its porch
  recess showed the footing panel 1.5 up). Audit: 48 → 0 errors; warnings 16, kept below. AU's sounds:
  `xeen_yard_gate` on the yard gate's four leaves, `xeen_sphinx_stir` with the Sphinx door's sealed line (when
  q-c9.door holds); the open door's sound goes in with XD-15's arrival. Walk 296 steps 2/2, hostility 2/2 from
  assets_dev (`output/studio_cal/a5/fit/x6_*.log`). XD-14/15/20 and FD-02 stay sealed (not installed).
- **Installed 20:10:29** (A5 ninth session, `run/install_s9.log`) with its bake in the same step, built by merge point
  15's oymap (20:03:53); `stale_bakes.py` lists nothing for X6; terrain weights through `terrain_swap.sh`. Minimap
  unchanged (no land change). Since 19:40: the door check's six errors gone (Castle Basenji's and the arena gate's
  chb1dl once per leaf, the Northern Sphinx's egydrlgl once per leaf: the new oymap's two-leaf building doors); D-35
  (below); the edges' `days: 7` in project.yml (A6: as A2's travel rows and edge_spans). Audit (`--reach --solve`,
  dressing, doors): 0 errors, 0 warnings (`run/audit_s9.txt`). Figures unchanged: POIs 25, 135 at load, 42.1k,
  relief 2,720, textures 50.
- **From assets_dev** (A2's row 9104, A4's houses 4301-4305, edge_spans both ways): walk (`playtest.yml`, 296 steps:
  every house screen, the cliff path, the yard gate both ways, the east edge into X4 and X4's west edge back, the
  south edge into X5 and X5's north edge back) **2 of 2** before (`run/ad_walk1.log`, `ad_walk2.log`) and after the
  20:10 install (`run/s9_walk1.log`, `s9_walk2.log`); hostility **2 of 2** both times (`ad_host*`, `s9_host*`).
  The scratch root `output/studio_cal/x6/root` is deleted.
- **D-35 done:** the three sand-falls stand on the cove's north wall (`places.SANDFALLS_SOUTH`, y 84) with `turn: 180`
  (facing 180 in the scene), pouring south toward the crest; shot 11 re-aimed from [38, 96] north-north-west at
  [31, 81]: the falls' three faces and the Southern Sphinx's nemes with its face in profile in one frame, the near rim
  below them. Pictures `output/studio_cal/x6/tour/d35/` (`11-signature.png`, `cove_falls`, `cove_from_sphinx`);
  `tools/gen_tour.py` takes `TOUR_ONLY=a,b` and `tour.sh` `TOUR_SECONDS`. A camera east of the Sphinx (41.5, 97) was
  tried: the crest hides the falls.
- **Next install** (no install for these alone): AU's sounds (`devdocs/xeen/AUDIO.md`): `xeen_yard_gate` on the yard
  gate's clicks, `xeen_sphinx_stir` on the Northern Sphinx's door (q-c9.door's open); `xeen_sandfall_loop` on the
  falls once A1's outdoor emitters (E9) exist. The dungeon doors XD-14, XD-15, XD-20, FD-02 when A7 gives their
  inside points (`places.INSIDE`; a named arrival string is preferred, as D3's dd18).

## Earlier state (eighth session)

- **Installed** 19:40:11 (second pass) with its bake in the same step; terrain weights through `terrain_swap.sh`;
  `stale_bakes.py` lists nothing for X6. Minimap `icons_x2/xeen_x6.png`.
- **Not loadable from assets_dev yet**: there is no map_stats row 9104 (A2's `map_rows.yml` X6 has lock and trap only)
  and no house rows 4301-4305 (A4's `x6.yml` is `planned`). X6's two edges are not in the world's edge_spans
  (the orchestrator's `maps.yml`, from project.yml's `span`/`arrival`), and X4 and X5 still seal their X6 edges.
- **Scratch root**: the walk, hostility and tours run from `output/studio_cal/x6/root`, made by `root.sh` and updated
  by `refresh_root.sh`: a hard-link copy of assets_dev with X6's build and three tables replaced by new files
  (`tools/root_tables.py`): map_stats (X6's stand-in row from project.yml), edge_spans and outdoor_travels (X6's east
  and south edges both ways). Results on the final build:
  - walk (`playtest.yml`, 289 steps): 2 of 2 (`run/p2_walk1.log`, `p2_walk2.log`);
  - hostility (`playtest_hostility.yml`): 2 of 2 (`run/p2_host1.log`, `p2_host2.log`).
  The walk clicks every door; each house's event runs, but no house screen opens until A4's rows exist (noted per
  door). It walks the cliff path from Arie's camp up to Castle Basenji's gate, opens the yard gate from the desert side
  and walks in (and again after a reload without a click), and crosses both edges each way.
- **Once A2 and A4 deliver**: rerun `tools/gen_walk.py devdocs/xeen/briefs/x6/L4 output/studio_cal/x6/build_w
  assets_dev`, then `walk.sh` twice for each scenario from assets_dev.

## What was built

- **Sphinx Wells** on the pan at 1,248, on the caravan road (A4's x6.yml), in the **sandcaster kit** D3 used (MM8
  t07 sandstone in grades, flat roofs behind parapets; MM6's single `hcsmdr` door, the t07 doors being halves of double
  doors): the Last Waterskin (4301, the rich grade, a shade awning on posts, A6's tavern sign) and the caravans' shed
  (4302, flat roof, an open lean-to stall at its back, caravan sign) facing the street; the Well Keeper's House (4303)
  and the Saddle Loft (4304) across it; Old Ibb's roofed well in the street; the camel pen and trough; a date stall;
  barrel pairs against walls; palms. The verges are desert sand (no dirt yards).
- **The oasis**: the pond (water 1,000, the only water) in a hollow, date palms, reeds, the oasis fountain (+2
  Endurance, permanent, once per character); the tracks go round the pond.
- **The Northern Sphinx (XD-15)** at (82, 39) facing south, MM6 pyramid stone, sculpted as a recumbent lion: domed
  haunches at the back, a long body under a rounded (vaulted) back about half the head's height, two long low
  vaulted forelegs reaching to y 45 with 768 clear between, broad battered shoulders, a flat-topped nemes headdress in
  striped stone (`egycol64`) wider than the face and narrowing upward, its two lappets falling in front of the
  shoulders either side of a smooth face (`egywalh`) and brow, a tail along the flank. Head top about 2,400 over the
  ground; no pyramid cap, no windows. The door (two leaves, egydrlgl mirrored) in the breast at y 44; the hoard
  mound by the east foreleg.
- **The Southern Sphinx (FD-02)** buried to its shoulders at (34-40, 83-85) facing east, at the edge of the sand-fall
  cove: the striped nemes and the face out of the sand, a vaulted hump of back and a domed haunch behind; its door
  (two leaves) in the breast.
- **The sand-fall cove (D-31's signature)**: a cove cut into the west rim at x 24-33, y 84-92, its void the stars
  (water 0), its walls cliffs; the dune crest at [38, 96] raised to 2,304. Lane S's three **sand-falls**
  (`xeen_sandfall`) stand on the cove's south wall at x 25.3, 28.5, 31.7 (1,640 apart), pouring north into the cove:
  the studio gives every decoration facing 0, which pours north (below, "Words the studio lacked"). From the raised
  crest the tops of the three falls and the cove are in frame with the Southern Sphinx (`tour/t7/11-signature.png`);
  from the dunes north of the cove they read whole (`12-cove_falls.png`, `13-cove_from_sphinx.png`).
- **Castle Basenji (XD-14)** on its crag at (38, 30) at the north rim (D-31: never moved nearer): grey rubble
  (hwm2wall) with black plank cones, a hall with battlements, a tall keep, four round towers, and a small gabled
  gatehouse on the hall's front holding the gate (two leaves, pointed arch) on the terrace at 2,592. The escarpment
  (bare red-brown rock, cliffs either side) is climbed by the **cliff path** from Arie's camp (the walk walks it).
- **The Warzone coach yard (D-8.1)** at (83-89, 92-98), a pocket in the rock: terrain shoulders north and south with
  cliff faces (560) and red rock scatter, the Barbaric cliff at its back (960); a short fieldstone wall between the
  two west shoulders holds the desert gate (two planked wings a side, A3's x6.warzone_gate / x6.warzone_gate_open);
  Gorm's coach house (4305) against the north shoulder, his closed coach, hay and barrels, a trough; the **arena gate
  (XD-20)** a carved stone portal sunk into the back cliff (its top under the rock), two leaves (chb1dl mirrored),
  two standing torches beside it. No spawn inside or near it.
- **The west**: Saul's hermitage (x6.saul_urn) about 7,000 beyond the Southern Sphinx from the crest, the Shrine of
  Energy by the rim, an explorer's pack at the lip.
- **Devices**: the obelisk on its red knoll; the caravan cairn (x6.caravan_cairn, +Luck once per character a day);
  the sun stones (x6.sun_stones, +Fire resistance once per character a day); the Well of Accuracy (once a day); the
  Waters of Great Power (once a day); the Air Reflector on the rock spit where the rims meet (m37.reflector_air).
- **Chests (7)**: the swallowed wagon, the werewolves' den, the ruined caravanserai, the bone fields' pay chest, the
  explorer's pack, the nest on the big mesa (a crack climbs it), the prospector's camp (a gully path climbs to it).
- **Relief**: the pan (1,250), red mesas, dunes, rolling dry downs, a red ridge along the north rim behind the Sphinx
  (no rim or stars behind it in the arrival view), the Gargoyle foothills (3,000), the Barbaric Mountains (3,712).
- **People**: Arie (4608) at her camp, Saul (4602), the Summer Druid (4601) in her grove, four caravaners.
- **Monsters**: 54 markers on walkable ground in L1's six areas (sand worms 20, Dif 2; werewolves 16, Dif 4; elemental
  golems 18, Dif 2), groups of 2-3; nothing placed; no scorpions (D-31).
- **Sky**: `sky: plansky2` (the clear preset in every weather), no weather; the world's sky.yml gives xeen_x6.odm the
  arid theme (A6). Music 17.

## Measurements (`run/measure_final.txt`, `tools/measure.py`, the D-20 census)

| Figure | Target | X6 |
| --- | --- | --- |
| POIs (D-20 census, D-31 cap 30) | 20-30 | **25** (no click taken off; signposts are arms only) |
| Hostiles at load | 135 | 135.0: 54 markers x 2.5 |
| Kill XP per member | 41.5k ±15 % (D-31 42.1k) | **42.1k** (worms 18.2k, werewolves 12.6k, golems 11.3k) |
| First fight, map-edge arrivals | 2,000-6,000 | X4 road 2,901; X5 road 4,390 |
| Town buffer (D-15) | 2,500 | Sphinx Wells' doors 7,944, its arrival 8,494; the coach yard (house, both gates) 5,315, its arrival 5,039; Arie 5,258, Saul 3,502, the Summer Druid 6,936 |
| Quiet land | >= 1/3 | 0.58 |
| 6,000 rule | none over 6,000 | farthest 5,611 at (73, 24); 0 tiles over 6,000 |
| Wild land, 3 cells from anything (D-11.5) | <= 0.16 | 0.130 |
| Chests | 4-10 | 7 |
| Relief inside the box (D-31) | >= 2,500 | 992 (the oasis shore; the pond 1,000) to 3,712 (the Barbaric peak) = **2,720** |
| Roads | 1-4 % | 2.4 % road tiles |
| Obelisk | 1 | 1 |
| Textures (ROADMAP 5.2) | <= 120, <= 12 new | 50 distinct BModel face textures, 0 new (MM8 t07, MM6 egy/hc, MM7 hwm/chb/hh, A6's xs signs) |
| Audit (`--reach --solve --dressing`) | no errors | 0 errors, 0 warnings; 1,216 props, 5 house doors, 5 walking lines checked |
| Dressing check | | 0 doors with something before them; barrels in 6 pairs |
| `fmt --check` | | L1-L4 clean |

## Texture fit exceptions

- `egycol64` (`tile_seams`, 8): the Sphinxes' nemes and lappets: the gold stripe picture stacked up the tapered
  headdress; its seam lines read as the headdress's banding (set piece).
- `egywla` beside `egycol64` (`family_switch`, 8): the Northern Sphinx's lappets against its stone breast: the gold
  headdress over the stone is the figure, not two wall families.

## Dressing exceptions

None: the audit and the dressing check report nothing.

## Town feel exceptions (D-20)

**Sphinx Wells** (`town_feel.py --small`, `run/tf_wells.txt`, town box -5120,-1536,2560,5120; a private root,
`tools/tf_root.py`, types the house rows from A4's planned `x6.yml`). All 16 out figures follow from a caravan stop of
two services and two homes on a flat pan, as L1 and D-31 approved, and from the lead's desert verges:
- distinct shapes per house 1.0 and mirror partners 1.0: four houses, each its own shape, two pairs across the street;
- straight road run median 4,096: the caravan road runs straight through the hamlet;
- road or dirt cells 0.12 and door to road median 500: the verges and yards are desert sand, not dirt (the lead's
  fix 4); the road is the one cell of the caravan road between the two rows;
- services 2, enterable residences 2, stables rank 1.0, square 1,395, farthest service 1,163, core radius 985: the
  hamlet's size (WORLD_DESIGN 5.1);
- nearest monster group 7,944 and monsters by a wild road 0.0: the pan is quiet by design (D-15's buffer, D-31);
- thematic sprites per cell 0.08: the camel pen's hay and the barrel pairs;
- wells and fountains on the map 11: the checker matches titles (the troughs, the spring); the devices are 5;
- flat terrain share 1.0: the pan.

## Words the studio lacked, and workarounds

- **Decoration facing** (A1): the studio writes every decoration's facing as 0 (`openyamm-studio/core/OutdoorBuild.cpp`
  around lines 443 and 488) and refuses `turn`/`facing` on a decoration. Lane S's sand-fall pours west at facing 90 and
  north at facing 0. The falls therefore stand where pouring north is right: on the cove's south wall. With a facing
  word they move to the cove's north wall pouring south, toward the crest (`places.SANDFALLS_SOUTH`), or onto the open
  west lip pouring west as S's spec says.
- **Tall two-leaf doors** (A1's coming paired-leaf word): a building door takes its width from a bay
  (`walls: {s: [wall, [door, 384], wall]}`) and `leaves: 2` splits it, but stays 256 high; `door_height` only acts on
  a door cut into the roof, which the studio draws as one plain face without leaves or arch. The four dungeon doors
  are therefore two leaves at A7's widths (384, 384, 384, 320) and 256 high, not 512 / 448.
- **A gate with a different event on each side**: the yard gate is four thin wall leaves (two planked wings a side,
  `hhm1b1`, a seamless plank tile), hidden together; walls take no door picture.
- **Terrain colours** (A6's `terrain_materials/world.yml`, MM7's tiles): the classic road is dark pebbles in a bed of
  brown soil, and cliffs read as soil. D-31's pale 3-4 m pebble road and MU-2's X6 ground need a `maps:` block there,
  proposed: `xeen_x6.odm: {road: {library: road_pebbles, tint_scale: [1.35, 1.25, 1.05]}, dirt: {library:
  dirt_cracked, tint_scale: [1.25, 1.1, 0.9]}, wasteland: {library: dirt_cracked}}` (and `rock_red` for the cliffs
  if A6 adds a cliff material per map). The road is one tile wide (the classic road); its pebble band reads about
  4 m.
- **The world rim's void** is water at 0 (as every Xeen rim map): it reads as a grey sea below the lip.
- The scenario Lua has no `PlayerBit`: the walk cannot assert a member's bit (it clicks each device twice instead).

## Gaps and blocks (no stand-ins)

- **A2**: X6's map_stats row 9104 with its slots (project.yml: Xeen Sand Worm Dif 2, Xeen Werewolf Dif 4, Xeen
  Elemental Golem Dif 2, each 2-3 a marker, weights 37/30/33; treasure 3, lock 8, trap 4, perception 4, encounter 10,
  refill 672, music 17); markers 20 worm, 16 werewolf, 18 golem = 135 monsters, kill XP 42.1k a member. For
  `map_rows.yml`: `X6: {lock: 8, trap: 4, perception: 4, environment: DESERT, slots: [{family: sand_burrowers, tier: 2,
  count: [2, 3], weight: 37}, {family: werewolves, tier: 4, count: [2, 3], weight: 30}, {family: elemental_golems,
  tier: 2, count: [2, 3], weight: 33}]}`.
- **A3**: register X6's player bits (A5's proposal): 11330 oasis_fountain (permanent), 11331 shrine_energy
  (permanent), 11332 well_accuracy, 11333 waters_power, 11334 sun_stones, 11335 caravan_cairn (the last four cleared
  daily by the map's `evt:daily_bits`); give `obelisks.cloud_hoard` a fail text ("Sand, and more sand.") so the mound
  answers before the seven words (it is silent today).
- **A4**: un-plan `x6.yml` with the arrivals in DOORS.md. House screens are blocked until then.
- **A7**: the inside points of XD-14, XD-15, XD-20 (and FD-02 in phase 6); the doors' points and sizes in DOORS.md.
- **A1**: a decoration facing (the sand-falls) and a tall paired-leaf door (above).
- **A6**: the terrain materials block for xeen_x6.odm (above).
- **The orchestrator / X4 / X5**: X6's two edges (project.yml `span`/`arrival`), X4's west edge and X5's north edge
  into X6 (their points in DOORS.md); X4 and X5 open their roads when they add them.

## Original lines (`aaze` references)

- "Shrine of Energy.  Pray?" (xeen/aaze0001:0): the Shrine of Energy's question (`thing:shrine_energy`).
- "The water is cool and refreshing." (xeen/aaze0001:4): Old Ibb's well and the Waters of Great Power.
- "Reflector. Activate?" (xeen/aaze0001:17): the Air Reflector's question (A3's hook gives "The Reflector hums
  quietly.", :18).
- "Castle Basenji.  Enter?" (xeen/aaze0001:19): Castle Basenji's gate.
- "Enter the War Zone?" (xeen/aaze0006:4): the arena gate.

## What the user should look at (tour `output/studio_cal/x6/tour/t7`)

- The arrival from X4, Sphinx Wells in sandstone, the oasis.
- The Northern Sphinx head-on (`05`) and from the road (`04`): sculpted from vaulted and battered boxes, it reads as a
  lion with a raised head from the side and as a stylised sphinx front head-on; a sphinx decoration model from lane S
  would read better if wanted.
- The signature from the raised crest (`11`), the cove's falls (`12`, `13`).
- Castle Basenji from Arie's camp and its gatehouse; the coach yard in its rock pocket and the arena portal (`09`,
  `10`).

## Nineteenth session (A5, 2026-11-21)

- The Reflector is one Yes/No prompt with buttons (D-65 B1: a message before a question drops the question's text; D-66 item 6): the look and "Reflector. Activate?" joined, `AskChoiceWithAnswerSteps` written as `lua` effects (the studio's `question` word has only typed answers); Yes calls the hook, No does nothing. Only the Lua changed (odm and scene byte-identical, the bake stays fresh); the walk asserts the joined prompt. Lua installed 07:45:53 (`tools/places.py` `reflector()`, `places.py.pre_s19`). Audit 0/0. Walk 353 2/2,
  hostility 2/2 from assets_dev (`output/studio_cal/a5/s19/x6_*.log`).

## Twenty-first session (A5, 2026-11-21): D-70, the temporary sources once a day

- The Well of Accuracy, the sun stones and the caravan cairn: from player bits (11332, 11334, 11335, cleared by
  `evt:daily_bits`, active member only) to `places.daily()` (`Xeen.usedToday("x6_<thing>")`, every member). The well
  now says "(+10 Accuracy until you rest)" and refuses with "The water is cool and refreshing."; the stones and the
  cairn keep A3's hooks (their texts still say "until tomorrow": asked of A3). `evt:daily_bits` clears only the Waters
  of Great Power's bit (an HP restoration, exempt). Backup `x6/tools/places.py.pre_s21`.
- odm and scene byte-identical: Lua and studio.yml installed 08:26:14, bake fresh; walk 353 and hostility 2/2 from
  assets_dev; audit 0/0.

## Twenty-second session (A5, 2026-11-21): D-72, the entrance questions shown

- Castle Basenji's gate (event 83) and the arena gate (80) asked with `SetMessage` + `AskQuestion`, so the question's
  own text was dropped (D-65 B1). Each is now one Yes/No prompt with buttons (`places.asked_way()`: the `into` under
  the condition `continueStep == 1`, the prompt in `else_effects`), its text the look followed by the source question:
  "Black oak doors under a pointed arch. Somewhere inside, a dog howls, then a man. Castle Basenji. Enter?" and "An
  iron-bound gate cut into the cliff. Beyond it a crowd roars, and something roars back. Enter the War Zone?". Yes
  moves as before, No and Escape stay. The walk (`gen_walk.py` `asked()`) asserts the question in the dialog, answers
  No (still on X6, no dialog), then Yes. Backups `places.py.pre_s22`, `gen_walk.py.pre_s22`.
- odm and scene byte-identical: Lua and studio.yml installed 08:55:03, bake fresh; audit 0/0; walk 371 and hostility
  2/2 from assets_dev (`output/studio_cal/a5/s22/`).
- The Shrine of Energy (event 40) had the same fault; the orchestrator applied D-72 item 3 to every such prompt. It
  is now one Yes/No prompt with buttons (`places.asked_first()`: the once-per-character condition and its refusal
  stay, the effects open with the prompt): "A pedestal crackling with blue sparks under an open roof. Shrine of
  Energy. Pray?". The walk answers No first (no dialog after), then Yes. Lua and studio.yml installed 08:59:50, audit 0/0, walk 380 and hostility 2/2 from assets_dev (`output/studio_cal/a5/s22/r2/`).

## Twenty-fifth session (A5, 2026-11-21): the Sphinx's door shows its line (event 81)

- A3's Q-C9 answer 6: "The amulet grows warm, and the stone between the paws slides aside." was never read. The door
  ran `q-c9.door` (a 2-second status line) and `evt.MoveToMap` in the same click: the line was set on X6, spent its
  time over the load (a minimised run: an 870 ms load frame; nothing on screen 1 s after the move) and XD-15's own
  arrival line ("Cool air, ...", 6 s) took the status bar.
- Now the opening click stays on X6 (`places.northern_sphinx`, s25): condition `qbit 112180`; else
  `if XeenQuests.hook("q-c9.door") then evt.PlaySoundName("xeen_sphinx_stir") end`. With the amulet the first click
  shows the hook's line for its full time with the stir; every later click (112180 set) goes straight into XD-15's
  `entrance:x6_paws`. Without the amulet the hook's refusal box, as before. The hook's `else_text` stays unused.
- The walk (`gen_walk.py`, backup `.pre_s25`) asserts the line in `status()` and 112180 after the first click, still
  on X6 with no dialog, then the second click into XD-15 and back by both exits. odm and scene byte-identical: Lua and
  studio.yml installed 16:32:15 (`output/studio_cal/a5/s25/stage_lua.sh`, `q.sh`), bake fresh, audit 0/0; walk 385
  and hostility 2/2 from assets_dev, 1/1 in the stage first (`output/studio_cal/a5/s25/q.log`).

## Twenty-sixth session (A5, 2026-11-21): D-85

- D-85 (no hostile marker within 5,888 of an outdoor talking quest giver): Saul (4602, (-16845, -3379)) had two dunes
  worm groups at 3,502 and 3,798. `gen.py` (backup `.pre_s26`) now moves any `pop:west_dunes` marker nearer than
  12.5 cells (5,888 + the circle's 512) to Saul to the nearest free walkable candidate beyond (`clear_givers`); the
  area's other seven markers and every other area keep their places. Marker 2 (27, 77) -> (27, 83): spawn 12
  (-18528, -6784) -> (-18880, -10016), 6,942 from Saul; marker 8 (30, 77) -> (29, 83): spawn 18 (-17664, -6784) ->
  (-17792, -9888), 6,578. Nearest hostile to Saul 3,502 -> 6,578. Same 54 markers, slots and groups; only these two
  spawns and circles changed (scene and sketch diffs); odm byte-identical.
- Warnings kept (5,120-5,888, lane rule): Arie (4608) spawn 33 at 5,258 and spawn 20 at 5,621 (`pop:basenji_heights`
  14 and 1). The Summer Druid 6,936. `check_d85.py` at 5,120 passes (`output/studio_cal/a5/s26/x6_d85.txt`, the 5,888
  list in `x6_d85_5888.txt`).
- Measure: first fights X4 road 2,901, X5 road 4,390; town buffer Saul 6,577; quiet land 0.58; wild land 0.131; 6,000
  rule 5,611. Installed with its bake 19:28:16; audit 0/0; walk 385 and hostility 2/2 from assets_dev
  (`output/studio_cal/a5/s26/x6_walk_{1,2}.log`, `x6_host_{1,2}.log`).

## Twenty-seventh session (A5, 2026-11-21): D-87

- **Kept by D-87 (4):** Arie (4608)'s two warnings, spawn 33 at 5,258 and spawn 20 at 5,621 (`pop:basenji_heights`,
  Werewolf slot: Wolfman, Werewolf, Greater Werewolf, melee only, their Disease by melee hits), stay where they are.
  They are not ranged disablers, so D-85's 5,120 is the giver limit on X6.
- D-87 (3): X6 has no ranged disabler at all (slots Sand Worm, Werewolf, Elemental Golem: Uncon, Asleep and the others
  only on melee attacks, no Paralyze or Finger of Death spell). Every arrival point (start and Sphinx Wells, both edges,
  the coach yard and its gate, FD-02, XD-14, XD-15, XD-20, the coaches) and every talking NPC passes:
  `output/studio_cal/a5/s27/x6_build.txt`. No rebuild.
- `vw.sh` runs `output/studio_cal/x2/tools/check_d85.py <scene> 5120` after the build (D-85 at 5,120 plus D-87's
  ranged-disabler rule at 5,888 for givers and arrivals); a breach stops the build.

## Twenty-ninth session (A5 s29, 2026-11-22, merge point 41 rebuild; run files output/studio_cal/a5/s29/)
- Rebuilt twice and installed with bakes. MP41's sphinx doors (whole egydrlgl per leaf; door_check 0). D-91: the
  werewolves' den `form: blocked` with its line (no 7solid01 face); the Summer Druid (4601) on Druidess A 517 with a
  friendly 517 relation. F16: trans 5014/5015/5020/5063; War Zone 80 and Basenji 83 no longer ask Yes/No. D-89: the
  Sphinx opens without the amulet (walk: first click's status line, then the window). Walk step 59 (cairn status) fixed
  by the walk's status-or-window check.
- Left: F10 empty zone at tile [45, 57] (11,192 deep, 601 tiles > 520) in the middle desert between Arie's camp and the
  caravan stop (not on this session's list; needs a marker set, NEXT).

## Thirtieth session (A5 s30, 2026-11-22; run files output/studio_cal/a5/s30/)
- D-91: the Summer Druid (4601) on lane S's friendly row 11929 Xeen Druidess; the map-wide 517 relation dropped
  (`gen.py`, `places.py`; backups `*.pre_s30`). `key_npcs.py --write`: 0 errors.
- F10: new area `pop:pan_west` (slot 1, sand burrowers, two single markers at fixed cells (26, 59) and (36, 55),
  `gen_l1.AREAS` + `gen.py FIXED_SPOTS`; population on `zone:cliff_foot`), outside the oasis and the central pan's
  open polygons, 12.5+ cells from Arie and Saul. Empty zone [45, 57] 601 tiles / 11,192 -> largest zone 429 tiles
  (the south one, [65, 98], unchanged), the pan's 252; land > 6,000 17 % -> 12 %. 56 markers, 140 at load, kill XP
  1.01 -> 1.06, Act IV 1.05. D-85/D-87 0 errors, audit 0.
- Installed with its bake 01:36; walk and hostility pass from assets_dev.

## Rim rebuild (agent xeen-rimmap-b, 2026-11-23; U-12, D-109, D-112, D-114; run files output/xeen_rimmap_b/x6/)

- **The void and the ship.** The regeneration carries the rim kit (`common/rim.py` through `wild.apply`): the rim sea
  and the cove are `void:rim_sea` and `void:cove` (`terrain.void` in the scene), 72 hull pieces along every land/void
  edge, the three sand-falls on the cove's north wall on the land's edge (25.3, 28.5, 31.7 at y 83.98, turn 180). D-114
  (decider, no spillway for sand and lava): the falls keep their 1.6-cell gap, which now holds plain kerbless hull
  faces (`xeen_hullf`, new) instead of nothing, so from the void the sand pours in front of a hull wall with running
  lights (`cap_extra/05`, `06`, `13`). The cove's other walls keep their decks (their inner corners read; D-109).
- **The rescue covers the cove.** `wild.py` `RIM_VOIDS` gains `void:cove`: before, the cove lay outside the rescue's
  polygon (a party in its middle was not lifted) and `check_wild.py` flagged 36 `rim.pit` cells there. 20 return
  points, one new at (37, 88) beside the cove. The wild changes come with it (Arie's campfire event, D-104).
- Studio F30/F31 (ruins, tents) and the rest of the current studio come with the rebuild.
- **Checks** (private root, then assets_dev): audit 0 errors (2 kept warnings, the tavern's back-to-back faces, which
  `check_faces.py` keeps), `void.occupied` 0, door_check 0, wall_check 0, town_fit 0, D-85/D-87 at 5,120 0, empty
  zones pass, props support 0, check_wild clean, check_faces clean, house signs 0, check_exits 0, stale bakes 0.
  town_feel: 19 figures outside the shipped ranges as before (Town feel exceptions above).
- **Tests**: walk (370 steps) and hostility 2 of 2, `x6_warzone_entrance`, `rim_fall`; side quests q-c1, q-c8/q-c9
  normal and `--reload` pass.
- Installed with its bake 15:13; terrain weights; minimap re-rendered and its void painted (`void_minimap.py`).
- **Pictures**: `output/xeen_rim/after/x6/` (rim tour, against `output/xeen_rim/before/x6/`),
  `output/xeen_rimmap_b/x6/cap_extra/` (signature, cove falls by day and night, the falls from the void, the notch
  corners), sheets `output/xeen_rimmap_b/x6/sheet_extra.jpg`, `sheet_rim.jpg`.
- Seen: the rim tour's day shots (no weather command) show the void grey (65, 65, 72): the day's random weather is
  above `voidVisibility`'s 0.4 haze; with clear weather it is 24, 28, 40 as on X1 (`cap_w/`). Engine behaviour by
  D-109 (4), not this map's.
- Side quests crossing it, normal and `--reload` (2026-11-23, after the installs): pass (rim doc §6, map agent MB).
  Story segments and promotions: held for the orchestrator's single chain run after all 12 rim maps.
