# Prerequisites in branch chains: decision (D-75)

Decider D-75, 2026-11-21. I read the following:
- `reviews/D68_DECISION.md`.
- `tests/playthrough/PLAYBOOK.md` §1–§2.
- `tests/playthrough/xeen/promotions/README.md`, its `run.py` STARTS, segments 25, 51 and 67, and the prep sheets `C_pagoda.md`, `E_H_tier2_rest.md` and `F_racial.md`.
- The main chain's segment list. Main 57 asserts 111400; no main segment plays Q-C4, Q-C15 or Q-C25.
- `tests/scenarios/xeen/side_quests/q-c15_troll_problem.yml`. It starts from a new game on X5 and asserts 112302 at its end.
- The quest files `t2-clan.yml`, `t2-leafpoint.yml`, `q-c15.yml`, `m20.yml` and `q-c25.yml`.
- The MM9 promotions README. MM9 branches block E from main 60 because no earlier checkpoint holds key 108. It never stands a key in.

## The rule

**DECISION: Extend CONVENTION by one narrow kind, `prerequisite`. It is allowed only in branch chains (promotion chains) and standalone scenarios, never in the main chain.**

A branch segment may set a quest-prerequisite qbit as a logged CONVENTION only when all of the following hold:

1. **No natural branch point.** No checkpoint of the main chain or of this chain carries the bit together with the state the segment needs. If one exists, and branching from it loses none of the segment's checks, the segment branches from it, and the convention is not allowed.
2. **Proven elsewhere.** Another test in the long-check family plays the content and asserts this exact bit set. That can be a main-chain segment, a side-quest scenario, or a segment of the same chain. The log line names that file. If the file is removed, stops asserting the bit, or fails, the line counts as an ISSUE, not a CONVENTION.
3. **The gate reads only that bit.** The step's state condition in the quest file depends on the bit alone, plus what the segment plays itself. The convention is not allowed if the gate also needs something the prerequisite content leaves behind: items, map state, other bits or NPC moves. Then the segment replays the leg or branches later.
4. **The honest try comes first.** The segment plays the gate closed and asserts its refusal line before it sets the bit. This is the prerequisite form of D-68's honest try, and it proves the gate itself.
5. **Exactly the bit, nothing else.** The segment sets one qbit. It sets none of the prerequisite's rewards, experience, items, autonotes or other bits. This is the prerequisite form of "only the shortfall".
6. **It switches itself off loudly.** The segment asserts the bit clear at its start. If the start state ever carries the bit naturally, that assert fails, and the segment goes back to the natural path, as PLAYBOOK §2 already requires for fixed workarounds.
7. **Checkpoints are contained.** A checkpoint carrying a stood-in bit never starts a segment that checks the prerequisite's own quest, and never feeds the main chain.
8. **The log line has a fixed form:** `log("CONVENTION prerequisite <quest>.<bit> (<id>): <why the chain does not play it>; proven by <test path>")`. The report lists it in the existing CONVENTION section.

A logged class setup (`SetPlayerClass`) is a different thing. It stays a "test setup" line, not a CONVENTION, because the class is the subject under test, not a prerequisite.

**WHY:**
- D-68's definition already covers prerequisites: a CONVENTION is "a logged stand-in for progress the chain does not play".
- Its two guards carry over directly:
  - The honest try becomes "the gate is played closed first".
  - The shortfall becomes "the one bit the gate reads, and nothing else".
- Replaying would duplicate whole legs that are already proven: main 39–57 for M20, and Q-C15's full XD-23 walk plus two pyramid crossings for Leafpoint. That is the duplication the branch design exists to avoid ("nothing the main chain plays is replayed").
- Condition 3 keeps the stand-in from hiding a game bug. Condition 2 keeps it from hiding untested content.
- MM9 is consistent with this. It branched later where a natural branch existed (condition 1), and it never needed a stand-in.

**WHO ACTS:**
- **A3** adds this text to `tests/playthrough/PLAYBOOK.md` §2, directly after the stat-gate CONVENTION bullet:

  > "A `CONVENTION prerequisite` line (branch chains and standalone scenarios only, never the main chain) sets one quest-prerequisite qbit that no usable checkpoint carries: another named test must play that content and assert the bit, the gate must read that bit alone, the segment first plays the gate closed and asserts the refusal, sets nothing else, and asserts the bit clear at its start: `log("CONVENTION prerequisite <quest>.<bit> (<id>): <why>; proven by <path>")` (Xeen: D-75)."

- **A3-promo:**
  - Make `promotions/run.py` check each `CONVENTION prerequisite` line: the named path exists and has a `qbit_set` containing the id. A miss is reported as ISSUE.
  - Update the README's "CONVENTION lines" bullet to name D-75.

**REVERSIBLE:** Yes. This is a rule wording plus a report check. A stood-in bit lives only in branch checkpoints.

## Case 1: `m20.started` in segment 25 (T2-CLAN)

**DECISION: Keep it as a CONVENTION prerequisite. Fix only the log form.**

**WHY:**
- No checkpoint holds both `q-c4.done` and `m20.started`. The main chain never plays Q-C4, and block C plays it itself in 21.
- Re-rooting block C at a later X5 checkpoint (main 85 or later) would set m20 naturally. But it would lose 25's pre-m20 refusal ("Strong, yes. Ready, no."), which is the only check that the gate is closed. It would also move Q-C4 and T1-D past Act IV. Condition 1's "loses none of its checks" fails, so the convention is the better choice.
- The travel pyramid does not help. Crossing sides does not set m20; only replaying main 39–57 does.
- The other conditions hold:
  - `t2-clan.yml`'s state needs only `promotable: clan` and the `m20.started` bit, inside `show: q-c4.done`, which the block plays.
  - The refusal is asserted first.
  - 111400 is asserted clear at the start.
  - One bit is set.
  - The block ends at 27, and its checkpoints feed nothing else.
  - Main 57 asserts 111400.

**WHO ACTS:**
- **A3-promo:** rewrite 25's log line as `CONVENTION prerequisite m20.started (111400): the Act IV main story on the Darkside; block C starts on Cloudside after Q-C4 (21); proven by tests/playthrough/xeen/57_lost_souls.yml`. Rerun `run.py 25 27` once.

**REVERSIBLE:** Yes. This is one log line.

## Case 2: `q-c15.done` in segment 51 (T2-LEAFPOINT)

**DECISION: Keep it as a CONVENTION prerequisite. Fix only the log form.**

**WHY:**
- No checkpoint anywhere carries 112302, so no natural branch point exists.
- Replaying would copy the side-quest scenario's whole XD-23 route (about 120 steps), plus two pyramid crossings and the walk from D1 to D4. That gives two copies of one route to maintain and proves nothing new.
- The other conditions hold:
  - `t2-leafpoint.yml`'s states read `q-c15.done` alone, plus `promotable`.
  - The stranger's refusal is asserted first.
  - 112302 is asserted clear at the start.
  - Only the bit is set: no Thickbark reward, and none of Q-C15's 112300, 112301 or 110930.
  - Block E ends at 53.
  - `q-c15_troll_problem.yml` asserts 112302.

**WHO ACTS:**
- **A3-promo:** rewrite 51's line to the fixed form, ending `; proven by tests/scenarios/xeen/side_quests/q-c15_troll_problem.yml`. Rerun `run.py 51 53` once.
- **A3-side:** if Q-C15's done bit is renumbered, the scenario and 51 change together. The run.py check catches a miss.

**REVERSIBLE:** Yes.

## Case 3: the tax gems in segment 67 (Q-C25)

**DECISION: It is already a valid D-68 CONVENTION (loot, gems up to a fee). No new rule is needed and no change is required.**

**WHY:**
- This is a missing loot item, not a prerequisite bit, so it falls under D-68's existing "gems or gold only up to the fee".
- The honest try is played: Scaldrith's "No gems, no entry" is asserted, with no gold taken.
- The grant equals the shortfall: 20, against 0 held.
- The step fails loudly if the party ever holds a gem: `error(... 'grant only the shortfall')`. That is an acceptable loud switch-off, because `grant_item` counts are fixed and the step can never over-grant.
- If a later party holds 20 or more gems, the refusal assert fails first, and the segment then goes to the natural path.
- The current form `CONVENTION loot q-c25 gems: 0 -> 20` is fine.

**WHO ACTS:**
- **A3-promo:** nothing required.
- **A2:** add Q-C25's 20 gems to `balance.py`'s gem-budget table (D-68 5) as a promotion-path payment, because the Great Wyrm promotion cannot be reached without the tax. This is report-only. A shortfall goes back to the deciders as a world change.

**REVERSIBLE:** Yes.

## SUMMARY ROW

| D-75 | 2026-11-21 | Prerequisites in branch chains | Branch chains (never main) may set one prerequisite qbit as `CONVENTION prerequisite` when no checkpoint has it, a named test asserts it, the gate reads it alone, the refusal is played first, the start asserts it clear. 25 and 51 kept (log names proof); 67 already D-68. Detail: `reviews/D75_DECISION.md` | A3-promo, A3, A2 |
