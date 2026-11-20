# MM9 monster AI: what the data and the scripts say

Status (2026-11-04): research only. Nothing in the engine or assets was changed for this document.

This is a taxonomy of Might and Magic IX monster AI built from MM9's own data (`MONSTERS.txt`, the placed objects in
the world DATs) and its JSL scripts. Its purpose is to decide how OpenYAMM implements MM9 monster AI: a native base
AI with a few archetypes, plus optional cheap per-monster Lua extensions.

Paths are relative to the repository root. Scripts live in `mm9/extracted/SCRIPTS/SCRIPTS/` and are cited as
`FILE:line`. Line numbers count the file's own lines (the files have CRLF endings).

Related records: [MM9 animation blending RE](../MM9_ACTOR_ANIMATION_BLENDING_RE.md) (the BaseMelee footwork in
detail, already implemented as the `skirmisher` modifier, see [Monster modifiers](../../MONSTER_MODIFIERS.md)),
[monster jumps and rails](../MM9_MONSTER_JUMP_RE.md), [water and swimming](../MM9_WATER_SWIMMING_RE.md) section 6,
[collision](../MM9_MONSTER_COLLISION_RE.md), [actor scripting](../../ACTOR_SCRIPTING_INVESTIGATION.md).

## Summary

- `MONSTERS.txt` has 283 data rows. 135 are monsters (`IsMonster 1`, plus the Magic Mine), 148 are not:
  86 `NPCbase.scr` townsfolk, 36 named characters, guards and hireable heroes with `IsMonster 0`, 13 animals and
  13 empty placeholder rows.
- **Every mobile monster melees.** No row is "ranged only" or "caster only"; shooting and casting are add-ons to a
  chasing melee loop. The only non-melee monsters are three turrets (two Lobbers, the Magic Mine) and the Dragon King.
- Of the 135 monster rows, **104 (77 %) use a pure shared base script** with no code of their own. About 25 more
  use a thin wrapper that changes one flag or adds one hook. **Six rows** (Dragon King, Yanmir, the two Lobbers,
  the Magic Mine and, arguably, the Banshee family's undead phase) have behaviour that is genuinely their own.
- Of 1 625 placed monsters in the 45 shipped world DATs, **1 262 (78 %) run their default script**. The 363
  overrides are mostly reusable encounter patterns (dormant until triggered, patrol paths, hostility gates,
  summoners); only 13 placements run unique boss logic.
- MM9 really has **seven AI archetypes** (crawler, skirmisher, ranged holder, air flier, swimmer, turret, civilian)
  plus two add-ons (ranged/caster shots for walkers and for fliers) and a set of shared layers (wander/patrol,
  flee/cower, doors, alerts, resurrection). See [Conclusion](#5-conclusion).

## How MM9 monster AI is built

The engine (`object.lto`) owns perception, pathing (AI rails), movement, animation, damage and which attack or
spell a monster uses. A JSL script per actor drives the decisions through commands and callbacks (manual:
`mm9/mm9_tools/script.txt`; AI commands at lines 1170–2160). Key points:

- An actor runs `MONSTERS.txt` `ScriptName` unless the placed object (or a spawn string) sets its own `ScriptName`
  and `ScriptParams` (`p0..pN`, read with `GetParam`).
- Scripts are event driven: `OnFoundTarget`, `OnDamage`/`OnDamageDone`, `OnAlert`, `OnHelp`, `OnProjectile`,
  `OnLostTarget`, `OnTargetDead`, `OnDeath`/`OnDeathDone`, `OnFear`/`OnEnrage`, `OnDoor`, `OnObstacle`, and timers
  (`Wait <slot>, <seconds>, <routine>`; slots are listed in `BASETIMERS.inc:14-27`).
- Includes form an inheritance chain. A routine defined again in a later include overrides the earlier one, and
  `gosub Name,1` (or `,2`) calls the version one (or two) levels up. So `baserange.scr` is
  `BaseCrawl.inc` → `BaseMelee.inc` → `Range.inc`, each refining the previous.
- The script never chooses between projectile 1, projectile 2 or a spell. It calls `Attack` (melee) or
  `RangeAttack` (shoot or cast, "whatever range attack he has", `script.txt:1355-1364`); the engine picks the
  concrete attack from the row's attack and spell columns. `CastSpell` is used by only six scripts, all scripted
  set pieces (for example `WIZARDSUMMONER.scr`), not by any base.

### The dependency tree of the bases

```
AICommon.inc (alerts, resurrection, hate/enrage triggers)
├── BaseCrawl.inc (+ BaseWander, BaseRun, BaseDoor, SpeedThrottle, BaseEvade)  "crawler"
│   ├── BaseMelee.inc (strafe attack, evade, taunt)                            "skirmisher"
│   │   ├── + Range.inc  → baserange.scr, ghost.scr, LesserDemon, GreaterDemon, EvilSorcerer (Type 2)
│   │   └── PoliceMan.inc → policeman.scr; Basemelee.scr → GuardBase.scr, MonkBase.scr
│   ├── + Range.inc → crawlrange.scr, titan.scr, YanmirBase.scr, lobberpod.scr (range disabled)
│   └── BaseSwim.inc → BaseSwim.scr
└── BaseFly.inc (+ BaseWander, BaseEvade)                                       "air flier"
    ├── FlyRange.inc → flyrange.scr, Banshee.scr
    └── FlyingIcky.scr
NPCBase.inc (BaseWander + BaseRun, chat, RUDE dialogue)                        "civilian"
FarmAnimal.inc / wander.inc (animals); lobber.scr, dragon.scr (stand-alone)
```

`BASE.inc` (1 321 lines), `OLDBASE.inc`, `NEWBASE.inc` and `AGGRESIVE1.inc` are older bases. Only `rooster.scr`,
`base2.scr` and the unused `DRAGONAZURE.scr` still use them; `BASEMELEE.inc:15` says "Base.Inc should be phased out
as soon as possible".

## 1. Column semantics

### Which columns the AI module reads

The `object.lto` loader for `data\monsters.txt` (disassembly in `re_mm8/work/mm9_water/montxt.txt`) reads cells by
their spreadsheet column letter: it pushes the letters `A`, `B`, ... `CA` as strings (`object.lto` `0x101a21b0`–
`0x101a2294`). Mapping the pushed letters to the header gives the columns the server-side AI and actor code reads:

| Read by `object.lto` | Not read by `object.lto` |
|---|---|
| Number, names, models, skins (A–F), LVL, HP, AC, EXP, SPD, TreasureType, WalkVelocity, RunVelocity, FlyVelocity, LungeVelocity, AttackReach, AttackRange, Recovery, Bonus, AlertRadius, Accuracy, Type1 + dice + Projectile1 + Att% (col 33), Type2 + dice, Type3 + dice + the second `Projectile2` (col 66), SpellUse%1, Spl1, Spl2, Always Wince?, WinceThreshold, WinceTrackTime, five resistances, ScriptName, FootSound, FootRadius, Transparent, HeadTurn, Scale, Evade Chance, Strafe Attack Pct, IsMonster, Treasure Level, BaseName, Resurrect, FX0–FX2, ResurrectFX, Voice Radius | Type/Picture, Quest, **Fly**, **Move**, **Target Pref**, Damage1/2/3 text (the dice columns are read instead), the first **Projectile2** (col 39), **SpellUse%2**, **Special**, **ConcatAttk**, **Hostility Group**, the second **Att%** (col 67) |

`cshell.dll` also references `data\monsters.txt`; the columns missing above are presumably read there (the party
combat rules), but that is not verified. Two consequences are certain:

- The first `Projectile2` column is dead data for the AI. The Horde's `FireAr`, the Birds' `Air`/`Fire`, the
  Astral Icky's `Fire`, the Lizard-Orcs' `Earth` and the hireable heroes' `arrow` are never thrown. This matches the
  importer's existing note that the Horde never throws (`tools/mm9_import_discovery/generate_mm9_monster_tables.py`
  `MELEE_ONLY_SOURCES`).
- `Fly` and `Move` do not steer the server AI. Flight comes from the actor class and script (`BaseFly.inc`, the
  `AISwimFly` swimmers) and the velocities. The Banshees have `Fly 0` yet fly through `FlyRange.inc`; the
  Jellyspores have `Fly 1` yet swim.

### AI-relevant columns

Confidence: **High** = read by a script through `GetStat` or by RE; **Med** = consistent with every row and a named
engine stat; **Low** = inferred from values only.

| Column | Meaning | Values in data | Confidence |
|---|---|---|---|
| Fly | Designer tag "can fly". Not read by the AI loader (see above). | 1 on 22 rows | Med |
| Move | Not read by the AI loader. Rises with tier inside families (Colloidal 5/6/7, Jellyspore 5/6/7) and is 0 on every named NPC, animal and turret, so it reads like an MM8-style range class (stationary … free). The OpenYAMM importer maps it to MM8 wander classes (`MOVEMENT_TYPES`) for the MM8 idle only; Move 0 with a velocity is Short, and only a row with no velocity is Stationary (2026-11-06). | 0, 2–8 | Low |
| WalkVelocity / RunVelocity / FlyVelocity | Engine stats `WalkVel`, `RunVel`, `FlyVel`; the scripts read them (`BASECRAWL.inc:1268-1269`, `BASEFLY.inc:836-838`) and throttle them during attacks (`SPEEDTHROTTLE.inc:38-135`). All zero = turret. | run 75–450, fly 0–500 | High |
| LungeVelocity | Speed of the forward impulse from the animation's `lunge` key (record `+0x64` × 2 × the key's factor); on blending models only the `Lunging` flag, which makes SpeedThrottle run 1.25× (`SPEEDTHROTTLE.inc:58-62`; animation RE). | 0–350, mostly 100 | High |
| AttackRange | Stat `AttackRange`: the edge-to-edge distance (`AIGetDistance` subtracts both radii) inside which a walker counts as "in melee range" and attacks (`BASECRAWL.inc:444-450`). Chase stop distance is 0.95× and "keep running after a moving target" 0.70× of it (`BASECRAWL.inc:1272-1273`). | 60 typical; 125–130 Terrors, Sea Monsters, Wolves; 160 Giants, Evil Sorcerers; 200 Winged Mutants; 250 Dragon King | High |
| AttackReach | Read by the loader, not by any script. Probably the reach of the blow itself (36 typical; 0 on the Lobbers, which never melee; 100 on Terrors, 150 on the Dragon King). | 0–150 | Low |
| Recovery | Time between attacks; scripts see it as `RecoveryTime`/`RecoveryTimeLeft` and `CanAttack`. The importer treats it as tenths of a second. | 30 on 120 monsters, 40 on 14 | High |
| AlertRadius | Most likely the radius of `SendAlert`/`Help` (the alert tick re-broadcasts the target to friends, `AICOMMON.inc:41-51`). 1600 for Noblemen, Evil Sorcerers and Winged Mutants. Sight and hearing are separate placed properties. | 1200, 1600 | Med |
| Type1, dice, Projectile1 | Attack 1. Its damage is used for melee; `Projectile1` is what `RangeAttack` throws (Axe, Knife, Stone, Goo, bolts) or `Spell` (= the ranged attack is the spell). | | Med |
| Att% (col 33) | **Resolved in phase 2** ([plan](../MM9_MONSTER_AI_PLAN.md) "Phase 2"): the chance (d100 at most the value) that a monster with a blow and a ranged attack or spell both at hand strikes in reach (object.lto `0x100b577d`, character `+0x200`). Earlier reading: unresolved. Pure throwers have 100 (Imps, Thralls, Dwarves, Half-Orcs, Bigfoot); rows that also cast have 50 (Dragonflies, Troglodyte Wren/Gnoll, Eye/Orbus/Oculus, Ice Lobber, Dragon King); Honks 75; Njam 15; but Gezzampts and Colloidals shoot with 0. Read as "chance a range attack uses Projectile1 rather than the spell", the 0s contradict it; read as MM8's "chance of attack 2" (as `generate_mm9_monster_tables.py` does), the 100s on pure throwers contradict it. The record field is at `+0x620` (`montxt.txt:616-627`); its consumer was not traced. | 0, 15, 50, 75, 100 | Low |
| Type2/Type3, dice | Attacks 2 and 3. Attack 3's projectile is the second `Projectile2` column (only the Dragon King: `DragonBreath2`). | | Med |
| SpellUse%1 / Spl1 / SpellUse%2 / Spl2 | Spells as `id,mastery,skill`. `SpellUse%1` is a percentage or the word `concat`; only `SpellUse%1` is read by the AI loader. `concat` (wolves, mummies, dagrells, basilisks, ghouls, Dripper, Zombie) chains the spell into a melee hit as an on-hit effect instead of casting it. | 0–100, `concat` | Med |
| ConcatAttk | Probably the chance (%) that a `concat` spell lands with a hit (10–25 on some concat rows, 0 on others). Not read by the AI loader. | 0, 10, 15, 20, 25 | Low |
| Target Pref | Which party member the monster prefers. Letter codes (`CP`, `XE`, `H`, `M`, `S`, `E`, `G`, `AR`, `DR`, `P`, `W`, `D`, `OC`, `DC`, `SD`, `X`) and digits (2, 3, 4). Plausibly race/class/gender initials, but not decoded; not read by the AI loader, so it affects only which character is hit, not movement. | 0 on 199 rows | Low |
| Always Wince? / WinceThreshold / WinceTrackTime | Native hit reaction. Probably: always wince on a hit when 1; otherwise wince when the damage tracked over `WinceTrackTime` seconds reaches `WinceThreshold` (% of HP?). The scripts only receive `OnDamageDone` after the wince (`script.txt:1693-1700`). Turrets, swimmers and big monsters have 0. | 1 on 162 rows; threshold 0/40; track 0/0.5 | Low |
| ScriptName | Default AI script (see section 3). Placed objects and spawn strings override it. | 38 scripts | High |
| HeadTurn | Stat `CanHeadTurn` (`BASEMELEE.inc:270`): the head tracks the target. 0 on non-humanoids. | 0/1 | High |
| Special | Only the evil mouse has 1. Not read by the AI loader. | | Low |
| Evade Chance | Stat `EvadeChance`: chance (%) to evade after a melee attack, BaseMelee only (`BASEMELEE.inc:124-145`). | 40 on every row | High |
| Strafe Attack Pct | Stat `StrafeAttackPct`: chance (%) of a strafe attack, BaseMelee only (`BASEMELEE.inc:89-121`). | 80 mostly; 95 Terrors; 60 Troglodytes; 40 Banshees; 30 Half-Orcs; 20 Imps, Thralls, Town Guards; 100 Lobber Pods; 0 Nagates, Birds, bandits, Lobbers, Dagrells | High |
| IsMonster | Stat `IsMonster`. Guards ignore alerts from monsters (`POLICEMAN.inc:50-56`); separates monsters from NPCs in the data. | 0/1 | High |
| Hostility Group | Faction number, not read by the AI loader: 1 town/friendly (peasants, monks, guards, Thralls, Honks, noblemen), 2 animals and wolves/birds, 3 dwarves and Dook militia, 4 vermin (imps, nagates, dragonflies, ickies, troglodytes, lobbers, sea monsters), 5 bandits, Horde, Evil Sorcerers, 6 undead, 7 everything else. AI friend/enemy lists are otherwise set by class name in scripts (`AddEnemy`/`AddFriend`). | 1–7 | Med |
| Resurrect | Stat `IsResurrecter`: the monster raises dead friends (`AICOMMON.inc:509-530`). 1 on Skeleton Master, Petrified Mummy, Evil Sorcerers, Terror (Banshee), Revenant, Zombie, Skeletoid, Bone Thrasher, Skull Thrower, Annelid, Vampir, Power Lich, Lich King. Being raisable is the placed property `CanBeResurrected` plus a `Resurrect` animation (`AICOMMON.inc:62-81`). | 1 on 16 rows | High |
| ResurrectFX, FX0–FX2 | Client effects: `ResurrectFX` `GreaterDemon` on the raisable undead; FX0–2 (`bluedots`, `redyeldots`, `greenyeldots`) on casters, probably cast sparkles. | | Low |

### Placed-object properties that matter as much as the table

Read from all 45 `mm9/extracted/WORLDS/WORLDS/*.dat` (2 217 placed AI actors; scan with
`tools/mm9_import_discovery/transcode_mm9_dat_to_odm.read_dat_world`):

| Property | Meaning | Values |
|---|---|---|
| `SightDistance`, `HearingDistance` | Vision and hearing (stats `VisibleRange`, `HearingRange`); both double the first time the party is targeted (`BASECRAWL.inc:692-709`). | sight 600 (749), 1320 (565), 1800 (319), …; hearing 360, 144, 1200, … |
| `RunawayChance` | Input to the native `ShouldRunAway` (flee decision). | 0.25 on 1 783, 0.05 on 256, 0 on 96, 1.0 on 2 |
| `RangeAttackType` | 1 = chase and shoot (Type 1), 2 = hold position and shoot (Type 2) (`RANGE.inc:6-22`). | 1 on 2 184, 2 on 33 |
| `WanderON`, `WanderPathName`, `WanderPathRandom`, `WanderLeash`, `WanderWaitMin/Max`, `WanderTimeMin/Max` | Idle wander or marker patrol (`BASEWANDER.inc:645-699`). | WanderON 1 on 265; 97 with a path |
| `CanBeResurrected` | May be raised by a resurrecter. | 1 on 959 |
| `UsesRails`, `CanReachAll`, `CheckForAIBarrier`, `TerrainMode` | Navigation, see the jump and rail RE. | |
| `DeathTriggerTarget/Message`, `DamageTriggerTarget/Message` | Fire a trigger on death or damage (doors, quests). | 56 death, 5 damage triggers |
| `HidingPlace0-2`, `HidingPlaces` | Flee targets; `HidingPlaces` is 0 everywhere. | |
| `AutoDeactivate`, `FadeOnDeath`, `BuryOnDeath`, `ShouldRepopulate`, `GiveTreasure` | Lifecycle. | |

## 2. Classification of every row

### Non-monster buckets (148 rows)

| Bucket | Rows | Scripts |
|---|---|---|
| Placeholder rows (no name, no script) | 13: 193, 194, 218–226, 240, 243 | — |
| Townsfolk (`NPCbase.scr`) | 86: Commoner, Town, Shopkeeper, Prisoner and Child variants of every race (1–74) plus named story NPCs 246–258 (Bjarni, Sigmund, Markel, Sven, Tryggva, Kira, Ivsar, Yrsa, Krohn, Fre, Skraelos, Bori) | `NPCbase.scr` |
| Animals (`Hostility 2`, `IsMonster 0`) | 13: Cow, Brown Cow, Goat, Hen, Rooster, Pig, Ewe, Ram, Goose, cat, dog, mouse, evil mouse | `cow`, `goat`, `hen`, `rooster`, `pig`, `duck`, `cat`, `dog` scripts; `basecrawl.scr` for sheep |
| Named characters, guards, heroes (`IsMonster 0`) | 36: Town Guard ×4 (`policeman.scr`), Clan Soldier/Corporal/Sergeant, Fish, Old Hag, Forad Darre, Ratatosk, Hanndl, The Great Honk, the three Wyrdes, Green Man, Scholar, Master Scholar, the 14 hireable heroes (279–292: Hrolf … Tamur Leng), RailTest, Huber Carryall, Phantom Fighter | mostly `basemelee.scr`; `baserange.scr` for the two caster heroes |

### Monster matrix (135 rows)

Rules: **movement** from the default script and velocities (swimmer = `BaseSwim`; turret = all velocities 0 or a
script that never moves; air flier = a `BaseFly` script; hover flier = `Fly 1` with a walker script; else ground).
**Melee** = the script calls `Attack`. **Ranged** = a real projectile in `Projectile1` (or col 66) and a script
with a `RangeAttack` path. **Caster** = a non-`concat` spell with a chance above 0 and a `RangeAttack` path.
`concat` spells count as melee riders.

| Movement \ Attack | Melee only | Melee + ranged | Melee + caster | Melee + ranged + caster | Special | Total |
|---|---|---|---|---|---|---|
| Ground walker | 37 | 51 | 10 | 3 | 1 | **102** |
| Flier, air combat (`BaseFly`) | 6 | 0 | 6 | 3 | 0 | **15** |
| Flier, hovering on walker logic | 2 | 0 | 1 | 3 | 0 | **6** |
| Stationary / turret | 0 | 0 | 3 | 0 | 4 | **7** |
| Swimmer | 5 | 0 | 0 | 0 | 0 | **5** |
| **Total** | **50** | **51** | **20** | **9** | **5** | **135** |

No row is ranged only, caster only or ranged + caster without melee.

#### Families per cell

| Cell | Rows | Families (row numbers) and default scripts |
|---|---|---|
| Ground, melee only | 37 | Nagate Hatchling, Nagate (81–82, `basecrawl`); Lobber Pod ×2 and Ice Lobbercicle (84, 85, 105, `lobberpod`: its range attack is switched off, `LOBBERPOD.scr:150-158`); Guard ×3 (111–113, `Guardbase`); Grey/Red/Black Wolf (114–116, `basecrawl`, concat poison/disease/paralyse bite); Initiate, Monk, Reverend Monk (123–125, `MonkBase`: spells in the data but no `RangeAttack` path unless the placed `monkguardbasic.scr` turns them hostile, which also runs `RangeInit`, `MONKHOSTILITY.inc:33-42`); Horde Grunt/Warrior/Leader (129–131, `basemelee`, axes and fire arrows in the data never used); Canopic and Embalmed Mummy (144–145, `basecrawl`, concat disease); Dagrell ×3 (147 `basemelee`, 148–149 `dagrell`, concat fear/paralyse); Baron, Viscount, Count (153–155, `basemelee`); Ghast, Ghoul, Revenant (174–176, `baserange` with nothing to shoot, concat fear/paralyse); Skeletoid, Bone Thrasher (183–184, `basemelee`); Amphibious/Desert/Reptilian Terror (237–239, `basemelee`); MagreebBaby, Magreeb Spawn, Magreeb, Armored Magreeb (244, 276–278, `Magreeb`) |
| Ground, melee + ranged | 51 | Imply, Imp, Imp Elder (78–80, axes); Nagate Elder (83, `crawlrange`); Field Thrall, Thrall, Thrall Master (90–92, knives); Troglodyte (96); Cutpurse, Burglar, Bandit (99–101); Half-Orc Recruit/Soldier/Captain (102–104); Dwarven Guard/Soldier/Commander (120–122); Skeleton, Skeleton Warrior, Skeleton Master, Skull Thrower, Skeleton (135–137, 185, 192); Basilisk ×3 (150–152, `crawlrange`, also concat poison); Trellborg ×3 (165–167); Gezzamptling, Gezzampt, Gezzampt Elder (171–173, lightning, Att% 0); Rotter, Dripper (180–181, goo); Honk ×5 (186–188, 216–217, eggs); Lizard-Orc ×3 (189–191); Bigfoot, Sasquatch, Yeti (198–200, stones); Plain and Forest Giant (204–205, `titan`); Colloidal Soldier/Warrior/Guardian (234–236, goo, Att% 0); Lesser Demon, Greater Demon (241–242). All `baserange` unless named. |
| Ground, melee + caster | 10 | Petrified Mummy (146: Curse, Paralyse); Zombie (182: Spell Reaver, Wound); Bloodsucker, Annelid, Vampir (195–197: Wound, Dark Grasp, Souldrinker); Lich, Power Lich, Lich King (207–209: Fear, Curse, Dark Grasp); Ebora, Concubine (301–302: Column of Fire / Sparks). All `baserange`. |
| Ground, melee + ranged + caster | 3 | Troglodyte Wren and Gnoll (97–98: GreenThingy + Poison/Disease); Njam the Meddler (261: RedYellowThingy + two GM spells). `baserange`. |
| Ground, special | 1 | Yanmir (206, `YanmirBase`): boss, see section 4. |
| Air flier, melee only | 6 | Airborne, Flying, Astral Icky (87–89, `FlyingIcky`; the Astral Icky's poison spell and fire projectile are unused); Bird ×3 (93–95, `basefly`; their Air/Fire projectiles are in the unread column). |
| Air flier, melee + caster | 6 | Winged Oddity/Mutant/Aberration (159–161, `flyrange`: Sparks 50 %, Elemental Bolt); Fright, Dread, Terror (162–164, `Banshee`: Fear 100 %). |
| Air flier, melee + ranged + caster | 3 | Dragonfly Mite, Dragonfly, Fire Dragonfly (75–77, `flyrange`: coloured "thingy" bolts + Elemental Bolt). |
| Hover flier, melee only | 2 | Shadow, Apparition (138–139, `ghost` = BaseMelee + Range with nothing to shoot). |
| Hover flier, melee + caster | 1 | Specter (140, `ghost`, Dark Grasp). |
| Hover flier, melee + ranged + caster | 3 | Eye, Orbus, Oculus (228–230, `baserange`, `Fly 1`, run velocity 0, fly velocity 250: beholders run the walker loop while hovering). |
| Turret, melee + caster | 3 | Evil Apprentice, Evil Sorcerer, Evil Grand Sorcerer (156–158, `EvilSorcerer`: range Type 2, never chases, melees only what walks into reach). |
| Turret, special | 4 | Lobber, Ice Lobber (86, 106, `lobber`: rooted, shoots and launches Lobber Pods); Magic Mine (179, `MagicMine.scr`, which is **missing** from the extracted scripts and is placed nowhere); Dragon King (212, `dragon`: boss, never moves after landing). |
| Swimmer, melee only | 5 | Jellyspore, Gelatinous Spore, Nettle Spore (168–170); Sea Monster Male/Female (177–178). `BaseSwim`. |

#### Placed counts per default script

Placed monsters in the shipped DATs, by their row's default script (overridden or not): `baserange` 853,
`basecrawl` 115, `flyrange` 109, `basemelee` 106, `FlyingIcky` 71, `Guardbase` 58, `ghost` 46, `EvilSorcerer` 42,
`BaseSwim` 39, `crawlrange` 36, `lobber` 30, `MonkBase` 30, `dagrell` 19, `Magreeb` 18, `LesserDemon` 16,
`Banshee` 15, `lobberpod` 14, `titan` 4, `GreaterDemon` 2, `dragon` 1, `YanmirBase` 1. More than half of all placed
monsters run `baserange.scr`.

## 3. The base scripts as state machines

All walker bases share the crawler loop; the skirmisher, ranged and swimmer variants override single states.
Numbers are seconds and world units (MM9 units; distances from `AIGetDistance` are edge to edge).

### 3.1 Crawler: `BaseCrawl.inc` (`basecrawl.scr`, 12 rows; core of every walker)

"No strafe attacks, no dodging, just run up and attack" (`BASECRAWL.inc:6-10`).

| State | Behaviour | Citation |
|---|---|---|
| Init | Reads `RunVel`, `WalkVel`, `AttackRange`; chase stop = 0.95 × range, re-chase = 0.70 × range; starts wander, flee and door layers; a pre-set target starts combat at once. | `BASECRAWL.inc:1254-1286` |
| Idle / wander | Wander layer (3.7) until a callback fires. | `BASECRAWL.inc:1064-1074` |
| Detection | `OnFoundTarget` (native sight/hearing). If `ShouldRunAway` says flee → Flee. Else set target, then 40 % `Taunt` (aware animation) before Aggressive, 60 % straight to Aggressive. | `BASECRAWL.inc:714-748`, `AWARE_CHANCE` `:21` |
| Set up target | Stop wander and cower; face the target permanently; start the alert tick; **the first time it targets the party, double its vision and hearing ranges**. | `BASECRAWL.inc:678-711` |
| Aggressive tick (0.2 s) | Give up after `MAX_CHASE_TIME` 30 s without attacking or being attacked; check `ShouldRunAway`; then in range → In range, else Out of range. | `BASECRAWL.inc:410-452`, `:36` |
| Out of range (pursuit) | Re-check `CanReachTarget` (0.1–0.4 s); unreachable → stop and wait. Reachable → `RunTo` the target, **only if its recovery would finish before it arrives** (`RecoveryTimeLeft < distance / RunVel`). | `BASECRAWL.inc:354-400`, `:324-351` |
| In range | Attack ready and clear shot → Attack. A non-friend in the way becomes the new target. Not ready: stop if within 0.75 × range and the target is still. | `BASECRAWL.inc:247-303` |
| Attack | Face the target (360°/s), `Attack`; while the clip plays run after a moving target or stop near a still one (0.2 s tick). | `BASECRAWL.inc:576-626`, `:500-528` |
| Attack done | Stop if the target is still; drop the target if it became a friend; back to Aggressive. | `BASECRAWL.inc:635-666` |
| Retarget on damage / alert / help / nearby projectile | `NewTargetCheck`: no target → take the attacker. Else switch with 70 % (45 % if already in range), halved if the attacker is farther than the current target, ×1.15 if it is less than twice as far. Alerts and help only from friends; help only when idle; projectiles within 200 units count, own shots ignored. | `BASECRAWL.inc:890-995`, `:998-1037`, `:1078-1099`, `:1212` |
| Call for help | While it has a target, a timer re-sends `SendAlert` (interval is a stale random number). | `AICOMMON.inc:35-57` |
| Target died | Clear target, re-enable wander; if it made the kill, taunt after 0.5 s. | `BASECRAWL.inc:821-841`, `:781-803` |
| Lost target | Clear target, back to wander (wander restarts from where it is; there is no walk back home except the leash). | `BASECRAWL.inc:806-811` |
| Flee | See 3.8. | `BASECRAWL.inc:213-229` |
| Wince | Native; the script only hears `OnDamageDone` afterwards and re-runs `NewTargetCheck`. | `BASECRAWL.inc:769-778` |
| Death and resurrection | See 3.9. | `BASECRAWL.inc:1102-1231` |
| Triggers | `GetPlayer` (attack the party now), `GetMe` (attack the sender) let level scripts aggro a monster. | `BASECRAWL.inc:1234-1251`, `:1266` |

### 3.2 Skirmisher: `BaseMelee.inc` (`basemelee.scr` and everything built on it)

Adds the footwork documented in the [animation blending RE](../MM9_ACTOR_ANIMATION_BLENDING_RE.md) and implemented
as OpenYAMM's `skirmisher` modifier.

| State | Behaviour | Citation |
|---|---|---|
| Strafe attack | After the swing starts, if it is still moving and the target is not: `StrafeAttackPct` chance to run ±45° past the target while swinging. | `BASEMELEE.inc:89-121`, `BASEEVADE.inc:92-115` |
| Evade | After an attack, `EvadeChance` (40 %): back-pedal away ±5–35° for half the time then strafe ±65° in 0.1–0.4 s ticks; fixed 2 s; cancelled beyond 500 units. | `BASEMELEE.inc:124-181`, `BASEEVADE.inc:119-286` |
| Back-off and taunt | A strafe attack without an evade: 0.3 s back-pedal, then 40 % `Taunt`. | `BASEMELEE.inc:184-243` |
| Speed throttle | Stays glued to a moving target (0.95 × its speed), 1.25 × while lunging, half speed during a strafe attack before the blow lands. | `SPEEDTHROTTLE.inc:38-135` |
| Obstacle | Bumping the target during the attack stops it only if the target is still. | `BASEMELEE.inc:59-85` |

Turn-based mode skips strafe attacks and taunts (`BASEMELEE.inc:99-103`, `:200-203`).

### 3.3 Ranged add-on Type 1: `Range.inc` on a walker (`baserange`, `crawlrange`, `ghost`, `titan`, demons)

"Prefers melee, runs after the target, shoots periodically, when the target is out of range or unreachable"
(`RANGE.inc:6-12`).

| State | Behaviour | Citation |
|---|---|---|
| Shot check (1.0–2.5 s) | Only if `CanRangeAttack`, the target is outside melee range and inside `RangeAttackRange`. `EstimateRangeAttackHit`: target 100 %, nothing 20 %, other object 15 %, another AI or world 0 %. | `RANGE.inc:151-224`, `:34-41` |
| Pursuit veto | Within range attack range, if 5 s passed since the last shot and the shot is clear: don't chase, shoot instead. | `RANGE.inc:496-531` |
| Shot | Stop only if the target is less than 1 s of running away; face; `RangeAttack` (the engine picks projectile or spell). Melee attacks postpone the next check. | `RANGE.inc:71-120`, `:262-273` |
| After the shot | Back to Aggressive. | `RANGE.inc:465-482` |
| Hiding after shots | Written but disabled on 2002-02-18 ("Unused/Untested feature causing problems"). | `RANGE.inc:416-426` |

The same `RangeAttack` covers casters: liches and vampires "shoot" their spell through this loop.

### 3.4 Ranged holder, Type 2 (`EvilSorcerer.scr`; placed `RangeAttackType 2` on 33 actors)

Never chases (`EVILSORCERER.scr:11-33` empties `BaseCrawlGetHim`, `TargetStill`, `TargetMoving` and forces
`ShouldRunAfter` false), checks for a shot every 0.2–0.4 s (`RANGE.inc:40-41`, `:485-492`), and only follows a
target it has meleed, up to 3 × melee range (`RANGE.inc:292-316`). It still evades after a melee swing (BaseMelee).

### 3.5 Air flier: `BaseFly.inc` (`basefly`, `FlyingIcky`) and `FlyRange.inc` (`flyrange`, `Banshee`)

A separate loop, not built on the crawler.

| State | Behaviour | Citation |
|---|---|---|
| Detection | Always taunts (aware animation) before attacking. | `BASEFLY.inc:507-520` |
| Aggressive tick (0.2 s) | 30 s chase limit; in range and ready → strafing pass; in range not ready → Back off; out of range → `RunTo` (fly) the target. | `BASEFLY.inc:160-202` |
| Attack pass | `Attack` while strafing ±45° past the target; slows to 0.8 × speed (cap 200) on a still target. | `BASEFLY.inc:453-484`, `:376-411` |
| Back off | 1 s flight away and **up** (vertical 0.6, level if the target flies too), then a swoop. | `BASEFLY.inc:277-319`, `:36-37` |
| Swoop | 1 s flight at 30–50° off the line to the target, then Aggressive. | `BASEFLY.inc:217-247` |
| Retarget | Damage: no target → attacker; else 50 % switch. Alerts and projectiles only fill an empty target. | `BASEFLY.inc:536-574`, `:617-665` |
| Wander | Slow (`WalkVel` as fly speed), obstacle checks off. | `BASEFLY.inc:705-741` |
| No flee | The flier has no `BaseRun` layer: it never flees or cowers. | `BASEFLY.inc:11-14` |
| FlyRange shots | Shot check every 0.3–1.3 s, skipped 40 % of the time, never while swooping or backing off, at least 2 s apart, only with a clear shot. After a back-off, a shot replaces the swoop. Stops if the target is less than 1.1 s away. | `FLYRANGE.inc:18-21`, `:66-80`, `:96-189` |

### 3.6 Swimmer: `BaseSwim.inc` (`BaseSwim.scr`)

The crawler with one rule: `ShouldRunAway` and `BaseShouldRun` return true when the target is **not in water**, so
a swimmer never leaves the water to chase and disengages from targets on land (`BASESWIM.inc:14-56`). Swimming
itself is native (`AISwimFly`, see the water RE). The Isle of Ashes Sea Monster adds a patrol with jumps
(`ISLE_SEAMON.scr`).

### 3.7 Wander and patrol layer: `BaseWander.inc` (all bases)

| Mode | Behaviour | Citation |
|---|---|---|
| Off | `WanderON 0` (1 952 of 2 217 placed actors): stands idle; native fidgets. | `BASEWANDER.inc:712-738` |
| Aimless | Wait `WanderWaitMin–Max` (default 3–8 s), turn 15–180° (15–90° after an obstacle), walk `WanderTimeMin–Max`; beyond `WanderLeash` turn back to the start point (leash checked every 0.25 s). | `BASEWANDER.inc:352-384`, `:245-286`, `:525-550` |
| Marker path | `WanderPathName` + index markers, in order or random; per-marker wait, rotation and animation; no leash on paths; falls back to aimless if a marker is unreachable. | `BASEWANDER.inc:57-130`, `:407-447`, `:645-699` |
| Triggers | `Wander`, `WanderStop`, `TouchedMarker`. | `BASEWANDER.inc:725-727` |

### 3.8 Flee, cower and hide: `BaseRun.inc` (walkers, NPCs, animals)

| State | Behaviour | Citation |
|---|---|---|
| Decide | Native `ShouldRunAway` (placed `RunawayChance`, presumably HP); not again within 30 s of the last flight unless feared. `Fear` forces it; `FearDone` ends it. | `BASECRAWL.inc:164-192`, `BASERUN.inc:219-242`, `:556-579` |
| Run | 10 % cower in place if it has a `Cower` clip; else run away ±15–45°, re-aimed every 0.3–0.8 s, ray-probing for walls; calls `Help` on every tick. Ends after 15 s (cower if possible) or beyond 1 000 units. | `BASERUN.inc:504-553`, `:245-307`, `:18-26` |
| Obstacle | Picks the side (±90°) that ends farther from the attacker; three bumps within a second → cower or stop. | `BASERUN.inc:310-395` |
| Hide | `FindHidingPlace`, run there, turn around and call `Help`. (`HidingPlaces` is 0 on every placed actor.) | `BASERUN.inc:398-479` |
| Cower | Loop `Cower` until the attacker is out of sight (5 s checks). | `BASERUN.inc:93-148` |
| Water | Swimmers force flight from targets out of water (3.6). | |

### 3.9 Alerts, resurrection and faction triggers: `AICommon.inc`

- **Alert:** periodic `SendAlert` while it has a target (`AICOMMON.inc:35-57`).
- **Resurrection chain:** a raisable monster (`CanBeResurrected` + `Resurrect` clip) records its killer's target,
  then asks every `AIBase` within 1 000 units that is a resurrecter (`IsResurrecter` = the `Resurrect` column)
  every 5 s (4 s turn-based). The resurrecter waits 3–6 s (1–2 s turn-based), faces the corpse, plays
  `ResurrectSpell`; the `DoResurrection` key raises it. The raised monster waits until nobody stands within twice
  its radius, plays `Resurrect` and attacks its old target. A corpse nobody raises after asking is removed
  (gibbers excepted); a resurrecter with no one else raises itself after 2–10 s.
  (`AICOMMON.inc:62-404`; overrides `BASECRAWL.inc:1102-1201`.)
- **Triggers:** `HateAll`, `StopHateAll`, `HateAllOthers`, `StopHateAllOthers` change enemy lists by class
  (`AICOMMON.inc:435-467`, `:536-540`); `Enrage` and `EnrageDone` drop the target so detection picks a new one
  (`AICOMMON.inc:484-505`).

### 3.10 Doors: `BaseDoor.inc`

Walking or running (or flying) into a closed AI-triggerable door within 45° of its facing: stop, face it, send
`Use`, pause all timers for the door's open time, resume the walk or chase (`BASEDOOR.inc:27-135`).

### 3.11 Civilian: `NPCBase.inc` (`NPCbase.scr`, 86 rows) and the guard

| State | Behaviour | Citation |
|---|---|---|
| Idle | Wander layer; every 5–15 s look for another NPC to chat with for 10–30 s (`Converse` animations, hello/goodbye handshake). | `NPCBASE.inc:23-41`, `:183-513` |
| Use | Pauses everything and hands over to RUDE dialogue; resumes on exit. | `NPCBASE.inc:516-552`, `:812` |
| Damage or nearby projectile | Run away from the attacker, calling `Help`; prefer running to a `GuardBase` within 1 600 units, else to its marker. | `NPCBASE.inc:574-656`, `:682-772`, `:818` |
| Guard (`policeman.scr`) | BaseMelee with friends Player, NPC, Cat, Animal, guards and enemies `AIBase` (all AI); ignores alerts from monsters; turns hostile to the party after 3 hits; answers `Help` from friends by making the culprit's class an enemy. | `POLICEMAN.inc:22-25`, `:41-154` |

Animals (`FarmAnimal.inc`, `hen/pig/duck/rooster` on the older `wander.inc`) wander and flee when damaged, with
gimmicks (cats flee dogs, dogs chase cats and follow actors, goats butt users, cow tipping). The Fish swims in its
water volume (`FISH.scr`).

## 4. Special monsters

### 4.1 Rows whose default script is not a pure base

Pure bases: `basemelee`, `baserange`, `basecrawl`, `crawlrange`, `basefly`, `flyrange`, `BaseSwim`, plus
`ghost.scr` (= BaseMelee + Range, `GHOST.scr:7-18`) and `titan.scr` (= BaseCrawl + Range, `TITAN.scr:9-19`), which
add no code. Everything else:

| Script (rows) | What it adds beyond the base | Kind |
|---|---|---|
| `dagrell.scr` (148–149) | BaseMelee without the speed throttle ("looks funny") (`DAGRELL.scr:16-22`). | flag |
| `EvilSorcerer.scr` (156–158) | Range Type 2, never chases (`EVILSORCERER.scr:11-46`). | parameter |
| `Guardbase.scr` (111–113) | Base + random idle sounds. It includes `Basemelee.scr`, whose `:Main` comes first; the manual says the first `:Main` runs, so `GS_Init` may never run (`GUARDBASE.scr:8-24`, unverified). | cosmetic |
| `MonkBase.scr` (123–125) | Same include pattern plus a hostility parameter tested through a misspelt variable (`bHotstile`), so the monk's own logic likely never runs (`MONKBASE.scr:12-26`). Placed monks use `monkguardbasic.scr` instead (29 of 30). | cosmetic / faction |
| `policeman.scr` (Town Guards) | Guard faction rules (3.11). | faction |
| `Magreeb.scr` (244, 276–278) | On first sight of the party, gives quest key 202 if it holds key 201 (`MAGREEB.scr:14-39`). | event hook |
| `LesserDemon.scr` (241) | `p0 = 1`: spawn a Greater Demon (spawning in) at its corpse (`LESSERDEMON.scr:18-53`). Used by 1000 Terrors spawners. | death spawn |
| `GreaterDemon.scr` (242) | `p0 = 1`: start invisible, client effect, `Spawn` clip, `Aware`, then fight (`GREATERDEMON.scr:14-77`). | spawn-in |
| `Banshee.scr` (162–164) | FlyRange; sets stat `Undead` for up to 5 s during each melee pass (probably an immunity or "insubstantial" window), no swoop, lower and shorter back-off, hides its `Cloth` piece (`BANSHEE.scr:19-84`). | phase |
| `FlyingIcky.scr` (87–89) | Starts hanging upside down (`Hang` loop, `hangfidget` every 2–10 s) unless it is the Airborne Icky or `p0 = 2`; any damage, alert, help, projectile or sighting makes it drop (`Launch`) into BaseFly (`FLYINGICKY.scr:18-247`). | dormant start |
| `lobberpod.scr` (84–85, 105) | Crawler that always evades after an attack (1.8–2.2 s), never shoots (switched off 2002-02-11), and turns on any Lobber that hits it (`LOBBERPOD.scr:18-158`). | flags |
| `lobber.scr` (86, 106) | Stand-alone turret: idle scans by turning 20–120° every 5–15 s; on a target, `Aware` then a 1 s attack check: every 5–10 s `LaunchPod` (a pod-spawning clip, stat `CanLob`), else `RangeAttack` in range, 75 % skip without a clear shot; forgets the target after 30 s without attacking (`LOBBER.scr:39-340`). | **unique** |
| `MagicMine.scr` (179) | Missing from `SCRIPTS.REZ` extraction; the row is placed nowhere. | unknown |
| `dragon.scr` (212) | Boss, below. | **unique** |
| `YanmirBase.scr` (206) | Boss, below. | **unique** |

**Dragon King** (`DRAGON.scr`, placed in DRAGONSTADIUM with `p0 = 1`): hates every AI (`:1158`); `p0 = 1` hides it
until a `Trigger`, then it flies in, lands and taunts (`:1057-1086`); otherwise it starts awake (`NormalSetup`, `:1009-1038`). A sleep-until-damaged mode exists
(`:897-910`) but nothing calls it. It never moves: attacks are chosen by distance: under 200 → 20 % wing buffet (no
damage, pushes back) or breath; under 230 → breath (continuous flame); under 1 800 → fire bolt; beyond → idle
(`:259-298`, `:319-380`, `:71-76`). Targets are re-evaluated every 3–6 s over all enemies: 20 % switch, 80 % if
the new one is closer, +45 % for the last attacker, ignoring 75 % of targets without a clear shot
(`:740-797`, `:56-69`). A `SpawnMutants` trigger spawns two Winged Mutants at markers every 45 s, doubling the
interval each time (`:976-1006`, `:124-125`). On death by the party: key 472 and item 577 (`:1112-1122`).

**Yanmir** (`YANMIRBASE.scr`, YANMIRSFORT): dormant until the `Squish` trigger, then patrols a marker path and hunts
**Ice Lobbercicles** within 500 units ("bugs") to squash them, wiping its shoe after a kill
(`:23-69`, `:238-334`); ignores alerts (`:336-341`); does not chase into the earthquake spot (`:277-294`); kicks
doors open with dust effects (`:139-195`); `TimeToDie`, `DestroyFloor`, `PlayerRanAway` triggers drive the
set-piece ending; immune to damage (`CanDamage FALSE`, re-applied after loads, `:549-554` and the TELP note
`:6-8`).

### 4.2 Placed-object and spawned overrides on monsters

363 of 1 625 placed monsters (22 %) override the script. By kind:

| Kind | Placed | Scripts (examples, all in `mm9/extracted/SCRIPTS/SCRIPTS/`) |
|---|---|---|
| Dormant until triggered, then the base | 135 | `MUMMYAWAKEN` (39 mummies stand or lie until triggered, chain the next one on death, `p0..p3`), `COFFINMUMMY` (8 Rotters in coffins), `AUTORESURRECT` (26 undead start invisible underground, rise on the `Resurrect` trigger, `AUTORESURRECT.scr:66-83`), `KINGKONG` (cage break-outs: `ForceBreak`/`ForceFall`/`ForceAttack`, 17), `DP_CAGEMONSTER` (Terrors released by doors), `SCURRYCREATURE` (Basilisks that hide), `KLUSOSSLEEPER`/`KLUSOSHIDDEN`, `YANMIRHIDDEN` (Forest Giants that appear and run `titan.scr` once Yanmir is gone), `DOOKSLEEPGAURD`, `SPAWNCREATURE` |
| Patrol paths and flocks | 82 | `1000T_FLYINGCREATURE_`, `LL_FLYINGCREATURE` (Flying Ickies circling marker lists), `IS_FICKYFLOCK`, `KLUSOSPATROL`, `DP_PATROL`, `HONKFOLLOWER` (ceremony), `TH_LOBBYGHOULS`, `GUARDTONEGATE`, `TASARGUARDDUTY` |
| Hostility gates (friendly until provoked) | 75 | `MONKGUARDBASIC` (19; aggression checks, work animations, then `BaseInit` + `RangeInit`), `DOOKGUARDBASIC` (16; hostile after the tunnel), `DRANGHEIMGUARDBASIC`, `GUARDRUDE`, `GUARDHELP`, `GREENPARTY`, `TASARSTUDENT`, `THJORADMONK`, `HONKIES` |
| Set pieces, cutscene actors, NPC roles | 42 | `TH_TRAININGORCS`, `TH_JOUSTTRELLBORG`, `THORGARD_ACTOR` (night ambush, cliff jumpers), `DARKP_WARRIOR`, `FATC`, `COLLOIDALGENIE`, `ARMWRESTLE`, `MP_IMP` (an Imp that runs to its friends before attacking), `NPC*.scr` dialogue roles |
| Unique boss fights | 13 | `NJAMFREEZE`/`NJAMTAUNT`/`NJAMCHASE` (Njam cameo chases and vanishes), `EBORABATH`/`EBORAMINES` (an invulnerable Ebora taunts from the tub; when three concubines or her Colloidal bathmate die she flies out, casts and vanishes in a column of fire, giving keys and experience), `EBORACONCUBINE`, `YANMIRBASE`, `THRONHEIMCITY_BADASS` (a Desert Terror breaks out and chases NPCs until guards kill it), `AK_GIANTIMP`, `IS_KILLINGLICH`, `ISLE_SEAMON` |
| Summoners | 10 | `SUMMONER`, `ISLE_SUMMONER` (spawn minions from markers, refocus them, stop on death), `WIZARDSUMMONER` (Evil Apprentices channel a summoning ritual through `Shooter` objects, then fight as Type 2 casters), `WIZARDMASTER` (the Grand Sorcerer's ritual summons a `WizardDemon` that hates the wizards and the party), `CHASM_GHOSTSPAWNER` |
| Base swap / jumper | 6 | `JUMPER` (4 Yetis wait hidden on a cliff and leap down at the party, `JUMPER.inc:73-193`), `flyrange` on two Oculi |

Scripts named in the brief that run on spawned rather than placed monsters:

| Script | Spawned by | What it adds |
|---|---|---|
| `NJAM1000.scr` + `.inc` | `SPAWNNJAM.scr:26` (8 spawn points, 1000 Terrors) | Njam hunts the party as a BaseMelee + Range caster, cannot be damaged (`CanDamage FALSE`), and vanishes with effects and sounds once its HP drop below a random 1 500–4 500 (`NJAM1000.inc:23-73`; the HP test runs inside `ShouldRunAway`). |
| `ENDDEMON.scr` | `ENDCOUNT.scr:24` (1000 Terrors finale) | Greater Demon spawn-in; on death opens the last doors. Intended ×10 HP and ×1.5 AC, but both lines write `Hitpoints` (HP ends as AC × 1.5), and `sDoorA` is declared twice while `sDoorB` is never set (`ENDDEMON.scr:18-37`, `:93-101`). |
| `WIZARDDEMON.scr` | `WIZARDMASTER.scr:24` | Spawn and roar clips, then BaseMelee + Range against the wizards and the party; `finish` trigger hands over to `WizardDemonDeath.scr` (`WIZARDDEMON.scr:11-59`). |
| `ARENACREATURE`, `ARENAMINI`, `BC_MONSTERFIGHT`, `HATE`, `HATENPC`, `ISLE_SPAWNCREATURE`, `BANDITATTACK`, `PEASANTTRANSFORMEE`, `SPAWNFACE` | arena, battle and spawn managers | Faction changes (`Hate`: make X hate Y, then BaseMelee) and arena bookkeeping on top of the bases. |

`DP2MEGAHYDRA.scr` (only a `DamageOn` trigger setting `CanDamage 1`), `DRAGONRED`, `DRAGONAZURE`, `DRAGONEARTH`,
`DRAGONREDAIR`, `DRAGONPHARAOH2FLAME/WATER`, `DP2DRAGONDEAD`, `BONEDRAGON`, `LICHSORCERER` and `SPELLCASTER` are not
placed or spawned by any shipped world; they are cut or test content (`DRAGONRED.scr` is a 2000-era sleeping red
dragon).

`CanDamage`: `YANMIRBASE.scr:6-8` calls `CanDamage FALSE` "immune to physical damage", so it is an invulnerability
switch (Yanmir, Njam, Ebora in the bathhouse, the unused mega-hydra until `DamageOn`).

### 4.3 How many monsters need more than a parametrised base

| Level | Monster rows | Placed monsters |
|---|---|---|
| Pure base, row parameters only | 104 (77 %) | 1 262 run their default (78 %), most of them a pure base |
| Base + one flag or hook (no throttle, never chase, dormant start, spawn-in, death spawn, always evade, quest-key hook, sounds) | 25 (19 %) | — |
| Genuinely unique | 6 (4 %): Dragon King, Yanmir, Lobber, Ice Lobber, Magic Mine (unknown), Banshee phase | 13 boss placements |
| Encounter scripting on placements | — | 350 (22 %), almost all reusable patterns: dormant/awaken 135, patrol 82, hostility gate 75, set pieces 42, summoners 10, jumpers 6 |

## 5. Conclusion

### The archetypes MM9 really has

1. **Crawler** (`BaseCrawl.inc`): chase with arrival timing, attack, re-target by chance, 30 s give-up, flee
   when told. Animals-like monsters, wolves, mummies, Nagates, Magreebs, swimmers' core.
2. **Skirmisher** (`BaseMelee.inc` = crawler + strafe attack, evade, back-off taunt, speed throttle): the default
   for humanoids and most monsters. Already in OpenYAMM as the `skirmisher` modifier.
3. **Ranged holder** (Range Type 2): stays put, shoots or casts often, melees only what reaches it. Evil
   Sorcerers, summoners, 33 placed actors.
4. **Air flier** (`BaseFly.inc`): strafing passes, back off upwards, swoop in, never flees. Birds, Ickies,
   Dragonflies, Winged Mutants, Banshees.
5. **Swimmer** (crawler bound to water: ignores and flees targets on land). Jellyspores, Sea Monsters.
6. **Turret** (Lobber): rooted, scans by turning, shoots and spawns pods. The Dragon King is a turret boss.
7. **Civilian** (`NPCBase.inc`, animals, `PoliceMan.inc`): wander and chat, flee and call help, guards answer
   help and police the party.

Two **add-ons** apply across archetypes and are data-driven: the walker ranged loop (Type 1: chase and take
opportunistic shots or casts every 1–2.5 s outside melee range, clear-shot weighting) and the flier ranged loop
(shots every 0.3–1.3 s with a 40 % skip, at least 2 s apart, a shot instead of a swoop). Casting is not a separate
behaviour: casters are ranged monsters whose `RangeAttack` is a spell. Hovering beholders and ghosts use the walker
loops while flying.

Shared **layers** every archetype composes: wander/patrol with leash (3.7), flee/cower/hide (3.8), alert and
help propagation, the resurrection chain and hate/enrage triggers (3.9), doors (3.10), and the native hit reaction.

### What distinguishes monsters inside an archetype

- From `MONSTERS.txt`: walk/run/fly speed, `LungeVelocity`, `AttackRange` (and reach), `Recovery`,
  `Strafe Attack Pct`, `Evade Chance` (constant 40), `HeadTurn`, the wince columns, `AlertRadius`, `Resurrect`
  (resurrecter), the attack and spell columns (which decide whether the ranged add-on does anything and what it
  fires), `concat` on-hit riders.
- From the placement: `SightDistance`, `HearingDistance`, `RunawayChance`, `RangeAttackType` (Type 1 or 2),
  wander mode, path and leash, `CanBeResurrected`, rails and barrier flags, death and damage triggers,
  `ScriptParams`.

### What is genuinely per-monster

- **Bosses:** Dragon King (distance-banded wing/breath/bolt, multi-target switching, timed Winged Mutant
  reinforcements, fly-in trigger), Yanmir (hunts Ice Lobbercicles, door kicking, invulnerable set piece), Njam
  (invulnerable cameo that vanishes), Ebora (invulnerable taunting, escape once her concubines die), the summoners.
- **Small per-family hooks** that OpenYAMM can express as data flags rather than code: the Lobber's pod launch
  (a summon-on-cooldown), the Banshee's undead window during melee passes, the Icky's hanging start (a generic
  "dormant until disturbed" start), the Greater Demon's spawn-in and the Lesser Demon's death spawn, the Dagrell's
  missing speed throttle, the Lobber Pod's always-evade, the Magreeb's quest-key hook.
- **Encounter scripting** (22 % of placements) is mostly a handful of reusable patterns: dormant until a trigger,
  marker patrol, friendly-until-provoked faction gates, cage or coffin break-outs, rise from the ground, leap from
  a cliff, summon minions from markers. These fit OpenYAMM's per-actor behaviour scripts or map events better than
  per-monster AI.

### Open questions

- `Att%` (col 33): its consumer at record `+0x620` in `object.lto` (or `cshell.dll`) is not traced, and the current
  importer's MM8 reading (chance of attack 2) conflicts with the data.
- How `RangeAttack` chooses between `Projectile1`, the spell and `SpellUse%1`, and what `RangeAttackRange` is
  (perhaps the projectile's `range (ft)` in `PROJECTILE.txt`).
- The native `ShouldRunAway` formula (`RunawayChance`, HP), the wince rule (`WinceThreshold`/`WinceTrackTime`),
  and where `Fly`, `Move`, `Target Pref`, `ConcatAttk`, `SpellUse%2` and `Hostility Group` are read (probably
  `cshell.dll`).
- `MagicMine.scr` is missing from the extracted scripts.
