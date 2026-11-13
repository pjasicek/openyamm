#include "game/items/ItemRuntime.h"
#include "engine/Localization.h"

#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/party/SkillData.h"

#include <algorithm>
#include <limits>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
int masteryMultiplier(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return 1;

        case SkillMastery::Expert:
            return 2;

        case SkillMastery::Master:
            return 3;

        case SkillMastery::Grandmaster:
            return 5;

        case SkillMastery::None:
        default:
            return 0;
    }
}

int identifyRepairSkillScore(const Character &character, const char *pSkillName)
{
    const CharacterSkill *pSkill = character.findSkill(pSkillName);
    const int bonusLevel = character.skillBonus(std::string(pSkillName));

    if ((pSkill == nullptr || pSkill->mastery == SkillMastery::None || pSkill->level == 0) && bonusLevel == 0)
    {
        return 0;
    }

    if (pSkill != nullptr && pSkill->mastery == SkillMastery::Grandmaster)
    {
        return std::numeric_limits<int>::max();
    }

    const int baseLevel = pSkill != nullptr ? static_cast<int>(pSkill->level) : 0;
    const SkillMastery mastery = pSkill != nullptr ? pSkill->mastery : SkillMastery::Normal;
    return (baseLevel + bonusLevel) * masteryMultiplier(mastery);
}

bool hasMeaningfulUnidentifiedName(const ItemDefinition &itemDefinition)
{
    return !itemDefinition.unidentifiedName.empty()
        && itemDefinition.unidentifiedName != "0"
        && itemDefinition.unidentifiedName != "N / A";
}

bool matchesClassOrPromotion(const std::string &characterClassName, const std::string &requiredClassName)
{
    const std::string canonicalCharacterClass = canonicalClassName(characterClassName);
    const std::string canonicalRequiredClass = canonicalClassName(requiredClassName);

    if (canonicalCharacterClass.empty() || canonicalRequiredClass.empty())
    {
        return false;
    }

    if (canonicalCharacterClass == canonicalRequiredClass)
    {
        return true;
    }

    std::vector<std::string> pendingClasses = promotionClassNames(canonicalRequiredClass);

    while (!pendingClasses.empty())
    {
        const std::string className = canonicalClassName(pendingClasses.back());
        pendingClasses.pop_back();

        if (className == canonicalCharacterClass)
        {
            return true;
        }

        const std::vector<std::string> nextPromotions = promotionClassNames(className);
        pendingClasses.insert(pendingClasses.end(), nextPromotions.begin(), nextPromotions.end());
    }

    return false;
}

const std::string &characterClassName(const Character &character)
{
    return character.className.empty() ? character.role : character.className;
}
}

bool ItemRuntime::requiresIdentification(const ItemDefinition &itemDefinition)
{
    return identifyRepairDifficulty(itemDefinition) > 0
        && hasMeaningfulUnidentifiedName(itemDefinition)
        && itemDefinition.unidentifiedName != itemDefinition.name;
}

int ItemRuntime::identifyRepairDifficulty(const ItemDefinition &itemDefinition)
{
    return std::max(0, itemDefinition.identifyRepairDifficulty);
}

bool ItemRuntime::isRareItem(const ItemDefinition &itemDefinition)
{
    return itemDefinition.rarity != ItemRarity::Common;
}

bool ItemRuntime::isUniquelyGeneratedRareItem(const ItemDefinition &itemDefinition)
{
    return isArtifact(itemDefinition) && itemDefinition.value > 0;
}

bool ItemRuntime::isArtifact(const ItemDefinition &itemDefinition)
{
    return itemDefinition.rarity == ItemRarity::Artifact || itemDefinition.rarity == ItemRarity::Relic;
}

bool ItemRuntime::isHardened(bool hardenedFlag, const ItemDefinition &itemDefinition)
{
    return hardenedFlag || isArtifact(itemDefinition);
}

std::optional<std::string> ItemRuntime::classRestriction(const ItemDefinition &itemDefinition)
{
    if (!itemDefinition.allowedClassRoots.empty())
    {
        return itemDefinition.allowedClassRoots.front();
    }

    switch (itemDefinition.itemId)
    {
        case 515:
            return "Knight";

        case 516:
            return "Cleric";

        case 521:
            return "Lich";

        case 529:
            return "Necromancer";

        default:
            return std::nullopt;
    }
}

std::optional<std::string> ItemRuntime::raceRestriction(const ItemDefinition &itemDefinition)
{
    switch (itemDefinition.itemId)
    {
        case 504:
            return "Minotaur";

        case 508:
            return "Vampire";

        case 514:
            return "DarkElf";

        case 532:
            return "DarkElfOrElf";

        case 1333:
            return "Goblin";

        case 1334:
            return "Human";

        case 1335:
            return "DarkElfOrElf";

        case 1336:
            return "Dwarf";

        case 1337:
            return "Male";

        case 1338:
            return "Female";

        default:
            return std::nullopt;
    }
}

std::optional<std::string> ItemRuntime::wearRequirementText(const ItemDefinition &itemDefinition)
{
    if (!itemDefinition.allowedClassRoots.empty())
    {
        std::string classes;

        for (const std::string &classRoot : itemDefinition.allowedClassRoots)
        {
            classes += (classes.empty() ? "" : ", ") + Engine::localize(displayClassName(classRoot), "class");
        }

        return Engine::tr("{classes} only", {{"classes", classes}});
    }

    // MAW's artifactWearReq texts for MMMerge's gated artifacts.
    static const std::unordered_map<std::string, std::string_view> Texts = {
        {"Knight", Engine::trNoop("Knights only")},
        {"Cleric", Engine::trNoop("Clerics only")},
        {"Lich", Engine::trNoop("Liches only")},
        {"Necromancer", Engine::trNoop("Necromancers and Liches only")},
        {"Minotaur", Engine::trNoop("Minotaurs only")},
        {"Vampire", Engine::trNoop("Vampires only")},
        {"DarkElf", Engine::trNoop("Dark Elves only")},
        {"DarkElfOrElf", Engine::trNoop("Elves only")},
        {"Goblin", Engine::trNoop("Goblins only")},
        {"Human", Engine::trNoop("Humans only")},
        {"Dwarf", Engine::trNoop("Dwarves only")},
        {"Male", Engine::trNoop("Men only")},
        {"Female", Engine::trNoop("Women only")},
    };
    std::optional<std::string> restriction = classRestriction(itemDefinition);

    if (!restriction)
    {
        restriction = raceRestriction(itemDefinition);
    }

    if (!restriction)
    {
        return std::nullopt;
    }

    const std::unordered_map<std::string, std::string_view>::const_iterator textIt = Texts.find(*restriction);
    return textIt != Texts.end()
        ? Engine::tr(textIt->second)
        : Engine::tr("{classes} only", {{"classes", Engine::localize(*restriction, "class")}});
}

bool ItemRuntime::characterMeetsClassRestriction(const Character &character, const ItemDefinition &itemDefinition)
{
    if (!itemDefinition.allowedClassRoots.empty())
    {
        const bool matchesAllowedClass = std::any_of(
            itemDefinition.allowedClassRoots.begin(),
            itemDefinition.allowedClassRoots.end(),
            [&character](const std::string &classRoot)
            {
                return matchesClassOrPromotion(characterClassName(character), classRoot);
            });

        if (!matchesAllowedClass)
        {
            return false;
        }
    }

    const int actualMight = static_cast<int>(character.might)
        + character.permanentBonuses.might + character.magicalBonuses.might;
    const int actualAccuracy = static_cast<int>(character.accuracy)
        + character.permanentBonuses.accuracy + character.magicalBonuses.accuracy;

    // Only items with a requirement check it: a negative stat (Lightning Crossbow's Accuracy -50) must not lock out
    // every item that has none.
    if ((itemDefinition.requiredMight > 0 && actualMight < itemDefinition.requiredMight)
        || (itemDefinition.requiredAccuracy > 0 && actualAccuracy < itemDefinition.requiredAccuracy))
    {
        return false;
    }

    const std::optional<std::string> restriction = classRestriction(itemDefinition);
    return !restriction || !itemDefinition.allowedClassRoots.empty()
        || matchesClassOrPromotion(characterClassName(character), *restriction);
}

bool ItemRuntime::characterMeetsRaceRestriction(const Character &character, const ItemDefinition &itemDefinition)
{
    switch (itemDefinition.itemId)
    {
        case 504:
            return character.raceId == 3;

        case 508:
            return character.raceId == 1;

        case 514:
            return character.raceId == 2;

        case 532:
        case 1335:
            return character.raceId == 2 || character.raceId == 7;

        case 1333:
            return character.raceId == 8;

        case 1334:
            return character.raceId == 0;

        case 1336:
            return character.raceId == 9;

        case 1337:
            return character.sexId == 0;

        case 1338:
            return character.sexId == 1;

        default:
            return true;
    }
}

bool ItemRuntime::canCharacterIdentifyItem(const Character &character, const ItemDefinition &itemDefinition)
{
    if (!requiresIdentification(itemDefinition))
    {
        return true;
    }

    return identifyRepairSkillScore(character, "IdentifyItem") >= identifyRepairDifficulty(itemDefinition);
}

bool ItemRuntime::canCharacterRepairItem(const Character &character, const ItemDefinition &itemDefinition)
{
    return identifyRepairSkillScore(character, "RepairItem") >= identifyRepairDifficulty(itemDefinition);
}

bool ItemRuntime::canDrop(const ItemDefinition &itemDefinition)
{
    return !itemDefinition.hasContentFlag("NoDrop");
}

std::string ItemRuntime::foundItemName(const ItemDefinition &itemDefinition)
{
    if (hasMeaningfulUnidentifiedName(itemDefinition))
    {
        return Engine::localize(itemDefinition.unidentifiedName);
    }

    return !itemDefinition.name.empty() ? Engine::localize(itemDefinition.name) : Engine::tr("item");
}

std::string ItemRuntime::displayName(const InventoryItem &item, const ItemDefinition &itemDefinition)
{
    return displayName(item, itemDefinition, nullptr, nullptr);
}

std::string ItemRuntime::displayName(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    // An item that needs no identifying (Zokarr's Axe: OY-362) is named as identified, as its tooltip already is.
    if (!item.identified && requiresIdentification(itemDefinition))
    {
        return Engine::localize(itemDefinition.unidentifiedName);
    }

    return boundGameRules().items.displayName(item, itemDefinition, pStandardEnchantTable, pSpecialEnchantTable);
}

std::string ItemRuntime::identifiedDisplayName(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    // A Special item keeps its own name with its fixed enchantment (Noblebone Bow, not "Noblebone Bow of Carnage"),
    // as MM7 names its special items.
    if ((item.standardEnchantId != 0 || item.specialEnchantId != 0) && itemDefinition.rarity != ItemRarity::Special)
    {
        return ItemEnchantRuntime::displayName(item, itemDefinition, pStandardEnchantTable, pSpecialEnchantTable);
    }

    if (!itemDefinition.name.empty())
    {
        return Engine::localize(itemDefinition.name);
    }

    if (hasMeaningfulUnidentifiedName(itemDefinition))
    {
        return Engine::localize(itemDefinition.unidentifiedName);
    }

    return Engine::tr("Unknown item");
}
}
