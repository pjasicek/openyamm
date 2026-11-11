# MM9 spells mapped to MM6–MM8 spells

Status: **implemented** (2026-11-04), with the user's answers to the open questions. What was built, the answers and
the final mapping are in [section 6](#6-implementation-2026-11-04); sections 1-5 are the review proposal as written,
kept for the evidence, and section 6 supersedes them where they differ. The spell choice and the `concat` rows were
redone the same day from the native RE ([6.6](#66-spell-choice-and-concat-as-mm9-plays-them-2026-11-04)): MM9's own
chances, `concat` spells as ordinary spells, no on-hit riders and no `special_attack_chance`; then
([6.7](#67-no-bonus-specials-blows-in-reach-and-placement-scripts-2026-11-04)) no `Bonus` specials, blows in reach and the
placement's script deciding whether a monster shoots. Section 1 is corrected to the RE; the tables of sections 2-3 and
6.1-6.3 keep the earlier spell choice where 6.6 and 6.7 say otherwise.

**Decision (user, 2026-11-04).** The first version of the MM9 content does not use MM9's own spells. Every spell
an MM9 monster, script or trap casts becomes the MM6–MM8 spell from the merged MMerge table
(`assets_dev/engine/data_tables/spells.txt`) that fits best, cast through the engine's existing monster spell and
event spell paths.

This document has four parts: what MM9 casts and where ([inventory](#1-inventory)), what OpenYAMM can cast today
and what the importer does now ([current state](#2-current-state)), the [proposed mapping](#3-proposed-mapping),
and the [engine gaps](#4-engine-gaps) and [open questions](#5-open-questions-for-the-user).

Sources:

- `mm9/extracted/DATA/DATA/MONSTERS.txt` (spell columns 40–43, `Projectile1` col 32, the second `Projectile2`
  col 66), `SPELL.txt`, `PROJECTILE.txt`.
- `mm9/extracted/SCRIPTS/SCRIPTS/*.scr|*.inc` (715 scripts, 87 includes) and the manual `mm9/mm9_tools/script.txt`.
- The placed DAT objects in `assets_dev/worlds/mm9/maps/*.raw_objects.yml` (45 maps): monster classes, `Shooter`,
  `Spawner`, `DamageBrush`, `EarthQuake`, `PoisonGas` and others.
- Which columns MM9's AI reads: [MM9_AI_DATA_AND_SCRIPTS.md](monster_ai/MM9_AI_DATA_AND_SCRIPTS.md) section 1, and
  the `Att%`/`RangeAttack` RE in [MM9_MONSTER_AI_PLAN.md](MM9_MONSTER_AI_PLAN.md).
- The importer: `tools/mm9_import_discovery/generate_mm9_monster_tables.py` (`SPELL_NAMES`, `spell_columns`,
  `condition_for_concat_spell`) and its output `assets_dev/worlds/mm9/data_tables/monster_conversion_audit.tsv`.
- The engine: `game/gameplay/MonsterSpellSupport.cpp`, `GameplayActorAiSystem.cpp`, `GameplayProjectileService.cpp`,
  `GameplayCombatController.cpp`, `game/indoor/IndoorWorldRuntime.cpp`, `game/outdoor/OutdoorWorldRuntime.cpp`.

Placed counts below are DAT objects whose class name matches the monster name (case, spaces and punctuation
ignored), across all 45 shipped maps. Spawned monsters (spawners, arena and summoner scripts) are not counted,
except where noted.

## 1. Inventory

### 1.1 How MM9 chooses a spell

> **RE result (2026-11-04, [native RE §7.2.2](monster_ai/MM9_AI_NATIVE_RE.md#722-attack-kind-spell-choice-rangeattack-and-concat)):** `object.lto` settles both guesses below.
>
> - The chance of a spell instead of an attack is `100 − Att%` when the row has attack-2 damage, and 100 % when it does not.
> - `SpellUse%1` only splits that share between `Spl1` and `Spl2` (d100 ≤ `SpellUse%1` → `Spl1`). A lone spell is always the one chosen, whatever `SpellUse%1` holds.
> - Two non-offensive spells are never cast.
> - `RangeAttack` either casts (the spell is re-chosen at the release) or fires `Projectile1`.
> - Blows are always physical.

- A spell cell is `id,mastery,skill1,skill2` (for example `12,E,6,1 (Elemental Bolt)`). `skill1` is the skill
  in the spell's first element and drives damage; `skill2` drives duration and radius.
- The MM9 AI loader (`object.lto`) reads `SpellUse%1`, `Spl1` and `Spl2`, but **not** `SpellUse%2`.
  `SpellUse%1` is a percentage or the word `concat`, which parses as 0. With two spells, `Spl2` takes the casts
  `SpellUse%1` leaves; a lone spell takes them all.
- `concat` is not implemented: no spell rides on a hit, and `ConcatAttk` and `Bonus` are never read (1.4).
- Scripts never choose a spell. They call `Attack` or `RangeAttack`, and the engine picks the projectile or the
  spell from the row. `Att%` (col 33) is the chance a monster in reach strikes rather than shoots or casts, and its
  complement the chance a `RangeAttack` casts when the row has attack 2. A blow is always physical.
- `Projectile1 = Spell` means that the ranged attack is the spell. The coloured "thingy" projectiles (BlueThingy,
  RedThingy, GreenThingy, PurpleThingy, BlueLine, Redline, Lightning, LightningBolt, IceBlast, FireBolt,
  DragonFireBolt, RedYellowThingy, Goo1–3, RingOfFire) are ranged **attacks**. They carry the row's attack dice,
  not a spell, so they stay monster missiles (see [1.6](#16-projectile-attacks-that-look-like-spells)).

### 1.2 MM9 spells that are used

`SPELL.txt` has 48 spells (ids 0–48; id 3 is absent). Twenty appear in monster rows; 17 of those are on imported
rows (Elemental Blast, Magic Mine and Poison Cloud are only on unimported rows). In MM9's formulas, `s` is
`skill1`.

| MM9 id | Spell | School (resistance) | Effect at the masteries used | Role |
|---|---|---|---|---|
| 1 | Bless | Light/Spirit (none) | to-hit +n1 + 1 per point (E: 5 + s) | buff |
| 2 | Chain Lightning | Elemental/Light (Elem) | M/G: s × 1–8 to the target, the same to everything within 100/200 | damage bolt + chain |
| 4 | Column-of-Fire | Elemental/Light (Elem) | M/G: 30 + s × 1–6; G hits a 100-inch area | heavy damage |
| 5 | Curse | Dark/Light (Dark) | to-hit penalty 20 + 2–6 per point; E+ halves attack rate; M+ stops casting | debuff |
| 6 | Dark Grasp | Dark/Spirit (Dark) | M: movement −50 %, AC −25 %, melee damage −50 % (G: 75/50/50) | debuff |
| 7 | Death's Touch | Dark/Light/Elemental (Dark) | G: 7 + s × 1–7 drained, 30 % heals the caster | drain |
| 8 | Disease | Dark/Elemental (Dark) | E/M/G: 2/4/7 HP per minute for 5/7/10 minutes per point | damage over time |
| 11 | Elemental Blast | Elemental/Light (Elem) | E/M/G: s × 1–6/8/10 in a growing ring (180/240/420) | area |
| 12 | Elemental Bolt | Elemental/Spirit (Elem) | N/E/M/G: s × 1–4/6/8/10 | damage bolt |
| 19 | Fear | Dark/Spirit (Dark) | no numbers in the table: the Fear condition | debuff |
| 23 | Heal | Spirit/Light (none) | 5 + 2/3/4/10 per point | heal |
| 25 | Magic Mine | Elemental/Dark (Elem) | a mine that explodes near a creature | trap |
| 27 | Natural Armor | Spirit/Elemental (none) | M: AC +2 per 2 points; G: +2 per point | buff |
| 29 | Paralyze | Dark/Elemental (Dark) | the Paralyze condition, 1 minute per point | debuff |
| 31 | Poison | Elemental/Dark (Elem) | s × 1–4/6/8/10, then 1–2 per point of skill2 each minute for 10 minutes | bolt + damage over time |
| 32 | Poison Cloud | Elemental/Dark (Elem) | M/G: 25 + s × 1–10 | damage |
| 39 | Souldrinker | Dark/Spirit/Elemental (Dark) | G: 25 + s × 1–8 to everything on screen; heals the caster | party-wide drain |
| 40 | Sparks | Elemental/Light (Elem) | 5/7/9/12 sparks, each 2 + 1 per point | volley |
| 41 | Spell Reaver | Light/Spirit (Light) | dispels magic within 10/15/20 inches per point | dispel |
| 47 | Wound | Dark/Spirit (Dark) | E/M/G: 10 + s × 2–6/8/10 | damage |

The other 28 MM9 spells are never cast by a monster, script or trap and need no mapping: Arms of Earth, Divine
Intervention, Elemental Aura, Elemental Protection, Enchant Item, Enrage, Eye of Leggib, Eye of the Storm, Faith,
Feather Fall, Fleet Foot, Haste, Lloyd's Beacon, Meteor Shower, Pain Reflection, Phantom Fighter, Power Draw,
Purify, Regeneration, Resist Death, Resurrection, Shared Life, Torchlight, Town Portal, Transfusion, Turn Undead,
Wizard Eye and Wrath of Bugs. Party spells, spellbooks and scrolls already use the OpenYAMM catalogue
([MM9_RUDE_SCR_INTEGRATION.md](../mm9/MM9_RUDE_SCR_INTEGRATION.md)). Fleet Foot is a separate world rule in
Fly's slot (`world.yml fleetFoot`, `game/party/WorldSpells.h`; [PLAN.md](PLAN.md)).

### 1.3 Monster rows that cast

55 `MONSTERS.txt` rows have a spell cell. Fifty-two of them are imported; Magic Mine (179) and the hirelings Arienh
A'Klindor (281) and Ake the Righteous (283) are not. Of the imported rows, 35 have a number above 0 in
`SpellUse%1`, 14 are `concat` (1.4), and 3 have 0 (1.5). As MM9 plays them (native RE §7.2.2), 42 cast: every row
whose scripts call `RangeAttack`, unless `Att%` is 100 with attack 2 (the Dripper) or both its spells are defense or
healing (the Reverend Monk). The "Slot, chance" column below gives the `SpellUse` cells as written; the chances MM9
casts by are in [6.6](#66-spell-choice-and-concat-as-mm9-plays-them-2026-11-04).

"MM9 avg" is the average damage of one cast. For Sparks it is the whole volley if every spark hits.

| Row | Monster (level) | Placed | Slot, chance | MM9 cell | MM9 avg | Notes |
|---|---|---|---|---|---|---|
| 75 | Dragonfly Mite (2) | 18 | S1 100 % | Elemental Bolt N1 | 2.5 | also BlueThingy bolt, Att% 50 |
| 76 | Dragonfly (3) | 31 | S1 100 % | Elemental Bolt N2 | 5 | YellowThingy |
| 77 | Fire Dragonfly (5) | 25 | S1 100 % | Elemental Bolt N4 | 10 | RedThingy |
| 89 | Astral Icky (18) | 3 | S1 100 % | Poison N1 | — | **never cast in MM9**: `FlyingIcky.scr` has no `RangeAttack` path |
| 97 | Troglodyte Wren (17) | 8 | S1 100 % | Poison N3 | 7.5 + DoT | GreenThingy, Att% 50 |
| 98 | Troglodyte Gnoll (24) | 11 | S1 100 % | Disease E6 | 0, then 2/min for 30 min | GreenThingy |
| 106 | Ice Lobber (20) | 14 | S1 100 % | Elemental Bolt E6 | 21 | BlueThingy2, rooted |
| 123 | Initiate (25) | 18 | S1 100 % | Sparks N4 | 5 × 6 = 30 | casts only when hostile (`monkguardbasic`) |
| 124 | Monk (35) | 8 | S1 95 %, S2 5 % | Sparks E6; Bless E7 | 7 × 8 = 56; +12 to-hit | same |
| 125 | Reverend Monk (50) | 4 | S1 85 %, S2 15 % | Natural Armor M10; Heal M7 | AC +10; 33 HP | same |
| 140 | Specter (55) | 18 | S1 100 % | Dark Grasp M10 | debuff | `ghost` hover |
| 146 | Petrified Mummy (40) | 19 | S1 95 %, S2 5 % | Curse M12; Paralyze M10 | debuffs | resurrecter |
| 156 | Evil Apprentice (25) | 18 | S1 100 % | Elemental Bolt E6 | 21 | turret caster, `EvilSorcerer` |
| 157 | Evil Sorcerer (35) | 15 | S1 100 % | Elemental Bolt E8 | 28 | same |
| 158 | Evil Grand Sorcerer (50) | 9 | S1 80 %, S2 20 % | Chain Lightning M10; Spell Reaver M8 | 45 + chain; dispel | same |
| 159 | Winged Oddity (27) | 15 | S1 50 %, S2 50 % | Sparks N3; Elemental Bolt E4 | 25; 14 | `flyrange` |
| 160 | Winged Mutant (39) | 8 | S1 50 %, S2 50 % | Sparks E6; Elemental Bolt E6 | 56; 21 | same |
| 161 | Winged Aberration (51) | 12 | S1 50 %, S2 50 % | Sparks M9; Elemental Bolt E8 | 99; 28 | same |
| 162 | Fright (35) | 8 | S1 100 % | Fear E4 | debuff | `Banshee` flier |
| 163 | Dread (55) | 1 | S1 100 % | Fear E8 | debuff | same |
| 164 | Terror (65) | 6 | S1 100 % | Fear M10 | debuff | same, resurrecter |
| 182 | Zombie (17) | 20 | S1 10 %, S2 90 % | Spell Reaver M10; Wound M8 | dispel; 50 | resurrecter |
| 195 | Bloodsucker (20) | 16 | S1 100 % | Wound E5 | 30 | |
| 196 | Annelid (33) | 12 | S1 50 %, S2 50 % | Dark Grasp M7; Wound E7 | debuff; 38 | |
| 197 | Vampir (48) | 6 | S1 45 %, S2 55 % | Souldrinker G12; Wound M10 | 79 to all + heal; 60 | |
| 207 | Lich (45) | 13 | S1 100 % | Fear E6 | debuff | |
| 208 | Power Lich (55) | 15 | S1 85 % | Curse E7 | debuff | |
| 209 | Lich King (65) | 10 | S1 50 %, S2 50 % | Dark Grasp M10; Curse M8 | debuffs | |
| 212 | Dragon King (500) | 1 | S1 90 %, S2 10 % | Column-of-Fire G15; Paralyze E5 | 82.5 (area); debuff | boss, also DragonFireBolt and DragonBreath2 |
| 228 | Eye (35) | 43 | S1 100 % | Fear E4 | debuff | PurpleThingy bolt, Att% 50 |
| 229 | Orbus (45) | 31 (+4 spawners) | S1 100 % | Fear E7 | debuff | BlueLine bolt |
| 230 | Oculus (50) | 30 | S1 25 %, S2 75 % | Paralyze E10; Curse M8 | debuffs | BlueLine bolt |
| 261 | Njam the Meddler (200) | 3 | S1 20 %, S2 20 % | Death's Touch G15; Disease G15 | 67 + heal; 7/min for 150 min | invulnerable cameo boss |
| 301 | Ebora (99) | 2 (`SuccEbora`) | S1 60 %, S2 40 % | Column-of-Fire G15; Souldrinker G12 | 82.5; 79 to all | bathhouse set piece |
| 302 | Concubine (60) | 3 | S1 50 %, S2 50 % | Sparks N3; Elemental Bolt N3 | 25; 7.5 | bathhouse |

Spells by placed casters (casting rows only):

| MM9 spell | Rows | Placed casters |
|---|---|---|
| Elemental Bolt | 75, 76, 77, 106, 156, 157, 159, 160, 161, 302 | 159 |
| Fear | 162, 163, 164, 207, 228, 229 | 102 (+4 spawners) |
| Curse | 146, 208, 209, 230 | 74 |
| Sparks | 123, 124, 159, 160, 161, 302 | 64 |
| Wound | 182, 195, 196, 197 | 54 |
| Paralyze | 146, 212, 230 | 50 |
| Dark Grasp | 140, 196, 209 | 40 |
| Spell Reaver | 158, 182 | 29 |
| Disease | 98, 261 | 14 |
| Chain Lightning | 158 | 9 |
| Bless | 124 | 8 |
| Poison | 97 | 8 (89: 3, never cast) |
| Souldrinker | 197, 301 | 8 |
| Natural Armor, Heal | 125 | 4 |
| Death's Touch | 261 | 3 |
| Column-of-Fire | 212, 301 | 3 |

### 1.4 `concat` rows

> **RE result (2026-11-04, [native RE §7.2.2](monster_ai/MM9_AI_NATIVE_RE.md#722-attack-kind-spell-choice-rangeattack-and-concat)):** MM9 has no on-hit `concat`.
>
> - The word parses as `SpellUse%1` 0. `ConcatAttk` and `Bonus` are never read, and no spell is created on a melee hit.
> - A `concat` row's spell is an ordinary ranged spell. The BaseCrawl and Dagrell rows (wolves, mummies 144-145, dagrells) never cast it, because their scripts never call `RangeAttack`.
> - The Basilisks (50 % of shots), Ghast and Revenant (every shot) and the Ghoul (always its `Spl2` Disease) cast it as a normal ranged spell. The Dripper (`Att%` 100) never does.
> - The table below and the `special_attack_chance` rule from `ConcatAttk` (6.1 #8) are therefore OpenYAMM choices, not MM9 behaviour.
> - §1.5 needs a recheck. A lone spell with `SpellUse%1` 0 is still cast through `RangeAttack` (Honk: 25 % of shots at `Att%` 75), and the Ghoul does have a ranged path (`baserange.scr`).

| Row | Monster (level) | Placed | MM9 cell | `ConcatAttk` | Importer's special attack |
|---|---|---|---|---|---|
| 114 | Grey Wolf (20) | 16 | Poison N2 | 10 | Poison1 |
| 115 | Red Wolf (30) | 10 | Disease E4 | 10 | Disease2 |
| 116 | Black Wolf (40) | 8 | Paralyze E7 | 20 | Paralyze |
| 144 | Canopic Mummy (20) | 0 | Disease N2 | 0 | Disease1 |
| 145 | Embalmed Mummy (30) | 20 | Disease E5 | 15 | Disease2 |
| 148 | Venomous Dagrell (59) | 10 | Fear E5 | 10 | Afraid |
| 149 | Spectre Dagrell (79) | 9 | Paralyze E7 | 15 | Paralyze |
| 150–152 | Basilisk, Fibrase, King (15, 23, 30) | 23, 4, 4 | Poison N2, N5, E8 | 0 | Poison1, Poison2, Poison3 |
| 174 | Ghast (20) | 1 | Fear N2 | 0 | Afraid |
| 175 | Ghoul (27) | 8 | Paralyze E5 (+ `SpellUse%2` 100 Disease E5) | 0 | Paralyze |
| 176 | Revenant (38) | 1 | Fear M10 | 0 | Afraid |
| 181 | Dripper (13) | 10 | Disease E5 | 10 | Disease2 |

The proposal (and the first implementation) gave these rows the "importer's special attack" above as an on-hit
condition instead of a spell, with `ConcatAttk` as its chance. That was an OpenYAMM invention. Now
([6.6](#66-spell-choice-and-concat-as-mm9-plays-them-2026-11-04)): the wolves, mummies 144-145 and dagrells have no
spell and no on-hit condition from it (and since 6.7 no `Bonus` special attack either); the Basilisks, Ghast, Ghoul and
Revenant cast it as an ordinary ranged spell (the placed Ghast and Revenant never: 6.7); the Dripper never casts.

### 1.5 Spell cells MM9 never casts

| Row | Monster | Cell | Why it is never cast |
|---|---|---|---|
| 86 | Lobber (16 placed) | Poison N1 | **Rechecked (RE):** cast. A lone spell is chosen whatever `SpellUse%1` holds, and with `Att%` 0 every `RangeAttack` of `lobber.scr` casts it (whether the Lobber class routes `RangeAttack` elsewhere is still open, native RE §16) |
| 186, 216 | Honk (18 placed as `Honk`/`Honk2`) | Spell Reaver M10 | **Rechecked (RE):** cast on 25 % of its shots (`Att%` 75 with attack 2) |
| 89 | Astral Icky (3) | Poison N1 at 100 % | `FlyingIcky.scr` is melee only |
| 175 | Ghoul (8) | Disease E5 in `Spl2` | **Rechecked (RE):** cast. `baserange.scr` shoots, and `Spl1` Paralyze (`concat`, 0) loses every roll to it |
| 123–125 | Initiate, Monk, Reverend Monk | (cast) | only after `monkguardbasic.scr` turns them hostile; the Reverend Monk never (both spells are defense or healing) |
| 179 | Magic Mine | Magic Mine M10 | not imported, placed nowhere, `MagicMine.scr` missing |
| 281, 283 | Arienh A'Klindor, Ake the Righteous | Elemental Blast E6 / Poison Cloud M7; Sparks N3 / Elemental Bolt N3 | hirelings, not imported as monsters |

### 1.6 Projectile attacks that look like spells

These are `Projectile1` (or col 66) attacks with the row's own dice. The importer maps them to MM6–MM8 monster
missile tokens (`monster_projectiles.txt`), and they need no spell. Listed for completeness.

| MM9 projectile | Rows | Token now | Remark |
|---|---|---|---|
| BlueThingy, BlueLine | 75, 105; 229, 230 | Water | |
| BlueThingy2, IceBlast | 106; 206 (Yanmir) | Cold | |
| YellowThingy, Lightning, LightningBolt | 76; 171–173; 204–205 | Elec | |
| RedThingy, Redline, RingOfFire, FireBolt, DragonFireBolt, DragonBreath2 | 77; 83; 165–167; 190–191; 212 | Fire | |
| GreenThingy | 96–98 | Earth | |
| GreenYellowThingy, Goo1–3 | 86, 150–152; 180–181, 234–236 | Body | |
| PurpleThingy | 228 | Dark | the Eye's attacks are Spirit; a `Spirit` or `Mind` token exists |
| RedYellowThingy | 241, 242, 261 | Light | the damage type is mapped to Fire (`ELEMENTAL_PROJECTILE_DAMAGE_TYPES`), so the visual and the element disagree |

The first `Projectile2` column (Horde `FireAr`, Birds `Air`/`Fire`, Astral Icky `Fire`, Lizard-Orcs `Earth`,
hirelings `arrow`) is never read by MM9's AI and is correctly ignored.

### 1.7 Traps, map objects and scripts

**Shooters.** There are 169 `Shooter` DAT objects. Each fires a `PROJECTILE.txt` projectile with a fixed
`DamageAmt` when triggered or on its `ShootInterval`.

| Projectile | Count | Maps (count, DamageAmt) | Driver |
|---|---|---|---|
| FireBolt (fire, 25 ft splash) | 136 | dungeonofsecrets (80 × 5); 1000terrors (23 × 50); chasmofthedead (12 × 20); frosgardcity (6 × 5, 5 × 500); anskramkeep (4 × 5, 2 × 10); lichlab (3 × 5); isleofashes (1 × 5, 1 × 500); verhoffinruins (2 × 20) | triggers, `FrosgardShooter`, `1000t_CircleShooter` |
| Lightning | 15 | 1000terrors (2 × 50); lichlab (6 × 0); wizardslab (7 × 0) | `1000t_LightningShooter`; lichlab/wizardslab ones do no damage (`WizardEffect` ritual visuals) |
| KBYellowLine (knockback 600) | 8 | darkpassageway (8 × 5) | triggers |
| YellowLine | 5 | darkpassageway (5 × 0) | `PassageLaser.scr` mirror puzzle beam |
| DragonBreath2 | 2 | 1000terrors (2 × 50) | triggers |
| ScreamingSkull | 2 | 1000terrors (2 × 50) | `1000t_SkHeadShooter` |
| PurpleThingy | 1 | chasmofthedead (1 × 35) | `OffRailTrigger.scr`: fires at the player while he is off the cart |

**Launch sounds (2026-11-09).** MM9's client plays a projectile's `Launch Sound` (PROJECTILE.txt) where it starts
(cshell.dll `0x10076d15`, the projectile effect's init), Shooter shots included. The map scripts that fire Shooter
missiles (`evt.FireMissile`: Anskram Keep, Chasm of the Dead, Dark Passageway, Dungeon of Secrets, Frosgard City,
Isle of Ashes, Lich Lab, Verhoffin Ruins, 1000 Terrors) call `MM9.launchSound(<ProjectileName>, x, y, z)` at the
shooter (worlds/mm9/events/common/mm9_common.lua `MM9.ProjectileLaunchSounds`: FireBolt dragonfireboltlaunch,
KBYellowLine kbyellowlinelaunch, Lightning chainlight01, PurpleThingy purplethingylaunch, ScreamingSkull fear,
YellowLine yellowlinelaunch; DragonBreath2 has none). The impact sounds are not carried: the missiles are engine
tokens (`Fire`) without one.

The rework's dungeon converter does not carry shooters yet (`overnight/dungeons_ledger.md`: "Not carried: shooters
travelling their markers").

**Other hazards (not spells).** 28 `DamageBrush` volumes (steam vents in the bathhouse at 200, currents in Dungeon
of Secrets at 5–10, Verhoffin Ruins at 40), one `PoisonGas` volume (darkpassageway, 10), one `CorrosiveFluid`
(chasmofthedead), 20 `PropDamager` spike pits, 29 `EarthQuake` objects (a few with `InnerDamage` 1–2), and script
`Damage` calls (`DAMAGER.scr`, `TREMORS.scr`, Yanmir's squish, `PropThrower`/`PropLauncher`). These map to
event damage, not to spells.

**Scripts.** No script casts a gameplay spell. `CastSpell` appears only as a label or a clip name (`EBORABATH`,
`WIZARDMASTER`, `WIZARDSUMMONER`, `ILSFIREBOOK`, `DARKP_CANYONSWITCH`). Spell names in scripts are
`DoClientFX` visuals from `SPELLNAMES.inc` (Column of Fire for Ebora's exit, Elemental Blast in `IMPTRICKSTER` and
`ISLE_ISLANDEXPLOSION`, and Meteor, Town Portal and Paralyze sparkles in the wizard rituals). The scripted effects
are:

- Shooters fired by scripts (`ILSFIREBOOK` and `ISLEASHESBOOK` fire a shooter at the player, plus the shooter
  scripts above).
- `NPC336.scr`/`SIXFIRES.inc`: `SetCondition 13` "poison and disease player". This is a direct condition on the
  party, not a spell; map it to event conditions (Poisoned + Diseased).
- Summons: `SUMMONER`, `ISLE_SUMMONER`, `WIZARDMASTER` (the WizardDemon), `WIZARDSUMMONER`, `CHASM_GHOSTSPAWNER`,
  `SPAWNNJAM`, 23 `Spawner` objects, and Lobber pods (already done natively, `applyMm9PodLaunch`). These are
  monster spawns through map Lua, not spells. MM6–MM8 has only the party's Summon Wisp, so there is nothing to
  map.
- Resurrection: 16 `Resurrect` rows raise the dead with the `ResurrectSpell` clip. This is already implemented as
  the MM9 corpse layer (phase 4a of [MM9_MONSTER_AI_PLAN.md](MM9_MONSTER_AI_PLAN.md)) and needs no spell.

**RUDE/SCR NPC hooks.** None casts a spell on the party. RUDE only mentions curses in dialogue text (NPC207).

## 2. Current state

### 2.1 What a monster can cast in OpenYAMM today

From the shared monster spell support (`MonsterSpellSupport.cpp`) and the indoor and outdoor checks
(`indoorMonsterSpellCastSupported`, `outdoorMonsterSpellCastSupported`):

- **Projectile spells** (`isMonsterProjectileSpellName`): Fire Bolt, Fireball, Incinerate, Lightning Bolt,
  Implosion, Meteor Shower, Ice Bolt, Ice Blast, Acid Burst, Deadly Swarm, Blades, Rock Blast, Mass Distortion,
  Sparks, Mind Blast, Psychic Shock, Harm, Flying Fist, Light Bolt, Spirit Lash, Toxic Cloud, Shrapmetal,
  Dark Grasp, Dragon Breath and Poison Spray.
- **Outdoors only**: Meteor Shower and Starburst. MM9 maps are rebuilt as BLVs, so neither helps.
- **Self actions** (`isMonsterSelfActionSpellName`): Heal, Power Cure, Dispel Magic (clears the party's
  dispellable buffs), and the self-buffs Bless, Day of Protection, Fate, Hammerhands, Haste, Heroism, Hour of Power,
  Pain Reflection, Shield and Stone Skin.
- **Known unsupported**: Paralyze, Mass Curse, Finger of Death and Day of the Gods. Seven MM6–MM8 rows already cast
  Paralyze.
- **Damage of a monster spell** (`rollMonsterSpellDamage`): `DamageBase + skill × 1..DamageDiceSides` from
  `spells.txt`. Mastery does not change damage, except for Fire Spike and Death Blossom. One cast fires one
  projectile; Sparks' multiple projectiles are party-only (`PartySpellCastEffectKind::MultiProjectile`). The
  damage type is the spell's school. Fireball, Meteor Shower, Starburst, Rock Blast, Death Blossom, Dragon Breath
  and Flame Blast burst and hit the whole party (`spellImpactDamageRadius`).
- **No debuffs on the party.** A monster spell that hits the party only does damage. Dark Grasp, Mind Blast and
  the others do nothing else. The row's special attack (a condition) applies only to a melee hit or an attack-1
  missile with spell id 0 (`shouldApplyMonsterSpecialAttack`, `GameplayCombatController.cpp`). Its chance is
  monster level × the special level, in percent.
- **Event (trap) spells** (`evt.CastSpell` / `castSpellFromTo` → `castEventSpell`, indoors and outdoors): any
  spell. Damage is `2 × skill` (Meteor Shower: `8 + skill`; `resolveEventProjectileDamage`). MM6–MM8 traps mostly
  cast Fireball (124 event casts), Sparks (70), Poison Spray (32), Meteor Shower (31) and Fire Bolt (19).

Average damage of the candidates for one monster cast (`s` = skill):

| Spell (id) | School | Avg | Spell (id) | School | Avg |
|---|---|---|---|---|---|
| Fire Bolt (2) | Fire | 2 s | Mind Blast (59) | Mind | 3 + 2 s |
| Fireball (6) | Fire, area | 3.5 s | Psychic Shock (65) | Mind | 12 + 6.5 s |
| Incinerate (11) | Fire | 15 + 8 s | Harm (70) | Body | 8 + 1.5 s |
| Sparks (15) | Air | 2 + s (one spark) | Light Bolt (78) | Light | 2.5 s |
| Lightning Bolt (18) | Air | 4.5 s | Toxic Cloud (90) | Dark | 25 + 5.5 s |
| Implosion (20) | Air | 10 + 5.5 s | Shrapmetal (93) | Dark | 3.5 s (one piece) |
| Poison Spray (24) | Water | 2 + 1.5 s | Dark Grasp (96) | Dark | s |
| Ice Bolt (26) | Water | 2.5 s | Dragon Breath (97) | Dark, area | 13 s |
| Ice Blast (32) | Water | 12 + 3.5 s | Spirit Lash (52) | Spirit | 10 + 5 s |

Self-buff power (`monsterSelfBuffPower`) is `skill + 5` for Bless, Heroism, Hour of Power and Stoneskin. Heal is
5 + 2/3/4/5 per point by mastery.

### 2.2 What the importer maps now

`SPELL_NAMES` in `generate_mm9_monster_tables.py` keeps MM9's mastery and `skill1` as they are. It maps:

| MM9 spell | Mapped to now | Assessment |
|---|---|---|
| Elemental Bolt | Fire Bolt / Lightning Bolt / Ice Bolt / Rock Blast by the row's projectile family (Air when the row has none) | good element choice; skill not rescaled, so damage is off by 0.75–1.8× |
| Sparks | Sparks | right spell, but one spark instead of 5–12, so 10–20 % of MM9's volley |
| Chain Lightning | Lightning Bolt | good: 45 = 45 at M10 |
| Column-of-Fire | Incinerate | good spell, 135 vs 82.5 (1.6×) |
| Curse | Dark Grasp | only `skill` damage, no curse |
| Dark Grasp | Dark Grasp | only `skill` damage, no debuff |
| Paralyze | Dark Grasp | only `skill` damage, no paralysis |
| Fear | Mind Blast | adds 11–23 damage that MM9 does not have; no fear |
| Disease | Toxic Cloud | Gnoll E6: 58 instant damage, no disease |
| Poison | Poison Spray | good (6.5 vs 7.5), no lingering poison |
| Wound | Harm | right idea; Harm's 1–2 per point gives 40 % of MM9's damage |
| Death's Touch | Dragon Breath | Njam GM15: 195 to the whole party vs 67 to one, with no heal (3×, area) |
| Souldrinker | Dragon Breath | GM12: 156 to the whole party vs 79 (2×) |
| Natural Armor | Stone Skin | skill 10 gives +15 AC vs +10, and see the bug below |
| Bless | Bless | exact (+12) |
| Heal | Heal | exact (33) |
| Spell Reaver | Dispel Magic | good, same role |
| `concat` | the row's special attack (Poison1–3, Disease1–3, Afraid, Paralyze, Curse) | wrong (RE): MM9 casts it as an ordinary spell or not at all (6.6) |

Doubtful choices and bugs:

- **Stone Skin gives no AC.** `parseMonsterSpellName` lowercases the table name to `"stone skin"`.
  `monsterSelfBuffPower` matches only `"stoneskin"`, so the power is 0, while the timer accepts both spellings.
  Found by reading, not tested. It also affects the three MM6–MM8 Stone Skin casters.
- **Spells MM9 never casts become real casts.** The Astral Icky gets Poison Spray at 100 %. The Ghoul's unread
  `Spl2` becomes Toxic Cloud E5 at 100 % (52 damage from a melee-only monster).
- **Concat chance.** OpenYAMM's chance is level × level %: Spectre Dagrell 79 %, Venomous Dagrell 59 %, Black Wolf
  40 %. MM9's `ConcatAttk` is 10–25 % (not read by MM9's AI loader, so unconfirmed).
- **Spell 2's chance** is the complement `100 − SpellUse%1` (Zombie 90 % Wound). MM9's own `Spl2` choice was not
  traced.

## 3. Proposed mapping

Principles:

1. Keep the **role and element**: a damage bolt becomes a same-element MM6–MM8 bolt, area becomes area, and buff,
   heal and dispel stay the same.
2. Pick **`skill1`** so the average of one cast is close to MM9's at that monster's level. Keep MM9's mastery
   letter; it matters only for heals and buffs.
3. Map a **debuff** (Curse, Dark Grasp, Fear, Paralyze) to the MM6–MM8 spell of the same name or role, and give a
   monster's cast of that spell a party effect (engine gap G1). Until then, the fallback is the MM6–MM8 special
   attack (on-hit condition), which works today, or a low-skill vehicle.
4. **Sparks:** one spark per cast, so scale the skill so one spark is about half of MM9's volley (open question 3).
5. **Drop** spell cells MM9 never casts (1.5).

### 3.1 Per MM9 spell

| MM9 spell (element, effect) | MM6–MM8 spell (id) | Skill rule | Why | Alternatives | Monster cast today |
|---|---|---|---|---|---|
| Elemental Bolt (Elem, s × 1–4/6/8/10) | by the row's projectile: Ice Bolt (26), Lightning Bolt (18), Fire Bolt (2); no projectile: Lightning Bolt (18); Concubine: Ice Bolt (26) | match the average: Ice Bolt `2.5 s`, Lightning `4.5 s`, Fire Bolt `2 s` | same element as the row's coloured bolt; MM6–MM8's basic bolts | Rock Blast for earth rows (none cast it); Fire Bolt for the sorcerers | yes |
| Sparks (Elem, 5–12 sparks of 2 + s) | Sparks (15) | `s' = n × (2 + s) / 2 − 2`, n = 5/7/9/12 by mastery | same spell, same formula per spark | full volley `n × (2 + s) − 2`; Lightning Bolt for the M9 Aberration | yes, one spark |
| Chain Lightning (Elem, s × 1–8 + chain) | Lightning Bolt (18) | same skill (45 = 45) | same damage; MM6–MM8 has no chain | Implosion M6 (43) | yes |
| Column-of-Fire (Elem, 30 + s × 1–6, G area) | Incinerate (11) | `s' = (avg − 15) / 8` → 9 | MM6–MM8's heavy single-target fire | Fireball (6) s = 24 (84, area like the G radius); Meteor Shower is outdoor only | yes |
| Curse (Dark, to-hit and attack-rate penalty, no casting) | Dark Grasp (96) + **G1**: a monster's Dark Grasp leaves the struck character **Cursed** | keep the MM9 skill (Dark Grasp does `skill` damage) | Dark-school debuff projectile; MM6–MM8's Cursed (actions fail) is the nearest party state | fallback today: special attack `Curse` (on hit); Mind Blast s = 1 as a token cast | yes (damage only) |
| Dark Grasp (Dark, slow, AC and damage down) | Dark Grasp (96) + G1 (same effect as Curse, or **Weak**; open question 2) | keep | same name, same role in MM7/MM8 | special attack `Weak` | yes (damage only) |
| Fear (Dark, Afraid) | Fear (122, Mind, the MM8 dragon ability) + **G1**: the struck character becomes **Afraid** | keep (no damage) | same name; Mind is MM6–MM8's fear school (Remove Fear, Mass Fear) | Mass Fear (63); fallback today: Mind Blast (59) at skill 1 (5 damage) or special attack `Afraid` | no |
| Paralyze (Dark, Paralyzed) | Paralyze (81) + **G1**: the struck character becomes **Paralyzed** | keep | same name and role; already in seven MM6–MM8 rows that the engine cannot cast, so one fix serves both | fallback today: special attack `Paralyze` | no (known unsupported) |
| Disease (Dark, damage over time) | Toxic Cloud (90) | low skill: Gnoll E1 (30); Njam keeps GM15 | Dark element, a "noxious gas"; MM6–MM8 has no disease spell | Poison Spray (24) E6 (11); add a Diseased rider with G1b | yes |
| Poison (Elem, s × 1–4 + damage over time) | Poison Spray (24) | `s' = (avg − 2) / 1.5` | same name and role | Poisoned rider with G1b | yes |
| Wound (Dark, 10 + s × 2–6/8/10) | Harm (70) | `s' = (avg − 8) / 1.5` | "inflicts magical damage directly", same role | Toxic Cloud (Dark): s = 1/2/5/6 for 30/38/50/60; Shrapmetal | yes |
| Death's Touch (Dark, 7 + s × 1–7, 30 % heals the caster) | Spirit Lash (52) | `10 + 5 s` → GM11 (65) | "weakens the link between body and soul", single target; Njam's melee is Spirit | target: Lifedrain (111, heals the caster by a third), **G2**; Toxic Cloud GM8 (69) | yes |
| Souldrinker (Dark, 25 + s × 1–8 to all, heals the caster) | fallback: Dragon Breath (97); target: **Souldrinker (99)** with **G2** | Dragon Breath `13 s` → GM6 (78 to the party); Souldrinker keeps G12 (same formula, 25 + s × 1–8) | Dragon Breath is Dark and hits the whole party; Souldrinker is the same spell | Toxic Cloud GM10 (80, one target) | Dragon Breath yes; Souldrinker no |
| Natural Armor (AC +2 per 2 points) | Stone Skin (38) | `skill + 5` = +10 → 5 | same role, self-buff | — | yes, but see bug **G4** |
| Bless (to-hit 5 + s) | Bless (46) | keep (7 → +12) | exact | — | yes |
| Heal (5 + 4 per point at M) | Heal (68) | keep (M7 → 33) | exact | Power Cure | yes |
| Spell Reaver (dispel) | Dispel Magic (80) | keep | same role; clears party buffs | — | yes |
| Elemental Blast (s × 1–6 area; hireling 281 only) | Fireball (6) | keep (same formula) | area fire | — | yes |
| Poison Cloud (25 + s × 1–10; hireling 281 only) | Toxic Cloud (90) | keep (same formula) | identical numbers | — | yes |
| Magic Mine (179, placed nowhere) | Fire Spike (7) | — | the MM6–MM8 mine | not needed | no |

### 3.2 Per monster row

`New?`: **skill** = same spell, new skill; **spell** = a different spell; **drop** = remove; **G1/G2** = needs an
engine gap; `=` = the importer already does this.

| Row | Monster | MM9 | MM9 avg | Now (avg) | Proposed | Avg | New? |
|---|---|---|---|---|---|---|---|
| 75 | Dragonfly Mite | Elemental Bolt N1 | 2.5 | Ice Bolt,N,1 (2.5) | Ice Bolt,N,1 | 2.5 | = |
| 76 | Dragonfly | Elemental Bolt N2 | 5 | Lightning Bolt,N,2 (9) | Lightning Bolt,N,1 | 4.5 | skill |
| 77 | Fire Dragonfly | Elemental Bolt N4 | 10 | Fire Bolt,N,4 (8) | Fire Bolt,N,5 | 10 | skill |
| 89 | Astral Icky | Poison N1 (never cast) | — | Poison Spray,N,1 @100 % | none | — | drop |
| 97 | Troglodyte Wren | Poison N3 | 7.5 | Poison Spray,N,3 (6.5) | Poison Spray,N,4 | 8 | skill |
| 98 | Troglodyte Gnoll | Disease E6 | DoT | Toxic Cloud,E,6 (58) | Toxic Cloud,E,1 | 30.5 | skill |
| 106 | Ice Lobber | Elemental Bolt E6 | 21 | Ice Bolt,E,6 (15) | Ice Bolt,E,8 | 20 | skill |
| 123 | Initiate | Sparks N4 | 30 | Sparks,N,4 (6) | Sparks,N,13 | 15 | skill |
| 124 | Monk | Sparks E6; Bless E7 | 56; +12 | Sparks,E,6 (8); Bless,E,7 | Sparks,E,26; Bless,E,7 | 28; +12 | skill; = |
| 125 | Reverend Monk | Natural Armor M10; Heal M7 | +10 AC; 33 | Stone Skin,M,10 (0 by bug); Heal,M,7 | Stone Skin,M,5; Heal,M,7 | +10 (after G4); 33 | skill; = |
| 140 | Specter | Dark Grasp M10 | debuff | Dark Grasp,M,10 (10) | Dark Grasp,M,10 | 10 + debuff | = (+G1) |
| 146 | Petrified Mummy | Curse M12; Paralyze M10 | debuffs | Dark Grasp,M,12; Dark Grasp,M,10 | Dark Grasp,M,12; Paralyze,M,10 | debuffs | = (+G1); spell (G1) |
| 156 | Evil Apprentice | Elemental Bolt E6 | 21 | Lightning Bolt,E,6 (27) | Lightning Bolt,E,5 | 22.5 | skill |
| 157 | Evil Sorcerer | Elemental Bolt E8 | 28 | Lightning Bolt,E,8 (36) | Lightning Bolt,E,6 | 27 | skill |
| 158 | Evil Grand Sorcerer | Chain Lightning M10; Spell Reaver M8 | 45; dispel | Lightning Bolt,M,10; Dispel Magic,M,8 | same | 45 | = |
| 159 | Winged Oddity | Sparks N3; Elemental Bolt E4 | 25; 14 | Sparks,N,3 (5); Lightning Bolt,E,4 (18) | Sparks,N,11; Lightning Bolt,E,3 | 13; 13.5 | skill |
| 160 | Winged Mutant | Sparks E6; Elemental Bolt E6 | 56; 21 | Sparks,E,6 (8); Lightning Bolt,E,6 (27) | Sparks,E,26; Lightning Bolt,E,5 | 28; 22.5 | skill |
| 161 | Winged Aberration | Sparks M9; Elemental Bolt E8 | 99; 28 | Sparks,M,9 (11); Lightning Bolt,E,8 (36) | Sparks,M,47; Lightning Bolt,E,6 | 49; 27 | skill |
| 162 | Fright | Fear E4 | debuff | Mind Blast,E,4 (11) | Fear,E,4 (G1) / fallback Mind Blast,E,1 | 0 / 5 | spell |
| 163 | Dread | Fear E8 | debuff | Mind Blast,E,8 (19) | Fear,E,8 (G1) / Mind Blast,E,1 | 0 / 5 | spell |
| 164 | Terror | Fear M10 | debuff | Mind Blast,M,10 (23) | Fear,M,10 (G1) / Mind Blast,M,1 | 0 / 5 | spell |
| 175 | Ghoul | (Spl2 Disease E5, unread) | — | Toxic Cloud,E,5 @100 % (52.5) | none (keeps the concat Paralyze); superseded by 6.6: Toxic Cloud,E,1 on every shot | — | drop |
| 182 | Zombie | Spell Reaver M10; Wound M8 | dispel; 50 | Dispel Magic,M,10; Harm,M,8 (20) | Dispel Magic,M,10; Harm,M,28 | 50 | =; skill |
| 186, 216 | Honk | Spell Reaver M10 @0 % | — | Dispel Magic,M,10 @0 % | unchanged (never cast) | — | = |
| 195 | Bloodsucker | Wound E5 | 30 | Harm,E,5 (15.5) | Harm,E,15 | 30.5 | skill |
| 196 | Annelid | Dark Grasp M7; Wound E7 | debuff; 38 | Dark Grasp,M,7; Harm,E,7 (18.5) | Dark Grasp,M,7; Harm,E,20 | 7 + debuff; 38 | = (+G1); skill |
| 197 | Vampir | Souldrinker G12; Wound M10 | 79 all; 60 | Dragon Breath,GM,12 (156 area); Harm,M,10 (23) | Dragon Breath,GM,6 (Souldrinker,GM,12 with G2); Harm,M,35 | 78 area; 60.5 | skill (spell with G2); skill |
| 207 | Lich | Fear E6 | debuff | Mind Blast,E,6 (15) | Fear,E,6 (G1) / Mind Blast,E,1 | 0 / 5 | spell |
| 208 | Power Lich | Curse E7 | debuff | Dark Grasp,E,7 (7) | Dark Grasp,E,7 | 7 + Cursed | = (+G1) |
| 209 | Lich King | Dark Grasp M10; Curse M8 | debuffs | Dark Grasp,M,10; Dark Grasp,M,8 | same | 10 / 8 + debuff | = (+G1) |
| 212 | Dragon King | Column-of-Fire G15; Paralyze E5 | 82.5 area; debuff | Incinerate,GM,15 (135); Dark Grasp,E,5 | Incinerate,GM,9; Paralyze,E,5 | 87; debuff | skill; spell (G1) |
| 228 | Eye | Fear E4 | debuff | Mind Blast,E,4 (11) | Fear,E,4 (G1) / Mind Blast,E,1 | 0 / 5 | spell |
| 229 | Orbus | Fear E7 | debuff | Mind Blast,E,7 (17) | Fear,E,7 (G1) / Mind Blast,E,1 | 0 / 5 | spell |
| 230 | Oculus | Paralyze E10; Curse M8 | debuffs | Dark Grasp,E,10; Dark Grasp,M,8 | Paralyze,E,10; Dark Grasp,M,8 | debuffs | spell (G1); = (+G1) |
| 261 | Njam the Meddler | Death's Touch G15; Disease G15 | 67 + heal; DoT | Dragon Breath,GM,15 (195 area); Toxic Cloud,GM,15 (107.5) | Spirit Lash,GM,11 (Lifedrain with G2); Toxic Cloud,GM,15 | 65; 107.5 | spell; = |
| 301 | Ebora | Column-of-Fire G15; Souldrinker G12 | 82.5; 79 all | Incinerate,GM,15 (135); Dragon Breath,GM,12 (156) | Incinerate,GM,9; Dragon Breath,GM,6 (Souldrinker with G2) | 87; 78 area | skill; skill |
| 302 | Concubine | Sparks N3; Elemental Bolt N3 | 25; 7.5 | Sparks,N,3 (5); Lightning Bolt,N,3 (13.5) | Sparks,N,11; Ice Bolt,N,3 | 13; 7.5 | skill; spell |

The `concat` rows (1.4) keep their on-hit special attacks. Lobber (86) and the Honks keep their 0 % cells or
lose them; nothing changes in play either way. (Superseded by 6.6: no on-hit riders; the Lobber and the Honks cast.)

### 3.3 Traps

All shooters become event casts (`castSpellFromTo` or a scene shooter that calls it). Event spell damage is
`2 × skill`, so skill = `DamageAmt / 2` (rounded up).

| MM9 shooter projectile | MM6–MM8 spell (id) | Skill | Why | Alternatives |
|---|---|---|---|---|
| FireBolt (136, 25 ft splash) | Fireball (6) | 5 → 3, 10 → 5, 20 → 10, 50 → 25, 500 → 250 | MM9's FireBolt explodes; Fireball is MM6–MM8's standard trap (124 event casts) | Fire Bolt (2), one target |
| Lightning (2 damaging, 1000 Terrors) | Lightning Bolt (18) | 25 | same element and look | Sparks (15) |
| Lightning (13 with `DamageAmt` 0) | none: visual only (ritual arcs) | — | they do no damage | — |
| DragonBreath2 (2, 1000 Terrors) | Fireball (6) | 25 | fire breath, area | Dragon Breath (97) is Dark; Flame Blast (123) is fire but untested as an event cast |
| ScreamingSkull (2, 1000 Terrors) | Mind Blast (59) | 25 | the "screaming" skull: mind | an event missile with the `MM9Skull` object (no spell, carries its own damage) |
| KBYellowLine (8, darkpassageway) | Light Bolt (78) | 3 | yellow light beam | Sparks; the knockback is not reproduced |
| YellowLine (5, mirror puzzle) | none: puzzle beam | — | no damage | — |
| PurpleThingy (1, chasmofthedead, 35) | Mind Blast (59) | 18 | purple bolt, as the Eye's | Toxic Cloud (Dark) |

The other hazards stay event damage: `DamageBrush`, `PoisonGas` (Body/poison damage, optionally Poisoned),
`EarthQuake` and the script `Damage` calls. Six Fires' `SetCondition 13` becomes event Poisoned + Diseased.

## 4. Engine gaps

| Id | Gap | Needed for | Where |
|---|---|---|---|
| G1 | **Monster debuff spells do nothing to the party.** A monster spell hit only deals damage. Add a party effect for monster casts: Paralyze (81) → Paralyzed, Fear (122) → Afraid, Dark Grasp (96) → Cursed (or Weak), with a resistance save. Paralyze then also works for the seven MM6–MM8 rows (now `isKnownUnsupportedMonsterSpellName`). Dark Grasp from MM6–MM8 monsters would change as well; no MM6–MM8 row casts it, so nothing regresses. | Curse, Dark Grasp, Fear, Paralyze: 207 placed casters | `MonsterSpellSupport.cpp`, `GameplayCombatController.cpp` (party projectile impact), indoor/outdoor cast checks |
| G1b | Optional: a condition rider on a damaging monster spell (Poisoned on Poison Spray, Diseased on Toxic Cloud), as a per-row opt-in so MM6–MM8 rows are unchanged; for example, let the row's special attack also apply on spell hits. | Poison, Disease (Troglodytes, Njam) | `shouldApplyMonsterSpecialAttack` |
| G2 | Monster Souldrinker (party-wide drain, heals the caster) and Lifedrain (single target, heals by a third) are not castable. Until then: Dragon Breath and Spirit Lash. | Souldrinker (Vampir, Ebora), Death's Touch (Njam) | `isMonsterProjectileSpellName`, the direct-spell path |
| G3 | One spark per monster Sparks cast (multi-shot is party-only). The data workaround is the skill scaling in 3.2. Firing several sparks for monsters would change MM6–MM8's seven Sparks casters, so it would need an opt-in. | Sparks rows | `GameplaySpellService`, monster cast path |
| G4 | **Bug:** `monsterSelfBuffPower` matches `"stoneskin"` but monster spell names are lowercased table names (`"stone skin"`), so a monster's Stone Skin gives +0 AC. | Reverend Monk; three MM6–MM8 rows | `GameplayActorAiSystem.cpp` `monsterSelfBuffPower` |
| G5 | Shooters are not carried by the dungeon converter (markers, `ShootInterval`, `StartOn`, triggers and script control). Event casts exist, but there is no shooter object in scenes. KBYellowLine's knockback has no counterpart. | 151 damaging shooters on 9 maps | dungeon converter, scene/event support |
| G6 | Meteor Shower and Starburst are cast by monsters only outdoors. This matters only if Column-of-Fire uses Meteor Shower (not proposed). | — | `indoorMonsterSpellCastSupported` |

## 5. Open questions for the user

1. **Debuffs (G1):** implement the party effects of monster Paralyze, Fear and Dark Grasp before the MM9 monsters
   ship, or ship the first version with the fallbacks (MM6–MM8 special-attack conditions on hit, or a 5-damage
   Mind Blast instead of Fear)?
2. **Dark Grasp on the party:** Cursed (MM9's Curse and Dark Grasp both become Dark Grasp) or Weak (closer to MM9
   Dark Grasp's "−50 % melee damage")? Or Cursed for Curse rows and Weak for Dark Grasp rows, which would need a
   row-level choice?
3. **Sparks:** scale one spark to half the MM9 volley (proposed: Initiate 13, Monk and Winged Mutant 26, Winged
   Aberration 47), to the full volley, or leave the authored skill (one weak spark)?
4. **Spells MM9 never casts:** drop the Astral Icky's Poison and the Ghoul's Disease (proposed), or keep them as
   OpenYAMM additions? The Monks cast only once turned hostile; they keep their spells.
5. **Elemental Bolt without a coloured projectile** (Evil Sorcerers, Winged monsters): keep Lightning Bolt
   (proposed), or choose per monster (for example Fire Bolt for the sorcerers)? The Concubines change to Ice Bolt
   for the bathhouse.
6. **Wound:** Harm with large skills (15–35; Body school), or Toxic Cloud with small skills (Dark, the MM9
   element)?
7. **Fire shooters:** Fireball (area, as MM6–MM8 traps) or Fire Bolt? Are the `DamageAmt` 500 shooters in
   Frosgard City and on the Isle of Ashes meant to kill, and should they stay so?
8. **`concat` chance:** OpenYAMM's on-hit chance is level × level % (Spectre Dagrell 79 %), while MM9's
   `ConcatAttk` is 10–25 %. Cap or override the chance for MM9 rows?
9. **Spell 2 chance:** keep the importer's complement rule (`100 − SpellUse%1`, for example Zombie 90 % Wound),
   given that MM9's own `Spl2` choice is untraced?

## 6. Implementation (2026-11-04)

> **RE result (2026-11-04, [native RE §7.2.2](monster_ai/MM9_AI_NATIVE_RE.md#722-attack-kind-spell-choice-rangeattack-and-concat)):** answers 8 and 9 in 6.1 rest on guesses that the binary contradicts.
>
> - Spell 2's share is `100 − SpellUse%1` of the spell casts only, and only when both spells exist.
> - The spell-versus-attack chance is `100 − Att%`.
> - `ConcatAttk` has no MM9 effect.
> - The Oculus should cast about 12.5 % Paralyze, 37.5 % Curse and 50 % `BlueLine` per shot.
> - `mm9RangedAbility` now never reaches spell 2 when attack 1 is ranged.
>
> Done in [6.6](#66-spell-choice-and-concat-as-mm9-plays-them-2026-11-04).

The user approved the mapping with these answers, and it is in place: generators, regenerated MM9 tables in
`assets_dev/worlds/mm9/` (hard-linked into both review roots, `output/mm9_rework/assets_dev` and
`output/mm9_rework/isleofashes_blv_root`), and two new optional monster modifiers in the shared engine. There are no
world checks in the code: a monster row that sets the modifiers gets the behaviour, whatever its world; MM6-MM8 rows
set none, and their tables are byte-identical.

### 6.1 Answers

| # | Question | Answer (user) | Done |
|---|---|---|---|
| 1 | Debuffs (G1) | Build now as an optional per-row field: Fear → Afraid, Paralyze → Paralyzed, Curse (as Dark Grasp) → Cursed, Dark Grasp → Weak. The seven MM6-MM8 rows that list Paralyze stay as they are. | modifier `spell_conditions` |
| 2 | Dark Grasp on the party | Dark Grasp leaves Weak, Curse leaves Cursed (per spell slot: the Lich King casts both as Dark Grasp) | as 1 |
| 3 | Sparks | Revised (user, 2026-11-04): a monster's Sparks fires the MM6-MM8 volley by mastery (G3 fixed in the engine for every world); MM9 rows take the mastery whose spark count is nearest MM9's and keep MM9's skill, so each spark does MM9's damage. | engine + generator (`SPARKS_MASTERY`) |
| 4 | Spells MM9 never casts | Drop the Astral Icky's Poison and the Ghoul's second spell (Disease) | generator (`NEVER_CAST_SPELLS`); 6.6: the Ghoul does cast its Disease (RE), the rows without `RangeAttack` are `NO_RANGE_ATTACK_SOURCES` |
| 5 | Elemental Bolt without a coloured projectile | Per monster from its MM9 spell effect or FX; Lightning Bolt where nothing tells | generator (`ELEMENTAL_BOLT_BY_CAST_FX`) |
| 6 | Wound | Harm, skills to MM9's damage | generator |
| 7 | Fire shooters | Fire Bolt, as MM9 fires; report on the 500-damage shooters, keep MM9's damage | [6.4](#64-traps) |
| 8 | `concat` chance | An optional per-row override of level x level %; MM9 rows get `ConcatAttk` | modifier `special_attack_chance`; removed in 6.6 (MM9 never reads `ConcatAttk`) |
| 9 | Spell 2 chance | Keep `100 − SpellUse%1` | replaced in 6.6 by MM9's own choice |

### 6.2 The new fields

Both are monster modifiers (`worlds/<world>/modifiers.yml`, [MONSTER_MODIFIERS.md](../MONSTER_MODIFIERS.md)), not
monster table columns. The table's columns are MM8's `monster_data.txt` layout shared by every world, and a new column
would mean rewriting the MM6-MM8 rows; a modifier is the existing per-world, per-monster, optional add-on with
validated parameters and line-numbered errors, which MM9 already uses for its AI profile and recovery.

- `spell_conditions: {spell1, spell2, chance}`: the condition a hit on a party member by that spell slot leaves (by
  `chance`, then the member's save as against a special attack). It also makes Paralyze and Fear castable for that slot,
  as projectiles that deal no damage; without a condition for them they stay unsupported (`isKnownUnsupportedMonsterSpellName`
  now lists Fear too), so the MM6-MM8 Paralyze rows still never cast it.
- `special_attack_chance: {percent}`: the special attack's chance per hit instead of monster level x special level %.
  Removed in 6.6.

Engine: `game/tables/MonsterModifiers.{h,cpp}` (catalogue, parsing), `game/tables/MonsterSpecialAttackKind.h` (the
enum, moved out of `MonsterTable.h` so the modifiers can name it), `GameplayCombatActorInfo` (four fields) filled by
`applyHitConditionModifiers` in both runtimes, `monsterHitCondition` / `rollMonsterHitCondition` in
`GameplayCombatController.cpp`, `MonsterSpellSupport` (`isMonsterConditionSpellName`, `isMonsterConditionSpellId`,
`monsterConditionSpellCastSupported`, `monsterSpellProjectileCount`, `monsterSpellVolleyTarget`), the projectile
resolvers and actor spell casts of both runtimes, no damage in
`GameplayProjectileService::resolveProjectilePartyImpactDamage`. No save field (data only); the save version is unchanged.

**G4 fixed** in every world: `monsterSelfBuffPower` now matches `"stone skin"` (the lowercased table name), so a
monster's Stone Skin gives skill + 5 AC (the three MM6-MM8 Stone Skin casters too; their table rows are unchanged).

Generators: `tools/mm9_import_discovery/generate_mm9_monster_tables.py` (`SPELL_NAMES`, `mapped_skill`,
`mm9_spell_average`, `MONSTER_SPELL_AVERAGE`, `SPARKS_MASTERY`, `ELEMENTAL_BOLT_BY_CAST_FX`, `NO_RANGE_ATTACK_SOURCES` (6.6), `SPELL_CONDITIONS`,
`cast_spells`, `spell_conditions`; a `concat` rider keeps MM9's own skill for its Poison/Disease level) and
`generate_mm9_monster_modifiers.py` (`hit_condition_items`; it skips the recovery of a dropped spell). Run both, then
re-link the five files in the review roots (or `review_root.py`'s refresh):

```sh
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py
python3 tools/mm9_import_discovery/generate_mm9_monster_modifiers.py
```

### 6.3 Final mapping applied

Sparks: a monster's Sparks fires 3/5/7/9 sparks at Normal/Expert/Master/Grandmaster (MM6-MM8; MM9 fires 5/7/9/12), each
2 + 1 per point of skill in both games. The MM9 rows keep MM9's skill and take the mastery with the nearest count:
Normal → Expert (5), Expert → Master (7), Master and Grandmaster → Grandmaster (9; MM9's Grandmaster 12 has no match).
In the table "Avg" for Sparks is sparks x damage per spark.

Skill rule for the other spells: the nearest skill at which one cast's average (`rollMonsterSpellDamage`: DamageBase + skill x 1..DiceSides
from `spells.txt`) equals MM9's average at that row's mastery and skill; at least 1. Debuffs, buffs, heals and dispels
keep MM9's skill; Natural Armor's AC (+s at Master) is Stone Skin's skill + 5; Disease is Toxic Cloud at skill 1 below
Grandmaster (its base 25 alone), Njam's Grandmaster 15 as it is.

| Row | Monster | MM9 | Applied (was) | Avg (MM9) | Condition |
|---|---|---|---|---|---|
| 75 | Dragonfly Mite | Elemental Bolt N1 | Ice Bolt,N,1 (=) | 2.5 (2.5) | |
| 76 | Dragonfly | Elemental Bolt N2 | Lightning Bolt,N,1 (N,2) | 4.5 (5) | |
| 77 | Fire Dragonfly | Elemental Bolt N4 | Fire Bolt,N,5 (N,4) | 10 (10) | |
| 89 | Astral Icky | Poison N1, never cast | none (Poison Spray,N,1 @100 %) | — | |
| 97 | Troglodyte Wren | Poison N3 | Poison Spray,N,4 (N,3) | 8 (7.5) | |
| 98 | Troglodyte Gnoll | Disease E6 | Toxic Cloud,E,1 (E,6) | 30.5 (DoT) | |
| 106 | Ice Lobber | Elemental Bolt E6 | Ice Bolt,E,8 (E,6) | 20 (21) | |
| 123 | Initiate | Sparks N4 | Sparks,E,4 (N,4) | 5 x 6 = 30 (5 x 6) | |
| 124 | Monk | Sparks E6; Bless E7 | Sparks,M,6 (E,6); Bless,E,7 | 7 x 8 = 56 (7 x 8); +12 | |
| 125 | Reverend Monk | Natural Armor M10; Heal M7 | Stone Skin,M,5 (M,10); Heal,M,7 | +10 AC (+10); 33 | |
| 140 | Specter | Dark Grasp M10 | Dark Grasp,M,10 (=) | 10 | spell1 weak |
| 146 | Petrified Mummy | Curse M12; Paralyze M10 | Dark Grasp,M,12 (=); Paralyze,M,10 (Dark Grasp) | 12; 0 | spell1 cursed, spell2 paralyzed |
| 156 | Evil Apprentice | Elemental Bolt E6 | Fire Bolt,E,11 (Lightning Bolt,E,6) | 22 (21) | |
| 157 | Evil Sorcerer | Elemental Bolt E8 | Fire Bolt,E,14 (Lightning Bolt,E,8) | 28 (28) | |
| 158 | Evil Grand Sorcerer | Chain Lightning M10; Spell Reaver M8 | Lightning Bolt,M,10; Dispel Magic,M,8 (=) | 45 (45) | |
| 159 | Winged Oddity | Sparks N3; Elemental Bolt E4 | Sparks,E,3; Lightning Bolt,E,3 (N,3; E,4) | 5 x 5 (5 x 5); 13.5 (14) | |
| 160 | Winged Mutant | Sparks E6; Elemental Bolt E6 | Sparks,M,6; Lightning Bolt,E,5 (E,6; E,6) | 7 x 8 (7 x 8); 22.5 (21) | |
| 161 | Winged Aberration | Sparks M9; Elemental Bolt E8 | Sparks,G,9; Lightning Bolt,E,6 (M,9; E,8) | 9 x 11 (9 x 11); 27 (28) | |
| 162-164 | Fright, Dread, Terror | Fear E4, E8, M10 | Fear,E,4 / E,8 / M,10 (Mind Blast) | 0 | spell1 afraid |
| 175 | Ghoul | Disease E5 in Spl2 | none (Toxic Cloud,E,5 @100 %); 6.6: Toxic Cloud,E,1 | — (30.5) | (concat Paralyze kept: its Bonus) |
| 182 | Zombie | Spell Reaver M10; Wound M8 | Dispel Magic,M,10; Harm,M,28 (M,8) | 50 (50) | |
| 195 | Bloodsucker | Wound E5 | Harm,E,15 (E,5) | 30.5 (30) | |
| 196 | Annelid | Dark Grasp M7; Wound E7 | Dark Grasp,M,7; Harm,E,20 (E,7) | 7; 38 (38) | spell1 weak |
| 197 | Vampir | Souldrinker G12; Wound M10 | Dragon Breath,G,6 (GM,12); Harm,M,35 (M,10) | 78 area (79 all); 60.5 (60) | |
| 207 | Lich | Fear E6 | Fear,E,6 (Mind Blast) | 0 | spell1 afraid |
| 208 | Power Lich | Curse E7 | Dark Grasp,E,7 (=) | 7 | spell1 cursed |
| 209 | Lich King | Dark Grasp M10; Curse M8 | Dark Grasp,M,10; Dark Grasp,M,8 (=) | 10; 8 | spell1 weak, spell2 cursed |
| 212 | Dragon King | Column-of-Fire G15; Paralyze E5 | Incinerate,G,8 (GM,15); Paralyze,E,5 (Dark Grasp) | 79 (82.5); 0 | spell2 paralyzed |
| 228, 229 | Eye, Orbus | Fear E4, E7 | Fear,E,4 / E,7 (Mind Blast) | 0 | spell1 afraid |
| 230 | Oculus | Paralyze E10; Curse M8 | Paralyze,E,10 (Dark Grasp); Dark Grasp,M,8 (=) | 0; 8 | spell1 paralyzed, spell2 cursed |
| 261 | Njam the Meddler | Death's Touch G15; Disease G15 | Spirit Lash,G,11 (Dragon Breath,G,15); Toxic Cloud,G,15 (=) | 65 (67); 107.5 | |
| 301 | Ebora | Column-of-Fire G15; Souldrinker G12 | Incinerate,G,8 (GM,15); Dragon Breath,G,6 (GM,12) | 79 (82.5); 78 area (79 all) | |
| 302 | Concubine | Sparks N3; Elemental Bolt N3 | Sparks,E,3 (N,3); Lightning Bolt,N,2 (N,3) | 5 x 5 (5 x 5); 9 (7.5) | |

Grandmaster is written `G` in the table, as MM6-MM8's rows write it: the importer wrote `GM`, which the table parser
(`parseSkillMasteryToken`) read as no mastery (fixed in the generator; it mattered for nothing until the Sparks volley,
whose count follows the mastery).

Differences from the proposal in 3.2: Sparks fires a volley (answer 3, revised) instead of one scaled spark; Incinerate is GM 8 (79, the
nearest to 82.5; the proposal rounded up to 9); the Evil Apprentice and Sorcerer cast Fire Bolt (MM9 shows the element
by the cast's hand effect: `EvilSorcerer.abc` rAttack1 `DoFX 2 1`, read as FX1 `redyeldots`; DoFX is 0-based
(`object.lto` `0x1001af90`, found 2026-11-10), so the cast shows FX2 `greenyeldots` and the element is open again), skill 11 and 14; the Winged
monsters and the Concubines have no projectile and no FX, so Lightning Bolt (the Concubine 2, not the proposal's Ice
Bolt). MM9's own Elemental Bolt effect does not tell: its SPELL.txt FX is a random colour per cast at Normal.

`special_attack_chance` (MM9 `ConcatAttk`, where the row has an on-hit condition and a `ConcatAttk` above 0): Grey Wolf
10, Red Wolf 10, Black Wolf 20, Embalmed Mummy 15, Venomous Dagrell 10 (its special is BrkArmor, from the Bonus
column), Spectre Dagrell 15 (BrkItem), Dripper 10, Zombie 15 (DrainSP), Bloodsucker 25 (Disease2). Rows with
`ConcatAttk` 0 (the Basilisks, Canopic Mummy, Ghast, Ghoul, Revenant, and Bonus-only rows such as the Specter's Uncon)
keep level x level %. (Removed in 6.6: every row has level x level % again.)

**G3 fixed** in every world (user, 2026-11-04): a monster's Sparks cast fires the volley of its mastery, 3/5/7/9 sparks
evenly over a 60 degree fan centred on its target (MM6-MM8's monster Sparks; OpenEnroth `Actor.cpp` was the behavioural
reference), each with the normal per-spark damage. `monsterSpellProjectileCount` and `monsterSpellVolleyTarget`
(`MonsterSpellSupport.h`, on `GameMechanics::projectileFanYawOffsetRadians`, the party's fan) are used by
`IndoorWorldRuntime::applyIndoorActorProjectileRequest` and `OutdoorWorldRuntime::castSpell` (actor casts). This
deliberately changes the seven MM6-MM8 Sparks rows, which fired one spark: 82 Lesser Air Elemental (M: 7), 232 Tempest
(E: 5), 233 Cyclone (M: 7), 234 Air Elemental (G: 9), and as their second spell 409 Titan (M: 7), 410 Storm Titan (M: 7),
411 Blood Titan (G: 9).

**Indoor monster spell damage fixed** (found while doing G3; every world): indoors a monster's spell projectile carried
the AI's fallback damage (monster level, at least 2, plus its damage buffs), which `resolveProjectilePartyImpactDamage`
returns before it rolls the spell, so indoor monster spells ignored their dice and skill (outdoors, `castSpell` carries
no damage and the spell rolls). `applyIndoorActorProjectileRequest` now spawns a spell projectile without damage, so it
rolls `DamageBase + skill x 1..DiceSides` at impact as outdoors (and Paralyze and Fear deal none). Without it the skills
above had no effect on MM9's BLV maps, Fear did the caster's level in damage, and a volley of sparks did the level per
spark. This changes every MM6-MM8 monster spell cast indoors to the spell's own damage, as section 2.1 assumed and as
the originals roll it.

Not done (out of scope, fallbacks as proposed): G2 (Souldrinker and Lifedrain casts: Dragon Breath and Spirit Lash
stand in), G6 (outdoor-only Meteor Shower and Starburst: not used). MM9's condition durations
(Paralyze 1 minute per point) are not reproduced: MM6-MM8 conditions last until cured.

### 6.4 Traps

**The 500-damage shooters are cut-scene cannons, not kill-zones.** None aims at the party:

- Frosgard City: Shooter1-4 (FireBolt 500, ShootInterval 0, no script) are switched on only by `BreakIce.scr`'s
  letterboxed cinema (Camera0-2) to shatter the frozen harbour's ice brushes (`DestructableBrush14-42`), started when the
  powder barrel (DestructableProp0) blows; Shooter7 (500) only by `FrosgardShooter.scr`'s test mode (Shooter5,
  ScriptParams `Test 1`). The 5-damage cannons Shooter0/Shooter5 (`FrosgardShooter.scr`, 0.5 s) aim at random
  `Shoot0-5` / `Test0-5` objects, and Shooter6 (5, every 50 s) is the powder seller's night cannon test (`NPC215.scr`,
  keys 71/72). 500 is MM9's way of making sure a destructible breaks in one shot; it is not a data error. The rework's
  `mm9r_frosgardcity/citylua.py` carries the cinema as scripted floe breaks (no projectile); NPC215's night test is not
  carried (noted in that script).
- Isle of Ashes: Shooter0 (500) fires once in `IsleAshesBook.scr`'s cut-scene at the islet's FortWall0, the bunker's
  Shooter (5) once out through the broken FortWall. The rework carries both (`isleofashes.lua`: `fireShooter`, at the
  wall and along the shooter's aim).

**G5 is already carried by the map converters**, through the existing event missile: every damaging Shooter of the
reworked dungeons (1000 Terrors, Anskram Keep, Chasm of the Dead, Dark Passageway, Dungeon of Secrets, Lich Lab,
Verhoffin Ruins, Isle of Ashes) is fired by its map Lua with
`evt.FireMissile("Fire", from, to, DamageAmt, "Fire", 0, 0, true)` (or the projectile's own missile and damage type) on
its trigger, plate or interval, generated by each map's `convert.py`. That is a single-target fire bolt, as MM9 fires
(answer 7), with MM9's exact `DamageAmt`. The last argument (`strikesParty`) makes the missile strike the party in its
path like a monster's missile; without it an event missile passes the party (the event deals the party's damage
itself), and until 2026-11-11 every MM9 shooter bolt passed the party harmlessly (Chasm of the Dead's HSP6, the user's
playthrough note). Isle of Ashes' two wall-breaking shots, Lich Lab's range and Frosgard City's cinema shots are not
aimed at the party and keep the default.
`evt.CastSpell`/`castSpellFromTo` were not used: an event spell's damage is 2 x skill (`resolveEventProjectileDamage`),
which cannot give MM9's 5-damage bolts, while `evt.FireMissile` carries the damage itself. Lich Lab's three FireBolt
shooters fire at the shooting range's straw targets, and its 0-damage Lightning arcs are `evt.Beam` visuals. Not carried
(no damage, or a cut scene): Wizard's Lab's 0-damage Lightning arcs (ritual visuals), Dark Passageway's YellowLine mirror
beams (a puzzle; its KBYellowLine shooters are carried, 5 Energy damage without the knockback), Frosgard City's cannons
above.

**A shooter object, if ever wanted** (not built: nothing needs it now). A scene `shooters` list written by the converters
from the DAT objects: `{name, at, aim (yaw, pitch) or target point, missile (monster_projectiles token) or spell id with
skill, damage, damage_type, interval_seconds, burst, start_on, path (marker points)}`, owned by the shared event runtime
(both world kinds): `on`/`off`/`go`/`stop` through the map's object messages (the 1000 Terrors dispatcher's `send`),
each shot through the same path as `evt.FireMissile`, its timer on the map's fixed clock, its state (on, next shot,
burst left, marker index) in the map delta, which would need a save version bump. It would replace the per-map Lua
shooter tables and add MM9's travelling shooters (markers), which no converter carries yet.

### 6.5 Checks (2026-11-04)

- Unit tests: `tests/MonsterModifierTests.cpp` (`spell_conditions` / `special_attack_chance` parsing, defaults and errors,
  the combat info, Paralyze/Fear castability and no damage, the Sparks count by mastery and the fan),
  `tests/GameplayRuleRegressionTests.cpp` (each slot's condition on a spell hit, a hit without damage on an
  invulnerable party, a spell hit without the modifier, chance 0, the chance override both ways),
  `tests/GameplayActorAiSystemTests.cpp` (Stone Skin's power), `tools/mm9_import_discovery/test_generate_mm9_monster_tables.py`
  (skills, Sparks masteries, the sorcerers' Fire Bolt, dropped spells, spell conditions). Full suite: all pass but
  the two known unrelated failures ("mm6 Temple of the Fist switch face...", "levitate pressure trap export...").
- Arenas (`tests/scenarios/mm9/ai/`): new `spell_conditions` (a Lich's Fear leaves Afraid, an Oculus's Paralyze leaves
  Paralyzed; health full) and `sparks` (5 sparks at Expert, 9 at Grandmaster); all 30 pass, and the MM8 actor scenarios
  pass except `mm8_right_click_portrait_item` (already failing: the right click is refused).
- **The MM9 arenas run without a party** (none but `spell_conditions`, which starts with `new_game_flow`): no monster
  blow or spell of theirs lands, so their traces never showed damage, conditions or the indoor damage bug above.
- The MM6-MM8 monster table (`assets_dev/engine/data_tables/monster_data.txt`) is byte-identical to HEAD; the Stone
  Skin, Sparks and indoor damage fixes are engine-only.

### 6.6 Spell choice and `concat` as MM9 plays them (2026-11-04)

The user approved redoing the spell choice from the [native RE §7.2.2](monster_ai/MM9_AI_NATIVE_RE.md#722-attack-kind-spell-choice-rangeattack-and-concat)
("MM9 as MM9 plays it"), as one shared, data-driven rule: no world checks in the code.

**Generator** (`generate_mm9_monster_tables.py`: `total_spell_chance`, `sequential_spell_chances`, `cast_spells`,
`NO_RANGE_ATTACK_SOURCES`, `NON_OFFENSIVE_SPELLS`):

- The total spell chance T of a `RangeAttack` is `100 − Att%` when the row has attack 2 (its dice × sides + bonus
  above 0), else 100; 0 when both spells are defense or healing (SPELL.txt `SpellType`: Bless, Heal, Natural Armor).
- With both spells, `SpellUse%1` (S1; `concat` is 0) splits T; a lone spell takes all of T. `SpellUse%2` is not read.
- The table's chances stay sequential, as every world's rows are (spell 1 by its chance, then spell 2 by its own):
  spell1 = T × S1, spell2 = T × (1 − S1) / (1 − T × S1), rounded half up to whole percent (spell 2 against the
  rounded spell 1). A slot whose chance comes out 0 is left empty.
- Rows whose scripts never call `RangeAttack` get no spell: the Astral Icky, the wolves (114-116), the Canopic and
  Embalmed Mummies (144-145) and the Dagrells (148-149).
- No `concat` rider: the special attack is the `Bonus` column's alone, and `ConcatAttk` is not read. Five rows lost
  the on-hit condition the importer made from their `concat` spell: Grey Wolf (Poison1), Red Wolf (Disease2), Black
  Wolf (Paralyze), Canopic Mummy (Disease1), Embalmed Mummy (Disease2). The Bonus-column specials stayed at level ×
  level % (removed in 6.7: MM9 never reads the column).
- `generate_mm9_monster_modifiers.py`: no `special_attack_chance` (it was on 9 rows); `spell_conditions` on 15 rows
  (the Ghast's and Revenant's Fear added); `spell1_recovery`/`spell2_recovery` only for the slots the table casts (the
  Basilisks, Ghoul and Revenant gain one, the Reverend Monk loses both).

**AI** (`mm9RangedAbility`, `GameplayActorAiSystem.cpp`; the pure rule `mm9RangedSpellSlot`, `Mm9ActorRules`): one
seeded roll in [0, 1) casts spell 1 below its chance, else spell 2 by the rest of the roll rescaled against its
chance, else fires attack 1's projectile (a thrower's ranged attack 2), else, with no projectile, a spell as its only
ranged attack. A spell with chance 0 or one it cannot cast now (`monsterSpellIsOkToCast`) counts as chance 0. Before,
it rolled only spell 1 and then fired the projectile, so a row with a projectile never reached spell 2 (the Oculus never
cursed). Only the MM9 loops call it; MM6-MM8 rows keep `chooseAttackAbility`, which reads the same sequential columns.
The Dragon King's attacks are picked by his behaviour script (`self:attack`), so his chances are not used.

**Removed:** the `special_attack_chance` modifier (catalogue, parsing, `GameplayCombatActorInfo::specialAttackChancePercent`,
its tests and docs); the generator's `condition_for_concat_spell` and `NEVER_CAST_SPELLS`. `spell_conditions` stays:
15 rows cast Curse, Dark Grasp, Fear or Paralyze, and the condition is the spell's own effect.

| Row | Monster | `Att%` / attack 2 | `SpellUse%1` | T | Table spell 1 / 2 (was) | Per shot: spell 1 / spell 2 % |
|---|---|---|---|---|---|---|
| 75-77 | Dragonflies | 50 / yes | 100 | 50 | 50 / — (100 / —) | 50 / 0 |
| 86 | Lobber | 0 / yes | 0 | 100 | 100 / — (0 / —) | 100 / 0 |
| 89 | Astral Icky | — | 100 | 0 | — (—) | no `RangeAttack` |
| 97, 98 | Troglodyte Wren, Gnoll | 50 / yes | 100 | 50 | 50 / — (100 / —) | 50 / 0 |
| 106 | Ice Lobber | 50 / yes | 100 | 50 | 50 / — (100 / —) | 50 / 0 |
| 114-116, 144-145, 148-149 | wolves, Canopic and Embalmed Mummies, Dagrells | — | `concat` | 0 | — (—, the rider dropped where it was the importer's) | no `RangeAttack` |
| 123 | Initiate | 0 / no | 100 | 100 | 100 / — (=) | 100 / 0 |
| 124 | Monk | 0 / no | 95 | 100 | 95 / 100 (95 / 5) | 95 / 5 |
| 125 | Reverend Monk | 0 / no | 85 | 0 (Natural Armor and Heal) | — / — (85 / 15) | never |
| 140 | Specter | 0 / yes | 100 | 100 | 100 / — (=) | 100 / 0 |
| 146 | Petrified Mummy | 0 / yes | 95 | 100 | 95 / 100 (95 / 5) | 95 / 5 |
| 150-152 | Basilisks | 50 / yes | `concat` | 50 | 50 / — (— / —): Poison Spray N2, N7, E17 | 50 / 0 |
| 156, 157 | Evil Apprentice, Sorcerer | 0 / yes | 100 | 100 | 100 / — (=) | 100 / 0 |
| 158 | Evil Grand Sorcerer | 0 / yes | 80 | 100 | 80 / 100 (80 / 20) | 80 / 20 |
| 159-161 | Winged monsters | 0 / yes | 50 | 100 | 50 / 100 (50 / 50) | 50 / 50 |
| 162-164 | Fright, Dread, Terror | 0 / yes | 100 | 100 | 100 / — (=) | 100 / 0 |
| 174 | Ghast | 0 / yes | `concat` | 100 | 100 / — (— / —): Fear N2, leaves Afraid | 100 / 0 |
| 175 | Ghoul | 0 / yes | `concat` | 100 | — / 100 (— / —): Toxic Cloud E1 | 0 / 100 |
| 176 | Revenant | 0 / yes | `concat` | 100 | 100 / — (— / —): Fear M10, leaves Afraid | 100 / 0 |
| 181 | Dripper | 100 / yes | `concat` | 0 | — (—) | never |
| 182 | Zombie | 0 / yes | 10 | 100 | 10 / 100 (10 / 90) | 10 / 90 |
| 186, 216 | Honk | 75 / yes | 0 | 25 | 25 / — (0 / —) | 25 / 0 |
| 195 | Bloodsucker | 0 / yes | 100 | 100 | 100 / — (=) | 100 / 0 |
| 196 | Annelid | 0 / yes | 50 | 100 | 50 / 100 (50 / 50) | 50 / 50 |
| 197 | Vampir | 0 / yes | 45 | 100 | 45 / 100 (45 / 55) | 45 / 55 |
| 207 | Lich | 0 / yes | 100 | 100 | 100 / — (=) | 100 / 0 |
| 208 | Power Lich | 0 / yes | 85 | 100 | 100 / — (85 / —) | 100 / 0 |
| 209 | Lich King | 0 / yes | 50 | 100 | 50 / 100 (50 / 50) | 50 / 50 |
| 212 | Dragon King | 50 / yes | 90 | 50 | 45 / 9 (90 / 10) | his script picks |
| 228, 229 | Eye, Orbus | 50 / yes | 100 | 50 | 50 / — (100 / —) | 50 / 0 |
| 230 | Oculus | 50 / yes | 25 | 50 | 13 / 43 (25 / 75) | 13 / 37.4 |
| 261 | Njam the Meddler | 15 / yes | 20 | 85 | 17 / 82 (20 / 20) | 17 / 68.1 |
| 301 | Ebora | 0 / no | 60 | 100 | 60 / 100 (60 / 40) | 60 / 40 |
| 302 | Concubine | 0 / no | 50 | 100 | 50 / 100 (50 / 50) | 50 / 50 |

"Was" is the earlier table. The earlier AI cast spell 2 only when spell 1 could not be cast (a row with a projectile
fired it instead, a row without one fell back to spell 1), so in play the difference is larger than the columns show
(the Oculus: no Curse at all).

Not MM9 (resolved in 6.7): the placed Ghast and Revenant run `KingKong.scr` (BaseMelee without Range.inc, no
`RangeAttack`) in MM9, so they never cast there; the profile followed the row's default script (`baserange.scr`) and
cast. The Lobber's 100 % Poison Spray follows the rule (confirmed by the native RE §7.2.3: the Lobber routes its shot
like AIBase). The `Bonus` column was not read by MM9 either; its specials were kept until 6.7.

Checks (2026-11-04): unit tests `tests/Mm9ActorRulesTests.cpp` ("MM9 RangeAttack casts by the sequential spell
chances", "MM9 ranged walker with a projectile casts both its spells": 400 seeded shot checks of an Oculus),
`tools/mm9_import_discovery/test_generate_mm9_monster_tables.py` (T, the split, the sequential formula over all T and
S1, two non-offensive spells, `concat` rows with and without `RangeAttack`, the Dripper, the Ghoul); the full unit suite
passes but the four known unrelated failures. The `spell_conditions` arena now runs 120 s and asserts the Oculus casts
both spells, Curse more often than Paralyze, and fires its BlueLine (Afraid, Paralyzed and Cursed all left). Oculus
casts over 240 s in that arena: before 44 BlueLine, 9 Paralyze, 0 Curse; after 19 BlueLine, 3 Paralyze, 28 Curse
(over 900 s: 101, 20, 76, that is 51 %, 10 %, 39 % of its shots against MM9's 50, 12.5, 37.5). Re-tuned: `lobber`
(its shot is now its Poison cast) and `dragon_king` (the Winged Mutant's second spell shifted the fight; the mutant now
dies at 24 s as the party steps close, so the breath and wing still come). All 31 arenas and the MM8 actor scenarios
pass but `mm8_right_click_portrait_item` (already failing). The MM6-MM8 monster tables are byte-identical to HEAD.

### 6.7 No `Bonus` specials, blows in reach and placement scripts (2026-11-04)

Approved follow-ups to 6.6, from the native RE (§7.2.2: nothing reads the `Bonus` column; §7.2.3: in reach `Attack` is
always a blow), one shared rule each, driven by data.

**No `Bonus` specials.** `generate_mm9_monster_tables.py` writes no special attack for any MM9 row (the `SPECIAL_ATTACKS`
map and `special_attack` are gone): MM9 loads `Bonus` and never reads it, `ConcatAttk` is never read, and no spell or
condition rides on a hit. 60 rows lost an on-hit special that rolled at level × level %:

| Special | Rows |
| --- | --- |
| Poison1-3, Poison3x2 | Nagate Hatchling, Nagate, Nagate Elder; Lobber, Ice Lobbercicle, Ice Lobber; Troglodyte Gnoll; Basilisk (Poison2), Fibrase Basilisk (Poison3), King Basilisk (Poison3x2) |
| Disease1-3 | Airborne, Flying and Astral Icky; Field Thrall, Thrall, Thrall Master; Ghast (Disease1); Rotter, Dripper (Disease3), Bloodsucker |
| Paralyze, Paralyzex1 (Stun) | Ghoul, Revenant, Desert Terror, Reptilian Terror; Bigfoot, Sasquatch, Yeti |
| Afraid | Skeleton Warrior, Shadow, Yanmir, Orbus, Amphibious Terror |
| Curse, Cursex2, Insane, Asleep, Agex2, Uncon, Dead, Drunk, DrainSP | Skeleton Master; Imp; Lich King, Oculus, Colloidal Warrior; Eye; Apparition; Specter; Colloidal Guardian; Imply; Zombie, Annelid, Vampir |
| BrkArmor, BrkWeapon, BrkItem, BrkItemx1-2 (Steal) | Dwarven Commander, Venomous Dagrell, Winged Aberration, Gezzamptling, Gezzampt, Gezzampt Elder, Dragon King; Town Guard, Guard Captain, Dagrell; Spectre Dagrell, Lizard-Orc Mage; Cutpurse, Burglar, Bandit |

Only column 17 of `worlds/mm9/data_tables/monster_data.txt` changed (every MM9 row now `0`); the descriptors and the
conversion audit are unchanged. The spells MM9 casts and their `spell_conditions` stay (15 rows).

**Blows in reach** (`mm9BlowOrShot`, `GameplayActorAiSystem.cpp`). A monster in reach always strikes its blow: `CanAttack`'s
`Att%` roll only sets a kind `Attack` ignores, whatever its script (EvilSorcerer.scr calls no `RangeAttack` of its
own; only Range.inc's out-of-reach shot check, FlyRange.inc, lobber.scr and IsleOfAshesActor.scr's set piece call it).
Only a monster holding a ranged weapon prop (profile `ranged_weapon`, from a script's `AttachProp` of a `WEAPON.txt`
ranged weapon) turns `Attack` into `RangeAttack`; no MM9 row or placement holds one. `Att%` is rolled once per action
and only matters for shots (the sequential chances of 6.6, unchanged). A row with attack 1 alone fires no shot (none in
MM9). So the Oculus strikes in reach and shoots or casts only at its shot checks, the Evil Apprentice strikes a party in
its reach, and fliers strike in their passes (the plan's phase 3 open question). The Lobber Pods and the Ice
Lobbercicle lost their projectiles in the table (`MELEE_ONLY_SOURCES`: lobberpod.scr never enables its range attack)
and evade for a seeded 1.8-2.2 s after every attack (profile `evade_min_seconds`/`evade_max_seconds`). A Lobber's pod
launch arms its recovery like a released shot; it launches whenever its attack is ready and fewer than five pods live
(no 5-10 s spacing, as phase 3 already did).

**The placement's script decides** (`devdocs/mm9_rework/monster_ai/PROFILE.md` "Placement scripts"). A placement whose
`ScriptName` has no Range.inc never shoots or casts, whatever its row's script: the placed Ghast and Revenant
(KingKong.scr, Lich Lab), 19 Petrified Mummies (MummyAwaken.scr), Dook's guards, the concubines, Njam's chase and others
(70 placements, `profile: {ranged: none}`); 33 placements gain Range.inc and cast (the monks once hostile, Tasar's
students and teacher). The spell columns stay the row's: a placement without Range.inc simply never reaches them.

Checks: unit tests (`tests/Mm9ActorRulesTests.cpp` "MM9 monster in reach always strikes its blow...", "MM9 walker with
attack 1 alone never shoots", "MM9 placement script with no AI keeps its monster passive"; `tests/Mm9MonsterAiTests.cpp`;
`tools/mm9_import_discovery/test_generate_mm9_monster_tables.py`, `test_mm9_ai_placement.py`); arena
`placement_script` (a KingKong Ghast never casts, a row-script Ghast does); `holder`, `ranged`, `spell_conditions` and
`dragon_king` re-tuned (tests/scenarios/mm9/ai/README.md).
