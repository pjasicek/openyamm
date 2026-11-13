#include "doctest/doctest.h"

#include "engine/SpriteAtlas.h"

#include "game/SpriteObjectDefs.h"
#include "game/events/EventRuntime.h"
#include "game/events/EventDialogContent.h"
#include "game/events/ISceneEventContext.h"
#include "game/FaceEnums.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/items/InventoryBags.h"
#include "game/gameplay/GameplayActorHitFeedback.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/JournalArcomageRuntime.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/maps/ActorModelManifest.h"
#include "game/maps/MapAssetLoader.h"
#include "game/StringUtils.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"
#include "game/tables/CharacterDollTable.h"

#include "tests/RegressionGameData.h"
#include "tests/RegressionMapLoader.h"

#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <memory>
#include <filesystem>
#include <optional>
#include <sstream>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

TEST_SUITE_BEGIN(OpenYAMM::Tests::SharedRegressionMapSuite);

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

    struct PersistentItemMechanismStateCall
    {
        std::string sourceId;
        bool visible = false;
        bool solid = false;
    };

    struct PersistentItemMechanismVariantCall
    {
        std::string sourceId;
        uint32_t variantIndex = 0;
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

    bool summonEventObject(
        uint32_t objectId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate) override
    {
        (void)objectId;
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

    bool consumeWorldItem(const std::string &sourceId) override
    {
        consumedWorldItemSourceIds.push_back(sourceId);
        return true;
    }

    bool setPersistentItemMechanismState(
        const std::string &sourceId,
        bool visible,
        bool solid) override
    {
        persistentItemMechanismStateCalls.push_back({sourceId, visible, solid});
        return true;
    }

    bool setPersistentItemMechanismVariant(
        const std::string &sourceId,
        uint32_t variantIndex) override
    {
        persistentItemMechanismVariantCalls.push_back({sourceId, variantIndex});
        return true;
    }

    bool isMapActorHostile(size_t actorIndex) const override
    {
        return actorIndex == hostileActorIndex;
    }

    bool isMapActorWithinPartyDistance(size_t actorIndex, float distance) const override
    {
        return actorIndex == nearbyActorIndex && distance >= nearbyActorDistance;
    }

    std::vector<CastSpellCall> castSpellCalls;
    std::vector<SummonMonstersCall> summonMonstersCalls;
    std::vector<OutdoorModelMechanismCall> outdoorModelMechanismCalls;
    std::vector<std::string> consumedWorldItemSourceIds;
    std::vector<PersistentItemMechanismStateCall> persistentItemMechanismStateCalls;
    std::vector<PersistentItemMechanismVariantCall> persistentItemMechanismVariantCalls;
    std::unordered_map<uint32_t, bool> killedGroupResults;
    size_t hostileActorIndex = 8;
    size_t nearbyActorIndex = 3;
    float nearbyActorDistance = 512.0f;
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

    void refreshRulesetMonsters() override
    {
    }

    bool healMapActor(size_t, int) override
    {
        return false;
    }

    OpenYAMM::Game::ActorRulesetFacts *mutableActorRulesetFacts(size_t) override
    {
        return nullptr;
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

    float partyEyeZ() const override
    {
        return m_partyZ + 160.0f;
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

    OpenYAMM::Game::GameplayActorHitFeedback &actorHitFeedback() override
    {
        return m_actorHitFeedback;
    }

    const OpenYAMM::Game::GameplayActorHitFeedback &actorHitFeedback() const override
    {
        return m_actorHitFeedback;
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
        uint32_t sourcePartyMemberIndex,
        bool critical) override
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
        (void)critical;
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
        float z,
        int32_t summonerMemberIndex) override
    {
        (void)monsterId;
        (void)count;
        (void)durationSeconds;
        (void)summonerMemberIndex;
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
        const OpenYAMM::Game::GameplayWorldPoint &source,
        OpenYAMM::Game::ShieldAttackTier shieldTier,
        const OpenYAMM::Game::ShieldHitModifiers &shieldModifiers = {},
        bool critical = false) override
    {
        (void)actorIndex;
        (void)damage;
        (void)source;
        (void)shieldTier;
        (void)shieldModifiers;
        (void)critical;
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

    std::vector<size_t> spellActionVisibleHostileActorIndices() const override
    {
        return {};
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

    // Satchels the loot tests add, one an actor index; a satchel emptied is gone, as a consumed corpse.
    void addSatchel(OpenYAMM::Game::GameplayCorpseViewState satchel)
    {
        satchel.sourceIndex = uint32_t(m_satchels.size());
        m_satchels.push_back(std::move(satchel));
    }

    const std::vector<OpenYAMM::Game::GameplayCorpseViewState> &satchels() const
    {
        return m_satchels;
    }

    std::vector<size_t> lootableCorpseActorIndices() const override
    {
        std::vector<size_t> actorIndices;

        for (size_t index = 0; index < m_satchels.size(); ++index)
        {
            if (!m_satchels[index].items.empty())
            {
                actorIndices.push_back(index);
            }
        }

        return actorIndices;
    }

    bool openActorCorpseView(size_t actorIndex) override
    {
        if (actorIndex >= m_satchels.size() || m_satchels[actorIndex].items.empty())
        {
            return false;
        }

        m_activeCorpseView = m_satchels[actorIndex];
        return true;
    }

    OpenYAMM::Game::GameplayCorpseViewState *activeCorpseView() override
    {
        return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
    }

    const OpenYAMM::Game::GameplayCorpseViewState *activeCorpseView() const override
    {
        return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
    }

    void commitActiveCorpseView() override
    {
    }

    bool takeActiveCorpseItem(size_t itemIndex, OpenYAMM::Game::GameplayChestItemState &item) override
    {
        if (!m_activeCorpseView || itemIndex >= m_activeCorpseView->items.size())
        {
            return false;
        }

        item = m_activeCorpseView->items[itemIndex];
        m_activeCorpseView->items.erase(m_activeCorpseView->items.begin() + std::ptrdiff_t(itemIndex));
        m_satchels[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;

        if (m_activeCorpseView->items.empty())
        {
            m_activeCorpseView.reset();
        }

        return true;
    }

    void closeActiveCorpseView() override
    {
        m_activeCorpseView.reset();
    }

private:
    std::vector<OpenYAMM::Game::GameplayCorpseViewState> m_satchels;
    std::optional<OpenYAMM::Game::GameplayCorpseViewState> m_activeCorpseView;
    OpenYAMM::Game::GameplayActorHitFeedback m_actorHitFeedback;
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

// Character 25, a dragon, on the creature paperdoll (doll type 5), which cannot wear armour.
OpenYAMM::Game::CharacterDollTable makeDragonDollTable()
{
    std::vector<std::string> dragon(24);
    dragon[0] = "25";
    dragon[1] = "5";
    std::vector<std::string> creatureDoll(28, "0");
    creatureDoll[0] = "5";
    std::fill(creatureDoll.begin() + 1, creatureDoll.begin() + 8, "-");
    OpenYAMM::Game::CharacterDollTable table;
    REQUIRE(table.loadCharacterRows({{}, dragon}));
    REQUIRE(table.loadDollTypeRows({{}, creatureDoll}));
    return table;
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
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/common/mm7_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/maps" / (std::string(pBaseName) + ".lua"));
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/maps" / (std::string(pOverlayName) + ".lua"));

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

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadMm7GlobalSupplementProgram(
    const std::filesystem::path &sourceRoot,
    std::string &error)
{
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/common/mm7_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/events/Global.lua");
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm7/events/Global_mm7_mmmerge.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    return OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        *supportLua + "\n\n" + *commonLua + "\n\n" + *baseLua + "\n\n" + *overlayLua,
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
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    const std::optional<std::string> baseLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/events/Global.lua");
    const std::optional<std::string> overlayLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/Global_mm6_mmmerge.lua");

    REQUIRE(supportLua.has_value());
    REQUIRE(commonLua.has_value());
    REQUIRE(baseLua.has_value());
    REQUIRE(overlayLua.has_value());

    return OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
        *supportLua + "\n\n" + *commonLua + "\n\n" + *baseLua + "\n\n" + *overlayLua,
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

TEST_CASE("levitate does not suppress direct scripted trap spell execution")
{
    using namespace OpenYAMM::Game;
    struct TrapScript
    {
        const char *path;
        uint16_t eventId;
        size_t castCount;
    };
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> support = readSourceTextFile(
        sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(support);
    for (const TrapScript &trap : {
             TrapScript{"mm6/events/maps/6t7.lua", 61, 1},
             TrapScript{"mm7/events/maps/7d10.lua", 452, 1},
             TrapScript{"mm8/events/maps/d26.lua", 101, 10}})
    {
        INFO(trap.path);
        const std::optional<std::string> source = readSourceTextFile(sourceRoot / "assets_dev/worlds" / trap.path);
        REQUIRE(source);
        std::string error;
        const std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
            *support + "\n" + *source, trap.path, ScriptedEventScope::Map, error);
        REQUIRE_MESSAGE(program, error);
        CHECK(program->isLevitateSensitivePressurePlate(trap.eventId, 0x8c000102));
        Party party = makeScriptedRegressionParty();
        party.applyPartyBuff(PartyBuffId::Levitate, 600.0f, 0, 112, 1, SkillMastery::Expert, 0);
        EventRuntimeState state;
        RecordingSceneEventContext scene;
        EventRuntime runtime;
        REQUIRE(runtime.executeEventById(program, std::nullopt, trap.eventId, state, &party, &scene));
        CHECK(scene.castSpellCalls.size() == trap.castCount);
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
        selectedMap->globalEventProgram->luaSourceName()->find("events/Global_mm8_promotions.lua")
        != std::string::npos);
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

TEST_CASE("mm7 and mm8 ore crafting consumes one ore from any party member and cannot repeat for free")
{
    using namespace OpenYAMM;
    REQUIRE_MESSAGE(Tests::regressionGameDataLoaded(), Tests::regressionGameDataFailure().c_str());
    const Tests::RegressionGameData &gameData = Tests::regressionGameData();
    REQUIRE(gameData.globalEventProgram.has_value());
    Game::EventRuntime eventRuntime;

    for (uint16_t eventId : {501, 502, 503, 594, 595, 596})
    {
        for (uint32_t grade = 0; grade < 6; ++grade)
        {
            const uint32_t oreId = (eventId < 594 ? 1488u : 686u) + grade;
            CAPTURE(eventId);
            CAPTURE(oreId);
            Game::PartySeed seed;
            seed.members = {makeScriptedRegressionMember(), makeScriptedRegressionMember()};
            Game::Party party;
            party.setItemTable(&gameData.itemTable);
            party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);
            party.seed(seed);
            Game::InventoryItem ore = makeScriptedInventoryItem(oreId);
            ore.quantity = 2;
            REQUIRE(party.member(1)->addInventoryItem(ore));
            REQUIRE_EQ(party.activeMemberIndex(), 0);
            REQUIRE_EQ(party.inventoryItemCount(oreId, 0), 0);
            Game::EventRuntimeState state;

            for (int remaining = 1; remaining >= 0; --remaining)
            {
                REQUIRE(eventRuntime.executeNpcTopicEventById(
                    std::nullopt, gameData.globalEventProgram, eventId, state, &party));
                CHECK_EQ(party.inventoryItemCount(oreId), remaining);
                REQUIRE_EQ(state.grantedItems.size(), 1u);
                CHECK_NE(state.grantedItems.front().objectDescriptionId, oreId);
                party.applyEventRuntimeState(state);
                // Handed over, as the game does (applyGrantedEventItemsToHeldInventory): granted items wait for it.
                state.grantedItems.clear();
            }

            REQUIRE(eventRuntime.executeNpcTopicEventById(
                std::nullopt, gameData.globalEventProgram, eventId, state, &party));
            CHECK(state.grantedItems.empty());
            CHECK_EQ(party.inventoryItemCount(oreId), 0);
            REQUIRE_FALSE(state.messages.empty());
            CHECK(state.messages.back().find("You need ore") != std::string::npos);
        }
    }
}

TEST_CASE("lua inventory removal matches party possession, prefers the current member and honors explicit members")
{
    using namespace OpenYAMM::Game;
    const std::optional<std::string> supportLua = readSourceTextFile(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportLua.has_value());
    std::string error;
    const std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
        *supportLua + R"(
RegisterEvent(1, nil, function()
    evt.ForPlayer(Players.Current)
    RemoveItem(691)
end)
RegisterEvent(2, nil, function()
    evt.ForPlayer(Players.Member1)
    RemoveItem(691)
end)
RegisterEvent(3, nil, function()
    SetValue(InventoryItem(691), 0)
end)
RegisterEvent(4, nil, function()
    evt.ForPlayer(Players.All)
    RemoveItem(691)
end)
)", "@inventory_selection.lua", ScriptedEventScope::Map, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    PartySeed seed;
    seed.members = {makeScriptedRegressionMember(), makeScriptedRegressionMember()};
    Party party;
    party.seed(seed);
    InventoryItem ore = makeScriptedInventoryItem(691);
    ore.quantity = 2;
    REQUIRE(party.member(1)->addInventoryItem(ore));
    EventRuntime eventRuntime;
    EventRuntimeState state;
    const auto memberOreCount = [&party](size_t memberIndex)
    {
        size_t count = 0;

        for (const InventoryItem &item : party.member(memberIndex)->inventory)
        {
            count += item.objectDescriptionId == 691 ? item.quantity : 0;
        }

        return count;
    };

    // "Current" takes from whoever has it when the active member does not (MM8's Conflux Key checks the party,
    // then removes the hearts under Current).
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 1, state, &party));
    CHECK_EQ(party.inventoryItemCount(691), 1);
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 2, state, &party));
    CHECK_EQ(party.inventoryItemCount(691), 0);

    // The active member gives it up first.
    ore.quantity = 1;
    REQUIRE(party.member(0)->addInventoryItem(ore));
    REQUIRE(party.member(1)->addInventoryItem(ore));
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 1, state, &party));
    CHECK_EQ(memberOreCount(0), 0u);
    CHECK_EQ(memberOreCount(1), 1u);

    // An explicit member keeps the selection: Member1 lacks it, so nothing goes.
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 3, state, &party));
    CHECK_EQ(party.inventoryItemCount(691), 0);
    REQUIRE(party.member(0)->addInventoryItem(ore));
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 2, state, &party));
    CHECK_EQ(memberOreCount(0), 1u);

    REQUIRE(party.member(1)->addInventoryItem(ore));
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 4, state, &party));
    CHECK_EQ(party.inventoryItemCount(691), 1);
    CHECK_EQ(party.activeMemberIndex(), 0);
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

TEST_CASE("mm6 path of light and dark topics change the class and merge the magic schools")
{
    using namespace OpenYAMM;
    REQUIRE_MESSAGE(Tests::regressionGameDataLoaded(), Tests::regressionGameDataFailure().c_str());
    const Tests::RegressionGameData &gameData = Tests::regressionGameData();
    std::string error;
    const std::optional<Game::ScriptedEventProgram> globalProgram =
        loadMm6GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalProgram.has_value(), error.c_str());
    REQUIRE(globalProgram->hasEvent(10001));
    REQUIRE(globalProgram->hasEvent(10002));

    const std::optional<Game::NpcDialogTable::ResolvedTopic> lightTopic = gameData.npcDialogTable.getTopicById(10001);
    const std::optional<Game::NpcDialogTable::ResolvedTopic> darkTopic = gameData.npcDialogTable.getTopicById(10002);
    REQUIRE(lightTopic.has_value());
    REQUIRE(darkTopic.has_value());
    CHECK_EQ(lightTopic->topic, "Path of Light");
    CHECK_EQ(darkTopic->topic, "Path of Dark");

    Game::EventRuntime eventRuntime(nullptr, &gameData.npcDialogTable);
    const std::string darkAdvert = gameData.npcDialogTable.getText(2107).value_or("");
    const std::string darkWarning = gameData.npcDialogTable.getText(2105).value_or("");
    const std::string notReady = gameData.npcDialogTable.getText(2109).value_or("");
    REQUIRE_FALSE(darkWarning.empty());

    const auto makePathParty =
        [&gameData](const std::string &className)
        {
            Game::Character member = makeScriptedRegressionMember();
            member.className = className;
            member.skills["LightMagic"] = {"LightMagic", 10, Game::SkillMastery::Master};
            member.skills["DarkMagic"] = {"DarkMagic", 12, Game::SkillMastery::Expert};
            member.learnSpell(78);
            member.learnSpell(90);
            Game::PartySeed seed;
            seed.members = {makeScriptedRegressionMember(), member};
            Game::Party party;
            party.setClassSkillTable(&gameData.classSkillTable);
            party.seed(seed);
            party.setActiveMemberIndex(1);
            return party;
        };

    SUBCASE("the topics are attached to slot 4 of the five masters")
    {
        Game::Party party = makePathParty("MasterWizard");
        Game::EventRuntimeState state;
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 65303, state, &party));
        CHECK_EQ(state.npcTopicOverrides[1040][4], 10002u);
        CHECK_EQ(state.npcTopicOverrides[1030][4], 10002u);
        CHECK_EQ(state.npcTopicOverrides[1057][4], 10001u);
        CHECK_EQ(state.npcTopicOverrides[1031][4], 10001u);
        CHECK_EQ(state.npcTopicOverrides[795][4], 10001u);
    }

    SUBCASE("a master wizard asks on the second click and turns dark")
    {
        Game::Party party = makePathParty("MasterWizard");
        Game::EventRuntimeState state;
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10002, state, &party));
        CHECK_FALSE(state.pendingInputPrompt.has_value());
        REQUIRE_FALSE(state.messages.empty());
        CHECK_EQ(state.messages.back(), darkAdvert);

        state = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10002, state, &party));
        REQUIRE(state.pendingInputPrompt.has_value());
        CHECK_EQ(state.pendingInputPrompt->eventId, 10002u);
        CHECK_EQ(state.pendingInputPrompt->continueStep, 2u);
        REQUIRE_EQ(state.pendingInputPrompt->answers.size(), 1u);
        CHECK_EQ(state.pendingInputPrompt->answers.front(), "yes");
        REQUIRE_EQ(state.pendingInputPrompt->answerContinueSteps.size(), 1u);
        const uint8_t yesStep = state.pendingInputPrompt->answerContinueSteps.front();
        CHECK_EQ(state.pendingInputPrompt->text.value_or(""), darkWarning);

        // The answer is resolved after the active member changed; the asking member still changes path.
        party.setActiveMemberIndex(0);
        state = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10002, state, &party, nullptr, yesStep));
        const Game::Character &member = *party.member(1);
        CHECK_EQ(member.className, "DarkArchMage");
        CHECK_EQ(party.member(0)->className, "Knight");
        CHECK(member.findSkill("LightMagic") == nullptr);
        const Game::CharacterSkill *pDark = member.findSkill("DarkMagic");
        REQUIRE(pDark != nullptr);
        CHECK_EQ(pDark->level, 10u);
        CHECK_EQ(pDark->mastery, Game::SkillMastery::Master);
        CHECK_FALSE(member.knowsSpell(78));
        CHECK(member.knowsSpell(90));
    }

    SUBCASE("declining keeps the class")
    {
        Game::Party party = makePathParty("HighPriest");
        Game::EventRuntimeState state;
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10001, state, &party));
        state = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10001, state, &party));
        REQUIRE(state.pendingInputPrompt.has_value());
        const uint8_t declinedStep = state.pendingInputPrompt->continueStep;
        state = {};
        REQUIRE(
            eventRuntime.executeEventById(std::nullopt, globalProgram, 10001, state, &party, nullptr, declinedStep));
        CHECK_EQ(party.member(1)->className, "HighPriest");
        CHECK(party.member(1)->findSkill("DarkMagic") != nullptr);
        CHECK(party.member(1)->knowsSpell(90));
    }

    SUBCASE("a high priest turns light and keeps the higher mastery")
    {
        Game::Party party = makePathParty("HighPriest");
        Game::EventRuntimeState state;
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10001, state, &party));
        state = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10001, state, &party));
        REQUIRE(state.pendingInputPrompt.has_value());
        REQUIRE_EQ(state.pendingInputPrompt->answerContinueSteps.size(), 1u);
        const uint8_t yesStep = state.pendingInputPrompt->answerContinueSteps.front();
        state = {};
        REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10001, state, &party, nullptr, yesStep));
        const Game::Character &member = *party.member(1);
        CHECK_EQ(member.className, "PriestLight");
        CHECK(member.findSkill("DarkMagic") == nullptr);
        const Game::CharacterSkill *pLight = member.findSkill("LightMagic");
        REQUIRE(pLight != nullptr);
        CHECK_EQ(pLight->level, 10u);
        CHECK_EQ(pLight->mastery, Game::SkillMastery::Master);
        CHECK(member.knowsSpell(78));
        CHECK_FALSE(member.knowsSpell(90));
    }

    SUBCASE("classes outside the tables are not ready")
    {
        for (const char *pClassName : {"Wizard", "PriestLight", "Lich"})
        {
            CAPTURE(pClassName);
            Game::Party party = makePathParty(pClassName);
            Game::EventRuntimeState state;
            REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10001, state, &party));
            REQUIRE(eventRuntime.executeEventById(std::nullopt, globalProgram, 10001, state, &party));
            CHECK_FALSE(state.pendingInputPrompt.has_value());
            REQUIRE_FALSE(state.messages.empty());
            CHECK_EQ(state.messages.back(), notReady);
            CHECK_EQ(party.member(1)->className, pClassName);
        }
    }
}

TEST_CASE("lua player skill and spell functions read and change one member")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportLua.has_value());
    const std::string scriptLua = R"lua(
RegisterEvent(1, "Skills", function()
    local level, mastery = GetPlayerSkill(1, "Light Magic")
    SetPlayerSkill(1, "BodyMagic", level + 1, mastery - 1)
    SetPlayerSkill(1, "DarkMagic", 0, 0)
    ForgetPlayerSpell(1, 78)
    local missingLevel, missingMastery = GetPlayerSkill(1, "FireMagic")
    SetPlayerSkill(1, "FireMagic", missingLevel + 3, missingMastery + 1)
end)
)lua";
    std::string error;
    const std::optional<Game::ScriptedEventProgram> program = Game::ScriptedEventProgram::loadFromLuaText(
        *supportLua + "\n\n" + scriptLua,
        "@events/player_skill_test.lua",
        Game::ScriptedEventScope::Map,
        error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());

    Game::Character member = makeScriptedRegressionMember();
    member.skills["LightMagic"] = {"LightMagic", 7, Game::SkillMastery::Expert};
    member.skills["DarkMagic"] = {"DarkMagic", 4, Game::SkillMastery::Normal};
    member.learnSpell(78);
    member.learnSpell(79);
    Game::PartySeed seed;
    seed.members = {makeScriptedRegressionMember(), member};
    Game::Party party;
    party.seed(seed);

    Game::EventRuntime eventRuntime;
    Game::EventRuntimeState state;
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 1, state, &party));
    const Game::Character &changed = *party.member(1);
    const Game::CharacterSkill *pBody = changed.findSkill("BodyMagic");
    REQUIRE(pBody != nullptr);
    CHECK_EQ(pBody->level, 8u);
    CHECK_EQ(pBody->mastery, Game::SkillMastery::Normal);
    CHECK(changed.findSkill("DarkMagic") == nullptr);
    const Game::CharacterSkill *pFire = changed.findSkill("FireMagic");
    REQUIRE(pFire != nullptr);
    CHECK_EQ(pFire->level, 3u);
    CHECK_EQ(pFire->mastery, Game::SkillMastery::Normal);
    CHECK_FALSE(changed.knowsSpell(78));
    CHECK(changed.knowsSpell(79));
    CHECK(party.member(0)->skills.empty());
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

TEST_CASE("mm6 monthly shrines reward in their month and name the Seer when the pilgrimage is done")
{
    using namespace OpenYAMM::Game;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path mapsDirectory = sourceRoot / "assets_dev/worlds/mm6/events/maps";
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    REQUIRE(supportLua.has_value());
    REQUIRE(commonLua.has_value());

    struct ShrineCase
    {
        const char *pMapName;
        uint16_t eventId;
        int month;
        std::vector<EvtVariable> rewards;
    };
    const std::array<ShrineCase, 12> shrines = {{
        {"outd2", 261, 0, {EvtVariable::BaseMight}},
        {"oute2", 261, 1, {EvtVariable::BaseIntellect}},
        {"outd1", 261, 2, {EvtVariable::BasePersonality}},
        {"outc1", 261, 3, {EvtVariable::BaseEndurance}},
        {"outc2", 261, 4, {EvtVariable::BaseAccuracy}},
        {"outc3", 261, 5, {EvtVariable::BaseSpeed}},
        {"oute3", 261, 6, {EvtVariable::BaseLuck}},
        {"outb1", 262, 7, {EvtVariable::FireResistance}},
        {"outd3", 261, 8, {EvtVariable::AirResistance}},
        {"outb1", 261, 9, {EvtVariable::WaterResistance}},
        {"oute1", 261, 10, {EvtVariable::EarthResistance}},
        {"outb2", 261, 11, {EvtVariable::MindResistance, EvtVariable::BodyResistance, EvtVariable::SpiritResistance}},
    }};

    for (const ShrineCase &shrine : shrines)
    {
        CAPTURE(std::string(shrine.pMapName));
        CAPTURE(shrine.month);
        const std::string mapName = shrine.pMapName;
        const std::optional<std::string> mapLua = readSourceTextFile(mapsDirectory / (mapName + ".lua"));
        const std::optional<std::string> shrineLua = readSourceTextFile(mapsDirectory / (mapName + "_shrine.lua"));
        REQUIRE(mapLua.has_value());
        REQUIRE(shrineLua.has_value());
        std::string error;
        const std::optional<ScriptedEventProgram> program = ScriptedEventProgram::loadFromLuaText(
            *supportLua + "\n\n" + *commonLua + "\n\n" + *mapLua + "\n\n" + *shrineLua,
            "@monthly-shrine.lua",
            ScriptedEventScope::Map,
            error);
        REQUIRE_MESSAGE(program.has_value(), error.c_str());

        PartySeed seed = {};
        seed.members = {makeScriptedRegressionMember(), makeScriptedRegressionMember()};
        Party party = {};
        party.seed(seed);
        EventRuntime runtime = {};
        EventRuntimeState state = {};
        RecordingSceneEventContext context = {};
        std::vector<EventRuntime::VariableRef> rewards;
        std::vector<int32_t> initialValues;

        for (EvtVariable reward : shrine.rewards)
        {
            rewards.push_back(EventRuntime::decodeVariable(static_cast<uint32_t>(reward)));
            initialValues.push_back(EventRuntime::getVariableValue(state, rewards.back(), &party, 0));
        }

        const auto checkRewards = [&](int32_t expectedGain)
        {
            for (size_t rewardIndex = 0; rewardIndex < rewards.size(); ++rewardIndex)
            {
                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    CHECK_EQ(
                        EventRuntime::getVariableValue(state, rewards[rewardIndex], &party, memberIndex),
                        initialValues[rewardIndex] + expectedGain);
                }
            }
        };
        const uint32_t firstVisitBit = 1231u + shrine.month;

        context.setCurrentGameMinutes(((shrine.month + 11) % 12) * 28 * 1440.0f);
        REQUIRE(runtime.executeEventById(program, std::nullopt, shrine.eventId, state, &party, &context));
        CHECK_FALSE(party.hasQuestBit(1230));
        CHECK_FALSE(party.hasQuestBit(firstVisitBit));
        REQUIRE_FALSE(state.statusMessages.empty());
        CHECK_EQ(state.statusMessages.back(), "You pray at the shrine.");
        checkRewards(0);

        context.setCurrentGameMinutes(shrine.month * 28 * 1440.0f);
        REQUIRE(runtime.executeEventById(program, std::nullopt, shrine.eventId, state, &party, &context));
        CHECK(party.hasQuestBit(1230));
        CHECK(party.hasQuestBit(firstVisitBit));
        CHECK(state.statusMessages.back().starts_with("+10 "));
        checkRewards(10);

        // In its month, but the shared pilgrimage bit is set: say so instead of the wrong-month text.
        REQUIRE(runtime.executeEventById(program, std::nullopt, shrine.eventId, state, &party, &context));
        CHECK_EQ(state.statusMessages.back(), "The shrine is silent. Ask the Seer about your next pilgrimage.");
        checkRewards(10);

        // The Seer clears the shared completion bit for another eligible pilgrimage.
        party.setQuestBit(1230, false);
        context.setCurrentGameMinutes((336 + shrine.month * 28 + 27) * 1440.0f);
        REQUIRE(runtime.executeEventById(program, std::nullopt, shrine.eventId, state, &party, &context));
        CHECK(party.hasQuestBit(1230));
        CHECK(state.statusMessages.back().starts_with("+3 "));
        checkRewards(13);
    }
}

TEST_CASE("mm6 obelisk dialogs reopen after collection and other dialogs")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    const std::optional<std::string> commonLua =
        readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6/events/common/mm6_common.lua");
    REQUIRE(supportLua.has_value());
    REQUIRE(commonLua.has_value());

    struct ObeliskCase
    {
        const char *pMapName;
        uint16_t eventId;
        uint32_t questBit;
        uint32_t autonoteId;
    };
    const std::array<ObeliskCase, 3> obelisks = {{
        {"oute3", 240, 1398, 456},
        {"oute2", 212, 1397, 455},
        {"outa1", 210, 1384, 442}
    }};

    for (const ObeliskCase &obelisk : obelisks)
    {
        CAPTURE(std::string(obelisk.pMapName));
        const std::string scriptPath = std::string("events/maps/") + obelisk.pMapName + ".lua";
        const std::optional<std::string> mapLua = readSourceTextFile(sourceRoot / "assets_dev/worlds/mm6" / scriptPath);
        REQUIRE(mapLua.has_value());
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
                *supportLua + "\n\n" + *commonLua + "\n\n" + *mapLua,
                "@" + scriptPath,
                OpenYAMM::Game::ScriptedEventScope::Map,
                error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        runtimeState.messages = {"Previous dialog"};
        CHECK_FALSE(party.hasQuestBit(obelisk.questBit));
        CHECK_FALSE(party.hasAutonote(obelisk.autonoteId));

        for (int visit = 0; visit < 2; ++visit)
        {
            CAPTURE(visit);
            const size_t previousMessageCount = runtimeState.messages.size();
            REQUIRE(eventRuntime.executeEventById(
                localEventProgram, std::nullopt, obelisk.eventId, runtimeState, &party, nullptr));
            REQUIRE(runtimeState.pendingInputPrompt.has_value());
            CHECK_EQ(
                runtimeState.pendingInputPrompt->kind,
                OpenYAMM::Game::EventRuntimeState::PendingInputPrompt::Kind::PressAnyKey);
            CHECK_EQ(runtimeState.pendingInputPrompt->eventId, obelisk.eventId);
            CHECK_EQ(runtimeState.pendingInputPrompt->continueStep, 2u);
            REQUIRE_EQ(runtimeState.messages.size(), 1u);
            const OpenYAMM::Game::EventDialogContent dialog = OpenYAMM::Game::buildEventDialogContent(
                runtimeState, previousMessageCount, true,
                nullptr, nullptr, nullptr, nullptr, nullptr, nullptr, nullptr, &party, nullptr, 0.0f);
            CHECK(dialog.isActive);
            REQUIRE_FALSE(dialog.lines.empty());
            CHECK(dialog.lines.front().find("surface of the obelisk") != std::string::npos);

            runtimeState.pendingInputPrompt.reset();
            REQUIRE(eventRuntime.executeEventById(
                localEventProgram, std::nullopt, obelisk.eventId, runtimeState, &party, nullptr, 2));
            CHECK(party.hasQuestBit(obelisk.questBit));
            CHECK(party.hasAutonote(obelisk.autonoteId));
            if (visit == 0)
            {
                REQUIRE_EQ(runtimeState.portraitFxRequests.size(), 1u);
                CHECK_EQ(runtimeState.portraitFxRequests.front().kind, OpenYAMM::Game::PortraitFxEventKind::AutoNote);
            }
            runtimeState.pendingDialogueContext.reset();
        }
    }
}

TEST_CASE("Lua quest completion feedback announces the whole party without changing quest state")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportLua.has_value());
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> program =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            *supportLua + R"lua(
RegisterEvent(1, "Explicit completion feedback", function()
    evt.ForPlayer(evt.Players.Player1)
    evt.QuestCompleteFeedback()
    evt.QuestCompleteFeedback()
    evt.Add(eventSupport.varTag.Experience, 7)
end)
)lua",
            "@tests/quest_feedback.lua", OpenYAMM::Game::ScriptedEventScope::Map, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());

    OpenYAMM::Game::PartySeed seed = {};
    seed.members.resize(5, makeScriptedRegressionMember());
    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    party.setQuestBit(158, true);
    const OpenYAMM::Game::Party::Snapshot before = party.snapshot();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntime eventRuntime = {};
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 1, runtimeState, &party));
    CHECK(party.snapshot().questBits == before.questBits);
    REQUIRE_EQ(runtimeState.portraitFxRequests.size(), 1u);
    CHECK_EQ(runtimeState.portraitFxRequests.front().kind, OpenYAMM::Game::PortraitFxEventKind::QuestComplete);
    CHECK_EQ(runtimeState.portraitFxRequests.front().memberIndices, std::vector<size_t>({0, 1, 2, 3, 4}));
    REQUIRE_EQ(runtimeState.pendingSounds.size(), 1u);
    CHECK_EQ(runtimeState.pendingSounds.front().soundId, static_cast<uint32_t>(OpenYAMM::Game::SoundId::Quest));
    CHECK_EQ(runtimeState.pendingSounds.front().soundScope, OpenYAMM::Game::SoundScope::Engine);
    CHECK_FALSE(runtimeState.pendingSounds.front().positional);
    // The presentation call must not change the selection used by subsequent event commands.
    for (size_t index = 0; index < party.members().size(); ++index)
    {
        CHECK_EQ(party.members()[index].experience, seed.members[index].experience + (index == 1 ? 7 : 0));
    }
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
        [11] = {2},
    },
    contextActions = {
        [10] = { kind = "open_chest", source = "opcode", chestIds = {1} },
        [11] = { kind = "open_chest", source = "opcode", chestIds = {2} },
        [12] = { kind = "open_door", source = "title" },
        [13] = { kind = "open_door", source = "title" },
    },
    timers = {
        { eventId = 10, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
        {
            eventId = 65000,
            sourceEventId = 10,
            triggerStep = 4,
            origin = "legacy",
            triggerKind = "long",
            scheduleKind = "daily",
            startSecond = 1,
        },
    },
})

RegisterEvent(10, "Generated", function()
end, "Generated hint")

RegisterEvent(11, "Kept", function()
end, "Kept hint")

RegisterEvent(65000, "", function()
end)

RemoveMapEvent(10)
ReplaceMapEvent(11, "Overlay", function()
end, "Overlay hint")
ReplaceMapEvent(12, "Repurposed", function() end)
SetMapContextAction(12, { kind = "teleport", targetMap = "oute3.odm" })
ReplaceMapEvent(13, "No action", function() end)
SetMapContextAction(13, nil)

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
        if (timer.sourceEventId == 10)
        {
            hasRemovedTimer = true;
        }
    }

    CHECK_FALSE(hasRemovedTimer);
    CHECK_FALSE(localEventProgram->hasEvent(65000));
    CHECK(localEventProgram->hasEvent(11));
    const std::optional<std::string> replacementSummary = localEventProgram->summarizeEvent(11);
    const std::optional<std::string> replacementHint = localEventProgram->getHint(11);
    REQUIRE(replacementSummary.has_value());
    REQUIRE(replacementHint.has_value());
    CHECK_EQ(*replacementSummary, "Overlay");
    CHECK_EQ(*replacementHint, "Overlay hint");
    REQUIRE(localEventProgram->getContextActionMetadata(11).has_value());
    CHECK_EQ(localEventProgram->getContextActionMetadata(11)->kind, "open_chest");
    CHECK_EQ(localEventProgram->getOpenedChestIds(11), std::vector<uint32_t>({2}));
    CHECK(std::find(
        localEventProgram->onLoadEventIds().begin(),
        localEventProgram->onLoadEventIds().end(),
        11) == localEventProgram->onLoadEventIds().end());
    REQUIRE(localEventProgram->getContextActionMetadata(12).has_value());
    CHECK_EQ(localEventProgram->getContextActionMetadata(12)->kind, "teleport");
    CHECK_EQ(localEventProgram->getContextActionMetadata(12)->targetMap, std::optional<std::string>("oute3.odm"));
    CHECK_FALSE(localEventProgram->getContextActionMetadata(13).has_value());
}

TEST_CASE("scripted event program normalizes legacy and native timer metadata")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportLua.has_value());

    const std::string luaSource =
        *supportLua
        + R"lua(

SetMapMetadata({
    timers = {
        {
            eventId = 20,
            sourceEventId = 19,
            triggerStep = 7,
            origin = "legacy",
            triggerKind = "long",
            scheduleKind = "daily",
            startHour = 24,
            startMinute = 2,
            startSecond = 3,
        },
        {
            eventId = 40,
            sourceEventId = 40,
            origin = "native",
            scheduleKind = "relative",
            repeating = true,
            intervalGameMinutes = 1,
            initialDelayGameMinutes = 1,
        },
        {
            eventId = 40,
            sourceEventId = 40,
            origin = "native",
            scheduleKind = "relative",
            repeating = true,
            intervalGameMinutes = 2,
            initialDelayGameMinutes = 2,
        },
    },
})

RegisterEvent(20, "Legacy timer", function()
end)

RegisterEvent(40, "Duplicate native timers", function()
end)

RegisterMapTimerEvent(30, 300, function()
end, "Native timer", nil, 120)

)lua";

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> program =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            luaSource,
            "@events/maps/timer_metadata.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    REQUIRE_EQ(program->timerTriggers().size(), 4u);

    const OpenYAMM::Game::ScriptedEventProgram::TimerTrigger &legacy = program->timerTriggers()[0];
    CHECK_EQ(legacy.scope, OpenYAMM::Game::ScriptedEventScope::Map);
    CHECK_EQ(legacy.origin, OpenYAMM::Game::ScriptedEventTimerOrigin::Legacy);
    CHECK_EQ(legacy.triggerKind, OpenYAMM::Game::ScriptedEventTimerTriggerKind::LongTimer);
    CHECK_EQ(legacy.scheduleKind, OpenYAMM::Game::ScriptedEventTimerScheduleKind::Daily);
    CHECK_EQ(legacy.eventId, 20);
    CHECK_EQ(legacy.sourceEventId, 19);
    CHECK_EQ(legacy.triggerStep, 7);
    CHECK_EQ(legacy.startHour, 24);
    CHECK_EQ(legacy.startMinute, 2);
    CHECK_EQ(legacy.startSecond, 3);
    CHECK(legacy.repeating);

    const OpenYAMM::Game::ScriptedEventProgram::TimerTrigger &firstDuplicate = program->timerTriggers()[1];
    const OpenYAMM::Game::ScriptedEventProgram::TimerTrigger &secondDuplicate = program->timerTriggers()[2];
    CHECK_EQ(firstDuplicate.registrationIndex, 1u);
    CHECK_EQ(secondDuplicate.registrationIndex, 2u);
    CHECK_FALSE(OpenYAMM::Game::sameScriptedEventTimerIdentity(firstDuplicate, secondDuplicate));

    const OpenYAMM::Game::ScriptedEventProgram::TimerTrigger &native = program->timerTriggers()[3];
    CHECK_EQ(native.origin, OpenYAMM::Game::ScriptedEventTimerOrigin::Native);
    CHECK_EQ(native.scheduleKind, OpenYAMM::Game::ScriptedEventTimerScheduleKind::Relative);
    CHECK_EQ(native.eventId, 30);
    CHECK_EQ(native.sourceEventId, 30);
    CHECK_EQ(native.registrationIndex, 1u);
    CHECK(native.repeating);
    CHECK_EQ(native.intervalGameMinutes, doctest::Approx(5.0));
    CHECK_EQ(native.initialDelayGameMinutes, doctest::Approx(2.0));
}

TEST_CASE("scoped timer dispatch does not fall through an event id collision")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportLua.has_value());

    const std::string localLua = *supportLua + R"lua(
RegisterEvent(50, "Local", function()
    SetValue(MapVar(1), 1)
end)
)lua";
    const std::string globalLua = *supportLua + R"lua(
RegisterGlobalEvent(50, "Global", function()
    SetValue(MapVar(1), 2)
end)
)lua";

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            localLua,
            "@events/maps/timer_scope_local.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localProgram.has_value(), error.c_str());
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            globalLua,
            "@events/Global.lua",
            OpenYAMM::Game::ScriptedEventScope::Global,
            error);
    REQUIRE_MESSAGE(globalProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    REQUIRE(eventRuntime.executeEventById(
        localProgram,
        globalProgram,
        50,
        runtimeState,
        &party,
        nullptr,
        std::nullopt,
        true,
        OpenYAMM::Game::ScriptedEventScope::Global));
    CHECK_EQ(runtimeState.mapVars[1], 2u);
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

TEST_CASE("event runtime routes generated pickup consumption through the scene source id")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::optional<std::string> supportLua =
        readSourceTextFile(sourceRoot / "assets_dev/engine/scripts/common/event_support.lua");
    REQUIRE(supportLua.has_value());

    const std::string localLuaSource =
        *supportLua
        + R"lua(

RegisterEvent(30017, "Pickup", function()
    evt.ConsumeWorldItem("mm9:test:object:17")
    evt.SetPersistentItemMechanismState("mm9:test:object:18", false, false)
    evt.SetPersistentItemMechanismVariant("mm9:test:object:18", 1)
    evt.ApplyPartyPrimaryStatBuff(0, 2, 3000)
    if evt.IsMapActorHostile(8) then
        evt.SetMapVar("MM9ActorHostile", 1)
    end
    if evt.IsMapActorWithinPartyDistance(3, 512) then
        evt.SetMapVar("MM9ActorNearby", 1)
    end
end)

)lua";
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            localLuaSource,
            "@events/maps/test_mm9_pickup.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    RecordingSceneEventContext sceneContext = {};

    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        30017,
        runtimeState,
        &party,
        &sceneContext));
    CHECK_EQ(sceneContext.consumedWorldItemSourceIds, std::vector<std::string>({"mm9:test:object:17"}));
    REQUIRE_EQ(sceneContext.persistentItemMechanismStateCalls.size(), 1u);
    CHECK_EQ(sceneContext.persistentItemMechanismStateCalls[0].sourceId, "mm9:test:object:18");
    CHECK_FALSE(sceneContext.persistentItemMechanismStateCalls[0].visible);
    CHECK_FALSE(sceneContext.persistentItemMechanismStateCalls[0].solid);
    REQUIRE_EQ(sceneContext.persistentItemMechanismVariantCalls.size(), 1u);
    CHECK_EQ(sceneContext.persistentItemMechanismVariantCalls[0].variantIndex, 1u);
    CHECK_EQ(party.member(0)->magicalBonuses.might, 2);
    CHECK_EQ(runtimeState.namedMapVars["MM9ActorHostile"], 1);
    CHECK_EQ(runtimeState.namedMapVars["MM9ActorNearby"], 1);
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

    const std::array<Case, 25> Cases = {{
        {"7out01", "7out01_mmmerge", {65001}, {}},
        {"7out02", "7out02_mmmerge", {37, 301, 1777, 65002, 65003}, {65002}},
        {"7out03", "7out03_mmmerge", {65004, 65005, 65006}, {65005, 65006}},
        {"7out04", "7out04_mmmerge", {401, 503}, {401}},
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
        {"7d34", "7d34_mmmerge", {376, 377, 378, 379, 380, 381, 382, 65034}, {65034}},
        {"7d36", "7d36_mmmerge", {501}, {}},
        {"7d37", "7d37_mmmerge", {376, 65037}, {65037}},
        {"out11", "out11_mmmerge", {501}, {}},
        {"out12", "out12_mmmerge", {65012}, {65012}},
        {"out09", "out09_mmmerge", {65009}, {65009}},
        {"out14", "out14_mmmerge", {65014}, {}},
        {"7nwc", "7nwc_mmmerge", {501}, {}},
        {"mdt15", "mdt15_mmmerge", {65015}, {}},
        {"mdt10", "mdt10_mmmerge", {65010}, {65010}},
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
            INFO(eventId);
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
        {"d19", "d19_mmmerge", {15, 131, 901}, {901}},
        {"d24", "d24_mmmerge", {901}, {901}},
        {"d34", "d34_mmmerge", {451}, {}},
        {"d38", "d38_mmmerge", {901}, {901}},
        {"d39", "d39_mmmerge", {901}, {901}},
        {"d42", "d42_mmmerge", {501}, {}},
        {"out01", "out01_mmmerge", {901}, {901}},
        {"out02", "out02_mmmerge", {104, 504, 1777}, {}},
        {"out05", "out05_mmmerge", {131, 65031}, {}},
        {"out07", "out07_mmmerge", {132, 133, 134, 135, 136, 455}, {}},
        {"out13", "out13_mmmerge", {451, 452, 901}, {901}},
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
            INFO(eventId);
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

TEST_CASE("mm6 mire of the damned upper house doors open Terry Ros's house")
{
    // Both upper-floor doors use event 68. OUTC3.EVT repeats step 0 with a second EnterHouse that the original
    // interpreter never reaches, so the event must stay on Terry Ros's house for the Lich Book quest.
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outc3", "outc3_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 68, runtimeState, &party));
    REQUIRE(runtimeState.pendingDialogueContext.has_value());
    CHECK_EQ(runtimeState.pendingDialogueContext->kind, OpenYAMM::Game::DialogueContextKind::HouseService);
    CHECK_EQ(runtimeState.pendingDialogueContext->sourceId, 1436u);
}

TEST_CASE("outdoor facet overlays reconstruct old saves from durable progress")
{
    const uint32_t invisibleMask =
        OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible);
    const uint32_t untouchableMask =
        OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Untouchable);

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outc3", "outc3_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        CHECK(localEventProgram->hasEvent(65031));

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::MapDeltaData openDelta = {};
        openDelta.eventVariables.mapVars[11] = 1;
        OpenYAMM::Game::EventRuntimeState openState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, openDelta, openState, &party));
        CHECK_EQ(openState.facetClearMasks[4] & invisibleMask, invisibleMask);

        OpenYAMM::Game::EventRuntimeState closedState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, closedState, &party));
        CHECK_EQ(closedState.facetSetMasks[4] & invisibleMask, invisibleMask);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outd3", "outd3_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        CHECK(localEventProgram->hasEvent(65032));

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::MapDeltaData enabledDelta = {};
        enabledDelta.eventVariables.mapVars[11] = 1;
        enabledDelta.eventVariables.mapVars[16] = 1;
        OpenYAMM::Game::EventRuntimeState enabledState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            enabledDelta,
            enabledState,
            &party));
        CHECK_EQ(enabledState.facetSetMasks[1] & invisibleMask, invisibleMask);
        CHECK_EQ(enabledState.facetSetMasks[1] & untouchableMask, untouchableMask);

        OpenYAMM::Game::EventRuntimeState disabledState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, disabledState, &party));
        CHECK_EQ(disabledState.facetClearMasks[1] & invisibleMask, invisibleMask);
        CHECK_EQ(disabledState.facetClearMasks[1] & untouchableMask, untouchableMask);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out03", "7out03_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party completedParty = makeScriptedRegressionParty();
        completedParty.setQuestBit(569, true);
        OpenYAMM::Game::EventRuntimeState completedState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            completedState,
            &completedParty));
        CHECK_EQ(completedState.facetSetMasks[16] & invisibleMask, invisibleMask);
        CHECK_EQ(completedState.facetSetMasks[16] & untouchableMask, untouchableMask);
        CHECK_EQ(completedState.facetClearMasks[17] & invisibleMask, invisibleMask);

        OpenYAMM::Game::Party pendingParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState pendingState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            pendingState,
            &pendingParty));
        CHECK_EQ(pendingState.facetSetMasks[16] & (invisibleMask | untouchableMask), 0u);
        CHECK_EQ(pendingState.facetClearMasks[17] & invisibleMask, 0u);
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out13", "out13_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party completedParty = makeScriptedRegressionParty();
        completedParty.setQuestBit(37, true);
        OpenYAMM::Game::EventRuntimeState completedState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            completedState,
            &completedParty));
        CHECK_EQ(completedState.facetClearMasks[31] & invisibleMask, invisibleMask);
        CHECK_EQ(completedState.facetClearMasks[31] & untouchableMask, untouchableMask);
        CHECK_EQ(completedState.facetSetMasks[30] & invisibleMask, invisibleMask);
        CHECK_EQ(completedState.facetSetMasks[30] & untouchableMask, untouchableMask);

        OpenYAMM::Game::Party pendingParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState pendingState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            pendingState,
            &pendingParty));
        CHECK_EQ(pendingState.facetClearMasks[31] & (invisibleMask | untouchableMask), 0u);
        CHECK_EQ(pendingState.facetSetMasks[30] & (invisibleMask | untouchableMask), 0u);
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
    CHECK_FALSE(localEventProgram->getHint(131).has_value());
    CHECK_FALSE(localEventProgram->summarizeEvent(131).has_value());

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

    OpenYAMM::Game::Party restoredTransformerParty = makeScriptedRegressionParty();
    restoredTransformerParty.setQuestBit(27, true);
    OpenYAMM::Game::EventRuntimeState restoredTransformerState = {};
    REQUIRE(eventRuntime.buildOnLoadState(
        localEventProgram,
        std::nullopt,
        std::nullopt,
        restoredTransformerState,
        &restoredTransformerParty));
    CHECK_EQ(
        restoredTransformerState.facetSetMasks[30]
            & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
    CHECK_EQ(
        restoredTransformerState.facetSetMasks[30]
            & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable));
}

TEST_CASE("mm8 mmmerge out07 statues and duplicate gems apply")
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

    // MMerge's Shadowspire Dimension Door (event 500) is gone: dimensional travel is the towns' pedestals.
    CHECK_FALSE(localEventProgram->hasEvent(500));
}

TEST_CASE("mm8 mmmerge out13 cannon sequence advances through every reusable stage")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out13", "out13_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    bool foundCannonTimer = false;
    for (const OpenYAMM::Game::ScriptedEventProgram::TimerTrigger &timer : localEventProgram->timerTriggers())
    {
        if (timer.eventId == 452)
        {
            foundCannonTimer = true;
            CHECK(timer.repeating);
            CHECK_EQ(timer.intervalGameMinutes, doctest::Approx(1.0f));
            CHECK_EQ(timer.initialDelayGameMinutes, doctest::Approx(1.0f));
        }
    }
    CHECK(foundCannonTimer);

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

TEST_CASE("mm8 mmmerge arena exit applies and the dimension door tiles are gone")
{
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "d42", "d42_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        REQUIRE(localEventProgram->getContextActionMetadata(501).has_value());
        CHECK_EQ(localEventProgram->getContextActionMetadata(501)->kind, "leave_dungeon");
        CHECK_EQ(localEventProgram->getContextActionMetadata(501)->targetName,
            std::optional<std::string>("Leave the Arena"));
        CHECK_FALSE(localEventProgram->getContextActionMetadata(501)->targetMap.has_value());

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

    // MMerge's Dimension Door tiles on Dagger Wound (out01) and in Shadowspire (out07) are gone; out01 still unlocks
    // Blood Drop's Town Portal.
    for (const char *pMapName : {"out01", "out07"})
    {
        INFO(pMapName);
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, pMapName, (std::string(pMapName) + "_mmmerge").c_str(), error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
        CHECK_FALSE(localEventProgram->hasEvent(902));

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, runtimeState, &party));
        CHECK_EQ(party.hasQuestBit(185), std::string(pMapName) == "out01");
        CHECK_FALSE(runtimeState.pendingDimensionDoorOverlay);
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
        CHECK_FALSE(localEventProgram->getHint(1).has_value());
        CHECK_FALSE(localEventProgram->summarizeEvent(1).has_value());

        OpenYAMM::Game::Party firstVisitParty = makeScriptedRegressionParty();
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::EventRuntimeState firstVisitState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            firstVisitState,
            &firstVisitParty));
        CHECK_EQ(firstVisitState.actorGroupSetMasks[8] & actorHostileBit, actorHostileBit);
        CHECK_EQ(firstVisitState.actorGroupSetMasks[10] & actorHostileBit, actorHostileBit);
        CHECK_EQ(firstVisitState.actorGroupClearMasks[8] & actorInvisibleBit, actorInvisibleBit);
        CHECK_EQ(firstVisitState.actorGroupSetMasks[11] & actorInvisibleBit, actorInvisibleBit);

        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(10, true);
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
    CHECK_FALSE(profile.weatherMap.rainEnabled);
    CHECK_FALSE(profile.weatherMap.snowEnabled);
    CHECK_EQ(profile.weatherMap.rainChancePercent, doctest::Approx(20.0f));
    CHECK_EQ(profile.weatherMap.snowChancePercent, doctest::Approx(15.0f));
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
    CHECK(tularean.weatherMap.rainEnabled);
    CHECK_FALSE(tularean.weatherMap.snowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile harmondale = loadWeatherProfile("7out02.odm");
    CHECK(harmondale.mergedWeatherEnabled);
    CHECK(harmondale.weatherMap.rainEnabled);
    CHECK(harmondale.weatherMap.snowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile erathia = loadWeatherProfile("7out03.odm");
    CHECK(erathia.mergedWeatherEnabled);
    CHECK(erathia.weatherMap.rainEnabled);
    CHECK(erathia.weatherMap.snowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile bracada = loadWeatherProfile("7out06.odm");
    CHECK_EQ(bracada.mergedCustomSkyTextureName, "7plansky3");
    CHECK_FALSE(bracada.mergedWeatherEnabled);
    CHECK_FALSE(bracada.weatherMap.rainEnabled);
    CHECK_FALSE(bracada.weatherMap.snowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile nighon = loadWeatherProfile("out10.odm");
    CHECK(nighon.mergedWeatherEnabled);
    CHECK(nighon.weatherMap.rainEnabled);
    CHECK(nighon.weatherMap.snowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile landOfTheGiants = loadWeatherProfile("out12.odm");
    CHECK(landOfTheGiants.mergedWeatherEnabled);
    CHECK(landOfTheGiants.weatherMap.rainEnabled);
    CHECK(landOfTheGiants.weatherMap.snowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile kriegspire = loadWeatherProfile("outb1.odm");
    CHECK(kriegspire.mergedWeatherEnabled);
    CHECK(kriegspire.weatherMap.rainEnabled);
    CHECK(kriegspire.weatherMap.snowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile frozenHighlands = loadWeatherProfile("outc1.odm");
    CHECK(frozenHighlands.mergedWeatherEnabled);
    CHECK(frozenHighlands.weatherMap.rainEnabled);
    CHECK_FALSE(frozenHighlands.weatherMap.snowEnabled);

    const OpenYAMM::Game::OutdoorWeatherProfile newSorpigal = loadWeatherProfile("oute3.odm");
    REQUIRE_EQ(newSorpigal.mergedSkyTextureNames.size(), 7u);
    CHECK(newSorpigal.mergedCustomSkyTextureName.empty());
    CHECK_EQ(newSorpigal.mergedSkyTextureNames[0], "6plansky1");
    CHECK_EQ(newSorpigal.mergedSkyTextureNames[1], "6plansky1");
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
            static_cast<uint32_t>(OpenYAMM::Game::HouseActionId::OpenTeacherLedgerMenu),
        });

    hookContext.menuId = static_cast<uint32_t>(OpenYAMM::Game::DialogueMenuId::LearnSkills);
    runtimeState.activeHookContext = hookContext;

    REQUIRE(eventRuntime.executeHooks(
        localEventProgram,
        std::nullopt,
        OpenYAMM::Game::EventRuntimeHookKind::HouseTopicFilter,
        runtimeState,
        &party));
    REQUIRE(runtimeState.activeHookContext.has_value());
    CHECK(runtimeState.activeHookContext->houseTopicActionIds.empty());
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

TEST_CASE("dimensional travel fountains keep their own effects and need no quest")
{
    // MMerge's travel fountains, without its Verdant quest gate (Verdant removed, the fountains kept: the user,
    // 2026-11-09).
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> ravenshoreProgram =
        loadMm8MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out02", "out02_mmmerge", error);
    REQUIRE_MESSAGE(ravenshoreProgram.has_value(), error.c_str());
    CHECK_EQ(ravenshoreProgram->getHint(104).value_or(""), "Drink from the fountain");
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    // Ravenshore's fountain keeps MM8's Town Portal and 200 gold twice to a poor party, and opens the travel.
    OpenYAMM::Game::Party poorParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState fountainState = {};
    for (int expectedGold : {200, 200, 0})
    {
        poorParty.addGold(-poorParty.gold());
        fountainState.pendingDimensionDoorOverlay = false;
        REQUIRE(eventRuntime.executeEventById(ravenshoreProgram, std::nullopt, 104, fountainState, &poorParty));
        CHECK(poorParty.hasQuestBit(302));
        CHECK(fountainState.pendingDimensionDoorOverlay);
        CHECK_EQ(poorParty.gold(), expectedGold);
    }
    CHECK_EQ(fountainState.mapVars[29], 2);

    // Its pedestal (1777, worlds/mm8/maps/out02_dimensional_travel.scene.yml) travels too.
    OpenYAMM::Game::Party pedestalParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState pedestalState = {};
    REQUIRE(eventRuntime.executeEventById(ravenshoreProgram, std::nullopt, 1777, pedestalState, &pedestalParty));
    CHECK(pedestalState.pendingDimensionDoorOverlay);

    const OpenYAMM::Game::MapAssetInfo *pCastle = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "7d29.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{.allowSceneYml = true, .allowLegacyCompanion = true});
    REQUIRE(pCastle != nullptr);
    REQUIRE(pCastle->indoorMapData.has_value());
    REQUIRE(pCastle->indoorMapDeltaData.has_value());
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> castleProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d29", "7d29_mmmerge", error);
    REQUIRE_MESSAGE(castleProgram.has_value(), error.c_str());

    for (size_t faceIndex : {1668, 1669, 1689, 1697, 4669, 4670})
    {
        const OpenYAMM::Game::IndoorFace &face = pCastle->indoorMapData->faces.at(faceIndex);
        CHECK_EQ(face.cogNumber, 65031u);
        CHECK_EQ(face.cogTriggered, 65031u);
        CHECK_EQ(face.textureName, "7wtrtyl");
        CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Fluid));
        CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Clickable));
        CHECK_FALSE(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::HasHint));
    }
    CHECK_EQ(pCastle->indoorMapData->faces.at(4229).cogTriggered, 0u);
    CHECK_EQ(pCastle->indoorMapData->faces.at(4234).cogTriggered, 0u);

    // Castle Harmondale's courtyard water travels whether the castle is restored or not, with no quest.
    for (bool restored : {false, true})
    {
        OpenYAMM::Game::Party castleParty = makeScriptedRegressionParty();
        castleParty.setQuestBit(610, restored);
        OpenYAMM::Game::EventRuntimeState castleState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            castleProgram, std::nullopt, pCastle->indoorMapDeltaData, castleState, &castleParty));
        CHECK(castleParty.hasQuestBit(718));
        CHECK(OpenYAMM::Game::hasFaceAttribute(
            castleState.facetSetMasks.at(65031), OpenYAMM::Game::FaceAttribute::Clickable));
        CHECK_FALSE(castleState.textureOverrides.contains(65031));
        REQUIRE(eventRuntime.executeEventById(
            castleProgram, std::nullopt, 65031, castleState, &castleParty));
        CHECK(castleState.pendingDimensionDoorOverlay);
        CHECK(castleParty.hasQuestBit(718));
    }
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
        // The Paramount Guild of Water (event 6) is a guild again: MMerge's Dimension Door spot here is gone.
        OpenYAMM::Game::EventRuntimeState guildState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 6, guildState, &party));
        CHECK_FALSE(guildState.pendingDimensionDoorOverlay);
        CHECK_FALSE(localEventProgram->hasEvent(65010));

        OpenYAMM::Game::EventRuntimeState treasureState = {};
        treasureState.variables[static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::Hour)] = 1;
        for (uint32_t qbitId = 676; qbitId <= 689; ++qbitId)
        {
            party.setQuestBit(qbitId, true);
        }
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 65009, treasureState, &party));
        CHECK_FALSE(treasureState.spriteOverrides.contains(170));
        REQUIRE(treasureState.spriteOverrides.contains(20));
        CHECK(treasureState.spriteOverrides[20].hidden);
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

    // MMerge's Tularean Forest Dimension Door (event 504) is gone: dimensional travel is the towns' pedestals.
    CHECK_FALSE(localEventProgram->hasEvent(504));

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

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(591, true);
        party.setQuestBit(649, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.mapVars[11] = 1;
        RecordingSceneEventContext sceneContext = {};

        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            401,
            runtimeState,
            &party,
            &sceneContext));
        CHECK(sceneContext.summonMonstersCalls.empty());
        REQUIRE(runtimeState.facetClearMasks.contains(1));
        CHECK((runtimeState.facetClearMasks.at(1)
            & OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Invisible)) != 0);
        CHECK((runtimeState.facetClearMasks.at(1)
            & OpenYAMM::Game::faceAttributeBit(OpenYAMM::Game::FaceAttribute::Untouchable)) != 0);
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
        REQUIRE(localEventProgram->getContextActionMetadata(501).has_value());
        CHECK_EQ(localEventProgram->getContextActionMetadata(501)->kind, "leave_dungeon");
        CHECK_EQ(localEventProgram->getContextActionMetadata(501)->targetName,
            std::optional<std::string>("Leave The Strange Temple"));
        CHECK_FALSE(localEventProgram->getContextActionMetadata(501)->targetMap.has_value());

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
        CHECK(party.hasQuestBit(526));
        CHECK_EQ(runtimeState.npcItemOverrides[345], 0u);
        CHECK_EQ(runtimeState.npcTopicOverrides[345][0], 767u);
        CHECK_EQ(runtimeState.npcTopicOverrides[345][1], 0u);
        CHECK_EQ(runtimeState.npcGreetingOverrides[345], 122u);
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
        REQUIRE_FALSE(resolvedState.messages.empty());
        CHECK_EQ(resolvedState.npcTopicOverrides[461][0], 0u);
        CHECK_EQ(resolvedState.npcTopicOverrides[461][1], 0u);

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
        REQUIRE_FALSE(activeState.messages.empty());
        CHECK_EQ(activeState.npcTopicOverrides[461][0], 0u);
        CHECK_EQ(activeState.npcTopicOverrides[461][1], 0u);

        OpenYAMM::Game::Party paidParty = makeScriptedRegressionParty();
        paidParty.addGold(1000);
        OpenYAMM::Game::EventRuntimeState paidState = {};
        RecordingSceneEventContext paidSceneContext = {};
        REQUIRE(eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            513,
            paidState,
            &paidParty,
            &paidSceneContext));
        CHECK(paidParty.hasQuestBit(761));
        CHECK_EQ(paidParty.gold(), 0);
        CHECK(paidSceneContext.summonMonstersCalls.empty());
        REQUIRE_FALSE(paidState.messages.empty());
        CHECK_EQ(paidState.npcTopicOverrides[461][0], 0u);
        CHECK_EQ(paidState.npcTopicOverrides[461][1], 0u);

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
        REQUIRE_FALSE(forcedState.messages.empty());
        CHECK_EQ(forcedState.npcTopicOverrides[461][0], 0u);
        CHECK_EQ(forcedState.npcTopicOverrides[461][1], 0u);
    }

    {
        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.setQuestBit(528, true);
        OpenYAMM::Game::EventRuntimeState runtimeState = {};
        runtimeState.activeHistoryContinentId = 2;
        runtimeState.variables[static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::Hour)] = 6;
        RecordingGameplayWorldContext sceneContext = {};
        sceneContext.setCurrentGameMinutes(360.0f);
        REQUIRE(eventRuntime.executeEventById(
            std::nullopt, globalEventProgram, 783, runtimeState, &party, &sceneContext));
        // Its pages 1 and 2 are the forward pages, known from the start; the castle pages come later.
        CHECK_FALSE(party.historyEventTimes(2).contains(3));
        CHECK_FALSE(party.historyEventTimes(2).contains(4));
        CHECK_EQ(sceneContext.currentGameMinutes(), 360.0f + 14 * 24 * 60);
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

TEST_CASE("mm7 global mmmerge supplement applies hatchling fixups and has no Verdant")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> globalEventProgram =
        loadMm7GlobalSupplementProgram(OPENYAMM_SOURCE_DIR, error);
    REQUIRE_MESSAGE(globalEventProgram.has_value(), error.c_str());
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();

    // Verdant (MMerge's Cross Continents quest) is removed (2026-11-09): none of her topics, timers or hooks remain.
    for (uint32_t eventId : {1778u, 1781u, 1782u, 1783u, 1784u, 1788u, 10000u, 65200u, 65201u, 65202u, 65203u, 65204u})
    {
        INFO(eventId);
        CHECK_FALSE(globalEventProgram->hasEvent(eventId));
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
        // Mind and Body come from the Undead race (ClassRules::applyClassBonuses), never Light or Dark.
        CHECK_EQ(pWizard->raceId, 6u);
        CHECK_EQ(pWizard->baseResistances.light, 0);
        CHECK_FALSE(pWizard->permanentImmunities.light);
        CHECK_FALSE(pWizard->permanentImmunities.dark);
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

TEST_CASE("looting every satchel takes all the gold and each item that fits, and leaves the rest")
{
    // Bags with room for one more item.
    RecordingGameplayWorldContext world;
    *world.party() = makeScriptedRegressionParty();

    while (world.party()->tryGrantInventoryItemStartingAt(0, makeScriptedInventoryItem(1406)))
    {
    }

    world.party()->member(0)->inventory.pop_back();
    const auto gold = [](uint32_t amount)
    {
        OpenYAMM::Game::GameplayChestItemState item = {};
        item.isGold = true;
        item.goldAmount = amount;
        return item;
    };
    const auto lootItem = [](uint32_t itemId)
    {
        OpenYAMM::Game::GameplayChestItemState item = {};
        item.itemId = itemId;
        item.quantity = 1;
        return item;
    };
    OpenYAMM::Game::GameplayCorpseViewState first = {};
    first.items = {gold(100), lootItem(1406)};
    OpenYAMM::Game::GameplayCorpseViewState second = {};
    second.items = {lootItem(1407), gold(50)};
    world.addSatchel(first);
    world.addSatchel(second);
    const int goldBefore = world.party()->gold();
    world.party()->clearPendingAudioRequests();

    const OpenYAMM::Game::GameplayUiController::LootSummaryOverlayState summary =
        OpenYAMM::Game::lootAllCorpses(world, *world.party());

    CHECK(summary.active);
    CHECK_EQ(summary.satchelCount, 2u);
    CHECK_EQ(summary.goldAmount, 150);
    CHECK_EQ(world.party()->gold() - goldBefore, 150);
    // One gold sound for the whole sweep, not one per satchel.
    size_t goldSounds = 0;

    for (const OpenYAMM::Game::Party::PendingAudioRequest &request : world.party()->pendingAudioRequests())
    {
        goldSounds += request.soundId == OpenYAMM::Game::SoundId::Gold ? 1 : 0;
    }

    CHECK_EQ(goldSounds, 1u);
    REQUIRE_EQ(summary.takenItems.size(), 1u);
    CHECK_EQ(summary.takenItems[0].objectDescriptionId, 1406u);
    // Where it went, for the summary to inspect (identify, repair) the item itself.
    REQUIRE_EQ(summary.takenItemPlaces.size(), 1u);
    const OpenYAMM::Game::GameplayUiController::LootedItemPlace &place = summary.takenItemPlaces[0];
    const OpenYAMM::Game::Character *pRecipient = world.party()->member(place.memberIndex);
    REQUIRE(pRecipient != nullptr);
    const OpenYAMM::Game::InventoryItem *pPlaced =
        OpenYAMM::Game::InventoryBags::itemInBagAt(*pRecipient, place.bag, place.gridX, place.gridY);
    REQUIRE(pPlaced != nullptr);
    CHECK_EQ(pPlaced->objectDescriptionId, 1406u);
    REQUIRE_EQ(summary.leftItems.size(), 1u);
    CHECK_EQ(summary.leftItems[0].objectDescriptionId, 1407u);
    // The first satchel is empty and gone; the second keeps the item that did not fit.
    CHECK(world.satchels()[0].items.empty());
    REQUIRE_EQ(world.satchels()[1].items.size(), 1u);
    CHECK_EQ(world.satchels()[1].items[0].itemId, 1407u);
    CHECK_EQ(world.lootableCorpseActorIndices(), std::vector<size_t>{1});
}

TEST_CASE("mm7 shoals let a dragon in with a carried wetsuit and still want the others worn")
{
    const OpenYAMM::Game::CharacterDollTable dolls = makeDragonDollTable();
    const auto makeParty =
        [&](bool dragon, bool carried)
        {
            OpenYAMM::Game::Party party = makeScriptedRegressionParty();
            party.setCharacterDollTable(&dolls);
            party.setQuestBit(642, true);
            OpenYAMM::Game::Character &member = *party.member(0);
            member.characterDataId = dragon ? 25 : 0;
            member.health = 40;

            if (carried)
            {
                member.inventory.push_back(makeScriptedInventoryItem(1406));
            }

            return party;
        };

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> lincoln =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d23", "7d23_mmmerge", error);
    REQUIRE_MESSAGE(lincoln.has_value(), error.c_str());
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> avlee =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out14", "out14_mmmerge", error);
    REQUIRE_MESSAGE(avlee.has_value(), error.c_str());
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> shoals =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7out15", "7out15_mmmerge", error);
    REQUIRE_MESSAGE(shoals.has_value(), error.c_str());
    OpenYAMM::Game::EventRuntime eventRuntime = {};

    for (const auto &[dragon, carried, suited] :
         std::vector<std::tuple<bool, bool, bool>>{{true, true, true}, {true, false, false}, {false, true, false}})
    {
        CAPTURE(dragon);
        CAPTURE(carried);

        OpenYAMM::Game::Party lincolnParty = makeParty(dragon, carried);
        OpenYAMM::Game::EventRuntimeState lincolnState = {};
        REQUIRE(eventRuntime.executeEventById(lincoln, std::nullopt, 501, lincolnState, &lincolnParty));
        CHECK_EQ(pendingMapMove(lincolnState) != nullptr, suited);

        OpenYAMM::Game::Party avleeParty = makeParty(dragon, carried);
        OpenYAMM::Game::EventRuntimeState avleeState = {};
        OpenYAMM::Game::EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.kind = OpenYAMM::Game::EventRuntimeHookKind::MapTransition;
        hookContext.boundaryEdge = static_cast<uint32_t>(OpenYAMM::Game::MapBoundaryEdge::West);
        hookContext.destinationMapName = "7out15.odm";
        avleeState.activeHookContext = hookContext;
        REQUIRE(eventRuntime.executeHooks(
            avlee, std::nullopt, OpenYAMM::Game::EventRuntimeHookKind::MapTransition, avleeState, &avleeParty));
        REQUIRE(avleeState.activeHookContext.has_value());
        CHECK_EQ(avleeState.activeHookContext->blocked, !suited);

        OpenYAMM::Game::Party shoalsParty = makeParty(dragon, carried);
        RecordingGameplayWorldContext shoalsWorldContext;
        shoalsWorldContext.setPartyPosition(0.0f, 0.0f, 0.0f);
        OpenYAMM::Game::EventRuntimeState shoalsState = {};
        REQUIRE(eventRuntime.executeEventById(
            shoals, std::nullopt, 65017, shoalsState, &shoalsParty, &shoalsWorldContext));
        CHECK_EQ(shoalsParty.member(0)->health, suited ? 40 : 0);
    }
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

TEST_CASE("mm7 colony zod releases Roland and restores the open pathway")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d27", "7d27_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
    CHECK_FALSE(localEventProgram->summarizeEvent(376).has_value());
    CHECK_FALSE(localEventProgram->getHint(376).has_value());

    OpenYAMM::Game::EventRuntime eventRuntime = {};

    OpenYAMM::Game::Party freshParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState freshState = {};
    freshState.activeHistoryContinentId = 2;
    freshState.variables[static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::Hour)] = 6;
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, freshState, &freshParty));
    CHECK_EQ(freshParty.historyEventTimes(2).at(24), 360);
    // Handed over, as the game does (applyGrantedEventItemsToHeldInventory): granted items wait for it.
    freshState.grantedItems.clear();
    freshState.variables[static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::Hour)] = 7;
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, freshState, &freshParty));
    CHECK_EQ(freshParty.historyEventTimes(2).at(24), 360);
    REQUIRE_EQ(freshState.grantedItems.size(), 1u);
    CHECK_EQ(freshState.grantedItems.front().objectDescriptionId, 1463u);
    CHECK(freshParty.hasQuestBit(752));
    CHECK_EQ(freshState.spriteOverrides[20].textureName, "0");
    CHECK_EQ(
        freshState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
    CHECK_EQ(
        freshState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable));

    OpenYAMM::Game::Party inventoryKeyParty = makeScriptedRegressionParty();
    REQUIRE(inventoryKeyParty.member(0) != nullptr);
    inventoryKeyParty.member(0)->inventory.push_back(makeScriptedInventoryItem(1463));
    OpenYAMM::Game::EventRuntimeState inventoryKeyState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        376,
        inventoryKeyState,
        &inventoryKeyParty));
    CHECK(inventoryKeyState.grantedItems.empty());
    CHECK(inventoryKeyParty.hasQuestBit(752));
    CHECK_EQ(inventoryKeyState.spriteOverrides[20].textureName, "0");
    CHECK_EQ(
        inventoryKeyState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
    CHECK_EQ(
        inventoryKeyState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable));

    OpenYAMM::Game::Party heldKeyParty = makeScriptedRegressionParty();
    heldKeyParty.setHeldItemForQueries(makeScriptedInventoryItem(1463));
    OpenYAMM::Game::EventRuntimeState heldKeyState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 376, heldKeyState, &heldKeyParty));
    CHECK(heldKeyState.grantedItems.empty());
    CHECK(heldKeyParty.hasQuestBit(752));
    CHECK_EQ(heldKeyState.spriteOverrides[20].textureName, "0");
    CHECK_EQ(
        heldKeyState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
    CHECK_EQ(
        heldKeyState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable));

    OpenYAMM::Game::Party unreleasedParty = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState unreleasedState = {};
    REQUIRE(eventRuntime.buildOnLoadState(
        localEventProgram,
        std::nullopt,
        std::nullopt,
        unreleasedState,
        &unreleasedParty));
    CHECK(unreleasedState.spriteOverrides.find(20) == unreleasedState.spriteOverrides.end());
    CHECK(unreleasedState.facetSetMasks.find(1) == unreleasedState.facetSetMasks.end());

    OpenYAMM::Game::Party releasedParty = makeScriptedRegressionParty();
    releasedParty.setQuestBit(752, true);
    OpenYAMM::Game::EventRuntimeState releasedState = {};
    REQUIRE(eventRuntime.buildOnLoadState(
        localEventProgram,
        std::nullopt,
        std::nullopt,
        releasedState,
        &releasedParty));
    CHECK_EQ(releasedState.spriteOverrides[20].textureName, "0");
    CHECK_EQ(
        releasedState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Invisible));
    CHECK_EQ(
        releasedState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable),
        static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable));
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
        CHECK_EQ(
            runtimeState.facetSetMasks[1] & static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable),
            static_cast<uint32_t>(OpenYAMM::Game::FaceAttribute::Untouchable));
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

TEST_CASE("mm7 Evenmorn obelisk treasure shows only at midnight after every obelisk")
{
    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "out09", "out09_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

    // Recomputed on map load and every half hour.
    CHECK(localEventProgram->hasEvent(65009));
    const std::vector<OpenYAMM::Game::ScriptedEventProgram::TimerTrigger> &timers = localEventProgram->timerTriggers();
    const auto clock = std::find_if(timers.begin(), timers.end(),
        [](const OpenYAMM::Game::ScriptedEventProgram::TimerTrigger &timer) { return timer.eventId == 65011; });
    REQUIRE(clock != timers.end());
    CHECK(clock->repeating);
    CHECK_EQ(clock->intervalGameMinutes, doctest::Approx(30.0));

    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    constexpr uint32_t TreasureCog = 20;
    const uint32_t hourVariable = static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::Hour);
    const auto treasureHidden = [&](int hour)
    {
        OpenYAMM::Game::EventRuntimeState state = {};
        state.variables[hourVariable] = hour;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 65009, state, &party));
        const auto sprite = state.spriteOverrides.find(TreasureCog);
        REQUIRE(sprite != state.spriteOverrides.end());
        return sprite->second.hidden;
    };

    for (uint32_t qbitId = 676; qbitId <= 688; ++qbitId)
    {
        party.setQuestBit(qbitId, true);
    }
    CHECK(treasureHidden(0));

    party.setQuestBit(689, true);
    CHECK(treasureHidden(5));
    CHECK(treasureHidden(1));
    CHECK(treasureHidden(23));
    CHECK_FALSE(treasureHidden(0));
}

TEST_CASE("mm7 rescued dwarf and Haunted Mansion portrait states survive map reloads")
{
    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d34", "7d34_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party party = makeScriptedRegressionParty();
        party.grantItem(1431);
        party.setQuestBit(1689, true);

        OpenYAMM::Game::EventRuntimeState interactionState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            376,
            interactionState,
            &party));
        CHECK(interactionState.hiredNpcFollowers.empty());
        CHECK_FALSE(interactionState.pendingDialogueContext.has_value());

        OpenYAMM::Game::EventRuntimeState restoredState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            restoredState,
            &party));
        const std::unordered_map<uint32_t, OpenYAMM::Game::EventRuntimeState::SpriteOverride>::const_iterator
            restoredSprite = restoredState.spriteOverrides.find(1u);
        REQUIRE(restoredSprite != restoredState.spriteOverrides.end());
        CHECK(restoredSprite->second.hidden);
        REQUIRE(restoredSprite->second.textureName.has_value());
        CHECK_EQ(*restoredSprite->second.textureName, "0");
    }

    {
        std::string error;
        const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
            loadMm7MapOverlayProgram(OPENYAMM_SOURCE_DIR, "7d37", "7d37_mmmerge", error);
        REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());

        OpenYAMM::Game::EventRuntime eventRuntime = {};
        OpenYAMM::Game::Party restoredParty = makeScriptedRegressionParty();
        restoredParty.setQuestBit(778, true);
        OpenYAMM::Game::EventRuntimeState restoredState = {};
        REQUIRE(eventRuntime.buildOnLoadState(
            localEventProgram,
            std::nullopt,
            std::nullopt,
            restoredState,
            &restoredParty));
        CHECK_EQ(restoredState.namedMapVars["PortraitTaken"], 1);
        CHECK_EQ(restoredState.textureOverrides[15], "t2bs");

        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            376,
            restoredState,
            &restoredParty));
        CHECK(restoredState.grantedItemIds.empty());

        OpenYAMM::Game::Party paintingParty = makeScriptedRegressionParty();
        paintingParty.grantItem(1423);
        OpenYAMM::Game::EventRuntimeState paintingState = {};
        REQUIRE(eventRuntime.executeEventById(
            localEventProgram,
            std::nullopt,
            376,
            paintingState,
            &paintingParty));
        CHECK(paintingParty.hasQuestBit(778));
        CHECK(paintingState.grantedItemIds.empty());
        CHECK_EQ(paintingState.namedMapVars["PortraitTaken"], 1);
        CHECK_EQ(paintingState.textureOverrides[15], "t2bs");
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
                CHECK_EQ(timer.initialDelayGameMinutes, 5.0f);
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

        // The map's own hostile.txt cell (faction numbers): the faction is peaceful toward the party (0) here.
        if (testCase.peacefulMonsterKind != 0)
        {
            const std::vector<OpenYAMM::Game::ScriptedEventProgram::FactionRelation> &relations =
                localEventProgram->factionRelations();
            CHECK(std::any_of(relations.begin(), relations.end(),
                [&testCase](const OpenYAMM::Game::ScriptedEventProgram::FactionRelation &relation)
                {
                    return relation.faction == testCase.peacefulMonsterKind && relation.otherFaction == 0
                        && relation.relation == 0;
                }));
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
    CHECK_FALSE(globalEventProgram->hasEvent(1778));
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
            {1373, "Wizard", "MasterWizard", {}, 2077, 1641},
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

TEST_CASE("mm6 oute3 overlay: the fountain and the pedestal travel, the volcano erupts")
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
    // The northwest fountain (event 140) and the pedestal (1777, worlds/mm6/maps/oute3_dimensional_travel.scene.yml)
    // both open the dimensional travel, with no quest.
    OpenYAMM::Game::EventRuntimeState fountainState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        140,
        fountainState,
        &party,
        nullptr));
    CHECK(fountainState.pendingDimensionDoorOverlay);

    OpenYAMM::Game::EventRuntimeState pedestalState = {};
    REQUIRE(eventRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        1777,
        pedestalState,
        &party,
        nullptr));
    CHECK(pedestalState.pendingDimensionDoorOverlay);

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

TEST_CASE("mm6 Shrine of the Gods blessing follows characters and migrates older saves")
{
    using namespace OpenYAMM::Game;
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outb3", "outb3_mmmerge", error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    PartySeed seed = {};
    seed.members = {makeScriptedRegressionMember(), makeScriptedRegressionMember(), makeScriptedRegressionMember()};
    Party party = {};
    party.seed(seed);
    EventRuntime runtime = {};
    EventRuntimeState state = {};
    REQUIRE(party.setActiveMemberIndex(1));
    REQUIRE(runtime.executeEventById(program, std::nullopt, 103, state, &party));
    CHECK_EQ(party.member(1)->might, 34u);
    CHECK(party.member(1)->playerBits.contains(70));
    CHECK_FALSE(party.member(0)->playerBits.contains(70));

    REQUIRE(party.dismissMemberToAdventurersInn(1));
    REQUIRE(party.hireAdventurersInnMember(0));
    // An unblessed character now occupies the old blessed slot.
    REQUIRE(party.setActiveMemberIndex(1));
    REQUIRE(runtime.executeEventById(program, std::nullopt, 103, state, &party));
    CHECK_EQ(party.member(1)->might, 34u);
    CHECK(party.member(1)->playerBits.contains(70));

    // The previously blessed character moved to slot 2; repeat visits only heal.
    REQUIRE(party.setActiveMemberIndex(2));
    party.applyMemberCondition(2, CharacterCondition::Weak);
    REQUIRE(runtime.executeEventById(program, std::nullopt, 103, state, &party));
    CHECK_EQ(party.member(2)->might, 34u);
    CHECK_FALSE(party.member(2)->conditions.test(static_cast<size_t>(CharacterCondition::Weak)));

    Party oldParty = {};
    oldParty.seed(seed);
    oldParty.member(1)->might = 34;
    EventRuntimeState oldState = {};
    oldState.namedMapVars["ShrineOfGodsBlessed1"] = 1;
    oldState.namedMapVars["ShrineOfGodsBlessed4"] = 1;
    REQUIRE(runtime.executeOnLoadEvents(program, std::nullopt, oldState, &oldParty));
    CHECK(oldParty.member(1)->playerBits.contains(70));
    CHECK_FALSE(oldParty.member(0)->playerBits.contains(70));
    CHECK_FALSE(oldParty.member(2)->playerBits.contains(70));
    CHECK_EQ(oldState.namedMapVars["ShrineOfGodsBlessed1"], 0);
    CHECK_EQ(oldState.namedMapVars["ShrineOfGodsBlessed4"], 0);
    REQUIRE(runtime.executeOnLoadEvents(program, std::nullopt, oldState, &oldParty));
    REQUIRE(oldParty.setActiveMemberIndex(1));
    REQUIRE(runtime.executeEventById(program, std::nullopt, 103, oldState, &oldParty));
    CHECK_EQ(oldParty.member(1)->might, 34u);
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
        CHECK_EQ(runtimeState.textureOverrides[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(2912)], "trekscon");
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
        REQUIRE(localEventProgram->getContextActionMetadata(16).has_value());
        CHECK_EQ(localEventProgram->getContextActionMetadata(16)->kind, "open_chest");
        CHECK_EQ(localEventProgram->getContextActionMetadata(16)->chestIds, std::vector<uint32_t>({1, 6}));
        CHECK_EQ(localEventProgram->getOpenedChestIds(16), std::vector<uint32_t>({1, 6}));

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
        CHECK_EQ(keyState.mapVars[4], 1u);
        CHECK(keyParty.hasQuestBit(1035));
        CHECK(keyParty.hasQuestBit(1223));
        REQUIRE_FALSE(keyState.openedChestIds.empty());
        CHECK_EQ(keyState.openedChestIds.back(), 6u);

        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 16, keyState, &keyParty));
        CHECK_EQ(keyState.openedChestIds.back(), 1u);
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
        CHECK_EQ(runtimeState.textureOverrides[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(949)], "d6flora");

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
        for (uint16_t eventId = 1; eventId <= 21; ++eventId)
        {
            if (eventId == 19)
            {
                continue;
            }
            REQUIRE(localEventProgram->getContextActionMetadata(eventId).has_value());
            CHECK_EQ(localEventProgram->getContextActionMetadata(eventId)->kind, "open_door");
        }

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
            CHECK_EQ(cubeState.textureOverrides[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(faceIndex)], "lavatyl");
            CHECK((cubeState.facetSetMasks[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(faceIndex)]
                & fluidMask) != 0);
        }

        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 45, cubeState, &party));
        CHECK_EQ(cubeState.mapVars[4], 0u);
        for (uint32_t faceIndex : {4298u, 4299u, 4300u, 4301u, 4302u})
        {
            CHECK_EQ(cubeState.textureOverrides[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(faceIndex)], "orwtrtyl");
        }

        OpenYAMM::Game::EventRuntimeState clearedWayState = {};
        clearedWayState.mapVars[3] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 33, clearedWayState, &party));
        CHECK_EQ(clearedWayState.mapVars[3], 2u);
        CHECK((clearedWayState.facetSetMasks[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(4522)]
            & untouchableMask) != 0);
        CHECK((clearedWayState.facetSetMasks[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(4575)]
            & untouchableMask) != 0);

        OpenYAMM::Game::EventRuntimeState onLoadState = {};
        onLoadState.mapVars[2] = 1;
        onLoadState.mapVars[3] = 1;
        onLoadState.mapVars[4] = 1;
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 58, onLoadState, &party));
        for (uint32_t faceIndex : {4219u, 4220u, 4221u, 4222u, 4223u})
        {
            CHECK_EQ(onLoadState.textureOverrides[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(faceIndex)], "lavatyl");
        }
        for (uint32_t faceIndex : {4265u, 4266u, 4267u, 4268u, 4269u})
        {
            CHECK_EQ(onLoadState.textureOverrides[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(faceIndex)], "lavatyl");
        }
        for (uint32_t faceIndex : {4298u, 4299u, 4300u, 4301u, 4302u})
        {
            CHECK_EQ(onLoadState.textureOverrides[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(faceIndex)], "lavatyl");
        }
        CHECK((onLoadState.facetSetMasks[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(4522)]
            & untouchableMask) != 0);
        CHECK((onLoadState.facetSetMasks[OpenYAMM::Game::EventRuntime::indoorFaceReferenceKey(4575)]
            & untouchableMask) != 0);
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
        // Dragonsand's pedestal (event 105) no longer opens MMerge's dimensional travel.
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 105, runtimeState, &party));
        CHECK_FALSE(runtimeState.pendingDimensionDoorOverlay);

        OpenYAMM::Game::Party shrineParty = makeScriptedRegressionParty();
        OpenYAMM::Game::Character *pMember = shrineParty.member(0);
        REQUIRE(pMember != nullptr);
        OpenYAMM::Game::EventRuntimeState shrineState = {};
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 103, shrineState, &shrineParty));
        CHECK(pMember->playerBits.contains(70));
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
        eventRuntime.executeMapRefillHooks(localEventProgram, std::nullopt, mapDeltaData, shrineState, &shrineParty);
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 103, shrineState, &shrineParty));
        CHECK(pMember->playerBits.contains(70));
        CHECK_EQ(pMember->might, 34u);

        // A map reset must not reset the character's blessing.
        eventRuntime.initializeMapRuntimeState(mapDeltaData, shrineState);
        REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 103, shrineState, &shrineParty));
        CHECK_EQ(pMember->might, 34u);
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
        REQUIRE(localEventProgram->getContextActionMetadata(60).has_value());
        CHECK_EQ(localEventProgram->getContextActionMetadata(60)->kind, "leave_dungeon");
        CHECK_EQ(localEventProgram->getContextActionMetadata(60)->targetMap, std::optional<std::string>("oute3.odm"));

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

TEST_CASE("mm6 ironfist sword removal updates its decoration and restores from quest progress")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "outd3.odm",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });

    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->outdoorMapData.has_value());
    REQUIRE_GT(pLoadedMap->outdoorMapData->entities.size(), 232u);
    const OpenYAMM::Game::OutdoorEntity &swordEntity = pLoadedMap->outdoorMapData->entities[230];
    CHECK_EQ(swordEntity.name, "swrdstn");
    CHECK_EQ(swordEntity.eventIdSecondary, 225u);
    const uint32_t swordKey = swordEntity.spriteOverrideKey(230);
    const uint32_t otherRockKey = pLoadedMap->outdoorMapData->entities[232].spriteOverrideKey(232);
    REQUIRE_NE(swordKey, otherRockKey);

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram =
        loadMm6MapOverlayProgram(OPENYAMM_SOURCE_DIR, "outd3", "outd3_mmmerge", error);
    REQUIRE_MESSAGE(localEventProgram.has_value(), error.c_str());
    OpenYAMM::Game::EventRuntime eventRuntime = {};
    OpenYAMM::Game::Party party = makeScriptedRegressionParty();
    OpenYAMM::Game::EventRuntimeState weakState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 225, weakState, &party));
    CHECK_FALSE(party.hasQuestBit(1327));
    CHECK(weakState.grantedItems.empty());
    CHECK(weakState.spriteOverrides.empty());

    OpenYAMM::Game::EventRuntimeState freshLoadState = {};
    REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, freshLoadState, &party));
    CHECK_FALSE(freshLoadState.spriteOverrides.contains(swordKey));

    REQUIRE(party.member(0) != nullptr);
    party.member(0)->might = 40;
    OpenYAMM::Game::EventRuntimeState removalState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 225, removalState, &party));
    CHECK(party.hasQuestBit(1327));
    REQUIRE_EQ(removalState.grantedItems.size(), 1u);
    CHECK_EQ(removalState.grantedItems.front().objectDescriptionId, 1609u);
    REQUIRE(removalState.spriteOverrides.contains(swordKey));
    CHECK_EQ(removalState.spriteOverrides.at(swordKey).textureName, "swrdstx");
    CHECK_FALSE(removalState.spriteOverrides.at(swordKey).hidden);
    CHECK_FALSE(removalState.spriteOverrides.contains(otherRockKey));

    OpenYAMM::Game::EventRuntimeState repeatedState = {};
    REQUIRE(eventRuntime.executeEventById(localEventProgram, std::nullopt, 225, repeatedState, &party));
    CHECK(repeatedState.grantedItems.empty());

    OpenYAMM::Game::EventRuntimeState completedLoadState = {};
    REQUIRE(eventRuntime.buildOnLoadState(localEventProgram, std::nullopt, std::nullopt, completedLoadState, &party));
    REQUIRE(completedLoadState.spriteOverrides.contains(swordKey));
    CHECK_EQ(completedLoadState.spriteOverrides.at(swordKey).textureName, "swrdstx");
    CHECK_FALSE(completedLoadState.spriteOverrides.contains(otherRockKey));
    CHECK(completedLoadState.grantedItems.empty());
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

TEST_CASE("mm7 actor previews draw every actor as a model and load no monster sprite")
{
    // The MM7 monster billboards were retired (assets_legacy/sprites_mm7_monsters_20261021): every MM7 monster,
    // the arena rats included, draws its model, so maps with MM7 monsters (also MM7 art on Mount Nighon) request
    // none of their frames and miss none.
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MonsterTable &monsterTable = mapLoader.gameDataLoader.getMonsterTable();
    std::shared_ptr<OpenYAMM::Game::ActorModelManifest> pActorModels =
        std::make_shared<OpenYAMM::Game::ActorModelManifest>();
    std::string error;
    REQUIRE_MESSAGE(pActorModels->load(mapLoader.assetFileSystem,
        {"worlds/mm6/models/actors.yml", "worlds/mm7/models/actors.yml", "worlds/mm8/models/actors.yml"}, {},
        monsterTable, error), error);

    for (const char *pMapFileName : {"7out01.odm", "7d06.blv", "out10.odm", "7d35.blv", "7d28.blv", "7d11.blv"})
    {
        CAPTURE(pMapFileName);
        const OpenYAMM::Game::MapStatsEntry *pMapEntry =
            mapLoader.gameDataLoader.getMapStats().findByFileName(pMapFileName);
        REQUIRE(pMapEntry != nullptr);
        const OpenYAMM::Game::MapAssetLoader loader = {};
        const std::optional<OpenYAMM::Game::MapAssetInfo> loadedMap = loader.load(
            mapLoader.assetFileSystem,
            *pMapEntry,
            monsterTable,
            mapLoader.gameDataLoader.getObjectTable(),
            OpenYAMM::Game::MapLoadPurpose::ActorPreviews,
            OpenYAMM::Game::MapCompanionLoadOptions{
                .allowSceneYml = true,
                .allowLegacyCompanion = true,
            },
            {},
            nullptr,
            pActorModels);
        REQUIRE(loadedMap.has_value());
        const std::optional<OpenYAMM::Game::ActorPreviewBillboardSet> &billboards =
            loadedMap->outdoorActorPreviewBillboardSet ? loadedMap->outdoorActorPreviewBillboardSet
                                                       : loadedMap->indoorActorPreviewBillboardSet;
        REQUIRE(billboards.has_value());
        REQUIRE_FALSE(billboards->billboards.empty());
        CHECK_EQ(billboards->missingTextureActorCount, 0u);
        for (const OpenYAMM::Game::ActorPreviewBillboard &billboard : billboards->billboards)
        {
            CHECK_MESSAGE(billboard.modelled, billboard.monsterId);
        }
        CHECK(billboards->textures.empty());
    }
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

    CHECK_FALSE(actorService.resolveActorTargetPolicy(warlock, peasant).canTarget);

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

TEST_CASE("mm7 walls of mist air elementals resolve their merged sprite frames")
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
    // The frame is metadata only: the elementals draw models and the image left the runtime on 2026-10-21.
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
    const OpenYAMM::Game::DecorationBillboardSet &decorations = *pLoadedMap->indoorDecorationBillboardSet;
    CHECK_FALSE(decorations.billboards.empty());
    // Every MM7 decoration is a 3D model since 2026-10-16 (engine/models/indoor_decorations.yml): each billboard is
    // drawn by a model, so no sprite texture loads unless one shows a sprite.
    CHECK(std::all_of(decorations.billboards.begin(), decorations.billboards.end(),
        [&](const OpenYAMM::Game::DecorationBillboard &billboard)
        {
            return billboard.spriteId == 0 || decorations.modelSpriteIds.contains(billboard.spriteId)
                || !decorations.textures.empty();
        }));
    CHECK(std::any_of(
        pLoadedMap->indoorDecorationBillboardSet->billboards.begin(),
        pLoadedMap->indoorDecorationBillboardSet->billboards.end(),
        [](const OpenYAMM::Game::DecorationBillboard &billboard)
        {
            return billboard.sectorId >= 0;
        }));
    REQUIRE(pLoadedMap->indoorActorPreviewBillboardSet.has_value());
    CHECK_GT(pLoadedMap->indoorActorPreviewBillboardSet->billboards.size(), 0u);
    // Its dragons draw models (see "mm7 actor previews draw every actor as a model and load no monster sprite").
}

TEST_CASE("mm7 red dwarf mine statues are models and skip their nonzero-palette sprite textures")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "7d34.blv",
        OpenYAMM::Game::MapLoadPurpose::BillboardPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorDecorationBillboardSet.has_value());

    const OpenYAMM::Game::DecorationBillboardSet &billboardSet =
        *pLoadedMap->indoorDecorationBillboardSet;
    const auto textureLoaded =
        [&billboardSet](const std::string &textureName, int16_t paletteId)
        {
            return std::any_of(
                billboardSet.textures.begin(),
                billboardSet.textures.end(),
                [&](const OpenYAMM::Game::OutdoorBitmapTexture &texture)
                {
                    return texture.textureName == textureName && texture.paletteId == paletteId;
                });
        };

    for (uint16_t eventId = 376; eventId <= 382; ++eventId)
    {
        const std::vector<OpenYAMM::Game::DecorationBillboard>::const_iterator billboardIterator =
            std::find_if(
                billboardSet.billboards.begin(),
                billboardSet.billboards.end(),
                [eventId](const OpenYAMM::Game::DecorationBillboard &billboard)
                {
                    return billboard.eventIdSecondary == eventId;
                });
        REQUIRE_MESSAGE(
            billboardIterator != billboardSet.billboards.end(),
            ("missing Red Dwarf Mines statue event " + std::to_string(eventId)).c_str());

        const OpenYAMM::Game::SpriteFrameEntry *pFrame =
            billboardSet.spriteFrameTable.getFrame(billboardIterator->spriteId, 0);
        REQUIRE(pFrame != nullptr);
        CHECK_EQ(pFrame->paletteId, 3);

        // The dwarf statues (7dec54, 7dec55) are 3D models since 2026-10-16: their palette-3 sprite views do not
        // load.
        CHECK(billboardSet.modelSpriteIds.contains(billboardIterator->spriteId));
        for (int octant = 0; octant < 8; ++octant)
        {
            const OpenYAMM::Game::ResolvedSpriteTexture resolvedTexture =
                OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pFrame, octant);
            CHECK_FALSE(textureLoaded(resolvedTexture.textureName, pFrame->paletteId));
        }
    }
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

TEST_CASE("mm6 merged indoor maps normalize legacy static lights to visible white")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "oracle.blv",
        OpenYAMM::Game::MapLoadPurpose::HeadlessGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());

    const OpenYAMM::Game::IndoorMapData &mapData = *pLoadedMap->indoorMapData;
    REQUIRE_EQ(mapData.version, 8);
    REQUIRE_GT(mapData.lights.size(), 62u);

    for (size_t lightId = 52; lightId <= 62; ++lightId)
    {
        const OpenYAMM::Game::IndoorLight &light = mapData.lights[lightId];
        CHECK_GT(light.radius, 0);
        CHECK_GT(light.brightness, 0);
        CHECK_EQ(light.red, 255);
        CHECK_EQ(light.green, 255);
        CHECK_EQ(light.blue, 255);
    }
}

TEST_CASE("mm8 Ogre peasant bindings resolve all civilian tiers without combat animations or equipment")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MonsterTable &monsters = mapLoader.gameDataLoader.getMonsterTable();
    OpenYAMM::Game::ActorModelManifest models;
    std::string error;
    REQUIRE_MESSAGE(models.load(mapLoader.assetFileSystem, {"worlds/mm8/models/actors.yml"}, {}, monsters, error),
        error);
    for (int16_t id = 28; id <= 30; ++id)
    {
        const OpenYAMM::Game::MonsterEntry *pMonster = monsters.findById(id);
        REQUIRE(pMonster != nullptr);
        CHECK(models.bindsMonster(id));
        const OpenYAMM::Game::ActorModelManifest::Entry *pBinding = models.find(pMonster->internalName);
        REQUIRE(pBinding != nullptr);
        const YAML::Node &entry = pBinding->node;
        CHECK_EQ(entry["model"].as<std::string>(), "worlds/mm8/models/mm8_m436.glb");
        CHECK_EQ(entry["skin"].as<std::string>(), "m436_" + std::string(1, char('a' + id - 28)));
        CHECK_FALSE(entry["attachments"].IsDefined());
        CHECK_FALSE(entry["animation"]["cast"].IsDefined());
        CHECK_FALSE(entry["clips"]["attack_melee"].IsDefined());
        CHECK_FALSE(entry["clips"]["attack_ranged"].IsDefined());
        CHECK(entry["scale"].as<float>() == doctest::Approx(133.257758f));
        CHECK_FALSE(entry["animation"]["events"].IsDefined());
        const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats =
            monsters.findStatsByPictureName(pMonster->internalName);
        REQUIRE(pStats != nullptr);
        CHECK(pStats->aiType == OpenYAMM::Game::MonsterTable::MonsterAiType::Wimp);
    }
}

TEST_CASE("mm8 Ogre actor bindings resolve merged monster ids and the fitted club")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MonsterTable &monsters = mapLoader.gameDataLoader.getMonsterTable();
    OpenYAMM::Game::ActorModelManifest models;
    std::string error;
    REQUIRE_MESSAGE(models.load(mapLoader.assetFileSystem, {"worlds/mm8/models/actors.yml"}, {}, monsters, error),
        error);
    for (int16_t id = 31; id <= 33; ++id)
    {
        const OpenYAMM::Game::MonsterEntry *pMonster = monsters.findById(id);
        REQUIRE(pMonster != nullptr);
        CHECK(models.bindsMonster(id));
        const OpenYAMM::Game::ActorModelManifest::Entry *pBinding = models.find(pMonster->internalName);
        REQUIRE(pBinding != nullptr);
        const YAML::Node &entry = pBinding->node;
        CHECK_EQ(entry["model"].as<std::string>(), "worlds/mm8/models/mm8_m440.glb");
        CHECK_EQ(entry["skin"].as<std::string>(), "m440_" + std::string(1, char('a' + id - 31)));
        REQUIRE_EQ(entry["attachments"].size(), 1);
        CHECK_EQ(entry["attachments"][0]["node"].as<std::string>(), "Club");
        CHECK_EQ(entry["attachments"][0]["model"].as<std::string>(), "worlds/mm8/models/mm8_m440_club.glb");
        CHECK(entry["scale"].as<float>() == doctest::Approx(154.312274f));
        // The MM8 creature post-process (2026-10-21) retimed the impact to the club's contact.
        CHECK(entry["animation"]["events"]["attack_melee"]["impact"].as<float>() == doctest::Approx(0.955f));
    }
}

TEST_CASE("mm8 Vampire actor bindings resolve all tiers and dual palm spell release")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MonsterTable &monsters = mapLoader.gameDataLoader.getMonsterTable();
    OpenYAMM::Game::ActorModelManifest models;
    std::string error;
    REQUIRE_MESSAGE(models.load(mapLoader.assetFileSystem, {"worlds/mm8/models/actors.yml"}, {}, monsters, error),
        error);
    for (int16_t id = 52; id <= 54; ++id)
    {
        const OpenYAMM::Game::MonsterEntry *pMonster = monsters.findById(id);
        REQUIRE(pMonster != nullptr);
        CHECK(models.bindsMonster(id));
        const OpenYAMM::Game::ActorModelManifest::Entry *pBinding = models.find(pMonster->internalName);
        REQUIRE(pBinding != nullptr);
        const YAML::Node &entry = pBinding->node;
        CHECK_EQ(entry["model"].as<std::string>(), "worlds/mm8/models/mm8_m468.glb");
        CHECK_EQ(entry["skin"].as<std::string>(), "m468_" + std::string(1, char('a' + id - 52)));
        CHECK(entry["scale"].as<float>() == doctest::Approx(114.478790f));
        const YAML::Node &animation = entry["animation"];
        CHECK_EQ(animation["cast"].as<std::string>(), "Cast");
        CHECK_NE(animation["cast"].as<std::string>(), entry["clips"]["attack_ranged"].as<std::string>());
        CHECK_NE(animation["cast"].as<std::string>(), entry["clips"]["attack_melee"].as<std::string>());
        CHECK_EQ(animation["sockets"]["palm_left"].as<std::string>(), "Socket_Palm_Left");
        CHECK_EQ(animation["sockets"]["palm_right"].as<std::string>(), "Socket_Palm_Right");
        CHECK(animation["events"]["attack_melee"]["impact"].as<float>() == doctest::Approx(1.482f));
        CHECK(animation["events"]["cast"]["impact"].as<float>() == doctest::Approx(35.0f / 30.0f));
        CHECK_EQ(animation["events"]["cast"]["glow"].as<std::vector<std::string>>(),
            std::vector<std::string>{"palm_left", "palm_right"});
    }
}

TEST_CASE("mm6 darkmoor actor previews build encounter tiers and summoned wisps as models without sprites")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MonsterTable &monsterTable = mapLoader.gameDataLoader.getMonsterTable();
    const OpenYAMM::Game::MapStatsEntry *pMapEntry =
        mapLoader.gameDataLoader.getMapStats().findByFileName("cd2.blv");
    REQUIRE(pMapEntry != nullptr);

    std::shared_ptr<OpenYAMM::Game::ActorModelManifest> pActorModels =
        std::make_shared<OpenYAMM::Game::ActorModelManifest>();
    std::string error;
    // Every world's bindings, as the game loads them: the summoned wisps are bound by MM8's.
    REQUIRE_MESSAGE(pActorModels->load(mapLoader.assetFileSystem,
        {"worlds/mm6/models/actors.yml", "worlds/mm7/models/actors.yml", "worlds/mm8/models/actors.yml"}, {},
        monsterTable, error), error);

    const OpenYAMM::Game::MapAssetLoader loader = {};
    const std::optional<OpenYAMM::Game::MapAssetInfo> loadedMap = loader.load(
        mapLoader.assetFileSystem,
        *pMapEntry,
        monsterTable,
        mapLoader.gameDataLoader.getObjectTable(),
        OpenYAMM::Game::MapLoadPurpose::ActorPreviews,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        },
        {},
        nullptr,
        pActorModels);
    REQUIRE(loadedMap.has_value());
    REQUIRE(loadedMap->indoorActorPreviewBillboardSet.has_value());

    const OpenYAMM::Game::ActorPreviewBillboardSet &billboardSet = *loadedMap->indoorActorPreviewBillboardSet;
    const std::array<const OpenYAMM::Game::MapEncounterInfo *, 3> encounters = {{
        &pMapEntry->encounter1,
        &pMapEntry->encounter2,
        &pMapEntry->encounter3,
    }};

    for (const OpenYAMM::Game::MapEncounterInfo *pEncounter : encounters)
    {
        const std::string pictureBase =
            pEncounter->pictureName.empty() ? pEncounter->monsterName : pEncounter->pictureName;

        for (char tierLetter : {'A', 'B', 'C'})
        {
            const std::string pictureName = pictureBase + " " + std::string(1, tierLetter);
            const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats =
                monsterTable.findStatsByPictureName(pictureName);
            REQUIRE(pStats != nullptr);
            const OpenYAMM::Game::MonsterEntry *pMonsterEntry = monsterTable.findById(int16_t(pStats->id));
            REQUIRE(pMonsterEntry != nullptr);
            CHECK_MESSAGE(billboardSet.drawsModel(pMonsterEntry), pictureName);
            CHECK_MESSAGE(std::find(billboardSet.modelDescriptors.begin(), billboardSet.modelDescriptors.end(),
                pMonsterEntry->internalName) != billboardSet.modelDescriptors.end(), pictureName);
        }
    }

    for (const OpenYAMM::Game::ActorPreviewBillboard &billboard : billboardSet.billboards)
    {
        CHECK(billboard.modelled);
    }

    // Every monster the map can show is modelled, so no sprite is decoded.
    CHECK(billboardSet.textures.empty());

    constexpr std::array<int16_t, 3> SummonWispMonsterIds = {97, 98, 99};

    for (int16_t summonMonsterId : SummonWispMonsterIds)
    {
        const OpenYAMM::Game::MonsterEntry *pMonsterEntry = monsterTable.findById(summonMonsterId);
        REQUIRE(pMonsterEntry != nullptr);
        CHECK(billboardSet.drawsModel(pMonsterEntry));
    }
}

TEST_CASE("full gameplay map load preloads no sprites for unplaced items or missiles")
{
    // Items on the ground are models and spell missiles and impacts are models and effects
    // (GROUND_ITEMS_3D_BEHAVIOUR.md), so no object the map might spawn later has its sprite preloaded.
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "6d01.blv",
        OpenYAMM::Game::MapLoadPurpose::FullGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapDeltaData.has_value());
    REQUIRE(pLoadedMap->indoorSpriteObjectBillboardSet.has_value());

    const OpenYAMM::Game::ObjectTable &objectTable = mapLoader.gameDataLoader.getObjectTable();
    const OpenYAMM::Game::SpriteObjectBillboardSet &billboardSet = *pLoadedMap->indoorSpriteObjectBillboardSet;
    const auto unplacedObject = [&](int16_t objectId) -> const OpenYAMM::Game::ObjectEntry *
    {
        const std::optional<uint16_t> objectDescriptionId = objectTable.findDescriptionIdByObjectId(objectId);
        REQUIRE(objectDescriptionId.has_value());
        const bool placed = std::any_of(
            pLoadedMap->indoorMapDeltaData->spriteObjects.begin(),
            pLoadedMap->indoorMapDeltaData->spriteObjects.end(),
            [objectDescriptionId](const OpenYAMM::Game::MapDeltaSpriteObject &object)
            {
                return object.objectDescriptionId == *objectDescriptionId;
            });
        REQUIRE_FALSE(placed);
        return objectTable.get(*objectDescriptionId);
    };
    const auto preloaded = [&](const OpenYAMM::Game::ObjectEntry &object)
    {
        const OpenYAMM::Game::SpriteFrameEntry *pFrame = billboardSet.spriteFrameTable.getFrame(object.spriteId, 0);
        REQUIRE(pFrame != nullptr);
        const OpenYAMM::Game::ResolvedSpriteTexture resolvedTexture =
            OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
        return std::any_of(
            billboardSet.textures.begin(),
            billboardSet.textures.end(),
            [&resolvedTexture, pFrame](const OpenYAMM::Game::OutdoorBitmapTexture &texture)
            {
                return texture.textureName == resolvedTexture.textureName && texture.paletteId == pFrame->paletteId;
            });
    };

    // Object 307: a dagger, an item.
    const OpenYAMM::Game::ObjectEntry *pDagger = unplacedObject(307);
    REQUIRE(pDagger != nullptr);
    REQUIRE((pDagger->flags & OpenYAMM::Game::ObjectDescUnpickable) == 0);
    CHECK_FALSE(preloaded(*pDagger));

    // Object 10030: the DarkFire Bolt missile.
    const OpenYAMM::Game::ObjectEntry *pMissile = unplacedObject(10030);
    REQUIRE(pMissile != nullptr);
    REQUIRE((pMissile->flags & OpenYAMM::Game::ObjectDescUnpickable) != 0);
    CHECK_FALSE(preloaded(*pMissile));
}

TEST_CASE("MM9 quest and miscellaneous items resolve dedicated WorldItem sprites")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "6d01.blv",
        OpenYAMM::Game::MapLoadPurpose::FullGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorSpriteObjectBillboardSet.has_value());

    const OpenYAMM::Game::ItemTable &itemTable = mapLoader.gameDataLoader.getItemTable();
    const OpenYAMM::Game::ObjectTable &objectTable = mapLoader.gameDataLoader.getObjectTable();
    const OpenYAMM::Game::SpriteObjectBillboardSet &billboardSet =
        *pLoadedMap->indoorSpriteObjectBillboardSet;
    size_t checkedItemCount = 0;

    for (const OpenYAMM::Game::ItemDefinition &item : itemTable.entries())
    {
        if (item.packageId != "mm9"
            || (!item.hasContentFlag("Quest") && OpenYAMM::Game::toLowerCopy(item.sourceEquipType) != "items"))
        {
            continue;
        }

        const uint32_t expectedObjectId = 20000 + item.sourceItemId;
        const uint32_t expectedSpriteId = 24000 + item.sourceItemId;
        CHECK_EQ(item.spriteIndex, expectedObjectId);
        const std::optional<uint16_t> descriptionId =
            objectTable.findDescriptionIdByObjectId(static_cast<int16_t>(expectedObjectId));
        REQUIRE(descriptionId.has_value());
        const OpenYAMM::Game::ObjectEntry *pObjectEntry = objectTable.get(*descriptionId);
        REQUIRE(pObjectEntry != nullptr);
        CHECK_EQ(pObjectEntry->spriteId, expectedSpriteId);

        const OpenYAMM::Game::SpriteFrameEntry *pFrame =
            billboardSet.spriteFrameTable.getFrame(pObjectEntry->spriteId, 0);
        REQUIRE(pFrame != nullptr);
        const std::string rawItemId = std::to_string(item.sourceItemId);
        const std::string expectedTextureName =
            "mm9wi" + std::string(4 - rawItemId.size(), '0') + rawItemId;
        const OpenYAMM::Game::ResolvedSpriteTexture resolvedTexture =
            OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
        CHECK_EQ(resolvedTexture.textureName, expectedTextureName);
        ++checkedItemCount;
    }

    CHECK_EQ(checkedItemCount, 173);
}

TEST_CASE("full gameplay New Sorpigal load keeps actor textures lazy and loads no modelled decoration sprite")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "oute3.odm",
        OpenYAMM::Game::MapLoadPurpose::FullGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->outdoorActorPreviewBillboardSet.has_value());

    const OpenYAMM::Game::ActorPreviewBillboardSet &billboardSet =
        *pLoadedMap->outdoorActorPreviewBillboardSet;
    CHECK(billboardSet.textures.empty());
    REQUIRE_FALSE(billboardSet.billboards.empty());

    bool resolvedActorTexture = false;

    for (const OpenYAMM::Game::ActorPreviewBillboard &billboard : billboardSet.billboards)
    {
        const OpenYAMM::Game::SpriteFrameEntry *pFrame =
            billboardSet.spriteFrameTable.getFrame(billboard.spriteFrameIndex, 0);

        if (pFrame == nullptr)
        {
            continue;
        }

        const OpenYAMM::Game::ResolvedSpriteTexture resolvedTexture =
            OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
        CHECK_FALSE(resolvedTexture.textureName.empty());
        resolvedActorTexture = true;
    }

    CHECK(resolvedActorTexture);

    REQUIRE(pLoadedMap->outdoorDecorationBillboardSet.has_value());
    const OpenYAMM::Game::DecorationBillboardSet &decorationSet =
        *pLoadedMap->outdoorDecorationBillboardSet;
    const auto decorationTextureLoaded =
        [&decorationSet](const std::string &textureName, int16_t paletteId)
        {
            return std::any_of(
                decorationSet.textures.begin(),
                decorationSet.textures.end(),
                [&](const OpenYAMM::Game::OutdoorBitmapTexture &texture)
                {
                    return texture.textureName == textureName && texture.paletteId == paletteId;
                });
        };

    // Models draw every New Sorpigal decoration (engine/models/decorations.yml), so none of their sprites loads,
    // including a state an event switches to (the drawn sword) or a frame of an animation (flags, sea arches).
    for (const char *pDecorationName : {"swrdstn", "swrdstx", "fla3__01", "bigbarel", "searka01", "searkb01"})
    {
        const OpenYAMM::Game::DecorationEntry *pDecoration =
            decorationSet.decorationTable.findByInternalName(pDecorationName);
        REQUIRE_MESSAGE(pDecoration != nullptr, pDecorationName);
        CHECK_MESSAGE(decorationSet.modelSpriteIds.contains(pDecoration->spriteId), pDecorationName);
    }

    CHECK_FALSE(decorationTextureLoaded("swrdstn", 546));
    CHECK_FALSE(decorationTextureLoaded("fla3__06", 546));
    CHECK_FALSE(decorationTextureLoaded("bigbarel", 547));
    CHECK_FALSE(decorationTextureLoaded("searka06", 873));
    CHECK_FALSE(decorationTextureLoaded("searkb05", 873));
}

TEST_CASE("full gameplay Dagger Wound load does not decode predicted actor textures")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem,
        mapLoader.gameDataLoader,
        "out01.odm",
        OpenYAMM::Game::MapLoadPurpose::FullGameplay,
        OpenYAMM::Game::MapCompanionLoadOptions{
            .allowSceneYml = true,
            .allowLegacyCompanion = true,
        });
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->outdoorActorPreviewBillboardSet.has_value());

    const OpenYAMM::Game::ActorPreviewBillboardSet &billboardSet =
        *pLoadedMap->outdoorActorPreviewBillboardSet;
    CHECK(billboardSet.textures.empty());
    CHECK_FALSE(billboardSet.billboards.empty());
    CHECK_EQ(billboardSet.texturedActorCount, billboardSet.billboards.size());
    CHECK_EQ(billboardSet.missingTextureActorCount, 0);
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

TEST_CASE("outdoor liquid bmodel faces load no art and carry their liquid colour")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();

    struct WaterMapCase
    {
        const char *pMapFileName = nullptr;
        const char *pBaseTextureName = nullptr;
        const char *pLegacyFrameTextureName = nullptr;
    };

    const std::array<WaterMapCase, 3> waterMapCases = {{
        {"out01.odm", "wtrtyl", "hdwtr000"},
        {"7out01.odm", "7wtrtyl", "7hdwtr000"},
        {"oute3.odm", "6wtrtyl", "6hdwtr000"},
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
        const auto water = std::find_if(textureSet.textures.begin(), textureSet.textures.end(),
            [&](const OpenYAMM::Game::OutdoorBitmapTexture &texture)
            { return texture.textureName == waterMapCase.pBaseTextureName; });
        REQUIRE(water != textureSet.textures.end());
        CHECK(water->liquid == OpenYAMM::Game::LiquidKind::Water);
        CHECK(water->waterColorAbgr != 0);
        // The liquid shader draws these faces: a 128-texel face keeps its UVs, the art is only the colour.
        CHECK(water->width == 128);
        CHECK(water->physicalWidth < 16);
        CHECK_FALSE(bitmapTextureSetContains(textureSet.textures, waterMapCase.pLegacyFrameTextureName));

        const OpenYAMM::Game::SurfaceAnimationSequence *pAnimation =
            findSurfaceAnimationBinding(textureSet.animationBindings, waterMapCase.pBaseTextureName);
        REQUIRE(pAnimation != nullptr);
        CHECK(pAnimation->frames.size() <= 1);
    }
}

TEST_CASE("MM7 Haunted Mansion cleric portrait animates instead of drawing water")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedIndoorMapWithCompanionOptions(
        mapLoader.assetFileSystem, mapLoader.gameDataLoader, "7d37.blv",
        OpenYAMM::Game::MapLoadPurpose::Full,
        OpenYAMM::Game::MapCompanionLoadOptions{.allowSceneYml = true, .allowLegacyCompanion = true});
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->indoorMapData.has_value());
    REQUIRE(pLoadedMap->indoorTextureSet.has_value());

    // Face 1844 keeps the leftover name hdwtr010; its stored frame table index 13 is the cleric portrait.
    REQUIRE(pLoadedMap->indoorMapData->faces.size() > 1844);
    const OpenYAMM::Game::IndoorFace &portraitFace = pLoadedMap->indoorMapData->faces[1844];
    CHECK_EQ(portraitFace.textureName, "hdwtr010");
    CHECK(OpenYAMM::Game::hasFaceAttribute(portraitFace.attributes, OpenYAMM::Game::FaceAttribute::Animated));
    CHECK_EQ(portraitFace.textureFrameTableIndex, 13);

    const OpenYAMM::Game::IndoorTextureSet &textureSet = *pLoadedMap->indoorTextureSet;
    const OpenYAMM::Game::SurfaceAnimationSequence *pAnimation =
        findSurfaceAnimationBinding(textureSet.animationBindings, "hdwtr010");
    REQUIRE(pAnimation != nullptr);
    REQUIRE(pAnimation->frames.size() > 1);
    CHECK_EQ(pAnimation->frames.front().textureName, "cleric_0");
    CHECK_EQ(pAnimation->frames[1].textureName, "cleric_20");

    // The liquid shader no longer claims the face: no water stand-in is made for its leftover name.
    for (const OpenYAMM::Game::OutdoorBitmapTexture &texture : textureSet.textures)
    {
        if (texture.textureName == "hdwtr010")
        {
            CHECK(texture.liquid == OpenYAMM::Game::LiquidKind::None);
            CHECK(texture.waterColorAbgr == 0);
        }
    }

    CHECK(bitmapTextureSetContains(textureSet.textures, "cleric_0"));
}

TEST_CASE("MM8 lava terrain is drawn by the liquid shader")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MapAssetInfo *pLoadedMap = loadCachedOutdoorMapWithCompanionOptions(
        mapLoader.assetFileSystem, mapLoader.gameDataLoader, "elemf.odm",
        OpenYAMM::Game::MapLoadPurpose::RenderSurfaces,
        OpenYAMM::Game::MapCompanionLoadOptions{.allowSceneYml = true, .allowLegacyCompanion = true});
    REQUIRE(pLoadedMap != nullptr);
    REQUIRE(pLoadedMap->outdoorTerrainTiles.has_value());
    const OpenYAMM::Game::OutdoorTerrainTiles &terrainTiles = *pLoadedMap->outdoorTerrainTiles;
    size_t lavaTiles = 0;
    size_t lavaEdgeTiles = 0;
    for (size_t tileId = 0; tileId < terrainTiles.tiles.size(); ++tileId)
    {
        const OpenYAMM::Game::OutdoorTerrainTile &tile = terrainTiles.tiles[tileId];
        if (tile.liquid != OpenYAMM::Game::LiquidKind::Lava)
        {
            continue;
        }
        CHECK(tile.valid);
        CHECK(tile.water);
        CHECK(tile.waterSurface);
        CHECK(tile.waterColorAbgr != 0);
        if (tile.transitionOverlay)
        {
            ++lavaEdgeTiles;
            CHECK(terrainTiles.liquidCoverageMasks[tileId].size() == 128 * 128);
        }
        else
        {
            ++lavaTiles;
            CHECK(tile.textureName == "lavtyl");
            CHECK(terrainTiles.liquidCoverageMasks[tileId].empty());
        }
    }
    CHECK(lavaTiles > 0);
    CHECK(lavaEdgeTiles > 0);
}

TEST_CASE("outdoor terrain water and shore tiles share their world's water and shore coverage")
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
    std::array<uint32_t, 3> waterColors = {};
    size_t colorIndex = 0;

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
        REQUIRE(pLoadedMap->outdoorTerrainTiles.has_value());

        const OpenYAMM::Game::OutdoorTerrainTiles &terrainTiles = *pLoadedMap->outdoorTerrainTiles;
        const OpenYAMM::Game::OutdoorTerrainTile &fullWater =
            terrainTiles.tiles[static_cast<size_t>(waterMapCase.fullWaterTileId)];
        const OpenYAMM::Game::OutdoorTerrainTile &cachedFullWater =
            terrainTiles.tiles[static_cast<size_t>(waterMapCase.fullWaterTileId + 1)];
        const OpenYAMM::Game::OutdoorTerrainTile &transitionWater =
            terrainTiles.tiles[static_cast<size_t>(waterMapCase.transitionWaterTileId)];

        REQUIRE(fullWater.valid);
        CHECK(fullWater.water);
        CHECK(fullWater.waterSurface);
        CHECK(fullWater.liquid == OpenYAMM::Game::LiquidKind::Water);
        CHECK_FALSE(fullWater.transitionOverlay);

        REQUIRE(cachedFullWater.valid);
        CHECK(cachedFullWater.water);
        CHECK(cachedFullWater.waterSurface);
        CHECK_FALSE(cachedFullWater.transitionOverlay);

        REQUIRE(transitionWater.valid);
        CHECK(transitionWater.water);
        CHECK(transitionWater.waterSurface);
        CHECK(terrainTiles.liquidCoverageMasks[waterMapCase.transitionWaterTileId].size() == 128 * 128);
        CHECK(transitionWater.transitionOverlay);
        CHECK((fullWater.waterColorAbgr & 0xff000000u) == 0xff000000u);
        CHECK(cachedFullWater.waterColorAbgr == fullWater.waterColorAbgr);
        CHECK(transitionWater.waterColorAbgr == fullWater.waterColorAbgr);
        waterColors[colorIndex++] = fullWater.waterColorAbgr;
    }
    CHECK(waterColors[0] != waterColors[1]);
    CHECK(waterColors[0] != waterColors[2]);
    CHECK(waterColors[1] != waterColors[2]);
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

    REQUIRE(sceneLoadedMap.indoorMapData.has_value());
    REQUIRE_GT(sceneLoadedMap.indoorMapData->faces.size(), 1625u);
    REQUIRE_GT(sceneLoadedMap.indoorMapDeltaData->faceAttributes.size(), 1625u);

    const OpenYAMM::Game::IndoorFace &submarineEntryFace = sceneLoadedMap.indoorMapData->faces[1625];
    const uint32_t submarineEntryAttributes = sceneLoadedMap.indoorMapDeltaData->faceAttributes[1625];

    CHECK_EQ(submarineEntryFace.cogTriggered, 451u);
    CHECK_EQ(submarineEntryFace.facetType, 3u);
    CHECK(OpenYAMM::Game::hasFaceAttribute(submarineEntryAttributes, OpenYAMM::Game::FaceAttribute::Clickable));
    CHECK_FALSE(OpenYAMM::Game::hasFaceAttribute(submarineEntryAttributes, OpenYAMM::Game::FaceAttribute::HasHint));
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
        "mm8",
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
        "mm8",
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

TEST_CASE("mm8 Nightmare slime actor bindings resolve all tiers without ranged spell behaviour")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    const OpenYAMM::Game::MonsterTable &monsters = mapLoader.gameDataLoader.getMonsterTable();
    OpenYAMM::Game::ActorModelManifest models;
    std::string error;
    REQUIRE_MESSAGE(models.load(mapLoader.assetFileSystem, {"worlds/mm8/models/actors.yml"}, {}, monsters, error),
        error);
    for (int16_t id = 151; id <= 153; ++id)
    {
        const OpenYAMM::Game::MonsterEntry *pMonster = monsters.findById(id);
        REQUIRE(pMonster != nullptr);
        CHECK(models.bindsMonster(id));
        const OpenYAMM::Game::ActorModelManifest::Entry *pBinding = models.find(pMonster->internalName);
        REQUIRE(pBinding != nullptr);
        const YAML::Node &entry = pBinding->node;
        CHECK_EQ(entry["model"].as<std::string>(), "worlds/mm8/models/mm8_m600.glb");
        CHECK_EQ(entry["skin"].as<std::string>(), "nightmare_" + std::string(1, char('a' + id - 151)));
        CHECK_FALSE(entry["attachments"].IsDefined());
        CHECK_FALSE(entry["animation"]["cast"].IsDefined());
        // The bite glows at the jaws; there is no cast event.
        CHECK_FALSE(entry["animation"]["events"]["cast"].IsDefined());
        CHECK(entry["animation"]["events"]["attack_melee"]["impact"].as<float>() == doctest::Approx(0.563f));
        CHECK_EQ(entry["clips"]["attack_melee"].as<std::string>(), "Attack");
        CHECK_EQ(entry["clips"]["dying"].as<std::string>(), "Death");
        CHECK_EQ(entry["clips"]["dead"].as<std::string>(), "Dead");
        CHECK_GT(entry["scale"].as<float>(), 275.0f);
        CHECK_LT(entry["scale"].as<float>(), 286.0f);
    }
}

TEST_SUITE_END();

TEST_CASE("the journal's Arcomage notes list every tavern per continent and the ones the party has won")
{
    const OpenYAMM::Tests::RegressionMapLoader &mapLoader = requireRegressionMapLoader();
    OpenYAMM::Game::Party party = {};
    party.seed(createRegressionPartySeed());
    // 228: the first MM8 tavern, in Jadame.
    party.recordArcomageWin(228, 0, 0);

    const std::vector<std::string> texts = OpenYAMM::Game::buildArcomageTavernTexts(
        mapLoader.gameDataLoader.getHouseTable(), mapLoader.gameDataLoader.getMapStats(), party);

    REQUIRE(!texts.empty());
    CHECK(std::find(texts.begin(), texts.end(), "Jadame: 1 of 11 taverns won.") != texts.end());
    // Emerald Island's Two Palms Tavern plays Arcomage too, though Antagarich's champion award counts the other 13: it is
    // listed, but not counted (OY-308).
    CHECK(std::find(texts.begin(), texts.end(), "Antagarich: 0 of 13 taverns won.") != texts.end());
    CHECK(std::count_if(texts.begin(), texts.end(),
              [](const std::string &text) { return text.ends_with("(not needed for Champion)"); })
        == 1);
    CHECK(std::find(texts.begin(), texts.end(), "The Vampyre Lounge, The Pit: not won yet") != texts.end());
    CHECK(std::count_if(texts.begin(), texts.end(), [](const std::string &text) { return text.ends_with(": won"); })
        == 1);
}
