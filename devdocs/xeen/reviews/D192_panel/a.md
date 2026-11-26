# D-192, panelist A (round 1): X6 p14, worms stuck at the Sphinx cove

Read-only. One probe run: the repro `output/xeen_fb/p5_engine2/r5/x6_cove_worms_pursue.yml` (copied to
`output/xeen_fb/d192_a/`) on `build-xeen/game/openyamm` (16:34) with the installed X6 (11:03), the outdoor
pathfinding log on. Log: `output/xeen_fb/d192_a/run1.log`, traced with `output/xeen_fb/p5_engine2/r5/trace.py`.

## What the run shows (it changes the picture in the brief)

- **Two of the three Great Worms are still stuck, at two different seams.** Actor 149 (the first spawn) holds at
  (-15858, -10196), cell (33.0, 83.9), the cove's east corner, where `hull_093` (north run) ends and `hull_094` (east
  run, `xeen_hullf`, **not sunk**: no `raise` in the sketch) begins. Actor 150 (the second spawn) still holds at
  (-16428, -10176), its front 4 short of the `hull_092`/`hull_093` seam (x -16384), within 2 units of where it held
  before `hull_sink`. Actor 151 reaches the party (310 off). The Sand Worm (11440) never logs a move: its assert has
  never been reached, so nobody knows whether it passes. The round summary's "the first worm now passes the seam" is
  true of one worm only.
- **Why `hull_sink` did not free the seam.** The sketch has `hull_092` and `hull_093` both at `raise: -16`: each sank
  to the lowest land under its own strip, so the 32 between their tops (1488/1520 then, 1472/1504 now) is still there.
  The land west of the seam, where the worm stands, is 1500-1501, so `hull_093`'s top is still a 3-4 rise from the
  worm's feet, and its sampler stops at 0.95 of the half span and ignores a sink of 2 or less (`sink < -2`), which is
  why `hull_094` stayed up.
- **The stall is a refused step, not a wall slide.** Every stalled frame: `wanted=1`, resolved `velocity=(0,0,0)`,
  `final == start`, `contacts=0`, support terrain, the waypoint 4 higher on the next piece's top. In
  `OutdoorMovementController::resolveOutdoorActorMove` only two branches end a ground walker's move with zero velocity
  and no actor contact: the floor branch's `actorFloorRiseHasClearance` refusal (`floorRise` > 0 and < 128, no
  clearance: velocity zeroed, break), or a floor hit outside (0, 128) repeated until the 0.89 decay drops it under 20.
  A wall contact (the end cap) would slide and turn the walker instead.
- **The "fin" has a tread.** `assets_source/worlds/xeen/models/xeen_deco_hullf.glb` at its end, in world units (out,
  up): a top 48 deep at 0 (out -64 to -16), the plain face down from -16 to -2400, and a steep back face from (-64, 0)
  to (-150, -1200) to (-300, -2700), buried in the land. So the piece offers a real 48-deep floor; what the walker
  refuses is the step onto it. `actorFloorRiseHasClearance` skips a face below the stepped feet only when it is
  vertical (`normal.z` ~ 0, "the ordinary horizontal sweep handles risers"); the hull's back face is steep but not
  vertical (normal.z ~ 0.07), so it goes through the sloped-face branch, whose interval ends at the face's top, the
  tread's own height, above the walker's feet, and it can count as an overhead blocker. This is my reading of the
  code, not yet proven by a test (see the engine half); it fits the zero-velocity, no-contact signature.
- **Scope.** Kerbless pieces exist on X6 (11, 6 sunk), X7 (11, the lava falls) and D6 (8 `xeen_hullfbn`, 4 over
  water). Kerbed pieces (`xeen_hull1/4/c/n`) have a 150 kerb the planner treats as a wall (step 128), so their seams
  do not stall walkers, and they must never sink (the round's `x4_hull_edge` incident).

## DECISION

**Both, data first. The data closes the pin; the engine fix comes after it, test-first, and is about the general
walker, not the hull.**

1. **Data, now (A5, `level_generation/projects/xeen/common/rim.py`, kerbless pieces only).** `hull_sink` puts a
   `SINKING` piece's top at least `HULL_SINK_CLEAR = 8` below the land everywhere a walker can stand on or beside it:
   samples every 32 along the span **and 64 past each end** (so the neighbour's side of each seam counts), across the
   band from 0.04 to 0.25 cells inland (the 48-deep top and a 40-radius body beside it), void cells left out;
   `raise = floor(min(land) - 8 - mid)`, clamped at -`HULL_SINK_MAX` (128); the `sink < -2` dead zone goes (any
   sink applies). Kerbed kinds unchanged and never sunk (`SINKING` as it is). No levelling of run tops is needed once
   every kerbless top lies under the land. Rebuild and install X6, X7 and D6 (the three maps with kerbless pieces).
2. **Gate (A5, `tools/xeen/check_wild.py`).** A new error `rim.fin`: a kerbless hull piece whose top stands above the
   installed land anywhere in that band and span (+64 each end). Expected 0 on X6, X7, D6 after the rebuild. Where the
   128 clamp cannot get under the land (only very steep land on a short piece), the error stands and that piece's
   fall gap gets a short piece or the generator moves it; no kept-line for it.
3. **The test that closes the pin.** When the repro passes from X6's stage: it moves to
   `tests/scenarios/xeen/x6_cove_worms_pursue.yml` (header: cause and fix, D-192), joins `tools/xeen/regressions.sh`'s
   scenario list after `x6_warzone_entrance.yml`, and joins X6's stage extras (the outdoor lane's per-map extra
   scenarios, `EXX` for x6). Before it moves, check the Sand Worm's assert: if a Normal-AI Sand Worm does not pursue
   from that range at all (no move logged in this run), drop it from the scenario rather than loosen the 700, and say
   so in the header. Three Great Worms must end within 700 of the party after 16 turns. `x1_hull_edge`,
   `x4_hull_edge`, `x7_edges`, `d1_hull_edge` must still pass on the rebuilt maps.
4. **Engine, next A1 merge point, test-first (A1, `game/outdoor/OutdoorMovementController.cpp`).** First a doctest on
   generic geometry, no hull: a ground actor (radius 40, height 146, step 128) walking over terrain toward a walkable
   BModel tread 48 deep whose top stands 4, 16 and 32 over its feet, the tread's back and end faces steep (about 85°)
   and running down below the terrain. If the actor stops there today, the fix is in `actorFloorRiseHasClearance`: a
   blocking face whose whole extent lies at or below the stepped feet (`maxZ <= targetFootZ + CollisionEpsilon`)
   is not an obstruction, whatever its slope, the same as the vertical-riser rule beside it. Re-run the doctest and
   the repro **on the unsunk X6** (a scratch copy of today's installed map) to prove the walker alone now gets
   through. If the doctest does not reproduce the stall, no engine change: the data half stands alone and A1 reports
   the branch it found.
   **Rejected as worded: "step over a tread-less fin lower than its step height".** Letting a walker climb any face
   under 128 with no floor on top would let monsters on MM6-MM8 outdoor maps climb onto or over low walls, parapets
   and kerbs, a broad behaviour change that would hide bad data. The hull's fin has a tread anyway.
   MM6-MM8: the narrow rule only lets actors take steps the planner already plans (`OutdoorGroundPathStepHeight`
   128) onto real floors; A1 names it at the merge point and runs the unit tests, `tools/xeen/regressions.sh` (its
   MM6-MM9 roundtrips) and the outdoor actor scenarios under `tests/scenarios/mm6|mm7|mm8` that pursue or path.

## WHY

- The pin is a data fault first: kerbless rim pieces stand a few units above land that falls along the run, and
  the round's sink, done per piece, kept the step between neighbours. Putting every kerbless top under the land
  removes all hull faces from the walker's way, including the corner seam the brief did not know about, costs
  nothing at runtime, touches only Xeen (D-109/D-114 kit, R5's map half extended) and is cheap to undo.
- AGENTS.md: fix the authoritative data, and keep engine fixes general and shared. The engine change is worth having
  only as a general walker fix (a step the planner plans that the walker refuses is a permanent stall on any map), so
  it must be shown on generic geometry, not tuned to the hull.
- Engine first was rejected: it needs a build and an MM6-MM8 rerun, and it would leave the invisible fins in place
  (a party in turn-based mode or a future kit change would meet them again). Data only was rejected because the
  walker/planner disagreement would stay hidden until the next map hits it. Levelling each run's tops was rejected
  as unnecessary once every top is under the land; it would also raise some pieces over falling land.
- Precedents: D-109/D-114 (the rim kit, kerbless plain faces behind falls), F60 (each short piece on its own land),
  R5's `hull_sink` and its rule that kerbed pieces never sink (the `x4_hull_edge` incident), D-185 (a check becomes
  the gate), AGENT_GUIDE §6 (only A1 builds; lanes send specs).

## WHO ACTS

- **A5** (with A6 for D6): `rim.py` `hull_sink` change and `check_wild.py` `rim.fin`; rebuild, stage-check, bake and
  install X6, X7, D6; run the repro from X6's stage; then move the scenario in and add the regressions line. About
  half a day (three map cycles).
- **A1**, next merge point: the doctest, then the `actorFloorRiseHasClearance` change only if the doctest shows the
  stall; MM6-MM9 checks as above. About half a day.

## REVERSIBLE

Yes. Data: one constant and one sampling change in `rim.py`, three rebuilds. Engine: one condition behind a doctest.
Confidence 75 % (the cause of the stall is read from the code and the log, not yet shown by a test).

## SUMMARY ROW

`| D-192 | 2026-11-26 | X6 p14: worms stuck at the Sphinx cove (decider panel) | Data first: rim.py hull_sink puts every kerbless piece's top at least 8 under the land over its span plus 64 past each end (no -2 dead zone; kerbed never sink); new check_wild rim.fin error; rebuild X6, X7, D6; the repro joins tests/scenarios/xeen/ and regressions.sh when it passes. Then A1, test-first: a ground actor refused a step onto a real floor because a steep face lies wholly below the stepped feet (actorFloorRiseHasClearance) gets it; no general "step over any fin". 75 % | A5 (+A6 D6), then A1 |`

## Round 2

Read b.md and c.md. All three runs agree on the facts: worms 149 and 150 hold at the `hull_093`/`hull_094` corner and
the `hull_092`/`hull_093` seam, velocity zeroed with no contact, the refusal in the clearance check, and the Sand Worm
never acting.

1. **Data first or engine only: keep data first (with B).** It is Xeen-only, works on the released binary, closes the
   pin with one X6 rebuild, and lives in the generator, so later rebuilds do not need it redone. C's trench worry does
   not hold up: the land already overhangs the plain face by about 26, and kerbless pieces are already sunk 16 to 128
   (X6, X7) with nothing visible. The engine fix still follows at the next merge point; the pin does not wait for it.
2. **The engine fix: merge onto B's rule and drop my "only if a doctest shows it".** B traced the refusal to the
   settle path on rising land (a flat-bottomed cylinder in the lift check, a sphere in the sweep), and this covers my
   steep back face and C's vertical cap alike. In `actorFloorRiseHasClearance` (actors only), a face counts only where
   it enters the low sphere's rounded bottom (`position.z + 1 + r - sqrt(r² - d²)`, d < r); above that band the test
   stays as it is. Reason: it matches the body the sweep already moves, so it needs no magic constant like C's 32. The
   doctest is still written first and uses B's geometry (approached uphill and on level ground, both must end on the
   tread). C's cases are added: a fin 3, 16 or 32 over the land passes; one 64 over, a 150 kerb and the back of a low
   wall still stop the actor. The four existing clearance doctests must pass unchanged. No general step over a wall
   fin (all three agree).
3. **The check: concede to B (`rim.py hull_tops()` plus `tools/xeen/check_hull_tops.py`, in `regressions.sh`'s map
   gates).** The generator and the gate share one measure and the check becomes a gate. My `check_wild.py rim.fin`
   would not be a regressions gate. The rule is: a non-wet kerbless top above the land along its strip or 0.25 cell
   past either end is an error; a piece already at -128 is a warning.
4. **The Sand Worm: merge.** Drop it from this scenario and put in a fourth Great Worm grounded north of the cove
   (C's (-16896, -9216), z at the land) so the scenario still has three worms coming from the north side. Reason: the
   closing test must test this pin only. The Sand Worm hanging idle at z 2200 goes to A1 as its own item, not hidden by
   a loosened assert. The scenario keeps 700 after 16 turns, goes to `tests/scenarios/xeen/`, `regressions.sh` and
   X6's stage extras.
5. **Maps: concede to B's measurement.** X6 now, then X7 at once (9 of its 11 kerbless tops stand over the land past
   their ends, up to 52). D6 only at its next rebuild (no top changes outside its wet pieces). Kerbed pieces never
   sink. X6 p14 is resolved when the rebuilt X6 passes the scenario on the released binary.

Merged summary row:
`| D-192 | 2026-11-26 | X6 p14: worms stuck at the Sphinx cove (decider panel) | Both, data first. A5: rim.py hull_sink samples the strip plus 0.25 cell past each end and sinks kerbless pieces to that land − 8 (max 128; kerbed never; wet +24 kept); rim.py hull_tops + tools/xeen/check_hull_tops.py gate in regressions.sh; X6 now, X7 next, D6 at its next rebuild. A1, next merge point, doctest first: actorFloorRiseHasClearance counts a face only where it enters the low sphere's rounded bottom (actors only; uphill = level; fins 3–32 pass, 64, a 150 kerb and a low wall's back still stop); no wall-fin step-over. x6_cove_worms_pursue.yml with a grounded fourth Great Worm for the idle Sand Worm (its own A1 item) moves to tests/scenarios/xeen/, regressions.sh and X6's extras; p14 resolved when the rebuilt X6 passes. 75 % | A5 (X6, X7), A6 (D6), A1 |`
