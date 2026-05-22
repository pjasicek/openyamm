#include "game/events/ISceneEventContext.h"
#include "game/events/EventRuntime.h"
#include "engine/scripting/LuaStateOwner.h"
#include "game/audio/SoundIds.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/NpcDialogTable.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <iostream>
#include <limits>
#include <string_view>
#include <unordered_map>

extern "C"
{
#include <lauxlib.h>
}

namespace OpenYAMM::Game
{
namespace
{
constexpr int OeDaysPerWeek = 7;
constexpr int OeDaysPerMonth = 28;
constexpr int OeDaysPerYear = 12 * OeDaysPerMonth;
constexpr int OeGameStartingYear = 1168;
constexpr uint32_t DefaultEventPortraitDurationTicks = 96;
constexpr uint32_t MaxBitfieldFlagIndex = 31;
constexpr uint32_t DefaultHistoryContinentId = 1;
constexpr uint32_t Mm7HistoryContinentId = 2;
constexpr uint32_t Mm6CircusLodestoneItemId = 2090;
constexpr uint32_t Mm6CircusHarpyFeatherItemId = 2091;
constexpr uint32_t Mm6CircusFourLeafCloverItemId = 2097;
constexpr int32_t Mm6CircusLodestonePoints = 1;
constexpr int32_t Mm6CircusHarpyFeatherPoints = 3;
constexpr int32_t Mm6CircusFourLeafCloverPoints = 5;

int resolveMonthFromDayOfYear(int dayOfYear);
int currentGameMinutesFromRuntimeState(const EventRuntimeState &runtimeState);
uint32_t randomJumpSeed(uint16_t eventId, uint8_t step, const EventRuntimeState &runtimeState);
uint32_t nextEventRandom(uint16_t eventId, uint8_t step, EventRuntimeState &runtimeState);
std::optional<std::string> skillNameForEvtVariable(EvtVariable variableId);
SkillMastery normalizeCheckSkillMastery(uint32_t rawMastery);
bool evaluateCompareValue(
    const EventRuntimeState &runtimeState,
    uint32_t rawVariableId,
    int32_t compareValue,
    const Party *pParty,
    const std::vector<size_t> &targetMemberIndices,
    bool usePartyWideInventory,
    const ISceneEventContext *pSceneEventContext = nullptr);
const Party *readableParty(lua_State *pLuaState);
const MapDeltaDoor *findMechanismDoorById(const MapDeltaData *pMapDeltaData, uint32_t mechanismId);
void initializeRuntimeMechanismStateFromDoor(
    const MapDeltaDoor &door,
    RuntimeMechanismState &runtimeMechanism);

uint32_t normalizedHistoryContinent(uint32_t continentId)
{
    return continentId != 0 ? continentId : DefaultHistoryContinentId;
}

std::unordered_map<uint32_t, int32_t> &mutableHistoryEventTimesForActiveContinent(EventRuntimeState &runtimeState)
{
    const uint32_t continentId = normalizedHistoryContinent(runtimeState.activeHistoryContinentId);
    runtimeState.activeHistoryContinentId = continentId;

    if (continentId == DefaultHistoryContinentId
        && runtimeState.historyEventTimesByContinent.find(continentId)
            == runtimeState.historyEventTimesByContinent.end()
        && !runtimeState.historyEventTimes.empty())
    {
        runtimeState.historyEventTimesByContinent[continentId] = runtimeState.historyEventTimes;
    }

    return runtimeState.historyEventTimesByContinent[continentId];
}

const std::unordered_map<uint32_t, int32_t> &historyEventTimesForContinent(
    const EventRuntimeState &runtimeState,
    uint32_t continentId)
{
    const uint32_t normalizedContinentId = normalizedHistoryContinent(continentId);
    const std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>>::const_iterator found =
        runtimeState.historyEventTimesByContinent.find(normalizedContinentId);

    if (found != runtimeState.historyEventTimesByContinent.end())
    {
        return found->second;
    }

    if (normalizedContinentId == DefaultHistoryContinentId)
    {
        return runtimeState.historyEventTimes;
    }

    static const std::unordered_map<uint32_t, int32_t> emptyTimes;
    return emptyTimes;
}

void synchronizeLegacyHistoryMirror(EventRuntimeState &runtimeState)
{
    const std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>>::const_iterator found =
        runtimeState.historyEventTimesByContinent.find(DefaultHistoryContinentId);

    runtimeState.historyEventTimes = found != runtimeState.historyEventTimesByContinent.end()
        ? found->second
        : std::unordered_map<uint32_t, int32_t>{};
}

std::string traceQuoted(const std::string &value)
{
    std::string quoted = "\"";

    for (char character : value)
    {
        if (character == '\\' || character == '"')
        {
            quoted.push_back('\\');
        }

        quoted.push_back(character);
    }

    quoted.push_back('"');
    return quoted;
}

void traceRuntimeValueChange(
    const EventRuntimeState &runtimeState,
    const std::string &eventName,
    const std::string &identity,
    int32_t previousValue,
    int32_t currentValue,
    const char *pOperation)
{
    if (previousValue == currentValue)
    {
        return;
    }

    GAMEPLAY_DEBUG_TRACE(
        eventName
        + " map=\"" + runtimeState.mapFileName + "\""
        + " operation=" + pOperation
        + " " + identity
        + " previous=" + std::to_string(previousValue)
        + " current=" + std::to_string(currentValue));
}

void traceIndexedRuntimeValueChange(
    const EventRuntimeState &runtimeState,
    const std::string &eventName,
    size_t index,
    int32_t previousValue,
    int32_t currentValue,
    const char *pOperation)
{
    traceRuntimeValueChange(
        runtimeState,
        eventName,
        "index=" + std::to_string(index),
        previousValue,
        currentValue,
        pOperation);
}

void traceNamedRuntimeValueChange(
    const EventRuntimeState &runtimeState,
    const std::string &eventName,
    const std::string &name,
    int32_t previousValue,
    int32_t currentValue,
    const char *pOperation)
{
    traceRuntimeValueChange(
        runtimeState,
        eventName,
        "name=\"" + name + "\"",
        previousValue,
        currentValue,
        pOperation);
}

void seedForwardHistoryEntries(EventRuntimeState &runtimeState)
{
    std::unordered_map<uint32_t, int32_t> &historyTimes = mutableHistoryEventTimesForActiveContinent(runtimeState);
    const uint32_t continentId = normalizedHistoryContinent(runtimeState.activeHistoryContinentId);

    if (continentId == DefaultHistoryContinentId)
    {
        historyTimes[1] = 1;
    }
    else if (continentId == Mm7HistoryContinentId)
    {
        historyTimes[1] = 1;
        historyTimes[2] = 2;
    }

    synchronizeLegacyHistoryMirror(runtimeState);
}

int32_t moveToMapYawUnitsToDegrees(int32_t yawUnits)
{
    const int32_t normalizedYawUnits = ((yawUnits % 2048) + 2048) % 2048;
    return normalizedYawUnits * 360 / 2048;
}

std::string sanitizeEventString(const std::string &value)
{
    std::string sanitized;
    sanitized.reserve(value.size());

    for (char character : value)
    {
        if (std::isprint(static_cast<unsigned char>(character)) != 0)
        {
            sanitized.push_back(character);
        }
    }

    return sanitized;
}

bool isCurrentMapMoveSentinel(const std::string &mapName)
{
    size_t begin = 0;
    while (begin < mapName.size() && std::isspace(static_cast<unsigned char>(mapName[begin])) != 0)
    {
        ++begin;
    }

    size_t end = mapName.size();
    while (end > begin && std::isspace(static_cast<unsigned char>(mapName[end - 1])) != 0)
    {
        --end;
    }

    std::string normalizedMapName;
    normalizedMapName.reserve(end - begin);
    for (size_t index = begin; index < end; ++index)
    {
        normalizedMapName.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(mapName[index]))));
    }

    return normalizedMapName == "0" || normalizedMapName == "0.";
}

bool matchesRandomGiveItemType(const ItemDefinition &itemDefinition, uint32_t treasureType)
{
    const std::string &equipStat = itemDefinition.equipStat;

    switch (treasureType)
    {
        case 0:
            return true;

        case 20: // const.ItemType.Weapon_
            return equipStat == "Weapon"
                || equipStat == "Weapon1or2"
                || equipStat == "Weapon2"
                || equipStat == "Missile";

        case 21: // const.ItemType.Armor_
            return equipStat == "Armor"
                || equipStat == "Shield"
                || equipStat == "Helm"
                || equipStat == "Belt"
                || equipStat == "Cloak"
                || equipStat == "Gauntlets"
                || equipStat == "Boots"
                || equipStat == "Amulet";

        case 22: // const.ItemType.Misc
            return equipStat == "Misc"
                || equipStat == "Bottle"
                || equipStat == "Reagent"
                || equipStat == "Gold"
                || equipStat == "Gem"
                || equipStat == "Message"
                || equipStat == "0"
                || equipStat == "N / A"
                || equipStat.empty();

        case 40: // const.ItemType.Ring_
            return equipStat == "Ring";

        case 43: // const.ItemType.Scroll_
            return equipStat == "Sscroll"
                || equipStat == "Mscroll"
                || equipStat == "Book";

        default:
            return true;
    }
}

std::optional<InventoryItem> createGrantedEventItem(
    EventRuntimeState &runtimeState,
    Party *pParty,
    uint16_t eventId,
    uint32_t treasureLevel,
    uint32_t treasureType,
    uint32_t itemId)
{
    const ItemTable *pItemTable = pParty != nullptr ? pParty->itemTable() : nullptr;

    if (itemId != 0)
    {
        if (pItemTable != nullptr)
        {
            return ItemGenerator::makeInventoryItem(itemId, *pItemTable, ItemGenerationMode::Generic);
        }

        InventoryItem item = {};
        item.objectDescriptionId = itemId;
        item.quantity = 1;
        return item;
    }

    if (pParty == nullptr
        || pItemTable == nullptr
        || pParty->standardItemEnchantTable() == nullptr
        || pParty->specialItemEnchantTable() == nullptr)
    {
        return std::nullopt;
    }

    ItemGenerationRequest request = {};
    request.treasureLevel = std::clamp(static_cast<int>(treasureLevel), 1, 6);
    request.mode = ItemGenerationMode::Generic;
    request.allowRareItems = true;

    std::mt19937 rng(nextEventRandom(
        eventId,
        static_cast<uint8_t>(runtimeState.grantedItems.size() & 0xFFu),
        runtimeState));

    return ItemGenerator::generateRandomInventoryItem(
        *pItemTable,
        *pParty->standardItemEnchantTable(),
        *pParty->specialItemEnchantTable(),
        request,
        pParty,
        rng,
        [treasureType](const ItemDefinition &itemDefinition)
        {
            return matchesRandomGiveItemType(itemDefinition, treasureType);
        });
}

float mechanismDistanceForState(const MapDeltaDoor &door, uint16_t state, float timeSinceTriggeredMs)
{
    if (state == static_cast<uint16_t>(EvtMechanismState::Open))
    {
        return 0.0f;
    }

    const float elapsedMilliseconds = static_cast<float>(timeSinceTriggeredMs);

    if (state == static_cast<uint16_t>(EvtMechanismState::Closing))
    {
        const float closingDistance = elapsedMilliseconds * static_cast<float>(door.closeSpeed) / 1000.0f;
        return std::min(closingDistance, static_cast<float>(door.moveLength));
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Opening))
    {
        const float openingDistance = elapsedMilliseconds * static_cast<float>(door.openSpeed) / 1000.0f;
        return std::max(0.0f, static_cast<float>(door.moveLength) - openingDistance);
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Closed) || (door.attributes & 0x2) != 0)
    {
        return static_cast<float>(door.moveLength);
    }

    return 0.0f;
}

const MapDeltaDoor *findMechanismDoorById(const MapDeltaData *pMapDeltaData, uint32_t mechanismId)
{
    if (pMapDeltaData == nullptr)
    {
        return nullptr;
    }

    for (const MapDeltaDoor &door : pMapDeltaData->doors)
    {
        if (door.doorId == mechanismId)
        {
            return &door;
        }
    }

    return nullptr;
}

void initializeRuntimeMechanismStateFromDoor(
    const MapDeltaDoor &door,
    RuntimeMechanismState &runtimeMechanism)
{
    runtimeMechanism = {};
    runtimeMechanism.state = door.state;
    runtimeMechanism.timeSinceTriggeredMs = float(door.timeSinceTriggered);
    runtimeMechanism.currentDistance =
        mechanismDistanceForState(door, runtimeMechanism.state, runtimeMechanism.timeSinceTriggeredMs);
    runtimeMechanism.isMoving =
        door.state == static_cast<uint16_t>(EvtMechanismState::Opening)
        || door.state == static_cast<uint16_t>(EvtMechanismState::Closing);
}

enum class PartySelectorKind
{
    None,
    Member,
    All,
    Current,
};

struct PartySelector
{
    PartySelectorKind kind = PartySelectorKind::None;
    size_t memberIndex = 0;
};

PartySelector decodePartySelector(uint32_t selectorValue)
{
    if (selectorValue <= static_cast<uint32_t>(EvtPartySelector::Member4))
    {
        PartySelector selector = {};
        selector.kind = PartySelectorKind::Member;
        selector.memberIndex = selectorValue;
        return selector;
    }

    if (selectorValue == static_cast<uint32_t>(EvtPartySelector::All))
    {
        PartySelector selector = {};
        selector.kind = PartySelectorKind::All;
        return selector;
    }

    if (selectorValue == static_cast<uint32_t>(EvtPartySelector::Current))
    {
        PartySelector selector = {};
        selector.kind = PartySelectorKind::Current;
        return selector;
    }

    return {};
}

void markOutdoorSurfaceStateChanged(EventRuntimeState &runtimeState)
{
    ++runtimeState.outdoorSurfaceRevision;
}

uint32_t maxFacetOverrideId(const std::unordered_map<uint32_t, uint32_t> &masks)
{
    uint32_t maxId = 0;

    for (const std::pair<const uint32_t, uint32_t> &entry : masks)
    {
        if ((entry.second & faceAttributeBit(FaceAttribute::Invisible)) == 0)
        {
            continue;
        }

        maxId = std::max(maxId, entry.first);
    }

    return maxId;
}

std::vector<size_t> resolveTargetMemberIndices(const PartySelector &selector, const Party *pParty)
{
    std::vector<size_t> result;

    if (pParty == nullptr)
    {
        return result;
    }

    if (selector.kind == PartySelectorKind::Member)
    {
        if (selector.memberIndex < pParty->members().size())
        {
            result.push_back(selector.memberIndex);
        }

        return result;
    }

    if (selector.kind == PartySelectorKind::Current)
    {
        if (!pParty->members().empty())
        {
            result.push_back(pParty->activeMemberIndex());
        }

        return result;
    }

    if (selector.kind == PartySelectorKind::All)
    {
        for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
        {
            result.push_back(memberIndex);
        }

        return result;
    }

    if (!pParty->members().empty())
    {
        result.push_back(pParty->activeMemberIndex());
    }

    return result;
}

std::optional<size_t> singleTargetMemberIndex(const std::vector<size_t> &targetMemberIndices)
{
    if (targetMemberIndices.size() == 1)
    {
        return targetMemberIndices.front();
    }

    return std::nullopt;
}

bool classIdMatchesPromotionFamily(const Party *pParty, int32_t currentClassId, int32_t compareClassId)
{
    if (currentClassId == compareClassId)
    {
        return true;
    }

    const ClassSkillTable *pClassSkillTable = pParty != nullptr ? pParty->classSkillTable() : nullptr;
    if (pClassSkillTable != nullptr && currentClassId >= 0 && compareClassId >= 0)
    {
        return pClassSkillTable->classIdIsAtLeast(
            static_cast<uint32_t>(currentClassId),
            static_cast<uint32_t>(compareClassId));
    }

    return compareClassId >= 0
        && compareClassId <= 14
        && (compareClassId % 2) == 0
        && currentClassId == compareClassId + 1;
}

std::optional<size_t> luaMemberIndexArgument(lua_State *pLuaState, int argumentIndex)
{
    const Party *pParty = readableParty(pLuaState);

    if (pParty == nullptr || lua_gettop(pLuaState) < argumentIndex || lua_isnil(pLuaState, argumentIndex))
    {
        return pParty != nullptr ? std::optional<size_t>(pParty->activeMemberIndex()) : std::nullopt;
    }

    const lua_Integer rawIndex = luaL_checkinteger(pLuaState, argumentIndex);

    if (rawIndex < 0)
    {
        return std::nullopt;
    }

    return static_cast<size_t>(rawIndex);
}

std::optional<uint32_t> tableBackedClassIdForName(const Party *pParty, const std::string &className)
{
    const ClassSkillTable *pClassSkillTable = pParty != nullptr ? pParty->classSkillTable() : nullptr;

    if (pClassSkillTable != nullptr)
    {
        const std::optional<uint32_t> classId = pClassSkillTable->classIdForName(className);

        if (classId)
        {
            return classId;
        }
    }

    return mm8ClassIdForClassName(className);
}

std::optional<std::string> tableBackedClassNameForId(const Party *pParty, uint32_t classId)
{
    const ClassSkillTable *pClassSkillTable = pParty != nullptr ? pParty->classSkillTable() : nullptr;

    if (pClassSkillTable != nullptr)
    {
        const std::optional<std::string> className = pClassSkillTable->classNameForId(classId);

        if (className)
        {
            return className;
        }
    }

    return classNameForMm8ClassId(classId);
}

std::optional<std::string> luaClassNameArgument(lua_State *pLuaState, int argumentIndex)
{
    const Party *pParty = readableParty(pLuaState);

    if (lua_isinteger(pLuaState, argumentIndex))
    {
        return tableBackedClassNameForId(pParty, static_cast<uint32_t>(lua_tointeger(pLuaState, argumentIndex)));
    }

    if (lua_type(pLuaState, argumentIndex) == LUA_TSTRING)
    {
        const char *pClassName = lua_tostring(pLuaState, argumentIndex);
        const std::string className = canonicalClassName(pClassName != nullptr ? pClassName : "");
        return !className.empty() ? std::optional<std::string>(className) : std::nullopt;
    }

    return std::nullopt;
}

std::vector<size_t> resolvePortraitFxTargetMemberIndices(const Party *pParty, const std::vector<size_t> &targetMemberIndices)
{
    if (pParty == nullptr || pParty->members().empty())
    {
        return {};
    }

    if (!targetMemberIndices.empty())
    {
        return targetMemberIndices;
    }

    return {pParty->activeMemberIndex()};
}

std::optional<SoundId> soundIdForPortraitFxEvent(PortraitFxEventKind kind)
{
    switch (kind)
    {
        case PortraitFxEventKind::AutoNote:
        case PortraitFxEventKind::QuestComplete:
        case PortraitFxEventKind::StatIncrease:
            return SoundId::Quest;

        case PortraitFxEventKind::AwardGain:
            return SoundId::Chimes;

        case PortraitFxEventKind::StatDecrease:
        case PortraitFxEventKind::Disease:
        case PortraitFxEventKind::None:
            return std::nullopt;
    }

    return std::nullopt;
}

bool shouldQueueQuestBitFx(const Party *pParty, uint32_t qbitId, int32_t previousValue, int32_t newValue)
{
    if (pParty == nullptr || previousValue != 0 || newValue == 0)
    {
        return false;
    }

    const JournalQuestTable *pQuestTable = pParty->journalQuestTable();
    return pQuestTable != nullptr && pQuestTable->hasQuestText(qbitId);
}

std::optional<SpeechId> speechIdForLegacyFaceAnimationId(uint32_t faceAnimationId)
{
    switch (faceAnimationId)
    {
        case 1:
            return SpeechId::KillWeakEnemy;
        case 2:
            return SpeechId::KillStrongEnemy;
        case 3:
            return SpeechId::StoreClosed;
        case 4:
            return SpeechId::DisarmTrap;
        case 5:
            return SpeechId::TrapExploded;
        case 7:
            return SpeechId::IdentifyWeakItem;
        case 8:
            return SpeechId::IdentifyGreatItem;
        case 9:
            return SpeechId::IdentifyFailItem;
        case 10:
            return SpeechId::RepairSuccess;
        case 11:
            return SpeechId::RepairFail;
        case 12:
            return SpeechId::SetQuickSpell;
        case 13:
            return SpeechId::CantRestHere;
        case 14:
            return SpeechId::SkillIncreased;
        case 15:
            return SpeechId::InventoryRoom;
        case 16:
            return SpeechId::PotionSuccess;
        case 17:
            return SpeechId::PotionFail;
        case 18:
            return SpeechId::DoorLocked;
        case 20:
            return SpeechId::CantLearnSpell;
        case 21:
            return SpeechId::LearnSpell;
        case 22:
            return SpeechId::HelloDay;
        case 23:
            return SpeechId::HelloEvening;
        case 24:
            return SpeechId::DamageMinor;
        case 27:
            return SpeechId::Poisoned;
        case 29:
            return SpeechId::Insane;
        case 30:
            return SpeechId::Cursed;
        case 31:
            return SpeechId::Drunk;
        case 33:
            return SpeechId::Dying;
        case 36:
            return SpeechId::PotionSuccess;
        case 38:
            return SpeechId::NotEnoughGold;
        case 39:
            return SpeechId::CantEquip;
        case 44:
            return SpeechId::DamagedParty;
        case 45:
            return SpeechId::Hungry;
        case 46:
            return SpeechId::EnterDungeon;
        case 47:
            return SpeechId::LeaveDungeon;
        case 48:
            return SpeechId::Dying;
        case 49:
            return SpeechId::CastSpell;
        case 50:
            return SpeechId::Shoot;
        case 51:
            return SpeechId::AttackHit;
        case 52:
            return SpeechId::AttackMiss;
        case 53:
            return SpeechId::Beg;
        case 54:
            return SpeechId::BegFail;
        case 55:
            return SpeechId::Threat;
        case 56:
            return SpeechId::ThreatFail;
        case 57:
            return SpeechId::Bribe;
        case 58:
            return SpeechId::BribeFail;
        case 59:
            return SpeechId::NpcDontTalk;
        case 60:
            return SpeechId::FoundItem;
        case 61:
            return SpeechId::HireNpc;
        case 65:
            return SpeechId::Yell;
        case 66:
            return SpeechId::Falling;
        case 67:
            return SpeechId::TavernPacksFull;
        case 68:
            return SpeechId::TavernDrink;
        case 69:
            return SpeechId::TavernGotDrunk;
        case 70:
            return SpeechId::TavernTip;
        case 71:
            return SpeechId::TravelHorse;
        case 72:
            return SpeechId::TravelBoat;
        case 73:
            return SpeechId::ShopIdentify;
        case 74:
            return SpeechId::ShopRepair;
        case 75:
            return SpeechId::ShopItemBought;
        case 76:
            return SpeechId::AlreadyIdentified;
        case 77:
            return SpeechId::ItemSold;
        case 78:
            return SpeechId::SkillLearned;
        case 79:
            return SpeechId::WrongShop;
        case 80:
            return SpeechId::ShopRude;
        case 81:
            return SpeechId::BankDeposit;
        case 82:
            return SpeechId::TempleHeal;
        case 83:
            return SpeechId::TempleDonate;
        case 84:
            return SpeechId::HelloHouse;
        case 85:
            return SpeechId::SkillMasteryIncreased;
        case 86:
            return SpeechId::JoinedGuild;
        case 87:
            return SpeechId::LevelUp;
        case 91:
            return SpeechId::StatBonusIncreased;
        case 92:
            return SpeechId::StatBaseIncreased;
        case 93:
            return SpeechId::QuestGot;
        case 96:
            return SpeechId::AwardGot;
        case 98:
            return SpeechId::AfraidSilent;
        case 99:
            return SpeechId::CheatedDeath;
        case 100:
            return SpeechId::InPrison;
        case 102:
            return SpeechId::SelectCharacter;
        case 103:
            return SpeechId::Awaken;
        case 104:
            return SpeechId::IdentifyMonsterWeak;
        case 105:
            return SpeechId::IdentifyMonsterBig;
        case 106:
            return SpeechId::IdentifyMonsterFail;
        case 107:
            return SpeechId::LastPersonStanding;
        case 108:
            return SpeechId::Hungry;
        case 109:
            return SpeechId::DeathBlow;

        default:
            return std::nullopt;
    }
}

void queuePortraitFxRequest(
    EventRuntimeState &runtimeState,
    PortraitFxEventKind kind,
    const Party *pParty,
    const std::vector<size_t> &targetMemberIndices)
{
    if (kind == PortraitFxEventKind::None)
    {
        return;
    }

    const std::vector<size_t> memberIndices = resolvePortraitFxTargetMemberIndices(pParty, targetMemberIndices);

    if (memberIndices.empty())
    {
        return;
    }

    for (EventRuntimeState::PortraitFxRequest &request : runtimeState.portraitFxRequests)
    {
        if (request.kind != kind)
        {
            continue;
        }

        for (size_t memberIndex : memberIndices)
        {
            if (std::find(request.memberIndices.begin(), request.memberIndices.end(), memberIndex)
                == request.memberIndices.end())
            {
                request.memberIndices.push_back(memberIndex);
            }
        }

        return;
    }

    EventRuntimeState::PortraitFxRequest request = {};
    request.kind = kind;
    request.memberIndices = memberIndices;
    runtimeState.portraitFxRequests.push_back(std::move(request));

    if (const std::optional<SoundId> soundId = soundIdForPortraitFxEvent(kind))
    {
        const uint32_t rawSoundId = static_cast<uint32_t>(*soundId);
        const bool alreadyQueued = std::any_of(
            runtimeState.pendingSounds.begin(),
            runtimeState.pendingSounds.end(),
            [rawSoundId](const EventRuntimeState::PendingSound &sound)
            {
                return sound.kind == EventRuntimeState::PendingSound::Kind::PlayOneShot
                    && !sound.positional
                    && sound.soundScope == SoundScope::Engine
                    && sound.soundId == rawSoundId;
            });

        if (alreadyQueued)
        {
            return;
        }

        EventRuntimeState::PendingSound sound = {};
        sound.soundId = rawSoundId;
        sound.positional = false;
        runtimeState.pendingSounds.push_back(sound);
    }
}

std::optional<std::string> permanentVariableDisplayName(uint32_t rawId)
{
    switch (static_cast<EvtVariable>(rawId))
    {
        case EvtVariable::BaseMight: return "Might";
        case EvtVariable::BaseIntellect: return "Intellect";
        case EvtVariable::BasePersonality: return "Personality";
        case EvtVariable::BaseEndurance: return "Endurance";
        case EvtVariable::BaseSpeed: return "Speed";
        case EvtVariable::BaseAccuracy: return "Accuracy";
        case EvtVariable::BaseLuck: return "Luck";
        case EvtVariable::FireResistance: return "Fire Resistance";
        case EvtVariable::AirResistance: return "Air Resistance";
        case EvtVariable::WaterResistance: return "Water Resistance";
        case EvtVariable::EarthResistance: return "Earth Resistance";
        case EvtVariable::SpiritResistance: return "Spirit Resistance";
        case EvtVariable::MindResistance: return "Mind Resistance";
        case EvtVariable::BodyResistance: return "Body Resistance";
        case EvtVariable::LightResistance: return "Light Resistance";
        case EvtVariable::DarkResistance: return "Dark Resistance";
        case EvtVariable::MagicResistance: return "Magic Resistance";
        case EvtVariable::PhysicalResistance: return "Physical Resistance";
        default: return std::nullopt;
    }
}

std::optional<std::string> formatPermanentVariableStatusText(uint32_t rawId, int32_t delta)
{
    if (delta <= 0)
    {
        return std::nullopt;
    }

    const std::optional<std::string> name = permanentVariableDisplayName(rawId);

    if (!name)
    {
        return std::nullopt;
    }

    return *name + " +" + std::to_string(delta) + " (Permanent)";
}

void queuePermanentVariableStatusMessage(
    EventRuntimeState &runtimeState,
    uint32_t rawId,
    int32_t delta,
    size_t repeatCount
)
{
    const std::optional<std::string> text = formatPermanentVariableStatusText(rawId, delta);

    if (!text)
    {
        return;
    }

    const size_t count = std::max<size_t>(1, repeatCount);

    for (size_t i = 0; i < count; ++i)
    {
        runtimeState.statusMessages.push_back(*text);
    }
}

Character *resolveCharacterForVariableWrite(Party *pParty, const std::optional<size_t> &memberIndex)
{
    if (pParty == nullptr || !memberIndex.has_value())
    {
        return nullptr;
    }

    return pParty->member(*memberIndex);
}

const Character *resolveCharacterForVariableRead(const Party *pParty, const std::optional<size_t> &memberIndex)
{
    if (pParty == nullptr || !memberIndex.has_value())
    {
        return nullptr;
    }

    return pParty->member(*memberIndex);
}

bool removeInventoryItemFromTargets(Party &party, const std::vector<size_t> &targetMemberIndices, uint32_t objectDescriptionId)
{
    for (size_t memberIndex : targetMemberIndices)
    {
        if (party.removeItemFromMember(memberIndex, objectDescriptionId))
        {
            return true;
        }
    }

    return false;
}

std::optional<CharacterCondition> conditionForEvtVariable(EvtVariable variableId)
{
    switch (variableId)
    {
        case EvtVariable::Cursed: return CharacterCondition::Cursed;
        case EvtVariable::Weak: return CharacterCondition::Weak;
        case EvtVariable::Asleep: return CharacterCondition::Asleep;
        case EvtVariable::Afraid: return CharacterCondition::Fear;
        case EvtVariable::Drunk: return CharacterCondition::Drunk;
        case EvtVariable::Insane: return CharacterCondition::Insane;
        case EvtVariable::PoisonedGreen: return CharacterCondition::PoisonWeak;
        case EvtVariable::DiseasedGreen: return CharacterCondition::DiseaseWeak;
        case EvtVariable::PoisonedYellow: return CharacterCondition::PoisonMedium;
        case EvtVariable::DiseasedYellow: return CharacterCondition::DiseaseMedium;
        case EvtVariable::PoisonedRed: return CharacterCondition::PoisonSevere;
        case EvtVariable::DiseasedRed: return CharacterCondition::DiseaseSevere;
        case EvtVariable::Paralyzed: return CharacterCondition::Paralyzed;
        case EvtVariable::Unconscious: return CharacterCondition::Unconscious;
        case EvtVariable::Dead: return CharacterCondition::Dead;
        case EvtVariable::Stoned: return CharacterCondition::Petrified;
        case EvtVariable::Eradicated: return CharacterCondition::Eradicated;
        default: return std::nullopt;
    }
}

bool isPoisonOrDiseaseCondition(CharacterCondition condition)
{
    return condition == CharacterCondition::PoisonWeak
        || condition == CharacterCondition::PoisonMedium
        || condition == CharacterCondition::PoisonSevere
        || condition == CharacterCondition::DiseaseWeak
        || condition == CharacterCondition::DiseaseMedium
        || condition == CharacterCondition::DiseaseSevere;
}

std::optional<std::string> skillNameForEvtVariable(EvtVariable variableId)
{
    switch (variableId)
    {
        case EvtVariable::StaffSkill: return "Staff";
        case EvtVariable::SwordSkill: return "Sword";
        case EvtVariable::DaggerSkill: return "Dagger";
        case EvtVariable::AxeSkill: return "Axe";
        case EvtVariable::SpearSkill: return "Spear";
        case EvtVariable::BowSkill: return "Bow";
        case EvtVariable::MaceSkill: return "Mace";
        case EvtVariable::BlasterSkill: return "Blaster";
        case EvtVariable::ShieldSkill: return "Shield";
        case EvtVariable::LeatherSkill: return "LeatherArmor";
        case EvtVariable::ChainSkill: return "ChainArmor";
        case EvtVariable::PlateSkill: return "PlateArmor";
        case EvtVariable::FireSkill: return "FireMagic";
        case EvtVariable::AirSkill: return "AirMagic";
        case EvtVariable::WaterSkill: return "WaterMagic";
        case EvtVariable::EarthSkill: return "EarthMagic";
        case EvtVariable::SpiritSkill: return "SpiritMagic";
        case EvtVariable::MindSkill: return "MindMagic";
        case EvtVariable::BodySkill: return "BodyMagic";
        case EvtVariable::LightSkill: return "LightMagic";
        case EvtVariable::DarkSkill: return "DarkMagic";
        case EvtVariable::IdentifyItemSkill: return "IdentifyItem";
        case EvtVariable::MerchantSkill: return "Merchant";
        case EvtVariable::RepairSkill: return "RepairItem";
        case EvtVariable::BodybuildingSkill: return "Bodybuilding";
        case EvtVariable::MeditationSkill: return "Meditation";
        case EvtVariable::PerceptionSkill: return "Perception";
        case EvtVariable::DiplomacySkill: return "Diplomacy";
        case EvtVariable::ThieverySkill: return "Thievery";
        case EvtVariable::DisarmTrapSkill: return "DisarmTraps";
        case EvtVariable::DodgeSkill: return "Dodging";
        case EvtVariable::UnarmedSkill: return "Unarmed";
        case EvtVariable::IdentifyMonsterSkill: return "IdentifyMonster";
        case EvtVariable::ArmsmasterSkill: return "Armsmaster";
        case EvtVariable::StealingSkill: return "Stealing";
        case EvtVariable::AlchemySkill: return "Alchemy";
        case EvtVariable::LearningSkill: return "Learning";
        default: return std::nullopt;
    }
}

SkillMastery masteryFromJoinedValue(uint16_t joinedValue)
{
    if ((joinedValue & static_cast<uint16_t>(EvtSkillJoinedMask::Master)) != 0)
    {
        return SkillMastery::Grandmaster;
    }

    if ((joinedValue & static_cast<uint16_t>(EvtSkillJoinedMask::Expert)) != 0)
    {
        return SkillMastery::Master;
    }

    if ((joinedValue & static_cast<uint16_t>(EvtSkillJoinedMask::Normal)) != 0)
    {
        return SkillMastery::Expert;
    }

    return (joinedValue & static_cast<uint16_t>(EvtSkillJoinedMask::Level)) != 0
        ? SkillMastery::Normal
        : SkillMastery::None;
}

uint16_t joinedSkillValue(uint32_t level, SkillMastery mastery)
{
    uint16_t joinedValue = static_cast<uint16_t>(
        std::min<uint32_t>(level, static_cast<uint16_t>(EvtSkillJoinedMask::Level)));

    switch (mastery)
    {
        case SkillMastery::Expert:
            joinedValue |= static_cast<uint16_t>(EvtSkillJoinedMask::Normal);
            break;

        case SkillMastery::Master:
            joinedValue |= static_cast<uint16_t>(EvtSkillJoinedMask::Expert);
            break;

        case SkillMastery::Grandmaster:
            joinedValue |= static_cast<uint16_t>(EvtSkillJoinedMask::Master);
            break;

        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            break;
    }

    return joinedValue;
}

EvtSeason currentSeasonFromRuntimeState(const EventRuntimeState &runtimeState)
{
    const int currentDayOfYear = std::max(1, currentGameMinutesFromRuntimeState(runtimeState) / (60 * 24));
    const int monthIndex = (resolveMonthFromDayOfYear(currentDayOfYear) - 1) % 12;

    if (monthIndex <= 2)
    {
        return EvtSeason::Spring;
    }

    if (monthIndex <= 5)
    {
        return EvtSeason::Summer;
    }

    if (monthIndex <= 8)
    {
        return EvtSeason::Autumn;
    }

    return EvtSeason::Winter;
}

uint32_t randomJumpSeed(uint16_t eventId, uint8_t step, const EventRuntimeState &runtimeState)
{
    return static_cast<uint32_t>(eventId) * 2654435761u
        ^ static_cast<uint32_t>(step) * 40503u
        ^ static_cast<uint32_t>(std::max(0, currentGameMinutesFromRuntimeState(runtimeState)));
}

uint32_t nextEventRandom(uint16_t eventId, uint8_t step, EventRuntimeState &runtimeState)
{
    if (runtimeState.eventRandomState == 0)
    {
        runtimeState.eventRandomState = randomJumpSeed(eventId, step, runtimeState);
    }

    runtimeState.eventRandomState = runtimeState.eventRandomState * 1664525u + 1013904223u;
    return runtimeState.eventRandomState;
}

std::optional<PortraitId> eventPortraitId(uint32_t rawPortraitId)
{
    if (rawPortraitId == 0)
    {
        return std::nullopt;
    }

    const PortraitId portraitId = static_cast<PortraitId>(rawPortraitId);
    return portraitId == PortraitId::Invalid ? std::nullopt : std::optional<PortraitId>(portraitId);
}

uint32_t eventReferenceId(lua_Integer rawId)
{
    if (rawId < 0)
    {
        const int64_t signedId = static_cast<int64_t>(rawId);
        const uint64_t magnitude = static_cast<uint64_t>(-(signedId + 1)) + 1;
        return static_cast<uint32_t>(magnitude);
    }

    const uint64_t unsignedId = static_cast<uint64_t>(rawId);

    if (unsignedId > static_cast<uint64_t>(std::numeric_limits<int32_t>::max())
        && unsignedId <= static_cast<uint64_t>(std::numeric_limits<uint32_t>::max()))
    {
        const int64_t signedId = static_cast<int64_t>(unsignedId) -
            (static_cast<int64_t>(std::numeric_limits<uint32_t>::max()) + 1);
        return static_cast<uint32_t>(signedId < 0 ? -signedId : signedId);
    }

    return static_cast<uint32_t>(rawId);
}

std::string damageStatusForEvtVariable(const std::vector<size_t> &targetMemberIndices)
{
    return targetMemberIndices.size() > 1 ? "event damaged party" : "event damaged member";
}

void queuePendingSound(
    EventRuntimeState &runtimeState,
    uint32_t soundId,
    int32_t x,
    int32_t y,
    bool positional)
{
    if (soundId == 0)
    {
        return;
    }

    EventRuntimeState::PendingSound request = {};
    request.soundId = soundId;
    request.soundScope = soundId >= 30000 ? SoundScope::World : SoundScope::Engine;
    request.x = x;
    request.y = y;
    request.positional = positional;
    runtimeState.pendingSounds.push_back(std::move(request));
}

std::optional<std::string> skillNameForCheckSkillArgument(uint32_t rawSkillId)
{
    switch (rawSkillId)
    {
        case 29:
        case 31:
            return "Perception";
        case 33:
            return "DisarmTraps";
        default:
            break;
    }

    return skillNameForEvtVariable(static_cast<EvtVariable>(rawSkillId));
}

int masteryEffectiveMultiplier(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Expert: return 2;
        case SkillMastery::Master: return 3;
        case SkillMastery::Grandmaster: return 5;
        case SkillMastery::Normal: return 1;
        case SkillMastery::None:
        default:
            return 0;
    }
}

int characterEffectiveSkillCheckValue(const Character &member, const std::string &skillName)
{
    if (skillName == "Perception")
    {
        return GameMechanics::resolveCharacterPerceptionValue(member);
    }

    if (skillName == "DisarmTraps")
    {
        return GameMechanics::resolveCharacterDisarmTrapValue(member);
    }

    if (!GameMechanics::canAct(member))
    {
        return 0;
    }

    const CharacterSkill *pSkill = member.findSkill(skillName);

    if (pSkill == nullptr || pSkill->level == 0 || pSkill->mastery == SkillMastery::None)
    {
        return 0;
    }

    return static_cast<int>(pSkill->level) * masteryEffectiveMultiplier(pSkill->mastery);
}

bool characterMeetsSkillCheck(
    const Character &member,
    const std::string &skillName,
    uint32_t rawMastery,
    uint32_t level)
{
    const CharacterSkill *pSkill = member.findSkill(skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    if (rawMastery == 0)
    {
        return characterEffectiveSkillCheckValue(member, skillName) >= static_cast<int>(level);
    }

    const SkillMastery mastery = normalizeCheckSkillMastery(rawMastery);
    return pSkill->mastery >= mastery
        && characterEffectiveSkillCheckValue(member, skillName) >= static_cast<int>(level);
}

bool characterHasLearnedSkill(const Character &member, const std::string &skillName)
{
    const CharacterSkill *pSkill = member.findSkill(skillName);
    return pSkill != nullptr && pSkill->level > 0 && pSkill->mastery != SkillMastery::None;
}

SkillMastery normalizeCheckSkillMastery(uint32_t rawMastery)
{
    switch (rawMastery)
    {
        case 1: return SkillMastery::Expert;
        case 2: return SkillMastery::Master;
        default: return SkillMastery::Grandmaster;
    }
}

int resolveCharacterAge(const Character &member)
{
    if (member.birthYear > 0 && member.birthYear <= static_cast<uint32_t>(OeGameStartingYear))
    {
        return std::max(0, OeGameStartingYear - static_cast<int>(member.birthYear) + member.ageModifier);
    }

    return std::max(0, member.ageModifier);
}

int resolveMonthFromDayOfYear(int dayOfYear)
{
    const int normalizedDayOfYear = std::max(1, dayOfYear);
    return ((normalizedDayOfYear - 1) / OeDaysPerMonth) + 1;
}

int currentGameMinutesFromRuntimeState(const EventRuntimeState &runtimeState)
{
    const auto hourIt = runtimeState.variables.find(static_cast<uint32_t>(EvtVariable::Hour));
    const auto dayIt = runtimeState.variables.find(static_cast<uint32_t>(EvtVariable::DayOfYear));
    const int hour = hourIt != runtimeState.variables.end() ? std::max(0, hourIt->second) : 0;
    const int dayOfYear = dayIt != runtimeState.variables.end() ? std::max(1, dayIt->second) : 1;
    return ((dayOfYear - 1) * 24 + hour) * 60;
}

float conditionStartGameMinutes(
    const EventRuntimeState &runtimeState,
    const ISceneEventContext *pSceneEventContext)
{
    if (pSceneEventContext != nullptr)
    {
        return std::max(0.0f, pSceneEventContext->currentGameMinutes());
    }

    return static_cast<float>(currentGameMinutesFromRuntimeState(runtimeState));
}

bool isTradingTriangleBuyTopic(uint16_t topicId)
{
    switch (topicId)
    {
        case 250:
        case 252:
        case 254:
        case 256:
        case 258:
        case 260:
        case 262:
        case 264:
        case 266:
            return true;

        default:
            return false;
    }
}

int resolveCharacterBaseArmorClass(const Character &member, const Party *pParty)
{
    if (pParty == nullptr)
    {
        return member.armorClassModifier;
    }

    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
        member,
        pParty->itemTable(),
        pParty->standardItemEnchantTable(),
        pParty->specialItemEnchantTable());
    return summary.armorClass.base + member.armorClassModifier;
}

int resolveCharacterActualArmorClass(const Character &member, const Party *pParty)
{
    if (pParty == nullptr)
    {
        return member.armorClassModifier;
    }

    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
        member,
        pParty->itemTable(),
        pParty->standardItemEnchantTable(),
        pParty->specialItemEnchantTable());
    return summary.armorClass.actual + member.armorClassModifier;
}

int resolveCharacterMajorConditionValue(const Character &member)
{
    for (int conditionIndex = static_cast<int>(CharacterCondition::Eradicated);
         conditionIndex >= static_cast<int>(CharacterCondition::Cursed);
         --conditionIndex)
    {
        if (member.conditions.test(static_cast<size_t>(conditionIndex)))
        {
            return conditionIndex;
        }
    }

    return 0;
}

bool activePartyHasRosterMember(const Party *pParty, uint32_t rosterId)
{
    if (pParty == nullptr || rosterId == 0)
    {
        return false;
    }

    for (const Character &member : pParty->members())
    {
        if (member.rosterId == rosterId)
        {
            return true;
        }
    }

    return false;
}

int32_t readCharacterVariableValue(const Character &member, uint32_t rawId)
{
    switch (static_cast<EvtVariable>(rawId & 0xFFFFu))
    {
        case EvtVariable::MightBonus:
        case EvtVariable::ActualMight:
            return member.permanentBonuses.might;

        case EvtVariable::IntellectBonus:
        case EvtVariable::ActualIntellect:
            return member.permanentBonuses.intellect;

        case EvtVariable::PersonalityBonus:
        case EvtVariable::ActualPersonality:
            return member.permanentBonuses.personality;

        case EvtVariable::EnduranceBonus:
        case EvtVariable::ActualEndurance:
            return member.permanentBonuses.endurance;

        case EvtVariable::SpeedBonus:
        case EvtVariable::ActualSpeed:
            return member.permanentBonuses.speed;

        case EvtVariable::AccuracyBonus:
        case EvtVariable::ActualAccuracy:
            return member.permanentBonuses.accuracy;

        case EvtVariable::LuckBonus:
        case EvtVariable::ActualLuck:
            return member.permanentBonuses.luck;

        case EvtVariable::BaseMight:
            return static_cast<int32_t>(member.might);

        case EvtVariable::BaseIntellect:
            return static_cast<int32_t>(member.intellect);

        case EvtVariable::BasePersonality:
            return static_cast<int32_t>(member.personality);

        case EvtVariable::BaseEndurance:
            return static_cast<int32_t>(member.endurance);

        case EvtVariable::BaseSpeed:
            return static_cast<int32_t>(member.speed);

        case EvtVariable::BaseAccuracy:
            return static_cast<int32_t>(member.accuracy);

        case EvtVariable::BaseLuck:
            return static_cast<int32_t>(member.luck);

        case EvtVariable::FireResistance:
            return member.baseResistances.fire;

        case EvtVariable::AirResistance:
            return member.baseResistances.air;

        case EvtVariable::WaterResistance:
            return member.baseResistances.water;

        case EvtVariable::EarthResistance:
            return member.baseResistances.earth;

        case EvtVariable::SpiritResistance:
            return member.baseResistances.spirit;

        case EvtVariable::MindResistance:
            return member.baseResistances.mind;

        case EvtVariable::BodyResistance:
            return member.baseResistances.body;

        case EvtVariable::LightResistance:
            return member.baseResistances.light;

        case EvtVariable::DarkResistance:
            return member.baseResistances.dark;

        case EvtVariable::PhysicalResistance:
            return member.baseResistances.physical;

        case EvtVariable::MagicResistance:
            return member.baseResistances.magic;

        case EvtVariable::FireResistanceBonus:
            return member.permanentBonuses.resistances.fire;

        case EvtVariable::AirResistanceBonus:
            return member.permanentBonuses.resistances.air;

        case EvtVariable::WaterResistanceBonus:
            return member.permanentBonuses.resistances.water;

        case EvtVariable::EarthResistanceBonus:
            return member.permanentBonuses.resistances.earth;

        case EvtVariable::SpiritResistanceBonus:
            return member.permanentBonuses.resistances.spirit;

        case EvtVariable::MindResistanceBonus:
            return member.permanentBonuses.resistances.mind;

        case EvtVariable::BodyResistanceBonus:
            return member.permanentBonuses.resistances.body;

        case EvtVariable::LightResistanceBonus:
            return member.permanentBonuses.resistances.light;

        case EvtVariable::DarkResistanceBonus:
            return member.permanentBonuses.resistances.dark;

        case EvtVariable::PhysicalResistanceBonus:
            return member.permanentBonuses.resistances.physical;

        case EvtVariable::MagicResistanceBonus:
            return member.permanentBonuses.resistances.magic;

        default: break;
    }

    return 0;
}

int32_t readCharacterActualStatValue(const Character &member, uint32_t rawId, const Party *pParty)
{
    return GameMechanics::resolveCharacterDisplayedActualPrimaryStat(
        member,
        rawId & 0xFFFFu,
        pParty != nullptr ? pParty->itemTable() : nullptr,
        pParty != nullptr ? pParty->standardItemEnchantTable() : nullptr,
        pParty != nullptr ? pParty->specialItemEnchantTable() : nullptr);
}

void writeCharacterVariableValue(Character &member, uint32_t rawId, int32_t value)
{
    const int clampedValue = std::clamp(value, 0, 255);

    switch (static_cast<EvtVariable>(rawId & 0xFFFFu))
    {
        case EvtVariable::MightBonus:
        case EvtVariable::ActualMight:
            member.permanentBonuses.might = clampedValue;
            return;

        case EvtVariable::IntellectBonus:
        case EvtVariable::ActualIntellect:
            member.permanentBonuses.intellect = clampedValue;
            return;

        case EvtVariable::PersonalityBonus:
        case EvtVariable::ActualPersonality:
            member.permanentBonuses.personality = clampedValue;
            return;

        case EvtVariable::EnduranceBonus:
        case EvtVariable::ActualEndurance:
            member.permanentBonuses.endurance = clampedValue;
            return;

        case EvtVariable::SpeedBonus:
        case EvtVariable::ActualSpeed:
            member.permanentBonuses.speed = clampedValue;
            return;

        case EvtVariable::AccuracyBonus:
        case EvtVariable::ActualAccuracy:
            member.permanentBonuses.accuracy = clampedValue;
            return;

        case EvtVariable::LuckBonus:
        case EvtVariable::ActualLuck:
            member.permanentBonuses.luck = clampedValue;
            return;

        case EvtVariable::BaseMight:
            member.might = clampedValue;
            return;

        case EvtVariable::BaseIntellect:
            member.intellect = clampedValue;
            return;

        case EvtVariable::BasePersonality:
            member.personality = clampedValue;
            return;

        case EvtVariable::BaseEndurance:
            member.endurance = clampedValue;
            return;

        case EvtVariable::BaseSpeed:
            member.speed = clampedValue;
            return;

        case EvtVariable::BaseAccuracy:
            member.accuracy = clampedValue;
            return;

        case EvtVariable::BaseLuck:
            member.luck = clampedValue;
            return;

        case EvtVariable::FireResistance:
            member.baseResistances.fire = clampedValue;
            return;

        case EvtVariable::AirResistance:
            member.baseResistances.air = clampedValue;
            return;

        case EvtVariable::WaterResistance:
            member.baseResistances.water = clampedValue;
            return;

        case EvtVariable::EarthResistance:
            member.baseResistances.earth = clampedValue;
            return;

        case EvtVariable::SpiritResistance:
            member.baseResistances.spirit = clampedValue;
            return;

        case EvtVariable::MindResistance:
            member.baseResistances.mind = clampedValue;
            return;

        case EvtVariable::BodyResistance:
            member.baseResistances.body = clampedValue;
            return;

        case EvtVariable::LightResistance:
            member.baseResistances.light = clampedValue;
            return;

        case EvtVariable::DarkResistance:
            member.baseResistances.dark = clampedValue;
            return;

        case EvtVariable::PhysicalResistance:
            member.baseResistances.physical = clampedValue;
            return;

        case EvtVariable::MagicResistance:
            member.baseResistances.magic = clampedValue;
            return;

        case EvtVariable::FireResistanceBonus:
            member.permanentBonuses.resistances.fire = clampedValue;
            return;

        case EvtVariable::AirResistanceBonus:
            member.permanentBonuses.resistances.air = clampedValue;
            return;

        case EvtVariable::WaterResistanceBonus:
            member.permanentBonuses.resistances.water = clampedValue;
            return;

        case EvtVariable::EarthResistanceBonus:
            member.permanentBonuses.resistances.earth = clampedValue;
            return;

        case EvtVariable::SpiritResistanceBonus:
            member.permanentBonuses.resistances.spirit = clampedValue;
            return;

        case EvtVariable::MindResistanceBonus:
            member.permanentBonuses.resistances.mind = clampedValue;
            return;

        case EvtVariable::BodyResistanceBonus:
            member.permanentBonuses.resistances.body = clampedValue;
            return;

        case EvtVariable::LightResistanceBonus:
            member.permanentBonuses.resistances.light = clampedValue;
            return;

        case EvtVariable::DarkResistanceBonus:
            member.permanentBonuses.resistances.dark = clampedValue;
            return;

        case EvtVariable::PhysicalResistanceBonus:
            member.permanentBonuses.resistances.physical = clampedValue;
            return;

        case EvtVariable::MagicResistanceBonus:
            member.permanentBonuses.resistances.magic = clampedValue;
            return;

        default: break;
    }
}

int resolveCharacterEffectiveMaxHealth(const Character &member)
{
    return GameMechanics::calculateEffectiveCharacterMaxHealth(member);
}

int resolveCharacterEffectiveMaxSpellPoints(const Character &member)
{
    return GameMechanics::calculateEffectiveCharacterMaxSpellPoints(member);
}

int floorToInt(float value)
{
    return static_cast<int>(std::floor(value));
}

void syncTimeVariablesFromSceneContext(EventRuntimeState &runtimeState, const ISceneEventContext *pSceneEventContext)
{
    if (pSceneEventContext == nullptr)
    {
        return;
    }

    constexpr int MinutesPerDay = 24 * 60;
    const int totalMinutes = std::max(0, floorToInt(pSceneEventContext->currentGameMinutes()));
    const int totalDays = totalMinutes / MinutesPerDay;
    runtimeState.variables[static_cast<uint32_t>(EvtVariable::Hour)] = (totalMinutes / 60) % 24;
    runtimeState.variables[static_cast<uint32_t>(EvtVariable::DayOfYear)] = (totalDays % OeDaysPerYear) + 1;
    runtimeState.variables[static_cast<uint32_t>(EvtVariable::DayOfWeek)] = totalDays % OeDaysPerWeek;
}
}

EventRuntime::VariableRef EventRuntime::decodeVariable(uint32_t rawId)
{
    VariableRef variable = {};
    variable.rawId = rawId;
    variable.tag = static_cast<uint16_t>(rawId & 0xFFFF);
    variable.index = rawId >> 16;

    if (variable.tag == 0x013Cu)
    {
        variable.tag = static_cast<uint16_t>(EvtVariable::Invisible);
    }
    else if (variable.tag == 0x013Du)
    {
        variable.tag = static_cast<uint16_t>(EvtVariable::ItemEquipped);
    }

    const EvtVariable variableId = static_cast<EvtVariable>(variable.tag);

    if (variableId == EvtVariable::QBits)
    {
        variable.kind = VariableKind::QBits;
        variable.rawId = variable.index;
        return variable;
    }

    if (variableId == EvtVariable::Inventory)
    {
        variable.kind = VariableKind::Inventory;
        variable.rawId = variable.index;
        return variable;
    }

    if (variableId == EvtVariable::Awards)
    {
        variable.kind = VariableKind::Awards;
        return variable;
    }

    if (variableId == EvtVariable::Players)
    {
        variable.kind = VariableKind::Players;
        return variable;
    }

    if (variableId >= EvtVariable::MapPersistentVariableBegin && variableId <= EvtVariable::MapPersistentVariableEnd)
    {
        variable.kind = VariableKind::MapPersistent;
        variable.index = static_cast<uint32_t>(variableId)
            - static_cast<uint32_t>(EvtVariable::MapPersistentVariableBegin);
        variable.rawId = variable.index;
        return variable;
    }

    if (variableId >= EvtVariable::MapPersistentDecorVariableBegin
        && variableId <= EvtVariable::MapPersistentDecorVariableEnd)
    {
        variable.kind = VariableKind::DecorPersistent;
        variable.index = static_cast<uint32_t>(variableId)
            - static_cast<uint32_t>(EvtVariable::MapPersistentDecorVariableBegin);
        variable.rawId = variable.index;
        return variable;
    }

    if (variable.index != 0 && variableId == EvtVariable::IsIntellectMoreThanBase)
    {
        variable.kind = VariableKind::AutoNote;
        variable.rawId = rawId;
        return variable;
    }

    if (variable.index != 0 && variableId == EvtVariable::AutoNotes)
    {
        variable.kind = VariableKind::AutoNote;
        variable.rawId = rawId;
        return variable;
    }

    if (variable.index != 0 && variable.tag == 0x00E9u)
    {
        variable.kind = VariableKind::BoolFlag;
        variable.rawId = rawId;
        return variable;
    }

    if (variableId >= EvtVariable::HistoryBegin && variableId <= EvtVariable::HistoryEnd)
    {
        variable.kind = VariableKind::History;
        variable.rawId = static_cast<uint32_t>(variableId);
        variable.index = static_cast<uint32_t>(variableId)
            - static_cast<uint32_t>(EvtVariable::HistoryBegin) + 1;
        return variable;
    }

    switch (variableId)
    {
        case EvtVariable::Food:
        case EvtVariable::RandomFood:
            variable.kind = VariableKind::Food;
            break;

        case EvtVariable::AutoNotes:
            variable.kind = VariableKind::AutoNote;
            break;

        case EvtVariable::ClassId:
            variable.kind = VariableKind::ClassId;
            break;

        case EvtVariable::Experience:
            variable.kind = VariableKind::Experience;
            break;

        case EvtVariable::CurrentHealth:
            variable.kind = VariableKind::CurrentHealth;
            break;

        case EvtVariable::MaxHealth:
            variable.kind = VariableKind::MaxHealth;
            break;

        case EvtVariable::CurrentSpellPoints:
            variable.kind = VariableKind::CurrentSpellPoints;
            break;

        case EvtVariable::MaxSpellPoints:
            variable.kind = VariableKind::MaxSpellPoints;
            break;

        case EvtVariable::Hour:
            variable.kind = VariableKind::Hour;
            break;

        case EvtVariable::DayOfYear:
            variable.kind = VariableKind::DayOfYear;
            break;

        case EvtVariable::DayOfWeek:
            variable.kind = VariableKind::DayOfWeek;
            break;

        case EvtVariable::Gold:
        case EvtVariable::RandomGold:
            variable.kind = VariableKind::Gold;
            break;

        case EvtVariable::GoldInBank:
            variable.kind = VariableKind::GoldInBank;
            break;

        case EvtVariable::BaseLevel:
            variable.kind = VariableKind::BaseLevel;
            break;

        case EvtVariable::LevelBonus:
            variable.kind = VariableKind::LevelBonus;
            break;

        case EvtVariable::Sex:
            variable.kind = VariableKind::Sex;
            break;

        case EvtVariable::Race:
            variable.kind = VariableKind::Race;
            break;

        case EvtVariable::Age:
            variable.kind = VariableKind::Age;
            break;

        case EvtVariable::ActualArmorClass:
            variable.kind = VariableKind::ArmorClass;
            break;

        case EvtVariable::ArmorClassBonus:
            variable.kind = VariableKind::ArmorClassBonus;
            break;

        case EvtVariable::BaseMight:
        case EvtVariable::BaseIntellect:
        case EvtVariable::BasePersonality:
        case EvtVariable::BaseEndurance:
        case EvtVariable::BaseSpeed:
        case EvtVariable::BaseAccuracy:
        case EvtVariable::BaseLuck:
            variable.kind = VariableKind::BaseStat;
            break;

        case EvtVariable::ActualMight:
        case EvtVariable::ActualIntellect:
        case EvtVariable::ActualPersonality:
        case EvtVariable::ActualEndurance:
        case EvtVariable::ActualSpeed:
        case EvtVariable::ActualAccuracy:
        case EvtVariable::ActualLuck:
            variable.kind = VariableKind::ActualStat;
            break;

        case EvtVariable::IsMightMoreThanBase:
        case EvtVariable::IsIntellectMoreThanBase:
        case EvtVariable::IsPersonalityMoreThanBase:
        case EvtVariable::IsEnduranceMoreThanBase:
        case EvtVariable::IsSpeedMoreThanBase:
        case EvtVariable::IsAccuracyMoreThanBase:
        case EvtVariable::IsLuckMoreThanBase:
            variable.kind = VariableKind::StatMoreThanBase;
            break;

        case EvtVariable::MightBonus:
        case EvtVariable::IntellectBonus:
        case EvtVariable::PersonalityBonus:
        case EvtVariable::EnduranceBonus:
        case EvtVariable::SpeedBonus:
        case EvtVariable::AccuracyBonus:
        case EvtVariable::LuckBonus:
            variable.kind = VariableKind::StatBonus;
            break;

        case EvtVariable::FireResistance:
        case EvtVariable::AirResistance:
        case EvtVariable::WaterResistance:
        case EvtVariable::EarthResistance:
        case EvtVariable::SpiritResistance:
        case EvtVariable::MindResistance:
        case EvtVariable::BodyResistance:
        case EvtVariable::LightResistance:
        case EvtVariable::DarkResistance:
        case EvtVariable::PhysicalResistance:
        case EvtVariable::MagicResistance:
            variable.kind = VariableKind::BaseResistance;
            break;

        case EvtVariable::FireResistanceBonus:
        case EvtVariable::AirResistanceBonus:
        case EvtVariable::WaterResistanceBonus:
        case EvtVariable::EarthResistanceBonus:
        case EvtVariable::SpiritResistanceBonus:
        case EvtVariable::MindResistanceBonus:
        case EvtVariable::BodyResistanceBonus:
        case EvtVariable::LightResistanceBonus:
        case EvtVariable::DarkResistanceBonus:
        case EvtVariable::PhysicalResistanceBonus:
        case EvtVariable::MagicResistanceBonus:
            variable.kind = VariableKind::ResistanceBonus;
            break;

        case EvtVariable::StaffSkill:
        case EvtVariable::SwordSkill:
        case EvtVariable::DaggerSkill:
        case EvtVariable::AxeSkill:
        case EvtVariable::SpearSkill:
        case EvtVariable::BowSkill:
        case EvtVariable::MaceSkill:
        case EvtVariable::BlasterSkill:
        case EvtVariable::ShieldSkill:
        case EvtVariable::LeatherSkill:
        case EvtVariable::ChainSkill:
        case EvtVariable::PlateSkill:
        case EvtVariable::FireSkill:
        case EvtVariable::AirSkill:
        case EvtVariable::WaterSkill:
        case EvtVariable::EarthSkill:
        case EvtVariable::SpiritSkill:
        case EvtVariable::MindSkill:
        case EvtVariable::BodySkill:
        case EvtVariable::LightSkill:
        case EvtVariable::DarkSkill:
        case EvtVariable::IdentifyItemSkill:
        case EvtVariable::MerchantSkill:
        case EvtVariable::RepairSkill:
        case EvtVariable::BodybuildingSkill:
        case EvtVariable::MeditationSkill:
        case EvtVariable::PerceptionSkill:
        case EvtVariable::DiplomacySkill:
        case EvtVariable::ThieverySkill:
        case EvtVariable::DisarmTrapSkill:
        case EvtVariable::DodgeSkill:
        case EvtVariable::UnarmedSkill:
        case EvtVariable::IdentifyMonsterSkill:
        case EvtVariable::ArmsmasterSkill:
        case EvtVariable::StealingSkill:
        case EvtVariable::AlchemySkill:
        case EvtVariable::LearningSkill:
            variable.kind = VariableKind::Skill;
            break;

        case EvtVariable::Cursed:
        case EvtVariable::Weak:
        case EvtVariable::Asleep:
        case EvtVariable::Afraid:
        case EvtVariable::Drunk:
        case EvtVariable::Insane:
        case EvtVariable::PoisonedGreen:
        case EvtVariable::DiseasedGreen:
        case EvtVariable::PoisonedYellow:
        case EvtVariable::DiseasedYellow:
        case EvtVariable::PoisonedRed:
        case EvtVariable::DiseasedRed:
        case EvtVariable::Paralyzed:
        case EvtVariable::Unconscious:
        case EvtVariable::Dead:
        case EvtVariable::Stoned:
        case EvtVariable::Eradicated:
            variable.kind = VariableKind::Condition;
            break;

        case EvtVariable::MajorCondition:
            variable.kind = VariableKind::MajorCondition;
            break;

        case EvtVariable::PlayerBits:
        case EvtVariable::Npcs2:
        case EvtVariable::IsFlying:
        case EvtVariable::HiredNpcHasSpeciality:
        case EvtVariable::NumSkillPoints:
        case EvtVariable::MonthIs:
        case EvtVariable::Counter1:
        case EvtVariable::Counter2:
        case EvtVariable::Counter3:
        case EvtVariable::Counter4:
        case EvtVariable::Counter5:
        case EvtVariable::Counter6:
        case EvtVariable::Counter7:
        case EvtVariable::Counter8:
        case EvtVariable::Counter9:
        case EvtVariable::Counter10:
        case EvtVariable::ReputationInCurrentLocation:
        case EvtVariable::Unknown1:
        case EvtVariable::NumDeaths:
        case EvtVariable::NumBounties:
        case EvtVariable::PrisonTerms:
        case EvtVariable::ArenaWinsPage:
        case EvtVariable::ArenaWinsSquire:
        case EvtVariable::ArenaWinsKnight:
        case EvtVariable::ArenaWinsLord:
        case EvtVariable::Invisible:
        case EvtVariable::ItemEquipped:
            variable.kind = VariableKind::PartyState;
            break;

        case EvtVariable::CircusPrises:
            variable.kind = VariableKind::CircusPrises;
            break;

        default:
            variable.kind = VariableKind::Generic;
            break;
    }

    return variable;
}

int32_t EventRuntime::getVariableValue(
    const EventRuntimeState &runtimeState,
    const VariableRef &variable,
    const Party *pParty,
    const std::optional<size_t> &memberIndex,
    const ISceneEventContext *pSceneEventContext
)
{
    const EvtVariable variableId = static_cast<EvtVariable>(variable.tag);

    if (variable.kind == VariableKind::Inventory)
    {
        return getInventoryItemCount(runtimeState, pParty, variable.rawId, memberIndex);
    }

    if (variable.kind == VariableKind::Players)
    {
        if (pParty == nullptr)
        {
            return 0;
        }

        return pParty->hasRosterMember(variable.index) ? static_cast<int32_t>(variable.index) : 0;
    }

    if (variable.kind == VariableKind::Food)
    {
        if (pParty != nullptr)
        {
            return pParty->food();
        }

        const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
        return iterator != runtimeState.variables.end() ? iterator->second : 0;
    }

    if (variable.kind == VariableKind::AutoNote)
    {
        const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
        return iterator != runtimeState.variables.end() ? iterator->second : 0;
    }

    if (variable.kind == VariableKind::History)
    {
        const std::unordered_map<uint32_t, int32_t> &historyTimes =
            historyEventTimesForContinent(runtimeState, runtimeState.activeHistoryContinentId);
        return historyTimes.find(variable.index) != historyTimes.end() ? 1 : 0;
    }

    if (variable.kind == VariableKind::Awards)
    {
        const std::unordered_map<uint32_t, int32_t>::const_iterator overrideIt =
            runtimeState.variables.find(variable.rawId);

        if (overrideIt != runtimeState.variables.end())
        {
            return overrideIt->second;
        }

        if (pParty == nullptr)
        {
            return 0;
        }

        if (memberIndex)
        {
            return pParty->hasAward(*memberIndex, variable.index) ? static_cast<int32_t>(variable.index) : 0;
        }

        return pParty->hasAward(variable.index) ? static_cast<int32_t>(variable.index) : 0;
    }

    if (variable.kind == VariableKind::CircusPrises)
    {
        return getInventoryItemCount(runtimeState, pParty, Mm6CircusLodestoneItemId, std::nullopt)
            * Mm6CircusLodestonePoints
            + getInventoryItemCount(runtimeState, pParty, Mm6CircusHarpyFeatherItemId, std::nullopt)
                * Mm6CircusHarpyFeatherPoints
            + getInventoryItemCount(runtimeState, pParty, Mm6CircusFourLeafCloverItemId, std::nullopt)
                * Mm6CircusFourLeafCloverPoints;
    }

    if (variable.kind == VariableKind::ClassId)
    {
        if (!memberIndex || pParty == nullptr)
        {
            return 0;
        }

        const Character *pMember = pParty->member(*memberIndex);

        if (pMember == nullptr)
        {
            return 0;
        }

        const std::optional<uint32_t> classId = tableBackedClassIdForName(pParty, pMember->className);
        return classId ? static_cast<int32_t>(*classId) : 0;
    }

    if (variable.kind == VariableKind::Experience)
    {
        if (!memberIndex || pParty == nullptr)
        {
            return 0;
        }

        const Character *pMember = pParty->member(*memberIndex);
        return pMember != nullptr
            ? static_cast<int32_t>(std::min<uint32_t>(pMember->experience, static_cast<uint32_t>(std::numeric_limits<int32_t>::max())))
            : 0;
    }

    if (variable.kind == VariableKind::CurrentHealth
        || variable.kind == VariableKind::MaxHealth
        || variable.kind == VariableKind::CurrentSpellPoints
        || variable.kind == VariableKind::MaxSpellPoints)
    {
        const Character *pMember = resolveCharacterForVariableRead(pParty, memberIndex);

        if (pMember == nullptr)
        {
            return 0;
        }

        switch (variable.kind)
        {
            case VariableKind::CurrentHealth:
                return pMember->health;

            case VariableKind::MaxHealth:
                return resolveCharacterEffectiveMaxHealth(*pMember);

            case VariableKind::CurrentSpellPoints:
                return pMember->spellPoints;

            case VariableKind::MaxSpellPoints:
                return resolveCharacterEffectiveMaxSpellPoints(*pMember);

            default:
                break;
        }

        return 0;
    }

    if (variable.kind == VariableKind::Gold)
    {
        return pParty != nullptr ? pParty->gold() : 0;
    }

    if (variable.kind == VariableKind::GoldInBank)
    {
        return pParty != nullptr ? pParty->bankGold() : 0;
    }

    if (variable.kind == VariableKind::BaseLevel
        || variable.kind == VariableKind::LevelBonus
        || variable.kind == VariableKind::Sex
        || variable.kind == VariableKind::Race
        || variable.kind == VariableKind::Age
        || variable.kind == VariableKind::ArmorClass
        || variable.kind == VariableKind::ArmorClassBonus)
    {
        const Character *pMember = resolveCharacterForVariableRead(pParty, memberIndex);

        if (pMember == nullptr)
        {
            return 0;
        }

        switch (variable.kind)
        {
            case VariableKind::BaseLevel:
                return static_cast<int32_t>(pMember->level);

            case VariableKind::LevelBonus:
                return pMember->levelModifier;

            case VariableKind::Sex:
                return static_cast<int32_t>(pMember->sexId);

            case VariableKind::Race:
                return static_cast<int32_t>(pMember->raceId);

            case VariableKind::Age:
                return resolveCharacterAge(*pMember);

            case VariableKind::ArmorClass:
                return resolveCharacterActualArmorClass(*pMember, pParty);

            case VariableKind::ArmorClassBonus:
                return pMember->armorClassModifier;

            default:
                break;
        }

        return 0;
    }

    if (variable.kind == VariableKind::BaseStat
        || variable.kind == VariableKind::ActualStat
        || variable.kind == VariableKind::StatBonus
        || variable.kind == VariableKind::BaseResistance
        || variable.kind == VariableKind::ResistanceBonus)
    {
        if (!memberIndex || pParty == nullptr)
        {
            return 0;
        }

        const Character *pMember = pParty->member(*memberIndex);
        if (pMember == nullptr)
        {
            return 0;
        }

        if (variable.kind == VariableKind::ActualStat)
        {
            return readCharacterActualStatValue(*pMember, variable.rawId, pParty);
        }

        return readCharacterVariableValue(*pMember, variable.rawId);
    }

    if (variable.kind == VariableKind::StatMoreThanBase)
    {
        const Character *pMember = resolveCharacterForVariableRead(pParty, memberIndex);

        if (pMember == nullptr)
        {
            return 0;
        }

        EvtVariable actualVariableId = EvtVariable::ActualMight;
        EvtVariable baseVariableId = EvtVariable::BaseMight;

        switch (variableId)
        {
            case EvtVariable::IsMightMoreThanBase:
                actualVariableId = EvtVariable::ActualMight;
                baseVariableId = EvtVariable::BaseMight;
                break;

            case EvtVariable::IsIntellectMoreThanBase:
                actualVariableId = EvtVariable::ActualIntellect;
                baseVariableId = EvtVariable::BaseIntellect;
                break;

            case EvtVariable::IsPersonalityMoreThanBase:
                actualVariableId = EvtVariable::ActualPersonality;
                baseVariableId = EvtVariable::BasePersonality;
                break;

            case EvtVariable::IsEnduranceMoreThanBase:
                actualVariableId = EvtVariable::ActualEndurance;
                baseVariableId = EvtVariable::BaseEndurance;
                break;

            case EvtVariable::IsSpeedMoreThanBase:
                actualVariableId = EvtVariable::ActualSpeed;
                baseVariableId = EvtVariable::BaseSpeed;
                break;

            case EvtVariable::IsAccuracyMoreThanBase:
                actualVariableId = EvtVariable::ActualAccuracy;
                baseVariableId = EvtVariable::BaseAccuracy;
                break;

            case EvtVariable::IsLuckMoreThanBase:
                actualVariableId = EvtVariable::ActualLuck;
                baseVariableId = EvtVariable::BaseLuck;
                break;

            default:
                break;
        }

        const int actualValue = readCharacterActualStatValue(*pMember, static_cast<uint32_t>(actualVariableId), pParty);
        const int baseValue = GameMechanics::resolveCharacterDisplayedBasePrimaryStat(
            *pMember,
            static_cast<uint32_t>(baseVariableId),
            pParty != nullptr ? pParty->itemTable() : nullptr,
            pParty != nullptr ? pParty->standardItemEnchantTable() : nullptr,
            pParty != nullptr ? pParty->specialItemEnchantTable() : nullptr);
        return actualValue >= baseValue ? 1 : 0;
    }

    if (variable.kind == VariableKind::Skill)
    {
        const std::optional<std::string> skillName = skillNameForEvtVariable(variableId);

        if (!skillName)
        {
            return 0;
        }

        const Character *pMember =
            pParty != nullptr && Party::isPartyWideUtilitySkill(*skillName)
                ? pParty->bestPartyWideUtilitySkillMember(*skillName)
                : resolveCharacterForVariableRead(pParty, memberIndex);

        if (pMember == nullptr)
        {
            return 0;
        }

        const CharacterSkill *pSkill = pMember->findSkill(*skillName);

        if (pSkill == nullptr)
        {
            return 0;
        }

        return joinedSkillValue(pSkill->level, pSkill->mastery);
    }

    if (variable.kind == VariableKind::Condition)
    {
        const Character *pMember = resolveCharacterForVariableRead(pParty, memberIndex);

        if (pMember == nullptr)
        {
            return 0;
        }

        const std::optional<CharacterCondition> condition = conditionForEvtVariable(variableId);

        if (!condition)
        {
            return 0;
        }

        return pMember->conditions.test(static_cast<size_t>(*condition)) ? 1 : 0;
    }

    if (variable.kind == VariableKind::MajorCondition)
    {
        const Character *pMember = resolveCharacterForVariableRead(pParty, memberIndex);
        return pMember != nullptr ? resolveCharacterMajorConditionValue(*pMember) : 0;
    }

    if (variable.kind == VariableKind::MapPersistent)
    {
        return variable.index < runtimeState.mapVars.size() ? runtimeState.mapVars[variable.index] : 0;
    }

    if (variable.kind == VariableKind::DecorPersistent)
    {
        return variable.index < runtimeState.decorVars.size() ? runtimeState.decorVars[variable.index] : 0;
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        if (variable.kind == VariableKind::QBits
            && variable.rawId >= 400
            && variable.rawId <= 449
            && pParty != nullptr)
        {
            const uint32_t rosterId = variable.rawId - 399;
            return pParty->hasRosterMember(rosterId) ? 1 : 0;
        }

        if (variable.kind == VariableKind::QBits && pParty != nullptr)
        {
            return pParty->hasQuestBit(variable.rawId) ? 1 : 0;
        }

        const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
        return iterator != runtimeState.variables.end() ? iterator->second : 0;
    }

    if (variable.kind == VariableKind::PartyState)
    {
        const Character *pMember = resolveCharacterForVariableRead(pParty, memberIndex);

        switch (variableId)
        {
            case EvtVariable::PlayerBits:
                return pMember != nullptr
                    ? (pMember->playerBits.contains(variable.index) ? 1 : 0)
                    : 0;

            case EvtVariable::Npcs2:
                return pMember != nullptr
                    ? ((pMember->npcs2 & (1u << std::min<uint32_t>(variable.index, MaxBitfieldFlagIndex))) != 0 ? 1 : 0)
                    : 0;

            case EvtVariable::IsFlying:
                if (pParty == nullptr || !pParty->hasPartyBuff(PartyBuffId::Fly))
                {
                    return 0;
                }

                if (pSceneEventContext == nullptr)
                {
                    return 1;
                }

                {
                    const IGameplayWorldRuntime *pWorldRuntime =
                        dynamic_cast<const IGameplayWorldRuntime *>(pSceneEventContext);
                    return pWorldRuntime != nullptr && pWorldRuntime->partyIsFlyingForEventChecks() ? 1 : 0;
                }

            case EvtVariable::HiredNpcHasSpeciality:
                for (const EventRuntimeState::HiredNpcFollower &follower : runtimeState.hiredNpcFollowers)
                {
                    if (follower.professionId == variable.index)
                    {
                        return 1;
                    }
                }
                return 0;

            case EvtVariable::NumSkillPoints:
                return pMember != nullptr ? static_cast<int32_t>(pMember->skillPoints) : 0;

            case EvtVariable::MonthIs:
                return resolveMonthFromDayOfYear(getVariableValue(
                    runtimeState,
                    decodeVariable(static_cast<uint32_t>(EvtVariable::DayOfYear)),
                    pParty,
                    std::nullopt,
                    pSceneEventContext));

            case EvtVariable::Counter1:
            case EvtVariable::Counter2:
            case EvtVariable::Counter3:
            case EvtVariable::Counter4:
            case EvtVariable::Counter5:
            case EvtVariable::Counter6:
            case EvtVariable::Counter7:
            case EvtVariable::Counter8:
            case EvtVariable::Counter9:
            case EvtVariable::Counter10:
                return pParty != nullptr ? pParty->eventVariableValue(variable.tag) : 0;

            case EvtVariable::ReputationInCurrentLocation:
                return runtimeState.currentLocationReputation;

            case EvtVariable::Unknown1:
            case EvtVariable::NumDeaths:
            case EvtVariable::NumBounties:
            case EvtVariable::PrisonTerms:
            case EvtVariable::ArenaWinsPage:
            case EvtVariable::ArenaWinsSquire:
            case EvtVariable::ArenaWinsKnight:
            case EvtVariable::ArenaWinsLord:
                return pParty != nullptr ? pParty->eventVariableValue(variable.tag) : 0;

            case EvtVariable::Invisible:
                return pParty != nullptr && pParty->hasPartyBuff(PartyBuffId::Invisibility) ? 1 : 0;

            default:
                break;
        }
    }

    if (pParty != nullptr)
    {
        const int32_t partyValue = pParty->eventVariableValue(variable.tag);

        if (partyValue != 0)
        {
            return partyValue;
        }
    }

    if (const Character *pMember = resolveCharacterForVariableRead(pParty, memberIndex))
    {
        const auto memberIt = pMember->eventVariables.find(variable.tag);

        if (memberIt != pMember->eventVariables.end())
        {
            return memberIt->second;
        }
    }

    const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
    return iterator != runtimeState.variables.end() ? iterator->second : 0;
}

void EventRuntime::setVariableValue(
    EventRuntimeState &runtimeState,
    const VariableRef &variable,
    int32_t value,
    Party *pParty,
    const std::vector<size_t> &targetMemberIndices,
    const ISceneEventContext *pSceneEventContext
)
{
    const EvtVariable variableId = static_cast<EvtVariable>(variable.tag);
    const std::optional<size_t> memberIndex = singleTargetMemberIndex(targetMemberIndices);
    const int32_t previousValue = getVariableValue(runtimeState, variable, pParty, memberIndex);

    if (variable.kind == VariableKind::Inventory)
    {
        if (value != 0)
        {
            runtimeState.grantedItemIds.push_back(variable.rawId);
        }
        else if (pParty != nullptr && !targetMemberIndices.empty())
        {
            removeInventoryItemFromTargets(*pParty, targetMemberIndices, variable.rawId);
        }

        return;
    }

    if (variable.kind == VariableKind::Food)
    {
        if (pParty != nullptr)
        {
            pParty->addFood(value - pParty->food());
        }
        else
        {
            runtimeState.variables[variable.rawId] = value;
        }

        if (value > previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
        }
        else if (value < previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Awards)
    {
        if (pParty != nullptr)
        {
            std::vector<size_t> changedMemberIndices;

            for (size_t memberIndex : targetMemberIndices)
            {
                if (value != 0)
                {
                    if (pParty->hasAward(memberIndex, variable.index))
                    {
                        continue;
                    }

                    pParty->addAward(memberIndex, variable.index);
                    changedMemberIndices.push_back(memberIndex);
                }
                else
                {
                    if (!pParty->hasAward(memberIndex, variable.index))
                    {
                        continue;
                    }

                    pParty->removeAward(memberIndex, variable.index);
                    changedMemberIndices.push_back(memberIndex);
                }
            }

            if (value != 0 && !changedMemberIndices.empty())
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, changedMemberIndices);
            }

            return;
        }

        if (value != 0)
        {
            runtimeState.variables[variable.rawId] = static_cast<int32_t>(variable.index);
            runtimeState.grantedAwardIds.push_back(variable.index);
        }
        else
        {
            runtimeState.variables[variable.rawId] = 0;
            runtimeState.removedAwardIds.push_back(variable.index);
        }

        return;
    }

    if (variable.kind == VariableKind::AutoNote)
    {
        const int32_t normalizedValue = value != 0 ? value : 0;
        runtimeState.variables[variable.rawId] = normalizedValue;

        if (normalizedValue != 0 && previousValue == 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AutoNote, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::History)
    {
        const int32_t normalizedValue = value != 0 ? 1 : 0;
        runtimeState.variables[variable.rawId] = normalizedValue;
        std::unordered_map<uint32_t, int32_t> &historyTimes =
            mutableHistoryEventTimesForActiveContinent(runtimeState);

        if (normalizedValue != 0 && previousValue == 0)
        {
            historyTimes[variable.index] = std::max(1, currentGameMinutesFromRuntimeState(runtimeState));
        }
        else if (normalizedValue == 0)
        {
            historyTimes.erase(variable.index);
        }

        synchronizeLegacyHistoryMirror(runtimeState);

        return;
    }

    if (variable.kind == VariableKind::ClassId)
    {
        if (pParty == nullptr)
        {
            return;
        }

        const std::optional<std::string> className =
            tableBackedClassNameForId(pParty, static_cast<uint32_t>(value));

        if (!className)
        {
            return;
        }

        std::vector<size_t> changedMemberIndices;

        for (size_t memberIndex : targetMemberIndices)
        {
            const Character *pMember = pParty->member(memberIndex);

            if (pMember == nullptr || pMember->className == *className)
            {
                continue;
            }

            if (pParty->setMemberClassName(memberIndex, *className))
            {
                changedMemberIndices.push_back(memberIndex);
            }
        }

        if (!changedMemberIndices.empty())
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, changedMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Experience)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t memberIndex : targetMemberIndices)
        {
            pParty->setMemberExperience(memberIndex, std::max(0, value));
        }

        if (value > previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
        }
        else if (value < previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::CurrentHealth
        || variable.kind == VariableKind::MaxHealth
        || variable.kind == VariableKind::CurrentSpellPoints
        || variable.kind == VariableKind::MaxSpellPoints)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            switch (variable.kind)
            {
                case VariableKind::CurrentHealth:
                    pMember->health = std::clamp(value, 0, resolveCharacterEffectiveMaxHealth(*pMember));
                    break;

                case VariableKind::MaxHealth:
                    pMember->maxHealth = std::max(1, value);
                    pMember->health = std::clamp(pMember->health, 0, resolveCharacterEffectiveMaxHealth(*pMember));
                    break;

                case VariableKind::CurrentSpellPoints:
                    pMember->spellPoints = std::clamp(value, 0, resolveCharacterEffectiveMaxSpellPoints(*pMember));
                    break;

                case VariableKind::MaxSpellPoints:
                    pMember->maxSpellPoints = std::max(0, value);
                    pMember->spellPoints = std::clamp(pMember->spellPoints, 0, resolveCharacterEffectiveMaxSpellPoints(*pMember));
                    break;

                default:
                    break;
            }
        }

        if (value > previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatIncrease, pParty, targetMemberIndices);
        }
        else if (value < previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Gold)
    {
        if (pParty != nullptr)
        {
            pParty->addGold(value - pParty->gold());
        }
        else
        {
            runtimeState.variables[variable.rawId] = value;
        }

        if (value > previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
        }
        else if (value < previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::GoldInBank)
    {
        if (pParty != nullptr)
        {
            const int delta = value - pParty->bankGold();

            if (delta >= 0)
            {
                pParty->depositGoldToBank(delta);
            }
            else
            {
                pParty->withdrawBankGold(-delta);
            }
        }
        else
        {
            runtimeState.variables[variable.rawId] = value;
        }

        if (value > previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
        }
        else if (value < previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::BaseStat
        || variable.kind == VariableKind::ActualStat
        || variable.kind == VariableKind::StatBonus
        || variable.kind == VariableKind::BaseResistance
        || variable.kind == VariableKind::ResistanceBonus)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t memberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(memberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            writeCharacterVariableValue(*pMember, variable.rawId, value);
        }

        if (value > previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatIncrease, pParty, targetMemberIndices);
        }
        else if (value < previousValue)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        if ((variable.kind == VariableKind::BaseStat || variable.kind == VariableKind::BaseResistance)
            && value > previousValue)
        {
            for (size_t memberIndex : targetMemberIndices)
            {
                pParty->requestSpeech(memberIndex, SpeechId::StatBaseIncreased);
            }

            queuePermanentVariableStatusMessage(
                runtimeState,
                variable.rawId,
                value - previousValue,
                targetMemberIndices.size()
            );
        }

        return;
    }

    if (variable.kind == VariableKind::BaseLevel
        || variable.kind == VariableKind::LevelBonus
        || variable.kind == VariableKind::Sex
        || variable.kind == VariableKind::Race
        || variable.kind == VariableKind::Age
        || variable.kind == VariableKind::ArmorClassBonus)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            switch (variable.kind)
            {
                case VariableKind::BaseLevel:
                    pMember->level = std::max(1, value);
                    break;

                case VariableKind::LevelBonus:
                    pMember->levelModifier = value;
                    break;

                case VariableKind::Sex:
                    pMember->sexId = std::max(0, value);
                    break;

                case VariableKind::Race:
                    pMember->raceId = std::max(0, value);
                    break;

                case VariableKind::Age:
                    pMember->ageModifier = value;
                    break;

                case VariableKind::ArmorClassBonus:
                    pMember->armorClassModifier = value;
                    break;

                default:
                    break;
            }
        }

        if (variable.kind == VariableKind::LevelBonus)
        {
            if (value > previousValue)
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatIncrease, pParty, targetMemberIndices);
            }
            else if (value < previousValue)
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
            }
        }

        return;
    }

    if (variable.kind == VariableKind::Skill)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        const std::optional<std::string> skillName = skillNameForEvtVariable(variableId);

        if (!skillName)
        {
            return;
        }

        const uint16_t joinedValue = static_cast<uint16_t>(std::max(0, value));
        const uint32_t level = joinedValue & 0x3Fu;
        const SkillMastery mastery = masteryFromJoinedValue(joinedValue);
        std::vector<size_t> learnedMemberIndices;

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            if (level == 0 || mastery == SkillMastery::None)
            {
                pMember->skills.erase(*skillName);
                GameMechanics::refreshCharacterBaseResources(
                    *pMember,
                    false,
                    pParty != nullptr ? pParty->classMultiplierTable() : nullptr);
                continue;
            }

            const bool hadLearnedSkill = characterHasLearnedSkill(*pMember, *skillName);
            CharacterSkill &skill = pMember->skills[*skillName];
            skill.name = *skillName;
            skill.level = level;
            skill.mastery = mastery;
            if (!hadLearnedSkill)
            {
                learnedMemberIndices.push_back(targetMemberIndex);
            }
            GameMechanics::refreshCharacterBaseResources(
                *pMember,
                false,
                pParty != nullptr ? pParty->classMultiplierTable() : nullptr);
        }

        if (!learnedMemberIndices.empty())
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::QuestComplete, pParty, learnedMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Condition)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        const std::optional<CharacterCondition> condition = conditionForEvtVariable(variableId);

        if (!condition)
        {
            return;
        }

        bool changed = false;

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            const Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            const bool hadCondition = pMember->conditions.test(static_cast<size_t>(*condition));

            if (pParty->applyMemberCondition(
                    targetMemberIndex,
                    *condition,
                    conditionStartGameMinutes(runtimeState, pSceneEventContext))
                && !hadCondition)
            {
                changed = true;
            }
        }

        if (changed && isPoisonOrDiseaseCondition(*condition))
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::Disease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::MajorCondition)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember != nullptr)
            {
                pMember->conditions.reset();
                pMember->conditionStartGameMinutes.fill(0.0f);
            }
        }

        return;
    }

    if (variable.kind == VariableKind::MapPersistent)
    {
        if (variable.index < runtimeState.mapVars.size())
        {
            const int32_t currentValue = static_cast<int32_t>(runtimeState.mapVars[variable.index]);
            const int32_t updatedValue = std::clamp(value, 0, 255);
            runtimeState.mapVars[variable.index] = static_cast<uint8_t>(updatedValue);
            traceIndexedRuntimeValueChange(
                runtimeState,
                "map_var_changed",
                variable.index,
                currentValue,
                updatedValue,
                "set");
        }
        return;
    }

    if (variable.kind == VariableKind::DecorPersistent)
    {
        if (variable.index < runtimeState.decorVars.size())
        {
            const int32_t currentValue = static_cast<int32_t>(runtimeState.decorVars[variable.index]);
            const int32_t updatedValue = std::clamp(value, 0, 255);
            runtimeState.decorVars[variable.index] = static_cast<uint8_t>(updatedValue);
            traceIndexedRuntimeValueChange(
                runtimeState,
                "decor_var_changed",
                variable.index,
                currentValue,
                updatedValue,
                "set");
        }
        return;
    }

    if (variable.kind == VariableKind::PartyState)
    {
        if (variableId == EvtVariable::PlayerBits && pParty != nullptr)
        {
            for (size_t targetMemberIndex : targetMemberIndices)
            {
                Character *pMember = pParty->member(targetMemberIndex);

                if (pMember == nullptr)
                {
                    continue;
                }

                if (value != 0)
                {
                    pMember->playerBits.insert(variable.index);
                }
                else
                {
                    pMember->playerBits.erase(variable.index);
                }
            }

            return;
        }

        if (variableId == EvtVariable::Npcs2 && pParty != nullptr)
        {
            for (size_t targetMemberIndex : targetMemberIndices)
            {
                Character *pMember = pParty->member(targetMemberIndex);

                if (pMember == nullptr || variable.index >= 32)
                {
                    continue;
                }

                if (value != 0)
                {
                    pMember->npcs2 |= (1u << std::min<uint32_t>(variable.index, MaxBitfieldFlagIndex));
                }
                else
                {
                    pMember->npcs2 &= ~(1u << std::min<uint32_t>(variable.index, MaxBitfieldFlagIndex));
                }
            }

            return;
        }

        if ((variableId >= EvtVariable::Counter1 && variableId <= EvtVariable::Counter10) && pParty != nullptr)
        {
            pParty->setEventVariableValue(variable.tag, currentGameMinutesFromRuntimeState(runtimeState));
            return;
        }

        if (variableId == EvtVariable::NumSkillPoints && pParty != nullptr)
        {
            for (size_t targetMemberIndex : targetMemberIndices)
            {
                Character *pMember = pParty->member(targetMemberIndex);

                if (pMember != nullptr)
                {
                    pMember->skillPoints = std::max(0, value);
                }
            }

            return;
        }

        if (variableId == EvtVariable::ReputationInCurrentLocation)
        {
            runtimeState.currentLocationReputation = clampReputation(value);
            return;
        }

        if (pParty != nullptr)
        {
            if (variableId == EvtVariable::PrisonTerms && value > previousValue)
            {
                pParty->requestSpeech(pParty->activeMemberIndex(), SpeechId::InPrison);
            }

            pParty->setEventVariableValue(variable.tag, value);
            return;
        }
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        const int32_t normalizedValue = value != 0 ? 1 : 0;

        if (variable.kind == VariableKind::QBits && pParty != nullptr)
        {
            pParty->setQuestBit(variable.rawId, normalizedValue != 0);
        }
        else
        {
            runtimeState.variables[variable.rawId] = normalizedValue;
        }

        if (variable.kind == VariableKind::QBits
            && shouldQueueQuestBitFx(pParty, variable.rawId, previousValue, normalizedValue))
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::QuestComplete, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::History)
    {
        const int32_t normalizedValue = value != 0 ? 1 : 0;
        runtimeState.variables[variable.rawId] = normalizedValue;
        std::unordered_map<uint32_t, int32_t> &historyTimes =
            mutableHistoryEventTimesForActiveContinent(runtimeState);

        if (normalizedValue != 0 && previousValue == 0)
        {
            historyTimes[variable.index] = std::max(1, currentGameMinutesFromRuntimeState(runtimeState));
        }
        else if (normalizedValue == 0)
        {
            historyTimes.erase(variable.index);
        }

        synchronizeLegacyHistoryMirror(runtimeState);

        return;
    }

    if (pParty != nullptr && memberIndex)
    {
        Character *pMember = pParty->member(*memberIndex);

        if (pMember != nullptr)
        {
            if (value == 0)
            {
                pMember->eventVariables.erase(variable.tag);
            }
            else
            {
                pMember->eventVariables[variable.tag] = value;
            }
            return;
        }
    }

    if (pParty != nullptr)
    {
        pParty->setEventVariableValue(variable.tag, value);
        return;
    }

    runtimeState.variables[variable.rawId] = value;
}

void EventRuntime::addVariableValue(
    EventRuntimeState &runtimeState,
    const VariableRef &variable,
    int32_t value,
    Party *pParty,
    const std::vector<size_t> &targetMemberIndices,
    const ISceneEventContext *pSceneEventContext
)
{
    const EvtVariable variableId = static_cast<EvtVariable>(variable.tag);
    const std::optional<size_t> memberIndex = singleTargetMemberIndex(targetMemberIndices);
    const int32_t previousValue = getVariableValue(runtimeState, variable, pParty, memberIndex);

    if (variable.kind == VariableKind::Inventory)
    {
        if (value > 0)
        {
            runtimeState.grantedItemIds.push_back(static_cast<uint32_t>(value));
        }
        return;
    }

    if (variable.kind == VariableKind::Condition)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        const std::optional<CharacterCondition> condition = conditionForEvtVariable(variableId);

        if (!condition)
        {
            return;
        }

        bool changed = false;

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            const Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            const bool hadCondition = pMember->conditions.test(static_cast<size_t>(*condition));

            if (pParty->applyMemberCondition(
                    targetMemberIndex,
                    *condition,
                    conditionStartGameMinutes(runtimeState, pSceneEventContext))
                && !hadCondition)
            {
                changed = true;
            }
        }

        if (changed && isPoisonOrDiseaseCondition(*condition))
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::Disease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Food)
    {
        if (pParty != nullptr)
        {
            pParty->addFood(value);
        }
        else
        {
            runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable, nullptr) + value;
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::QuestComplete, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Awards)
    {
        if (pParty != nullptr)
        {
            std::vector<size_t> changedMemberIndices;

            for (size_t memberIndex : targetMemberIndices)
            {
                if (value > 0)
                {
                    if (pParty->hasAward(memberIndex, variable.index))
                    {
                        continue;
                    }

                    pParty->addAward(memberIndex, variable.index);
                    changedMemberIndices.push_back(memberIndex);
                }
            }

            if (value > 0 && !changedMemberIndices.empty())
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::QuestComplete, pParty, changedMemberIndices);
            }

            return;
        }

        if (value > 0)
        {
            runtimeState.variables[variable.rawId] = static_cast<int32_t>(variable.index);
            runtimeState.grantedAwardIds.push_back(variable.index);
        }

        return;
    }

    if (variable.kind == VariableKind::AutoNote)
    {
        const int32_t updatedValue = previousValue != 0 ? previousValue : value;
        runtimeState.variables[variable.rawId] = updatedValue;

        if (updatedValue != 0 && previousValue == 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AutoNote, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::History)
    {
        const int32_t updatedValue = previousValue != 0 ? previousValue : (value != 0 ? 1 : 0);
        runtimeState.variables[variable.rawId] = updatedValue;
        std::unordered_map<uint32_t, int32_t> &historyTimes =
            mutableHistoryEventTimesForActiveContinent(runtimeState);

        if (updatedValue != 0 && previousValue == 0)
        {
            historyTimes[variable.index] = std::max(1, currentGameMinutesFromRuntimeState(runtimeState));
            synchronizeLegacyHistoryMirror(runtimeState);
        }

        return;
    }

    if (variable.kind == VariableKind::ClassId)
    {
        setVariableValue(runtimeState, variable, value, pParty, targetMemberIndices, pSceneEventContext);
        return;
    }

    if (variable.kind == VariableKind::Experience)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t memberIndex : targetMemberIndices)
        {
            pParty->addExperienceToMember(memberIndex, value);
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::QuestComplete, pParty, targetMemberIndices);
        }
        else if (value < 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::CurrentHealth
        || variable.kind == VariableKind::CurrentSpellPoints)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            if (variable.kind == VariableKind::CurrentHealth)
            {
                pMember->health = std::clamp(pMember->health + value, 0, resolveCharacterEffectiveMaxHealth(*pMember));
            }
            else
            {
                pMember->spellPoints = std::clamp(
                    pMember->spellPoints + value,
                    0,
                    resolveCharacterEffectiveMaxSpellPoints(*pMember)
                );
            }
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatIncrease, pParty, targetMemberIndices);
        }
        else if (value < 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Gold)
    {
        if (pParty != nullptr)
        {
            pParty->addGold(value);
        }
        else
        {
            runtimeState.variables[variable.rawId] = previousValue + value;
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
        }
        else if (value < 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::GoldInBank)
    {
        if (pParty != nullptr)
        {
            pParty->depositGoldToBank(value);
        }
        else
        {
            runtimeState.variables[variable.rawId] = previousValue + value;
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
        }
        else if (value < 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::BaseStat
        || variable.kind == VariableKind::ActualStat
        || variable.kind == VariableKind::StatBonus
        || variable.kind == VariableKind::BaseResistance
        || variable.kind == VariableKind::ResistanceBonus)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t memberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(memberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            const int32_t currentValue = readCharacterVariableValue(*pMember, variable.rawId);
            writeCharacterVariableValue(*pMember, variable.rawId, currentValue + value);
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatIncrease, pParty, targetMemberIndices);
        }
        else if (value < 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        if ((variable.kind == VariableKind::BaseStat || variable.kind == VariableKind::BaseResistance)
            && value > 0)
        {
            queuePermanentVariableStatusMessage(
                runtimeState,
                variable.rawId,
                value,
                targetMemberIndices.size()
            );
        }

        return;
    }

    if (variable.kind == VariableKind::MapPersistent)
    {
        if (variable.index < runtimeState.mapVars.size())
        {
            const int32_t currentValue = static_cast<int32_t>(runtimeState.mapVars[variable.index]);
            const int updatedValue = std::clamp(static_cast<int>(currentValue) + value, 0, 255);
            runtimeState.mapVars[variable.index] = static_cast<uint8_t>(updatedValue);
            traceIndexedRuntimeValueChange(
                runtimeState,
                "map_var_changed",
                variable.index,
                currentValue,
                updatedValue,
                "add");
        }
        return;
    }

    if (variable.kind == VariableKind::DecorPersistent)
    {
        if (variable.index < runtimeState.decorVars.size())
        {
            const int32_t currentValue = static_cast<int32_t>(runtimeState.decorVars[variable.index]);
            const int updatedValue = std::clamp(static_cast<int>(currentValue) + value, 0, 255);
            runtimeState.decorVars[variable.index] = static_cast<uint8_t>(updatedValue);
            traceIndexedRuntimeValueChange(
                runtimeState,
                "decor_var_changed",
                variable.index,
                currentValue,
                updatedValue,
                "add");
        }
        return;
    }

    if (variable.kind == VariableKind::PartyState && variableId == EvtVariable::PlayerBits && pParty != nullptr)
    {
        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember != nullptr && value != 0)
            {
                pMember->playerBits.insert(variable.index);
            }
        }

        return;
    }

    if (variable.kind == VariableKind::Skill)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        const std::optional<std::string> skillName = skillNameForEvtVariable(variableId);

        if (!skillName)
        {
            return;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            const bool hadLearnedSkill = characterHasLearnedSkill(*pMember, *skillName);
            CharacterSkill &skill = pMember->skills[*skillName];
            skill.name = *skillName;
            skill.level = std::max(0, static_cast<int>(skill.level) + value);

            if (skill.level == 0)
            {
                skill.mastery = SkillMastery::None;
                pMember->skills.erase(*skillName);
            }
            else if (skill.mastery == SkillMastery::None)
            {
                skill.mastery = SkillMastery::Normal;
            }

            if (!hadLearnedSkill && characterHasLearnedSkill(*pMember, *skillName))
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::QuestComplete, pParty, {targetMemberIndex});
            }

            GameMechanics::refreshCharacterBaseResources(
                *pMember,
                false,
                pParty != nullptr ? pParty->classMultiplierTable() : nullptr);
        }

        return;
    }

    if (variable.kind == VariableKind::PartyState)
    {
        if ((variableId >= EvtVariable::Counter1 && variableId <= EvtVariable::Counter10) && pParty != nullptr)
        {
            pParty->setEventVariableValue(variable.tag, currentGameMinutesFromRuntimeState(runtimeState));
            return;
        }

        if (variableId == EvtVariable::NumSkillPoints && pParty != nullptr)
        {
            for (size_t targetMemberIndex : targetMemberIndices)
            {
                Character *pMember = pParty->member(targetMemberIndex);

                if (pMember != nullptr)
                {
                    const int updatedSkillPoints = std::max(0, int(pMember->skillPoints) + value);
                    pMember->skillPoints = updatedSkillPoints;
                }
            }

            if (value > 0)
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
            }
            else if (value < 0)
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
            }

            return;
        }

        if (variableId == EvtVariable::ReputationInCurrentLocation)
        {
            runtimeState.currentLocationReputation = clampReputation(runtimeState.currentLocationReputation + value);
            return;
        }

        if (pParty != nullptr)
        {
            if (variableId == EvtVariable::PrisonTerms && value > 0)
            {
                pParty->requestSpeech(pParty->activeMemberIndex(), SpeechId::InPrison);
            }

            pParty->addEventVariableValue(variable.tag, value);
            return;
        }
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        const int32_t normalizedValue = value != 0 ? 1 : 0;

        if (variable.kind == VariableKind::QBits && pParty != nullptr)
        {
            pParty->setQuestBit(variable.rawId, normalizedValue != 0);
        }
        else
        {
            runtimeState.variables[variable.rawId] = normalizedValue;
        }

        if (variable.kind == VariableKind::QBits
            && shouldQueueQuestBitFx(pParty, variable.rawId, previousValue, normalizedValue))
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::QuestComplete, pParty, targetMemberIndices);
        }

        return;
    }

    if (pParty != nullptr && memberIndex)
    {
        Character *pMember = pParty->member(*memberIndex);

        if (pMember != nullptr)
        {
            const int32_t currentValue = getVariableValue(runtimeState, variable, pParty, memberIndex);
            const int32_t updatedValue = currentValue + value;

            if (updatedValue == 0)
            {
                pMember->eventVariables.erase(variable.tag);
            }
            else
            {
                pMember->eventVariables[variable.tag] = updatedValue;
            }
            return;
        }
    }

    runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable, nullptr) + value;
}

void EventRuntime::subtractVariableValue(
    EventRuntimeState &runtimeState,
    const VariableRef &variable,
    int32_t value,
    Party *pParty,
    const std::vector<size_t> &targetMemberIndices
)
{
    const EvtVariable variableId = static_cast<EvtVariable>(variable.tag);
    const std::optional<size_t> memberIndex = singleTargetMemberIndex(targetMemberIndices);
    const int32_t previousValue = getVariableValue(runtimeState, variable, pParty, memberIndex);

    if (variable.kind == VariableKind::Inventory)
    {
        if (pParty != nullptr && !targetMemberIndices.empty())
        {
            if (value > 0)
            {
                removeInventoryItemFromTargets(*pParty, targetMemberIndices, static_cast<uint32_t>(value));
            }
            return;
        }

        if (value > 0)
        {
            runtimeState.removedItemIds.push_back(static_cast<uint32_t>(value));
        }
        return;
    }

    if (variable.kind == VariableKind::Condition)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        const std::optional<CharacterCondition> condition = conditionForEvtVariable(variableId);

        if (!condition)
        {
            return;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            pParty->clearMemberCondition(targetMemberIndex, *condition);
        }

        return;
    }

    if (variable.kind == VariableKind::AutoNote)
    {
        if (value > 0)
        {
            runtimeState.variables[variable.rawId] = 0;
        }

        return;
    }

    if (variable.kind == VariableKind::History)
    {
        if (value > 0)
        {
            runtimeState.variables[variable.rawId] = 0;
            std::unordered_map<uint32_t, int32_t> &historyTimes =
                mutableHistoryEventTimesForActiveContinent(runtimeState);
            historyTimes.erase(variable.index);
            synchronizeLegacyHistoryMirror(runtimeState);
        }

        return;
    }

    if (variable.kind == VariableKind::Food)
    {
        if (pParty != nullptr)
        {
            pParty->addFood(-value);
        }
        else
        {
            runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable, nullptr) - value;
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Awards)
    {
        if (pParty != nullptr)
        {
            for (size_t memberIndex : targetMemberIndices)
            {
                if (value > 0)
                {
                    pParty->removeAward(memberIndex, variable.index);
                }
            }

            return;
        }

        if (value > 0)
        {
            runtimeState.variables[variable.rawId] = 0;
            runtimeState.removedAwardIds.push_back(variable.index);
        }

        return;
    }

    if (variable.kind == VariableKind::ClassId)
    {
        return;
    }

    if (variable.kind == VariableKind::Experience)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t memberIndex : targetMemberIndices)
        {
            pParty->addExperienceToMember(memberIndex, -static_cast<int64_t>(value));
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::CurrentHealth
        || variable.kind == VariableKind::CurrentSpellPoints)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            if (variable.kind == VariableKind::CurrentHealth)
            {
                pMember->health = std::clamp(pMember->health - value, 0, resolveCharacterEffectiveMaxHealth(*pMember));
            }
            else
            {
                pMember->spellPoints = std::clamp(
                    pMember->spellPoints - value,
                    0,
                    resolveCharacterEffectiveMaxSpellPoints(*pMember)
                );
            }
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::Gold)
    {
        if (pParty != nullptr)
        {
            pParty->addGold(-value);
        }
        else
        {
            runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable, nullptr) - value;
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::GoldInBank)
    {
        if (pParty != nullptr)
        {
            pParty->withdrawBankGold(value);
        }
        else
        {
            runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable, nullptr) - value;
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::BaseStat
        || variable.kind == VariableKind::ActualStat
        || variable.kind == VariableKind::StatBonus
        || variable.kind == VariableKind::BaseResistance
        || variable.kind == VariableKind::ResistanceBonus)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        for (size_t memberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(memberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            const int32_t currentValue = readCharacterVariableValue(*pMember, variable.rawId);
            writeCharacterVariableValue(*pMember, variable.rawId, currentValue - value);
        }

        if (value > 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::MapPersistent)
    {
        if (variable.index < runtimeState.mapVars.size())
        {
            const int32_t currentValue = static_cast<int32_t>(runtimeState.mapVars[variable.index]);
            const int updatedValue = std::clamp(static_cast<int>(currentValue) - value, 0, 255);
            runtimeState.mapVars[variable.index] = static_cast<uint8_t>(updatedValue);
            traceIndexedRuntimeValueChange(
                runtimeState,
                "map_var_changed",
                variable.index,
                currentValue,
                updatedValue,
                "subtract");
        }
        return;
    }

    if (variable.kind == VariableKind::DecorPersistent)
    {
        if (variable.index < runtimeState.decorVars.size())
        {
            const int32_t currentValue = static_cast<int32_t>(runtimeState.decorVars[variable.index]);
            const int updatedValue = std::clamp(static_cast<int>(currentValue) - value, 0, 255);
            runtimeState.decorVars[variable.index] = static_cast<uint8_t>(updatedValue);
            traceIndexedRuntimeValueChange(
                runtimeState,
                "decor_var_changed",
                variable.index,
                currentValue,
                updatedValue,
                "subtract");
        }
        return;
    }

    if (variable.kind == VariableKind::PartyState && variableId == EvtVariable::PlayerBits && pParty != nullptr)
    {
        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember != nullptr && value != 0)
            {
                pMember->playerBits.erase(variable.index);
            }
        }

        return;
    }

    if (variable.kind == VariableKind::Skill)
    {
        if (pParty == nullptr || targetMemberIndices.empty())
        {
            return;
        }

        const std::optional<std::string> skillName = skillNameForEvtVariable(variableId);

        if (!skillName)
        {
            return;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            CharacterSkill *pSkill = pMember->findSkill(*skillName);

            if (pSkill == nullptr)
            {
                continue;
            }

            pSkill->level = std::max(0, static_cast<int>(pSkill->level) - value);

            if (pSkill->level == 0)
            {
                pMember->skills.erase(*skillName);
            }

            GameMechanics::refreshCharacterBaseResources(
                *pMember,
                false,
                pParty != nullptr ? pParty->classMultiplierTable() : nullptr);
        }

        return;
    }

    if (variable.kind == VariableKind::PartyState)
    {
        if ((variableId >= EvtVariable::Counter1 && variableId <= EvtVariable::Counter10) && pParty != nullptr)
        {
            pParty->setEventVariableValue(variable.tag, 0);
            return;
        }

        if (variableId == EvtVariable::NumSkillPoints && pParty != nullptr)
        {
            for (size_t targetMemberIndex : targetMemberIndices)
            {
                Character *pMember = pParty->member(targetMemberIndex);

                if (pMember != nullptr)
                {
                    const int updatedSkillPoints = std::max(0, int(pMember->skillPoints) - value);
                    pMember->skillPoints = updatedSkillPoints;
                }
            }

            if (value > 0)
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::StatDecrease, pParty, targetMemberIndices);
            }

            return;
        }

        if (variableId == EvtVariable::ReputationInCurrentLocation)
        {
            runtimeState.currentLocationReputation = clampReputation(runtimeState.currentLocationReputation - value);
            return;
        }

        if (pParty != nullptr)
        {
            pParty->subtractEventVariableValue(variable.tag, value);
            return;
        }
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        if (variable.kind == VariableKind::QBits && pParty != nullptr)
        {
            pParty->setQuestBit(variable.rawId, false);
        }
        else
        {
            runtimeState.variables[variable.rawId] = 0;
        }

        return;
    }

    if (pParty != nullptr && memberIndex)
    {
        Character *pMember = pParty->member(*memberIndex);

        if (pMember != nullptr)
        {
            const int32_t currentValue = getVariableValue(runtimeState, variable, pParty, memberIndex);
            const int32_t updatedValue = currentValue - value;

            if (updatedValue == 0)
            {
                pMember->eventVariables.erase(variable.tag);
            }
            else
            {
                pMember->eventVariables[variable.tag] = updatedValue;
            }
            return;
        }
    }

    runtimeState.variables[variable.rawId] = getVariableValue(runtimeState, variable, nullptr) - value;
}

namespace
{
constexpr char LuaScopeMap[] = "map";
constexpr char LuaScopeGlobal[] = "global";
constexpr char LuaScopeCanShowTopic[] = "CanShowTopic";
int LuaSessionRegistryKey = 0;

struct LuaScopeProgram
{
    std::unordered_map<uint16_t, int> handlers;
    std::unordered_map<uint16_t, int> canShowTopicHandlers;
    std::vector<uint16_t> onLoadEventIds;
    std::vector<uint16_t> onLeaveEventIds;
    std::vector<uint16_t> npcEnterHookEventIds;
    std::vector<uint16_t> npcExitHookEventIds;
    std::vector<uint16_t> houseTopicFilterHookEventIds;
    std::vector<uint16_t> houseTopicClickHookEventIds;
    std::vector<uint16_t> restFoodCostHookEventIds;
    std::vector<uint16_t> gameplayActionHookEventIds;
    std::vector<uint16_t> mapRefillHookEventIds;
    std::vector<uint16_t> mapTransitionHookEventIds;
    std::vector<uint16_t> monsterKilledHookEventIds;
    std::vector<uint16_t> monsterDamageHookEventIds;
    std::vector<uint16_t> chestOpenHookEventIds;
    std::vector<uint16_t> inventoryOpenHookEventIds;
};

struct LuaExecutionContext
{
    const EventRuntime *pEventRuntime = nullptr;
    EventRuntimeState *pRuntimeState = nullptr;
    const EventRuntimeState *pReadonlyRuntimeState = nullptr;
    Party *pParty = nullptr;
    const Party *pReadonlyParty = nullptr;
    ISceneEventContext *pSceneEventContext = nullptr;
    const ISceneEventContext *pReadonlySceneEventContext = nullptr;
    PartySelector selector = {};
    std::optional<std::string> pendingMessageText;
    std::optional<bool> canShowTopicVisible;
    uint16_t currentEventId = 0;
    bool readonly = false;
    bool preservePendingOutputsOnBegin = false;
    bool preserveRuntimeOutputsOnBegin = false;
    bool allowStandaloneMapEventDialogueContext = true;
    bool executingGlobalHandler = false;
};

}

struct LuaSessionCache
{
    Engine::LuaStateOwner lua;
    std::optional<std::string> lastError;
    LuaScopeProgram localScope;
    LuaScopeProgram globalScope;
    LuaExecutionContext *pExecutionContext = nullptr;
};

namespace
{
void prepareRuntimeStateForEventExecution(
    EventRuntimeState &runtimeState,
    const ISceneEventContext *pSceneEventContext,
    bool clearPendingOutputs)
{
    runtimeState.lastAffectedMechanismIds.clear();
    runtimeState.openedChestIds.clear();
    runtimeState.openedChestRequests.clear();
    runtimeState.grantedItems.clear();
    runtimeState.grantedItemIds.clear();
    runtimeState.clearHeldItemRequest = false;
    runtimeState.removedItemIds.clear();
    runtimeState.grantedAwardIds.clear();
    runtimeState.removedAwardIds.clear();

    if (clearPendingOutputs)
    {
        runtimeState.pendingDialogueContext.reset();
        runtimeState.pendingMapMove.reset();
        runtimeState.pendingMovie.reset();
        runtimeState.pendingReturnToMainMenu = false;
        runtimeState.pendingInputPrompt.reset();
    }

    runtimeState.pendingSounds.clear();
    runtimeState.actorHostilityRequests.clear();
    runtimeState.actorGroupHostilityRequests.clear();
    syncTimeVariablesFromSceneContext(runtimeState, pSceneEventContext);
}

LuaSessionCache *luaSessionFromLua(lua_State *pLuaState)
{
    lua_pushlightuserdata(pLuaState, &LuaSessionRegistryKey);
    lua_rawget(pLuaState, LUA_REGISTRYINDEX);
    LuaSessionCache *pSession = static_cast<LuaSessionCache *>(lua_touserdata(pLuaState, -1));
    lua_pop(pLuaState, 1);
    return pSession;
}

LuaExecutionContext *executionContextFromLua(lua_State *pLuaState)
{
    LuaSessionCache *pSession = luaSessionFromLua(pLuaState);
    return pSession != nullptr ? pSession->pExecutionContext : nullptr;
}

bool luaEventBoolean(lua_State *pLuaState, int index)
{
    if (lua_type(pLuaState, index) == LUA_TNUMBER)
    {
        return lua_tonumber(pLuaState, index) != 0.0;
    }

    return lua_toboolean(pLuaState, index) != 0;
}

const Party *readonlyParty(const LuaExecutionContext *pExecutionContext)
{
    if (pExecutionContext == nullptr)
    {
        return nullptr;
    }

    return pExecutionContext->readonly ? pExecutionContext->pReadonlyParty : pExecutionContext->pParty;
}

const ISceneEventContext *readonlySceneEventContext(const LuaExecutionContext *pExecutionContext)
{
    if (pExecutionContext == nullptr)
    {
        return nullptr;
    }

    return pExecutionContext->readonly
        ? pExecutionContext->pReadonlySceneEventContext
        : pExecutionContext->pSceneEventContext;
}

bool sceneEventContextIsIndoorMap(const LuaExecutionContext *pExecutionContext)
{
    const ISceneEventContext *pSceneEventContext = readonlySceneEventContext(pExecutionContext);
    const IGameplayWorldRuntime *pWorldRuntime = dynamic_cast<const IGameplayWorldRuntime *>(pSceneEventContext);
    return pWorldRuntime != nullptr && pWorldRuntime->isIndoorMap();
}

bool eventStringEndsWithIgnoreCase(const std::string &value, std::string_view suffix)
{
    if (value.size() < suffix.size())
    {
        return false;
    }

    const size_t offset = value.size() - suffix.size();

    for (size_t index = 0; index < suffix.size(); ++index)
    {
        const unsigned char valueCharacter = static_cast<unsigned char>(value[offset + index]);
        const unsigned char suffixCharacter = static_cast<unsigned char>(suffix[index]);

        if (std::tolower(valueCharacter) != std::tolower(suffixCharacter))
        {
            return false;
        }
    }

    return true;
}

bool moveToMapLeavesIndoorDungeon(
    const LuaExecutionContext *pExecutionContext,
    const EventRuntimeState::PendingMapMove &move)
{
    return sceneEventContextIsIndoorMap(pExecutionContext)
        && move.mapName.has_value()
        && !move.useMapStartPosition
        && eventStringEndsWithIgnoreCase(*move.mapName, ".odm");
}

EventRuntimeState *writableRuntimeState(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || pExecutionContext->readonly)
    {
        return nullptr;
    }

    return pExecutionContext->pRuntimeState;
}

const EventRuntimeState *readableRuntimeState(lua_State *pLuaState)
{
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr)
    {
        return nullptr;
    }

    return pExecutionContext->readonly ? pExecutionContext->pReadonlyRuntimeState : pExecutionContext->pRuntimeState;
}

const Party *readableParty(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    return pExecutionContext != nullptr ? readonlyParty(pExecutionContext) : nullptr;
}

Party *writableParty(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || pExecutionContext->readonly)
    {
        return nullptr;
    }

    return pExecutionContext->pParty;
}

const EventRuntime *readableEventRuntime(lua_State *pLuaState)
{
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    return pExecutionContext != nullptr ? pExecutionContext->pEventRuntime : nullptr;
}

std::vector<size_t> selectedTargetMemberIndices(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    return pExecutionContext != nullptr ? resolveTargetMemberIndices(pExecutionContext->selector, readableParty(pLuaState))
                                        : std::vector<size_t>();
}

int luaBeginEvent(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pExecutionContext != nullptr && pRuntimeState != nullptr)
    {
        pExecutionContext->currentEventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
        pExecutionContext->selector = {};
        pExecutionContext->pendingMessageText.reset();
        if (!pExecutionContext->preserveRuntimeOutputsOnBegin)
        {
            prepareRuntimeStateForEventExecution(
                *pRuntimeState,
                pExecutionContext->pSceneEventContext,
                !pExecutionContext->preservePendingOutputsOnBegin);
        }
    }

    return 0;
}

int luaBeginCanShowTopic(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext != nullptr)
    {
        pExecutionContext->currentEventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
        pExecutionContext->selector = {};
        pExecutionContext->pendingMessageText.reset();
        pExecutionContext->canShowTopicVisible.reset();
    }

    return 0;
}

std::string luaDebugSourceName(const lua_Debug &debugInfo)
{
    const char *pSource = debugInfo.source != nullptr ? debugInfo.source : debugInfo.short_src;

    if (pSource == nullptr || pSource[0] == '\0')
    {
        return "lua";
    }

    if (pSource[0] == '@')
    {
        return std::string(pSource + 1);
    }

    return std::string(pSource);
}

int luaDebugPrint(lua_State *pLuaState)
{
    lua_Debug debugInfo = {};
    std::string sourceName = "lua";
    int lineNumber = 0;

    if (lua_getstack(pLuaState, 1, &debugInfo) != 0
        && lua_getinfo(pLuaState, "Sl", &debugInfo) != 0)
    {
        sourceName = luaDebugSourceName(debugInfo);
        lineNumber = debugInfo.currentline;
    }

    std::string message;
    const int argumentCount = lua_gettop(pLuaState);

    for (int argumentIndex = 1; argumentIndex <= argumentCount; ++argumentIndex)
    {
        if (argumentIndex > 1)
        {
            message += '\t';
        }

        size_t length = 0;
        const char *pText = luaL_tolstring(pLuaState, argumentIndex, &length);

        if (pText != nullptr)
        {
            message.append(pText, length);
        }

        lua_pop(pLuaState, 1);
    }

    std::cout << '[' << sourceName << ':' << lineNumber << "]: " << message << '\n';
    return 0;
}

int luaForPlayer(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext != nullptr)
    {
        pExecutionContext->selector = decodePartySelector(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)));
    }

    return 0;
}

int luaCompare(lua_State *pLuaState)
{
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const uint32_t rawVariableId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const int32_t compareValue = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
    lua_pushboolean(
        pLuaState,
        evaluateCompareValue(
            *readableRuntimeState(pLuaState),
            rawVariableId,
            compareValue,
            readableParty(pLuaState),
            selectedTargetMemberIndices(pLuaState),
            pExecutionContext == nullptr || pExecutionContext->selector.kind == PartySelectorKind::None,
            readonlySceneEventContext(pExecutionContext)));
    return 1;
}

int luaHasEverOwnedItem(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    lua_pushboolean(pLuaState, pParty != nullptr && pParty->hasEverOwnedItem(itemId));
    return 1;
}

int luaHasItemAnywhere(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    lua_pushboolean(pLuaState, pParty != nullptr && pParty->hasItemAnywhere(itemId));
    return 1;
}

int luaGetPartyPosition(lua_State *pLuaState)
{
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const ISceneEventContext *pSceneEventContext = readonlySceneEventContext(pExecutionContext);
    const IGameplayWorldRuntime *pWorldRuntime = dynamic_cast<const IGameplayWorldRuntime *>(pSceneEventContext);

    lua_pushinteger(pLuaState, pWorldRuntime != nullptr ? std::lround(pWorldRuntime->partyX()) : 0);
    lua_pushinteger(pLuaState, pWorldRuntime != nullptr ? std::lround(pWorldRuntime->partyY()) : 0);
    lua_pushinteger(pLuaState, pWorldRuntime != nullptr ? std::lround(pWorldRuntime->partyFootZ()) : 0);
    return 3;
}

int luaGetEnemyDetectorState(lua_State *pLuaState)
{
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const ISceneEventContext *pSceneEventContext = readonlySceneEventContext(pExecutionContext);
    const IGameplayWorldRuntime *pWorldRuntime = dynamic_cast<const IGameplayWorldRuntime *>(pSceneEventContext);
    bool yellow = false;
    bool red = false;

    if (pWorldRuntime != nullptr)
    {
        for (size_t actorIndex = 0; actorIndex < pWorldRuntime->mapActorCount(); ++actorIndex)
        {
            GameplayRuntimeActorState actorState = {};

            if (!pWorldRuntime->actorRuntimeState(actorIndex, actorState)
                || actorState.isDead
                || actorState.isInvisible
                || !actorState.hostileToParty
                || !actorState.hasDetectedParty)
            {
                continue;
            }

            yellow = true;

            if (actorState.combatTargetingParty)
            {
                red = true;
                break;
            }
        }
    }

    lua_pushboolean(pLuaState, yellow);
    lua_pushboolean(pLuaState, red);
    return 2;
}

int luaGetCurrentScreen(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    lua_pushinteger(
        pLuaState,
        pRuntimeState != nullptr && pRuntimeState->activeHookContext
            ? pRuntimeState->activeHookContext->menuId
            : 0);
    return 1;
}

int luaGetCurrentMapName(lua_State *pLuaState)
{
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const ISceneEventContext *pSceneEventContext = readonlySceneEventContext(pExecutionContext);
    const IGameplayWorldRuntime *pWorldRuntime = dynamic_cast<const IGameplayWorldRuntime *>(pSceneEventContext);
    lua_pushstring(pLuaState, pWorldRuntime != nullptr ? pWorldRuntime->mapName().c_str() : "");
    return 1;
}

int luaGetCurrentContinent(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    lua_pushinteger(pLuaState, pRuntimeState != nullptr ? pRuntimeState->activeHistoryContinentId : 0);
    return 1;
}

int32_t luaIntegerField(lua_State *pLuaState, int tableIndex, const char *pFieldName, int32_t defaultValue)
{
    const int absoluteIndex = lua_absindex(pLuaState, tableIndex);
    lua_getfield(pLuaState, absoluteIndex, pFieldName);
    const int32_t value = lua_isnil(pLuaState, -1)
        ? defaultValue
        : static_cast<int32_t>(luaL_checkinteger(pLuaState, -1));
    lua_pop(pLuaState, 1);
    return value;
}

uint32_t luaUnsignedField(lua_State *pLuaState, int tableIndex, const char *pFieldName, uint32_t defaultValue)
{
    return static_cast<uint32_t>(std::max<int32_t>(0, luaIntegerField(pLuaState, tableIndex, pFieldName, defaultValue)));
}

std::string luaStringField(lua_State *pLuaState, int tableIndex, const char *pFieldName, const std::string &defaultValue)
{
    const int absoluteIndex = lua_absindex(pLuaState, tableIndex);
    lua_getfield(pLuaState, absoluteIndex, pFieldName);
    const std::string value = lua_isnil(pLuaState, -1) ? defaultValue : luaL_checkstring(pLuaState, -1);
    lua_pop(pLuaState, 1);
    return value;
}

bool luaBooleanField(lua_State *pLuaState, int tableIndex, const char *pFieldName, bool defaultValue)
{
    const int absoluteIndex = lua_absindex(pLuaState, tableIndex);
    lua_getfield(pLuaState, absoluteIndex, pFieldName);
    const bool value = lua_isnil(pLuaState, -1) ? defaultValue : luaEventBoolean(pLuaState, -1);
    lua_pop(pLuaState, 1);
    return value;
}

std::array<bool, 7> luaWeekdayField(lua_State *pLuaState, int tableIndex, const std::array<bool, 7> &defaultValue)
{
    const int absoluteIndex = lua_absindex(pLuaState, tableIndex);
    lua_getfield(pLuaState, absoluteIndex, "daysAvailable");

    if (lua_isnil(pLuaState, -1))
    {
        lua_pop(pLuaState, 1);
        lua_getfield(pLuaState, absoluteIndex, "days");
    }

    if (!lua_istable(pLuaState, -1))
    {
        lua_pop(pLuaState, 1);
        return defaultValue;
    }

    std::array<bool, 7> days = defaultValue;

    for (size_t index = 0; index < days.size(); ++index)
    {
        lua_rawgeti(pLuaState, -1, static_cast<lua_Integer>(index + 1));

        if (!lua_isnil(pLuaState, -1))
        {
            days[index] = luaEventBoolean(pLuaState, -1);
        }

        lua_pop(pLuaState, 1);
    }

    lua_pop(pLuaState, 1);
    return days;
}

int luaSaveCurrentLocation(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 1);
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const ISceneEventContext *pSceneEventContext = readonlySceneEventContext(pExecutionContext);
    const IGameplayWorldRuntime *pWorldRuntime = dynamic_cast<const IGameplayWorldRuntime *>(pSceneEventContext);

    if (pRuntimeState != nullptr && pWorldRuntime != nullptr)
    {
        EventRuntimeState::SavedLocation location = {};
        location.x = static_cast<int32_t>(std::lround(pWorldRuntime->partyX()));
        location.y = static_cast<int32_t>(std::lround(pWorldRuntime->partyY()));
        location.z = static_cast<int32_t>(std::lround(pWorldRuntime->partyFootZ()));
        location.continentId = pRuntimeState->activeHistoryContinentId;
        location.mapName = pWorldRuntime->mapName();
        pRuntimeState->savedLocations[name] = std::move(location);
    }

    return 0;
}

int luaHasSavedLocation(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 1);
    lua_pushboolean(
        pLuaState,
        pRuntimeState != nullptr && pRuntimeState->savedLocations.find(name) != pRuntimeState->savedLocations.end());
    return 1;
}

int luaMoveToSavedLocation(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 1);
    const bool clearAfterUse = lua_gettop(pLuaState) >= 2 && luaEventBoolean(pLuaState, 2);

    if (pRuntimeState == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const auto iterator = pRuntimeState->savedLocations.find(name);

    if (iterator == pRuntimeState->savedLocations.end() || iterator->second.mapName.empty())
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const EventRuntimeState::SavedLocation location = iterator->second;
    EventRuntimeState::PendingMapMove pendingMapMove = {};
    pendingMapMove.mapName = location.mapName;
    pendingMapMove.x = location.x;
    pendingMapMove.y = location.y;
    pendingMapMove.z = location.z;
    pRuntimeState->pendingMapMove = std::move(pendingMapMove);

    if (location.continentId != 0)
    {
        setActiveHistoryContinent(*pRuntimeState, location.continentId);
    }

    if (clearAfterUse)
    {
        pRuntimeState->savedLocations.erase(name);
    }

    lua_pushboolean(pLuaState, true);
    return 1;
}

int luaClearSavedLocation(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 1);

    if (pRuntimeState != nullptr)
    {
        pRuntimeState->savedLocations.erase(name);
    }

    return 0;
}

int luaSetTransportRouteOverride(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t houseId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t routeIndex = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const uint64_t key = EventRuntime::transportRouteOverrideKey(houseId, routeIndex);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    if (lua_isnoneornil(pLuaState, 3))
    {
        pRuntimeState->transportRouteOverrides.erase(key);
        return 0;
    }

    luaL_checktype(pLuaState, 3, LUA_TTABLE);

    EventRuntimeState::TransportRouteOverride route = {};
    route.houseId = houseId;
    route.routeIndex = routeIndex;
    route.destinationName = luaStringField(pLuaState, 3, "destinationName", "");
    route.mapFileName = luaStringField(pLuaState, 3, "mapFileName", luaStringField(pLuaState, 3, "mapName", ""));
    route.daysAvailable = luaWeekdayField(pLuaState, 3, route.daysAvailable);
    route.travelDays = luaUnsignedField(pLuaState, 3, "travelDays", 0);
    route.x = luaIntegerField(pLuaState, 3, "x", 0);
    route.y = luaIntegerField(pLuaState, 3, "y", 0);
    route.z = luaIntegerField(pLuaState, 3, "z", 0);
    route.directionDegrees = luaIntegerField(pLuaState, 3, "directionDegrees", 0);
    route.requiredQBit = luaUnsignedField(pLuaState, 3, "requiredQBit", 0);
    route.useMapStartPosition = luaBooleanField(pLuaState, 3, "useMapStartPosition", false);

    pRuntimeState->transportRouteOverrides[key] = std::move(route);
    return 0;
}

int luaClearTransportRouteOverride(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t houseId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t routeIndex = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));

    if (pRuntimeState != nullptr)
    {
        pRuntimeState->transportRouteOverrides.erase(EventRuntime::transportRouteOverrideKey(houseId, routeIndex));
    }

    return 0;
}

int luaGetMapVar(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 1);
    const int32_t defaultValue = lua_gettop(pLuaState) >= 2
        ? static_cast<int32_t>(luaL_checkinteger(pLuaState, 2))
        : 0;
    int32_t value = defaultValue;

    if (pRuntimeState != nullptr)
    {
        const auto iterator = pRuntimeState->namedMapVars.find(name);

        if (iterator != pRuntimeState->namedMapVars.end())
        {
            value = iterator->second;
        }
    }

    lua_pushinteger(pLuaState, value);
    return 1;
}

int luaSetMapVar(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 1);
    const int32_t value = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));

    if (pRuntimeState != nullptr)
    {
        const auto previousIterator = pRuntimeState->namedMapVars.find(name);
        const int32_t previousValue =
            previousIterator != pRuntimeState->namedMapVars.end() ? previousIterator->second : 0;
        pRuntimeState->namedMapVars[name] = value;
        traceNamedRuntimeValueChange(
            *pRuntimeState,
            "named_map_var_changed",
            name,
            previousValue,
            value,
            "set");
    }

    return 0;
}

int luaGetGlobalVar(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 1);
    const int32_t defaultValue = lua_gettop(pLuaState) >= 2
        ? static_cast<int32_t>(luaL_checkinteger(pLuaState, 2))
        : 0;
    int32_t value = defaultValue;

    if (pRuntimeState != nullptr)
    {
        const auto iterator = pRuntimeState->namedGlobalVars.find(name);

        if (iterator != pRuntimeState->namedGlobalVars.end())
        {
            value = iterator->second;
        }
    }

    lua_pushinteger(pLuaState, value);
    return 1;
}

int luaSetGlobalVar(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const std::string name = luaL_checkstring(pLuaState, 1);
    const int32_t value = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));

    if (pRuntimeState != nullptr)
    {
        const auto previousIterator = pRuntimeState->namedGlobalVars.find(name);
        const int32_t previousValue =
            previousIterator != pRuntimeState->namedGlobalVars.end() ? previousIterator->second : 0;
        pRuntimeState->namedGlobalVars[name] = value;
        traceNamedRuntimeValueChange(
            *pRuntimeState,
            "named_global_var_changed",
            name,
            previousValue,
            value,
            "set");
    }

    return 0;
}

int luaGetHeldItemId(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const Party *pParty = readableParty(pLuaState);

    if (pRuntimeState != nullptr && pRuntimeState->activeHookContext && pRuntimeState->activeHookContext->heldItemId != 0)
    {
        lua_pushinteger(pLuaState, pRuntimeState->activeHookContext->heldItemId);
    }
    else
    {
        lua_pushinteger(pLuaState, pParty != nullptr ? pParty->heldItemIdForQueries() : 0);
    }

    return 1;
}

int luaSetHeldItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    Party *pParty = writableParty(pLuaState);
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));

    if (pRuntimeState == nullptr || itemId == 0)
    {
        return 0;
    }

    std::optional<InventoryItem> item = createGrantedEventItem(*pRuntimeState, pParty, 0, 1, 0, itemId);

    if (!item)
    {
        return 0;
    }

    if (lua_istable(pLuaState, 2))
    {
        lua_getfield(pLuaState, 2, "identified");
        if (!lua_isnil(pLuaState, -1))
        {
            item->identified = luaEventBoolean(pLuaState, -1);
        }
        lua_pop(pLuaState, 1);

        lua_getfield(pLuaState, 2, "charges");
        if (lua_isinteger(pLuaState, -1))
        {
            item->currentCharges = static_cast<uint16_t>(std::max<lua_Integer>(0, lua_tointeger(pLuaState, -1)));
        }
        lua_pop(pLuaState, 1);

        lua_getfield(pLuaState, 2, "maxCharges");
        if (lua_isinteger(pLuaState, -1))
        {
            item->maxCharges = static_cast<uint16_t>(std::max<lua_Integer>(0, lua_tointeger(pLuaState, -1)));
        }
        lua_pop(pLuaState, 1);

        lua_getfield(pLuaState, 2, "bonus");
        if (lua_isinteger(pLuaState, -1))
        {
            item->standardEnchantPower = static_cast<uint16_t>(std::max<lua_Integer>(0, lua_tointeger(pLuaState, -1)));
        }
        lua_pop(pLuaState, 1);

        lua_getfield(pLuaState, 2, "enchantment");
        if (lua_isinteger(pLuaState, -1))
        {
            item->standardEnchantId = static_cast<uint16_t>(std::max<lua_Integer>(0, lua_tointeger(pLuaState, -1)));
        }
        lua_pop(pLuaState, 1);

        lua_getfield(pLuaState, 2, "artifact");
        if (lua_isinteger(pLuaState, -1))
        {
            item->artifactId = static_cast<uint16_t>(std::max<lua_Integer>(0, lua_tointeger(pLuaState, -1)));
        }
        lua_pop(pLuaState, 1);
    }

    pRuntimeState->grantedItems.push_back(*item);
    pRuntimeState->clearHeldItemRequest = false;
    return 0;
}

int luaClearHeldItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    Party *pParty = writableParty(pLuaState);

    if (pRuntimeState != nullptr)
    {
        pRuntimeState->clearHeldItemRequest = true;
    }

    if (pParty != nullptr)
    {
        pParty->clearHeldItemForQueries();
    }

    return 0;
}

int luaGetPartyMemberCount(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    lua_pushinteger(pLuaState, pParty != nullptr ? pParty->members().size() : 0);
    return 1;
}

int luaGetCurrentPlayerIndex(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    lua_pushinteger(pLuaState, pParty != nullptr ? static_cast<lua_Integer>(pParty->activeMemberIndex()) : -1);
    return 1;
}

std::string partyPortraitTextureName(uint32_t pictureId)
{
    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", static_cast<unsigned>(pictureId + 1u));
    return buffer;
}

int luaGetPartyMemberPortraitId(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const size_t memberIndex = static_cast<size_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const Character *pMember = pParty != nullptr ? pParty->member(memberIndex) : nullptr;
    lua_pushinteger(pLuaState, pMember != nullptr ? pMember->portraitPictureId : 0);
    return 1;
}

int luaSetPartyMemberPortraitId(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);
    const size_t memberIndex = static_cast<size_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const uint32_t pictureId = static_cast<uint32_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 2)));
    Character *pMember = pParty != nullptr ? pParty->member(memberIndex) : nullptr;

    if (pMember != nullptr)
    {
        pMember->portraitPictureId = pictureId;
        pMember->portraitTextureName = partyPortraitTextureName(pictureId);
        pMember->portraitState = PortraitId::Normal;
        pMember->portraitElapsedTicks = 0;
        pMember->portraitDurationTicks = 0;
        pMember->portraitImageIndex = 0;
    }

    return 0;
}

int luaPartyMemberHasItem(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const size_t memberIndex = static_cast<size_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const Character *pMember = pParty != nullptr ? pParty->member(memberIndex) : nullptr;
    bool hasItem = false;

    if (pMember != nullptr)
    {
        for (const InventoryItem &item : pMember->inventory)
        {
            if (item.objectDescriptionId == itemId)
            {
                hasItem = true;
                break;
            }
        }
    }

    lua_pushboolean(pLuaState, hasItem);
    return 1;
}

int luaPartyMemberItemCount(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const size_t memberIndex = static_cast<size_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const int count = pParty != nullptr ? pParty->inventoryItemCount(itemId, memberIndex) : 0;
    lua_pushinteger(pLuaState, count);
    return 1;
}

int luaGivePartyMemberItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    Party *pParty = writableParty(pLuaState);
    const size_t memberIndex = static_cast<size_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const uint32_t itemId = static_cast<uint32_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 2)));
    const uint32_t quantity = lua_isnoneornil(pLuaState, 3)
        ? 1u
        : static_cast<uint32_t>(std::max<lua_Integer>(1, luaL_checkinteger(pLuaState, 3)));

    if (pRuntimeState == nullptr || pParty == nullptr || itemId == 0)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    std::optional<InventoryItem> item = createGrantedEventItem(*pRuntimeState, pParty, 0, 1, 0, itemId);

    if (!item)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    item->quantity = quantity;
    size_t recipientMemberIndex = 0;
    const bool granted = pParty->tryGrantInventoryItemStartingAt(memberIndex, *item, &recipientMemberIndex);
    lua_pushboolean(pLuaState, granted);
    return 1;
}

int luaReplacePartyInventoryItems(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);
    const uint32_t fromItemId = static_cast<uint32_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const uint32_t toItemId = static_cast<uint32_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 2)));
    int32_t replacedCount = 0;

    if (pParty != nullptr && fromItemId != 0 && toItemId != 0)
    {
        for (size_t memberIndex = 0; memberIndex < pParty->memberCount(); ++memberIndex)
        {
            Character *pMember = pParty->member(memberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            for (InventoryItem &item : pMember->inventory)
            {
                if (item.objectDescriptionId == fromItemId)
                {
                    item.objectDescriptionId = toItemId;
                    ++replacedCount;
                }
            }
        }
    }

    lua_pushinteger(pLuaState, replacedCount);
    return 1;
}

int luaPartyMemberKnowsSpell(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const std::optional<size_t> memberIndex = luaMemberIndexArgument(pLuaState, 1);
    const uint32_t spellId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const Character *pMember = pParty != nullptr && memberIndex ? pParty->member(*memberIndex) : nullptr;
    lua_pushboolean(pLuaState, pMember != nullptr && pMember->knowsSpell(spellId));
    return 1;
}

int luaRemovePartyMemberItem(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);
    const size_t memberIndex = static_cast<size_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const uint32_t quantity = lua_isnoneornil(pLuaState, 3)
        ? 1u
        : static_cast<uint32_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 3)));
    const bool removed = pParty != nullptr && pParty->removeItemFromMember(memberIndex, itemId, quantity);
    lua_pushboolean(pLuaState, removed);
    return 1;
}

int luaApplyLichTransformation(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);
    const size_t memberIndex = static_cast<size_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const bool transformed = pParty != nullptr && pParty->applyLichTransformation(memberIndex);
    lua_pushboolean(pLuaState, transformed);
    return 1;
}

std::optional<EquipmentSlot> equipmentSlotFromLua(lua_State *pLuaState, int index)
{
    if (lua_isnoneornil(pLuaState, index))
    {
        return std::nullopt;
    }

    const int slot = static_cast<int>(luaL_checkinteger(pLuaState, index));

    if (slot < static_cast<int>(EquipmentSlot::OffHand) || slot > static_cast<int>(EquipmentSlot::Ring6))
    {
        return std::nullopt;
    }

    return static_cast<EquipmentSlot>(slot);
}

int luaPartyMemberHasEquippedItem(lua_State *pLuaState)
{
    static constexpr EquipmentSlot EquipmentSlots[] = {
        EquipmentSlot::OffHand,
        EquipmentSlot::MainHand,
        EquipmentSlot::Bow,
        EquipmentSlot::Armor,
        EquipmentSlot::Helm,
        EquipmentSlot::Belt,
        EquipmentSlot::Cloak,
        EquipmentSlot::Gauntlets,
        EquipmentSlot::Boots,
        EquipmentSlot::Amulet,
        EquipmentSlot::Ring1,
        EquipmentSlot::Ring2,
        EquipmentSlot::Ring3,
        EquipmentSlot::Ring4,
        EquipmentSlot::Ring5,
        EquipmentSlot::Ring6,
    };
    const Party *pParty = readableParty(pLuaState);
    const size_t memberIndex = static_cast<size_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const std::optional<EquipmentSlot> slot = equipmentSlotFromLua(pLuaState, 3);
    bool hasItem = false;

    if (pParty != nullptr)
    {
        if (slot)
        {
            hasItem = pParty->equippedItemId(memberIndex, *slot) == itemId;
        }
        else
        {
            for (EquipmentSlot candidateSlot : EquipmentSlots)
            {
                if (pParty->equippedItemId(memberIndex, candidateSlot) == itemId)
                {
                    hasItem = true;
                    break;
                }
            }
        }
    }

    lua_pushboolean(pLuaState, hasItem);
    return 1;
}

int luaGetHookContext(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const EventRuntimeState::ActiveHookContext *pContext =
        pRuntimeState != nullptr && pRuntimeState->activeHookContext
            ? &*pRuntimeState->activeHookContext
            : nullptr;

    lua_newtable(pLuaState);

    if (pContext == nullptr)
    {
        return 1;
    }

    lua_pushinteger(pLuaState, static_cast<int>(pContext->kind));
    lua_setfield(pLuaState, -2, "kind");
    lua_pushinteger(pLuaState, pContext->npcId);
    lua_setfield(pLuaState, -2, "npcId");
    lua_pushinteger(pLuaState, pContext->actorIndex.value_or(0));
    lua_setfield(pLuaState, -2, "actorIndex");
    lua_pushinteger(pLuaState, pContext->monsterId);
    lua_setfield(pLuaState, -2, "monsterId");
    lua_pushinteger(pLuaState, pContext->damage);
    lua_setfield(pLuaState, -2, "damage");
    lua_pushinteger(pLuaState, pContext->damageType);
    lua_setfield(pLuaState, -2, "damageType");
    lua_pushinteger(pLuaState, pContext->houseId);
    lua_setfield(pLuaState, -2, "houseId");
    lua_pushinteger(pLuaState, pContext->houseServiceType);
    lua_setfield(pLuaState, -2, "houseServiceType");
    lua_pushinteger(pLuaState, pContext->menuId);
    lua_setfield(pLuaState, -2, "menuId");
    lua_pushinteger(pLuaState, pContext->houseActionId);
    lua_setfield(pLuaState, -2, "houseActionId");
    lua_pushinteger(pLuaState, pContext->gameplayActionId);
    lua_setfield(pLuaState, -2, "actionId");
    lua_pushinteger(pLuaState, pContext->boundaryEdge);
    lua_setfield(pLuaState, -2, "boundaryEdge");
    lua_pushinteger(pLuaState, pContext->chestId);
    lua_setfield(pLuaState, -2, "chestId");
    lua_pushinteger(pLuaState, pContext->heldItemId);
    lua_setfield(pLuaState, -2, "heldItemId");
    lua_pushinteger(pLuaState, pContext->inventorySource);
    lua_setfield(pLuaState, -2, "inventorySource");
    lua_pushinteger(pLuaState, pContext->inventorySourceIndex);
    lua_setfield(pLuaState, -2, "inventorySourceIndex");
    lua_pushinteger(pLuaState, pContext->inventoryPage);
    lua_setfield(pLuaState, -2, "inventoryPage");
    lua_pushstring(pLuaState, pContext->destinationMapName.c_str());
    lua_setfield(pLuaState, -2, "destinationMapName");
    lua_pushinteger(pLuaState, pContext->baseRestFoodCost);
    lua_setfield(pLuaState, -2, "baseRestFoodCost");
    return 1;
}

int luaSetHookDamage(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState != nullptr && pRuntimeState->activeHookContext)
    {
        const int32_t damage = static_cast<int32_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
        pRuntimeState->activeHookContext->damageOverride = damage;
    }

    return 0;
}

int luaSetHookBlocked(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState != nullptr && pRuntimeState->activeHookContext)
    {
        pRuntimeState->activeHookContext->blocked = luaEventBoolean(pLuaState, 1);

        if (lua_gettop(pLuaState) >= 2 && !lua_isnil(pLuaState, 2))
        {
            pRuntimeState->activeHookContext->statusText = luaL_checkstring(pLuaState, 2);
        }
    }

    return 0;
}

int luaSetHookRestFoodCost(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState != nullptr && pRuntimeState->activeHookContext)
    {
        pRuntimeState->activeHookContext->restFoodCostOverride =
            static_cast<int32_t>(luaL_checkinteger(pLuaState, 1));
    }

    return 0;
}

int luaSetHookHouseTopics(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState == nullptr || !pRuntimeState->activeHookContext || !lua_istable(pLuaState, 1))
    {
        return 0;
    }

    std::vector<uint32_t> actionIds;
    const lua_Integer count = luaL_len(pLuaState, 1);

    for (lua_Integer index = 1; index <= count; ++index)
    {
        lua_geti(pLuaState, 1, index);

        if (lua_isinteger(pLuaState, -1))
        {
            const lua_Integer rawActionId = lua_tointeger(pLuaState, -1);

            if (rawActionId > 0)
            {
                actionIds.push_back(static_cast<uint32_t>(rawActionId));
            }
        }

        lua_pop(pLuaState, 1);
    }

    pRuntimeState->activeHookContext->houseTopicActionIds = std::move(actionIds);
    return 0;
}

int luaPlaySound(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t soundId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const int32_t x = static_cast<int32_t>(luaL_optinteger(pLuaState, 2, 0));
    const int32_t y = static_cast<int32_t>(luaL_optinteger(pLuaState, 3, 0));
    queuePendingSound(*pRuntimeState, soundId, x, y, x != 0 || y != 0);
    return 0;
}

int luaMoveNpc(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t houseId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    pRuntimeState->npcHouseOverrides[npcId] = houseId;

    if (pExecutionContext->pParty != nullptr)
    {
        pExecutionContext->pParty->setNpcHouseOverride(npcId, houseId);
    }

    return 0;
}

int luaRandomJump(lua_State *pLuaState)
{
    const uint16_t eventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    const uint8_t step = static_cast<uint8_t>(luaL_checkinteger(pLuaState, 2));
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    luaL_checktype(pLuaState, 3, LUA_TTABLE);

    const size_t count = lua_rawlen(pLuaState, 3);
    std::vector<uint32_t> validTargets;
    validTargets.reserve(count);

    for (size_t index = 1; index <= count; ++index)
    {
        lua_rawgeti(pLuaState, 3, index);
        const uint32_t target = static_cast<uint32_t>(lua_tointeger(pLuaState, -1));

        if (target != 0)
        {
            validTargets.push_back(target);
        }

        lua_pop(pLuaState, 1);
    }

    if (validTargets.empty())
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const uint32_t randomValue = nextEventRandom(eventId, step, *pRuntimeState);
    lua_pushinteger(pLuaState, validTargets[randomValue % validTargets.size()]);
    return 1;
}

int luaDamagePlayer(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);

    if (pParty == nullptr)
    {
        return 0;
    }

    const PartySelector selector = decodePartySelector(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)));
    const int damage = static_cast<int>(luaL_checkinteger(pLuaState, 3));
    std::vector<size_t> targets = resolveTargetMemberIndices(selector, pParty);

    if (targets.empty())
    {
        targets = selectedTargetMemberIndices(pLuaState);
    }

    const std::string status = damageStatusForEvtVariable(targets);

    for (size_t memberIndex : targets)
    {
        pParty->applyDamageToMember(memberIndex, damage, status);
    }

    return 0;
}

int luaSetSnow(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)) == 0)
    {
        pRuntimeState->snowEnabled = luaEventBoolean(pLuaState, 2);
    }

    return 0;
}

int luaSetRain(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)) == 0)
    {
        pRuntimeState->rainEnabled = luaEventBoolean(pLuaState, 2);
    }

    return 0;
}

int luaSetOutdoorSky(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (lua_gettop(pLuaState) >= 1 && lua_type(pLuaState, 1) == LUA_TSTRING)
    {
        pRuntimeState->outdoorSkyTextureOverride = sanitizeEventString(lua_tostring(pLuaState, 1));
    }
    else
    {
        pRuntimeState->outdoorSkyTextureOverride.reset();
    }

    return 0;
}

int luaSetOutdoorFog(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (lua_gettop(pLuaState) >= 2)
    {
        pRuntimeState->outdoorFogWeakDistanceOverride =
            static_cast<int32_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 1)));
        pRuntimeState->outdoorFogStrongDistanceOverride =
            static_cast<int32_t>(std::max<lua_Integer>(0, luaL_checkinteger(pLuaState, 2)));
    }
    else
    {
        pRuntimeState->outdoorFogWeakDistanceOverride.reset();
        pRuntimeState->outdoorFogStrongDistanceOverride.reset();
    }

    return 0;
}

int luaOpenDimensionDoor(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->pendingDimensionDoorOverlay = true;
    pRuntimeState->lastActivationResult = "You feel high magic presence here.";
    return 0;
}

int luaClearDimensionDoorOverlay(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->pendingDimensionDoorOverlay = false;
    return 0;
}

void ensureMapEventDialogueContext(lua_State *pLuaState, EventRuntimeState &runtimeState)
{
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext != nullptr && !pExecutionContext->allowStandaloneMapEventDialogueContext)
    {
        return;
    }

    if (runtimeState.pendingDialogueContext
        && runtimeState.pendingDialogueContext->kind != DialogueContextKind::None)
    {
        return;
    }

    runtimeState.messages.clear();

    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::MapEvent;
    runtimeState.pendingDialogueContext = std::move(context);
}

int luaShowMovie(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    EventRuntimeState::PendingMovie movie = {};
    movie.movieName = sanitizeEventString(luaL_checkstring(pLuaState, 1));
    movie.restoreAfterPlayback = luaEventBoolean(pLuaState, 2);
    pRuntimeState->pendingMovie = std::move(movie);
    return 0;
}

int luaReturnToMainMenu(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState != nullptr)
    {
        pRuntimeState->pendingReturnToMainMenu = true;
    }

    return 0;
}

int luaSetSprite(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const uint32_t cogNumber = eventReferenceId(luaL_checkinteger(pLuaState, 1));
    const bool visible = luaEventBoolean(pLuaState, 2);
    EventRuntimeState::SpriteOverride spriteOverride = {};
    spriteOverride.hidden = !visible;

    if (lua_gettop(pLuaState) >= 3 && lua_type(pLuaState, 3) == LUA_TSTRING)
    {
        spriteOverride.textureName = sanitizeEventString(lua_tostring(pLuaState, 3));
    }

    pRuntimeState->spriteOverrides[cogNumber] = std::move(spriteOverride);
    GAMEPLAY_DEBUG_TRACE(
        std::string("event_set_sprite")
        + " map=\"" + pRuntimeState->mapFileName + "\""
        + " event_id=" + std::to_string(pExecutionContext != nullptr ? pExecutionContext->currentEventId : 0)
        + " cog=" + std::to_string(cogNumber)
        + " visible=" + (visible ? std::string("true") : std::string("false"))
        + " hidden=" + (!visible ? std::string("true") : std::string("false"))
        + " texture=" + traceQuoted(spriteOverride.textureName.value_or(std::string())));
    return 0;
}

int luaEnterHouse(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t houseId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    pRuntimeState->messages.clear();

    if (houseId == PseudoHouseId::ThroneroomWinGood || houseId == PseudoHouseId::ThroneroomWinEvil)
    {
        EventRuntimeState::PendingWinGame ending = {};
        ending.houseId = houseId;
        pRuntimeState->pendingDialogueContext.reset();
        pRuntimeState->dialogueState = {};
        pRuntimeState->pendingWinGame = ending;
        return 0;
    }

    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::HouseService;
    context.sourceId = houseId;
    context.hostHouseId = context.sourceId;
    context.mapNoteSourcePoint = pRuntimeState->activeEventMapNoteSourcePoint;
    pRuntimeState->dialogueState.hostHouseId = context.sourceId;
    pRuntimeState->pendingDialogueContext = std::move(context);

    return 0;
}

int luaSpeakNpc(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->messages.clear();
    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::NpcTalk;
    context.sourceId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    context.hostHouseId = pRuntimeState->dialogueState.hostHouseId;
    pRuntimeState->pendingDialogueContext = std::move(context);
    return 0;
}

int luaMoveToMap(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    EventRuntimeState::PendingMapMove move = {};
    const int argumentCount = lua_gettop(pLuaState);
    move.x = static_cast<int32_t>(luaL_checkinteger(pLuaState, 1));
    move.y = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
    move.z = static_cast<int32_t>(luaL_checkinteger(pLuaState, 3));

    std::optional<int32_t> yawUnits;

    if (argumentCount >= 4 && lua_type(pLuaState, 4) != LUA_TNIL)
    {
        yawUnits = static_cast<int32_t>(luaL_checkinteger(pLuaState, 4));
        move.directionDegrees = moveToMapYawUnitsToDegrees(*yawUnits);
    }

    int mapNameArgumentIndex = 0;

    if (argumentCount >= 9 && lua_type(pLuaState, 9) == LUA_TSTRING)
    {
        mapNameArgumentIndex = 9;
    }
    else if (argumentCount >= 5 && lua_type(pLuaState, 5) == LUA_TSTRING)
    {
        mapNameArgumentIndex = 5;
    }

    if (mapNameArgumentIndex != 0)
    {
        const std::string mapName = sanitizeEventString(lua_tostring(pLuaState, mapNameArgumentIndex));

        if (!mapName.empty() && !isCurrentMapMoveSentinel(mapName))
        {
            move.mapName = mapName;
        }
    }

    if (pExecutionContext != nullptr)
    {
        move.traceSourceKind = "lua_event";
        move.traceEventId = pExecutionContext->currentEventId;
        move.traceDestinationName = move.mapName.value_or(std::string("current_map"));
    }

    if (move.mapName.has_value() && move.x == 0 && move.y == 0 && move.z == 0)
    {
        move.useMapStartPosition = true;

        if (yawUnits.has_value() && *yawUnits == 0)
        {
            move.directionDegrees.reset();
        }
    }

    const uint32_t transitionTextId =
        argumentCount >= 7 && lua_type(pLuaState, 7) != LUA_TNIL
            ? static_cast<uint32_t>(std::max(0, static_cast<int>(luaL_checkinteger(pLuaState, 7))))
            : 0u;
    const uint32_t transitionImageId =
        argumentCount >= 8 && lua_type(pLuaState, 8) != LUA_TNIL
            ? static_cast<uint32_t>(std::max(0, static_cast<int>(luaL_checkinteger(pLuaState, 8))))
            : 0u;

    if (transitionTextId != 0 || transitionImageId != 0 || moveToMapLeavesIndoorDungeon(pExecutionContext, move))
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::MapTransition;
        context.transitionMapMove = std::move(move);
        context.transitionTextId = transitionTextId;
        context.transitionImageId = transitionImageId;
        pRuntimeState->pendingDialogueContext = std::move(context);
    }
    else
    {
        GAMEPLAY_DEBUG_TRACE(
            "event_move_to_map_queued map=\"" + pRuntimeState->mapFileName + "\""
            + " event_id=" + std::to_string(pExecutionContext != nullptr ? pExecutionContext->currentEventId : 0)
            + " scope=\""
            + (pExecutionContext != nullptr && pExecutionContext->executingGlobalHandler ? "global" : "local")
            + "\" target_map=\"" + move.mapName.value_or(std::string("current_map")) + "\""
            + " use_start_position=" + (move.useMapStartPosition ? std::string("true") : std::string("false"))
            + " pos=(" + std::to_string(move.x)
            + "," + std::to_string(move.y)
            + "," + std::to_string(move.z) + ")"
            + " direction_degrees="
            + (move.directionDegrees.has_value() ? std::to_string(*move.directionDegrees) : std::string("none")));
        pRuntimeState->pendingMapMove = std::move(move);
    }

    return 0;
}

int luaCastSpell(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || pExecutionContext->pSceneEventContext == nullptr)
    {
        return 0;
    }

    pExecutionContext->pSceneEventContext->castEventSpell(
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)),
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2)),
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 3)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 4)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 5)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 6)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 7)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 8)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 9)));
    return 0;
}

int luaFaceExpression(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);

    if (pParty == nullptr)
    {
        return 0;
    }

    const std::optional<PortraitId> portraitId = eventPortraitId(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)));

    if (!portraitId)
    {
        return 0;
    }

    for (size_t memberIndex : selectedTargetMemberIndices(pLuaState))
    {
        Character *pMember = pParty->member(memberIndex);

        if (pMember == nullptr)
        {
            continue;
        }

        pMember->portraitState = *portraitId;
        pMember->portraitElapsedTicks = 0;
        pMember->portraitDurationTicks = DefaultEventPortraitDurationTicks;
        pMember->portraitSequenceCounter += 1;
    }

    return 0;
}

int luaCheckItemsCount(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const int32_t currentCount = EventRuntime::getInventoryItemCount(
        *pRuntimeState,
        readableParty(pLuaState),
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)),
        singleTargetMemberIndex(selectedTargetMemberIndices(pLuaState)));
    lua_pushboolean(pLuaState, currentCount >= static_cast<int32_t>(luaL_checkinteger(pLuaState, 2)));
    return 1;
}

int luaCheckSkill(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);

    if (pParty == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const int rawSkillArgument = std::max(0, static_cast<int>(luaL_checkinteger(pLuaState, 1)));
    const int rawMasteryArgument = std::max(0, static_cast<int>(luaL_checkinteger(pLuaState, 2)));
    const std::optional<std::string> skillName =
        skillNameForCheckSkillArgument(static_cast<uint32_t>(rawSkillArgument));
    const uint32_t level = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 3));
    bool passed = false;

    if (!skillName)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    if (Party::isPartyWideUtilitySkill(*skillName))
    {
        const std::optional<size_t> memberIndex = pParty->bestPartyWideUtilitySkillMemberIndex(*skillName);
        const Character *pMember = memberIndex ? pParty->member(*memberIndex) : nullptr;
        passed =
            pMember != nullptr
            && characterMeetsSkillCheck(*pMember, *skillName, static_cast<uint32_t>(rawMasteryArgument), level);
    }
    else
    {
        for (size_t memberIndex : selectedTargetMemberIndices(pLuaState))
        {
            const Character *pMember = pParty->member(memberIndex);

            if (pMember != nullptr
                && characterMeetsSkillCheck(*pMember, *skillName, static_cast<uint32_t>(rawMasteryArgument), level))
            {
                passed = true;
                break;
            }
        }
    }

    lua_pushboolean(pLuaState, passed);
    return 1;
}

int luaSummonItem(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || pExecutionContext->pSceneEventContext == nullptr)
    {
        return 0;
    }

    pExecutionContext->pSceneEventContext->summonEventItem(
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 2)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 3)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 4)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 5)),
        static_cast<uint32_t>(luaL_optinteger(pLuaState, 6, 1)),
        luaEventBoolean(pLuaState, 7));
    return 0;
}

int luaSetMonsterGroup(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->actorIdGroupOverrides[static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))] =
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    return 0;
}

int luaSetNpcGreeting(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t greetingId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    pRuntimeState->npcGreetingOverrides[npcId] = greetingId;
    pRuntimeState->npcGreetingDisplayCounts[npcId] = 0;

    if (pExecutionContext->pParty != nullptr)
    {
        pExecutionContext->pParty->setNpcGreetingOverride(npcId, greetingId);
    }

    return 0;
}

int luaSetNpcName(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const char *pName = luaL_checkstring(pLuaState, 2);

    if (pRuntimeState != nullptr)
    {
        if (pName[0] == '\0')
        {
            pRuntimeState->npcNameOverrides.erase(npcId);
        }
        else
        {
            pRuntimeState->npcNameOverrides[npcId] = pName;
        }
    }

    return 0;
}

int luaSetNpcPicture(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t pictureId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));

    if (pRuntimeState != nullptr)
    {
        if (pictureId == 0)
        {
            pRuntimeState->npcPictureOverrides.erase(npcId);
        }
        else
        {
            pRuntimeState->npcPictureOverrides[npcId] = pictureId;
        }
    }

    return 0;
}

int luaSetNpcProfession(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t professionId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));

    if (pRuntimeState != nullptr)
    {
        if (professionId == 0)
        {
            pRuntimeState->npcProfessionOverrides.erase(npcId);
        }
        else
        {
            pRuntimeState->npcProfessionOverrides[npcId] = professionId;
        }
    }

    return 0;
}

int luaSetNpcItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isGive = lua_gettop(pLuaState) < 3 || luaEventBoolean(pLuaState, 3);
    pRuntimeState->npcItemOverrides[npcId] = isGive ? itemId : 0;

    if (pExecutionContext->pParty != nullptr)
    {
        pExecutionContext->pParty->setNpcItemOverride(npcId, isGive ? itemId : 0);
    }

    return 0;
}

int luaSetMonsterItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t actorId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isGive = lua_gettop(pLuaState) < 3 || luaEventBoolean(pLuaState, 3);

    if (isGive && itemId != 0)
    {
        const auto primaryIterator = pRuntimeState->actorItemOverrides.find(actorId);

        if (primaryIterator == pRuntimeState->actorItemOverrides.end() || primaryIterator->second == 0)
        {
            pRuntimeState->actorItemOverrides[actorId] = itemId;
        }
        else if (primaryIterator->second != itemId)
        {
            std::vector<uint32_t> &extraItems = pRuntimeState->actorExtraItemOverrides[actorId];

            if (std::find(extraItems.begin(), extraItems.end(), itemId) == extraItems.end())
            {
                extraItems.push_back(itemId);
            }
        }

        pRuntimeState->actorSetMasks[actorId] |= static_cast<uint32_t>(EvtActorAttribute::HasItem);
        pRuntimeState->actorClearMasks[actorId] &= ~static_cast<uint32_t>(EvtActorAttribute::HasItem);
    }
    else
    {
        pRuntimeState->actorItemOverrides.erase(actorId);
        pRuntimeState->actorExtraItemOverrides.erase(actorId);
        pRuntimeState->actorClearMasks[actorId] |= static_cast<uint32_t>(EvtActorAttribute::HasItem);
        pRuntimeState->actorSetMasks[actorId] &= ~static_cast<uint32_t>(EvtActorAttribute::HasItem);
    }

    return 0;
}

int luaFaceAnimation(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);

    if (pParty == nullptr)
    {
        return 0;
    }

    const uint32_t legacyFaceAnimationId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const std::optional<SpeechId> speechId = speechIdForLegacyFaceAnimationId(legacyFaceAnimationId);

    if (!speechId)
    {
        return 0;
    }

    if (legacyFaceAnimationId == static_cast<uint32_t>(FaceAnimationId::DoorLocked))
    {
        pParty->requestSpeech(pParty->activeMemberIndex(), *speechId);
        return 0;
    }

    for (size_t memberIndex : selectedTargetMemberIndices(pLuaState))
    {
        pParty->requestSpeech(memberIndex, *speechId);
    }

    return 0;
}

int luaChangeGroupToGroup(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->actorGroupOverrides[static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))] =
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    return 0;
}

int luaChangeGroupAlly(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->actorGroupAllyOverrides[static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))] =
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    return 0;
}

int luaCheckSeason(lua_State *pLuaState)
{
    lua_pushboolean(
        pLuaState,
        currentSeasonFromRuntimeState(*readableRuntimeState(pLuaState))
            == static_cast<EvtSeason>(luaL_checkinteger(pLuaState, 1)));
    return 1;
}

int luaSetChestBit(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t chestId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t flag = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isOn = luaEventBoolean(pLuaState, 3);

    if (isOn)
    {
        pRuntimeState->chestSetMasks[chestId] |= flag;
        pRuntimeState->chestClearMasks[chestId] &= ~flag;
    }
    else
    {
        pRuntimeState->chestClearMasks[chestId] |= flag;
        pRuntimeState->chestSetMasks[chestId] &= ~flag;
    }

    if ((flag & static_cast<uint32_t>(EvtChestFlag::Opened)) != 0 && isOn)
    {
        pRuntimeState->openedChestIds.push_back(chestId);
        pRuntimeState->openedChestRequests.push_back(
            EventRuntimeState::OpenedChestRequest{
                .chestId = chestId,
                .openedByTelekinesis = pRuntimeState->activeEventOpenedByTelekinesis,
            });
    }

    return 0;
}

int luaEnsureChestItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    const uint32_t chestId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    EventRuntimeState::ChestItemRequest request = {};
    request.itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    request.gridX = static_cast<uint8_t>(std::clamp(static_cast<int>(luaL_optinteger(pLuaState, 3, 0)), 0, 255));
    request.gridY = static_cast<uint8_t>(std::clamp(static_cast<int>(luaL_optinteger(pLuaState, 4, 0)), 0, 255));

    if (request.itemId != 0)
    {
        pRuntimeState->chestItemRequests[chestId].push_back(request);
    }

    return 0;
}

int luaRemoveFollowerProfession(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t professionId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));

    if (pRuntimeState == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const auto iterator = std::find_if(
        pRuntimeState->hiredNpcFollowers.begin(),
        pRuntimeState->hiredNpcFollowers.end(),
        [professionId](const EventRuntimeState::HiredNpcFollower &follower)
        {
            return follower.professionId == professionId;
        });

    if (iterator != pRuntimeState->hiredNpcFollowers.end())
    {
        const uint32_t npcId = iterator->npcId;
        pRuntimeState->hiredNpcFollowers.erase(iterator);
        pRuntimeState->unavailableNpcIds.erase(npcId);

        Party *pParty = writableParty(pLuaState);
        if (pParty != nullptr)
        {
            pParty->removeHiredNpcFollower(npcId);
            pParty->setNpcUnavailable(npcId, false);
        }

        lua_pushboolean(pLuaState, 1);
        return 1;
    }

    lua_pushboolean(pLuaState, 0);
    return 1;
}

int luaHasFollowerNpc(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));

    if (pRuntimeState == nullptr || npcId == 0)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const bool hasFollower = std::find_if(
        pRuntimeState->hiredNpcFollowers.begin(),
        pRuntimeState->hiredNpcFollowers.end(),
        [npcId](const EventRuntimeState::HiredNpcFollower &follower)
        {
            return follower.npcId == npcId;
        }) != pRuntimeState->hiredNpcFollowers.end();

    lua_pushboolean(pLuaState, hasFollower ? 1 : 0);
    return 1;
}

int luaAddFollowerNpc(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t professionId = static_cast<uint32_t>(luaL_optinteger(pLuaState, 2, 0));
    const uint32_t weeklyCost = static_cast<uint32_t>(luaL_optinteger(pLuaState, 3, 0));

    if (pRuntimeState == nullptr || npcId == 0)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    EventRuntimeState::HiredNpcFollower follower = {};
    follower.npcId = npcId;
    follower.professionId = professionId;
    follower.weeklyCost = weeklyCost;

    const auto iterator = std::find_if(
        pRuntimeState->hiredNpcFollowers.begin(),
        pRuntimeState->hiredNpcFollowers.end(),
        [npcId](const EventRuntimeState::HiredNpcFollower &existingFollower)
        {
            return existingFollower.npcId == npcId;
        });

    if (iterator == pRuntimeState->hiredNpcFollowers.end())
    {
        pRuntimeState->hiredNpcFollowers.push_back(follower);
    }
    else
    {
        *iterator = follower;
    }

    pRuntimeState->unavailableNpcIds.insert(npcId);

    Party *pParty = writableParty(pLuaState);
    if (pParty != nullptr)
    {
        pParty->addHiredNpcFollower(follower);
        pParty->setNpcUnavailable(npcId, true);
    }

    lua_pushboolean(pLuaState, 1);
    return 1;
}

int luaRemoveFollowerNpc(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));

    if (pRuntimeState == nullptr || npcId == 0)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const auto iterator = std::remove_if(
        pRuntimeState->hiredNpcFollowers.begin(),
        pRuntimeState->hiredNpcFollowers.end(),
        [npcId](const EventRuntimeState::HiredNpcFollower &follower)
        {
            return follower.npcId == npcId;
        });

    const bool removed = iterator != pRuntimeState->hiredNpcFollowers.end();
    if (removed)
    {
        pRuntimeState->hiredNpcFollowers.erase(iterator, pRuntimeState->hiredNpcFollowers.end());
    }

    pRuntimeState->unavailableNpcIds.erase(npcId);

    Party *pParty = writableParty(pLuaState);
    if (pParty != nullptr)
    {
        pParty->removeHiredNpcFollower(npcId);
        pParty->setNpcUnavailable(npcId, false);
    }

    lua_pushboolean(pLuaState, removed ? 1 : 0);
    return 1;
}

int luaCurrentGameMinutes(lua_State *pLuaState)
{
    const ISceneEventContext *pSceneEventContext = readonlySceneEventContext(executionContextFromLua(pLuaState));
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const int32_t currentGameMinutes = pSceneEventContext != nullptr
        ? std::max(0, floorToInt(pSceneEventContext->currentGameMinutes()))
        : (pRuntimeState != nullptr ? currentGameMinutesFromRuntimeState(*pRuntimeState) : 0);
    lua_pushinteger(pLuaState, currentGameMinutes);
    return 1;
}

int luaAdvanceGameMinutes(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const float minutes = static_cast<float>(luaL_checknumber(pLuaState, 1));

    if (pExecutionContext == nullptr || pExecutionContext->readonly || minutes == 0.0f)
    {
        return 0;
    }

    IGameplayWorldRuntime *pWorldRuntime = dynamic_cast<IGameplayWorldRuntime *>(pExecutionContext->pSceneEventContext);
    if (pWorldRuntime != nullptr)
    {
        pWorldRuntime->advanceGameMinutes(minutes);
    }

    return 0;
}

int luaGetRuntimeVariable(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const uint32_t rawVariableId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));

    if (pRuntimeState == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = pRuntimeState->variables.find(rawVariableId);
    lua_pushinteger(pLuaState, iterator != pRuntimeState->variables.end() ? iterator->second : 0);
    return 1;
}

int luaSetRuntimeVariable(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t rawVariableId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const int32_t value = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));

    if (pRuntimeState != nullptr)
    {
        if (value == 0)
        {
            pRuntimeState->variables.erase(rawVariableId);
        }
        else
        {
            pRuntimeState->variables[rawVariableId] = value;
        }
    }

    return 0;
}

int luaGetActiveEventSpellId(lua_State *pLuaState)
{
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    lua_pushinteger(pLuaState, pRuntimeState != nullptr ? pRuntimeState->activeEventSpellId : 0);
    return 1;
}

int luaGetPartyVariable(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const uint16_t variableId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    lua_pushinteger(pLuaState, pParty != nullptr ? pParty->eventVariableValue(variableId) : 0);
    return 1;
}

int luaSetPartyVariable(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);
    const uint16_t variableId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    const int32_t value = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));

    if (pParty != nullptr)
    {
        pParty->setEventVariableValue(variableId, value);
    }

    return 0;
}

int luaGetClassId(lua_State *pLuaState)
{
    const char *pClassName = luaL_checkstring(pLuaState, 1);
    const std::optional<uint32_t> classId =
        tableBackedClassIdForName(readableParty(pLuaState), pClassName != nullptr ? pClassName : "");
    lua_pushinteger(pLuaState, classId ? static_cast<lua_Integer>(*classId) : -1);
    return 1;
}

int luaGetClassName(lua_State *pLuaState)
{
    const uint32_t classId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const std::optional<std::string> className = tableBackedClassNameForId(readableParty(pLuaState), classId);
    lua_pushstring(pLuaState, className ? className->c_str() : "");
    return 1;
}

int luaGetPlayerClass(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const std::optional<size_t> memberIndex = luaMemberIndexArgument(pLuaState, 1);
    const Character *pMember = pParty != nullptr && memberIndex ? pParty->member(*memberIndex) : nullptr;

    if (pMember == nullptr)
    {
        lua_pushinteger(pLuaState, -1);
        return 1;
    }

    const std::optional<uint32_t> classId = tableBackedClassIdForName(pParty, pMember->className);
    lua_pushinteger(pLuaState, classId ? static_cast<lua_Integer>(*classId) : -1);
    return 1;
}

int luaGetPlayerClassName(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const std::optional<size_t> memberIndex = luaMemberIndexArgument(pLuaState, 1);
    const Character *pMember = pParty != nullptr && memberIndex ? pParty->member(*memberIndex) : nullptr;
    lua_pushstring(pLuaState, pMember != nullptr ? pMember->className.c_str() : "");
    return 1;
}

int luaSetPlayerClass(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);
    const std::optional<size_t> memberIndex = luaMemberIndexArgument(pLuaState, 1);
    const std::optional<std::string> className = luaClassNameArgument(pLuaState, 2);

    if (pParty == nullptr || !memberIndex || !className)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    lua_pushboolean(pLuaState, pParty->setMemberClassName(*memberIndex, *className) ? 1 : 0);
    return 1;
}

int luaGetClassSkillCap(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const ClassSkillTable *pClassSkillTable = pParty != nullptr ? pParty->classSkillTable() : nullptr;
    const std::optional<std::string> className = luaClassNameArgument(pLuaState, 1);
    const char *pSkillName = luaL_checkstring(pLuaState, 2);

    if (pClassSkillTable == nullptr || !className || pSkillName == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    lua_pushinteger(
        pLuaState,
        static_cast<lua_Integer>(pClassSkillTable->getClassCap(*className, pSkillName)));
    return 1;
}

int luaCanClassLearnSkill(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const ClassSkillTable *pClassSkillTable = pParty != nullptr ? pParty->classSkillTable() : nullptr;
    const std::optional<std::string> className = luaClassNameArgument(pLuaState, 1);
    const char *pSkillName = luaL_checkstring(pLuaState, 2);
    const SkillMastery requiredMastery =
        static_cast<SkillMastery>(std::clamp(static_cast<int>(luaL_optinteger(pLuaState, 3, 1)), 1, 4));

    lua_pushboolean(
        pLuaState,
        pClassSkillTable != nullptr
            && className
            && pSkillName != nullptr
            && pClassSkillTable->getClassCap(*className, pSkillName) >= requiredMastery);
    return 1;
}

int luaCanPlayerLearnSkill(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const std::optional<size_t> memberIndex = luaMemberIndexArgument(pLuaState, 1);
    const Character *pMember = pParty != nullptr && memberIndex ? pParty->member(*memberIndex) : nullptr;
    const ClassSkillTable *pClassSkillTable = pParty != nullptr ? pParty->classSkillTable() : nullptr;
    const char *pSkillName = luaL_checkstring(pLuaState, 2);
    const SkillMastery requiredMastery =
        static_cast<SkillMastery>(std::clamp(static_cast<int>(luaL_optinteger(pLuaState, 3, 1)), 1, 4));

    lua_pushboolean(
        pLuaState,
        pMember != nullptr
            && pClassSkillTable != nullptr
            && pSkillName != nullptr
            && pClassSkillTable->getEffectiveCap(pMember->className, pMember->raceId, pSkillName)
                >= requiredMastery);
    return 1;
}

void appendLuaStringTable(lua_State *pLuaState, int tableIndex, std::vector<std::string> &values)
{
    const lua_Integer tableLength = static_cast<lua_Integer>(lua_rawlen(pLuaState, tableIndex));

    for (lua_Integer index = 1; index <= tableLength; ++index)
    {
        lua_rawgeti(pLuaState, tableIndex, index);

        if (lua_type(pLuaState, -1) == LUA_TSTRING)
        {
            const char *pValue = lua_tostring(pLuaState, -1);
            values.emplace_back(pValue != nullptr ? pValue : "");
        }

        lua_pop(pLuaState, 1);
    }
}

bool appendPendingMessageText(lua_State *pLuaState, EventRuntimeState &runtimeState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || !pExecutionContext->pendingMessageText)
    {
        return false;
    }

    runtimeState.messages.push_back(*pExecutionContext->pendingMessageText);
    pExecutionContext->pendingMessageText.reset();
    return true;
}

void tracePendingInputPromptCreated(
    const EventRuntimeState &runtimeState,
    const EventRuntimeState::PendingInputPrompt &prompt,
    const char *pSource)
{
    const char *pContextKind = "none";

    if (runtimeState.pendingDialogueContext)
    {
        switch (runtimeState.pendingDialogueContext->kind)
        {
            case DialogueContextKind::None:
                pContextKind = "none";
                break;
            case DialogueContextKind::MapEvent:
                pContextKind = "map_event";
                break;
            case DialogueContextKind::MapTransition:
                pContextKind = "map_transition";
                break;
            case DialogueContextKind::HouseService:
                pContextKind = "house_service";
                break;
            case DialogueContextKind::NpcTalk:
                pContextKind = "npc_talk";
                break;
            case DialogueContextKind::NpcNews:
                pContextKind = "npc_news";
                break;
        }
    }

    GAMEPLAY_DEBUG_TRACE(
        std::string("input_prompt_created source=") + pSource
        + " map=" + traceQuoted(runtimeState.mapFileName)
        + " context=" + pContextKind
        + " event_id=" + std::to_string(prompt.eventId)
        + " continue_step=" + std::to_string(prompt.continueStep)
        + " correct_step=" + std::to_string(prompt.correctStep)
        + " text_id=" + std::to_string(prompt.textId)
        + " prompt=" + traceQuoted(prompt.text.value_or(std::string()))
        + " answer_count=" + std::to_string(prompt.answers.size())
        + " message_count=" + std::to_string(runtimeState.messages.size()));
}

int luaAskQuestion(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    ensureMapEventDialogueContext(pLuaState, *pRuntimeState);

    EventRuntimeState::PendingInputPrompt prompt = {};
    prompt.kind = EventRuntimeState::PendingInputPrompt::Kind::InputString;
    prompt.eventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    prompt.continueStep = static_cast<uint8_t>(luaL_checkinteger(pLuaState, 2));
    prompt.textId = static_cast<uint32_t>(luaL_optinteger(pLuaState, 3, 0));

    const int argumentCount = lua_gettop(pLuaState);
    int textArgumentIndex = 4;

    if (argumentCount >= 4 && lua_type(pLuaState, 4) == LUA_TNUMBER)
    {
        prompt.correctStep = static_cast<uint8_t>(lua_tointeger(pLuaState, 4));
        textArgumentIndex = 5;

        for (int argumentIndex = 5; argumentIndex <= argumentCount; ++argumentIndex)
        {
            if (lua_type(pLuaState, argumentIndex) == LUA_TNUMBER)
            {
                prompt.answerTextIds.push_back(static_cast<uint32_t>(lua_tointeger(pLuaState, argumentIndex)));
                textArgumentIndex = argumentIndex + 1;
                continue;
            }

            break;
        }
    }

    for (int argumentIndex = textArgumentIndex; argumentIndex <= argumentCount; ++argumentIndex)
    {
        if (lua_type(pLuaState, argumentIndex) == LUA_TTABLE && prompt.text)
        {
            appendLuaStringTable(pLuaState, argumentIndex, prompt.answers);
            continue;
        }

        if (lua_type(pLuaState, argumentIndex) == LUA_TSTRING)
        {
            const char *pText = lua_tostring(pLuaState, argumentIndex);

            if (prompt.text)
            {
                prompt.answers.emplace_back(pText != nullptr ? pText : "");
            }
            else
            {
                prompt.text = pText != nullptr ? pText : "";
            }
        }
    }

    if (!appendPendingMessageText(pLuaState, *pRuntimeState)
        && pRuntimeState->messages.empty()
        && prompt.text
        && !prompt.text->empty())
    {
        pRuntimeState->messages.push_back(*prompt.text);
    }

    tracePendingInputPromptCreated(*pRuntimeState, prompt, "AskQuestion");
    pRuntimeState->pendingInputPrompt = std::move(prompt);
    return 0;
}

int luaAskQuestionWithAnswerSteps(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    ensureMapEventDialogueContext(pLuaState, *pRuntimeState);

    EventRuntimeState::PendingInputPrompt prompt = {};
    prompt.kind = EventRuntimeState::PendingInputPrompt::Kind::InputString;
    prompt.eventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    prompt.continueStep = static_cast<uint8_t>(luaL_checkinteger(pLuaState, 2));
    prompt.text = luaL_checkstring(pLuaState, 3);

    luaL_checktype(pLuaState, 4, LUA_TTABLE);
    const lua_Integer choiceCount = static_cast<lua_Integer>(lua_rawlen(pLuaState, 4));

    for (lua_Integer choiceIndex = 1; choiceIndex <= choiceCount; ++choiceIndex)
    {
        lua_rawgeti(pLuaState, 4, choiceIndex);

        if (lua_type(pLuaState, -1) == LUA_TTABLE)
        {
            lua_getfield(pLuaState, -1, "Answer");
            const char *pAnswer = lua_tostring(pLuaState, -1);
            std::string answer = pAnswer != nullptr ? pAnswer : "";
            lua_pop(pLuaState, 1);

            if (answer.empty())
            {
                lua_rawgeti(pLuaState, -1, 1);
                pAnswer = lua_tostring(pLuaState, -1);
                answer = pAnswer != nullptr ? pAnswer : "";
                lua_pop(pLuaState, 1);
            }

            lua_getfield(pLuaState, -1, "Step");
            uint8_t step = static_cast<uint8_t>(lua_tointeger(pLuaState, -1));
            lua_pop(pLuaState, 1);

            if (step == 0)
            {
                lua_rawgeti(pLuaState, -1, 2);
                step = static_cast<uint8_t>(lua_tointeger(pLuaState, -1));
                lua_pop(pLuaState, 1);
            }

            prompt.answers.push_back(answer);
            prompt.answerContinueSteps.push_back(step);
        }
        else if (lua_type(pLuaState, -1) == LUA_TSTRING)
        {
            prompt.answers.emplace_back(lua_tostring(pLuaState, -1));
            prompt.answerContinueSteps.push_back(0);
        }

        lua_pop(pLuaState, 1);
    }

    if (!appendPendingMessageText(pLuaState, *pRuntimeState)
        && pRuntimeState->messages.empty()
        && prompt.text
        && !prompt.text->empty())
    {
        pRuntimeState->messages.push_back(*prompt.text);
    }

    tracePendingInputPromptCreated(*pRuntimeState, prompt, "AskQuestionWithAnswerSteps");
    pRuntimeState->pendingInputPrompt = std::move(prompt);
    return 0;
}

int luaPressAnyKey(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    ensureMapEventDialogueContext(pLuaState, *pRuntimeState);

    EventRuntimeState::PendingInputPrompt prompt = {};
    prompt.kind = EventRuntimeState::PendingInputPrompt::Kind::PressAnyKey;
    prompt.eventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    prompt.continueStep = static_cast<uint8_t>(luaL_checkinteger(pLuaState, 2));
    appendPendingMessageText(pLuaState, *pRuntimeState);
    pRuntimeState->pendingInputPrompt = std::move(prompt);
    return 0;
}

int luaSpecialJump(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || pExecutionContext->pSceneEventContext == nullptr)
    {
        return 0;
    }

    pExecutionContext->pSceneEventContext->specialJump(
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)),
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2)));
    return 0;
}

int luaJump(lua_State *pLuaState)
{
    return luaSpecialJump(pLuaState);
}

int luaIsTotalBountyInRange(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);
    const int32_t totalBounty = pParty != nullptr
        ? pParty->eventVariableValue(static_cast<uint16_t>(EvtVariable::NumBounties))
        : 0;
    const int32_t minValue = static_cast<int32_t>(luaL_checkinteger(pLuaState, 1));
    const int32_t maxValue = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
    lua_pushboolean(pLuaState, totalBounty >= minValue && totalBounty <= maxValue);
    return 1;
}

int luaIsNpcInParty(lua_State *pLuaState)
{
    lua_pushboolean(
        pLuaState,
        activePartyHasRosterMember(readableParty(pLuaState), static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))));
    return 1;
}

int luaCheckMonstersKilled(lua_State *pLuaState)
{
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || readonlySceneEventContext(pExecutionContext) == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    lua_pushboolean(
        pLuaState,
        readonlySceneEventContext(pExecutionContext)->checkMonstersKilled(
            static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)),
            static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2)),
            static_cast<uint32_t>(luaL_checkinteger(pLuaState, 3)),
            luaEventBoolean(pLuaState, 4)));
    return 1;
}

int luaIsHouseOpen(lua_State *pLuaState)
{
    const EventRuntime *pEventRuntime = readableEventRuntime(pLuaState);
    const HouseTable *pHouseTable = pEventRuntime != nullptr ? pEventRuntime->houseTable() : nullptr;
    const HouseEntry *pHouse = pHouseTable != nullptr
        ? pHouseTable->get(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)))
        : nullptr;

    if (pHouse == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const ISceneEventContext *pSceneEventContext = readonlySceneEventContext(pExecutionContext);
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    const float currentGameMinutes = pSceneEventContext != nullptr
        ? pSceneEventContext->currentGameMinutes()
        : (pRuntimeState != nullptr ? static_cast<float>(currentGameMinutesFromRuntimeState(*pRuntimeState)) : 0.0f);
    lua_pushboolean(pLuaState, isHouseOpenAtGameMinute(*pHouse, currentGameMinutes));
    return 1;
}

int luaNpcText(lua_State *pLuaState)
{
    const uint32_t textId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const char *pFallback = lua_gettop(pLuaState) >= 2 && !lua_isnil(pLuaState, 2)
        ? luaL_checkstring(pLuaState, 2)
        : "";

    const EventRuntime *pEventRuntime = readableEventRuntime(pLuaState);
    const NpcDialogTable *pNpcDialogTable = pEventRuntime != nullptr ? pEventRuntime->npcDialogTable() : nullptr;

    if (pNpcDialogTable != nullptr)
    {
        const std::optional<std::string> text = pNpcDialogTable->getText(textId);

        if (text.has_value())
        {
            lua_pushlstring(pLuaState, text->data(), text->size());
            return 1;
        }
    }

    lua_pushstring(pLuaState, pFallback);
    return 1;
}

int luaSetMonsterRelation(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    const uint32_t leftMonsterId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t rightMonsterId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const int32_t relation = static_cast<int32_t>(luaL_checkinteger(pLuaState, 3));
    pRuntimeState->monsterRelationOverrides[
        EventRuntime::monsterRelationOverrideKey(leftMonsterId, rightMonsterId)] = relation;
    return 0;
}

int luaAdd(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    EventRuntime::addVariableValue(
        *pRuntimeState,
        EventRuntime::decodeVariable(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 2)),
        writableParty(pLuaState),
        selectedTargetMemberIndices(pLuaState),
        readonlySceneEventContext(pExecutionContext));
    return 0;
}

int luaSubtract(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    EventRuntime::subtractVariableValue(
        *pRuntimeState,
        EventRuntime::decodeVariable(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 2)),
        writableParty(pLuaState),
        selectedTargetMemberIndices(pLuaState));
    return 0;
}

int luaSet(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    EventRuntime::setVariableValue(
        *pRuntimeState,
        EventRuntime::decodeVariable(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 2)),
        writableParty(pLuaState),
        selectedTargetMemberIndices(pLuaState),
        readonlySceneEventContext(pExecutionContext));
    return 0;
}

int luaSummonMonsters(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || pExecutionContext->pSceneEventContext == nullptr)
    {
        return 0;
    }

    pExecutionContext->pSceneEventContext->summonMonsters(
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)),
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2)),
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 3)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 4)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 5)),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 6)),
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 7)),
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 8)));
    return 0;
}

int luaChangeEvent(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState->activeDecorationContext)
    {
        EventRuntimeState::ActiveDecorationContext &context = *pRuntimeState->activeDecorationContext;
        const uint16_t targetEventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
        uint8_t newState = 0;

        if (targetEventId == 0)
        {
            newState = context.hideWhenCleared ? context.eventCount : 0;
        }
        else if (targetEventId >= context.baseEventId)
        {
            const uint16_t delta = targetEventId - context.baseEventId;
            newState = delta > std::numeric_limits<uint8_t>::max()
                ? std::numeric_limits<uint8_t>::max()
                : static_cast<uint8_t>(delta);
        }

        pRuntimeState->decorVars[context.decorVarIndex] = newState;
        context.currentEventId = targetEventId;
    }

    return 0;
}

int luaStatusText(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const char *pText = luaL_checkstring(pLuaState, 1);
    pRuntimeState->statusMessages.push_back(pText);
    return 0;
}

int luaOpenChest(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t chestId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    pRuntimeState->openedChestIds.push_back(chestId);
    pRuntimeState->openedChestRequests.push_back(
        EventRuntimeState::OpenedChestRequest{
            .chestId = chestId,
            .openedByTelekinesis = pRuntimeState->activeEventOpenedByTelekinesis,
        });
    return 0;
}

int luaGiveItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    Party *pParty = writableParty(pLuaState);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    const int argumentCount = lua_gettop(pLuaState);

    if (argumentCount <= 0)
    {
        return 0;
    }

    if (argumentCount == 1)
    {
        const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
        const std::optional<InventoryItem> item = createGrantedEventItem(*pRuntimeState, pParty, 0, 1, 0, itemId);

        if (item)
        {
            pRuntimeState->grantedItems.push_back(*item);
        }

        return 0;
    }

    const uint32_t treasureLevel = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t treasureType = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const uint32_t itemId =
        argumentCount >= 3 ? static_cast<uint32_t>(luaL_checkinteger(pLuaState, 3)) : 0;
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const uint16_t eventId = pExecutionContext != nullptr ? pExecutionContext->currentEventId : 0;
    const std::optional<InventoryItem> item =
        createGrantedEventItem(*pRuntimeState, pParty, eventId, treasureLevel, treasureType, itemId);

    if (item)
    {
        pRuntimeState->grantedItems.push_back(*item);
    }

    return 0;
}

int luaRemoveItems(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->removedItemIds.push_back(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)));
    return 0;
}

int luaSetDoorState(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    const uint32_t mechanismId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t actionValue = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const MapDeltaData *pMapDeltaData =
        pExecutionContext != nullptr && pExecutionContext->pSceneEventContext != nullptr
            ? pExecutionContext->pSceneEventContext->mapDeltaData()
            : nullptr;
    const MapDeltaDoor *pDoor = findMechanismDoorById(pMapDeltaData, mechanismId);

    auto [iterator, inserted] = pRuntimeState->mechanisms.try_emplace(mechanismId);
    RuntimeMechanismState &runtimeMechanism = iterator->second;

    if (inserted && pDoor != nullptr)
    {
        initializeRuntimeMechanismStateFromDoor(*pDoor, runtimeMechanism);
    }

    MechanismAction action = MechanismAction::Open;

    if (actionValue == static_cast<uint32_t>(EvtMechanismAction::Close))
    {
        action = MechanismAction::Close;
    }
    else if (actionValue == static_cast<uint32_t>(EvtMechanismAction::Trigger))
    {
        action = MechanismAction::Trigger;
    }

    const uint16_t previousState = runtimeMechanism.state;
    const bool wasMoving = runtimeMechanism.isMoving;
    EventRuntime::applyMechanismAction(runtimeMechanism, pDoor, action);
    GAMEPLAY_DEBUG_TRACE(
        "mechanism_triggered kind=indoor_door id=" + std::to_string(mechanismId)
        + " action=" + gameplayDebugTraceMechanismActionName(actionValue)
        + " raw_action=" + std::to_string(actionValue)
        + " previous_state=" + gameplayDebugTraceMechanismStateName(previousState)
        + " new_state=" + gameplayDebugTraceMechanismStateName(runtimeMechanism.state)
        + " was_moving=" + (wasMoving ? "true" : "false")
        + " moving=" + (runtimeMechanism.isMoving ? "true" : "false")
        + " door_slot=" + std::to_string(pDoor != nullptr ? pDoor->slotIndex : 0)
        + " move_length=" + std::to_string(pDoor != nullptr ? pDoor->moveLength : 0)
        + " open_speed=" + std::to_string(pDoor != nullptr ? pDoor->openSpeed : 0)
        + " close_speed=" + std::to_string(pDoor != nullptr ? pDoor->closeSpeed : 0));
    pRuntimeState->lastAffectedMechanismIds.push_back(mechanismId);
    return 0;
}

int luaRegisterOutdoorModelMechanism(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext == nullptr || pExecutionContext->pSceneEventContext == nullptr)
    {
        return 0;
    }

    const uint32_t mechanismId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const std::string modelName = sanitizeEventString(luaL_checkstring(pLuaState, 2));
    const int32_t dx = static_cast<int32_t>(luaL_checkinteger(pLuaState, 3));
    const int32_t dy = static_cast<int32_t>(luaL_checkinteger(pLuaState, 4));
    const int32_t dz = static_cast<int32_t>(luaL_checkinteger(pLuaState, 5));
    const uint32_t moveTimeMs = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 6));
    const bool closed = lua_gettop(pLuaState) < 7 || luaEventBoolean(pLuaState, 7);
    const bool moveParty = lua_gettop(pLuaState) >= 8 && luaEventBoolean(pLuaState, 8);

    pExecutionContext->pSceneEventContext->registerOutdoorModelMechanism(
        mechanismId,
        modelName,
        dx,
        dy,
        dz,
        moveTimeMs,
        closed,
        moveParty);
    return 0;
}

int luaSetOutdoorModelMechanismState(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    const uint32_t mechanismId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t actionValue = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));

    if (pRuntimeState->outdoorModelMechanisms.find(mechanismId) == pRuntimeState->outdoorModelMechanisms.end())
    {
        return 0;
    }

    RuntimeMechanismState &runtimeMechanism = pRuntimeState->mechanisms[mechanismId];
    const EventRuntimeState::OutdoorModelMechanismDefinition &definition =
        pRuntimeState->outdoorModelMechanisms.at(mechanismId);
    MechanismAction action = MechanismAction::Open;

    if (actionValue == static_cast<uint32_t>(EvtMechanismAction::Close))
    {
        action = MechanismAction::Close;
    }
    else if (actionValue == static_cast<uint32_t>(EvtMechanismAction::Trigger))
    {
        action = MechanismAction::Trigger;
    }

    const uint16_t previousState = runtimeMechanism.state;
    const bool wasMoving = runtimeMechanism.isMoving;
    EventRuntime::applyMechanismAction(runtimeMechanism, nullptr, action);
    GAMEPLAY_DEBUG_TRACE(
        "mechanism_triggered kind=outdoor_model id=" + std::to_string(mechanismId)
        + " action=" + gameplayDebugTraceMechanismActionName(actionValue)
        + " raw_action=" + std::to_string(actionValue)
        + " previous_state=" + gameplayDebugTraceMechanismStateName(previousState)
        + " new_state=" + gameplayDebugTraceMechanismStateName(runtimeMechanism.state)
        + " was_moving=" + (wasMoving ? "true" : "false")
        + " moving=" + (runtimeMechanism.isMoving ? "true" : "false")
        + " model=\"" + definition.modelName + "\""
        + " bmodel_index=" + std::to_string(definition.bmodelIndex)
        + " move_time_ms=" + std::to_string(definition.moveTimeMs)
        + " delta=(" + std::to_string(definition.dx) + "," + std::to_string(definition.dy)
        + "," + std::to_string(definition.dz) + ")"
        + " move_party=" + (definition.moveParty ? "true" : "false"));
    pRuntimeState->lastAffectedMechanismIds.push_back(mechanismId);
    markOutdoorSurfaceStateChanged(*pRuntimeState);
    return 0;
}

int luaStopDoor(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t mechanismId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    RuntimeMechanismState &runtimeMechanism = pRuntimeState->mechanisms[mechanismId];
    const bool wasMoving = runtimeMechanism.isMoving;
    runtimeMechanism.isMoving = false;
    GAMEPLAY_DEBUG_TRACE(
        "mechanism_stopped id=" + std::to_string(mechanismId)
        + " state=" + gameplayDebugTraceMechanismStateName(runtimeMechanism.state)
        + " was_moving=" + (wasMoving ? "true" : "false"));
    pRuntimeState->lastAffectedMechanismIds.push_back(mechanismId);
    return 0;
}

int luaSetTexture(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t cogNumber = eventReferenceId(luaL_checkinteger(pLuaState, 1));

    if (lua_gettop(pLuaState) >= 2 && lua_type(pLuaState, 2) == LUA_TSTRING)
    {
        pRuntimeState->textureOverrides[cogNumber] = sanitizeEventString(lua_tostring(pLuaState, 2));
    }
    else
    {
        pRuntimeState->textureOverrides.erase(cogNumber);
    }

    markOutdoorSurfaceStateChanged(*pRuntimeState);
    return 0;
}

int luaSetOutdoorModelFacetTexture(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (pRuntimeState == nullptr)
    {
        return 0;
    }

    const uint32_t modelIndex = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t faceIndex = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const uint32_t key = EventRuntime::outdoorModelFacetTextureOverrideKey(modelIndex, faceIndex);

    if (lua_gettop(pLuaState) >= 3 && lua_type(pLuaState, 3) == LUA_TSTRING)
    {
        pRuntimeState->outdoorModelFacetTextureOverrides[key] = sanitizeEventString(lua_tostring(pLuaState, 3));
    }
    else
    {
        pRuntimeState->outdoorModelFacetTextureOverrides.erase(key);
    }

    markOutdoorSurfaceStateChanged(*pRuntimeState);
    return 0;
}

int luaSetLight(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const lua_Integer rawReferenceId = luaL_checkinteger(pLuaState, 1);
    const bool enabled = luaEventBoolean(pLuaState, 2);
    const LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext != nullptr && pExecutionContext->pSceneEventContext != nullptr)
    {
        const std::vector<uint32_t> resolvedLightIds =
            pExecutionContext->pSceneEventContext->resolveIndoorLightReferenceIds(
                static_cast<int32_t>(rawReferenceId));

        if (!resolvedLightIds.empty())
        {
            for (uint32_t lightId : resolvedLightIds)
            {
                pRuntimeState->indoorLightsEnabled[lightId] = enabled;
            }
            return 0;
        }
    }

    pRuntimeState->indoorLightsEnabled[eventReferenceId(rawReferenceId)] = enabled;
    return 0;
}

int luaSetFacetBit(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t cogNumber = eventReferenceId(luaL_checkinteger(pLuaState, 1));
    const uint32_t bit = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isOn = luaEventBoolean(pLuaState, 3);

    if (pExecutionContext != nullptr
        && pExecutionContext->pSceneEventContext != nullptr
        && pExecutionContext->pSceneEventContext->setFacetBit(cogNumber, bit, isOn))
    {
        markOutdoorSurfaceStateChanged(*pRuntimeState);
        return 0;
    }

    if (isOn)
    {
        pRuntimeState->facetSetMasks[cogNumber] |= bit;
        pRuntimeState->facetClearMasks[cogNumber] &= ~bit;
    }
    else
    {
        pRuntimeState->facetClearMasks[cogNumber] |= bit;
        pRuntimeState->facetSetMasks[cogNumber] &= ~bit;
    }

    markOutdoorSurfaceStateChanged(*pRuntimeState);
    return 0;
}

int luaSetMonsterBit(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t actorId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t bit = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isOn = luaEventBoolean(pLuaState, 3);

    if (isOn)
    {
        pRuntimeState->actorSetMasks[actorId] |= bit;
        pRuntimeState->actorClearMasks[actorId] &= ~bit;
        if (pRuntimeState->actorClearMasks[actorId] == 0)
        {
            pRuntimeState->actorClearMasks.erase(actorId);
        }
    }
    else
    {
        pRuntimeState->actorClearMasks[actorId] |= bit;
        pRuntimeState->actorSetMasks[actorId] &= ~bit;
        if (pRuntimeState->actorSetMasks[actorId] == 0)
        {
            pRuntimeState->actorSetMasks.erase(actorId);
        }
    }

    if (bit == static_cast<uint32_t>(EvtActorAttribute::Hostile))
    {
        pRuntimeState->actorHostilityRequests[actorId] = isOn;
    }

    return 0;
}

int luaSetMonGroupBit(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t groupId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t bit = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isOn = luaEventBoolean(pLuaState, 3);

    if (isOn)
    {
        pRuntimeState->actorGroupSetMasks[groupId] |= bit;
        pRuntimeState->actorGroupClearMasks[groupId] &= ~bit;
        if (pRuntimeState->actorGroupClearMasks[groupId] == 0)
        {
            pRuntimeState->actorGroupClearMasks.erase(groupId);
        }
    }
    else
    {
        pRuntimeState->actorGroupClearMasks[groupId] |= bit;
        pRuntimeState->actorGroupSetMasks[groupId] &= ~bit;
        if (pRuntimeState->actorGroupSetMasks[groupId] == 0)
        {
            pRuntimeState->actorGroupSetMasks.erase(groupId);
        }
    }

    if (bit == static_cast<uint32_t>(EvtActorAttribute::Hostile))
    {
        pRuntimeState->actorGroupHostilityRequests[groupId] = isOn;
    }

    return 0;
}

int luaSetNpcTopic(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t topicSlotIndex = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const uint32_t topicId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 3));
    pRuntimeState->npcTopicOverrides[npcId][topicSlotIndex] = topicId;

    if (pExecutionContext->pParty != nullptr)
    {
        pExecutionContext->pParty->setNpcTopicOverride(npcId, topicSlotIndex, topicId);
    }

    return 0;
}

int luaSetNpcGroupNews(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);
    const uint32_t groupId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t newsId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    pRuntimeState->npcGroupNews[groupId] = newsId;

    if (pExecutionContext->pParty != nullptr)
    {
        pExecutionContext->pParty->setNpcGroupNews(groupId, newsId);
    }

    return 0;
}

int luaSetMessage(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext != nullptr)
    {
        pExecutionContext->pendingMessageText = luaL_checkstring(pLuaState, 1);

        EventRuntimeState *pRuntimeState = pExecutionContext->pRuntimeState;
        const bool isNpcTopicExecution = !pExecutionContext->allowStandaloneMapEventDialogueContext;
        const bool shouldDisplayGlobalMessage =
            pRuntimeState != nullptr
            &&
            pExecutionContext->executingGlobalHandler
            && (!pRuntimeState->pendingDialogueContext
                || pRuntimeState->pendingDialogueContext->kind != DialogueContextKind::MapEvent);
        const bool hasNonMapDialogueContext =
            pRuntimeState != nullptr
            && pRuntimeState->pendingDialogueContext
            && pRuntimeState->pendingDialogueContext->kind != DialogueContextKind::None
            && pRuntimeState->pendingDialogueContext->kind != DialogueContextKind::MapEvent
            && pRuntimeState->pendingDialogueContext->kind != DialogueContextKind::MapTransition;

        if (pRuntimeState != nullptr && (isNpcTopicExecution || shouldDisplayGlobalMessage || hasNonMapDialogueContext))
        {
            pRuntimeState->messages.push_back(*pExecutionContext->pendingMessageText);
            pExecutionContext->pendingMessageText.reset();
        }
    }

    return 0;
}

int luaSimpleMessage(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    ensureMapEventDialogueContext(pLuaState, *pRuntimeState);

    if (lua_gettop(pLuaState) >= 1 && lua_type(pLuaState, 1) == LUA_TSTRING)
    {
        pRuntimeState->messages.push_back(lua_tostring(pLuaState, 1));
        return 0;
    }

    appendPendingMessageText(pLuaState, *pRuntimeState);

    return 0;
}

int luaCanPlayerAct(lua_State *pLuaState)
{
    const Party *pParty = readableParty(pLuaState);

    if (pParty == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const int rosterId = static_cast<int>(luaL_checkinteger(pLuaState, 1));

    for (const Character &member : pParty->members())
    {
        if (member.rosterId == rosterId)
        {
            lua_pushboolean(pLuaState, GameMechanics::canAct(member));
            return 1;
        }
    }

    lua_pushboolean(pLuaState, 0);
    return 1;
}

int luaRefundChestArtifacts(lua_State *pLuaState)
{
    (void)pLuaState;
    return 0;
}

int luaQuestion(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    EventRuntimeState::PendingInputPrompt prompt = {};
    prompt.kind = EventRuntimeState::PendingInputPrompt::Kind::InputString;
    prompt.eventId = executionContextFromLua(pLuaState) != nullptr
        ? executionContextFromLua(pLuaState)->currentEventId
        : 0;
    prompt.continueStep = 0;
    prompt.text = luaL_checkstring(pLuaState, 1);
    pRuntimeState->pendingInputPrompt = std::move(prompt);
    return 0;
}

void registerLuaFunction(lua_State *pLuaState, const char *pName, lua_CFunction function)
{
    lua_pushcfunction(pLuaState, function);
    lua_setfield(pLuaState, -2, pName);
}

void registerEventBindings(LuaSessionCache &session)
{
    lua_State *pLuaState = session.lua.state();
    lua_newtable(pLuaState);

    registerLuaFunction(pLuaState, "_BeginEvent", luaBeginEvent);
    registerLuaFunction(pLuaState, "_BeginCanShowTopic", luaBeginCanShowTopic);
    registerLuaFunction(pLuaState, "Debug", luaDebugPrint);
    registerLuaFunction(pLuaState, "_RandomJump", luaRandomJump);
    registerLuaFunction(pLuaState, "AskQuestion", luaAskQuestion);
    registerLuaFunction(pLuaState, "AskQuestionWithAnswerSteps", luaAskQuestionWithAnswerSteps);
    registerLuaFunction(pLuaState, "_PressAnyKey", luaPressAnyKey);
    registerLuaFunction(pLuaState, "_SpecialJump", luaSpecialJump);
    registerLuaFunction(pLuaState, "_IsNpcInParty", luaIsNpcInParty);

    registerLuaFunction(pLuaState, "ForPlayer", luaForPlayer);
    registerLuaFunction(pLuaState, "Cmp", luaCompare);
    registerLuaFunction(pLuaState, "HasEverOwnedItem", luaHasEverOwnedItem);
    registerLuaFunction(pLuaState, "HasItemAnywhere", luaHasItemAnywhere);
    registerLuaFunction(pLuaState, "GetPartyPosition", luaGetPartyPosition);
    registerLuaFunction(pLuaState, "GetEnemyDetectorState", luaGetEnemyDetectorState);
    registerLuaFunction(pLuaState, "GetCurrentScreen", luaGetCurrentScreen);
    registerLuaFunction(pLuaState, "GetCurrentMapName", luaGetCurrentMapName);
    registerLuaFunction(pLuaState, "GetCurrentContinent", luaGetCurrentContinent);
    registerLuaFunction(pLuaState, "SaveCurrentLocation", luaSaveCurrentLocation);
    registerLuaFunction(pLuaState, "HasSavedLocation", luaHasSavedLocation);
    registerLuaFunction(pLuaState, "MoveToSavedLocation", luaMoveToSavedLocation);
    registerLuaFunction(pLuaState, "ClearSavedLocation", luaClearSavedLocation);
    registerLuaFunction(pLuaState, "SetTransportRouteOverride", luaSetTransportRouteOverride);
    registerLuaFunction(pLuaState, "ClearTransportRouteOverride", luaClearTransportRouteOverride);
    registerLuaFunction(pLuaState, "GetMapVar", luaGetMapVar);
    registerLuaFunction(pLuaState, "SetMapVar", luaSetMapVar);
    registerLuaFunction(pLuaState, "GetGlobalVar", luaGetGlobalVar);
    registerLuaFunction(pLuaState, "SetGlobalVar", luaSetGlobalVar);
    registerLuaFunction(pLuaState, "GetHeldItemId", luaGetHeldItemId);
    registerLuaFunction(pLuaState, "SetHeldItem", luaSetHeldItem);
    registerLuaFunction(pLuaState, "ClearHeldItem", luaClearHeldItem);
    registerLuaFunction(pLuaState, "GetPartyMemberCount", luaGetPartyMemberCount);
    registerLuaFunction(pLuaState, "GetCurrentPlayerIndex", luaGetCurrentPlayerIndex);
    registerLuaFunction(pLuaState, "GetPartyMemberPortraitId", luaGetPartyMemberPortraitId);
    registerLuaFunction(pLuaState, "SetPartyMemberPortraitId", luaSetPartyMemberPortraitId);
    registerLuaFunction(pLuaState, "PartyMemberHasItem", luaPartyMemberHasItem);
    registerLuaFunction(pLuaState, "PartyMemberItemCount", luaPartyMemberItemCount);
    registerLuaFunction(pLuaState, "GivePartyMemberItem", luaGivePartyMemberItem);
    registerLuaFunction(pLuaState, "ReplacePartyInventoryItems", luaReplacePartyInventoryItems);
    registerLuaFunction(pLuaState, "PartyMemberKnowsSpell", luaPartyMemberKnowsSpell);
    registerLuaFunction(pLuaState, "RemovePartyMemberItem", luaRemovePartyMemberItem);
    registerLuaFunction(pLuaState, "ApplyLichTransformation", luaApplyLichTransformation);
    registerLuaFunction(pLuaState, "PartyMemberHasEquippedItem", luaPartyMemberHasEquippedItem);
    registerLuaFunction(pLuaState, "GetHookContext", luaGetHookContext);
    registerLuaFunction(pLuaState, "SetHookBlocked", luaSetHookBlocked);
    registerLuaFunction(pLuaState, "SetHookDamage", luaSetHookDamage);
    registerLuaFunction(pLuaState, "SetHookRestFoodCost", luaSetHookRestFoodCost);
    registerLuaFunction(pLuaState, "SetHookHouseTopics", luaSetHookHouseTopics);
    registerLuaFunction(pLuaState, "EnterHouse", luaEnterHouse);
    registerLuaFunction(pLuaState, "PlaySound", luaPlaySound);
    registerLuaFunction(pLuaState, "MoveToMap", luaMoveToMap);
    registerLuaFunction(pLuaState, "OpenChest", luaOpenChest);
    registerLuaFunction(pLuaState, "FaceExpression", luaFaceExpression);
    registerLuaFunction(pLuaState, "DamagePlayer", luaDamagePlayer);
    registerLuaFunction(pLuaState, "SetSnow", luaSetSnow);
    registerLuaFunction(pLuaState, "SetRain", luaSetRain);
    registerLuaFunction(pLuaState, "SetOutdoorSky", luaSetOutdoorSky);
    registerLuaFunction(pLuaState, "SetOutdoorFog", luaSetOutdoorFog);
    registerLuaFunction(pLuaState, "OpenDimensionDoor", luaOpenDimensionDoor);
    registerLuaFunction(pLuaState, "ClearDimensionDoorOverlay", luaClearDimensionDoorOverlay);
    registerLuaFunction(pLuaState, "SetTexture", luaSetTexture);
    registerLuaFunction(pLuaState, "SetTextureOutdoors", luaSetTexture);
    registerLuaFunction(pLuaState, "SetOutdoorModelFacetTexture", luaSetOutdoorModelFacetTexture);
    registerLuaFunction(pLuaState, "ShowMovie", luaShowMovie);
    registerLuaFunction(pLuaState, "ReturnToMainMenu", luaReturnToMainMenu);
    registerLuaFunction(pLuaState, "SetSprite", luaSetSprite);
    registerLuaFunction(pLuaState, "SetDoorState", luaSetDoorState);
    registerLuaFunction(pLuaState, "RegisterOutdoorModelMechanism", luaRegisterOutdoorModelMechanism);
    registerLuaFunction(pLuaState, "SetOutdoorModelMechanismState", luaSetOutdoorModelMechanismState);
    registerLuaFunction(pLuaState, "Add", luaAdd);
    registerLuaFunction(pLuaState, "Subtract", luaSubtract);
    registerLuaFunction(pLuaState, "Set", luaSet);
    registerLuaFunction(pLuaState, "SummonMonsters", luaSummonMonsters);
    registerLuaFunction(pLuaState, "CastSpell", luaCastSpell);
    registerLuaFunction(pLuaState, "SpeakNPC", luaSpeakNpc);
    registerLuaFunction(pLuaState, "SetFacetBit", luaSetFacetBit);
    registerLuaFunction(pLuaState, "SetFacetBitOutdoors", luaSetFacetBit);
    registerLuaFunction(pLuaState, "SetMonsterBit", luaSetMonsterBit);
    registerLuaFunction(pLuaState, "Question", luaQuestion);
    registerLuaFunction(pLuaState, "StatusText", luaStatusText);
    registerLuaFunction(pLuaState, "SetMessage", luaSetMessage);
    registerLuaFunction(pLuaState, "SetLight", luaSetLight);
    registerLuaFunction(pLuaState, "SimpleMessage", luaSimpleMessage);
    registerLuaFunction(pLuaState, "SummonItem", luaSummonItem);
    registerLuaFunction(pLuaState, "SummonObject", luaSummonItem);
    registerLuaFunction(pLuaState, "SetNPCTopic", luaSetNpcTopic);
    registerLuaFunction(pLuaState, "MoveNPC", luaMoveNpc);
    registerLuaFunction(pLuaState, "GiveItem", luaGiveItem);
    registerLuaFunction(pLuaState, "ChangeEvent", luaChangeEvent);
    registerLuaFunction(pLuaState, "CheckSkill", luaCheckSkill);
    registerLuaFunction(pLuaState, "SetNPCGroupNews", luaSetNpcGroupNews);
    registerLuaFunction(pLuaState, "SetMonsterGroup", luaSetMonsterGroup);
    registerLuaFunction(pLuaState, "SetNPCItem", luaSetNpcItem);
    registerLuaFunction(pLuaState, "SetNPCGreeting", luaSetNpcGreeting);
    registerLuaFunction(pLuaState, "SetNPCName", luaSetNpcName);
    registerLuaFunction(pLuaState, "SetNPCPicture", luaSetNpcPicture);
    registerLuaFunction(pLuaState, "SetNPCProfession", luaSetNpcProfession);
    registerLuaFunction(pLuaState, "CheckMonstersKilled", luaCheckMonstersKilled);
    registerLuaFunction(pLuaState, "IsHouseOpen", luaIsHouseOpen);
    registerLuaFunction(pLuaState, "NPCText", luaNpcText);
    registerLuaFunction(pLuaState, "ChangeGroupToGroup", luaChangeGroupToGroup);
    registerLuaFunction(pLuaState, "ChangeGroupAlly", luaChangeGroupAlly);
    registerLuaFunction(pLuaState, "CheckSeason", luaCheckSeason);
    registerLuaFunction(pLuaState, "SetMonGroupBit", luaSetMonGroupBit);
    registerLuaFunction(pLuaState, "SetChestBit", luaSetChestBit);
    registerLuaFunction(pLuaState, "EnsureChestItem", luaEnsureChestItem);
    registerLuaFunction(pLuaState, "RemoveFollowerProfession", luaRemoveFollowerProfession);
    registerLuaFunction(pLuaState, "HasFollowerNpc", luaHasFollowerNpc);
    registerLuaFunction(pLuaState, "AddFollowerNpc", luaAddFollowerNpc);
    registerLuaFunction(pLuaState, "RemoveFollowerNpc", luaRemoveFollowerNpc);
    registerLuaFunction(pLuaState, "CurrentGameMinutes", luaCurrentGameMinutes);
    registerLuaFunction(pLuaState, "AdvanceGameMinutes", luaAdvanceGameMinutes);
    registerLuaFunction(pLuaState, "GetRuntimeVariable", luaGetRuntimeVariable);
    registerLuaFunction(pLuaState, "SetRuntimeVariable", luaSetRuntimeVariable);
    registerLuaFunction(pLuaState, "GetActiveEventSpellId", luaGetActiveEventSpellId);
    registerLuaFunction(pLuaState, "GetPartyVariable", luaGetPartyVariable);
    registerLuaFunction(pLuaState, "SetPartyVariable", luaSetPartyVariable);
    registerLuaFunction(pLuaState, "GetClassId", luaGetClassId);
    registerLuaFunction(pLuaState, "GetClassName", luaGetClassName);
    registerLuaFunction(pLuaState, "GetPlayerClass", luaGetPlayerClass);
    registerLuaFunction(pLuaState, "GetPlayerClassName", luaGetPlayerClassName);
    registerLuaFunction(pLuaState, "SetPlayerClass", luaSetPlayerClass);
    registerLuaFunction(pLuaState, "GetClassSkillCap", luaGetClassSkillCap);
    registerLuaFunction(pLuaState, "CanClassLearnSkill", luaCanClassLearnSkill);
    registerLuaFunction(pLuaState, "CanPlayerLearnSkill", luaCanPlayerLearnSkill);
    registerLuaFunction(pLuaState, "SetMonsterRelation", luaSetMonsterRelation);
    registerLuaFunction(pLuaState, "SetLocalMonsterRelation", luaSetMonsterRelation);
    registerLuaFunction(pLuaState, "FaceAnimation", luaFaceAnimation);
    registerLuaFunction(pLuaState, "SetMonsterItem", luaSetMonsterItem);
    registerLuaFunction(pLuaState, "StopDoor", luaStopDoor);
    registerLuaFunction(pLuaState, "CheckItemsCount", luaCheckItemsCount);
    registerLuaFunction(pLuaState, "RemoveItems", luaRemoveItems);
    registerLuaFunction(pLuaState, "Jump", luaJump);
    registerLuaFunction(pLuaState, "IsTotalBountyInRange", luaIsTotalBountyInRange);
    registerLuaFunction(pLuaState, "CanPlayerAct", luaCanPlayerAct);
    registerLuaFunction(pLuaState, "RefundChestArtifacts", luaRefundChestArtifacts);

    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeGlobal);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeMap);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeCanShowTopic);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "hint");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "house");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "str");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "VarNum");
    lua_newtable(pLuaState);
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::Member0));
    lua_setfield(pLuaState, -2, "Player0");
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::Member1));
    lua_setfield(pLuaState, -2, "Player1");
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::Member2));
    lua_setfield(pLuaState, -2, "Player2");
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::Member3));
    lua_setfield(pLuaState, -2, "Player3");
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::Member4));
    lua_setfield(pLuaState, -2, "Player4");
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::All));
    lua_setfield(pLuaState, -2, "All");
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::Current));
    lua_setfield(pLuaState, -2, "Current");
    lua_setfield(pLuaState, -2, "Players");
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::Current));
    lua_setfield(pLuaState, -2, "CurrentPlayer");
    lua_pushinteger(pLuaState, static_cast<int>(EvtPartySelector::Current));
    lua_setfield(pLuaState, -2, "Player");
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, "const");

    lua_newtable(pLuaState);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeGlobal);
    lua_newtable(pLuaState);
    lua_setfield(pLuaState, -2, LuaScopeMap);
    lua_setfield(pLuaState, -2, "meta");

    lua_setglobal(pLuaState, "evt");
}

void releaseScopeProgram(Engine::LuaStateOwner &lua, LuaScopeProgram &scopeProgram)
{
    for (auto &[eventId, reference] : scopeProgram.handlers)
    {
        (void)eventId;
        lua.releaseRegistryReference(reference);
    }

    for (auto &[topicId, reference] : scopeProgram.canShowTopicHandlers)
    {
        (void)topicId;
        lua.releaseRegistryReference(reference);
    }

    scopeProgram.handlers.clear();
    scopeProgram.canShowTopicHandlers.clear();
    scopeProgram.onLoadEventIds.clear();
    scopeProgram.onLeaveEventIds.clear();
    scopeProgram.npcEnterHookEventIds.clear();
    scopeProgram.npcExitHookEventIds.clear();
    scopeProgram.houseTopicFilterHookEventIds.clear();
    scopeProgram.houseTopicClickHookEventIds.clear();
    scopeProgram.restFoodCostHookEventIds.clear();
    scopeProgram.gameplayActionHookEventIds.clear();
    scopeProgram.mapRefillHookEventIds.clear();
    scopeProgram.mapTransitionHookEventIds.clear();
    scopeProgram.monsterKilledHookEventIds.clear();
    scopeProgram.monsterDamageHookEventIds.clear();
    scopeProgram.chestOpenHookEventIds.clear();
    scopeProgram.inventoryOpenHookEventIds.clear();
}

void freezeHandlerTable(
    Engine::LuaStateOwner &lua,
    const char *pTableName,
    std::unordered_map<uint16_t, int> &targetHandlers)
{
    lua_State *pLuaState = lua.state();
    lua_getglobal(pLuaState, "evt");
    lua_getfield(pLuaState, -1, pTableName);

    lua_pushnil(pLuaState);

    while (lua_next(pLuaState, -2) != 0)
    {
        if (lua_isinteger(pLuaState, -2) && lua_isfunction(pLuaState, -1))
        {
            const uint16_t eventId = static_cast<uint16_t>(lua_tointeger(pLuaState, -2));
            targetHandlers[eventId] = lua.createRegistryReference();
        }
        else
        {
            lua_pop(pLuaState, 1);
        }
    }

    lua_pop(pLuaState, 2);
}

std::vector<uint16_t> readMetaEventIdArray(
    Engine::LuaStateOwner &lua,
    std::string_view scopeName,
    const char *pFieldName)
{
    std::vector<uint16_t> eventIds;
    lua_State *pLuaState = lua.state();

    lua_getglobal(pLuaState, "evt");
    lua_getfield(pLuaState, -1, "meta");
    lua_getfield(pLuaState, -1, scopeName == LuaScopeGlobal ? LuaScopeGlobal : LuaScopeMap);
    lua_getfield(pLuaState, -1, pFieldName);

    if (lua_istable(pLuaState, -1))
    {
        const lua_Integer count = luaL_len(pLuaState, -1);

        for (lua_Integer index = 1; index <= count; ++index)
        {
            lua_geti(pLuaState, -1, index);

            if (lua_isinteger(pLuaState, -1))
            {
                const lua_Integer rawEventId = lua_tointeger(pLuaState, -1);

                if (rawEventId > 0 && rawEventId <= std::numeric_limits<uint16_t>::max())
                {
                    eventIds.push_back(static_cast<uint16_t>(rawEventId));
                }
            }

            lua_pop(pLuaState, 1);
        }
    }

    lua_pop(pLuaState, 4);
    return eventIds;
}

LuaScopeProgram buildScopeProgram(
    LuaSessionCache &session,
    const ScriptedEventProgram &program,
    std::string_view scopeName,
    const std::string &chunkName)
{
    LuaScopeProgram scopeProgram = {};
    if (!program.luaSourceText().has_value())
    {
        session.lastError = "scripted event program is missing lua source text";
        return scopeProgram;
    }

    const std::string &chunkText = *program.luaSourceText();
    const std::string resolvedChunkName = program.luaSourceName().has_value() ? *program.luaSourceName() : chunkName;

    if (!session.lua.runChunk(chunkText, resolvedChunkName, session.lastError))
    {
        return scopeProgram;
    }

    freezeHandlerTable(session.lua, scopeName == LuaScopeGlobal ? LuaScopeGlobal : LuaScopeMap, scopeProgram.handlers);

    if (scopeName == LuaScopeGlobal)
    {
        freezeHandlerTable(session.lua, LuaScopeCanShowTopic, scopeProgram.canShowTopicHandlers);
    }

    scopeProgram.onLoadEventIds = program.onLoadEventIds();
    scopeProgram.onLeaveEventIds = program.onLeaveEventIds();
    scopeProgram.npcEnterHookEventIds = readMetaEventIdArray(session.lua, scopeName, "npcEnterHooks");
    scopeProgram.npcExitHookEventIds = readMetaEventIdArray(session.lua, scopeName, "npcExitHooks");
    scopeProgram.houseTopicFilterHookEventIds =
        readMetaEventIdArray(session.lua, scopeName, "houseTopicFilterHooks");
    scopeProgram.houseTopicClickHookEventIds =
        readMetaEventIdArray(session.lua, scopeName, "houseTopicClickHooks");
    scopeProgram.restFoodCostHookEventIds = readMetaEventIdArray(session.lua, scopeName, "restFoodCostHooks");
    scopeProgram.gameplayActionHookEventIds = readMetaEventIdArray(session.lua, scopeName, "gameplayActionHooks");
    scopeProgram.mapRefillHookEventIds = readMetaEventIdArray(session.lua, scopeName, "mapRefillHooks");
    scopeProgram.mapTransitionHookEventIds = readMetaEventIdArray(session.lua, scopeName, "mapTransitionHooks");
    scopeProgram.monsterKilledHookEventIds = readMetaEventIdArray(session.lua, scopeName, "monsterKilledHooks");
    scopeProgram.monsterDamageHookEventIds = readMetaEventIdArray(session.lua, scopeName, "monsterDamageHooks");
    scopeProgram.chestOpenHookEventIds = readMetaEventIdArray(session.lua, scopeName, "chestOpenHooks");
    scopeProgram.inventoryOpenHookEventIds = readMetaEventIdArray(session.lua, scopeName, "inventoryOpenHooks");

    return scopeProgram;
}

bool ensureLuaSession(
    const EventRuntime &eventRuntime,
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram)
{
    const ScriptedEventProgram *pLocalProgram = localProgram ? &*localProgram : nullptr;
    const ScriptedEventProgram *pGlobalProgram = globalProgram ? &*globalProgram : nullptr;
    const uint64_t localProgramCacheId = localProgram ? localProgram->cacheId() : 0;
    const uint64_t globalProgramCacheId = globalProgram ? globalProgram->cacheId() : 0;

    if (eventRuntime.m_luaSessionCache != nullptr
        && eventRuntime.m_pCachedLocalProgram == pLocalProgram
        && eventRuntime.m_pCachedGlobalProgram == pGlobalProgram
        && eventRuntime.m_cachedLocalProgramCacheId == localProgramCacheId
        && eventRuntime.m_cachedGlobalProgramCacheId == globalProgramCacheId)
    {
        return true;
    }

    eventRuntime.m_luaSessionCache.reset();
    eventRuntime.m_pCachedLocalProgram = nullptr;
    eventRuntime.m_pCachedGlobalProgram = nullptr;
    eventRuntime.m_cachedLocalProgramCacheId = 0;
    eventRuntime.m_cachedGlobalProgramCacheId = 0;

    auto session = std::make_unique<LuaSessionCache>();

    if (!session->lua.isValid())
    {
        return false;
    }

    session->lua.openApprovedLibraries();
    registerEventBindings(*session);

    lua_State *pLuaState = session->lua.state();
    lua_pushlightuserdata(pLuaState, &LuaSessionRegistryKey);
    lua_pushlightuserdata(pLuaState, session.get());
    lua_rawset(pLuaState, LUA_REGISTRYINDEX);

    if (globalProgram)
    {
        session->globalScope = buildScopeProgram(*session, *globalProgram, LuaScopeGlobal, "@Global.lua");

        if (session->lastError)
        {
            return false;
        }
    }

    if (localProgram)
    {
        session->localScope = buildScopeProgram(*session, *localProgram, LuaScopeMap, "@Local.lua");

        if (session->lastError)
        {
            return false;
        }
    }

    eventRuntime.m_pCachedLocalProgram = pLocalProgram;
    eventRuntime.m_pCachedGlobalProgram = pGlobalProgram;
    eventRuntime.m_cachedLocalProgramCacheId = localProgramCacheId;
    eventRuntime.m_cachedGlobalProgramCacheId = globalProgramCacheId;
    eventRuntime.m_luaSessionCache = std::move(session);
    return true;
}

bool invokeLuaHandler(
    const EventRuntime &eventRuntime,
    int handlerReference,
    LuaExecutionContext &executionContext,
    std::optional<uint8_t> continueStep = std::nullopt,
    std::optional<bool> *pBooleanResult = nullptr)
{
    if (eventRuntime.m_luaSessionCache == nullptr)
    {
        return false;
    }

    LuaSessionCache &session = *eventRuntime.m_luaSessionCache;
    session.pExecutionContext = &executionContext;
    lua_State *pLuaState = session.lua.state();
    session.lua.pushRegistryReference(handlerReference);

    if (continueStep)
    {
        lua_pushinteger(pLuaState, *continueStep);
    }

    std::optional<std::string> errorMessage;
    const bool ok = session.lua.call(continueStep ? 1 : 0, pBooleanResult != nullptr ? 1 : 0, errorMessage);
    session.pExecutionContext = nullptr;

    if (!ok)
    {
        session.lastError = errorMessage;
        return false;
    }

    if (pBooleanResult != nullptr)
    {
        *pBooleanResult = lua_toboolean(pLuaState, -1) != 0;
        lua_pop(pLuaState, 1);
    }

    return true;
}
}

bool EventRuntimeState::hasFacetInvisibleOverride(uint32_t faceId) const
{
    if (facetSetMasks.empty() && facetClearMasks.empty())
    {
        return false;
    }

    if (facetInvisibleOverrideCacheRevision != outdoorSurfaceRevision
        || facetInvisibleOverrideCacheSetSize != facetSetMasks.size()
        || facetInvisibleOverrideCacheClearSize != facetClearMasks.size())
    {
        const uint32_t maxSetId = maxFacetOverrideId(facetSetMasks);
        const uint32_t maxClearId = maxFacetOverrideId(facetClearMasks);
        const uint32_t maxId = std::max(maxSetId, maxClearId);

        facetInvisibleOverrideCache.assign(static_cast<size_t>(maxId) + 1u, 0u);

        for (const std::pair<const uint32_t, uint32_t> &entry : facetSetMasks)
        {
            if ((entry.second & faceAttributeBit(FaceAttribute::Invisible)) != 0)
            {
                facetInvisibleOverrideCache[entry.first] = 1u;
            }
        }

        for (const std::pair<const uint32_t, uint32_t> &entry : facetClearMasks)
        {
            if ((entry.second & faceAttributeBit(FaceAttribute::Invisible)) != 0
                && entry.first < facetInvisibleOverrideCache.size())
            {
                facetInvisibleOverrideCache[entry.first] = 0u;
            }
        }

        facetInvisibleOverrideCacheRevision = outdoorSurfaceRevision;
        facetInvisibleOverrideCacheSetSize = facetSetMasks.size();
        facetInvisibleOverrideCacheClearSize = facetClearMasks.size();
    }

    return faceId < facetInvisibleOverrideCache.size() && facetInvisibleOverrideCache[faceId] != 0u;
}

void clearTransientEventRuntimeState(EventRuntimeState &runtimeState)
{
    runtimeState.actorHostilityRequests.clear();
    runtimeState.actorGroupHostilityRequests.clear();
    runtimeState.dialogueState = {};
    runtimeState.activeDecorationContext.reset();
    runtimeState.activeHookContext.reset();
    runtimeState.messages.clear();
    runtimeState.statusMessages.clear();
    runtimeState.openedChestIds.clear();
    runtimeState.openedChestRequests.clear();
    runtimeState.activeEventOpenedByTelekinesis = false;
    runtimeState.activeEventSpellId = 0;
    runtimeState.grantedItems.clear();
    runtimeState.grantedItemIds.clear();
    runtimeState.clearHeldItemRequest = false;
    runtimeState.removedItemIds.clear();
    runtimeState.grantedAwardIds.clear();
    runtimeState.removedAwardIds.clear();
    runtimeState.portraitFxRequests.clear();
    runtimeState.spellFxRequests.clear();
    runtimeState.pendingDialogueContext.reset();
    runtimeState.pendingMapMove.reset();
    runtimeState.pendingMovie.reset();
    runtimeState.pendingWinGame.reset();
    runtimeState.pendingReturnToMainMenu = false;
    runtimeState.pendingInputPrompt.reset();
    runtimeState.pendingArcomageGame.reset();
    runtimeState.pendingSounds.clear();
    runtimeState.lastAffectedMechanismIds.clear();
    runtimeState.lastActivationResult.reset();
}

std::vector<uint32_t> consumeOpenedChestIds(EventRuntimeState &runtimeState)
{
    std::vector<uint32_t> openedChestIds = runtimeState.openedChestIds;
    runtimeState.openedChestIds.clear();
    runtimeState.openedChestRequests.clear();
    return openedChestIds;
}

std::vector<EventRuntimeState::OpenedChestRequest> consumeOpenedChestRequests(EventRuntimeState &runtimeState)
{
    std::vector<EventRuntimeState::OpenedChestRequest> requests = runtimeState.openedChestRequests;

    if (requests.empty())
    {
        requests.reserve(runtimeState.openedChestIds.size());

        for (uint32_t chestId : runtimeState.openedChestIds)
        {
            requests.push_back(
                EventRuntimeState::OpenedChestRequest{
                    .chestId = chestId,
                    .openedByTelekinesis = false,
                });
        }
    }

    runtimeState.openedChestIds.clear();
    runtimeState.openedChestRequests.clear();
    return requests;
}

uint32_t normalizedHistoryContinentId(uint32_t continentId)
{
    return normalizedHistoryContinent(continentId);
}

void setActiveHistoryContinent(EventRuntimeState &runtimeState, uint32_t continentId)
{
    runtimeState.activeHistoryContinentId = normalizedHistoryContinent(continentId);
    mutableHistoryEventTimesForActiveContinent(runtimeState);
    seedForwardHistoryEntries(runtimeState);
}

const std::unordered_map<uint32_t, int32_t> &historyEventTimesForActiveContinent(
    const EventRuntimeState &runtimeState)
{
    return historyEventTimesForContinent(runtimeState, runtimeState.activeHistoryContinentId);
}

EventRuntime::EventRuntime(const HouseTable *pHouseTable, const NpcDialogTable *pNpcDialogTable)
    : m_pHouseTable(pHouseTable)
    , m_pNpcDialogTable(pNpcDialogTable)
{
}

EventRuntime::~EventRuntime() = default;
EventRuntime::EventRuntime(EventRuntime &&other) noexcept = default;
EventRuntime &EventRuntime::operator=(EventRuntime &&other) noexcept = default;

void EventRuntime::bindHouseTable(const HouseTable *pHouseTable)
{
    m_pHouseTable = pHouseTable;
}

const HouseTable *EventRuntime::houseTable() const
{
    return m_pHouseTable;
}

void EventRuntime::bindNpcDialogTable(const NpcDialogTable *pNpcDialogTable)
{
    m_pNpcDialogTable = pNpcDialogTable;
}

const NpcDialogTable *EventRuntime::npcDialogTable() const
{
    return m_pNpcDialogTable;
}

uint32_t EventRuntime::outdoorModelFacetTextureOverrideKey(uint32_t modelIndex, uint32_t faceIndex)
{
    return (modelIndex << 16) | (faceIndex & 0xFFFFu);
}

uint32_t EventRuntime::monsterRelationOverrideKey(uint32_t leftMonsterId, uint32_t rightMonsterId)
{
    return (leftMonsterId << 16) | (rightMonsterId & 0xFFFFu);
}

uint64_t EventRuntime::transportRouteOverrideKey(uint32_t houseId, uint32_t routeIndex)
{
    return (static_cast<uint64_t>(houseId) << 32) | routeIndex;
}

void EventRuntime::initializeMapRuntimeState(
    const std::optional<MapDeltaData> &mapDeltaData,
    EventRuntimeState &runtimeState
) const
{
    const std::unordered_map<std::string, int32_t> namedGlobalVars = runtimeState.namedGlobalVars;
    runtimeState = {};
    runtimeState.namedGlobalVars = namedGlobalVars;

    if (mapDeltaData)
    {
        runtimeState.processedMapRespawnCount = mapDeltaData->locationInfo.respawnCount;
        runtimeState.currentLocationReputation = mapDeltaData->locationInfo.reputation;
        runtimeState.decorVars = mapDeltaData->eventVariables.decorVars;

        for (const MapDeltaDoor &door : mapDeltaData->doors)
        {
            RuntimeMechanismState runtimeMechanism = {};
            initializeRuntimeMechanismStateFromDoor(door, runtimeMechanism);
            runtimeState.mechanisms[door.doorId] = runtimeMechanism;
        }

        for (size_t mapVarIndex = 0; mapVarIndex < mapDeltaData->eventVariables.mapVars.size(); ++mapVarIndex)
        {
            runtimeState.mapVars[mapVarIndex] = mapDeltaData->eventVariables.mapVars[mapVarIndex];
        }
    }
}

bool EventRuntime::buildOnLoadState(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    const std::optional<MapDeltaData> &mapDeltaData,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext
) const
{
    initializeMapRuntimeState(mapDeltaData, runtimeState);

    return executeOnLoadEvents(localProgram, globalProgram, runtimeState, pParty, pSceneEventContext);
}

bool EventRuntime::executeOnLoadEvents(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext
) const
{
    if (!ensureLuaSession(*this, localProgram, globalProgram))
    {
        return false;
    }

    if (m_luaSessionCache == nullptr)
    {
        return true;
    }

    LuaExecutionContext executionContext = {};
    executionContext.pEventRuntime = this;
    executionContext.pRuntimeState = &runtimeState;
    executionContext.pParty = pParty;
    executionContext.pSceneEventContext = pSceneEventContext;
    // Some maps queue first-entry UI from an early on-load handler and run setup handlers afterwards.
    executionContext.preservePendingOutputsOnBegin = true;

    for (uint16_t eventId : m_luaSessionCache->globalScope.onLoadEventIds)
    {
        const auto iterator = m_luaSessionCache->globalScope.handlers.find(eventId);

        if (iterator == m_luaSessionCache->globalScope.handlers.end())
        {
            continue;
        }

        executionContext.currentEventId = eventId;
        executionContext.executingGlobalHandler = true;

        if (invokeLuaHandler(*this, iterator->second, executionContext))
        {
            ++runtimeState.globalOnLoadEventsExecuted;
            GAMEPLAY_DEBUG_TRACE(
                std::string("event_onload_executed")
                + " map=\"" + runtimeState.mapFileName + "\""
                + " scope=global"
                + " event_id=" + std::to_string(eventId)
                + " local_count=" + std::to_string(runtimeState.localOnLoadEventsExecuted)
                + " global_count=" + std::to_string(runtimeState.globalOnLoadEventsExecuted)
                + " sprite_overrides=" + std::to_string(runtimeState.spriteOverrides.size()));
        }
    }

    for (uint16_t eventId : m_luaSessionCache->localScope.onLoadEventIds)
    {
        const auto iterator = m_luaSessionCache->localScope.handlers.find(eventId);

        if (iterator == m_luaSessionCache->localScope.handlers.end())
        {
            continue;
        }

        executionContext.currentEventId = eventId;
        executionContext.executingGlobalHandler = false;

        if (invokeLuaHandler(*this, iterator->second, executionContext))
        {
            ++runtimeState.localOnLoadEventsExecuted;
            GAMEPLAY_DEBUG_TRACE(
                std::string("event_onload_executed")
                + " map=\"" + runtimeState.mapFileName + "\""
                + " scope=local"
                + " event_id=" + std::to_string(eventId)
                + " local_count=" + std::to_string(runtimeState.localOnLoadEventsExecuted)
                + " global_count=" + std::to_string(runtimeState.globalOnLoadEventsExecuted)
                + " sprite_overrides=" + std::to_string(runtimeState.spriteOverrides.size()));
        }
    }

    return true;
}

bool EventRuntime::executeOnLeaveEvents(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext
) const
{
    if (!localProgram || !ensureLuaSession(*this, localProgram, globalProgram) || m_luaSessionCache == nullptr)
    {
        return false;
    }

    LuaExecutionContext executionContext = {};
    executionContext.pEventRuntime = this;
    executionContext.pRuntimeState = &runtimeState;
    executionContext.pParty = pParty;
    executionContext.pSceneEventContext = pSceneEventContext;

    bool executedAny = false;

    for (uint16_t eventId : m_luaSessionCache->localScope.onLeaveEventIds)
    {
        const auto iterator = m_luaSessionCache->localScope.handlers.find(eventId);

        if (iterator == m_luaSessionCache->localScope.handlers.end())
        {
            continue;
        }

        if (invokeLuaHandler(*this, iterator->second, executionContext))
        {
            executedAny = true;
        }
    }

    return executedAny;
}

bool EventRuntime::validateProgramBindings(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    EventRuntimeBindingReport &report
) const
{
    report = {};

    if (!ensureLuaSession(*this, localProgram, globalProgram))
    {
        if (m_luaSessionCache != nullptr && m_luaSessionCache->lastError.has_value())
        {
            report.errorMessage = *m_luaSessionCache->lastError;
        }

        return false;
    }

    if (m_luaSessionCache == nullptr)
    {
        return true;
    }

    if (localProgram)
    {
        report.localEventCount = localProgram->eventIds().size();
        report.localHandlerCount = m_luaSessionCache->localScope.handlers.size();

        for (uint16_t eventId : localProgram->eventIds())
        {
            if (!m_luaSessionCache->localScope.handlers.contains(eventId))
            {
                report.missingLocalHandlerEventIds.push_back(eventId);
            }
        }
    }

    if (globalProgram)
    {
        report.globalEventCount = globalProgram->eventIds().size();
        report.globalHandlerCount = m_luaSessionCache->globalScope.handlers.size();
        report.canShowTopicHandlerCount = m_luaSessionCache->globalScope.canShowTopicHandlers.size();

        for (uint16_t eventId : globalProgram->eventIds())
        {
            if (!m_luaSessionCache->globalScope.handlers.contains(eventId))
            {
                report.missingGlobalHandlerEventIds.push_back(eventId);
            }
        }

        report.canShowTopicEventCount = globalProgram->canShowTopicEventIds().size();

        for (uint16_t topicId : globalProgram->canShowTopicEventIds())
        {
            if (!m_luaSessionCache->globalScope.canShowTopicHandlers.contains(topicId))
            {
                report.missingCanShowTopicEventIds.push_back(topicId);
            }
        }
    }

    return report.missingLocalHandlerEventIds.empty()
        && report.missingGlobalHandlerEventIds.empty()
        && report.missingCanShowTopicEventIds.empty();
}

void executeOpenedChestHooks(
    const EventRuntime &eventRuntime,
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    size_t openedChestBeginIndex,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext)
{
    const size_t openedChestEndIndex = runtimeState.openedChestIds.size();

    if (openedChestBeginIndex >= openedChestEndIndex)
    {
        return;
    }

    const std::optional<EventRuntimeState::ActiveHookContext> previousHookContext = runtimeState.activeHookContext;

    for (size_t openedChestIndex = openedChestBeginIndex; openedChestIndex < openedChestEndIndex; ++openedChestIndex)
    {
        EventRuntimeState::ActiveHookContext hookContext = {};
        hookContext.kind = EventRuntimeHookKind::ChestOpen;
        hookContext.chestId = runtimeState.openedChestIds[openedChestIndex];
        hookContext.heldItemId = pParty != nullptr ? pParty->heldItemIdForQueries() : 0;
        runtimeState.activeHookContext = std::move(hookContext);
        eventRuntime.executeHooks(
            localProgram,
            globalProgram,
            EventRuntimeHookKind::ChestOpen,
            runtimeState,
            pParty,
            pSceneEventContext);
    }

    runtimeState.activeHookContext = previousHookContext;
}

bool EventRuntime::executeEventById(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    uint16_t eventId,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext,
    std::optional<uint8_t> continueStep,
    bool allowGlobalFallback
) const
{
    if (eventId == 0)
    {
        return false;
    }

    if (!ensureLuaSession(*this, localProgram, globalProgram) || m_luaSessionCache == nullptr)
    {
        return false;
    }

    LuaExecutionContext executionContext = {};
    executionContext.pEventRuntime = this;
    executionContext.pRuntimeState = &runtimeState;
    executionContext.pParty = pParty;
    executionContext.pSceneEventContext = pSceneEventContext;
    executionContext.currentEventId = eventId;

    const auto localIterator = m_luaSessionCache->localScope.handlers.find(eventId);

    if (localIterator != m_luaSessionCache->localScope.handlers.end())
    {
        const size_t openedChestBeginIndex = runtimeState.openedChestIds.size();
        GAMEPLAY_DEBUG_TRACE(
            "lua_event_execute map=\"" + runtimeState.mapFileName + "\""
            + " scope=\"local\""
            + " event_id=" + std::to_string(eventId)
            + " continue_step="
            + (continueStep.has_value() ? std::to_string(*continueStep) : std::string("none")));
        const bool invoked = invokeLuaHandler(*this, localIterator->second, executionContext, continueStep);

        if (invoked)
        {
            executeOpenedChestHooks(
                *this,
                localProgram,
                globalProgram,
                openedChestBeginIndex,
                runtimeState,
                pParty,
                pSceneEventContext);
        }

        return invoked;
    }

    if (localProgram && localProgram->isHintOnlyEvent(eventId))
    {
        return true;
    }

    if (!allowGlobalFallback)
    {
        return false;
    }

    const auto globalIterator = m_luaSessionCache->globalScope.handlers.find(eventId);

    if (globalIterator != m_luaSessionCache->globalScope.handlers.end())
    {
        executionContext.executingGlobalHandler = true;
        const size_t openedChestBeginIndex = runtimeState.openedChestIds.size();
        GAMEPLAY_DEBUG_TRACE(
            "lua_event_execute map=\"" + runtimeState.mapFileName + "\""
            + " scope=\"global\""
            + " event_id=" + std::to_string(eventId)
            + " continue_step="
            + (continueStep.has_value() ? std::to_string(*continueStep) : std::string("none")));
        const bool invoked = invokeLuaHandler(*this, globalIterator->second, executionContext, continueStep);

        if (invoked)
        {
            executeOpenedChestHooks(
                *this,
                localProgram,
                globalProgram,
                openedChestBeginIndex,
                runtimeState,
                pParty,
                pSceneEventContext);
        }

        return invoked;
    }

    if (globalProgram && globalProgram->isHintOnlyEvent(eventId))
    {
        return true;
    }

    return false;
}

bool EventRuntime::executeNpcTopicEventById(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    uint16_t eventId,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext,
    std::optional<uint8_t> continueStep
) const
{
    if (eventId == 0)
    {
        return false;
    }

    if (!ensureLuaSession(*this, localProgram, globalProgram) || m_luaSessionCache == nullptr)
    {
        return false;
    }

    LuaExecutionContext executionContext = {};
    executionContext.pEventRuntime = this;
    executionContext.pRuntimeState = &runtimeState;
    executionContext.pParty = pParty;
    executionContext.pSceneEventContext = pSceneEventContext;
    executionContext.currentEventId = eventId;
    executionContext.allowStandaloneMapEventDialogueContext = false;

    const bool continueExistingMapEventDialogue =
        runtimeState.pendingDialogueContext
        && runtimeState.pendingDialogueContext->kind == DialogueContextKind::MapEvent;

    if (continueExistingMapEventDialogue)
    {
        const auto localIterator = m_luaSessionCache->localScope.handlers.find(eventId);

        if (localIterator != m_luaSessionCache->localScope.handlers.end())
        {
            return invokeLuaHandler(*this, localIterator->second, executionContext, continueStep);
        }

        if (localProgram && localProgram->isHintOnlyEvent(eventId))
        {
            return true;
        }
    }

    const auto globalIterator = m_luaSessionCache->globalScope.handlers.find(eventId);

    if (globalIterator != m_luaSessionCache->globalScope.handlers.end())
    {
        executionContext.executingGlobalHandler = true;
        return invokeLuaHandler(*this, globalIterator->second, executionContext, continueStep);
    }

    const auto localIterator = m_luaSessionCache->localScope.handlers.find(eventId);

    if (localIterator != m_luaSessionCache->localScope.handlers.end())
    {
        return invokeLuaHandler(*this, localIterator->second, executionContext, continueStep);
    }

    if ((globalProgram && globalProgram->isHintOnlyEvent(eventId))
        || (localProgram && localProgram->isHintOnlyEvent(eventId)))
    {
        return true;
    }

    return false;
}

bool EventRuntime::canShowTopic(
    const std::optional<ScriptedEventProgram> &globalProgram,
    uint16_t topicId,
    const EventRuntimeState &runtimeState,
    const Party *pParty,
    const ISceneEventContext *pSceneEventContext
) const
{
    if (topicId == 0 || !globalProgram)
    {
        return topicId != 0;
    }

    if (isTradingTriangleBuyTopic(topicId))
    {
        return true;
    }

    if (!ensureLuaSession(*this, std::nullopt, globalProgram) || m_luaSessionCache == nullptr)
    {
        return false;
    }

    const auto iterator = m_luaSessionCache->globalScope.canShowTopicHandlers.find(topicId);

    if (iterator == m_luaSessionCache->globalScope.canShowTopicHandlers.end())
    {
        return true;
    }

    LuaExecutionContext executionContext = {};
    executionContext.pEventRuntime = this;
    executionContext.pReadonlyRuntimeState = &runtimeState;
    executionContext.pReadonlyParty = pParty;
    executionContext.pReadonlySceneEventContext = pSceneEventContext;
    executionContext.readonly = true;
    std::optional<bool> visible = std::nullopt;

    if (!invokeLuaHandler(*this, iterator->second, executionContext, std::nullopt, &visible))
    {
        return false;
    }

    return visible.value_or(true);
}

const std::vector<uint16_t> &hookEventIdsForKind(
    const LuaScopeProgram &scopeProgram,
    EventRuntimeHookKind kind)
{
    switch (kind)
    {
        case EventRuntimeHookKind::NpcEnter:
            return scopeProgram.npcEnterHookEventIds;
        case EventRuntimeHookKind::NpcExit:
            return scopeProgram.npcExitHookEventIds;
        case EventRuntimeHookKind::HouseTopicFilter:
            return scopeProgram.houseTopicFilterHookEventIds;
        case EventRuntimeHookKind::HouseTopicClick:
            return scopeProgram.houseTopicClickHookEventIds;
        case EventRuntimeHookKind::RestFoodCost:
            return scopeProgram.restFoodCostHookEventIds;
        case EventRuntimeHookKind::GameplayAction:
            return scopeProgram.gameplayActionHookEventIds;
        case EventRuntimeHookKind::MapRefill:
            return scopeProgram.mapRefillHookEventIds;
        case EventRuntimeHookKind::MapTransition:
            return scopeProgram.mapTransitionHookEventIds;
        case EventRuntimeHookKind::MonsterKilled:
            return scopeProgram.monsterKilledHookEventIds;
        case EventRuntimeHookKind::MonsterDamage:
            return scopeProgram.monsterDamageHookEventIds;
        case EventRuntimeHookKind::ChestOpen:
            return scopeProgram.chestOpenHookEventIds;
        case EventRuntimeHookKind::InventoryOpen:
            return scopeProgram.inventoryOpenHookEventIds;
    }

    return scopeProgram.npcEnterHookEventIds;
}

bool executeHookScope(
    const EventRuntime &eventRuntime,
    const LuaScopeProgram &scopeProgram,
    EventRuntimeHookKind kind,
    LuaExecutionContext &executionContext)
{
    bool executedAny = false;

    for (uint16_t eventId : hookEventIdsForKind(scopeProgram, kind))
    {
        const auto iterator = scopeProgram.handlers.find(eventId);

        if (iterator == scopeProgram.handlers.end())
        {
            continue;
        }

        executionContext.currentEventId = eventId;

        if (invokeLuaHandler(eventRuntime, iterator->second, executionContext))
        {
            executedAny = true;
        }
    }

    return executedAny;
}

bool scriptedProgramHasHook(
    const std::optional<ScriptedEventProgram> &program,
    EventRuntimeHookKind kind)
{
    if (!program)
    {
        return false;
    }

    switch (kind)
    {
        case EventRuntimeHookKind::MonsterKilled:
            return !program->monsterKilledHookEventIds().empty();

        case EventRuntimeHookKind::MonsterDamage:
            return !program->monsterDamageHookEventIds().empty();

        default:
            return true;
    }
}

bool EventRuntime::executeHooks(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    EventRuntimeHookKind kind,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext) const
{
    if (!runtimeState.activeHookContext)
    {
        return false;
    }

    if (!scriptedProgramHasHook(localProgram, kind) && !scriptedProgramHasHook(globalProgram, kind))
    {
        return false;
    }

    if (!ensureLuaSession(*this, localProgram, globalProgram) || m_luaSessionCache == nullptr)
    {
        return false;
    }

    LuaExecutionContext executionContext = {};
    executionContext.pEventRuntime = this;
    executionContext.pRuntimeState = &runtimeState;
    executionContext.pParty = pParty;
    executionContext.pSceneEventContext = pSceneEventContext;
    executionContext.preservePendingOutputsOnBegin = true;
    executionContext.preserveRuntimeOutputsOnBegin = true;

    const bool globalExecuted = executeHookScope(*this, m_luaSessionCache->globalScope, kind, executionContext);
    const bool localExecuted = executeHookScope(*this, m_luaSessionCache->localScope, kind, executionContext);
    return globalExecuted || localExecuted;
}

bool EventRuntime::executeMapRefillHooks(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    const std::optional<MapDeltaData> &mapDeltaData,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext) const
{
    if (!mapDeltaData || mapDeltaData->locationInfo.respawnCount <= runtimeState.processedMapRespawnCount)
    {
        return false;
    }

    runtimeState.processedMapRespawnCount = mapDeltaData->locationInfo.respawnCount;

    EventRuntimeState::ActiveHookContext hookContext = {};
    hookContext.kind = EventRuntimeHookKind::MapRefill;
    runtimeState.activeHookContext = hookContext;
    const bool executed = executeHooks(
        localProgram,
        globalProgram,
        EventRuntimeHookKind::MapRefill,
        runtimeState,
        pParty,
        pSceneEventContext);
    runtimeState.activeHookContext.reset();
    return executed;
}

void EventRuntime::advanceMechanisms(
    const std::optional<MapDeltaData> &mapDeltaData,
    float deltaMilliseconds,
    EventRuntimeState &runtimeState
) const
{
    if (!mapDeltaData || deltaMilliseconds == 0)
    {
        return;
    }

    for (const MapDeltaDoor &door : mapDeltaData->doors)
    {
        const std::unordered_map<uint32_t, RuntimeMechanismState>::iterator iterator =
            runtimeState.mechanisms.find(door.doorId);

        if (iterator == runtimeState.mechanisms.end() || !iterator->second.isMoving)
        {
            continue;
        }

        RuntimeMechanismState &runtimeMechanism = iterator->second;
        runtimeMechanism.timeSinceTriggeredMs += deltaMilliseconds;
        runtimeMechanism.currentDistance =
            calculateMechanismDistance(door, runtimeMechanism);
        const auto logMechanismCompleted =
            [&door](const RuntimeMechanismState &mechanism, float elapsedMs)
            {
                GAMEPLAY_DEBUG_TRACE(
                    "mechanism_completed kind=indoor_door id=" + std::to_string(door.doorId)
                    + " state=" + gameplayDebugTraceMechanismStateName(mechanism.state)
                    + " elapsed_seconds=" + std::to_string(elapsedMs / 1000.0f)
                    + " door_slot=" + std::to_string(door.slotIndex)
                    + " move_length=" + std::to_string(door.moveLength)
                    + " open_speed=" + std::to_string(door.openSpeed)
                    + " close_speed=" + std::to_string(door.closeSpeed));
            };

        if (door.moveLength <= 0)
        {
            const float elapsedMs = runtimeMechanism.timeSinceTriggeredMs;
            runtimeMechanism.state =
                runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing)
                    ? static_cast<uint16_t>(EvtMechanismState::Closed)
                    : static_cast<uint16_t>(EvtMechanismState::Open);
            runtimeMechanism.timeSinceTriggeredMs = 0.0f;
            runtimeMechanism.currentDistance = 0.0f;
            runtimeMechanism.isMoving = false;
            logMechanismCompleted(runtimeMechanism, elapsedMs);
            continue;
        }

        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
        {
            if (door.closeSpeed <= 0)
            {
                const float elapsedMs = runtimeMechanism.timeSinceTriggeredMs;
                runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closed);
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = static_cast<float>(door.moveLength);
                runtimeMechanism.isMoving = false;
                logMechanismCompleted(runtimeMechanism, elapsedMs);
                continue;
            }

            const float closedDistance = runtimeMechanism.timeSinceTriggeredMs * float(door.closeSpeed) / 1000.0f;

            if (closedDistance >= float(door.moveLength))
            {
                const float elapsedMs = runtimeMechanism.timeSinceTriggeredMs;
                runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closed);
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = static_cast<float>(door.moveLength);
                runtimeMechanism.isMoving = false;
                logMechanismCompleted(runtimeMechanism, elapsedMs);
            }
        }
        else if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
        {
            if (door.openSpeed <= 0)
            {
                const float elapsedMs = runtimeMechanism.timeSinceTriggeredMs;
                runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = 0.0f;
                runtimeMechanism.isMoving = false;
                logMechanismCompleted(runtimeMechanism, elapsedMs);
                continue;
            }

            const float openedDistance = runtimeMechanism.timeSinceTriggeredMs * float(door.openSpeed) / 1000.0f;

            if (openedDistance >= float(door.moveLength))
            {
                const float elapsedMs = runtimeMechanism.timeSinceTriggeredMs;
                runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = 0.0f;
                runtimeMechanism.isMoving = false;
                logMechanismCompleted(runtimeMechanism, elapsedMs);
            }
        }
        else
        {
            runtimeMechanism.isMoving = false;
        }
    }
}


int32_t EventRuntime::getInventoryItemCount(
    const EventRuntimeState &runtimeState,
    const Party *pParty,
    uint32_t objectDescriptionId,
    const std::optional<size_t> &memberIndex
)
{
    int32_t itemCount = pParty != nullptr ? pParty->inventoryItemCount(objectDescriptionId, memberIndex) : 0;

    if (!memberIndex)
    {
        for (const InventoryItem &item : runtimeState.grantedItems)
        {
            if (item.objectDescriptionId == objectDescriptionId)
            {
                itemCount += static_cast<int32_t>(std::max<uint32_t>(1, item.quantity));
            }
        }

        for (uint32_t grantedItemId : runtimeState.grantedItemIds)
        {
            if (grantedItemId == objectDescriptionId)
            {
                itemCount += 1;
            }
        }

        for (uint32_t removedItemId : runtimeState.removedItemIds)
        {
            if (removedItemId == objectDescriptionId)
            {
                itemCount = std::max(0, itemCount - 1);
            }
        }
    }

    return itemCount;
}

float EventRuntime::calculateMechanismDistance(
    const MapDeltaDoor &door,
    const RuntimeMechanismState &runtimeMechanism
)
{
    return mechanismDistanceForState(door, runtimeMechanism.state, runtimeMechanism.timeSinceTriggeredMs);
}

void EventRuntime::applyMechanismAction(
    RuntimeMechanismState &runtimeMechanism,
    const MapDeltaDoor *pDoor,
    MechanismAction action
)
{
    if (action == MechanismAction::Trigger)
    {
        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening)
            || runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
        {
            return;
        }

        runtimeMechanism.timeSinceTriggeredMs = 0.0f;

        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closed))
        {
            runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Opening);
        }
        else
        {
            runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closing);
        }

        runtimeMechanism.isMoving = true;
        return;
    }

    if (action == MechanismAction::Open)
    {
        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Open)
            || runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
        {
            return;
        }

        if (pDoor != nullptr && runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
        {
            const float openDistance =
                std::max(0.0f, static_cast<float>(pDoor->moveLength) - runtimeMechanism.currentDistance);
            runtimeMechanism.timeSinceTriggeredMs =
                openDistance * 1000.0f / std::max(1.0f, static_cast<float>(pDoor->openSpeed));
        }
        else
        {
            runtimeMechanism.timeSinceTriggeredMs = 0.0f;
        }

        runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Opening);
        runtimeMechanism.isMoving = true;
        return;
    }

    if (action == MechanismAction::Close)
    {
        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closed)
            || runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
        {
            return;
        }

        if (pDoor != nullptr && runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
        {
            runtimeMechanism.timeSinceTriggeredMs =
                runtimeMechanism.currentDistance * 1000.0f / std::max(1.0f, static_cast<float>(pDoor->closeSpeed));
        }
        else
        {
            runtimeMechanism.timeSinceTriggeredMs = 0.0f;
        }

        runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closing);
        runtimeMechanism.isMoving = true;
    }
}

namespace
{
bool evaluateCompareValue(
    const EventRuntimeState &runtimeState,
    uint32_t rawVariableId,
    int32_t compareValue,
    const Party *pParty,
    const std::vector<size_t> &targetMemberIndices,
    bool usePartyWideInventory,
    const ISceneEventContext *pSceneEventContext
)
{
    const EventRuntime::VariableRef variable = EventRuntime::decodeVariable(rawVariableId);
    const EvtVariable variableId = static_cast<EvtVariable>(variable.tag);
    const std::optional<size_t> memberIndex =
        usePartyWideInventory && variable.kind == EventRuntime::VariableKind::Inventory
            ? std::nullopt
            : singleTargetMemberIndex(targetMemberIndices);
    const int32_t currentValue =
        EventRuntime::getVariableValue(runtimeState, variable, pParty, memberIndex, pSceneEventContext);

    if (variable.kind == EventRuntime::VariableKind::ClassId)
    {
        if (targetMemberIndices.empty())
        {
            return classIdMatchesPromotionFamily(pParty, currentValue, compareValue);
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            const int32_t targetValue =
                EventRuntime::getVariableValue(
                    runtimeState,
                    variable,
                    pParty,
                    targetMemberIndex,
                    pSceneEventContext);

            if (classIdMatchesPromotionFamily(pParty, targetValue, compareValue))
            {
                return true;
            }
        }

        return false;
    }

    if (variable.kind == EventRuntime::VariableKind::Awards
        || variable.kind == EventRuntime::VariableKind::Players)
    {
        return currentValue != 0;
    }

    if (variable.kind == EventRuntime::VariableKind::Generic)
    {
        const std::unordered_map<uint32_t, int32_t>::const_iterator iterator =
            runtimeState.variables.find(variable.rawId);
        return iterator != runtimeState.variables.end() && iterator->second >= compareValue;
    }

    if (variable.kind == EventRuntime::VariableKind::AutoNote
        || variable.kind == EventRuntime::VariableKind::History
        || variable.kind == EventRuntime::VariableKind::QBits
        || variable.kind == EventRuntime::VariableKind::BoolFlag
        || variable.kind == EventRuntime::VariableKind::Condition
        || variable.kind == EventRuntime::VariableKind::StatMoreThanBase)
    {
        return currentValue != 0;
    }

    if (variable.kind == EventRuntime::VariableKind::Inventory)
    {
        return currentValue != 0;
    }

    if (variable.kind == EventRuntime::VariableKind::DayOfWeek
        || variable.kind == EventRuntime::VariableKind::DayOfYear
        || variable.kind == EventRuntime::VariableKind::Hour)
    {
        return currentValue == compareValue;
    }

    if ((variable.kind == EventRuntime::VariableKind::MaxHealth
         || variable.kind == EventRuntime::VariableKind::MaxSpellPoints)
        && memberIndex)
    {
        const Character *pMember = pParty != nullptr ? pParty->member(*memberIndex) : nullptr;

        if (pMember == nullptr)
        {
            return false;
        }

        if (variable.kind == EventRuntime::VariableKind::MaxHealth)
        {
            return pMember->health >= resolveCharacterEffectiveMaxHealth(*pMember);
        }

        return pMember->spellPoints >= resolveCharacterEffectiveMaxSpellPoints(*pMember);
    }

    if (variable.kind == EventRuntime::VariableKind::PartyState)
    {
        if (variableId == EvtVariable::PlayerBits)
        {
            return currentValue != 0;
        }

        if (variableId == EvtVariable::MonthIs)
        {
            return currentValue == compareValue;
        }

        if (variableId >= EvtVariable::Counter1 && variableId <= EvtVariable::Counter10)
        {
            if (currentValue == 0)
            {
                return false;
            }

            return currentGameMinutesFromRuntimeState(runtimeState) >= currentValue + compareValue * 60;
        }

        if (variableId == EvtVariable::Unknown1)
        {
            return currentValue == compareValue;
        }

        if (variableId == EvtVariable::Invisible || variableId == EvtVariable::IsFlying)
        {
            return currentValue != 0;
        }

        if (variableId == EvtVariable::ItemEquipped)
        {
            if (!memberIndex || pParty == nullptr)
            {
                return false;
            }

            const Character *pMember = pParty->member(*memberIndex);

            if (pMember == nullptr)
            {
                return false;
            }

            const uint32_t itemId = static_cast<uint32_t>(compareValue);
            return pMember->equipment.offHand == itemId
                || pMember->equipment.mainHand == itemId
                || pMember->equipment.bow == itemId
                || pMember->equipment.armor == itemId
                || pMember->equipment.helm == itemId
                || pMember->equipment.belt == itemId
                || pMember->equipment.cloak == itemId
                || pMember->equipment.gauntlets == itemId
                || pMember->equipment.boots == itemId
                || pMember->equipment.amulet == itemId
                || pMember->equipment.ring1 == itemId
                || pMember->equipment.ring2 == itemId
                || pMember->equipment.ring3 == itemId
                || pMember->equipment.ring4 == itemId
                || pMember->equipment.ring5 == itemId
                || pMember->equipment.ring6 == itemId;
        }
    }

    return currentValue >= compareValue;
}

}

}
