# STD4 (second pass): Standard regressions in files the first pass did not cover, plus the full rules-seam inventory

Baseline: git HEAD `7fdb25667`; released tags `v1.8`-`v1.10` checked for the updater. Read-only, nothing built, no
tests run. Method: (1) listed every changed or new file under `game engine editor tests android` (`git diff --stat
HEAD`, `git status -uall`; `android/` has no changes), marked the first-pass slice that covered it, and read the
uncovered diffs; (2) listed every virtual method of the nine rules classes, grepped every call site outside
`game/rules/` (`std4_methods.txt` beside this file), and checked the methods pass 1 did not name; (3) followed the
rulesets package through packaging, the asset mounts, the updater and the editor build.

## Findings

### STD4-2-1: Installed releases v1.8-v1.10 cannot self-update to the first release that ships the rulesets package
Severity: P2 (every player's self-update fails until they download the complete package; no gameplay effect)
Confidence: confirmed (read both sides: v1.10 and the working tree; not run)
MAW: n/a (packaging of the ruleset)
OpenYAMM:
- The new pack: `tools/runtime_packs.py:161-164` and `tools/packaging/packs.yml:34-38` give the `rulesets` package
  the mount `/rulesets/maw`. `packaging/publish_release.py:233-247` copies `package` and `mount` into each platform's
  release manifest.
- The installed updater parses that manifest with its own code: `AppUpdater.cpp:366` calls `parseReleaseManifest`,
  which runs `validateAssetPackRecord` on every pack (`engine/update/ReleaseManifest.cpp:246`).
- In v1.8-v1.10, `isPackageMount` accepts only `/engine` or `/worlds/<package>` (`git show
  v1.10:engine/AssetPackIndex.cpp:40`). For package `rulesets` it expects `/worlds/rulesets`, so `/rulesets/maw`
  fails.
- The parse therefore returns nothing, and the old game reports "The update server sent an unexpected release (pack
  ... mounts outside its package: /rulesets/maw)." (`AppUpdater.cpp:368-371`). This happens before the
  `min_updater_schema` check (`:374`), so even a schema bump would not show its friendlier "needs the complete
  package" text.
- The new `isPackageMount` (`engine/AssetPackIndex.cpp:41`) only helps builds that already have it.
Not covered by: GAPS E.1 (marked done 2026-10-24: "a `rulesets` package ... so the updater's index carries it"). The
row is incomplete: older updaters reject that index. DEVIATIONS 1-4 do not mention it.
Suggested fix: do one of these.
- Ship one release whose updater accepts `/rulesets` before any manifest lists a rulesets pack.
- Publish the ruleset files inside a mount that v1.8-v1.10 accept. One way is package `engine`, mount
  `/engine/rulesets/maw`, with the game reading rulesets from there.

Either way, add an old-updater manifest check to `packaging/test_publish_release.py`.

### STD4-2-2: The editor no longer links: the scene loaders call scene-overlay functions it does not build
Severity: P2 (the editor target; the main `build/` tree has `OPENYAMM_BUILD_EDITOR=ON`, so a full `cmake --build
build` fails at link; the game itself is unaffected)
Confidence: confirmed by reading CMake and the sources (not built; `build/editor/openyamm-editor` dates from 22 Oct,
before the new file)
MAW: n/a (ruleset scene overlays, "rulesets that edit a map without copying it")
OpenYAMM:
- The editor compiles `game/maps/IndoorSceneYml.cpp` and `OutdoorSceneYml.cpp` directly (`editor/CMakeLists.txt:31,
  35`) and links only `openyamm_engine`, imgui and yaml-cpp (`:77-82`).
- Both files now call `applySceneActorOverrides` and `readSceneRemovalPosition`:
  - `IndoorSceneYml.cpp:1518`;
  - `OutdoorSceneYml.cpp:2963, 3007`;
  - `applySceneSpawnRemovals` in the header calls `readSceneRemovalPosition`.
- These two functions are defined only in the new `game/maps/SceneOverlayOperations.cpp`. That file is in
  `game/CMakeLists.txt` and `tests/CMakeLists.txt:210`, but not in the editor's source list.
- Another session already added the three monster add-on tables to the editor list (`MonsterShields.cpp`,
  `MonsterModifiers.cpp`, `MonsterRelationAddOns.cpp`). The overlay file was missed.
Not covered by: no related row (HANDOFF §6 does not mention the editor).
Suggested fix: add `${CMAKE_SOURCE_DIR}/game/maps/SceneOverlayOperations.cpp` to `editor/CMakeLists.txt`, then build
the editor target once.

### STD4-2-3: The SetTexture face-key change (extends and corrects STD3-6): HEAD already swapped the MM6 face, old saves lose their swaps, and MM7/MM8 no longer swap a stray face
Severity: P3
Confidence: confirmed for the code and the map data (scripted scan of every BLV with SetTexture calls); the save effect
is plausible (needs a load of a HEAD-era MM6 save)
MAW: n/a (Standard map fixes, GAPS N8.x / §11 D.19)
OpenYAMM:
- What HEAD did:
  - At HEAD, `resolveFaceTextureName` tried three keys for every face: its face index, `cogNumber` and
    `textureFrameTableCog` (`git show HEAD:game/indoor/IndoorRenderer.cpp:1819`).
  - The HEAD MM6 scripts called `evt.SetTexture(2011, ...)` (HEAD `6d01.lua:163`). Through the face-index key, that
    already swapped face 2011.
  - My scan (`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/ff95062f-c7c8-4a63-bccd-089ec5bf6da6/scratchpad/std4/settex.py`)
    of all 228 MM6 calls found no face whose cog or frame-table cog matches
    the number. So for a new MM6 game the visible result is the same as at HEAD. STD3-6's premise ("At HEAD the same
    calls targeted cog number 2011") misses this: HEAD swapped the right face by accident.
- What changed (`IndoorRenderer.cpp:1818-1822`, `EventRuntime.cpp:8288-8299`):
  - The renderer now tries only `0x80000000 | faceIndex` and `cogNumber`.
  - Negative references are stored under the face key.
- Effects in Standard:
  - **HEAD-era MM6 saves (v≤94).** Their `textureOverrides` hold the old positive keys (saved in `EventRuntimeState`,
    `SaveGame.cpp:2600`). The new renderer reads a positive key as a cog number, and no MM6 face has that cog, so
    levers and switches pulled before the update show their original texture after loading. This lasts until the
    event runs again, unless the map's OnLoad event re-applies the swap. The mechanism and map-variable state is
    unaffected, so a lever can look unpulled while its door is open.
  - **MM7/MM8 (42 + 178 positive calls).** HEAD also retextured the face whose index equals the cog number, which was
    unintended, e.g. face 1 for `SetTexture(1, ...)` in 7d08. That no longer happens: 70 (map, cog) pairs changed by
    exactly that one face, and 7d17 cog 3, 7d29 cog 1, 7d30 cog 15, d03 cog 15 and d05 cogs 10/11 swapped only that
    face. This is a fix matching OpenEnroth (cog only), but it is not recorded.
  - **Frame-table cog.** Dropping `textureFrameTableCog` changes no face in any scanned map.
- Also new and Standard-visible (fixes): `ensureIndoorSwapTexture` loads a swapped-in texture that the map does not
  use (`:10509-10551`), and a surface revision change now rebuilds the batches in the same frame (`:3890-3898`) instead
  of waiting for a door.
Not covered by: STD3-6 (asks for approval of the MM6 change only), GAPS N8.5.
Suggested fix: record the MM7/MM8 stray-face removal and the immediate rebuild as approved Standard fixes next to
N8.5/D.19. Correct STD3-6's description. Add an explicit save migration for MM6 maps: when loading a save older than
the change, re-key positive `textureOverrides` of `worlds/mm6` indoor maps to `indoorFaceTextureOverrideKey`. AGENTS.md
asks for explicit migrations rather than fallbacks.

### STD4-2-4: On Android the combat log, on by default in Standard, sits on the touch controls (extends STD2-M1)
Severity: P3
Confidence: plausible (layout arithmetic only; needs an Android capture)
MAW: n/a
OpenYAMM:
- The combat log is on by default on every platform (`GameSettings.h:302`, `combatLog = true`). Its toggle is drawn
  whenever the setting is on (`GameplayUiRenderer.cpp:1175-1184`), with no Android branch.
- **Toggle against the flight buttons.** `CombatLogToggle` (`assets_dev/engine/ui/gameplay/gameplay.yml:1646-1651`:
  top_right, -28/146, 26×26, screen space) spans x W-54…W-28, y 146…172 in layout units.
  - The Android flight panel (`touch_controls.yml:101-131`: top_right, -32/156, 96×44, same scale range) spans x
    W-128…W-32, y 156…200. Its Fly Down button covers x W-76…W-32.
  - Outdoors with Fly active, the toggle therefore overlaps the top of the Fly Down button by about 22×16 units.
- **Panel against the system column.** When open, the docked panel (`gameplay.yml:1674-1680`: bottom_left, 8/-112,
  280×160) spans x 8…288, y H-272…H-112.
  - The Android lower-left column (`OutdoorMobileSystemPanel`, 24/-16, 80×256) has Inspect and Inventory at x
    24…104, y H-272…H-104.
  - While the panel is open, clicks over it are taken by the log (STD2-M1 addendum), so it covers those two thumb
    buttons.
- Android keeps desktop-only features off elsewhere: compact bags are disabled on Android
  (`GameplayHudOverlaySupport.cpp` `compactBagViewActive`).
Not covered by: STD2-M1 (desktop settings and default only), no GAPS row on Android placement.
Suggested fix: on Android, default the log off or place its toggle and panel clear of `touch_controls.yml`. At least
move the toggle off the flight panel's rectangle.

### STD4-2-5: The "Item rarity glow" Interface row also shows in Standard games, where it does nothing (extends STD2-M1)
Severity: P3 (cosmetic; one more inert setting and INI key)
Confidence: confirmed
MAW: n/a
OpenYAMM:
- `settings_catalog.yml:122-127` adds the row `rarity_glow` (group "Items") to the Interface section with no
  `ruleset`/`game_only` gate. `settings_interface.yml` lays it out as Group4 at y≈470-512 for every game.
- `GameSettings.cpp:997-1003, 2272` add the INI key `gameplay.rarity_glow`.
- In Standard, `nameColor` is always nullopt, so the toggle has no effect
  (`GameplayHudOverlaySupport::renderItemRarityGlow:1336-1344`).
- The study (`level_generation/ui/maw_hints_rarity_20261024/README.md:67`) says "it changes nothing in rulesets without
  rarities", but no approval says the row should appear in Standard games. STD2-M1 raised the same question for the
  combat-log row.
Not covered by: DEVIATIONS 140 / GAPS H.6 (§11 D.16) record the setting, not its presence in Standard.
Suggested fix: confirm with the user together with STD2-M1. If the row should not appear, list it only with
`m_currentGame` and a ruleset that has rarities, as the MAW key rows are (D.18).

## Notes (not findings)
- **Per-action scans for MAW-only context now run in Standard.** All are cheap; they extend the pattern of STD3-4
  and are not a regression worth fixing alone:
  - each melee blow counts live actors within 384 of the target (`GameplayActionController.cpp:1072-1083`);
  - each targeted spell does the same (`PartySpellSystem.cpp:1345-1358`);
  - each held-item use computes the yellow alert (`GameplayItemService.cpp:269`);
  - each quicksave computes the yellow alert (`GameApplication::saveFoodCost`).
- **Arena HP.** `ArenaRuntime.cpp:212` dropped the 1..32767 clamp, like STD1-1. No Standard arena monster comes near
  the old limit.
- **Editor HP field.** `EditorMainWindow.cpp:14351` keeps the int16 range for the now-32-bit HP override, so it stays
  writable to the legacy delta format.
- **Unrelated features seen in the uncovered files** (checked only for ruleset hooks; none found):
  - energy shields: ModelInstance/ModelRenderer shield shell, the `*_shield*` shaders,
    `GameplayActorShields`/`MonsterShields`, the personal-shield code in `Party.cpp`, `GameplayCombatController`
    `personalShieldPassedDamage`, the HUD shield rim, the shield floating text in both GameViews;
  - monster modifiers and relations: `GameplayActorModifiers`, `MonsterModifiers`, `MonsterRelationAddOns`,
    `ActorBehaviorCatalog::applyMonsterModifiers`;
  - Hesper technology: EnergyGuns/EnergyBlades/ShieldTech/Hacking in `GameMechanics`, `SkillData`,
    `MasteryTeacherDialog`, `Party::isPartyWideUtilitySkill`, tech points;
  - turrets: `ActorTurretScan.h`, `GameplayActorAiSystem` idle aim, the traverse ease and aim lead, `WorldFxSystem`
    look scan; no Standard world data has `traverse_degrees_per_second`;
  - projectile object bindings in `ProjectileEffectBindings`: no `objects:` in any `projectiles.yml`;
  - MM8 foot-travel tests.
- **MAW-side, outside Standard.** `GameplayScreenRuntime::m_dimensionDoorWithoutQuest` stays true after an
  `evt.OpenDimensionDoor(true)` until the next spell or HUD open resets it. Standard scripts never pass `true`
  (`mm6_common.lua:381`, `out07_mmmerge.lua:50`).

## Coverage: changed and new files outside `game/rules/maw` (slice that covered each)
- **STD1:** `game/rules/*.cpp|h` (the ten classes in its list), `PartySpellSystem.*`, `GameplayActionController.*`,
  `ChestRuntime.*`, `HouseServiceRuntime.*`, `HouseInteraction.cpp`, `TurnBasedCombatRuntime.*`, `ItemRuntime.*`,
  `ItemEnchantRuntime.*`, `ItemGenerator.*`, `GameplayBolsterRuntime.h`, `GameplayProjectileService.*` (homing,
  chain, missile hit), `IndoorWorldRuntime.*`, `OutdoorWorldRuntime.*`, `GameplayPartyOverlayRenderer.cpp`
  (inspect).
- **STD2:** `InventoryItemUseRuntime.*`, `PotionEffectTable.*`, `InventoryItemMixingRuntime.cpp`,
  `AlchemyBenchRuntime.*`, `GameplayAlchemyBench*`, `GameplayBenchPainter.h`, `PriceCalculator.*`,
  `ItemEnchantTables.*`, `MasteryTeacherDialog.cpp`, `MercenaryRecruitmentRuntime.cpp`, `NpcFollowerRuntime.*`,
  `GameplayPartyOverlayInputController.*`, `GameplayPartyOverlayRenderer.cpp`, `GameplayHudOverlaySupport.*`,
  `GameplayBuffHud.*`, `EnemyHealthBarRenderer.cpp`, `GameplayDialogueRenderer.cpp`, `InventoryBags.*`,
  `InventoryCompactBags.h`, `CombatLog.*`, `GameplayCombatLogPanel.*`, `GameplayHudInputController.cpp`, the three
  menu screens, `KeyboardBindings.*`, `GameSettings.*`, the GameApplication menu and save call sites.
- **STD3:** `GameApplication.*` (lifecycle), `GameSession.*`, `main.cpp`, `content/*` (ContentManifest,
  ContentTableComposer), `GameDataLoader.*`, `GameDataRepository.*`, `game/events/*`, `game/maps/*` (SaveGame,
  MapDeltaData, MapAssetLoader, the scene ymls), `game/tables/*`, `ActorBehaviorRuntime.*`,
  `GameplayRuntimeInterfaces.h`, `CorpseLootRuntime.*`.
- **This pass (STD4), read hunk by hunk:**
  - engine: `AssetFileSystem.cpp`, `AssetPackIndex.*` (→2-1), `ApplicationConfig.h`, `ModelInstance.*` and
    `ModelRenderer.*` (shields);
  - editor: `editor/CMakeLists.txt` and `EditorMainWindow.cpp` (→2-2);
  - packaging: `tools/packaging/packs.yml`, `runtime_packs.py`, `package_runtime_assets.py`, `run_game.py`,
    `.github/workflows/packages.yml`, `cmake/BgfxRuntime.cmake`;
  - `game/CMakeLists.txt`, `game/fx/*`;
  - gameplay: `ActorBehaviorCatalog.*`, `ArenaRuntime.cpp`, `BountyHuntRuntime.*`, `GameMechanics.*` (all 880 lines),
    `GameplayActorAiSystem.cpp`, `GameplayActorAiTypes.h`, `GameplayActorService.*`, `GameplayCombatController.*`
    (the non-rules parts), `GameplayDialogController.cpp`, `GameplayHeldItemController.cpp`,
    `GameplayInputController.cpp`, `GameplayInputFrame.h`, `GameplayInteractionController.cpp`,
    `GameplayItemService.*`, `GameplayOverlayInputController.cpp`, `GameplayScreenController.cpp`,
    `GameplayScreenRuntime.*`, `GameplaySpellService.cpp`, `PartyHostileAlert.*`, `GameplayMonsterSpawn.*`,
    `GameplayCraftingBenchInputController.*`;
  - indoor and outdoor: `IndoorGameView.cpp`, `IndoorPartyRuntime.*`, `IndoorRenderer.*` (→2-3),
    `HeadlessOutdoorDiagnostics.cpp`, `OutdoorBillboardRenderer.cpp`, `OutdoorGameView.cpp`,
    `OutdoorInteractionController.cpp`, `OutdoorMovementDriver.*`, `OutdoorPartyRuntime.*`, `OutdoorRenderer.cpp`;
  - party and items: `Party.*` (all 895 lines), `CharacterState.h`, `CharacterRulesetState.h`, `InventoryItem.h`,
    `EventSpellBuffs.*`, `SkillData.*`, `CraftingRuntime.*`, `ItemRulesetFields.h`;
  - ui: `GameplayHudCommon.cpp`, `GameplayHudOverlayRenderer.cpp`, `GameplayHudRenderer.cpp`,
    `GameplayOverlayTypes.h`, `GameplayUiController.*`, `GameplayUiRenderer.cpp`, `GameplayUiSkin.*`,
    `MenuDesignScreen.*`, `MenuSettingsModel.cpp` (→2-5), `GameplayAlchemyBenchView.cpp`,
    `GameplayCraftingBench*`;
  - `SceneOverlayOperations.*`, `RulesetDefinition.*`, `RulesetOptions.*`, `NewGameOptions.h`;
  - scenario harness: `game/scenario/*` (only the removed lines; harness only), and the modified existing tests (no
    Standard expectation was loosened).
- **Unchanged:** `android/` (no diff); `touch_controls.yml` (no diff; →2-4).

## Rules seam: methods pass 1 did not name, and what their Standard base does at each call site
Binding: `Party::rules()` → Standard when `m_pRules` is null (`Party::seed` now nulls it); `gameRulesFor(nullptr)` and
`boundGameRules()` → Standard; `bindGameRules` only in `GameSession.cpp:260, 371`. `bindItemRules` does not exist.
- **CombatRules**
  - `resolveCharacterAttack` (no-op; `GameplayActionController.cpp:1087`).
  - `characterAttackRecoveryTicks` (nullopt; `GameplayHudOverlaySupport.cpp:134`, falls through to HEAD's
    tooltip).
  - `spellDamageOnTarget` (nullopt; `PartySpellSystem.cpp:2627`).
  - `partySpellDamageType` (identity; `PartySpellSystem.cpp:2534, 2572`).
  - `updateCombat` (no-op; `GameSession`).
- **MonsterRules**
  - `rulesTopic`, `scriptInfo` and `arenaWaveMonster` are reached only through `evt.RulesTopic`/`RulesetInfo`/
    `ArenaMonster`, which no Standard script calls (grep of `assets_dev/engine`, `assets_dev/worlds`).
  - `makeBoss` (false), `resetMap` (only from the `MapTransitionReset` action, which needs `mapResetOffer`).
  - `teleportBlockedText` (only after `teleportBlockedNearEnemies`, false).
  - `bountyRefusal`/`bountyElsewhere` (nullopt) and `bountyKillCounts` (true). The new open-bounty scan over
    `namedGlobalVars` has no side effects.
- **ItemRules**
  - `levelSevenGivesRareItem` (true: `ItemGenerator.cpp:174` keeps HEAD's level-7 path).
  - `levelRequirement` (0) and `wearRefusal` (nullopt) in `Party::tryEquipItemOnMember`.
  - `openSealedItem` (false; the new `GameplayScreenController.cpp:513` hook does nothing).
  - `gathersItem` (after `lootGathering` nullopt).
  - `alchemist`/`alchemySortRank` (nullopt: HEAD sort).
- **SkillRules**
  - `extraHouseSkills` (empty, `HouseInteraction.cpp:871`).
  - `applyStatBonuses`/`applyResourceBonuses` (no-ops, `Party::rebuildMagicalBonusesFromBuffs`).
  - `skillResetCost`/`resetSkills` (only via an evt function MAW scripts call).
  - `updateRegeneration` (no-op).
  - `skillLevelCap` (no external caller; nullopt in `canRaiseSkill`).
- **SpellRules**
  - `castRefusal` (nullopt; `GameplaySpellService.cpp:124`, PartySpellSystem).
  - `castsAsAura` (false).
  - `auraDamage` (nullopt; immolation keeps `rollImmolationDamage`, `OutdoorWorldRuntime.cpp:8127`).
  - `updateAuras` and `memberLeaving` (no-ops).
  - `reservedSpellPoints` (no caller).
- **ClassRules**
  - `applyClassBonuses`, `update` (no-ops).
  - `unstuckLift`/`partyCharge` (nullopt; their keys have no default binding).
- **PotionRules:** `estimatedPool` (0; Standard `potion_effects.yml` has no `pool_share`).
- **CraftingRules:** `isExtraTarget`, `craft`, `materialAction`, `gemTier`, `gemCombineCount`, `combinedGem` and
  `craftOutlook` are reached only from the crafting tab or `CraftingRuntime`. Those are unreachable in Standard:
  `hasCrafting` is false, `isMaterial` is false, the tab hit test is gated on `available`, and Tab is gated on
  `GameplayCraftingBenchView::available`. `materialDescription` has no caller.
- **ExperienceRules**
  - `rewardMapProgress` (empty string, no message; `OutdoorWorldRuntime.cpp:17291`).
  - `prepareNewParty` (no-op).

## Checked and matching (Standard identical to HEAD)
- **GameMechanics**
  - `resolveEquippedItems` asks `baseStats` per slot. The result is nullopt, so the dice and armour are the table's;
    all 16 slots have a runtime state, so there is no null dereference.
  - `combatRows` and `baseMaxHealth`/`baseMaxSpellPoints` are nullopt, so the HEAD formulas apply. `wield` reproduces
    HEAD's two-handed and off-hand rules in `resolveCharacterEquipPlan`.
  - `CharacterAgeReferenceYear` = 1168 (HEAD `GameStartingYear`). `maximumTrainableLevelFromExperience` uses the same
    formula.
- **Party**
  - Meditation and Regeneration per-tick amounts are equal (mastery 1-4, level 0 gives 0). A skill raise costs and
    subtracts level+1.
  - Follower bonuses still stack. Mist Form keeps physical immunity.
  - `applyDamageToMember` gets the identity from `absorbCharacterDamage` after HEAD's own `damage <= 0` guard.
  - `environmentDamage` is applied to drowning, lava and falls (identity).
- **Monster attacks** (`GameplayCombatController`): the hit, evade and armour stages use the same seeds.
  `personalShieldPassedDamage` passes the damage unchanged for members without shields against monsters without a
  shield profile. Computing `adjustedDamage` after the evade roll draws from separate generators.
- **`GameplayActorService::tryApplySharedSpellEffect`:** with `rulesetSeconds` nullopt, every branch is HEAD's.
- **`SkillData`:** the 40 classic skill ids keep their positions (teacher topics 300-416 unchanged). The appended
  technology and ruleset skills are excluded or capped None for Standard characters and mercenaries. The 12 new class
  names only extend the lookup.
- **Asset mounting:** a `rulesets` pack mounts at `/rulesets` after the engine, so no Standard path collides.
  `loadAvailableRulesets` falls back to Standard on any error (`NewGameScreen::loadRulesets`).
- **Quick save:** the text is still "Game Saved!" when `saveFoodCost` is 0. `startNewSession` and
  character-creation start activate `mmerge` (an early return when it is already active).
- **HUD:** the world-item hover label, potion and aura personal-buff lines, portrait counter, map progress and death
  timer are all empty in Standard. Colour-code parsing affects only `\f` text.
