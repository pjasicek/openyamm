#include "game/indoor/IndoorWorldRuntime.h"

#include "game/SpriteObjectDefs.h"
#include "game/events/EvtEnums.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <iostream>
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
    Party *pParty,
    std::optional<MapDeltaData> *pMapDeltaData,
    std::optional<EventRuntimeState> *pEventRuntimeState
)
{
    m_map = map;
    m_pMonsterTable = &monsterTable;
    m_pObjectTable = &objectTable;
    m_pItemTable = &itemTable;
    m_pParty = pParty;
    m_pMapDeltaData = pMapDeltaData;
    m_pEventRuntimeState = pEventRuntimeState;
}

float IndoorWorldRuntime::currentGameMinutes() const
{
    return m_gameMinutes;
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

void IndoorWorldRuntime::advanceGameMinutes(float minutes)
{
    if (minutes > 0.0f)
    {
        m_gameMinutes += minutes;
    }
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
        }
    }

    for (const auto &[chestId, clearMask] : pEventRuntimeState->chestClearMasks)
    {
        if (chestId < pMapDeltaData->chests.size())
        {
            pMapDeltaData->chests[chestId].flags &= ~static_cast<uint16_t>(clearMask);
        }
    }

    for (uint32_t openedChestId : pEventRuntimeState->openedChestIds)
    {
        if (openedChestId < pMapDeltaData->chests.size())
        {
            pMapDeltaData->chests[openedChestId].flags |= static_cast<uint16_t>(EvtChestFlag::Opened);
        }
    }
}

float IndoorWorldRuntime::gameMinutes() const
{
    return m_gameMinutes;
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
