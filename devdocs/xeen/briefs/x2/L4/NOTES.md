# X2 Rivercity and Lake Darzog, L4 (2026-11-16)

The Cloudside hub, a new map with no original, built from `devdocs/xeen/MAPS.md` (X2 sheet, §0 row, original lines),
WORLD_DESIGN.md §3-5, QUESTS.md (M5-M13, Q-C2, Q-C3, Q-C12, Q-C13, Q-C17-Q-C19, Q-C23) and `devdocs/xeen/ACT2_BUILD.md`.
Built and played in MM7's world as a stand-in (`world: mm7`), as X1 and the Act I dungeons. Map file `xeen_x2.odm`,
map_stats 9136 (its row and bolster row from Erathia's, `map_stats.reference: 7out03.odm`: LowerToEqual, MAPS A4),
qbits 110201-110206 used (range 110200-110299), no items of the range used yet (12100 is the planned Skeleton Key).


**2026-11-20 (A5 tenth session, texture fit):** rebuilt with merge point 16's oymap (the L4 unchanged) and installed
with its bake 21:28:32 (A1's lava rows changed the tile table at 21:05:55 and made the 20:21 bake stale). Audit: 0
errors; the texture check reports nothing now that D-41 is live (the half-timber `hhm3b`, `hhm3bw2`, `hhm3el2`,
`hhm3er2a` are `module` panels); the three known coplanar pairs inside MM7's mast model. Walk 455 steps **2 of 2**,
hostility **2 of 2** from assets_dev (`output/studio_cal/a5/fit/x2_*.log`). Texture fit exceptions: none. AU's sounds:
none named for X2.

**2026-11-20 (A5 tenth session, second pass):** Shop signs (A6's texture classes of 21:58: the MM7 `7sg*` signs are pictures meant once): the kit hung them on 96 x 96 boards, showing the 64 x 64 picture 1.5 times (`feature_repeated`); the board now takes the picture's own size from `texture_classes.yml` (`sign_size`). Reinstalled with its bake in the second pass (`output/studio_cal/a5/fit/pipeline2.log`), walk and hostility 2/2 there.

**2026-11-20 (A5 ninth session):** A8's explicit inside points: XD-06 (0, 384, 0) facing 512, XD-21 (-2560, 320, 0)
facing 512 (XD-12 (2752, 0, 0) facing 1024 as before); the walk asserts each arrival. Installed with its bake 20:21:07
(merge point 15 oymap; audit 0 errors, door check included); walk 455 steps **2 of 2**, hostility **2 of 2**
(`output/studio_cal/x2/run/s9_*.log`). For the next install: AU's sounds if any are named for X2 (none yet).

## How it is written

Every project file of L1-L4 is written by `output/studio_cal/x2/tools/gen.py` (the same plan at three levels: L1 the
plan with spaces, links, entrances and a diagram; L2 the specification with POIs, landmarks, bands and landform; L3
with the sketch; L4 = L3 + the lock, the walk and these notes). `playtest.yml` is written by `tools/gen_walk.py` from
the build (house doors from build.json, the dark faces of the doorway and the cave mouth from the export, ground
heights, event numbers from ids.lock.yml). Shared house shapes and the even tree stand are copied from X1's tools into
`tools/kit.py` (X2 imports nothing of X1). Run `output/studio_cal/x2/v.sh` (generate, fmt, validate L1-L4, build into
`output/studio_cal/x2/build`, install X1 and X2 into `output/studio_cal/x2/mount` with their travel rows merged,
terrain material files). `play_mount.sh` makes `output/studio_cal/x2/play_mount` = the mount plus the dungeons the
other agents have built (copied from their mounts, their map_stats rows appended) for the walk and the pictures.
`tools/doors.py` prints the four doors and their outside arrivals from the build (DOORS.md).

## What was built

**Rivercity** (centre about [64, 53]; compacted 2026-11-16, see "Compact town" below): the Great River (576; five
cells wide outside the town, its water nodes 51-55 between the quays) runs west to east through the town between stone
quays (640, two nodes wide) under two terraced halves (1024) held by quay walls of `cnb` stone with
four flights of steps; **the great bridge** joins them, a level stone deck 1024 wide at the terraces' height on four
segment arches (`cwb` deck, `cnb` sides and piers, tall end posts), with the quays passing under its end arches.
- North bank: Bridge Square at the bridge's head, paved (a 16-high court of `t3s2fl`, Steadwick's plaza stone): the
  stopped fountain on a step in its middle, the town mirror, ad boards, three market stalls, the party start; the
  alchemist and a tall house on its sides, the bank, the magic shop and the tavern across the main street. The main
  street east to the river road from Vertigo and west to the lake road, jogging a cell north at its two cobbled cross
  lanes; the north road from the square past the stables; the riverside promenade (dirt) along the terrace's edge.
- South bank: the South Square at the bridge's head, the guild row west of it and the skill row east on the riverside
  row with their doors on the south street, homes across the street, Pray N Pay (nave and round spire) on the south
  road, the back lane behind; the riverside promenade.
- The quays: Captain Nystor's dock house and pier at the town's east end; a fisherman's house on the north quay and a
  ferryman's on the south quay, both beside the bridge, and four warehouses against the south quay's wall; **the
  Robbers' Den's door** (XD-21) in the south quay wall beside the bridge's south abutment; an empty strongbox.
- 13 services open MM7 rows of Steadwick (Erathia, MM7's second town) and Harmondale's guilds under Rivercity's names
  (aaze0030:44-52): Rivercity Smithing (10), Rivercity Armoury (49), Witch's Cauldron (86), The Bubbling Flask (118),
  The Bank (287), Bull's Tavern (241), Street Fightin' (1572), Pray N Pay (312), Guilds of Body (165), Mind (159) and
  Spirit (153), Royal Steeds of Rivercity (462), Captain Nystor's Dock (486, MM7's Lady Catherine with its own routes).
  **30 enterable residences** (MAPS: 30) open Erathia's residence rows 910-945, whose people teach and sell guild
  memberships: the skill row is Arnold's Gym (945, Expert Mace), Martial Training (923, Expert Sword), Lindon's Temps
  (929, Expert Shield), each with a board quoting its Xeen teacher (aaze0030:0-5); the Body, Mind and Spirit guild
  memberships (932, 933, 937) live on the back lane south of the guild row (932 named after Vatawna the Guildmaster,
  aaze0030:12). 9 more houses are plain (no door event: five homes and the four warehouses), as shipped towns have.
- 18 townsfolk (MM7 peasants) and 8 guards: pairs at both bridge heads, singles on the square, streets and quays.
- Style: one family (Harmondale's `hh` kits, MM7): timber and grey stone with shingle roofs, darker than Vertigo's
  cream plaster; Pray N Pay and the guilds in stone.

**The land** (plateau 1024; the height range of the square 0 to 2,816 with the rim, land 640 to 2,816):
- West, **Lake Darzog** (two lake bodies round the island), its east shore Medin's hut and jetty, Crodo's second bottle
  on the south shore, a ruined cottage with a chest, the obelisk on the south-west shore; the **wooded island** (768)
  with **Darzog's Tower** (XD-12): a dark round tower in three set-back storeys (`cwb1`, red cone roof, about 2,900
  high), a black iron door on its east side facing the island's jetty, a chest by the jetty; **three Young Dragons**
  (60) fly round it (Medin's lake beasts, a trap for this level).
- North-west, **the ogres' hills** (to about 2,800) with the north river's gorge from X4 into the lake: the ogres'
  timber bridge on the west road, the **Ogre Lair** (XD-27) as a grey rock cave mouth in a bluff, the ogres' fire,
  skulls and bones, the boulders they threw into the river below (Q-C23), the ogres' boulder (Might 30).
- North, **farmland**: hedged fields with crop rows, orchards, five farmsteads, the farm well, two **evil-ranger
  camps** (a tent, a fire, a chest, five rangers), the Shrine of Electricity on the north-east hill, a ruined
  watchtower with a chest.
- South, **the fairy woods** (even stands of Tularean trees, 0.13 a cell): Danulf the Faery King's ring of six
  trilithons with an altar, mushroom fairy rings, Tito's chapel with a holy well (+25 HP) and an elven grave field, the
  Sage's Fountain (+2 Intellect, once), the sprites' egg hollow (the stolen Wand of Faery Magic), a hunters' old camp.
- The woods' **dark south end**: a bog of dead trees before the rim, the **Temple of Yak** (XD-06): a stone front with
  a columned porch between two towers, against a rise, torches and skull piles; a fouled well (poison), a burial cairn
  with a chest.
- **The world rim** along the south: the land ends in a 900 cliff at y 104 above water at 0 standing for the stars
  (as X1's east rim), boulders along its lip; Ligono the Spirit on the cliff top in the south-west, his skull among the
  rocks at the south-east (Q-C19).
- Edges and ways: east the river road to Vertigo (X1, arriving at X1's west start), west the lake road to X3 (Erathia
  as the stand-in, one way), north the farm road to X4 (Tatalia as the stand-in, one way); Captain Nystor's pier: 100
  gold for a ride down the river to Vertigo's creek bank (an event); Medin's boat between his jetty and the island once
  the dragons are dead (qbit 110201, set by a timer event when the dragon group dies).

**Monsters** (MAPS: A 6-12, C 24, lake dragons 60; 135 hostiles; none in the town buffer), MM7 stand-ins:
slot 1 killer sprites = Will o' Wisp family tier 1 (Dancing Light 15), 2-4 a marker, 23 markers in the woods and the
dark end; slot 2 evil rangers = Archer tier 1 (Archer 9), 2-3, 17 markers round the camps, on the farm lanes, by the
east road and the lake shore; slot 3 ogres = Ogre tier 2 (Ogre Raider 20), 2-3, 9 markers at the river crossings only.
Placed: 10 rangers at the two camps (Archers and Bowmen 19), the lair's Ogre Chieftain (28) and two Raiders, five
Wisps (23) before the temple, the three lake dragons, four lone wanderers. **49 spawn markers in 6 encounter areas,
about 136 monsters** (town_feel's estimate). Nothing within 4,500 of a town door (gen.py refuses a build that has).
First fights: 4,700 from the east arrival (rangers by the river road), 2,300 from the west (ogres at their bridge),
2,300 from the north.

**Points of interest** (MAPS: 40-50, named 17): 4 dungeon doors; obelisk; Sage's Fountain; Shrine of Electricity;
Danulf's ring; Tito's chapel and holy well; Medin's hut, jetty and boat; the island jetty and boat; Ligono; Ligono's
skull; 2 ranger camps; Nystor's dock and pier; Crodo's bottle; Barok's hut; the mirror; the town fountain; the sprite
eggs; 5 signposts; 4 ruins and graves (3 with chests); the ogres' fire; the hunters' camp; the ogres' boulder; the
river boulders; the ogres' bridge; the fouled well; the farm well; the island chest; 5 farmsteads: about 45.
6 outdoor chests (ranger camps 2, watchtower, shore ruin, cairn, island), each with a reason. 7 wells and fountains,
3 giving something (Sage's +2 Intellect, the shrine +5 Air resistance, the holy well +25 HP; the town fountain +100 SP
once Barok has his pendant), one that poisons.

## Original lines (`output/xeen_review/story/alltext.txt`)

| Line | Where | Reference |
|---|---|---|
| "Get lost. Can't you see I'm drinkin'?" | a cask outside Bull's Tavern | xeen/aaze0030:17 |
| "If Barok ever got his pendant back, this place might charge me for drinks." | a cask outside the tavern | aaze0030:19 |
| "The tavern hired the sorceresses to run Barok out of town." | the same | aaze0030:21 |
| "Now THIS is a wild town." | the same | aaze0030:23 |
| "If you can read this ad, so can your customers." | notice board, Bridge Square | aaze0030:29 |
| "School of Navigation 9N. Mountains in your way? Try due N." | notice board by the north street | aaze0030:27-28 |
| "REAL adventurers try Deep Mine Alpha!" | notice board, Bridge Square | aaze0030:67 |
| "Pray, pay, and be healed today." / "I can't believe the cost of healing these days!" | Pray N Pay's notice | aaze0030:31, :26 |
| "The chest is empty. What did you expect, money?" | the strongbox on the robbers' quay | aaze0030:32-33 |
| "If you say the name of a town to a mirror, it will take you there." / "If you like to fight, say 'Warzone' to a mirror." | the town mirror | aaze0030:68-69 |
| Lindon, Flint and Arnold's offers (gold prices left out) | the skill row's boards | aaze0030:1, :3, :5 |
| Barok's pendant | Barok's hut | aaze0030:34 (and :36 after) |
| Captain Nystor's ride ("I can give ya a boat ride to the Eastern shore for 100 gold pieces") and his ogres | the pier, the dock notice | aaze0030:66, aaze0010:23 |
| Danulf, Tito, Medin | the ring, the chapel, the hut | aaze0011:1-3, :5, :9-12 |
| The sprite eggs ("blue speckled Sprite eggs ... crush the eggs") | the egg hollow | aaze0015:0-1 |
| "No one seems to be listening." | the shrine, used | aaze0015:6 |
| Ligono ("I hate the surf ...", "My skull! Thank you! ...") | the rim | aaze0015:10-12 |
| "Help! I am in Darzog's Tower!--Crodo" | the bottle on the lake shore | aaze0023:19 |
| "The water is cool and refreshing." | the farm well, the Sage's Fountain once drunk | aaze0030:71, aaze0015:9 |

## Measured against shipped maps

**Town feel** (`openyamm-studio/calibration/town_feel.py` on the compact town of 2026-11-16, installed in the scratch
root `output/studio_cal/x2/town_root`; output `output/studio_cal/x2/town_feel.txt`): **0 of 71 figures outside the
shipped ranges** (59 before the density figures were added). The town is found by itself (43 house doors, 53 buildings
in its cluster). Among them: main wall family 0.91, shapes per house 0.6, mirror share 0.51, doors on the compass axes
1.0, town cells of road or dirt 0.72, road turns of 80-100 deg 1.0, junction angles 0.53, straight runs median 2,560 /
longest 5,632 (3,072-5,655), services 13, residences 30, tavern 0.19 from the centre (it faces the square), stables
0.74, boats 0.71, monster groups 52, monsters about 136, 1.07 a hundred land cells, 0.07 along the wild roads, nearest
group to a town door 5,666 (the lone Wisp wanderer moved from [88, 70] to [84, 69], as the skill row moved west), town
fringe/core 1.41 and farthest/core 1.63. The density figures: see "Compact town" below.

**Wild land** (OUTDOOR_REBUILD_PROCEDURE.md "Wild land density"): relief, the standard deviation of height in 8 x 8
cells, median 160, 90th percentile 407 (shipped 131-557 / 727-1219; X1 141 / 409); decorations 14.8 per 100 land
cells, 6.2 of them trees (shipped 3.5-8.3; X1 12.9); land more than 3 cells from anything 0.16 (shipped 0.28-0.60; X1
0.12): busier than the shipped wilds, as X1 is after the user found its meadow "ultra empty". 2026-11-16, measured
again with `output/studio_cal/x2/town2/wild.py` (its own windows and kinds, so its numbers sit a little off the ones
above; before / after on the same script): 13.4 / 13.3 per 100 land cells, trees 5.6 / 5.6, land more than 3 cells
from anything 0.16 / 0.16, relief 170 / 172 and 470 / 470: inside the party's square the wilds are as they were. Past
it: 0 / 323 decorations (see "The land to the edge").

**Audit** (`oymap audit`, `output/studio_cal/x2/audit.txt`): one finding, a pair of faces in one plane inside the
ruined watchtower (759 square units, the `ruin` word's own faces). Build: 70 buildings, 189 doors with an event, 1,273
entities (1,623 after the south pass), 47 spawn points placed (2 markers found no place), 14 warnings (none about
the doors, the town or hostility).

## The walk

`playtest.yml`, 407 steps: a new game on Bridge Square; the mirror, the fountain, the ads; the alchemist, the bank,
the magic shop, the training hall, the tavern, the drunk, the armoury, the smithy, the stables; over the great bridge;
the three guilds, the temple, the skill row; along the promenade and down the quay steps to the dock house and along
the quay to the Robbers' Den (**entered**, XD-21); the lake path, Medin (beasts alive), his boat refused, then with the
dragons dead (qbit 110201) rowed to the island; Darzog's door refused, then with the key (1461) **entered** (XD-12); the
boat back; through town and out by the west road past Barok, over the ogres' bridge and up to the **Ogre Lair
(entered**, XD-27); the west edge's prompt declined; the fairy woods, Danulf's ring, the Temple of Yak refused, then
with the Yak Stone (qbit 110101) **entered** (XD-06); the east edge's prompt **accepted: on X1 at its west start**,
Gunther's errand closed, X1's west edge accepted: **back on X2 at its east start**; Nystor's pier: 100 gold, a ride to
Vertigo. After each dungeon the walk returns by `load_map` (the dungeons' own exits are their agents'). The compact
town (2026-11-16): **passed two of two** on the final build from the scratch root with every dungeon in it
(`output/studio_cal/x2/town2/run/walk_11.log`, `walk_12.log`; `town2/walk2.sh`).

Play: `./tools/run_game.sh --isolated x2 --world mm7 --map xeen_x2.odm --assets "$PWD/output/studio_play/xeen_root" --extra-mount "$PWD/output/studio_cal/x2/play_mount" --visible --seconds 0`
(the lead installs into xeen_root; until then the play mount holds X2, the rebuilt X1 and the four dungeons).

## Compact town (2026-11-16)

The user, after playing: "IMO the city way way too much stretched idk ... like check erathia or top left region of
alvar". Measured first: `town_feel.py` gained the density figures (`town_density`, new lines only; ranges over the
thirteen shipped towns, `town2/shipped.json`). Buildings are house-sized models with the parts of one building merged;
the footprint is the land within 768 of them; the street width runs from the first building on one side of a road
tile's middle to the first on the other.

| figure | Steadwick (7out03) | Alvar (out03) | X2 before | X2 now | shipped |
|---|--:|--:|--:|--:|---|
| buildings in the town | 30 | 40 | 64 | 53 | 12-73 |
| buildings per 100 cells of footprint | 6.3 | 6.0 | 9.2 | 9.3 | 3.6-11.2 |
| built share of the footprint | 0.22 | 0.26 | **0.20** | 0.21 | 0.21-0.37 |
| gap to nearest building, median / p90 | 398 / 1,274 | 530 / 754 | 384 / 638 | 368 / 552 | 162-744 / 411-1,358 |
| middle to nearest middle, median / p90 | 1,178 / 2,328 | 1,449 / 2,023 | 1,180 / 1,413 | 1,152 / 1,436 | 913-2,233 / 1,265-2,850 |
| town extent (box) | 13,768 x 11,376 | 25,560 x 12,028 | 17,280 x 16,784 | 12,960 x 14,736 | |
| extent per building | 2,285 | 2,772 | 2,129 | 1,898 | 1,413-3,576 |
| street width house to house, median | 2,464 | 992 | 1,408 | 928 | 512-3,168 |
| dirt lane width, median (not judged) | 2,480 | 2,720 | 1,680 | 1,248 | 1,472-2,912 |
| largest open circle (the square) | 2,851 | 5,100 | 3,456 (dirt) | 3,045 (paved) | 1,802-5,602 |
| farthest service from the middle | 8,539 | 12,196 | 8,921 | 7,934 | 3,918-16,598 |
| service to service, median of pairs | 6,595 | 4,574 | **10,504** | 8,658 | 2,909-8,789 |
| core radius | 3,540 | 4,803 | **7,174** | 6,242 | 2,626-6,552 |
| middle of the town to a building (not judged) | 0 | 109 | 1,662 | 1,648 | 0-767 |

What made the old town read stretched was not the gap between neighbours (it was Steadwick's) but its spread: 64
buildings in three long rows a side, the services 10.5k apart on average, an 11-cell band of quays, river and
promenades with nothing on it between the halves, a bare dirt square. What changed (`tools/gen.py`, "Rivercity"):
- The river between the quays narrowed to its water nodes 51-55 (49-55), the north terrace edge from 46.5 to 48.5:
  the halves 9 cells apart (11), the bridge 9.5 cells (11.5), still four arches over both quays. The south terrace
  edge, the south quay and the Robbers' Den's door did not move.
- 51 town plots (61; 14 plain houses fewer, 4 warehouses more) in rows half a cell apart (walls 352-384 apart), back to back over half-cell alleys, the main
  street 1.5 cells between house fronts, jogging a cell north at its two cross lanes (the junction and run figures);
  the town 25 x 29 cells (34 x 33). Plots on the half-cell grid (the studio's rule), group indices renumbered.
- Bridge Square paved: a 16-high court of `t3s2fl` (Steadwick's plaza stone) with the fountain on a step in its middle
  (`tiers`), the mirror, three market stalls, barrels; the alchemist and a tall house on its sides, the bank, the magic
  shop and Bull's Tavern across the main street. The party starts on it ([64, 45], facing the fountain and the bridge).
- The guild row and the skill row moved to the south bank's riverside row, their doors on the south street; the
  stables to the north road behind the tavern; four plain warehouses on the south quay; the fisherman's and the
  ferryman's houses beside the bridge's ends.
- Kept: the 13 services (MM7 rows as before), 30 residences on Erathia's rows (24 named, 3 guild stewards, the skill
  row), the quays, the dock at the east end, the travel edges and their starts, the dungeon doors.
- The lone Wisp wanderer moved from [88, 70] to [84, 69] (its `hostile` flag untouched) so that a monster group stays
  within the shipped 6,796 of a town door after the skill row moved west.
- The walk's town part (`tools/gen_walk.py`) follows the new streets.

## The land to the edge (2026-11-16)

The user: "the trees suddenly are 'cut off' when the party map bounds end but map itself continues". The cause was
X2's generator only: every scatter polygon lay inside the party's square (cells 19-109), so 950 decorations stood
within 23,008 of the middle; the studio places scatter anywhere (no studio change, no calibration rebuild). Now nine
bands beyond the square (`scatter:rim_trees_*`, `rim_rocks_*`, `rim_boulders_*`: hill trees north-west and west,
farm trees north-east and east, the fairy woods' kinds south-west and south-east; 4.5-7 trees a hundred cells, rocks on
the steep ground) carry 323 decorations to the map's edge; the north road's valley (x 62-70), the west road's (y
37-43), the east road and river (y 42-57) and the north river's gorge are left open; nothing south of the world rim.
The west and east ridges ended at the rim's cliff in a 2,000-2,700 cut (a mesa seen from the woods); they now end at y
94 and a 1,100 shelf runs to the rim (`frame.rim`). Pictures from inside looking out at every side:
`output/studio_cal/x2/town2/shots/edges_final/` (sheet `edges_final_sheet.jpg`; before: `edges_before/`).

**The south (2026-11-16, the lead's review: "the south is still bare").** The land between the woods and the world
rim west and east of the dark end was flat grass to the cliff (the rolling ground is held flat within 7 cells of the
rim; the shore and woods stands stopped at y 79 and 91). Now: six heath knolls along the rim (`height`, 260-420 high,
clear of Ligono's rock, his skull, the temple and the cairn); windswept heath west (x 19-46, y 79-100) and east (x
80-109, y 91-101 and x 98-109, y 66-91: trees 4-5 a hundred cells in clumps, shrubs `bush07`/`bush02`, `plant02`,
rocks); the cliff's lip planted along its whole length (trees 16 a hundred cells, `bush07`/`bush08`, rocks; open at
Ligono's rock and his skull, and before the temple's rise), five small groves on the lip (one where the dark end's dead
trees give way at x 80), and 18 sea stacks below the cliff. The water beyond the cliff stays empty: it stands for the
stars below the world's rim (the plan's `water:sky`). Pictures: `output/studio_cal/x2/town2/shots/edges_south_final/`
(sheet `edges_south_final_sheet.jpg`: every edge, the corners, `high_s`, `high_sw`, `high_se`, two along the rim;
mid-work `edges_south`, `edges_south2`, `edges_south3`). Wild land inside the party's square after this
(`town2/wild.py`): 18.0 decorations a hundred land cells, 7.0 trees, land more than 3 cells from anything 0.05, relief
173 / 482; 332 decorations past it; 1,623 entities in all (950 before the land-to-the-edge passes).

**Hostility (2026-11-16, the hostility pass's patch applied by hand to the compacted tools):** `relations` makes MM7's
Archer family (202-204: the evil rangers) the party's foe on this map (MMerge's table had them friendly); the walk's
step onto X1's west edge clears hostiles within 3,000 (X1's slot monsters no longer fight each other). Built with the
lead's oymap (merge 40): no hostility warning. `playtest_hostility.yml` (from
`output/studio_cal/hostility/scenarios/x2_playtest_hostility.yml`, unchanged: its arena at (12288, -3072) is east of
the woods, away from the moved town) **2 of 2**; the walk **2 of 2** (`town2/run/walk_21.log`, `walk_22.log`,
`walk_31.log`, `walk_32.log`), from the scratch root with the current X1 reinstalled.

X1 (not changed): its scatter does reach past the square on its three land sides (north 76, west 81, south 67); its
east is the world rim (water). Its north and south ridges run on into the east rim and end there in the same kind of
cut (about 3,400 at the north-east corner, 2,100 at the south-east): a `frame.rim` change in X1's generator would
cure it.

## X1's change (ACT2_BUILD.md "Links between the maps")

`output/studio_cal/x1/tools/gen.py` (X1's project is its output): `door:xd06`, its plan entrance, its sketch point, the
sealed Temple of Yak cave mouth and its two torches and two skull piles removed (the rise and the forest path stay);
`edge:west` leads to `xeen_x2.odm` (was 7out03 Erathia), with `arrival_side: west` and `one_way: true` (the studio
defect below; S8g made it `arrival_side: east`, two-way, 3 days: see the end). Nothing else. Rebuilt as X1's v.sh does, into `output/studio_cal/x2/x1_build` and X2's mount
(`output/studio_cal/x2/x1_v.sh`); X1's own build and the shared xeen_root untouched. X1's `playtest.yml` regenerated by
its gen_walk.py (388 steps; its last step, the west road's prompt, now names "Rivercity and Lake Darzog"): passed four
of four against the mount (`output/studio_cal/x2/run/walk_x1_1.log` to `walk_x1_4.log`; 3 and 4 on the final X1).
Backup of X1's project and tools before the change: `output/studio_cal/x2/x1_backup/`.

## Gaps (what the map cannot say yet), most harmful first

1. **The world rim** is a cliff above water at 0 (the game draws no void, a fall is a swim): E5, as X1.
2. **The mirror network** is not built: the mirror is a portal ring that tells its two lines.
3. **No ship at the dock**: a model of a shipped map cannot be turned, and MM7's ships lie north-south across an
   east-west river. Nystor's ride is an event (teleport to X1's creek bank); the dock house opens MM7's Lady Catherine
   with its MM7 routes, as X1's stables open the J.V.C Corral.
4. **The sorceresses** (Barok's pendant, Q-C2) and the sprites holding Danulf's wand are not built as people: the
   pendant's qbit 110204 is never set (the fountain stays stopped); the wand lies among the eggs.
5. **Teachers**: the skill row's people are Erathia's (Expert Sword, Mace, Shield), not Bodybuilding, Armsmaster and
   Lindon's paid work; the boards quote the Xeen teachers.
6. **Stand-ins**: sprites are Will o' Wisps, the lake dragons Young Dragons, the rangers Archers.

## Words needed (studio) and tool defects

- **Edge travel east-west is written inverted**: `oymap install` writes the target side's word (`left` for west),
  the game reads MMerge's `left` as entering by the target's **east** start (`game/tables/MapStats.cpp:205`). A party
  leaving X2 east arrived at X1's party start ("no start point 'east start'"). Workaround: east-west edges say the
  opposite `arrival_side` and `one_way: true` (the way back would be inverted again), each map writing its own row.
  Up and down are right. **Fixed in S8g (2026-11-16)**: see "Travel two-way again (S8g)" below.
- **`install --mount` takes the tables from the asset root**: installing X1 and then X2 into one mount loses X1's row;
  `install_both.sh` merges the two rows (scratch mount only). **Fixed in S8g**: an install into a mount starts from
  the mount's tables; `install_both.sh`'s merge step is harmless and may go once the lead's build has the fix.
- **A doorway takes the land's height at its middle** (X1 asked for `doorway.floor`): the den's frame stands half a
  cell out on the quay so that its sill is the quay's 640. **S8g**: a doorway's `floor` (the sill's height) now
  exists; this map does not use it yet.
- **Models cannot be turned** (`kind: model`): no ship. **S8g**: a model's `turn` now turns what is taken (tried on
  Erathia's Lady Catherine, `output/s8g/turn/shots2/`); this map has no ship yet.
- **`ruin`**: two faces of one ruined round part lie in one plane (the watchtower). Not fixed in S8g: the caps of two
  walls overlap at a corner when both happen to stand at the same height (faces 78 and 84 at 1511/1512); the cure is
  mitred cap corners, which would change every built ruin.
- A round part's door wall is counted from the south (wall 3 of 12 faces east): not said in the schema.
- Scenario: `setup_shortcut: {kind: grant_item}` grants nothing; the `grant_item` step does.

## What the user should look at when playing

- The great bridge from the quays, from the river's ends and from its deck; the quays passing under its end arches;
  the Robbers' door beside its south end.
- Bridge Square (paved since 2026-11-16) and the compact town: does it now read as close as Steadwick and Alvar.
- The rim's ridges past the party's reach: trees to the map's edge, no flat cut at the south-west and south-east.
- The town's density and its one timber-and-grey style against Vertigo's cream; whether the riverfront rows on both
  terraces read as a river town.
- Darzog's Tower over the lake from Medin's jetty, with the three dragons circling (they are level 60: keep off the
  water at level 7-11).
- The fairy woods (even stands, fairy rings, Danulf's stones) darkening into the bog and the Temple of Yak.
- The south rim from the woods' edge and Ligono's rock.
- The ogres' hills: the gorge, their bridge and the cave mouth.

## Pictures

`output/studio_cal/x2/tour/` (`a/` the first tour, `b/` and `c/` the final map; contact sheets `sheet_*.jpg`; tours
`tour.yml`, `tour_b.yml`, `tour_c.yml`); building shots (`calibration/building_shots.py --original 7out03.odm`, thirteen buildings: the services, the dock, the tower, the bridge, three houses) in `output/studio_cal/x2/bshots2/` (index.html, contact sheets; Steadwick's land at the same cameras on the left, no counterpart of a new map; the Ostler house and the Temple of Yak found no clear camera, the tours have them); plan renders `output/studio_cal/x2/pics/` (`plan.png`, `iso.png`,
`sketch_town.png`).


2026-11-16 (compact town, land to the edge): `output/studio_cal/x2/town2/shots/` (same cameras round each town's
middle: `steadwick/`, `alvar/`, `x2_before/`, `x2_final/`, sheet `cmp_aerial_final.jpg`; X2's streets
`x2_final_streets.jpg`; edges `edges_before/`, `edges_final/`). Plan render `town2/sketch_town.png` is a mid-work one.
## Travel two-way again (S8g, 2026-11-16)

The studio now writes the game's word for the arrival side (`left` for an east arrival, `right` for a west one), so
the workaround is undone in `tools/gen.py`: `edge:east` to X1 says `arrival_side: west` (X1's west start) and is
two-way (no `one_way`); `edge:west` to Erathia says `arrival_side: east` (Erathia's east start, as before in the
table: `7out03.odm left`); X1's `edge:west` says `arrival_side: east`, two-way, 3 days. The installed rows are as
before (`xeen_x2.odm ... 7out03.odm left 5 xeen_x1.odm right 3`, `xeen_x1.odm ... xeen_x2.odm left 3`); the builds are
byte-identical. With the S8g studio build both maps were installed into one mount by two plain installs (no merge;
`output/s8g/xx/mount`, played with the four dungeons in `output/s8g/xx/play_mount`): this map's walk 2 of 2 (east edge:
on X1 at (-22016, 9216), its west start; X1's west edge: back here at (21504, 9216), the east start), X1's walk 2 of 2.

## Into the world (2026-11-20, A5)

`IN_WORLD = True` in `output/studio_cal/x2/tools/gen.py` (False rebuilds the MM7 stand-in of 2026-11-16; backup of the
tools and briefs before the change: `output/studio_cal/x2/world_backup/`). Run `output/studio_cal/x2/vw.sh [--install]`
(generate L1-L4, fmt, validate, build into `build_w`, X1's `measure.py`, `dress_check.py`; with `--install` into
`assets_dev` and the terrain material weights and liquid edges). Installed: `worlds/xeen/maps/xeen_x2.*`,
`events/maps/xeen_x2.lua`, `terrain_materials/xeen_x2*`.

What changed:
- `world: xeen`; the map_stats `reference` (Erathia) dropped.
- **Houses**: every door opens A4's house (`HOUSE_XEEN`, from the stand-in's row: 4051-4063 services and the dock,
  4065-4094 residences, A4's names); Barok's, Medin's and Tito's huts are houses 4095, 4096, 4097 (their talk is A3's).
  The mirror calls `Xeen.useMirror(4064)` (A3's continuation form waits for the studio word, as X1's).
- **Monsters** (A2's rows): slots Xeen Sprite 2-3 a marker (2-4 before), Xeen Ranger 2-3, Xeen Ogre 2-3 at Dif 0
  (Ogres only, at the crossings); placed: the two ranger camps Evil Archers 11130 and Evil Rangers 11131, the lair's
  leader and his two an Ogre Brute 11061 each (the Chieftain 11063 is XD-27's boss), the temple's five Killer Sprites
  11531, the lake's three Water Dragons 11640 (Q-C13's trap, 60), the wanderers Ogre 11060, Medusa Sprite 11530 and
  Evil Archer 11130. 47 markers in 5 areas; **142 at load** (`measure.py`: markers x their means + 25 placed; MAPS 135).
  The world's relations.yml holds the families' hostility; the map's own relations keep Ligono's figure peaceful.
- **People**: Danulf (4154, MM7 peasant 371) by his altar (the ring's old message event is gone: his topics are A3's
  Q-C17); Ligono (4155, MM7 Ghost 270, peaceful) on the cliff top in place of the statue.
- **Hooks** (A3, `XeenQuests.hook`): m1.crodo_bottle_lake (the bottle), q-c17.nest (the sprite eggs), q-c19.skull,
  q-c13.medin_boat (the boat's refusal; with qbit 110201 it still rows), q-c2.strongbox (new: the sorceresses'
  strongbox against the east wall of their house on the south quay, `building:quay_houses#5`), x2.bank_chest (the empty
  strongbox on the robbers' quay), x2.ad_deep_mine, x2.ad_customers, x2.ad_navigation (the boards). Darzog's door:
  `evt.GetHeldItemId() == 12100 or XeenQuests.hook("m13.darzog_door")` (the Skeleton Key 12100; the hook has no refusal
  text, so the map's own stays). The fountain reads qbit 110204 (q-c2.done) as before; the temple door 110101.
  Not wired: x2.ad_mountains (a sign by Martin's door, 4076: next pass), q-c18.teacher and q-c23.upriver (A4's houses).
- **Nystor**: the dock house is A4's 4063 (its routes are A4's); the pier's post only quotes him (the 100-gold teleport
  to Vertigo is gone). **His ship waits on a studio word**: a `kind: model` is taken only from a map of the project's
  own world, and worlds/xeen has no 7out03.odm (asked of A1: `from.world`); `SHIP_WORD` in gen.py turns it on (the
  Lady Catherine turned 90 on the pier's east side).
- **Edges**: east to X1 two-way (A2's driver wrote both travel rows: `xeen_x1.odm left 3`, `xeen_x2.odm right 3`);
  west and north sealed: their neighbours and ways in dropped, a sign at each road's end ("flooded" to Lifeforce Lagoon,
  "bridge out" to Castle Burlock).
- **Dressing** (DRESSING.md): the tavern's four patron casks stand as two pairs against its front either side of the
  door (they stood out on the square); every lone barrel got a partner; the town flowers in 5 clumps (6 put one before
  the bank's door). `dress_check.py`: no door with anything before it; barrels 12 pairs, the rest hay, wood and the dock's
  and the north quay's pairs half a cell apart.

Checks with `build-xeen/game/openyamm --world xeen --asset-root assets_dev` (`output/studio_cal/x2/walk_world.sh`):
- the walk (`playtest.yml`, 399 steps, regenerated by `tools/gen_walk.py` for the world: the build's houses, Danulf by
  `interact_actor`, the west edge's sign instead of its prompt, the X1 round trip by the east edge, all four dungeons
  entered; a dungeon not installed is passed by with a note): **2 of 2** (`run/walk_world_11.log`, `_12.log`);
- `playtest_hostility.yml` (new, `tools/gen_hostility_x2.py` from the shared generator: the three families and the
  dragons hostile, none fighting another, the townsfolk and Ligono peaceful): **2 of 2** (`run/host_world_3.log`, `_4.log`).

Build: 15 warnings (none on doors or hostility; the world's continent the studio cannot say, as X1). Textures 52 (cap 120).
POIs about 45 (the strongbox and the two road signs added, Ligono's statue gone). Pictures:
`output/studio_cal/x2/world_tour/x2/` (sheet `sheet_x2.jpg`): Danulf and Ligono stand where they should, the road-end
signs read at the roads' ends, the tavern's casks against its front. Not done: minimap and lighting bake (the bake
waits on the same tile-table fix as X1's), the sorceresses' house and guards (A4, A2).

Kill XP (`tools/xeen/balance.py`, against A2's map_rows slots, which still say sprites 2-4 and ogres tier 2): 13.2k
against 8.2k (1.61). The three lake dragons are 3.15k of it; without them and with the slots above about 8.4k (1.03).
Whether a trap's XP counts in the map's budget is the orchestrator's question.

## Third session (2026-11-20, A5)

- **The mirror** is `function(continueStep) Xeen.useMirror(4064, eventId, continueStep) end` (studio merge point 3
  gives a `lua` effect naming `eventId` its handler's number, event 120). Checked headless with X1's
  (`output/studio_cal/x1/mirror/mirror.yml`, passes, `run1.log`): Vertigo's mirror with nothing else touched shows the
  square; with Rivercity's qbit 119002 it lists Rivercity and lands at (0, 9728); Rivercity's then lists Vertigo
  (touched first) and lands on Vertigo square.
- **`map_stats.continent: 6`** (Cloudside): the fallback-sky warning is gone.
- **The sorceresses' house**: `building:quay_houses#5` (was plain) enters A4's 4098 (Velda 4156, Ysmay 4157: the house
  screen with both). **Q-C2's guards**: two Apprentice Sorceresses (A2's 11184, level 12, placed only) in group 54,
  hidden and hostile, at (72.3, 56.0) and (72.7, 55.5) east of the house; the strongbox's event shows the group before
  the hook (`evt.SetMonGroupBit(54, Invisible, 0)`), so opening it brings them out. The walk proves it: the hidden pair
  is not met on the way to the strongbox (clear_hostiles kills 0), the pendant (12523) is in the party after the
  click, and the next walk kills the two that came out.
- **x2.ad_mountains** on a board beside Martin's south door (house 4076, [75.15, 47.6]); **x2.ad_navigation** moved
  from the square's board to beside the School of Navigation's north door (4069, [53.3, 42.85]); both off their doors'
  sides by more than DRESSING's 288 (`dress_check.py`: no door with anything before it).
- **Minimap**: `assets_dev/worlds/xeen/icons_x2/xeen_x2.png` (X1's recipe; `output/studio_cal/x2/present/redo.sh
  minimap`, work in `present/minimap/`). X1's `prepare_minimap.py` now takes a texture's native size from the extracted
  MM6-MM8 originals when only its x2/x4 art is mounted (MM7's `sgdock`).
- **Checks** (`build-xeen`, `--world xeen`, from `assets_dev`): the walk (426 steps) 2 of 2
  (`run/walk_world_13.log`, `_14.log`), the hostility check (11184 added as a foe and a placed kind) 2 of 2
  (`run/host_world_5.log`, `_6.log`).
- **Kill XP** (`balance.py`, the orchestrator's trap rule): 8.9k against 8.2k, 1.08; the three dragons count in Act VI.
- **Still open**: Nystor's ship (the studio's `from.world`, A1: not in merge point 3), the lighting bake (the tile
  table fix of `tools/lighting/bake_outdoor.py`, not applied; `present/redo.sh bake` refuses MM8's table),
  q-c18.teacher and q-c23.upriver (A4's houses).
- **X8's falls (D-6.4)**: the landing point for a fall from Cloudreach's middle is **(-10240, 8448), water surface
  576** (cell [44, 47.5]), in Lake Darzog's north-east lobe about 1,000-1,300 off the north and east shores; 6,900
  from the nearest lake dragon (placed at [31, 50.5]), 8,000 from Darzog's tower door (-16031, 3014) and more than 4,500
  from the island's shore. Nothing on X2 changes for it (A6 writes the fall's move).
- Pictures in game: `output/studio_cal/x2/world_tour/x2b/` (sheet `sheet_x2b.jpg`; `run_game.sh --isolated`): the
  minimap on the HUD, the sorceresses' house with the strongbox at its east wall, the two boards beside their doors.
- **Lighting bake** (merge point 4): installed `worlds/xeen/maps/xeen_x2.lighting` and `.bake.json` (MM7's tile table;
  `present/redo.sh bake`). The dock's sign `sgdock` has no native BMP under `assets_source/worlds/mm7/textures` (only
  its x2/x4 art; the original is in `assets_source/textures/native_mm6_mm8/mm7/textures/`), so the bake borrows it
  through `--sources present/srcroot` and `stale_bakes.py` lists X2 as stale for that one dependency until the BMP is
  in `assets_source/worlds/mm7/textures` (asked of A1). Checked in game (`world_tour/x2c/`).
- **Ligono leaves** (A3, Q-C19): his surf figure (NPC 4155) is in a group of its own (55); `evt:ligono_freed` (load)
  hides it when q-c19.done (112380) is set. Rebuilt, installed, re-baked; walk 2 of 2 (`run/walk_world_15.log`,
  `_16.log`), hostility (`run/host_world_7.log`). `stale_bakes.py` lists X2 only for `sgdock.bmp` (above).

## Flicker found by the audit (2026-11-20, A5, fourth session)

`oymap audit` (merge point 5) found one pair of faces in one plane in the ruined watchtower (the studio's `ruin`
z-fighting, noted above): two faces of part `t` at (18170, 14146, 1511), 759 square units. `tools/gen.py` now uses
ruin seed 5 (was 3); a scratch build audits clean (0 pairs). Installed with Nystor's ship (below).

## Nystor's ship (2026-11-20, A5, fourth session; A1's merge point 6)

`kind: model` with `from: {world: mm7, map: 7out03.odm, models: [...]}` (`SHIP_WORD = True`): Erathia's ship east of
Nystor's pier, along the river, its click the dock house (4063). Taken models keep their source heights, and Erathia's
keel stands at its sea (0): `raise: 560` sets it 16 into X2's river (576). Moved east to `SHIP_AT` (83.6, 53.4) so that
its stern clears the pier (x 8,102-8,486) and the mooring post (to 8,666): the ship spans x 8,725-11,345. The audit's
three remaining pairs (TRIM2_32a, faces 292/293/295 against 297) are inside MM7's own mast model, the same three pairs
Erathia has. Pictures `output/studio_cal/x2/world_tour/ship/` (tour `tour_ship.yml`): hull, deck, masts and sails draw
MM7's textures. Also A2's D-9.4: the walk checks Barok's Pendant as quest item 12152 (was 12523; `tools/gen_walk.py`).
Rebuilt, installed, terrain materials, minimap and bake redone (`stale_bakes.py`: 0), walk 2/2 (426 steps), hostility
pass (45 steps).

## Fifth session (2026-11-20, A5): the edges to X3 and X4, D-14's dressing

- `X3_LIVE` and `X4_LIVE` in gen.py (both maps installed): the west edge leads to X3's east start (21504, 12288),
  the north edge to X4's south start (16384, -22016) on X4's X2 road (D-11.6); X3's east edge and X4's south edge
  arrive at X2's west start [21, 40] and north start [66, 21]. First fights from them 2,368 (west) and 2,029 (north).
  The walk (`tools/gen_walk.py`) crosses both edges and comes back. A2 wrote the travel rows.
- The obelisk on A3's `obelisks.x2` (the word, its bit and the autonote), not the map's own message.
- D-14 (outdoor dressing): the three errors are gone. Props 13 (the barrel on the south street, decoration 1573) and
  16, 17 (the kegs on the Kettle-Yang and Bank-Flask walking lines, 1580, 1582) are dropped with their partners
  (`DROPPED_PROPS`); props 11 and 14 moved against the quay house's and the spirit guild's walls and, with 15, paired
  along their walls (`PAIR`).

## Dressing exceptions

- Decorations 1554-1557 (two barrels and two casks before Bull's Tavern, y 42.45): the tavern's patrons sit on them
  with their lines (set pieces); they stand 46-56 from the Bank-Tavern-Kettle walking line, which keeps its 128 free.
- Three coplanar pairs inside MM7's own mast model of Nystor's ship (Erathia has them; not dressing).

## Sixth session (2026-11-20, A5): decorations with models

Every placed kind without an outdoor model (A1's list, merge point 8) swapped in `tools/gen.py` for a bound kind of
the same use, same places: the tavern patrons' and the street props' barrels `7dec24` -> `7dec21` (cask, radius 29),
the graves `rock66` -> `rock65`, the ogres' boulder `rock67` -> `rock68`, the fourth fairy ring `mushrm04` ->
`mushrm05`, the coast and lip bushes `bush07`/`bush08` -> `bush03`. Left without a model (no bound kind fits): 2 hay
bales (`haybale2`), 1 woodpile (`7dec12`), Crodo's bottle (`7dec41`). Decorations 1618 (were 1622: four coast bushes
found no place). Audit: dressing clean, the ship's three coplanar pairs as before. Installed 16:28:56, baked 16:46:22 (the first bake call deadlocked: `present/redo.sh` takes the Blender lock itself, so never wrap it in another `flock` on `locks/blender.lock`). Walk 2/2 (`run/walk_s6a.log`, `_s6b.log`) and hostility 2/2 (`run/host_s6a.log`, `_s6b.log`), headless from
assets_dev on the 16:06 binary.

## Seventh session (2026-11-20, A5): Darzog's Tower's arrival point

- A3/A8: X2's tower door (event 96) moved the party into XD-12 at (0, 0, 0); XD-12's NOTES ask for its start (2752,
  0, 0) facing west. `gen.py` now writes `into: {map: xeen_xd12.blv, at: [2752, 0, 0], facing: 1024}`; the walk asserts
  the arrival within 256 of (2752, 0). Installed with its bake through `install_baked.sh` at 17:44:16 (0 stale); walk
  2/2 (453 steps), hostility 2/2 from assets_dev. XD-06's and XD-21's doors still move to (0, 0, 0): each dungeon's
  start is its owner's to confirm.

## Fourteenth session (2026-11-21, A5): X9's fall landing (D-50 change 4)

- `entrance:x9_fall` named at **(-15360, 3072, 768), facing east (0)**, cell [34, 58], inside `zone:island`'s
  keep-clear (`gen.py` `X9_FALL`). D-50's (-14592, 2816) failed its check: 3,874 from the lake dragon placed at
  [36.5, 66] (the nearest, not [31, 50.5]), so the point moved along the island toward the tower door, never into the
  lake: now 4,136 / 4,291 / 5,976 from the three placements (5,976, not 6,800 as first written: the scene's positions,
  corrected under D-54). Points must be whole cells, so it shares XD-12's
  `entrance:xd12_tower` cell. D-50's "placement plus home radius ≥ 4,000" cannot be met anywhere on the island: the
  Water Dragons (11640) move `Long` (wander 5,120) and are placed round the island (DECIDE in the lane report).
- The rebuild was byte-identical in `.odm`, `.scene.yml` and Lua, so only `xeen_x2.studio.yml` (the arrivals list) was
  swapped in (00:52:31); the bake stays fresh (0 stale). Audit: the ship's three known coplanar pairs only.
- X9's fall playtests (from assets_dev, 01:30) land at the point and nobody dies from the fall (about a third of each
  member's HP). But the two nearest Water Dragons (11640, level 60, flying, aggressive) reach the party within
  seconds: one run lost a cleric while waiting 8 s, and 3 of 9 falls showed a dragon hit within 0.5 s. The X9 tests
  read HP right after landing. Moving the point nearer the tower door gains nothing (the island's best point is
  4,210), so this is a design question in the lane report: leash the dragons, land elsewhere, or keep it as a hazard.

## Fifteenth session (2026-11-21, A5): the lake dragons leashed (D-54)

- The three Water Dragons (11640, group 80, hostile, notes unchanged) moved out on the lake and leashed (`gen.py`
  `LAKE_DRAGONS`): [23, 48] (-20992, 8192) `leash: 1024` in the north-west lobe, [19.5, 58] (-22784, 3072) `leash: 768`
  in the west channel, [28, 71] (-18432, -3584) `leash: 1024` in the south lobe; the build places each at the water
  surface (z 576) with the scene's `leash_radius`. Their leash circles are 6,587 / 6,656 / 6,307 from
  `entrance:x9_fall`, 6,147 / 5,985 / 5,997 from Darzog's door and more than 9,700 from X8's lake landing: D-54's
  5,888 (Ice Blast's 5,120 + 768) is met everywhere. The old placements were 4,136 / 4,291 / 5,976 from the landing.
- Sketch diff: only the three actors. `.odm` and Lua byte-identical; the scene changed, so the bake was stale:
  installed with a fresh bake through `install_baked.sh` (01:57:57; 0 stale). Audit: the ship's three known coplanar
  pairs only.
- Playtests from assets_dev (`run/s15/`): walk 2/2, hostility 2/2 (the dragons still hostile), and the new
  `playtest_lake_dragons.yml` 2/2 (`tools/gen_lake_dragons.py`): a level-46 party at `entrance:x9_fall` unhurt after
  30 s and 60 s; after 60 s each dragon within its leash + 256 of home; group 80 killed, `lake_beasts_slain` (110201)
  set by `evt:lake_beasts`, Medin's boat (event 141) rows the party to the island.
- **The leash does not hold a flyer that sees the party** (engine bug, sent to A1): `playtest_lake_dragons_leash.yml`
  puts an immortal party on the north shore 2,816 from the north-west dragon's home. The dragon targets the party and
  circles it at about 2,800, leaving its 1,024 leash: 1,211 from home after 5 s, 4,347 after 30 s, climbing over the
  land (z 768 -> 1,036). Fails 2/2 on merge point 22 (`run/s15/playtest_lake_dragons_leash_*.log`). The two dragons
  that never saw the party stayed exactly at home. No workaround in the map: the falls are safe because the dragons do
  not see the landing, not because the leash holds.
- Darzog's Tower from Medin's jetty re-shot (the named view `landmark:darzog_tower`, (-8704, 3072, 840) looking west;
  `world_tour/s15/sheet_s15.jpg`): the north-west and south dragons read as small shapes to either side of the island;
  the tower reads as before.


## Twenty-third session (A5, 2026-11-21): AU's night beds

- AU's session 5 list (`level_generation/sounds/xeen_20261120/review/beds/x2.yml`) copied into
  `output/studio_cal/a5/beds/x2.yml` (the previous list in `a5/beds/before_s23/`): the night beds `bed_night_*`
  (`xeen_amb_night`, `night_only`, `pan: false`, volume 0.3) at the day beds' points; day lines unchanged. Sketch diff
  only `sounds`; audit as before. Installed with its bake (`output/studio_cal/a5/s23/`, `pipeline.sh`); 0 stale.
- Walk 455 and hostility 45, each 2/2 from assets_dev (`output/studio_cal/a5/s23/x2_*.log`).

## Twenty-sixth session (A5, 2026-11-21): D-85, Danulf's ring

- D-85: six sprite markers moved to small whole-cell circles (`gen.py` `camps`; the split pairs' second markers last,
  so every other area keeps its seed and its marker): nest guards (46, 87) and (46, 88), (45, 80), (69, 81), (68, 78),
  (60, 94). Nearest hostile to Danulf (-3686, -9523) now spawn 2 at 5,989 (was 3,078); three nest guards 1,670-1,688
  from the nest; the fork-to-ring road passes one group (spawn 19, 3,392 off it). 47 markers, slots 23/17/7 as before;
  odm and Lua byte-identical, only the scene's spawns changed. `tools/check_d85.py` (in `vw.sh`) fails a build with any
  hostile within 5,888 of a placed talking NPC. Installed with its bake 19:19:59; audit 0 errors (3 kept); walk 455,
  hostility 45, the new `playtest_danulf_ring.yml` (level-9 party posed at the ring, no clear, no condition in 5 s,
  Danulf talks) each 2/2, lake dragons 1/1 from assets_dev (`output/studio_cal/a5/s26/`). On the old map the ring test
  failed: Brokk Cursed and Petrified within 5 s.

## Twenty-seventh session (A5, 2026-11-21): D-87, ranged disablers at arrivals

- `output/studio_cal/x2/tools/check_d85.py` now also applies D-87 (3): no ranged disabler (monster_data's special
  attack Stone, Curse, Paralyze, Asleep, Insane, Afraid, Uncon, Dead or Errad with a missile attack, or a Paralyze or
  Finger of Death spell; a marker counts if its slot can roll one) within 5,888 of a talking NPC or of any arrival
  point (named arrivals and edge starts, coaches and docks, mirror, Town Portal, edge spans, every Lua move into the
  map, falls). On X2 the Xeen Sprite slot (Medusa Sprite: Stone, Killer Sprite: Curse, both by missile) and the placed
  Killer and Medusa Sprites qualify.
- Danulf, Ligono, the start (mirror, Town Portal), dock, coaches, the three edges, X9's and X8's fall landings, XD-12,
  XD-21, XD-27: all clear (`output/studio_cal/a5/s27/x2_build.txt`).
- **Breach, kept until a decider answers (DECIDE in the lane report):** the XD-06 exit (Temple of Yak; the named
  arrival (-1024, -17408) and XD-06's own move (-1024, -17840)). The temple's five placed Killer Sprites
  (`pop:temple_wisps`, group 63) stand 873-2,885 from it, and the dark-end markers 17, 22, 20 and 21 stand 2,304-4,766.
  Clearing 5,888 would take every sprite out of the temple front and the dark south end: the guards would move about
  5,600 and spawn 17 about 4,600 (the nearest whole cells outside both Danulf's and the exit's circles), so this is
  not a small marker move. `vw.sh` passes `--kept xd06` so a rebuild is not blocked meanwhile; nothing moved.

## Twenty-eighth session (A5, 2026-11-21): D-88, the XD-06 exit

- D-88: temple guards kept (passed on entry), dark-end markers moved.
- `gen.py` `camps`: the sprite marker (60, 94) -> (51, 93) and the dark-end markers (55, 98) -> (49, 99),
  (71, 96) -> (74, 97), (65, 92) -> (69, 85), circles 0.25. Built: spawn 17 (-6752, -14912), 20 (-7744, -17952),
  21 (5056, -16800), 22 (2624, -10816); from the exit points 6,110-7,915 (each at least 5,888 from (-1024, -17408) and
  (-1024, -17840)), from Danulf 6,200-11,374. 22 stands between the (69, 81) marker (2,240) and the (72, 88) pair
  (2,176 and 2,694), not on top of the pair as (69, 88) would (1,375). The nest keeps three guards at 1,568-1,775;
  the fork-to-ring road sees the same markers as before (19 at 3,562, 5 at 4,912). 47 markers, slots 23/17/7, groups
  and sizes unchanged; odm and Lua byte-identical, only the four spawn positions in the scene changed. `gen.py` now
  stops a build with a sprite area within 5,888 of either exit point (`XD06_EXIT`).
- The waiver is narrower: `vw.sh` passes `check_d85.py --kept-group 63` (only the five placed Killer Sprites of
  `pop:temple_wisps` are reported KEPT at an arrival; every marker counts). On the pre-D-88 scene it reports 2 errors
  (markers 17, 22, 20, 21 at the exit); on the new build 0 (`output/studio_cal/a5/s28/`).
- Installed with its bake 20:05:09 (`a5/install_baked.sh`); audit 0 errors (the 3 kept warnings, Nystor's ship); walk 455,
  hostility 45 and `playtest_danulf_ring.yml` 14 steps, each 2/2 from assets_dev (`output/studio_cal/a5/s28/q.log`);
  0 stale bakes.

## Twenty-ninth session (A5 s29, 2026-11-22, merge point 41 rebuild; run files output/studio_cal/a5/s29/)
- Rebuilt and installed with its bake (01:07-01:10). D-89: the Temple of Yak's door (98) opens without the Yak Stone
  (`XeenQuests.hook("q-c12.temple_door")`, then the window). D-90/F15: the sorceresses' strongbox (a crate) holds Barok's
  pendant 12152 as its item (A3's q-c2.strongbox still gives it too until it says map_gives). F8: the Ogre Lair 640 wide.
  F16: trans 5006/5012/5021/5027. F10: the west shore's pair moved (22, 76) -> (22, 88); the rim corner's zone 12,998 ->
  gone (largest 11,983, 502 tiles; `vw.sh` now runs empty_zones and the audit). Walk 449, hostility, Danulf ring, lake
  dragons and leash pass from assets_dev; D-85/D-87 0 errors; audit 0.
- Not done: Ligono's skull 12311 as a ground item (no outdoor ground-item kind, A1 request).

## Thirtieth session (A5 s30, 2026-11-22, merge point 42 oymap; run files output/studio_cal/a5/s30/)
- D-90: Ligono's skull (12311) is a 3D ground item at (16691, -19866, 1024) (sketch `items`); the 7dec20 decoration
  and its `q-c19.skull` click are gone (A3 makes the hook `map_gives`). `gen.py` backup `gen.py.pre_s30`. The walk
  never visited the skull (A3's q-c19 scenario does).
- Installed with its bake 02:01; audit 0; walk, hostility, Danulf ring and lake dragons pass from assets_dev.

## The world's rim as void and hull (2026-11-23, agent `xeen-rimmap-a`; U-12, D-106, D-109, D-112, D-113)

Scripts and logs `output/xeen_rimmap_a/` (`build.sh x2`, `install.sh x2`, `tests.sh`; `x2/run/`). Regenerated twice
(the second from the first build's land, so the rescue's return points follow it) and installed with its bake 15:12.
- **The rim.** The south rim sea `water:sky` is `void:sky` (y >= 105); 32 hull pieces along the edge; the rescue
  (`evt:rim_fall`) has 12 return points along y 101. Shrine of Electricity on an altar (D-103), three campfires feed
  once (D-104); the ruins (watchtower, shore ruin) are closed shells and the camp tents single-sided (F30/F31).
- **Quay walls (F26).** `north_wall_1-4`, `south_wall_1-5`: X1's rule, `raise: BANK - (PLATEAU + BANK) / 2`
  (-192), `height: PLATEAU + 48 - BANK` (432): each stands 576-1072, its foot 64 in the quay, its top 48 over the
  terrace. The cross lanes `LANE_W`/`LANE_E` end a cell short of the step (47.5): their last road cell lay on the
  step and its grading lifted the quay's nodes at the steps' feet to 960 (a dirt mound at the steps, and the walls
  beside the steps took their tops from 960: 1142-1200).
- **farmsteads#2 (F27)** faces north, downhill (the land before its south door stood 88 over the sill).
- **Empty zones.** The void keeps the land's height on its outline, so the rim's last tile row (y 104) is land now:
  the south-east corner lay 12,408 from every monster (521 tiles). The sprite marker (94, 84) moved to (96, 86).
- Checks (build, private root and assets_dev): audit 0 errors, town fit 0, walls 0, doors 0, D-85/D-87 0 (group 63
  kept), empty zones, props support, check_wild clean, house signs 0, `stale_bakes --check` 0, town feel as before.
  `check_faces`: tents and ruins 0; the 4 left are inside MM7's own boat model of Nystor's ship (kept, below).
- Tests from the root (twice) and assets_dev: walk, hostility, Danulf ring, lake dragons, leash pass.
- Captures `output/xeen_rimmap_a/x2/cap_install/` (baked; rim low/along/high/mid day and night, quay walls,
  terrace top, farmstead door, hull from the void day/night, the far void), root `cap_after/`; before
  `output/xeen_rim/before/x2/`.
- Exceptions: `faces.back_to_back` 2 and `faces.coplanar` 2 in `thing:nystor_ship` (MM7's `Boat 201_S` models from
  7out03, not ours). Build warning `gates.road_off` on `thing:ogre_bridge` (its line y 40, the road's tiles 40-41):
  not moved in this rebuild.
- 2026-11-25 (agent xeen-fb4-outdoor4, installed with its bake 11:56): `check_spawn_clear` 9 → 0. `d142_enforce()`
  passes `also=d142.hull_reason(l4)` (rangers 1-4, ogres 5 off the north bound); `common/d142.py standard_ok()` keeps
  moved circles off the districts' houses (rangers 5 to (44, 28), not onto farmstead 1). The Great Bridge's guards at
  x 63.35 / 64.65 (22 from the parapets before), Danulf (56.5, 81.8) north-east of his altar (20 from a ring stone
  before; 5,999 from the sprites' circle), the west lake dragon (20.5, 58) (322 from the west bound before), the ogre
  wanderer (30, 20.5). Every check 0 and every playtest passes (both dragon tests rewritten by gen_lake_dragons.py).
- 2026-11-25 (agent xeen-d167, D-167, issue #45): the sprites' nest (Q-C17, `thing:sprite_eggs`, event 147 kept) is a
  large prop at `SPRITE_NEST` (44.5, 84.0), the dry hollow (land 640) at the heart of the sprite-held west woods, 6,250
  from Danulf: a 12-sided floor of woven twigs (`gkp1flr`, X9's roc nests) 600 across and 56 high with the hook, a rim
  of 14 twig bundles 140 high (`stone_ring`, `same_event_as` the floor) and six dead branches (7dec16, 7dec12) round it.
  The small mushroom at (49.2, 87.3) is gone (stand-in only). Named "Sprite nest" under the crosshair 380-500 from its
  middle on all four sides at 17 degrees down; the interact key there puts the wand on the cursor. Audit, faces and
  props-support findings unchanged against the installed map. Built and checked in a private root only: the install
  and bake go with D-170's rebuild of X2 (the generator carries both).
