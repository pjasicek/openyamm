# D: combat/spell fixes (Life Drain targeting, attack-spell fallback, clubs, incapacitated speech, Ooze collision)

All shared gameplay code except the per-view projection lists. Line refs are against HEAD (2476b1e90).
Order: 3 (trivial), 4, 1, 2, 5 (data, needs in-game check).

---

## 1. Spell actor targets: drop `hasDetectedParty`, one shared 5120 range check

### Facts checked before proposing
- Detection filter lives in three per-view copies:
  - outdoor hovered `OutdoorInteractionController::resolveSpellActionHoveredActorIndex` (`OutdoorInteractionController.cpp:578-602`, filter at :592-596)
  - outdoor list `resolveVisibleHostileActorIndices` (:604-702, filter at :656-660)
  - indoor list `IndoorRenderer::gameplayVisibleHostileActorIndices` (`IndoorRenderer.cpp:6042+`, filter at :6091-6095)
  - Indoor hovered (`IndoorRenderer::gameplayHoveredActorIndex`, :6032-6040) has **no** liveness/hostility filter at all, so
    indoor and outdoor already disagree.
- `spellActionVisibleHostileActorIndices()` has one caller only: `PartySpellSystem::quickCastActorTarget`
  (`PartySpellSystem.cpp:3124-3135`). `spellActionHoveredActorIndex()` is used by `GameplaySpellService.cpp:286`
  (Actor targets) and `:328` (GroundPoint aim).
- Who relies on `setMapActorHostileToParty` clearing `hasDetectedParty` (`OutdoorWorldRuntime.cpp:17096-17139`, clear at
  :17119)? Readers of the flag: the AI engagement (`GameplayActorAiSystem.cpp:1359-1403`, recomputed every update;
  it sets the flag again once the party is the target), charge modifier `engagesParty` (`OutdoorWorldRuntime.cpp:7450`),
  presentation `combatTargetingParty` (:15415-15418), Wizard Eye markers (:21608), and the spell target lists above.
  Indoor does the opposite: making an actor hostile sets `hasDetectedParty = hostileToParty` (`IndoorWorldRuntime.cpp:12065-12072`).
  **Proposal: leave `setMapActorHostileToParty` alone in this fix.** Once the lists stop reading the flag and the range cap
  keeps targets within 5120 (< outdoor active-AI range 5632, `OutdoorWorldRuntime.cpp:514`), a hit actor is always simulated
  and detects the party on its next update. Setting the flag to true at hit (to match indoor) would start the charge
  modifier and Wizard Eye markers immediately, and would leave the flag stale on frozen far actors. That would be a
  separate behaviour change; log it as a follow-up.

### Change
a) Shared helper in `game/party/PartySpellSystem.{h,cpp}`, next to `quickCastActorTarget`:
```cpp
// Original pick depth for spell and ranged targets (MM7/MM8; OpenEnroth RangedAttackDepth).
static constexpr float SpellActorTargetRange = 5120.0f;

// A living, visible actor within spell reach of the party. Hostile-only for picks the game makes for the player
// (quick cast); a target cursor click may pick anyone.
static bool isUsableSpellActorTarget(
    const IGameplayWorldRuntime &worldRuntime,
    size_t actorIndex,
    bool requireHostile);
```
```cpp
bool PartySpellSystem::isUsableSpellActorTarget(
    const IGameplayWorldRuntime &worldRuntime,
    size_t actorIndex,
    bool requireHostile)
{
    GameplayRuntimeActorState actor = {};

    if (!worldRuntime.actorRuntimeState(actorIndex, actor) || actor.isDead || actor.isInvisible
        || (requireHostile && !actor.hostileToParty))
    {
        return false;
    }

    const float dx = actor.preciseX - worldRuntime.partyX();
    const float dy = actor.preciseY - worldRuntime.partyY();
    const float dz = actor.preciseZ - worldRuntime.partyFootZ();
    return dx * dx + dy * dy + dz * dz <= SpellActorTargetRange * SpellActorTargetRange;
}
```
b) `PartySpellSystem::quickCastActorTarget` (:3124): build `visible` and then drop entries that fail
   `isUsableSpellActorTarget(worldRuntime, index, true)` before the `front()` / spread-debuff selection. The existing 4800 cap
   for spread debuffs stays.
c) `GameplaySpellService::tryResolveQuickCastRequest` (`GameplaySpellService.cpp:281-294`):
```cpp
-            request.targetActorIndex = pWorldRuntime->spellActionHoveredActorIndex();
+            if (!request.targetActorIndex
+                || !PartySpellSystem::isUsableSpellActorTarget(*pWorldRuntime, *request.targetActorIndex, true))
+            {
+                request.targetActorIndex = pWorldRuntime->spellActionHoveredActorIndex();
+            }
+
+            if (request.targetActorIndex
+                && !PartySpellSystem::isUsableSpellActorTarget(*pWorldRuntime, *request.targetActorIndex, true))
+            {
+                request.targetActorIndex.reset();
+            }
```
   (The first clause keeps a preset target; fix 2 uses it.) Fear's path (:236-246) goes through the same function.
d) `GameplaySpellActionController::resolvePendingActorTarget` (`GameplaySpellActionController.cpp:238-259`): after the
   existing checks, reject when the target is out of range. Keep Reanimate's dead-target exemption by checking range only:
```cpp
+    if (pWorldRuntime != nullptr && !PartySpellSystem::isActorWithinSpellTargetRange(*pWorldRuntime, worldHit.actor->actorIndex))
+    {
+        return false;   // cursor stays active; status "Target is out of range" if a status hook exists there
+    }
```
   That means splitting (a) into `isActorWithinSpellTargetRange` (distance only, dead allowed) and
   `isUsableSpellActorTarget` (alive, visible, optional hostility, then range).
e) Per-view lists: delete only the detection line in the three filters (outdoor :596 and :660, indoor :6095). Do the same
   in the outdoor hovered filter (:592-596), so both hovered sources return any picked actor, which matches indoor.
   Liveness and hostility for Actor-target quick casts then come from the shared helper in (c). The GroundPoint aim at
   :328 will now also aim at a friendly actor under the cursor; that is harmless (it only aims the projectile).
f) Do **not** add the range check to the cast core (`PartySpellSystem.cpp:1613-1640`). Scripted and scenario casts
   (`cast_spell` with `actor_index`) bypass the UI, and some may target far actors. If a hard cap is wanted there, add it
   behind `request.quickCast || request.fromUi` later.

### Edge cases
- Hostile actors that haven't noticed the party (or were just hit outdoors) are targetable again. That fixes the
  intermittent "No valid target".
- Range is measured centre to party feet with no radius subtraction, as in the original pick depth (to the sprite). A
  huge monster just past 5120 is excluded; acceptable.
- Indoors the cap rarely matters (rooms are smaller). Indoor hovered now also requires hostility for quick casts (it
  didn't before), which makes the two views consistent.
- MAW `quickCastSpreadsDebuff` path: unchanged apart from the extra filter.

### Verification
- doctest, extend `tests/GameplaySpellServiceTests.cpp` with
  `TEST_CASE("quick cast actor target skips actors beyond spell reach")`: in `PartySpellTestWorldRuntime`
  (`tests/PartySpellTestHarness.h`) put hostile actors at 3000 and 6000; `quickCastActorTarget` returns the 3000 one; with
  only the 6000 one it returns nullopt and `tryStartQuickSpellCast` gives `AttackFallback`.
- Extend the SPL-18 case in `tests/MawAuditCombatSpellTests.cpp:796` to check a spread debuff ignores a sixth actor at 6000.
- Headless: new `tests/scenarios/mm6/lifedrain_reach.yml`: spawn a hostile actor at 4000 and one at 7000 outdoors;
  `cast_spell` through the quick-cast path. The near one is damaged and is pursuing after 2 s; the far one is not chosen.
  The view-list detection removal can only be checked in game: hit a far mob once, then quick-cast again.

---

## 2. Attack spell with no target falls back to the weapon

### Change
- `GameplaySpellService.h:40-44` `MemberSpellCastResolution`: add `bool noTarget = false;`.
- `GameplaySpellService::castSpellFromMember` (`GameplaySpellService.cpp:155-191`): when `quickCast` prep fails, set
  `resolution.noTarget = true` and return **without** the status line. Only `tryBeginAttackCast` calls it with
  `quickCast = true` (`GameplaySpellActionController.cpp:58`; the other callers use the default `false`), so no other UI
  loses the message.
- `GameplaySpellActionController.h:28-33`: add `NoTarget` to `AttackCastDisposition`. In `tryBeginAttackCast`
  (`GameplaySpellActionController.cpp:32-78`), take a new `std::optional<size_t> preferredActorIndex`, preset
  `request.targetActorIndex` through a `castSpellFromMember` overload or parameter, and map `noTarget` → `NoTarget`.
- `GameplayActionController::executePartyAttack` (`GameplayActionController.cpp:975-1002`):
```cpp
-    if (!pAttacker->attackSpellName.empty() && !cannotCastAttackSpell(config, actingMemberIndex, *pAttacker))
+    if (!pAttacker->attackSpellName.empty() && !cannotCastAttackSpell(config, actingMemberIndex, *pAttacker))
     {
         AttackCastResult attackCastResult = {};
+        bool noTarget = false;
         ...
                 GameplaySpellActionController::tryBeginAttackCast(
                     *config.pRuntime, *config.pSpellService, actingMemberIndex,
-                    pAttacker->attackSpellName, config.targetQueries);
+                    pAttacker->attackSpellName, config.targetQueries, config.directTargetActorIndex);
+            noTarget = spellAttackCastResult.disposition == GameplaySpellActionController::AttackCastDisposition::NoTarget;
         ...
-        return result;
+        if (!noTarget)
+        {
+            return result;
+        }
     }
     // falls through to the weapon attack below (target resolve, melee/ranged)
```
### Edge cases
- Ground-capable projectile spells never reach `NoTarget` (they fall back to the cursor point, `GameplaySpellService.cpp:301-316`),
  so they keep casting at the cursor, as now.
- Turn-based mode: the weapon path already handles TB; no extra member switch is needed.
- `cannotCastAttackSpell` (MAW Assassin combo points, mana) is unchanged.
- **Existing scenario breaks:** `tests/scenarios/rulesets/maw_assassin_attack_spell.yml` step 2 (5 points,
  `max_weapon_attacks: 0`) relies on "no headless target → silent no-op". With `directTargetActorIndex` passed as the
  preferred target, that step now really casts Blades (5 → 2 points), so the following `cast_spell ... expect: applied`
  would be refused. Update it: keep step 2 expecting no swing, add `console: ruleset counter 1 5` before the `cast_spell`
  step, and update the comment ("A headless run has no visible hostile target...").

### Verification
- doctest in `tests/GameplaySpellServiceTests.cpp`:
  `TEST_CASE("an attack spell without a target swings the weapon instead")`. Set an attack spell of Actor kind
  (Lifedrain), give the world no hostile actors, run `executePartyAttack` with `directTargetActorIndex` empty, and check
  the weapon attack was attempted (result target/attack fields) and no mana was spent. Second subcase: the direct target
  is set → the cast starts on it.
- Headless: rerun `maw_assassin_attack_spell.yml` after updating it. Add one step there or in a new
  `tests/scenarios/rulesets/attack_spell_no_target.yml` (Standard): attack spell Lifedrain, no actor in reach,
  `party_attack` → `min_weapon_attacks: 1`.

---

## 3. Clubs equip without a skill

### Change
`GameMechanics.cpp:793-797`:
```cpp
 bool requiresLearnedSkillToEquip(const ItemDefinition &itemDefinition)
 {
     const std::string skillName = canonicalSkillName(itemDefinition.skillGroup);
-    return !skillName.empty() && skillName != "Misc";
+    // Anyone can wield a club: it has no skill of its own (MM7/MM8, MMerge).
+    return !skillName.empty() && skillName != "Misc" && skillName != "Club";
 }
```
### Combat code reading the club skill (checked; no change needed)
- Attack and damage skill bonus: `skillLevel(character, "Club")` is 0 → just the Armsmaster bonus (`GameMechanics.cpp:1010-1033`,
  `:1052-1070`). Correct: clubs get no skill bonus.
- Recovery: `baseRecoveryTicksForSkillName("Club")` falls to the default 100 (`:437-489`), which matches OpenEnroth
  `SKILL_CLUB 100_ticks` (`mm7_data.cpp:515`).
- Attack profile `meleeSkillLevel/Mastery` (`:2600-2603`): 0 / None. Fine.
- Shop type filters (`HouseServiceRuntime.cpp:308`), MAW `isMeleeWeaponSkill` (`MawCharacterSheet.cpp:62`) and MAW
  unarmed-enchant exclusion (`MawItemRules.cpp:1113`): unaffected.
- Shared base rule; nothing world- or ruleset-specific is needed (MAW grants no Club skill either).

### Verification
- Extend `tests/InventoryEquipRegressionTests.cpp:633` ("equip plan requires the skill and respects the doll type"): a
  skill-less character `CHECK(canCharacterEquipItem(character, *itemTable.get(76), &dollType))` and the same for 860 and
  1660, and `resolveCharacterEquipPlan` gives `MainHand`.

---

## 4. No speech from incapacitated members; Dying only on the transition

### Change
a) Pure rule in `game/gameplay/GameplaySpeechRules.{h,cpp}` (shared, testable):
```cpp
// Whether a member in this condition may speak. Incapacitated members (asleep, paralysed, unconscious, dead, stone,
// eradicated) are silent, except for the lines about that state.
bool canMemberSpeak(const Character &member, SpeechId speechId);
```
```cpp
bool canMemberSpeak(const Character &member, SpeechId speechId)
{
    switch (speechId)
    {
        case SpeechId::Dying:
        case SpeechId::CheatedDeath:
            return true;                                  // queued at the moment health crosses zero

        case SpeechId::Awaken:
            return !GameMechanics::hasCondition(member, CharacterCondition::Dead)
                && !GameMechanics::hasCondition(member, CharacterCondition::Petrified)
                && !GameMechanics::hasCondition(member, CharacterCondition::Eradicated);

        default:
            return GameMechanics::canAct(member);         // GameMechanics.cpp:3516
    }
}
```
   Allowed exceptions: **Dying, CheatedDeath** (both are about losing consciousness, and both are spoken after health ≤ 0
   because the queue plays them later) and **Awaken** (in case Asleep is still set when the line plays after rest). Every
   other line (damage, kills, Falling, DamagedParty, LastPersonStanding, dialogue/shop lines, condition lines) needs
   `canAct`. This matches OpenEnroth gating its damage reaction with `CanAct()` (`Character.cpp:1323`).
   If `hasCondition` isn't public, use `member.conditions.test(size_t(...))` as `Party.cpp:1169-1175` does.
b) `GameplayScreenRuntime::playSpeechReaction` (`GameplayScreenRuntime.cpp:2798-2819`): after `pMember` is resolved,
```cpp
+    if (!canMemberSpeak(*pMember, speechId))
+    {
+        return;   // also skips the face animation; portraits of incapacitated members show their condition
+    }
```
   This covers the queued party requests (:2990-2994), kill/hit lines from projectiles that land after the shooter
   fell (`GameplayCombatController.cpp:1525, 1678, 1686`) and `queueDelayedSpeechReaction`.
c) `Party::applyDamageToMember` (`Party.cpp:3026-3100`):
```cpp
     const int previousHealth = member.health;
+    const bool couldActBefore = GameMechanics::canAct(member);
 ...
-    if (status == "falling")
+    if (status == "falling" && couldActBefore)
     {
         queueSpeech(memberIndex, SpeechId::Falling);
     }
 ...
-    if (member.health <= 0)
+    if (member.health <= 0 && previousHealth > 0)
     {
         queueSpeech(memberIndex, SpeechId::Dying);
     }
```
   Keep the `!m_debugDamageImmune` behaviour: with immunity health doesn't change, so Dying never fires. That is already
   the case today.

### Edge cases
- A member killed outright from conscious still gets Dying (transition). A member already unconscious and hit by area
  damage (`allowUnconscious`, `Party.cpp:1169`) or finished off to Dead gets nothing. That matches the original:
  dead/eradicated portraits don't react (OpenEnroth `playEmotion`, `Character.cpp:6552-6567`).
- Scripted EVT speech (`EventRuntime.cpp:772-888`) is now silent for incapacitated targets. Intended.
- The active member is normally able to act, so dialogue and shop lines are unaffected.

### Verification
- Extend `tests/AudioRegressionTests.cpp` (next to :823-883):
  - `TEST_CASE("an unconscious member hit by area damage queues no dying speech")`: set Unconscious and health −5,
    `applyDamageToMember(i, 5, "", true)` → no Speech request.
  - `TEST_CASE("dying speech is queued once, when health crosses zero")`: health 3, damage 10 → exactly one Dying.
  - `TEST_CASE("incapacitated members only speak about their state")`: a table over `canMemberSpeak`: Unconscious →
    AttackHit false, KillWeakEnemy false, Dying true, CheatedDeath true; Dead → Awaken false; healthy → all true.
  - Check the existing "major damage threshold..." and "debug damage immunity..." cases still pass unchanged.

---

## 5. MM7 Ooze collision (needs in-game check)

### Where it lives
- Collision height and radius are the `Height`/`Radius` columns of the engine table
  `assets_dev/engine/data_tables/monster_descriptors.txt` (rows 310-312, "Ooze A/B/C": 120 / 47, identical to MMerge
  `MonList.txt` 309-311). `CREATURE_POSTPROCESS.md:37`: Height is collision, never a visual size. `actors.yml` bindings
  are presentation only (scale, clips); there is no collision key there, and adding one would be a new engine feature.
- The precedent for changing collision is MAW's descriptor override (`assets_dev/engine/rulesets/maw/ruleset.yml:248-256`,
  `content/monster_descriptors_patch.txt`, rows like `208	Height	192`). That is ruleset-scoped. This fix is
  world-agnostic and model-driven, so it should be an **engine table edit** of rows 310-312, with the deviation from
  MMerge recorded in `level_generation/creatures/mm7_m298_claude/README.md` ("Scale and timing for the binding").
  If the user would rather not diverge from the MMerge table, the alternative is a world-level override file, but no
  such mechanism exists yet (it would be medium work).
- MAW's patch has no 310-312 rows (checked), so no ruleset interaction.

### Proposed values (needs in-game check)
- The model is about 178 wide, 41 tall at rest, with a pseudopod up to 151 during the attack
  (`mm7_m298_claude/README.md:30,48-51,107-110`).
- Proposal: **Radius 80, Height 64**. That matches the MM6 BOoze's 64 height (rows 589-591: 64 / 111). Radius 80 rather
  than 89 leaves a little room for MM7 tunnel pathing (MAW had to shrink stuck monsters).
- Side effects to watch:
  - Larger radius means melee reach measured from the edge (`GameplayActionController.cpp:62-67`), so the party can hit
    from further away; the ooze's own reach grows the same way.
  - Pathing in narrow MM7 dungeon corridors.
  - Projectiles over the blob now miss where they used to hit air.
  - Health-bar and inspect offsets (`InspectYOffset -90`) may need a look.

### Verification
- Headless: extend the existing MM7 creature regression for m298 (or `actors` suite). Spawn Ooze A on flat ground and
  check that a party projectile aimed 70 units off-centre at height 30 hits, and one at height 100 above the centre misses.
- In game (`tools/run_game.sh --isolated`): melee from the visible edge, walk into it, arrows from range, and narrow
  corridors in an MM7 dungeon with oozes. Confirm before committing the values.
