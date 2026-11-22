# Q-C25's gem tax: decision (D-81)

Decider D-81, 2026-11-21. I read the following:
- `reviews/D68_DECISION.md` (Q1 point 5), `reviews/D59_DECISION.md` and `reviews/D75_DECISION.md` (case 3).
- `output/xeen_a2_check/stat_gates_20261121c.md` (the gem budget) and `output/xeen_a2_check/gems/report.md` (the gem ledger).
- `tools/xeen/balance.py` (`PROMOTION_PAYMENTS` and the gem-budget block).
- `source/quests/q-c25.yml`, `source/quests/q-d27.yml` and `source/towns/xd18.yml`.
- QUESTS.md (Q-C25, the racial promotions), DECISIONS.md D-5.2, ORIGINAL_LINES.md (`xeen/aaze0050:0-2`) and the MAPS.md rows for X7, XD-16 and XD-18.

**DECISION: (a), made precise. The tax stays at the source's 2,000 gold and 20 gems, and no gems are placed. A promotion-path gem row may also count Q-D27's gem wish, which is a fixed choice and not random loot. Counted that way, the row passes: 36 fixed + one wish of 10 − 45 = +1.**

1. **The world does not change.** Option (b) is rejected: no gems on X7's north slope, in XD-16 or in the tax office. Option (c) is rejected: the 20 is the source's own line ("2000 gold pieces and 20 gems fly from your packs", `xeen/aaze0050:0`), and the quest file and ORIGINAL_LINES quote it.
2. **The rule for main payments stays as it is.** D-68's rule still holds: only fixed gems count, and a shortfall fails `--gates`.
3. **Promotion-path rows (D-75, report-only) get one more source: fixed choices.** These are the `alternative: true` gem gives the party can choose before the payment. Today that means only `q-d27.wish_gems`: ten gems, as the third wish of any of the Act V wish lamps in D5 and D6 (Q-D27, level 42, all before the tax at about level 50).
   - The row counts the fewest wishes that close the gap and names them.
   - It shows "pass (one gem wish)" when fixed gems plus those wishes cover the fee.
   - It shows **short** only if all four wishes (40) still leave a gap.
   - Today's figures: 36 fixed against 45 needed is short 9, which one wish covers, for a margin of +1.
4. **Random loot stays out of the pass, but the row's note quotes it.** By the end of Act V the ledger expects about 92 gems without MM9 and 81 with it. Against 45 needed, that is about 36–47 to spare.

**WHY:**
- **The gap is within the shortfall D-59 accepts.** Its standard is "fixed sources reach the number or fall short by at most 10, which one item or one buff can cover". Here the gap is 9, and one fixed, non-random choice covers it. That choice is in the same act as the tax, and it is the very next thing a player who is short would reach for.
- **The wish costs nothing the budget counts on.** The experience and gold wishes are `alternative` too, so the act's experience count already leaves them out (D-53). Taking gems at one lamp therefore costs nothing the balance assumes the party has.
- **Placing gems would not guarantee them at the tax.** The budget's fixed-gem model assumes no optional gem spending. The optional sinks before the tax are large: XD-10's skulls take 26 and D1's gemsmiths 22, and both can be paid again. A placed gem can be spent before the tax. A wish is taken when the player needs it. Nine more fixed gems would also change Act V's gem economy only to make a report row add up.
- **Lowering the tax would change a quoted source line to suit a test.** D-68 explicitly rejects changing a gate number for the chain's sake.
- **Little depends on the tax.** It is optional twice over: D-68 names Scaldrith's 20 as optional, and the Great Wyrm promotion is racial and optional. It also does not gate the Dragon Grandmaster. In `towns/xd18.yml`, Scaldrith teaches as a resident of the office, and the office "stays open to all", with no `tax_paid` condition. The tax gates only the promotion and XD-18's interior, which is level 60–64. A party arriving at that level also holds Act VI's four fixed gems.
- **Promotions segment 67's D-68 CONVENTION (gems 0 → 20, after the honest try) stands as D-75 left it.** The chain's party holds no gems, and that has nothing to do with this budget.

**WHO ACTS:**
- **A2:**
  - In `tools/xeen/balance.py`, let promotion-path rows count fixed choices as in point 3. Main rows stay fixed-only.
  - Collect the alternative gem gives the same way `gifts` collects fixed ones, keeping them in their own list, and change the shortfall message to match.
  - Regenerate the stat-gate report. The Q-C25 row should read 36 fixed + 1 wish (10), required 45, margin +1, "pass (one gem wish)", and the promotion short line should disappear.
  - Add a ledger note that the Dragon Tax uses one Q-D27 gem wish (D-81).
- **A3-side (q-c25):** nothing. Keep the 20 gems and the texts.
- **A3 (q-d27):** nothing. If `wish_gems` ever drops below 9 gems or leaves Act V, the row goes **short** again and comes back to a decider.
- **A5 (X7), A7 (XD-16, XD-18), A8:** nothing. No gems are placed.
- **A3-promo:** nothing. Segment 67's convention stands (D-75).

**REVERSIBLE:** Yes. The change is one report rule in `balance.py`, and nothing in the world or the playthroughs changes. If a later change to the gem economy makes the gap bigger than one wish, the row reports it and the placement option comes back.

## SUMMARY ROW

| D-81 | 2026-11-21 | Q-C25's gem tax | Keep the source's 20 gems; place none. Promotion-path gem rows may count fixed choices: one Q-D27 gem wish (10, Act V) covers the 9 short (+1). Main payments stay fixed-only. Detail: `reviews/D81_DECISION.md` | A2 |
