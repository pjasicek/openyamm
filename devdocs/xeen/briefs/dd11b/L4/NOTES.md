# DD-11B Troll Holes, second pocket: L4 notes

Lane A7 phase 3 (agent `xeen-a7-dd11`), 2026-11-20. Map 9163, `xeen_dd11b.blv`, class S, `world: xeen`. Built from the
MU-6 graph `devdocs/xeen/mockups/act3_graphs/dd11b.graph.yml` and `notes_d2.md` with D-25
(`mockups/act3_a7_decisions.md`), which wins: Troll Juice +2 Endurance and Poisoned once a character (Q8), the second
letter kept as a paraphrase, the burrow's top the `exit` preset with no question. Generator
`output/studio_cal/dd11b/tools/gen.py` (shared helpers `output/studio_cal/dd11/tools/lib.py`; writes L1-L4; never
hand-edit the written files). Cycle `output/studio_cal/dd11/cycle.sh dd11b`; playtests `output/studio_cal/dd11/play.sh
dd11b <name>` and `four.sh`; pictures `shots.sh dd11b`. Scratch root `output/studio_cal/dd11/root` (shared).

## What was built

x east, y north; the pit (where D2's second hole drops the party) is at the origin. The vats lie 448 down, partly under
the gallery's east end.

| Room | Floor | Size | Monsters (placed, group) | What |
| --- | --: | --- | --- | --- |
| Pit bottom | 0 | octagon 768 across, shaft to 768 | — | Start; a heap of torn packs; D2's sky at the shaft's top |
| Gnawed gallery | 0 | 320 × 2,432 | 3 Troll (10) | East to the clay drop (a 256 × 224 hole in its floor near the end) |
| Expired adventurers | 0 | 768 × 736 | — | Behind the fallen root (hinged): 4 skeletons, the thief's satchel, the strongbox (T3) |
| Fungus cave | 0 | 896 × 1,504, domed | 3 Troll (11) | Mushrooms; the root stair in its east wall, the hide flap to the burrow in its west |
| The burrow up | 0 → 384 | 224 × 1,152 | — | Root-floored ramp west to the sod hatch (the exit) |
| Vat rim | −448 | 1,024 square | 3 Troll (13) | Where the clay drop lands (under the gallery's end); a clay heap |
| Juice pit | −448 | 1,536 × 1,920, domed | 5 Troll Guard (14) | The vat (an octagonal platform 56 high, juice on top): Troll Juice |
| Brewers' den | −448 | 640 × 768, straw | 3 Troll Guard (15) | Behind the log door; their chest (T3) |
| Grub pens | −448 | 1,024 square | 3 Troll (12) | Two wicker pens (xopoles sides, straw tops) |
| Root stair | −448 → 0 | 768 × 384, 14 steps | — | West up to the fungus cave (the loop) |

**Counts and sizes** (`output/studio_cal/dd11b/metrics.json`): 10 rooms (11 sectors with sector 0), 9.6 M units², 452
faces, 20 monsters (12 Troll 11690 at 18, 8 Troll Guard 11691 at 28), 2 chests (T3, T3), 3 doors (fallen root,
log door, hide flap), 1 loop (gallery, drop, rim, pens, stair, fungus).

**Textures:** 14 distinct, 0 new: 7dirttyl, straw, xohide, xdbark, xopoles, wtrtyl (the juice, `liquid: water`),
xodaylt, the plain chest set. Cap 30.

**Monsters.** A2's Troll Holes rows, all placed, one group per room, without the hostile flag (relations decide).

**Map card.** As DD-11A: music 8, cave, treasure 3, encounter 10 (D-33), slot 1 `Xeen Warren Troll` tier 1 [2, 3] weight 100;
test row 9163 in the scratch root until A2 writes it.

## The clay drop (the only one-way link)

A hole (`in: floor`, 256 × 224) in the gallery's floor near its east end, over the vat rim 448 below (the rim's ceiling
is the gallery's floor, 64 thick). Walking on falls through; the step line on landing says "There is no climbing back up
that way." The gallery's step line warns of the wet clay ahead. Back up by the root stair.

## Troll Juice (D-25 Q8)

`evt:juice` (event 8) on `platform:vat`, hover "Troll Juice": a member without player bit 11294 (A3's
`q-d13.troll_juice`, used by number, not declared) gets A3's text hook (aaze0040:2), `AddValue(BaseEndurance, 2)`,
`SetValue(PoisonedGreen, 1)` (the weakest poison), the bit, and the status line "+2 Endurance (permanent). You are
poisoned."; a member with the bit gets `q-d13.troll_juice_again`. The playtest checks the text, PoisonWeak on the
drinker and the repeat line.

## Ways in and out (D-24, D-25)

- **In (A6's side):** D2's second hole (event 33) drops the party at the map's start, **(96, −32, 0) in room:pit,
  facing east (direction 0)**, beside the heap of packs, facing the gallery.
- **Out:** the burrow's sod hatch (`evt:hatch`, event 7, the `exit` preset, no question) to `exit:d2_return`, A6's
  point **(3072, −10240, 960) facing west (180°)**. `playtest_exit.yml` measures the landing at **(3072, −10240, 961)**.

## Hooks and lines

- `q-d13.troll_juice`, `q-d13.troll_juice_again` on the vat. Map qbits 110970-110979: **none used**; player bit 11294
  (A3's) read and set by number.
- Original lines: "Troll Juice" / "This stuff is poisonous, but the experience improves you." (aaze0040:1-2, A3's
  hook); "Expired Adventurer" / "Nothing here." (aaze0040:3-4) on the four skeletons; "Chest" (aaze0040:0).
- The second letter (D-25: ours, a paraphrase of aaze0040:6-7; A3's ORIGINAL_LINES row exists), in a window on the
  thief's satchel: "A message on thieves' guild letterhead reads: To all members: Troll holes located by the Forbidden
  Fruit hut, by the dead adventurer's pack, and the wide one near the rim. The wide one is the King's."
- Our lines: the landing, the gallery's warning, the drop's landing, the vat's step line, the fallen root's.

## Checks (scratch root `output/studio_cal/dd11/root`, merge point 12)

- `fmt --check`, `validate` (L1-L4 no issues), `build` (0 warnings), `audit --reach --solve`
  (`output/studio_cal/dd11b/audit.txt`): no error or warning; 7 of 10 sectors on foot with doors shut (the drop
  counted), 10 with them open; info: the hatch's stretched daylight.
- Playtests 4 of 4 each (`output/studio_cal/dd11b/four.out`, logs `output/studio_cal/dd11b/run/`): `playtest.yml` 60
  steps (landing, root door, skeleton, letter, strongbox, the drop and its line, the juice and its repeat, PoisonWeak,
  brewers' door and chest, pens, stair, flap, burrow, "RELOAD ok at step 58"), `playtest_hostility.yml` 35 (as
  DD-11A's), `playtest_exit.yml` 15.
- Pictures `output/studio_cal/dd11b/shots/` (`sheet1.jpg`, `sheet2.jpg`), unbaked. Fixed before: two mushroom
  decorations the world does not draw (mushrm04, 06, 07 have no model); the landing line did not fire on the clay heap
  (now a source of the step event).

## Words needed

- A step event on a room does not run on a platform in it (the landing heap): `sources` lists the platform.

## Dressing exceptions

None (audit clean). A skull in the gallery was taken out (a corridor has no room beside its walking line).

## For the user

- The clay drop: the floor gives way at the gallery's end; there is no way back but round by the root stair.
- Troll Juice: one drink a character; the second asks nothing and says you have had enough.
- The second letter names the King's hole: does it read as a clue to DD-11C?

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
- Audit no error or warning, build warnings 0. Installed, re-baked; from `assets_dev`: playtest (60), playtest_hostility (35), playtest_exit (15) 4 of 4 each
  (`output/studio_cal/a7/s7_mp15_chain.out`).

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- The hide flap's doorway 128 wide (was 192; a folding leaf takes pictures at one texel a unit, so the flap now shows one hide).
- The torn packs and the satchel heaps in `straw` (hides were cut on their small sloped faces).
- The shared `DAY_LIGHT` is now in L4 as D-34 meant ([150, 140, 122]).
- Audit: no `textures.*` finding.

## chest.front (2026-11-22, lane A7 twenty-seventh session)

The build's `chest.front` warning (merge point 41: an indoor chest's `facing` is its long axis, its front 90 degrees
anticlockwise of it): the chest(s) it named turned 180 degrees in place, back to the wall, front to the room.
Installed with the bake; build warnings and audit as before.

## D-89 cave shape, identity and name test (2026-11-22, lane A7 28th-29th sessions)

Shared pass `tools/xeen/cave_shape.py` (corners cut where no other room, object or numbered wall is near, `rough` walls,
floor points that rise and fall with everything standing pinned level, vaulted roofs), called from this map's generator
after L4 is written; `identity:` in project.yml. Metrics are `oymap metrics`' cave_shape (floor uneven share, ceiling
spread, rough wall share; the audit's numbers 0.30 / 80 / 0.18). `tools/xeen/check_identity.py <key>` checks the family
share and the shape of the installed map.

- Metrics before -> after (floor / ceiling spread / rough): 0.12 / 162 / 0.37 -> 0.37 / 87 / 0.39; family d43 0 % (dirt
  burrows: DECIDE).
- s29: the gnawed gallery out of the pit stays as built: its floor hole (open:clay_drop) must stay clear of its walls,
  so the pass leaves a tunnel with a hole level and plain (`cave_shape.py`).
- Name test (arrival, first fight room, signature room), engine captures from `assets_dev` in
  `output/studio_cal/a7/s29/names/dd11b/shots/`  (01-1_arrival.png, 02-2_fungus.png, 03-3_vat_cave.png); all eight maps
  on one sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`. Reads as named: fungus cave with its mushrooms, the
  juice pit's vat; the arrival tunnel is a plain box as DD-11A's was (kept: the hole).

- 2026-11-22 fixup (fourth orchestrator, for A7): `project.yml` had lost `map_code: DD-11B` and `units: {plan_grid: 512}`: s28's D-89 `identity` line in `output/studio_cal/dd11b/tools/gen.py` ended in a `#` comment that swallowed the rest of that line. Line split, L4 regenerated (only those two keys), rebuilt (BLV identical, studio file only), installed, no rebake; audit 0/0, exits 0, drops 0, tests 12/12 from assets_dev. `quests.py` keyed the map `DD11B` without it (DD-11B's player bit 11294 error); it now fails any L4 project whose key maps.yml does not know.
