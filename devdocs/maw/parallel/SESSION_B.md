# Session B: spells, auras and classes

Read [README.md](README.md) first: the shared rules, your build directory (`build-b`), the files to claim, your
numbers (DEVIATIONS 100-129, SaveVersion 109) and how to reach the coordinator.

## Your rows (GAPS.md §5 and §6)

Work P2 first, then P3. Rows already `done` are context only.

**§5 Spells and auras**

- P2: A7.1 Shared Life, A7.2 quick-cast heal auto-target, A7.3 aura holders are slot indexes (bug on dismissal),
  A7.4 quick-cast Meditation, A7.5 Shrinking Ray's extra targets, L5.1 non-aura buffs wiped by the 0.5 s aura pass
  (and the temple-donation mana exemption, R clearing them), L5.5 Vampiric Aura and Immolation damage, L5.6 Staff's
  party-wide resistance.
- P3: A7.6-A7.8, A7.10-A7.14, L5.7 (legendaries 20, 25 and 32 are done; check what is left and close it), L5.8
  (reserved SP shown).
- A7.15 is "decide": leave it, or bring the coordinator a recommendation.

**§6 Classes, races, creation**

- P2: A6.1 dragon rules by portrait race, A6.2 dragon breath and Flame Blast through MAW's attack, A6.3, A6.4, A6.6
  free selection, A6.7 MAW portrait races, L6.1 Knight Charge (deviation 48 explains why it was left: it needs a
  party dash in both worlds and a key; implementing it closes dev 48), L6.4 dragons' items ×3 and knockback.
- P3: A6.9, A6.10, A6.11, L6.2-L6.7.

## Where things are

- Rules: `game/rules/SpellRules.h`, `ClassRules.h`, `SkillRules.h`; MAW: `game/rules/maw/MawSpellRules.*`,
  `MawClassRules.*`, `MawClassSpells.*`, `MawSkillFormulas.*`; spell casting `game/party/PartySpellSystem.cpp`.
- Specs: `devdocs/maw/CLASSES_SPELLS_SPEC.md`, `SKILLS_SPELLS_ALCHEMY.md`, `data/spells.yml`, `buff_auras.yml`,
  `class_perks.yml`, `promotions.yml`, `race_bonuses.yml`.
- MAW: `Scripts/General/zzMaw-Spells.lua` (SP), `Scripts/Modules/MawCore/Classes.lua` (CL),
  `Scripts/General/zzClasses.lua`, `Scripts/General/zzMAW-Skills.lua` (S).
- Existing tests to extend the style of: `tests/MawSpellTests.cpp`, `tests/MawClassTests.cpp` (yours to add to as
  well as `tests/MawSpellClassTests.cpp`).

## Expected overlaps

- Damage done by spells runs through `MawCombatRules` stages (claim before editing). Dragon breath (A6.2) and
  Knight Charge (L6.1) touch the attack path (`GameplayActionController.cpp`) and the worlds: claim them.
- Knight Charge needs a key binding (keyboard settings YAML and the input layer) and an Android control decision:
  ask the coordinator before adding a touch control.
- Character creation changes (A6.6, A6.7, A6.11) touch the continent and party-creation screens; their approved
  look is in AGENTS.md (Carved Obsidian menus). Screenshot what you change.
