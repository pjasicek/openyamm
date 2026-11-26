#pragma once

#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class CampaignState;

// The Web of Worlds: Town Portal's tab of other planets, from the mounted worlds' `web_of_worlds` table contributions
// (world.yml tableContributions, mode append). No contribution: no tab. Text is English, localized where drawn; chart
// positions are in the Town Portal page's 640 x 480 units.
struct WebOfWorldsGreeting
{
    uint32_t qbit = 0;
    std::string message;
    std::string sound;
};

struct WebOfWorldsBeacon
{
    std::string name;
    // The rail's "Travel to <planet>: <travel>"; empty: the name.
    std::string travel;
    std::string mapFileName;
    // No position: the map's start.
    std::optional<std::array<int32_t, 3>> position;
    std::optional<int32_t> directionDegrees;
    // 0: always lit.
    uint32_t litQBit = 0;
};

struct WebOfWorldsCounter
{
    std::string label;
    std::vector<uint32_t> qbits;
};

struct WebOfWorldsSignal
{
    std::string name;
    // The name once the planet is cleansed; empty: the name.
    std::string clearedName;
    std::string epithet;
    std::string message;
    std::string icon;
    float x = 0;
    float y = 0;
    float radius = 8;
};

struct WebOfWorldsPlanet
{
    std::string key;
    std::string worldId;
    std::string name;
    std::string epithet;
    std::string clearedEpithet;
    std::string status;
    std::string clearedStatus;
    std::string icon;
    std::string clearedIcon;
    float x = 0;
    float y = 0;
    float radius = 20;
    std::string threadFrom;
    uint32_t threat = 0;
    uint32_t clearedQBit = 0;
    std::vector<WebOfWorldsCounter> counters;
    std::vector<uint32_t> purgeQBits;
    std::vector<WebOfWorldsBeacon> beacons;
    std::vector<WebOfWorldsSignal> signals;
};

struct WebOfWorldsKnownWorld
{
    std::string name;
    std::string subtitle;
    float x = 0;
    float y = 0;
    float radius = 10;
    // Town Portal groups (town_portal_switch.txt) the node opens, the first one present.
    std::vector<std::string> continents;
};

struct WebOfWorldsCount
{
    uint32_t done = 0;
    uint32_t total = 0;
};

// What a party has done on a planet, worked out from its QBits.
struct WebOfWorldsPlanetProgress
{
    bool cleared = false;
    // 0 to 100.
    uint32_t purgePercent = 0;
    std::vector<WebOfWorldsCount> counters;
    // Indexes of the lit beacons, in list order.
    std::vector<size_t> litBeacons;
};

// The open chart's progress, shared by drawing, hit testing and travel selection.
class WebOfWorldsProgressReading
{
public:
    const WebOfWorldsPlanetProgress &get(const WebOfWorldsPlanet &planet, const CampaignState *pCampaign);

private:
    const WebOfWorldsPlanet *m_pPlanet = nullptr;
    const CampaignState *m_pCampaign = nullptr;
    uint64_t m_questRevision = 0;
    WebOfWorldsPlanetProgress m_progress;
};

using WebOfWorldsQBitQuery = std::function<bool(uint32_t)>;

class WebOfWorldsTable
{
public:
    bool appendFromYaml(const std::string &yamlText, std::string &errorMessage);

    bool empty() const;
    const std::vector<uint32_t> &unlockQBits() const;
    const std::string &lockedHint() const;
    const std::string &openHint() const;
    const WebOfWorldsGreeting &firstOpen() const;
    const std::vector<WebOfWorldsKnownWorld> &knownWorlds() const;
    const std::vector<WebOfWorldsPlanet> &planets() const;
    // The planet whose world this is, or null.
    const WebOfWorldsPlanet *findPlanetByWorld(const std::string &worldId) const;

    // The tab opens when the party has any unlock QBit, or stands on a planet (it must be able to go home).
    bool isUnlocked(const WebOfWorldsQBitQuery &hasQBit, bool partyOnPlanet) const;

private:
    std::vector<uint32_t> m_unlockQBits;
    std::string m_lockedHint;
    std::string m_openHint;
    WebOfWorldsGreeting m_firstOpen;
    std::vector<WebOfWorldsKnownWorld> m_knownWorlds;
    std::vector<WebOfWorldsPlanet> m_planets;
};

WebOfWorldsPlanetProgress webOfWorldsPlanetProgress(
    const WebOfWorldsPlanet &planet, const WebOfWorldsQBitQuery &hasQBit);
}
