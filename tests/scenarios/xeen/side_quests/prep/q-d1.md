# Prep: Q-D1 The Gremlin Court

Scenarios `q-d1_gremlin_court.yml` (peace: the notice starts it, the three rounds, Snarfblad's pay and gift) and
`q-d1_gremlin_court_fight.yml` (fight: Snarfblad starts it, Gettlewaithe killed, the throne's treasury, the pay without
a gift). Quest file `source/quests/q-d1.yml` (qbits 113020-113029, autonotes 4410 court, 4411 won); topics in
`events/common/xeen_quests.lua`. Routes: `devdocs/xeen/briefs/d1/L4/playtest.yml` (the notice 166, the burrow 170),
`devdocs/xeen/briefs/dd04/L4/playtest.yml` and `playtest_kill.yml` (the court), chain segment
`tests/playthrough/xeen/41_gremlin_court.yml` (peace). `after: [m7.sigil]` is ordering only; a new game on D1.

## D1 (Castleview Vale)

| what | where | how / text |
| --- | --- | --- |
| the Mayor's notice, event 166 (thing `gate_notice`) | stand (-512, 11520, 1168) yaw -pi/2, outside the north gate | `q-d1.gate_notice`: first time started 113020, autonote 4410, "BY ORDER OF THE MAYOR..."; again its else_text "...a gremlin on it, upside down." |
| the burrow, event 170 (thing `dd04_burrow`) | stand (2304, 11059, 1152) yaw -pi/2 | `evt.MoveToMap` into DD-04 (no prompt); the hook's text after |
| Castleview Town Hall, house 4466 | stand (1540, 5888, 1152) yaw 0, use | house screen "Mayor Snarfblad" (NPC 4916). "Gremlins": none set: the offer (started, autonote 4410); started: "No gold for you"; court_won: "Oh, frabjous day!" (done 113022, autonote 4411, 5,000 XP each, 2,500 gold, Castleview Pass 12330); done: "Castleview likes you!". "Gettlewaithe's gift" shown with court_peace, done, not gift_paid: three Energy Disks 12334 (gift_paid 113029) |

## DD-04 (the Gremlin Court)

Arrival (0, 256, 0). Walk: (0, 900), (256, 1600), (0, 2150), (0, 2816), (0, 3200); the waiting room door event 10
(door 5); (-150, 3776), (0, 3980); the court door event 8 (door 1); the court (0, 4900, z 2). Gettlewaithe (actor 0,
monster 11023, own faction, immobile) talks through his throne event 22 (or the dais 7): first the challenge
"Imperator Primus of the Gremlins". Topics: "We come in peace" (round1 113023), "The Mayor's demand" (court_hostile
113024, the court and guards turn), guards (actors 1-3, 11026) dead: the map's timer (guards_beaten 113025, "a much
paler shade of green"), "Submit or die" (court_peace 113026, court_won 113021, autonote 4411). Fight: Gettlewaithe
dead: the timer's status line "topples off his throne of chairs" (gettlewaithe_slain 113027, court_won,
court_hostile). The treasury, chest event 5, stand (208, 5330, z 2): refused while he lives ("The throne is
occupied"); after his death "You find 3 Energy Disks under the late Gettlewaithe's throne." (throne_searched 113028, 3
disks, 600 gold); the throne afterwards "Under the throne: crumbs". Exit: the tiny door event 13 at (0, 128), "OK", to
D1 (2048, 11264).

## Asserts

Starting bits clear; autonotes; every line; Snarfblad's 5,000 XP per member and 2,500 gold; the pass; 3 disks either
route (gift on peace, treasury on fight; never both: the gift topic is absent after a fight); gettlewaithe_slain clear
on peace; the gremlin king alive on peace.
