# XD-18 Dragon Cave: L4 notes

Lane A7 phase 6 (agent `agent:xeen-a7-xd18`, seventeenth session), 2026-11-21. Map 9143, `xeen_xd18.blv`, class M,
`world: xeen`, on X7 Mount Firestone (the cave in the black crag at the north rim, behind the tax road), Q-C25
(optional), party 60-64, music 13. Built from `devdocs/xeen/mockups/act6_graphs/xd18.graph.yml` with decider D-57
(`mockups/act6_a7_decisions.md`), which wins where they differ, and A3's `source/quests/q-c25.yml` (every line of the
tax, the urn, the receipt and Dragon Lore is A3's hook).

Generator: `output/studio_cal/xd18/tools/gen.py` writes L1-L4 (`--levels` for L1-L3). Never hand-edit the written
files; diff L4 against `.oymap/last` before re-running it after any hand edit. The playtests are written by
`tools/gen_tests.py` from the built `ids.lock.yml`; the test rows by `tools/test_rows.py` (`--check` says whether A4's
real rows have landed). The cycle (generate, fmt, validate, build and install into the scratch root, audit) is
`output/studio_cal/xd18/cycle.sh`. Scratch root `output/studio_cal/xd18/root` (hard-link copy, `maps/` and
`events/maps/` real copies, every data table a real copy by `copy_tables.py`). No new texture.

## State

Done to L4 in the scratch root (2026-11-21, revision ff1811aa): validate clean, `fmt --check` clean, build warnings 0,
audit 0 errors 0 warnings (`output/studio_cal/xd18/audit.txt`); L1-L3 written and valid; every playtest 4 of 4. Left
for others: A4's house 4852, S's King skin and nest eggs (Blocked on); the lead installs and bakes.

## What was built

- **Floor 0 (z 0, the south band, west to east).** The mouth (1,024 x 768, 640 high; X7's daylight `xodaylt` in its
  west wall, the way out), the arrival `entrance:x7_mouth` 384 inside it facing east. The tax office hall (d16 stone,
  384 high): Scaldrith's door (house 4852: two wing panels `gkp103a`/`gkp103b` in the south wall), the counter with the
  urn (q-c25.urn), benches; the waiting room (a pair of doors) with the lectern of volume 1; the inner door (a pair,
  288 high) east. The scorched passage (384 wide, 288 high), the bone hall (2,048 x 1,536, 1,280 high; four Acid
  Dragons, two of them by the dragon road), the acid hollows (three), the last taxpayer (the knight's remains: the
  receipt; his strongbox), the sulphur vents (two, yellow steam), the fire crossing (a Fire pair), the egg cave (the
  nest's scraped hollow, the mother, a chest), the stair head (a 384-high tunnel) and the walked stair (32 steps of 32,
  north, down 1,024).
- **Floor -1 (z -1,024, north band).** The stair foot (a bent low tunnel), the great roost (3,072 x 2,688, z -1,024 to
  1,024; the floor-0 ledge 384 wide along its south wall behind a 128 rock lip; four Fire and two Frost Dragons), the
  steaming pools (a `wtrtyl` pool, steam; three Fire), the east den (two Fire, a chest), the old roost (three Fire), the
  ember gallery (a 768 dragon road; a Fire pair), the library of Dragon Lore (d16, 1,280 high, a course of bookshelves,
  shelves 2-4 and the ledger stand; two Frost Dragons; east and north pairs of leaves, 288 high), the King's door
  antechamber (shelf 5; the King's door, a pair 384 x 288), the Dragon King's hall (2,688 x 2,048, 1,536 high, the dais
  with heaps of `xncoins`, goblets and bowls; the King and two Frost Dragons), the hoard behind the grate (`xkportc`,
  rises at the King's death), the starwell (2,560 x 2,048, 1,536 high; the slot of stars 2,048 x 640 in its north wall,
  sill 640, `sky: true`, X7's preset `ashen` in atmosphere.yml; three Frost), the frost den (a Frost pair) and the rime
  cave (three Frost, a chest).
- **D-32.** Every party passage between dragon halls is 288 high (the stair tunnels 384, no dragon fits); the dragon
  roads (768) join only the bone hall (onto the ledge), the roost, the ember gallery and the starwell.
- **Counts.** 25 rooms, 25 sectors (M: 20-45), 60.4 M units² of floor by `oymap metrics` (M: 30-90). 6 door objects
  (5 pairs and the grate) plus the office's house door: 7 (M: 6-16). 5 chests T6 (the strongbox, the egg cave, the east
  den, the rime cave, the hoard). 41 monsters, all placed and hostile by room in groups 10-33: Acid Dragon 11641 (66) x
  9 on floor 0, Fire Dragon 11642 (75) x 17 (3 on floor 0), Frost Dragon 11643 (85) x 14, the Dragon King 11645 (110):
  66.64k per member, 69.94k with the King (D-57). Rest encounters 0 (row 9143 encounter 0, no slots). Map card in
  project.yml: treasure 6, lock 20, trap 10, perception 20 (A2's row's values), music 13, refill 672, environment cave.
- **Textures:** 15 distinct (built map, `oymap metrics`): d17 `t68a02b`, `t68a02a`; d16 `gtrlwal3`, `gtrlflr`, `tfb11`,
  `gtrlrf2`, `gtrlrf3` (also the benches, counter, lectern and chests), `gtrltrm2`, `t1books` (the bookshelves; d16's
  `t1books1` is plain board), `gkp103a`/`gkp103b`; `wtrtyl`; Xeen's `xodaylt`, `xkportc`, `xncoins`. **0 new:** the
  dais with heaps and banks of shipped `xncoins`, goblets and bowls reads as a hoard in the tour
  (`output/studio_cal/xd18/shots2/08-dais_close.png`), so `xdhoard` is not made (D-57).

## Count exceptions

- 40 monsters (and the King) under M's 45 (D-57 Q1): the source's dragons and MAPS's count.

## Mechanisms and the qbits (D-43)

| Qbit | Name | Set by | Shows |
| --- | --- | --- | --- |
| 118100 | inner_door_open | the inner door's click with tax_paid (`q-c25.inner_door` true) | the inner door open in the same visit and on every load |
| 118101 | king_slain | the kill timer (`evt:king_dead`, every 2 s) | the hoard's grate up in the same visit and on every load |
| 112500 | (A3's tax_paid) | Scaldrith's 'The tax' | read by the inner door |

## Measurements

- **The exit's landing** on X7 (playtest_exit, 4 of 4): (-4096, 16896, 2145) facing south (1536): X7's named
  arrival `entrance:xd18_mouth`.
- **The tax throw's landing** (playtest_tax, 4 of 4): the same point, (-4096, 16896, 2145) facing 1536; A3's fail line
  ("Tax first," says the door...) on the status line, then the throw at once (`leave`, no window: D-63 4); the
  door stays shut and 118100 unset.
- **The roost** (playtest_dragons): after 60 s with the party at the stair foot's low opening, two of the roost's four
  Fire Dragons press against the roost's east wall at (8132, 0, -1024), 60 short of the wall, and get no further; the
  other two stay at their posts. No Fire Dragon in the foot, none extra in the pools, old roost, crossing, library or
  office.
- **The starwell slot** (playtest_dragons): a Frost Dragon summoned pressed into the slot (4736, 2620, -100) is pushed
  back to (4534, 2359, -337) within 0.5 s and settles at the wall's foot (y 2628); the starwell's three end at y 2628
  too; all 15 Frost Dragons alive and in the map after 40 s. The `sky: true` face holds a flyer (nothing for A1).
- **The ledge lip** (playtest_dragons): walking 3 s straight at it from y -2080 the party stops after 219 (y -1861,
  the lip's face at -1832), z 0 every run: the 128 lip stops a walking party; no raise to 192 needed.
- **The quiet arrival** (playtest_hostility): 10 s at the arrival, not immortal, party unchanged.

## Into the world (for the lead and the neighbour's lane)

- **Arrival from X7:** `entrance:x7_mouth` at (384, -3072), floor 0, facing east (0), 384 inside the mouth. X7's
  `door:xd18` (A5) names it.
- **The way out and the throw:** the exit preset at the mouth's daylight ("Exit Dragon Cave?", aaze0050:17, as the
  window's meaning) and the inner door's `{leave}` (at once, D-63 4) both go to X7's named arrival `entrance:xd18_mouth`
  ((-4096, 16896, 2144) facing south in X7's studio file).

## Original lines (aaze references)

aaze0050:1 (the urn after the tax, A3's q-c25.urn), :2 (the inner door's fail, A3's fail_text), :5-10 (the hovers
"Dragon Lore Volume 1" ... "Volume 5", "The Art of Taxation"), :17 (the exit's meaning). New map lines (no source
line): the arrival ("Sulphur and old smoke..."), the ledge, the starwell and the library's first looks, the grate's
refusal, the King's death.

## Test rows

Only in the scratch root's copied tables, written by `output/studio_cal/xd18/tools/test_rows.py`:
- `house_data.txt` 4852 "The Dragon Tax Office" (a residence copied from 4019's shape) and `house_animations.txt` 4852
  with resident 5702; `npc.txt` 5702 Scaldrith's 2D location 0 -> 4852. A4's `source/towns/xd18.yml` lists the house
  as `planned: true`, so the generated tables have no row yet.
Landed and used (no test row): map row 9143 (`map_stats.txt`, `bolster_maps.txt`), 11641-11643, 11645.

## Blocked on

- **A4:** house 4852 (the Dragon Tax Office, Scaldrith 5702) in the generated tables (`planned: true` today); until
  then the office door enters nothing in `assets_dev` (the test rows above stand in, in the root only).
- **S (and A2):** the Dragon King's skin `xcdr_king` (D-57 Q3): 11645's descriptor still binds `mm6_cdr1` with
  `cdr1_c` (the Fire Dragon's look). The eggs of the egg cave's nest (the same shipped decoration S picks for FD-04's
  nest, D-57 S): the hollow is built, the eggs are not placed.

## Words needed

- Door `pictures` take no `uneven`; a parapet stands on the room's floor, never on a level (the ledge's lip is a
  platform with `base` instead).

## Dressing, lights, doors, texture fit

`oymap audit --world xeen --reach --solve`: 0 errors, 0 warnings; build warnings 0. Infos: `xodaylt` squashed on the
mouth's daylight (meant: `uneven`); the office door's two clicks "show nothing" in the sandbox (they enter house 4852).

## DECIDE (cheaper-to-reverse option taken)

1. **The throw** (decided, D-63 4): `leave`, at once, no window, as the fail line ("you are outside on the mountain")
   says; changed in gen.py and `playtest_tax` in the eighteenth session.
2. **The ledge pair** of the graph stands in the bone hall by the dragon road: a 487-tall dragon (radius 238) does not
   fit on a 384-wide ledge behind the lip; they fly onto it.
3. **The King's door** is 384 wide, not the graph's 512 (D-57 sets only its height): a 128-wide wing picture on a
   256-wide leaf is squashed (a build warning).
4. **The scorched passage** is 384 wide (the graph's 256 leaves no wall beside the 256 inner door).

## Checks (scratch root, merge point 25 binaries)

`output/studio_cal/xd18/four_final.out`, logs `output/studio_cal/xd18/a7_xrun/<test>_<n>.log`: playtest (100 steps),
playtest_tax (20), playtest_dragons (52: D-57's three checks), playtest_exit (15), playtest_hostility (25): each 4 of 4.

## Pictures

`output/studio_cal/xd18/shots/` (16, `tour.yml`; sheets `shots_sheet1.jpg`, `shots_sheet2.jpg`) and `shots2/` (9 after
the fixes: the bookshelves, the wooden furniture, the dais's gold; `shots2_sheet.jpg`). Unbaked: the light is the
editor's flat one. Looked at: the slot shows X7's sky; the library reads as a library only with `t1books` (fixed); the
dais reads as a hoard with the banked `xncoins` (no `xdhoard`); the King wears the Fire Dragon's look (S's skin).

## What the user should look at

The view down from the ledge into the roost, the starwell's slot of sky, the library and the King on his gold. The tax
office's throw: out to X7 at once (D-63 4). Lighting is unbaked in the scratch root.

## Installed (2026-11-21, lane A7 lead, seventeenth session)

- A4's house 4852 and Scaldrith 5702 landed (the root's test rows replaced by the real tables, `refresh_tables.py`);
  rebuilt with merge point 25's oymap (build warnings 0), installed with its bake 04:33:48 (`install_baked.sh`, profile
  `tools/lighting/baked_indoors/profiles/xeen_xd18.yml`), stale bakes 0. Audit from `assets_dev` 0 errors, 0 warnings
  (`output/studio_cal/xd18/audit_assets_dev.txt`). **20/20 from `assets_dev`** (playtest 100, tax 20, dragons 52, exit
  15, hostility 25; `output/studio_cal/a7/s17_xd18_four.out`).
- Open: S's `xcdr_king` and the nest eggs; X7's `door:xd18` to `entrance:x7_mouth` (A5).

## Eighteenth session (2026-11-21, lane A7 lead)

- D-63 4: the tax throw is `{leave: exit:x7_mouth}` (at once, no window); `playtest_tax` lands on X7 at entrance:xd18_mouth with no window, the cancelled branch dropped, 118100 still unset after the landing.
- Installed with its bake 05:17:26 (`output/studio_cal/a7/s18/install_queue.sh`), stale bakes 0; audit from `assets_dev` 0 errors, 0 warnings (`output/studio_cal/a7/s18/audit/xd18.txt`); **20/20 from `assets_dev`** (playtest 100, tax 15, dragons 52, exit 15, hostility 25; `output/studio_cal/a7/s18_four.out`, merge point 25/26 binaries).

## Twenty-sixth session (2026-11-22, lane A7): a real cave (D-89 identity) and the inward tax door (D-89 1)

- **Identity (D-89, `reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2):** `project.yml` `identity: {shape: cave, family: d17,
  seen: [...]}`. gen.py's new "D-89 identity" pass: 15 cave rooms lose their rectangle's corners (each cut on a slant
  with a break pushed in, up to 12 sides; a corner is cut only as far as every chest, decoration, platform, ladder and
  dragon of the room keeps clear, and stays square where a shared opening needs the wall: bone hall NE, vents NE, pools
  SW/NW, starwell NE/NW/SE, crossing SW/NW), rough walls everywhere in them, floors that rise and fall between points
  inside the room (`floor_points`, grid 448, up to 96; the walls' feet and every sill stay level), roofs vaulted up
  to 384 (`ceiling_points`) and hanging rock (`stalactites`) in the high caves; the roost keeps its ledge and lip and
  gets the uneven floor and vault. The tax office, waiting room and library are cut into the rock (t68a02b walls and
  roof, worn floor; counter, benches, urn, doors and the shelf band are the fittings). The scorched passage is charred
  (`xochar`). The King's hall and the hoard are floored with gold (xncoins) heaped into a mound 192 high under the
  Dragon King (the flat dais and the four gold boxes gone). The starwell's slot shows stars (`open_sky` preset
  `night_stars`). Cave shape (`oymap metrics`): floor uneven 0.088 -> 0.262 -> **over 0.30** (no `identity.cave_shape`
  warning), ceiling spread 24 -> 187, ceiling uneven 0.035 -> 0.72, rough walls 0.118 -> 0.312.
- **D-89 1 (A3 34th's request):** the inner door opens to everyone (sets 118100, q-c25.inner_door, no throw); the Dragon
  King's door is `XeenQuests.hook("q-c25.king_door")` (tax first, "Tax first," on the status line, nobody moves).
  `playtest_tax.yml` now checks both. `tools/xeen/check_exits.py` lost the inner door's SPECIAL line; `quests.py`'s
  D89 open row for it removed.
- F13: gen_tests.py writes the status-line checks (volumes 1-5, the Art of Taxation) itself now.
- Installed 00:36 (Lua, scene, BLV), baked 00:42 (`output/studio_cal/a7/s26/bakew.sh`); build warnings 0, audit 0/0,
  check_exits 0, check_drops 0 pockets. Name test: before `output/studio_cal/a7/s26/xd18/before_sheet.jpg` (16 shots),
  after `after_sheet.jpg` (18: + the mound, the hollows); the arrival opens on rock, the first fight room (bone hall)
  is a broken-floored cave, the signature room is the King on his gold.

## Mouth exit kept clear of rough rock (2026-11-23, agent:xeen-xd05-exit)

The rough wall behind this map's exit stood in front of its black face (no click reached it: the XD-05 Discord report,
`tools/xeen/check_exits.py` `exits.hidden`). `tools/xeen/cave_shape.py` `flat_behind_panels` now gives the exit's
wall a flat panel under it (the generator writes it); rebuilt, installed and baked; all playtests pass. See XD-05's
NOTES.md, same date.
