#include "core/Coplanar.h"
#include "core/CoreMath.h"

#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <optional>
#include <set>
#include <tuple>
#include <utility>

// Faces in one plane over each other (the user's walk through Gharik's Forge, 2026-11-13: faces flickered at the
// doors by the lava and on the bridge mechanisms). Each drawn face's plane is found from its corners (Newell's
// method); faces are grouped by their normal and sorted by their distance from the origin, so only faces whose
// planes are within a unit of each other are compared. Two such faces facing the same way are clipped against each
// other (Sutherland-Hodgman, in the plane's two widest axes) and the overlap's area and width decide.

namespace OpenYAMM::Studio
{
namespace
{
using Point2d = std::array<double, 2>;

constexpr double PlaneDistance = 1.0;
constexpr double NormalAgreement = 0.9999996;
constexpr double LeastArea = 8.0;
constexpr double LeastWidth = 1.5;

struct DrawnFace
{
    uint32_t face = 0;
    std::array<double, 3> normal = {};
    double offset = 0.0;
    std::vector<std::array<double, 3>> points;
    std::array<double, 3> low = {};
    std::array<double, 3> high = {};
    bool moves = false;
};

double signedArea(const std::vector<Point2d> &polygon)
{
    double twice = 0.0;

    for (size_t index = 0; index < polygon.size(); ++index)
    {
        const Point2d &current = polygon[index];
        const Point2d &next = polygon[(index + 1) % polygon.size()];
        twice += current[0] * next[1] - next[0] * current[1];
    }

    return twice / 2.0;
}

bool convex(const std::vector<Point2d> &polygon)
{
    const size_t count = polygon.size();

    for (size_t index = 0; index < count; ++index)
    {
        const Point2d &a = polygon[index];
        const Point2d &b = polygon[(index + 1) % count];
        const Point2d &c = polygon[(index + 2) % count];

        if ((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) < -1.0e-6)
        {
            return false;
        }
    }

    return true;
}

// `subject` clipped to the inside of the convex counter-clockwise `clip`.
std::vector<Point2d> clipPolygon(const std::vector<Point2d> &subject, const std::vector<Point2d> &clip)
{
    std::vector<Point2d> output = subject;

    for (size_t edge = 0; edge < clip.size() && !output.empty(); ++edge)
    {
        const Point2d &from = clip[edge];
        const Point2d &to = clip[(edge + 1) % clip.size()];
        const auto side = [&from, &to](const Point2d &point)
        {
            return (to[0] - from[0]) * (point[1] - from[1]) - (to[1] - from[1]) * (point[0] - from[0]);
        };
        const std::vector<Point2d> input = output;
        output.clear();

        for (size_t index = 0; index < input.size(); ++index)
        {
            const Point2d &current = input[index];
            const Point2d &previous = input[(index + input.size() - 1) % input.size()];
            const double currentSide = side(current);
            const double previousSide = side(previous);

            if ((currentSide >= 0.0) != (previousSide >= 0.0))
            {
                const double share = previousSide / (previousSide - currentSide);
                output.push_back({previous[0] + (current[0] - previous[0]) * share,
                    previous[1] + (current[1] - previous[1]) * share});
            }

            if (currentSide >= 0.0)
            {
                output.push_back(current);
            }
        }
    }

    return output;
}

std::vector<DrawnFace> drawnFaces(
    const Game::IndoorMapData &map,
    const Game::MapDeltaData *pState,
    const std::vector<Game::IndoorVertex> &vertices,
    const std::set<uint32_t> &movingFaces)
{
    std::vector<DrawnFace> faces;

    for (size_t faceIndex = 0; faceIndex < map.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = map.faces[faceIndex];
        const uint32_t attributes = pState != nullptr && faceIndex < pState->faceAttributes.size()
            ? pState->faceAttributes[faceIndex] : face.attributes;

        if (face.isPortal || face.vertexIndices.size() < 3
            || Game::hasFaceAttribute(attributes, Game::FaceAttribute::IsPortal)
            || Game::hasFaceAttribute(attributes, Game::FaceAttribute::Invisible))
        {
            continue;
        }

        DrawnFace drawn;
        drawn.face = static_cast<uint32_t>(faceIndex);
        drawn.moves = movingFaces.contains(drawn.face);
        bool whole = true;

        for (const uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex >= vertices.size())
            {
                whole = false;
                break;
            }

            const Game::IndoorVertex &vertex = vertices[vertexIndex];
            drawn.points.push_back({static_cast<double>(vertex.x), static_cast<double>(vertex.y),
                static_cast<double>(vertex.z)});
        }

        if (!whole)
        {
            continue;
        }

        std::array<double, 3> normal = {};

        for (size_t index = 0; index < drawn.points.size(); ++index)
        {
            const std::array<double, 3> &current = drawn.points[index];
            const std::array<double, 3> &next = drawn.points[(index + 1) % drawn.points.size()];
            normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
            normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
            normal[2] += (current[0] - next[0]) * (current[1] + next[1]);
        }

        const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

        if (length < 1.0e-6)
        {
            continue;
        }

        drawn.low = drawn.points[0];
        drawn.high = drawn.points[0];
        double offset = 0.0;

        for (const std::array<double, 3> &point : drawn.points)
        {
            for (int axis = 0; axis < 3; ++axis)
            {
                drawn.low[axis] = std::min(drawn.low[axis], point[axis]);
                drawn.high[axis] = std::max(drawn.high[axis], point[axis]);
            }
        }

        for (int axis = 0; axis < 3; ++axis)
        {
            drawn.normal[axis] = normal[axis] / length;
        }

        for (const std::array<double, 3> &point : drawn.points)
        {
            offset += drawn.normal[0] * point[0] + drawn.normal[1] * point[1] + drawn.normal[2] * point[2];
        }

        drawn.offset = offset / static_cast<double>(drawn.points.size());
        faces.push_back(drawn);
    }

    return faces;
}

// The overlap of two faces in one plane: its area and middle, or nothing when it is a sliver.
// `slack`: how far apart the two bounds may lie on an axis.
std::optional<std::pair<double, std::array<double, 3>>> overlapOf(
    const DrawnFace &first,
    const DrawnFace &second,
    double slack = 0.5,
    double leastWidth = LeastWidth)
{
    for (int axis = 0; axis < 3; ++axis)
    {
        if (first.high[axis] < second.low[axis] - slack || second.high[axis] < first.low[axis] - slack)
        {
            return std::nullopt;
        }
    }

    // The plane's two widest axes.
    int dropped = 0;

    for (int axis = 1; axis < 3; ++axis)
    {
        if (std::abs(first.normal[axis]) > std::abs(first.normal[dropped]))
        {
            dropped = axis;
        }
    }

    const int u = dropped == 0 ? 1 : 0;
    const int v = dropped == 2 ? 1 : 2;
    const auto flat = [u, v](const DrawnFace &face)
    {
        std::vector<Point2d> polygon;

        for (const std::array<double, 3> &point : face.points)
        {
            polygon.push_back({point[u], point[v]});
        }

        if (signedArea(polygon) < 0.0)
        {
            std::reverse(polygon.begin(), polygon.end());
        }

        return polygon;
    };

    std::vector<Point2d> subject = flat(first);
    std::vector<Point2d> clip = flat(second);

    if (!convex(clip))
    {
        std::swap(subject, clip);
    }

    const std::vector<Point2d> overlap = clipPolygon(subject, clip);

    if (overlap.size() < 3)
    {
        return std::nullopt;
    }

    const double scale = 1.0 / std::abs(first.normal[dropped]);
    const double area = std::abs(signedArea(overlap)) * scale;
    double perimeter = 0.0;
    Point2d middle = {0.0, 0.0};

    for (size_t index = 0; index < overlap.size(); ++index)
    {
        const Point2d &current = overlap[index];
        const Point2d &next = overlap[(index + 1) % overlap.size()];
        perimeter += oy::hypot(next[0] - current[0], next[1] - current[1]);
        middle[0] += current[0] / static_cast<double>(overlap.size());
        middle[1] += current[1] / static_cast<double>(overlap.size());
    }

    if (area < LeastArea || perimeter <= 0.0 || 2.0 * area / perimeter < leastWidth)
    {
        return std::nullopt;
    }

    std::array<double, 3> at = {};
    at[u] = middle[0];
    at[v] = middle[1];
    at[dropped] = (first.offset - first.normal[u] * middle[0] - first.normal[v] * middle[1]) / first.normal[dropped];
    return std::pair<double, std::array<double, 3>>(area, at);
}

// `doors`: the door record of each moving face; given, a pose between the ends, where two faces of different moving
// parts are not compared.
void findInPose(
    const std::vector<DrawnFace> &faces,
    const std::string &pose,
    bool movingOnly,
    std::set<std::pair<uint32_t, uint32_t>> &seen,
    std::vector<CoplanarPair> &pairs,
    const std::map<uint32_t, uint32_t> *pDoors = nullptr,
    double planeDistance = PlaneDistance,
    double leastWidth = LeastWidth)
{
    // By the normal (to about a fifth of a degree), then by the plane's distance.
    std::map<std::array<long long, 3>, std::vector<size_t>> byNormal;

    for (size_t index = 0; index < faces.size(); ++index)
    {
        byNormal[{std::llround(faces[index].normal[0] * 300.0), std::llround(faces[index].normal[1] * 300.0),
            std::llround(faces[index].normal[2] * 300.0)}].push_back(index);
    }

    for (std::pair<const std::array<long long, 3>, std::vector<size_t>> &group : byNormal)
    {
        std::vector<size_t> &members = group.second;
        std::sort(members.begin(), members.end(), [&faces](size_t left, size_t right)
        {
            return faces[left].offset < faces[right].offset
                || (faces[left].offset == faces[right].offset && faces[left].face < faces[right].face);
        });

        for (size_t first = 0; first < members.size(); ++first)
        {
            const DrawnFace &a = faces[members[first]];

            for (size_t second = first + 1; second < members.size(); ++second)
            {
                const DrawnFace &b = faces[members[second]];

                if (b.offset - a.offset >= planeDistance)
                {
                    break;
                }

                if ((movingOnly && !a.moves && !b.moves)
                    || a.normal[0] * b.normal[0] + a.normal[1] * b.normal[1] + a.normal[2] * b.normal[2]
                        < NormalAgreement)
                {
                    continue;
                }

                const std::pair<uint32_t, uint32_t> key = {std::min(a.face, b.face), std::max(a.face, b.face)};

                if (seen.contains(key))
                {
                    continue;
                }

                if (pDoors != nullptr && a.moves && b.moves && pDoors->at(a.face) != pDoors->at(b.face))
                {
                    continue;
                }

                const std::optional<std::pair<double, std::array<double, 3>>> overlap = overlapOf(a, b, planeDistance > PlaneDistance ? planeDistance : 0.5, leastWidth);

                if (!overlap)
                {
                    continue;
                }

                seen.insert(key);
                CoplanarPair pair;
                pair.firstFace = key.first;
                pair.secondFace = key.second;
                pair.area = overlap->first;
                pair.at = overlap->second;
                pair.pose = pose;
                pair.normal = a.normal;
                pairs.push_back(pair);
            }
        }
    }
}

std::string whole(double value)
{
    return std::to_string(static_cast<long long>(std::llround(value)));
}

std::string named(const std::map<int, std::string> &names, int number, const std::string &word)
{
    const std::map<int, std::string>::const_iterator name = names.find(number);
    return name != names.end() ? name->second : word + " " + std::to_string(number);
}
}

double projectedOverlapArea(
    const std::vector<std::array<double, 3>> &first,
    const std::vector<std::array<double, 3>> &second,
    const std::array<double, 3> &normal)
{
    int dropped = 0;

    for (int axis = 1; axis < 3; ++axis)
    {
        if (std::abs(normal[axis]) > std::abs(normal[dropped]))
        {
            dropped = axis;
        }
    }

    const int u = dropped == 0 ? 1 : 0;
    const int v = dropped == 2 ? 1 : 2;
    const auto flat = [u, v](const std::vector<std::array<double, 3>> &points)
    {
        std::vector<Point2d> polygon;

        for (const std::array<double, 3> &point : points)
        {
            polygon.push_back({point[u], point[v]});
        }

        if (signedArea(polygon) < 0.0)
        {
            std::reverse(polygon.begin(), polygon.end());
        }

        return polygon;
    };

    std::vector<Point2d> subject = flat(first);
    std::vector<Point2d> clip = flat(second);

    if (subject.size() < 3 || clip.size() < 3 || std::abs(normal[dropped]) < 1.0e-6)
    {
        return 0.0;
    }

    if (!convex(clip))
    {
        std::swap(subject, clip);
    }

    const std::vector<Point2d> overlap = clipPolygon(subject, clip);
    return overlap.size() < 3 ? 0.0 : std::abs(signedArea(overlap)) / std::abs(normal[dropped]);
}

std::string describeCoplanarPair(
    const Game::IndoorMapData &map,
    const Game::MapDeltaData *pState,
    const CoplanarPair &pair,
    const CoplanarNames &names)
{
    const std::map<uint32_t, uint32_t> doors = doorOfFaces(pState);
    const auto faceText = [&map, &doors, &names](uint32_t faceIndex)
    {
        const Game::IndoorFace &face = map.faces[faceIndex];
        std::string text = "face " + std::to_string(faceIndex) + " (" + face.textureName + ", "
            + named(names.sectors, face.roomNumber, "sector");
        const std::map<uint32_t, uint32_t>::const_iterator door = doors.find(faceIndex);

        if (door != doors.end())
        {
            text += ", moved by " + named(names.doors, static_cast<int>(door->second), "door");
        }

        if (face.cogTriggered != 0)
        {
            text += ", clicked: " + named(names.events, face.cogTriggered, "event");
        }

        return text + ")";
    };

    return faceText(pair.firstFace) + " and " + faceText(pair.secondFace) + " lie in one plane facing the same way "
        "and overlap by " + whole(pair.area) + " square units at [" + whole(pair.at[0]) + ", " + whole(pair.at[1])
        + ", " + whole(pair.at[2]) + "]" + (pair.pose == "start" ? std::string(" as the map starts")
            : pair.pose == "moved" ? std::string(" with the moving parts at the other end of their way")
            : pair.pose == "quarter" ? std::string(" with the moving parts a quarter of their way along")
            : pair.pose == "half" ? std::string(" with the moving parts half their way along")
            : std::string(" with the moving parts three quarters of their way along")) + ": they flicker (z-fighting)"
        + (pair.asOriginal ? std::string("; the original has the same pair here") : std::string());
}

std::vector<CoplanarPlace> coplanarPlaces(const Game::IndoorMapData &map, const std::vector<CoplanarPair> &pairs)
{
    std::vector<CoplanarPlace> places;
    const auto lower = [](std::string text)
    {
        std::transform(text.begin(), text.end(), text.begin(), [](unsigned char letter)
        {
            return static_cast<char>(std::tolower(letter));
        });
        return text;
    };

    for (const CoplanarPair &pair : pairs)
    {
        CoplanarPlace place;
        place.firstTexture = lower(map.faces[pair.firstFace].textureName);
        place.secondTexture = lower(map.faces[pair.secondFace].textureName);

        if (place.secondTexture < place.firstTexture)
        {
            std::swap(place.firstTexture, place.secondTexture);
        }

        place.normal = pair.normal;
        place.at = pair.at;
        places.push_back(place);
    }

    return places;
}

size_t markPairsAsOriginal(
    const Game::IndoorMapData &map,
    std::vector<CoplanarPair> &pairs,
    const std::vector<CoplanarPlace> &originalPlaces)
{
    const std::vector<CoplanarPlace> places = coplanarPlaces(map, pairs);
    size_t marked = 0;

    for (size_t index = 0; index < pairs.size(); ++index)
    {
        const CoplanarPlace &place = places[index];

        for (const CoplanarPlace &original : originalPlaces)
        {
            const double agreement = place.normal[0] * original.normal[0] + place.normal[1] * original.normal[1]
                + place.normal[2] * original.normal[2];
            const std::array<double, 3> apart = {
                place.at[0] - original.at[0], place.at[1] - original.at[1], place.at[2] - original.at[2]};
            const double offPlane =
                std::abs(apart[0] * place.normal[0] + apart[1] * place.normal[1] + apart[2] * place.normal[2]);

            if (place.firstTexture == original.firstTexture && place.secondTexture == original.secondTexture
                && agreement > 0.9998 && offPlane <= 2.0
                && std::sqrt(apart[0] * apart[0] + apart[1] * apart[1] + apart[2] * apart[2]) <= 128.0)
            {
                pairs[index].asOriginal = true;
                ++marked;
                break;
            }
        }
    }

    return marked;
}

std::map<uint32_t, uint32_t> doorOfFaces(const Game::MapDeltaData *pState)
{
    std::map<uint32_t, uint32_t> doors;

    if (pState == nullptr)
    {
        return doors;
    }

    for (const Game::MapDeltaDoor &door : pState->doors)
    {
        for (const uint16_t face : door.faceIds)
        {
            doors.emplace(face, door.doorId);
        }
    }

    return doors;
}

std::vector<CoplanarPair> findCoplanarFaces(const Game::IndoorMapData &map, const Game::MapDeltaData *pState)
{
    std::vector<CoplanarPair> pairs;
    std::set<std::pair<uint32_t, uint32_t>> seen;
    std::set<uint32_t> movingFaces;

    for (const std::pair<const uint32_t, uint32_t> &face : doorOfFaces(pState))
    {
        movingFaces.insert(face.first);
    }

    const std::vector<Game::IndoorVertex> start = Game::buildIndoorMechanismAdjustedVertices(map, pState, nullptr);
    findInPose(drawnFaces(map, pState, start, movingFaces), "start", false, seen, pairs);

    if (pState == nullptr || pState->doors.empty())
    {
        return pairs;
    }

    // Every moving part at the other end of its way: open where it starts shut, shut where it starts open.
    Game::EventRuntimeState moved;

    for (const Game::MapDeltaDoor &door : pState->doors)
    {
        const bool startsOpen = door.state == static_cast<uint16_t>(Game::EvtMechanismState::Open)
            || door.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening);
        Game::RuntimeMechanismState pose;
        pose.state = static_cast<uint16_t>(
            startsOpen ? Game::EvtMechanismState::Closed : Game::EvtMechanismState::Open);
        pose.currentDistance = startsOpen ? static_cast<float>(door.moveLength) : 0.0f;
        moved.mechanisms[door.doorId] = pose;
    }

    const std::vector<Game::IndoorVertex> movedVertices =
        Game::buildIndoorMechanismAdjustedVertices(map, pState, &moved);
    findInPose(drawnFaces(map, pState, movedVertices, movingFaces), "moved", true, seen, pairs);

    // Between the ends: every moving part a quarter, half and three quarters of its way from where it starts.
    const std::map<uint32_t, uint32_t> doors = doorOfFaces(pState);

    for (const std::pair<double, const char *> &along :
         std::vector<std::pair<double, const char *>>{{0.25, "quarter"}, {0.5, "half"}, {0.75, "three_quarters"}})
    {
        Game::EventRuntimeState between;

        for (const Game::MapDeltaDoor &door : pState->doors)
        {
            const bool startsOpen = door.state == static_cast<uint16_t>(Game::EvtMechanismState::Open)
                || door.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening);
            // The distance runs from 0 (open) to the move length (shut).
            const double length = static_cast<double>(door.moveLength);
            Game::RuntimeMechanismState pose;
            pose.state = static_cast<uint16_t>(Game::EvtMechanismState::Opening);
            pose.currentDistance = static_cast<float>(startsOpen ? length * along.first : length * (1.0 - along.first));
            between.mechanisms[door.doorId] = pose;
        }

        const std::vector<Game::IndoorVertex> vertices =
            Game::buildIndoorMechanismAdjustedVertices(map, pState, &between);
        findInPose(drawnFaces(map, pState, vertices, movingFaces), along.second, true, seen, pairs, &doors);
    }

    std::sort(pairs.begin(), pairs.end(), [](const CoplanarPair &left, const CoplanarPair &right)
    {
        return std::tie(left.firstFace, left.secondFace) < std::tie(right.firstFace, right.secondFace);
    });
    return pairs;
}
}

namespace OpenYAMM::Studio
{
namespace
{
std::string lowerText(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char letter)
    {
        return static_cast<char>(std::tolower(letter));
    });
    return text;
}

std::string partOfFace(const OutdoorFaceParts &parts, size_t model, size_t face)
{
    return model < parts.size() && face < parts[model].size() ? parts[model][face] : std::string();
}
}

namespace
{
// The drawn faces of outdoor models (not invisible, at least three corners, some area), each with its (model, face).
std::vector<DrawnFace> drawnOutdoorFaces(
    const std::vector<Game::OutdoorBModel> &models,
    std::vector<std::pair<size_t, size_t>> &origin)
{
    std::vector<DrawnFace> faces;

    for (size_t modelIndex = 0; modelIndex < models.size(); ++modelIndex)
    {
        const Game::OutdoorBModel &model = models[modelIndex];

        for (size_t faceIndex = 0; faceIndex < model.faces.size(); ++faceIndex)
        {
            const Game::OutdoorBModelFace &face = model.faces[faceIndex];

            if (face.vertexIndices.size() < 3
                || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible))
            {
                continue;
            }

            DrawnFace drawn;
            drawn.face = static_cast<uint32_t>(origin.size());
            bool whole = true;

            for (const uint16_t vertexIndex : face.vertexIndices)
            {
                if (vertexIndex >= model.vertices.size())
                {
                    whole = false;
                    break;
                }

                const Game::OutdoorBModelVertex &vertex = model.vertices[vertexIndex];
                drawn.points.push_back({static_cast<double>(vertex.x), static_cast<double>(vertex.y),
                    static_cast<double>(vertex.z)});
            }

            std::array<double, 3> normal = {};

            for (size_t index = 0; whole && index < drawn.points.size(); ++index)
            {
                const std::array<double, 3> &current = drawn.points[index];
                const std::array<double, 3> &next = drawn.points[(index + 1) % drawn.points.size()];
                normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
                normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
                normal[2] += (current[0] - next[0]) * (current[1] + next[1]);
            }

            const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

            if (!whole || length < 1.0e-6)
            {
                continue;
            }

            drawn.low = drawn.points[0];
            drawn.high = drawn.points[0];
            double offset = 0.0;

            for (int axis = 0; axis < 3; ++axis)
            {
                drawn.normal[axis] = normal[axis] / length;
            }

            for (const std::array<double, 3> &point : drawn.points)
            {
                for (int axis = 0; axis < 3; ++axis)
                {
                    drawn.low[axis] = std::min(drawn.low[axis], point[axis]);
                    drawn.high[axis] = std::max(drawn.high[axis], point[axis]);
                }

                offset += drawn.normal[0] * point[0] + drawn.normal[1] * point[1] + drawn.normal[2] * point[2];
            }

            drawn.offset = offset / static_cast<double>(drawn.points.size());
            faces.push_back(drawn);
            origin.push_back({modelIndex, faceIndex});
        }
    }

    return faces;
}

// Whether a point stands in the open or shut inside a solid, as tools/xeen/check_faces.py tells it: faces face out of
// the solids they bound, so a ray from open space meets a face's front first (or nothing: the sky, or the land),
// one from inside a solid a face's back. Six rays nearly along the axes vote; four open is open.
class OpenSpace
{
public:
    explicit OpenSpace(const std::vector<DrawnFace> &faces)
        : m_faces(faces)
    {
        for (size_t index = 0; index < faces.size(); ++index)
        {
            const DrawnFace &face = faces[index];

            for (int x = cellOf(face.low[0]); x <= cellOf(face.high[0]); ++x)
            {
                for (int y = cellOf(face.low[1]); y <= cellOf(face.high[1]); ++y)
                {
                    m_cells[{x, y}].push_back(index);
                }
            }
        }
    }

    bool openAt(const std::array<double, 3> &point, size_t skipFirst, size_t skipSecond) const
    {
        static const std::array<std::array<double, 3>, 6> directions = {{{1.0, 0.013, 0.007},
            {-1.0, -0.011, 0.009}, {0.012, 1.0, 0.006}, {-0.008, -1.0, 0.011}, {0.009, 0.007, 1.0},
            {0.006, -0.012, -1.0}}};
        int open = 0;

        for (const std::array<double, 3> &direction : directions)
        {
            open += rayOpen(point, direction, skipFirst, skipSecond) ? 1 : 0;
        }

        return open >= 4;
    }

private:
    static constexpr double Cell = 512.0;
    static constexpr double Reach = 8192.0;

    static int cellOf(double value)
    {
        return static_cast<int>(std::floor(value / Cell));
    }

    bool rayOpen(const std::array<double, 3> &origin, std::array<double, 3> direction, size_t skipFirst,
        size_t skipSecond) const
    {
        const double length = std::sqrt(direction[0] * direction[0] + direction[1] * direction[1]
            + direction[2] * direction[2]);
        direction = {direction[0] / length, direction[1] / length, direction[2] / length};
        std::set<std::pair<int, int>> cells;

        for (double step = 0.0; step <= Reach; step += Cell * 0.5)
        {
            cells.insert({cellOf(origin[0] + direction[0] * step), cellOf(origin[1] + direction[1] * step)});

            if (std::fabs(direction[2]) > 0.99)
            {
                break;
            }
        }

        double nearest = Reach;
        bool front = true;
        std::set<size_t> tried;

        for (const std::pair<int, int> &cell : cells)
        {
            const std::map<std::pair<int, int>, std::vector<size_t>>::const_iterator found = m_cells.find(cell);

            if (found == m_cells.end())
            {
                continue;
            }

            for (const size_t index : found->second)
            {
                if (index == skipFirst || index == skipSecond || !tried.insert(index).second)
                {
                    continue;
                }

                const DrawnFace &face = m_faces[index];
                const double facing = face.normal[0] * direction[0] + face.normal[1] * direction[1]
                    + face.normal[2] * direction[2];

                if (std::fabs(facing) < 1.0e-9)
                {
                    continue;
                }

                const double distance = (face.offset - face.normal[0] * origin[0] - face.normal[1] * origin[1]
                    - face.normal[2] * origin[2]) / facing;

                if (distance <= 0.5 || distance >= nearest)
                {
                    continue;
                }

                const std::array<double, 3> hit = {origin[0] + direction[0] * distance,
                    origin[1] + direction[1] * distance, origin[2] + direction[2] * distance};

                if (inside(face, hit))
                {
                    nearest = distance;
                    front = facing < 0.0;
                }
            }
        }

        return front;
    }

    // A point of a face's plane inside its polygon (even-odd, in the plane's two widest axes).
    static bool inside(const DrawnFace &face, const std::array<double, 3> &point)
    {
        int dropped = 0;

        for (int axis = 1; axis < 3; ++axis)
        {
            if (std::fabs(face.normal[axis]) > std::fabs(face.normal[dropped]))
            {
                dropped = axis;
            }
        }

        const int u = dropped == 0 ? 1 : 0;
        const int v = dropped == 2 ? 1 : 2;
        bool in = false;

        for (size_t index = 0, previous = face.points.size() - 1; index < face.points.size(); previous = index++)
        {
            const std::array<double, 3> &a = face.points[index];
            const std::array<double, 3> &b = face.points[previous];

            if ((a[v] > point[v]) != (b[v] > point[v])
                && point[u] < (b[u] - a[u]) * (point[v] - a[v]) / (b[v] - a[v]) + a[u])
            {
                in = !in;
            }
        }

        return in;
    }

    const std::vector<DrawnFace> &m_faces;
    std::map<std::pair<int, int>, std::vector<size_t>> m_cells;
};
}

std::vector<OutdoorCoplanarPair> findOutdoorCoplanarFaces(const std::vector<Game::OutdoorBModel> &models)
{
    std::vector<std::pair<size_t, size_t>> origin;
    const std::vector<DrawnFace> faces = drawnOutdoorFaces(models, origin);
    std::vector<CoplanarPair> found;
    std::set<std::pair<uint32_t, uint32_t>> seen;
    // Outdoors a face 1 unit in front of another still flickers at the distances the party sees models from (a
    // sign's picture on its board): planes within a unit, that unit included. And the thin slivers where the tops of
    // two wall runs cross count (on average 0.75 wide), as the count the outdoor rounds made by script
    // (output/studio_cal/mm8_out06/scripts/coplanar_odm.py) has them.
    findInPose(faces, "start", false, seen, found, nullptr, PlaneDistance + 1.0e-3, LeastWidth / 2.0);
    std::vector<OutdoorCoplanarPair> pairs;

    for (const CoplanarPair &pair : found)
    {
        OutdoorCoplanarPair outdoor;
        outdoor.firstModel = origin[pair.firstFace].first;
        outdoor.firstFace = origin[pair.firstFace].second;
        outdoor.secondModel = origin[pair.secondFace].first;
        outdoor.secondFace = origin[pair.secondFace].second;
        outdoor.area = pair.area;
        outdoor.at = pair.at;
        outdoor.normal = pair.normal;
        pairs.push_back(outdoor);
    }

    std::sort(pairs.begin(), pairs.end(), [](const OutdoorCoplanarPair &left, const OutdoorCoplanarPair &right)
    {
        return std::tie(left.firstModel, left.firstFace, left.secondModel, left.secondFace)
            < std::tie(right.firstModel, right.firstFace, right.secondModel, right.secondFace);
    });
    return pairs;
}

std::vector<OutdoorCoplanarPair> findOutdoorBackToBackFaces(const std::vector<Game::OutdoorBModel> &models)
{
    std::vector<std::pair<size_t, size_t>> origin;
    const std::vector<DrawnFace> faces = drawnOutdoorFaces(models, origin);
    // By the normal (to about a fifth of a degree), as findInPose: a group meets the group of the opposite normal.
    std::map<std::array<long long, 3>, std::vector<size_t>> byNormal;

    for (size_t index = 0; index < faces.size(); ++index)
    {
        byNormal[{std::llround(faces[index].normal[0] * 300.0), std::llround(faces[index].normal[1] * 300.0),
            std::llround(faces[index].normal[2] * 300.0)}].push_back(index);
    }

    std::vector<OutdoorCoplanarPair> pairs;
    const OpenSpace space(faces);

    for (const std::pair<const std::array<long long, 3>, std::vector<size_t>> &group : byNormal)
    {
        const std::array<long long, 3> opposite = {-group.first[0], -group.first[1], -group.first[2]};
        const std::map<std::array<long long, 3>, std::vector<size_t>>::const_iterator other =
            byNormal.find(opposite);

        // Each two groups once.
        if (other == byNormal.end() || !(group.first < opposite))
        {
            continue;
        }

        // The other group's faces by their plane's distance seen along this group's normal (its offset negated).
        std::vector<std::pair<double, size_t>> along;

        for (const size_t index : other->second)
        {
            along.push_back({-faces[index].offset, index});
        }

        std::sort(along.begin(), along.end());

        for (const size_t first : group.second)
        {
            const DrawnFace &a = faces[first];
            const double reach = PlaneDistance + 1.0e-3;
            std::vector<std::pair<double, size_t>>::const_iterator candidate = std::lower_bound(along.begin(),
                along.end(), std::pair<double, size_t>(a.offset - reach, 0));

            for (; candidate != along.end() && candidate->first < a.offset + reach; ++candidate)
            {
                const DrawnFace &b = faces[candidate->second];

                if (a.normal[0] * b.normal[0] + a.normal[1] * b.normal[1] + a.normal[2] * b.normal[2]
                    > -NormalAgreement)
                {
                    continue;
                }

                const std::optional<std::pair<double, std::array<double, 3>>> overlap = overlapOf(a, b, reach);

                if (!overlap)
                {
                    continue;
                }

                // Two solids touching hide the faces between them: only a pair with open space on a side shows.
                const std::array<double, 3> &at = overlap->second;
                const auto beside = [&](double way)
                {
                    return std::array<double, 3>{at[0] + a.normal[0] * way, at[1] + a.normal[1] * way,
                        at[2] + a.normal[2] * way};
                };

                if (!space.openAt(beside(2.0), first, candidate->second)
                    && !space.openAt(beside(-2.0), first, candidate->second))
                {
                    continue;
                }

                OutdoorCoplanarPair pair;
                const std::pair<size_t, size_t> &from = origin[std::min(a.face, b.face)];
                const std::pair<size_t, size_t> &to = origin[std::max(a.face, b.face)];
                pair.firstModel = from.first;
                pair.firstFace = from.second;
                pair.secondModel = to.first;
                pair.secondFace = to.second;
                pair.area = overlap->first;
                pair.at = overlap->second;
                pair.normal = faces[std::min(a.face, b.face)].normal;
                pairs.push_back(pair);
            }
        }
    }

    std::sort(pairs.begin(), pairs.end(), [](const OutdoorCoplanarPair &left, const OutdoorCoplanarPair &right)
    {
        return std::tie(left.firstModel, left.firstFace, left.secondModel, left.secondFace)
            < std::tie(right.firstModel, right.firstFace, right.secondModel, right.secondFace);
    });
    return pairs;
}

std::vector<CoplanarPlace> outdoorCoplanarPlaces(
    const std::vector<Game::OutdoorBModel> &models,
    const std::vector<OutdoorCoplanarPair> &pairs)
{
    std::vector<CoplanarPlace> places;

    for (const OutdoorCoplanarPair &pair : pairs)
    {
        CoplanarPlace place;
        place.firstTexture = lowerText(models[pair.firstModel].faces[pair.firstFace].textureName);
        place.secondTexture = lowerText(models[pair.secondModel].faces[pair.secondFace].textureName);

        if (place.secondTexture < place.firstTexture)
        {
            std::swap(place.firstTexture, place.secondTexture);
        }

        place.normal = pair.normal;
        place.at = pair.at;
        places.push_back(place);
    }

    return places;
}

size_t markOutdoorPairsAsOriginal(
    const std::vector<Game::OutdoorBModel> &models,
    std::vector<OutdoorCoplanarPair> &pairs,
    const std::vector<CoplanarPlace> &originalPlaces)
{
    const std::vector<CoplanarPlace> places = outdoorCoplanarPlaces(models, pairs);
    size_t marked = 0;

    for (size_t index = 0; index < pairs.size(); ++index)
    {
        const CoplanarPlace &place = places[index];

        for (const CoplanarPlace &original : originalPlaces)
        {
            const double agreement = place.normal[0] * original.normal[0] + place.normal[1] * original.normal[1]
                + place.normal[2] * original.normal[2];
            const std::array<double, 3> apart = {
                place.at[0] - original.at[0], place.at[1] - original.at[1], place.at[2] - original.at[2]};
            const double offPlane =
                std::abs(apart[0] * place.normal[0] + apart[1] * place.normal[1] + apart[2] * place.normal[2]);

            if (place.firstTexture == original.firstTexture && place.secondTexture == original.secondTexture
                && agreement > 0.9998 && offPlane <= 2.0
                && std::sqrt(apart[0] * apart[0] + apart[1] * apart[1] + apart[2] * apart[2]) <= 128.0)
            {
                pairs[index].asOriginal = true;
                ++marked;
                break;
            }
        }
    }

    return marked;
}

std::string describeOutdoorCoplanarPair(
    const std::vector<Game::OutdoorBModel> &models,
    const OutdoorCoplanarPair &pair,
    const OutdoorFaceParts &parts,
    bool backToBack)
{
    const auto faceText = [&models, &parts](size_t model, size_t face)
    {
        const std::string part = partOfFace(parts, model, face);
        return models[model].name + (part.empty() ? std::string() : " " + part) + " face " + std::to_string(face)
            + " (" + models[model].faces[face].textureName + ")";
    };

    return faceText(pair.firstModel, pair.firstFace) + " and " + faceText(pair.secondModel, pair.secondFace)
        + (backToBack ? " lie in one plane back to back" : " lie in one plane facing the same way")
        + " and overlap by " + whole(pair.area) + " square units at ["
        + whole(pair.at[0]) + ", " + whole(pair.at[1]) + ", " + whole(pair.at[2]) + "]: they flicker (z-fighting)"
        + (pair.asOriginal ? std::string("; the original has the same pair here") : std::string());
}

std::vector<std::string> describeOutdoorCoplanarGroups(
    const std::vector<Game::OutdoorBModel> &models,
    const std::vector<OutdoorCoplanarPair> &pairs,
    const OutdoorFaceParts &parts,
    bool backToBack)
{
    // A group: the two (model, part) sides, in the order met.
    using Side = std::pair<size_t, std::string>;
    std::vector<std::pair<Side, Side>> order;
    std::map<std::pair<Side, Side>, std::vector<const OutdoorCoplanarPair *>> groups;

    for (const OutdoorCoplanarPair &pair : pairs)
    {
        Side first = {pair.firstModel, partOfFace(parts, pair.firstModel, pair.firstFace)};
        Side second = {pair.secondModel, partOfFace(parts, pair.secondModel, pair.secondFace)};

        if (second < first)
        {
            std::swap(first, second);
        }

        const std::pair<Side, Side> key = {first, second};

        if (!groups.contains(key))
        {
            order.push_back(key);
        }

        groups[key].push_back(&pair);
    }

    // The drawn faces of a side.
    const auto drawnOf = [&models, &parts](const Side &side)
    {
        std::set<size_t> faces;
        const Game::OutdoorBModel &model = models[side.first];

        for (size_t face = 0; face < model.faces.size(); ++face)
        {
            if (partOfFace(parts, side.first, face) == side.second
                && !Game::hasFaceAttribute(model.faces[face].attributes, Game::FaceAttribute::Invisible))
            {
                faces.insert(face);
            }
        }

        return faces;
    };
    std::vector<std::string> sentences;

    for (const std::pair<Side, Side> &key : order)
    {
        const std::vector<const OutdoorCoplanarPair *> &members = groups[key];
        const auto sideText = [&models](const Side &side)
        {
            return models[side.first].name + (side.second.empty() ? std::string() : " " + side.second);
        };
        double area = 0.0;
        size_t original = 0;
        std::set<size_t> firstMet;
        std::set<size_t> secondMet;

        for (const OutdoorCoplanarPair *pPair : members)
        {
            area += pPair->area;
            original += pPair->asOriginal ? 1 : 0;
            const bool straight = Side{pPair->firstModel, partOfFace(parts, pPair->firstModel, pPair->firstFace)}
                == key.first;
            firstMet.insert(straight ? pPair->firstFace : pPair->secondFace);
            secondMet.insert(straight ? pPair->secondFace : pPair->firstFace);
        }

        const bool samePart = key.first == key.second;
        std::string what;

        if (backToBack)
        {
            what = "the game draws outdoor faces from both sides, so one face is enough: leave one out or hide it "
                   "(the party still meets a hidden face), or move it off the other's plane";
        }
        else if (!samePart && !key.first.second.empty() && !key.second.second.empty()
            && firstMet == drawnOf(key.first)
            && secondMet == drawnOf(key.second))
        {
            what = "the two parts are identical (every face of each lies on one of the other): leave one out";
        }
        else if (!samePart && key.first.first == key.second.first)
        {
            what = "the two parts run through each other along a shared plane: let one end where the other's wall "
                   "stands, or make them one part";
        }
        else if (samePart)
        {
            what = "faces of one part lie on each other";
        }
        else
        {
            what = "the two lie on each other: move one off the other's plane or cut it where the other lies";
        }

        const OutdoorCoplanarPair &first = *members.front();
        sentences.push_back((samePart ? sideText(key.first) : sideText(key.first) + " and " + sideText(key.second))
            + ": " + std::to_string(members.size()) + (members.size() == 1 ? " pair" : " pairs")
            + (backToBack ? " of faces in one plane back to back (" : " of faces in one plane facing the same way (")
            + whole(area) + " square units; the first "
            + models[first.firstModel].faces[first.firstFace].textureName + " on "
            + models[first.secondModel].faces[first.secondFace].textureName + " at [" + whole(first.at[0]) + ", "
            + whole(first.at[1]) + ", " + whole(first.at[2]) + "]" + (original != 0 ? ", " + std::to_string(original)
                + " as the original" : std::string()) + "): " + what + "; they flicker (z-fighting)");
    }

    return sentences;
}
}
