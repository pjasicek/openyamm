# STD2: Standard regressions in potions, alchemy, items, houses/shops/training, skills UI, HUD and screens

Baseline: git HEAD 7fdb25667. Code read only; nothing built or run. Three parts: core (potions, alchemy, items, houses, dialogs, input), menus/settings, character/inventory/HUD UI.

## Approved Standard changes (not findings)
- GAPS A7.2: quick-cast/attack heal targeting shared by both rulesets (verified as implemented for Heal; a cure-target nuance is STD2-4).
- GAPS D.5: Carnage arrows explode in Standard (ExplosiveArrows flag in ItemEnchantRuntime).
- GAPS D.7: 10 complex item picture cells in the engine table.
- GAPS D.8: Monster scaling row keeps its place; ruleset_desc only in ruleset games.
- GAPS D.18: MAW bindings group listed only in MAW games (verified).
- GAPS D.19 / N8.1 / N8.4 / N8.5: map and dragon-hatchling base fixes.
- Continent screen ruleset switch layout (user approved 2026-10-23, level_generation/ui/ruleset_choice_20261023).
- Unclear approval (flagged in findings): combat log in Standard (STD2-M1), bench Enter/Delete keys (STD2-2), Load/Save ruleset filters (STD2-M2), quick-reference fitting (STD2-U3).

## Core sub-slice: potions, alchemy, items, houses/shops/training, dialogs, input

### STD2-1: Re-drinking a once-per-character potion now says "Can't benefit anymore" in Standard
Severity: P3
Confidence: confirmed (read both sides)
MAW: n/a (Standard regression)
OpenYAMM: `game/items/InventoryItemUseRuntime.cpp:1285-1287`. When an Essence (272-278), Potion of the Gods (283) or
Pure Resistance (284-289) potion is refused because the character drank one before, the status is the new
"Can't benefit anymore". HEAD (`git show HEAD:game/items/InventoryItemUseRuntime.cpp:1124`) returned
`itemCannotBeUsedStatusText`, i.e. "<item name> can not be used that way". `SpeechId::PotionFail` and keeping the
potion are unchanged.
Not covered by: no related row (DEVIATIONS, GAPS §7 checked).
Suggested fix: return `itemCannotBeUsedStatusText(*pItemDefinition)` for NoBenefit when the potion has no best-step
effect, or let the potion table give the refusal text so MAW keeps its wording.

### STD2-2: Enter, Shift+Enter and Delete now act on the Standard Alchemy bench
Severity: P3
Confidence: confirmed (read both sides); Standard approval unclear
MAW: n/a (an OpenYAMM convenience from CRAFTING_BENCH_DESIGN.md §7)
OpenYAMM: `game/gameplay/GameplayAlchemyBenchInputController.cpp:561-576`. With the search field inactive, Enter (or
keypad Enter) presses Mix, Shift+Enter Mix All, Delete Clear. This path runs for every ruleset; only the Tab switch
is gated by `GameplayCraftingBenchView::available`. HEAD's `handleInput` ignored these keys outside the search field.
Delete is also a default gameplay binding (`KeyboardBindings.cpp:63`), and Enter another
(`KeyboardBindings.cpp:33`); on the bench they now brew.
Not covered by: GAPS L7.4 records the keys as done but does not say the user approved them for Standard games.
Suggested fix: ask the user. If they are MAW-only, gate the block with `GameplayCraftingBenchView::available(context)`
(as the Tab switch is); if wanted in both, note the Standard change in L7.4.

### STD2-3: Overlay hover texts (Town Portal, Dimension Door, Lloyd's Beacon) are no longer cleared by the world and can stay on the status bar
Severity: P3
Confidence: plausible (needs a runtime check)
MAW: n/a
OpenYAMM: `game/gameplay/GameplayInteractionController.cpp:1067` (`clearWorldInteractionFrameState`) and `:2076`
(`setWorldStatusBarHoverText`), `game/outdoor/OutdoorGameView.cpp:4473`, `game/ui/GameplayUiController.cpp:636-646`.
HEAD cleared the whole hover text each frame from the world (`setStatusBarHoverText("")` or
`clearStatusBarHoverText()`). Now the world clears only text it set itself (`hoverTextFromWorld`). The utility
overlays set hover text with `fromWorld = false` (`GameplayPartyOverlayInputController.cpp:922, 1066, 1081, 1086`). If
an overlay closes while it shows such a line (a click that sets a beacon, recalls or portals, or Escape), nothing
clears it: the world's empty hover only calls `clearWorldStatusBarHoverText`, so "Set beacon to ..." or "Town Portal
to ..." can stay on the gameplay status bar (`GameplayHudRenderer.cpp:428`) until the pointer passes over a named
world object. The change was made for the MAW skills-page cost hover and the rarity label.
Not covered by: no related row.
Suggested fix: clear overlay-owned hover text when the overlay closes (reset in
`resetUtilitySpellOverlayInteractionState` and the overlay close paths), or have the world clear any hover text on
the first unblocked frame after an overlay closes.

### STD2-4: The shared quick-cast rule (A7.2) can aim a cure at a dead, petrified or eradicated member in Standard
Severity: P3
Confidence: confirmed (read both sides); question for the user
MAW: `zzClasses.lua:238-257` (per A7.2)
OpenYAMM: `game/party/PartySpellSystem.cpp:3097-3227` (`quickCastCharacterTarget`, `withCondition`). For Remove
Curse, Remove Fear, Cure Paralysis, Cure Insanity, Cure Weakness, Cure Poison and Cure Disease it picks the member
with the condition and the lowest HP share, without skipping the dead, petrified or eradicated. A dead member's share
is 0 or below, so a dead cursed member wins over a living cursed one and the quick cast is spent on the corpse. HEAD
(`git show HEAD:game/gameplay/GameplaySpellService.cpp:260-278`) never chose those members (and aimed every
character spell at the wounded member with the least HP). The heal branch does skip them, as A7.2 says.
Not covered by: GAPS A7.2 (approved Standard change) says "cures go to a member with their condition" but does not
say whether the dead count.
Suggested fix: skip `beyondHealing` members in `withCondition` for the cure spells (keep it only for Raise Dead,
Resurrection and Stone to Flesh), and add that to A7.2.

## Observed, not attributable to MAW (out of scope, for the user's attention)
- `game/gameplay/GameplayScreenRuntime.cpp:1546-1566`: a Heal rest now sets `Asleep` on every member who is not dead,
  petrified or eradicated at its start ("sleep portraits"); `restAndHealAll` clears it at the end. No MAW document
  mentions it; it changes Standard state during a rest (anything that reads conditions while resting).
- `game/gameplay/HouseServiceRuntime.cpp:1897`: the "Sold X for Y gold" text now names the removed item instead of
  `*pItem` after the item left the pack (HEAD read a pointer into the inventory after the removal). A fix, not a
  regression.

## Checked and matching (core)
Potions (`potion_effects.yml` + `PotionEffectTable.cpp` + `InventoryItemUseRuntime.cpp` vs HEAD's switch):
- Item id = potion id + 220 (`potion_settings.txt`), so HEAD's potion-id cases map one to one. Every drinkable id
  222-232, 234-235, 237-245, 251-262, 264-290 has an entry; non-drinkable 233, 236, 246-250, 263 are item actions
  only; the drinkable Catalyst 221 has no entry and fails with the same text and `PotionFail` as HEAD.
- Power `max(1, standardEnchantPower)`, no cap, no minimum, no charges (Standard `charges` 1, `currentCharges` 0 on
  potions), no combat recovery, no ready-member check: as HEAD.
- Duration 30 min x power for every timed effect (`per_power_minutes: 30`), and the "keep a longer active buff" rule
  (`applyPotionBuff`) unchanged; buffs still applied at Master with the drinker as caster.
- 222 HP 10+P, 223 SP 10+P, 253 HP 5P, 254 SP 5P (`restoreSpellPoints` clamp unchanged); cures 224, 225 (3 stages),
  226 (3 stages), 227, 237, 238, 239, 251, 262; 252 `clearAllRestorableConditions` (same list plus Paralyzed,
  Zombie).
- 228 Haste 5 unless Weak (still consumed when Weak), 229 Heroism 5, 230 Bless 5, 234 Stoneskin 5, 235 Water
  Breathing 5, 231 Preservation 3P, 232 Shield 3P, 240-245 and 255 stat boosts 3P, 256-261 resistances 3P.
- 264-270 +50 into permanent bonuses, not once-per-character (as HEAD). 271 Rejuvenation: clears positive magic age,
  else younger by max(1, ceil(P/10)). 272-278 essences +15/-5 (base, floored at 0), once; 275 the six -1 then +15
  Endurance, once. 279 Doom +1 base stats and base resistances, +5 years, repeatable. 280/281 seven/six 3P buffs in
  HEAD's order. 282 level modifier +20. 283 +20 base stats, +10 years, once. 284-289 +40 base resistance, once.
  290 party Protection from Magic power 3, skill 10, Grandmaster, caster = drinker, 30 min x P.
- Once-per-character bits (200000 + item id in `playerBits`) unchanged, so old saves keep their marks.
- `Party::applyCharacterBuff`, `applyPartyBuff`, `healMember`, `clearMemberCondition` are byte-identical to HEAD; the
  extra `rebuildMagicalBonusesFromBuffs` after a drink only recomputes derived bonuses (it also zeroes the regen
  accumulators, as every buff application already did).
- Drink sound, face animation, consumption and the held-item path (`GameplayItemService.cpp:630-655`) unchanged when
  `potionUsesLeft` is unset (always in Standard).
Mixing and alchemy:
- Recharge (233), Harden (236), weapon enchant potions (246 Flame, 247 Frost, 248 Poison, 249 Sparks, 250 Swift, 263
  DragonSlaying) now come from the table's item actions: same item ids, same kinds, same 30 min x P duration.
- Reagent into bottle: Alchemy level + reagent table power (`PotionRules::reagentPower`); catalyst power (both
  catalysts: max; else the held item's) and the target id change; `mixingAlchemyLevel` = trained level; explosions
  and failure levels untouched.
- Alchemy bench: `resolveAlchemist`, ingredient power, recipe notes (`allRecipesKnown` false), chain planner and the
  E/Escape keys behave as HEAD; the crafting tab and Tab switch are gated by `CraftingRules::hasCrafting` (false).
Items:
- Item generation: rare roll order and RNG draws (`ItemRules::rollsRareItem`), enchantment rolls
  (`ItemRules::rollEnchantments` is HEAD's code), plain items unchanged; shops now pass the party, which changes nothing
  with `allowRareItems = false` and Shop mode.
- Item value, display name, enchant effects, drop permission, special enchant parsing (the four HEAD junk rows after
  the blank line in `special_item_enchants.txt` had zero weights; none of the ruleset suffixes match a Standard
  suffix).
- `InventoryItemUseRuntime` LearnSpell (`ClassRules::learnsSpellsFromBooks` true), scroll casts (`keepsScroll`
  false, `castSourceBuff` false, `partyBuffSeconds` nullopt), travel items (nullopt), open-from-drop workbench
  (`isMaterial` false).
Houses, shops, training, teachers, chests, followers, mercenaries, dialogs:
- Shop stock (`adjustShopStock` no-op), buy value (`shopBuyValue` = HEAD's value with minimum 1), merchant member and
  value (`merchantValue` nullopt), identify/repair multipliers, sell (`sellRefusal` nullopt, `itemSold` no-op),
  reroll button gated by `shopRerollCost` (nullopt).
- Training: experience check moved from `PriceCalculator::trainingPrice` to `trainingExperienceShortfall`, which runs
  before every `trainingCost` use; same 1000 L(L+1)/2, same cap (`trainingLevelCap` identity), same duration,
  `trainActiveMember` unchanged. Class name line uses `ClassRules::displayName` (className, else role).
- Mastery teachers: level 4/7/10 checks reordered with the same result; cost hook identity; teacher speech
  unchanged; skill id lookup uses the same first 40 ids.
- Temple donation, hireling and event buffs: `castSourceBuff` false; `questGoldBonus` 0; `mapResetOffer` nullopt;
  `followerHireRefusal` nullopt; follower skill bonuses still add (`followerSkillBonusesStack` true).
- Chests: placed item ids (`placedItemId` identity, no RNG draw), gold piles (`chestGoldAmount` nullopt, same
  fallback levels), random gold, loot filter (false), open refusal (nullopt); trap damage through
  `CombatRules::damageToCharacter`, whose only stage for a non-monster hit is HEAD's
  `resolveCharacterIncomingDamage` (it now also feeds the combat log, see the combat-log finding).
- Mercenaries: class kinds identity, skill points level x 5 - 5, the extra 8 skill names add no available skills
  (no Standard caps), `trimMercenaryItem` no-op, `offersMercenaries` true.
Input in Standard:
- New hidden key actions: Gather Loot (G) returns before doing anything (`lootGathering` nullopt); Alchemist (A)
  `pickAlchemist` nullopt; Cover (P) and Mana Shield (M) need the skill on the open skills page, so P (Adventurer's
  Inn) and M (map) work as before; Rotation (R) `toggleSpellRotation` nullopt; Unstuck, Open Workbench and Knight
  Charge have no default key. Spellbook R (`removeAllBuffs` nullopt) and Tab (`tabCyclesSpellbookSchools` false) are
  inert. Number keys 1-5 open bags only with `bagCount > 1`. Sort with Shift/Ctrl uses the HEAD path with one bag.
- Skills page: rows use the same group lists and order; labels `displaySkillName(canonical)` (no Standard
  overrides); raisable = skill points >= level + 1 (HEAD's `skillPoints > level`); the raise cost and the
  `lastStatus` message are HEAD's (empty `afterSkillRaised`).
- Quick spell status names `SpellRules::spellName` = the table name.
- A7.2 (approved Standard change) is implemented as written for Heal: the lowest share among members at or below a
  third, else the largest gain from `healAmount` (Standard: Heal's table amount), ties to the lowest share, never the
  dead, eradicated, petrified or whole; revivals target the dead; other member spells keep HEAD's lowest-HP rule.

## Menus and settings sub-slice

Scope: `game/ui/screens/MainMenuScreen.*`, `LoadGameScreen.*`, `NewGameScreen.*`, `assets_dev/engine/ui/gameplay/
settings_*.yml`, `load_game.yml`, `save_game.yml`, `continent_selection.yml`, `ruleset_rules.yml`,
`assets_dev/engine/ui/menu/settings_catalog.yml`, plus the call sites in `game/app/GameApplication.cpp` and the key
binding storage in `game/app/KeyboardBindings.cpp` / `GameSettings.*`. Compared with `git show HEAD:<path>`.

### STD2-M1: Combat log row added to the Interface settings of every game, and the log is on by default
Severity: P2
Confidence: confirmed (read both sides)
MAW: n/a (MAW GAPS H.3, an OpenYAMM feature request)
OpenYAMM: `assets_dev/engine/ui/menu/settings_catalog.yml:65-70` adds `combat_log` (no `ruleset:` or game-only
gate) to the Interface tab; `assets_dev/engine/ui/gameplay/settings_interface.yml` inserts the
`SettingsInterfaceCombatLog*` row above "Hit messages", moving every following row and the three group headers down by
38.9 units. `game/app/GameSettings.h:302` defaults `combatLog = true`, so a Standard game records hits
(`GameSession.cpp:1086`) and draws the `CombatLogToggle` HUD button (`GameplayUiRenderer.cpp:1176`).
The settings row and the button show in the main menu and in Standard games.
Not covered by: GAPS H.3 says "Native work TBD (deferred by the user)", and
`level_generation/ui/maw_combat_log_20261024/README.md:6` says the same. Neither says whether the log is for both
rulesets. Standard approval is unclear. (The parent STD2 file covers the HUD and the recording cost.)
Suggested fix: ask the user whether the log belongs in Standard. If not, gate the row with the game-only or ruleset
mechanism and gate the button and the recording on the ruleset. If it does, record that the user approved it in GAPS
H.3.

### STD2-M2: The Load and Save screens always show the All / Standard / MAW filter buttons, and each open rereads the ruleset packages
Severity: P3
Confidence: confirmed (read both sides)
MAW: n/a
OpenYAMM: `game/ui/screens/LoadGameScreen.cpp` `drawRulesetFilters` draws buttons when
`m_rulesetFilters.size() >= 2`. `refreshRulesetFilters` adds Standard plus every package that
`loadAvailableRulesets` finds. The `rulesets` package is mounted for every install (GAPS E.1), so a player who only
plays Standard always sees "All | Standard | MAW" in the Load and Save headers. Each time the screen opens (cached
list or not), `refreshRulesetFilters` parses every `rulesets/*/ruleset.yml` again (`LoadGameScreen.cpp`
`refreshRulesetFilters`, `loadCachedSaveSlots`). The badge row (`LoadGameSelectedRuleset`) is empty for Standard
saves, and the food-cost line is 0 under Standard's `MonsterRules::saveFoodCost`. Both match HEAD.
Not covered by: the behaviour is the plan in `devdocs/maw/README.md:331` ("they appear once a second ruleset is
installed or saved"). No row records that a Standard-only player sees them on every install. Approval of the visible
Standard change is unclear.
Suggested fix: if the buttons should appear only for players with saves of more than one ruleset, count the
rulesets of the existing saves instead of the installed ones. Either way, cache the ruleset list once rather than
reparsing it on every open.

### STD2-M3: Character creation help popups are taller in Standard
Severity: P3
Confidence: confirmed (read both sides)
MAW: n/a
OpenYAMM: `game/ui/screens/NewGameScreen.cpp:3005`: `height = bodyTop + 40 * scale + ...`. HEAD had `28 * scale`.
This applies to every creation help popup (skill, class, stat), so each Standard popup gets 12 scaled units of empty
space at the bottom. MAW's skill matrix is added as mastery lines, which have their own height terms, so nothing in
Standard needs the extra space.
Not covered by: no related row (DEVIATIONS and GAPS checked; nothing about creation popups).
Suggested fix: restore 28, or keep 40 only when the rules add lines (for example
`creationRules().classes.showsCreationSkillMatrix()`). If it fixes clipping seen in Standard, say so in a comment.

## Notes, not findings
- Hidden MAW key actions keep their default keys in Standard games: Gather Loot G, Alchemist A, Cover P,
  Mana Shield M, Rotation R (`KeyboardBindings.cpp:78-93`). Their rows are left out of Standard's Keyboard page
  (`MainMenuScreen.cpp` `loadCatalog`, `listed`). Conflict detection compares only listed rows of the same context,
  so binding a Standard action to G, P, M or R raises no conflict, the same as HEAD. Both actions then share the key
  in play. That matters only if the hidden actions are not inert in Standard; the parent STD2 file checks that
  (`gatherLoot`, `pickAlchemist`, `toggleSpellRotation`, `skillSwitchForAction`). With the Classic control preset,
  Attack is A, which shares A with Alchemist. Alchemist acts only on the inventory page and is inert in Standard.
- When the MAW package is installed, Standard's continent screen shows the ruleset switch, and the continent cards
  are resized and moved (`continent_selection.yml`). The user approved this layout on 2026-10-23
  (`level_generation/ui/ruleset_choice_20261023/README.md:4`), so it is not a finding.
- Out of scope, not checked further: choosing New Game from the pause menu of a MAW game and then picking Standard
  calls `activateRuleset` from `NewGameScreen::selectContinent`. That reloads the data, clears the session and shuts
  down the renderer while the New Game screen is active.

## Checked and matching
- Settings tab bar in Standard: the `game` (Rules) section is skipped without `CurrentGame`. `CurrentGame` is passed
  only when `paused && !ruleset().isStandard()` (`GameApplication.cpp:10103-10109`). Tabs are drawn per loaded
  section id, so `SettingsXTabGame` is never drawn in Standard. Updates keeps its element and position (the Rules tab
  shares its slot, offset_y 361.38, and the two never appear together). The six other `settings_*.yml` files only
  add the unused Rules tab element.
- `ruleset_desc` (Monster scaling) applies only with `m_currentGame`. That is GAPS D.8, approved.
- MAW binding rows (`ruleset: maw`) are listed only when `m_currentGame->selection.id == "maw"` (D.18). The `found`
  check still covers them, so the catalog validation is unchanged. Standard conflict detection is unchanged (every
  listed Standard row has context "").
- `dirtyCount`, `settingEnabled`, Revert, Apply and Restore defaults behave as in HEAD for non-game sections.
  `applySettings` touches rulesets only with `m_currentGame`.
- settings.ini: the new actions are written only when they differ from the preset defaults
  (`settingsEntriesToSave`). Old files without them load the defaults, and parsing is unchanged. `compact_bags` and
  `combat_log` are new INI keys with defaults.
- Character creation in Standard: the skill choices use the fixed `OrderedSkillNames` (unchanged). Standard class
  tables give Cover, Mana Shield, Enlightenment and Retaliation no cap, so their availability is None. The class and
  race lists come from the Standard `character_selection.yml` (no `free_selection`), and `startingCasterClassId` and
  `availableAtStart` filtering are unchanged. The MAW class names in `CanonicalClassNames` need a ruleset class table.
  `getEffectiveCap` without `m_raceShiftWithoutClassCap` equals HEAD (the new `maxMastery` is unused there). The God
  Lich debug roster still gets exactly the 40 classic skills.
- Creation popups in Standard: `creationRules()` returns `standardGameRules()`. The skill tooltip text and mastery
  lines are the table's (same as HEAD). The class matrix is off (`showsCreationSkillMatrix` false) and race notes are
  empty, so there is no race card.
- New game hand-off: `NewGameOptions{continentId, preserveDebugLoadout, ruleset}` replaces
  `(continentId, godLichParty)`. The default `RulesetSelection` id is `mmerge`, and `activateRuleset` returns early
  when that ruleset is already active.
- Load/Save in Standard: with the All filter the rows equal HEAD's. The selection, keyboard and PageUp/PageDown
  mapping through `shown` is the identity. Without a filter the "No saved games" text is unchanged. The Load
  confirmation text is unchanged (`ExperienceRules::loadWarning` is nullopt). The save food cost is 0
  (`MonsterRules::saveFoodCost`), so there is no label and Confirm is enabled. The quick-save message is still
  "Game Saved!". The new `saveFolderSignature` cache check only adds a directory scan per open.

## Character, inventory, alchemy and HUD UI sub-slice

Scope: Standard (mmerge) regressions against git HEAD `7fdb25667` in the files listed in the sub-slice. Read-only code
comparison; nothing built or run. Not re-reported (known to the parent): the combat log button and panel shown in
Standard by default, Enter/Delete on the Standard alchemy tab, and the status-bar hover text world/overlay split.

### STD2-U1: Standard skill popups are now titled with the mastery suffix ("Sword Expert", "Fire Magic Grand")
Severity: P3
Confidence: confirmed (read both sides)
MAW: n/a (Standard regression)
OpenYAMM: `game/ui/GameplayHudOverlaySupport.cpp:785`: `overlay.title = row.label != displaySkillName(row.canonicalName) ? row.label : pEntry->name;`. The rows here come from this file's own `appendCharacterSkillUiRows` (`:353-380`), whose `row.label` is `displaySkillName(pSkill->name)` plus `" " + skillPageMasteryDisplayName(mastery)` for Expert and above. So in Standard, any skill at Expert, Master or Grandmaster gets a popup title like "Sword Expert", "Body Building Master" or "Fire Magic Grand". At HEAD the title was always `pEntry->name` (`git show HEAD:game/ui/GameplayHudOverlaySupport.cpp`, the same block). Normal-mastery skills are unchanged. The MAW intent fails here too, because this copy of the rows never calls `SkillRules::skillDisplayName`. So a class's renamed school would show only through the mastery-suffix accident.
Not covered by: no related row (GAPS L5.4 and the skill-tooltip work do not mention the title).
Suggested fix: compute the title from `gameRulesFor(party).skills.skillDisplayName(character, canonical)` and compare that with `displaySkillName(canonical)`, not with `row.label`. Or keep `pEntry->name` unless the rules rename the skill.

### STD2-U2: A Standard potion with power 0 now shows "Power: 0" in its item popup
Severity: P3
Confidence: confirmed (read both sides)
MAW: n/a
OpenYAMM: `game/ui/GameplayPartyOverlayRenderer.cpp:2731-2744`. The Bottle branch now also fires on `itemDefinition.hasPotionPower`, which `ItemTable::applyPotionSettings` (`game/tables/ItemTable.cpp:775-789`) sets for every potion id 1-70, catalyst included. At HEAD the branch needed `standardEnchantPower > 0`. A potion with power 0 fell through and showed no detail line. Generated, placed and monster potions get a power (`ItemGenerator::assign*PotionPower`). Potions that keep 0 now read "Power: 0": event or quest `GiveItem` items, scenario or seeded items, the catalyst. Drinking still uses `max(1, power)`, so the popup is also misleading.
Not covered by: no related row (GAPS L7.5 covers MAW's potion popups).
Suggested fix: keep HEAD's `standardEnchantPower > 0` test for Standard. Show the zero-power line and the "Uses:" suffix only when the potion's rules call for it (`pPotion->charges > 1` or `minimumPower > 0`).

### STD2-U3: Quick-reference text fitting changed for every row in Standard
Severity: P3
Confidence: confirmed (read both sides); the visual size of the change needs a capture
MAW: n/a
OpenYAMM: `game/ui/GameplayPartyOverlayRenderer.cpp:3342-3354` (`renderQuickReferenceOverlay`'s `renderMemberRow`):
- The fit margin changed from `width - 8` to `width - 10` for all rows.
- The class row (`rowIndex == 2`) may shrink to scale 0.4 instead of clamping at 14/19 (HEAD clamped and cut long names).
- A new snap step lowers the scale by about 0.11 when a bitmap font would round up to a whole scale.

In Standard this shrinks some values that fit at HEAD, and long class names ("Priest of the Light") now render smaller instead of being cut. It was done for MAW's long class names. The comment calls it a rounding fix, but it changes the approved Standard overlay.
Not covered by: no related row.
Suggested fix: if it is wanted as a base fix, record it as an approved Standard change. Otherwise keep `-8` and the 14/19 floor for Standard.

### STD2-U4: Stats page class label widened from 145 to 240; long Standard class names now run under "Skill Points:"
Severity: P3
Confidence: plausible (needs a capture)
MAW: n/a
OpenYAMM: `assets_dev/engine/ui/gameplay/character.yml:261-273`: `CharacterStatsClassLabel`, a child of the 180-wide name label at x=20, so it starts at x=204. Its width went from 145 to 240. Labels clamp text to their width (`GameplayHudCommon::renderLayoutLabel`, `clampHudTextToWidth`). At HEAD the class text was cut at x≈349; it can now reach x≈444. "Skill Points:" is right-aligned and ends at x=416 (`CharacterStatsSkillPointsTextLabel`, top_right −52, width 140), and its value ends at x=443. A long Standard class, such as "the Priest of the Light" or "the Master Necromancer", can now overlap them. The skills page's `CharacterSkillsClassLabel` (`:1026-1038`) stays at 145, so the two pages disagree.
Not covered by: no related row (H.9 mentions widening only the value cells).
Suggested fix: check with a capture using a long class name. If it overlaps, keep 145 for Standard or move the skill-points labels, and give MAW names their own fit (shrink, as the quick reference does).

### STD2-U5: The monster inspect panel's Effects box now wraps and can grow the panel in Standard
Severity: P3
Confidence: confirmed (read both sides)
MAW: n/a
OpenYAMM: `game/ui/GameplayPartyOverlayRenderer.cpp:11014-11035` and `:11477`. In Standard, `effectRows` is the same single joined string as HEAD's `effectsText`. It is now drawn with `renderMultilineTextForLayout`, which wraps to the 120-unit box, one line per `dynamicStatLineAdvance`. More than 4 wrapped lines also grow the root (`extraLeftLines`). HEAD drew one `renderTextForLayout` label, clamped to the box width. A monster with several effects (Slow, Afraid, Bless, Haste, Casting X…) now shows them all, and the popup can get taller. It is a visible Standard change, though arguably a fix. The text, order and the "None" and "?" cases are unchanged.
Not covered by: GAPS H.2 (monster inspect) covers MAW's numbers, not Standard's wrapping.
Suggested fix: accept it as a base improvement and note it, or keep the single-line render when `rulesNumbers` is empty.

## Side notes (outside this sub-slice or not Standard regressions)
- `GameplayScreenRuntime::beginRestAction` (`game/gameplay/GameplayScreenRuntime.cpp:1545-1567`) now sets every living member Asleep when a Heal rest starts. This is a Standard behaviour change with no MAW document behind it, probably another session's work. If the rest is interrupted, members may stay Asleep. Worth a check by whoever owns rest.
- `game/ui/GameplayHudOverlaySupport.cpp:102-106` and the HP-arc personal-shield rim (`GameplayUiRenderer.cpp:622-645`) belong to the technology and energy-shields features, which are out of scope.

## Checked and matching (Standard identical to HEAD)
- Character overlay: skill rows use `skillSheetGroupSkillNames` (the same lists and order as HEAD's arrays). The label `skillDisplayName` gives `displaySkillName(canonical)`. `canRaiseSkill` (level+1 ≤ skillPoints, no cap) matches `skillPoints > level`. `skillRaiseCostDetail` is nullopt (no cost tag, unchanged name width). "(off)" never applies. The Technology header and its children are hidden unless the character has a technology skill, and `characterSkillsContentHeight` skips that region.
- Stats page: `statValueText`, `statRowText` and `statTooltip` are identity or nullopt. `ClassRules::displayName` matches HEAD's `displayClassName(className or role)`. `{run_deaths}` is empty. The HP, SP, AC, melee and ranged value cells grew 40 to the left but are right-aligned, so the right edge is unchanged; the only difference is less clamping of text wider than 85 units. The experience and training texts use `ExperienceRules::experienceForNextLevel`, the same formula as HEAD's `experienceRequiredForNextLevel`.
- Alchemy button label: `renderButton(..., &label)` with `label = pLayout->labelText` (`hasCrafting` false) draws the same as HEAD.
- Inventory: `InventoryBags` and `InventoryCompactBags` are reached only when `bagCount > 1` or `compactBagViewActive` (which needs `bagCount > 1`). Standard renders `pCharacter->inventory` on the full grid exactly as HEAD did. The held item's `compactBagFractionAt` returns 1. The bag, tab and compact-toggle elements are skipped by explicit `continue`s, have no id prefix collisions, and their hit tests are gated on `bagCount`. The rarity gem returns early (`nameColor` nullopt) in the inventory, chest and nested-overlay grids.
- Item popup: `baseStats` nullopt, so HEAD's dice and armour text is used. `enchantDescription` is `buildEnchantDescription`. `itemDescription` falls back to `notes`. `inspectLines` and `comparisonLines` are empty. The special-detail colour is the same `pDetailValueLayout->textColorAbgr`. The name is drawn uncoloured through `renderSingleLine`.
- Spell popup: `PartySpellSystem::manaCost`, using the same mastery and `SpellRules::manaCost` identity, equals HEAD's `spellInspectManaCostForMastery`. `spellTooltip` returns the table's name, description and mastery lines. The school name is unchanged. The quick-spell names (spellbook "Select X", quick reference, character detail) come from `spellName`, which is `spell.name`.
- Buff popups and HUD: `personalBuffName` and `formatBuffDuration` fall back to HEAD's names and durations (`heldBuffText` nullopt). `gameplayPotionEffectLines` is empty (the Standard potion_effects.yml has no timed potion effects). `gameplayUnslottedAuraLines` is empty. `portraitCounter` is "", and the counters are excluded from the generic layout pass (`obsidianpc` prefix).
- Minimap plates: `mapProgressText` and `deathPendingSeconds` are nullopt. The plate and timer are `visible: false`. `ObsidianMinimapProgress` has an empty label and no asset, so the generic pass draws nothing.
- Enemy health bars: `actorBadges` is empty. Monster inspect: `identifyMonsterReveal` gives the same best-member reveal (rulesetFacts are empty in Standard, so `pStats->level` is used). `inspectNumbers` is nullopt. The armour-class label moves only with `levelOffset = 0`. `monsterResistanceText` is the same "Imm"/number.
- Dialogue: `shopRerollCost` is nullopt. The reroll button is skipped in `renderDialogueTextureElement`, which covers both its texture and its label, and its input slot is gated on `canReroll`.
- Alchemy bench renderer: `GameplayBenchPainter` is a verbatim move of the old `BenchPainter`, with the same colours. The title stays "Alchemy Bench" and the Workbench tabs are hidden (`hasCrafting` false). The preview adds nothing at charges 1 and minimumPower 0. `itemDescription` is nullopt and there is no best-step ladder. The tab hit test is gated on `available`. The `AlchemyChainPlanner` and `ingredientPower` reagent power equal HEAD's (`PotionRules::reagentPower`, trained level).
- `alchemy_bench.yml`, `dialogue.yml`, `gameplay.yml`: additions only, no Standard element moved or resized. `CombatLogToggle` is not in the generic HUD pass (not a descendant of the listed bars). Of `character.yml`'s Standard elements, only the stat value cells and the stats class label changed (see U4).
- HUD font colour codes (`\f` + 5 digits): no Standard data or engine text contains `\f`, so measuring, wrapping and rendering are unchanged.

## Addendum to STD2-M1 (combat log in Standard)
- While the log is open, clicks over its panel and the mouse wheel over it are taken by the log
  (`GameplayHudInputController.cpp:345-351, 403-417`); in HEAD they reached the world/HUD.
- Standard damage that runs through `CombatRules` (including chest trap damage, `ChestRuntime.cpp:974-983`) is
  recorded with its stages every hit while the setting is on (the default).
