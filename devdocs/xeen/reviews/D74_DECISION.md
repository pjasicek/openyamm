# Promoting later members: decision (D-74)

**Question (A3-promo).** Should every tier-2 and racial promoter also promote party members who reach the eligible class after the quest was handed in, unpaid? Can such a topic let a member cross from Light to Dark? Can a later member of the right tier-1 class pick either path's promoter? Should Q-D23's ritual text name Necromancers?

## 1. Every promoter keeps a later-members path, unpaid

**DECISION.** Yes. Every tier-1, tier-2 and racial promoter keeps a topic or hook that promotes members eligible now. It pays nothing: no experience, gold or items. Each quest pays once, on the hand-in that completes it, whoever that promotes. T2-A, T2-LEAFPOINT and T2-CLAN already work this way: they pay on the first promotion they make and are unpaid after. `t2-later.yml` stays as written, and its eight gates are right:
- Dreyfus: `q-d6.done`
- Sharla: `q-d10.done` + `polite`
- Luna: `q-d20.done`
- Astra: `q-d14.done`
- Nasir: `q-d18.archmage`
- Kramer: `q-d11.bounty_paid`
- Reger: `q-d3.done`
- Master Thief: `inner_circle`, not `master_slain`

**WHY.** QUESTS §3 is MM9's composite model, and MM9 keeps "Promote our eligible characters." at every promoter. The T1 files, Dimitri, Q-C4, Q-C7, Q-C17, Q-C25, Q-D17 (`oath_again`) and Q-D25 (`throne_again`) already do the same. Without it, a member recruited or promoted after a hand-in can never be promoted: there is no other source of the class, so this is a dead end, not a choice. D-16 says the class change is the reward, so a second payment would only inflate the act budgets.

**WHO ACTS.**
- A3-promo: keep `t2-later.yml`. In its header, replace "requests to their quests' owners" with "see D-74". In the README's "Promoters with no later path" bullet, replace the request with a pointer to D-74. Once points 3 to 5 are done, add the troll, coven and sandro rows to `class_table.py`.
- A3 main: nothing. M4 is the only m-file that promotes, and T1-A already covers it.

**REVERSIBLE.** Yes: delete `t2-later.yml`.

## 2. Light/Dark: no crossing, and later members may pick either path

**DECISION.**
- **No crossing.** `Xeen.promotionTarget` matches a member's current class only. Every key of a tier-2 or racial row is a step-1 class in `class_extra.txt` (Necromancer is step 1 too), so a promoted member matches no other promoter, whether at a hand-in or a later topic. A3-promo adds that invariant as an assertion to `class_table.py`: no "from" class of a tier-2 or racial row may be a step-2 class. It guards the rule until engine O2 lands, and after.
- **Either path.** A later member of the right tier-1 class may use any promoter whose quest the party finished on the route that keeps that promoter. A later Cavalier can go to Dimitri, or to the Voweless plaque if the oath was sworn.
- **Closed routes stay closed.** No later path is made for a route the party closed in the world:
  - Sharla paid on the mercenary route
  - the Chalice given to Bosco
  - the Master Thief slain
  - the coven broken before joining, or after it
- **O2.** When O2 lands, its per-member choice or check goes into `Xeen.promotionTarget` / `Xeen.promote`. Every hand-in and later topic already calls those, so no quest file changes. Until then, later topics are opt-in by nature: a member waiting for the other path simply does not ask.

**WHY.** QUESTS §3 says "the party may promote different members on different paths". That needs both promoters to remain where the world allows it. The exclusivity is per character and comes from the class, not from the party. A world route the party chose (gave the Chalice away, broke the coven) is a real consequence, and the other path of each line stays open.

**WHO ACTS.**
- A3-promo: the invariant assertion.
- A3-promo also fixes the `seasons` comment in `xeen_common.lua`. It says Q-C1; it should say Q-C10 (D-1).

**REVERSIBLE.** Yes. The assertion is test-only, and the rule changes no data.

## 3. Q-D13 (Troll → War Troll): no change to DD-11C

**DECISION.**
- **Hobstadt's "Sacrifice one" (A3-side).** Change `show` to `{not: {qbit: hostile}}`. Add a first state for `{all: [{qbit: trial}, {promotable: troll}]}` that promotes, unpaid, for example: "Another troll? Hobstadt take him too. One night. (Morning.) War Troll. Hobstadt has two friends now." Add a second state for `{qbit: trial}` with no promotion, for example: "Hobstadt has his War Troll. Go where you like." Keep the existing promotable and no-troll states. The tribute route already reaches the existing state.
- **The vacant throne (A3-side).** Drop `once: true` from `q-d13.throne`. Its `requires` (`hobstadt_slain` + `Xeen.canPromote("troll")`) already limits it to eligible Trolls, and its fail line "The throne is vacant." covers everyone else.
- **DD-11C (A8).** The throne event already calls `q-d13.throne` whenever `hobstadt_slain` is set, so the map needs no rebuild.
- **Fallback.** If `quests.py` requires `once` on a hook that `sets`, use the Q-D25 pattern instead: a `throne_again` hook, and A8 adds `if not hook("q-d13.throne") then hook("q-d13.throne_again")` to DD-11C's `evt:throne`.

**WHY.** Today, once a Troll is promoted (`trial`, or the throne's `once`), no later Troll can be. Hobstadt alive and friendly, or his empty throne, is the natural promoter for both of Q-D13's endings.

**WHO ACTS.** A3-side (`q-d13.yml`). A8 only for the fallback.

**REVERSIBLE.** Yes: restore `once` and the topic's `show`.

## 4. Q-D22 (Great Druid → Warlock): no change to DD-20

**DECISION.** Rewrite `q-d22.initiation` as a states hook without `once`.
- Keep its `requires`: `riddle_answered`, not `head_witch_slain`.
- Move `sets: [joined]` into the joining state's `do`.
- First state, joined and eligible: `{all: [{qbit: joined}, {promotable: coven}]}`, with `{promote: coven}` and a line such as: "Another of the green ways drinks. The witches clap, politely. Warlock."
- Second state, `{qbit: joined}`: today's else line, "You have had some. It is still toad."
- Last state: today's joining text, with `do: [{set: joined}, {promote: coven}]`.
- DD-20's event 39 already asks "Drink?" and calls this hook, so the map needs no rebuild. If `quests.py` objects, use `initiation_again` and A8 adds one call in DD-20.
- After the Head Witch dies, the cauldron stays cold: the existing fail line. Leafpoint (Light) is still open.

**WHY.** Today a party that joined with no Great Druid, or recruits one later, can never get Warlock while the coven still stands. Breaking the coven is the party's own route choice, so the path stays closed after it (point 2).

**WHO ACTS.** A3-side (`q-d22.yml`). A8 only for the fallback.

**REVERSIBLE.** Yes: restore the `once` hook.

## 5. Q-D23 (Priest of Dark, Lich): the later path is Master Morbius, not DD-21

**DECISION.** No later-members hook in DD-21. The ritual and the release run in one prompt sequence, and the release hides Sandro for good, so a `ritual_again` hook would have no one to talk to. Instead, Master Morbius (5506, D6) gets the later path in `q-d23.yml`. His topic "Sandro" becomes states:
- Released and eligible: `{all: [{qbit: released}, {promotable: sandro}]}` promotes, unpaid, for example: "Sandro is at rest, and he left the House his notes: everything but the heart. A Priest, a Wizard or a Necromancer who wants to walk where he walked: sit. This takes an evening."
- Released: `{qbit: released}`, for example: "Sandro is at rest. The House has his notes, if one of yours ever wants them."
- Otherwise: today's line, with Necromancers added (below).

The gate is `released`, not `taught`. Both endings release Sandro, and the ritual prompt is offered only while someone is eligible (DD-21 tests `XeenQuests.can("q-d23.ritual")`). Gating on `taught` would permanently close Priest of Dark and Lich for any party that had no Priest or Wizard at that moment, and the player would never have been shown the choice. Declining the ritual grants no Light promotion, so opening Morbius after release crosses nothing. The Light paths for these classes are Q-D6 and Q-D18.

**WHY.** This is the only working later path, it needs no map work, and `class_table.py` can test it like any other NPC promoter.

**WHO ACTS.** A3-side (`q-d23.yml`). A8: nothing in DD-21.

**REVERSIBLE.** Yes: revert Morbius's topic.

## 6. Necromancers are named in Q-D23's texts

**DECISION.** Yes.
- **The ritual hook.** "The Priests among you rise as Priests of Dark, the Wizards and Necromancers as Liches."
- **Morbius's line.** "A Priest, a Wizard or a Necromancer who asked him nicely, before the end, might learn how it was done."
- **The table.** Keep `Necromancer = "Lich"` in `Xeen.Promotions.sandro`. It is MMerge class 44, step 1 → 45, step 2. QUESTS §3 already gives the line to Sandro, and the Standard ruleset offers Human Necromancers.
- **Out of scope.** Necromancers get their only promotion in Act V, at about level 45, later than any other line. If playtests find that too late, it is a separate question; D-74 does not decide it.

**WHY.** Every promoter text names the classes it promotes. A Necromancer turning into a Lich under a text that names only Priests and Wizards would read as a bug. Morbius runs the Necromancers' House, so the mention fits the setting in any ruleset.

**WHO ACTS.** A3-side (texts in `q-d23.yml`). A3-promo (keep the table row, and add a Necromancer to the sandro row's class-table round).

**REVERSIBLE.** Yes: text only.

## SUMMARY ROW

| D-74 | 2026-11-21 | Promoting later members | Every promoter keeps an unpaid later path; keep `t2-later.yml`. No crossing (tier-2 keys are step-1 classes; `class_table.py` asserts it). Later members may use either surviving promoter; closed routes stay closed. Q-D13 topic state and throne without `once`; Q-D22 cauldron states; Q-D23 via Morbius after `released`, no DD-21 hook; Necromancers named | A3-promo, A3-side; A8 only for fallbacks |
