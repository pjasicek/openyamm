# Playthrough stat gates and DD-26's reach step: decisions (D-68)

Decider D-68, 2026-11-21. I read the following:
- `tests/playthrough/PLAYBOOK.md` (§1 and §2).
- `tests/playthrough/xeen/run.py`, plus the party in `01_vertigo.yml` and segment 83's carnival block.
- The MM9 chain's README and segments 01, 51 and 56, and its promotions README.
- `devdocs/xeen/lanes/A3.md` (session 25, Waiting, Next), and A2's permanent-stat ledger in `lanes/A2.md`.
- `reviews/D59_DECISION.md`, `reviews/COMBAT_AND_PROGRESSION.md` and `source/quests/m34.yml`.
- D-67 item 7, `briefs/dd26/L4/NOTES.md` and `briefs/dd26/L4/playtest_hostility.yml`.

## Q1: How the main-story chain passes stat gates

**DECISION: (B), reworked as a convention. It is not a BLOCKER. (C) is rejected.**

1. **The chain does not grow its party.** Option (A) is rejected for the chain.
   - Training changes nothing at these gates: on MM6–MM8 rules a level-up adds skill points, not statistics.
   - Every permanent stat source in A2's ledger is a side visit (juices, wells, books, thrones, skulls). A main-line chain that collected them would become a side-quest chain.

2. **The convention step has a fixed shape.** Segment 83's +45 to base stats is replaced with this:
   - **The honest try comes first.** The segment first plays each booth with the party as it is, as it already does: the strongest member plays, and a lost game is tried by every member.
   - **Only the shortfall is given, and only to the member who plays.** If every member loses a game, that member's statistic for that game is raised to exactly the gate's number (60). It is raised as a temporary bonus until rest, by the same `AddValue` the world's wells use (for example `q-f1.well`).
   - **Base statistics are not touched.** So nothing carries over to later gates (FD-02's Might 60, Q-F1's balls), and each later gate has to pass or log its own convention.
   - **Gems:** only the shortfall to the booth's fee is granted (today 15 needed, 5 held).
   - **One log line per grant**, of the form `log("CONVENTION stat-gate M34 <stat>: member N <before> -> 60; gems <before> -> <after>")`.
   - If the party later gets strong enough (a better party creation, or stat sources), the step stops firing by itself. No edit is needed then.

3. **Logging uses a new tag, `CONVENTION`.**
   - Under PLAYBOOK §2, BLOCKER means a game problem the run can only pass with a cheat. Nothing in the game is broken here: the chain deliberately skips optional progress (stat sources, loot, gear).
   - PLAYBOOK §2 gains one rule: a `CONVENTION` line is a logged stand-in for progress the chain does not play. It may only make up a shortfall, and only after an honest try. A clean run may contain CONVENTION lines, but never BLOCKER or ISSUE lines.
   - The report lists CONVENTION lines in their own section.
   - Segment 83 keeps its real **BLOCKER A8** (the cloud stair) and its **ISSUE A1** (the wield step).

4. **The Q-F1 crystal balls need no chain convention.**
   - D-59 says failing a ball costs nothing on the path, so they are not a story gate.
   - `hooks_x9_dragon_clouds` already proves both outcomes, using the well.

5. **A separate check must prove the gates can be reached by normal play. Owner: A2.**
   - `tools/xeen/balance.py` gains a **stat-gate table**. It lists every `IsAtLeast(Actual<Stat>, n)` gate in the quest files, plus DD-21's pry at Might 30 and FD-02's Might 60. For each gate, the best-suited member's value is the sum of:
     - their best creation value for that statistic;
     - the ledger's counted-route permanent sources before the gate;
     - the fixed temporary help reachable before the gate without a rest, each source named (for example D5's Shrine of Great Power +15, D5's Fountain of Might +20, the event-given Might Boosts +30).
   - Random items and spells are left out of that sum.
   - **Pass rule (D-59's standard):** fixed sources reach the number, or fall short by at most 10, which one item or one buff can cover.
   - A gate that fails goes back to the deciders as a world change (another source, or a different number). It is never changed for the chain's sake.
   - **Gem budget:** the fixed gem sources on the route before each required payment must cover it. M34's 15 is required; Scaldrith's 20 and the scarabs are optional.
   - **My own rough count from the ledger, for A2 to confirm:** by M34, Might and Endurance land near 50–55, Speed near 40–45 and Accuracy near 35–45 before temporary help. **Accuracy is the gate at risk.**

**WHY:**
- PLAYBOOK §1 says the chain proves the story can be finished, and does not test combat or balance. Whether a gate can be reached is a balance fact, so it belongs in A2's balance check, which can cover every gate and every act at once.
- Giving only the shortfall, as a temporary bonus and only after the honest try, means the convention never hides a game bug, never inflates later gates, and disappears when the party earns the statistic.
- Lowering the numbers (C) would change the game for players to suit a test harness.
- The MM9 precedent supports this:
  - MM9's party plays chance gates as it is (the bell by Might).
  - MM9 has no hard statistic gate, so it never needed a grant.
  - Xeen's gates are hard thresholds that a creation-stat party cannot reach by retrying.

**WHO ACTS:**
- **A3:**
  - Change segment 83 as in point 2.
  - Add the CONVENTION section to `tests/playthrough/xeen/run.py`'s report.
  - Add the §2 rule to `tests/playthrough/PLAYBOOK.md`.
  - Rerun 83 twice and once with `--reload`, then 85 from 83's new checkpoint.
  - Mark item 2 of A3's "Next" list done. Later gates on the main path (FD-02, if it is on it) use the same form.
- **A2:**
  - Add the stat-gate and gem-budget tables to `balance.py`.
  - Report the first result. Any gate outside the pass rule is raised as a DECIDE.

**REVERSIBLE:** Yes.
- The convention is a few guarded steps that switch themselves off.
- The check only reports. A gate it fails is decided separately.

## Q2: DD-26's elemental reach step

**DECISION: Confirm the step with the Water Elemental 11710 and its normal shooting AI, but tighten it. As written, it does not prove what D-67 asked.**

1. **The goal changes from "melee range" to "its attack range, out on the cistern's walkway".**
   - D-67's real aim is that a body capped at radius 60 and 202 high gets through the lowest opening on the walking line: the culvert mouth, 320 high.
   - The cistern's walkways are 320 wide under a vault of 768, so they cannot bind once the mouth is passed. Melee range adds nothing.

2. **Today's asserts can pass with the elemental still in the mouth.**
   - The party stands at (1280, 2144), only about 900 from the east culvert's mouth at about (2176, 2240).
   - An elemental that stops about 750 off to shoot can therefore be standing in the mouth itself, and it still meets "within 900".
   - The second assert (within 2050 of (0, 2496)) proves even less.

3. **The changed step:**
   - Keep the spawn at (2080, 320), and keep the party being seen at the mouth for 3 s.
   - Then move the party out of sight onto the cistern's south walkway, about 2,000 west of the mouth (for example (0, 2144)). The elemental must then come through the mouth and walk at least 1,000 along the walkway before it can shoot.
   - Advance 45–60 s instead of 30.
   - Assert, on actor 20:
     - `hidden: false`;
     - `near` the party, within 900;
     - `far` from the mouth (2176, 2240), at least 1,000.
   - If the AI trace has a stuck or no-path event, also assert `ai_trace` `max_count: 0` for it.
   - Drop the (0, 2496) assert.
   - Going round the basin to the north walkway is not needed.

**WHY:**
- The step has to prove the one binding number named in the NOTES (the 320 opening) on the body that binds (11710).
- Forcing melee would mean a different monster or a changed AI, which is not what the test is for.
- A `far` assert from the mouth, with the party out of range of the mouth, rules out an elemental standing in the mouth and shooting.

**WHO ACTS:**
- **A8:**
  - Make the change in `briefs/dd26/L4/playtest_hostility.yml` (the playtests are written by hand) and in the notes inside it.
  - Change the NOTES' Playtests row and its "Walking room" paragraph to say "through the culvert mouth (320) and at least 1,000 along the cistern's walkway".
  - Rerun 4 of 4 from assets_dev.
- If the elemental sticks, that is a geometry finding to fix in gen.py, as the outfall recess was. It is not a reason to loosen the assert.

**REVERSIBLE:** Yes. This is one test's poses and asserts.

## SUMMARY ROW

| D-68 | 2026-11-21 | Chain stat gates; DD-26 reach step | Chain: after an honest try, the playing member gets only the shortfall to the gate (temporary bonus) and gems; logged CONVENTION, not BLOCKER; never lower the gates. A2's balance.py proves reachability (stat gates, gem budget). DD-26: 11710 keeps shooting; party 2,000 from the culvert mouth, asserts ≤900 from the party, ≥1,000 from the mouth. Detail: `reviews/D68_DECISION.md` | A3, A2, A8 |
