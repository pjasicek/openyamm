# Xeen playthrough

A headless run of the World of Xeen main story, from a new game to the ending (devdocs/xeen/ROADMAP.md §5.10), as
evidence that it can be played through. Built and run by the [Playthrough playbook](../PLAYBOOK.md); every segment
`NN_<name>.yml` loads the checkpoint the one before it saved and saves its own. Owner: A3 (the quest steps); A1 keeps
`run.py`. Not in CI; a long check (AGENTS.md).

    python3 tests/playthrough/xeen/run.py              # every segment, stopping at the first failure
    python3 tests/playthrough/xeen/run.py 57 59        # some segments (their starting checkpoints must exist)
    python3 tests/playthrough/xeen/run.py --reload     # save and load back after each settling step

Output (git-ignored): `output/playthrough/xeen/checkpoints/`, `logs/`, `report.md`; `reload/` for the save-and-load
run. `--reload` puts no reload before a step that reads the status line (`status()` before any click), nor between
it and the `advance_runtime` just before it: a status line does not outlive a save and load (D-90's status-line finds,
touches and deaths). Nor does it put one between a step and an `advance_runtime` that presents dialogs when an
assert on the dialog follows: that shows a message the step raised (a timer's `evt.SimpleMessage`), and a player cannot
save over an open message. The side-quest runner does the same. Binary: `build-xeen/game/openyamm` (A1's). The promotion chain ([promotions/](promotions/README.md)) starts from
these checkpoints; keep them in place.

## Coverage

52 segments (01-93 in odd numbers, then 95-99), every main step M1-M42 of devdocs/xeen/QUESTS.md, plus the side
quests the main line needs (Q-C14's Widget for M40, the promotions T1-A, T1-B, T1-E, Q-D6, Q-D10, Q-D18 the party
meets on the way). Segment 99 ends on 111840 (M42 done), the unification cinematic and the ceremony.

The party is a Knight, a Paladin, a Sorcerer and a Ranger, made by the new-game screen in segment 01; at the end they
are a Cavalier, a Hero, an ArchMage and a Ranger Lord.

## State

**2026-11-22 (A3 session 41, MP46): the whole chain passes again, normal (52/52, 16:36-16:44) and `--reload` (52/52,
16:47-17:22; 4,401 reloads), on the maps after D-98 (Castle Xeen's extra monsters and throne guards; Lord Xeen is
actor 37), D-99 (chests turned and moved) and D-100 (every Xeen BLV rebaked).** Promotions `--start` 41/41, side
quests 71/71 normal and 71/71 `--reload`. Details: devdocs/xeen/lanes/A3.md (session 41).

**2026-11-22 (A3 session 40, MP45): the whole chain passes, normal (52/52, 13:33) and `--reload` (52/52, 14:11; 4,401
reloads), on the maps after D-93 (X1's rain barrel and X5's torn pack give their finds onto the cursor), X1's water
end piece and the villagers with their race palettes (X1-X6, D1-D4); quest topics read "Quest" (session 39).**
Promotions `--start` 41/41, side quests 71/71 (normal). Details: devdocs/xeen/lanes/A3.md (session 40).

**2026-11-21 (A3 session 33, merge point 37): the whole chain passes from a new game to the ending, normal and
`--reload`, with D-82's party check, on the maps rebuilt since session 32 (X1, X2, X4, X5, X6, D1, D2, D3, D6, D7, P1,
XD-12, DD-10C, XD-19).** Normal: 52 segments, 7,238 steps, 537 s (checkpoints written 20:08-20:39). `--reload`:
12,265 steps, 2,271 s, 4,397 reloads done, 632 skipped, 4 dismissed an arrival (checkpoints 20:08-20:48). One fix:
71 fights DD-16's main-deck eyes before the inner door. Details: devdocs/xeen/lanes/A3.md (session 33).

- The only CONVENTION lines are segment 83's four stat gates (D-68): Might, Speed, Endurance and Accuracy, each
  raised to 60 as a temporary bonus after every member has tried.
- No BLOCKER or ISSUE lines.
- Since merge point 33 a clear keeps to the party's storey indoors (radius below 5,000). Monsters on another floor are
  fought where they meet the party (57, 61, 63), and monsters above or below are fought with the step's `height`
  (`clear_hostiles: {radius, height}`, `walk_to`'s `clear_height`; 61 and 67 on DD-14's battlements, 77's robots).
  77 and 95 assert that no member is Eradicated or Dead after their robot fights.
- **The party ends every segment able to act (D-82, PLAYBOOK §2):** `run.py` runs a copy of each segment
  (`output/playthrough/xeen/segments/`, or `reload/`) with a check before its final save: it logs
  `PARTY <NN> end: [c0] [c1] [c2] [c3]` (the report's PARTY section) and fails the segment when a member is Dead,
  Eradicated, Petrified, Paralyzed or Unconscious. A member who is down is cured at the first temple on the route
  (`heal_at_temple: {house, min: 0}`, a `HEAL` line in the log) or the cause is fought first; lesser conditions
  (Weak, Diseased, Cursed …) are logged only. The promotion chain inherits the check (its run.py calls this runner).
- The party drops its spare loot at the starts of 23, 27, 31, 35 and 57 (quest items, gems, potions kept): full
  packs leave a reward on the cursor.

## D-82: where the party is hurt and where it is healed (sessions 32 and 33)

The temple cures stay where session 32 put them even where a map fix has since removed the cause: a cure costs nothing
when nobody needs it (no `HEAL` line), and it still answers what remains.

| Cause | Segments | Answer |
| --- | --- | --- |
| Sprite Forest (D2): Gorgon and Medusa Sprites (Stone), met on the edge roads (monsters that followed the party to an edge wait there when it comes back). **Removed by D-87:** D2's edge arrivals rebuilt at least 6,001 from any ranged disabler; session 33 met none (both chain runs, one condition-logged probe of each D2 segment) | 43, 51, 53, 55, 59, 61, 63, 65, 67, 69 | kept: Temple of Mok 4455 (Castleview, D1) at the end of 43, 51, 53, 55, 59, 63, 67 and on 61's way north; Temple of the Desert Sun 4605 (Sandcaster, D3) on 57's and 69's way and at the end of 65 |
| XD-12's gate hall: the Well's Floating Eyes (11570, Paralyze missiles) shot along the arch line at the arrival. **Removed for 37** (A8, XD-12 session 25: the group moved to the cistern; 37 three of three with nobody Paralyzed) | 37 | kept: Pray N Pay 4058 (Rivercity, X2) after the tower; it now cures the Disease one or two members bring from 27 (below) |
| XD-12 inside the tower: the Floating Eyes of the upper floors (works, library, roof) (on the walk at z 3,072 to the cloud stair) and the eyes that drift into the Well (on the lift down, `click(15)`) Paralyze a member in 3 of 3 probes | 79 | Pray N Pay 4058 at the end of 79 |
| X2's dark-end Medusa Sprite markers at the XD-06 door (moved by D-88) (Petrify, reload run) | 23 | kept: Pray N Pay 4058 at the end of 23; session 33: 3 of 3 probes and both chain runs clean |
| DD-14's battlements: Gargoyle Sentinels (11551, Paralyze), Gargoyle Overlords (11552, Stone) | 61, 67 | fought where they meet the party: `clear_hostiles: {height: 700}` on the south-west tower top and back on the battlements (61), on the landing (67); 67 also ends at the Temple of Mok |
| Castle Alamar's robots (Eradicate), FD-01's Autobot | 77, 95 | fought first (77 with the step's `height`) |
| DD-16, Corak's pod: the main deck's Floating and Terrible Eyes (11570, 11571, Paralyze missiles) behind the inner door; with the door open, a reload landed their shots in flight (reload 71, 2 of 2 probes) | 71 | fought before the door opens (session 33: `clear_hostiles` on the walk to the door and 2,500 there) |
| D6's field eyes by the DD-22 hatch (moved off it by D-87) | none (the main chain does not use DD-22's hatch) | — |
| XD-08's Grave Ghouls (11252, Disease on melee) at the foot of the hanging cage, while the cage comes down (`click(2); wait(8)`): one or two members DiseaseMedium (a lesser condition, logged only) | 27 to 35 | Pray N Pay 4058 at the end of 37 |

- 61's Count Blackfang: his death message comes during the walk west from the hall's door (`walk_to ... expect:
  dialog` with the clear), not after a separate `clear_hostiles`: a reload between the kill and the message (the
  `--reload` copy) presented the message and closed it, and the assert after it failed.
- 67's reload Petrify (session 30) and D2's west edge: the same D2 cause as above; no save/load cause was found
  (session 31's probes `output/a3_s31/probe/`), so nothing went to A1.
- The ending (Reviewer row 18): the chain closes every window with Escape; merge point 36 stops a Return that closes
  a window from also acting in play (session 31 found it toggling turn-based mode).

## Rerun after

| Change | Segments |
| --- | --- |
| X1, XD-01 to XD-05 | 01-11 |
| X2, X3, X4, XD-06 to XD-12, XD-21, XD-27 | 13-37 |
| D1-D4, DD-01 to DD-12 | 39-67 |
| D5, D6, D7, DD-15, DD-16, DD-17, P1-P5 | 69-99 |
| XD-12, X9, XD-19 | 79-85 |
| FD-01 / FD-02 / FD-03 | 95 / 97 / 98 (regenerate first: `output/a3_s27/make95.py`, `make97_98.py`; make95 adds door 10's fight) |
| X5, X7 | 96 |
| quest files, `xeen_common.lua`, the scenario runner, saves | all |

## Journal checks (A3 s38)

The scenario runner cannot read the journal itself, so `run.py` expands a segment's `journal:` step into the qbit
asserts that decide a Current Quests line (`english/quests.txt`'s required and forbidden columns, as
`JournalQuestTable::isVisible`): `- journal: {shown: [111740], gone: [111743], unstarted: [111720]}`. `shown`: every
required bit set and every forbidden bit clear; `gone`: the required bits and the line's one ending bit set; `unstarted`:
the required bits clear. Segments 59 and 85 use it.
