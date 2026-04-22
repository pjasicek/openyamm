#pragma once

#include "game/events/ISceneEventContext.h"
#include "game/events/EventRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/maps/MapAssetLoader.h"
#include "game/maps/MapDeltaData.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterProjectileTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorMovementController.h"
#include "game/outdoor/OutdoorWeatherProfile.h"
#include "game/party/Party.h"
#include "game/tables/SpellTable.h"

#include <optional>
#include <random>
#include <string>
#include <utility>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class ChestTable;
class GameplayFxService;
class GameplayProjectileService;
class OutdoorGameView;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
class ParticleSystem;
class OutdoorPartyRuntime;

class OutdoorWorldRuntime : public ISceneEventContext, public IGameplayWorldRuntime
{
public:
    using ChestItemState = GameplayChestItemState;
    using ChestViewState = GameplayChestViewState;
    using CorpseViewState = GameplayCorpseViewState;

    struct AtmosphereState
    {
        std::string sourceSkyTextureName;
        std::string skyTextureName;
        int32_t weatherFlags = 0;
        int32_t fogWeakDistance = 0;
        int32_t fogStrongDistance = 0;
        bool redFog = false;
        bool hasFogTint = false;
        uint8_t fogTintRed = 255;
        uint8_t fogTintGreen = 255;
        uint8_t fogTintBlue = 255;
        bool isNight = false;
        float fogDensity = 0.0f;
        float rainIntensity = 0.0f;
        float ambientBrightness = 0.69f;
        float visibilityDistance = 200000.0f;
        float darknessOverlayAlpha = 0.0f;
        uint32_t darknessOverlayColorAbgr = 0x00000000u;
        float gameplayOverlayAlpha = 0.0f;
        uint32_t gameplayOverlayColorAbgr = 0x00000000u;
        float sunDirectionX = 0.0f;
        float sunDirectionY = 0.0f;
        float sunDirectionZ = 1.0f;
        uint32_t clearColorAbgr = 0x000000ffu;
    };

    enum class ActorAiState
    {
        Standing,
        Wandering,
        Pursuing,
        Fleeing,
        Stunned,
        Attacking,
        Dying,
        Dead,
    };

    enum class ActorAnimation
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

    using MonsterAttackAbility = GameplayProjectileService::MonsterAttackAbility;

    enum class DebugTargetKind
    {
        None,
        Party,
        Actor,
    };

    enum class ProjectileCollisionKind
    {
        None,
        Party,
        Actor,
        BModel,
        Terrain,
    };

    enum class ActorControlMode : uint8_t
    {
        None = 0,
        Charm,
        Berserk,
        Enslaved,
        ControlUndead,
        Reanimated,
    };

    enum class RainIntensityPreset : uint8_t
    {
        Off = 0,
        Light = 1,
        Medium = 2,
        Heavy = 3,
        VeryHeavy = 4,
    };

    struct SpellCastRequest;
    struct PartyProjectileRequest;

    struct MapActorState
    {
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        std::string displayName;
        uint32_t uniqueNameId = 0;
        bool spawnedAtRuntime = false;
        bool fromSpawnPoint = false;
        size_t spawnPointIndex = static_cast<size_t>(-1);
        uint32_t group = 0;
        uint32_t ally = 0;
        uint8_t hostilityType = 0;
        uint32_t specialItemId = 0;
        int currentHp = 0;
        int maxHp = 0;
        int x = 0;
        int y = 0;
        int z = 0;
        float preciseX = 0.0f;
        float preciseY = 0.0f;
        float preciseZ = 0.0f;
        int homeX = 0;
        int homeY = 0;
        int homeZ = 0;
        float homePreciseX = 0.0f;
        float homePreciseY = 0.0f;
        float homePreciseZ = 0.0f;
        uint16_t radius = 0;
        uint16_t height = 0;
        uint16_t moveSpeed = 0;
        uint16_t spriteFrameIndex = 0;
        std::array<uint16_t, 8> actionSpriteFrameIndices = {};
        bool useStaticSpriteFrame = false;
        bool hostileToParty = false;
        bool isDead = false;
        bool isInvisible = false;
        bool bloodSplatSpawned = false;
        bool hasDetectedParty = false;
        ActorAiState aiState = ActorAiState::Standing;
        ActorAnimation animation = ActorAnimation::Standing;
        float animationTimeTicks = 0.0f;
        float recoverySeconds = 0.0f;
        float attackAnimationSeconds = 0.3f;
        float attackCooldownSeconds = 0.0f;
        float idleDecisionSeconds = 0.0f;
        float actionSeconds = 0.0f;
        float moveDirectionX = 0.0f;
        float moveDirectionY = 0.0f;
        float velocityX = 0.0f;
        float velocityY = 0.0f;
        float velocityZ = 0.0f;
        float yawRadians = 0.0f;
        float slowRemainingSeconds = 0.0f;
        float slowMoveMultiplier = 1.0f;
        float slowRecoveryMultiplier = 1.0f;
        float stunRemainingSeconds = 0.0f;
        float paralyzeRemainingSeconds = 0.0f;
        float fearRemainingSeconds = 0.0f;
        float blindRemainingSeconds = 0.0f;
        float controlRemainingSeconds = 0.0f;
        ActorControlMode controlMode = ActorControlMode::None;
        float shrinkRemainingSeconds = 0.0f;
        float shrinkDamageMultiplier = 1.0f;
        float shrinkArmorClassMultiplier = 1.0f;
        float darkGraspRemainingSeconds = 0.0f;
        uint32_t idleDecisionCount = 0;
        uint32_t pursueDecisionCount = 0;
        uint32_t attackDecisionCount = 0;
        bool attackImpactTriggered = false;
        MonsterAttackAbility queuedAttackAbility = MonsterAttackAbility::Attack1;
        OutdoorMoveState movementState = {};
        bool movementStateInitialized = false;
        float crowdSideLockRemainingSeconds = 0.0f;
        float crowdNoProgressSeconds = 0.0f;
        float crowdLastEdgeDistance = 0.0f;
        float crowdRetreatRemainingSeconds = 0.0f;
        float crowdStandRemainingSeconds = 0.0f;
        float crowdProbeX = 0.0f;
        float crowdProbeY = 0.0f;
        float crowdProbeEdgeDistance = 0.0f;
        float crowdProbeElapsedSeconds = 0.0f;
        uint8_t crowdEscapeAttempts = 0;
        int8_t crowdSideSign = 0;
    };

    using CombatEvent = GameplayCombatController::CombatEvent;

    struct ActorDecisionDebugInfo
    {
        size_t actorIndex = static_cast<size_t>(-1);
        int16_t monsterId = 0;
        uint8_t hostilityType = 0;
        bool hostileToParty = false;
        bool hasDetectedParty = false;
        ActorAiState aiState = ActorAiState::Standing;
        ActorAnimation animation = ActorAnimation::Standing;
        float idleDecisionSeconds = 0.0f;
        float actionSeconds = 0.0f;
        float attackCooldownSeconds = 0.0f;
        uint32_t idleDecisionCount = 0;
        uint32_t pursueDecisionCount = 0;
        uint32_t attackDecisionCount = 0;
        int monsterAiType = 0;
        bool movementAllowed = false;
        float partySenseRange = 0.0f;
        float distanceToParty = 0.0f;
        bool canSenseParty = false;
        DebugTargetKind targetKind = DebugTargetKind::None;
        size_t targetActorIndex = static_cast<size_t>(-1);
        int16_t targetMonsterId = 0;
        int relationToTarget = 0;
        float targetDistance = 0.0f;
        float targetEdgeDistance = 0.0f;
        bool targetCanSense = false;
        bool shouldPromoteHostility = false;
        float promotionRange = 0.0f;
        bool shouldEngageTarget = false;
        bool shouldFlee = false;
        bool inMeleeRange = false;
        bool attackJustCompleted = false;
        bool attackInProgress = false;
        bool friendlyNearParty = false;
    };

    using ProjectileState = GameplayProjectileService::ProjectileState;
    using ProjectileImpactState = GameplayProjectileService::ProjectileImpactState;

    struct ProjectileCollisionFacts
    {
        bool hit = false;
        float factor = 2.0f;
        bx::Vec3 point = {0.0f, 0.0f, 0.0f};
        ProjectileCollisionKind kind = ProjectileCollisionKind::None;
        std::string colliderName;
        size_t actorIndex = static_cast<size_t>(-1);
        size_t faceIndex = static_cast<size_t>(-1);
        bool waterTerrainImpact = false;
    };

    struct ProjectileFrameWorldFacts
    {
        GameplayProjectileService::ProjectileFrameFacts frame;
        ProjectileCollisionFacts collision;
    };

    struct FireSpikeTrapState
    {
        uint32_t trapId = 0;
        ProjectileState::SourceKind sourceKind = ProjectileState::SourceKind::Party;
        uint32_t sourceId = 0;
        uint32_t sourcePartyMemberIndex = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Attack1;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t impactObjectDescriptionId = 0;
        uint16_t objectFlags = 0;
        uint16_t radius = 0;
        uint16_t height = 0;
        int spellId = 0;
        int effectSoundId = 0;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        std::string objectName;
        std::string objectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint32_t timeSinceCreatedTicks = 0;
        bool isExpired = false;
    };

    struct WorldItemState
    {
        uint32_t worldItemId = 0;
        InventoryItem item = {};
        uint32_t goldAmount = 0;
        bool isGold = false;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t objectFlags = 0;
        uint16_t radius = 0;
        uint16_t height = 0;
        uint16_t soundId = 0;
        uint16_t attributes = 0;
        int16_t sectorId = 0;
        std::string objectName;
        std::string objectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float velocityX = 0.0f;
        float velocityY = 0.0f;
        float velocityZ = 0.0f;
        float initialX = 0.0f;
        float initialY = 0.0f;
        float initialZ = 0.0f;
        uint32_t timeSinceCreatedTicks = 0;
        uint32_t lifetimeTicks = 0;
        bool spawnedByPlayer = false;
        bool isExpired = false;
    };

    struct SpawnPointState
    {
        int x = 0;
        int y = 0;
        int z = 0;
        uint16_t radius = 0;
        uint16_t typeId = 0;
        uint16_t index = 0;
        uint16_t attributes = 0;
        uint32_t group = 0;
        int encounterSlot = 0;
        bool isFixedTier = false;
        char fixedTier = '\0';
        int minCount = 0;
        int maxCount = 0;
        int16_t representativeMonsterId = 0;
        uint8_t hostilityType = 0;
        bool hostileToParty = false;
        std::string monsterFamilyName;
        std::string representativePictureName;
    };

    struct TimerState
    {
        uint16_t eventId = 0;
        bool repeating = false;
        float intervalGameMinutes = 0.0f;
        float remainingGameMinutes = 0.0f;
        std::optional<int> targetHour;
        bool hasFired = false;
    };

    struct AudioEvent
    {
        uint32_t soundId = 0;
        uint32_t sourceId = 0;
        std::string reason;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        bool positional = true;
    };

    struct ArmageddonState
    {
        float remainingSeconds = 0.0f;
        uint32_t skillLevel = 0;
        SkillMastery skillMastery = SkillMastery::None;
        uint32_t casterMemberIndex = 0;
        uint32_t shakeStepsRemaining = 0;
        uint32_t shakeSequence = 0;
        float cameraShakeYawRadians = 0.0f;
        float cameraShakePitchRadians = 0.0f;

        bool active() const
        {
            return remainingSeconds > 0.0f;
        }
    };

    struct Snapshot
    {
        float gameMinutes = 0.0f;
        AtmosphereState atmosphere = {};
        std::vector<TimerState> timers;
        std::vector<MapActorState> mapActors;
        std::vector<MapDeltaChest> chests;
        std::vector<uint8_t> openedChestFlags;
        std::vector<std::optional<ChestViewState>> materializedChestViews;
        std::optional<ChestViewState> activeChestView;
        std::optional<EventRuntimeState> eventRuntimeState;
        float actorUpdateAccumulatorSeconds = 0.0f;
        uint32_t sessionChestSeed = 0;
        uint32_t nextActorId = 0;
        std::vector<std::optional<CorpseViewState>> mapActorCorpseViews;
        std::optional<CorpseViewState> activeCorpseView;
        std::vector<WorldItemState> worldItems;
        uint32_t nextWorldItemId = 1;
        uint32_t nextProjectileId = 1;
        uint32_t nextProjectileImpactId = 1;
        uint32_t nextFireSpikeTrapId = 1;
        float gameplayOverlayRemainingSeconds = 0.0f;
        float gameplayOverlayDurationSeconds = 0.0f;
        float gameplayOverlayPeakAlpha = 0.0f;
        uint32_t gameplayOverlayColorAbgr = 0x00000000u;
        std::vector<ProjectileState> projectiles;
        std::vector<ProjectileImpactState> projectileImpacts;
        std::vector<FireSpikeTrapState> fireSpikeTraps;
        ArmageddonState armageddon = {};
        bool hasRainIntensityOverride = false;
        RainIntensityPreset rainIntensityPreset = RainIntensityPreset::Off;
    };

    void initialize(
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const MonsterProjectileTable &monsterProjectileTable,
        const ObjectTable &objectTable,
        const SpellTable &spellTable,
        const ItemTable &itemTable,
        Party *pParty,
        OutdoorPartyRuntime *pPartyRuntime,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const ChestTable *pChestTable,
        const std::optional<OutdoorMapData> &outdoorMapData,
        const std::optional<MapDeltaData> &outdoorMapDeltaData,
        const std::optional<OutdoorWeatherProfile> &outdoorWeatherProfile,
        const std::optional<EventRuntimeState> &eventRuntimeState,
        const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet = std::nullopt,
        const std::optional<std::vector<uint8_t>> &outdoorLandMask = std::nullopt,
        const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet = std::nullopt,
        const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet = std::nullopt,
        const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet = std::nullopt,
        const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet = std::nullopt,
        GameplayActorService *pGameplayActorService = nullptr,
        GameplayProjectileService *pGameplayProjectileService = nullptr,
        GameplayCombatController *pGameplayCombatController = nullptr,
        GameplayFxService *pGameplayFxService = nullptr
    );

    bool isInitialized() const;
    void bindInteractionView(OutdoorGameView *pView);
    int mapId() const;
    const std::string &mapName() const override;
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    float currentGameMinutes() const override;
    float gameMinutes() const override;
    int currentHour() const override;
    int currentLocationReputation() const override;
    void setCurrentLocationReputation(int reputation) override;
    const OutdoorMapData *mapData() const;
    const AtmosphereState &atmosphereState() const;
    RainIntensityPreset cycleRainIntensityPreset();
    RainIntensityPreset rainIntensityPreset() const;
    const char *rainIntensityPresetName() const;
    void advanceGameMinutes(float minutes) override;
    void updateMapActors(float deltaSeconds, float partyX, float partyY, float partyZ);
    void queueActorAiUpdate(float deltaSeconds, float partyX, float partyY, float partyZ);

    void applyEventRuntimeState();
    bool updateTimers(
        float deltaSeconds,
        const EventRuntime &eventRuntime,
        const std::optional<ScriptedEventProgram> &localEventProgram,
        const std::optional<ScriptedEventProgram> &globalEventProgram
    );
    bool isChestOpened(uint32_t chestId) const;
    size_t mapActorCount() const override;
    bool actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const override;
    bool actorInspectState(
        size_t actorIndex,
        uint32_t animationTicks,
        GameplayActorInspectState &state) const override;
    std::optional<GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const override;
    const MapActorState *mapActorState(size_t actorIndex) const;
    std::optional<GameplayWorldPoint> partyAttackFallbackProjectionPoint(size_t actorIndex) const;
    std::optional<GameplayPartyAttackActorFacts> partyAttackActorFacts(
        size_t actorIndex,
        bool visibleForFallback) const override;
    std::vector<GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const GameplayPartyAttackFallbackQuery &query) const override;
    std::optional<ActorDecisionDebugInfo> debugActorDecisionInfo(
        size_t actorIndex,
        float partyX,
        float partyY,
        float partyZ
    ) const;
    bool debugSpawnMapActorProjectile(
        size_t actorIndex,
        MonsterAttackAbility ability,
        float targetX,
        float targetY,
        float targetZ);
    bool debugSpawnEncounterFromSpawnPoint(size_t spawnIndex, uint32_t countOverride = 0);
    bool setMapActorDead(size_t actorIndex, bool isDead, bool emitAudio = true);
    bool applyPartyAttackToMapActor(size_t actorIndex, int damage, float partyX, float partyY, float partyZ);
    bool applyPartyAttackMeleeDamage(
        size_t actorIndex,
        int damage,
        const GameplayWorldPoint &source) override;
    bool spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request) override;
    bool castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request) override;
    void recordPartyAttackWorldResult(
        std::optional<size_t> actorIndex,
        bool attacked,
        bool actionPerformed) override;
    bool worldInteractionReady() const override;
    bool worldInspectModeActive() const override;
    GameplayWorldPickRequest buildWorldPickRequest(const GameplayWorldPickRequestInput &input) const override;
    std::optional<GameplayHeldItemDropRequest> buildHeldItemDropRequest() const override;
    GameplayPartyAttackFrameInput buildPartyAttackFrameInput(
        const GameplayWorldPickRequest &pickRequest) const override;
    std::optional<size_t> spellActionHoveredActorIndex() const override;
    std::optional<size_t> spellActionClosestVisibleHostileActorIndex() const override;
    std::optional<bx::Vec3> spellActionActorTargetPoint(size_t actorIndex) const override;
    std::optional<bx::Vec3> spellActionGroundTargetPoint(float screenX, float screenY) const override;
    bool applyPartySpellToActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex = 0) override;
    bool applyPartySpellToMapActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex = 0);
    bool applyDirectSpellImpactToMapActor(
        size_t actorIndex,
        uint32_t spellId,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex,
        const GameplayActorService::DirectSpellImpactResult &impact);
    bool healMapActor(size_t actorIndex, int amount);
    bool resurrectMapActor(size_t actorIndex, int health, bool friendlyToParty);
    bool clearMapActorSpellEffects(size_t actorIndex);
    int effectiveMapActorArmorClass(size_t actorIndex) const;
    std::vector<size_t> collectMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        bool requireLineOfSight,
        float sourceX,
        float sourceY,
        float sourceZ) const override;
    bool notifyPartyContactWithMapActor(size_t actorIndex, float partyX, float partyY, float partyZ);
    float sampleSupportFloorHeight(float x, float y, float z, float maxRise, float xySlack) const;
    size_t spawnPointCount() const;
    const SpawnPointState *spawnPointState(size_t spawnIndex) const;
    size_t chestCount() const;
    size_t openedChestCount() const;
    ChestViewState *activeChestView() override;
    const ChestViewState *activeChestView() const override;
    void commitActiveChestView() override;
    bool takeActiveChestItem(size_t itemIndex, ChestItemState &item) override;
    bool takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, ChestItemState &item) override;
    bool tryPlaceActiveChestItemAt(const ChestItemState &item, uint8_t gridX, uint8_t gridY) override;
    void closeActiveChestView() override;
    CorpseViewState *activeCorpseView() override;
    const CorpseViewState *activeCorpseView() const override;
    void commitActiveCorpseView() override;
    bool openMapActorCorpseView(size_t actorIndex);
    bool takeActiveCorpseItem(size_t itemIndex, ChestItemState &item) override;
    void closeActiveCorpseView() override;
    const std::vector<AudioEvent> &pendingAudioEvents() const;
    void clearPendingAudioEvents();
    const std::vector<CombatEvent> &pendingCombatEvents() const;
    void clearPendingCombatEvents();
    size_t worldItemCount() const;
    const WorldItemState *worldItemState(size_t worldItemIndex) const;
    WorldItemState *worldItemStateMutable(size_t worldItemIndex);
    bool takeWorldItem(size_t worldItemIndex, WorldItemState &item);
    bool identifyWorldItem(size_t worldItemIndex, std::string &statusText);
    bool tryIdentifyWorldItem(size_t worldItemIndex, const Character &inspector, std::string &statusText);
    bool tryRepairWorldItem(size_t worldItemIndex, const Character &inspector, std::string &statusText);
    bool spawnWorldItem(
        const InventoryItem &item,
        float sourceX,
        float sourceY,
        float sourceZ,
        float yawRadians
    );
    bool spawnPartyFireSpikeTrap(
        uint32_t casterMemberIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        float x,
        float y,
        float z) override;
    size_t projectileCount() const;
    const ProjectileState *projectileState(size_t projectileIndex) const;
    size_t projectileImpactCount() const;
    const ProjectileImpactState *projectileImpactState(size_t effectIndex) const;
    size_t fireSpikeTrapCount() const;
    const FireSpikeTrapState *fireSpikeTrapState(size_t trapIndex) const;
    void startGameplayScreenOverlay(uint32_t colorAbgr, float durationSeconds, float peakAlpha);
    bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        std::string &failureText) override;
    bool canActivateWorldHit(
        const GameplayWorldHit &hit,
        GameplayInteractionMethod interactionMethod) const override;
    bool activateWorldHit(const GameplayWorldHit &hit) override;
    GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickHeldItemWorldTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickCurrentInteractionTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHoverCacheState worldHoverCacheState() const override;
    GameplayHoverStatusPayload refreshWorldHover(const GameplayWorldHoverRequest &request) override;
    GameplayHoverStatusPayload readCachedWorldHover() override;
    void clearWorldHover() override;
    bool canUseHeldItemOnWorld(const GameplayWorldHit &hit) const override;
    bool useHeldItemOnWorld(const GameplayWorldHit &hit) override;
    void applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult) override;
    bool dropHeldItemToWorld(const GameplayHeldItemDropRequest &request) override;
    bool tryGetGameplayMinimapState(GameplayMinimapState &state) const override;
    void collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const override;
    bool isArmageddonActive() const;
    float armageddonCameraShakeYawRadians() const;
    float armageddonCameraShakePitchRadians() const;

    const EventRuntimeState::PendingMapMove *pendingMapMove() const;
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove();

    Party *party() override;
    const Party *party() const override;
    const std::vector<uint8_t> *journalMapFullyRevealedCells() const override;
    const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const override;
    int restFoodRequired() const override;
    float partyX() const override;
    float partyY() const override;
    float partyFootZ() const override;
    void syncSpellMovementStatesFromPartyBuffs() override;
    void requestPartyJump() override;
    void setAlwaysRunEnabled(bool enabled) override;
    void updateWorldMovement(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput) override;
    void updateActorAi(float deltaSeconds) override;
    void updateWorld(float deltaSeconds) override;
    void renderWorld(
        int width,
        int height,
        const GameplayInputFrame &input,
        float deltaSeconds) override;
    GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const override;
    bool requestTravelAutosave() override;
    void presentPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent);
    void handleDialogueCloseRequest();
    void executeActiveDialogAction();
    void openDebugNpcDialogue(uint32_t npcId);
    void applyGrantedEventItemsToHeldInventory();
    bool tryTriggerLocalEventById(uint16_t eventId);
    void cancelPendingMapTransition() override;
    bool executeNpcTopicEvent(uint16_t eventId, size_t &previousMessageCount) override;
    const MapDeltaData *mapDeltaData() const override;
    EventRuntimeState *eventRuntimeState() override;
    const EventRuntimeState *eventRuntimeState() const override;
    bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ
    ) override;
    bool castPartySpell(const SpellCastRequest &request);
    bool castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request) override;
    bool spawnPartyProjectile(const PartyProjectileRequest &request);
    bool summonMonsters(
        uint32_t typeIndexInMapStats,
        uint32_t level,
        uint32_t count,
        int32_t x,
        int32_t y,
        int32_t z,
        uint32_t group,
        uint32_t uniqueNameId
    ) override;
    bool summonEventItem(
        uint32_t itemId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    ) override;
    bool summonFriendlyMonsterById(
        int16_t monsterId,
        uint32_t count,
        float durationSeconds,
        float x,
        float y,
        float z
    ) override;
    void setParticleSystem(ParticleSystem *pParticleSystem);
    bool checkMonstersKilled(uint32_t checkType, uint32_t id, uint32_t count, bool invisibleAsDead) const override;

public:
    struct ResolvedProjectileDefinition
    {
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t impactObjectDescriptionId = 0;
        uint16_t impactObjectSpriteId = 0;
        uint16_t objectFlags = 0;
        uint16_t radius = 0;
        uint16_t height = 0;
        uint32_t lifetimeTicks = 0;
        float speed = 0.0f;
        int spellId = 0;
        int effectSoundId = 0;
        std::string objectName;
        std::string objectSpriteName;
        std::string impactObjectName;
        std::string impactObjectSpriteName;
    };

    enum class RuntimeSpellSourceKind
    {
        Actor,
        Event,
        Party,
    };

    struct SpellCastRequest
    {
        RuntimeSpellSourceKind sourceKind = RuntimeSpellSourceKind::Event;
        uint32_t sourceId = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Spell1;
        uint32_t spellId = 0;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        uint32_t sourcePartyMemberIndex = 0;
        int damage = 0;
        int attackBonus = 0;
        bool useActorHitChance = false;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceZ = 0.0f;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
    };

    struct PartyProjectileRequest
    {
        uint32_t sourcePartyMemberIndex = 0;
        uint32_t objectId = 0;
        uint32_t impactObjectId = 0;
        int damage = 0;
        int attackBonus = 0;
        bool useActorHitChance = false;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceZ = 0.0f;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
    };

    struct MonsterVisualState
    {
        uint16_t spriteFrameIndex = 0;
        std::array<uint16_t, 8> actionSpriteFrameIndices = {};
        bool useStaticFrame = false;
    };

    struct BloodSplatState
    {
        struct Vertex
        {
            float x = 0.0f;
            float y = 0.0f;
            float z = 0.0f;
            float u = 0.0f;
            float v = 0.0f;
        };

        uint32_t sourceActorId = 0;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float radius = 0.0f;
        std::vector<Vertex> vertices;
    };

    void collectOutdoorFaceCandidates(float minX, float minY, float maxX, float maxY, std::vector<size_t> &indices) const;
    const OutdoorFaceGeometryData *outdoorFace(size_t faceIndex) const;
    size_t bloodSplatCount() const;
    const BloodSplatState *bloodSplatState(size_t splatIndex) const;
    uint64_t bloodSplatRevision() const;

private:
    static uint32_t makeChestSeed(uint32_t sessionSeed, int mapId, uint32_t chestId, uint32_t salt);
    static int generateGoldAmount(int treasureLevel, std::mt19937 &rng);
    static std::pair<int, int> remapTreasureLevelRange(int itemTreasureLevel, int mapTreasureLevel);
    static int sampleRemappedTreasureLevel(int itemTreasureLevel, int mapTreasureLevel, std::mt19937 &rng);

    bool applyMonsterAttackToMapActor(size_t actorIndex, int damage, uint32_t sourceActorId, bool emitAudio = true);
    bool spawnEncounterFromResolvedData(
        int encounterSlot,
        char fixedTier,
        uint32_t count,
        float x,
        float y,
        float z,
        uint16_t radius,
        uint16_t attributes,
        uint32_t group,
        uint32_t uniqueNameId,
        bool fromSpawnPoint,
        size_t spawnPointIndex,
        bool aggro);
    bool setMapActorHostileToParty(size_t actorIndex, float partyX, float partyY, float partyZ, bool resetActionState);
    void aggroNearbyMapActorFaction(size_t actorIndex, float partyX, float partyY, float partyZ);
    ChestViewState buildChestView(uint32_t chestId) const;
    void activateChestView(uint32_t chestId);
    int normalizedMapTreasureLevel() const;
    void pushAudioEvent(
        uint32_t soundId,
        uint32_t sourceId,
        const std::string &reason,
        float x,
        float y,
        float z,
        bool positional = true);
    void pushProjectileAudioEvent(const GameplayProjectileService::ProjectileAudioRequest &request);
    bool spawnProjectileFromMapActor(
        const MapActorState &actor,
        const MonsterTable::MonsterStatsEntry &stats,
        MonsterAttackAbility ability,
        float targetX,
        float targetY,
        float targetZ
    );
    bool castSpellFromMapActor(
        const MapActorState &actor,
        const MonsterTable::MonsterStatsEntry &stats,
        MonsterAttackAbility ability,
        float targetX,
        float targetY,
        float targetZ
    );
    bool castSpell(const SpellCastRequest &request);
    bool resolveObjectProjectileDefinition(
        int objectId,
        int impactObjectId,
        ResolvedProjectileDefinition &definition) const;
    bool castDirectSpellProjectile(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition
    );
    bool spawnDeathBlossomFalloutProjectiles(
        const ProjectileState &projectile,
        float x,
        float y,
        float z);
    bool castMeteorShower(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition
    );
    bool castStarburst(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition
    );
    bool projectileSourceIsFriendlyToActor(const ProjectileState &projectile, const MapActorState &actor) const;
    bool spawnSpellProjectile(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition,
        float sourceX,
        float sourceY,
        float sourceZ,
        float targetX,
        float targetY,
        float targetZ,
        float spawnForwardOffset
    );
    bool hasClearOutdoorLineOfSight(const bx::Vec3 &start, const bx::Vec3 &end) const;
    void buildOutdoorFaceSpatialIndex();
    bool materializeTreasureSpawnFromSpawnPoint(size_t spawnPointIndex);
    bool resolveWorldItemVisual(
        uint32_t itemId,
        uint16_t &objectDescriptionId,
        uint16_t &objectSpriteId,
        uint16_t &objectSpriteFrameIndex,
        uint16_t &objectFlags,
        uint16_t &radius,
        uint16_t &height,
        std::string &objectName,
        std::string &objectSpriteName) const;
    void materializeMapDeltaWorldItems();
    void updateWorldItems(float deltaSeconds);
    void updateFireSpikeTraps(float deltaSeconds, float partyX, float partyY, float partyZ);
    void applyFireSpikeTrapTriggerDecision(
        FireSpikeTrapState &trap,
        const GameplayProjectileService::FireSpikeTrapTriggerDecision &decision);
    int resolveProjectilePartyImpactDamage(const ProjectileState &projectile) const;
    GameplayProjectileService::ProjectileAreaImpactInput buildProjectileAreaImpactInput(
        const ProjectileState &projectile,
        const bx::Vec3 &impactPoint,
        float impactRadius,
        float partyX,
        float partyY,
        float partyZ,
        bool canHitParty,
        size_t directActorIndex) const;
    void applyProjectileAreaImpact(
        const ProjectileState &projectile,
        const bx::Vec3 &impactPoint,
        float impactRadius,
        float partyX,
        float partyY,
        float partyZ,
        bool canHitParty,
        size_t directActorIndex,
        bool logAoeHits);
    int resolvePartyProjectileDamageMultiplier(
        const ProjectileState &projectile,
        size_t actorIndex) const;
    GameplayProjectileService::ProjectileDirectActorImpactInput buildProjectileDirectActorImpactInput(
        const ProjectileState &projectile,
        size_t actorIndex) const;
    void applyProjectileDirectPartyImpact(const ProjectileState &projectile);
    void applyProjectileDirectActorImpact(const ProjectileState &projectile, size_t actorIndex);
    ProjectileCollisionFacts buildProjectileCollisionFacts(
        const ProjectileState &projectile,
        const bx::Vec3 &segmentStart,
        const bx::Vec3 &segmentEnd,
        float partyX,
        float partyY,
        float partyZ) const;
    ProjectileFrameWorldFacts collectProjectileFrameFacts(
        const ProjectileState &projectile,
        float deltaSeconds,
        float partyX,
        float partyY,
        float partyZ) const;
    GameplayProjectileService::ProjectileBounceSurfaceFacts buildProjectileBounceSurfaceFacts(
        const ProjectileCollisionFacts &collision) const;
    void applyProjectileFrameResult(
        ProjectileState &projectile,
        const ProjectileCollisionFacts &collision,
        const GameplayProjectileService::ProjectileFrameResult &frameResult);
    bool applyProjectileSpawnEffects(
        const GameplayProjectileService::ProjectileSpawnResult &spawnResult,
        const GameplayProjectileService::ProjectileSpawnEffects &decision,
        const std::string &spawnKindName,
        const std::string &instantColliderName);
    static const char *projectileCollisionKindName(ProjectileCollisionKind kind);
    void updateProjectiles(float deltaSeconds, float partyX, float partyY, float partyZ);
    void spawnProjectileImpact(
        const ProjectileState &projectile,
        float x,
        float y,
        float z,
        bool centerVertically = false);
    bool spawnImmediateSpellVisual(
        uint32_t spellId,
        float x,
        float y,
        float z,
        bool centerVertically = false,
        bool preferImpactObject = true);
    bool spawnWaterSplashImpact(float x, float y, float z);
    void addBloodSplat(uint32_t sourceActorId, float x, float y, float z, float radius);
    void bakeBloodSplatGeometry(BloodSplatState &splat) const;
    void spawnBloodSplatForActorIfNeeded(size_t actorIndex);
    void removeBloodSplat(uint32_t sourceActorId);
    GameplayProjectileService &projectileService();
    const GameplayProjectileService &projectileService() const;
    GameplayProjectileService::ProjectileImpactSpawnResult spawnProjectileImpactVisual(
        const ProjectileState &projectile,
        const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z,
        bool centerVertically);
    GameplayProjectileService::ProjectileImpactSpawnResult spawnWaterSplashImpactVisual(
        const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z);
    GameplayProjectileService::ProjectileImpactSpawnResult spawnImmediateSpellImpactVisual(
        const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
        int sourceSpellId,
        const std::string &sourceObjectName,
        const std::string &sourceObjectSpriteName,
        float x,
        float y,
        float z,
        bool centerVertically,
        bool freezeAnimation);

    int m_mapId = 0;
    int m_mapTreasureLevel = 0;
    MapStatsEntry m_map = {};
    std::string m_mapName;
    float m_gameMinutes = 9.0f * 60.0f;
    AtmosphereState m_atmosphereState = {};
    std::optional<OutdoorWeatherProfile> m_outdoorWeatherProfile;
    std::vector<TimerState> m_timers;
    std::vector<MapActorState> m_mapActors;
    std::vector<SpawnPointState> m_spawnPoints;
    std::vector<MapDeltaChest> m_chests;
    std::vector<bool> m_openedChests;
    std::vector<std::optional<ChestViewState>> m_materializedChestViews;
    std::optional<ChestViewState> m_activeChestView;
    std::optional<EventRuntimeState> m_eventRuntimeState;
    const ItemTable *m_pItemTable = nullptr;
    Party *m_pParty = nullptr;
    OutdoorPartyRuntime *m_pPartyRuntime = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    const ChestTable *m_pChestTable = nullptr;
    const MonsterTable *m_pMonsterTable = nullptr;
    const MonsterProjectileTable *m_pMonsterProjectileTable = nullptr;
    const ObjectTable *m_pObjectTable = nullptr;
    const OutdoorMapData *m_pOutdoorMapData = nullptr;
    const MapDeltaData *m_pOutdoorMapDeltaData = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    GameplayActorService *m_pGameplayActorService = nullptr;
    GameplayProjectileService *m_pGameplayProjectileService = nullptr;
    GameplayProjectileService m_fallbackGameplayProjectileService;
    GameplayCombatController *m_pGameplayCombatController = nullptr;
    GameplayFxService *m_pGameplayFxService = nullptr;
    const SpriteFrameTable *m_pActorSpriteFrameTable = nullptr;
    const SpriteFrameTable *m_pProjectileSpriteFrameTable = nullptr;
    ParticleSystem *m_pParticleSystem = nullptr;
    OutdoorGameView *m_pInteractionView = nullptr;
    std::optional<std::vector<uint8_t>> m_outdoorLandMask;
    std::vector<OutdoorFaceGeometryData> m_outdoorFaces;
    std::vector<std::vector<size_t>> m_outdoorFaceGridCells;
    mutable std::vector<uint32_t> m_outdoorFaceVisitGenerations;
    mutable uint32_t m_outdoorFaceVisitGenerationCounter = 1;
    float m_outdoorFaceGridMinX = 0.0f;
    float m_outdoorFaceGridMinY = 0.0f;
    size_t m_outdoorFaceGridWidth = 0;
    size_t m_outdoorFaceGridHeight = 0;
    std::optional<OutdoorMovementController> m_outdoorMovementController;
    std::unordered_map<int16_t, MonsterVisualState> m_monsterVisualsById;
    float m_actorUpdateAccumulatorSeconds = 0.0f;
    bool m_actorAiUpdateQueued = false;
    float m_queuedActorAiDeltaSeconds = 0.0f;
    float m_queuedActorAiPartyX = 0.0f;
    float m_queuedActorAiPartyY = 0.0f;
    float m_queuedActorAiPartyZ = 0.0f;
    uint32_t m_sessionChestSeed = 0;
    uint32_t m_nextActorId = 0;
    std::vector<std::optional<CorpseViewState>> m_mapActorCorpseViews;
    std::optional<CorpseViewState> m_activeCorpseView;
    std::vector<AudioEvent> m_pendingAudioEvents;
    std::vector<WorldItemState> m_worldItems;
    uint32_t m_nextWorldItemId = 1;
    float m_gameplayOverlayRemainingSeconds = 0.0f;
    float m_gameplayOverlayDurationSeconds = 0.0f;
    float m_gameplayOverlayPeakAlpha = 0.0f;
    uint32_t m_gameplayOverlayColorAbgr = 0x00000000u;
    bool m_hasRainIntensityOverride = false;
    RainIntensityPreset m_rainIntensityPreset = RainIntensityPreset::Off;
    std::vector<FireSpikeTrapState> m_fireSpikeTraps;
    std::vector<BloodSplatState> m_bloodSplats;
    uint64_t m_bloodSplatRevision = 0;
    ArmageddonState m_armageddonState = {};

    void updateGameplayScreenOverlay(float deltaSeconds);
    void updateActorFrameGlobalEffects(float deltaSeconds, float partyX, float partyY, float partyZ);
    std::vector<bool> selectOutdoorActiveActors(float partyX, float partyY, float partyZ) const;
    struct OutdoorActorAiFrameApplication
    {
        std::vector<bool> handledActorMask;
        std::vector<bool> activeUpdatesAppliedActorMask;
        std::vector<bool> behaviorAppliedActorMask;
        std::vector<bool> keepCurrentAnimationMask;
        std::vector<bool> resetAnimationTimeMask;
        std::vector<bool> resetCrowdSteeringMask;
        std::vector<bool> clearVelocityMask;
        std::vector<bool> applyMovementMask;
        std::vector<float> desiredMoveX;
        std::vector<float> desiredMoveY;
        std::vector<bool> meleePursuitActiveMask;
        std::vector<float> movementEffectiveMoveSpeed;
        std::vector<GameplayWorldPoint> movementTargetPosition;
        std::vector<float> movementTargetEdgeDistance;
        std::vector<bool> movementInMeleeRangeMask;
    };
    ActorAiFrameFacts collectOutdoorActorAiFrameFacts(
        float deltaSeconds,
        float partyX,
        float partyY,
        float partyZ,
        const std::vector<bool> &activeActorMask) const;
    std::optional<ActorAiFacts> collectOutdoorActorAiFacts(
        size_t actorIndex,
        bool active,
        float partyX,
        float partyY,
        float partyZ,
        std::vector<int8_t> &actorLineOfSightCache) const;
    OutdoorActorAiFrameApplication applyOutdoorActorAiFrameResult(
        const ActorAiFrameResult &result,
        const std::vector<bool> &activeActorMask,
        const ActorAiFrameFacts &facts);
    void applyOutdoorActorPostMovementAiUpdate(
        MapActorState &actor,
        const ActorAiUpdate &movementUpdate,
        float &desiredMoveX,
        float &desiredMoveY);
    void applyOutdoorActorMovementIntegration(
        size_t actorIndex,
        const MonsterTable::MonsterStatsEntry *pStats,
        const std::vector<bool> &activeActorMask,
        float moveSpeed,
        bool meleePursuitActive,
        bool inMeleeRange,
        const GameplayWorldPoint &targetPosition,
        float targetEdgeDistance,
        const GameplayActorAiSystem &actorAiSystem,
        ActorAiState &nextAiState,
        ActorAnimation &nextAnimation,
        float &desiredMoveX,
        float &desiredMoveY);
    void updateOutdoorActorsForStep(
        float partyX,
        float partyY,
        float partyZ,
        const std::vector<bool> &activeActorMask,
        const OutdoorActorAiFrameApplication &sharedActorApplication,
        const GameplayActorAiSystem &actorAiSystem);
    void applyActorFrameSideEffects(float deltaSeconds, float partyX, float partyY, float partyZ);
    void advanceGameMinutesInternal(float minutes);
    void applyInitialWeatherProfile();
    void applyDailyWeatherRollover(int weatherDayIndex);
    void applyFogDistances(const OutdoorFogDistances &distances, bool foggy);
    void syncAtmosphereStateToMapDelta();
    int weatherDayIndexForMinutes(float gameMinutes) const;
    void resetDailySpellCounters();
    void updateArmageddon(float deltaSeconds, float partyX, float partyY, float partyZ);
    void resolveArmageddonDetonation(float partyX, float partyY, float partyZ);
    void refreshAtmosphereState();
};
}
