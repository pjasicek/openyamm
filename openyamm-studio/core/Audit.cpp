#include "core/Audit.h"

#include "core/Coplanar.h"
#include "core/Compare.h"
#include "core/EyeSector.h"
#include "core/Looks.h"
#include "core/Metrics.h"
#include "core/OutdoorInteractive.h"
#include "core/Project.h"
#include "core/Reachability.h"
#include "core/Things.h"

#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/gameplay/CinematicLibrary.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/outdoor/OutdoorGeometryUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>
#include <map>
#include <numbers>
#include <optional>
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

    // A destructible runs its events when it is damaged and when it breaks (the scene's `destructibles`).
    if (map.indoorScene)
    {
        for (const Game::IndoorDestructible &destructible : map.indoorScene->destructibles)
        {
            for (const uint16_t eventId : {destructible.destroyedEvent, destructible.damagedEvent})
            {
                if (eventId != 0)
                {
                    runByEngine.insert(eventId);
                }
            }
        }
    }

    // A cinematic's `event` cues run map events as it plays (or at once when it is skipped).
    if (map.cinematicsText)
    {
        std::string cinematicsError;

        if (const std::optional<Game::CinematicLibrary> library =
                Game::parseCinematicLibrary(*map.cinematicsText, cinematicsError))
        {
            for (const Game::CinematicDefinition &cinematic : library->cinematics)
            {
                for (const Game::CinematicCue &cue : cinematic.cues)
                {
                    if (cue.kind == Game::CinematicCueKind::Event && cue.eventId != 0)
                    {
                        runByEngine.insert(cue.eventId);
                    }
                }
            }
        }
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
                + " is bound to no face or decoration and is not run on load, on leave, by a timer or by a destructible"
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

namespace
{
// An upright face seen from above: its two ends, its height range, the sectors on each side (outdoors: the model).
struct UprightFace
{
    size_t face = 0;
    std::array<double, 2> from = {};
    std::array<double, 2> to = {};
    double low = 0.0;
    double high = 0.0;
    int room = -1;
    int roomBehind = -1;

    double width() const
    {
        return std::hypot(to[0] - from[0], to[1] - from[1]);
    }

    std::array<double, 2> middle() const
    {
        return {(from[0] + to[0]) * 0.5, (from[1] + to[1]) * 0.5};
    }
};

// A polygon whose normal lies within about 45 degrees of level, seen from above: its ends (the vertices furthest along
// it each way) and its height range. Nothing for a polygon that is not upright.
std::optional<UprightFace> uprightPolygon(const std::vector<std::array<double, 3>> &points)
{
    const size_t count = points.size();

    if (count < 3)
    {
        return std::nullopt;
    }

    std::array<double, 3> normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < count; ++index)
    {
        const std::array<double, 3> &a = points[index];
        const std::array<double, 3> &b = points[(index + 1) % count];
        normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
        normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
        normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }

    const double horizontal = std::hypot(normal[0], normal[1]);

    if (horizontal <= 0.0 || horizontal < 0.7 * std::hypot(horizontal, normal[2]))
    {
        return std::nullopt;
    }

    // Along the face: the normal turned a quarter; its ends are the vertices furthest along each way.
    const std::array<double, 2> along = {-normal[1] / horizontal, normal[0] / horizontal};
    UprightFace upright;
    double least = 1.0e18;
    double most = -1.0e18;
    upright.low = 1.0e18;
    upright.high = -1.0e18;

    for (const std::array<double, 3> &point : points)
    {
        const double side = point[0] * along[0] + point[1] * along[1];

        if (side < least)
        {
            least = side;
            upright.from = {point[0], point[1]};
        }

        if (side > most)
        {
            most = side;
            upright.to = {point[0], point[1]};
        }

        upright.low = std::min(upright.low, point[2]);
        upright.high = std::max(upright.high, point[2]);
    }

    return upright;
}

std::optional<UprightFace> uprightFace(const Game::IndoorMapData &indoor, size_t faceIndex)
{
    const Game::IndoorFace &face = indoor.faces[faceIndex];
    std::vector<std::array<double, 3>> points;

    for (const uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= indoor.vertices.size())
        {
            return std::nullopt;
        }

        const Game::IndoorVertex &vertex = indoor.vertices[vertexIndex];
        points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
    }

    std::optional<UprightFace> upright = uprightPolygon(points);

    if (upright)
    {
        upright->face = faceIndex;
        upright->room = face.roomNumber;
        upright->roomBehind = face.roomBehindNumber;
    }

    return upright;
}

// From a point to the segment between two points, seen from above; `along` gets how far past either end the point's
// foot lies (0 when it is between them).
double distanceToSegment(
    const std::array<double, 2> &point, const std::array<double, 2> &from, const std::array<double, 2> &to,
    double *pBeyond = nullptr)
{
    const double dx = to[0] - from[0];
    const double dy = to[1] - from[1];
    const double length = std::hypot(dx, dy);

    if (length <= 0.0)
    {
        if (pBeyond != nullptr)
        {
            *pBeyond = 0.0;
        }

        return std::hypot(point[0] - from[0], point[1] - from[1]);
    }

    const double t = ((point[0] - from[0]) * dx + (point[1] - from[1]) * dy) / length;

    if (pBeyond != nullptr)
    {
        *pBeyond = t < 0.0 ? -t : (t > length ? t - length : 0.0);
    }

    const double clamped = std::clamp(t, 0.0, length);
    return std::hypot(point[0] - (from[0] + dx / length * clamped), point[1] - (from[1] + dy / length * clamped));
}

std::string roundedUnits(double value)
{
    return std::to_string(static_cast<long>(std::lround(value)));
}

// devdocs/xeen/formats/DRESSING.md, "Measurements" (Warlord's Fortress and Castle Harmondale); decision D-7.1.
namespace Dressing
{
constexpr double WallReach = 240.0;
constexpr double StoreroomWallReach = 320.0;
constexpr double DoorClearance = 192.0;
constexpr double SideMargin = 64.0;
constexpr double DoorwayFrontClearance = 320.0;
constexpr double DoorwayBesideClearance = 192.0;
constexpr double WalkingLineMargin = 64.0;
constexpr double WalkingLineRadius = 24.0;
constexpr double FreeGap = 128.0;
constexpr double OnFloor = 24.0;
constexpr double ClumpDistance = 200.0;
constexpr size_t ClumpSize = 3;
constexpr size_t StoreroomContainers = 8;
constexpr double PartyRadius = 37.0;
constexpr double WidestDoorway = 512.0;
// Outdoors: a container this near a model's wall stands "by a house" and keeps to its wall; the walking line runs
// between two house doors this near each other with nothing built between them.
constexpr double ByAHouse = 512.0;
constexpr double DoorLineReach = 2048.0;
// A road is drawn along the line through its cells' middles: a prop's body keeps this far from that line.
constexpr double RoadMiddle = 64.0;
}

// A decoration row as the dressing rules read it: radius, whether it blocks, whether its hint or name makes it a
// container or a set piece.
struct DressingKind
{
    double radius = 0.0;
    bool blocks = false;
    bool container = false;
    bool setPiece = false;
    std::string hint;
    // The row's internal name.
    std::string name;
};

// The rows by number and by internal name (lower case; the first row of a name), as the game resolves a placed
// decoration: by its name, else by its number.
struct DressingKinds
{
    std::map<int, DressingKind> byId;
    std::map<std::string, int> idByName;

    bool empty() const
    {
        return byId.empty();
    }
};

std::string trimmedLower(const std::string &text)
{
    const size_t begin = text.find_first_not_of(" \t\r");
    const size_t end = text.find_last_not_of(" \t\r");
    std::string lowered = begin == std::string::npos ? std::string() : text.substr(begin, end - begin + 1);
    std::transform(lowered.begin(), lowered.end(), lowered.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return lowered;
}

DressingKinds readDressingKinds(const std::string &decorationTableText)
{
    DressingKinds kinds;
    std::istringstream table(decorationTableText);
    // MM6's bigbarel and bag01, MM7's barrels and casks; firewood and log piles (MM7's woodpiles, hint "wood") too.
    static const std::regex containerWords(
        "barrel|barel|cask|keg|sack|\\bbag|crate|\\bbox|bucket|firewood|woodpile|log pile");
    static const std::regex setPieceWords("\\btree|statue|pillar|column|altar|hearth|fire(?!wood)|brazier"
        "|cauldron|\\bvat|fountain|pedestal|shrine|obelisk|\\bstall|\\brock|boulder");

    for (std::string line; std::getline(table, line);)
    {
        std::vector<std::string> cells;
        std::istringstream row(line);

        for (std::string cell; std::getline(row, cell, '\t');)
        {
            cells.push_back(cell);
        }

        if (cells.size() < 12 || cells[0].empty() || !std::isdigit(static_cast<unsigned char>(cells[0][0])))
        {
            continue;
        }

        std::string names = cells[1] + " " + cells[2];
        std::transform(names.begin(), names.end(), names.begin(), [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
        DressingKind kind;
        kind.radius = std::atof(cells[4].c_str());
        kind.hint = cells[2];
        kind.name = cells[1];
        kind.blocks = kind.radius > 0.0 && cells[11].find("MoveThrough") == std::string::npos
            && cells[11].find("DontDraw") == std::string::npos && !decorationHangs(cells[2])
            && names.find("party start") == std::string::npos;
        kind.setPiece = std::regex_search(names, setPieceWords);
        kind.container = !kind.setPiece
            && (std::regex_search(names, containerWords) || trimmedLower(cells[2]) == "wood");
        const int id = std::atoi(cells[0].c_str()) - 1;
        kinds.byId[id] = kind;
        kinds.idByName.emplace(trimmedLower(cells[1]), id);
    }

    return kinds;
}

// The row of a placed decoration that is a prop: a blocking row, not hanging, no marker (the party's start, sounds and
// other unseen rows: hint "null" or "pending", no name). Null for anything else.
const DressingKind *propKindOf(
    const DressingKinds &kinds, int decorationListId, const std::string &name, bool hangs)
{
    const std::map<std::string, int>::const_iterator named = kinds.idByName.find(trimmedLower(name));
    const std::map<int, DressingKind>::const_iterator kind =
        kinds.byId.find(named != kinds.idByName.end() ? named->second : decorationListId);

    if (kind == kinds.byId.end() || !kind->second.blocks || hangs || decorationHangs(name) || name.empty()
        || name.find("Party Start") == 0 || kind->second.hint == "null" || kind->second.hint == "pending")
    {
        return nullptr;
    }

    return &kind->second;
}

enum class PropClass
{
    Container,
    SetPiece,
    Other,
};

// A blocking decoration with its sector (outdoors none), class and whether it stands on the floor.
struct DressingProp
{
    size_t entity = 0;
    std::string name;
    std::array<double, 2> at = {};
    double z = 0.0;
    int room = -1;
    const DressingKind *pKind = nullptr;
    PropClass propClass = PropClass::Other;
    bool onFloor = true;
};

// A clicked or event-bound decoration is a set piece, whatever it is.
PropClass propClassOf(const DressingKind &kind, bool hasEvent, bool onFloor)
{
    if (hasEvent || kind.setPiece)
    {
        return PropClass::SetPiece;
    }

    return kind.container && onFloor ? PropClass::Container : PropClass::Other;
}

std::string describeProp(const DressingProp &prop)
{
    return "decoration " + std::to_string(prop.entity) + " (" + prop.name + ", " + prop.pKind->hint + ", radius "
        + roundedUnits(prop.pKind->radius) + ") at [" + roundedUnits(prop.at[0]) + ", " + roundedUnits(prop.at[1])
        + ", " + roundedUnits(prop.z) + "]";
}

bool spansHeight(const UprightFace &face, double z)
{
    return z >= face.low - 64.0 && z <= face.high - 64.0;
}

// The nearest wall that spans a prop's height (1e18 when none does).
double nearestWall(const DressingProp &prop, const std::vector<UprightFace> &walls)
{
    double nearest = 1.0e18;

    for (const UprightFace &wall : walls)
    {
        if (spansHeight(wall, prop.z))
        {
            nearest = std::min(nearest, distanceToSegment(prop.at, wall.from, wall.to));
        }
    }

    return nearest;
}

// Groups of three or more containers each within 200 of another, as entity numbers.
std::vector<std::vector<size_t>> containerClumps(const std::vector<const DressingProp *> &members)
{
    std::vector<std::vector<size_t>> clumps;
    std::vector<int> group(members.size(), -1);

    for (size_t first = 0; first < members.size(); ++first)
    {
        if (group[first] >= 0)
        {
            continue;
        }

        group[first] = static_cast<int>(first);
        std::vector<size_t> open = {first};

        while (!open.empty())
        {
            const size_t current = open.back();
            open.pop_back();

            for (size_t other = 0; other < members.size(); ++other)
            {
                if (group[other] < 0
                    && std::hypot(members[other]->at[0] - members[current]->at[0],
                           members[other]->at[1] - members[current]->at[1]) <= Dressing::ClumpDistance)
                {
                    group[other] = static_cast<int>(first);
                    open.push_back(other);
                }
            }
        }

        std::vector<size_t> clump;

        for (size_t index = 0; index < members.size(); ++index)
        {
            if (group[index] == static_cast<int>(first))
            {
                clump.push_back(members[index]->entity);
            }
        }

        if (clump.size() >= Dressing::ClumpSize)
        {
            clumps.push_back(clump);
        }
    }

    return clumps;
}

std::string entityList(const std::vector<size_t> &entities)
{
    std::string list;

    for (const size_t entity : entities)
    {
        list += (list.empty() ? "" : ", ") + std::to_string(entity);
    }

    return list;
}

// An opening one walks through: doorways and doors side by side (parallel, in line, at most 64 apart) are one, from
// the outer end of the first to the outer end of the last.
struct Opening
{
    std::array<double, 2> from = {};
    std::array<double, 2> to = {};
    double low = 0.0;
    double high = 0.0;
    std::vector<size_t> faces;

    std::array<double, 2> middle() const
    {
        return {(from[0] + to[0]) * 0.5, (from[1] + to[1]) * 0.5};
    }

    double width() const
    {
        return std::hypot(to[0] - from[0], to[1] - from[1]);
    }
};

bool sideBySide(const UprightFace &first, const UprightFace &second)
{
    const double firstWidth = first.width();
    const double secondWidth = second.width();

    if (firstWidth <= 0.0 || secondWidth <= 0.0)
    {
        return false;
    }

    const std::array<double, 2> along = {
        (first.to[0] - first.from[0]) / firstWidth, (first.to[1] - first.from[1]) / firstWidth};
    const double parallel = std::abs(along[0] * (second.to[0] - second.from[0]) / secondWidth
        + along[1] * (second.to[1] - second.from[1]) / secondWidth);
    const std::array<double, 2> middle = second.middle();
    const double offset = std::abs((middle[0] - first.from[0]) * along[1] - (middle[1] - first.from[1]) * along[0]);
    const double gap = std::min({distanceToSegment(second.from, first.from, first.to),
        distanceToSegment(second.to, first.from, first.to), distanceToSegment(first.from, second.from, second.to),
        distanceToSegment(first.to, second.from, second.to)});
    return parallel >= 0.9 && offset <= Dressing::SideMargin && gap <= Dressing::SideMargin;
}

std::vector<Opening> mergedOpenings(const std::vector<const UprightFace *> &faces)
{
    std::vector<size_t> group(faces.size());

    for (size_t index = 0; index < faces.size(); ++index)
    {
        group[index] = index;
    }

    const auto root = [&group](size_t index)
    {
        while (group[index] != index)
        {
            index = group[index];
        }

        return index;
    };

    for (size_t first = 0; first < faces.size(); ++first)
    {
        for (size_t second = first + 1; second < faces.size(); ++second)
        {
            if (sideBySide(*faces[first], *faces[second]))
            {
                group[root(second)] = root(first);
            }
        }
    }

    std::map<size_t, std::vector<const UprightFace *>> merged;

    for (size_t index = 0; index < faces.size(); ++index)
    {
        merged[root(index)].push_back(faces[index]);
    }

    std::vector<Opening> openings;

    for (const std::pair<const size_t, std::vector<const UprightFace *>> &members : merged)
    {
        // The ends: the two points furthest apart along the first face.
        const UprightFace &first = *members.second.front();
        const double width = std::max(first.width(), 1.0);
        const std::array<double, 2> along = {(first.to[0] - first.from[0]) / width,
            (first.to[1] - first.from[1]) / width};
        Opening opening;
        opening.low = 1.0e18;
        opening.high = -1.0e18;
        double least = 1.0e18;
        double most = -1.0e18;

        for (const UprightFace *pFace : members.second)
        {
            for (const std::array<double, 2> &end : {pFace->from, pFace->to})
            {
                const double position = end[0] * along[0] + end[1] * along[1];

                if (position < least)
                {
                    least = position;
                    opening.from = end;
                }

                if (position > most)
                {
                    most = position;
                    opening.to = end;
                }
            }

            opening.low = std::min(opening.low, pFace->low);
            opening.high = std::max(opening.high, pFace->high);
            opening.faces.push_back(pFace->face);
        }

        openings.push_back(opening);
    }

    return openings;
}

// Free room on one side of a prop: along `direction` from its centre to the first wall that spans its height or the
// first other blocking floor prop of its room, less both radii (4096 when nothing is met).
double freeRoomBeside(const DressingProp &prop, const std::array<double, 2> &direction,
    const std::vector<UprightFace> &walls, const std::vector<DressingProp> &props)
{
    double free = 4096.0;

    for (const UprightFace &wall : walls)
    {
        if (!spansHeight(wall, prop.z))
        {
            continue;
        }

        // The ray against the wall's segment, seen from above.
        const double ex = wall.to[0] - wall.from[0];
        const double ey = wall.to[1] - wall.from[1];
        const double denominator = direction[0] * ey - direction[1] * ex;

        if (std::abs(denominator) < 1.0e-9)
        {
            continue;
        }

        const double wx = wall.from[0] - prop.at[0];
        const double wy = wall.from[1] - prop.at[1];
        const double t = (wx * ey - wy * ex) / denominator;
        const double s = (wx * direction[1] - wy * direction[0]) / denominator;

        if (t >= 0.0 && s >= 0.0 && s <= 1.0)
        {
            free = std::min(free, t - prop.pKind->radius);
        }
    }

    for (const DressingProp &other : props)
    {
        if (&other == &prop || other.room != prop.room || !other.onFloor)
        {
            continue;
        }

        const double ox = other.at[0] - prop.at[0];
        const double oy = other.at[1] - prop.at[1];
        const double ahead = ox * direction[0] + oy * direction[1];
        const double across = std::abs(ox * direction[1] - oy * direction[0]);

        if (ahead > 0.0 && across < other.pKind->radius)
        {
            free = std::min(free, ahead - std::sqrt(other.pKind->radius * other.pKind->radius - across * across)
                - prop.pKind->radius);
        }
    }

    return std::max(free, 0.0);
}

// One prop against one walking line from `from` to `to` (`where` names it, " the walking line between ..."): within
// its radius and 64 of the line, an error (a set piece: a warning) unless `onLine` says one was given; near the line
// and leaving under 128 free on both sides across it, an error unless `narrowed` says one was given.
void checkWalkingLine(const DressingProp &prop, const std::array<double, 2> &from, const std::array<double, 2> &to,
    const std::string &where, const std::vector<UprightFace> &walls, const std::vector<DressingProp> &props,
    bool &onLine, bool &narrowed, std::vector<AuditFinding> &findings)
{
    const bool setPiece = prop.propClass == PropClass::SetPiece;
    const double clearance = prop.pKind->radius + Dressing::WalkingLineMargin;
    const double distance = distanceToSegment(prop.at, from, to);

    if (!onLine && distance < clearance)
    {
        findings.push_back({"dressing.walking_line", setPiece ? "warning" : "error", describeProp(prop)
                + " stands " + roundedUnits(distance) + " from" + where + ": a prop keeps its radius and "
                + roundedUnits(Dressing::WalkingLineMargin) + " clear of it"
                + (setPiece ? " (a set piece: fix it or keep it under \"Dressing exceptions\")" : ""),
            "Move it at least " + roundedUnits(std::ceil(clearance - distance)) + " aside, towards a wall."});
        onLine = true;
    }

    const double length = std::hypot(to[0] - from[0], to[1] - from[1]);

    if (!narrowed && length > 0.0 && distance < prop.pKind->radius + Dressing::FreeGap)
    {
        const std::array<double, 2> across = {-(to[1] - from[1]) / length, (to[0] - from[0]) / length};
        const double left = freeRoomBeside(prop, across, walls, props);
        const double right = freeRoomBeside(prop, {-across[0], -across[1]}, walls, props);

        if (left < Dressing::FreeGap && right < Dressing::FreeGap)
        {
            findings.push_back({"dressing.walking_line", "error", describeProp(prop) + " leaves "
                    + roundedUnits(left) + " and " + roundedUnits(right) + " free on its two sides of" + where
                    + ": the party needs " + roundedUnits(Dressing::FreeGap) + " on one side",
                "Move it against a wall, or out of the passage."});
            narrowed = true;
        }
    }
}

// The events of an outdoor map's script whose handler enters a house (`RegisterEvent(n, ...)` up to the next one
// holds evt.EnterHouse): the house doors.
std::set<int> houseDoorEvents(const std::string &scriptText)
{
    static const std::regex registration("RegisterEvent\\(\\s*(\\d+)");
    std::vector<std::pair<size_t, int>> starts;

    for (std::sregex_iterator match(scriptText.begin(), scriptText.end(), registration);
         match != std::sregex_iterator(); ++match)
    {
        starts.push_back({size_t(match->position(0)), std::atoi(match->str(1).c_str())});
    }

    std::set<int> events;

    for (size_t index = 0; index < starts.size(); ++index)
    {
        const size_t end = index + 1 < starts.size() ? starts[index + 1].first : scriptText.size();

        if (scriptText.substr(starts[index].first, end - starts[index].first).find("EnterHouse(") != std::string::npos)
        {
            events.insert(starts[index].second);
        }
    }

    return events;
}

// Whether the segment from `a` to `b` crosses a wall's, seen from above.
bool crossesWall(const std::array<double, 2> &a, const std::array<double, 2> &b, const UprightFace &wall)
{
    const auto side = [](const std::array<double, 2> &p, const std::array<double, 2> &q, const std::array<double, 2> &r)
    {
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
    };
    const double d1 = side(a, b, wall.from);
    const double d2 = side(a, b, wall.to);
    const double d3 = side(wall.from, wall.to, a);
    const double d4 = side(wall.from, wall.to, b);
    return ((d1 > 0.0) != (d2 > 0.0)) && ((d3 > 0.0) != (d4 > 0.0));
}

// From a point to the middle line of the nearest road (the lines between the middles of road cells side by side, and
// each road cell's middle), seen from above; 1e18 when no road cell lies within two cells. `cellKinds`: core/
// OutdoorGround's outdoorCellKinds (3 a road).
double distanceToRoad(const std::array<double, 2> &point, const std::vector<uint8_t> &cellKinds)
{
    constexpr int Cells = Game::OutdoorMapData::TerrainWidth;
    constexpr double Size = Game::OutdoorMapData::TerrainTileSize;
    const auto road = [&cellKinds](int x, int y)
    {
        return x >= 0 && y >= 0 && x < Cells && y < Cells && size_t(y * Cells + x) < cellKinds.size()
            && cellKinds[size_t(y * Cells + x)] == 3;
    };
    const auto middle = [](int x, int y)
    {
        return std::array<double, 2>{(x - 64 + 0.5) * Size, (64 - y - 0.5) * Size};
    };
    const int cellX = static_cast<int>(std::floor(point[0] / Size)) + 64;
    const int cellY = 64 - static_cast<int>(std::ceil(point[1] / Size));
    double nearest = 1.0e18;

    for (int y = cellY - 2; y <= cellY + 2; ++y)
    {
        for (int x = cellX - 2; x <= cellX + 2; ++x)
        {
            if (!road(x, y))
            {
                continue;
            }

            nearest = std::min(nearest, distanceToSegment(point, middle(x, y), middle(x, y)));

            for (const std::array<int, 2> &next : {std::array<int, 2>{1, 0}, std::array<int, 2>{0, 1}})
            {
                if (road(x + next[0], y + next[1]))
                {
                    nearest = std::min(
                        nearest, distanceToSegment(point, middle(x, y), middle(x + next[0], y + next[1])));
                }
            }
        }
    }

    return nearest;
}

// The dressing rules outdoors (Audit.h): by a house as indoors by a room's walls and doors.
std::vector<AuditFinding> auditOutdoorDressing(const LoadedMap &map, const DressingKinds &kinds,
    const std::set<int> &hanging, const std::vector<uint8_t> &cellKinds)
{
    std::vector<AuditFinding> findings;
    const Game::OutdoorMapData &outdoor = *map.outdoor;
    const std::set<int> houseEvents = houseDoorEvents(map.scriptText);

    // The models' upright faces: the faces that enter a house are its doors (side by side: one door), the rest walls.
    struct HouseDoor
    {
        Opening opening;
        std::array<double, 2> outward = {};
        size_t model = 0;
        int event = 0;
    };
    std::vector<UprightFace> walls;
    std::vector<HouseDoor> doors;

    for (size_t modelIndex = 0; modelIndex < outdoor.bmodels.size(); ++modelIndex)
    {
        const Game::OutdoorBModel &model = outdoor.bmodels[modelIndex];
        std::map<int, std::vector<UprightFace>> doorFaces;

        for (size_t faceIndex = 0; faceIndex < model.faces.size(); ++faceIndex)
        {
            const Game::OutdoorBModelFace &face = model.faces[faceIndex];
            std::vector<std::array<double, 3>> points;

            for (const uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex < model.vertices.size())
                {
                    const Game::OutdoorBModelVertex &vertex = model.vertices[vertexIndex];
                    points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
                }
            }

            std::optional<UprightFace> upright =
                points.size() == face.vertexIndices.size() ? uprightPolygon(points) : std::nullopt;

            if (!upright)
            {
                continue;
            }

            upright->face = faceIndex;
            upright->room = static_cast<int>(modelIndex);
            upright->roomBehind = static_cast<int>(modelIndex);

            if (houseEvents.contains(face.cogTriggeredNumber))
            {
                doorFaces[face.cogTriggeredNumber].push_back(*upright);
            }
            else if (!Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
                || !Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Untouchable))
            {
                walls.push_back(*upright);
            }
        }

        // Out of the house: away from the model's middle.
        const std::array<double, 2> centre = {(model.minX + model.maxX) * 0.5, (model.minY + model.maxY) * 0.5};

        for (const std::pair<const int, std::vector<UprightFace>> &event : doorFaces)
        {
            std::vector<const UprightFace *> faces;

            for (const UprightFace &face : event.second)
            {
                faces.push_back(&face);
            }

            for (const Opening &opening : mergedOpenings(faces))
            {
                const double width = std::max(opening.width(), 1.0);
                HouseDoor door;
                door.opening = opening;
                door.model = modelIndex;
                door.event = event.first;
                door.outward = {-(opening.to[1] - opening.from[1]) / width, (opening.to[0] - opening.from[0]) / width};
                const std::array<double, 2> middle = opening.middle();

                if ((middle[0] - centre[0]) * door.outward[0] + (middle[1] - centre[1]) * door.outward[1] < 0.0)
                {
                    door.outward = {-door.outward[0], -door.outward[1]};
                }

                doors.push_back(door);
            }
        }
    }

    const auto doorName = [&map](const HouseDoor &door)
    {
        const std::optional<std::string> hint =
            map.events ? map.events->getHint(static_cast<uint16_t>(door.event)) : std::nullopt;
        return "the door of " + (hint && !hint->empty() ? *hint : std::string("a house")) + " (event "
            + std::to_string(door.event) + ", model " + std::to_string(door.model) + ")";
    };

    // The props, standing on the land or on a model's top.
    std::vector<DressingProp> props;

    for (size_t entityIndex = 0; entityIndex < outdoor.entities.size(); ++entityIndex)
    {
        const Game::OutdoorEntity &entity = outdoor.entities[entityIndex];
        const DressingKind *pKind = propKindOf(
            kinds, entity.decorationListId, entity.name, hanging.contains(static_cast<int>(entityIndex)));

        if (pKind == nullptr)
        {
            continue;
        }

        DressingProp prop;
        prop.entity = entityIndex;
        prop.name = entity.name;
        prop.at = {double(entity.x), double(entity.y)};
        prop.z = double(entity.z);
        prop.pKind = pKind;
        const double floor = Game::sampleOutdoorPlacementFloorHeight(
            outdoor, float(entity.x), float(entity.y), float(entity.z));
        prop.onFloor = prop.z - floor <= Dressing::OnFloor;
        prop.propClass = propClassOf(*pKind, entity.eventIdPrimary != 0 || entity.eventIdSecondary != 0, prop.onFloor);
        props.push_back(prop);
    }

    // The walking lines: from before one house door to before another, at most 2048 apart, nothing built between.
    struct DoorLine
    {
        std::array<double, 2> from = {};
        std::array<double, 2> to = {};
        double low = 0.0;
        double high = 0.0;
        std::string where;
    };
    std::vector<DoorLine> lines;

    for (size_t first = 0; first < doors.size(); ++first)
    {
        for (size_t second = first + 1; second < doors.size(); ++second)
        {
            const HouseDoor &a = doors[first];
            const HouseDoor &b = doors[second];
            const std::array<double, 2> aMiddle = a.opening.middle();
            const std::array<double, 2> bMiddle = b.opening.middle();
            DoorLine line;
            line.from = {aMiddle[0] + a.outward[0] * Dressing::SideMargin,
                aMiddle[1] + a.outward[1] * Dressing::SideMargin};
            line.to = {bMiddle[0] + b.outward[0] * Dressing::SideMargin,
                bMiddle[1] + b.outward[1] * Dressing::SideMargin};
            line.low = std::min(a.opening.low, b.opening.low);
            line.high = std::max(a.opening.low, b.opening.low);

            if (std::hypot(line.to[0] - line.from[0], line.to[1] - line.from[1]) > Dressing::DoorLineReach)
            {
                continue;
            }

            const bool blocked = std::any_of(walls.begin(), walls.end(), [&line](const UprightFace &wall)
            {
                return wall.low <= line.high + 64.0 && wall.high >= line.low + 64.0
                    && crossesWall(line.from, line.to, wall);
            });

            if (!blocked)
            {
                line.where = " the walking line between " + doorName(a) + " and " + doorName(b);
                lines.push_back(line);
            }
        }
    }

    for (const DressingProp &prop : props)
    {
        const bool setPiece = prop.propClass == PropClass::SetPiece;
        const bool walkingSize = prop.onFloor && prop.pKind->radius >= Dressing::WalkingLineRadius;
        const double wall = nearestWall(prop, walls);

        for (const HouseDoor &door : doors)
        {
            const Opening &opening = door.opening;
            const std::array<double, 2> toProp = {
                prop.at[0] - opening.middle()[0], prop.at[1] - opening.middle()[1]};

            // Not behind the door, in the house.
            if (toProp[0] * door.outward[0] + toProp[1] * door.outward[1] < 0.0
                || prop.z < opening.low - 64.0 || prop.z > opening.high)
            {
                continue;
            }

            double beyond = 0.0;
            const double distance = distanceToSegment(prop.at, opening.from, opening.to, &beyond);

            if (prop.propClass == PropClass::Container)
            {
                // As a doorway: 320 in front (its foot within the door and 64 past its ends), 192 beside it.
                const bool inFront = beyond <= Dressing::SideMargin;
                const double clearance = inFront ? Dressing::DoorwayFrontClearance : Dressing::DoorwayBesideClearance;

                if (distance < clearance)
                {
                    findings.push_back({"dressing.door", "error", describeProp(prop) + " stands "
                            + roundedUnits(distance) + (inFront ? " in front of " : " beside ") + doorName(door)
                            + ": a container keeps " + roundedUnits(Dressing::DoorwayFrontClearance)
                            + " clear in front of a house door and " + roundedUnits(Dressing::DoorwayBesideClearance)
                            + " beside it",
                        "Move it along the house's wall, away from the door, or to a corner of the house."});
                    break;
                }
            }
            else if (walkingSize && beyond <= prop.pKind->radius
                && distance - prop.pKind->radius < Dressing::FreeGap)
            {
                // Anything else before the door, within the party's 128 of it.
                findings.push_back({"dressing.door", setPiece ? "warning" : "error", describeProp(prop)
                        + " stands " + roundedUnits(distance) + " in front of " + doorName(door)
                        + ": nothing stands within " + roundedUnits(Dressing::FreeGap) + " before a house door"
                        + (setPiece ? " (a set piece: fix it or keep it under \"Dressing exceptions\")" : ""),
                    "Move it aside, clear of the door."});
                break;
            }
        }

        // Against a house's wall: a container by a house (within 512 of a model's wall) stands within 240 of it.
        if (prop.propClass == PropClass::Container && wall <= Dressing::ByAHouse && wall > Dressing::WallReach)
        {
            findings.push_back({"dressing.wall", "warning", describeProp(prop) + " stands " + roundedUnits(wall)
                    + " from the nearest wall of a model: by a house, containers stand against its wall, within "
                    + roundedUnits(Dressing::WallReach),
                "Set it against the house's wall or in a corner, away from the door."});
        }

        // On a road (its body within 64 of the road's middle line), unless against a wall (a house by the road).
        const double road = distanceToRoad(prop.at, cellKinds);

        if (walkingSize && wall > prop.pKind->radius + Dressing::WalkingLineMargin
            && road - prop.pKind->radius < Dressing::RoadMiddle)
        {
            findings.push_back({"dressing.road", setPiece ? "warning" : "error", describeProp(prop) + " stands "
                    + roundedUnits(road) + " from the middle of a road: no prop stands on a road away from a wall"
                    + (setPiece ? " (a set piece: fix it or keep it under \"Dressing exceptions\")" : ""),
                "Move it off the road, at least " + roundedUnits(std::ceil(prop.pKind->radius + Dressing::RoadMiddle
                    - road)) + " further to its verge."});
        }

        if (!walkingSize)
        {
            continue;
        }

        // A prop against a model's wall is off the walking lines (decision D-14); the free gap still counts.
        bool onLine = wall <= prop.pKind->radius + Dressing::WalkingLineMargin;
        bool narrowed = false;

        for (const DoorLine &line : lines)
        {
            if (prop.z >= line.low - 256.0 && prop.z <= line.high + 256.0)
            {
                checkWalkingLine(prop, line.from, line.to, line.where, walls, props, onLine, narrowed, findings);
            }
        }
    }

    findings.push_back({"dressing.outdoor", "info", std::to_string(props.size()) + " props, "
            + std::to_string(doors.size()) + " house doors and " + std::to_string(lines.size())
            + " walking lines between them checked", ""});

    // Clumps of three or more containers (outdoors no storerooms).
    std::vector<const DressingProp *> containers;

    for (const DressingProp &prop : props)
    {
        if (prop.propClass == PropClass::Container)
        {
            containers.push_back(&prop);
        }
    }

    for (const std::vector<size_t> &clump : containerClumps(containers))
    {
        findings.push_back({"dressing.clump", "warning", std::to_string(clump.size())
                + " containers stand together (decorations " + entityList(clump)
                + "): outdoors, keep singles and pairs by a house's wall",
            "Spread them along the walls in singles and pairs."});
    }

    return findings;
}

// tools/xeen/check_props_support.py, families F3 and F6 of the user's play feedback (2026-11-21): what props and
// chests stand on, what the chests look like and what they stand in front of.
namespace Support
{
// What the party steps onto counts as under a base; a footprint sample may sit this far over the ground.
constexpr double Step = 24.0;
constexpr double Overhang = 24.0;
// How far beyond the footprint an edge counts, and the drop there that makes one (a 45 degree slope over the reach is
// not one).
constexpr double EdgeReach = 48.0;
constexpr double EdgeDrop = 64.0;
constexpr double FloorNormalZ = 0.6;
// Indoors a table or a shelf is no deeper than this.
constexpr double Furniture = 128.0;
// Outdoors what a prop other than a container may hang over a hillside, and the drop beside it that still reads as a
// steep hillside, not an edge.
constexpr double SlopeOverhang = 48.0;
constexpr double SlopeEdgeDrop = 96.0;
constexpr double Cell = 512.0;
// A chest keeps this far in front of an opening (outdoors; indoors the indoor dressing's door clearance), and a cave
// mouth's dark door face, at the back of its arch, reaches this much further out.
constexpr double OutdoorOpeningReach = 320.0;
constexpr double IndoorOpeningReach = 192.0;
constexpr double MouthDepth = 256.0;
}

// A face as the support rules read it: its points, its plane (the stored normal, made unit), its texture (lower case),
// event, group (indoors the faces of its event, outdoors its model; -1 none), whether it is a floor and a portal.
struct SupportFace
{
    std::vector<std::array<double, 3>> points;
    std::array<double, 3> normal = {};
    double distance = 0.0;
    std::string texture;
    int event = 0;
    int64_t group = -1;
    bool floor = false;
    bool portal = false;
    std::array<double, 3> low = {};
    std::array<double, 3> high = {};
};

// Every face of a map, bucketed by 512 cells, and the terrain outdoors.
struct SupportWorld
{
    std::vector<SupportFace> faces;
    std::map<std::pair<int64_t, int64_t>, std::vector<size_t>> grid;
    const Game::OutdoorMapData *pOutdoor = nullptr;
};

int64_t supportCell(double value)
{
    return static_cast<int64_t>(std::floor(value / Support::Cell));
}

void addSupportFace(SupportWorld &world, const std::vector<std::array<double, 3>> &points,
    std::array<double, 3> normal, const std::string &texture, int event, int64_t group, bool portal)
{
    if (points.size() < 3)
    {
        return;
    }

    const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);
    const double scale = length > 0.0 ? length : 1.0;
    SupportFace face;
    face.points = points;
    face.normal = {normal[0] / scale, normal[1] / scale, normal[2] / scale};
    face.distance = -(face.normal[0] * points[0][0] + face.normal[1] * points[0][1] + face.normal[2] * points[0][2]);
    face.texture = trimmedLower(texture);
    face.event = event;
    face.group = group;
    face.portal = portal;
    face.floor = face.normal[2] >= Support::FloorNormalZ && !portal;
    face.low = points[0];
    face.high = points[0];

    for (const std::array<double, 3> &point : points)
    {
        for (size_t axis = 0; axis < 3; ++axis)
        {
            face.low[axis] = std::min(face.low[axis], point[axis]);
            face.high[axis] = std::max(face.high[axis], point[axis]);
        }
    }

    const size_t index = world.faces.size();
    world.faces.push_back(std::move(face));
    const SupportFace &added = world.faces.back();

    for (int64_t x = supportCell(added.low[0]); x <= supportCell(added.high[0]); ++x)
    {
        for (int64_t y = supportCell(added.low[1]); y <= supportCell(added.high[1]); ++y)
        {
            world.grid[{x, y}].push_back(index);
        }
    }
}

SupportWorld supportWorldOf(const LoadedMap &map)
{
    SupportWorld world;

    if (map.outdoor)
    {
        world.pOutdoor = &*map.outdoor;

        for (size_t modelIndex = 0; modelIndex < map.outdoor->bmodels.size(); ++modelIndex)
        {
            const Game::OutdoorBModel &model = map.outdoor->bmodels[modelIndex];

            for (const Game::OutdoorBModelFace &face : model.faces)
            {
                std::vector<std::array<double, 3>> points;

                for (const uint16_t vertexIndex : face.vertexIndices)
                {
                    if (vertexIndex < model.vertices.size())
                    {
                        const Game::OutdoorBModelVertex &vertex = model.vertices[vertexIndex];
                        points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
                    }
                }

                addSupportFace(world, points, {double(face.planeNormalX), double(face.planeNormalY),
                        double(face.planeNormalZ)}, face.textureName, face.cogTriggeredNumber,
                    static_cast<int64_t>(modelIndex), false);
            }
        }
    }
    else if (map.indoor)
    {
        const Game::IndoorMapData &indoor = *map.indoor;

        for (const Game::IndoorFace &face : indoor.faces)
        {
            std::vector<std::array<double, 3>> points;

            for (const uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex < indoor.vertices.size())
                {
                    const Game::IndoorVertex &vertex = indoor.vertices[vertexIndex];
                    points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
                }
            }

            // The stored plane; a face without one by its polygon (Newell's normal).
            std::array<double, 3> normal = {0.0, 0.0, 0.0};

            if (face.planeNormal)
            {
                normal = {double((*face.planeNormal)[0]), double((*face.planeNormal)[1]),
                    double((*face.planeNormal)[2])};
            }
            else
            {
                for (size_t index = 0; index < points.size(); ++index)
                {
                    const std::array<double, 3> &a = points[index];
                    const std::array<double, 3> &b = points[(index + 1) % points.size()];
                    normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
                    normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
                    normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
                }
            }

            addSupportFace(world, points, normal, face.textureName, face.cogTriggered,
                face.cogTriggered != 0 ? int64_t(face.cogTriggered) : -1, face.isPortal);
        }
    }

    return world;
}

// Inside a polygon seen from above; on (within 1 of) an edge counts as inside (a prop on a seam between two floors).
bool insidePlan(const std::vector<std::array<double, 3>> &points, double x, double y)
{
    bool inside = false;
    const size_t count = points.size();

    for (size_t index = 0; index < count; ++index)
    {
        const std::array<double, 3> &a = points[index];
        const std::array<double, 3> &b = points[(index + 1) % count];

        if ((a[1] > y) != (b[1] > y) && x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
        {
            inside = !inside;
        }
    }

    if (inside)
    {
        return true;
    }

    for (size_t index = 0; index < count; ++index)
    {
        const std::array<double, 3> &a = points[index];
        const std::array<double, 3> &b = points[(index + 1) % count];
        const double dx = b[0] - a[0];
        const double dy = b[1] - a[1];
        const double length = dx * dx + dy * dy;

        if (length == 0.0)
        {
            continue;
        }

        const double t = std::clamp(((x - a[0]) * dx + (y - a[1]) * dy) / length, 0.0, 1.0);
        const double ex = a[0] + t * dx - x;
        const double ey = a[1] + t * dy - y;

        if (ex * ex + ey * ey < 1.0)
        {
            return true;
        }
    }

    return false;
}

// The highest ground or floor at (x, y) no more than a step over z; z itself when the ground there rises over that
// (the prop's side is sunk in a slope, which holds it); nothing when there is nothing under it. The floors of
// `skipGroup` (a chest's own) do not count. The ground is the game's: its terrain triangles split north-west to
// south-east.
std::optional<double> supportUnder(const SupportWorld &world, double x, double y, double z, int64_t skipGroup = -1)
{
    std::optional<double> best;

    if (world.pOutdoor != nullptr)
    {
        const double ground = Game::outdoorNativeTerrainHeight(*world.pOutdoor,
            Game::outdoorWorldToGridXFloat(float(x)), Game::outdoorWorldToGridYFloat(float(y)));
        best = ground <= z + Support::Step ? ground : z;
    }

    const std::map<std::pair<int64_t, int64_t>, std::vector<size_t>>::const_iterator cell =
        world.grid.find({supportCell(x), supportCell(y)});

    if (cell == world.grid.end())
    {
        return best;
    }

    for (const size_t index : cell->second)
    {
        const SupportFace &face = world.faces[index];

        if (!face.floor || (skipGroup >= 0 && face.group == skipGroup)
            || x < face.low[0] - 0.5 || x > face.high[0] + 0.5 || y < face.low[1] - 0.5 || y > face.high[1] + 0.5
            || !insidePlan(face.points, x, y))
        {
            continue;
        }

        const double height = -(face.normal[0] * x + face.normal[1] * y + face.distance) / face.normal[2];

        if (height <= z + Support::Step && (!best || height > *best))
        {
            best = height;
        }
    }

    return best;
}

// Whether a wall (an upright face, not a portal) standing over z + 16 crosses the plan segment a-b.
bool supportWallBetween(const SupportWorld &world, const std::array<double, 2> &a, const std::array<double, 2> &b,
    double z)
{
    std::set<size_t> seen;

    for (const std::pair<int64_t, int64_t> &key : {std::pair<int64_t, int64_t>{supportCell(a[0]), supportCell(a[1])},
             std::pair<int64_t, int64_t>{supportCell(b[0]), supportCell(b[1])}})
    {
        const std::map<std::pair<int64_t, int64_t>, std::vector<size_t>>::const_iterator cell = world.grid.find(key);

        if (cell == world.grid.end())
        {
            continue;
        }

        for (const size_t index : cell->second)
        {
            if (!seen.insert(index).second)
            {
                continue;
            }

            const SupportFace &face = world.faces[index];

            if (face.portal || std::abs(face.normal[2]) >= 0.7 || z + 16.0 < face.low[2] || z + 16.0 > face.high[2])
            {
                continue;
            }

            // Its ends: the points furthest along it each way.
            UprightFace wall;
            double least = 0.0;
            double most = 0.0;

            for (size_t point = 0; point < face.points.size(); ++point)
            {
                const double along = -face.points[point][0] * face.normal[1] + face.points[point][1] * face.normal[0];

                if (point == 0 || along < least)
                {
                    least = along;
                    wall.from = {face.points[point][0], face.points[point][1]};
                }

                if (point == 0 || along > most)
                {
                    most = along;
                    wall.to = {face.points[point][0], face.points[point][1]};
                }
            }

            if (crossesWall(a, b, wall))
            {
                return true;
            }
        }
    }

    return false;
}

std::vector<std::array<double, 2>> supportRing(double x, double y, double radius)
{
    std::vector<std::array<double, 2>> points;

    for (int index = 0; index < 8; ++index)
    {
        const double angle = 2.0 * std::numbers::pi * index / 8.0;
        points.push_back({x + radius * std::cos(angle), y + radius * std::sin(angle)});
    }

    return points;
}

// The corners and edge middles of a box seen from above, grown by `grow`.
std::vector<std::array<double, 2>> supportBoxPoints(
    const std::array<double, 3> &low, const std::array<double, 3> &high, double grow)
{
    const std::array<double, 3> xs = {low[0] - grow, (low[0] + high[0]) * 0.5, high[0] + grow};
    const std::array<double, 3> ys = {low[1] - grow, (low[1] + high[1]) * 0.5, high[1] + grow};
    std::vector<std::array<double, 2>> points;

    for (size_t x = 0; x < 3; ++x)
    {
        for (size_t y = 0; y < 3; ++y)
        {
            if (x != 1 || y != 1)
            {
                points.push_back({xs[x], ys[y]});
            }
        }
    }

    return points;
}

// The worst overhang below the base under the footprint and the worst drop just beyond it. A point with no floor
// under it (indoors: in or behind a wall) or behind a wall from the prop's middle is no drop: the prop stands against
// that wall.
std::pair<double, double> judgeFootprint(const SupportWorld &world, double base,
    const std::vector<std::array<double, 2>> &footprint, const std::vector<std::array<double, 2>> &margin,
    const std::array<double, 2> &centre, int64_t skipGroup = -1)
{
    const auto worst = [&](const std::vector<std::array<double, 2>> &points)
    {
        double most = points.empty() ? 0.0 : -1.0e18;

        for (const std::array<double, 2> &point : points)
        {
            const std::optional<double> under = supportUnder(world, point[0], point[1], base, skipGroup);
            const double gap = !under || supportWallBetween(world, centre, point, base) ? 0.0 : base - *under;
            most = std::max(most, gap);
        }

        return most;
    };

    return {worst(footprint), worst(margin)};
}
}

std::vector<AuditFinding> auditDressing(const LoadedMap &map, const std::string &decorationTableText,
    const std::set<int> &hanging, const std::set<int> &storerooms, const std::vector<uint8_t> &cellKinds)
{
    std::vector<AuditFinding> findings;
    const DressingKinds kinds = readDressingKinds(decorationTableText);

    if (kinds.empty())
    {
        return findings;
    }

    if (map.outdoor)
    {
        return auditOutdoorDressing(map, kinds, hanging, cellKinds);
    }

    if (!map.indoor)
    {
        return findings;
    }

    const Game::IndoorMapData &indoor = *map.indoor;

    // The faces of doors, by face.
    std::set<size_t> doorFaces;

    if (map.state)
    {
        for (const Game::MapDeltaDoor &door : map.state->doors)
        {
            doorFaces.insert(door.faceIds.begin(), door.faceIds.end());
        }
    }

    // Walls, door leaves and doorways (portals one walks through: upright, a party wide, at most a door wide); the
    // level faces (floors, tops, ceilings) for what stands on the floor.
    std::vector<UprightFace> walls;
    std::vector<UprightFace> leaves;
    std::vector<UprightFace> doorways;
    RayScene levels;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];
        const std::optional<UprightFace> upright = uprightFace(indoor, faceIndex);
        const bool portal = face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal);

        if (!upright)
        {
            if (!portal && face.vertexIndices.size() >= 3)
            {
                std::vector<std::array<double, 3>> points;

                for (const uint16_t vertexIndex : face.vertexIndices)
                {
                    if (vertexIndex < indoor.vertices.size())
                    {
                        const Game::IndoorVertex &vertex = indoor.vertices[vertexIndex];
                        points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
                    }
                }

                levels.addFace(points, {0.0, 0.0, 0.0}, static_cast<int32_t>(faceIndex), face.textureName);
            }

            continue;
        }

        const bool tall = upright->high - upright->low >= 128.0;
        const bool wide = upright->width() >= 2.0 * Dressing::PartyRadius;

        if (portal)
        {
            if (tall && wide && upright->width() <= Dressing::WidestDoorway)
            {
                doorways.push_back(*upright);
            }
        }
        else if (doorFaces.contains(faceIndex))
        {
            if (tall && wide)
            {
                leaves.push_back(*upright);
            }
        }
        else if (!Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
            || !Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Untouchable))
        {
            walls.push_back(*upright);
        }
    }

    levels.build();

    // The props: blocking decorations of the table, with their sector, class and whether they stand on its floor.
    std::vector<DressingProp> props;
    std::map<size_t, int> entityRooms;

    for (size_t sectorIndex = 0; sectorIndex < indoor.sectors.size(); ++sectorIndex)
    {
        for (const uint16_t entityIndex : indoor.sectors[sectorIndex].decorationIds)
        {
            entityRooms[entityIndex] = static_cast<int>(sectorIndex);
        }
    }

    for (size_t entityIndex = 0; entityIndex < indoor.entities.size(); ++entityIndex)
    {
        const Game::IndoorEntity &entity = indoor.entities[entityIndex];
        const DressingKind *pKind = propKindOf(
            kinds, entity.decorationListId, entity.name, hanging.contains(static_cast<int>(entityIndex)));

        if (pKind == nullptr)
        {
            continue;
        }

        const std::map<size_t, int>::const_iterator room = entityRooms.find(entityIndex);
        DressingProp prop;
        prop.entity = entityIndex;
        prop.name = entity.name;
        prop.at = {double(entity.x), double(entity.y)};
        prop.z = double(entity.z);
        prop.room = room != entityRooms.end() ? room->second : -1;
        prop.pKind = pKind;

        // On the floor: within 24 of its sector's lowest level face under it (a goblet on a table is not).
        double lowest = 1.0e18;

        for (const std::pair<double, int32_t> &height : levels.heightsAt(prop.at[0], prop.at[1]))
        {
            if (height.second >= 0 && size_t(height.second) < indoor.faces.size()
                && indoor.faces[size_t(height.second)].roomNumber == prop.room && height.first <= prop.z + 4.0)
            {
                lowest = std::min(lowest, height.first);
            }
        }

        prop.onFloor = lowest > 1.0e17 || prop.z - lowest <= Dressing::OnFloor;
        prop.propClass = propClassOf(*pKind, entity.eventIdPrimary != 0 || entity.eventIdSecondary != 0, prop.onFloor);
        props.push_back(prop);
    }

    // Containers by room: storerooms hold 8 or more, or are tagged.
    std::map<int, std::vector<const DressingProp *>> roomContainers;

    for (const DressingProp &prop : props)
    {
        if (prop.propClass == PropClass::Container && prop.room >= 0)
        {
            roomContainers[prop.room].push_back(&prop);
        }
    }

    const auto storeroom = [&](int room)
    {
        const std::map<int, std::vector<const DressingProp *>>::const_iterator found = roomContainers.find(room);
        return storerooms.contains(room)
            || (found != roomContainers.end() && found->second.size() >= Dressing::StoreroomContainers);
    };

    for (const DressingProp &prop : props)
    {
        if (prop.propClass != PropClass::Container)
        {
            continue;
        }

        // Door faces: within 192 of the leaf's plane, beside it no further than its width and 64.
        for (const UprightFace &leaf : leaves)
        {
            double beyond = 0.0;
            const double distance = distanceToSegment(prop.at, leaf.from, leaf.to, &beyond);

            if (spansHeight(leaf, prop.z) && beyond <= Dressing::SideMargin && distance < Dressing::DoorClearance)
            {
                findings.push_back({"dressing.door", "error", describeProp(prop) + " stands "
                        + roundedUnits(distance) + " from the door face " + std::to_string(leaf.face)
                        + ": a container keeps " + roundedUnits(Dressing::DoorClearance) + " clear of a door",
                    "Move it along the wall, away from the door, or into a corner."});
                break;
            }
        }

        // Doorways: 320 in front of the opening (its foot within the opening and 64 past its ends), 192 beside it.
        for (const UprightFace &doorway : doorways)
        {
            double beyond = 0.0;
            const double distance = distanceToSegment(prop.at, doorway.from, doorway.to, &beyond);
            const bool inFront = beyond <= Dressing::SideMargin;
            const double clearance = inFront ? Dressing::DoorwayFrontClearance : Dressing::DoorwayBesideClearance;

            if (spansHeight(doorway, prop.z) && distance < clearance)
            {
                findings.push_back({"dressing.doorway", "error", describeProp(prop) + " stands "
                        + roundedUnits(distance) + (inFront ? " in front of" : " beside")
                        + " the doorway of face " + std::to_string(doorway.face) + " (sectors "
                        + std::to_string(doorway.room) + " and " + std::to_string(doorway.roomBehind)
                        + "): a container keeps " + roundedUnits(Dressing::DoorwayFrontClearance)
                        + " clear in front of an open doorway and " + roundedUnits(Dressing::DoorwayBesideClearance)
                        + " beside it",
                    "Move it into the room, against a wall away from the opening."});
                break;
            }
        }

        // Against a wall (of any sector: a room may be several).
        const bool stored = storeroom(prop.room);
        const double nearest = nearestWall(prop, walls);
        const double reach = stored ? Dressing::StoreroomWallReach : Dressing::WallReach;

        if (nearest < 1.0e17 && nearest > reach)
        {
            findings.push_back({"dressing.wall", "warning", describeProp(prop) + " stands " + roundedUnits(nearest)
                    + " from the nearest wall: containers stand against a wall, within " + roundedUnits(reach)
                    + (stored ? " in a storeroom" : " (320 in a storeroom)"),
                "Set it against a wall or in a corner, its centre about a radius and a hand from the wall."});
        }
    }

    // Clumps of three or more containers outside storerooms.
    for (const std::pair<const int, std::vector<const DressingProp *>> &room : roomContainers)
    {
        if (storeroom(room.first))
        {
            continue;
        }

        for (const std::vector<size_t> &clump : containerClumps(room.second))
        {
            findings.push_back({"dressing.clump", "warning", std::to_string(clump.size())
                    + " containers stand together in sector " + std::to_string(room.first) + " (decorations "
                    + entityList(clump) + "), which holds " + std::to_string(room.second.size())
                    + ": clumps of three or more belong in storerooms (8 or more containers, or `store: true`)",
                "Keep singles and pairs along the walls, or make the room a storeroom."});
        }
    }

    // The openings of each sector (doorways and doors), side by side ones merged.
    std::map<int, std::vector<const UprightFace *>> sectorFaces;

    for (const std::vector<UprightFace> *pFaces : {&doorways, &leaves})
    {
        for (const UprightFace &face : *pFaces)
        {
            sectorFaces[face.room].push_back(&face);

            if (face.roomBehind != face.room)
            {
                sectorFaces[face.roomBehind].push_back(&face);
            }
        }
    }

    std::map<int, std::vector<Opening>> openings;

    for (const std::pair<const int, std::vector<const UprightFace *>> &sector : sectorFaces)
    {
        openings[sector.first] = mergedOpenings(sector.second);
    }

    const auto faceList = [](const Opening &opening)
    {
        std::string list;

        for (const size_t face : opening.faces)
        {
            list += (list.empty() ? "" : "+") + std::to_string(face);
        }

        return list;
    };

    // The walking lines between two openings of a prop's sector.
    for (const DressingProp &prop : props)
    {
        const std::map<int, std::vector<Opening>>::const_iterator room = openings.find(prop.room);

        if (prop.room < 0 || room == openings.end() || !prop.onFloor
            || prop.pKind->radius < Dressing::WalkingLineRadius)
        {
            continue;
        }

        const std::vector<Opening> &ways = room->second;
        bool onLine = false;
        bool narrowed = false;

        for (size_t first = 0; first < ways.size(); ++first)
        {
            for (size_t second = first + 1; second < ways.size(); ++second)
            {
                const Opening &a = ways[first];
                const Opening &b = ways[second];

                // At the openings' level (stairs between them included).
                if (prop.z < std::min(a.low, b.low) - Dressing::OnFloor
                    || prop.z > std::max(a.low, b.low) + Dressing::OnFloor)
                {
                    continue;
                }

                const std::string where = " the walking line between the openings of faces " + faceList(a) + " and "
                    + faceList(b) + " of sector " + std::to_string(prop.room);
                checkWalkingLine(prop, a.middle(), b.middle(), where, walls, props, onLine, narrowed, findings);
            }
        }
    }

    return findings;
}

std::vector<AuditFinding> auditPropSupport(const LoadedMap &map, const std::string &decorationTableText,
    const std::string &flowJson, const std::set<int> &hanging)
{
    std::vector<AuditFinding> findings;

    if (!map.indoor && !map.outdoor)
    {
        return findings;
    }

    const bool outdoors = map.outdoor.has_value();
    const SupportWorld world = supportWorldOf(map);
    const DressingKinds kinds = readDressingKinds(decorationTableText);
    // Plants grow on slopes; natural rocks lie where the land puts them, half sunk or at a cliff's lip: not judged.
    static const std::regex naturalWords("\\brock|boulder|basalt|stalagmite|crag|plant|bush|flower|fern|shrub|grass"
        "|reed|mushroom|weed|cactus|vine|lily|stump|log\\b");
    const auto at = [](double x, double y, double z)
    {
        return " at [" + roundedUnits(x) + ", " + roundedUnits(y) + ", " + roundedUnits(z) + "]";
    };

    // The props: the decorations (outdoors the scene's) whose rows block, not hanging, no markers, no plants or rocks.
    const size_t entityCount = outdoors ? map.outdoor->entities.size() : map.indoor->entities.size();

    for (size_t entityIndex = 0; entityIndex < entityCount; ++entityIndex)
    {
        std::string name;
        int listId = 0;
        std::array<double, 3> position = {};
        int event = 0;

        if (outdoors)
        {
            const Game::OutdoorEntity &entity = map.outdoor->entities[entityIndex];
            name = entity.name;
            listId = entity.decorationListId;
            position = {double(entity.x), double(entity.y), double(entity.z)};
            event = entity.eventIdSecondary != 0 ? entity.eventIdSecondary : entity.eventIdPrimary;
        }
        else
        {
            const Game::IndoorEntity &entity = map.indoor->entities[entityIndex];
            name = entity.name;
            listId = entity.decorationListId;
            position = {double(entity.x), double(entity.y), double(entity.z)};
            event = entity.eventIdSecondary != 0 ? entity.eventIdSecondary : entity.eventIdPrimary;
        }

        if (hanging.contains(static_cast<int>(entityIndex)))
        {
            continue;
        }

        // The row by its name, else by its number.
        const std::map<std::string, int>::const_iterator named = kinds.idByName.find(trimmedLower(name));
        std::map<int, DressingKind>::const_iterator row =
            kinds.byId.find(named != kinds.idByName.end() ? named->second : listId);

        if (row == kinds.byId.end())
        {
            row = kinds.byId.find(listId);
        }

        if (row == kinds.byId.end())
        {
            continue;
        }

        const DressingKind &kind = row->second;
        const std::string hint = trimmedLower(kind.hint);
        const std::string rowName = trimmedLower(kind.name);

        if (!kind.blocks || hint.empty() || hint == "null" || hint == "pending" || decorationHangs(name)
            || rowName.starts_with("7tree") || rowName.starts_with("tree") || hint.find("tree") != std::string::npos
            || std::regex_search(rowName + " " + hint, naturalWords))
        {
            continue;
        }

        const double x = position[0];
        const double y = position[1];
        const double z = position[2];
        const double radius = kind.radius;
        const std::string label = "decoration " + std::to_string(entityIndex) + " (" + name + ", row "
            + kind.name + ", radius " + roundedUnits(radius) + ")" + at(x, y, z);
        const std::optional<double> middle = supportUnder(world, x, y, z);

        if (!middle || z - *middle > Support::Step)
        {
            // Over another decoration (within its radius, above its foot) it stands on that one: the glowing orb over
            // a dimensional travel pedestal, which a scene overlay adds (the Python tool read no overlays).
            bool onDecoration = false;

            for (size_t otherIndex = 0; otherIndex < entityCount && !onDecoration; ++otherIndex)
            {
                std::array<double, 3> other = {};
                int otherListId = 0;
                std::string otherName;

                if (outdoors)
                {
                    const Game::OutdoorEntity &entity = map.outdoor->entities[otherIndex];
                    other = {double(entity.x), double(entity.y), double(entity.z)};
                    otherListId = entity.decorationListId;
                    otherName = entity.name;
                }
                else
                {
                    const Game::IndoorEntity &entity = map.indoor->entities[otherIndex];
                    other = {double(entity.x), double(entity.y), double(entity.z)};
                    otherListId = entity.decorationListId;
                    otherName = entity.name;
                }

                const std::map<std::string, int>::const_iterator otherNamed =
                    kinds.idByName.find(trimmedLower(otherName));
                const std::map<int, DressingKind>::const_iterator otherRow =
                    kinds.byId.find(otherNamed != kinds.idByName.end() ? otherNamed->second : otherListId);
                onDecoration = otherIndex != entityIndex && otherRow != kinds.byId.end() && other[2] < z
                    && std::hypot(other[0] - x, other[1] - y) <= otherRow->second.radius;
            }

            if (onDecoration)
            {
                continue;
            }

            findings.push_back({"support.floating", "error", label + " floats: nothing under its middle within "
                    + roundedUnits(Support::Step) + (middle ? " (ground " + roundedUnits(*middle) + ")" : ""),
                "Stand it on the ground or floor under it, or mark it as hanging."});
            continue;
        }

        const double base = std::max(z, *middle);
        const bool setPiece = kind.setPiece || event != 0;
        std::vector<std::array<double, 2>> margin = supportRing(x, y, radius + Support::EdgeReach);
        const std::vector<std::array<double, 2>> inner = supportRing(x, y, radius + Support::EdgeReach / 2.0);
        margin.insert(margin.end(), inner.begin(), inner.end());
        std::pair<double, double> judged =
            judgeFootprint(world, base, supportRing(x, y, radius * 0.85), margin, {x, y});
        double overhang = judged.first;
        double drop = judged.second;
        const std::string propClass = kind.container ? "container" : setPiece ? "set piece" : "other";

        // Indoors small things stand on tables and shelves (a candle, a cup, a crystal ball): only a drop deeper than
        // furniture counts for them. Containers stand on the floor. Outdoors a bone pile or a skull pole may lie on a
        // hillside: only a container must stand level.
        if (!kind.container)
        {
            const double overhangAllowed = outdoors ? Support::SlopeOverhang : Support::Furniture;
            const double dropAllowed = outdoors ? Support::SlopeEdgeDrop : Support::Furniture;
            overhang = overhang > overhangAllowed ? overhang : 0.0;
            drop = drop > dropAllowed ? drop : 0.0;
        }

        if (overhang > Support::Overhang)
        {
            findings.push_back({"support.overhang", setPiece ? "warning" : "error", label + ", a " + propClass
                    + ": part of its footprint is " + roundedUnits(std::min(overhang, 9999.0))
                    + " over the ground or floor",
                "Move it onto the ground or floor, clear of the edge."});
        }
        else if (drop > Support::EdgeDrop)
        {
            findings.push_back({"support.edge", setPiece ? "warning" : "error", label + ", a " + propClass
                    + ": a drop of " + roundedUnits(std::min(drop, 9999.0)) + " within "
                    + roundedUnits(Support::EdgeReach) + " of its footprint (it stands at an edge)",
                "Move it back from the edge, against a wall or into the room."});
        }
    }

    // The chests: things whose click opens one, or clicked things built mostly of chest pieces (a chest that asks a
    // question first is a panel).
    std::map<int, std::string> modelNames;
    const std::vector<InteractiveThing> things = outdoors ? listOutdoorInteractiveThings(map, flowJson, modelNames)
        : listInteractiveThings(map, flowJson, CoplanarNames());
    std::map<std::string, std::set<int>> eventsByKind;

    for (const InteractiveThing &thing : things)
    {
        eventsByKind[thing.kind].insert(thing.eventId);
    }

    // MM6's chest kinds (ch1 to ch5 pieces, ch001 to ch006).
    static const std::regex mm6Chest("^ch[1-5](frle|frntb?|frre|side|top|tople|topre|topb|toplb|toprb|tpbv|tplev"
        "|tprev|topv|bkre|bkle)$|^ch00[1-6][a-h]$");
    static const std::regex bookcase("books|cab");
    static const std::regex furniture(
        "sarcophag|coffin|cabinet|bookcase|shelf|desk|wardrobe|cupboard|dresser", std::regex::icase);
    // Titles that name a place rather than the box that opens.
    static const std::regex placeWords("\\b(den|cave|cavern|mine|adit|lair|hall|tower|house|camp|gate|grotto|hole"
        "|tunnel|passage|entrance|crypt|tomb|barrow|ruin|ruins|keep|fort|shrine|temple|well)\\b", std::regex::icase);
    static const std::regex containerTitleWords("chest|box|cache|crate|coffer|strongbox|hoard|loot|plunder|supplies"
        "|pack|goods|offerings|bag|sack|purse|trunk|casket|cask|barrel|stash|kit|satchel|case|haul|spoils|treasure"
        "|bundle|basket|urn|jar", std::regex::icase);
    static const std::set<std::string> crateTextures = {"7gt001a", "gt001a", "cr64", "crside"};
    static const std::set<std::string> mouthTextures = {"7solid01", "solid01", "blackwal"};
    static const std::array<const char *, 4> openingKinds = {"house", "exit", "door", "teleport"};
    const auto openingKindOf = [&eventsByKind](int event) -> const char *
    {
        for (const char *pKind : openingKinds)
        {
            const std::map<std::string, std::set<int>>::const_iterator kind = eventsByKind.find(pKind);

            if (kind != eventsByKind.end() && kind->second.contains(event))
            {
                return pKind;
            }
        }

        return nullptr;
    };

    // The openings: upright faces that enter a house, leave, open, teleport, or show a cave mouth's dark door.
    std::vector<size_t> openings;

    for (size_t index = 0; index < world.faces.size(); ++index)
    {
        const SupportFace &face = world.faces[index];

        if (!face.floor && std::abs(face.normal[2]) < 0.5
            && ((face.event != 0 && openingKindOf(face.event) != nullptr) || mouthTextures.contains(face.texture)))
        {
            openings.push_back(index);
        }
    }

    for (const InteractiveThing &thing : things)
    {
        std::map<std::string, int> textures;

        for (const std::pair<const std::string, int> &texture : thing.textures)
        {
            textures[trimmedLower(texture.first)] += texture.second;
        }

        int chestPieces = 0;

        for (const std::pair<const std::string, int> &texture : textures)
        {
            if (texture.first.starts_with("7gt002") || texture.first.starts_with("gt002")
                || std::regex_match(texture.first, mm6Chest))
            {
                chestPieces += texture.second;
            }
        }

        const int faceCount = static_cast<int>(thing.faces.size());

        if (thing.kind != "chest" && !(faceCount >= 9 && chestPieces * 2 > faceCount))
        {
            continue;
        }

        std::vector<size_t> chestFaces;

        for (size_t index = 0; index < world.faces.size(); ++index)
        {
            if (world.faces[index].event == thing.eventId)
            {
                chestFaces.push_back(index);
            }
        }

        if (chestFaces.empty())
        {
            continue;
        }

        std::array<double, 3> low = world.faces[chestFaces[0]].low;
        std::array<double, 3> high = world.faces[chestFaces[0]].high;

        for (const size_t index : chestFaces)
        {
            for (size_t axis = 0; axis < 3; ++axis)
            {
                low[axis] = std::min(low[axis], world.faces[index].low[axis]);
                high[axis] = std::max(high[axis], world.faces[index].high[axis]);
            }
        }

        const std::array<double, 2> middle = {(low[0] + high[0]) * 0.5, (low[1] + high[1]) * 0.5};
        const std::map<int, std::string>::const_iterator modelName = modelNames.find(thing.sector);
        const std::string group = !outdoors ? "sector " + std::to_string(thing.sector)
            : modelName != modelNames.end() ? modelName->second : "model " + std::to_string(thing.sector);
        const std::string label = "chest \"" + thing.title + "\" (event " + std::to_string(thing.eventId) + ", "
            + group + ")" + at(middle[0], middle[1], low[2]);

        // Shipped: MM7's or MM8's chest model (19 faces of the a, b, c, e and g pieces of 7gt002 or gt002), MM6's
        // chest kinds, a crate, a bookcase; and furniture that opens like a chest is no chest.
        bool shipped = faceCount >= 18;

        for (const char *pSuffix : {"a", "b", "c", "e", "g"})
        {
            shipped = shipped && (textures.contains(std::string("7gt002") + pSuffix)
                || textures.contains(std::string("gt002") + pSuffix));
        }

        bool allMm6 = true;
        bool allCrate = true;
        bool anyBookcase = false;

        for (const std::pair<const std::string, int> &texture : textures)
        {
            allMm6 = allMm6 && std::regex_match(texture.first, mm6Chest);
            allCrate = allCrate && crateTextures.contains(texture.first);
            anyBookcase = anyBookcase || std::regex_search(texture.first, bookcase);
        }

        shipped = shipped || allMm6 || allCrate || anyBookcase || std::regex_search(thing.title, furniture);

        if (!shipped)
        {
            std::string pieces;

            for (const std::pair<const std::string, int> &texture : textures)
            {
                pieces += (pieces.empty() ? "" : ", ") + texture.first + " " + std::to_string(texture.second);
            }

            findings.push_back({"chest.look", "error", label + ": " + std::to_string(faceCount) + " faces of " + pieces
                    + ": not a shipped chest (MM7/MM8 19 faces of 7gt002/gt002 pieces, MM6 ch1-ch5, a crate)",
                "Build it as one of the shipped chests (the studio's chest model) or a crate."});
        }

        if (std::regex_search(thing.title, placeWords) && !std::regex_search(thing.title, containerTitleWords))
        {
            findings.push_back({"chest.title", "warning", label + ": its hover title names a place, not the chest",
                "Name what opens: a chest, a crate, a cache."});
        }

        // In front of an opening: the chest's footprint against each opening face (outdoors 320 in front, 192 beside;
        // indoors the indoor dressing's 192 from a door's plane).
        const Game::IndoorSector *pSector = !outdoors && thing.sector >= 0
                && size_t(thing.sector) < map.indoor->sectors.size()
            ? &map.indoor->sectors[size_t(thing.sector)] : nullptr;

        for (const size_t index : openings)
        {
            const SupportFace &face = world.faces[index];
            const bool mouth = mouthTextures.contains(face.texture);
            const double reach = (outdoors ? Support::OutdoorOpeningReach : Support::IndoorOpeningReach)
                + (mouth && outdoors ? Support::MouthDepth : 0.0);

            if (face.event == thing.eventId || face.high[2] < low[2] - 64.0 || face.low[2] > high[2] + 64.0)
            {
                continue;
            }

            const double plan = std::hypot(face.normal[0], face.normal[1]);
            const std::array<double, 2> normal = {face.normal[0] / (plan > 0.0 ? plan : 1.0),
                face.normal[1] / (plan > 0.0 ? plan : 1.0)};
            const std::array<double, 2> centre = {
                (face.low[0] + face.high[0]) * 0.5, (face.low[1] + face.high[1]) * 0.5};

            // A cupboard: the chest's sector is a dead end (one portal) too shallow for anything in it to stand
            // `reach` from this face (XD-04's cabinet behind its wainscot panel). The door is the cupboard's own.
            if (pSector != nullptr && pSector->portalFaceIds.size() == 1)
            {
                double deepest = 0.0;

                for (const double cornerX : {double(pSector->minX), double(pSector->maxX)})
                {
                    for (const double cornerY : {double(pSector->minY), double(pSector->maxY)})
                    {
                        deepest = std::max(deepest,
                            std::abs((cornerX - centre[0]) * normal[0] + (cornerY - centre[1]) * normal[1]));
                    }
                }

                if (deepest <= reach + 64.0)
                {
                    continue;
                }
            }

            const std::array<double, 2> along = {-normal[1], normal[0]};
            double half = 0.0;

            for (const std::array<double, 3> &point : face.points)
            {
                half = std::max(half, std::abs((point[0] - centre[0]) * along[0] + (point[1] - centre[1]) * along[1]));
            }

            std::optional<double> worst;

            for (const std::array<double, 2> &point : supportBoxPoints(low, high, 0.0))
            {
                const double ahead = (point[0] - centre[0]) * normal[0] + (point[1] - centre[1]) * normal[1];
                const double side = std::abs((point[0] - centre[0]) * along[0] + (point[1] - centre[1]) * along[1]);

                if (std::abs(ahead) <= reach && side <= half + 64.0 && (!worst || std::abs(ahead) < std::abs(*worst)))
                {
                    worst = ahead;
                }
            }

            if (worst)
            {
                const char *pKind = openingKindOf(face.event);
                std::string other = face.texture;

                for (const InteractiveThing &opening : things)
                {
                    if (opening.eventId == face.event)
                    {
                        other = opening.title;
                        break;
                    }
                }

                findings.push_back({"chest.entrance", "error", label + " stands " + roundedUnits(std::abs(*worst))
                        + " from the " + (pKind != nullptr ? pKind : "cave mouth") + " face of \"" + other
                        + "\" (event " + std::to_string(face.event) + ", " + face.texture
                        + "), within its opening's width",
                    "Move it aside, out of the way in or out."});
                break;
            }
        }

        // What it stands on: the lowest corner of its faces, its own faces (indoors its event's, outdoors its model)
        // not counted.
        const std::pair<double, double> judged = judgeFootprint(world, low[2], supportBoxPoints(low, high, -4.0),
            supportBoxPoints(low, high, Support::EdgeReach), middle, world.faces[chestFaces[0]].group);

        if (judged.first > Support::Overhang)
        {
            findings.push_back({"support.overhang", "error", label + ": part of its footprint is "
                    + roundedUnits(std::min(judged.first, 9999.0)) + " over the ground or floor",
                "Move it onto the ground or floor, clear of the edge."});
        }
        else if (judged.second > Support::EdgeDrop)
        {
            findings.push_back({"support.edge", "error", label + ": a drop of "
                    + roundedUnits(std::min(judged.second, 9999.0)) + " within " + roundedUnits(Support::EdgeReach)
                    + " of its footprint (it stands at an edge)",
                "Move it back from the edge, against a wall or into the room."});
        }
    }

    return findings;
}

DressingFacts projectDressingFacts(const Project &built)
{
    DressingFacts facts;
    const YAML::Node identity = built.has("project.yml") ? built.document("project.yml")["identity"] : YAML::Node();

    if (identity && identity.IsMap() && identity["shape"] && identity["shape"].IsScalar())
    {
        facts.identityShape = identity["shape"].Scalar();
    }

    // D-91: the cave mouths that lead nowhere and are neither a shelter nor blocked.
    const YAML::Node structures = built.has("sketch.yml") ? built.document("sketch.yml")["structures"] : YAML::Node();

    for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size(); ++index)
    {
        const YAML::Node structure = structures[index];

        if (structure.IsMap() && structure["kind"] && structure["kind"].IsScalar()
            && structure["kind"].Scalar() == "cave_mouth" && !structure["into"] && !structure["form"])
        {
            facts.blindMouths.push_back(structure["id"] && structure["id"].IsScalar() ? structure["id"].Scalar()
                : "structures[" + std::to_string(index) + "]");
        }
    }

    if (!built.has("ids.lock.yml"))
    {
        return facts;
    }

    const YAML::Node lock = built.document("ids.lock.yml");
    const YAML::Node decorationNumbers = lock["decorations"];

    for (const YAML::Node &decoration : built.document("objects.yml")["decorations"])
    {
        const std::string id = decoration["id"] ? decoration["id"].Scalar() : std::string();
        const bool hangs = (decoration["hangs"] && decoration["hangs"].Scalar() == "true")
            || decoration["wall"].IsDefined();

        if (hangs && decorationNumbers.IsMap() && decorationNumbers[id])
        {
            facts.hanging.insert(decorationNumbers[id].as<int>());
        }
    }

    const YAML::Node doorNumbers = lock["doors"];

    for (const YAML::Node &lift : built.document("objects.yml")["lifts"])
    {
        const std::string id = lift["id"] ? lift["id"].Scalar() : std::string();

        if (lift["trap"] && lift["trap"].Scalar() == "true" && doorNumbers.IsMap() && doorNumbers[id])
        {
            facts.traps.insert(doorNumbers[id].as<int>());
        }
    }

    const YAML::Node sectorNumbers = lock["sectors"];

    for (const YAML::Node &room : built.document("rooms.yml")["rooms"])
    {
        const std::string id = room["id"] ? room["id"].Scalar() : std::string();

        if (room["store"] && room["store"].Scalar() == "true" && sectorNumbers.IsMap() && sectorNumbers[id])
        {
            facts.storerooms.insert(sectorNumbers[id].as<int>());
        }
    }

    return facts;
}

DressingFacts studioFileDressingFacts(const YAML::Node &studioFile)
{
    DressingFacts facts;

    for (const std::pair<const char *, std::set<int> *> list :
        {std::pair<const char *, std::set<int> *>{"hanging_decorations", &facts.hanging},
            std::pair<const char *, std::set<int> *>{"storerooms", &facts.storerooms},
            std::pair<const char *, std::set<int> *>{"trap_doors", &facts.traps}})
    {
        const YAML::Node numbers = studioFile.IsMap() ? studioFile[list.first] : YAML::Node();

        for (size_t index = 0; numbers.IsDefined() && numbers.IsSequence() && index < numbers.size(); ++index)
        {
            list.second->insert(numbers[index].as<int>());
        }
    }

    const YAML::Node identity = studioFile.IsMap() ? studioFile["identity"] : YAML::Node();

    if (identity && identity.IsMap() && identity["shape"] && identity["shape"].IsScalar())
    {
        facts.identityShape = identity["shape"].Scalar();
    }

    const YAML::Node blind = studioFile.IsMap() ? studioFile["blind_mouths"] : YAML::Node();

    for (size_t index = 0; blind.IsDefined() && blind.IsSequence() && index < blind.size(); ++index)
    {
        facts.blindMouths.push_back(blind[index].Scalar());
    }

    return facts;
}

std::vector<AuditFinding> auditBlindMouths(const std::vector<std::string> &blindMouths)
{
    std::vector<AuditFinding> findings;

    for (const std::string &id : blindMouths)
    {
        findings.push_back({"caves.blind_mouth", "error", "the cave mouth " + id + " shows a dark way in that "
                "leads nowhere (no `into`)",
            "Give it `into` (a way in), or make it `form: shelter` (a shallow open overhang, its back and floor lit, "
            "a light inside) or `form: blocked` (rubble fills the mouth) with a click line (D-91)."});
    }

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

std::vector<AuditFinding> auditRides(
    const LoadedMap &map, const std::string &flowJson, const CoplanarNames &names, const std::set<int> &traps)
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
        // (A trapdoor carries the party down once: no ride.)
        if (moving == eventsByDoor.end() || door.moveLength < 64 || traps.contains(static_cast<int>(door.doorId))
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
        for (const char *pWord : {"StatusText", "SimpleMessage", "SetMessage", "AskQuestion", "AskChoice", "door ",
                 "open chest", "GiveItem", "leave to", "teleport", "MoveToMap", "DamagePlayer", "SetTexture",
                 "SetSprite", "SummonMonsters", "SetLight", "CameraShake", "SetFacetBit", "SpeakNPC", "CastSpell",
                 "gold", "Gold", "PlaySound", "ShowMovie", "SetMonGroupBit", "Experience", "RemovePartyBuff"})
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

            // A question's continuation that shows nothing is the answer refused: the player saw the question.
            const bool continuation = path["tests"].size() > 0 && path["tests"][0]["what"]
                && path["tests"][0]["what"].Scalar().starts_with("answered:");

            if (visible || continuation)
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

std::vector<AuditFinding> auditEntranceWindows(const LoadedMap &map)
{
    std::vector<AuditFinding> findings;
    const std::string &script = map.scriptText;
    const std::regex handlerPattern(R"re(RegisterEvent\((\d+),\s*(nil|"((?:[^"\\]|\\.)*)"),\s*function)re");
    // evt.MoveToMap(x, y, z, direction, look, speed, text, picture, "map.blv"[, {options}])
    const std::regex movePattern(
        R"re(evt\.MoveToMap\(([^")]*)"([^"]+\.[bB][lL][vV])"\s*(,\s*\{([^}]*)\})?\s*\))re");
    const std::regex yesNoPattern(
        R"re((evt\.AskQuestion\([^{]*\{[^}]*"(?:[Yy]es|[Yy]|[Nn]o)"[^}]*\})|)re"
        R"re((AskChoiceWithAnswerSteps\([\s\S]*?Answer\s*=\s*"(?:[Yy]es|[Nn]o)"))re");
    std::string ownMap = map.fileName;
    std::transform(ownMap.begin(), ownMap.end(), ownMap.begin(),
        [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
    std::vector<std::pair<size_t, std::smatch>> starts;

    for (std::sregex_iterator match(script.begin(), script.end(), handlerPattern), end; match != end; ++match)
    {
        starts.push_back({static_cast<size_t>(match->position()), *match});
    }

    for (size_t index = 0; index < starts.size(); ++index)
    {
        const size_t from = starts[index].first;
        const size_t to = index + 1 < starts.size() ? starts[index + 1].first : script.size();
        const std::string body = script.substr(from, to - from);
        const std::string eventText = "event " + starts[index].second[1].str() + " (\""
            + starts[index].second[3].str() + "\")";
        bool movesIntoDungeon = false;

        for (std::sregex_iterator move(body.begin(), body.end(), movePattern), end; move != end; ++move)
        {
            std::string target = (*move)[2].str();
            std::transform(target.begin(), target.end(), target.begin(),
                [](unsigned char character) { return static_cast<char>(std::tolower(character)); });

            if (target == ownMap)
            {
                continue;
            }

            movesIntoDungeon = true;
            std::vector<std::string> numbers;
            std::stringstream arguments((*move)[1].str());
            std::string argument;

            while (std::getline(arguments, argument, ','))
            {
                argument.erase(std::remove_if(argument.begin(), argument.end(),
                    [](unsigned char character) { return std::isspace(character) != 0; }), argument.end());

                if (!argument.empty())
                {
                    numbers.push_back(argument);
                }
            }

            const bool direct = (*move)[4].str().find("direct") != std::string::npos;
            const bool noWindow = numbers.size() >= 8 && numbers[6] == "0" && numbers[7] == "0";

            if (noWindow && !direct)
            {
                findings.push_back({"entrance.no_window", "warning", eventText + " moves into " + (*move)[2].str()
                        + " with no entrance window (text and picture 0)",
                    "Leave `screen` out (the studio writes the standard window, picture 1), or say `screen: none` "
                    "for a move that has decided already (a fall, a throw, an answered question)."});
            }
        }

        if (movesIntoDungeon && std::regex_search(body, yesNoPattern))
        {
            findings.push_back({"entrance.question", "error", eventText + " asks Yes or No before a move into a "
                    "dungeon: the entrance window asks (OK, Close)",
                "Drop the question; a line of its own goes into the world's trans.txt and the door's `screen: "
                "{text: <its row>}` (D-90)."});
        }
    }

    return findings;
}

std::vector<AuditFinding> auditCaveShape(const LoadedMap &map, const std::string &identityShape)
{
    std::vector<AuditFinding> findings;

    if (!map.indoor || (identityShape != "cave" && identityShape != "mine"))
    {
        return findings;
    }

    const CaveShape shape = caveShapeOf(*map.indoor);
    const CaveShapeTargets targets = caveShapeTargets();
    const auto percent = [](double share) { return std::to_string(static_cast<int>(std::lround(share * 100.0))); };
    const std::string what = "a " + identityShape + " (identity.shape) ";

    if (shape.floorUnevenShare < targets.floorUnevenShare)
    {
        findings.push_back({"identity.cave_shape", "warning", what + "with " + percent(shape.floorUnevenShare)
                + " % of its floor uneven (shipped caves " + percent(targets.floorUnevenShare) + " % or more)",
            "Slope the floors (`floor_points`, rubble ramps) of the natural rooms, as MM8's Dragon Cave and MM6's "
            "mines are laid (oymap metrics: cave_shape.rooms lists the flattest)."});
    }

    if (shape.ceilingSpread < targets.ceilingSpread)
    {
        findings.push_back({"identity.cave_shape", "warning", what + "whose ceilings vary by "
                + std::to_string(static_cast<int>(std::lround(shape.ceilingSpread))) + " on average (shipped caves "
                + std::to_string(static_cast<int>(std::lround(targets.ceilingSpread))) + " or more)",
            "Give the natural rooms vaulted, broken ceilings (`ceiling_points`, stalactites)."});
    }

    if (shape.wallRoughShare < targets.wallRoughShare)
    {
        findings.push_back({"identity.cave_shape", "warning", what + "with " + percent(shape.wallRoughShare)
                + " % of its wall area rough (shipped caves " + percent(targets.wallRoughShare) + " % or more)",
            "Draw the natural rooms with irregular outlines off the grid and `rough` walls."});
    }

    return findings;
}
}
