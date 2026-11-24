# Prep: block F, the racial promotion quests (segments 61, 63, 65, 67)

Quests: Q-C7 (Vampire -> Nosferatu), Q-D13 (Troll -> War Troll), Q-D25 (Minotaur -> Minotaur Lord), Q-C25 (Dragon ->
Great Wyrm); `Xeen.Promotions` rows `vampire`, `troll`, `minotaur`, `dragon` (xeen_common.lua). The chain's party is
the main chain's Knight/Paladin/Sorcerer/Ranger line, so none of these promotes anybody in it (README check 3). Each
segment starts from a copy of the main chain's checkpoint just before the quest (or after it, for Q-D25's throne).

| Segment | Start | Party at start | Quest |
| --- | --- | --- | --- |
| 61_nightshadow_count | `00_main_35` (main 35, X3 after XD-11) | Cavalier Crusader Wizard Hunter | Q-C7 played; no setup |
| 63_hobstadt_tribute | `00_main_49` (main 49, D2 at Sharla's) | Cavalier Crusader Wizard RangerLord | Q-D13 tribute; later Trolls by setup |
| 65_horned_throne | `00_main_57` (main 57, D4 Lakeside's jetty; Q-D25 done) | Cavalier Crusader Wizard RangerLord | the walk back to the throne |
| 67_dragon_tax | `00_main_83` (main 83, X4 outside Castle Burlock) | Cavalier Hero ArchMage RangerLord | Q-C25; the Dragon by setup |

## Q-C7 The Count of Nightshadow (X3, XD-24), segment 61

- Source `source/quests/q-c7.yml`; X3 events `events/maps/xeen_x3.lua` 46-56; XD-24 `xeen_xd24.lua`.
- Qbits: started 112140 (the rhyme board), done 112141 (Draco's kill timer), dials_set 112142 (the map, all three
  dials at 9), coffin_opened 112143, vault_open 110940 (XD-24's iron door at night).
- X3, Nightshadow's square: the party placed at (17920, -4352, 992) facing north. Click 49 the rhyme ("If the dials
  are properly set...", started), 50 "The Count wakes at nine and sleeps at nine.", 54 "A stitch in time.", 55 "Lives
  of a cat.", 48 "Only at night can you put up a fight.", 56 the well ("black and tastes of iron" before done; "tastes
  faintly of garlic" after, +10 Personality and the cures).
- Coffin, event 46: dials wrong "none of them set as they should be"; by day "while the sun is up"; at night (21:00 to
  6:00) "The lid slides aside." (coffin_opened). Event 47 the stair down into XD-24 at (0, 704, 0).
- Sundials 51-53: each click asks "The sundial is set to V.  Turn? (Yes/No)"; Yes turns it on by one (12 wraps to 1).
  Main 35 leaves them at 3, 6 and 12 (mapvars `x3_dial_1..3` unset, read 0 by `mapvar`; the event's defaults): 6, 3
  and 9 turns. The segment reads each dial's question first.
- Night: main 35's party stands on X3 at about 10:05; the segment camps on the square until 21:00 (`AdvanceGameMinutes`
  + `RestAndHealParty`, a logged `CAMP` line, as main 57's camp at Lakeside's jetty).
- XD-24 route (A3-side's standalone, the L4 playtest): (0, 300) -> (0, -384) -> (-900, -384) -> (0, 512) -> (-1280, 576)
  -> (-1800, 576) door `open_door(14, 6)` -> (-2400, 576) -> (-2688, -500) -> (-2688, -2300, -640) -> (-2000, -2496)
  -> (-500, -2496) -> (990, -2496, -1280); sign 22; the iron door 18 at night (door 5, vault_open). Draco is actor 7
  (kill timer event 16, every minute: doors 1 and 2 open, `q-c7.draco`: done, 10,000 each, the message "Count Draco
  crumbles to dust"). The household blocks the vault's doorway (`walk_to` stuck at (1235, -2496)): the segment kills
  them from the door (`clear_hostiles` 3000) and measures the hook's 10,000 apart from the kills' experience. The
  sarcophagus 21 ("bid him farewell"), the hoard chest 5 at (2688, -1800, -1248), the Count's stair up (2048, -1700)
  -> (2048, 380, -450) -> (800, 512) -> (0, 512) -> (0, 1800, 384), event 17 OK -> X3.
- Du Monay Manor (house 4105, Count Du Monay 4205): the party placed at (19204, -1920, 960) facing east,
  `press_interact`. "The Count": after done "Draco is gone. The town breathes."; "Nosferatu" shown only with done and
  a Vampire (`show`), text "...Rise, Nosferatu.", unpaid.
- Rewards asserted: 10,000 experience each at Draco's death; nothing at Du Monay; classes kept.

## Q-D13 Hobstadt's Trolls (D2, DD-11A, DD-11C), segment 63

- Source `source/quests/q-d13.yml` (D-74 point 3 landed); D2 events 32-34 (`xeen_d2.lua:131-152`); DD-11A
  `xeen_dd11a.lua`; DD-11C `xeen_dd11c.lua`.
- Qbits: started 113260 (the thief's letter; `until: [done]` is the journal line only, the bit stays), tribute 113261,
  trial 113262, hostile 113263, hobstadt_slain 113264, throne_taken 113265, done 113266. Autonote 4530.
- Ending chosen: **the tribute** ("Give gold", 2,000). Cheapest: no Troll needed (the sacrifice needs one), no fight
  (the fight needs Hobstadt killed, his kill timer and the court turned hostile), and the party carries about 57,000.
- D2 holes (party placed at each; `click`): A event 32 at (-2048, -6144, 992) -> DD-11A (80, -208); B event 33 at
  (3072, -10240, 960) -> DD-11B; C event 34 at (1536, -17408, 928) -> DD-11C (128, -64).
- DD-11A (A7's playtest): (1100, 0) -> (2150, 0) -> (2656, 200) -> (2656, 580, 160) boulder `open_door(2, 1)` ->
  (2656, 920, 192) -> (2560, 1020, 192), the dead thief event 10 (letter: started, autonote 4530; again "nothing else
  to say"). Out: (2656, 880, 192) -> (2656, 150) -> (1100, 0) -> the sleeping hollow (1150, -1000) -> (720, -1088) ->
  the burrow (-620, -1088, 340), sod hatch event 7, "Do you wish to leave" OK -> D2 (-2048, -6144).
- DD-11C: (960, 0) the doors' step line (map variable 4, once a visit: "Nobody stops you"); (2300, 0); the throne floor
  near (2688, 0) runs event 2 (`SpeakNPC(5110)`, once: map variable 0, not after hostile or slain). Hobstadt's topics
  before a deal: Give gold, Sacrifice one, Fight to the death. "Give gold" with 2,000: "Hobstadt cannot count past two
  thousand. Good. Go where you like." (tribute). The sacks event 15 at (3800, -320): before a deal "Hobstadt is
  sitting in front of it"; after "Sacks of gold, each stamped THIEVES' GUILD." (done, 4,000 each, 2,500 gold); again
  "Empty sacks. Labelled." The strongbox chest event 4 at (4060, -500) (gold, the map's). The throne event 16 alive:
  "Hobstadt stands before it and watches you". Hobstadt himself: `interact_actor` actor 12.
- After the tribute: "Give gold" and "Fight" hidden; "Thieves' gold" ("Thief gold in back...") and "Sacrifice one"
  shown. Sacrifice one, by state: trial + a Troll "Another troll? Hobstadt take him too..." (promotes, unpaid; D-74
  new); trial "Hobstadt has his War Troll. Go where you like." (D-74 new); a Troll "Troll in your party... Now he is War
  Troll. You are friends of Hobstadt." (sets trial, promotes); else "No troll. Hobstadt not eat your kind. Too many
  bones. Give gold, or fight." The segment plays the else line (nobody a Troll), then the three later states by a
  logged test setup (members 1 and 2 made Trolls; classes put back). Nothing is paid by any of them.
- Out of DD-11C: (2300, 0) -> (960, 0) -> (-300, 0) -> (-1650, 0, 340), sod hatch event 12, OK -> D2 (1536, -17408).
- Fight ending (not played): `Fight to the death` sets hostile; Hobstadt (11073, actor 12) killed -> event 14 every
  minute (`CheckMonstersKilled ActorIdOe 12`) -> `q-d13.hobstadt` (slain, status line); the throne event 16 then calls
  `q-d13.throne` (requires slain + a Troll; no `once`; fail "The throne is vacant.").

## Q-D25 The Minotaur's Labyrinth (DD-12), segment 65

- Source `source/quests/q-d25.yml`; DD-12 `xeen_dd12.lua` events 24 and 90 (`if not hook("q-d25.throne") then
  hook("q-d25.throne_again") end`). done 113500 (main 57).
- From main 57 (D4 Lakeside's jetty at about 17:45): the yachts (house 4655, route 420) run 6AM-6PM; the segment
  camps until 6 as main 57 does. Isle (4096, -4096); the ruined tower's door (4095, -2843) -> DD-12 (0, -352).
- DD-12: gate 1 (event 37) open since 57 (doors 6, 7: a click only toggles them once its bit is set); the hall of
  storage (0, 780) -> (-1900, 780) -> the lift head (-2320, 800); the cage (door 1, up since 57) at (-2304, 1312, 0);
  event 80 (ride down; the button in reach on the raised cage) sinks it to L5 (needs bird_freed 111480). The aviary
  (-2304, 1700) -> (-2100, 2112); gate 5 (event 49, door 14) open since 57; the maze, 57's way out reversed: (-1100,
  1920) (-736, 1920) (-224, 1920) (-224, 2432) (-736, 2432) (-736, 2944) (288, 2944) (288, 2432) (800, 2432) (800,
  2176) (1312, 2176) (1312, 2944) (2336, 2944) (2464, 2048): the horned throne, event 90.
- Nobody a Minotaur: "The horned throne waits. It honours Minotaurs, and anyone else who sits gets a sore back." (the
  `throne` hook's else text); `throne_again` is silent; no experience, no class change.
- With a Minotaur (probed from 65's checkpoint): he is promoted (MinotaurLord, unpaid), but the only window is the
  same else line: see finding D25-1.

## Q-C25 The Dragon Tax (X7, XD-18), segment 67

- Source `source/quests/q-c25.yml`; A3-side's `tests/scenarios/xeen/side_quests/prep/q-c25.md` (all the places).
- Qbits: tax_paid 112500, volume1 112501, wyrm 112507, inner_door_open 118100 (XD-18's). Autonote 4390, award 430.
- Route: X4's east edge (22016, -1280) -> X7 (-22016, -1024) (main 85's edge); the party placed at the cave's mouth
  (-3891, 16589, 2144), event 40 Yes -> XD-18 (384, -3072). Urn 25 at (1536, -3460); Scaldrith event 18 at (1984,
  -3560); the lectern 26 behind door 10 (`open_door(10, 10)` from (1920, -2600), stand (1920, -1900)); the inner door
  14 at (2560, -3072); the mouth 11 at (140, -3072), "Do you wish to leave" OK -> X7 (-4096, 16896).
- Gems: main 83's party carries none (and gold about 70,000): the 20 gems are a logged CONVENTION after Scaldrith's
  refusal ("No gems, no entry"), granted only while the party has none.
- "Great Wyrm" (show: tax_paid and volume1), by state: a Dragon and no wyrm "A dragon who pays tax and reads..." (wyrm,
  12,000 each, promotes); a Dragon "Another dragon who reads? The office is becoming a library. Rise, Great Wyrm."
  (unpaid; probed from 67's checkpoint); none "Great Wyrms are made of dragons, and you have none with you." The
  hand-in pays only when it promotes, so the segment makes member 1 a Dragon by a logged test setup.
- Rewards asserted: 2,000 gold and 20 gems taken; volume 1 2,000 each and award 430 for every member; Great Wyrm
  12,000 each once; classes put back.

## Suspected bugs and findings

- **D25-1 (A3, q-d25.yml:30; DD-12 events 24/90, `xeen_dd12.lua:216-220, 831-836`):** after done, a Minotaur who sits
  is promoted by `q-d25.throne_again`, but the player reads only `throne`'s else text ("anyone else who sits gets a sore
  back"): its own line "The Minotaur sits, and rises a lord of the maze." never shows (two `SimpleMessage`s in one
  event: the first stays). Repro: load `checkpoints/65_horned_throne.oysav`, `lua_event SetPlayerClass(0, 'Minotaur')`,
  `click(90)`: classes MinotaurLord..., the one window is the else line, nothing after it. Fix idea: drop the
  throne's `else_text` and give `throne_again` a `fail_text` with it, or let the map call `throne_again` first.
- **D13-1, fixed (A3-side, 2026-11-21; D-72): the hook is now a status line, "You let yourselves down into the troll hole.", and the party moves at once with no question (63 and 69 assert it). The finding as first written:** (A3, q-d13.yml:71-74; D2 `xeen_d2.lua:131-152`) `q-d13.troll_holes` says "Troll Hole. Descend?" as a
  message, then the map moves the party at once: there is no Yes/No, and the window is lost in the move (headless: no
  window on arrival in DD-11A). Either an `AskQuestion` (a player could step back) or a plain statement.
- **D13-2 (A3, q-d13.yml:56):** after the tribute, "Sacrifice one" with no Troll still ends "Give gold, or fight.",
  though neither is offered any more.
- Check 3 shape: Du Monay's "Nosferatu" is hidden while nobody is a Vampire (`show`); Hobstadt's "Sacrifice one" and
  Scaldrith's "Great Wyrm" stay offered with a nobody line (their states), as Dimitri's "The dungeon"; the horned
  throne says its else line.
