# MAW solo-class simulation

Which classes can play MAW as a party of one, at character levels 10, 50, 200 and 500, on all eight difficulties
(Normal, MAW, Hard, Hell, Nightmare, Doom, Road to Insanity, Beyond Madness). Built 2026-11-13/14 for the question
"which MAW classes are best solo"; the findings are in [RESULTS.md](RESULTS.md).

Every number comes from OpenYAMM's own MAW code, run through a doctest harness linked against the game library: the
character sheet, MAW's attack resolver, monster sizing, experience, loot, chests and crafting. A simulated solo
playthrough clears the real MM6–MM8 maps (as the game spawns them on each difficulty), each build then wears the best
gear that playthrough's loot offers, crafted with the materials it found, and fights the actual monster groups of the
maps it has reached. Python scripts do the fights (expected values in 0.1 s steps) and the tables.

- Page: <https://jasicek.net/openyamm/maw-solo/> (public), also a private claude.ai artifact
  (<https://claude.ai/artifact/4wpJoT3RA9xF4cMJxSmhys>). [page/deploy.sh](page/deploy.sh) publishes it.
- Proposals for making a maxed solo clear Beyond Madness (power gap, talents, items, endgame loop) and their merged
  recommendation: [proposals/README.md](proposals/README.md).
- Work directory: `$SOLO_SIM_DIR`, default `output/maw_solo_sim/` (git-ignored, about 580 MB with every
  intermediate). It holds the binary, the inventory logs, the routes, every harness output and the page data. The
  2026-11-14 run is kept there.

## The power curve run (2026-11-15)

The second pipeline, built for [the solo power-curve direction](../../solo_action/POWER_CURVE_DIRECTION.md): the same
simulation with a kit a player would wear, a party-of-five reference run, every stage of the route and "map
cleared" measures. Results: [CURVE_RESULTS.md](CURVE_RESULTS.md). Its work directory is `output/maw_solo_sim_v2/`
(the 2026-11-14 run stays in `output/maw_solo_sim/`); `inv/`, `caps.txt`, `caps2.txt` and `monsters.json` were copied
from there.

```sh
export SOLO_SIM_DIR=$PWD/output/maw_solo_sim_v2
devdocs/maw/solo_sim/harness/build.sh
python3 devdocs/maw/solo_sim/prep/5_routes.py          # route specs with the level stages of prep/_common.py
# the eight solo routes (ROUTE_SPEC=route/route_<dk>.json), then:
python3 devdocs/maw/solo_sim/prep/7_party_routes.py    # the party's routes, staged where the solo's stages fell
# the eight party routes (ROUTE_SPEC=route/route_<dk>_party.json), then:
devdocs/maw/solo_sim/scripts/rebuild_curve.sh          # cases, harness, fights, data_curve.json and its tables
```

What changed against the first pipeline (which the sections below describe):

- **Stages.** Level 1 (the start, before the first map: a solo starts at level 5 with MAW's 10,000 experience), 10,
  20, 30, 50, 100, 150, 200, 300 … 800 and the end of every run (stage 9999), not only 10/50/200/500. Skill, alchemy
  and potion tables follow the character's actual level.
- **Items kept by what is on them** (`SoloRoute.cpp` `selectKept`): per item kind the union of the highest rarity, the
  highest drop level, the highest item power, and for every enchantment type the strongest first and second
  enchantment. Before, one list by rarity and then drop level threw away well-rolled items and kept low-level
  legendaries (the best two-handed axe of a level-500 Knight was of drop level 55).
- **Bought weapon and armour.** A weapon, shield, bow or body armour the loot does not hold is bought as a common
  item of the content level, of the rung that level sells. Before, the slot stayed empty: at the level-10 stage most
  builds fought bare-handed or unarmoured, so the old level-10 figures are far too low.
- **Crafting as at the Workbench** (`SoloHarness.cpp`, `craft: smart`, the default; `craft: found` is the old order):
  the Hourglass's and the Eye's results are previewed and taken only when they make the build stronger, a Pearl
  removes the enchantment the player picks, and a gem or Crafting Cube moves the item's craft stream on for another
  look.
- **The party reference** (`party_count: 5` in a route spec): five members share every award as MAW shares it, the
  bank grows as MAW grows it, and the run is staged at the numbers of cleared maps where the solo reached its
  stages. Its members (`gen_pool.py` `PARTY`: two Knights, an Archer, a Priest, an Arch Mage) deal the loot round
  among those who can wear each kind and share the materials. `realfight.py` `party_fight` fights them together:
  monsters spread their attacks over the living members, the Priest heals with Heal and Power Cure.
- **Measures** (`agg_curve.py`): maps fully cleared (potions allowed, a group split in fours when it cannot be beaten
  whole), potions per 100 monsters, seconds per monster, party members lost.
- **Sweeps on the curve run** (`proposals/`): `early_cut_sweep.py` (the monster cut that makes a solo's whole groups
  as beatable as the party's) and `party_line_sweep.py` (solo strength ÷ party strength at every stage).
- **Harness rows** also carry the worn kit (`gear`), the healing spells (`heals`) and MAW's expected character of the
  character's own level (`own_exp_health`, `own_exp_power`, `own_mon_hp_b`, `own_mon_dmg_b`).

## Layout

| Path | What |
| --- | --- |
| `harness/SoloHarness.cpp` | doctest cases `solo harness` (one solo character per case: sheet, gear, potions, numbers out) and `solo caps` (class skill caps, HP/SP per level). |
| `harness/SoloRoute.cpp` | doctest cases `solo route` (the playthrough) and `solo monsters` (the monster table as JSON). |
| `harness/build.sh` | Compiles both with the unit tests' flags and links them with the unit-test objects and the game and engine libraries into `<work>/solo_harness`. |
| `prep/1_inventory_scenarios.py` … `prep/6_tables.sh` | Inputs: map list, headless inventory of every map's spawns, chests, quests, routes, class tables, monster table. |
| `prep/caps.yml`, `prep/caps2.yml` | The classes whose caps are dumped: final classes; base and first-promotion classes. |
| `scripts/gen.py` | The 22 builds (class, race, portrait, skill weights, gear plan), the skill allocator, stats, potions; also the first-version random-gear spec. |
| `scripts/gen_pool.py` | The playthrough cases: each build at each stage, difficulty and seed, with that run's loot pool, materials, class at that stage and the attacker-level grid. |
| `scripts/sim.py` | Generic pack fights (B-tier physical melee monsters, packs of 4, 10, largest survived). |
| `scripts/realfight.py` | Real-group fights against the actual groups of the maps around each stage. |
| `scripts/agg2.py`, `agg_route.py`, `agg_real.py` | Medians over seeds: first version, playthrough, real groups. |
| `scripts/rebuild_route.sh` | Everything after the routes: cases, harness runs, both fight models, aggregates, page data. `rebuild_tail.sh` is its second half (from the harness outputs on). |
| `scripts/results_tables.py` | Prints the measured tables of RESULTS.md from the page data. |
| `scripts/simdir.py`, `prep/_common.py` | The work directory and paths. |
| `page/template.html`, `make_page.py`, `deploy.sh` | The page (data inlined at `__DATA__`), its build and its publication. |
| `proposals/` | Design proposals built on these results; `power_gap_sweep.py` scales a build's numbers in realfight to measure the gap. |
| `scripts/talents_v2.py`, `gen_talent_pool.py`, `talentfight.py`, `page/talent_data.py` | Talent tree v2: the trees and allocation, the harness variants (talents, Bodybuilding cap), the fight model with range, actives, keystones and Legend lines, and the page data. Results: `proposals/TALENT_TREE_V2_RESULTS.md`. |
| `proposals/discord_notes/` | Reading notes from the MAW #balance-discussion export, merged in `proposals/DISCORD_DISTILL.md` (slices made by `scripts/discord_flatten.py`, `scripts/discord_context.py`). |
| `validation/*.yml` | Headless scenarios used to check the harness against the running game (see Validation). |

## Running it

```sh
cmake --build build --target openyamm_unit_tests -j25 && cmake --build build --target openyamm -j25
devdocs/maw/solo_sim/harness/build.sh                    # 20 s
P=devdocs/maw/solo_sim/prep
python3 $P/1_inventory_scenarios.py && $P/2_run_inventory.sh     # 24 headless scenarios, about 10 min
python3 $P/3_parse_inventory.py && python3 $P/4_mapdata.py && python3 $P/5_routes.py
$P/6_tables.sh                                           # caps.txt, caps2.txt, monsters.json
cd output/maw_solo_sim && for dk in normal maw hard hell nightmare doom insanity madness; do
  ROUTE_SPEC=$PWD/route/route_$dk.json ROUTE_OUT=$PWD/route/out_$dk.jsonl ./solo_harness --test-case="solo route" \
    > route/run_$dk.log 2>&1 & done; wait; cd -           # 5 seeds each, about 6 min in parallel
devdocs/maw/solo_sim/scripts/rebuild_route.sh            # about 15 min
python3 devdocs/maw/solo_sim/page/make_page.py           # or page/deploy.sh to publish
python3 devdocs/maw/solo_sim/scripts/results_tables.py   # the tables for RESULTS.md
```

The first-version comparison (random rarity gear at a pace estimate, the page's "First version" modes) is
`python3 scripts/gen.py caps.txt spec.yml meta.json` in the work directory, the spec copied per gear seed (7, 101,
202, 303 in `case.gear.seed`), `SOLO_SPEC=spec_<seed>.yml SOLO_OUT=out_<seed>.jsonl ./solo_harness --test-case="solo
harness"`, `sim.py` three times per seed (plain, `MAW_FLAT=1`, `OPENER=3`), then `agg2.py` → `data.json`.
`rebuild_route.sh` merges it into the page data unchanged.

## The pipeline

### 1. Inventory of the maps (prep 1–4)

- `inv/maps.json`: the 189 MM6–MM8 maps with MAW level bands, from `tools/maw_site/world_maps.py` (arenas left out of
  the route).
- One headless scenario per world and difficulty: a one-member MAW game, banks zeroed (`ruleset banks 0 0 0 0`), the
  map monster table dumped (`ruleset mapmonsters <tsv>`), then every map loaded and `actor remaining` listing each
  spawned actor with id, position and HP. This captures MAW's density per difficulty, bosses (HP over twice the row's)
  and uniques exactly as the game spawns them. Nightmare: 21,187 actors on 189 maps; Normal 16,597.
- `inv/mapdata.json`: each map's chests from its scene file (type, flags, raw item records) and its script's
  `AddValue(Experience)` awards.

### 2. Routes (prep 5)

`route/route_<dk>.json` per difficulty: every map's actors as [monster id, HP ratio to its row, group], chests,
quests, five seeds, stages 10/50/200/500.

- Group: the actors standing within 512 units of each other (z counted twice), union-find over spawn positions.
  Median group size 3 (MAW) to 5 (Beyond Madness); the largest tenth 5–11.
- Quests: one reward per quest event, the largest `AddValue(Experience)` in each evt function of `Global.lua` and every
  map script, because a quest's branches are alternatives ("Promotion to Champion" has four rewards, one is paid). 196
  rewards, 9.44 M experience before MAW's bonus. An earlier count of every award (272, 11.4 M) double-counted.

### 3. The playthrough (`solo route`)

Per difficulty and seed, a fresh MAW state with a one-member party:

- Picks the uncleared map whose median B-tier monster level is lowest at the current banks
  (`MawRules::mapMonsterTable`), kills every spawned actor, opens every chest, takes the map completion.
- Kill experience: MAW's award `exp × monHP / monsterHealth(min(charLevel, totalLevel))`, capped at (lvl+1)·1000;
  the solo gets the whole award, the bank `addBankedExperience` gets Σawards/5 (as for any party size). There is no
  penalty by character level: the shrink against easy monsters is measured against the bank.
- Quests: smallest first, spread along the route by map count; MAW pays `value·(1+P/100) + 500·P` × 5/partyCount, P
  = levels banked on the other continents. Map completion: fully to the bank, ×5 to the solo, plus a Crafting Cube and
  two gems of tier min(⌈level/25 + 0.5⌉, 16).
- Loot: `corpseLoot` and `rollMonsterCarriedLoot` per actor, chests through `buildMaterializedChestView` (random
  records at the remapped treasure level, −7 = artifact), reagents and crafting materials kept.
- Character level from MAW's curve `mawLevelForExperience` (step `1000·L·max(1 + (L−100)·0.005, 1)`).
- Snapshots when the character passes each stage and at the end: banks, maps, kills, chests, a top-40 item pool per
  equipment kind, materials, experience by source, the last five cleared maps and the next five with their actors
  ([id, level, HP, attack-1 damage, group, boss, physical base, magic base] at the banks then).

Where a full clear ends below 500 (all difficulties but Nightmare and Beyond Madness), the end snapshot stands in for
the level-500 stage at the level reached (469–498), labelled as such on the page.

### 4. Characters (`gen_pool.py` → `solo harness`)

For every build, stage, difficulty and seed:

- Class at that stage: base class until 15 % of one continent's maps are cleared, then the first promotion, the final
  class at 40 %; Elder (×1.25 HP and SP per level) with two continents past 40 %, Ultimate (×1.5) with three
  (`promotion_worlds`, MAW's `promotionFactor`). The promotion quests themselves are not played.
- Skill points: Σ(5 + ⌊i/10⌋) per level (plus Transcendence from potions past level 200); a raise to s costs s, the
  shared set (weapons and schools; hybrids share schools only) costs ⌈s/(1+n)⌉. Points go to Alchemy first, then by the
  build's weights; caps and masteries from the class at that stage and the difficulty's thresholds (free 4/7/10,
  horizontal and Doom 6/12/20, Road to Insanity 8/16/25, Beyond Madness 10/24/40). Solo auto-mastery at 1/4/7/10 for
  Alchemy, Identify, Repair, Merchant, Perception, Disarm and Identify Monster.
- Stats per build kind, plus Pure potions past level 200. Potions: aura skill 50(f−1) (DoG/DoP 70), level 0.5·P·f,
  f = 0.75 + 0.75·min(P,200)/200; Cure Wounds 20 + 25 % and Divine Cure 50 + 35 % of the expected HP at power P;
  Regeneration potion √maxHP × ⌊P/2⌋^1.25 × 0.005. Potion power: best reagent of the content level (drop level / 3,
  base 30, catalyst 45) plus Grandmaster Alchemy.
- Gear from the run's loot pool: per slot the item that makes the build strongest (its damage × MAW's vitality, leech
  counted, casters' mana weighted), greedy in two passes, gated by the portrait's doll (Minotaurs: no helm or boots;
  Dragons: rings, amulet and gauntlets only). Then the run's crafting materials through `crafting.craft()` in order:
  Emerald, Hourglass, Eye of the Void, gems, Pandora's Cube, Crafting Cubes (+2 power, +4 on jewellery, cap
  min(level/5, 120)).
- Spells: a spell is used only if the character knows it at that stage (mastery reached).

The harness then reports HP, SP, the power report, empirical melee/bow/breath through `resolveCharacterAttack` against
a B-tier target, damage taken per type, hit chance against it, dodge, regeneration (full, half HP, potion), leech,
the Seraph and Shaman on-hit heals, the class flat cut, spell cost and recovery, and a grid of [hit chance, taken %
for 11 damage types] per attacker level of the maps around that stage.

### 5. Fights

Both models are expected-value simulations in 0.1 s steps; the character starts each fight at full HP.

- Monster attacks: every recovery/60 × 1.05 s (MAW's U(0.9, 1.2) spread). Hit chance 1/(1 + speed/(100 +
  stat(L))·0.5); missiles and spells roll it twice; Grandmaster Dodging dodges. Damage after the character's taken %
  of the type, then the class flat cut `max(dmg − flat, 0.25·dmg)`.
- Regeneration: {5, 7.5, 10, 10} % × √(model HP of skill^1.4 × full), Grandmaster × (1 + missing²); Regeneration
  potion on top. Leech: dealt/HP_B × share × full, floor full × share/5 × recovery ticks/100. Mana Shield, Assassin
  energy, Seraph and Shaman on-hit heals (only those classes) modelled. Potions (with potions only): a Divine Cure
  below 35 % HP, one per second, costing the attack.
- Attack choice per swing: the attack with the most damage per second on the pack (area attacks hit 75 % of it),
  spells weighed by what mana regeneration can pay below half mana.

`sim.py`, generic packs: N B-tier monsters of the content level, physical melee, recovery 80, no resistances. Reports
the pack of 4 and 10 (time, lowest HP, potions) and the largest pack survived without potions (binary search to 40).
Variants: `MAW_FLAT=1` (MAW's flat-cut formula), `OPENER=3` (ranged builds get 3 s before the pack arrives).

`realfight.py`, real groups: the ten maps around each stage, every group as spawned. Each monster has its own tier,
level, HP (boss HP as spawned), and attack mix: spell 1 at its chance, then spell 2, then attack 2, else attack 1.
Attack 1 is the map's MAW value for the row; attack 2 its class's base × its dice over attack 1's; a player-school
spell the monster's magic base × MAW's monster spell multiplier (Fire Bolt 0.75, Fireball 0.5, Lightning Bolt 0.95,
Psychic Shock 1.25 …); buffs and curses cost the turn. Boss damage × 1.3. The character's hits are divided by
2^(resistance/100) (capped at 200); a dragon's breath takes the lowest resistance. Kill order: most damage per HP
first. Reported per group: whole group at once, and pulled four at a time resting to full between pulls, each with
and without potions.

## Validation

- Harness against the running game (`validation/*.yml`, headless with `party_attack` and timed `hp show`): a level-100
  Champion, Vampire Death Knight, Dragon (with and without gear), Seraph and Troll (regeneration in and out of combat).
  Attack damage per swing, recovery, damage taken and regeneration matched the harness. The `/tmp/maw_solo_validation`
  paths in them are where the harness's `val_*.tsv` monster tables were written; adjust before rerunning.
- Monster damage: the physical base the route writes equals the map table's attack value for every row checked
  (e.g. Giant Rat 505.675); spells use the same formula as the monster inspect screen (`MawMonsterInspect.cpp`).
- Monster sizing: a level-70 Dire Wolf has 1,358 / 1,360 HP and 500.6 attack damage in both.
- Reproduction after the move (2026-11-14): the prep scripts rebuild `maps.json`, `inventory*.json`,
  `mapmonsters.json`, `mapdata.json` and every main `route_<dk>.json` identically; the rebuilt binary reproduces all
  560 Nightmare cases field for field; `realfight` + `agg_real` reproduce the 88 Nightmare rows; `rebuild_tail.sh`
  reproduces the page data (same rows, different order). The `route_<dk>_one/_none.json` variants in the work
  directory predate the group index; `5_routes.py` writes them with it.

## Known limits

- Stand and trade: no kiting, line of sight, doors, terrain or first strike from range (except the generic `OPENER=3`
  variant). No crowd control: the Dragon's Fear (spell 122; MAW skips the resistance check and the skill scaling of
  its duration) and the solo's doubled crowd-control durations are not modelled. Ranged builds are undersold.
- No conditions (paralysis, stone, disease) or monster buffs. A solo whose only member is paralysed, stoned or
  unconscious loses; Protection from Magic blocks them.
- Not used: Death Knight spells (Death Coil), Shaman spells, Assassin finishers, the Seraph's Divine Protection.
  Elementalist stacks held at 5.
- The route clears every map once, easiest first: no resets, dimension maps, Arena, bounties or shops; MM9 (Chedian)
  is not in it, so Supreme (four promotions) is never reached. The Mirror, Pearl and Orbs are not spent.
- Gear choice per slot by damage × vitality; immunity specials (of Freedom, of the Medusa) are worth more to a solo.
- One skill split per build, not an optimisation.

## Open items

- **Flat-cut port difference (Seraph Spirit, Shaman Water).** `mawClassDefense`
  (`game/rules/maw/MawClassRules.cpp`) computes `monsterDamage(L+1) · s/estimateSkill(L) · avgTaken/2 ·
  0.99^estimateSkill(L)`, where MAW's `avgTaken` also carries `chanceToBeHit × legendaryDamageTaken` (COMBAT.md, the
  taken formula). OpenYAMM's cut is 25–40 % larger. It changes nothing up to Road to Insanity (both exceed the hit;
  the 25 % floor binds) but at Beyond Madness L500 a physical hit lands for 2,692 with MAW's formula instead of
  1,248. The harness reports the MAW factor (`flat_maw_factor`); `sim.py MAW_FLAT=1` applies it. Not fixed.
- **Experience curve.** MAW changed the step past level 100 from 1 % to 0.5 % per level on 2026-11-10 (commit
  ba572ec2, "reduced experience to level up"). OpenYAMM and this simulation use the new curve. On the old one the same
  experience gives level 433 instead of 500 and 675 instead of 804 (150→151 cost 225 k, now 188 k). Players of 5.0
  releases before that change were notably weaker solo.
- **Player feedback (Discord, 2026-11-14).** MAW 5.0 players: solo melee is "in the gutter in the second half",
  ranged gets by "with copious amounts of cheese", the only successful 5.0 solo run was a Dragon and the same player
  gave up with a Knight; the Dragon is ranged, has crowd control, is easy to gear and has a "crazy dps/tankiness
  ratio". The simulation agrees on the order; the missing ranged play and Fear mean the Dragon's lead is larger than
  shown.
- Offered, not built: ranged approach (monsters walking in from aggro range at their speed), Fear in the fights, a
  rerun on the old 1 % curve, a "finish one continent first" route, the page in `tools/maw_site`.
