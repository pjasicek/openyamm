# D1 Castleview Vale, L4 (2026-11-20, A6)

Built from the approved L1 mock-up (`../L1`, board `level_generation/xeen_art/phase3/d1/board_d1.png`) with the
decider's changes D-23 (and D-5.3, D-9.3, D-14, D-15, D-20), A6's relays of D-26/D-27 (DD-01's outfall grate, four
street grates, Ellinger's five storeys, the `xkshimmer` ghost castle) and A2's kill-XP recount (slots Dif 3/3/2).
Map file `xeen_d1.odm`, map_stats 9108 (A2's row), `world: xeen`, `continent: 6`, music 37, treasure 2, lock 4 /
trap 2, no weather, sky `xeendark1` set on load by A3's `Xeen.applyDarksideSky()`.

## How it is written

Every project file of L2-L4 is written by `output/studio_cal/d1/tools/gen.py` (L1 stays the approved mock-up). It
reads A4's `source/towns/d1.yml` (house ids and names, the jetty's `opens`) and every A3 quest file, and **asserts
that each of the 27 hooks with `map: D1` is used**. Run `output/studio_cal/d1/v.sh [--install]` (generate, fmt,
validate L2-L4, build into `output/studio_cal/d1/build`, X1's `dress_check.py`; install and terrain weights). Other
tools: `tools/measure.py` (hostiles, first fights, the D-15/D-20 POI census, the 6,000 rule; adapted from A5's X4
measure), `tools/gen_walk.py` (`playtest.yml` from the build), `tools/gen_hostility_d1.py` (`playtest_hostility.yml`
from the shared generator), `tools/tour.py`, `tools/sheet.py`, `look.sh <set> <label>` (install, weights, engine tour,
contact sheet in `output/studio_cal/d1/pics/`), `walk.sh` (a scenario headless against `assets_dev`),
`present/bake.sh` (the lighting bake under `flock output/studio_cal/a6_bake.lock`; asserts the tile table
`terrain_tile_data_2.txt`, which is D1's as every Xeen map's), `present/redo_minimap.sh` (X1's minimap scripts). The
neighbours go live by themselves: the east edge when `xeen_d2.odm` is installed (it is), each dungeon door when its
BLV is installed (`D1_<KEY>_LIVE=1/0` overrides).

## What was built

- **Land** (heights above the stars at 0): the vale 1,000-1,250 round the town; Castleview on a level terrace at
  1,150; the Vale Water at 830, rising in a pool at the foot of the Sardaj cliff (84, 18), running south through the
  mill gorge (270 under the vale, shelves at 880) east of the walls, west under Kalindra's rise and over the south rim
  at x 31 by a waterfall word into the stars: **it touches no map edge (D-23)**. The world rim west at x 24 and south
  at **y 104**. Kalindra's rise 1,750 with a 450 cliff to the river; the gemsmiths' shelf and the Western Tower's knoll
  1,600; the Sardaj camp 1,550; the pyramid's knoll 1,250; the north hills to 3,300-3,700 (the mine hills, the Sardaj
  Horn), the mountain road's valley at x 64 (sealed at its top: D6 is not built); the Gemstone foothills north-east.
  The acid pond at 1,080 in a cracked rim.
- **Castleview** (A4's 50 houses + the mirror): a walled town of Darkside grey stone (kit `darkside_town`: poor
  houses t06 boulder under `xlslatemos`, middle t06 with the frieze under t06a05, rich t09 ashlar under `xlslate`,
  services t09 with the carved door; MM8 shop signs, `xlinn`, `xljail`, `xlstorage`). Walls 600 high in MM6 `cswl128`
  with battlements and a walkable top; **two gates (D-23)**: the north gatehouse (two towers, Kalindra's crest
  `xkkalcrst`) and the small round-arched **Queen's Gate** in the south-west wall onto the Kalindra road. Each gate has
  two portcullis leaves (`xkportc`): the outer one runs `XeenQuests.can("m14.gate_open") or hook("m14.gate")`; the
  inner one (D-30) runs `XeenQuests.can("m14.gate_open")`: after `m14.entered` it opens the gate, before it it moves
  the party just outside its gate (north (-512, 10752, 1152) facing 1536, Queen's Gate (-6656, 0, 1152) facing 256)
  and then calls A3's `m14.let_out`, the status line "The guard unbars the gate and waves you out. 'Out is free. In
  takes a pass.'" (a party can be inside first: death wakes at the temple, Sandcaster's caravan
  lands inside). Either opening hides both leaves (the gate stands open), and the load event `evt:gates_open` opens
  both gates once `m14.entered` is set. Texture fit (2026-11-20): each leaf is 256 high, `xkportc` once top to bottom
  with its spikes on the ground (1.5 and 1.25 across, the grille's seamless axis), and a fixed stone lintel
  (`thing:north_gate_lintel`, `thing:queens_gate_lintel`, 256 up to the passage's head) fills the opening above it.
  The gatehouse's towers are plain castle stone with one row of single arrow slits in their top 256 (MM6's grey
  `csaro128`, the wall's own stone: one on the north and south faces, two on the outer side); Kalindra's arms over
  the arch are one whole 128 x 256 panel in a `cstr128` frame. Gate Street (x 63) from the gate to the
  square; the tavern and the inn first inside, the smiths across; magic shop and alchemist on the square's west,
  town hall and bank on its east; the five guilds along the Guild Row (y 58), the temple at its east end; the coach
  yard inside the east wall (the barracks, Kramer's stables); the back lane with the Drawkcab cells, Public Storage and
  its two chest yards; Ellinger's round tower in the north-east quarter (**five storeys** of 384 with string courses,
  1,920 to the eaves, a `xtslatew` cone: the tallest thing in town; D-27). **Lucio's Jetty** (D-5.3): the west wall is
  a thick bastion between y 52.8 and 55.6, a timber deck over it at 1,766 reached by the wall stair from the west lane,
  Lucio's booth (house 4901, shut with A4's closed text until `m30.done`) on the deck and a pier out west into the
  air. The square is paved (t09a02a); Lyle's bench beside the mirror; the sewer hatch (DD-01) by its south-east corner;
  four plain street grates (no event; D-26) on the Guild Row, the gate passage, by the temple and in the square.
- **Outside the north gate**: the travel pyramid on its knoll (`Xeen.travelPyramid("castleview")`, A3's m7), Joe's
  stall and sign (`q-c24.joes_sign`), Justine's lean-to and fire, the Mayor's notice by the gate
  (`q-d1.gate_notice`), the gremlins' burrow under the wall east of the gate (a tiny doorway, `q-d1.court_entrance`,
  then DD-04 sealed).
- **The gates' lanes** (fix of 2026-11-20): no tree or prop stands within 4 cells of either gate, inside or out,
  across the opening's half width plus 0.75 cells for a tree and plus the prop's radius and 64 for anything else
  (D-14); gen.py refuses a structure or a scatter that could fall there and `tools/gate_check.py` (run by v.sh) checks
  the built scene. A short flagstone lane leads in from the Queen's Gate to the back lane.
- **The mill gorge**: the cut rope bridge (two post pairs on the banks and a message; the mended rope bridge and the
  rebuilt mill are hidden models shown by the load event `evt:sabotage` once `q-d1.court_won`, A3's `q-d1.sabotage`),
  the burnt mill on the west rim with the miller's strongbox, **DD-01's outfall grate** (a culvert in the gorge's west
  wall under the mill, D-26: A3's `m16.outfall` (qbit `outfall_unbarred` 111323, lifted from inside in DD-01; its fail text "An
  iron grate, barred from inside."), then a sealed message until DD-01 is installed). The East Bridge (stone, MM6 castle stone) carries the east road over the river at y 60.
- **The Sardaj lands**: Yog's camp (two tents, a fire, a totem), twelve Sardaj in their own group 60, peaceful at load;
  the tents ask "You have found a Barbarian camp. Destroy?" (`q-d12.camp`), which also makes group 60 hostile; the
  load event `evt:sardaj` makes them hostile on `q-d12.hostile` or `camp_burned` (`q-d12.sardaj`). Vespar's tower house
  on his knoll.
- **The west**: the Dark Grove, a dense dark wood (fix of 2026-11-20: 127 close-spaced shipped trees, MM7's dark
  broadleaf `7tree04`/`7tree10`, MM8's dead `tree28`, MM6's swamp `swptree2/4` and a few `tree60` conifers, 0.6-0.8
  cells apart, with ferns and bushes under them), its clearings kept for the arachnoids' seven markers and the three
  electrapede packs, a glade round the great tree and the rope's foot. **The great tree** at [46.2, 34.0]: a tapered
  16-sided BModel trunk in D2's `xdbark` (D2's proportions: foot 760 in radius and 384 high with 15 root buttresses
  320 deep, none on the wall facing the rope; trunk 2,800 higher, taper 0.72 to 547 at its top, 3,184 over the floor)
  carrying **S's great-tree crown** (`xeen_greatcrown`, row 4001, one decoration, `GREAT_CROWN` in gen.py) raised
  2,984 (trunk top - 200: its 539 stub sinks 200 into the trunk) and turned 11.25 degrees so the stub's 16 corners
  stand on the trunk's (the trunk's corners are at 11.25 + k x 22.5, the stub's at k x 22.5; checked at the junction
  in the tour); the crown's top about 6,640 over the grove floor, about 4,650 across; the grove's trees are
  1,000-1,400. The rope (40 wide, 3,900 high, up through the crown's limbs into its leaves, their underside ~3,560 there) hangs at [47.51, 35.45], 1,000 from the
  trunk's middle toward D7's return point: "A rope hangs down out of the sky. Climb?" then `m30.grove_rope`, whose fail
  text is D-23's final refusal; its yes branch says the Skyroads are not open yet. The grove path runs round the
  trunk's south side to the rope's foot. The webbed pack; the electrapedes in three clearings round the tree.
  The **Western Tower** (DD-05) on its knoll: a shaft of seamless castle stone (`cswl128`, Castleview's own; D-41,
  D-42), the skull frieze `hkm3b` once in the top storey under the eaves with the `hkm3elw` windows only there (every
  second face, the north one right over the heretics' rope), one MM6 arrow slit `csaro128` (the wall's own stone) per
  storey up the north face where the rope climbs, `xtslate` cone; its front door runs
  `Xeen.isSet("q-d6.tower_opened") or hook("q-d6.front_door_outside")` (A3's text, the key `west_tower_key` from
  outside sets `tower_opened` and the `door` autonote), then DD-05 sealed; the **heretics' rope** on its north wall
  ("A rope hangs from a window near the tower's top. Climb?", `q-d6.tower_rope`, D-9.3) with the heretic's pack at its
  foot (one spot, D-23). D-42: the rope hangs 24 off the north face, 40 west of the slits' column, from its foot
  past the slits up into the window's glass (its top 4,032; the window 3,904-4,160). The gemsmiths' row (4495-4498) on its shelf with DD-10's west adit above it, each house with a low open workshop
  against its side wall (one slope falling away from the house, its high side 240 under the 256 eaves, four posts, a
  workbench along the house wall and a crate in the back corner; the kit's `forge`, so the weapon smithy in town has
  the same); the Edge Stone
  ("DON'T."); the old west well (+10 Personality, daily); Luna's ring of stones.
- **The south-west**: **Castle Kalindra out of phase, in parts by stage (D-30)**: curtain walls, a three-storey keep
  with an observatory turret and a bell tower, four round towers and a gatehouse. Each stage's parts are built twice:
  in A6's shimmer texture `xkshimmer` (D-27, `GHOST_TEX`; `thing:kalindra_<n>_ghost`, `thing:kalindra_gate`) shown at
  load, and restored in the royal kit's white stone (`hcwall`, `hcwindo`, `hcw1le/re`, `cstr128`, `xtslate` cones;
  `thing:kalindra_<n>`, `thing:kalindra_gate_restored`) hidden at load; load events `evt:kalindra_1..4` (256-259) swap
  them on `Xeen.stageOf("kalindra") >= n` (X3's Newcastle). After A8's table (briefs/dd03/NOTES.md): stage 1 the
  gatehouse and gate, the curtain walls, the keep's ground storey; 2 the keep's second storey and the observatory
  turret; 3 the two south towers (over the dungeon and the cell block: DD-03's dungeon stair is off the south wing);
  4 the keep's third storey with its battlements, the bell tower, the two north towers and their cones, the banner
  (`xkkalban`, restored only, one whole panel on the keep's third storey) and the stable yard's gate, a gatehouse over
  the north curtain whose restored version has an arched oak double door (two leaves of 128 x 256, MM7's wing
  `chb1dl` once on each, the right one mirrored: "The stable yard's gate is barred from inside."; the yard is inside
  DD-03). Texture fit: windows once per face and few (the keep's second and
  third storeys three or four `hcwindo` per side, the towers one row of four in their top 384, the observatory's
  lantern five, the belfry one per side; the out-of-phase version shows no window motif on the shimmer); the gate a
  256 x 256 `xkportc` opening, the arms one whole panel above it in a `cstr128` frame. Both gates run
  `m19.ghost_castle`, then DD-03 sealed (the shown one keeps event 123); a ramp from the forecourt; fallen white stones below the cliff. The obelisk on
  the headland (`obelisks.d1`: DIG).
- **The south**: Pip Melonby's field by the south wall (`q-d9.melon_field`, one Monga melon, once), the wild melon
  patch among the centipedes (`q-d9.melons_south`, three melons), the Well of Might (+2 Might, once per character),
  the prayer shrine on its knoll (+10 to every stat, daily), Falista's hut, Brother Reger's cell (house 4500: the door
  opens on `q-d3.word_said`; else `q-d3.reger_door`, then "What's the word?" palindrome(s) -> `q-d3.reger_word`, any
  other -> `q-d3.reger_wrong`), the castaway's wreck in the shallows with his sea chest and the bottle in the reeds
  (one spot, D-23), his lean-to under Kalindra's cliff, the Vale Falls (a view, no click, D-23).
- **East**: the besiegers' camp with the wrecked trebuchet ("Property of Castleview. Do not touch.") and the gremlins'
  loot, the wayside shrine of Mok (+10 Luck, daily), the east road to D2 (live: 5 days, D2's west start).
- Four signposts (the gate fork, the East Bridge, the west fork, the south fork).

## Monsters (A2's rows)

Slots (map_stats 9108): **Xeen Gremlin Dif 3, 2-3; Xeen Arachnoid Dif 3, 2-4; Xeen Crawler Dif 2, 2-3** (weights
40/30/30). A2's recount of the first install: 0.81 of the 18.3k kill-XP target at Dif 1; Dif 3/3/2 (tier mixes
50/30/20, 50/30/20, 70/20/10) raise it to about 1.0 with the same count (my estimate 0.98-1.0; A2 writes the row).
Placed: four Gremlin Saboteurs at the cut bridge's west end, seven gremlins (4 + 2 Guards + a Saboteur) round the
trebuchet, three packs of Electrapedes (11361, 7) round the great tree; the Sardaj (11100 x7, 11101 x3, 11102, Yog
11103 with NPC 4953) peaceful in group 60. NPC actors: Joe 4956, Justine 4951, Luna 4952.

## Measured

- Size: 128 x 128 cells, the playable vale x 24-110, y 18-104; relief 320-3,744 (the vale 900-1,250).
- Hostiles at load **134.5** (44 markers: E1 siege lines 9, E2 east road 7, E3 grove 7 + heath 6, E4 meadows 10,
  E5 foothills 5; 18 placed); 5 encounter areas; **quiet land 0.75** of the central cells.
- First fight: the pyramid (MAPS: within 3,000) **2,388**; the D2 east start 4,679 (2,000-6,000); nearest hostile to a
  town door 4,868 (buffer 2,500); square 10,357, temple 10,214, stables 7,012, Kalindra's gate 10,890.
- **POIs 51** (D-15/D-20 census: bound events chained within 400, one set piece one spot, residences and NPCs out;
  D-23 cap 55) with D-23's merges (the heretic's pack with the rope, the bottle with the wreck, Lyle's bench with the
  mirror, the falls no click); the Edge Stone's and the west well's clicks kept (not needed). The outfall grate merges
  into the mill and bridge's set piece (D-26).
- **Outdoor chests 6** (the miller's strongbox, the gremlins' loot, the webbed pack, the heretic's pack, the
  castaway's sea chest, the runaway chest); Public Storage's 18 lidded chests are a puzzle, not treasure.
- The grove rope's foot (D7's return point): nearest hostile 1,423 (the electrapedes moved out of the new trunk into
  clearings; was 512).
- 6,000 rule: 10 tiles over 6,000, all on the south rim's lip (y 102-103); land more than 3 cells from anything 0.257.
- Decorations 801 (was 814: S's one crown replaces the 14 `tree69` crowns; 632 before the dense grove).
- Roads 536 of 7,032 land tiles (7.6 %; MAPS 1-4 %): a walled hub with five town lanes and eighteen tracks; kept.
- **Model triangles (second reinstall, 2026-11-20): 25,012 on the map, 19,254 shown at load, 5,758 hidden at load**
  (`output/studio_cal/d1/tools/tris.py`; 19,878 before D-30, 26,900 after the first reinstall). Castle Kalindra 11,014
  (was 5,356): 5,506 shown (the shimmer parts: stage 1 3,152, 2 172, 3 308, 4 1,486, gate 388) and 5,508 hidden (the
  restored parts: 3,152, 172, 308, 1,488 with the banner and the stable gate's door, gate 388), D-30's ~5.4k. The
  other 250 hidden are the mended bridge and mill. Earlier (19,878; was 19,416: the great tree 298, its rope, the workshops): **about 10.2k
  for Castleview** (models whose middle stands on the town terrace, the jetty included; the walls, the gatehouse, 50
  houses, Ellinger's Tower 732) against Ravenshore's ~14k; Castle Kalindra 5,356, the Western Tower 532, a gemsmith's
  house with its workshop 168.
- **Textures: 82 distinct on the models** (cap 120; was 77: Kalindra's restored parts add the royal kit's shipped MM6
  `hcwall`, `hcwindo`, `hcw1le`, `hcw1re`, the stable gate's MM7 wing `chb1dl` (ninth session; was `hcdoor32`), the
  gatehouse MM6's `csaro128`; `xkarrow` is no longer used), **no new texture** for D1: D2's `xdbark` reused on the great tree (registered
  for D1 in source/textures.yml), the kits' `xlslate`, `xlslatemos`, `xlinn`,
  `xljail`, `xlstorage`, `xtslate`, `xtslatew`, `xkarrow`, `xkportc`, `xkkalcrst`, `xkkalban` and A6's `xkshimmer`
  (D-27, shared with DD-03).
- **POIs 52** after the second reinstall (the stable yard's barred gate at stage 4).
- Audit (`--reach --solve --dressing`): 0 errors, 7 warnings (the 7 older coplanar pairs: walls' ends, the jetty
  deck and pier, a street grate (fixed 2026-11-25, issue #45, last section); the observatory's floor lifted 32 off the keep's second storey to keep it at 7).
- `town_feel` (full, 16 services): 73 figures in range, 5 out (below).

- Eleventh session: `entrance:dd05_door` faces south (1536, A8's request; DD-05's door is not live yet, so only the
  published return point changed); rebuilt with oymap 22:38:19, installed with its bake at 23:01:48 (bake
  `output/studio_cal/a6/bake_xeen_d1_225943`), not stale; walk 2/2 (`run/walk_s11_1.log`, `walk_s11_2.log`),
  hostility pass (`run/host_s11.log`); audit with all checks 0 errors, the same 7 coplanar warnings
  (`run/audit_s11.txt`, `run/audit_s11_installed.txt`); `towns.py --strict` 0.
- Ninth session, D-42 (the Western Tower's north face: slits, the window over the rope, the rope's arrival facing
  512): installed with its bake at 21:25:12 (bake `output/studio_cal/a6/bake_xeen_d1_212237`), D1 not stale, walk
  2/2 (`run/s9d_walk_1.log`, `s9d_walk_2.log`), hostility pass (`s9d_hostility.log`), audit 0 errors
  (`run/audit_s9h.txt`), `towns.py --strict` 0. Tour `output/studio_cal/d1/tour/s9_final` (the town, the tower's
  north face from the rope's foot, its window), sheet `pics/sheet_s9_final.jpg`.
- Ninth session follow-up (texture fit, D-41): installed with its bake at 20:55:27 (bake
  `output/studio_cal/a6/bake_xeen_d1_205344`), stale 0, minimap redone; walk 2/2 (`run/s9b_walk_1.log`,
  `s9b_walk_2.log`), hostility pass (`s9b_hostility.log`), audit 0 errors and no texture warning
  (`run/audit_s9f.txt`); POIs 52, hostiles 134.5, triangles 24,854 (19,094 shown, 5,760 hidden). Tour
  `output/studio_cal/d1/tour/s9_town`, sheet `pics/sheet_s9_town.jpg`.
- Ninth session (2026-11-20: double stable gate, named arrivals, the let-out line, the phase sound, DD-03 live):
  installed with its bake at 20:27:30 (bake `output/studio_cal/a6/bake_xeen_d1_202352`), stale 0, minimap redone;
  walk 2/2 (`output/studio_cal/d1/run/s9_walk_1.log`, `s9_walk_2.log`, 859 steps, now with the let-out text and DD-03
  in and out at stage 1), hostility pass (`s9_hostility.log`), audit 0 errors with `--lights --doors`
  (`run/audit_s9.txt`), `towns.py --strict` 0; POIs 52, hostiles 134.5, triangles 25,014 (19,254 shown, 5,760
  hidden). Tour `output/studio_cal/d1/tour/s9`, sheet `pics/sheet_s9.jpg`.
- Second reinstall (2026-11-20, D-30 + texture fit + DD-10A; installed with its bake at 19:18 by
  `output/studio_cal/a6/install_baked.sh`, bake `output/studio_cal/a6/bake_xeen_d1_191639`): walk 2/2
  (`output/studio_cal/d1/run/walk_19.log`, `walk_20.log`, 830 steps: the D-30 case from the temple, M14's gate 2,000
  XP with 111281 and 119021, a save and load, both gates, the hatch and the outfall into DD-01 and out, Ellinger's
  door into DD-02 and out, the adit into DD-10A and out, DD-04 last), hostility pass (`hostility_08.log`), audit 0
  errors (`audit.txt`), `towns.py --strict` exit 0, `stale_bakes.py` 0 stale, minimap redone; POIs 52, hostiles
  134.5. Tours `output/studio_cal/d1/tour/final_d30` (first reinstall: the tree, Kalindra at stages 0/1/2/4) and
  `tour/final_tex` (this one: gates, slits, arms, adit, Kalindra at stages 0 and 4, the stable door, a shop sign);
  sheets `output/studio_cal/d1/pics/sheet_final_d30.jpg`, `pics/sheet_final_tex.jpg`.

## Texture fit (the lane rule of 2026-11-20)

Merge point 16's check (`textures.*` in `oymap audit`, rules `devdocs/xeen/formats/TEXTURE_FIT.md`; A1's first list:
155 errors, 25 warnings on D1), fixed in the ninth session: **0 errors, 0 warnings**.
- The middle houses' `trim` (soffits, fascias, porches, the workshops' posts and soffits) is plain timber `t06a10`
  (was the frieze band `t06b11`, tiled up porch posts, porch floors and the workshops' and the jetty shop's soffits;
  the gable walls `t06b01` keep their own frieze).
- The burnt mill's ruin in `t06a01` (was the strip `t06a06`, tiled across its walls).
- Ellinger's string courses topped in castle stone `csbr128` (was the band `hkm3b` laid flat over the ring).
- The Western Tower (D-41): ashlar shaft, `hkm3b` and `hkm3elw` once, in the top storey (256, was 384: 1.5 times up),
  no storey stacked; the heretics' rope 2,432 high, into the windowed storey. D-42: the shaft in `cswl128` (first
  `gtrlwal1`) so that the slit panels `csaro128` match the stone round them (border 80/71/75 against 80/70/75).

Earlier (session 8):

Measured per face with `output/studio_cal/d1/tools/texfit.py` (a face's texels against the picture's size) and looked
at in the tour. Fixed in this build: the gatehouse's arrow slits (were `xkarrow`'s pale panels in stacked columns),
Kalindra's arms (were a 160-wide strip over a 128 portcullis; the north gatehouse's were stretched to 192 x 192), the
portcullis leaves (a spike row 96 over the ground on 416-high leaves), Kalindra's windows (every second bay of every
row) and its banner (stretched 256 x 384), the shop boards (MM8's 64 x 64 `sg*` pictures on 96 x 96 boards, 1.5 times
each way; `xlinn` 128 x 64 cut and repeated on 96 x 96: kit.py now sizes each board to its picture). Note for the
studio: a bay shows as many texels as it is wide (a 192 window bay shows `hcwindo` 1.5 times), so window and door
bays are 128 here. Left as they are: wall, roof and band textures repeating along their seamless axes; the kit
houses' window and door bays (one picture per face, measured).

## Double doors (the lane rule of 2026-11-20)

Ninth session (2026-11-20): the stable yard's gate is now a double door: `door: {leaves: 2}` on a 256 bay, MM7's
arched oak wing `chb1dl` (the warm stone frame nearest the royal kit's `hcwall`), each 128 x 256 leaf showing it once,
the right one mirrored (the studio since merge point 15); `oymap audit --doors` 0 errors. Earlier text:

D1's doors checked against it (after this reinstall; no reinstall made for it): the town's house doors are single
leaves 118-144 wide (`t06b03`, `t09a03a`, `t09a03c`, `t06a03`), Ellinger's 108 (`hkm1d`) and the Western Tower's 110
(`hkm3dr`) single doors; the two Castleview gates (leaves 384 and 320) and Castle Kalindra's gate (128, both versions)
are `xkportc` portcullis grilles, not winged doors; the hatches and the adit `7solid01`. One to change with the
studio's `door: {leaves: 2}` was tried for the stable yard's gate and dropped: **the studio spreads the whole bay's
width of texels over each leaf** (OutdoorBuildings.cpp `dressedPiece`, `across` = the bay's width), so a 128 wing
picture on a 256 bay shows twice on each 128 leaf, and a 256 double-gate picture is squeezed whole onto each leaf.
Reported to A1. The stable yard's gate is now one 128-wide arched oak door (`hcdoor32`, once); when the leaves map
half a bay each (or a wing picture is fitted per leaf), it can become a double door.

## Town feel exceptions

- Junction branch angles 80-100 deg 0.67 (shipped up to 0.60): a walled grid town; its lanes meet square on.
- Straight road run, median 4,096 and longest 7,168 (shipped up to 3,072 and 5,655): Gate Street and the Guild Row
  run the length of the walls, as a besieged town's main streets do.
- Stables rank from centre 0.88 (shipped up to 0.81): Kramer's coach yard stands inside the east wall (L1, approved).
- Flat terrain share in town 1.0 (shipped up to 0.97): Castleview stands on one levelled terrace inside its walls.

## Dressing exceptions

None (the audit has no dressing warning). Props: barrels in pairs against the tavern's back wall and the stables'
back wall, barrels (`7dec32`, MM7's barrel) against the smithy's back wall, hay against the barracks; none before a
door. (Until session 26 the smithy's pair was `7dec24`, read as an anvil: it is MM7's campfire sprite, which has no
3D model and no sprite files any more, so it failed to load and showed nothing.)

## Original lines (`aaze` Darkside map scripts)

- "This bench reserved for Lyle the Pigeon Feeder" (Lyle's bench; Darkside A3/B3 Castleview, `aaze` castleview
  script, the bench message).
- "Ellinger has a great fondness for boots." (A3's `m17.tower_door` fail text on Ellinger's door).
- "Property of Castleview. Do not touch." is ours; the source's gremlin complaint about Mayor Snarfblad is A4's
  greeting of 4916, and "A rope hangs down out of the sky. Climb?" / "You have found a Barbarian camp. Destroy?" are
  the source's questions at the rope and the Sardaj camp.
- The `aaze` file references of these lines are A3's (in the hooks' quest files); see `research/MM5_DARKSIDE_CONTENT`
  section 4.

## Gaps and words the studio lacked

- No translucent BModel face: the out-of-phase castle is drawn in the shimmer texture (D-27), solid.
- A message shown just before or just after an in-map move (`evt.MoveToMap` on the same map) is gone after the move;
  A3 made `m14.let_out` a status line (`evt.StatusText`), which the walk asserts after each let-out.
- `hidden` structures are invisible and untouchable; `show` restores them (used for the mended bridge and mill).
- The studio has no decoration scale: S's crown is built at the trunk's scale (binding height 3655).

## Doors and arrivals for the other lanes

- **`entrance:north_road`** (D6's arrival, session 15) moved from (64, 19) to (64, 21) = (0, 22016, 1504), facing
  south: at y 19 it lay past the north edge's travel line, so a party arriving from D6 that stepped north was asked to
  travel again at once. A2's `edge_spans` row D6 south -> D1 still says (0, 23040) until A2 regenerates it.

Map units X, Y, Z (cells [x, y]); facing in the game's units (0 east, 512 north, 1024 west, 1536 south).

- Arrivals: `castleview_square` (-512, 4096, 1152) [63, 56] 512 (start, Town Portal, mirror 4467); `castleview_temple`
  (2560, 2048, 1152) [69, 60] 0; `castleview_stables` (3584, 5120, 1152) [71, 54] 0; `castleview_pyramid` (-1024,
  13312, 1248) [62, 38] 1792; `kalindra_gate` (-9216, -3072, 1664) [46, 70] 1024; the east start (D2's edge) (21504,
  2048, 1088) [106, 60] 1024. All five of A4's d1.yml arrivals are where A4 has them.
- Gates: north gate leaves at [62.6-63.4, 43.68] (outer, event 134) and [.., 44.32] (inner, 135), arrival outside
  (-512, 10752, 1152) [63, 43] 1536; Queen's Gate leaves at [51.8-52.3, 62.5-62.9] (outer, 136) and [52.2-52.7,
  62.1-62.5] (inner, 137), arrival outside (-6656, 0, 1152) [51, 64] 256. Before `m14.entered` the inner leaves (135,
  137) move the party to those outside points, then `m14.let_out` (D-30).
- Castle Kalindra's stages: load events 256-259 (`evt:kalindra_1..4`); the restored gate's door is event 254 (same
  hook and way in as 123). Load event 265 (`evt:kalindra_phase`) plays `xeen_phase_shift` at the castle hill
  (-12800, -3072, 2550) when the stage differs from the one last shown on D1 (named map variable
  `kalindra_stage_shown`), not on every load (AU, 2026-11-20).
- Dungeon doors (each runs its hook first; sealed until its BLV is installed) and the points their exits return to
  (the ways in by name, D-37: DD-01 hatch -> `entrance:d1_hatch`, DD-01 outfall -> `entrance:d1_outfall`, DD-02
  Ellinger's door (`m17.tower_door`) -> `entrance:front_door`, DD-03 Kalindra's gate -> `entrance:gate`; DD-04 and
  DD-10A list no entrance and keep their start / coordinates):
  DD-01 hatch [66.5, 57.5] event 145 -> (1024, 3072, 1152) 0; DD-01 outfall culvert [79, 48] event 222 -> (8192, 8192,
  832) [80, 48] 0 (on the gorge floor, facing away from the grate); DD-02 Ellinger's door (3285, 9321, 1152) event
  102 -> (2560, 9216, 1152) 0; DD-03 Kalindra's gate (-10457, -3072, 1760) event 123 -> (-9728, -3072, 1664) 1024;
  DD-04 burrow [68.5, 43.62] event 170 -> (2048, 11264, 1152) 1536; DD-05 front door (-16896, 15254, 1600) event 118
  -> (-16896, 14848, 1600) 1536 (out of the door, facing away from it); DD-05 rope [30.77, 31.72] event 121 -> its return point `entrance:dd05_rope` (-16896,
  16896, 1600) facing 512, away from the wall (D-42; was 1536); DD-10A adit [45, 22] event 187 -> (-9728, 20480, 1600) 1536.
- Other: the travel pyramid [58.5-61.5, 34.5-37.5] event 109; the mirror [63, 53.6] event 144; Kramer's stables door
  (4144, 5376, 1152) house 4464; Lucio's Jetty door (-7232, 5120, 1766) house 4901 (arrival on the deck (-6656,
  5120, 1766) 1024; the build's ground point is under the deck); the grove rope [47.51, 35.45] event 117 (D7 later:
  arrival at its foot (-8192, 14336, 1088) 768, unchanged by the 2026-11-20 fix).
- Live in this build: DD-01's hatch and outfall (`xeen_dd01.blv`, row 9150), DD-02's door (`xeen_dd02.blv`, row
  9151), DD-10A's adit (`xeen_dd10a.blv`, row 9159: into its start (0, 192, 0) facing 512, out by its event 19 to
  (-9728, 20480, 1600)), DD-03's gate (`xeen_dd03.blv`, at stage 1 and later; out by its event 19 to (-9728, -3072,
  1664)), DD-04's burrow (`xeen_dd04.blv`); each walked in and out to its return point. DD-05 sealed.

## What the user should look at when playing

- Both gates: refused without a pass, open with it (north gatehouse and the Queen's Gate); from inside before the
  first entry the guard lets the party out (it lands outside the gate), after it the gates open from inside.
- Lucio's Jetty up the wall stair; Ellinger's five-storey tower over the roofs; the cut bridge and burnt mill.
- The ghost castle in `xkshimmer` from the south bank and the forecourt, and its parts coming back in white stone
  by stage (1, 2, 4 in the tour); the falls off the south rim.
- The Dark Grove: a dense dark wood, the great tree's buttressed trunk and crown over it from the heath, the rope
  hanging from S's crown to its foot; the trunk-crown junction.
- The Queen's Gate from inside and out (a clear lane), the gemsmiths' workshops against their houses.
- Inside the walls before the first entry: the guard's status line after the let-out. Castle Kalindra at stage 4:
  the stable yard's double gate on the north curtain; the phase sound on the castle hill when a stage comes back.

## Session 12 (A6, 2026-11-20)

- **DD-05 live** (A8 installed it): the Western Tower's front door names `arrival: entrance:d1_door`, the rope
  `entrance:d1_rope` (the climb's yes calls q-d6.tower_rope, then moves to DD-05's top floor (1376, 1472, 1920)). The
  first opening with the key only opens the door (A3's "... sulky pop." text and `tower_opened`); the next click goes in
  (a move right after the hook would hide its text). DD-05's exits land at (-16896, 14848) facing south (front) and
  (-16896, 16896) facing north (rope). The walk goes in and out by both (877 steps). Installed with bake 23:55:05;
  walk 2/2 and hostility on assets_dev; audit 0 errors.

- Session 12 (2026-11-21): AU's outdoor bed (E9) from `output/studio_cal/a6/beds/d1.yml`, read by gen.py; reinstalled with
  bake, walk 2/2 and hostility on assets_dev.

## D-58: the fall from D7 (A6, 2026-11-21, sixteenth session)

`entrance:d7_fall` at (-6656, 6144, 1152), facing south, 1,024 north of Lucio's Jetty (zone A3-B4, A3's `d7_ab34`). Checked against the installed map (`output/studio_cal/a6/s16/fall_points.py`): a whole flat cell (the 3 x 3 nodes level), no water or lava, no decoration or wall within 256, no hostile with a ranged attack within 5,888 (placed actors and spawn markers with their slot monsters). The entrance is kind `both` in the plan only so that it does not become the party start (the studio takes the first `arrival`). The map and its scene are unchanged by the point (byte-identical), so only the studio sidecar was installed and the bake stays valid. The Dark Grove rope's arrival is renamed `entrance:d7_rope` (-8192, 14336, 1088), facing 768: D7's 'Descend to the Darkness Below?' lands here, and the rope's yes branch climbs to D7's `entrance:d1_rope` once `xeen_d7.blv` is installed and names it (gen.py `D7_LIVE`, `d7_rope_move`). The fall tests (D-54's shape) run from D7.

**D7 installed (A6, 04:56):** the grove rope's yes branch now climbs to D7's `entrance:d1_rope` (-24768, -6624, 1024)
once `m30.done` (A3's `m30.grove_rope`, qbit 111600); D7's "Descend to the Darkness Below?" lands on
`entrance:d7_rope`. Map and scene byte-identical (sidecar and Lua only, bake valid). Round trip 2/2
(`output/studio_cal/a6/s16/tests/rope.yml`); walk rerun from assets_dev.

## Side-quest faults (A6, 2026-11-21, twenty-seventh session)

- **Q-D12 war:** `evt:sardaj_war` (event 266, a one-second timer) turns the Sardaj (group 60) within a second of Yog's
  "Battle!" (A3's dialogue sets `q-d12.hostile`) or the burnt camp; a map variable (`sardaj_turned`) keeps it to one
  run per map state. `evt:sardaj` (215, load) still keeps them hostile on every later load.
- **The Sardaj tents (176):** the source's "You have found a Barbarian camp. Destroy?" is one Yes/No button prompt
  (D-72 rule 3); the typed "Destroy (Yes/No)?" and the message before it are gone.
- **Q-D4's lettered chests:** each lid now says what it did, like the numbered row: right "A letter on the lid reads:
  P. The lid drops shut.", already shut "The P chest is shut.", wrong "A letter on the lid reads: I. It will not
  shut. All nine lids spring open again." (the source has only "A letter on the lid reads: P"; the rest are the
  map's own, as the numbered row's). The walk asserts a wrong lid, every right lid and one shut lid.

## D-85: missile range round the talking givers (A6, 2026-11-21, thirtieth session)

- Measured (`output/studio_cal/a6/s30/d85.py`): Joe (4956) had two siege lines at 4,086 and 4,845, Justine (4951) the
  second Electrapede pack at 3,745. Moved, counts and slots kept: `pop:siege_north` 1-2 from (64, 34), (66, 32) to
  (63, 28), (80, 36); the pack `ELECTRAPEDES[1]` from (50.4, 37.4) to (40.5, 35.5) on the great tree's west side (the
  dark wood's trees re-spaced round the new clearing). Warnings left (5,120-5,888): Joe 5,803 (the gremlin pack at
  (77.6, 42)), Justine 5,527 (arachnoid marker 19) and 5,650 (Electrapedes, group 3), Luna (4952) 5,503 / 5,578 (west
  heath markers 26, 27), Yog (4953) 5,799 (foothills marker 39). `gen.py` refuses a circle middle or placed pack within
  5,120 of the four.
- The pyramid's first fight is now 5,656 away (was 2,388; a town arrival: D-15 sets no upper limit).

## D-87: ranged disablers (A6, 2026-11-21, thirty-first session)

- No ranged disabler on D1 (Gremlin Guards' Afraid is melee; arachnoids, crawlers, Electrapedes and the siege lines
  carry no missile condition): every arrival, mirror, Town Portal point and coach stop and every giver measured by
  `output/studio_cal/a6/s31/d85.py`.
- Kept by D-87: Joe 5,803, Justine 5,527 / 5,650, Luna 5,503 / 5,578, Yog 5,799 (melee kinds).

## F10: the empty south-west (feedback-fix agent for A6, 2026-11-21)

The user's empty-land feedback (F10; `tools/xeen/empty_zones.py`): the south-west quarter (Kalindra's rise, the rim
headland, the south bank) held no monster within 22,313 of its corner, one zone of 1,417 tiles, the worst in the world;
land farther than 6,000 from any monster 27 %. The approved L1 had marked the headland and the south bank `safe`;
both now hold monsters (`safe: false`, DECIDE in the F10 report).
- Six markers moved, counts and slots kept (kill XP unchanged: D1 0.9676, Act III 1.0179 before and after):
  `pop:rim_headland` (27, 84), (28, 86) arachnoids, from the west heath's (29, 42), (26, 34); `pop:south_bank`
  (39, 94), (41, 96) crawlers west of Falista's hut, from the foothills' (106, 32), (107, 34); `pop:north_bank`
  (56, 75), (58, 77) gremlins, the siege's south line below the south wall, from the siege lines' (60, 25), (71, 26).
  The west heath's pair nearest Luna moved from (29, 51), (33, 52) to (28, 49), (35, 50): Luna's D-85 warnings
  (5,503 / 5,578) are gone. Plan populations: west heath 4, siege lines 7, foothills 3 groups, the three new ones 2.
  `gen.py.pre_f10` is the script before.
- Exemptions in `tools/xeen/empty_zones.yml`: Luna's 5,888 (D-85) and Kalindra's forecourt 2,500 (D-15's town buffer
  for a Town Portal point; L1 keeps spawns off it). Without them the map passes too (largest zone 430).
- After: largest zone 227 tiles (Kalindra's castle hill), deepest 9,474 (the north-west corner), land > 6,000 9 %
  (exempt left out; 12 % without), `--check` passes. The map's own measure: hostiles 134.5, POIs 52, first fights
  D2 road 4,679, D6 road 2,832 (was 2,276), pyramid 5,656, Kalindra's gate 5,309 (was 10,890), dd03 exit 5,771;
  6,000 rule 10 tiles (unchanged), land more than 3 cells from anything 0.245 (was 0.253). D-87: no ranged
  disabler; `check_d85.py` 0 errors at 5,120 (3 melee warnings at 5,888: Joe, Justine, Yog, as before).
- Installed with its bake at 23:53 (`output/xeen_fb/F10/d1/bake_xeen_d1_234510`), not stale; audit L4 0 errors and
  the 7 coplanar warnings. Hostility and daily pass (`output/xeen_fb/F10/d1/run/`). **The walk fails at step 121**
  (Ellinger's door no longer refuses: D-89 opened `m17.tower_door`) and, with that step removed, at step 189 (the
  north gate's "reads your pass" line: `m14.yml` changed 23:28); F2's run before this install failed the same way.
  `gen_walk.py` needs the D-89 hook changes. The assets_dev audit lists 2 errors, `entrance.question` on events 117
  and 121 (the grove rope and the heretics' rope ask Yes/No before a move into a dungeon), also not from this change.

## S32 (2026-11-22, A6 32nd session: merge point 41 and the feedback fixes)

Rebuilt on merge point 41 (chests as chest kinds, ground heights, scatter), installed with its bake 01:06; Lua-only 01:12. F16: both ropes lose their Yes/No (the grove rope: m30.grove_rope decides, then the standard window into D7; the tower rope: q-d6.tower_rope's status line, then the window with trans row 5033); every dungeon door shows its row (5028-5032, 5038, `tools/xeen/entrance_screens.py`); the burrow drops q-d1.court_entrance's message after the move (it replaced the window: nobody got in). Walk (gen_walk.py): window OK steps, Ellinger's door (D-89: no lock) shows row 5029 and Close, the D-90 status-line hooks (output/studio_cal/a6/s32/hookwin.py), F1 houses. Walk 905/905, hostility, daily pass; audits 0; empty_zones passes; terrain check 0 seams; plants installed (F5).

## Rim rebuild (2026-11-23, agent xeen-rimmap-c: U-12, D-106, D-109, D-112, D-113, F25, F28)

- The rim sea is the void (`terrain.void [[0, 0, 22, 104], [0, 105, 127, 127]]`), 56 hull pieces, the corner at
  (23, 104), 23 return points; Rim Falls (31, 105) down the spillway; the rim event, shrine altars, campfires and the
  studio's F30/F31 come with the regeneration.
- **North gate** (F28): `NORTH_GATE` (63, 44) -> (63.5, 44), on its road tiles' middle (the gate lane on the line x 63
  lays cell 63..64); walls, gatehouse, leaves, `NORTH_OUT` (-256, 10752), the entrance, the gate-passage grate and
  `tools/xeen/town_walls.yml`'s seal follow; `gen_walk.py` `GX`; story segment 39's three gate poses x -512 -> -256.
- **Queen's Gate** (F28): both lanes (`QUEEN_LANE`, `QUEEN_IN_LANE`) start in the gate's passage, so the road tiles
  centre on it (was 469 off).
- **dd01_outfall** (F25, D-105, not the kit): a `doorway` in the gorge's west face (sill 832 on the gorge floor, face
  up to the vale's edge 1152, frame 576 wide, 512 back into the slope, dark arched door 224 x 256), no tunnel, no water;
  `town_fit_check` culverts 0. Captures `cap/d1_after/12-16` (gates in/out, the outfall).
- Checks: audit 0 errors (36 warnings, was 42: back-to-back pairs of the gatehouse and Kalindra's gate), `void.occupied`
  0, gate_check 0, town_fit 0, walls 0, doors 0, empty zones, props, check_wild clean, check_faces 28 findings (was 35),
  `common/d85.py` DIS 0 (FAIL/WARN counts as before), house signs 0, `stale_bakes --check` 0. Build warning kept:
  `gates.road_off` on `east_bridge` (y 60, a cell line; not in town_fit_pending).
- Tests: walk x2 (after `gen_walk.py` GX) and hostility pass.
- Generated twice (the rescue's return points from the first build's land, `XEEN_WILD_MAPS`), built, villagers placed, recorded (`agent:xeen-rimmap-c`), checked in a private hard-link root, installed with its bake, terrain weights, the minimap re-rendered and its void painted (`tools/xeen/void_minimap.py`). Scripts `output/xeen_rimmap_c/build.sh`, `install.sh`, `tests.sh`, `tours.py`; logs `output/xeen_rimmap_c/run_<key>/`; captures `output/xeen_rimmap_c/cap/<key>_after/` (day and night, against `output/xeen_rim/before/<key>/`).

## Final outdoor round (2026-11-24, `xeen-fb3-final-dark`)

- Regenerated with the classic kit and `classic_kit.yml fit_maps` (whole storeys; ruins and low walls plain), the studio
  round's hoods (`dd10a_adit`) and bridge ends (`east_bridge`, `rope_bridge`). Kramer's Caravans' door is the classic
  stables office's (4144, 5904): the tests' Kramer pose is (3844, 5904) (Q-D11, Q-D2, story 43, promotions 47, 49,
  `class_table.py`); the jail's door pose is (2176, 8724).
- DD-01's iron hatch a cell east, `DD01_AT` (67.5, 57.5): its wedge's raised land rose 79 through the square's paving
  (`town_fit_check platforms.through`); DD-01's arrival (1024, 3072) is unchanged; the hatch's test pose is (1300, 3328)
  (story 45, Q-D5).
- Villagers re-placed (`villagers.py --place D1`): villager 47 stood 493 from a house door.
- Checks: town_fit 0 (kept: `jetty_pier`), check_reach 0, door 0, wall 0, check_wild 0, villagers 0 on D1, stale bakes
  0. check_faces 28 (unchanged: the F31 list, gatehouse, Kalindra's ghost houses, wall NE, jetty, street grate
  (fixed 2026-11-25, issue #45, last section), mill). Audit errors: `doors.tiled` on `kalindra_gate_restored` (xvsdoor 2 across) and `textures.feature_repeated`
  xvswin (model 15): the classic kit's, for c7. D-85: NPCs 4951, 4953, 4956 at 5,527-5,803 (as before this run).
  Playtests: walk 908, hostility 50 pass.

## D-142, D-157, F59, F63 (agent xeen-fb4-outdoor2-x7d1, 2026-11-25; run files output/xeen_fb/p4_outdoor2/d1/)

- **D-142 / D-157.** `gen.py` `d142_enforce()` (common/d142.py, D-85's 5,120 to the givers, 2,600 from Castleview's
  doors, the keep-clear areas, 3 cells plus r off the electrapedes' packs): 11 circles moved (siege_north 1, 3, 4 off
  the north edge arrival, 2,185-3,544 before; east_road_camp 7 off the east arrival; 7 off roads, lanes and paths:
  east_road_camp 2, 5, 6, grove_arachnoids 1, 2 (to the heath west of the grove, (27, 27) and (27, 23)), west_heath 3,
  centipede_meadows 2). check_d85 `5120` 0 errors, no road-setback WARN; `common/d85.py` exit 0.
- **Dungeon exits not held to D-142 yet:** D1 is not in `check_arrivals.D142_EXITS`. 27 exit WARN lines remain (D7's
  rope at the great tree: the electrapedes' packs 3-5 and the grove's arachnoids; DD-05's door and rope, DD-10's
  adit, DD-01's outfall (group 1's saboteurs at the cut bridge), the Castleview pyramid 5,805 < 5,888). Holding them
  would empty the Dark Grove and the west heath of monsters: a DECIDE in the agent's report.
- **F63.** Centipede marker (107, 88) → (105, 88) (578 from the bounds); Luna in the middle of her stones (30, 62)
  (`LUNA_AT`; she stood inside a stone); the Barbarian chief and the seven barbarians south of the moved tent.
  check_spawn_clear 0.
- **F59.** `thing:sardaj_tent_1` (86.5, 23.0) → (87.0, 23.9): it hung 578 over the gorge's lip, which no pad can
  level; now on the camp's shelf at 1,536 (padded). `mill_beam` sinks 26 to its rim. town_fit 0; D1's line out of
  `town_fit_pending.yml`. The Sardaj camp keeps its question (Q-D12, D-144's `OUTDOOR_KEEP`).
- Installed with its bake 10:27:59. Checks: audit the known kinds (classic kit `feature_repeated` 1, back-to-back,
  coplanar, tile seams), door 0, wall 0, wild 0, fit 0, reach 0, faces 28 (as before), stale_bakes 0; walk, hostility,
  daily, `d1_hull_edge` pass. Captures `output/xeen_fb/p4_outdoor2/after/d1/` (the Sardaj camp, Luna's ring).

## D-161, D-160 (agent xeen-fb4-outdoor3, 2026-11-25; run files output/xeen_fb/p4_outdoor3/d1/)

- **D-161: D1 is in `check_arrivals.D142_EXITS`.** Every dungeon exit takes D-142's floors (4,096; 5,888 for a slot
  that shoots or casts). `d1/gen.py`: the grove's arachnoid markers 3-7 (spawns 16-20) are `GROVE_PACKS`, five placed
  packs of three (Arachnoid 11330 ×12, Arachnoid Queen 11332 ×3, no Hunter; groups 6-10) in the grove's clearings
  (40.0, 32.5), (40.5, 39.0), (44.5, 40.5), (52.5, 29.0), (55.5, 30.0): every member 2,000 or more from the rope's
  landing, 4,096 or more from DD-10A's adit, both DD-05 arrivals and the pyramid, 5,120 from Justine. The grove's
  markers 1-2 and the heath's marker 1 moved off the rope and DD-05 by `d142_enforce` (to (77, 26), (59, 71), (32, 75):
  nothing nearer passes 5,888 from the rope, DD-05 and the adit), the siege's marker 7 off the adit (55, 25). Group 1's
  four saboteurs at the cut rope bridge's east end on the east bank lane (`SABOTEURS_AT` (86.6, 40.4); were at its
  west end, 3,033 from DD-01's outfall; nearest now 4,966). The pyramid is held (no marker or group within 5,888).
- **Kept groups (D-161, the D7 rope's door guards only):** the Electrapedes, groups 3, 4, 5 (melee; nearest 2,328 from
  `entrance:d7_rope`), and the grove packs, groups 6-10 (melee; nearest 2,827). Checks:
  `x2/check_d85.py <scene> 5120 --kept-group 3 ... --kept-group 10` 0 errors (12 KEPT lines, all at the rope);
  `common/d85.py ... xeen_d1 --kept-group 3 ... --kept-group 10` exit 0 (it takes `--kept-group` since this round).
- **D-160:** Kalindra's ramp (bmodel 138) had its four side faces wound inward, as X4's castle lane: Map Studio's
  `stairs` `ramp: true` now winds them outward (oymap 10:39). `tests/scenarios/xeen/d1_ramp.yml`
  (`tools/xeen/ramp_test.py d1`): stations, the walk down and up, the foot from three headings, party and solo: pass.
  The cheeks stand under a step over the land here, so no cheek pushes.
- Installed with its bake 10:50:25; door, wall, wild, fit, reach 0; faces 28 (as before); gate lanes 0; walk,
  hostility, daily pass.

## Issue #45: the market grate (agent `xeen-cv45`, 2026-11-25; run files output/cv45/)

- **Fault:** `thing:street_grate_4` ("the market (the square)", 8 high on the land) had its top in the plane of
  `thing:square_paving`'s top (z 1160; check_faces `faces.coplanar`, overlap 24,576): the grate vanished up close and
  showed black fragments from afar.
- **Fix (`gen.py`):** a street grate over another platform (any unturned, drawn `kind: platform` placed before it whose
  top holds the grate's footprint) stands with its top 4 over that platform's top (`raise` = the platform's raise +
  height - 4, still 8 high, the least a platform takes). Only grate 4 lies on a platform: `raise: 4`, top 1164. The
  other three stay on the land.
- check_faces 27 (was 28; the grate pair gone; the rest as listed above). Audit errors as before (`feature_repeated`
  xvswin, the classic kit's), door 0, wall 0, town_fit 0, reach 0, gate lanes 0, stale_bakes 0. Installed with its bake
  (a6_install_baked.sh), key_npcs rewritten (D1's figures are actors 44-47 since D-161's packs; the list still said
  29-32). Walk 1,166, hostility 51, daily 82: pass from the scratch root and from assets_dev.
- Captures `output/cv45/shots_d1/` (near, mid, far side; looked at): the grate reads whole at every distance.
- D-196 (2026-11-26, A6 doors): Ellinger's Tower (192 x 320) and the Western Tower (160 x 320) show the tower kit's
  `xvtdoor` once, fitted over the leaf (`classic_kit.py`), not MM7's framed `hkm1d`/`hkm3dr` (1.5 and 1.25 doors).
  Audit `doors.*` 0, door_check 0; all 6 playtests and extras pass; installed with its bake 19:30. Captures
  `output/xeen_fb/p6_doors/shots/d1_installed/`.
