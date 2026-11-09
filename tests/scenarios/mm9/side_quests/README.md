# MM9 side quests

One standalone headless scenario per side quest of the MM9 guide (the "Side quests" tab,
https://jasicek.net/openyamm/mm9-guide/#quests-side, written from `tools/mm9_site/story/side_*.yml`; promotions are
separate). Each starts a new game at the quest giver's map (`new_game_flow`), sets only the story quest bits the quest
needs (commented in the file), and plays the quest from its giver to its reward by the rules of the
[Playthrough playbook](../../../playthrough/PLAYBOOK.md): the party is immortal and nearby enemies die, it may be
placed outdoors and in cities, dungeons are walked, talk is by the line a player reads, and every workaround is a
logged `ISSUE` or `BLOCKER`. They do not load the main playthrough's checkpoints (those are git-ignored).

Like the main story's playthrough, these are a long check, not routine tests: not in CI (never add them to
`tests/scenarios/release/scenarios.txt`) and not run for ordinary changes. Run them when asked, before a release, or
after a change that can break a quest (a quest map's converter or rebuild, event, dialogue, item or map-transition
code, save format, the scenario runner), and then only the affected quests (`run.py <stem>`).

    cmake --build build --target openyamm -j25
    python3 tests/scenarios/mm9/side_quests/run.py              # every scenario
    python3 tests/scenarios/mm9/side_quests/run.py find_gungnir # some (file stems or prefixes)
    python3 tests/scenarios/mm9/side_quests/run.py --repeat 2   # twice each (determinism)
    python3 tests/scenarios/mm9/side_quests/run.py --reload     # save and load back at each settling step

Logs and the evidence report go to the git-ignored `output/side_quests/mm9/`. Research (actors, lines, events, quest
bits, routes, and where the guide, our scripts and MM9's own scripts disagree) is in `prep/`.

| Scenario | Quest (where) | Story bits set | Prep |
| --- | --- | --- | --- |
| `find_the_saboteur` | Bjarni Herjolfssen, Randver the Storm (Sturmford City) | none | A |
| `take_love_letter_to_kira_the_cold` | Jarl Bjarni to Kira the Cold in Thronheim City and back (boats) | none | A |
| `retrieve_ludwig_s_manuscript` | Ludwig; the sewers under Sturmford walked (logged CLIMB, SWIM, DROP) | none | A |
| `find_out_who_is_spreading_gossip` | Sigmund, Greudach (Drangheim City), Marsaili (Sturmford City) | none | A |
| `get_nicolai_a_job` | Nicolai (Drangheim City), Thorir Mouth at the Gathering (Guberland) | none | A |
| `convince_the_dook_to_leave_guberland` | Markel; the Dook's Castle walked among friendly guards | none | B |
| `sell_brewmaster_smith_s_new_concoction_to_guberland` | the Brewmaster (Frosgard City), Aklai Dorka (Guberland City) | Frosgard's docks freed | B |
| `take_the_news_to_the_temple_of_ratatosk` | Dagfari, Erlend (Thronheim City) | none | B |
| `steal_the_golden_honk` | Fre (Hall of the Gods); the Temple of Honk walked; back by defeat | Arslegard reached, the Great Gate open | B |
| `survive_the_training_hall` | Snorri (Thjorgard City); the Training Hall's cracked wall broken | none | C |
| `retrieve_the_missing_relic` | Leffery (Lindisfarne Monastery); the Wizard's Lab walked (logged TELEPORT steps) | the Training Hall done | C |
| `slay_the_dragon` | the Dragon's Lair (Lindisfarne); the Super Guber Award | the relic returned | C |
| `get_black_orb_of_knowledge` | Ealusaid (Thronheim City); Robinssen in the Wizard's Lab | none | C |
| `get_the_orbs_of_linking` | Brynhildr; the Inventa Storca walked; an orb at each of the six banks | none | D |
| `find_gungnir` | Hanndl (Arslegard); Gungnir in the Inventa Storca; back by defeat | Arslegard reached, the Writ shown | D |
| `clean_out_the_bathhouse` | Jokull (Arslegard); the Bathhouse walked, Ebora's Concubines | Arslegard reached, the Great Gate open | D |

Prep sheets: A `prep/A_sturmford_drangheim.md`, B `prep/B_guberland_frosgard_honk.md`, C `prep/C_dragon_wizards_lab.md`,
D `prep/D_inventa_storca_arslegard.md`. Compass words in the guide follow its map images, which flip many maps
(`output/mm9_site/data/presentations.json`: with `flipV: false` +y is south, with `flipU: true` +x is west); judge a
direction on the map image, never by "+y is north".

## Kept as MM9 had it (revisit)

- **Snorri lets a party skip the Training Hall** (the user, 2026-11-09: stay faithful for now, revisit later). MM9's
  own dialogue data (`NPC6.rude` row 6, choice 3): "Of course." with key 483 and without 301 answers "Come back and
  buy me another drink when you've learned that for yourselves." but goes on to node 15, whose "We're ready for the
  challenge." has no condition and sets 484 (Leffery's dragon talk) without the hall. A fix would be a dialogue
  override sending that row to 999 instead of 15. `survive_the_training_hall.yml` plays the intended order.
