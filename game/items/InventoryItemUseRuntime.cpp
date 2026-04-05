#include "game/items/InventoryItemUseRuntime.h"

#include "game/tables/ItemTable.h"
#include "game/party/SpellSchool.h"

#include <algorithm>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
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

    if (item.objectDescriptionId == 656)
    {
        return InventoryItemUseAction::UseHorseshoe;
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
    const ReadableScrollTable *pReadableScrollTable)
{
    InventoryItemUseResult result = {};
    result.action = classifyItemUse(item, itemTable);

    const ItemDefinition *pItemDefinition = itemTable.get(item.objectDescriptionId);
    Character *pTargetMember = party.member(targetMemberIndex);

    if (pItemDefinition == nullptr || pTargetMember == nullptr)
    {
        result.statusText = "Can't use that item";
        return result;
    }

    switch (result.action)
    {
        case InventoryItemUseAction::CastScroll:
        {
            const std::optional<uint32_t> spellId = tryParseSpellId(*pItemDefinition);

            if (!spellId)
            {
                return makeFailure(result.action, "Unknown scroll spell");
            }

            result.handled = true;
            result.consumed = true;
            result.spellId = *spellId;
            result.spellSkillLevelOverride = 5;
            result.spellSkillMasteryOverride = SkillMastery::Master;
            result.statusText = "Cast " + pItemDefinition->name;
            return result;
        }

        case InventoryItemUseAction::LearnSpell:
        {
            const std::optional<uint32_t> spellId = tryParseSpellId(*pItemDefinition);

            if (!spellId)
            {
                return makeFailure(result.action, "Unknown spell book", SpeechId::CantLearnSpell);
            }

            const std::optional<std::string> skillName = resolveMagicSkillName(*spellId);

            if (!skillName)
            {
                return makeFailure(result.action, "Unknown spell school", SpeechId::CantLearnSpell);
            }

            const CharacterSkill *pSkill = pTargetMember->findSkill(*skillName);

            if (pSkill == nullptr || pSkill->mastery == SkillMastery::None || pSkill->level == 0)
            {
                return makeFailure(result.action, "Missing " + displaySkillName(*skillName), SpeechId::CantLearnSpell);
            }

            const SkillMastery requiredMastery = requiredMasteryForSpell(*spellId);

            if (requiredMastery != SkillMastery::None && pSkill->mastery < requiredMastery)
            {
                return makeFailure(
                    result.action,
                    "Requires " + masteryDisplayName(requiredMastery) + " " + displaySkillName(*skillName),
                    SpeechId::CantLearnSpell);
            }

            if (pTargetMember->knowsSpell(*spellId))
            {
                result = makeFailure(result.action, "Spell already learned");
                result.alreadyKnown = true;
                return result;
            }

            pTargetMember->learnSpell(*spellId);
            result.handled = true;
            result.consumed = true;
            result.spellId = *spellId;
            result.statusText = "Learned " + pItemDefinition->name;
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
                result.statusText = "Drank Cure Wounds";
                return result;
            }

            if (item.objectDescriptionId == 223)
            {
                restoreSpellPoints(*pTargetMember, 10);
                result.handled = true;
                result.consumed = true;
                result.statusText = "Drank Magic Potion";
                return result;
            }

            if (item.objectDescriptionId == 252)
            {
                clearAllRestorableConditions(party, targetMemberIndex);
                result.handled = true;
                result.consumed = true;
                result.statusText = "Drank Divine Restoration";
                return result;
            }

            if (item.objectDescriptionId == 253)
            {
                party.healMember(targetMemberIndex, 50);
                result.handled = true;
                result.consumed = true;
                result.statusText = "Drank Divine Cure";
                return result;
            }

            if (item.objectDescriptionId == 254)
            {
                restoreSpellPoints(*pTargetMember, 50);
                result.handled = true;
                result.consumed = true;
                result.statusText = "Drank Divine Power";
                return result;
            }

            if (item.objectDescriptionId == 262)
            {
                party.clearMemberCondition(targetMemberIndex, CharacterCondition::Petrified);
                result.handled = true;
                result.consumed = true;
                result.statusText = "Drank Stone to Flesh";
                return result;
            }

            if (applyPermanentStatPotion(*pTargetMember, item.objectDescriptionId))
            {
                result.handled = true;
                result.consumed = true;
                result.statusText = "Drank " + pItemDefinition->name;
                return result;
            }

            return makeFailure(result.action, "That potion needs another target", SpeechId::PotionFail);
        }

        case InventoryItemUseAction::ReadMessageScroll:
        {
            const ReadableScrollEntry *pEntry =
                pReadableScrollTable != nullptr ? pReadableScrollTable->get(item.objectDescriptionId) : nullptr;

            if (pEntry == nullptr || pEntry->text.empty())
            {
                return makeFailure(result.action, "Nothing to read");
            }

            result.handled = true;
            result.readableTitle = pItemDefinition->name.empty() ? pEntry->itemName : pItemDefinition->name;
            result.readableBody = pEntry->text;
            result.statusText = "Read " + result.readableTitle;
            return result;
        }

        case InventoryItemUseAction::UseHorseshoe:
        {
            pTargetMember->skillPoints += 2;
            result.handled = true;
            result.consumed = true;
            result.statusText = "Gained 2 skill points";
            return result;
        }

        case InventoryItemUseAction::Equip:
        case InventoryItemUseAction::None:
        default:
            result.statusText = "Can't use that item here";
            return result;
    }
}
}
