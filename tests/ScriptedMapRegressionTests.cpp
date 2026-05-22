#include "doctest/doctest.h"

#include "game/events/EventRuntime.h"
#include "game/events/EventDialogContent.h"
#include "game/events/ISceneEventContext.h"
#include "game/FaceEnums.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/maps/MapAssetLoader.h"
#include "game/StringUtils.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"

#include "tests/RegressionGameData.h"
#include "tests/RegressionMapLoader.h"

#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <filesystem>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{
class RecordingSceneEventContext : public OpenYAMM::Game::ISceneEventContext
{
public:
    struct CastSpellCall
    {
        uint32_t spellId = 0;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        int32_t fromX = 0;
        int32_t fromY = 0;
        int32_t fromZ = 0;
        int32_t toX = 0;
        int32_t toY = 0;
        int32_t toZ = 0;
    };

    struct SummonMonstersCall
    {
        uint32_t typeIndexInMapStats = 0;
        uint32_t level = 0;
        uint32_t count = 0;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
        uint32_t group = 0;
        uint32_t uniqueNameId = 0;
    };

    struct OutdoorModelMechanismCall
    {
        uint32_t mechanismId = 0;
        std::string modelName;
        int32_t dx = 0;
        int32_t dy = 0;
        int32_t dz = 0;
        uint32_t moveTimeMs = 0;
        bool closed = false;
        bool moveParty = false;
    };

    float currentGameMinutes() const override
    {
        return m_currentGameMinutes;
    }

    void setCurrentGameMinutes(float currentGameMinutes)
    {
        m_currentGameMinutes = currentGameMinutes;
    }

    const OpenYAMM::Game::MapDeltaData *mapDeltaData() const override
    {
        return nullptr;
    }

    OpenYAMM::Game::MapDeltaData *mapDeltaData() override
    {
        return nullptr;
    }

    bool setFacetBit(uint32_t cogNumber, uint32_t bit, bool isOn) override
    {
        (void)cogNumber;
        (void)bit;
        (void)isOn;
        return false;
    }

    std::vector<uint32_t> resolveIndoorLightReferenceIds(int32_t rawReferenceId) const override
    {
        if (pIndoorMapData == nullptr)
        {
            return {};
        }

        return OpenYAMM::Game::resolveIndoorLightReferenceIds(*pIndoorMapData, rawReferenceId);
    }

    bool registerOutdoorModelMechanism(
        uint32_t mechanismId,
        const std::string &modelName,
        int32_t dx,
        int32_t dy,
        int32_t dz,
        uint32_t moveTimeMs,
        bool closed,
        bool moveParty) override
    {
        outdoorModelMechanismCalls.push_back({
            mechanismId,
            modelName,
            dx,
            dy,
            dz,
            moveTimeMs,
            closed,
            moveParty});
        return true;
    }

    bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ) override
    {
        CastSpellCall call = {};
        call.spellId = spellId;
        call.skillLevel = skillLevel;
        call.skillMastery = skillMastery;
        call.fromX = fromX;
        call.fromY = fromY;
        call.fromZ = fromZ;
        call.toX = toX;
        call.toY = toY;
        call.toZ = toZ;
        castSpellCalls.push_back(call);
        return true;
    }

    bool summonMonsters(
        uint32_t typeIndexInMapStats,
        uint32_t level,
        uint32_t count,
        int32_t x,
        int32_t y,
        int32_t z,
        uint32_t group,
        uint32_t uniqueNameId) override
    {
        summonMonstersCalls.push_back({
            typeIndexInMapStats,
            level,
            count,
            x,
            y,
            z,
            group,
            uniqueNameId});
        return true;
    }

    bool summonEventItem(
        uint32_t itemId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate) override
    {
        (void)itemId;
        (void)x;
        (void)y;
        (void)z;
        (void)speed;
        (void)count;
        (void)randomRotate;
        return false;
    }

    bool checkMonstersKilled(uint32_t checkType, uint32_t id, uint32_t count, bool invisibleAsDead) const override
    {
        (void)checkType;
        (void)count;
        (void)invisibleAsDead;

        const std::unordered_map<uint32_t, bool>::const_iterator iterator = killedGroupResults.find(id);
        return iterator != killedGroupResults.end() ? iterator->second : false;
    }

    std::vector<CastSpellCall> castSpellCalls;
    std::vector<SummonMonstersCall> summonMonstersCalls;
    std::vector<OutdoorModelMechanismCall> outdoorModelMechanismCalls;
    std::unordered_map<uint32_t, bool> killedGroupResults;
    const OpenYAMM::Game::IndoorMapData *pIndoorMapData = nullptr;

private:
    float m_currentGameMinutes = 0.0f;
};

class RecordingGameplayWorldContext : public RecordingSceneEventContext, public OpenYAMM::Game::IGameplayWorldRuntime
{
public:
    void setPartyPosition(float x, float y, float z)
    {
        m_partyX = x;
        m_partyY = y;
        m_partyZ = z;
    }

    void setIndoorMap(bool indoorMap)
    {
        m_indoorMap = indoorMap;
    }

    void setPartyFlyingForEventChecks(bool flying)
    {
        m_partyFlyingForEventChecks = flying;
    }

    const std::string &mapName() const override
    {
        return m_mapName;
    }

    bool isIndoorMap() const override
    {
        return m_indoorMap;
    }

    float gameMinutes() const override
    {
        return currentGameMinutes();
    }

    int currentHour() const override
    {
        return 0;
    }

    const std::vector<uint8_t> *journalMapFullyRevealedCells() const override
    {
        return nullptr;
    }

    const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const override
    {
        return nullptr;
    }

    int restFoodRequired() const override
    {
        return 0;
    }

    void advanceGameMinutes(float minutes) override
    {
        setCurrentGameMinutes(currentGameMinutes() + minutes);
    }

    int currentLocationReputation() const override
    {
        return 0;
    }

    void setCurrentLocationReputation(int reputation) override
    {
        (void)reputation;
    }

    OpenYAMM::Game::Party *party() override
    {
        return &m_party;
    }

    const OpenYAMM::Game::Party *party() const override
    {
        return &m_party;
    }

    float partyX() const override
    {
        return m_partyX;
    }

    float partyY() const override
    {
        return m_partyY;
    }

    float partyFootZ() const override
    {
        return m_partyZ;
    }

    bool partyIsFlyingForEventChecks() const override
    {
        return m_partyFlyingForEventChecks;
    }

    void syncSpellMovementStatesFromPartyBuffs() override
    {
    }

    void requestPartyJump(float verticalVelocity = 0.0f, float lift = 1.0f) override
    {
        (void)verticalVelocity;
        (void)lift;
    }

    void setAlwaysRunEnabled(bool enabled) override
    {
        (void)enabled;
    }

    void updateWorldMovement(
        const OpenYAMM::Game::GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput) override
    {
        (void)input;
        (void)deltaSeconds;
        (void)allowWorldInput;
    }

    void updateActorAi(float deltaSeconds) override
    {
        (void)deltaSeconds;
    }

    void updateWorld(float deltaSeconds) override
    {
        (void)deltaSeconds;
    }

    void renderWorld(
        int width,
        int height,
        const OpenYAMM::Game::GameplayInputFrame &input,
        float deltaSeconds) override
    {
        (void)width;
        (void)height;
        (void)input;
        (void)deltaSeconds;
    }

    OpenYAMM::Game::GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const override
    {
        (void)width;
        (void)height;
        return {};
    }

    bool requestTravelAutosave() override
    {
        return false;
    }

    void cancelPendingMapTransition() override
    {
    }

    bool executeNpcTopicEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override
    {
        (void)eventId;
        (void)previousMessageCount;
        (void)continueStep;
        return false;
    }

    bool executeMapEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override
    {
        (void)eventId;
        (void)previousMessageCount;
        (void)continueStep;
        return false;
    }

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> *globalEventProgram() const override
    {
        return nullptr;
    }

    OpenYAMM::Game::EventRuntimeState *eventRuntimeState() override
    {
        return nullptr;
    }

    const OpenYAMM::Game::EventRuntimeState *eventRuntimeState() const override
    {
        return nullptr;
    }

    bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ) override
    {
        return RecordingSceneEventContext::castEventSpell(
            spellId,
            skillLevel,
            skillMastery,
            fromX,
            fromY,
            fromZ,
            toX,
            toY,
            toZ);
    }

    size_t mapActorCount() const override
    {
        return 0;
    }

    bool actorRuntimeState(size_t actorIndex, OpenYAMM::Game::GameplayRuntimeActorState &state) const override
    {
        (void)actorIndex;
        (void)state;
        return false;
    }

    bool actorInspectState(
        size_t actorIndex,
        uint32_t animationTicks,
        OpenYAMM::Game::GameplayActorInspectState &state) const override
    {
        (void)actorIndex;
        (void)animationTicks;
        (void)state;
        return false;
    }

    std::optional<OpenYAMM::Game::GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const override
    {
        (void)actorId;
        return std::nullopt;
    }

    bool castPartySpellProjectile(const OpenYAMM::Game::GameplayPartySpellProjectileRequest &request) override
    {
        (void)request;
        return false;
    }

    bool applyPartySpellToActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        OpenYAMM::Game::SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex) override
    {
        (void)actorIndex;
        (void)spellId;
        (void)skillLevel;
        (void)skillMastery;
        (void)damage;
        (void)partyX;
        (void)partyY;
        (void)partyZ;
        (void)sourcePartyMemberIndex;
        return false;
    }

    std::vector<size_t> collectMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        bool requireLineOfSight,
        float sourceX,
        float sourceY,
        float sourceZ) const override
    {
        (void)centerX;
        (void)centerY;
        (void)centerZ;
        (void)radius;
        (void)requireLineOfSight;
        (void)sourceX;
        (void)sourceY;
        (void)sourceZ;
        return {};
    }

    bool spawnPartyFireSpikeTrap(
        uint32_t casterMemberIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        float x,
        float y,
        float z) override
    {
        (void)casterMemberIndex;
        (void)spellId;
        (void)skillLevel;
        (void)skillMastery;
        (void)x;
        (void)y;
        (void)z;
        return false;
    }

    bool summonFriendlyMonsterById(
        int16_t monsterId,
        uint32_t count,
        float durationSeconds,
        float x,
        float y,
        float z) override
    {
        (void)monsterId;
        (void)count;
        (void)durationSeconds;
        (void)x;
        (void)y;
        (void)z;
        return false;
    }

    bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        OpenYAMM::Game::SkillMastery skillMastery,
        std::string &failureText) override
    {
        (void)casterMemberIndex;
        (void)skillLevel;
        (void)skillMastery;
        failureText.clear();
        return false;
    }

    bool canActivateWorldHit(
        const OpenYAMM::Game::GameplayWorldHit &hit,
        OpenYAMM::Game::GameplayInteractionMethod interactionMethod) const override
    {
        (void)hit;
        (void)interactionMethod;
        return false;
    }

    bool activateWorldHit(const OpenYAMM::Game::GameplayWorldHit &hit) override
    {
        (void)hit;
        return false;
    }

    bool canActivateTelekinesisTarget(const OpenYAMM::Game::GameplayWorldHit &hit) const override
    {
        (void)hit;
        return false;
    }

    bool activateTelekinesisTarget(const OpenYAMM::Game::GameplayWorldHit &hit) override
    {
        (void)hit;
        return false;
    }

    std::optional<OpenYAMM::Game::GameplayPartyAttackActorFacts> partyAttackActorFacts(
        size_t actorIndex,
        bool visibleForFallback) const override
    {
        (void)actorIndex;
        (void)visibleForFallback;
        return std::nullopt;
    }

    std::vector<OpenYAMM::Game::GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const OpenYAMM::Game::GameplayPartyAttackFallbackQuery &query) const override
    {
        (void)query;
        return {};
    }

    bool applyPartyAttackMeleeDamage(
        size_t actorIndex,
        int damage,
        const OpenYAMM::Game::GameplayWorldPoint &source) override
    {
        (void)actorIndex;
        (void)damage;
        (void)source;
        return false;
    }

    bool spawnPartyAttackProjectile(const OpenYAMM::Game::GameplayPartyAttackProjectileRequest &request) override
    {
        (void)request;
        return false;
    }

    bool castPartyAttackSpell(const OpenYAMM::Game::GameplayPartyAttackSpellRequest &request) override
    {
        (void)request;
        return false;
    }

    void recordPartyAttackWorldResult(std::optional<size_t> actorIndex, bool attacked, bool actionPerformed) override
    {
        (void)actorIndex;
        (void)attacked;
        (void)actionPerformed;
    }

    bool worldInteractionReady() const override
    {
        return false;
    }

    bool worldInspectModeActive() const override
    {
        return false;
    }

    OpenYAMM::Game::GameplayWorldPickRequest buildWorldPickRequest(
        const OpenYAMM::Game::GameplayWorldPickRequestInput &input) const override
    {
        (void)input;
        return {};
    }

    std::optional<OpenYAMM::Game::GameplayHeldItemDropRequest> buildHeldItemDropRequest() const override
    {
        return std::nullopt;
    }

    OpenYAMM::Game::GameplayPartyAttackFrameInput buildPartyAttackFrameInput(
        const OpenYAMM::Game::GameplayWorldPickRequest &pickRequest) const override
    {
        (void)pickRequest;
        return {};
    }

    std::optional<size_t> spellActionHoveredActorIndex() const override
    {
        return std::nullopt;
    }

    std::optional<size_t> spellActionClosestVisibleHostileActorIndex() const override
    {
        return std::nullopt;
    }

    std::optional<bx::Vec3> spellActionActorTargetPoint(size_t actorIndex) const override
    {
        (void)actorIndex;
        return std::nullopt;
    }

    std::optional<bx::Vec3> spellActionGroundTargetPoint(float screenX, float screenY) const override
    {
        (void)screenX;
        (void)screenY;
        return std::nullopt;
    }

    OpenYAMM::Game::GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        const OpenYAMM::Game::GameplayWorldPickRequest &request) override
    {
        (void)request;
        return {};
    }

    OpenYAMM::Game::GameplayWorldHit pickKeyboardInteractionTarget(
        const OpenYAMM::Game::GameplayWorldPickRequest &request) override
    {
        (void)request;
        return {};
    }

    OpenYAMM::Game::GameplayWorldHit pickHeldItemWorldTarget(
        const OpenYAMM::Game::GameplayWorldPickRequest &request) override
    {
        (void)request;
        return {};
    }

    OpenYAMM::Game::GameplayWorldHit pickMouseInteractionTarget(
        const OpenYAMM::Game::GameplayWorldPickRequest &request) override
    {
        (void)request;
        return {};
    }

    OpenYAMM::Game::GameplayWorldHoverCacheState worldHoverCacheState() const override
    {
        return {};
    }

    OpenYAMM::Game::GameplayHoverStatusPayload refreshWorldHover(
        const OpenYAMM::Game::GameplayWorldHoverRequest &request) override
    {
        (void)request;
        return {};
    }

    OpenYAMM::Game::GameplayHoverStatusPayload readCachedWorldHover() override
    {
        return {};
    }

    void clearWorldHover() override
    {
    }

    bool canUseHeldItemOnWorld(const OpenYAMM::Game::GameplayWorldHit &hit) const override
    {
        (void)hit;
        return false;
    }

    bool useHeldItemOnWorld(const OpenYAMM::Game::GameplayWorldHit &hit) override
    {
        (void)hit;
        return false;
    }

    void applyPendingSpellCastWorldEffects(const OpenYAMM::Game::PartySpellCastResult &castResult) override
    {
        (void)castResult;
    }

    bool dropHeldItemToWorld(const OpenYAMM::Game::GameplayHeldItemDropRequest &request) override
    {
        (void)request;
        return false;
    }

    bool tryGetGameplayMinimapState(OpenYAMM::Game::GameplayMinimapState &state) const override
    {
        (void)state;
        return false;
    }

    void collectGameplayMinimapLines(std::vector<OpenYAMM::Game::GameplayMinimapLineState> &lines) override
    {
        (void)lines;
    }

    void collectGameplayMinimapMarkers(std::vector<OpenYAMM::Game::GameplayMinimapMarkerState> &markers) const override
    {
        (void)markers;
    }

    OpenYAMM::Game::GameplayChestViewState *activeChestView() override
    {
        return nullptr;
    }

    const OpenYAMM::Game::GameplayChestViewState *activeChestView() const override
    {
        return nullptr;
    }

    void commitActiveChestView() override
    {
    }

    bool takeActiveChestItem(size_t itemIndex, OpenYAMM::Game::GameplayChestItemState &item) override
    {
        (void)itemIndex;
        (void)item;
        return false;
    }

    bool takeActiveChestItemAt(
        uint8_t gridX,
        uint8_t gridY,
        OpenYAMM::Game::GameplayChestItemState &item) override
    {
        (void)gridX;
        (void)gridY;
        (void)item;
        return false;
    }

    bool tryPlaceActiveChestItemAt(
        const OpenYAMM::Game::GameplayChestItemState &item,
        uint8_t gridX,
        uint8_t gridY) override
    {
        (void)item;
        (void)gridX;
        (void)gridY;
        return false;
    }

    void closeActiveChestView() override
    {
    }

    OpenYAMM::Game::GameplayCorpseViewState *activeCorpseView() override
    {
        return nullptr;
    }

    const OpenYAMM::Game::GameplayCorpseViewState *activeCorpseView() const override
    {
        return nullptr;
    }

    void commitActiveCorpseView() override
    {
    }

    bool takeActiveCorpseItem(size_t itemIndex, OpenYAMM::Game::GameplayChestItemState &item) override
    {
        (void)itemIndex;
        (void)item;
        return false;
    }

    void closeActiveCorpseView() override
    {
    }

private:
    std::string m_mapName = "out01.odm";
    OpenYAMM::Game::Party m_party = {};
    float m_partyX = 0.0f;
    float m_partyY = 0.0f;
    float m_partyZ = 0.0f;
    bool m_indoorMap = false;
    bool m_partyFlyingForEventChecks = false;
};

const OpenYAMM::Tests::RegressionMapLoader &requireRegressionMapLoader()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionMapLoaderLoaded(),
        OpenYAMM::Tests::regressionMapLoaderFailure().c_str());
    return OpenYAMM::Tests::regressionMapLoader();
}

OpenYAMM::Game::Character makeScriptedRegressionMember()
{
    OpenYAMM::Game::Character member = {};
    member.name = "Ariel";
    member.className = "Knight";
    member.role = "Knight";
    member.portraitTextureName = "PC01-01";
    member.characterDataId = 1;
    member.birthYear = 1160;
    member.level = 1;
    member.might = 14;
    member.intellect = 14;
    member.personality = 14;
    member.endurance = 14;
    member.speed = 14;
    member.accuracy = 14;
    member.luck = 14;
    member.maxHealth = 40;
    member.health = 40;
    return member;
}

OpenYAMM::Game::InventoryItem makeScriptedInventoryItem(uint32_t objectDescriptionId)
{
    OpenYAMM::Game::InventoryItem item = {};
    item.objectDescriptionId = objectDescriptionId;
    item.quantity = 1;
    item.width = 1;
    item.height = 1;
    item.identified = true;
    return item;
}

int circusPrizeItemCount(const OpenYAMM::Game::Party &party)
{
    return party.inventoryItemCount(2090)
        + party.inventoryItemCount(2091)
        + party.inventoryItemCount(2097);
}

int eventInventoryItemCount(
    const OpenYAMM::Game::EventRuntimeState &runtimeState,
    const OpenYAMM::Game::Party &party,
    uint32_t itemId)
{
    return OpenYAMM::Game::EventRuntime::getInventoryItemCount(runtimeState, &party, itemId, std::nullopt);
}

OpenYAMM::Game::Party makeScriptedRegressionParty()
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(makeScriptedRegressionMember());
    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    return party;
}

const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pendingMapMove(
    const OpenYAMM::Game::EventRuntimeState &runtimeState)
{
    if (runtimeState.pendingMapMove.has_value())
    {
        return &*runtimeState.pendingMapMove;
    }

    if (runtimeState.pendingDialogueContext.has_value()
        && runtimeState.pendingDialogueContext->transitionMapMove.has_value())
    {
        return &*runtimeState.pendingDialogueContext->transitionMapMove;
    }

    return nullptr;
}

bool loadOutdoorMapWithCompanionOptions(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::GameDataLoader &gameDataLoader,
    const std::string &mapFileName,
    OpenYAMM::Game::MapLoadPurpose loadPurpose,
    const OpenYAMM::Game::MapCompanionLoadOptions &loadOptions,
    OpenYAMM::Game::MapAssetInfo &mapAssetInfo)
{
    const OpenYAMM::Game::MapStatsEntry *pMapEntry = gameDataLoader.getMapStats().findByFileName(mapFileName);

    if (pMapEntry == nullptr)
    {
        return false;
    }

    OpenYAMM::Game::MapAssetLoader loader = {};
    const std::optional<OpenYAMM::Game::MapAssetInfo> loadedMap = loader.load(
        assetFileSystem,
        *pMapEntry,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getObjectTable(),
        loadPurpose,
        loadOptions);

    if (!loadedMap || !loadedMap->outdoorMapData || !loadedMap->outdoorMapDeltaData)
    {
        return false;
    }

    mapAssetInfo = *loadedMap;
    return true;
}

std::string cachedMapKey(
    const char *pKind,
    const std::string &mapFileName,
    OpenYAMM::Game::MapLoadPurpose loadPurpose,
    const OpenYAMM::Game::MapCompanionLoadOptions &loadOptions)
{
    return std::string(pKind)
        + "|"
        + mapFileName
        + "|"
        + std::to_string(static_cast<int>(loadPurpose))
        + "|"
        + (loadOptions.allowSceneYml ? "scene" : "no_scene")
        + "|"
        + (loadOptions.allowLegacyCompanion ? "legacy" : "no_legacy");
}

const OpenYAMM::Game::MapAssetInfo *loadCachedMapWithCompanionOptions(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::GameDataLoader &gameDataLoader,
    const std::string &mapFileName,
    OpenYAMM::Game::MapLoadPurpose loadPurpose,
    const OpenYAMM::Game::MapCompanionLoadOptions &loadOptions,
    bool indoor)
{
    static std::unordered_map<std::string, OpenYAMM::Game::MapAssetInfo> cachedMaps;

    const std::string key = cachedMapKey(
        indoor ? "indoor" : "outdoor",
        mapFileName,
        loadPurpose,
        loadOptions);
    const std::unordered_map<std::string, OpenYAMM::Game::MapAssetInfo>::const_iterator cachedIt =
        cachedMaps.find(key);

    if (cachedIt != cachedMaps.end())
    {
        return &cachedIt->second;
    }

    const OpenYAMM::Game::MapStatsEntry *pMapEntry = gameDataLoader.getMapStats().findByFileName(mapFileName);

    if (pMapEntry == nullptr)
    {
        return nullptr;
    }

    OpenYAMM::Game::MapAssetLoader loader = {};
    std::optional<OpenYAMM::Game::MapAssetInfo> loadedMap = loader.load(
        assetFileSystem,
        *pMapEntry,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getObjectTable(),
        loadPurpose,
        loadOptions);

    if (!loadedMap)
    {
        return nullptr;
    }

    if (indoor)
    {
        if (!loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData)
        {
            return nullptr;
        }
    }
    else if (!loadedMap->outdoorMapData || !loadedMap->outdoorMapDeltaData)
    {
        return nullptr;
    }

    const auto inserted = cachedMaps.emplace(key, std::move(*loadedMap));
    return &inserted.first->second;
}

const OpenYAMM::Game::MapAssetInfo *loadCachedOutdoorMapWithCompanionOptions(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::GameDataLoader &gameDataLoader,
    const std::string &mapFileName,
    OpenYAMM::Game::MapLoadPurpose loadPurpose,
    const OpenYAMM::Game::MapCompanionLoadOptions &loadOptions)
{
    return loadCachedMapWithCompanionOptions(
        assetFileSystem,
        gameDataLoader,
        mapFileName,
        loadPurpose,
        loadOptions,
        false);
}

const OpenYAMM::Game::MapAssetInfo *loadCachedIndoorMapWithCompanionOptions(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::GameDataLoader &gameDataLoader,
    const std::string &mapFileName,
    OpenYAMM::Game::MapLoadPurpose loadPurpose,
    const OpenYAMM::Game::MapCompanionLoadOptions &loadOptions)
{
    return loadCachedMapWithCompanionOptions(
        assetFileSystem,
        gameDataLoader,
        mapFileName,
        loadPurpose,
        loadOptions,
        true);
}

bool loadIndoorMapWithCompanionOptions(
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const OpenYAMM::Game::GameDataLoader &gameDataLoader,
    const std::string &mapFileName,
    OpenYAMM::Game::MapLoadPurpose loadPurpose,
    const OpenYAMM::Game::MapCompanionLoadOptions &loadOptions,
    OpenYAMM::Game::MapAssetInfo &mapAssetInfo)
{
    const OpenYAMM::Game::MapStatsEntry *pMapEntry = gameDataLoader.getMapStats().findByFileName(mapFileName);

    if (pMapEntry == nullptr)
    {
        return false;
    }

    OpenYAMM::Game::MapAssetLoader loader = {};
    const std::optional<OpenYAMM::Game::MapAssetInfo> loadedMap = loader.load(
        assetFileSystem,
        *pMapEntry,
        gameDataLoader.getMonsterTable(),
        gameDataLoader.getObjectTable(),
        loadPurpose,
        loadOptions);

    if (!loadedMap || !loadedMap->indoorMapData || !loadedMap->indoorMapDeltaData)
    {
        return false;
    }

    mapAssetInfo = *loadedMap;
    return true;
}

bool outdoorMapHasCogTriggeredNumber(const OpenYAMM::Game::MapAssetInfo &mapAssetInfo, uint16_t eventId)
{
    if (!mapAssetInfo.outdoorMapData)
    {
        return false;
    }

    for (const OpenYAMM::Game::OutdoorBModel &bmodel : mapAssetInfo.outdoorMapData->bmodels)
    {
        for (const OpenYAMM::Game::OutdoorBModelFace &face : bmodel.faces)
        {
            if (face.cogTriggeredNumber == eventId)
            {
                return true;
            }
        }
    }

    return false;
}

bool bitmapTextureSetContains(
    const std::vector<OpenYAMM::Game::OutdoorBitmapTexture> &textures,
    const std::string &textureName)
{
    const std::string normalizedTextureName = OpenYAMM::Game::toLowerCopy(textureName);

    for (const OpenYAMM::Game::OutdoorBitmapTexture &texture : textures)
    {
        if (OpenYAMM::Game::toLowerCopy(texture.textureName) == normalizedTextureName)
        {
            return true;
        }
    }

    return false;
}

const OpenYAMM::Game::SurfaceAnimationSequence *findSurfaceAnimationBinding(
    const std::vector<std::pair<std::string, OpenYAMM::Game::SurfaceAnimationSequence>> &bindings,
    const std::string &textureName)
{
    const std::string normalizedTextureName = OpenYAMM::Game::toLowerCopy(textureName);

    for (const auto &binding : bindings)
    {
        if (OpenYAMM::Game::toLowerCopy(binding.first) == normalizedTextureName)
        {
            return &binding.second;
        }
    }

    return nullptr;
}

OpenYAMM::Game::Character makeRegressionPartyMember(
    const std::string &name,
    const std::string &className,
    const std::string &portraitTextureName,
    uint32_t characterDataId)
{
    OpenYAMM::Game::Character member = {};
    member.name = name;
    member.className = className;
    member.role = className;
    member.portraitTextureName = portraitTextureName;
    member.characterDataId = characterDataId;
    member.birthYear = 1160;
    member.experience = 0;
    member.level = 1;
    member.skillPoints = 5;
    member.might = 14;
    member.intellect = 14;
    member.personality = 14;
    member.endurance = 14;
    member.speed = 14;
    member.accuracy = 14;
    member.luck = 14;
    member.maxHealth = 40;
    member.health = 40;
    member.maxSpellPoints = 20;
    member.spellPoints = 20;
    return member;
}

OpenYAMM::Game::PartySeed createRegressionPartySeed()
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.gold = 200;
    seed.food = 7;
    seed.members.push_back(makeRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));
    seed.members.push_back(makeRegressionPartyMember("Brom", "Cleric", "PC03-01", 3));
    seed.members.push_back(makeRegressionPartyMember("Cedric", "Druid", "PC05-01", 5));
    seed.members.push_back(makeRegressionPartyMember("Daria", "Sorcerer", "PC07-01", 7));
    return seed;
}

std::string bytesToUpperHex(const std::vector<uint8_t> &bytes)
{
    static constexpr char HexDigits[] = "0123456789ABCDEF";

    std::string text;
    text.reserve(bytes.size() * 2);

    for (uint8_t value : bytes)
    {
        text.push_back(HexDigits[(value >> 4) & 0x0F]);
        text.push_back(HexDigits[value & 0x0F]);
    }

    return text;
}

std::optional<std::string> readSourceTextFile(const std::filesystem::path &path)
{
    std::ifstream stream(path);

    if (!stream)
    {
        return std::nullopt;
    }

    std::ostringstream contents;
    contents << stream.rdbuf();
    return contents.str();
}

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadMm7MapOverlayProgram(
    const std::filesystem::path &sourceRoot,
    const char *pBaseName,
    const char *pOverlayName,
    std::string &error)
{
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> crossContinentsCommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/events/common/cross_continents_common.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/common/mm7_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/maps" / (std::string(pBaseName) + ".lua"));
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/maps" / (std::string(pOverlayName) + ".lua"));

    REQUIRE(supportLua.has_value());
    REQUIRE(crossContinentsCommonLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    return OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        *supportLua + "\n\n" + *crossContinentsCommonLua + "\n\n" + *commonLua + "\n\n" + *baseLua
            + "\n\n" + *overlayLua,
        std::string("@events/maps/") + pBaseName + ".lua + events/maps/" + pOverlayName + ".lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        error);
}

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadMm7GlobalSupplementProgram(
    const std::filesystem::path &sourceRoot,
    std::string &error)
{
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> crossContinentsCommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/events/common/cross_continents_common.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/common/mm7_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/events/Global.lua");
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/Global_mm7_mmmerge.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(crossContinentsCommonLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    return OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        *supportLua + "\n\n" + *crossContinentsCommonLua + "\n\n" + *commonLua + "\n\n" + *baseLua
            + "\n\n" + *overlayLua,
        "@events/Global.lua + events/Global_mm7_mmmerge.lua",
        OpenYAMM::Game::ScriptedEventScope::Global,
        error);
}

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadMm6MapOverlayProgram(
    const std::filesystem::path &sourceRoot,
    const char *pBaseName,
    const char *pOverlayName,
    std::string &error)
{
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> crossContinentsCommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/events/common/cross_continents_common.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps" / (std::string(pBaseName) + ".lua"));
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps" / (std::string(pOverlayName) + ".lua"));

    REQUIRE(supportLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    return OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        *supportLua + "\n\n" + *commonLua + "\n\n" + *baseLua + "\n\n" + *overlayLua,
        std::string("@events/maps/") + pBaseName + ".lua + events/maps/" + pOverlayName + ".lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        error);
}

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadMm8MapOverlayProgram(
    const std::filesystem::path &sourceRoot,
    const char *pBaseName,
    const char *pOverlayName,
    std::string &error)
{
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm8/events/common/mm8_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm8/events/maps" / (std::string(pBaseName) + ".lua"));
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm8/events/maps" / (std::string(pOverlayName) + ".lua"));

    REQUIRE(supportLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    return OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        *supportLua + "\n\n" + *commonLua + "\n\n" + *baseLua + "\n\n" + *overlayLua,
        std::string("@events/maps/") + pBaseName + ".lua + events/maps/" + pOverlayName + ".lua",
        OpenYAMM::Game::ScriptedEventScope::Map,
        error);
}

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadMm6GlobalSupplementProgram(
    const std::filesystem::path &sourceRoot,
    std::string &error)
{
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> crossContinentsCommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/events/common/cross_continents_common.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/events/Global.lua");
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/Global_mm6_mmmerge.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(crossContinentsCommonLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    return OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        *supportLua + "\n\n" + *crossContinentsCommonLua + "\n\n" + *commonLua + "\n\n" + *baseLua
            + "\n\n" + *overlayLua,
        "@events/Global.lua + events/Global_mm6_mmmerge.lua",
        OpenYAMM::Game::ScriptedEventScope::Global,
        error);
}

void appendNormalizedPosition(std::ostringstream &stream, int x, int y, int z)
{
    stream << x << ',' << y << ',' << z;
}

std::string buildNormalizedOutdoorAuthoredSnapshot(const OpenYAMM::Game::MapAssetInfo &mapAssetInfo)
{
    std::ostringstream stream;

    if (!mapAssetInfo.outdoorMapData || !mapAssetInfo.outdoorMapDeltaData)
    {
        stream << "missing_outdoor_state\n";
        return stream.str();
    }

    const OpenYAMM::Game::OutdoorMapData &outdoorMapData = *mapAssetInfo.outdoorMapData;
    const OpenYAMM::Game::MapDeltaData &mapDeltaData = *mapAssetInfo.outdoorMapDeltaData;
    const std::string effectiveSkyTexture =
        !mapDeltaData.locationTime.skyTextureName.empty()
        ? mapDeltaData.locationTime.skyTextureName
        : outdoorMapData.skyTexture;
    uint32_t mapExtraBitsRaw = 0;
    int32_t ceiling = 0;

    if (mapDeltaData.locationTime.reserved.size() >= sizeof(mapExtraBitsRaw) + sizeof(ceiling))
    {
        std::memcpy(&mapExtraBitsRaw, mapDeltaData.locationTime.reserved.data(), sizeof(mapExtraBitsRaw));
        std::memcpy(
            &ceiling,
            mapDeltaData.locationTime.reserved.data() + sizeof(mapExtraBitsRaw),
            sizeof(ceiling));
    }

    stream << "environment\n";
    stream << "sky_texture=" << effectiveSkyTexture << '\n';
    stream << "ground_tileset_name=" << outdoorMapData.groundTilesetName << '\n';
    stream << "master_tile=" << static_cast<int>(outdoorMapData.masterTile) << '\n';
    stream << "tile_set_lookup_indices="
           << outdoorMapData.tileSetLookupIndices[0] << ','
           << outdoorMapData.tileSetLookupIndices[1] << ','
           << outdoorMapData.tileSetLookupIndices[2] << ','
           << outdoorMapData.tileSetLookupIndices[3] << '\n';
    stream << "day_bits_raw=" << mapDeltaData.locationTime.weatherFlags << '\n';
    stream << "map_extra_bits_raw=" << mapExtraBitsRaw << '\n';
    stream << "flag_foggy=" << (((mapDeltaData.locationTime.weatherFlags & 0x1) != 0) ? 1 : 0) << '\n';
    stream << "flag_raining=" << (((mapExtraBitsRaw & 0x1) != 0) ? 1 : 0) << '\n';
    stream << "flag_snowing=" << (((mapExtraBitsRaw & 0x2) != 0) ? 1 : 0) << '\n';
    stream << "flag_underwater=" << (((mapExtraBitsRaw & 0x4) != 0) ? 1 : 0) << '\n';
    stream << "flag_no_terrain=" << (((mapExtraBitsRaw & 0x8) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_dark=" << (((mapExtraBitsRaw & 0x10) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_light=" << (((mapExtraBitsRaw & 0x20) != 0) ? 1 : 0) << '\n';
    stream << "flag_always_foggy=" << (((mapExtraBitsRaw & 0x40) != 0) ? 1 : 0) << '\n';
    stream << "flag_red_fog=" << (((mapExtraBitsRaw & 0x80) != 0) ? 1 : 0) << '\n';
    stream << "fog_weak_distance=" << mapDeltaData.locationTime.fogWeakDistance << '\n';
    stream << "fog_strong_distance=" << mapDeltaData.locationTime.fogStrongDistance << '\n';
    stream << "ceiling=" << ceiling << '\n';

    stream << "terrain\n";

    for (size_t cellIndex = 0; cellIndex < outdoorMapData.attributeMap.size(); ++cellIndex)
    {
        const uint8_t value = outdoorMapData.attributeMap[cellIndex];

        if (value == 0)
        {
            continue;
        }

        const size_t x = cellIndex % OpenYAMM::Game::OutdoorMapData::TerrainWidth;
        const size_t y = cellIndex / OpenYAMM::Game::OutdoorMapData::TerrainWidth;
        stream << x << ',' << y << ',' << static_cast<int>(value)
               << ',' << (((value & 0x01) != 0) ? 1 : 0)
               << ',' << (((value & 0x02) != 0) ? 1 : 0) << '\n';
    }

    stream << "interactive_faces\n";

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OpenYAMM::Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex)
        {
            const OpenYAMM::Game::OutdoorBModelFace &face = bmodel.faces[faceIndex];

            if (face.attributes == 0
                && face.cogNumber == 0
                && face.cogTriggeredNumber == 0
                && face.cogTrigger == 0)
            {
                continue;
            }

            stream << bmodelIndex << ',' << faceIndex << ','
                   << face.attributes << ','
                   << face.cogNumber << ','
                   << face.cogTriggeredNumber << ','
                   << face.cogTrigger << '\n';
        }
    }

    stream << "entities\n";

    for (size_t entityIndex = 0; entityIndex < outdoorMapData.entities.size(); ++entityIndex)
    {
        const OpenYAMM::Game::OutdoorEntity &entity = outdoorMapData.entities[entityIndex];
        const uint16_t decorationFlag =
            entityIndex < mapDeltaData.decorationFlags.size()
            ? mapDeltaData.decorationFlags[entityIndex]
            : 0;

        stream << entity.name << '|'
               << entity.decorationListId << '|'
               << entity.aiAttributes << '|';
        appendNormalizedPosition(stream, entity.x, entity.y, entity.z);
        stream << '|'
               << entity.facing << '|'
               << entity.eventIdPrimary << '|'
               << entity.eventIdSecondary << '|'
               << entity.variablePrimary << '|'
               << entity.variableSecondary << '|'
               << entity.specialTrigger << '|'
               << decorationFlag << '\n';
    }

    stream << "spawns\n";

    for (const OpenYAMM::Game::OutdoorSpawn &spawn : outdoorMapData.spawns)
    {
        appendNormalizedPosition(stream, spawn.x, spawn.y, spawn.z);
        stream << '|'
               << spawn.radius << '|'
               << spawn.typeId << '|'
               << spawn.index << '|'
               << spawn.attributes << '|'
               << spawn.group << '\n';
    }

    stream << "location\n";
    stream << mapDeltaData.locationInfo.respawnCount << '|'
           << mapDeltaData.locationInfo.lastRespawnDay << '|'
           << mapDeltaData.locationInfo.reputation << '|'
           << mapDeltaData.locationInfo.alertStatus << '\n';

    stream << "face_attribute_overrides\n";
    size_t flattenedFaceIndex = 0;

    for (size_t bmodelIndex = 0; bmodelIndex < outdoorMapData.bmodels.size(); ++bmodelIndex)
    {
        const OpenYAMM::Game::OutdoorBModel &bmodel = outdoorMapData.bmodels[bmodelIndex];

        for (size_t faceIndex = 0; faceIndex < bmodel.faces.size(); ++faceIndex, ++flattenedFaceIndex)
        {
            const uint32_t baseValue = bmodel.faces[faceIndex].attributes;
            const uint32_t overrideValue =
                flattenedFaceIndex < mapDeltaData.faceAttributes.size()
                ? mapDeltaData.faceAttributes[flattenedFaceIndex]
                : baseValue;

            if (overrideValue == baseValue)
            {
                continue;
            }

            stream << bmodelIndex << ',' << faceIndex << ',' << overrideValue << '\n';
        }
    }

    stream << "actors\n";

    for (const OpenYAMM::Game::MapDeltaActor &actor : mapDeltaData.actors)
    {
        stream << actor.name << '|'
               << actor.npcId << '|'
               << actor.attributes << '|'
               << actor.hp << '|'
               << static_cast<int>(actor.hostilityType) << '|'
               << actor.monsterInfoId << '|'
               << actor.monsterId << '|'
               << actor.radius << '|'
               << actor.height << '|'
               << actor.moveSpeed << '|';
        appendNormalizedPosition(stream, actor.x, actor.y, actor.z);
        stream << '|'
               << actor.spriteIds[0] << ','
               << actor.spriteIds[1] << ','
               << actor.spriteIds[2] << ','
               << actor.spriteIds[3] << '|'
               << actor.sectorId << '|'
               << actor.currentActionAnimation << '|'
               << actor.group << '|'
               << actor.ally << '|'
               << actor.uniqueNameIndex << '\n';
    }

    stream << "sprite_objects\n";

    for (const OpenYAMM::Game::MapDeltaSpriteObject &spriteObject : mapDeltaData.spriteObjects)
    {
        stream << spriteObject.spriteId << '|'
               << spriteObject.objectDescriptionId << '|';
        appendNormalizedPosition(stream, spriteObject.x, spriteObject.y, spriteObject.z);
        stream << '|';
        appendNormalizedPosition(
            stream,
            spriteObject.velocityX,
            spriteObject.velocityY,
            spriteObject.velocityZ);
        stream << '|'
               << spriteObject.yawAngle << '|'
               << spriteObject.soundId << '|'
               << spriteObject.attributes << '|'
               << spriteObject.sectorId << '|'
               << spriteObject.timeSinceCreated << '|'
               << spriteObject.temporaryLifetime << '|'
               << spriteObject.glowRadiusMultiplier << '|'
               << spriteObject.spellId << '|'
               << spriteObject.spellLevel << '|'
               << spriteObject.spellSkill << '|'
               << spriteObject.field54 << '|'
               << spriteObject.spellCasterPid << '|'
               << spriteObject.spellTargetPid << '|'
               << static_cast<int>(spriteObject.lodDistance) << '|'
               << static_cast<int>(spriteObject.spellCasterAbility) << '|';
        appendNormalizedPosition(
            stream,
            spriteObject.initialX,
            spriteObject.initialY,
            spriteObject.initialZ);
        stream << '|'
               << bytesToUpperHex(spriteObject.rawContainingItem) << '\n';
    }

    stream << "chests\n";

    for (const OpenYAMM::Game::MapDeltaChest &chest : mapDeltaData.chests)
    {
        stream << chest.chestTypeId << '|'
               << chest.flags << '|'
               << bytesToUpperHex(chest.rawItems) << '|';

        for (size_t index = 0; index < chest.inventoryMatrix.size(); ++index)
        {
            if (index > 0)
            {
                stream << ',';
            }

            stream << chest.inventoryMatrix[index];
        }

        stream << '\n';
    }

    stream << "variables_map\n";

    for (size_t index = 0; index < mapDeltaData.eventVariables.mapVars.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << static_cast<int>(mapDeltaData.eventVariables.mapVars[index]);
    }

    stream << "\nvariables_decor\n";

    for (size_t index = 0; index < mapDeltaData.eventVariables.decorVars.size(); ++index)
    {
        if (index > 0)
        {
            stream << ',';
        }

        stream << static_cast<int>(mapDeltaData.eventVariables.decorVars[index]);
    }

    stream << '\n';
    return stream.str();
}
}

TEST_CASE("generated_lua_event_scripts_are_loaded_from_files")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::optional<OpenYAMM::Game::MapAssetInfo> &selectedMap = mapLoader.gameDataLoader.getSelectedMap();

    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->globalEventProgram.has_value());
    REQUIRE(selectedMap->globalEventProgram->luaSourceText().has_value());
    REQUIRE(selectedMap->globalEventProgram->luaSourceName().has_value());
    CHECK(selectedMap->globalEventProgram->luaSourceName()->starts_with("@events/Global.lua"));
    CHECK(
        selectedMap->globalEventProgram->luaSourceName()->find("events/Global_mm6_mmmerge.lua")
        != std::string::npos);
    CHECK(
        selectedMap->globalEventProgram->luaSourceName()->find("events/Global_mm7_mmmerge.lua")
        != std::string::npos);
    CHECK(std::filesystem::exists(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/events/Global.lua"));
    CHECK_FALSE(std::filesystem::exists(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/scripts/Global.lua"));
    CHECK_FALSE(std::filesystem::exists(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm8/events/Global.lua"));

    REQUIRE(selectedMap->localEventProgram.has_value());
    REQUIRE(selectedMap->localEventProgram->luaSourceText().has_value());
    REQUIRE(selectedMap->localEventProgram->luaSourceName().has_value());

    const std::string expectedLocalSourceName =
        "@events/maps/"
        + OpenYAMM::Game::toLowerCopy(std::filesystem::path(selectedMap->map.fileName).stem().string())
        + ".lua";

    CHECK(selectedMap->localEventProgram->luaSourceName()->starts_with(expectedLocalSourceName));

    if (OpenYAMM::Game::toLowerCopy(std::filesystem::path(selectedMap->map.fileName).stem().string()) == "out01")
    {
        CHECK(
            selectedMap->localEventProgram->luaSourceName()->find("events/maps/out01_mmmerge.lua")
            != std::string::npos);
    }
}

TEST_CASE("mmmerge shared Breach maps are mounted and scripted")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapCompanionLoadOptions loadOptions = {};

    OpenYAMM::Game::MapAssetInfo breach = {};
    REQUIRE(loadOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "Breach.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        loadOptions,
        breach));
    CHECK_EQ(breach.map.worldId, "mmmerge");
    REQUIRE(breach.scenePath.has_value());
    CHECK(breach.geometryPath.ends_with("Breach.odm"));
    CHECK(breach.scenePath->ends_with("Breach.scene.yml"));
    CHECK_EQ(breach.authoredCompanionSource, OpenYAMM::Game::AuthoredCompanionSource::SceneYml);
    CHECK(outdoorMapHasCogTriggeredNumber(breach, 54));
    CHECK(outdoorMapHasCogTriggeredNumber(breach, 81));
    CHECK(outdoorMapHasCogTriggeredNumber(breach, 900));

    OpenYAMM::Game::MapAssetInfo brAlvar = {};
    REQUIRE(loadOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "BrAlvar.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        loadOptions,
        brAlvar));
    CHECK_EQ(brAlvar.map.worldId, "mmmerge");
    REQUIRE(brAlvar.scenePath.has_value());
    CHECK(brAlvar.geometryPath.ends_with("BrAlvar.odm"));
    CHECK(brAlvar.scenePath->ends_with("BrAlvar.scene.yml"));
    CHECK_EQ(brAlvar.authoredCompanionSource, OpenYAMM::Game::AuthoredCompanionSource::SceneYml);
    CHECK(outdoorMapHasCogTriggeredNumber(brAlvar, 53));
    CHECK(outdoorMapHasCogTriggeredNumber(brAlvar, 54));
    CHECK(outdoorMapHasCogTriggeredNumber(brAlvar, 81));

    OpenYAMM::Game::MapAssetInfo brBase = {};
    REQUIRE(loadIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "BrBase.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        loadOptions,
        brBase));
    CHECK_EQ(brBase.map.worldId, "mmmerge");
    REQUIRE(brBase.scenePath.has_value());
    CHECK(brBase.geometryPath.ends_with("BrBase.blv"));
    CHECK(brBase.scenePath->ends_with("BrBase.scene.yml"));
    CHECK_EQ(brBase.authoredCompanionSource, OpenYAMM::Game::AuthoredCompanionSource::SceneYml);

    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportLua.has_value());

    struct ScriptExpectation
    {
        const char *pPath;
        std::vector<uint32_t> expectedEventIds;
    };

    const ScriptExpectation scripts[] = {
        {
            "assets_dev/worlds/mmmerge/events/maps/Breach.lua",
            {54, 81, 900, 101, 104, 110, 118, 125, 128, 66001}
        },
        {
            "assets_dev/worlds/mmmerge/events/maps/BrAlvar.lua",
            {
                5, 7, 15, 16, 30, 53, 54, 60, 81, 82, 101, 104, 110,
                118, 125, 128, 301, 315, 1790, 1792, 1793, 1794, 65005, 66002, 66004
            }
        },
        {"assets_dev/worlds/mmmerge/events/maps/BrBase.lua", {1, 2, 66003}},
    };

    std::optional<OpenYAMM::Game::ScriptedEventProgram> breachProgram = std::nullopt;
    std::optional<OpenYAMM::Game::ScriptedEventProgram> brAlvarProgram = std::nullopt;

    for (const ScriptExpectation &script : scripts)
    {
        const std::optional<std::string> scriptLua = readSourceTextFile(sourceRoot / script.pPath);
        REQUIRE(scriptLua.has_value());

        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> program =
            OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
                *supportLua + "\n\n" + *scriptLua,
                std::string("@") + script.pPath,
                OpenYAMM::Game::ScriptedEventScope::Map,
                error);
        REQUIRE_MESSAGE(program.has_value(), error.c_str());

        for (uint32_t eventId : script.expectedEventIds)
        {
            CHECK(program->hasEvent(eventId));
        }

        if (std::strcmp(script.pPath, "assets_dev/worlds/mmmerge/events/maps/Breach.lua") == 0)
        {
            breachProgram = program;
        }
        else if (std::strcmp(script.pPath, "assets_dev/worlds/mmmerge/events/maps/BrAlvar.lua") == 0)
        {
            brAlvarProgram = program;
        }
    }

    REQUIRE(breachProgram.has_value());
    REQUIRE(brAlvarProgram.has_value());

    auto hasFollower = [](const OpenYAMM::Game::EventRuntimeState &state, uint32_t npcId)
    {
        return std::find_if(
            state.hiredNpcFollowers.begin(),
            state.hiredNpcFollowers.end(),
            [npcId](const OpenYAMM::Game::EventRuntimeState::HiredNpcFollower &follower)
            {
                return follower.npcId == npcId;
            }) != state.hiredNpcFollowers.end();
    };

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    runtimeState.mapVars[12] = 1;
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    RecordingSceneEventContext sceneContext = {};

    REQUIRE(eventRuntime.buildOnLoadState(
        breachProgram,
        std::nullopt,
        std::nullopt,
        runtimeState,
        &party,
        &sceneContext));

    REQUIRE_EQ(sceneContext.outdoorModelMechanismCalls.size(), 28u);
    CHECK_EQ(sceneContext.outdoorModelMechanismCalls.front().mechanismId, 101u);
    CHECK_EQ(sceneContext.outdoorModelMechanismCalls.front().modelName, "Time_1");
    CHECK_EQ(sceneContext.outdoorModelMechanismCalls.front().dz, -10);
    CHECK_EQ(sceneContext.outdoorModelMechanismCalls.front().moveTimeMs, 1000u);
    CHECK(sceneContext.outdoorModelMechanismCalls.front().closed);
    CHECK_FALSE(sceneContext.outdoorModelMechanismCalls.front().moveParty);
    CHECK_EQ(sceneContext.outdoorModelMechanismCalls.back().mechanismId, 128u);
    CHECK_EQ(sceneContext.outdoorModelMechanismCalls.back().modelName, "Elev_3_Button");
    CHECK_EQ(sceneContext.outdoorModelMechanismCalls.back().dz, 5);
    CHECK_EQ(sceneContext.outdoorModelMechanismCalls.back().moveTimeMs, 250u);

    OpenYAMM::Game::EventRuntimeState brAlvarRuntimeState = {};
    OpenYAMM::Game::Party brAlvarParty = makeScriptedRegressionParty();
    RecordingSceneEventContext brAlvarSceneContext = {};

    REQUIRE(eventRuntime.buildOnLoadState(
        brAlvarProgram,
        std::nullopt,
        std::nullopt,
        brAlvarRuntimeState,
        &brAlvarParty,
        &brAlvarSceneContext));

    REQUIRE_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.size(), 28u);
    CHECK_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.front().mechanismId, 101u);
    CHECK_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.front().modelName, "Time_1");
    CHECK_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.front().dz, -10);
    CHECK_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.front().moveTimeMs, 1000u);
    CHECK_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.back().mechanismId, 128u);
    CHECK_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.back().modelName, "Elev_3_Button");
    CHECK_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.back().dz, 5);
    CHECK_EQ(brAlvarSceneContext.outdoorModelMechanismCalls.back().moveTimeMs, 250u);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(260, 448)],
        4);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(448, 260)],
        4);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(260, 449)],
        4);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(449, 260)],
        4);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(261, 450)],
        4);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(450, 261)],
        4);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(475, 0)],
        0);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(476, 0)],
        0);
    CHECK_EQ(
        brAlvarRuntimeState.monsterRelationOverrides[
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(477, 0)],
        0);
    CHECK_EQ(brAlvarRuntimeState.npcTopicOverrides[772][0], 1793u);
    const uint32_t actorInvisibleBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Invisible);
    CHECK((brAlvarRuntimeState.actorClearMasks[77] & actorInvisibleBit) != 0);
    CHECK((brAlvarRuntimeState.actorClearMasks[78] & actorInvisibleBit) != 0);
    CHECK((brAlvarRuntimeState.actorClearMasks[79] & actorInvisibleBit) != 0);
    CHECK((brAlvarRuntimeState.actorClearMasks[80] & actorInvisibleBit) != 0);

    OpenYAMM::Game::EventRuntimeState::ActiveHookContext friendHook = {};
    friendHook.kind = OpenYAMM::Game::EventRuntimeHookKind::NpcEnter;
    friendHook.npcId = 772;
    brAlvarRuntimeState.activeHookContext = friendHook;
    REQUIRE(eventRuntime.executeHooks(
        brAlvarProgram,
        std::nullopt,
        OpenYAMM::Game::EventRuntimeHookKind::NpcEnter,
        brAlvarRuntimeState,
        &brAlvarParty,
        &brAlvarSceneContext));
    CHECK_EQ(brAlvarRuntimeState.namedMapVars["CurrentFriendNpc"], 772);

    size_t previousMessageCount = brAlvarRuntimeState.messages.size();
    REQUIRE(eventRuntime.executeNpcTopicEventById(
        brAlvarProgram,
        std::nullopt,
        1793,
        brAlvarRuntimeState,
        &brAlvarParty,
        &brAlvarSceneContext));
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.GotFQHints"], 1);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.GotFQHint1"], 1);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.HintByNPC.772"], 1);
    CHECK((brAlvarRuntimeState.actorSetMasks[77] & actorInvisibleBit) != 0);
    CHECK_GT(brAlvarRuntimeState.messages.size(), previousMessageCount);

    friendHook.npcId = 773;
    brAlvarRuntimeState.activeHookContext = friendHook;
    REQUIRE(eventRuntime.executeHooks(
        brAlvarProgram,
        std::nullopt,
        OpenYAMM::Game::EventRuntimeHookKind::NpcEnter,
        brAlvarRuntimeState,
        &brAlvarParty,
        &brAlvarSceneContext));
    REQUIRE(eventRuntime.executeNpcTopicEventById(
        brAlvarProgram,
        std::nullopt,
        1793,
        brAlvarRuntimeState,
        &brAlvarParty,
        &brAlvarSceneContext));
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.GotFQHints"], 2);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.GotFQHint2"], 1);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.HintByNPC.773"], 2);
    CHECK_EQ(brAlvarRuntimeState.npcTopicOverrides[1092][0], 1794u);

    brAlvarRuntimeState.namedGlobalVars.erase("MMerge.CrossContinents.GotFQHint2");
    brAlvarRuntimeState.namedGlobalVars.erase("MMerge.CrossContinents.GotFQHint3");
    REQUIRE(eventRuntime.executeEventById(
        brAlvarProgram,
        std::nullopt,
        5,
        brAlvarRuntimeState,
        &brAlvarParty,
        &brAlvarSceneContext));
    CHECK_EQ(brAlvarRuntimeState.npcHouseOverrides[1092], 712u);
    REQUIRE(brAlvarRuntimeState.pendingDialogueContext.has_value());
    CHECK_EQ(brAlvarRuntimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
    CHECK_EQ(brAlvarRuntimeState.pendingDialogueContext->sourceId, 712u);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.GotFQHint2"], 1);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.GotFQHint3"], 1);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.RiddlesAnswered"], 5);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.ChaosReadyToFollow"], 1);
    CHECK_EQ(brAlvarRuntimeState.npcTopicOverrides[1092][0], 1792u);
    CHECK_EQ(brAlvarRuntimeState.npcTopicOverrides[1092][1], 0u);

    REQUIRE(eventRuntime.executeNpcTopicEventById(
        brAlvarProgram,
        std::nullopt,
        1792,
        brAlvarRuntimeState,
        &brAlvarParty,
        &brAlvarSceneContext));
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.CaughtChaos"], 1);
    CHECK_EQ(brAlvarRuntimeState.namedGlobalVars["MMerge.CrossContinents.CoughtChaos"], 1);
    CHECK(hasFollower(brAlvarRuntimeState, 1092));
    CHECK_EQ(brAlvarRuntimeState.npcHouseOverrides[1092], 0u);
}

TEST_CASE("seer lost item topic recovers ever owned active quest items")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> mm6CommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    const std::optional<std::string> mm6GlobalLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/Global_mm6_mmmerge.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(mm6CommonLua.has_value());
    REQUIRE(mm6GlobalLua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *mm6CommonLua + "\n\n" + *mm6GlobalLua,
            "@events/Global_mm6_mmmerge.lua",
            OpenYAMM::Game::ScriptedEventScope::Global,
            error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());
    REQUIRE(globalEventProgram->hasEvent(1358));

    OpenYAMM::Game::EventRuntime eventRuntime = {};

    OpenYAMM::Game::Party recoveredParty = makeScriptedRegressionParty();
    recoveredParty.recordEverOwnedItem(2170);
    recoveredParty.setQuestBit(1215, true);
    OpenYAMM::Game::EventRuntimeState recoveredState = {};
    REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1358, recoveredState, &recoveredParty));
    REQUIRE_EQ(recoveredState.grantedItems.size(), 1u);
    CHECK_EQ(recoveredState.grantedItems.front().objectDescriptionId, 2170);
    REQUIRE_FALSE(recoveredState.messages.empty());
    CHECK_EQ(recoveredState.messages.back(), "Here is your missing item.");

    OpenYAMM::Game::Party heldParty = makeScriptedRegressionParty();
    heldParty.setQuestBit(1215, true);
    heldParty.setHeldItemForQueries(makeScriptedInventoryItem(2170));
    OpenYAMM::Game::EventRuntimeState heldState = {};
    REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1358, heldState, &heldParty));
    CHECK(heldState.grantedItems.empty());
    REQUIRE_FALSE(heldState.messages.empty());
    CHECK_EQ(heldState.messages.back(), "You never had it!");

    OpenYAMM::Game::Party completedParty = makeScriptedRegressionParty();
    completedParty.recordEverOwnedItem(2170);
    OpenYAMM::Game::EventRuntimeState completedState = {};
    REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1358, completedState, &completedParty));
    CHECK(completedState.grantedItems.empty());
    REQUIRE_FALSE(completedState.messages.empty());
    CHECK_EQ(completedState.messages.back(), "You never had it!");

    OpenYAMM::Game::Party letterParty = makeScriptedRegressionParty();
    letterParty.recordEverOwnedItem(2125);
    letterParty.setQuestBit(1105, true);
    OpenYAMM::Game::EventRuntimeState letterState = {};
    REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1358, letterState, &letterParty));
    REQUIRE_EQ(letterState.grantedItems.size(), 1u);
    CHECK_EQ(letterState.grantedItems.front().objectDescriptionId, 2125);

    OpenYAMM::Game::Party dischargePapersParty = makeScriptedRegressionParty();
    dischargePapersParty.recordEverOwnedItem(2128);
    dischargePapersParty.setQuestBit(1211, true);
    OpenYAMM::Game::EventRuntimeState dischargePapersState = {};
    REQUIRE(eventRuntime.executeEventById(
        std::nullopt,
        globalEventProgram,
        1358,
        dischargePapersState,
        &dischargePapersParty));
    REQUIRE_EQ(dischargePapersState.grantedItems.size(), 1u);
    CHECK_EQ(dischargePapersState.grantedItems.front().objectDescriptionId, 2128);

    OpenYAMM::Game::Party kilburnParty = makeScriptedRegressionParty();
    kilburnParty.recordEverOwnedItem(2119);
    kilburnParty.setQuestBit(1110, true);
    OpenYAMM::Game::EventRuntimeState kilburnState = {};
    REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1358, kilburnState, &kilburnParty));
    REQUIRE_EQ(kilburnState.grantedItems.size(), 1u);
    CHECK_EQ(kilburnState.grantedItems.front().objectDescriptionId, 2119);

    OpenYAMM::Game::Party kilburnLegacyProofParty = makeScriptedRegressionParty();
    kilburnLegacyProofParty.setQuestBit(1110, true);
    kilburnLegacyProofParty.setQuestBit(1206, true);
    OpenYAMM::Game::EventRuntimeState kilburnLegacyProofState = {};
    REQUIRE(eventRuntime.executeEventById(
        std::nullopt,
        globalEventProgram,
        1358,
        kilburnLegacyProofState,
        &kilburnLegacyProofParty));
    REQUIRE_EQ(kilburnLegacyProofState.grantedItems.size(), 1u);
    CHECK_EQ(kilburnLegacyProofState.grantedItems.front().objectDescriptionId, 2119);

    OpenYAMM::Game::Party kilburnNeverOwnedParty = makeScriptedRegressionParty();
    kilburnNeverOwnedParty.setQuestBit(1110, true);
    OpenYAMM::Game::EventRuntimeState kilburnNeverOwnedState = {};
    REQUIRE(eventRuntime.executeEventById(
        std::nullopt,
        globalEventProgram,
        1358,
        kilburnNeverOwnedState,
        &kilburnNeverOwnedParty));
    CHECK(kilburnNeverOwnedState.grantedItems.empty());
}

TEST_CASE("seer lost item tables compile for mm7 and mm8")
{
    struct Case
    {
        const char *pWorldId = nullptr;
        uint16_t eventId = 0;
        uint32_t itemId = 0;
        uint32_t qbitId = 0;
    };

    constexpr std::array<Case, 2> Cases = {{
        {"mm7", 889, 1477, 746},
        {"mm8", 705, 662, 224},
    }};

    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportLua.has_value());

    for (const Case &testCase : Cases)
    {
        const std::filesystem::path commonPath =
            sourceRoot / "assets_dev/worlds" / testCase.pWorldId / "events/common"
            / (std::string(testCase.pWorldId) + "_common.lua");
        const std::optional<std::string> commonLua = readSourceTextFile(commonPath);
        REQUIRE(commonLua.has_value());

        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
            OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
                *supportLua + "\n\n" + *commonLua,
                "@events/common/" + std::string(testCase.pWorldId) + "_common.lua",
                OpenYAMM::Game::ScriptedEventScope::Global,
                error);
        REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());
        REQUIRE(globalEventProgram->hasEvent(testCase.eventId));

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.recordEverOwnedItem(testCase.itemId);
        party.setQuestBit(testCase.qbitId, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            testCase.eventId,
            runtimeState,
            &party));
        REQUIRE_EQ(runtimeState.grantedItems.size(), 1u);
        CHECK_EQ(runtimeState.grantedItems.front().objectDescriptionId, testCase.itemId);
    }
}

TEST_CASE("mm6 new sorpigal tree event stores decoration sprite override")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> oute3Lua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps/oute3.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(oute3Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *oute3Lua,
            "@events/maps/oute3.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 113, runtimeState, &party, nullptr));

    const auto overrideIterator = runtimeState.spriteOverrides.find(300);
    REQUIRE(overrideIterator != runtimeState.spriteOverrides.end());
    CHECK_FALSE(overrideIterator->second.hidden);
    REQUIRE(overrideIterator->second.textureName.has_value());
    CHECK_EQ(*overrideIterator->second.textureName, "6tree06");
}

TEST_CASE("mm6 New Sorpigal obelisk applies autonote on press-any-key continuation")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    const std::optional<std::string> outa1Lua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps/outa1.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(outa1Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *commonLua + "\n\n" + *outa1Lua,
            "@events/maps/outa1.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 210, runtimeState, &party, nullptr));
    REQUIRE(runtimeState.pendingInputPrompt.has_value());
    CHECK_EQ(
        runtimeState.pendingInputPrompt->kind,
        OpenYAMM::Game::EventRuntimeState::PendingInputPrompt::Kind::PressAnyKey);
    CHECK_EQ(runtimeState.pendingInputPrompt->eventId, 210u);
    CHECK_EQ(runtimeState.pendingInputPrompt->continueStep, 2u);
    CHECK_FALSE(party.hasQuestBit(1384));

    constexpr uint32_t ObeliskAutonoteVariable = (442u << 16) | 0x00e1u;
    CHECK(runtimeState.variables.find(ObeliskAutonoteVariable) == runtimeState.variables.end());

    runtimeState.pendingInputPrompt.reset();
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 210, runtimeState, &party, nullptr, 2));

    CHECK(party.hasQuestBit(1384));
    const auto autonoteIt = runtimeState.variables.find(ObeliskAutonoteVariable);
    REQUIRE(autonoteIt != runtimeState.variables.end());
    CHECK_EQ(autonoteIt->second, 442);
    REQUIRE_EQ(runtimeState.portraitFxRequests.size(), 1u);
    CHECK_EQ(runtimeState.portraitFxRequests.front().kind, OpenYAMM::Game::PortraitFxEventKind::AutoNote);
}

TEST_CASE("map Lua overlays can remove and replace generated events")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");

    REQUIRE(supportLua.has_value());

    const std::string luaSource =
        *supportLua
        + R"lua(

SetMapMetadata({
    onLoad = {10, 11},
    onLeave = {10},
    openedChestIds = {
        [10] = {1},
    },
    contextActions = {
        [10] = { kind = "open_chest", source = "opcode", chestIds = {1} },
        [11] = { kind = "open_door", source = "title" },
    },
    timers = {
        { eventId = 10, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
    },
})

RegisterEvent(10, "Generated", function()
end, "Generated hint")

RegisterEvent(11, "Kept", function()
end, "Kept hint")

RemoveMapEvent(10)
ReplaceMapEvent(11, "Overlay", function()
end, "Overlay hint")

)lua";

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            luaSource,
            "@events/maps/test_overlay.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    CHECK_FALSE(localEventProgram->hasEvent(10));
    CHECK_FALSE(localEventProgram->getHint(10).has_value());
    CHECK(localEventProgram->getOpenedChestIds(10).empty());
    CHECK_FALSE(localEventProgram->getContextActionMetadata(10).has_value());
    CHECK(std::find(
        localEventProgram->onLoadEventIds().begin(),
        localEventProgram->onLoadEventIds().end(),
        10) == localEventProgram->onLoadEventIds().end());
    CHECK(std::find(
        localEventProgram->onLeaveEventIds().begin(),
        localEventProgram->onLeaveEventIds().end(),
        10) == localEventProgram->onLeaveEventIds().end());

    bool hasRemovedTimer = false;

    for (const OpenYAMM::Game::ScriptedEventProgram::TimerTrigger &timer : localEventProgram->timerTriggers())
    {
        if (timer.eventId == 10)
        {
            hasRemovedTimer = true;
        }
    }

    CHECK_FALSE(hasRemovedTimer);
    CHECK(localEventProgram->hasEvent(11));
    const std::optional<std::string> replacementSummary = localEventProgram->summarizeEvent(11);
    const std::optional<std::string> replacementHint = localEventProgram->getHint(11);
    REQUIRE(replacementSummary.has_value());
    REQUIRE(replacementHint.has_value());
    CHECK_EQ(*replacementSummary, "Overlay");
    CHECK_EQ(*replacementHint, "Overlay hint");
    CHECK_FALSE(localEventProgram->getContextActionMetadata(11).has_value());
}

TEST_CASE("scripted event program reads context action metadata")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");

    REQUIRE(supportLua.has_value());

    const std::string luaSource =
        *supportLua
        + R"lua(

SetMapMetadata({
    contextActions = {
        [50] = {
            kind = "leave_dungeon",
            source = "opcode",
            targetMap = "outd3.odm",
            targetName = "Castle Ironfist",
            houseId = 123,
            chestIds = {2, 2, 1},
            hidden = true,
        },
    },
})

RegisterEvent(50, "Exit", function()
end)

)lua";

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            luaSource,
            "@events/maps/context_action.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    const std::optional<OpenYAMM::Game::ScriptedEventProgram::ContextActionMetadata> metadata =
        localEventProgram->getContextActionMetadata(50);

    REQUIRE(metadata.has_value());
    CHECK_EQ(metadata->kind, "leave_dungeon");
    CHECK_EQ(metadata->source, "opcode");
    REQUIRE(metadata->targetMap.has_value());
    REQUIRE(metadata->targetName.has_value());
    REQUIRE(metadata->houseId.has_value());
    CHECK_EQ(*metadata->targetMap, "outd3.odm");
    CHECK_EQ(*metadata->targetName, "Castle Ironfist");
    CHECK_EQ(*metadata->houseId, 123u);
    CHECK_EQ(metadata->chestIds, std::vector<uint32_t>({1, 2}));
    CHECK(metadata->hidden);
}

TEST_CASE("event runtime runs global chest open hooks for opened chest ids")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");

    REQUIRE(supportLua.has_value());

    const std::string localLuaSource =
        *supportLua
        + R"lua(

RegisterEvent(10, "Open test chest", function()
    evt.OpenChest(5)
end)

)lua";

    const std::string globalLuaSource =
        *supportLua
        + R"lua(

RegisterGlobalChestOpenHook(65000, "Global chest hook", function(context)
    evt.SetGlobalVar("Test.ChestOpenHookChestId", context.chestId)
    evt.EnsureChestItem(context.chestId, 772, 0, 0)
end)

)lua";

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            localLuaSource,
            "@events/maps/test_chest_open.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            globalLuaSource,
            "@events/Global.lua",
            OpenYAMM::Game::ScriptedEventScope::Global,
            error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(localEventProgram, globalEventProgram, 10, runtimeState, &party));
    REQUIRE_EQ(runtimeState.openedChestIds.size(), 1u);
    CHECK_EQ(runtimeState.openedChestIds.front(), 5u);
    CHECK_EQ(runtimeState.namedGlobalVars["Test.ChestOpenHookChestId"], 5);
    REQUIRE(runtimeState.chestItemRequests.contains(5));
    REQUIRE_FALSE(runtimeState.chestItemRequests.at(5).empty());
    CHECK_EQ(runtimeState.chestItemRequests.at(5).front().itemId, 772u);
}

TEST_CASE("mm7 lincoln mmmerge supplement registers containment actors on load")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d23", "7d23_mmmerge", error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
    CHECK(localEventProgram->hasEvent(65023));
    CHECK(std::find(
        localEventProgram->onLoadEventIds().begin(),
        localEventProgram->onLoadEventIds().end(),
        65023) != localEventProgram->onLoadEventIds().end());

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState));
    CHECK_EQ(
        runtimeState.actorGroupClearMasks[56] & static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile),
        static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile));
    CHECK_EQ(
        runtimeState.actorGroupSetMasks[56] & static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Invisible));
}

TEST_CASE("mm7 phase1 mmmerge map overlays compile and expose expected event ids")
{
    struct Case
    {
        const char *pBaseName = nullptr;
        const char *pOverlayName = nullptr;
        std::vector<uint16_t> eventIds;
        std::vector<uint16_t> onLoadEventIds;
    };

    const std::array<Case, 24> Cases = {{
        {"7out01", "7out01_mmmerge", {65001}, {}},
        {"7out02", "7out02_mmmerge", {37, 301, 65002, 65003}, {65002}},
        {"7out03", "7out03_mmmerge", {65004, 65005}, {65005}},
        {"7out04", "7out04_mmmerge", {401, 503, 504}, {401}},
        {"7out05", "7out05_mmmerge", {65005, 65006}, {65005}},
        {"7out13", "7out13_mmmerge", {82}, {}},
        {"7out15", "7out15_mmmerge", {65016, 65017, 65018, 65019}, {65018}},
        {"7d08", "7d08_mmmerge", {376}, {}},
        {"7d23", "7d23_mmmerge", {501, 65023}, {65023}},
        {"7d24", "7d24_mmmerge", {416, 65024}, {}},
        {"7d25", "7d25_mmmerge", {65025}, {65025}},
        {"7d27", "7d27_mmmerge", {376}, {}},
        {"7d29", "7d29_mmmerge", {376, 377, 65029, 65030}, {377}},
        {"7d30", "7d30_mmmerge", {416}, {}},
        {"d03", "d03_mmmerge", {5}, {}},
        {"7d34", "7d34_mmmerge", {376, 377, 378, 379, 380, 381, 382}, {}},
        {"7d36", "7d36_mmmerge", {501}, {}},
        {"7d37", "7d37_mmmerge", {376}, {}},
        {"out11", "out11_mmmerge", {501}, {}},
        {"out12", "out12_mmmerge", {65012}, {65012}},
        {"out09", "out09_mmmerge", {6, 65009, 65010}, {65009}},
        {"out14", "out14_mmmerge", {65014}, {}},
        {"7nwc", "7nwc_mmmerge", {501}, {}},
        {"mdt15", "mdt15_mmmerge", {65015}, {}},
    }};

    for (const Case &testCase : Cases)
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, testCase.pBaseName, testCase.pOverlayName, error);
        INFO(testCase.pOverlayName);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        for (uint16_t eventId : testCase.eventIds)
        {
            CHECK(localEventProgram->hasEvent(eventId));
        }

        for (uint16_t eventId : testCase.onLoadEventIds)
        {
            CHECK(std::find(
                localEventProgram->onLoadEventIds().begin(),
                localEventProgram->onLoadEventIds().end(),
                eventId) != localEventProgram->onLoadEventIds().end());
        }
    }

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm7GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());

    for (uint16_t eventId :
        {513, 514, 769, 783, 858, 859, 860, 861, 862, 863, 864, 865, 875, 876, 884, 885, 886, 891, 893,
            920, 922, 65070, 65071})
    {
        CHECK(globalEventProgram->hasEvent(eventId));
    }
}

TEST_CASE("mm8 mmmerge map overlays compile and expose expected event ids")
{
    struct Case
    {
        const char *pBaseName = nullptr;
        const char *pOverlayName = nullptr;
        std::vector<uint16_t> eventIds;
        std::vector<uint16_t> onLoadEventIds;
    };

    const std::array<Case, 14> Cases = {{
        {"d06", "d06_mmmerge", {451}, {}},
        {"d07", "d07_mmmerge", {1, 901}, {}},
        {"d19", "d19_mmmerge", {15, 131}, {}},
        {"d24", "d24_mmmerge", {901}, {901}},
        {"d34", "d34_mmmerge", {451}, {}},
        {"d38", "d38_mmmerge", {901}, {901}},
        {"d39", "d39_mmmerge", {901}, {901}},
        {"d42", "d42_mmmerge", {501}, {}},
        {"out01", "out01_mmmerge", {901, 902}, {901}},
        {"out02", "out02_mmmerge", {504}, {}},
        {"out05", "out05_mmmerge", {131}, {}},
        {"out07", "out07_mmmerge", {132, 133, 134, 135, 136, 455, 500, 901, 902}, {901}},
        {"out13", "out13_mmmerge", {451, 452}, {}},
        {"pbp", "pbp_mmmerge", {502, 503, 504, 505}, {}},
    }};

    for (const Case &testCase : Cases)
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, testCase.pBaseName, testCase.pOverlayName, error);
        INFO(testCase.pOverlayName);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        for (uint16_t eventId : testCase.eventIds)
        {
            CHECK(localEventProgram->hasEvent(eventId));
        }

        for (uint16_t eventId : testCase.onLoadEventIds)
        {
            CHECK(std::find(
                localEventProgram->onLoadEventIds().begin(),
                localEventProgram->onLoadEventIds().end(),
                eventId) != localEventProgram->onLoadEventIds().end());
        }
    }
}

TEST_CASE("mm8 mmmerge reusable travel keys preserve opened map state")
{
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d06", "d06_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party keyedParty = makeScriptedRegressionParty();
        keyedParty.grantItem(619);
        OpenYAMM::Game::EventRuntimeState keyedState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 451, keyedState, &keyedParty));
        CHECK(keyedParty.hasQuestBit(214));
        const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pKeyedMove = pendingMapMove(keyedState);
        REQUIRE(pKeyedMove != nullptr);
        CHECK_EQ(pKeyedMove->mapName, std::optional<std::string>("d34.blv"));
        CHECK_EQ(pKeyedMove->x, -2416);
        CHECK_EQ(pKeyedMove->y, 1850);
        CHECK_EQ(pKeyedMove->z, -687);

        OpenYAMM::Game::Party reopenedParty = makeScriptedRegressionParty();
        reopenedParty.setQuestBit(214, true);
        OpenYAMM::Game::EventRuntimeState reopenedState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 451, reopenedState, &reopenedParty));
        const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pReopenedMove = pendingMapMove(reopenedState);
        REQUIRE(pReopenedMove != nullptr);
        CHECK_EQ(pReopenedMove->mapName, std::optional<std::string>("d34.blv"));

        OpenYAMM::Game::Party lockedParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState lockedState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 451, lockedState, &lockedParty));
        CHECK_FALSE(lockedState.pendingMapMove.has_value());
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d34", "d34_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 451, runtimeState, &party));
        const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pMove = pendingMapMove(runtimeState);
        REQUIRE(pMove != nullptr);
        CHECK_EQ(pMove->mapName, std::optional<std::string>("d06.blv"));
        CHECK_EQ(pMove->x, 7097);
        CHECK_EQ(pMove->y, -1117);
        CHECK_EQ(pMove->z, -639);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out02", "out02_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party keyedParty = makeScriptedRegressionParty();
        keyedParty.grantItem(610);
        OpenYAMM::Game::EventRuntimeState keyedState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 504, keyedState, &keyedParty));
        CHECK_EQ(keyedState.namedMapVars["CrystalOpened"], 1);
        const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pKeyedMove = pendingMapMove(keyedState);
        REQUIRE(pKeyedMove != nullptr);
        CHECK_EQ(pKeyedMove->mapName, std::optional<std::string>("d10.blv"));
        CHECK_EQ(pKeyedMove->x, -1024);
        CHECK_EQ(pKeyedMove->y, -1626);
        CHECK_EQ(pKeyedMove->z, 0);

        OpenYAMM::Game::Party reopenedParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState reopenedState = {};
        reopenedState.namedMapVars["CrystalOpened"] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 504, reopenedState, &reopenedParty));
        const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pReopenedMove = pendingMapMove(reopenedState);
        REQUIRE(pReopenedMove != nullptr);
        CHECK_EQ(pReopenedMove->mapName, std::optional<std::string>("d10.blv"));
    }
}

TEST_CASE("mm8 mmmerge elemental prisons stay reusable after ring of keys")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "pbp", "pbp_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    struct PrisonCase
    {
        uint16_t eventId = 0;
        const char *pFlag = nullptr;
        const char *pMapName = nullptr;
        int32_t x = 0;
        int32_t y = 0;
        int32_t z = 0;
    };

    const std::array<PrisonCase, 4> Cases = {{
        {502, "AirPrisonOpen", "d36.blv", -733, -2563, -1051},
        {503, "FirePrisonOpen", "d37.blv", -128, 896, 1},
        {504, "WaterPrisonOpen", "d38.blv", 2393, -10664, 1},
        {505, "EarthPrisonOpen", "d39.blv", -2, 118, 1},
    }};

    OpenYAMM::Game::EventRuntime eventRuntime = {};

    for (const PrisonCase &testCase : Cases)
    {
        INFO(testCase.pFlag);

        OpenYAMM::Game::Party lockedParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState lockedState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            testCase.eventId,
            lockedState,
            &lockedParty));
        CHECK_FALSE(lockedState.pendingMapMove.has_value());

        OpenYAMM::Game::Party keyedParty = makeScriptedRegressionParty();
        keyedParty.grantItem(629);
        OpenYAMM::Game::EventRuntimeState keyedState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            testCase.eventId,
            keyedState,
            &keyedParty));
        CHECK_EQ(keyedState.namedMapVars[testCase.pFlag], 1);
        const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pKeyedMove = pendingMapMove(keyedState);
        REQUIRE(pKeyedMove != nullptr);
        CHECK_EQ(pKeyedMove->mapName, std::optional<std::string>(testCase.pMapName));
        CHECK_EQ(pKeyedMove->x, testCase.x);
        CHECK_EQ(pKeyedMove->y, testCase.y);
        CHECK_EQ(pKeyedMove->z, testCase.z);

        OpenYAMM::Game::Party reopenedParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState reopenedState = {};
        reopenedState.namedMapVars[testCase.pFlag] = 1;
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            testCase.eventId,
            reopenedState,
            &reopenedParty));
        const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pReopenedMove = pendingMapMove(reopenedState);
        REQUIRE(pReopenedMove != nullptr);
        CHECK_EQ(pReopenedMove->mapName, std::optional<std::string>(testCase.pMapName));
    }
}

TEST_CASE("mm8 mmmerge d19 dyson and skeleton transformer branches apply")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d19", "d19_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};

    OpenYAMM::Game::Party alliedParty = makeScriptedRegressionParty();
    alliedParty.setQuestBit(20, true);
    OpenYAMM::Game::EventRuntimeState alliedState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 15, alliedState, &alliedParty));
    CHECK_EQ(alliedState.lastAffectedMechanismIds, std::vector<uint32_t>{5});

    OpenYAMM::Game::Party invisibleParty = makeScriptedRegressionParty();
    invisibleParty.applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::Invisibility,
        300.0f,
        0,
        0,
        0,
        OpenYAMM::Game::SkillMastery::Normal,
        0);
    OpenYAMM::Game::EventRuntimeState invisibleState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 15, invisibleState, &invisibleParty));
    CHECK(invisibleState.lastAffectedMechanismIds.empty());
    CHECK_FALSE(invisibleState.pendingDialogueContext.has_value());

    OpenYAMM::Game::Party blockedParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState blockedState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 15, blockedState, &blockedParty));
    CHECK_EQ(blockedState.npcGreetingOverrides[45], 107u);
    REQUIRE(blockedState.pendingDialogueContext.has_value());
    CHECK_EQ(blockedState.pendingDialogueContext->sourceId, 45u);

    OpenYAMM::Game::Party transformerParty = makeScriptedRegressionParty();
    transformerParty.setQuestBit(26, true);
    OpenYAMM::Game::EventRuntimeState transformerState = {};
    transformerState.mapVars[21] = 15;
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        131,
        transformerState,
        &transformerParty));
    CHECK(transformerParty.hasQuestBit(27));
    CHECK_EQ(
        transformerState.facetSetMasks[30] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
    CHECK_EQ(
        transformerState.facetSetMasks[30] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable));
}

TEST_CASE("mm8 mmmerge out07 statues dimension door and duplicate gems apply")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out07", "out07_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};

    const std::optional<OpenYAMM::Game::ScriptedEventProgram::ContextActionMetadata> cauriStatueMetadata =
        localEventProgram->getContextActionMetadata(132);
    REQUIRE(cauriStatueMetadata.has_value());
    CHECK_EQ(cauriStatueMetadata->kind, "stone_to_flesh");
    CHECK_EQ(cauriStatueMetadata->source, "spell");

    OpenYAMM::Game::Party interactSpellParty = makeScriptedRegressionParty();
    REQUIRE(interactSpellParty.member(0) != nullptr);
    CHECK(interactSpellParty.member(0)->learnSpell(40));
    OpenYAMM::Game::EventRuntimeState interactSpellState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        132,
        interactSpellState,
        &interactSpellParty));
    CHECK_FALSE(interactSpellParty.hasQuestBit(40));
    CHECK_FALSE(interactSpellParty.hasQuestBit(430));
    CHECK_FALSE(interactSpellState.spriteOverrides[20].hidden);
    CHECK_FALSE(interactSpellState.pendingDialogueContext.has_value());

    OpenYAMM::Game::Party spellParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState spellState = {};
    spellState.activeEventSpellId = 40;
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 132, spellState, &spellParty));
    CHECK(spellParty.hasQuestBit(40));
    CHECK(spellParty.hasQuestBit(430));
    CHECK(spellState.spriteOverrides[20].hidden);
    REQUIRE(spellState.pendingDialogueContext.has_value());
    CHECK_EQ(spellState.pendingDialogueContext->sourceId, 42u);

    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pOut07 = loadCachedOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "out07.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pOut07 != nullptr);
    REQUIRE(pOut07->outdoorMapData.has_value());
    REQUIRE_GT(pOut07->outdoorMapData->entities.size(), 1418u);
    const OpenYAMM::Game::OutdoorEntity &cauriStatueEntity = pOut07->outdoorMapData->entities[1418];
    CHECK_EQ(cauriStatueEntity.eventIdPrimary, 20u);
    CHECK_EQ(cauriStatueEntity.eventIdSecondary, 132u);
    CHECK_EQ(cauriStatueEntity.spriteOverrideKey(1418), 20u);

    OpenYAMM::Game::Party scrollParty = makeScriptedRegressionParty();
    scrollParty.grantItem(339);
    OpenYAMM::Game::EventRuntimeState scrollState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 133, scrollState, &scrollParty));
    CHECK_EQ(scrollParty.inventoryItemCount(339), 0);
    CHECK(scrollState.spriteOverrides[21].hidden);
    REQUIRE(scrollState.pendingDialogueContext.has_value());
    CHECK_EQ(scrollState.pendingDialogueContext->sourceId, 46u);

    OpenYAMM::Game::Party gemParty = makeScriptedRegressionParty();
    gemParty.grantItem(2056);
    OpenYAMM::Game::EventRuntimeState gemState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 455, gemState, &gemParty));
    CHECK_EQ(gemParty.inventoryItemCount(2056), 0);
    CHECK(
        std::find(gemState.grantedItemIds.begin(), gemState.grantedItemIds.end(), 656)
        != gemState.grantedItemIds.end());

    OpenYAMM::Game::Party sapphireParty = makeScriptedRegressionParty();
    sapphireParty.grantItem(2065);
    const int initialGold = sapphireParty.gold();
    OpenYAMM::Game::EventRuntimeState sapphireState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 455, sapphireState, &sapphireParty));
    CHECK_EQ(sapphireParty.inventoryItemCount(2065), 0);
    CHECK_EQ(sapphireParty.gold(), initialGold + 2000);

    OpenYAMM::Game::Party dimensionDoorParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState dimensionDoorState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        500,
        dimensionDoorState,
        &dimensionDoorParty));
    CHECK(dimensionDoorState.pendingDimensionDoorOverlay);
    REQUIRE(dimensionDoorState.lastActivationResult.has_value());
    CHECK_EQ(*dimensionDoorState.lastActivationResult, "You feel high magic presence here.");
}

TEST_CASE("mm8 mmmerge out13 cannon sequence advances through every reusable stage")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out13", "out13_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    party.grantItem(662);
    party.setQuestBit(224, true);
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 451, runtimeState, &party));
    CHECK_EQ(party.inventoryItemCount(662), 0);
    CHECK_FALSE(party.hasQuestBit(224));
    CHECK_EQ(runtimeState.mapVars[41], 1u);
    REQUIRE_FALSE(runtimeState.pendingSounds.empty());
    CHECK_EQ(runtimeState.pendingSounds.back().soundId, 473u);

    RecordingSceneEventContext sceneContext = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        452,
        runtimeState,
        &party,
        &sceneContext));
    CHECK_EQ(runtimeState.mapVars[41], 2u);
    REQUIRE_EQ(sceneContext.castSpellCalls.size(), 8u);
    CHECK_EQ(sceneContext.castSpellCalls.front().spellId, 6u);
    REQUIRE_FALSE(runtimeState.pendingSounds.empty());
    CHECK_EQ(runtimeState.pendingSounds.back().soundId, 472u);

    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        452,
        runtimeState,
        &party,
        &sceneContext));
    CHECK_EQ(runtimeState.mapVars[41], 3u);
    REQUIRE_EQ(sceneContext.castSpellCalls.size(), 30u);
    CHECK_EQ(sceneContext.castSpellCalls[8].spellId, 9u);
    CHECK_EQ(sceneContext.castSpellCalls[19].spellId, 18u);
    CHECK_EQ(sceneContext.castSpellCalls[26].spellId, 43u);

    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        452,
        runtimeState,
        &party,
        &sceneContext));
    CHECK_EQ(runtimeState.mapVars[41], 0u);
    CHECK(party.hasQuestBit(37));
    CHECK_EQ(runtimeState.npcHouseOverrides[64], 899u);
    CHECK_EQ(runtimeState.npcHouseOverrides[20], 900u);
    CHECK_EQ(runtimeState.npcHouseOverrides[21], 900u);
    CHECK_EQ(
        runtimeState.facetClearMasks[31] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
    CHECK_EQ(
        runtimeState.facetSetMasks[30] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
}

TEST_CASE("mm8 mmmerge arena exit and dimension door tile hooks apply")
{
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d42", "d42_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        struct ArenaCase
        {
            uint32_t continentId = 0;
            const char *pMapName = nullptr;
            int32_t x = 0;
            int32_t y = 0;
            int32_t z = 0;
        };

        const std::array<ArenaCase, 3> Cases = {{
            {1, "out02.odm", 17091, -12524, 1},
            {2, "7out02.odm", -5692, 11137, 1},
            {3, "outd3.odm", 14305, 2696, 96},
        }};

        for (const ArenaCase &testCase : Cases)
        {
            INFO(testCase.pMapName);
            OpenYAMM::Game::EventRuntime eventRuntime = {};
            OpenYAMM::Game::Party party = makeScriptedRegressionParty();
            OpenYAMM::Game::EventRuntimeState runtimeState = {};
            runtimeState.activeHistoryContinentId = testCase.continentId;
            REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 501, runtimeState, &party));
            const OpenYAMM::Game::EventRuntimeState::PendingMapMove *pMove = pendingMapMove(runtimeState);
            REQUIRE(pMove != nullptr);
            CHECK_EQ(pMove->mapName, std::optional<std::string>(testCase.pMapName));
            CHECK_EQ(pMove->x, testCase.x);
            CHECK_EQ(pMove->y, testCase.y);
            CHECK_EQ(pMove->z, testCase.z);
        }
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out01", "out01_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK(party.hasQuestBit(185));
        CHECK_EQ(runtimeState.namedMapVars["DimensionDoorTileActive"], 0);

        RecordingGameplayWorldContext sceneContext = {};
        sceneContext.setPartyPosition(-512.0f, 2560.0f, 0.0f);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            902,
            runtimeState,
            &party,
            &sceneContext));
        CHECK(runtimeState.pendingDimensionDoorOverlay);
        CHECK_EQ(runtimeState.namedMapVars["DimensionDoorTileActive"], 1);

        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            902,
            runtimeState,
            &party,
            &sceneContext));
        CHECK_FALSE(runtimeState.pendingDimensionDoorOverlay);
        CHECK_EQ(runtimeState.namedMapVars["DimensionDoorTileActive"], 1);

        sceneContext.setPartyPosition(0.0f, 0.0f, 0.0f);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            902,
            runtimeState,
            &party,
            &sceneContext));
        CHECK_FALSE(runtimeState.pendingDimensionDoorOverlay);
        CHECK_EQ(runtimeState.namedMapVars["DimensionDoorTileActive"], 0);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out07", "out07_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(runtimeState.namedMapVars["DimensionDoorTileActive"], 0);

        RecordingGameplayWorldContext sceneContext = {};
        sceneContext.setPartyPosition(-10752.0f, -17408.0f, 0.0f);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            902,
            runtimeState,
            &party,
            &sceneContext));
        CHECK(runtimeState.pendingDimensionDoorOverlay);
        CHECK_EQ(runtimeState.namedMapVars["DimensionDoorTileActive"], 1);
    }
}

TEST_CASE("mm8 mmmerge on-load and kill-tracker overlays apply runtime state")
{
    const uint32_t actorInvisibleBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Invisible);
    const uint32_t actorHostileBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile);

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d24", "d24_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(23, true);
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(runtimeState.actorGroupSetMasks[0] & actorInvisibleBit, actorInvisibleBit);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d38", "d38_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party pendingParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState pendingState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            pendingState,
            &pendingParty));
        CHECK_EQ(pendingState.npcHouseOverrides[24], 662u);

        OpenYAMM::Game::Party completedParty = makeScriptedRegressionParty();
        completedParty.setQuestBit(53, true);
        OpenYAMM::Game::EventRuntimeState completedState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            completedState,
            &completedParty));
        CHECK_EQ(completedState.npcHouseOverrides.count(24), 0u);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d39", "d39_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party pendingParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState pendingState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            pendingState,
            &pendingParty));
        CHECK_EQ(pendingState.npcHouseOverrides[25], 663u);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d07", "d07_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(10, true);
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        RecordingSceneEventContext sceneContext = {};
        sceneContext.killedGroupResults[8] = true;
        sceneContext.setCurrentGameMinutes(100.0f);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            901,
            runtimeState,
            &party,
            &sceneContext));
        CHECK_EQ(runtimeState.namedMapVars["WereratsMad"], 1);
        CHECK_EQ(runtimeState.namedMapVars["WereratsMadUntil"], 1540);

        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            1,
            runtimeState,
            &party,
            &sceneContext));
        CHECK_EQ(runtimeState.actorGroupSetMasks[8] & actorHostileBit, actorHostileBit);
        CHECK_EQ(runtimeState.actorGroupSetMasks[10] & actorHostileBit, actorHostileBit);
        CHECK_EQ(runtimeState.actorGroupSetMasks[11] & actorHostileBit, actorHostileBit);
        CHECK_EQ(runtimeState.actorGroupSetMasks[11] & actorInvisibleBit, actorInvisibleBit);

        sceneContext.setCurrentGameMinutes(1540.0f);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            1,
            runtimeState,
            &party,
            &sceneContext));
        CHECK_EQ(runtimeState.namedMapVars["WereratsMad"], 0);
        CHECK_EQ(runtimeState.actorGroupClearMasks[8] & actorHostileBit, actorHostileBit);
        CHECK_EQ(runtimeState.actorGroupClearMasks[10] & actorHostileBit, actorHostileBit);
        CHECK_EQ(runtimeState.actorGroupClearMasks[11] & actorHostileBit, actorHostileBit);
    }

    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        const std::optional<std::string> supportLua =
            readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
        const std::optional<std::string> commonLua =
            readSourceTextFile(sourceRoot / "assets_dev/worlds/mm8/events/common/mm8_common.lua");
        const std::optional<std::string> overlayLua =
            readSourceTextFile(sourceRoot / "assets_dev/worlds/mm8/events/maps/out05_mmmerge.lua");
        REQUIRE(supportLua.has_value());
        REQUIRE(commonLua.has_value());
        REQUIRE(overlayLua.has_value());

        const std::string baseLua = "RegisterEvent(131, \"Synthetic base event\", function()\nend)\n";
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
                *supportLua + "\n\n" + *commonLua + "\n\n" + baseLua + "\n\n" + *overlayLua,
                "@tests/mm8_out05_mmmerge_synthetic.lua",
                OpenYAMM::Game::ScriptedEventScope::Map,
                error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        RecordingSceneEventContext sceneContext = {};
        sceneContext.killedGroupResults[189] = true;
        sceneContext.killedGroupResults[190] = true;
        sceneContext.killedGroupResults[191] = true;
        sceneContext.killedGroupResults[42] = true;
        sceneContext.killedGroupResults[43] = true;
        sceneContext.killedGroupResults[44] = true;
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            131,
            runtimeState,
            &party,
            &sceneContext));
        CHECK(party.hasQuestBit(155));
        CHECK(party.hasQuestBit(158));
    }
}

TEST_CASE("merged continent weather settings are applied to selected outdoor maps")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();

    OpenYAMM::Game::GameDataLoader gameDataLoader = {};
    REQUIRE(gameDataLoader.loadForHeadlessGameplay(mapLoader.assetFileSystem));
    REQUIRE(gameDataLoader.loadMapByFileNameForHeadlessGameplay(mapLoader.assetFileSystem, "out04.odm"));

    const std::optional<OpenYAMM::Game::MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();
    REQUIRE(selectedMap.has_value());
    REQUIRE(selectedMap->outdoorMapData.has_value());
    REQUIRE(selectedMap->outdoorMapDeltaData.has_value());
    REQUIRE(selectedMap->outdoorWeatherProfile.has_value());

    const OpenYAMM::Game::OutdoorWeatherProfile &profile = *selectedMap->outdoorWeatherProfile;
    CHECK(profile.mergedWeatherConfigured);
    CHECK_EQ(profile.mergedMapId, 4u);
    CHECK_FALSE(profile.mergedWeatherEnabled);
    CHECK_FALSE(profile.mergedRainEnabled);
    CHECK_FALSE(profile.mergedSnowEnabled);
    CHECK_EQ(profile.mergedRainChancePercent, 20);
    CHECK_EQ(profile.mergedSnowChancePercent, 15);
    CHECK_EQ(profile.mergedCustomSkyTextureName, "plansky3");
    REQUIRE_FALSE(profile.mergedSkyTextureNames.empty());
    CHECK_EQ(profile.mergedSkyTextureNames.front(), "plansky3");
    CHECK_EQ(selectedMap->outdoorMapData->skyTexture, "plansky3");
    CHECK_EQ(selectedMap->outdoorMapDeltaData->locationTime.skyTextureName, "plansky3");

    auto loadWeatherProfile =
        [&](const char *pMapFileName) -> OpenYAMM::Game::OutdoorWeatherProfile
        {
            OpenYAMM::Game::GameDataLoader loader = {};
            REQUIRE(loader.loadForHeadlessGameplay(mapLoader.assetFileSystem));
            REQUIRE(loader.loadMapByFileNameForHeadlessGameplay(mapLoader.assetFileSystem, pMapFileName));

            const std::optional<OpenYAMM::Game::MapAssetInfo> &mapInfo = loader.getSelectedMap();
            REQUIRE(mapInfo.has_value());
            REQUIRE(mapInfo->outdoorWeatherProfile.has_value());
            return *mapInfo->outdoorWeatherProfile;
        };

    const OpenYAMM::Game::OutdoorWeatherProfile tularean = loadWeatherProfile("7out04.odm");
    CHECK(tularean.mergedWeatherEnabled);
    CHECK(tularean.mergedRainEnabled);
    CHECK_FALSE(tularean.mergedSnowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile harmondale = loadWeatherProfile("7out02.odm");
    CHECK(harmondale.mergedWeatherEnabled);
    CHECK(harmondale.mergedRainEnabled);
    CHECK(harmondale.mergedSnowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile erathia = loadWeatherProfile("7out03.odm");
    CHECK(erathia.mergedWeatherEnabled);
    CHECK(erathia.mergedRainEnabled);
    CHECK(erathia.mergedSnowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile bracada = loadWeatherProfile("7out06.odm");
    CHECK_FALSE(bracada.mergedWeatherEnabled);
    CHECK_FALSE(bracada.mergedRainEnabled);
    CHECK_FALSE(bracada.mergedSnowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile nighon = loadWeatherProfile("out10.odm");
    CHECK(nighon.mergedWeatherEnabled);
    CHECK(nighon.mergedRainEnabled);
    CHECK(nighon.mergedSnowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile landOfTheGiants = loadWeatherProfile("out12.odm");
    CHECK(landOfTheGiants.mergedWeatherEnabled);
    CHECK(landOfTheGiants.mergedRainEnabled);
    CHECK(landOfTheGiants.mergedSnowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile kriegspire = loadWeatherProfile("outb1.odm");
    CHECK(kriegspire.mergedWeatherEnabled);
    CHECK(kriegspire.mergedRainEnabled);
    CHECK(kriegspire.mergedSnowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile frozenHighlands = loadWeatherProfile("outc1.odm");
    CHECK(frozenHighlands.mergedWeatherEnabled);
    CHECK(frozenHighlands.mergedRainEnabled);
    CHECK_FALSE(frozenHighlands.mergedSnowEnabled);
}

TEST_CASE("mm7 emerald island mmmerge tavern topics remove arcomage")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out01", "7out01_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
    hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::HouseTopicFilter;
    hookContext.houseId = 239;
    hookContext.houseServiceType = static_cast<uint32_t>(OpenYAMM::Game::HouseServiceType::Tavern);
    runtimeState.activeHookContext = hookContext;

    REQUIRE(eventRuntime.executeHooks(
        localEventProgram,
        std::nullopt,
        OpenYAMM::Game::EventRuntimeHookKind::HouseTopicFilter,
        runtimeState,
        &party));
    REQUIRE(runtimeState.activeHookContext.has_value());
    CHECK_EQ(
        runtimeState.activeHookContext->houseTopicActionIds,
        std::vector<uint32_t>{
            static_cast<uint32_t>(OpenYAMM::Game::HouseActionId::TavernRentRoom),
            static_cast<uint32_t>(OpenYAMM::Game::HouseActionId::TavernBuyFood),
            static_cast<uint32_t>(OpenYAMM::Game::HouseActionId::OpenLearnSkillsMenu),
        });
}

TEST_CASE("mm7 global mmmerge arcomage requires deck")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm7GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());

    auto executeArcomageClickHook =
        [&globalEventProgram](OpenYAMM::Game::Party &party, OpenYAMM::Game::HouseActionId actionId)
        {
            OpenYAMM::Game::EventRuntime eventRuntime = {};
            OpenYAMM::Game::EventRuntimeState runtimeState = {};
            OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
            hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::HouseTopicClick;
            hookContext.houseId = 239;
            hookContext.houseServiceType = static_cast<uint32_t>(OpenYAMM::Game::HouseServiceType::Tavern);
            hookContext.houseActionId = static_cast<uint32_t>(actionId);
            runtimeState.activeHookContext = hookContext;

            REQUIRE(eventRuntime.executeHooks(
                std::nullopt,
                globalEventProgram,
                OpenYAMM::Game::EventRuntimeHookKind::HouseTopicClick,
                runtimeState,
                &party));
            REQUIRE(runtimeState.activeHookContext.has_value());
            return *runtimeState.activeHookContext;
        };

    OpenYAMM::Game::Party partyWithoutDeck = makeScriptedRegressionParty();
    const OpenYAMM::Game::EventRuntimeState::ActiveHookContext submenuContext =
        executeArcomageClickHook(partyWithoutDeck, OpenYAMM::Game::HouseActionId::OpenTavernArcomageMenu);
    CHECK_FALSE(submenuContext.blocked);
    CHECK_FALSE(submenuContext.statusText.has_value());

    const OpenYAMM::Game::EventRuntimeState::ActiveHookContext blockedContext =
        executeArcomageClickHook(partyWithoutDeck, OpenYAMM::Game::HouseActionId::TavernArcomagePlay);
    CHECK(blockedContext.blocked);
    REQUIRE(blockedContext.statusText.has_value());
    CHECK_EQ(*blockedContext.statusText, "You must have your own card deck to play here.");

    OpenYAMM::Game::Party partyWithDeck = makeScriptedRegressionParty();
    REQUIRE(partyWithDeck.member(0) != nullptr);
    partyWithDeck.member(0)->inventory.push_back(makeScriptedInventoryItem(1453));
    const OpenYAMM::Game::EventRuntimeState::ActiveHookContext allowedContext =
        executeArcomageClickHook(partyWithDeck, OpenYAMM::Game::HouseActionId::OpenTavernArcomageMenu);
    CHECK_FALSE(allowedContext.blocked);
    CHECK_FALSE(allowedContext.statusText.has_value());
}

TEST_CASE("mm7 castle harmondale mmmerge local quest state")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d29", "7d29_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    const uint32_t hostileBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile);
    const uint32_t invisibleBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Invisible);

    auto hasFollower = [](const OpenYAMM::Game::EventRuntimeState &runtimeState, uint32_t npcId)
    {
        return std::find_if(
            runtimeState.hiredNpcFollowers.begin(),
            runtimeState.hiredNpcFollowers.end(),
            [npcId](const OpenYAMM::Game::EventRuntimeState::HiredNpcFollower &follower)
            {
                return follower.npcId == npcId;
            }) != runtimeState.hiredNpcFollowers.end();
    };

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(585, true);
        party.addHiredNpcFollower({395, 0, 0});
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.hiredNpcFollowers.push_back({395, 0, 0});

        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, runtimeState, &party));
        CHECK_FALSE(hasFollower(runtimeState, 395));
        CHECK_EQ(runtimeState.actorGroupSetMasks[57] & hostileBit, hostileBit);
        CHECK_EQ(runtimeState.actorGroupClearMasks[57] & invisibleBit, invisibleBit);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::RestFoodCost;
        hookContext.baseRestFoodCost = 2;
        runtimeState.activeHookContext = hookContext;

        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::RestFoodCost,
            runtimeState,
            &party));
        REQUIRE(runtimeState.activeHookContext.has_value());
        CHECK_FALSE(runtimeState.activeHookContext->restFoodCostOverride.has_value());

        party.setQuestBit(610, true);
        runtimeState.activeHookContext = hookContext;
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::RestFoodCost,
            runtimeState,
            &party));
        REQUIRE(runtimeState.activeHookContext.has_value());
        REQUIRE(runtimeState.activeHookContext->restFoodCostOverride.has_value());
        CHECK_EQ(*runtimeState.activeHookContext->restFoodCostOverride, 0);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.addGold(500);
        CHECK_EQ(party.depositGoldToBank(500), 500);
        party.setQuestBit(526, true);
        party.setQuestBit(693, true);
        party.setQuestBit(694, true);
        party.setQuestBit(695, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(runtimeState.actorGroupClearMasks[56] & hostileBit, 0u);
        CHECK_EQ(runtimeState.actorGroupSetMasks[56] & invisibleBit, 0u);
        CHECK_EQ(runtimeState.actorGroupSetMasks[60] & hostileBit, hostileBit);
        CHECK_EQ(runtimeState.actorGroupClearMasks[60] & invisibleBit, invisibleBit);
        CHECK_EQ(party.bankGold(), 0);
        CHECK_FALSE(party.hasQuestBit(693));
        CHECK_FALSE(party.hasQuestBit(694));
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(610, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(runtimeState.actorGroupClearMasks[56] & hostileBit, hostileBit);
        CHECK_EQ(runtimeState.actorGroupSetMasks[56] & invisibleBit, invisibleBit);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(695, true);
        party.setQuestBit(697, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        RecordingSceneEventContext sceneContext = {};
        sceneContext.killedGroupResults[60] = true;

        REQUIRE(eventRuntime.executeOnLeaveEvents(localEventProgram, std::nullopt, runtimeState, &party, &sceneContext));
        CHECK(party.hasQuestBit(696));
        CHECK(party.hasQuestBit(702));
        CHECK_FALSE(party.hasQuestBit(695));
    }
}

TEST_CASE("mm7 castle lambent and gloaming mmmerge faction gates")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> lambentProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d30", "7d30_mmmerge", error);
    REQUIRE_MESSAGE(lambentProgram.has_value(), error.c_str());

    error.clear();
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> gloamingProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d03", "d03_mmmerge", error);
    REQUIRE_MESSAGE(gloamingProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime(&OpenYAMM::Tests::regressionGameData().houseTable);

    auto executeGate =
        [&eventRuntime](
            const std::optional<OpenYAMM::Game::ScriptedEventProgram> &program,
            uint16_t eventId,
            OpenYAMM::Game::Party &party)
        {
            OpenYAMM::Game::EventRuntimeState runtimeState = {};
            RecordingSceneEventContext sceneContext = {};
            REQUIRE(eventRuntime.executeEventById(
                program,
                std::nullopt,
                eventId,
                runtimeState,
                &party,
                &sceneContext));
            return runtimeState;
        };

    {
        OpenYAMM::Game::Party noPathParty = makeScriptedRegressionParty();
        const OpenYAMM::Game::EventRuntimeState noPathState = executeGate(lambentProgram, 416, noPathParty);
        REQUIRE_FALSE(noPathState.statusMessages.empty());
        CHECK_EQ(noPathState.statusMessages.back(), "The Door is Locked");

        OpenYAMM::Game::Party darkParty = makeScriptedRegressionParty();
        darkParty.setQuestBit(612, true);
        const OpenYAMM::Game::EventRuntimeState darkState = executeGate(lambentProgram, 416, darkParty);
        REQUIRE_FALSE(darkState.statusMessages.empty());
        CHECK_EQ(darkState.statusMessages.back(), "The Door is Locked");

        OpenYAMM::Game::Party lightParty = makeScriptedRegressionParty();
        lightParty.setQuestBit(611, true);
        const OpenYAMM::Game::EventRuntimeState lightState = executeGate(lambentProgram, 416, lightParty);
        REQUIRE(lightState.pendingDialogueContext.has_value());
        CHECK_EQ(lightState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
        CHECK_EQ(lightState.pendingDialogueContext->sourceId, 220u);
    }

    {
        OpenYAMM::Game::Party noPathParty = makeScriptedRegressionParty();
        const OpenYAMM::Game::EventRuntimeState noPathState = executeGate(gloamingProgram, 5, noPathParty);
        REQUIRE_FALSE(noPathState.statusMessages.empty());
        CHECK_EQ(noPathState.statusMessages.back(), "The Door is Locked");

        OpenYAMM::Game::Party lightParty = makeScriptedRegressionParty();
        lightParty.setQuestBit(611, true);
        const OpenYAMM::Game::EventRuntimeState lightState = executeGate(gloamingProgram, 5, lightParty);
        REQUIRE_FALSE(lightState.statusMessages.empty());
        CHECK_EQ(lightState.statusMessages.back(), "The Door is Locked");

        OpenYAMM::Game::Party darkParty = makeScriptedRegressionParty();
        darkParty.setQuestBit(612, true);
        const OpenYAMM::Game::EventRuntimeState darkState = executeGate(gloamingProgram, 5, darkParty);
        REQUIRE(darkState.pendingDialogueContext.has_value());
        CHECK_EQ(darkState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
        CHECK_EQ(darkState.pendingDialogueContext->sourceId, 219u);

        OpenYAMM::Game::Party archibaldParty = makeScriptedRegressionParty();
        archibaldParty.setQuestBit(612, true);
        archibaldParty.setQuestBit(710, true);
        const OpenYAMM::Game::EventRuntimeState archibaldState = executeGate(gloamingProgram, 5, archibaldParty);
        REQUIRE(archibaldState.pendingDialogueContext.has_value());
        CHECK_EQ(archibaldState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
        CHECK_EQ(archibaldState.pendingDialogueContext->sourceId, 221u);
    }
}

TEST_CASE("mm7 castle gloaming soul jar chest stops after dark path chest")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d03", "d03_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    party.setQuestBit(611, true);

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 176, runtimeState, &party));

    REQUIRE_EQ(runtimeState.openedChestIds.size(), 1u);
    CHECK_EQ(runtimeState.openedChestIds.front(), 0u);
    CHECK(party.hasQuestBit(743));
    CHECK(party.hasQuestBit(662));
}

TEST_CASE("mm7 deyja tatalia and evenmorn mmmerge overlays apply local behavior")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    const uint32_t hostileBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile);

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out05", "7out05_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(611, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(
            runtimeState.actorGroupSetMasks[56] & hostileBit,
            hostileBit);
        CHECK_EQ(
            runtimeState.actorGroupSetMasks[55] & hostileBit,
            hostileBit);
        CHECK_EQ(
            runtimeState.monsterRelationOverrides[
                OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(91, 0)],
            0);

        OpenYAMM::Game::EventRuntimeState ambushState = {};
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::NpcExit;
        hookContext.npcId = 461;
        ambushState.activeHookContext = hookContext;
        RecordingSceneEventContext sceneContext = {};
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::NpcExit,
            ambushState,
            &party,
            &sceneContext));
        REQUIRE_EQ(sceneContext.summonMonstersCalls.size(), 1u);
        CHECK_EQ(sceneContext.summonMonstersCalls.front().typeIndexInMapStats, 3u);
        CHECK_EQ(sceneContext.summonMonstersCalls.front().level, 3u);
        CHECK_EQ(sceneContext.summonMonstersCalls.front().count, 5u);
        CHECK_EQ(sceneContext.summonMonstersCalls.front().group, 59u);
        CHECK_EQ(ambushState.actorGroupSetMasks[59] & hostileBit, hostileBit);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out13", "7out13_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime(&OpenYAMM::Tests::regressionGameData().houseTable);
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 82, runtimeState, &party));
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
        CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 1607u);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out09", "out09_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState dimensionState = {};
        dimensionState.namedGlobalVars["MMerge.CrossContinents.GotMainQuest"] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 6, dimensionState, &party));
        CHECK(dimensionState.pendingDimensionDoorOverlay);
        REQUIRE(dimensionState.lastActivationResult.has_value());
        CHECK_EQ(*dimensionState.lastActivationResult, "You feel high magic presence here.");

        OpenYAMM::Game::EventRuntimeState treasureState = {};
        treasureState.variables[static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::Hour)] = 1;
        for (uint32_t qbitId = 676; qbitId <= 689; ++qbitId)
        {
            party.setQuestBit(qbitId, true);
        }
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 65009, treasureState, &party));
        REQUIRE(treasureState.spriteOverrides.contains(170));
        CHECK_EQ(treasureState.spriteOverrides[170].textureName, "0");
    }
}

TEST_CASE("mm7 tularean forest mmmerge artifact and clanker overlays apply")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out04", "7out04_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.namedGlobalVars["MMerge.CrossContinents.GotMainQuest"] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 504, runtimeState, &party));
        CHECK(runtimeState.pendingDimensionDoorOverlay);
        REQUIRE(runtimeState.lastActivationResult.has_value());
        CHECK_EQ(*runtimeState.lastActivationResult, "You feel high magic presence here.");
    }

    {
        OpenYAMM::Game::MapAssetInfo loadedMap = {};
        REQUIRE(loadOutdoorMapWithCompanionOptions(
            requireRegressionMapLoader().assetFileSystem,
            requireRegressionMapLoader().gameDataLoader,
            "7out04.odm",
            OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
            OpenYAMM::Game::MapCompanionLoadOptions{
                .allowSceneYml = true,
                .allowLegacyCompanion = true},
            loadedMap));
        REQUIRE(loadedMap.outdoorMapData.has_value());

        const auto bmodelIt = std::find_if(
            loadedMap.outdoorMapData->bmodels.begin(),
            loadedMap.outdoorMapData->bmodels.end(),
            [](const OpenYAMM::Game::OutdoorBModel &bmodel)
            {
                return bmodel.name == "ClL1_W";
            });
        REQUIRE(bmodelIt != loadedMap.outdoorMapData->bmodels.end());
        REQUIRE_FALSE(bmodelIt->faces.empty());

        for (const OpenYAMM::Game::OutdoorBModelFace &face : bmodelIt->faces)
        {
            CHECK_EQ(face.cogTriggeredNumber, 504u);
        }
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(600, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        RecordingSceneEventContext sceneContext = {};

        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            401,
            runtimeState,
            &party,
            &sceneContext));
        CHECK(party.hasQuestBit(649));
        CHECK(party.hasQuestBit(591));
        REQUIRE_EQ(runtimeState.grantedItemIds.size(), 1u);
        CHECK_EQ(runtimeState.grantedItemIds.front(), 1502u);
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 412u);
        REQUIRE_EQ(sceneContext.summonMonstersCalls.size(), 6u);
        CHECK_EQ(sceneContext.summonMonstersCalls[0].count, 3u);
        CHECK_EQ(sceneContext.summonMonstersCalls[3].typeIndexInMapStats, 3u);
        CHECK_EQ(sceneContext.summonMonstersCalls[3].count, 3u);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime(&OpenYAMM::Tests::regressionGameData().houseTable);
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(710, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 503, runtimeState, &party));
        CHECK_EQ(runtimeState.npcHouseOverrides[427], 395u);
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
        CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 395u);
    }
}

TEST_CASE("mm7 harmondale erathia shoals and strange temple mmmerge overlays apply")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out02", "7out02_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.addHiredNpcFollower({416, 0, 0});
        party.addHiredNpcFollower({417, 0, 0});
        party.setQuestBit(1697, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.hiredNpcFollowers = {{416, 0, 0}, {417, 0, 0}};

        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 37, runtimeState, &party));
        CHECK(runtimeState.hiredNpcFollowers.empty());
        CHECK(party.hasQuestBit(611));
        CHECK(party.hasQuestBit(664));
        CHECK_FALSE(party.hasQuestBit(1697));
        CHECK_FALSE(party.hasQuestBit(1698));

        party.setQuestBit(519, true);
        OpenYAMM::Game::EventRuntimeState castleState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 301, castleState, &party));
        CHECK(party.hasQuestBit(587));
        CHECK(party.hasQuestBit(644));
        CHECK_EQ(castleState.npcHouseOverrides[397], 240u);
        REQUIRE(castleState.pendingDialogueContext.has_value());
        CHECK_EQ(castleState.pendingDialogueContext->sourceId, 397u);

        OpenYAMM::Game::Party unrepairedParty = makeScriptedRegressionParty();
        unrepairedParty.setQuestBit(519, true);
        unrepairedParty.setQuestBit(644, true);
        OpenYAMM::Game::EventRuntimeState unrepairedCastleState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            301,
            unrepairedCastleState,
            &unrepairedParty));
        REQUIRE(unrepairedCastleState.pendingDialogueContext.has_value());
        CHECK_EQ(unrepairedCastleState.pendingDialogueContext->transitionTextId, 390u);
        const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
        const std::vector<OpenYAMM::Game::MapStatsEntry> harmondaleMapEntries = {
            []()
            {
                OpenYAMM::Game::MapStatsEntry entry = {};
                entry.id = 63;
                entry.name = "Harmondale";
                entry.fileName = "7out02.odm";
                return entry;
            }(),
            []()
            {
                OpenYAMM::Game::MapStatsEntry entry = {};
                entry.id = 103;
                entry.name = "Castle Harmondale";
                entry.fileName = "7d29.blv";
                return entry;
            }(),
        };
        const OpenYAMM::Game::EventDialogContent unrepairedDialog = OpenYAMM::Game::buildEventDialogContent(
            unrepairedCastleState,
            0,
            true,
            nullptr,
            &gameData.houseTable,
            nullptr,
            nullptr,
            &gameData.transitionTable,
            &harmondaleMapEntries[0],
            &harmondaleMapEntries,
            nullptr,
            nullptr,
            0.0f);
        CHECK_EQ(unrepairedDialog.videoName, "out02 castle harmondy");

        OpenYAMM::Game::Party repairedParty = makeScriptedRegressionParty();
        repairedParty.setQuestBit(519, true);
        repairedParty.setQuestBit(610, true);
        OpenYAMM::Game::EventRuntimeState repairedCastleState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            301,
            repairedCastleState,
            &repairedParty));
        REQUIRE(repairedCastleState.pendingDialogueContext.has_value());
        CHECK_EQ(repairedCastleState.pendingDialogueContext->transitionTextId, 382u);
        const OpenYAMM::Game::EventDialogContent repairedDialog = OpenYAMM::Game::buildEventDialogContent(
            repairedCastleState,
            0,
            true,
            nullptr,
            &gameData.houseTable,
            nullptr,
            nullptr,
            &gameData.transitionTable,
            &harmondaleMapEntries[0],
            &harmondaleMapEntries,
            nullptr,
            nullptr,
            0.0f);
        CHECK_EQ(repairedDialog.videoName, "out02 castle harmondy abandoned");

        OpenYAMM::Game::Party invadedParty = makeScriptedRegressionParty();
        invadedParty.setQuestBit(693, true);
        OpenYAMM::Game::EventRuntimeState invasionState = {};
        invasionState.namedMapVars["InvasionTime"] = 1;
        invasionState.variables[static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::DayOfYear)] = 2;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 65002, invasionState, &invadedParty));
        CHECK(invadedParty.hasQuestBit(695));
        CHECK_EQ(
            invasionState.actorGroupSetMasks[60] & static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile),
            static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile));

    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d29", "7d29_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(610, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.mapFileName = "7d29.blv";
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        REQUIRE(runtimeState.spriteOverrides.contains(10));
        CHECK(runtimeState.spriteOverrides.at(10).hidden);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out14", "out14_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party blockedParty = makeScriptedRegressionParty();
        blockedParty.setQuestBit(642, true);
        OpenYAMM::Game::EventRuntimeState blockedState = {};
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::MapTransition;
        hookContext.boundaryEdge = static_cast<uint32_t>(OpenYAMM::Game::MapBoundaryEdge::West);
        hookContext.destinationMapName = "7out15.odm";
        blockedState.activeHookContext = hookContext;
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::MapTransition,
            blockedState,
            &blockedParty));
        REQUIRE(blockedState.activeHookContext.has_value());
        CHECK(blockedState.activeHookContext->blocked);
        REQUIRE(blockedState.activeHookContext->statusText.has_value());
        CHECK_EQ(*blockedState.activeHookContext->statusText, "You must all be wearing your wetsuits!");

        OpenYAMM::Game::Party inventoryOnlyParty = makeScriptedRegressionParty();
        inventoryOnlyParty.setQuestBit(642, true);
        REQUIRE(inventoryOnlyParty.member(0) != nullptr);
        inventoryOnlyParty.member(0)->inventory.push_back(makeScriptedInventoryItem(1406));
        OpenYAMM::Game::EventRuntimeState inventoryOnlyState = {};
        inventoryOnlyState.activeHookContext = hookContext;
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::MapTransition,
            inventoryOnlyState,
            &inventoryOnlyParty));
        REQUIRE(inventoryOnlyState.activeHookContext.has_value());
        CHECK(inventoryOnlyState.activeHookContext->blocked);

        OpenYAMM::Game::Party noQuestParty = makeScriptedRegressionParty();
        REQUIRE(noQuestParty.member(0) != nullptr);
        noQuestParty.member(0)->equipment.armor = 1406;
        OpenYAMM::Game::EventRuntimeState noQuestState = {};
        noQuestState.activeHookContext = hookContext;
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::MapTransition,
            noQuestState,
            &noQuestParty));
        REQUIRE(noQuestState.activeHookContext.has_value());
        CHECK(noQuestState.activeHookContext->blocked);

        OpenYAMM::Game::Party allowedParty = makeScriptedRegressionParty();
        allowedParty.setQuestBit(642, true);
        REQUIRE(allowedParty.member(0) != nullptr);
        allowedParty.member(0)->equipment.armor = 1406;
        OpenYAMM::Game::EventRuntimeState allowedState = {};
        allowedState.activeHookContext = hookContext;
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::MapTransition,
            allowedState,
            &allowedParty));
        REQUIRE(allowedState.activeHookContext.has_value());
        CHECK_FALSE(allowedState.activeHookContext->blocked);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out15", "7out15_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        REQUIRE(party.member(0) != nullptr);
        party.member(0)->portraitPictureId = 4;
        party.member(0)->portraitTextureName = "PC05-01";
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        REQUIRE(party.member(0) != nullptr);
        CHECK_EQ(party.member(0)->portraitPictureId, 4u);

        REQUIRE(eventRuntime.executeOnLeaveEvents(localEventProgram, std::nullopt, runtimeState, &party));
        REQUIRE(party.member(0) != nullptr);
        CHECK_EQ(party.member(0)->portraitPictureId, 4u);

        OpenYAMM::Game::Party oldSaveParty = makeScriptedRegressionParty();
        REQUIRE(oldSaveParty.member(0) != nullptr);
        oldSaveParty.member(0)->portraitPictureId = 30;
        oldSaveParty.member(0)->portraitTextureName = "WetS_01";
        OpenYAMM::Game::EventRuntimeState oldSaveState = {};
        eventRuntime.initializeMapRuntimeState(std::nullopt, oldSaveState);
        oldSaveState.namedMapVars["ShoalsOriginalPortrait0"] = 5;
        REQUIRE(eventRuntime.executeOnLoadEvents(
            localEventProgram,
            std::nullopt,
            oldSaveState,
            &oldSaveParty));
        REQUIRE(oldSaveParty.member(0) != nullptr);
        CHECK_EQ(oldSaveParty.member(0)->portraitPictureId, 4u);
        CHECK_EQ(oldSaveState.namedMapVars["ShoalsOriginalPortrait0"], 0);

        runtimeState = {};
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::GameplayAction;
        hookContext.gameplayActionId = 133;
        runtimeState.activeHookContext = hookContext;
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::GameplayAction,
            runtimeState,
            &party));
        REQUIRE(runtimeState.activeHookContext.has_value());
        CHECK(runtimeState.activeHookContext->blocked);

        OpenYAMM::Game::Party unsuitedParty = makeScriptedRegressionParty();
        REQUIRE(unsuitedParty.member(0) != nullptr);
        unsuitedParty.member(0)->health = 40;
        RecordingGameplayWorldContext shoalsWorldContext;
        shoalsWorldContext.setPartyPosition(0.0f, 0.0f, 0.0f);
        OpenYAMM::Game::EventRuntimeState unsuitedTimerState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            65017,
            unsuitedTimerState,
            &unsuitedParty,
            &shoalsWorldContext));
        REQUIRE(unsuitedParty.member(0) != nullptr);
        CHECK_EQ(unsuitedParty.member(0)->health, 0);
        CHECK(unsuitedParty.member(0)->conditions.test(
            static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead)));

        OpenYAMM::Game::Party suitedParty = makeScriptedRegressionParty();
        REQUIRE(suitedParty.member(0) != nullptr);
        suitedParty.member(0)->equipment.armor = 1406;
        OpenYAMM::Game::EventRuntimeState suitedTimerState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            65017,
            suitedTimerState,
            &suitedParty,
            &shoalsWorldContext));
        REQUIRE(suitedParty.member(0) != nullptr);
        CHECK_EQ(suitedParty.member(0)->health, 40);
        CHECK_FALSE(suitedParty.member(0)->conditions.test(
            static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead)));
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7nwc", "7nwc_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 501, runtimeState, &party));
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        REQUIRE(runtimeState.pendingDialogueContext->transitionMapMove.has_value());
        const OpenYAMM::Game::EventRuntimeState::PendingMapMove &move =
            *runtimeState.pendingDialogueContext->transitionMapMove;
        CHECK_EQ(move.mapName, std::optional<std::string>("out02.odm"));
        CHECK_EQ(move.x, -177331);
        CHECK_EQ(move.y, 12547);
        CHECK_EQ(move.z, 465);

        runtimeState = {};
        OpenYAMM::Game::EventRuntimeState::SavedLocation returnLocation = {};
        returnLocation.mapName = "7out03.odm";
        returnLocation.x = -100;
        returnLocation.y = 200;
        returnLocation.z = 300;
        returnLocation.continentId = 2;
        runtimeState.savedLocations["TempleInABottleReturn"] = returnLocation;

        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 501, runtimeState, &party));
        REQUIRE(runtimeState.pendingMapMove.has_value());
        CHECK_EQ(runtimeState.pendingMapMove->mapName, std::optional<std::string>("7out03.odm"));
        CHECK_EQ(runtimeState.pendingMapMove->x, -100);
        CHECK_EQ(runtimeState.pendingMapMove->y, 200);
        CHECK_EQ(runtimeState.pendingMapMove->z, 300);
        CHECK_EQ(runtimeState.activeHistoryContinentId, 2u);
        CHECK_FALSE(runtimeState.savedLocations.contains("TempleInABottleReturn"));
    }
}

TEST_CASE("mm7 erathia mmmerge transport route switches contest destination")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out03", "7out03_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    const uint64_t routeKey = OpenYAMM::Game::EventRuntime::transportRouteOverrideKey(462, 4);

    OpenYAMM::Game::Party firstVisitParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState firstVisitState = {};
    REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, firstVisitState, &firstVisitParty));
    REQUIRE(firstVisitState.transportRouteOverrides.contains(routeKey));
    const OpenYAMM::Game::EventRuntimeState::TransportRouteOverride &emeraldRoute =
        firstVisitState.transportRouteOverrides.at(routeKey);
    CHECK_EQ(emeraldRoute.mapFileName, "7Out01.odm");
    CHECK_EQ(emeraldRoute.destinationName, "Emerald Island");
    CHECK_EQ(emeraldRoute.x, 12552);
    CHECK_EQ(emeraldRoute.directionDegrees, 90);

    OpenYAMM::Game::Party completedContestParty = makeScriptedRegressionParty();
    completedContestParty.setQuestBit(519, true);
    OpenYAMM::Game::EventRuntimeState completedContestState = {};
    REQUIRE(eventRuntime.buildOnLoadState(
        localEventProgram,
        std::nullopt,
        std::nullopt,
        completedContestState,
        &completedContestParty));
    REQUIRE(completedContestState.transportRouteOverrides.contains(routeKey));
    const OpenYAMM::Game::EventRuntimeState::TransportRouteOverride &bracadaRoute =
        completedContestState.transportRouteOverrides.at(routeKey);
    CHECK_EQ(bracadaRoute.mapFileName, "7Out06.odm");
    CHECK_EQ(bracadaRoute.destinationName, "Bracada Desert");
    CHECK_EQ(bracadaRoute.x, 19171);
    CHECK_EQ(bracadaRoute.directionDegrees, 180);
}

TEST_CASE("mm7 small house mmmerge refill restores cube and blaster monster drops")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "mdt15", "mdt15_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::MapDeltaData mapDeltaData = {};
    mapDeltaData.locationInfo.respawnCount = 0;

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, mapDeltaData, runtimeState, &party));
    CHECK_EQ(runtimeState.processedMapRespawnCount, 0);
    CHECK_EQ(runtimeState.actorItemOverrides[0], 1477u);
    CHECK_EQ(runtimeState.actorItemOverrides[1], 1477u);
    REQUIRE(runtimeState.actorExtraItemOverrides.contains(0));
    REQUIRE(runtimeState.actorExtraItemOverrides.contains(1));
    CHECK_EQ(runtimeState.actorExtraItemOverrides[0], std::vector<uint32_t>{866u});
    CHECK_EQ(runtimeState.actorExtraItemOverrides[1], std::vector<uint32_t>{866u});

    runtimeState.actorItemOverrides.clear();
    runtimeState.actorExtraItemOverrides.clear();
    runtimeState.actorSetMasks.clear();
    runtimeState.actorClearMasks.clear();
    mapDeltaData.locationInfo.respawnCount = 1;

    REQUIRE(eventRuntime.executeMapRefillHooks(localEventProgram, std::nullopt, mapDeltaData, runtimeState, &party));
    CHECK_EQ(runtimeState.processedMapRespawnCount, 1);
    CHECK_EQ(runtimeState.actorItemOverrides[0], 1477u);
    CHECK_EQ(runtimeState.actorItemOverrides[1], 1477u);
    REQUIRE(runtimeState.actorExtraItemOverrides.contains(0));
    REQUIRE(runtimeState.actorExtraItemOverrides.contains(1));
    CHECK_EQ(runtimeState.actorExtraItemOverrides[0], std::vector<uint32_t>{866u});
    CHECK_EQ(runtimeState.actorExtraItemOverrides[1], std::vector<uint32_t>{866u});
    CHECK_FALSE(eventRuntime.executeMapRefillHooks(localEventProgram, std::nullopt, mapDeltaData, runtimeState, &party));
}

TEST_CASE("mm7 tularean caves mmmerge overlay adds Loren Steel as quest follower")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d08", "7d08_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, runtimeState, &party));
    CHECK(party.hasQuestBit(1695));
    CHECK(party.hasQuestBit(605));
    REQUIRE_EQ(runtimeState.hiredNpcFollowers.size(), 1u);
    CHECK_EQ(runtimeState.hiredNpcFollowers.front().npcId, 410u);
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 410u);

    OpenYAMM::Game::Party existingQuestParty = makeScriptedRegressionParty();
    existingQuestParty.setQuestBit(1695, true);
    OpenYAMM::Game::EventRuntimeState existingQuestState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, existingQuestState, &existingQuestParty));
    REQUIRE_EQ(existingQuestState.hiredNpcFollowers.size(), 1u);
    CHECK_EQ(existingQuestState.hiredNpcFollowers.front().npcId, 410u);
}

TEST_CASE("mm7 global mmmerge supplement keeps quest followers in sync")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm7GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());

    auto hasFollower = [](const OpenYAMM::Game::EventRuntimeState &runtimeState, uint32_t npcId)
    {
        return std::find_if(
            runtimeState.hiredNpcFollowers.begin(),
            runtimeState.hiredNpcFollowers.end(),
            [npcId](const OpenYAMM::Game::EventRuntimeState::HiredNpcFollower &follower)
            {
                return follower.npcId == npcId;
            }) != runtimeState.hiredNpcFollowers.end();
    };

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 842, runtimeState, &party));
        CHECK(party.hasQuestBit(557));
        CHECK(party.hasQuestBit(1686));
        CHECK(hasFollower(runtimeState, 395));
        CHECK_EQ(runtimeState.npcTopicOverrides[387][0], 843u);
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK(runtimeState.messages.back().find("build a golem") != std::string::npos);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(611, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 805, runtimeState, &party));
        CHECK(party.hasQuestBit(537));
        CHECK(party.hasQuestBit(1685));
        CHECK(hasFollower(runtimeState, 393));
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK(runtimeState.messages.back().find("William has captured me") != std::string::npos);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 859, runtimeState, &party));
        CHECK(party.hasQuestBit(1688));
        REQUIRE_EQ(runtimeState.hiredNpcFollowers.size(), 1u);
        CHECK_EQ(runtimeState.hiredNpcFollowers.front().npcId, 399u);

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 865, runtimeState, &party));
        CHECK(party.hasQuestBit(1694));
        CHECK(hasFollower(runtimeState, 405));
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        for (uint32_t qbitId = 1688; qbitId <= 1694; ++qbitId)
        {
            party.setQuestBit(qbitId, true);
        }

        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        for (uint32_t npcId = 399; npcId <= 405; ++npcId)
        {
            runtimeState.hiredNpcFollowers.push_back({npcId, 0, 0});
            party.addHiredNpcFollower({npcId, 0, 0});
        }

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 858, runtimeState, &party));
        CHECK(party.hasQuestBit(610));
        CHECK(runtimeState.hiredNpcFollowers.empty());
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(610, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.hiredNpcFollowers.push_back({399, 0, 0});
        party.addHiredNpcFollower({399, 0, 0});
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::NpcEnter;
        hookContext.npcId = 398;
        runtimeState.activeHookContext = hookContext;
        REQUIRE(eventRuntime.executeHooks(
            std::nullopt,
            globalEventProgram,
            OpenYAMM::Game::EventRuntimeHookKind::NpcEnter,
            runtimeState,
            &party));
        CHECK(runtimeState.hiredNpcFollowers.empty());
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 884, runtimeState, &party));
        CHECK(party.hasQuestBit(1696));
        CHECK(hasFollower(runtimeState, 411));
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(1695, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.hiredNpcFollowers.push_back({410, 0, 0});
        party.addHiredNpcFollower({410, 0, 0});
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 875, runtimeState, &party));
        CHECK_FALSE(party.hasQuestBit(1695));
        CHECK_FALSE(hasFollower(runtimeState, 410));
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.hiredNpcFollowers.push_back({416, 0, 0});
        party.addHiredNpcFollower({416, 0, 0});
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 891, runtimeState, &party));
        CHECK_FALSE(hasFollower(runtimeState, 416));
        CHECK(hasFollower(runtimeState, 417));
        CHECK_FALSE(party.hasQuestBit(1697));
        CHECK(party.hasQuestBit(1698));

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 893, runtimeState, &party));
        CHECK(hasFollower(runtimeState, 416));
        CHECK_FALSE(hasFollower(runtimeState, 417));
        CHECK(party.hasQuestBit(1697));
        CHECK_FALSE(party.hasQuestBit(1698));
    }
}

TEST_CASE("mm7 global mmmerge supplement applies remaining original quest fixups")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm7GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());

    const uint32_t hostileBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile);

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 769, runtimeState, &party));
        REQUIRE_EQ(runtimeState.grantedItems.size(), 1u);
        CHECK_EQ(runtimeState.grantedItems.front().objectDescriptionId, 947u);
        CHECK(runtimeState.grantedItems.front().identified);
        CHECK_EQ(runtimeState.grantedItems.front().currentCharges, 30u);
        CHECK_EQ(runtimeState.grantedItems.front().maxCharges, 30u);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party resolvedParty = makeScriptedRegressionParty();
        resolvedParty.setQuestBit(761, true);
        OpenYAMM::Game::EventRuntimeState resolvedState = {};
        RecordingSceneEventContext sceneContext = {};
        REQUIRE(eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            513,
            resolvedState,
            &resolvedParty,
            &sceneContext));
        CHECK(sceneContext.summonMonstersCalls.empty());
        CHECK_FALSE(resolvedState.actorGroupSetMasks.contains(59));

        OpenYAMM::Game::Party activeParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState activeState = {};
        REQUIRE(eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            513,
            activeState,
            &activeParty,
            &sceneContext));
        CHECK_EQ(sceneContext.summonMonstersCalls.size(), 1u);
        CHECK_EQ(sceneContext.summonMonstersCalls.back().group, 59u);
        REQUIRE(activeState.actorGroupSetMasks.contains(59));
        CHECK_EQ(activeState.actorGroupSetMasks[59] & hostileBit, hostileBit);

        OpenYAMM::Game::EventRuntimeState forcedState = {};
        OpenYAMM::Game::Party forcedParty = makeScriptedRegressionParty();
        forcedParty.setQuestBit(761, true);
        REQUIRE(eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            514,
            forcedState,
            &forcedParty,
            &sceneContext));
        REQUIRE(forcedState.actorGroupSetMasks.contains(59));
        CHECK_EQ(forcedState.actorGroupSetMasks[59] & hostileBit, hostileBit);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(528, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 783, runtimeState, &party));
        CHECK_FALSE(party.hasQuestBit(528));
        CHECK_EQ(runtimeState.npcHouseOverrides[340], 215u);
        CHECK_EQ(runtimeState.npcGreetingOverrides[340], 320u);
        CHECK_EQ(runtimeState.npcTopicOverrides[340][3], 0u);
        REQUIRE(runtimeState.pendingMapMove.has_value());
        CHECK_EQ(runtimeState.pendingMapMove->mapName, std::optional<std::string>("7out02.odm"));
        CHECK_EQ(runtimeState.pendingMapMove->x, -17331);
        CHECK_EQ(runtimeState.pendingMapMove->y, 12547);
        CHECK_EQ(runtimeState.pendingMapMove->z, 465);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        REQUIRE(party.member(0) != nullptr);
        REQUIRE(party.member(0)->addInventoryItem(makeScriptedInventoryItem(1407)));
        party.setQuestBit(642, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 920, runtimeState, &party));
        CHECK(party.hasQuestBit(783));
        CHECK_FALSE(party.hasQuestBit(642));
        CHECK_EQ(party.inventoryItemCount(1407), 0);
        CHECK_EQ(runtimeState.npcTopicOverrides[419][1], 0u);
        REQUIRE(runtimeState.pendingMovie.has_value());
        CHECK_EQ(runtimeState.pendingMovie->movieName, "\"Endgame 1 Good\"");
        CHECK(runtimeState.pendingMovie->restoreAfterPlayback);

        OpenYAMM::Game::Party darkParty = makeScriptedRegressionParty();
        REQUIRE(darkParty.member(0) != nullptr);
        REQUIRE(darkParty.member(0)->addInventoryItem(makeScriptedInventoryItem(1407)));
        darkParty.setQuestBit(643, true);
        OpenYAMM::Game::EventRuntimeState darkRuntimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 922, darkRuntimeState, &darkParty));
        CHECK(darkParty.hasQuestBit(783));
        CHECK_FALSE(darkParty.hasQuestBit(643));
        CHECK_EQ(darkParty.inventoryItemCount(1407), 0);
        CHECK_EQ(darkRuntimeState.npcTopicOverrides[423][1], 0u);
        REQUIRE(darkRuntimeState.pendingMovie.has_value());
        CHECK_EQ(darkRuntimeState.pendingMovie->movieName, "\"Endgame 2 Evil\"");
        CHECK(darkRuntimeState.pendingMovie->restoreAfterPlayback);
    }
}

TEST_CASE("mm7 global mmmerge supplement applies custom CrossContinents and hatchling fixups")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm7GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.activeHistoryContinentId = 2;

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1778, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.MetVerdant"], 1);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.IntroStep"], 1);

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1778, runtimeState, &party));
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1778, runtimeState, &party));
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1778, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.GotMainQuest"], 1);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.StartedContinent"], 2);
        REQUIRE(runtimeState.npcTopicOverrides.contains(803));
        CHECK_EQ(runtimeState.npcTopicOverrides[803][0], 1783u);

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1788, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.GotConnectorStone"], 1);
        CHECK_EQ(party.inventoryItemCount(624), 1);

        party.setQuestBit(783, true);
        runtimeState.activeHookContext = OpenYAMM::Game::EventRuntimeState::ActiveHookContext{};
        runtimeState.activeHookContext->kind = OpenYAMM::Game::EventRuntimeHookKind::NpcEnter;
        runtimeState.activeHookContext->npcId = 803;
        REQUIRE(eventRuntime.executeHooks(
            std::nullopt,
            globalEventProgram,
            OpenYAMM::Game::EventRuntimeHookKind::NpcEnter,
            runtimeState,
            &party));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.Finished.2"], 1);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.Reward.2"], 1);
        CHECK_EQ(runtimeState.npcHouseOverrides[803], 641u);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        REQUIRE(party.member(0) != nullptr);
        party.member(0)->experience = 50001;
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.activeHistoryContinentId = 3;
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::ChestOpen;
        hookContext.chestId = 7;
        runtimeState.activeHookContext = hookContext;

        REQUIRE(eventRuntime.executeHooks(
            std::nullopt,
            globalEventProgram,
            OpenYAMM::Game::EventRuntimeHookKind::ChestOpen,
            runtimeState,
            &party));
        REQUIRE(runtimeState.chestItemRequests.contains(7));
        REQUIRE_FALSE(runtimeState.chestItemRequests.at(7).empty());
        CHECK_EQ(runtimeState.chestItemRequests.at(7).front().itemId, 772u);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.ScrollGenerated"], 1);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.ScrollItemId"], 772);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.activeHistoryContinentId = 1;
        runtimeState.namedGlobalVars["MMerge.CrossContinents.GotMainQuest"] = 1;
        runtimeState.namedGlobalVars["MMerge.CrossContinents.StartedContinent"] = 3;

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 65200, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.GotConnectorStone"], 1);
        CHECK_EQ(party.inventoryItemCount(624), 1);
        CHECK_EQ(runtimeState.npcGreetingOverrides[803], 331u);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        party.setQuestBit(784, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.activeHistoryContinentId = 3;

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 65200, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.Finished.3"], 1);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.Reward.3"], 1);
        CHECK_EQ(runtimeState.npcGreetingOverrides[803], 325u);
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::NpcTalk);
        CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 803u);
        CHECK_EQ(party.inventoryItemCount(543), 1);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        REQUIRE(party.member(0) != nullptr);
        party.member(0)->inventory.push_back(makeScriptedInventoryItem(771));
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.activeHistoryContinentId = 2;
        std::optional<OpenYAMM::Game::ScriptedEventProgram> dimensionDoorProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out04", "7out04_mmmerge", error);
        REQUIRE_MESSAGE(dimensionDoorProgram.has_value(), error.c_str());

        REQUIRE(eventRuntime.executeEventById(dimensionDoorProgram, std::nullopt, 504, runtimeState, &party));
        CHECK_FALSE(runtimeState.pendingDimensionDoorOverlay);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.ScrollGotten"], 1);
        CHECK_EQ(runtimeState.npcGreetingOverrides[803], 329u);
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::NpcTalk);
        CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 803u);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        party.addFood(200);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        RecordingSceneEventContext sceneContext = {};
        sceneContext.setCurrentGameMinutes(0.0f);

        REQUIRE(eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            789,
            runtimeState,
            &party,
            &sceneContext));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.DragonFood"], 5);
        CHECK_EQ(party.food(), 195);

        runtimeState.namedGlobalVars["MMerge.CrossContinents.DragonFood"] = 95;
        runtimeState.namedGlobalVars["MMerge.CrossContinents.DragonFirstFeedMinutes"] = 1;
        sceneContext.setCurrentGameMinutes(29.0f * 24.0f * 60.0f);
        REQUIRE(eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            789,
            runtimeState,
            &party,
            &sceneContext));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.DragonGrown"], 1);

        REQUIRE(eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            789,
            runtimeState,
            &party,
            &sceneContext));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.DragonJoined"], 1);
        CHECK(runtimeState.unavailableNpcIds.contains(396));
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        party.setQuestBit(611, true);
        party.setQuestBit(1613, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 850, runtimeState, &party));
        CHECK(party.hasQuestBit(566));
        CHECK_EQ(runtimeState.npcTopicOverrides[389][1], 851u);

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 852, runtimeState, &party));
        CHECK(party.hasQuestBit(567));
        CHECK_EQ(runtimeState.npcTopicOverrides[390][0], 853u);

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 950, runtimeState, &party));
        const OpenYAMM::Game::Character *pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        const OpenYAMM::Game::CharacterSkill *pBlasterSkill = pMember->findSkill("Blaster");
        REQUIRE(pBlasterSkill != nullptr);
        CHECK_EQ(pBlasterSkill->level, 1);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        party.setCharacterDollTable(&mapLoader.gameDataLoader.getCharacterDollTable());
        OpenYAMM::Game::Character *pWizard = party.member(0);
        REQUIRE(pWizard != nullptr);
        pWizard->className = "Wizard";
        pWizard->role = "Wizard";
        pWizard->raceId = 9;
        pWizard->sexId = 0;
        pWizard->characterDataId = 62;
        pWizard->inventory.push_back(makeScriptedInventoryItem(1417));
        pWizard->baseResistances.fire = 5;
        pWizard->skillPoints = 0;
        pWizard->skills["ChainArmor"] = {"ChainArmor", 3, OpenYAMM::Game::SkillMastery::Expert};
        pWizard->skills["RepairItem"] = {"RepairItem", 2, OpenYAMM::Game::SkillMastery::Normal};
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 847, runtimeState, &party));
        pWizard = party.member(0);
        REQUIRE(pWizard != nullptr);
        CHECK_EQ(pWizard->className, "Lich");
        CHECK_EQ(pWizard->characterDataId, 66u);
        CHECK_EQ(pWizard->portraitPictureId, 65u);
        CHECK_EQ(pWizard->voiceId, 26);
        CHECK_EQ(pWizard->baseResistances.fire, 20);
        CHECK_EQ(pWizard->baseResistances.light, 65000);
        CHECK(pWizard->permanentImmunities.light);
        CHECK(pWizard->permanentImmunities.dark);
        CHECK_EQ(pWizard->skills.count("ChainArmor"), 0u);
        CHECK_EQ(pWizard->skills.count("RepairItem"), 0u);
        CHECK_EQ(pWizard->skillPoints, 7u);
        CHECK_EQ(party.inventoryItemCount(1417), 0);
        CHECK(party.hasQuestBit(1623));
        CHECK(party.hasQuestBit(1624));
        CHECK_EQ(runtimeState.npcTopicOverrides[388][0], 0u);
        CHECK_EQ(runtimeState.npcGreetingOverrides[388], 194u);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime(nullptr, &mapLoader.gameDataLoader.getNpcDialogTable());
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        REQUIRE(party.setMemberClassName(0, "Monk"));
        party.setQuestBit(539, true);
        party.setQuestBit(1685, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 810, runtimeState, &party));
        const OpenYAMM::Game::Character *pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        CHECK_EQ(pMember->className, "Initiate");
        CHECK(party.hasQuestBit(1572));
        CHECK(party.hasQuestBit(1573));
        CHECK_FALSE(party.hasQuestBit(539));
        CHECK(party.hasQuestBit(1685));
        CHECK_EQ(runtimeState.npcTopicOverrides[377][0], 810u);
        CHECK_EQ(runtimeState.npcTopicOverrides[377][1], 811u);
        CHECK_EQ(runtimeState.npcTopicOverrides[394][0], 810u);
        CHECK_EQ(runtimeState.npcTopicOverrides[394][1], 811u);
        REQUIRE_FALSE(runtimeState.messages.empty());
        const std::optional<std::string> monkPromotionText = mapLoader.gameDataLoader.getNpcDialogTable().getText(1032);
        REQUIRE(monkPromotionText.has_value());
        CHECK_EQ(runtimeState.messages.back(), *monkPromotionText);
        CHECK(runtimeState.messages.back().find("enlightenment is gained by the journey") != std::string::npos);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        party.setQuestBit(652, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 824, runtimeState, &party));
        const OpenYAMM::Game::Character *pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        CHECK_EQ(pMember->className, "Cavalier");
        CHECK(party.hasQuestBit(1566));
        CHECK(party.hasQuestBit(1567));
        CHECK_EQ(runtimeState.npcTopicOverrides[382][1], 825u);

        party.setQuestBit(611, true);
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 821, runtimeState, &party));
        CHECK(party.hasQuestBit(545));
        CHECK_EQ(runtimeState.npcTopicOverrides[381][0], 822u);

        party.setEventVariableValue(static_cast<uint16_t>(OpenYAMM::Game::EvtVariable::ArenaWinsKnight), 5);
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 822, runtimeState, &party));
        pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        CHECK_EQ(pMember->className, "Champion");
        CHECK(party.hasQuestBit(1568));
        CHECK(party.hasQuestBit(1569));
        CHECK_FALSE(party.hasQuestBit(545));
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
        REQUIRE(party.setMemberClassName(0, "GreatDruid"));
        party.setQuestBit(577, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 851, runtimeState, &party));
        const OpenYAMM::Game::Character *pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        CHECK_EQ(pMember->className, "ArchDruid");
        CHECK(party.hasQuestBit(1615));
        CHECK(party.hasQuestBit(1616));
    }
}

TEST_CASE("mm7 lincoln mmmerge exit requires each active member to have a wetsuit")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d23", "7d23_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party blockedParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState blockedState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 501, blockedState, &blockedParty));
    CHECK_FALSE(blockedState.pendingMapMove.has_value());
    REQUIRE_FALSE(blockedState.statusMessages.empty());
    CHECK_EQ(blockedState.statusMessages.back(), "You must all be wearing your wetsuits to exit the ship");

    OpenYAMM::Game::Party allowedParty = makeScriptedRegressionParty();
    REQUIRE(allowedParty.member(0) != nullptr);
    allowedParty.member(0)->equipment.armor = 1406;
    OpenYAMM::Game::EventRuntimeState allowedState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 501, allowedState, &allowedParty));
    REQUIRE(allowedState.pendingDialogueContext.has_value());
    CHECK_EQ(allowedState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::MapTransition);
    REQUIRE(allowedState.pendingDialogueContext->transitionMapMove.has_value());
    CHECK_EQ(allowedState.pendingDialogueContext->transitionMapMove->x, -7005);
    CHECK_EQ(allowedState.pendingDialogueContext->transitionMapMove->y, 7856);
    CHECK_EQ(allowedState.pendingDialogueContext->transitionMapMove->z, 225);
    REQUIRE(allowedState.pendingDialogueContext->transitionMapMove->mapName.has_value());
    CHECK_EQ(*allowedState.pendingDialogueContext->transitionMapMove->mapName, "7out15.odm");
}

TEST_CASE("mm7 stone city mmmerge throne room and dwarf king cleanup")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d24", "7d24_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party lockedParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState lockedState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 416, lockedState, &lockedParty));
    CHECK_FALSE(lockedState.pendingDialogueContext.has_value());
    REQUIRE_FALSE(lockedState.statusMessages.empty());
    CHECK_EQ(lockedState.statusMessages.back(), "The Door is Locked");

    OpenYAMM::Game::Party allowedParty = makeScriptedRegressionParty();
    allowedParty.setQuestBit(647, true);
    OpenYAMM::Game::EventRuntimeState allowedState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 416, allowedState, &allowedParty));
    REQUIRE(allowedState.pendingDialogueContext.has_value());
    CHECK_EQ(allowedState.pendingDialogueContext->sourceId, 216u);

    OpenYAMM::Game::Party cleanupParty = makeScriptedRegressionParty();
    cleanupParty.setQuestBit(658, true);
    OpenYAMM::Game::EventRuntimeState cleanupState = {};
    OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
    hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::NpcExit;
    hookContext.npcId = 398;
    cleanupState.activeHookContext = hookContext;
    REQUIRE(eventRuntime.executeHooks(
        localEventProgram,
        std::nullopt,
        OpenYAMM::Game::EventRuntimeHookKind::NpcExit,
        cleanupState,
        &cleanupParty));
    CHECK_FALSE(cleanupParty.hasQuestBit(658));
}

TEST_CASE("mm7 phase1 mmmerge map overlays apply runtime state changes")
{
    {
        const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
        OpenYAMM::Game::GameDataLoader gameDataLoader = {};
        REQUIRE(gameDataLoader.loadForHeadlessGameplay(mapLoader.assetFileSystem));
        REQUIRE(gameDataLoader.loadMapByFileNameForHeadlessGameplay(mapLoader.assetFileSystem, "7d25.blv"));

        const std::optional<OpenYAMM::Game::MapAssetInfo> &selectedMap = gameDataLoader.getSelectedMap();
        REQUIRE(selectedMap.has_value());
        REQUIRE(selectedMap->eventRuntimeState.has_value());
        const OpenYAMM::Game::EventRuntimeState &loadedState = *selectedMap->eventRuntimeState;
        CHECK_EQ(loadedState.localOnLoadEventsExecuted, 0u);
        CHECK_EQ(loadedState.globalOnLoadEventsExecuted, 0u);
        CHECK_EQ(loadedState.mapVars[6], 0u);

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(611, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = loadedState;
        REQUIRE(eventRuntime.executeOnLoadEvents(
            selectedMap->localEventProgram,
            selectedMap->globalEventProgram,
            runtimeState,
            &party));
        CHECK_EQ(runtimeState.mapVars[6], 0u);

        constexpr uint32_t hostileMask = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile);
        for (const uint32_t groupId : {55u, 56u, 57u})
        {
            const std::unordered_map<uint32_t, uint32_t>::const_iterator it =
                runtimeState.actorGroupSetMasks.find(groupId);
            const uint32_t setMask = it != runtimeState.actorGroupSetMasks.end() ? it->second : 0u;
            CHECK_EQ(setMask & hostileMask, 0u);
        }
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d25", "7d25_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(612, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(
            runtimeState.actorGroupSetMasks[55] & static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile),
            static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile));
        CHECK_EQ(
            runtimeState.actorGroupSetMasks[56] & static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile),
            static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile));
        CHECK_EQ(
            runtimeState.actorGroupSetMasks[57] & static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile),
            static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile));
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d27", "7d27_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, runtimeState, &party));
        REQUIRE_EQ(runtimeState.grantedItems.size(), 1u);
        CHECK_EQ(runtimeState.grantedItems.front().objectDescriptionId, 1463u);
        CHECK(party.hasQuestBit(752));
        CHECK_EQ(runtimeState.spriteOverrides[20].textureName, "0");
        CHECK_EQ(
            runtimeState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
            static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d34", "7d34_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        REQUIRE(party.member(0) != nullptr);
        party.member(0)->inventory.push_back(makeScriptedInventoryItem(1431));
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, runtimeState, &party));
        REQUIRE_EQ(runtimeState.hiredNpcFollowers.size(), 1u);
        CHECK_EQ(runtimeState.hiredNpcFollowers.front().npcId, 400u);
        CHECK(party.hasQuestBit(1689));
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::NpcTalk);
        CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 400u);
        REQUIRE_MESSAGE(
            OpenYAMM::Tests::regressionGameDataLoaded(),
            OpenYAMM::Tests::regressionGameDataFailure().c_str());
        const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
        const OpenYAMM::Game::NpcEntry *pJaycen = gameData.npcDialogTable.getNpc(400);
        REQUIRE(pJaycen != nullptr);
        CHECK_EQ(pJaycen->greetId, 205u);
        const OpenYAMM::Game::NpcGreetingEntry *pJaycenGreeting =
            gameData.npcDialogTable.getGreetingForNpc(400);
        REQUIRE(pJaycenGreeting != nullptr);
        CHECK_FALSE(pJaycenGreeting->greetingPrimary.empty());
        const OpenYAMM::Game::EventDialogContent dialog = OpenYAMM::Game::buildEventDialogContent(
            runtimeState,
            runtimeState.messages.size(),
            true,
            &gameData.globalEventProgram,
            &gameData.houseTable,
            &gameData.classSkillTable,
            &gameData.npcDialogTable,
            &gameData.transitionTable,
            nullptr,
            nullptr,
            &party,
            nullptr,
            -1.0f,
            &gameData.mergedNpcProfessionTable,
            &gameData.mergedNewsProfessionTopicTable,
            &gameData.mergedNpcBtbTable,
            &gameData.mergedTeacherTopicTable,
            &gameData.mergedContinentSettingTable);
        CHECK(dialog.isActive);
        CHECK_EQ(dialog.title, "Jaycen Keldin");
        CHECK_FALSE(dialog.lines.empty());
        const bool hasDwarfGreeting =
            std::find(dialog.lines.begin(), dialog.lines.end(), "Who are you?") != dialog.lines.end()
            || std::find(dialog.lines.begin(), dialog.lines.end(), "I owe you my life.") != dialog.lines.end();
        CHECK(hasDwarfGreeting);
        const auto spriteOverride = runtimeState.spriteOverrides.find(1u);
        REQUIRE(spriteOverride != runtimeState.spriteOverrides.end());
        CHECK(spriteOverride->second.hidden);
        REQUIRE(spriteOverride->second.textureName.has_value());
        CHECK_EQ(*spriteOverride->second.textureName, "0");
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d37", "7d37_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, runtimeState, &party));
        CHECK_EQ(runtimeState.namedMapVars["PortraitTaken"], 1);
        CHECK(party.hasQuestBit(778));
        REQUIRE_EQ(runtimeState.grantedItemIds.size(), 1u);
        CHECK_EQ(runtimeState.grantedItemIds.front(), 1423u);
        CHECK_EQ(runtimeState.textureOverrides[15], "t2bs");
    }
}

TEST_CASE("mm7 phase1 mmmerge travel and after-load overlays apply destinations")
{
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d36", "7d36_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 501, runtimeState));
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::MapTransition);
        REQUIRE(runtimeState.pendingDialogueContext->transitionMapMove.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->transitionMapMove->z, 5);
        REQUIRE(runtimeState.pendingDialogueContext->transitionMapMove->mapName.has_value());
        CHECK_EQ(*runtimeState.pendingDialogueContext->transitionMapMove->mapName, "out12.odm");
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out11", "out11_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 501, runtimeState));
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::MapTransition);
        REQUIRE(runtimeState.pendingDialogueContext->transitionMapMove.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->transitionMapMove->x, 179);
        CHECK_EQ(runtimeState.pendingDialogueContext->transitionMapMove->y, -5386);
        CHECK_EQ(runtimeState.pendingDialogueContext->transitionMapMove->z, 33);
        REQUIRE(runtimeState.pendingDialogueContext->transitionMapMove->mapName.has_value());
        CHECK_EQ(*runtimeState.pendingDialogueContext->transitionMapMove->mapName, "7d24.blv");
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out12", "out12_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(616, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK(party.hasQuestBit(775));
        CHECK_EQ(runtimeState.npcGreetingOverrides[462], 316u);
        REQUIRE_EQ(runtimeState.grantedItems.size(), 1u);
        CHECK_EQ(runtimeState.grantedItems.front().objectDescriptionId, 866u);
        CHECK(runtimeState.grantedItems.front().identified);
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 462u);
    }
}

TEST_CASE("mm6 outdoor mmmerge supplements unlock local town portal destinations")
{
    struct Case
    {
        const char *pBaseName = nullptr;
        const char *pOverlayName = nullptr;
        uint32_t qbitId = 0;
        uint16_t onLoadEventId = 0;
        bool clearsGuardHostility = false;
        uint32_t dragonTowerQbitId = 0;
        uint16_t dragonTowerEventId = 0;
        uint32_t dragonTowerModelIndex = 0;
        uint32_t dragonTowerFaceIndex = 0;
        uint32_t peacefulMonsterKind = 0;
    };

    constexpr std::array<Case, 6> Cases = {{
        {"outb2", "outb2_mmmerge", 310, 65024, true, 1184, 211, 61, 42, 196},
        {"outc1", "outc1_mmmerge", 315, 65025, true, 1185, 210, 114, 42, 0},
        {"outc2", "outc2_mmmerge", 311, 65026, false, 1183, 210, 25, 55, 0},
        {"outd1", "outd1_mmmerge", 314, 65027, false, 1182, 210, 117, 42, 211},
        {"oute2", "oute2_mmmerge", 312, 65028, false, 1181, 211, 53, 42, 211},
        {"oute3", "oute3_mmmerge", 313, 65029, false, 1180, 231, 84, 42, 185},
    }};

    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> mm6CommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    REQUIRE(supportLua.has_value());
    REQUIRE(mm6CommonLua.has_value());

    for (const Case &testCase : Cases)
    {
        const std::optional<std::string> baseLua =
            readSourceTextFile(
                sourceRoot / "assets_dev/worlds/mm6/events/maps" / (std::string(testCase.pBaseName) + ".lua"));
        const std::optional<std::string> overlayLua =
            readSourceTextFile(
                sourceRoot / "assets_dev/worlds/mm6/events/maps" / (std::string(testCase.pOverlayName) + ".lua"));

        REQUIRE(baseLua.has_value());
        REQUIRE(overlayLua.has_value());

        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
                *supportLua + "\n\n" + *mm6CommonLua + "\n\n" + *baseLua + "\n\n" + *overlayLua,
                std::string("@events/maps/") + testCase.pBaseName + ".lua + events/maps/"
                    + testCase.pOverlayName + ".lua",
                OpenYAMM::Game::ScriptedEventScope::Map,
                error);

        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        CHECK(localEventProgram->hasEvent(testCase.onLoadEventId));
        CHECK(std::find(
            localEventProgram->onLoadEventIds().begin(),
            localEventProgram->onLoadEventIds().end(),
            testCase.onLoadEventId) != localEventProgram->onLoadEventIds().end());
        const uint16_t dragonTowerTimerEventId = testCase.dragonTowerEventId - 1;
        CHECK(localEventProgram->hasEvent(dragonTowerTimerEventId));

        size_t dragonTowerTimerCount = 0;
        for (const OpenYAMM::Game::ScriptedEventProgram::TimerTrigger &timer : localEventProgram->timerTriggers())
        {
            if (timer.eventId == dragonTowerTimerEventId)
            {
                ++dragonTowerTimerCount;
                CHECK(timer.repeating);
                CHECK_EQ(timer.intervalGameMinutes, 5.0f);
                CHECK_EQ(timer.remainingGameMinutes, 5.0f);
            }
        }
        CHECK_EQ(dragonTowerTimerCount, 1u);

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};

        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK(party.hasQuestBit(testCase.qbitId));
        CHECK_FALSE(party.hasQuestBit(testCase.dragonTowerQbitId));

        if (std::string(testCase.pBaseName) == "outc1")
        {
            REQUIRE(runtimeState.outdoorSkyTextureOverride.has_value());
            CHECK_EQ(*runtimeState.outdoorSkyTextureOverride, "sky04");
            REQUIRE(runtimeState.outdoorFogWeakDistanceOverride.has_value());
            CHECK_EQ(*runtimeState.outdoorFogWeakDistanceOverride, 100);
            REQUIRE(runtimeState.outdoorFogStrongDistanceOverride.has_value());
            CHECK_EQ(*runtimeState.outdoorFogStrongDistanceOverride, 1000);
            REQUIRE(runtimeState.snowEnabled.has_value());
            CHECK(*runtimeState.snowEnabled);

            OpenYAMM::Game::Party hermitOnlyParty = makeScriptedRegressionParty();
            hermitOnlyParty.setQuestBit(1252, true);
            OpenYAMM::Game::EventRuntimeState hermitOnlyState = {};
            REQUIRE(eventRuntime.buildOnLoadState(
                localEventProgram,
                std::nullopt,
                std::nullopt,
                hermitOnlyState,
                &hermitOnlyParty));
            REQUIRE(hermitOnlyState.snowEnabled.has_value());
            CHECK(*hermitOnlyState.snowEnabled);

            OpenYAMM::Game::Party endedWinterParty = makeScriptedRegressionParty();
            endedWinterParty.addAward(62);
            OpenYAMM::Game::EventRuntimeState endedWinterState = {};
            REQUIRE(eventRuntime.buildOnLoadState(
                localEventProgram,
                std::nullopt,
                std::nullopt,
                endedWinterState,
                &endedWinterParty));
            CHECK_FALSE(endedWinterState.outdoorSkyTextureOverride.has_value());
            CHECK_FALSE(endedWinterState.outdoorFogWeakDistanceOverride.has_value());
            CHECK_FALSE(endedWinterState.outdoorFogStrongDistanceOverride.has_value());
            REQUIRE(endedWinterState.snowEnabled.has_value());
            CHECK_FALSE(*endedWinterState.snowEnabled);
        }

        const uint32_t textureKey =
            OpenYAMM::Game::EventRuntime::outdoorModelFacetTextureOverrideKey(
                testCase.dragonTowerModelIndex,
                testCase.dragonTowerFaceIndex);
        CHECK_FALSE(runtimeState.outdoorModelFacetTextureOverrides.contains(textureKey));

        if (testCase.peacefulMonsterKind != 0)
        {
            const uint32_t relationKey =
                OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(testCase.peacefulMonsterKind, 0);
            REQUIRE(runtimeState.monsterRelationOverrides.contains(relationKey));
            CHECK_EQ(runtimeState.monsterRelationOverrides.at(relationKey), 0);
        }

        OpenYAMM::Game::EventRuntimeState towerState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, towerState, &party));
        CHECK_FALSE(towerState.outdoorModelFacetTextureOverrides.contains(textureKey));
        party.grantItem(2106);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            testCase.dragonTowerEventId,
            towerState,
            &party,
            nullptr));
        CHECK(party.hasQuestBit(testCase.dragonTowerQbitId));

        REQUIRE(towerState.outdoorModelFacetTextureOverrides.contains(textureKey));
        CHECK_EQ(towerState.outdoorModelFacetTextureOverrides.at(textureKey), "t1swbu");

        OpenYAMM::Game::EventRuntimeState noFlyTimerState = {};
        OpenYAMM::Game::Party noFlyParty = makeScriptedRegressionParty();
        RecordingGameplayWorldContext noFlyContext = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            dragonTowerTimerEventId,
            noFlyTimerState,
            &noFlyParty,
            &noFlyContext));
        CHECK(noFlyContext.castSpellCalls.empty());

        OpenYAMM::Game::EventRuntimeState groundedFlyTimerState = {};
        OpenYAMM::Game::Party groundedFlyParty = makeScriptedRegressionParty();
        groundedFlyParty.applyPartyBuff(
            OpenYAMM::Game::PartyBuffId::Fly,
            300.0f,
            0,
            0,
            0,
            OpenYAMM::Game::SkillMastery::Normal,
            0);
        RecordingGameplayWorldContext groundedFlyContext = {};
        groundedFlyContext.setPartyFlyingForEventChecks(false);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            dragonTowerTimerEventId,
            groundedFlyTimerState,
            &groundedFlyParty,
            &groundedFlyContext));
        CHECK(groundedFlyContext.castSpellCalls.empty());

        OpenYAMM::Game::EventRuntimeState flyTimerState = {};
        OpenYAMM::Game::Party flyParty = makeScriptedRegressionParty();
        flyParty.applyPartyBuff(
            OpenYAMM::Game::PartyBuffId::Fly,
            300.0f,
            0,
            0,
            0,
            OpenYAMM::Game::SkillMastery::Normal,
            0);
        RecordingGameplayWorldContext flyContext = {};
        flyContext.setPartyFlyingForEventChecks(true);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            dragonTowerTimerEventId,
            flyTimerState,
            &flyParty,
            &flyContext));
        REQUIRE_EQ(flyContext.castSpellCalls.size(), 1u);
        CHECK_EQ(flyContext.castSpellCalls.front().spellId, 6u);
        CHECK_EQ(flyContext.castSpellCalls.front().skillLevel, 5u);
        CHECK_EQ(flyContext.castSpellCalls.front().skillMastery, 3u);
        CHECK_EQ(flyContext.castSpellCalls.front().toX, 0);
        CHECK_EQ(flyContext.castSpellCalls.front().toY, 0);
        CHECK_EQ(flyContext.castSpellCalls.front().toZ, 0);

        OpenYAMM::Game::EventRuntimeState invisibleTimerState = {};
        OpenYAMM::Game::Party invisibleParty = makeScriptedRegressionParty();
        invisibleParty.applyPartyBuff(
            OpenYAMM::Game::PartyBuffId::Fly,
            300.0f,
            0,
            0,
            0,
            OpenYAMM::Game::SkillMastery::Normal,
            0);
        invisibleParty.applyPartyBuff(
            OpenYAMM::Game::PartyBuffId::Invisibility,
            300.0f,
            0,
            0,
            0,
            OpenYAMM::Game::SkillMastery::Normal,
            0);
        RecordingGameplayWorldContext invisibleContext = {};
        invisibleContext.setPartyFlyingForEventChecks(true);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            dragonTowerTimerEventId,
            invisibleTimerState,
            &invisibleParty,
            &invisibleContext));
        CHECK(invisibleContext.castSpellCalls.empty());

        OpenYAMM::Game::EventRuntimeState disabledTimerState = {};
        OpenYAMM::Game::Party disabledParty = makeScriptedRegressionParty();
        disabledParty.applyPartyBuff(
            OpenYAMM::Game::PartyBuffId::Fly,
            300.0f,
            0,
            0,
            0,
            OpenYAMM::Game::SkillMastery::Normal,
            0);
        disabledParty.setQuestBit(testCase.dragonTowerQbitId, true);
        RecordingGameplayWorldContext disabledContext = {};
        disabledContext.setPartyFlyingForEventChecks(true);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            dragonTowerTimerEventId,
            disabledTimerState,
            &disabledParty,
            &disabledContext));
        CHECK(disabledContext.castSpellCalls.empty());

        if (testCase.clearsGuardHostility)
        {
            const uint32_t hostileBit =
                static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile);
            CHECK_EQ(runtimeState.actorGroupClearMasks[39] & hostileBit, hostileBit);
            REQUIRE(runtimeState.actorGroupHostilityRequests.contains(39));
            CHECK_FALSE(runtimeState.actorGroupHostilityRequests.at(39));
        }
    }
}

TEST_CASE("mm6 loretta stable overlays preserve stable entry")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());

    struct Case
    {
        const char *pBaseName = nullptr;
        const char *pOverlayName = nullptr;
        uint16_t eventId = 0;
        uint32_t houseId = 0;
        uint32_t lorettaQbitId = 0;
    };

    constexpr std::array<Case, 9> Cases = {{
        {"outb1", "outb1_mmmerge", 8, 477, 1515},
        {"outb2", "outb2_mmmerge", 10, 478, 1516},
        {"outc1", "outc1_mmmerge", 31, 476, 1517},
        {"outc2", "outc2_mmmerge", 14, 472, 1518},
        {"outc2", "outc2_mmmerge", 16, 473, 1519},
        {"outc3", "outc3_mmmerge", 8, 474, 1520},
        {"outd1", "outd1_mmmerge", 10, 475, 1521},
        {"outd3", "outd3_mmmerge", 8, 471, 1522},
        {"oute3", "oute3_mmmerge", 15, 470, 1523},
    }};

    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> mm6CommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    REQUIRE(supportLua.has_value());
    REQUIRE(mm6CommonLua.has_value());

    for (const Case &testCase : Cases)
    {
        const std::optional<std::string> baseLua =
            readSourceTextFile(
                sourceRoot / "assets_dev/worlds/mm6/events/maps" / (std::string(testCase.pBaseName) + ".lua"));
        const std::optional<std::string> overlayLua =
            readSourceTextFile(
                sourceRoot / "assets_dev/worlds/mm6/events/maps" / (std::string(testCase.pOverlayName) + ".lua"));
        REQUIRE(baseLua.has_value());
        REQUIRE(overlayLua.has_value());

        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
                *supportLua + "\n\n" + *mm6CommonLua + "\n\n" + *baseLua + "\n\n" + *overlayLua,
                std::string("@events/maps/") + testCase.pBaseName + ".lua + events/maps/"
                    + testCase.pOverlayName + ".lua",
                OpenYAMM::Game::ScriptedEventScope::Map,
                error);

        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        REQUIRE(localEventProgram->hasEvent(testCase.eventId));

        OpenYAMM::Game::EventRuntime eventRuntime(&OpenYAMM::Tests::regressionGameData().houseTable);
        RecordingSceneEventContext noonContext = {};
        noonContext.setCurrentGameMinutes(12.0f * 60.0f);

        OpenYAMM::Game::Party fallbackParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState fallbackState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            testCase.eventId,
            fallbackState,
            &fallbackParty,
            &noonContext));
        CHECK_FALSE(fallbackParty.hasQuestBit(testCase.lorettaQbitId));
        REQUIRE(fallbackState.pendingDialogueContext.has_value());
        CHECK_EQ(fallbackState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
        CHECK_EQ(fallbackState.pendingDialogueContext->sourceId, testCase.houseId);

        OpenYAMM::Game::Party activeParty = makeScriptedRegressionParty();
        activeParty.setQuestBit(1140, true);
        OpenYAMM::Game::EventRuntimeState activeState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            testCase.eventId,
            activeState,
            &activeParty,
            &noonContext));
        CHECK_FALSE(activeParty.hasQuestBit(testCase.lorettaQbitId));
        CHECK_FALSE(activeParty.hasQuestBit(1141));
        REQUIRE(activeState.pendingDialogueContext.has_value());
        CHECK_EQ(activeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
        CHECK_EQ(activeState.pendingDialogueContext->sourceId, testCase.houseId);
    }
}

TEST_CASE("mm6 global mmmerge supplement keeps rescue followers and collector topics in sync")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm6GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());
    REQUIRE(globalEventProgram->hasEvent(1778));
    REQUIRE(globalEventProgram->hasEvent(65300));
    REQUIRE(globalEventProgram->hasEvent(65301));

    {
        const std::vector<uint16_t> &onLoadEventIds = globalEventProgram->onLoadEventIds();
        CHECK(std::find(onLoadEventIds.begin(), onLoadEventIds.end(), 65300) != onLoadEventIds.end());
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        struct EnrothGrandmasterTopic
        {
            uint32_t npcId = 0;
            uint32_t slot = 0;
            uint32_t topic = 0;
            uint32_t requiredQBit = 0;
        };
        const std::array<EnrothGrandmasterTopic, 33> expectedTopics = {{
            {1043, 3, 302, 0},
            {837, 3, 305, 0},
            {995, 3, 308, 0},
            {817, 3, 311, 1051},
            {991, 3, 314, 0},
            {973, 3, 317, 0},
            {874, 3, 320, 0},
            {830, 3, 329, 0},
            {811, 3, 332, 0},
            {808, 3, 335, 0},
            {890, 4, 338, 0},
            {965, 4, 341, 0},
            {829, 4, 344, 0},
            {894, 3, 347, 0},
            {923, 4, 350, 0},
            {858, 3, 353, 0},
            {840, 4, 356, 0},
            {1057, 3, 359, 0},
            {1040, 3, 362, 0},
            {814, 3, 377, 0},
            {996, 3, 380, 0},
            {972, 3, 383, 0},
            {1014, 3, 386, 0},
            {842, 3, 389, 0},
            {875, 3, 395, 0},
            {1114, 3, 405, 0},
            {860, 3, 406, 0},
            {860, 4, 407, 0},
            {819, 3, 413, 0},
            {809, 4, 416, 0},
            {870, 3, 374, 0},
            {915, 3, 973, 0},
            {966, 4, 326, 0},
        }};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 65300, runtimeState, &party));
        for (const EnrothGrandmasterTopic &expectedTopic : expectedTopics)
        {
            REQUIRE(runtimeState.npcTopicOverrides.contains(expectedTopic.npcId));
            const uint32_t actualTopic = runtimeState.npcTopicOverrides[expectedTopic.npcId][expectedTopic.slot];
            CHECK_EQ(actualTopic, expectedTopic.requiredQBit == 0 ? expectedTopic.topic : 0u);
        }

        runtimeState.npcTopicOverrides.clear();
        runtimeState.activeHookContext = OpenYAMM::Game::EventRuntimeState::ActiveHookContext{};
        runtimeState.activeHookContext->kind = OpenYAMM::Game::EventRuntimeHookKind::NpcEnter;
        runtimeState.activeHookContext->npcId = 829;
        REQUIRE(eventRuntime.executeHooks(
            std::nullopt,
            globalEventProgram,
            OpenYAMM::Game::EventRuntimeHookKind::NpcEnter,
            runtimeState,
            &party));
        REQUIRE(runtimeState.npcTopicOverrides.contains(829));
        CHECK_EQ(runtimeState.npcTopicOverrides[829][4], 344u);

        runtimeState.npcTopicOverrides.clear();
        runtimeState.activeHookContext->npcId = 817;
        REQUIRE(eventRuntime.executeHooks(
            std::nullopt,
            globalEventProgram,
            OpenYAMM::Game::EventRuntimeHookKind::NpcEnter,
            runtimeState,
            &party));
        REQUIRE(runtimeState.npcTopicOverrides.contains(817));
        CHECK_EQ(runtimeState.npcTopicOverrides[817][3], 0u);

        party.setQuestBit(1051, true);
        REQUIRE(eventRuntime.executeHooks(
            std::nullopt,
            globalEventProgram,
            OpenYAMM::Game::EventRuntimeHookKind::NpcEnter,
            runtimeState,
            &party));
        REQUIRE(runtimeState.npcTopicOverrides.contains(817));
        CHECK_EQ(runtimeState.npcTopicOverrides[817][3], 311u);
    }

    auto hasFollower = [](const OpenYAMM::Game::EventRuntimeState &runtimeState, uint32_t npcId)
    {
        return std::find_if(
            runtimeState.hiredNpcFollowers.begin(),
            runtimeState.hiredNpcFollowers.end(),
            [npcId](const OpenYAMM::Game::EventRuntimeState::HiredNpcFollower &follower)
            {
                return follower.npcId == npcId;
            }) != runtimeState.hiredNpcFollowers.end();
    };

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1331, runtimeState, &party));
        CHECK(party.hasQuestBit(1114));
        CHECK(party.hasQuestBit(1700));
        CHECK(hasFollower(runtimeState, 798));
        CHECK_EQ(runtimeState.npcTopicOverrides[798][0], 1332u);
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK(runtimeState.messages.back().find("The palace is deadly dull") != std::string::npos);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1334, runtimeState, &party));
        CHECK(party.hasQuestBit(1700));
        CHECK(hasFollower(runtimeState, 798));
        CHECK_EQ(runtimeState.npcTopicOverrides[798][0], 1335u);
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK(runtimeState.messages.back().find("Would you believe I got lost") != std::string::npos);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1634, runtimeState, &party));
        CHECK(party.hasQuestBit(1702));
        CHECK(hasFollower(runtimeState, 893));

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1631, runtimeState, &party));
        CHECK_FALSE(party.hasQuestBit(1702));
        CHECK_FALSE(hasFollower(runtimeState, 893));
        CHECK(party.hasAward(88));
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.hiredNpcFollowers.push_back({980, 0, 0});
        party.addHiredNpcFollower({980, 0, 0});
        party.setQuestBit(1704, true);
        party.setQuestBit(1163, true);
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1642, runtimeState, &party));
        CHECK_FALSE(hasFollower(runtimeState, 980));
        CHECK_FALSE(party.hasQuestBit(1704));
        CHECK(party.hasAward(91));
    }

    {
        OpenYAMM::Game::PartySeed seed = createRegressionPartySeed();
        seed.gold = 0;
        seed.members.push_back(makeRegressionPartyMember("Edrin", "Archer", "PC09-01", 9));
        OpenYAMM::Game::Party party = {};
        party.seed(seed);
        REQUIRE(party.member(4) != nullptr);
        party.member(4)->inventory.push_back(makeScriptedInventoryItem(2082));

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1426, runtimeState, &party));
        CHECK_EQ(party.inventoryItemCount(2082), 0);
        CHECK_EQ(party.gold(), 2000);
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK_EQ(
            runtimeState.messages.back(),
            "This one's a little dirty, but I suppose it will do.\nHere is the gold I promised you for it.\nThanks for your help!");
    }

    {
        struct PromotionCase
        {
            uint16_t eventId = 0;
            const char *pStartClassName = nullptr;
            const char *pExpectedClassName = nullptr;
            std::vector<uint32_t> prerequisiteQBitIds = {};
            uint32_t itemId = 0;
            uint32_t receivedPromotionQBitId = 0;
        };

        const std::vector<PromotionCase> cases = {
            {1327, "Paladin", "Crusader", {1699}, 0, 1635},
            {1329, "Crusader", "Hero", {}, 2075, 1637},
            {1349, "Cleric", "Priest", {1130}, 0, 1647},
            {1349, "PriestLight", "PriestLight", {1130}, 0, 1648},
            {1351, "Priest", "HighPriest", {1132}, 0, 1649},
            {1371, "Sorcerer", "Wizard", {}, 0, 1639},
            {1373, "Wizard", "ArchMage", {}, 2077, 1641},
            {1382, "Knight", "Cavalier", {}, 0, 1643},
            {1384, "Cavalier", "Champion", {}, 2128, 1645},
            {1405, "Archer", "WarriorMage", {}, 2106, 1655},
            {1413, "WarriorMage", "MasterArcher", {1180, 1181, 1182, 1183, 1184, 1185}, 0, 1657},
            {1678, "Druid", "GreatDruid", {}, 0, 1651},
            {1679, "GreatDruid", "ArchDruid", {}, 0, 1653},
        };

        for (const PromotionCase &testCase : cases)
        {
            OpenYAMM::Game::PartySeed seed = createRegressionPartySeed();
            seed.members.push_back(makeRegressionPartyMember("Edrin", testCase.pStartClassName, "PC07-01", 7));

            OpenYAMM::Game::Party party = {};
            party.setClassMultiplierTable(&OpenYAMM::Tests::regressionGameData().classMultiplierTable);
            party.setClassSkillTable(&OpenYAMM::Tests::regressionGameData().classSkillTable);
            party.seed(seed);

            const OpenYAMM::Game::Character *pFifthMember = party.member(4);
            REQUIRE(pFifthMember != nullptr);
            REQUIRE_EQ(pFifthMember->className, std::string(testCase.pStartClassName));

            for (uint32_t qbitId : testCase.prerequisiteQBitIds)
            {
                party.setQuestBit(qbitId, true);
            }

            if (testCase.itemId != 0)
            {
                REQUIRE(party.grantItemToMember(0, testCase.itemId));
            }

            OpenYAMM::Game::EventRuntime eventRuntime = {};
            OpenYAMM::Game::EventRuntimeState runtimeState = {};
            CAPTURE(testCase.eventId);
            REQUIRE(eventRuntime.executeEventById(
                std::nullopt,
                globalEventProgram,
                testCase.eventId,
                runtimeState,
                &party));

            pFifthMember = party.member(4);
            REQUIRE(pFifthMember != nullptr);
            CHECK_EQ(pFifthMember->className, std::string(testCase.pExpectedClassName));
            CHECK(party.hasQuestBit(testCase.receivedPromotionQBitId));
        }
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.activeHistoryContinentId = 3;

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1778, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.MetVerdant"], 1);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.IntroStep"], 1);

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1778, runtimeState, &party));
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1778, runtimeState, &party));
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1778, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.GotMainQuest"], 1);
        CHECK_EQ(runtimeState.namedGlobalVars["MMerge.CrossContinents.StartedContinent"], 3);
        REQUIRE(runtimeState.npcTopicOverrides.contains(803));
        CHECK_EQ(runtimeState.npcTopicOverrides[803][0], 1784u);
    }
}

TEST_CASE("mm6 rescue map overlays add quest followers")
{
    struct Case
    {
        const char *pBaseName = nullptr;
        const char *pOverlayName = nullptr;
        uint16_t eventId = 0;
        uint32_t prerequisiteQbitId = 0;
        uint32_t rescueQbitId = 0;
        uint32_t followerNpcId = 0;
    };

    constexpr std::array<Case, 5> Cases = {{
        {"6d02", "6d02_mmmerge", 14, 0, 1704, 980},
        {"6d03", "6d03_mmmerge", 22, 0, 1703, 978},
        {"6t3", "6t3_mmmerge", 30, 0, 1705, 940},
        {"6t8", "6t8_mmmerge", 25, 0, 1702, 893},
        {"sewer", "sewer_mmmerge", 8, 1122, 1701, 802},
    }};

    auto hasFollower = [](const OpenYAMM::Game::EventRuntimeState &runtimeState, uint32_t npcId)
    {
        return std::find_if(
            runtimeState.hiredNpcFollowers.begin(),
            runtimeState.hiredNpcFollowers.end(),
            [npcId](const OpenYAMM::Game::EventRuntimeState::HiredNpcFollower &follower)
            {
                return follower.npcId == npcId;
            }) != runtimeState.hiredNpcFollowers.end();
    };

    for (const Case &testCase : Cases)
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, testCase.pBaseName, testCase.pOverlayName, error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        if (testCase.prerequisiteQbitId != 0)
        {
            party.setQuestBit(testCase.prerequisiteQbitId, true);
        }

        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, testCase.eventId, runtimeState, &party));
        CHECK(party.hasQuestBit(testCase.rescueQbitId));
        CHECK(hasFollower(runtimeState, testCase.followerNpcId));
        REQUIRE(runtimeState.pendingDialogueContext.has_value());
        CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, testCase.followerNpcId);
    }
}

TEST_CASE("mm6 castle ironfist mmmerge overlay ports Archibald and bandit gates")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outd3", "outd3_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime(&OpenYAMM::Tests::regressionGameData().houseTable);

    {
        OpenYAMM::Game::Party lockedParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState lockedState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 42, lockedState, &lockedParty));
        REQUIRE(lockedState.pendingDialogueContext.has_value());
        CHECK_EQ(lockedState.pendingDialogueContext->sourceId, 1215u);

        OpenYAMM::Game::Party bellParty = makeScriptedRegressionParty();
        bellParty.grantItem(2081);
        OpenYAMM::Game::EventRuntimeState bellState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 42, bellState, &bellParty));
        REQUIRE(bellState.pendingMovie.has_value());
        CHECK_EQ(bellState.pendingMovie->movieName, "archie");
        REQUIRE(bellState.pendingDialogueContext.has_value());
        CHECK_EQ(bellState.pendingDialogueContext->sourceId, 1244u);
    }

    {
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState promptState = {};
        promptState.mapVars[6] = 1;
        RecordingSceneEventContext sceneContext = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 210, promptState, &party, &sceneContext));
        REQUIRE(promptState.pendingInputPrompt.has_value());
        CHECK_EQ(promptState.pendingInputPrompt->eventId, 210);
        CHECK_EQ(promptState.pendingInputPrompt->continueStep, 13);
        REQUIRE_EQ(promptState.pendingInputPrompt->answerContinueSteps.size(), 2u);
        CHECK_EQ(promptState.pendingInputPrompt->answerContinueSteps[0], 9u);
        CHECK_EQ(promptState.pendingInputPrompt->answerContinueSteps[1], 14u);
        CHECK_EQ(sceneContext.castSpellCalls.size(), 2u);

        OpenYAMM::Game::EventRuntimeState payState = {};
        payState.mapVars[6] = 1;
        party.addGold(100);
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            210,
            payState,
            &party,
            nullptr,
            9));
        CHECK_EQ(party.gold(), 0);
        CHECK_EQ(payState.mapVars[6], 0u);

        OpenYAMM::Game::EventRuntimeState fightState = {};
        fightState.mapVars[6] = 1;
        RecordingSceneEventContext fightContext = {};
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            210,
            fightState,
            &party,
            &fightContext,
            14));
        REQUIRE_EQ(fightContext.summonMonstersCalls.size(), 1u);
        CHECK_EQ(fightContext.summonMonstersCalls.front().typeIndexInMapStats, 1u);
        CHECK_EQ(fightState.mapVars[6], 0u);
    }
}

TEST_CASE("mm6 outc2 overlay ports council and temple local fixes")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> mm6CommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps/outc2.lua");
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps/outc2_mmmerge.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(mm6CommonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *mm6CommonLua + "\n\n" + *baseLua + "\n\n" + *overlayLua,
            "@events/maps/outc2.lua + events/maps/outc2_mmmerge.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::PartySeed councilSeed = {};
    councilSeed.members.push_back(makeScriptedRegressionMember());
    councilSeed.members.push_back(makeScriptedRegressionMember());
    OpenYAMM::Game::Party councilParty = {};
    councilParty.seed(councilSeed);
    REQUIRE(councilParty.setActiveMemberIndex(0));
    REQUIRE(councilParty.grantItemToMember(1, 2122));
    OpenYAMM::Game::EventRuntimeState councilState = {};

    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        49,
        councilState,
        &councilParty,
        nullptr));
    REQUIRE(councilState.pendingMovie.has_value());
    CHECK_EQ(councilState.pendingMovie->movieName, "citytrtr");
    CHECK_EQ(councilState.npcHouseOverrides[1089], 0u);
    CHECK(councilParty.hasQuestBit(1192));
    CHECK(councilParty.hasAward(63));
    CHECK_EQ(councilParty.inventoryItemCount(2122), 0);
    REQUIRE(councilState.pendingDialogueContext.has_value());
    CHECK_EQ(councilState.pendingDialogueContext->sourceId, 209u);

    councilState.pendingMovie.reset();
    councilState.pendingDialogueContext.reset();
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        49,
        councilState,
        &councilParty,
        nullptr));
    CHECK_FALSE(councilState.pendingMovie.has_value());
    REQUIRE(councilState.pendingDialogueContext.has_value());
    CHECK_EQ(councilState.pendingDialogueContext->sourceId, 209u);

    OpenYAMM::Game::Party templeParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState templeState = {};
    templeState.hiredNpcFollowers.push_back({20001, 63, 0});
    templeState.hiredNpcFollowers.push_back({20002, 64, 0});
    templeParty.addHiredNpcFollower({20001, 63, 0});
    templeParty.addHiredNpcFollower({20002, 64, 0});

    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        19,
        templeState,
        &templeParty,
        nullptr));
    CHECK(templeParty.hasQuestBit(1130));
    CHECK(templeState.hiredNpcFollowers.empty());
    OpenYAMM::Game::EventRuntimeState syncedTempleState = {};
    templeParty.applyGlobalNpcStateTo(syncedTempleState);
    CHECK(syncedTempleState.hiredNpcFollowers.empty());
    REQUIRE_FALSE(templeState.messages.empty());
    CHECK_EQ(templeState.messages.back(), "The stone cutter and carpenter begin rebuilding the temple.");
    REQUIRE(templeState.pendingDialogueContext.has_value());
    CHECK_EQ(
        templeState.pendingDialogueContext->kind,
        OpenYAMM::Game::DialogueContextKind::MapEvent);

    OpenYAMM::Game::Party chaliceParty = makeScriptedRegressionParty();
    chaliceParty.setQuestBit(1131, true);
    chaliceParty.setQuestBit(1212, true);
    chaliceParty.grantItem(2054);
    OpenYAMM::Game::EventRuntimeState chaliceState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        19,
        chaliceState,
        &chaliceParty,
        nullptr));
    CHECK_FALSE(chaliceParty.hasQuestBit(1212));
    CHECK(chaliceParty.hasQuestBit(1132));
    CHECK_EQ(chaliceParty.inventoryItemCount(2054), 0);
    REQUIRE(chaliceState.pendingDialogueContext.has_value());
    CHECK_EQ(
        chaliceState.pendingDialogueContext->kind,
        OpenYAMM::Game::DialogueContextKind::HouseService);
    CHECK_EQ(chaliceState.pendingDialogueContext->sourceId, 326u);
    REQUIRE_FALSE(chaliceState.messages.empty());
    CHECK(
        chaliceState.messages.back().find("Sacred Chalice")
        != std::string::npos);

    OpenYAMM::Game::Party chaliceMissingParty = makeScriptedRegressionParty();
    chaliceMissingParty.setQuestBit(1131, true);
    OpenYAMM::Game::EventRuntimeState chaliceMissingState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        19,
        chaliceMissingState,
        &chaliceMissingParty,
        nullptr));
    REQUIRE(chaliceMissingState.pendingDialogueContext.has_value());
    CHECK_EQ(chaliceMissingState.pendingDialogueContext->sourceId, 1442u);

    OpenYAMM::Game::Party repairedQuestCompleteParty = makeScriptedRegressionParty();
    repairedQuestCompleteParty.setQuestBit(1130, true);
    repairedQuestCompleteParty.setQuestBit(1129, true);
    OpenYAMM::Game::EventRuntimeState repairedQuestCompleteState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        19,
        repairedQuestCompleteState,
        &repairedQuestCompleteParty,
        nullptr));
    REQUIRE(repairedQuestCompleteState.pendingDialogueContext.has_value());
    CHECK_EQ(repairedQuestCompleteState.pendingDialogueContext->sourceId, 1442u);

    OpenYAMM::Game::Party repairedQuestPendingParty = makeScriptedRegressionParty();
    repairedQuestPendingParty.setQuestBit(1130, true);
    OpenYAMM::Game::EventRuntimeState repairedQuestPendingState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        19,
        repairedQuestPendingState,
        &repairedQuestPendingParty,
        nullptr));
    REQUIRE(repairedQuestPendingState.pendingDialogueContext.has_value());
    CHECK_EQ(repairedQuestPendingState.pendingDialogueContext->sourceId, 1442u);

    OpenYAMM::Game::Party restoredTempleParty = makeScriptedRegressionParty();
    restoredTempleParty.setQuestBit(1132, true);
    OpenYAMM::Game::EventRuntimeState restoredTempleState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        19,
        restoredTempleState,
        &restoredTempleParty,
        nullptr));
    REQUIRE(restoredTempleState.pendingDialogueContext.has_value());
    CHECK_EQ(restoredTempleState.pendingDialogueContext->sourceId, 326u);
}

TEST_CASE("mm6 oute3 overlay ports dimension door and volcano events")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> mm6CommonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps/oute3.lua");
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps/oute3_mmmerge.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(mm6CommonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *mm6CommonLua + "\n\n" + *baseLua + "\n\n" + *overlayLua,
            "@events/maps/oute3.lua + events/maps/oute3_mmmerge.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState dimensionState = {};

    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        140,
        dimensionState,
        &party,
        nullptr));
    CHECK(dimensionState.pendingDimensionDoorOverlay);

    OpenYAMM::Game::EventRuntimeState blockedDimensionState = {};
    blockedDimensionState.mapVars[50] = 1;
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        140,
        blockedDimensionState,
        &party,
        nullptr));
    CHECK_FALSE(blockedDimensionState.pendingDimensionDoorOverlay);

    OpenYAMM::Game::EventRuntimeState volcanoState = {};
    RecordingSceneEventContext volcanoContext = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        220,
        volcanoState,
        &party,
        &volcanoContext));
    CHECK_EQ(volcanoContext.castSpellCalls.size(), 15u);
    REQUIRE_FALSE(volcanoState.pendingSounds.empty());
    CHECK_EQ(volcanoState.pendingSounds.front().soundId, 18090u);
}

TEST_CASE("mm6 New Sorpigal overlay repairs missing starting letter state without resetting progression")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "oute3", "oute3_1", error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
    CHECK(localEventProgram->hasEvent(65521));
    CHECK_EQ(
        std::count(
            localEventProgram->onLoadEventIds().begin(),
            localEventProgram->onLoadEventIds().end(),
            65521),
        1);
    REQUIRE_FALSE(localEventProgram->onLoadEventIds().empty());
    CHECK_EQ(localEventProgram->onLoadEventIds().back(), 65521);

    OpenYAMM::Game::EventRuntime eventRuntime = {};

    OpenYAMM::Game::Party missingStartParty = makeScriptedRegressionParty();
    missingStartParty.setQuestBit(1104, true);
    OpenYAMM::Game::EventRuntimeState missingStartState = {};
    REQUIRE(eventRuntime.buildOnLoadState(
        localEventProgram,
        std::nullopt,
        std::nullopt,
        missingStartState,
        &missingStartParty));
    CHECK(missingStartParty.hasQuestBit(1105));
    CHECK(missingStartState.grantedItems.empty());
    CHECK(missingStartState.grantedItemIds.empty());
    CHECK_EQ(missingStartParty.inventoryItemCount(2125, 0), 1);

    OpenYAMM::Game::Party progressedParty = makeScriptedRegressionParty();
    progressedParty.setQuestBit(1104, true);
    progressedParty.setQuestBit(1106, true);
    OpenYAMM::Game::EventRuntimeState progressedState = {};
    REQUIRE(eventRuntime.buildOnLoadState(
        localEventProgram,
        std::nullopt,
        std::nullopt,
        progressedState,
        &progressedParty));
    CHECK_FALSE(progressedParty.hasQuestBit(1105));
    CHECK(progressedState.grantedItems.empty());
    CHECK(progressedState.grantedItemIds.empty());
    CHECK_EQ(progressedParty.inventoryItemCount(2125), 0);
}

TEST_CASE("mm6 and mm8 initial cutscene overlays queue intro movies once")
{
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "oute3", "oute3_intro", error);

        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        CHECK(localEventProgram->hasEvent(65030));

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["OpenYAMM.WorldIntro.MM6"], 1);
        REQUIRE(runtimeState.pendingMovie.has_value());
        CHECK_EQ(runtimeState.pendingMovie->movieName, "6intro");
        CHECK(runtimeState.pendingMovie->restoreAfterPlayback);

        runtimeState.pendingMovie.reset();
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_FALSE(runtimeState.pendingMovie.has_value());
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out01", "out01_intro", error);

        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        CHECK(localEventProgram->hasEvent(65030));

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(runtimeState.namedGlobalVars["OpenYAMM.WorldIntro.MM8"], 1);
        REQUIRE(runtimeState.pendingMovie.has_value());
        CHECK_EQ(runtimeState.pendingMovie->movieName, "intro");
        CHECK(runtimeState.pendingMovie->restoreAfterPlayback);

        runtimeState.pendingMovie.reset();
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_FALSE(runtimeState.pendingMovie.has_value());
    }
}

TEST_CASE("mm6 remaining mmmerge delta overlays port map event fixes")
{
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "sci-fi", "sci-fi_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::PartySeed partySeed = {};
        partySeed.members.push_back(makeScriptedRegressionMember());
        partySeed.members.push_back(makeScriptedRegressionMember());
        partySeed.members.push_back(makeScriptedRegressionMember());
        OpenYAMM::Game::Party party = {};
        party.seed(partySeed);
        party.setClassSkillTable(&OpenYAMM::Tests::regressionGameData().classSkillTable);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 61, runtimeState, &party));
        CHECK(party.hasQuestBit(1300));
        CHECK_EQ(runtimeState.textureOverrides[2927], "trekscon");
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK(
            runtimeState.messages.back().find("Blaster weapons provide an effective, accurate ranged attack")
            != std::string::npos);

        for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
        {
            const OpenYAMM::Game::Character *pMember = party.member(memberIndex);
            REQUIRE(pMember != nullptr);
            const OpenYAMM::Game::CharacterSkill *pSkill = pMember->findSkill("Blaster");
            REQUIRE(pSkill != nullptr);
            CHECK_EQ(pSkill->level, 1);
        }

        REQUIRE_EQ(runtimeState.portraitFxRequests.size(), 1u);
        CHECK_EQ(runtimeState.portraitFxRequests.front().kind, OpenYAMM::Game::PortraitFxEventKind::QuestComplete);
        CHECK_EQ(runtimeState.portraitFxRequests.front().memberIndices, std::vector<size_t>({0, 1, 2}));
        REQUIRE_EQ(runtimeState.pendingSounds.size(), 1u);
        CHECK_EQ(runtimeState.pendingSounds.front().soundId, static_cast<uint32_t>(OpenYAMM::Game::SoundId::Quest));

        runtimeState.portraitFxRequests.clear();
        runtimeState.pendingSounds.clear();
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 61, runtimeState, &party));
        CHECK(runtimeState.portraitFxRequests.empty());
        CHECK(runtimeState.pendingSounds.empty());
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outb2", "outb2_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 68, runtimeState, &party));
        REQUIRE(runtimeState.chestItemRequests.contains(1));
        REQUIRE_FALSE(runtimeState.chestItemRequests.at(1).empty());
        CHECK_EQ(runtimeState.chestItemRequests.at(1).front().itemId, 2119u);

        OpenYAMM::Game::Party ownedParty = makeScriptedRegressionParty();
        ownedParty.grantItem(2119);
        OpenYAMM::Game::EventRuntimeState ownedState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 68, ownedState, &ownedParty));
        CHECK_FALSE(ownedState.chestItemRequests.contains(1));
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outb1", "outb1_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::PartySeed partySeed = {};
        partySeed.members.push_back(makeRegressionPartyMember("Brom", "Cleric", "PC03-01", 3));
        OpenYAMM::Game::Party party = {};
        party.seed(partySeed);
        OpenYAMM::Game::Character *pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        pMember->level = 5;
        pMember->maxHealth = 80;
        pMember->health = 80;
        pMember->maxSpellPoints = 60;
        pMember->spellPoints = 60;

        const int baseEffectiveHealth = OpenYAMM::Game::Party::effectiveMaximumHealth(*pMember);
        const int baseEffectiveSpellPoints = OpenYAMM::Game::Party::effectiveMaximumSpellPoints(*pMember);

        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 102, runtimeState, &party));

        pMember = party.member(0);
        REQUIRE(pMember != nullptr);
        CHECK_EQ(pMember->levelModifier, 30);
        CHECK_GT(OpenYAMM::Game::Party::effectiveMaximumHealth(*pMember), baseEffectiveHealth);
        CHECK_GT(OpenYAMM::Game::Party::effectiveMaximumSpellPoints(*pMember), baseEffectiveSpellPoints);

        bool foundStatIncreaseFx = false;
        for (const OpenYAMM::Game::EventRuntimeState::PortraitFxRequest &request : runtimeState.portraitFxRequests)
        {
            if (request.kind == OpenYAMM::Game::PortraitFxEventKind::StatIncrease
                && request.memberIndices == std::vector<size_t>({0}))
            {
                foundStatIncreaseFx = true;
            }
        }

        CHECK(foundStatIncreaseFx);
        REQUIRE_EQ(runtimeState.pendingSounds.size(), 1u);
        CHECK_EQ(runtimeState.pendingSounds.front().soundId, static_cast<uint32_t>(OpenYAMM::Game::SoundId::Quest));
        REQUIRE_FALSE(runtimeState.statusMessages.empty());
        CHECK_EQ(runtimeState.statusMessages.back(), "+30 Level temporary.  Look Out!");
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "6d07", "6d07_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party noKeyParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState noKeyState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 16, noKeyState, &noKeyParty));
        CHECK_EQ(noKeyState.mapVars[4], 1u);
        CHECK(noKeyParty.hasQuestBit(1035));
        CHECK(noKeyParty.hasQuestBit(1223));
        REQUIRE_FALSE(noKeyState.openedChestIds.empty());
        CHECK_EQ(noKeyState.openedChestIds.back(), 1u);

        OpenYAMM::Game::Party keyParty = makeScriptedRegressionParty();
        keyParty.grantItem(2107);
        OpenYAMM::Game::EventRuntimeState keyState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 16, keyState, &keyParty));
        CHECK_FALSE(keyParty.hasQuestBit(1035));
        REQUIRE_FALSE(keyState.openedChestIds.empty());
        CHECK_EQ(keyState.openedChestIds.back(), 6u);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "6d08", "6d08_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 62, runtimeState, &party));
        REQUIRE(runtimeState.pendingInputPrompt.has_value());
        REQUIRE_EQ(runtimeState.pendingInputPrompt->answers.size(), 2u);
        CHECK_EQ(runtimeState.pendingInputPrompt->answers[0], "arrow");
        CHECK_EQ(runtimeState.pendingInputPrompt->answers[1], "an arrow");

        runtimeState.pendingInputPrompt.reset();
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            62,
            runtimeState,
            &party,
            nullptr,
            4));
        REQUIRE(runtimeState.mechanisms.contains(62));
        CHECK_EQ(
            runtimeState.mechanisms.at(62).state,
            static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Closing));
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "6d13", "6d13_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::PartySeed partySeed = {};
        partySeed.members.push_back(makeScriptedRegressionMember());
        partySeed.members.push_back(makeScriptedRegressionMember());
        partySeed.members.push_back(makeScriptedRegressionMember());
        OpenYAMM::Game::Party party = {};
        party.seed(partySeed);
        party.setClassSkillTable(&OpenYAMM::Tests::regressionGameData().classSkillTable);
        REQUIRE(party.member(0) != nullptr);
        REQUIRE(party.member(1) != nullptr);
        REQUIRE(party.member(2) != nullptr);
        party.member(0)->className = "Cleric";
        party.member(0)->personality = 11;
        party.member(1)->className = "Druid";
        party.member(1)->personality = 12;
        party.member(2)->className = "Knight";
        party.member(2)->personality = 13;

        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 24, runtimeState, &party));
        CHECK_EQ(party.member(0)->personality, 16);
        CHECK_EQ(party.member(1)->personality, 17);
        CHECK_EQ(party.member(2)->personality, 13);
        CHECK(party.hasQuestBit(1047));
        CHECK_EQ(runtimeState.textureOverrides[949], "d6flora");

        OpenYAMM::Game::PartySeed mapVarPartySeed = {};
        mapVarPartySeed.members.push_back(makeScriptedRegressionMember());
        OpenYAMM::Game::Party mapVarParty = {};
        mapVarParty.seed(mapVarPartySeed);
        mapVarParty.setClassSkillTable(&OpenYAMM::Tests::regressionGameData().classSkillTable);
        REQUIRE(mapVarParty.member(0) != nullptr);
        mapVarParty.member(0)->className = "Knight";
        mapVarParty.member(0)->personality = 20;

        OpenYAMM::Game::EventRuntimeState mapVarState = {};
        mapVarState.mapVars[7] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 24, mapVarState, &mapVarParty));
        CHECK_EQ(mapVarParty.member(0)->personality, 25);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "6t7", "6t7_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 1, runtimeState, &party));
        CHECK(runtimeState.lastAffectedMechanismIds.empty());
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "cd1", "cd1_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 69, runtimeState, nullptr, nullptr));
        REQUIRE(runtimeState.pendingInputPrompt.has_value());
        CHECK_EQ(runtimeState.pendingInputPrompt->continueStep, 4);

        runtimeState.pendingInputPrompt.reset();
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            69,
            runtimeState,
            nullptr,
            nullptr,
            23));
        CHECK_EQ(runtimeState.mapVars[6], 1u);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "cd2", "cd2_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setItemTable(&gameData.itemTable);
        party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 61, runtimeState, &party));
        REQUIRE(runtimeState.pendingInputPrompt.has_value());
        REQUIRE_EQ(runtimeState.pendingInputPrompt->answers.size(), 2u);
        CHECK_EQ(runtimeState.pendingInputPrompt->answers[0], "Yes");
        CHECK_EQ(runtimeState.pendingInputPrompt->answers[1], "Y");

        runtimeState.pendingInputPrompt.reset();
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            61,
            runtimeState,
            &party,
            nullptr,
            4));
        CHECK_EQ(runtimeState.mapVars[9], 1u);
        REQUIRE_FALSE(runtimeState.grantedItems.empty());
        CHECK_NE(runtimeState.grantedItems.back().objectDescriptionId, 0u);
        CHECK_EQ(runtimeState.currentLocationReputation, 200);

        const uint32_t fluidMask = static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Fluid);
        const uint32_t untouchableMask = static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable);

        OpenYAMM::Game::EventRuntimeState cubeState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 45, cubeState, &party));
        CHECK_EQ(cubeState.mapVars[4], 1u);
        REQUIRE(cubeState.pendingInputPrompt.has_value());
        CHECK_EQ(cubeState.pendingInputPrompt->eventId, 45);
        CHECK_EQ(cubeState.pendingInputPrompt->continueStep, 4);
        cubeState.pendingInputPrompt.reset();
        cubeState.pendingDialogueContext.reset();

        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            45,
            cubeState,
            &party,
            nullptr,
            4));
        for (uint32_t faceIndex : {4298u, 4299u, 4300u, 4301u, 4302u})
        {
            CHECK_EQ(cubeState.textureOverrides[faceIndex], "lavatyl");
            CHECK((cubeState.facetSetMasks[faceIndex] & fluidMask) != 0);
        }

        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 45, cubeState, &party));
        CHECK_EQ(cubeState.mapVars[4], 0u);
        for (uint32_t faceIndex : {4298u, 4299u, 4300u, 4301u, 4302u})
        {
            CHECK_EQ(cubeState.textureOverrides[faceIndex], "orwtrtyl");
        }

        OpenYAMM::Game::EventRuntimeState clearedWayState = {};
        clearedWayState.mapVars[3] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 33, clearedWayState, &party));
        CHECK_EQ(clearedWayState.mapVars[3], 2u);
        CHECK((clearedWayState.facetSetMasks[4522] & untouchableMask) != 0);
        CHECK((clearedWayState.facetSetMasks[4575] & untouchableMask) != 0);

        OpenYAMM::Game::EventRuntimeState onLoadState = {};
        onLoadState.mapVars[2] = 1;
        onLoadState.mapVars[3] = 1;
        onLoadState.mapVars[4] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 58, onLoadState, &party));
        for (uint32_t faceIndex : {4219u, 4220u, 4221u, 4222u, 4223u})
        {
            CHECK_EQ(onLoadState.textureOverrides[faceIndex], "lavatyl");
        }
        for (uint32_t faceIndex : {4265u, 4266u, 4267u, 4268u, 4269u})
        {
            CHECK_EQ(onLoadState.textureOverrides[faceIndex], "lavatyl");
        }
        for (uint32_t faceIndex : {4298u, 4299u, 4300u, 4301u, 4302u})
        {
            CHECK_EQ(onLoadState.textureOverrides[faceIndex], "lavatyl");
        }
        CHECK((onLoadState.facetSetMasks[4522] & untouchableMask) != 0);
        CHECK((onLoadState.facetSetMasks[4575] & untouchableMask) != 0);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "cd3", "cd3_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.addGold(60000);
        OpenYAMM::Game::EventRuntimeState guardianState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 13, guardianState, &party));
        REQUIRE(guardianState.pendingInputPrompt.has_value());
        CHECK_EQ(guardianState.pendingInputPrompt->continueStep, 3);
        CHECK_EQ(guardianState.pendingInputPrompt->correctStep, 5);
        REQUIRE_EQ(guardianState.pendingInputPrompt->answers.size(), 2u);
        CHECK_EQ(guardianState.pendingInputPrompt->answers[0], "Yes");
        CHECK_EQ(guardianState.pendingInputPrompt->answers[1], "Y");

        guardianState.pendingInputPrompt.reset();
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            13,
            guardianState,
            &party,
            nullptr,
            5));
        CHECK_EQ(party.gold(), 10000);
        REQUIRE(guardianState.pendingMapMove.has_value());
        CHECK_EQ(guardianState.pendingMapMove->x, 13487);

        OpenYAMM::Game::Party curatorParty = makeScriptedRegressionParty();
        curatorParty.addGold(10000);
        OpenYAMM::Game::EventRuntimeState curatorState = {};
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            27,
            curatorState,
            &curatorParty,
            nullptr,
            4));
        CHECK_EQ(curatorParty.gold(), 0);
        CHECK_EQ(curatorState.currentLocationReputation, 50);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outb3", "outb3_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 105, runtimeState, &party));
        CHECK(runtimeState.pendingDimensionDoorOverlay);

        OpenYAMM::Game::Party shrineParty = makeScriptedRegressionParty();
        OpenYAMM::Game::Character *pMember = shrineParty.member(0);
        REQUIRE(pMember != nullptr);
        OpenYAMM::Game::EventRuntimeState shrineState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 103, shrineState, &shrineParty));
        CHECK_EQ(shrineState.namedMapVars["ShrineOfGodsBlessed0"], 1);
        CHECK_EQ(pMember->might, 34u);
        CHECK_EQ(pMember->intellect, 34u);
        CHECK_EQ(pMember->baseResistances.fire, 20);
        CHECK_EQ(pMember->baseResistances.body, 20);
        REQUIRE_FALSE(shrineState.pendingSounds.empty());
        CHECK_EQ(shrineState.pendingSounds.back().soundId, 42797u);

        shrineParty.applyMemberCondition(0, OpenYAMM::Game::CharacterCondition::Weak);
        REQUIRE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak)));
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 103, shrineState, &shrineParty));
        CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak)));
        CHECK_EQ(pMember->might, 34u);

        OpenYAMM::Game::MapDeltaData mapDeltaData = {};
        mapDeltaData.locationInfo.respawnCount = 1;
        shrineState.namedMapVars["ShrineOfGodsBlessed0"] = 1;
        REQUIRE(eventRuntime.executeMapRefillHooks(localEventProgram, std::nullopt, mapDeltaData, shrineState, &party));
        CHECK_EQ(shrineState.namedMapVars["ShrineOfGodsBlessed0"], 0);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "pyramid", "pyramid_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party firstMateParty = makeScriptedRegressionParty();
        firstMateParty.grantItem(2158);
        firstMateParty.setQuestBit(1253, true);
        OpenYAMM::Game::EventRuntimeState firstMateState = {};
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            21,
            firstMateState,
            &firstMateParty,
            nullptr,
            9));
        CHECK_EQ(firstMateState.mapVars[10], 1u);
        CHECK_FALSE(firstMateParty.hasQuestBit(1253));
        CHECK_EQ(firstMateParty.inventoryItemCount(2158), 0);

        OpenYAMM::Game::Party allCodesParty = makeScriptedRegressionParty();
        allCodesParty.grantItem(2162);
        allCodesParty.setQuestBit(1254, true);
        OpenYAMM::Game::EventRuntimeState allCodesState = {};
        allCodesState.mapVars[10] = 1;
        allCodesState.mapVars[11] = 1;
        allCodesState.mapVars[12] = 1;
        allCodesState.mapVars[13] = 1;
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            25,
            allCodesState,
            &allCodesParty,
            nullptr,
            9));
        CHECK_EQ(allCodesState.mapVars[14], 1u);
        CHECK_EQ(allCodesState.mapVars[27], 1u);

        OpenYAMM::Game::Party captainParty = makeScriptedRegressionParty();
        captainParty.grantItem(2157);
        captainParty.setQuestBit(1255, true);
        OpenYAMM::Game::EventRuntimeState captainState = {};
        captainState.mapVars[27] = 1;
        REQUIRE(eventRuntime.executeNpcTopicEventById(
            localEventProgram,
            std::nullopt,
            1,
            captainState,
            &captainParty,
            nullptr,
            14));
        CHECK_EQ(captainState.mapVars[15], 1u);
        REQUIRE(captainState.mechanisms.contains(1));
        CHECK_EQ(
            captainState.mechanisms.at(1).state,
            static_cast<uint16_t>(OpenYAMM::Game::EvtMechanismState::Closing));
        CHECK_FALSE(captainParty.hasQuestBit(1255));
        CHECK_EQ(captainParty.inventoryItemCount(2157), 0);

        OpenYAMM::Game::EventRuntimeState bookState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 26, bookState));
        CHECK_EQ(bookState.mapVars[25], 1u);
        CHECK_EQ(bookState.grantedItemIds.back(), 2160u);

        OpenYAMM::Game::EventRuntimeState controlRoomState = {};
        controlRoomState.mapVars[15] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 35, controlRoomState));
        CHECK(controlRoomState.mechanisms.contains(39));
        CHECK(controlRoomState.mechanisms.contains(40));
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "hive", "hive_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState damageState = {};
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext damageContext = {};
        damageContext.kind = OpenYAMM::Game::EventRuntimeHookKind::MonsterDamage;
        damageContext.actorIndex = 3;
        damageContext.monsterId = 647;
        damageContext.damage = 200;
        damageContext.damageType = 4;
        damageState.activeHookContext = damageContext;
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::MonsterDamage,
            damageState,
            &party));
        REQUIRE(damageState.activeHookContext.has_value());
        REQUIRE(damageState.activeHookContext->damageOverride.has_value());
        CHECK_GE(*damageState.activeHookContext->damageOverride, 2);
        CHECK_LE(*damageState.activeHookContext->damageOverride, 40);

        OpenYAMM::Game::Party reactorParty = makeScriptedRegressionParty();
        reactorParty.grantItem(2164);
        OpenYAMM::Game::EventRuntimeState reactorState = {};
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext killedContext = {};
        killedContext.kind = OpenYAMM::Game::EventRuntimeHookKind::MonsterKilled;
        killedContext.actorIndex = 4;
        killedContext.monsterId = 647;
        reactorState.activeHookContext = killedContext;
        RecordingSceneEventContext reactorContext = {};
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::MonsterKilled,
            reactorState,
            &reactorParty,
            &reactorContext));
        CHECK_EQ(reactorState.namedMapVars["HiveReactorKilled"], 1);
        CHECK_EQ(reactorContext.summonMonstersCalls.size(), 16u);
        CHECK(reactorState.mechanisms.contains(28));
        CHECK(reactorState.mechanisms.contains(30));
        REQUIRE(reactorState.pendingMapMove.has_value());
        CHECK_EQ(reactorState.pendingMapMove->directionDegrees.value_or(0), 90);

        OpenYAMM::Game::EventRuntimeState queenState = {};
        queenState.namedMapVars["HiveReactorKilled"] = 1;
        killedContext.monsterId = 646;
        queenState.activeHookContext = killedContext;
        REQUIRE(eventRuntime.executeHooks(
            localEventProgram,
            std::nullopt,
            OpenYAMM::Game::EventRuntimeHookKind::MonsterKilled,
            queenState,
            &party));
        CHECK_EQ(queenState.namedMapVars["HiveQueenKilled"], 1);
        CHECK(party.hasQuestBit(1226));

        OpenYAMM::Game::Party endingParty = makeScriptedRegressionParty();
        endingParty.grantItem(2164);
        endingParty.setQuestBit(1222, true);
        OpenYAMM::Game::EventRuntimeState endingState = {};
        endingState.namedMapVars["HiveReactorKilled"] = 1;
        endingState.namedMapVars["HiveQueenKilled"] = 1;
        REQUIRE(eventRuntime.executeOnLeaveEvents(localEventProgram, std::nullopt, endingState, &endingParty));
        REQUIRE(endingState.pendingMovie.has_value());
        CHECK_EQ(endingState.pendingMovie->movieName, "mm6end1");
        CHECK(endingParty.hasQuestBit(784));
        CHECK_FALSE(endingParty.hasQuestBit(1222));
        REQUIRE(endingParty.member(0) != nullptr);
        CHECK(endingParty.member(0)->awards.contains(78));

        OpenYAMM::Game::Party completedWithoutScrollParty = makeScriptedRegressionParty();
        completedWithoutScrollParty.setQuestBit(784, true);
        OpenYAMM::Game::EventRuntimeState completedWithoutScrollState = {};
        completedWithoutScrollState.namedMapVars["HiveReactorKilled"] = 1;
        completedWithoutScrollState.namedMapVars["HiveQueenKilled"] = 1;
        REQUIRE(eventRuntime.executeOnLeaveEvents(
            localEventProgram,
            std::nullopt,
            completedWithoutScrollState,
            &completedWithoutScrollParty));
        REQUIRE(completedWithoutScrollState.pendingMovie.has_value());
        CHECK_EQ(completedWithoutScrollState.pendingMovie->movieName, "mm6end2");
        CHECK(completedWithoutScrollState.pendingReturnToMainMenu);
        REQUIRE_FALSE(completedWithoutScrollState.pendingSounds.empty());
        CHECK_EQ(completedWithoutScrollState.pendingSounds.back().soundId, 130u);

        OpenYAMM::Game::EventRuntimeState badEndingState = {};
        badEndingState.namedMapVars["HiveReactorKilled"] = 1;
        REQUIRE(eventRuntime.executeOnLeaveEvents(localEventProgram, std::nullopt, badEndingState, &party));
        REQUIRE(badEndingState.pendingMovie.has_value());
        CHECK_EQ(badEndingState.pendingMovie->movieName, "mm6end2");
        CHECK(badEndingState.pendingReturnToMainMenu);
        REQUIRE_FALSE(badEndingState.pendingSounds.empty());
        CHECK_EQ(badEndingState.pendingSounds.back().soundId, 130u);

        OpenYAMM::Game::EventRuntimeState lockedExitState = {};
        OpenYAMM::Game::Party lockedExitParty = makeScriptedRegressionParty();
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 60, lockedExitState, &lockedExitParty));
        REQUIRE_FALSE(lockedExitState.statusMessages.empty());
        CHECK_EQ(lockedExitState.statusMessages.back(), "The door is locked");

        OpenYAMM::Game::EventRuntimeState openExitState = {};
        party.setQuestBit(1226, true);
        RecordingGameplayWorldContext openExitContext = {};
        openExitContext.setIndoorMap(true);
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            60,
            openExitState,
            &party,
            &openExitContext));
        CHECK_FALSE(openExitState.pendingDialogueContext.has_value());
        REQUIRE(openExitState.pendingMapMove.has_value());
        REQUIRE(openExitState.pendingMapMove->mapName.has_value());
        CHECK_EQ(*openExitState.pendingMapMove->mapName, "oute3.odm");
        CHECK(openExitState.pendingMapMove->useMapStartPosition);
        CHECK_FALSE(openExitState.pendingMapMove->directionDegrees.has_value());
    }
}

TEST_CASE("mm6 shadow guild scene applies spike trap facet type fixup")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "6d08.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });

    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());
    REQUIRE_GT(pLoadedMap->indoorMapData->faces.size(), 373u);
    CHECK_EQ(pLoadedMap->indoorMapData->faces[373].facetType, 5);
}

TEST_CASE("mm6 indoor stair floor facets clear imported untouchable flag")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "6d02.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });

    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());
    REQUIRE_GT(pLoadedMap->indoorMapData->faces.size(), 2503u);
    CHECK(
        hasFaceAttribute(
            pLoadedMap->indoorMapData->faces[2502].attributes,
            OpenYAMM::Game::FaceAttribute::Untouchable));
    CHECK_FALSE(
        hasFaceAttribute(
            pLoadedMap->indoorMapData->faces[2503].attributes,
            OpenYAMM::Game::FaceAttribute::Untouchable));
}

TEST_CASE("mm6 castle alamos password plate keeps pressure trigger metadata")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "cd1.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });

    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());

    size_t passwordPlateCount = 0;

    for (const OpenYAMM::Game::IndoorFace &face : pLoadedMap->indoorMapData->faces)
    {
        if (face.cogTriggered == 69
            && OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::PressurePlate))
        {
            ++passwordPlateCount;
        }
    }

    CHECK_GT(passwordPlateCount, 0u);
}

TEST_CASE("mm6 castle alamos beta memory crystal sprite override targets map sprite index")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "cd1.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });

    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());
    REQUIRE_GT(pLoadedMap->indoorMapData->entities.size(), 394u);

    const OpenYAMM::Game::IndoorEntity &crystalEntity = pLoadedMap->indoorMapData->entities[394];
    CHECK_EQ(crystalEntity.eventIdPrimary, 0u);
    CHECK_EQ(crystalEntity.eventIdSecondary, 59u);
    CHECK_EQ(crystalEntity.spriteOverrideKey(394), 394u);

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "cd1", "cd1_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 59, runtimeState, &party));

    REQUIRE(runtimeState.spriteOverrides.contains(crystalEntity.spriteOverrideKey(394)));
    CHECK_EQ(runtimeState.spriteOverrides.at(crystalEntity.spriteOverrideKey(394)).textureName, "crysdisc");
}

TEST_CASE("mm7 castle harmondale repair sprite override targets map sprite index")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "7d29.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });

    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());
    REQUIRE_GT(pLoadedMap->indoorMapData->entities.size(), 10u);

    const OpenYAMM::Game::IndoorEntity &repairEntity = pLoadedMap->indoorMapData->entities[10];
    CHECK_EQ(repairEntity.spriteOverrideKey(10), 10u);

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d29", "7d29_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    party.setQuestBit(610, true);
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 1, runtimeState, &party));

    REQUIRE(runtimeState.spriteOverrides.contains(repairEntity.spriteOverrideKey(10)));
    CHECK(runtimeState.spriteOverrides.at(repairEntity.spriteOverrideKey(10)).hidden);
}

TEST_CASE("mm6 castle alamos wrong password sends party to current-map fallback point")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> cd1Lua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps/cd1.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(cd1Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *cd1Lua,
            "@events/maps/cd1.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 69, runtimeState, nullptr, nullptr));
    REQUIRE(runtimeState.pendingInputPrompt.has_value());
    CHECK_EQ(runtimeState.pendingInputPrompt->eventId, 69);
    CHECK_EQ(runtimeState.pendingInputPrompt->continueStep, 4);

    runtimeState.pendingInputPrompt.reset();
    REQUIRE(eventRuntime.executeNpcTopicEventById(
        localEventProgram,
        std::nullopt,
        69,
        runtimeState,
        nullptr,
        nullptr,
        4));
    REQUIRE(runtimeState.pendingMapMove.has_value());
    CHECK_FALSE(runtimeState.pendingDialogueContext.has_value());
    CHECK_FALSE(runtimeState.pendingMapMove->mapName.has_value());
    CHECK_EQ(runtimeState.pendingMapMove->x, -3136);
    CHECK_EQ(runtimeState.pendingMapMove->y, 2240);
    CHECK_EQ(runtimeState.pendingMapMove->z, 224);
}

TEST_CASE("mm6 new sorpigal dragonsand exit keeps destination map name")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> oute3Lua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/maps/oute3.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(oute3Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *oute3Lua,
            "@events/maps/oute3.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 104, runtimeState, &party, nullptr));
    REQUIRE(runtimeState.pendingMapMove.has_value());
    CHECK_EQ(runtimeState.pendingMapMove->mapName, std::optional<std::string>("outb3.odm"));
    CHECK_EQ(runtimeState.pendingMapMove->x, 12808);
    CHECK_EQ(runtimeState.pendingMapMove->y, 6832);
    CHECK_EQ(runtimeState.pendingMapMove->z, 64);
}

TEST_CASE("d19 blv MoveNPC updates party global npc house overrides")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapStatsEntry *pMapEntry =
        mapLoader.gameDataLoader.getMapStats().findByFileName("d19.blv");
    const std::optional<std::string> supportLua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/common/event_support.lua");
    const std::optional<std::string> d19Lua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/maps/d19.lua");

    REQUIRE(pMapEntry != nullptr);
    REQUIRE(supportLua.has_value());
    REQUIRE(d19Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *d19Lua,
            "@Data/scripts/maps/d19.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());
    party.setQuestBit(19, true);

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        6,
        runtimeState,
        &party));

    CHECK_EQ(runtimeState.npcHouseOverrides[9], 0u);
    CHECK_EQ(runtimeState.npcHouseOverrides[56], 751u);
    CHECK_EQ(runtimeState.npcHouseOverrides[63], 213u);

    OpenYAMM::Game::EventRuntimeState seededRuntimeState = {};
    party.applyGlobalNpcStateTo(seededRuntimeState);

    CHECK_EQ(seededRuntimeState.npcHouseOverrides[9], 0u);
    CHECK_EQ(seededRuntimeState.npcHouseOverrides[56], 751u);
    CHECK_EQ(seededRuntimeState.npcHouseOverrides[63], 213u);
}

TEST_CASE("d16 on-leave events move allied dragon hunters before map exit")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::optional<std::string> supportLua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/common/event_support.lua");
    const std::optional<std::string> d16Lua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/maps/d16.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(d16Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *d16Lua,
            "@Data/scripts/maps/d16.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);

    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
    REQUIRE_EQ(localEventProgram->onLeaveEventIds().size(), 5u);
    CHECK_EQ(localEventProgram->onLeaveEventIds()[0], 6u);
    CHECK_EQ(localEventProgram->onLeaveEventIds()[4], 10u);

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());
    party.setQuestBit(21, true);

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    REQUIRE(eventRuntime.executeOnLeaveEvents(localEventProgram, std::nullopt, runtimeState, &party));

    CHECK_EQ(runtimeState.npcHouseOverrides[19], 0u);
    CHECK_EQ(runtimeState.npcHouseOverrides[52], 751u);
    CHECK_EQ(runtimeState.npcHouseOverrides[51], 753u);

    OpenYAMM::Game::EventRuntimeState seededRuntimeState = {};
    party.applyGlobalNpcStateTo(seededRuntimeState);

    CHECK_EQ(seededRuntimeState.npcHouseOverrides[19], 0u);
    CHECK_EQ(seededRuntimeState.npcHouseOverrides[52], 751u);
    CHECK_EQ(seededRuntimeState.npcHouseOverrides[51], 753u);
}

TEST_CASE("out05 authored special actors preserve relation override and carried item")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MapAssetInfo loadedMap = {};

    REQUIRE(loadOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "out05.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        },
        loadedMap));
    REQUIRE(loadedMap.outdoorMapDeltaData.has_value());
    REQUIRE_GT(loadedMap.outdoorMapDeltaData->actors.size(), 3u);

    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[0].monsterInfoId, 72);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[0].uniqueNameIndex, 3);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[0].ally, 15u);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[1].ally, 15u);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[2].ally, 15u);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[3].monsterInfoId, 45);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[3].uniqueNameIndex, 2);
    CHECK_EQ(loadedMap.outdoorMapDeltaData->actors[3].carriedItemId, 540u);

    OpenYAMM::Game::GameplayActorService actorService = {};
    actorService.bindTables(&mapLoader.gameDataLoader.getMonsterTable(), &mapLoader.gameDataLoader.getSpellTable());

    OpenYAMM::Game::GameplayActorTargetPolicyState dragonslayer = {};
    dragonslayer.monsterId = 45;
    dragonslayer.relationMonsterId = actorService.relationMonsterId(dragonslayer.monsterId, 15);
    dragonslayer.height = 160;

    OpenYAMM::Game::GameplayActorTargetPolicyState pet = {};
    pet.monsterId = 72;
    pet.relationMonsterId = actorService.relationMonsterId(pet.monsterId, 15);
    pet.height = 500;

    CHECK_GT(mapLoader.gameDataLoader.getMonsterTable().getRelationBetweenMonsters(45, 72), 0);
    CHECK_FALSE(actorService.resolveActorTargetPolicy(dragonslayer, pet).canTarget);

    OpenYAMM::Game::GameplayActorTargetPolicyState naturalDragonslayer = dragonslayer;
    naturalDragonslayer.relationMonsterId =
        actorService.relationMonsterId(naturalDragonslayer.monsterId, 0);

    OpenYAMM::Game::GameplayActorTargetPolicyState naturalDragon = pet;
    naturalDragon.relationMonsterId = actorService.relationMonsterId(naturalDragon.monsterId, 0);

    CHECK(actorService.resolveActorTargetPolicy(naturalDragonslayer, naturalDragon).canTarget);
    CHECK_FALSE(actorService.resolveActorTargetPolicy(naturalDragon, naturalDragonslayer).canTarget);

    naturalDragonslayer.group = 24;
    naturalDragon.group = 24;
    CHECK_FALSE(actorService.resolveActorTargetPolicy(naturalDragonslayer, naturalDragon).canTarget);
}

TEST_CASE("mm7 world prefixed monster sprites resolve on Emerald Island")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "7out01.odm",
        OpenYAMM::Game::MapLoadPurpose::ActorPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->outdoorActorPreviewBillboardSet.has_value());

    const OpenYAMM::Game::ActorPreviewBillboardSet &billboardSet =
        *pLoadedMap->outdoorActorPreviewBillboardSet;
    CHECK(billboardSet.spriteFrameTable.findFrameIndexBySpriteName("7m409s").has_value());

    const auto standingTextureIt = std::find_if(
        billboardSet.textures.begin(),
        billboardSet.textures.end(),
        [](const OpenYAMM::Game::OutdoorBitmapTexture &texture)
        {
            return texture.textureName == "m406sa0" && texture.paletteId == 409;
        });
    REQUIRE(standingTextureIt != billboardSet.textures.end());
    REQUIRE_GE(standingTextureIt->physicalWidth, 133);
    REQUIRE_GE(standingTextureIt->physicalHeight, 94);

    const size_t torsoPixelOffset =
        (static_cast<size_t>(78) * static_cast<size_t>(standingTextureIt->physicalWidth) + 127u) * 4u;
    REQUIRE_LT(torsoPixelOffset + 3u, standingTextureIt->pixels.size());
    CHECK_EQ(standingTextureIt->pixels[torsoPixelOffset + 0u], 68u);
    CHECK_EQ(standingTextureIt->pixels[torsoPixelOffset + 1u], 73u);
    CHECK_EQ(standingTextureIt->pixels[torsoPixelOffset + 2u], 82u);
    CHECK_EQ(standingTextureIt->pixels[torsoPixelOffset + 3u], 255u);

    bool foundAdventurer = false;

    for (const OpenYAMM::Game::ActorPreviewBillboard &billboard : billboardSet.billboards)
    {
        if (billboard.monsterId != 405)
        {
            continue;
        }

        foundAdventurer = true;
        CHECK_NE(billboard.spriteFrameIndex, 0u);
        CHECK_NE(
            billboard.actionSpriteFrameIndices[
                static_cast<size_t>(OpenYAMM::Game::OutdoorWorldRuntime::ActorAnimation::Standing)],
            0u);
    }

    CHECK(foundAdventurer);
}

TEST_CASE("mm7 world prefixed monster sprites load for indoor actor previews")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "7d06.blv",
        OpenYAMM::Game::MapLoadPurpose::ActorPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorActorPreviewBillboardSet.has_value());

    const OpenYAMM::Game::ActorPreviewBillboardSet &billboardSet =
        *pLoadedMap->indoorActorPreviewBillboardSet;
    const std::optional<uint16_t> swordsmanFrameIndex =
        billboardSet.spriteFrameTable.findFrameIndexBySpriteName("7m407s");
    REQUIRE(swordsmanFrameIndex.has_value());
    const OpenYAMM::Game::SpriteFrameEntry *pSwordsmanFrame =
        billboardSet.spriteFrameTable.getFrame(*swordsmanFrameIndex, 0);
    REQUIRE(pSwordsmanFrame != nullptr);
    const OpenYAMM::Game::ResolvedSpriteTexture swordsmanTexture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pSwordsmanFrame, 0);
    CHECK_EQ(swordsmanTexture.textureName, "m406sa0");
    CHECK_EQ(pSwordsmanFrame->paletteId, 70);
    REQUIRE_GT(billboardSet.mapDeltaActorCount, 0u);
    CHECK_EQ(billboardSet.missingTextureActorCount, 0u);
    CHECK_EQ(billboardSet.texturedActorCount, billboardSet.billboards.size());
    CHECK_FALSE(billboardSet.textures.empty());
}

TEST_CASE("mm7 nighon actor previews load world sprite packages")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();

    const auto textureLoaded =
        [](const OpenYAMM::Game::ActorPreviewBillboardSet &billboardSet,
           const std::string &textureName,
           int16_t paletteId) -> bool
        {
            return std::any_of(
                billboardSet.textures.begin(),
                billboardSet.textures.end(),
                [&](const OpenYAMM::Game::OutdoorBitmapTexture &texture)
                {
                    return texture.textureName == textureName && texture.paletteId == paletteId;
                });
        };

    const OpenYAMM::Game::MapAssetInfo *pMountNighon = loadCachedOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "out10.odm",
        OpenYAMM::Game::MapLoadPurpose::ActorPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pMountNighon != nullptr);
    REQUIRE(pMountNighon->outdoorActorPreviewBillboardSet.has_value());
    CHECK_EQ(pMountNighon->outdoorActorPreviewBillboardSet->missingTextureActorCount, 0u);
    CHECK(textureLoaded(*pMountNighon->outdoorActorPreviewBillboardSet, "m390sa0", 553));
    CHECK(textureLoaded(*pMountNighon->outdoorActorPreviewBillboardSet, "m390sa0", 555));

    const OpenYAMM::Game::MapAssetInfo *pNighonTunnels = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "7d35.blv",
        OpenYAMM::Game::MapLoadPurpose::ActorPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pNighonTunnels != nullptr);
    REQUIRE(pNighonTunnels->indoorActorPreviewBillboardSet.has_value());
    CHECK_EQ(pNighonTunnels->indoorActorPreviewBillboardSet->missingTextureActorCount, 0u);
    CHECK(textureLoaded(*pNighonTunnels->indoorActorPreviewBillboardSet, "m250sa0", 613));
    CHECK(textureLoaded(*pNighonTunnels->indoorActorPreviewBillboardSet, "m250sa0", 615));
}

TEST_CASE("mm6 circus prize games require the 50 gold entry fee")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm6GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());
    REQUIRE(globalEventProgram->hasEvent(1424));

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        REQUIRE(party.member(0) != nullptr);
        party.member(0)->luck = 200;
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1424, runtimeState, &party));
        CHECK_EQ(party.gold(), 0);
        CHECK_EQ(circusPrizeItemCount(party), 0);
        CHECK(runtimeState.messages.empty());
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        REQUIRE(party.member(0) != nullptr);
        party.member(0)->luck = 200;
        party.addGold(50);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1424, runtimeState, &party));
        CHECK_EQ(party.gold(), 0);
        REQUIRE_FALSE(runtimeState.messages.empty());
    }
}

TEST_CASE("mm6 circus master trades souvenir points for keg or pyramid")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm6GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());
    REQUIRE(globalEventProgram->hasEvent(1418));

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        REQUIRE(party.member(0) != nullptr);
        for (int itemIndex = 0; itemIndex < 9; ++itemIndex)
        {
            party.member(0)->inventory.push_back(makeScriptedInventoryItem(2090));
        }
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1418, runtimeState, &party));
        CHECK_EQ(party.inventoryItemCount(2090), 9);
        CHECK_EQ(party.inventoryItemCount(2093), 0);
        CHECK_EQ(party.inventoryItemCount(2092), 0);
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK(runtimeState.messages.back().find("don't have 10 points") != std::string::npos);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        REQUIRE(party.member(0) != nullptr);
        party.member(0)->inventory.push_back(makeScriptedInventoryItem(2097));
        party.member(0)->inventory.push_back(makeScriptedInventoryItem(2097));
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1418, runtimeState, &party));
        CHECK_EQ(circusPrizeItemCount(party), 0);
        CHECK_EQ(eventInventoryItemCount(runtimeState, party, 2093), 1);
        CHECK_EQ(eventInventoryItemCount(runtimeState, party, 2092), 0);
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK(runtimeState.messages.back().find("win a keg of wine") != std::string::npos);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        REQUIRE(party.member(0) != nullptr);
        for (int itemIndex = 0; itemIndex < 6; ++itemIndex)
        {
            party.member(0)->inventory.push_back(makeScriptedInventoryItem(2097));
        }
        OpenYAMM::Game::EventRuntimeState runtimeState = {};

        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalEventProgram, 1418, runtimeState, &party));
        CHECK_EQ(circusPrizeItemCount(party), 0);
        CHECK_EQ(eventInventoryItemCount(runtimeState, party, 2093), 0);
        CHECK_EQ(eventInventoryItemCount(runtimeState, party, 2092), 1);
        REQUIRE_FALSE(runtimeState.messages.empty());
        CHECK(runtimeState.messages.back().find("win a golden pyramid") != std::string::npos);
    }
}

TEST_CASE("mm7 Mount Nighon local relations keep resident warlocks peaceful to town peasants")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MapAssetInfo loadedMap = {};

    REQUIRE(loadOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "out10.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        },
        loadedMap));
    REQUIRE(loadedMap.outdoorMapDeltaData.has_value());

    const std::vector<OpenYAMM::Game::MapDeltaActor> &actors = loadedMap.outdoorMapDeltaData->actors;
    REQUIRE_GT(actors.size(), 31u);

    for (size_t actorIndex = 0; actorIndex <= 8; ++actorIndex)
    {
        CHECK_EQ(actors[actorIndex].monsterInfoId, 419);
        CHECK_EQ(actors[actorIndex].group, 55u);
    }

    CHECK_EQ(actors[12].group, 79u);
    CHECK_EQ(actors[13].group, 77u);
    CHECK_EQ(actors[30].group, 77u);
    CHECK_EQ(actors[31].group, 78u);

    OpenYAMM::Game::GameplayActorService actorService = {};
    actorService.bindTables(&mapLoader.gameDataLoader.getMonsterTable(), &mapLoader.gameDataLoader.getSpellTable());

    OpenYAMM::Game::GameplayActorTargetPolicyState warlock = {};
    warlock.monsterId = actors[0].monsterInfoId;
    warlock.relationMonsterId = actorService.relationMonsterId(warlock.monsterId, actors[0].ally);
    warlock.group = actors[0].group;
    warlock.height = actors[0].height;

    OpenYAMM::Game::GameplayActorTargetPolicyState peasant = {};
    peasant.monsterId = actors[9].monsterInfoId;
    peasant.relationMonsterId = actorService.relationMonsterId(peasant.monsterId, actors[9].ally);
    peasant.group = actors[9].group;
    peasant.height = actors[9].height;

    CHECK(actorService.resolveActorTargetPolicy(warlock, peasant).canTarget);

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out10", "out10_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));

    for (uint32_t peasantId = 360; peasantId <= 366; ++peasantId)
    {
        const uint32_t warlockToPeasantKey =
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(419, peasantId);
        const uint32_t peasantToWarlockKey =
            OpenYAMM::Game::EventRuntime::monsterRelationOverrideKey(peasantId, 419);

        REQUIRE(runtimeState.monsterRelationOverrides.contains(warlockToPeasantKey));
        CHECK_EQ(runtimeState.monsterRelationOverrides.at(warlockToPeasantKey), 0);
        REQUIRE(runtimeState.monsterRelationOverrides.contains(peasantToWarlockKey));
        CHECK_EQ(runtimeState.monsterRelationOverrides.at(peasantToWarlockKey), 0);
    }
}

TEST_CASE("mm7 walls of mist air elementals resolve actor preview textures")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "7d11.blv",
        OpenYAMM::Game::MapLoadPurpose::ActorPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorActorPreviewBillboardSet.has_value());

    const OpenYAMM::Game::ActorPreviewBillboardSet &billboardSet =
        *pLoadedMap->indoorActorPreviewBillboardSet;
    const auto airElementalIt = std::find_if(
        billboardSet.billboards.begin(),
        billboardSet.billboards.end(),
        [](const OpenYAMM::Game::ActorPreviewBillboard &billboard)
        {
            return billboard.monsterId == 232;
        });
    REQUIRE(airElementalIt != billboardSet.billboards.end());
    CHECK_NE(airElementalIt->spriteFrameIndex, 0u);

    const std::optional<uint16_t> airElementalCFrameIndex =
        billboardSet.spriteFrameTable.findFrameIndexBySpriteName("m197s");
    REQUIRE(airElementalCFrameIndex.has_value());
    const OpenYAMM::Game::SpriteFrameEntry *pAirElementalCFrame =
        billboardSet.spriteFrameTable.getFrame(*airElementalCFrameIndex, 0);
    REQUIRE(pAirElementalCFrame != nullptr);
    const OpenYAMM::Game::ResolvedSpriteTexture airElementalTexture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pAirElementalCFrame, 0);
    CHECK_EQ(airElementalTexture.textureName, "m508sa0");
    CHECK_EQ(pAirElementalCFrame->paletteId, 508);

    const auto textureIt = std::find_if(
        billboardSet.textures.begin(),
        billboardSet.textures.end(),
        [&airElementalTexture, pAirElementalCFrame](const OpenYAMM::Game::OutdoorBitmapTexture &texture)
        {
            return texture.textureName == airElementalTexture.textureName
                && texture.paletteId == pAirElementalCFrame->paletteId;
        });
    CHECK(textureIt != billboardSet.textures.end());
}

TEST_CASE("mm7 dragon lair loads indoor billboards and lights")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "7d28.blv",
        OpenYAMM::Game::MapLoadPurpose::BillboardPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());
    CHECK_FALSE(pLoadedMap->indoorMapData->lights.empty());
    REQUIRE(pLoadedMap->indoorDecorationBillboardSet.has_value());
    CHECK_FALSE(pLoadedMap->indoorDecorationBillboardSet->billboards.empty());
    CHECK_FALSE(pLoadedMap->indoorDecorationBillboardSet->textures.empty());
    CHECK(std::any_of(
        pLoadedMap->indoorDecorationBillboardSet->billboards.begin(),
        pLoadedMap->indoorDecorationBillboardSet->billboards.end(),
        [](const OpenYAMM::Game::DecorationBillboard &billboard)
        {
            return billboard.sectorId >= 0;
        }));
    REQUIRE(pLoadedMap->indoorActorPreviewBillboardSet.has_value());
    CHECK_GT(pLoadedMap->indoorActorPreviewBillboardSet->billboards.size(), 0u);
    CHECK_EQ(pLoadedMap->indoorActorPreviewBillboardSet->missingTextureActorCount, 0u);
    CHECK_EQ(
        pLoadedMap->indoorActorPreviewBillboardSet->texturedActorCount,
        pLoadedMap->indoorActorPreviewBillboardSet->billboards.size());
}

TEST_CASE("mm8 abandoned temple buttons resolve SetLight by authored light group id")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "d05.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());

    const OpenYAMM::Game::IndoorMapData &mapData = *pLoadedMap->indoorMapData;
    REQUIRE_GT(mapData.faces.size(), 776u);
    REQUIRE_GT(mapData.lights.size(), 5u);
    CHECK_EQ(mapData.faces[776].cogTriggered, 104u);
    CHECK_EQ(mapData.faces[776].cogNumber, 3u);
    CHECK_EQ(mapData.lights[3].id, 3);
    CHECK_EQ(mapData.lights[2].id, 4);
    CHECK_EQ(mapData.lights[4].id, 5);

    CHECK_EQ(OpenYAMM::Game::resolveIndoorLightReferenceIds(mapData, 3), std::vector<uint32_t>{3u});
    CHECK_EQ(OpenYAMM::Game::resolveIndoorLightReferenceIds(mapData, 4), std::vector<uint32_t>{2u});
    CHECK_EQ(OpenYAMM::Game::resolveIndoorLightReferenceIds(mapData, 5), std::vector<uint32_t>{4u});

    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm8/events/common/mm8_common.lua");
    const std::optional<std::string> d05Lua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm8/events/maps/d05.lua");
    REQUIRE(supportLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(d05Lua.has_value());

    CHECK(d05Lua->find("RegisterEvent(104") != std::string::npos);
    CHECK(d05Lua->find("evt.SetLight(3, 0)") != std::string::npos);

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> lightProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *commonLua + "\n\n"
            "RegisterEvent(1, \"Button\", function()\n"
            "    evt.SetLight(3, 0)\n"
            "end, \"Button\")\n",
            "@tests/mm8_light_group.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(lightProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    RecordingSceneEventContext sceneContext = {};
    sceneContext.pIndoorMapData = &mapData;

    REQUIRE(eventRuntime.executeEventById(
        lightProgram,
        std::nullopt,
        1,
        runtimeState,
        &party,
        &sceneContext));

    const auto light3Iterator = runtimeState.indoorLightsEnabled.find(3u);
    REQUIRE(light3Iterator != runtimeState.indoorLightsEnabled.end());
    CHECK_FALSE(light3Iterator->second);
    CHECK(runtimeState.indoorLightsEnabled.find(2u) == runtimeState.indoorLightsEnabled.end());
}

TEST_CASE("mm6 darkmoor actor previews preload random encounter tier textures")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "cd2.blv",
        OpenYAMM::Game::MapLoadPurpose::ActorPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorActorPreviewBillboardSet.has_value());

    const OpenYAMM::Game::ActorPreviewBillboardSet &billboardSet =
        *pLoadedMap->indoorActorPreviewBillboardSet;
    const OpenYAMM::Game::MapStatsEntry *pMapEntry =
        mapLoader.gameDataLoader.getMapStats().findByFileName("cd2.blv");
    REQUIRE(pMapEntry != nullptr);

    const auto textureLoaded =
        [&billboardSet](const std::string &textureName, int16_t paletteId) -> bool
        {
            return std::any_of(
                billboardSet.textures.begin(),
                billboardSet.textures.end(),
                [&](const OpenYAMM::Game::OutdoorBitmapTexture &texture)
                {
                    return texture.textureName == textureName && texture.paletteId == paletteId;
                });
        };
    const auto requireTierTexture =
        [&](const OpenYAMM::Game::MapEncounterInfo &encounter, char tierLetter)
        {
            const std::string pictureBase =
                encounter.pictureName.empty() ? encounter.monsterName : encounter.pictureName;
            const std::string pictureName = pictureBase + " " + std::string(1, tierLetter);
            const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats =
                mapLoader.gameDataLoader.getMonsterTable().findStatsByPictureName(pictureName);
            REQUIRE(pStats != nullptr);

            const OpenYAMM::Game::MonsterEntry *pMonsterEntry =
                mapLoader.gameDataLoader.getMonsterTable().findById(static_cast<int16_t>(pStats->id));
            REQUIRE(pMonsterEntry != nullptr);

            bool checkedAnySprite = false;

            for (const std::string &spriteName : pMonsterEntry->spriteNames)
            {
                if (spriteName.empty() || spriteName == "null")
                {
                    continue;
                }

                const std::optional<uint16_t> spriteFrameIndex =
                    billboardSet.spriteFrameTable.findFrameIndexBySpriteName(spriteName);
                REQUIRE(spriteFrameIndex.has_value());

                const OpenYAMM::Game::SpriteFrameEntry *pFrame =
                    billboardSet.spriteFrameTable.getFrame(*spriteFrameIndex, 0);
                REQUIRE(pFrame != nullptr);

                const OpenYAMM::Game::ResolvedSpriteTexture resolvedTexture =
                    OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
                CHECK(textureLoaded(resolvedTexture.textureName, pFrame->paletteId));
                checkedAnySprite = true;
            }

            CHECK(checkedAnySprite);
        };

    const std::array<const OpenYAMM::Game::MapEncounterInfo *, 3> encounters = {{
        &pMapEntry->encounter1,
        &pMapEntry->encounter2,
        &pMapEntry->encounter3,
    }};

    for (const OpenYAMM::Game::MapEncounterInfo *pEncounter : encounters)
    {
        REQUIRE(pEncounter != nullptr);
        requireTierTexture(*pEncounter, 'B');
        requireTierTexture(*pEncounter, 'C');
    }
}

TEST_CASE("mm6 darkmoor indoor decoration billboards keep editor room ownership")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "cd2.blv",
        OpenYAMM::Game::MapLoadPurpose::BillboardPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorDecorationBillboardSet.has_value());

    struct ExpectedDecorationSector
    {
        size_t entityIndex = 0;
        int16_t sectorId = -1;
    };

    const std::array<ExpectedDecorationSector, 21> expectedSectors = {{
        {328, 51},
        {327, 51},
        {292, 50},
        {291, 50},
        {293, 50},
        {294, 50},
        {267, 80},
        {264, 80},
        {268, 80},
        {266, 80},
        {265, 80},
        {269, 80},
        {270, 80},
        {372, 71},
        {373, 71},
        {374, 71},
        {375, 71},
        {376, 71},
        {385, 71},
        {386, 71},
        {387, 71},
    }};

    for (const ExpectedDecorationSector &expected : expectedSectors)
    {
        const std::vector<OpenYAMM::Game::DecorationBillboard> &billboards =
            pLoadedMap->indoorDecorationBillboardSet->billboards;
        const std::vector<OpenYAMM::Game::DecorationBillboard>::const_iterator billboardIt =
            std::find_if(
                billboards.begin(),
                billboards.end(),
                [&expected](const OpenYAMM::Game::DecorationBillboard &billboard)
                {
                    return billboard.entityIndex == expected.entityIndex;
                });

        REQUIRE_MESSAGE(
            billboardIt != billboards.end(),
            ("missing Darkmoor decoration billboard " + std::to_string(expected.entityIndex)).c_str());
        CHECK_EQ(billboardIt->sectorId, expected.sectorId);
    }
}

TEST_CASE("outdoor water bmodel faces load terrain-owned animation frames")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();

    struct WaterMapCase
    {
        const char *pMapFileName = nullptr;
        const char *pBaseTextureName = nullptr;
        const char *pFirstFrameTextureName = nullptr;
        const char *pLastFrameTextureName = nullptr;
    };

    const std::array<WaterMapCase, 3> waterMapCases = {{
        {"out01.odm", "wtrtyl", "hdwtr000", "hdwtr013"},
        {"7out01.odm", "7wtrtyl", "7hdwtr000", "7hdwtr013"},
        {"oute3.odm", "6wtrtyl", "6hdwtr000", "6hdwtr013"},
    }};

    for (const WaterMapCase &waterMapCase : waterMapCases)
    {
        const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedOutdoorMapWithCompanionOptions(
            mapLoader.assetFileSystem,
            mapLoader.gameDataLoader,
            waterMapCase.pMapFileName,
            OpenYAMM::Game::MapLoadPurpose::RenderSurfaces,
            OpenYAMM::Game::MapCompanionLoadOptions{
                .allowSceneYml = true,
                .allowLegacyCompanion = true,
            });
        REQUIRE(pLoadedMap != nullptr);
        REQUIRE(pLoadedMap->outdoorBModelTextureSet.has_value());

        const OpenYAMM::Game::OutdoorBModelTextureSet &textureSet = *pLoadedMap->outdoorBModelTextureSet;
        CHECK(bitmapTextureSetContains(textureSet.textures, waterMapCase.pBaseTextureName));
        CHECK(bitmapTextureSetContains(textureSet.textures, waterMapCase.pFirstFrameTextureName));
        CHECK(bitmapTextureSetContains(textureSet.textures, waterMapCase.pLastFrameTextureName));

        const OpenYAMM::Game::SurfaceAnimationSequence *pAnimation =
            findSurfaceAnimationBinding(textureSet.animationBindings, waterMapCase.pBaseTextureName);
        REQUIRE(pAnimation != nullptr);
        CHECK(pAnimation->frames.size() == 14);
        CHECK(pAnimation->animationLengthTicks == 210);
        CHECK(pAnimation->frames.front().textureName == waterMapCase.pFirstFrameTextureName);
        CHECK(pAnimation->frames.back().textureName == waterMapCase.pLastFrameTextureName);
    }
}

TEST_CASE("outdoor terrain water transition tiles do not use full-tile shader warp")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();

    struct WaterTransitionMapCase
    {
        const char *pMapFileName = nullptr;
        uint8_t fullWaterTileId = 0;
        uint8_t transitionWaterTileId = 0;
    };

    const std::array<WaterTransitionMapCase, 3> waterMapCases = {{
        {"out01.odm", 126, 138},
        {"7out01.odm", 126, 138},
        {"oute3.odm", 126, 138},
    }};

    for (const WaterTransitionMapCase &waterMapCase : waterMapCases)
    {
        const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedOutdoorMapWithCompanionOptions(
            mapLoader.assetFileSystem,
            mapLoader.gameDataLoader,
            waterMapCase.pMapFileName,
            OpenYAMM::Game::MapLoadPurpose::RenderSurfaces,
            OpenYAMM::Game::MapCompanionLoadOptions{
                .allowSceneYml = true,
                .allowLegacyCompanion = true,
            });
        REQUIRE(pLoadedMap != nullptr);
        REQUIRE(pLoadedMap->outdoorTerrainTextureAtlas.has_value());

        const OpenYAMM::Game::OutdoorTerrainTextureAtlas &atlas = *pLoadedMap->outdoorTerrainTextureAtlas;
        const OpenYAMM::Game::OutdoorTerrainAtlasRegion &fullWaterRegion =
            atlas.tileRegions[static_cast<size_t>(waterMapCase.fullWaterTileId)];
        const OpenYAMM::Game::OutdoorTerrainAtlasRegion &cachedFullWaterRegion =
            atlas.tileRegions[static_cast<size_t>(waterMapCase.fullWaterTileId + 1)];
        const OpenYAMM::Game::OutdoorTerrainAtlasRegion &transitionWaterRegion =
            atlas.tileRegions[static_cast<size_t>(waterMapCase.transitionWaterTileId)];

        REQUIRE(fullWaterRegion.isValid);
        CHECK(fullWaterRegion.isWater);
        CHECK_FALSE(fullWaterRegion.isTransitionOverlay);

        REQUIRE(cachedFullWaterRegion.isValid);
        CHECK(cachedFullWaterRegion.isWater);
        CHECK_FALSE(cachedFullWaterRegion.isTransitionOverlay);

        REQUIRE(transitionWaterRegion.isValid);
        CHECK(transitionWaterRegion.isWater);
        CHECK(transitionWaterRegion.isTransitionOverlay);

        const auto findAnimatedTileSource =
            [&](const OpenYAMM::Game::OutdoorTerrainAtlasRegion &region)
            -> const OpenYAMM::Game::OutdoorAnimatedWaterTileSource *
            {
                for (const OpenYAMM::Game::OutdoorAnimatedWaterTileSource &source : atlas.animatedWaterTiles)
                {
                    if (source.region.u0 == region.u0
                        && source.region.v0 == region.v0
                        && source.region.u1 == region.u1
                        && source.region.v1 == region.v1)
                    {
                        return &source;
                    }
                }

                return nullptr;
            };

        const OpenYAMM::Game::OutdoorAnimatedWaterTileSource *pFullWaterSource =
            findAnimatedTileSource(fullWaterRegion);
        const OpenYAMM::Game::OutdoorAnimatedWaterTileSource *pCachedFullWaterSource =
            findAnimatedTileSource(cachedFullWaterRegion);

        REQUIRE(pFullWaterSource != nullptr);
        REQUIRE(pCachedFullWaterSource != nullptr);
        CHECK(pFullWaterSource->framePixels.size() == 14);
        CHECK(pFullWaterSource->animation.frames.size() == 14);
        CHECK(pFullWaterSource->animation.animationLengthTicks == 210);
        CHECK(pCachedFullWaterSource->framePixels.size() == 14);
        CHECK(pCachedFullWaterSource->animation.frames.size() == 14);
        CHECK(pCachedFullWaterSource->animation.animationLengthTicks == 210);
    }
}

TEST_CASE("d06 indoor actor loader preserves Blackwell Cooper guaranteed key drop")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MapAssetInfo loadedMap = {};

    REQUIRE(loadIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "d06.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = false,
            .allowLegacyCompanion = true,
        },
        loadedMap));
    REQUIRE(loadedMap.indoorMapDeltaData.has_value());
    REQUIRE_GT(loadedMap.indoorMapDeltaData->actors.size(), 0u);

    const OpenYAMM::Game::MapDeltaActor &blackwell = loadedMap.indoorMapDeltaData->actors[0];
    CHECK_EQ(blackwell.uniqueNameIndex, 1);
    CHECK_EQ(blackwell.sectorId, 11);
    CHECK_EQ(blackwell.carriedItemId, 619u);

    OpenYAMM::Game::MapAssetInfo sceneLoadedMap = {};
    REQUIRE(loadIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "d06.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        },
        sceneLoadedMap));
    REQUIRE(sceneLoadedMap.indoorMapDeltaData.has_value());
    REQUIRE_GT(sceneLoadedMap.indoorMapDeltaData->actors.size(), 0u);
    CHECK_EQ(sceneLoadedMap.indoorMapDeltaData->actors[0].carriedItemId, 619u);
}

TEST_CASE("d06 submarine event plays cutscene and moves to small sub pen")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const std::optional<std::string> supportLua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/common/event_support.lua");
    const std::optional<std::string> d06Lua =
        mapLoader.assetFileSystem.readTextFile("Data/scripts/maps/d06.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(d06Lua.has_value());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *d06Lua,
            "@Data/scripts/maps/d06.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::InventoryItem pirateLeaderKey = {};
    pirateLeaderKey.objectDescriptionId = 619;
    REQUIRE(party.tryGrantInventoryItem(pirateLeaderKey));

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 451, runtimeState, &party, nullptr));
    REQUIRE(runtimeState.pendingMovie.has_value());
    CHECK_EQ(runtimeState.pendingMovie->movieName, "\"Subcut\"");
    CHECK(runtimeState.pendingMovie->restoreAfterPlayback);
    REQUIRE(runtimeState.pendingMapMove.has_value());
    CHECK_EQ(runtimeState.pendingMapMove->mapName, std::optional<std::string>("d34.blv"));
    CHECK_EQ(runtimeState.pendingMapMove->x, -2416);
    CHECK_EQ(runtimeState.pendingMapMove->y, 1850);
    CHECK_EQ(runtimeState.pendingMapMove->z, -687);
}

TEST_CASE("corpse loot includes authored guaranteed carried item")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MonsterTable::LootPrototype noRandomLoot = {};

    const OpenYAMM::Game::GameplayCorpseViewState corpse = OpenYAMM::Game::buildMonsterCorpseView(
        "Jeric Whistlebone",
        noRandomLoot,
        &mapLoader.gameDataLoader.getItemTable(),
        nullptr,
        {540});

    REQUIRE_EQ(corpse.items.size(), 1u);
    CHECK_EQ(corpse.items.front().itemId, 540u);
    CHECK_EQ(corpse.items.front().item.objectDescriptionId, 540u);
}

TEST_CASE("corpse loot with authored guaranteed carried item suppresses random item roll")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());

    OpenYAMM::Game::MonsterTable::LootPrototype guaranteedRandomLoot = {};
    guaranteedRandomLoot.goldDiceRolls = 1;
    guaranteedRandomLoot.goldDiceSides = 1;
    guaranteedRandomLoot.itemChance = 100;
    guaranteedRandomLoot.itemLevel = 1;
    guaranteedRandomLoot.itemKind = OpenYAMM::Game::MonsterTable::LootItemKind::Any;

    const OpenYAMM::Game::GameplayCorpseViewState corpse = OpenYAMM::Game::buildMonsterCorpseView(
        "Jeric Whistlebone",
        guaranteedRandomLoot,
        &mapLoader.gameDataLoader.getItemTable(),
        &party,
        {540});

    REQUIRE_EQ(corpse.items.size(), 2u);
    CHECK(corpse.items[0].isGold);
    CHECK_EQ(corpse.items[0].goldAmount, 1u);
    CHECK_FALSE(corpse.items[1].isGold);
    CHECK_EQ(corpse.items[1].itemId, 540u);
    CHECK_EQ(corpse.items[1].item.objectDescriptionId, 540u);
}

TEST_CASE("outdoor_party_runtime_wait_advances_buff_durations_with_game_clock")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::MapAssetInfo loadedMap = {};

    REQUIRE(loadOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "out01.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        },
        loadedMap));
    REQUIRE(loadedMap.outdoorMapData.has_value());

    OpenYAMM::Game::OutdoorMovementDriver movementDriver(
        *loadedMap.outdoorMapData,
        loadedMap.outdoorLandMask,
        loadedMap.outdoorDecorationCollisionSet,
        loadedMap.outdoorActorCollisionSet,
        loadedMap.outdoorSpriteObjectCollisionSet);
    OpenYAMM::Game::OutdoorPartyRuntime partyRuntime(
        std::move(movementDriver),
        mapLoader.gameDataLoader.getItemTable());
    OpenYAMM::Game::Party party = {};
    party.setItemTable(&mapLoader.gameDataLoader.getItemTable());
    party.setItemEnchantTables(
        &mapLoader.gameDataLoader.getStandardItemEnchantTable(),
        &mapLoader.gameDataLoader.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&mapLoader.gameDataLoader.getClassMultiplierTable());
    party.setClassSkillTable(&mapLoader.gameDataLoader.getClassSkillTable());
    party.seed(createRegressionPartySeed());
    party.applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::FireResistance,
        36000.0f,
        1,
        0,
        0,
        OpenYAMM::Game::SkillMastery::None,
        0);
    partyRuntime.setParty(party);
    partyRuntime.initialize(8704.0f, 2000.0f, 686.0f, false);

    const OpenYAMM::Game::PartyBuffState *pInitialBuff =
        partyRuntime.party().partyBuff(OpenYAMM::Game::PartyBuffId::FireResistance);
    REQUIRE(pInitialBuff != nullptr);
    CHECK(pInitialBuff->remainingSeconds == doctest::Approx(36000.0f));

    OpenYAMM::Game::OutdoorMovementInput idleInput = {};
    partyRuntime.update(idleInput, 2.0f);

    const OpenYAMM::Game::PartyBuffState *pUpdatedBuff =
        partyRuntime.party().partyBuff(OpenYAMM::Game::PartyBuffId::FireResistance);
    REQUIRE(pUpdatedBuff != nullptr);
    CHECK(pUpdatedBuff->remainingSeconds == doctest::Approx(35940.0f));
}
