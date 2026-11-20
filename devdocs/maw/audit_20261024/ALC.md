# ALC — Alchemy, potions, crafting, dimension maps

Auditor: ALC. MAW = `/home/pjasicek/github/Maw-Mod-MMMerge` (paths below relative to `Scripts/` unless noted).
OpenYAMM paths relative to the repo root. MAW's `POTION.TXT`/`POTNOTES.TXT` were compared against an extraction of
`Data/zMaw.T.lod` already present in another session's scratchpad (identical but for stripped quotes).

Findings are ordered by severity.

### ALC-1: Endless Arena kills drop no crafting materials, reagents, Endless Potions or dimension maps
Severity: P2
Confidence: confirmed
MAW: `Global/zzMaw_Arena.lua:293-299` empties only the corpse treasure of d42 monsters (on PickCorpse); the crafting
handler `General/zzAlchemy.lua:1118-1236` (gems, the nine specials with pity), the reagent/Endless handler
`zzAlchemy.lua:654-698` and the map drop `General/zzMaw-Maps.lua:826-939` all still run for arena kills. Only Beyond
Madness skips them (`zzAlchemy.lua:1122-1126`, explicit list zarena/d42/7d05). The C-tier wave boss counts as a normal
kill there, and arena monsters are high level, so the arena is a real crafting source in MAW.
OpenYAMM: `assets_dev/rulesets/maw/events/maps/d42_maw.lua:46-47` spawns every wave with `loot = false` →
`request.dropsLoot = false` → `actor.proceduralDeathLoot = false` (`game/outdoor/OutdoorWorldRuntime.cpp:20080`,
`game/indoor/IndoorWorldRuntime.cpp:14211`), and `mapActorCorpseLoot` returns an empty `CorpseLoot` for such actors
(`OutdoorWorldRuntime.cpp:18895`, `IndoorWorldRuntime.cpp:17270`), so `MawMonsterRules::corpseLoot` and with it
`rollCraftingDrops`/`rollDimensionMapDrop` never run. Same for `lootWithoutCorpse` (needs `proceduralDeathLoot`).
Not covered by: DEVIATIONS 50 (arena levels only); GAPS (no arena row); MAPS_CONTENT §4.7 says only "corpses carry
nothing".
Suggested fix: keep the arena corpses' treasure empty but still roll the ruleset's extra drops — e.g. a spawn flag
that zeroes the monster's own treasure/gold yet keeps `proceduralDeathLoot` (or call the crafting/map rolls from the
kill path for `loot = false` actors), and skip them only under `madnessRewardlessMap`.

### ALC-2: Dimension affix 12 "Monster resistances are increased by X" has no effect
Severity: P2
Confidence: confirmed
MAW: `General/zzMaw-Monsters.lua:600-605` — every monster resistance (all but index 5) becomes
`min(base + X, X + 200, 999)` with X = `getMapAffixPower(12)` (30 + 2·power, e.g. +130 at power 50); outside a run X = 0
gives the usual 200 cap.
OpenYAMM: the affix is defined (`assets_dev/rulesets/maw/data/dimension_maps.yml:63`, `MawMapAffix::MonsterResistance`
in `game/rules/maw/MawDimensionMaps.h:39`) and its line shows on the map, but nothing reads it: `MawMapAffix::
MonsterResistance` appears nowhere outside the enum, and the resistance used in combat is
`mawCappedMonsterResistance` = `min(max(0, r) % 1000, 200)` (`game/rules/maw/MawCombatRules.cpp:711-714`), with no map
term. `MawMonsterRules::resolveMonster` (`game/rules/maw/MawMonsterRules.cpp:449-560`) applies affixes 15, 11, 3, 4 but
not 12.
Not covered by: DEVIATIONS 59/60 (60 lists only 25 and 33 as not ported); GAPS L8.2 (25, 33).
Suggested fix: add the run's affix-12 value to every non-physical resistance and raise the cap to 200 + X (999 at most)
where monster resistance is capped (`mawCappedMonsterResistance` callers / resolveMonster), and in the inspect text.

### ALC-3: Magic Protection potion's Protection from Magic never reaches Grandmaster, so it does not stop Dead/Eradicated
Severity: P2
Confidence: confirmed (MAW side relies on the engine's GM check, which OpenYAMM itself reproduces)
MAW: drinking 237 sets party buff 13 with Skill 3, or 4 (GM) from power 50 (`General/zzAlchemy.lua:145-153`, text
"From 50 power on will protect also from death and eradication"); then every 0.5 s aura pass while the potion lasts
forces `Power=4, Skill=10` (`General/zzMaw-Spells.lua:2985-2990`, inside `mawBuffApply`), i.e. GM-level protection for
the whole party regardless of power. The held PfM *spell* aura likewise forces `Power=50, Skill=4`
(`zzMaw-Spells.lua:2904-2907`) whatever the caster's mastery.
OpenYAMM: the potion aura source always has `mastery = Master` (`game/rules/maw/MawRules.cpp:538`), and the party PfM
slot is applied with that mastery and 1 charge (`game/rules/maw/MawSpellRules.cpp:1221-1236`; the spell aura uses the
caster's own mastery, `:1212-1217`). `Party::blockConditionWithProtectionFromMagic` refuses Dead and Eradicated below
Grandmaster (`game/party/Party.cpp:6710-6730`, `conditionRequiresGrandmasterProtectionFromMagic`). So neither the
potion (any power) nor a Master-cast aura blocks death/eradication, which MAW's always do.
Not covered by: DEVIATIONS 31 (says the potion now matches MAW: party PfM, recharged, keeps conscious — mastery not
mentioned); GAPS (none).
Suggested fix: give the potion's PfM slot Grandmaster mastery (and, for the spells owner, the held aura too), and a
few charges per refresh rather than 1 (MAW: 4 for the potion, 50 for the aura).

### ALC-4: Dimension map drop chance uses the uncapped monster level; MAW's level factor reads the byte `mon.Level` (≤ 255)
Severity: P2
Confidence: confirmed
MAW: `General/zzMaw-Maps.lua:885` — `dropChance = pity * mon.Level / 100 / (mapsDropped+1) * mult`. `mon.Level` is a
`u1` field (`reference/mmmerge/Scripts/Structs/01 common structs.lua:1255`) and MAW writes it as
`min(totalLevel, 255)` (`General/zzMaw-Monsters.lua:479-583`), so the factor never exceeds 2.55. Only the level gate
and the map's power use the uncapped `getMonsterLevel` (`:906, :921`).
OpenYAMM: `game/rules/maw/MawMonsterRules.cpp:254-256` multiplies by `level / 100.0` with `pFacts->level` uncapped. At
monster level 500 (late MAW, Doom/Insanity much higher) maps drop ~2× (×4 at 1000) as often as in MAW. The corpse-loot
code already caps to 255 where MAW reads the table level (`tableLevel`, `:897`), but the map drop does not.
Not covered by: DEVIATIONS 58 (affix count only); GAPS A2.9/none.
Suggested fix: use `std::min(level, 255)` for the chance factor; keep the uncapped level for the 100 (70) gate and the
power.

### ALC-5: A non-charge potion mixed from a partly drunk charged potion gets several drinks
Severity: P3
Confidence: confirmed
MAW: consumption is by list — potions in `potionUsingCharges` count their `Charges` down, every other potion is
removed after one drink whatever its `Charges` (`General/zzAlchemy.lua:249-259, 283`). Mixing keeps the target's
`Charges` field (engine), which is harmless for non-charge results.
OpenYAMM: `game/items/InventoryItemUseRuntime.cpp:1297` — `usesBefore = currentCharges > 0 ? currentCharges :
pPotion->charges`, regardless of whether the potion has `charges`. Mixing keeps the target's `currentCharges`
(`InventoryItemMixingRuntime::mixItems` never resets it), so e.g. a Stone Skin (234) or Water Breathing (235) with 4
drinks left, mixed with green into Divine Restoration (246: cure-all + 6 h immunity to everything), drinks 4 times;
Twilight/Dawn (258/260) from 247/248 likewise. Black potions are saved only by their best-step refusal.
Not covered by: no related row.
Suggested fix: when the potion definition has no `charges`, consume it after one drink (or clear `currentCharges` when
a mix produces a potion without charges).

### ALC-6: The four ancient blasters (866, 867, 1666, 1667) cannot be crafted on
Severity: P3
Confidence: confirmed
MAW: every crafting gate uses `IsBaseItemId` (`General/zzMaw-Items.lua:95-97`), whose bands include the four blasters;
the comment at `:105-112` says this is deliberate ("ancient weapons stay craftable by hand"). Gems, Eye, Hourglass,
Pandora's Cube (`CanTakeCube`: EquipStat ≤ 2 and skill < Shield), Mirror, Emerald, Pearl, both orbs, Crafting Cube and
Enchant Item all accept them (only the element potions refuse, skill < 7).
OpenYAMM: `MawCraftingRules::craft` requires `itemData().baseItem(id)` (`game/rules/maw/MawCraftingRules.cpp:461-469`),
and `rulesets/maw/data/items.yml` `bases` lists every id of the three bands except exactly 866, 867, 1666, 1667, so
they are refused ("Works on weapons, armour and jewellery only").
Not covered by: CRAFTING.md §3.2 states MAW's behaviour; no DEVIATIONS/GAPS row.
Suggested fix: accept those four ids as crafting targets (a crafting-only base list, or a `craftable` flag), or record a
deviation.

### ALC-7: MAW's crafting bag (Shift+B pickup routing) is not ported and not listed
Severity: P3
Confidence: confirmed
MAW: `General/zzzMaw_CraftingBag.lua:20-55, 194-255` — Shift+B marks the open bag as a crafting bag; picking up any
crafting material (1041-1070) puts it into a flagged bag of the picker or, failing that, of any party member, with
"You found an item (…)! -- <name>".
OpenYAMM: no counterpart; materials go to the picker's open bag. Only the sort-time alchemist routing exists
(`MawItemRules::alchemist`, `pickAlchemist`, `game/rules/maw/MawItemRules.cpp:2154-2179`). CRAFTING_BENCH_DESIGN §8
planned "Send crafting materials to <member>, applied on pickup and by the Sort button"; only the Sort half was built.
Not covered by: GAPS H.1, L7.2 and DEVIATIONS 131/139 cover the multibag, sorts, alchemist key and K pull, not Shift+B.
Suggested fix: apply the alchemist preference (or a crafting-bag flag) on pickup of crafting materials, or add a GAPS
row.

### ALC-8: Item rarity after orb crafting loses Ancient/Primordial, and removing Celestial always leaves Primordial
Severity: P3
Confidence: confirmed
MAW: tier (ancient/primordial), legendary affix and celestial are independent bits (`General/zMaw_ItemBits.lua:98-245`)
and rarity is read back from them (`MawItemRarity`, `General/zzMaw-Items.lua:691-715`). A Primordial item given an
affix by the Orb of Creation and later stripped of it is Primordial again; a plain (tier 0) item given Celestial and
then stripped returns to its enchant-count rarity; an Ancient one to Ancient.
OpenYAMM: one stored `lootRarity`. `mawCraftedRarity` (`game/rules/maw/MawCraftingRules.cpp:214-238`) keeps
Primordial/Ancient only while the stored value is still Primordial/Ancient, so Primordial → +affix (stored Legendary) →
−affix gives Epic; `transferCelestial` writes Primordial unconditionally when extracting (`:1020`), so any item that
was made Celestial with a charged orb becomes Primordial (value, cube step, filter, name colour) when the status is
taken out.
Not covered by: DEVIATIONS 35-43 (none about rarity bookkeeping).
Suggested fix: store the drop tier separately from the affix/celestial state (e.g. keep the rolled tier in its own
field) and derive the shown rarity as MAW does.

### ALC-9: The Workbench refuses unidentified items; MAW crafts on them
Severity: P3
Confidence: plausible (MAW's PotionEffects/UseItem handlers have no identification test; the engine path may or may
not)
MAW: none of `evt.PotionEffects[18/23/24/35/36/71-98]`, `UseItem` (`General/zzAlchemy.lua:759-1089`,
`Global/zzMAWPotions.lua`) checks `Identified`; the Mirror even produces unidentified copies (DEVIATIONS 38).
OpenYAMM: `MawCraftingRules::craft` returns "Identify the item first" (`game/rules/maw/MawCraftingRules.cpp:471-474`).
Not covered by: DEVIATIONS 36 (lists level owner, messages, cooldown, confirmations — not identification).
Suggested fix: record it as part of DEVIATIONS 36 or drop the check.

### ALC-10: Mixing uses the party's best alchemist; MAW uses the character whose inventory is open
Severity: P3
Confidence: confirmed
MAW: the reagent bonus and its overflow into Alchemy read `Party[Game.CurrentPlayer]:GetSkill(Alchemy)`
(`General/zzAlchemy.lua:601-637`), the catalyst cap too (`General/MiscTweaks.lua:784`), and the engine mixes with the
current player's skill and mastery (explosions included). MAW makes Repair party-wide (`zzMAW-Skills.lua:2019-2023`)
but not Alchemy.
OpenYAMM: `InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem` and the Alchemy bench use
`bestPartyWideUtilitySkillMember("Alchemy")` (`game/items/InventoryItemMixingRuntime.cpp:428`,
`game/items/AlchemyBenchRuntime.cpp:234`) — pre-existing Standard behaviour, kept under MAW by the bench design
(CRAFTING_BENCH_DESIGN.md:47). Practical effect is small (players open the alchemist's pack in MAW), but no deviation
row records it.
Not covered by: no DEVIATIONS/GAPS row (README §"Utility skills are party-wide" claims it for MAW generally, which MAW's
code does not do for Alchemy).
Suggested fix: add a DEVIATIONS row (UI convenience), no code change.

### ALC-11: Reagent drops roll to a potion at "> 200" with integer division
Severity: P3
Confidence: confirmed
MAW: `General/zzAlchemy.lua:679-688` — `power = s*m/2` (float), potion when `round(partyLevel/2) + power > 200`, power
`round(bonus + power)`.
OpenYAMM: `game/rules/maw/MawMonsterRules.cpp:196` — `itemLevel + alchemySkill * alchemyMastery / 2` in integers, so
an odd `s·m` loses 0.5: at exactly 200.5 MAW gives a potion of 201 (200), we give a reagent.
Not covered by: no related row.
Suggested fix: compute in double and round as MAW.

### ALC-12: Reagents and Endless Potions are not dropped by Nightmare-risen monsters or on Beyond Madness's rewardless maps
Severity: P3
Confidence: confirmed
MAW: the reagent/Endless handler (`General/zzAlchemy.lua:654-698`) skips only party-reanimated monsters
(`Ally == 9999`); the NameId > 300 (risen) and Madness map exclusions are in the other handler (`:1118-1126`).
OpenYAMM: `rollCraftingDrops` returns before the reagent and Endless rolls on `risen || madnessRewardlessMap`
(`game/rules/maw/MawMonsterRules.cpp:111-114`).
Not covered by: GAPS A4.4 ("risen monsters drop nothing" — true for gems/specials, not for MAW's reagent handler).
Suggested fix: apply the risen/madness early return only to gems and specials.

### ALC-13: Telepathy pre-rolls a live monster's crafting and map drops (pity counters move without a kill)
Severity: P3
Confidence: confirmed
MAW: crafting, reagent and map drops are rolled in `MonsterKilled` only.
OpenYAMM: Telepathy calls `revealActorLoot` (`game/party/PartySpellSystem.cpp:2596-2598`), which rolls
`mapActorCorpseLoot` → `MawMonsterRules::corpseLoot` → `rollCraftingDrops`/`rollDimensionMapDrop`
(`game/outdoor/OutdoorWorldRuntime.cpp:18943-18982`, indoor likewise), updating `craftingPity`, `mapDropPity` and
`mapsDropped` at cast time; a monster that is then not killed (flees, the party leaves) has already advanced or reset
the counters, and the status line reveals crafting/map drops MAW never shows.
Not covered by: no related row.
Suggested fix: let `revealActorLoot` roll only the table loot, and roll the ruleset extras at death.

### ALC-14: Enchant Item (238) strength rounds once where MAW truncates first
Severity: P3
Confidence: plausible (depends on MMExt truncating a float written to the i4 `BonusStrength`, as the Regeneration
potion's `JoinSkill(Bonus/2, 4)` also assumes)
MAW: `Global/zzMAWPotions.lua:73-86` — `BonusStrength = min(P,500)/5` is stored (integer field), then
`ceil(BonusStrength * slotMult)`.
OpenYAMM: `game/rules/maw/MawCraftingRules.cpp:1116-1117` — `ceil(min(P,500)/5 * slotMult)` with no intermediate floor:
P = 33 on body armour gives 10 (MAW 9), P = 7 on a two-hander 3 (MAW 2).
Not covered by: no related row.
Suggested fix: floor the fifth before the slot multiplier.

### ALC-15: Crafting Cube on a map treats the Plane of Earth (map 10, eleme.blv) as indoor
Severity: P3
Confidence: confirmed
MAW: `General/zzAlchemy.lua:1009` lists map 10 among `overworldMaps`, so a map of the Plane of Earth moves only to
outdoor places and outdoor maps can move to it.
OpenYAMM: `MawCraftingRules::craftDimensionMap` decides by the file extension (`game/rules/maw/MawCraftingRules.cpp:
577-581`), so eleme.blv is indoor. Every other dungeon id agrees with MAW's list.
Not covered by: DEVIATIONS 62 (pool/seed only).
Suggested fix: use MAW's id list (data) or accept as a deliberate correction with a note.

## Checked and matching

- Potion settings: OpenYAMM's `patches/potion_settings.txt` turns the engine table into MAW's `Data/Tables/Potion
  settings.txt` for every Drinkable/Usable cell and note; Required mastery identical (no diff); rows 71-102 (crafting
  items as usable) are irrelevant to our Workbench.
- Mixing matrix and notes: `rulesets/maw/tables/english/potion.txt`/`potnotes.txt` equal zMaw.T.lod's POTION/POTNOTES
  (quotes only). Mixed power = average; explosion by required mastery (Standard path unchanged under Standard).
- Drink rules: power cap 500, min powers 231/235/239 = 20, 246 = 40 (and the item potions 243/244 = 40, 255 = 55,
  256 = 100 in `zzMAWPotions.lua`), "Player must be active", payer order drinker → active → first ready, 60 ticks only
  near enemies, "Can't benefit anymore" refused without cost.
- Charges: the 20 charge potions and 5 drinks match `potionUsingCharges`; Endless Potion targets match `chargePotions`;
  `+min(best Alchemy + 10, 100)` drinks match MAW's raw-charge arithmetic (uses + b).
- Duration 6 h + 6 game minutes per GM Alchemy point (best GM, with item bonus).
- Effects: heals/mana `round(flat + share × estimated HP/SP at level = power)` (20/25 %, 10/25 %, 50/35 %, 50/35 %);
  immunities and cures of 224-227, 239, 246 (incl. Unconscious); Meditation `ceil(√P/1.5)+1`; Regeneration skill
  `floor(P/2)` at GM; aura potions (Haste, Heroism, Bless, Shield+Preservation, Stone Skin, Champion's, Paladin's,
  Elemental, Self, Day of the Gods, Day of Protection) at Master with fraction 0.75-1.5 over 0-200 power, span 50/70,
  level P·0.5·fraction; black potions 20/step (30 for 261/262) into the right stats/resistances with best-step refusal;
  Transcendence `5s²+15s` difference; Twilight/Dawn ages; DEVIATIONS 30-34 as recorded.
- Reagents: base table (tier-5 Mod1 30/45 patched), `floor(b(1+L·0.25/20)+0.75L)`, +½s Master / +s GM, cap 255 and
  half the excess (≤ 900) to Alchemy; Alchemy capped at 2× the skill cap; catalyst formula.
- Kill drops: gems 0.006 × √(L/10) × (boss 10, Broodling /(5−tier), no-corpse ×3, dimension `1+(P·n+20n)/800·1.5`),
  Insanity ×1.5 on gems only, Austerity zero; tier `floor(N(max(L^0.6/4+1, L/40), 2))` clamped 1-16; the nine specials'
  chances and pity `c^(1.38 − c·k/2) × bonus`, counter += round(bonus); reagents (m−2) % from Master, tier by table
  level, item level round(banked/2), potion 221-224 above 200; Endless Potion 0.2 % at GM.
- Crafting operations against `zzAlchemy.lua`/`zzMAWPotions.lua`: gem caps (`round(t/20·PrimMax)`, skill
  `ceil(max(√r, r/10))`, ×slot rounded up, DEVIATIONS 40), weaker-relative-to-cap choice, +3/+1; Eye pool D by slot;
  Hourglass type roll (rings 1-16), `min(round(s·(1..1.25)), 100·bolster mult·slot)` with the per-difficulty
  multipliers 1/1.05/1.1/1.2/1.5; Pandora steps 20/20/10/7/5/4/4/1, artifacts 2, cap 20 (DEVIATIONS 37); Mirror;
  Emerald next rung / weakest stronger base (DEVIATIONS 39); Pearl uniform over present enchantments with enc2
  promotion; Orb extract/imprint; Celestial Orb; Crafting Cube +2 weapons/body, +4 else, cap `min(floor(L/5), 120)`;
  Enchant Item type roll and skill nerf; element potions' special ids (5/8/11/14, 6/9/12/15, 59, 41) and weapon-skill
  gate.
- Shops: replace chance 0.3 (gems always), special chance `min((gold/2·10⁷)^0.7, 1)` with weights 7/7/15/2/5/7/3/15,
  gem tier `1 + min(floor(banked/25) + {0:.70, 1:.25, 2:.05}, 15)`, buy prices `reagentPrices`, sell values.
- Map completion: cube + 2 gems of `min(ceil((level+bolster)/25+0.5), 16)`; dimension run first completion by affix
  count (1070/1061/1062/1065); repeat completion gives the next map (slot chances 40/100/60/50 %, power + 1).
- Dimension maps: dungeon list, indoor/outdoor family lists and all 33 affix base/scale/kind equal MAW's tables; affix
  roll order (2, 3, 4, then 1) and active-slot mapping; drop 0.001 × completed share, pity, ×level/100, ÷(dropped+1),
  boss ×10 (Broodling share), level ≥ 100 (Madness 70 and map level 950), power `round(L/10 − U{0..3})`, RtI ≥ 30,
  failures += multiplier; quest tiers 100 → 500 (steps 20/15/10), quest map power `(tier−20)/10`, reward level × 1000
  gold and experience; run density `1 + (P·n + 20n)/300`; Eye/Hourglass/Emerald on maps.
- Black-potion turn-in quests 181/203/212/234/244/246 (`events/Global_maw.lua`) match `Global/GLOBAL.lua:98-292`.
- Save/load: potion effects and steps, crafting pity, map pity and per-map counts, dimension quest/runs, alchemist
  member are written and read.
- Standard: `PotionRules`/`CraftingRules` defaults reproduce HEAD's mixing (reagent + level, catalyst, wand recharge,
  weapon potions) — no MAW leak found.
