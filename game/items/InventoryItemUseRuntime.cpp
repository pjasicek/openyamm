#include "game/items/InventoryItemUseRuntime.h"

#include "game/tables/ItemTable.h"
#include "game/party/SpellSchool.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MinutesPerDay = 24 * 60;
constexpr int DaysPerMonth = 28;
constexpr uint32_t GreenAppleItemId = 655;
constexpr uint32_t HorseshoeItemId = 656;
constexpr uint32_t ReagentFirstItemId = 200;
constexpr uint32_t ReagentLastItemId = 219;

std::string lowerAscii(std::string value)
{
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return value;
}

bool itemNameEquals(const ItemDefinition &itemDefinition, const std::string &name)
{
    return lowerAscii(itemDefinition.name) == lowerAscii(name);
}

bool itemNameContains(const ItemDefinition &itemDefinition, const std::string &text)
{
    return lowerAscii(itemDefinition.name).find(lowerAscii(text)) != std::string::npos;
}

int totalDaysFromGameMinutes(float gameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(gameMinutes)));
    return totalMinutes / MinutesPerDay;
}

int monthIndexFromGameMinutes(float gameMinutes)
{
    return (totalDaysFromGameMinutes(gameMinutes) / DaysPerMonth) % 12;
}

int monthWeekFromGameMinutes(float gameMinutes)
{
    return (totalDaysFromGameMinutes(gameMinutes) % DaysPerMonth) / 7;
}

int dayOfMonthFromGameMinutes(float gameMinutes)
{
    return 1 + totalDaysFromGameMinutes(gameMinutes) % DaysPerMonth;
}

std::optional<uint32_t> tryParseSpellId(const ItemDefinition &itemDefinition)
{
    if (itemDefinition.mod1.size() < 2
        || (itemDefinition.mod1[0] != 'S' && itemDefinition.mod1[0] != 's'))
    {
        return std::nullopt;
    }

    for (size_t index = 1; index < itemDefinition.mod1.size(); ++index)
    {
        if (!std::isdigit(static_cast<unsigned char>(itemDefinition.mod1[index])))
        {
            return std::nullopt;
        }
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(itemDefinition.mod1.substr(1)));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

int maxSpellPointsForMember(const Character &member)
{
    return std::max(
        0,
        member.maxSpellPoints + member.permanentBonuses.maxSpellPoints + member.magicalBonuses.maxSpellPoints);
}

bool restoreSpellPoints(Character &member, int amount)
{
    if (amount <= 0)
    {
        return false;
    }

    const int previousSpellPoints = member.spellPoints;
    member.spellPoints = std::clamp(member.spellPoints + amount, 0, maxSpellPointsForMember(member));
    return member.spellPoints > previousSpellPoints;
}

bool clearAllRestorableConditions(Party &party, size_t memberIndex)
{
    static constexpr std::array<CharacterCondition, 12> clearableConditions = {
        CharacterCondition::Cursed,
        CharacterCondition::Weak,
        CharacterCondition::Asleep,
        CharacterCondition::Fear,
        CharacterCondition::Drunk,
        CharacterCondition::Insane,
        CharacterCondition::PoisonWeak,
        CharacterCondition::DiseaseWeak,
        CharacterCondition::PoisonMedium,
        CharacterCondition::DiseaseMedium,
        CharacterCondition::PoisonSevere,
        CharacterCondition::DiseaseSevere,
    };

    bool changed = false;

    for (CharacterCondition condition : clearableConditions)
    {
        changed = party.clearMemberCondition(memberIndex, condition) || changed;
    }

    changed = party.clearMemberCondition(memberIndex, CharacterCondition::Paralyzed) || changed;
    changed = party.clearMemberCondition(memberIndex, CharacterCondition::Zombie) || changed;
    return changed;
}

bool applyPermanentStatPotion(Character &member, uint32_t itemId)
{
    switch (itemId)
    {
        case 264:
            member.permanentBonuses.luck += 50;
            return true;
        case 265:
            member.permanentBonuses.speed += 50;
            return true;
        case 266:
            member.permanentBonuses.intellect += 50;
            return true;
        case 267:
            member.permanentBonuses.endurance += 50;
            return true;
        case 268:
            member.permanentBonuses.personality += 50;
            return true;
        case 269:
            member.permanentBonuses.accuracy += 50;
            return true;
        case 270:
            member.permanentBonuses.might += 50;
            return true;
        default:
            return false;
    }
}

std::optional<CharacterCondition> majorCondition(const Character &member)
{
    constexpr CharacterCondition conditions[] = {
        CharacterCondition::Eradicated,
        CharacterCondition::Petrified,
        CharacterCondition::Dead,
        CharacterCondition::Unconscious,
        CharacterCondition::Paralyzed,
        CharacterCondition::Asleep,
        CharacterCondition::Insane,
        CharacterCondition::Fear,
        CharacterCondition::DiseaseSevere,
        CharacterCondition::DiseaseMedium,
        CharacterCondition::DiseaseWeak,
        CharacterCondition::PoisonSevere,
        CharacterCondition::PoisonMedium,
        CharacterCondition::PoisonWeak,
        CharacterCondition::Weak,
        CharacterCondition::Cursed,
        CharacterCondition::Drunk,
    };

    for (CharacterCondition condition : conditions)
    {
        if (member.conditions.test(static_cast<size_t>(condition)))
        {
            return condition;
        }
    }

    if (member.health <= 0)
    {
        return CharacterCondition::Unconscious;
    }

    return std::nullopt;
}

std::string conditionDisplayName(CharacterCondition condition)
{
    switch (condition)
    {
        case CharacterCondition::Cursed:
            return "Cursed";
        case CharacterCondition::Weak:
            return "Weak";
        case CharacterCondition::Asleep:
            return "Asleep";
        case CharacterCondition::Fear:
            return "Afraid";
        case CharacterCondition::Drunk:
            return "Drunk";
        case CharacterCondition::Insane:
            return "Insane";
        case CharacterCondition::PoisonWeak:
        case CharacterCondition::PoisonMedium:
        case CharacterCondition::PoisonSevere:
            return "Poisoned";
        case CharacterCondition::DiseaseWeak:
        case CharacterCondition::DiseaseMedium:
        case CharacterCondition::DiseaseSevere:
            return "Diseased";
        case CharacterCondition::Paralyzed:
            return "Paralyzed";
        case CharacterCondition::Unconscious:
            return "Unconscious";
        case CharacterCondition::Dead:
            return "Dead";
        case CharacterCondition::Petrified:
            return "Petrified";
        case CharacterCondition::Eradicated:
            return "Eradicated";
        case CharacterCondition::Zombie:
            return "Zombie";
        case CharacterCondition::Count:
            break;
    }

    return {};
}

bool canUseSpellItem(const Character &member)
{
    const std::optional<CharacterCondition> condition = majorCondition(member);
    return !condition.has_value()
        || (*condition != CharacterCondition::Asleep
            && *condition != CharacterCondition::Paralyzed
            && *condition != CharacterCondition::Unconscious
            && *condition != CharacterCondition::Dead
            && *condition != CharacterCondition::Petrified
            && *condition != CharacterCondition::Eradicated);
}

std::string inactiveCharacterStatusText(const Character &member)
{
    const std::optional<CharacterCondition> condition = majorCondition(member);

    if (condition)
    {
        return "That player is " + conditionDisplayName(*condition);
    }

    return "That player is not active";
}

std::string itemDisplayNameForStatus(const ItemDefinition &itemDefinition)
{
    return itemDefinition.name.empty() ? "Item" : itemDefinition.name;
}

std::string itemCannotBeUsedStatusText(const ItemDefinition &itemDefinition)
{
    return itemDisplayNameForStatus(itemDefinition) + " can not be used that way";
}

bool isFoodItem(const InventoryItem &item, const ItemDefinition &itemDefinition)
{
    return item.objectDescriptionId == GreenAppleItemId
        || itemNameContains(itemDefinition, "apple")
        || itemNameContains(itemDefinition, "tobersk fruit");
}

std::optional<SoundId> instrumentSoundId(const ItemDefinition &itemDefinition)
{
    if (itemNameContains(itemDefinition, "lute"))
    {
        return SoundId::LuteGuitar;
    }

    if (itemNameContains(itemDefinition, "faerie pipes")
        || itemNameContains(itemDefinition, "pan flute")
        || itemNameContains(itemDefinition, "panflute"))
    {
        return SoundId::PanFlute;
    }

    if (itemNameContains(itemDefinition, "trumpet"))
    {
        return SoundId::Trumpet;
    }

    if (itemNameEquals(itemDefinition, "flute"))
    {
        return SoundId::Flute;
    }

    return std::nullopt;
}

void addPermanentStatBonus(Character &member, int CharacterStatBonuses::*field, int value)
{
    member.permanentBonuses.*field += value;
}

void addPermanentResistanceBonus(Character &member, int CharacterResistanceSet::*field, int value)
{
    member.permanentBonuses.resistances.*field += value;
}

std::string applyGenieLampReward(Party &party, Character &member, size_t memberIndex, float gameMinutes)
{
    const int value = monthWeekFromGameMinutes(gameMinutes) + 1;

    switch (monthIndexFromGameMinutes(gameMinutes))
    {
        case 0:
            addPermanentStatBonus(member, &CharacterStatBonuses::might, value);
            return "+" + std::to_string(value) + " Might Permanent";
        case 1:
            addPermanentStatBonus(member, &CharacterStatBonuses::intellect, value);
            return "+" + std::to_string(value) + " Intellect Permanent";
        case 2:
            addPermanentStatBonus(member, &CharacterStatBonuses::personality, value);
            return "+" + std::to_string(value) + " Personality Permanent";
        case 3:
            addPermanentStatBonus(member, &CharacterStatBonuses::endurance, value);
            return "+" + std::to_string(value) + " Endurance Permanent";
        case 4:
            addPermanentStatBonus(member, &CharacterStatBonuses::accuracy, value);
            return "+" + std::to_string(value) + " Accuracy Permanent";
        case 5:
            addPermanentStatBonus(member, &CharacterStatBonuses::speed, value);
            return "+" + std::to_string(value) + " Speed Permanent";
        case 6:
            addPermanentStatBonus(member, &CharacterStatBonuses::luck, value);
            return "+" + std::to_string(value) + " Luck Permanent";
        case 7:
        {
            const int gold = 1000 * value;
            party.addGold(gold);
            return "+" + std::to_string(gold) + " Gold";
        }
        case 8:
        {
            const int food = 5 * value;
            party.addFood(food);
            return "+" + std::to_string(food) + " Food";
        }
        case 9:
            member.skillPoints += static_cast<uint32_t>(2 * value);
            return "+" + std::to_string(2 * value) + " Skill Points";
        case 10:
            party.addExperienceToMember(memberIndex, 2500LL * value);
            return "+" + std::to_string(2500 * value) + " Experience";
        case 11:
        {
            static thread_local std::mt19937 rng(std::random_device{}());
            const int resistanceIndex = std::uniform_int_distribution<int>(0, 5)(rng);

            switch (resistanceIndex)
            {
                case 0:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::fire, value);
                    return "+" + std::to_string(value) + " Fire Permanent";
                case 1:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::air, value);
                    return "+" + std::to_string(value) + " Air Permanent";
                case 2:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::water, value);
                    return "+" + std::to_string(value) + " Water Permanent";
                case 3:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::earth, value);
                    return "+" + std::to_string(value) + " Earth Permanent";
                case 4:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::mind, value);
                    return "+" + std::to_string(value) + " Mind Permanent";
                default:
                    addPermanentResistanceBonus(member, &CharacterResistanceSet::body, value);
                    return "+" + std::to_string(value) + " Body Permanent";
            }
        }
        default:
            break;
    }

    return {};
}

SkillMastery requiredMasteryForSpell(uint32_t spellId)
{
    const std::optional<std::string> skillName = resolveMagicSkillName(spellId);

    if (!skillName)
    {
        return SkillMastery::None;
    }

    const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(*skillName);

    if (!spellRange || spellId < spellRange->first || spellId > spellRange->second)
    {
        return SkillMastery::None;
    }

    const uint32_t spellCount = spellRange->second - spellRange->first + 1;

    if (spellCount < 11)
    {
        return SkillMastery::Normal;
    }

    const uint32_t spellOrdinal = spellId - spellRange->first + 1;

    if (spellOrdinal <= 4)
    {
        return SkillMastery::Normal;
    }

    if (spellOrdinal <= 7)
    {
        return SkillMastery::Expert;
    }

    if (spellOrdinal <= 10)
    {
        return SkillMastery::Master;
    }

    return SkillMastery::Grandmaster;
}

InventoryItemUseResult makeFailure(
    InventoryItemUseAction action,
    const std::string &statusText,
    std::optional<SpeechId> speechId = std::nullopt)
{
    InventoryItemUseResult result = {};
    result.handled = true;
    result.action = action;
    result.statusText = statusText;
    result.speechId = speechId;
    return result;
}
}

InventoryItemUseAction InventoryItemUseRuntime::classifyItemUse(const InventoryItem &item, const ItemTable &itemTable)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return InventoryItemUseAction::None;
    }

    if (pItemDefinition->equipStat == "Sscroll")
    {
        return InventoryItemUseAction::CastScroll;
    }

    if (pItemDefinition->equipStat == "Book")
    {
        return InventoryItemUseAction::LearnSpell;
    }

    if (pItemDefinition->equipStat == "Bottle")
    {
        return InventoryItemUseAction::ConsumePotion;
    }

    if (pItemDefinition->equipStat == "Mscroll")
    {
        return InventoryItemUseAction::ReadMessageScroll;
    }

    if (item.objectDescriptionId == HorseshoeItemId || itemNameEquals(*pItemDefinition, "horseshoe"))
    {
        return InventoryItemUseAction::UseHorseshoe;
    }

    if (itemNameEquals(*pItemDefinition, "genie lamp"))
    {
        return InventoryItemUseAction::UseGenieLamp;
    }

    if (isFoodItem(item, *pItemDefinition))
    {
        return InventoryItemUseAction::EatFoodItem;
    }

    if (instrumentSoundId(*pItemDefinition).has_value())
    {
        return InventoryItemUseAction::PlayInstrument;
    }

    if (itemNameEquals(*pItemDefinition, "temple in a bottle"))
    {
        return InventoryItemUseAction::UseTempleInABottle;
    }

    if (item.objectDescriptionId >= ReagentFirstItemId
        && item.objectDescriptionId <= ReagentLastItemId
        && pItemDefinition->equipStat == "Reagent")
    {
        return InventoryItemUseAction::UseReagent;
    }

    if (!pItemDefinition->equipStat.empty()
        && pItemDefinition->equipStat != "0"
        && pItemDefinition->equipStat != "N / A"
        && pItemDefinition->equipStat != "Misc")
    {
        return InventoryItemUseAction::Equip;
    }

    return InventoryItemUseAction::None;
}

InventoryItemUseResult InventoryItemUseRuntime::useItemOnMember(
    Party &party,
    size_t targetMemberIndex,
    const InventoryItem &item,
    const ItemTable &itemTable,
    const ReadableScrollTable *pReadableScrollTable,
    const InventoryItemUseContext &context)
{
    InventoryItemUseResult result = {};
    result.action = classifyItemUse(item, itemTable);

    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);
    Character *pTargetMember = party.member(targetMemberIndex);

    if (pItemDefinition == nullptr || pTargetMember == nullptr)
    {
        return makeFailure(result.action, "Item can not be used that way");
    }

    switch (result.action)
    {
        case InventoryItemUseAction::CastScroll:
        {
            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            if (context.underwater)
            {
                return makeFailure(result.action, "You can not do that while you are underwater!");
            }

            if (pTargetMember->recoverySecondsRemaining > 0.0f)
            {
                return makeFailure(result.action, "That player is not active");
            }

            const std::optional<uint32_t> spellId = tryParseSpellId(*pItemDefinition);

            if (!spellId)
            {
                return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
            }

            result.handled = true;
            result.consumed = true;
            result.spellId = *spellId;
            result.spellSkillLevelOverride = 5;
            result.spellSkillMasteryOverride = SkillMastery::Master;
            return result;
        }

        case InventoryItemUseAction::LearnSpell:
        {
            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            const std::optional<uint32_t> spellId = tryParseSpellId(*pItemDefinition);

            if (!spellId)
            {
                return makeFailure(
                    result.action,
                    itemCannotBeUsedStatusText(*pItemDefinition),
                    SpeechId::CantLearnSpell);
            }

            const std::optional<std::string> skillName = resolveMagicSkillName(*spellId);

            if (!skillName)
            {
                return makeFailure(
                    result.action,
                    itemCannotBeUsedStatusText(*pItemDefinition),
                    SpeechId::CantLearnSpell);
            }

            const CharacterSkill *pSkill = pTargetMember->findSkill(*skillName);

            if (pSkill == nullptr || pSkill->mastery == SkillMastery::None || pSkill->level == 0)
            {
                return makeFailure(
                    result.action,
                    "You don't have the skill to learn " + itemDisplayNameForStatus(*pItemDefinition),
                    SpeechId::CantLearnSpell);
            }

            const SkillMastery requiredMastery = requiredMasteryForSpell(*spellId);

            if (requiredMastery != SkillMastery::None && pSkill->mastery < requiredMastery)
            {
                return makeFailure(
                    result.action,
                    "You don't have the skill to learn " + itemDisplayNameForStatus(*pItemDefinition),
                    SpeechId::CantLearnSpell);
            }

            if (pTargetMember->knowsSpell(*spellId))
            {
                result = makeFailure(
                    result.action,
                    "You already know the " + itemDisplayNameForStatus(*pItemDefinition) + " spell");
                result.alreadyKnown = true;
                return result;
            }

            pTargetMember->learnSpell(*spellId);
            result.handled = true;
            result.consumed = true;
            result.spellId = *spellId;
            result.speechId = SpeechId::LearnSpell;
            return result;
        }

        case InventoryItemUseAction::ConsumePotion:
        {
            if (item.objectDescriptionId == 222)
            {
                party.healMember(targetMemberIndex, 10);
                result.handled = true;
                result.consumed = true;
                return result;
            }

            if (item.objectDescriptionId == 223)
            {
                restoreSpellPoints(*pTargetMember, 10);
                result.handled = true;
                result.consumed = true;
                return result;
            }

            if (item.objectDescriptionId == 252)
            {
                clearAllRestorableConditions(party, targetMemberIndex);
                result.handled = true;
                result.consumed = true;
                return result;
            }

            if (item.objectDescriptionId == 253)
            {
                party.healMember(targetMemberIndex, 50);
                result.handled = true;
                result.consumed = true;
                return result;
            }

            if (item.objectDescriptionId == 254)
            {
                restoreSpellPoints(*pTargetMember, 50);
                result.handled = true;
                result.consumed = true;
                return result;
            }

            if (item.objectDescriptionId == 262)
            {
                party.clearMemberCondition(targetMemberIndex, CharacterCondition::Petrified);
                result.handled = true;
                result.consumed = true;
                return result;
            }

            if (applyPermanentStatPotion(*pTargetMember, item.objectDescriptionId))
            {
                result.handled = true;
                result.consumed = true;
                return result;
            }

            return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition), SpeechId::PotionFail);
        }

        case InventoryItemUseAction::ReadMessageScroll:
        {
            const ReadableScrollEntry *pEntry =
                pReadableScrollTable != nullptr ? pReadableScrollTable->get(item.objectDescriptionId) : nullptr;

            if (pEntry == nullptr || pEntry->text.empty())
            {
                return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
            }

            if (!canUseSpellItem(*pTargetMember))
            {
                return makeFailure(result.action, inactiveCharacterStatusText(*pTargetMember));
            }

            result.handled = true;
            result.readableTitle = pItemDefinition->name.empty() ? pEntry->itemName : pItemDefinition->name;
            result.readableBody = pEntry->text;
            return result;
        }

        case InventoryItemUseAction::UseHorseshoe:
        {
            pTargetMember->skillPoints += 2;
            result.handled = true;
            result.consumed = true;
            result.statusText = "+2 Skill Points!";
            result.soundId = SoundId::Quest;
            result.speechId = SpeechId::QuestGot;
            return result;
        }

        case InventoryItemUseAction::UseGenieLamp:
        {
            result.handled = true;
            result.consumed = true;
            result.statusText = applyGenieLampReward(party, *pTargetMember, targetMemberIndex, context.gameMinutes);
            result.soundId = SoundId::Chimes;
            result.speechId = SpeechId::QuestGot;

            const int dayOfMonth = dayOfMonthFromGameMinutes(context.gameMinutes);

            if (dayOfMonth == 6 || dayOfMonth == 20)
            {
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Eradicated);
                result.soundId = SoundId::Gong;
            }
            else if (dayOfMonth == 12 || dayOfMonth == 26)
            {
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Dead);
                result.soundId = SoundId::Gong;
            }
            else if (dayOfMonth == 4 || dayOfMonth == 25)
            {
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Petrified);
                result.soundId = SoundId::Gong;
            }

            return result;
        }

        case InventoryItemUseAction::EatFoodItem:
        {
            party.addFood(1);
            result.handled = true;
            result.consumed = true;
            return result;
        }

        case InventoryItemUseAction::PlayInstrument:
        {
            result.handled = true;
            result.soundId = instrumentSoundId(*pItemDefinition);
            return result;
        }

        case InventoryItemUseAction::UseTempleInABottle:
        {
            result.handled = true;
            return result;
        }

        case InventoryItemUseAction::UseReagent:
        {
            return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
        }

        case InventoryItemUseAction::Equip:
        case InventoryItemUseAction::None:
        default:
        {
            return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
        }
    }
}
}
