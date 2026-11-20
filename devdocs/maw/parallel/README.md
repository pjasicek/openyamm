# MAW parity: parallel sessions

Three sessions close the open rows of [GAPS.md](../GAPS.md) at the same time, in one working tree. Each owns a set of
GAPS sections and the files that come with them. Phase 9 (challenge modes, seeded Madness bosses, randomizer) is out
of scope for all three.

| Session | Owns (GAPS.md) | Brief |
|---|---|---|
| A, the coordinator | §3 monsters, §4 skills and trainers, §10 packaging/data/tests, C.1 docs, §11 decisions | (the first session) |
| B | §5 spells and auras, §6 classes, races, creation | [SESSION_B.md](SESSION_B.md) |
| C | §7 alchemy and crafting, §8 content and maps, §9 interface, plus L4.5 from §2 | [SESSION_C.md](SESSION_C.md) |

## Read first

1. [HANDOFF.md](../HANDOFF.md): the goal, the rules hooks (`game/rules/*Rules.h`, the MAW overrides in
   `game/rules/maw/`), the ruleset package (`assets_dev/engine/rulesets/maw/`) and the phase notes.
2. [GAPS.md](../GAPS.md): your sections, plus §11 (open decisions) and its header (priorities, statuses).
3. [DEVIATIONS.md](../DEVIATIONS.md): what we deliberately do differently. Do not "fix" a recorded deviation.
4. The specs for your area under `devdocs/maw/` (COMBAT_SPEC, CLASSES_SPELLS_SPEC, SKILLS_SPELLS_ALCHEMY,
   CRAFTING, MAPS_CONTENT, ITEMS_DATA, `data/*.yml`). They are drafts: MAW's code at
   `/home/pjasicek/github/Maw-Mod-MMMerge` (commit ef23ee17) is the truth. Where MAW's text and MAW's code disagree,
   keep MAW's code (or the current behaviour), add a §11 "decide" row and tell the coordinator.

## Hard rules

- Never copy MAW Lua; reimplement in C++ (or YAML/TXT data) in the repository's style (AGENTS.md: C++20, 120
  columns, braces on new lines, `m_` members, `p` pointer prefixes, explicit types, no `[[nodiscard]]`).
- The Standard ruleset's behaviour does not change: put MAW behaviour behind a rules hook whose Standard default does
  what the engine did. A hook added for MAW costs Standard nothing (no extra random draws on Standard paths).
- No `git add`, `commit`, `stash`, `restore --staged` or `reset`. No Vulkan builds. Do not edit generated Lua events.
- **Your own build directory**: `cmake -S . -B build-b` (or `build-c`), then
  `cmake --build build-b --target openyamm openyamm_unit_tests -j12`. Never build in `build/`: concurrent builds in
  one tree leave stale objects. Run your tests and scenarios from your own build.
- Desktop game runs only when no `openyamm` process runs (`pgrep -x openyamm`); headless scenarios and unit tests
  may run beside anything.

## Shared files: claim before editing

Two sessions rewriting the same file lose edits. Before you edit any of these, send the coordinator a one-line
claim ("B: editing MawCombatRules.cpp, Shrinking Ray stage") and wait for the go-ahead; say when you are done.

- `game/rules/CombatRules.h/.cpp`, `game/rules/maw/MawCombatRules.h/.cpp`, `game/rules/maw/MawRules.h/.cpp`,
  `game/rules/maw/MawMonsterRules.*`, `game/rules/maw/MawItemRules.*`
- `game/gameplay/GameplayRuntimeInterfaces.h`, `game/party/Party.h/.cpp`, `game/maps/SaveGame.cpp`
- `game/outdoor/OutdoorWorldRuntime.*`, `game/indoor/IndoorWorldRuntime.*` (claim the function, not the file, when
  the change is small)
- `assets_dev/engine/rulesets/maw/ruleset.yml`, `assets_dev/engine/rulesets/maw/content/items_patch.txt`
- `tests/MawGapTests.cpp`, `tests/RulesetTests.cpp`, `tests/PartySpellTestHarness.h`
- `devdocs/maw/DEVIATIONS.md`, `devdocs/maw/HANDOFF.md`

Files only your area touches (for B: `MawSpellRules.*`, `MawClassRules.*`, `MawClassSpells.*`; for C:
`MawPotionRules.*`, `MawCraftingRules.*`, crafting and UI files) need no claim.

## Numbers you must not collide on

- DEVIATIONS rows: A continues from 75, **B uses 100-129, C uses 130-159**. Keep the table's columns.
- SaveVersion: 108 is taken. **B may use 109, C 110**, and only after telling the coordinator (bump `SaveVersion` in
  `game/maps/SaveGame.cpp` together with your gate constant, and gate every new field).
- Scenario files: `tests/scenarios/rulesets/maw_<area>_*.yml`, new files only.

## How to work a row

1. Read MAW's code for it and our current code; decide what "parity" means. Small fix: do it. A real disagreement
   with a spec or a design question: §11 row, ask the coordinator.
2. Implement behind the right hook. Comments cite the MAW source as the existing code does (`(SP:824-1003)`).
3. Test it:
   - Formulas and rules: doctest cases in **your own file** (B `tests/MawSpellClassTests.cpp`, C
     `tests/MawContentUiTests.cpp`), added to `tests/CMakeLists.txt` (a claim: tell the coordinator). Patterns:
     `tests/MawGapTests.cpp` (rules objects, `PartySpellTestWorldRuntime`, a recording test world).
   - In a map, through the real paths: headless scenarios, see `tests/scenarios/README.md` and
     `tests/scenarios/rulesets/maw_combat_rules.yml`, `maw_bosses.yml` (`new_game_flow` with a MAW ruleset,
     `spawn_actor` with `near_party` and `boss_affix`, `party_attack` with `record`/`ratio_to`, `damage_actor`,
     `advance_runtime`, `assert: {actor_count: ...}`). Run one with
     `./build-b/game/openyamm --headless-run-scenario <file>`. New scenario steps go in `game/scenario/` (a claim).
   - UI: engine screenshots (AGENTS.md "Native Game Visual Checks"; the `debug.menu_input_tour_path` scripted tour).
4. Mark the row in GAPS.md: `done 2026-10-24` (or the day), `dev N`, `decide (§11 D.N)`. Edit only your own
   sections' rows; a new §11 row goes through the coordinator.
5. Before you report a batch: your unit tests, the whole unit suite
   (`./build-b/tests/openyamm_unit_tests`; 7 failures are known and unrelated: darkmoor previews, flour sack,
   recovery enchant, demon LOD, mm8 Ogre/Vampire/slime) and the ruleset scenarios
   (`tests/scenarios/rulesets/*.yml`, all must pass).

## Talking to the coordinator

`ListAgents` lists the local sessions; the coordinator is the one working on "MAW parity" (ask the user if several
match). `SendMessage` it for claims, numbers, §11 questions and anything that crosses areas. Keep messages short and
concrete; the coordinator answers between steps. When a batch is finished, send a summary: rows done, deviations
added, tests and their results, anything left open and why.
