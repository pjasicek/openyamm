# MAW as an optional ruleset

> Formulas updated to MAW `8fbb48d1` (2026-11-05) and `8967ae88` (2026-11-12) where [UPSTREAM_SYNC_8fbb48d1.md](UPSTREAM_SYNC_8fbb48d1.md) and [UPSTREAM_SYNC_8967ae88.md](UPSTREAM_SYNC_8967ae88.md) list a change.

Status: investigation only (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). This folder describes what the MAW mod for MMMerge does, how it differs from the
standard MMMerge rules OpenYAMM runs today, how a "Standard / MAW" choice at new game would work, and which improvements
are cheap because OpenYAMM is not bound to the vanilla interface.

**To implement, start with [HANDOFF.md](HANDOFF.md)**: decisions taken on 2026-10-23, phase plan, contracts and tests.
What is still missing or wrong is listed in [GAPS.md](GAPS.md); deliberate differences in [DEVIATIONS.md](DEVIATIONS.md).
MAW in MM9 (Chedian, MAW's fourth continent): [MM9_SUPPORT.md](MM9_SUPPORT.md) (built), [MM9_BALANCE_DESIGN.md](MM9_BALANCE_DESIGN.md) (the user's decisions, the balance file and tool, what is next).

Source analysed: `/home/pjasicek/github/Maw-Mod-MMMerge` at commit `ef23ee17` (2026-10-22). The copy in
`reference/Maw-Mod-MMMerge/` is older (87 script files differ) and should not be used.

## Documents

| Document | Contents |
|---|---|
| [ITEMS.md](ITEMS.md) | Loot generation, rarities, enchants, item level, crafting items, artifacts, legendaries, inventory tools, item tooltips |
| [COMBAT.md](COMBAT.md) | Stats, damage pipeline, resistances, monsters, bosses, difficulty, bolster and progression, experience, arena, maps |
| [SKILLS_SPELLS_ALCHEMY.md](SKILLS_SPELLS_ALCHEMY.md) | Skills, Ascension, spells, buff auras, crowd control, classes, races, alchemy, respec, table diffs |
| [UI_CONTENT.md](UI_CONTENT.md) | Every hotkey, button, screen and prompt; settings; map scripts, quests, NPCs; LOD contents; multiplayer |
| [ENGINE_INTEGRATION.md](ENGINE_INTEGRATION.md) | Where a ruleset plugs into OpenYAMM: new game flow, tables, mechanics, item struct, Lua, UI, saves |

Verified specifications (second pass, precise enough to implement and test from; numbers produced by running MAW's own
Lua where possible):

| Document | Contents |
|---|---|
| [COMBAT_SPEC.md](COMBAT_SPEC.md) | Every attack path both ways, all 36 + 8 pipeline stages, delays, leech, regen, crowd control, rounding order, golden worked examples |
| [BALANCE_MODEL.md](BALANCE_MODEL.md) | The expected-player model behind monster HP and damage; level, HP, damage, AC, resistance and experience per mode |
| [MONSTER_TABLE_DIFF.md](MONSTER_TABLE_DIFF.md) | All 220 monster rows and 182 map-stats rows MAW changes, as patches onto our tables |
| [RANDOMS.md](RANDOMS.md) | Every random draw, its distribution and seeding; bad-luck protection; the randomizer; a deterministic-stream design |
| [CRAFTING.md](CRAFTING.md) | Every crafting item, cap tables, drop rates, shop sources, previews, potion-on-item crafting, bugs |
| [CRAFTING_BENCH_DESIGN.md](CRAFTING_BENCH_DESIGN.md) | Workbench with Alchemy and Crafting tabs on top of our alchemy bench: layout, behaviour, classes, phasing |
| [TRAINERS_SKILLS.md](TRAINERS_SKILLS.md) | Trainer relocation, teacher rules and prices, training halls, skill-point economy, respec, class and race table patches |
| [CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) | All 111 spells, Ascension, buff auras, crowd control, the new classes, promotions, races, every potion and recipe |
| [CLASS_SPELLBOOKS.md](CLASS_SPELLBOOKS.md) | Proposal: the Death Knight's and Assassin's own spellbook pages, pictures and names over unchanged rules; mockup and open decisions |
| [ITEMS_DATA.md](ITEMS_DATA.md) | Item, random-item and special-enchant patches in our formats; item tooltip spec; item record and save notes |
| [MAPS_CONTENT.md](MAPS_CONTENT.md) | The 12 edited maps, every map and quest script change, dropped base fixes, overlay operations needed |

Machine-readable drafts extracted from MAW are in [data/](data/): YAML in the proposed ruleset shape (loot, legendary
affixes, artifacts, special enchants, crafting items, spells, buff auras, crowd control, class perks, promotions, race
bonuses, potion effects and recipes, skill rules, mastery requirements, difficulty, map levels, monster scaling,
bosses, dimension affixes, experience curve, map overlays) and two golden CSVs (`balance_golden.csv`,
`rarity_golden.csv`) for unit tests. [harness/](harness/) keeps the scripts that produced them.

The first-pass documents were corrected against the specs; where they still differ, the specs win. This README is the
summary and the recommendation.

Related: [vanilla mode investigation](../vanilla/README.md) (same day), which needs the same "ruleset chosen at new
game" machinery for MM6/MM7/MM8 rules, and the [hardcore mode investigation](../plans/HARDCORE_MODE_INVESTIGATION.md),
which overlaps MAW's Nightmare and Beyond Madness rules.

---

## 1. What MAW is

- **A rules overhaul, not a content pack.** About 73,000 lines of MMExtension Lua in 154 files, 17 replacement TXT
  tables and five LOD archives. It adds no new maps; it edits the geometry of 12 existing maps and the scripts of
  about 35. Most of the mod is code that intercepts engine events and rewrites numbers.
- **Always on once installed.** It is a file overlay on MMMerge, the Rodril nightly patch and the multiplayer branch,
  in that order. There is no master switch and no "this is a MAW save" flag.
- **Actively developed and mid-refactor.** 4,615 commits since June 2023, the latest on the day of this analysis.
  Logic is migrating into a cleaner `Modules/MawCore/` layer (named damage-pipeline stages, pure formula functions,
  a planned clean-break save), while older global code still runs beside it.
- **The README is out of date.** Where the README and the code disagree, the detailed documents follow the code. The
  differences that matter most:

  | README says | Code does |
  |---|---|
  | Ancient and Primordial items; 14 crafting items | 8 rarities (Common, Uncommon, Rare, Epic, Ancient, Primordial, Legendary, Celestial); 20 gem tiers plus 10 special crafting items |
  | Monsters ×2 early, ×12 at L100, ×250 at L250 | HP and damage are derived from a model of the average player at that level, as hits-to-kill tables per difficulty |
  | Difficulty multiplies HP and damage by 0.6/0.8/1/1.5/2/3 | Hits-to-kill tables, widened further by the balance model (at level 300 Hell is ×1.63 HP and ×1.26 damage of MAW); Easy and Normal are accidentally identical |
  | Loot cannot be save-scummed | Only partly true: rolls follow the item id, corpse loot depends on other draws in the same frame, chest and shop base items are unseeded ([RANDOMS.md](RANDOMS.md)) |
  | Trainers moved so every continent has every skill | 21 NPCs (64 table entries on 19 maps) for racial abilities, Regeneration, Dodging, Unarmed and Identify Monster |
  | Resistance: damage/2^(res/100) for the player | That is the monster side. Player resistances are hyperbolic and scale with the attacker's level |
  | Ascension: −10/20/30/40 % mana per mastery, spell tiers | −12.5/25/37.5/50 %, no tiers; one Ascension level scales every spell |
  | Nightmare forbids saving near monsters | Saving costs food (up to 10 indoors with enemies close); Lloyd's Beacon and Town Portal are refused near enemies |
  | Click a utility skill to share it | Sharing is automatic: the best party member's skill counts |
  | Press the top-right icon at party creation for MAW classes | The icon was removed; free class and portrait selection is always on |
  | Solo gets 5× experience | Not a special rule: kill experience is split among living members, quest experience is ×5/party size |

## 2. What MAW changes, by area

Numbers here are summaries. Each heading links to the full treatment.

### 2.1 Progression, difficulty and modes ([COMBAT.md](COMBAT.md) §3–5)

- **MMMerge's bolster is switched off** on every map load and replaced.
- **Banked levels per continent.** Experience feeds a per-continent level bank.
  - *Free progression*: a continent's monsters gain the levels you banked on the other continents (minus 4).
    You can finish MM6 at 100, then MM7 starts +100.
  - *Horizontal progression*: every map's monsters are fixed at roughly 2.5× the map's vanilla level band (the band's
    spread and tier offsets stay at 1×; a few starter maps are excepted), so the party must move between
    continents to progress. Mastery thresholds become 6/12/20 instead of 4/7/10, and teleporters in the three
    starting towns link the continents.
- **Difficulty**: Easy, Normal, MAW, Hard, Hell, Nightmare. Each step changes monster HP and damage (hits-to-kill
  tables), monster density (with an experience correction), loot rarity and enchant strength, crowd-control costs,
  and adds rules:
  - from MAW up: affixed bosses on every map;
  - from Hard: attacking cancels Fly;
  - from Hell: melee monsters outdoors can gain a ranged attack;
  - Nightmare (irreversible): saving costs food, no Lloyd/Town Portal near enemies, dungeons left below 65 % killed
    revive their dead, deep overkill means death or eradication.
- **Game modes, fixed at party creation**: Normal, Doom, Road to Insanity, Beyond Madness, Austerity. Each is a
  harsher package: Doom adds on-hit conditions, hiring limits, identify-before-wear, more and stronger spawns and a
  turn-based move limit; Insanity and Madness inherit Doom's spawn rules and add harder masteries and no map refills;
  Beyond Madness resets the party to level 1, fixes per-map levels up to 500, uses seeded boss affixes and keeps a
  run-wide death counter that also counts loading during combat; Austerity removes legendaries and changes armour
  rules. The new-game gold and experience bonus applies only to Doom, Insanity and Madness.
- **Randomizer** (party creation): shuffles 101 quest items and 452 monster slots across 185 maps, seeded from the
  clock, without checking that items stay reachable.
- **Map completion**: killing a required share of a map's monsters awards experience, gold and crafting items once.
  A completed dungeon can be reset for harder monsters (+20 levels per reset).
- **Experience curve** costs 1 % more per level above 100. Kill experience scales with how tough the monster is
  relative to the party's level.

### 2.2 Monsters ([BALANCE_MODEL.md](BALANCE_MODEL.md), [MONSTER_TABLE_DIFF.md](MONSTER_TABLE_DIFF.md))

- **HP** = expected player damage per base-recovery attack × hits-to-kill (1 to 5 by difficulty). **Damage** =
  expected player effective HP ÷ hits-to-death (14 down to 4). Weak/normal/strong variants deal 0.66/1/1.5 damage;
  their HP follows the base table's HP ratio to the middle variant, clamped to 0.6–1.8. The "expected player" is
  a balance model of stats, gear, skills and buffs at each level (`Estimates.lua`). Porting monster stats needs MAW's
  item, skill and buff curves first; `data/balance_golden.csv` (run from MAW's own code, levels 1–2000, all
  difficulties, party and solo) is the reference to test against.
- **Monster levels** come from a per-map Low/Mid/High table (208 entries, re-keyed to all 207 map files in
  `data/map_levels.yml`) plus the progression rules above.
- **Speed**: fast melee monsters move at v/2 + 300 (300 becomes 450). Monster missiles home on the party while it
  stays within 0.5° of their path; running sideways breaks the lock.
- **Resistances** capped at 200 (damage ÷4 at most): no immunities. Monsters do not resist Energy, which includes
  blaster shots.
- **Bosses**: 14 affixes (Summoner, Venomous, Plagueborn, Fixator, Exploding, Thorn, Reflecting, Adamantite, Swapper,
  Regenerating, Puller, Leecher, Swift, Shadow) plus rare Broodlord and Omnipotent cascades. Bosses always drop an item
  and roll from the top quarter of the rarity table.
- 220 rows of the monster table change (experience, damage, HP, level, treasure; mostly MM6 families) and 182 rows of
  map stats (treasure level 6 everywhere; 38 maps change pools, counts or tier mix). Some MM7 maps get scripted
  ambushes and extra packs.

### 2.3 Combat and character stats ([COMBAT_SPEC.md](COMBAT_SPEC.md))

- **Stats**: from 25 up, every 5 points give +1 of the usual effect. Each stat also has its own bonus: Might +1 %
  physical damage per 10 (bows included); the higher of Intellect/Personality +1 % spell damage per 10; Endurance
  +1 % HP per 10; Accuracy raises crit damage and Luck crit chance; Speed gives attack speed, cast speed and a dodge
  chance; Luck also adds resistances. Melee and bow crits scale against the monster's level, spell and enchant crits
  against the party's total banked level.
- **Armour and resistances** reduce damage hyperbolically against the attacker's level:
  `taken = 1 / (AC / (200 + L) + 1)`, and the same shape for resistances with `100 + L`. A 10 % floor applies to
  the hit before shields, but flat class reductions and some legendaries come after it, so the final hit can be lower.
  Light uses the lower of Mind/Body, Dark the lowest element, Energy the lowest of all.
- **Crits** for melee, bows and spells (Accuracy/Luck/Intellect driven).
- **Attack speed**: speed bonuses add into one percentage that divides the delay; swiftness, armour penalties and
  Haste multiply on top. Each weapon has a base speed that slows with item level, and slow weapons hit proportionally
  harder, so DPS depends only on bonus speed. The engine's 30-tick floor is removed. Dual wielding uses both weapons.
- **Weapon enchant damage also adds to spells** (all three weapon slots; ÷2.5 for area spells), resisted as the
  spell's element. Blasters use melee damage and are never resisted.
- **Homing**: player missiles re-aim at their target every frame (a setting, on by default).
- **Leech** is measured in fractions of the monster's health bar, so it does not scale with overkill.
- **Power and Vitality**: the character screen shows estimated DPS (melee/ranged/spell) and effective HP, and item
  tooltips show the % change if you equip the item.

### 2.4 Items, loot and crafting ([ITEMS_DATA.md](ITEMS_DATA.md), [RANDOMS.md](RANDOMS.md), [CRAFTING.md](CRAFTING.md))

- **8 rarities**. One roll picks Common/Uncommon/Rare/Epic (bands widen with loot tier and difficulty); an Epic can
  upgrade to Ancient (12 %), Primordial (4 %), Legendary (3 %) or Celestial (0.2 %). Bad-luck protection makes rare
  outcomes certain after a long dry run. MAW's loot guide PDF tabulates the resulting odds; a model including the
  bad-luck protection reproduces every cell, and `data/rarity_golden.csv` holds it as a unit-test oracle. (MAW's own
  `GetRarityDistribution` ignores the protection and is slightly off.)
- **Up to 3 enchants**: two base enchants (stats, HP/SP, AC, resistances on rings, 10 % chance of a skill enchant)
  and one special. Strength grows with loot tier, by rarity band, by difficulty and by slot (two-handers ×2).
- **Item level** (a repurposed field) drives weapon damage, armour AC, special-enchant scaling, price and a **level
  requirement** to wear the item.
- **Legendary** items carry one of 25 affixes (cheat death, crit overflow, +10 Ascension, buffs reserving HP instead
  of mana, …). **Celestial** items rescale to the wearer's level forever.
- **Artifacts** drop at 0.5 % with pity, scale with total party level from a stat budget (98 budgets over a list of
  104 entries, 103 distinct ids), and gain on-hit effects, wear requirements, permanent buffs and immunities.
- **Seeding** is meant to stop save-scumming but only partly does: an item's rolls follow its item id, not the kill;
  corpse loot below Insanity depends on other random draws in the same frame; chest and shop base items are
  unseeded; refilling a map repeats crafting drops; Telepathy fixes the drop at cast time rather than previewing it.
  OpenYAMM should use named deterministic streams keyed by the drop ([RANDOMS.md](RANDOMS.md) §6).
- **Crafting** (right-click a crafting item onto equipment): gems raise the weaker base enchant up to a tier cap,
  three gems merge into the next tier (U), the Eye adds a special, the Hourglass a second base enchant, Pandora's Cube
  adds base-stat quality, the Crafting Cube adds item level, the Mirror duplicates, the Emerald upgrades the base
  type, the Pearl removes an enchant, two orbs move Legendary and Celestial status between items. Five potions also
  enchant items. Holding ALT previews the result for the Eye, Hourglass and Enchant Item only (the Hourglass preview
  is wrong for HP/SP). At monster level 100 a regular kill yields about 19 gems per 1000 kills, a Pandora's Cube every
  ~320 kills and an Eye every ~1,600; bosses ×10.
- **Shops** reroll for gold (R), stock crafting items more often for rich parties, and price items by loot power.
- **Loot filter** turns drops at or below a rarity into gold.
- **Dimension maps** (endgame): map items that send the party into a completed dungeon with random affixes (dropped
  maps unlock 2–4). Several of the 33 affixes do not do what their text says ([BALANCE_MODEL.md](BALANCE_MODEL.md)).

### 2.5 Skills ([TRAINERS_SKILLS.md](TRAINERS_SKILLS.md))

- **Skill limits** raised to 500 (1023 with bonuses).
- **Every weapon and armour skill rebalanced** per mastery: attack, speed, damage %, AC and resistance from armour
  skills, and specials (dagger crit, axe crit damage, spear damage-taken stacks, mace and staff stuns, bow multi-shot
  and fire arrows). Armour slows casting as well as attacking.
- **Regeneration and Meditation** tick every 0.1 s and are much stronger out of combat.
- **Learning is replaced by Ascension** (see spells).
- **Four new skills**: Cover (take hits for allies), Mana Shield, Enlightenment (cheaper buff auras), Retaliation.
- **Cheaper second skills**: raising a skill costs `ceil((s+1)/n)` where n counts your other weapons and schools
  already at that level. This covers weapons too, not only magic schools.
- **Utility skills are party-wide** (best member). Solo characters get utility masteries automatically.
- **Respec** at the Seer, Judge Grey and the Oracle for 1000 gold per level; old masteries return automatically.
  Alchemy is not reset.
- **Mastery requirements** by mode: 4/7/10 normally, 6/12/20 in horizontal progression or Doom, 8/16/25 in Insanity,
  10/24/40 in Madness.
- **Trainers moved**: 21 NPCs teaching the racial abilities, Regeneration, Dodging, Unarmed and Identify Monster appear
  on every continent. Teacher prices escalate with each mastery owned.
- **Class skill caps** in play come from `Class Skillz.txt`, which overrides `Class Skills.txt` (157 cells differ).
  `Race Skills.txt` is never read; only `Race Skillz.txt` applies, so base racial bonuses do not apply under MAW.

### 2.6 Spells ([CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md))

- **About 37 damage spells re-tuned** and 16 cost/delay changes; Lightning Bolt becomes Chain Lightning.
- **Ascension** is a power dial: damage per die `×(1+0.02s)·1.02^s`, flat damage `×(1+0.01s²)·1.02^s`, mana
  `×(1+0.125s)·1.04^s`, cast time `×1.015^s`; mastery is the only discount (12.5–50 %).
- **Extra heals**: Remove Curse and Cure Disease become heals; quick-cast heals target the most injured member.
- **Crowd control** has no resistance roll except Stun (30/(30 + L/4)); duration is cut by resistance. Fear, charm,
  berserk, enslave and paralysis (including mace and staff stuns) also get diminishing returns per monster up to
  immunity and are halved on bosses; slows, Dark Grasp and Shrinking Ray get neither.
- **Buffs become toggled auras** that reserve a share of the caster's mana instead of expiring. This is the largest
  systemic change and the default ("Buff Rework ON"); the OFF path is mostly dead code.

### 2.7 Classes and races ([CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §5–6)

- **Four new class lines** with three tiers each: Seraphim (holy melee healer), Death Knight (spells unlocked by
  mastery, priced off weapon damage), Shaman (every school gives a melee perk), Elementalist (learns spells by casting,
  stacking damage). The README names only three; Elementalist is the fourth.
- **The Thief line becomes an energy and combo-point Assassin.**
- **Promotions** work from any continent's quest; a random final class is picked when there are several; completing
  2 or 3 continents' promotions gives "Elder"/"Ultimate" with ×1.25/×1.5 HP and SP (MAW changes the class itself,
  so every character of that class gets it; we should apply it per character).
- **Race bonuses**: +3 (and +1 per 10) to signature skills, mastery shifts (Humans +1 on utility skills), racial
  resistances, Minotaur and Dwarf axe dual wield.
- HP/SP per level and skill caps re-tuned for many vanilla classes (the base Dragon drops to 5 HP per level, Rangers
  gain magic, the Thief line loses Learning, Shield and Armsmaster).

### 2.8 Alchemy ([CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §7)

- **A new, much smaller recipe tree**: 87 recipes (base → secondary → tertiary → white → black); every other mix
  simply fails. **No explosions, no dilution**; mixing still needs the result's Alchemy mastery.
- Timed potions last 6 hours (longer with GM Alchemy); 20 of the 43 MAW potions have **5 charges** (not cures, the
  basic heals or black potions). Some need a minimum power.
- **Black potions** give permanent stats, resistances or skill points on a "best step only" ladder.
- A potion and the matching spell aura do not stack; the stronger one applies.
- **Reagent power** comes from item level and Alchemy mastery; heals scale with power and stay relevant late.
- Solo hotkeys G and V drink the strongest heal or mana potion (15 s cooldown), with formulas that differ from
  drinking the same potion.

### 2.9 Content ([MAPS_CONTENT.md](MAPS_CONTENT.md))

- **Teleporters** (events 1777 Antagarich, 1888 Jadame, 2666 Enroth). No new geometry: New Sorpigal gets decorations
  (pedestals, markers, columns) and terrain edits; Ravenshore and Harmondale get shifted copies of existing buildings
  with changed face events and flattened terrain. The other nine edited maps change bosses, monsters, spawns and the
  d42 arena gate.
- Trainer relocation; MM6 stat shrines usable in any month; respec and Dimensional Maps topics on the Seer, Judge Grey
  and the Oracle; a Druid Circlet quest; Saving Goobers needs one Philosopher's Stone instead of ten; Dragon Hatchling
  feedback and release; Endless Arena waves in d42; scripted ambushes and bosses in about 10 maps; Doom-mode hiring
  refusal; mercenaries disabled in Beyond Madness.
- **Several MAW map scripts are stale copies** of older MMMerge files and drop base behaviour: Judge Grey's death and
  the Arbiter messenger (7out02), throne-room and Dwarf-king fixes (7d24), cross-continent completion (7d29), the
  invisibility and Necromancer-alliance paths (d19), the Hive entrance lock after the MM6 ending, the Barrow VII
  destination, Snergle's door guard, quest/timer checks in 7d32 and 7d34, and the whole 7out01 file on non-Redone
  data. Dimensional Maps also hides the Seer's "Pilgrimage" topic, so stat shrines pay out once in total. MAW
  content must be ported as additions on top of our current events, never as whole-file replacements.
- **Fixes worth taking into Standard**: Galvinus' potion quest QBits (our `Global.lua` has the same bug), stuck pillar
  doors in 7d11, the re-collectable d26 sarcophagus, the 7d12/7d37 bookshelf doors, and potion quests accepting all
  three games' reagents.

### 2.10 Multiplayer

MAW vendors a partial copy of the MMMerge multiplayer branch (about 13,600 lines). It is separable from MAW's
gameplay; for OpenYAMM it can be ignored, except that MAW's list of host-authoritative settings is a useful design
note for the multiplayer plan.

## 3. Interface: what MAW adds or changes

Full catalogue with positions and `file:line`: [UI_CONTENT.md](UI_CONTENT.md) §1. Summary:

| Area | Element | Notes |
|---|---|---|
| Party creation | **Mode** spinner (Normal/Doom/Insanity/Madness/Austerity), **Randomizer** toggle | Free class selection forced on; the class-unlock icon is gone |
| Extra settings page 1 | "Bolster monsters" toggle now means free/horizontal progression; "Bolstering power" now means difficulty | Labels are wrong because MAW reuses MMMerge's painted backgrounds |
| "MAW SETTINGS" page | Buff Rework, M&M6 projectiles, Homing, Friendly damage, Loot filter, Extra item tooltip | Only exists if the multiplayer module is installed |
| `MAWSettings.lua` file | Hotkey key codes and per-install flags (all trainers, strafe speed, auto-target heals, …) | Rebinding means editing numbers in a text file |
| Inventory | 10 multibag buttons (5 bags, 5 tabs when solo), crafting-bag "C" markers | Bags are whole extra 14×9 grids swapped in and out |
| Stats screen | Power (M/R/S) and Vitality replace "Condition"/"Quick Spell"; resistances shown as % taken | Right-click texts for every stat, level (banked levels), damage recount |
| Item tooltip | Rarity colours, real damage/AC, quality %, 3 enchants, legendary text, Power/Vitality % vs equipped, level required, attack speed; ALT previews crafting | Comparison works by temporarily swapping the real item in |
| Monster tooltip | Real HP, level, damage already reduced by your defences (ALT: raw), debuffs with timers | |
| Skill and spell tooltips | Per-mastery tables, next-level numbers, Ascension multipliers, reserved mana | |
| HUD | Map completion % (colour-coded), Madness death timer and counter, Elementalist/Assassin stack counters | Free-floating text at fixed 640×480 positions |
| Prompts | Nightmare confirmation, dungeon reset, dragon release, map-data reset | Typed "yes"/"Y" answers |

**Hotkeys** (about 25; several overload the same key per screen):

| Key | Where | Action |
|---|---|---|
| R | inventory / shop / spellbook / skills / stats | sort bag / reroll shop / remove all buffs / Elementalist rotation / reset damage recount (with Y) |
| T, C, G | inventory | sort party bags / all own bags / all party bags |
| E | inventory / map (solo knight) | alchemy-item owner / Charge |
| U | inventory | merge 3 gems into the next tier (press twice) |
| Shift+B | inventory | mark crafting bag |
| 1–5, Shift+1–5 | inventory, chests, houses | switch bag / tab |
| G, V | map (solo) | drink strongest heal / mana potion |
| K | anywhere | pull up to 30 corpses and crafting items to the party |
| L, O | map | unstuck (Z+100) / disable bow |
| P, M | skills | toggle Cover / Mana Shield |
| Tab | spellbook | next known school |
| ALT (hold) | tooltips | crafting previews, recipes, raw monster damage |

## 4. How "Standard / MAW" would play in OpenYAMM

### 4.1 The player's view

1. **New Game → Choose Starting Continent.** A two-way ruleset switch sits above the three continent cards:
   *Standard MMMerge* (default) and *MAW*. Standard looks and plays exactly as today.
2. Choosing **MAW** reveals a compact options row with a **Rules…** button opening one panel that replaces MAW's five
   scattered settings places:
   - **Difficulty**: Easy, Normal, MAW (default), Hard, Hell, Nightmare. A table beside it shows monster HP/damage
     relative to MAW, density, loot bonus and special rules. Nightmare's irreversibility is stated there; no typed
     "yes".
   - **Progression**: Free (bolster on continent change) or Horizontal (fixed map levels, 6/12/20 masteries).
   - **Challenge mode**: None, Doom, Road to Insanity, Beyond Madness, Austerity (locked after creation).
   - **Randomizer** checkbox.
   - **Preferences**: homing projectiles, friendly fire, loot filter. These are not rules and can change later.
3. **Character creation** then offers the MAW class lines (Seraphim, Death Knight, Shaman, Elementalist and the
   reworked Assassin) and MAW's race bonuses, with perk cards instead of a right-click wall of text.
4. **In game**, a read-only "Current game" page in Settings shows the ruleset and locked options. Difficulty can
   change within MAW's rules (never out of Nightmare or a challenge mode), from that same page.
5. **Load and Save screens**: buttons above the list (All, Standard, MAW) filter the saves by ruleset; they appear
   once a second ruleset is installed or saved. A selected MAW save lists `MAW · Hell difficulty · Horizontal
   progression` under its name. Loading a save from the other ruleset reloads the rule tables first (a short extra
   pause).
6. Presentation is shared: 3D creatures, HD art, weather, Obsidian UI and our QoL features work in both rulesets.

Standard MMMerge's bolster toggle is a global settings.ini value today. For consistency it should also become a
per-save option of the Standard ruleset (with MMMerge's missing 0–200 % strength), shown on the same panel.

### 4.2 Engine shape

Full detail: [ENGINE_INTEGRATION.md](ENGINE_INTEGRATION.md) §8. OpenYAMM has no ruleset, mod or difficulty concept
today, and nothing about these choices is stored in saves.

1. **One ruleset identity, shared with vanilla mode.** Ids `mmerge` (default), `maw`, later `mm6`/`mm7`/`mm8`. A
   `RulesetOptions` record (difficulty, progression, challenge mode, randomizer, flags) is chosen once at new game,
   stored at the start of the save (the next `SaveVersion`; older saves default to `mmerge`) and shown on the Load screen.
2. **Table overlay.** `assets_dev/engine/rulesets/maw/` holds MAW's versions of existing tables (class skills, HP/SP,
   starting skills and stats, race skills, spells, items, special enchants, random items, monsters, map stats,
   potion recipes and notes, house rules, class texts). It mounts in front of `engine/data_tables`, and
   `GameDataLoader` reloads and rebinds when the ruleset changes (at new game and at load). `switchActiveWorld`
   already re-mounts at runtime, so this has a precedent.
3. **A mechanics strategy owned by the session.** `GameMechanics` is a set of static functions with good choke
   points, so a `RulesetMechanics` interface fits: stat effects, max HP/SP, attack profile, hit and dodge, crit,
   recovery, incoming damage both ways, monster stat resolution and difficulty, item generation, description and
   value, level requirement, potion effects, skill costs and thresholds, experience. The Standard implementation
   wraps today's code unchanged. Avoid the scattered `usesMm9ActorRules`-style ifs.
   - Before this, de-duplicate the experience formula (two copies) and the five kill-reward call sites.
   - Incoming damage needs the attacker's level, which today's signature lacks.
4. **A damage pipeline of named stages**, copied as a concept from `MawCore/Pipeline.lua`. Each stage records its
   input and output, which gives the damage breakdown and combat log for free.
5. **A MAW monster stat resolver**, computed per spawn from data plus the balance model. MAW rewrites the global
   monster table on every map load; we would not. It replaces, rather than configures, `GameplayBolsterRuntime`.
6. **Item data model**: two base enchants, special enchant, stored rarity, legendary affix, item power, drop level,
   quality %, craft seed, potion charges. These extend `InventoryItem` and `EquippedItemRuntimeState` and their save
   code; there is no spare room today. Store rarity explicitly; MAW derives it and that breaks when an enchant is
   removed.
7. **Deterministic loot RNG streams** keyed by (save seed, map, actor or chest, counter): MAW's anti-save-scum, and
   reproducible headless tests.
8. **Lua only for content rules** (Nightmare respawn, map completion rewards, ambushes, teleporters, respec and
   dimension-map topics) through existing hooks plus perhaps `ItemUse` and `ShopOpen`. Bosses' affixes fit the actor
   behaviour system. Per-hit maths stays in C++.
9. **MAW map content as per-map overlays** on our generated events (never MAW's stale whole-file scripts). New
   Sorpigal's teleporter is decorations plus terrain; Ravenshore and Harmondale need copies of existing buildings, so
   the overlay system must be able to place a copy of a building.

### 4.3 Engine gaps found by the verification pass

These are concrete OpenYAMM obstacles, independent of how much of MAW is ported:

| Gap | Where | Consequence for a ruleset |
|---|---|---|
| A hard-coded spell rule table overrides `spells.txt` for about 48 spells and already disagrees with it on about 20 | `game/party/PartySpellSystem.cpp` (`BackendSpellRule`) | A MAW `spells.txt` would be silently ignored; move every number into the table first |
| Potion ids hard-coded in mixing | `game/items/InventoryItemMixingRuntime.cpp:19-26` (233, 246–250, 263) | Under MAW its Regeneration potion would recharge wands; ids must come from ruleset data |
| Potion effects are a C++ switch by item id | `game/items/InventoryItemUseRuntime.cpp` | MAW potions need `potion_effects.yml`; best done for Standard too |
| Footer comment rows occupy special-enchant ids 74–77 | special-enchant loader | MAW's new specials 74–80 must be inserted after row 73; renaming 39/40 would delete our Ogre/Dragon Slaying effects |
| Item 290 becomes a dimension map in MAW | `potion_settings.txt` row 70 | Clash to resolve in the patch |
| Monster table parsing | `GameDataLoader` | MAW's rows use quoted numbers with thousands commas, letter codes in the attack-preference column and two typos; the loader needs fixes before patching |
| `house_data.txt` `Map` column is 2 too high for MM7 maps after Bracada Desert | data | Our own bug; matters for trainer relocation and anything looking up a house's map |
| Ruleset-only event overlays and load order | event loader | `<map>_maw.lua` would sort before `_mmmerge.lua`; needs an explicit order (or `_zz_maw`) |
| Scene overlay operations | map loading | Remove a decoration, override terrain height and tiles, place a copy of an existing building, override indoor spawns and actors |
| Spawn by monster id, extra boss names, a hook before `MoveToMap` | Lua API | Needed for MAW ambushes and the dungeon-reset prompt (the map-transition hook only covers walking off the edge) |
| Item record has no spare fields | `InventoryItem`, `EquippedItemRuntimeState`, save code | Second base enchant, rarity, affix, item power, drop level, quality, craft seed, charges must be added |

### 4.4 What is a table swap and what is code

| Area | Mostly data | Mostly new code |
|---|---|---|
| Classes, races, skill caps, HP/SP, starting kits | yes | promotions graph, Elder/Ultimate scaling per character |
| Spell costs, delays, damage dice | yes | Ascension scaling, buff auras, crowd-control diminishing returns, scripted class spells |
| Potion recipes and notes | yes | potion effects (ours are a C++ switch), charges, per-drinker buffs vs auras |
| Item names, special enchant pools, random items | yes | rarity roller, 2+1 enchants, item level, level requirement, value, Celestial, legendaries |
| Monster table, map stats | yes | stat resolver, balance model, density, bosses, homing, respawn, completion |
| Stats and combat | constants as YAML | stat effects, mitigation, crit, recovery, damage pipeline |
| Skills | per-mastery rules as YAML | Ascension replacing Learning, shared-cost discount, continuous regen, Cover/Mana Shield/Retaliation/Enlightenment, respec |

MAW is mostly code, so the table overlay covers a minority of it. Expect most of the work to be new C++ rules behind
the strategy interface.

### 4.5 Data tables: patch, add, leave alone

MAW's table files cannot be dropped into `assets_dev/engine/data_tables/`. Ours started as MMerge's tables but have
diverged in both content and format:

- `items.txt` has four extra OpenYAMM columns (`package_id`, `canonical_id`, `source_item_id`, `content_flags`).
- `class_multipliers.txt` and `class_starting_skills.txt` use a different layout from MMerge's `Class HP SP.txt` and
  `Class Starting Skills.txt`. `race_skills.yml` is YAML, not MMerge's TXT.
- `house_rules.txt` and `object_list.txt` carry our own edits.

MAW's files are full copies of MMerge's tables with MAW's edits mixed in. Replacing ours with them would undo our
fixes, and later fixes to the base would never reach MAW games. That is the same failure as MAW's stale map scripts.
So the MAW ruleset should hold **only MAW's differences, in our formats**, in four groups.

**1. Patches to existing tables** (only the changed rows, cells or columns, keyed by id or name):

| Our table | From MAW | MAW's change |
|---|---|---|
| `items.txt` | `ITEMS.txt` (zMaw.T.lod) | 202 rows: leather/chain dice, belts gain AC, potions 224–263 renamed and repurposed, item 290 becomes "Map", crafting items 1051–1067 filled into free reagent placeholders (1041–1070 used in code), some artifact dice, DeathBlade removed. Patch by cell: whole rows would undo our fixes on 1307, 2030 and 2045 |
| `random_items.txt` | `rnditems.txt` | 93 rows: removes potions 264–289 and recipe scrolls 700–731 and 751–769 from treasure, moves black potions to higher treasure levels; two cells conflict with our spellbook changes (418, 1220) |
| `special_item_enchants.txt` | `SPCITEMS.TXT` | two specials repurposed (Ascension, Lichs'), seven new hybrids 74–80, slot chances and grade changes |
| `monster_data.txt` | `MONSTERS.txt` | 220 rows: experience, damage, HP, level, treasure (mostly MM6 families); no overlap with our edits |
| `map_stats.txt` | `mapstats.txt` | 182 rows: treasure level 6 everywhere, 38 maps change pools, counts or tier mix; the three Breach rows have no OpenYAMM map |
| `class_skills.txt` | `Class Skillz.txt` (overrides `Class Skills.txt` in play; 157 cells differ) | caps changed for about 40 classes, columns for the 12 new classes, Supreme Armsmaster, rows for the 4 new skills |
| `class_multipliers.txt`, `class_extra.txt`, `class_starting_skills.txt`, `class_starting_stats.txt` | `Class HP SP/Extra/Starting Skills/Starting Stats.txt` | rebalanced rows plus 12 new class rows |
| `race_skills.yml` | `Race Skillz.txt` only (`Race Skills.txt` is never read by MAW) | mastery shifts; base racial bonuses such as Human Learning +1 do not apply |
| `character_selection.yml`, `character_data.txt` | menu script, `Character portraits.txt` | free class selection, new classes at start, portrait race fixes, new portrait 77 |
| `english/class.txt` | `class.txt` | 12 new class names and descriptions |
| `spells.txt` | `Spells2.txt` plus `spellPowers` in Lua | costs, delays, damage dice |
| `house_rules.txt` | `House rules.txt` | two spellbook-shop tiers +1 |

**2. Whole-table replacements**, where MAW redesigned the table rather than editing it:

- `english/potion.txt` (the mixing matrix: 87 recipes; every other cell fails, no explosions);
- `english/potnotes.txt`.

**3. New tables** that only the MAW ruleset has. Today these numbers live in MAW's Lua, not in any table:

`difficulty.yml`, `progression.yml`, `map_levels.yml` (208 entries over 207 map files), `monster_scaling.yml`,
`bosses.yml`, `loot.yml` (rarities, odds, bad-luck protection, enchant strength, slot multipliers, value),
`legendary_affixes.yml`, `artifacts.yml` (98 budgets over 103 artifact ids, on-hit effects, wear requirements),
`crafting_items.yml`, `formulas.yml` (stats, mitigation, crit, hit, regeneration), `skill_rules.yml`,
`mastery_requirements.yml`, `spell_scaling.yml` (Ascension, heals, crowd control), `buff_auras.yml`,
`potion_effects.yml`, `class_perks.yml`, `race_bonuses.yml`, `exp_curve.yml`, `dimension_affixes.yml`.

Drafts of almost all of these, extracted from MAW, are already in [data/](data/). `formulas.yml`, `progression.yml`
and `spell_scaling.yml` are not separate drafts: their numbers are in `COMBAT_SPEC.md`, `BALANCE_MODEL.md`,
`difficulty.yml` and `spells.yml`.

Some of these schemas should also get a Standard version reproducing today's hard-coded behaviour, so that both
rulesets read data rather than branching in code. Good candidates: `potion_effects.yml` (today a C++ switch),
`skill_rules.yml`, `formulas.yml`, `exp_curve.yml`.

**4. Left alone.** Most of our tables are untouched by MAW and shared by both rulesets: NPCs, topics, houses, house
data, transport, quests, autonotes, events, sounds, decorations, terrain, Arcomage, chests and roster.

**Not carried over:**

- `bolster_*.txt`: MAW switches MMMerge's bolster off, so these are not read under MAW.
- `object_list.txt` objects 700–743 and the `SFT.txt` scales: they serve the classic MM6 projectile sprites. OpenYAMM
  draws no classic projectile sprites.
- `place_mon.txt` padding to 1000 rows: an engine workaround for naming bosses at runtime.
- `potion_settings.txt` rows 71–101: a workaround so crafting items can be used like potions. `crafting_items.yml`
  replaces them.
- `Complex item pictures.txt`: MAW's copy only carries newer base MMMerge paperdoll fixes, which belong in the
  Standard table rather than the ruleset.

**Mechanism.**

- Keep the ruleset in `assets_dev/engine/rulesets/maw/` with a `ruleset.yml` manifest.
- Groups 1 and 2 use the table contribution machinery worlds already have. `Append` exists. `Override` is parsed but
  unimplemented; implementing it would cover keyed row and cell overrides, and whole-table replacement.
- New ids (classes, special enchants 74–80, crafting items 1041–1070) sit in free slots, so they can be declared id
  ranges, as MM9's are. Item ids match ours 1:1. Special enchants 74–77 collide with footer comment rows in our
  loader (§4.3).
- Generate the patch files with a conversion tool from a pinned MAW commit plus MMerge base, rather than by hand.
  The MM6 table exporter is the precedent. When MAW updates, re-run the tool and review the diff.

### 4.6 Suggested phases

| Phase | Work | Size |
|---|---|---|
| 0 | Decide the questions in §7; pin a MAW commit to port | — |
| 1 | Ruleset identity, new-game switch and Rules panel, save field, Load badges, table overlay and reload (shared with vanilla mode) | M |
| 2 | Mechanics strategy seam with the Standard implementation unchanged; damage pipeline with breakdown; de-duplicated experience and kill rewards; the engine gaps in §4.3 (spell numbers into `spells.txt`, potion effects as data, loader fixes, overlay operations) | L |
| 3 | MAW core combat: stat effects, mitigation, crit, recovery, monster resolver plus balance model, difficulty table, progression banks, density, bosses | XL |
| 4 | MAW items: data model, rarity roller, enchants, item level, deterministic loot, tooltips, value, artifacts, legendaries, shop reroll, loot filter | L |
| 5 | MAW skills and spells: skill rules, Ascension, buff auras, crowd control, continuous regen, discounts, respec, four new skills | XL |
| 6 | New classes (Seraphim, Death Knight, Shaman, Elementalist) and the Assassin rework | L |
| 7 | Alchemy and crafting: MAW tables in the bench, potion effects as data, charges, crafting panel | M |
| 8 | Content: teleporters, trainers, quests, ambushes, Nightmare rules, dungeon reset, map completion, Endless Arena, dimension maps | L |
| 9 | Challenge modes (Doom, Insanity, Madness, Austerity) and the Randomizer | M |

Phases 3 to 5 depend on each other through the balance model: monster HP and damage are defined against the
expected player, so items, skills and buffs must be in place, or a precomputed table used, before monster numbers
mean anything. A playable MAW needs phases 1–7; phases 8 and 9 can follow.

Every phase has a test oracle: `data/balance_golden.csv` (monster and expected-player numbers), `data/rarity_golden.csv`
(loot odds), the worked examples in `COMBAT_SPEC.md` §11, and the computed tables in `CRAFTING.md`, `ITEMS_DATA.md`
and `CLASSES_SPELLS_SPEC.md`. All were produced by running MAW's own Lua.

## 5. Cheap, high-value improvements

Because OpenYAMM is not limited to the vanilla interface, many of MAW's workarounds become ordinary UI. Several of
these help the Standard ruleset too and could ship first.

### 5.1 Useful in both rulesets

| Improvement | Replaces in MAW | Cost |
|---|---|---|
| **Damage breakdown and combat log** from the named-stage pipeline (roll, speed, Might, crit, enchants, resistance, boss affix, leech; incoming AC %, resistance %, floor) | Status-line text assembled across ticks | S once the pipeline exists |
| **Side-by-side item comparison** (all stat deltas, both rings or both hands, best swap) computed on a copied character | Power/Vitality % by swapping the real item in | S–M |
| **Rarity colours on inventory icons and loot labels or beams on 3D ground items**, coloured by rarity | Name colour only | S |
| **Sort and routing buttons** on inventory and stash (by type, rarity, level, value; "send potions/reagents/crafting to X") | Hidden R/T/E/C/G keys, alchemy owner, crafting bag | S (sorting already exists via `CharacterInventorySortButton`) |
| **Potion quick-slots** on the HUD with cooldown rings, "strongest of type", working in a party | Solo-only hidden G/V with their own formulas | S–M |
| **Monster inspect panel**: real level and HP, each resistance as "% taken", damage vs selected character with a raw toggle, hits to kill, boss affix text, crowd-control state | Hidden ALT, raw numbers | S–M |
| **Button dialogs** for every confirmation | Typed "yes"/"Y" answers | S |
| **All new actions in the keybinding screen**, overloads resolved per screen | Key codes in `MAWSettings.lua` | S |
| **Skill tooltips with next-level and next-mastery numbers**, mastery requirement and teacher price | Partial | S |
| **Deterministic RNG streams** | Per-feature seeding | M, also helps scenario tests and multiplayer |

### 5.2 MAW-specific

| Improvement | Replaces in MAW | Cost |
|---|---|---|
| **One Rules panel at new game** with an explanation table and correct labels; locked options read-only in game | Five scattered places, mislabelled toggles, a Lua settings file | S–M |
| **Alchemy bench, MAW edition**: swap the tables; treat all recipes as known; show the recipe tree with each potion's effect at the power you would brew, its power requirement and charges; the existing chain planner already brews missing intermediates and never meets an explosion because MAW has none | ALT recipe lists, tooltip-only effects | S (tables, flag) + M (effect preview needs potion effects as data) |
| **A Crafting tab on the same bench** ([design](CRAFTING_BENCH_DESIGN.md)): item slot, reagent picker with counts, a preview computed by the same function as Apply, "Apply ×N" for gems, "Combine 3 → 1" / "Combine all"; dropping a crafting item on equipment opens the bench prefilled instead of consuming it (also covers Android, which has no right-click) | Right-click a crafting item onto equipment; previews only via ALT; the craft is performed by building a tooltip; U pressed twice | M; reuses the bench layout and style |
| **Party stash with tabs** at inns, or anywhere when solo | Five swapped 14×9 grids per character (25 when solo), with a save-corruption guard | M |
| **Shop "Reroll stock (N gold)" button** with the real price | Hidden R with a wrong "20000 gold" message | S |
| **Rule-based loot filter** (rarity, slot, level, legendary) with a pickup log | Rarity threshold that deletes items at generation | S–M |
| **Power/Vitality panel** with a breakdown and a chosen reference level | Two rewritten labels, reference level silently the sum of all banked levels | S |
| **Progression panel**: banked levels per continent, bolster per continent, predicted monster levels here, effect of switching Free/Horizontal | Right-click on Level | S |
| **Map completion HUD**: progress bar, 65 % respawn-safe mark, reward preview, reset count | Coloured percentage at a fixed position | S |
| **Save-cost hint** on the save button in Nightmare ("costs 10 food here") | Status line after clicking | S |
| **Aura panel** for the buff rework: active auras, holder, reserved mana segment on the portrait, one-click toggles, which potions are overridden | Spellbook R to clear all | M |
| **Ascension and skill-cost previews**: damage, mana and cast time vs Ascension for a spell; discounted cost on the "+" button; respec preview | Tooltip numbers, surprise refunds | S each |
| **Class perk cards** and the class/skill matrix inside character creation | Right-click text, external HTML guide | S–M |
| **Real projectile homing** with a turn rate and lock cone in the projectile update | Per-frame velocity overwrites from Lua (frame-rate dependent, pulls cosmetic missiles) | S–M |
| **Drop transparency page**: current loot tier, difficulty multipliers, bad-luck progress | A separate PDF guide | S |

### 5.3 Do not port (engine workarounds)

The 16-bit monster HP ledger and 32,500 damage clamp, levels capped at 255 with side tables, data hidden in
resistance values, boss affixes parsed from monster names, PlaceMon placeholder rows, rewriting the global monster
and map tables on every load, label rewriting on timers, polling for settings changes, the UI-loop register guard,
the Town Portal click fix, assembly strafe and backpedal patches, crash diagnostics, console-use logging and the
obfuscated death-counter file. A native engine needs none of them. Full list: [COMBAT.md](COMBAT.md) §8.3 and
[UI_CONTENT.md](UI_CONTENT.md) §7.4.

## 6. MAW bugs to fix rather than copy

Each fix should be recorded as a documented deviation.

- Easy and Normal map to the same difficulty index and play identically.
- GM Shield's 15 % reduction applies twice to magic damage.
- Speed and spell-haste tooltips disagree with the code (/10 vs /20, +20 vs ×1.1).
- Ice Blast appears twice in the monster spell multipliers; the second value wins.
- The MM7 experience doubling reads a variable only set while training.
- Every `not vars.MAWSETTINGS.buffRework=="ON"` check is always false, so the "Buff Rework OFF" path is mostly dead.
  Port only the rework behaviour.
- The list protecting quest artifacts in chests is commented out, so they are replaced by random loot.
- Legendary affix 28 says "doubled" but applies ×1.5; the value formula mishandles the second enchant's HP/SP.
- Eye and Hourglass notes state requirements the code does not check; the Mirror copies artifacts despite the README.
- The Hourglass preview and apply paths compute HP/SP strength differently.
- Tooltip building mutates items (Celestial recalculation, the comparison swap).
- G/V potion hotkeys use different formulas from drinking; V shows one amount and restores another.
- Dwarf gets Shield instead of the documented Axe; respec checks the wrong character for the Assassin refund.
- Survival mode is unreachable and would crash. Do not port it.
- Monster Dispel is unchanged in the data, but auras are re-applied every 0.5 s, so it has no lasting effect. Make
  the intended rule explicit (for example, dispel suppresses auras for N seconds).
- Stale map scripts drop MMMerge fixes (§2.9).

Found by the verification pass (each spec lists its own, about 80 in total):

- **Combat** ([COMBAT_SPEC.md](COMBAT_SPEC.md) §13): Empower Magic uses Haste's numbers; vampiric artifacts give no
  leech; the crowd-control difficulty multiplier is never used; resistance randomisation can never run;
  monster-vs-monster damage is resisted twice; spear stacks boost everyone's physical hits.
- **Dimension-map affixes**: "+HP" leaves HP unchanged, "Energy damage" converts every hit, the reflect affixes are
  inverted ((100 − p) %), regeneration is broken, control resistance only affects Stun.
- **Balance model** ([BALANCE_MODEL.md](BALANCE_MODEL.md) §10.2): Cover stops counting at Grandmaster; spell power
  uses Haste where Empower Magic was meant; a shared global corrupts chest gold; bounty level boosts are never
  cleared; from level 863 training becomes free (the requirement is clamped at 2^31).
- **Items** ([ITEMS_DATA.md](ITEMS_DATA.md)): weapon damage stops growing at item power 100 while armour keeps
  growing; clubs never slow with item level; special 80 adds nothing to price; a second-enchant resistance shows +10
  that is not applied; Carnage is ×0.25 though its text says half; item skill bonuses are capped at 2× base skill, so
  untrained skills get nothing.
- **Crafting** ([CRAFTING.md](CRAFTING.md)): Pandora's Cube is accepted and wasted on jewellery; the Oracle's Orb
  silently overwrites an existing affix; two-handed axe gem caps halve while a Minotaur is selected; dropped
  dimension maps never roll exactly 2 affixes in one path; the Crafting Cube and map operations run inside tooltip
  building and probably work on shop and chest items.
- **Spells and potions** ([CLASSES_SPELLS_SPEC.md](CLASSES_SPELLS_SPEC.md) §8): Power, Wisdom and Resilience Boost
  potions do nothing; Magic Protection potion power has no effect; Vampire Charm and Dragon Fear read the wrong
  school; Shaman spell damage never scales with Ascension; quick-casting Resurrection is broken.
- **Skills and teachers** ([TRAINERS_SKILLS.md](TRAINERS_SKILLS.md)): remembered masteries count one rank too high in
  teacher prices; gold is checked against the vanilla price first; seven skill tooltips contradict the code.
- **Content** ([MAPS_CONTENT.md](MAPS_CONTENT.md)): the znwc potion seller's 50-sale cap never stops sales; copied
  Ravenshore obelisks pay the real obelisk's reward; Harmondale shrine copies keep the Land-of-the-Giants altar.
- **Randomizer**: no reachability check; items can be duplicated or lost.

## 7. Decisions

Decided on 2026-10-23 (see [HANDOFF.md](HANDOFF.md) §1): items 1, 2, 3 (fix and document by default), 4 (target
phases 1–7), 5 (changeable like MAW, with locks), 6 (continent screen plus Rules panel) and 7 (one shared ruleset
identity). Item 8 is handled in phase 1. Items 9 and 10 are asked when their phase is reached.

1. **Permission: settled.** The MAW repository has no licence file, but the user confirmed on 2026-10-22 that the
   MAW author agrees to this integration. Keep following the project's practice of reimplementing behaviour as new
   code rather than copying Lua. Crediting the MAW team (README credits list) in the ruleset description is a
   courtesy worth keeping.
2. **Which MAW.** MAW changes daily and is mid-refactor. Proposal: port the behaviour of a pinned commit
   (`ef23ee17` or a tagged release), follow the code rather than the README, and track later changes as diffs.
3. **Fidelity versus fixes.** Proposal: fix the bugs in §6 and record each deviation; keep MAW's balance numbers.
4. **Scope of the first playable MAW.** Proposal: difficulty, both progression modes, items, crafting, skills,
   spells, alchemy and the four new classes (phases 1–7). Challenge modes, Randomizer, dimension maps and Endless
   Arena later.
5. **Mid-game difficulty changes.** MAW allows them except out of Nightmare and challenge modes. Keep that, or fix
   difficulty at new game? Changing it requires resetting saved per-actor bolster caches.
6. **Where the rules choice lives.** Proposal: a ruleset switch on the continent screen plus a Rules panel, rather than
   a separate screen. It needs an update to the approved Obsidian menu design for that screen.
7. **Overlap with vanilla mode and hardcore mode.** Proposal: one ruleset identity and save field for all three
   investigations. MAW's Beyond Madness death counter maps onto the hardcore ledger design rather than MAW's
   obfuscated file.
8. **AGENTS.md rules.** "Worlds must not own gameplay tables" and "no campaign layer for now" need the same explicit
   exception the vanilla investigation asks for: a ruleset package overriding named engine tables.
9. **Small crafting calls** ([CRAFTING.md](CRAFTING.md)): may the Mirror copy artifacts (code yes, MAW README no)?
   Doom's top enchant strength 138 (exact) or 139 (MAW's floating-point result)? Make the Emerald of Power sellable?
   Let more alchemists stock crafting items? Fix the dimension-map affix-count bug?
10. **Trainer relocation as data.** Proposal: a static "this NPC also appears in these houses" overlay behind a ruleset
   option, instead of MAW's permanent house moves written into saves.
