#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class MapRegistry;
class Mm9RudeDialogueTable;
class Party;

struct Mm9TransportRoute
{
    std::string canonicalId;
    uint32_t dockNpcId = 0;
    uint32_t shopId = 0;
    std::string dockName;
    std::string serviceClassification;
    size_t sourceRudeRowIndex = 0;
    size_t sourceLine = 0;
    std::string destinationName;
    std::string destinationMapCanonicalId;
    std::string destinationMapFileName;
    std::string destinationStartPoint;
    int arrivalX = 0;
    int arrivalY = 0;
    int arrivalZ = 0;
    double facingDegrees = 0.0;
    uint16_t facingYawUnits = 0;
    bool movePlayerToFloor = false;
    std::string availableWeekday;
    uint8_t sourceDayIndex = 0;
    uint32_t travelDays = 0;
    uint32_t basePrice = 0;
    float priceMultiplier = 0.0f;
    std::vector<int32_t> requiredRawKeys;
    std::vector<int32_t> forbiddenRawKeys;
    uint32_t routeOrder = 0;
    std::string sourceShop;
    std::string sourceRude;
    std::string scheduleSource;
    std::string executableRva;
    std::string reviewState;
    std::string provenance;
};

class Mm9TransportRouteTable
{
public:
    void clear();
    bool loadFromRows(
        const std::vector<std::vector<std::string>> &rows,
        const MapRegistry &mapRegistry,
        const Mm9RudeDialogueTable &rudeDialogueTable);
    const Mm9TransportRoute *findByCanonicalId(const std::string &canonicalId) const;
    const Mm9TransportRoute *findForServiceDay(uint32_t rudeId, uint8_t sourceDayIndex) const;
    std::vector<const Mm9TransportRoute *> forService(uint32_t rudeId) const;
    const std::vector<Mm9TransportRoute> &entries() const;
    const std::vector<std::string> &errors() const;

private:
    void addError(size_t rowNumber, const std::string &message);

    std::vector<Mm9TransportRoute> m_entries;
    std::unordered_map<std::string, size_t> m_entryIndexByCanonicalId;
    std::unordered_map<uint32_t, std::vector<size_t>> m_entryIndicesByService;
    std::unordered_map<uint64_t, size_t> m_entryIndexByServiceDay;
    std::vector<std::string> m_errors;
};

// MM9's day index (its schedule's own order, 0 Saturday) of the calendar's weekday at that time (the shared calendar
// starts each week on Monday), so a dock sails its Monday route on the day the game calls Monday.
uint8_t mm9TransportDayIndex(float gameMinutes);
// The calendar weekday a route sails on, 0 Monday.
int mm9TransportWeekday(const Mm9TransportRoute &route);
bool mm9TransportRouteConditionsSatisfied(const Mm9TransportRoute &route, const Party &party);
}
