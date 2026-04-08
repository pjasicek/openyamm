#include "game/events/ISceneEventContext.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"

#include <iostream>
#include <algorithm>
#include <cmath>
#include <limits>
#include <unordered_map>

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
std::optional<std::string> skillNameForEvtVariable(EvtVariable variableId);

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

float mechanismDistanceForState(const MapDeltaDoor &door, uint16_t state, float timeSinceTriggeredMs)
{
    if (state == static_cast<uint16_t>(EvtMechanismState::Closed))
    {
        return 0.0f;
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Open) || (door.attributes & 0x2) != 0)
    {
        return static_cast<float>(door.moveLength);
    }

    const float elapsedMilliseconds = static_cast<float>(timeSinceTriggeredMs);

    if (state == static_cast<uint16_t>(EvtMechanismState::Closing))
    {
        const float openDistance = elapsedMilliseconds * static_cast<float>(door.openSpeed) / 1000.0f;
        return std::max(0.0f, static_cast<float>(door.moveLength) - openDistance);
    }

    if (state == static_cast<uint16_t>(EvtMechanismState::Opening))
    {
        const float closeDistance = elapsedMilliseconds * static_cast<float>(door.closeSpeed) / 1000.0f;
        return std::min(closeDistance, static_cast<float>(door.moveLength));
    }

    return 0.0f;
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

PartySelector decodePartySelector(const EventIrInstruction &instruction)
{
    if (instruction.operation != EventIrOperation::ForPartyMember || instruction.arguments.empty())
    {
        return {};
    }

    const uint32_t selectorValue = instruction.arguments[0];

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

bool grantInventoryItemToTargets(Party &party, const std::vector<size_t> &targetMemberIndices, uint32_t objectDescriptionId)
{
    for (size_t memberIndex : targetMemberIndices)
    {
        if (party.grantItemToMember(memberIndex, objectDescriptionId))
        {
            return true;
        }
    }

    return false;
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

uint32_t randomJumpSeed(const EventIrInstruction &instruction, const EventRuntimeState &runtimeState)
{
    return static_cast<uint32_t>(instruction.eventId) * 2654435761u
        ^ static_cast<uint32_t>(instruction.step) * 40503u
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
        if (pParty != nullptr && !targetMemberIndices.empty())
        {
            if (value != 0)
            {
                grantInventoryItemToTargets(*pParty, targetMemberIndices, variable.rawId);
            }
            else
            {
                removeInventoryItemFromTargets(*pParty, targetMemberIndices, variable.rawId);
            }
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
        runtimeState.variables[variable.rawId] = value != 0 ? 1 : 0;

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
        if (pParty != nullptr && !targetMemberIndices.empty())
        {
            if (value > 0)
            {
                grantInventoryItemToTargets(*pParty, targetMemberIndices, static_cast<uint32_t>(value));
            }
            return;
        }

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

        if (pParty != nullptr)
        {
            pParty->addEventVariableValue(variable.tag, value);
            return;
        }
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        runtimeState.variables[variable.rawId] = value != 0 ? 1 : 0;

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

        if (pParty != nullptr)
        {
            pParty->subtractEventVariableValue(variable.tag, value);
            return;
        }
    }

    if (variable.kind == VariableKind::QBits || variable.kind == VariableKind::BoolFlag)
    {
        runtimeState.variables[variable.rawId] = 0;
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

bool EventRuntime::buildOnLoadState(
    const std::optional<EventIrProgram> &localProgram,
    const std::optional<EventIrProgram> &globalProgram,
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
            runtimeMechanism.state = door.state;
            runtimeMechanism.timeSinceTriggeredMs = float(door.timeSinceTriggered);
            runtimeMechanism.currentDistance =
                mechanismDistanceForState(door, runtimeMechanism.state, runtimeMechanism.timeSinceTriggeredMs);
            runtimeMechanism.isMoving =
                door.state == static_cast<uint16_t>(EvtMechanismState::Opening)
                || door.state == static_cast<uint16_t>(EvtMechanismState::Closing);
            runtimeState.mechanisms[door.doorId] = runtimeMechanism;
        }

        for (size_t mapVarIndex = 0; mapVarIndex < mapDeltaData->eventVariables.mapVars.size(); ++mapVarIndex)
        {
            runtimeState.mapVars[mapVarIndex] = mapDeltaData->eventVariables.mapVars[mapVarIndex];
        }
    }

    if (globalProgram)
    {
        executeProgramOnLoad(*globalProgram, runtimeState, runtimeState.globalOnLoadEventsExecuted);
    }

    if (localProgram)
    {
        executeProgramOnLoad(*localProgram, runtimeState, runtimeState.localOnLoadEventsExecuted);
    }

    return true;
}

bool EventRuntime::executeEventById(
    const std::optional<EventIrProgram> &localProgram,
    const std::optional<EventIrProgram> &globalProgram,
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

    if (localProgram)
    {
        const EventIrEvent *pEvent = findEventById(*localProgram, eventId);

        if (pEvent != nullptr)
        {
            return executeEvent(*pEvent, runtimeState, pParty, pSceneEventContext);
        }
    }

    if (globalProgram)
    {
        const EventIrEvent *pEvent = findEventById(*globalProgram, eventId);

        if (pEvent != nullptr)
        {
            return executeEvent(*pEvent, runtimeState, pParty, pSceneEventContext);
        }
    }

    return false;
}

bool EventRuntime::canShowTopic(
    const std::optional<EventIrProgram> &globalProgram,
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

    const EventIrEvent *pEvent = findEventById(*globalProgram, topicId);
    return pEvent == nullptr ? true : evaluateCanShowTopic(*pEvent, runtimeState, pParty, pSceneEventContext);
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
            const float openedDistance = runtimeMechanism.timeSinceTriggeredMs * float(door.openSpeed) / 1000.0f;

            if (openedDistance >= float(door.moveLength))
            {
                runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closed);
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = 0.0f;
                runtimeMechanism.isMoving = false;
            }
        }
        else if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
        {
            const float closedDistance = runtimeMechanism.timeSinceTriggeredMs * float(door.closeSpeed) / 1000.0f;

            if (closedDistance >= float(door.moveLength))
            {
                runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Open);
                runtimeMechanism.timeSinceTriggeredMs = 0.0f;
                runtimeMechanism.currentDistance = static_cast<float>(door.moveLength);
                runtimeMechanism.isMoving = false;
            }
        }
        else
        {
            runtimeMechanism.isMoving = false;
        }
    }
}

void EventRuntime::executeProgramOnLoad(
    const EventIrProgram &program,
    EventRuntimeState &runtimeState,
    size_t &executedCount
)
{
    for (const EventIrEvent &event : program.getEvents())
    {
        bool hasOnLoadTrigger = false;

        for (const EventIrInstruction &instruction : event.instructions)
        {
            if (instruction.operation == EventIrOperation::TriggerOnLoadMap)
            {
                hasOnLoadTrigger = true;
                break;
            }
        }

        if (!hasOnLoadTrigger)
        {
            continue;
        }

        if (executeEvent(event, runtimeState, nullptr, nullptr))
        {
            ++executedCount;
        }
    }
}

const EventIrEvent *EventRuntime::findEventById(const EventIrProgram &program, uint16_t eventId)
{
    for (const EventIrEvent &event : program.getEvents())
    {
        if (event.eventId == eventId)
        {
            return &event;
        }
    }

    return nullptr;
}

void EventRuntime::executeTimerEvents(const EventIrProgram &program, EventRuntimeState &runtimeState)
{
    for (const EventIrEvent &event : program.getEvents())
    {
        bool hasTimerTrigger = false;

        for (const EventIrInstruction &instruction : event.instructions)
        {
            if (instruction.operation == EventIrOperation::TriggerOnTimer)
            {
                hasTimerTrigger = true;
                break;
            }
        }

        if (!hasTimerTrigger)
        {
            continue;
        }

        std::cout << "Executing timer event " << event.eventId << '\n';
        executeEvent(event, runtimeState, nullptr, nullptr);
    }
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

        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Open))
        {
            runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closing);
        }
        else
        {
            runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Opening);
        }

        runtimeMechanism.isMoving = true;
        return;
    }

    if (action == MechanismAction::Open)
    {
        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closed)
            || runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Closing))
        {
            return;
        }

        runtimeMechanism.timeSinceTriggeredMs = 0.0f;
        runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Closing);
        runtimeMechanism.isMoving = true;
        return;
    }

    if (action == MechanismAction::Close)
    {
        if (runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Open)
            || runtimeMechanism.state == static_cast<uint16_t>(EvtMechanismState::Opening))
        {
            return;
        }

        runtimeMechanism.timeSinceTriggeredMs = 0.0f;
        runtimeMechanism.state = static_cast<uint16_t>(EvtMechanismState::Opening);
        runtimeMechanism.isMoving = true;
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

bool EventRuntime::evaluateCompare(
    const EventRuntimeState &runtimeState,
    const EventIrInstruction &instruction,
    const Party *pParty,
    const std::vector<size_t> &targetMemberIndices
)
{
    if (instruction.arguments.size() < 2)
    {
        return false;
    }

    const VariableRef variable = decodeVariable(instruction.arguments[0]);
    const EvtVariable variableId = static_cast<EvtVariable>(variable.tag);
    const int32_t compareValue = static_cast<int32_t>(instruction.arguments[1]);
    const std::optional<size_t> memberIndex = singleTargetMemberIndex(targetMemberIndices);
    const int32_t currentValue = getVariableValue(runtimeState, variable, pParty, memberIndex);

    if (variable.kind == VariableKind::ClassId)
    {
        if (targetMemberIndices.empty())
        {
            return currentValue == compareValue;
        }

        for (size_t targetMemberIndex : targetMemberIndices)
        {
            if (getVariableValue(runtimeState, variable, pParty, targetMemberIndex) == compareValue)
            {
                return true;
            }
        }

        return false;
    }

    if (variable.kind == VariableKind::Awards || variable.kind == VariableKind::Players)
    {
        return currentValue != 0;
    }

    if (variable.kind == VariableKind::AutoNote
        || variable.kind == VariableKind::History
        || variable.kind == VariableKind::QBits
        || variable.kind == VariableKind::BoolFlag
        || variable.kind == VariableKind::Condition
        || variable.kind == VariableKind::StatMoreThanBase)
    {
        return currentValue != 0;
    }

    if (variable.kind == VariableKind::Inventory)
    {
        return currentValue != 0;
    }

    if (variable.kind == VariableKind::DayOfWeek
        || variable.kind == VariableKind::DayOfYear
        || variable.kind == VariableKind::Hour)
    {
        return currentValue == compareValue;
    }

    if ((variable.kind == VariableKind::MaxHealth || variable.kind == VariableKind::MaxSpellPoints) && memberIndex)
    {
        const Character *pMember = pParty != nullptr ? pParty->member(*memberIndex) : nullptr;

        if (pMember == nullptr)
        {
            return false;
        }

        if (variable.kind == VariableKind::MaxHealth)
        {
            return pMember->health >= resolveCharacterEffectiveMaxHealth(*pMember);
        }

        return pMember->spellPoints >= resolveCharacterEffectiveMaxSpellPoints(*pMember);
    }

    if (variable.kind == VariableKind::PartyState)
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

bool EventRuntime::evaluateCanShowTopic(
    const EventIrEvent &event,
    const EventRuntimeState &runtimeState,
    const Party *pParty,
    const ISceneEventContext *pSceneEventContext
)
{
    std::unordered_map<uint8_t, size_t> stepToInstructionIndex;

    for (size_t instructionIndex = 0; instructionIndex < event.instructions.size(); ++instructionIndex)
    {
        stepToInstructionIndex[event.instructions[instructionIndex].step] = instructionIndex;
    }

    bool sawCanShowInstruction = false;
    bool isVisible = true;
    size_t instructionIndex = 0;
    PartySelector selector = {};

    while (instructionIndex < event.instructions.size())
    {
        const EventIrInstruction &instruction = event.instructions[instructionIndex];
        const std::vector<size_t> targetMemberIndices = resolveTargetMemberIndices(selector, pParty);

        switch (instruction.operation)
        {
            case EventIrOperation::ForPartyMember:
                selector = decodePartySelector(instruction);
                break;

            case EventIrOperation::CompareCanShowTopic:
            {
                sawCanShowInstruction = true;
                const bool compareSucceeded = evaluateCompare(runtimeState, instruction, pParty, targetMemberIndices);

                if (compareSucceeded && instruction.jumpTargetStep)
                {
                    const std::unordered_map<uint8_t, size_t>::const_iterator iterator =
                        stepToInstructionIndex.find(*instruction.jumpTargetStep);

                    if (iterator != stepToInstructionIndex.end())
                    {
                        instructionIndex = iterator->second;
                        continue;
                    }
                }
                break;
            }

            case EventIrOperation::IsActorKilledCanShowTopic:
            {
                sawCanShowInstruction = true;
                if (instruction.arguments.size() >= 4 && pSceneEventContext != nullptr)
                {
                    const uint32_t checkType = instruction.arguments[0];
                    const uint32_t id = instruction.arguments[1];
                    const uint32_t count = instruction.arguments[2];
                    const bool invisibleAsDead = instruction.arguments[3] != 0;
                    const bool killed =
                        pSceneEventContext->checkMonstersKilled(checkType, id, count, invisibleAsDead);

                    if (killed && instruction.jumpTargetStep)
                    {
                        const std::unordered_map<uint8_t, size_t>::const_iterator iterator =
                            stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::SetCanShowTopic:
                sawCanShowInstruction = true;
                isVisible = !instruction.arguments.empty() && instruction.arguments[0] != 0;
                break;

            case EventIrOperation::EndCanShowTopic:
                return isVisible;

            default:
                return sawCanShowInstruction ? isVisible : true;
        }

        ++instructionIndex;
    }

    return sawCanShowInstruction ? isVisible : true;
}

bool EventRuntime::executeEvent(
    const EventIrEvent &event,
    EventRuntimeState &runtimeState,
    Party *pParty,
    ISceneEventContext *pSceneEventContext
)
{
    runtimeState.lastAffectedMechanismIds.clear();
    runtimeState.openedChestIds.clear();
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

    std::unordered_map<uint8_t, size_t> stepToInstructionIndex;

    for (size_t instructionIndex = 0; instructionIndex < event.instructions.size(); ++instructionIndex)
    {
        stepToInstructionIndex[event.instructions[instructionIndex].step] = instructionIndex;
    }

    size_t instructionIndex = 0;
    PartySelector selector = {};

    while (instructionIndex < event.instructions.size())
    {
        const EventIrInstruction &instruction = event.instructions[instructionIndex];
        const std::vector<size_t> targetMemberIndices = resolveTargetMemberIndices(selector, pParty);

        switch (instruction.operation)
        {
            case EventIrOperation::Exit:
                return true;

            case EventIrOperation::TriggerMouseOver:
            case EventIrOperation::TriggerOnLoadMap:
            case EventIrOperation::TriggerOnLeaveMap:
            case EventIrOperation::TriggerOnTimer:
            case EventIrOperation::TriggerOnLongTimer:
            case EventIrOperation::TriggerOnDateTimer:
            case EventIrOperation::EnableDateTimer:
            case EventIrOperation::CompareCanShowTopic:
            case EventIrOperation::SetCanShowTopic:
            case EventIrOperation::EndCanShowTopic:
            case EventIrOperation::LocationName:
                break;

            case EventIrOperation::ForPartyMember:
                selector = decodePartySelector(instruction);
                std::cout << "  player_selector="
                          << (instruction.arguments.empty() ? 0 : instruction.arguments[0]) << '\n';
                break;

            case EventIrOperation::PlaySound:
            {
                if (instruction.arguments.size() >= 3)
                {
                    const uint32_t soundId = instruction.arguments[0];
                    const int32_t x = static_cast<int32_t>(instruction.arguments[1]);
                    const int32_t y = static_cast<int32_t>(instruction.arguments[2]);
                    const bool positional = x != 0 || y != 0;
                    queuePendingSound(runtimeState, soundId, x, y, positional);
                    std::cout << "  play_sound id=" << soundId
                              << " x=" << x
                              << " y=" << y
                              << " positional=" << (positional ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::MoveNpc:
            {
                if (instruction.arguments.size() >= 2)
                {
                    runtimeState.npcHouseOverrides[instruction.arguments[0]] = instruction.arguments[1];
                    std::cout << "  move_npc npc=" << instruction.arguments[0]
                              << " house=" << instruction.arguments[1] << '\n';
                }
                break;
            }

            case EventIrOperation::RandomJump:
            {
                std::vector<uint32_t> validTargets;
                validTargets.reserve(instruction.arguments.size());

                for (uint32_t target : instruction.arguments)
                {
                    if (target != 0)
                    {
                        validTargets.push_back(target);
                    }
                }

                if (!validTargets.empty())
                {
                    const uint32_t seed = randomJumpSeed(instruction, runtimeState);
                    const size_t choiceIndex = seed % validTargets.size();
                    const uint8_t targetStep = static_cast<uint8_t>(validTargets[choiceIndex] & 0xffu);
                    std::cout << "  random_jump seed=" << seed
                              << " choice=" << choiceIndex
                              << " -> " << static_cast<unsigned>(targetStep) << '\n';

                    if (targetStep == 0)
                    {
                        break;
                    }

                    const auto iterator = stepToInstructionIndex.find(targetStep);

                    if (iterator != stepToInstructionIndex.end())
                    {
                        instructionIndex = iterator->second;
                        continue;
                    }
                }
                break;
            }

            case EventIrOperation::SummonItem:
            {
                if (instruction.arguments.size() >= 7)
                {
                    const uint32_t objectId = instruction.arguments[0];
                    const int32_t x = static_cast<int32_t>(instruction.arguments[1]);
                    const int32_t y = static_cast<int32_t>(instruction.arguments[2]);
                    const int32_t z = static_cast<int32_t>(instruction.arguments[3]);
                    const int32_t speed = static_cast<int32_t>(instruction.arguments[4]);
                    const uint32_t count = instruction.arguments[5];
                    const bool randomRotate = instruction.arguments[6] != 0;
                    const bool summoned =
                        pSceneEventContext != nullptr
                        && pSceneEventContext->summonEventItem(objectId, x, y, z, speed, count, randomRotate);

                    std::cout << "  summon_item object=" << objectId
                              << " pos=(" << x << "," << y << "," << z << ")"
                              << " speed=" << speed
                              << " count=" << count
                              << " random_rotate=" << (randomRotate ? "1" : "0")
                              << " -> " << (summoned ? "true" : "false") << '\n';
                }
                break;
            }

            case EventIrOperation::ShowFace:
            {
                if (instruction.arguments.size() >= 2 && pParty != nullptr)
                {
                    const std::optional<PortraitId> portraitId = eventPortraitId(instruction.arguments[1]);

                    if (!portraitId)
                    {
                        break;
                    }

                    for (size_t memberIndex : targetMemberIndices)
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

                    std::cout << "  show_face portrait=" << instruction.arguments[1] << '\n';
                }
                break;
            }

            case EventIrOperation::ReceiveDamage:
            {
                if (instruction.arguments.size() >= 3 && pParty != nullptr)
                {
                    const int damage = static_cast<int>(instruction.arguments[2]);
                    const std::string status = damageStatusForEvtVariable(targetMemberIndices);

                    for (size_t memberIndex : targetMemberIndices)
                    {
                        pParty->applyDamageToMember(memberIndex, damage, status);
                    }

                    std::cout << "  receive_damage type=" << instruction.arguments[1]
                              << " damage=" << damage
                              << " targets=" << targetMemberIndices.size() << '\n';
                }
                break;
            }

            case EventIrOperation::SetSnow:
            {
                if (instruction.arguments.size() >= 2 && instruction.arguments[0] == 0)
                {
                    runtimeState.snowEnabled = instruction.arguments[1] != 0;
                    std::cout << "  set_snow enabled=" << (*runtimeState.snowEnabled ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::ShowMovie:
            {
                if (instruction.text && !instruction.text->empty())
                {
                    EventRuntimeState::PendingMovie movie = {};
                    movie.movieName = sanitizeEventString(*instruction.text);
                    movie.restoreAfterPlayback = !instruction.arguments.empty() && instruction.arguments[0] != 0;
                    runtimeState.pendingMovie = std::move(movie);
                    std::cout << "  show_movie name=\"" << *instruction.text << "\"\n";
                }
                break;
            }

            case EventIrOperation::SetSprite:
            {
                if (!instruction.arguments.empty())
                {
                    EventRuntimeState::SpriteOverride override = {};
                    override.hidden = instruction.arguments.size() >= 2 && instruction.arguments[1] != 0;

                    if (instruction.text && !instruction.text->empty())
                    {
                        override.textureName = sanitizeEventString(*instruction.text);
                    }

                    runtimeState.spriteOverrides[instruction.arguments[0]] = std::move(override);
                    std::cout << "  set_sprite cog=" << instruction.arguments[0]
                              << " hidden="
                              << (runtimeState.spriteOverrides[instruction.arguments[0]].hidden ? "1" : "0")
                              << '\n';
                }
                break;
            }

            case EventIrOperation::SpeakInHouse:
            {
                if (!instruction.arguments.empty())
                {
                    runtimeState.messages.clear();
                    EventRuntimeState::PendingDialogueContext context = {};
                    context.kind = DialogueContextKind::HouseService;
                    context.sourceId = instruction.arguments[0];
                    context.hostHouseId = instruction.arguments[0];
                    runtimeState.dialogueState.hostHouseId = instruction.arguments[0];
                    runtimeState.pendingDialogueContext = std::move(context);
                    std::cout << "  house=" << instruction.arguments[0];

                    if (instruction.text && !instruction.text->empty())
                    {
                        std::cout << " name=\"" << *instruction.text << "\"";
                    }

                    std::cout << '\n';
                }
                break;
            }

            case EventIrOperation::SpeakNpc:
            {
                if (!instruction.arguments.empty())
                {
                    runtimeState.messages.clear();
                    EventRuntimeState::PendingDialogueContext context = {};
                    context.kind = DialogueContextKind::NpcTalk;
                    context.sourceId = instruction.arguments[0];
                    context.hostHouseId = runtimeState.dialogueState.hostHouseId;
                    runtimeState.pendingDialogueContext = std::move(context);
                    std::cout << "  npc=" << instruction.arguments[0] << '\n';
                }
                break;
            }

            case EventIrOperation::MoveToMap:
            {
                if (instruction.arguments.size() >= 3)
                {
                    EventRuntimeState::PendingMapMove pendingMapMove = {};
                    pendingMapMove.x = static_cast<int32_t>(instruction.arguments[0]);
                    pendingMapMove.y = static_cast<int32_t>(instruction.arguments[1]);
                    pendingMapMove.z = static_cast<int32_t>(instruction.arguments[2]);

                    if (instruction.arguments.size() >= 4)
                    {
                        pendingMapMove.directionDegrees = static_cast<int32_t>(instruction.arguments[3]);
                    }

                    if (instruction.text && !instruction.text->empty())
                    {
                        const std::string sanitizedName = sanitizeEventString(*instruction.text);

                        if (!sanitizedName.empty())
                        {
                            pendingMapMove.mapName = sanitizedName;
                        }
                    }

                    runtimeState.pendingMapMove = pendingMapMove;
                    std::cout << "  move_to_map=("
                              << pendingMapMove.x << ","
                              << pendingMapMove.y << ","
                              << pendingMapMove.z << ")";

                    if (pendingMapMove.directionDegrees)
                    {
                        std::cout << " yaw=" << *pendingMapMove.directionDegrees;
                    }

                    if (pendingMapMove.mapName && !pendingMapMove.mapName->empty())
                    {
                        std::cout << " name=\"" << *pendingMapMove.mapName << "\"";
                    }

                    std::cout << '\n';
                }
                break;
            }

            case EventIrOperation::CastSpell:
            {
                if (instruction.arguments.size() >= 9)
                {
                    const uint32_t spellId = instruction.arguments[0];
                    const uint32_t skillLevel = instruction.arguments[1];
                    const uint32_t skillMastery = instruction.arguments[2];
                    const int32_t fromX = static_cast<int32_t>(instruction.arguments[3]);
                    const int32_t fromY = static_cast<int32_t>(instruction.arguments[4]);
                    const int32_t fromZ = static_cast<int32_t>(instruction.arguments[5]);
                    const int32_t toX = static_cast<int32_t>(instruction.arguments[6]);
                    const int32_t toY = static_cast<int32_t>(instruction.arguments[7]);
                    const int32_t toZ = static_cast<int32_t>(instruction.arguments[8]);
                    const bool casted =
                        pSceneEventContext != nullptr
                        && pSceneEventContext->castEventSpell(
                            spellId,
                            skillLevel,
                            skillMastery,
                            fromX,
                            fromY,
                            fromZ,
                            toX,
                            toY,
                            toZ);

                    std::cout << "  cast_spell spell=" << spellId
                              << " skill=" << skillLevel
                              << " mastery=" << skillMastery
                              << " from=(" << fromX << "," << fromY << "," << fromZ << ")"
                              << " to=(" << toX << "," << toY << "," << toZ << ")"
                              << " -> " << (casted ? "true" : "false") << '\n';
                }
                break;
            }

            case EventIrOperation::CheckItemsCount:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const uint32_t itemId = instruction.arguments[0];
                    const int32_t requiredCount = static_cast<int32_t>(instruction.arguments[1]);
                    const int32_t currentCount = getInventoryItemCount(
                        runtimeState,
                        pParty,
                        itemId,
                        singleTargetMemberIndex(targetMemberIndices));
                    const bool hasEnough = currentCount >= requiredCount;

                    std::cout << "  check_items item=" << itemId
                              << " count=" << requiredCount
                              << " current=" << currentCount
                              << " -> " << (hasEnough ? "true" : "false") << '\n';

                    if (hasEnough && instruction.jumpTargetStep)
                    {
                        const auto iterator = stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::CheckSkill:
            {
                if (instruction.arguments.size() >= 3 && pParty != nullptr)
                {
                    const EvtVariable skillVariable = static_cast<EvtVariable>(instruction.arguments[0]);
                    const SkillMastery requiredMastery = static_cast<SkillMastery>(instruction.arguments[1]);
                    const uint32_t requiredLevel = instruction.arguments[2];
                    bool passed = false;

                    for (size_t memberIndex : targetMemberIndices)
                    {
                        const Character *pMember = pParty->member(memberIndex);

                        if (pMember != nullptr
                            && characterMeetsSkillCheck(*pMember, skillVariable, requiredMastery, requiredLevel))
                        {
                            passed = true;
                            break;
                        }
                    }

                    std::cout << "  check_skill var=" << instruction.arguments[0]
                              << " mastery=" << instruction.arguments[1]
                              << " level=" << requiredLevel
                              << " -> " << (passed ? "true" : "false") << '\n';

                    if (passed && instruction.jumpTargetStep)
                    {
                        const auto iterator = stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::SetActorGroup:
            {
                if (instruction.arguments.size() >= 2)
                {
                    runtimeState.actorIdGroupOverrides[instruction.arguments[0]] = instruction.arguments[1];
                    std::cout << "  set_actor_group actor=" << instruction.arguments[0]
                              << " group=" << instruction.arguments[1] << '\n';
                }
                break;
            }

            case EventIrOperation::SetNpcGreeting:
            {
                if (instruction.arguments.size() >= 2)
                {
                    runtimeState.npcGreetingOverrides[instruction.arguments[0]] = instruction.arguments[1];
                    runtimeState.npcGreetingDisplayCounts[instruction.arguments[0]] = 0;
                    std::cout << "  set_npc_greeting npc=" << instruction.arguments[0]
                              << " greeting=" << instruction.arguments[1] << '\n';
                }
                break;
            }

            case EventIrOperation::SetNpcItem:
            {
                if (instruction.arguments.size() >= 2)
                {
                    runtimeState.npcItemOverrides[instruction.arguments[0]] =
                        instruction.arguments.size() >= 3 && instruction.arguments[2] == 0 ? 0 : instruction.arguments[1];
                    std::cout << "  set_npc_item npc=" << instruction.arguments[0]
                              << " item=" << instruction.arguments[1] << '\n';
                }
                break;
            }

            case EventIrOperation::SetActorItem:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const uint32_t actorId = instruction.arguments[0];
                    const uint32_t itemId = instruction.arguments[1];
                    const bool isGive = instruction.arguments.size() < 3 || instruction.arguments[2] != 0;

                    if (isGive && itemId != 0)
                    {
                        runtimeState.actorItemOverrides[actorId] = itemId;
                        runtimeState.actorSetMasks[actorId] |= static_cast<uint32_t>(EvtActorAttribute::HasItem);
                        runtimeState.actorClearMasks[actorId] &= ~static_cast<uint32_t>(EvtActorAttribute::HasItem);
                    }
                    else
                    {
                        runtimeState.actorItemOverrides.erase(actorId);
                        runtimeState.actorClearMasks[actorId] |= static_cast<uint32_t>(EvtActorAttribute::HasItem);
                        runtimeState.actorSetMasks[actorId] &= ~static_cast<uint32_t>(EvtActorAttribute::HasItem);
                    }

                    std::cout << "  set_actor_item actor=" << actorId
                              << " item=" << itemId
                              << " give=" << (isGive ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::CharacterAnimation:
            {
                if (instruction.arguments.size() >= 2 && pParty != nullptr)
                {
                    const SpeechId speechId = static_cast<SpeechId>(instruction.arguments[1]);

                    for (size_t memberIndex : targetMemberIndices)
                    {
                        pParty->requestSpeech(memberIndex, speechId);
                    }

                    std::cout << "  character_animation speech=" << instruction.arguments[1]
                              << " targets=" << targetMemberIndices.size() << '\n';
                }
                break;
            }

            case EventIrOperation::IsActorKilledCanShowTopic:
                break;

            case EventIrOperation::ChangeGroup:
            {
                if (instruction.arguments.size() >= 2)
                {
                    runtimeState.actorGroupOverrides[instruction.arguments[0]] = instruction.arguments[1];
                    std::cout << "  change_group old=" << instruction.arguments[0]
                              << " new=" << instruction.arguments[1] << '\n';
                }
                break;
            }

            case EventIrOperation::ChangeGroupAlly:
            {
                if (instruction.arguments.size() >= 2)
                {
                    runtimeState.actorGroupAllyOverrides[instruction.arguments[0]] = instruction.arguments[1];
                    std::cout << "  change_group_ally group=" << instruction.arguments[0]
                              << " ally=" << instruction.arguments[1] << '\n';
                }
                break;
            }

            case EventIrOperation::CheckSeason:
            {
                if (!instruction.arguments.empty())
                {
                    const bool matches = currentSeasonFromRuntimeState(runtimeState)
                        == static_cast<EvtSeason>(instruction.arguments[0]);

                    std::cout << "  check_season season=" << instruction.arguments[0]
                              << " -> " << (matches ? "true" : "false") << '\n';

                    if (matches && instruction.jumpTargetStep)
                    {
                        const auto iterator = stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::ToggleChestFlag:
            {
                if (instruction.arguments.size() >= 3)
                {
                    const uint32_t chestId = instruction.arguments[0];
                    const uint32_t flag = instruction.arguments[1];
                    const bool isOn = instruction.arguments[2] != 0;

                    if (isOn)
                    {
                        runtimeState.chestSetMasks[chestId] |= flag;
                        runtimeState.chestClearMasks[chestId] &= ~flag;
                    }
                    else
                    {
                        runtimeState.chestClearMasks[chestId] |= flag;
                        runtimeState.chestSetMasks[chestId] &= ~flag;
                    }

                    if ((flag & static_cast<uint32_t>(EvtChestFlag::Opened)) != 0 && isOn)
                    {
                        runtimeState.openedChestIds.push_back(chestId);
                    }

                    std::cout << "  toggle_chest_flag chest=" << chestId
                              << " flag=0x" << std::hex << flag << std::dec
                              << " on=" << (isOn ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::InputString:
            {
                EventRuntimeState::PendingInputPrompt prompt = {};
                prompt.kind = EventRuntimeState::PendingInputPrompt::Kind::InputString;
                prompt.eventId = event.eventId;
                prompt.continueStep = instruction.step + 1;
                prompt.textId = !instruction.arguments.empty() ? instruction.arguments[0] : 0;
                prompt.text = instruction.text;
                runtimeState.pendingInputPrompt = std::move(prompt);
                std::cout << "  input_string text=" << (!instruction.arguments.empty() ? instruction.arguments[0] : 0) << '\n';
                return true;
            }

            case EventIrOperation::PressAnyKey:
            {
                EventRuntimeState::PendingInputPrompt prompt = {};
                prompt.kind = EventRuntimeState::PendingInputPrompt::Kind::PressAnyKey;
                prompt.eventId = event.eventId;
                prompt.continueStep = instruction.step + 1;
                runtimeState.pendingInputPrompt = std::move(prompt);
                std::cout << "  press_any_key\n";
                return true;
            }

            case EventIrOperation::SpecialJump:
                std::cout << "  special_jump a="
                          << (instruction.arguments.empty() ? 0 : instruction.arguments[0])
                          << " b=" << (instruction.arguments.size() >= 2 ? instruction.arguments[1] : 0) << '\n';
                break;

            case EventIrOperation::IsTotalBountyHuntingAwardInRange:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const int32_t totalBounty =
                        pParty != nullptr
                            ? pParty->eventVariableValue(static_cast<uint16_t>(EvtVariable::NumBounties))
                            : 0;
                    const int32_t minValue = static_cast<int32_t>(instruction.arguments[0]);
                    const int32_t maxValue = static_cast<int32_t>(instruction.arguments[1]);
                    const bool inRange = totalBounty >= minValue && totalBounty <= maxValue;

                    std::cout << "  check_bounty total=" << totalBounty
                              << " range=[" << minValue << "," << maxValue << "]"
                              << " -> " << (inRange ? "true" : "false") << '\n';

                    if (inRange && instruction.jumpTargetStep)
                    {
                        const auto iterator = stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::IsNpcInParty:
            {
                if (!instruction.arguments.empty())
                {
                    const bool inParty = runtimeState.unavailableNpcIds.contains(instruction.arguments[0]);

                    std::cout << "  is_npc_in_party npc=" << instruction.arguments[0]
                              << " -> " << (inParty ? "true" : "false") << '\n';

                    if (inParty && instruction.jumpTargetStep)
                    {
                        const auto iterator = stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::Compare:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    const int32_t compareValue = static_cast<int32_t>(instruction.arguments[1]);
                    const std::optional<size_t> memberIndex = singleTargetMemberIndex(targetMemberIndices);
                    const int32_t currentValue = getVariableValue(runtimeState, variable, pParty, memberIndex);
                    const bool compareSucceeded = evaluateCompare(runtimeState, instruction, pParty, targetMemberIndices);

                    std::cout << "  cmp raw=" << instruction.arguments[0]
                              << " current=" << currentValue
                              << " expect=" << compareValue
                              << " -> " << (compareSucceeded ? "true" : "false") << '\n';

                    if (compareSucceeded && instruction.jumpTargetStep)
                    {
                        const std::unordered_map<uint8_t, size_t>::const_iterator iterator =
                            stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::Jump:
            {
                std::cout << "  jump -> "
                          << (instruction.jumpTargetStep ? std::to_string(*instruction.jumpTargetStep) : "-")
                          << '\n';

                if (instruction.jumpTargetStep)
                {
                    const std::unordered_map<uint8_t, size_t>::const_iterator iterator =
                        stepToInstructionIndex.find(*instruction.jumpTargetStep);

                    if (iterator != stepToInstructionIndex.end())
                    {
                        instructionIndex = iterator->second;
                        continue;
                    }
                }
                break;
            }

            case EventIrOperation::IsActorKilled:
            {
                if (instruction.arguments.size() >= 4)
                {
                    const uint32_t checkType = instruction.arguments[0];
                    const uint32_t id = instruction.arguments[1];
                    const uint32_t count = instruction.arguments[2];
                    const bool invisibleAsDead = instruction.arguments[3] != 0;
                    const bool killed = pSceneEventContext != nullptr
                        && pSceneEventContext->checkMonstersKilled(checkType, id, count, invisibleAsDead);

                    std::cout << "  check_monsters_killed type=" << checkType
                              << " id=" << id
                              << " count=" << count
                              << " invisible_as_dead=" << (invisibleAsDead ? "1" : "0")
                              << " -> " << (killed ? "true" : "false") << '\n';

                    if (killed && instruction.jumpTargetStep)
                    {
                        const std::unordered_map<uint8_t, size_t>::const_iterator iterator =
                            stepToInstructionIndex.find(*instruction.jumpTargetStep);

                        if (iterator != stepToInstructionIndex.end())
                        {
                            instructionIndex = iterator->second;
                            continue;
                        }
                    }
                }
                break;
            }

            case EventIrOperation::Add:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    addVariableValue(
                        runtimeState,
                        variable,
                        static_cast<int32_t>(instruction.arguments[1]),
                        pParty,
                        targetMemberIndices
                    );
                    std::cout << "  add raw=" << instruction.arguments[0]
                              << " value=" << instruction.arguments[1]
                              << " -> " << getVariableValue(
                                  runtimeState,
                                  variable,
                                  pParty,
                                  singleTargetMemberIndex(targetMemberIndices)) << '\n';
                }
                break;
            }

            case EventIrOperation::SummonMonsters:
            {
                if (instruction.arguments.size() >= 8)
                {
                    const uint32_t typeIndex = instruction.arguments[0];
                    const uint32_t level = instruction.arguments[1];
                    const uint32_t count = instruction.arguments[2];
                    const int32_t x = static_cast<int32_t>(instruction.arguments[3]);
                    const int32_t y = static_cast<int32_t>(instruction.arguments[4]);
                    const int32_t z = static_cast<int32_t>(instruction.arguments[5]);
                    const uint32_t group = instruction.arguments[6];
                    const uint32_t uniqueNameId = instruction.arguments[7];
                    const bool summoned = pSceneEventContext != nullptr
                        && pSceneEventContext->summonMonsters(
                            typeIndex,
                            level,
                            count,
                            x,
                            y,
                            z,
                            group,
                            uniqueNameId);

                    std::cout << "  summon_monsters type=" << typeIndex
                              << " level=" << level
                              << " count=" << count
                              << " pos=(" << x << "," << y << "," << z << ")"
                              << " group=" << group
                              << " unique=" << uniqueNameId
                              << " -> " << (summoned ? "true" : "false") << '\n';
                }
                break;
            }

            case EventIrOperation::Subtract:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    subtractVariableValue(
                        runtimeState,
                        variable,
                        static_cast<int32_t>(instruction.arguments[1]),
                        pParty,
                        targetMemberIndices
                    );
                    std::cout << "  sub raw=" << instruction.arguments[0]
                              << " value=" << instruction.arguments[1]
                              << " -> " << getVariableValue(
                                  runtimeState,
                                  variable,
                                  pParty,
                                  singleTargetMemberIndex(targetMemberIndices)) << '\n';
                }
                break;
            }

            case EventIrOperation::ChangeEvent:
            {
                if (!instruction.arguments.empty() && runtimeState.activeDecorationContext)
                {
                    EventRuntimeState::ActiveDecorationContext &context = *runtimeState.activeDecorationContext;
                    const uint16_t targetEventId = static_cast<uint16_t>(instruction.arguments[0]);
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

                    runtimeState.decorVars[context.decorVarIndex] = newState;
                    context.currentEventId = targetEventId;

                    std::cout << "  change_event target=" << targetEventId
                              << " decor_var[" << static_cast<int>(context.decorVarIndex) << "]="
                              << static_cast<int>(newState) << '\n';
                }
                break;
            }

            case EventIrOperation::Set:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const VariableRef variable = decodeVariable(instruction.arguments[0]);
                    setVariableValue(
                        runtimeState,
                        variable,
                        static_cast<int32_t>(instruction.arguments[1]),
                        pParty,
                        targetMemberIndices
                    );
                    std::cout << "  set raw=" << instruction.arguments[0]
                              << " value=" << instruction.arguments[1]
                              << " -> " << getVariableValue(
                                  runtimeState,
                                  variable,
                                  pParty,
                                  singleTargetMemberIndex(targetMemberIndices)) << '\n';
                }
                break;
            }

            case EventIrOperation::ShowMessage:
            {
                if (instruction.text && !instruction.text->empty())
                {
                    runtimeState.messages.push_back(*instruction.text);
                }
                break;
            }

            case EventIrOperation::StatusText:
            {
                if (instruction.text && !instruction.text->empty())
                {
                    runtimeState.statusMessages.push_back(*instruction.text);
                }
                break;
            }

            case EventIrOperation::OpenChest:
            {
                if (!instruction.arguments.empty())
                {
                    runtimeState.openedChestIds.push_back(instruction.arguments[0]);
                    std::cout << "  open_chest=" << instruction.arguments[0] << '\n';
                }
                break;
            }

            case EventIrOperation::GiveItem:
            {
                if (!instruction.arguments.empty())
                {
                    runtimeState.grantedItemIds.push_back(instruction.arguments[0]);
                    std::cout << "  give_item=" << instruction.arguments[0] << '\n';
                }
                break;
            }

            case EventIrOperation::RemoveItems:
            {
                if (!instruction.arguments.empty())
                {
                    runtimeState.removedItemIds.push_back(instruction.arguments[0]);
                    std::cout << "  remove_item=" << instruction.arguments[0] << '\n';
                }
                break;
            }

            case EventIrOperation::ChangeDoorState:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const uint32_t mechanismId = instruction.arguments[0];
                    RuntimeMechanismState &runtimeMechanism = runtimeState.mechanisms[mechanismId];
                    const uint32_t actionValue = instruction.arguments[1];
                    MechanismAction action = MechanismAction::Open;

                    if (actionValue == static_cast<uint32_t>(EvtMechanismAction::Close))
                    {
                        action = MechanismAction::Close;
                    }
                    else if (actionValue == static_cast<uint32_t>(EvtMechanismAction::Trigger))
                    {
                        action = MechanismAction::Trigger;
                    }

                    applyMechanismAction(runtimeMechanism, action);
                    runtimeState.lastAffectedMechanismIds.push_back(mechanismId);
                    std::cout << "  mech " << mechanismId
                              << " action=" << actionValue
                              << " state=" << runtimeMechanism.state
                              << " moving=" << (runtimeMechanism.isMoving ? "yes" : "no") << '\n';
                }
                break;
            }

            case EventIrOperation::StopAnimation:
            {
                if (!instruction.arguments.empty())
                {
                    const uint32_t mechanismId = instruction.arguments[0];
                    RuntimeMechanismState &runtimeMechanism = runtimeState.mechanisms[mechanismId];
                    runtimeMechanism.isMoving = false;
                    runtimeState.lastAffectedMechanismIds.push_back(mechanismId);
                    std::cout << "  mech " << mechanismId
                              << " stopped at distance=" << runtimeMechanism.currentDistance << '\n';
                }
                break;
            }

            case EventIrOperation::SetTexture:
            {
                if (instruction.arguments.empty())
                {
                    break;
                }

                const uint32_t cogNumber = instruction.arguments[0];

                if (instruction.text && !instruction.text->empty())
                {
                    runtimeState.textureOverrides[cogNumber] = *instruction.text;
                    std::cout << "  texture cog=" << cogNumber << " name=\"" << *instruction.text << "\"\n";
                }
                else
                {
                    runtimeState.textureOverrides.erase(cogNumber);
                    std::cout << "  texture cog=" << cogNumber << " cleared\n";
                }
                break;
            }

            case EventIrOperation::ToggleIndoorLight:
            {
                if (instruction.arguments.size() >= 2)
                {
                    const uint32_t lightId = instruction.arguments[0];
                    const bool isEnabled = instruction.arguments[1] != 0;
                    runtimeState.indoorLightsEnabled[lightId] = isEnabled;
                    std::cout << "  light " << lightId << " on=" << (isEnabled ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::SetFacetBit:
            {
                if (instruction.arguments.size() >= 3)
                {
                    const uint32_t faceId = instruction.arguments[0];
                    const uint32_t bit = instruction.arguments[1];
                    const bool isOn = instruction.arguments[2] != 0;

                    if (isOn)
                    {
                        runtimeState.facetSetMasks[faceId] |= bit;
                        runtimeState.facetClearMasks[faceId] &= ~bit;
                    }
                    else
                    {
                        runtimeState.facetClearMasks[faceId] |= bit;
                        runtimeState.facetSetMasks[faceId] &= ~bit;
                    }

                    std::cout << "  facet " << faceId
                              << " bit=0x" << std::hex << bit << std::dec
                              << " on=" << (isOn ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::SetActorFlag:
            {
                if (instruction.arguments.size() >= 3)
                {
                    const uint32_t actorId = instruction.arguments[0];
                    const uint32_t bit = instruction.arguments[1];
                    const bool isOn = instruction.arguments[2] != 0;

                    if (isOn)
                    {
                        runtimeState.actorSetMasks[actorId] |= bit;
                        runtimeState.actorClearMasks[actorId] &= ~bit;
                    }
                    else
                    {
                        runtimeState.actorClearMasks[actorId] |= bit;
                        runtimeState.actorSetMasks[actorId] &= ~bit;
                    }

                    std::cout << "  actor " << actorId
                              << " bit=0x" << std::hex << bit << std::dec
                              << " on=" << (isOn ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::SetActorGroupFlag:
            {
                if (instruction.arguments.size() >= 3)
                {
                    const uint32_t groupId = instruction.arguments[0];
                    const uint32_t bit = instruction.arguments[1];
                    const bool isOn = instruction.arguments[2] != 0;

                    if (isOn)
                    {
                        runtimeState.actorGroupSetMasks[groupId] |= bit;
                        runtimeState.actorGroupClearMasks[groupId] &= ~bit;
                    }
                    else
                    {
                        runtimeState.actorGroupClearMasks[groupId] |= bit;
                        runtimeState.actorGroupSetMasks[groupId] &= ~bit;
                    }

                    std::cout << "  actor_group " << groupId
                              << " bit=0x" << std::hex << bit << std::dec
                              << " on=" << (isOn ? "1" : "0") << '\n';
                }
                break;
            }

            case EventIrOperation::SetNpcTopic:
            {
                if (instruction.arguments.size() >= 3)
                {
                    runtimeState.npcTopicOverrides[instruction.arguments[0]][instruction.arguments[1]] =
                        instruction.arguments[2];
                    std::cout << "  npc_topic npc=" << instruction.arguments[0]
                              << " slot=" << instruction.arguments[1]
                              << " event=" << instruction.arguments[2] << '\n';
                }
                break;
            }

            case EventIrOperation::SetNpcGroupNews:
            {
                if (instruction.arguments.size() >= 2)
                {
                    runtimeState.npcGroupNews[instruction.arguments[0]] = instruction.arguments[1];
                }
                break;
            }

            case EventIrOperation::Unknown:
                break;
        }

        ++instructionIndex;
    }

    return true;
}
}
