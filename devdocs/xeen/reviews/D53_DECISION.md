# Act V quest experience (D-53)

**DECISION:** (d), which combines (b) and (c) with a smaller wish.
- **XD-17's well: 20,000 → 15,000** experience, once per character. The award "Found Shangri-La" and the player bit 11358 stay. This is the trim D-50 Q1 already named.
- **Q-D27's experience wish: 3,000 → 2,000** per member, per wish lamp. Taking it at all four wish lamps now gives at most 8,000. The gold wish (10,000), the gems wish (10 gems) and the greedy lamp (5,000 shared, or 5,000 lost) stay as they are.
- Every other Act V source stays: D5's lair 1k, D6's archers' camp 1k, the Books of the Dead 9k (they also cost 24 years of age), X9's five nests 5 × 2,000, X7 0.5k, and the 195.0k from the quest files.
- **The gate rule is unchanged.** `balance.py` still counts one route per exclusive choice, and the gate applies to that counted route. A2's report adds one line, "most experience": the counted route plus every experience-or-goods choice taken as experience (the wish lamps). That line must also stay at or below 1.15.
- The extra experience on the violent route (QUESTS §0's rule; Q-D16's throne 14k against 12k) is reported but not held to the gate.
- **Result:** the counted route is 231.5k of 209k (1.11). With all four lamps taken as experience it is 239.5k (1.146, inside the gate). Adding Q-D16's violent throne makes it 241.5k (1.16), reported only.

**WHY:**
1. With the wishes at 3,000, the all-experience route is 248.5k (1.19), over the 15 % gate. Option (b) alone still leaves it at 244.5k (1.17), and option (c) alone at 243.5k (1.165), so only the two together bring it inside, at 239.5k (1.146).
2. At 1.13, the counted route leaves only about 4k (2 %) for Act V hooks not yet in A3's files (D6's remaining hooks, XD-19, DD-24). It also comes on top of Act IV's accepted 1.10 (D-16, +16.5k), so the two acts together are about 0.8 of a level over at level 55.
3. The well at 15,000 is still the act's largest single reward. It is about 0.3 of a level at 48 and well under the 0.75-level cap.
4. A 2,000 wish equals one roc nest (D-50 Q5), so experience is still a real choice against 10,000 gold or 10 gems.
5. The counted route drops to 1.11, close to the 1.10 the question aimed for, and that is enough margin for the hooks still to come.

**WHO ACTS:**
- **A3:**
  - `source/npcs/xd17.yml`:
    - the well's line becomes `AddValue(Experience, 15000)`;
    - its text becomes "(+15,000 experience)";
    - its `where` text and the 11358 note say 15,000.
  - `source/quests/q-d27.yml`:
    - `wish_experience` becomes `{xp: 2000}`, with the text "(+2,000 experience)";
    - the header comment becomes "up to 2,000 per member per wish lamp (four lamps, 8,000 at most)";
    - `rewards` says 2,000.
  - Regenerate `xeen_quests.lua` and the hooks. Update any playthrough segment or scenario that checks the well's or a wish's experience.
- **A2:**
  - Ledger rows: XD-17 at 15,000 (D-53), and the wish lamps at 2,000 ×4 under "most experience".
  - Add the "most experience" line to `balance.py`'s act table. It takes each experience-or-goods choice at its highest `xp`, here Q-D27's wishes. Report it beside the counted route.
  - Recount and publish the new figures: counted 231.5k (1.11), most experience 239.5k (1.15).
  - If later Act V hooks push the counted route over 1.12, or the most-experience line over 1.15, bring the next trim to a decider rather than absorbing it.
- **Orchestrator:**
  - MAPS XD-17 row: "the well 15,000 experience once per character (D-50, D-53)".
  - WORLD_DESIGN Shangri-La row and §5.1: 15,000.
  - The DECISIONS row.
- **A5:** none (the XD-17 map only calls the hook).

**REVERSIBLE:** Yes. It is two values in two source files plus a report line, and it can be undone by regenerating and recounting at any time before Act V's gate.

**SUMMARY ROW:** | D-53 | 2026-11-21 | Act V quest XP (236.5k of 209k, 1.13; 1.19 with every wish as experience) | XD-17's well 20,000 → 15,000 (D-50's trim); Q-D27 experience wish 3,000 → 2,000 per lamp. Counted 231.5k (1.11); all wishes as experience 239.5k (1.15). The gate stays on the counted route; A2 adds a "most experience" line, also ≤ 1.15 | A3 (xd17.yml, q-d27.yml, regenerate), A2 (ledger, balance.py line, recount), orchestrator (MAPS, WORLD_DESIGN) |
