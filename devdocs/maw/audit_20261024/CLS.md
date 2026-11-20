# CLS: classes, races, promotions, character creation, HP/SP

Auditor: CLS. MAW = `/home/pjasicek/github/Maw-Mod-MMMerge` at `ef23ee17`; paths below are relative to its `Scripts/`
unless they start with `Data/`. OpenYAMM paths are relative to the repository root. No build or test was run.

### CLS-1: MAW's mana comes from Personality only; we also count the class's Intellect
Severity: P2 (every Intellect and mixed caster gets a different SP pool; Sorcerers, Archers, Dark Elves, Elementalists
and Death Knights' stat choices change)
Confidence: confirmed (read both sides)
MAW: `General/zzMaw-Items.lua:4427-4433` sets `Game.Classes.SPStats[i]=2` (Personality) for every class whose SP stat
is above 0. The value is the engine's SP-stat kind (`reference/mmmerge/Scripts/Structs/00 structs.lua:1145`,
"0 = no SP, 1 = Intellect, 2 = Personality, 3 = both"). The engine's full SP therefore uses E(Personality), and
`addMana` (`General/zzMaw-Items.lua:3131-3146`) adds `SPFactor × E(Personality)` again in row 9, so the pool is
`SPBase + SPFactor × (level + 2·E(Personality))`. The `effect*2` in `totalMana`, the Enlightenment base, says the same.
Intellect gives no SP. `devdocs/maw/TRAINERS_SKILLS.md:842` records the override; the class code did not take it up.
OpenYAMM: `game/rules/maw/MawClassRules.cpp:192-222` adds the class's `manaMode` stat effect (Intellect,
Personality, or for Mixed classes Intellect + Personality) and then a second Personality effect. Intellect classes
get E(I) + E(P), and Mixed classes (Druid line, Ranger line, Shaman line) get E(I) + 2·E(P).
Not covered by: DEVIATIONS 25 describes MAW as "adds the Personality effect to every class" and records our formula as
"class stat effect + Personality effect". It misses the SPStats override, so the deviation rests on a misreading of
MAW. No GAPS row.
Suggested fix: use 2·E(Personality) for every class with SP (ignore `manaMode` except None), or record the Intellect
term as a deliberate change. Related note on DEVIATIONS 25's "depends on engine internals": `General/zzMAW-Skills.lua:402-404`
sets every `CalcStatBonusBySkills` result to 0. That removes the engine's own Meditation SP, and row 9 never adds
`SPFactor × Meditation`, so in MAW Meditation adds SP only through Enlightenment's base. Our flat Meditation SP is
therefore a real difference too, and the deviation's MAW column can say so plainly.

### CLS-2: Class perks read the effective school skill; MAW reads the trained skill
Severity: P2 (a school-skill item or follower bonus can almost double a class perk, because D.4 lets item bonuses
reach the trained level)
Confidence: confirmed
MAW: every class perk reads `pl.Skills[...]`, the trained level without item, follower or race bonuses:
- DK, Seraphim, Shaman and Assassin flat melee damage: `General/zzMaw-Items.lua:2881-2900`.
- Shaman Spirit damage multiplier: `General/zzMaw-Items.lua:3339-3342`.
- DK Frost and Seraphim Light attack speed, and the Assassin's Subtlety stack speed: `General/zzMAW-Skills.lua:532-552`.
- Seraphim Spirit and Shaman Water flat reduction: `General/zzMaw-Stats.lua:742-758`.
- Shaman Air and DK Blood/Unholy cuts: `General/zzMaw-Stats.lua:778-787`.
- Shaman Fire burn and Assassin Poisons burn: `Modules/MawCore/Damage.lua:1048-1062`.
- Shaman Mind/Body leech: `Modules/MawCore/Damage.lua:676-680`.
- DK Blood Leech: `Modules/MawCore/Damage.lua:746`.
- Seraphim Body heal: `Modules/MawCore/Damage.lua:110`.
- Shaman's seven-school sum for spell damage and heals: `Modules/MawCore/Damage.lua:1118-1127`,
  `General/zzMaw-Spells.lua:2371-2376`.
OpenYAMM: `schoolSkill` (`game/rules/maw/MawClassRules.cpp:572-577`) and `school`/`skillLevel`
(`game/rules/maw/MawCombatRules.cpp:41-45, 2978-2984`) add `Character::skillBonus`, which counts item, follower and
race bonuses (`game/party/Party.cpp:1959-1972`). This feeds `mawClassMeleeFlatDamage`, `mawClassMeleeMultiplier`,
`mawClassAttackSpeedPercent`, `mawClassDefense`, `mawShamanSchoolSum`, the Shaman/Assassin burns
(`MawCombatRules.cpp:1474-1478`), the Subtlety speed (`MawCombatRules.cpp:1324, 1370`) and the Seraphim, Shaman and DK
on-hit effects (`MawCombatRules.cpp:3020-3140`). The Ascension sums (`mawAscension`) already use the trained levels,
as MAW does.
Not covered by: no related row (D.4 is about the item cap, not about which skill the perks read).
Suggested fix: read the trained level (`findSkill(...)->level`) in these perks. Keep the effective skill where MAW uses
`GetSkill`: the Assassin's energy-refund chance, the Assassin SP pool's mastery, the energy regeneration mastery, and
the dragon formulas.

### CLS-3: Assassin kills with class spells refund no energy and build no combo point
Severity: P2 (combo points feed the Assassin's finishers; a spell kill is worth (1+Subtlety mastery)×5 energy and a point)
Confidence: confirmed
MAW: `assassinationDamage` (`Modules/MawCore/Classes.lua:365-432`) is also called for the Assassin's spells
(`Modules/MawCore/Damage.lua:824-835`, all `assassinSpells`). For a spell, cost and refund chance are 0
(`Classes.lua:376-379`), but the `RunNextTick` kill check (`Classes.lua:388-395`) still adds `(1+m)*5` SP (m = Air
mastery) and one combo point when the monster dies.
OpenYAMM: `MawCombatRules::applyClassHitEffects` sends only melee blows and arrows to `applyAssassinHit`
(`game/rules/maw/MawCombatRules.cpp:2993-2997`). Spell hits from an Assassin reach none of the kill code, and
`comboPoints` is raised only in `applyAssassinHit` (`MawCombatRules.cpp:3181, 3191`).
Not covered by: DEVIATIONS 28 (payment by landed blows) and L6.2/L6.3 (crowd cut, Lightning chaining) do not cover
spell kills.
Suggested fix: on an Assassin class-spell hit that kills, add `(1 + Air mastery) × 5` SP (capped) and one combo point,
without cost, stacks or refund roll.

### CLS-4: Elementalist stacks wait about twice as long before they fade
Severity: P3
Confidence: confirmed
MAW: `Classes.eleCastRotation` sets `eleTimer = Game.Time + max(getSpellDelay(pl,spell)*4, 128)`
(`Modules/MawCore/Classes.lua:533`). `getSpellDelay` returns recovery units (`General/zzMaw-Stats.lua:162-243`, e.g.
120 for Dragon Fear), and they are added to `Game.Time` unchanged, at 128 ticks per real second
(`reference/OpenEnroth-git/src/Engine/Time/Duration.h:28`). The window is therefore `max(4·delay, 128) / 128` seconds,
about 1.9 casts' worth, since a cast's recovery lasts delay × 2.133 / 128 s. Once the window passes,
`elementalistStacksDecay`, run every 0.1 s (`General/zzMaw-Timers.lua:97`), halves the stacks at once and then every
128 ticks (`Classes.lua:300-315`).
OpenYAMM: `idleLimit = max(4·elementalLastDelayTicks, 128) / 128 × 2.1333` s (`game/rules/maw/MawClassRules.cpp:418`).
That is 2.13 times MAW's window, and the minimum becomes 2.13 s instead of 1 s. The first halving also comes a full second
after the window (`MawClassRules.cpp:420-428`); MAW halves within 0.1 s.
Not covered by: DEVIATIONS 26 and GAPS A6.9 (building and spellbook reset only).
Suggested fix: drop the ×2.1333 and halve as soon as the window passes, then once a second.

### CLS-5: Fractional HP/SP factors: Elemental Adept 2.5 and Elder/Ultimate factors are integers in MAW
Severity: P3
Confidence: confirmed for the Elemental Adept, plausible for the exact rounding of Elder/Ultimate factors
MAW: `Game.Classes.HPFactor` and `SPFactor` are byte arrays. In `reference/mmmerge/Scripts/Structs/00 structs.lua:1135-1138`
they are `.u1`, and `Structs/After/RemoveClassLimits.lua:140-147` moves them to a new byte block. So
`Game.Classes.HPFactor[63]=2.5` (`General/zzClasses.lua:606`) stores 2, by truncation or banker's rounding, and the
Elemental Adept keeps 2 HP a level. `checkPromo` writes `oldHP*(0.75+0.25*n)` into the same bytes
(`General/zzClasses.lua:97-98`). Examples: 5×1.25 = 6.25, 3×1.25 = 3.75, 5×1.5 = 7.5. These become whole numbers,
probably truncated, in both the engine and `addHP`/`addMana`, which read `Game.Classes.HPFactor[pl.Class]`
(`General/zzMaw-Items.lua:3111, 3132`).
OpenYAMM: `MawClassRules::healthPerLevel` uses exactly 2.5 for the Elemental Adept (`game/rules/maw/MawClassRules.cpp:172`).
`promotionFactor` multiplies by the exact 1.25 or 1.5 (`MawClassRules.cpp:162-179`).
Not covered by: DEVIATIONS 24 (Elder/Ultimate by multiplying, "same numbers") assumes MAW keeps the fractions.
Suggested fix: Elemental Adept 2 HP a level (or record 2.5 as intended). Floor the promoted factors
(`int(perLevel × factor)`) unless a runtime check of MMExtension's u1 store shows it rounds.

### CLS-6: Vampires' night Preservation starts at 22:00, MAW's at 21:00
Severity: P3
Confidence: confirmed
MAW: `hour = Game.Time%const.Day/const.Hour` is a fraction, and the test is `hour>21 or hour<5`
(`General/zzMaw-Spells.lua:1083-1087, 2957-2962`). The night therefore runs 21:00–04:59.
OpenYAMM: `world.currentHour()` returns a whole hour (`game/gameplay/GameplayRuntimeInterfaces.h:623`), so
`hour > 21 || hour < 5` (`game/rules/maw/MawClassRules.cpp:481-482`) starts at 22:00. CLASSES_SPELLS_SPEC §6.4 says
"22:00", copying the same misreading.
Not covered by: no related row.
Suggested fix: `hour >= 21 || hour < 5`, using the game minutes for the exact boundary if wanted.

### CLS-7: The Assassin's 15-energy refund is rolled only on paid blows
Severity: P3
Confidence: confirmed
MAW: `assassinationDamage` rolls the refund (`0.1 + 0.01·Combat skill`, halved for arrows) and adds 15 SP before it
checks whether the blow can be paid (`Modules/MawCore/Classes.lua:372-387`). An Assassin with no energy can therefore
regain it by hitting.
OpenYAMM: the roll sits inside `if (member.spellPoints >= cost)` (`game/rules/maw/MawCombatRules.cpp:3170-3184`). An
Assassin at 0 energy only regains energy from regeneration and kills.
Not covered by: DEVIATIONS 28 ("paid by blows that land" is about the cost, not the refund).
Suggested fix: roll the refund on every melee blow and arrow hit, before the payment check.

### CLS-8: Death Knight on-hit effects apply to melee only; MAW applies them to every physical hit, arrows included
Severity: P3
Confidence: confirmed
MAW: `stage_dkAttack` runs the SP regeneration (10/15/20, ×1.5 on a killing blow), Blood/Superior Blood Leech and
Death Grasp under `t.DamageKind==4` with no `data.Object` test (`Modules/MawCore/Damage.lua:744-789`). A Death
Knight's arrow (Bow E in `Class Skillz.txt`) refills SP, leeches and grasps.
OpenYAMM: these effects sit after `if (!meleeBlow) return;` (`game/rules/maw/MawCombatRules.cpp:3051-3054, 3110-3139`).
Arrows do none of them.
Not covered by: DEVIATIONS 29 and 47 (spell details, Dark Grasp state).
Suggested fix: run the Death Knight block for arrows too (physical, `hit.spellId == 0`).

### CLS-9: Dragon SP and Assassin energy regenerate while the member is dead, stoned, eradicated or insane
Severity: P3
Confidence: confirmed
MAW: the SP regeneration loop, which also holds the dragon (`pl.Class==10/11`) and Assassin terms, runs only when
the main condition is good, zombie or below 14, and the member is not insane (`General/zzMAW-Skills.lua:1434-1436,
1470-1481`).
OpenYAMM: `MawClassRules::update` refills the dragon pool and Assassin energy for every member, whatever their
condition (`game/rules/maw/MawClassRules.cpp:443-478`).
Not covered by: GAPS A6.10 (dragon rates; no condition gate mentioned).
Suggested fix: skip the refill for Dead, Petrified, Eradicated and Insane members.

### CLS-10: A dragon's effective level counts the fourth continent's levels
Severity: P3
Confidence: confirmed
MAW: `dragonEffLevel` uses `getPartyLevel(4)+1` (`Modules/MawCore/Classes.lua:730-741`). `getPartyLevel(4)` sums
`vars.MMLVL[1..3]` and leaves out world 4 (`General/zzzMaw_Experience.lua:278-290`).
OpenYAMM: `dragonLevel` uses `rules.state().totalLevel()`, all four continent banks (`game/rules/maw/MawCharacterSheet.cpp:76-87`,
`game/rules/maw/MawGameState.cpp:32-42`).
Not covered by: no related row.
Suggested fix: `rules.state().levelOutside(4) + 1`.

### CLS-11: Class runtime (combo points, stacks, energy remainder) is keyed by the Character's address
Severity: P3
Confidence: plausible (needs a runtime check)
MAW: `vars.assassinStacks`, `vars.eleStacks` and `AttackSpeedStack` are kept by roster index in `vars`, so they
survive saves and party changes.
OpenYAMM: `MawRules::m_classRuntime` is an `unordered_map<const Character *, ...>` (`game/rules/maw/MawRules.h:254`,
`MawRules.cpp:100-114`). `Party` adds members with `m_members.push_back` (`game/party/Party.cpp:3967, 3987, 4055`) and
loads with `m_members = snapshot.members` (`Party.cpp:2514`). A reallocation moves every member, so their entries are
pruned and the state is lost. A new member that lands at a freed address can inherit another character's combo points
or stacks until the next prune. Dismissal is remapped (`MawSpellRules.cpp:788-799`, A7.3), but hire and load are not.
`m_dragonRefills` is indexed by slot and is not shifted on dismissal either (`MawClassRules.cpp:363, 445`).
Not covered by: GAPS A7.3 (dismissal only).
Suggested fix: keep the runtime in `CharacterRulesetState` (saved, moves with the Character), or key it by a stable
member id.

### Question (MAW quirk, not ported): DK quick-cast toggle
MAW's quick-cast toggle for Blood Leech, Superior Blood Leech and Death Grasp compares and stores `t.Param` (the action
parameter) instead of the quick spell (`Modules/MawCore/Classes.lua:859-873`). Quick-casting a toggle therefore
stores a wrong value. OpenYAMM toggles the quick spell properly. This is a MAW bug that OpenYAMM fixes without a
deviation row; it is worth one line in DEVIATIONS.

## Checked and matching

- Class HP/SP table: our engine `class_multipliers.txt` plus the MAW patch and append equal
  `Data/Tables/Class HP SP.txt` row by row (script comparison). Lua overrides are honoured: Dragon SPBase 60, Great
  Wyrm 120, SPFactor 0, Minotaur 6/12.
- HP formula: `HPBase + HPFactor·(level + E(End) + Bodybuilding·m2)` with Grandmaster counting 5, then the Endurance
  ‰ and Bodybuilding % (`MawSkillRules::applyResourceBonuses`) match `addHP`. Death Knight and dragon-race item SP is
  0, and the Assassin line's item SP is 10 × Assassination mastery (CL:798-800, 838-840, SP:3628-3634). No Enlightenment
  cap for DK, Dragon or the Thief line.
- Skill caps: the composed `class_skills.txt` (with Cover, Mana Shield, Enlightenment and Retaliation columns) equals
  `Class Skillz.txt` for all 65 classes, except the unused `n/u` columns and the Black Knight/Champion Armsmaster "S",
  which is `mawSupremeArmsmaster`. Dragon Fangs and Scales are M/G, as in zzClasses:339-342.
- Race limits: `content/race_skills.yml` equals `Race Skillz.txt` (Human `+` ×7, Vampire/Dark Elf ability min M,
  Minotaur Dagger 0 and Axe min E, Troll Regeneration `+`, Dragon weapons and armour 0 with Dragon
  Ability/Dodging/Unarmed min M, Dwarf Axe min E). `getEffectiveCap` follows the DLL order: shift, then max, then min,
  with the shift also applied at cap 0.
- Racial flat skills (+3 + ⌊base/10⌋, also unlearned) and resistances (elves, Troll, Goblin, Dwarf 25 + level; Dragon
  Fire 100 + 2·level; Undead Mind and Body immune; Vampire Mind immune) match S:2348-2400 and ST:1349-1383.
- Starting skills: the composed `class_starting_skills.txt` equals `Class Starting Skills.txt` for every starting class.
  The column is ⌊class id/2⌋: Seraphim 26, DK 28, Shaman 29, Elementalist 31. The only exception is Learning
  (DEVIATIONS 27). The extra skills 39+ start at nothing. Starting stats: Dragon 14/50 +3 and Dark Elf Intellect 14/30
  +2 rows equal.
- Portraits: `character_data_patch.txt` and the append equal MAW's rows 67-70, 76 and 77, one-based. Free selection
  allows every class with no lower step of its kind (Peasant and the four new lines included) and every portrait.
- Promotions: `promotions.yml` equals `promotionList` and `midPromo`. World count, final step at one world, Elder ×1.25
  and Ultimate ×1.5 on HP and SP factors with the name prefix, mid step only for kinds 17-20, and the final candidates
  include High Priest and Master Wizard as in MAW. Awards are ids below 105, QBits 1544, 1541 and 1539. The promotion
  QBits match the generated MM6/MM7 events.
- Class spell lists: DK spells by Frost, Blood and Unholy mastery, costs from `DKManaCost`, multipliers from
  `DKDamageMult`, and toggles 68, 74 and 96. Assassin lists (m+1, Subtlety m+2), costs, combo costs and damage
  multipliers. Book learning is refused for DK, Elementalist and Assassin.
- Elementalist: always-known 2, 15, 24 and 37; tier thresholds and masteries; Insanity Invisibility needs Grandmaster;
  progress `tier^1.5·√L·√party` (÷3 for area spells but Sparks and Poison Spray); cost `(base+stacks)` ascended ×
  (1+0.075·stacks); delay ×1.5/(1+0.05·stacks); weapon hits clear the stacks; halving by `floor`.
- Ascension sources: Elementalist sum/4 (floored for cast time), Shaman sum/7 at Grandmaster, none for DK and Assassin.
- Seraphim one-handed two-handed swords with no off hand; Dwarf/Minotaur axe handling; Divine Protection (25 %, 150
  game minutes, conscious only); Seraphim Body heal formula and target; Shaman Mind/Body leech formulas; Blood Leech
  formula; Icy Touch slow power; dragon fang, breath and scales formulas and dragon-level cap 600/900; dragon bite refill
  10/20; dragon passive refill 2/5 SP/s × multipliers; Assassin regeneration (0.6+0.2m)·10.
- Supreme Armsmaster: Knight line, Grandmaster, trained level 30/50/70, +⌊effective/10⌋ capped at twice the skill.
- Leech table (vampire race ×2 for Vampire/Nosferatu classes, DK +10 %/5 %).
