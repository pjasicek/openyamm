# MM9 hirelings: implementation plan

Plan (2026-11-06) for the MM9-only hireling system. Research and the user's decisions: [MM9_HIRELINGS.md](MM9_HIRELINGS.md)
(its "OpenYAMM design" section and section 9, the combat code). HUD design: the study
`level_generation/ui/mm9_hirelings_20261106/` revision 2. Portraits: `9npcNN-01..56` families from openyamm-2e (MM9 PC
portrait pipeline), installed in `worlds/mm9/icons_x2` after the user's approval. Phases 1-8 and 10 are done
(2026-11-06); phase 9's MM9 scenarios are not written yet.

## Shape

Hirelings are **party members that the player commands**, as in MM9 (section 9): they join the active-member rotation,
attack or cast at the crosshair target on the Attack and quick-cast commands, take hits by formation position, get
conditions, buffs and healing, and have no inventory, equipment or spellbook.

They are **not** added to `Party::members()`: that list has about 245 readers (inventory, spellbook, experience split,
party creation, saves, per-member arrays sized `MaxMembers` = 5), and every one would pick them up. Instead the party
holds a separate list, and the systems that must include hirelings opt in through one accessor of "combatants" (members
then hirelings). MM6-MM8 worlds never fill the list, so their paths are unchanged.

## Phases

1. **Data.** `tools/mm9_import_discovery/generate_mm9_hirelings.py` writes `worlds/mm9/data_tables/hirelings.txt` (one row
   per hireling, the columns of MM9_HIRELINGS.md "Proposed OpenYAMM table" plus the combat values): RUDE id, name, kind
   (paid / story), portrait prefix `9npcNN-`, level, HP, AC, recovery, attack 1 and 2 (damage type, dice, bonus, reach),
   spells (MM9_SPELL_MAPPING.md replacements, skill, mastery, use percent), resistances on the MM6-MM8 schools, hire key,
   fee, wage, service and cooldown, cured conditions, passive, the world object to hide. Values from `MONSTERS.txt`
   through the balance profile (devdocs/mm9_rework/BALANCE_PLAN.md: the balance work may revise them). Loader and
   unit tests.
   **Done.** The table (15 rows: 13 paid, 2 story) is registered in `worlds/mm9/world.yml` (`hirelings`,
   distribution); cured conditions use the engine's condition names (`CharacterConditionNames` in
   `game/party/CharacterState.h`, shared with potions.yml), so MM9's one poison and one disease are all three stages.
   `tools/mm9_import_discovery/test_generate_mm9_hirelings.py` checks it against a fresh generation.
   `game/mm9/Mm9HirelingTable.{h,cpp}`: `Mm9HirelingTable::loadFromRows/find(rudeId)/entries()/errors()`, rows as
   `Mm9Hireling` (kind, service, cured `CharacterCondition`s, typed passives with canonical skill names, attacks as
   `CombatDamageType` + `DamageProfile` + missile, spells as name + `SkillMastery` + skill, `CharacterResistanceSet`);
   malformed rows are rejected. It reuses MonsterTable's cell parsers (`parseDamageProfile`,
   `parseMonsterResistanceValue`, `parseMonsterSpellName/SkillLevel/SkillMastery`, now declared in MonsterTable.h).
   `GameDataLoader::getMm9HirelingTable()` (also `GameDataRepository::mm9HirelingTable()`) is loaded in the MM9 world
   only. Tests: `tests/Mm9HirelingTableTests.cpp`.
2. **Party state.** `Party` gets the hireling list: per hireling a `Character` without inventory or spellbook (HP,
   conditions, buffs, recovery) plus its table row, hire day, wage timer and service cooldown. Save/load with a
   save-version step. World gate: only in the MM9 world; there the MM6-MM8 followers are off (not shown, no wages, no
   gold share, no follower effects).
   **Done.** `Mm9PartyHireling` (Party.h): RUDE id, kind, a `Character` set from the row (name, portrait, level, HP,
   AC in `armorClassModifier`, `baseResistances`), its own `buffs` array (not `m_characterBuffs`), hire day, next wage
   time (28 days after hiring; none for story companions), service ready time, formation cell (-1). `Party::hirelings()`,
   `findHireling(rudeId)`, `paidHirelingCount()`, `canAddHireling(row)`, `addHireling(row)` (the row carries the RUDE
   id), `removeHireling(rudeId)`; limits `MaxMm9Hirelings` 3, `MaxPaidMm9Hirelings` 2. Saved as
   `Party::Snapshot::mm9Hirelings` from save version 157 (`SaveVersionMm9Hirelings`; older saves have none).
   Followers gate: world.yml `npcFollowers: false` (MM9) -> `WorldManifest::npcFollowers` -> `GameSession` and
   `GameApplication::bindPartyDependencies` -> `Party::setNpcFollowersActive`. Off, the party keeps its followers for
   other worlds, but `applyGlobalNpcStateTo` gives the map's event state none (so the HUD panel, found-gold share,
   identify/repair, travel and rest reductions and reputation see none), the party's own follower bonuses
   (skills, luck, resistances, cartographer's Wizard Eye, identify, repair) are off, events cannot add followers, NPC
   hire offers are not made, and the followers button, panel and keys are hidden. MM6-MM8 worlds are unchanged.
   Hirelings gate (2026-11-13): outside MM9 (a world without the hireling table) the hirelings wait behind,
   `Party::setMm9HirelingsAlong(false)` from `bindPartyDependencies`. The party keeps and saves them, but
   `hirelings()`, the combatants, wages and passives see none; they rejoin, on free formation cells, when the party
   is back in MM9. Wages that fell due meanwhile are asked on the return. Scenario:
   `tests/scenarios/mm9/hireling_leaves_world.yml`.
   Left for later phases: nothing reads the hireling list yet (combat, HUD, wages, services, passives); AC sits in
   `armorClassModifier` and the primary stats are 0, which phase 3 must account for when it computes AC and damage.
   Tests: `tests/Mm9HirelingTableTests.cpp` (limits, round trip, followers gate) and `tests/RulesetTests.cpp`
   ("saves before the MM9 hirelings load with none").
3. **Shared rules for hirelings.** Damage taken (AC, resistances), conditions, party buffs and personal buffs, healing
   and cures, recovery with haste/slow. MM9: 0 HP makes a hireling Unconscious, never Dead; any healing wakes it (section
   9). Dead or Eradicated set by an effect: greyed on the rail, cured at a temple or by PC spells (the user's rule).
   No experience share.
   **Done.** *Combatants* (Party.h): the members (0 .. memberCount() - 1), then the hirelings. `combatantCount()`,
   `combatant(i)`, `isHirelingCombatant(i)`, `hirelingCombatant(i)`; `member()`/`members()` stay the PCs. These take
   combatant indices, unchanged for members: `applyDamageToMember`, `applyMemberCondition`, `clearMemberCondition`,
   `hasMemberConditionImmunity`, `healMember`, `adjustMemberHealth`, `reviveMember`, `applyCharacterBuff`,
   `clearCharacterBuff`, `characterBuff`/`hasCharacterBuff` (the hireling's own `buffs`), `applyRecoveryToMember`,
   `reachableMaximumHealth`; so a spell's `targetCharacterIndex` may name a hireling (PartySpellSystem's character
   target checks use `combatant()`). Damage to a hireling (`applyDamageToHireling`) skips the members' shields, ruleset
   absorption and voices, clamps at 0 and sets Unconscious (`updateHirelingKnockOut`); a heal of any size clears it;
   Dead/Eradicated stay until `reviveMember`. Primary stats are `Party::Mm9HirelingPrimaryStat` (13, parameter bonus 0),
   so the shared formulas derive AC = row AC (`armorClassModifier`) + buffs, resistances = row + buffs, and luck adds
   nothing to saves; saves of version 155 are migrated to it (`SaveVersionMm9Formation` 156). Buff bonuses:
   `rebuildMagicalBonusesFromBuffs` now applies the party buffs and a character's own through `applyPartyBuffBonuses`
   and `applyCharacterBuffBonuses` (one owner, members and hirelings), and `applyBuffBonusesToHirelings` (no items,
   skills, class or followers). `advanceTimedStates` ticks the hirelings' buffs (Regeneration heals, Haste ends in
   Weak, the party Haste's weakness too); `updateRecovery` ticks their recovery (`recoveryProgressMultiplier`);
   `restAndHealAll` wakes and heals them (Dead stays), `reviveAndRestoreAll` restores them. Party-wide loops that
   now include hirelings: `applyDamageToAllLivingMembers`, the monster combat's `affectsAllParty` hits
   (GameplayCombatController), Hour of Power's Bless, Bless (Expert+), Preservation (Master+), Hammerhands (GM),
   Pain Reflection (Master+), Awaken, Power Cure, Divine Intervention. Not: experience (`grantSharedExperience` loops
   the PCs), inventory, skills, Shared Life, Soul Drinker, Glamour, environment damage (water, burning floors), event
   damage (`evt.DamagePlayer`), temples.
4. **Actions.** The active-member rotation runs over PCs then hirelings. A hireling active: Attack and quick cast use its
   attack (attack 1 in reach, attack 2 beyond, skipped without one) or, for the casters, one of its two spells (use
   percent picks), at the crosshair target, from the party's position, with no mana; then its recovery. Inventory,
   spellbook, character screen and the other PC screens ignore hirelings. Turn-based: hirelings are in the turn order.
   **Done.** `Party::activeCombatantIndex()`, `activeHireling()`, `setActiveCombatantIndex()`; `activeMember()` stays
   the last active PC, so every PC screen keeps working while a hireling acts; `setActiveMemberIndex` (a portrait
   click) leaves the hirelings' turn; `switchToNextReadyMember` cycles all combatants (identical without hirelings);
   removing the active hireling hands the turn back. `executePartyAttack` (GameplayActionController) hands an active
   hireling to `executeHirelingAttack`: the action from `chooseMm9HirelingAction` (game/mm9/Mm9HirelingCombat), a blow
   or Arrow rolled with the monster rules (`rollMm9HirelingAttackDamage`, `mm9HirelingAttackHits`: row dice, level;
   Heroism/Hammerhands/Bless on top) and landed through the party's melee damage (`resolveMeleeAppliedDamage`,
   `applyPartyAttackMeleeDamage`) or missile (`spawnPartyAttackProjectile`, the hireling's combatant index as source);
   the casters through `PartySpellSystem::castSpell` with the row's skill and mastery, `spendMana`/`applyRecovery`
   false (castSpell's caster is a `combatant()`); then `Party::hirelingRecoverySeconds` (row seconds less haste ticks).
   Nothing in reach (no target, no attack 2): passed over. Quick cast with a hireling active falls back to the attack
   (`GameplaySpellActionController::tryBeginQuickSpellCast`). Turn-based: the queue's character entries are combatants
   (`MaximumTrackedMembers` 8), hirelings after the PCs, made active on their turn and waiting for the command.
   Hireling missiles and spells skip the rulesets' party hit effects; the HUD ignores their indices until phase 6.
5. **Monster targeting.** Hirelings are candidate targets like PCs (MM9 weights by formation row; the shared targeting
   gets them as members of the formation's last row unless the user wants otherwise).
   **Done**, with the formation cells of phase 10's party state. World capability `formations: true` (MM9 world.yml)
   -> `WorldManifest::formations` -> `GameSession::setFormations` / `GameApplication::bindPartyDependencies` ->
   `Party::setFormationTargetingActive`. `Party::formationCell(i)`, `setFormationCell(i, cell)` (empty cells only);
   members' cells saved as `Party::Snapshot::memberFormationCells` (save version 158; older saves get defaults),
   hirelings' in `Mm9PartyHireling::formationCell`; `normalizeFormationCells` gives every member and hireling without a
   valid cell the lowest free one (MM9 10.3: PCs 1-3 front, PC 4 middle-left, joiners next) on seed, restore,
   recruit, dismiss and hire. With the capability on, `chooseMonsterAttackTarget` uses `chooseFormationAttackTarget`
   (d10 rank 70/20/10, d3 cell, rerolls for empty cells and fallen members, nobody once every PC is down; seeded by the
   existing selection seed); off (MM6-MM8) the old path runs untouched. The combat controller's monster-hit path reads
   the target through `combatant()` (hit roll, shields, conditions, pain reflection, log; MAW's boss-affix hit effects
   too). MAW's own target rules
   (Fixator, cover, random-target missiles) still choose among the PCs.
   Tests: `tests/Mm9HirelingCombatTests.cpp` (knock-out and wake, AC/resistances, party and personal buffs, no
   experience, rotation, recovery, attack choice, dice, caster cast without mana, Power Cure/Bless/Heal on a hireling,
   formation defaults and 70/20/10 targeting, MM6-MM8 targeting unchanged, turn-based order), `tests/RulesetTests.cpp`
   (version 155 saves). Open: temples curing a dead hireling, MM9's rule that a party with every PC down is defeated
   (the defeat itself is the existing party-death path), hireling missile visuals beyond the Arrow, the formation's
   attack-direction rotation (columns/rear first) (the builder screen: phase 10, done), a headless MM9 scenario.
6. **HUD.** The right-edge rail (revision 2): the basebar's panel, up to three slots, face animation on the `9npcNN-`
   family, HP arc, aggro diamond with recovery arc, buff medallion, greyed when down. Click: make active; a second click
   or double click: its dialogue. Held RMB: inspection (HP, AC, resistances, attacks, spells, conditions, buffs). The
   combat-log and followers buttons hidden in MM9 and in the Standard ruleset (a setting can show the combat log).
   **Done** (2026-11-06; captures `level_generation/ui/mm9_hirelings_20261106/native/`). Layout: `gameplay.yml`
   `Mm9HirelingRail` (top right, y 178, 70 wide, height for three) and its slots `Mm9Hireling1-3` (8-unit band, 58
   units, 60 apart) with `Face`, `Rim`, `Selection`, `Health` (meter arc 100/160, 3.6), `Readiness` and
   `PersonalBuffs` children, the study's numbers. `GameplayUiRenderer` `renderMm9HirelingRail` draws it after the
   party portraits on the plain HUD (not on the fullscreen screens): `GameplayUiSkin::renderPanel` (border 0.75) ended
   8 units under the last live slot (`mm9HirelingRailPanel`, game/mm9/Mm9HirelingHud), the faces through the members'
   portrait animation (`syncPartyConditionPortraits`, `updatePartyPortraitAnimations`, `playPortraitExpression` and the
   party-wide face reactions now run over the combatants, so damage, conditions and idle frames play; portrait spell
   effects use the combatant index), greyed while it cannot act, a dead or eradicated hireling with its own face
   greyed (not the members' tombstone), rim strokes and the selection diamond at 34/47.52 of the party's, the
   readiness diamond and recovery ring (`renderPortraitReadiness`, shared with the party's), the HP arc with the
   members' damage trail (`updatePortraitHealthTrail`; `GameplayPortraitPresentationState::meters` holds 8). The
   selection follows `activeCombatantIndex()` on the plain HUD (an acting hireling takes it from the PC), the
   fullscreen screens keep the last active member. Input: `GameplayScreenRuntime::resolveHirelingSlotRect` and
   `resolveCombatantPortraitIndexAtPoint` (party portraits, then the slots, `mm9HirelingRailSlotAt`) feed the portrait
   clicks (`GameplayHudInputController::activateHirelingPortrait`: select, or the dialogue on the active one or a double
   click, also for a hireling that cannot act; turn-based keeps the acting combatant as for members), the pending
   spell's portrait target in `GameplayInteractionController` and the held-RMB popup. Dialogue:
   `GameplayScreenRuntime::openHirelingDialogue(rudeId)` (`openMm9RudeDialogue`, then presented). Inspection: the
   members' popup (`CharacterDetailOverlayState::statLines`): name, level, HP, AC, condition, attacks
   (`formatMm9HirelingAttack`: dice, damage type, missile), spells (name, mastery, skill), resistances (the six schools
   with buffs; Spirit, Light, Dark and Physical are not shown: the shared damage rules take Spirit as Body and give the others none, so the row's values never count, open for the combat rules), personal buffs. Party stat buffs (Day of the Gods, stat potions) give hirelings no primary-stat bonus (`applyBuffBonusesToHirelings`), so they no longer raise a hireling's armour class through speed. Combat log: the `combat_log` setting is now Auto / On / Off
   (`CombatLogMode`; INI `true` reads as auto, `false` as off); Auto shows and records it in a ruleset other than
   Standard in a world with world.yml `combatLog` (new, default true; MM9 `false`), `GameplayScreenRuntime::
   combatLogShown()`; headless scenarios force On. Debug console: `hireling list | add | remove | active | talk | hp |
   recovery | buff | condition` (add sets the hire key as phase 7's hire will). Tests: `tests/Mm9HirelingHudTests.cpp`
   (revision 2 geometry from gameplay.yml, panel height, hit testing, attack/spell text).
   Open: Android (the rail at y 178-372 meets the right touch group: the flight arrows at y 156-200, the context popup
   over Attack/Spell at about y 304-346 and the Attack/Spell pair's top at 360; not redesigned, the rail draws there
   unchanged); hirelings say nothing (no voices), so no talking mouth frames; MM9's keys 5-7 to talk to a hireling are
   not bound (the number keys stay the members'); the formation button for the free row: phase 10, done.
7. **Dialogue services.** RUDE -10 hire (at most two paid plus one story companion; fee; not enough gold: the PC's voice
   line; hire key 450-462), -11 dismiss (key removed, the world object returns), -15 the hireling's service (Town Portal,
   heal, heal and cure; once a day), the passives (gold +20 %, experience +10 %, identify and repair always succeed,
   skill bonuses), the wage every 28 days (unpaid: the purse emptied, that retainer leaves).
   **Done.** `game/mm9/Mm9HirelingServices.{h,cpp}`: `hireMm9Hireling` (refused when `canAddHireling` fails, MM9's
   error sound and no message; `NotEnoughGold` without the fee, story companions free; else the fee charged with the
   gold sound, the hireling added, its table `hire_qbit` set), `dismissMm9Hireling` (removed, the key always cleared),
   `useMm9HirelingService` (`TownPortal`, `Healed`, `CoolingDown`, `Unavailable`; the cooldown is
   `Mm9PartyHireling::serviceReadyGameMinutes`, 24 game hours after use, saved), `mm9PartyHirelingPassives`,
   `payMm9HirelingWages`. RUDE rows (`GameplayDialogController`, `executeMm9HirelingRudeRow`, before the row's key
   tail is applied, so a refused hire changes nothing): -10 for the dialogue's RUDE id (no table row, Huber: error
   sound): not enough gold says "You don't have enough gold." and the active member's NotEnoughGold line, the talk
   goes on; hired: the row's own keys (Forad's 29, 371), the speaking actor hidden at once (`hideMapActorByIndex`,
   as MM9's server, `object@0x100b6bd3`; the converted maps' load handlers keep it hidden while the key is held and
   show it again after a dismissal on the next load, as MM9), "<name> joins the party.", the RUDE exit callback (the
   Isle's Forad: 368 and 4 000 experience) and the dialogue closes. -11: removed, key cleared (the row's tail clears
   it too), "<name> leaves the party.", closes. -15: Ehwaz opens the shared Town Portal destination choice (the Gate
   Master's overlay: Grandmaster, no mana, no recovery) and closes; Sowelu and Florie heal every member and hireling
   to full HP (`healMember`: wakes knocked-out hirelings and PCs, the dead stay dead; Florie also clears her table
   conditions, Sowelu none, as MM9) with the heal sound and the conversation goes on with the response; cooling: the
   status "%s can cast this but once per day!" (fizzle for the healers). The service tag is now "Service".
   Passives (`Party::mm9HirelingPassives`, from `Party::setMm9HirelingTable`, bound in `bindPartyDependencies`):
   Edina's +20 % in `resolveFoundGold` (now takes the party): world gold, chests and corpses; not shop sales, quest
   rewards (`MM9.giveGold`) or the bank, since MM9's callers were not traced; Cleirach's +10 % in
   `grantSharedExperience` (kill experience before the split; not script `GiveExp`); identify and repair always
   (`canIdentifyItem`, `canRepairItem`); Alberik's and Beagan's skill bonuses through the members'
   `hiredNpcSkillBonuses` in `rebuildMagicalBonusesFromBuffs` (derived, not saved; only on a skill the member has;
   gone on dismissal). Wages: `payMm9HirelingWages` runs after every game-time advance (both world runtimes'
   `advanceGameMinutes`), each paid retainer every 28 days from its hire, every period passed (a long voyage pays
   them all), wages due together in MM9's order (rows 279, 280, 281, 282, 284, 285, 286, 288, 289, 290, 291, 283,
   287); unpaid: the purse to 0, that retainer leaves with its key cleared (not MM9's bug), the first member able to
   act says NotEnoughGold (no message, as MM9). The gold share is never deducted. Debug: `hireling talk` opens any
   table hireling's dialogue; `hireling remove` dismisses (key cleared).
8. **Story companions.** Forad joins on the Isle of Ashes (key 29) and leaves at the council; Tamur joins by script
   (key 190). The converters' story scripts call the hireling add and remove.
   **Done** in code; the two maps need reconversion. Forad joins through his -10 rows (the hire service above, kind
   story: free, no wage). Lua: `evt.AddMm9Hireling(rudeId)` / `evt.RemoveMm9Hireling(rudeId)` (EventRuntime.cpp,
   `Party::addHirelingByRudeId` / `removeHireling`; return whether the party changed; keys untouched, the scripts set
   them as MM9's), wrapped as `MM9.addHireling` / `MM9.removeHireling` in `worlds/mm9/events/common/mm9_common.lua`.
   Converters: `mm9r_thronheimcity/citylua.py` `war()` calls `MM9.removeHireling(2)` (ARGUMENT.scr:202; key 29 stays,
   as MM9), `mm9r_frosgardcity/citylua.py` Tamur's dialogue exit calls `MM9.addHireling(309)` after key 190
   (NPC309.scr). Their Lua is written from the built map (actor indices), so it cannot be regenerated alone: **Thronheim
   City and Frosgard City need a reconversion** (`convert.py` of each) before the game sees these calls (not run: map
   conversions are on hold). The Isle of Ashes needs nothing (the -10 row and its story Lua's key-29 hiding).
   Tests (phases 7-8): `tests/Mm9HirelingServicesTests.cpp` on the world's `hirelings.txt` (hire, refusals, limits,
   fee; dismissal clears the key and allows a rehire; Sowelu's heal and cooldown through a snapshot; Florie's cures;
   Ehwaz's Town Portal cooldown; Edina's gold, Cleirach's experience, identify, repair, skill bonuses; wages paid,
   caught up, unpaid in MM9's order; story companions free and without wages, script add and remove). Headless:
   `tests/scenarios/mm9/hireling_tesar_hire_dismiss.yml` (rebuilt Sturmford City, `--asset-root
   output/mm9_rework/assets_dev`): Tesar refuses 400 gold, joins for 500 by a real click (key 451, his body gone at
   once), dismissed from his dialogue (key cleared); then Ake the Righteous by his prop's click event 304: his
   prop (cog 404) hidden at once (`assert: sprite_hidden`, a new scenario check).
   Talking props (follow-up, 2026-11-06): `evt.OpenMm9Rude` run from a decoration's click event records that
   decoration (`ISceneEventContext::decorationSpriteKeyForScriptEvent`: the one indoor or outdoor decoration whose
   script event it is, keyed as evt.SetSprite's overrides; `PendingDialogueContext::sourceDecorationKey`, kept for the
   open dialogue in `dialogueState.mm9RudeSourceDecorationKey`). A hire from that dialogue hides it as
   `evt.SetSprite(cog, 0)` does (`spriteOverrides`, saved with the map's event state); after a dismissal the map's load
   script shows it again. No reconversion needed. Test: `EventScriptingTests.cpp` (the decoration is recorded only
   for its own event).
   Open: the shared Lua `GiveExp`/`MM9.giveGold` and shop sales get no Cleirach/Edina bonus (MM9's callers untraced);
   whether boat and coach prices count hirelings (research section 6); a status message for a wage departure
   (MM9 has only the voice line); the Lua of Thronheim and Frosgard City until their reconversion.
9. **Checks.** Unit tests per phase; MM9 scenarios (hire, fight, knock-out and wake, service once a day, wage, dismiss,
   save/load); MM6-MM8 regression (unit tests, tests/scenarios) after phases 2-6.

## Decisions (user, 2026-11-06)

- Hirelings are a representation of their own, separate from `Party::members()`, so nothing leaks into the MM6-MM8
  code paths.
- MM9's death rule: Unconscious at 0 HP, never Dead from damage, any healing wakes; Dead or Eradicated set by an
  effect: greyed, cured at a temple or by PC spells.
- **Formations (MM9 only):** monsters choose targets by formation row as MM9 (70 % front, 20 % middle, 10 % back).
  A button under the minimap (the MM9 world's, in the row of the hidden combat-log and followers buttons) opens a
  formation builder: a 3 × 3 grid onto which the PCs (and hirelings) are dragged. Phase 10 below; MM9's own formation
  screen is researched in MM9_HIRELINGS.md section 10.

## Phase 10: formations

Party state: a grid cell per PC and hireling (saved); MM9's default formation for new and joining members. The shared
monster targeting reads the row weights in the MM9 world only (elsewhere unchanged). **Party state and targeting done
with phase 5.** The builder: the accepted design `level_generation/ui/mm9_formation_20261106/` (2026-11-06): an
Obsidian overlay that pauses the game, portraits dragged onto empty cells, opened by the MM9 minimap button and a key.

**Builder done** (2026-11-06; captures `level_generation/ui/mm9_formation_20261106/native/`).
- Rules: `game/mm9/Mm9Formation.{h,cpp}`: `mm9FormationMove` (only onto an empty cell, no swap; an occupied cell, the
  own cell or an invalid one changes nothing: the face returns), `mm9FormationFrontLineCovered` (nobody behind an empty
  cell of the same column; an empty column is fine), `mm9FormationOccupant`, the grid's hit testing
  (`Mm9FormationGrid`, `mm9FormationCellRect/CellAt`) and the open builder's state (`Mm9FormationBuilderState`, in
  `GameplayOverlayInteractionState::formationBuilder`). `Party::formationCells()` / `setFormationCells(cells)` read
  and apply the whole arrangement at once (one valid, distinct cell per combatant, else nothing changes). The defaults
  are phase 5's `normalizeFormationCells` (the builder opens on the party's cells).
- Screen: `assets_dev/engine/ui/gameplay/mm9_formation.yml` (screen `Mm9Formation`, the study's numbers in the
  centred 640 x 480 frame: panel 330 x 334 at 155, 38; grid 174 x 210 with 54 x 66 cells 6 apart; faces 40 x 54; the
  rank names and 70 / 20 / 10 % lines; instruction, refusal, Cancel / Accept `obsidian_button_tab_*`, tooltip style),
  drawn by `game/ui/GameplayFormationBuilder.{h,cpp}` from the overlay orchestrator after the loot summary: a 45 %
  black shade over the whole screen (HUD included), `GameplayUiSkin::renderPanel` (border 0.75), Fondamento texts,
  recessed cells (an empty one dashed, the drop target gold), each combatant's face through the members' portrait
  animation in a brass ring (greyed while it cannot act; a dead one keeps its face), the brass diamond in a
  hireling's cell, the name of the face under the pointer, the dragged face (5 % larger, shadowed) under the pointer.
- Input: `GameplayFormationBuilder::handleInput` from `GameplayScreenController::gateStandardWorldInput` (the loot
  summary's place: the world is blocked and paused; `GameSession` counts it as a modal overlay, so portraits, HUD
  buttons, quick items, quick cast, the world's hover text and indoor picking are off). Press on a face takes it,
  release over an empty cell drops it there, anywhere else it returns; Cancel and Accept act on a release over the
  button they were pressed on. Accept: refused (`SoundId::Error`, the instruction line becomes the refusal, stays
  open) while someone stands behind an empty cell; else `setFormationCells` and closed. Cancel, Escape and the
  formation key again close it without applying; a map move closes it.
- Opening: `gameplay.yml` `Mm9FormationButton` (top right, -4, 148, 24 x 24: the followers' place, hidden in MM9; the
  combat log's button, when the setting shows it, stays at -28), a carved slab (green-black gradient, brass border,
  gold on hover or while open) with a 3 x 3 grid of brass diamonds, the front rank larger and gold, drawn with HUD
  quads (`GameplayFormationBuilder::renderButton`, in `renderGameplayHudArt` on the plain gameplay HUD); a HUD pointer
  target `FormationButton`. Key: `KeyboardAction::PartyFormation` (`party_formation`, "Party formation (MM9)" in the
  settings' key list, Party & books). **F is OpenYAMM's Attack key** (MM9 opens the screen with F), so the default is
  **O** (MM9's art is `PARTYORDER*`); a player can bind F in the MM9 world's game if they move Attack. World gate:
  `Party::formationTargetingActive()` (world.yml `formations: true`), the same capability as the targeting: no
  button, no key, no builder in MM6-MM8.
- Android: the button is a touch control (`mobileTouchControls`, HUD role); while the builder is open one full-screen
  HUD control takes every touch, so a finger drags a face (the shared touch-to-pointer path: press, held motion,
  release at the drop point) and nothing moves or turns the camera under it. Not run on a device. The button
  (y 148-172) sits just above the right touch group's flight arrows (y 156-200 at their reference scale, shown only on
  an indoor ladder in MM9, which has no Fly), so the two may touch at some aspect ratios; not redesigned.
- Debug: `hireling formation [open|cancel|accept|show|move <combatant> <cell>]` (move edits the open builder, else the
  party).
- Tests: `tests/Mm9FormationTests.cpp` (defaults for five members and three hirelings, drop rules, the front-line
  rule, the whole arrangement applied and saved, a joiner after a dismissal, the design's geometry from the YAML).
- Open: the formation's attack-direction rotation (MM9 10.2, columns or rear first for two monster-AI callers);
  MM9's party-defeat rule; keyboard-only placement (MM9 has none); the rail's own touch overlap (phase 6).
