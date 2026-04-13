#include "tools/LegacyLuaExport.h"
#include "game/events/EvtEnums.h"
#include "game/tables/PortraitEnums.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
bool luaExportTraceEnabled()
{
    static const bool enabled = std::getenv("OPENYAMM_LUA_EXPORT_TRACE") != nullptr;
    return enabled;
}

constexpr char LuaScopeGlobal[] = "global";
constexpr char LuaScopeMap[] = "map";

enum class LegacyLuaOperation
{
    Exit,
    TriggerMouseOver,
    TriggerOnLoadMap,
    TriggerOnLeaveMap,
    TriggerOnTimer,
    TriggerOnLongTimer,
    TriggerOnDateTimer,
    EnableDateTimer,
    PlaySound,
    LocationName,
    Compare,
    CompareCanShowTopic,
    Jump,
    SetCanShowTopic,
    EndCanShowTopic,
    Add,
    Subtract,
    Set,
    ShowMessage,
    StatusText,
    SpeakInHouse,
    SpeakNpc,
    MoveToMap,
    MoveNpc,
    ChangeEvent,
    OpenChest,
    RandomJump,
    SummonMonsters,
    SummonItem,
    GiveItem,
    CastSpell,
    ShowFace,
    ReceiveDamage,
    SetSnow,
    ShowMovie,
    SetSprite,
    ChangeDoorState,
    StopAnimation,
    SetTexture,
    ToggleIndoorLight,
    SetFacetBit,
    SetActorFlag,
    SetActorGroupFlag,
    SetActorGroup,
    SetNpcTopic,
    SetNpcGroupNews,
    SetNpcGreeting,
    SetNpcItem,
    SetActorItem,
    CharacterAnimation,
    ForPartyMember,
    CheckItemsCount,
    RemoveItems,
    CheckSkill,
    IsActorKilled,
    IsActorKilledCanShowTopic,
    ChangeGroup,
    ChangeGroupAlly,
    CheckSeason,
    ToggleChestFlag,
    InputString,
    PressAnyKey,
    SpecialJump,
    IsTotalBountyHuntingAwardInRange,
    IsNpcInParty,
    Unknown,
};

enum class SelectorSemantic
{
    Generic,
    QBit,
    Award,
    Autonote,
    InventoryItem,
    PlayerValue,
    PlayerBit,
    MapVar,
    DecorVar,
    Counter,
    History,
};

struct LegacyLuaInstruction
{
    uint16_t eventId = 0;
    uint8_t step = 0;
    LegacyLuaOperation operation = LegacyLuaOperation::Unknown;
    std::vector<uint32_t> arguments;
    std::optional<uint8_t> jumpTargetStep;
    std::optional<std::string> text;
};

struct LegacyLuaEvent
{
    uint16_t eventId = 0;
    std::vector<LegacyLuaInstruction> instructions;
};

struct FormattedSelector
{
    std::string expression;
    SelectorSemantic semantic = SelectorSemantic::Generic;
    uint32_t index = 0;
};

template <typename TValue>
std::optional<TValue> readPayloadValue(const std::vector<uint8_t> &payload, size_t offset)
{
    TValue value = {};

    if (offset > payload.size() || sizeof(TValue) > (payload.size() - offset))
    {
        return std::nullopt;
    }

    std::memcpy(&value, payload.data() + offset, sizeof(TValue));
    return value;
}

std::string escapeLuaString(std::string_view text)
{
    std::string escaped;
    escaped.reserve(text.size());

    for (char character : text)
    {
        switch (character)
        {
            case '\\':
                escaped += "\\\\";
                break;

            case '"':
                escaped += "\\\"";
                break;

            case '\n':
                escaped += "\\n";
                break;

            case '\r':
                escaped += "\\r";
                break;

            case '\t':
                escaped += "\\t";
                break;

            default:
                escaped.push_back(character);
                break;
        }
    }

    return escaped;
}

std::string luaQuoted(std::string_view text)
{
    return "\"" + escapeLuaString(text) + "\"";
}

std::string toLowerCopy(std::string_view text)
{
    std::string lowered(text);

    for (char &character : lowered)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return lowered;
}

std::string sanitizeLuaCommentText(std::string_view text)
{
    std::string sanitized;
    sanitized.reserve(text.size());

    bool previousWasSpace = false;

    for (char character : text)
    {
        const bool isWhitespace = character == '\r' || character == '\n' || character == '\t';

        if (isWhitespace)
        {
            if (!previousWasSpace)
            {
                sanitized.push_back(' ');
                previousWasSpace = true;
            }

            continue;
        }

        sanitized.push_back(character);
        previousWasSpace = character == ' ';
    }

    while (!sanitized.empty() && sanitized.back() == ' ')
    {
        sanitized.pop_back();
    }

    return sanitized;
}

std::string formatFaceAnimation(uint32_t value)
{
    switch (static_cast<FaceAnimationId>(value))
    {
        case FaceAnimationId::KillSmallEnemy:
            return "FaceAnimation.KillSmallEnemy";
        case FaceAnimationId::KillBigEnemy:
            return "FaceAnimation.KillBigEnemy";
        case FaceAnimationId::StoreClosed:
            return "FaceAnimation.StoreClosed";
        case FaceAnimationId::DisarmTrap:
            return "FaceAnimation.DisarmTrap";
        case FaceAnimationId::TrapExploded:
            return "FaceAnimation.TrapExploded";
        case FaceAnimationId::AvoidDamage:
            return "FaceAnimation.AvoidDamage";
        case FaceAnimationId::IdentifyUseless:
            return "FaceAnimation.IdentifyUseless";
        case FaceAnimationId::IdentifyGreat:
            return "FaceAnimation.IdentifyGreat";
        case FaceAnimationId::IdentifyFail:
            return "FaceAnimation.IdentifyFail";
        case FaceAnimationId::RepairItem:
            return "FaceAnimation.RepairItem";
        case FaceAnimationId::RepairFail:
            return "FaceAnimation.RepairFail";
        case FaceAnimationId::SetQuickSpell:
            return "FaceAnimation.SetQuickSpell";
        case FaceAnimationId::CantRestHere:
            return "FaceAnimation.CantRestHere";
        case FaceAnimationId::SkillIncreased:
            return "FaceAnimation.SkillIncreased";
        case FaceAnimationId::CantCarry:
            return "FaceAnimation.CantCarry";
        case FaceAnimationId::MixPotion:
            return "FaceAnimation.MixPotion";
        case FaceAnimationId::PotionExplode:
            return "FaceAnimation.PotionExplode";
        case FaceAnimationId::DoorLocked:
            return "FaceAnimation.DoorLocked";
        case FaceAnimationId::WontBudge:
            return "FaceAnimation.WontBudge";
        case FaceAnimationId::CantLearnSpell:
            return "FaceAnimation.CantLearnSpell";
        case FaceAnimationId::LearnSpell:
            return "FaceAnimation.LearnSpell";
        case FaceAnimationId::Hello:
            return "FaceAnimation.Hello";
        case FaceAnimationId::HelloNight:
            return "FaceAnimation.HelloNight";
        case FaceAnimationId::Damaged:
            return "FaceAnimation.Damaged";
        case FaceAnimationId::Weak:
            return "FaceAnimation.Weak";
        case FaceAnimationId::Afraid:
            return "FaceAnimation.Afraid";
        case FaceAnimationId::Poisoned:
            return "FaceAnimation.Poisoned";
        case FaceAnimationId::Diseased:
            return "FaceAnimation.Diseased";
        case FaceAnimationId::Insane:
            return "FaceAnimation.Insane";
        case FaceAnimationId::Cursed:
            return "FaceAnimation.Cursed";
        case FaceAnimationId::Drunk:
            return "FaceAnimation.Drunk";
        case FaceAnimationId::Unconscious:
            return "FaceAnimation.Unconscious";
        case FaceAnimationId::Death:
            return "FaceAnimation.Death";
        case FaceAnimationId::Stoned:
            return "FaceAnimation.Stoned";
        case FaceAnimationId::Eradicated:
            return "FaceAnimation.Eradicated";
        case FaceAnimationId::DrinkPotion:
            return "FaceAnimation.DrinkPotion";
        case FaceAnimationId::ReadScroll:
            return "FaceAnimation.ReadScroll";
        case FaceAnimationId::NotEnoughGold:
            return "FaceAnimation.NotEnoughGold";
        case FaceAnimationId::CantEquip:
            return "FaceAnimation.CantEquip";
        case FaceAnimationId::ItemBrokenStolen:
            return "FaceAnimation.ItemBrokenStolen";
        case FaceAnimationId::SpellPointsDrained:
            return "FaceAnimation.SpellPointsDrained";
        case FaceAnimationId::Aged:
            return "FaceAnimation.Aged";
        case FaceAnimationId::SpellFailed:
            return "FaceAnimation.SpellFailed";
        case FaceAnimationId::DamagedParty:
            return "FaceAnimation.DamagedParty";
        case FaceAnimationId::Tired:
            return "FaceAnimation.Tired";
        case FaceAnimationId::EnterDungeon:
            return "FaceAnimation.EnterDungeon";
        case FaceAnimationId::LeaveDungeon:
            return "FaceAnimation.LeaveDungeon";
        case FaceAnimationId::AlmostDead:
            return "FaceAnimation.AlmostDead";
        case FaceAnimationId::CastSpell:
            return "FaceAnimation.CastSpell";
        case FaceAnimationId::Shoot:
            return "FaceAnimation.Shoot";
        case FaceAnimationId::AttackHit:
            return "FaceAnimation.AttackHit";
        case FaceAnimationId::AttackMiss:
            return "FaceAnimation.AttackMiss";
        case FaceAnimationId::ShopIdentify:
            return "FaceAnimation.ShopIdentify";
        case FaceAnimationId::ShopRepair:
            return "FaceAnimation.ShopRepair";
        case FaceAnimationId::AlreadyIdentified:
            return "FaceAnimation.AlreadyIdentified";
        case FaceAnimationId::ItemSold:
            return "FaceAnimation.ItemSold";
        case FaceAnimationId::WrongShop:
            return "FaceAnimation.WrongShop";
    }

    return std::to_string(value);
}

std::optional<std::string> lookupText(
    const std::unordered_map<uint32_t, std::string> &table,
    uint32_t id)
{
    const auto iterator = table.find(id);

    if (iterator == table.end() || iterator->second.empty())
    {
        return std::nullopt;
    }

    return iterator->second;
}

std::optional<std::string> lookupMapName(
    const std::unordered_map<std::string, std::string> &table,
    std::string_view pathOrStem)
{
    if (pathOrStem.empty())
    {
        return std::nullopt;
    }

    const std::filesystem::path path(pathOrStem);
    const std::string loweredPath = toLowerCopy(path.generic_string());
    const auto pathIterator = table.find(loweredPath);

    if (pathIterator != table.end() && !pathIterator->second.empty())
    {
        return pathIterator->second;
    }

    const std::string loweredFilename = toLowerCopy(path.filename().generic_string());
    const auto filenameIterator = table.find(loweredFilename);

    if (filenameIterator != table.end() && !filenameIterator->second.empty())
    {
        return filenameIterator->second;
    }

    const std::string loweredStem = toLowerCopy(path.stem().generic_string());
    const auto stemIterator = table.find(loweredStem);

    if (stemIterator != table.end() && !stemIterator->second.empty())
    {
        return stemIterator->second;
    }

    return std::nullopt;
}

std::string formatFacetBit(uint32_t value)
{
    switch (value)
    {
        case 0x00002000: return "FacetBits.Invisible";
        case 0x00000002: return "FacetBits.IsSecret";
        case 0x00040000: return "FacetBits.MoveByDoor";
        case 0x20000000: return "FacetBits.Untouchable";
        default: return std::to_string(value);
    }
}

std::string formatMonsterBit(uint32_t value)
{
    switch (value)
    {
        case 0x00010000: return "MonsterBits.Invisible";
        case 0x00080000: return "MonsterBits.Hostile";
        default: return std::to_string(value);
    }
}

std::string formatPartySelector(uint32_t value)
{
    switch (value)
    {
        case 0: return "Players.Member0";
        case 1: return "Players.Member1";
        case 2: return "Players.Member2";
        case 3: return "Players.Member3";
        case 4: return "Players.Member4";
        case 5: return "Players.All";
        case 7: return "Players.Current";
        default: return std::to_string(value);
    }
}

std::string formatRandomItemType(uint32_t value)
{
    switch (value)
    {
        case 20: return "ItemType.Weapon_";
        case 21: return "ItemType.Armor_";
        case 22: return "ItemType.Misc";
        case 40: return "ItemType.Ring_";
        case 43: return "ItemType.Scroll_";
        default: return std::to_string(value);
    }
}

FormattedSelector formatSelector(uint32_t rawValue)
{
    const EvtVariable variableId = static_cast<EvtVariable>(rawValue & 0xFFFFu);
    const uint32_t index = rawValue >> 16;

    if (variableId == EvtVariable::QBits)
    {
        return {"QBit(" + std::to_string(index) + ")", SelectorSemantic::QBit, index};
    }

    if (variableId == EvtVariable::Inventory)
    {
        return {"InventoryItem(" + std::to_string(index) + ")", SelectorSemantic::InventoryItem, index};
    }

    if (variableId == EvtVariable::Awards)
    {
        return {"Award(" + std::to_string(index) + ")", SelectorSemantic::Award, index};
    }

    if (variableId == EvtVariable::AutoNotes)
    {
        return {"AutonoteBit(" + std::to_string(index) + ")", SelectorSemantic::Autonote, index};
    }

    if (variableId == EvtVariable::Players)
    {
        return {"Player(" + std::to_string(index) + ")", SelectorSemantic::PlayerValue, index};
    }

    if (variableId == EvtVariable::PlayerBits)
    {
        return {"PlayerBit(" + std::to_string(index) + ")", SelectorSemantic::PlayerBit, index};
    }

    if (variableId >= EvtVariable::MapPersistentVariableBegin && variableId <= EvtVariable::MapPersistentVariableEnd)
    {
        return {
            "MapVar(" + std::to_string(static_cast<uint32_t>(variableId) -
                static_cast<uint32_t>(EvtVariable::MapPersistentVariableBegin)) + ")",
            SelectorSemantic::MapVar,
            static_cast<uint32_t>(variableId) - static_cast<uint32_t>(EvtVariable::MapPersistentVariableBegin)
        };
    }

    if (variableId >= EvtVariable::MapPersistentDecorVariableBegin
        && variableId <= EvtVariable::MapPersistentDecorVariableEnd)
    {
        return {
            "DecorVar(" + std::to_string(static_cast<uint32_t>(variableId) -
                static_cast<uint32_t>(EvtVariable::MapPersistentDecorVariableBegin)) + ")",
            SelectorSemantic::DecorVar,
            static_cast<uint32_t>(variableId) - static_cast<uint32_t>(EvtVariable::MapPersistentDecorVariableBegin)
        };
    }

    if (variableId >= EvtVariable::HistoryBegin && variableId <= EvtVariable::HistoryEnd)
    {
        return {
            "History(" + std::to_string(static_cast<uint32_t>(variableId) -
                static_cast<uint32_t>(EvtVariable::HistoryBegin) + 1) + ")",
            SelectorSemantic::History,
            static_cast<uint32_t>(variableId) - static_cast<uint32_t>(EvtVariable::HistoryBegin) + 1
        };
    }

    if (variableId >= EvtVariable::Counter1 && variableId <= EvtVariable::Counter10)
    {
        return {
            "Counter(" + std::to_string(static_cast<uint32_t>(variableId) -
                static_cast<uint32_t>(EvtVariable::Counter1) + 1) + ")",
            SelectorSemantic::Counter,
            static_cast<uint32_t>(variableId) - static_cast<uint32_t>(EvtVariable::Counter1) + 1
        };
    }

    switch (variableId)
    {
        case EvtVariable::Sex: return {"Sex"};
        case EvtVariable::ClassId: return {"ClassId"};
        case EvtVariable::CurrentHealth: return {"CurrentHealth"};
        case EvtVariable::MaxHealth: return {"MaxHealth"};
        case EvtVariable::CurrentSpellPoints: return {"CurrentSpellPoints"};
        case EvtVariable::MaxSpellPoints: return {"MaxSpellPoints"};
        case EvtVariable::ActualArmorClass: return {"ActualArmorClass"};
        case EvtVariable::ArmorClassBonus: return {"ArmorClassBonus"};
        case EvtVariable::BaseLevel: return {"BaseLevel"};
        case EvtVariable::LevelBonus: return {"LevelBonus"};
        case EvtVariable::Age: return {"Age"};
        case EvtVariable::Experience: return {"Experience"};
        case EvtVariable::Race: return {"Race"};
        case EvtVariable::Hour: return {"Hour"};
        case EvtVariable::DayOfYear: return {"DayOfYear"};
        case EvtVariable::DayOfWeek: return {"DayOfWeek"};
        case EvtVariable::Gold:
        case EvtVariable::RandomGold: return {"Gold"};
        case EvtVariable::Food:
        case EvtVariable::RandomFood: return {"Food"};
        case EvtVariable::MightBonus: return {"MightBonus"};
        case EvtVariable::IntellectBonus: return {"IntellectBonus"};
        case EvtVariable::PersonalityBonus: return {"PersonalityBonus"};
        case EvtVariable::EnduranceBonus: return {"EnduranceBonus"};
        case EvtVariable::SpeedBonus: return {"SpeedBonus"};
        case EvtVariable::AccuracyBonus: return {"AccuracyBonus"};
        case EvtVariable::LuckBonus: return {"LuckBonus"};
        case EvtVariable::BaseMight: return {"BaseMight"};
        case EvtVariable::BaseIntellect: return {"BaseIntellect"};
        case EvtVariable::BasePersonality: return {"BasePersonality"};
        case EvtVariable::BaseEndurance: return {"BaseEndurance"};
        case EvtVariable::BaseSpeed: return {"BaseSpeed"};
        case EvtVariable::BaseAccuracy: return {"BaseAccuracy"};
        case EvtVariable::BaseLuck: return {"BaseLuck"};
        case EvtVariable::ActualMight: return {"ActualMight"};
        case EvtVariable::ActualIntellect: return {"ActualIntellect"};
        case EvtVariable::ActualPersonality: return {"ActualPersonality"};
        case EvtVariable::ActualEndurance: return {"ActualEndurance"};
        case EvtVariable::ActualSpeed: return {"ActualSpeed"};
        case EvtVariable::ActualAccuracy: return {"ActualAccuracy"};
        case EvtVariable::ActualLuck: return {"ActualLuck"};
        case EvtVariable::FireResistance: return {"FireResistance"};
        case EvtVariable::AirResistance: return {"AirResistance"};
        case EvtVariable::WaterResistance: return {"WaterResistance"};
        case EvtVariable::EarthResistance: return {"EarthResistance"};
        case EvtVariable::SpiritResistance: return {"SpiritResistance"};
        case EvtVariable::MindResistance: return {"MindResistance"};
        case EvtVariable::BodyResistance: return {"BodyResistance"};
        case EvtVariable::LightResistance: return {"LightResistance"};
        case EvtVariable::DarkResistance: return {"DarkResistance"};
        case EvtVariable::PhysicalResistance: return {"PhysicalResistance"};
        case EvtVariable::MagicResistance: return {"MagicResistance"};
        case EvtVariable::FireResistanceBonus: return {"FireResistanceBonus"};
        case EvtVariable::AirResistanceBonus: return {"AirResistanceBonus"};
        case EvtVariable::WaterResistanceBonus: return {"WaterResistanceBonus"};
        case EvtVariable::EarthResistanceBonus: return {"EarthResistanceBonus"};
        case EvtVariable::SpiritResistanceBonus: return {"SpiritResistanceBonus"};
        case EvtVariable::MindResistanceBonus: return {"MindResistanceBonus"};
        case EvtVariable::BodyResistanceBonus: return {"BodyResistanceBonus"};
        case EvtVariable::LightResistanceBonus: return {"LightResistanceBonus"};
        case EvtVariable::DarkResistanceBonus: return {"DarkResistanceBonus"};
        case EvtVariable::PhysicalResistanceBonus: return {"PhysicalResistanceBonus"};
        case EvtVariable::MagicResistanceBonus: return {"MagicResistanceBonus"};
        case EvtVariable::StaffSkill: return {"StaffSkill"};
        case EvtVariable::SwordSkill: return {"SwordSkill"};
        case EvtVariable::DaggerSkill: return {"DaggerSkill"};
        case EvtVariable::AxeSkill: return {"AxeSkill"};
        case EvtVariable::SpearSkill: return {"SpearSkill"};
        case EvtVariable::BowSkill: return {"BowSkill"};
        case EvtVariable::MaceSkill: return {"MaceSkill"};
        case EvtVariable::BlasterSkill: return {"BlasterSkill"};
        case EvtVariable::ShieldSkill: return {"ShieldSkill"};
        case EvtVariable::LeatherSkill: return {"LeatherSkill"};
        case EvtVariable::ChainSkill: return {"ChainSkill"};
        case EvtVariable::PlateSkill: return {"PlateSkill"};
        case EvtVariable::FireSkill: return {"FireSkill"};
        case EvtVariable::AirSkill: return {"AirSkill"};
        case EvtVariable::WaterSkill: return {"WaterSkill"};
        case EvtVariable::EarthSkill: return {"EarthSkill"};
        case EvtVariable::SpiritSkill: return {"SpiritSkill"};
        case EvtVariable::MindSkill: return {"MindSkill"};
        case EvtVariable::BodySkill: return {"BodySkill"};
        case EvtVariable::LightSkill: return {"LightSkill"};
        case EvtVariable::DarkSkill: return {"DarkSkill"};
        case EvtVariable::IdentifyItemSkill: return {"IdentifyItemSkill"};
        case EvtVariable::MerchantSkill: return {"MerchantSkill"};
        case EvtVariable::RepairSkill: return {"RepairSkill"};
        case EvtVariable::BodybuildingSkill: return {"BodybuildingSkill"};
        case EvtVariable::MeditationSkill: return {"MeditationSkill"};
        case EvtVariable::PerceptionSkill: return {"PerceptionSkill"};
        case EvtVariable::DiplomacySkill: return {"DiplomacySkill"};
        case EvtVariable::ThieverySkill: return {"ThieverySkill"};
        case EvtVariable::DisarmTrapSkill: return {"DisarmTrapSkill"};
        case EvtVariable::DodgeSkill: return {"DodgeSkill"};
        case EvtVariable::UnarmedSkill: return {"UnarmedSkill"};
        case EvtVariable::IdentifyMonsterSkill: return {"IdentifyMonsterSkill"};
        case EvtVariable::ArmsmasterSkill: return {"ArmsmasterSkill"};
        case EvtVariable::StealingSkill: return {"StealingSkill"};
        case EvtVariable::AlchemySkill: return {"AlchemySkill"};
        case EvtVariable::LearningSkill: return {"LearningSkill"};
        case EvtVariable::Cursed: return {"Cursed"};
        case EvtVariable::Weak: return {"Weak"};
        case EvtVariable::Asleep: return {"Asleep"};
        case EvtVariable::Afraid: return {"Afraid"};
        case EvtVariable::Drunk: return {"Drunk"};
        case EvtVariable::Insane: return {"Insane"};
        case EvtVariable::PoisonedGreen: return {"PoisonedGreen"};
        case EvtVariable::DiseasedGreen: return {"DiseasedGreen"};
        case EvtVariable::PoisonedYellow: return {"PoisonedYellow"};
        case EvtVariable::DiseasedYellow: return {"DiseasedYellow"};
        case EvtVariable::PoisonedRed: return {"PoisonedRed"};
        case EvtVariable::DiseasedRed: return {"DiseasedRed"};
        case EvtVariable::Paralyzed: return {"Paralyzed"};
        case EvtVariable::Unconscious: return {"Unconscious"};
        case EvtVariable::Dead: return {"Dead"};
        case EvtVariable::Stoned: return {"Stoned"};
        case EvtVariable::Eradicated: return {"Eradicated"};
        case EvtVariable::MajorCondition: return {"MajorCondition"};
        case EvtVariable::IsMightMoreThanBase: return {"IsMightMoreThanBase"};
        case EvtVariable::IsIntellectMoreThanBase: return {"IsIntellectMoreThanBase"};
        case EvtVariable::IsPersonalityMoreThanBase: return {"IsPersonalityMoreThanBase"};
        case EvtVariable::IsEnduranceMoreThanBase: return {"IsEnduranceMoreThanBase"};
        case EvtVariable::IsSpeedMoreThanBase: return {"IsSpeedMoreThanBase"};
        case EvtVariable::IsAccuracyMoreThanBase: return {"IsAccuracyMoreThanBase"};
        case EvtVariable::IsLuckMoreThanBase: return {"IsLuckMoreThanBase"};
        case EvtVariable::Npcs2: return {"Npcs2"};
        case EvtVariable::IsFlying: return {"IsFlying"};
        case EvtVariable::HiredNpcHasSpeciality: return {"HiredNpcHasSpeciality"};
        case EvtVariable::CircusPrises: return {"CircusPrises"};
        case EvtVariable::NumSkillPoints: return {"SkillPoints"};
        case EvtVariable::MonthIs: return {"MonthIs"};
        case EvtVariable::ReputationInCurrentLocation: return {"ReputationInCurrentLocation"};
        case EvtVariable::Unknown1: return {"Unknown1"};
        case EvtVariable::GoldInBank: return {"BankGold"};
        case EvtVariable::NumDeaths: return {"NumDeaths"};
        case EvtVariable::NumBounties: return {"NumBounties"};
        case EvtVariable::PrisonTerms: return {"PrisonTerms"};
        case EvtVariable::ArenaWinsPage: return {"ArenaWinsPage"};
        case EvtVariable::ArenaWinsSquire: return {"ArenaWinsSquire"};
        case EvtVariable::ArenaWinsKnight: return {"ArenaWinsKnight"};
        case EvtVariable::ArenaWinsLord: return {"ArenaWinsLord"};
        case EvtVariable::Invisible: return {"Invisible"};
        case EvtVariable::ItemEquipped: return {"ItemEquipped"};
        default: break;
    }

    return {std::to_string(rawValue)};
}

std::optional<std::string> resolveSelectorComment(
    const FormattedSelector &selector,
    const LegacyLuaExportLookups &lookups)
{
    if (selector.semantic == SelectorSemantic::InventoryItem)
    {
        return lookupText(lookups.itemNames, selector.index);
    }

    return std::nullopt;
}

std::string formatCompareExpression(
    const FormattedSelector &selector,
    uint32_t value)
{
    if ((selector.semantic == SelectorSemantic::QBit
            || selector.semantic == SelectorSemantic::Award
            || selector.semantic == SelectorSemantic::Autonote
            || selector.semantic == SelectorSemantic::PlayerBit)
        && value == selector.index)
    {
        switch (selector.semantic)
        {
            case SelectorSemantic::QBit: return "IsQBitSet(" + selector.expression + ")";
            case SelectorSemantic::Award: return "HasAward(" + selector.expression + ")";
            case SelectorSemantic::Autonote: return "IsAutonoteSet(" + selector.expression + ")";
            case SelectorSemantic::PlayerBit: return "IsPlayerBitSet(" + selector.expression + ")";
            default: break;
        }
    }

    if (selector.semantic == SelectorSemantic::InventoryItem && value == selector.index)
    {
        return "HasItem(" + std::to_string(selector.index) + ")";
    }

    return "IsAtLeast(" + selector.expression + ", " + std::to_string(static_cast<int32_t>(value)) + ")";
}

std::string formatAddExpression(
    const FormattedSelector &selector,
    uint32_t value)
{
    if (value == selector.index)
    {
        switch (selector.semantic)
        {
            case SelectorSemantic::QBit: return "SetQBit(" + selector.expression + ")";
            case SelectorSemantic::Award: return "SetAward(" + selector.expression + ")";
            case SelectorSemantic::Autonote: return "SetAutonote(" + selector.expression + ")";
            case SelectorSemantic::PlayerBit: return "SetPlayerBit(" + selector.expression + ")";
            default: break;
        }
    }

    return "AddValue(" + selector.expression + ", " + std::to_string(static_cast<int32_t>(value)) + ")";
}

std::string formatSubtractExpression(
    const FormattedSelector &selector,
    uint32_t value)
{
    if (value == selector.index)
    {
        switch (selector.semantic)
        {
            case SelectorSemantic::QBit: return "ClearQBit(" + selector.expression + ")";
            case SelectorSemantic::Award: return "ClearAward(" + selector.expression + ")";
            case SelectorSemantic::Autonote: return "ClearAutonote(" + selector.expression + ")";
            case SelectorSemantic::PlayerBit: return "ClearPlayerBit(" + selector.expression + ")";
            default: break;
        }
    }

    if (selector.semantic == SelectorSemantic::InventoryItem && value == selector.index)
    {
        return "RemoveItem(" + std::to_string(selector.index) + ")";
    }

    return "SubtractValue(" + selector.expression + ", " + std::to_string(static_cast<int32_t>(value)) + ")";
}

std::string formatSetExpression(
    const FormattedSelector &selector,
    uint32_t value)
{
    if (value == selector.index)
    {
        switch (selector.semantic)
        {
            case SelectorSemantic::QBit: return "SetQBit(" + selector.expression + ")";
            case SelectorSemantic::Award: return "SetAward(" + selector.expression + ")";
            case SelectorSemantic::Autonote: return "SetAutonote(" + selector.expression + ")";
            case SelectorSemantic::PlayerBit: return "SetPlayerBit(" + selector.expression + ")";
            default: break;
        }
    }

    return "SetValue(" + selector.expression + ", " + std::to_string(static_cast<int32_t>(value)) + ")";
}

template <typename TValue>
void sortAndUnique(std::vector<TValue> &values)
{
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end()), values.end());
}

LegacyLuaOperation mapOperation(EvtOpcode opcode)
{
    switch (opcode)
    {
        case EvtOpcode::Exit: return LegacyLuaOperation::Exit;
        case EvtOpcode::MouseOver: return LegacyLuaOperation::TriggerMouseOver;
        case EvtOpcode::OnMapReload: return LegacyLuaOperation::TriggerOnLoadMap;
        case EvtOpcode::OnMapLeave: return LegacyLuaOperation::TriggerOnLeaveMap;
        case EvtOpcode::OnTimer: return LegacyLuaOperation::TriggerOnTimer;
        case EvtOpcode::OnLongTimer: return LegacyLuaOperation::TriggerOnLongTimer;
        case EvtOpcode::OnDateTimer: return LegacyLuaOperation::TriggerOnDateTimer;
        case EvtOpcode::EnableDateTimer: return LegacyLuaOperation::EnableDateTimer;
        case EvtOpcode::PlaySound: return LegacyLuaOperation::PlaySound;
        case EvtOpcode::LocationName: return LegacyLuaOperation::LocationName;
        case EvtOpcode::Compare: return LegacyLuaOperation::Compare;
        case EvtOpcode::OnCanShowDialogItemCmp: return LegacyLuaOperation::CompareCanShowTopic;
        case EvtOpcode::Jmp: return LegacyLuaOperation::Jump;
        case EvtOpcode::SetCanShowDialogItem: return LegacyLuaOperation::SetCanShowTopic;
        case EvtOpcode::EndCanShowDialogItem: return LegacyLuaOperation::EndCanShowTopic;
        case EvtOpcode::Add: return LegacyLuaOperation::Add;
        case EvtOpcode::Subtract: return LegacyLuaOperation::Subtract;
        case EvtOpcode::Set: return LegacyLuaOperation::Set;
        case EvtOpcode::ShowMessage: return LegacyLuaOperation::ShowMessage;
        case EvtOpcode::StatusText: return LegacyLuaOperation::StatusText;
        case EvtOpcode::SpeakInHouse: return LegacyLuaOperation::SpeakInHouse;
        case EvtOpcode::SpeakNpc: return LegacyLuaOperation::SpeakNpc;
        case EvtOpcode::MoveToMap: return LegacyLuaOperation::MoveToMap;
        case EvtOpcode::MoveNpc: return LegacyLuaOperation::MoveNpc;
        case EvtOpcode::ChangeEvent: return LegacyLuaOperation::ChangeEvent;
        case EvtOpcode::OpenChest: return LegacyLuaOperation::OpenChest;
        case EvtOpcode::RandomGoTo: return LegacyLuaOperation::RandomJump;
        case EvtOpcode::SummonMonsters: return LegacyLuaOperation::SummonMonsters;
        case EvtOpcode::SummonItem: return LegacyLuaOperation::SummonItem;
        case EvtOpcode::GiveItem: return LegacyLuaOperation::GiveItem;
        case EvtOpcode::CastSpell: return LegacyLuaOperation::CastSpell;
        case EvtOpcode::ShowFace: return LegacyLuaOperation::ShowFace;
        case EvtOpcode::ReceiveDamage: return LegacyLuaOperation::ReceiveDamage;
        case EvtOpcode::SetSnow: return LegacyLuaOperation::SetSnow;
        case EvtOpcode::ShowMovie: return LegacyLuaOperation::ShowMovie;
        case EvtOpcode::SetSprite: return LegacyLuaOperation::SetSprite;
        case EvtOpcode::ChangeDoorState: return LegacyLuaOperation::ChangeDoorState;
        case EvtOpcode::StopAnimation: return LegacyLuaOperation::StopAnimation;
        case EvtOpcode::SetTexture: return LegacyLuaOperation::SetTexture;
        case EvtOpcode::ToggleIndoorLight: return LegacyLuaOperation::ToggleIndoorLight;
        case EvtOpcode::SetFacesBit: return LegacyLuaOperation::SetFacetBit;
        case EvtOpcode::ToggleActorFlag: return LegacyLuaOperation::SetActorFlag;
        case EvtOpcode::ToggleActorGroupFlag: return LegacyLuaOperation::SetActorGroupFlag;
        case EvtOpcode::SetActorGroup: return LegacyLuaOperation::SetActorGroup;
        case EvtOpcode::SetNpcTopic: return LegacyLuaOperation::SetNpcTopic;
        case EvtOpcode::SetNpcGroupNews: return LegacyLuaOperation::SetNpcGroupNews;
        case EvtOpcode::SetNpcGreeting: return LegacyLuaOperation::SetNpcGreeting;
        case EvtOpcode::NpcSetItem: return LegacyLuaOperation::SetNpcItem;
        case EvtOpcode::SetActorItem: return LegacyLuaOperation::SetActorItem;
        case EvtOpcode::CharacterAnimation: return LegacyLuaOperation::CharacterAnimation;
        case EvtOpcode::ForPartyMember: return LegacyLuaOperation::ForPartyMember;
        case EvtOpcode::CheckItemsCount: return LegacyLuaOperation::CheckItemsCount;
        case EvtOpcode::RemoveItems: return LegacyLuaOperation::RemoveItems;
        case EvtOpcode::CheckSkill: return LegacyLuaOperation::CheckSkill;
        case EvtOpcode::IsActorKilled: return LegacyLuaOperation::IsActorKilled;
        case EvtOpcode::CanShowTopicIsActorKilled: return LegacyLuaOperation::IsActorKilledCanShowTopic;
        case EvtOpcode::ChangeGroup: return LegacyLuaOperation::ChangeGroup;
        case EvtOpcode::ChangeGroupAlly: return LegacyLuaOperation::ChangeGroupAlly;
        case EvtOpcode::CheckSeason: return LegacyLuaOperation::CheckSeason;
        case EvtOpcode::ToggleChestFlag: return LegacyLuaOperation::ToggleChestFlag;
        case EvtOpcode::InputString: return LegacyLuaOperation::InputString;
        case EvtOpcode::PressAnyKey: return LegacyLuaOperation::PressAnyKey;
        case EvtOpcode::SpecialJump: return LegacyLuaOperation::SpecialJump;
        case EvtOpcode::IsTotalBountyHuntingAwardInRange: return LegacyLuaOperation::IsTotalBountyHuntingAwardInRange;
        case EvtOpcode::IsNpcInParty: return LegacyLuaOperation::IsNpcInParty;
        case EvtOpcode::Invalid: break;
    }

    return LegacyLuaOperation::Unknown;
}

bool isCanShowTopicEvent(const EvtEvent &event)
{
    for (const EvtInstruction &instruction : event.instructions)
    {
        if (instruction.opcode == EvtOpcode::OnCanShowDialogItemCmp
            || instruction.opcode == EvtOpcode::SetCanShowDialogItem
            || instruction.opcode == EvtOpcode::EndCanShowDialogItem
            || instruction.opcode == EvtOpcode::CanShowTopicIsActorKilled)
        {
            return true;
        }
    }

    return false;
}

bool hasOnLoadTrigger(const EvtEvent &event)
{
    return std::any_of(
        event.instructions.begin(),
        event.instructions.end(),
        [](const EvtInstruction &instruction)
        {
            return instruction.opcode == EvtOpcode::OnMapReload;
        });
}

std::optional<std::string> resolveInstructionText(
    const EvtInstruction &instruction,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups)
{
    if (instruction.opcode == EvtOpcode::ShowMessage || instruction.opcode == EvtOpcode::StatusText)
    {
        if (instruction.value1)
        {
            std::optional<std::string> text;

            if (*instruction.value1 <= 0xffu)
            {
                text = strTable.get(static_cast<uint8_t>(*instruction.value1));
            }

            if (!text)
            {
                text = lookupText(lookups.npcTexts, *instruction.value1);
            }

            if (text)
            {
                return *text;
            }
        }
    }

    if (instruction.opcode == EvtOpcode::MouseOver && instruction.textId)
    {
        const std::optional<std::string> text = strTable.get(*instruction.textId);

        if (text && !text->empty())
        {
            return *text;
        }
    }

    if (instruction.opcode == EvtOpcode::SpeakInHouse && instruction.value1)
    {
        const std::optional<std::string> houseName = lookupText(lookups.houseNames, *instruction.value1);

        if (houseName && !houseName->empty())
        {
            return *houseName;
        }
    }

    if (instruction.stringValue && !instruction.stringValue->empty())
    {
        return *instruction.stringValue;
    }

    return std::nullopt;
}

LegacyLuaInstruction decodeInstruction(
    uint16_t eventId,
    const EvtInstruction &instruction,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups)
{
    LegacyLuaInstruction decoded = {};
    decoded.eventId = eventId;
    decoded.step = instruction.step;
    decoded.operation = mapOperation(instruction.opcode);
    decoded.jumpTargetStep = instruction.targetStep;

    if (instruction.value1)
    {
        decoded.arguments.push_back(*instruction.value1);
    }

    if (instruction.value2)
    {
        decoded.arguments.push_back(*instruction.value2);
    }

    if (instruction.value3)
    {
        decoded.arguments.push_back(*instruction.value3);
    }

    if (instruction.booleanValue)
    {
        decoded.arguments.push_back(*instruction.booleanValue);
    }

    decoded.text = resolveInstructionText(instruction, strTable, lookups);

    if (decoded.operation == LegacyLuaOperation::ForPartyMember)
    {
        decoded.arguments.clear();

        for (uint8_t value : instruction.listValues)
        {
            decoded.arguments.push_back(value);
        }
    }
    else if (decoded.operation == LegacyLuaOperation::RandomJump)
    {
        decoded.arguments.clear();

        for (uint8_t value : instruction.listValues)
        {
            if (value != 0)
            {
                decoded.arguments.push_back(value);
            }
        }
    }

    if (decoded.operation == LegacyLuaOperation::SummonMonsters)
    {
        const std::optional<uint8_t> typeIndex = readPayloadValue<uint8_t>(instruction.rawPayload, 0);
        const std::optional<uint8_t> level = readPayloadValue<uint8_t>(instruction.rawPayload, 1);
        const std::optional<uint8_t> count = readPayloadValue<uint8_t>(instruction.rawPayload, 2);
        const std::optional<int32_t> x = readPayloadValue<int32_t>(instruction.rawPayload, 3);
        const std::optional<int32_t> y = readPayloadValue<int32_t>(instruction.rawPayload, 7);
        const std::optional<int32_t> z = readPayloadValue<int32_t>(instruction.rawPayload, 11);
        const std::optional<uint32_t> group = readPayloadValue<uint32_t>(instruction.rawPayload, 15);
        const std::optional<uint32_t> uniqueNameId = readPayloadValue<uint32_t>(instruction.rawPayload, 19);

        if (typeIndex && level && count && x && y && z && group && uniqueNameId)
        {
            decoded.arguments = {
                *typeIndex,
                *level,
                *count,
                static_cast<uint32_t>(*x),
                static_cast<uint32_t>(*y),
                static_cast<uint32_t>(*z),
                *group,
                *uniqueNameId
            };
        }
    }
    else if (decoded.operation == LegacyLuaOperation::SummonItem)
    {
        const std::optional<uint32_t> objectId = readPayloadValue<uint32_t>(instruction.rawPayload, 0);
        const std::optional<int32_t> x = readPayloadValue<int32_t>(instruction.rawPayload, 4);
        const std::optional<int32_t> y = readPayloadValue<int32_t>(instruction.rawPayload, 8);
        const std::optional<int32_t> z = readPayloadValue<int32_t>(instruction.rawPayload, 12);
        const std::optional<int32_t> speed = readPayloadValue<int32_t>(instruction.rawPayload, 16);
        const std::optional<uint8_t> count = readPayloadValue<uint8_t>(instruction.rawPayload, 20);
        const std::optional<uint8_t> randomRotate = readPayloadValue<uint8_t>(instruction.rawPayload, 21);

        if (objectId && x && y && z && speed && count && randomRotate)
        {
            decoded.arguments = {
                *objectId,
                static_cast<uint32_t>(*x),
                static_cast<uint32_t>(*y),
                static_cast<uint32_t>(*z),
                static_cast<uint32_t>(*speed),
                *count,
                *randomRotate
            };
        }
    }
    else if (decoded.operation == LegacyLuaOperation::GiveItem)
    {
        const std::optional<uint8_t> treasureLevel = readPayloadValue<uint8_t>(instruction.rawPayload, 0);
        const std::optional<uint8_t> treasureType = readPayloadValue<uint8_t>(instruction.rawPayload, 1);
        const std::optional<uint32_t> itemId = readPayloadValue<uint32_t>(instruction.rawPayload, 2);

        if (treasureLevel && treasureType && itemId)
        {
            decoded.arguments = {
                *treasureLevel,
                *treasureType,
                *itemId,
            };
        }
    }
    else if (decoded.operation == LegacyLuaOperation::IsActorKilled
        || decoded.operation == LegacyLuaOperation::IsActorKilledCanShowTopic)
    {
        const std::optional<uint8_t> policy = readPayloadValue<uint8_t>(instruction.rawPayload, 0);
        const std::optional<uint32_t> param = readPayloadValue<uint32_t>(instruction.rawPayload, 1);
        const std::optional<uint8_t> count = readPayloadValue<uint8_t>(instruction.rawPayload, 5);
        const std::optional<uint8_t> invisibleAsDead = readPayloadValue<uint8_t>(instruction.rawPayload, 6);
        const std::optional<uint8_t> jump = readPayloadValue<uint8_t>(instruction.rawPayload, 7);

        if (policy && param && count && invisibleAsDead)
        {
            decoded.arguments = {*policy, *param, *count, *invisibleAsDead};
        }

        if (jump)
        {
            decoded.jumpTargetStep = *jump;
        }
    }
    else if (decoded.operation == LegacyLuaOperation::CastSpell)
    {
        const std::optional<uint8_t> spellId = readPayloadValue<uint8_t>(instruction.rawPayload, 0);
        const std::optional<uint8_t> skillMasteryRaw = readPayloadValue<uint8_t>(instruction.rawPayload, 1);
        const std::optional<uint8_t> skillLevel = readPayloadValue<uint8_t>(instruction.rawPayload, 2);
        const std::optional<int32_t> fromX = readPayloadValue<int32_t>(instruction.rawPayload, 3);
        const std::optional<int32_t> fromY = readPayloadValue<int32_t>(instruction.rawPayload, 7);
        const std::optional<int32_t> fromZ = readPayloadValue<int32_t>(instruction.rawPayload, 11);
        const std::optional<int32_t> toX = readPayloadValue<int32_t>(instruction.rawPayload, 15);
        const std::optional<int32_t> toY = readPayloadValue<int32_t>(instruction.rawPayload, 19);
        const std::optional<int32_t> toZ = readPayloadValue<int32_t>(instruction.rawPayload, 23);

        if (spellId && skillLevel && skillMasteryRaw && fromX && fromY && fromZ && toX && toY && toZ)
        {
            decoded.arguments = {
                *spellId,
                *skillLevel,
                static_cast<uint32_t>(*skillMasteryRaw) + 1,
                static_cast<uint32_t>(*fromX),
                static_cast<uint32_t>(*fromY),
                static_cast<uint32_t>(*fromZ),
                static_cast<uint32_t>(*toX),
                static_cast<uint32_t>(*toY),
                static_cast<uint32_t>(*toZ)
            };
        }
    }
    else if (decoded.operation == LegacyLuaOperation::MoveToMap)
    {
        const std::optional<int32_t> x = readPayloadValue<int32_t>(instruction.rawPayload, 0);
        const std::optional<int32_t> y = readPayloadValue<int32_t>(instruction.rawPayload, 4);
        const std::optional<int32_t> z = readPayloadValue<int32_t>(instruction.rawPayload, 8);
        const std::optional<int32_t> yaw = readPayloadValue<int32_t>(instruction.rawPayload, 12);
        const std::optional<int32_t> pitch = readPayloadValue<int32_t>(instruction.rawPayload, 16);
        const std::optional<int32_t> zSpeed = readPayloadValue<int32_t>(instruction.rawPayload, 20);
        const std::optional<uint8_t> houseId = readPayloadValue<uint8_t>(instruction.rawPayload, 24);
        const std::optional<uint8_t> exitPicId = readPayloadValue<uint8_t>(instruction.rawPayload, 25);

        if (x && y && z && yaw && pitch && zSpeed && houseId && exitPicId)
        {
            decoded.arguments = {
                static_cast<uint32_t>(*x),
                static_cast<uint32_t>(*y),
                static_cast<uint32_t>(*z),
                static_cast<uint32_t>(*yaw),
                static_cast<uint32_t>(*pitch),
                static_cast<uint32_t>(*zSpeed),
                *houseId,
                *exitPicId
            };
        }
    }

    return decoded;
}

std::vector<LegacyLuaEvent> decodeEvents(
    const EvtProgram &evtProgram,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups)
{
    std::vector<LegacyLuaEvent> decodedEvents;
    decodedEvents.reserve(evtProgram.getEvents().size());

    for (const EvtEvent &event : evtProgram.getEvents())
    {
        LegacyLuaEvent decodedEvent = {};
        decodedEvent.eventId = event.eventId;
        decodedEvent.instructions.reserve(event.instructions.size());

        for (const EvtInstruction &instruction : event.instructions)
        {
            decodedEvent.instructions.push_back(
                decodeInstruction(event.eventId, instruction, strTable, lookups));
        }

        decodedEvents.push_back(std::move(decodedEvent));
    }

    return decodedEvents;
}

std::optional<std::string> getLegacyHint(
    const EvtEvent &event,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups)
{
    bool mouseOverFound = false;

    for (const EvtInstruction &instruction : event.instructions)
    {
        if (instruction.opcode == EvtOpcode::MouseOver)
        {
            mouseOverFound = true;

            if (instruction.textId)
            {
                const std::optional<std::string> text = strTable.get(*instruction.textId);

                if (text && !text->empty())
                {
                    return text;
                }
            }
        }

        if (mouseOverFound && instruction.opcode == EvtOpcode::SpeakInHouse && instruction.value1)
        {
            const std::optional<std::string> houseName = lookupText(lookups.houseNames, *instruction.value1);

            if (houseName && !houseName->empty())
            {
                return houseName;
            }
        }
    }

    return std::nullopt;
}

std::optional<std::string> summarizeLegacyEvent(
    const EvtEvent &event,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups)
{
    std::ostringstream stream;
    stream << event.eventId << ":";

    const std::optional<std::string> hint = getLegacyHint(event, strTable, lookups);

    if (hint && !hint->empty())
    {
        stream << " " << luaQuoted(*hint);
    }

    if (!event.instructions.empty())
    {
        stream << " ";
    }

    const size_t instructionCount = std::min<size_t>(event.instructions.size(), 3);

    for (size_t instructionIndex = 0; instructionIndex < instructionCount; ++instructionIndex)
    {
        if (instructionIndex > 0)
        {
            stream << ",";
        }

        stream << EvtProgram::opcodeName(event.instructions[instructionIndex].opcode);
    }

    if (event.instructions.size() > instructionCount)
    {
        stream << ",...";
    }

    return stream.str();
}

std::vector<uint32_t> getOpenedChestIds(const EvtEvent &event)
{
    std::vector<uint32_t> chestIds;

    for (const EvtInstruction &instruction : event.instructions)
    {
        if (instruction.opcode != EvtOpcode::OpenChest || !instruction.value1)
        {
            continue;
        }

        chestIds.push_back(*instruction.value1);
    }

    return chestIds;
}

void collectSetTextureNames(const EvtProgram &evtProgram, std::vector<std::string> &textureNames)
{
    for (const EvtEvent &event : evtProgram.getEvents())
    {
        for (const EvtInstruction &instruction : event.instructions)
        {
            if (instruction.opcode != EvtOpcode::SetTexture || !instruction.stringValue || instruction.stringValue->empty())
            {
                continue;
            }

            textureNames.push_back(*instruction.stringValue);
        }
    }

    sortAndUnique(textureNames);
}

void collectSetSpriteNames(const EvtProgram &evtProgram, std::vector<std::string> &spriteNames)
{
    for (const EvtEvent &event : evtProgram.getEvents())
    {
        for (const EvtInstruction &instruction : event.instructions)
        {
            if (instruction.opcode != EvtOpcode::SetSprite || !instruction.stringValue || instruction.stringValue->empty())
            {
                continue;
            }

            spriteNames.push_back(*instruction.stringValue);
        }
    }

    sortAndUnique(spriteNames);
}

void collectCastSpellIds(const EvtProgram &evtProgram, std::vector<uint32_t> &spellIds)
{
    for (const EvtEvent &event : evtProgram.getEvents())
    {
        for (const EvtInstruction &instruction : event.instructions)
        {
            if (instruction.opcode != EvtOpcode::CastSpell)
            {
                continue;
            }

            const std::optional<uint8_t> spellId = readPayloadValue<uint8_t>(instruction.rawPayload, 0);

            if (spellId)
            {
                spellIds.push_back(*spellId);
            }
        }
    }

    sortAndUnique(spellIds);
}

bool isIgnoredNormalOperation(LegacyLuaOperation operation);

std::vector<uint8_t> collectNormalEventSteps(const LegacyLuaEvent &event)
{
    std::vector<uint8_t> steps;

    for (const LegacyLuaInstruction &instruction : event.instructions)
    {
        if (isIgnoredNormalOperation(instruction.operation))
        {
            continue;
        }

        if (steps.empty() || steps.back() != instruction.step)
        {
            steps.push_back(instruction.step);
        }
    }

    return steps;
}

bool isCanShowTopicOperation(LegacyLuaOperation operation)
{
    switch (operation)
    {
        case LegacyLuaOperation::ForPartyMember:
        case LegacyLuaOperation::CompareCanShowTopic:
        case LegacyLuaOperation::SetCanShowTopic:
        case LegacyLuaOperation::EndCanShowTopic:
        case LegacyLuaOperation::IsActorKilledCanShowTopic:
        case LegacyLuaOperation::Jump:
        case LegacyLuaOperation::Exit:
            return true;

        default:
            return false;
    }
}

std::vector<uint8_t> collectCanShowTopicSteps(const LegacyLuaEvent &event)
{
    std::vector<uint8_t> steps;

    for (const LegacyLuaInstruction &instruction : event.instructions)
    {
        if (!isCanShowTopicOperation(instruction.operation))
        {
            continue;
        }

        if (steps.empty() || steps.back() != instruction.step)
        {
            steps.push_back(instruction.step);
        }
    }

    return steps;
}

bool isIgnoredNormalOperation(LegacyLuaOperation operation)
{
    switch (operation)
    {
        case LegacyLuaOperation::TriggerMouseOver:
        case LegacyLuaOperation::TriggerOnLoadMap:
        case LegacyLuaOperation::TriggerOnLeaveMap:
        case LegacyLuaOperation::TriggerOnTimer:
        case LegacyLuaOperation::TriggerOnLongTimer:
        case LegacyLuaOperation::TriggerOnDateTimer:
        case LegacyLuaOperation::EnableDateTimer:
        case LegacyLuaOperation::CompareCanShowTopic:
        case LegacyLuaOperation::SetCanShowTopic:
        case LegacyLuaOperation::EndCanShowTopic:
        case LegacyLuaOperation::LocationName:
        case LegacyLuaOperation::Unknown:
        case LegacyLuaOperation::IsActorKilledCanShowTopic:
            return true;

        default:
            return false;
    }
}

bool isReadableCompareOperation(LegacyLuaOperation operation)
{
    switch (operation)
    {
        case LegacyLuaOperation::Compare:
        case LegacyLuaOperation::CheckItemsCount:
        case LegacyLuaOperation::CheckSkill:
        case LegacyLuaOperation::IsActorKilled:
        case LegacyLuaOperation::CheckSeason:
        case LegacyLuaOperation::IsTotalBountyHuntingAwardInRange:
        case LegacyLuaOperation::IsNpcInParty:
            return true;

        default:
            return false;
    }
}

bool isReadableControlFlowOperation(LegacyLuaOperation operation)
{
    return operation == LegacyLuaOperation::Exit
        || operation == LegacyLuaOperation::Jump
        || operation == LegacyLuaOperation::RandomJump
        || operation == LegacyLuaOperation::InputString
        || operation == LegacyLuaOperation::PressAnyKey
        || isReadableCompareOperation(operation);
}

struct NormalStepInfo
{
    std::vector<const LegacyLuaInstruction *> actions;
    const LegacyLuaInstruction *terminalInstruction = nullptr;
};

bool isNoOpEvent(const LegacyLuaEvent &event)
{
    for (const LegacyLuaInstruction &instruction : event.instructions)
    {
        if (instruction.operation == LegacyLuaOperation::Exit || isIgnoredNormalOperation(instruction.operation))
        {
            continue;
        }

        return false;
    }

    return true;
}

std::string buildGeneratedEventTitle(
    const EvtEvent &event,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups)
{
    const auto explicitTitleIterator = lookups.eventTitles.find(event.eventId);

    if (explicitTitleIterator != lookups.eventTitles.end() && !explicitTitleIterator->second.empty())
    {
        return explicitTitleIterator->second;
    }

    const std::optional<std::string> hint = getLegacyHint(event, strTable, lookups);

    if (hint && !hint->empty())
    {
        return *hint;
    }

    return "Legacy event " + std::to_string(event.eventId);
}

void emitIndentedLineWithComment(
    std::ostringstream &stream,
    std::string_view line,
    const std::optional<std::string> &comment,
    int indentLevel)
{
    for (int indentIndex = 0; indentIndex < indentLevel; ++indentIndex)
    {
        stream << "    ";
    }

    stream << line;

    if (comment && !comment->empty())
    {
        stream << " -- " << sanitizeLuaCommentText(*comment);
    }

    stream << '\n';
}

std::optional<std::string> resolveSummonItemComment(uint32_t payload, const LegacyLuaExportLookups &lookups)
{
    std::optional<std::string> comment = lookupText(lookups.objectPayloadNames, payload);

    if (!comment)
    {
        comment = lookupText(lookups.itemNames, payload);
    }

    return comment;
}

bool formatGiveItemCall(
    const LegacyLuaInstruction &instruction,
    const LegacyLuaExportLookups &lookups,
    std::string &expression,
    std::optional<std::string> &comment)
{
    if (instruction.arguments.size() < 3)
    {
        return false;
    }

    const uint32_t treasureLevel = instruction.arguments[0];
    const uint32_t treasureType = instruction.arguments[1];
    const uint32_t itemId = instruction.arguments[2];
    std::ostringstream line;
    line << "evt.GiveItem(" << treasureLevel << ", " << formatRandomItemType(treasureType);

    if (itemId != 0)
    {
        line << ", " << itemId;
        comment = lookupText(lookups.itemNames, itemId);
    }
    else
    {
        comment = std::nullopt;
    }

    line << ")";
    expression = line.str();
    return true;
}

void emitNpcGroupNewsComments(
    std::ostringstream &stream,
    uint32_t groupId,
    uint32_t newsId,
    const LegacyLuaExportLookups &lookups,
    int indentLevel)
{
    const std::optional<std::string> groupName = lookupText(lookups.npcGroupNames, groupId);
    const std::optional<std::string> newsText = lookupText(lookups.npcNewsTexts, newsId);

    if (groupName && !groupName->empty())
    {
        for (int indentIndex = 0; indentIndex < indentLevel; ++indentIndex)
        {
            stream << "    ";
        }

        stream << "-- NPC group " << groupId << " \"" << sanitizeLuaCommentText(*groupName)
               << "\" -> news " << newsId << '\n';
    }

    if (newsText && !newsText->empty())
    {
        for (int indentIndex = 0; indentIndex < indentLevel; ++indentIndex)
        {
            stream << "    ";
        }

        stream << "-- \"" << sanitizeLuaCommentText(*newsText) << "\"\n";
    }
}

void emitEventRegistrationHeader(
    std::ostringstream &stream,
    std::string_view registerFunction,
    uint16_t eventId,
    const std::string &title,
    const std::optional<std::string> &hint);

std::vector<const LegacyLuaInstruction *> collectMeaningfulInstructionsForStep(
    const LegacyLuaEvent &event,
    uint8_t step)
{
    std::vector<const LegacyLuaInstruction *> instructions;

    for (const LegacyLuaInstruction &instruction : event.instructions)
    {
        if (instruction.step != step || isIgnoredNormalOperation(instruction.operation))
        {
            continue;
        }

        instructions.push_back(&instruction);
    }

    return instructions;
}

std::vector<const LegacyLuaInstruction *> collectMeaningfulInstructionsForCanShowTopicStep(
    const LegacyLuaEvent &event,
    uint8_t step)
{
    std::vector<const LegacyLuaInstruction *> instructions;

    for (const LegacyLuaInstruction &instruction : event.instructions)
    {
        if (instruction.step != step)
        {
            continue;
        }

        switch (instruction.operation)
        {
            case LegacyLuaOperation::ForPartyMember:
            case LegacyLuaOperation::CompareCanShowTopic:
            case LegacyLuaOperation::SetCanShowTopic:
            case LegacyLuaOperation::EndCanShowTopic:
            case LegacyLuaOperation::IsActorKilledCanShowTopic:
            case LegacyLuaOperation::Jump:
            case LegacyLuaOperation::Exit:
                instructions.push_back(&instruction);
                break;

            default:
                break;
        }
    }

    return instructions;
}

struct CanShowTopicStepInfo
{
    std::vector<const LegacyLuaInstruction *> actions;
    const LegacyLuaInstruction *terminalInstruction = nullptr;
};

bool decomposeNormalStep(
    const LegacyLuaEvent &event,
    uint8_t step,
    NormalStepInfo &stepInfo)
{
    const std::vector<const LegacyLuaInstruction *> instructions = collectMeaningfulInstructionsForStep(event, step);

    if (instructions.empty())
    {
        return true;
    }

    for (size_t instructionIndex = 0; instructionIndex < instructions.size(); ++instructionIndex)
    {
        const LegacyLuaInstruction *instruction = instructions[instructionIndex];
        const bool isLastInstruction = instructionIndex + 1 == instructions.size();

        if (isReadableControlFlowOperation(instruction->operation))
        {
            if (!isLastInstruction)
            {
                return false;
            }

            stepInfo.terminalInstruction = instruction;
            return true;
        }

        stepInfo.actions.push_back(instruction);
    }

    return true;
}

bool decomposeCanShowTopicStep(
    const LegacyLuaEvent &event,
    uint8_t step,
    CanShowTopicStepInfo &stepInfo)
{
    const std::vector<const LegacyLuaInstruction *> instructions =
        collectMeaningfulInstructionsForCanShowTopicStep(event, step);

    if (instructions.empty())
    {
        return true;
    }

    for (size_t instructionIndex = 0; instructionIndex < instructions.size(); ++instructionIndex)
    {
        const LegacyLuaInstruction *instruction = instructions[instructionIndex];
        const bool isLastInstruction = instructionIndex + 1 == instructions.size();

        if (instruction->operation == LegacyLuaOperation::CompareCanShowTopic
            || instruction->operation == LegacyLuaOperation::IsActorKilledCanShowTopic
            || instruction->operation == LegacyLuaOperation::EndCanShowTopic
            || instruction->operation == LegacyLuaOperation::Jump
            || instruction->operation == LegacyLuaOperation::Exit)
        {
            if (!isLastInstruction)
            {
                return false;
            }

            stepInfo.terminalInstruction = instruction;
            return true;
        }

        stepInfo.actions.push_back(instruction);
    }

    return true;
}

std::optional<size_t> findStepIndex(const std::vector<uint8_t> &steps, uint8_t step)
{
    for (size_t index = 0; index < steps.size(); ++index)
    {
        if (steps[index] == step)
        {
            return index;
        }
    }

    return std::nullopt;
}

std::optional<uint8_t> nextStepAfter(const std::vector<uint8_t> &steps, uint8_t step)
{
    const std::optional<size_t> index = findStepIndex(steps, step);

    if (!index || *index + 1 >= steps.size())
    {
        return std::nullopt;
    }

    return steps[*index + 1];
}

bool isImmediateReturnPath(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> step)
{
    std::vector<uint8_t> visited;

    while (step)
    {
        if (std::find(visited.begin(), visited.end(), *step) != visited.end())
        {
            return false;
        }

        visited.push_back(*step);
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo))
        {
            return false;
        }

        if (stepInfo.actions.empty() && !stepInfo.terminalInstruction)
        {
            step = nextStepAfter(steps, *step);
            continue;
        }

        if (!stepInfo.actions.empty() || !stepInfo.terminalInstruction)
        {
            return false;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::Exit)
        {
            return true;
        }

        if (instruction.operation == LegacyLuaOperation::Jump && instruction.jumpTargetStep)
        {
            step = instruction.jumpTargetStep;
            continue;
        }

        return false;
    }

    return true;
}

struct SimpleBranchArm
{
    std::vector<const LegacyLuaInstruction *> actions;
    std::optional<uint8_t> continuation;
    bool returns = false;
};

const LegacyLuaInstruction *findInstructionByStep(const LegacyLuaEvent &event, uint8_t step)
{
    for (const LegacyLuaInstruction &instruction : event.instructions)
    {
        if (instruction.step == step)
        {
            return &instruction;
        }
    }

    return nullptr;
}

bool resolveSignificantStep(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> step,
    std::optional<uint8_t> &resolvedStep)
{
    std::vector<uint8_t> visited;

    while (step)
    {
        if (std::find(visited.begin(), visited.end(), *step) != visited.end())
        {
            return false;
        }

        visited.push_back(*step);
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo))
        {
            return false;
        }

        if (stepInfo.actions.empty() && !stepInfo.terminalInstruction)
        {
            step = nextStepAfter(steps, *step);
            continue;
        }

        if (!stepInfo.actions.empty() || !stepInfo.terminalInstruction)
        {
            resolvedStep = *step;
            return true;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::Jump)
        {
            if (!instruction.jumpTargetStep)
            {
                return false;
            }

            step = instruction.jumpTargetStep;
            continue;
        }

        resolvedStep = *step;
        return true;
    }

    resolvedStep = std::nullopt;
    return true;
}

bool resolvesDirectlyToStep(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep,
    std::optional<uint8_t> targetStep)
{
    if (!targetStep)
    {
        return false;
    }

    std::optional<uint8_t> resolvedStep;

    if (!resolveSignificantStep(event, steps, startStep, resolvedStep))
    {
        return false;
    }

    return resolvedStep && *resolvedStep == *targetStep;
}

std::vector<uint8_t> collectSuccessorSteps(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t step)
{
    NormalStepInfo stepInfo;

    if (!decomposeNormalStep(event, step, stepInfo))
    {
        return {};
    }

    if (stepInfo.actions.empty() && !stepInfo.terminalInstruction)
    {
        const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);
        return nextStep ? std::vector<uint8_t>{*nextStep} : std::vector<uint8_t>{};
    }

    if (!stepInfo.terminalInstruction)
    {
        const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);
        return nextStep ? std::vector<uint8_t>{*nextStep} : std::vector<uint8_t>{};
    }

    const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

    switch (instruction.operation)
    {
        case LegacyLuaOperation::Exit:
            return {};

        case LegacyLuaOperation::Jump:
            return instruction.jumpTargetStep ? std::vector<uint8_t>{*instruction.jumpTargetStep} : std::vector<uint8_t>{};

        case LegacyLuaOperation::Compare:
        case LegacyLuaOperation::CheckItemsCount:
        case LegacyLuaOperation::CheckSkill:
        case LegacyLuaOperation::IsActorKilled:
        case LegacyLuaOperation::CheckSeason:
        case LegacyLuaOperation::IsTotalBountyHuntingAwardInRange:
        case LegacyLuaOperation::IsNpcInParty:
        {
            std::vector<uint8_t> successors;

            if (instruction.jumpTargetStep)
            {
                successors.push_back(*instruction.jumpTargetStep);
            }

            const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);

            if (nextStep && std::find(successors.begin(), successors.end(), *nextStep) == successors.end())
            {
                successors.push_back(*nextStep);
            }

            return successors;
        }

        case LegacyLuaOperation::RandomJump:
        {
            std::vector<uint8_t> successors;

            for (uint32_t argument : instruction.arguments)
            {
                const uint8_t successor = static_cast<uint8_t>(argument);

                if (std::find(successors.begin(), successors.end(), successor) == successors.end())
                {
                    successors.push_back(successor);
                }
            }

            return successors;
        }

        default:
        {
            const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);
            return nextStep ? std::vector<uint8_t>{*nextStep} : std::vector<uint8_t>{};
        }
    }
}

std::vector<uint8_t> collectReachableSteps(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep)
{
    std::vector<uint8_t> reachable;

    if (!startStep)
    {
        return reachable;
    }

    std::vector<uint8_t> stack = {*startStep};

    while (!stack.empty())
    {
        const uint8_t step = stack.back();
        stack.pop_back();

        if (std::find(reachable.begin(), reachable.end(), step) != reachable.end())
        {
            continue;
        }

        reachable.push_back(step);

        for (uint8_t successor : collectSuccessorSteps(event, steps, step))
        {
            if (std::find(reachable.begin(), reachable.end(), successor) == reachable.end())
            {
                stack.push_back(successor);
            }
        }
    }

    return reachable;
}

std::optional<uint8_t> findCommonJoinStepForBranches(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    const std::vector<uint8_t> &branchStarts);

std::optional<uint8_t> findCommonJoinStep(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> trueBranchStart,
    std::optional<uint8_t> falseBranchStart)
{
    if (!trueBranchStart || !falseBranchStart)
    {
        return std::nullopt;
    }

    return findCommonJoinStepForBranches(event, steps, {*trueBranchStart, *falseBranchStart});
}

bool allPathsLeadToStepRecursive(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t step,
    uint8_t targetStep,
    std::vector<uint8_t> &activeSteps,
    std::map<uint8_t, bool> &memo)
{
    if (step == targetStep)
    {
        return true;
    }

    const auto memoIterator = memo.find(step);

    if (memoIterator != memo.end())
    {
        return memoIterator->second;
    }

    if (std::find(activeSteps.begin(), activeSteps.end(), step) != activeSteps.end())
    {
        memo[step] = false;
        return false;
    }

    activeSteps.push_back(step);
    const std::vector<uint8_t> successors = collectSuccessorSteps(event, steps, step);

    if (successors.empty())
    {
        activeSteps.pop_back();
        memo[step] = false;
        return false;
    }

    for (uint8_t successor : successors)
    {
        if (!allPathsLeadToStepRecursive(event, steps, successor, targetStep, activeSteps, memo))
        {
            activeSteps.pop_back();
            memo[step] = false;
            return false;
        }
    }

    activeSteps.pop_back();
    memo[step] = true;
    return true;
}

bool allPathsLeadToStep(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep,
    uint8_t targetStep)
{
    if (!startStep)
    {
        return false;
    }

    std::vector<uint8_t> activeSteps;
    std::map<uint8_t, bool> memo;
    return allPathsLeadToStepRecursive(event, steps, *startStep, targetStep, activeSteps, memo);
}

std::optional<uint8_t> findCommonJoinStepForBranches(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    const std::vector<uint8_t> &branchStarts)
{
    if (branchStarts.empty())
    {
        return std::nullopt;
    }

    for (uint8_t step : steps)
    {
        bool isJoinStep = true;

        for (uint8_t branchStart : branchStarts)
        {
            if (!allPathsLeadToStep(event, steps, branchStart, step))
            {
                isJoinStep = false;
                break;
            }
        }

        if (isJoinStep)
        {
            return step;
        }
    }

    return std::nullopt;
}

bool formatReadableConditionInstruction(
    const LegacyLuaInstruction &instruction,
    const LegacyLuaExportLookups &lookups,
    std::string &condition,
    std::optional<std::string> &comment)
{
    switch (instruction.operation)
    {
        case LegacyLuaOperation::Compare:
        case LegacyLuaOperation::CompareCanShowTopic:
        {
            if (instruction.arguments.size() < 2)
            {
                return false;
            }

            const FormattedSelector selector = formatSelector(instruction.arguments[0]);
            condition = formatCompareExpression(selector, instruction.arguments[1]);
            comment = resolveSelectorComment(selector, lookups);
            return true;
        }

        case LegacyLuaOperation::CheckItemsCount:
        {
            if (instruction.arguments.size() < 2)
            {
                return false;
            }

            const FormattedSelector selector = formatSelector(instruction.arguments[0]);
            condition = "evt.CheckItemsCount(" + selector.expression + ", "
                + std::to_string(instruction.arguments[1]) + ")";
            comment = resolveSelectorComment(selector, lookups);
            return true;
        }

        case LegacyLuaOperation::CheckSkill:
            if (instruction.arguments.size() < 3)
            {
                return false;
            }

            condition = "evt.CheckSkill(" + std::to_string(instruction.arguments[0]) + ", "
                + std::to_string(instruction.arguments[1]) + ", "
                + std::to_string(instruction.arguments[2]) + ")";
            comment = std::nullopt;
            return true;

        case LegacyLuaOperation::IsActorKilled:
        case LegacyLuaOperation::IsActorKilledCanShowTopic:
            if (instruction.arguments.size() < 4)
            {
                return false;
            }

            condition = "evt.CheckMonstersKilled(" + std::to_string(instruction.arguments[0]) + ", "
                + std::to_string(instruction.arguments[1]) + ", "
                + std::to_string(instruction.arguments[2]) + ", "
                + (instruction.arguments[3] != 0 ? std::string("true") : std::string("false")) + ")";
            comment = std::nullopt;
            return true;

        case LegacyLuaOperation::CheckSeason:
            if (instruction.arguments.empty())
            {
                return false;
            }

            condition = "evt.CheckSeason(" + std::to_string(instruction.arguments[0]) + ")";
            comment = std::nullopt;
            return true;

        case LegacyLuaOperation::IsTotalBountyHuntingAwardInRange:
            if (instruction.arguments.size() < 2)
            {
                return false;
            }

            condition = "evt.IsTotalBountyInRange(" + std::to_string(static_cast<int32_t>(instruction.arguments[0])) + ", "
                + std::to_string(static_cast<int32_t>(instruction.arguments[1])) + ")";
            comment = std::nullopt;
            return true;

        case LegacyLuaOperation::IsNpcInParty:
            if (instruction.arguments.empty())
            {
                return false;
            }

            condition = "evt._IsNpcInParty(" + std::to_string(instruction.arguments[0]) + ")";
            comment = std::nullopt;
            return true;

        default:
            return false;
    }
}

bool emitReadableActionInstruction(
    std::ostringstream &stream,
    const LegacyLuaInstruction &instruction,
    const LegacyLuaExportLookups &lookups,
    int indentLevel)
{
    switch (instruction.operation)
    {
        case LegacyLuaOperation::PlaySound:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.PlaySound(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[1])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[2])) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::ForPartyMember:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ForPlayer(" + formatPartySelector(instruction.arguments[0]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::Add:
            if (instruction.arguments.size() >= 2)
            {
                const FormattedSelector selector = formatSelector(instruction.arguments[0]);
                emitIndentedLineWithComment(
                    stream,
                    formatAddExpression(selector, instruction.arguments[1]),
                    resolveSelectorComment(selector, lookups),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::Subtract:
            if (instruction.arguments.size() >= 2)
            {
                const FormattedSelector selector = formatSelector(instruction.arguments[0]);
                emitIndentedLineWithComment(
                    stream,
                    formatSubtractExpression(selector, instruction.arguments[1]),
                    resolveSelectorComment(selector, lookups),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::Set:
            if (instruction.arguments.size() >= 2)
            {
                const FormattedSelector selector = formatSelector(instruction.arguments[0]);
                emitIndentedLineWithComment(
                    stream,
                    formatSetExpression(selector, instruction.arguments[1]),
                    resolveSelectorComment(selector, lookups),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::RemoveItems:
            if (!instruction.arguments.empty())
            {
                const FormattedSelector selector = formatSelector(instruction.arguments[0]);
                emitIndentedLineWithComment(
                    stream,
                    "evt.RemoveItems(" + selector.expression + ")",
                    resolveSelectorComment(selector, lookups),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::ShowMessage:
            if (instruction.text)
            {
                if (instruction.text->empty())
                {
                    return true;
                }

                emitIndentedLineWithComment(
                    stream,
                    "evt.SimpleMessage(" + luaQuoted(*instruction.text) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "-- Missing legacy show message text " + std::to_string(instruction.arguments[0]),
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::StatusText:
            if (instruction.text)
            {
                if (instruction.text->empty())
                {
                    return true;
                }

                emitIndentedLineWithComment(
                    stream,
                    "evt.StatusText(" + luaQuoted(*instruction.text) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "-- Missing legacy status text " + std::to_string(instruction.arguments[0]),
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SpeakInHouse:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.EnterHouse(" + std::to_string(instruction.arguments[0]) + ")",
                    lookupText(lookups.houseNames, instruction.arguments[0]),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SpeakNpc:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SpeakNPC(" + std::to_string(instruction.arguments[0]) + ")",
                    lookupText(lookups.npcNames, instruction.arguments[0]),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::MoveNpc:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.MoveNPC(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::ChangeEvent:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ChangeEvent(" + std::to_string(instruction.arguments[0]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::OpenChest:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.OpenChest(" + std::to_string(instruction.arguments[0]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::GiveItem:
        {
            std::string expression;
            std::optional<std::string> comment;

            if (formatGiveItemCall(instruction, lookups, expression, comment))
            {
                emitIndentedLineWithComment(
                    stream,
                    expression,
                    comment,
                    indentLevel);
                return true;
            }

            return false;
        }

        case LegacyLuaOperation::MoveToMap:
        {
            if (instruction.arguments.size() < 3)
            {
                return false;
            }

            std::ostringstream line;
            std::optional<std::string> mapComment;
            line << "evt.MoveToMap("
                 << static_cast<int32_t>(instruction.arguments[0]) << ", "
                 << static_cast<int32_t>(instruction.arguments[1]) << ", "
                 << static_cast<int32_t>(instruction.arguments[2]) << ", ";

            line << (instruction.arguments.size() >= 4 ? std::to_string(static_cast<int32_t>(instruction.arguments[3])) : "nil");
            line << ", " << (instruction.arguments.size() >= 5 ? std::to_string(static_cast<int32_t>(instruction.arguments[4])) : "nil");
            line << ", " << (instruction.arguments.size() >= 6 ? std::to_string(static_cast<int32_t>(instruction.arguments[5])) : "nil");
            line << ", " << (instruction.arguments.size() >= 7 ? std::to_string(instruction.arguments[6]) : "nil");
            line << ", " << (instruction.arguments.size() >= 8 ? std::to_string(instruction.arguments[7]) : "nil");

            if (instruction.text && !instruction.text->empty())
            {
                line << ", " << luaQuoted(*instruction.text);
                mapComment = lookupMapName(lookups.mapNamesByFile, *instruction.text);
            }

            line << ")";
            emitIndentedLineWithComment(stream, line.str(), mapComment, indentLevel);
            return true;
        }

        case LegacyLuaOperation::SummonItem:
            if (instruction.arguments.size() >= 7)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SummonItem(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[1])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[2])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[3])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[4])) + ", "
                    + std::to_string(instruction.arguments[5]) + ", "
                    + (instruction.arguments[6] != 0 ? std::string("true") : std::string("false")) + ")",
                    resolveSummonItemComment(instruction.arguments[0], lookups),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SummonMonsters:
            if (instruction.arguments.size() >= 8)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SummonMonsters(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[3])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[4])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[5])) + ", "
                    + std::to_string(instruction.arguments[6]) + ", "
                    + std::to_string(instruction.arguments[7]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::CastSpell:
            if (instruction.arguments.size() >= 9)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.CastSpell(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[3])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[4])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[5])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[6])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[7])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[8])) + ")",
                    lookupText(lookups.spellNames, instruction.arguments[0]),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetSnow:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetSnow(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::ShowMovie:
            if (instruction.text && !instruction.text->empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ShowMovie(" + luaQuoted(*instruction.text) + ", "
                    + (!instruction.arguments.empty() && instruction.arguments[0] != 0 ? "true" : "false") + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetSprite:
            if (!instruction.arguments.empty())
            {
                std::ostringstream line;
                line << "evt.SetSprite(" << instruction.arguments[0];

                if (instruction.arguments.size() >= 2)
                {
                    line << ", " << instruction.arguments[1];
                }
                else
                {
                    line << ", 0";
                }

                if (instruction.text && !instruction.text->empty())
                {
                    line << ", " << luaQuoted(*instruction.text);
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), std::nullopt, indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::ChangeDoorState:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetDoorState(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::StopAnimation:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.StopDoor(" + std::to_string(instruction.arguments[0]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetTexture:
            if (!instruction.arguments.empty())
            {
                std::ostringstream line;
                line << "evt.SetTexture(" << instruction.arguments[0];

                if (instruction.text && !instruction.text->empty())
                {
                    line << ", " << luaQuoted(*instruction.text);
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), std::nullopt, indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::ToggleIndoorLight:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetLight(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetFacetBit:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetFacetBit(" + std::to_string(instruction.arguments[0]) + ", "
                    + formatFacetBit(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetActorFlag:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetMonsterBit(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetActorGroupFlag:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetMonGroupBit(" + std::to_string(instruction.arguments[0]) + ", "
                    + formatMonsterBit(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetActorGroup:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetMonsterGroup(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetNpcTopic:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetNPCTopic(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetNpcGroupNews:
            if (instruction.arguments.size() >= 2)
            {
                emitNpcGroupNewsComments(stream, instruction.arguments[0], instruction.arguments[1], lookups, indentLevel);
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetNPCGroupNews(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetNpcGreeting:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetNPCGreeting(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetNpcItem:
            if (instruction.arguments.size() >= 2)
            {
                std::ostringstream line;
                line << "evt.SetNPCItem(" << instruction.arguments[0] << ", " << instruction.arguments[1];

                if (instruction.arguments.size() >= 3)
                {
                    line << ", " << instruction.arguments[2];
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), std::nullopt, indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetActorItem:
            if (instruction.arguments.size() >= 2)
            {
                std::ostringstream line;
                line << "evt.SetMonsterItem(" << instruction.arguments[0] << ", " << instruction.arguments[1];

                if (instruction.arguments.size() >= 3)
                {
                    line << ", " << instruction.arguments[2];
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), std::nullopt, indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::CharacterAnimation:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.FaceAnimation(" + formatFaceAnimation(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::Exit:
        case LegacyLuaOperation::Jump:
        case LegacyLuaOperation::Compare:
        case LegacyLuaOperation::RandomJump:
        case LegacyLuaOperation::InputString:
        case LegacyLuaOperation::PressAnyKey:
            return false;

        case LegacyLuaOperation::SpecialJump:
        {
            if (instruction.arguments.empty())
            {
                return false;
            }

            std::ostringstream line;
            line << "evt._SpecialJump(";

            for (size_t argumentIndex = 0; argumentIndex < instruction.arguments.size(); ++argumentIndex)
            {
                if (argumentIndex > 0)
                {
                    line << ", ";
                }

                line << instruction.arguments[argumentIndex];
            }

            line << ")";
            emitIndentedLineWithComment(stream, line.str(), std::nullopt, indentLevel);
            return true;
        }

        default:
            return false;
    }
}

bool canEmitReadableActionInstruction(
    const LegacyLuaInstruction &instruction,
    const LegacyLuaExportLookups &lookups)
{
    std::ostringstream scratch;
    return emitReadableActionInstruction(scratch, instruction, lookups, 0);
}

bool summarizeSimpleBranchArm(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> branchStep,
    const LegacyLuaExportLookups &lookups,
    SimpleBranchArm &summary)
{
    std::optional<uint8_t> significantStep;

    if (!resolveSignificantStep(event, steps, branchStep, significantStep))
    {
        return false;
    }

    if (!significantStep)
    {
        summary.returns = true;
        return true;
    }

    std::vector<uint8_t> visited;

    while (significantStep)
    {
        if (std::find(visited.begin(), visited.end(), *significantStep) != visited.end())
        {
            return false;
        }

        visited.push_back(*significantStep);
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *significantStep, stepInfo))
        {
            return false;
        }

        if (stepInfo.actions.empty() && !stepInfo.terminalInstruction)
        {
            if (!resolveSignificantStep(event, steps, nextStepAfter(steps, *significantStep), significantStep))
            {
                return false;
            }

            continue;
        }

        for (const LegacyLuaInstruction *action : stepInfo.actions)
        {
            if (!canEmitReadableActionInstruction(*action, lookups))
            {
                return false;
            }

            summary.actions.push_back(action);

            if (summary.actions.size() > 16)
            {
                return false;
            }
        }

        if (!stepInfo.terminalInstruction)
        {
            if (!resolveSignificantStep(event, steps, nextStepAfter(steps, *significantStep), significantStep))
            {
                return false;
            }

            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::Exit)
        {
            summary.returns = true;
            return true;
        }

        if (instruction.operation == LegacyLuaOperation::Jump)
        {
            if (!instruction.jumpTargetStep)
            {
                return false;
            }

            if (!resolveSignificantStep(event, steps, instruction.jumpTargetStep, significantStep))
            {
                return false;
            }

            continue;
        }

        if (instruction.operation == LegacyLuaOperation::Compare
            || instruction.operation == LegacyLuaOperation::CheckItemsCount
            || instruction.operation == LegacyLuaOperation::CheckSkill
            || instruction.operation == LegacyLuaOperation::IsActorKilled
            || instruction.operation == LegacyLuaOperation::CheckSeason
            || instruction.operation == LegacyLuaOperation::IsTotalBountyHuntingAwardInRange
            || instruction.operation == LegacyLuaOperation::IsNpcInParty)
        {
            summary.continuation = *significantStep;
            return true;
        }

        return false;
    }

    summary.returns = true;
    return true;
}

bool summarizeBoundedBranchArm(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> branchStep,
    uint8_t stopStep,
    const LegacyLuaExportLookups &lookups,
    SimpleBranchArm &summary)
{
    std::optional<uint8_t> significantStep;

    if (!resolveSignificantStep(event, steps, branchStep, significantStep))
    {
        return false;
    }

    if (!significantStep)
    {
        summary.returns = true;
        return true;
    }

    std::vector<uint8_t> visited;

    while (significantStep)
    {
        if (*significantStep == stopStep)
        {
            summary.continuation = stopStep;
            return true;
        }

        if (std::find(visited.begin(), visited.end(), *significantStep) != visited.end())
        {
            return false;
        }

        visited.push_back(*significantStep);
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *significantStep, stepInfo))
        {
            return false;
        }

        if (stepInfo.actions.empty() && !stepInfo.terminalInstruction)
        {
            if (!resolveSignificantStep(event, steps, nextStepAfter(steps, *significantStep), significantStep))
            {
                return false;
            }

            continue;
        }

        for (const LegacyLuaInstruction *action : stepInfo.actions)
        {
            if (!canEmitReadableActionInstruction(*action, lookups))
            {
                return false;
            }

            summary.actions.push_back(action);

            if (summary.actions.size() > 16)
            {
                return false;
            }
        }

        if (!stepInfo.terminalInstruction)
        {
            if (!resolveSignificantStep(event, steps, nextStepAfter(steps, *significantStep), significantStep))
            {
                return false;
            }

            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::Exit)
        {
            summary.returns = true;
            return true;
        }

        if (instruction.operation == LegacyLuaOperation::Jump)
        {
            if (!instruction.jumpTargetStep)
            {
                return false;
            }

            if (!resolveSignificantStep(event, steps, instruction.jumpTargetStep, significantStep))
            {
                return false;
            }

            continue;
        }

        return false;
    }

    summary.returns = true;
    return true;
}

void emitSimpleBranchArm(
    std::ostringstream &stream,
    const SimpleBranchArm &arm,
    const LegacyLuaExportLookups &lookups,
    int indentLevel)
{
    for (const LegacyLuaInstruction *action : arm.actions)
    {
        emitReadableActionInstruction(stream, *action, lookups, indentLevel);
    }

    if (arm.returns)
    {
        emitIndentedLineWithComment(stream, "return", std::nullopt, indentLevel);
    }
}

std::vector<std::string> splitPreservingLines(const std::string &text)
{
    std::vector<std::string> lines;
    size_t start = 0;

    while (start < text.size())
    {
        const size_t end = text.find('\n', start);

        if (end == std::string::npos)
        {
            lines.push_back(text.substr(start));
            break;
        }

        lines.push_back(text.substr(start, end - start + 1));
        start = end + 1;
    }

    return lines;
}

std::string joinLines(
    const std::vector<std::string> &lines,
    size_t beginIndex,
    size_t endIndex)
{
    std::string result;

    for (size_t index = beginIndex; index < endIndex; ++index)
    {
        result += lines[index];
    }

    return result;
}

std::string normalizeIndentation(const std::string &text, int expectedIndentLevel)
{
    const std::vector<std::string> lines = splitPreservingLines(text);
    size_t minimumIndent = std::numeric_limits<size_t>::max();

    for (const std::string &line : lines)
    {
        size_t index = 0;

        while (index < line.size() && line[index] == ' ')
        {
            ++index;
        }

        if (index < line.size() && line[index] != '\n')
        {
            minimumIndent = std::min(minimumIndent, index);
        }
    }

    if (minimumIndent == std::numeric_limits<size_t>::max())
    {
        return text;
    }

    const size_t expectedIndent = static_cast<size_t>(std::max(expectedIndentLevel, 0) * 4);
    const size_t removeIndent = (minimumIndent > expectedIndent) ? (minimumIndent - expectedIndent) : 0;
    std::string result;

    for (const std::string &line : lines)
    {
        if (removeIndent > 0 && line.size() >= removeIndent && line.compare(0, removeIndent, std::string(removeIndent, ' ')) == 0)
        {
            result += line.substr(removeIndent);
        }
        else
        {
            result += line;
        }
    }

    return result;
}

bool extractCommonSuffix(
    const std::string &trueBody,
    const std::string &falseBody,
    std::string &truePrefix,
    std::string &falsePrefix,
    std::string &commonSuffix)
{
    const std::vector<std::string> trueLines = splitPreservingLines(trueBody);
    const std::vector<std::string> falseLines = splitPreservingLines(falseBody);

    size_t suffixLength = 0;

    while (suffixLength < trueLines.size() && suffixLength < falseLines.size())
    {
        const std::string &trueLine = trueLines[trueLines.size() - 1 - suffixLength];
        const std::string &falseLine = falseLines[falseLines.size() - 1 - suffixLength];

        if (trueLine != falseLine)
        {
            break;
        }

        ++suffixLength;
    }

    if (suffixLength == 0 || suffixLength == trueLines.size() || suffixLength == falseLines.size())
    {
        return false;
    }

    truePrefix = joinLines(trueLines, 0, trueLines.size() - suffixLength);
    falsePrefix = joinLines(falseLines, 0, falseLines.size() - suffixLength);
    commonSuffix = joinLines(trueLines, trueLines.size() - suffixLength, trueLines.size());
    return !truePrefix.empty() && !falsePrefix.empty() && !commonSuffix.empty();
}

bool tryEmitBranchToJoin(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const std::optional<std::string> &conditionComment,
    const std::string &condition,
    std::optional<uint8_t> branchStart,
    std::optional<uint8_t> joinStep,
    bool negateCondition,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited);

bool branchResolvedToStopOrTerminated(
    std::optional<uint8_t> branchStep,
    std::optional<uint8_t> stopStep)
{
    return !branchStep || branchStep == stopStep;
}

bool tryEmitIfElseToCommonJoin(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const std::optional<std::string> &conditionComment,
    const std::string &condition,
    std::optional<uint8_t> trueBranchStart,
    std::optional<uint8_t> falseBranchStart,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited);

bool tryEmitIfElseToTermination(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const std::optional<std::string> &conditionComment,
    const std::string &condition,
    std::optional<uint8_t> trueBranchStart,
    std::optional<uint8_t> falseBranchStart,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited);

bool extractCommonSuffix(
    const std::string &trueBody,
    const std::string &falseBody,
    std::string &truePrefix,
    std::string &falsePrefix,
    std::string &commonSuffix);

bool tryEmitReadableCompareLadder(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited);

bool tryEmitReadableGuardChainIfElse(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited);

bool emitReadableBlock(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    std::optional<uint8_t> stopStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited);

std::optional<uint32_t> getLeadingPartyMember(const LegacyLuaEvent &event, uint8_t step)
{
    NormalStepInfo stepInfo;

    if (!decomposeNormalStep(event, step, stepInfo) || stepInfo.actions.empty())
    {
        return std::nullopt;
    }

    const LegacyLuaInstruction *instruction = stepInfo.actions.front();

    if (instruction->operation != LegacyLuaOperation::ForPartyMember
        || instruction->arguments.empty()
        || instruction->arguments[0] > 4)
    {
        return std::nullopt;
    }

    return instruction->arguments[0];
}

std::string normalizePartyMemberLoopBody(std::string body)
{
    for (uint32_t memberIndex = 0; memberIndex <= 4; ++memberIndex)
    {
        const std::string from = "Players.Member" + std::to_string(memberIndex);
        const std::string to = "player";
        size_t offset = 0;

        while ((offset = body.find(from, offset)) != std::string::npos)
        {
            body.replace(offset, from.size(), to);
            offset += to.size();
        }
    }

    return body;
}

bool tryEmitReadablePartyMemberLoop(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited)
{
    if (!currentStep)
    {
        return false;
    }

    const std::optional<uint32_t> firstMember = getLeadingPartyMember(event, *currentStep);

    if (!firstMember)
    {
        return false;
    }

    std::vector<uint8_t> memberSteps = {*currentStep};
    uint8_t searchFromStep = *currentStep;
    uint32_t expectedMember = *firstMember + 1;

    while (expectedMember <= 4)
    {
        const std::optional<size_t> currentIndex = findStepIndex(steps, searchFromStep);

        if (!currentIndex)
        {
            return false;
        }

        std::optional<uint8_t> nextMemberStep;

        for (size_t stepIndex = *currentIndex + 1; stepIndex < steps.size(); ++stepIndex)
        {
            const std::optional<uint32_t> member = getLeadingPartyMember(event, steps[stepIndex]);

            if (member && *member == expectedMember)
            {
                nextMemberStep = steps[stepIndex];
                break;
            }
        }

        if (!nextMemberStep)
        {
            break;
        }

        memberSteps.push_back(*nextMemberStep);
        searchFromStep = *nextMemberStep;
        expectedMember += 1;
    }

    if (memberSteps.size() < 2)
    {
        return false;
    }

    auto formatPlayerList = [&]() -> std::string
    {
        std::ostringstream listStream;
        listStream << "{";

        for (size_t memberIndex = 0; memberIndex < memberSteps.size(); ++memberIndex)
        {
            const std::optional<uint32_t> member = getLeadingPartyMember(event, memberSteps[memberIndex]);

            if (!member)
            {
                return "";
            }

            if (memberIndex > 0)
            {
                listStream << ", ";
            }

            listStream << "Players.Member" << *member;
        }

        listStream << "}";
        return listStream.str();
    };

    const std::string playerList = formatPlayerList();

    if (playerList.empty())
    {
        return false;
    }

    auto emitBranchActions = [&](std::ostringstream &bodyStream, const SimpleBranchArm &arm, int bodyIndentLevel) -> bool
    {
        if (arm.returns)
        {
            return false;
        }

        for (const LegacyLuaInstruction *action : arm.actions)
        {
            if (!emitReadableActionInstruction(bodyStream, *action, lookups, bodyIndentLevel))
            {
                return false;
            }
        }

        return true;
    };

    auto tryEmitDirectValidationLoop = [&]() -> bool
    {
        auto isCompareInstructionStep = [&](const std::optional<uint8_t> &step) -> bool
        {
            if (!step)
            {
                return false;
            }

            const LegacyLuaInstruction *instruction = findInstructionByStep(event, *step);
            return instruction && isReadableCompareOperation(instruction->operation);
        };

        auto isNextMemberRangeStep = [&](size_t memberIndex, const std::optional<uint8_t> &step) -> bool
        {
            if (!step || memberIndex + 1 >= memberSteps.size())
            {
                return false;
            }

            const uint8_t minStep = memberSteps[memberIndex + 1];
            const uint8_t maxStep =
                memberIndex + 2 < memberSteps.size() ? static_cast<uint8_t>(memberSteps[memberIndex + 2] - 1) : 255;
            return *step >= minStep && *step <= maxStep;
        };

        std::optional<uint8_t> afterLoopStep;
        std::optional<uint8_t> commonFailureStep;
        std::string commonFailureBlock;
        std::vector<std::string> memberBodies;
        std::vector<std::string> normalizedBodies;
        std::vector<uint8_t> mergedVisited = visited;

        for (size_t memberIndex = 0; memberIndex < memberSteps.size(); ++memberIndex)
        {
            const std::optional<uint8_t> primaryCompareStep = nextStepAfter(steps, memberSteps[memberIndex]);

            if (!primaryCompareStep)
            {
                return false;
            }

            const LegacyLuaInstruction *primaryCompareInstruction = findInstructionByStep(event, *primaryCompareStep);

            if (!primaryCompareInstruction || !isReadableCompareOperation(primaryCompareInstruction->operation))
            {
                return false;
            }

            std::string primaryCondition;
            std::optional<std::string> primaryComment;

            if (!formatReadableConditionInstruction(*primaryCompareInstruction, lookups, primaryCondition, primaryComment))
            {
                return false;
            }

            std::optional<uint8_t> primaryJumpStep;
            std::optional<uint8_t> primaryFallthroughStep;

            if (!resolveSignificantStep(event, steps, primaryCompareInstruction->jumpTargetStep, primaryJumpStep)
                || !resolveSignificantStep(event, steps, nextStepAfter(steps, *primaryCompareStep), primaryFallthroughStep))
            {
                return false;
            }

            std::optional<uint8_t> requirementStep;
            std::optional<uint8_t> directSuccessStep;
            bool negatePrimaryCondition = false;

            if (isCompareInstructionStep(primaryJumpStep) && primaryFallthroughStep)
            {
                requirementStep = primaryJumpStep;
                directSuccessStep = primaryFallthroughStep;
                negatePrimaryCondition = true;
            }
            else if (isCompareInstructionStep(primaryFallthroughStep) && primaryJumpStep)
            {
                requirementStep = primaryFallthroughStep;
                directSuccessStep = primaryJumpStep;
                negatePrimaryCondition = false;
            }
            else
            {
                return false;
            }

            if (memberIndex + 1 < memberSteps.size())
            {
                if (!isNextMemberRangeStep(memberIndex, directSuccessStep))
                {
                    return false;
                }
            }

            const LegacyLuaInstruction *requirementInstruction = findInstructionByStep(event, *requirementStep);

            if (!requirementInstruction || !isReadableCompareOperation(requirementInstruction->operation))
            {
                return false;
            }

            std::string requirementCondition;
            std::optional<std::string> requirementComment;

            if (!formatReadableConditionInstruction(
                    *requirementInstruction,
                    lookups,
                    requirementCondition,
                    requirementComment))
            {
                return false;
            }

            std::optional<uint8_t> requirementJumpStep;
            std::optional<uint8_t> requirementFallthroughStep;

            if (!resolveSignificantStep(event, steps, requirementInstruction->jumpTargetStep, requirementJumpStep)
                || !resolveSignificantStep(event, steps, nextStepAfter(steps, *requirementStep), requirementFallthroughStep))
            {
                return false;
            }

            auto isRequirementSuccess = [&](const std::optional<uint8_t> &step) -> bool
            {
                if (memberIndex + 1 < memberSteps.size())
                {
                    return isNextMemberRangeStep(memberIndex, step);
                }

                return step && afterLoopStep && *step == *afterLoopStep;
            };

            std::optional<uint8_t> failureStep;
            bool negateRequirementCondition = false;

            if (memberIndex + 1 == memberSteps.size() && commonFailureStep)
            {
                if (requirementJumpStep && *requirementJumpStep == *commonFailureStep && requirementFallthroughStep)
                {
                    failureStep = requirementJumpStep;
                    afterLoopStep = requirementFallthroughStep;
                    negateRequirementCondition = false;
                }
                else if (requirementFallthroughStep && *requirementFallthroughStep == *commonFailureStep && requirementJumpStep)
                {
                    failureStep = requirementFallthroughStep;
                    afterLoopStep = requirementJumpStep;
                    negateRequirementCondition = true;
                }
                else
                {
                    return false;
                }
            }
            else if (isRequirementSuccess(requirementJumpStep) && requirementFallthroughStep)
            {
                failureStep = requirementFallthroughStep;
                negateRequirementCondition = true;
            }
            else if (isRequirementSuccess(requirementFallthroughStep) && requirementJumpStep)
            {
                failureStep = requirementJumpStep;
                negateRequirementCondition = false;
            }
            else
            {
                return false;
            }

            std::ostringstream failureStream;
            std::vector<uint8_t> failureVisited = visited;
            std::optional<uint8_t> failureCurrentStep = failureStep;

            if (!emitReadableBlock(
                    failureStream,
                    event,
                    steps,
                    failureCurrentStep,
                    std::nullopt,
                    lookups,
                    indentLevel + 3,
                    failureVisited))
            {
                return false;
            }

            if (failureCurrentStep)
            {
                return false;
            }

            const std::string currentFailureBlock = failureStream.str();

            if (!commonFailureStep)
            {
                commonFailureStep = failureStep;
                commonFailureBlock = currentFailureBlock;
            }
            else if (*commonFailureStep != *failureStep || commonFailureBlock != currentFailureBlock)
            {
                return false;
            }

            std::ostringstream memberBody;
            emitIndentedLineWithComment(memberBody, "evt.ForPlayer(player)", std::nullopt, indentLevel + 1);
            emitIndentedLineWithComment(
                memberBody,
                std::string("if ") + (negatePrimaryCondition ? "not " : "") + primaryCondition + " then",
                primaryComment,
                indentLevel + 1);
            emitIndentedLineWithComment(
                memberBody,
                std::string("if ") + (negateRequirementCondition ? "not " : "") + requirementCondition + " then",
                requirementComment,
                indentLevel + 2);
            memberBody << currentFailureBlock;
            emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 2);
            emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 1);
            memberBodies.push_back(memberBody.str());
            normalizedBodies.push_back(normalizePartyMemberLoopBody(memberBody.str()));

            for (uint8_t visitedStep : failureVisited)
            {
                if (std::find(mergedVisited.begin(), mergedVisited.end(), visitedStep) == mergedVisited.end())
                {
                    mergedVisited.push_back(visitedStep);
                }
            }
        }

        if (!afterLoopStep || normalizedBodies.empty())
        {
            return false;
        }

        bool allBodiesEqual = true;

        for (size_t bodyIndex = 1; bodyIndex < normalizedBodies.size(); ++bodyIndex)
        {
            if (normalizedBodies[bodyIndex] != normalizedBodies.front())
            {
                allBodiesEqual = false;
                break;
            }
        }

        if (allBodiesEqual)
        {
            emitIndentedLineWithComment(
                stream,
                "for _, player in ipairs(" + playerList + ") do",
                std::nullopt,
                indentLevel);
            stream << normalizedBodies.front();
            emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
        }
        else
        {
            for (const std::string &memberBody : memberBodies)
            {
                stream << memberBody;
            }
        }

        visited = std::move(mergedVisited);
        currentStep = afterLoopStep;
        return true;
    };

    auto tryEmitDirectActionLoop = [&]() -> bool
    {
        const std::optional<uint8_t> lastPrimaryCompareStep = nextStepAfter(steps, memberSteps.back());

        if (!lastPrimaryCompareStep)
        {
            return false;
        }

        const LegacyLuaInstruction *lastPrimaryCompareInstruction = findInstructionByStep(event, *lastPrimaryCompareStep);

        if (!lastPrimaryCompareInstruction || !isReadableCompareOperation(lastPrimaryCompareInstruction->operation))
        {
            return false;
        }

        const std::optional<uint8_t> afterLoopStep = findCommonJoinStep(
            event,
            steps,
            lastPrimaryCompareInstruction->jumpTargetStep,
            nextStepAfter(steps, *lastPrimaryCompareStep));

        if (!afterLoopStep)
        {
            return false;
        }

        std::vector<std::string> memberBodies;
        std::vector<std::string> normalizedBodies;

        for (size_t memberIndex = 0; memberIndex < memberSteps.size(); ++memberIndex)
        {
            const std::optional<uint8_t> primaryCompareStep = nextStepAfter(steps, memberSteps[memberIndex]);

            if (!primaryCompareStep)
            {
                return false;
            }

            const LegacyLuaInstruction *primaryCompareInstruction = findInstructionByStep(event, *primaryCompareStep);

            if (!primaryCompareInstruction || !isReadableCompareOperation(primaryCompareInstruction->operation))
            {
                return false;
            }

            std::string condition;
            std::optional<std::string> conditionComment;

            if (!formatReadableConditionInstruction(*primaryCompareInstruction, lookups, condition, conditionComment))
            {
                return false;
            }

            const std::optional<uint8_t> expectedContinuation =
                memberIndex + 1 < memberSteps.size() ? std::optional<uint8_t>(memberSteps[memberIndex + 1]) : afterLoopStep;

            if (!expectedContinuation)
            {
                return false;
            }

            SimpleBranchArm trueArm;
            SimpleBranchArm falseArm;

            if (!summarizeBoundedBranchArm(
                    event,
                    steps,
                    primaryCompareInstruction->jumpTargetStep,
                    *expectedContinuation,
                    lookups,
                    trueArm)
                || !summarizeBoundedBranchArm(
                    event,
                    steps,
                    nextStepAfter(steps, *primaryCompareStep),
                    *expectedContinuation,
                    lookups,
                    falseArm))
            {
                return false;
            }

            if (trueArm.returns || falseArm.returns || !trueArm.continuation || !falseArm.continuation
                || *trueArm.continuation != *expectedContinuation
                || *falseArm.continuation != *expectedContinuation)
            {
                return false;
            }

            std::ostringstream memberBody;
            emitIndentedLineWithComment(memberBody, "evt.ForPlayer(player)", std::nullopt, indentLevel + 1);

            if (trueArm.actions.empty() && falseArm.actions.empty())
            {
                continue;
            }

            if (falseArm.actions.empty())
            {
                emitIndentedLineWithComment(
                    memberBody,
                    "if " + condition + " then",
                    conditionComment,
                    indentLevel + 1);

                if (!emitBranchActions(memberBody, trueArm, indentLevel + 2))
                {
                    return false;
                }

                emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 1);
            }
            else if (trueArm.actions.empty())
            {
                emitIndentedLineWithComment(
                    memberBody,
                    "if not " + condition + " then",
                    conditionComment,
                    indentLevel + 1);

                if (!emitBranchActions(memberBody, falseArm, indentLevel + 2))
                {
                    return false;
                }

                emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 1);
            }
            else
            {
                emitIndentedLineWithComment(
                    memberBody,
                    "if " + condition + " then",
                    conditionComment,
                    indentLevel + 1);

                if (!emitBranchActions(memberBody, trueArm, indentLevel + 2))
                {
                    return false;
                }

                emitIndentedLineWithComment(memberBody, "else", std::nullopt, indentLevel + 1);

                if (!emitBranchActions(memberBody, falseArm, indentLevel + 2))
                {
                    return false;
                }

                emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 1);
            }

            memberBodies.push_back(memberBody.str());
            normalizedBodies.push_back(normalizePartyMemberLoopBody(memberBody.str()));
        }

        if (normalizedBodies.empty())
        {
            return false;
        }

        bool allBodiesEqual = true;

        for (size_t bodyIndex = 1; bodyIndex < normalizedBodies.size(); ++bodyIndex)
        {
            if (normalizedBodies[bodyIndex] != normalizedBodies.front())
            {
                allBodiesEqual = false;
                break;
            }
        }

        if (allBodiesEqual)
        {
            emitIndentedLineWithComment(
                stream,
                "for _, player in ipairs(" + playerList + ") do",
                std::nullopt,
                indentLevel);
            stream << normalizedBodies.front();
            emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
        }
        else
        {
            for (const std::string &memberBody : memberBodies)
            {
                stream << memberBody;
            }
        }

        currentStep = afterLoopStep;
        return true;
    };

    if (tryEmitDirectValidationLoop())
    {
        return true;
    }

    if (tryEmitDirectActionLoop())
    {
        return true;
    }

    auto findPrimaryCompareForMember =
        [&](uint8_t memberStep,
            NormalStepInfo &memberInfo,
            const LegacyLuaInstruction *&compareInstruction,
            std::optional<uint8_t> &fallthroughStep) -> bool
    {
        compareInstruction = nullptr;
        fallthroughStep = std::nullopt;

        if (!decomposeNormalStep(event, memberStep, memberInfo)
            || memberInfo.actions.empty()
            || memberInfo.actions.front()->operation != LegacyLuaOperation::ForPartyMember)
        {
            return false;
        }

        if (memberInfo.terminalInstruction && isReadableCompareOperation(memberInfo.terminalInstruction->operation))
        {
            compareInstruction = memberInfo.terminalInstruction;
            fallthroughStep = nextStepAfter(steps, memberStep);
            return true;
        }

        if (!memberInfo.terminalInstruction)
        {
            const std::optional<uint8_t> compareStep = nextStepAfter(steps, memberStep);

            if (!compareStep)
            {
                return false;
            }

            NormalStepInfo compareStepInfo;

            if (!decomposeNormalStep(event, *compareStep, compareStepInfo)
                || !compareStepInfo.actions.empty()
                || !compareStepInfo.terminalInstruction
                || !isReadableCompareOperation(compareStepInfo.terminalInstruction->operation))
            {
                return false;
            }

            compareInstruction = compareStepInfo.terminalInstruction;
            fallthroughStep = nextStepAfter(steps, *compareStep);
            return true;
        }

        return false;
    };

    auto tryEmitValidationLoop = [&]() -> bool
    {
        struct ValidationMemberShape
        {
            std::string primaryCondition;
            std::optional<std::string> primaryComment;
            bool negatePrimaryCondition = false;
            std::string requirementCondition;
            std::optional<std::string> requirementComment;
            bool negateRequirementCondition = false;
            uint8_t failureStep = 0;
        };

        auto isCompareInstructionStep = [&](const std::optional<uint8_t> &step) -> bool
        {
            if (!step)
            {
                return false;
            }

            const LegacyLuaInstruction *instruction = findInstructionByStep(event, *step);
            return instruction && isReadableCompareOperation(instruction->operation);
        };

        auto memberRangeContainsSuccessStep = [&](size_t memberIndex, uint8_t step) -> bool
        {
            if (memberIndex + 1 >= memberSteps.size())
            {
                return false;
            }

            const uint8_t minStep = memberSteps[memberIndex + 1];
            const uint8_t maxStep =
                memberIndex + 2 < memberSteps.size() ? static_cast<uint8_t>(memberSteps[memberIndex + 2] - 1) : 255;
            return step >= minStep && step <= maxStep;
        };

        auto parseValidationMember =
            [&](size_t memberIndex, std::optional<uint8_t> afterLoopStep, ValidationMemberShape &shape) -> bool
        {
            const std::optional<uint8_t> primaryCompareStep = nextStepAfter(steps, memberSteps[memberIndex]);

            if (!primaryCompareStep)
            {
                return false;
            }

            const LegacyLuaInstruction *primaryCompareInstruction = findInstructionByStep(event, *primaryCompareStep);

            if (!primaryCompareInstruction || !isReadableCompareOperation(primaryCompareInstruction->operation))
            {
                return false;
            }

            if (!formatReadableConditionInstruction(
                    *primaryCompareInstruction,
                    lookups,
                    shape.primaryCondition,
                    shape.primaryComment))
            {
                return false;
            }

            std::optional<uint8_t> jumpStep;
            std::optional<uint8_t> fallthroughSignificantStep;

            if (!resolveSignificantStep(event, steps, primaryCompareInstruction->jumpTargetStep, jumpStep)
                || !resolveSignificantStep(event, steps, nextStepAfter(steps, *primaryCompareStep), fallthroughSignificantStep))
            {
                return false;
            }

            std::optional<uint8_t> requirementStep;
            std::optional<uint8_t> directSuccessStep;

            if (isCompareInstructionStep(jumpStep) && fallthroughSignificantStep)
            {
                requirementStep = jumpStep;
                directSuccessStep = fallthroughSignificantStep;
                shape.negatePrimaryCondition = true;
            }
            else if (isCompareInstructionStep(fallthroughSignificantStep) && jumpStep)
            {
                requirementStep = fallthroughSignificantStep;
                directSuccessStep = jumpStep;
                shape.negatePrimaryCondition = false;
            }
            else
            {
                return false;
            }

            const LegacyLuaInstruction *requirementInstruction = findInstructionByStep(event, *requirementStep);

            if (!requirementInstruction || !isReadableCompareOperation(requirementInstruction->operation))
            {
                return false;
            }

            if (!formatReadableConditionInstruction(
                    *requirementInstruction,
                    lookups,
                    shape.requirementCondition,
                    shape.requirementComment))
            {
                return false;
            }

            std::optional<uint8_t> requirementJumpStep;
            std::optional<uint8_t> requirementFallthroughSignificantStep;

            if (!resolveSignificantStep(event, steps, requirementInstruction->jumpTargetStep, requirementJumpStep)
                || !resolveSignificantStep(event, steps, nextStepAfter(steps, *requirementStep), requirementFallthroughSignificantStep))
            {
                return false;
            }

            auto isExpectedSuccess = [&](const std::optional<uint8_t> &step) -> bool
            {
                if (!step)
                {
                    return false;
                }

                if (memberIndex + 1 < memberSteps.size())
                {
                    return memberRangeContainsSuccessStep(memberIndex, *step);
                }

                return afterLoopStep && *step == *afterLoopStep;
            };

            if (!directSuccessStep || !isExpectedSuccess(directSuccessStep))
            {
                return false;
            }

            if (requirementJumpStep && isExpectedSuccess(requirementJumpStep) && requirementFallthroughSignificantStep)
            {
                shape.failureStep = *requirementFallthroughSignificantStep;
                shape.negateRequirementCondition = true;
                return true;
            }

            if (requirementFallthroughSignificantStep && isExpectedSuccess(requirementFallthroughSignificantStep)
                && requirementJumpStep)
            {
                shape.failureStep = *requirementJumpStep;
                shape.negateRequirementCondition = false;
                return true;
            }

            return false;
        };

        const std::optional<uint8_t> lastPrimaryCompareStep = nextStepAfter(steps, memberSteps.back());

        if (!lastPrimaryCompareStep)
        {
            return false;
        }

        const LegacyLuaInstruction *lastPrimaryCompareInstruction = findInstructionByStep(event, *lastPrimaryCompareStep);

        if (!lastPrimaryCompareInstruction || !isReadableCompareOperation(lastPrimaryCompareInstruction->operation))
        {
            return false;
        }

        std::optional<uint8_t> lastDirectStep;

        if (!resolveSignificantStep(event, steps, nextStepAfter(steps, *lastPrimaryCompareStep), lastDirectStep))
        {
            return false;
        }

        if (!lastDirectStep)
        {
            return false;
        }

        std::optional<uint8_t> afterLoopStep = lastDirectStep;

        std::vector<std::string> normalizedBodies;
        std::vector<uint8_t> mergedVisited = visited;
        std::optional<uint8_t> failureStep;
        std::string failureBlock;

        for (size_t memberIndex = 0; memberIndex < memberSteps.size(); ++memberIndex)
        {
            ValidationMemberShape shape;

            if (!parseValidationMember(memberIndex, afterLoopStep, shape))
            {
                return false;
            }

            std::ostringstream memberBody;
            emitIndentedLineWithComment(memberBody, "evt.ForPlayer(player)", std::nullopt, indentLevel + 1);
            emitIndentedLineWithComment(
                memberBody,
                std::string("if ") + (shape.negatePrimaryCondition ? "not " : "") + shape.primaryCondition + " then",
                shape.primaryComment,
                indentLevel + 1);
            emitIndentedLineWithComment(
                memberBody,
                std::string("if ") + (shape.negateRequirementCondition ? "not " : "") + shape.requirementCondition + " then",
                shape.requirementComment,
                indentLevel + 2);

            std::ostringstream memberFailureStream;
            std::vector<uint8_t> failureVisited = visited;
            std::optional<uint8_t> failureCurrentStep = shape.failureStep;

            if (!emitReadableBlock(
                    memberFailureStream,
                    event,
                    steps,
                    failureCurrentStep,
                    std::nullopt,
                    lookups,
                    indentLevel + 3,
                    failureVisited))
            {
                return false;
            }

            if (failureCurrentStep)
            {
                return false;
            }

            const std::string currentFailureBlock = memberFailureStream.str();

            if (!failureStep)
            {
                failureStep = shape.failureStep;
                failureBlock = currentFailureBlock;
            }
            else if (*failureStep != shape.failureStep || failureBlock != currentFailureBlock)
            {
                return false;
            }

            memberBody << currentFailureBlock;
            emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 2);
            emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 1);
            normalizedBodies.push_back(normalizePartyMemberLoopBody(memberBody.str()));

            for (uint8_t visitedStep : failureVisited)
            {
                if (std::find(mergedVisited.begin(), mergedVisited.end(), visitedStep) == mergedVisited.end())
                {
                    mergedVisited.push_back(visitedStep);
                }
            }
        }

        for (size_t bodyIndex = 1; bodyIndex < normalizedBodies.size(); ++bodyIndex)
        {
            if (normalizedBodies[bodyIndex] != normalizedBodies.front())
            {
                return false;
            }
        }

        emitIndentedLineWithComment(
            stream,
            "for _, player in ipairs(" + playerList + ") do",
            std::nullopt,
            indentLevel);
        stream << normalizedBodies.front();
        emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
        visited = std::move(mergedVisited);
        currentStep = afterLoopStep;
        return true;
    };

    auto tryEmitActionLoop = [&]() -> bool
    {
        const std::optional<uint8_t> lastPrimaryCompareStep = nextStepAfter(steps, memberSteps.back());

        if (!lastPrimaryCompareStep)
        {
            return false;
        }

        const LegacyLuaInstruction *lastPrimaryCompareInstruction = findInstructionByStep(event, *lastPrimaryCompareStep);

        if (!lastPrimaryCompareInstruction || !isReadableCompareOperation(lastPrimaryCompareInstruction->operation))
        {
            return false;
        }

        const std::optional<uint8_t> afterLoopStep = findCommonJoinStep(
            event,
            steps,
            lastPrimaryCompareInstruction->jumpTargetStep,
            nextStepAfter(steps, *lastPrimaryCompareStep));

        if (!afterLoopStep)
        {
            return false;
        }

        std::vector<std::string> normalizedBodies;

        for (size_t memberIndex = 0; memberIndex < memberSteps.size(); ++memberIndex)
        {
            const std::optional<uint8_t> primaryCompareStep = nextStepAfter(steps, memberSteps[memberIndex]);

            if (!primaryCompareStep)
            {
                return false;
            }

            const LegacyLuaInstruction *primaryCompareInstruction = findInstructionByStep(event, *primaryCompareStep);

            if (!primaryCompareInstruction || !isReadableCompareOperation(primaryCompareInstruction->operation))
            {
                return false;
            }

            std::string condition;
            std::optional<std::string> conditionComment;

            if (!formatReadableConditionInstruction(*primaryCompareInstruction, lookups, condition, conditionComment))
            {
                return false;
            }

            SimpleBranchArm trueArm;
            SimpleBranchArm falseArm;

            const std::optional<uint8_t> expectedContinuation =
                memberIndex + 1 < memberSteps.size() ? std::optional<uint8_t>(memberSteps[memberIndex + 1]) : afterLoopStep;

            if (!expectedContinuation
                || !summarizeBoundedBranchArm(
                    event,
                    steps,
                    primaryCompareInstruction->jumpTargetStep,
                    *expectedContinuation,
                    lookups,
                    trueArm)
                || !summarizeBoundedBranchArm(
                    event,
                    steps,
                    nextStepAfter(steps, *primaryCompareStep),
                    *expectedContinuation,
                    lookups,
                    falseArm))
            {
                return false;
            }

            if (trueArm.returns || falseArm.returns || !trueArm.continuation || !falseArm.continuation
                || *trueArm.continuation != *expectedContinuation
                || *falseArm.continuation != *expectedContinuation)
            {
                return false;
            }

            std::ostringstream memberBody;
            emitIndentedLineWithComment(memberBody, "evt.ForPlayer(player)", std::nullopt, indentLevel + 1);

            if (trueArm.actions.empty() && falseArm.actions.empty())
            {
                continue;
            }

            if (falseArm.actions.empty())
            {
                emitIndentedLineWithComment(
                    memberBody,
                    "if " + condition + " then",
                    conditionComment,
                    indentLevel + 1);

                if (!emitBranchActions(memberBody, trueArm, indentLevel + 2))
                {
                    return false;
                }

                emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 1);
            }
            else if (trueArm.actions.empty())
            {
                emitIndentedLineWithComment(
                    memberBody,
                    "if not " + condition + " then",
                    conditionComment,
                    indentLevel + 1);

                if (!emitBranchActions(memberBody, falseArm, indentLevel + 2))
                {
                    return false;
                }

                emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 1);
            }
            else
            {
                emitIndentedLineWithComment(
                    memberBody,
                    "if " + condition + " then",
                    conditionComment,
                    indentLevel + 1);

                if (!emitBranchActions(memberBody, trueArm, indentLevel + 2))
                {
                    return false;
                }

                emitIndentedLineWithComment(memberBody, "else", std::nullopt, indentLevel + 1);

                if (!emitBranchActions(memberBody, falseArm, indentLevel + 2))
                {
                    return false;
                }

                emitIndentedLineWithComment(memberBody, "end", std::nullopt, indentLevel + 1);
            }

            normalizedBodies.push_back(normalizePartyMemberLoopBody(memberBody.str()));
        }

        if (normalizedBodies.empty())
        {
            return false;
        }

        for (size_t bodyIndex = 1; bodyIndex < normalizedBodies.size(); ++bodyIndex)
        {
            if (normalizedBodies[bodyIndex] != normalizedBodies.front())
            {
                return false;
            }
        }

        emitIndentedLineWithComment(
            stream,
            "for _, player in ipairs(" + playerList + ") do",
            std::nullopt,
            indentLevel);
        stream << normalizedBodies.front();
        emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
        currentStep = afterLoopStep;
        return true;
    };

    if (tryEmitValidationLoop())
    {
        return true;
    }

    return tryEmitActionLoop();
}

struct PromptContinuation
{
    uint8_t promptStep = 0;
    uint8_t continueStep = 0;
    LegacyLuaOperation operation = LegacyLuaOperation::InputString;
    uint32_t textId = 0;
    std::optional<std::string> text;
};

std::vector<PromptContinuation> collectPromptContinuations(const LegacyLuaEvent &event)
{
    std::vector<PromptContinuation> continuations;

    for (const LegacyLuaInstruction &instruction : event.instructions)
    {
        if (instruction.operation != LegacyLuaOperation::InputString
            && instruction.operation != LegacyLuaOperation::PressAnyKey)
        {
            continue;
        }

        PromptContinuation continuation = {};
        continuation.promptStep = instruction.step;
        continuation.continueStep = static_cast<uint8_t>(instruction.step + 1);
        continuation.operation = instruction.operation;

        if (!instruction.arguments.empty())
        {
            continuation.textId = instruction.arguments[0];
        }

        if (instruction.text && !instruction.text->empty())
        {
            continuation.text = *instruction.text;
        }

        continuations.push_back(std::move(continuation));
    }

    return continuations;
}

bool emitReadableBlock(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    std::optional<uint8_t> stopStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited)
{
    while (currentStep && currentStep != stopStep)
    {
        if (tryEmitReadablePartyMemberLoop(stream, event, steps, currentStep, lookups, indentLevel, visited))
        {
            continue;
        }

        if (std::find(visited.begin(), visited.end(), *currentStep) != visited.end())
        {
            return false;
        }

        visited.push_back(*currentStep);
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *currentStep, stepInfo))
        {
            return false;
        }

        if (stepInfo.actions.empty() && !stepInfo.terminalInstruction)
        {
            currentStep = nextStepAfter(steps, *currentStep);
            continue;
        }

        for (const LegacyLuaInstruction *action : stepInfo.actions)
        {
            if (!emitReadableActionInstruction(stream, *action, lookups, indentLevel))
            {
                return false;
            }
        }

        if (!stepInfo.terminalInstruction)
        {
            currentStep = nextStepAfter(steps, *currentStep);
            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::Exit)
        {
            emitIndentedLineWithComment(stream, "return", std::nullopt, indentLevel);
            currentStep = std::nullopt;
            continue;
        }

        if (instruction.operation == LegacyLuaOperation::Jump)
        {
            if (!instruction.jumpTargetStep)
            {
                return false;
            }

            currentStep = instruction.jumpTargetStep;
            continue;
        }

        if (instruction.operation == LegacyLuaOperation::InputString)
        {
            std::ostringstream line;
            line << "evt._InputString(" << event.eventId << ", " << static_cast<unsigned>(instruction.step + 1);

            if (!instruction.arguments.empty())
            {
                line << ", " << instruction.arguments[0];
            }

            if (instruction.text && !instruction.text->empty())
            {
                if (instruction.arguments.empty())
                {
                    line << ", 0";
                }

                line << ", " << luaQuoted(*instruction.text);
            }

            line << ")";
            emitIndentedLineWithComment(stream, line.str(), std::nullopt, indentLevel);
            currentStep = std::nullopt;
            continue;
        }

        if (instruction.operation == LegacyLuaOperation::PressAnyKey)
        {
            emitIndentedLineWithComment(
                stream,
                "evt._PressAnyKey(" + std::to_string(event.eventId) + ", "
                + std::to_string(static_cast<unsigned>(instruction.step + 1)) + ")",
                std::nullopt,
                indentLevel);
            currentStep = std::nullopt;
            continue;
        }

        if (instruction.operation == LegacyLuaOperation::Compare
            || instruction.operation == LegacyLuaOperation::CheckItemsCount
            || instruction.operation == LegacyLuaOperation::CheckSkill
            || instruction.operation == LegacyLuaOperation::IsActorKilled
            || instruction.operation == LegacyLuaOperation::CheckSeason
            || instruction.operation == LegacyLuaOperation::IsTotalBountyHuntingAwardInRange
            || instruction.operation == LegacyLuaOperation::IsNpcInParty)
        {
            if (tryEmitReadableCompareLadder(stream, event, steps, currentStep, lookups, indentLevel, visited))
            {
                continue;
            }

            if (tryEmitReadableGuardChainIfElse(stream, event, steps, currentStep, lookups, indentLevel, visited))
            {
                continue;
            }

            if (!instruction.jumpTargetStep)
            {
                return false;
            }

            std::string condition;
            std::optional<std::string> conditionComment;

            if (!formatReadableConditionInstruction(instruction, lookups, condition, conditionComment))
            {
                return false;
            }

            const std::optional<uint8_t> fallthroughStep = nextStepAfter(steps, *currentStep);
            std::optional<uint8_t> trueSignificantStep;
            std::optional<uint8_t> falseSignificantStep;

            if (!resolveSignificantStep(event, steps, instruction.jumpTargetStep, trueSignificantStep))
            {
                return false;
            }

            if (!resolveSignificantStep(event, steps, fallthroughStep, falseSignificantStep))
            {
                return false;
            }

            if (isImmediateReturnPath(event, steps, fallthroughStep))
            {
                emitIndentedLineWithComment(
                    stream,
                    "if not " + condition + " then return end",
                    conditionComment,
                    indentLevel);
                currentStep = instruction.jumpTargetStep;
                continue;
            }

            if (isImmediateReturnPath(event, steps, instruction.jumpTargetStep))
            {
                emitIndentedLineWithComment(
                    stream,
                    "if " + condition + " then return end",
                    conditionComment,
                    indentLevel);
                currentStep = fallthroughStep;
                continue;
            }

            if (falseSignificantStep && fallthroughStep && *falseSignificantStep != *fallthroughStep)
            {
                if (tryEmitBranchToJoin(
                        stream,
                        event,
                        steps,
                        currentStep,
                        conditionComment,
                        condition,
                        instruction.jumpTargetStep,
                        falseSignificantStep,
                        false,
                        lookups,
                        indentLevel,
                        visited))
                {
                    continue;
                }
            }

            if (trueSignificantStep && instruction.jumpTargetStep && *trueSignificantStep != *instruction.jumpTargetStep)
            {
                if (tryEmitBranchToJoin(
                        stream,
                        event,
                        steps,
                        currentStep,
                        conditionComment,
                        condition,
                        fallthroughStep,
                        trueSignificantStep,
                        true,
                        lookups,
                        indentLevel,
                        visited))
                {
                    continue;
                }
            }

            if (tryEmitBranchToJoin(
                    stream,
                    event,
                    steps,
                    currentStep,
                    conditionComment,
                    condition,
                    fallthroughStep,
                    instruction.jumpTargetStep,
                    true,
                    lookups,
                    indentLevel,
                    visited))
            {
                continue;
            }

            if (tryEmitBranchToJoin(
                    stream,
                    event,
                    steps,
                    currentStep,
                    conditionComment,
                    condition,
                    instruction.jumpTargetStep,
                    fallthroughStep,
                    false,
                    lookups,
                    indentLevel,
                    visited))
            {
                continue;
            }

            SimpleBranchArm trueArm;
            SimpleBranchArm falseArm;

            if (summarizeSimpleBranchArm(event, steps, instruction.jumpTargetStep, lookups, trueArm)
                && summarizeSimpleBranchArm(event, steps, fallthroughStep, lookups, falseArm))
            {
                if (trueArm.returns && falseArm.returns)
                {
                    emitIndentedLineWithComment(
                        stream,
                        "if " + condition + " then",
                        conditionComment,
                        indentLevel);
                    emitSimpleBranchArm(stream, trueArm, lookups, indentLevel + 1);
                    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
                    emitSimpleBranchArm(stream, falseArm, lookups, indentLevel);
                    currentStep = std::nullopt;
                    continue;
                }

                if (trueArm.continuation && falseArm.continuation && *trueArm.continuation == *falseArm.continuation)
                {
                    emitIndentedLineWithComment(
                        stream,
                        "if " + condition + " then",
                        conditionComment,
                        indentLevel);
                    emitSimpleBranchArm(stream, trueArm, lookups, indentLevel + 1);
                    emitIndentedLineWithComment(stream, "else", std::nullopt, indentLevel);
                    emitSimpleBranchArm(stream, falseArm, lookups, indentLevel + 1);
                    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
                    currentStep = trueArm.continuation;
                    continue;
                }

                if (trueArm.returns && falseArm.continuation)
                {
                    emitIndentedLineWithComment(
                        stream,
                        "if " + condition + " then",
                        conditionComment,
                        indentLevel);
                    emitSimpleBranchArm(stream, trueArm, lookups, indentLevel + 1);
                    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

                    for (const LegacyLuaInstruction *action : falseArm.actions)
                    {
                        emitReadableActionInstruction(stream, *action, lookups, indentLevel);
                    }

                    currentStep = falseArm.continuation;
                    continue;
                }

                if (falseArm.returns && trueArm.continuation)
                {
                    emitIndentedLineWithComment(
                        stream,
                        "if not " + condition + " then",
                        conditionComment,
                        indentLevel);
                    emitSimpleBranchArm(stream, falseArm, lookups, indentLevel + 1);
                    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

                    for (const LegacyLuaInstruction *action : trueArm.actions)
                    {
                        emitReadableActionInstruction(stream, *action, lookups, indentLevel);
                    }

                    currentStep = trueArm.continuation;
                    continue;
                }
            }

            if (tryEmitIfElseToCommonJoin(
                    stream,
                    event,
                    steps,
                    currentStep,
                    conditionComment,
                    condition,
                    instruction.jumpTargetStep,
                    fallthroughStep,
                    lookups,
                    indentLevel,
                    visited))
            {
                continue;
            }

            if (tryEmitIfElseToTermination(
                    stream,
                    event,
                    steps,
                    currentStep,
                    conditionComment,
                    condition,
                    instruction.jumpTargetStep,
                    fallthroughStep,
                    lookups,
                    indentLevel,
                    visited))
            {
                continue;
            }

            if (stopStep && instruction.jumpTargetStep == stopStep && fallthroughStep && fallthroughStep != stopStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if not " + condition + " then",
                    conditionComment,
                    indentLevel);

                std::optional<uint8_t> branchStep = fallthroughStep;

                if (!emitReadableBlock(stream, event, steps, branchStep, stopStep, lookups, indentLevel + 1, visited))
                {
                    return false;
                }

                if (!branchResolvedToStopOrTerminated(branchStep, stopStep))
                {
                    return false;
                }

                emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
                currentStep = stopStep;
                continue;
            }

            if (stopStep && resolvesDirectlyToStep(event, steps, fallthroughStep, stopStep)
                && instruction.jumpTargetStep != stopStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if " + condition + " then",
                    conditionComment,
                    indentLevel);

                std::optional<uint8_t> branchStep = instruction.jumpTargetStep;

                if (!emitReadableBlock(stream, event, steps, branchStep, stopStep, lookups, indentLevel + 1, visited))
                {
                    return false;
                }

                if (!branchResolvedToStopOrTerminated(branchStep, stopStep))
                {
                    return false;
                }

                emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
                currentStep = stopStep;
                continue;
            }

            if (stopStep && fallthroughStep == stopStep && instruction.jumpTargetStep != stopStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if " + condition + " then",
                    conditionComment,
                    indentLevel);

                std::optional<uint8_t> branchStep = instruction.jumpTargetStep;

                if (!emitReadableBlock(stream, event, steps, branchStep, stopStep, lookups, indentLevel + 1, visited))
                {
                    return false;
                }

                if (!branchResolvedToStopOrTerminated(branchStep, stopStep))
                {
                    return false;
                }

                emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
                currentStep = stopStep;
                continue;
            }

            if (stopStep && resolvesDirectlyToStep(event, steps, instruction.jumpTargetStep, stopStep)
                && fallthroughStep != stopStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if not " + condition + " then",
                    conditionComment,
                    indentLevel);

                std::optional<uint8_t> branchStep = fallthroughStep;

                if (!emitReadableBlock(stream, event, steps, branchStep, stopStep, lookups, indentLevel + 1, visited))
                {
                    return false;
                }

                if (!branchResolvedToStopOrTerminated(branchStep, stopStep))
                {
                    return false;
                }

                emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
                currentStep = stopStep;
                continue;
            }

            return false;
        }

        if (instruction.operation == LegacyLuaOperation::RandomJump)
        {
            if (instruction.arguments.empty())
            {
                return false;
            }

            std::vector<uint8_t> branchStarts;

            for (uint32_t argument : instruction.arguments)
            {
                const uint8_t branchStep = static_cast<uint8_t>(argument);

                if (std::find(branchStarts.begin(), branchStarts.end(), branchStep) == branchStarts.end())
                {
                    branchStarts.push_back(branchStep);
                }
            }

            const std::optional<uint8_t> joinStep = findCommonJoinStepForBranches(event, steps, branchStarts);

            if (joinStep)
            {
                bool needsChoiceVariable = false;

                for (uint8_t branchStep : branchStarts)
                {
                    if (!resolvesDirectlyToStep(event, steps, branchStep, joinStep))
                    {
                        needsChoiceVariable = true;
                        break;
                    }
                }

                std::ostringstream randomCall;
                randomCall << "PickRandomOption(" << event.eventId << ", " << static_cast<unsigned>(instruction.step + 1) << ", {";

                for (size_t argumentIndex = 0; argumentIndex < instruction.arguments.size(); ++argumentIndex)
                {
                    if (argumentIndex > 0)
                    {
                        randomCall << ", ";
                    }

                    randomCall << instruction.arguments[argumentIndex];
                }

                randomCall << "})";

                if (!needsChoiceVariable)
                {
                    emitIndentedLineWithComment(stream, randomCall.str(), std::nullopt, indentLevel);
                    currentStep = joinStep;
                    continue;
                }

                emitIndentedLineWithComment(stream, "local randomStep = " + randomCall.str(), std::nullopt, indentLevel);

                bool emittedAnyBranch = false;
                std::vector<uint8_t> mergedVisited = visited;

                for (uint8_t branchStep : branchStarts)
                {
                    if (resolvesDirectlyToStep(event, steps, branchStep, joinStep))
                    {
                        continue;
                    }

                    emitIndentedLineWithComment(
                        stream,
                        std::string(emittedAnyBranch ? "elseif" : "if") + " randomStep == " + std::to_string(branchStep) + " then",
                        std::nullopt,
                        indentLevel);

                    std::ostringstream branchStream;
                    std::vector<uint8_t> branchVisited = visited;
                    std::optional<uint8_t> nestedStep = branchStep;

                    if (!emitReadableBlock(
                            branchStream,
                            event,
                            steps,
                            nestedStep,
                            joinStep,
                            lookups,
                            indentLevel + 1,
                            branchVisited))
                    {
                        return false;
                    }

                    if (nestedStep != joinStep)
                    {
                        return false;
                    }

                    stream << branchStream.str();
                    emittedAnyBranch = true;

                    for (uint8_t visitedStep : branchVisited)
                    {
                        if (std::find(mergedVisited.begin(), mergedVisited.end(), visitedStep) == mergedVisited.end())
                        {
                            mergedVisited.push_back(visitedStep);
                        }
                    }
                }

                if (emittedAnyBranch)
                {
                    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
                }

                visited = std::move(mergedVisited);
                currentStep = joinStep;
                continue;
            }
        }

        if (instruction.operation == LegacyLuaOperation::RandomJump)
        {
            if (instruction.arguments.empty())
            {
                return false;
            }

            std::vector<uint8_t> branchStarts;

            for (uint32_t argument : instruction.arguments)
            {
                const uint8_t branchStep = static_cast<uint8_t>(argument);

                if (std::find(branchStarts.begin(), branchStarts.end(), branchStep) == branchStarts.end())
                {
                    branchStarts.push_back(branchStep);
                }
            }

            std::ostringstream randomCall;
            randomCall << "PickRandomOption(" << event.eventId << ", " << static_cast<unsigned>(instruction.step + 1) << ", {";

            for (size_t argumentIndex = 0; argumentIndex < instruction.arguments.size(); ++argumentIndex)
            {
                if (argumentIndex > 0)
                {
                    randomCall << ", ";
                }

                randomCall << instruction.arguments[argumentIndex];
            }

            randomCall << "})";

            std::vector<uint8_t> mergedVisited = visited;
            std::ostringstream branchCases;
            bool emittedAnyBranch = false;

            for (uint8_t branchStep : branchStarts)
            {
                std::ostringstream branchStream;
                std::vector<uint8_t> branchVisited = visited;
                std::optional<uint8_t> nestedStep = branchStep;

                if (!emitReadableBlock(
                        branchStream,
                        event,
                        steps,
                        nestedStep,
                        std::nullopt,
                        lookups,
                        indentLevel + 1,
                        branchVisited))
                {
                    emittedAnyBranch = false;
                    branchCases.str({});
                    branchCases.clear();
                    break;
                }

                if (nestedStep)
                {
                    emittedAnyBranch = false;
                    branchCases.str({});
                    branchCases.clear();
                    break;
                }

                branchCases << std::string(emittedAnyBranch ? "elseif" : "if") << " randomStep == "
                            << std::to_string(branchStep) << " then\n";
                branchCases << branchStream.str();
                emittedAnyBranch = true;

                for (uint8_t visitedStep : branchVisited)
                {
                    if (std::find(mergedVisited.begin(), mergedVisited.end(), visitedStep) == mergedVisited.end())
                    {
                        mergedVisited.push_back(visitedStep);
                    }
                }
            }

            if (emittedAnyBranch)
            {
                emitIndentedLineWithComment(stream, "local randomStep = " + randomCall.str(), std::nullopt, indentLevel);
                stream << branchCases.str();
                emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
                visited = std::move(mergedVisited);
                currentStep = std::nullopt;
                continue;
            }
        }

        if (!emitReadableActionInstruction(stream, instruction, lookups, indentLevel))
        {
            return false;
        }

        currentStep = nextStepAfter(steps, *currentStep);
    }

    return true;
}

struct CompareLadderArm
{
    std::string condition;
    std::optional<std::string> comment;
    uint8_t branchStart = 0;
};

bool tryEmitReadableCompareLadder(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited)
{
    if (!currentStep)
    {
        return false;
    }

    std::vector<CompareLadderArm> arms;
    std::vector<uint8_t> ladderSteps;
    std::optional<uint8_t> ladderElseStep;
    std::optional<uint8_t> ladderStep = *currentStep;

    while (ladderStep)
    {
        const LegacyLuaInstruction *instruction = findInstructionByStep(event, *ladderStep);

        if (!instruction
            || instruction->operation != LegacyLuaOperation::Compare
            || instruction->arguments.size() < 2
            || !instruction->jumpTargetStep)
        {
            return false;
        }

        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *ladderStep, stepInfo)
            || !stepInfo.actions.empty()
            || stepInfo.terminalInstruction != instruction)
        {
            return false;
        }

        std::string condition;
        std::optional<std::string> conditionComment;

        if (!formatReadableConditionInstruction(*instruction, lookups, condition, conditionComment))
        {
            return false;
        }

        std::optional<uint8_t> branchStart;
        std::optional<uint8_t> fallthroughStep;

        if (!resolveSignificantStep(event, steps, instruction->jumpTargetStep, branchStart)
            || !resolveSignificantStep(event, steps, nextStepAfter(steps, *ladderStep), fallthroughStep)
            || !branchStart)
        {
            return false;
        }

        arms.push_back({condition, conditionComment, *branchStart});
        ladderSteps.push_back(*ladderStep);

        if (!fallthroughStep)
        {
            ladderElseStep = std::nullopt;
            break;
        }

        const LegacyLuaInstruction *fallthroughInstruction = findInstructionByStep(event, *fallthroughStep);
        NormalStepInfo fallthroughInfo;

        if (!fallthroughInstruction
            || !decomposeNormalStep(event, *fallthroughStep, fallthroughInfo)
            || !fallthroughInfo.actions.empty()
            || fallthroughInfo.terminalInstruction != fallthroughInstruction
            || fallthroughInstruction->operation != LegacyLuaOperation::Compare
            || fallthroughInstruction->arguments.size() < 2)
        {
            ladderElseStep = fallthroughStep;
            break;
        }

        ladderStep = fallthroughStep;
    }

    if (arms.size() < 2)
    {
        return false;
    }

    std::optional<uint8_t> hoistedJoinStep;

    if (ladderElseStep)
    {
        const std::optional<uint8_t> joinStep = findCommonJoinStep(event, steps, arms.back().branchStart, ladderElseStep);

        if (joinStep && *joinStep != arms.back().branchStart && *joinStep != *ladderElseStep)
        {
            hoistedJoinStep = joinStep;
        }
    }

    std::vector<std::string> branchBodies;
    std::vector<std::vector<uint8_t>> branchVisitedSets;

    for (size_t armIndex = 0; armIndex < arms.size(); ++armIndex)
    {
        const CompareLadderArm &arm = arms[armIndex];
        std::ostringstream branchStream;
        std::vector<uint8_t> branchVisited = visited;
        std::optional<uint8_t> branchStep = arm.branchStart;
        const std::optional<uint8_t> stopStep =
            (hoistedJoinStep && armIndex == arms.size() - 1) ? hoistedJoinStep : std::nullopt;

        if (!emitReadableBlock(
                branchStream,
                event,
                steps,
                branchStep,
                stopStep,
                lookups,
                indentLevel + 1,
                branchVisited)
            || branchStep != stopStep)
        {
            return false;
        }

        branchBodies.push_back(branchStream.str());
        branchVisitedSets.push_back(std::move(branchVisited));
    }

    std::string elseBody;
    std::vector<uint8_t> elseVisited = visited;

    if (ladderElseStep)
    {
        std::ostringstream elseStream;
        std::optional<uint8_t> elseStep = ladderElseStep;
        const std::optional<uint8_t> stopStep = hoistedJoinStep;

        if (!emitReadableBlock(
                elseStream,
                event,
                steps,
                elseStep,
                stopStep,
                lookups,
                indentLevel + 1,
                elseVisited)
            || elseStep != stopStep)
        {
            return false;
        }

        elseBody = elseStream.str();
    }

    std::optional<std::string> hoistedSuffix;

    if (hoistedJoinStep)
    {
        std::ostringstream suffixStream;
        std::vector<uint8_t> suffixVisited = visited;
        std::optional<uint8_t> suffixStep = hoistedJoinStep;

        if (!emitReadableBlock(
                suffixStream,
                event,
                steps,
                suffixStep,
                std::nullopt,
                lookups,
                indentLevel,
                suffixVisited)
            || suffixStep)
        {
            return false;
        }

        hoistedSuffix = normalizeIndentation(suffixStream.str(), indentLevel - 1);

        for (uint8_t step : suffixVisited)
        {
            if (std::find(visited.begin(), visited.end(), step) == visited.end())
            {
                visited.push_back(step);
            }
        }
    }
    else if (ladderElseStep && !branchBodies.empty())
    {
        std::string branchPrefix;
        std::string elsePrefix;
        std::string commonSuffix;

        if (extractCommonSuffix(branchBodies.back(), elseBody, branchPrefix, elsePrefix, commonSuffix))
        {
            branchBodies.back() = branchPrefix;
            elseBody = elsePrefix;
            hoistedSuffix = normalizeIndentation(commonSuffix, indentLevel);
        }
    }

    for (size_t armIndex = 0; armIndex < arms.size(); ++armIndex)
    {
        const std::string keyword = (armIndex == 0) ? "if " : "elseif ";
        emitIndentedLineWithComment(
            stream,
            keyword + arms[armIndex].condition + " then",
            arms[armIndex].comment,
            indentLevel);
        stream << branchBodies[armIndex];
    }

    if (ladderElseStep)
    {
        emitIndentedLineWithComment(stream, "else", std::nullopt, indentLevel);
        stream << elseBody;
    }

    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

    if (hoistedSuffix)
    {
        stream << *hoistedSuffix;
    }

    for (uint8_t step : ladderSteps)
    {
        if (std::find(visited.begin(), visited.end(), step) == visited.end())
        {
            visited.push_back(step);
        }
    }

    for (const std::vector<uint8_t> &branchVisited : branchVisitedSets)
    {
        for (uint8_t step : branchVisited)
        {
            if (std::find(visited.begin(), visited.end(), step) == visited.end())
            {
                visited.push_back(step);
            }
        }
    }

    for (uint8_t step : elseVisited)
    {
        if (std::find(visited.begin(), visited.end(), step) == visited.end())
        {
            visited.push_back(step);
        }
    }

    currentStep = std::nullopt;
    return true;
}

bool tryEmitReadableGuardChainIfElse(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited)
{
    if (!currentStep)
    {
        return false;
    }

    std::vector<std::string> conditions;
    std::vector<std::optional<std::string>> comments;
    std::vector<uint8_t> chainSteps;
    std::optional<uint8_t> defaultStep;
    std::optional<uint8_t> specialStep;
    std::optional<uint8_t> step = currentStep;

    while (step)
    {
        const LegacyLuaInstruction *instruction = findInstructionByStep(event, *step);

        if (!instruction
            || !isReadableCompareOperation(instruction->operation)
            || instruction->arguments.size() < 2
            || !instruction->jumpTargetStep)
        {
            return false;
        }

        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo)
            || !stepInfo.actions.empty()
            || stepInfo.terminalInstruction != instruction)
        {
            return false;
        }

        std::string condition;
        std::optional<std::string> conditionComment;

        if (!formatReadableConditionInstruction(*instruction, lookups, condition, conditionComment))
        {
            return false;
        }

        std::optional<uint8_t> trueStep;
        std::optional<uint8_t> falseStep;

        if (!resolveSignificantStep(event, steps, instruction->jumpTargetStep, trueStep)
            || !resolveSignificantStep(event, steps, nextStepAfter(steps, *step), falseStep))
        {
            return false;
        }

        if (!falseStep)
        {
            return false;
        }

        if (!defaultStep)
        {
            defaultStep = falseStep;
        }
        else if (falseStep != defaultStep)
        {
            return false;
        }

        conditions.push_back(condition);
        comments.push_back(conditionComment);
        chainSteps.push_back(*step);

        const LegacyLuaInstruction *nextInstruction = trueStep ? findInstructionByStep(event, *trueStep) : nullptr;
        NormalStepInfo nextStepInfo;

        if (trueStep
            && nextInstruction
            && isReadableCompareOperation(nextInstruction->operation)
            && decomposeNormalStep(event, *trueStep, nextStepInfo)
            && nextStepInfo.actions.empty()
            && nextStepInfo.terminalInstruction == nextInstruction)
        {
            step = trueStep;
            continue;
        }

        specialStep = trueStep;
        break;
    }

    if (conditions.size() < 2 || !defaultStep || !specialStep || *defaultStep == *specialStep)
    {
        return false;
    }

    const std::optional<uint8_t> joinStep = findCommonJoinStep(event, steps, defaultStep, specialStep);

    if (!joinStep)
    {
        return false;
    }

    std::ostringstream specialStream;
    std::ostringstream defaultStream;
    std::vector<uint8_t> specialVisited = visited;
    std::vector<uint8_t> defaultVisited = visited;
    std::optional<uint8_t> specialBranchStep = specialStep;
    std::optional<uint8_t> defaultBranchStep = defaultStep;

    if (!emitReadableBlock(
            specialStream,
            event,
            steps,
            specialBranchStep,
            joinStep,
            lookups,
            indentLevel + 1,
            specialVisited)
        || !emitReadableBlock(
            defaultStream,
            event,
            steps,
            defaultBranchStep,
            joinStep,
            lookups,
            indentLevel + 1,
            defaultVisited)
        || specialBranchStep != joinStep
        || defaultBranchStep != joinStep)
    {
        return false;
    }

    std::string combinedCondition;

    for (size_t conditionIndex = 0; conditionIndex < conditions.size(); ++conditionIndex)
    {
        if (conditionIndex > 0)
        {
            combinedCondition += " and ";
        }

        combinedCondition += conditions[conditionIndex];
    }

    emitIndentedLineWithComment(stream, "if " + combinedCondition + " then", comments.front(), indentLevel);
    stream << specialStream.str();
    emitIndentedLineWithComment(stream, "else", std::nullopt, indentLevel);
    stream << defaultStream.str();
    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

    for (uint8_t chainStep : chainSteps)
    {
        if (std::find(visited.begin(), visited.end(), chainStep) == visited.end())
        {
            visited.push_back(chainStep);
        }
    }

    for (uint8_t visitedStep : specialVisited)
    {
        if (std::find(visited.begin(), visited.end(), visitedStep) == visited.end())
        {
            visited.push_back(visitedStep);
        }
    }

    for (uint8_t visitedStep : defaultVisited)
    {
        if (std::find(visited.begin(), visited.end(), visitedStep) == visited.end())
        {
            visited.push_back(visitedStep);
        }
    }

    currentStep = joinStep;
    return true;
}

bool tryEmitBranchToJoin(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const std::optional<std::string> &conditionComment,
    const std::string &condition,
    std::optional<uint8_t> branchStart,
    std::optional<uint8_t> joinStep,
    bool negateCondition,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited)
{
    if (!branchStart || !joinStep || branchStart == joinStep)
    {
        return false;
    }

    std::ostringstream branchStream;
    std::vector<uint8_t> branchVisited = visited;
    std::optional<uint8_t> branchStep = branchStart;

    if (!emitReadableBlock(branchStream, event, steps, branchStep, joinStep, lookups, indentLevel + 1, branchVisited))
    {
        return false;
    }

    if (!branchResolvedToStopOrTerminated(branchStep, joinStep))
    {
        return false;
    }

    const bool branchReachedJoinStep = branchStep && branchStep == joinStep;

    emitIndentedLineWithComment(
        stream,
        std::string("if ") + (negateCondition ? "not " : "") + condition + " then",
        conditionComment,
        indentLevel);
    stream << branchStream.str();
    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

    if (branchReachedJoinStep)
    {
        visited = std::move(branchVisited);
    }

    currentStep = joinStep;
    return true;
}

bool tryEmitIfElseToTermination(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const std::optional<std::string> &conditionComment,
    const std::string &condition,
    std::optional<uint8_t> trueBranchStart,
    std::optional<uint8_t> falseBranchStart,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited)
{
    if (!trueBranchStart || !falseBranchStart)
    {
        return false;
    }

    std::vector<uint8_t> trueReachable = collectReachableSteps(event, steps, trueBranchStart);
    std::vector<uint8_t> combinedReachable = std::move(trueReachable);
    const std::vector<uint8_t> falseReachable = collectReachableSteps(event, steps, falseBranchStart);

    for (uint8_t step : falseReachable)
    {
        if (std::find(combinedReachable.begin(), combinedReachable.end(), step) == combinedReachable.end())
        {
            combinedReachable.push_back(step);
        }
    }

    if (combinedReachable.size() > 128)
    {
        return false;
    }

    std::ostringstream trueStream;
    std::ostringstream falseStream;
    std::vector<uint8_t> trueVisited = visited;
    std::vector<uint8_t> falseVisited = visited;
    std::optional<uint8_t> trueStep = trueBranchStart;
    std::optional<uint8_t> falseStep = falseBranchStart;

    if (!emitReadableBlock(
            trueStream,
            event,
            steps,
            trueStep,
            std::nullopt,
            lookups,
            indentLevel + 1,
            trueVisited))
    {
        return false;
    }

    if (!emitReadableBlock(
            falseStream,
            event,
            steps,
            falseStep,
            std::nullopt,
            lookups,
            indentLevel + 1,
            falseVisited))
    {
        return false;
    }

    if (trueStep || falseStep)
    {
        return false;
    }

    const std::string trueBody = trueStream.str();
    const std::string falseBody = falseStream.str();
    std::string truePrefix;
    std::string falsePrefix;
    std::string commonSuffix;

    if (extractCommonSuffix(trueBody, falseBody, truePrefix, falsePrefix, commonSuffix))
    {
        emitIndentedLineWithComment(
            stream,
            "if " + condition + " then",
            conditionComment,
            indentLevel);
        stream << truePrefix;
        emitIndentedLineWithComment(stream, "else", std::nullopt, indentLevel);
        stream << falsePrefix;
        emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
        stream << commonSuffix;

        for (uint8_t step : trueVisited)
        {
            if (std::find(visited.begin(), visited.end(), step) == visited.end())
            {
                visited.push_back(step);
            }
        }

        for (uint8_t step : falseVisited)
        {
            if (std::find(visited.begin(), visited.end(), step) == visited.end())
            {
                visited.push_back(step);
            }
        }

        currentStep = std::nullopt;
        return true;
    }

    emitIndentedLineWithComment(
        stream,
        "if " + condition + " then",
        conditionComment,
        indentLevel);
    stream << trueStream.str();
    emitIndentedLineWithComment(stream, "else", std::nullopt, indentLevel);
    stream << falseStream.str();
    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

    for (uint8_t step : trueVisited)
    {
        if (std::find(visited.begin(), visited.end(), step) == visited.end())
        {
            visited.push_back(step);
        }
    }

    for (uint8_t step : falseVisited)
    {
        if (std::find(visited.begin(), visited.end(), step) == visited.end())
        {
            visited.push_back(step);
        }
    }

    currentStep = std::nullopt;
    return true;
}

bool tryEmitIfElseToCommonJoin(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    const std::optional<std::string> &conditionComment,
    const std::string &condition,
    std::optional<uint8_t> trueBranchStart,
    std::optional<uint8_t> falseBranchStart,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited)
{
    if (!trueBranchStart || !falseBranchStart)
    {
        return false;
    }

    const std::optional<uint8_t> joinStep = findCommonJoinStep(event, steps, trueBranchStart, falseBranchStart);

    if (!joinStep)
    {
        return false;
    }

    std::ostringstream trueStream;
    std::ostringstream falseStream;
    std::vector<uint8_t> trueVisited = visited;
    std::vector<uint8_t> falseVisited = visited;
    std::optional<uint8_t> trueStep = trueBranchStart;
    std::optional<uint8_t> falseStep = falseBranchStart;

    if (!emitReadableBlock(
            trueStream,
            event,
            steps,
            trueStep,
            joinStep,
            lookups,
            indentLevel + 1,
            trueVisited))
    {
        return false;
    }

    if (!emitReadableBlock(
            falseStream,
            event,
            steps,
            falseStep,
            joinStep,
            lookups,
            indentLevel + 1,
            falseVisited))
    {
        return false;
    }

    if (trueStep != joinStep || falseStep != joinStep)
    {
        return false;
    }

    const std::string trueBody = trueStream.str();
    const std::string falseBody = falseStream.str();

    if (trueBody.empty() && falseBody.empty())
    {
        currentStep = joinStep;
        return true;
    }

    if (trueBody.empty())
    {
        emitIndentedLineWithComment(
            stream,
            "if not " + condition + " then",
            conditionComment,
            indentLevel);
        stream << falseBody;
        emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

        for (uint8_t step : falseVisited)
        {
            if (std::find(visited.begin(), visited.end(), step) == visited.end())
            {
                visited.push_back(step);
            }
        }

        currentStep = joinStep;
        return true;
    }

    if (falseBody.empty())
    {
        emitIndentedLineWithComment(
            stream,
            "if " + condition + " then",
            conditionComment,
            indentLevel);
        stream << trueBody;
        emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

        for (uint8_t step : trueVisited)
        {
            if (std::find(visited.begin(), visited.end(), step) == visited.end())
            {
                visited.push_back(step);
            }
        }

        currentStep = joinStep;
        return true;
    }

    emitIndentedLineWithComment(
        stream,
        "if " + condition + " then",
        conditionComment,
        indentLevel);
    stream << trueBody;
    emitIndentedLineWithComment(stream, "else", std::nullopt, indentLevel);
    stream << falseBody;
    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

    for (uint8_t step : trueVisited)
    {
        if (std::find(visited.begin(), visited.end(), step) == visited.end())
        {
            visited.push_back(step);
        }
    }

    for (uint8_t step : falseVisited)
    {
        if (std::find(visited.begin(), visited.end(), step) == visited.end())
        {
            visited.push_back(step);
        }
    }

    currentStep = joinStep;
    return true;
}

bool tryEmitReadableLinearEventFunction(
    std::ostringstream &stream,
    std::string_view registerFunction,
    uint16_t eventId,
    const std::string &title,
    const std::optional<std::string> &hint,
    const LegacyLuaEvent &event,
    const LegacyLuaExportLookups &lookups)
{
    const std::vector<uint8_t> steps = collectNormalEventSteps(event);

    if (steps.empty())
    {
        return false;
    }

    for (uint8_t step : steps)
    {
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, step, stepInfo))
        {
            return false;
        }
    }

    emitEventRegistrationHeader(stream, registerFunction, eventId, title, hint);

    std::optional<uint8_t> currentStep = steps.front();
    std::vector<uint8_t> visited;

    if (!emitReadableBlock(stream, event, steps, currentStep, std::nullopt, lookups, 1, visited))
    {
        return false;
    }

    if (currentStep)
    {
        return false;
    }

    if (hint && !hint->empty())
    {
        stream << "end, " << luaQuoted(*hint) << ")\n";
    }
    else
    {
        stream << "end)\n";
    }

    return true;
}

bool tryEmitReadablePromptEventFunction(
    std::ostringstream &stream,
    std::string_view registerFunction,
    uint16_t eventId,
    const std::string &title,
    const std::optional<std::string> &hint,
    const LegacyLuaEvent &event,
    const LegacyLuaExportLookups &lookups)
{
    const std::vector<PromptContinuation> continuations = collectPromptContinuations(event);

    if (continuations.empty())
    {
        return false;
    }

    const std::vector<uint8_t> steps = collectNormalEventSteps(event);

    if (steps.empty())
    {
        return false;
    }

    for (uint8_t step : steps)
    {
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, step, stepInfo))
        {
            return false;
        }
    }

    stream << registerFunction << "(" << eventId << ", " << luaQuoted(title) << ", function(continueStep)\n";

    for (const PromptContinuation &continuation : continuations)
    {
        emitIndentedLineWithComment(
            stream,
            "if continueStep == " + std::to_string(continuation.continueStep) + " then",
            std::nullopt,
            1);

        std::optional<uint8_t> currentStep = continuation.continueStep;
        std::vector<uint8_t> visited;

        if (!emitReadableBlock(stream, event, steps, currentStep, std::nullopt, lookups, 2, visited))
        {
            return false;
        }

        if (currentStep)
        {
            return false;
        }

        emitIndentedLineWithComment(stream, "end", std::nullopt, 1);
    }

    if (!continuations.empty())
    {
        emitIndentedLineWithComment(stream, "if continueStep ~= nil then return end", std::nullopt, 1);
    }

    std::optional<uint8_t> currentStep = steps.front();
    std::vector<uint8_t> visited;

    if (!emitReadableBlock(stream, event, steps, currentStep, std::nullopt, lookups, 1, visited))
    {
        return false;
    }

    if (currentStep)
    {
        return false;
    }

    if (hint && !hint->empty())
    {
        stream << "end, " << luaQuoted(*hint) << ")\n";
    }
    else
    {
        stream << "end)\n";
    }

    return true;
}

void emitNormalInstruction(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const LegacyLuaInstruction &instruction,
    const LegacyLuaExportLookups &lookups,
    std::optional<uint8_t> nextStep,
    bool &stepTerminated)
{
    if (stepTerminated || isIgnoredNormalOperation(instruction.operation))
    {
        return;
    }

    switch (instruction.operation)
    {
        case LegacyLuaOperation::Exit:
            emitIndentedLineWithComment(stream, "return nil", std::nullopt, 2);
            stepTerminated = true;
            return;

        case LegacyLuaOperation::ForPartyMember:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ForPlayer(" + formatPartySelector(instruction.arguments[0]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::PlaySound:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.PlaySound(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[1])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[2])) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::Compare:
            if (instruction.arguments.size() >= 2 && instruction.jumpTargetStep)
            {
                const FormattedSelector selector = formatSelector(instruction.arguments[0]);
                emitIndentedLineWithComment(
                    stream,
                    "if " + formatCompareExpression(selector, instruction.arguments[1]) + " then return "
                    + std::to_string(*instruction.jumpTargetStep) + " end",
                    resolveSelectorComment(selector, lookups),
                    2);
            }
            break;

        case LegacyLuaOperation::Jump:
            if (instruction.jumpTargetStep)
            {
                emitIndentedLineWithComment(stream, "return " + std::to_string(*instruction.jumpTargetStep), std::nullopt, 2);
                stepTerminated = true;
                return;
            }
            break;

        case LegacyLuaOperation::MoveNpc:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.MoveNPC(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::RandomJump:
        {
            std::ostringstream line;
            line << "return PickRandomOption(" << event.eventId << ", "
                 << static_cast<unsigned>(instruction.step) << ", {";

            for (size_t argumentIndex = 0; argumentIndex < instruction.arguments.size(); ++argumentIndex)
            {
                if (argumentIndex > 0)
                {
                    line << ", ";
                }

                line << instruction.arguments[argumentIndex];
            }

            line << "})";
            emitIndentedLineWithComment(stream, line.str(), std::nullopt, 2);
            stepTerminated = true;
            return;
        }

        case LegacyLuaOperation::Add:
            if (instruction.arguments.size() >= 2)
            {
                const FormattedSelector selector = formatSelector(instruction.arguments[0]);
                emitIndentedLineWithComment(
                    stream,
                    formatAddExpression(selector, instruction.arguments[1]),
                    resolveSelectorComment(selector, lookups),
                    2);
            }
            break;

        case LegacyLuaOperation::Subtract:
            if (instruction.arguments.size() >= 2)
            {
                const FormattedSelector selector = formatSelector(instruction.arguments[0]);
                emitIndentedLineWithComment(
                    stream,
                    formatSubtractExpression(selector, instruction.arguments[1]),
                    resolveSelectorComment(selector, lookups),
                    2);
            }
            break;

        case LegacyLuaOperation::Set:
            if (instruction.arguments.size() >= 2)
            {
                const FormattedSelector selector = formatSelector(instruction.arguments[0]);
                emitIndentedLineWithComment(
                    stream,
                    formatSetExpression(selector, instruction.arguments[1]),
                    resolveSelectorComment(selector, lookups),
                    2);
            }
            break;

        case LegacyLuaOperation::ShowMessage:
            if (instruction.text && !instruction.text->empty())
            {
                emitIndentedLineWithComment(stream, "evt.SimpleMessage(" + luaQuoted(*instruction.text) + ")", std::nullopt, 2);
            }
            else if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "-- Missing legacy show message text " + std::to_string(instruction.arguments[0]),
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::StatusText:
            if (instruction.text && !instruction.text->empty())
            {
                emitIndentedLineWithComment(stream, "evt.StatusText(" + luaQuoted(*instruction.text) + ")", std::nullopt, 2);
            }
            else if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "-- Missing legacy status text " + std::to_string(instruction.arguments[0]),
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SpeakInHouse:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.EnterHouse(" + std::to_string(instruction.arguments[0]) + ")",
                    lookupText(lookups.houseNames, instruction.arguments[0]),
                    2);
            }
            break;

        case LegacyLuaOperation::SpeakNpc:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SpeakNPC(" + std::to_string(instruction.arguments[0]) + ")",
                    lookupText(lookups.npcNames, instruction.arguments[0]),
                    2);
            }
            break;

        case LegacyLuaOperation::MoveToMap:
        {
            if (instruction.arguments.size() >= 3)
            {
                std::ostringstream line;
                std::optional<std::string> mapComment;
                line << "evt.MoveToMap("
                     << static_cast<int32_t>(instruction.arguments[0]) << ", "
                     << static_cast<int32_t>(instruction.arguments[1]) << ", "
                     << static_cast<int32_t>(instruction.arguments[2]) << ", ";

                if (instruction.arguments.size() >= 4)
                {
                    line << static_cast<int32_t>(instruction.arguments[3]);
                }
                else
                {
                    line << "nil";
                }

                if (instruction.arguments.size() >= 5)
                {
                    line << ", " << static_cast<int32_t>(instruction.arguments[4]);
                }
                else
                {
                    line << ", nil";
                }

                if (instruction.arguments.size() >= 6)
                {
                    line << ", " << static_cast<int32_t>(instruction.arguments[5]);
                }
                else
                {
                    line << ", nil";
                }

                if (instruction.arguments.size() >= 7)
                {
                    line << ", " << instruction.arguments[6];
                }
                else
                {
                    line << ", nil";
                }

                if (instruction.arguments.size() >= 8)
                {
                    line << ", " << instruction.arguments[7];
                }
                else
                {
                    line << ", nil";
                }

                if (instruction.text && !instruction.text->empty())
                {
                    line << ", " << luaQuoted(*instruction.text);
                    mapComment = lookupMapName(lookups.mapNamesByFile, *instruction.text);
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), mapComment, 2);
            }
            break;
        }

        case LegacyLuaOperation::ChangeEvent:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ChangeEvent(" + std::to_string(instruction.arguments[0]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::OpenChest:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(stream, "evt.OpenChest(" + std::to_string(instruction.arguments[0]) + ")", std::nullopt, 2);
            }
            break;

        case LegacyLuaOperation::SummonMonsters:
            if (instruction.arguments.size() >= 8)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SummonMonsters(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[3])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[4])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[5])) + ", "
                    + std::to_string(instruction.arguments[6]) + ", "
                    + std::to_string(instruction.arguments[7]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SummonItem:
            if (instruction.arguments.size() >= 7)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SummonItem(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[1])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[2])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[3])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[4])) + ", "
                    + std::to_string(instruction.arguments[5]) + ", "
                    + (instruction.arguments[6] != 0 ? "true" : "false") + ")",
                    resolveSummonItemComment(instruction.arguments[0], lookups),
                    2);
            }
            break;

        case LegacyLuaOperation::GiveItem:
        {
            std::string expression;
            std::optional<std::string> comment;

            if (formatGiveItemCall(instruction, lookups, expression, comment))
            {
                emitIndentedLineWithComment(
                    stream,
                    expression,
                    comment,
                    2);
            }
            break;
        }

        case LegacyLuaOperation::CastSpell:
            if (instruction.arguments.size() >= 9)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.CastSpell(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[3])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[4])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[5])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[6])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[7])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[8])) + ")",
                    lookupText(lookups.spellNames, instruction.arguments[0]),
                    2);
            }
            break;

        case LegacyLuaOperation::ShowFace:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.FaceExpression(" + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::ReceiveDamage:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.DamagePlayer(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetSnow:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetSnow(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::ShowMovie:
            if (instruction.text && !instruction.text->empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ShowMovie(" + luaQuoted(*instruction.text) + ", "
                    + (!instruction.arguments.empty() && instruction.arguments[0] != 0 ? "true" : "false") + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetSprite:
            if (!instruction.arguments.empty())
            {
                std::ostringstream line;
                line << "evt.SetSprite(" << instruction.arguments[0];

                if (instruction.arguments.size() >= 2)
                {
                    line << ", " << instruction.arguments[1];
                }
                else
                {
                    line << ", 0";
                }

                if (instruction.text && !instruction.text->empty())
                {
                    line << ", " << luaQuoted(*instruction.text);
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), std::nullopt, 2);
            }
            break;

        case LegacyLuaOperation::ChangeDoorState:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetDoorState(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::StopAnimation:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(stream, "evt.StopDoor(" + std::to_string(instruction.arguments[0]) + ")", std::nullopt, 2);
            }
            break;

        case LegacyLuaOperation::SetTexture:
            if (!instruction.arguments.empty())
            {
                std::ostringstream line;
                line << "evt.SetTexture(" << instruction.arguments[0];

                if (instruction.text && !instruction.text->empty())
                {
                    line << ", " << luaQuoted(*instruction.text);
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), std::nullopt, 2);
            }
            break;

        case LegacyLuaOperation::ToggleIndoorLight:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetLight(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetFacetBit:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetFacetBit(" + std::to_string(instruction.arguments[0]) + ", "
                    + formatFacetBit(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetActorFlag:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetMonsterBit(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetActorGroupFlag:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetMonGroupBit(" + std::to_string(instruction.arguments[0]) + ", "
                    + formatMonsterBit(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetActorGroup:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetMonsterGroup(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetNpcTopic:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetNPCTopic(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetNpcGroupNews:
            if (instruction.arguments.size() >= 2)
            {
                emitNpcGroupNewsComments(stream, instruction.arguments[0], instruction.arguments[1], lookups, 2);
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetNPCGroupNews(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetNpcGreeting:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetNPCGreeting(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::SetNpcItem:
            if (instruction.arguments.size() >= 2)
            {
                std::ostringstream line;
                line << "evt.SetNPCItem(" << instruction.arguments[0] << ", " << instruction.arguments[1];

                if (instruction.arguments.size() >= 3)
                {
                    line << ", " << instruction.arguments[2];
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), std::nullopt, 2);
            }
            break;

        case LegacyLuaOperation::SetActorItem:
            if (instruction.arguments.size() >= 2)
            {
                std::ostringstream line;
                line << "evt.SetMonsterItem(" << instruction.arguments[0] << ", " << instruction.arguments[1];

                if (instruction.arguments.size() >= 3)
                {
                    line << ", " << instruction.arguments[2];
                }

                line << ")";
                emitIndentedLineWithComment(stream, line.str(), std::nullopt, 2);
            }
            break;

        case LegacyLuaOperation::CharacterAnimation:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.FaceAnimation(" + formatFaceAnimation(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::CheckItemsCount:
            if (instruction.arguments.size() >= 2 && instruction.jumpTargetStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if evt.CheckItemsCount(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ") then return "
                    + std::to_string(*instruction.jumpTargetStep) + " end",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::RemoveItems:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(stream, "evt.RemoveItems(" + std::to_string(instruction.arguments[0]) + ")", std::nullopt, 2);
            }
            break;

        case LegacyLuaOperation::CheckSkill:
            if (instruction.arguments.size() >= 3 && instruction.jumpTargetStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if evt.CheckSkill(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ") then return "
                    + std::to_string(*instruction.jumpTargetStep) + " end",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::IsActorKilled:
            if (instruction.arguments.size() >= 4 && instruction.jumpTargetStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if evt.CheckMonstersKilled(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ", "
                    + (instruction.arguments[3] != 0 ? "true" : "false") + ") then return "
                    + std::to_string(*instruction.jumpTargetStep) + " end",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::ChangeGroup:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ChangeGroupToGroup(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::ChangeGroupAlly:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ChangeGroupAlly(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::CheckSeason:
            if (!instruction.arguments.empty() && instruction.jumpTargetStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if evt.CheckSeason(" + std::to_string(instruction.arguments[0]) + ") then return "
                    + std::to_string(*instruction.jumpTargetStep) + " end",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::ToggleChestFlag:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetChestBit(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::InputString:
        {
            std::ostringstream line;
            line << "evt._InputString(" << event.eventId << ", " << static_cast<unsigned>(instruction.step + 1);

            if (!instruction.arguments.empty())
            {
                line << ", " << instruction.arguments[0];
            }
            else
            {
                line << ", 0";
            }

            if (instruction.text && !instruction.text->empty())
            {
                line << ", " << luaQuoted(*instruction.text);
            }

            line << ")";
            emitIndentedLineWithComment(stream, line.str(), std::nullopt, 2);
            emitIndentedLineWithComment(stream, "return nil", std::nullopt, 2);
            stepTerminated = true;
            return;
        }

        case LegacyLuaOperation::PressAnyKey:
            emitIndentedLineWithComment(
                stream,
                "evt._PressAnyKey(" + std::to_string(event.eventId) + ", "
                + std::to_string(static_cast<unsigned>(instruction.step + 1)) + ")",
                std::nullopt,
                2);
            emitIndentedLineWithComment(stream, "return nil", std::nullopt, 2);
            stepTerminated = true;
            return;

        case LegacyLuaOperation::SpecialJump:
        {
            std::ostringstream line;
            line << "evt._SpecialJump(";

            for (size_t argumentIndex = 0; argumentIndex < instruction.arguments.size(); ++argumentIndex)
            {
                if (argumentIndex > 0)
                {
                    line << ", ";
                }

                line << instruction.arguments[argumentIndex];
            }

            line << ")";
            emitIndentedLineWithComment(stream, line.str(), std::nullopt, 2);
            break;
        }

        case LegacyLuaOperation::IsTotalBountyHuntingAwardInRange:
            if (instruction.arguments.size() >= 2 && instruction.jumpTargetStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if evt.IsTotalBountyInRange(" + std::to_string(static_cast<int32_t>(instruction.arguments[0])) + ", "
                    + std::to_string(static_cast<int32_t>(instruction.arguments[1])) + ") then return "
                    + std::to_string(*instruction.jumpTargetStep) + " end",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::IsNpcInParty:
            if (!instruction.arguments.empty() && instruction.jumpTargetStep)
            {
                emitIndentedLineWithComment(
                    stream,
                    "if evt._IsNpcInParty(" + std::to_string(instruction.arguments[0]) + ") then return "
                    + std::to_string(*instruction.jumpTargetStep) + " end",
                    std::nullopt,
                    2);
            }
            break;

        case LegacyLuaOperation::CompareCanShowTopic:
        case LegacyLuaOperation::SetCanShowTopic:
        case LegacyLuaOperation::EndCanShowTopic:
        case LegacyLuaOperation::LocationName:
        case LegacyLuaOperation::Unknown:
        case LegacyLuaOperation::IsActorKilledCanShowTopic:
        case LegacyLuaOperation::TriggerMouseOver:
        case LegacyLuaOperation::TriggerOnLoadMap:
        case LegacyLuaOperation::TriggerOnLeaveMap:
        case LegacyLuaOperation::TriggerOnTimer:
        case LegacyLuaOperation::TriggerOnLongTimer:
        case LegacyLuaOperation::TriggerOnDateTimer:
        case LegacyLuaOperation::EnableDateTimer:
            break;
    }

}

void emitEventRegistrationHeader(
    std::ostringstream &stream,
    std::string_view registerFunction,
    uint16_t eventId,
    const std::string &title,
    const std::optional<std::string> &hint)
{
    stream << registerFunction << "(" << eventId << ", " << luaQuoted(title);

    if (registerFunction == "RegisterNoOpEvent" || registerFunction == "RegisterGlobalNoOpEvent")
    {
        if (hint && !hint->empty())
        {
            stream << ", " << luaQuoted(*hint);
        }

        stream << ")\n";
        return;
    }

    stream << ", function()\n";
}

void emitNormalEventFunction(
    std::ostringstream &stream,
    std::string_view tableName,
    const EvtEvent &sourceEvent,
    const LegacyLuaEvent &event,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups)
{
    const std::optional<std::string> hint = getLegacyHint(sourceEvent, strTable, lookups);
    const std::string title = buildGeneratedEventTitle(sourceEvent, strTable, lookups);
    const std::string_view registerFunction = tableName == LuaScopeGlobal ? "RegisterGlobalEvent" : "RegisterEvent";
    const std::string_view noOpFunction = tableName == LuaScopeGlobal ? "RegisterGlobalNoOpEvent" : "RegisterNoOpEvent";

    if (isNoOpEvent(event))
    {
        emitEventRegistrationHeader(stream, noOpFunction, event.eventId, title, hint);
        return;
    }

    std::ostringstream readableStream;

    if (tryEmitReadablePromptEventFunction(readableStream, registerFunction, event.eventId, title, hint, event, lookups))
    {
        stream << readableStream.str();
        return;
    }

    if (tryEmitReadableLinearEventFunction(readableStream, registerFunction, event.eventId, title, hint, event, lookups))
    {
        stream << readableStream.str();
        return;
    }

    emitEventRegistrationHeader(stream, registerFunction, event.eventId, title, hint);

    const std::vector<uint8_t> steps = collectNormalEventSteps(event);

    for (size_t stepIndex = 0; stepIndex < steps.size(); ++stepIndex)
    {
        const uint8_t step = steps[stepIndex];
        const std::optional<uint8_t> nextStep = stepIndex + 1 < steps.size()
            ? std::optional<uint8_t>(steps[stepIndex + 1])
            : std::nullopt;

        stream << "    local function Step_" << static_cast<unsigned>(step) << "()\n";
        bool stepTerminated = false;

        for (const LegacyLuaInstruction &instruction : event.instructions)
        {
            if (instruction.step != step)
            {
                continue;
            }

            emitNormalInstruction(stream, event, instruction, lookups, nextStep, stepTerminated);
        }

        if (!stepTerminated)
        {
            if (nextStep)
            {
                emitIndentedLineWithComment(stream, "return " + std::to_string(*nextStep), std::nullopt, 2);
            }
            else
            {
                emitIndentedLineWithComment(stream, "return nil", std::nullopt, 2);
            }
        }

        stream << "    end\n";
    }

    if (!steps.empty())
    {
        stream << "    local step = " << static_cast<unsigned>(steps.front()) << "\n";
        stream << "    while step ~= nil do\n";

        for (size_t stepIndex = 0; stepIndex < steps.size(); ++stepIndex)
        {
            const std::string_view branchPrefix = stepIndex == 0 ? "if" : "elseif";
            stream << "        " << branchPrefix << " step == " << static_cast<unsigned>(steps[stepIndex])
                   << " then\n";
            stream << "            step = Step_" << static_cast<unsigned>(steps[stepIndex]) << "()\n";
        }

        stream << "        else\n";
        stream << "            step = nil\n";
        stream << "        end\n";
        stream << "    end\n";
    }

    if (hint && !hint->empty())
    {
        stream << "end, " << luaQuoted(*hint) << ")\n";
    }
    else
    {
        stream << "end)\n";
    }
}

std::vector<uint8_t> collectCanShowTopicSuccessorSteps(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t step)
{
    CanShowTopicStepInfo stepInfo;

    if (!decomposeCanShowTopicStep(event, step, stepInfo))
    {
        return {};
    }

    if (stepInfo.actions.empty() && !stepInfo.terminalInstruction)
    {
        const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);
        return nextStep ? std::vector<uint8_t>{*nextStep} : std::vector<uint8_t>{};
    }

    if (!stepInfo.terminalInstruction)
    {
        const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);
        return nextStep ? std::vector<uint8_t>{*nextStep} : std::vector<uint8_t>{};
    }

    const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

    switch (instruction.operation)
    {
        case LegacyLuaOperation::EndCanShowTopic:
        case LegacyLuaOperation::Exit:
            return {};

        case LegacyLuaOperation::Jump:
            return instruction.jumpTargetStep ? std::vector<uint8_t>{*instruction.jumpTargetStep}
                                             : std::vector<uint8_t>{};

        case LegacyLuaOperation::CompareCanShowTopic:
        case LegacyLuaOperation::IsActorKilledCanShowTopic:
        {
            std::vector<uint8_t> successors;

            if (instruction.jumpTargetStep)
            {
                successors.push_back(*instruction.jumpTargetStep);
            }

            const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);

            if (nextStep && std::find(successors.begin(), successors.end(), *nextStep) == successors.end())
            {
                successors.push_back(*nextStep);
            }

            return successors;
        }

        default:
        {
            const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);
            return nextStep ? std::vector<uint8_t>{*nextStep} : std::vector<uint8_t>{};
        }
    }
}

std::vector<uint8_t> collectReachableCanShowTopicSteps(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep)
{
    std::vector<uint8_t> reachable;

    if (!startStep)
    {
        return reachable;
    }

    std::vector<uint8_t> stack = {*startStep};

    while (!stack.empty())
    {
        const uint8_t step = stack.back();
        stack.pop_back();

        if (std::find(reachable.begin(), reachable.end(), step) != reachable.end())
        {
            continue;
        }

        reachable.push_back(step);

        for (uint8_t successor : collectCanShowTopicSuccessorSteps(event, steps, step))
        {
            if (std::find(reachable.begin(), reachable.end(), successor) == reachable.end())
            {
                stack.push_back(successor);
            }
        }
    }

    return reachable;
}

bool allCanShowTopicPathsLeadToStepRecursive(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t step,
    uint8_t targetStep,
    std::vector<uint8_t> &activeSteps,
    std::map<uint8_t, bool> &memo)
{
    if (step == targetStep)
    {
        return true;
    }

    const std::map<uint8_t, bool>::const_iterator memoIterator = memo.find(step);

    if (memoIterator != memo.end())
    {
        return memoIterator->second;
    }

    if (std::find(activeSteps.begin(), activeSteps.end(), step) != activeSteps.end())
    {
        memo[step] = false;
        return false;
    }

    activeSteps.push_back(step);
    const std::vector<uint8_t> successors = collectCanShowTopicSuccessorSteps(event, steps, step);

    if (successors.empty())
    {
        activeSteps.pop_back();
        memo[step] = false;
        return false;
    }

    for (uint8_t successor : successors)
    {
        if (!allCanShowTopicPathsLeadToStepRecursive(event, steps, successor, targetStep, activeSteps, memo))
        {
            activeSteps.pop_back();
            memo[step] = false;
            return false;
        }
    }

    activeSteps.pop_back();
    memo[step] = true;
    return true;
}

bool allCanShowTopicPathsLeadToStep(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep,
    uint8_t targetStep)
{
    if (!startStep)
    {
        return false;
    }

    std::vector<uint8_t> activeSteps;
    std::map<uint8_t, bool> memo;
    return allCanShowTopicPathsLeadToStepRecursive(event, steps, *startStep, targetStep, activeSteps, memo);
}

std::optional<uint8_t> findCommonJoinStepForCanShowTopicBranches(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    const std::vector<uint8_t> &branchStarts)
{
    if (branchStarts.empty())
    {
        return std::nullopt;
    }

    for (uint8_t step : steps)
    {
        bool isJoinStep = true;

        for (uint8_t branchStart : branchStarts)
        {
            if (!allCanShowTopicPathsLeadToStep(event, steps, branchStart, step))
            {
                isJoinStep = false;
                break;
            }
        }

        if (isJoinStep)
        {
            return step;
        }
    }

    return std::nullopt;
}

bool emitReadableCanShowTopicActionInstruction(
    std::ostringstream &stream,
    const LegacyLuaInstruction &instruction,
    int indentLevel)
{
    switch (instruction.operation)
    {
        case LegacyLuaOperation::ForPartyMember:
            if (!instruction.arguments.empty())
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.ForPlayer(" + formatPartySelector(instruction.arguments[0]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetCanShowTopic:
            emitIndentedLineWithComment(
                stream,
                std::string("visible = ") + (!instruction.arguments.empty() && instruction.arguments[0] != 0 ? "true" : "false"),
                std::nullopt,
                indentLevel);
            return true;

        default:
            return false;
    }
}

bool emitReadableCanShowTopicBlock(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> &currentStep,
    std::optional<uint8_t> stopStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel,
    std::vector<uint8_t> &visited)
{
    while (currentStep && currentStep != stopStep)
    {
        if (std::find(visited.begin(), visited.end(), *currentStep) != visited.end())
        {
            return false;
        }

        visited.push_back(*currentStep);
        CanShowTopicStepInfo stepInfo;

        if (!decomposeCanShowTopicStep(event, *currentStep, stepInfo))
        {
            return false;
        }

        if (stepInfo.actions.empty() && !stepInfo.terminalInstruction)
        {
            currentStep = nextStepAfter(steps, *currentStep);
            continue;
        }

        for (const LegacyLuaInstruction *action : stepInfo.actions)
        {
            if (!emitReadableCanShowTopicActionInstruction(stream, *action, indentLevel))
            {
                return false;
            }
        }

        if (!stepInfo.terminalInstruction)
        {
            currentStep = nextStepAfter(steps, *currentStep);
            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::EndCanShowTopic
            || instruction.operation == LegacyLuaOperation::Exit)
        {
            emitIndentedLineWithComment(stream, "return visible", std::nullopt, indentLevel);
            currentStep = std::nullopt;
            continue;
        }

        if (instruction.operation == LegacyLuaOperation::Jump)
        {
            if (!instruction.jumpTargetStep)
            {
                return false;
            }

            currentStep = instruction.jumpTargetStep;
            continue;
        }

        if (instruction.operation != LegacyLuaOperation::CompareCanShowTopic
            && instruction.operation != LegacyLuaOperation::IsActorKilledCanShowTopic)
        {
            return false;
        }

        if (!instruction.jumpTargetStep)
        {
            return false;
        }

        std::string condition;
        std::optional<std::string> conditionComment;

        if (!formatReadableConditionInstruction(instruction, lookups, condition, conditionComment))
        {
            return false;
        }

        const std::optional<uint8_t> falseBranchStep = nextStepAfter(steps, *currentStep);
        const std::optional<uint8_t> trueBranchStep = instruction.jumpTargetStep;

        if (!trueBranchStep || !falseBranchStep)
        {
            return false;
        }

        const std::optional<uint8_t> joinStep =
            findCommonJoinStepForCanShowTopicBranches(event, steps, {*trueBranchStep, *falseBranchStep});

        if (joinStep && *joinStep != *trueBranchStep && *joinStep != *falseBranchStep)
        {
            std::ostringstream trueStream;
            std::ostringstream falseStream;
            std::vector<uint8_t> trueVisited = visited;
            std::vector<uint8_t> falseVisited = visited;
            std::optional<uint8_t> nestedTrueStep = trueBranchStep;
            std::optional<uint8_t> nestedFalseStep = falseBranchStep;

            if (!emitReadableCanShowTopicBlock(
                    trueStream,
                    event,
                    steps,
                    nestedTrueStep,
                    joinStep,
                    lookups,
                    indentLevel + 1,
                    trueVisited))
            {
                return false;
            }

            if (!emitReadableCanShowTopicBlock(
                    falseStream,
                    event,
                    steps,
                    nestedFalseStep,
                    joinStep,
                    lookups,
                    indentLevel + 1,
                    falseVisited))
            {
                return false;
            }

            if (nestedTrueStep != joinStep || nestedFalseStep != joinStep)
            {
                return false;
            }

            emitIndentedLineWithComment(stream, "if " + condition + " then", conditionComment, indentLevel);
            stream << trueStream.str();
            emitIndentedLineWithComment(stream, "else", std::nullopt, indentLevel);
            stream << falseStream.str();
            emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

            visited = std::move(trueVisited);

            for (uint8_t visitedStep : falseVisited)
            {
                if (std::find(visited.begin(), visited.end(), visitedStep) == visited.end())
                {
                    visited.push_back(visitedStep);
                }
            }

            currentStep = joinStep;
            continue;
        }

        std::ostringstream trueStream;
        std::ostringstream falseStream;
        std::vector<uint8_t> trueVisited = visited;
        std::vector<uint8_t> falseVisited = visited;
        std::optional<uint8_t> nestedTrueStep = trueBranchStep;
        std::optional<uint8_t> nestedFalseStep = falseBranchStep;

        if (!emitReadableCanShowTopicBlock(
                trueStream,
                event,
                steps,
                nestedTrueStep,
                std::nullopt,
                lookups,
                indentLevel + 1,
                trueVisited))
        {
            return false;
        }

        if (!emitReadableCanShowTopicBlock(
                falseStream,
                event,
                steps,
                nestedFalseStep,
                std::nullopt,
                lookups,
                indentLevel + 1,
                falseVisited))
        {
            return false;
        }

        if (nestedTrueStep || nestedFalseStep)
        {
            return false;
        }

        emitIndentedLineWithComment(stream, "if " + condition + " then", conditionComment, indentLevel);
        stream << trueStream.str();
        emitIndentedLineWithComment(stream, "else", std::nullopt, indentLevel);
        stream << falseStream.str();
        emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

        visited = std::move(trueVisited);

        for (uint8_t visitedStep : falseVisited)
        {
            if (std::find(visited.begin(), visited.end(), visitedStep) == visited.end())
            {
                visited.push_back(visitedStep);
            }
        }

        currentStep = std::nullopt;
    }

    return true;
}

bool tryEmitReadableCanShowTopicFunction(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const LegacyLuaExportLookups &lookups)
{
    const std::vector<uint8_t> steps = collectCanShowTopicSteps(event);

    if (steps.empty())
    {
        return false;
    }

    stream << "RegisterCanShowTopic(" << event.eventId << ", function()\n";
    emitIndentedLineWithComment(stream, "evt._BeginCanShowTopic(" + std::to_string(event.eventId) + ")", std::nullopt, 1);
    emitIndentedLineWithComment(stream, "local visible = true", std::nullopt, 1);

    std::optional<uint8_t> currentStep = steps.front();
    std::vector<uint8_t> visited;

    if (!emitReadableCanShowTopicBlock(stream, event, steps, currentStep, std::nullopt, lookups, 1, visited))
    {
        return false;
    }

    if (currentStep)
    {
        return false;
    }

    stream << "end)\n";
    return true;
}

void emitCanShowTopicFunction(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const LegacyLuaExportLookups &lookups)
{
    std::ostringstream readableStream;

    if (tryEmitReadableCanShowTopicFunction(readableStream, event, lookups))
    {
        stream << readableStream.str();
        return;
    }

    stream << "RegisterCanShowTopic(" << event.eventId << ", function()\n";
    stream << "    evt._BeginCanShowTopic(" << event.eventId << ")\n";
    stream << "    local _saw = false\n";
    stream << "    local _visible = true\n";
    stream << "    local _result = nil\n";

    const std::vector<uint8_t> steps = collectCanShowTopicSteps(event);

    for (size_t stepIndex = 0; stepIndex < steps.size(); ++stepIndex)
    {
        const uint8_t step = steps[stepIndex];
        const std::optional<uint8_t> nextStep = stepIndex + 1 < steps.size()
            ? std::optional<uint8_t>(steps[stepIndex + 1])
            : std::nullopt;

        stream << "    local function Step_" << static_cast<unsigned>(step) << "()\n";
        bool stepTerminated = false;

        for (const LegacyLuaInstruction &instruction : event.instructions)
        {
            if (instruction.step != step || stepTerminated)
            {
                continue;
            }

            switch (instruction.operation)
            {
                case LegacyLuaOperation::ForPartyMember:
                    if (!instruction.arguments.empty())
                    {
                        emitIndentedLineWithComment(
                            stream,
                            "evt.ForPlayer(" + formatPartySelector(instruction.arguments[0]) + ")",
                            std::nullopt,
                            2);
                    }
                    break;

                case LegacyLuaOperation::CompareCanShowTopic:
                    if (instruction.arguments.size() >= 2 && instruction.jumpTargetStep)
                    {
                        emitIndentedLineWithComment(stream, "_saw = true", std::nullopt, 2);
                        emitIndentedLineWithComment(
                            stream,
                            "if evt.Cmp(" + std::to_string(instruction.arguments[0]) + ", "
                            + std::to_string(static_cast<int32_t>(instruction.arguments[1])) + ") then return "
                            + std::to_string(*instruction.jumpTargetStep) + " end",
                            std::nullopt,
                            2);
                    }
                    break;

                case LegacyLuaOperation::IsActorKilledCanShowTopic:
                    if (instruction.arguments.size() >= 4 && instruction.jumpTargetStep)
                    {
                        emitIndentedLineWithComment(stream, "_saw = true", std::nullopt, 2);
                        emitIndentedLineWithComment(
                            stream,
                            "if evt.CheckMonstersKilled(" + std::to_string(instruction.arguments[0]) + ", "
                            + std::to_string(instruction.arguments[1]) + ", "
                            + std::to_string(instruction.arguments[2]) + ", "
                            + (instruction.arguments[3] != 0 ? "true" : "false") + ") then return "
                            + std::to_string(*instruction.jumpTargetStep) + " end",
                            std::nullopt,
                            2);
                    }
                    break;

                case LegacyLuaOperation::SetCanShowTopic:
                    emitIndentedLineWithComment(stream, "_saw = true", std::nullopt, 2);
                    emitIndentedLineWithComment(
                        stream,
                        std::string("_visible = ") + (!instruction.arguments.empty() && instruction.arguments[0] != 0 ? "true" : "false"),
                        std::nullopt,
                        2);
                    break;

                case LegacyLuaOperation::EndCanShowTopic:
                    emitIndentedLineWithComment(stream, "_result = _visible", std::nullopt, 2);
                    emitIndentedLineWithComment(stream, "return nil", std::nullopt, 2);
                    stepTerminated = true;
                    break;

                default:
                    emitIndentedLineWithComment(stream, "_result = _saw and _visible or true", std::nullopt, 2);
                    emitIndentedLineWithComment(stream, "return nil", std::nullopt, 2);
                    stepTerminated = true;
                    break;
            }
        }

        if (!stepTerminated)
        {
            if (nextStep)
            {
                emitIndentedLineWithComment(stream, "return " + std::to_string(*nextStep), std::nullopt, 2);
            }
            else
            {
                emitIndentedLineWithComment(stream, "return nil", std::nullopt, 2);
            }
        }

        stream << "    end\n";
    }

    if (!steps.empty())
    {
        stream << "    local step = " << static_cast<unsigned>(steps.front()) << "\n";
        stream << "    while step ~= nil do\n";

        for (size_t stepIndex = 0; stepIndex < steps.size(); ++stepIndex)
        {
            const std::string_view branchPrefix = stepIndex == 0 ? "if" : "elseif";
            stream << "        " << branchPrefix << " step == " << static_cast<unsigned>(steps[stepIndex])
                   << " then\n";
            stream << "            step = Step_" << static_cast<unsigned>(steps[stepIndex]) << "()\n";
        }

        stream << "        else\n";
        stream << "            step = nil\n";
        stream << "        end\n";
        stream << "    end\n";
    }

    stream << "    if _result == nil then _result = _saw and _visible or true end\n";
    stream << "    return _result\n";
    stream << "end)\n";
}

void emitMetadata(
    std::ostringstream &stream,
    const EvtProgram &evtProgram,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups,
    LegacyLuaExportScope scope)
{
    std::vector<std::string> textureNames;
    std::vector<std::string> spriteNames;
    std::vector<uint32_t> castSpellIds;
    collectSetTextureNames(evtProgram, textureNames);
    collectSetSpriteNames(evtProgram, spriteNames);
    collectCastSpellIds(evtProgram, castSpellIds);

    stream << (scope == LegacyLuaExportScope::Global ? "SetGlobalMetadata" : "SetMapMetadata") << "({\n";
    stream << "    onLoad = {";

    bool wroteEntry = false;

    for (const EvtEvent &event : evtProgram.getEvents())
    {
        if (!hasOnLoadTrigger(event))
        {
            continue;
        }

        if (wroteEntry)
        {
            stream << ", ";
        }

        stream << event.eventId;
        wroteEntry = true;
    }

    stream << "},\n";
    stream << "    openedChestIds = {\n";

    for (const EvtEvent &event : evtProgram.getEvents())
    {
        const std::vector<uint32_t> chestIds = getOpenedChestIds(event);

        if (chestIds.empty())
        {
            continue;
        }

        stream << "    [" << event.eventId << "] = {";

        for (size_t chestIndex = 0; chestIndex < chestIds.size(); ++chestIndex)
        {
            if (chestIndex > 0)
            {
                stream << ", ";
            }

            stream << chestIds[chestIndex];
        }

        stream << "},\n";
    }

    stream << "    },\n";
    stream << "    textureNames = {";

    for (size_t index = 0; index < textureNames.size(); ++index)
    {
        if (index > 0)
        {
            stream << ", ";
        }

        stream << luaQuoted(textureNames[index]);
    }

    stream << "},\n";
    stream << "    spriteNames = {";

    for (size_t index = 0; index < spriteNames.size(); ++index)
    {
        if (index > 0)
        {
            stream << ", ";
        }

        stream << luaQuoted(spriteNames[index]);
    }

    stream << "},\n";
    stream << "    castSpellIds = {";

    for (size_t index = 0; index < castSpellIds.size(); ++index)
    {
        if (index > 0)
        {
            stream << ", ";
        }

        stream << castSpellIds[index];
    }

    stream << "},\n";
    stream << "    timers = {\n";

    for (const EvtEvent &event : evtProgram.getEvents())
    {
        for (const EvtInstruction &instruction : event.instructions)
        {
            if (instruction.opcode != EvtOpcode::OnTimer)
            {
                continue;
            }

            if (instruction.listValues.size() > 6 && instruction.listValues[6] > 0)
            {
                const float intervalGameMinutes = static_cast<float>(instruction.listValues[6]) * 0.5f;
                stream << "    { eventId = " << event.eventId
                       << ", repeating = true"
                       << ", intervalGameMinutes = " << intervalGameMinutes
                       << ", remainingGameMinutes = " << intervalGameMinutes << " },\n";
                break;
            }

            if (instruction.listValues.size() > 3 && instruction.listValues[3] > 0)
            {
                float remainingGameMinutes = static_cast<float>(instruction.listValues[3]) * 60.0f - 9.0f * 60.0f;

                if (remainingGameMinutes < 0.0f)
                {
                    remainingGameMinutes += 24.0f * 60.0f;
                }

                stream << "    { eventId = " << event.eventId
                       << ", repeating = false"
                       << ", targetHour = " << static_cast<int>(instruction.listValues[3])
                       << ", intervalGameMinutes = " << (static_cast<float>(instruction.listValues[3]) * 60.0f)
                       << ", remainingGameMinutes = " << remainingGameMinutes << " },\n";
                break;
            }
        }
    }

    stream << "    },\n";
    stream << "})\n";
}
}

std::string generateLegacyEventLuaChunk(
    const EvtProgram &evtProgram,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups,
    LegacyLuaExportScope scope)
{
    const std::string_view scopeTableName = scope == LegacyLuaExportScope::Global ? LuaScopeGlobal : LuaScopeMap;
    const std::vector<LegacyLuaEvent> decodedEvents = decodeEvents(evtProgram, strTable, lookups);
    std::ostringstream stream;

    if (lookups.mapName && !lookups.mapName->empty())
    {
        stream << "-- " << sanitizeLuaCommentText(*lookups.mapName) << "\n";
    }

    stream << "-- generated from legacy EVT/STR\n\n";
    emitMetadata(stream, evtProgram, strTable, lookups, scope);
    stream << '\n';

    for (size_t eventIndex = 0; eventIndex < decodedEvents.size(); ++eventIndex)
    {
        const LegacyLuaEvent &event = decodedEvents[eventIndex];
        const EvtEvent &sourceEvent = evtProgram.getEvents()[eventIndex];

        if (luaExportTraceEnabled())
        {
            std::cerr << "lua_export "
                      << (scope == LegacyLuaExportScope::Global ? "global" : "map")
                      << " event=" << event.eventId << '\n';
        }

        emitNormalEventFunction(stream, scopeTableName, sourceEvent, event, strTable, lookups);

        if (scope == LegacyLuaExportScope::Global)
        {
            if (isCanShowTopicEvent(sourceEvent))
            {
                emitCanShowTopicFunction(stream, event, lookups);
            }
        }

        stream << '\n';
    }

    return stream.str();
}
}
