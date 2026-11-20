# MAW: every random roll, and how deterministic it is

Status: investigation only (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). Source: `/home/pjasicek/github/Maw-Mod-MMMerge` at `ef23ee17`. Paths are relative to
`Scripts/` unless stated. Companion data: [data/rarity_golden.csv](data/rarity_golden.csv).

Read [README.md](README.md) and [ITEMS.md](ITEMS.md) §1.4 and §1.12 first; this document goes deeper on randomness only.

## 0. Findings in short

- MAW has **two independent random streams**: LuaJIT's `math.random` (one global Tausworthe state for the whole Lua VM)
  and the engine's C runtime `rand()` (`Game.Rand()`, state `Game.RandSeed`). MAW reseeds both from many places, so
  most "unseeded" draws actually inherit whatever the last reseed left behind.
- **The rarity, enchant and artifact roll of an item is keyed by item id, not by the drop.** Every generated item
  reseeds `math.random` from `vars.SeedList[itemId]` and advances that entry. The k-th Longsword generated in a save
  always gets the same random numbers, wherever it drops. The corpse/chest/shop seed only decides *which* item id it is.
- **Corpse loot is not reliably save-scum proof in Easy..Doom.** The crafting-drop handler writes the engine
  RNG state back into the monster's seed one tick after the kill (`zzAlchemy.lua:1141`), so the seed later used for
  the corpse depends on how much engine randomness the rest of that frame consumed.
- **Telepathy does not preview the drop; it fixes a different one.** The engine generates the treasure at cast time
  from the monster's unmodified treasure fields, with no MAW loot context (chest rules, no boss bonus). In
  Insanity/Madness and for bosses it also consumes a loot seed, so the corpse would have rolled with the next one.
- **Chests and shops are only half seeded.** The engine picks the base items with an unseeded stream; only MAW's
  roll on top follows `SeedList`.
- **The bad-luck protection is a renewal process** (`pity_chance`). Its long-run averages reproduce *every* number in
  `MAW 5.0 Loot Guide.pdf` (14 tables, 154 rows, all summaries). MAW's own analytic `GetRarityDistribution` ignores
  pity and misses the PDF in the third digit (e.g. Celestial at tier 20 is 1 in 2,500 without pity, 1 in 2,449 with
  it; the PDF prints 1 in 2,400).
- **Seeded Madness boss affixes come from a stateless hash whose consecutive values step by 0.236.** Broodlord and
  Omnipotent are perfectly correlated with the affix draw; Venomous bosses are ~40 % rarer than the other 13.
- **Refill repeats crafting drops.** `mapvars` is cleared on refill, the per-monster seeds are rebuilt from the same
  inputs, and gem drops and map-item drops of monster index *i* repeat on every refill of a map.
- The Randomizer (`zzzzMalekith-Randomizer.lua`) is an `os.time()` Fisher–Yates of 101 quest items and of 452
  monster-pool slots across 185 maps. Its found-item bookkeeping is inconsistent and can duplicate or lose items.

---------------------------------------------------------------------------------------------------------------------

## 1. Streams, seed contexts and reload classes

### 1.1 The two streams

- **L**, Lua `math.random`: LuaJIT 2.1 TW223 Tausworthe (`Src/MMExtension/LuaJIT/src/lib_math.c` in the
  MMExtension tree). `math.random()` is a double in [0,1); `math.random(a,b)` is `floor(u·(b−a+1)) + a`. Seeded by
  `math.randomseed(double)`, once with `os.time()` at VM start (`Scripts/Core/Common.lua:150`, MMExtension tree).
  **Not saved**: the Lua VM survives loading a save, so L continues from wherever the session was.
- **E**, engine `rand()`: MSVC CRT, `s = s·214013 + 2531011 mod 2^32`, returns `(s >> 16) & 0x7FFF`.
  `Game.RandSeed = x` writes `_holdrand` in the CRT per-thread data (`Scripts/Structs/00 structs.lua:712`,
  MMExtension tree); `Game.Rand()` calls it. **Not saved.**

L and E are never derived from each other, except that MAW often sets both from the same number. The engine draws
from E for spawn counts, monster AI, gold dice, "does the corpse drop an item", which base item a treasure level
yields, its own hit rolls, sounds and particles.

### 1.2 Seed contexts used below

| Code | What L or E was last seeded with | Defined at |
|---|---|---|
| inh | nothing specific: inherits the last reseed of that stream (effectively unseeded across a reload) | – |
| OT | `os.time()` (1-second resolution) | several, see §3.1 |
| MS | per-map monster seed `mapvars.MonsterSeed[i]` (chain built on first map load) | `zzMaw-Items.lua:357-403` |
| MSd | MS after the post-kill write-back (drifted, see §3.8) | `zzAlchemy.lua:1138-1142` |
| TL | per-monster-type LCG `vars.monsterSeeds[id]` (Road to Insanity, Beyond Madness) | `zzMaw-Items.lua:33-61` |
| BL | boss loot seed (save seed + map hash + index + id + per-boss counter) | `zzMaw-Items.lua:64-91` |
| SL | per-item-id sequence `vars.SeedList[id]` | `zzMaw-Items.lua:987-996` |
| ES | `vars.enchantSeedList[id] + MaxCharges` | `Global/zzMAWPotions.lua:59-65` |
| IF | the target item's own fields | `zzAlchemy.lua:806, 831, 1058`, `zzMaw-Maps.lua:978` |
| PS | `pseudoSpawnpoint` seed from save seed, monster, position and map | `pseudoSpawnpoint.lua:50-67` |
| QM | `vars.seed + level*7919` | `Global/zzMaw_DimensionalMapsQuest.lua:46` |
| LC | after the `LoadMap` seed chain (first visit, Easy..Doom only) | `zzMaw-Items.lua:380-399` |
| BA | stateless hash, no stream (`(x*9301+49297) % 233280`) | `zzMaw-Monsters.lua:3142-3194` |

### 1.3 Reload classes

| Class | Meaning |
|---|---|
| **Fixed** | Reload and repeat the same action: same result. Save-scum proof. |
| **Seq** | Fixed per save, but the next element of a shared sequence (per item id, monster type or counter); doing something else first that uses the sequence changes it. |
| **Drift** | Depends on how many engine draws happened elsewhere in the same frame. Not reproducible in practice. |
| **Free** | Re-rolled after a reload. |
| **World** | No save seed involved: the same inputs give the same result in every save of every player. |
| **Visit** | Fixed once the map has been generated and saved; re-rolled if you reload a save made before entering. |

Mode ranges: "Easy..Doom" is difficulty index 1–7, everything except Road to Insanity and Beyond Madness (which set
`vars.insanityMode`); "Insanity" below means both of those unless Beyond Madness (`vars.madnessMode`) is named.

---------------------------------------------------------------------------------------------------------------------

## 2. Catalogue

U = `math.random()` uniform [0,1). U{a..b} = uniform integer. "→" = what the draw decides. "p" = `getMapAffixPower(n)`.
Files marked *(base)* are MMMerge scripts MAW ships unchanged or nearly so; they are listed for completeness.

### 2.1 Seeding sites (no gameplay draw of their own)

| # | file:line | What it does | Reload |
|---|---|---|---|
| S1 | `zzMaw-Items.lua:36, 67, 364`; `Global/zzMaw_DimensionalMapsQuest.lua:44` | `vars.seed = os.time()` on first need (first map load outside Insanity) | saved |
| S2 | `zzMaw-Items.lua:357-403` (`LoadMap`, not Insanity, `mapvars.MonsterSeed` empty) | builds the MS chain, leaves E and L seeded (LC) | Fixed per (save, map, monster count) |
| S3 | `zzMaw-Items.lua:169-205` (`PickCorpse`) | E and L ← BL (boss) / TL (Insanity) / MS (else; created as `mapSeed + index*97` if missing) | see §2.2 |
| S4 | `zzMaw-Items.lua:319-325` | next tick: `MonsterSeed[index] = Game.RandSeed` (not bosses, not Insanity) | – |
| S5 | `zzMaw-Items.lua:336-354` (`CastTelepathy`) | E ← BL / TL / MS (no L reseed); next tick writes E back to MS | consumes BL/TL |
| S6 | `zzMaw-Items.lua:988-995` (`ItemGenerated`) | creates `SeedList` once (L inh), then per item L ← `SeedList[id]` and advances it (§3.5) | Seq |
| S7 | `zzAlchemy.lua:1129-1143` (`MonsterKilled`) | E and L ← TL (Insanity: **advances the type LCG**) or MS; next tick `MonsterSeed[index] = Game.RandSeed` | MSd |
| S8 | `zzAlchemy.lua:1209-1212` | per special crafting item: `E = (E*1664525 + 1013904223) % 2^32`, L ← E | – |
| S9 | `zzMaw-Maps.lua:893-898` (`MonsterKilled`) | L ← `MonsterSeed[index] + 1337`, 1 + 3 draws | Fixed (repeats on refill) |
| S10 | `pseudoSpawnpoint.lua:50-67` | if `vars.seed`: E and L ← PS, then 10 draws of each | Fixed per spawn args |
| S11 | `zzMaw-Monsters.lua:2254-2257` (`LeaveMap`, Nightmare and up) | `MonsterSeed[i] = Game.RandSeed` (E inh), then 30 E draws | unused |
| S12 | `zzAlchemy.lua:806, 831`; `Modules/MawCore/Tooltip.lua:300, 438` | L ← IF (Eye, Hourglass, and their ALT previews) | World |
| S13 | `zzAlchemy.lua:1058, 1071` | L ← IF (Crafting Cube on a map), then L ← OT | World |
| S14 | `Global/zzMAWPotions.lua:65`; `Tooltip.lua:340` | L ← ES (Enchant Item potion and its preview) | Seq |
| S15 | `zzMaw-Maps.lua:978` | L ← IF (using a dimension map) | World |
| S16 | `Global/zzMaw_DimensionalMapsQuest.lua:46, 60` | L ← QM, then L ← OT | Fixed |
| S17 | `zzzzMalekith-Randomizer.lua:44, 135` | L ← OT before each shuffle | stored result |
| S18 | `zzMaw-Monsters.lua:2380` (`SeedDeaths.new_game`) | L ← OT, draws a 31-bit run id for the Madness death ledger (not gameplay) | stored |
| S19 | `NPCMercenaries.lua:546` *(base)* | L ← OT | – |

### 2.2 Monster corpse loot (`events.PickCorpse`, `zzMaw-Items.lua:161-327`)

All of these run after S3. "E draws" are engine draws inside `pickCorpseDefault`.

| # | file:line | → | Distribution | Stream | Reload |
|---|---|---|---|---|---|
| C1 | `:250` | regular grade: fractional part of `(lvl + 10·tier)/20` adds +1 | Bernoulli(frac) | L·MSd/TL | as below |
| C2 | `:258` | item type forced to "any" | Bernoulli(0.7) | L | |
| C3 | `:289` | boss grade fraction `lvl/20 + 2` | Bernoulli(frac) | L·BL | |
| C4 | engine | item drops at all (`TreasureItemPercent`) | Bernoulli | E | |
| C5 | engine | gold amount `TreasureDiceCount d TreasureDiceSides` | dice | E | |
| C6 | engine | base item id for grade and type | engine table | E | |
| C7 | `ItemGenerated` | rarity, enchants, artifact (§2.3) | – | L·SL | Seq |

Reload behaviour of C1–C6: bosses (all modes) **Fixed** (BL with counter, `mapvars.BossSeed[index]`); Insanity and
Madness regular monsters **Seq** per monster type (the type LCG advances once on kill, S7, and once on loot, S3; so
skipping a corpse or casting Telepathy shifts every later drop of that type); Easy..Doom regular monsters
**Drift** (S7 write-back). C7 is Seq in all modes.

### 2.3 Item generation (`events.ItemGenerated`, `zzMaw-Items.lua:973-1369`)

Runs for every engine-generated item (corpses, chests at map load, shops, `evt.GiveItem`, `Item:Randomize`), except
on screens 16/21 (party creation) and map index 0. The L stream is reseeded from SL at `:994` *before* anything below.

| # | file:line | → | Distribution | Notes |
|---|---|---|---|---|
| I1 | `:1011` | enchantable non-shop drop becomes an artifact | U < `pity_chance(0.005, artifactRollPity)` | counter +1 per failure, reset on success (§4) |
| I2 | `:1021` → `get_affix` `:1391` | which artifact | weight ∝ 1/(times found + 1) over the 104 list positions | `mawArtifacts` lists 533 twice: double weight, two counters |
| I3 | `:1040` | misc shop (house ≤ 110) turns a stock item into a crafting item | `EquipStat ≥ 12` and U < 0.3, or reagent (19) always | shop only, not Austerity |
| I4 | `:1061` | special crafting item instead of a gem | U < min((PartyGold/2·10^7)^0.7, 1) | |
| I5 | `:1069` | which special | weighted: Eye 7, Hourglass 7, Pandora 15, Mirror 2, Emerald 5, Pearl 7, Oracle 3, Cube 15 (sum 61) | |
| I6 | `:1085` | gem tier `floor(partyLevel/25)` | +2 at 5 %, +1 at 25 %, else +0; capped at 16 | |
| I7 | `:1141` | loot tier +1 | Bernoulli((dropLevel mod 15)/15) | |
| I8 | `:1146` | rarity band Common/Uncommon/Rare/Epic | one U walks normalised band widths best-first; bosses use U/4 | §5 |
| I9 | `:801` (`RollItemRarity`) | Epic → Celestial/Legendary/Primordial/Ancient | ≤ 4 Bernoulli `U < pity_chance(c, f)·m` | only after an Epic band (§4, §5) |
| I10 | `:517, 520, 522` | item power (`MaxCharges`) | `round(c·U{12..20}/20)`; Legendary U{16..20}; Ancient `max(…U{20..24}…, c+2)` | Primordial/Celestial: no draw |
| I11 | `:884` (`RollEnchantType`) | base enchant type | U{1..10} (rings U{1..16}), rejection until ≠ excluded | 1 + geometric draws |
| I12 | `:470, 474` (`rollEnchantStrength`) | enchant strength | U{Min..Max}/20 × ceiling; Min..Max = 8..20, Legendary 16..20, Ancient 20..25, Primordial/Celestial 25..25 | 25..25 still draws |
| I13 | `:1174-1175` | enchant 1 becomes a skill enchant | Bernoulli(0.1), then U{17..24} | Dodge→22 on leather/chain, Unarmed→22 on weapons |
| I14 | `:1186-1188` | enchant 2 strength and type | as I12, I11 | Rare and above |
| I15 | `:1211` | special enchant | U{1..total} over SPCITEMS `ChanceForSlot` of the pool for `clamp(grade,3,boss?6:5)` | Epic and above |
| I16 | `:1239` → `:1391` | legendary affix | `get_affix` over 25 affixes, weight ∝ 1/(found+1) | Legendary, Celestial |
| I17 | `:1305, 1309` | resistance enchant on a non-ring re-rolled | U{1..10} | only after slot moves |
| I18 | `:1320` | duplicate enchant re-rolled | U{1..10} or U{11..16}, rejection | |
| I19 | `:983` | boss drop that is not a base item | engine `Item:Randomize(strength,0)`, handler re-enters | E inh + new SL step |

Per enchantable item, the L draws in order are: next SL entry; I1 (+I2); I7; I8; I9 (0–4); I10 (0–1); I11; I12; I13
(1–2); I14 (2+); I15; I16; I17; I18. Bit-exact replay would need LuaJIT TW223 and this exact order; §7 does not
recommend chasing it.

### 2.4 Chests, ground items, shops, quest rewards

| # | file:line | → | Distribution | Stream | Reload |
|---|---|---|---|---|---|
| T1 | engine, map load | chest random items (base id per placeholder) | engine tables | E inh (before S2) | Visit; MAW roll Seq |
| T2 | `zzMaw-Items.lua:923` (`AfterLoadMap`, once per map) | chest gold piles `10·(mapLevel+bolster)·{1,2,4}·U(0.66,1.32)` | uniform | L·LC (after `Sleep(1)`) | Visit |
| T3 | `zzMaw-Items.lua:963` | loot-filter gold pile icon | U{0..1} | L inh | cosmetic |
| T4 | `zzMaw-Items.lua:4454, 4461` (`LoadMap`) | potions 264–289 on the ground or in chests | U{252..263} | L·LC | Visit |
| T5 | `zzMaw-Items.lua:4531` (`AfterLoadMap`) | chest artifacts worth ≥ 20000 replaced by boss-grade loot | `Randomize(6,0)` | E inh + SL | Visit |
| T6 | `zzMaw-Items.lua:4333, 4342` | "Redone" variant: unrolled base items in chests and on the ground | `Randomize(lootLevel, kind)` | E inh + SL | Visit |
| T7 | engine, shop refresh | shop stock base ids | engine tables | E inh | Free; MAW roll Seq |
| T8 | `zzMaw-Items.lua:3968` (R key) | reroll strength +1 for this and every later slot | U{1..18} < `MMLVL mod 18`, i.e. ((MMLVL mod 18) − 1)/18, sticky | L inh/SL | Free |
| T9 | `zzMaw-Items.lua:3974, 3977` | reroll item kind | uniform over {31,32,33,34,5} (armour shops) or over `vars.shopType[house]` | L | Free |
| T10 | `zzMaw-Items.lua:3975, 3978` | reroll base item | `Randomize(strength, kind)` | E inh + SL | Free |
| T11 | `Global/GLOBAL.lua:557, 565`; `Global/zzMAW_DruidCircletQuest.lua:18`; EVT `GiveItem` | quest reward | engine + MAW roll | E inh + SL | Free / Seq |
| T12 | `General/MenuChooseCharacter.lua:299` *(base)* | starting item enchant strength | U{1..5} | L inh | creation only |

### 2.5 Crafting-item and reagent drops

| # | file:line | → | Distribution | Stream | Reload |
|---|---|---|---|---|---|
| R1 | `zzAlchemy.lua:671` | reagent drop (Alchemy Master/GM in party) | Bernoulli((m−2)/100): 1 %/2 % | L inh | Free |
| R2 | `zzAlchemy.lua:674` | reagent tier | `round(clamp(lvl/20·U(1.75,2.25), 1, 5))` | L inh | Free |
| R3 | `zzAlchemy.lua:675` | reagent id | uniform in tier list | L inh | Free |
| R4 | `zzAlchemy.lua:686` | strong reagent becomes a potion | U{221..224} | L inh | Free |
| R5 | `zzAlchemy.lua:693` | Endless Potion (Alchemy GM) | Bernoulli(0.002) | L inh | Free |
| R6 | `zzAlchemy.lua:1146` | map affix 9: kill spawns a monster | Bernoulli(p/100) | L·MS/TL | Fixed / Seq |
| R7 | `zzAlchemy.lua:1192` | gem drop | Bernoulli(0.006·b·(1.5 Insanity)), b = `bonusRoll` (§4.3) | L·MS/TL | Fixed / Seq, repeats on refill |
| R8 | `zzAlchemy.lua:1194` → `:1106` | gem tier | `floor(N(max(lvl^0.6/4+1, lvl/40), 2))`, clamp 1..16; Box–Muller, 2 draws | L | as R7 |
| R9 | `zzAlchemy.lua:1219-1221` | each of 9 special items (independent) | U < `pity_chance(base_i, counter_i)·b`; counter += round(b) | L·LCG(E) | Fixed / Seq |
| R10 | `zzMaw-Monsters.lua:3786` (`MonsterDropItem`) | monster's carried item suppressed | Bernoulli(0.8) | L inh | Free |
| R11 | `zzMaw-Monsters.lua:4053` | post-kill object removed (ids 217, 632, 633, 640, 654 or EquipStat 13 with Bonus 0) | Bernoulli(0.8) | L inh | Free |

### 2.6 Crafting outcomes and previews

| # | file:line | → | Distribution | Stream | Reload |
|---|---|---|---|---|---|
| K1 | `zzAlchemy.lua:810` (Eye of Void, potion 91) | special enchant from pool power 6 | weighted `ChanceForSlot` | L·IF | World |
| K2 | `zzAlchemy.lua:838-840` (Hourglass, 92) | enchant 2 type and strength `round(s·(1+0.25U))` capped | I11 + U | L·IF | World |
| K3 | `zzAlchemy.lua:949` (Pearl, 96) | which enchant is removed | U{1..3} rejection until present | L inh | **Free** |
| K4 | `zzAlchemy.lua:1066` (Crafting Cube on a map) | new destination | uniform over other completed dungeons of the same kind | L·IF | World |
| K5 | `Global/zzMAWPotions.lua:22` (Greater Element, pot 35) | Ice/Thunderbolts/Infernos/Acid (6/9/12/15) | U{1..4} | L inh | **Free** |
| K6 | `Global/zzMAWPotions.lua:35` (Lesser Element, pot 23) | Frost/Lightning/Flame/Venom (5/8/11/14) | U{1..4} | L inh | **Free** |
| K7 | `Global/zzMAWPotions.lua:66-71` (Enchant Item, pot 18) | enchant type | 10 % U{17..24}, else U{1..16} rings, U{1..10} | L·ES | Seq |
| K8 | `Global/zzMAWPotions.lua:62, 87` | `enchantSeedList` init U{1..100000}; advance += U{1..1000} | uniform | L inh / L·ES | Seq |
| K9 | `Modules/MawCore/Tooltip.lua:300-323, 334-346, 438-442` | ALT previews of K2, K7, K1 | same as the apply path | L·IF / L·ES | side effect: reseeds global L on every tooltip build |

Mirror, Emerald, Pandora's Cube, Crafting Cube on items, gems, the U gem merge and both Orbs draw nothing.

### 2.7 Bosses

| # | file:line | → | Distribution | Stream | Reload |
|---|---|---|---|---|---|
| B1 | `zzMaw-Monsters.lua:2906` | affix 17: A/B-tier monster promoted one tier | Bernoulli(p/100) each | L·LC (first visit, not Insanity) or L inh | Visit |
| B2 | `zzMaw-Monsters.lua:2916` | affix 19: extra boss from an A/B monster | Bernoulli(p/100) each | same | Visit |
| B3 | `zzMaw-Monsters.lua:2932` | which C-tier monsters become bosses; count `ceil((N−30)/150)` (/60 Doom) ×(1+affix16/100) | uniform without replacement | same | Visit |
| B4 | `zzMaw-Monsters.lua:3007` | HP roll ×`(1 + 0.5U)` (Austerity ×`(1+0.125U)`) | uniform | L | Visit |
| B5 | `zzMaw-Monsters.lua:3016` | `TreasureItemType` | U{1..12} | L | Visit |
| B6 | `zzMaw-Monsters.lua:3019` | damage multiplier | U(1.2, 1.4) | L | Visit |
| B7 | `zzMaw-Monsters.lua:3050` | affix (Easy..Insanity) | uniform over 14 | L | Visit |
| B8 | `zzMaw-Monsters.lua:3051-3054` | Broodlord: HP ×1.5, damage replaced by U(1.5, 1.8) | Bernoulli(0.01·cm); cm 1, Doom 2, Insanity 3 | L | Visit |
| B9 | `zzMaw-Monsters.lua:3059-3061` | Omnipotent: HP ×4, damage replaced by U(2, 2.5) | Bernoulli(0.001·cm), can override a Broodlord | L | Visit |
| B10 | `zzMaw-Monsters.lua:3153-3159` | affix (Beyond Madness only) | BA hash of `MawBossSeed + mapHash + 31·totalBossesSpawned` | none | Seq |
| B11 | `zzMaw-Monsters.lua:3180-3226` | Broodlord (HP ×2, damage ×1.5 on B6), else Omnipotent (HP ×4, damage ×2) | BA +123 / +456 vs `pity_chance` | none | Seq |
| B12 | `zzMaw-Monsters.lua:325, 327` | boss (NameId 220–299) level, when outside 1.1–1.3× (or +10..+30) of base | `round(base·U(1.1,1.3))` (<100) or `base + U(10,30)` | L inh | Visit |
| B13 | `zzMaw-Items.lua:84` | boss loot seed counter (see §3.4) | – | BL | Fixed |

B4–B9 also run for Arena, Bounty Hunt, Survival and Broodling/Omnipotent child bosses. `generatedByBroodlord` is
read at `:3037, 3051, 3055` but never assigned anywhere, so it is always nil. `generateBossLootSeed` (`:3100`) is
never defined, so that call is dead.

### 2.8 Spawns and monster setup

| # | file:line | → | Distribution | Stream | Reload |
|---|---|---|---|---|---|
| M1 | engine, map load | spawn-point counts (`Mon{n}Low..Hi`) and tier mix (`Mon{n}Dif`) | engine | E inh | Visit |
| M2 | `pseudoSpawnpoint.lua:38, 40` | count from "a-b" or {a,b} | U{a..b} | **L inh** (drawn before the reseed) | Free |
| M3 | `pseudoSpawnpoint.lua:79-81` | position: angle U·2π, x and y radius U{1..r} each | uniform (not area-uniform) | L·PS | Fixed per args |
| M4 | `pseudoSpawnpoint.lua:124` | tier A/B/C by `powerChances` | U{1..100} | L·PS | Fixed per args |
| M5 | `zzMaw-Monsters.lua:3698` (Doom and up, once per map) | monster gets an on-hit condition | Bernoulli(√L·2/100) | L inh | Visit |
| M6 | `zzMaw-Monsters.lua:3734` | which condition (level-gated list) | uniform | L inh | Visit |
| M7 | `Modules/MawCore/Damage.lua:1809, 1828` | Summoner/Omnipotent adds on hit | Bernoulli(0.4), always on melee | L inh; spawn PS | Free |
| M8 | `zzMaw-Monsters.lua:4107` | Broodlord death spawn location | uniform over arena locations, **unused** (spawns at the corpse) | L | – |
| M9 | `Global/zzMaw_Arena.lua:261-265` | Endless Arena wave sizes (5 draws per wave call) | U{8..10}, U{6..8}, U{4..6}, U{3..4}, U{2..4} | L·PS chain | Seq |
| M10 | `Global/zzMaw_Arena.lua:271` | spawn location per monster | uniform | L·PS (previous spawn) | Seq |
| M11 | `Modules/MawCore/Fixes.lua:97` | arena pool fallback tie-break | U | L inh | Free |
| M12 | `BountyHunt.lua:197` | bounty target | uniform over `monTbl` | L inh | Free |
| M13 | `BountyHunt.lua:222, 233` | Omnipotent bounty horde U{100..200}; escorts U{5..15} | uniform | L inh | Free |
| M14 | `BountyHunt.lua:96-137` *(base)* | bounty spawn point | uniform room/facet or U{−15000..15000} | L inh | Free |
| M15 | `Maps/7out05.lua:32` | Tularean Forest night ambush (every 5 min, 22:00–04:00) | Bernoulli(0.1), forced after 23:54 | L inh | Free |
| M16 | `zzMaw-Survival.lua:74-79` | survival wave position | U{500..3500}, signs Bernoulli(0.5) | L inh | unreachable mode |

### 2.9 Combat

| # | file:line | → | Distribution | Stream |
|---|---|---|---|---|
| X1 | `Damage.lua:33` (`rollDice`; callers `:465, 476, 612, 635, 712, 833`) | weapon, dragon, DK, Assassin damage | `round((U{lo..hi}+U{lo..hi})/2)` | L inh |
| X2 | `zzMaw-Stats.lua:140` (`getCritInfo`) | crit (melee, ranged, spell, heal) | Bernoulli(min(chance,1)); legendary 14 lifts the cap | L inh |
| X3 | `zMaw-hooks.lua:191` (hook 0x4256DB) | player hits monster | Bernoulli(`mawPlayerHitChance`, 0.25..1) | L inh, after the engine's own roll (E) |
| X4 | `zzMaw-Stats.lua:254` (hook 0x425893, `MawRollDodge`) | monster hits player (speed dodge) | Bernoulli(`1/(1+speed/(100+est(L))·share)`) | L inh |
| X5 | `Damage.lua:1682-1686` | GM Dodging `1 − 1/(1+(s+10)/200)`; plus X4 again for spells/missiles | Bernoulli | L inh |
| X6 | `zzMaw-Stats.lua:1152` | incoming mitigation jitter `res + min(res,1−res)·(U+U−1)` | triangular | L inh |
| X7 | `Damage.lua:1750` | monster damage ×`(U{75..125}+U{75..125})/200` | triangular | L inh |
| X8 | `Damage.lua:655` | dragon breath ×`(0.75+0.25U+0.25U)` | triangular | L inh |
| X9 | `zzMaw-Spells.lua:1980` | spell damage: Σ over skill of U{diceMin..diceMax} | Irwin–Hall | L inh |
| X10 | `Damage.lua:1613` | friendly-fire spell damage, same dice | Irwin–Hall | L inh |
| X11 | `zzMaw-Items.lua:2133`; `zzzMaw_Artifacts.lua:462` | weapon special / artifact on-hit damage | U{lo..hi} | L inh |
| X12 | `Damage.lua:287` | Mace/Staff Master+ stun | Bernoulli(s/estSkill(L)·{0.15,0.10}·meleeMult/min(1+L/150,3)) | L inh |
| X13 | `Damage.lua:347` | Stun spell (34) lands | Bernoulli(30/(30+L'/4)), affix 13 cuts | L inh |
| X14 | `zzMaw-Spells.lua:1612` | other crowd control | roll commented out: always lands, duration decides | – |
| X15 | `Damage.lua:891` | Retaliation stun | Bernoulli(0.25·stacks) | L inh |
| X16 | `Damage.lua:571` | legendary 29 stack from AoE spells | Bernoulli(0.4) | L inh |
| X17 | `zzMAW-Skills.lua:1276`; `zzMaw-Monsters.lua:3946` | Cover, per eligible member; highest HP wins | melee 0.1+0.01s (+0.15); missile 1.05−0.99^s (+0.3) | L inh |
| X18 | `zzMAW-Skills.lua:1299` / `zzMaw-Monsters.lua:3990` | Retaliation stack | Bernoulli(s/100) | L inh |
| X19 | `zzMaw-Monsters.lua:3913` | MM6 missile target | uniform over conscious members | L inh |
| X20 | `Modules/MawCore/Classes.lua:385` | Assassin SP restore | Bernoulli(0.1+0.01s, halved ranged) | L inh |
| X21 | `Modules/MawCore/Classes.lua:345` | Elementalist next bound spell | uniform over known spells of the category | L inh |
| X22 | `Damage.lua:1150` | affix 30: player hit deals 0 | Bernoulli(p/100) | L inh |
| X23 | `Damage.lua:1735` | affix 14: incoming damage becomes Energy | `U < p` with p ≥ 20: **always** | – |
| X24 | `Damage.lua:1948` | affix 2: incoming damage doubled | Bernoulli(p/100) | L inh |
| X25 | `Global/zzMaw_Mapping.lua:2` | affix 8: condition ignores resistance | Bernoulli(p/100) | L inh |
| X26 | `Core/events.lua:2596` *(base)* | fallback target when the attacker has no monster | `Game.Rand() % n` | E |

All combat draws are Free across reloads. The cover loop on the missile path is `for i=0,#cover-1`; `#cover` is
`Party.High`, so the last member never covers and a solo character never covers missiles.

### 2.10 Dimension maps

| # | file:line | → | Distribution | Stream | Reload |
|---|---|---|---|---|---|
| D1 | `zzMaw-Maps.lua:872-904` | map item from a kill (L ≥ 100; Madness L ≥ 70, map ≥ 950) | U < pity·L/100/(dropped+1)·mult (§4.2) | L·MS+1337; Insanity L inh | Fixed / Free |
| D2 | `zzMaw-Maps.lua:909` | destination | uniform over completed dungeons | L·MS+1337 | |
| D3 | `zzMaw-Maps.lua:911-914` → `:818` | four distinct affixes of 33 | rejection sampling | L | |
| D4 | `zzMaw-Maps.lua:917-924` | affixes unlocked (`Bonus`) | 4 at 10 %, 3 at 20 %, 2 at 70 %, never 1 (`elseif bonus<=0.6` tests the constant) | L | |
| D5 | `zzMaw-Maps.lua:927` | map power `round(L/10 − U{0..3})` | uniform | L | |
| D6 | `zzMaw-Monsters.lua:2679-2689` | map from a completed rift: destination; affix slots 2 always, 3 at 60 %, 4 at 50 %, 1 at 40 % | uniform, Bernoulli | L inh | Free |
| D7 | `Global/zzMaw_DimensionalMapsQuest.lua:53-59` | quest map: destination, 4 affixes, unlocked 10/20/70 % | as D2–D4 | L·QM | Fixed per (save, level) |
| D8 | `zzMaw-Maps.lua:984, 988` | on use: three monster families | uniform from 145 indoor / 154 outdoor ids | L·IF | World |

The D6 map has `Bonus = 0`, which the use code treats as "4 unlocked", so all of its present slots are active.

### 2.11 Classes, party, miscellaneous

| # | file:line | → | Distribution | Stream |
|---|---|---|---|---|
| P1 | `zzClasses.lua:126` | final promotion when several step-2 classes exist | uniform | L inh |
| P2 | `MenuChooseCharacter.lua:271` *(base)* | birth year | U{1150..1154} | L inh |
| P3 | `NPCMercenaries.lua:229-474, 705, 722-723` *(base)*; `:351` (MAW) | mercenary face, name, skills, items, class, level; MAW drops one of two enchants at 50 % | uniform | L·OT |
| P4 | `NPCFollowers.lua:553, 849` *(base)* | follower alignment, portrait | uniform | L inh |
| P5 | `MiscTweaks.lua:392, 817` *(base)* | default name, music track | uniform | L inh |
| P6 | `Structs/extraEditableDescriptions.lua:285` | random string ids | uniform | L inh |
| P7 | `Maps/oute3.lua:78` *(base)* | cosmetic spell targets | uniform | L inh |
| P8 | `Maps/7d20.lua:8, 16, 29`, `Maps/pyramid.lua:86`, `Maps/znwc.lua:13` | EVT `RandomGoTo` content (radiation, reagent fountain) | `Game.Rand() % 6` | E |
| P9 | `Core/events.lua:1716` *(base)* | face-animation sound | `Game.Rand() % 100` | E |
| P10 | `SpellsTweaks.lua:21` *(base)* | Slow / Mass Distortion apply check | `U{5..100} + skill + 2.5m > res` | L inh |
| P11 | `AdaptiveMonstersStats.lua:302-352, 985` *(base)* | MMMerge bolster damage and spell picks | uniform | inactive: MAW sets `UseMonsterBolster=false` (`zzMaw-Monsters.lua:2135`) |
| P12 | `Maps/BrBase.lua` *(base, 28 draws)* | the Breach maze: layout, bitmap set, monsters, treasure, traps | uniform | L inh |
| P13 | `zzMaw-Spells.lua:803` | `randomizeHP` | U{1..maxHP} | defined, never called |
| P14 | `Modules/Multiplayer/Network/*` | STUN ids, debug packet drop | – | networking only |

### 2.12 Randomizer

`zzzzMalekith-Randomizer.lua:44-52` (item permutation) and `:135-139` (monster-pool permutation), both Fisher–Yates
on L·OT. Full specification in §6.

---------------------------------------------------------------------------------------------------------------------

## 3. Seeding architecture

### 3.1 Save seed

`vars.seed = os.time()` the first time any of S1's sites runs: in Easy..Doom the first `LoadMap` of a new game;
in Insanity/Madness the first kill, corpse or Telepathy. It is never re-seeded and is synced as party state in
multiplayer (`Modules/MawCore/Sync.lua:75`). Two parties created in the same second share it. Separate save-level
seeds: `vars.MawBossSeed` (`zzMaw-Monsters.lua:3122`, Insanity first boss), `vars.SeedList` (S6),
`vars.enchantSeedList` (K8), `vars.MadnessDeathSeed` (S18, an id, not an RNG seed).

### 3.2 Per-map monster seeds (Easy..Doom)

`zzMaw-Items.lua:357-403`, on `LoadMap` when `mapvars.MonsterSeed` is nil (first visit, and after every refill
because MMExtension clears `mapvars` on refill):

```
mapSeed = vars.seed + Σ_i byte(Map.Name, i)·i·13 + MapStatsIndex·47
E := mapSeed; L.seed(mapSeed)
for i = 0 .. Map.Monsters.High:
    E := E_state + i·97;  L.seed(E)              -- chained: E_state is the state left by monster i−1
    repeat 50 + (i mod 20) times: rand(); math.random()
    MonsterSeed[i] := E_state
```

The chain makes seed *i* a fixed function of (`mapSeed`, *i*) computed through all lower indices, not
`mapSeed + i·97`; it does not depend on the monster count, but the L/E state left after the loop does.
Monsters spawned later (summons, ambushes) get `mapSeed + index·97` unchained, lazily in `PickCorpse` (`:182-201`).
After the loop L and E are left in a known state (context LC), which makes the next unseeded draws of that load
(bosses, chest gold, potion re-rolls) reproducible on a first visit.

### 3.3 Per-type LCG (Road to Insanity, Beyond Madness)

`getMonsterSeed(id)` (`zzMaw-Items.lua:33-61`): first use `vars.monsterSeeds[id] = vars.seed + id·1009`; each call
returns the current value and advances `x := (x·1664525 + 1013904223) mod 2^32` (Numerical Recipes LCG). It is called
by `MonsterKilled` (crafting drops, S7), `PickCorpse` (S3) and `CastTelepathy` (S5). A normally looted kill
therefore consumes two consecutive values; an unlooted kill one; a Telepathy cast one more.

### 3.4 Boss loot seeds

`getBossLootSeed(mon)` (`zzMaw-Items.lua:64-91`):
`|vars.seed + Σ byte·i·31 + MapStatsIndex·97 + index·1337 + Id·2003 + BossSeed[index]| mod (2^31−1)`, then
`BossSeed[index] += 1`. Used by `PickCorpse` and `CastTelepathy` in every mode. `BossSeed` lives in `mapvars`, so a
refill resets it and a boss on the same index with the same id rolls the same seed again.

### 3.5 `SeedList` (per item id)

`vars.SeedList[0..2500]`, created once with `i·10^9 + U{0..999999999}` from L inh. On each `ItemGenerated`:
`L.seed(SeedList[id])`, then `SeedList[id] := id·10^9 + U{0..999999999}` from that stream. Each id therefore has
its own deterministic chain, and the MAW part of every item (§2.3) is a function of (save, item id, how many items of
that id were generated before, the pity counters). Every source shares the chain: corpses, chests, shops, rewards,
re-randomised boss drops, even non-enchantable items (potions, gold, scrolls) advance their own id's entry.

### 3.6 Other seeds

- `enchantSeedList[0..2500] = U{1..100000}`; Enchant Item seeds `entry + MaxCharges` and adds U{1..1000} after use.
- Item-field seeds: Eye/Hourglass `Number·10^4 + MaxCharges·10^3 + Bonus·100 + BonusStrength·10 + Charges`
  (collisions are possible: the terms overlap); Cube-on-map `BonusStrength + Bonus2·1000 + Charges + 10^6`; map use
  `BonusExpireTime + Bonus2·10^3 + Charges·10^6 + MaxCharges·10^9 + BonusStrength·10^12`. None includes the save
  seed.
- `pseudoSpawnpoint`: `vars.seed + monster·73 + x + 19y + 31z + Σ byte·i·7`, then 10 draws of each stream. `x`, `y`
  are often fractional; map scripts that pass `Z=` (capital) contribute 0.
- Boss affixes (Beyond Madness): `h(s) = ((s·9301 + 49297) mod 233280)/233280` with
  `s = MawBossSeed + Σ byte·i + MapStatsIndex·7 + 31·totalBossesSpawned (+123 Broodlord, +456 Omnipotent)`.
  Consecutive bosses step by 31·9301 mod 233280 = 0.23599 of the unit interval, a Weyl sequence. The Omnipotent value
  is the Broodlord value + 0.27689 (mod 1) and the affix value is the Broodlord value + 0.09592: Broodlord fires when
  its value is small, which is when the affix value falls in Venomous's slot, so Venomous drops to 4.3 % of bosses
  (others 6.8–7.1 %). Simulated over 100,000 bosses: Broodlord 3.16 %, Omnipotent 0.28 %, independent of the seed.

### 3.7 Interaction with `Game.RandSeed`

- MAW writes E at S2, S3, S5, S7, S8, S10, S11. Each write also changes the engine's own later behaviour (AI,
  spawns, sounds) until the next write: e.g. after every `pseudoSpawnpoint` the engine stream restarts from a value
  derived from the spawn position.
- E values above 2^31 are stored as signed 32-bit, so reading `Game.RandSeed` back can be negative; Lua's `%` keeps
  the LCG results non-negative.
- The engine draws for a corpse (drop or not, gold, base id) come from E; MAW's draws come from L. Seeding both from
  one number makes them correlated but not identical streams.

### 3.8 Where determinism leaks

1. **Post-kill write-back** (`zzAlchemy.lua:1141`, `RunNextTick`): the corpse seed becomes "MS after the rest of the
   frame's engine draws". Corpse gold, drop chance and base id are Drift in Easy..Doom.
2. **Telepathy** generates the treasure at cast time (engine `SetRandomGoldIfTheresNoItem`, see OpenEnroth
   `src/Engine/Objects/Actor.cpp:186`) with the monster's *unmodified* `TreasureItemPercent/Level/Type` and no
   `LootContext` (drop level falls back to `MawMapDropLevel`, no boss tier or U/4 band). It then consumes a BL/TL
   value the corpse would have used. The corpse later yields the stored items; `PickCorpse`'s rewrites are ignored.
   The hook behind MMExtension's `CastTelepathy` event (`mm78(0x4086E9, 0x408E89)`) is that pre-generation routine
   itself; in MM7 the engine also calls it when stealing from a monster (OpenEnroth `Character::StealFromActor`), so
   a steal attempt most likely has the same effect in MM8 (not checked in the MM8 binary).
3. **Unconsumed loot context**: `LootContext.set` happens on every corpse pick, but only `ItemGenerated` consumes it.
   A boss corpse that rolls no item (Broodlings drop at 4–30 %) leaves `boss=true` for the next generated item
   anywhere: a chest, a ground item or a shop slot.
4. **Order dependence**: SL (per id), TL (per type), artifact/legendary-affix counts and every pity counter are shared
   sequences. Looting corpse A before B swaps their outcomes if both drop the same base id.
5. **Global L pollution**: tooltips (K9), `getCritInfo` in UI code (`zzMaw-Stats.lua:310-371`), `pseudoSpawnpoint`
   and item generation all reseed or consume L. Any later "unseeded" draw is a deterministic function of whatever
   happened last, but the Lua state is not saved, so after a reload it is effectively random.
6. **Unseeded engine generation**: chest placeholders (map load, before S2), shop stock, quest rewards, the R reroll,
   chest artifact replacement. Only MAW's roll on top is sequenced.
7. **Refill repetition**: `mapvars` is cleared on refill and MS/BossSeed are rebuilt from the same inputs. Monster
   *i*'s crafting rolls (R7–R9) and map-drop roll (D1) see the same uniforms again; with higher levels the drop
   thresholds only grow, so the same indices keep dropping. Bosses chosen on a first visit after refill (B3) are
   also a deterministic function of the monster count.
8. **Insanity has no LC**: `LoadMap` seeds nothing there, so boss selection, Doom buffs and chest gold are Free.
9. **Respawn seed** (S11) takes E at departure, but it is effectively unused: revived monsters (NameId > 300) get
   no item, no gold and no crafting or map drops.
10. **World-constant crafting**: Eye, Hourglass, Cube-on-map and map contents depend only on item fields; ALT shows
    the result, and anyone can reproduce it in any save.
11. **Index-keyed state**: MS, BossSeed and `uniqueMonsterLevel` are keyed by monster array index, which changes if
    the engine compacts or reuses slots.

### 3.9 What is actually save-scum resistant

| Outcome | Easy..Nightmare | Doom | Insanity / Madness |
|---|---|---|---|
| Boss corpse: drop, gold, base id | Fixed | Fixed | Fixed |
| Regular corpse: drop, gold, base id | Drift | Drift | Seq (type) |
| Rarity/enchants/artifact of any item | Seq (id) | Seq (id) | Seq (id) |
| Chest base items, shop stock, rewards | Visit / Free | Visit / Free | Visit / Free |
| Gem and special crafting drops | Fixed (per index, repeats on refill) | same | Seq (type) |
| Reagents, Endless Potion | Free | Free | Free |
| Map item drop (D1) | Fixed (repeats on refill) | same | Free |
| Boss selection and stats | Visit (LC) | Visit (LC) | Free |
| Boss affix | Visit (LC) | Visit (LC) | Free (Insanity), Seq (Madness) |
| Eye / Hourglass / Enchant Item | World / World / Seq | | |
| Pearl, Lesser/Greater Element | Free | | |
| Combat | Free | | |

---------------------------------------------------------------------------------------------------------------------

## 4. Bad-luck protection

### 4.1 The function

`pity_chance(c, f) = c^(1.38 − 0.5·c·f)`, or 1 when `c ≥ 1` (`zzMaw-Items.lua:4472-4478`). At `f = 0` it returns
`c^1.38`, far below `c`; it reaches 1 when `f = 2.76/c`. Past that the exponent goes negative and the value exceeds
1, which every caller treats as certain. Every user multiplies the result by a factor afterwards (see table), so the
effective hazard is `h(k) = min(pity_chance(c, k·inc)·mult, 1)` after k failures.

### 4.2 Counters

| Counter (`vars.`) | Base c | Increment on failure | Reset | Multiplier on chance | Where |
|---|---|---|---|---|---|
| `celestialPityCounter` | 0.002 | +mult on every Epic-band roll that ended below Celestial and could have produced it | on Celestial | rarity mult (§5.1) | `zzMaw-Items.lua:794-818` |
| `legendaryPityCounter` | 0.03 | +mult when the result is below Legendary (a Celestial does not charge it) | on Legendary | rarity mult | same |
| `primordialPityCounter` | 0.04 | +mult when the result is Ancient or Epic | on Primordial | rarity mult | same |
| (Ancient) | 0.12 | none | – | rarity mult | same |
| `artifactRollPity` | 0.005 | +1 per enchantable non-shop item that did not become an artifact | on artifact | 1 | `:1008-1032` |
| `craftPityCounters[1061..1070]` | see the rows of §4.3 | +round(b) per kill | on that item | b = bonusRoll | `zzAlchemy.lua:1206-1236` |
| `mapDropFailures` | 0.001 × completed share | +mult (1; bosses 10; Broodlings 10/(5−tier)) if L ≥ req. | on a map drop | L/100/(dropped+1)·mult | `zzMaw-Maps.lua:870-933` |
| `broodlordPityCounter` | 0.01·cm = 0.03 | +1 per non-Broodlord boss | on Broodlord | 1 | `zzMaw-Monsters.lua:3196-3226` (Madness) |
| `omnipotentPityCounter` | 0.001·cm = 0.003 | +1 per boss that was neither | on Omnipotent | 1 | same |
| `artPity[i]`, `legendaryAffixDropped[i]` | – | +1 to the picked entry | never | weights ∝ 1/(count+1) | `get_affix` `:1372-1402` |

`bonusRoll` b = √(L/10) × (10 boss; 1/(5−tier) Broodling; 3 for corpse-less monsters; dimension-map bonus), ÷ players
in multiplayer, 0 in Austerity.

### 4.3 Numbers (computed by running MAW's `pity_chance` in Lua 5.4)

Increment 1, multiplier 1. "E[wait]" is the expected number of trials to a success; "ratio" is E[wait]·c.

| Counter (c) | Chance at f=0 (÷ c) | Certain at f | E[wait] (ratio) | Median / 90 % / 99 % wait | Without pity |
|---|---|---|---|---|---|
| Celestial 0.002 | 0.0189 % (0.094) | 1380 | 489.7 (0.979) | 511 / 699 / 809 | 347 / 1151 / 2301 |
| Legendary 0.03 | 0.792 % (0.264) | 92 | 32.9 (0.987) | 33 / 53 / 65 | 23 / 76 / 152 |
| Primordial 0.04 | 1.18 % (0.294) | 69 | 24.8 (0.990) | 25 / 41 / 50 | 17 / 57 / 113 |
| Artifact 0.005 | 0.0668 % (0.134) | 552 | 196.0 (0.980) | 204 / 291 / 341 | 139 / 460 / 919 |
| Pandora, Crafting Cube, map drop 0.001 | 0.00724 % (0.072) | 2760 | 978.8 (0.979) | 1022 / 1363 / 1562 | 693 / 2302 / 4603 |
| Emerald 0.00025 | 0.00107 % (0.043) | 11040 | 3905.9 (0.976) | 4074 / 5221 / 5887 | 2773 / 9210 / 18419 |
| Eye, Hourglass, Pearl 0.0002 | 0.000786 % (0.039) | 13800 | 4879.8 (0.976) | 5087 / 6486 / 7296 | 3466 / 11512 / 23024 |
| Oracle's Orb 0.00006 | 0.000149 % (0.025) | 46000 | 16210 (0.973) | 16858 / 20956 / 23329 | 11553 / 38376 / 76751 |
| Mirror 0.00001 | 1.26·10⁻⁵ % (0.013) | 276000 | 96629 (0.966) | 100095 / 120912 / 132944 | 69315 / 230258 / 460515 |
| Celestial Orb 0.0000025 | 1.86·10⁻⁶ % (0.007) | 1104000 | 384322 (0.961) | 396978 / 471363 / 514335 | 277259 / 921033 / 1842066 |
| Broodlord 0.03 | as Legendary | 92 | 32.9 | | |
| Omnipotent 0.003 | 0.0330 % (0.110) | 920 | 326.6 (0.980) | 341 / 474 / 552 | 231 / 767 / 1533 |

Chance after N failures (%): Legendary 0.79 (N=0), 1.34 (10), 2.95 (25), 11.0 (50), 100 (92). Primordial 1.18, 2.24,
5.89, 29.4 at 0/10/25/50, 100 at 69. Celestial 0.019, 0.035 (100), 0.065 (200), 0.42 (500), 9.4 (1000), 100 (1380).
Artifact 0.067, 0.25 (100), 0.94 (200), 50.2 (500), 100 (552). Pandora/Cube 0.0072, 0.010 (100), 0.041 (500),
0.23 (1000), 7.2 (2000), 100 (2760).

With a multiplier m (counter +m, chance ×m) the rarity upgrades wait E ≈ 0.98–1.06 × 1/(c·m): Celestial 652.7 / 489.7
/ 245.2 / 123.0 Epic rolls at m = 0.75 / 1 / 2 / 4; Legendary 43.7 / 32.9 / 16.7 / 8.7; Primordial 32.8 / 24.8 /
12.7 / 6.6. The fastest certainty (Beyond Madness boss, m = 4) is after 23 failed Epic rolls for Legendary, 18 for
Primordial and 345 for Celestial.

Crafting specials per kill, E[kills] with pity vs flat 1/(c·b):

| b (level) | Pandora/Cube | Eye/Hourglass/Pearl | Mirror |
|---|---|---|---|
| 0.45 (L ≈ 2) | 30,680 vs 2,222 | 282,700 vs 11,111 | 1.8·10⁷ vs 2.2·10⁵ |
| 1 (L 10) | 979 vs 1,000 | 4,880 vs 5,000 | 96,630 vs 100,000 |
| 3.16 (L 100) | 322 vs 316 | 1,608 vs 1,582 | 31,910 vs 31,650 |
| 31.6 (boss L 100) | 31 vs 32 | 154 vs 158 | 3,027 vs 3,165 |

Observations:

- The tuning comment ("average wait within 2 % of 1/chance") holds for Legendary and Primordial (1.0–1.3 %), and
  roughly for Celestial and artifacts (2.0–2.1 %); the crafting rates wait 2.1–3.9 % less than nominal.
- Pity mostly reshapes the spread: the 99th-percentile drought is 2.3–3.6× shorter, and right after a reset the
  chance is 0.7–29 % of the printed one.
- **b < 0.5 rounds the increment to 0**: monsters below level 2.5 never charge crafting pity and roll at `c^1.38·b`,
  13–80× rarer than the flat chance.
- The rarity counters are shared by regular drops and boss drops, so in real play bosses also ride the counter that
  regular drops built up, and vice versa. The PDF numbers are per-source steady states.
- `get_affix` is anti-repeat rather than pity: after one Legendary affix, that affix is 2.04 % and each other 4.08 %.

---------------------------------------------------------------------------------------------------------------------

## 5. Golden rarity distributions

### 5.1 Model

Per drop at loot tier t and difficulty index d (1 Easy, 2 Normal, 3 MAW, 4 Hard, 5 Hell, 6 Nightmare, 7 Doom,
8 Road to Insanity, 9 Beyond Madness; `GetDifficulty`, `zzMaw-Stats.lua:1507`):

1. Band shares (Common..Epic) from `GetEnchantBands(t, d)`. Bosses: the uniform is divided by 4, so the shares are
   the bands clipped to the first 25 points of the 100, renormalised.
2. Upgrade multiplier `mult = rarityDifficultyMult[d] · min(60+t, 80)/80` (×2 bosses).
3. The Epic share then splits by the long-run cascade. Celestial is checked first and its counter moves on every
   other result, so it is an independent renewal process with hazard `h(k) = min(pity_chance(0.002, k·m)·m, 1)`:
   `f_C = 1/E[W_C]`. Legendary only sees rolls that were not Celestial, and its counter stands still on a Celestial:
   `f_L = (1 − f_C)/E[W_L]`. Likewise `f_P = (1 − f_C − f_L)/E[W_P]`, `f_A = (1 − f_C − f_L − f_P)·min(0.12m, 1)`,
   Epic is the rest.

Validation:

- The "nominal" variant (step 3 with flat chances) equals MAW's `GetRarityDistribution` to 3·10⁻¹⁶ for all
  9 × 21 regular rows; the harness loads MAW's own code, extracted verbatim from `zzMaw-Items.lua:574-851, 1372-1402,
  4466-4478`.
- The renewal model matches a Monte Carlo of 4·10⁶ Epic rolls through MAW's own `RollItemRarity` (with live `vars`
  counters) within sampling error at (MAW, t20), (Madness boss, t20), (Nightmare, t0), (Madness boss, t0).

### 5.2 Comparison with `MAW 5.0 Loot Guide.pdf`

The PDF (rendered with `pdftoppm`, 14 pages) has, for MAW, Hard, Hell, Nightmare, Doom, Road to Insanity and Beyond
Madness, a regular and a boss table at even tiers 0–20 (Common..Legendary), a "1 in N Ancient or better, Celestial
1 in N" line under each, and a side-by-side tier-20 summary.

- **Every table cell matches** the renewal model when formatted like the PDF (one decimal at ≥ 10 %, two below):
  14 tables × 11 rows × 7 columns, including the boss "—" cells and boss Uncommon 20.0 % / 4.00 % (MAW t0/t2) and
  8.43 % (Hard t0).
- **Every summary matches**: e.g. MAW regular 1 in 27, Celestial 1 in 2,400 (model 27.3, 2,449); MAW boss 1 in 4,
  1 in 310 (3.6, 307); Hard 22 / 2,000 (22.3, 1,989); Hell 19 / 1,700; Nightmare 16 / 1,400; Doom 13 / 1,100;
  Insanity 11 / 900; Madness 8 / 700; Madness boss 1 in 2, 1 in 120 (1.6, 123). Side-by-side tier-20 table: Ancient+
  3.66 / 27.6 (MAW), 4.48 / 33.5, 5.29 / 39.4, 6.44 / 46.0, 7.56 / 51.3, 9.51 / 56.4, 12.1 / 61.3; Celestial 0.041 %
  … 0.81 %. The prose claims also hold: boss = 5.1–7.5 regular drops (model 5.08–7.53), Madness/MAW = ×3.3 regular,
  ×2.2 boss; bosses are always at least Epic from tier 19 (Nightmare), 18 (Doom), 14 (Insanity), 10 (Madness).
- **The analytic `GetRarityDistribution` does not match** at the third digit, because it ignores pity: MAW t20
  Primordial 0.774 % (PDF 0.78), Legendary 0.599 % (0.61), Celestial 1 in 2,500 (2,400). Use the pity model as the
  oracle.
- The PDF says "Easy and Normal roll exactly the same table as MAW": true, d = 1, 2, 3 are identical.
- Unrendered placeholders on PDF p. 13, filled in from the code: right after a reset the chance is about **26 %**
  (Legendary), **29 %** (Primordial), **9 %** (Celestial) of the printed value; certainty after **92**, **69**,
  **1,380** failed Epic-band rolls on MAW (m = 1), down to **23**, **18**, **345** for a Beyond Madness boss (m = 4).
  Four affixes multiply the upgrade chance by **×1.50** at map power 30 and **×1.70** at 50. Austerity's ceiling at
  tier 20 is **22** instead of **49**. A shop Ancient rolls at **4 %** of Epic rolls instead of **12 %**.

### 5.3 `data/rarity_golden.csv`

756 rows: 9 difficulties × {regular, boss} × {`pity_longrun`, `nominal`} × tiers 0–20. Columns:

| Column | Meaning |
|---|---|
| `difficulty_index`, `difficulty` | 1–9 as above |
| `source` | `regular` or `boss` (U/4 band window, upgrade mult ×2) |
| `model` | `pity_longrun` (matches the PDF; use this one) or `nominal` (`GetRarityDistribution`, bosses extended) |
| `loot_tier` | 0–20; tiers above 20 equal tier 20 |
| `upgrade_mult` | the cascade multiplier m |
| `common` … `celestial` | percent of drops |
| `ancient_plus`, `one_in_ancient_plus`, `one_in_celestial` | summaries |

Not modelled (all change the numbers): map affixes (tiers and the ×(1 + (P+20)·n/400) multiplier), shops, Austerity
(no Legendary/Celestial), Omnipotent (always Celestial), and the shared-counter mixture of regular and boss drops.

---------------------------------------------------------------------------------------------------------------------

## 6. Randomizer (`General/zzzzMalekith-Randomizer.lua`, 408 lines)

**Enabling.** A "Randomizer" tumbler at (485, 55) on the party-creation screen (21) sets `Game.RandomizerMode`;
`BeforeNewGameAutosave` copies it to `vars.RandomizerMode` (`:374-408`). There is no way to turn it on later.

**Item half.**

- Lists (`:1-16`): MM8 ids `516 541 602–616 623 626 627 630 636 637 639 641 652 658–661 741 742` (32); MM7 ids
  `487 542–544 600–603 605–607 614 615 617–624 626 628 629 633 638–645 647 648 651 676 677 683 705`, +802
  (40, i.e. 1289…1507); MM6 ids `400 433 434 448 449 455–459 464 475 479–481 485 486 498 499 502–504 506 508 543
  550–553`, +1620 (29, i.e. 2020…2173). 101 quest and key-like unique items. `keysMM8/MM7/MM6` and
  `emeraldIsland` are defined and never used.
- First `LoadMap` with the mode on (`:18-25`): `OriginalItemOrder` = the 101 ids; `Randomizer` = a Fisher–Yates
  permutation of it (L·OT, `:43-54`); `ItemFound = {}`. All three are saved (`vars`) and host-synced.
- Every `LoadMap` (`:56-79`): each chest item and ground object whose id is in the list and **not in `ItemFound`** is
  replaced by its image `Randomizer[pos]`, and **the new id** is appended to `ItemFound`. Ground objects also get
  the new sprite.
- `Action` 404 or 14 (quest/NPC item grants, `:81-100`), next tick: every listed id the party holds that is not in
  `ItemFound` is removed and replaced by its image, and **the original id** is appended; the mouse item is swapped
  the same way but appends the new id.
- Constraints and defects:
  - No logic constraint: an item needed to progress can land on another continent or behind content that needs it;
    nothing checks reachability.
  - The double bookkeeping (new id from chests, original id from grants) lets one placement suppress another: if
    chest A's X became Y, a later chest that originally holds Y keeps Y, so Y exists twice and Y's own image Z is
    never placed from there. Order of discovery decides which items are lost.
  - Every `LoadMap` scans every chest, including unopened ones, so replacements happen on map entry, not on opening.
  - Shops, monster drops and `evt.Add` grants without Action 14/404 are not intercepted.

**Monster half.**

- `BeforeLoadMap`, once (`:116-142`): `SetMonsterDensity()` rewrites `Mon{n}Low/Hi/Dif` from `BackupMapStats` by the
  legacy rules (`:211-372`: Hard +1 Hi, Hell Low ≥ 2, Nightmare Hi +3 and Dif +1, Doom Hi +4, Insanity Low 3, Madness
  Low 5 and Hi +6, then big monsters thinned by `monsterPicTable[pic]/18|14|10`). Then a pool of
  `{Pic, Dif, Hi, Low}` is collected from every `MapStats` row 1..High except 53 (Arena), 61 (NWC), 132 (The Small
  House), 200, 206 (Breach base), 207 (Strange Temple), for each non-"0" Monster1/2/3 picture (Monster3 "DemonQueen"
  excluded). With MAW's `mapstats.txt` that is **452 slots on 185 maps** (184 / 166 / 102 by slot). The pool is
  shuffled (L·OT) and saved as `vars.MonsterShuffleList`.
- Every `BeforeLoadMap` (`:143-170`): the same traversal reassigns slot by slot, so each map slot receives a random
  other slot's monster **with that slot's density and difficulty**. A non-randomizer game loaded later in the same
  session gets the original table back.
- One-off fix (`:106-115`): "DemonQueen" entries become "DemonFly" (only reachable through Monster1/2 slots).
- Interactions: `AdjustMonsterDensity` is skipped in randomizer mode (`zzMaw-Monsters.lua:766`), so the densities are
  frozen at creation by the legacy rules and do not follow a later difficulty change. Monster levels still come from
  MAW's map levels, so a starting map can field any family at the map's level. Town maps' pools are shuffled too.
- Not seeded from the save seed; reproducible only through the stored permutation.

---------------------------------------------------------------------------------------------------------------------

## 7. Recommended OpenYAMM design

### 7.1 Today in OpenYAMM

- `game/gameplay/HouseServiceRuntime.cpp:450` seeds shop stock from `party.houseStockSeed()`, house id and
  `refreshSequence`: already a keyed stream.
- `game/outdoor/OutdoorWorldRuntime.cpp:5182` creates `m_sessionChestSeed` from `random_device` and time when a map
  is first initialised, then saves it (`game/maps/SaveGame.cpp:1673`): chests are Visit-class, like MAW's.
- `game/gameplay/CorpseLootRuntime.cpp:266, 355` use a `thread_local std::mt19937(random_device)`: corpse loot is
  Free.
- `game/gameplay/GameplayCombatController.cpp:362` builds monster-attack RNGs from frame ticks and event fields.
- About 170 references to `std::mt19937` in `game/` and `engine/`; there is no shared RNG service.

### 7.2 One service, named counter-based streams

- A save-level `rootSeed` (64-bit), created at new game, stored in the save header, shown in debug UI, settable from
  a scenario or the command line.
- A stream is a key, not a state: `key = hash(rootSeed, domain, a, b, c)`, and draw *n* is `mix(key, n)` (SplitMix64
  or a Philox-style counter mixer). Only the per-stream counter `n` needs saving, and only where a stream is reused.
  Most MAW streams never need a counter because their key is unique (an actor's spawn id, a chest slot).
- Keys use stable ids: map id, actor spawn uid (not array index), chest id and slot, house id and refresh sequence,
  item uid. `domain` is a small enum, so adding a domain never shifts another.
- A `RollContext` object hands out draws in a fixed order per domain; the rules code never touches a global RNG.

### 7.3 Which MAW draws get which stream

| Domain key | MAW draws | Notes |
|---|---|---|
| `loot.corpse(map, visit, actorUid)` | C1–C6, then the item roll I1–I19 as a sub-stream | generate at kill time and store on the actor: Telepathy shows the real drop, no write-back drift |
| `loot.chest(map, visit, chest, slot)` | T1, T2, T5, T6 + item roll | replaces `m_sessionChestSeed`'s random_device |
| `loot.ground(map, visit, objectId)` | T4, T6 | |
| `shop.stock(house, refreshSeq)`, `shop.reroll(house, rerollSeq)` | T7–T10 + item roll | extends the existing `createStockRng` |
| `reward(questId or eventId, n)` | T11 | |
| `item.roll(sourceKey)` | I1–I19 | keyed by the *drop*, not by item id: removes MAW's per-id order dependence (a documented deviation) |
| `craft.drop(map, visit, actorUid)` | R1–R9, D1–D5 | `visit` increments on refill, so refills do not repeat drops (deviation) |
| `craft.apply(itemUid, craftCount, reagent)` | K1–K7 | preview = apply by construction; adding `rootSeed` deviates from MAW's world-constant seeds |
| `boss.select(map, visit)`, `boss.stats(map, visit, actorUid)` | B1–B9, B12 | |
| `boss.affix(bossCounter)` | B10, B11 | a real stream instead of the 9301/49297 hash; fixes the Venomous skew |
| `spawn(map, visit, spawnPointId)`, `spawn.script(scriptId, callIndex)` | M1–M6, M9–M16 | |
| `dimension(mapItemUid)`, `dimension.quest(level)` | D6–D8 | |
| `randomizer` | §6, both halves | one stream at new game; store the permutations |
| plain session RNG | X1–X26, P1–P14 | combat and cosmetics stay unseeded in play |

As built (2026-10-24): corpse loot, crafting drops and applications, bosses, dimensions and their quests use their streams. A completed run's next map, BecomeBoss and HigherTier have their own domains (19-21), as the shared Dimension keys could coincide (audit ROB-2-9). Chests, ground items, shops, rewards and spawns keep the engine's per-visit seeds (`m_sessionChestSeed`, `createStockRng`), so they do not repeat from the root seed alone; their domain numbers (2-7, 13, 14) stay unused. The corpse stream also mixes in the visit seed, so a fixed root seed does not repeat a kill's drop either.

Pity counters, `get_affix` counts and the boss counter are ruleset save state (`MawRuleState`), not hidden globals.
UI code (tooltips, Power/Vitality) must never draw from a gameplay stream.

### 7.4 Headless tests and multiplayer

- Unit tests: rarity roller vs `data/rarity_golden.csv` (`pity_longrun` rows) by Monte Carlo with a tolerance, and the
  analytic bands exactly; `pity_chance` vs §4.3; the renewal formula vs simulation.
- Scenario tests: `--set rules.root_seed=…` plus the counter-based streams make "kill actor X in map Y" produce the
  same item every run; combat can get its own session stream seeded by the scenario for full replay.
- Multiplayer: the host owns `rootSeed` and the counters; streams keyed by stable ids need no stream-state sync, and
  clients can verify or pre-compute loot. Decide whether pity counters are per party (MAW: per party, `Sync.PartyVars`)
  or shared.

---------------------------------------------------------------------------------------------------------------------

## 8. Corrections to existing docs

Not edited; listed for the owners of those files.

**README.md**

- §2.4 "Anti-save-scum: every corpse, chest, shop and crafting outcome is seeded from a per-save seed, so reloading
  does not change loot. Telepathy previews the real drop." Only partly true: corpse loot drifts in Easy..Doom
  (§3.8 item 1), chest and shop base items are unseeded, Pearl and the element potions are unseeded, Eye/Hourglass are
  seeded from item fields only, and Telepathy fixes a drop rolled under different rules (§3.8 item 2).

**ITEMS.md**

- §1.4 "`GetRarityDistribution` being the analytic form": it is the no-pity form; the PDF is the pity long-run
  average and differs in the third digit (§5.2).
- §1.4 "The exponent 1.38 was tuned so the average wait equals 1/base": waits are 0.961–0.990 × 1/base (§4.3).
- §1.11 reroll: the extra strength is `U{1..18} < MMLVL mod 18`, i.e. probability ((MMLVL mod 18) − 1)/18, and once
  raised it stays raised for the remaining slots.
- §1.12 "each monster i gets seed + i·97": the seeds are chained (§3.2). "so each corpse's loot is fixed per save
  regardless of reloads or kill order": not in Easy..Doom (post-kill write-back), and order matters everywhere
  through `SeedList`. "CastTelepathy uses the same seeds, so Telepathy previews the real drop": wrong (§3.8).
  "Shops and chests are deterministic per save as well": only MAW's roll; the base items are unseeded. The Insanity
  type LCG advances on kill, on loot and on Telepathy.
- §3.3: Lesser and Greater Element potions are unseeded too; Eye/Hourglass seeds contain no save seed, so the result
  is the same in every save.
- §3.5: special drops reseed L from an LCG step of `Game.RandSeed` per item; with b < 0.5 the counter never grows.
- §4.1 "`mawArtifacts` (98 ids)": 104 entries, 103 distinct; 533 appears twice (double weight), 532 is absent.
- §4.4: `ItemFound` records the new id for chests and ground items but the original id for grants (§6 defects).

**COMBAT.md**

- §3.5 "Insanity and Madness use seeded affix rolls": only Beyond Madness (`getMapSeedForBossAffixes` needs
  `insanityMode`, and the branch also needs `madnessMode`); Road to Insanity uses the random path with chanceMult 3.
  The seeded Broodlord is HP ×2 and damage ×1.5 on top of U(1.2,1.4) (not ×1.5 and U(1.5,1.8)); the seeded Omnipotent
  multiplies damage by 2 (not U(2,2.5)). In the §4 difficulty table, "Insanity: ×3 specials, seeded" should read
  "not seeded".
- §2.9 step 6 "Map affix 14 changes the type to energy": always, because the roll compares U with a power ≥ 20.
- §6.8 dimension maps: dropped maps unlock 2 affixes at 70 %, 3 at 20 %, 4 at 10 %, never 1; maps from a completed
  rift have 1–4 slots filled (40/100/60/50 %) and all of them active.
- The MM6-missile Cover loop skips the last party member and never fires for a solo character.

---------------------------------------------------------------------------------------------------------------------

## 9. Not covered

- Engine-internal randomness of MM8 itself (AI, spawn-point placement, engine item generation tables, engine hit
  rolls not hooked by MAW, spell effects, particles). Only the places where MAW seeds or replaces them are listed.
- Bit-exact reproduction of MAW streams (LuaJIT TW223 plus MSVC `rand` plus the engine's call order). Not attempted
  and not recommended.
- The Breach maze generator (`Maps/BrBase.lua`) and `NPCMercenaries.lua` are base MMMerge and listed only by site.
- `zzMaw-Survival.lua` is unreachable (README §6) and was not analysed beyond its draws.
- The multiplayer module's networking randomness and how its boss-sync snapshots interact with seeds.
- Austerity, shop and map-affix variants of the rarity tables (§5.3), and the mixture of regular and boss drops on
  the shared pity counters.
- Whether `Map.Monsters` indices stay stable through engine slot reuse (relevant to §3.8 item 11) was not checked in
  the engine.

The Lua harness used for §4 and §5 loaded MAW's functions verbatim from `zzMaw-Items.lua` into a stock Lua 5.4
interpreter; it lived in the session scratchpad and is not part of the repository. Re-deriving the CSV needs only §5.1.
