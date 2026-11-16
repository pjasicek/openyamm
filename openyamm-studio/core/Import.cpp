#include "core/Import.h"

#include "core/CanonicalYaml.h"
#include "core/EventFlow.h"
#include "core/Project.h"
#include "core/SceneOverlay.h"
#include "core/Schema.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
// A sector smaller than this is an alcove or a key slot, not a place of the plan (core/Reachability's niche rule).
constexpr double NicheFloorArea = 40000.0;

std::string idSafe(const std::string &text)
{
    std::string result;

    for (const char character : text)
    {
        const char lower = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
        result.push_back((lower >= 'a' && lower <= 'z') || (lower >= '0' && lower <= '9') ? lower : '_');
    }

    return result.empty() ? "map" : result;
}

struct SectorShape
{
    double floorArea = 0.0;
    double lowestFloor = 0.0;
    double highestFloor = 0.0;
    bool hasFloor = false;
};

const char *sizeClass(double area)
{
    const double millions = area / 1.0e6;

    if (millions < 0.15)
    {
        return "XS";
    }

    if (millions < 0.5)
    {
        return "S";
    }

    if (millions < 1.5)
    {
        return "M";
    }

    return millions < 3.0 ? "L" : "XL";
}
}

bool importMapAsProject(
    const LoadedMap &map,
    const std::filesystem::path &projectDirectory,
    std::vector<std::string> &writtenFiles,
    std::string &errorMessage)
{
    const SchemaSet &schemas = SchemaSet::builtIn();
    YAML::Node card(YAML::NodeType::Map);
    card["format"] = 0;
    card["id"] = idSafe(map.stem);
    card["world"] = map.world;
    card["kind"] = map.indoor ? "indoor" : "outdoor";
    // An indoor map open to the sky is an MM9 region (with terrain) or city (S6_PLAN.md item O).
    card["profile"] = map.indoor ? (map.indoorScene ? indoorSceneProfile(*map.indoorScene) : "dungeon") : "odm";
    card["base"] = map.fileName;

    YAML::Node plan(YAML::NodeType::Map);
    plan["format"] = 0;
    plan["level"] = "L1";
    YAML::Node lock(YAML::NodeType::Map);
    lock["format"] = 0;

    // Where the map's exits lead, from its handlers.
    std::string flowJson;
    std::string flowError;
    std::map<std::string, std::set<int>> exitEventsByMap;

    if (exploreEventHandlers(map, flowJson, flowError))
    {
        const YAML::Node events = YAML::Load(flowJson);

        for (const YAML::Node &event : events)
        {
            for (const YAML::Node &path : event["paths"])
            {
                for (const YAML::Node &effect : path["effects"])
                {
                    if (effect.Scalar().starts_with("leave to "))
                    {
                        exitEventsByMap[effect.Scalar().substr(9)].insert(event["event"].as<int>());
                    }
                }
            }
        }
    }

    YAML::Node neighbours(YAML::NodeType::Sequence);

    for (const std::pair<const std::string, std::set<int>> &entry : exitEventsByMap)
    {
        YAML::Node neighbour(YAML::NodeType::Map);
        const std::filesystem::path target(entry.first);
        neighbour["id"] = "exit:" + idSafe(target.stem().string());
        neighbour["to"] = entry.first;
        neighbour["kind"] = "door";
        neighbours.push_back(neighbour);
    }

    if (neighbours.size() > 0)
    {
        card["neighbours"] = neighbours;
    }

    YAML::Node totals(YAML::NodeType::Map);

    if (map.events)
    {
        YAML::Node eventNumbers(YAML::NodeType::Map);

        for (const uint16_t eventId : map.events->eventIds())
        {
            eventNumbers["evt:e" + std::to_string(eventId)] = static_cast<int>(eventId);
        }

        if (eventNumbers.size() > 0)
        {
            lock["events"] = eventNumbers;
        }

        totals["handlers"] = static_cast<int>(map.events->eventIds().size());
    }

    if (map.state)
    {
        YAML::Node doorNumbers(YAML::NodeType::Map);

        for (const Game::MapDeltaDoor &door : map.state->doors)
        {
            if (door.doorId > 0)
            {
                doorNumbers["door:d" + std::to_string(door.doorId)] = static_cast<int>(door.doorId);
            }
        }

        if (doorNumbers.size() > 0)
        {
            lock["doors"] = doorNumbers;
        }

        totals["doors"] = static_cast<int>(map.state->doors.size());
        totals["fixed_actors"] = static_cast<int>(map.state->actors.size());
    }

    if (map.indoor)
    {
        const Game::IndoorMapData &indoor = *map.indoor;
        std::vector<SectorShape> shapes(indoor.sectors.size());
        std::set<std::pair<size_t, size_t>> links;
        std::map<std::pair<size_t, size_t>, std::array<double, 6>> portalBounds;

        for (const Game::IndoorFace &face : indoor.faces)
        {
            if (face.vertexIndices.size() < 3 || face.roomNumber >= indoor.sectors.size())
            {
                continue;
            }

            double doubleArea = 0.0;
            std::array<double, 6> bounds = {1.0e9, 1.0e9, 1.0e9, -1.0e9, -1.0e9, -1.0e9};
            double normalX = 0.0;
            double normalY = 0.0;

            for (size_t index = 0; index < face.vertexIndices.size(); ++index)
            {
                const Game::IndoorVertex &current = indoor.vertices[face.vertexIndices[index]];
                const Game::IndoorVertex &next =
                    indoor.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
                doubleArea += static_cast<double>(current.x) * next.y - static_cast<double>(next.x) * current.y;
                normalX += (static_cast<double>(current.y) - next.y) * (static_cast<double>(current.z) + next.z);
                normalY += (static_cast<double>(current.z) - next.z) * (static_cast<double>(current.x) + next.x);
                bounds[0] = std::min(bounds[0], static_cast<double>(current.x));
                bounds[1] = std::min(bounds[1], static_cast<double>(current.y));
                bounds[2] = std::min(bounds[2], static_cast<double>(current.z));
                bounds[3] = std::max(bounds[3], static_cast<double>(current.x));
                bounds[4] = std::max(bounds[4], static_cast<double>(current.y));
                bounds[5] = std::max(bounds[5], static_cast<double>(current.z));
            }

            if (face.isPortal)
            {
                if (face.roomNumber != 0 && face.roomBehindNumber != 0 && face.roomNumber != face.roomBehindNumber)
                {
                    const std::pair<size_t, size_t> link = {
                        std::min<size_t>(face.roomNumber, face.roomBehindNumber),
                        std::max<size_t>(face.roomNumber, face.roomBehindNumber)};
                    links.insert(link);
                    portalBounds[link] = bounds;
                }

                continue;
            }

            // A floor: facing up more than sideways.
            const double horizontal = std::sqrt(normalX * normalX + normalY * normalY);

            if (doubleArea > 0.0 && doubleArea > horizontal)
            {
                SectorShape &shape = shapes[face.roomNumber];
                shape.lowestFloor = shape.hasFloor ? std::min(shape.lowestFloor, bounds[2]) : bounds[2];
                shape.highestFloor = shape.hasFloor ? std::max(shape.highestFloor, bounds[5]) : bounds[5];
                shape.floorArea += doubleArea / 2.0;
                shape.hasFloor = true;
            }
        }

        // Which pairs of sectors a door stands between: its faces lie at the pair's portal.
        std::set<std::pair<size_t, size_t>> doorLinks;

        if (map.state)
        {
            for (const Game::MapDeltaDoor &door : map.state->doors)
            {
                std::array<double, 6> bounds = {1.0e9, 1.0e9, 1.0e9, -1.0e9, -1.0e9, -1.0e9};

                for (const uint16_t vertexId : door.vertexIds)
                {
                    if (vertexId < indoor.vertices.size())
                    {
                        const Game::IndoorVertex &vertex = indoor.vertices[vertexId];
                        bounds[0] = std::min(bounds[0], static_cast<double>(vertex.x));
                        bounds[1] = std::min(bounds[1], static_cast<double>(vertex.y));
                        bounds[2] = std::min(bounds[2], static_cast<double>(vertex.z));
                        bounds[3] = std::max(bounds[3], static_cast<double>(vertex.x));
                        bounds[4] = std::max(bounds[4], static_cast<double>(vertex.y));
                        bounds[5] = std::max(bounds[5], static_cast<double>(vertex.z));
                    }
                }

                for (const std::pair<const std::pair<size_t, size_t>, std::array<double, 6>> &portal : portalBounds)
                {
                    const double reach = 96.0;
                    const std::array<double, 6> &other = portal.second;

                    if (bounds[0] <= other[3] + reach && bounds[3] >= other[0] - reach && bounds[1] <= other[4] + reach
                        && bounds[4] >= other[1] - reach && bounds[2] <= other[5] + reach
                        && bounds[5] >= other[2] - reach)
                    {
                        doorLinks.insert(portal.first);
                    }
                }
            }
        }

        const auto isPlace = [&shapes](size_t sector)
        {
            return sector < shapes.size() && shapes[sector].hasFloor && shapes[sector].floorArea >= NicheFloorArea;
        };

        YAML::Node spaces(YAML::NodeType::Sequence);
        YAML::Node sectorNumbers(YAML::NodeType::Map);
        double totalArea = 0.0;

        for (size_t sector = 1; sector < shapes.size(); ++sector)
        {
            if (!isPlace(sector))
            {
                continue;
            }

            const SectorShape &shape = shapes[sector];
            YAML::Node space(YAML::NodeType::Map);
            const std::string id = "room:s" + std::to_string(sector);
            space["id"] = id;
            space["kind"] = "room";
            space["size"] = sizeClass(shape.floorArea);
            space["area"] = std::round(shape.floorArea / 1.0e4) / 100.0;

            if (shape.highestFloor - shape.lowestFloor > 1.0)
            {
                space["floor"].push_back(std::round(shape.lowestFloor));
                space["floor"].push_back(std::round(shape.highestFloor));
            }
            else
            {
                space["floor"] = std::round(shape.lowestFloor);
            }

            space["clear_height"] = static_cast<int>(indoor.sectors[sector].maxZ - indoor.sectors[sector].minZ);
            spaces.push_back(space);
            sectorNumbers[id] = static_cast<int>(sector);
            totalArea += shape.floorArea;
        }

        YAML::Node planLinks(YAML::NodeType::Sequence);

        for (const std::pair<size_t, size_t> &link : links)
        {
            if (!isPlace(link.first) || !isPlace(link.second))
            {
                continue;
            }

            YAML::Node node(YAML::NodeType::Map);
            node["id"] = "link:s" + std::to_string(link.first) + "_s" + std::to_string(link.second);
            node["from"] = "room:s" + std::to_string(link.first);
            node["to"] = "room:s" + std::to_string(link.second);
            node["kind"] = doorLinks.contains(link) ? "door" : "open";
            planLinks.push_back(node);
        }

        if (spaces.size() > 0)
        {
            plan["spaces"] = spaces;
            lock["sectors"] = sectorNumbers;
        }

        if (planLinks.size() > 0)
        {
            plan["links"] = planLinks;
        }

        totals["sectors"] = static_cast<int>(spaces.size());
        totals["links"] = static_cast<int>(planLinks.size());
        totals["floor_area_millions"] = std::round(totalArea / 1.0e4) / 100.0;
        totals["spawn_points"] = static_cast<int>(indoor.spawns.size());
        totals["lights"] = static_cast<int>(indoor.lights.size());
        totals["decorations"] = static_cast<int>(indoor.entities.size());

        // The scene's own things an overlay changes or removes, under stable ids.
        if (map.indoorScene)
        {
            lockBaseSceneThings(*map.indoorScene, lock);

            // Its cinematics, which an overlay's of the same name replaces (S8a).
            if (map.cinematicsText)
            {
                lockBaseCinematics(*map.cinematicsText, lock);
            }

            const Game::IndoorSceneData &scene = *map.indoorScene;

            for (const std::pair<const char *, size_t> &count : {std::pair<const char *, size_t>{"pulsing_lights",
                     scene.pulsingLights.size()}, {"ambient_sounds", scene.ambientSounds.size()},
                     {"destructibles", scene.destructibles.size()}, {"water_volumes", scene.waterVolumes.size()}})
            {
                if (count.second > 0)
                {
                    totals[count.first] = static_cast<int>(count.second);
                }
            }
        }
    }
    else if (map.outdoor)
    {
        totals["bmodels"] = static_cast<int>(map.outdoor->bmodels.size());
        totals["spawn_points"] = static_cast<int>(map.outdoor->spawns.size());
        totals["decorations"] = static_cast<int>(map.outdoor->entities.size());
    }

    plan["totals"] = totals;
    plan["notes"] = "Derived from " + map.fileName + " by oymap import. The geometry stays in the base map.";

    const std::vector<std::pair<std::string, std::pair<YAML::Node, std::string>>> files = {
        {"project.yml", {card, "project.schema.json"}},
        {"plan.yml", {plan, "plan.schema.json"}},
        {"ids.lock.yml", {lock, "ids_lock.schema.json"}},
    };

    for (const std::pair<std::string, std::pair<YAML::Node, std::string>> &file : files)
    {
        const std::string text = writeCanonicalYaml(file.second.first, schemas, file.second.second);

        if (!writeTextFileAtomically(projectDirectory / file.first, text, errorMessage))
        {
            return false;
        }

        writtenFiles.push_back(file.first);
    }

    return true;
}
}
