#include "core/Things.h"

#include "core/CoreMath.h"
#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <optional>
#include <set>

#include <yaml-cpp/yaml.h>

// The interactive things of an indoor map, for a person or an agent to look at each (the user's walk through
// Gharik's Forge, 2026-11-13): faces are grouped by the event a click on them runs; a decoration with an event is a
// thing of its own. What the event does comes from `oymap flow` (the first path through its handler). Where a player
// uses it: in front of it, along the summed outward normals of its upright faces (a plate on a wall, a lever on its
// post, a door), or, where they cancel out (a free-standing chest, a decoration), along the first side that has a
// floor and a clear view, 176 away (more for a large door), on the highest floor there no higher than its top.

namespace OpenYAMM::Studio
{
namespace
{
constexpr double PartyEye = 160.0;
constexpr double StandDistance = 176.0;

struct Face3
{
    std::vector<std::array<double, 3>> points;
    std::array<double, 3> normal = {};
    double offset = 0.0;
    double area = 0.0;
    bool drawn = false;
};

std::vector<Face3> facesAt(const Game::IndoorMapData &map, const Game::MapDeltaData *pState,
    const std::vector<Game::IndoorVertex> &vertices)
{
    std::vector<Face3> faces(map.faces.size());

    for (size_t index = 0; index < map.faces.size(); ++index)
    {
        const Game::IndoorFace &face = map.faces[index];
        Face3 &built = faces[index];
        const uint32_t attributes = pState != nullptr && index < pState->faceAttributes.size()
            ? pState->faceAttributes[index] : face.attributes;

        for (const uint16_t vertex : face.vertexIndices)
        {
            if (vertex < vertices.size())
            {
                built.points.push_back({static_cast<double>(vertices[vertex].x),
                    static_cast<double>(vertices[vertex].y), static_cast<double>(vertices[vertex].z)});
            }
        }

        if (built.points.size() < 3 || built.points.size() != face.vertexIndices.size())
        {
            built.points.clear();
            continue;
        }

        std::array<double, 3> normal = {};

        for (size_t corner = 0; corner < built.points.size(); ++corner)
        {
            const std::array<double, 3> &current = built.points[corner];
            const std::array<double, 3> &next = built.points[(corner + 1) % built.points.size()];
            normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
            normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
            normal[2] += (current[0] - next[0]) * (current[1] + next[1]);
        }

        const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

        if (length < 1.0e-6)
        {
            built.points.clear();
            continue;
        }

        built.area = length / 2.0;

        for (int axis = 0; axis < 3; ++axis)
        {
            built.normal[axis] = normal[axis] / length;
        }

        built.offset = built.normal[0] * built.points[0][0] + built.normal[1] * built.points[0][1]
            + built.normal[2] * built.points[0][2];
        built.drawn = !face.isPortal && !Game::hasFaceAttribute(attributes, Game::FaceAttribute::IsPortal)
            && !Game::hasFaceAttribute(attributes, Game::FaceAttribute::Invisible);
    }

    return faces;
}

bool insideXY(const std::vector<std::array<double, 3>> &polygon, double x, double y)
{
    bool inside = false;

    for (size_t index = 0, previous = polygon.size() - 1; index < polygon.size(); previous = index++)
    {
        const std::array<double, 3> &a = polygon[index];
        const std::array<double, 3> &b = polygon[previous];

        if ((a[1] > y) != (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0])
        {
            inside = !inside;
        }
    }

    return inside;
}

// The highest floor at a point no higher than `ceiling`.
std::optional<double> floorUnder(const std::vector<Face3> &faces, double x, double y, double ceiling)
{
    std::optional<double> best;

    for (const Face3 &face : faces)
    {
        if (face.points.empty() || face.normal[2] < 0.6 || !insideXY(face.points, x, y))
        {
            continue;
        }

        const double z = (face.offset - face.normal[0] * x - face.normal[1] * y) / face.normal[2];

        if (z <= ceiling + 0.5 && (!best || z > *best))
        {
            best = z;
        }
    }

    return best;
}

// Whether the segment from `from` to `to` passes through no solid drawn face other than `own`'s.
bool clearLine(const std::vector<Face3> &faces, const std::set<uint32_t> &own, const std::array<double, 3> &from,
    const std::array<double, 3> &to)
{
    for (size_t index = 0; index < faces.size(); ++index)
    {
        const Face3 &face = faces[index];

        if (face.points.empty() || !face.drawn || own.contains(static_cast<uint32_t>(index)))
        {
            continue;
        }

        const double a = face.normal[0] * from[0] + face.normal[1] * from[1] + face.normal[2] * from[2] - face.offset;
        const double b = face.normal[0] * to[0] + face.normal[1] * to[1] + face.normal[2] * to[2] - face.offset;

        if ((a > 0.0) == (b > 0.0) || std::abs(a - b) < 1.0e-9)
        {
            continue;
        }

        const double share = a / (a - b);
        const std::array<double, 3> hit = {from[0] + (to[0] - from[0]) * share, from[1] + (to[1] - from[1]) * share,
            from[2] + (to[2] - from[2]) * share};
        // Inside the polygon: the hit lies on the inner side of every edge (faces are convex).
        bool inside = true;
        const size_t count = face.points.size();

        for (size_t corner = 0; corner < count && inside; ++corner)
        {
            const std::array<double, 3> &p = face.points[corner];
            const std::array<double, 3> &q = face.points[(corner + 1) % count];
            const std::array<double, 3> edge = {q[0] - p[0], q[1] - p[1], q[2] - p[2]};
            const std::array<double, 3> toHit = {hit[0] - p[0], hit[1] - p[1], hit[2] - p[2]};
            const std::array<double, 3> crossed = {edge[1] * toHit[2] - edge[2] * toHit[1],
                edge[2] * toHit[0] - edge[0] * toHit[2], edge[0] * toHit[1] - edge[1] * toHit[0]};
            inside = crossed[0] * face.normal[0] + crossed[1] * face.normal[1] + crossed[2] * face.normal[2] >= -1.0e-6;
        }

        if (inside)
        {
            return false;
        }
    }

    return true;
}

std::string named(const std::map<int, std::string> &names, int number, const std::string &word)
{
    const std::map<int, std::string>::const_iterator name = names.find(number);
    return name != names.end() ? name->second : word + " " + std::to_string(number);
}

std::string texturesText(const std::map<std::string, int> &textures)
{
    std::string text;

    for (const std::pair<const std::string, int> &texture : textures)
    {
        text += (text.empty() ? "" : ", ") + texture.first + " " + std::to_string(texture.second);
    }

    return text;
}
}

std::vector<InteractiveThing> listInteractiveThings(
    const LoadedMap &map,
    const std::string &flowJson,
    const CoplanarNames &names)
{
    std::vector<InteractiveThing> things;

    if (!map.indoor)
    {
        return things;
    }

    const Game::IndoorMapData &indoor = *map.indoor;
    const Game::MapDeltaData *pState = map.state ? &*map.state : nullptr;
    const std::vector<Game::IndoorVertex> vertices =
        Game::buildIndoorMechanismAdjustedVertices(indoor, pState, nullptr);
    const std::vector<Face3> faces = facesAt(indoor, pState, vertices);
    const std::map<uint32_t, uint32_t> doorOfFace = doorOfFaces(pState);
    std::map<uint32_t, const Game::MapDeltaDoor *> doors;

    if (pState != nullptr)
    {
        for (const Game::MapDeltaDoor &door : pState->doors)
        {
            doors[door.doorId] = &door;
        }
    }

    // What each handler does on its first path, and its title.
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

    std::map<int, std::vector<uint32_t>> facesByEvent;

    for (size_t index = 0; index < indoor.faces.size(); ++index)
    {
        if (indoor.faces[index].cogTriggered != 0 && !faces[index].points.empty())
        {
            facesByEvent[indoor.faces[index].cogTriggered].push_back(static_cast<uint32_t>(index));
        }
    }

    const std::vector<CoplanarPair> coplanar = findCoplanarFaces(indoor, pState);

    for (const std::pair<const int, std::vector<uint32_t>> &group : facesByEvent)
    {
        InteractiveThing thing;
        thing.eventId = group.first;
        thing.title = titleOf[group.first];
        thing.faces = group.second;
        thing.effects = effectsOf[group.first];
        const std::set<uint32_t> own(thing.faces.begin(), thing.faces.end());
        bool first = true;
        std::array<double, 3> outward = {};
        double uprightArea = 0.0;
        std::set<uint32_t> ownDoors;

        for (const uint32_t face : thing.faces)
        {
            thing.textures[indoor.faces[face].textureName] += 1;
            thing.sector = indoor.faces[face].roomNumber;

            for (const std::array<double, 3> &point : faces[face].points)
            {
                for (int axis = 0; axis < 3; ++axis)
                {
                    thing.low[axis] = first ? point[axis] : std::min(thing.low[axis], point[axis]);
                    thing.high[axis] = first ? point[axis] : std::max(thing.high[axis], point[axis]);
                }

                first = false;
            }

            if (std::abs(faces[face].normal[2]) < 0.5)
            {
                outward[0] += faces[face].normal[0] * faces[face].area;
                outward[1] += faces[face].normal[1] * faces[face].area;
                uprightArea += faces[face].area;
            }

            if (doorOfFace.contains(face))
            {
                ownDoors.insert(doorOfFace.at(face));
            }
        }

        thing.ownDoors.assign(ownDoors.begin(), ownDoors.end());

        for (int axis = 0; axis < 3; ++axis)
        {
            thing.middle[axis] = (thing.low[axis] + thing.high[axis]) / 2.0;
        }

        // What it is.
        const auto effectStarts = [&thing](const std::string &start)
        {
            return std::any_of(thing.effects.begin(), thing.effects.end(), [&start](const std::string &effect)
            {
                return effect.rfind(start, 0) == 0;
            });
        };
        bool movesOwnDoor = false;
        uint32_t ownMoved = 0;

        for (const std::string &effect : thing.effects)
        {
            unsigned doorId = 0;

            if (std::sscanf(effect.c_str(), "door %u", &doorId) == 1 && ownDoors.contains(doorId))
            {
                movesOwnDoor = true;
                ownMoved = doorId;
            }
        }

        if (effectStarts("open chest"))
        {
            thing.kind = "chest";
        }
        else if (effectStarts("leave to"))
        {
            thing.kind = "exit";
        }
        else if (effectStarts("teleport to"))
        {
            thing.kind = "teleport";
        }
        else if (movesOwnDoor && doors.contains(ownMoved))
        {
            const Game::MapDeltaDoor &door = *doors.at(ownMoved);
            const double extent = std::max({thing.high[0] - thing.low[0], thing.high[1] - thing.low[1],
                thing.high[2] - thing.low[2]});
            thing.kind = extent > 96.0 ? "door"
                : std::abs(door.directionZ) > std::max(std::abs(door.directionX), std::abs(door.directionY))
                ? "lever" : "button";
        }
        else if (effectStarts("door ") || effectStarts("SetTexture"))
        {
            thing.kind = "switch";
        }
        else
        {
            thing.kind = "panel";
        }

        thing.safeToUse = thing.kind != "chest" && thing.kind != "exit" && thing.kind != "teleport"
            && !effectStarts("AskQuestion") && !effectStarts("MoveToMap");

        // What it changes: the faces of the doors it moves and of the textures it sets.
        for (const std::string &effect : thing.effects)
        {
            unsigned doorId = 0;
            int cog = 0;
            char textureName[64] = {};
            std::map<std::string, int> textures;
            size_t count = 0;

            if (std::sscanf(effect.c_str(), "door %u", &doorId) == 1 && doors.contains(doorId))
            {
                for (const uint16_t face : doors.at(doorId)->faceIds)
                {
                    if (face < indoor.faces.size())
                    {
                        textures[indoor.faces[face].textureName] += 1;
                        ++count;
                    }
                }

                thing.changes.push_back(effect + " (" + named(names.doors, static_cast<int>(doorId), "door") + "): "
                    + std::to_string(count) + " faces (" + texturesText(textures) + ")");
            }
            else if (std::sscanf(effect.c_str(), "SetTexture(%d, %63[^)])", &cog, textureName) == 2)
            {
                for (size_t face = 0; face < indoor.faces.size(); ++face)
                {
                    if ((cog > 0 && indoor.faces[face].cogNumber == cog) || (cog < 0 && face == size_t(-cog)))
                    {
                        textures[indoor.faces[face].textureName] += 1;
                        ++count;
                    }
                }

                thing.changes.push_back(effect + ": " + std::to_string(count) + " faces (" + texturesText(textures)
                    + ")");
            }
        }

        // Where a player uses it from.
        // (A small handle is looked at from closer.)
        const double reach = thing.kind == "lever" || thing.kind == "button" ? 128.0
            : std::max(StandDistance, 0.9 * std::max(thing.high[0] - thing.low[0], thing.high[1] - thing.low[1]));
        std::vector<std::array<double, 2>> directions;
        const double summed = oy::hypot(outward[0], outward[1]);

        if (uprightArea > 0.0 && summed >= 0.25 * uprightArea)
        {
            // A lever's arm or a button points at a player straight in front of it: seen a little from the side
            // first, where it shows how far it stands out and moves.
            if (thing.kind == "lever" || thing.kind == "button")
            {
                for (const double turn : {0.6, -0.6})
                {
                    directions.push_back({(outward[0] * oy::cos(turn) - outward[1] * oy::sin(turn)) / summed,
                        (outward[0] * oy::sin(turn) + outward[1] * oy::cos(turn)) / summed});
                }
            }

            directions.push_back({outward[0] / summed, outward[1] / summed});
        }

        for (int step = 0; step < 8; ++step)
        {
            const double angle = step * 3.14159265358979323846 / 4.0;
            directions.push_back({oy::cos(angle), oy::sin(angle)});
        }

        bool placed = false;

        // Nearer where nothing is found at the full distance (XD-04's cabinet in a cupboard 128 deep: its stand
        // point lay 160 behind the cupboard's wall).
        for (const double share : {1.0, 0.75, 0.5, 0.35})
        {
            for (const std::array<double, 2> &direction : directions)
            {
                if (placed || (share < 1.0 && reach * share < 48.0))
                {
                    break;
                }

                const double x = thing.middle[0] + direction[0] * reach * share;
                const double y = thing.middle[1] + direction[1] * reach * share;
                const std::optional<double> floor = floorUnder(faces, x, y, thing.high[2] + 64.0);

                if (!floor || !clearLine(faces, own, {x, y, *floor + PartyEye}, thing.middle))
                {
                    continue;
                }

                thing.stand = {std::round(x), std::round(y), std::round(*floor)};
                placed = true;
            }
        }

        if (!placed)
        {
            const std::array<double, 2> &direction = directions.front();
            const double x = thing.middle[0] + direction[0] * reach;
            const double y = thing.middle[1] + direction[1] * reach;
            thing.stand = {std::round(x), std::round(y),
                std::round(floorUnder(faces, x, y, thing.high[2] + 64.0).value_or(thing.low[2]))};
            thing.overlaps.push_back("no place with a floor and a clear view found within " + std::to_string(
                static_cast<int>(reach)) + " of it; the picture is taken from in front of it all the same");
        }

        const double dx = thing.middle[0] - thing.stand[0];
        const double dy = thing.middle[1] - thing.stand[1];
        thing.yaw = oy::atan2(dy, dx);
        thing.pitch = oy::atan2(thing.middle[2] - (thing.stand[2] + PartyEye), oy::hypot(dx, dy));

        // Faces in one plane over its own or over those it changes.
        std::set<uint32_t> involved = own;

        for (const std::string &effect : thing.effects)
        {
            unsigned doorId = 0;

            if (std::sscanf(effect.c_str(), "door %u", &doorId) == 1 && doors.contains(doorId))
            {
                involved.insert(doors.at(doorId)->faceIds.begin(), doors.at(doorId)->faceIds.end());
            }
        }

        for (const CoplanarPair &pair : coplanar)
        {
            if (involved.contains(pair.firstFace) || involved.contains(pair.secondFace))
            {
                thing.overlaps.push_back(describeCoplanarPair(indoor, pState, pair, names));
            }
        }

        // A clicked upright face that lies over more than one face of the wall behind it (within 4 units), or
        // hangs off it.
        for (const uint32_t face : thing.faces)
        {
            const Face3 &front = faces[face];

            if (std::abs(front.normal[2]) > 0.5)
            {
                continue;
            }

            std::map<std::string, int> behind;
            double covered = 0.0;

            for (size_t other = 0; other < faces.size(); ++other)
            {
                const Face3 &wall = faces[other];

                if (wall.points.empty() || !wall.drawn || own.contains(static_cast<uint32_t>(other))
                    || wall.normal[0] * front.normal[0] + wall.normal[1] * front.normal[1]
                            + wall.normal[2] * front.normal[2] < 0.999
                    || front.offset - wall.offset < 0.5 || front.offset - wall.offset > 4.0)
                {
                    continue;
                }

                const double area = projectedOverlapArea(front.points, wall.points, front.normal);

                if (area > 1.0)
                {
                    behind[indoor.faces[other].textureName] += 1;
                    covered += area;
                }
            }

            if (behind.empty())
            {
                continue;
            }

            int count = 0;

            for (const std::pair<const std::string, int> &texture : behind)
            {
                count += texture.second;
            }

            if (count > 1 || covered < front.area - 1.0)
            {
                thing.overlaps.push_back("face " + std::to_string(face) + " (" + indoor.faces[face].textureName
                    + ") lies over " + (count > 1 ? std::to_string(count) + " faces of the wall behind it ("
                        + texturesText(behind) + "): it is not wholly on one wall face"
                        : "a wall face (" + texturesText(behind) + ") that covers only "
                            + std::to_string(static_cast<int>(covered)) + " of its "
                            + std::to_string(static_cast<int>(front.area)) + " square units: it hangs off it"));
            }
        }

        things.push_back(thing);
    }

    // Clicked decorations.
    for (size_t index = 0; index < indoor.entities.size(); ++index)
    {
        const Game::IndoorEntity &entity = indoor.entities[index];

        if (entity.scriptEventId() == 0)
        {
            continue;
        }

        InteractiveThing thing;
        thing.eventId = entity.scriptEventId();
        thing.title = titleOf[thing.eventId];
        thing.kind = "decoration";
        thing.effects = effectsOf[thing.eventId];
        thing.textures[entity.name] = 1;
        thing.low = {double(entity.x), double(entity.y), double(entity.z)};
        thing.high = thing.low;
        thing.middle = {double(entity.x), double(entity.y), double(entity.z) + 48.0};
        // The sector it stands in, as the game finds a point's (Castle Darkmoor's crystal was "in sector 0").
        thing.sector = Game::findIndoorSectorForPoint(indoor, indoor.vertices,
            {float(entity.x), float(entity.y), float(entity.z) + 16.0f}).value_or(0);

        for (int step = 0; step < 8; ++step)
        {
            const double angle = step * 3.14159265358979323846 / 4.0;
            const double x = thing.middle[0] + oy::cos(angle) * StandDistance;
            const double y = thing.middle[1] + oy::sin(angle) * StandDistance;
            const std::optional<double> floor = floorUnder(faces, x, y, thing.middle[2] + 64.0);

            if (floor && clearLine(faces, {}, {x, y, *floor + PartyEye}, thing.middle))
            {
                thing.stand = {std::round(x), std::round(y), std::round(*floor)};
                break;
            }
        }

        const double dx = thing.middle[0] - thing.stand[0];
        const double dy = thing.middle[1] - thing.stand[1];
        thing.yaw = oy::atan2(dy, dx);
        thing.pitch = oy::atan2(thing.middle[2] - (thing.stand[2] + PartyEye), oy::hypot(dx, dy));
        thing.safeToUse = false;
        things.push_back(thing);
    }

    std::sort(things.begin(), things.end(), [](const InteractiveThing &left, const InteractiveThing &right)
    {
        return left.eventId < right.eventId;
    });
    return things;
}
}
