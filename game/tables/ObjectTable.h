#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct ObjectEntry
{
    std::string internalName;
    std::string spriteName;
    int16_t objectId = 0;
    int16_t radius = 0;
    int16_t height = 0;
    uint16_t flags = 0;
    uint16_t spriteId = 0;
    int16_t lifetimeTicks = 0;
    uint32_t particleTrailColor = 0;
    int16_t speed = 0;
    uint8_t particleTrailRed = 0;
    uint8_t particleTrailGreen = 0;
    uint8_t particleTrailBlue = 0;
};

class ObjectTable
{
public:
    bool loadRows(const std::vector<std::vector<std::string>> &rows);
    const ObjectEntry *get(uint16_t objectDescriptionId) const;
    const ObjectEntry *findByObjectId(int16_t objectId) const;
    std::optional<uint16_t> findDescriptionIdByObjectId(int16_t objectId) const;

private:
    std::vector<ObjectEntry> m_entries;
    std::unordered_map<int16_t, uint16_t> m_descriptionIdByObjectId;
};
}
