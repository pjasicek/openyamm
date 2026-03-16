#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct ChestEntry
{
    std::string name;
    uint8_t width = 0;
    uint8_t height = 0;
    int16_t textureId = 0;
    std::string textureName;
};

class ChestTable
{
public:
    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    const ChestEntry *get(uint16_t chestTypeId) const;
    const std::vector<ChestEntry> &getEntries() const;

private:
    std::vector<ChestEntry> m_entries;
};
}
