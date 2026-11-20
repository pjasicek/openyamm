# Mad Necromancer's Lab (MM8 `d20.blv`) rebuilt as a Map Studio project: notes

A held-out rebuild (the studio was never tuned on this map), by [REBUILD_PROCEDURE.md](../../../REBUILD_PROCEDURE.md),
2026-11-13, from the shipped original to L4. Project id `calib_mm8_d20`, map row 9720 (`reference: d20.blv`), drawn in
the original's own frame. Scratch data, every helper, the comparison reports and the pictures are in
`output/studio_cal/mm8_d20/`: `orig/` (the original's audit, solve, flow, things, metrics, export, plan and iso
renders, one file of faces per sector), `tools/` (`outline.py`: a sector's floor outline by cancelling shared edges;
`faces.py`, `sect.py`, `rep.py` as the Fortress's; `furn.py`: the furniture faces clustered; `pairs.py`: the things
pictures side by side), `loop.sh <tag>` (fmt, validate, build, compare, audit `--strict --reach`, solve, things),
`play.sh` and `play4.sh <tag>` (install into the scratch mount and play the playtest once, or four times at once),
`root/` (a hard-link copy of assets_dev for the pictures), `run/` (the playtests' logs).

The four project files were written by `gen/gen.py` (round one only: measured numbers, outlines from `outline.py`);
from now on the files are the source and the generator is not run again. `playtest.yml` is by hand.

## Round one (2026-11-13): scores and bands

| Stage | score | shape | textures |
|---|---|---|---|
| first shell with objects (`compare_r1a`) | 99.6 % | 99.8 % | 99.2 % |
| exit halves swapped right, benches as body and top, the bed (`compare_r1b`) | 99.7 % | 99.8 % | 99.5 % |
| blade slots, fire vents (**end**, `compare_r1c`) | **99.7 %** | 99.8 % | 99.6 % |

405 points, none without a floor either way; offset agreement 0.46 (not chased: swamptyl and GNecWalB show no
pattern that a phase betrays). 32 rooms for 26 sectors with floors (the stair is seven rooms; the cistern under the
hall, a part of sector 1, is its own room).

- **Playtest**: 119 steps, four runs of four pass (`run/play_r1c_1..4.log`; also four of four on build r1b). Arrival,
  well, all four double doors, four bookshelves (map variables counted), basin, the hall button and the quarters
  button each send the lift both ways, the lift ridden up and down by clicking its top, Blazen speaks through the cell
  door ("Help me!"), the square stair, every cave room, chests c3 and c4, the fire plates (event asserted), the
  cistern, the blades plate (asserted), chest c2 gives Ebonest and c1 the Puzzle Box, back up and out of the front
  door to Shadowspire with quest bit 199 set by the leave event.
- **Events**: of the original's handlers that are bound or run (5, 6, 10, 11, 12, 13, 61-64, 82-85, 102, 103, 131,
  451-455, 501) all do the same (`oymap flow` of both, same calls and branches). Differ: 501's MoveToMap passes 0 as
  its last number where the original passes 1 (transition picture), and 451 and 501 are split over two or three
  sources (two kerb halves and the basin; two exit halves). Not built: 14-60, 65, 66, 81, 86-100 (handlers for doors
  and chests that do not exist or have no face), 1-4, 7-9, 101, 104-106 (empty).
- **Coplanar**: `oymap audit --strict`: 0 pairs, 0 new (the original has 0).
- `solve`/`audit --reach`: every room reached; the original's 25 and 26 are "never reached" only by a tool defect
  (below).

## What the player sees, per interactive thing (`things_pairs_r1/`, original left, rebuild right)

- Double doors (records 51-58): GNecWal2 leaves 128 wide that fold 124 to their jambs at 100/s, 16 and 80 thick as
  the original's; alike shut and open.
- Lift (record 1): slab 16 thick, top 32, rises 513 at 50/s; clicking its top toggles it (event 11). Alike.
- Lift buttons (records 2, 3): the original's are blocks 24 by 8 by 24 whose door record does not move; built as
  clicked platforms of that size (no motion), as the original.
- Chests: MM8 `gt002` kind, front as the original's; contents and trap flags from the scene.
- Cell door: a GNecDr4R panel 130 by 256 on the quarters' west wall, no hover name, as the original.
- Bookcases: T1books blocks with Trim9_32/Trim9_32a tops and ends.
- Well: a 12-sided kerb 64 high (two halves) round water at floor level, the cistern's roof rising into it as a drum
  under the water. Basin of the south-west room: a single 12-sided block to 80 with water on top (the original is a
  bowl on a stem): reads bigger and squarer than the original's. Worst pair: `things_pairs_r1/451-13.jpg`.
- Plates: invisible C1FL plates as the original's floor faces. Best pairs: the doors, `61-11.jpg`, `62-10.jpg`.
- Raised tops: the lift's top at 545 (party rides it; view checked in the playtest, no eye-sector finding); the stair
  landings. No platform the party is meant to stand on hangs into another room.

## Gaps, most harmful first

1. **The green floor mist** (`d20_mist.scene.yml`, two layers at 30 and -994): no project word for a scene `mist`
   block; the rebuild is visibly clearer and greyer than the original everywhere (compare any pair).
2. **An exit's transition picture**: the studio writes MoveToMap's last number as 0; the MM8 dungeons give 1
   (`core/IndoorLowering.cpp` exit writer). Same in d05.
3. **One exit face with two pictures** (GNecDr4R | GNecDr4L): two exits of 128 side by side, two events for 501.
4. **A ring-shaped block** (the well kerb): two C-shaped halves, two events for one.
5. **Furniture shapes**: the basin's bowl on a stem, the bench's sunk basin (a water slab on top instead), the bed's
   curved headboard (two raking halves) and rounded pillow, the blade slots (a solid01 panel instead of a 64-deep
   recess). None measures; all are small.
6. **A doorway's lintel of its own surface** (GNecStpT over GNecStpV jambs): `reveal` covers sides and top alike.

## Tool defects

- `oymap solve`/`audit --reach d20.blv`: the walk stops at the wall faces of sector 23 (faces 1006, 1030), a sector
  with no floor and no portal lying in the plane of the portal 22->25; the game neither draws nor collides with them
  (`run/wall23.yml`: the party walks from 22 into 25 in the original). Rooms 25 and 26 (Ebonest) wrongly reported
  unreached. `oymap compare` likewise sees them as a wall (S22 loses 0.1 %); the rebuild keeps the passage open, as
  played: where score and original pull apart, the original's play was followed.
- `oymap build`: openings between rooms that face each other across several wall pairs pick the longest pair even
  192 apart, where a pair 0 apart shares the real stretch (c9/c10, c11/c12, c13/c14, c16/c17, c16/c18, c25/c26: all
  needed `from_wall`/`to_wall`).
- `things_shots.py`: no faults seen. The tour format's pitch is radians, `run_game.sh` takes degrees.

## Unsure of in the original

- Sector 27 (a 16-thick sliver under the quarters' floor) and sector 23 (two stray faces) are left out.
- The original lights stand 8 above the floor; kept.

## Round two: the user's walk (2026-11-13)

The user walked the rebuild ("otherwise good") and found two faults. Backup of round one: `output/studio_cal/mm8_d20/r2_backup/`.

1. **The well should be fallen through** (pose -827.7, 606.7, 64, yaw 2.361, pitch -63.6°, on the kerb looking
   down). The original's water, face 7 (WtrTyl at 0), carries fluid and the untouchable flag (0x20000000): it is
   drawn and nothing stands on it, and the hall, the shaft (faces 155 to 166, Grastyl, 0 to -512) and the cistern
   are one sector, so the party drops through the water to the cistern floor at -1024. Round one built the water as
   a floor plate of the hall (solid) over the cistern's ceiling level (a second water face in the same plane, room
   under). Now: an opening `in: floor` from the hall to the cistern with the well's twelve-sided outline and Grastyl
   `reveal` (the shaft), and the water a platform of the hall 1 thick, `solid: false`, WtrTyl with `liquid: water`
   on every side. The playtest walks into the well after the west store and asserts the party at -1024 in the
   cistern (four of four).
2. **Secret trap plates**: the original has exactly three faces with the secret flag, the trap plates: 1286 (blades,
   event 102) and 1309, 1310 (fire, event 103). The three plates carry `secret: true`; `oymap metrics`
   `secret_faces` 3 in both maps, and the plates pulse red in the game as the original's.

Scores (`compare_r2c`): 99.7 %, distance 0.998, textures 0.996 (unchanged); `audit --strict`: 0 coplanar pairs, 0
new; every room reached. Playtest 123 steps, four of four (`run/play_r2c_1..4.log`). Pictures, original | round
one | round two: `look_r2/pair_*.jpg` (the user's pose, the kerb, the shaft from the cistern, the three plates).
Installed into `output/studio_play/rebuilds_root`.

Lesson: a liquid face of the original that is untouchable is a way down, not a floor; check the flags of every
water and floor face over a room below (the export's attributes), not only its texture.
