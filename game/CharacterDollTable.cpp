#include "game/CharacterDollTable.h"

#include "game/StringUtils.h"

#include <cctype>
#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
bool parseUnsigned(const std::string &text, uint32_t &value)
{
    if (text.empty() || text[0] == '#')
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(text.c_str(), &pEnd, 10);

    if (pEnd == text.c_str() || *pEnd != '\0')
    {
        return false;
    }

    value = static_cast<uint32_t>(parsed);
    return true;
}

bool parseSigned(const std::string &text, int &value)
{
    if (text.empty() || text[0] == '#')
    {
        return false;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(text.c_str(), &pEnd, 10);

    if (pEnd == text.c_str() || *pEnd != '\0')
    {
        return false;
    }

    value = static_cast<int>(parsed);
    return true;
}

bool parseSigned32(const std::string &text, int32_t &value)
{
    int parsed = 0;

    if (!parseSigned(text, parsed))
    {
        return false;
    }

    value = parsed;
    return true;
}

std::string trimAsciiWhitespaceCopy(const std::string &value)
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

std::string normalizeAssetName(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimAsciiWhitespaceCopy(value));
    return normalized == "null" ? "none" : normalized;
}
}

bool CharacterDollTable::loadCharacterRows(const std::vector<std::vector<std::string>> &rows)
{
    m_characterEntries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 24)
        {
            continue;
        }

        CharacterDollEntry entry = {};

        if (!parseUnsigned(row[0], entry.id) || entry.id == 0)
        {
            continue;
        }

        parseUnsigned(row[1], entry.dollTypeId);
        parseUnsigned(row[2], entry.defaultClassId);
        parseUnsigned(row[3], entry.defaultVoiceId);
        parseUnsigned(row[4], entry.defaultSex);
        entry.availableAtStart = toLowerCopy(trimAsciiWhitespaceCopy(row[5])) == "x";
        parseSigned(row[6], entry.bodyOffsetX);

        int bodyY = 0;

        if (parseSigned(row[7], bodyY))
        {
            entry.bodyOffsetY = -bodyY;
        }

        entry.backgroundAsset = normalizeAssetName(row[8]);
        entry.bodyAsset = normalizeAssetName(row[9]);
        entry.headAsset = normalizeAssetName(row[10]);
        entry.leftHandClosedAsset = normalizeAssetName(row[11]);
        entry.leftHandHoldAsset = normalizeAssetName(row[12]);
        entry.leftHandOpenAsset = normalizeAssetName(row[13]);
        entry.rightHandFingersAsset = normalizeAssetName(row[14]);
        entry.rightHandOpenAsset = normalizeAssetName(row[17]);
        entry.rightHandHoldAsset = normalizeAssetName(row[18]);
        entry.facePicturesPrefix = trimAsciiWhitespaceCopy(row[19]);
        parseUnsigned(row[22], entry.npcPictureId);
        parseSigned32(row[23], entry.raceId);
        m_characterEntries[entry.id] = std::move(entry);
    }

    return !m_characterEntries.empty();
}

bool CharacterDollTable::loadDollTypeRows(const std::vector<std::vector<std::string>> &rows)
{
    m_dollTypeEntries.clear();

    for (size_t rowIndex = 1; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() < 28)
        {
            continue;
        }

        CharacterDollTypeEntry entry = {};

        if (!parseUnsigned(row[0], entry.id))
        {
            continue;
        }

        entry.canEquipBow = toLowerCopy(trimAsciiWhitespaceCopy(row[1])) == "x";
        entry.canEquipArmor = toLowerCopy(trimAsciiWhitespaceCopy(row[2])) == "x";
        entry.canEquipHelm = toLowerCopy(trimAsciiWhitespaceCopy(row[3])) == "x";
        entry.canEquipBelt = toLowerCopy(trimAsciiWhitespaceCopy(row[4])) == "x";
        entry.canEquipBoots = toLowerCopy(trimAsciiWhitespaceCopy(row[5])) == "x";
        entry.canEquipCloak = toLowerCopy(trimAsciiWhitespaceCopy(row[6])) == "x";
        entry.canEquipWeapon = toLowerCopy(trimAsciiWhitespaceCopy(row[7])) == "x";

        int *positions[] = {
            &entry.rightHandOpenX,
            &entry.rightHandOpenY,
            &entry.rightHandClosedX,
            &entry.rightHandClosedY,
            &entry.rightHandFingersX,
            &entry.rightHandFingersY,
            &entry.leftHandClosedX,
            &entry.leftHandClosedY,
            &entry.leftHandOpenX,
            &entry.leftHandOpenY,
            &entry.leftHandFingersX,
            &entry.leftHandFingersY,
            &entry.offHandOffsetX,
            &entry.offHandOffsetY,
            &entry.mainHandOffsetX,
            &entry.mainHandOffsetY,
            &entry.bowOffsetX,
            &entry.bowOffsetY,
            &entry.shieldX,
            &entry.shieldY
        };

        for (size_t index = 0; index < std::size(positions); index += 2)
        {
            int x = 0;
            int y = 0;
            parseSigned(row[8 + index], x);

            if (parseSigned(row[9 + index], y))
            {
                y = -y;
            }

            *positions[index] = x;
            *positions[index + 1] = y;
        }

        m_dollTypeEntries[entry.id] = std::move(entry);
    }

    return !m_dollTypeEntries.empty();
}

const CharacterDollEntry *CharacterDollTable::getCharacter(uint32_t characterId) const
{
    const std::unordered_map<uint32_t, CharacterDollEntry>::const_iterator it = m_characterEntries.find(characterId);
    return it != m_characterEntries.end() ? &it->second : nullptr;
}

const CharacterDollTypeEntry *CharacterDollTable::getDollType(uint32_t dollTypeId) const
{
    const std::unordered_map<uint32_t, CharacterDollTypeEntry>::const_iterator it =
        m_dollTypeEntries.find(dollTypeId);
    return it != m_dollTypeEntries.end() ? &it->second : nullptr;
}
}
