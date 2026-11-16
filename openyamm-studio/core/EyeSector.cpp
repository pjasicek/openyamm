#include "core/EyeSector.h"

#include "core/Compare.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMovementController.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <optional>

namespace OpenYAMM::Studio
{
namespace
{
// A sample point's eye counts as in a sector when at least this many of its five rays (four level, one up) first
// meet that sector's faces from its side.
constexpr size_t EyeVotes = 3;
constexpr double SampleSpacing = 192.0;
constexpr size_t MaximumSamples = 24;
constexpr double RayReach = 8192.0;

std::string wholeText(double value)
{
    return std::to_string(static_cast<long long>(std::llround(value)));
}

std::string sectorName(const std::map<int, std::string> &names, int sector)
{
    const std::map<int, std::string>::const_iterator found = names.find(sector);
    return found != names.end() ? found->second + " (sector " + std::to_string(sector) + ")"
                                : "sector " + std::to_string(sector);
}

bool insidePlan(const std::vector<std::array<double, 3>> &points, double x, double y)
{
    bool inside = false;

    for (size_t index = 0, previous = points.size() - 1; index < points.size(); previous = index++)
    {
        const std::array<double, 3> &first = points[index];
        const std::array<double, 3> &second = points[previous];

        if ((first[1] > y) != (second[1] > y)
            && x < (second[0] - first[0]) * (y - first[1]) / (second[1] - first[1]) + first[0])
        {
            inside = !inside;
        }
    }

    return inside;
}
}

std::vector<EyeSectorFinding> findEyeOutsideSector(const Game::IndoorMapData &map, const Game::MapDeltaData *pState)
{
    std::vector<EyeSectorFinding> findings;
    const std::vector<Game::IndoorVertex> vertices =
        Game::buildIndoorMechanismAdjustedVertices(map, pState, nullptr);
    Game::IndoorFaceGeometryCache cache(map.faces.size());
    // Every face, a portal from both sides (source number 2 * face + 1 for its back), and the solid faces alone.
    RayScene all;
    RayScene solid;
    std::vector<std::vector<std::array<double, 3>>> facePoints(map.faces.size());
    std::vector<std::array<double, 3>> faceNormals(map.faces.size(), {0.0, 0.0, 0.0});
    // For a portal, the sector on the side its normal points to.
    std::map<uint32_t, int> portalFront;

    for (size_t faceIndex = 0; faceIndex < map.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = map.faces[faceIndex];
        std::vector<std::array<double, 3>> &points = facePoints[faceIndex];
        bool whole = face.vertexIndices.size() >= 3;

        for (const uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= vertices.size())
            {
                whole = false;
                break;
            }

            const Game::IndoorVertex &vertex = vertices[vertexIndex];
            points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
        }

        if (!whole)
        {
            points.clear();
            continue;
        }

        std::array<double, 3> &normal = faceNormals[faceIndex];

        for (size_t index = 0; index < points.size(); ++index)
        {
            const std::array<double, 3> &current = points[index];
            const std::array<double, 3> &next = points[(index + 1) % points.size()];
            normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
            normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
            normal[2] += (current[0] - next[0]) * (current[1] + next[1]);
        }

        const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

        if (length < 1.0e-6)
        {
            points.clear();
            continue;
        }

        normal = {normal[0] / length, normal[1] / length, normal[2] / length};
        const bool portal = face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal);
        all.addFace(points, normal, static_cast<int32_t>(faceIndex * 2), std::string());

        if (portal)
        {
            const std::array<double, 3> back = {-normal[0], -normal[1], -normal[2]};
            all.addFace(points, back, static_cast<int32_t>(faceIndex * 2 + 1), std::string());
            // Which of its two sectors lies in front: the game's own lookup a little off its middle, each way.
            std::array<double, 3> middle = {0.0, 0.0, 0.0};

            for (const std::array<double, 3> &point : points)
            {
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    middle[axis] += point[axis] / double(points.size());
                }
            }

            const auto lookup = [&](double side)
            {
                return Game::findIndoorSectorForPoint(map, vertices,
                    {float(middle[0] + normal[0] * 8.0 * side), float(middle[1] + normal[1] * 8.0 * side),
                        float(middle[2] + normal[2] * 8.0 * side)},
                    &cache, false);
            };
            const std::optional<int16_t> front = lookup(1.0);
            const std::optional<int16_t> behind = lookup(-1.0);
            const int room = face.roomNumber;
            const int roomBehind = face.roomBehindNumber;
            portalFront[uint32_t(faceIndex)] = (front && *front == roomBehind) || (behind && *behind == room)
                ? roomBehind : room;
        }
        else
        {
            solid.addFace(points, normal, static_cast<int32_t>(faceIndex), std::string());
        }
    }

    all.build();
    solid.build();
    const std::optional<Game::MapDeltaData> state =
        pState != nullptr ? std::optional<Game::MapDeltaData>(*pState) : std::nullopt;
    const std::optional<Game::EventRuntimeState> noEvents;
    const Game::IndoorMovementController movement(map, &state, &noEvents);
    const std::array<std::array<double, 3>, 5> directions = {{
        {1.0, 0.0, 0.0}, {-1.0, 0.0, 0.0}, {0.0, 1.0, 0.0}, {0.0, -1.0, 0.0}, {0.0, 0.0, 1.0}}};

    for (size_t faceIndex = 0; faceIndex < map.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = map.faces[faceIndex];
        const std::vector<std::array<double, 3>> &points = facePoints[faceIndex];
        const std::array<double, 3> &normal = faceNormals[faceIndex];
        const uint32_t attributes = pState != nullptr && faceIndex < pState->faceAttributes.size()
            ? pState->faceAttributes[faceIndex] : face.attributes;

        // A floor one can stand on: drawn or not, solid, facing up and not too steep to walk.
        if (points.empty() || face.isPortal || Game::hasFaceAttribute(attributes, Game::FaceAttribute::IsPortal)
            || Game::hasFaceAttribute(attributes, Game::FaceAttribute::Untouchable) || normal[2] < 0.7)
        {
            continue;
        }

        std::array<double, 3> low = points[0];
        std::array<double, 3> high = points[0];
        std::array<double, 3> middle = {0.0, 0.0, 0.0};

        for (const std::array<double, 3> &point : points)
        {
            for (size_t axis = 0; axis < 3; ++axis)
            {
                low[axis] = std::min(low[axis], point[axis]);
                high[axis] = std::max(high[axis], point[axis]);
                middle[axis] += point[axis] / double(points.size());
            }
        }

        std::vector<std::array<double, 2>> samples = {{middle[0], middle[1]}};

        for (double x = std::floor(low[0] / SampleSpacing) * SampleSpacing + SampleSpacing / 2.0; x < high[0];
             x += SampleSpacing)
        {
            for (double y = std::floor(low[1] / SampleSpacing) * SampleSpacing + SampleSpacing / 2.0; y < high[1];
                 y += SampleSpacing)
            {
                if (samples.size() < MaximumSamples && insidePlan(points, x, y))
                {
                    samples.push_back({x, y});
                }
            }
        }

        EyeSectorFinding finding;
        finding.face = static_cast<uint32_t>(faceIndex);
        finding.floorSector = face.roomNumber;
        const double offset = normal[0] * points[0][0] + normal[1] * points[0][1] + normal[2] * points[0][2];

        for (const std::array<double, 2> &sample : samples)
        {
            const double footZ = (offset - normal[0] * sample[0] - normal[1] * sample[1]) / normal[2];
            // No room to stand: a solid face overhead within the party's height.
            const RayHit overhead = solid.cast({sample[0], sample[1], footZ + 2.0}, {0.0, 0.0, 1.0}, RayReach);

            if (overhead.hit && overhead.distance < PartyEyeHeight - 2.0)
            {
                continue;
            }

            ++finding.sampled;
            const std::array<double, 3> eye = {sample[0], sample[1], footZ + PartyEyeHeight};
            std::map<int, size_t> votes;

            for (const std::array<double, 3> &direction : directions)
            {
                const RayHit hit = all.cast(eye, direction, RayReach);

                if (!hit.hit || hit.sourceId < 0)
                {
                    continue;
                }

                const uint32_t hitFace = static_cast<uint32_t>(hit.sourceId / 2);
                const Game::IndoorFace &met = map.faces[hitFace];
                const std::map<uint32_t, int>::const_iterator front = portalFront.find(hitFace);
                int sector = met.roomNumber;

                if (front != portalFront.end())
                {
                    const int other = front->second == met.roomNumber ? met.roomBehindNumber : met.roomNumber;
                    sector = hit.sourceId % 2 == 0 ? front->second : other;
                }

                ++votes[sector];
            }

            int eyeSector = -1;

            for (const std::pair<const int, size_t> &vote : votes)
            {
                if (vote.second >= EyeVotes)
                {
                    eyeSector = vote.first;
                }
            }

            if (eyeSector < 0)
            {
                continue;
            }

            // The game draws from the sector it finds for the eye after each step, and from the one its placement
            // finds when the party arrives or is put there (a teleport, a screenshot tour): the floor's.
            const std::optional<int16_t> lookedUp = Game::findIndoorSectorForPoint(
                map, vertices, {float(eye[0]), float(eye[1]), float(eye[2])}, &cache, false);
            const int drawnSector = lookedUp ? *lookedUp : face.roomNumber;
            const Game::IndoorMoveState placed = movement.initializeStateFromEyePosition(
                float(eye[0]), float(eye[1]), float(eye[2]), Game::IndoorBodyDimensions{});
            const int arrivalSector = placed.eyeSectorId >= 0 ? placed.eyeSectorId : drawnSector;

            // Judged by what a party walking there sees (the step's lookup). An eye in the floor's own sector's space
            // is not judged: the game's lookup names a neighbour there at 19 places of the shipped maps of the
            // rebuilds, not looked at in the game. (Put there by an arrival or a teleport, the party sees from the
            // arrival sector: the shipped maps' pits have an eye outside it at 76 places, so that alone is not
            // judged.)
            if (eyeSector == drawnSector || eyeSector == face.roomNumber)
            {
                continue;
            }

            if (finding.points == 0)
            {
                finding.foot = {sample[0], sample[1], footZ};
                finding.eyeSector = eyeSector;
                finding.drawnSector = drawnSector;
                finding.arrivalSector = arrivalSector;
            }

            ++finding.points;
        }

        if (finding.points > 0)
        {
            findings.push_back(finding);
        }
    }

    return findings;
}

std::string describeEyeSectorFinding(
    const Game::IndoorMapData &map,
    const Game::MapDeltaData *pState,
    const EyeSectorFinding &finding,
    const CoplanarNames &names)
{
    const Game::IndoorFace &face = map.faces[finding.face];
    const std::map<uint32_t, uint32_t> doors = doorOfFaces(pState);
    const std::map<uint32_t, uint32_t>::const_iterator door = doors.find(finding.face);
    std::string text = "standing on face " + std::to_string(finding.face) + " (" + face.textureName + ", "
        + sectorName(names.sectors, finding.floorSector);

    if (door != doors.end())
    {
        const std::map<int, std::string>::const_iterator name = names.doors.find(static_cast<int>(door->second));
        text += ", moved by " + (name != names.doors.end() ? name->second : "door " + std::to_string(door->second));
    }

    text += ") at [" + wholeText(finding.foot[0]) + ", " + wholeText(finding.foot[1]) + ", "
        + wholeText(finding.foot[2]) + "] (" + std::to_string(finding.points) + " of its "
        + std::to_string(finding.sampled) + " points), the party's eye is in "
        + sectorName(names.sectors, finding.eyeSector) + "'s space";

    if (finding.drawnSector != finding.eyeSector)
    {
        text += " and the game draws from " + sectorName(names.sectors, finding.drawnSector)
            + " after a step there (the sector it finds for the eye)";
    }

    if (finding.arrivalSector != finding.eyeSector)
    {
        text += std::string(finding.drawnSector != finding.eyeSector ? " and" : " and the game draws from")
            + " " + sectorName(names.sectors, finding.arrivalSector) + " when the party is put there (arrival, "
            "teleport)";
    }

    return text + ": the walls round the eye are not drawn, the view is black. (The game finds the eye's sector by "
        "the nearest floor under it, a portal counting as a floor of each sector that has a hole in its floor, the "
        "lower sector number winning a tie: a walkable top in the plane of a floor hole, or under one within a "
        "party's height, is seen from the room below.) Make the top and what rises to it part of the room above, "
        "as the shipped maps do (the hole's edge where the top begins), or keep it a party's height under the hole";
}
}
