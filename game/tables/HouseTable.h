#pragma once

#include <cstdint>
#include <array>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct HouseEntry
{
    struct TransportRoute
    {
        uint32_t routeIndex = 0;
        std::string destinationName;
        std::string mapFileName;
        std::array<bool, 7> daysAvailable = {true, true, true, true, true, true, true};
        uint32_t travelDays = 0;
        int x = 0;
        int y = 0;
        int z = 0;
        int directionDegrees = 0;
        uint32_t requiredQBit = 0;
        bool useMapStartPosition = false;
    };

    uint32_t id = 0;
    uint32_t mapId = 0;
    uint32_t proprietorPictureId = 0;
    uint32_t roomSoundId = 0;
    uint32_t houseSoundBaseId = 0;
    std::string type;
    std::string name;
    std::string buildingName;
    std::string videoName;
    std::string proprietorName;
    std::string proprietorTitle;
    float priceMultiplier = 0.0f;
    float skillPriceMultiplier = 0.0f;
    int standardStockTier = 0;
    int specialStockTier = 0;
    int stockRefreshDays = 0;
    int trainingMaxLevel = 0;
    int openHour = 0;
    int closeHour = 0;
    std::string enterText;
    std::vector<std::string> offeredSkills;
    std::vector<uint32_t> residentNpcIds;
    std::vector<TransportRoute> transportRoutes;
};

class HouseTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadAnimationRows(const std::vector<std::vector<std::string>> &rows);
    bool loadTransportScheduleRows(const std::vector<std::vector<std::string>> &rows);
    std::optional<std::string> getName(uint32_t houseId) const;
    const HouseEntry *get(uint32_t houseId) const;
    const std::unordered_map<uint32_t, HouseEntry> &entries() const;

private:
    std::unordered_map<uint32_t, HouseEntry> m_entries;
};
}
