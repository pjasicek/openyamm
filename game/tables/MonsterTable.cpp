#include "game/tables/MonsterTable.h"
#include "game/BinaryReader.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <cctype>
#include <regex>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t MonsterRecordSize = 184;

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string relationFactionKey(const std::string &label)
{
    std::vector<std::string> tokens;
    std::string currentToken;

    for (unsigned char character : label)
    {
        if (std::isalpha(character))
        {
            currentToken.push_back(static_cast<char>(std::tolower(character)));
        }
        else if (!currentToken.empty())
        {
            tokens.push_back(currentToken);
            currentToken.clear();
        }
    }

    if (!currentToken.empty())
    {
        tokens.push_back(currentToken);
    }

    for (const std::string &token : tokens)
    {
        if (token == "wimpy")
        {
            continue;
        }

        return token;
    }

    return {};
}

bool hasMonsterAbilityDescriptor(const std::string &value)
{
    return !value.empty() && value != "0";
}

bool isSupportedMonsterMissileToken(const std::string &value)
{
    const std::string token = toLowerCopy(trimCopy(value));

    return token == "arrow"
        || token == "arrowf"
        || token == "firear"
        || token == "air"
        || token == "earth"
        || token == "fire"
        || token == "water"
        || token == "body"
        || token == "mind"
        || token == "spirit"
        || token == "light"
        || token == "dark"
        || token == "ener"
        || token == "rock";
}

bool isNumericString(const std::string &value);

MonsterTable::MonsterStatsEntry::DamageProfile parseDamageProfile(const std::string &value)
{
    MonsterTable::MonsterStatsEntry::DamageProfile profile = {};
    static const std::regex damagePattern(R"(^\s*(\d+)\s*[dD]\s*(\d+)\s*(?:([+-])\s*(\d+))?\s*$)");
    static const std::regex flatDamagePattern(R"(^\s*(\d+)\s*$)");
    std::smatch match;

    if (std::regex_match(value, match, flatDamagePattern))
    {
        profile.diceRolls = std::stoi(match[1].str());
        profile.diceSides = 1;
        return profile;
    }

    if (std::regex_match(value, match, damagePattern))
    {
        profile.diceRolls = std::stoi(match[1].str());
        profile.diceSides = std::stoi(match[2].str());

        if (match[4].matched)
        {
            profile.bonus = std::stoi(match[4].str());

            if (match[3].matched && match[3].str() == "-")
            {
                profile.bonus = -profile.bonus;
            }
        }
    }

    return profile;
}

int parseMonsterResistanceValue(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    if (isNumericString(value))
    {
        return std::stoi(value);
    }

    const std::string normalized = toLowerCopy(value);

    if (normalized == "imm" || normalized == "immune")
    {
        return 200;
    }

    return 0;
}

MonsterTable::MonsterAttackStyle classifyAttackStyle(const MonsterTable::MonsterStatsEntry &entry)
{
    if (entry.attack1HasMissile)
    {
        return MonsterTable::MonsterAttackStyle::Ranged;
    }

    if ((entry.attack2HasMissile && entry.attack2Chance > 0)
        || (entry.hasSpell1 && entry.spell1UseChance > 0)
        || (entry.hasSpell2 && entry.spell2UseChance > 0))
    {
        return MonsterTable::MonsterAttackStyle::MixedMeleeRanged;
    }

    return MonsterTable::MonsterAttackStyle::MeleeOnly;
}

std::string parseMonsterSpellName(const std::string &value)
{
    if (!hasMonsterAbilityDescriptor(value))
    {
        return {};
    }

    const size_t commaIndex = value.find(',');
    const std::string spellName = commaIndex == std::string::npos ? value : value.substr(0, commaIndex);
    return toLowerCopy(spellName);
}

std::vector<std::string> parseMonsterSpellDescriptorTokens(const std::string &value)
{
    std::vector<std::string> tokens;
    size_t tokenBegin = 0;

    while (tokenBegin <= value.size())
    {
        const size_t tokenEnd = value.find(',', tokenBegin);
        tokens.push_back(trimCopy(value.substr(
            tokenBegin,
            tokenEnd == std::string::npos ? std::string::npos : tokenEnd - tokenBegin)));

        if (tokenEnd == std::string::npos)
        {
            break;
        }

        tokenBegin = tokenEnd + 1;
    }

    return tokens;
}

uint32_t parseMonsterSpellSkillLevel(const std::string &value)
{
    const std::vector<std::string> tokens = parseMonsterSpellDescriptorTokens(value);

    if (tokens.size() < 3 || tokens[2].empty())
    {
        return 0;
    }

    for (unsigned char character : tokens[2])
    {
        if (std::isdigit(character) == 0)
        {
            return 0;
        }
    }

    return static_cast<uint32_t>(std::stoul(tokens[2]));
}

SkillMastery parseMonsterSpellSkillMastery(const std::string &value)
{
    const std::vector<std::string> tokens = parseMonsterSpellDescriptorTokens(value);

    if (tokens.size() < 2)
    {
        return SkillMastery::None;
    }

    return parseSkillMasteryToken(tokens[1]);
}

struct MonsterSpecialAttackParseResult
{
    MonsterSpecialAttackKind kind = MonsterSpecialAttackKind::None;
    int level = 0;
};

MonsterSpecialAttackParseResult parseMonsterSpecialAttack(const std::string &value)
{
    MonsterSpecialAttackParseResult result = {};
    std::string token = toLowerCopy(trimCopy(value));

    if (token.empty() || token == "0" || token == "none")
    {
        return result;
    }

    token.erase(
        std::remove_if(
            token.begin(),
            token.end(),
            [](unsigned char character)
            {
                return std::isspace(character) != 0 || character == '_' || character == '-' || character == '"';
            }),
        token.end());

    result.level = 1;
    const size_t multiplierIndex = token.rfind('x');

    if (multiplierIndex != std::string::npos && multiplierIndex + 1 < token.size())
    {
        const std::string multiplierText = token.substr(multiplierIndex + 1);

        if (isNumericString(multiplierText))
        {
            result.level = std::max(1, std::stoi(multiplierText));
            token = token.substr(0, multiplierIndex);
        }
    }

    if (token.rfind("curse", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Curse;
    }
    else if (token.rfind("weak", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Weak;
    }
    else if (token.rfind("asleep", 0) == 0 || token.rfind("sleep", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Sleep;
    }
    else if (token.rfind("afraid", 0) == 0 || token.rfind("fear", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Fear;
    }
    else if (token.rfind("drunk", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Drunk;
    }
    else if (token.rfind("insane", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Insane;
    }
    else if (token.rfind("poisonweak", 0) == 0 || token.rfind("poison1", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::PoisonWeak;
    }
    else if (token.rfind("poisonmedium", 0) == 0 || token.rfind("poison2", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::PoisonMedium;
    }
    else if (token.rfind("poisonsevere", 0) == 0 || token.rfind("poison3", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::PoisonSevere;
    }
    else if (token.rfind("diseaseweak", 0) == 0 || token.rfind("disease1", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::DiseaseWeak;
    }
    else if (token.rfind("diseasemedium", 0) == 0 || token.rfind("disease2", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::DiseaseMedium;
    }
    else if (token.rfind("diseasesevere", 0) == 0 || token.rfind("disease3", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::DiseaseSevere;
    }
    else if (token.rfind("paralyze", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Paralyze;
    }
    else if (token.rfind("uncon", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Unconscious;
    }
    else if (token.rfind("dead", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Dead;
    }
    else if (token.rfind("stone", 0) == 0 || token.rfind("petrify", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Petrify;
    }
    else if (token.rfind("erad", 0) == 0 || token.rfind("errad", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Eradicate;
    }
    else if (token.rfind("brkitem", 0) == 0 || token.rfind("breakitem", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::BreakAny;
    }
    else if (token.rfind("brkarmor", 0) == 0 || token.rfind("breakarmor", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::BreakArmor;
    }
    else if (token.rfind("brkweapon", 0) == 0 || token.rfind("breakweapon", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::BreakWeapon;
    }
    else if (token.rfind("age", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::Aging;
    }
    else if (token.rfind("drainsp", 0) == 0 || token.rfind("manadrain", 0) == 0)
    {
        result.kind = MonsterSpecialAttackKind::ManaDrain;
    }

    if (result.kind == MonsterSpecialAttackKind::None)
    {
        result.level = 0;
    }

    return result;
}

bool isNumericString(const std::string &value)
{
    if (value.empty())
    {
        return false;
    }

    for (char character : value)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return false;
        }
    }

    return true;
}

uint32_t parseUnsignedIntegerValue(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return 0;
    }

    return static_cast<uint32_t>(std::stoul(trimmed, nullptr, 0));
}

MonsterTable::MonsterMovementType parseMovementType(const std::string &value)
{
    const std::string lower = toLowerCopy(value);

    if (lower == "med")
    {
        return MonsterTable::MonsterMovementType::Medium;
    }

    if (lower == "long")
    {
        return MonsterTable::MonsterMovementType::Long;
    }

    if (lower == "global")
    {
        return MonsterTable::MonsterMovementType::Global;
    }

    if (lower == "free")
    {
        return MonsterTable::MonsterMovementType::Free;
    }

    if (lower == "stationary")
    {
        return MonsterTable::MonsterMovementType::Stationary;
    }

    return MonsterTable::MonsterMovementType::Short;
}

MonsterTable::MonsterAiType parseAiType(const std::string &value)
{
    const std::string lower = toLowerCopy(value);

    if (lower == "wimp")
    {
        return MonsterTable::MonsterAiType::Wimp;
    }

    if (lower == "normal")
    {
        return MonsterTable::MonsterAiType::Normal;
    }

    if (lower == "aggress")
    {
        return MonsterTable::MonsterAiType::Aggressive;
    }

    return MonsterTable::MonsterAiType::Suicide;
}

MonsterTable::LootPrototype parseLootPrototype(const std::string &value)
{
    MonsterTable::LootPrototype loot = {};
    std::string lower = toLowerCopy(value);

    if (lower.empty() || lower == "0")
    {
        return loot;
    }

    const std::smatch diceMatch = [&]() -> std::smatch
    {
        std::smatch match;
        std::regex_search(lower, match, std::regex("([0-9]+)d([0-9]+)"));
        return match;
    }();

    if (!diceMatch.empty())
    {
        loot.goldDiceRolls = std::stoi(diceMatch[1].str());
        loot.goldDiceSides = std::stoi(diceMatch[2].str());
    }

    const size_t percentIndex = lower.find('%');

    if (percentIndex != std::string::npos && percentIndex > 0)
    {
        loot.itemChance = std::stoi(lower.substr(0, percentIndex));
    }
    else if (lower.find('l') != std::string::npos)
    {
        loot.itemChance = 100;
    }

    const size_t levelIndex = lower.find('l');

    if (levelIndex != std::string::npos && levelIndex + 1 < lower.size() && std::isdigit(lower[levelIndex + 1]) != 0)
    {
        loot.itemLevel = lower[levelIndex + 1] - '0';
        loot.itemKind = MonsterTable::LootItemKind::Any;
        const std::string itemToken = lower.substr(levelIndex + 2);

        if (itemToken.find("gem") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Gem;
        }
        else if (itemToken.find("weapon") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Weapon;
        }
        else if (itemToken.find("armor") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Armor;
        }
        else if (itemToken.find("misc") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Misc;
        }
        else if (itemToken.find("ring") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Ring;
        }
        else if (itemToken.find("amulet") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Amulet;
        }
        else if (itemToken.find("boots") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Boots;
        }
        else if (itemToken.find("gloves") != std::string::npos || itemToken.find("gauntlets") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Gauntlets;
        }
        else if (itemToken.find("cloak") != std::string::npos || itemToken.find("cape") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Cloak;
        }
        else if (itemToken.find("wand") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Wand;
        }
        else if (itemToken.find("ore") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Ore;
        }
        else if (itemToken.find("scroll") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Scroll;
        }
        else if (itemToken.find("sword") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Sword;
        }
        else if (itemToken.find("dagger") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Dagger;
        }
        else if (itemToken.find("axe") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Axe;
        }
        else if (itemToken.find("spear") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Spear;
        }
        else if (itemToken.find("chain") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Chain;
        }
        else if (itemToken.find("leather") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Leather;
        }
        else if (itemToken.find("plate") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Plate;
        }
        else if (itemToken.find("mace") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Mace;
        }
        else if (itemToken.find("club") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Club;
        }
        else if (itemToken.find("staff") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Staff;
        }
        else if (itemToken.find("bow") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Bow;
        }
        else if (itemToken.find("shield") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Shield;
        }
        else if (itemToken.find("helm") != std::string::npos || itemToken.find("helmet") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Helm;
        }
        else if (itemToken.find("belt") != std::string::npos)
        {
            loot.itemKind = MonsterTable::LootItemKind::Belt;
        }
    }

    return loot;
}
}

bool MonsterTable::loadFromBytes(const std::vector<uint8_t> &bytes)
{
    const ByteReader reader(bytes);
    uint32_t entryCount = 0;

    if (!reader.readUInt32(0, entryCount))
    {
        return false;
    }

    const size_t expectedSize = sizeof(uint32_t) + static_cast<size_t>(entryCount) * MonsterRecordSize;

    if (!reader.canRead(0, expectedSize))
    {
        return false;
    }

    m_entries.clear();
    m_entries.resize(static_cast<size_t>(entryCount) + 1);

    for (uint32_t index = 0; index < entryCount; ++index)
    {
        const size_t offset = sizeof(uint32_t) + static_cast<size_t>(index) * MonsterRecordSize;
        MonsterEntry entry = {};

        if (!reader.readUInt16(offset + 0x00, entry.height)
            || !reader.readUInt16(offset + 0x02, entry.radius)
            || !reader.readUInt16(offset + 0x04, entry.movementSpeed)
            || !reader.readInt16(offset + 0x06, entry.toHitRadius)
            || !reader.readUInt32(offset + 0x08, entry.tintColor)
            || !reader.readUInt16(offset + 0x0c, entry.soundSampleIds[0])
            || !reader.readUInt16(offset + 0x0e, entry.soundSampleIds[1])
            || !reader.readUInt16(offset + 0x10, entry.soundSampleIds[2])
            || !reader.readUInt16(offset + 0x12, entry.soundSampleIds[3]))
        {
            return false;
        }

        entry.internalName = reader.readFixedString(offset + 0x14, 32);

        for (size_t spriteIndex = 0; spriteIndex < entry.spriteNames.size(); ++spriteIndex)
        {
            entry.spriteNames[spriteIndex] = reader.readFixedString(offset + 0x54 + spriteIndex * 10, 10);
        }

        const size_t monsterId = static_cast<size_t>(index) + 1;
        m_entries[monsterId] = std::move(entry);
    }

    return !m_entries.empty();
}

bool MonsterTable::loadEntriesFromRows(const std::vector<std::vector<std::string>> &rows)
{
    static constexpr size_t ColumnId = 0;
    static constexpr size_t ColumnInternalName = 1;
    static constexpr size_t ColumnHeight = 2;
    static constexpr size_t ColumnRadius = 3;
    static constexpr size_t ColumnMovementSpeed = 4;
    static constexpr size_t ColumnToHitRadius = 5;
    static constexpr size_t ColumnTintColor = 6;
    static constexpr size_t ColumnAttackSoundId = 7;
    static constexpr size_t ColumnDeathSoundId = 8;
    static constexpr size_t ColumnWinceSoundId = 9;
    static constexpr size_t ColumnAwareSoundId = 10;
    static constexpr size_t ColumnSpriteStanding = 11;

    size_t maxId = 0;

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= ColumnInternalName || !isNumericString(trimCopy(row[ColumnId])))
        {
            continue;
        }

        maxId = std::max(maxId, static_cast<size_t>(std::stoul(trimCopy(row[ColumnId]))));
    }

    m_entries.clear();
    m_entries.resize(maxId + 1);

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= ColumnInternalName || !isNumericString(trimCopy(row[ColumnId])))
        {
            continue;
        }

        const size_t id = static_cast<size_t>(std::stoul(trimCopy(row[ColumnId])));
        MonsterEntry entry = {};
        entry.internalName = trimCopy(row[ColumnInternalName]);

        if (entry.internalName.empty())
        {
            continue;
        }

        entry.height = row.size() > ColumnHeight && !trimCopy(row[ColumnHeight]).empty()
            ? static_cast<uint16_t>(std::stoi(trimCopy(row[ColumnHeight])))
            : 0;
        entry.radius = row.size() > ColumnRadius && !trimCopy(row[ColumnRadius]).empty()
            ? static_cast<uint16_t>(std::stoi(trimCopy(row[ColumnRadius])))
            : 0;
        entry.movementSpeed = row.size() > ColumnMovementSpeed && !trimCopy(row[ColumnMovementSpeed]).empty()
            ? static_cast<uint16_t>(std::stoi(trimCopy(row[ColumnMovementSpeed])))
            : 0;
        entry.toHitRadius = row.size() > ColumnToHitRadius && !trimCopy(row[ColumnToHitRadius]).empty()
            ? static_cast<int16_t>(std::stoi(trimCopy(row[ColumnToHitRadius])))
            : 0;
        entry.tintColor = row.size() > ColumnTintColor ? parseUnsignedIntegerValue(row[ColumnTintColor]) : 0;
        entry.soundSampleIds[0] = row.size() > ColumnAttackSoundId && !trimCopy(row[ColumnAttackSoundId]).empty()
            ? static_cast<uint16_t>(std::stoi(trimCopy(row[ColumnAttackSoundId])))
            : 0;
        entry.soundSampleIds[1] = row.size() > ColumnDeathSoundId && !trimCopy(row[ColumnDeathSoundId]).empty()
            ? static_cast<uint16_t>(std::stoi(trimCopy(row[ColumnDeathSoundId])))
            : 0;
        entry.soundSampleIds[2] = row.size() > ColumnWinceSoundId && !trimCopy(row[ColumnWinceSoundId]).empty()
            ? static_cast<uint16_t>(std::stoi(trimCopy(row[ColumnWinceSoundId])))
            : 0;
        entry.soundSampleIds[3] = row.size() > ColumnAwareSoundId && !trimCopy(row[ColumnAwareSoundId]).empty()
            ? static_cast<uint16_t>(std::stoi(trimCopy(row[ColumnAwareSoundId])))
            : 0;

        for (size_t spriteIndex = 0; spriteIndex < entry.spriteNames.size(); ++spriteIndex)
        {
            const size_t columnIndex = ColumnSpriteStanding + spriteIndex;

            if (row.size() > columnIndex)
            {
                entry.spriteNames[spriteIndex] = trimCopy(row[columnIndex]);
            }
        }

        if (id < m_entries.size())
        {
            m_entries[id] = std::move(entry);
        }
    }

    return !m_entries.empty();
}

bool MonsterTable::loadDisplayNamesFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_displayNames.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 3 || row[0].empty())
        {
            continue;
        }

        if (!isNumericString(row[0]) || row[1].empty() || row[2].empty())
        {
            continue;
        }

        MonsterDisplayNameEntry entry = {};
        entry.id = std::stoi(row[0]);
        entry.displayName = row[1];
        entry.pictureName = toLowerCopy(row[2]);
        m_displayNames.push_back(std::move(entry));
    }

    return !m_displayNames.empty();
}

bool MonsterTable::loadStatsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_statsById.clear();
    m_statsIdByPictureName.clear();

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 15 || !isNumericString(row[0]))
        {
            continue;
        }

        MonsterStatsEntry entry = {};
        entry.id = std::stoi(row[0]);
        entry.name = row[1];
        entry.pictureName = row[2];
        entry.level = row[3].empty() ? 0 : std::stoi(row[3]);
        entry.hitPoints = row[4].empty() ? 0 : std::stoi(row[4]);
        entry.armorClass = row[5].empty() ? 0 : std::stoi(row[5]);
        entry.experience = row.size() > 6 && !row[6].empty() ? std::stoi(row[6]) : 0;
        entry.attack1Type = row.size() > 17 ? row[17] : std::string();
        entry.bloodSplatOnDeath = row.size() > 8 && !row[8].empty() && row[8] != "0";
        entry.canFly = row.size() > 9 && !row[9].empty() && toLowerCopy(row[9]) == "y";
        entry.movementType = row.size() > 10 ? parseMovementType(row[10]) : MonsterMovementType::Short;
        entry.aiType = row.size() > 11 ? parseAiType(row[11]) : MonsterAiType::Suicide;
        entry.treasureDefinition = row[7];
        entry.loot = parseLootPrototype(entry.treasureDefinition);
        entry.hostility = row[12].empty() ? 0 : std::stoi(row[12]);
        entry.speed = row[13].empty() ? 0 : std::stoi(row[13]);
        entry.recovery = row[14].empty() ? 0 : std::stoi(row[14]);
        entry.attackPreferences =
            row.size() > 15 && isNumericString(row[15]) ? static_cast<uint32_t>(std::stoul(row[15])) : 0;
        entry.specialAttackDescriptor = row.size() > 16 ? row[16] : std::string();
        const MonsterSpecialAttackParseResult specialAttack =
            parseMonsterSpecialAttack(entry.specialAttackDescriptor);
        entry.specialAttackKind = specialAttack.kind;
        entry.specialAttackLevel = specialAttack.level;
        entry.attack1MissileType = row.size() > 19 ? row[19] : std::string();
        entry.attack1HasMissile = isSupportedMonsterMissileToken(entry.attack1MissileType);
        entry.attack1Damage = row.size() > 18 ? parseDamageProfile(row[18]) : MonsterStatsEntry::DamageProfile();
        entry.attack2Chance = row.size() > 20 && !row[20].empty() ? std::stoi(row[20]) : 0;
        entry.attack2Type = row.size() > 21 ? row[21] : std::string();
        entry.attack2MissileType = row.size() > 23 ? row[23] : std::string();
        entry.attack2HasMissile = isSupportedMonsterMissileToken(entry.attack2MissileType);
        entry.attack2Damage = row.size() > 22 ? parseDamageProfile(row[22]) : MonsterStatsEntry::DamageProfile();
        entry.spell1Descriptor = row.size() > 25 ? row[25] : std::string();
        entry.spell1Name = parseMonsterSpellName(entry.spell1Descriptor);
        entry.hasSpell1 = hasMonsterAbilityDescriptor(entry.spell1Descriptor);
        entry.spell1UseChance = row.size() > 24 && !row[24].empty() ? std::stoi(row[24]) : 0;
        entry.spell1SkillLevel = parseMonsterSpellSkillLevel(entry.spell1Descriptor);
        entry.spell1SkillMastery = parseMonsterSpellSkillMastery(entry.spell1Descriptor);
        entry.spell2Descriptor = row.size() > 27 ? row[27] : std::string();
        entry.spell2Name = parseMonsterSpellName(entry.spell2Descriptor);
        entry.hasSpell2 = hasMonsterAbilityDescriptor(entry.spell2Descriptor);
        entry.spell2UseChance = row.size() > 26 && !row[26].empty() ? std::stoi(row[26]) : 0;
        entry.spell2SkillLevel = parseMonsterSpellSkillLevel(entry.spell2Descriptor);
        entry.spell2SkillMastery = parseMonsterSpellSkillMastery(entry.spell2Descriptor);
        entry.fireResistance = row.size() > 28 ? parseMonsterResistanceValue(row[28]) : 0;
        entry.airResistance = row.size() > 29 ? parseMonsterResistanceValue(row[29]) : 0;
        entry.waterResistance = row.size() > 30 ? parseMonsterResistanceValue(row[30]) : 0;
        entry.earthResistance = row.size() > 31 ? parseMonsterResistanceValue(row[31]) : 0;
        entry.mindResistance = row.size() > 32 ? parseMonsterResistanceValue(row[32]) : 0;
        entry.spiritResistance = row.size() > 33 ? parseMonsterResistanceValue(row[33]) : 0;
        entry.bodyResistance = row.size() > 34 ? parseMonsterResistanceValue(row[34]) : 0;
        entry.lightResistance = row.size() > 35 ? parseMonsterResistanceValue(row[35]) : 0;
        entry.darkResistance = row.size() > 36 ? parseMonsterResistanceValue(row[36]) : 0;
        entry.physicalResistance = row.size() > 37 ? parseMonsterResistanceValue(row[37]) : 0;
        entry.attackStyle = classifyAttackStyle(entry);

        const MonsterEntry *pEntry = findById(static_cast<int16_t>(entry.id));

        if (pEntry != nullptr)
        {
            entry.attackSoundId = pEntry->soundSampleIds[0];
            entry.deathSoundId = pEntry->soundSampleIds[1];
            entry.winceSoundId = pEntry->soundSampleIds[2];
            entry.awareSoundId = pEntry->soundSampleIds[3];
        }

        m_statsIdByPictureName[toLowerCopy(entry.pictureName)] = entry.id;
        m_statsById[entry.id] = std::move(entry);
    }

    return !m_statsById.empty();
}

bool MonsterTable::loadRelationsFromRows(const std::vector<std::vector<std::string>> &rows)
{
    m_relationLabels.clear();
    m_relations.clear();

    if (!rows.empty())
    {
        const std::vector<std::string> &header = rows.front();

        for (size_t columnIndex = 1; columnIndex < header.size(); ++columnIndex)
        {
            m_relationLabels.push_back(header[columnIndex]);
        }
    }

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 2)
        {
            continue;
        }

        std::vector<int> relationRow;
        relationRow.reserve(row.size() - 1);

        for (size_t columnIndex = 1; columnIndex < row.size(); ++columnIndex)
        {
            relationRow.push_back(row[columnIndex].empty() ? 0 : std::stoi(row[columnIndex]));
        }

        m_relations.push_back(std::move(relationRow));
    }

    return !m_relations.empty();
}

bool MonsterTable::loadUniqueNamesFromRows(const std::vector<std::vector<std::string>> &rows)
{
    size_t maxIndex = 0;

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 2 || row[0].empty())
        {
            continue;
        }

        if (!isNumericString(row[0]))
        {
            continue;
        }

        const size_t index = static_cast<size_t>(std::stoul(row[0]));
        maxIndex = std::max(maxIndex, index);
    }

    m_uniqueNames.clear();
    m_uniqueNames.resize(maxIndex + 1);

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() < 2 || row[0].empty())
        {
            continue;
        }

        if (!isNumericString(row[0]))
        {
            continue;
        }

        const size_t index = static_cast<size_t>(std::stoul(row[0]));

        if (index < m_uniqueNames.size())
        {
            m_uniqueNames[index] = row[1];
        }
    }

    return !m_uniqueNames.empty();
}

const MonsterEntry *MonsterTable::findByInternalName(const std::string &internalName) const
{
    const std::string normalizedName = toLowerCopy(internalName);

    for (const MonsterEntry &entry : m_entries)
    {
        if (toLowerCopy(entry.internalName) == normalizedName)
        {
            return &entry;
        }
    }

    return nullptr;
}

const MonsterEntry *MonsterTable::findById(int16_t monsterId) const
{
    if (monsterId < 0)
    {
        return nullptr;
    }

    const size_t index = static_cast<size_t>(monsterId);

    if (index >= m_entries.size())
    {
        return nullptr;
    }

    return &m_entries[index];
}

const MonsterTable::MonsterStatsEntry *MonsterTable::findStatsById(int16_t monsterId) const
{
    const auto iterator = m_statsById.find(monsterId);
    return iterator != m_statsById.end() ? &iterator->second : nullptr;
}

const MonsterTable::MonsterStatsEntry *MonsterTable::findStatsByPictureName(const std::string &pictureName) const
{
    const auto idIt = m_statsIdByPictureName.find(toLowerCopy(pictureName));

    if (idIt == m_statsIdByPictureName.end())
    {
        return nullptr;
    }

    return findStatsById(static_cast<int16_t>(idIt->second));
}

const MonsterTable::MonsterDisplayNameEntry *MonsterTable::findDisplayEntryById(int id) const
{
    for (const MonsterDisplayNameEntry &entry : m_displayNames)
    {
        if (entry.id == id)
        {
            return &entry;
        }
    }

    return nullptr;
}

std::optional<std::string> MonsterTable::findDisplayNameByInternalName(const std::string &internalName) const
{
    const std::string normalizedName = toLowerCopy(internalName);

    for (const MonsterDisplayNameEntry &entry : m_displayNames)
    {
        if (entry.pictureName == normalizedName)
        {
            return entry.displayName;
        }
    }

    return std::nullopt;
}

std::optional<std::string> MonsterTable::getUniqueName(int32_t uniqueNameIndex) const
{
    if (uniqueNameIndex <= 0)
    {
        return std::nullopt;
    }

    const size_t index = static_cast<size_t>(uniqueNameIndex);

    if (index >= m_uniqueNames.size() || m_uniqueNames[index].empty())
    {
        return std::nullopt;
    }

    return m_uniqueNames[index];
}

size_t MonsterTable::relationIndexForMonsterId(int16_t monsterId)
{
    if (monsterId <= 0)
    {
        return 0;
    }

    return static_cast<size_t>((monsterId - 1) / 3 + 1);
}

int MonsterTable::getRelationToParty(int16_t monsterId) const
{
    if (m_relations.empty())
    {
        return 0;
    }

    const size_t relationIndex = relationIndexForMonsterId(monsterId);

    if (relationIndex >= m_relations[0].size())
    {
        return 0;
    }

    return m_relations[0][relationIndex];
}

int MonsterTable::getRelationBetweenMonsters(int16_t leftMonsterId, int16_t rightMonsterId) const
{
    if (m_relations.empty())
    {
        return 0;
    }

    const size_t leftRelationIndex = relationIndexForMonsterId(leftMonsterId);
    const size_t rightRelationIndex = relationIndexForMonsterId(rightMonsterId);

    if (rightRelationIndex >= m_relations.size() || leftRelationIndex >= m_relations[rightRelationIndex].size())
    {
        return 0;
    }

    return m_relations[rightRelationIndex][leftRelationIndex];
}

bool MonsterTable::isHostileToParty(int16_t monsterId) const
{
    return getRelationToParty(monsterId) > 0;
}

bool MonsterTable::isLikelySameFaction(int16_t leftMonsterId, int16_t rightMonsterId) const
{
    const size_t leftRelationIndex = relationIndexForMonsterId(leftMonsterId);
    const size_t rightRelationIndex = relationIndexForMonsterId(rightMonsterId);

    if (leftRelationIndex == rightRelationIndex)
    {
        return true;
    }

    if (leftRelationIndex >= m_relationLabels.size() || rightRelationIndex >= m_relationLabels.size())
    {
        return false;
    }

    const std::string leftFactionKey = relationFactionKey(m_relationLabels[leftRelationIndex]);
    const std::string rightFactionKey = relationFactionKey(m_relationLabels[rightRelationIndex]);
    return !leftFactionKey.empty() && leftFactionKey == rightFactionKey;
}

const std::vector<MonsterEntry> &MonsterTable::getEntries() const
{
    return m_entries;
}
}
