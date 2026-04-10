#include "game/party/SkillData.h"

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
    {"Bodybuilding", "Body Building"},
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

std::vector<std::string> promotionClassNames(const std::string &className)
{
    const std::string canonicalName = canonicalClassName(className);

    if (canonicalName == "Archer")
    {
        return {"MasterArcher"};
    }

    if (canonicalName == "MasterArcher")
    {
        return {"Sniper"};
    }

    if (canonicalName == "Cleric")
    {
        return {"Priest"};
    }

    if (canonicalName == "Priest")
    {
        return {"PriestLight", "PriestDark"};
    }

    if (canonicalName == "DarkElf")
    {
        return {"Patriarch"};
    }

    if (canonicalName == "Dragon")
    {
        return {"GreatWyrm"};
    }

    if (canonicalName == "Druid")
    {
        return {"GreatDruid"};
    }

    if (canonicalName == "GreatDruid")
    {
        return {"Warlock", "ArchDruid"};
    }

    if (canonicalName == "Knight")
    {
        return {"Champion"};
    }

    if (canonicalName == "Champion")
    {
        return {"Cavalier", "BlackKnight"};
    }

    if (canonicalName == "Minotaur")
    {
        return {"MinotaurLord"};
    }

    if (canonicalName == "Monk")
    {
        return {"Initiate"};
    }

    if (canonicalName == "Initiate")
    {
        return {"Master", "Ninja"};
    }

    if (canonicalName == "Paladin")
    {
        return {"Crusader"};
    }

    if (canonicalName == "Crusader")
    {
        return {"Hero", "Villain"};
    }

    if (canonicalName == "Ranger")
    {
        return {"Hunter"};
    }

    if (canonicalName == "Hunter")
    {
        return {"BountyHunter", "RangerLord"};
    }

    if (canonicalName == "Thief")
    {
        return {"Rogue"};
    }

    if (canonicalName == "Rogue")
    {
        return {"Assassin", "Spy"};
    }

    if (canonicalName == "Troll")
    {
        return {"WarTroll"};
    }

    if (canonicalName == "Vampire")
    {
        return {"Nosferatu"};
    }

    if (canonicalName == "Sorcerer")
    {
        return {"Wizard"};
    }

    if (canonicalName == "Wizard")
    {
        return {"ArchMage"};
    }

    if (canonicalName == "Necromancer")
    {
        return {"Lich"};
    }

    return {};
}

std::optional<uint32_t> mm8ClassIdForClassName(const std::string &className)
{
    const std::string canonicalName = canonicalClassName(className);

    if (canonicalName == "Necromancer")
    {
        return 0;
    }

    if (canonicalName == "Lich")
    {
        return 1;
    }

    if (canonicalName == "Cleric")
    {
        return 2;
    }

    if (canonicalName == "Priest")
    {
        return 3;
    }

    if (canonicalName == "Knight")
    {
        return 4;
    }

    if (canonicalName == "Champion")
    {
        return 5;
    }

    if (canonicalName == "Troll")
    {
        return 6;
    }

    if (canonicalName == "WarTroll")
    {
        return 7;
    }

    if (canonicalName == "Minotaur")
    {
        return 8;
    }

    if (canonicalName == "MinotaurLord")
    {
        return 9;
    }

    if (canonicalName == "DarkElf")
    {
        return 10;
    }

    if (canonicalName == "Patriarch")
    {
        return 11;
    }

    if (canonicalName == "Vampire")
    {
        return 12;
    }

    if (canonicalName == "Nosferatu")
    {
        return 13;
    }

    if (canonicalName == "Dragon")
    {
        return 14;
    }

    if (canonicalName == "GreatWyrm")
    {
        return 15;
    }

    return std::nullopt;
}

std::optional<std::string> classNameForMm8ClassId(uint32_t classId)
{
    switch (classId)
    {
        case 0: return "Necromancer";
        case 1: return "Lich";
        case 2: return "Cleric";
        case 3: return "Priest";
        case 4: return "Knight";
        case 5: return "Champion";
        case 6: return "Troll";
        case 7: return "WarTroll";
        case 8: return "Minotaur";
        case 9: return "MinotaurLord";
        case 10: return "DarkElf";
        case 11: return "Patriarch";
        case 12: return "Vampire";
        case 13: return "Nosferatu";
        case 14: return "Dragon";
        case 15: return "GreatWyrm";
        default: break;
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
