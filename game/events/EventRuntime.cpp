#include "game/events/ISceneEventContext.h"
#include "game/events/EventRuntime.h"
#include "engine/scripting/LuaStateOwner.h"
#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"

#include <iostream>
#include <algorithm>
#include <cmath>
#include <limits>
#include <sstream>
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

int resolveMonthFromDayOfYear(int dayOfYear);
int currentGameMinutesFromRuntimeState(const EventRuntimeState &runtimeState);
uint32_t randomJumpSeed(uint16_t eventId, uint8_t step, const EventRuntimeState &runtimeState);
std::optional<std::string> skillNameForEvtVariable(EvtVariable variableId);
bool evaluateCompareValue(
    const EventRuntimeState &runtimeState,
    uint32_t rawVariableId,
    int32_t compareValue,
    const Party *pParty,
    const std::vector<size_t> &targetMemberIndices);
const MapDeltaDoor *findMechanismDoorById(const MapDeltaData *pMapDeltaData, uint32_t mechanismId);
void initializeRuntimeMechanismStateFromDoor(
    const MapDeltaDoor &door,
    RuntimeMechanismState &runtimeMechanism);

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

    std::mt19937 rng(randomJumpSeed(
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

    if (state == static_cast<uint16_t>(EvtMechanismState::Closed) || (door.attributes & 0x2) != 0)
    {
        return static_cast<float>(door.moveLength);
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
        case EvtVariable::RepairSkill: return "Repair";
        case EvtVariable::BodybuildingSkill: return "Bodybuilding";
        case EvtVariable::MeditationSkill: return "Meditation";
        case EvtVariable::PerceptionSkill: return "Perception";
        case EvtVariable::DiplomacySkill: return "Diplomacy";
        case EvtVariable::ThieverySkill: return "Thievery";
        case EvtVariable::DisarmTrapSkill: return "DisarmTrap";
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

std::optional<PortraitId> eventPortraitId(uint32_t rawPortraitId)
{
    if (rawPortraitId == 0)
    {
        return std::nullopt;
    }

    const PortraitId portraitId = static_cast<PortraitId>(rawPortraitId);
    return portraitId == PortraitId::Invalid ? std::nullopt : std::optional<PortraitId>(portraitId);
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
    request.x = x;
    request.y = y;
    request.positional = positional;
    runtimeState.pendingSounds.push_back(std::move(request));
}

bool characterMeetsSkillCheck(const Character &member, EvtVariable skillVariable, SkillMastery mastery, uint32_t level)
{
    const std::optional<std::string> skillName = skillNameForEvtVariable(skillVariable);

    if (!skillName)
    {
        return false;
    }

    const CharacterSkill *pSkill = member.findSkill(*skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    return pSkill->level >= level && pSkill->mastery == mastery;
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
    return std::max(
        1,
        member.maxHealth + member.permanentBonuses.maxHealth + member.magicalBonuses.maxHealth
    );
}

int resolveCharacterEffectiveMaxSpellPoints(const Character &member)
{
    return std::max(
        0,
        member.maxSpellPoints + member.permanentBonuses.maxSpellPoints + member.magicalBonuses.maxSpellPoints
    );
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
        case EvtVariable::CircusPrises:
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
    const std::optional<size_t> &memberIndex
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
        const std::unordered_map<uint32_t, int32_t>::const_iterator iterator = runtimeState.variables.find(variable.rawId);
        return iterator != runtimeState.variables.end() ? iterator->second : 0;
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

        const std::optional<uint32_t> classId = mm8ClassIdForClassName(pMember->className);
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
        const Character *pMember = resolveCharacterForVariableRead(pParty, memberIndex);

        if (pMember == nullptr)
        {
            return 0;
        }

        const std::optional<std::string> skillName = skillNameForEvtVariable(variableId);

        if (!skillName)
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
                    ? ((pMember->playerBits & (1u << std::min<uint32_t>(variable.index, MaxBitfieldFlagIndex))) != 0 ? 1 : 0)
                    : 0;

            case EvtVariable::Npcs2:
                return pMember != nullptr
                    ? ((pMember->npcs2 & (1u << std::min<uint32_t>(variable.index, MaxBitfieldFlagIndex))) != 0 ? 1 : 0)
                    : 0;

            case EvtVariable::IsFlying:
                return pParty != nullptr && pParty->hasPartyBuff(PartyBuffId::Fly) ? 1 : 0;

            case EvtVariable::NumSkillPoints:
                return pMember != nullptr ? static_cast<int32_t>(pMember->skillPoints) : 0;

            case EvtVariable::MonthIs:
                return resolveMonthFromDayOfYear(getVariableValue(
                    runtimeState,
                    decodeVariable(static_cast<uint32_t>(EvtVariable::DayOfYear)),
                    pParty));

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
    const std::vector<size_t> &targetMemberIndices
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
        if (pParty != nullptr && !targetMemberIndices.empty())
        {
            for (size_t memberIndex : targetMemberIndices)
            {
                if (value != 0)
                {
                    pParty->addAward(memberIndex, variable.index);
                }
                else
                {
                    pParty->removeAward(memberIndex, variable.index);
                }
            }

            if (value != 0)
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
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

        if (normalizedValue != 0 && previousValue == 0)
        {
            runtimeState.historyEventTimes[variable.index] = std::max(1, currentGameMinutesFromRuntimeState(runtimeState));
        }
        else if (normalizedValue == 0)
        {
            runtimeState.historyEventTimes.erase(variable.index);
        }

        return;
    }

    if (variable.kind == VariableKind::ClassId)
    {
        if (pParty == nullptr)
        {
            return;
        }

        const std::optional<std::string> className = classNameForMm8ClassId(static_cast<uint32_t>(value));

        if (!className)
        {
            return;
        }

        for (size_t memberIndex : targetMemberIndices)
        {
            pParty->setMemberClassName(memberIndex, *className);
        }

        if (!targetMemberIndices.empty())
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
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
                continue;
            }

            CharacterSkill &skill = pMember->skills[*skillName];
            skill.name = *skillName;
            skill.level = level;
            skill.mastery = mastery;
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
            Character *pMember = pParty->member(targetMemberIndex);

            if (pMember == nullptr)
            {
                continue;
            }

            pMember->conditions.set(static_cast<size_t>(*condition), value != 0);
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
            }
        }

        return;
    }

    if (variable.kind == VariableKind::MapPersistent)
    {
        if (variable.index < runtimeState.mapVars.size())
        {
            runtimeState.mapVars[variable.index] = static_cast<uint8_t>(std::clamp(value, 0, 255));
        }
        return;
    }

    if (variable.kind == VariableKind::DecorPersistent)
    {
        if (variable.index < runtimeState.decorVars.size())
        {
            runtimeState.decorVars[variable.index] = static_cast<uint8_t>(std::clamp(value, 0, 255));
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

                if (pMember == nullptr || variable.index >= 32)
                {
                    continue;
                }

                if (value != 0)
                {
                    pMember->playerBits |= (1u << std::min<uint32_t>(variable.index, MaxBitfieldFlagIndex));
                }
                else
                {
                    pMember->playerBits &= ~(1u << std::min<uint32_t>(variable.index, MaxBitfieldFlagIndex));
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

        if (pParty != nullptr)
        {
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

        if (variable.kind == VariableKind::QBits && value != 0 && previousValue == 0)
        {
            queuePortraitFxRequest(runtimeState, PortraitFxEventKind::AwardGain, pParty, targetMemberIndices);
        }

        return;
    }

    if (variable.kind == VariableKind::History)
    {
        const int32_t normalizedValue = value != 0 ? 1 : 0;
        runtimeState.variables[variable.rawId] = normalizedValue;

        if (normalizedValue != 0 && previousValue == 0)
        {
            runtimeState.historyEventTimes[variable.index] = std::max(1, currentGameMinutesFromRuntimeState(runtimeState));
        }
        else if (normalizedValue == 0)
        {
            runtimeState.historyEventTimes.erase(variable.index);
        }

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
    const std::vector<size_t> &targetMemberIndices
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
        if (pParty != nullptr && !targetMemberIndices.empty())
        {
            for (size_t memberIndex : targetMemberIndices)
            {
                if (value > 0)
                {
                    pParty->addAward(memberIndex, variable.index);
                }
            }

            if (value > 0)
            {
                queuePortraitFxRequest(runtimeState, PortraitFxEventKind::QuestComplete, pParty, targetMemberIndices);
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

        if (updatedValue != 0 && previousValue == 0)
        {
            runtimeState.historyEventTimes[variable.index] = std::max(1, currentGameMinutesFromRuntimeState(runtimeState));
        }

        return;
    }

    if (variable.kind == VariableKind::ClassId)
    {
        setVariableValue(runtimeState, variable, value, pParty, targetMemberIndices);
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
            const int updatedValue = std::clamp(static_cast<int>(runtimeState.mapVars[variable.index]) + value, 0, 255);
            runtimeState.mapVars[variable.index] = static_cast<uint8_t>(updatedValue);
        }
        return;
    }

    if (variable.kind == VariableKind::DecorPersistent)
    {
        if (variable.index < runtimeState.decorVars.size())
        {
            const int updatedValue = std::clamp(static_cast<int>(runtimeState.decorVars[variable.index]) + value, 0, 255);
            runtimeState.decorVars[variable.index] = static_cast<uint8_t>(updatedValue);
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

        if (pParty != nullptr)
        {
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

        if (variable.kind == VariableKind::QBits && value != 0 && previousValue == 0)
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
            runtimeState.historyEventTimes.erase(variable.index);
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
        if (pParty != nullptr && !targetMemberIndices.empty())
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
            const int updatedValue = std::clamp(static_cast<int>(runtimeState.mapVars[variable.index]) - value, 0, 255);
            runtimeState.mapVars[variable.index] = static_cast<uint8_t>(updatedValue);
        }
        return;
    }

    if (variable.kind == VariableKind::DecorPersistent)
    {
        if (variable.index < runtimeState.decorVars.size())
        {
            const int updatedValue = std::clamp(static_cast<int>(runtimeState.decorVars[variable.index]) - value, 0, 255);
            runtimeState.decorVars[variable.index] = static_cast<uint8_t>(updatedValue);
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

    const std::optional<size_t> memberIndex = singleTargetMemberIndex(targetMemberIndices);

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
};

struct LuaExecutionContext
{
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
void prepareRuntimeStateForEventExecution(EventRuntimeState &runtimeState, const ISceneEventContext *pSceneEventContext)
{
    runtimeState.lastAffectedMechanismIds.clear();
    runtimeState.openedChestIds.clear();
    runtimeState.grantedItems.clear();
    runtimeState.grantedItemIds.clear();
    runtimeState.removedItemIds.clear();
    runtimeState.grantedAwardIds.clear();
    runtimeState.removedAwardIds.clear();
    runtimeState.pendingDialogueContext.reset();
    runtimeState.pendingMapMove.reset();
    runtimeState.pendingMovie.reset();
    runtimeState.pendingInputPrompt.reset();
    runtimeState.pendingSounds.clear();
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
        prepareRuntimeStateForEventExecution(*pRuntimeState, pExecutionContext->pSceneEventContext);
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
    const uint32_t rawVariableId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const int32_t compareValue = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
    lua_pushboolean(
        pLuaState,
        evaluateCompareValue(
            *readableRuntimeState(pLuaState),
            rawVariableId,
            compareValue,
            readableParty(pLuaState),
            selectedTargetMemberIndices(pLuaState)));
    return 1;
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
    pRuntimeState->npcHouseOverrides[static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))] =
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    return 0;
}

int luaRandomJump(lua_State *pLuaState)
{
    const uint16_t eventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    const uint8_t step = static_cast<uint8_t>(luaL_checkinteger(pLuaState, 2));
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
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

    const uint32_t seed = randomJumpSeed(eventId, step, *pRuntimeState);
    lua_pushinteger(pLuaState, validTargets[seed % validTargets.size()]);
    return 1;
}

int luaDamagePlayer(lua_State *pLuaState)
{
    Party *pParty = writableParty(pLuaState);

    if (pParty == nullptr)
    {
        return 0;
    }

    const int damage = static_cast<int>(luaL_checkinteger(pLuaState, 3));
    const std::vector<size_t> targets = selectedTargetMemberIndices(pLuaState);
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
        pRuntimeState->snowEnabled = lua_toboolean(pLuaState, 2) != 0;
    }

    return 0;
}

int luaSetRain(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)) == 0)
    {
        pRuntimeState->rainEnabled = lua_toboolean(pLuaState, 2) != 0;
    }

    return 0;
}

int luaShowMovie(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    EventRuntimeState::PendingMovie movie = {};
    movie.movieName = sanitizeEventString(luaL_checkstring(pLuaState, 1));
    movie.restoreAfterPlayback = lua_toboolean(pLuaState, 2) != 0;
    pRuntimeState->pendingMovie = std::move(movie);
    return 0;
}

int luaSetSprite(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t cogNumber = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    EventRuntimeState::SpriteOverride spriteOverride = {};
    spriteOverride.hidden = lua_toboolean(pLuaState, 2) != 0;

    if (lua_gettop(pLuaState) >= 3 && lua_type(pLuaState, 3) == LUA_TSTRING)
    {
        spriteOverride.textureName = sanitizeEventString(lua_tostring(pLuaState, 3));
    }

    pRuntimeState->spriteOverrides[cogNumber] = std::move(spriteOverride);
    return 0;
}

int luaEnterHouse(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->messages.clear();
    EventRuntimeState::PendingDialogueContext context = {};
    context.kind = DialogueContextKind::HouseService;
    context.sourceId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    context.hostHouseId = context.sourceId;
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
    EventRuntimeState::PendingMapMove move = {};
    const int argumentCount = lua_gettop(pLuaState);
    move.x = static_cast<int32_t>(luaL_checkinteger(pLuaState, 1));
    move.y = static_cast<int32_t>(luaL_checkinteger(pLuaState, 2));
    move.z = static_cast<int32_t>(luaL_checkinteger(pLuaState, 3));

    if (argumentCount >= 4 && lua_type(pLuaState, 4) != LUA_TNIL)
    {
        move.directionDegrees = moveToMapYawUnitsToDegrees(static_cast<int32_t>(luaL_checkinteger(pLuaState, 4)));
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

        if (!mapName.empty())
        {
            move.mapName = mapName;
        }
    }

    pRuntimeState->pendingMapMove = std::move(move);
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

    const EvtVariable skillVariable = static_cast<EvtVariable>(luaL_checkinteger(pLuaState, 1));
    const SkillMastery mastery = static_cast<SkillMastery>(luaL_checkinteger(pLuaState, 2));
    const uint32_t level = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 3));
    bool passed = false;

    for (size_t memberIndex : selectedTargetMemberIndices(pLuaState))
    {
        const Character *pMember = pParty->member(memberIndex);

        if (pMember != nullptr && characterMeetsSkillCheck(*pMember, skillVariable, mastery, level))
        {
            passed = true;
            break;
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
        lua_toboolean(pLuaState, 7) != 0);
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
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    pRuntimeState->npcGreetingOverrides[npcId] = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    pRuntimeState->npcGreetingDisplayCounts[npcId] = 0;
    return 0;
}

int luaSetNpcItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t npcId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isGive = lua_gettop(pLuaState) < 3 || lua_toboolean(pLuaState, 3) != 0;
    pRuntimeState->npcItemOverrides[npcId] = isGive ? itemId : 0;
    return 0;
}

int luaSetMonsterItem(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t actorId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t itemId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isGive = lua_gettop(pLuaState) < 3 || lua_toboolean(pLuaState, 3) != 0;

    if (isGive && itemId != 0)
    {
        pRuntimeState->actorItemOverrides[actorId] = itemId;
        pRuntimeState->actorSetMasks[actorId] |= static_cast<uint32_t>(EvtActorAttribute::HasItem);
        pRuntimeState->actorClearMasks[actorId] &= ~static_cast<uint32_t>(EvtActorAttribute::HasItem);
    }
    else
    {
        pRuntimeState->actorItemOverrides.erase(actorId);
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

    const SpeechId speechId = static_cast<SpeechId>(luaL_checkinteger(pLuaState, 1));

    for (size_t memberIndex : selectedTargetMemberIndices(pLuaState))
    {
        pParty->requestSpeech(memberIndex, speechId);
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
    const bool isOn = lua_toboolean(pLuaState, 3) != 0;

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
    }

    return 0;
}

int luaInputString(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    EventRuntimeState::PendingInputPrompt prompt = {};
    prompt.kind = EventRuntimeState::PendingInputPrompt::Kind::InputString;
    prompt.eventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    prompt.continueStep = static_cast<uint8_t>(luaL_checkinteger(pLuaState, 2));
    prompt.textId = static_cast<uint32_t>(luaL_optinteger(pLuaState, 3, 0));

    if (lua_gettop(pLuaState) >= 4 && lua_type(pLuaState, 4) == LUA_TSTRING)
    {
        prompt.text = lua_tostring(pLuaState, 4);
    }

    pRuntimeState->pendingInputPrompt = std::move(prompt);
    return 0;
}

int luaPressAnyKey(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    EventRuntimeState::PendingInputPrompt prompt = {};
    prompt.kind = EventRuntimeState::PendingInputPrompt::Kind::PressAnyKey;
    prompt.eventId = static_cast<uint16_t>(luaL_checkinteger(pLuaState, 1));
    prompt.continueStep = static_cast<uint8_t>(luaL_checkinteger(pLuaState, 2));
    pRuntimeState->pendingInputPrompt = std::move(prompt);
    return 0;
}

int luaSpecialJump(lua_State *pLuaState)
{
    (void)pLuaState;
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
    const EventRuntimeState *pRuntimeState = readableRuntimeState(pLuaState);
    lua_pushboolean(
        pLuaState,
        pRuntimeState->unavailableNpcIds.contains(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))));
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
            lua_toboolean(pLuaState, 4) != 0));
    return 1;
}

int luaAdd(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    EventRuntime::addVariableValue(
        *pRuntimeState,
        EventRuntime::decodeVariable(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 2)),
        writableParty(pLuaState),
        selectedTargetMemberIndices(pLuaState));
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
    EventRuntime::setVariableValue(
        *pRuntimeState,
        EventRuntime::decodeVariable(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))),
        static_cast<int32_t>(luaL_checkinteger(pLuaState, 2)),
        writableParty(pLuaState),
        selectedTargetMemberIndices(pLuaState));
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
    pRuntimeState->statusMessages.push_back(luaL_checkstring(pLuaState, 1));
    return 0;
}

int luaOpenChest(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->openedChestIds.push_back(static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1)));
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

    EventRuntime::applyMechanismAction(runtimeMechanism, pDoor, action);
    pRuntimeState->lastAffectedMechanismIds.push_back(mechanismId);
    return 0;
}

int luaStopDoor(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t mechanismId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    pRuntimeState->mechanisms[mechanismId].isMoving = false;
    pRuntimeState->lastAffectedMechanismIds.push_back(mechanismId);
    return 0;
}

int luaSetTexture(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t cogNumber = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));

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

int luaSetLight(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->indoorLightsEnabled[static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))] =
        lua_toboolean(pLuaState, 2) != 0;
    return 0;
}

int luaSetFacetBit(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t faceId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t bit = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isOn = lua_toboolean(pLuaState, 3) != 0;

    if (isOn)
    {
        pRuntimeState->facetSetMasks[faceId] |= bit;
        pRuntimeState->facetClearMasks[faceId] &= ~bit;
    }
    else
    {
        pRuntimeState->facetClearMasks[faceId] |= bit;
        pRuntimeState->facetSetMasks[faceId] &= ~bit;
    }

    markOutdoorSurfaceStateChanged(*pRuntimeState);
    return 0;
}

int luaSetMonsterBit(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t actorId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t bit = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isOn = lua_toboolean(pLuaState, 3) != 0;

    if (isOn)
    {
        pRuntimeState->actorSetMasks[actorId] |= bit;
        pRuntimeState->actorClearMasks[actorId] &= ~bit;
    }
    else
    {
        pRuntimeState->actorClearMasks[actorId] |= bit;
        pRuntimeState->actorSetMasks[actorId] &= ~bit;
    }

    return 0;
}

int luaSetMonGroupBit(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    const uint32_t groupId = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1));
    const uint32_t bit = static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    const bool isOn = lua_toboolean(pLuaState, 3) != 0;

    if (isOn)
    {
        pRuntimeState->actorGroupSetMasks[groupId] |= bit;
        pRuntimeState->actorGroupClearMasks[groupId] &= ~bit;
    }
    else
    {
        pRuntimeState->actorGroupClearMasks[groupId] |= bit;
        pRuntimeState->actorGroupSetMasks[groupId] &= ~bit;
    }

    return 0;
}

int luaSetNpcTopic(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->npcTopicOverrides[static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))]
                                  [static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2))] =
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 3));
    return 0;
}

int luaSetNpcGroupNews(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);
    pRuntimeState->npcGroupNews[static_cast<uint32_t>(luaL_checkinteger(pLuaState, 1))] =
        static_cast<uint32_t>(luaL_checkinteger(pLuaState, 2));
    return 0;
}

int luaSetMessage(lua_State *pLuaState)
{
    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext != nullptr)
    {
        pExecutionContext->pendingMessageText = luaL_checkstring(pLuaState, 1);
    }

    return 0;
}

int luaSimpleMessage(lua_State *pLuaState)
{
    EventRuntimeState *pRuntimeState = writableRuntimeState(pLuaState);

    if (lua_gettop(pLuaState) >= 1 && lua_type(pLuaState, 1) == LUA_TSTRING)
    {
        pRuntimeState->messages.push_back(lua_tostring(pLuaState, 1));
        return 0;
    }

    LuaExecutionContext *pExecutionContext = executionContextFromLua(pLuaState);

    if (pExecutionContext != nullptr && pExecutionContext->pendingMessageText)
    {
        pRuntimeState->messages.push_back(*pExecutionContext->pendingMessageText);
    }

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
    registerLuaFunction(pLuaState, "_RandomJump", luaRandomJump);
    registerLuaFunction(pLuaState, "_InputString", luaInputString);
    registerLuaFunction(pLuaState, "_PressAnyKey", luaPressAnyKey);
    registerLuaFunction(pLuaState, "_SpecialJump", luaSpecialJump);
    registerLuaFunction(pLuaState, "_IsNpcInParty", luaIsNpcInParty);

    registerLuaFunction(pLuaState, "ForPlayer", luaForPlayer);
    registerLuaFunction(pLuaState, "Cmp", luaCompare);
    registerLuaFunction(pLuaState, "EnterHouse", luaEnterHouse);
    registerLuaFunction(pLuaState, "PlaySound", luaPlaySound);
    registerLuaFunction(pLuaState, "MoveToMap", luaMoveToMap);
    registerLuaFunction(pLuaState, "OpenChest", luaOpenChest);
    registerLuaFunction(pLuaState, "FaceExpression", luaFaceExpression);
    registerLuaFunction(pLuaState, "DamagePlayer", luaDamagePlayer);
    registerLuaFunction(pLuaState, "SetSnow", luaSetSnow);
    registerLuaFunction(pLuaState, "SetRain", luaSetRain);
    registerLuaFunction(pLuaState, "SetTexture", luaSetTexture);
    registerLuaFunction(pLuaState, "SetTextureOutdoors", luaSetTexture);
    registerLuaFunction(pLuaState, "ShowMovie", luaShowMovie);
    registerLuaFunction(pLuaState, "SetSprite", luaSetSprite);
    registerLuaFunction(pLuaState, "SetDoorState", luaSetDoorState);
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
    registerLuaFunction(pLuaState, "CheckMonstersKilled", luaCheckMonstersKilled);
    registerLuaFunction(pLuaState, "ChangeGroupToGroup", luaChangeGroupToGroup);
    registerLuaFunction(pLuaState, "ChangeGroupAlly", luaChangeGroupAlly);
    registerLuaFunction(pLuaState, "CheckSeason", luaCheckSeason);
    registerLuaFunction(pLuaState, "SetMonGroupBit", luaSetMonGroupBit);
    registerLuaFunction(pLuaState, "SetChestBit", luaSetChestBit);
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

    return scopeProgram;
}

bool ensureLuaSession(
    const EventRuntime &eventRuntime,
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram)
{
    const ScriptedEventProgram *pLocalProgram = localProgram ? &*localProgram : nullptr;
    const ScriptedEventProgram *pGlobalProgram = globalProgram ? &*globalProgram : nullptr;

    if (eventRuntime.m_luaSessionCache != nullptr
        && eventRuntime.m_pCachedLocalProgram == pLocalProgram
        && eventRuntime.m_pCachedGlobalProgram == pGlobalProgram)
    {
        return true;
    }

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
    eventRuntime.m_luaSessionCache = std::move(session);
    return true;
}

bool invokeLuaHandler(
    const EventRuntime &eventRuntime,
    int handlerReference,
    LuaExecutionContext &executionContext,
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
    std::optional<std::string> errorMessage;
    const bool ok = session.lua.call(0, pBooleanResult != nullptr ? 1 : 0, errorMessage);
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

EventRuntime::EventRuntime() = default;
EventRuntime::~EventRuntime() = default;
EventRuntime::EventRuntime(EventRuntime &&other) noexcept = default;
EventRuntime &EventRuntime::operator=(EventRuntime &&other) noexcept = default;


bool EventRuntime::buildOnLoadState(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    const std::optional<MapDeltaData> &mapDeltaData,
    EventRuntimeState &runtimeState
) const
{
    runtimeState = {};

    if (mapDeltaData)
    {
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

    if (!ensureLuaSession(*this, localProgram, globalProgram))
    {
        return false;
    }

    if (m_luaSessionCache == nullptr)
    {
        return true;
    }

    LuaExecutionContext executionContext = {};
    executionContext.pRuntimeState = &runtimeState;

    for (uint16_t eventId : m_luaSessionCache->globalScope.onLoadEventIds)
    {
        const auto iterator = m_luaSessionCache->globalScope.handlers.find(eventId);

        if (iterator == m_luaSessionCache->globalScope.handlers.end())
        {
            continue;
        }

        if (invokeLuaHandler(*this, iterator->second, executionContext))
        {
            ++runtimeState.globalOnLoadEventsExecuted;
        }
    }

    for (uint16_t eventId : m_luaSessionCache->localScope.onLoadEventIds)
    {
        const auto iterator = m_luaSessionCache->localScope.handlers.find(eventId);

        if (iterator == m_luaSessionCache->localScope.handlers.end())
        {
            continue;
        }

        if (invokeLuaHandler(*this, iterator->second, executionContext))
        {
            ++runtimeState.localOnLoadEventsExecuted;
        }
    }

    return true;
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

bool EventRuntime::executeEventById(
    const std::optional<ScriptedEventProgram> &localProgram,
    const std::optional<ScriptedEventProgram> &globalProgram,
    uint16_t eventId,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext
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
    executionContext.pRuntimeState = &runtimeState;
    executionContext.pParty = pParty;
    executionContext.pSceneEventContext = pSceneEventContext;

    const auto localIterator = m_luaSessionCache->localScope.handlers.find(eventId);

    if (localIterator != m_luaSessionCache->localScope.handlers.end())
    {
        return invokeLuaHandler(*this, localIterator->second, executionContext);
    }

    const auto globalIterator = m_luaSessionCache->globalScope.handlers.find(eventId);

    if (globalIterator != m_luaSessionCache->globalScope.handlers.end())
    {
        return invokeLuaHandler(*this, globalIterator->second, executionContext);
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
    executionContext.pReadonlyRuntimeState = &runtimeState;
    executionContext.pReadonlyParty = pParty;
    executionContext.pReadonlySceneEventContext = pSceneEventContext;
    executionContext.readonly = true;
    std::optional<bool> visible = std::nullopt;

    if (!invokeLuaHandler(*this, iterator->second, executionContext, &visible))
    {
        return false;
    }

    return visible.value_or(true);
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

        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
        {
            const float closedDistance = runtimeMechanism.timeSinceTriggeredMs * float(door.closeSpeed) / 1000.0f;

            if (closedDistance >= float(door.moveLength))
            {
                runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closed);
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = static_cast<float>(door.moveLength);
                runtimeMechanism.isMoving = false;
            }
        }
        else if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
        {
            const float openedDistance = runtimeMechanism.timeSinceTriggeredMs * float(door.openSpeed) / 1000.0f;

            if (openedDistance >= float(door.moveLength))
            {
                runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = 0.0f;
                runtimeMechanism.isMoving = false;
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
    const std::vector<size_t> &targetMemberIndices
)
{
    const EventRuntime::VariableRef variable = EventRuntime::decodeVariable(rawVariableId);
    const EvtVariable variableId = static_cast<EvtVariable>(variable.tag);
    const std::optional<size_t> memberIndex = singleTargetMemberIndex(targetMemberIndices);
    const int32_t currentValue = EventRuntime::getVariableValue(runtimeState, variable, pParty, memberIndex);

    if (variable.kind == EventRuntime::VariableKind::ClassId)
    {
        if (targetMemberIndices.empty())
        {
            return currentValue == compareValue;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            if (EventRuntime::getVariableValue(runtimeState, variable, pParty, targetMemberIndex) == compareValue)
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
