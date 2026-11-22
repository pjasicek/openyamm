# D-87: D-85 follow-ups — givers in a fight, edge-arrival leeway (2026-11-21, fourth orchestrator's decider)

**D-87: givers standing in a fight, and how much room edge arrivals need**

**1. X5 Mayor Randon (4502): DECISION (a), keep him in the haunted square, with one protection.**
- WHY:
  - **Are the ghosts hostile at once?** Yes. The Spirit Bones (11241, group 40) are hostile and aggressive from load, 456–1,000 from him, and engage within seconds. The Polter-Fools and Ghost Riders appear on his word at the 16 wave spots round the square.
  - **Are they a ranged threat?** No. All three kinds are melee only: no missile and no spell. Their "Age" effect comes only from melee hits, so nothing can stone, curse or paralyse a party from range here. That ranged danger is what D-85 was written for.
  - **Can the party talk to him on arrival?** Yes. Only Town Portal and resting refuse when hostiles are near; dialogue does not check. The Q-C6 test confirms there are at least 6 hostile Bones, then opens his dialogue (with the party made immortal).
  - **This is his quest.** His first line is "The town is currently haunted by Spirit Bones", and the loop of signboard, gong and Randon is the square's set piece.
  - **Moving him (b) would not help.** The wave spots run across the whole town, 456–5,235 from him, so no doorway in Winterkill is 5,888 from them.
  - **The real risk is the party's own spells.** In Standard rules the party's hits and splash damage hurt peaceful actors (`CombatRules::harmsFriendlyActors()` returns true). Randon has 3 HP, so one stray Fireball kills him. That softlocks Q-C6, and Winterkill's houses only open when it is done.
- WHO ACTS: A6.
  - Make actor 120 unable to take damage, the way D-51 protects Corak. Write it through `x5/tools/gen.py`: either the actor's `mm9_can_receive_damage: false`, or `evt.SetMm9ActorCanReceiveDamage(120, false)` in the load event. That check runs before the code that turns a hit NPC and its kin hostile.
  - Add steps to the Q-C6 test or X5's playtest: on a fresh load with the wave alive and nothing cleared, a party hit or area spell on Randon leaves his HP unchanged and he stays peaceful. After 20 s Randon is alive and his dialogue opens.
  - Add one line to the L4 NOTES. The square's arrival (`start` / `winterkill_square`, 544 away) is covered by the same reasoning: melee wave, the town's quest.
- REVERSIBLE: yes, one actor flag.

**2. D2 Graalg (5108): DECISION (a), keep the fire where it is.**
- WHY:
  - D-23 put the parley fire between the forts on purpose. Graalg and his Brutes are their own faction, peaceful until `q-d11.hostile`, and fights with the pass ogres do not turn them hostile.
  - The fort ogres' only ranged attack is a 20 % rock throw (Phys 2D6+5, no condition). The Chiefs' Uncon is melee. So the party gets an ordinary fight, not a ranged condition wipe.
  - (b) would undo D-23's "hostile at load" and Kramer's premise. It would also need a separate faction for the garrisons, because hitting a road-group ogre alerts its kin.
  - (c) cannot work inside the pass: the forts are about 8,800 apart, so no spot in the saddle is 5,888 from both. Moving the fire out would throw away a built set piece.
  - The party's spells can still hit Graalg and close the peace route. That is the normal Might and Magic consequence, and the war route stays open, so nothing softlocks. No protection is added.
- WHO ACTS: A6.
  - New test `playtest_graalg_parley.yml`: fresh load, a level-24 party posed at the fire, nothing cleared. No member gains a condition in the first 5 s; actor 22's dialogue opens.
  - Add one line to the D2 NOTES.
- REVERSIBLE: yes.

**3. Edge-arrival leeway: DECISION, keep D-15's band and add a rule by threat.**
- The rule: a **ranged disabler** must be at least 5,888 from every outdoor arrival point (edges, a new game's start, falls, dungeon exits, mirrors and Town Portal points, docks and coaches) and from every talking giver.
  - A ranged disabler is a monster with Stone, Curse, Paralyze, Asleep, Insane, Afraid, Uncon, Dead or Errad on an attack that has a missile, or one with a Paralyze or Finger of Death spell.
  - A spawn marker counts if any monster its slot can roll qualifies. This covers the Xeen Sprite, Dark Sprite and Eye slots, Wicked and Head Witches, Liches, Octopods, Ninja and Clan Masters, the Clan King, Autobots and Sandro.
  - Every other kind keeps D-15's 2,000–6,000 band at edges and the start, and the town buffer elsewhere.
- WHY:
  - Every harm we have seen was ranged Stone or Curse from sprites. A melee group at 2,000 or more has to walk to the party in plain view.
  - The five edges you listed all hold melee kinds, so none moves: X5 north (Barbarians A–C), X5 east (Dark Wolves), D1 north (Gremlins A–C), D1 east (Gremlin Guards, Afraid on melee only) and D5 west (Vulture Roc, Roc and Griffin, Paralyze on melee only).
- WHO ACTS:
  - A5 on X1–X4, X6, X7, X9 and D3; A6 on X5, X8, D1, D2 and D4–D7. Each adds this kind filter to `check_d85.py` / `d85.py` and measures every arrival point.
  - Any ranged disabler inside 5,888 is moved by a small marker move with no decider. Counts, slots and pack sizes stay the same; rebuild with bake and run the tests.
  - If a move would break a set piece, report it as DECIDE.
  - Likely hits are D6's dungeon exits (its slot 1 is Xeen Eye: Floating Eye has Paralyze on a missile) and any Sprite or Dark Sprite marker near a dungeon exit.
- REVERSIBLE: yes.

**4. X6 Arie: DECISION, keep both markers where they are.**
- WHY: spawns 33 (5,258) and 20 (5,621) are Basenji-heights werewolves. They are melee only (their Disease comes from melee hits) and stand on the heights at floor height 2,300–2,750, above her camp. The 768 leeway exists for monsters that shoot.
- The same answer applies to every other warning in the 5,120–5,888 band: X5's druid (Sabertooths), D1's Joe, Justine, Luna and Yog, D4's Leafpoint (her witches cast Lightning Bolt and Psychic Shock, which do damage but cause no condition) and D6's Ambrose (griffin). None is a ranged disabler, so all stay as warnings. Under the rule in 3, a warning moves only if it is one.
- WHO ACTS: A5 records "kept by D-87" in X6's NOTES; A6 does the same in its NOTES.
- REVERSIBLE: yes.

**SUMMARY ROW**

| D-87 | 2026-11-21 | D-85 follow-ups: givers in a fight, edge-arrival leeway | Randon stays in Q-C6's square (melee-only waves; he is made undamageable as Corak in D-51, with a test) and Graalg stays at D-23's parley fire (rocks carry no condition; new parley test). D-15's band stays for edge arrivals, but no ranged disabler (Stone, Curse, Paralyze, Asleep, Insane, Afraid, Uncon, Dead or Errad by missile or spell) may stand within 5,888 of any outdoor arrival point or talking giver; X6 Arie's werewolves and every other 5,120–5,888 warning of melee or damage-only kinds stay. | A6 (X5 Randon flag and test, D2 parley test, arrival measure on X5/X8/D1/D2/D4–D7), A5 (arrival measure on X1–X4/X6/X7/X9/D3, X6 NOTES) |
