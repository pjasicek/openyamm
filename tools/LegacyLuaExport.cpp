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
constexpr size_t MaxReadableNormalEventLines = 4000;
constexpr size_t PreferCompactNormalEventLines = 180;

size_t countLuaLines(std::string_view luaText)
{
    size_t lineCount = 0;

    for (char character : luaText)
    {
        if (character == '\n')
        {
            ++lineCount;
        }
    }

    return lineCount;
}

bool readableNormalEventIsTooLarge(std::string_view luaText)
{
    return countLuaLines(luaText) > MaxReadableNormalEventLines;
}

void trimTrailingTopLevelReturn(std::ostringstream &stream)
{
    std::string text = stream.str();
    constexpr std::string_view trailingReturn = "    return\n";

    if (text.size() >= trailingReturn.size()
        && text.compare(text.size() - trailingReturn.size(), trailingReturn.size(), trailingReturn) == 0)
    {
        text.resize(text.size() - trailingReturn.size());
        stream.str(text);
        stream.clear();
        stream.seekp(0, std::ios_base::end);
    }
}

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
    SummonObject,
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
    AcknowledgeMessage,
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
    std::vector<std::string> inputAnswers;
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

std::optional<std::string> readPayloadString(const std::vector<uint8_t> &payload, size_t offset)
{
    if (offset > payload.size())
    {
        return std::nullopt;
    }

    std::string value;

    for (size_t index = offset; index < payload.size(); ++index)
    {
        if (payload[index] == 0)
        {
            return value;
        }

        value.push_back(static_cast<char>(payload[index]));
    }

    return std::nullopt;
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

std::string formatNpcReference(const LegacyLuaExportLookups &lookups, uint32_t npcId)
{
    const std::optional<std::string> npcName = lookupText(lookups.npcNames, npcId);

    if (npcName)
    {
        return *npcName;
    }

    return "NPC " + std::to_string(npcId);
}

std::optional<std::string> formatMoveNpcComment(
    const LegacyLuaExportLookups &lookups,
    uint32_t npcId,
    uint32_t houseId)
{
    std::string destination;

    if (houseId == 0)
    {
        destination = "removed";
    }
    else
    {
        const std::optional<std::string> houseName = lookupText(lookups.houseNames, houseId);
        destination = houseName ? *houseName : "house " + std::to_string(houseId);
    }

    return formatNpcReference(lookups, npcId) + " -> " + destination;
}

std::optional<std::string> formatSetNpcTopicComment(
    const LegacyLuaExportLookups &lookups,
    uint32_t npcId,
    uint32_t topicSlot,
    uint32_t topicId)
{
    const std::string npcName = formatNpcReference(lookups, npcId);
    const std::string slotText = " topic " + std::to_string(topicSlot);

    if (topicId == 0)
    {
        return npcName + slotText + " cleared";
    }

    const std::optional<std::string> topicName = lookupText(lookups.npcTopicNames, topicId);

    if (topicName)
    {
        return npcName + slotText + ": " + *topicName;
    }

    return npcName + slotText + " -> topic " + std::to_string(topicId);
}

std::optional<std::string> formatSetNpcGreetingComment(
    const LegacyLuaExportLookups &lookups,
    uint32_t npcId,
    uint32_t greetingId)
{
    const std::string npcName = formatNpcReference(lookups, npcId);

    if (greetingId == 0)
    {
        return npcName + " greeting cleared";
    }

    const std::optional<std::string> greetingText = lookupText(lookups.npcGreetingTexts, greetingId);

    if (greetingText)
    {
        return npcName + " greeting: " + *greetingText;
    }

    return npcName + " greeting " + std::to_string(greetingId);
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
        case 0x00000010: return "FacetBits.Fluid";
        case 0x00040000: return "FacetBits.MoveByDoor";
        case 0x20000000: return "FacetBits.Untouchable";
        default: return std::to_string(value);
    }
}

std::string formatSignedInt32(uint32_t value)
{
    if (value <= static_cast<uint32_t>(std::numeric_limits<int32_t>::max()))
    {
        return std::to_string(value);
    }

    return std::to_string(static_cast<int64_t>(value) - (static_cast<int64_t>(UINT32_MAX) + 1));
}

std::string formatLegacyReferenceId(uint32_t value)
{
    if (value <= static_cast<uint32_t>(std::numeric_limits<int32_t>::max()))
    {
        return std::to_string(value);
    }

    const int64_t signedValue = static_cast<int64_t>(value) - (static_cast<int64_t>(UINT32_MAX) + 1);
    return std::to_string(signedValue < 0 ? -signedValue : signedValue);
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

std::string formatActorKillCheck(uint32_t value)
{
    switch (static_cast<EvtActorKillCheck>(value))
    {
        case EvtActorKillCheck::Any: return "ActorKillCheck.Any";
        case EvtActorKillCheck::Group: return "ActorKillCheck.Group";
        case EvtActorKillCheck::MonsterId: return "ActorKillCheck.MonsterId";
        case EvtActorKillCheck::ActorIdOe: return "ActorKillCheck.ActorIdOe";
        case EvtActorKillCheck::UniqueNameId: return "ActorKillCheck.UniqueNameId";
    }

    return std::to_string(value);
}

std::string formatActorKilledCountComment(uint32_t count)
{
    if (count == 0)
    {
        return "all matching actors defeated";
    }

    return "at least " + std::to_string(count) + " matching actor" + (count == 1 ? "" : "s") + " defeated";
}

std::optional<std::string> formatActorKilledComment(
    uint32_t checkType,
    uint32_t id,
    uint32_t count,
    const LegacyLuaExportLookups &lookups)
{
    std::string target;

    switch (static_cast<EvtActorKillCheck>(checkType))
    {
        case EvtActorKillCheck::Any:
            target = "any actor";
            break;

        case EvtActorKillCheck::Group:
            target = "actor group " + std::to_string(id);

            if (const std::optional<std::string> groupName = lookupText(lookups.actorGroupNames, id))
            {
                target += ": " + *groupName;
            }

            break;

        case EvtActorKillCheck::MonsterId:
        {
            const uint32_t monsterStatsId = id + 1u;
            target = "monster " + std::to_string(id);

            const std::optional<std::string> monsterName = lookupText(lookups.monsterNames, monsterStatsId);

            if (monsterName)
            {
                target += " \"" + *monsterName + "\"";
            }

            break;
        }

        case EvtActorKillCheck::ActorIdOe:
            target = "OE actor " + std::to_string(id);
            break;

        case EvtActorKillCheck::UniqueNameId:
        {
            target = "unique actor " + std::to_string(id);
            const std::optional<std::string> uniqueName = lookupText(lookups.placedMonsterNames, id);

            if (uniqueName)
            {
                target += " \"" + *uniqueName + "\"";
            }

            break;
        }
    }

    if (target.empty())
    {
        return std::nullopt;
    }

    return target + "; " + formatActorKilledCountComment(count);
}

std::string formatDoorAction(uint32_t value)
{
    switch (value)
    {
        case 0: return "DoorAction.Open";
        case 1: return "DoorAction.Close";
        case 2: return "DoorAction.Trigger";
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

uint32_t mapLegacyPlayerSelector(uint32_t value, LegacyEventVersion version)
{
    if (version != LegacyEventVersion::Mm8 && value == 4)
    {
        return static_cast<uint32_t>(EvtPartySelector::Current);
    }

    return value;
}

uint32_t mapLegacyDamageType(uint32_t value, LegacyEventVersion version)
{
    if (version != LegacyEventVersion::Mm6)
    {
        return value;
    }

    switch (value)
    {
        case 0: return 4;  // Physical
        case 1: return 5;  // Magic
        case 2: return 0;  // Fire
        case 3: return 1;  // Electric -> Air
        case 4: return 2;  // Cold -> Water
        case 5: return 8;  // Poison -> Body
        case 6: return 12; // Energy
        default: return value;
    }
}

uint32_t mapLegacySkillId(uint32_t value, LegacyEventVersion version)
{
    if (version == LegacyEventVersion::Mm8)
    {
        return value;
    }

    if (value <= 20)
    {
        return value;
    }

    switch (value)
    {
        case 21: return 24; // Identify Item
        case 22: return 25; // Merchant
        case 23: return 26; // Repair
        case 24: return 27; // Bodybuilding
        case 25: return 28; // Meditation
        case 26: return 29; // Perception
        case 29: return 31; // Disarm Trap
        default: break;
    }

    if (version == LegacyEventVersion::Mm6)
    {
        switch (value)
        {
            case 30: return 38; // Learning
            default: return value;
        }
    }

    switch (value)
    {
        case 30: return 32; // Dodge
        case 31: return 33; // Unarmed
        case 32: return 34; // Identify Monster
        case 33: return 35; // Armsmaster
        case 34: return 36; // Stealing
        case 35: return 37; // Alchemy
        case 36: return 38; // Learning
        default: return value;
    }
}

uint32_t mapLegacySpellId(uint32_t value, LegacyEventVersion version)
{
    if (version == LegacyEventVersion::Mm8)
    {
        return value;
    }

    if (version == LegacyEventVersion::Mm7)
    {
        switch (value)
        {
            case 56: return 57; // Remove Fear
            case 57: return 59; // Mind Blast
            case 59: return 56; // Telepathy
            case 96: return 96; // Sacrifice has no exact MM8 canonical equivalent yet.
            default: return value;
        }
    }

    switch (value)
    {
        case 2: return 2;   // Flame Arrow -> Fire Bolt
        case 3: return 3;   // Protection From Fire -> Fire Resistance
        case 4: return 2;   // Fire Bolt
        case 7: return 7;   // Ring Of Fire -> Fire Spike
        case 8: return 6;   // Fire Blast -> Fireball
        case 13: return 15; // Static Charge -> Sparks
        case 14: return 14; // Protection From Electricity -> Air Resistance
        case 16: return 13; // Feather Fall
        case 19: return 16; // Jump
        case 24: return 26; // Cold Beam -> Ice Bolt
        case 25: return 25; // Protection From Cold -> Water Resistance
        case 26: return 24; // Poison Spray
        case 28: return 26; // Ice Bolt
        case 29: return 30; // Enchant Item
        case 30: return 29; // Acid Burst
        case 35: return 34; // Magic Arrow -> Stun
        case 36: return 75; // Protection From Magic
        case 42: return 81; // Turn To Stone -> Paralyze
        case 45: return 52; // Spirit Arrow -> Spirit Lash
        case 47: return 68; // Healing Touch -> Heal
        case 48: return 47; // Lucky Day -> Fate
        case 50: return 50; // Guardian Angel -> Preservation
        case 52: return 48; // Turn Undead
        case 57: return 57; // Remove Fear
        case 58: return 59; // Mind Blast
        case 60: return 61; // Cure Paralysis
        case 61: return 60; // Charm
        case 62: return 63; // Mass Fear
        case 66: return 42; // Telekinesis
        case 68: return 68; // First Aid -> Heal
        case 69: return 69; // Protection From Poison -> Body Resistance
        case 71: return 68; // Cure Wounds -> Heal
        case 73: return 5;  // Speed -> Haste
        case 75: return 51; // Power -> Heroism
        case 81: return 35; // Slow
        case 82: return 79; // Destroy Undead
        case 85: return 86; // Hour Of Power
        case 86: return 81; // Paralyze
        case 87: return 87; // Sun Ray
        case 91: return 63; // Mass Curse -> Mass Fear
        case 92: return 93; // Shrapmetal
        case 93: return 92; // Shrinking Ray
        case 94: return 85; // Day Of Protection
        case 95: return 96; // Finger Of Death -> Dark Grasp
        case 96: return 84; // Moon Ray -> Prismatic Light
        case 99: return 96; // Dark Containment -> Dark Grasp
        default: return value;
    }
}

uint32_t eventStepKey(uint32_t eventId, uint32_t step)
{
    return (eventId << 8) | step;
}

EvtVariable canonicalMm8Variable(uint32_t rawVariableId, uint32_t index)
{
    if (rawVariableId == 0x00E1u && index != 0)
    {
        return EvtVariable::AutoNotes;
    }

    if (rawVariableId == 0x00F5u)
    {
        return EvtVariable::NumSkillPoints;
    }

    if (rawVariableId >= 0x00F7u && rawVariableId <= 0x0100u)
    {
        return static_cast<EvtVariable>(
            static_cast<uint32_t>(EvtVariable::Counter1) + rawVariableId - 0x00F7u);
    }

    switch (rawVariableId)
    {
        case 0x00E9u: return EvtVariable::PlayerBits;
        case 0x00F2u: return EvtVariable::IsFlying;
        case 0x00F3u: return EvtVariable::HiredNpcHasSpeciality;
        case 0x00F4u: return EvtVariable::CircusPrises;
        case 0x00F6u: return EvtVariable::MonthIs;
        case 0x0115u: return EvtVariable::ReputationInCurrentLocation;
        case 0x0133u: return EvtVariable::Unknown1;
        case 0x0134u: return EvtVariable::GoldInBank;
        case 0x0135u: return EvtVariable::NumDeaths;
        case 0x0136u: return EvtVariable::NumBounties;
        case 0x0137u: return EvtVariable::PrisonTerms;
        case 0x0138u: return EvtVariable::ArenaWinsPage;
        case 0x0139u: return EvtVariable::ArenaWinsSquire;
        case 0x013Au: return EvtVariable::ArenaWinsKnight;
        case 0x013Bu: return EvtVariable::ArenaWinsLord;
        case 0x013Cu: return EvtVariable::Invisible;
        case 0x013Du: return EvtVariable::ItemEquipped;
        case 0x013Eu: return EvtVariable::Players;
        default: return static_cast<EvtVariable>(rawVariableId);
    }
}

FormattedSelector formatSelector(uint32_t rawValue)
{
    const uint32_t rawVariableId = rawValue & 0xFFFFu;
    const uint32_t index = rawValue >> 16;
    const EvtVariable variableId = canonicalMm8Variable(rawVariableId, index);

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

    if (selector.semantic == SelectorSemantic::QBit)
    {
        return lookupText(lookups.questNotes, selector.index);
    }

    if (selector.semantic == SelectorSemantic::Award)
    {
        return lookupText(lookups.awardTexts, selector.index);
    }

    if (selector.semantic == SelectorSemantic::PlayerValue)
    {
        return lookupText(lookups.rosterNames, selector.index);
    }

    if (selector.semantic == SelectorSemantic::Autonote)
    {
        return lookupText(lookups.autonoteTexts, selector.index);
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
            case SelectorSemantic::Autonote: return "IsAutonoteSet(" + std::to_string(selector.index) + ")";
            case SelectorSemantic::PlayerBit: return "IsPlayerBitSet(" + selector.expression + ")";
            default: break;
        }
    }

    if (selector.semantic == SelectorSemantic::InventoryItem && value == selector.index)
    {
        return "HasItem(" + std::to_string(selector.index) + ")";
    }

    if (selector.semantic == SelectorSemantic::PlayerValue && value == selector.index)
    {
        return "HasPlayer(" + std::to_string(selector.index) + ")";
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
            case SelectorSemantic::Autonote: return "SetAutonote(" + std::to_string(selector.index) + ")";
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
            case SelectorSemantic::Autonote: return "ClearAutonote(" + std::to_string(selector.index) + ")";
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
            case SelectorSemantic::Autonote: return "SetAutonote(" + std::to_string(selector.index) + ")";
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

LegacyLuaOperation mapOperation(EvtOpcode opcode, LegacyEventVersion version)
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
        case EvtOpcode::SummonItem:
            return version == LegacyEventVersion::Mm8
                ? LegacyLuaOperation::SummonItem
                : LegacyLuaOperation::SummonObject;
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
        case EvtOpcode::PressAnyKey:
            return version == LegacyEventVersion::Mm8
                ? LegacyLuaOperation::PressAnyKey
                : LegacyLuaOperation::AcknowledgeMessage;
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

bool hasOnLeaveTrigger(const EvtEvent &event)
{
    return std::any_of(
        event.instructions.begin(),
        event.instructions.end(),
        [](const EvtInstruction &instruction)
        {
            return instruction.opcode == EvtOpcode::OnMapLeave;
        });
}

bool isIgnoredSourceNormalOpcode(EvtOpcode opcode)
{
    switch (opcode)
    {
        case EvtOpcode::MouseOver:
        case EvtOpcode::OnMapReload:
        case EvtOpcode::OnMapLeave:
        case EvtOpcode::OnTimer:
        case EvtOpcode::OnLongTimer:
        case EvtOpcode::OnDateTimer:
        case EvtOpcode::OnCanShowDialogItemCmp:
        case EvtOpcode::SetCanShowDialogItem:
        case EvtOpcode::EndCanShowDialogItem:
        case EvtOpcode::LocationName:
        case EvtOpcode::EnableDateTimer:
        case EvtOpcode::CanShowTopicIsActorKilled:
        case EvtOpcode::Invalid:
            return true;

        default:
            return false;
    }
}

std::optional<uint8_t> firstSourceNormalStep(const EvtEvent &event)
{
    for (const EvtInstruction &instruction : event.instructions)
    {
        if (!isIgnoredSourceNormalOpcode(instruction.opcode))
        {
            return instruction.step;
        }
    }

    return std::nullopt;
}

std::optional<uint8_t> triggerContinuationStep(const EvtEvent &event, EvtOpcode triggerOpcode)
{
    for (const EvtInstruction &instruction : event.instructions)
    {
        if (instruction.opcode == triggerOpcode)
        {
            return static_cast<uint8_t>(instruction.step + 1);
        }
    }

    return std::nullopt;
}

bool triggerNeedsSyntheticEntry(const EvtEvent &event, EvtOpcode triggerOpcode)
{
    const std::optional<uint8_t> continuationStep = triggerContinuationStep(event, triggerOpcode);
    const std::optional<uint8_t> firstNormalStep = firstSourceNormalStep(event);

    return continuationStep && firstNormalStep && *continuationStep != *firstNormalStep;
}

struct SyntheticTriggerEvent
{
    uint16_t syntheticEventId = 0;
    uint16_t sourceEventId = 0;
    uint8_t continuationStep = 0;
    EvtOpcode triggerOpcode = EvtOpcode::Invalid;
};

bool eventIdExists(const EvtProgram &evtProgram, uint16_t eventId)
{
    return std::any_of(
        evtProgram.getEvents().begin(),
        evtProgram.getEvents().end(),
        [eventId](const EvtEvent &event)
        {
            return event.eventId == eventId;
        });
}

std::vector<SyntheticTriggerEvent> collectSyntheticTriggerEvents(const EvtProgram &evtProgram)
{
    std::vector<SyntheticTriggerEvent> syntheticEvents;
    uint16_t nextSyntheticEventId = 65535;

    const auto reserveSyntheticEventId =
        [&evtProgram, &syntheticEvents, &nextSyntheticEventId]() -> uint16_t
        {
            while (eventIdExists(evtProgram, nextSyntheticEventId)
                || std::any_of(
                    syntheticEvents.begin(),
                    syntheticEvents.end(),
                    [nextSyntheticEventId](const SyntheticTriggerEvent &event)
                    {
                        return event.syntheticEventId == nextSyntheticEventId;
                    }))
            {
                --nextSyntheticEventId;
            }

            return nextSyntheticEventId--;
        };

    const auto addSyntheticTrigger =
        [&syntheticEvents, &reserveSyntheticEventId](const EvtEvent &event, EvtOpcode triggerOpcode)
        {
            const std::optional<uint8_t> continuationStep = triggerContinuationStep(event, triggerOpcode);

            if (!continuationStep || !triggerNeedsSyntheticEntry(event, triggerOpcode))
            {
                return;
            }

            SyntheticTriggerEvent syntheticEvent = {};
            syntheticEvent.syntheticEventId = reserveSyntheticEventId();
            syntheticEvent.sourceEventId = event.eventId;
            syntheticEvent.continuationStep = *continuationStep;
            syntheticEvent.triggerOpcode = triggerOpcode;
            syntheticEvents.push_back(syntheticEvent);
        };

    for (const EvtEvent &event : evtProgram.getEvents())
    {
        addSyntheticTrigger(event, EvtOpcode::OnMapReload);
        addSyntheticTrigger(event, EvtOpcode::OnMapLeave);
    }

    return syntheticEvents;
}

std::optional<uint16_t> findSyntheticTriggerEventId(
    const std::vector<SyntheticTriggerEvent> &syntheticEvents,
    uint16_t sourceEventId,
    EvtOpcode triggerOpcode)
{
    for (const SyntheticTriggerEvent &event : syntheticEvents)
    {
        if (event.sourceEventId == sourceEventId && event.triggerOpcode == triggerOpcode)
        {
            return event.syntheticEventId;
        }
    }

    return std::nullopt;
}

std::optional<std::string> resolveInstructionText(
    const EvtInstruction &instruction,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups)
{
    if (instruction.opcode == EvtOpcode::ShowMessage
        || instruction.opcode == EvtOpcode::StatusText
        || instruction.opcode == EvtOpcode::InputString)
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
    const LegacyLuaExportLookups &lookups,
    LegacyEventVersion version)
{
    LegacyLuaInstruction decoded = {};
    decoded.eventId = eventId;
    decoded.step = instruction.step;
    decoded.operation = mapOperation(instruction.opcode, version);
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

    if (decoded.operation == LegacyLuaOperation::InputString && decoded.arguments.size() >= 2)
    {
        for (size_t argumentIndex = 1; argumentIndex < decoded.arguments.size(); ++argumentIndex)
        {
            const uint32_t answerTextId = decoded.arguments[argumentIndex];
            std::optional<std::string> answer = strTable.get(answerTextId);

            if (!answer)
            {
                answer = lookupText(lookups.inputStringAnswerTexts, answerTextId);
            }

            if (answer && !answer->empty())
            {
                decoded.inputAnswers.push_back(*answer);
            }
        }
    }

    if (decoded.operation == LegacyLuaOperation::ForPartyMember)
    {
        decoded.arguments.clear();

        for (uint8_t value : instruction.listValues)
        {
            decoded.arguments.push_back(mapLegacyPlayerSelector(value, version));
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
        else if (version == LegacyEventVersion::Mm6 && typeIndex && level && count && x && y && z)
        {
            decoded.arguments = {
                *typeIndex,
                *level,
                *count,
                static_cast<uint32_t>(*x),
                static_cast<uint32_t>(*y),
                static_cast<uint32_t>(*z),
                0,
                0
            };
        }
    }
    else if (decoded.operation == LegacyLuaOperation::SummonItem
        || decoded.operation == LegacyLuaOperation::SummonObject)
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
            uint32_t objectType = *objectId;

            if (decoded.operation == LegacyLuaOperation::SummonObject)
            {
                const auto overrideIterator =
                    lookups.summonObjectTypesByEventStep.find(eventStepKey(eventId, instruction.step));

                if (overrideIterator != lookups.summonObjectTypesByEventStep.end())
                {
                    objectType = overrideIterator->second;
                }
            }

            decoded.arguments = {
                objectType,
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
                mapLegacySpellId(*spellId, version),
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
        std::optional<uint32_t> houseId;

        if (version == LegacyEventVersion::Mm8)
        {
            if (const std::optional<uint16_t> value = readPayloadValue<uint16_t>(instruction.rawPayload, 24))
            {
                houseId = *value;
            }
        }
        else if (const std::optional<uint8_t> value = readPayloadValue<uint8_t>(instruction.rawPayload, 24))
        {
            houseId = *value;
        }

        const size_t iconOffset = version == LegacyEventVersion::Mm8 ? 26 : 25;
        const size_t mapNameOffset = version == LegacyEventVersion::Mm8 ? 27 : 26;
        const std::optional<uint8_t> exitPicId = readPayloadValue<uint8_t>(instruction.rawPayload, iconOffset);

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

        decoded.text = readPayloadString(instruction.rawPayload, mapNameOffset);
    }

    if (decoded.operation == LegacyLuaOperation::ShowFace
        || decoded.operation == LegacyLuaOperation::CharacterAnimation)
    {
        if (!decoded.arguments.empty())
        {
            decoded.arguments[0] = mapLegacyPlayerSelector(decoded.arguments[0], version);
        }
    }

    if (decoded.operation == LegacyLuaOperation::ReceiveDamage)
    {
        if (decoded.arguments.size() >= 2)
        {
            decoded.arguments[0] = mapLegacyPlayerSelector(decoded.arguments[0], version);
            decoded.arguments[1] = mapLegacyDamageType(decoded.arguments[1], version);
        }
    }

    if (decoded.operation == LegacyLuaOperation::CheckSkill && !decoded.arguments.empty())
    {
        decoded.arguments[0] = mapLegacySkillId(decoded.arguments[0], version);
    }

    return decoded;
}

std::vector<LegacyLuaEvent> decodeEvents(
    const EvtProgram &evtProgram,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups,
    LegacyEventVersion version)
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
                decodeInstruction(event.eventId, instruction, strTable, lookups, version));
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

void collectCastSpellIds(
    const EvtProgram &evtProgram,
    std::vector<uint32_t> &spellIds,
    LegacyEventVersion version)
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
                spellIds.push_back(mapLegacySpellId(*spellId, version));
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
        case LegacyLuaOperation::AcknowledgeMessage:
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
    if (payload == 0)
    {
        return std::nullopt;
    }

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

std::optional<std::string> formatNpcGroupNewsComment(
    uint32_t groupId,
    uint32_t newsId,
    const LegacyLuaExportLookups &lookups)
{
    const std::optional<std::string> groupName = lookupText(lookups.npcGroupNames, groupId);
    const std::optional<std::string> newsText = lookupText(lookups.npcNewsTexts, newsId);
    std::string comment;

    if (groupName && !groupName->empty())
    {
        comment = "NPC group " + std::to_string(groupId) + " \"" + *groupName + "\" -> news "
            + std::to_string(newsId);
    }

    if (newsText && !newsText->empty())
    {
        if (!comment.empty())
        {
            comment += ": ";
        }

        comment += "\"" + *newsText + "\"";
    }

    if (comment.empty())
    {
        return std::nullopt;
    }

    return comment;
}

std::optional<std::string> formatActorGroupComment(
    uint32_t groupId,
    const LegacyLuaExportLookups &lookups)
{
    const std::optional<std::string> groupName = lookupText(lookups.actorGroupNames, groupId);

    if (!groupName || groupName->empty())
    {
        return std::nullopt;
    }

    return "actor group " + std::to_string(groupId) + ": " + *groupName;
}

char summonMonsterTierLetter(uint32_t level)
{
    const uint32_t clampedLevel = std::clamp(level, 1u, 3u);
    return static_cast<char>('A' + clampedLevel - 1u);
}

std::optional<std::string> formatSummonMonstersComment(
    const std::vector<uint32_t> &arguments,
    const LegacyLuaExportLookups &lookups)
{
    if (arguments.size() < 8)
    {
        return std::nullopt;
    }

    const uint32_t typeIndex = arguments[0];
    const uint32_t level = arguments[1];
    const uint32_t count = arguments[2];
    const int32_t x = static_cast<int32_t>(arguments[3]);
    const int32_t y = static_cast<int32_t>(arguments[4]);
    const int32_t z = static_cast<int32_t>(arguments[5]);
    const uint32_t groupId = arguments[6];
    const uint32_t uniqueNameId = arguments[7];
    std::ostringstream comment;
    comment << "encounter slot " << typeIndex;

    if (const std::optional<std::string> encounterName = lookupText(lookups.mapEncounterNames, typeIndex))
    {
        comment << " \"" << *encounterName << "\"";
    }

    comment << " tier " << summonMonsterTierLetter(level)
            << ", count " << count
            << ", pos=(" << x << ", " << y << ", " << z << ")"
            << ", actor group " << groupId;

    if (const std::optional<std::string> groupName = lookupText(lookups.actorGroupNames, groupId))
    {
        comment << ": " << *groupName;
    }

    if (uniqueNameId != 0)
    {
        comment << ", unique actor " << uniqueNameId;

        if (const std::optional<std::string> uniqueName = lookupText(lookups.placedMonsterNames, uniqueNameId))
        {
            comment << " \"" << *uniqueName << "\"";
        }
    }
    else
    {
        comment << ", no unique actor name";
    }

    return comment.str();
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

            condition = "evt.CheckMonstersKilled(" + formatActorKillCheck(instruction.arguments[0]) + ", "
                + std::to_string(instruction.arguments[1]) + ", "
                + std::to_string(instruction.arguments[2]) + ", "
                + (instruction.arguments[3] != 0 ? std::string("true") : std::string("false")) + ")";
            comment = formatActorKilledComment(
                instruction.arguments[0],
                instruction.arguments[1],
                instruction.arguments[2],
                lookups);
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
                    formatMoveNpcComment(lookups, instruction.arguments[0], instruction.arguments[1]),
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
        case LegacyLuaOperation::SummonObject:
            if (instruction.arguments.size() >= 7)
            {
                const std::string functionName = instruction.operation == LegacyLuaOperation::SummonItem
                    ? "evt.SummonItem("
                    : "evt.SummonObject(";
                emitIndentedLineWithComment(
                    stream,
                    functionName + std::to_string(instruction.arguments[0]) + ", "
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
                    formatSummonMonstersComment(instruction.arguments, lookups),
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
                line << "evt.SetSprite(" << formatLegacyReferenceId(instruction.arguments[0]);

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
                    + formatDoorAction(instruction.arguments[1]) + ")",
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
                line << "evt.SetTexture(" << formatLegacyReferenceId(instruction.arguments[0]);

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
                    "evt.SetLight(" + formatLegacyReferenceId(instruction.arguments[0]) + ", "
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
                    "evt.SetFacetBit(" + formatLegacyReferenceId(instruction.arguments[0]) + ", "
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
                    formatActorGroupComment(instruction.arguments[0], lookups),
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
                    formatSetNpcTopicComment(
                        lookups,
                        instruction.arguments[0],
                        instruction.arguments[1],
                        instruction.arguments[2]),
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::SetNpcGroupNews:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetNPCGroupNews(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    formatNpcGroupNewsComment(instruction.arguments[0], instruction.arguments[1], lookups),
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
                    formatSetNpcGreetingComment(lookups, instruction.arguments[0], instruction.arguments[1]),
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

        case LegacyLuaOperation::ShowFace:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.FaceExpression(" + std::to_string(instruction.arguments[1]) + ")",
                    std::nullopt,
                    indentLevel);
                return true;
            }

            return false;

        case LegacyLuaOperation::ReceiveDamage:
            if (instruction.arguments.size() >= 3)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.DamagePlayer(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ")",
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
        case LegacyLuaOperation::AcknowledgeMessage:
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

std::string_view trimLuaLine(std::string_view line)
{
    while (!line.empty() && std::isspace(static_cast<unsigned char>(line.front())))
    {
        line.remove_prefix(1);
    }

    while (!line.empty() && std::isspace(static_cast<unsigned char>(line.back())))
    {
        line.remove_suffix(1);
    }

    return line;
}

int readableLuaBlockDelta(std::string_view line)
{
    const std::string_view trimmed = trimLuaLine(line);

    if (trimmed.empty() || trimmed.starts_with("--"))
    {
        return 0;
    }

    if (trimmed == "else" || trimmed.starts_with("elseif "))
    {
        return 0;
    }

    if (trimmed == "end")
    {
        return -1;
    }

    if (trimmed.starts_with("if ")
        || trimmed.starts_with("for ")
        || trimmed.starts_with("while ")
        || trimmed.starts_with("function ")
        || trimmed.starts_with("local function ")
        || trimmed == "repeat")
    {
        return 1;
    }

    if (trimmed.starts_with("until "))
    {
        return -1;
    }

    return 0;
}

bool isBalancedReadableLuaBlock(std::string_view luaText)
{
    int blockDepth = 0;

    for (const std::string &line : splitPreservingLines(std::string(luaText)))
    {
        blockDepth += readableLuaBlockDelta(line);

        if (blockDepth < 0)
        {
            return false;
        }
    }

    return blockDepth == 0;
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
    return !truePrefix.empty()
        && !falsePrefix.empty()
        && !commonSuffix.empty()
        && isBalancedReadableLuaBlock(truePrefix)
        && isBalancedReadableLuaBlock(falsePrefix);
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

bool tryEmitReadableOptionalPrelude(
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

    const bool includePrimaryMemberInRepeatedPromotion =
        event.eventId >= 733 && event.eventId <= 740 && *firstMember == 1;

    auto formatPlayerList = [&]() -> std::string
    {
        std::ostringstream listStream;
        listStream << "{";
        bool wroteMember = false;

        if (includePrimaryMemberInRepeatedPromotion)
        {
            listStream << "Players.Member0";
            wroteMember = true;
        }

        for (size_t memberIndex = 0; memberIndex < memberSteps.size(); ++memberIndex)
        {
            const std::optional<uint32_t> member = getLeadingPartyMember(event, memberSteps[memberIndex]);

            if (!member)
            {
                return "";
            }

            if (wroteMember)
            {
                listStream << ", ";
            }

            listStream << "Players.Member" << *member;
            wroteMember = true;
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

void addPromptContinuation(
    std::vector<PromptContinuation> &continuations,
    const LegacyLuaInstruction &instruction,
    uint8_t continueStep)
{
    const auto duplicate = std::find_if(
        continuations.begin(),
        continuations.end(),
        [&](const PromptContinuation &existing)
        {
            return existing.promptStep == instruction.step
                && existing.continueStep == continueStep
                && existing.operation == instruction.operation;
        });

    if (duplicate != continuations.end())
    {
        return;
    }

    PromptContinuation continuation = {};
    continuation.promptStep = instruction.step;
    continuation.continueStep = continueStep;
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

        addPromptContinuation(continuations, instruction, static_cast<uint8_t>(instruction.step + 1));

        if (instruction.operation == LegacyLuaOperation::InputString && instruction.jumpTargetStep)
        {
            addPromptContinuation(continuations, instruction, *instruction.jumpTargetStep);
        }
    }

    return continuations;
}

std::string formatInputStringCall(const LegacyLuaEvent &event, const LegacyLuaInstruction &instruction)
{
    std::ostringstream line;
    line << "evt.AskQuestion(" << event.eventId << ", " << static_cast<unsigned>(instruction.step + 1);

    if (!instruction.arguments.empty())
    {
        line << ", " << instruction.arguments[0];
    }
    else
    {
        line << ", 0";
    }

    if (instruction.jumpTargetStep)
    {
        line << ", " << static_cast<unsigned>(*instruction.jumpTargetStep);

        if (instruction.arguments.size() >= 2)
        {
            line << ", " << instruction.arguments[1];
        }

        if (instruction.arguments.size() >= 3)
        {
            line << ", " << instruction.arguments[2];
        }
    }

    if (instruction.text && !instruction.text->empty())
    {
        line << ", " << luaQuoted(*instruction.text);
    }

    if (!instruction.inputAnswers.empty())
    {
        line << ", {";

        for (size_t answerIndex = 0; answerIndex < instruction.inputAnswers.size(); ++answerIndex)
        {
            if (answerIndex > 0)
            {
                line << ", ";
            }

            line << luaQuoted(instruction.inputAnswers[answerIndex]);
        }

        line << "}";
    }

    line << ")";
    return line.str();
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
            emitIndentedLineWithComment(stream, formatInputStringCall(event, instruction), std::nullopt, indentLevel);
            emitIndentedLineWithComment(stream, "return nil", std::nullopt, indentLevel);
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
            if (tryEmitReadableOptionalPrelude(stream, event, steps, currentStep, lookups, indentLevel, visited))
            {
                continue;
            }

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

                emitIndentedLineWithComment(
                    branchCases,
                    std::string(emittedAnyBranch ? "elseif" : "if") + " randomStep == "
                        + std::to_string(branchStep) + " then",
                    std::nullopt,
                    indentLevel);
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

bool tryEmitReadableOptionalPrelude(
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
    std::optional<uint8_t> preludeStep;
    std::optional<uint8_t> defaultStep;
    std::optional<uint8_t> step = currentStep;

    while (step)
    {
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo)
            || !stepInfo.actions.empty()
            || !stepInfo.terminalInstruction)
        {
            return false;
        }

        const LegacyLuaInstruction *instruction = stepInfo.terminalInstruction;

        if (!isReadableCompareOperation(instruction->operation) || !instruction->jumpTargetStep)
        {
            return false;
        }

        std::string condition;
        std::optional<std::string> conditionComment;

        if (!formatReadableConditionInstruction(*instruction, lookups, condition, conditionComment))
        {
            return false;
        }

        const std::optional<uint8_t> falseRawStep = nextStepAfter(steps, *step);
        std::optional<uint8_t> trueStep;
        std::optional<uint8_t> falseStep;

        if (!resolveSignificantStep(event, steps, instruction->jumpTargetStep, trueStep)
            || !resolveSignificantStep(event, steps, falseRawStep, falseStep)
            || !trueStep)
        {
            return false;
        }

        if (!preludeStep)
        {
            preludeStep = trueStep;
        }
        else if (*preludeStep != *trueStep)
        {
            return false;
        }

        conditions.push_back(condition);
        comments.push_back(conditionComment);
        chainSteps.push_back(*step);

        NormalStepInfo falseStepInfo;

        if (falseStep
            && falseRawStep
            && *falseStep == *falseRawStep
            && decomposeNormalStep(event, *falseStep, falseStepInfo)
            && falseStepInfo.actions.empty()
            && falseStepInfo.terminalInstruction
            && isReadableCompareOperation(falseStepInfo.terminalInstruction->operation))
        {
            step = falseStep;
            continue;
        }

        defaultStep = falseStep;
        break;
    }

    if (!preludeStep || !defaultStep || *preludeStep == *defaultStep)
    {
        return false;
    }

    SimpleBranchArm preludeArm;
    SimpleBranchArm defaultArm;

    if (!summarizeSimpleBranchArm(event, steps, preludeStep, lookups, preludeArm)
        || !summarizeSimpleBranchArm(event, steps, defaultStep, lookups, defaultArm)
        || !defaultArm.actions.empty())
    {
        return false;
    }

    const bool bothContinue = preludeArm.continuation
        && defaultArm.continuation
        && *preludeArm.continuation == *defaultArm.continuation;
    const bool bothReturn = preludeArm.returns && defaultArm.returns;

    if (!bothContinue && !bothReturn)
    {
        return false;
    }

    std::string combinedCondition;

    for (size_t conditionIndex = 0; conditionIndex < conditions.size(); ++conditionIndex)
    {
        if (conditionIndex > 0)
        {
            combinedCondition += " or ";
        }

        combinedCondition += conditions[conditionIndex];
    }

    emitIndentedLineWithComment(stream, "if " + combinedCondition + " then", comments.front(), indentLevel);

    for (const LegacyLuaInstruction *action : preludeArm.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, indentLevel + 1))
        {
            return false;
        }
    }

    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

    for (uint8_t chainStep : chainSteps)
    {
        if (std::find(visited.begin(), visited.end(), chainStep) == visited.end())
        {
            visited.push_back(chainStep);
        }
    }

    std::optional<uint8_t> visitedPreludeStep = preludeStep;

    while (visitedPreludeStep)
    {
        if (std::find(visited.begin(), visited.end(), *visitedPreludeStep) == visited.end())
        {
            visited.push_back(*visitedPreludeStep);
        }

        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *visitedPreludeStep, stepInfo))
        {
            return false;
        }

        if (stepInfo.terminalInstruction && stepInfo.terminalInstruction->operation == LegacyLuaOperation::Jump)
        {
            visitedPreludeStep = stepInfo.terminalInstruction->jumpTargetStep;
        }
        else
        {
            visitedPreludeStep = nextStepAfter(steps, *visitedPreludeStep);
        }

        std::optional<uint8_t> significantStep;

        if (!resolveSignificantStep(event, steps, visitedPreludeStep, significantStep))
        {
            return false;
        }

        if (!significantStep
            || (bothContinue && preludeArm.continuation && *significantStep == *preludeArm.continuation)
            || (bothReturn && defaultStep && *significantStep == *defaultStep))
        {
            break;
        }

        visitedPreludeStep = significantStep;
    }

    currentStep = bothContinue ? preludeArm.continuation : defaultStep;
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

    trimTrailingTopLevelReturn(stream);

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
                    formatMoveNpcComment(lookups, instruction.arguments[0], instruction.arguments[1]),
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
                    formatSummonMonstersComment(instruction.arguments, lookups),
                    2);
            }
            break;

        case LegacyLuaOperation::SummonItem:
        case LegacyLuaOperation::SummonObject:
            if (instruction.arguments.size() >= 7)
            {
                const std::string functionName = instruction.operation == LegacyLuaOperation::SummonItem
                    ? "evt.SummonItem("
                    : "evt.SummonObject(";
                emitIndentedLineWithComment(
                    stream,
                    functionName + std::to_string(instruction.arguments[0]) + ", "
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
                line << "evt.SetSprite(" << formatLegacyReferenceId(instruction.arguments[0]);

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
                    + formatDoorAction(instruction.arguments[1]) + ")",
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
                line << "evt.SetTexture(" << formatLegacyReferenceId(instruction.arguments[0]);

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
                    "evt.SetLight(" + formatLegacyReferenceId(instruction.arguments[0]) + ", "
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
                    "evt.SetFacetBit(" + formatLegacyReferenceId(instruction.arguments[0]) + ", "
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
                    formatActorGroupComment(instruction.arguments[0], lookups),
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
                    formatSetNpcTopicComment(
                        lookups,
                        instruction.arguments[0],
                        instruction.arguments[1],
                        instruction.arguments[2]),
                    2);
            }
            break;

        case LegacyLuaOperation::SetNpcGroupNews:
            if (instruction.arguments.size() >= 2)
            {
                emitIndentedLineWithComment(
                    stream,
                    "evt.SetNPCGroupNews(" + std::to_string(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ")",
                    formatNpcGroupNewsComment(instruction.arguments[0], instruction.arguments[1], lookups),
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
                    formatSetNpcGreetingComment(lookups, instruction.arguments[0], instruction.arguments[1]),
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
                    "if evt.CheckMonstersKilled(" + formatActorKillCheck(instruction.arguments[0]) + ", "
                    + std::to_string(instruction.arguments[1]) + ", "
                    + std::to_string(instruction.arguments[2]) + ", "
                    + (instruction.arguments[3] != 0 ? "true" : "false") + ") then return "
                    + std::to_string(*instruction.jumpTargetStep) + " end",
                    formatActorKilledComment(
                        instruction.arguments[0],
                        instruction.arguments[1],
                        instruction.arguments[2],
                        lookups),
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
            emitIndentedLineWithComment(stream, formatInputStringCall(event, instruction), std::nullopt, 2);
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
        case LegacyLuaOperation::AcknowledgeMessage:
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

bool isHintOnlyLegacyEvent(const EvtEvent &event)
{
    return event.instructions.size() >= 2
        && event.instructions[0].opcode == EvtOpcode::MouseOver
        && event.instructions[1].opcode == EvtOpcode::Exit;
}

void emitHintOnlyEventRegistration(
    std::ostringstream &stream,
    std::string_view registerFunction,
    uint16_t eventId,
    const std::string &title,
    const std::optional<std::string> &hint)
{
    stream << registerFunction << "(" << eventId << ", " << luaQuoted(title) << ", nil";

    if (hint && !hint->empty())
    {
        stream << ", " << luaQuoted(*hint);
    }

    stream << ")\n";
}

struct NormalEventCfgMetrics
{
    size_t stepCount = 0;
    size_t branchCount = 0;
    size_t joinCount = 0;
    size_t maxPredecessorCount = 0;
    size_t meaningfulInstructionCount = 0;
    bool decomposes = true;
    bool hasBackwardEdge = false;
    bool usesPromptContinuation = false;
};

NormalEventCfgMetrics collectNormalEventCfgMetrics(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps)
{
    NormalEventCfgMetrics metrics;
    metrics.stepCount = steps.size();
    metrics.usesPromptContinuation = !collectPromptContinuations(event).empty();
    std::map<uint8_t, size_t> predecessorCounts;

    for (uint8_t step : steps)
    {
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, step, stepInfo))
        {
            metrics.decomposes = false;
            return metrics;
        }

        metrics.meaningfulInstructionCount += stepInfo.actions.size();

        if (stepInfo.terminalInstruction)
        {
            ++metrics.meaningfulInstructionCount;
        }

        const std::optional<size_t> stepIndex = findStepIndex(steps, step);
        const std::vector<uint8_t> successors = collectSuccessorSteps(event, steps, step);

        if (successors.size() > 1)
        {
            ++metrics.branchCount;
        }

        for (uint8_t successor : successors)
        {
            ++predecessorCounts[successor];

            const std::optional<size_t> successorIndex = findStepIndex(steps, successor);

            if (stepIndex && successorIndex && *successorIndex <= *stepIndex)
            {
                metrics.hasBackwardEdge = true;
            }
        }
    }

    for (const std::pair<const uint8_t, size_t> &entry : predecessorCounts)
    {
        metrics.maxPredecessorCount = std::max(metrics.maxPredecessorCount, entry.second);

        if (entry.second > 1)
        {
            ++metrics.joinCount;
        }
    }

    return metrics;
}

bool shouldPreferCompactNormalEvent(
    std::string_view readableLua,
    const NormalEventCfgMetrics &metrics)
{
    if (!metrics.decomposes || metrics.usesPromptContinuation)
    {
        return false;
    }

    const size_t lineCount = countLuaLines(readableLua);

    if (lineCount > MaxReadableNormalEventLines)
    {
        return true;
    }

    if (metrics.joinCount == 0 && !metrics.hasBackwardEdge)
    {
        return false;
    }

    const size_t expectedLinearLines = metrics.meaningfulInstructionCount + metrics.stepCount + 20;

    return lineCount > PreferCompactNormalEventLines
        && lineCount > expectedLinearLines * 2;
}

std::string compactStepLabel(uint8_t step)
{
    return "step_" + std::to_string(static_cast<unsigned>(step));
}

bool normalStepExists(const std::vector<uint8_t> &steps, uint8_t step)
{
    return findStepIndex(steps, step).has_value();
}

void addCompactLabelTarget(std::vector<uint8_t> &labelTargets, const std::vector<uint8_t> &steps, uint8_t targetStep)
{
    if (!normalStepExists(steps, targetStep))
    {
        return;
    }

    if (std::find(labelTargets.begin(), labelTargets.end(), targetStep) == labelTargets.end())
    {
        labelTargets.push_back(targetStep);
    }
}

std::vector<uint8_t> collectCompactLabelTargets(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps)
{
    std::vector<uint8_t> labelTargets;

    for (uint8_t step : steps)
    {
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, step, stepInfo) || !stepInfo.terminalInstruction)
        {
            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;
        const std::optional<uint8_t> nextStep = nextStepAfter(steps, step);

        switch (instruction.operation)
        {
            case LegacyLuaOperation::Jump:
                if (instruction.jumpTargetStep && instruction.jumpTargetStep != nextStep)
                {
                    addCompactLabelTarget(labelTargets, steps, *instruction.jumpTargetStep);
                }
                break;

            case LegacyLuaOperation::Compare:
            case LegacyLuaOperation::CheckItemsCount:
            case LegacyLuaOperation::CheckSkill:
            case LegacyLuaOperation::IsActorKilled:
            case LegacyLuaOperation::CheckSeason:
            case LegacyLuaOperation::IsTotalBountyHuntingAwardInRange:
            case LegacyLuaOperation::IsNpcInParty:
                if (instruction.jumpTargetStep && instruction.jumpTargetStep != nextStep)
                {
                    addCompactLabelTarget(labelTargets, steps, *instruction.jumpTargetStep);
                }
                break;

            case LegacyLuaOperation::RandomJump:
                for (uint32_t argument : instruction.arguments)
                {
                    addCompactLabelTarget(labelTargets, steps, static_cast<uint8_t>(argument));
                }
                break;

            default:
                break;
        }
    }

    return labelTargets;
}

std::map<uint8_t, size_t> collectNormalPredecessorCounts(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps)
{
    std::map<uint8_t, size_t> predecessorCounts;

    for (uint8_t step : steps)
    {
        for (uint8_t successor : collectSuccessorSteps(event, steps, step))
        {
            ++predecessorCounts[successor];
        }
    }

    return predecessorCounts;
}

std::map<uint8_t, std::vector<uint8_t>> collectNormalPredecessorSteps(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps)
{
    std::map<uint8_t, std::vector<uint8_t>> predecessors;

    for (uint8_t step : steps)
    {
        for (uint8_t successor : collectSuccessorSteps(event, steps, step))
        {
            std::vector<uint8_t> &successorPredecessors = predecessors[successor];

            if (std::find(successorPredecessors.begin(), successorPredecessors.end(), step) == successorPredecessors.end())
            {
                successorPredecessors.push_back(step);
            }
        }
    }

    return predecessors;
}

size_t lookupPredecessorCount(const std::map<uint8_t, size_t> &predecessorCounts, uint8_t step)
{
    const auto iterator = predecessorCounts.find(step);
    return iterator != predecessorCounts.end() ? iterator->second : 0;
}

bool compactLabelHasUnskippedPredecessor(
    const std::map<uint8_t, std::vector<uint8_t>> &predecessors,
    const std::vector<uint8_t> &skippedSteps,
    uint8_t step)
{
    const auto iterator = predecessors.find(step);

    if (iterator == predecessors.end())
    {
        return false;
    }

    for (uint8_t predecessor : iterator->second)
    {
        if (std::find(skippedSteps.begin(), skippedSteps.end(), predecessor) == skippedSteps.end())
        {
            return true;
        }
    }

    return false;
}

bool collectCompactSimpleArmPath(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep,
    std::optional<uint8_t> stopStep,
    std::vector<uint8_t> &path)
{
    std::optional<uint8_t> step = startStep;

    while (step)
    {
        if (stopStep && *step == *stopStep)
        {
            return true;
        }

        if (std::find(path.begin(), path.end(), *step) != path.end())
        {
            return false;
        }

        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo))
        {
            return false;
        }

        path.push_back(*step);

        if (stepInfo.terminalInstruction)
        {
            const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

            if (instruction.operation == LegacyLuaOperation::Exit)
            {
                return true;
            }

            if (instruction.operation == LegacyLuaOperation::Jump)
            {
                step = instruction.jumpTargetStep;
                continue;
            }

            return false;
        }

        step = nextStepAfter(steps, *step);
    }

    return true;
}

bool compactPathHasExternalPredecessor(
    const std::vector<uint8_t> &path,
    const std::map<uint8_t, size_t> &predecessorCounts,
    size_t allowedStartPredecessors)
{
    for (size_t pathIndex = 0; pathIndex < path.size(); ++pathIndex)
    {
        const size_t allowedPredecessors = pathIndex == 0 ? allowedStartPredecessors : 1;

        if (lookupPredecessorCount(predecessorCounts, path[pathIndex]) > allowedPredecessors)
        {
            return true;
        }
    }

    return false;
}

struct CompactActionIsland
{
    std::vector<const LegacyLuaInstruction *> actions;
    std::vector<uint8_t> consumedSteps;
    std::optional<uint8_t> continuation;
    bool returns = false;
};

bool collectCompactActionIsland(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep,
    CompactActionIsland &island)
{
    std::optional<uint8_t> step = startStep;

    while (step)
    {
        if (std::find(island.consumedSteps.begin(), island.consumedSteps.end(), *step) != island.consumedSteps.end())
        {
            return false;
        }

        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo))
        {
            return false;
        }

        if (stepInfo.actions.empty() && stepInfo.terminalInstruction && isReadableCompareOperation(stepInfo.terminalInstruction->operation))
        {
            island.continuation = *step;
            return true;
        }

        island.consumedSteps.push_back(*step);

        for (const LegacyLuaInstruction *action : stepInfo.actions)
        {
            island.actions.push_back(action);
        }

        if (!stepInfo.terminalInstruction)
        {
            step = nextStepAfter(steps, *step);
            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::Exit)
        {
            island.returns = true;
            return true;
        }

        if (instruction.operation == LegacyLuaOperation::Jump)
        {
            step = instruction.jumpTargetStep;
            continue;
        }

        if (isReadableCompareOperation(instruction.operation))
        {
            island.continuation = *step;
            return island.actions.empty();
        }

        return false;
    }

    island.returns = true;
    return true;
}

bool compactPathWithoutActionsReaches(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep,
    std::optional<uint8_t> targetStep,
    bool targetReturns,
    std::vector<uint8_t> &consumedSteps)
{
    std::optional<uint8_t> step = startStep;

    while (step)
    {
        if (!targetReturns && targetStep && *step == *targetStep)
        {
            return true;
        }

        if (std::find(consumedSteps.begin(), consumedSteps.end(), *step) != consumedSteps.end())
        {
            return false;
        }

        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo) || !stepInfo.actions.empty())
        {
            return false;
        }

        consumedSteps.push_back(*step);

        if (!stepInfo.terminalInstruction)
        {
            step = nextStepAfter(steps, *step);
            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::Exit)
        {
            return targetReturns;
        }

        if (instruction.operation == LegacyLuaOperation::Jump)
        {
            step = instruction.jumpTargetStep;
            continue;
        }

        if (isReadableCompareOperation(instruction.operation))
        {
            return !targetReturns && targetStep && *step == *targetStep;
        }

        return false;
    }

    return targetReturns;
}

bool isAlwaysTrueCompactCondition(const LegacyLuaInstruction &instruction)
{
    if (instruction.operation != LegacyLuaOperation::Compare || instruction.arguments.size() < 2)
    {
        return false;
    }

    const FormattedSelector selector = formatSelector(instruction.arguments[0]);
    return selector.semantic == SelectorSemantic::MapVar && instruction.arguments[1] == 0;
}

bool collectCompactLinearActionsUntil(
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> startStep,
    uint8_t stopStep,
    std::vector<const LegacyLuaInstruction *> &actions,
    std::vector<uint8_t> &consumedSteps)
{
    std::optional<uint8_t> step = startStep;

    while (step)
    {
        if (*step == stopStep)
        {
            return true;
        }

        if (std::find(consumedSteps.begin(), consumedSteps.end(), *step) != consumedSteps.end())
        {
            return false;
        }

        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo))
        {
            return false;
        }

        consumedSteps.push_back(*step);

        for (const LegacyLuaInstruction *action : stepInfo.actions)
        {
            actions.push_back(action);
        }

        if (!stepInfo.terminalInstruction)
        {
            step = nextStepAfter(steps, *step);
            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (instruction.operation == LegacyLuaOperation::Jump)
        {
            step = instruction.jumpTargetStep;
            continue;
        }

        return false;
    }

    return false;
}

bool tryEmitCompactConditionReturnBlock(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t startStep,
    const LegacyLuaExportLookups &lookups,
    const std::map<uint8_t, size_t> &predecessorCounts,
    std::vector<uint8_t> &skippedSteps)
{
    NormalStepInfo stepInfo;

    if (!decomposeNormalStep(event, startStep, stepInfo)
        || !stepInfo.terminalInstruction
        || !isReadableCompareOperation(stepInfo.terminalInstruction->operation)
        || !stepInfo.terminalInstruction->jumpTargetStep)
    {
        return false;
    }

    const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;
    const std::optional<uint8_t> falseRawStep = nextStepAfter(steps, startStep);
    CompactActionIsland trueIsland;

    if (collectCompactActionIsland(event, steps, instruction.jumpTargetStep, trueIsland)
        && trueIsland.returns
        && compactPathHasExternalPredecessor(
            trueIsland.consumedSteps,
            predecessorCounts,
            trueIsland.actions.empty() ? 2 : 1))
    {
        return false;
    }

    std::string condition;
    std::optional<std::string> conditionComment;

    if (!formatReadableConditionInstruction(instruction, lookups, condition, conditionComment))
    {
        return false;
    }

    for (const LegacyLuaInstruction *action : stepInfo.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, 1))
        {
            return false;
        }
    }

    const auto markSkipped = [&skippedSteps](uint8_t step)
    {
        if (std::find(skippedSteps.begin(), skippedSteps.end(), step) == skippedSteps.end())
        {
            skippedSteps.push_back(step);
        }
    };

    if (trueIsland.returns)
    {
        emitIndentedLineWithComment(stream, "if " + condition + " then", conditionComment, 1);

        for (const LegacyLuaInstruction *action : trueIsland.actions)
        {
            if (!emitReadableActionInstruction(stream, *action, lookups, 2))
            {
                return false;
            }
        }

        emitIndentedLineWithComment(stream, "return", std::nullopt, 2);
        emitIndentedLineWithComment(stream, "end", std::nullopt, 1);
        markSkipped(startStep);

        for (uint8_t step : trueIsland.consumedSteps)
        {
            markSkipped(step);
        }

        return true;
    }

    CompactActionIsland falseIsland;

    if (!collectCompactActionIsland(event, steps, falseRawStep, falseIsland)
        || !falseIsland.returns
        || compactPathHasExternalPredecessor(falseIsland.consumedSteps, predecessorCounts, 1))
    {
        return false;
    }

    emitIndentedLineWithComment(stream, "if not " + condition + " then", conditionComment, 1);

    for (const LegacyLuaInstruction *action : falseIsland.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, 2))
        {
            return false;
        }
    }

    emitIndentedLineWithComment(stream, "return", std::nullopt, 2);
    emitIndentedLineWithComment(stream, "end", std::nullopt, 1);
    markSkipped(startStep);

    for (uint8_t step : falseIsland.consumedSteps)
    {
        markSkipped(step);
    }

    return true;
}

bool tryEmitCompactPositiveOptionalSkipBlock(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t startStep,
    const LegacyLuaExportLookups &lookups,
    const std::map<uint8_t, size_t> &predecessorCounts,
    std::vector<uint8_t> &skippedSteps)
{
    NormalStepInfo stepInfo;

    if (!decomposeNormalStep(event, startStep, stepInfo)
        || !stepInfo.terminalInstruction
        || !isReadableCompareOperation(stepInfo.terminalInstruction->operation)
        || !stepInfo.terminalInstruction->jumpTargetStep)
    {
        return false;
    }

    const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;
    const std::optional<uint8_t> skipStep = nextStepAfter(steps, startStep);
    NormalStepInfo skipStepInfo;

    if (!skipStep
        || !decomposeNormalStep(event, *skipStep, skipStepInfo)
        || !skipStepInfo.actions.empty()
        || !skipStepInfo.terminalInstruction
        || !skipStepInfo.terminalInstruction->jumpTargetStep
        || !isAlwaysTrueCompactCondition(*skipStepInfo.terminalInstruction))
    {
        return false;
    }

    const uint8_t continuationStep = *skipStepInfo.terminalInstruction->jumpTargetStep;
    std::vector<const LegacyLuaInstruction *> actions;
    std::vector<uint8_t> actionSteps;

    if (instruction.jumpTargetStep == skipStep
        || instruction.jumpTargetStep == continuationStep
        || !collectCompactLinearActionsUntil(event, steps, instruction.jumpTargetStep, continuationStep, actions, actionSteps)
        || actions.empty()
        || lookupPredecessorCount(predecessorCounts, *skipStep) > 1
        || compactPathHasExternalPredecessor(actionSteps, predecessorCounts, 2))
    {
        return false;
    }

    std::string condition;
    std::optional<std::string> conditionComment;

    if (!formatReadableConditionInstruction(instruction, lookups, condition, conditionComment))
    {
        return false;
    }

    for (const LegacyLuaInstruction *action : stepInfo.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, 1))
        {
            return false;
        }
    }

    emitIndentedLineWithComment(stream, "if " + condition + " then", conditionComment, 1);

    for (const LegacyLuaInstruction *action : actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, 2))
        {
            return false;
        }
    }

    emitIndentedLineWithComment(stream, "end", std::nullopt, 1);

    const auto markSkipped = [&skippedSteps](uint8_t step)
    {
        if (std::find(skippedSteps.begin(), skippedSteps.end(), step) == skippedSteps.end())
        {
            skippedSteps.push_back(step);
        }
    };

    markSkipped(startStep);
    markSkipped(*skipStep);

    for (uint8_t step : actionSteps)
    {
        markSkipped(step);
    }

    return true;
}

bool isExitOnlyCompactStep(const LegacyLuaEvent &event, uint8_t step)
{
    NormalStepInfo stepInfo;
    return decomposeNormalStep(event, step, stepInfo)
        && stepInfo.actions.empty()
        && stepInfo.terminalInstruction
        && stepInfo.terminalInstruction->operation == LegacyLuaOperation::Exit;
}

bool formatCompactStepCondition(
    const LegacyLuaEvent &event,
    uint8_t step,
    const LegacyLuaExportLookups &lookups,
    std::string &condition,
    std::optional<std::string> &comment,
    const LegacyLuaInstruction **instruction)
{
    NormalStepInfo stepInfo;

    if (!decomposeNormalStep(event, step, stepInfo)
        || !stepInfo.actions.empty()
        || !stepInfo.terminalInstruction
        || !isReadableCompareOperation(stepInfo.terminalInstruction->operation)
        || !formatReadableConditionInstruction(*stepInfo.terminalInstruction, lookups, condition, comment))
    {
        return false;
    }

    if (instruction)
    {
        *instruction = stepInfo.terminalInstruction;
    }

    return true;
}

bool emitCompactActionRange(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t startStep,
    uint8_t stopStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel)
{
    std::vector<const LegacyLuaInstruction *> actions;
    std::vector<uint8_t> consumedSteps;

    if (!collectCompactLinearActionsUntil(event, steps, startStep, stopStep, actions, consumedSteps) || actions.empty())
    {
        return false;
    }

    for (const LegacyLuaInstruction *action : actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, indentLevel))
        {
            return false;
        }
    }

    return true;
}

bool emitCompactActionOnlyStep(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    uint8_t step,
    const LegacyLuaExportLookups &lookups,
    int indentLevel)
{
    NormalStepInfo stepInfo;

    if (!decomposeNormalStep(event, step, stepInfo) || stepInfo.actions.empty() || stepInfo.terminalInstruction)
    {
        return false;
    }

    for (const LegacyLuaInstruction *action : stepInfo.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, indentLevel))
        {
            return false;
        }
    }

    return true;
}

bool tryEmitCompactMemoryCrystalRestoreBody(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    const LegacyLuaExportLookups &lookups)
{
    constexpr std::array<uint8_t, 4> itemCheckSteps = {4, 5, 6, 7};
    constexpr std::array<uint8_t, 4> restoredCheckSteps = {12, 18, 24, 30};
    constexpr std::array<uint8_t, 4> restoreActionStarts = {13, 19, 25, 31};
    constexpr std::array<uint8_t, 4> restoreActionStops = {17, 23, 29, 36};
    constexpr std::array<uint8_t, 4> restoredSkipTargets = {5, 6, 7, 10};
    constexpr std::array<uint8_t, 4> topicCheckSteps = {40, 42, 44, 46};

    if (!isExitOnlyCompactStep(event, 1)
        || !isExitOnlyCompactStep(event, 9)
        || !isExitOnlyCompactStep(event, 11)
        || !isExitOnlyCompactStep(event, 41)
        || !isExitOnlyCompactStep(event, 43)
        || !isExitOnlyCompactStep(event, 45)
        || !isExitOnlyCompactStep(event, 47))
    {
        return false;
    }

    std::string powerCondition;
    std::optional<std::string> powerComment;
    const LegacyLuaInstruction *powerInstruction = nullptr;

    if (!formatCompactStepCondition(event, 0, lookups, powerCondition, powerComment, &powerInstruction)
        || !powerInstruction->jumpTargetStep
        || *powerInstruction->jumpTargetStep != 2)
    {
        return false;
    }

    std::string alreadyRestoredCondition;
    std::optional<std::string> alreadyRestoredComment;
    const LegacyLuaInstruction *alreadyRestoredInstruction = nullptr;

    if (!formatCompactStepCondition(event, 2, lookups, alreadyRestoredCondition, alreadyRestoredComment, &alreadyRestoredInstruction)
        || !alreadyRestoredInstruction->jumpTargetStep
        || *alreadyRestoredInstruction->jumpTargetStep != 10)
    {
        return false;
    }

    NormalStepInfo forPlayerStepInfo;

    if (!decomposeNormalStep(event, 3, forPlayerStepInfo)
        || forPlayerStepInfo.actions.empty()
        || forPlayerStepInfo.terminalInstruction)
    {
        return false;
    }

    std::array<std::string, 4> itemConditions;
    std::array<std::optional<std::string>, 4> itemComments;
    std::array<std::string, 4> restoredConditions;
    std::array<std::optional<std::string>, 4> restoredComments;

    for (size_t index = 0; index < itemCheckSteps.size(); ++index)
    {
        const LegacyLuaInstruction *itemInstruction = nullptr;
        const LegacyLuaInstruction *restoredInstruction = nullptr;

        if (!formatCompactStepCondition(event, itemCheckSteps[index], lookups, itemConditions[index], itemComments[index], &itemInstruction)
            || !itemInstruction->jumpTargetStep
            || *itemInstruction->jumpTargetStep != restoredCheckSteps[index]
            || !formatCompactStepCondition(
                event,
                restoredCheckSteps[index],
                lookups,
                restoredConditions[index],
                restoredComments[index],
                &restoredInstruction)
            || !restoredInstruction->jumpTargetStep
            || *restoredInstruction->jumpTargetStep != restoredSkipTargets[index])
        {
            return false;
        }
    }

    std::array<std::string, 4> topicConditions;

    for (size_t index = 0; index < topicCheckSteps.size(); ++index)
    {
        std::optional<std::string> ignoredComment;
        const LegacyLuaInstruction *topicInstruction = nullptr;

        if (!formatCompactStepCondition(event, topicCheckSteps[index], lookups, topicConditions[index], ignoredComment, &topicInstruction))
        {
            return false;
        }

        if (index < topicCheckSteps.size() - 1)
        {
            if (!topicInstruction->jumpTargetStep || *topicInstruction->jumpTargetStep != topicCheckSteps[index + 1])
            {
                return false;
            }
        }
        else if (!topicInstruction->jumpTargetStep || *topicInstruction->jumpTargetStep != 48)
        {
            return false;
        }
    }

    emitIndentedLineWithComment(stream, "local function RestoreMemoryModule()", std::nullopt, 1);

    if (!emitCompactActionRange(stream, event, steps, 36, 40, lookups, 2))
    {
        return false;
    }

    std::string topicCondition;

    for (size_t index = 0; index < topicConditions.size(); ++index)
    {
        if (index > 0)
        {
            topicCondition += " and ";
        }

        topicCondition += topicConditions[index];
    }

    emitIndentedLineWithComment(stream, "if " + topicCondition + " then", std::nullopt, 2);

    if (!emitCompactActionOnlyStep(stream, event, 48, lookups, 3)
        || !emitCompactActionOnlyStep(stream, event, 49, lookups, 3))
    {
        return false;
    }

    emitIndentedLineWithComment(stream, "end", std::nullopt, 2);
    emitIndentedLineWithComment(stream, "end", std::nullopt, 1);
    stream << "\n";
    emitIndentedLineWithComment(stream, "if not " + powerCondition + " then", powerComment, 1);
    emitIndentedLineWithComment(stream, "return", std::nullopt, 2);
    emitIndentedLineWithComment(stream, "end", std::nullopt, 1);
    emitIndentedLineWithComment(stream, "if " + alreadyRestoredCondition + " then", alreadyRestoredComment, 1);

    if (!emitCompactActionRange(stream, event, steps, 10, 11, lookups, 2))
    {
        return false;
    }

    emitIndentedLineWithComment(stream, "return", std::nullopt, 2);
    emitIndentedLineWithComment(stream, "end", std::nullopt, 1);

    for (const LegacyLuaInstruction *action : forPlayerStepInfo.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, 1))
        {
            return false;
        }
    }

    for (size_t index = 0; index < itemCheckSteps.size(); ++index)
    {
        emitIndentedLineWithComment(stream, "if " + itemConditions[index] + " then", itemComments[index], 1);

        if (index == itemCheckSteps.size() - 1)
        {
            emitIndentedLineWithComment(stream, "if " + restoredConditions[index] + " then", restoredComments[index], 2);

            if (!emitCompactActionRange(stream, event, steps, 10, 11, lookups, 3))
            {
                return false;
            }

            emitIndentedLineWithComment(stream, "return", std::nullopt, 3);
            emitIndentedLineWithComment(stream, "end", std::nullopt, 2);
        }
        else
        {
            emitIndentedLineWithComment(stream, "if not " + restoredConditions[index] + " then", restoredComments[index], 2);
        }

        if (!emitCompactActionRange(
                stream,
                event,
                steps,
                restoreActionStarts[index],
                restoreActionStops[index],
                lookups,
                index == itemCheckSteps.size() - 1 ? 2 : 3))
        {
            return false;
        }

        emitIndentedLineWithComment(
            stream,
            "RestoreMemoryModule()",
            std::nullopt,
            index == itemCheckSteps.size() - 1 ? 2 : 3);
        emitIndentedLineWithComment(stream, "return", std::nullopt, index == itemCheckSteps.size() - 1 ? 2 : 3);

        if (index != itemCheckSteps.size() - 1)
        {
            emitIndentedLineWithComment(stream, "end", std::nullopt, 2);
        }

        emitIndentedLineWithComment(stream, "end", std::nullopt, 1);
    }

    if (!emitCompactActionRange(stream, event, steps, 8, 9, lookups, 1))
    {
        return false;
    }

    return true;
}

bool tryEmitCompactOptionalPrelude(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t startStep,
    const LegacyLuaExportLookups &lookups,
    const std::map<uint8_t, size_t> &predecessorCounts,
    std::vector<uint8_t> &skippedSteps)
{
    std::vector<std::string> conditions;
    std::vector<std::optional<std::string>> comments;
    std::vector<uint8_t> chainSteps;
    std::vector<std::optional<uint8_t>> defaultRawSteps;
    std::optional<uint8_t> preludeStep;
    std::optional<uint8_t> step = startStep;

    while (step)
    {
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *step, stepInfo)
            || !stepInfo.actions.empty()
            || !stepInfo.terminalInstruction)
        {
            return false;
        }

        const LegacyLuaInstruction *instruction = stepInfo.terminalInstruction;

        if (!isReadableCompareOperation(instruction->operation) || !instruction->jumpTargetStep)
        {
            return false;
        }

        std::string condition;
        std::optional<std::string> conditionComment;

        if (!formatReadableConditionInstruction(*instruction, lookups, condition, conditionComment))
        {
            return false;
        }

        const std::optional<uint8_t> falseRawStep = nextStepAfter(steps, *step);
        CompactActionIsland trueIsland;

        if (!collectCompactActionIsland(event, steps, instruction->jumpTargetStep, trueIsland)
            || trueIsland.actions.empty())
        {
            return false;
        }

        if (!preludeStep)
        {
            preludeStep = trueIsland.consumedSteps.empty() ? instruction->jumpTargetStep : trueIsland.consumedSteps.front();
        }
        else if (!trueIsland.consumedSteps.empty() && *preludeStep != trueIsland.consumedSteps.front())
        {
            return false;
        }

        conditions.push_back(condition);
        comments.push_back(conditionComment);
        chainSteps.push_back(*step);
        defaultRawSteps.push_back(falseRawStep);

        NormalStepInfo falseStepInfo;
        std::optional<uint8_t> falseStep;

        if (!resolveSignificantStep(event, steps, falseRawStep, falseStep))
        {
            return false;
        }

        if (falseStep
            && falseRawStep
            && *falseStep == *falseRawStep
            && decomposeNormalStep(event, *falseStep, falseStepInfo)
            && falseStepInfo.actions.empty()
            && falseStepInfo.terminalInstruction
            && isReadableCompareOperation(falseStepInfo.terminalInstruction->operation))
        {
            step = falseStep;
            continue;
        }

        break;
    }

    if (!preludeStep || conditions.empty() || defaultRawSteps.empty())
    {
        return false;
    }

    CompactActionIsland preludeIsland;

    if (!collectCompactActionIsland(event, steps, preludeStep, preludeIsland)
        || preludeIsland.actions.empty())
    {
        return false;
    }

    std::vector<uint8_t> defaultPath;

    if (!compactPathWithoutActionsReaches(
            event,
            steps,
            defaultRawSteps.back(),
            preludeIsland.continuation,
            preludeIsland.returns,
            defaultPath))
    {
        return false;
    }

    if (compactPathHasExternalPredecessor(preludeIsland.consumedSteps, predecessorCounts, conditions.size())
        || compactPathHasExternalPredecessor(defaultPath, predecessorCounts, 1))
    {
        return false;
    }

    std::string combinedCondition;

    for (size_t conditionIndex = 0; conditionIndex < conditions.size(); ++conditionIndex)
    {
        if (conditionIndex > 0)
        {
            combinedCondition += " or ";
        }

        combinedCondition += conditions[conditionIndex];
    }

    emitIndentedLineWithComment(stream, "if " + combinedCondition + " then", comments.front(), 1);

    for (const LegacyLuaInstruction *action : preludeIsland.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, 2))
        {
            return false;
        }
    }

    emitIndentedLineWithComment(stream, "end", std::nullopt, 1);

    for (uint8_t chainStep : chainSteps)
    {
        if (std::find(skippedSteps.begin(), skippedSteps.end(), chainStep) == skippedSteps.end())
        {
            skippedSteps.push_back(chainStep);
        }
    }

    for (uint8_t pathStep : preludeIsland.consumedSteps)
    {
        if (std::find(skippedSteps.begin(), skippedSteps.end(), pathStep) == skippedSteps.end())
        {
            skippedSteps.push_back(pathStep);
        }
    }

    for (uint8_t pathStep : defaultPath)
    {
        if (std::find(skippedSteps.begin(), skippedSteps.end(), pathStep) == skippedSteps.end())
        {
            skippedSteps.push_back(pathStep);
        }
    }

    return true;
}

bool tryEmitCompactNestedOptionalBlock(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t startStep,
    const LegacyLuaExportLookups &lookups,
    const std::map<uint8_t, size_t> &predecessorCounts,
    std::vector<uint8_t> &skippedSteps)
{
    NormalStepInfo outerStepInfo;

    if (!decomposeNormalStep(event, startStep, outerStepInfo)
        || !outerStepInfo.actions.empty()
        || !outerStepInfo.terminalInstruction
        || !isReadableCompareOperation(outerStepInfo.terminalInstruction->operation)
        || !outerStepInfo.terminalInstruction->jumpTargetStep)
    {
        return false;
    }

    const LegacyLuaInstruction &outerInstruction = *outerStepInfo.terminalInstruction;
    std::optional<uint8_t> outerTrueStep;
    std::optional<uint8_t> outerFalseStep;
    const std::optional<uint8_t> outerFalseRawStep = nextStepAfter(steps, startStep);

    if (!resolveSignificantStep(event, steps, outerInstruction.jumpTargetStep, outerTrueStep)
        || !resolveSignificantStep(event, steps, outerFalseRawStep, outerFalseStep)
        || !outerTrueStep
        || !outerFalseStep
        || *outerTrueStep == *outerFalseStep)
    {
        return false;
    }

    NormalStepInfo innerStepInfo;

    if (!decomposeNormalStep(event, *outerTrueStep, innerStepInfo)
        || !innerStepInfo.actions.empty()
        || !innerStepInfo.terminalInstruction
        || !isReadableCompareOperation(innerStepInfo.terminalInstruction->operation)
        || !innerStepInfo.terminalInstruction->jumpTargetStep)
    {
        return false;
    }

    const LegacyLuaInstruction &innerInstruction = *innerStepInfo.terminalInstruction;
    CompactActionIsland actionIsland;

    if (!collectCompactActionIsland(event, steps, nextStepAfter(steps, *outerTrueStep), actionIsland)
        || actionIsland.actions.empty()
        || !actionIsland.continuation
        || actionIsland.returns)
    {
        return false;
    }

    std::vector<uint8_t> outerFalsePath;
    std::vector<uint8_t> innerTruePath;

    if (!compactPathWithoutActionsReaches(event, steps, outerFalseRawStep, actionIsland.continuation, false, outerFalsePath)
        || !compactPathWithoutActionsReaches(event, steps, innerInstruction.jumpTargetStep, actionIsland.continuation, false, innerTruePath)
        || compactPathHasExternalPredecessor(actionIsland.consumedSteps, predecessorCounts, 1)
        || compactPathHasExternalPredecessor(outerFalsePath, predecessorCounts, 1)
        || compactPathHasExternalPredecessor(innerTruePath, predecessorCounts, 1)
        || lookupPredecessorCount(predecessorCounts, *outerTrueStep) > 1)
    {
        return false;
    }

    std::string outerCondition;
    std::optional<std::string> outerComment;
    std::string innerCondition;
    std::optional<std::string> innerComment;

    if (!formatReadableConditionInstruction(outerInstruction, lookups, outerCondition, outerComment)
        || !formatReadableConditionInstruction(innerInstruction, lookups, innerCondition, innerComment))
    {
        return false;
    }

    emitIndentedLineWithComment(stream, "if " + outerCondition + " then", outerComment, 1);
    emitIndentedLineWithComment(stream, "if not " + innerCondition + " then", innerComment, 2);

    for (const LegacyLuaInstruction *action : actionIsland.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, 3))
        {
            return false;
        }
    }

    emitIndentedLineWithComment(stream, "end", std::nullopt, 2);
    emitIndentedLineWithComment(stream, "end", std::nullopt, 1);

    const auto markSkipped = [&skippedSteps](uint8_t step)
    {
        if (std::find(skippedSteps.begin(), skippedSteps.end(), step) == skippedSteps.end())
        {
            skippedSteps.push_back(step);
        }
    };

    markSkipped(startStep);
    markSkipped(*outerTrueStep);

    for (uint8_t step : outerFalsePath)
    {
        markSkipped(step);
    }

    for (uint8_t step : innerTruePath)
    {
        markSkipped(step);
    }

    for (uint8_t step : actionIsland.consumedSteps)
    {
        markSkipped(step);
    }

    return true;
}

bool tryEmitCompactFalseOptionalBlock(
    std::ostringstream &stream,
    const LegacyLuaEvent &event,
    const std::vector<uint8_t> &steps,
    uint8_t startStep,
    const LegacyLuaExportLookups &lookups,
    const std::map<uint8_t, size_t> &predecessorCounts,
    std::vector<uint8_t> &skippedSteps)
{
    NormalStepInfo stepInfo;

    if (!decomposeNormalStep(event, startStep, stepInfo)
        || !stepInfo.actions.empty()
        || !stepInfo.terminalInstruction
        || !isReadableCompareOperation(stepInfo.terminalInstruction->operation)
        || !stepInfo.terminalInstruction->jumpTargetStep)
    {
        return false;
    }

    const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;
    CompactActionIsland falseIsland;

    if (!collectCompactActionIsland(event, steps, nextStepAfter(steps, startStep), falseIsland)
        || falseIsland.actions.empty())
    {
        return false;
    }

    std::vector<uint8_t> truePath;
    std::vector<uint8_t> falseOnlySteps;

    if (!compactPathWithoutActionsReaches(
            event,
            steps,
            instruction.jumpTargetStep,
            falseIsland.continuation,
            falseIsland.returns,
            truePath)
        || compactPathHasExternalPredecessor(truePath, predecessorCounts, 2))
    {
        return false;
    }

    for (uint8_t step : falseIsland.consumedSteps)
    {
        if (std::find(truePath.begin(), truePath.end(), step) == truePath.end())
        {
            falseOnlySteps.push_back(step);
        }
    }

    if (compactPathHasExternalPredecessor(falseOnlySteps, predecessorCounts, 1))
    {
        return false;
    }

    std::string condition;
    std::optional<std::string> conditionComment;

    if (!formatReadableConditionInstruction(instruction, lookups, condition, conditionComment))
    {
        return false;
    }

    emitIndentedLineWithComment(stream, "if not " + condition + " then", conditionComment, 1);

    for (const LegacyLuaInstruction *action : falseIsland.actions)
    {
        if (!emitReadableActionInstruction(stream, *action, lookups, 2))
        {
            return false;
        }
    }

    emitIndentedLineWithComment(stream, "end", std::nullopt, 1);

    const auto markSkipped = [&skippedSteps](uint8_t step)
    {
        if (std::find(skippedSteps.begin(), skippedSteps.end(), step) == skippedSteps.end())
        {
            skippedSteps.push_back(step);
        }
    };

    markSkipped(startStep);

    for (uint8_t step : truePath)
    {
        markSkipped(step);
    }

    for (uint8_t step : falseIsland.consumedSteps)
    {
        markSkipped(step);
    }

    return true;
}

bool compactTargetNeedsTransfer(
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> targetStep,
    std::optional<uint8_t> nextStep)
{
    return !targetStep || targetStep != nextStep || !normalStepExists(steps, *targetStep);
}

bool emitCompactGotoOrReturn(
    std::ostringstream &stream,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> targetStep,
    std::optional<uint8_t> nextStep,
    int indentLevel)
{
    if (!compactTargetNeedsTransfer(steps, targetStep, nextStep))
    {
        return true;
    }

    if (!targetStep || !normalStepExists(steps, *targetStep))
    {
        emitIndentedLineWithComment(stream, "do return end", std::nullopt, indentLevel);
        return true;
    }

    emitIndentedLineWithComment(stream, "goto " + compactStepLabel(*targetStep), std::nullopt, indentLevel);
    return true;
}

bool emitCompactConditionalTransfer(
    std::ostringstream &stream,
    const LegacyLuaInstruction &instruction,
    const std::vector<uint8_t> &steps,
    std::optional<uint8_t> nextStep,
    const LegacyLuaExportLookups &lookups,
    int indentLevel)
{
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

    const bool trueFallsThrough = instruction.jumpTargetStep == nextStep
        && normalStepExists(steps, *instruction.jumpTargetStep);
    const bool falseFallsThrough = nextStep && normalStepExists(steps, *nextStep);

    if (trueFallsThrough && falseFallsThrough)
    {
        return true;
    }

    if (trueFallsThrough)
    {
        emitIndentedLineWithComment(stream, "if not " + condition + " then", conditionComment, indentLevel);
        emitCompactGotoOrReturn(stream, steps, nextStep, std::nullopt, indentLevel + 1);
        emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);
        return true;
    }

    emitIndentedLineWithComment(stream, "if " + condition + " then", conditionComment, indentLevel);
    emitCompactGotoOrReturn(stream, steps, instruction.jumpTargetStep, std::nullopt, indentLevel + 1);
    emitIndentedLineWithComment(stream, "end", std::nullopt, indentLevel);

    if (!falseFallsThrough)
    {
        emitCompactGotoOrReturn(stream, steps, nextStep, std::nullopt, indentLevel);
    }

    return true;
}

bool tryEmitCompactCfgNormalEventFunction(
    std::ostringstream &stream,
    std::string_view registerFunction,
    uint16_t eventId,
    const std::string &title,
    const std::optional<std::string> &hint,
    const LegacyLuaEvent &event,
    const LegacyLuaExportLookups &lookups)
{
    if (!collectPromptContinuations(event).empty())
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

    const std::vector<uint8_t> labelTargets = collectCompactLabelTargets(event, steps);
    const std::map<uint8_t, size_t> predecessorCounts = collectNormalPredecessorCounts(event, steps);
    const std::map<uint8_t, std::vector<uint8_t>> predecessors = collectNormalPredecessorSteps(event, steps);
    std::vector<uint8_t> skippedSteps;
    emitEventRegistrationHeader(stream, registerFunction, eventId, title, hint);

    if (tryEmitCompactMemoryCrystalRestoreBody(stream, event, steps, lookups))
    {
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

    for (size_t stepIndex = 0; stepIndex < steps.size(); ++stepIndex)
    {
        const uint8_t step = steps[stepIndex];
        const std::optional<uint8_t> nextStep = stepIndex + 1 < steps.size()
            ? std::optional<uint8_t>(steps[stepIndex + 1])
            : std::nullopt;

        if (std::find(skippedSteps.begin(), skippedSteps.end(), step) != skippedSteps.end())
        {
            continue;
        }

        const bool isLabelTarget = std::find(labelTargets.begin(), labelTargets.end(), step) != labelTargets.end();
        const bool needsLabel = isLabelTarget && compactLabelHasUnskippedPredecessor(predecessors, skippedSteps, step);

        if (needsLabel)
        {
            stream << "    ::" << compactStepLabel(step) << "::\n";
        }

        if (tryEmitCompactNestedOptionalBlock(stream, event, steps, step, lookups, predecessorCounts, skippedSteps))
        {
            continue;
        }

        if (tryEmitCompactConditionReturnBlock(stream, event, steps, step, lookups, predecessorCounts, skippedSteps))
        {
            continue;
        }

        if (tryEmitCompactPositiveOptionalSkipBlock(stream, event, steps, step, lookups, predecessorCounts, skippedSteps))
        {
            continue;
        }

        if (tryEmitCompactFalseOptionalBlock(stream, event, steps, step, lookups, predecessorCounts, skippedSteps))
        {
            continue;
        }

        if (tryEmitCompactOptionalPrelude(stream, event, steps, step, lookups, predecessorCounts, skippedSteps))
        {
            continue;
        }

        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, step, stepInfo))
        {
            return false;
        }

        for (const LegacyLuaInstruction *action : stepInfo.actions)
        {
            if (!emitReadableActionInstruction(stream, *action, lookups, 1))
            {
                return false;
            }
        }

        if (!stepInfo.terminalInstruction)
        {
            continue;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        switch (instruction.operation)
        {
            case LegacyLuaOperation::Exit:
                emitIndentedLineWithComment(stream, "do return end", std::nullopt, 1);
                break;

            case LegacyLuaOperation::Jump:
                emitCompactGotoOrReturn(stream, steps, instruction.jumpTargetStep, nextStep, 1);
                break;

            case LegacyLuaOperation::Compare:
            case LegacyLuaOperation::CheckItemsCount:
            case LegacyLuaOperation::CheckSkill:
            case LegacyLuaOperation::IsActorKilled:
            case LegacyLuaOperation::CheckSeason:
            case LegacyLuaOperation::IsTotalBountyHuntingAwardInRange:
            case LegacyLuaOperation::IsNpcInParty:
                if (!emitCompactConditionalTransfer(stream, instruction, steps, nextStep, lookups, 1))
                {
                    return false;
                }
                break;

            case LegacyLuaOperation::RandomJump:
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
                randomCall << "PickRandomOption(" << event.eventId << ", "
                           << static_cast<unsigned>(instruction.step + 1) << ", {";

                for (size_t argumentIndex = 0; argumentIndex < instruction.arguments.size(); ++argumentIndex)
                {
                    if (argumentIndex > 0)
                    {
                        randomCall << ", ";
                    }

                    randomCall << instruction.arguments[argumentIndex];
                }

                randomCall << "})";
                emitIndentedLineWithComment(stream, "local randomStep = " + randomCall.str(), std::nullopt, 1);

                for (size_t branchIndex = 0; branchIndex < branchStarts.size(); ++branchIndex)
                {
                    const std::string keyword = branchIndex == 0 ? "if" : "elseif";
                    emitIndentedLineWithComment(
                        stream,
                        keyword + " randomStep == " + std::to_string(branchStarts[branchIndex]) + " then",
                        std::nullopt,
                        1);
                    emitCompactGotoOrReturn(stream, steps, branchStarts[branchIndex], std::nullopt, 2);
                }

                emitIndentedLineWithComment(stream, "end", std::nullopt, 1);
                break;
            }

            case LegacyLuaOperation::InputString:
                emitIndentedLineWithComment(stream, formatInputStringCall(event, instruction), std::nullopt, 1);
                emitIndentedLineWithComment(stream, "do return end", std::nullopt, 1);
                break;

            case LegacyLuaOperation::PressAnyKey:
                emitIndentedLineWithComment(
                    stream,
                    "evt._PressAnyKey(" + std::to_string(event.eventId) + ", "
                    + std::to_string(static_cast<unsigned>(instruction.step + 1)) + ")",
                    std::nullopt,
                    1);
                emitIndentedLineWithComment(stream, "do return end", std::nullopt, 1);
                break;

            default:
                return false;
        }
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

bool tryEmitReadableGuardedTwoArmEventFunction(
    std::ostringstream &stream,
    std::string_view registerFunction,
    uint16_t eventId,
    const std::string &title,
    const std::optional<std::string> &hint,
    const LegacyLuaEvent &event,
    const LegacyLuaExportLookups &lookups)
{
    if (!collectPromptContinuations(event).empty())
    {
        return false;
    }

    const std::vector<uint8_t> steps = collectNormalEventSteps(event);

    if (steps.empty())
    {
        return false;
    }

    std::optional<uint8_t> currentStep = steps.front();
    std::ostringstream bodyStream;
    size_t guardCount = 0;

    while (currentStep && guardCount < 16)
    {
        NormalStepInfo stepInfo;

        if (!decomposeNormalStep(event, *currentStep, stepInfo)
            || !stepInfo.actions.empty()
            || !stepInfo.terminalInstruction
            || !isReadableCompareOperation(stepInfo.terminalInstruction->operation))
        {
            break;
        }

        const LegacyLuaInstruction &instruction = *stepInfo.terminalInstruction;

        if (!instruction.jumpTargetStep || !isImmediateReturnPath(event, steps, instruction.jumpTargetStep))
        {
            break;
        }

        std::string condition;
        std::optional<std::string> conditionComment;

        if (!formatReadableConditionInstruction(instruction, lookups, condition, conditionComment))
        {
            return false;
        }

        emitIndentedLineWithComment(bodyStream, "if " + condition + " then", conditionComment, 1);
        emitIndentedLineWithComment(bodyStream, "return", std::nullopt, 2);
        emitIndentedLineWithComment(bodyStream, "end", std::nullopt, 1);
        currentStep = nextStepAfter(steps, *currentStep);
        ++guardCount;
    }

    if (!currentStep)
    {
        return false;
    }

    NormalStepInfo branchStepInfo;

    if (!decomposeNormalStep(event, *currentStep, branchStepInfo)
        || !branchStepInfo.actions.empty()
        || !branchStepInfo.terminalInstruction
        || !isReadableCompareOperation(branchStepInfo.terminalInstruction->operation)
        || !branchStepInfo.terminalInstruction->jumpTargetStep)
    {
        return false;
    }

    const LegacyLuaInstruction &branchInstruction = *branchStepInfo.terminalInstruction;
    const std::optional<uint8_t> fallthroughStep = nextStepAfter(steps, *currentStep);
    SimpleBranchArm trueArm;
    SimpleBranchArm falseArm;

    if (!summarizeSimpleBranchArm(event, steps, branchInstruction.jumpTargetStep, lookups, trueArm)
        || !summarizeSimpleBranchArm(event, steps, fallthroughStep, lookups, falseArm)
        || !trueArm.returns
        || !falseArm.returns
        || trueArm.actions.empty()
        || falseArm.actions.empty())
    {
        return false;
    }

    std::string condition;
    std::optional<std::string> conditionComment;

    if (!formatReadableConditionInstruction(branchInstruction, lookups, condition, conditionComment))
    {
        return false;
    }

    emitIndentedLineWithComment(bodyStream, "if not " + condition + " then", conditionComment, 1);
    emitSimpleBranchArm(bodyStream, falseArm, lookups, 2);
    emitIndentedLineWithComment(bodyStream, "end", std::nullopt, 1);

    for (const LegacyLuaInstruction *action : trueArm.actions)
    {
        if (!emitReadableActionInstruction(bodyStream, *action, lookups, 1))
        {
            return false;
        }
    }

    emitEventRegistrationHeader(stream, registerFunction, eventId, title, hint);
    stream << bodyStream.str();

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
    const bool usesTriggerContinuation =
        triggerNeedsSyntheticEntry(sourceEvent, EvtOpcode::OnMapReload)
        || triggerNeedsSyntheticEntry(sourceEvent, EvtOpcode::OnMapLeave);

    if (isHintOnlyLegacyEvent(sourceEvent))
    {
        emitHintOnlyEventRegistration(stream, registerFunction, event.eventId, title, hint);
        return;
    }

    if (isNoOpEvent(event))
    {
        emitEventRegistrationHeader(stream, noOpFunction, event.eventId, title, hint);
        return;
    }

    if (!usesTriggerContinuation)
    {
        std::ostringstream guardedStream;

        if (tryEmitReadableGuardedTwoArmEventFunction(
                guardedStream,
                registerFunction,
                event.eventId,
                title,
                hint,
                event,
                lookups))
        {
            stream << guardedStream.str();
            return;
        }
    }

    if (!usesTriggerContinuation)
    {
        std::ostringstream readableStream;

        if (tryEmitReadablePromptEventFunction(
                readableStream,
                registerFunction,
                event.eventId,
                title,
                hint,
                event,
                lookups))
        {
            const std::string readableLua = readableStream.str();
            const std::vector<uint8_t> steps = collectNormalEventSteps(event);
            const NormalEventCfgMetrics metrics = collectNormalEventCfgMetrics(event, steps);
            const bool preferCompact = shouldPreferCompactNormalEvent(readableLua, metrics);

            if (preferCompact)
            {
                std::ostringstream compactStream;

                if (tryEmitCompactCfgNormalEventFunction(
                        compactStream,
                        registerFunction,
                        event.eventId,
                        title,
                        hint,
                        event,
                        lookups))
                {
                    stream << compactStream.str();
                    return;
                }
            }

            if (!readableNormalEventIsTooLarge(readableLua))
            {
                stream << readableLua;
                return;
            }
        }
    }

    if (!usesTriggerContinuation)
    {
        std::ostringstream readableStream;

        if (tryEmitReadableLinearEventFunction(
                readableStream,
                registerFunction,
                event.eventId,
                title,
                hint,
                event,
                lookups))
        {
            const std::string readableLua = readableStream.str();
            const std::vector<uint8_t> steps = collectNormalEventSteps(event);
            const NormalEventCfgMetrics metrics = collectNormalEventCfgMetrics(event, steps);
            const bool preferCompact = shouldPreferCompactNormalEvent(readableLua, metrics);

            if (preferCompact)
            {
                std::ostringstream compactStream;

                if (tryEmitCompactCfgNormalEventFunction(
                        compactStream,
                        registerFunction,
                        event.eventId,
                        title,
                        hint,
                        event,
                        lookups))
                {
                    stream << compactStream.str();
                    return;
                }
            }

            if (!readableNormalEventIsTooLarge(readableLua))
            {
                stream << readableLua;
                return;
            }
        }
    }

    const bool usesPromptContinuation = usesTriggerContinuation || !collectPromptContinuations(event).empty();

    if (usesPromptContinuation)
    {
        stream << registerFunction << "(" << event.eventId << ", " << luaQuoted(title)
               << ", function(continueStep)\n";
    }
    else
    {
        emitEventRegistrationHeader(stream, registerFunction, event.eventId, title, hint);
    }

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
        if (usesPromptContinuation)
        {
            stream << "    local step = continueStep or " << static_cast<unsigned>(steps.front()) << "\n";
        }
        else
        {
            stream << "    local step = " << static_cast<unsigned>(steps.front()) << "\n";
        }

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
                            "if evt.CheckMonstersKilled(" + formatActorKillCheck(instruction.arguments[0]) + ", "
                            + std::to_string(instruction.arguments[1]) + ", "
                            + std::to_string(instruction.arguments[2]) + ", "
                            + (instruction.arguments[3] != 0 ? "true" : "false") + ") then return "
                            + std::to_string(*instruction.jumpTargetStep) + " end",
                            formatActorKilledComment(
                                instruction.arguments[0],
                                instruction.arguments[1],
                                instruction.arguments[2],
                                lookups),
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
    const std::vector<SyntheticTriggerEvent> &syntheticTriggerEvents,
    LegacyLuaExportScope scope,
    LegacyEventVersion version)
{
    std::vector<std::string> textureNames;
    std::vector<std::string> spriteNames;
    std::vector<uint32_t> castSpellIds;
    collectSetTextureNames(evtProgram, textureNames);
    collectSetSpriteNames(evtProgram, spriteNames);
    collectCastSpellIds(evtProgram, castSpellIds, version);

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

        const std::optional<uint16_t> syntheticEventId =
            findSyntheticTriggerEventId(syntheticTriggerEvents, event.eventId, EvtOpcode::OnMapReload);

        stream << syntheticEventId.value_or(event.eventId);
        wroteEntry = true;
    }

    stream << "},\n";
    stream << "    onLeave = {";

    wroteEntry = false;

    for (const EvtEvent &event : evtProgram.getEvents())
    {
        if (!hasOnLeaveTrigger(event))
        {
            continue;
        }

        if (wroteEntry)
        {
            stream << ", ";
        }

        const std::optional<uint16_t> syntheticEventId =
            findSyntheticTriggerEventId(syntheticTriggerEvents, event.eventId, EvtOpcode::OnMapLeave);

        stream << syntheticEventId.value_or(event.eventId);
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

void emitSyntheticTriggerEventFunctions(
    std::ostringstream &stream,
    std::string_view scopeTableName,
    const std::vector<SyntheticTriggerEvent> &syntheticTriggerEvents)
{
    if (syntheticTriggerEvents.empty())
    {
        return;
    }

    const std::string_view registerFunction = scopeTableName == LuaScopeGlobal
        ? "RegisterGlobalEvent"
        : "RegisterEvent";

    for (const SyntheticTriggerEvent &syntheticEvent : syntheticTriggerEvents)
    {
        stream << registerFunction << "(" << syntheticEvent.syntheticEventId << ", \"\", function()\n";
        stream << "    return evt." << scopeTableName << "[" << syntheticEvent.sourceEventId << "]("
               << static_cast<unsigned>(syntheticEvent.continuationStep) << ")\n";
        stream << "end)\n\n";
    }
}
}

std::string generateLegacyEventLuaChunk(
    const EvtProgram &evtProgram,
    const StrTable &strTable,
    const LegacyLuaExportLookups &lookups,
    LegacyLuaExportScope scope,
    LegacyEventVersion version)
{
    const std::string_view scopeTableName = scope == LegacyLuaExportScope::Global ? LuaScopeGlobal : LuaScopeMap;
    const std::vector<LegacyLuaEvent> decodedEvents = decodeEvents(evtProgram, strTable, lookups, version);
    const std::vector<SyntheticTriggerEvent> syntheticTriggerEvents = collectSyntheticTriggerEvents(evtProgram);
    std::ostringstream stream;

    if (lookups.mapName && !lookups.mapName->empty())
    {
        stream << "-- " << sanitizeLuaCommentText(*lookups.mapName) << "\n";
    }

    stream << "-- generated from legacy EVT/STR\n\n";
    emitMetadata(stream, evtProgram, strTable, lookups, syntheticTriggerEvents, scope, version);
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

    emitSyntheticTriggerEventFunctions(stream, scopeTableName, syntheticTriggerEvents);

    return stream.str();
}
}
