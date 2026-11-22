# X9's fall landing on X2 (D-54)

## DECISION

**(a), with the dragons moved as well as leashed.** The landing stays at `entrance:x9_fall` (-15360, 3072, 768), facing east, at cell [34, 58]. All three Water Dragons (11640, group 80, Q-C13) get new places further out on the lake and a studio `leash`:

| Dragon (current cell in X2's `sketch.yml`) | New home (cell / units) | `leash` | Leash circle's nearest point to the landing | … to Darzog's door (-16031, 3014) |
| --- | --- | --- | --- | --- |
| [31, 50.5], north | **[23, 48]** / (-20992, 8192), north-west lobe | **1,024** | 6,587 | 6,147 |
| [22.5, 60], west | **[19.5, 58]** / (-22784, 3072), west channel | **768** | 6,656 | 5,985 |
| [36.5, 66], south | **[28, 71]** / (-18432, -3584), south lobe | **1,024** | 6,307 | 5,997 |

All three homes are over water, each at least the leash radius from the shore, give or take one cell. Each is more than 9,700 from X8's lake landing (-10240, 8448).

**This replaces the rule in D-50 change 4 and D-6.4.** The rule becomes: on X2, the nearest point of each lake dragon's leash circle must be at least **5,888** from every fall landing (`entrance:x9_fall` and X8's lake point) and from Darzog's tower door. 5,888 is the 5,120 reach of a monster's ranged attack (`MaximumRangedAttackDistance`, the Ice Blast) plus 768 for the walk to the door. The old 4,000 was below a dragon's firing range.

How the leash works, from the code (`MapDeltaActor::leashRadius`, `ActorBehaviorRuntime` hold-post, `tacticMoveLeavesLeash`):
- A placement with a leash holds its post whatever its `Long` wander says.
- It stops chasing at the edge of the circle and goes home when it has no target.
- It still fires from inside the circle.

So leashing the dragons where they are now would not be enough: the nearest one would still fire from 4,136. The dragons have to move.

## WHY

The fall is the price of missing the unseen way. D-50 Q1 made that price deliberately mild, and D-6.4 keeps fall landings clear of the lake dragons. An ambush by two level-60 dragons on a party that has just lost a third of its HP breaks both, so (c) is rejected. Option (b) strands a fallen party from the cloud stair behind the very trap it would still have to clear. That trap belongs to Act III and Q-C13 ("kill the three dragons for Medin's boat"), not to an Act V ambush. With the move and leash, all three dragons stay on Lake Darzog, still hostile and still killable from the shore for Q-C13, with the same experience and the same qbit. A side effect: the dragon now at [36.5, 66], about 5,750 from Medin's jetty, no longer threatens level 7–11 parties on the east shore. Accepted: the east channel becomes dragon-free, so a party with Water Walk can reach the island early, which only gives the island chest because Darzog's door still needs the key.

## WHO ACTS

- **A5 (X2)**
  - In `gen.py` / `sketch.yml`, move the three 11640 entries to the cells above and add `leash: 1024`, `768` and `1024`. `group: 80`, `hostile` and the notes stay.
  - Rebuild and install, then run `tools/lighting/stale_bakes.py`. Moving actors should not make the bake stale; re-bake if the tool lists X2.
  - Update X2's NOTES. One correction there: the third dragon is 5,976 from the landing by the scene's positions, not 6,800.
  - Playtests, two runs each, from assets_dev:
    - The X2 walk.
    - `playtest_hostility.yml`: the dragons are still hostile.
    - A new short `playtest_lake_dragons.yml`:
      - Wait 60 s and check that each dragon is within its leash + 256 of its home.
      - Put a party at `entrance:x9_fall`: nobody is hurt in 30 s.
      - Kill group 80, then check that `lake_beasts_slain` is set and Medin's boat runs.
  - Re-shoot the `landmark:darzog_tower` view from Medin's jetty. The dragons may read smaller behind the island; that is accepted and is not a gate.
- **A5 (X9)**
  - Change the three fall playtests (`playtest_fall_south`, `_chain`, `_xeendom`) back to checking the dragons:
    - After the landing, wait 20 s on X2.
    - Check that all four members are alive and that each HP equals its value just after the fall.
    - Walk to the tower door and check again.
  - Two runs each. Update X9's NOTES ("Falls").
- **A6 (X8)**
  - Re-run `playtest_fall.yml` (the lake landing) with a 20-s wait after the landing: HP still full, two runs.
- **A1**
  - Nothing, unless a playtest shows a leashed flyer leaving its circle. That is an engine bug and goes to A1.
- **A2, A3**
  - Nothing. Kill experience (Act III under D-1.2), Q-C13 and `Xeen.SkyFalls.x9` are unchanged. A2 reads the new hostility result.
- **Orchestrator**
  - Add the DECISIONS row.
  - Mark the rule in D-50 change 4 and in D-6.4 as replaced by D-54.
  - Close the DECIDE in A5's lane report.

## REVERSIBLE

Yes. This is three placements and three leash numbers in X2's sketch. No ids, qbits, rows, experience or text change. To go back to (c), drop the three `leash` fields and restore the old cells.

## SUMMARY ROW

| D-54 | 2026-11-21 | X9's fall landing on X2 vs the lake dragons | `entrance:x9_fall` kept. Three Water Dragons moved to [23, 48], [19.5, 58], [28, 71] with `leash` 1,024/768/1,024. New rule: leash circle ≥ 5,888 (Ice Blast's 5,120 + 768) from fall landings and Darzog's door; replaces D-50 change 4's and D-6.4's 4,000. Fall tests wait 20 s. Detail: `reviews/D54_DECISION.md` | A5, A6 |
