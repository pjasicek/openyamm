#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/EventSpellBuffs.h"
#include "game/party/Party.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Tests
{
inline Game::Character makeSpellRegressionPartyMember(
    const std::string &name,
    const std::string &className,
    const std::string &portraitTextureName,
    uint32_t characterDataId)
{
    Game::Character member = {};
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

inline Game::PartySeed createSpellRegressionPartySeed()
{
    Game::PartySeed seed = {};
    seed.gold = 200;
    seed.food = 7;
    seed.members.push_back(makeSpellRegressionPartyMember("Ariel", "Knight", "PC01-01", 1));
    seed.members.push_back(makeSpellRegressionPartyMember("Brom", "Cleric", "PC03-01", 3));
    seed.members.push_back(makeSpellRegressionPartyMember("Cedric", "Druid", "PC05-01", 5));
    seed.members.push_back(makeSpellRegressionPartyMember("Daria", "Sorcerer", "PC07-01", 7));
    return seed;
}

inline Game::Party makeSpellRegressionParty(const RegressionGameData &gameData)
{
    Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setCharacterDollTable(&gameData.characterDollTable);
    party.setItemEnchantTables(
        &gameData.standardItemEnchantTable,
        &gameData.specialItemEnchantTable);
    party.setClassSkillTable(&gameData.classSkillTable);
    party.seed(createSpellRegressionPartySeed());
    return party;
}

class PartySpellTestWorldRuntime : public Game::IGameplayWorldRuntime
{
public:
    struct AppliedSpellToActor
    {
        size_t actorIndex = 0;
        uint32_t spellId = 0;
        uint32_t skillLevel = 0;
        Game::SkillMastery skillMastery = Game::SkillMastery::None;
        int damage = 0;
        float partyX = 0.0f;
        float partyY = 0.0f;
        float partyZ = 0.0f;
        uint32_t sourcePartyMemberIndex = 0;
    };

    struct FriendlySummonRequest
    {
        int16_t monsterId = 0;
        uint32_t count = 0;
        float durationSeconds = 0.0f;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
    };

    PartySpellTestWorldRuntime()
    {
        m_mapName = "spell_test.odm";
    }

    void bindParty(Game::Party *pParty)
    {
        m_pParty = pParty;
    }

    void bindEventRuntimeState(Game::EventRuntimeState *pEventRuntimeState)
    {
        m_pEventRuntimeState = pEventRuntimeState;
    }

    void bindGlobalEventProgram(const std::optional<Game::ScriptedEventProgram> *pGlobalEventProgram)
    {
        m_pGlobalEventProgram = pGlobalEventProgram;
    }

    size_t addActor(const Game::GameplayRuntimeActorState &actor)
    {
        m_actors.push_back(actor);
        return m_actors.size() - 1;
    }

    void setPartyPosition(float x, float y, float footZ)
    {
        m_partyX = x;
        m_partyY = y;
        m_partyFootZ = footZ;
    }

    void setCurrentHour(int hour)
    {
        m_currentHour = hour;
    }

    void setIndoorMap(bool indoorMap)
    {
        m_indoorMap = indoorMap;
        m_mapName = indoorMap ? "spell_test.blv" : "spell_test.odm";
    }

    const std::vector<Game::GameplayPartySpellProjectileRequest> &projectileRequests() const
    {
        return m_projectileRequests;
    }

    const std::vector<AppliedSpellToActor> &appliedSpellRequests() const
    {
        return m_appliedSpellRequests;
    }

    const std::vector<FriendlySummonRequest> &friendlySummonRequests() const
    {
        return m_friendlySummonRequests;
    }

    const std::vector<size_t> &radiusQueryActorIndices() const
    {
        return m_radiusQueryActorIndices;
    }

    bool syncSpellMovementStatesCalled() const
    {
        return m_syncSpellMovementStatesCalled;
    }

    bool partyJumpRequested() const
    {
        return m_partyJumpRequested;
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
        return m_gameMinutes;
    }

    int currentHour() const override
    {
        return m_currentHour;
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
        return 2;
    }

    void advanceGameMinutes(float minutes) override
    {
        m_gameMinutes += minutes;
    }

    int currentLocationReputation() const override
    {
        return m_currentLocationReputation;
    }

    void setCurrentLocationReputation(int reputation) override
    {
        m_currentLocationReputation = reputation;
    }

    Game::Party *party() override
    {
        return m_pParty;
    }

    const Game::Party *party() const override
    {
        return m_pParty;
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
        return m_partyFootZ;
    }

    void syncSpellMovementStatesFromPartyBuffs() override
    {
        m_syncSpellMovementStatesCalled = true;
    }

    void requestPartyJump() override
    {
        m_partyJumpRequested = true;
    }

    void setAlwaysRunEnabled(bool enabled) override
    {
        m_alwaysRunEnabled = enabled;
    }

    void updateWorldMovement(
        const Game::GameplayInputFrame &input,
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
        const Game::GameplayInputFrame &input,
        float deltaSeconds) override
    {
        (void)width;
        (void)height;
        (void)input;
        (void)deltaSeconds;
    }

    Game::GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const override
    {
        (void)width;
        (void)height;
        Game::GameplayWorldUiRenderState state = {};
        state.canRenderHudOverlays = true;
        return state;
    }

    bool requestTravelAutosave() override
    {
        return false;
    }

    void cancelPendingMapTransition() override
    {
    }

    bool executeNpcTopicEvent(uint16_t eventId, size_t &previousMessageCount) override
    {
        (void)previousMessageCount;

        Game::EventRuntime eventRuntime;
        const std::optional<Game::ScriptedEventProgram> emptyGlobalEventProgram = std::nullopt;
        const std::optional<Game::ScriptedEventProgram> &globalEventProgram =
            m_pGlobalEventProgram != nullptr ? *m_pGlobalEventProgram : emptyGlobalEventProgram;
        const bool executed = eventRuntime.executeEventById(
            std::nullopt,
            globalEventProgram,
            eventId,
            *eventRuntimeState(),
            m_pParty);

        if (executed && m_pParty != nullptr)
        {
            m_pParty->applyEventRuntimeState(*eventRuntimeState());
        }

        return executed;
    }

    Game::EventRuntimeState *eventRuntimeState() override
    {
        return m_pEventRuntimeState != nullptr ? m_pEventRuntimeState : &m_eventRuntimeState;
    }

    const Game::EventRuntimeState *eventRuntimeState() const override
    {
        return m_pEventRuntimeState != nullptr ? m_pEventRuntimeState : &m_eventRuntimeState;
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
        (void)fromX;
        (void)fromY;
        (void)fromZ;
        (void)toX;
        (void)toY;
        (void)toZ;

        if (m_pParty == nullptr || !tryApplyEventSpellBuffs(*m_pParty, spellId, skillLevel, skillMastery))
        {
            return false;
        }

        Game::EventRuntimeState::SpellFxRequest request = {};
        request.spellId = spellId;
        request.memberIndices.reserve(m_pParty->members().size());

        for (size_t memberIndex = 0; memberIndex < m_pParty->members().size(); ++memberIndex)
        {
            request.memberIndices.push_back(memberIndex);
        }

        eventRuntimeState()->spellFxRequests.push_back(std::move(request));
        return true;
    }

    size_t mapActorCount() const override
    {
        return m_actors.size();
    }

    bool actorRuntimeState(size_t actorIndex, Game::GameplayRuntimeActorState &state) const override
    {
        if (actorIndex >= m_actors.size())
        {
            return false;
        }

        state = m_actors[actorIndex];
        return true;
    }

    bool actorInspectState(
        size_t actorIndex,
        uint32_t animationTicks,
        Game::GameplayActorInspectState &state) const override
    {
        (void)actorIndex;
        (void)animationTicks;
        (void)state;
        return false;
    }

    std::optional<Game::GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const override
    {
        (void)actorId;
        return std::nullopt;
    }

    bool castPartySpellProjectile(const Game::GameplayPartySpellProjectileRequest &request) override
    {
        m_projectileRequests.push_back(request);
        return true;
    }

    bool applyPartySpellToActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        Game::SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex) override
    {
        if (actorIndex >= m_actors.size() || m_actors[actorIndex].isDead || m_actors[actorIndex].isInvisible)
        {
            return false;
        }

        AppliedSpellToActor request = {};
        request.actorIndex = actorIndex;
        request.spellId = spellId;
        request.skillLevel = skillLevel;
        request.skillMastery = skillMastery;
        request.damage = damage;
        request.partyX = partyX;
        request.partyY = partyY;
        request.partyZ = partyZ;
        request.sourcePartyMemberIndex = sourcePartyMemberIndex;
        m_appliedSpellRequests.push_back(request);
        return true;
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
        (void)requireLineOfSight;
        (void)sourceX;
        (void)sourceY;
        (void)sourceZ;

        m_radiusQueryActorIndices.clear();

        for (size_t actorIndex = 0; actorIndex < m_actors.size(); ++actorIndex)
        {
            const Game::GameplayRuntimeActorState &actor = m_actors[actorIndex];

            if (actor.isDead || actor.isInvisible)
            {
                continue;
            }

            const float dx = actor.preciseX - centerX;
            const float dy = actor.preciseY - centerY;
            const float dz = actor.preciseZ - centerZ;
            const float distanceSquared = dx * dx + dy * dy + dz * dz;

            if (distanceSquared <= radius * radius)
            {
                m_radiusQueryActorIndices.push_back(actorIndex);
            }
        }

        return m_radiusQueryActorIndices;
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
        return true;
    }

    bool summonFriendlyMonsterById(
        int16_t monsterId,
        uint32_t count,
        float durationSeconds,
        float x,
        float y,
        float z) override
    {
        m_friendlySummonRequests.push_back({
            .monsterId = monsterId,
            .count = count,
            .durationSeconds = durationSeconds,
            .x = x,
            .y = y,
            .z = z
        });

        for (uint32_t summonIndex = 0; summonIndex < count; ++summonIndex)
        {
            Game::GameplayRuntimeActorState actor = {};
            actor.monsterId = monsterId;
            actor.preciseX = x;
            actor.preciseY = y;
            actor.preciseZ = z;
            actor.radius = 32;
            actor.height = 96;
            actor.hostileToParty = false;
            actor.hasDetectedParty = false;
            m_actors.push_back(actor);
        }

        return true;
    }

    bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        Game::SkillMastery skillMastery,
        std::string &failureText) override
    {
        (void)casterMemberIndex;
        (void)skillLevel;
        (void)skillMastery;
        failureText.clear();
        return true;
    }

    bool canActivateWorldHit(
        const Game::GameplayWorldHit &hit,
        Game::GameplayInteractionMethod interactionMethod) const override
    {
        (void)hit;
        (void)interactionMethod;
        return false;
    }

    bool activateWorldHit(const Game::GameplayWorldHit &hit) override
    {
        (void)hit;
        return false;
    }

    std::optional<Game::GameplayPartyAttackActorFacts> partyAttackActorFacts(
        size_t actorIndex,
        bool visibleForFallback) const override
    {
        (void)actorIndex;
        (void)visibleForFallback;
        return std::nullopt;
    }

    std::vector<Game::GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const Game::GameplayPartyAttackFallbackQuery &query) const override
    {
        (void)query;
        return {};
    }

    bool applyPartyAttackMeleeDamage(size_t actorIndex, int damage, const Game::GameplayWorldPoint &source) override
    {
        (void)actorIndex;
        (void)damage;
        (void)source;
        return false;
    }

    bool spawnPartyAttackProjectile(const Game::GameplayPartyAttackProjectileRequest &request) override
    {
        (void)request;
        return false;
    }

    bool castPartyAttackSpell(const Game::GameplayPartyAttackSpellRequest &request) override
    {
        (void)request;
        return false;
    }

    void recordPartyAttackWorldResult(
        std::optional<size_t> actorIndex,
        bool attacked,
        bool actionPerformed) override
    {
        (void)actorIndex;
        (void)attacked;
        (void)actionPerformed;
    }

    bool worldInteractionReady() const override
    {
        return true;
    }

    bool worldInspectModeActive() const override
    {
        return false;
    }

    Game::GameplayWorldPickRequest buildWorldPickRequest(
        const Game::GameplayWorldPickRequestInput &input) const override
    {
        (void)input;
        return {};
    }

    std::optional<Game::GameplayHeldItemDropRequest> buildHeldItemDropRequest() const override
    {
        return std::nullopt;
    }

    Game::GameplayPartyAttackFrameInput buildPartyAttackFrameInput(
        const Game::GameplayWorldPickRequest &pickRequest) const override
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
        for (size_t actorIndex = 0; actorIndex < m_actors.size(); ++actorIndex)
        {
            const Game::GameplayRuntimeActorState &actor = m_actors[actorIndex];

            if (!actor.isDead && !actor.isInvisible && actor.hostileToParty)
            {
                return actorIndex;
            }
        }

        return std::nullopt;
    }

    std::optional<bx::Vec3> spellActionActorTargetPoint(size_t actorIndex) const override
    {
        if (actorIndex >= m_actors.size())
        {
            return std::nullopt;
        }

        const Game::GameplayRuntimeActorState &actor = m_actors[actorIndex];
        return bx::Vec3{
            actor.preciseX,
            actor.preciseY,
            actor.preciseZ + std::max(48.0f, static_cast<float>(actor.height) * 0.6f)};
    }

    std::optional<bx::Vec3> spellActionGroundTargetPoint(float screenX, float screenY) const override
    {
        (void)screenX;
        (void)screenY;
        return std::nullopt;
    }

    Game::GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        const Game::GameplayWorldPickRequest &request) override
    {
        (void)request;
        return {};
    }

    Game::GameplayWorldHit pickKeyboardInteractionTarget(
        const Game::GameplayWorldPickRequest &request) override
    {
        (void)request;
        return {};
    }

    Game::GameplayWorldHit pickHeldItemWorldTarget(const Game::GameplayWorldPickRequest &request) override
    {
        (void)request;
        return {};
    }

    Game::GameplayWorldHit pickMouseInteractionTarget(const Game::GameplayWorldPickRequest &request) override
    {
        (void)request;
        return {};
    }

    Game::GameplayWorldHoverCacheState worldHoverCacheState() const override
    {
        return {};
    }

    Game::GameplayHoverStatusPayload refreshWorldHover(
        const Game::GameplayWorldHoverRequest &request) override
    {
        (void)request;
        return {};
    }

    Game::GameplayHoverStatusPayload readCachedWorldHover() override
    {
        return {};
    }

    void clearWorldHover() override
    {
    }

    bool canUseHeldItemOnWorld(const Game::GameplayWorldHit &hit) const override
    {
        (void)hit;
        return false;
    }

    bool useHeldItemOnWorld(const Game::GameplayWorldHit &hit) override
    {
        (void)hit;
        return false;
    }

    void applyPendingSpellCastWorldEffects(const Game::PartySpellCastResult &castResult) override
    {
        (void)castResult;
    }

    bool dropHeldItemToWorld(const Game::GameplayHeldItemDropRequest &request) override
    {
        (void)request;
        return false;
    }

    bool tryGetGameplayMinimapState(Game::GameplayMinimapState &state) const override
    {
        (void)state;
        return false;
    }

    void collectGameplayMinimapLines(std::vector<Game::GameplayMinimapLineState> &lines) override
    {
        (void)lines;
    }

    void collectGameplayMinimapMarkers(std::vector<Game::GameplayMinimapMarkerState> &markers) const override
    {
        (void)markers;
    }

    Game::GameplayChestViewState *activeChestView() override
    {
        return nullptr;
    }

    const Game::GameplayChestViewState *activeChestView() const override
    {
        return nullptr;
    }

    void commitActiveChestView() override
    {
    }

    bool takeActiveChestItem(size_t itemIndex, Game::GameplayChestItemState &item) override
    {
        (void)itemIndex;
        (void)item;
        return false;
    }

    bool takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, Game::GameplayChestItemState &item) override
    {
        (void)gridX;
        (void)gridY;
        (void)item;
        return false;
    }

    bool tryPlaceActiveChestItemAt(
        const Game::GameplayChestItemState &item,
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

    Game::GameplayCorpseViewState *activeCorpseView() override
    {
        return nullptr;
    }

    const Game::GameplayCorpseViewState *activeCorpseView() const override
    {
        return nullptr;
    }

    void commitActiveCorpseView() override
    {
    }

    bool takeActiveCorpseItem(size_t itemIndex, Game::GameplayChestItemState &item) override
    {
        (void)itemIndex;
        (void)item;
        return false;
    }

    void closeActiveCorpseView() override
    {
    }

private:
    mutable std::vector<size_t> m_radiusQueryActorIndices;
    std::string m_mapName;
    bool m_indoorMap = false;
    Game::Party *m_pParty = nullptr;
    Game::EventRuntimeState m_eventRuntimeState = {};
    Game::EventRuntimeState *m_pEventRuntimeState = nullptr;
    const std::optional<Game::ScriptedEventProgram> *m_pGlobalEventProgram = nullptr;
    std::vector<Game::GameplayRuntimeActorState> m_actors;
    std::vector<Game::GameplayPartySpellProjectileRequest> m_projectileRequests;
    std::vector<AppliedSpellToActor> m_appliedSpellRequests;
    std::vector<FriendlySummonRequest> m_friendlySummonRequests;
    float m_gameMinutes = 0.0f;
    float m_partyX = 0.0f;
    float m_partyY = 0.0f;
    float m_partyFootZ = 0.0f;
    int m_currentHour = 12;
    int m_currentLocationReputation = 0;
    bool m_syncSpellMovementStatesCalled = false;
    bool m_partyJumpRequested = false;
    bool m_alwaysRunEnabled = false;
};
}
