# Handoff: the solo run's power curve (state of 2026-11-15, night)

For the session that takes over the MAW solo run's balance work. Read this file, then
[POWER_CURVE_DIRECTION.md](POWER_CURVE_DIRECTION.md) (the full record: the user's words in §1, §7 and §8) and
[the curve results](../maw/solo_sim/CURVE_RESULTS.md). Everything below is uncommitted in the working tree.

## 1. What this work is

The user plays MAW with one character (the solo run: the `solo` ruleset option, first-person arms, talents) and
wants it "smoother" without being trivial. MAW stays the baseline; solo rules sit on top and never change MAW's own
ruleset or a party game. One day of work: a direction discussion, a rebuilt simulator, one rule built in the game
(the early monster cut), a shelved talent-tree study.

## 2. What the user decided (in order; all 2026-11-15)

1. **MAW is the baseline,** solo rules on top; overriding MAW for solo runs is allowed.
2. **Benchmark:** the solo run about as hard as a party of five, "or 25 % harder, I don't mind"; the goal is to clear
   whole maps (map completion pays).
3. **The start must not be daunting.** "Deterministically nerf a bit the early game." The quest route ("cheese") may
   be the entry price on the highest difficulties, not on the MAW difficulty.
4. **Regeneration is always the first pick** (quality of life, no potion spam). Lone Discipline already lets every
   solo class learn it.
5. **"At no point should the solo char be better than a full party?"** Said as a question, never confirmed as a rule.
6. **Keep the built talents as they are.** "I don't want to implement some additional skills or mechanics on top of
   what we have." The bigger tree (v3) is a shelved study. Earlier the same day the user had asked for a bigger,
   Path of Exile-like tree, one point per 5 levels and more active skills; decision 6 replaced that for now.
7. **The early cut:** "division by 2.5 in the early seems fine", taper "up to you, maybe earlier" than 100. Built,
   then lowered after the user's first play (§4), then given the simulation's 1.4 at level 50 and a linear fade
   to nothing at 75 ("make it linear to like the 75 as you proposed, 1.4 at 50").
8. **The simulator:** "fix the simulator" (done) and "add Regeneration there" (done).
9. **The experience surcharge halved for solo runs:** "yes, 0.25 % for solo only" (MAW's is 0.5 %). Built (§3.2).

Not decided, do not build unasked:
- stronger monsters for a solo in the mid and late game (to keep decision 5 strictly);
- more talent points or front-loaded points;
- anything from talent tree v3.

## 3. What is in the game (uncommitted)

### 3.1 The early monster cut (solo runs only)

- **Data:** `early_monster_cut` in `assets_dev/engine/data_tables/talents.yml`: `[character level, divisor]` pairs,
  linear between, nothing past the last. Now `[[1, 2.5], [5, 2.0], [10, 1.6], [50, 1.4], [75, 1.0]]` (the tail
  lengthened to 75 after the lowering, direction §8).
  A data change needs only a game restart.
- **Table:** `SoloTalentTable::earlyMonsterCut(level)` (`game/rules/SoloTalents.{h,cpp}`).
- **Level:** `MawSoloTalents::earlyMonsterCut(character)` uses the higher of the character's level and the level its
  experience has earned (`game/rules/maw/MawSoloTalents.{h,cpp}`).
- **Runtime value:** `MawRules::soloMonsterCut()` / `setSoloMonsterCut()` (`MawRules.{h,cpp}`), set in
  `MawClassRules::applyClassBonuses` and in `MawClassRules::update`, both only when `options().soloRun`.
- **Effect:** two stages named `solo-early-cut` in `MawCombatRules.cpp`:
  - in `m_damageToCharacter`, right after `damage-recompute`: a monster's hit ÷ cut, before armour, resistances and
    the class's flat cut (falls and traps are not cut);
  - in `m_damageToMonster`, last: the party's hit × cut (`attackerFacts.level <= 0` marks a party hit).
  Monster HP, experience, loot and the inspect screen are untouched; the damage the player sees is the multiplied
  one. Nothing tells the player about the cut.
- **Tests:** `tests/SoloTalentTests.cpp` ("solo run: the early monster cut ..."), `tests/MawGapTests.cpp` ("A solo
  run's early monster cut ..."). Run `./build/tests/openyamm_unit_tests --test-case='*early monster cut*'`; the
  whole MAW and solo group (`--test-case='*solo*,*MAW*,*Maw*,*maw*'`) was 364 cases passing.

### 3.2 The solo experience surcharge (solo runs only)

- **Data:** `experience_surcharge: 0.0025` in `talents.yml` (`SoloTalentTable::experienceSurcharge`).
- **Code:** `MawExperienceCurve` (`game/rules/maw/MawExperienceCurve.{h,cpp}`) is now a class with its surcharge;
  `mawExperienceCurve()` and the old free functions are MAW's 0.5 %. `MawRules::characterCurve()` returns the solo
  curve in a solo run with the line present; `MawExperienceRules::experienceForNextLevel` uses it. Banks, monster
  levels and kill awards stay on MAW's curve. Direction §8 has the details; the simulator does not model it yet.
- **Tests:** `--test-case='*experience surcharge*'` (`tests/MawGapTests.cpp`), the shipped value in
  `tests/SoloTalentTests.cpp`.

### 3.3 `testparty` takes a build written out in full

- `game/debug/MawTestParties.{h,cpp}`: a stage's optional `builds:` map (party id → `stats` (seven), `skills`
  (name: [level, mastery]), `worn` (13 numbers per item)). For a one-member party named there it replaces the generic
  stats, skills and randomly rolled gear.
- `assets_dev/engine/rulesets/maw/debug/test_parties.yml`: the solo stages (`solo_<maw|nightmare|madness>_<10|50|
  100|200|300|500>` and `solo_madness_end`, level 804) regenerated by
  `devdocs/maw/solo_sim/scripts/gen_solo_stages.py` with the simulation's characters for the eight `solo_*` parties.
  Example: `testparty solo_madness_500 solo_champion nightmare beyond_madness horizontal solo`.
- Checked: `rulesets/maw_test_parties.yml` scenario and the testparty unit test pass; the Champion of
  `solo_madness_500` wears its 14 items. **The stages were generated before the Regeneration rerun** (§4.3): their
  builds have no Regeneration and the old Bodybuilding. Regenerate them (§5.4). The `.oysav` saves named
  "Solo ... L500" from 2026-11-14 are older still (random gear).

### 3.4 What other sessions changed in the same files

`MawItemRules.{h,cpp}`, `MawSkillRules.cpp` and `devdocs/maw/MM9_BALANCE_DESIGN.md` are modified by other sessions,
not by this work. In the files this work touched, every hunk is its own (checked with `git diff --numstat`), except
that `devdocs/maw/README.md`'s one added line predates it. The tree is shared: several Claude sessions build in it
(`tests/CMakeLists.txt` was mid-edit by another session once and broke the configure for a minute; wait and retry).

## 4. The simulator (`devdocs/maw/solo_sim/`, all untracked)

Start with its [README](../maw/solo_sim/README.md), section "The power curve run". Work directory of the current
run: `output/maw_solo_sim_v2/` (the 2026-11-14 run stays in `output/maw_solo_sim/`).

### 4.1 What was wrong and is fixed

- Items were kept by rarity, then drop level; now by what is on them (`SoloRoute.cpp` `selectKept`).
- A slot with no fitting loot stayed empty (bare-handed level-10 stage); now a common weapon, shield, bow or armour
  of the content level is bought (`SoloHarness.cpp`, `shopFallback`).
- Crafting ignored previews; now the Hourglass, Eye and Pearl are used as at the Workbench (`craft: smart`).
- Stages: the start (stage 1: level 5 with MAW's starting experience), 10, 20, 30, 50, 100, 150, 200, 300 … 800
  and the end of every run (stage 9999).
- A party-of-five reference run (`party_count: 5`; two Knights, an Archer, a Priest, an Arch Mage) fought by
  `realfight.py` `party_fight`.
- Solo builds train under Lone Discipline (Regeneration weight 0.6, lifted Bodybuilding 0.8; `gen_pool.py`
  `LONE_DISCIPLINE`, `LONE=0` for the cases without it).

Every table of 2026-11-14 (`RESULTS.md`, `proposals/TALENT_TREE_V2_RESULTS.md`, `POWER_GAP.md`, `SOLO_RULES.md` and
the public page) stands on the wrong kits. Do not quote them.

### 4.2 How to rerun

```sh
export SOLO_SIM_DIR=$PWD/output/maw_solo_sim_v2
devdocs/maw/solo_sim/harness/build.sh            # after game code changes that the harness should see
# routes only when the route harness or the stages change (README): run_routes.sh "" then prep/7_party_routes.py,
# then run_routes.sh "_party" (both in the work directory)
devdocs/maw/solo_sim/scripts/rebuild_curve.sh    # cases, harness (80 shards), fights, data_curve.json: ~30 min
python3 devdocs/maw/solo_sim/scripts/agg_curve.py tables > $SOLO_SIM_DIR/curve_tables.md
cp devdocs/maw/solo_sim/scripts/realfight.py $SOLO_SIM_DIR/realfight.py    # the sweeps exec the copy there
python3 devdocs/maw/solo_sim/proposals/party_line_sweep.py > $SOLO_SIM_DIR/party_line.md
CUT_STAGES=1,10,20,30,50,100 CUT_TARGET=party python3 devdocs/maw/solo_sim/proposals/early_cut_sweep.py
```

Run long commands in the background and wait for their notification. A hook refuses `rm` with wildcards or
variables: delete by literal path in a command of its own.

### 4.3 What it says now (with Lone Discipline, no solo rule applied)

- **Solo ÷ party** (monster strength each can face, typical build, Nightmare): 0.34 at the start, 0.52 at level 10,
  0.61 at 20, 0.74 at 50, 1.29 at 100, 1.8 to 2.1 from 200. Classes: the Dragon far above (4 to 10), the Priest far
  below (0.2 to 0.9).
- **The cut that equals the party**, toe to toe on Nightmare: 2.6 at the start, 2.0 at 10, 1.7 at 20, 1.6 at 30,
  1.4 at 50, none at 100. The game's table is lower on purpose (§4.4).
- **Late Beyond Madness** is a wall for the simulated party too.
- The melee kits match MAW's design numbers; casters stay far below MAW's expected HP.

### 4.4 Why the game's cut is lower than the simulator's

The user played a level-15 Dark Elf with a bow and Expert Regeneration on Nightmare (Misty Islands, `oute2.odm`)
with the first table (÷1.9 at that level) and could hardly die. Checked headless on a copy of the quicksave
(direction §8): the cut was right, Regeneration gave about 6 to 8 HP a second in combat, one Bounty Hunter did about
3.9 HP a second. The simulator stands every build in the whole group and has no ranged play, and the party it is
compared with is itself hardly ever in danger at those levels. **The user's play decides the table; do not raise it
from the simulator alone.** A melee solo will find the start harder than the bow user did; that is untested in play.

### 4.5 Known limits

- No ranged approach, kiting, terrain or crowd control: bow and caster builds are undersold. `talentfight.py` has a
  range model but was not rerun on the new kits and stages.
- One party composition, with two weak casters: its line is probably low.
- Expected values: no one-shots, no conditions.
- No shops beyond a plain weapon and armour, no gold, no farming, no Chedian.
- The simulator does not apply the built cut or the built talents (it measures plain MAW with Lone Discipline).
- The CURVE_RESULTS tables above its "Rerun with Lone Discipline" section are the run without Lone Discipline (kept
  in `before_regeneration/` of the work directory).

## 5. Next steps, in the order I would take them

1. **Ask the user how the lowered cut plays** (their save: Nightmare, level 15 to 16, Misty Islands, playthrough
   `8bdc5d4c22aa7912c2ec31588cf8c8d1` in `saves/`; never write there, load a copy with a scenario's
   `load_game: {path: ...}`). Adjust `early_monster_cut` by their word.
2. **A melee start in play:** `testparty solo_nightmare_10 solo_champion nightmare free solo` after step 4, or a
   fresh Knight; the cut may need to differ by attack style if melee is too hard and the bow too easy.
3. **Ranged play in the simulator** (monsters walk in from their aggro range at their speed, shooters stand off):
   the one model gap that produced a wrong recommendation today. `talentfight.py` has the pieces.
4. **Regenerate the test-party stages** from the current run: `SOLO_SIM_DIR=... python3 scripts/gen_solo_stages.py >
   solo_stages.yml`, then replace the block between "# Solo stages (generated ..." and `parties:` in
   `test_parties.yml` (the harness rows must carry 13-number `gear` entries: they do in the current run).
5. **Tell the player about the cut** if the user wants it (the inspect screen shows MAW's numbers; damage text reads
   higher than the sheet).
6. **Mid and late game:** only on the user's word (§2, "not decided"). The measurements for it are in direction §7
   and §8 and CURVE_RESULTS "The party line".
7. **Measure the built talents** on the new kits (they were estimated at ×1.15 at level 100, ×1.35 from 300 by the
   mockups' rough model, not simulated).

## 6. The shelved study: talent tree v3

`level_generation/ui/solo_talents_v3_20261115/` (README there): three live mockups and a viewer, published privately
at <https://claude.ai/artifact/BAHdNVgqL1aTPqvLiD4fFs> (republish `viewer.html` with the folder's files after any
change). 75 nodes, 395 ranks, five paths, a party-line chart. The user chose to keep the built tree instead; keep
the study as reference only. Its `earlyCut` table and its numbers are not the game's.

## 7. Files of this work

| Where | What |
| --- | --- |
| `devdocs/solo_action/POWER_CURVE_DIRECTION.md` | The record: the user's words, measurements, proposals, decisions (§8 is the latest) |
| `devdocs/solo_action/HANDOFF_POWER_CURVE.md` | This file |
| `devdocs/solo_action/README.md`, `TALENT_TREE_V2_BUILD.md` | Links and the cut's line |
| `devdocs/maw/solo_sim/` | The simulator: `README.md`, `CURVE_RESULTS.md`, `harness/`, `prep/` (`7_party_routes.py` new), `scripts/` (`gen_pool.py`, `realfight.py`, `agg_curve.py`, `rebuild_curve.sh`, `gen_solo_stages.py`), `proposals/` (`early_cut_sweep.py`, `party_line_sweep.py`) |
| `output/maw_solo_sim_v2/` | The run (git-ignored): routes, cases, harness rows, `data_curve.json`, `party_line.json`, `before_regeneration/` |
| `game/rules/SoloTalents.*`, `game/rules/maw/MawSoloTalents.*`, `MawRules.*`, `MawClassRules.cpp`, `MawCombatRules.cpp` | The early cut |
| `game/debug/MawTestParties.*`, `assets_dev/engine/rulesets/maw/debug/test_parties.yml` | Exact builds for `testparty` |
| `assets_dev/engine/data_tables/talents.yml` | `early_monster_cut`, `experience_surcharge` |
| `game/rules/maw/MawExperienceCurve.*`, `MawExperienceRules.cpp`, `game/rules/SoloTalents.*` | The solo surcharge |
| `tests/SoloTalentTests.cpp`, `tests/MawGapTests.cpp` | The cut's tests |
| `level_generation/ui/solo_talents_v3_20261115/` | The shelved tree study |

## 8. Working with this user on it

- They judge by playing and by the saves; a number that contradicts their play is wrong until explained.
- They think aloud and revise: take the latest statement, and record their words in the direction document when
  they decide something.
- Explicit mockup requests always get a published viewer page (AGENTS.md).
- Never `git add`, commit or stash unless asked; never co-author trailers.
- Scratch scenarios used today are in the session scratchpad and are not kept; the patterns are in direction §8
  (load a save copy, `actor kill`, `spawn_actor ... near_party`, `hp full`, `advance_runtime`, `hp show`).
