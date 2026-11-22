# Party health in the playthroughs: decision (D-82)

Decider D-82, 2026-11-21. I read the following:
- `tests/playthrough/PLAYBOOK.md` (all of it), `tests/playthrough/xeen/README.md`, `tests/playthrough/mm9/README.md`.
- `devdocs/xeen/lanes/A3.md` session 30, plus D-68, D-75 and D-77.
- Segments 25, 45, 67, 77, 83 and 95, the logs of 67 and 83 from both runs, and `output/a3_s30/probe/`.
- In the code: `Party::hasActableMember`, `GameMechanics::canAct`, `GameApplication::shouldTriggerPartyDefeat` and `processPendingPartyDefeat`, `ScenarioRuntimeDriver::runPartyDefeat`, and the Immortal guard in `Party.cpp` (`m_debugDamageImmune`).
- For D2: `xeen_d2.scene.yml` (its actors and spawn points), `map_stats.txt` row 9109, `monster_data.txt` rows 11530–11538 and `outdoor_travels.txt`.

## DECISION

**Option (a), with the conditions taken from the game's own defeat rule, plus a check in the runner. Not (b) and not (c).**

1. **The runner fails a step that leaves nobody able to act.**
   - In the real game, a party with no member able to act is defeated: `shouldTriggerPartyDefeat` fires when `!hasActableMember()`.
   - Headless runs never call `processPendingPartyDefeat`; only the `party_defeat` step does. So segments 77–81 played on with a party the real game would already have defeated.
   - After every step except `party_defeat`, the runner fails with: `PARTY DOWN after step N (the game would run its defeat here): member 0 <conditions> | …`.
   - The check is opt-in by tag. It applies to scenarios tagged `playthrough` (the main and promotion chains of Xeen and MM9) or `side_quest`. Ordinary scenarios that test a defeat are not affected.

2. **The main chain checks the party at the end of every segment.**
   - Just before each segment's final `save_game`, no member may be Dead, Eradicated, Petrified, Paralyzed or Unconscious. This is exactly the list `Party::hasActableMember` uses.
   - `run.py` inserts the check into both the normal and the `--reload` copies. It is not written into 52 separate files.
   - The same inserted `play_lua` logs `PARTY <segment> end: [c0] [c1] [c2] [c3]`, and the report gets a PARTY section.

3. **How a failed check is handled.**
   - **Triage comes first (PLAYBOOK §5).** A condition caused by a game bug or a save/load bug is fixed, not cured.
   - **Otherwise the segment does what a player would.** Either it uses `heal_at_temple: {house, min: 0}` at the first temple on its route after the cause, or it fights the cause first, as 77 and 95 now do. Placing the party next to a temple is allowed outdoors and in towns (§2).
   - **A temple visit is not a CONVENTION.** It is the game's own service at its own price, and its HEAL lines are the record.
   - **Segments that end indoors** (05, 73, 87–93, 98, 99) cure with what the party carries, or walk out. A condition never carries into the next segment unchecked.
   - **The checks already inside 77 and 95 stay.** They name the place where the damage happened.

4. **Lesser conditions are logged, not asserted.** These are Weak, Diseased, Poisoned, Cursed, Afraid, Insane, Drunk and Asleep.
   - Some steps depend on a member's statistics or turn: D-68's honest tries, Slick's games, stat gates, class rounds.
   - Such a step cures first and asserts that the members it uses are clear, as 25, 45 and 83 already do.

5. **The promotion chain follows the same rules as the main chain (points 2–4), in `promotions/run.py`.**
   - Its branch points are main-chain checkpoints, and point 2 makes those clean.
   - Its own segments fight (61, 63, 67, 69 and others), and its hand-ins and class rounds read individual members.
   - A hand-in or class round whose result depends on particular members first asserts that those members can act.

6. **Side-quest scenarios** get the runner check (point 1), but no end check and no cure at the end, because nothing continues from them.
   - Each scenario's report logs the conditions at its end.
   - A step that reads one member (an honest try, a D-77 later-member test setup, a stat gate) first asserts that member can act.
   - A side-quest scenario that saves a checkpoint for another test to load gets the end check from point 2.

7. **The D2 Petrify is not a map fault on the present evidence, so nothing goes to A6.**
   - **Where segment 67 is on D2:**
     - It arrives on D2's east edge from D3 (`outdoor_travels`: D2's right-hand neighbour is D3). Both D2 reloads in the reload copy happen there, at steps 19 and 21.
     - It is then placed at (-22016, 2048). After 1.4 s the walk opens the Castleview Vale prompt at x -23106, so step 25's reload is skipped.
     - **No reload ever happens on the west edge.**
   - **East side (x > 12,000):** five placed Ogres, and 12 spawn points of slot 1 (Xeen Wolf). No monster there turns members to stone or paralyses them.
   - **West pose:** no placed actor within 6,000.
     - The nearest spawn point is at (-21056, -2720), 4,860 away. It is slot 3, Xeen Dark Sprite: Gorgon Sprite 11534 (Stone) and Elder Gorgon Sprite 11535 (Curse).
     - Three more such spawn points lie 7,000–8,700 to the south.
     - The placed Medusa Sprites (11537 Stone ×5) and Killer Sprites (11538 ×3) are by the Temple of Bark, about 15,000 away.
   - A Dark Sprite group 4.9k inside Sprite Forest's edge is the map's intended encounter, at normal MM6–MM8 spacing.
   - **It appeared in both reload runs and in neither normal run.** Under PLAYBOOK §4.4 that makes it a save/load suspect until shown otherwise.
   - **A3 bisects it:**
     - Log conditions at the end of 65 and after every step of 67's reload copy, and name the step and the attacker.
     - Record the results of the probes already started (`output/a3_s30/probe/saveload.yml`, `firstload.yml`).
     - If a load caused it (a spawn group re-rolled or moved on load, lost AI state, a condition restored wrongly), it goes to A1.
     - It goes to A6 only if a placed petrifier turns out to sit at an arrival point the map itself defines.

## WHY

- **PLAYBOOK §1:** the chain proves the story can be finished *with the game's own rules*.
  - A party the game would have defeated has not finished by those rules.
  - The game's defeat rule counts Petrified, Paralyzed and Eradicated alike as "cannot act". Option (b) would split a list the game treats as one.
- **The evidence shows (b) would have let the next 77 through.** Segment 83's "before the shrine" lines:
  - Normal run: members 1 and 3 Paralyzed.
  - Reload run: member 0 Petrified, members 1 and 3 Paralyzed.
  - So in the reload run, member 2 (Cursed, Weak) carried segments 67–81 alone. One more Stone hit and the real game would have defeated the party, which is the same failure 77 had.
- **Immortal only blocks HP loss.** `m_debugDamageImmune` guards `health`, not special-attack conditions.
  - Under the harness's rules, Stone, Paralysis, Eradication and Death are the only ways the party can be harmed.
  - They do not wear off: only a spell, a potion or a temple cures them.
  - This is not combat balance. It is state the story carries forward, and the promotion chain inherits it.
- **The cost is small.**
  - `heal_at_temple` exists and is already used in 25, 45 and 83.
  - With `min: 0` it does nothing when nobody needs healing, so one step serves both runs even though their random draws differ (§4.4).
  - The rules allow placing the party next to a temple, and the party holds more than 80k gold from Act IV on.
- **Option (c) is what hid 77–81 for five segments.**
- **Lesser conditions leave members able to act.** Asserting them would add a temple trip to almost every segment for conditions a player happily walks around with. Where they matter, cures already happen before the step.
- **MM9 already ran into this.** Its days-awake pitfall carried Dead members at 1 HP through Chapter II unnoticed. The PLAYBOOK's advice ("check `conditions(i)` before combat, heal at a temple") becomes a rule here instead of a pitfall.
- **Point 1 is a runner gap by PLAYBOOK §5.2:** work the game's frame does and the headless frame did not.

## WHO ACTS

- **A1 (runner):**
  - Add point 1's check to `ScenarioRunner`: opt-in by the tags `playthrough` and `side_quest`, every step except `party_defeat`.
  - Document it in `tests/scenarios/README.md` and PLAYBOOK §3.
  - After the runner change, run the release scenario list, the Xeen chains and MM9's main chain once.
  - A1 later gets the D2 case too, if A3's bisect shows a load cause.
- **A3 (main chain):**
  - Add point 2's insert and the PARTY report section to `tests/playthrough/xeen/run.py`, and tell A1, who keeps that file.
  - Add this bullet to PLAYBOOK §2:

    > "**The party ends every segment able to act**: no member Dead, Eradicated, Petrified, Paralyzed or Unconscious (the game's own defeat list, `Party::hasActableMember`); `run.py` checks it before each segment's save and logs every member's conditions. The Immortal cheat stops HP loss, not conditions. A member who is down is cured as a player would, at a temple on the route (`heal_at_temple: {house, min: 0}`), or the cause is fought; neither is a CONVENTION. Lesser conditions (Weak, Diseased, Cursed …) are logged; a step that depends on a member's statistics cures first. A step that leaves nobody able to act fails (the game would run its defeat) (Xeen: D-82)."

  - Replace the README's "Members' conditions are not cured" bullet with this rule.
  - Run the whole chain, normal and `--reload`. Triage each failed check, then cure or fight as in point 3.
  - Bisect 67's reload run as in point 7.
- **A3-promo:**
  - Add the same insert and report section to `promotions/run.py`.
  - Add the per-member asserts from point 5.
  - Rerun the chain from the main chain's new checkpoints.
- **A3-side:**
  - Log each scenario's end conditions in the side-quest report.
  - Add the per-member asserts from point 6, plus the end check for any scenario that saves a checkpoint for another test.
- **A6:** nothing, unless the bisect finds a petrifier at an arrival point the map defines.

## REVERSIBLE

Yes. Everything here can be undone:
- an insert in each `run.py`;
- an opt-in runner check;
- temple steps that do nothing when nobody is down.

## SUMMARY ROW

Party health: runner fails a playthrough or side-quest step leaving nobody able to act; main and promotion chains assert no member Dead, Eradicated, Petrified, Paralyzed or Unconscious at segment ends (temple cures); lesser conditions logged; D2: no map fault.
