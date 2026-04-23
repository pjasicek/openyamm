#pragma once

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
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

struct GameplayRuntimeActorState
{
    float preciseX = 0.0f;
    float preciseY = 0.0f;
    float preciseZ = 0.0f;
    uint16_t radius = 0;
    uint16_t height = 0;
    bool isDead = false;
    bool isInvisible = false;
    bool hostileToParty = false;
    bool hasDetectedParty = false;
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
    int16_t monsterId = 0;
    int16_t previewPaletteId = 0;
    int currentHp = 0;
    int maxHp = 0;
    int armorClass = 0;
    bool isDead = false;
    float slowRemainingSeconds = 0.0f;
    float stunRemainingSeconds = 0.0f;
    float paralyzeRemainingSeconds = 0.0f;
    float fearRemainingSeconds = 0.0f;
    float shrinkRemainingSeconds = 0.0f;
    float darkGraspRemainingSeconds = 0.0f;
    GameplayActorControlMode controlMode = GameplayActorControlMode::None;
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
    float darkGraspRemainingSeconds = 0.0f;
    bool hostileToParty = false;
    bool hasDetectedParty = false;
};

struct GameplayActorTargetPolicyState
{
    int16_t monsterId = 0;
    float preciseZ = 0.0f;
    uint16_t height = 0;
    bool hostileToParty = false;
    GameplayActorControlMode controlMode = GameplayActorControlMode::None;
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
    float sourceX = 0.0f;
    float sourceY = 0.0f;
    float sourceZ = 0.0f;
    float targetX = 0.0f;
    float targetY = 0.0f;
    float targetZ = 0.0f;
};

struct GameplayProjectilePresentationState
{
    uint32_t projectileId = 0;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t objectFlags = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    int spellId = 0;
    std::string objectName;
    std::string objectSpriteName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float velocityX = 0.0f;
    float velocityY = 0.0f;
    float velocityZ = 0.0f;
    uint32_t timeSinceCreatedTicks = 0;
};

struct GameplayProjectileImpactPresentationState
{
    uint32_t effectId = 0;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    uint16_t objectSpriteFrameIndex = 0;
    uint16_t sourceObjectFlags = 0;
    int sourceSpellId = 0;
    std::string objectName;
    std::string objectSpriteName;
    std::string sourceObjectName;
    std::string sourceObjectSpriteName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    uint32_t timeSinceCreatedTicks = 0;
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
    bool isDead = false;
    bool isInvisible = false;
    bool hostileToParty = false;
    bool visibleForFallback = false;
};

struct GameplayCombatActorInfo
{
    uint32_t actorId = 0;
    int16_t monsterId = 0;
    int maxHp = 0;
    uint32_t attackPreferences = 0;
    std::string displayName;
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
    int damage = 0;
    int attackBonus = 0;
    bool useActorHitChance = false;
    GameplayWorldPoint source = {};
    GameplayWorldPoint target = {};
};

struct GameplayPartyAttackFallbackQuery
{
    std::array<float, 16> viewMatrix = {};
    std::array<float, 16> projectionMatrix = {};
};

struct GameplayPartyAttackFrameInput
{
    bool enabled = false;
    GameplayWorldPoint partyPosition = {};
    GameplayWorldPoint rangedSource = {};
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
    virtual float gameMinutes() const = 0;
    virtual int currentHour() const = 0;
    virtual const std::vector<uint8_t> *journalMapFullyRevealedCells() const = 0;
    virtual const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const = 0;
    virtual int restFoodRequired() const = 0;
    virtual void advanceGameMinutes(float minutes) = 0;
    virtual int currentLocationReputation() const = 0;
    virtual void setCurrentLocationReputation(int reputation) = 0;
    virtual Party *party() = 0;
    virtual const Party *party() const = 0;
    virtual float partyX() const = 0;
    virtual float partyY() const = 0;
    virtual float partyFootZ() const = 0;
    virtual void syncSpellMovementStatesFromPartyBuffs() = 0;
    virtual void requestPartyJump() = 0;
    virtual void setAlwaysRunEnabled(bool enabled) = 0;
    virtual void updateWorldMovement(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput) = 0;
    virtual void updateActorAi(float deltaSeconds) = 0;
    virtual void updateWorld(float deltaSeconds) = 0;
    virtual void renderWorld(
        int width,
        int height,
        const GameplayInputFrame &input,
        float deltaSeconds) = 0;
    virtual GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const = 0;
    virtual bool requestTravelAutosave() = 0;
    virtual void cancelPendingMapTransition() = 0;
    virtual bool executeNpcTopicEvent(uint16_t eventId, size_t &previousMessageCount) = 0;
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
    virtual size_t mapActorCount() const = 0;
    virtual bool actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const = 0;
    virtual bool actorInspectState(
        size_t actorIndex,
        uint32_t animationTicks,
        GameplayActorInspectState &state) const = 0;
    virtual std::optional<GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const = 0;
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
        uint32_t sourcePartyMemberIndex) = 0;
    virtual std::vector<size_t> collectMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        bool requireLineOfSight,
        float sourceX,
        float sourceY,
        float sourceZ) const = 0;
    virtual bool spawnPartyFireSpikeTrap(
        uint32_t casterMemberIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        float x,
        float y,
        float z) = 0;
    virtual bool summonFriendlyMonsterById(
        int16_t monsterId,
        uint32_t count,
        float durationSeconds,
        float x,
        float y,
        float z) = 0;
    virtual bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        std::string &failureText) = 0;
    virtual bool canActivateWorldHit(
        const GameplayWorldHit &hit,
        GameplayInteractionMethod interactionMethod) const = 0;
    virtual bool activateWorldHit(const GameplayWorldHit &hit) = 0;
    virtual std::optional<GameplayPartyAttackActorFacts> partyAttackActorFacts(
        size_t actorIndex,
        bool visibleForFallback) const = 0;
    virtual std::vector<GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const GameplayPartyAttackFallbackQuery &query) const = 0;
    virtual bool applyPartyAttackMeleeDamage(
        size_t actorIndex,
        int damage,
        const GameplayWorldPoint &source) = 0;
    virtual bool spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request) = 0;
    virtual bool castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request) = 0;
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
    virtual std::optional<size_t> spellActionClosestVisibleHostileActorIndex() const = 0;
    virtual std::optional<bx::Vec3> spellActionActorTargetPoint(size_t actorIndex) const = 0;
    virtual std::optional<bx::Vec3> spellActionGroundTargetPoint(float screenX, float screenY) const = 0;
    virtual GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        const GameplayWorldPickRequest &request) = 0;
    virtual GameplayWorldHit pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request) = 0;
    virtual GameplayWorldHit pickHeldItemWorldTarget(const GameplayWorldPickRequest &request) = 0;
    virtual GameplayWorldHit pickMouseInteractionTarget(const GameplayWorldPickRequest &request) = 0;
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
}
