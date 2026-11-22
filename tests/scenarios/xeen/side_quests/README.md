# Xeen side quests

One standalone headless scenario per Xeen side quest: the 54 of [QUESTS.md](../../../../devdocs/xeen/QUESTS.md) §2
(Q-C1-Q-C26 Cloudside, Q-D1-Q-D28 Darkside), the two optional finale quests Q-F1 and Q-F2 (§2.3), and our own
optional quests (X1-TAM Oslo's son, X8-SKY Cloudreach, the obelisks). Promotions that a side quest pays (T1-B, T1-C,
T1-D, T1-E, the Light and Dark tier-2 quests, the racial ones) are asserted here as the quest's reward; the full
promotion table by class is the promotions run's (`tests/playthrough/xeen/promotions/`). The main story is
`tests/playthrough/xeen/`.

Each scenario starts a new game (`new_game_flow`) on the giver's map with a party of the quest's level and the
classes its promotion serves, sets only the story quest bits the quest needs (by `console: {line: "qbit set N"}`,
commented with the story step each stands for), and plays the quest from its giver to its reward by the rules of the
[Playthrough playbook](../../../playthrough/PLAYBOOK.md) §2:

- the party is immortal (`setup_shortcut: {kind: immortal}`) and enemies near it die (`clear_hostiles`);
- outdoors and in towns the party may be placed (`set_pose`) beside each person, house, prop or exit; exits are still
  entered by walking into them and confirming their prompt;
- dungeons are walked (`walk_to`, ladders with `climb`), never placed in; the routes come from the map lanes'
  `devdocs/xeen/briefs/<map>/L4/playtest.yml` and the main chain's segments;
- talk is by the line a player reads (`select_topic: {match_label: ...}`); items on the ground are picked up
  (`pick_up`), chests looted with Take All;
- every workaround is a logged `ISSUE` (a game problem the run steps around) or `BLOCKER` (one it cannot pass without
  a cheat, the cheat right after it); a `CONVENTION` line is a logged stand-in for progress the quest does not play
  (PLAYBOOK §2), never for a broken game.

What each asserts: the quest's started bit (its journal line) when the giver asks, the done bit and the started bit
cleared at the hand-in (where the quest file says `until`), the step bits and their autonotes, the rewards (experience
per member, gold, items by id, promotions by class, statistics), the dialogue text a player reads at each step, and the
quest's after-state (the giver's done line, a door that now opens, a person who moved).

Like the main story's playthrough, these are a long check, not routine tests: not in CI (never add them to
`tests/scenarios/release/scenarios.txt`) and not run for ordinary changes. Run them when asked, before a release, or
after a change that can break a quest (a quest's map rebuilt, its quest file regenerated, event, dialogue, item or
map-transition code, the save format, the scenario runner), and then only the affected quests.

    python3 tests/scenarios/xeen/side_quests/run.py                 # every scenario (writes report.md)
    python3 tests/scenarios/xeen/side_quests/run.py q-c3_ q-d6_     # some (file-name prefixes; q-c1_ not q-c1)
    python3 tests/scenarios/xeen/side_quests/run.py --repeat 2 q-c3_  # twice each (determinism)
    python3 tests/scenarios/xeen/side_quests/run.py --reload        # save and load back after every settling step

The game binary is `build-xeen/game/openyamm` (STATUS.md, "Engine"). Each result line lists the scenario's ISSUE,
BLOCKER and CONVENTION lines. Logs go to the git-ignored `output/scenarios/xeen/side_quests/` (the `--reload` copies
and their logs to its `reload/`). A new scenario passes twice (`--repeat 2`) and once with `--reload` before it is
listed as passing. Research per quest (maps, people, topic lines, events, routes, qbits, rewards, suspected bugs) is in
`prep/<quest>.md`; the quest logic is `assets_dev/worlds/xeen/source/quests/<quest>.yml`.

## Quests

State: **pass** (normal twice and `--reload`), **pass normal** (reload not yet passing), **blocked** (waits on the
lane named), **partial** (the scenario plays a part of the quest; the rest is said), **none** (no scenario yet).

| Quest | Title (maps) | Scenario | Start | Story bits and preconditions | State | Prep |
| --- | --- | --- | --- | --- | --- | --- |
| Q-C1 | The Seasons Relay (X6, X4, X5, X1) | `q-c1_seasons_relay` | X6 | none; CONVENTION +10 magical age | pass | [q-c1](prep/q-c1.md) |
| Q-C2 | Barok's Pendant (X2), T1-B | `q-c2_baroks_pendant` | X2 | none | pass | (in the file's header) |
| Q-C3 | The Tiara (XD-07, XD-21), T1-E | `q-c3_the_tiara` | X4 | Crusaders 110047 (M4) | pass | [q-c3](prep/q-c3.md) |
| Q-C4 | The Ninja Pagoda (X5, XD-22), T1-D | `q-c4_ninja_pagoda` | X5 | none | pass | [q-c4](prep/q-c4.md) |
| Q-C5 | The Snakes of Asp (X4, XD-25) | `q-c5_q-c11_asp_and_crystals` | X4 | none | pass | [q-c5_q-c11](prep/q-c5_q-c11.md) |
| Q-C6 | Ghosts of Winterkill (X5) | `q-c6_ghosts_of_winterkill` | X5 | none | pass | (in the file's header) |
| Q-C7 | The Count of Nightshadow (X3, XD-24) | `q-c7_count_of_nightshadow` | X3 | none | pass | (in the file's header) |
| Q-C8 | The Scroll of Insight (X6, XD-14) | `q-c8_q-c9_scroll_and_sphinx` | X6 | none | pass | (in the file's header) |
| Q-C9 | The Sphinx (X6, XD-15) | `q-c8_q-c9_scroll_and_sphinx` | X6 | none | pass | (in the file's header) |
| Q-C10 | Scarab of Imaging (X4, XD-26), T1-C | `q-c10_scarab_of_imaging` | X4 | none | pass | [q-c10](prep/q-c10.md) |
| Q-C11 | Crystals of Piezoelectricity (X4, XD-25) | `q-c5_q-c11_asp_and_crystals` | X4 | none | pass | [q-c5_q-c11](prep/q-c5_q-c11.md) |
| Q-C12 | Mirabeth's Elixir (X3, X2, XD-06) | `q-c12_mirabeths_elixir` | X2 | none | pass | [q-c12](prep/q-c12.md) |
| Q-C13 | Lake Beasts (X2) | `q-c13_lake_beasts` | X2 | none | pass | (in the file's header) |
| Q-C14 | Lava for the Water Clock (X5, X7) | `q-c14_lava_for_the_clock` | X5 | none | pass | (in the file's header) |
| Q-C15 | Troll Problem (X5, XD-23) | `q-c15_troll_problem` | X5 | none | pass | (in the file's header) |
| Q-C16 | Cyclops Outpost (X5) | `q-c16_cyclops_outpost` | X5 | none | pass | [q-c16](prep/q-c16.md) |
| Q-C17 | Wand of Faery Magic (X2) | `q-c17_faery_wand` | X2 | none | pass | (in the file's header) |
| Q-C18 | Holy Book of Elvenkind (X2, X5) | `q-c18_holy_book` | X2 | none | pass | (in the file's header) |
| Q-C19 | Ligono's Skull (X2) | `q-c19_ligonos_skull` | X2 | none | pass | (in the file's header) |
| Q-C20 | The Bone Whistle (X1) | `q-c20_bone_whistle` | X1 | none | pass | (in the file's header) |
| Q-C21 | Phirna Root (X1) | `q-c21_phirna_root` | X1 | none | pass | (in the file's header) |
| Q-C22 | Rescue Celia (X1, D3's cottage) | `q-c22_rescue_celia` | X1 | none (`travel` to D3 for the cottage) | pass | (in the file's header) |
| Q-C23 | The Ogre Boulders (X2, XD-27) | `q-c23_ogre_boulders` | X2 | none | pass | (in the file's header) |
| Q-C24 | Joe's Second Business (D1, D4) | `q-d2_q-c24_jasper_and_joes_maps` | D1 | none | pass | [q-d2_q-c24](prep/q-d2_q-c24.md) |
| Q-C25 | The Dragon Tax (X7, XD-18) | `q-c25_dragon_tax` | X7 | none; CONVENTION the 20-gem fee | pass | [q-c25](prep/q-c25.md) |
| Q-C26 | Shangri-La (X7, XD-16, XD-17) | `q-c26_shangri_la` | X7 | none | pass | [q-c26](prep/q-c26.md) |
| Q-D1 | The Gremlin Court (D1, DD-04): peace, fight | `q-d1_gremlin_court`, `q-d1_gremlin_court_fight` | D1 | none | pass | [q-d1](prep/q-d1.md) |
| Q-D2 | Jasper in Jail (D1) | `q-d2_q-c24_jasper_and_joes_maps` | D1 | none | pass | [q-d2_q-c24](prep/q-d2_q-c24.md) |
| Q-D3 | The Drawkcab Way (D1) | `q-d3_drawkcab_way` | D1 | M20 started 111400 (after the refusal before it) | pass | [q-d3](prep/q-d3.md) |
| Q-D4 | Public Storage (D1) | `q-d4_public_storage` | D1 | none | pass | [q-d4](prep/q-d4.md) |
| Q-D5 | Rooka (D1, DD-01) | `q-d5_rooka` | D1 | none | pass | [q-d5](prep/q-d5.md) |
| Q-D6 | The Heretics of Mok (D1, DD-05) | `q-d6_heretics_of_mok` | D1 | none | pass | (in the file's header) |
| Q-D7 | The Gemsmiths (D1, DD-10A, DD-10B): two smiths; the God's refill | `q-d7_gemsmiths`, `q-d7_god_of_minerals` | D1; DD-10B | CONVENTION the gem fees (2, 4) | pass | [q-d7](prep/q-d7.md) |
| Q-D8 | Vespar's Staff (D1) | `q-d8_vespars_staff` | D1 | none | pass | [q-d8](prep/q-d8.md) |
| Q-D9 | Nibbler's Melons (D2, D1) | `q-d9_nibblers_melons` | D2 | none | pass | [q-d9](prep/q-d9.md) |
| Q-D10 | Princess Sheewana (D2, DD-09): polite, mercenary, robbery | `q-d10_sheewana_polite`, `q-d10_sheewana_mercenary`, `q-d10_sheewana_robbery` | D2 | plays Q-D9 for the key; CONVENTION 2 gems | pass | [q-d10](prep/q-d10.md) |
| Q-D11 | Graalg's Ogres (D1, D2): peace, forts | `q-d11_peace_graalgs_ogres`, `q-d11_forts_graalgs_ogres` | D1 | none | pass | [q-d11](prep/q-d11.md) |
| Q-D12 | Yog's Barbarians (D1): peace, war | `q-d12_peace_yogs_barbarians`, `q-d12_war_yogs_barbarians` | D1 | none | pass | [q-d12](prep/q-d12.md) |
| Q-D13 | Hobstadt's Trolls (D2, DD-11A/C): sacrifice, fight | `q-d13_hobstadts_trolls`, `q-d13_hobstadts_trolls_fight` | D2 | none; test setup: a later Troll (D-74) | pass | [q-d13](prep/q-d13.md) |
| Q-D14 | The Wizard Quarter (D3, DD-19) | `q-d14_wizard_quarter` | D3 | none | pass | [q-d14](prep/q-d14.md) |
| Q-D15 | Caleb's Magnifying Glass (D3, D4, DD-23) | `q-d15_calebs_glass` | D3 | none | pass | [q-d15](prep/q-d15.md) |
| Q-D16 | Gurodel's Giants (D5, DD-24) | `q-d16_gurodels_giants` | D5 | none | pass | (in the file's header) |
| Q-D17 | The Chalice of Protection (D5, DD-08, DD-25): Bosco, Voweless | `q-d17_chalice_of_protection`, `q-d17_chalice_of_protection_voweless` | D5 | none; test setup: a later Cavalier (D-74) | pass | [q-d17](prep/q-d17.md) |
| Q-D18 | The Jewel of Ages (D3, DD-07) | `q-d18_jewel_of_ages` | D3 | the Eastern Tower key (Q-D19) | pass | (in the file's header) |
| Q-D19 | The Southern Tower (D3, D2, DD-06): the route; the inner circle alone | `q-d19_southern_tower`, `q-d19_inner_circle` | D3; DD-06 | none | pass | [q-d19](prep/q-d19.md) |
| Q-D20 | Luna's Statuettes (D1, DD-05, DD-20, DD-07) | `q-d20_lunas_statuettes` | D1 | q-d6.tower_opened 113125; the Eastern Tower key (CONVENTION prerequisite lines) | pass | [q-d20](prep/q-d20.md) |
| Q-D21 | Ector's Ring (D4) | `q-d21_ectors_ring` | D4 | none | pass | [q-d21](prep/q-d21.md) |
| Q-D22 | The Coven (D4, DD-20) | `q-d22_the_coven` | D4 | none | pass | (in the file's header) |
| Q-D23 | Sandro's Heart (D6, DD-21): ritual, release | `q-d23_sandros_heart_ritual`, `q-d23_sandros_heart_release` | D6 | the Necropolis pass (grant) | pass | [q-d23](prep/q-d23.md) |
| Q-D24 | The Enchanted Boulders (D5) | `q-d24_enchanted_boulders` | D5 | none | pass | [q-d24](prep/q-d24.md) |
| Q-D25 | The Minotaur's Labyrinth (D4, DD-12) | `q-d25_minotaurs_labyrinth` | D4 | M20 started 111400, Megan's key (grant); test setup: a later Minotaur | pass | [q-d25](prep/q-d25.md) |
| Q-D26 | The Megadragon (D7) | `q-d26_megadragon` | D7 | Chosen Ones 111600 (M30); the Soul Box (grant) | pass | [q-d26](prep/q-d26.md) |
| Q-D27 | Genie Lamps (D2, D4, D5, D6, D7) | `q-d27_genie_lamps_d2` … `_d7` (five) | each map | D7: as Q-D26 | pass | [q-d27](prep/q-d27.md) |
| Q-D28 | Cyrano's Tribble (D7, DD-26) | `q-d28_cyranos_tribble` | D7 | Chosen Ones 111600; 25,200 starting gold | pass | [q-d28](prep/q-d28.md) |
| Q-F1 | Alister and the Dragon Egg (X7, FD-04, X9) | `q-f1_alister_dragon_egg` | X7 | M39 done 111781, the Dragon Tower key (grant) | pass | [q-f1](prep/q-f1.md) |
| Q-F2 | The Dungeon of Death (X7, FD-04) | `q-f2_dungeon_of_death` | X7 | Sandro released 113462, his key (grant) | pass | [q-f2](prep/q-f2.md) |
| X1-TAM | Oslo's Son (X1, XD-05) | `x1-tam_oslos_son` | X1 | none | pass | (in the file's header) |
| X8-SKY | Cloudreach (X1, XD-04, X8) | `x8-sky_cloudreach` | X1 | Crusaders 110047 (M4), the Crystal Key (grant) | pass | [x8-sky](prep/x8-sky.md) |
| OBELISKS | The obelisks and their hoards (X1-X7, X6; D1-D6, D5) | `obelisks_cloudside`, `obelisks_darkside` | X1; D1 | none (`travel` between maps) | pass | [obelisks](prep/obelisks.md) |

Last full runs: 2026-11-21 20:08-20:42, `build-xeen` of merge point 37 (18:35:58), the 71 scenarios, after the map
reinstalls that moved monster markers (X1, X2 by D-85/D-88, X4, X5 by D-87, X6, D1, D2, D3, D6, D7, P1, XD-12,
XD-19, DD-10C): normal 71 of 71, `--reload` 71 of 71, no ISSUE or BLOCKER line. The scenarios the map lanes named
(Q-C1, Q-C4, Q-C12, Q-C14-Q-C19, Q-D2/Q-C24, Q-D23, Q-D27, both obelisk walks) passed a second time in both modes,
and A1's `xeen/d6_ambrose_flight.yml` passes on the rebuilt D6. No scenario needed a change for the moved markers.
Every scenario's `PARTY end` line is in the report (members still down at the end are logged, not failed: Q-D16's
giants, Q-D27 D7's angry genie's intended stone).

Session 3 (merge points 35-37): the D-82 checks found Q-F2 (FD-04's undead eradicated the whole party), Q-C9 (a
member asleep from the paw hall), Q-D16 war under reload (the giants' knock-outs at the longhall door) and members
down before promotions in Q-C10, Q-D10 polite, Q-D13 and Q-D23 (both routes); all are fought or cured as
"Conventions" below says.

## Open items

None logged in the scenarios (no ISSUE or BLOCKER lines). Found, not worked around (nothing in the run depends on it):

- **Q-D12 war, Yog falls with his camp:** Yog (actor 29, monster 11103) is in the Sardaj's group 60, so "Battle!"
  turns him hostile with them and the clear kills him; the scenario no longer talks to him afterwards. Reads as the
  war route intends ("you shall not leave these lands alive"); noted for A6 in case Yog should survive to be spoken to.

Closed on 2026-11-21 (session 2):

- **Q-C1, magical age (A1):** rests and travel days no longer clear it (merge point 33, 14:44); the scenario gives the
  ten years at the start and checks them still there on X1 (at least 38: a ghost's touch on the road may add a year).
- **Runner clear radii across storeys (A1):** merge point 33 keeps clears below radius 5,000 to the party's storey.
- **Random treasure drawing MM9 items (A1/O, D-44):** gone in merge point 33.
- **Q-D12 war, D1 event 215 (A6):** the Sardaj turn hostile within a second of "Battle!" (14:31); the save and load
  step is gone.
- **Q-C16, X5 event 112 (A6):** the outpost asks "You have found the Cyclops' outpost! Burn?" on Yes/No buttons
  (14:35); the scenario answers Yes.
- **Q-D4, D1's lettered chests (A6):** they say "A letter on the lid reads: P. The lid drops shut.", "The P chest is
  shut." and "... It will not shut. All nine lids spring open again."; the scenario asserts them.
- **Q-D27, the small lamps' second rub (A6):** "The lamp is cold. Its genie has gone back in for good." (D4's skerry:
  "The lamp is cold and still wet. Its genie has gone."); asserted on D2 and D4.
- **DD-10A, "a emerald" (A8):** fixed 14:26; Q-D7 asserts "You work an emerald rock out of the vein." on each vein.
- **DD-20's outfall (A8):** not one way; the earlier walk back stuck against a live Sewer Stalker (A8's probe
  `output/studio_cal/a8_s22/probe/dd20_back4.yml` walks it with `clear_hostiles: 1500`). Q-D20 still returns by the
  warren.
- **The Megadragon's experience (A2):** 16,875 for the party (4,218 each of four) is intended (D-77 Q1); q-d26's note
  already says so.
- **Q-D10, Sharla paid robbers (A3's answer to lane G):** her first state is now `robbery` (no pay); the new robbery
  scenario asserts it. **Q-D15:** the nest gives the glass only once the roost is destroyed (`requires`, a fail line);
  asserted before the Yes.

Conventions the scenarios use (PLAYBOOK §2):

- **Party health (D-82):** the runner fails a step after which no member can act (`PARTY DOWN after step N`; the tag
  `side_quest`). `run.py` runs every scenario from a copy that ends with `PARTY end: [c0] [c1] [c2] [c3]` (each
  member's conditions; logged, not asserted: nothing continues from a side quest; none saves a checkpoint for another
  test). A step that reads particular members (a promotion hand-in, a later-member test setup, a throne or scroll that
  raises the selected member) first asserts they can act (none of Dead, Eradicated, Petrified, Paralyzed, Unconscious,
  Asleep). A member who is down before such a step is cured as a player would, at a temple on the way
  (`heal_at_temple: {house, min: 0}`: Q-C10 X4's chapel 4153; Q-D10 polite and Q-D13 D1's 4455, Sprite Forest
  having none; Q-D23 D6's 4752, the ritual walking out of the crypt and back for it), or the cause is fought first
  (Q-C9's paw hall on arrival, Q-F2's eradicating undead: every walk clears 3,000).

- A new game carries no gems: a gem fee is granted exactly after an honest refusal (Q-C25's tax, Q-D10's alcoves,
  Q-D7's smiths).
- A member recruited after a hand-in is stood in by a logged test setup (`CLASSES test setup later-member`, D-74, D-75,
  D-77), not a CONVENTION: `SetPlayerClass` on an existing member just before the later path (Q-D13 both routes,
  Q-D17's oath, Q-D25), after the nobody-eligible line is asserted, and the unpaid result asserted after.
- A started bit with `until: done` stays set after the hand-in (only its journal line hides); the scenarios assert
  what the quest file says.
- There is no journal-line assert: the quest's started and done bits stand for its journal lines; autonotes are
  asserted by id (`assert: {autonote: ...}`).

Not covered:

- Q-C25's Dragon skills (QUESTS §2.1) are Scaldrith's teaching in `towns/xd18.yml`, not a quest reward; not tested.
