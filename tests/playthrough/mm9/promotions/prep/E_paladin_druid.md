# Prep: block E, segments 70-84 (the Paladin's Three Crusades, the Druid's Green Man)

Research for `70_*.yml` .. `84_*.yml` (2026-11-08). Sources: the map scripts
(`assets_dev/worlds/mm9/events/maps/{lindisfarnemonastery,thjorgardcity,thearena,sturmfordcity,frosgardcity,frosgard}.lua`),
the RUDE files (`assets_dev/worlds/mm9/dialogue/rude/NPC*.rude`), the scenes, `dialogue/promotions.yml`, the
original scripts (`mm9/extracted/SCRIPTS/SCRIPTS/NPC3.scr`, `NPC180.scr`, `NPC48.scr`, `NPC245.scr`,
`NPC416.scr`, `SVENARENA.scr`). Keys: `MM9.hasKey(K)` = qbit 90000+K. Items: engine id 10000 + the raw MM9 id.

## Why block E is its own branch (after Krohn)

From the war council (key 40) until Krohn's task (key 108), every Jarl is away. The relevant lines are
`thjorgardcity.lua:252` `show(50, not has(40) or has(108))` (Sven) and `frosgardcity.lua:320` `show(5, has(108) or not
(has(104) or has(40)))` (Tryygva). MM9 does the same: NPC3.scr and NPC180.scr `:Init` call `haskey 40 -> Vanish` and
`haskey 108 -> unvanish`. The Thronheim council copies show only from keys 90 and 91 until key 94 (Bikki's prize), and
key 94 is already set in Chapter II. A probe from `00_start.oysav` (Chapter II): `interact_actor 50` in Thjorgard City
fails with "actor activation failed".

- **Paladin**: blocked at Sven's first line, "We have found a disturbing letter" (RUDE 3, row 3.11). Without it there
  is no key 230, so Byri is not in the Arena, so there is no 231, so Harris says nothing, so there are no keys 232,
  234 or 235. Grehgknak's "We have completed our Crusades." needs 235.
- **Druid**: blocked at Tryygva's runestone (key 278, row 32.1 of RUDE 180). The Green Man's report needs 278.

The two Jarls are reachable in these windows:

| Jarl | When | Where | Notes |
| --- | --- | --- | --- |
| Sven | Chapter I (before key 40) | Thjorgard City | |
| Sven | keys 102-104 (Chapter IV) | Arslegard City | Its exit hook also pays 234 -> 235. |
| Sven | Chapter III | the Afterworld | His ghost has RUDE 3 rows but no exit hook, so no 235. |
| Sven | after key 108 | Thjorgard City | |
| Tryygva | Chapter I | Frosgard City | |
| Tryygva | Chapter III | the Afterworld | RUDE 180 there; key 278 comes from the row itself. |
| Tryygva | after key 108 | Frosgard City | |

The coordinator's decision: no cheat. Block E starts from `checkpoints/00_after_krohn.oysav`, a copy of the main run's
`60_krohn.oysav` (Hall of the Gods, key 108 set). The guide's "requires" for both quests should say that the Jarls are
away from the war council until Krohn's task.

On 2026-11-08 the main run's 60 has the user's old two-member party (Lich, Priest) and 0 gold. The segments assert
"unchanged from before", not class names. Rewards are checked as gains: `gold()`, `experience(i)`, and
`remember`/`recall`.

## The Paladin (RUDE 282, Grehgknak the Right; done key 237)

- **Lindisfarne Monastery** (a walked map). The way in is the region's ExitTrigger0 at (-11749, -21240, 2734); the
  party arrives at (-327, -935). The route:
  1. Walk to (-330, 1000). Doors 1 and 2 are clicked open with event 101.
  2. Walk along the nave's east side, x 150. The monk Bred Gagii (actor 7) wanders the middle of the nave and pinned
     the party at (-113, 4149) in a reload run.
  3. Walk to (-100, 5600). Doors 3 and 4 are clicked open with event 102.
  4. Walk through the crossing to (-100, 6700), (600, 6700) and (2350, 6390).
  5. Click the east transept's door (event 105, door 37) and walk to (3000, 6390).
  6. Walk with the planner to Grehgknak (actor 1) at (3837, 5200, -40), south of the east wing.
  7. To leave, walk back the same way to the narthex's ExitTrigger0 at (-328, -1393).

  Hurting a monk sets `MonksHostile` (asserted 0). No `clear_hostiles` here.
- **His talk.** The lines, in order: "Do you have any interesting tasks for a party of adventurers?" (key 2080),
  "Yes. Please tell us what you have for us." (requires key 137, the Crusader promotion; waived), "Tell us of the
  Three Crusades.", "Yes.", "How are we going to do that?" (key 228), "Alright, what are the other crusades?",
  "What? That's terrible!", "What family do I have to ruin?", "We will do this." (key 153) and "Thank you." The talk's
  close (50409) gives key 229 and the Letter (item 10419). "No. There are no Crusaders in our group" is also offered:
  the waiver does not remove it.
- **Thjorgard City.** The party comes in by the west gate (-8790, 4392). Sven is actor 50 at (82, 20736, 3608).
  - The letter: "We have found a disturbing letter that you need to read.", "How so?", "Sounds like a plan." (key 230),
    then "Goodbye.".
  - The Arena: its exit Arenaexit is at (9912, 11141). Set the party at (9585, 11141, -19) facing east and walk in.
    The party arrives at (0, -3686).
  - Inside, walk to (0, -1700) and click the double door (event 100): `svenWalk` sets SvenWalked=1. The stand-in and
    the soldiers (actors 1-3) appear in the box. After 4 s the east pen opens and Byri (actor 4) shows at Marker2
    (0, 0).
  - The party steps onto the sand at (0, -500) and talks to Byri: "We're not going to allow you to murder Sven.",
    "This letter.", "A dying messenger." (key 231), "I'm sure we could come to an arrangement.", "Who put you up to
    this?", "Why did he want Sven dead?", "Sven is going to find out about this.  We suggest leaving town." and
    "Goodbye.". After 2 s he opens the door and runs off; he is gone 4 s later.
  - Do not attack Byri. His death would leave the plot stuck.
  - The Arena Master holds no fights while key 230 is set and 231 is not.
  - Leave by ExitTrigger0 at (0, -3891).
  - Sven again: "The assassin fingered a man named Harris Willington." (key 479), then "Very well.".
  - Harris (actor 2) is at (1925, 8438, 1) in Hreidmar's Stuff: "Seen this letter before?" (key 232), "Unfortunately,
    Sven survived.", "Not you.  You're going to jail." and "Goodbye.". Nothing happens after it (NPC416.scr has no
    exit hook).
  - Sven: "Harris Willington is the accountant at the General Store." (key 234), then "Thank you.  Farewell.". The
    talk's close (51098) gives key 235, 5 000 experience to each member and 10 000 gold.
- **Sturmford City.** The party comes in by the land gate (7300, -3312).
  - Fridleif (actor 31, upstairs in the town hall, (5775, 4603, 20565)): "Have you had any trouble with thieves
    lately?" (optional).
  - Hatlati Oord (actor 12, RUDE 48) walks a six-point path, so the party is set at his spawn (-5253, 11663).
    `interact_actor` has no range. The lines: "We've been watching you, Hat'lai.", "Yes.  We're going to have to arrest
    you.", "You've committed a crime. You will have to go to prison for it.", "Sorry." (key 154) and "Goodbye.".
  - The guard (actor 43) is at (5550, 4690, 19744). His click gives key 5008, which unlocks "We have a criminal here.".
    Then "Goodbye.". The talk's close moves Hatlati into the cell at (5693, 5120, 19743), shuts the door and gives
    key 5009 (`JailOpen` is 0).
  - Itlor (actor 22) is upstairs at (6738, 1610, 20133): "And now he's in jail.", "Why don't you get a job?", "Maybe
    we can help you with that." (key 155), "It's the least we could do.  Can we ask you a few questions?" and "Thanks.".
  - Injor (actor 40) is at (4588, 19046, 19744): "Are you looking for any help?", "We might have the perfect person.",
    "Itlor Oord is looking for work." (key 156) and "Thank you.".
  - Itlor again: "We've found you a job.", "At the Magic Shop.  Injor needs someone to help out." (key 157) and
    "You're welcome.  Good luck.". On the next load he stands in the shop at (4260, 19538).
  - Hatlati in the cell (optional): "Your children will be taken care of, Hatlati", "We found Itlor a job." and "We
    shall.".
- **Grehgknak again.** "We have completed our Crusades." (requires keys 157 and 235, forbids 236), then "Thank you."
  (key 236). The talk's close gives 37 500 experience to each member, `promoteParty("Paladin")` (Crusader -> Hero),
  5 000 gold and key 237. His first page then keeps "Promote our eligible characters.".

## The Druid (RUDE 221, the Green Man; done key 280)

- **Frosgard.** The party comes in by the road gate (1783, 3250) and arrives at (10486, 7209). The city's exit
  ExitTrigger0 is at (11983, 8146): set the party at (11983, 7600) and walk north. Chapter V's city is quiet (key 377:
  the battle is over).
- **Menja** (actor 46, (12042, 369, 1)): "Our Healers are looking for promotion.", "Yes." (requires key 213; waived),
  "How do we find the Green Man?", "We will find the Green Man." (key 262) and "Goodbye.".
- **Fland** (actor 35 in the region, (3551, 6312, 1329); optional): "We need your help.", "We've been charged with
  finding the Green Man.", "Thank you.", "Yes." and "Goodbye.".
- **The Green Man** (actor 36, (-18078, 22282, 1773)): "We've come on behalf of Frosgard.", "We think the
  Frosgardians are eager for your return.", "How can we help?", "We can do that." (key 264), "That can be done."
  (key 265), "We will do that." (key 266) and "Goodbye.".
- **The maypole.** Soxolf (actor 16, (1556, -532, 1)): "What do you do?", "We'd like you to fix it." (requires 264),
  "Sure.  That's no problem." (key 267) and "Goodbye.". The talk's close (50562) takes 500 gold and gives key 268.
  Without the gold, key 267 is taken back. The branch starts with 0 gold, and Sven's 10 000 pays for it.
- **The pledges.** Five of the six keys 269-274 are counted when the talk of 190, 191, 193, 195, 196, 197, 199, 217
  or 218 closes. Goti (192) has no such check. The result is key 277 and 5 000 experience to each member.
  - Soxolf: "Frosgard needs your help.", "The Green Man requires a pledge from Frosgard.", "A pledge to not neglect him
    again." (key 269), "Thank you." and "Alright.".
  - Gudrun (17): "We need your help.", "We need a pledge from you.", "That you will remember the Green Man.", "Without
    him, your crops will fail.", "The Green Man will fix your crops." (key 270) and "Thank you.".
  - Goti (18): "We've come to get a pledge from you.", "The Green Man does not wish to be forgotten again." (key 271)
    and "Thank you.".
  - Tuathal (19): "We need your help.", "The Green Man needs a pledge from you.", "To not forget to celebrate him
    again.", "You won't starve anymore." (key 272) and "Thank you.".
  - Tjorvi the Bold (37): "We need your help.", "The Green Man needs your help.", "It's time for another one.  He wants
    a pledge.", "That you will continue to have the festivals." (key 273) and "Thank you.". His talk's close is the
    fifth pledge and gives 277.
  - Jozka Dorcan (38, key 274) is then offered nothing more: every pledge row forbids 277.
- **Tryygva** (actor 5, (-3768, -1638, 45)): "The Green Man asked you to do something for him." (requires 266), "He
  wants you to make a promise.", "A promise to remember to celebrate him.", "He wants you to carve it on a runestone."
  (key 278), "We will tell him that for you.", "You're welcome." and "Thanks for your time.". The runestone (cog 403)
  shows on the next map load.
- **The Green Man again.** "We have completed your tasks." (requires 268, 277 and 278; gives 279), then "Thank you.".
  The talk's close (frosgard.lua 50103) gives key 280, 37 500 experience to each member, 5 000 gold and the amulet
  (item 10213), and runs `promoteParty("Druid")` (GreatDruid -> ArchDruid, DarkElf -> Patriarch).

## Guide errors and notes

- Both quests' "requires" lack the Jarls' absence from the war council (key 40) until Krohn's task (key 108).
- side_b.yml stop-jarl-sven-s-assassination "requires" says "The Crusader promotion done". It is waived
  (promotions.yml), and the quest is offered to any party.
- The Arena: you step through the double door onto the sand to meet Byri, who comes to the middle.

## Bugs and issues

1. **The Jarls' absence** (above). It is MM9-faithful. Whether to keep it is the user's decision.
2. **A load inside The Arena undoes Sven's plot** (found by `run.py --reload 72`).
   - The map's onLoad handler (`thearena.lua:351-363`) treats every load as a new visit: it sets SvenWalked=0, hides
     actors 1-4, and resets the bouts, doors and locks. So after a save and load with Byri on the sand, Byri is
     invisible.
   - MM9 runs these Inits only at `:Main` and `OnPostStartWorld`, not on a save load.
   - A player recovers by clicking the door again.
   - The coordinator is putting it to the user together with block A's lost Lord purse (same cause). 72's reload run
     is left failing, with no workaround.
