#include "game/SkillData.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
std::string trimCopy(const std::string &value)
{
    size_t start = 0;

    while (start < value.size() && std::isspace(static_cast<unsigned char>(value[start])))
    {
        ++start;
    }

    size_t end = value.size();

    while (end > start && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(start, end - start);
}

std::string canonicalLookupKey(const std::string &value)
{
    const std::string trimmed = trimCopy(value);
    std::string result;

    for (unsigned char character : trimmed)
    {
        if (std::isalnum(character))
        {
            result.push_back(static_cast<char>(std::tolower(character)));
        }
    }

    return result;
}

const std::array<std::string, 50> CanonicalClassNames = {
    "Archer",
    "WarriorMage",
    "MasterArcher",
    "Sniper",
    "Cleric",
    "Priest",
    "PriestLight",
    "PriestDark",
    "DarkElf",
    "Patriarch",
    "Dragon",
    "GreatWyrm",
    "Druid",
    "GreatDruid",
    "Warlock",
    "ArchDruid",
    "Knight",
    "Cavalier",
    "BlackKnight",
    "Champion",
    "Minotaur",
    "MinotaurLord",
    "Monk",
    "Initiate",
    "Master",
    "Ninja",
    "Paladin",
    "Crusader",
    "Hero",
    "Villain",
    "Ranger",
    "Hunter",
    "BountyHunter",
    "RangerLord",
    "Thief",
    "Rogue",
    "Assassin",
    "Spy",
    "Troll",
    "WarTroll",
    "Vampire",
    "Nosferatu",
    "Sorcerer",
    "Wizard",
    "Necromancer",
    "Lich",
    "ArchMage",
    "Peasant",
    "n/u",
    "None",
};

const std::array<std::string, 39> CanonicalSkillNames = {
    "Staff",
    "Sword",
    "Dagger",
    "Axe",
    "Spear",
    "Bow",
    "Mace",
    "Blaster",
    "Shield",
    "LeatherArmor",
    "ChainArmor",
    "PlateArmor",
    "FireMagic",
    "AirMagic",
    "WaterMagic",
    "EarthMagic",
    "SpiritMagic",
    "MindMagic",
    "BodyMagic",
    "LightMagic",
    "DarkMagic",
    "DarkElfAbility",
    "VampireAbility",
    "DragonAbility",
    "IdentifyItem",
    "Merchant",
    "RepairItem",
    "Bodybuilding",
    "Meditation",
    "Perception",
    "Regeneration",
    "DisarmTraps",
    "Dodging",
    "Unarmed",
    "IdentifyMonster",
    "Armsmaster",
    "Stealing",
    "Alchemy",
    "Learning",
};

const std::unordered_map<std::string, std::string> ClassAliases = {
    {"cleric2", "Priest"},
    {"darkelf2", "Patriarch"},
    {"dragon2", "GreatWyrm"},
    {"knight2", "Champion"},
    {"minotaur2", "MinotaurLord"},
    {"troll2", "WarTroll"},
    {"vampire2", "Nosferatu"},
    {"necromancer2", "Lich"},
};

const std::unordered_map<std::string, std::string> SkillAliases = {
    {"leather", "LeatherArmor"},
    {"chain", "ChainArmor"},
    {"plate", "PlateArmor"},
    {"fire", "FireMagic"},
    {"air", "AirMagic"},
    {"water", "WaterMagic"},
    {"earth", "EarthMagic"},
    {"spirit", "SpiritMagic"},
    {"mind", "MindMagic"},
    {"body", "BodyMagic"},
    {"light", "LightMagic"},
    {"dark", "DarkMagic"},
    {"darkelf", "DarkElfAbility"},
    {"vampire", "VampireAbility"},
    {"dragon", "DragonAbility"},
    {"iditem", "IdentifyItem"},
    {"identifyitem", "IdentifyItem"},
    {"repair", "RepairItem"},
    {"repairitem", "RepairItem"},
    {"bbuilding", "Bodybuilding"},
    {"bodybuilding", "Bodybuilding"},
    {"meditate", "Meditation"},
    {"meditation", "Meditation"},
    {"disarmtrap", "DisarmTraps"},
    {"disarmtraps", "DisarmTraps"},
    {"identmon", "IdentifyMonster"},
    {"identifymonster", "IdentifyMonster"},
    {"lightmagic", "LightMagic"},
    {"darkmagic", "DarkMagic"},
};

const std::unordered_map<std::string, std::string> DisplayClassNames = {
    {"WarriorMage", "Warrior Mage"},
    {"MasterArcher", "Master Archer"},
    {"PriestLight", "Priest Light"},
    {"PriestDark", "Priest Dark"},
    {"DarkElf", "Dark Elf"},
    {"GreatWyrm", "Great Wyrm"},
    {"GreatDruid", "Great Druid"},
    {"ArchDruid", "Arch Druid"},
    {"BlackKnight", "Black Knight"},
    {"MinotaurLord", "Minotaur Lord"},
    {"BountyHunter", "Bounty Hunter"},
    {"RangerLord", "Ranger Lord"},
    {"WarTroll", "War Troll"},
    {"ArchMage", "Arch Mage"},
};

const std::unordered_map<std::string, std::string> DisplaySkillNames = {
    {"LeatherArmor", "Leather Armor"},
    {"ChainArmor", "Chain Armor"},
    {"PlateArmor", "Plate Armor"},
    {"FireMagic", "Fire Magic"},
    {"AirMagic", "Air Magic"},
    {"WaterMagic", "Water Magic"},
    {"EarthMagic", "Earth Magic"},
    {"SpiritMagic", "Spirit Magic"},
    {"MindMagic", "Mind Magic"},
    {"BodyMagic", "Body Magic"},
    {"LightMagic", "Light Magic"},
    {"DarkMagic", "Dark Magic"},
    {"DarkElfAbility", "Dark Elf Ability"},
    {"VampireAbility", "Vampire Ability"},
    {"DragonAbility", "Dragon Ability"},
    {"IdentifyItem", "Identify Item"},
    {"RepairItem", "Repair Item"},
    {"IdentifyMonster", "Identify Monster"},
    {"DisarmTraps", "Disarm Traps"},
};
}

std::string canonicalClassName(const std::string &name)
{
    const std::string lookupKey = canonicalLookupKey(name);

    if (lookupKey.empty())
    {
        return {};
    }

    const std::unordered_map<std::string, std::string>::const_iterator aliasIt = ClassAliases.find(lookupKey);

    if (aliasIt != ClassAliases.end())
    {
        return aliasIt->second;
    }

    for (const std::string &candidate : CanonicalClassNames)
    {
        if (canonicalLookupKey(candidate) == lookupKey)
        {
            return candidate;
        }
    }

    return trimCopy(name);
}

std::string canonicalSkillName(const std::string &name)
{
    const std::string lookupKey = canonicalLookupKey(name);

    if (lookupKey.empty())
    {
        return {};
    }

    const std::unordered_map<std::string, std::string>::const_iterator aliasIt = SkillAliases.find(lookupKey);

    if (aliasIt != SkillAliases.end())
    {
        return aliasIt->second;
    }

    for (const std::string &candidate : CanonicalSkillNames)
    {
        if (canonicalLookupKey(candidate) == lookupKey)
        {
            return candidate;
        }
    }

    return trimCopy(name);
}

std::string displayClassName(const std::string &className)
{
    const std::string canonicalName = canonicalClassName(className);
    const std::unordered_map<std::string, std::string>::const_iterator displayIt =
        DisplayClassNames.find(canonicalName);

    if (displayIt != DisplayClassNames.end())
    {
        return displayIt->second;
    }

    return canonicalName;
}

std::string displaySkillName(const std::string &skillName)
{
    const std::string canonicalName = canonicalSkillName(skillName);
    const std::unordered_map<std::string, std::string>::const_iterator displayIt =
        DisplaySkillNames.find(canonicalName);

    if (displayIt != DisplaySkillNames.end())
    {
        return displayIt->second;
    }

    return canonicalName;
}

std::string masteryDisplayName(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return "Normal";
        case SkillMastery::Expert:
            return "Expert";
        case SkillMastery::Master:
            return "Master";
        case SkillMastery::Grandmaster:
            return "Grandmaster";
        default:
            return "None";
    }
}

std::optional<std::string> nextPromotionClassName(const std::string &className)
{
    const std::string canonicalName = canonicalClassName(className);

    if (canonicalName == "Cleric")
    {
        return "Priest";
    }

    if (canonicalName == "DarkElf")
    {
        return "Patriarch";
    }

    if (canonicalName == "Dragon")
    {
        return "GreatWyrm";
    }

    if (canonicalName == "Knight")
    {
        return "Champion";
    }

    if (canonicalName == "Minotaur")
    {
        return "MinotaurLord";
    }

    if (canonicalName == "Troll")
    {
        return "WarTroll";
    }

    if (canonicalName == "Vampire")
    {
        return "Nosferatu";
    }

    if (canonicalName == "Necromancer")
    {
        return "Lich";
    }

    return std::nullopt;
}

SkillMastery parseSkillMasteryToken(const std::string &token)
{
    const std::string trimmed = trimCopy(token);

    if (trimmed == "B")
    {
        return SkillMastery::Normal;
    }

    if (trimmed == "E")
    {
        return SkillMastery::Expert;
    }

    if (trimmed == "M")
    {
        return SkillMastery::Master;
    }

    if (trimmed == "G")
    {
        return SkillMastery::Grandmaster;
    }

    return SkillMastery::None;
}

StartingSkillAvailability parseStartingSkillAvailabilityToken(const std::string &token)
{
    const std::string trimmed = trimCopy(token);

    if (trimmed == "C")
    {
        return StartingSkillAvailability::CanLearn;
    }

    if (trimmed == "F")
    {
        return StartingSkillAvailability::HasByDefault;
    }

    return StartingSkillAvailability::None;
}
}
