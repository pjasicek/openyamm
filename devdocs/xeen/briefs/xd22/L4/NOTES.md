# XD-22 Ninja Pagoda: L4 notes

Lane A7 phase 3 (agent `xeen-a7-xd22`), 2026-11-20. Map 9145, `xeen_xd22.blv`, class S, `world: xeen`. Built from the
MU-6 graph `devdocs/xeen/mockups/act3_graphs/xd22.graph.yml` with D-25 (`mockups/act3_a7_decisions.md`), which wins:
Shinobu's survivors on their own peaceful row, the `q-c4.done` stage, inside at most twice the outside, the paper
screens per Q15 (A1's three checks passed: merge point 12). Generator: `output/studio_cal/xd22/tools/gen.py` (writes
L1-L4; never hand-edit the written files; `--standin` lays t2bedsht for the two new textures); cycle
`output/studio_cal/xd22/cycle.sh`; playtests `play.sh <name>` and `four.sh`; pictures `tools/tour.py` + `tour.sh`.

## What was built

Kai Wu's pagoda on X5's frozen mere, five storeys of dark timber stacked as X5's `thing:pagoda` stacks them, each
smaller than the one below and all centred on (0, -1024); x east, y north; the north door is the entry hall's north
wall at y 0. Storeys 512 apart, rooms 416 high (the hall under the top roof 384 to its walls and a hipped ceiling to
768), walls between rooms 128.

| Storey (floor) | Inside, at most (X5 outside ×2) | Rooms (size; monsters placed, group) |
| --- | --- | --- |
| Ground (0) | 3,072 × 2,048 | Entry hall (start, 1,024 square; 2 Ninja, 10): the monks' bell, Kai Wu's broom; Monks' kitchen (896 × 1,024; 2 Ninja, 11): hearth, table, the ladder up; Shrine hall (2,560 × 896; 3 Ninja, 12): the altar, the clan's banner, the mat over the cellar hatch; East stair (384 × 800) |
| Cellar (-448) | under the shrine | Clan cellar (1,536 × 960, `store: true`): rope, cloth, rice, barrels, the chest (T3); Shinobu and four survivors after `q-c4.done` |
| Second (512) | 2,688 × 1,664 | Dojo (an L, 1.9 M; 5 Ninja, 14): straw targets, weapon wall, the kitchen hatch; Sleeping loft (832 × 1,664; 3 Ninja, 13, two behind the paper wall): mats; West stair (384 × 896) |
| Third (1,024) | 2,304 × 1,280 | Hall of Screens (2.4 M): a maze of eight free-standing paper screens; Shadow Ninjas 2 + 2 in two cells of paper (15, 16), 2 Ninja loose in the middle band (17); the crane screen; the rope's foot. Crane stair (384 × 672) behind the crane |
| Fourth (1,536) | 1,920 × 896, the gallery on the third storey's roof | Armoury (an L, 0.9 M; 2 Shadow Ninja, 18): racks, the chest (T3); Moon gallery (west and south walks, 0.7 M; 2 Ninja, 19): open to the sky, railed; Top stair (896 × 256) |
| Fifth (2,048) | 1,664 × 640 | Clan master's hall: dais, gong, two banners, strongbox (T4, trap 3); Ninja Master (20) and the Clan Master (21) |

- **Stairs** alternate sides: east (ground to second), west (second to third), east behind the crane (third to
  fourth), west (fourth to fifth). Each is a stepped room (16 steps of 32) under the storey above and open to it
  through its whole ceiling (`in: floor`, XD-09's diamond stair), entered at its low end.
- **Ladders through holes in the floors:** the kitchen ladder (into the dojo's floor), the cellar ladder (the shrine's
  trapdoor under the mat), the clan's rope ladder (the gallery's slot at the south walk's east end, down into the Hall
  of Screens' south-east alcove).
- **Loops:** lower (the east stair up, the kitchen ladder down); upper (up behind the crane, back down the rope).

**Counts and sizes** (`oymap metrics`, `output/studio_cal/xd22/metrics.json`):

| | Value | Band (S) |
| --- | --- | --- |
| Sectors | 14 rooms (the audit's 15 counts sector 0) | ≤ 15 |
| Floor area | 14.7 M units² | ≤ 20 M |
| Monsters | 27 placed (19 Ninja 11120 at 22, 6 Shadow Ninja 11121 at 30, 1 Ninja Master 11122 at 40, the Clan Master 11123 at 42); plus 5 Clan Survivors 11124 (not counted) | 15–30 |
| Chests | 3 (cellar T3, armoury T3, strongbox T4) | 0–3 |
| Doors | 7: four plank doors (hkm2d) and three paper screens (the paper wall's two panels, the crane); the hatch is a mover (the studio counts 8 door records) | 3–8 |
| Distinct textures | 21 (14 named in the project, 7 the plain chest set); 2 new | cap 30, ≤ 4 new |
| Loops | 2 | |

Kill XP per member, L(L+10)/4: (19 × 704 + 6 × 1,200 + 2,000 + 2,184) / 4 = **6.2k** (the graph's 6.2k).

`scale_bands.py` (`output/studio_cal/xd22/scale_bands.txt`): the bigger rooms at the shipped median (percentile 47);
the largest room (the Hall of Screens, 2.4 M) and the taller rooms (512) are under the shipped 25th percentile, on
purpose: D-25 caps the inside at twice X5's outside and the storeys stand 512 apart as the graph and X5's model have
them; doorways 256.

## Monsters, map card, hostility

- A2's rows (D-25 Q4, Q14): the Ninjas family 11120-11122, the Clan Master's boss row 11123 (look C, shuriken, blink on
  hit 0.2), the Clan Survivor 11124 (faction `clan`, friendly, placed only). All hostile ninjas placed with
  `hostile: true`, one group per room (10-20, the Clan Master 21), so the done stage hides them by group.
- **Map card** (A2's row; a test row 9145 copied from 9149's in the scratch root's `map_stats.txt` and
  `bolster_maps.txt`): music 12; environment wood hall; treasure 3; lock 6, trap 3, perception 6; refill 672; bolster
  LowerToEqual; **encounter 0** (no rest encounters: the done stage must stay free of ninjas); slot 1 `Xeen Ninja`,
  tier 1, [2, 3], weight 100 (for the card only).
- The Ninjas' model is the family's stand-in (BMonk: they read as brown, blue and red robed monks in the pictures; A2/S).

## Mechanisms

- **The paper screens (D-25 Q15, the breakable-window route; A1's checks passed).**
  - Screens between rooms: each a door leaf in its opening with no door event, `surface: {texture: xjshoji |
    xjcrane, translucent: 0.6}`, and a destructible `of` the door (hp 20, wood). They never open; struck, shot or broken
    by script they vanish, and the opening's portal lets party and monsters through. The paper wall (dojo / loft, two
    Ninjas behind it) is two panels of 192 × 384 with a pier of the wall between, `door:paper_dorm` (north, at y -448,
    destructible 7) and `door:paper_dorm2` (south, at y -672, destructible 16); `door:crane` (the Hall of Screens'
    alcove / the crane stair, 352 square).
  - The crane screen also has a click: `evt:crane` ("Crane screen") destroys it with "The paper tears from top to
    bottom, and the crane falls away. Behind it a stair climbs into the dark." The stair shows through the lit paper
    before. No riddle.
  - The maze: eight free-standing screens of the Hall of Screens, each a row of paper panels (platforms 16 thick and
    384 tall in the same translucent paper, 162-220 wide) between square black posts (trim11_32, 24 thick); every panel
    is a destructible (hp 20) and breaks alone, the posts stand (texture fit, merge point 16). Row A and the cross screen close the straight way east along the
    south side; the way round runs north through the west gap, east along the middle band (two Ninjas) and south
    through row A's east gap to the crane's alcove. Two cells of screens on the north wall hold the Shadow Ninjas,
    seen as figures through the paper, who come out when a screen breaks.
  - Translucency 0.6 (A1's 0.5–0.6): the figures behind read as shadows, the lattice as black wood. Both textures are
    alpha 255 everywhere (RGB), the lattice painted in.
  - To swap them for D-25's fallbacks: `PAPER_T` and the two surfaces at the top of `gen.py` (opaque: drop
    `translucent`); the maze is `MAZE`, the paper doors `door:paper_dorm` / `door:crane`.
- **The cellar hatch.** `mover:hatch` is the straw altar mat on a plank lid (288 × 272, 24 high) over a 256 × 240 hole
  in the shrine's floor in front of the altar. Its click (`evt:hatch`, "Mat") slides it 352 west with the graph's line
  "A draught comes up between the floorboards. The mat lifts: a trapdoor, and a ladder down into the dark."; the
  cellar ladder (448) goes down through the hole.
- **The Clan Master's death:** `evt:clan_master_dead` (a kill timer every 2 s, `kills: monster:clan_master`, once;
  XD-05's method) runs A3's `XeenQuests.hook("q-c4.clan_master")`: clan_master_slain 112081 and "The clan master
  falls. You have dishonored the Ninjas by entering the Pagoda. They surely will not return to reclaim it."
  (aaze0003:5). The map adds no message.
- **The clan's return** (`evt:stage_done`, every load with `q-c4.done` 112082, D-25 Q14, XD-23's stage-on-load
  pattern): every hostile group hidden (10-21), the hatch sent open, Shinobu (group 31) and the four survivors (group
  30) shown. They are placed `hidden: true`, `immobile`, with `hostile` left out (their faction is friendly).
- **Shinobu talks** herself: she is NPC 4530 (`monsters[].npc`, merge point 22), clicked once the done stage shows
  her: "You walk loudly for people who killed a ninja master." and A3's T2-CLAN topic "The clan". The source has no
  Shinobu, so nothing greets the party unasked. Her cushion (`evt:shinobu`, "Cushion") is a line at any stage: "A
  worn cushion on the cellar floor, still warm."
- Clicked lines: the bell, the broom, the altar, the clan's banner, the hearth, the kitchen table, three straw
  targets, the weapon wall, three weapon racks, the gong. Step lines (once): the Hall of Screens, the gallery, the
  cellar. Arrival line (a one-shot timer).

**Map qbits 110920–110929: none used.** The map names A3's `q-c4.clan_master_slain` 112081 and `q-c4.done` 112082;
the build's `once.*` variables.

## Exit (live, D-24) and the start

- **The north door** (`exit:north_door`, the shell's hkm2d, `evt:north_door`, the `exit` preset, title "Winterkill
  Tundra", no question) → `exit:x5_pagoda`: X5 at **(320, 9872, 1000), facing north (90)**: 400 north of
  `thing:pagoda`'s door face (event 61 "The Ninja Pagoda", its panel at (320, 9472, 1120), used from (320, 9728, 992),
  `oymap things` on the installed X5), facing away from it.
- **X5's `into` (A6):** the map's start, **(0, -256, 0) in room:porch, facing south (270)**, just inside the north door.

### Measured heights (2026-11-20)

| Point on X5 | Ground |
| --- | --: |
| (320, 9872), 400 north of the door | 993 (arrival 1,000) |

`playtest_exit.yml` lands at 985–1,010 and stays there 3 s later.

## Original lines

- "You have dishonored the Ninjas by entering the Pagoda. They surely will not return to reclaim it." (aaze0003:5):
  A3's hook at the Clan Master's death.
- The bell: "... until the Evil Ninja clan drove him from his sacred home." (echoes aaze0003:15, "I am a peace loving
  old monk driven from my sacred home ... until the Evil Ninja clan drove me out.").
- The broom: "\"There are still Ninja in my Pagoda,\" Kai Wu said." (aaze0003:16).
- "A draught comes up between the floorboards." (the graph's hatch line).
- The map's own: the arrival ("The barred door gives way. The pagoda smells of cold incense and lamp oil ..."), the
  Hall of Screens ("Paper screens stand everywhere, lit from behind. Shadows move on the paper, and stop when you
  do."), the gallery, the cellar, the crane, the gong, the altar.

## Textures (one family per area; 2 new)

- **The storeys:** X5's pagoda shell inside out: MM7 `hkm2b` (fieldstone between blackened beams, a 256 band) and
  `hkm2d` (plank doors) from the Deyja houses (in no shipped dungeon: they are X5's model's own, the brief's family),
  with MM7 Clanker's Laboratory's black timber above and overhead (`hwm2rf`, `trim11_32` posts, ladders and railing
  tops), `7trimd` plank floors, `7t1cabs` furniture, `t2bedsht` mats, MM6 `straw` (targets, the mat, the broom's head),
  MM7 `tap11` (the clan's dark banner with a carrion bird) and XD-03's `xngong` (the gong, the bell).
- **The cellar:** Clanker's Laboratory's plain stone, `hwm2wall` walls and `7tfb11` flags.
- **New (Codex, `output/studio_cal/xd22/tex`, `xtex.py --project`; refs mm7 t2bedsht, hwm2rf, trim11_32):**

  | Name | Size | Kind | Where | Finished master |
  | --- | --- | --- | --- | --- |
  | `xjshoji` | 128 × 256 | picture | every paper panel (fitted once per panel, translucent 0.75) | `output/studio_cal/xd22/tex/finished/xjshoji.png` |
  | `xjcrane` | 256 × 256 | picture | the crane screen (352 square, `fit`, translucent 0.75) | `output/studio_cal/xd22/tex/finished/xjcrane.png` |

  Installed in the scratch root only (`worlds/xeen/textures_x4`, `textures_x2`); for A6's registry and the lead's
  copy to `assets_source/worlds/xeen/textures_x4/` before the bake.
- **Count:** 21 distinct with the chest set (cap 30).

## Dressing

`oymap audit --world xeen`: no dressing error or warning. Containers only in the kitchen (a pair of sacks by the north
wall) and the cellar (a storeroom, `store: true`: two pairs of sacks and a pair of barrels by the walls, rope coils and
cloth bolts as low platforms). Two candlesticks stand on the floor by the altar.

**Lights and fixtures** (the user's rule, lanes/README.md, 2026-11-20; checked by hand and in the pictures `look5/`,
`sheet7.jpg`): the fourteen `torch01` torches are wall-mounted (`wall`, `along`, 160 up), none in a doorway, on a
panel or on a door leaf; no ceiling-hung lamps; the two candlesticks stand on the floor; every point light of
`objects.lights` stands in its room's air under the ceiling and outside every platform (the stair halls' lights were
lowered to 300 above the steps, the clan master's hall's to 340 under the hipped ceiling).

**Dressing exceptions:** none.

## Checks (scratch root `output/studio_cal/xd22/root`, binaries of merge point 12)

- `oymap fmt --check`, `validate` (L1-L4: no issues), `build` (0 warnings), `audit --reach --solve`
  (`output/studio_cal/xd22/audit.txt`): no error, no warning, 0 coplanar pairs; every sector on foot with the doors
  out of the way (1 of 14 with the doors as they start); infos only (the two paper doors never moved by the script,
  squashed ladder rails).
- Playtests 4 of 4 each (`output/studio_cal/xd22/four.out`, logs `output/studio_cal/xd22/run/<name>_<n>.log`):
  `playtest.yml` (131 steps: the critical path, the bell and broom lines, the hatch and the cellar, the paper wall
  broken, the kitchen ladder down and up, the maze, the crane clicked, the Clan Master's kill timer and 112081, the
  rope down, then 112082, a reload ("RELOAD ok"), the stage, Shinobu's talk and her "The clan" topic),
  `playtest_hostility.yml` (47: ninjas hostile, no fights among them, survivors friendly at the done stage and after
  a reload), `playtest_exit.yml` (15).
- `python3 tools/xeen/quests.py`: no error from XD-22 (`q-c4.clan_master` wired; its one error is DD-10A's).
- Pictures `output/studio_cal/xd22/look1/` (31 poses; sheets `sheet1-3.jpg`), `look4/` and `sheet4-6.jpg` after the
  fixes; unbaked (flat light, the lead bakes). Fixed after looking: the crane screen showed a second crane from its back
  face (the back is now plain paper), the dais was white cloth (planks now), the rope ladder was bright straw (black
  rungs now), the plank doors (two door pictures per 256 leaf), the lanterns (`dec07`) and rice jars (`potery1/2`) draw
  nothing in this world (wall torches instead; the jars are only in the table's line).

## Words needed

1. **A ladder through a hole in a floor** must stand inside the hole: a strip against the wall under the hole's edge
   lets the climber's body (radius 37, held 41 in front of the strip) rest on the slab's edge, so climbing down from
   the top stops at once ("let go at height 0"). The three ladders stand 10 inside their holes' edges (free of the
   walls); the build cannot warn of it.
2. A two-picture door leaf that folds is refused; the plank doors are single sliding leaves with two pictures.

## DECIDE

1. *Paper opacity.* 0.6 (A1's upper bound): figures behind the paper are clearly seen, a little washed. Options: keep;
   0.7–0.8 for paper that shows only shadows. Default keep.
2. *Rest encounters.* Encounter 0, so the done stage stays empty. Option: 10 % (rests would then spawn ninjas in Kai
   Wu's swept pagoda). Default 0.

## For the user

- The Hall of Screens: the shapes behind the paper; walk the maze or strike through it; the crane screen and the stair
  behind it.
- The moon gallery's sky over the railing, and the clan's rope down at its east end.
- Set `q-c4.done` (Kai Wu) and come back: the cellar hatch stands open, Shinobu and her people sit among the clan's
  stores, and the pagoda is empty of ninjas.

## Sixth session (2026-11-20, lane A7)

- **D-33 (5):** the paper (screens, maze, crane screen) at opacity **0.75** (`gen.py` `PAPER_T`). Retaken
  `output/studio_cal/xd22/s6paper/` (dorm paper, dojo paper, screens band and cells): the Shadow Ninjas behind the
  paper still read as figures, so 0.75 stays (not 0.7). Playtests 4 of 4 from `assets_dev`; re-baked.
- Lamp rule: clean under A1's audit. The shoji paper (`xjshoji`) tiles as a seamless grid along the screens; the crane
  screen is one picture fitted once.

## Merge point 15 doors (2026-11-20, lane A7, seventh session)

- The three 256-wide sliding doors (porch to shrine, porch to kitchen, dojo to loft) showed `hkm2d` (one door's picture)
  2.5 times across a single leaf (`doors.tiled`): now sliding pairs (`leaves: 2`) with MM7's Deyja double-door wings
  `hkm1dl` / `hkm1dr`, one on each leaf (gen.py `DOOR2`). `hkm2d` stays on the armoury door and the north exit.
  Textures 23 of 30.
- Audit no error or warning, build warnings 0. Installed, re-baked; from `assets_dev`: `playtest` (131),
  `playtest_hostility` (47), `playtest_exit` (15) 4 of 4 each (`output/studio_cal/a7/s7_mp15_chain.out`).

## Texture fit (2026-11-20, merge point 16)

A1's texture-fit check found 38 errors (`oymap audit`, `output/studio_cal/xd22/s8_audit_before.txt`): 35
`textures.feature_repeated` on `xjshoji` (a 128 × 256 shoji panel, frame top and bottom, laid at 1 texel a unit along
the whole maze screens and the paper wall: up to 6.1 copies across and 1.5 down), `xjcrane` 1.4 × 1.4 on the crane leaf
and its back's `xjshoji` 1.5 × 1.5 (both had `size` of the leaf, 352 or 192 × 384, not the picture's own), and two
`textures.feature_cut` on the bell's top and underside (`xngong` laid 96 on its 128: fit does not stretch a level face).
Now none (`a7_xaudit.txt`, `s8_audit_after_full.txt`: infos only); build warnings 0 as before; textures 23 of 30 (no new).

- `gen.py` `PAPER`, `CRANE`: the pictures' own sizes, `fit: true` (one shoji per face; `uneven` on the paper, whose
  panels are 162-220 wide against the picture's 192 at full height).
- **The maze** (`screen()`, `SCREENS`): each of the eight screens is a row of paper panels between square black posts
  (`trim11_32`, 24 × 24, 384 tall; the screens' ends too, and one post at each corner of the cells and at the T of row A
  and the cross screen, which has a 56-long post at its foot by the south wall). No two panels touch. Each panel is its
  own platform and destructible and breaks alone, the posts stand: the first panel keeps the screen's id and number
  (`platform:screen_a`, destructibles 2-6 and 8-10 as before), the others are `platform:<screen>_2`, `_3` (destructibles 11-21).
  Panel widths: row A 202, 202, 172; cross 220; row B 4 × 166; cell south sides 2 × 192 and 2 × 182; cell sides 2 × 162.
- **The paper wall** (dojo / loft): two openings of 192 × 384 (`open:dojo_dorm_paper` at y -448 and the new
  `open:dojo_dorm_paper2` at -672, one link) with a pier of the wall 32 wide between, each a paper leaf
  (`door:paper_dorm`, destructible 7; `door:paper_dorm2`, destructible 16), the shoji stretched once on each.
- **The crane screen:** the crane once over the 352 leaf; its back one shoji stretched over the leaf (seen only through
  the lit paper).
- **The bell:** its top and underside the hanger's black wood (`trim11_32`); the gong picture stays fitted on its four
  sides.
- Pictures before and after, unbaked both (`output/studio_cal/xd22/s8_before/`, `s8_after/`, sheets
  `s8_sheet1-3.jpg`; the baked `assets_dev` before in `s8_before_baked/`).
- Playtests from the scratch root (`output/studio_cal/xd22/root`), 4 of 4 each (`output/studio_cal/xd22/s8_four.out`):
  `playtest` 131 of 131, `playtest_hostility` 47 of 47, `playtest_exit` 15 of 15; unchanged (the paper wall's
  destructible 7 is still the panel on the walk at y -448).
- For the lead: install and re-bake (the paper wall's openings and the maze's posts change the geometry).

**Texture fit exceptions:** none.

## Merge point 17 (2026-11-20, ninth session, lane A7)

- The themes' door `hkm2d` at [160, 320], the size of the exit's and the shrine door's leaves (same shape; the build
  keeps one size per texture), in L4 and `tools/gen.py`. 0 build warnings.

## Fifteenth session (2026-11-21, lane A7 sub-agent)

- **Shinobu talks herself** (merge point 22, `monsters[].npc`): `monster:shinobu` carries `npc: 4530` (scene actor
  24). Dropped from `gen.py`: `plate:shinobu`, `evt:shinobu_greets` and the map variable `greeted` (the source has no
  Shinobu, so no greeting unasked to keep; her presence is the done stage's, which stays); the cushion
  (`evt:shinobu`, now a `text` preset titled "Cushion") keeps only its line.
- `playtest.yml` (129 steps): at the done stage Shinobu clicked (`interact_actor` 24): her greeting, "The clan", and
  clicked again.
- `xcycle.sh`: build warnings 0, audit 0 errors, 0 warnings. Installed with bake (01:54:03), stale bakes 0. From
  `assets_dev`, 4 of 4 each: `playtest` 129, `playtest_hostility` 47, `playtest_exit` 15
  (`output/studio_cal/a7/s15_xd22_four.out`).

## Merge point 35 (2026-11-21, lane A7 twenty-fifth session)

- `playtest.yml` failed once at step 86: the Clan Master, alive since merge point 33 (storey-bound clears), stands in
  front of the party at the top of the stair. The walk there arrives within 128 (was 64); his death stays with the
  explicit clear after it. The map unchanged; 3 tests 4 of 4 (191 steps a round).
