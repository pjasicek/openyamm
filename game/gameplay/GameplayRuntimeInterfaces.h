#pragma once

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActorShields.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/items/WorldItemShape.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/rules/ActorRulesetFacts.h"
#include "game/tables/MonsterTable.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// How far ahead of the party MAW's gather key tries to put what it brings, the nearer ones when a wall or a drop is in
// the way of the farther; at the party's feet when none will do.
inline constexpr std::array<float, 3> LootGatherDistances = {192.0f, 128.0f, 64.0f};

class ActorAiTrace;
class ISceneEventContext;
class ActorBehaviorRuntime;
class GameplayActorHitFeedback;
class GameplayProjectileService;
class MergedBolsterMonsterTable;
struct MapStatsEntry;
struct WorldAmbientSound;
struct GameplayMonsterSpawnRequest;
struct MapKillProgress;
struct GameplayMinimapState;
struct GameplayMinimapLineState;
struct GameplayMinimapMarkerState;
struct GameplayInputFrame;
struct PartySpellCastResult;

struct GameplayWorldUiRenderState
{
    bool canRenderHudOverlays = false;
    bool renderGameplayHud = true;
    bool renderActorInspectOverlay = true;
    bool renderDebugFallbacks = false;
};

struct GameplayWorldMovementFrameDiagnostics
{
    static constexpr size_t MaxTimerEventIds = 8;

    bool collected = false;
    uint64_t totalNanoseconds = 0;
    uint64_t controllerNanoseconds = 0;
    uint64_t sceneAdvanceNanoseconds = 0;
    uint64_t actorColliderBuildNanoseconds = 0;
    uint64_t partyUpdateNanoseconds = 0;
    uint64_t movementDriverNanoseconds = 0;
    uint64_t movementInputNanoseconds = 0;
    uint64_t movementCollisionNanoseconds = 0;
    uint64_t movementTraceNanoseconds = 0;
    uint64_t movementContactsNanoseconds = 0;
    uint64_t movementConsequencesNanoseconds = 0;
    uint64_t partyRecoveryNanoseconds = 0;
    uint64_t partyTimedStateNanoseconds = 0;
    uint64_t partySpellStateNanoseconds = 0;
    uint64_t partyEffectsNanoseconds = 0;
    uint64_t timerNanoseconds = 0;
    uint64_t timerEventExecutionNanoseconds = 0;
    uint64_t timerEventApplyNanoseconds = 0;
    uint64_t partyEventApplyNanoseconds = 0;
    uint64_t pressurePlateNanoseconds = 0;
    uint64_t boundaryTransitionNanoseconds = 0;
    uint64_t actorQueueAndContactsNanoseconds = 0;
    uint32_t movementStepCount = 0;
    uint32_t timerEventsFired = 0;
    size_t storedTimerEventIdCount = 0;
    std::array<uint16_t, MaxTimerEventIds> timerEventIds = {};
};

struct GameplayChestItemState
{
    InventoryItem item = {};
    uint32_t itemId = 0;
    uint32_t quantity = 0;
    uint32_t goldAmount = 0;
    uint32_t goldRollCount = 0;
    bool isGold = false;
    uint8_t width = 1;
    uint8_t height = 1;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
};

struct GameplayChestViewState
{
    uint32_t chestId = 0;
    uint16_t chestTypeId = 0;
    uint16_t flags = 0;
    uint8_t gridWidth = 0;
    uint8_t gridHeight = 0;
    std::vector<GameplayChestItemState> items;
    std::vector<GameplayChestItemState> hiddenItems;
};

struct GameplayCorpseViewState
{
    bool fromSummonedMonster = false;
    uint32_t sourceIndex = 0;
    std::string title;
    std::vector<GameplayChestItemState> items;
};

struct GameplayWorldItemInspectState
{
    InventoryItem item = {};
    uint32_t goldAmount = 0;
    bool isGold = false;
};

enum class ActorAiAnimationState : uint8_t
{
    Standing = 0,
    Walking = 1,
    AttackMelee = 2,
    AttackRanged = 3,
    GotHit = 4,
    Dying = 5,
    Dead = 6,
    Bored = 7,
};

// Charges (MonsterModifiers charge) on a map since it loaded: started, and how they ended.
struct GameplayChargeCounts
{
    uint32_t started = 0;
    uint32_t hits = 0;
    uint32_t misses = 0;
    // Frenzies (MonsterModifierSet::frenzy) started so far.
    uint32_t frenzies = 0;
};

enum class ActorTurnBasedMode : uint8_t
{
    // Real-time play: actors attack whenever their recovery cooldown allows.
    RealTime,
    // Turn-based wait stage: actors move but never attack.
    MoveOnly,
    // Turn-based attack and movement stages: actors hold position and only granted actors take their action.
    Hold,
};

// What the rules read of an actor, without the presentation GameplayRuntimeActorState carries (animation, shield,
// behaviour clips): cheap enough for a pass over every actor each frame (audit ROB-2-5).
struct GameplayActorRulesView
{
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    float preciseX = 0.0f;
    float preciseY = 0.0f;
    float preciseZ = 0.0f;
    uint16_t radius = 0;
    bool isDead = false;
    bool isInvisible = false;
    bool hostileToParty = false;
    bool hasDetectedParty = false;
    // Fights for the party (a summon, a reanimated or controlled monster: ally 999).
    bool partyAlly = false;
    int currentHp = 0;
    int maxHp = 0;
    ActorRulesetFacts rulesetFacts;
};

struct GameplayRuntimeActorState
{
    uint32_t actorId = 0;
    float yawRadians = 0.0f;
    ActorAiAnimationState animationState = ActorAiAnimationState::Standing;
    float animationTimeTicks = 0.0f;
    // Presentation observes the same action clock and movement as combat; it never drives either.
    float actionSeconds = 0.0f;
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    // Horizontal speed the AI asked for before collision (0 when not moving): what velocity would be without walls.
    float intendedSpeed = 0.0f;
    // Pursuing or fleeing (moving at twice the wander speed): a 3D model prefers its run clip.
    bool hurrying = false;
    // A skirmisher's footwork (strafe attack, evade, circle, back-off: MM9's Strafe and Backpedal states, which face
    // the target), from the AI's skirmish phase in any world: its model keeps the AI's facing. While the AI backs it
    // away (skirmishBackpedals) the model plays its backpedal clip, or its gait reversed without one; every other move
    // plays the gait forwards at any angle, as MM9's Strafe state does (devdocs/mm9_rework/MM9_ANIMATION_AUDIT.md A2).
    bool footwork = false;
    bool backpedalling = false;
    bool castingSpell = false;
    bool secondaryAttack = false;
    uint32_t castingSpellId = 0;
    bool attackImpactTriggered = false;
    // Action seconds still to run once the attack applies at its sprite's contact frame; 0 when it applies at the end.
    float attackImpactLeadSeconds = 0.0f;
    float visualScale = 1.0f;
    int16_t monsterId = 0;
    int32_t mm9RudeId = 0;
    uint32_t mm9SourceObjectIndex = 0;
    float preciseX = 0.0f;
    float preciseY = 0.0f;
    float preciseZ = 0.0f;
    uint16_t radius = 0;
    // Collision height: indoors at least 2 x radius + 2, so wide monsters fit the floor/ceiling sweep.
    uint16_t height = 0;
    // The actor's own height (map placement or descriptor), unpadded; presentation (3D model scale) uses this.
    uint16_t bodyHeight = 0;
    // Its 3D model's scale against its binding's (scene draw_scale); when set it replaces bodyHeight's ratio to the
    // descriptor's height. 0: none.
    float drawScale = 0.0f;
    bool isDead = false;
    bool isInvisible = false;
    bool hostileToParty = false;
    bool hasDetectedParty = false;
    bool combatTargetingParty = false;
    // The party member whose spell summoned the actor, -1 for none.
    int32_t summonerMemberIndex = -1;
    int currentHp = 0;
    int maxHp = 0;
    // What the ruleset resolved for the actor (empty under Standard).
    ActorRulesetFacts rulesetFacts;
    // A behaviour script's clip role (actors.yml `script_clips`; `fidget` the binding's own fidget) and its playback
    // time; empty when none plays. Past its end it holds its last frame, loops, or releases the actor's own animation.
    std::string scriptedClip;
    // Clips that follow scriptedClip in order (a map script's clip sequence); the end rule applies to the last one.
    std::vector<std::string> scriptedClipThen;
    float scriptedClipSeconds = 0.0f;
    enum class ScriptedClipEnd : uint8_t
    {
        Hold,
        Loop,
        Release,
    };
    ScriptedClipEnd scriptedClipEnd = ScriptedClipEnd::Hold;
    // Hit flash mixed over the sprite or model (GameplayActorHitFeedback), 0 when none.
    float hitFlash = 0.0f;
    // Multiplier of the model's emission (a frenzy's glow, GameplayActorModifiers), 1 when none.
    float emissionMultiplier = 1.0f;
    // Energy shield (GameplayActorShields); `present` is false for every monster without a shield profile.
    GameplayActorShieldView shield;
    // The target an actor with tactics is engaging (ActorBehaviorRuntime; its attack aim point), for a model whose
    // look follows its combat target (actors.yml `look.target: combat`). Unset for every other actor.
    bool hasAimTarget = false;
    float aimTargetX = 0.0f;
    float aimTargetY = 0.0f;
    float aimTargetZ = 0.0f;
    // An idle turret scanning (tactics `scan`): its look holds `hold_clip` and pitches its nodes to aimScanPitchRadians
    // (the body's yaw is the scan itself). Unset for every other actor.
    bool aimScanning = false;
    float aimScanPitchRadians = 0.0f;
    // An actor on MM9's loop (MM9_AMBIENT_ANIMATION.md section 2.4): its model's look turns only toward the target its
    // AI holds (the party, or another actor's head at heldTarget*) or toward the party talking to it, never toward a
    // party that is merely near; headTurn false (its row's HeadTurn 0): its head turns toward nothing.
    bool looksAtHeldTarget = false;
    bool headTurn = true;
    bool holdsPartyTarget = false;
    bool holdsActorTarget = false;
    float heldTargetX = 0.0f;
    float heldTargetY = 0.0f;
    float heldTargetZ = 0.0f;
    uint32_t npcId = 0;
    uint32_t group = 0;
};

struct GameplayCombatFeedbackEvent
{
    size_t actorIndex = 0;
    int damage = 0;
    // Points a raised energy shield took instead (the body took none): shown as a blue number.
    int shieldDamage = 0;
    int experience = 0;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float height = 0.0f;
    bool killed = false;
};

enum class GameplayActorControlMode : uint8_t
{
    None = 0,
    Charm = 1,
    Berserk = 2,
    Enslaved = 3,
    ControlUndead = 4,
    Reanimated = 5,
};

// How long evt.TurnActor's "for good" lasts: a control that never runs out in play (about thirty years).
constexpr float TurnedForGoodSeconds = 1.0e9f;

// A monster that fights for the party for good (MAW's Ally 9999): a summon, controlled undead, the reanimated. A
// charmed or berserk monster is only borrowed.
inline bool gameplayActorFightsForParty(GameplayActorControlMode mode)
{
    return mode == GameplayActorControlMode::Enslaved || mode == GameplayActorControlMode::ControlUndead
        || mode == GameplayActorControlMode::Reanimated;
}

enum class GameplayActorAiType : uint8_t
{
    Suicide = 0,
    Wimp = 1,
    Normal = 2,
    Aggressive = 3,
};

enum class GameplayActorAttackAbility : uint8_t
{
    Attack1 = 0,
    Attack2 = 1,
    Spell1 = 2,
    Spell2 = 3,
};

struct GameplayActorInspectState
{
    std::string displayName;
    std::string previewTextureName;
    size_t uniqueActorIndex = static_cast<size_t>(-1);
    int16_t monsterId = 0;
    int16_t previewPaletteId = 0;
    int previewYOffset = -40;
    int currentHp = 0;
    int maxHp = 0;
    int armorClass = 0;
    MonsterTable::MonsterStatsEntry::DamageProfile attack1Damage = {};
    MonsterTable::MonsterStatsEntry::DamageProfile attack2Damage = {};
    int attack2Chance = 0;
    bool hasSpell1 = false;
    bool hasSpell2 = false;
    std::string spell1Name;
    std::string spell2Name;
    uint32_t spell1SkillLevel = 0;
    SkillMastery spell1SkillMastery = SkillMastery::None;
    uint32_t spell2SkillLevel = 0;
    SkillMastery spell2SkillMastery = SkillMastery::None;
    bool isDead = false;
    float slowRemainingSeconds = 0.0f;
    float stunRemainingSeconds = 0.0f;
    float paralyzeRemainingSeconds = 0.0f;
    float fearRemainingSeconds = 0.0f;
    float shrinkRemainingSeconds = 0.0f;
    float darkGraspRemainingSeconds = 0.0f;
    // How long the actor's charm, berserk or enslavement (controlMode) still holds.
    float controlRemainingSeconds = 0.0f;
    float dayOfProtectionRemainingSeconds = 0.0f;
    float hourOfPowerRemainingSeconds = 0.0f;
    float painReflectionRemainingSeconds = 0.0f;
    float hammerhandsRemainingSeconds = 0.0f;
    float hasteRemainingSeconds = 0.0f;
    float shieldRemainingSeconds = 0.0f;
    float stoneskinRemainingSeconds = 0.0f;
    float blessRemainingSeconds = 0.0f;
    float fateRemainingSeconds = 0.0f;
    float heroismRemainingSeconds = 0.0f;
    std::string pendingSelfBuffName;
    GameplayActorControlMode controlMode = GameplayActorControlMode::None;
    // What the ruleset resolved for the actor (MAW: its level and boss affix); empty under Standard.
    ActorRulesetFacts rulesetFacts;
};

struct GameplayActorSpellEffectState
{
    float slowRemainingSeconds = 0.0f;
    float slowMoveMultiplier = 1.0f;
    float slowRecoveryMultiplier = 1.0f;
    float stunRemainingSeconds = 0.0f;
    float paralyzeRemainingSeconds = 0.0f;
    float fearRemainingSeconds = 0.0f;
    float blindRemainingSeconds = 0.0f;
    float controlRemainingSeconds = 0.0f;
    GameplayActorControlMode controlMode = GameplayActorControlMode::None;
    float shrinkRemainingSeconds = 0.0f;
    float shrinkDamageMultiplier = 1.0f;
    float shrinkArmorClassMultiplier = 1.0f;
    float armorClassHalvedRemainingSeconds = 0.0f;
    float darkGraspRemainingSeconds = 0.0f;
    float dayOfProtectionRemainingSeconds = 0.0f;
    int dayOfProtectionPower = 0;
    float hourOfPowerRemainingSeconds = 0.0f;
    int hourOfPowerPower = 0;
    float painReflectionRemainingSeconds = 0.0f;
    float hammerhandsRemainingSeconds = 0.0f;
    int hammerhandsPower = 0;
    float hasteRemainingSeconds = 0.0f;
    float shieldRemainingSeconds = 0.0f;
    float stoneskinRemainingSeconds = 0.0f;
    int stoneskinPower = 0;
    float blessRemainingSeconds = 0.0f;
    int blessPower = 0;
    float fateRemainingSeconds = 0.0f;
    int fatePower = 0;
    float heroismRemainingSeconds = 0.0f;
    int heroismPower = 0;
    bool hostileToParty = false;
    bool hasDetectedParty = false;
};

struct GameplayActorTargetPolicyState
{
    int16_t monsterId = 0;
    int16_t relationMonsterId = 0;
    uint32_t group = 0;
    float preciseZ = 0.0f;
    uint16_t height = 0;
    bool hostileToParty = false;
    GameplayActorControlMode controlMode = GameplayActorControlMode::None;
    uint32_t actorId = 0;
    // The monster that last hit it (the original's lastCharacterIdToHit): it fights that one back at long range.
    std::optional<uint32_t> lastActorAttackerId;
};

struct GameplayActorTargetPolicyResult
{
    bool canTarget = false;
    int relationToTarget = 0;
    float engagementRange = 0.0f;
};

struct GameplayActorAttackChoiceResult
{
    GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
    uint32_t nextDecisionCount = 0;
};

struct GameplayActorAttackConstraintState
{
    bool attack1IsRanged = false;
    bool attack2IsRanged = false;
    bool blindActive = false;
    bool darkGraspActive = false;
    bool rangedCommitAllowed = true;
};

struct GameplayPartySpellProjectileRequest
{
    uint32_t casterMemberIndex = 0;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int damage = 0;
    CombatDamageType damageType = CombatDamageType::Physical;
    float sourceX = 0.0f;
    float sourceY = 0.0f;
    float sourceZ = 0.0f;
    float targetX = 0.0f;
    float targetY = 0.0f;
    float targetZ = 0.0f;
    uint32_t effectSoundIdOverride = 0;
    uint32_t impactSoundIdOverride = 0;
    bool turnBasedPendingAction = false;
    // The actor the spell was aimed at, for rules whose missiles home (MAW).
    std::optional<size_t> targetActorIndex;
    // Its damage was a critical hit (the status line and combat log say so where it lands).
    bool critical = false;
};

enum class GameplayProjectileVisualMode
{
    SpriteBillboard,
    FxOnly,
};

struct GameplayProjectilePresentationState
{
    uint32_t projectileId = 0;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    GameplayProjectileVisualMode visualMode = GameplayProjectileVisualMode::SpriteBillboard;
    uint16_t radius = 0;
    uint16_t height = 0;
    int spellId = 0;
    // The monster that threw it (0: party, event or unknown), for per-monster enhanced visuals.
    int16_t sourceMonsterId = 0;
    std::string objectName;
    std::string objectSpriteName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float velocityZ = 0.0f;
    uint32_t timeSinceCreatedTicks = 0;
    int16_t sectorId = -1;
    bool isSettled = false;
};

// An item lying on the ground (or dropped and still falling), for its 3D model.
struct GameplayWorldItemPresentationState
{
    // Stable while the item lies there: the world's item id outdoors, its map object index indoors.
    uint32_t key = 0;
    uint32_t itemId = 0;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    int16_t sectorId = -1;
    // In flight or sliding: drawn flat at its simulated height; at rest it is fitted to the ground under it.
    bool moving = false;
    // Floats where it was placed (NoGravity objects): never fitted to the ground.
    bool floating = false;
    // A treasure bag holding loot rather than an item: it draws lootBagModelBinding().
    bool lootBag = false;
    WorldItemSparkle sparkle = WorldItemSparkle::None;
    // A placed item's authored pose (a scene world item's `pose`): drawn turned so, resting on its position.
    std::optional<WorldItemPose> pose;
};

// A projectile that ended (hit something or ran out of lifetime) and where it stopped, so its flight effect can
// reach that point before it fades.
struct GameplayProjectileEndPresentationState
{
    uint32_t projectileId = 0;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct GameplayProjectileImpactPresentationState
{
    uint32_t effectId = 0;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t sourceObjectFlags = 0;
    int sourceSpellId = 0;
    int16_t sourceMonsterId = 0;
    // The unit direction the projectile flew when it struck; zero when unknown.
    float flightDirectionX = 0.0f;
    float flightDirectionY = 0.0f;
    float flightDirectionZ = 0.0f;
    std::string objectName;
    std::string objectSpriteName;
    std::string sourceObjectName;
    std::string sourceObjectSpriteName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    uint32_t timeSinceCreatedTicks = 0;
    uint32_t lifetimeTicks = 0;
    int16_t sectorId = -1;
    size_t targetActorIndex = static_cast<size_t>(-1);
    bool freezeAnimation = false;
};

struct GameplayHeldItemDropRequest
{
    InventoryItem item = {};
    float sourceX = 0.0f;
    float sourceY = 0.0f;
    float sourceZ = 0.0f;
    float yawRadians = 0.0f;
};

struct GameplayWorldPoint
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct GameplayPartyAttackActorFacts
{
    size_t actorIndex = 0;
    int16_t monsterId = 0;
    std::string displayName;
    GameplayWorldPoint position = {};
    uint16_t radius = 0;
    uint16_t height = 0;
    int currentHp = 0;
    int maxHp = 0;
    int effectiveArmorClass = 0;
    int hourOfPowerPower = 0;
    ActorRulesetFacts rulesetFacts;
    bool isDead = false;
    bool isInvisible = false;
    bool hostileToParty = false;
    bool visibleForFallback = false;
    bool lineOfSightToParty = true;
};

// A debuff a party member's hit leaves on an actor (MAW's Death Grasp and Icy Touch).
enum class GameplayActorHitDebuff : uint8_t
{
    DarkGrasp,
    Slow,
};

struct GameplayCombatActorInfo
{
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    int monsterLevel = 0;
    int currentHp = 0;
    int maxHp = 0;
    uint32_t attackPreferences = 0;
    int attackBonus = 0;
    bool bolsterAffectsPlayerArmorClass = false;
    MonsterSpecialAttackKind specialAttackKind = MonsterSpecialAttackKind::None;
    int specialAttackLevel = 0;
    std::string displayName;
    // Shrinking Ray or Dark Grasp holds the attacker; rules that recompute its damage cut it themselves.
    bool damageDebuffed = false;
    // What the ruleset resolved for the attacker (empty under Standard).
    ActorRulesetFacts rulesetFacts;
    // spell_conditions (MonsterModifiers.h): the condition a hit by its Spell1 / Spell2 leaves, the chance (0-1), and
    // the game minutes until it wears off (0: until cured).
    MonsterSpecialAttackKind spell1Condition = MonsterSpecialAttackKind::None;
    MonsterSpecialAttackKind spell2Condition = MonsterSpecialAttackKind::None;
    float spellConditionChance = 1.0f;
    float spell1ConditionMinutes = 0.0f;
    float spell2ConditionMinutes = 0.0f;
};

struct GameplayPartyAttackSpellRequest
{
    size_t sourcePartyMemberIndex = 0;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    uint32_t skillMastery = 0;
    int damage = 0;
    int attackBonus = 0;
    bool useActorHitChance = false;
    GameplayWorldPoint source = {};
    GameplayWorldPoint target = {};
};

struct GameplayPartyAttackProjectileRequest
{
    size_t sourcePartyMemberIndex = 0;
    uint32_t objectId = 0;
    uint32_t impactObjectId = 0;
    // Its impact's sound (a party gun's world missile), 0: the object's own.
    uint32_t impactSoundId = 0;
    int damage = 0;
    int attackBonus = 0;
    bool useActorHitChance = false;
    CombatDamageType damageType = CombatDamageType::Physical;
    ShieldAttackTier shieldTier = ShieldAttackTier::Physical;
    ShieldHitModifiers shieldModifiers;
    // Resisted by the lower of the monster's physical and fire resistance (MAW's Grandmaster fire arrows).
    bool weakerOfPhysicalAndFire = false;
    // The radius the missile's damage reaches around its impact (Carnage arrows); 0 strikes only what it hits.
    float explosionRadius = 0.0f;
    GameplayWorldPoint source = {};
    GameplayWorldPoint target = {};
    bool turnBasedPendingAction = false;
    // The actor the shot was aimed at, for rules whose missiles home (MAW).
    std::optional<size_t> targetActorIndex;
    // Its shots home (CharacterAttackResult::homing).
    bool homing = false;
    // Its damage was a critical hit (CharacterAttackResult::criticalDamage).
    bool critical = false;
};

struct GameplayPartyAttackFallbackQuery
{
    float screenX = 0.0f;
    float screenY = 0.0f;
    int viewWidth = 0;
    int viewHeight = 0;
    std::array<float, 16> viewMatrix = {};
    std::array<float, 16> projectionMatrix = {};
};

struct GameplayPartyAttackFrameInput
{
    bool enabled = false;
    GameplayWorldPoint partyPosition = {};
    GameplayWorldPoint rangedSource = {};
    GameplayWorldPoint rangedRight = {};
    GameplayWorldPoint defaultRangedTarget = {};
    GameplayWorldPoint rayRangedTarget = {};
    bool hasRayRangedTarget = false;
    GameplayPartyAttackFallbackQuery fallbackQuery = {};
};

enum class GameplayInteractionMethod
{
    Keyboard,
    Mouse,
};

class IGameplayWorldRuntime
{
public:
    virtual ~IGameplayWorldRuntime() = default;

    virtual const std::string &mapName() const = 0;
    virtual const MonsterTable *monsterTable() const
    {
        return nullptr;
    }
    virtual const MergedBolsterMonsterTable *mergedBolsterMonsterTable() const
    {
        return nullptr;
    }
    virtual GameplayWorldPoint chooseBountyHuntSpawnPoint(uint32_t seed) const
    {
        (void)seed;
        return GameplayWorldPoint{partyX() + 1024.0f, partyY(), partyFootZ()};
    }
    virtual bool isIndoorMap() const = 0;
    // Whether the map lies open to the sky for spells: an outdoor map that is not enclosed, or a BLV its world declares
    // open (world.yml openAirMaps, MapStatsEntry::openAir). Meteor Shower and the other outdoor spells work there,
    // Inferno and Prismatic Light do not.
    virtual bool isOpenAirMap() const
    {
        return !isIndoorMap();
    }
    // The party is on a ladder (the flight arrows then climb it).
    virtual bool partyClimbingLadder() const
    {
        return false;
    }
    // The party swims in a scene water volume (the flight arrows then swim up and down).
    virtual bool partySwimming() const
    {
        return false;
    }
    // The party's breath left (1 full) while its eye is under a scene water volume; none otherwise (the HUD's meter).
    virtual std::optional<float> partyBreathFraction() const
    {
        return std::nullopt;
    }
    virtual bool isUnderwaterMap() const
    {
        return false;
    }
    virtual bool allowsLloydsBeacon() const
    {
        return true;
    }
    virtual bool allowsRest() const
    {
        return true;
    }
    virtual float gameMinutes() const = 0;
    virtual int currentHour() const = 0;
    virtual const std::vector<uint8_t> *journalMapFullyRevealedCells() const = 0;
    virtual const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const = 0;
    virtual int restFoodRequired() const = 0;
    virtual void advanceGameMinutes(float minutes) = 0;
    virtual void applyMapReentryReset()
    {
    }
    // Resolves the living actors' ruleset numbers again (a difficulty change).
    virtual void refreshRulesetMonsters() = 0;
    // Restores up to `amount` HP of a living actor (ruleset effects such as MAW's Regenerating bosses).
    virtual bool healMapActor(size_t actorIndex, int amount) = 0;
    // The ruleset facts of a living actor for rules that change them as it is hit (MAW's Spear stacks), or null.
    virtual ActorRulesetFacts *mutableActorRulesetFacts(size_t actorIndex) = 0;
    virtual int currentLocationReputation() const = 0;
    virtual void setCurrentLocationReputation(int reputation) = 0;
    virtual void applyEventRuntimeState(bool syncPersistentHostilityMasks = false)
    {
        static_cast<void>(syncPersistentHostilityMasks);
    }
    // The world's event context (map actors, faces, mechanisms) for shared systems outside the event runtime (a
    // cinematic's actor steps); null in a world without one.
    virtual ISceneEventContext *sceneEventContext()
    {
        return nullptr;
    }
    virtual Party *party() = 0;
    virtual const Party *party() const = 0;
    virtual float partyX() const = 0;
    virtual float partyY() const = 0;
    virtual float partyFootZ() const = 0;
    // Places the party's feet at a point (an AI arena's party walk); nothing in a world without one.
    virtual void teleportParty(float x, float y, float footZ)
    {
        static_cast<void>(x);
        static_cast<void>(y);
        static_cast<void>(footZ);
    }
    // The map's placed ambient sounds (devdocs/AMBIENT_SOUNDS.md), or none.
    virtual const std::vector<WorldAmbientSound> *ambientSounds() const
    {
        return nullptr;
    }
    // The party's eyes: the camera height over the party's feet in this world.
    virtual float partyEyeZ() const = 0;
    virtual float partyEngagementRange() const
    {
        return 10240.0f;
    }
    // How far from the party its shots, targeted spells and area spells reach a monster (GameplayActorService::
    // partyHitReach): the yellow alert range, 5120, or a world's shorter one (MM9's 3800). Armageddon strikes the
    // whole map.
    virtual float partyHitReach() const
    {
        return 5120.0f;
    }
    virtual float gameplayCameraYawRadians() const
    {
        return 0.0f;
    }
    virtual float gameplayCameraPitchRadians() const
    {
        return 0.0f;
    }
    // Width over height of the view the party sees through; the narrowest supported view until one is drawn.
    virtual float gameplayViewAspectRatio() const
    {
        return 4.0f / 3.0f;
    }
    virtual bool partyIsAirborneForRest() const
    {
        return false;
    }
    virtual bool partyIsFlyingForEventChecks() const
    {
        return false;
    }
    virtual bool partyIsActivelyFlyingForHud() const
    {
        return false;
    }
    // The party stands on water it would otherwise drown in (Water Walk carries it).
    virtual bool partyIsWalkingOnWaterForHud() const
    {
        return false;
    }
    virtual bool partyNeedsTurnBasedPhysicsUpdate() const
    {
        return false;
    }
    virtual void syncSpellMovementStatesFromPartyBuffs() = 0;
    virtual void requestPartyJump(float verticalVelocity = 0.0f, float lift = 1.0f) = 0;
    virtual void setAlwaysRunEnabled(bool enabled) = 0;
    virtual void updateWorldMovement(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput) = 0;
    virtual const GameplayWorldMovementFrameDiagnostics *lastWorldMovementFrameDiagnostics() const
    {
        return nullptr;
    }
    virtual void setScenarioPartyActorCollisionEnabled(bool enabled)
    {
        (void)enabled;
    }
    virtual void updateActorAi(float deltaSeconds) = 0;
    virtual void updateTurnBasedPausedActorAnimations(float deltaSeconds)
    {
        (void)deltaSeconds;
    }
    virtual size_t turnBasedPendingWorldActionCount() const
    {
        return 0;
    }
    // The Yell key: villagers (MonsterKind::Peasant) that can act, are not hostile and stand within radius of the
    // party flee from it for the given seconds (OE Party::yell; guards and calm monsters keep their ground).
    virtual void scareNearbyPeasants(float radius, float seconds)
    {
        (void)radius;
        (void)seconds;
    }
    virtual bool turnBasedActorActionInProgress() const
    {
        return false;
    }
    virtual void stopTurnBasedActorMovement()
    {
    }
    // The turn engine schedules turn-based actor actions; the world applies them to actor AI.
    virtual void setTurnBasedActorMode(ActorTurnBasedMode mode)
    {
        (void)mode;
    }
    // Turn-based combat: the monsters' spell effects (stun, paralysis, slow, their buffs) run down once per completed
    // turn by its game time, in equivalent real seconds, instead of by actor AI time (the original's game clock).
    virtual void advanceTurnBasedActorTimers(float seconds)
    {
        (void)seconds;
    }
    // Lets the actor take its queued action (attack when it can) in the next actor AI step.
    virtual void grantTurnBasedActorAction(size_t actorIndex)
    {
        (void)actorIndex;
    }
    virtual bool turnBasedActorActionGrantPending() const
    {
        return false;
    }
    // Monster recovery in turn-based initiative ticks, doubled while the actor is slowed.
    virtual int turnBasedActorRecoveryTicks(size_t actorIndex) const
    {
        (void)actorIndex;
        return 100;
    }
    virtual void setActorAttackCooldownSeconds(size_t actorIndex, float seconds)
    {
        (void)actorIndex;
        (void)seconds;
    }
    virtual void updateWorld(float deltaSeconds) = 0;
    virtual void renderWorld(
        int width,
        int height,
        const GameplayInputFrame &input,
        float deltaSeconds) = 0;
    virtual GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const = 0;
    virtual bool requestTravelAutosave() = 0;
    virtual void cancelPendingMapTransition() = 0;
    virtual bool executeNpcTopicEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) = 0;
    virtual bool executeMapEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) = 0;
    virtual bool executeEventHooks(EventRuntimeHookKind kind)
    {
        (void)kind;
        return false;
    }
    virtual const std::optional<ScriptedEventProgram> *globalEventProgram() const = 0;
    virtual const MapDeltaData *mapDeltaData() const
    {
        return nullptr;
    }
    virtual MapDeltaData *mapDeltaData()
    {
        return nullptr;
    }
    virtual EventRuntimeState *eventRuntimeState() = 0;
    virtual const EventRuntimeState *eventRuntimeState() const = 0;
    virtual bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ) = 0;
    // The current map when it is an Arena (its definition is set).
    virtual const MapStatsEntry *arenaMap() const
    {
        return nullptr;
    }
    virtual size_t mapActorCount() const = 0;
    virtual bool actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const = 0;
    // The actor as the rules read it; a world may answer it without building the full runtime state.
    virtual bool actorRulesView(size_t actorIndex, GameplayActorRulesView &view) const
    {
        GameplayRuntimeActorState state = {};

        if (!actorRuntimeState(actorIndex, state))
        {
            return false;
        }

        view.actorId = state.actorId;
        view.monsterId = state.monsterId;
        view.preciseX = state.preciseX;
        view.preciseY = state.preciseY;
        view.preciseZ = state.preciseZ;
        view.radius = state.radius;
        view.isDead = state.isDead;
        view.isInvisible = state.isInvisible;
        view.hostileToParty = state.hostileToParty;
        view.hasDetectedParty = state.hasDetectedParty;
        view.currentHp = state.currentHp;
        view.maxHp = state.maxHp;
        view.rulesetFacts = state.rulesetFacts;
        return true;
    }
    virtual GameplayActorHitFeedback &actorHitFeedback() = 0;
    virtual const GameplayActorHitFeedback &actorHitFeedback() const = 0;
    // The actors' energy shields (null for a world without actors).
    virtual GameplayActorShields *actorShields()
    {
        return nullptr;
    }
    virtual const GameplayActorShields *actorShields() const
    {
        return nullptr;
    }
    // Stuns a living actor for at least `seconds`, without damage or knockback (the EMP grenade on machines).
    virtual bool stunActor(size_t actorIndex, float seconds)
    {
        (void)actorIndex;
        (void)seconds;
        return false;
    }
    // Holds a living actor under a hit debuff for at least `seconds`; Slow divides its speed and multiplies its
    // recovery by `power`, never weakening a stronger slow.
    virtual bool debuffActor(size_t actorIndex, GameplayActorHitDebuff debuff, float seconds, float power)
    {
        (void)actorIndex;
        (void)debuff;
        (void)seconds;
        (void)power;
        return false;
    }
    virtual ActorBehaviorRuntime *actorBehaviorRuntime()
    {
        return nullptr;
    }
    virtual const ActorBehaviorRuntime *actorBehaviorRuntime() const
    {
        return nullptr;
    }
    // Gold plus item value left in a dead actor's corpse (its loot is rolled at death); nullopt without corpse loot.
    virtual std::optional<uint32_t> corpseLootValue(size_t actorIndex) const
    {
        (void)actorIndex;
        return std::nullopt;
    }
    // Telepathy: what a living actor will leave when it dies. Its gold and random item are rolled now and kept for
    // its corpse, so the reveal holds; nullopt when the actor is dead, invisible or unknown.
    virtual std::optional<GameplayCorpseViewState> revealActorLoot(size_t actorIndex)
    {
        (void)actorIndex;
        return std::nullopt;
    }
    virtual bool tryStealFromActor(size_t actorIndex, uint32_t successRoll, uint32_t caughtRoll)
    {
        (void)actorIndex;
        (void)successRoll;
        (void)caughtRoll;
        return false;
    }
    virtual bool actorInspectState(
        size_t actorIndex,
        uint32_t animationTicks,
        GameplayActorInspectState &state) const = 0;
    virtual std::optional<GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const = 0;
    virtual bool applyReflectedDamageToActor(
        uint32_t actorId,
        int damage,
        CombatDamageType damageType,
        uint32_t sourcePartyMemberIndex)
    {
        (void)actorId;
        (void)damage;
        (void)damageType;
        (void)sourcePartyMemberIndex;
        return false;
    }
    virtual bool castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request) = 0;
    virtual bool applyPartySpellToActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex,
        bool critical) = 0;
    virtual std::vector<size_t> collectMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        bool requireLineOfSight,
        float sourceX,
        float sourceY,
        float sourceZ) const = 0;
    virtual std::vector<size_t> collectVisibleMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        float sourceX,
        float sourceY,
        float sourceZ,
        float viewX,
        float viewY,
        float viewZ,
        float viewYawRadians,
        float viewPitchRadians,
        float viewAspectRatio) const
    {
        (void)viewX;
        (void)viewY;
        (void)viewZ;
        (void)viewYawRadians;
        (void)viewPitchRadians;
        (void)viewAspectRatio;
        return collectMapActorIndicesWithinRadius(centerX, centerY, centerZ, radius, true, sourceX, sourceY, sourceZ);
    }
    // Items lying on the ground (their models replace the sprites, GROUND_ITEMS_3D_PLAN.md). None by default.
    virtual void collectWorldItemPresentationStates(std::vector<GameplayWorldItemPresentationState> &items) const
    {
        items.clear();
    }
    // Armed party Fire Spike traps, as settled projectiles (their models lie on the ground). None by default.
    virtual void collectFireSpikeTrapPresentationStates(std::vector<GameplayProjectilePresentationState> &traps) const
    {
        traps.clear();
    }
    virtual bool spawnPartyFireSpikeTrap(
        uint32_t casterMemberIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        float x,
        float y,
        float z) = 0;
    // `summonerMemberIndex`: the party member whose spell summons them, -1 for none (MM8's Summoner field).
    virtual bool summonFriendlyMonsterById(
        int16_t monsterId,
        uint32_t count,
        float durationSeconds,
        float x,
        float y,
        float z,
        int32_t summonerMemberIndex) = 0;
    // Debug and scenarios: the actor fires its attack or spell at the party now, through the path of an AI shot (a
    // true_aim monster's shot homes), with `damage`, regardless of range, recovery and sight. Worlds without support
    // return false.
    virtual bool debugFireActorProjectileAtParty(size_t actorIndex, GameplayActorAttackAbility ability, int damage)
    {
        (void)actorIndex;
        (void)ability;
        (void)damage;
        return false;
    }
    // Blinks the actor now as its blink modifier would (MonsterModifiers); false without one or without a free spot.
    virtual bool blinkActor(size_t actorIndex)
    {
        (void)actorIndex;
        return false;
    }
    // An actor script's self:suspendShield / self:restoreShield: its energy shield down without regeneration for the
    // seconds (negative: until restored), or regenerating again. False without a shield.
    virtual bool suspendActorShield(size_t actorIndex, float seconds)
    {
        (void)actorIndex;
        (void)seconds;
        return false;
    }
    virtual bool restoreActorShield(size_t actorIndex)
    {
        (void)actorIndex;
        return false;
    }
    // Swaps the places of a living actor and another one, or the party without one (MAW's Swapper bosses); the
    // actors keep their homes. False where the world cannot.
    virtual bool swapActorPlaces(size_t actorIndex, std::optional<size_t> otherActorIndex)
    {
        (void)actorIndex;
        (void)otherActorIndex;
        return false;
    }
    // Indoors, marks the living actors within `radius` of the actor as having seen the party (MM's ShowOnMap: awake,
    // and on the Wizard Eye map; MAW's Doom reveal); returns how many it marked. Outdoors: none.
    virtual size_t revealActorsAround(size_t actorIndex, float radius)
    {
        (void)actorIndex;
        (void)radius;
        return 0;
    }
    // Pushes a living actor about `distance` units along the unit direction, staggering it whatever it was doing
    // (MAW's dragon bites); false for a dead actor or where the world cannot.
    virtual bool pushActor(size_t actorIndex, float directionX, float directionY, float distance)
    {
        (void)actorIndex;
        (void)directionX;
        (void)directionY;
        (void)distance;
        return false;
    }
    // Dashes the party `distance` units along the unit direction over a third of a second, with the world's collision
    // (MAW's Knight Charge); false where the world cannot.
    virtual bool dashParty(float directionX, float directionY, float distance)
    {
        (void)directionX;
        (void)directionY;
        (void)distance;
        return false;
    }
    // Raises the party by `height` in place, to fall back from there (MAW's unstuck key); false where the world cannot.
    virtual bool liftParty(float height)
    {
        (void)height;
        return false;
    }
    // Moves at most `maxCount` lootable corpses in front of the party (MAW's gather key, LootGatherDistances); returns
    // how many moved.
    virtual size_t gatherCorpsesToParty(size_t maxCount)
    {
        (void)maxCount;
        return 0;
    }
    // Moves at most `maxCount` ground items that `gathers` accepts in front of the party; returns how many moved.
    virtual size_t gatherWorldItemsToParty(size_t maxCount, const std::function<bool(const InventoryItem &)> &gathers)
    {
        (void)maxCount;
        (void)gathers;
        return 0;
    }
    // The dead actors whose satchels can still be looted (MAW's gather key on a completed map loots them all).
    virtual std::vector<size_t> lootableCorpseActorIndices() const
    {
        return {};
    }
    // Opens an actor's satchel as the active corpse view, as clicking it does; false when it holds nothing.
    virtual bool openActorCorpseView(size_t actorIndex)
    {
        (void)actorIndex;
        return false;
    }
    // Launches the party as the event Jump does: a heading and horizontal and vertical speeds in the event's units
    // (MAW's Puller bosses).
    virtual bool launchParty(float headingRadians, float horizontalSpeed, float verticalSpeed)
    {
        (void)headingRadians;
        (void)horizontalSpeed;
        (void)verticalSpeed;
        return false;
    }
    // Starts the actor's charge at the party now (its wind-up, then the dash), regardless of its trigger band, sight
    // and cooldown; false without the charge modifier or while it charges already.
    virtual bool chargeActor(size_t actorIndex)
    {
        (void)actorIndex;
        return false;
    }
    // Starts the actor's frenzy now (its roar, then the frenzy), regardless of its triggers and cooldown; false
    // without the frenzy modifier, while it is in a frenzy or while it charges.
    virtual bool frenzyActor(size_t actorIndex)
    {
        (void)actorIndex;
        return false;
    }
    // Charges on this map so far (scenario checks, console); empty for a world without charges.
    virtual std::optional<GameplayChargeCounts> chargeCounts() const
    {
        return std::nullopt;
    }
    // The world's projectiles (scenario checks, debug); null for a world without them.
    virtual const GameplayProjectileService *projectileServiceView() const
    {
        return nullptr;
    }
    // Debug: the actor launches its attack or spell projectile at a point now, regardless of range, recovery and
    // targeting, for reviewing projectile visuals. Worlds without support return false.
    virtual bool debugFireActorProjectile(
        size_t actorIndex,
        GameplayActorAttackAbility ability,
        const GameplayWorldPoint &target)
    {
        (void)actorIndex;
        (void)ability;
        (void)target;
        return false;
    }
    // How far the party has cleared this map (slain and living hostile monsters); false for a world without monsters.
    virtual bool mapKillProgress(MapKillProgress &progress) const
    {
        (void)progress;
        return false;
    }
    // Raises the slain ordinary monsters (no bosses, named actors or NPCs) where they fell, at full health, as
    // "Resurrected <name>", worth this share of their experience; those whose corpse was searched carry no loot
    // (MAW's Nightmare). Returns how many rose; a world without support raises none.
    virtual size_t reviveSlainMonsters(float experienceShare)
    {
        (void)experienceShare;
        return 0;
    }
    // Feeds the AI decision trace (an AI arena) after every AI step and applies its overrides; null unbinds. The
    // trace outlives the binding (GameApplication owns it).
    virtual void bindActorAiTrace(ActorAiTrace *pTrace)
    {
        (void)pTrace;
    }
    virtual const ActorAiTrace *actorAiTrace() const
    {
        return nullptr;
    }
    // Places a script's monsters (GameplayMonsterSpawnRequest) and returns their actor indices; a world without
    // support places none.
    virtual std::vector<size_t> spawnMonsters(const GameplayMonsterSpawnRequest &request)
    {
        (void)request;
        return {};
    }
    virtual bool summonHostileMonsterById(
        int16_t monsterId,
        uint32_t count,
        float x,
        float y,
        float z,
        uint32_t group)
    {
        (void)monsterId;
        (void)count;
        (void)x;
        (void)y;
        (void)z;
        (void)group;
        return false;
    }
    virtual bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        std::string &failureText) = 0;
    virtual bool canActivateWorldHit(
        const GameplayWorldHit &hit,
        GameplayInteractionMethod interactionMethod) const = 0;
    virtual bool activateWorldHit(const GameplayWorldHit &hit) = 0;
    virtual bool activateWorldHitFromSpell(const GameplayWorldHit &hit, uint32_t spellId)
    {
        (void)spellId;
        return activateWorldHit(hit);
    }
    virtual bool canActivateTelekinesisTarget(const GameplayWorldHit &hit) const = 0;
    virtual bool activateTelekinesisTarget(const GameplayWorldHit &hit) = 0;
    virtual std::optional<GameplayPartyAttackActorFacts> partyAttackActorFacts(
        size_t actorIndex,
        bool visibleForFallback) const = 0;
    virtual std::vector<GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const GameplayPartyAttackFallbackQuery &query) const = 0;
    virtual std::optional<GameplayWorldPoint> partyAttackActorContactPoint(
        size_t actorIndex,
        const GameplayPartyAttackFallbackQuery &query) const
    {
        (void)actorIndex;
        (void)query;
        return std::nullopt;
    }
    // shieldTier: what the blow is to an energy shield (GameplayActorShields); shieldModifiers: what the weapon's tech
    // skill adds to it.
    virtual bool applyPartyAttackMeleeDamage(
        size_t actorIndex,
        int damage,
        const GameplayWorldPoint &source,
        ShieldAttackTier shieldTier,
        const ShieldHitModifiers &shieldModifiers = {}) = 0;
    virtual bool applyPartyAttackMeleeBModelDamage(size_t bModelIndex, int damage)
    {
        (void)bModelIndex;
        (void)damage;
        return false;
    }
    virtual bool isPartyAttackMeleeBModelTarget(size_t bModelIndex) const
    {
        (void)bModelIndex;
        return false;
    }
    // A destructible decoration (an indoor entity index) a party blow damages.
    virtual bool applyPartyAttackMeleeEntityDamage(size_t entityIndex, int damage)
    {
        (void)entityIndex;
        (void)damage;
        return false;
    }
    virtual bool isPartyAttackMeleeEntityTarget(size_t entityIndex) const
    {
        (void)entityIndex;
        return false;
    }
    virtual void applyPartyAttackMeleeEffects(
        size_t actorIndex,
        const CharacterAttackResult &attack,
        const GameplayWorldPoint &source)
    {
        (void)actorIndex;
        (void)attack;
        (void)source;
    }
    virtual bool spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request) = 0;
    virtual bool castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request) = 0;
    virtual std::vector<GameplayCombatFeedbackEvent> drainCombatFeedbackEvents()
    {
        return {};
    }
    virtual void recordPartyAttackWorldResult(
        std::optional<size_t> actorIndex,
        bool attacked,
        bool actionPerformed) = 0;
    virtual bool worldInteractionReady() const = 0;
    virtual bool worldInspectModeActive() const = 0;
    virtual GameplayWorldPickRequest buildWorldPickRequest(const GameplayWorldPickRequestInput &input) const = 0;
    virtual std::optional<GameplayHeldItemDropRequest> buildHeldItemDropRequest() const = 0;
    virtual GameplayPartyAttackFrameInput buildPartyAttackFrameInput(
        const GameplayWorldPickRequest &pickRequest) const = 0;
    virtual std::optional<size_t> spellActionHoveredActorIndex() const = 0;
    // The hostile actors a party spell may take without a cursor target: on screen, in line of sight and aware of the
    // party, closest first. Built only when a cast asks.
    virtual std::vector<size_t> spellActionVisibleHostileActorIndices() const = 0;
    virtual std::optional<bx::Vec3> spellActionActorTargetPoint(size_t actorIndex) const = 0;
    virtual std::optional<bx::Vec3> spellActionGroundTargetPoint(float screenX, float screenY) const = 0;
    virtual GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        const GameplayWorldPickRequest &request) = 0;
    virtual GameplayWorldHit pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request) = 0;
    virtual GameplayWorldHit pickHeldItemWorldTarget(const GameplayWorldPickRequest &request) = 0;
    virtual GameplayWorldHit pickMouseInteractionTarget(const GameplayWorldPickRequest &request) = 0;
    virtual GameplayWorldHit pickPartyAttackTarget(const GameplayWorldPickRequest &request)
    {
        return pickMouseInteractionTarget(request);
    }
    virtual bool hasCustomWorldItemActivation(size_t worldItemIndex) const
    {
        (void)worldItemIndex;
        return false;
    }
    virtual bool activateCustomWorldItem(size_t worldItemIndex)
    {
        (void)worldItemIndex;
        return false;
    }
    virtual bool worldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state) const
    {
        (void)worldItemIndex;
        (void)state;
        return false;
    }
    virtual bool updateWorldItemInspectState(size_t worldItemIndex, const InventoryItem &item)
    {
        (void)worldItemIndex;
        (void)item;
        return false;
    }
    virtual bool takeWorldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state)
    {
        (void)worldItemIndex;
        (void)state;
        return false;
    }
    virtual GameplayWorldHoverCacheState worldHoverCacheState() const = 0;
    virtual GameplayHoverStatusPayload refreshWorldHover(const GameplayWorldHoverRequest &request) = 0;
    virtual GameplayHoverStatusPayload readCachedWorldHover() = 0;
    virtual void clearWorldHover() = 0;
    virtual bool canUseHeldItemOnWorld(const GameplayWorldHit &hit) const = 0;
    virtual bool useHeldItemOnWorld(const GameplayWorldHit &hit) = 0;
    virtual void applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult) = 0;
    virtual bool dropHeldItemToWorld(const GameplayHeldItemDropRequest &request) = 0;
    virtual bool tryGetGameplayMinimapState(GameplayMinimapState &state) const = 0;
    virtual void collectGameplayMinimapLines(std::vector<GameplayMinimapLineState> &lines) = 0;
    virtual void collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const = 0;
    virtual GameplayChestViewState *activeChestView() = 0;
    virtual const GameplayChestViewState *activeChestView() const = 0;
    virtual void commitActiveChestView() = 0;
    virtual bool takeActiveChestItem(size_t itemIndex, GameplayChestItemState &item) = 0;
    virtual bool takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, GameplayChestItemState &item) = 0;
    virtual bool tryPlaceActiveChestItemAt(const GameplayChestItemState &item, uint8_t gridX, uint8_t gridY) = 0;
    virtual void closeActiveChestView() = 0;
    virtual GameplayCorpseViewState *activeCorpseView() = 0;
    virtual const GameplayCorpseViewState *activeCorpseView() const = 0;
    virtual void commitActiveCorpseView() = 0;
    virtual bool takeActiveCorpseItem(size_t itemIndex, GameplayChestItemState &item) = 0;
    virtual void closeActiveCorpseView() = 0;
};

// Where a world hit lands on a standing destructible a party blow or missile damages (a face, BModel or prop), or
// none: a party missile with no actor under the crosshair flies there (devdocs/INDOOR_DESTRUCTIBLES.md "Aiming").
inline std::optional<bx::Vec3> standingDestructibleHitPoint(
    const IGameplayWorldRuntime &worldRuntime,
    const GameplayWorldHit &hit)
{
    if (!hit.hasHit || hit.kind != GameplayWorldHitKind::EventTarget || !hit.eventTarget)
    {
        return std::nullopt;
    }

    const GameplayEventTargetHit &target = *hit.eventTarget;
    const bool standing =
        (target.targetKind == GameplayWorldEventTargetKind::Surface
            && worldRuntime.isPartyAttackMeleeBModelTarget(target.targetIndex))
        || (target.targetKind == GameplayWorldEventTargetKind::Entity
            && worldRuntime.isPartyAttackMeleeEntityTarget(target.targetIndex));
    return standing ? std::optional<bx::Vec3>(target.hitPoint) : std::nullopt;
}
}
