# Solo run talents (MAW): as built

**Superseded in part by talent tree v2 (2026-11-14):** [TALENT_TREE_V2_BUILD.md](TALENT_TREE_V2_BUILD.md) (Arms /
Archery / Arcana / Any, keystones, Lone Discipline; Whirlwind, Volley, Disengage, Frenzy, Purify and Mana Font
replaced). The sections below describe the first build.

The special skills ("talents") of an augmented solo run under MAW, built on top of the ruleset: Standard games and
party games see nothing and run exactly as before. Design: [BALANCE_AND_TALENTS.md §5.0](BALANCE_AND_TALENTS.md)
(the revised table), the Talents page: [the study](../../level_generation/ui/solo_talents_20261113/README.md)
("Chosen": layout A with C's habits, reached by a Skills / Talents switch on the Skills page).

## Progress note (2026-11-14)

Stage 0: this note. Stages, in order: 1 data and points; 2 passives; 3 actives and cooldowns; 4 the Talents page; 5
presentation; 6 captures and tests. Each stage updates this note.

- **Stage 1 (built).** `assets_dev/engine/data_tables/talents.yml` (17 talents, `levels_per_point: 10`; a ruleset may
  replace it), read by `GameDataLoader::loadSoloTalents` into `SoloTalentTable` (`game/rules/SoloTalents.{h,cpp}`) and
  bound for rules and screens (`soloTalentTable()`). Points, locks, learn, reset, per-rank numbers there.
  `Character::talentRanks` (saved, `SaveVersionSoloTalents` = 182; older saves have none) and
  `Character::talentState` (`game/party/SoloTalentState.h`, transient). The gate: `soloTalentsActive(ruleset)` (solo run
  and ruleset `maw`); inside MAW's rules, `options().soloRun`.
- **Stage 2 (built).** `game/rules/maw/MawSoloTalents.{h,cpp}`, called from MAW's rules only in a solo run:
  `applyPrimaryStatBonuses` adds Conditioning and Steady Aim while still as a percent of the whole stat (base,
  permanent bonuses, items and buffs; since 2026-11-18, before it only the raw base stat), before HP and SP are derived
  from the stats; `applyClassBonuses` adds Resolve (see the v2 build; Spell Suppression is a damage stage instead);
  `MawClassRules::update` ticks cooldowns and timed effects, Mana Font and Steady Aim;
  `characterAttackRecoveryTicks` takes Frenzy; `absorbCharacterDamage` Shield Wall; `blocksMonsterCondition` Purify;
  `rollSpellDamage`, `healAmount`, `manaCost` and `afterCast` Attunement and Spell Surge (the original bodies kept as
  `...BeforeTalents`).
- **Stage 3 (built).** A bar slot of kind `Talent` (its id: the index in the table) sets
  `GameplayOverlayInteractionState::soloTalentRequested`; the world interaction frame uses it
  (`useSoloTalent`, GameplayInteractionController.cpp), only when `GameplayScreenRuntime::soloTalents()`, out of
  turn-based combat, with the member ready and the talent off cooldown. Strikes go through the ordinary party attack
  with three new optional `PartyAttackConfig` fields (`talentShare`, `talentExtraBlow`, `talentShot`): the ruleset's
  to-hit, damage, effects and experience; an extra blow plays no sound and pays no recovery, and the extra blows run
  before the one that pays (a recovering member strikes no more). Targets: `pickTalentTargets` (nearest first, in
  reach and arc). Cleave: the crosshair's monster at the full blow, up to four more in ±60° at 60 %. Whirlwind: every
  living hostile within reach all around at 50 %. Volley: up to five in ±30° at 60 %. Pinning Shot: a shot and the
  existing actor slow (`debuffActor Slow`, power 2). Charge: `dashParty` toward the crosshair's monster (to 260 short),
  a blow and `stunActor` 1.5 s. Blink and Disengage: `dashParty` (the worlds' collision) 1600 forward or 420 back, the
  monster blink's `openyamm:fx/arcane_pulse` at both ends and its `monster_blink` sound. Frenzy, Shield Wall, Spell
  Surge, Purify set the transient state that stage 2's hooks read. Cooldowns on the bar: a shade from the top and the
  seconds; a gold frame while Frenzy or Shield Wall runs or a surge is armed. MAW's capped costs read "65k".
- **Stage 4 (built).** `game/ui/GameplaySoloTalentsPage.{h,cpp}`: the Skills / Talents switch (top right of the Skills
  page) and layout A over the skill lists: three columns, rows of icon (actives double-rimmed), name, rank pips, n/max;
  gold learned, teal learnable now, grey locked; a detail card for the hovered talent (now and next rank, the refusal,
  the hint). Click learns a rank; right click puts an active on the bar. Drawn after the character overlay
  (`GameplayUiOverlayOrchestrator`), input first in `handleCharacterOverlayInput`; the skill rows under it take no
  hover. Respec: "Forget talents (free)" in every training hall while the member has talents
  (`HouseActionId::TrainingResetTalents`).
- **Stage 5 (built).** `FirstPersonViewModel` plays a talent's clip when `ViewModelLink::talentSerial` changes: Cleave a
  sideways power attack, Whirlwind two sweeps queued at 2.4×, Charge the forward lunge, Volley the bow shot, the rest a
  cast; Shield Wall holds the block pose. Presentation only.
- **Debug console.** `talent <id> <rank>`, `talent reset`, `talent list`, `talent page`, `talent use <id>`,
  `talent clearbar`.

**Decisions taken here.** Melee locks read the best melee weapon skill or Armsmaster, not only the weapon in hand (so a
weapon swap does not take actives away); caster the best of the nine magic schools. Passive percents are of the base
stat, not items or buffs (no compounding). Cleave's crosshair target takes the full blow and the other four 60 %.
Talent blows land at once (the arms show their clip; they do not wait for its Hit key). Steady Aim adds Luck (MAW's
critical chance), not a critical chance of its own. A surge's damage window is 3 s after the cast (a missile rolls on
impact). A bar slot names a talent by its table index.

**Captures** (`level_generation/ui/solo_talents_20261113/native/`, MAW solo, 1600 × 900, no arms): `maw_solo_cleave`
(three goblins in the arc killed by one Cleave), `maw_solo_whirlwind` (the goblin behind the party killed),
`maw_solo_blink` (the party 15 m up the street), `maw_solo_talents_page` and `maw_solo_talents_hover` (layout A, the
detail card), `maw_solo_frenzy_cooldowns`, `maw_solo_bar_talents`. Those runs had the talents set while the bar was full
of the Cleric's spells, so the bar shows no talent slot; the tours (`talent clearbar` first) for the bar's cooldowns, a
Standard solo run and a MAW party game could not run: the desktop display went away ("The video driver did not add any
displays"). Tours kept in the session scratchpad; rerun them.

**Tests.** `tests/SoloTalentTests.cpp` (9 cases): the shipped table, the point economy, locks, learning onto the bar and
reset, the save round trip, each passive's numbers, Frenzy / Shield Wall / Spell Surge / Purify, cooldowns and the
update, the sweep's target choice. All pass; the focused solo, melee, shield, MAW, house, spell, combat and HUD groups
pass, except three ruleset legacy-save conversions that failed before this work (another session's save change).

## What is left

- The bar's talent cooldown capture, the Standard solo and party-game captures (above), and in-game checks of Charge,
  Volley, Pinning Shot, Disengage, Spell Surge, Purify and Shield Wall (built, unit-tested where pure, not yet seen in
  the game); captures with the arms (private, `reference/oblivion_poc/preview/`).
- Talent blows do not wait for their clip's Hit key; Frenzy's warm screen edge; a slash ring for Whirlwind (the
  contact effects show per target).
- Drag from the Talents page onto the bar (right click places it now); the Android layout of the page.
- Icons of their own (all 17 use placeholder spell and item art); Steady Aim as a real critical chance; Mana Font and
  Steady Aim tick four times a second with MAW's class update.
- Open decisions: the unlock rule (taken as above), respec (free at training halls), auto-placing (on), and the
  numbers (first guesses in `talents.yml`).

## Files

New: `assets_dev/engine/data_tables/talents.yml`, `game/rules/SoloTalents.{h,cpp}`,
`game/rules/maw/MawSoloTalents.{h,cpp}`, `game/party/SoloTalentState.h`, `game/ui/GameplaySoloTalentsPage.{h,cpp}`,
`tests/SoloTalentTests.cpp`. Changed: `game/party/Party.h` (`talentRanks`, `talentState`),
`game/party/ActionBarSlot.h` (comment), `game/maps/SaveGame.cpp` (version 182), `game/data/GameDataLoader.{h,cpp}`,
`game/rules/maw/MawClassRules.cpp`, `MawCombatRules.{h,cpp}`, `MawSpellRules.{h,cpp}`,
`game/gameplay/GameplayActionController.{h,cpp}` (talent blow fields), `GameplayInteractionController.cpp`
(`useSoloTalent`), `GameplayInputController.cpp` (bar key), `GameplayScreenRuntime.{h,cpp}` (`soloTalents`, talent
clip link), `GameplayPartyOverlayInputController.cpp`, `HouseInteraction.{h,cpp}` (respec), `game/ui/GameplaySoloHud.cpp`
(talent slots, cooldowns, "65k"), `GameplayOverlayTypes.h`, `GameplayUiController.h`, `GameplayUiOverlayOrchestrator.cpp`,
`game/render/FirstPersonViewModel.{h,cpp}` (talent clips), `game/app/GameApplication.cpp` (`talent` console command,
view model input), `game/CMakeLists.txt`, `tests/CMakeLists.txt`.
