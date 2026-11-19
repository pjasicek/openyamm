#include "game/items/InventoryItemUseRuntime.h"

#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/party/SpellIds.h"
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
constexpr uint32_t ToberskFruitItemId = 643;
constexpr uint32_t GreenAppleItemId = 655;
constexpr uint32_t Mm7RedAppleItemId = 1432;
constexpr uint32_t Mm6AppleItemId = 2104;
constexpr uint32_t HorseshoeItemId = 656;
constexpr uint32_t Mm7HorseshoeItemId = 1448;
constexpr uint32_t Mm6HorseshoeItemId = 2083;
constexpr uint32_t DimensionDoorScrollItemId = 190;
constexpr uint32_t ChargedConnectorStoneItemId = 624;
constexpr uint32_t DischargedConnectorStoneItemId = 625;
constexpr uint32_t GenieLampItemId = 1418;
constexpr uint32_t DeckOfFateItemId = 2067;
constexpr uint32_t ExtraPotionPlayerBitBase = 200000;

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

std::vector<std::string> pipeSeparatedSkills(const std::string &value)
{
    std::vector<std::string> result;
    size_t begin = 0;

    while (begin <= value.size())
    {
        const size_t end = value.find('|', begin);
        const std::string canonicalName = canonicalSkillName(value.substr(begin, end - begin));

        if (!canonicalName.empty()
            && std::find(result.begin(), result.end(), canonicalName) == result.end())
        {
            result.push_back(canonicalName);
        }

        if (end == std::string::npos)
        {
            break;
        }

        begin = end + 1;
    }

    return result;
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
    return Party::effectiveMaximumSpellPoints(member);
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

bool markExtraPotionUsed(Character &member, uint32_t itemId)
{
    const uint32_t bit = ExtraPotionPlayerBitBase + itemId;

    if (member.playerBits.contains(bit))
    {
        return false;
    }

    member.playerBits.insert(bit);
    return true;
}

void applyTemporaryStatPotion(Character &member, int CharacterStatBonuses::*field, int power)
{
    member.magicalBonuses.*field += std::max(1, power);
}

void applyTemporaryResistancePotion(Character &member, int CharacterResistanceSet::*field, int power)
{
    member.magicalBonuses.resistances.*field += std::max(1, power);
}

bool applyBoostPotion(Character &member, uint32_t potionId, int power)
{
    switch (potionId)
    {
        case 20:
            applyTemporaryStatPotion(member, &CharacterStatBonuses::might, power);
            return true;
        case 21:
            applyTemporaryStatPotion(member, &CharacterStatBonuses::intellect, power);
            return true;
        case 22:
            applyTemporaryStatPotion(member, &CharacterStatBonuses::personality, power);
            return true;
        case 23:
            applyTemporaryStatPotion(member, &CharacterStatBonuses::endurance, power);
            return true;
        case 24:
            applyTemporaryStatPotion(member, &CharacterStatBonuses::speed, power);
            return true;
        case 25:
            applyTemporaryStatPotion(member, &CharacterStatBonuses::accuracy, power);
            return true;
        case 35:
            applyTemporaryStatPotion(member, &CharacterStatBonuses::luck, power);
            return true;
        case 36:
            applyTemporaryResistancePotion(member, &CharacterResistanceSet::fire, power);
            return true;
        case 37:
            applyTemporaryResistancePotion(member, &CharacterResistanceSet::air, power);
            return true;
        case 38:
            applyTemporaryResistancePotion(member, &CharacterResistanceSet::water, power);
            return true;
        case 39:
            applyTemporaryResistancePotion(member, &CharacterResistanceSet::earth, power);
            return true;
        case 40:
            applyTemporaryResistancePotion(member, &CharacterResistanceSet::mind, power);
            return true;
        case 41:
            applyTemporaryResistancePotion(member, &CharacterResistanceSet::body, power);
            return true;
        default:
            return false;
    }
}

void decreaseBaseStat(uint32_t &stat, uint32_t amount)
{
    stat = stat > amount ? stat - amount : 0;
}

bool applyEssencePotion(Character &member, uint32_t itemId, uint32_t Character::*primary, uint32_t Character::*penalty)
{
    if (!markExtraPotionUsed(member, itemId))
    {
        return false;
    }

    member.*primary += 15;
    decreaseBaseStat(member.*penalty, 5);
    return true;
}

bool applyExtraPotionEffect(Party &party, size_t targetMemberIndex, Character &member, uint32_t potionId, uint32_t itemId, int power)
{
    switch (potionId)
    {
        case 51:
            member.ageModifier -= std::max(1, static_cast<int>(std::ceil(static_cast<double>(power) / 10.0)));
            return true;
        case 52:
            return applyEssencePotion(member, itemId, &Character::might, &Character::intellect);
        case 53:
            return applyEssencePotion(member, itemId, &Character::intellect, &Character::might);
        case 54:
            return applyEssencePotion(member, itemId, &Character::personality, &Character::speed);
        case 55:
            if (!markExtraPotionUsed(member, itemId))
            {
                return false;
            }
            decreaseBaseStat(member.might, 1);
            decreaseBaseStat(member.intellect, 1);
            decreaseBaseStat(member.personality, 1);
            decreaseBaseStat(member.accuracy, 1);
            decreaseBaseStat(member.speed, 1);
            decreaseBaseStat(member.luck, 1);
            member.endurance += 15;
            return true;
        case 56:
            return applyEssencePotion(member, itemId, &Character::accuracy, &Character::luck);
        case 57:
            return applyEssencePotion(member, itemId, &Character::speed, &Character::personality);
        case 58:
            return applyEssencePotion(member, itemId, &Character::luck, &Character::accuracy);
        case 59:
            member.might += 1;
            member.intellect += 1;
            member.personality += 1;
            member.endurance += 1;
            member.accuracy += 1;
            member.speed += 1;
            member.luck += 1;
            member.baseResistances.fire += 1;
            member.baseResistances.air += 1;
            member.baseResistances.water += 1;
            member.baseResistances.earth += 1;
            member.baseResistances.mind += 1;
            member.baseResistances.body += 1;
            member.ageModifier += 5;
            return true;
        case 60:
            member.magicalBonuses.might += power * 3;
            member.magicalBonuses.intellect += power * 3;
            member.magicalBonuses.personality += power * 3;
            member.magicalBonuses.endurance += power * 3;
            member.magicalBonuses.accuracy += power * 3;
            member.magicalBonuses.speed += power * 3;
            member.magicalBonuses.luck += power * 3;
            return true;
        case 61:
            member.magicalBonuses.resistances.fire += power * 3;
            member.magicalBonuses.resistances.air += power * 3;
            member.magicalBonuses.resistances.water += power * 3;
            member.magicalBonuses.resistances.earth += power * 3;
            member.magicalBonuses.resistances.mind += power * 3;
            member.magicalBonuses.resistances.body += power * 3;
            return true;
        case 62:
            member.levelModifier += 20;
            return true;
        case 63:
            if (!markExtraPotionUsed(member, itemId))
            {
                return false;
            }
            member.might += 20;
            member.intellect += 20;
            member.personality += 20;
            member.endurance += 20;
            member.accuracy += 20;
            member.speed += 20;
            member.luck += 20;
            member.ageModifier += 10;
            return true;
        case 64:
            if (!markExtraPotionUsed(member, itemId)) return false;
            member.baseResistances.fire += 40;
            return true;
        case 65:
            if (!markExtraPotionUsed(member, itemId)) return false;
            member.baseResistances.air += 40;
            return true;
        case 66:
            if (!markExtraPotionUsed(member, itemId)) return false;
            member.baseResistances.water += 40;
            return true;
        case 67:
            if (!markExtraPotionUsed(member, itemId)) return false;
            member.baseResistances.earth += 40;
            return true;
        case 68:
            if (!markExtraPotionUsed(member, itemId)) return false;
            member.baseResistances.mind += 40;
            return true;
        case 69:
            if (!markExtraPotionUsed(member, itemId)) return false;
            member.baseResistances.body += 40;
            return true;
        case 70:
            party.applyPartyBuff(
                PartyBuffId::ProtectionFromMagic,
                30.0f * 60.0f * static_cast<float>(std::max(1, power)),
                3,
                0,
                10,
                SkillMastery::Grandmaster,
                static_cast<uint32_t>(targetMemberIndex));
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

bool isFoodItem(uint32_t itemId)
{
    return itemId == ToberskFruitItemId || itemId == GreenAppleItemId
        || itemId == Mm7RedAppleItemId || itemId == Mm6AppleItemId;
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

std::string applyDeckOfFateReward(Character &member, float gameMinutes)
{
    const int value = monthWeekFromGameMinutes(gameMinutes) + 1;

    switch (monthIndexFromGameMinutes(gameMinutes))
    {
        case 0:
            addPermanentStatBonus(member, &CharacterStatBonuses::might, value);
            return "+" + std::to_string(value) + " Might!";
        case 1:
            addPermanentStatBonus(member, &CharacterStatBonuses::intellect, value);
            return "+" + std::to_string(value) + " Intellect!";
        case 2:
            addPermanentStatBonus(member, &CharacterStatBonuses::personality, value);
            return "+" + std::to_string(value) + " Personality!";
        case 3:
            addPermanentStatBonus(member, &CharacterStatBonuses::endurance, value);
            return "+" + std::to_string(value) + " Endurance!";
        case 4:
            addPermanentStatBonus(member, &CharacterStatBonuses::accuracy, value);
            return "+" + std::to_string(value) + " Accuracy!";
        case 5:
            addPermanentStatBonus(member, &CharacterStatBonuses::speed, value);
            return "+" + std::to_string(value) + " Speed!";
        case 6:
            addPermanentStatBonus(member, &CharacterStatBonuses::luck, value);
            return "+" + std::to_string(value) + " Luck!";
        case 7:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::fire, value);
            return "+" + std::to_string(value) + " Fire Resistance!";
        case 8:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::air, value);
            return "+" + std::to_string(value) + " Air Resistance!";
        case 9:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::water, value);
            return "+" + std::to_string(value) + " Water Resistance!";
        case 10:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::earth, value);
            return "+" + std::to_string(value) + " Earth Resistance!";
        case 11:
            addPermanentResistanceBonus(member, &CharacterResistanceSet::body, value);
            return "+" + std::to_string(value) + " Body Resistance!";
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

InventoryItemUseAction InventoryItemUseRuntime::classifyItemUse(
    const InventoryItem &item,
    const ItemTable &itemTable,
    const MergedPotionSettingTable *pPotionSettingTable,
    const MergedReagentSettingTable *pReagentSettingTable)
{
    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return InventoryItemUseAction::None;
    }

    if (item.objectDescriptionId == DimensionDoorScrollItemId)
    {
        return InventoryItemUseAction::UseDimensionDoorScroll;
    }

    if (item.objectDescriptionId == ChargedConnectorStoneItemId
        || item.objectDescriptionId == DischargedConnectorStoneItemId)
    {
        return InventoryItemUseAction::UseConnectorStone;
    }

    if (lowerAscii(pItemDefinition->useAction) == "learnskill")
    {
        return InventoryItemUseAction::LearnSkill;
    }

    if (lowerAscii(pItemDefinition->useAction) == "readtext")
    {
        return InventoryItemUseAction::ReadMessageScroll;
    }

    if (pItemDefinition->equipStat == "Sscroll")
    {
        return InventoryItemUseAction::CastScroll;
    }

    if (pItemDefinition->equipStat == "Book")
    {
        return InventoryItemUseAction::LearnSpell;
    }

    const MergedPotionSettingEntry *pPotionSetting =
        pPotionSettingTable != nullptr ? pPotionSettingTable->getByItemId(item.objectDescriptionId) : nullptr;

    if (pPotionSetting != nullptr)
    {
        return pPotionSetting->drinkable ? InventoryItemUseAction::ConsumePotion : InventoryItemUseAction::None;
    }

    if (pItemDefinition->equipStat == "Bottle")
    {
        return InventoryItemUseAction::ConsumePotion;
    }

    if (pItemDefinition->equipStat == "Mscroll")
    {
        return InventoryItemUseAction::ReadMessageScroll;
    }

    if (item.objectDescriptionId == HorseshoeItemId
        || item.objectDescriptionId == Mm7HorseshoeItemId
        || item.objectDescriptionId == Mm6HorseshoeItemId)
    {
        return InventoryItemUseAction::UseHorseshoe;
    }

    if (item.objectDescriptionId == GenieLampItemId)
    {
        return InventoryItemUseAction::UseGenieLamp;
    }

    if (item.objectDescriptionId == DeckOfFateItemId || itemNameEquals(*pItemDefinition, "deck of fate"))
    {
        return InventoryItemUseAction::UseDeckOfFate;
    }

    if (isFoodItem(item.objectDescriptionId))
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

    if (pReagentSettingTable != nullptr
        && pReagentSettingTable->resultItemIdForReagent(item.objectDescriptionId).has_value())
    {
        return InventoryItemUseAction::UseReagent;
    }

    if (pItemDefinition->equipStat == "Reagent")
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
    const MergedPotionSettingTable *pPotionSettingTable,
    const MergedReagentSettingTable *pReagentSettingTable,
    const InventoryItemUseContext &context)
{
    InventoryItemUseResult result = {};
    result.action = classifyItemUse(item, itemTable, pPotionSettingTable, pReagentSettingTable);

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
            result.spellBypassRequiredMastery = true;
            return result;
        }

        case InventoryItemUseAction::UseDimensionDoorScroll:
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

            result.handled = true;
            result.consumed = true;
            result.spellId = spellIdValue(SpellId::TownPortal);
            result.spellSkillLevelOverride = 5;
            result.spellSkillMasteryOverride = SkillMastery::Master;
            result.spellBypassRequiredMastery = true;
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

        case InventoryItemUseAction::LearnSkill:
        {
            const std::vector<std::string> targetSkills = pipeSeparatedSkills(pItemDefinition->useTarget);

            if (targetSkills.empty())
            {
                return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition));
            }

            std::vector<std::string> learnableSkills;
            bool hasAlreadyKnownSkill = false;
            const ClassSkillTable *pClassSkillTable = party.classSkillTable();

            for (const std::string &skillName : targetSkills)
            {
                const bool classCanLearn = pClassSkillTable != nullptr
                    && pClassSkillTable->getEffectiveCap(
                        pTargetMember->className,
                        pTargetMember->raceId,
                        skillName) != SkillMastery::None;

                if (!classCanLearn)
                {
                    continue;
                }

                if (pTargetMember->hasSkill(skillName))
                {
                    hasAlreadyKnownSkill = true;
                    continue;
                }

                if (party.canMemberLearnSkill(targetMemberIndex, skillName))
                {
                    learnableSkills.push_back(skillName);
                }
            }

            if (hasAlreadyKnownSkill)
            {
                result = makeFailure(
                    result.action,
                    "You already know one or more skills in " + itemDisplayNameForStatus(*pItemDefinition));
                result.alreadyKnown = true;
                return result;
            }

            if (learnableSkills.size() != targetSkills.size())
            {
                result = makeFailure(
                    result.action,
                    "This character cannot learn the skills in " + itemDisplayNameForStatus(*pItemDefinition));
                return result;
            }

            for (const std::string &skillName : learnableSkills)
            {
                if (!party.learnMemberSkill(targetMemberIndex, skillName))
                {
                    return makeFailure(result.action, "The skill could not be learned");
                }
            }

            result.handled = true;
            result.consumed = true;
            result.learnedSkills = learnableSkills;
            result.statusText = learnableSkills.size() == 1
                ? "Learned " + displaySkillName(learnableSkills.front())
                : "Learned the skills in " + itemDisplayNameForStatus(*pItemDefinition);
            return result;
        }

        case InventoryItemUseAction::ConsumePotion:
        {
            const MergedPotionSettingEntry *pPotionSetting =
                pPotionSettingTable != nullptr ? pPotionSettingTable->getByItemId(item.objectDescriptionId) : nullptr;
            const uint32_t potionId = pPotionSetting != nullptr ? pPotionSetting->potionId : 0;
            const int potionPower = std::max(1, static_cast<int>(item.standardEnchantPower));

            if (potionId >= 51 && potionId <= 70)
            {
                if (applyExtraPotionEffect(
                        party,
                        targetMemberIndex,
                        *pTargetMember,
                        potionId,
                        item.objectDescriptionId,
                        potionPower))
                {
                    result.handled = true;
                    result.consumed = true;
                    return result;
                }

                return makeFailure(result.action, itemCannotBeUsedStatusText(*pItemDefinition), SpeechId::PotionFail);
            }

            if (applyBoostPotion(*pTargetMember, potionId, potionPower))
            {
                result.handled = true;
                result.consumed = true;
                return result;
            }

            switch (potionId)
            {
                case 4:
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::Weak);
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 5:
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::DiseaseWeak);
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::DiseaseMedium);
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::DiseaseSevere);
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 6:
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::PoisonWeak);
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::PoisonMedium);
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::PoisonSevere);
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 7:
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::Asleep);
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 8:
                    party.applyPartyBuff(PartyBuffId::Haste, 30.0f * 60.0f * potionPower, potionPower, 0, potionPower,
                        SkillMastery::Expert, static_cast<uint32_t>(targetMemberIndex));
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 9:
                    party.applyPartyBuff(PartyBuffId::Heroism, 30.0f * 60.0f * potionPower, potionPower, 0, potionPower,
                        SkillMastery::Expert, static_cast<uint32_t>(targetMemberIndex));
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 10:
                    party.applyCharacterBuff(targetMemberIndex, CharacterBuffId::Bless, 30.0f * 60.0f * potionPower,
                        potionPower, 0, potionPower, SkillMastery::Expert, static_cast<uint32_t>(targetMemberIndex));
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 11:
                    party.applyCharacterBuff(targetMemberIndex, CharacterBuffId::Preservation, 30.0f * 60.0f * potionPower,
                        potionPower, 0, potionPower, SkillMastery::Expert, static_cast<uint32_t>(targetMemberIndex));
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 12:
                    party.applyPartyBuff(PartyBuffId::Shield, 30.0f * 60.0f * potionPower, potionPower, 0, potionPower,
                        SkillMastery::Expert, static_cast<uint32_t>(targetMemberIndex));
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 14:
                    party.applyPartyBuff(PartyBuffId::Stoneskin, 30.0f * 60.0f * potionPower, potionPower, 0, potionPower,
                        SkillMastery::Expert, static_cast<uint32_t>(targetMemberIndex));
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 15:
                    party.applyPartyBuff(PartyBuffId::WaterWalk, 30.0f * 60.0f * potionPower, potionPower, 0, potionPower,
                        SkillMastery::Expert, static_cast<uint32_t>(targetMemberIndex));
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 17:
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::Fear);
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 18:
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::Cursed);
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 19:
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::Insane);
                    result.handled = true;
                    result.consumed = true;
                    return result;
                case 31:
                    party.clearMemberCondition(targetMemberIndex, CharacterCondition::Paralyzed);
                    result.handled = true;
                    result.consumed = true;
                    return result;
                default:
                    break;
            }

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
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Eradicated, context.gameMinutes);
                result.soundId = SoundId::Gong;
            }
            else if (dayOfMonth == 12 || dayOfMonth == 26)
            {
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Dead, context.gameMinutes);
                result.soundId = SoundId::Gong;
            }
            else if (dayOfMonth == 4 || dayOfMonth == 25)
            {
                party.applyMemberCondition(targetMemberIndex, CharacterCondition::Petrified, context.gameMinutes);
                result.soundId = SoundId::Gong;
            }

            return result;
        }

        case InventoryItemUseAction::UseDeckOfFate:
        {
            result.handled = true;
            result.consumed = true;
            result.statusText = applyDeckOfFateReward(*pTargetMember, context.gameMinutes);
            return result;
        }

        case InventoryItemUseAction::EatFoodItem:
        {
            party.addFood(1);
            result.handled = true;
            result.consumed = true;
            result.soundId = SoundId::Eat;
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

        case InventoryItemUseAction::UseConnectorStone:
        {
            result.handled = true;
            return result;
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
