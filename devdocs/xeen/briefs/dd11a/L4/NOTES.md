# DD-11A Troll Holes, first pocket: L4 notes

Lane A7 phase 3 (agent `xeen-a7-dd11`), 2026-11-20. Map 9162, `xeen_dd11a.blv`, class S, `world: xeen`. Built from the
MU-6 graph `devdocs/xeen/mockups/act3_graphs/dd11a.graph.yml` and `notes_d2.md` with D-25
(`mockups/act3_a7_decisions.md`), which wins: the burrow's top is the `exit` preset with no "Exit the Troll Hole?"
question (aaze0040:12 stays in the ledger). Generator `output/studio_cal/dd11a/tools/gen.py` (shared helpers
`output/studio_cal/dd11/tools/lib.py`; writes L1-L4; never hand-edit the written files). Cycle
`output/studio_cal/dd11/cycle.sh dd11a`; playtests `output/studio_cal/dd11/play.sh dd11a <name>` and `four.sh`;
pictures `output/studio_cal/dd11/shots.sh dd11a`. Scratch root shared by the three pockets: `output/studio_cal/dd11/root`.

## What was built

A warren dug under D2's forest at two depths. x east, y north; the pit (where D2's first hole drops the party) is at the
origin.

| Room | Floor | Size | Monsters (placed, group) | What |
| --- | --: | --- | --- | --- |
| Pit bottom | 0 | octagon 768 across, shaft to 768 | — | Start; a mound of earth and bones; D2's sky at the shaft's top |
| Root tunnel | 0 | 320 × 1,280 | 3 Troll (10) | East to the midden; the hollow off its south side |
| Bone midden | 0 | 1,280 square, domed | 3 Troll (11) | Bone heaps; the bone slope (a sloping platform, 0 → 192) up the north wall to the boulder; an Expired Adventurer |
| Dead thief's crawl | 192 | 576 × 448 | — | The dead thief (Corpse05, the letter), his pack (T3) |
| Sleeping hollow | 0 | 1,024 × 1,248, straw | 4 Troll (12) | Three nests; the burrow leaves its west wall |
| The burrow up | 0 → 384 | 224 × 1,280 | — | Root-floored ramp west to the sod hatch (the exit, daylight) |
| Bone slope | 0 → −384 | 256 × 1,536 | — | Bones underfoot down to the larder |
| Troll larder | −384 | 1,024 × 1,152 | 2 Troll, 2 Troll Guard (14) | Hides and carcasses on the south wall |
| Guard den | −384 | 832 × 896, straw | 3 Troll Guard (15) | Behind the log door; their chest (T3) |
| Dripping seep | −384 | 896 × 1,024 | 2 Troll, 1 Troll Guard (13) | Pool (wtrtyl, water); the root stair north |
| Root stair | −384 → 0 | 384 × 768, 12 steps | — | Up to the sleeping hollow (the loop) |

**Counts and sizes** (`oymap metrics`, `output/studio_cal/dd11a/metrics.json`): 11 rooms (12 sectors with the BLV's
sector 0), 8.3 M units² of floor, 477 faces, 20 monsters (14 Troll 11690 at 18, 6 Troll Guard 11691 at 28), 2 chests
(T3, T3), 3 doors (the boulder, the wicker gate, the log door), 1 loop.

**Textures:** 16 distinct, 0 new: 7dirttyl (walls, roofs, floors), straw, xohide (the larder's hides), xdbark (log door,
root floors), xobones (bone slope, heaps), xopoles (wicker gate), wtrtyl (pool), xodaylt (the sod hatch's daylight),
t66cave (the boulder), the plain chest set. Cap 30.

**Monsters.** A2's Troll Holes rows (D-25 Q7), all placed, one group per room, **without** the hostile flag: the world's
relations.yml decides (xeen_warren_trolls long at load, friendly on 113261/113262, long again on 113263).

**Map card.** Music 8; cave; treasure 3; lock 6, trap 3, perception 6; refill 672; bolster LowerToEqual; encounter 10 (D-33: the warren trolls follow relations.yml, so a rest spawn after the tribute is friendly)
(every troll placed; a rest spawn in a befriended pocket would be odd); slot 1 `Xeen Warren Troll`, tier 1, [2, 3],
weight 100. Test row 9162 in the scratch root (copied from 9149's, music 8, the slot) until A2 writes it.

## Ways in and out (D-24, D-25)

- **In (A6's side):** D2's first hole (event 32) drops the party at the map's start, **(96, −32, 0) in room:pit, facing
  east (direction 0)**, beside the bone mound, facing the root tunnel. No way back up the shaft.
- **Out:** the burrow's sod hatch (`evt:hatch`, event 7, the `exit` preset: the game's leave window, no question) to
  `exit:d2_return`, A6's point **(−2048, −6144, 992) facing west (180°)**. `playtest_exit.yml` measures the landing at
  **(−2048, −6144, 993)**, standing there 2 s later.

## Hooks and lines

- `q-d13.thieves_letter` on the dead thief (`deco:thief`, hover "Dead thief"): A3's letter window (aaze0040:5), started
  113260 and the autonote; a second click its else text.
- Map qbits 110960-110969: **none used**.
- Original lines: the guild letter (aaze0040:5, A3's hook); "Expired Adventurer" / "Nothing here." (aaze0040:3-4) on a
  skeleton in the midden; "Chest" (aaze0040:0) on the den's chest. "Troll Hole. Descend?" (aaze0008:2) is D2's.
- Our lines: the landing ("You land on a mound of earth and old bones ..."), the midden's and the larder's step lines,
  the boulder's "You put your shoulders to the boulder, and it rolls aside."

## Checks (scratch root `output/studio_cal/dd11/root`, binaries of merge point 12)

- `oymap fmt --check`, `validate` (L1-L4 no issues), `build` (0 warnings), `audit --reach --solve`
  (`output/studio_cal/dd11a/audit.txt`): no error or warning; 9 of 11 sectors on foot with the doors shut, 11 with them
  open; info: xodaylt stretched on the hatch (meant, `uneven`).
- Playtests 4 of 4 each (`output/studio_cal/dd11a/four.out`, logs `output/studio_cal/dd11a/run/`): `playtest.yml` 55
  steps (landing line, the midden, the boulder, the letter and its else text, both chests, the loop, the burrow's top,
  reload "RELOAD ok at step 53"), `playtest_hostility.yml` 35 (hostile at load and after a reload; tribute 113261
  friendly, kept over a reload; hostile 113263 hostile again; kinds leave each other alone), `playtest_exit.yml` 15.
- Pictures `output/studio_cal/dd11a/shots/` (sheets `sheet1.jpg`, `sheet2.jpg`): unbaked (flat light; the lead bakes).
  Fixed after looking: the boulder was MM6's carved cave door (now t66cave rock).

## Words needed

- None new. (A decoration as a clicked source worked for the dead thief.)

## Dressing exceptions

None (audit clean). The bone heaps are low platforms against the midden's walls; the two chests stand by walls, far
from the doors.

## For the user

- The landing: look up the shaft (D2's sky), then the root tunnel ahead.
- The bone midden: the slope of bones up to the boulder, the dead thief and the guild's letter behind it.
- Whether the burrow's daylit hatch reads as the way out.

## Sixth session (2026-11-20, lane A7)

- **D-33 (2):** rest encounters 10 % (`lib.py` map card; A2's row has it).
- **Lamp rule:** lights written with negative heights (meant as absolute z) lay under the floor, and the burrow's or
  stair's daylight above its ceiling: each now over its floor inside its room (`gen.py`; A1's audit and
  `output/studio_cal/a7/lampcheck.py` clean).

## D-34: the Darkside view at the hatch (2026-11-20, lane A7, seventh session)

- The sod hatch's view (`exit:hatch`, an upright face at eye level) is DD-13's new `xddaylt` (D2's pass road between
  dark forest and rock under the dim amber-grey sky) in place of XD-05's sunny Cloudside meadow `xodaylt`; the shared
  `DAY_LIGHT` (the shaft's and the burrow top's daylight) dimmed from a noon white [205, 200, 185] to the Darkside's
  [150, 140, 122] (`output/studio_cal/dd11/tools/lib.py`; before: `lib_before_d34.py`). Picture:
  `output/studio_cal/a7/s7_look/dd11a/01-hatch_day.png`.
- Audit no error or warning, build warnings 0. Installed, re-baked; from `assets_dev`: playtest (55), playtest_hostility (35), playtest_exit (15) 4 of 4 each
  (`output/studio_cal/a7/s7_mp15_chain.out`).

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- The larder's hides: two single `xohide` panels 128 wide with dirt between (was one panel of 512, the hide 4 times; `panel:hides_s2` added).
- The shared `DAY_LIGHT` is now in L4 as D-34 meant ([150, 140, 122]; the seventh session's L4 still had the noon white).
- Audit: no `textures.*` finding.

## D-89 cave shape, identity and name test (2026-11-22, lane A7 28th-29th sessions)

Shared pass `tools/xeen/cave_shape.py` (corners cut where no other room, object or numbered wall is near, `rough` walls,
floor points that rise and fall with everything standing pinned level, vaulted roofs), called from this map's generator
after L4 is written; `identity:` in project.yml. Metrics are `oymap metrics`' cave_shape (floor uneven share, ceiling
spread, rough wall share; the audit's numbers 0.30 / 80 / 0.18). `tools/xeen/check_identity.py <key>` checks the family
share and the shape of the installed map.

- Metrics before -> after (floor / ceiling spread / rough): 0.20 / 111 / 0.27 -> 0.35 / 98 / 0.27; family d43 0 % (dirt
  burrows; d43 only in DD-11C's hall: DECIDE).
- s29: the root tunnel out of the pit rough (`path_rough`): the arrival looked down a straight box.
- Name test (arrival, first fight room, signature room), engine captures from `assets_dev` in
  `output/studio_cal/a7/s29/names/dd11a/shots/`  (01-1_arrival.png, 02-2_midden.png, 03-3_larder.png); all eight maps on
  one sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`. Reads as a troll hole: trolls in the tunnel at once, the
  bone midden, the larder's hides. The arrival looks through a square opening down a straight tunnel; the tunnel's rough walls (s29) barely
  show from there (`output/studio_cal/a7/s29/names/dd11a_arrival_before_after.jpg`): the opening's square frame is what reads as a box.

- 2026-11-22 fixup (fourth orchestrator, for A7): `project.yml` had lost `map_code: DD-11A` and `units: {plan_grid: 512}`: s28's D-89 `identity` line in `output/studio_cal/dd11a/tools/gen.py` ended in a `#` comment that swallowed the rest of that line. Line split, L4 regenerated (only those two keys), rebuilt (BLV identical, studio file only), installed, no rebake; audit 0/0, exits 0, drops 0, tests 12/12 from assets_dev. `quests.py` keyed the map `DD11A` without it (DD-11B's player bit 11294 error); it now fails any L4 project whose key maps.yml does not know.
