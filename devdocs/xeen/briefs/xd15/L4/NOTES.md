# XD-15 The Sphinx: L4 notes

Lane A7 phase 4 (agent `agent:xeen-a7-xd15`), 2026-11-20. Map 9141, `xeen_xd15.blv`, class M, `world: xeen`, on X6
Desert of the Sphinx (the Northern Sphinx), Act IV, party 31-34. Built from the MU-6 graph
`devdocs/xeen/mockups/act4_graphs/xd15.graph.yml` with decider D-39 (`mockups/act4_a7_decisions.md`), which wins where
they differ, and A3's `source/quests/q-c9.yml`.

Generator: `output/studio_cal/xd15/tools/gen.py` writes L1-L4. Never hand-edit the written files. The playtests are
written by `tools/gen_tests.py` from the built `ids.lock.yml`. The cycle (generate, fmt, validate, build, install into
the scratch root, audit) is `output/studio_cal/xd15/cycle.sh`; the pictures are `shots.sh` with `shots.yml`. The scratch
root is `output/studio_cal/xd15/root`; its `map_stats.txt` and `bolster_maps.txt` carry a test row 9141 (copied from
9124, renamed) until A2 writes the real one.

## What was built

- **The body (z 0).** The breast gate (the arrival, quiet; the two leaves out to X6 in its south wall). The hall of the
  paws: four striped columns and two braziers, a 'Stairs up.' tablet by the throat stair's mouth. The two sarcophagus
  galleries on the flanks. In the west gallery the great sarcophagus is a chest that needs Might 40 (D-39 Q4); in the
  east gallery the last sarcophagus holds gems. The belly hall has six striped columns, the stripes as a frieze, and
  four braziers. It has two carved throne doors (D-39): the crown door (a pair, `egydrsml`/`egydrsmr`, Horus in the
  double crown) to the King's throne, and the veil door (`egydrsmc`) to the Queen's throne. In the Queen's room the
  loose panel with the carved jackal mask (`egywlspa`) is a secret door to the Thieves' throne. The haunch vault holds
  grave goods in niches, the vault chest (two Might Boosts on its first opening) and the dungeon stair.
- **The head (z 1280)**, up the throat stair (40 steps of 32): the neck landing and two lappets. The west lappet holds a
  priest's chest; the east lappet an offering niche with gems. The riddle chamber lies behind the face:
  - two eyes in its south wall, with two bright lights in front of them;
  - two hieroglyph plaques;
  - the sun disc (a scarab on its face) over a 192-deep shaft;
  - two Iron Golems on guard.

  West of it, through the legend door (`egydrlgl`/`egydrlgr`, a pair), is the throne of legends with two lecterns: the
  Book of the Heavens (Starburst, Air) and the Book of the Sun (Divine Intervention, Light).
- **The hieroglyph dungeon (z -640)**, down the dungeon stair (20 steps): the stair foot; the west and east hieroglyph
  halls; the scribes' library, with shelves of tablets, the lectern, a chest, the fifth clue and the whole riddle on the
  end wall; and the drop cell, with a sand heap, the first clue and a slab that opens from inside and stays open.
- **Counts.** 21 rooms (21 sectors), 37.9 M units² of floor. 7 doors (two of them pairs) and the disc mover. 4 chests
  at treasure 4, 4 loops (flanks, head, glyphs, the drop's way). 45 monsters, all placed and hostile in groups 10-22 by
  room: 16 Sand Golems 11590 (22), 18 Stone Golems 11581 (26), 4 Iron Golems 11582 (40) and 7 Tomb Mummies 11270 (42).
  Kill XP is 12.85k per member, as the graph has it. Music 46.
- **Textures:** MM6's Tomb of VARN (pyramid.blv) upper set throughout; 43 distinct of the 45 cap, 0 new.

## The riddle and the drop (D-39 Q5)

- Entering the riddle chamber the first time calls A3's `q-c9.riddle` (a step event on the room, once).
- Stepping on the disc asks "What is my name?" on every step until the Sphinx is named.
- **GOLUX** (any case):
  - `xeen_sphinx_stir` and a shake;
  - A3's `q-c9.name_right` (done 112181, award 419, 6,000);
  - the crown, veil and legend doors open.

  On every later load the doors are opened again by `q-c9.done`. Once named, the disc answers with the hook's else
  text ("Golux. Yes. Still me.").
- **Anything else** (D-39 Q5's order since the tenth session, merge point 18):
  - `xeen_sphinx_stir`;
  - 30 damage to every member (about 10 % of a level-31 knight's HP, 15-20 % of a sorcerer's);
  - map var `drop` 1; within a second a timer sets the party on the disc's middle (the question comes as soon as the
    party's edge is on the disc, so the disc would otherwise drop out from under it) and the disc sinks 176 into its
    shaft with the party on it (`evt:drop_sink`);
  - one tick later on the sunk disc (`evt:drop_ride`), then the party falls to the drop cell's sand heap
    (`evt:drop_move`, an in-map move from a timer, which merge point 18 applies; the game's teleport sound plays);
  - landing on the heap shows A3's `q-c9.name_wrong` (step event on `platform:sand_heap`), `drop` back to 0; the disc
    rises again by itself 3 s after it sank (`auto_return_seconds`).

  The disc asks only while `drop` is 0 (the ride must not ask again); its else branch calls `q-c9.name_right` only once
  named (`IsQBitSet(QBit(112181))`), since one object runs one event. `playtest_drop.yml` asserts the party on the
  disc's middle at z 1,112 (sunk) before the fall, then the landing's words and the heap (`advance_runtime` with
  `follow_map_move: true`, A1's answer: without it a move stays pending in a scenario). The earlier deviations (the
  move in the disc's own event, nobody seeing it sink) are gone.
- The damage is not checked numerically in the playtests: they run immortal, and `play_lua` has no HP reader.

## Visible sink (2026-11-20, tenth session, lane A7)

`gen.py` and `gen_tests.py` changed (the generator was checked first: it rewrote L4 unchanged). Build 0 warnings, audit
the one kept `question.answer` warning. Installed with its bake; from `assets_dev`: `playtest.yml` (94),
`playtest_drop.yml` (111), `playtest_exit.yml` (14), `playtest_hostility.yml` (26) 4 of 4 each
(`output/studio_cal/a7/s10_disc_xd15.out`). `xeen_sphinx_stir` plays on both answers (built in the ninth session).

## Measurements

- **Arrival** `entrance:x6_paws`: (0, 256, 0) facing north, in the breast gate about 256 inside the leaves. It is the
  map's start too.
- **Way out:** `exit:x6_paws` (both leaves, the exit preset) to X6 (9216, 9728, 1408), facing south (270°). Measured
  landing (`playtest_exit.yml`): **(9216, 9728, 1409)** after 2 s.

## Checks (2026-11-20, from `output/studio_cal/xd15/root`)

- `oymap validate` reports no issues on L1-L4, `fmt --check` is clean, and the build has 0 warnings.
- `oymap audit --reach --solve` (`output/studio_cal/xd15/audit.txt`): 0 errors. There are 0 `lights.*`, 0 `doors.*` and
  0 `textures.*` findings, and no dressing finding. One warning, `question.answer`, is kept (below).
- Playtests, 4 of 4 each (`output/studio_cal/xd15/four_final.out`, logs in `output/studio_cal/xd15/a7_xrun/`):
  - `playtest.yml`: the critical path, GOLUX, the four thrones and the books, a reload;
  - `playtest_drop.yml`: a wrong name, the drop, the five clues and the summary, the gem finds, the climb back by the
    dungeon stair, the vault's Might Boosts, Might 15 refused and 12 + a boost opening the great sarcophagus, a reload;
  - `playtest_exit.yml`;
  - `playtest_hostility.yml`.
- Pictures: `output/studio_cal/xd15/sheet1.jpg` to `sheet4.jpg` (unbaked, so the rooms are evenly bright).

## Audit exceptions

- `question.answer` (event 13, the disc): the audit cannot see that GOLUX is given. The map gives it letter by letter
  on the five clue walls, and A3's `q-c9.hieroglyphs` gives the whole riddle on the library's end wall. Arie, the Basenji
  peasant and Alexander say it plainly.

## Texture fit exceptions

None.

## Dressing exceptions

None. The braziers stand between the columns, off the walking lines; the vases and urns stand in corners.

- F14 (A7 s27): `check_drops.py` lists the sun disc's shaft (the riddle chamber, 192 deep, floor 1,088) as a pocket:
  the disc is a mover lying over it (the check leaves movers out) and the wrong name drops the party through it by
  design, onto the drop cell's sand heap, which leads on. Kept.

## Words needed

- None open. (The delayed in-map move landed in merge point 18; the wrong name now sinks with the party, above.)

## What the user should look at

- The riddle chamber: the two bars of light from the eyes, and the disc on a wrong answer (it sinks with you, then
  the drop and the landing line).
- The crown door's two Horus leaves, and the veil door's single carved leaf.
- The mask panel in the Queen's room: it pulses as a secret door.
- The legend door's pair of framed scenes: 256 by 256 pictures on two 256 by 256 leaves, a doorway only 256 high, as
  MM6's pyramid lays them.
- The map is unbaked; the lane lead bakes it.

## Hum centred (2026-11-21, fifteenth session, lane A7 sub-agent)

- D-48 (AUDIO.md "Indoor beds"): `sound:dungeon_hum_lib` and `sound:dungeon_hum_w`, the dungeon's bed, take `pan:
  false` (`tools/gen.py`); the braziers and `sound:eyes_wind` keep panning.
- `xcycle.sh`: build warnings 0, audit 0 errors, 1 warning (the `question.answer` above). Installed with bake
  (01:58:20), stale bakes 0. From `assets_dev`, 4 of 4 each: `playtest` 94, `playtest_drop` 111, `playtest_hostility`
  26, `playtest_exit` 14 (`output/studio_cal/a7/s15_xd15_four.out`).
