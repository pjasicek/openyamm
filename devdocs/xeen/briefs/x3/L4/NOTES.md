# X3 Lifeforce Lagoon, L4 (lane A5, 2026-11-20)

Built from the approved L1 (`../L1/NOTES.md`, board `output/studio_cal/x3/mockups/board_x3.png`) with D-11.1, D-11.3,
D-11.4 and D-11.6, later D-15 and D-20. `world: xeen`, map_stats 9101. Installed (see State).

## How it is written

- `output/studio_cal/x3/tools/gen_l1.py` writes L1 (the plan; D-11.1's moved toad markers and D-11.6's edge notes are
  in it now). `output/studio_cal/x3/tools/gen.py` reads L1 and writes L2 (plan only), L3 and L4 (plan, sketch,
  atmosphere). Edit the scripts, never the YAML.
- `output/studio_cal/x3/vw.sh [--install]`: gen_l1, gen, fmt, validate L1-L3 and L4, build into
  `output/studio_cal/x3/build_w`; with `--install` into `assets_dev` and the terrain material files.
- `output/studio_cal/x3/tools/measure.py [build] [project]`: hostiles, first fights, camp/gate distances (D-11.1),
  the POI census of D-20 (`census()`), the 6,000 rule, paved road share, land heights.
- `tools/kit.py` is X2's (house shapes, geometry), copied; its `edge_dist` bug fixed.

## State (2026-11-20, A5 tenth session): texture fit and AU's sounds

- **Installed with its bake 21:15:19** (merge point 16's oymap; after A1's 21:05:55 tile table, so the bake is fresh).
  Texture fit: the Tower of High Magic's plaster storeys used the castle kit's `window` (ch1b1 rubble) in their
  window bays (16 `family_switch` warnings, colour 113 apart); they now take the plaster set's framed bay with its round
  window, `hwp1b1w`. Audit: 0 errors, 0 warnings.
- AU's sounds (`devdocs/xeen/AUDIO.md`): `xeen_coffin_lid` when q-c7.coffin opens the lid; `xeen_spring_drink` with the
  Lifeforce Spring's +2; `xeen_well_drink` on the town well (both states), the masons' well, the Marsh Well and the
  spring's "cool and refreshing" reply.
- Walk 692 steps 2/2, hostility 2/2 from assets_dev (`output/studio_cal/a5/fit/x3_*.log`). The L4 differs from the
  previous one by these words only.

- **Shop signs (A6's texture classes of 21:58: the MM7 `7sg*` signs are pictures meant once):** the kit hung them on 96 x 96 boards, showing the 64 x 64 picture 1.5 times (`feature_repeated`); the board now takes the picture's own size from `texture_classes.yml` (`sign_size`). Reinstalled with its bake in the second pass (`output/studio_cal/a5/fit/pipeline2.log`), walk and hostility 2/2 there.

### Texture fit exceptions

None.

## State (2026-11-20, A5 sixth session): installed, XD-08 and XD-13 live

Sixth session (rebuilt; first installed 16:31:53 and baked 16:45:05; then, after merge point 9, the north edge by
edge_spans and one install through `output/studio_cal/a5/install_baked.sh` (bake in a stage, then map and bake
swapped in together): installed with its bake at 17:01:30, 0 stale bakes, terrain files unchanged):
- **Doors to A7's dungeons**: the Tomb's door leads into XD-08 (`xeen_xd08.blv`, (0, 384, 0) facing north) behind A3's
  `m10.tomb_door` (the Stone of a Thousand Terrors; its fail text without it); the foundation stair
  (`thing:xd13_stair`) into XD-13 (`xeen_xd13.blv`, (0, 320, 0) facing north) once the deed is the party's (m8.deed,
  111160), else "A board is nailed across the stair: CROWN LAND. FOR SALE. ENQUIRE AT EBENEZER'S TENT." (A3 has no
  line for it). XD-24 is not installed: the coffin's stair stays sealed. A7's exits land on the ground in front of
  each door: XD-08's (-15360, -9830, 1146) and XD-13's (10496, 15216, 1760) are this build's terrain heights exactly.
- **Mist and sky (D-11.1)**: the load event `evt:nightshadow_dawn` runs `evt.SetMist(0) evt.SetOutdoorSky("sky15")`
  once q-c7.done (112141) is set. q-c7.done is set only in XD-24 (A3's `q-c7.draco`), never on X3, so no fade on
  this map. The script share is one for every layer: the lagoon's ground mist lifts with the town's fog.
- **ShowThing/HideThing** (merge point 8) in the coffin's and the ranger tents' Lua: the HIDE_CALLS workaround is gone.
- **The north edge (D-11.6) by the world's edge_spans table** (A1, merge point 9): the step plate `thing:x4_plate`, the
  two unseen barriers and `X4_LIVE` are gone; `edge:north` is a plain edge with `span: [-32768, 32768]` and X4's x 36
  arrival (-14336, -22016, 992, facing north) as in `edge_spans.yml`, so it writes no travel row (neither way). The
  road's end sign only points the way. X4's south edge west of x 0 arrives at X3's north start (-7168, 22016, 1120).
- **Decorations** without a 3D model swapped for bound kinds of the same use: tree43 -> tree41, tree44 and tree45 ->
  tree42, tree46 -> tree28 (the scatter mixes merged), rock66 -> rock65 (graves), rock67 -> rock68 (yard, rise),
  mushrm06 -> mushrm05, the camp's 7dec24 -> bigbarel. Left without a model (no bound kind fits): 7dec12 x2 (the
  causeway posts), haybale2 x1 (the work yard).
- **Checks**: `oymap audit` of the project and of the installed map with `--reach --solve` (dressing included): no
  error, no warning; build warnings the same 7 notes. On the merge point 9 binaries (game 16:42, oymap 16:40), headless
  from assets_dev: walk (684 steps) 2 of 2, hostility (46) 2 of 2 and `tests/scenarios/xeen/edge_spans.yml` (28)
  (`output/studio_cal/x3/run/walk_s6b_1.log`, `walk_s6b_2.log`, `host_s6b_1.log`, `host_s6b_2.log`,
  `edge_spans_s6b.log`): the hatch refused without the deed and into XD-13 at (0, 320) with it, the Tomb's
  door refused without the stone and into XD-08 at (0, 384) with it, the north edge's travel prompt onto X4 at
  (-14336, -22016, 993),
  every house screen. The runner has no assertion for the scripted mist or sky: the tour shows them (below).
- **D-20's census** in measure.py; the camp's cold fire (dec24x) moved to (84.6, 45.75) and the punt hull to
  (58.25, 58.65), each into its set piece's spot.

## State (2026-11-20, A5 fifth session)

**Installed** in `assets_dev/worlds/xeen` (map, scene, Lua, studio file; terrain weights through
`output/studio_cal/a5/terrain_swap.sh`; minimap `icons_x2/xeen_x3.png`). A2 has written row 9101 and the travel rows.
L1-L4 validate with no issues; the build's 7 warnings are notes (two road cells taken out of a square of four, one reed
without a place, and the "not built yet" kinds); `fmt --check` clean; `oymap audit` (dressing included) clean;
textures 51 of 120, no new ones.

Changes this session: the tomb path's crossing of the Lagoon Water is the fen bridge's own link (`link:fen_bridge`,
`bridge: true`, two bridge-head junctions) and the bridge reaches y 67.2; the XD-13 stair a pit hatch (no back step);
the islet terrace [63-66, 67-71] (no node in water); a third food tree in the Bogwood's west (20.5, 46.5) closes the
6,000 rule; the masons' well in Emerson's yard (town_feel: wells 3); the camp's rain barrels behind the tent (D-14:
they stood before its door); the causeway posts against the causeway; the coffin in grey stone (`cwb`/`cnb`, it read
as a mud block in the tour); `HIDE_CALLS` from the locked cogs, so the coffin opens and the ranger tents burn on the
click; the obelisk on A3's `obelisks.x3`; the north road live (`X4_LIVE`): a step plate at its end leads to X4's x 36
arrival, an unseen barrier along y 19.5 keeps the party off the rest of the north edge (the travel table's X3-north
row lands on X4's south start, X2's road, D-11.6).

Measured on the installed build (`measure.py`; D-15's census):

| figure | target | build |
|---|---|---|
| hostiles at load | 135 | 135 (46 markers, 15 placed) |
| first fight from the map-edge arrivals: east (X2) / west (X5) / north start (X4's south edge) | 2,000-6,000 | 4,685 / 4,399 / 5,583 (unchanged in the sixth session) |
| town arrivals, not banded (D-15): Nightshadow square / Newcastle gate / the camp (respawn) / XD-11's door | town buffer | 7,688 / 5,977 / 7,543 / 6,590 |
| nearest monster to Ebenezer's tent / the Newcastle gate / the camp shrine (D-11.1) | 5,000-6,500 | 5,645 / 5,465 / 6,879 |
| nearest monster to a Nightshadow door | town buffer | 5,322 |
| POIs, the shipped census (D-20: bound events chained within 400, one set piece one spot; NPCs and event-less landmarks not counted) | 30-40 | 39 (sixth session; D-15's count was 38) |
| chests | 4-10 with a reason | 9 |
| 6,000 rule | none over 6,000 | none (farthest 5,766 at [108, 19], the rim corner) |
| paved road tiles | 1-4 % | 1.7 % |
| land heights in the square | range >= 2,500 | 672-3,488 |
| kill XP per member (A2's balance.py) | 14.0k | 10.8k, 0.77: off (see below) |

**Kill XP (A2's report: 0.77).** Proposed slot lines for row 9101, Dif only (the markers, the count of 135, D-11.1's
distances and the quiet land stay): Swamp Thing **Dif 2** [2, 3] w40, Toad **Dif 2** [2, 4] w20, Zombie **Dif 4**
[2, 3] w40. Estimated with balance.py's tier weights: about 13.6k per member, 0.97. (Swamp Thing at Dif 3 would reach
1.02 but puts a level-32 Marsh Horror in one group of five against a party of 13-16.)

**Walk** (`output/studio_cal/x3/tools/gen_walk.py`, 477 steps then; 682 since the sixth session, see above) and **hostility** (`gen_hostility_x3.py`): 2 of 2 each
on the build with the north edge sealed and again on the installed build (see the lane log for the runs). The walk:
the camp, the Newcastle gate and its mirror, the foundation stair, the Marsh Well, the obelisk, the causeway and
XD-11 (refused, then with the Enchanted Key in and back), all 16 Nightshadow doors before the liberation (A4's closed
texts), the boards and plinths, the coffin's two refusals, the dials turned to 9-9-9, night, the coffin opened, the
town well after q-c7.done, the Lifeforce Spring, the Tomb's door, the fen bridge, the west edge into X5, the north
road's plate into X4, the east edge into X2. **The house screens are not asserted yet**: A4's `source/towns/x3.yml`
is still `planned`, so house_data has no rows 4101-4121 (the doors call EnterHouse on missing houses). When A4 removes
`planned` and the generator runs, `gen_walk.py` asserts every house screen by itself (HOUSES_LIVE) and the walk is
run again.

**town_feel** (fifth session; the sixth session's `--small` run is under "Town feel exceptions"; `town_feel.py`, root `output/studio_cal/x3/tf`: the world's rows appended
to the engine tables, the doors as after q-c7.done, since before it the studio reads Nightshadow's doors as messages;
output `output/studio_cal/x3/run/town_feel_open.txt`): 16 houses, 8 figures outside the shipped ranges, all of the
cursed town's plan (A4's x3.yml plots, the approved L1): services in town 5 (6-25), magic shop to alchemist 1,024
(1,147), service to nearest service median 2,690 (2,424), the tavern's rank from the centre 0.87 (0.86), the town's
spread 4,197 (4,358), built footprint covered 0.14 (0.21: the yards and the churchyard), monsters within 1,500 of a
wild paved road 0.0 (X3's only paved wild roads, east and camp, lie inside D-11.1's buffers), wild group spacing
median 2,763 (2,433). Left as they are and sent to the orchestrator as a design question (lane report).

**Bake**: after the final install (`output/studio_cal/x3/present/redo.sh bake`); see the lane log.

Tours (`output/studio_cal/x3/tour/tour_x3.yml`, shots in `tour/shots/`, looked at): the causeway at dusk and noon,
the Tower's door, the square, the dial walk, the coffin, the camp and its barrels, the Newcastle gate and courtyard,
the yard, the three edge arrivals, the Tomb, the spring, the fen bridge, the rangers' camp, the Bogwood tree, the
town at night, an overview. Fixed from them: the coffin's texture. Sixth session: `tour/tour_mist.yml` (shots in
`tour/mist/`): the town and the square at noon before and after q-c7.done, looked at: before, the town fog under a
clear sky; after, no mist and the overcast sky15 (a debug `sky weather` override outranks the script's sky, so the
after shots clear it first).

## What was built

- **The lagoon** (860) in two bodies round the Tower's islet; **the causeway** a stone bridge of eight segment arches
  (deck 940, `cwb`/`cnb`) from the north shore at x 64.5 to the islet; **the Tower of High Magic** (towers kit: `hwm2wall`
  base, `hwp1bwall` storeys, slate cone; about 2,900 high) with its door facing north up the causeway, into XD-11
  through A3's `m13.tower_door`. A ground mist on the lagoon and a fog volume over the town lift on q-c7.done, and the
  sky turns overcast (`evt:nightshadow_dawn`, D-11.1).
- **Nightshadow** (A4's 16 doors on their L1 plots, `cloudside_town`'s darkest grades: poor, grey and timber houses;
  the Moon Guild, Du Monay Manor and the Temple of the Dawn in stone). Doors: 4103 by night while the Count rules,
  4104 after `q-c7.done`; 4105 always; the others open on `q-c7.done` and say A4's closed texts before.
  **The square** (paved, 1,000): the dial walk along its north side (three sundials 384 apart, each asking the
  source's "The sundial is set to N.  Turn?"; while all three read 9 the map sets `q-c7.dials_set` 112142 and clears it
  otherwise); `q-c7.sign_nine` at the walk's west end; `q-c7.clue_stitch` and `q-c7.clue_cat` on the plinths of dials 1
  and 2; **Draco's coffin** west of the street (D-11.3: closed, a stone sarcophagus whose click refuses while the dials
  are not set, then while it is day, then runs `q-c7.coffin` and opens at once; open, a pit with a dark stair, shown on
  load once 112143 is set; the stair is sealed until XD-24 exists); `q-c7.sign_night` on its plinth; `q-c7.rhyme` 384 from the
  coffin; the town well (`q-c7.well`'s texts; after `q-c7.done` cures disease and weakness and gives +10 Personality
  as a bonus); the mirror 4110 between the two east doors; the Town Portal arrival on the square's south side, clear.
  The churchyard: 14 graves, the sexton's shed and chest. A ground mist on the lagoon and a fog volume over the town.
- **Ebenezer's camp** (1,020): Ebenezer's Tent `thing:ebenezer_tent` (house 4101, a tent structure; A4 took the id),
  the Camp Shrine 4102, the fire, the rain barrel ("The barrel is empty.", aaze0012:13), the respawn point.
- **Newcastle** (rise terrace 1,750): stage 0 the ruin (north range, side walls, two round gate towers, `ch1b1`),
  the foundation stair (XD-13, sealed), Emerson's work yard with its chest; stage 1 the new curtain walls (hidden,
  shown by `evt:newcastle_walls` when `Xeen.stageOf("newcastle") >= 1`, m9.walls); stage 2 the keep (hidden, shown at
  stage 2, m11.keep); the foundation stair into XD-13 with the deed (m8.deed); the mirror 4121 outside the gate; three
  workmen (peaceful).
- **The wild**: the Bogwood with the evil rangers' camp (two tents, fire, chest; "You have come upon an Evil Ranger
  camp.  Destroy?" asks and burns, then `x3.ranger_camp`; aaze0012:3-4), the Black Fen and the Lagoon Water with a
  timber bridge on the tomb path, the eel-fisher's hut and chest, the Gloomwood with the Tomb's barrow (into XD-08
  through `m10.tomb_door`), the sunken graves and the pilgrim's pack, the Drowned Shore with the Lifeforce Spring
  (+2 Endurance once per character, player bit 11280), the wreck and its chest, the Crow Hills with the fallen
  watchtower and its chest, the Crow's Crown (3,450); the Marsh Well (+10 four elements, temporary), the garlic
  shrine (+10 Dark resistance, temporary), two food trees (2 food a day; "You find nothing in the tree.", aaze0029:11),
  the obelisk (third word "HOARD"), four signposts, the north road's sign (X4 sealed), Ebenezer's coffer and the
  sunken punt's chest in the reeds. Trees and rocks run to the map's edge in six rim bands (road valleys left open).
- **Mirabeth** (NPC 4202, MM7 Peasant 350) on her black rock off the quay, hidden on load once q-c12.done (112240).
- **Monsters**: the L1 areas (Swamp Thing 2-3, Toad 2-4, Zombie 2-3), the camp's 7 rangers (11130-11132), 8 night bats
  (11310-11312) below the churchyard and over the shore pools. D-11.1: two Crow Hills toad markers in a small area at
  the hills' south foot ([92-96, 30-33]). Fixed single markers for the arrivals' first fights and three for the 6,000
  rule ([22, 22], [45, 45] Bogwood; [52, 72] fen; [59, 83], [35, 100] Gloomwood). No marker on the tomb door's step.

## Original lines (`output/xeen_review/story/alltext.txt`)

| Line | Where | Reference |
|---|---|---|
| "The sundial is set to N.  Turn?" | the three sundials | xeen/aaze0029:12-23 |
| "You have come upon an Evil Ranger camp.  Destroy?" / "You ruin their food, burn their tents, and poison their water." | the rangers' tents | xeen/aaze0012:3-4 |
| "You find nothing in the tree" | the food trees once picked | xeen/aaze0029:11 |
| "Rain Barrel" / "The barrel is empty." | the camp's rain barrel | xeen/aaze0012:12-13 |
| The rhyme, the signs and the clues | A3's hooks (q-c7.*) | xeen/aaze0029:6-10 |

## Hooks wired (A3, by name)

q-c7.rhyme, q-c7.sign_nine, q-c7.sign_night, q-c7.clue_stitch, q-c7.clue_cat, q-c7.coffin (after the map's two
refusals), q-c7.well (its texts and the map's effect, qbit 112141), q-c7.done (the mist and sky on load),
m13.tower_door (XD-11's door), m10.tomb_door (XD-08's door), m8.deed (qbit 111160: XD-13's stair), x3.ranger_camp (after the burn), m9.walls / m11.keep (Xeen.stageOf), m8.site (the stage-0 ruin),
q-c12.lagoon_rock (Mirabeth's group, qbit 112240). Mirrors: Xeen.useMirror(4110 / 4121, eventId, continueStep).

## Slots wanted (A2, `source/map_rows.yml`; X3 has no map_stats slots yet)

| slot | family | tier (Dif) | per marker | weight | markers |
|---|---|---|---|---|---|
| 1 | Xeen Swamp Thing (11460-11462) | 1 | 2-3 | 40 | 18 |
| 2 | Xeen Toad (11450-11452) | 1 | 2-4 | 20 | 10 |
| 3 | Xeen Zombie (11250-11252) | 1 | 2-3 | 40 | 18 |

No traps. Placed rows: 11130, 11131, 11132 (the rangers' camp), 11310, 11311, 11312 (night bats).

## Sealed exits and what opens them

- North road (X4): live, the whole north edge by edge_spans (D-11.6), above.
- XD-08 and XD-13: live (sixth session).
- XD-24: a message; when A7 installs it, replace the sealed message of `thing:coffin_open` by `into` (its start) and
  drop `listed_only` from `door:xd24`.

## Words the studio lacked (workarounds)

- One edge with two arrivals (D-11.6): now the world's edge_spans table (merge point 9; the studio's `span`); the
  plate and barrier that stood in for it are gone.
- `chest.gold` does not exist (Ebenezer's coffer holds items only).
- Merge point 8 gave the words that were missing: `ShowThing`/`HideThing` (now used by the coffin and the ranger
  tents), `evt.SetMist` (now used), outdoor `player_bit` and `question` (the spring, the sundials and the rangers'
  camp still say them in Lua, which works; not rewritten).

## Town feel exceptions

`town_feel.py --small` (D-20, TOWN_FEEL.md §5c; Xeen's own tables) on a scratch build of the project with
Nightshadow's doors as after q-c7.done (`X3_TF_OPEN=1`, never installed: the checker counts a gated door as no house),
`--project` mode; output `output/studio_cal/x3/run/town_feel_small.txt`. 16 houses, 5 services. Four figures out:

- Service to nearest service, median 2,690 (854-2,424): the approved L1 and A4's plots put the camp's two services by
  the X2 road and the town's five round the square, apart by the lagoon shore; kept (D-20).
- Built footprint covered by buildings 0.14 (0.15-0.37): the town's yards and the churchyard are inside its footprint;
  kept (D-20).
- Monsters within 1,500 of a wild road per 1,000 of road 0.0 (0.03-0.58): X3's only paved wild roads (east and the camp
  road) are the safe spine D-11.1 cleared (5,000-6,500 from the camp and the gate); kept.
- Wild group to nearest group, median 2,763 (403-2,433): inside MAP_CRAFT §6.1's 2,600-3,800 for wild land; kept.

## Dressing exceptions

None: `oymap audit devdocs/xeen/briefs/x3/L4 --world xeen` reports no error and no warning.

## What the user should look at (once installed)

The causeway from its head at dusk with the Tower and Nightshadow's fog; the square's dials, coffin and boards; the
coffin opening at night; Newcastle's stages; the Gloomwood's darkness and the Tomb's barrow.

## Seventh session (2026-11-20, A5): the coffin stair into XD-24

- A7 installed `xeen_xd24.blv` (17:41). `thing:coffin_open` now leads in (`into: {map: xeen_xd24.blv, at: [0, 704, 0],
  facing: 1536}`, A7's start at the coffin stair's foot); `door:xd24` is no longer `listed_only`; the plan's entrance is
  `both` (XD-24's exit arrives at (17664, -5120, 992), 512 south of the coffin). DOORS.md updated. Audit `--reach
  --solve` clean (three `never_read` infos on the dial map vars, as before). Installed with its bake through
  `install_baked.sh` at 17:45:03 (0 stale). Hostility 2/2 from assets_dev.
- **Open:** XD-24 has no `map_stats.txt` row yet (A2; `source/maps.yml` has it as 9147), so the game cannot load it
  ("cannot resolve map world for xeen_xd24.blv"). The walk enters the crypt only once the row exists (`gen_walk.py`
  `XD24_ROW`); until then it notes the wait (679 steps; 2/2, `run/walk_7c.log`, `_7d.log`). Regenerate the walk and run it again when A2 writes the row.

## Eighth session (2026-11-20, A5): the town well cures

- A3: the town well (event 56, `thing:town_well`) set DiseasedGreen, DiseasedYellow, DiseasedRed and Weak, which
  inflicts them. `gen.py` now writes the four as `subtract` (the event's SubtractValue clears a condition), as D-11.4
  means: cured of disease and weakness, +10 Personality. The rebuild changed only the Lua (the odm and scene are the
  same bytes). Installed with its bake through `install_baked.sh` at 18:38:37 (0 stale).
- The walk now gives member 0 Weak, Disease (weak) and Disease (severe) before the liberated well and asserts all
  three gone after it. XD-24's row exists now, so the walk enters the crypt by the coffin stair and comes back:
  692 steps, 2 of 2 from assets_dev (`run/walk_s8_1.log`, `_2.log`); hostility 2 of 2 (`run/host_s8_*.log`).

## Twenty-first session (A5, 2026-11-21): D-70, the temporary sources once a day

- Wayside (garlic) shrine and the Marsh Well: `daily()` in gen.py (`Xeen.usedToday("x3_<thing>")`, every member);
  refusals: the well's water line, the shrine "The strings are picked bare. More garlic will hang there tomorrow."
- The town well (event 56): q-c7.done (112141) still opens it. The cure now reaches every member on every drink (a
  condition cure, not a temporary bonus); the +10 Personality is once a day for the party (`x3_town_well`), else "The
  water is cool and refreshing."; the gain says "until you rest". Backup `x3/tools/gen.py.pre_s21`.
- odm and scene byte-identical: Lua and studio.yml installed 08:26:06, bake fresh; walk 692 and hostility 2/2 from
  assets_dev; audit 0/0.

## F10 (2026-11-21 night, feedback fix for A5): monsters in the empty east and north

The user found Xeen's outdoor land "ultra empty". `tools/xeen/empty_zones.py xeen_x3` measured one zone of 1,208 tiles
(the north vale, the reedbeds, Newcastle's rise, the camp, the meadow and the east ridge; deepest 15,194 at [87, 61])
and paved roads a median 7,768 from a monster. `gen_l1.py` now has seven single markers at fixed spots (E6 north vale:
toads [55, 27] and [56, 47], swamp things [60, 37]; E7 reedbeds: zombies [68, 48] and [76, 53], swamp things [88, 57];
E8 east ridge: toads [103, 51]); the fen's swamp things 6 -> 5 and the shore's dead 4 -> 2 (the Gloomwood's count was
kept: changing it re-seeds its markers, one fell 1,774 from XD-08's exit). The north vale and the reedbeds are wild land
with these populations now; their `open` areas are the obelisk's knoll and the causeway head with the X8 landing.

| figure | before | after |
|---|---|---|
| empty zones (largest, deepest) | 1,208 tiles, 15,194 | 133 tiles, 10,073 (`--check` passes) |
| paved roads, median distance to a monster | 7,768 | 4,129 |
| land farther than 6,000 from a monster | 22 % | 5 % |
| markers / hostiles at load | 46 / 135 | 50 / 146 |
| kill XP: X3 / Act II | 0.9754 / 1.0759 | 1.0252 / 1.0827 |
| D-11.1: tent / gate / camp shrine / camp fire | 5,645 / 5,465 / 6,879 / 7,543 | 5,645 / 5,465 / 6,450 / 6,117 |
| D-15 first fights: east / west / north | 4,685 / 4,399 / 5,583 | 4,685 / 4,399 / 3,857 |
| D-85 Mirabeth; D-87 disablers | 5,889; none | 5,889; none |
| nearest monster to a Nightshadow door | 5,322 | 4,908 |
| 6,000 rule | 5,766 | 5,766 |

Installed with its bake 23:33:10; audit 0/0; hostility passes. The walk fails at XD-11's and the Tomb's refusals, which
D-89 removed (both doors now enter at once); without those two blocks it passes 682 steps
(`output/xeen_fb/F10/x3/walk3.log`). `gen_walk.py` must drop both refusals. Logs, measures and before/after captures
are in `output/xeen_fb/F10/x3/`.

## Twenty-ninth session (A5 s29, 2026-11-22, merge point 41 rebuild; run files output/studio_cal/a5/s29/)
- Rebuilt and installed with its bake (01:15-01:19). D-89: Draco's coffin has no night branch (the dials alone); the
  walk opens it by day; XD-11's and the Tomb's doors enter at once (refusal steps gone). F16: trans 5008/5011/5013/5024.
  Walk and hostility pass from assets_dev. Still typed: the sundials and the ranger camp (D-72, NEXT).

## Thirtieth session (A5 s30, 2026-11-22; run files output/studio_cal/a5/s30/)
- D-72: the three sundials ("The sundial is set to N.  Turn?") and the Evil Ranger camp ("You have come upon an Evil
  Ranger camp.  Destroy?") ask with Yes/No buttons (`AskChoiceWithAnswerSteps`, no SetMessage before; `gen.py`), the
  walk selects Yes (`gen_walk.py`); backups `*.pre_s30`. No typed prompt left on X3.
- Installed with its bake 01:41; audit 0; walk and hostility pass from assets_dev.

## The world's rim as void and hull (2026-11-23, agent `xeen-rimmap-a`; U-12, D-106, D-109, D-112, D-113)

Scripts and logs `output/xeen_rimmap_a/` (`build.sh x3`, `install.sh x3`, `tests.sh`; `x3/run/`). Regenerated twice
(the second from the first build's land) and installed with its bake 15:30; minimap re-rendered and its void painted.
- **The rim.** The south rim sea `water:rim_sea` is `void:rim_sea` (y >= 105); 32 hull pieces along the edge; the
  rescue (`evt:rim_fall`) has 19 return points along y 101. Campfires feed once (D-104); the ruins (watchtower,
  Newcastle ruin) are closed shells and the tents (Ebenezer's, the rangers' two) single-sided (F30/F31):
  `check_faces` 0 findings.
- No other change: no town fit item was pending; walk regenerated unchanged; one scatter decoration of 1586 found
  no place.
- Checks (build, private root and assets_dev): audit 0 errors, town fit 0, walls 0, doors 0, D-85/D-87 0, empty
  zones, props support, check_wild clean, house signs 0, `stale_bakes --check` 0.
- Tests: walk and hostility from the root twice and from assets_dev pass.
- Captures `output/xeen_rimmap_a/x3/cap_after/` (rim low/along/high/mid day and night, Ebenezer's tent, the
  Newcastle ruin, the hull from the void day/night, the west rim, the far void); before `output/xeen_rim/before/x3/`.

## D-142/D-157, D-159, F58/F59/F63 (2026-11-25, `xeen-fb4-outdoor2-x5x3`; scratch output/xeen_fb/p4_outdoor2/x3/)
- D-142: the L1 polygons' markers are fixed circles (`gen.py POLY_SPOTS`, the spots the studio had drawn, whole cells,
  r 0.5); `d142_enforce` (common/d142.py) moved 10: fen_things 2, 3, fen_toads 1, 2 (road setback), gloomwood_dead
  1, 5 (XD-08's exit), crow_foot 1 (XD-13's exit), vale_toads 1 (the north edge, 3,455 -> past 4,096), reed_dead 1, 2
  (the X8 landing). X3 is in check_arrivals.D142_EXITS: check_d85 0 errors, common/d85 exit 0 (FF 0, ROAD 0; six
  D-85 FAIL lines with no disabler, melee only, as before).
- D-159: a click turns a sundial one step ("You turn the sundial. It is set to N."); q-c7.dials_set as before.
  `gen_walk.py` and `tests/scenarios/xeen/side_quests/q-c7_count_of_nightshadow.yml` click (both pass).
- F58/F59/F63: newcastle_ruin and wreck 0 `faces.on_land` (A1's ruin courses), the watchtower levelled by a terrace
  under its plot (2688); rangers' tents and the rune stones `yard_1`, `yard_2` (sunk, `rune stone` natural in
  common/level_pads.py) 0 town_fit; Ebenezer's third workman out of the stage-2 keep (80.4, 34.0); crow_toads and a
  shore marker a cell in from the bounds (check_spawn_clear 0). Left: `faces.on_land` on nightshadow_temple and the
  causeway (not F58's ruins); audit's classic-kit `textures.feature_repeated` (6).
- Installed with its bake 10:07; walk and hostility pass; stale_bakes 0.
