# D-192, panel B (round 1): X6 p14, worms stuck at the Sphinx cove

Evidence of my own (read-only): one probe run on the released `build-xeen/game/openyamm` against the installed X6
(11:03), scratch `output/xeen_fb/d192_b/` (`x6_cove_probe.yml` = the repro's spawns with report-only asserts after 6,
12, 18 and 30 turns; `probe1.log` with `logging.outdoor_pathfinding`), the installed map's collision faces
(`faces_near.py` over outdoor2's export of the installed X6), and `sink_ext.py` (kerbless hull tops against the land
past their ends, X6/X7/D6).

## What holds the worms now

After 30 turns two of the three Great Worms still stand still (the third, from the south-east, reached the party):

| Worm | Stands at | Its feet | The face in front | Last step / refused step |
| --- | --- | --- | --- | --- |
| 151 | (-16427.9, -10176), the `hull_092`/`hull_093` seam, cell (31.9, 83.9) | 1501.25, terrain rising 0.49 a step | `hull_093`'s top strip and west cap, top **1504** (sunk 1520 → 1504 by outdoor2) | 43.9 from the strip → 36.1 refused |
| 150 | (-15858.2, -10196.5), the cove's east corner, cell (33.0, 83.9) | 1533.28, terrain rising 0.32 a step | `hull_094`'s strip and north cap, top **1536** (`raise` 0) | 45.6 from its corner → 38.9 refused |

Both refusals return velocity (0, 0, 0) and happen exactly when the body's 2D radius (40, `OeNonFlyingActorRadius`; the
worm's sphere would touch these edges only at ~12) would reach a face whose top stands **2.7 units** over the
land. Cause, in `OutdoorMovementController::resolveOutdoorActorMove`: walking uphill, the terrain under the new position
is above the feet, so `settleActorToGround` runs `actorFloorRiseHasClearance`, which treats the body as a flat-bottomed
cylinder: any face within the radius whose top is above the target foot (a tread 2.7 up, or a riser's top edge) counts
as an obstruction, the move is undone and the velocity zeroed. On level or falling ground the check does not run, the
sphere sweep reaches the edge and the step branch (`PolygonFloor`, rise < 128) puts the body on the tread. The planner
(`OutdoorPathfindingBuilder`) routes along y -10176, 64 from the void's edge, over the kerbless strips, and does not
re-plan because its route is valid; the AI keeps pushing into the same refusal. So it is no longer a fin of 16–32 but an
uphill-only stall at any face a few units over the land, and the data fix of the round left exactly that: `hull_sink`
looks only under each piece's own strip, while the walker comes from the lower land beyond its end.

Also found: the repro's Sand Worm (11440) never moves (no move record in the whole run, 5,700 from the party): its
fourth assert can never pass, whatever the geometry. `targeting_party=false` in the reports flips between asserts and
is not the cause.

## DECISION

Both, data first, then engine; the requested engine step over a tread-less **wall** fin is not done.

1. **A5, now (closes the pin): no kerbless hull top over the land a walker reaches.** `common/rim.py hull_sink` samples
   the land along the strip **and 0.25 cell past each end cap** (along the run, inland 0.04–0.64 cells, void cells left
   out) and sinks the piece to that lowest land **minus `HULL_SINK_MARGIN = 8`**, at most `HULL_SINK_MAX` 128, as now
   only for `SINKING` (`xeen_hullf`, `xeen_hullfbn`) and only in the non-wet branch (F72's +24 pieces over water stay).
   Kerbed pieces (`hull4/1`, `4n/1n`, corners) never sink (the round's `x4_hull_edge` incident stands). Measured on the
   installed land: X6 `hull_093` -16 → about -28, `hull_094` 0 → about -12, `hull_086`/`088`/`089`/`092` likewise (6 of
   11 tops stand 7–8 over the land past their ends); X7 9 of 11 (up to 52); D6 none outside the wet ones. A check keeps it:
   `rim.py` gets `hull_tops(sketch, terrain)` and a `tools/xeen/check_hull_tops.py` (all outdoor maps) fails when a
   non-wet kerbless piece's top stands over that land, a warning where the piece is already at -128 (X7's lava-cove
   cliffs, `hull_067`, `hull_077`); it joins `regressions.sh`'s map gates. Rebuild X6 now (lock, gate, bake, install),
   X7 at once after; D6 at its next rebuild (no top changes there).
2. **A1, next merge point: the actor's lift check uses the sweep's body.** In `actorFloorRiseHasClearance` (actors only;
   the party's `resolveMoveForBody` is untouched) a face counts only where it enters the lower sphere's rounded bottom:
   with d its 2D distance from the body's centre to the face (0 inside), it obstructs when its height there exceeds
   `position.z + 1 + r - sqrt(r² - d²)` (d < r) and is below the standing top as now; above the sphere's band the
   cylinder test is unchanged. Doctest "outdoor actor walking uphill reaches a tread a few units over the terrain as on
   level ground": terrain rising 1 in 16, a tread with a riser under its edge (the `hull_093` shape: strip 48 deep, cap to
   its top) 3 over the land; uphill and level approaches both end on or past the tread within the same ticks (if the
   sweep then hits the cap's top edge before the tread's, the shared edge is taken as the tread's step, a riser under a
   tread being a step). The four existing clearance doctests ("entire lift", "sloped and off-center", "honors body step
   height", "cannot step through an overhead face") must pass unchanged; I checked their geometry against the formula
   (each obstruction lies far above the sphere's bottom at its d). Run `tools/xeen/regressions.sh`, `x1_hull_edge`,
   `x4_hull_edge`, `d1_hull_edge`, `x7_edges` and name the MM6–MM8 change in the merge note ("outdoor actors walking
   uphill now reach low treads they stalled at before, as they already did on level ground").
3. **Not done: stepping over a tread-less wall fin lower than 128.** In MM6–MM8 only floors are steps; walls block at any
   height. A general fin step would let monsters cross bridge railings, well rims, parapets and low town walls on every
   world. The data rule (no kerbless top over the land) leaves Xeen no tread-less fin to step.
4. **The test that closes the pin.** `output/xeen_fb/p5_engine2/r5/x6_cove_worms_pursue.yml` moves to
   `tests/scenarios/xeen/x6_cove_worms_pursue.yml` **without the Sand Worm** (asserts `last-2`, `last-1`, `last`: the three
   Great Worms within 700 of the party after 16 turns, as written), its header naming D-192 and both stall points;
   it joins `tools/xeen/regressions.sh`'s list (it guards an engine behaviour every merge point can change) and X6's NOTES
   as a map extra for every X6 rebuild. A5 resolves X6 p14 when the rebuilt X6 passes it on the released binary, with an
   after picture from the corner. If it still fails after step 1, A5 records the new stall from a pathfinding trace and
   the pin waits for step 2; no other hull data change.

## WHY

- The trace shows one mechanism at both spots: refusal at radius + one step from a face 2.7 over the land, only uphill.
  That is an engine asymmetry (cylinder bottom in the lift check, sphere bottom in the sweep) and a data gap (tops
  sampled only under their own strip). Fixing either clears X6; fixing only the data would leave the same stall at every
  other low outdoor tread on rising land (Xeen's D-170 bridge pads, level pads, plinths; MM6–MM8 bridge ends and
  platforms), fixing only the engine would leave Xeen's hull tops over the land, so do both.
- Data first: it is Xeen-only, runs on the released binary, closes the player's pin in one X6 rebuild and touches only
  the kerbless pieces (the kind outdoor2 already sinks), never the kerbs that keep the party out of the void. The engine
  change carries MM6–MM8 risk and needs a merge point, a doctest and the regression set, so it follows, and the moved
  scenario then guards both.
- The engine change is narrow and rests on a rule the code already has: the sweep decides what a body touches; the lift
  check should not be stricter at the rim than the body the sweep moves. It does not touch the party, the planner, the
  void restriction or the step height, so the hull-edge scenarios' party behaviour is unchanged.
- Rejected: (a) the fin step-over (MM rule and MM6–MM8 railings, above); (b) sinking kerbed pieces (the round's
  incident: a party stepped over a sunk kerb into the void); (c) a planner keep-out over the hull strips (the walk along
  the rim is a fine route, and it would hide the engine fault); (d) a small fixed "lip" tolerance in the clearance check
  (8 units would clear 2.7 but not the next 12; the sphere profile is the real shape); (e) keeping the Sand Worm in the
  test (it never acts: the test could never pass).
- Margin 8 rather than 0: the studio's rendered terrain and `wild._terrain_at` differ by a few units, and the residual
  2.7 is what defeated the first sink; 8 under the land does not show behind a sand-fall.

## WHO ACTS

- A5: `rim.py` + `check_hull_tops.py` (small), X6 rebuild/bake/install + after picture (about an hour), X7 rebuild;
  A6: D6 at its next rebuild.
- A1: the clearance change + doctest + the scenario's move into `tests/scenarios/xeen/` and `regressions.sh` (small;
  one merge point).
- Orchestrator: DECISIONS row; X6 p14 stays open until A5's pass.

## REVERSIBLE

Yes (a generator constant and one engine function). Confidence 75 % (the mechanism is measured; that the cove then
lets every worm through is the scenario's to show).

## SUMMARY ROW

`| D-192 | 2026-11-26 | X6 p14: worms still stuck at the Sphinx cove (panel B) | Both, data first. A5: rim.py hull_sink also samples 0.25 cell past each end and sinks kerbless pieces to that land − 8 (kerbed never), check_hull_tops.py in regressions.sh, X6 then X7 rebuilt. A1: actorFloorRiseHasClearance uses the sweep's rounded body bottom (an uphill walker stalled at its radius from a tread 2.7 over the land), doctest uphill = level; no wall-fin step-over. x6_cove_worms_pursue.yml (Sand Worm dropped: it never acts) moves to tests/scenarios/xeen/ and regressions.sh; p14 resolved when the rebuilt X6 passes it. 75 % | A5 (rim, X6, X7), A6 (D6), A1 |`

## Round 2

Read a.md and c.md. All three runs agree on the facts: two Great Worms frozen at the same two spots, velocity
(0, 0, 0) with no contact (the settle path's refusal), and a Sand Worm that never acts.

1. **Data first vs engine only: keep data first (with A).** It closes p14 on the released binary with a Xeen-only
   generator change and no MM6–MM8 risk. A kerbless top standing over the land is a kit fault the party meets too
   (an invisible lip). C's "trench" does not arise: the top lies under the land's own surface behind the edge, so at
   most an 8-unit sliver of the land's cut shows from the void side, behind a sand-fall.
2. **The engine fix: merge. A's test-first gate, with B's rounded bottom as the rule, and A's "wholly at or below the
   stepped feet" clause folded in.** The doctest must first show the uphill stall (terrain rising, a walkable tread 3,
   16 and 32 over the feet with a vertical cap and a steep back face down into the land). Then
   `actorFloorRiseHasClearance` counts a face only where it reaches above `position.z + 1 + r − sqrt(r² − d²)` (d is
   the 2D distance from the body's centre to the face). It also skips any face whose whole extent lies at or below the
   stepped feet, whatever its slope. Reason: the stall has two blockers, and neither other rule clears both.
   - The tread itself (faces 0/1 of `hull_093`, horizontal, 1504 over the target foot of 1502.25) fails the
     horizontal branch. C's vertical-only allowance and A's below-the-feet clause both leave that branch as it is.
   - A flat ≤ 32 allowance on every face would break the existing doctest "sloped and off-center" (its slab is 15
     over the target foot at d = 8 and must block).
   - The rounded bottom blocks exactly where the sweep's sphere would touch. So C's one-sided parapets approached
     from behind still stop the body (a 30-high back is refused at d ≈ 38.5 instead of 40), and every existing
     doctest keeps its result.
   - If the sweep reaches the cap's top edge before the tread's, the shared edge counts as the tread's step.
3. **The check: concede to A (`tools/xeen/check_wild.py`, error `rim.fin`).** `check_wild.py` is already a map gate
   that the outdoor lanes run, so no new tool is needed. A's band (span + 64 past each end, 0.04–0.25 cells inland,
   no kept lines) replaces my `check_hull_tops.py`.
4. **The Sand Worm: merge with C.** First spawn it at its land height (~1,440, not 2,200). If it still never acts,
   replace it with a fourth Great Worm at a grounded spot north of the cove, (-16896, -9216). Its idling becomes its
   own row only if A1 finds an engine fault. Reason: dropping it untested could hide a fault, and a test cannot keep
   an actor that never acts.
5. **Maps: concede to A (X6, X7 and D6, all this round).** A's sampling (every 32, 64 past each end, margin 8, no
   `sink < -2` dead zone) also moves D6's non-wet kerbless pieces, and the rule is "every site of its kind". Order:
   X6 first (the pin), then X7, then D6 (A6). Kerbed pieces never sink, and the four hull-edge scenarios must pass on
   each rebuilt map.

Merged row: `| D-192 | 2026-11-26 | X6 p14: worms stuck at the Sphinx cove (decider panel) | Data first: rim.py hull_sink puts every kerbless (non-wet) piece's top ≥ 8 under the land over its span + 64 past each end, 0.04–0.25 cells inland, no −2 dead zone, kerbed never sink; check_wild.py rim.fin error; X6, X7, D6 rebuilt. Then A1, test-first: a doctest shows the uphill stall; actorFloorRiseHasClearance counts a face only where it reaches above the body's rounded bottom (z + 1 + r − √(r² − d²)) and skips faces wholly at or below the stepped feet; no wall-fin step-over. Repro → tests/scenarios/xeen/x6_cove_worms_pursue.yml + regressions.sh + X6 extras, Sand Worm grounded or replaced by a fourth Great Worm; p14 resolved when the rebuilt X6 passes. 75 % | A5 (X6, X7), A6 (D6), then A1 |`
