#pragma once

#include "game/EventRuntime.h"
#include "game/EventIr.h"
#include "game/MapAssetLoader.h"
#include "game/MapDeltaData.h"
#include "game/MapStats.h"
#include "game/MonsterProjectileTable.h"
#include "game/MonsterTable.h"
#include "game/ObjectTable.h"
#include "game/OutdoorGeometryUtils.h"
#include "game/OutdoorMapData.h"
#include "game/OutdoorMovementController.h"
#include "game/SpellTable.h"

#include <random>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;

class OutdoorWorldRuntime
{
public:
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

    enum class MonsterAttackAbility
    {
        Attack1,
        Attack2,
        Spell1,
        Spell2,
    };

    enum class DebugTargetKind
    {
        None,
        Party,
        Actor,
    };

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
        uint8_t hostilityType = 0;
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
        uint32_t idleDecisionCount = 0;
        uint32_t pursueDecisionCount = 0;
        uint32_t attackDecisionCount = 0;
        bool attackImpactTriggered = false;
        MonsterAttackAbility queuedAttackAbility = MonsterAttackAbility::Attack1;
        OutdoorMoveState movementState = {};
        bool movementStateInitialized = false;
    };

    struct CombatEvent
    {
        enum class Type
        {
            MonsterMeleeImpact,
            MonsterRangedRelease,
            PartyProjectileImpact,
        };

        Type type = Type::MonsterMeleeImpact;
        uint32_t sourceId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Attack1;
        int damage = 0;
        int spellId = 0;
    };

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

    struct ProjectileState
    {
        uint32_t projectileId = 0;
        uint32_t sourceId = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Attack1;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t impactObjectDescriptionId = 0;
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
        float velocityX = 0.0f;
        float velocityY = 0.0f;
        float velocityZ = 0.0f;
        uint32_t timeSinceCreatedTicks = 0;
        uint32_t lifetimeTicks = 0;
        bool isExpired = false;
    };

    struct ProjectileImpactState
    {
        uint32_t effectId = 0;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        std::string objectName;
        std::string objectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint32_t timeSinceCreatedTicks = 0;
        uint32_t lifetimeTicks = 0;
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

    struct ChestItemState
    {
        uint32_t itemId = 0;
        uint32_t quantity = 0;
        uint32_t goldAmount = 0;
        uint32_t goldRollCount = 0;
        bool isGold = false;
    };

    struct ChestViewState
    {
        uint32_t chestId = 0;
        uint16_t chestTypeId = 0;
        uint16_t flags = 0;
        std::vector<ChestItemState> items;
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

    struct CorpseViewState
    {
        bool fromSummonedMonster = false;
        uint32_t sourceIndex = 0;
        std::string title;
        std::vector<ChestItemState> items;
    };

    struct AudioEvent
    {
        uint32_t soundId = 0;
        uint32_t sourceId = 0;
        std::string reason;
    };

    void initialize(
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const MonsterProjectileTable &monsterProjectileTable,
        const ObjectTable &objectTable,
        const SpellTable &spellTable,
        const ItemTable &itemTable,
        const std::optional<OutdoorMapData> &outdoorMapData,
        const std::optional<MapDeltaData> &outdoorMapDeltaData,
        const std::optional<EventRuntimeState> &eventRuntimeState,
        const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet = std::nullopt,
        const std::optional<std::vector<uint8_t>> &outdoorLandMask = std::nullopt,
        const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet = std::nullopt,
        const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet = std::nullopt,
        const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet = std::nullopt,
        const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet = std::nullopt
    );

    bool isInitialized() const;
    int mapId() const;
    const std::string &mapName() const;
    float gameMinutes() const;
    int currentHour() const;
    void advanceGameMinutes(float minutes);
    void updateMapActors(float deltaSeconds, float partyX, float partyY, float partyZ);

    void applyEventRuntimeState();
    bool updateTimers(
        float deltaSeconds,
        const EventRuntime &eventRuntime,
        const std::optional<EventIrProgram> &localEventIrProgram,
        const std::optional<EventIrProgram> &globalEventIrProgram
    );
    bool isChestOpened(uint32_t chestId) const;
    size_t mapActorCount() const;
    const MapActorState *mapActorState(size_t actorIndex) const;
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
    bool notifyPartyContactWithMapActor(size_t actorIndex, float partyX, float partyY, float partyZ);
    size_t spawnPointCount() const;
    const SpawnPointState *spawnPointState(size_t spawnIndex) const;
    size_t chestCount() const;
    size_t openedChestCount() const;
    const ChestViewState *activeChestView() const;
    bool takeActiveChestItem(size_t itemIndex, ChestItemState &item);
    void closeActiveChestView();
    const CorpseViewState *activeCorpseView() const;
    bool openMapActorCorpseView(size_t actorIndex);
    bool takeActiveCorpseItem(size_t itemIndex, ChestItemState &item);
    void closeActiveCorpseView();
    const std::vector<AudioEvent> &pendingAudioEvents() const;
    void clearPendingAudioEvents();
    const std::vector<CombatEvent> &pendingCombatEvents() const;
    void clearPendingCombatEvents();
    size_t projectileCount() const;
    const ProjectileState *projectileState(size_t projectileIndex) const;
    size_t projectileImpactCount() const;
    const ProjectileImpactState *projectileImpactState(size_t effectIndex) const;

    const EventRuntimeState::PendingMapMove *pendingMapMove() const;
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove();

    EventRuntimeState *eventRuntimeState();
    const EventRuntimeState *eventRuntimeState() const;
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
    );
    bool summonMonsters(
        uint32_t typeIndexInMapStats,
        uint32_t level,
        uint32_t count,
        int32_t x,
        int32_t y,
        int32_t z,
        uint32_t group,
        uint32_t uniqueNameId
    );
    bool checkMonstersKilled(uint32_t checkType, uint32_t id, uint32_t count, bool invisibleAsDead) const;

public:
    struct ResolvedProjectileDefinition
    {
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t impactObjectDescriptionId = 0;
        uint16_t impactObjectSpriteId = 0;
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

private:
    static uint32_t makeChestSeed(uint32_t sessionSeed, int mapId, uint32_t chestId, uint32_t salt);
    static void appendChestItem(std::vector<ChestItemState> &items, const ChestItemState &item);
    static int generateGoldAmount(int treasureLevel, std::mt19937 &rng);
    static int remapTreasureLevel(int itemTreasureLevel, int mapTreasureLevel);

    uint32_t generateRandomItemId(int treasureLevel, std::mt19937 &rng) const;
    uint32_t generateRandomLootItemId(
        int treasureLevel,
        MonsterTable::LootItemKind itemKind,
        std::mt19937 &rng
    ) const;
    bool applyMonsterAttackToMapActor(size_t actorIndex, int damage, uint32_t sourceActorId);
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
    CorpseViewState buildCorpseView(const std::string &title, const MonsterTable::LootPrototype &loot, uint32_t seed) const;
    void pushAudioEvent(uint32_t soundId, uint32_t sourceId, const std::string &reason);
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
    bool castDirectSpellProjectile(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition
    );
    bool castMeteorShower(
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
    void collectOutdoorFaceCandidates(float minX, float minY, float maxX, float maxY, std::vector<size_t> &indices) const;
    void updateProjectiles(float deltaSeconds, float partyX, float partyY, float partyZ);
    void spawnProjectileImpact(const ProjectileState &projectile, float x, float y, float z);

    int m_mapId = 0;
    int m_mapTreasureLevel = 0;
    MapStatsEntry m_map = {};
    std::string m_mapName;
    float m_gameMinutes = 9.0f * 60.0f;
    std::vector<TimerState> m_timers;
    std::vector<MapActorState> m_mapActors;
    std::vector<SpawnPointState> m_spawnPoints;
    std::vector<MapDeltaChest> m_chests;
    std::vector<bool> m_openedChests;
    std::vector<std::optional<ChestViewState>> m_materializedChestViews;
    std::optional<ChestViewState> m_activeChestView;
    std::optional<EventRuntimeState> m_eventRuntimeState;
    const ItemTable *m_pItemTable = nullptr;
    const MonsterTable *m_pMonsterTable = nullptr;
    const MonsterProjectileTable *m_pMonsterProjectileTable = nullptr;
    const ObjectTable *m_pObjectTable = nullptr;
    const OutdoorMapData *m_pOutdoorMapData = nullptr;
    const MapDeltaData *m_pOutdoorMapDeltaData = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    const SpriteFrameTable *m_pActorSpriteFrameTable = nullptr;
    const SpriteFrameTable *m_pProjectileSpriteFrameTable = nullptr;
    std::optional<std::vector<uint8_t>> m_outdoorLandMask;
    std::vector<OutdoorFaceGeometryData> m_outdoorFaces;
    std::vector<std::vector<size_t>> m_outdoorFaceGridCells;
    float m_outdoorFaceGridMinX = 0.0f;
    float m_outdoorFaceGridMinY = 0.0f;
    size_t m_outdoorFaceGridWidth = 0;
    size_t m_outdoorFaceGridHeight = 0;
    std::optional<OutdoorMovementController> m_outdoorMovementController;
    std::unordered_map<int16_t, MonsterVisualState> m_monsterVisualsById;
    float m_actorUpdateAccumulatorSeconds = 0.0f;
    uint32_t m_sessionChestSeed = 0;
    uint32_t m_nextActorId = 0;
    std::vector<std::optional<CorpseViewState>> m_mapActorCorpseViews;
    std::optional<CorpseViewState> m_activeCorpseView;
    std::vector<AudioEvent> m_pendingAudioEvents;
    std::vector<CombatEvent> m_pendingCombatEvents;
    uint32_t m_nextProjectileId = 1;
    uint32_t m_nextProjectileImpactId = 1;
    std::vector<ProjectileState> m_projectiles;
    std::vector<ProjectileImpactState> m_projectileImpacts;
};
}
