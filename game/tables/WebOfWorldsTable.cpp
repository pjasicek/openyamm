#include "game/tables/WebOfWorldsTable.h"

#include "game/StringUtils.h"
#include "game/party/CampaignState.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <exception>

namespace OpenYAMM::Game
{
namespace
{
std::string text(const YAML::Node &node, const char *pKey)
{
    const YAML::Node value = node[pKey];
    return value && value.IsScalar() ? value.as<std::string>() : std::string();
}

bool readQBits(const YAML::Node &node, std::vector<uint32_t> &qbits, std::string &errorMessage)
{
    if (!node)
    {
        return true;
    }

    if (!node.IsSequence())
    {
        errorMessage = "a QBit list must be a sequence";
        return false;
    }

    for (const YAML::Node &item : node)
    {
        qbits.push_back(item.as<uint32_t>());
    }

    return true;
}

bool readPoint(const YAML::Node &node, float &x, float &y, std::string &errorMessage, const std::string &owner)
{
    if (!node || !node.IsSequence() || node.size() != 2)
    {
        errorMessage = owner + " needs position: [x, y]";
        return false;
    }

    x = node[0].as<float>();
    y = node[1].as<float>();
    return true;
}
}

bool WebOfWorldsTable::appendFromYaml(const std::string &yamlText, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(yamlText);

        if (!readQBits(root["unlock_qbits"], m_unlockQBits, errorMessage))
        {
            return false;
        }

        if (m_lockedHint.empty())
        {
            m_lockedHint = text(root, "locked_hint");
        }

        if (m_openHint.empty())
        {
            m_openHint = text(root, "open_hint");
        }

        if (const YAML::Node greeting = root["first_open"])
        {
            if (m_firstOpen.qbit != 0 || !greeting.IsMap() || greeting["qbit"].as<uint32_t>(0) == 0
                || text(greeting, "message").empty())
            {
                errorMessage = "first_open needs a unique greeting with a qbit and message";
                return false;
            }
            m_firstOpen = {greeting["qbit"].as<uint32_t>(), text(greeting, "message"), text(greeting, "sound")};
        }

        for (const YAML::Node &node : root["known_worlds"])
        {
            WebOfWorldsKnownWorld world;
            world.name = text(node, "name");

            if (world.name.empty() || !readPoint(node["position"], world.x, world.y, errorMessage, "known world"))
            {
                errorMessage = world.name.empty() ? "a known world needs a name" : errorMessage;
                return false;
            }

            world.subtitle = text(node, "subtitle");
            world.radius = node["radius"] ? node["radius"].as<float>() : world.radius;

            for (const YAML::Node &continent : node["continents"])
            {
                world.continents.push_back(continent.as<std::string>());
            }

            // Several worlds may draw the same known world: the first wins.
            const bool known = std::any_of(m_knownWorlds.begin(), m_knownWorlds.end(),
                [&world](const WebOfWorldsKnownWorld &other) { return other.name == world.name; });

            if (!known)
            {
                m_knownWorlds.push_back(std::move(world));
            }
        }

        for (const YAML::Node &node : root["planets"])
        {
            WebOfWorldsPlanet planet;
            planet.key = text(node, "key");
            planet.worldId = toLowerCopy(text(node, "world"));
            planet.name = text(node, "name");

            if (planet.key.empty() || planet.worldId.empty() || planet.name.empty())
            {
                errorMessage = "a planet needs key, world and name";
                return false;
            }

            if (!readPoint(node["position"], planet.x, planet.y, errorMessage, "planet " + planet.key))
            {
                return false;
            }

            planet.epithet = text(node, "epithet");
            planet.clearedEpithet = text(node, "cleared_epithet");
            planet.status = text(node, "status");
            planet.clearedStatus = text(node, "cleared_status");
            planet.icon = toLowerCopy(text(node, "icon"));
            planet.clearedIcon = toLowerCopy(text(node, "cleared_icon"));
            planet.radius = node["radius"] ? node["radius"].as<float>() : planet.radius;
            planet.threadFrom = text(node, "thread_from");
            planet.threat = node["threat"] ? node["threat"].as<uint32_t>() : 0;
            planet.clearedQBit = node["cleared_qbit"] ? node["cleared_qbit"].as<uint32_t>() : 0;

            if (!readQBits(node["purge_qbits"], planet.purgeQBits, errorMessage))
            {
                return false;
            }

            for (const YAML::Node &counterNode : node["counters"])
            {
                WebOfWorldsCounter counter;
                counter.label = text(counterNode, "label");

                if (counter.label.empty() || !readQBits(counterNode["qbits"], counter.qbits, errorMessage))
                {
                    errorMessage = counter.label.empty() ? "a planet counter needs a label" : errorMessage;
                    return false;
                }

                planet.counters.push_back(std::move(counter));
            }

            for (const YAML::Node &beaconNode : node["beacons"])
            {
                WebOfWorldsBeacon beacon;
                beacon.name = text(beaconNode, "name");
                beacon.travel = text(beaconNode, "travel");
                beacon.mapFileName = toLowerCopy(text(beaconNode, "map"));

                if (beacon.name.empty() || beacon.mapFileName.empty())
                {
                    errorMessage = "a beacon of planet " + planet.key + " needs name and map";
                    return false;
                }

                if (const YAML::Node position = beaconNode["position"])
                {
                    if (!position.IsSequence() || position.size() != 3)
                    {
                        errorMessage = "beacon " + beacon.name + ": position must be [x, y, z]";
                        return false;
                    }

                    beacon.position = std::array<int32_t, 3>{
                        position[0].as<int32_t>(), position[1].as<int32_t>(), position[2].as<int32_t>()};
                }

                if (beaconNode["direction"])
                {
                    beacon.directionDegrees = beaconNode["direction"].as<int32_t>();
                }

                beacon.litQBit = beaconNode["lit_qbit"] ? beaconNode["lit_qbit"].as<uint32_t>() : 0;
                planet.beacons.push_back(std::move(beacon));
            }

            if (planet.beacons.empty())
            {
                errorMessage = "planet " + planet.key + " needs at least one beacon";
                return false;
            }

            for (const YAML::Node &signalNode : node["signals"])
            {
                WebOfWorldsSignal signal;
                signal.name = text(signalNode, "name");

                if (signal.name.empty()
                    || !readPoint(signalNode["position"], signal.x, signal.y, errorMessage, "signal"))
                {
                    errorMessage = signal.name.empty() ? "a signal needs a name" : errorMessage;
                    return false;
                }

                signal.clearedName = text(signalNode, "cleared_name");
                signal.epithet = text(signalNode, "epithet");
                signal.message = text(signalNode, "message");
                signal.icon = toLowerCopy(text(signalNode, "icon"));
                signal.radius = signalNode["radius"] ? signalNode["radius"].as<float>() : signal.radius;
                planet.signals.push_back(std::move(signal));
            }

            const bool duplicate = std::any_of(m_planets.begin(), m_planets.end(),
                [&planet](const WebOfWorldsPlanet &other) { return other.key == planet.key; });

            if (duplicate)
            {
                errorMessage = "planet " + planet.key + " is defined twice";
                return false;
            }

            m_planets.push_back(std::move(planet));
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    return true;
}

bool WebOfWorldsTable::empty() const
{
    return m_planets.empty();
}

const std::vector<uint32_t> &WebOfWorldsTable::unlockQBits() const
{
    return m_unlockQBits;
}

const std::string &WebOfWorldsTable::lockedHint() const
{
    return m_lockedHint;
}

const std::string &WebOfWorldsTable::openHint() const
{
    return m_openHint;
}

const WebOfWorldsGreeting &WebOfWorldsTable::firstOpen() const
{
    return m_firstOpen;
}

const std::vector<WebOfWorldsKnownWorld> &WebOfWorldsTable::knownWorlds() const
{
    return m_knownWorlds;
}

const std::vector<WebOfWorldsPlanet> &WebOfWorldsTable::planets() const
{
    return m_planets;
}

const WebOfWorldsPlanet *WebOfWorldsTable::findPlanetByWorld(const std::string &worldId) const
{
    const std::string wanted = toLowerCopy(worldId);

    for (const WebOfWorldsPlanet &planet : m_planets)
    {
        if (!wanted.empty() && planet.worldId == wanted)
        {
            return &planet;
        }
    }

    return nullptr;
}

bool WebOfWorldsTable::isUnlocked(const WebOfWorldsQBitQuery &hasQBit, bool partyOnPlanet) const
{
    if (partyOnPlanet)
    {
        return true;
    }

    return std::any_of(m_unlockQBits.begin(), m_unlockQBits.end(),
        [&hasQBit](uint32_t qbit) { return qbit != 0 && hasQBit(qbit); });
}

WebOfWorldsPlanetProgress webOfWorldsPlanetProgress(
    const WebOfWorldsPlanet &planet, const WebOfWorldsQBitQuery &hasQBit)
{
    WebOfWorldsPlanetProgress progress;
    progress.cleared = planet.clearedQBit != 0 && hasQBit(planet.clearedQBit);
    const auto count = [&hasQBit](const std::vector<uint32_t> &qbits)
    {
        WebOfWorldsCount result;
        result.total = uint32_t(qbits.size());
        result.done = uint32_t(std::count_if(qbits.begin(), qbits.end(), hasQBit));
        return result;
    };
    WebOfWorldsCount purge = count(planet.purgeQBits);

    for (const WebOfWorldsCounter &counter : planet.counters)
    {
        progress.counters.push_back(count(counter.qbits));

        if (planet.purgeQBits.empty())
        {
            purge.done += progress.counters.back().done;
            purge.total += progress.counters.back().total;
        }
    }

    progress.purgePercent = progress.cleared ? 100 : purge.total == 0 ? 0 : purge.done * 100 / purge.total;

    for (size_t index = 0; index < planet.beacons.size(); ++index)
    {
        const uint32_t qbit = planet.beacons[index].litQBit;

        if (qbit == 0 || hasQBit(qbit))
        {
            progress.litBeacons.push_back(index);
        }
    }

    return progress;
}

const WebOfWorldsPlanetProgress &WebOfWorldsProgressReading::get(
    const WebOfWorldsPlanet &planet, const CampaignState *pCampaign)
{
    const uint64_t revision = pCampaign ? pCampaign->questRevision() : 0;
    if (m_pPlanet != &planet || m_pCampaign != pCampaign || m_questRevision != revision)
    {
        m_progress = webOfWorldsPlanetProgress(planet,
            [pCampaign](uint32_t qbit) { return pCampaign && pCampaign->hasQuestBit(qbit); });
        m_pPlanet = &planet;
        m_pCampaign = pCampaign;
        m_questRevision = revision;
    }
    return m_progress;
}
}
