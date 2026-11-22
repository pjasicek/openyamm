# M1's pest count: decision (D-78)

**DECISION: (a).** Take the kill count out of QUESTS.md, because the game as built is the intended design. M1 has no pest kill count and no pest reward. Its journal line ("Mayor Gunther wants Vertigo rid of its slimes and doom bugs.") stays until `m2.done`. Gunther pays once, in M2, after Joe's invoice. Replace the "Reward / outcome" cell of QUESTS' M1 row with:

> Journal (until M2). No reward of its own: as in the source, Gunther thanks and pays the party once, for the cleanup and Joe's exposure together, in M2.

`m1.yml` stays as it is (`rewards: {xp: 0, gold: 0}`, no kill hook). So do segment 01 and the guide's act1 text, including "Gunther does not pay for kills".

**WHY**
- **The source has no kill count.** In the original Vertigo, Gunther's event (`maze0028`, cell 14,5) checks only the quest flags (20/9 and 20/10). Text 2 then rewards both deeds in one line: "Thank you for cleaning up Vertigo and discovering Joe's treachery … the outstanding citizenship award and this treasure". `maze0028` never uses the "all monsters dead" opcode (42); only `maze0032` and `maze0050` do. So "cleaning up" is part of exposing Joe, which is our M2 (1,500 XP, 1,000 gold). A separate kill count would change the source's quest shape, which QUESTS' first rule says to keep.
- **The story is better without it.** Joe breeds the pests. A kill count would pay the party to clear a plague whose answer is the invoice. The original's joke is that exterminating never works.
- **Budget.** Act I quest experience is 15.8k of 16.5k per member, so there is about 0.7k of room. A Gunther reward would fit only at 500 XP or less, too little to be worth an extra quest step. Kill XP pays for the pests already, and Act I's kill ledger is at 1.15 with traps. A count adds no XP of its own, but it would make players clear X1 and its meadows.
- **Cost and risk.** Building it would take A5's grouping of X1's pests, an `evt.CheckMonstersKilled` check on merge point 31's InvisibleAsDead rules, a new Gunther state, a new qbit, changes to segments 01 and 03, a guide rewrite and an A2 recount. A map-wide outdoor count is also fragile: wanderers, monsters in the meadows, hidden actors. Option (a) changes one table cell and matches the build, segment 01 and the published guide.

**WHO ACTS**
- **Orchestrator:** edits the M1 row in `devdocs/xeen/QUESTS.md` (the text above) and adds the DECISIONS.md row.
- **A3:** closes G item 28 as "final as built (D-78)" in `lanes/G.md` and the A3 answers. No change to quest files.
- **G:** keeps act1's M1 text as it is.
- **A5, A2:** nothing to do. The build tasks of option (b) are not started.

**REVERSIBLE:** Yes. Nothing is built or removed, so option (b) can still be added later. If it is, it should be an optional Gunther topic, separate from M1 and M2, paying no more than 500 XP within Act I's remaining room. It would need A5's X1 groups, the merge point 31 count, A3's new state and qbit, segment 01/03 assertions, the guide's "does not pay for kills" line rewritten and an A2 recount.

**SUMMARY ROW:** | D-78 | 2026-11-21 | M1's pest kill count | Strike it: the source's Gunther pays once, for cleanup and Joe together (maze0028, no kill-count check), and the build already does. QUESTS' M1 row says "no reward of its own, paid in M2". No build. | orchestrator (QUESTS), A3 (G item 28) |
