# Endgame loop: farming that outgrows the monsters

Balance proposal, 2026-11-14. Angle: where a solo can farm, what farming pays, and whether MAW's scaling rules let
hours turn into power faster than the monsters grow. Nothing in the game or its data was changed. Goal (the user):
a maxed solo rolls through Beyond Madness after grinding real gear upgrades, PoE-style, without making parties
trivial. Companion: [POWER_GAP.md](POWER_GAP.md) (how much stronger a solo must be). Code paths are OpenYAMM's MAW
port (`game/rules/maw/`), MAW at 8967ae88; numbers from `devdocs/maw/data/balance_golden.csv` (party of 5 rows;
solo differs only through Cover) unless the [solo study](../README.md) is named.

## Summary

- **Levels stop paying above ~500.** Monsters are sized against the expected character at their level, and its
  power × vitality (PV) grows about L^6 below 400 but only L^3 above 500, because gear, black potions and enchants
  saturate there. The same 1.6–1.8× level lead is worth PV ×35 at the end of Nightmare (L503 against 275) but only
  ×3.6 at the end of Beyond Madness (L804 against ~490), and 0.39 against the Breach (1100).
- **Every gear ceiling sits at drop level 465–640**, and the balance model already assumes nearly capped gear
  there, so loot past the knee buys at most the model's last 10–15 % plus rarity and gems, never a multiple.
- **Beyond Madness has no repeatable farm.** No refills or resets; Arena and bounties pay nothing; dimension runs give
  no next map; kill-dropped maps need a map level of 950 or more; the quest maps sit at the character's own level,
  where a solo cannot fight in Beyond Madness. A Beyond Madness solo's power ends at the route's last map.
- **Proposal:** an endless **Rift Atlas** (dimension maps with free tier choice, in every mode), paying
  **Rift Shards** that buy **Ascension ranks** on any item (×(1 + 0.06 r)), plus **rift-forged loot** whose item
  power and enchant curve continue past today's caps. The balance model stays capped, so the monsters never follow.
  Supporting changes: a separate rift bank, reads that treat a solo fairly, an optional solo density for rifts and
  pinnacle guardians. Parties need about 5× the hours per member: shards and loot are per kill, and kill experience
  is split.
- **Target, checkable with the route simulator:** pulls of four on the last Beyond Madness maps by about 40 hours of
  rift play, whole groups at about one second per monster by about 100 hours, and the Breach in pulls as the
  pinnacle.

## 1. Diagnosis

### 1.1 The level lead flattens exactly where Beyond Madness ends

Monster HP = Power(L_B) × hitToKillMonster, damage = Vitality(L_B) / hitToKill (BALANCE_MODEL.md §1). A solo against
N monsters wins roughly when its PV over the monsters' PV exceeds (hitToKillMonster / hitToKill) × N(N+1)/2:
12.5 for a pull of four in Beyond Madness (5/4 × 10), 19 for a group of five and 82 for a group of eleven.
Expected-character PV (Beyond Madness rows, interpolated):

| Content level | Character level for PV ×4 | ×12.5 (pull of 4) | ×19 | ×55 | ×100 |
|---|---|---|---|---|---|
| 300 (stage-500 Beyond Madness maps) | 367 | 436 | 475 | 717 | 887 |
| 490 (last Beyond Madness maps) | 834 | 1205 | 1358 | 1813 | >2000 |
| 1100 (the Breach) | 1629 | >2000 | | | |

The exponent falls because the model saturates: `powerFor` caps item power at 100 (item level 500,
`MawBalanceModel.cpp:143-146`), the black-potion term stops at level 500 (`MawBalanceModel.cpp:584`), and max enchant
reaches 110/132 at 500 (golden `max_enchant`). Above that, the expected character grows only by skill and HP per
level, and so does a real one. At a 1.6× level ratio a solo is therefore 4× worse off against the last Beyond Madness
maps than at stage 500. [POWER_GAP.md](POWER_GAP.md) measures ×14 effective power for pulls and ×120 for whole groups
at stage 500. Scaled by that factor, the end of Beyond Madness needs about ×60 and ×500 over the route's L804
character. That is an estimate; the simulation measures it in §3.

Experience cannot close this cheaply: a step is 1000·L·(1 + (L−100)·0.5 %) (`MawExperienceCurve.cpp:14-17`), so total
experience grows ~L³, and above 500 PV also grows ~L³. PV is roughly linear in experience earned. Kill experience is
award × monHP / monsterHealth(min(charLevel, bank)), capped at (level+1)·1000 (`MawExperienceRules.cpp:186-191`).
Against monsters at 0.6× its level (bank ~0.55× level) an L800 solo needs ~140 kills a level; against its own level,
~50. It can only take the second once it is far above the model.

### 1.2 Gear caps all sit at drop level ~500

| Ceiling | Reached at | Where |
|---|---|---|
| Item power floor(dropLevel/5) ≤ 100 (Primordial ×1.2 → 120) | drop level 500 | `MawItemFormulas.cpp:15, 314, 333-348` |
| Enchant curve 25 + 3(t−12) ≤ 100 at loot tier 37; tier = grade + dropLevel/15 + bonuses | drop level ~465 (grade 6) to ~540 (grade 1) | `MawItemFormulas.cpp:13, 78, 391-396` |
| Crafting Cube: item power ≤ min(owner level / 5, 120) | owner level 600 | `MawCraftingRules.cpp:29, 1094` |
| Gem drops: mean tier max(L^0.6/4+1, L/40), max 16; completion gems min(ceil(L/25+0.5), 16) | ~640 / 388 | `MawMonsterRules.cpp:150-157`, `MawExperienceRules.cpp:342-344` |
| Celestial grows to min(wearer, 1.2 × bank) ≤ 600 (Beyond Madness 1000), but feeds the capped curves above | ~540 in effect | `MawItemRules.cpp:51-52, 1470-1475` |

In Beyond Madness the route's last maps are level 500 (`map_levels.yml`), so loot reaches every cap on the final maps.
After that, "grinding gear" only rerolls rarity: Primordial against Epic is about 25/14 on enchant draws, plus
legendaries through the bad-luck counters. That is ×1.5–2, not ×60.

### 1.3 Beyond Madness has nowhere to farm

- No refills (RefillDays 1e9) and no dungeon resets in Road to Insanity and Beyond Madness (COMBAT.md §4); a map
  pays its completion reward once (`MawExperienceRules.cpp:207-216`).
- The Arena and bounty maps give no loot or experience (`MawRules.cpp:561-570`).
- Dimension runs pay their reward (Beyond Madness formula ×0.5) but never the next map (`MawExperienceRules.cpp:218-227,
  275-279`).
- Kill-dropped maps need map level ≥ 950, counted as band mean + 20 + 10 × run power, not the madness level
  (`MawMonsterRules.cpp:250-269`). That takes a dimension run of power ≥ ~85, i.e. a quest tier ≥ ~870.
- The quest gives one map per tier (80, 110, 139 … then +10), power (tier−20)/10 (`MawMonsterRules.cpp:2385-2461`):
  52 maps by L804, each at about the character's own level, where an expected character loses to groups.

So the Beyond Madness solo ends at L804 with no repeatable source of experience, loot or crafting materials.

### 1.4 Elsewhere the farm exists but is pegged to the character

Outside Beyond Madness, completing a dimension run on a completed map gives the next map at power +1, which is +10
monster levels (`MawExperienceRules.cpp:224-226, 380-403`). Kill drops roll power ≈ monster level/10 − U{0..3}
(`MawMonsterRules.cpp:302`). A run of ~300 kills gives an L800 solo 2–6 levels, so the +10 a run chain outruns it,
and nothing lets the player step down a tier. Resets (+20 levels a reset, `MawMonsterLevels.cpp:420`) raise
monsters and drop level together and pay no completion reward again.

### 1.5 Bank-tied reads short-change a solo

A solo banks a fifth of its kill experience (`MawExperienceRules.cpp:167-171`), so its bank sits at ~0.5× its
level. These reads use the bank, not the character:

- reagent drop level min(dropLevel, bank)/3 (`MawItemRules.cpp:1063-1069`): potions are a solo's party;
- the Celestial level min(wearer, 1.2 × bank) (`MawItemRules.cpp:1473`);
- the artifact loot tier from the bank (`MawItemRules.cpp:1611-1612`);
- shop stock at 0.75 × bank (`MawItemRules.cpp:1065, 1214`);
- bounty level and reward (`MawMonsterRules.cpp:1412, 1489`).

They bind wherever the content is above the bank: in rifts and in late Beyond Madness.

### 1.6 Free progression: farming raises the other side

The bolster is the bank on the other continents − 4 (`MawMonsterLevels.cpp:404-420`). Farming on one continent
raises every other continent's monsters, including Chedian or anything not yet played.

### 1.7 A calibration gap to check first

At L500 against level-300 content the model gives PV ×22, enough for pulls of four, yet 17 of 22 route builds beat
≤ 10 % of the Beyond Madness groups that way. The route's character sits well below the expected one there; 74 % of
the real damage is magic, which the model averages with physical (`MawBalanceModel.cpp:711-722`). Before tuning the
loop, run realfight once with a character set to the model's P and V at its level, so the targets in §3 are measured
from the real baseline.

## 2. Mechanisms

### M1. Rift Atlas: dimension maps with a chosen tier, in every mode

- **Change.** Rift tier T is the dimension power: monsters at 10T + 20 + the map's offsets
  (`MawMonsterLevels.cpp:423-426, 553`), independent of the bank. The Seer's new topic "Rift Atlas" sells a map of
  any tier ≤ highest tier cleared + 1, with 2–4 rolled affixes (gold 2000·T; the existing Crafting Cube and Hourglass
  reroll target and affixes on the Workbench). Completing a run raises the highest tier when T = highest + 1 and
  drops the next map at T + 1 in every mode, Beyond Madness included. Kill drops roll power from the monster level
  as today. In Beyond Madness they start at monster level 300 instead of map level 950.
- **Unlock:** the Dimensional Maps quest done (tier 500, `dimension_maps.yml` `unlock_tier`); in Beyond Madness, a
  character level of 500 (stage 500; the quest's 500 is the character's own level there).
- **Numbers.** Beyond Madness's content 300–500 is T 28–48; the Breach (1100) is T 108. A run has ~200–400 kills at
  density ×(1 + (T+20)·affixes/300) (`MawMonsterRules.cpp:1872`). Run rewards are unchanged: kill experience and
  loot at the monster level, rarity ×(1 + strength/400), crafting ×(1 + 1.5·strength/800)
  (`MawItemRules.cpp:1219-1229`, `MawMonsterRules.cpp:143-144`). Beyond Madness completion stays ×0.5.
- **Over hours.** The player picks the tier it clears fastest. The tier pushes up as power grows, PoE's atlas loop.
- **Parties:** the same content; it pays a party the same per kill, so a party gets a fifth per member.
- **Cost:** M. Hooks: `rulesTopic` (`MawMonsterRules.cpp:2374`), `completeDimensionRun`, removing the madness
  exclusion at `MawExperienceRules.cpp:224`, the gate at `MawMonsterRules.cpp:254-269`, and `highestRiftTier` in
  `MawGameState` (save).
- **Risk:** low-tier farming for experience. The health ratio already shrinks awards from weak monsters, and loot
  stays at the monster level.

### M2. Rift Shards and Ascension: the currency ladder

- **Change.** A new crafting item, the Rift Shard, drops only in rifts: chance per kill 0.05 × (1 + T/20) ×
  (1 + strength/400), ×10 from bosses. On the Workbench, shards raise an item's Ascension rank r by one, costing
  5 × 1.2^r shards. The rank may not exceed floor(highest tier cleared / 2). Each rank adds 6 % (non-compounding)
  to the item's enchant strengths, its item-power-derived damage and armour, and its special amounts:
  ×(1 + 0.06 r). It stacks on rarity, gems and Cubes and works on capped and Celestial items. New field
  `ItemRulesetFields::ascension` (save).
- **Numbers.** At T 30 a 300-kill run gives ~55 shards and at T 60 ~120. Rank 10 everywhere (13 slots, ~3,800
  shards) takes ~65 runs at T 30; rank 20 everywhere (~13,600) another ~95 runs at T 60. Gear values ×1.6 at rank 10
  and ×2.2 at rank 20 give an estimated PV ×2.5–4.5; the simulation measures this. Ranks 30–40 (×2.8–3.4) are the
  long tail.
- **Why this one:** it pays at any tier, so the solo can start where it is strong (Beyond Madness content at 0.4–0.6×
  its level) and climb. It is the incremental "pimping" the user asked for: every run moves a bar.
- **Parties:** shards are per kill, not per member, so five members need 5× the shards for the same ranks.
- **Cost:** M (crafting rule, preview, tooltip, save field, data). Hooks: `MawCraftingRules`, the
  `weaponDamage`/`armorClass`/enchant readers in `MawItemRules.cpp` (1500-1580, 1828-1836).
- **Risk:** the multiplier must never reach `MawBalanceModel`. Add a unit test that pins `balance_golden.csv` so a
  rank or cap change cannot move monsters.

### M3. Rift-forged loot past today's caps

- **Change.** Items generated during a rift run carry `riftTier = T`. For them only: item power
  floor(dropLevel/5) up to the field's 255 (`PowerHardCap`) instead of 100; the enchant curve continues past loot
  tier 37 at +2 a tier to 175 (tier 74); the Crafting Cube caps at max(owner/5, the item's own drop cap) instead of
  120; gem tiers 21–24 (Rift gems, from T ≥ 60) carry caps of 21/20–24/20 of today's tier-20 cap. Everything else
  stays capped, including `powerFor`.
- **Numbers.** At T 98 (drop level 1000), item power 200 roughly doubles weapon dice and flat (levelDamage 400
  against 200) and armour; enchants ×1.75. Estimated PV ×4–6 against capped gear. Enchants saturate around T 70,
  item power around T 125: a real upgrade every ~10 tiers, the gear treadmill on top of Ascension.
- **Parties:** the same rule; five members each need it.
- **Cost:** M. Hooks: `mawItemPower` and `mawEnchantStrengthCurve` (`MawItemFormulas.cpp:69-79, 333-348`) take the
  rift tier; the generation sites already know the run (`MawItemRules.cpp:1217-1229, 1287`); `MawCraftingRules.cpp:1094`;
  gem data in `crafting.yml`.
- **Risk:** single hits that big. Check the damage and HP proxy paths for overflow at item power 255 and Ascension 40.

### M4. A rift bank and fair reads for a solo

- **Change.** (a) Rift kills and completions bank into a fifth bank slot, "rifts", which counts in `totalLevel()`
  (the experience health ratio, item reads, Beyond Madness quest experience) and is left out of the
  free-progression bolster (`MawMonsterLevels.cpp:406` reads `levelOutside`, minus the rift slot). (b) The reads in
  §1.5 use max(bank, 0.8 × the party's highest member level) instead of the bank.
- **Numbers.** (a) keeps the existing ~50–140 kills a level: freezing the bank instead would let awards hit the per-kill
  cap and fall to ~5–10 kills a level, a runaway. (b) Rift reagents at T 98 rise from bank/3 ≈ 150 to ≈ 330 power
  (Stone Skin, Bless and resistances keep growing with power); the Celestial and artifact reads move from ~0.6× to
  0.8× the solo's level.
- **Parties:** (a) the same; (b) no change, since a party's members sit near its bank.
- **Cost:** S–M (continent array, save, five reads). **Risk:** the Progress tab and bank texts must show the slot.

### M5. Optional solo density for rifts

- **Change.** A rift option (Atlas topic toggle, solo runs only: `Party::soloRun` or one member) spawns groups at
  0.6× their count. Each kill pays ×1/0.6 experience, shards, crafting drops and item chance, so a run pays the same
  in fewer, bigger rewards.
- **Numbers.** By N(N+1)/2, a group of five shrinks to three (15 → 6, ÷2.5) and eleven to seven (66 → 28, ÷2.4).
  That is the effective power of about 1.35× the level in the steep part of the curve. Rewards per hour rise with the
  faster clears.
- **Parties:** none. **Cost:** S (`MawMonsterRules.cpp:1870-1878`, the reward multipliers). **Risk:** it is a solo
  assist, so keep it off campaign maps. The campaign stays as MAW sized it, and the grind is what beats it.

### M6. Pinnacles: rift guardians and the Breach

- **Change.** From T 30, a run whose tier is a multiple of 10 spawns a Rift Guardian, an Omnipotent boss (HP ×4).
  Its first kill per tier gives a Primordial item of a slot the player chose at the Atlas, at the tier's drop level
  (rift-forged), plus 50 shards. Repeat kills add ×5 to the Primordial and Legendary bad-luck counters. In Beyond
  Madness the Breach's first clear gives a Celestial of a chosen slot. In Beyond Madness the Endless Arena pays
  shards only (no experience, no bank), as a pure skill ladder (`MawRules.cpp:561-570`).
- **Numbers.** 8 guardians from T 30 to T 100: the guaranteed jumps of the gear treadmill.
- **Parties:** the same, one item per kill. **Cost:** S–M (boss spawn exists; targeted generation through
  `MawItemRules` with a forced rarity and slot). **Risk:** a chosen slot removes the luck; it is gated by tier.

## 3. Recommended loop and target

**Loop.** Finish the campaign, or reach stage 500 in Beyond Madness. Open the Atlas at a tier the character clears
in pulls (Beyond Madness: T 20–30). Run maps with affixes that raise density and rarity. Spend shards on Ascension
(the bar always moves) and Cubes and gems on the drops. Push the tier when runs get fast; every 10th tier a guardian
gives a chosen Primordial. From T ~48 rift-forged loot starts beating the campaign's caps, and from T ~70 the
enchant curve is the treadmill. The campaign's remaining Beyond Madness maps become the victory lap; the Breach (T 108
equivalent) is the pinnacle. Experience comes along at ~50–140 kills a level and adds the L³ part of PV.

**Expected power by source** (estimates for the simulation to replace; product over the route's L804 character):
levels 804 → ~1100 at ~60 h gives PV ×2.6; Ascension rank 20 gives ×2.5–4.5; rift-forged gear at T 70–100 gives
×4–6; solo density (in rifts only) gives ÷2.5 on group size. The product, ~×25–70 at 60 h and ~×100–500 at 100–150
h, brackets the ×60 (pulls) and ×500 (whole groups) of §1.1.

**Targets** (Beyond Madness, the route's last ten maps' real groups, realfight without potions; h = rift hours):

| h | Tier the solo farms | Pulls of 4 (ok4) | Whole groups (ok) | Seconds per monster |
|---|---|---|---|---|
| 0 (L804) | measured today | Dragon 84 %, Troll 57 %, Seraph 47 %, others 0–10 % | — | — |
| 15 | 30–40 | ≥ 60 % for the melee builds | — | — |
| 40 | 50–60 | ≥ 90 % for the melee and bow builds | ≥ 50 % | ≤ 4 |
| 100 | 80–90 | 100 % | ≥ 90 % for the melee and bow builds | ≤ 1.5 ("mash") |
| 150+ | 100+ | the Breach's groups ≥ 90 % | — | — |

Party guard: a party of five at 5h per member is no further along than a solo at h (shards, loot and experience
per member). Campaign checks on Normal through Road to Insanity are unchanged, because rifts open only after the
quest's tier 500 and the model is pinned.

**How to check.** Extend `harness/SoloRoute.cpp` with a rift phase after the route snapshot:

1. pick the tier the current gear clears at ok4 ≥ 95 % (realfight on a synthetic run);
2. build the run from a completed map's group sizes ×density, with the three rolled families (`families_indoor` /
   `families_outdoor`, tiers rolled as the game does) at 10T + 20, through `rollDimensionMap` and the same corpse-loot,
   crafting and experience calls the route uses;
3. book shards, Ascension and Cubes, and re-gear every 5 runs with the existing per-slot choice;
4. charge time per run as realfight's clear time per group + 45 s of travel per group + 2 min overhead.

`realfight.py` then fights the route's last ten Beyond Madness maps with each snapshot. Output: ok4, ok and
s/monster against h, per build and seed. The knobs to tune against the table: the shard rate, the Ascension step
(6 %) and cost base (1.2), the rift curve's slope (+2 a tier) and the solo density (0.6). First run the calibration of
§1.7 (a model-P/V character), and run the same rift phase on Nightmare and Doom to confirm the party guard.
