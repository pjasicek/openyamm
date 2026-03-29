#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct HouseEntry
{
    uint32_t id = 0;
    uint32_t proprietorPictureId = 0;
    uint32_t roomSoundId = 0;
    std::string type;
    std::string name;
    std::string buildingName;
    std::string videoName;
    std::string proprietorName;
    std::string proprietorTitle;
    float priceMultiplier = 0.0f;
    float skillPriceMultiplier = 0.0f;
    int stockRefreshDays = 0;
    int trainingMaxLevel = 0;
    int openHour = 0;
    int closeHour = 0;
    std::string enterText;
    std::vector<std::string> offeredSkills;
    std::vector<uint32_t> residentNpcIds;
};

class HouseTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadAnimationRows(const std::vector<std::vector<std::string>> &rows);
    std::optional<std::string> getName(uint32_t houseId) const;
    const HouseEntry *get(uint32_t houseId) const;

private:
    std::unordered_map<uint32_t, HouseEntry> m_entries;
};
}
