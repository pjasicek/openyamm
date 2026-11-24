# Prep: block D, tier 2 (segments 31, 33, 35, 41, 43, 45)

## 31 T2-A Dimitri's Test (t2-a.yml)

- Start: a copy of main 59 (D1 outside Ellinger's Tower; m24.done 111481, m26.stage3 111521). Party Cavalier Crusader
  Wizard RangerLord.
- Castle Kalindra: D1 event 254 at (-9728, -3072, 1664); DD-03 arrival (-1600, 0); the walk up to the Captain's
  Quarters is main 59's (Cloud Stairs at (-1536, 1600..3200)); Dimitri: event 21 (house 4502), topic "The dungeon"
  (states: done + promotable, done, liches_slain, started, first).
- The dungeon: A8's `devdocs/xeen/briefs/dd03/L4/playtest.yml` stage-3 route: the throne room crossed straight
  (`plan: false`; the planner sticks in its north-east), the closet door (event 13, door 7), the armory, the south
  wing (event 9, door 1), the dungeon stair (door 9, open at stage 3) down to z -640, the ledger (event 40,
  t2-a.cells: "Vexor the Black"), the cell block's door (event 12, door 6), the five liches (group 31) killed; the
  timer event 41 runs t2-a.liches (liches_slain 114521).
- **Bug (BLOCKER A1):** 114521 is already set in every main checkpoint from 51 on. Event 41 is
  `evt.CheckMonstersKilled(ActorKillCheck.Group, 31, 0, false)`; `IndoorWorldRuntime::checkMonstersKilled`
  (game/indoor/IndoorWorldRuntime.cpp:23638) counts an actor with the Invisible attribute as defeated and ignores
  `invisibleAsDead` (`(void)invisibleAsDead`), so the stage-hidden liches count as dead on the first visit at stage 1.
  Without the workaround Dimitri promotes on the first question. Segment 31 clears 114521 and MapVar(2) (logged).
- Exit: event 19 at (-1900, 0), OK, D1 at (-9728, -3072).

## 35 Q-D17 on the oath route

See `D_voweless_oath.md`.

## 41, 43, 45 the T2-LATER topics

`source/quests/t2-later.yml` (A3-promo, 2026-11-21): unpaid promote topics for members eligible later, at Dreyfus
(Mok's blessing), Sharla (Forest lords, polite route only), Luna (The altar's light), Astra (The guilds' word), Nasir
(Archmage's robes), Kramer (Guild title, bounty only), Brother Reger (Masters), the Master Thief (New members, inner
circle only). Their talks as the main chain opens them: Sharla's treehouse (D2 (-19300, -10839, 992), resident
"Sharla", main 49), the Temple of Mok (D1 (3092, 2048, 1152), resident "Dreyfus", main 63), Sandcaster's Guild of Light
(D3 (-13824, 20548, 1504), resident "Nasir", main 65; the guild keeps hours, the checkpoint is in them).
