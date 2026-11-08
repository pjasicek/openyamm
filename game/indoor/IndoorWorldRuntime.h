#pragma once

#include "game/gameplay/ActorBehaviorRuntime.h"
#include "game/gameplay/ActorInspectPreviewAnimation.h"
#include "game/gameplay/ArmageddonSpell.h"
#include "game/gameplay/GameplayActorHitFeedback.h"
#include "game/gameplay/GameplayActorModifiers.h"
#include "game/gameplay/GameplayActorShields.h"

#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorMovers.h"
#include "game/events/ISceneEventContext.h"
#include "game/gameplay/GameplayActorAiTypes.h"
#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/MonsterDeathExplosion.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/gameplay/SearchableLootPropRuntime.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/indoor/IndoorMovementController.h"
#include "game/indoor/IndoorSectorFaceGrid.h"
#include "game/maps/MapDeltaData.h"
#include "game/pathfinding/ActorPathRuntime.h"
#include "game/pathfinding/PathMap.h"
#include "game/rules/CorpseLoot.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"

#include <array>
#include <future>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayActorAiSystem;
class GameplayActorService;
class GameplayCombatController;
class GameplayProjectileService;
struct ChestTrapOpenResult;
struct Mm9PartyAwareness;
struct DecorationBillboardSet;
class IndoorRenderer;
class IndoorFaceGeometryCache;
class IndoorGameView;
class IndoorPartyRuntime;
class MergedBolsterMapTable;
class MergedBolsterMonsterTable;
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
        std::string actorProfile;
        uint32_t actorId = 0;
        // The monster that last hit it; it fights that one back (not saved).
        std::optional<uint32_t> lastActorAttackerId;
        int16_t monsterId = 0;
        std::string displayName;
        uint16_t spriteFrameIndex = 0;
        std::array<uint16_t, 8> actionSpriteFrameIndices = {};
        uint16_t collisionRadius = 32;
        uint16_t collisionHeight = 128;
        uint16_t projectileHitRadius = 32;
        uint16_t movementSpeed = 0;
        float bolsterRewardMultiplier = 1.0f;
        // The killing blow came from a party member (their weapons and spells), read as the death begins.
        bool killedByParty = false;
        GameplayActorAiType aiType = GameplayActorAiType::Normal;
        bool canFly = false;
        // A swimmer in a scene water volume (MM9's Sea Monsters, Spores): the volume it started in, which it swims in
        // and never leaves (-1: none). Runtime only, found from its position the first time the AI sees it.
        int16_t waterVolumeIndex = -1;
        bool waterVolumeResolved = false;
        CombatDamageType attack1DamageType = CombatDamageType::Physical;
        CombatDamageType attack2DamageType = CombatDamageType::Physical;
        uint32_t spell1Id = 0;
        CombatDamageType spell1DamageType = CombatDamageType::Physical;
        bool spell1CastSupported = true;
        uint32_t spell2Id = 0;
        CombatDamageType spell2DamageType = CombatDamageType::Physical;
        bool spell2CastSupported = true;
        float wanderRadius = 0.0f;
        bool hostileToParty = false;
        // The party made it hostile (hit it or its faction), so a hit on it still alerts its friendly faction; an
        // actor hostile on its own (map, template, event) alerts none.
        bool angeredByParty = false;
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
        // Horizontal speed the AI's movement asked for before collision; 0 when it did not try to move.
        float intendedSpeed = 0.0f;
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
        // The monster's attack contact frames, attack sound delays and fidget length from the sprite frame table,
        // looked up once instead of by sprite name on every AI step. Not saved: refreshed with the fields above.
        float meleeAttackImpactSeconds = 0.0f;
        float rangedAttackImpactSeconds = 0.0f;
        // A spell's action and cast where the model's cast clip times them (ActorRuntimeFacts); 0: the ranged attack's.
        float spellAttackAnimationSeconds = 0.0f;
        float spellAttackImpactSeconds = 0.0f;
        float meleeAttackSoundDelaySeconds = 0.0f;
        float rangedAttackSoundDelaySeconds = 0.0f;
        float boredAnimationSeconds = 2.0f;
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
        double suppressDirectPathUntilSeconds = 0.0;
        double nextPositionRecoveryAttemptSeconds = 0.0;
        uint32_t idleDecisionCount = 0;
        uint32_t pursueDecisionCount = 0;
        uint32_t attackDecisionCount = 0;
        uint8_t crowdEscapeAttempts = 0;
        int8_t crowdSideSign = 0;
        // Runtime only: carried between movement steps, as IndoorMoveState holds it for a single step.
        uint8_t stuckRecoveryCooldownSteps = 0;
        bool attackImpactTriggered = false;
        // A skirmisher's footwork (ActorRuntimeFacts::skirmishPhase); runtime only, not saved.
        ActorSkirmishPhase skirmishPhase = ActorSkirmishPhase::None;
        float skirmishSeconds = 0.0f;
        int8_t skirmishSide = 1;
        // An MM9 walker's loop (ActorRuntimeFacts::mm9) and what the world knows for it (ActorAiFacts::mm9World);
        // runtime only, not saved.
        ActorMm9State mm9;
        ActorMm9WorldFacts mm9World;
        // A party hit provoked it (Mm9PartyAwareness::provokeRange): it keeps the party it holds that far, and thinks
        // ahead of the nearest MM9 monsters. Cleared once it holds no target; runtime only, not saved.
        bool mm9Provoked = false;
        bool suppressLowHealthFlee = false;
        // A villager the party yelled at runs from it until this runs out (scareNearbyPeasants); not saved.
        float yellFleeRemainingSeconds = 0.0f;
        // The monster's stats as bolstered for this map, resolved once when the state is built (map load, spawn or
        // save restore); empty without monster stats.
        std::optional<GameplayMonsterBolsterResult> bolster;
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

    struct FireSpikeTrapState
    {
        uint32_t trapId = 0;
        GameplayProjectileService::ProjectileState::SourceKind sourceKind =
            GameplayProjectileService::ProjectileState::SourceKind::Party;
        uint32_t sourceId = 0;
        uint32_t sourcePartyMemberIndex = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        GameplayProjectileService::MonsterAttackAbility ability =
            GameplayProjectileService::MonsterAttackAbility::Attack1;
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
        int16_t sectorId = -1;
        uint32_t timeSinceCreatedTicks = 0;
        bool isExpired = false;
    };

    struct Snapshot
    {
        float gameMinutes = 9.0f * 60.0f;
        int currentLocationReputation = 0;
        uint32_t sessionChestSeed = 0;
        std::vector<std::optional<ChestViewState>> materializedChestViews;
        std::optional<ChestViewState> activeChestView;
        std::vector<std::optional<CorpseViewState>> mapActorCorpseViews;
        std::vector<std::optional<CorpseViewState>> mapActorRevealedLoot;
        std::optional<CorpseViewState> activeCorpseView;
        std::vector<GameplayActorSpellEffectState> mapActorSpellEffectStates;
        std::vector<MapActorAiState> mapActorAiStates;
        std::vector<uint8_t> activatedIndoorSectorMask;
        std::vector<BloodSplatState> bloodSplats;
        std::vector<FireSpikeTrapState> fireSpikeTraps;
        float actorUpdateAccumulatorSeconds = 0.0f;
        GameplayProjectileService::Snapshot projectileState;
        std::vector<std::string> searchedLootPropSourceIds;
        ActorBehaviorRuntime::Snapshot actorBehaviors;
        // On a map open to the sky (isOpenAirMap), the only indoor maps where the party casts it.
        ArmageddonState armageddon;
    };

    IndoorWorldRuntime() = default;

    void bindRenderer(IndoorRenderer *pRenderer);
    void bindGameplayView(IndoorGameView *pView);
    void bindEventExecution(
        const EventRuntime *pEventRuntime,
        const std::optional<ScriptedEventProgram> *pLocalEventProgram,
        const std::optional<ScriptedEventProgram> *pGlobalEventProgram);
    void bindActorBehaviorCatalog(const ActorBehaviorCatalog *pCatalog);
    ActorBehaviorRuntime *actorBehaviorRuntime() override;
    const ActorBehaviorRuntime *actorBehaviorRuntime() const override;
    GameplayActorShields *actorShields() override
    {
        return &m_actorShields;
    }
    const GameplayActorShields *actorShields() const override
    {
        return &m_actorShields;
    }
    // The party talks to an actor that is not hostile: it faces the party at once (its model turns to it at its own
    // rate) and stands, and an MM9 one keeps the facing it turns back to afterwards (ActorMm9State::beginTalk).
    bool faceMapActorForTalk(size_t actorIndex, float partyX, float partyY);
    bool stunActor(size_t actorIndex, float seconds) override;
    bool debuffActor(size_t actorIndex, GameplayActorHitDebuff debuff, float seconds, float power) override;
    bool setMapActorBehavior(size_t actorIndex, const std::string &behaviorId) override;
    bool triggerMapActor(size_t actorIndex, const std::string &message) override;
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
        const DecorationBillboardSet *pIndoorDecorationBillboardSet = nullptr,
        const MergedBolsterMapTable *pMergedBolsterMapTable = nullptr,
        const MergedBolsterMonsterTable *pMergedBolsterMonsterTable = nullptr,
        const MapItemSourceData *pItemSourceData = nullptr
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
        const DecorationBillboardSet *pIndoorDecorationBillboardSet = nullptr,
        const MergedBolsterMapTable *pMergedBolsterMapTable = nullptr,
        const MergedBolsterMonsterTable *pMergedBolsterMonsterTable = nullptr,
        const MapItemSourceData *pItemSourceData = nullptr
    );
    void setBolsterMonstersEnabled(bool enabled);

    const std::string &mapName() const override;
    const MonsterTable *monsterTable() const override;
    const SpellTable *spellTable() const override
    {
        return m_pSpellTable;
    }
    const MapStatsEntry *arenaMap() const override
    {
        return m_map && m_map->runtimeRestrictions.isArena && m_map->arena ? &*m_map : nullptr;
    }
    const MergedBolsterMonsterTable *mergedBolsterMonsterTable() const override;
    bool isIndoorMap() const override;
    bool isOpenAirMap() const override;
    bool partyClimbingLadder() const override;
    bool partySwimming() const override;
    std::optional<float> partyBreathFraction() const override;
    bool allowsLloydsBeacon() const override;
    bool allowsRest() const override;
    float currentGameMinutes() const override;
    const MapDeltaData *mapDeltaData() const override;
    MapDeltaData *mapDeltaData() override;
    bool setFacetBit(uint32_t cogNumber, uint32_t bit, bool isOn) override;
    std::optional<uint32_t> decorationSpriteKeyForScriptEvent(uint16_t eventId) const override;
    std::vector<uint32_t> resolveIndoorLightReferenceIds(int32_t rawReferenceId) const override;
    std::optional<bool> indoorMoverSpinStartsOn(uint32_t doorId) const override;
    bool isMapActorHostile(size_t actorIndex) const override;
    bool isMapActorDead(size_t actorIndex) const override;
    bool isMapActorWithinPartyDistance(size_t actorIndex, float distance) const override;
    bool searchLootProp(const std::string &sourceId) override;
    bool useMm9Barrel(const std::string &sourceId) override;
    bool useMm9BarrelEvent(uint16_t eventId) override;
    bool spawnLootContainer(const std::string &sourceId) override;
    bool damageDestructible(uint32_t id, int damage) override;
    bool destroyDestructible(uint32_t id) override;
    bool setDestructibleDamageEnabled(uint32_t id, bool enabled) override;
    // A melee blow on a face (the world surface hit's face index): a destructible's faces take its damage.
    bool applyPartyAttackMeleeBModelDamage(size_t faceIndex, int damage) override;
    bool isPartyAttackMeleeBModelTarget(size_t faceIndex) const override;
    // A melee blow on a decoration (an entity index): a destructible prop takes its damage.
    bool applyPartyAttackMeleeEntityDamage(size_t entityIndex, int damage) override;
    bool isPartyAttackMeleeEntityTarget(size_t entityIndex) const override;
    const std::vector<WorldAmbientSound> *ambientSounds() const override;
    bool consumeWorldItem(const std::string &sourceId) override;
    bool setPersistentItemMechanismState(
        const std::string &sourceId,
        bool visible,
        bool solid) override;
    bool setPersistentItemMechanismVariant(
        const std::string &sourceId,
        uint32_t variantIndex) override;
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
    void teleportParty(float x, float y, float footZ) override;
    float partyEyeZ() const override;
    float partyEngagementRange() const override;
    float partyHitReach() const override;
    GameplayWorldPoint chooseBountyHuntSpawnPoint(uint32_t seed) const override;
    float gameplayCameraYawRadians() const override;
    float gameplayCameraPitchRadians() const override;
    float gameplayViewAspectRatio() const override;
    bool partyNeedsTurnBasedPhysicsUpdate() const override;
    void syncSpellMovementStatesFromPartyBuffs() override;
    void requestPartyJump(float verticalVelocity = 0.0f, float lift = 1.0f) override;
    void setAlwaysRunEnabled(bool enabled) override;
    void updateWorldMovement(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput) override;
    void setScenarioPartyActorCollisionEnabled(bool enabled) override;
    bool scenarioPartyActorCollisionEnabled() const;
    void updateActorAi(float deltaSeconds) override;
    void updateTurnBasedPausedActorAnimations(float deltaSeconds) override;
    size_t turnBasedPendingWorldActionCount() const override;
    void scareNearbyPeasants(float radius, float seconds) override;
    bool turnBasedActorActionInProgress() const override;
    void advanceTurnBasedActorTimers(float seconds) override;
    void setTurnBasedActorMode(ActorTurnBasedMode mode) override;
    void grantTurnBasedActorAction(size_t actorIndex) override;
    bool turnBasedActorActionGrantPending() const override;
    int turnBasedActorRecoveryTicks(size_t actorIndex) const override;
    void setActorAttackCooldownSeconds(size_t actorIndex, float seconds) override;
    void updateWorld(float deltaSeconds) override;
    void renderWorld(
        int width,
        int height,
        const GameplayInputFrame &input,
        float deltaSeconds) override;
    GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const override;
    bool requestTravelAutosave() override;
    void cancelPendingMapTransition() override;
    bool executeNpcTopicEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override;
    bool executeMapEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override;
    bool executeEventHooks(EventRuntimeHookKind kind) override;
    const std::optional<ScriptedEventProgram> *globalEventProgram() const override;
    EventRuntimeState *eventRuntimeState() override;
    ISceneEventContext *sceneEventContext() override
    {
        return this;
    }
    const EventRuntimeState *eventRuntimeState() const override;
    bool fireEventMissile(const EventMissileRequest &request) override;
    bool turnMapActors(std::optional<size_t> actorIndex, uint32_t group, float seconds) override;
    bool wakeMapActors(std::optional<size_t> actorIndex, uint32_t group) override;
    bool setMapActorTarget(size_t actorIndex, std::optional<size_t> targetActorIndex) override;
    bool hasLineOfSight(float fromX, float fromY, float fromZ, float toX, float toY, float toZ) const override;
    bool summonEventGold(uint32_t amount, int32_t x, int32_t y, int32_t z, int32_t speed) override;
    bool mapActorPosition(size_t actorIndex, float &x, float &y, float &z) const override;
    // Moves an actor to stand at a point (feet at z) and makes it its home: evt.SetMapActorPosition indoors.
    bool setMapActorPosition(size_t actorIndex, float x, float y, float z) override;
    bool killMapActor(size_t actorIndex) override;
    bool setMapActorHp(size_t actorIndex, int hp) override;
    bool setMapActorImmobile(size_t actorIndex, bool immobile) override;
    bool setMm9ActorCanReceiveDamage(size_t actorIndex, bool canReceiveDamage) override;
    // MM9's CanDamage off (the scene's mm9_can_receive_damage false): no hit hurts the actor.
    bool mm9ActorRefusesDamage(size_t actorIndex) const;
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
    std::vector<int16_t> activatedIndoorSectorIds() const;
    // The map's sector face grid (IndoorSectorFaceGrid.h): built with the map state, valid for any door pose, so a
    // geometry cache over the renderer's vertices may use it too. Null without a map.
    const IndoorSectorFaceGrid *sectorFaceGrid() const;
    // The scene's `actor_movement: {drops: follow}`: monsters go down ledges of any height (MM9).
    bool actorDropsFollow() const;
    size_t bloodSplatCount() const;
    const BloodSplatState *bloodSplatState(size_t splatIndex) const;
    uint64_t bloodSplatRevision() const;
    void collectProjectilePresentationState(
        std::vector<GameplayProjectilePresentationState> &projectiles,
        std::vector<GameplayProjectileImpactPresentationState> &impacts) const;
    bool actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const override;
    bool actorRulesView(size_t actorIndex, GameplayActorRulesView &view) const override;
    GameplayActorHitFeedback &actorHitFeedback() override
    {
        return m_actorHitFeedback;
    }
    const GameplayActorHitFeedback &actorHitFeedback() const override
    {
        return m_actorHitFeedback;
    }
    std::optional<uint32_t> corpseLootValue(size_t actorIndex) const override;
    std::optional<CorpseViewState> revealActorLoot(size_t actorIndex) override;
    bool tryStealFromActor(size_t actorIndex, uint32_t successRoll, uint32_t caughtRoll) override;
    bool actorInspectState(
        size_t actorIndex,
        uint32_t animationTicks,
        GameplayActorInspectState &state) const override;
    std::optional<GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const override;
    bool applyReflectedDamageToActor(
        uint32_t actorId,
        int damage,
        CombatDamageType damageType,
        uint32_t sourcePartyMemberIndex) override;
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
        uint32_t sourcePartyMemberIndex,
        bool critical) override;
    std::vector<size_t> collectMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        bool requireLineOfSight,
        float sourceX,
        float sourceY,
        float sourceZ) const override;
    std::vector<size_t> collectVisibleMapActorIndicesWithinRadius(
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
        float viewAspectRatio) const override;
    void collectWorldItemPresentationStates(
        std::vector<GameplayWorldItemPresentationState> &items) const override;
    void collectFireSpikeTrapPresentationStates(
        std::vector<GameplayProjectilePresentationState> &traps) const override;
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
        float z,
        int32_t summonerMemberIndex) override;
    bool debugFireActorProjectile(
        size_t actorIndex,
        GameplayActorAttackAbility ability,
        const GameplayWorldPoint &target) override;
    bool debugFireActorProjectileAtParty(size_t actorIndex, GameplayActorAttackAbility ability, int damage) override;
    bool blinkActor(size_t actorIndex) override;
    bool suspendActorShield(size_t actorIndex, float seconds) override;
    bool restoreActorShield(size_t actorIndex) override;
    bool swapActorPlaces(size_t actorIndex, std::optional<size_t> otherActorIndex) override;
    bool pushActor(size_t actorIndex, float directionX, float directionY, float distance) override;
    size_t revealActorsAround(size_t actorIndex, float radius) override;
    bool launchParty(float headingRadians, float horizontalSpeed, float verticalSpeed) override;
    bool liftParty(float height) override;
    bool dashParty(float directionX, float directionY, float distance) override;
    size_t gatherCorpsesToParty(size_t maxCount) override;
    size_t gatherWorldItemsToParty(size_t maxCount, const std::function<bool(const InventoryItem &)> &gathers) override;
    std::vector<size_t> lootableCorpseActorIndices() const override;
    bool openActorCorpseView(size_t actorIndex) override;
    const GameplayProjectileService *projectileServiceView() const override
    {
        return m_pGameplayProjectileService;
    }
    bool chargeActor(size_t actorIndex) override;
    bool frenzyActor(size_t actorIndex) override;
    std::optional<GameplayChargeCounts> chargeCounts() const override;
    // Moves a living actor to (x, y) for a blink or a charge's step when the spot is free: a floor in a sector within
    // maxHeightChange of its own (walkable for walkers) with headroom, no wall within its radius, no other actor or
    // the party in its cylinder, and a clear line from where it stands; with keepSightOf also a clear line from there
    // to that point. pBlockedByParty (optional) tells that the party's cylinder was in the way.
    bool blinkMapActorTo(size_t actorIndex, float x, float y, float maxHeightChange,
        const std::optional<std::array<float, 3>> &keepSightOf = std::nullopt, bool *pBlockedByParty = nullptr);
    // Stands a living actor at a point of the sector with its feet at footZ, without the blink's checks; false when
    // a walker finds no floor there.
    bool placeMapActorAt(size_t actorIndex, float x, float y, float footZ, int16_t sectorId);
    // Where a living actor could stand at (x, y): the blink's checks without the move (blinkMapActorTo). The sight
    // line to keepSightOf starts at its eye eyeBelowTop under the top of its body there (MM9's eye; none: 70 % of its
    // height); pSightChecks (optional) counts the sight lines tested.
    struct IndoorActorSpot
    {
        float footZ = 0.0f;
        int16_t sectorId = -1;
    };
    std::optional<IndoorActorSpot> checkMapActorSpot(size_t actorIndex, float x, float y, float maxHeightChange,
        const std::optional<std::array<float, 3>> &keepSightOf, bool *pBlockedByParty,
        std::optional<float> eyeBelowTop, int *pSightChecks);
    bool mapKillProgress(MapKillProgress &progress) const override;
    size_t reviveSlainMonsters(float experienceShare) override;
    std::vector<size_t> spawnMonsters(const GameplayMonsterSpawnRequest &request) override;
    void bindActorAiTrace(ActorAiTrace *pTrace) override;
    const ActorAiTrace *actorAiTrace() const override;
    bool summonHostileMonsterById(
        int16_t monsterId,
        uint32_t count,
        float x,
        float y,
        float z,
        uint32_t group) override;
    bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        std::string &failureText) override;
    bool canActivateWorldHit(
        const GameplayWorldHit &hit,
        GameplayInteractionMethod interactionMethod) const override;
    bool activateWorldHit(const GameplayWorldHit &hit) override;
    bool activateWorldHitFromSpell(const GameplayWorldHit &hit, uint32_t spellId) override;
    bool canActivateTelekinesisTarget(const GameplayWorldHit &hit) const override;
    bool activateTelekinesisTarget(const GameplayWorldHit &hit) override;
    std::optional<GameplayPartyAttackActorFacts> partyAttackActorFacts(
        size_t actorIndex,
        bool visibleForFallback) const override;
    std::vector<GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const GameplayPartyAttackFallbackQuery &query) const override;
    std::optional<GameplayWorldPoint> partyAttackActorContactPoint(
        size_t actorIndex,
        const GameplayPartyAttackFallbackQuery &query) const override;
    bool applyPartyAttackMeleeDamage(
        size_t actorIndex,
        int damage,
        CombatDamageType damageType,
        const GameplayWorldPoint &source,
        ShieldAttackTier shieldTier,
        const ShieldHitModifiers &shieldModifiers = {});
    bool applyPartyAttackMeleeDamage(
        size_t actorIndex,
        int damage,
        const GameplayWorldPoint &source,
        ShieldAttackTier shieldTier,
        const ShieldHitModifiers &shieldModifiers = {}) override;
    void applyPartyAttackMeleeEffects(
        size_t actorIndex,
        const CharacterAttackResult &attack,
        const GameplayWorldPoint &source) override;
    bool spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request) override;
    bool castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request) override;
    std::vector<GameplayCombatFeedbackEvent> drainCombatFeedbackEvents() override;
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
    std::vector<size_t> spellActionVisibleHostileActorIndices() const override;
    std::optional<bx::Vec3> spellActionActorTargetPoint(size_t actorIndex) const override;
    std::optional<bx::Vec3> spellActionGroundTargetPoint(float screenX, float screenY) const override;
    GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickHeldItemWorldTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickMouseInteractionTarget(const GameplayWorldPickRequest &request) override;
    bool hasCustomWorldItemActivation(size_t worldItemIndex) const override;
    bool activateCustomWorldItem(size_t worldItemIndex) override;
    bool worldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state) const override;
    bool updateWorldItemInspectState(size_t worldItemIndex, const InventoryItem &item) override;
    bool takeWorldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state) override;
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
    // Rolls the actor's corpse loot once (at death, before a steal, or after loading) into its corpse view.
    bool ensureMapActorCorpseView(size_t actorIndex);
    std::vector<uint32_t> mapActorGuaranteedItemIds(size_t actorIndex) const;
    // What the actor carries as the rules size it; nothing for an actor without random loot.
    CorpseLoot mapActorCorpseLoot(
        size_t actorIndex,
        const MonsterTable::MonsterStatsEntry &stats,
        CorpseLootPart part = CorpseLootPart::All) const;
    // After a load: dead actors whose corpse loot was never rolled get it on the first AI update.
    void rollPendingCorpseLoot();
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
    bool summonEventInventoryItem(
        const InventoryItem &item,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        bool randomRotate
    ) override;
    bool summonEventObject(
        uint32_t objectId,
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

    void applyEventRuntimeState(bool syncPersistentHostilityMasks = false) override;
    void invalidateRuntimeGeometryCache();
    // The monsters' path map is stale: rebuilt off the main thread while they keep the previous one.
    void markIndoorPathMapStale() const;
    // Takes a rebuilt path map that has landed (the next AI update).
    void adoptPendingIndoorPathMap();
    void waitForPendingIndoorPathMap() const;
    // The live actors whose bodies reach into a box, and moving one of them (the rotating movers' body rules,
    // devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md).
    void collectMoverActorBodies(
        const bx::Vec3 &minimum,
        const bx::Vec3 &maximum,
        std::vector<std::pair<size_t, IndoorMoverBody>> &bodies) const;
    void displaceActorByMover(size_t actorIndex, float deltaX, float deltaY, float deltaZ);
    std::vector<uint32_t> refreshMechanismRuntimeGeometryCache(
        const std::unordered_map<uint32_t, RuntimeMechanismState> &previousMechanisms);
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    void applyMapReentryReset() override;
    void refreshRulesetMonsters() override;
    bool healMapActor(size_t actorIndex, int amount) override;
    ActorRulesetFacts *mutableActorRulesetFacts(size_t actorIndex) override;

    // Meteor Shower's and Starburst's shots fall on their landing points around the target, each from as high up to
    // its own height as the room above where it lands leaves clear.
    bool spawnIndoorFallingShots(
        const GameplayProjectileService::ProjectileSpawnRequest &baseRequest,
        const std::vector<GameplayProjectileService::AreaSpellProjectileShot> &shots,
        const GameplayWorldPoint &target);
    // A line longer than maximumRange (0: the shared detection range, 5 120) never counts as clear.
    bool hasIndoorCombatLineOfSight(
        const GameplayWorldPoint &from,
        int16_t fromSectorId,
        const GameplayWorldPoint &to,
        int16_t toSectorId,
        float maximumRange = 0.0f) const;
    bool partyAttackActorHasLineOfSight(size_t actorIndex) const;
    std::vector<IndoorActorCollision> actorMovementCollidersForActorMovement(
        const std::vector<size_t> &activeActorIndices) const;
    std::vector<IndoorActorCollision> actorMovementCollidersForPartyMovement() const;
    std::vector<IndoorCylinderCollision> decorationMovementColliders() const;
    std::vector<IndoorCylinderCollision> spriteObjectMovementColliders() const;

    // The monsters' walk map; null until it is built. After a door moves it is the previous map until the rebuild
    // off the main thread lands.
    std::shared_ptr<const PathMap> indoorPathMap() const;
    // The walk map as the geometry stands now (the scenarios' walk_to plans the party's route on it): a rebuild in
    // flight is waited for, and a map changed since is built at once.
    std::shared_ptr<const PathMap> currentIndoorPathMap();

private:
    // Whether a door is shut (closed or closing: MM9's IsClosed), from its runtime mechanism state.
    bool indoorDoorShut(uint32_t doorId) const;
    // The scene's `ai_open` doors that are not shut: their faces stand in the monsters' walk map.
    std::vector<uint32_t> openIndoorAiDoorIds() const;
    std::string mapWorldId() const;
    const ActorRulesetFacts &actorRulesetFacts(size_t actorIndex) const;
    // Homing for the missiles a party member just fired at an actor, when the rules make them home (MAW).
    // The ruleset's homing (MAW), or a weapon's (weaponHoming: an Energy Guns Grandmaster's shot, 360 degrees a second
    // for 1.5 s).
    void attachPartyMissileHoming(
        uint32_t firstProjectileId,
        uint32_t sourcePartyMemberIndex,
        std::optional<size_t> targetActorIndex,
        bool weaponHoming = false);
    // The ruleset's map-wide choices when the map's monsters are first placed (MAW bosses).
    void placeRulesetMapMonsters();
    void refreshRulesetMonster(size_t actorIndex);
    // After a kill: the ruleset's reward for clearing the map, if it has one.
    void rewardRulesetMapProgress();
    MonsterKillReward killReward(
        const MapDeltaActor &actor,
        const MapActorAiState &aiState,
        const MonsterTable::MonsterStatsEntry &stats) const;
    // A summon (ally 999), controlled undead or a reanimated monster.
    static bool actorFightsForParty(const MapDeltaActor &actor, const MapActorAiState &aiState);
    // The party is about to slay this actor (MAW's bounty reads who killed its target).
    void markActorKilledByParty(size_t actorIndex);
    // A monster slain by another: the rules' reward when the killer fights for the party.
    void rewardKillByActor(size_t victimIndex, uint32_t sourceActorId);
    // A hit on an MM9 walker (ActorMm9WorldFacts): its attacker (the party, or the actor at attackerActorIndex), the
    // largest hit and the count its AI reacts to. Nothing for any other actor.
    void noteMm9ActorHit(size_t actorIndex, ActorAiTargetKind attackerKind, size_t attackerActorIndex, int damage);
    // The world's Mm9PartyAwareness (the actor service's, MM9's rules without one).
    const Mm9PartyAwareness &mm9PartyAwareness() const;
    // A provoking party hit on an MM9 loop monster: it and its awake friends within the provoke radius that it sees
    // hold the party (MM9_MONSTER_AI_PLAN.md "Awareness of the party").
    void provokeMm9Actors(size_t actorIndex);
    size_t actorIndexForActorId(uint32_t actorId) const;
    bool summonEventPayload(
        uint32_t payloadId,
        bool payloadIsObjectId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    );

    struct RuntimeGeometryCache
    {
        bool valid = false;
        std::vector<IndoorVertex> vertices;
        IndoorFaceGeometryCache geometryCache;
        bool pathMapValid = false;
        std::shared_ptr<const PathMap> pathMapSnapshot;
        // Counts the path map's invalidations: a rebuilt map launched before the latest one is out of date when it lands.
        uint64_t pathMapGeneration = 0;
        // Rebuilt only for a new map or restored map state, not on every invalidation.
        bool sectorFaceGridValid = false;
        IndoorSectorFaceGrid sectorFaceGrid;
    };

    struct IndoorActorAiPerformanceDiagnostics
    {
        uint64_t updateCalls = 0;
        uint64_t fixedSteps = 0;
        uint64_t totalNanoseconds = 0;
        uint64_t syncStateNanoseconds = 0;
        uint64_t activationNanoseconds = 0;
        uint64_t collectNanoseconds = 0;
        uint64_t selectActiveNanoseconds = 0;
        uint64_t activeSelectionLosNanoseconds = 0;
        uint64_t actorFactNanoseconds = 0;
        uint64_t aiSystemNanoseconds = 0;
        uint64_t applyNanoseconds = 0;
        uint64_t colliderNanoseconds = 0;
        uint64_t movementIntegrationNanoseconds = 0;
        uint64_t movementSetupNanoseconds = 0;
        uint64_t movementPathSetupNanoseconds = 0;
        uint64_t physicsStepNanoseconds = 0;
        uint64_t pathResolveNanoseconds = 0;
        uint64_t movementEventNanoseconds = 0;
        uint64_t resolveMoveNanoseconds = 0;
        uint64_t movementStateWriteNanoseconds = 0;
        uint64_t movementFactBuildNanoseconds = 0;
        uint64_t postMovementAiNanoseconds = 0;
        uint64_t postMovementApplyNanoseconds = 0;
        uint64_t spellEffectNanoseconds = 0;
        uint64_t actorCount = 0;
        uint64_t activatedActorCount = 0;
        uint64_t activeActorCount = 0;
        uint64_t backgroundActorCount = 0;
        uint64_t selectedActorCount = 0;
        uint64_t actorFactCandidates = 0;
        uint64_t actorFactsCollected = 0;
        uint64_t actorUpdates = 0;
        uint64_t movementIntegrations = 0;
        uint64_t physicsSteps = 0;
        uint64_t contactedActors = 0;
        uint64_t blockedMoves = 0;
        uint64_t activeSelectionLosChecks = 0;
        uint64_t pathResolveCalls = 0;
        uint64_t pathDirectChecks = 0;
        uint64_t pathPlans = 0;
        uint64_t pathQueued = 0;
        uint64_t pathActive = 0;
        uint64_t pathStopped = 0;
        uint64_t crowdOverrideActors = 0;
        uint64_t crowdStateUpdates = 0;
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
    struct LootGatherSpot
    {
        float x = 0.0f;
        float y = 0.0f;
        float footZ = 0.0f;
        int16_t sectorId = -1;
    };
    LootGatherSpot lootGatherSpot() const;
    float flyingFootZUnderCeiling(float x, float y, float aimZ, float footZ, float collisionHeight) const;
    void carryRestingObjectsOnMovedFloors(const std::vector<std::pair<const MapDeltaDoor *, float>> &floorMoves);
    bool indoorActorPathfindingEnabled() const;
    // The painted map the minimap and journal map draw, or null for the line map (the Map style setting).
    const MapPresentation *activeMapPresentation() const;
    bool logIndoorPathfindingEnabled() const;
    bool actorAiPerformanceDiagnosticsEnabled() const;
    void logActorAiPerformanceDiagnostics(uint32_t currentTick);
    IndoorMovementController &actorMovementController();
    // Scene water volumes: their tops now, and the swimmers' volumes (MapActorAiState::waterVolumeIndex).
    void refreshActorWaterVolumes();
    void ensureIndoorSectorActivationMask();
    void activateIndoorSector(int16_t sectorId);
    void refreshActivatedIndoorSectors();
    bool indoorSectorActivated(int16_t sectorId) const;
    bool indoorActorSectorActivated(const MapDeltaActor &actor, const MapActorAiState *pAiState) const;
    std::vector<bool> selectIndoorActiveActors(
        const ActorPartyFacts &partyFacts,
        int16_t partySectorId,
        const std::vector<IndoorVertex> &vertices,
        IndoorActorAiPerformanceDiagnostics *pDiagnostics = nullptr);
    ActorAiFrameFacts collectIndoorActorAiFrameFacts(
        float deltaSeconds,
        IndoorActorAiPerformanceDiagnostics *pDiagnostics = nullptr);
    std::vector<bool> applyIndoorActorAiFrameResult(
        const ActorAiFrameResult &result,
        const GameplayActorAiSystem &actorAiSystem,
        IndoorActorAiPerformanceDiagnostics *pDiagnostics = nullptr);
    void applyActorSpawnRequests(const std::vector<ActorSpawnRequest> &spawnRequests);
    // The MM9 layers' requests (MM9_MONSTER_AI_PLAN.md phase 4a): calls to friends, resurrection, doors.
    void applyMm9Requests(const ActorAiFrameResult &result);
    void deliverMm9Call(size_t senderIndex, const ActorMm9Request &request, const std::vector<uint8_t> &active);
    void answerMm9ResurrectionAsk(size_t corpseIndex, const std::vector<uint8_t> &active);
    void answerMm9ChatSearch(size_t actorIndex, const std::vector<uint8_t> &active, std::vector<uint8_t> &claimed);
    void collectIndoorMm9ChatFacts(size_t actorIndex, ActorMm9WorldFacts &world) const;
    void reviveMm9Actor(size_t actorIndex);
    void openMm9Door(size_t actorIndex, uint32_t doorId);
    // The reposition modifier's query (ActorMm9Request::reposition): the first of its spots that passes, answered in
    // the actor's ActorMm9WorldFacts (repositionSerial).
    void answerRepositionQuery(size_t actorIndex, const ActorRepositionQuery &query);
    void collectIndoorMm9LayerFacts(size_t actorIndex, const ActorPartyFacts &partyFacts, ActorAiFacts &facts) const;
    bool mm9ActorsAreEnemies(size_t actorIndex, size_t otherActorIndex) const;
    std::optional<Mm9AiProfile> mm9ActorProfile(size_t actorIndex) const;
    void collectIndoorMm9Refuges(size_t actorIndex, ActorMm9WorldFacts &world) const;
    void applyIndoorActorMovementIntegration(
        IndoorMovementController &movementController,
        size_t actorIndex,
        const ActorAiUpdate &update,
        const GameplayActorAiSystem &actorAiSystem,
        IndoorActorAiPerformanceDiagnostics *pDiagnostics = nullptr);
    bool recoverInvalidIndoorActorPosition(
        size_t actorIndex,
        const IndoorBodyDimensions &body,
        IndoorMoveState &state,
        bool allowNearestFloorCenter,
        const IndoorMovementController &movementController);
    bool actorNeedsIndoorPositionRecovery(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body,
        bool actorCanFly) const;
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
    void populateIndoorProjectileAreaImpact(
        const GameplayProjectileService::ProjectileState &projectile,
        const GameplayProjectileService::ProjectileFrameFacts &facts,
        GameplayProjectileService::ProjectileFrameResult &frameResult) const;
    void applyIndoorProjectileFrameResult(
        GameplayProjectileService::ProjectileState &projectile,
        const GameplayProjectileService::ProjectileFrameFacts &facts,
        const GameplayProjectileService::ProjectileFrameResult &frameResult);
    void spawnIndoorDeathBlossomFallout(
        const GameplayProjectileService::ProjectileState &projectile,
        const GameplayWorldPoint &point);
    void updateIndoorProjectiles(float deltaSeconds);
    void updateFireSpikeTraps(float deltaSeconds);
    // Armageddon on a map open to the sky (game/gameplay/ArmageddonSpell.h): the quake, its meteors and strikes, then
    // the damage to every monster on the map and to the party.
    void updateArmageddon(float deltaSeconds);
    void resolveArmageddonDetonation(const GameplayWorldPoint &partyFeet);
    void applyFireSpikeTrapTriggerResult(
        FireSpikeTrapState &trap,
        const GameplayProjectileService::FireSpikeTrapTriggerResult &result);
    void updateImmolation(float deltaSeconds);
    void updateWorldItems(float deltaSeconds);
    bool updateWorldItemsStep(
        float deltaSeconds,
        const std::vector<IndoorVertex> &vertices,
        IndoorFaceGeometryCache &geometryCache);
    // Each patrolling actor's place in its round (MapDeltaActor::patrolPoints); advanced as the AI facts are read, not
    // saved (a load starts the round at its first waypoint).
    mutable std::unordered_map<size_t, size_t> m_actorPatrolIndices;
    std::optional<ActorAiFacts> collectIndoorActorAiFacts(
        size_t actorIndex,
        bool active,
        const ActorPartyFacts &partyFacts,
        const std::vector<IndoorVertex> &vertices,
        IndoorFaceGeometryCache &geometryCache,
        const std::vector<uint8_t> &spellEffectOverrideMask
    ) const;
    std::optional<GameplayMonsterBolsterResult> resolveActorBolster(const MapDeltaActor &actor) const;
    bool indoorActorCanApplyPartyMeleeImpact(size_t actorIndex) const;
    void materializeSemanticWorldItems();
    void dropRestingWorldItemsToFloor();
    void synchronizeSemanticWorldItemVisibility();
    // A scene's placed world item the party took: recorded, its quest bits set, its pickup event run.
    void onPlacedWorldItemTaken(const std::string &sourceId);
    bool activateSemanticLootContainer(size_t worldItemIndex);
    void removeDepletedSemanticLootContainer(uint32_t containerId);
    ChestViewState buildChestView(uint32_t chestId) const;
    void activateChestView(uint32_t chestId);
    bool attemptOpenChest(uint32_t chestId, bool openedByTelekinesis = false);
    GameplayWorldPoint chestTrapSourcePoint() const;
    GameplayWorldPoint chestTrapVisualPoint(const GameplayWorldPoint &sourcePoint) const;
    void applyChestTrapState(uint32_t chestId, const ChestTrapOpenResult &trapResult);
    // The impact of object objectId at point, with the fireball's sound: a chest trap or a monster's death blast.
    void spawnObjectBurstVisual(const GameplayWorldPoint &point, uint16_t objectId, CombatDamageType damageType);
    bool applyActorMeleeAttackToMapActor(size_t sourceActorIndex, const ActorAttackRequest &attackRequest);
    int applyMonsterDamageEventHooks(
        size_t actorIndex,
        int16_t monsterId,
        int damage,
        CombatDamageType damageType,
        bool byParty);
    void notifyMonsterKilledEventHooks(size_t actorIndex, int16_t monsterId);
    int effectiveIndoorActorArmorClass(
        size_t actorIndex,
        const MapDeltaActor &actor,
        const MonsterTable::MonsterStatsEntry &stats) const;
    void pushIndoorMonsterSound(size_t actorIndex, uint32_t soundId);
    void beginMapActorHitReaction(
        size_t actorIndex,
        MapDeltaActor &actor,
        const GameplayWorldPoint *pSource,
        bool force = false);
    void beginMapActorDyingState(size_t actorIndex, MapDeltaActor &actor);
    // Damage from a monster's splash or blast (not the party's): shields, event hooks, death and a kill reward for
    // sourceActorId when it is an actor.
    void applyNonPartyAreaDamageToActor(
        size_t actorIndex,
        int damage,
        CombatDamageType damageType,
        ShieldAttackTier shieldTier,
        const GameplayWorldPoint &sourcePoint,
        std::optional<uint32_t> killerActorId);
    void detonatePendingDeathExplosions();
    void spawnMonsterDeathDropsForActor(size_t actorIndex, const MapDeltaActor &actor);
    bool spawnMonsterDeathDropItem(
        const InventoryItem &item,
        float x,
        float y,
        float z,
        int16_t sectorId,
        uint32_t seed);
    void activateIndoorActorCorpsePhysics(size_t actorIndex);
    void applyIndoorActorCorpsePhysicsSteps(
        IndoorMovementController &movementController,
        const std::vector<uint8_t> &actorPhysicsApplied,
        IndoorActorAiPerformanceDiagnostics *pDiagnostics = nullptr);
    bool applyIndoorActorPhysicsStep(IndoorMovementController &movementController, size_t actorIndex);
    std::optional<GameplayWorldPoint> actorImpactPoint(size_t actorIndex) const;
    bool spawnIndoorProjectileImpactVisual(
        const GameplayProjectileService::ProjectileState &projectile,
        const GameplayWorldPoint &point,
        bool centerVertically,
        size_t targetActorIndex = static_cast<size_t>(-1));
    bool spawnIndoorWaterSplashImpactVisual(const GameplayWorldPoint &point);
    bool spawnImmediateSpellImpactVisualAt(
        const GameplayWorldPoint &point,
        uint32_t spellId,
        bool centerVertically = false,
        bool preferImpactObject = true,
        size_t targetActorIndex = static_cast<size_t>(-1));
    void spawnImmediateSpellImpactVisual(size_t actorIndex, uint32_t spellId);
    void updateIndoorJournalRevealIfNeeded();
    void setMapActorHostilityFromEvent(size_t actorIndex, bool hostileToParty);
    void alertMapActorToParty(size_t actorIndex);
    void updateYellFleeing(float deltaSeconds);
    // Energy shields: regeneration and presentation per actor step, and the QBit-switched relations of the world
    // add-on (MonsterRelationAddOns) applied to the map's actors whenever they change and after every load.
    void updateActorShields(float deltaSeconds);
    void refreshConditionalMonsterRelations();
    // A hit through the actor's shield (GameplayActorShields::applyHit), the ripple at the source's side of the body.
    GameplayActorShieldHit applyActorShieldHit(size_t actorIndex, int damage, ShieldAttackTier shieldTier,
        const GameplayWorldPoint &source, const ShieldHitModifiers &shieldModifiers = {});
    // Monster modifiers (MonsterModifiers): blinks per actor step, a true_aim monster's shots, never_staggers.
    void updateActorModifiers(float deltaSeconds);
    bool blinkMapActor(const GameplayActorModifiers::BlinkRequest &request);
    // Charges (GameplayActorModifiers) per fixed actor step after the AI, and what a charge does in this world.
    void updateActorCharges(float deltaSeconds);
    GameplayActorModifiers::ChargeWorld chargeWorld();
    GameplayActorModifiers::ChargeActorFacts chargeActorFacts(size_t actorIndex) const;
    void handleChargeEvent(const GameplayActorModifiers::ChargeEvent &event);
    // A monster's missile homes: a true_aim monster's at its target, the rules' cone at the party (MAW).
    void attachTrueAim(uint32_t firstProjectileId, const MapActorAiState &source, ActorAiTargetKind targetKind,
        size_t targetActorIndex, uint32_t spellId);
    // One step of a homing projectile toward its target's current position; true when it is to expire.
    bool steerIndoorHomingProjectile(GameplayProjectileService::ProjectileState &projectile, float deltaSeconds);
    bool monsterNeverStaggers(int16_t monsterId) const;
    // The original game drops a monster's Meteor Shower indoors: only a monster with the indoor_meteor_shower
    // modifier keeps it castable here, so the others pick another attack. A map open to the sky (isOpenAirMap) keeps
    // every monster's.
    void applyIndoorMeteorShowerRule(ActorAiFrameFacts &facts) const;
    // A party hit on the actor alerts its faction within 4096 (MM8 0x439278); friendly actors only when
    // alertsFriendlyActors (the victim was friendly or angered by the party).
    void aggroNearbyMapActorFaction(size_t actorIndex, bool alertsFriendlyActors);
    // Up to a few unaware hostile actors near this one, which they can see, become aware of the party.
    void wakeIndoorActorNeighbours(size_t actorIndex);
    void initializeMm9Barrels();
    // Scene destructibles (devdocs/INDOOR_DESTRUCTIBLES.md): their saved state, a destroyed one's faces and prop gone.
    void initializeIndoorDestructibles();
    const IndoorDestructible *indoorDestructible(uint32_t id) const;
    const IndoorDestructible *indoorDestructibleOfFace(size_t faceIndex) const;
    const IndoorDestructible *indoorDestructibleOfEntity(size_t entityIndex) const;
    bool indoorDestructibleTakesDamage(const IndoorDestructible *pDestructible) const;
    RuntimeDestructibleState *indoorDestructibleState(const IndoorDestructible &destructible);
    void hideIndoorDestructible(const IndoorDestructible &destructible);
    // Whether a decoration of this SetSprite key carries a light (unknown: true).
    bool indoorDecorationCogCarriesLight(uint16_t cog) const;
    bool destroyIndoorDestructible(const IndoorDestructible &destructible);
    bool damageIndoorDestructible(const IndoorDestructible &destructible, int damage);
    // The standing destructibles that take damage, by their boxes, for an area impact; the one whose face or prop the
    // missile struck is marked direct.
    std::vector<GameplayProjectileService::ProjectileAreaImpactDestructibleFacts> collectIndoorAreaDestructibles(
        size_t directFaceIndex,
        size_t directEntityIndex) const;
    void runPendingDestructibleEvents();
    // evt.MoveActorTo arrivals (EventRuntimeState::pendingActorArrivals): their events, each with its actor.
    void runPendingScriptedActorArrivals();
    // MM9's FoundPlayer greetings (RUDE event 56000 + the source object index, as outdoors): a living, visible person
    // with RUDE dialogue who perceives the party (mm9Perceives: its placement's sight in front, hearing all round, a
    // clear line; searched once a second) runs it once per visit.
    void updateMm9FoundPlayerEvents(float deltaSeconds);
    void applyMm9BarrelVisual(const MapMm9BarrelSource &source, const MapDeltaMm9BarrelState &state);

    std::optional<MapStatsEntry> m_map;
    const MonsterTable *m_pMonsterTable = nullptr;
    const MergedBolsterMapTable *m_pMergedBolsterMapTable = nullptr;
    const MergedBolsterMonsterTable *m_pMergedBolsterMonsterTable = nullptr;
    const MonsterProjectileTable *m_pMonsterProjectileTable = nullptr;
    const ObjectTable *m_pObjectTable = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    const ItemTable *m_pItemTable = nullptr;
    const ChestTable *m_pChestTable = nullptr;
    MapItemSourceData m_itemSourceData;
    SearchableLootPropState m_searchableLootPropState;
    const SpriteFrameTable *m_pActorSpriteFrameTable = nullptr;
    const SpriteFrameTable *m_pProjectileSpriteFrameTable = nullptr;
    const IndoorMapData *m_pIndoorMapData = nullptr;
    const DecorationBillboardSet *m_pIndoorDecorationBillboardSet = nullptr;
    std::vector<DecorationClearRule> m_decorationClearRules;
    // The map is still taking its first fill (MAW Nightmare revival raises only that roster).
    bool m_firstFillOpen = false;
    bool m_bolsterMonstersEnabled = false;
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
    // Frame-sized increments must remain representable after months of campaign time.
    double m_gameMinutes = 9.0 * 60.0;
    int m_currentLocationReputation = 0;
    uint32_t m_sessionChestSeed = 0;
    std::vector<std::optional<ChestViewState>> m_materializedChestViews;
    std::optional<ChestViewState> m_activeChestView;
    std::optional<GameplayWorldPoint> m_pendingEventSourcePoint;
    // Destructibles' destroyed and damaged events, run by the next world update (a destruction inside a running event
    // never runs another event inside it).
    std::vector<uint16_t> m_pendingDestructibleEvents;
    // The destructible props' hit cylinders (each decoration of a destructible's decoration cog), which party and
    // event missiles strike, and each scene destructible's box (its faces and props; aligned with
    // IndoorMapData::destructibles; min above max: none) for area impacts. Built by initializeIndoorDestructibles.
    struct DestructiblePropCollider
    {
        size_t entityIndex = 0;
        size_t destructibleIndex = 0;
        GameplayWorldPoint base = {};
        float radius = 0.0f;
        float height = 0.0f;
    };
    std::vector<DestructiblePropCollider> m_destructiblePropColliders;
    std::vector<std::array<GameplayWorldPoint, 2>> m_destructibleBounds;
    // Per map actor: its FoundPlayer greeting has run this visit; and the time since the last check.
    std::vector<bool> m_mm9FoundPlayerDone;
    float m_mm9FoundPlayerAccumulatorSeconds = 0.0f;
    std::vector<std::optional<CorpseViewState>> m_mapActorCorpseViews;
    // Gold and random item that Telepathy rolled for a living actor; its corpse takes them at death.
    std::vector<std::optional<CorpseViewState>> m_mapActorRevealedLoot;
    bool m_corpseLootPending = false;
    std::optional<CorpseViewState> m_activeCorpseView;
    std::vector<MapActorAiState> m_mapActorAiStates;
    // Each scene water volume's top offset this AI frame (empty on a map without water volumes).
    std::vector<float> m_waterTopOffsets;
    // Villagers still fleeing a yell (yellFleeRemainingSeconds > 0).
    std::vector<size_t> m_yellFleeingActorIndices;
    ActorTurnBasedFrameFacts m_turnBasedActorFacts = {};
    ActorBehaviorRuntime m_actorBehaviors;
    // The AI arena's decision trace (GameApplication owns it), null while off.
    ActorAiTrace *m_pActorAiTrace = nullptr;
    ActorPartyVelocityTracker m_actorAiPartyVelocity;
    GameplayActorHitFeedback m_actorHitFeedback;
    GameplayActorShields m_actorShields;
    GameplayActorModifiers m_actorModifiers;
    // MonsterRelationAddOns::revision() last applied to the actors; UINT64_MAX after a load.
    uint64_t m_appliedRelationRevision = UINT64_MAX;
    std::vector<size_t> m_actorCorpsePhysicsActorIndices;
    mutable ActorInspectPreviewAnimation m_actorInspectPreviewAnimation = {};
    std::vector<uint8_t> m_activatedIndoorSectorMask;
    // Advances once per active-actor selection; spreads the unaware actors' sight checks across AI steps.
    uint32_t m_indoorActorSightCheckStep = 0;
    std::vector<BloodSplatState> m_bloodSplats;
    uint64_t m_bloodSplatRevision = 0;
    float m_actorUpdateAccumulatorSeconds = 0.0f;
    float m_projectileUpdateAccumulatorSeconds = 0.0f;
    float m_worldItemUpdateAccumulatorSeconds = 0.0f;
    // The party's quest-bit revision the placed world items' visibility was last evaluated at.
    uint64_t m_placedWorldItemRevision = 0;
    float m_immolationTickAccumulatorGameMinutes = 0.0f;
    uint32_t m_immolationTickSequence = 0;
    bool m_scenarioPartyActorCollisionEnabled = true;
    bool m_indoorJournalRevealStateValid = false;
    int16_t m_lastIndoorJournalRevealSectorId = -1;
    int16_t m_lastIndoorJournalRevealEyeSectorId = -1;
    uint64_t m_lastIndoorJournalRevealSurfaceRevision = 0;
    uint64_t m_lastIndoorJournalRevealVisibilityRevision = 0;
    uint64_t m_indoorMinimapRevealRevision = 0;
    // Per sector: some of its faces are drawn on the automap. Rebuilt only when the reveal pass maps something new;
    // Wizard Eye shows the actors standing in these sectors.
    std::vector<bool> m_indoorDiscoveredSectors;
    // Deaths of exploding monsters, detonated on the next actor update (MonsterDeathExplosion.h).
    std::vector<PendingMonsterDeathExplosion> m_pendingDeathExplosions;
    size_t m_lastIndoorJournalRevealFaceCount = 0;
    size_t m_lastIndoorJournalRevealOutlineCount = 0;
    std::vector<FireSpikeTrapState> m_fireSpikeTraps;
    ArmageddonState m_armageddonState = {};
    mutable RuntimeGeometryCache m_runtimeGeometryCache;
    // The monsters' path map rebuilt off the main thread after a door settles or a wall breaks (indoorPathMap): until it
    // lands the monsters keep the previous map. Region-sized maps took 50-250 ms on the main thread (2026-11-05).
    struct PendingPathMap
    {
        std::future<std::shared_ptr<PathMap>> map;
        uint64_t generation = 0;
    };
    mutable PendingPathMap m_pendingPathMap;
    std::optional<IndoorMovementController> m_actorMovementController;
    ActorPathRuntime m_actorPathRuntime;
    double m_actorPathRuntimeSeconds = 0.0;
    size_t m_actorPathPlansThisStep = 0;
    double m_nextPositionRecoveryBatchSeconds = 0.0;
    bool m_positionRecoveryBatchActive = false;
    IndoorActorAiPerformanceDiagnostics m_actorAiPerformanceDiagnostics;
    uint32_t m_lastActorAiPerformanceLogTick = 0;
    bool m_cachedGameplayMinimapLinesValid = false;
    uint64_t m_cachedGameplayMinimapLineSignature = 0;
    std::vector<GameplayMinimapLineState> m_cachedGameplayMinimapLines;
    std::vector<GameplayCombatFeedbackEvent> m_combatFeedbackEvents;
};
}
