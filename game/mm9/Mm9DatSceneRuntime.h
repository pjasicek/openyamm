#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/mm9/Mm9AnimatedActorVisual.h"
#include "game/mm9/Mm9DatPartyRuntime.h"
#include "game/mm9/Mm9DatWorldRenderer.h"
#include "game/render/AnimatedModelRenderer.h"
#include "game/scene/IMapSceneRuntime.h"

#include <memory>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9DialoguePackage;
struct Mm9ScriptRuntimeState;

class Mm9DatWorldGameplayRuntime : public IGameplayWorldRuntime
{
public:
    Mm9DatWorldGameplayRuntime(
        std::string mapFileName,
        Mm9DatRuntimeDevEntryResult entry,
        Party *pParty,
        EventRuntimeState *pEventRuntimeState,
        const std::optional<ScriptedEventProgram> *pGlobalEventProgram,
        Mm9ScriptRuntimeState *pMm9ScriptRuntimeState = nullptr,
        const Mm9DialoguePackage *pMm9DialoguePackage = nullptr,
        float gameMinutes = 0.0f);
    ~Mm9DatWorldGameplayRuntime() override;

    const std::string &mapName() const override;
    std::string currentMapWorldId() const override;
    bool isIndoorMap() const override;
    float gameMinutes() const override;
    int currentHour() const override;
    const std::vector<uint8_t> *journalMapFullyRevealedCells() const override;
    const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const override;
    int restFoodRequired() const override;
    void advanceGameMinutes(float minutes) override;
    int currentLocationReputation() const override;
    void setCurrentLocationReputation(int reputation) override;
    Party *party() override;
    const Party *party() const override;
    float partyX() const override;
    float partyY() const override;
    float partyFootZ() const override;
    float gameplayCameraYawRadians() const override;
    float gameplayCameraPitchRadians() const override;
    void syncSpellMovementStatesFromPartyBuffs() override;
    void requestPartyJump(float verticalVelocity = 0.0f, float lift = 1.0f) override;
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
    bool executeNpcTopicEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override;
    bool executeMapEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override;
    const std::optional<ScriptedEventProgram> *globalEventProgram() const override;
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
        int32_t toZ) override;
    size_t mapActorCount() const override;
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
    bool teleportPartyTo(float x, float y, float z, int32_t directionDegrees) override;
    bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        std::string &failureText) override;
    bool canActivateWorldHit(
        const GameplayWorldHit &hit,
        GameplayInteractionMethod interactionMethod) const override;
    bool activateWorldHit(const GameplayWorldHit &hit) override;
    bool canActivateTelekinesisTarget(const GameplayWorldHit &hit) const override;
    bool activateTelekinesisTarget(const GameplayWorldHit &hit) override;
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
    GameplayChestViewState *activeChestView() override;
    const GameplayChestViewState *activeChestView() const override;
    void commitActiveChestView() override;
    bool takeActiveChestItem(size_t itemIndex, GameplayChestItemState &item) override;
    bool takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, GameplayChestItemState &item) override;
    bool tryPlaceActiveChestItemAt(const GameplayChestItemState &item, uint8_t gridX, uint8_t gridY) override;
    void closeActiveChestView() override;
    GameplayCorpseViewState *activeCorpseView() override;
    const GameplayCorpseViewState *activeCorpseView() const override;
    void commitActiveCorpseView() override;
    bool takeActiveCorpseItem(size_t itemIndex, GameplayChestItemState &item) override;
    void closeActiveCorpseView() override;

    Mm9DatWorldRuntime &datRuntime();
    const Mm9DatWorldRuntime &datRuntime() const;
    Mm9DatPartyRuntimeState &partyRuntimeState();
    const Mm9DatPartyRuntimeState &partyRuntimeState() const;
    const std::optional<Mm9DatPartyRuntimeMoveResult> &lastMoveResult() const;
    const std::optional<Mm9DatWorldUseResult> &lastUseResult() const;
    std::vector<std::string> debugStatusLines() const;

private:
    struct Mm9DatAnimatedObjectTextureHandle
    {
        std::string textureName;
        bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
        int width = 0;
        int height = 0;
    };

    struct Mm9DatAnimatedObjectInstance
    {
        Mm9AnimatedActorVisual visual;
        std::shared_ptr<AnimatedModelAsset> asset;
    };

    bool initializeRenderResources();
    void destroyRenderResources();
    void markDynamicRenderUploadDirty(const Mm9DatWorldRuntimeUpdateStats &stats);
    void markDynamicRenderUploadDirty(const Mm9DatWorldUseResult &result);
    bool refreshDynamicRenderUploadIfNeeded();
    void initializeAnimatedObjectInstances();
    void updateAnimatedObjectInstances(float deltaSeconds);
    void submitAnimatedObjectInstances();
    const Mm9DatAnimatedObjectTextureHandle *ensureAnimatedObjectTexture(
        const std::string &textureName);

    std::string m_mapFileName;
    Mm9DatRuntimeDevEntryResult m_entry;
    Party *m_pParty = nullptr;
    EventRuntimeState *m_pEventRuntimeState = nullptr;
    const std::optional<ScriptedEventProgram> *m_pGlobalEventProgram = nullptr;
    Mm9ScriptRuntimeState *m_pMm9ScriptRuntimeState = nullptr;
    const Mm9DialoguePackage *m_pMm9DialoguePackage = nullptr;
    Mm9DatPartyRuntimeState m_partyState;
    std::optional<Mm9DatPartyRuntimeMoveResult> m_lastMoveResult;
    std::optional<Mm9DatWorldUseResult> m_lastUseResult;
    float m_gameMinutes = 0.0f;
    int m_currentLocationReputation = 0;
    bool m_alwaysRun = false;
    bool m_worldAdvancedSinceLastUpdateWorld = false;
    bool m_renderResourcesInitialized = false;
    Mm9DatWorldRenderUploadPlan m_renderUploadPlan;
    Mm9DatWorldGeometryResources m_geometryResources;
    Mm9DatWorldTextureResources m_textureResources;
    Mm9DatWorldRenderSubmitPlan m_renderSubmitPlan;
    Mm9DatWorldRenderSubmitPlanStats m_lastRenderSubmitStats;
    AnimatedModelRenderResources m_animatedModelRenderResources;
    std::vector<Mm9DatAnimatedObjectInstance> m_animatedObjectInstances;
    std::vector<Mm9DatAnimatedObjectTextureHandle> m_animatedObjectTextureHandles;
    std::unordered_map<std::string, size_t> m_animatedObjectTextureIndexByName;
    bool m_dynamicRenderUploadDirty = true;
    bool m_animatedObjectInstancesInitialized = false;
    bgfx::ProgramHandle m_renderProgramHandle = BGFX_INVALID_HANDLE;
    bgfx::UniformHandle m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    GameplayHoverStatusPayload m_cachedHoverPayload;
    GameplayWorldHoverCacheState m_hoverCacheState;
};

class Mm9DatSceneRuntime : public IMapSceneRuntime
{
public:
    Mm9DatSceneRuntime(
        const std::string &mapFileName,
        Mm9DatRuntimeDevEntryResult entry,
        Party party,
        float gameMinutes = 0.0f,
        Mm9ScriptRuntimeState *pMm9ScriptRuntimeState = nullptr,
        const Mm9DialoguePackage *pMm9DialoguePackage = nullptr);

    SceneKind kind() const override;
    const std::string &currentMapFileName() const override;
    Party &party() override;
    const Party &party() const override;
    EventRuntimeState *eventRuntimeState() override;
    const EventRuntimeState *eventRuntimeState() const override;
    ISceneEventContext *sceneEventContext() override;
    const std::optional<ScriptedEventProgram> &localEventProgram() const override;
    const std::optional<ScriptedEventProgram> &globalEventProgram() const override;
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove() override;
    void advanceGameMinutes(float minutes) override;

    Mm9DatWorldGameplayRuntime &worldRuntime();
    const Mm9DatWorldGameplayRuntime &worldRuntime() const;

private:
    std::string m_mapFileName;
    Party m_party;
    EventRuntimeState m_eventRuntimeState;
    std::optional<ScriptedEventProgram> m_localEventProgram;
    std::optional<ScriptedEventProgram> m_globalEventProgram;
    Mm9DatWorldGameplayRuntime m_worldRuntime;
};
}
