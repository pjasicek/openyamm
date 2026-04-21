#include "game/indoor/IndoorWorldRuntime.h"

#include "game/SpriteObjectDefs.h"
#include "game/audio/SoundIds.h"
#include "game/data/ActorNameResolver.h"
#include "game/events/EvtEnums.h"
#include "game/StringUtils.h"
#include "game/gameplay/ChestRuntime.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/indoor/IndoorDebugRenderer.h"
#include "game/indoor/IndoorGameView.h"
#include "game/indoor/IndoorPartyRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/SpriteTables.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr uint32_t RawContainingItemSize = 0x24;
constexpr float IndoorDroppedItemForwardOffset = 64.0f;
constexpr float IndoorDroppedItemHeightOffset = 32.0f;
constexpr float IndoorMinimapWorldHalfExtent = 32768.0f;
constexpr float IndoorMinimapWorldExtent = IndoorMinimapWorldHalfExtent * 2.0f;

float indoorMinimapU(float x)
{
    return std::clamp((x + IndoorMinimapWorldHalfExtent) / IndoorMinimapWorldExtent, 0.0f, 1.0f);
}

float indoorMinimapV(float y)
{
    return std::clamp((IndoorMinimapWorldHalfExtent - y) / IndoorMinimapWorldExtent, 0.0f, 1.0f);
}

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

bool hasActiveActorSpellEffectOverride(const GameplayActorSpellEffectState &state)
{
    return state.slowRemainingSeconds > 0.0f
        || state.stunRemainingSeconds > 0.0f
        || state.paralyzeRemainingSeconds > 0.0f
        || state.fearRemainingSeconds > 0.0f
        || state.blindRemainingSeconds > 0.0f
        || state.controlRemainingSeconds > 0.0f
        || state.controlMode != GameplayActorControlMode::None
        || state.shrinkRemainingSeconds > 0.0f
        || state.darkGraspRemainingSeconds > 0.0f
        || state.slowMoveMultiplier != 1.0f
        || state.slowRecoveryMultiplier != 1.0f
        || state.shrinkDamageMultiplier != 1.0f
        || state.shrinkArmorClassMultiplier != 1.0f;
}

bool defaultActorHostileToParty(const MapDeltaActor &actor, const MonsterTable *pMonsterTable)
{
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;

    return (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) != 0
        || (pMonsterTable != nullptr
            && resolvedMonsterId > 0
            && pMonsterTable->isHostileToParty(resolvedMonsterId));
}

SkillMastery normalizeRuntimeSkillMastery(uint32_t rawSkillMastery)
{
    if (rawSkillMastery > static_cast<uint32_t>(SkillMastery::Grandmaster))
    {
        return SkillMastery::None;
    }

    return static_cast<SkillMastery>(rawSkillMastery);
}

std::optional<size_t> findActorOnAttackLine(
    const IndoorWorldRuntime &runtime,
    const GameplayWorldPoint &source,
    const GameplayWorldPoint &target)
{
    const float segmentX = target.x - source.x;
    const float segmentY = target.y - source.y;
    const float segmentZ = target.z - source.z;
    const float segmentLengthSquared =
        segmentX * segmentX + segmentY * segmentY + segmentZ * segmentZ;

    if (segmentLengthSquared <= 0.0f)
    {
        return std::nullopt;
    }

    std::optional<size_t> bestActorIndex;
    float bestLineProgress = std::numeric_limits<float>::max();
    float bestDistanceSquared = std::numeric_limits<float>::max();

    for (size_t actorIndex = 0; actorIndex < runtime.mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!runtime.actorRuntimeState(actorIndex, actorState)
            || actorState.isDead
            || actorState.isInvisible)
        {
            continue;
        }

        const float targetZ =
            actorState.preciseZ + std::max(24.0f, static_cast<float>(actorState.height) * 0.6f);
        const float actorX = actorState.preciseX - source.x;
        const float actorY = actorState.preciseY - source.y;
        const float actorZ = targetZ - source.z;
        const float lineProgress =
            std::clamp(
                (actorX * segmentX + actorY * segmentY + actorZ * segmentZ) / segmentLengthSquared,
                0.0f,
                1.0f);
        const float closestX = source.x + segmentX * lineProgress;
        const float closestY = source.y + segmentY * lineProgress;
        const float closestZ = source.z + segmentZ * lineProgress;
        const float deltaX = actorState.preciseX - closestX;
        const float deltaY = actorState.preciseY - closestY;
        const float deltaZ = targetZ - closestZ;
        const float distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
        const float hitRadius = std::max(32.0f, static_cast<float>(actorState.radius));

        if (distanceSquared > hitRadius * hitRadius)
        {
            continue;
        }

        if (!bestActorIndex
            || lineProgress < bestLineProgress
            || (lineProgress == bestLineProgress && distanceSquared < bestDistanceSquared))
        {
            bestActorIndex = actorIndex;
            bestLineProgress = lineProgress;
            bestDistanceSquared = distanceSquared;
        }
    }

    return bestActorIndex;
}

const MonsterEntry *resolveRuntimeMonsterEntry(const MonsterTable &monsterTable, const MapDeltaActor &actor)
{
    const MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
        monsterTable.findDisplayEntryById(actor.monsterInfoId);

    if (pDisplayEntry != nullptr)
    {
        const MonsterEntry *pMonsterEntry = monsterTable.findByInternalName(pDisplayEntry->pictureName);

        if (pMonsterEntry != nullptr)
        {
            return pMonsterEntry;
        }
    }

    return monsterTable.findById(actor.monsterId);
}

uint16_t resolveRuntimeActorSpriteFrameIndex(
    const SpriteFrameTable &spriteFrameTable,
    const MapDeltaActor &actor,
    const MonsterEntry *pMonsterEntry)
{
    if (pMonsterEntry != nullptr)
    {
        for (const std::string &spriteName : pMonsterEntry->spriteNames)
        {
            if (spriteName.empty())
            {
                continue;
            }

            const std::optional<uint16_t> frameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);

            if (frameIndex)
            {
                return *frameIndex;
            }
        }
    }

    for (uint16_t spriteId : actor.spriteIds)
    {
        if (spriteId != 0)
        {
            return spriteId;
        }
    }

    return 0;
}

void writeRawItemUInt16(std::vector<uint8_t> &bytes, size_t offset, uint16_t value)
{
    if (bytes.size() >= offset + sizeof(value))
    {
        std::memcpy(bytes.data() + offset, &value, sizeof(value));
    }
}

void writeRawItemUInt32(std::vector<uint8_t> &bytes, size_t offset, uint32_t value)
{
    if (bytes.size() >= offset + sizeof(value))
    {
        std::memcpy(bytes.data() + offset, &value, sizeof(value));
    }
}

bool readRawItemUInt16(const std::vector<uint8_t> &bytes, size_t offset, uint16_t &value)
{
    if (bytes.size() < offset + sizeof(value))
    {
        return false;
    }

    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return true;
}

bool readRawItemUInt32(const std::vector<uint8_t> &bytes, size_t offset, uint32_t &value)
{
    if (bytes.size() < offset + sizeof(value))
    {
        return false;
    }

    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return true;
}

void writeIndoorHeldItemPayload(std::vector<uint8_t> &bytes, const InventoryItem &item)
{
    bytes.assign(RawContainingItemSize, 0);
    writeRawItemUInt32(bytes, 0x00, item.objectDescriptionId);
    writeRawItemUInt32(bytes, 0x04, item.quantity);

    uint8_t flags = 0;
    flags |= item.identified ? 0x01 : 0x00;
    flags |= item.broken ? 0x02 : 0x00;
    flags |= item.stolen ? 0x04 : 0x00;

    if (bytes.size() > 0x08)
    {
        bytes[0x08] = flags;
    }

    writeRawItemUInt16(bytes, 0x10, item.standardEnchantId);
    writeRawItemUInt16(bytes, 0x12, item.standardEnchantPower);
    writeRawItemUInt16(bytes, 0x14, item.specialEnchantId);
    writeRawItemUInt16(bytes, 0x16, item.artifactId);

    if (bytes.size() > 0x18)
    {
        bytes[0x18] = static_cast<uint8_t>(item.rarity);
    }

    if (bytes.size() >= 0x20)
    {
        std::memcpy(bytes.data() + 0x1c, &item.temporaryBonusRemainingSeconds, sizeof(float));
    }
}

bool readIndoorHeldItemPayload(
    const std::vector<uint8_t> &bytes,
    const ItemTable *pItemTable,
    InventoryItem &item)
{
    uint32_t itemId = 0;

    if (!readRawItemUInt32(bytes, 0x00, itemId) || itemId == 0)
    {
        return false;
    }

    item = {};
    item.objectDescriptionId = itemId;

    uint32_t quantity = 0;

    if (readRawItemUInt32(bytes, 0x04, quantity) && quantity > 0)
    {
        item.quantity = quantity;
    }

    if (bytes.size() > 0x08)
    {
        item.identified = (bytes[0x08] & 0x01) != 0;
        item.broken = (bytes[0x08] & 0x02) != 0;
        item.stolen = (bytes[0x08] & 0x04) != 0;
    }

    readRawItemUInt16(bytes, 0x10, item.standardEnchantId);
    readRawItemUInt16(bytes, 0x12, item.standardEnchantPower);
    readRawItemUInt16(bytes, 0x14, item.specialEnchantId);
    readRawItemUInt16(bytes, 0x16, item.artifactId);

    if (bytes.size() > 0x18 && bytes[0x18] <= static_cast<uint8_t>(ItemRarity::Special))
    {
        item.rarity = static_cast<ItemRarity>(bytes[0x18]);
    }

    if (bytes.size() >= 0x20)
    {
        std::memcpy(&item.temporaryBonusRemainingSeconds, bytes.data() + 0x1c, sizeof(float));
    }

    const ItemDefinition *pItemDefinition = pItemTable != nullptr ? pItemTable->get(itemId) : nullptr;

    if (pItemDefinition != nullptr)
    {
        item.width = pItemDefinition->inventoryWidth;
        item.height = pItemDefinition->inventoryHeight;
    }

    return true;
}

std::optional<uint16_t> resolveIndoorItemObjectDescriptionId(
    const InventoryItem &item,
    const ItemTable *pItemTable,
    const ObjectTable *pObjectTable)
{
    if (item.objectDescriptionId == 0 || pItemTable == nullptr || pObjectTable == nullptr)
    {
        return std::nullopt;
    }

    const ItemDefinition *pItemDefinition = pItemTable->get(item.objectDescriptionId);

    if (pItemDefinition == nullptr || pItemDefinition->spriteIndex == 0)
    {
        return std::nullopt;
    }

    return pObjectTable->findDescriptionIdByObjectId(static_cast<int16_t>(pItemDefinition->spriteIndex));
}

uint16_t yawAngleFromRadians(float yawRadians)
{
    const float normalizedTurns = yawRadians / (Pi * 2.0f);
    int angle = int(std::lround(normalizedTurns * 2048.0f)) % 2048;

    if (angle < 0)
    {
        angle += 2048;
    }

    return uint16_t(angle);
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
    std::optional<EventRuntimeState> *pEventRuntimeState,
    GameplayActorService *pGameplayActorService,
    const SpriteFrameTable *pActorSpriteFrameTable
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
    m_pGameplayActorService = pGameplayActorService;
    m_pActorSpriteFrameTable = pActorSpriteFrameTable;
    std::random_device randomDevice;
    const uint64_t timeSeed = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    m_sessionChestSeed = randomDevice() ^ uint32_t(timeSeed) ^ uint32_t(timeSeed >> 32);
    m_materializedChestViews.clear();
    m_activeChestView.reset();
    m_mapActorCorpseViews.clear();
    m_activeCorpseView.reset();
    syncMapActorSpellEffectStates();
}

void IndoorWorldRuntime::bindRenderer(IndoorDebugRenderer *pRenderer)
{
    m_pRenderer = pRenderer;
}

void IndoorWorldRuntime::bindGameplayView(IndoorGameView *pView)
{
    m_pGameplayView = pView;
}

void IndoorWorldRuntime::syncMapActorSpellEffectStates()
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();
    const size_t actorCount = pMapDeltaData != nullptr ? pMapDeltaData->actors.size() : 0;
    m_mapActorSpellEffectStates.resize(actorCount);
}

const std::string &IndoorWorldRuntime::mapName() const
{
    return m_mapName;
}

const std::vector<uint8_t> *IndoorWorldRuntime::journalMapFullyRevealedCells() const
{
    return nullptr;
}

const std::vector<uint8_t> *IndoorWorldRuntime::journalMapPartiallyRevealedCells() const
{
    return nullptr;
}

int IndoorWorldRuntime::restFoodRequired() const
{
    int foodRequired = 2;

    if (m_pPartyRuntime == nullptr)
    {
        return foodRequired;
    }

    constexpr uint32_t DragonRaceId = 5;
    const Party &partyState = m_pPartyRuntime->party();

    for (const Character &member : partyState.members())
    {
        if (member.raceId == DragonRaceId)
        {
            ++foodRequired;
            break;
        }
    }

    return std::max(1, foodRequired);
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

void IndoorWorldRuntime::setAlwaysRunEnabled(bool enabled)
{
    if (m_pPartyRuntime != nullptr)
    {
        m_pPartyRuntime->setMovementSpeedMultiplier(enabled ? 2.0f : 1.0f);
    }
}

void IndoorWorldRuntime::updateWorldMovement(
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput)
{
    if (m_pRenderer != nullptr)
    {
        m_pRenderer->updateWorldMovement(input, deltaSeconds, allowWorldInput);
    }
}

void IndoorWorldRuntime::updateActorAi(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || m_pGameplayActorService == nullptr)
    {
        return;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    syncMapActorSpellEffectStates();

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
        GameplayActorSpellEffectState &effectState = m_mapActorSpellEffectStates[actorIndex];

        if (!hasActiveActorSpellEffectOverride(effectState))
        {
            continue;
        }

        m_pGameplayActorService->updateSpellEffectTimers(
            effectState,
            deltaSeconds,
            defaultActorHostileToParty(actor, m_pMonsterTable));
    }
}

void IndoorWorldRuntime::updateWorld(float deltaSeconds)
{
    (void)deltaSeconds;
}

void IndoorWorldRuntime::renderWorld(
    int width,
    int height,
    const GameplayInputFrame &input,
    float deltaSeconds)
{
    if (m_pGameplayView != nullptr)
    {
        m_pGameplayView->render(width, height, input, deltaSeconds);
    }
}

GameplayWorldUiRenderState IndoorWorldRuntime::gameplayUiRenderState(int width, int height) const
{
    if (m_pGameplayView == nullptr)
    {
        return GameplayWorldUiRenderState{.renderGameplayHud = false};
    }

    return m_pGameplayView->gameplayUiRenderState(width, height);
}

bool IndoorWorldRuntime::requestTravelAutosave()
{
    return false;
}

void IndoorWorldRuntime::cancelPendingMapTransition()
{
}

bool IndoorWorldRuntime::executeNpcTopicEvent(uint16_t eventId, size_t &previousMessageCount)
{
    (void)eventId;
    (void)previousMessageCount;
    return false;
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
        || (m_pMonsterTable != nullptr
            && resolvedMonsterId > 0
            && m_pMonsterTable->isHostileToParty(resolvedMonsterId));
    const bool defaultDetectedParty = hostileToParty && isAggressive;
    const GameplayActorSpellEffectState *pEffectState =
        actorIndex < m_mapActorSpellEffectStates.size() ? &m_mapActorSpellEffectStates[actorIndex] : nullptr;
    const bool useEffectOverride = pEffectState != nullptr && hasActiveActorSpellEffectOverride(*pEffectState);

    state.preciseX = static_cast<float>(actor.x);
    state.preciseY = static_cast<float>(actor.y);
    state.preciseZ = static_cast<float>(actor.z);
    state.radius = actor.radius;
    state.height = actor.height;
    state.isDead = actor.hp <= 0;
    state.isInvisible = isInvisible;
    state.hostileToParty = useEffectOverride ? pEffectState->hostileToParty : hostileToParty;
    state.hasDetectedParty = useEffectOverride ? pEffectState->hasDetectedParty : defaultDetectedParty;
    return true;
}

bool IndoorWorldRuntime::actorInspectState(
    size_t actorIndex,
    uint32_t animationTicks,
    GameplayActorInspectState &state) const
{
    state = {};

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr
        || m_pMonsterTable == nullptr
        || actorIndex >= pMapDeltaData->actors.size())
    {
        return false;
    }

    const MapDeltaActor &actor = pMapDeltaData->actors[actorIndex];
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(resolvedMonsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    state.displayName = resolveMapDeltaActorName(*m_pMonsterTable, actor);
    state.monsterId = resolvedMonsterId;
    state.currentHp = std::max(0, static_cast<int>(actor.hp));
    state.maxHp = std::max(0, pStats->hitPoints);
    state.isDead = actor.hp <= 0;

    int armorClass = pStats->armorClass;
    const GameplayActorSpellEffectState *pEffectState =
        actorIndex < m_mapActorSpellEffectStates.size() ? &m_mapActorSpellEffectStates[actorIndex] : nullptr;

    if (pEffectState != nullptr)
    {
        state.slowRemainingSeconds = pEffectState->slowRemainingSeconds;
        state.stunRemainingSeconds = pEffectState->stunRemainingSeconds;
        state.paralyzeRemainingSeconds = pEffectState->paralyzeRemainingSeconds;
        state.fearRemainingSeconds = pEffectState->fearRemainingSeconds;
        state.shrinkRemainingSeconds = pEffectState->shrinkRemainingSeconds;
        state.darkGraspRemainingSeconds = pEffectState->darkGraspRemainingSeconds;
        state.controlMode = pEffectState->controlMode;

        if (m_pGameplayActorService != nullptr)
        {
            armorClass = m_pGameplayActorService->effectiveArmorClass(armorClass, *pEffectState);
        }
    }

    state.armorClass = armorClass;

    if (m_pActorSpriteFrameTable == nullptr)
    {
        return true;
    }

    const MonsterEntry *pMonsterEntry = resolveRuntimeMonsterEntry(*m_pMonsterTable, actor);
    const uint16_t spriteFrameIndex =
        resolveRuntimeActorSpriteFrameIndex(*m_pActorSpriteFrameTable, actor, pMonsterEntry);

    if (spriteFrameIndex == 0)
    {
        return true;
    }

    const SpriteFrameEntry *pFrame = m_pActorSpriteFrameTable->getFrame(spriteFrameIndex, animationTicks);

    if (pFrame == nullptr)
    {
        pFrame = m_pActorSpriteFrameTable->getFrame(spriteFrameIndex, 0);
    }

    if (pFrame == nullptr)
    {
        return true;
    }

    const ResolvedSpriteTexture resolvedTexture = SpriteFrameTable::resolveTexture(*pFrame, 0);
    state.previewTextureName = resolvedTexture.textureName;
    state.previewPaletteId = pFrame->paletteId;
    return true;
}

std::optional<GameplayCombatActorInfo> IndoorWorldRuntime::combatActorInfoById(uint32_t actorId) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorId >= pMapDeltaData->actors.size() || m_pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    const size_t actorIndex = actorId;
    GameplayActorInspectState inspectState = {};

    if (!actorInspectState(actorIndex, 0, inspectState))
    {
        return std::nullopt;
    }

    GameplayCombatActorInfo info = {};
    info.actorId = actorId;
    info.monsterId = inspectState.monsterId;
    info.maxHp = inspectState.maxHp;
    info.displayName = inspectState.displayName;

    if (const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(inspectState.monsterId))
    {
        info.attackPreferences = pStats->attackPreferences;
    }

    return info;
}

bool IndoorWorldRuntime::castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request)
{
    const GameplayWorldPoint source =
    {
        .x = request.sourceX,
        .y = request.sourceY,
        .z = request.sourceZ,
    };
    const GameplayWorldPoint target =
    {
        .x = request.targetX,
        .y = request.targetY,
        .z = request.targetZ,
    };
    const std::optional<size_t> actorIndex = findActorOnAttackLine(*this, source, target);

    if (!actorIndex)
    {
        return false;
    }

    const bool applied = applyPartySpellToActor(
        *actorIndex,
        request.spellId,
        request.skillLevel,
        request.skillMastery,
        request.damage,
        request.sourceX,
        request.sourceY,
        request.sourceZ,
        request.casterMemberIndex);

    if (applied)
    {
        triggerProjectileImpactPresentation(*actorIndex, request.spellId);
    }

    return applied;
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
    (void)partyX;
    (void)partyY;
    (void)partyZ;
    (void)sourcePartyMemberIndex;

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

    syncMapActorSpellEffectStates();
    GameplayActorSpellEffectState &effectState = m_mapActorSpellEffectStates[actorIndex];
    const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
    const bool defaultHostileToParty =
        (actor.attributes & static_cast<uint32_t>(EvtActorAttribute::Hostile)) != 0
        || (m_pMonsterTable != nullptr
            && resolvedMonsterId > 0
            && m_pMonsterTable->isHostileToParty(resolvedMonsterId));

    if (m_pGameplayActorService != nullptr)
    {
        const GameplayActorService::SharedSpellEffectResult effectResult =
            m_pGameplayActorService->tryApplySharedSpellEffect(
                spellId,
                skillLevel,
                skillMastery,
                m_pGameplayActorService->actorLooksUndead(resolvedMonsterId),
                defaultHostileToParty,
                effectState);

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Rejected)
        {
            return false;
        }

        if (effectResult.disposition == GameplayActorService::SharedSpellDisposition::Applied)
        {
            return true;
        }
    }

    if (damage <= 0)
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

    syncMapActorSpellEffectStates();
    return spawnedAny;
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

bool IndoorWorldRuntime::canActivateWorldHit(
    const GameplayWorldHit &hit,
    GameplayInteractionMethod interactionMethod) const
{
    (void)interactionMethod;

    if (hit.kind == GameplayWorldHitKind::WorldItem && hit.worldItem)
    {
        const MapDeltaData *pMapDeltaData = mapDeltaData();

        return pMapDeltaData != nullptr
            && hit.worldItem->worldItemIndex < pMapDeltaData->spriteObjects.size()
            && hasContainingItemPayload(pMapDeltaData->spriteObjects[hit.worldItem->worldItemIndex].rawContainingItem);
    }

    return m_pRenderer != nullptr && m_pRenderer->canActivateGameplayWorldHit(hit);
}

bool IndoorWorldRuntime::activateWorldHit(const GameplayWorldHit &hit)
{
    if (hit.kind == GameplayWorldHitKind::WorldItem && hit.worldItem)
    {
        MapDeltaData *pMapDeltaData = mapDeltaData();

        if (pMapDeltaData == nullptr || hit.worldItem->worldItemIndex >= pMapDeltaData->spriteObjects.size())
        {
            return false;
        }

        MapDeltaSpriteObject &spriteObject = pMapDeltaData->spriteObjects[hit.worldItem->worldItemIndex];
        InventoryItem item = {};

        if (!readIndoorHeldItemPayload(spriteObject.rawContainingItem, m_pItemTable, item))
        {
            return false;
        }

        size_t recipientMemberIndex = 0;

        if (m_pParty == nullptr || !m_pParty->tryGrantInventoryItem(item, &recipientMemberIndex))
        {
            return false;
        }

        const ItemDefinition *pItemDefinition =
            m_pItemTable != nullptr ? m_pItemTable->get(item.objectDescriptionId) : nullptr;
        const std::string itemName =
            pItemDefinition != nullptr && !pItemDefinition->name.empty() ? pItemDefinition->name : "item";

        pMapDeltaData->spriteObjects.erase(
            pMapDeltaData->spriteObjects.begin() + std::ptrdiff_t(hit.worldItem->worldItemIndex));
        m_pParty->requestSound(SoundId::Gold);

        if (m_pEventRuntimeState != nullptr && *m_pEventRuntimeState)
        {
            (*m_pEventRuntimeState)->lastActivationResult = "picked up " + itemName;
        }

        (void)recipientMemberIndex;
        return true;
    }

    return m_pRenderer != nullptr && m_pRenderer->activateGameplayWorldHit(hit);
}

std::optional<GameplayPartyAttackActorFacts> IndoorWorldRuntime::partyAttackActorFacts(
    size_t actorIndex,
    bool visibleForFallback) const
{
    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size())
    {
        return std::nullopt;
    }

    GameplayRuntimeActorState runtimeState = {};
    GameplayActorInspectState inspectState = {};

    if (!actorRuntimeState(actorIndex, runtimeState) || !actorInspectState(actorIndex, 0, inspectState))
    {
        return std::nullopt;
    }

    return GameplayPartyAttackActorFacts{
        .actorIndex = actorIndex,
        .monsterId = inspectState.monsterId,
        .displayName = inspectState.displayName,
        .position =
            GameplayWorldPoint{
                .x = runtimeState.preciseX,
                .y = runtimeState.preciseY,
                .z = runtimeState.preciseZ,
            },
        .radius = runtimeState.radius,
        .height = runtimeState.height,
        .currentHp = inspectState.currentHp,
        .maxHp = inspectState.maxHp,
        .effectiveArmorClass = inspectState.armorClass,
        .isDead = runtimeState.isDead,
        .isInvisible = runtimeState.isInvisible,
        .hostileToParty = runtimeState.hostileToParty,
        .visibleForFallback = visibleForFallback,
    };
}

std::vector<GameplayPartyAttackActorFacts> IndoorWorldRuntime::collectPartyAttackFallbackActors(
    const GameplayPartyAttackFallbackQuery &query) const
{
    std::vector<GameplayPartyAttackActorFacts> actors;
    float viewProjectionMatrix[16] = {};
    bx::mtxMul(viewProjectionMatrix, query.viewMatrix.data(), query.projectionMatrix.data());

    for (size_t actorIndex = 0; actorIndex < mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState runtimeState = {};

        if (!actorRuntimeState(actorIndex, runtimeState))
        {
            continue;
        }

        const bx::Vec3 projected = bx::mulH(
            {
                runtimeState.preciseX,
                runtimeState.preciseY,
                runtimeState.preciseZ + std::max(48.0f, float(runtimeState.height) * 0.6f),
            },
            viewProjectionMatrix);
        const bool visibleForFallback =
            projected.z >= 0.0f
            && projected.z <= 1.0f
            && projected.x >= -1.0f
            && projected.x <= 1.0f
            && projected.y >= -1.0f
            && projected.y <= 1.0f;
        std::optional<GameplayPartyAttackActorFacts> facts =
            partyAttackActorFacts(actorIndex, visibleForFallback);

        if (facts)
        {
            actors.push_back(*facts);
        }
    }

    return actors;
}

bool IndoorWorldRuntime::applyPartyAttackMeleeDamage(
    size_t actorIndex,
    int damage,
    const GameplayWorldPoint &source)
{
    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr || actorIndex >= pMapDeltaData->actors.size() || damage <= 0)
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
    const int nextHp = std::max(0, previousHp - damage);
    actor.hp = static_cast<int16_t>(nextHp);
    actor.attributes |= static_cast<uint32_t>(EvtActorAttribute::Hostile)
        | static_cast<uint32_t>(EvtActorAttribute::Aggressor)
        | static_cast<uint32_t>(EvtActorAttribute::Active)
        | static_cast<uint32_t>(EvtActorAttribute::FullAi);

    if (previousHp > 0 && nextHp <= 0 && m_pMonsterTable != nullptr && m_pParty != nullptr)
    {
        const int16_t resolvedMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
        const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(resolvedMonsterId);

        if (pStats != nullptr && pStats->experience > 0)
        {
            m_pParty->grantSharedExperience(static_cast<uint32_t>(pStats->experience));
        }
    }

    (void)source;
    return actor.hp != previousHp;
}

bool IndoorWorldRuntime::spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request)
{
    if (request.damage <= 0)
    {
        return false;
    }

    const std::optional<size_t> actorIndex = findActorOnAttackLine(*this, request.source, request.target);

    if (!actorIndex)
    {
        return false;
    }

    const bool applied = applyPartyAttackMeleeDamage(*actorIndex, request.damage, request.source);

    if (applied)
    {
        triggerProjectileImpactPresentation(*actorIndex, 0);
    }

    return applied;
}

bool IndoorWorldRuntime::castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request)
{
    const std::optional<size_t> actorIndex = findActorOnAttackLine(*this, request.source, request.target);

    if (!actorIndex)
    {
        return false;
    }

    const bool applied = applyPartySpellToActor(
        *actorIndex,
        request.spellId,
        request.skillLevel,
        normalizeRuntimeSkillMastery(request.skillMastery),
        request.damage,
        request.source.x,
        request.source.y,
        request.source.z,
        static_cast<uint32_t>(request.sourcePartyMemberIndex));

    if (applied)
    {
        triggerProjectileImpactPresentation(*actorIndex, request.spellId);
    }

    return applied;
}

void IndoorWorldRuntime::recordPartyAttackWorldResult(
    std::optional<size_t> actorIndex,
    bool attacked,
    bool actionPerformed)
{
    if (!m_pEventRuntimeState || !*m_pEventRuntimeState)
    {
        return;
    }

    if (actorIndex)
    {
        (*m_pEventRuntimeState)->lastActivationResult =
            attacked
                ? "actor " + std::to_string(*actorIndex) + " hit by party"
                : "actor " + std::to_string(*actorIndex) + " attacked by party";
        return;
    }

    (*m_pEventRuntimeState)->lastActivationResult =
        actionPerformed
            ? "party attack released"
            : "party attack failed";
}

bool IndoorWorldRuntime::worldInteractionReady() const
{
    return true;
}

bool IndoorWorldRuntime::worldInspectModeActive() const
{
    return true;
}

GameplayWorldPickRequest IndoorWorldRuntime::buildWorldPickRequest(const GameplayWorldPickRequestInput &input) const
{
    if (m_pRenderer != nullptr)
    {
        return m_pRenderer->buildGameplayWorldPickRequest(input);
    }

    GameplayWorldPickRequest request = {};
    request.screenX = input.screenX;
    request.screenY = input.screenY;
    request.viewWidth = input.screenWidth;
    request.viewHeight = input.screenHeight;
    return request;
}

std::optional<GameplayHeldItemDropRequest> IndoorWorldRuntime::buildHeldItemDropRequest() const
{
    if (m_pPartyRuntime == nullptr)
    {
        return std::nullopt;
    }

    const float yawRadians = m_pRenderer != nullptr ? m_pRenderer->cameraYawRadians() : 0.0f;
    const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
    return GameplayHeldItemDropRequest{
        .sourceX = moveState.x + std::cos(yawRadians) * IndoorDroppedItemForwardOffset,
        .sourceY = moveState.y + std::sin(yawRadians) * IndoorDroppedItemForwardOffset,
        .sourceZ = moveState.footZ + IndoorDroppedItemHeightOffset,
        .yawRadians = yawRadians,
    };
}

GameplayPartyAttackFrameInput IndoorWorldRuntime::buildPartyAttackFrameInput(
    const GameplayWorldPickRequest &pickRequest) const
{
    if (m_pPartyRuntime == nullptr)
    {
        return {};
    }

    const IndoorMoveState &moveState = m_pPartyRuntime->movementState();
    const float attackSourceX = moveState.x;
    const float attackSourceY = moveState.y;
    const float attackSourceZ = moveState.eyeZ();

    GameplayPartyAttackFrameInput input = {};
    input.enabled = true;
    input.partyPosition =
        GameplayWorldPoint{
            .x = moveState.x,
            .y = moveState.y,
            .z = moveState.footZ,
        };
    input.rangedSource =
        GameplayWorldPoint{
            .x = attackSourceX,
            .y = attackSourceY,
            .z = attackSourceZ,
        };

    if (pickRequest.hasRay)
    {
        input.defaultRangedTarget =
            GameplayWorldPoint{
                .x = pickRequest.rayOrigin.x + pickRequest.rayDirection.x * 5120.0f,
                .y = pickRequest.rayOrigin.y + pickRequest.rayDirection.y * 5120.0f,
                .z = pickRequest.rayOrigin.z + pickRequest.rayDirection.z * 5120.0f,
            };
        input.rayRangedTarget = input.defaultRangedTarget;
        input.hasRayRangedTarget = true;
    }
    else
    {
        input.defaultRangedTarget =
            GameplayWorldPoint{
                .x = attackSourceX + 5120.0f,
                .y = attackSourceY,
                .z = attackSourceZ,
            };
    }

    std::copy(
        pickRequest.viewMatrix.begin(),
        pickRequest.viewMatrix.end(),
        input.fallbackQuery.viewMatrix.begin());
    std::copy(
        pickRequest.projectionMatrix.begin(),
        pickRequest.projectionMatrix.end(),
        input.fallbackQuery.projectionMatrix.begin());
    return input;
}

std::optional<size_t> IndoorWorldRuntime::spellActionHoveredActorIndex() const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayHoveredActorIndex() : std::nullopt;
}

std::optional<size_t> IndoorWorldRuntime::spellActionClosestVisibleHostileActorIndex() const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayClosestVisibleHostileActorIndex() : std::nullopt;
}

std::optional<bx::Vec3> IndoorWorldRuntime::spellActionActorTargetPoint(size_t actorIndex) const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayActorTargetPoint(actorIndex) : std::nullopt;
}

std::optional<bx::Vec3> IndoorWorldRuntime::spellActionGroundTargetPoint(float screenX, float screenY) const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayGroundTargetPoint(screenX, screenY) : std::nullopt;
}

GameplayPendingSpellWorldTargetFacts IndoorWorldRuntime::pickPendingSpellWorldTarget(
    const GameplayWorldPickRequest &request)
{
    GameplayPendingSpellWorldTargetFacts facts = {};

    if (m_pRenderer == nullptr)
    {
        return facts;
    }

    facts.worldHit = m_pRenderer->pickGameplayWorldHit(request);

    if (facts.worldHit.ground)
    {
        facts.fallbackGroundTargetPoint = facts.worldHit.ground->worldPoint;
    }
    else if (facts.worldHit.eventTarget)
    {
        facts.fallbackGroundTargetPoint = facts.worldHit.eventTarget->hitPoint;
    }
    else if (facts.worldHit.object)
    {
        facts.fallbackGroundTargetPoint = facts.worldHit.object->hitPoint;
    }
    else if (facts.worldHit.actor)
    {
        facts.fallbackGroundTargetPoint = facts.worldHit.actor->hitPoint;
    }

    return facts;
}

GameplayWorldHit IndoorWorldRuntime::pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->pickGameplayWorldHit(request) : GameplayWorldHit{};
}

GameplayWorldHit IndoorWorldRuntime::pickHeldItemWorldTarget(const GameplayWorldPickRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->pickGameplayWorldHit(request) : GameplayWorldHit{};
}

GameplayWorldHit IndoorWorldRuntime::pickCurrentInteractionTarget(const GameplayWorldPickRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->pickGameplayWorldHit(request) : GameplayWorldHit{};
}

GameplayWorldHoverCacheState IndoorWorldRuntime::worldHoverCacheState() const
{
    return m_pRenderer != nullptr ? m_pRenderer->gameplayWorldHoverCacheState() : GameplayWorldHoverCacheState{};
}

GameplayHoverStatusPayload IndoorWorldRuntime::refreshWorldHover(const GameplayWorldHoverRequest &request)
{
    return m_pRenderer != nullptr ? m_pRenderer->refreshGameplayWorldHover(request) : GameplayHoverStatusPayload{};
}

GameplayHoverStatusPayload IndoorWorldRuntime::readCachedWorldHover()
{
    return m_pRenderer != nullptr ? m_pRenderer->readCachedGameplayWorldHover() : GameplayHoverStatusPayload{};
}

void IndoorWorldRuntime::clearWorldHover()
{
    if (m_pRenderer != nullptr)
    {
        m_pRenderer->clearGameplayWorldHover();
    }
}

bool IndoorWorldRuntime::canUseHeldItemOnWorld(const GameplayWorldHit &hit) const
{
    return canActivateWorldHit(hit, GameplayInteractionMethod::Mouse);
}

bool IndoorWorldRuntime::useHeldItemOnWorld(const GameplayWorldHit &hit)
{
    return activateWorldHit(hit);
}

void IndoorWorldRuntime::applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult)
{
    if (m_pRenderer != nullptr)
    {
        m_pRenderer->triggerPendingSpellWorldFx(castResult);
    }
}

bool IndoorWorldRuntime::dropHeldItemToWorld(const GameplayHeldItemDropRequest &request)
{
    if (m_pObjectTable == nullptr || m_pItemTable == nullptr || request.item.objectDescriptionId == 0)
    {
        return false;
    }

    MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return false;
    }

    const std::optional<uint16_t> objectDescriptionId =
        resolveIndoorItemObjectDescriptionId(request.item, m_pItemTable, m_pObjectTable);

    if (!objectDescriptionId)
    {
        return false;
    }

    const ObjectEntry *pObjectEntry = m_pObjectTable->get(*objectDescriptionId);

    if (pObjectEntry == nullptr || (pObjectEntry->flags & ObjectDescNoSprite) != 0 || pObjectEntry->spriteId == 0)
    {
        return false;
    }

    MapDeltaSpriteObject spriteObject = {};
    spriteObject.spriteId = pObjectEntry->spriteId;
    spriteObject.objectDescriptionId = *objectDescriptionId;
    spriteObject.x = int(std::lround(request.sourceX));
    spriteObject.y = int(std::lround(request.sourceY));
    spriteObject.z = int(std::lround(request.sourceZ));
    spriteObject.yawAngle = yawAngleFromRadians(request.yawRadians);
    spriteObject.attributes = SpriteAttrDroppedByPlayer;
    spriteObject.sectorId = m_pPartyRuntime != nullptr ? m_pPartyRuntime->movementState().sectorId : -1;
    spriteObject.temporaryLifetime = pObjectEntry->lifetimeTicks;
    spriteObject.initialX = spriteObject.x;
    spriteObject.initialY = spriteObject.y;
    spriteObject.initialZ = spriteObject.z;
    writeIndoorHeldItemPayload(spriteObject.rawContainingItem, request.item);

    pMapDeltaData->spriteObjects.push_back(std::move(spriteObject));
    return true;
}

bool IndoorWorldRuntime::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    state = {};

    if (!m_map || m_map->fileName.empty() || m_pPartyRuntime == nullptr)
    {
        return false;
    }

    const Party *pParty = party();
    const PartyBuffState *pWizardEyeBuff = pParty != nullptr ? pParty->partyBuff(PartyBuffId::WizardEye) : nullptr;
    const SkillMastery wizardEyeMastery =
        pWizardEyeBuff != nullptr ? pWizardEyeBuff->skillMastery : SkillMastery::None;
    const IndoorMoveState &moveState = m_pPartyRuntime->movementState();

    state.textureName = toLowerCopy(std::filesystem::path(m_map->fileName).stem().string());
    state.partyU = indoorMinimapU(moveState.x);
    state.partyV = indoorMinimapV(moveState.y);
    state.wizardEyeActive = pWizardEyeBuff != nullptr;
    state.wizardEyeShowsExpertObjects = wizardEyeMastery >= SkillMastery::Expert;
    state.wizardEyeShowsMasterDecorations = wizardEyeMastery >= SkillMastery::Master;
    return true;
}

void IndoorWorldRuntime::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    markers.clear();

    GameplayMinimapState minimapState = {};

    if (!tryGetGameplayMinimapState(minimapState) || !minimapState.wizardEyeActive)
    {
        return;
    }

    const MapDeltaData *pMapDeltaData = mapDeltaData();

    if (pMapDeltaData == nullptr)
    {
        return;
    }

    for (size_t actorIndex = 0; actorIndex < pMapDeltaData->actors.size(); ++actorIndex)
    {
        GameplayRuntimeActorState actorState = {};

        if (!actorRuntimeState(actorIndex, actorState) || actorState.isInvisible)
        {
            continue;
        }

        GameplayMinimapMarkerState marker = {};
        marker.type = actorState.isDead
            ? GameplayMinimapMarkerType::CorpseActor
            : actorState.hostileToParty
            ? GameplayMinimapMarkerType::HostileActor
            : GameplayMinimapMarkerType::FriendlyActor;
        marker.u = indoorMinimapU(actorState.preciseX);
        marker.v = indoorMinimapV(actorState.preciseY);
        markers.push_back(marker);
    }

    if (!minimapState.wizardEyeShowsExpertObjects)
    {
        return;
    }

    for (const MapDeltaSpriteObject &spriteObject : pMapDeltaData->spriteObjects)
    {
        if (!hasContainingItemPayload(spriteObject.rawContainingItem))
        {
            continue;
        }

        GameplayMinimapMarkerState marker = {};
        marker.type = GameplayMinimapMarkerType::WorldItem;
        marker.u = indoorMinimapU(static_cast<float>(spriteObject.x));
        marker.v = indoorMinimapV(static_cast<float>(spriteObject.y));
        markers.push_back(marker);
    }
}

IndoorWorldRuntime::ChestViewState *IndoorWorldRuntime::activeChestView()
{
    return m_activeChestView ? &*m_activeChestView : nullptr;
}

const IndoorWorldRuntime::ChestViewState *IndoorWorldRuntime::activeChestView() const
{
    return m_activeChestView ? &*m_activeChestView : nullptr;
}

void IndoorWorldRuntime::commitActiveChestView()
{
    if (!m_activeChestView)
    {
        return;
    }

    const uint32_t chestId = m_activeChestView->chestId;

    if (chestId < m_materializedChestViews.size() && m_materializedChestViews[chestId].has_value())
    {
        m_materializedChestViews[chestId] = *m_activeChestView;
    }
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

IndoorWorldRuntime::CorpseViewState *IndoorWorldRuntime::activeCorpseView()
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

const IndoorWorldRuntime::CorpseViewState *IndoorWorldRuntime::activeCorpseView() const
{
    return m_activeCorpseView ? &*m_activeCorpseView : nullptr;
}

void IndoorWorldRuntime::commitActiveCorpseView()
{
    if (!m_activeCorpseView)
    {
        return;
    }

    if (m_activeCorpseView->sourceIndex < m_mapActorCorpseViews.size())
    {
        m_mapActorCorpseViews[m_activeCorpseView->sourceIndex] = *m_activeCorpseView;
    }
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

    syncMapActorSpellEffectStates();
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
    snapshot.mapActorSpellEffectStates = m_mapActorSpellEffectStates;
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
    m_mapActorSpellEffectStates = snapshot.mapActorSpellEffectStates;
    syncMapActorSpellEffectStates();
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

std::optional<GameplayWorldPoint> IndoorWorldRuntime::actorImpactPoint(size_t actorIndex) const
{
    GameplayRuntimeActorState actorState = {};

    if (!actorRuntimeState(actorIndex, actorState))
    {
        return std::nullopt;
    }

    return GameplayWorldPoint{
        .x = actorState.preciseX,
        .y = actorState.preciseY,
        .z = actorState.preciseZ + std::max(24.0f, static_cast<float>(actorState.height) * 0.6f),
    };
}

void IndoorWorldRuntime::triggerProjectileImpactPresentation(size_t actorIndex, uint32_t spellId)
{
    if (m_pRenderer == nullptr)
    {
        return;
    }

    const std::optional<GameplayWorldPoint> impactPoint = actorImpactPoint(actorIndex);

    if (!impactPoint)
    {
        return;
    }

    m_pRenderer->triggerProjectileImpactWorldFx(
        impactPoint->x,
        impactPoint->y,
        impactPoint->z,
        spellId);
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
