#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct ObjectEntry
{
    std::string internalName;
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
    bool loadFromBytes(const std::vector<uint8_t> &bytes);
    const ObjectEntry *get(uint16_t objectDescriptionId) const;

private:
    std::vector<ObjectEntry> m_entries;
};
}
