#pragma once

#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/events/ISceneEventContext.h"
#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/maps/MapDeltaData.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayActorAiSystem;
class GameplayActorService;
class GameplayCombatController;
class GameplayProjectileService;
struct DecorationBillboardSet;
class IndoorRenderer;
class IndoorFaceGeometryCache;
class IndoorGameView;
class IndoorPartyRuntime;
class MonsterProjectileTable;
class SpellTable;
class SpriteFrameTable;

class IndoorWorldRuntime : public ISceneEventContext, public IGameplayWorldRuntime
{
public:
    using ChestItemState = GameplayChestItemState;
    using ChestViewState = GameplayChestViewState;
    using CorpseViewState = GameplayCorpseViewState;

    struct MapActorAiState
    {
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        std::string displayName;
        uint16_t spriteFrameIndex = 0;
        std::array<uint16_t, 8> actionSpriteFrameIndices = {};
        uint16_t collisionRadius = 32;
        uint16_t collisionHeight = 128;
        uint16_t movementSpeed = 0;
        bool hostileToParty = false;
        bool hasDetectedParty = false;
        bool bloodSplatSpawned = false;
        ActorAiMotionState motionState = ActorAiMotionState::Standing;
        ActorAiAnimationState animationState = ActorAiAnimationState::Standing;
        GameplayActorAttackAbility queuedAttackAbility = GameplayActorAttackAbility::Attack1;
        GameplayActorSpellEffectState spellEffects = {};
        float preciseX = 0.0f;
        float preciseY = 0.0f;
        float preciseZ = 0.0f;
        float homePreciseX = 0.0f;
        float homePreciseY = 0.0f;
        float homePreciseZ = 0.0f;
        float moveDirectionX = 0.0f;
        float moveDirectionY = 0.0f;
        float velocityX = 0.0f;
        float velocityY = 0.0f;
        float velocityZ = 0.0f;
        int16_t sectorId = -1;
        int16_t eyeSectorId = -1;
        size_t supportFaceIndex = static_cast<size_t>(-1);
        bool grounded = true;
        float yawRadians = 0.0f;
        float animationTimeTicks = 0.0f;
        float recoverySeconds = 0.0f;
        float attackAnimationSeconds = 0.3f;
        float meleeAttackAnimationSeconds = 0.3f;
        float rangedAttackAnimationSeconds = 0.3f;
        float dyingAnimationSeconds = 0.6f;
        float attackCooldownSeconds = 0.0f;
        float idleDecisionSeconds = 0.0f;
        float actionSeconds = 0.0f;
        float crowdSideLockRemainingSeconds = 0.0f;
        float crowdNoProgressSeconds = 0.0f;
        float crowdLastEdgeDistance = 0.0f;
        float crowdRetreatRemainingSeconds = 0.0f;
        float crowdStandRemainingSeconds = 0.0f;
        float crowdProbeEdgeDistance = 0.0f;
        float crowdProbeElapsedSeconds = 0.0f;
        uint32_t idleDecisionCount = 0;
        uint32_t pursueDecisionCount = 0;
        uint32_t attackDecisionCount = 0;
        uint8_t crowdEscapeAttempts = 0;
        int8_t crowdSideSign = 0;
        bool attackImpactTriggered = false;
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

    struct Snapshot
    {
        float gameMinutes = 9.0f * 60.0f;
        int currentLocationReputation = 0;
        uint32_t sessionChestSeed = 0;
        std::vector<std::optional<ChestViewState>> materializedChestViews;
        std::optional<ChestViewState> activeChestView;
        std::vector<std::optional<CorpseViewState>> mapActorCorpseViews;
        std::optional<CorpseViewState> activeCorpseView;
        std::vector<GameplayActorSpellEffectState> mapActorSpellEffectStates;
        std::vector<MapActorAiState> mapActorAiStates;
        std::vector<BloodSplatState> bloodSplats;
        float actorUpdateAccumulatorSeconds = 0.0f;
    };

    IndoorWorldRuntime() = default;

    void bindRenderer(IndoorRenderer *pRenderer);
    void bindGameplayView(IndoorGameView *pView);
    void bindEventExecution(
        const EventRuntime *pEventRuntime,
        const std::optional<ScriptedEventProgram> *pLocalEventProgram,
        const std::optional<ScriptedEventProgram> *pGlobalEventProgram);
    bool executeFaceTriggeredEvent(
        size_t faceIndex,
        FaceAttribute triggerAttribute,
        bool grantItemsToInventory);

    void initialize(
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const MonsterProjectileTable &monsterProjectileTable,
        const ObjectTable &objectTable,
        const SpellTable &spellTable,
        const ItemTable &itemTable,
        const ChestTable &chestTable,
        Party *pParty,
        IndoorPartyRuntime *pPartyRuntime,
        std::optional<MapDeltaData> *pMapDeltaData,
        std::optional<EventRuntimeState> *pEventRuntimeState,
        GameplayActorService *pGameplayActorService,
        GameplayProjectileService *pGameplayProjectileService,
        GameplayCombatController *pGameplayCombatController = nullptr,
        const SpriteFrameTable *pActorSpriteFrameTable = nullptr,
        const SpriteFrameTable *pProjectileSpriteFrameTable = nullptr,
        const IndoorMapData *pIndoorMapData = nullptr,
        const DecorationBillboardSet *pIndoorDecorationBillboardSet = nullptr
    );
    void initialize(
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const ObjectTable &objectTable,
        const ItemTable &itemTable,
        const ChestTable &chestTable,
        Party *pParty,
        IndoorPartyRuntime *pPartyRuntime,
        std::optional<MapDeltaData> *pMapDeltaData,
        std::optional<EventRuntimeState> *pEventRuntimeState,
        GameplayActorService *pGameplayActorService,
        const SpriteFrameTable *pActorSpriteFrameTable = nullptr,
        const IndoorMapData *pIndoorMapData = nullptr,
        const DecorationBillboardSet *pIndoorDecorationBillboardSet = nullptr
    );

    const std::string &mapName() const override;
    float currentGameMinutes() const override;
    const MapDeltaData *mapDeltaData() const override;
    float gameMinutes() const override;
    int currentHour() const override;
    void advanceGameMinutes(float minutes) override;
    int currentLocationReputation() const override;
    void setCurrentLocationReputation(int reputation) override;
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
    void cancelPendingMapTransition() override;
    bool executeNpcTopicEvent(uint16_t eventId, size_t &previousMessageCount) override;
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
    bool specialJump(uint32_t encodedHorizontalVelocity, uint32_t verticalVelocity) override;
    size_t mapActorCount() const override;
    const MapActorAiState *mapActorAiState(size_t actorIndex) const;
    size_t bloodSplatCount() const;
    const BloodSplatState *bloodSplatState(size_t splatIndex) const;
    uint64_t bloodSplatRevision() const;
    void collectProjectilePresentationState(
        std::vector<GameplayProjectilePresentationState> &projectiles,
        std::vector<GameplayProjectileImpactPresentationState> &impacts) const;
    bool actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const override;
    bool actorInspectState(
        size_t actorIndex,
        uint32_t animationTicks,
        GameplayActorInspectState &state) const override;
    std::optional<GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const override;
    bool castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request) override;
    bool applyPartySpellToActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex) override;
    std::vector<size_t> collectMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        bool requireLineOfSight,
        float sourceX,
        float sourceY,
        float sourceZ) const override;
    bool spawnPartyFireSpikeTrap(
        uint32_t casterMemberIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        float x,
        float y,
        float z) override;
    bool summonFriendlyMonsterById(
        int16_t monsterId,
        uint32_t count,
        float durationSeconds,
        float x,
        float y,
        float z) override;
    bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        std::string &failureText) override;
    bool canActivateWorldHit(
        const GameplayWorldHit &hit,
        GameplayInteractionMethod interactionMethod) const override;
    bool activateWorldHit(const GameplayWorldHit &hit) override;
    std::optional<GameplayPartyAttackActorFacts> partyAttackActorFacts(
        size_t actorIndex,
        bool visibleForFallback) const override;
    std::vector<GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const GameplayPartyAttackFallbackQuery &query) const override;
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
    GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickHeldItemWorldTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickMouseInteractionTarget(const GameplayWorldPickRequest &request) override;
    bool worldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state) const override;
    bool updateWorldItemInspectState(size_t worldItemIndex, const InventoryItem &item) override;
    GameplayWorldHoverCacheState worldHoverCacheState() const override;
    GameplayHoverStatusPayload refreshWorldHover(const GameplayWorldHoverRequest &request) override;
    GameplayHoverStatusPayload readCachedWorldHover() override;
    void clearWorldHover() override;
    bool canUseHeldItemOnWorld(const GameplayWorldHit &hit) const override;
    bool useHeldItemOnWorld(const GameplayWorldHit &hit) override;
    void applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult) override;
    bool dropHeldItemToWorld(const GameplayHeldItemDropRequest &request) override;
    bool tryGetGameplayMinimapState(GameplayMinimapState &state) const override;
    void collectGameplayMinimapLines(std::vector<GameplayMinimapLineState> &lines) override;
    void collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const override;
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
    bool checkMonstersKilled(
        uint32_t checkType,
        uint32_t id,
        uint32_t count,
        bool invisibleAsDead
    ) const override;

    void applyEventRuntimeState();
    void invalidateRuntimeGeometryCache();
    void refreshMechanismRuntimeGeometryCache();
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);

    MapDeltaData *mapDeltaData();
    std::vector<IndoorActorCollision> actorMovementCollidersForActorMovement(
        const std::vector<size_t> &activeActorIndices) const;
    std::vector<IndoorActorCollision> actorMovementCollidersForPartyMovement() const;
    std::vector<IndoorCylinderCollision> decorationMovementColliders() const;
    std::vector<IndoorCylinderCollision> spriteObjectMovementColliders() const;

private:
    struct RuntimeGeometryCache
    {
        bool valid = false;
        std::vector<IndoorVertex> vertices;
        IndoorFaceGeometryCache geometryCache;
    };

    const MapEncounterInfo *encounterInfo(uint32_t typeIndexInMapStats) const;
    const MonsterTable::MonsterStatsEntry *resolveEncounterStats(
        uint32_t typeIndexInMapStats,
        uint32_t level
    ) const;
    bool autoLootMapActorCorpse(size_t actorIndex);
    bool materializeTreasureSpawn(size_t spawnIndex, const IndoorSpawn &spawn);
    void materializeInitialMonsterSpawns();
    void syncMapActorAiStates();
    RuntimeGeometryCache &runtimeGeometryCache() const;
    std::vector<bool> selectIndoorActiveActors(
        const ActorPartyFacts &partyFacts,
        int16_t partySectorId,
        const std::vector<IndoorVertex> &vertices,
        IndoorFaceGeometryCache &geometryCache) const;
    ActorAiFrameFacts collectIndoorActorAiFrameFacts(float deltaSeconds) const;
    std::vector<bool> applyIndoorActorAiFrameResult(
        const ActorAiFrameResult &result,
        const GameplayActorAiSystem &actorAiSystem);
    void applyIndoorActorMovementIntegration(
        IndoorMovementController &movementController,
        size_t actorIndex,
        const ActorAiUpdate &update,
        const GameplayActorAiSystem &actorAiSystem);
    bool applyIndoorActorProjectileRequest(const ActorProjectileRequest &projectileRequest);
    bool addBloodSplat(uint32_t sourceActorId, float x, float y, float z, float radius);
    void bakeBloodSplatGeometry(BloodSplatState &splat) const;
    void spawnBloodSplatForActorIfNeeded(size_t actorIndex);
    void removeBloodSplat(uint32_t sourceActorId);
    void pushIndoorProjectileAudioEvent(
        const GameplayProjectileService::ProjectileAudioRequest &audioRequest);
    bool projectileSourceIsFriendlyToActor(
        const GameplayProjectileService::ProjectileState &projectile,
        const MapActorAiState &actor) const;
    GameplayProjectileService::ProjectileFrameFacts collectIndoorProjectileFrameFacts(
        const GameplayProjectileService::ProjectileState &projectile,
        float deltaSeconds,
        const std::vector<IndoorVertex> &projectileVertices,
        IndoorFaceGeometryCache &projectileGeometryCache) const;
    void applyIndoorProjectileFrameResult(
        GameplayProjectileService::ProjectileState &projectile,
        const GameplayProjectileService::ProjectileFrameFacts &facts,
        const GameplayProjectileService::ProjectileFrameResult &frameResult);
    void updateIndoorProjectiles(float deltaSeconds);
    void updateWorldItems(float deltaSeconds);
    bool updateWorldItemsStep(
        float deltaSeconds,
        const std::vector<IndoorVertex> &vertices,
        IndoorFaceGeometryCache &geometryCache);
    std::optional<ActorAiFacts> collectIndoorActorAiFacts(
        size_t actorIndex,
        bool active,
        const ActorPartyFacts &partyFacts,
        const std::vector<IndoorVertex> &vertices,
        IndoorFaceGeometryCache &geometryCache
    ) const;
    ChestViewState buildChestView(uint32_t chestId) const;
    void activateChestView(uint32_t chestId);
    void beginMapActorDyingState(size_t actorIndex, MapDeltaActor &actor);
    std::optional<GameplayWorldPoint> actorImpactPoint(size_t actorIndex) const;
    bool spawnIndoorProjectileImpactVisual(
        const GameplayProjectileService::ProjectileState &projectile,
        const GameplayWorldPoint &point,
        bool centerVertically);
    bool spawnIndoorWaterSplashImpactVisual(const GameplayWorldPoint &point);
    bool spawnImmediateSpellImpactVisualAt(
        const GameplayWorldPoint &point,
        uint32_t spellId,
        bool centerVertically = false,
        bool preferImpactObject = true);
    void spawnImmediateSpellImpactVisual(size_t actorIndex, uint32_t spellId);
    void updateIndoorJournalRevealIfNeeded();

    std::optional<MapStatsEntry> m_map;
    const MonsterTable *m_pMonsterTable = nullptr;
    const MonsterProjectileTable *m_pMonsterProjectileTable = nullptr;
    const ObjectTable *m_pObjectTable = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    const ItemTable *m_pItemTable = nullptr;
    const ChestTable *m_pChestTable = nullptr;
    const SpriteFrameTable *m_pActorSpriteFrameTable = nullptr;
    const SpriteFrameTable *m_pProjectileSpriteFrameTable = nullptr;
    const IndoorMapData *m_pIndoorMapData = nullptr;
    const DecorationBillboardSet *m_pIndoorDecorationBillboardSet = nullptr;
    Party *m_pParty = nullptr;
    IndoorPartyRuntime *m_pPartyRuntime = nullptr;
    std::optional<MapDeltaData> *m_pMapDeltaData = nullptr;
    std::optional<EventRuntimeState> *m_pEventRuntimeState = nullptr;
    const EventRuntime *m_pEventRuntime = nullptr;
    const std::optional<ScriptedEventProgram> *m_pLocalEventProgram = nullptr;
    const std::optional<ScriptedEventProgram> *m_pGlobalEventProgram = nullptr;
    GameplayActorService *m_pGameplayActorService = nullptr;
    GameplayProjectileService *m_pGameplayProjectileService = nullptr;
    GameplayCombatController *m_pGameplayCombatController = nullptr;
    IndoorRenderer *m_pRenderer = nullptr;
    IndoorGameView *m_pGameplayView = nullptr;
    std::string m_mapName;
    float m_gameMinutes = 9.0f * 60.0f;
    int m_currentLocationReputation = 0;
    uint32_t m_sessionChestSeed = 0;
    std::vector<std::optional<ChestViewState>> m_materializedChestViews;
    std::optional<ChestViewState> m_activeChestView;
    std::vector<std::optional<CorpseViewState>> m_mapActorCorpseViews;
    std::optional<CorpseViewState> m_activeCorpseView;
    std::vector<MapActorAiState> m_mapActorAiStates;
    std::vector<BloodSplatState> m_bloodSplats;
    uint64_t m_bloodSplatRevision = 0;
    float m_actorUpdateAccumulatorSeconds = 0.0f;
    float m_worldItemUpdateAccumulatorSeconds = 0.0f;
    bool m_indoorJournalRevealStateValid = false;
    int16_t m_lastIndoorJournalRevealSectorId = -1;
    int16_t m_lastIndoorJournalRevealEyeSectorId = -1;
    uint64_t m_lastIndoorJournalRevealSurfaceRevision = 0;
    size_t m_lastIndoorJournalRevealFaceCount = 0;
    size_t m_lastIndoorJournalRevealOutlineCount = 0;
    mutable RuntimeGeometryCache m_runtimeGeometryCache;
    bool m_cachedGameplayMinimapLinesValid = false;
    uint64_t m_cachedGameplayMinimapLineSignature = 0;
    std::vector<GameplayMinimapLineState> m_cachedGameplayMinimapLines;
};
}
