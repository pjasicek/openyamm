# Solo power curve through items, loot and crafting (proposal)

Status: proposal, 2026-11-14. Nothing here is implemented. Scope: how gear progression could let a farming solo
outgrow MAW's Beyond Madness (BM) wall without changing what 5-member parties face. Inputs: the solo simulation of
2026-11-14 (`output/maw_solo_sim/`, scripts in [../scripts/](../scripts/)), the item and crafting specs
([../../ITEMS.md](../../ITEMS.md), [../../CRAFTING.md](../../CRAFTING.md), [../../BALANCE_MODEL.md](../../BALANCE_MODEL.md))
and the ruleset code in `game/rules/maw/`. Line numbers are from the tree on 2026-11-14.

---------------------------------------------------------------------------------------------------------------------

## 1. Diagnosis

### 1.1 Monsters are sized against a frozen model with its own copies of the item caps

A B-tier monster gets `Power(L) × hitsToKill` HP and `Vitality(L) / hitToKill` damage, where Power and Vitality
belong to an *expected character* of the monster's level ([BALANCE_MODEL.md](../../BALANCE_MODEL.md) §1). That
model keeps private copies of the item ceilings: `powerFor` capped at item power 100 (`MawBalanceModel.cpp:143-146`),
`maxEnchantStrength` from the same enchant curve (`MawBalanceModel.cpp:512-519`), `gearedFraction`
(`MawBalanceModel.cpp:547`). Item code (`MawItemFormulas.cpp`, `MawItemRules.cpp`, `MawCraftingRules.cpp`) does not
feed it. **Anything added to items below can stay out of monster sizing**, as long as the model's copies are left
alone. Every mechanism here relies on that.

### 1.2 Every item axis stops between item level 450 and 600

| Axis | Ceiling | Where |
|---|---|---|
| Enchant strength curve | `1+2t` to tier 12, then `25+3(t−12)`, **100 at loot tier 37** (drop level ≈ 450) | `MawItemFormulas.cpp:69-79` |
| Rarity roll | ×1.25 Primordial/Celestial, ×1.2 Insanity/Madness `enchantPower` | `MawItemFormulas.cpp:83-107` |
| Item power for weapon damage | `min(level/5, 100)`: **power 100 = item level 500** | `MawItemFormulas.cpp:15, 312-315`, used through `itemPower*5` in `MawItemRules.cpp:1509-1510` |
| Special-enchant stats | `× min(1 + power/25, 5)`: also stops at power 100 | `MawItemRules.cpp:328, 452` |
| Crafting Cube | `min(ownerLevel/5, 120)`, +2 (weapons, body) / +4 | `MawCraftingRules.cpp:29, 1094-1102` |
| Gems | cap `round(tier/20 × PrimordialMax) × slot`; PrimordialMax 150 in Insanity/Madness, so **150 × slot** at tier 20; tiers 17-20 only by 3:1 merges | `MawCraftingRules.cpp:391-409` |
| Creator's Hourglass | second enchant ≤ `100 × 1.5 × slot` (Doom and harder) | `MawCraftingRules.cpp:791` |
| Pandora's Cube quality | **20 %** on weapon rows and AC | `MawCraftingRules.cpp:27, 823-829` |
| Enchant count | 2 base + 1 special, no duplicate types | [ITEMS.md](../../ITEMS.md) §1.5 |
| Celestial | grows to wearer level 600 (1000 in Madness) | `MawItemRules.cpp:51-52, 1470-1475` |

Cube points 101-120 do nothing for weapon damage: damage reads power through the 100 cap, while the recovery keeps
slowing to item level 600 (`MawCombatFormulas.cpp:285`). The slower swing is paid back by the delay's
`damageMultiplier` (`MawCombatFormulas.cpp:306-309`), so it is DPS-neutral, but the cube points are wasted. Special
stats stop at 100 as well, so on weapons only the guard value grows, and on armour only AC.

### 1.3 What Beyond Madness drops, and what crafting can add

BM maps sit at monster level 300-320. With `lootTier = grade(6) + floor(level/15) + rounding (+1 boss)`
(`MawItemFormulas.cpp:391-396`):

| Drop level | Loot tier | Curve | Epic max (×1.2) | Primordial (×1.25) | Item power (Primordial) |
|---|---|---|---|---|---|
| 300 | 26 | 67 | 81 | 101 | 60 (72) |
| 320 | 27-28 | 70-73 | 84-88 | 105-110 | 64 (77) |
| 320 boss | 28-29 | 73-76 | 88-92 | 110-114 | 64 (77) |

All values × slot multiplier. Against that, crafting reaches:

- **Gems**: tier-16 cap 120, tier-20 cap 150 (× slot), i.e. ×1.1-1.5 over a BM drop with tier 16 and ×1.4-1.85 with
  tier 20. Kill gems at monster level 310 average tier ≈ 8 (`μ = max(L^0.6/4 + 1, L/40)` = 8.8,
  [CRAFTING.md](../../CRAFTING.md) §6.1), cap 60 × slot: **below what BM items already have, so useless**. Only the two
  completion gems per map (tier ≤ 16) and merges help. Tier 20 costs 81 tier-16 gems, which is 40 map completions.
- **Cubes**: power 62 → 100 is ×1.51 on 2H weapon damage (average `dice/2 + flat`: 148 → 224). It takes 19 cubes per
  weapon or armour piece and 10 per jewel, about 200 for a full set. The route earns 1 per map plus kill drops
  (≈ 4/1000 kills at L200-400), and the sim spent 127-173 cubes by L500. **The cube axis is nearly used up by the end
  of the clear.**
- **Quality**: +20 % on weapon rows and AC, reached with 1-5 Pandora's Cubes per item.

So the route's own crafting already took the solo most of the way to the ceilings. The rest of a full ceiling
(tier-20 gems on 26 enchants) is a ×1.2-1.4 stat gain bought with hundreds of map completions. That is grinding with
no felt payoff.

### 1.4 The wall is defence, and resistance is already spent

`mawMitigatedDamage` floors every hit at **10 % of the incoming damage** before the legendary multiplier and the
class flat cut (`MawCombatFormulas.cpp:224-230`). The L500 BM characters already sit on or near that floor
(harness rows `pool_out_madness.jsonl`, attacker level 310; B monster 70,009 HP, 36,800 physical / 71,220 magic):

| Build | HP | Physical taken | Magic taken | Magic hits to die | Melee DPS | Seconds per B |
|---|---|---|---|---|---|---|
| Dragon | 56,351 | 31.7 % | 10.7 % | 7.4 | 26,445 | 2.6 |
| Troll | 52,297 | 19.7 % | 11.6 % | 6.3 | 9,029 (+6.3k HP/s regen) | 7.8 |
| Champion 2H | 34,465 | 15.6 % | 12.6 % | 3.8 | 23,178 | 3.0 |
| Champion S&S | 33,912 | 10 % | 10 % | 4.8 | 17,927 | 3.9 |
| Lich King (DK vampire) | 11,581 | 10.7 % | 10 % | 1.6 | 23,671 | 3.0 |
| Archangel (Seraph) | 7,977 | 13.8 % | 11.9 % | 1.7 (after 3.8k flat cut) | 19,104 | 3.7 |

The magic hits to die follow the success shares the simulation reports (Dragon 84 %, Troll 57 %, others 0-10 %;
Seraph does better than its HP suggests because of its heal). Since **74 % of BM damage is magic and the floor
takes it to 10 %**, more resistance does nothing. A defensive affix "against magic" in the usual sense
(resistance, AC) would be dead on arrival. The only levers left are:

- **HP**: `fullHealth × (1 + Endurance/1000)` then Bodybuilding (`MawSkillRules.cpp:473-479`). Endurance is the gear
  path to HP.
- **Multipliers after the floor**: legendary 18 (×0.9) and 22 (×0.97^n, at least ×0.5) through `legendaryDefense`
  (`MawCombatRules.cpp:2612-2619`), and the Seraph/Shaman flat cut (`MawClassRules.cpp:830-842`, at least 25 % of
  the floored hit).
- Avoiding hits (Speed against the monster's stat, GM Dodge), regeneration, leech and Mana Shield.

### 1.5 Random enchant types waste a third of the solo's gear budget

Types are uniform over ten stats ([ITEMS.md](../../ITEMS.md) §1.5). Gear picked from the route's real loot leaves
the L500 Champion with Intellect 583 / Personality 493 (dead for a knight) and Endurance 276. Luck feeds a resistance
that is already at the floor. Meanwhile the model sizes monster damage against an expected stat of 766 in every stat
(`model_stat` at monster level 310). The Hourglass and Eye add random types, the Pearl removes one, and nothing
**chooses** a type.

### 1.6 Why farming does not help today

1. Loot level is monster level, so better drops need harder monsters. That is the wall itself.
2. Crafting is decoupled from monster level (gems, cubes and quality cap by tier or by player level), but its caps
   are within ×1.1-1.5 of BM drops (1.3) and mostly reached by the end of the clear.
3. A solo's real advantage is its share of the loot: one body takes every drop meant for five, and gets 5× a member's
   experience. Once the caps are hit, that share turns into gold and filtered junk
   ([DEVIATIONS.md](../../DEVIATIONS.md) #17).
4. Defence, the binding constraint, gains nothing from more resistance (1.4).

**What is missing:** (a) one currency that turns *all* surplus loot into progress, (b) deterministic control of
enchant types, (c) item scaling above the model's ceilings that does not feed the model, and (d) a defence that works
after the 10 % floor.

---------------------------------------------------------------------------------------------------------------------

## 2. Mechanisms

Each mechanism is a party-wide economy: currency is held by the party, not by a member. A solo therefore gears one
character with what a party spreads over five. That **5× per-character rate is the whole solo advantage**, and it
comes with no explicit solo rule. Nothing below touches `MawBalanceModel`.

### M1. Essence: salvage everything into one deterministic currency

**Change.** A party-wide counter `essence` (`uint64`, in `MawGameState`, saved). The Workbench gains *Salvage*. The
loot filter gains a "salvage" action next to "gold" and "leave on ground"
(`MawItemRules.cpp:2662-2700`, [DEVIATIONS.md](../../DEVIATIONS.md) #17).

```
essence(item) = ceil(itemPower × R[rarity] / 10)        enchantable base items and artifacts that dropped
R = Common 1, Uncommon 1.5, Rare 2, Epic 3, Ancient 4, Primordial 5, Legendary 6, Celestial 12
spare Crafting Cube (owner at its cube cap) = 40;  Pandora's Cube = 40;  Eye, Hourglass, Pearl = 150;  Emerald = 200
shop-generated items (ItemGenerationMode::Shop) and shop-bought materials = 0   (no gold-to-power pipe)
dimension map completion: + 100 × activeAffixes × (1 + power/10)
```

**Numbers.** A BM drop averages power ≈ 50 and R ≈ 2.3 (BM bands give about 35 % Epic+, 43 % Rare, 15 % Uncommon,
6 % Common at tier 27, [ITEMS.md](../../ITEMS.md) §1.4), so about **11 essence per item**. The route saw 3,670 items
in 17,931 kills plus 746 chests, about 0.2 items per kill. Replaying a 150-monster BM map therefore yields about 350
essence, plus materials. At 6 maps per hour that is **≈ 2,000-2,500 essence/h** at the wall, rising with clear speed.

**Time scaling.** Linear in kills, and higher on harder maps, because item power and rarity grow with drop level and
dimension-map affixes. There is no cap.

**Parties.** Same loot stream, so the same essence per hour shared over five characters: 1/5 per member.

**Cost and hooks.** Small: one state field, one Workbench op (`MawCraftingRules::craft` dispatch,
`MawCraftingRules.cpp:429`), one loot-filter action, a tooltip line ("Salvages for N essence"), a save-version bump.
Disabled in Austerity, which has no crafting today ([CRAFTING.md](../../CRAFTING.md) §1).

**Risks.** Inflation if a gold path leaks in, which the shop exclusions close. Players may salvage an item they later
want; the Workbench confirms anything Epic or better.

### M2. Inscription and Infusion: choose types, reach the existing caps deterministically

**Change.** Two Workbench ops paid in essence. Neither raises a ceiling.

- **Inscribe**: set one base enchant's *type* (1-10, rings 1-16) and keep its strength. Duplicates stay forbidden.
  Cost `2 × strength / slot` essence (100-300 per enchant at BM strengths). This is the Hourglass/Pearl pair made
  deterministic, in the Workbench's "pick, don't roll" spirit ([DEVIATIONS.md](../../DEVIATIONS.md) #36).
- **Infuse**: +1 strength on a base enchant up to the **existing tier-20 gem cap** (`gemCap(20, slot, skill)`,
  `MawCraftingRules.cpp:398-409`). Cost `ceil(strength / (10 × slot))` per point, i.e. 10-15 per point on a ×1 slot.
  Gems keep working as they do now; Infusion is the route around the 3:1 merge ladder for tiers 17-20.

**Numbers.** Taking one base enchant per slot to Endurance at the tier-20 cap gives `150 × Σslot` ≈ 150 × 14.75 ≈
**2,200 Endurance from gear** against 276-483 today. With HP `× (1 + End/1000)` (`MawSkillRules.cpp:475`) plus
Endurance's flat part, that is **HP ×2.0-2.5**, and the slot it takes was mostly dead (Int/Pers on a knight, Luck at
the floor). The second base enchant goes to Might or Speed at the cap: Might 1,100 → ~2,000 multiplies damage by
`(1 + Might/1000)` (`MawCharacterSheet.cpp:354`), ≈ ×1.2-1.4 depending on what it replaces. Full cost: Inscription
≈ 4k plus Infusion of 26 enchants from ~100 to 150 × slot ≈ 18k, **≈ 22k essence, about 10 h** at the wall.

**Time scaling.** Front-loaded and bounded. Once caps are reached it is done; it is the cheap first step.

**Parties.** Raises a member to a ceiling the model already assumes ×1.1-1.2 below (the model's 1.32 × curve ×
gearedFraction), so a party member who does it is somewhat over par, at 5× the per-member cost.

**Cost and hooks.** Small: two ops beside `raiseEnchant` / `addSecondEnchant` (`MawCraftingRules.cpp:632, 762`), the
Before → After panel already designed ([CRAFTING_BENCH_DESIGN.md](../../CRAFTING_BENCH_DESIGN.md) §6.4).

**Risks.** It makes gems and the Hourglass less special, though they stay cheaper per point at low tiers. Builds
converge on Endurance + Might everywhere; that is the intent for a solo, and Speed or Accuracy trade-offs remain.

### M3. Ascension: quality from 20 % to 120 %, paid in essence

**Change.** Extend the existing quality field (`ItemRulesetFields::qualityPercent`, `uint8`) past Pandora's 20 %. The
Workbench op *Ascend* adds +1 quality, up to 120, at an escalating essence cost. Quality already multiplies weapon
damage rows (`MawItemRules.cpp:1483, 1509-1510`, artifacts at 1489) and AC (`MawItemRules.cpp:1551, 1580`). It is
not part of the model, item value, level requirement or Celestial's level rewrite, which overwrites `itemPower`
only (`MawItemRules.cpp:1503-1507`). Jewellery, whose quality multiplies nothing today
([CRAFTING.md](../../CRAFTING.md) §3.7), gets a caster variant: spell damage `× (1 + Σ_jewels (q−20) × slot / 600)`,
up to ×1.9 with six rings and an amulet. That variant needs its own caster check.

```
cost(q → q+1) = ceil(10 × slot × 1.035^(q − 20))           q = 20..119
per ×1 item:   to q 70 ≈ 1.3k,   to q 120 ≈ 8.6k   (× slot multiplier)
```

**Numbers.** A weapon goes from ×1.2 to ×2.2 on its rows, **×1.83 on weapon damage**. At L500 the weapon is roughly
60 % of a melee hit's scaling term (weapon rows against Armsmaster and stat terms, [BALANCE_MODEL.md](../../BALANCE_MODEL.md)
§3.10), so expect **×1.5 per hit at q 120** and ×1.25 at q 70. Leech heals scale with damage dealt against the
monster's HP (`MawCombatRules.cpp:3394-3420`), so sustain rises with it. Full set (2H weapon plus 7 armour pieces,
Σslot ≈ 9.25): **≈ 12k essence to q 70, ≈ 80k to q 120**.

**Time scaling.** Geometric cost, so about half the power is reached at 15 % of the full cost. This is the long tail
of the curve.

**Parties.** 45 items to ascend instead of 9, at the same income. That is **5× the hours per member level of power**.

**Cost and hooks.** Small: raise `MaxQualityPercent` for essence crafts only (`MawCraftingRules.cpp:27`, Pandora stays
capped at 20), one op, a tooltip line, and the caster multiplier in the spell damage path next to the main-hand
enchant share.

**Risks.** Archibald's Mirror copies every field (`MawCraftingRules.cpp:836-849`). It must reset quality above 20 to
20, or one mirror duplicates tens of hours of essence. Very fast kills can outrun the experience curve on lower
difficulties; that is acceptable as a reward, since nobody needs Ascension below Doom.

### M4. Ward: armour Ascension works after the 10 % floor

**Change.** Each worn armour piece with quality above 20 adds Ward `W += (q − 20) × slot` (body 1.5, helm, gloves and
boots 1.25, belt, cloak and shield 1; the full set is 8.25, or 7.25 without a shield). Damage the character takes is
multiplied by `1 / (1 + W/400)` **after** the floor, in the same place as legendaries 18/22: fold it into
`MawCombatRules::legendaryDefense` (`MawCombatRules.cpp:2612-2619`), which feeds monster hits (`:1163`) and traps
(`:2426`) through `mawMitigatedDamage`'s `withFloor` (`MawCombatFormulas.cpp:224-230`). Clamp the combined post-floor
multiplier to at least ×0.25. Compute W when equipment changes, never per frame.

**Numbers.** q 70 on every piece: W ≈ 410, **taken ×0.49**. q 120: W = 825, **taken ×0.33**. It applies to physical
and magic alike, so to the 74 % magic share in full. With legendary 22 in a pack of four (×0.885) the total is ≈ ×0.29.

**Time scaling.** Same essence curve as M3. It is one sink, so a player chooses each hour between damage (weapon) and
toughness (armour).

**Parties.** Same 5× time argument. A party tank with Ward needs fewer heals. Parties already clear BM, and the gain
takes them 5× longer.

**Cost and hooks.** Small: one multiplier, one character-sheet line ("Ward N: −X % damage taken"), and an Inspect line.

**Risks.** It stacks multiplicatively with HP gains (M2), so the ×0.25 clamp is needed, and immunity would be the
failure mode. AC and resistances keep their role below the floor, so early defence is unchanged.

### M5. A farm ladder that pays more on harder maps (dimension maps and replays)

**Change.** No new content. Make the existing endless loop pay in essence:

- Dimension map completion pays `100 × activeAffixes × (1 + power/10)` essence beside MAW's Cube/Eye/Hourglass/Emerald
  rewards ([CRAFTING.md](../../CRAFTING.md) §6.3). The map's level `10·power + 20 + band`
  (`MawDimensionMaps.cpp:294-297`) and its loot-tier bonus `floor((power − 28)/2)` ([ITEMS.md](../../ITEMS.md) §1.3)
  already raise item power and rarity, so salvage pays more on harder maps too.
- A replay of a cleared map (respawned monsters) pays only salvage; MAW gives no repeat completion items
  ([CRAFTING.md](../../CRAFTING.md) §6.3).
- *Optional gate*: Ascension above q 70 requires a completed map of monster level ≥ `250 + 2 × (q − 70)` (q 120 needs
  level 350). This is PoE's atlas: each step of power opens the content that funds the next. Leave it out if
  simplicity matters more.

**Numbers.** A 4-affix power-10 dimension map pays 800 extra essence, about as much as two to three replays.

**Parties.** Unchanged content, same per-party income.

**Cost and hooks.** Trivial in the map-completion reward path. The gate is one check in the Ascend op.

**Risks.** A solo farms the best essence-per-minute map forever. That is fine; it is the genre.

### Considered and not proposed

- **Resistance or AC affixes against magic**: dead at the 10 % floor (1.4).
- **Raising the item-power cap of loot** (drops above power 100): it would also move free-progression and
  dimension-map monsters through any future model resync, and it does nothing for BM's fixed 300-320 levels.
- **Sockets, sets**: horizontal choice that needs new data and UI. Inscription already gives build control.
- **Corruption or gambling** (e.g. a second legendary affix with a chance to brick): it conflicts with the
  deterministic, unscummable crafting OpenYAMM chose ([RANDOMS.md](../../RANDOMS.md) §7). It could be a later chase
  item, after M1-M4 prove the curve.
- **Target-farmable uniques**: artifacts already scale with party level (`MawItemRules.cpp:1489, 1612`). Boss-locked
  artifact tables would add variety, not a power curve.

---------------------------------------------------------------------------------------------------------------------

## 3. Recommendation and power-curve target

**Combination:** M1 + M2 + M3 + M4, with M5's essence rewards (the gate optional). Order of value: M4 (it attacks the
binding constraint), M2 (cheap, about ×2 HP from stats that are wasted today), then M3/M1, which provide the long
tail and the currency for all of it. None of it enters `MawBalanceModel`, so monsters are the same for everyone. The
solo's edge is the 5× loot share per character that today ends in gold.

The gains are multipliers on top of par, independent of level. So the same edge holds on BM's fixed-level maps and on
dimension maps of any power, where the model reaches its own ceilings at item level 465-500 just as items do.

### Target curve (melee solo at the BM wall, character level ~500, monsters 300-320)

Assumptions: ≈ 2,000-2,500 essence/h from replays and dimension maps, rising about 50 % per stage as clears speed up.
Hours are counted after the route clear has reached the wall. `K_hp`, `T` and `M` are the multipliers to apply in the
simulation.

| Stage | What is bought | Essence | Farming hours | K_hp (HP) | T (taken, all types) | M (melee per attack) | Target (realfight, BM, no potions) |
|---|---|---|---|---|---|---|---|
| 0 | route as simulated | — | 0 | 1 | 1 | 1 | today: Dragon 84 %, Troll 57 %, Seraph 47 %, others 0-10 % (pulls of 4) |
| 1 | M2: Endurance + Might inscribed, infused to the tier-20 cap | 22k | ~10 | 2.0 | 1.0 | 1.2 | Champions, Minotaurs ≥ 60 %; DK, Seraph ≥ 40 % (pulls of 4) |
| 2 | M3/M4 to q 70 on the 2H weapon and 7 armour pieces | +12k | ~15 | 2.0 | 0.49 | 1.5 | every melee build ≥ 90 % in pulls of 4; Dragon/Troll whole groups |
| 3 | q 120 | +68k | ~40 | 2.0 | 0.33 | 1.8 | every melee build ≥ 95 % of **whole groups at once**, minimum HP ≥ 40 %, a B in ≤ 1.5 s |

At stage 3 the product (damage per second taken × seconds per kill) falls by ≈ 11× (K·M/T = 2 × 1.8 / 0.33). A pack
of four that costs a Champion about 240 % of its HP today costs about 22 %, before leech and regeneration. That is
the "mash through it" feel. A five-member party reaches the same per-member stage in about 5× the hours (≈ 200 h for
stage 3).

### Checking it with the simulation

Do not edit `realfight.py` for the proposal. A run scales three inputs per build after loading the harness row `d0`:

```
d0['hp']                  *= K_hp
d0['grid'][lvl][1:]       *= T          (every damage-taken percentage; applied before the flat cut, as the code does)
d0['emp_melee_per_attack']*= M          (also breath_per_attack for the Dragon; spells only with the jewellery variant)
```

The first-order check runs the stage table above on the BM L500 cases and compares the `dead4` / whole-group shares
with the targets. The second-order check makes K_hp and M exact: let the harness gear picker (`SoloRoute.cpp`) choose
enchant types freely at `gemCap(20, slot)` strength (M2), and multiply quality by `1 + q/100` on the weapon and
armour rows (M3). The real character sheet then yields HP and melee per attack, and only T is applied by hand. If
stage 2 misses its target, lower M3/M4's essence costs rather than raising the 120 ceiling. The curve's shape (half
the power at 15 % of the cost) should stay.
