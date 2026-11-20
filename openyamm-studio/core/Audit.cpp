#include "core/Audit.h"

#include "core/Coplanar.h"
#include "core/Compare.h"
#include "core/EyeSector.h"
#include "core/Looks.h"
#include "core/Reachability.h"

#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <sstream>
#include <map>
#include <regex>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
std::string joinNumbers(const std::vector<size_t> &numbers, size_t limit = 8)
{
    std::string text;

    for (size_t index = 0; index < numbers.size() && index < limit; ++index)
    {
        text += (index == 0 ? "" : ", ") + std::to_string(numbers[index]);
    }

    if (numbers.size() > limit)
    {
        text += " and " + std::to_string(numbers.size() - limit) + " more";
    }

    return text;
}

struct Bindings
{
    // Event number to the faces and decorations that call it.
    std::map<uint16_t, std::vector<size_t>> faces;
    std::map<uint16_t, std::vector<size_t>> decorations;
};

Bindings collectBindings(const LoadedMap &map)
{
    Bindings bindings;

    if (map.indoor)
    {
        for (size_t index = 0; index < map.indoor->faces.size(); ++index)
        {
            if (map.indoor->faces[index].cogTriggered != 0)
            {
                bindings.faces[map.indoor->faces[index].cogTriggered].push_back(index);
            }
        }

        for (size_t index = 0; index < map.indoor->entities.size(); ++index)
        {
            if (map.indoor->entities[index].scriptEventId() != 0)
            {
                bindings.decorations[map.indoor->entities[index].scriptEventId()].push_back(index);
            }
        }
    }

    if (map.outdoor)
    {
        size_t faceNumber = 0;

        for (const Game::OutdoorBModel &bmodel : map.outdoor->bmodels)
        {
            for (const Game::OutdoorBModelFace &face : bmodel.faces)
            {
                if (face.cogTriggeredNumber != 0)
                {
                    bindings.faces[face.cogTriggeredNumber].push_back(faceNumber);
                }

                ++faceNumber;
            }
        }

        for (size_t index = 0; index < map.outdoor->entities.size(); ++index)
        {
            if (map.outdoor->entities[index].scriptEventId() != 0)
            {
                bindings.decorations[map.outdoor->entities[index].scriptEventId()].push_back(index);
            }
        }
    }

    return bindings;
}
}

MapOverview overviewOf(const LoadedMap &map)
{
    MapOverview overview;

    if (map.indoor)
    {
        overview.sectors = map.indoor->sectors.size();
        overview.faces = map.indoor->faces.size();
        overview.spawns = map.indoor->spawns.size();
        overview.decorations = map.indoor->entities.size();
        overview.lights = map.indoor->lights.size();
    }

    if (map.outdoor)
    {
        overview.bmodels = map.outdoor->bmodels.size();
        overview.spawns = map.outdoor->spawns.size();
        overview.decorations = map.outdoor->entities.size();

        for (const Game::OutdoorBModel &bmodel : map.outdoor->bmodels)
        {
            overview.faces += bmodel.faces.size();
        }
    }

    if (map.state)
    {
        overview.doors = map.state->doors.size();
        overview.actors = map.state->actors.size();
        overview.chests = map.state->chests.size();
    }

    if (map.indoorScene)
    {
        overview.containers = map.indoorScene->itemSources.lootContainers.size();
    }
    else if (map.outdoorScene)
    {
        overview.containers = map.outdoorScene->itemSources.lootContainers.size();
    }

    if (map.events)
    {
        overview.handlers = map.events->eventIds().size();
    }

    const Bindings bindings = collectBindings(map);
    std::set<uint16_t> bound;

    for (const std::pair<const uint16_t, std::vector<size_t>> &entry : bindings.faces)
    {
        bound.insert(entry.first);
    }

    for (const std::pair<const uint16_t, std::vector<size_t>> &entry : bindings.decorations)
    {
        bound.insert(entry.first);
    }

    overview.boundEvents = bound.size();
    return overview;
}

std::vector<AuditFinding> auditWiring(const LoadedMap &map)
{
    std::vector<AuditFinding> findings;

    if (!map.events)
    {
        return findings;
    }

    const Game::ScriptedEventProgram &events = *map.events;
    const Bindings bindings = collectBindings(map);

    // What the map calls must be handled.
    const auto reportUnhandled = [&events, &findings](
                                     const std::map<uint16_t, std::vector<size_t>> &callers, const char *pWhat)
    {
        for (const std::pair<const uint16_t, std::vector<size_t>> &entry : callers)
        {
            // An event registered with a hint but no handler is a house door or a name plate: the engine acts on it.
            if (!events.hasEvent(entry.first) && !events.getHint(entry.first)
                && !events.getContextActionMetadata(entry.first))
            {
                findings.push_back({
                    "event.unhandled",
                    "error",
                    "event " + std::to_string(entry.first) + " is called by " + pWhat + " " + joinNumbers(entry.second)
                        + " but the map's script has no handler for it",
                    "add the handler, or clear the event on those " + std::string(pWhat)});
            }
        }
    };
    reportUnhandled(bindings.faces, "faces");
    reportUnhandled(bindings.decorations, "decorations");

    // A handler nothing can run: not bound, not run on load or leave, not a timer or hook, not a hint, and not
    // named anywhere else in the script (handlers call each other by number).
    std::set<uint16_t> runByEngine;

    for (const std::vector<uint16_t> *pList : {
             &events.onLoadEventIds(), &events.onLeaveEventIds(), &events.canShowTopicEventIds(),
             &events.monsterKilledHookEventIds(), &events.monsterDamageHookEventIds()})
    {
        runByEngine.insert(pList->begin(), pList->end());
    }

    for (const Game::ScriptedEventProgram::TimerTrigger &timer : events.timerTriggers())
    {
        runByEngine.insert(timer.eventId);
    }

    for (const uint16_t eventId : events.eventIds())
    {
        if (bindings.faces.contains(eventId) || bindings.decorations.contains(eventId)
            || runByEngine.contains(eventId))
        {
            continue;
        }

        // Named elsewhere than in its own RegisterEvent line?
        const std::regex mention("\\b" + std::to_string(eventId) + "\\b");
        const size_t mentions = static_cast<size_t>(std::distance(
            std::sregex_iterator(map.scriptText.begin(), map.scriptText.end(), mention), std::sregex_iterator()));
        findings.push_back({
            "event.unbound",
            mentions <= 1 ? "warning" : "info",
            "the handler of event " + std::to_string(eventId)
                + (events.getHint(eventId) ? " (\"" + *events.getHint(eventId) + "\")" : std::string())
                + " is bound to no face or decoration and is not run on load, on leave or by a timer"
                + (mentions <= 1 ? "" : "; its number appears elsewhere in the script, so another handler may run it"),
            "bind it, or remove it if it is a leftover"});
    }

    // The doors the script moves must exist and have something to move.
    if (map.state)
    {
        std::map<uint32_t, const Game::MapDeltaDoor *> doors;

        for (const Game::MapDeltaDoor &door : map.state->doors)
        {
            doors[door.doorId] = &door;
        }

        const std::regex doorCall("SetDoorState\\(\\s*([0-9]+)");
        std::map<uint32_t, size_t> moved;

        for (std::sregex_iterator match(map.scriptText.begin(), map.scriptText.end(), doorCall);
             match != std::sregex_iterator(); ++match)
        {
            ++moved[static_cast<uint32_t>(std::stoul((*match)[1].str()))];
        }

        for (const std::pair<const uint32_t, size_t> &entry : moved)
        {
            const std::map<uint32_t, const Game::MapDeltaDoor *>::const_iterator door = doors.find(entry.first);

            if (door == doors.end())
            {
                findings.push_back({
                    "door.missing",
                    "warning",
                    "the script moves door " + std::to_string(entry.first) + " (" + std::to_string(entry.second)
                        + " calls) but the map has no door with that number",
                    "point the call at an existing door, or add the door"});
            }
            else if (door->second->vertexIds.empty())
            {
                const bool hasFaces = !door->second->faceIds.empty();
                findings.push_back({
                    "door.empty",
                    hasFaces ? "warning" : "error",
                    "the script moves door " + std::to_string(entry.first) + ", which has no vertices: nothing moves"
                        + (hasFaces
                              ? " (its " + std::to_string(door->second->faceIds.size())
                                    + " faces can only shift their textures)"
                              : std::string()),
                    "give the door its geometry, or remove the calls"});
            }
        }

        for (const Game::MapDeltaDoor &door : map.state->doors)
        {
            if (door.doorId != 0 && !moved.contains(door.doorId) && !door.faceIds.empty())
            {
                findings.push_back({
                    "door.unused",
                    "info",
                    "door " + std::to_string(door.doorId) + " is never moved by the map's script",
                    "wire it, or leave it if another script or the engine moves it"});
            }
        }
    }

    return findings;
}

std::vector<AuditFinding> auditCoplanarFaces(
    const LoadedMap &map,
    const std::vector<CoplanarPlace> *pOriginalPlaces,
    bool strict,
    CoplanarSummary &summary,
    const CoplanarNames &names,
    const OutdoorFaceParts &outdoorParts)
{
    std::vector<AuditFinding> findings;

    if (map.outdoor)
    {
        const std::vector<Game::OutdoorBModel> &models = map.outdoor->bmodels;
        std::vector<OutdoorCoplanarPair> pairs = findOutdoorCoplanarFaces(models);
        summary.pairs = pairs.size();
        summary.asOriginal =
            pOriginalPlaces != nullptr ? markOutdoorPairsAsOriginal(models, pairs, *pOriginalPlaces) : 0;

        for (const OutdoorCoplanarPair &pair : pairs)
        {
            findings.push_back({"geometry.coplanar", pair.asOriginal ? "info" : strict ? "error" : "warning",
                describeOutdoorCoplanarPair(models, pair, outdoorParts),
                pair.asOriginal ? "As the original: leave it, or do better than the original."
                    : "Move one face off the other's plane or cut it where the other lies: two parts that are the "
                      "same, or run through each other along a wall, become one part or meet at the wall."});
        }

        return findings;
    }

    if (!map.indoor)
    {
        return findings;
    }

    const Game::MapDeltaData *pState = map.state ? &*map.state : nullptr;
    std::vector<CoplanarPair> pairs = findCoplanarFaces(*map.indoor, pState);
    summary.pairs = pairs.size();
    summary.asOriginal =
        pOriginalPlaces != nullptr ? markPairsAsOriginal(*map.indoor, pairs, *pOriginalPlaces) : 0;

    for (const CoplanarPair &pair : pairs)
    {
        findings.push_back({"geometry.coplanar", pair.asOriginal ? "info" : strict ? "error" : "warning",
            describeCoplanarPair(*map.indoor, pState, pair, names),
            pair.asOriginal ? "As the original: leave it, or do better than the original."
                : "Move one face off the other's plane, cut it where the other lies, or let a moving part stop "
                  "short of the faces beside it."});
    }

    return findings;
}

std::vector<AuditFinding> auditEyeSectors(const LoadedMap &map)
{
    std::vector<AuditFinding> findings;

    if (!map.indoor)
    {
        return findings;
    }

    const Game::MapDeltaData *pState = map.state ? &*map.state : nullptr;

    for (const EyeSectorFinding &finding : findEyeOutsideSector(*map.indoor, pState))
    {
        findings.push_back({"geometry.eye_sector", "warning",
            describeEyeSectorFinding(*map.indoor, pState, finding, {}),
            "Put the floor into the sector whose space the eye is in (one sector for the top and the room over it), "
            "or keep the top a party's height under the room above."});
    }

    return findings;
}

// S8d (outdoor code list item 19, XD-01's stash keg): a solid decoration standing in a doorway's way. A portal of
// the map's that one walks through (upright, at least a party high and wide) and a decoration of the table that
// blocks (no MoveThrough or DontDraw, a radius) within its radius and the party's (37) of the straight line through
// the opening's middle, 0 to 128 to either side of it, catch the party one walk in six.
static void auditDoorwayDecorations(const Game::IndoorMapData &indoor, const std::string &decorationTableText,
    const std::set<int> &hanging, std::vector<AuditFinding> &findings)
{
    constexpr double PartyRadius = 37.0;
    constexpr double Reach = 128.0;
    // A doorway: an opening no wider than this (a wider portal divides a hall).
    constexpr double WidestDoorway = 512.0;
    // Each decoration's radius and whether it blocks, by its list id (its row's number less one): not one the party
    // walks through, not one that hangs on a wall or from a ceiling, not the party's start marker.
    std::map<int, std::pair<double, bool>> solids;
    std::istringstream table(decorationTableText);

    for (std::string line; std::getline(table, line);)
    {
        std::vector<std::string> cells;
        std::istringstream row(line);

        for (std::string cell; std::getline(row, cell, '\t');)
        {
            cells.push_back(cell);
        }

        if (cells.size() >= 12 && !cells[0].empty() && std::isdigit(static_cast<unsigned char>(cells[0][0])))
        {
            const double radius = std::atof(cells[4].c_str());
            std::string names = cells[1] + " " + cells[2];
            std::transform(names.begin(), names.end(), names.begin(), [](unsigned char character)
            {
                return static_cast<char>(std::tolower(character));
            });
            const bool blocks = radius > 0.0 && cells[11].find("MoveThrough") == std::string::npos
                && cells[11].find("DontDraw") == std::string::npos && !decorationHangs(cells[2])
                && names.find("party start") == std::string::npos;
            solids[std::atoi(cells[0].c_str()) - 1] = {radius, blocks};
        }
    }

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size() && !solids.empty(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];

        if ((!face.isPortal && !Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal))
            || face.vertexIndices.size() < 3)
        {
            continue;
        }

        // The opening: its middle, its horizontal normal and the way across it, its width and height.
        std::array<double, 3> middle = {0.0, 0.0, 0.0};
        std::array<double, 3> normal = {0.0, 0.0, 0.0};
        const size_t count = face.vertexIndices.size();
        bool inside = true;

        for (size_t index = 0; index < count; ++index)
        {
            inside = inside && face.vertexIndices[index] < indoor.vertices.size()
                && face.vertexIndices[(index + 1) % count] < indoor.vertices.size();

            if (!inside)
            {
                break;
            }

            const Game::IndoorVertex &a = indoor.vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &b = indoor.vertices[face.vertexIndices[(index + 1) % count]];
            middle = {middle[0] + a.x / static_cast<double>(count), middle[1] + a.y / static_cast<double>(count),
                middle[2] + a.z / static_cast<double>(count)};
            normal[0] += static_cast<double>(a.y - b.y) * (a.z + b.z);
            normal[1] += static_cast<double>(a.z - b.z) * (a.x + b.x);
            normal[2] += static_cast<double>(a.x - b.x) * (a.y + b.y);
        }

        const double horizontal = std::hypot(normal[0], normal[1]);
        const double length = std::hypot(horizontal, normal[2]);

        if (!inside || length <= 0.0 || horizontal < 0.7 * length)
        {
            continue;
        }

        const std::array<double, 2> way = {normal[0] / horizontal, normal[1] / horizontal};
        const std::array<double, 2> across = {-way[1], way[0]};
        double least = 1.0e18;
        double most = -1.0e18;
        double low = 1.0e18;
        double high = -1.0e18;

        for (const uint16_t vertexIndex : face.vertexIndices)
        {
            const Game::IndoorVertex &vertex = indoor.vertices[vertexIndex];
            const double side = (vertex.x - middle[0]) * across[0] + (vertex.y - middle[1]) * across[1];
            least = std::min(least, side);
            most = std::max(most, side);
            low = std::min(low, static_cast<double>(vertex.z));
            high = std::max(high, static_cast<double>(vertex.z));
        }

        if (most - least < 2.0 * PartyRadius || most - least > WidestDoorway || high - low < 128.0)
        {
            continue;
        }

        const double centre = (least + most) * 0.5;

        for (size_t entityIndex = 0; entityIndex < indoor.entities.size(); ++entityIndex)
        {
            const Game::IndoorEntity &entity = indoor.entities[entityIndex];
            const std::map<int, std::pair<double, bool>>::const_iterator solid = solids.find(entity.decorationListId);

            if (solid == solids.end() || !solid->second.second || entity.z < low - 64.0 || entity.z > high - 64.0
                || hanging.contains(static_cast<int>(entityIndex)) || decorationHangs(entity.name)
                || entity.name.find("Party Start") != std::string::npos)
            {
                continue;
            }

            const double radius = solid->second.first;
            const double dx = entity.x - middle[0];
            const double dy = entity.y - middle[1];
            const double out = dx * way[0] + dy * way[1];
            const double off = dx * across[0] + dy * across[1] - centre;

            if (std::fabs(out) > Reach + radius || std::fabs(off) >= radius + PartyRadius)
            {
                continue;
            }

            findings.push_back({"thing.in_doorway", "warning", "decoration " + std::to_string(entityIndex) + " ("
                    + entity.name + ", radius " + std::to_string(static_cast<int>(radius)) + ") at ["
                    + std::to_string(entity.x) + ", " + std::to_string(entity.y) + ", " + std::to_string(entity.z)
                    + "] stands " + std::to_string(static_cast<int>(std::lround(std::fabs(off))))
                    + " from the line through the opening of face " + std::to_string(faceIndex) + " (sectors "
                    + std::to_string(face.roomNumber) + " and " + std::to_string(face.roomBehindNumber) + "), "
                    + std::to_string(static_cast<int>(std::lround(std::fabs(out)))) + " to its side: within its "
                    "radius and the party's (37), so a walk through catches on it",
                "Move it at least " + std::to_string(static_cast<int>(std::ceil(radius + PartyRadius - std::fabs(off))))
                    + " aside, or further than " + std::to_string(static_cast<int>(Reach + radius))
                    + " from the opening."});
        }
    }
}

std::vector<AuditFinding> auditLooks(
    const LoadedMap &map, const std::string &decorationTableText, const std::set<int> &hanging)
{
    std::vector<AuditFinding> findings;

    if (!map.indoor)
    {
        return findings;
    }

    const Game::IndoorMapData &indoor = *map.indoor;
    // Squashed pictures, by texture: how many faces and the worst.
    struct Squashed
    {
        size_t faces = 0;
        double ratio = 0.0;
        uint32_t face = 0;
        std::array<double, 2> rates = {};
    };
    std::map<std::string, Squashed> squashed;
    RayScene floors;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];

        if (face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal)
            || face.vertexIndices.size() < 3)
        {
            continue;
        }

        std::vector<std::array<double, 3>> points;
        std::vector<std::array<double, 2>> texels;

        for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
        {
            const Game::IndoorVertex &vertex = indoor.vertices[face.vertexIndices[corner]];
            points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});

            if (corner < face.textureUs.size() && corner < face.textureVs.size())
            {
                texels.push_back({double(face.textureUs[corner]) + face.textureDeltaU,
                    double(face.textureVs[corner]) + face.textureDeltaV});
            }
        }

        floors.addFace(points, {0.0, 0.0, 0.0}, static_cast<int32_t>(faceIndex), face.textureName);

        if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible))
        {
            continue;
        }

        const std::optional<std::array<double, 2>> rates = texelRates(points, texels);

        if (!rates)
        {
            continue;
        }

        const double ratio = std::max((*rates)[0], (*rates)[1]) / std::min((*rates)[0], (*rates)[1]);

        if (ratio > 1.6)
        {
            Squashed &entry = squashed[face.textureName];
            ++entry.faces;

            if (ratio > entry.ratio)
            {
                entry = {entry.faces, ratio, static_cast<uint32_t>(faceIndex), *rates};
            }
        }
    }

    const auto rounded = [](double value)
    {
        std::ostringstream text;
        text << std::round(value * 100.0) / 100.0;
        return text.str();
    };

    // (Information: the shipped maps have none, and the studio's own tunnels and gullies lay theirs a third of their
    // size down the face, which a rebuild cannot say otherwise yet; the build warns of each.)
    for (const std::pair<const std::string, Squashed> &entry : squashed)
    {
        findings.push_back({"texture.squashed", "info", entry.first + " is squashed on "
                + std::to_string(entry.second.faces) + " face(s); the worst, face "
                + std::to_string(entry.second.face) + ", lays " + rounded(entry.second.rates[0])
                + " texels a unit across against " + rounded(entry.second.rates[1]) + " down",
            "Lay the picture on a face of its shape, at its own size, or choose a texture made for the face."});
    }

    // Decorations in the air: hints by the table's row number.
    std::map<int, std::string> hints;
    std::istringstream table(decorationTableText);

    for (std::string line; std::getline(table, line);)
    {
        std::vector<std::string> cells;
        std::istringstream row(line);

        for (std::string cell; std::getline(row, cell, '\t');)
        {
            cells.push_back(cell);
        }

        if (cells.size() >= 3 && !cells[0].empty() && std::isdigit(static_cast<unsigned char>(cells[0][0])))
        {
            // (A decoration's list id is its row's number less one.)
            hints[std::atoi(cells[0].c_str()) - 1] = cells[2];
        }
    }

    floors.build();

    for (size_t entityIndex = 0; entityIndex < indoor.entities.size() && !hints.empty(); ++entityIndex)
    {
        const Game::IndoorEntity &entity = indoor.entities[entityIndex];
        const std::map<int, std::string>::const_iterator hint = hints.find(entity.decorationListId);

        if (hint == hints.end() || decorationHangs(hint->second) || decorationHangs(entity.name)
            || hanging.contains(static_cast<int>(entityIndex)))
        {
            continue;
        }

        double under = -1.0e9;

        for (const std::pair<double, int32_t> &height : floors.heightsAt(entity.x, entity.y))
        {
            if (height.first <= entity.z + 4.0)
            {
                under = std::max(under, height.first);
            }
        }

        if (under > -1.0e8 && entity.z - under > 16.0)
        {
            findings.push_back({"thing.floating", "warning", "decoration " + std::to_string(entityIndex) + " ("
                    + entity.name + ", " + hint->second + ") at [" + std::to_string(entity.x) + ", "
                    + std::to_string(entity.y) + ", " + std::to_string(entity.z) + "] stands "
                    + std::to_string(static_cast<int>(std::lround(entity.z - under)))
                    + " over the highest floor or top under it",
                "Stand it on what is to hold it, or on the floor."});
        }
    }

    auditDoorwayDecorations(indoor, decorationTableText, hanging, findings);
    return findings;
}

std::vector<AuditFinding> auditQuestions(const LoadedMap &map, const std::string &flowJson, const SolveResult *pSolved)
{
    std::vector<AuditFinding> findings;

    if (!map.indoor || !map.state)
    {
        return findings;
    }

    // Each handler's title, its texts and the answers it asks for.
    struct Handler
    {
        std::string title;
        std::vector<std::string> texts;
        std::vector<std::string> answers;
    };
    std::map<int, Handler> handlers;
    const std::regex handlerPattern(R"re(RegisterEvent\((\d+),\s*(nil|"((?:[^"\\]|\\.)*)"),\s*function)re");
    // (A status line may name its seconds: evt.StatusText("...", 5).)
    const std::regex textPattern(
        R"re(evt\.(?:SetMessage|SimpleMessage|StatusText)\("((?:[^"\\]|\\.)*)"(?:,\s*[0-9.]+)?\))re");
    const std::regex askPattern(R"re(evt\.AskQuestion\([^{]*\{([^}]*)\}\))re");
    const std::regex answerPattern(R"re("((?:[^"\\]|\\.)*)")re");
    const std::string &script = map.scriptText;
    std::vector<std::pair<size_t, int>> starts;

    for (std::sregex_iterator match(script.begin(), script.end(), handlerPattern), end; match != end; ++match)
    {
        const int eventId = std::stoi((*match)[1].str());
        handlers[eventId].title = (*match)[3].str();
        starts.push_back({static_cast<size_t>(match->position()), eventId});
    }

    for (size_t index = 0; index < starts.size(); ++index)
    {
        const size_t from = starts[index].first;
        const size_t to = index + 1 < starts.size() ? starts[index + 1].first : script.size();
        const std::string body = script.substr(from, to - from);
        Handler &handler = handlers[starts[index].second];

        for (std::sregex_iterator match(body.begin(), body.end(), textPattern), end; match != end; ++match)
        {
            handler.texts.push_back((*match)[1].str());
        }

        for (std::sregex_iterator match(body.begin(), body.end(), askPattern), end; match != end; ++match)
        {
            const std::string list = (*match)[1].str();

            for (std::sregex_iterator answer(list.begin(), list.end(), answerPattern), stop; answer != stop; ++answer)
            {
                std::string word = (*answer)[1].str();
                std::string lower = word;
                std::transform(lower.begin(), lower.end(), lower.begin(),
                    [](unsigned char character) { return static_cast<char>(std::tolower(character)); });

                // A yes or no needs no clue.
                if (lower.size() > 1 && lower != "yes" && lower != "no")
                {
                    handler.answers.push_back(lower);
                }
            }
        }
    }

    // Nothing asked: nothing to find, and no solve to walk (the walk is most of an audit's time on a large map).
    if (std::none_of(handlers.begin(), handlers.end(),
            [](const std::pair<const int, Handler> &handler) { return !handler.second.answers.empty(); }))
    {
        return findings;
    }

    // The step at which the party first reaches each event: the first wave of the solve that reaches one of the
    // sectors it is used from (its faces' sectors, a decoration's).
    const SolveResult solved = pSolved != nullptr ? *pSolved : solveMap(map, flowJson);
    std::map<size_t, size_t> waveOfSector;

    for (size_t wave = 0; wave < solved.waves.size(); ++wave)
    {
        for (const size_t sector : solved.waves[wave].sectors)
        {
            waveOfSector.emplace(sector, wave + 1);
        }
    }

    std::map<int, size_t> stepOf;
    const auto reachedAt = [&stepOf, &waveOfSector](int eventId, size_t sector)
    {
        const std::map<size_t, size_t>::const_iterator wave = waveOfSector.find(sector);

        if (eventId != 0 && wave != waveOfSector.end()
            && (!stepOf.contains(eventId) || wave->second < stepOf[eventId]))
        {
            stepOf[eventId] = wave->second;
        }
    };

    for (const Game::IndoorFace &face : map.indoor->faces)
    {
        reachedAt(face.cogTriggered, face.roomNumber);
    }

    for (const Game::IndoorEntity &entity : map.indoor->entities)
    {
        const std::optional<int16_t> sector = Game::findIndoorSectorForPoint(*map.indoor, map.indoor->vertices,
            {float(entity.x), float(entity.y), float(entity.z) + 16.0f});
        reachedAt(entity.scriptEventId(), sector ? static_cast<size_t>(*sector) : 0);
    }

    const auto stepText = [&stepOf](int eventId)
    {
        return stepOf.contains(eventId) ? "step " + std::to_string(stepOf.at(eventId)) : std::string("no step");
    };

    for (const std::pair<const int, Handler> &question : handlers)
    {
        for (const std::string &answer : question.second.answers)
        {
            std::string where;
            bool given = false;
            bool givenWell = false;

            for (const std::pair<const int, Handler> &other : handlers)
            {
                if (other.first == question.first)
                {
                    continue;
                }

                for (const std::string &text : other.second.texts)
                {
                    std::string lower = text;
                    std::transform(lower.begin(), lower.end(), lower.begin(),
                        [](unsigned char character) { return static_cast<char>(std::tolower(character)); });

                    if (lower.find(answer) == std::string::npos)
                    {
                        continue;
                    }

                    given = true;
                    const bool named = !other.second.title.empty();
                    const bool before = stepOf.contains(other.first) && (!stepOf.contains(question.first)
                        || stepOf.at(other.first) <= stepOf.at(question.first));
                    givenWell = givenWell || (named && before);
                    where += (where.empty() ? "" : "; ") + std::string("event ") + std::to_string(other.first) + " (\""
                        + other.second.title + "\", " + stepText(other.first) + (named ? "" : ", no hover name")
                        + ")";
                    break;
                }
            }

            const std::string asked = "event " + std::to_string(question.first) + " (\"" + question.second.title
                + "\", " + stepText(question.first) + ") asks for \"" + answer + "\"";

            if (!given)
            {
                findings.push_back({"question.answer", "warning", asked + ": no message, sign or status line of the "
                        "map gives it (NPC topics are not read)",
                    "Give the answer in a text the player meets before the question: a sign, a message of a thing "
                    "that has a hover name."});
            }
            else if (!givenWell)
            {
                findings.push_back({"question.answer", "warning", asked + ": given only by " + where
                        + ", which the player is not shown to meet before it with a name that invites a click",
                    "Give the answer by a thing with a hover name (a Sign, a Note) that the party reaches before "
                    "the question."});
            }
            else
            {
                findings.push_back({"question.answer", "info", asked + ": given by " + where, ""});
            }
        }
    }

    return findings;
}

std::vector<AuditFinding> auditRides(const LoadedMap &map, const std::string &flowJson, const CoplanarNames &names)
{
    std::vector<AuditFinding> findings;

    if (!map.indoor || !map.state || flowJson.empty() || map.state->doors.empty())
    {
        return findings;
    }

    YAML::Node events;

    try
    {
        events = YAML::Load(flowJson);
    }
    catch (const YAML::Exception &)
    {
        return findings;
    }

    // The game's reach for a click (GameSettings' interaction depth) from the party's eye.
    constexpr double Reach = 512.0;
    constexpr double Eye = 160.0;
    const Game::IndoorMapData &indoor = *map.indoor;
    std::map<uint32_t, std::set<int>> eventsByDoor;

    for (const YAML::Node &event : events)
    {
        for (const YAML::Node &path : event["paths"])
        {
            for (const YAML::Node &effect : path["effects"])
            {
                if (effect.IsScalar() && effect.Scalar().starts_with("door "))
                {
                    eventsByDoor[static_cast<uint32_t>(std::stoul(effect.Scalar().substr(5)))].insert(
                        event["event"].as<int>());
                }
            }
        }
    }

    std::map<int, std::vector<uint32_t>> clickedFaces;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];

        if (face.cogTriggered != 0 && !face.isPortal
            && Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Clickable))
        {
            clickedFaces[face.cogTriggered].push_back(static_cast<uint32_t>(faceIndex));
        }
    }

    // The two poses: as the map starts, and every moving part at the other end of its way.
    Game::EventRuntimeState moved;

    for (const Game::MapDeltaDoor &door : map.state->doors)
    {
        const bool startsOpen = door.state == static_cast<uint16_t>(Game::EvtMechanismState::Open)
            || door.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening);
        Game::RuntimeMechanismState pose;
        pose.state = static_cast<uint16_t>(
            startsOpen ? Game::EvtMechanismState::Closed : Game::EvtMechanismState::Open);
        pose.currentDistance = startsOpen ? static_cast<float>(door.moveLength) : 0.0f;
        moved.mechanisms[door.doorId] = pose;
    }

    const std::array<std::vector<Game::IndoorVertex>, 2> poses = {
        Game::buildIndoorMechanismAdjustedVertices(indoor, &*map.state, nullptr),
        Game::buildIndoorMechanismAdjustedVertices(indoor, &*map.state, &moved)};
    using Point = std::array<double, 3>;
    const auto pointsOf = [&indoor](const std::vector<Game::IndoorVertex> &vertices, uint32_t faceIndex)
    {
        std::vector<Point> points;

        for (const uint16_t vertex : indoor.faces[faceIndex].vertexIndices)
        {
            if (vertex < vertices.size())
            {
                points.push_back({static_cast<double>(vertices[vertex].x), static_cast<double>(vertices[vertex].y),
                    static_cast<double>(vertices[vertex].z)});
            }
        }

        return points;
    };
    // Newell's normal, the way the face looks (as core/Coplanar reads it), not made unit.
    const auto normalOf = [](const std::vector<Point> &points)
    {
        Point normal = {};

        for (size_t index = 0; index < points.size(); ++index)
        {
            const Point &current = points[index];
            const Point &next = points[(index + 1) % points.size()];
            normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
            normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
            normal[2] += (current[0] - next[0]) * (current[1] + next[1]);
        }

        return normal;
    };
    const auto middleOf = [](const std::vector<Point> &points)
    {
        Point middle = {};

        for (const Point &point : points)
        {
            for (int axis = 0; axis < 3; ++axis)
            {
                middle[axis] += point[axis] / static_cast<double>(points.size());
            }
        }

        return middle;
    };

    const std::map<uint32_t, uint32_t> doorOf = doorOfFaces(&*map.state);
    // Whether the straight line from `from` to `to` passes through a drawn face other than `except` (the clicked
    // thing's own faces) on its way: a wall between a rider and a lever.
    const auto blocked = [&](const std::vector<Game::IndoorVertex> &vertices, const Point &from, const Point &to,
                             const std::set<uint32_t> &except)
    {
        const Point way = {to[0] - from[0], to[1] - from[1], to[2] - from[2]};

        for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
        {
            const Game::IndoorFace &face = indoor.faces[faceIndex];

            if (face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
                || except.contains(static_cast<uint32_t>(faceIndex)))
            {
                continue;
            }

            const std::vector<Point> points = pointsOf(vertices, static_cast<uint32_t>(faceIndex));

            if (points.size() < 3)
            {
                continue;
            }

            const Point normal = normalOf(points);
            const double across = normal[0] * way[0] + normal[1] * way[1] + normal[2] * way[2];

            if (std::abs(across) < 1.0e-9)
            {
                continue;
            }

            const double share = (normal[0] * (points[0][0] - from[0]) + normal[1] * (points[0][1] - from[1])
                + normal[2] * (points[0][2] - from[2])) / across;

            if (share <= 0.01 || share >= 0.99)
            {
                continue;
            }

            const Point hit = {from[0] + way[0] * share, from[1] + way[1] * share, from[2] + way[2] * share};
            // Inside the face: on the plane of its two widest axes.
            const int dropped =
                std::abs(normal[2]) >= std::abs(normal[0]) && std::abs(normal[2]) >= std::abs(normal[1]) ? 2
                : std::abs(normal[1]) >= std::abs(normal[0]) ? 1 : 0;
            const int u = dropped == 0 ? 1 : 0;
            const int v = dropped == 2 ? 1 : 2;
            bool inside = false;

            for (size_t index = 0, previous = points.size() - 1; index < points.size(); previous = index++)
            {
                const Point &a = points[index];
                const Point &b = points[previous];

                if ((a[v] > hit[v]) != (b[v] > hit[v])
                    && hit[u] < (b[u] - a[u]) * (hit[v] - a[v]) / (b[v] - a[v]) + a[u])
                {
                    inside = !inside;
                }
            }

            if (inside)
            {
                return true;
            }
        }

        return false;
    };
    // Level floors that are no moving part, by their height and plan, for whether a deck stops beside one.
    std::vector<std::pair<double, std::vector<Point>>> floors;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const std::vector<Point> points = pointsOf(poses[0], static_cast<uint32_t>(faceIndex));
        const Point normal = normalOf(points);
        const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

        if (!indoor.faces[faceIndex].isPortal && !doorOf.contains(static_cast<uint32_t>(faceIndex))
            && points.size() >= 3 && length > 1.0 && normal[2] / length > 0.7)
        {
            floors.push_back({middleOf(points)[2], points});
        }
    }

    // Whether the deck stops with a floor beside it at its own height (within a step), so a party boards it there.
    const auto boardable = [&floors](const std::vector<Point> &deckPoints)
    {
        const auto near = [](const Point &point, const Point &a, const Point &b)
        {
            const double dx = b[0] - a[0];
            const double dy = b[1] - a[1];
            const double lengthSquared = dx * dx + dy * dy;
            const double share = lengthSquared < 1.0e-9 ? 0.0
                : std::clamp(((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / lengthSquared, 0.0, 1.0);
            const double ex = a[0] + dx * share - point[0];
            const double ey = a[1] + dy * share - point[1];
            return ex * ex + ey * ey <= 96.0 * 96.0;
        };
        const double deckHeight = deckPoints.empty() ? 0.0 : deckPoints[0][2];

        for (const std::pair<double, std::vector<Point>> &floor : floors)
        {
            if (std::abs(floor.first - deckHeight) > 48.0)
            {
                continue;
            }

            // A deck standing in a floor (a lift drawn level with it).
            for (const Point &corner : deckPoints)
            {
                bool inside = false;

                for (size_t index = 0, previous = floor.second.size() - 1; index < floor.second.size();
                     previous = index++)
                {
                    const Point &a = floor.second[index];
                    const Point &b = floor.second[previous];

                    if ((a[1] > corner[1]) != (b[1] > corner[1])
                        && corner[0] < (b[0] - a[0]) * (corner[1] - a[1]) / (b[1] - a[1]) + a[0])
                    {
                        inside = !inside;
                    }
                }

                if (inside)
                {
                    return true;
                }
            }

            for (size_t index = 0; index < floor.second.size(); ++index)
            {
                const Point &a = floor.second[index];
                const Point &b = floor.second[(index + 1) % floor.second.size()];

                for (size_t corner = 0; corner < deckPoints.size(); ++corner)
                {
                    if (near(deckPoints[corner], a, b)
                        || near(a, deckPoints[corner], deckPoints[(corner + 1) % deckPoints.size()]))
                    {
                        return true;
                    }
                }
            }
        }

        return false;
    };

    for (const Game::MapDeltaDoor &door : map.state->doors)
    {
        const std::map<uint32_t, std::set<int>>::const_iterator moving = eventsByDoor.find(door.doorId);

        // A ride carries the party (as the game does: up and down, or a slide whose mover says so) and travels further
        // than a button or a step.
        if (moving == eventsByDoor.end() || door.moveLength < 64
            || !Game::indoorDoorCarriesPartySupport(door, Game::findIndoorMoverDefinition(indoor, door.doorId)))
        {
            continue;
        }

        const std::set<uint16_t> movingVertices(door.vertexIds.begin(), door.vertexIds.end());

        const std::set<uint32_t> own(door.faceIds.begin(), door.faceIds.end());
        // Its deck: the widest level top among its faces, 64 or more across both ways.
        std::optional<uint32_t> deck;
        double deckArea = 0.0;

        for (const uint16_t faceIndex : door.faceIds)
        {
            if (faceIndex >= indoor.faces.size() || indoor.faces[faceIndex].isPortal)
            {
                continue;
            }

            const std::vector<Point> points = pointsOf(poses[0], faceIndex);
            const Point normal = normalOf(points);
            const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);
            // (The whole top moves: a bridge that stretches from its stub is walked, not ridden.)
            const bool whole = std::all_of(indoor.faces[faceIndex].vertexIndices.begin(),
                indoor.faces[faceIndex].vertexIndices.end(),
                [&movingVertices](uint16_t vertex) { return movingVertices.contains(vertex); });

            if (points.size() < 3 || length < 1.0 || normal[2] / length < 0.99 || !whole)
            {
                continue;
            }

            Point low = points[0];
            Point high = points[0];

            for (const Point &point : points)
            {
                for (int axis = 0; axis < 2; ++axis)
                {
                    low[axis] = std::min(low[axis], point[axis]);
                    high[axis] = std::max(high[axis], point[axis]);
                }
            }

            if (high[0] - low[0] >= 64.0 && high[1] - low[1] >= 64.0 && length / 2.0 > deckArea)
            {
                deck = faceIndex;
                deckArea = length / 2.0;
            }
        }

        // A ride stops with a floor beside its deck at both ends (a falling rock, a sinking slab are no rides).
        if (!deck || !boardable(pointsOf(poses[0], *deck)) || !boardable(pointsOf(poses[1], *deck)))
        {
            continue;
        }

        std::vector<uint32_t> switches;
        bool ownClick = false;

        for (const int eventId : moving->second)
        {
            const std::map<int, std::vector<uint32_t>>::const_iterator faces = clickedFaces.find(eventId);

            for (const uint32_t faceIndex : faces == clickedFaces.end() ? std::vector<uint32_t>() : faces->second)
            {
                ownClick = ownClick || own.contains(faceIndex);

                if (!own.contains(faceIndex))
                {
                    switches.push_back(faceIndex);
                }
            }
        }

        // Moved only by steps, timers or its own faces' clicks with nothing else: no switch is meant for riders.
        if (switches.empty())
        {
            continue;
        }

        std::vector<std::string> unserved;
        double nearestAway = 0.0;
        uint32_t nearestFace = 0;

        for (size_t pose = 0; pose < poses.size(); ++pose)
        {
            const std::vector<Point> deckPoints = pointsOf(poses[pose], *deck);
            const Point deckMiddle = middleOf(deckPoints);
            // Where a rider's eye can be: over the deck's middle and over each corner a body's width in from it.
            std::vector<Point> eyes = {{deckMiddle[0], deckMiddle[1], deckMiddle[2] + Eye}};

            for (const Point &corner : deckPoints)
            {
                const double dx = deckMiddle[0] - corner[0];
                const double dy = deckMiddle[1] - corner[1];
                const double inward = std::min(1.0, 32.0 / std::max(1.0, std::sqrt(dx * dx + dy * dy)));
                eyes.push_back({corner[0] + dx * inward, corner[1] + dy * inward, corner[2] + Eye});
            }

            bool served = false;
            double nearest = 1.0e12;
            uint32_t nearestHere = switches.front();

            for (const uint32_t faceIndex : switches)
            {
                const std::vector<Point> points = pointsOf(poses[pose], faceIndex);

                if (points.size() < 3)
                {
                    continue;
                }

                const Point middle = middleOf(points);
                const Point normal = normalOf(points);
                // (The clicked thing's own faces, all of its event's, do not hide it.)
                std::set<uint32_t> itself;

                for (const uint32_t other : switches)
                {
                    itself.insert(other);
                }

                for (const Point &eye : eyes)
                {
                    const double distance = std::sqrt((eye[0] - middle[0]) * (eye[0] - middle[0])
                        + (eye[1] - middle[1]) * (eye[1] - middle[1]) + (eye[2] - middle[2]) * (eye[2] - middle[2]));
                    const bool facing = (eye[0] - middle[0]) * normal[0] + (eye[1] - middle[1]) * normal[1]
                        + (eye[2] - middle[2]) * normal[2] > 0.0
                        && !blocked(poses[pose], eye, middle, itself);

                    if (facing && distance < nearest)
                    {
                        nearest = distance;
                        nearestHere = faceIndex;
                    }

                    served = served || (facing && distance < Reach);
                }
            }

            if (!served)
            {
                unserved.push_back(pose == 0 ? "where it starts" : "at the other end of its way");

                if (nearest > nearestAway && nearest < 1.0e11)
                {
                    nearestAway = nearest;
                    nearestFace = nearestHere;
                }
            }
        }

        if (unserved.empty())
        {
            continue;
        }

        const std::map<int, std::string>::const_iterator name = names.doors.find(static_cast<int>(door.doorId));
        const int switchEvent = indoor.faces[switches.front()].cogTriggered;
        const std::map<int, std::string>::const_iterator eventName = names.events.find(switchEvent);
        findings.push_back({"ride.no_switch", "warning",
            "door " + std::to_string(door.doorId) + (name == names.doors.end() ? "" : " (" + name->second + ")")
                + " carries the party on its top (face " + std::to_string(*deck) + "), and " + unserved.front()
                + (unserved.size() > 1 ? " and " + unserved.back() : "") + " none of the " + std::to_string(
                    switches.size()) + " clicked faces that move it (event " + std::to_string(switchEvent)
                + (eventName == names.events.end() ? "" : " " + eventName->second) + " ...) is within "
                + std::to_string(static_cast<int>(Reach)) + " of a rider's eye on the deck and facing him"
                + (nearestAway > 0.0 ? " (the nearest that faces the deck, face " + std::to_string(nearestFace)
                    + ", is " + std::to_string(std::lround(nearestAway)) + " away)" : " (none faces the deck)")
                + (ownClick ? "; its own faces run the event, which nothing tells a rider" : ""),
            "Put a switch at each stop on the riders' side, facing the deck within reach of its edge (XD-02's riders' "
            "levers beside each gate)"});
    }

    return findings;
}

std::vector<AuditFinding> auditSilentClicks(const LoadedMap &map, const std::string &flowJson)
{
    std::vector<AuditFinding> findings;

    if (!map.indoor || flowJson.empty())
    {
        return findings;
    }

    std::set<int> clicked;

    // (A face whose event runs when the party steps on it, without the clickable bit, is no click: the user's walk
    // through the Abandoned Temple, round seven.)
    for (const Game::IndoorFace &face : map.indoor->faces)
    {
        if (face.cogTriggered != 0 && !Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal)
            && Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Clickable))
        {
            clicked.insert(face.cogTriggered);
        }
    }

    for (const Game::IndoorEntity &entity : map.indoor->entities)
    {
        if (entity.scriptEventId() != 0)
        {
            clicked.insert(entity.scriptEventId());
        }
    }

    YAML::Node events;

    try
    {
        events = YAML::Load(flowJson);
    }
    catch (const YAML::Exception &)
    {
        return findings;
    }

    // What a player sees happen (anything else changes only state: variables, bits).
    const auto seen = [](const std::string &effect)
    {
        for (const char *pWord : {"StatusText", "SimpleMessage", "SetMessage", "AskQuestion", "door ", "open chest",
                 "GiveItem", "leave to", "teleport", "MoveToMap", "DamagePlayer", "SetTexture", "SetSprite",
                 "SummonMonsters", "SetLight", "CameraShake", "SetFacetBit", "SpeakNPC", "CastSpell", "gold",
                 "Gold", "PlaySound", "ShowMovie", "SetMonGroupBit", "Experience"})
        {
            if (effect.find(pWord) != std::string::npos)
            {
                return true;
            }
        }

        return false;
    };

    for (const YAML::Node &event : events)
    {
        const int eventId = event["event"] ? event["event"].as<int>() : 0;

        if (!clicked.contains(eventId))
        {
            continue;
        }

        for (const YAML::Node &path : event["paths"])
        {
            bool visible = false;

            for (const YAML::Node &effect : path["effects"])
            {
                visible = visible || (effect.IsScalar() && seen(effect.Scalar()));
            }

            if (visible)
            {
                continue;
            }

            std::string tests;

            for (const YAML::Node &test : path["tests"])
            {
                tests += (tests.empty() ? "" : ", ") + std::string(test["taken"].Scalar() == "true" ? "" : "not ")
                    + test["what"].Scalar();
            }

            const std::string title = event["title"] ? event["title"].Scalar() : std::string();
            findings.push_back({"click.silent", "info", "event " + std::to_string(eventId) + " (\"" + title
                    + "\"): " + (tests.empty() ? std::string("always") : "when " + tests)
                    + ", a click shows nothing (no text, nothing moves or is given)",
                "Say why in the status bar on that branch (`locked_text`, `else_effects` with `text`), as the "
                "shipped maps' locked doors and spent things do."});
        }
    }

    return findings;
}
}
