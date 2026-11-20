#include "core/OutdoorInteractive.h"

#include "core/CoreMath.h"
#include "game/FaceEnums.h"

#include <algorithm>
#include <cmath>
#include <set>

#include <yaml-cpp/yaml.h>

namespace OpenYAMM::Studio
{
namespace
{
constexpr double PartyEye = 160.0;
constexpr double StandDistance = 256.0;

// The terrain's height at a world point: the cell's two triangles as the game lays them (between the north-west and
// south-east corners), from the 128 x 128 height map in steps of 32.
double groundAt(const Game::OutdoorMapData &map, double x, double y)
{
    constexpr int Side = Game::OutdoorMapData::TerrainWidth;
    constexpr double Cell = Game::OutdoorMapData::TerrainTileSize;

    if (map.heightMap.size() < static_cast<size_t>(Side) * Side)
    {
        return 0.0;
    }

    const double gridX = std::clamp(x / Cell + Side / 2.0, 0.0, Side - 1.001);
    const double gridY = std::clamp(Side / 2.0 - y / Cell, 0.0, Side - 1.001);
    const int column = static_cast<int>(gridX);
    const int row = static_cast<int>(gridY);
    const auto height = [&map](int at, int on)
    {
        return static_cast<double>(map.heightMap[static_cast<size_t>(std::min(on, Side - 1)) * Side
            + std::min(at, Side - 1)]) * Game::OutdoorMapData::TerrainHeightScale;
    };
    const double u = gridX - column;
    const double v = gridY - row;
    const double northWest = height(column, row);
    const double northEast = height(column + 1, row);
    const double southWest = height(column, row + 1);
    const double southEast = height(column + 1, row + 1);

    if (u >= v)
    {
        return northWest + (northEast - northWest) * u + (southEast - northEast) * v;
    }

    return northWest + (southEast - southWest) * u + (southWest - northWest) * v;
}
}

std::vector<InteractiveThing> listOutdoorInteractiveThings(
    const LoadedMap &map,
    const std::string &flowJson,
    std::map<int, std::string> &modelNames)
{
    std::vector<InteractiveThing> things;

    if (!map.outdoor)
    {
        return things;
    }

    const Game::OutdoorMapData &outdoor = *map.outdoor;
    std::map<int, std::vector<std::string>> effectsOf;
    std::map<int, std::string> titleOf;

    try
    {
        const YAML::Node events = flowJson.empty() ? YAML::Node() : YAML::Load(flowJson);

        for (const YAML::Node &event : events)
        {
            const int id = event["event"].as<int>();
            titleOf[id] = event["title"] ? event["title"].as<std::string>() : std::string();

            if (event["paths"] && event["paths"].size() > 0)
            {
                for (const YAML::Node &effect : event["paths"][0]["effects"])
                {
                    effectsOf[id].push_back(effect.as<std::string>());
                }
            }
        }
    }
    catch (const YAML::Exception &)
    {
        effectsOf.clear();
    }

    const auto describe = [&](InteractiveThing &thing)
    {
        if (titleOf.contains(thing.eventId))
        {
            thing.title = titleOf.at(thing.eventId);
        }
        else if (map.events)
        {
            // An event with a name and no handler (a ship's hull, a house's walls).
            thing.title = map.events->getHint(static_cast<uint16_t>(thing.eventId)).value_or(std::string());
        }

        thing.effects = effectsOf[thing.eventId];
        const auto effectStarts = [&thing](const std::string &start)
        {
            return std::any_of(thing.effects.begin(), thing.effects.end(), [&start](const std::string &effect)
            {
                return effect.rfind(start, 0) == 0;
            });
        };

        if (thing.kind.empty())
        {
            thing.kind = effectStarts("EnterHouse") ? "house"
                : effectStarts("open chest") ? "chest"
                : effectStarts("leave to") || effectStarts("MoveToMap") ? "exit"
                : effectStarts("teleport to") ? "teleport"
                : thing.effects.empty() ? "name" : "panel";
        }

        thing.safeToUse = thing.kind != "chest" && thing.kind != "exit" && thing.kind != "teleport"
            && thing.kind != "house" && !effectStarts("AskQuestion") && !effectStarts("MoveToMap")
            && !effectStarts("EnterHouse");
    };

    // The models' faces by event.
    std::map<int, std::vector<uint32_t>> facesByEvent;

    for (size_t model = 0; model < outdoor.bmodels.size(); ++model)
    {
        modelNames[static_cast<int>(model)] = outdoor.bmodels[model].name;
        const std::vector<Game::OutdoorBModelFace> &faces = outdoor.bmodels[model].faces;

        for (size_t face = 0; face < faces.size() && face < 65536; ++face)
        {
            if (faces[face].cogTriggeredNumber != 0 && faces[face].vertexIndices.size() >= 3)
            {
                facesByEvent[faces[face].cogTriggeredNumber].push_back(
                    static_cast<uint32_t>(model * 65536 + face));
            }
        }
    }

    for (const std::pair<const int, std::vector<uint32_t>> &group : facesByEvent)
    {
        InteractiveThing thing;
        thing.eventId = group.first;
        thing.faces = group.second;
        bool first = true;
        std::array<double, 3> outward = {};
        std::map<int, size_t> facesOfModel;
        double largest = -1.0;
        std::array<double, 3> largestMiddle = {};
        std::array<double, 2> largestNormal = {0.0, -1.0};

        for (const uint32_t packed : thing.faces)
        {
            const Game::OutdoorBModel &model = outdoor.bmodels[packed / 65536];
            const Game::OutdoorBModelFace &face = model.faces[packed % 65536];
            thing.textures[face.textureName] += 1;
            facesOfModel[static_cast<int>(packed / 65536)] += 1;
            std::vector<std::array<double, 3>> points;

            for (const uint16_t vertex : face.vertexIndices)
            {
                if (vertex < model.vertices.size())
                {
                    points.push_back({static_cast<double>(model.vertices[vertex].x),
                        static_cast<double>(model.vertices[vertex].y), static_cast<double>(model.vertices[vertex].z)});
                }
            }

            if (points.size() < 3)
            {
                continue;
            }

            std::array<double, 3> normal = {};
            std::array<double, 3> middle = {};

            for (size_t corner = 0; corner < points.size(); ++corner)
            {
                const std::array<double, 3> &current = points[corner];
                const std::array<double, 3> &next = points[(corner + 1) % points.size()];
                normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
                normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
                normal[2] += (current[0] - next[0]) * (current[1] + next[1]);

                for (int axis = 0; axis < 3; ++axis)
                {
                    thing.low[axis] = first ? current[axis] : std::min(thing.low[axis], current[axis]);
                    thing.high[axis] = first ? current[axis] : std::max(thing.high[axis], current[axis]);
                    middle[axis] += current[axis] / points.size();
                }

                first = false;
            }

            const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

            if (length < 1.0e-6)
            {
                continue;
            }

            // The way the face looks: its stored plane's normal.
            const double area = length / 2.0;
            const std::array<double, 3> unit = {face.planeNormalX / 65536.0, face.planeNormalY / 65536.0,
                face.planeNormalZ / 65536.0};
            const bool hidden = Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible);

            if (std::abs(unit[2]) < 0.5 && !hidden)
            {
                outward[0] += unit[0] * area;
                outward[1] += unit[1] * area;

                if (area > largest)
                {
                    largest = area;
                    largestMiddle = middle;
                    largestNormal = {unit[0], unit[1]};
                }
            }
        }

        thing.sector = std::max_element(facesOfModel.begin(), facesOfModel.end(),
            [](const std::pair<const int, size_t> &a, const std::pair<const int, size_t> &b)
            {
                return a.second < b.second;
            })->first;

        for (int axis = 0; axis < 3; ++axis)
        {
            thing.middle[axis] = (thing.low[axis] + thing.high[axis]) / 2.0;
        }

        // In front of the largest upright face when the faces look one way (a door, a sign's board); along their
        // summed look else; south of a thing whose faces cancel out (a well, a chest seen from every side).
        std::array<double, 2> look = largestNormal;
        std::array<double, 3> target = largest > 0.0 ? largestMiddle : thing.middle;
        const double summed = oy::hypot(outward[0], outward[1]);

        if (largest <= 0.0 && summed > 1.0e-6)
        {
            look = {outward[0] / summed, outward[1] / summed};
        }

        const double reach = StandDistance + std::max(thing.high[0] - thing.low[0], thing.high[1] - thing.low[1])
            * (largest > 0.0 ? 0.0 : 0.5);
        thing.stand = {target[0] + look[0] * reach, target[1] + look[1] * reach, 0.0};
        thing.stand[2] = groundAt(outdoor, thing.stand[0], thing.stand[1]);
        thing.middle = target;
        thing.yaw = oy::atan2(target[1] - thing.stand[1], target[0] - thing.stand[0]);
        thing.pitch = oy::atan2(target[2] - (thing.stand[2] + PartyEye),
            oy::hypot(target[0] - thing.stand[0], target[1] - thing.stand[1]));
        describe(thing);
        things.push_back(thing);
    }

    // Decorations that run an event when clicked: no model holds them.
    modelNames[-1] = "no model (a decoration)";

    for (size_t index = 0; index < outdoor.entities.size(); ++index)
    {
        const Game::OutdoorEntity &entity = outdoor.entities[index];

        if (entity.scriptEventId() == 0)
        {
            continue;
        }

        InteractiveThing thing;
        thing.eventId = entity.scriptEventId();
        thing.kind = "decoration";
        thing.sector = -1;
        thing.textures[entity.name] = 1;
        thing.middle = {static_cast<double>(entity.x), static_cast<double>(entity.y), static_cast<double>(entity.z)
            + 64.0};
        thing.low = {static_cast<double>(entity.x), static_cast<double>(entity.y), static_cast<double>(entity.z)};
        thing.high = thing.middle;
        thing.stand = {thing.middle[0], thing.middle[1] - StandDistance, 0.0};
        thing.stand[2] = groundAt(outdoor, thing.stand[0], thing.stand[1]);
        thing.yaw = oy::atan2(thing.middle[1] - thing.stand[1], thing.middle[0] - thing.stand[0]);
        thing.pitch = oy::atan2(thing.middle[2] - (thing.stand[2] + PartyEye), StandDistance);
        describe(thing);
        thing.kind = "decoration";
        things.push_back(thing);
    }

    return things;
}
}
