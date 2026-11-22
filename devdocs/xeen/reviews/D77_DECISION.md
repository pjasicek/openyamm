# The Megadragon's experience and later-member stand-ins: decisions (D-77)

Decider D-77, 2026-11-21. I read the following:
- `assets_dev/worlds/xeen/data_tables/monster_data.txt`, all rows of level 60 and above.
- `source/monsters.yml` (dark dragons), `source/map_rows.yml` (D7), `source/quests/q-d26.yml`.
- `tools/xeen/balance.py` (kill XP and `most_experience`), `output/xeen_a2_check/balance_installed_20261121m.md`.
- `briefs/d7/L1/D58_DECISION.md` (Q3, Q8, ROWS, the A2 relay), MONSTERS_AND_ITEMS.md, QUESTS.md (Q-D26), the engine's `assets_dev/engine/data_tables/monster_data.txt`, lane G item 23.
- D-68, D-74, D-75, `tests/playthrough/PLAYBOOK.md` §2.
- `tests/scenarios/xeen/side_quests/README.md` and `run.py`, `tests/playthrough/xeen/promotions/README.md` and `run.py`.
- The scenarios `q-d13_hobstadts_trolls.yml`, `q-d13_hobstadts_trolls_fight.yml`, `q-d17_chalice_of_protection(_voweless).yml` and `q-d25_minotaurs_labyrinth.yml`.
- Promotion segments 25, 51, 55, 63 and 69, and the MM9 promotion segment 94.

## Q1 The Megadragon's experience

**DECISION.** The row is right. Row 11654 keeps EXP **16,875 for the party**: 4,218 each for four members, about 4.2k per member. The "16.9k per member" in D-58 and the notes that copy it is a labelling slip. The figure was the row's party value, written into a per-member column without the division by four. The text is corrected and no data changes.

**WHY.**
- **Every row follows one formula, EXP = L × (L + 10).** In Xeen's rows: 60 gives 4,200; 75 gives 6,375; 100 gives 11,000 (Energy Dragon, hp_x 2); 110 gives 13,200 (Dragon King); 125 gives 16,875. Bosses get no bonus: Lord Xeen 85 gives 8,075 and Morgana 60 gives 4,200, whatever their HP multiplier. A2 applied the formula as designed.
- **MM6–MM8 calibration.** The engine tables use the same formula:
  - MM6's Mega-Dragon (460–462) and the Great Wyrm, both level 100, give 11,000.
  - The highest monster in any MM6–MM8 table, the Ruby Dragon (114, level 125), gives exactly 16,875.
  - At 16,875 the Megadragon already ties the highest experience the merged games pay for any monster. At 67,500 it would be four times anything in MM6–MM8, and the only row in either table off the formula.
- **The slip is visible in D-58 itself.**
  - Its bandit figure is per member: 8 × 3,575 / 4 = 7,150. That is how `balance.py` counts (`sum(most) / 4`).
  - The Megadragon's 16.9k equals the row value with no division.
  - The installed report already shows the per-member figure. Act VI's "Kill XP off the route" is 11.4k (7.15k bandits + 4.22k Megadragon).
- **The budget does not decide this, but it is not affected.**
  - The Megadragon is off the counted route (D-58 D-3), so Act VI stays at 345.4k of 333.0k (1.04) either way.
  - With 67,500 the off-route line would be 24.0k. That is still inside D-53's 1.15, so the reason for keeping 16,875 is the formula and the calibration, not headroom.
- **The reward already sits elsewhere.** Q-D26's payoff is the hoard (Wyrmfang 12530, the top artifact, and the roof key) and the shortcut. Its quest XP is 0, as written. That matches MM6–MM8, where a superboss's reward is its loot, not an inflated kill.

**WHO ACTS.**
- **A2 rows.**
  - No change to row 11654.
  - Correct the wording in `source/map_rows.yml` line 225 to "Megadragon 16.9k for the party (4.2k per member), Sky Bandits 7.15k per member".
  - Correct the 11654 note in `source/monsters.yml` to "its 16,875 for the party (4.2k per member) is in Act VI's most experience".
  - Correct the same in `lanes/A2.md` (the D7 ledger line, about line 467).
- **Orchestrator.**
  - Add a note at the top of `briefs/d7/L1/D58_DECISION.md`: "ROWS and the A2 relay: '+16.9k Megadragon' is party XP; per member 4.2k (D-77)."
  - The D-58 row in DECISIONS.md does not mention the figure and stays as it is.
- **G.** Answer guide item 23 with: "16,875 shared by the party (4,218 each of four) is intended (D-77)."
- **A3-side.**
  - In the side-quest README, close the open item "The Megadragon's experience (A2)" with a pointer to D-77.
  - `q-d26.yml`'s reward note is already correct.

**REVERSIBLE.** Yes. It is one row cell plus text, and the counted route is unaffected.

## Q2 The later-member stand-in in scenarios

**DECISION.** (a) Accept the logged class setup. It is a **test setup**, not a CONVENTION, as D-75 says. Option (b), a scenario-runner recruit step, is rejected for these tests.

The tag has one fixed form, for the side quests and the promotion chain alike:

`log("CLASSES test setup later-member <quest>: member N <before> -> <class> by SetPlayerClass, standing for a <class> recruited after <the hand-in> (D-74 <item>)")`

It is logged just before the `lua_event` `SetPlayerClass`. All other class setups in the promotion chain keep their existing form, `log("CLASSES test setup: <classes>")`: the eligible member for a hand-in in 25, 51, 55 and 67, and the class-table rounds.

A later-member setup is valid only when all of the following hold. Today's five sites (Q-D13 ×2, Q-D17's oath, Q-D25; promotion segments 63 and 69) already meet them.
1. The later path's gate reads only the member's class (`promotable`) plus quest bits that the test itself played.
2. The test first plays the later path with nobody eligible and asserts that refusal or else line. This is the honest-try analogue.
3. The setup changes only the class. It grants no experience, gold, items or bits.
4. The test asserts the unpaid result: experience and gold unchanged, and every member's class.

The report does not list these lines in its CONVENTION section.

**WHY.**
- **The class is the subject under test (D-75).** D-74's later path is a gate on "a member of class X now". Whether that member was recruited or re-classed is invisible to the hook: `Xeen.promotionTarget` reads the current class only.
- **A recruit step would add no coverage.**
  - A runner shortcut for `Party::recruitCharacter` would still create a member of a chosen class by fiat. It is the same setup, with more code.
  - A recruit played through the Adventurer's Inn would test the inn, not the promoter. It would also need Troll, Minotaur and Cavalier roster characters.
  - A fifth member would also change the per-member split of every kill later in the same scenario.
- **MM9's promotion chain and Xeen's class table already use `SetPlayerClass` as a logged test setup**, so one form covers every class stand-in.
- **The tag stays greppable.** "later-member" marks these lines without turning them into CONVENTIONs, which D-68 and D-75 reserve for progress the chain does not play.

**WHO ACTS.**
- **A3-side tests.**
  - In `q-d13_hobstadts_trolls.yml`, `q-d13_hobstadts_trolls_fight.yml`, `q-d17_chalice_of_protection_voweless.yml` and `q-d25_minotaurs_labyrinth.yml`, rewrite each `CONVENTION later-member …` log to the fixed form above. The text after the tag is unchanged.
  - In the README:
    - Change the "Conventions the scenarios use" bullet to "A member recruited after a hand-in is stood in by a logged test setup (`CLASSES test setup later-member`, D-74, D-75, D-77), not a CONVENTION".
    - In the Q-D13, Q-D17 and Q-D25 table cells, "CONVENTION a later …" becomes "test setup: a later …".
  - `run.py` needs no change: it lists only ISSUE, BLOCKER and CONVENTION.
  - Rerun the four scenarios once.
- **A3-promo tests.**
  - Segments 63 (its two Trolls) and 69 (its two later Trolls) log each later-member setup in the fixed form. They keep their `CLASSES at start` and `CLASSES restored` lines.
  - Point README item 3 at D-77.
  - Rerun 63 and 69 once.
- **A1 runner.** Nothing.
- **A3 PLAYBOOK.** In §2, add after the CONVENTION bullets (together with D-75's still-pending prerequisite bullet):

  > "A **test setup** line sets the state a step tests, not progress it skips: a member's class for a promoter (`SetPlayerClass` in a `lua_event`), logged `CLASSES test setup: <classes>`, or `CLASSES test setup later-member <quest>: member N <before> -> <class> …` when it stands for a member recruited after the hand-in. The gate must read only the class and bits the test played. The nobody-eligible line is asserted first, and the unpaid result after. The setup changes nothing but the class. It is not a CONVENTION and is not listed as one (MM9 promotions; Xeen: D-75, D-77)."

**REVERSIBLE.** Yes. Only log text and README wording change. If a played inn recruit is ever wanted, it is a separate inn scenario, not a change to these.

## SUMMARY ROW

| D-77 | 2026-11-21 | Megadragon XP; later-member stand-ins | Row 11654 keeps 16,875 for the party (L×(L+10), equal to MMerge's Ruby Dragon); "16.9k per member" was a slip, so the text is fixed (4.2k per member). Later members: logged `SetPlayerClass` stays a test setup, tagged `CLASSES test setup later-member …`, not a CONVENTION; no recruit step | A2, G, A3-side, A3-promo, A3, orchestrator |
