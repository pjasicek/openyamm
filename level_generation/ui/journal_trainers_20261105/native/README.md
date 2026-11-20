# Journal trainer finder and Ledger of Teachers — native implementation (2026-11-05)

The approved [study](../README.md) ([mockup](../index.html)) built into the game for Standard MMMerge and MAW. The
journal's Notes › Trainers category is now a trainer finder; every tavern of a continent sells that continent's
Ledger of Teachers; MAW's skill-tooltip trainer hints name only trainers the party knows. The user's one change
request on the mockup is in: the trainer's map zooms (the Map view's three levels, the Zoom in/out buttons on the
rail, the wheel) and pans by dragging.

## What the player sees

- **Finder** (`JournalTrainerPage`, 364 × 360 logical at the journal's (98, 92)): continent tabs (Jadame, Antagarich,
  Enroth; opens on the party's continent; a gold seal on a tab whose ledger is bought), a search well (live filter over
  skill, mastery, trainer, town, house and map; every word must match; matches are marked behind the text), E/M/G
  toggles, and the list grouped by skill: mastery in the party creation screen's colours (white Expert, turquoise
  Master, gold Grand Master), trainer, town (the outdoor map with the door, or the dungeon or castle). Previous/Next on
  the rail and the wheel turn pages; the page number sits under the status strip. The search text is the journal's
  `notesSearch` (shared with the other note categories; Escape leaves the field).
- **Status strip** (the Map view's note bar): the hovered trainer's house, map and requirement (skill level from the
  topic or `SkillRules::masteryRequiredLevel`, price from the topic or `masteryTeacherStandardCost` through
  `SkillRules::masteryTeacherCost` for the active member, so MAW prices show, and "<previous mastery> first"), else the
  count.
- **Map**: a click shows "<Mastery> <Skill> · <trainer>", Close, and the trainer's outdoor map (`icons_x2/<map stem>`,
  loaded on demand) framed like the Map view with a pulsing marker and a label on the house door, or on the entrance of
  the dungeon or castle the trainer teaches in ("Entrance: <dungeon>"). Zoom in/out replace Previous/Next on the rail;
  wheel zooms; drag pans; Close or Escape returns to the list on the same page. A house with no outdoor way in says
  "No map of this place yet."
- **Knowledge**: without the continent's ledger the list shows only trainers the party has found — the teacher autonote
  (`teacher_autonotes.txt`), or for MM6 teachers, which have no autonotes, the journal map pin talking to them leaves
  (`tryAddRuntimeMapNote`, id continent·1000 + rank·100 + skill id) — and ends with "You have found N of the M
  trainers on <continent>. The Ledger of Teachers names them all: ask for it in any tavern on <continent>."
- **Tavern**: every tavern (`HouseServiceType::Tavern`) of a continent offers "Ledger of Teachers" while that ledger is
  not bought; it opens a sub-menu with the description and "Buy the ledger: 2000 gold". Buying takes the gold (refused
  with the innkeeper's line when short), records the ledger, fills every teacher autonote of the continent, returns to
  the tavern's topics (the topic is gone) and says so.
- **MAW**: moved trainers (`rulesets/maw/data/npc_extra_houses.yml`) appear at their extra houses; Cover, Mana Shield,
  Enlightenment and Retaliation read "learned at skill N · no trainer" (`SkillRules::teacherlessMasteryLadders`,
  MAW's `mawSkillMasteryLadder` for the game's mode). The trainer hints name the nearest *known* teacher, or say
  "No trainer known yet: a tavern sells the Ledger of Teachers." with the level requirement still shown.

## Files

| File | What |
| --- | --- |
| `game/gameplay/TrainerDirectory.{h,cpp}` | Shared trainer directory: `TrainerPlaceTable` (trainer_places.txt), `TeacherLedgerSettings` (teacher_ledger.yml), `TrainerDirectory::build` from the loaded tables, `forParty` (scripted topic slots, moved and gone NPCs), `TrainerLinks`/`pickTrainers` ranking (moved out of the MAW module), `trainerKnown`, `trainerSearchMatches`, `buyTeacherLedger`. |
| `game/ui/GameplayJournalTrainers.{h,cpp}` | The finder page and map: layout, hit targets, paging, zoom/drag, rendering. |
| `game/ui/GameplayPartyOverlayRenderer.cpp` | Notes view: the Trainers category renders the finder (the old trainer-note text and MM6 pin listing are gone). |
| `game/gameplay/GameplayOverlayInputController.cpp` | Journal input: `TrainerFinder` targets, zoom buttons on a trainer map, wheel, drag, Escape. |
| `game/ui/GameplayJournalMapUi.h` | `GameplayJournalMapView` overloads of the journal map transform and clamp (the Map view and the trainer map share them). |
| `game/gameplay/HouseInteraction.{h,cpp}`, `game/gameplay/GameplayDialogController.cpp`, `game/events/EventRuntime.h` | `HouseActionId::OpenTeacherLedgerMenu`/`BuyTeacherLedger`, `DialogueMenuId::TeacherLedger`, `tavernTeacherLedgerContinent`. |
| `assets_dev/engine/scripts/common/event_support.lua`, `assets_dev/worlds/mm7/events/common/mm7_common.lua` | `HouseAction.OpenTeacherLedgerMenu` (33) and `BuyTeacherLedger` (34); Emerald Island's tavern topic filter keeps the ledger. |
| `game/party/Party.{h,cpp}`, `game/maps/SaveGame.cpp` | `teacherLedgers` state, NPC override accessors, the trainer directory pointer; save version 153. |
| `game/data/GameDataLoader.cpp`, `GameDataRepository`, `GameSession.cpp`, `GameApplication.cpp`, `ScenarioRunner.cpp` | Loading and binding the directory to the party. |
| `game/rules/SkillRules.*`, `game/rules/maw/MawSkillRules.*` | `teacherlessMasteryLadders`. |
| `game/rules/maw/MawTrainerHints.{h,cpp}`, `MawRulesFactory.cpp` | Hints on the shared directory, gated by `trainerKnown`. |
| `assets_dev/engine/ui/gameplay/journal.yml` | `JournalTrainerPage`. |
| `assets_dev/engine/data_tables/teacher_ledger.yml` | Price (2000) and the innkeeper's texts; a ruleset may replace the file. |
| `assets_dev/engine/data_tables/trainer_places.txt`, `tools/trainer_places.py` | Generated house locations. |

## Data: runtime list, generated locations

The **trainer list is built at runtime** from tables the game loads: npc.txt topic slots that resolve as
mastery-teacher topics (`resolveMasteryTeacherTopic`: teacher_topics.txt or MM8's 300–416), house_data.txt,
map_stats.txt continents, teacher_autonotes.txt and the ruleset's extra houses. `TrainerDirectory::forParty` applies the
party's NPC state, so the Grand Master lessons MMMerge's map-load script (`Global_mm6_mmmerge.lua`
`enrothGrandmasterTeacherTopics`, which runs on every map load) sets as NPC topic overrides are listed, and the
QBit-gated Grand Master Axe shows only once the script gives it. The last party-specific directory is cached by a
fingerprint of the overrides. Ruleset patches and world packages are therefore picked up without regenerating anything.

**Only locations are generated**: `python3 -I tools/trainer_places.py` (about 25 s; `--check` fails when the file is
stale) writes `assets_dev/engine/data_tables/trainer_places.txt`, one row per teacher house (houses of npc.txt teachers,
of the script's Grand Masters and of MAW's extra houses): `House, Map, Kind, Marker map, X, Y, Entrance chain`. `door`:
the centre of the BModel faces and entities of the map that carry the house's `EnterHouse` event (the scene yml's
interactive faces when it has one); `entrance`: the shortest chain of map moves (`MoveToMap`, exported
passage/teleport/dungeon actions) from an outdoor map to the indoor map, preferring the house's continent, marked at
that outdoor map's entrance event; `indoor`: no outdoor way in. Positions are world coordinates; the map view places
them with the outdoor minimap transform (±32768, V flipped). A world package may add rows with a `trainer_places`
append contribution in its `world.yml` (same columns; later rows replace earlier ones). Today: 328 houses, 307 doors,
21 entrances. Left out: house 929 (Poundlin Lotts, Expert Shield, Erathia: door event 74 of 7out03.odm is on no face),
listed in the staleness test's skip list.

**Staleness test** (`tests/TrainerDirectoryTests.cpp`, "every teacher house of the game's tables has a trainer
place"): every house the runtime list produces (with MAW's extra houses) must have a row or be on the commented skip
list; a moved or added teacher fails it, and rerunning the tool fixes it.

## Ledger state: party save state, not QBits

The bought ledgers are `Party::Snapshot::teacherLedgers` (continent ids), saved since save version 153
(`SaveVersionTeacherLedgers`; older saves have none). QBits were considered: they are global save state too, but
there is no declared engine QBit range (only MAW's 10001–10099 and MM9's world range), a QBit would need a registry row
in quests.txt (and must not show as a quest), and scripts could clear it by accident. A purchase record is plain party
state like Arcomage wins, with an explicit save version. The teacher autonotes the purchase fills are ordinary
autonotes, so the journal's other systems see them.

The debug console's `ledger get` / `ledger set <1|2|3|all>` gives ledgers (with their notes) for testing.

## Tests

- Unit (`./build-b/tests/openyamm_unit_tests --test-case='*trainer*,*Trainer*,*Ledger*'`): place table parsing; the
  directory (door map override, entrance marker, extra houses, notes, requirements, continent notes); `forParty`
  (scripted topic added, lesson removed, moved and gone NPCs, cache); knowledge (note, MM6 pin, ledger); search; ledger
  purchase (refused when short, gold, notes of that continent only, snapshot round trip); MAW hints gated by knowledge;
  the real-data staleness test and per-continent counts; the existing MAW trainer hint tests on the shared types.
- Scenarios (`./build-b/game/openyamm --headless-run-scenario …`): `tests/scenarios/journal/teacher_ledger_jadame.yml`
  (topic offered, description, refused at 1500 gold, bought: 2000 taken, topic gone, notes 128/130 set, other
  continents untouched, kept through save/load, not offered again), `teacher_ledger_enroth.yml` (MM6, no notes),
  `teacher_ledger_emerald_island.yml` (MM7's tavern topic filter keeps the topic), and
  `tests/scenarios/rulesets/maw_teacher_ledger.yml` (MAW, save/load). New scenario asserts: `autonote: {id, present}`,
  `teacher_ledger: {continent, bought}`, and `dialog: {action_label_present, action_label_absent}`.

## Captures

Engine-native captures at 1600×900 from `tours/` (run with `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated
<name> --binary build-b/game/openyamm --world mm8 --map out01.odm --set debug.menu_input_tour_path=<tour>`; `maw.yml`
adds `--ruleset maw`):

- `images/01-finder-list.png` — Jadame, a third of its notes found, a row hovered (status: house, map, requirement);
  Enroth's tab carries the ledger seal.
- `images/02-finder-list-last-page.png` — the closing ledger line.
- `images/03-finder-search-sword.png` — search "sword", matches marked, Master row hovered.
- `images/04-finder-map.png`, `05-finder-map-zoomed.png`, `06-finder-map-dragged.png` — the trainer's map, the marker on
  the door of Stormlance Residence (Garrote Gorge), zoomed twice and dragged.
- `images/07-finder-back-to-list.png`, `08-finder-enroth-ledger-grandmasters.png` — Close back to the list; Enroth with
  its ledger and the G toggle (includes the script-given Grand Masters).
- `images/10-tavern-topics.png`, `11-tavern-ledger-topic.png`, `12-tavern-ledger-bought.png`,
  `13-finder-after-ledger.png` — the tavern topic, description and price, the purchase, and Jadame's full list after.
- `images/20-regression-potion-notes.png` … `23-regression-story.png` — the other note categories, Map, Quests and
  Story unchanged.
- `images/30-maw-finder-ladders.png` — MAW: Mana Shield's level ladder rows.

## Known gaps and differences from the mockup

- The mockup's clear (×) button in the search well is not drawn; Backspace clears.
- After buying, the mockup's temporary "Open the journal's Trainers" topic is not offered (the innkeeper's line says the
  notes are filled).
- Rows have no keyboard navigation (the mockup's arrow keys turn pages; the native finder uses Previous/Next and the
  wheel).
- The search is shared with the other note categories (one `notesSearch`).
- Poundlin Lotts (house 929) has no marker ("No map of this place yet"); 11 NPCs with lesson topics but no house are not
  listed (as in the study).
- Map images are drawn square (the 1024×1020 ones are stretched by 0.4 %).
- `trainer_places.txt` and `teacher_ledger.yml` are new engine tables the game requires: the git-ignored Hesper stage
  (`output/hesper_stage`) needs a restage (`stage.py` copies new engine tables) before `WorldMissileTests`' staged-Hesper
  case loads again.
- Ranking of the finder list is alphabetical by skill, mastery, name; the hint keeps MAW's nearest-first ranking.

## Continent journals and Chedian (2026-11-10)

Quests and ordinary notes now have Jadame, Antagarich, Enroth, Chedian and Shared tabs, using the trainer tab art.
They open on the current continent; recipes open on Shared. Changing continent resets pagination. Quest and note
selections are independent, and the existing note search still applies within the selected continent/category.

`english/quests.txt` column `Owner` now names the continent (or `Shared`), rather than the original developer.
The old names are preserved in `Author`, after the required/forbidden QBit columns. Former simple-bit rows explicitly
require that same bit; quest text and activation conditions are unchanged. MM9's overlay generator emits `Chedian`.
`english/autonote.txt` has the same `Owner` column after Category. Recipes and general counters are Shared; the three
obelisk puzzles and geographical notes belong to their own continent. Empty ownership on custom entries means Shared.
This is table metadata, so existing saves need no migration.

Chedian is continent **5** (4 is Between Time). Its finder reads lessons from the existing MM9 skill-trainer table
and racial-ability definitions; composite source skills become their individual shared skills. The original
`ActorOwnership: scheduled` labels in the source audit are historical: the rework has an empty teacher schedule table
and places these teachers in the installed scenes. `generate_mm9_trainer_places.py` indexes those actual positions,
including a teacher present on two maps, without loading other maps at runtime:

```sh
python3 tools/mm9_import_discovery/generate_mm9_trainer_places.py
python3 tools/mm9_import_discovery/generate_mm9_trainer_places.py --check
```

Run it after moving teachers or rebuilding their maps. It fails if an ordinary or racial teacher has no position.
The runtime validates identities, skills, maps, coordinates and painted-map availability. A clicked teacher uses
that map's existing painted image, world bounds, axis directions and floor at the teacher's height. Zoom and drag
use the same transform as the ordinary journal map. The marker labels the person. Long skill groups paginate rather
than overflowing the page.

Talking to an MM9 teacher records a normal saved journal pin (`90000 + RUDE id`, below the personal-note range).
Existing dialogue-choice records also establish discovery for older saves. A Chedian tavern sells the same 2000-gold
ledger and reveals its full directory. The service-venue table's appended `map` column binds each venue to its map;
the loader validates this reference and uses the ordinary map-continent lookup. The debug command accepts `ledger set 5`.

Focused coverage: `TrainerDirectoryTests` (MM9 locations, maps, racial lessons, discovery, old dialogue records,
party overrides, ledger and snapshot), `PartyRegressionTests` (filtered conditional quests), and
`tests/scenarios/journal/teacher_ledger_chedian.yml` (real dialogue discovery and tavern purchase/save/load).

Validation: the development game and unit targets build; 39 focused journal/trainer/mercenary unit cases pass
(4000 assertions); the Chedian, Jadame, Enroth, Emerald Island and MAW ledger scenarios and MM6–MM9 world-switch
scenario pass. MM9 story segment 01 passes. Desktop OpenGL/NVIDIA captures are in
`output/journal_continents_review/` (continent filters, recipes, all three obelisk puzzles, Chedian list and painted
teacher map with zoom/drag). A wider unit selection still has unrelated stale shop-capacity and MM9 vendor-count,
price and stock-version expectations in `HouseShopLedgerTests` and `Mm9RudeDialogueTests`.

Chedian journal content follows the existing MM9 world-table lifecycle: it is loaded while MM9 is active. Its saved
discoveries and ledger survive world switches. Other worlds do not load the MM9 dialogue/services just for this UI.
Live actor service venues are excluded from generated house-lobby mercenary placement, so giving them map references
does not inject MMerge recruits into MM9 talks.
