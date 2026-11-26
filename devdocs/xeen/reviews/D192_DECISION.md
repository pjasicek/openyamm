# D-192: X6 p14, worms stuck at the Sphinx cove (panel of three, converged, 2026-11-26)

Panel: proposals and second rounds in [D192_panel/](D192_panel/) (`a.md`, `b.md`, `c.md`). Brief:
[DECIDER_BRIEF_20261126b.md](DECIDER_BRIEF_20261126b.md). Each panelist ran the repro on the released binary (logs in
`output/xeen_fb/d192_a/`, `d192_b/`, `d192_c/`). Converged by the orchestrator from the second round; no point needed a
third.

## What the panel measured

Two of three Great Worms stay stuck (not one): at the `hull_092`/`hull_093` seam and at the cove's east corner
(`hull_094`, never sunk). Every stalled frame ends with zero velocity and no contact: a refused step, not a wall slide.
The tops stand 1–8 over the land past the pieces' ends (X6 6 of 11 kerbless pieces; X7 up to 52). The cause, agreed by
all three: `actorFloorRiseHasClearance` (`OutdoorMovementController.cpp`) treats a walking actor going uphill as a
flat-bottomed cylinder and refuses a step if any face top within its radius stands above the target foot; on level
ground the same top is stepped onto. The planner is right that the lip can be crossed.

| Point | Round 1 | Final | Panel |
| --- | --- | --- | --- |
| Order | A, B data first; C engine only | **Data first, then the engine test-first** | all three |
| Engine rule | A none unless a doctest shows it; B the body's rounded bottom; C ≤ 32 tolerance | **Doctest first; then a face counts only where it rises above the low sphere's rounded bottom, `z + 1 + r − √(r² − d²)`** (as the collision sweep) | all three (C dropped 32: X7's fins reach 52, and a flat allowance breaks the "sloped and off-center" doctest) |
| The check | A `check_wild.py rim.fin`; B `check_hull_tops.py`; C `rim.py --check` | **`rim.fin` error in `tools/xeen/check_wild.py`**, the sampler in `rim.py` shared with `hull_sink` | B, C (A conceded the other way) |
| Sand Worm in the repro | never moves in any run | **dropped from this scenario; a fourth Great Worm on the ground north of the cove (~ -16896, -9216); the idle Sand Worm (hangs at z 2200, never acts) is a separate A1 item** | A, C; B's fallback |
| Maps | | **X6 now, X7 straight after; D6 when `rim.fin` flags it** | merged |

## DECISION

1. **A5 (data, closes the pin):** `tools/xeen/common/rim.py` `hull_sink` samples the land along each kerbless piece's
   span and 0.25 cell (64) past each end and sinks the piece's top to that land minus 8, with no `sink < -2` dead zone.
   Kerbed pieces never sink (the round's incident); the +24 pieces over water stay. `check_wild.py` gains error
   `rim.fin` (a kerbless top over the land past its ends) using the same sampler. Rebuild X6 first, then X7; D6 if
   `rim.fin` flags it. The four hull-edge scenarios (`x1_hull_edge`, `x4_hull_edge`, `x7_edges` and the void tests) must
   still pass.
2. **Closing test:** `output/xeen_fb/p5_engine2/r5/x6_cove_worms_pursue.yml` moves to
   `tests/scenarios/xeen/x6_cove_worms_pursue.yml` without the Sand Worm, with a fourth Great Worm north of the cove,
   keeping "every worm within 700 of the party after 16 turns"; it joins `regressions.sh` and X6's extra scenarios.
   **X6 p14 is resolved when the rebuilt X6 passes it.**
3. **A1 (engine, next merge point, test-first):** a doctest on plain geometry, uphill vs level, shows the stall. Only if
   it does: in `actorFloorRiseHasClearance` (actors only; the party untouched), a face counts only where it reaches
   above the body's rounded bottom as above. Cases: fins of 3, 16 and 32 let a walker through; a 64 fin, a 150 kerb and
   the back of a low wall still stop it; the four existing clearance doctests pass unchanged. MM6–MM8 pursuit and
   hull-edge scenarios rerun at the merge point.
4. **A1 (separate item):** why the repro's Sand Worm never acts (hangs at z 2200 for every turn).

## WHY

Data first touches only Xeen, works on the released binary and is built into the generator, so later rebuilds keep
it. The engine fix is still right (the same refusal would stop any walker uphill against any low top), but only with a
doctest showing the stall and the sweep's own body shape: a flat tolerance either fails X7's 52 or lets monsters climb
railings, parapets and low town walls in every world. The requested general "step over a tread-less fin lower than a
step" is rejected for the same reason.

## WHO ACTS

A5 (rim.py, check_wild.py, X6 and X7 rebuilds; medium), A6 (D6 if flagged), A1 (doctest and the clearance rule; small
to medium; the Sand Worm item), orchestrator (the scenario's move into `tests/scenarios/xeen/` and `regressions.sh`).

## REVERSIBLE

Yes. 75 % (the weakest point: whether `hull_095`'s 150 kerb blocks worms further along the cove's east edge; the
scenario will show it).

## SUMMARY ROW

`| D-192 | 2026-11-26 | X6 p14: worms stuck at the Sphinx cove (panel of three) | Cause: actorFloorRiseHasClearance refuses an uphill step against a hull top 1–8 over the land (two of three worms stuck). Data first: rim.py hull_sink samples 64 past each end, sinks kerbless tops to land − 8 (kerbed never), check_wild.py error rim.fin; rebuild X6, then X7, D6 if flagged. Then A1 test-first: a doctest shows the stall, then a face counts only above the body's rounded bottom (as the sweep); no general fin step-over. Closing test tests/scenarios/xeen/x6_cove_worms_pursue.yml (Sand Worm out, a fourth Great Worm) in regressions.sh; the idle Sand Worm a separate A1 item. Detail: reviews/D192_DECISION.md, panel in reviews/D192_panel/. 75 % | A5, A6, A1, orchestrator |`
