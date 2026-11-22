# FD-02 Southern Sphinx: L4 notes

Lane A7 phase 6 (agent `agent:xeen-a7-fd02`, seventeenth session), 2026-11-21. Map 9180, `xeen_fd02.blv`, class S,
`world: xeen`, on X6 Desert of the Sphinx (the half-buried sphinx on the west rim), M40, Act VI, party 58-61, music 46.
Built from `devdocs/xeen/mockups/act6_graphs/fd02.graph.yml` with decider D-57 (`mockups/act6_a7_decisions.md`), which
wins where they differ, and A3's `source/quests/m40.yml` (landed during the build: every line is A3's hook).

Generator: `output/studio_cal/fd02/tools/gen.py` writes L1-L4 (`--levels` for L1-L3). Never hand-edit the written
files; diff L4 against `.oymap/last` before re-running it after any hand edit. The playtests are written by
`tools/gen_tests.py` from the built `ids.lock.yml`. The cycle (generate, fmt, validate, build and install into the scratch
root, audit) is `output/studio_cal/fd02/cycle.sh`; the pictures `output/studio_cal/fd02/tour.yml`. Scratch root
`output/studio_cal/fd02/root` (hard-link copy, `maps/` and `events/maps/` real copies, every data table a real copy,
refreshed with `output/studio_cal/a7/resync_root.py fd02 <root>`); the two new textures are installed only there.

## What was built

- **The breast (z 0 to -256).** The arrival `entrance:x6_door` on the top step 256 inside the two leaves
  (`egydrlgl`/`egydrlgr`, the way out), facing west; eight broad steps down to the body's doors (a pair,
  `egydrsml`/`egydrsmr`). Quiet: the doors keep the hall's mummies from seeing or reaching the arrival (see DECIDE 1).
- **The body (z -256).** The hall of embalming (2,176 x 896, 640 high), two embalming tables by the walls, jars; the
  embalmer's table gives the two Might Boosts once per game (A3's `m40.embalming_table`, 118119). West of it the two
  death runs (1,280 x 384, 512 high): the Swinging Death (four blades sweeping out of slots in the north wall) and the
  Chopping Death (three blades dropping out of the ceiling), each blade's underside 216 above the floor, a plate under
  each, a toll-keeper's carved figures (`egywlspb`) at each run's mouth. Then a door into each Preservation Room (three
  rune stones each, `xsrunes`; a great sarcophagus each, Might 60) and the canopic chamber where they meet (shelves of
  jars, the crypt's arch and its rune plaque).
- **The stair of the name.** From the hall's north-east corner 32 steps of 32 climb 1,024 north to the top landing (a
  level, the question's step source) and the door of the name; a rune plaque at its foot.
- **The head (z 768).** The Home of the Aged (1,280 x 1,024): `xsshelf` shelves as a band round the walls over an
  `egywla` footing, `egywlh` panels above, the inlaid star ceiling; the east wall is the face with two eyes
  (`egyswbon`) and two bright daylight lights before them; four books on lane S's carved lecterns (`xeen_lectern`); Picard the Aged by his very good chair
  (lane S's carved throne `xeen_throne`, row 4043, D-66: its back to the west wall, looking east, on the old block
  seat's centre (-1696, 3200); hover "Throne of Legends"; it replaced D-63 14's block throne of `cedsqrdk` in the
  twenty-first session). The two lappet galleries (north, south): two empty sarcophagi, two Phase
  Mummies and a find (a T6 item of any kind) each.
- **Under the sand (z -1,280).** The crypt of the dragons (2,176 x 1,536, 1,344 high, brick ribs): through the 288-high
  arch from the canopic chamber onto a gallery level at -256 with parapets, a flight of 32 steps with side walls down to
  the floor; four Dragon Mummies. West through a wide opening (768 x 640) the stalls: a wall between two stalls, a
  dragon mummy in each, and at their end the alcoves under a low roof (256 high): the illusion heap (`xncoins`) north,
  the embalmer's chest south.
- **Counts.** 13 rooms, 13 sectors (S: at most 15), 16.7 M units² of floor by `oymap metrics` (levels and flights
  counted; S: at most 20). 6 doors (one pair)
  plus 7 blade movers. 3 chests T6 (two great sarcophagi with Might 60, the embalmer's; all three sandstone boxes). 26 monsters, all placed and
  hostile by room in groups 10-19: Ghost Mummy 11273 (62) x 16 in the body, Phase Mummy 11274 (72) x 4 in the
  galleries, Dragon Mummy 11672 (65) x 6 in the crypt (4) and stalls (2): 31.07k per member (D-57). Picard the Aged
  11922 (npc 5704) peaceful, immobile, group 40, not counted. Rest encounters 0 (row 9180 encounter 0, no slots).
  Map card in project.yml: treasure 6, lock 20, trap 10, perception 20 (A2's row's values), music 46, refill 672.
- **Textures:** MM6 Tomb of VARN (pyramid.blv), the set's other half: `egywlj`, `egywla`, `egywalg1`, `egywalgm`,
  `egywlh`, `egywld`, `egyflorf`, `egyflord`, `egyceild`, `egyceila`, `egymedb`,
  `egytrmc`, `egytrmas`, `egywlspb`, `egyswbon`, `egydrsmd`, `egydrsml`/`egydrsmr`, `egydrlgl`/`egydrlgr`, Xeen's
  `xncoins`, MM7's brushed steel plate `ch004i` on the seven blades only (D-63 14; the pyramid set has no metal;
  laid at 128 x 112, it tiles across only); no striped `egycol64`, no `egywle`/`egywlc`. 24 distinct (installed map,
  `oymap export`) of the 30 cap, 2 new (`xsshelf`, `xsrunes`); Picard's throne is S's decoration (`cedsqrdk` gone).

## Mechanisms and the qbits (D-43: each shows its state, on every load)

| Qbit | Name | Set by | Shows |
| --- | --- | --- | --- |
| 118110-118115 | rune_p ... rune_d | A3's `m40.rune_<c>` (a stone's click) | the sixth (any stone once all six) calls `m40.runes` |
| 118116 | swinging_paid | A3's `m40.mask_swinging` (2,000 gold) | the four blades go into their wall slots and stay (timer `evt:swing_still`, also on load); the plates do nothing |
| 118117 | chopping_paid | A3's `m40.mask_chopping` | the three blades stay up in the ceiling |
| 118118 | illusion_gone | A3's `m40.illusion` (the heap's click) | the heap hidden and passable, on every load |
| 118119 | embalming_boosts | A3's `m40.embalming_table` | the two Might Boosts given once per game |
| 111800 | m40 name_said | `m40.name_right` (PICARD on the landing or at the door) | the door of the name opens in the same visit and on every load |
| 111801 | m40 done | Picard's topic with the widget | the Chime of Opening (12373) for the widget (12315) |

- The name: the landing level's step asks "What is my name?" on every climb until named; so does the door's click from
  the landing. `m40.name_wrong` / `m40.name_right`; the first step into the Home calls `m40.stair` (its line).
- The masks: the map asks "For 2,000 gold I can protect you from the ... Death. Will you pay?" (aazex125:9-10, the sum
  rescaled); Yes calls the hook (it pays, sets the qbit and says its line; without 2,000 its fail line); No
  `m40.mask_no` ("Begone, then!"), no throw. Every later click of a paid mask offers the clue "For another 500 I'll give
  you a clue. Will you pay?" (aazex125:11): Yes `m40.mask_clue`, No `m40.mask_no`.
- The blades: a timer every second toggles each run's blades (alternate ones together) until paid. Damage is the plates'
  (a step event per plate, once per crossing): 8 Physical per Swinging blade, 11 per Chopping blade.

## Measurements

- **Level-59 HP** (the playtest party, measured): Knight 335, Cleric 150, Archer 210, Sorcerer 140.
- **One unprotected crossing** (playtest_traps, measured): the Swinging Death 32 per member (4 x 8: the sorcerer 22.9 %,
  the knight 9.6 %), the Chopping Death 33 (3 x 11: 23.6 % / 9.9 %). D-57's "about 6 % / 8 % per blade" taken on the
  weakest member, so nobody passes 25 %.
- **The exit's landing** on X6 (playtest_exit): X6's named arrival `entrance:fd02_door` (-12288, -10240, 1536) facing
  east (0), the point A5 moved out of the sphinx (D-57's -12144 is not on a cell; nineteenth session).
- **The quiet arrival:** without the body's doors eight Ghost Mummies reached the arrival within 7 s and hurt the knight
  (335 to 113). With the doors the party stands 10 s unharmed (playtest_hostility).

## Into the world (for the lead and the neighbour's lane)

- **Arrival from X6:** `entrance:x6_door` at (-256, 0), floor 0, facing west (1024), on the top step 256 inside the
  leaves. X6's `door:fd02` (A5) names it; X6's door is sealed today ("(Not open yet.)" in `xeen_x6.lua`).
- **The way out:** the exit preset on either leaf ("Exit the Southern Sphinx?", aazex125:3, as the window's meaning) to
  X6's named arrival `entrance:fd02_door` (-12288, -10240, 1536) facing east (`project.yml` neighbours; by name since
  the nineteenth session).

## Original lines (aaze references)

aazex125:0-1 "Preservation Room" (step lines), :3 the exit's meaning, :5 "You are too weak to open the sarcophagus.",
:9-14 the masks (A3's hooks), :16-19 the name (A3's hooks); aazex126:11 "Throne of Legends" (the chair's hover, A3's
`m40.chair`), :13-21 the four books (map text, adapted: "beggar" for the source's "begger", the excised princess);
aazex127:2-9 the runes and the two plaques (A3's hooks), :13 "Nothing here." (the heap once gone, the galleries'
niches), :14 the illusion (A3's hook).

## Test rows

None. A2's real rows landed before the build and are used: map row 9180 (`map_stats.txt`, `bolster_maps.txt`), 11273
Ghost Mummy, 11274 Phase Mummy, 11922 Picard the Aged (npc 5704).

## Blocked on

- Nothing. (S bound `Xeen Picard the Aged` and the Ghost/Phase Mummies (actors.yml, S session 7); Picard draws
  his body in the eighteenth session's tour.) The exit names X6's `entrance:fd02_door` (nineteenth session).

## Words needed

None. (The studio has no swinging pendulum mover; the Swinging Death's blades sweep sideways out of wall slots as
linear movers, which reads as the source's swing.)

## Dressing, lights, doors, texture fit

`oymap audit --world xeen --reach --solve`: 0 errors, 0 warnings (`output/studio_cal/fd02/audit.txt`); build warnings 0.
Exceptions: none since the twenty-fourth session (the eighteenth session's 14 `textures.tile_seams` on the old
16-wide blade tops and undersides went with the slabs).

## DECIDE (cheaper-to-reverse option taken)

1. **A door between the breast steps and the hall** (not in the graph, which has the way open). Without it eight Ghost
   Mummies see and reach the arrival in seconds (D-11.3 broken). A pair of leaves (`egydrsml`/`egydrsmr`) at the steps'
   foot, as D-57 made FD-03's east way a door: 6 doors (S band 3-8). Alternative: move the hall's four mummies to the
   back rooms and bend the way in out of sight (more geometry).
2. **The galleries' finds** (the graph's "A2: two T6 potions, a T6 gem"): a T6 item of any kind once each
   (`give_item: {level: 6}`) until A2 names fixed items.
3. **The clue after paying** is offered on the mask's next click, not straight after the payment, so that A3's
   payment line is seen (a question right after it replaced it).
4. **The crypt's way down** is a gallery inside the arch and a flight of 32 steps in the crypt itself (13 rooms, not a
   separate stair room); the arch is the opening (288).

## Checks (scratch root, merge point 24 binaries)

`output/studio_cal/fd02/four_final.out`, logs `output/studio_cal/fd02/a7_xrun/<test>_<n>.log`: playtest, playtest_traps,
playtest_crypt, playtest_exit, playtest_hostility, each 4 of 4 (see the report).

## Pictures

`output/studio_cal/fd02/shots/` (17, `tour.yml`; sheets `shots_sheet1.jpg`, `shots_sheet2.jpg`) and `shots2/` (the steel
blades, the wooden chair, the eyes after the fixes; `shots2_sheet.jpg`). Unbaked: the light is the editor's flat one.

## What the user should look at

The two death runs (the blades are the tell; the toll-keepers' figures by the run mouths), the Home of the Aged (the
shelves, the eyes' light, Picard in his chair), the crypt from its gallery. Lighting is unbaked in the scratch root.

## Installed (2026-11-21, lane A7 lead, seventeenth session)

- Rebuilt in the root with merge point 25's oymap (03:57:50; build warnings 0, audit 0/0), `xsshelf` and `xsrunes`
  installed in `assets_dev` (`xtex.py install --root assets_dev --world xeen`; masters in
  `assets_source/worlds/xeen/textures_x4/`), the map installed with its bake 04:00:33 (`install_baked.sh`, profile
  `tools/lighting/baked_indoors/profiles/xeen_fd02.yml`), stale bakes 0. Audit from `assets_dev` 0 errors, 0 warnings
  (`output/studio_cal/fd02/audit_assets_dev.txt`). **20/20 from `assets_dev`** (playtest 106, traps 84, crypt 17, exit
  15, hostility 24; `output/studio_cal/a7/s17_fd02_four.out`).
- Open: X6's
  `entrance:fd02_door` move and `door:fd02` (A5), then the exit back to the name. Polish: the lecterns are blocks (a shipped decoration
  when one is found, D-63 14).

## Eighteenth session (2026-11-21, lane A7 lead)

- D-63 14: the seven blades 16 thick in MM7's brushed steel `ch004i` (sides, top and underside), the throne of `cedsqrdk` (seat, high back, two arms with the 'Throne of Legends' hover, footstool; Picard moved 32 east to (-1520, 3200) to clear it). Baked shots from the runs' mouths and of the throne: `output/studio_cal/fd02/s18/sheet.jpg` (shots `s18/shots/`, tour `s18/tour.yml`): the chopping blades read as grey steel plates, the swinging ones as steel warmed by the run's light; Picard now draws S's body. Lecterns: polish (D-63 14).
- Installed with its bake 05:16:20 (`output/studio_cal/a7/s18/install_queue.sh`), stale bakes 0; audit from `assets_dev` 0 errors, 14 warnings (the blades' tile_seams, kept above) (`output/studio_cal/a7/s18/audit/fd02.txt`); **20/20 from `assets_dev`** (playtest 106, crypt 17, exit 15, hostility 24, traps 84; `output/studio_cal/a7/s18_four.out`, merge point 25/26 binaries).

## Nineteenth session (2026-11-21, lane A7 lead)

- Merge point 27 (oymap 06:06:32): the peaceful-group load event runs once per fill (map var
  `studio_peaceful_groups`), first of the load events; the exit names X6's `entrance:fd02_door` (-12288, -10240, 1536)
  facing east (A5's moved point, X6 installed 03:43). Only the Lua and the studio file changed (the BLV and scene byte
  for byte the installed ones), so no rebake; installed 06:15:44, stale bakes 0. Audit from `assets_dev` 0 errors, 14
  kept tile_seams (`output/studio_cal/a7/s19/audit/fd02.txt`); playtests 2 of 2 from `assets_dev`
  (`output/studio_cal/a7/s19/two_fd02.out`).

## Twenty-first session (2026-11-21, lane A7 lead)

- Picard's throne is lane S's `xeen_throne` (row 4043, D-66; 250 tall, 150 x 133, origin at its foot's centre),
  `deco:throne` at the old block seat's centre (-1696, 3200) facing 0 (east, down the room; `yaw_offset` makes `facing`
  the way it looks), its back to the west wall. D-63 14's five `cedsqrdk` blocks are gone (24 textures, `cedsqrdk`
  out); the hover "Throne of Legends" and A3's `m40.chair` are one event, `evt:throne`, on the decoration. Lecterns: no
  lectern decoration exists yet (S), so they stay blocks.
- Baked shots `output/studio_cal/a7/s21/shots/fd02/` (throne_far, throne_near, throne_side): the carved throne stands
  against the shelves with its red cushion, Picard before it.
- Built with the oymap of merge point 27, installed with its bake 08:03:55 (`output/studio_cal/a7/s21/install.sh`),
  stale bakes 0. Audit from `assets_dev` 0 errors, 14 kept tile_seams (`output/studio_cal/a7/s21/audit/fd02.txt`).
  **20/20 from `assets_dev`** (playtest 106 (it clicks `evt:throne`), traps 84, crypt 17, exit 15, hostility 24;
  `output/studio_cal/a7/s21/four_fd02.out`).

## Twenty-second session (2026-11-21, lane A7 lead)
- **The lecterns** are lane S's `xeen_lectern` (row 4050: a carved stand in the throne's wood with an open book, 54 x 41
  at the desk, 120 tall; `yaw_offset` -90 makes `facing` the reader's side): `deco:book_1`-`4` where the four
  `platform:book_<n>` blocks stood, floor 768, centres 45 off the wall (backs 24 off): (-1600, 3667) and (-704, 3667)
  facing 270 (south), (-1664, 2733) and (-1088, 2733) facing 90 (north). `evt:book_1`-`4` (title "Book", the texts in
  a window) are on the decorations; playtest clicks `evt:book_4`. 24 textures (unchanged: `egyceila` stays the ceiling).
- Built with the oymap of merge point 29, installed with its bake 09:02:02 (`output/studio_cal/a7/s22/install.sh`),
  stale bakes 0. Audit from `assets_dev` 0 errors, 14 kept tile_seams (`output/studio_cal/a7/s22/audit/fd02.txt`).
  **20/20 from `assets_dev`** (`output/studio_cal/a7/s22/four_fd02.out`).
- Baked shots `output/studio_cal/a7/s22/shots/fd02/` (lecterns_north, lecterns_south, lectern_near, lectern_side; sheet
  `../fd02_sheet.jpg`): each lectern by the shelves with its book open toward the room.

## Twenty-fourth session (2026-11-21, lane A7 lead): real blades (review G3 row 54)

- The reviewer found the seven blades "thick hanging slabs as wide as the corridor": they read as falling blocks. Each
  blade is now a mover 4 thick and 28 high (`ch004i` at its native 64 texels, `scale` 5.5 so one picture runs the whole
  352 with no repeat, `offset` [0, 30] for the plate's middle, not its border band) with one part under it, the
  bevelled edge, 2 thick and 8 high in the paler seamless `gn_mtl01` (128, the face tiles along only): 36 high in all
  (was 16 x 112, the plate tiled every 128). Same places, travel, speed, states, plates, events and damage; the edge's
  underside is 216 above the floor at the walk as before. gen.py's `blade()`; 25 of 30 textures (gn_mtl01 new).
- Built with the oymap of merge point 31: build warnings 0, audit 0 errors and 0 warnings (the 14 kept `tile_seams`
  gone). Installed 16:35:39, baked from `assets_dev`. Pictures before `output/studio_cal/a7/s24/shots/fd02_before/`,
  after `.../fd02_after/` (sheet `output/studio_cal/a7/s24/shots/fd02_sheet.jpg`).
