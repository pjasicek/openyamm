#include "game/ItemTable.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
std::string toLowerCopy(const std::string &value)
{
    std::string lower = value;

    std::transform(
        lower.begin(),
        lower.end(),
        lower.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        }
    );

    return lower;
}

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])))
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string getCell(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return {};
    }

    return trimCopy(row[index]);
}

int parseInt(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    try
    {
        return std::stoi(value);
    }
    catch (...)
    {
        return 0;
    }
}

std::optional<uint32_t> parseItemId(const std::vector<std::string> &row)
{
    const std::string rawItemId = getCell(row, 0);

    if (rawItemId.empty())
    {
        return std::nullopt;
    }

    for (char character : rawItemId)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return std::nullopt;
        }
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(rawItemId));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

bool readInt32LittleEndian(const std::vector<uint8_t> &bytes, size_t offset, int32_t &value)
{
    if (offset + sizeof(value) > bytes.size())
    {
        return false;
    }

    std::memcpy(&value, bytes.data() + offset, sizeof(value));
    return true;
}

bool loadBitmapDimensions(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::unordered_map<std::string, std::string> &iconPaths,
    const std::string &iconName,
    int &width,
    int &height,
    std::string &virtualPath
)
{
    if (iconName.empty())
    {
        return false;
    }

    const auto foundPath = iconPaths.find(toLowerCopy(iconName));

    if (foundPath == iconPaths.end())
    {
        return false;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = assetFileSystem.readBinaryFile(foundPath->second);

    if (!bitmapBytes || bitmapBytes->size() < 26 || (*bitmapBytes)[0] != 'B' || (*bitmapBytes)[1] != 'M')
    {
        return false;
    }

    int32_t bitmapWidth = 0;
    int32_t bitmapHeight = 0;

    if (!readInt32LittleEndian(*bitmapBytes, 18, bitmapWidth)
        || !readInt32LittleEndian(*bitmapBytes, 22, bitmapHeight))
    {
        return false;
    }

    if (bitmapWidth <= 0 || bitmapHeight == 0)
    {
        return false;
    }

    width = bitmapWidth;
    height = std::abs(bitmapHeight);
    virtualPath = foundPath->second;
    return true;
}

uint8_t inventorySlotsFromPixels(int pixelSize)
{
    const int clampedPixels = std::max(14, pixelSize);
    const int slots = 1 + (clampedPixels - 14) / 32;
    return static_cast<uint8_t>(std::clamp(slots, 1, 14));
}

std::unordered_map<std::string, std::string> buildIconPathMap(const Engine::AssetFileSystem &assetFileSystem)
{
    std::unordered_map<std::string, std::string> iconPaths;
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/icons");

    for (const std::string &entry : entries)
    {
        const std::string lowerEntry = toLowerCopy(entry);

        if (lowerEntry.size() <= 4 || lowerEntry.substr(lowerEntry.size() - 4) != ".bmp")
        {
            continue;
        }

        const std::string iconStem = lowerEntry.substr(0, lowerEntry.size() - 4);
        iconPaths[iconStem] = "Data/icons/" + entry;
    }

    return iconPaths;
}
}

bool ItemTable::load(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::vector<std::string>> &itemRows,
    const std::vector<std::vector<std::string>> &randomItemRows
)
{
    const std::unordered_map<std::string, std::string> iconPaths = buildIconPathMap(assetFileSystem);
    uint32_t maxItemId = 0;

    for (const std::vector<std::string> &row : itemRows)
    {
        const std::optional<uint32_t> itemId = parseItemId(row);

        if (!itemId)
        {
            continue;
        }

        maxItemId = std::max(maxItemId, *itemId);
    }

    if (maxItemId == 0)
    {
        return false;
    }

    m_entries.clear();
    m_entries.resize(static_cast<size_t>(maxItemId) + 1);

    for (size_t itemIndex = 0; itemIndex < m_entries.size(); ++itemIndex)
    {
        m_entries[itemIndex].itemId = static_cast<uint32_t>(itemIndex);
    }

    for (const std::vector<std::string> &row : itemRows)
    {
        const std::optional<uint32_t> itemId = parseItemId(row);

        if (!itemId || *itemId >= m_entries.size())
        {
            continue;
        }

        ItemDefinition &entry = m_entries[*itemId];
        entry.itemId = *itemId;
        entry.iconName = getCell(row, 1);
        entry.name = getCell(row, 2);
        entry.value = parseInt(getCell(row, 3));
        entry.equipStat = getCell(row, 4);
        entry.skillGroup = getCell(row, 5);
        entry.mod1 = getCell(row, 6);
        entry.mod2 = getCell(row, 7);
        entry.material = parseInt(getCell(row, 8));
        entry.idRepSt = getCell(row, 9);
        entry.unidentifiedName = getCell(row, 10);
        entry.spriteIndex = static_cast<uint16_t>(std::max(0, parseInt(getCell(row, 11))));
        entry.varA = parseInt(getCell(row, 12));
        entry.varB = parseInt(getCell(row, 13));
        entry.equipX = parseInt(getCell(row, 14));
        entry.equipY = parseInt(getCell(row, 15));
        entry.notes = getCell(row, 16);

        int iconWidth = 0;
        int iconHeight = 0;

        if (loadBitmapDimensions(assetFileSystem, iconPaths, entry.iconName, iconWidth, iconHeight, entry.iconVirtualPath))
        {
            entry.inventoryWidth = inventorySlotsFromPixels(iconWidth);
            entry.inventoryHeight = inventorySlotsFromPixels(iconHeight);
        }
        else
        {
            entry.inventoryWidth = 1;
            entry.inventoryHeight = 1;
        }
    }

    for (const std::vector<std::string> &row : randomItemRows)
    {
        const std::optional<uint32_t> itemId = parseItemId(row);

        if (!itemId || *itemId >= m_entries.size())
        {
            continue;
        }

        ItemDefinition &entry = m_entries[*itemId];

        for (size_t weightIndex = 0; weightIndex < entry.randomTreasureWeights.size(); ++weightIndex)
        {
            entry.randomTreasureWeights[weightIndex] = parseInt(getCell(row, 2 + weightIndex));
        }
    }

    return true;
}

const ItemDefinition *ItemTable::get(uint32_t itemId) const
{
    if (itemId >= m_entries.size())
    {
        return nullptr;
    }

    const ItemDefinition &entry = m_entries[itemId];

    if (entry.itemId == 0 && itemId != 0)
    {
        return nullptr;
    }

    if (itemId != 0 && entry.name.empty() && entry.iconName.empty())
    {
        return nullptr;
    }

    return &entry;
}

const std::vector<ItemDefinition> &ItemTable::entries() const
{
    return m_entries;
}
}
