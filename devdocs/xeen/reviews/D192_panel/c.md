# D-192, panel member C, round 1: X6 p14, worms stuck at the Sphinx cove

Read: the brief, PLAYER_FEEDBACK_20261126.md (R5, outdoor2's "X6 hull", the Round summary),
`game/outdoor/OutdoorMovementController.cpp` (`resolveOutdoorActorMove`, `actorFloorRiseHasClearance`,
`queryFloorLevel`, the sweep), `game/outdoor/OutdoorPathfindingBuilder.cpp`, `level_generation/projects/xeen/common/rim.py`
(`hull_sink`, `hull_pieces`), the `xeen_deco_hullf.glb` triangles, X6's L4 sketch (hull_088–098), D-109, D-113, D-114,
D-140. I did not read a.md or b.md.

## What I measured (two runs, `build-xeen/game/openyamm` of 16:34, installed X6)

Run 1 did not start: the scenario path was relative. Run 2 was the repro with a report every 2 turns and the
pathfinding log on (`output/xeen_fb/d192_c/x6_cove_probe.yml`, `run2.log`, user data `d192_c/ud1`). Result:

- **Two worms are stuck, not one.** Worm 149 holds from turn 4 at (-15858.2, -10196.5, 1533.3), cell (33.03, 83.91),
  the cove's NE corner. Worm 150 holds from turn 4 at (-16427.9, -10176.0, 1501.3), cell (31.91, 83.88), the
  hull_092/093 seam. Both still have a successful plan (149: 51 waypoints going south-east round the corner; 150: going
  east). Each frame they get `desired` toward the waypoint, then `velocity=(0,0,0)`, `moved_horizontal=0`,
  `contacts=0`, `water_result=none`, support terrain, the same position to the last digit. They do not slide or turn
  aside: the movement throws the whole move away. Worm 151, on a route away from the rim, reaches 450 from the party.
- **The fourth actor never acts.** The Sand Worm (11440) spawned at (-17920, -8704, 2200) stays at z 2200 for 16
  turns, animation 7, with no pathfinding line. This is not the pin, but the repro's fourth assert would fail on it
  after the worms are fixed.
- **The fins are now 1–3 units high.** Installed land (`wild._terrain_at`): hull_094 (`xeen_hullf`, no `raise`) has its
  top at 1536 (the land under its strip is 1536 everywhere), but the land just north of its north end cap, where
  worm 149 stands, is 1532–1535. hull_093's top was sunk to 1504. The land at its west end cap rises from about 1500
  where worm 150 stands. outdoor2's `hull_sink` turned R5's 16–32 fin into a 1–3 one, but it is still there, because a
  flat top on sloping land always stands a little over the land on its lower side.

**Why a 3-unit fin stops a 40-radius worm (from the code).** `resolveOutdoorActorMove` sweeps the body. The sweep's
low sphere rolls over a lip lower than its radius. Then `settleActorToGround` checks the new spot: where the land
rises (terrain floor + `GroundSnapHeight` above the foot), it calls `actorFloorRiseHasClearance`. That function's
vertical-face branch skips a face only when `geometry.maxZ <= targetFootZ + CollisionEpsilon`, so any vertical face
whose top is even 1 unit above the target foot blocks, wherever its 2D footprint comes within the body's radius. The
end cap of a `xeen_hullf` is a vertical face 2,700 deep. Its top edge is the strip's 48-unit end, and below the land it
slants 300 inland, so its footprint reaches 300 under the land at height `maxZ`. When settle fails, the actor goes
back to `supportPosition`, its velocity is zeroed and the move ends. The next frame repeats this. So the actor is frozen
for as long as its path leads uphill past a hull cap. The planner is right: the strip's top is a floor and a 3-unit
lip is passable. Only the movement controller says no.

## DECISION

**Engine first (A1). The data half is already done and stays as it is. Then the repro becomes a tracked test.**

1. **A1, `game/outdoor/OutdoorMovementController.cpp` `actorFloorRiseHasClearance`:** a vertical face (|normal.z| ≤
   eps) whose top is no more than a riser allowance over the target foot is a riser left to the sweep, not an overhead
   blocker. Change the branch `else if (maxZ <= targetFootZ + CollisionEpsilon)` to
   `else if (maxZ <= targetFootZ + ActorRiserAllowance)`, with a new
   `constexpr float ActorRiserAllowance = 32.0f;` and, at its three call sites (settle twice, step floor once), the
   allowance capped by the body's `maxStepHeight` (pass it in: `std::min(ActorRiserAllowance, maxStepHeight)`). Update
   the comment: "A riser up to a kerb's height over the target foot is the sweep's matter (its low sphere rolls over a
   lip). Without this, a hull cap standing 1–3 over sloping land froze Xeen's worms at X6's Sphinx cove (F75, D-192)."
   Leave the sloped and horizontal branches, the sweep, the planner and the party's `resolveMoveForBody` unchanged.
2. **A1, doctest** in `tests/GameplayRuleRegressionTests.cpp`, beside "outdoor actor movement can separate from
   coincident actors". Name: "outdoor actor walks uphill past a topless fin lower than a riser and is still stopped by a
   kerb". Set up terrain rising 8 over 128 toward a single vertical quad with no tread, and an actor of radius 40 walking
   along it within 30 of its end. With fin tops 3, 16 and 32 over the land at the actor's foot, the actor moves on. With
   a top 64 over, the actor is stopped by the sweep, as today. With a 150 kerb, the actor is stopped.
3. **A5, no data change for this pin.** Keep `rim.py hull_sink` as installed (kerbless pieces sunk to their strip's
   lowest land, kerbed pieces never sunk, D-113's kerb). Optional and small: a read-only `rim.py --check` line that
   fails a kerbless piece whose top stands more than 32 (the engine's allowance) over the land within 0.15 cells beyond
   either end. outdoor2's `output/xeen_fb/p5_outdoor2/hull_fins.py` is the start; widen its samples past the ends.
   Today it would find nothing, which is the point.
4. **The test that closes the pin.** A1 moves `output/xeen_fb/p5_engine2/r5/x6_cove_worms_pursue.yml` to
   `tests/scenarios/xeen/x6_cove_worms_pursue.yml` (header: D-192, the riser allowance). It keeps the four 700 asserts
   after 16 turns. First, the Sand Worm: spawn it at its land height (about 1,440 at that spot) instead of 2200. If it
   still never acts, A1 finds out why (an engine fault outside this pin is logged as its own row). Only if it is a quirk
   of that monster, replace it with a fourth Great Worm at a grounded spot north of the cove, e.g. (-16896, -9216). Add
   the file to `tools/xeen/regressions.sh`'s scenario list (it is an engine movement guard) and to X6's extra scenarios
   in the map lane's run (`x6) EXX=...x6_cove_worms_pursue`). X6 p14 is resolved when it passes on the released binary
   with an after picture at the pin's pose.
5. **MM6–MM8 check at the merge point:** the regression set (MM7/MM8/MM9 round trips),
   `tests/scenarios/mm6/temple_of_tsantsa_monster_pursuit.yml`, `tests/scenarios/xeen/x1_bridge_walkers.yml`, the
   hull edge scenarios (`x1_hull_edge`, `x4_hull_edge`, `d1_hull_edge`, `x7_edges`) and the unit tests. Name the
   behaviour change in the release note: "outdoor monsters are no longer held by a wall top up to 32 above the ground
   they step onto".

## WHY

- **The cause is in the engine, and data can only chase it.** A flat-topped piece on land that is not flat stands a few
  units over the land at some edge. Sinking further (below the lowest land beyond the ends, as well) would leave a
  trench along the lip of every sand and lava fall. It would do nothing for kerbless studio pieces elsewhere (pads,
  plinths, bridge ends, D-170), and it would need doing again at every rebuild. The engine rule fixes the whole class
  with one constant. `hull_sink` was still worth it: it cut the fins from 16–32 to 1–3, and it stays.
- **Why 32 and not the full step height (128), as R5's request worded it.** The two tests disagree today: the sweep
  lets a body roll over a low lip, and the clearance test refuses even 1 unit. The allowance only has to cover what the
  sweep already lets through for these bodies, and every fin measured in the round (1–3 now, 16–32 before the sink).
  Outdoor faces are single-sided on terrain maps, and the sweep ignores a face approached from behind. Uphill, this
  clearance branch is the only thing keeping an actor out of the back of a low wall. At 128 it would let actors through
  the backs of MM6–MM8 parapets, low town walls and fences (64–128) on rising ground. At 32 nothing of that height
  changes, and Xeen's kerbs (about 150) stay walls. If a later fin needs more, raise the constant on evidence, with the
  doctest.
- **Rejected: clipping the face to its height at the body** (the slanted cap's buried part is lower than `maxZ`). It is
  more exact, but on its own it frees neither worm: both stand at the cap's real top edge, 1–3 over their foot.
- **Rejected: a planner change** (keep a radius off hull caps, or off model faces near the void). The planner's route
  is valid. Steering round a passable lip would hide the controller's fault and leave it for every other topless fin.
- **Rejected: closing the pin on data alone, or leaving the repro in scratch.** R5 asked for a tracked test, and this
  is an engine guard, so it goes into `regressions.sh`, not only into X6's run.
- **Precedents.** D-140 (the hull is the only `collision: model` decoration; low rocks are stepped over at 128),
  D-113 (the kerb is meant to stop the party, so it must stay a wall), D-185 (monster-fit gates are checks, not
  hacks), and AGENTS.md "Architecture" (a shared movement fix, not an X6 special case).
- **Least certain:** that the settle-path clearance is the only blocker. I read it from the code and the log
  (`velocity=(0,0,0)` with no contact or water result matches the reject-and-revert path exactly), but I did not run a
  build with the change. Past the corner, hull_095's kerb (`xeen_hull4`, about 150) may squeeze the route along the
  cove's east edge. The scenario will show that.

## WHO ACTS

- **A1:** the one-line rule plus the parameter at three call sites, the doctest, moving and fixing the scenario, the
  regression list, the merge-point checks and the release. Small: about half a lane session including the build and
  `regressions.sh`.
- **A5 (optional):** the `rim.py --check` fin line. Tiny.
- **Orchestrator:** the DECISIONS row, and closing X6 p14 when the scenario passes.

## REVERSIBLE

Yes: one constant and one comparison, with the doctest and the scenario guarding it. Confidence 75 %. It is 85 % that
the engine side is the right fix and that data needs nothing more. The lower figure is for whether 32 is enough
without a second blocker past the corner.

## SUMMARY ROW

`| D-192 | 2026-11-26 | X6 p14: worms stuck at the Sphinx cove (decider panel) | Engine first: actorFloorRiseHasClearance treats a vertical face whose top is ≤ 32 (capped by the body's step) over the target foot as a riser left to the sweep (today 1 unit froze worms 149/150 at hull_093's and hull_094's caps, fins 1–3 after hull_sink); no further data (hull_sink stays, kerbs never sunk; optional rim.py --check fin > 32); doctest; repro moved to tests/scenarios/xeen/x6_cove_worms_pursue.yml with the idle Sand Worm grounded or replaced, added to regressions.sh and X6's extra scenarios; MM6–MM8 pursuit and hull-edge scenarios rerun. 75 % | A1 (A5 optional) |`

## Round 2

Read a.md and b.md. All three runs agree on the facts: worms 149/150 are frozen at the cove corner and the
092/093 seam, by a refusal (velocity 0, no contact) uphill, at a face top about 3 over the land. The Sand Worm never
acts.

1. **Data first or engine only: concede, data first.** B measured kerbless tops 7–8 over the land past their ends on
   6 of X6's 11 pieces and up to 52 on X7. That is beyond my 32, so an engine allowance alone would not even clear
   X7. The data fix also runs on the released binary and closes the pin in one X6 rebuild. Take B's numbers:
   `hull_sink` samples along the strip and 0.25 cell past each end cap (inland 0.04–0.64, void left out), sinks to that
   lowest land minus `HULL_SINK_MARGIN = 8`, still at most 128, drops the `sink < -2` dead zone (A), and only for
   `SINKING` kinds outside the wet branch. Kerbed pieces never sink.
2. **The engine fix: concede my ≤ 32 constant, merge A's order with B's rule.** A1 writes the doctest first (A): uphill
   and level approaches to a 48-deep tread about 3 over terrain rising 1 in 16, with a riser to its top and steep back
   faces running below the land. It reaches the tread on level ground and stalls uphill today. If it stalls, the fix is
   B's: in `actorFloorRiseHasClearance` a face obstructs only where its height at 2D distance d exceeds the low
   sphere's bottom, `position.z + 1 + r - sqrt(r² - d²)` (d < r), the standing band above unchanged, for every face
   branch. B's objection to a fixed lip holds: the sphere is the shape the sweep already moves, so the two agree with
   no magic number. A's narrower rule ("a face wholly below the stepped feet") is not enough. The refusal comes in the
   settle path, where the target foot is the terrain's, below the 1536 tread, so that rule would not free worm 149.
   If the doctest does not stall, there is no engine change (A).
3. **The check: merge.** The sampler lives in `rim.py` (B's `hull_tops`, the same code `hull_sink` uses). The error
   is A's `rim.fin` in `tools/xeen/check_wild.py`, the existing per-map rim gate (it already holds `rim.hull_step`
   and runs in every stage install). No new script, and I drop my `rim.py --check`. A warning, not an error, where a
   piece is already at -128 (B: X7 `hull_067`, `hull_077`).
4. **The Sand Worm: concede, drop it.** It never logged a move in any of the three runs, so the 700 assert can never
   pass whatever the geometry. The closing test has three Great Worms within 700 after 16 turns, and the header says
   why the Sand Worm is gone. A separate DECISIONS/STATUS note goes to A1/A2: a Normal-AI Sand Worm spawned at z 2200
   never acts. That may be a real fault, but it is not this pin's.
5. **Maps: merge.** Rebuild, gate, bake and install X6 now, then X7 at once (B measured 9 of 11 tops over the land).
   D6 only when `rim.fin` flags it, at its next rebuild (B found no non-wet change there). The scenario moves to
   `tests/scenarios/xeen/x6_cove_worms_pursue.yml`, joins `regressions.sh` and X6's extras, and resolves X6 p14 when
   the rebuilt X6 passes it. `x1_hull_edge`, `x4_hull_edge`, `d1_hull_edge` and `x7_edges` must still pass.

Final row: `| D-192 | 2026-11-26 | X6 p14: worms stuck at the Sphinx cove (decider panel) | Both, data first. A5: rim.py hull_sink samples 0.25 cell past each end and sinks kerbless pieces to that land − 8 (no dead zone; kerbed never); check_wild.py rim.fin (shared rim.py sampler); rebuild X6, then X7, D6 only if flagged. A1, test-first: uphill doctest; if it stalls, actorFloorRiseHasClearance counts a face only above the low sphere's rounded bottom (no fixed lip, no wall-fin step-over). x6_cove_worms_pursue.yml without the idle Sand Worm joins tests/scenarios/xeen/ and regressions.sh. 75 % | A5 (+A6 D6), A1 |`
