#include "game/indoor/IndoorWorldRuntime.h"

#include "game/SpriteObjectDefs.h"
#include "game/events/EvtEnums.h"
#include "game/gameplay/ChestRuntime.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr uint32_t RawContainingItemSize = 0x24;

char tierLetterForSummonLevel(uint32_t level)
{
    const uint32_t clampedLevel = std::clamp(level, 1u, 3u);
    return static_cast<char>('A' + (clampedLevel - 1u));
}

std::string encounterPictureBase(const MapEncounterInfo &encounter)
{
    return encounter.pictureName.empty() ? encounter.monsterName : encounter.pictureName;
}

uint32_t defaultActorAttributes(bool hostileToParty)
{
    uint32_t attributes = static_cast<uint32_t>(EvtActorAttribute::Active)
        | static_cast<uint32_t>(EvtActorAttribute::FullAi);

    if (hostileToParty)
    {
        attributes |= static_cast<uint32_t>(EvtActorAttribute::Hostile);
    }

    return attributes;
}
}

void IndoorWorldRuntime::initialize(
    const MapStatsEntry &map,
    const MonsterTable &monsterTable,
    const ObjectTable &objectTable,
    const ItemTable &itemTable,
    const ChestTable &chestTable,
    Party *pParty,
    IndoorPartyRuntime *pPartyRuntime,
    std::optional<MapDeltaData> *pMapDeltaData,
    std::optional<EventRuntimeState> *pEventRuntimeState
)
{
    m_map = map;
    m_mapName = map.name;
    m_pMonsterTable = &monsterTable;
    m_pObjectTable = &objectTable;
    m_pItemTable = &itemTable;
    m_pChestTable = &chestTable;
    m_pParty = pParty;
    m_pPartyRuntime = pPartyRuntime;
    m_pMapDeltaData = pMapDeltaData;
    m_pEventRuntimeState = pEventRuntimeState;
    std::random_device randomDevice;
    const uint64_t timeSeed = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    m_sessionChestSeed = randomDevice() ^ uint32_t(timeSeed) ^ uint32_t(timeSeed >> 32);
    m_materializedChestViews.clear();
    m_activeChestView.reset();
    m_mapActorCorpseViews.clear();
    m_activeCorpseView.reset();
}

const std::string &IndoorWorldRuntime::mapName() const
{
    return m_mapName;
}

float IndoorWorldRuntime::currentGameMinutes() const
{
    return m_gameMinutes;
}

float IndoorWorldRuntime::gameMinutes() const
{
    return m_gameMinutes;
}

int IndoorWorldRuntime::currentHour() const
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(m_gameMinutes)));
    return (totalMinutes / 60) % 24;
}

void IndoorWorldRuntime::advanceGameMinutes(float minutes)
{
    if (minutes > 0.0f)
    {
        m_gameMinutes += minutes;
    }
}

int IndoorWorldRuntime::currentLocationReputation() const
{
    return m_currentLocationReputation;
}

void IndoorWorldRuntime::setCurrentLocationReputation(int reputation)
{
    m_currentLocationReputation = reputation;
}

Party *IndoorWorldRuntime::party()
{
    return m_pParty;
}

const Party *IndoorWorldRuntime::party() const
{
    return m_pParty;
}

float IndoorWorldRuntime::partyX() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyX() : 0.0f;
}

float IndoorWorldRuntime::partyY() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyY() : 0.0f;
}

float IndoorWorldRuntime::partyFootZ() const
{
    return m_pPartyRuntime != nullptr ? m_pPartyRuntime->partyFootZ() : 0.0f;
}

void IndoorWorldRuntime::syncSpellMovementStatesFromPartyBuffs()
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->syncSpellMovementStatesFromPartyBuffs();
    }
}

void IndoorWorldRuntime::requestPartyJump()
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->requestJump();
    }
}

void IndoorWorldRuntime::cancelPendingMapTransition()
{
}

bool IndoorWorldRuntime::castEventSpell(
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    int32_t fromX,
    int32_t fromY,
    int32_t fromZ,
    int32_t toX,
    int32_t toY,
    int32_t toZ
)
{
    (void)skillLevel;
    (void)skillMastery;
    (void)fromX;
    (void)fromY;
    (void)fromZ;
    (void)toX;
    (void)toY;
    (void)toZ;

    if (m_pEventRuntimeState == nullptr || !*m_pEventRuntimeState || m_pParty == nullptr)
    {
        return false;
    }

    EventRuntimeState::SpellFxRequest request = {};
    request.spellId = spellId;
    request.memberIndices.reserve(m_pParty->members().size());

    for (size_t memberIndex = 0; memberIndex < m_pParty->members().size(); ++memberIndex)
    {
        request.memberIndices.push_back(memberIndex);
    }

    (*m_pEventRuntimeState)->spellFxRequests.push_back(std::move(request));

    std::cout << "IndoorWorldRuntime: event spell " << spellId
              << " queued as FX only; projectile runtime support is pending\n";
    return true;
}

size_t IndoorWorldRuntime::mapActorCount() const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();
    return pMapDeltaData != nullptr ? pMapDeltaData->actors.size() : 0;
}

bool IndoorWorldRuntime::actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const bool isInvisible =
        (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0;
    const bool isAggressive =
        (actor.attributes & (static_cast<uint32_t>(EvtActorAttribute::Nearby)
            | static_cast<uint32_t>(EvtActorAttribute::Aggressor))) != 0;
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
    const bool hostileToParty =
        (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) != 0
        || (m_pMonsterTable != nullptr && resolvedMonsterId > 0 && m_pMonsterTable->isHostileToParty(resolvedMonsterId));

    state.preciseX = static_cast<float>(actor.x);
    state.preciseY = static_cast<float>(actor.y);
    state.preciseZ = static_cast<float>(actor.z);
    state.radius = actor.radius;
    state.height = actor.height;
    state.isDead = actor.hp <= 0;
    state.isInvisible = isInvisible;
    state.hostileToParty = hostileToParty;
    state.hasDetectedParty = hostileToParty && isAggressive;
    return true;
}

bool IndoorWorldRuntime::actorInspectState(
    size_t actorIndex,
    uint32_t animationTicks,
    GameplayActorInspectState &state) const
{
    (void)actorIndex;
    (void)animationTicks;
    state = {};
    return false;
}

bool IndoorWorldRuntime::castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request)
{
    (void)request;
    return false;
}

bool IndoorWorldRuntime::applyPartySpellToActor(
    size_t actorIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    int damage,
    float partyX,
    float partyY,
    float partyZ,
    uint32_t sourcePartyMemberIndex)
{
    (void)spellId;
    (void)skillLevel;
    (void)skillMastery;
    (void)partyX;
    (void)partyY;
    (void)partyZ;
    (void)sourcePartyMemberIndex;

    if (damage <= 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

    if (actor.hp <= 0
        || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return false;
    }

    const int previousHp = actor.hp;
    const int nextHp = std::clamp(
        previousHp - damage,
        static_cast<int>(std::numeric_limits<int16_t>::min()),
        previousHp);
    actor.hp = static_cast<int16_t>(nextHp);
    return actor.hp != previousHp;
}

std::vector<size_t> IndoorWorldRuntime::collectMapActorIndicesWithinRadius(
    float centerX,
    float centerY,
    float centerZ,
    float radius,
    bool requireLineOfSight,
    float sourceX,
    float sourceY,
    float sourceZ) const
{
    (void)sourceX;
    (void)sourceY;
    (void)sourceZ;

    std::vector<size_t> result;

    if (radius <= 0.0f)
    {
        return result;
    }

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return result;
    }

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible)
        {
            continue;
        }

        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
        const float targetZ =
            actorState.preciseZ + std::max(24.0f, static_cast<float>(actorState.height) * 0.7f);
        const float deltaX = actorState.preciseX - centerX;
        const float deltaY = actorState.preciseY - centerY;
        const float deltaZ = targetZ - centerZ;
        const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        const float edgeDistance = std::max(0.0f, distance - static_cast<float>(actor.radius));

        if (edgeDistance > radius || requireLineOfSight)
        {
            continue;
        }

        result.push_back(actorIndex);
    }

    return result;
}

bool IndoorWorldRuntime::spawnPartyFireSpikeTrap(
    uint32_t casterMemberIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    float x,
    float y,
    float z)
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

bool IndoorWorldRuntime::summonFriendlyMonsterById(
    int16_t monsterId,
    uint32_t count,
    float durationSeconds,
    float x,
    float y,
    float z)
{
    (void)durationSeconds;
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    const MonsterEntry *pMonsterEntry = m_pMonsterTable->findById(monsterId);

    if (pMonsterEntry == nullptr)
    {
        return false;
    }

    bool spawnedAny = false;

    for (uint32_t summonIndex = 0; summonIndex < count; ++summonIndex)
    {
        const float angleRadians = (Pi * 2.0f * summonIndex) / count;
        const float radius = 96.0f + 24.0f * float(summonIndex % 3u);
        MapDeltaActor actor = {};
        actor.name = pStats->name;
        actor.attributes = defaultActorAttributes(false);
        actor.hp = int16_t(std::clamp(pStats->hitPoints, 0, 32767));
        actor.hostilityType = 0;
        actor.monsterInfoId = int16_t(pStats->id);
        actor.monsterId = int16_t(pStats->id);
        actor.radius = pMonsterEntry->radius;
        actor.height = pMonsterEntry->height;
        actor.moveSpeed = pMonsterEntry->movementSpeed;
        actor.x = int(std::lround(x + std::cos(angleRadians) * radius));
        actor.y = int(std::lround(y + std::sin(angleRadians) * radius));
        actor.z = int(std::lround(z));
        actor.group = 999u;
        actor.ally = 999u;
        pMapDeltaData->actors.push_back(std::move(actor));
        spawnedAny = true;
    }

    return spawnedAny;
}

void IndoorWorldRuntime::triggerGameplayScreenOverlay(
    uint32_t colorAbgr,
    float durationSeconds,
    float peakAlpha)
{
    (void)colorAbgr;
    (void)durationSeconds;
    (void)peakAlpha;
}

bool IndoorWorldRuntime::tryStartArmageddon(
    size_t casterMemberIndex,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    std::string &failureText)
{
    (void)casterMemberIndex;
    (void)skillLevel;
    (void)skillMastery;
    failureText = "Spell failed";
    return false;
}

bool IndoorWorldRuntime::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    state = {};
    return false;
}

void IndoorWorldRuntime::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    markers.clear();
}

const IndoorWorldRuntime::ChestViewState *IndoorWorldRuntime::activeChestView() const
{
    return m_activeChestView ? &*m_activeChestView : nullptr;
}

bool IndoorWorldRuntime::identifyActiveChestItem(size_t itemIndex, std::string &statusText)
{
    statusText.clear();

    if (!m_activeChestView || itemIndex >= m_activeChestView->items.size() || m_pItemTable == nullptr)
    {
        return false;
    }

    ChestItemState &chestItem = m_activeChestView->items[itemIndex];

    if (chestItem.isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(chestItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (chestItem.item.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = "Already identified.";
        return false;
    }

    chestItem.item.identified = true;
    statusText = "Identified " + ItemRuntime::displayName(chestItem.item, *pItemDefinition) + ".";
    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

bool IndoorWorldRuntime::tryIdentifyActiveChestItem(
    size_t itemIndex,
    const Character &inspector,
    std::string &statusText)
{
    statusText.clear();

    if (!m_activeChestView || itemIndex >= m_activeChestView->items.size() || m_pItemTable == nullptr)
    {
        return false;
    }

    ChestItemState &chestItem = m_activeChestView->items[itemIndex];

    if (chestItem.isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(chestItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (chestItem.item.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = "Already identified.";
        return false;
    }

    if (!ItemRuntime::canCharacterIdentifyItem(inspector, *pItemDefinition))
    {
        statusText = "Not skilled enough.";
        return false;
    }

    chestItem.item.identified = true;
    statusText = "Identified " + ItemRuntime::displayName(chestItem.item, *pItemDefinition) + ".";
    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

bool IndoorWorldRuntime::tryRepairActiveChestItem(size_t itemIndex, const Character &inspector, std::string &statusText)
{
    statusText.clear();

    if (!m_activeChestView || itemIndex >= m_activeChestView->items.size() || m_pItemTable == nullptr)
    {
        return false;
    }

    ChestItemState &chestItem = m_activeChestView->items[itemIndex];

    if (chestItem.isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(chestItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (!chestItem.item.broken)
    {
        statusText = "Nothing to repair.";
        return false;
    }

    if (!ItemRuntime::canCharacterRepairItem(inspector, *pItemDefinition))
    {
        statusText = "Not skilled enough.";
        return false;
    }

    chestItem.item.broken = false;
    chestItem.item.identified = true;
    statusText = "Repaired " + ItemRuntime::displayName(chestItem.item, *pItemDefinition) + ".";
    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

bool IndoorWorldRuntime::takeActiveChestItem(size_t itemIndex, ChestItemState &item)
{
    if (!m_activeChestView || !takeChestItem(*m_activeChestView, itemIndex, item))
    {
        return false;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

bool IndoorWorldRuntime::takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, ChestItemState &item)
{
    if (!m_activeChestView || !takeChestItemAt(*m_activeChestView, gridX, gridY, item))
    {
        return false;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

bool IndoorWorldRuntime::tryPlaceActiveChestItemAt(const ChestItemState &item, uint8_t gridX, uint8_t gridY)
{
    if (!m_activeChestView || !tryPlaceChestItemAt(*m_activeChestView, item, gridX, gridY))
    {
        return false;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }

    return true;
}

void IndoorWorldRuntime::closeActiveChestView()
{
    m_activeChestView.reset();
}

const IndoorWorldRuntime::CorpseViewState *IndoorWorldRuntime::activeCorpseView() const
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

bool IndoorWorldRuntime::identifyActiveCorpseItem(size_t itemIndex, std::string &statusText)
{
    statusText.clear();

    if (!m_activeCorpseView || itemIndex >= m_activeCorpseView->items.size() || m_pItemTable == nullptr)
    {
        return false;
    }

    ChestItemState &corpseItem = m_activeCorpseView->items[itemIndex];

    if (corpseItem.isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(corpseItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (corpseItem.item.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = "Already identified.";
        return false;
    }

    corpseItem.item.identified = true;
    statusText = "Identified " + ItemRuntime::displayName(corpseItem.item, *pItemDefinition) + ".";

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }

    return true;
}

bool IndoorWorldRuntime::tryIdentifyActiveCorpseItem(
    size_t itemIndex,
    const Character &inspector,
    std::string &statusText)
{
    statusText.clear();

    if (!m_activeCorpseView || itemIndex >= m_activeCorpseView->items.size() || m_pItemTable == nullptr)
    {
        return false;
    }

    ChestItemState &corpseItem = m_activeCorpseView->items[itemIndex];

    if (corpseItem.isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(corpseItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (corpseItem.item.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = "Already identified.";
        return false;
    }

    if (!ItemRuntime::canCharacterIdentifyItem(inspector, *pItemDefinition))
    {
        statusText = "Not skilled enough.";
        return false;
    }

    corpseItem.item.identified = true;
    statusText = "Identified " + ItemRuntime::displayName(corpseItem.item, *pItemDefinition) + ".";

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }

    return true;
}

bool IndoorWorldRuntime::tryRepairActiveCorpseItem(
    size_t itemIndex,
    const Character &inspector,
    std::string &statusText)
{
    statusText.clear();

    if (!m_activeCorpseView || itemIndex >= m_activeCorpseView->items.size() || m_pItemTable == nullptr)
    {
        return false;
    }

    ChestItemState &corpseItem = m_activeCorpseView->items[itemIndex];

    if (corpseItem.isGold)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(corpseItem.item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = "Unavailable.";
        return false;
    }

    if (!corpseItem.item.broken)
    {
        statusText = "Nothing to repair.";
        return false;
    }

    if (!ItemRuntime::canCharacterRepairItem(inspector, *pItemDefinition))
    {
        statusText = "Not skilled enough.";
        return false;
    }

    corpseItem.item.broken = false;
    corpseItem.item.identified = true;
    statusText = "Repaired " + ItemRuntime::displayName(corpseItem.item, *pItemDefinition) + ".";

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }

    return true;
}

bool IndoorWorldRuntime::openMapActorCorpseView(size_t actorIndex)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size() || m_pMonsterTable == nullptr)
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];

    if (actor.hp > 0 || (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0)
    {
        return false;
    }

    if (actorIndex >= m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews.resize(actorIndex + 1);
    }

    if (!m_mapActorCorpseViews[actorIndex].has_value())
    {
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(actor.monsterId);

        if (pStats == nullptr)
        {
            return false;
        }

        const std::string &title = actor.name.empty() ? pStats->name : actor.name;
        CorpseViewState corpse = buildMonsterCorpseView(title, pStats->loot, m_pItemTable, m_pParty);

        if (corpse.items.empty())
        {
            return false;
        }

        corpse.fromSummonedMonster = false;
        corpse.sourceIndex = uint32_t(actorIndex);
        m_mapActorCorpseViews[actorIndex] = std::move(corpse);
    }

    m_activeCorpseView = *m_mapActorCorpseViews[actorIndex];
    return true;
}

bool IndoorWorldRuntime::takeActiveCorpseItem(size_t itemIndex, ChestItemState &item)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (!m_activeCorpseView || pMapDeltaData == nullptr || itemIndex >= m_activeCorpseView->items.size())
    {
        return false;
    }

    item = m_activeCorpseView->items[itemIndex];
    m_activeCorpseView->items.erase(m_activeCorpseView->items.begin() + itemIndex);

    if (m_activeCorpseView->items.empty())
    {
        if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
        {
            m_mapActorCorpseViews[m_activeCorpseView->sourceIndex].reset();
        }

        if (m_activeCorpseView->sourceIndex < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[m_activeCorpseView->sourceIndex].attributes
                |= static_cast<uint32_t>(EvtActorAttribute::Invisible);
        }

        m_activeCorpseView.reset();
        return true;
    }

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }

    return true;
}

void IndoorWorldRuntime::closeActiveCorpseView()
{
    m_activeCorpseView.reset();
}

bool IndoorWorldRuntime::summonMonsters(
    uint32_t typeIndexInMapStats,
    uint32_t level,
    uint32_t count,
    int32_t x,
    int32_t y,
    int32_t z,
    uint32_t group,
    uint32_t uniqueNameId
)
{
    if (m_pMonsterTable == nullptr || count == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = resolveEncounterStats(typeIndexInMapStats, level);

    if (pStats == nullptr)
    {
        return false;
    }

    const MonsterEntry *pMonsterEntry = m_pMonsterTable->findById(static_cast<int16_t>(pStats->id));

    if (pMonsterEntry == nullptr)
    {
        return false;
    }

    const bool hostileToParty = m_pMonsterTable->isHostileToParty(static_cast<int16_t>(pStats->id));
    bool spawnedAny = false;

    for (uint32_t summonIndex = 0; summonIndex < count; ++summonIndex)
    {
        const float angleRadians = (Pi * 2.0f * static_cast<float>(summonIndex)) / static_cast<float>(count);
        const float radius = 96.0f + 24.0f * static_cast<float>(summonIndex % 3u);
        MapDeltaActor actor = {};
        actor.name = pStats->name;
        actor.attributes = defaultActorAttributes(hostileToParty);
        actor.hp = static_cast<int16_t>(std::clamp(pStats->hitPoints, 0, 32767));
        actor.hostilityType = static_cast<uint8_t>(std::clamp(pStats->hostility, 0, 255));
        actor.monsterInfoId = static_cast<int16_t>(pStats->id);
        actor.monsterId = static_cast<int16_t>(pStats->id);
        actor.radius = pMonsterEntry->radius;
        actor.height = pMonsterEntry->height;
        actor.moveSpeed = pMonsterEntry->movementSpeed;
        actor.x = x + static_cast<int>(std::lround(std::cos(angleRadians) * radius));
        actor.y = y + static_cast<int>(std::lround(std::sin(angleRadians) * radius));
        actor.z = z;
        actor.group = group;
        actor.ally = hostileToParty ? 0u : 999u;
        actor.uniqueNameIndex = static_cast<int32_t>(uniqueNameId);
        pMapDeltaData->actors.push_back(std::move(actor));
        spawnedAny = true;
    }

    return spawnedAny;
}

bool IndoorWorldRuntime::summonEventItem(
    uint32_t itemId,
    int32_t x,
    int32_t y,
    int32_t z,
    int32_t speed,
    uint32_t count,
    bool randomRotate
)
{
    if (m_pObjectTable == nullptr || count == 0 || itemId == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable != nullptr ? m_pItemTable->get(itemId) : nullptr;
    std::optional<uint16_t> objectDescriptionId =
        m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(itemId));

    if (!objectDescriptionId && pItemDefinition != nullptr)
    {
        objectDescriptionId =
            m_pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(pItemDefinition->spriteIndex));
    }

    if (!objectDescriptionId)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = m_pObjectTable->get(*objectDescriptionId);

    if (pObjectEntry == nullptr)
    {
        return false;
    }

    std::mt19937 rng(itemId * 2654435761u + count * 977u);
    bool spawnedAny = false;

    for (uint32_t itemIndex = 0; itemIndex < count; ++itemIndex)
    {
        MapDeltaSpriteObject spriteObject = {};
        spriteObject.spriteId = pObjectEntry->spriteId;
        spriteObject.objectDescriptionId = *objectDescriptionId;
        spriteObject.x = x;
        spriteObject.y = y;
        spriteObject.z = z;
        spriteObject.attributes = SpriteAttrTemporary;
        spriteObject.temporaryLifetime = pObjectEntry->lifetimeTicks;
        spriteObject.initialX = x;
        spriteObject.initialY = y;
        spriteObject.initialZ = z;
        spriteObject.rawContainingItem.assign(RawContainingItemSize, 0);

        if (pItemDefinition != nullptr)
        {
            const int32_t rawItemId = static_cast<int32_t>(pItemDefinition->itemId);
            std::memcpy(spriteObject.rawContainingItem.data(), &rawItemId, sizeof(rawItemId));
        }

        if (speed > 0)
        {
            const float angleRadians = randomRotate
                ? std::uniform_real_distribution<float>(0.0f, Pi * 2.0f)(rng)
                : 0.0f;
            spriteObject.velocityX = static_cast<int16_t>(std::lround(std::cos(angleRadians) * speed));
            spriteObject.velocityY = static_cast<int16_t>(std::lround(std::sin(angleRadians) * speed));
        }

        pMapDeltaData->spriteObjects.push_back(std::move(spriteObject));
        spawnedAny = true;
    }

    return spawnedAny;
}

bool IndoorWorldRuntime::checkMonstersKilled(
    uint32_t checkType,
    uint32_t id,
    uint32_t count,
    bool invisibleAsDead
) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    int totalActors = 0;
    int defeatedActors = 0;

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
        bool matches = false;

        switch (static_cast<EvtActorKillCheck>(checkType))
        {
            case EvtActorKillCheck::Any:
                matches = true;
                break;

            case EvtActorKillCheck::Group:
                matches = actor.group == id;
                break;

            case EvtActorKillCheck::MonsterId:
                matches = actor.monsterId == static_cast<int16_t>(id);
                break;

            case EvtActorKillCheck::ActorIdOe:
            case EvtActorKillCheck::ActorIdMm8:
                matches = actorIndex == id;
                break;
        }

        if (!matches)
        {
            continue;
        }

        ++totalActors;
        const bool isInvisible =
            (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Invisible)) != 0;

        if (actor.hp <= 0 || (invisibleAsDead && isInvisible))
        {
            ++defeatedActors;
        }
    }

    if (count > 0)
    {
        return defeatedActors >= static_cast<int>(count);
    }

    return totalActors == defeatedActors;
}

void IndoorWorldRuntime::applyEventRuntimeState()
{
    MapDeltaData *pMapDeltaData = mapDeltaData();
    EventRuntimeState *pEventRuntimeState = eventRuntimeState();

    if (pMapDeltaData == nullptr || pEventRuntimeState == nullptr)
    {
        return;
    }

    pMapDeltaData->eventVariables.mapVars = pEventRuntimeState->mapVars;

    for (const auto &[actorId, setMask] : pEventRuntimeState->actorSetMasks)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[actorId].attributes |= setMask;
        }
    }

    for (const auto &[actorId, clearMask] : pEventRuntimeState->actorClearMasks)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[actorId].attributes &= ~clearMask;
        }
    }

    for (const auto &[actorId, groupId] : pEventRuntimeState->actorIdGroupOverrides)
    {
        if (actorId < pMapDeltaData->actors.size())
        {
            pMapDeltaData->actors[actorId].group = groupId;
        }
    }

    for (const auto &[fromGroupId, toGroupId] : pEventRuntimeState->actorGroupOverrides)
    {
        for (MapDeltaActor &actor : pMapDeltaData->actors)
        {
            if (actor.group == fromGroupId)
            {
                actor.group = toGroupId;
            }
        }
    }

    for (const auto &[groupId, allyId] : pEventRuntimeState->actorGroupAllyOverrides)
    {
        for (MapDeltaActor &actor : pMapDeltaData->actors)
        {
            if (actor.group == groupId)
            {
                actor.ally = allyId;
            }
        }
    }

    for (const auto &[groupId, setMask] : pEventRuntimeState->actorGroupSetMasks)
    {
        for (MapDeltaActor &actor : pMapDeltaData->actors)
        {
            if (actor.group == groupId)
            {
                actor.attributes |= setMask;
            }
        }
    }

    for (const auto &[groupId, clearMask] : pEventRuntimeState->actorGroupClearMasks)
    {
        for (MapDeltaActor &actor : pMapDeltaData->actors)
        {
            if (actor.group == groupId)
            {
                actor.attributes &= ~clearMask;
            }
        }
    }

    for (const auto &[chestId, setMask] : pEventRuntimeState->chestSetMasks)
    {
        if (chestId < pMapDeltaData->chests.size())
        {
            pMapDeltaData->chests[chestId].flags |= static_cast<uint16_t>(setMask);

            if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
            {
                m_materializedChestViews[chestId]->flags = pMapDeltaData->chests[chestId].flags;
            }

            if (m_activeChestView && m_activeChestView->chestId == chestId)
            {
                m_activeChestView->flags = pMapDeltaData->chests[chestId].flags;
            }
        }
    }

    for (const auto &[chestId, clearMask] : pEventRuntimeState->chestClearMasks)
    {
        if (chestId < pMapDeltaData->chests.size())
        {
            pMapDeltaData->chests[chestId].flags &= ~static_cast<uint16_t>(clearMask);

            if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
            {
                m_materializedChestViews[chestId]->flags = pMapDeltaData->chests[chestId].flags;
            }

            if (m_activeChestView && m_activeChestView->chestId == chestId)
            {
                m_activeChestView->flags = pMapDeltaData->chests[chestId].flags;
            }
        }
    }

    for (uint32_t openedChestId : pEventRuntimeState->openedChestIds)
    {
        if (openedChestId < pMapDeltaData->chests.size())
        {
            pMapDeltaData->chests[openedChestId].flags |= static_cast<uint16_t>(EvtChestFlag::Opened);
            activateChestView(openedChestId);
        }
    }
}

const MapDeltaData *IndoorWorldRuntime::mapDeltaData() const
{
    if (m_pMapDeltaData == nullptr || !*m_pMapDeltaData)
    {
        return nullptr;
    }

    return &**m_pMapDeltaData;
}

MapDeltaData *IndoorWorldRuntime::mapDeltaData()
{
    if (m_pMapDeltaData == nullptr || !*m_pMapDeltaData)
    {
        return nullptr;
    }

    return &**m_pMapDeltaData;
}

EventRuntimeState *IndoorWorldRuntime::eventRuntimeState()
{
    if (m_pEventRuntimeState == nullptr || !*m_pEventRuntimeState)
    {
        return nullptr;
    }

    return &**m_pEventRuntimeState;
}

const EventRuntimeState *IndoorWorldRuntime::eventRuntimeState() const
{
    if (m_pEventRuntimeState == nullptr || !*m_pEventRuntimeState)
    {
        return nullptr;
    }

    return &**m_pEventRuntimeState;
}

IndoorWorldRuntime::Snapshot IndoorWorldRuntime::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.gameMinutes = m_gameMinutes;
    snapshot.currentLocationReputation = m_currentLocationReputation;
    snapshot.sessionChestSeed = m_sessionChestSeed;
    snapshot.materializedChestViews = m_materializedChestViews;
    snapshot.activeChestView = m_activeChestView;
    snapshot.mapActorCorpseViews = m_mapActorCorpseViews;
    snapshot.activeCorpseView = m_activeCorpseView;
    return snapshot;
}

void IndoorWorldRuntime::restoreSnapshot(const Snapshot &snapshot)
{
    m_gameMinutes = snapshot.gameMinutes;
    m_currentLocationReputation = snapshot.currentLocationReputation;
    m_sessionChestSeed = snapshot.sessionChestSeed;
    m_materializedChestViews = snapshot.materializedChestViews;
    m_activeChestView = snapshot.activeChestView;
    m_mapActorCorpseViews = snapshot.mapActorCorpseViews;
    m_activeCorpseView = snapshot.activeCorpseView;
}

IndoorWorldRuntime::ChestViewState IndoorWorldRuntime::buildChestView(uint32_t chestId) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || chestId >= pMapDeltaData->chests.size())
    {
        return {};
    }

    return buildMaterializedChestView(
        chestId,
        pMapDeltaData->chests[chestId],
        m_map ? m_map->treasureLevel : 0,
        m_map ? m_map->id : 0,
        m_sessionChestSeed,
        m_pChestTable,
        m_pItemTable,
        m_pParty);
}

void IndoorWorldRuntime::activateChestView(uint32_t chestId)
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || chestId >= pMapDeltaData->chests.size())
    {
        return;
    }

    if (chestId >= m_materializedChestViews.size())
    {
        m_materializedChestViews.resize(chestId + 1);
    }

    if (!m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = buildChestView(chestId);
    }

    m_activeChestView = *m_materializedChestViews[chestId];
}

const MapEncounterInfo *IndoorWorldRuntime::encounterInfo(uint32_t typeIndexInMapStats) const
{
    if (!m_map || typeIndexInMapStats < 1 || typeIndexInMapStats > 3)
    {
        return nullptr;
    }

    static constexpr std::array<const MapEncounterInfo MapStatsEntry::*, 3> EncounterMembers = {{
        &MapStatsEntry::encounter1,
        &MapStatsEntry::encounter2,
        &MapStatsEntry::encounter3
    }};

    const MapStatsEntry &map = *m_map;
    return &(map.*EncounterMembers[typeIndexInMapStats - 1]);
}

const MonsterTable::MonsterStatsEntry *IndoorWorldRuntime::resolveEncounterStats(
    uint32_t typeIndexInMapStats,
    uint32_t level
) const
{
    if (m_pMonsterTable == nullptr)
    {
        return nullptr;
    }

    const MapEncounterInfo *pEncounter = encounterInfo(typeIndexInMapStats);

    if (pEncounter == nullptr)
    {
        return nullptr;
    }

    std::string pictureName = encounterPictureBase(*pEncounter);

    if (pictureName.empty())
    {
        return nullptr;
    }

    pictureName += " ";
    pictureName.push_back(tierLetterForSummonLevel(level));
    return m_pMonsterTable->findStatsByPictureName(pictureName);
}
}
