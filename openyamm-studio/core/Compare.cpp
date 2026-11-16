#include "core/Compare.h"

#include "core/CoreMath.h"
#include "core/EventFlow.h"
#include "core/Reachability.h"

#include "game/FaceEnums.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorPathfindingBuilder.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <map>
#include <optional>
#include <set>
#include <tuple>
#include <unordered_map>

#include <yaml-cpp/yaml.h>

namespace OpenYAMM::Studio
{
namespace
{
constexpr double Pi = 3.14159265358979323846;
constexpr double RayCap = 4096.0;
constexpr double EyeHeight = 160.0;
constexpr double FloorSearch = 512.0;
constexpr double WalkStep = 32.0;
constexpr size_t WorstPointCount = 40;
constexpr size_t ShotCount = 12;
constexpr double ShotSpacing = 1024.0;
constexpr size_t ListedFloorPoints = 200;
// How far a stand point keeps from a floor's edge and its eye from every face, and how thick a moving block may be
// for a point between two of its sides to count as inside it.
constexpr double EdgeClearance = 16.0;
constexpr double BlockThickness = 600.0;

std::string lowerCase(const std::string &text)
{
    std::string lowered = text;

    for (char &character : lowered)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return lowered;
}

std::string wholeNumber(double value)
{
    return std::to_string(static_cast<long long>(std::llround(value)));
}

// Even-odd: a point on a shared edge belongs to one of the two outlines when both are flattened the same way.
bool insideOutline(const std::vector<std::array<double, 2>> &outline, double u, double v)
{
    bool inside = false;

    for (size_t index = 0, previous = outline.size() - 1; index < outline.size(); previous = index++)
    {
        const std::array<double, 2> &first = outline[index];
        const std::array<double, 2> &second = outline[previous];

        if ((first[1] > v) != (second[1] > v)
            && u < (second[0] - first[0]) * (v - first[1]) / (second[1] - first[1]) + first[0])
        {
            inside = !inside;
        }
    }

    return inside;
}

// Whether a point lies within `tolerance` of the outline itself.
bool nearOutlineEdge(const std::vector<std::array<double, 2>> &outline, double u, double v, double tolerance)
{
    for (size_t index = 0, previous = outline.size() - 1; index < outline.size(); previous = index++)
    {
        const std::array<double, 2> &first = outline[previous];
        const std::array<double, 2> &second = outline[index];
        const double alongU = second[0] - first[0];
        const double alongV = second[1] - first[1];
        const double lengthSquared = alongU * alongU + alongV * alongV;
        const double along = lengthSquared < 1.0e-12 ? 0.0
            : std::clamp(((u - first[0]) * alongU + (v - first[1]) * alongV) / lengthSquared, 0.0, 1.0);
        const double offU = u - (first[0] + along * alongU);
        const double offV = v - (first[1] + along * alongV);

        if (offU * offU + offV * offV <= tolerance * tolerance)
        {
            return true;
        }
    }

    return false;
}
}

std::optional<std::array<double, 2>> offsetNeeded(
    const std::array<double, 2> &original, const std::array<double, 2> &rebuilt, const std::array<int, 2> &size)
{
    std::array<double, 2> needed = {};
    bool apart = false;

    for (size_t axis = 0; axis < 2; ++axis)
    {
        const double period = static_cast<double>(size[axis]);

        if (period <= 0.0)
        {
            return std::nullopt;
        }

        double difference = std::fmod(original[axis] - rebuilt[axis], period);
        difference = difference > period / 2.0 ? difference - period
            : difference <= -period / 2.0 ? difference + period : difference;
        needed[axis] = difference;
        apart = apart || std::fabs(difference) > OffsetTolerance;
    }

    return apart ? std::optional<std::array<double, 2>>(needed) : std::nullopt;
}

const char *surfaceKindName(SurfaceKind kind)
{
    switch (kind)
    {
    case SurfaceKind::Floor: return "floor";
    case SurfaceKind::Wall: return "wall";
    case SurfaceKind::Ceiling: return "ceiling";
    default: return "nothing";
    }
}

bool RayScene::addFace(
    const std::vector<std::array<double, 3>> &points,
    const std::array<double, 3> &normal,
    int32_t sourceId,
    const std::string &texture,
    const std::vector<std::array<double, 2>> *pTexels)
{
    if (points.size() < 3)
    {
        return false;
    }

    // Newell's sum: the plane of an outline that need be neither convex nor exactly flat.
    std::array<double, 3> winding = {0.0, 0.0, 0.0};
    std::array<double, 3> middle = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const std::array<double, 3> &current = points[index];
        const std::array<double, 3> &next = points[(index + 1) % points.size()];
        winding[0] += (current[1] - next[1]) * (current[2] + next[2]);
        winding[1] += (current[2] - next[2]) * (current[0] + next[0]);
        winding[2] += (current[0] - next[0]) * (current[1] + next[1]);

        for (size_t axis = 0; axis < 3; ++axis)
        {
            middle[axis] += current[axis] / static_cast<double>(points.size());
        }
    }

    const double length = std::sqrt(winding[0] * winding[0] + winding[1] * winding[1] + winding[2] * winding[2]);

    if (length < 1.0e-6)
    {
        return false;
    }

    Face face;
    const double facing = winding[0] * normal[0] + winding[1] * normal[1] + winding[2] * normal[2];
    const double sign = facing < 0.0 ? -1.0 : 1.0;

    for (size_t axis = 0; axis < 3; ++axis)
    {
        face.normal[axis] = sign * winding[axis] / length;
    }

    face.offset = face.normal[0] * middle[0] + face.normal[1] * middle[1] + face.normal[2] * middle[2];
    face.dropAxis = 0;

    for (int axis = 1; axis < 3; ++axis)
    {
        if (std::fabs(face.normal[static_cast<size_t>(axis)])
            > std::fabs(face.normal[static_cast<size_t>(face.dropAxis)]))
        {
            face.dropAxis = axis;
        }
    }

    const size_t first = face.dropAxis == 0 ? 1 : 0;
    const size_t second = face.dropAxis == 2 ? 1 : 2;
    face.low = points[0];
    face.high = points[0];

    for (const std::array<double, 3> &point : points)
    {
        face.flat.push_back({point[first], point[second]});

        for (size_t axis = 0; axis < 3; ++axis)
        {
            face.low[axis] = std::min(face.low[axis], point[axis]);
            face.high[axis] = std::max(face.high[axis], point[axis]);
        }
    }

    // Walls have no height over a point of the plan.
    if (std::fabs(face.normal[2]) > 0.1)
    {
        for (const std::array<double, 3> &point : points)
        {
            face.plan.push_back({point[0], point[1]});
        }
    }

    face.kind = face.normal[2] > 0.5 ? SurfaceKind::Floor : face.normal[2] < -0.5 ? SurfaceKind::Ceiling
        : SurfaceKind::Wall;
    face.sourceId = sourceId;
    face.texture = lowerCase(texture);

    // The texture's layout over the plane, from the three corners that span the most area: the texel changes along
    // the plane by a gradient g with g . (corner - first corner) = its texel less the first's.
    if (pTexels != nullptr && pTexels->size() == points.size())
    {
        const auto subtract = [](const std::array<double, 3> &left, const std::array<double, 3> &right)
        {
            return std::array<double, 3>{left[0] - right[0], left[1] - right[1], left[2] - right[2]};
        };
        const auto dotOf = [](const std::array<double, 3> &left, const std::array<double, 3> &right)
        {
            return left[0] * right[0] + left[1] * right[1] + left[2] * right[2];
        };
        size_t bestFirst = 0;
        size_t bestSecond = 1;
        size_t bestThird = 2;
        double bestArea = -1.0;

        for (size_t second = 1; second + 1 < points.size(); ++second)
        {
            for (size_t third = second + 1; third < points.size(); ++third)
            {
                const std::array<double, 3> one = subtract(points[second], points[0]);
                const std::array<double, 3> two = subtract(points[third], points[0]);
                const std::array<double, 3> across = {one[1] * two[2] - one[2] * two[1],
                    one[2] * two[0] - one[0] * two[2], one[0] * two[1] - one[1] * two[0]};
                const double area = dotOf(across, across);

                if (area > bestArea)
                {
                    bestArea = area;
                    bestSecond = second;
                    bestThird = third;
                }
            }
        }

        const std::array<double, 3> one = subtract(points[bestSecond], points[bestFirst]);
        const std::array<double, 3> two = subtract(points[bestThird], points[bestFirst]);
        const double oneOne = dotOf(one, one);
        const double oneTwo = dotOf(one, two);
        const double twoTwo = dotOf(two, two);
        const double determinant = oneOne * twoTwo - oneTwo * oneTwo;

        if (determinant > 1.0e-6)
        {
            const std::array<double, 2> &firstTexel = (*pTexels)[bestFirst];

            for (size_t component = 0; component < 2; ++component)
            {
                const double alongOne = (*pTexels)[bestSecond][component] - firstTexel[component];
                const double alongTwo = (*pTexels)[bestThird][component] - firstTexel[component];
                const double a = (alongOne * twoTwo - alongTwo * oneTwo) / determinant;
                const double b = (alongTwo * oneOne - alongOne * oneTwo) / determinant;
                std::array<double, 3> &gradient = component == 0 ? face.gradientU : face.gradientV;

                for (size_t axis = 0; axis < 3; ++axis)
                {
                    gradient[axis] = a * one[axis] + b * two[axis];
                }
            }

            face.hasTexel = true;
            face.texelOrigin = points[bestFirst];
            face.originTexel = firstTexel;
        }
    }

    m_faces.push_back(std::move(face));
    return true;
}

void RayScene::build(double cellSize)
{
    m_cells.clear();
    m_columns = 0;
    m_rows = 0;
    m_cellSize = std::max(1.0, cellSize);

    if (m_faces.empty())
    {
        return;
    }

    double highX = m_faces[0].high[0];
    double highY = m_faces[0].high[1];
    m_lowX = m_faces[0].low[0];
    m_lowY = m_faces[0].low[1];

    for (const Face &face : m_faces)
    {
        m_lowX = std::min(m_lowX, face.low[0]);
        m_lowY = std::min(m_lowY, face.low[1]);
        highX = std::max(highX, face.high[0]);
        highY = std::max(highY, face.high[1]);
    }

    // A margin, so faces on the rim lie inside a cell and not on the grid's edge.
    m_lowX -= 1.0;
    m_lowY -= 1.0;

    // A map far wider than the grid was meant for gets larger cells, not more of them.
    while ((highX - m_lowX) / m_cellSize > 1024.0 || (highY - m_lowY) / m_cellSize > 1024.0)
    {
        m_cellSize *= 2.0;
    }

    m_columns = static_cast<int>(std::floor((highX + 1.0 - m_lowX) / m_cellSize)) + 1;
    m_rows = static_cast<int>(std::floor((highY + 1.0 - m_lowY) / m_cellSize)) + 1;
    m_cells.resize(static_cast<size_t>(m_columns) * static_cast<size_t>(m_rows));

    for (size_t faceIndex = 0; faceIndex < m_faces.size(); ++faceIndex)
    {
        const Face &face = m_faces[faceIndex];
        const int fromColumn = std::clamp(
            static_cast<int>(std::floor((face.low[0] - 0.5 - m_lowX) / m_cellSize)), 0, m_columns - 1);
        const int toColumn = std::clamp(
            static_cast<int>(std::floor((face.high[0] + 0.5 - m_lowX) / m_cellSize)), 0, m_columns - 1);
        const int fromRow = std::clamp(
            static_cast<int>(std::floor((face.low[1] - 0.5 - m_lowY) / m_cellSize)), 0, m_rows - 1);
        const int toRow = std::clamp(
            static_cast<int>(std::floor((face.high[1] + 0.5 - m_lowY) / m_cellSize)), 0, m_rows - 1);

        for (int row = fromRow; row <= toRow; ++row)
        {
            for (int column = fromColumn; column <= toColumn; ++column)
            {
                m_cells[static_cast<size_t>(row) * static_cast<size_t>(m_columns) + static_cast<size_t>(column)]
                    .push_back(static_cast<uint32_t>(faceIndex));
            }
        }
    }
}

void RayScene::setSeamTolerance(double tolerance)
{
    m_seamTolerance = std::max(0.0, tolerance);
}

size_t RayScene::faceCount() const
{
    return m_faces.size();
}

void RayScene::testCell(
    size_t cell,
    const std::array<double, 3> &origin,
    const std::array<double, 3> &direction,
    double &best,
    int32_t &bestFace,
    std::vector<EdgeHit> &edgeHits) const
{
    for (const uint32_t faceIndex : m_cells[cell])
    {
        const Face &face = m_faces[faceIndex];
        const double approach =
            face.normal[0] * direction[0] + face.normal[1] * direction[1] + face.normal[2] * direction[2];

        // From behind or along the face: not seen.
        if (approach > -1.0e-9)
        {
            continue;
        }

        const double height =
            face.normal[0] * origin[0] + face.normal[1] * origin[1] + face.normal[2] * origin[2] - face.offset;
        const double distance = -height / approach;

        if (distance <= 1.0e-6 || distance >= best)
        {
            continue;
        }

        const std::array<double, 3> point = {origin[0] + direction[0] * distance,
            origin[1] + direction[1] * distance, origin[2] + direction[2] * distance};
        bool inBox = true;
        const double slack = m_seamTolerance + 1.0e-6;

        // The box is checked on the axes kept: an outline that is not exactly flat is still met on its plane.
        for (size_t axis = 0; axis < 3; ++axis)
        {
            if (static_cast<int>(axis) != face.dropAxis
                && (point[axis] < face.low[axis] - slack || point[axis] > face.high[axis] + slack))
            {
                inBox = false;
            }
        }

        if (!inBox)
        {
            continue;
        }

        const size_t first = face.dropAxis == 0 ? 1 : 0;
        const size_t second = face.dropAxis == 2 ? 1 : 2;

        if (insideOutline(face.flat, point[first], point[second]))
        {
            best = distance;
            bestFace = static_cast<int32_t>(faceIndex);
        }
        else if (m_seamTolerance > 0.0 && nearOutlineEdge(face.flat, point[first], point[second], m_seamTolerance))
        {
            // On a seam the even-odd test may give the point to neither of the faces that meet there (faces
            // flattened on different axes, a vertex of one on the edge of another): kept for the end of the cast.
            edgeHits.push_back({distance, approach, faceIndex});
        }
    }
}

RayHit RayScene::cast(
    const std::array<double, 3> &origin, const std::array<double, 3> &direction, double cap) const
{
    RayHit result;
    result.distance = cap;

    if (m_cells.empty())
    {
        return result;
    }

    double best = cap;
    int32_t bestFace = -1;
    const double highX = m_lowX + m_columns * m_cellSize;
    const double highY = m_lowY + m_rows * m_cellSize;
    // The part of the ray over the grid.
    double enter = 0.0;
    double leave = cap;
    const std::array<double, 2> lows = {m_lowX, m_lowY};
    const std::array<double, 2> highs = {highX, highY};

    for (size_t axis = 0; axis < 2; ++axis)
    {
        if (std::fabs(direction[axis]) < 1.0e-12)
        {
            if (origin[axis] < lows[axis] || origin[axis] >= highs[axis])
            {
                return result;
            }

            continue;
        }

        const double toLow = (lows[axis] - origin[axis]) / direction[axis];
        const double toHigh = (highs[axis] - origin[axis]) / direction[axis];
        enter = std::max(enter, std::min(toLow, toHigh));
        leave = std::min(leave, std::max(toLow, toHigh));
    }

    if (enter >= leave)
    {
        return result;
    }

    // Cell by cell along the ray's shadow on the plan; a hit nearer than the way out of a cell is the nearest.
    const double startX = origin[0] + direction[0] * (enter + 1.0e-7);
    const double startY = origin[1] + direction[1] * (enter + 1.0e-7);
    int column = std::clamp(static_cast<int>(std::floor((startX - m_lowX) / m_cellSize)), 0, m_columns - 1);
    int row = std::clamp(static_cast<int>(std::floor((startY - m_lowY) / m_cellSize)), 0, m_rows - 1);
    const int stepColumn = direction[0] > 0.0 ? 1 : -1;
    const int stepRow = direction[1] > 0.0 ? 1 : -1;
    const double never = 1.0e300;
    const double perColumn = std::fabs(direction[0]) < 1.0e-12 ? never : m_cellSize / std::fabs(direction[0]);
    const double perRow = std::fabs(direction[1]) < 1.0e-12 ? never : m_cellSize / std::fabs(direction[1]);
    double nextColumn = never;
    double nextRow = never;

    if (perColumn < never)
    {
        const double edge = m_lowX + (column + (stepColumn > 0 ? 1 : 0)) * m_cellSize;
        nextColumn = (edge - origin[0]) / direction[0];
    }

    if (perRow < never)
    {
        const double edge = m_lowY + (row + (stepRow > 0 ? 1 : 0)) * m_cellSize;
        nextRow = (edge - origin[1]) / direction[1];
    }

    std::vector<EdgeHit> edgeHits;

    while (column >= 0 && column < m_columns && row >= 0 && row < m_rows)
    {
        testCell(static_cast<size_t>(row) * static_cast<size_t>(m_columns) + static_cast<size_t>(column), origin,
            direction, best, bestFace, edgeHits);
        const double out = std::min(nextColumn, nextRow);

        if (best <= out || out >= leave)
        {
            break;
        }

        if (nextColumn < nextRow)
        {
            column += stepColumn;
            nextColumn += perColumn;
        }
        else
        {
            row += stepRow;
            nextRow += perRow;
        }
    }

    // A seam nearer than what the ray met inside an outline: two or more faces whose edges it ran into at one
    // place. The ray meets the one it looks at most squarely (of two alike, the one whose texture comes first by
    // name, so two maps with the same seam read it alike whatever the order of their faces).
    if (!edgeHits.empty())
    {
        double nearest = best;

        for (const EdgeHit &edgeHit : edgeHits)
        {
            nearest = std::min(nearest, edgeHit.distance);
        }

        const double together = 0.01 * (1.0 + nearest) + m_seamTolerance;
        int32_t seamFace = -1;
        double seamApproach = 0.0;
        double seamDistance = 0.0;
        size_t facesAtSeam = 0;

        for (const EdgeHit &edgeHit : edgeHits)
        {
            if (edgeHit.distance > nearest + together || edgeHit.distance >= best - 1.0e-6)
            {
                continue;
            }

            bool counted = false;

            for (const EdgeHit &other : edgeHits)
            {
                if (&other == &edgeHit)
                {
                    break;
                }

                counted = counted || (other.face == edgeHit.face && other.distance <= nearest + together);
            }

            facesAtSeam += counted ? 0 : 1;
            const uint32_t chosen = static_cast<uint32_t>(std::max(seamFace, 0));
            const bool better = seamFace < 0 || edgeHit.approach < seamApproach - 1.0e-6
                || (std::fabs(edgeHit.approach - seamApproach) <= 1.0e-6
                    && std::tie(m_faces[edgeHit.face].texture, edgeHit.face)
                        < std::tie(m_faces[chosen].texture, chosen));

            if (better)
            {
                seamFace = static_cast<int32_t>(edgeHit.face);
                seamApproach = edgeHit.approach;
                seamDistance = edgeHit.distance;
            }
        }

        if (facesAtSeam >= 2 && seamDistance < best - 1.0e-6)
        {
            best = seamDistance;
            bestFace = seamFace;
        }
    }

    if (bestFace >= 0)
    {
        const Face &face = m_faces[static_cast<size_t>(bestFace)];
        result.hit = true;
        result.distance = best;
        result.sourceId = face.sourceId;
        result.kind = face.kind;
        result.texture = face.texture;

        if (face.hasTexel)
        {
            const std::array<double, 3> offset = {origin[0] + direction[0] * best - face.texelOrigin[0],
                origin[1] + direction[1] * best - face.texelOrigin[1],
                origin[2] + direction[2] * best - face.texelOrigin[2]};
            result.hasTexel = true;
            result.texel = {
                face.originTexel[0] + face.gradientU[0] * offset[0] + face.gradientU[1] * offset[1]
                    + face.gradientU[2] * offset[2],
                face.originTexel[1] + face.gradientV[0] * offset[0] + face.gradientV[1] * offset[1]
                    + face.gradientV[2] * offset[2]};
        }
    }

    return result;
}

std::vector<std::pair<double, int32_t>> RayScene::heightsAt(double x, double y, bool withEdges) const
{
    // Half a unit: map points are whole numbers, so a point this near an edge is on it.
    constexpr double EdgeTolerance = 0.5;
    const double slack = withEdges ? EdgeTolerance : 0.0;

    std::vector<std::pair<double, int32_t>> heights;

    if (m_cells.empty() || x < m_lowX || y < m_lowY)
    {
        return heights;
    }

    const int column = static_cast<int>(std::floor((x - m_lowX) / m_cellSize));
    const int row = static_cast<int>(std::floor((y - m_lowY) / m_cellSize));

    if (column >= m_columns || row >= m_rows)
    {
        return heights;
    }

    for (const uint32_t faceIndex :
         m_cells[static_cast<size_t>(row) * static_cast<size_t>(m_columns) + static_cast<size_t>(column)])
    {
        const Face &face = m_faces[faceIndex];

        if (face.plan.empty() || x < face.low[0] - slack || x > face.high[0] + slack || y < face.low[1] - slack
            || y > face.high[1] + slack
            || (!insideOutline(face.plan, x, y) && !(withEdges && nearOutlineEdge(face.plan, x, y, EdgeTolerance))))
        {
            continue;
        }

        heights.push_back({(face.offset - face.normal[0] * x - face.normal[1] * y) / face.normal[2], face.sourceId});
    }

    std::sort(heights.begin(), heights.end());
    return heights;
}

Game::EventRuntimeState posesAfterLoadEvents(
    const Game::MapDeltaData &state, const std::string &eventFlowJson, const std::vector<uint16_t> &loadEvents)
{
    Game::EventRuntimeState poses;
    YAML::Node events;

    try
    {
        events = YAML::Load(eventFlowJson);
    }
    catch (const YAML::Exception &)
    {
        return poses;
    }

    for (const YAML::Node &event : events)
    {
        const YAML::Node paths = event["paths"];

        if (std::find(loadEvents.begin(), loadEvents.end(), event["event"].as<int>()) == loadEvents.end()
            || paths.size() == 0)
        {
            continue;
        }

        // The first way through a handler is the one with every test answered no.
        const YAML::Node firstVisit = paths[0];

        for (const YAML::Node &effectNode : firstVisit["effects"])
        {
            unsigned doorId = 0;
            char action[16] = {};

            if (std::sscanf(effectNode.Scalar().c_str(), "door %u %15s", &doorId, action) != 2)
            {
                continue;
            }

            const std::string name = action;

            for (const Game::MapDeltaDoor &door : state.doors)
            {
                if (door.doorId != doorId || (name != "open" && name != "close" && name != "toggle"))
                {
                    continue;
                }

                // Where it stands so far: as an earlier effect left it, else as the scene has it.
                const std::unordered_map<uint32_t, Game::RuntimeMechanismState>::const_iterator moved =
                    poses.mechanisms.find(doorId);
                const bool wasOpen = moved != poses.mechanisms.end()
                    ? moved->second.state == static_cast<uint16_t>(Game::EvtMechanismState::Open)
                    : door.state == static_cast<uint16_t>(Game::EvtMechanismState::Open)
                        || door.state == static_cast<uint16_t>(Game::EvtMechanismState::Opening);
                const bool open = name == "open" || (name == "toggle" && !wasOpen);
                Game::RuntimeMechanismState pose;
                pose.state =
                    static_cast<uint16_t>(open ? Game::EvtMechanismState::Open : Game::EvtMechanismState::Closed);
                pose.currentDistance = open ? 0.0f : static_cast<float>(door.moveLength);
                poses.mechanisms[doorId] = pose;
            }
        }
    }

    return poses;
}

namespace
{
struct StandPoint
{
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    int32_t face = -1;
    // Moved off its grid point to stand clear; left on it for want of a clear place.
    bool moved = false;
    bool onEdge = false;
};

// One map made ready: what is seen (the faces as the map starts), where one can stand (the walk floors with
// every door out of the way) and the stand points on the grid.
struct PreparedMap
{
    RayScene seen;
    RayScene floors;
    // The faces of the moving parts as the map starts, seen from behind: what a look from inside a shut block meets.
    RayScene blockInsides;
    std::vector<StandPoint> points;
    bool floorEdges = true;
};

// The party's body, as core/Reachability walks it.
Game::PathObject partyBody()
{
    Game::PathObject body;
    body.radius = 37.0f;
    body.height = 192.0f;
    body.stepLength = 32.0f;
    body.stepHeight = 40.0f;
    body.dropHeight = 2048.0f;
    body.riserHeight = 80.0f;
    return body;
}

// The path map with every door's faces out of the way as obstacles and kept, in both poses, where they are
// floors (lifts, bridges): the same reading of "doors open" as core/Reachability's.
Game::PathMap buildOpenPathMap(const LoadedMap &map)
{
    const Game::IndoorMapData &indoor = *map.indoor;
    const Game::MapDeltaData *pState = map.state ? &*map.state : nullptr;
    std::set<int32_t> doorFaces;
    Game::EventRuntimeState atOpen;
    Game::EventRuntimeState atClosed;

    if (pState != nullptr)
    {
        for (const Game::MapDeltaDoor &door : pState->doors)
        {
            for (const uint16_t faceId : door.faceIds)
            {
                doorFaces.insert(faceId);
            }

            Game::RuntimeMechanismState open;
            open.state = static_cast<uint16_t>(Game::EvtMechanismState::Open);
            open.currentDistance = 0.0f;
            atOpen.mechanisms[door.doorId] = open;
            Game::RuntimeMechanismState closed;
            closed.state = static_cast<uint16_t>(Game::EvtMechanismState::Closed);
            closed.currentDistance = static_cast<float>(door.moveLength);
            atClosed.mechanisms[door.doorId] = closed;
        }
    }

    std::vector<Game::PathFacet> facets;
    const std::array<const Game::EventRuntimeState *, 3> states = {nullptr, &atOpen, &atClosed};
    const std::set<uint32_t> ignored = facesTheGameIgnores(indoor);

    for (size_t pass = 0; pass < (doorFaces.empty() ? 1u : 3u); ++pass)
    {
        const std::vector<Game::IndoorVertex> vertices =
            Game::buildIndoorMechanismAdjustedVertices(indoor, pState, states[pass]);
        const Game::IndoorPathMapBuildResult built =
            Game::IndoorPathfindingBuilder::buildPathMap(indoor, vertices, pState);

        for (const Game::PathFacet &facet : built.pathMap.facets())
        {
            const bool isDoorFace = doorFaces.contains(facet.sourceId);

            if (ignored.contains(static_cast<uint32_t>(facet.sourceId)))
            {
                continue;
            }

            if ((!isDoorFace && pass == 0) || (isDoorFace && pass != 0 && facet.walkableFloor))
            {
                facets.push_back(facet);
            }
        }
    }

    Game::PathMap pathMap;
    pathMap.setFacets(std::move(facets));
    pathMap.buildSpatialGrid(512.0f);
    return pathMap;
}

uint64_t cellKey(long long column, long long row, long long level)
{
    return (static_cast<uint64_t>(column + (1 << 20)) & 0x1fffff) << 42
        | (static_cast<uint64_t>(row + (1 << 20)) & 0x1fffff) << 21
        | (static_cast<uint64_t>(level + (1 << 20)) & 0x1fffff);
}

// Walks from the seeds over the walk grid with the path map's own step, as core/Reachability's flood does, and
// keeps every cell stood on.
void floodStandCells(
    const Game::PathMap &pathMap,
    const std::vector<Game::PathPoint> &seeds,
    std::unordered_map<uint64_t, StandPoint> &cells)
{
    constexpr float Step = static_cast<float>(WalkStep);
    constexpr float LevelHeight = 64.0f;
    const Game::PathObject body = partyBody();
    const auto keyOf = [](const Game::PathPoint &point)
    {
        return cellKey(std::lround(point.x / Step), std::lround(point.y / Step), std::lround(point.z / LevelHeight));
    };
    const auto stand = [&pathMap, &cells, &keyOf](const Game::PathPoint &point)
    {
        const Game::PathFloorSample under = pathMap.floorAt({point.x, point.y, point.z + 1.0f});
        StandPoint cell;
        cell.x = point.x;
        cell.y = point.y;
        cell.z = point.z;

        if (under.hasFloor && under.facetIndex < pathMap.facets().size())
        {
            cell.face = pathMap.facets()[under.facetIndex].sourceId;
        }

        return cells.emplace(keyOf(point), cell).second;
    };
    std::vector<Game::PathPoint> frontier;

    for (const Game::PathPoint &seed : seeds)
    {
        bool valid = false;
        Game::PathPoint start = seed;
        const Game::PathFloorSample under = pathMap.floorAt({seed.x, seed.y, seed.z + body.stepHeight});

        if (under.hasFloor && !under.inVoid && std::abs(under.z - seed.z) <= body.stepHeight)
        {
            start.z = under.z;
            valid = true;
        }
        else
        {
            start = pathMap.snapToNearestWalkableFloor(seed, 256.0f, valid);
        }

        if (valid)
        {
            // The walk goes over grid points, so the stand points of two maps fall on the same places.
            start.x = std::round(start.x / Step) * Step;
            start.y = std::round(start.y / Step) * Step;
            const Game::PathFloorSample snapped = pathMap.floorAt({start.x, start.y, start.z + body.stepHeight});

            if (snapped.hasFloor && !snapped.inVoid)
            {
                start.z = snapped.z;
            }

            if (stand(start))
            {
                frontier.push_back(start);
            }
        }
    }

    static const std::array<std::array<float, 2>, 8> directions = {{
        {1.0f, 0.0f}, {-1.0f, 0.0f}, {0.0f, 1.0f}, {0.0f, -1.0f},
        {1.0f, 1.0f}, {1.0f, -1.0f}, {-1.0f, 1.0f}, {-1.0f, -1.0f}}};

    while (!frontier.empty())
    {
        const Game::PathPoint point = frontier.back();
        frontier.pop_back();

        for (const std::array<float, 2> &direction : directions)
        {
            Game::PathPoint target = {
                (std::round(point.x / Step) + direction[0]) * Step,
                (std::round(point.y / Step) + direction[1]) * Step,
                point.z};
            const Game::PathFloorSample targetFloor =
                pathMap.floorAt({target.x, target.y, point.z + body.stepHeight});

            if (!targetFloor.hasFloor || targetFloor.inVoid || targetFloor.z - point.z > body.stepHeight
                || point.z - targetFloor.z > body.dropHeight)
            {
                continue;
            }

            target.z = targetFloor.z;

            if (cells.contains(keyOf(target)) || !pathMap.resolveWalkStep(point, target, body))
            {
                continue;
            }

            if (stand(target))
            {
                frontier.push_back(target);
            }
        }
    }
}

const std::array<std::array<double, 2>, 8> &ringDirections()
{
    static const std::array<std::array<double, 2>, 8> ring = {{
        {1.0, 0.0}, {0.0, 1.0}, {-1.0, 0.0}, {0.0, -1.0},
        {0.70710678, 0.70710678}, {-0.70710678, 0.70710678}, {-0.70710678, -0.70710678}, {0.70710678, -0.70710678}}};
    return ring;
}

// Whether a face passes within `clearance` of an eye at its own height, seen from either side: eight lines through
// the eye, each looked along from both of its ends.
bool faceNearEye(const RayScene &seen, double x, double y, double eyeZ, double clearance)
{
    for (const std::array<double, 2> &direction : ringDirections())
    {
        if (seen.cast({x + direction[0] * clearance, y + direction[1] * clearance, eyeZ},
                    {-direction[0], -direction[1], 0.0}, 2.0 * clearance)
                .hit)
        {
            return true;
        }
    }

    return false;
}

// An eye this near a face is in the wall: the face is not seen from there and the look goes through it.
constexpr double InWall = 2.0;

// Whether a place stands clear: the walk floor runs on at its height all round it (no ledge, pit, panel edge or
// wall foot within the clearance; a slope or a low step is no edge), and no face stands within the clearance of the
// eye.
bool standsClear(const PreparedMap &prepared, double x, double y, double z)
{
    for (const std::array<double, 2> &direction : ringDirections())
    {
        bool floorRunsOn = false;

        for (const std::pair<double, int32_t> &entry :
             prepared.floors.heightsAt(x + direction[0] * EdgeClearance, y + direction[1] * EdgeClearance))
        {
            floorRunsOn = floorRunsOn || std::fabs(entry.first - z) <= EdgeClearance + 1.0;
        }

        if (!floorRunsOn)
        {
            return false;
        }
    }

    return !faceNearEye(prepared.seen, x, y, z + EyeHeight, EdgeClearance);
}

// Whether an eye is inside a moving block as the map starts: in two opposite level directions the nearest thing is
// the back of one of the block's own faces; or the back of its underside lies between the eye and the feet (a plug
// let down to the floor of its passage); or the back of its top is the first thing overhead (the pit under a solid
// lift that stands raised). A look from in there sees the block's inside and says nothing of the map.
bool insideShutBlock(const PreparedMap &prepared, double x, double y, double z)
{
    if (prepared.blockInsides.faceCount() == 0)
    {
        return false;
    }

    const std::array<double, 3> eye = {x, y, z + EyeHeight};
    const RayHit under = prepared.blockInsides.cast(eye, {0.0, 0.0, -1.0}, EyeHeight + 1.0);
    const RayHit over = prepared.blockInsides.cast(eye, {0.0, 0.0, 1.0}, BlockThickness);

    if ((under.hit && prepared.seen.cast(eye, {0.0, 0.0, -1.0}, under.distance).distance >= under.distance)
        || (over.hit && prepared.seen.cast(eye, {0.0, 0.0, 1.0}, over.distance).distance >= over.distance))
    {
        return true;
    }

    // Four lines through the eye, turned a little off the axes so none runs along a block's side.
    for (int index = 0; index < 4; ++index)
    {
        const double angle = (index * 45.0 + 7.0) * Pi / 180.0;
        const std::array<double, 3> forward = {oy::cos(angle), oy::sin(angle), 0.0};
        const std::array<double, 3> backward = {-forward[0], -forward[1], 0.0};
        const RayHit ahead = prepared.blockInsides.cast(eye, forward, BlockThickness);
        const RayHit behind = prepared.blockInsides.cast(eye, backward, BlockThickness);

        if (ahead.hit && behind.hit && ahead.distance + behind.distance <= BlockThickness
            && prepared.seen.cast(eye, forward, ahead.distance).distance >= ahead.distance
            && prepared.seen.cast(eye, backward, behind.distance).distance >= behind.distance)
        {
            return true;
        }
    }

    return false;
}

// The moving parts as the party first sees them (posesAfterLoadEvents), from the map's own handlers.
Game::EventRuntimeState startingPoses(const LoadedMap &map)
{
    std::string flowJson;
    std::string errorMessage;

    if (!map.events || !map.state || !exploreEventHandlers(map, flowJson, errorMessage))
    {
        return {};
    }

    return posesAfterLoadEvents(*map.state, flowJson, map.events->onLoadEventIds());
}

bool prepareMap(const LoadedMap &map, const CompareOptions &options, PreparedMap &prepared, std::string &errorMessage)
{
    const double step = std::max(WalkStep, std::round(options.step / WalkStep) * WalkStep);

    if (!map.indoor)
    {
        errorMessage = map.fileName + " is not an indoor map: compare reads indoor maps";
        return false;
    }

    const Game::IndoorMapData &indoor = *map.indoor;
    const Game::MapDeltaData *pState = map.state ? &*map.state : nullptr;
    const Game::EventRuntimeState starting = options.storedPoses ? Game::EventRuntimeState() : startingPoses(map);
    const std::vector<Game::IndoorVertex> vertices =
        Game::buildIndoorMechanismAdjustedVertices(indoor, pState, &starting);

    // What is seen: every face that the game draws, as the party first sees the map (not those of a sector nothing
    // enters, which the game never draws: facesTheGameIgnores).
    const std::set<uint32_t> ignored = facesTheGameIgnores(indoor);

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];
        const uint32_t attributes = pState != nullptr && faceIndex < pState->faceAttributes.size()
            ? pState->faceAttributes[faceIndex] : face.attributes;

        if (face.isPortal || Game::hasFaceAttribute(attributes, Game::FaceAttribute::IsPortal)
            || Game::hasFaceAttribute(attributes, Game::FaceAttribute::Invisible)
            || ignored.contains(static_cast<uint32_t>(faceIndex)))
        {
            continue;
        }

        std::vector<std::array<double, 3>> points;
        bool whole = face.vertexIndices.size() >= 3;
        // Its texels as the map stores them (each corner's and the face's delta). A face that stands moved at the
        // start and does not take its texture with it is drawn from its place in the world: its texels are not
        // read.
        std::vector<std::array<double, 2>> texels;
        bool texelsHold = face.textureUs.size() >= face.vertexIndices.size()
            && face.textureVs.size() >= face.vertexIndices.size();

        for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
        {
            const uint16_t vertexIndex = face.vertexIndices[corner];

            if (vertexIndex >= vertices.size())
            {
                whole = false;
                break;
            }

            const Game::IndoorVertex &vertex = vertices[vertexIndex];
            points.push_back(
                {static_cast<double>(vertex.x), static_cast<double>(vertex.y), static_cast<double>(vertex.z)});

            if (texelsHold)
            {
                const Game::IndoorVertex &stored = indoor.vertices[vertexIndex];
                texelsHold = (stored.x == vertex.x && stored.y == vertex.y && stored.z == vertex.z)
                    || Game::hasFaceAttribute(attributes, Game::FaceAttribute::TextureMoveByDoor);
                texels.push_back({double(face.textureUs[corner]) + face.textureDeltaU,
                    double(face.textureVs[corner]) + face.textureDeltaV});
            }
        }

        if (whole)
        {
            prepared.seen.addFace(points, {0.0, 0.0, 0.0}, static_cast<int32_t>(faceIndex), face.textureName,
                texelsHold ? &texels : nullptr);
        }
    }

    prepared.seen.setSeamTolerance(options.openSeams ? 0.0 : 0.5);
    prepared.seen.build();
    prepared.floorEdges = !options.exactFloorEdges;

    // The moving parts' faces turned round.
    if (pState != nullptr && !options.thinBlocksOnly)
    {
        for (const Game::MapDeltaDoor &door : pState->doors)
        {
            for (const uint16_t faceId : door.faceIds)
            {
                if (faceId >= indoor.faces.size() || indoor.faces[faceId].isPortal)
                {
                    continue;
                }

                std::vector<std::array<double, 3>> points;
                const std::vector<uint16_t> &vertexIndices = indoor.faces[faceId].vertexIndices;

                for (size_t index = vertexIndices.size(); index-- > 0;)
                {
                    if (vertexIndices[index] < vertices.size())
                    {
                        const Game::IndoorVertex &vertex = vertices[vertexIndices[index]];
                        points.push_back({static_cast<double>(vertex.x), static_cast<double>(vertex.y),
                            static_cast<double>(vertex.z)});
                    }
                }

                if (points.size() == vertexIndices.size())
                {
                    prepared.blockInsides.addFace(points, {0.0, 0.0, 0.0}, static_cast<int32_t>(faceId), std::string());
                }
            }
        }

        prepared.blockInsides.build();
    }

    // Where one can stand.
    const Game::PathMap pathMap = buildOpenPathMap(map);
    std::map<int32_t, double> walkAreaOfSector;
    std::map<int32_t, std::pair<double, Game::PathPoint>> seedOfSector;

    for (const Game::PathFacet &facet : pathMap.facets())
    {
        if (!facet.walkableFloor || facet.vertices.size() < 3)
        {
            continue;
        }

        std::vector<std::array<double, 3>> points;
        double doubleArea = 0.0;
        Game::PathPoint middle;

        for (size_t index = 0; index < facet.vertices.size(); ++index)
        {
            const Game::PathPoint &vertex = facet.vertices[index];
            const Game::PathPoint &next = facet.vertices[(index + 1) % facet.vertices.size()];
            points.push_back(
                {static_cast<double>(vertex.x), static_cast<double>(vertex.y), static_cast<double>(vertex.z)});
            doubleArea += static_cast<double>(vertex.x) * next.y - static_cast<double>(next.x) * vertex.y;
            middle.x += vertex.x / static_cast<float>(facet.vertices.size());
            middle.y += vertex.y / static_cast<float>(facet.vertices.size());
            middle.z += vertex.z / static_cast<float>(facet.vertices.size());
        }

        prepared.floors.addFace(points, {0.0, 0.0, 1.0}, facet.sourceId, std::string());

        if (facet.sourceId >= 0 && static_cast<size_t>(facet.sourceId) < indoor.faces.size())
        {
            const int32_t sector = indoor.faces[static_cast<size_t>(facet.sourceId)].roomNumber;
            const double area = std::abs(doubleArea) / 2.0;
            walkAreaOfSector[sector] += area;
            std::pair<double, Game::PathPoint> &seed = seedOfSector[sector];

            if (area > seed.first)
            {
                seed = {area, middle};
            }
        }
    }

    prepared.floors.build();
    std::optional<Game::IndoorPartyStartPoint> start = indoor.partyStartPoint;

    if (map.indoorScene && !map.indoorScene->partyStartPoints.empty())
    {
        start = map.indoorScene->partyStartPoints.front().startPoint;
    }

    std::unordered_map<uint64_t, StandPoint> cells;

    if (start)
    {
        floodStandCells(pathMap,
            {{static_cast<float>(start->x), static_cast<float>(start->y), static_cast<float>(start->z)}}, cells);
    }

    // What the walk from the start does not reach (behind a teleport, or a map without a start) is walked from
    // its own floors, sector by sector, where a sector has room to stand in.
    constexpr double NicheFloorArea = 40000.0;

    for (const std::pair<const int32_t, std::pair<double, Game::PathPoint>> &entry : seedOfSector)
    {
        if (walkAreaOfSector[entry.first] < NicheFloorArea)
        {
            continue;
        }

        std::set<int32_t> reachedSectors;

        for (const std::pair<const uint64_t, StandPoint> &cell : cells)
        {
            if (cell.second.face >= 0 && static_cast<size_t>(cell.second.face) < indoor.faces.size())
            {
                reachedSectors.insert(indoor.faces[static_cast<size_t>(cell.second.face)].roomNumber);
            }
        }

        if (!reachedSectors.contains(entry.first))
        {
            floodStandCells(pathMap, {entry.second.second}, cells);
        }
    }

    const long long every = std::max(1LL, std::llround(step / WalkStep));

    // Where the moving parts stand as the map starts. The walk has every door out of the way, so it also stands
    // inside shut leaves and gate blocks; a look from in there sees the block's inside and says nothing of the map.
    std::vector<std::array<double, 6>> doorBoxes;

    if (pState != nullptr)
    {
        for (const Game::MapDeltaDoor &door : pState->doors)
        {
            std::array<double, 6> box = {};
            bool any = false;

            // The block is what the door's faces enclose: its moving vertices alone may be one edge of it.
            for (const uint16_t faceId : door.faceIds)
            {
                if (faceId >= indoor.faces.size())
                {
                    continue;
                }

                for (const uint16_t vertexId : indoor.faces[faceId].vertexIndices)
                {
                    if (vertexId >= vertices.size())
                    {
                        continue;
                    }

                    const double at[3] = {static_cast<double>(vertices[vertexId].x),
                        static_cast<double>(vertices[vertexId].y), static_cast<double>(vertices[vertexId].z)};

                    for (size_t axis = 0; axis < 3; ++axis)
                    {
                        box[axis] = any ? std::min(box[axis], at[axis]) : at[axis];
                        box[axis + 3] = any ? std::max(box[axis + 3], at[axis]) : at[axis];
                    }

                    any = true;
                }
            }

            // Leaves and gate blocks are thin one way in plan. A wide moving floor or ring is no block to stand in,
            // and its box would cover the rooms round it.
            if (any && std::min(box[3] - box[0], box[4] - box[1]) <= 512.0)
            {
                doorBoxes.push_back(box);
            }
        }
    }

    const auto insideDoor = [&doorBoxes, &prepared](const StandPoint &point)
    {
        constexpr double Margin = 8.0;

        for (const std::array<double, 6> &box : doorBoxes)
        {
            if (point.x > box[0] - Margin && point.x < box[3] + Margin && point.y > box[1] - Margin
                && point.y < box[4] + Margin && point.z + EyeHeight > box[2] && point.z + 1.0 < box[5])
            {
                return true;
            }
        }

        // A block that is not thin along the axes (a gate set askew) has no such box.
        return insideShutBlock(prepared, point.x, point.y, point.z);
    };
    // The walk's floor under a place near a cell's height, where the walk stood on the cell there.
    const auto standAt = [&pathMap, &cells](double x, double y, double z, StandPoint &point)
    {
        const Game::PathFloorSample under =
            pathMap.floorAt({static_cast<float>(x), static_cast<float>(y), static_cast<float>(z) + 40.0f});

        if (!under.hasFloor || under.inVoid || std::fabs(under.z - z) > 40.0
            || under.facetIndex >= pathMap.facets().size())
        {
            return false;
        }

        const long long level = std::llround(under.z / 64.0);
        bool walked = false;

        for (long long offset = -1; offset <= 1; ++offset)
        {
            walked = walked || cells.contains(cellKey(std::llround(x / WalkStep), std::llround(y / WalkStep),
                level + offset));
        }

        point.x = x;
        point.y = y;
        point.z = under.z;
        point.face = pathMap.facets()[under.facetIndex].sourceId;
        return walked;
    };
    // Where a point may move to when its grid point is on a floor's edge or against a wall: the nearest first,
    // never as far as half the way to the next point.
    std::vector<std::array<double, 2>> nudges;

    for (const double reach : {16.0, 32.0, 48.0})
    {
        if (reach * 2.0 < step && !options.pointsOnGrid)
        {
            for (const std::array<double, 2> &direction : std::initializer_list<std::array<double, 2>>{
                     {1.0, 0.0}, {0.0, 1.0}, {-1.0, 0.0}, {0.0, -1.0}, {1.0, 1.0}, {-1.0, 1.0}, {-1.0, -1.0},
                     {1.0, -1.0}})
            {
                nudges.push_back({direction[0] * reach, direction[1] * reach});
            }
        }
    }

    for (const std::pair<const uint64_t, StandPoint> &cell : cells)
    {
        const long long column = std::llround(cell.second.x / WalkStep);
        const long long row = std::llround(cell.second.y / WalkStep);

        if (column % every != 0 || row % every != 0)
        {
            continue;
        }

        // A step that slid along a wall ends beside its grid point: the stand point is the grid point itself,
        // where it has the same floor.
        StandPoint point = cell.second;
        point.x = static_cast<double>(column) * WalkStep;
        point.y = static_cast<double>(row) * WalkStep;

        if (std::fabs(point.x - cell.second.x) > 0.01 || std::fabs(point.y - cell.second.y) > 0.01)
        {
            const Game::PathFloorSample under = pathMap.floorAt({static_cast<float>(point.x),
                static_cast<float>(point.y), static_cast<float>(point.z) + 40.0f});

            if (!under.hasFloor || under.inVoid || std::fabs(under.z - point.z) > 40.0
                || under.facetIndex >= pathMap.facets().size())
            {
                continue;
            }

            point.z = under.z;
            point.face = pathMap.facets()[under.facetIndex].sourceId;
        }

        if (insideDoor(point))
        {
            continue;
        }

        // A point exactly on a ledge, a panel's edge or a wall's line reads one map's floor here and the other's
        // there, and looks along the wall: it moves to the nearest place that stands clear. On a narrow ledge or a
        // stair there may be none, and it stays.
        if (!options.pointsOnGrid && !standsClear(prepared, point.x, point.y, point.z))
        {
            point.onEdge = true;

            for (const std::array<double, 2> &nudge : nudges)
            {
                StandPoint moved;

                if (standAt(point.x + nudge[0], point.y + nudge[1], point.z, moved)
                    && standsClear(prepared, moved.x, moved.y, moved.z) && !insideDoor(moved))
                {
                    moved.moved = true;
                    point = moved;
                    break;
                }
            }

            // Left with its eye in a wall, nothing can be read from it.
            if (!point.moved && faceNearEye(prepared.seen, point.x, point.y, point.z + EyeHeight, InWall))
            {
                continue;
            }
        }

        prepared.points.push_back(point);
    }

    std::sort(prepared.points.begin(), prepared.points.end(), [](const StandPoint &left, const StandPoint &right)
    {
        return std::tie(left.x, left.y, left.z) < std::tie(right.x, right.y, right.z);
    });
    return true;
}

// The floor of a map under a point nearest in height, within the search height. A floor's edge is part of the floor
// (the walk that found the point has it so): on a ledge's edge the ledge is found as well as the floor below, in
// both maps. But a floor whose edge is a wall's foot is no place to stand: with its eye in the wall the point has
// no floor there.
bool nearestFloor(const PreparedMap &map, double x, double y, double z, double &height, bool *pInWall = nullptr)
{
    bool found = false;

    for (const std::pair<double, int32_t> &entry : map.floors.heightsAt(x, y, map.floorEdges))
    {
        if (std::fabs(entry.first - z) <= FloorSearch && (!found || std::fabs(entry.first - z) < std::fabs(height - z)))
        {
            height = entry.first;
            found = true;
        }
    }

    const bool inWall = found && map.floorEdges && faceNearEye(map.seen, x, y, height + EyeHeight, InWall);

    if (pInWall != nullptr)
    {
        *pInWall = inWall;
    }

    return found && !inWall;
}

struct RayDirection
{
    std::array<double, 3> direction = {};
    // The horizontal direction as one of 24 steps of 15 degrees from east, counter-clockwise; -1 straight up or down.
    int azimuth = -1;
    // 0 level, 1 upward, -1 downward, 2 straight up, -2 straight down.
    int pitch = 0;
};

// 24 level rays, 12 at 35 degrees up, 12 at 35 degrees down, one up, one down. The level ones are turned half a
// degree off the axes, so a ray from a grid point does not run along the seam of two walls.
const std::vector<RayDirection> &rayDirections()
{
    static const std::vector<RayDirection> directions = []()
    {
        std::vector<RayDirection> list;
        const double offset = 0.5 * Pi / 180.0;

        for (int index = 0; index < 24; ++index)
        {
            const double angle = index * Pi / 12.0 + offset;
            list.push_back({{oy::cos(angle), oy::sin(angle), 0.0}, index, 0});
        }

        for (const int pitch : {1, -1})
        {
            const double tilt = pitch * 35.0 * Pi / 180.0;

            for (int index = 0; index < 12; ++index)
            {
                const double angle = index * Pi / 6.0 + offset;
                list.push_back({{oy::cos(angle) * oy::cos(tilt), oy::sin(angle) * oy::cos(tilt), oy::sin(tilt)},
                    index * 2, pitch});
            }
        }

        list.push_back({{0.0, 0.0, 1.0}, -1, 2});
        list.push_back({{0.0, 0.0, -1.0}, -1, -2});
        return list;
    }();
    return directions;
}

const char *compassName(int octant)
{
    static const char *const names[] = {"east", "north-east", "north", "north-west", "west", "south-west", "south",
        "south-east"};
    return names[static_cast<size_t>(((octant % 8) + 8) % 8)];
}

bool distancesAgree(double original, double rebuilt)
{
    return std::fabs(original - rebuilt) <= std::max(64.0, 0.12 * original);
}

struct SentencePart
{
    double weight = 0.0;
    std::string text;
};

// What differs at one point, the largest differences first; nothing where the maps agree.
std::vector<std::string> describePoint(
    const ComparePoint &point,
    const std::vector<RayHit> &originalHits,
    const std::vector<RayHit> &rebuiltHits,
    const std::vector<std::optional<std::array<double, 2>>> &offsets)
{
    const std::vector<RayDirection> &directions = rayDirections();
    std::vector<SentencePart> parts;

    if (std::fabs(point.floorDelta) >= 16.0)
    {
        parts.push_back({std::fabs(point.floorDelta) * 2.0, "the floor is " + wholeNumber(std::fabs(point.floorDelta))
            + (point.floorDelta > 0.0 ? " higher" : " lower")});
    }

    const RayHit &originalUp = originalHits[directions.size() - 2];
    const RayHit &rebuiltUp = rebuiltHits[directions.size() - 2];

    if (point.hasCeilingDelta && std::fabs(point.ceilingDelta) >= 32.0)
    {
        parts.push_back({std::fabs(point.ceilingDelta), "the ceiling is " + wholeNumber(std::fabs(point.ceilingDelta))
            + (point.ceilingDelta > 0.0 ? " higher" : " lower")});
    }
    else if (originalUp.hit != rebuiltUp.hit)
    {
        parts.push_back({1024.0, originalUp.hit
            ? "the rebuild has nothing overhead within 4096 (the original's ceiling is "
                + wholeNumber(originalUp.distance + EyeHeight) + " above the floor)"
            : "the rebuild has a ceiling " + wholeNumber(rebuiltUp.distance + EyeHeight)
                + " above the floor where the original has nothing within 4096"});
    }

    // Distances: the rays of one compass direction together, level, upward and downward apart.
    struct Group
    {
        size_t rays = 0;
        size_t differing = 0;
        double sum = 0.0;
        size_t rebuiltMisses = 0;
        size_t originalMisses = 0;
        double originalDistance = 0.0;
        double rebuiltDistance = 0.0;
        std::map<SurfaceKind, size_t> kinds;
    };
    std::map<std::pair<int, int>, Group> groups;
    // Textures: rays whose distances agree, by surface and pair of names; and on one texture, by the offset the
    // rebuild's picture needs.
    std::map<std::tuple<SurfaceKind, std::string, std::string>, std::set<int>> texturePairs;
    std::map<std::tuple<SurfaceKind, std::string, double, double>, std::set<int>> offsetPairs;

    for (size_t index = 0; index < directions.size(); ++index)
    {
        const RayDirection &ray = directions[index];
        const RayHit &original = originalHits[index];
        const RayHit &rebuilt = rebuiltHits[index];
        const bool agree = distancesAgree(original.distance, rebuilt.distance);

        if (agree)
        {
            // Level rays by octant; the others under one direction of their own.
            const int where = ray.pitch == 0 ? ((ray.azimuth + 1) / 3) % 8 : 8;

            if (original.hit && rebuilt.hit && original.texture != rebuilt.texture)
            {
                texturePairs[{original.kind, original.texture, rebuilt.texture}].insert(where);
            }
            else if (index < offsets.size() && offsets[index])
            {
                offsetPairs[{original.kind, original.texture, (*offsets[index])[0], (*offsets[index])[1]}].insert(
                    where);
            }
        }

        if (ray.azimuth < 0)
        {
            continue;
        }

        // Octants for the 24 level rays (three each), quarters for the 12 tilted ones (three each).
        const int where = ray.pitch == 0 ? ((ray.azimuth + 1) / 3) % 8 : (((ray.azimuth + 2) / 6) % 4) * 2;
        Group &group = groups[{ray.pitch, where}];
        ++group.rays;

        if (agree)
        {
            continue;
        }

        ++group.differing;
        group.sum += rebuilt.distance - original.distance;
        group.rebuiltMisses += rebuilt.hit ? 0 : 1;
        group.originalMisses += original.hit ? 0 : 1;
        group.originalDistance += original.distance;
        group.rebuiltDistance += rebuilt.distance;
        // The surface that stands nearer is the one the sentence names.
        ++group.kinds[rebuilt.distance < original.distance ? rebuilt.kind : original.kind];
    }

    for (const std::pair<const std::pair<int, int>, Group> &entry : groups)
    {
        const Group &group = entry.second;

        if (group.differing * 3 < group.rays * 2)
        {
            continue;
        }

        const double mean = group.sum / static_cast<double>(group.differing);
        const std::string compass = compassName(entry.first.second);
        const std::string where = entry.first.first == 0 ? "to the " + compass
            : entry.first.first > 0 ? "up to the " + compass : "down to the " + compass;
        SurfaceKind kind = SurfaceKind::Wall;
        size_t most = 0;

        for (const std::pair<const SurfaceKind, size_t> &counted : group.kinds)
        {
            if (counted.second > most && counted.first != SurfaceKind::None)
            {
                most = counted.second;
                kind = counted.first;
            }
        }

        std::string text;

        if (group.rebuiltMisses == group.differing)
        {
            text = "the rebuild has nothing within 4096 " + where + " (the original's " + surfaceKindName(kind)
                + " is at " + wholeNumber(group.originalDistance / static_cast<double>(group.differing)) + ")";
        }
        else if (group.originalMisses == group.differing)
        {
            text = "the rebuild has a " + std::string(surfaceKindName(kind)) + " " + where + " at "
                + wholeNumber(group.rebuiltDistance / static_cast<double>(group.differing))
                + " where the original has nothing within 4096";
        }
        else if (mean < 0.0)
        {
            text = "the rebuild's " + std::string(surfaceKindName(kind)) + " " + where + " is "
                + wholeNumber(-mean) + " nearer";
        }
        else
        {
            text = "the rebuild is open " + wholeNumber(mean) + " farther " + where + " than the original's "
                + surfaceKindName(kind);
        }

        // Level rays are what a person looks at first.
        parts.push_back({std::fabs(mean) * (entry.first.first == 0 ? 1.0 : 0.6), text});
    }

    for (const std::pair<const std::tuple<SurfaceKind, std::string, std::string>, std::set<int>> &entry :
         texturePairs)
    {
        std::string where;

        for (const int octant : entry.second)
        {
            if (octant < 8)
            {
                where += (where.empty() ? "" : ", ") + std::string(compassName(octant));
            }
        }

        const std::string kind = surfaceKindName(std::get<0>(entry.first));
        parts.push_back({60.0 + 10.0 * static_cast<double>(entry.second.size()),
            (where.empty() ? kind : where + " " + kind) + ": " + std::get<1>(entry.first) + " against "
                + std::get<2>(entry.first)});
    }

    // A picture at another phase weighs less than another picture.
    for (const std::pair<const std::tuple<SurfaceKind, std::string, double, double>, std::set<int>> &entry :
         offsetPairs)
    {
        std::string where;

        for (const int octant : entry.second)
        {
            if (octant < 8)
            {
                where += (where.empty() ? "" : ", ") + std::string(compassName(octant));
            }
        }

        const std::string kind = surfaceKindName(std::get<0>(entry.first));
        parts.push_back({30.0 + 5.0 * static_cast<double>(entry.second.size()),
            (where.empty() ? kind : where + " " + kind) + ": " + std::get<1>(entry.first) + " offset by ["
                + wholeNumber(std::get<2>(entry.first)) + ", " + wholeNumber(std::get<3>(entry.first)) + "]"});
    }

    std::stable_sort(parts.begin(), parts.end(), [](const SentencePart &left, const SentencePart &right)
    {
        return left.weight > right.weight;
    });
    std::vector<std::string> texts;

    for (const SentencePart &part : parts)
    {
        texts.push_back(part.text);
    }

    return texts;
}

// Where to look: the level direction with the most of what differs within a view of about 75 degrees.
double worstYawOf(const std::vector<RayHit> &originalHits, const std::vector<RayHit> &rebuiltHits)
{
    const std::vector<RayDirection> &directions = rayDirections();
    std::array<double, 24> weight = {};

    for (size_t index = 0; index < directions.size(); ++index)
    {
        const RayDirection &ray = directions[index];

        if (ray.azimuth < 0)
        {
            continue;
        }

        const double difference = std::fabs(originalHits[index].distance - rebuiltHits[index].distance);

        if (!distancesAgree(originalHits[index].distance, rebuiltHits[index].distance))
        {
            weight[static_cast<size_t>(ray.azimuth)] += 0.5 + std::min(difference, 1024.0) / 1024.0;
        }
        else if (originalHits[index].texture != rebuiltHits[index].texture)
        {
            weight[static_cast<size_t>(ray.azimuth)] += 0.25;
        }
    }

    int best = 0;
    double bestWeight = -1.0;

    for (int index = 0; index < 24; ++index)
    {
        double sum = 0.0;

        for (int offset = -2; offset <= 2; ++offset)
        {
            sum += weight[static_cast<size_t>((index + offset + 24) % 24)] * (offset == 0 ? 1.5 : 1.0);
        }

        if (sum > bestWeight + 1.0e-9)
        {
            bestWeight = sum;
            best = index;
        }
    }

    return best * Pi / 12.0;
}

// To a number of decimals, as the nearest double of that decimal (so it prints short).
double rounded(double value, int decimals)
{
    const double scale = oy::pow(10.0, decimals);
    return std::round(value * scale) / scale;
}

// The height the whole rebuild lies above (or, negative, below) the original: the commonest difference between a
// floor of the original and a floor of the rebuild over the same point. Nothing unless it is clearly commoner
// than no difference at all.
double estimateVerticalOffset(const PreparedMap &original, const PreparedMap &rebuilt)
{
    constexpr double Bin = 16.0;
    std::map<long long, size_t> bins;
    std::vector<double> deltas;

    for (const StandPoint &stand : original.points)
    {
        for (const std::pair<double, int32_t> &entry : rebuilt.floors.heightsAt(stand.x, stand.y, rebuilt.floorEdges))
        {
            const double delta = entry.first - stand.z;

            if (std::fabs(delta) <= 2048.0)
            {
                ++bins[std::llround(delta / Bin)];
                deltas.push_back(delta);
            }
        }
    }

    const auto support = [&bins](long long bin)
    {
        size_t count = 0;

        for (long long near = bin - 1; near <= bin + 1; ++near)
        {
            const std::map<long long, size_t>::const_iterator found = bins.find(near);
            count += found == bins.end() ? 0 : found->second;
        }

        return count;
    };
    long long best = 0;
    size_t bestSupport = support(0);

    for (const std::pair<const long long, size_t> &entry : bins)
    {
        // Clearly commoner: by a quarter.
        if (support(entry.first) * 4 > bestSupport * 5 && support(entry.first) > support(best))
        {
            best = entry.first;
        }
    }

    if (best == 0 || best == 1 || best == -1)
    {
        return 0.0;
    }

    std::vector<double> near;

    for (const double delta : deltas)
    {
        if (std::fabs(delta - static_cast<double>(best) * Bin) <= 1.5 * Bin)
        {
            near.push_back(delta);
        }
    }

    std::sort(near.begin(), near.end());
    return near.empty() ? 0.0 : std::round(near[near.size() / 2]);
}
}

bool compareMaps(
    const LoadedMap &original,
    const LoadedMap &rebuilt,
    const CompareOptions &options,
    CompareResult &result,
    std::string &errorMessage)
{
    result = {};
    result.originalName = original.fileName;
    result.rebuiltName = rebuilt.fileName;
    result.step = std::max(WalkStep, std::round(options.step / WalkStep) * WalkStep);
    PreparedMap first;
    PreparedMap second;

    if (!prepareMap(original, options, first, errorMessage) || !prepareMap(rebuilt, options, second, errorMessage))
    {
        return false;
    }

    if (first.points.empty())
    {
        errorMessage = original.fileName + " has no floor to stand on";
        return false;
    }

    result.verticalOffset = estimateVerticalOffset(first, second);
    result.originalFaces = first.seen.faceCount();
    result.rebuiltFaces = second.seen.faceCount();
    result.rebuiltPoints = second.points.size();
    const std::vector<RayDirection> &directions = rayDirections();
    std::vector<RayHit> originalHits(directions.size());
    std::vector<RayHit> rebuiltHits(directions.size());
    std::map<std::tuple<std::string, std::string, SurfaceKind>, size_t> pairRays;
    std::map<std::tuple<std::string, SurfaceKind, double, double>, size_t> offsetRays;
    std::vector<std::optional<std::array<double, 2>>> rayOffsets(directions.size());
    std::map<int, CompareSector> sectors;
    std::map<int, std::array<size_t, 3>> sectorCounts;
    size_t agreeing = 0;
    double sameTexture = 0.0;
    double sameTextureWhereSeen = 0.0;
    size_t withFloor = 0;
    size_t withCeiling = 0;
    double errorSum = 0.0;

    for (const StandPoint &stand : first.points)
    {
        ComparePoint point;
        point.x = stand.x;
        point.y = stand.y;
        point.z = stand.z;

        if (stand.face >= 0 && static_cast<size_t>(stand.face) < original.indoor->faces.size())
        {
            point.sector = original.indoor->faces[static_cast<size_t>(stand.face)].roomNumber;
        }

        CompareSector &sector = sectors[point.sector];
        sector.sector = point.sector;
        ++sector.points;
        bool inWall = false;
        point.hasFloor =
            nearestFloor(second, point.x, point.y, point.z + result.verticalOffset, point.rebuiltZ, &inWall);
        point.onEdge = stand.onEdge && !stand.moved;
        result.movedPoints += stand.moved ? 1 : 0;
        result.edgePoints += point.onEdge ? 1 : 0;

        if (!point.hasFloor)
        {
            point.sentence = inWall ? "the rebuild has a wall through this place, where the original has floor to "
                                      "stand on"
                : "the rebuild has no floor where the original has one";
            point.differences = {point.sentence};
            ++sector.missingFloor;
            result.missingFloor.push_back(result.points.size());
            result.points.push_back(point);
            continue;
        }

        point.floorDelta = point.rebuiltZ - point.z - result.verticalOffset;
        const std::array<double, 3> originalEye = {point.x, point.y, point.z + EyeHeight};
        const std::array<double, 3> rebuiltEye = {point.x, point.y, point.rebuiltZ + EyeHeight};
        size_t agree = 0;
        double textures = 0.0;
        double texturesWhereSeen = 0.0;
        double errors = 0.0;

        for (size_t index = 0; index < directions.size(); ++index)
        {
            originalHits[index] = first.seen.cast(originalEye, directions[index].direction, RayCap);
            rebuiltHits[index] = second.seen.cast(rebuiltEye, directions[index].direction, RayCap);
            const RayHit &originalHit = originalHits[index];
            const RayHit &rebuiltHit = rebuiltHits[index];
            const bool same = originalHit.texture == rebuiltHit.texture;
            // One texture at another phase: the offset the rebuild needs there (half a texture's worth).
            rayOffsets[index].reset();

            if (same && originalHit.hit && originalHit.hasTexel && rebuiltHit.hasTexel)
            {
                const std::map<std::string, std::array<int, 2>>::const_iterator size =
                    options.textureSizes.find(originalHit.texture);

                if (size != options.textureSizes.end())
                {
                    rayOffsets[index] = offsetNeeded(originalHit.texel, rebuiltHit.texel, size->second);
                }
            }

            const double weight = !same ? 0.0 : rayOffsets[index] && !options.ignoreOffsets ? 0.5 : 1.0;
            textures += weight;

            if (distancesAgree(originalHit.distance, rebuiltHit.distance))
            {
                ++agree;
                texturesWhereSeen += weight;

                if (!same && originalHit.hit && rebuiltHit.hit)
                {
                    ++pairRays[{originalHit.texture, rebuiltHit.texture, originalHit.kind}];
                }

                if (same && originalHit.hit)
                {
                    ++result.sameTextureRays;
                }

                if (rayOffsets[index])
                {
                    ++result.offsetRays;
                    ++offsetRays[{originalHit.texture, originalHit.kind, std::round((*rayOffsets[index])[0] / 8.0)
                        * 8.0, std::round((*rayOffsets[index])[1] / 8.0) * 8.0}];
                }
            }
            else
            {
                errors += std::fabs(originalHits[index].distance - rebuiltHits[index].distance);
            }
        }

        const size_t count = directions.size();
        point.distanceShare = static_cast<double>(agree) / static_cast<double>(count);
        point.meanError = agree == count ? 0.0 : errors / static_cast<double>(count - agree);
        point.textureShare = textures / static_cast<double>(count);
        const RayHit &originalUp = originalHits[count - 2];
        const RayHit &rebuiltUp = rebuiltHits[count - 2];

        if (originalUp.hit && rebuiltUp.hit)
        {
            point.hasCeilingDelta = true;
            point.ceilingDelta = (point.rebuiltZ + rebuiltUp.distance) - (point.z + originalUp.distance)
                - result.verticalOffset;
        }

        point.score = 0.7 * point.distanceShare + 0.3 * point.textureShare;
        point.worstYaw = worstYawOf(originalHits, rebuiltHits);
        point.differences = describePoint(point, originalHits, rebuiltHits, rayOffsets);

        for (size_t index = 0; index < point.differences.size() && index < 4; ++index)
        {
            point.sentence += (index == 0 ? "" : "; ") + point.differences[index];
        }

        if (point.differences.empty())
        {
            point.sentence = "agrees";
        }
        ++withFloor;
        agreeing += agree;
        sameTexture += textures;
        sameTextureWhereSeen += texturesWhereSeen;
        errorSum += errors;
        result.meanFloorDelta += std::fabs(point.floorDelta);
        sector.distanceShare += point.distanceShare;
        sector.textureShare += point.textureShare;
        sector.meanError += errors;
        sector.meanFloorDelta += std::fabs(point.floorDelta);
        sector.score += point.score;
        std::array<size_t, 3> &counts = sectorCounts[point.sector];
        counts[0] += count - agree;

        if (point.hasCeilingDelta)
        {
            ++withCeiling;
            ++counts[1];
            result.meanCeilingDelta += std::fabs(point.ceilingDelta);
            sector.meanCeilingDelta += std::fabs(point.ceilingDelta);
        }

        result.points.push_back(point);
    }

    result.rays = withFloor * directions.size();

    if (withFloor > 0)
    {
        const double rays = static_cast<double>(result.rays);
        result.distanceShare = static_cast<double>(agreeing) / rays;
        result.meanError = result.rays == agreeing ? 0.0 : errorSum / static_cast<double>(result.rays - agreeing);
        result.textureShare = sameTexture / rays;
        result.textureShareWhereSeen =
            agreeing == 0 ? 0.0 : sameTextureWhereSeen / static_cast<double>(agreeing);
        result.meanFloorDelta /= static_cast<double>(withFloor);
        result.meanCeilingDelta = withCeiling == 0 ? 0.0 : result.meanCeilingDelta / static_cast<double>(withCeiling);
        // A point without a floor in the rebuild scores nothing.
        result.score = (0.7 * result.distanceShare + 0.3 * result.textureShare) * static_cast<double>(withFloor)
            / static_cast<double>(result.points.size());
    }

    for (std::pair<const int, CompareSector> &entry : sectors)
    {
        CompareSector &sector = entry.second;
        const size_t standing = sector.points - sector.missingFloor;

        if (standing > 0)
        {
            const std::array<size_t, 3> &counts = sectorCounts[entry.first];
            sector.distanceShare /= static_cast<double>(standing);
            sector.textureShare /= static_cast<double>(standing);
            sector.meanError = counts[0] == 0 ? 0.0 : sector.meanError / static_cast<double>(counts[0]);
            sector.meanFloorDelta /= static_cast<double>(standing);
            sector.meanCeilingDelta = counts[1] == 0 ? 0.0 : sector.meanCeilingDelta / static_cast<double>(counts[1]);
            sector.score /= static_cast<double>(sector.points);
        }

        result.sectors.push_back(sector);
    }

    for (size_t index = 0; index < result.points.size(); ++index)
    {
        if (result.points[index].hasFloor)
        {
            result.worst.push_back(index);
        }
    }

    std::stable_sort(result.worst.begin(), result.worst.end(), [&result](size_t left, size_t right)
    {
        const ComparePoint &leftPoint = result.points[left];
        const ComparePoint &rightPoint = result.points[right];
        return std::tie(leftPoint.score, rightPoint.meanError) < std::tie(rightPoint.score, leftPoint.meanError);
    });

    for (const std::pair<const std::tuple<std::string, std::string, SurfaceKind>, size_t> &entry : pairRays)
    {
        result.texturePairs.push_back(
            {std::get<0>(entry.first), std::get<1>(entry.first), std::get<2>(entry.first), entry.second});
    }

    std::stable_sort(result.texturePairs.begin(), result.texturePairs.end(),
        [](const CompareTexturePair &left, const CompareTexturePair &right)
    {
        return left.rays > right.rays;
    });

    for (const std::pair<const std::tuple<std::string, SurfaceKind, double, double>, size_t> &entry : offsetRays)
    {
        result.offsets.push_back({std::get<0>(entry.first), std::get<1>(entry.first),
            {std::get<2>(entry.first), std::get<3>(entry.first)}, entry.second});
    }

    std::stable_sort(result.offsets.begin(), result.offsets.end(),
        [](const CompareOffset &left, const CompareOffset &right)
    {
        return left.rays > right.rays;
    });

    // The other way round: where the rebuild lets the party stand and the original has no floor.
    for (const StandPoint &stand : second.points)
    {
        double height = 0.0;

        if (!nearestFloor(first, stand.x, stand.y, stand.z - result.verticalOffset, height))
        {
            result.extraFloor.push_back({stand.x, stand.y, stand.z});
        }
    }

    return true;
}

std::vector<size_t> compareShotPoints(const CompareResult &result)
{
    std::vector<size_t> shots;

    for (const size_t index : result.worst)
    {
        const ComparePoint &point = result.points[index];
        bool apart = true;

        for (const size_t taken : shots)
        {
            const ComparePoint &other = result.points[taken];
            const double distance = std::sqrt((point.x - other.x) * (point.x - other.x)
                + (point.y - other.y) * (point.y - other.y) + (point.z - other.z) * (point.z - other.z));
            apart = apart && distance >= ShotSpacing;
        }

        if (apart)
        {
            shots.push_back(index);
        }

        if (shots.size() == ShotCount)
        {
            break;
        }
    }

    return shots;
}

std::string compareShotsYaml(const CompareResult &result)
{
    // Written by hand: a flat list of scalars, the same on every platform.
    std::string text = "# The worst points of `oymap compare " + result.originalName + " --with " + result.rebuiltName
        + "`, for calibration/ingame_compare.py.\n# at: x, y and the original's floor height; yaw in radians, 0 east, "
          "counter-clockwise;\n# rebuilt_z: the rebuild's floor height there.\nshots:\n";
    size_t number = 0;

    for (const size_t index : compareShotPoints(result))
    {
        const ComparePoint &point = result.points[index];
        ++number;
        text += "  - {name: worst" + std::string(number < 10 ? "0" : "") + std::to_string(number) + "-s"
            + std::to_string(point.sector) + ", at: [" + wholeNumber(point.x) + ", " + wholeNumber(point.y) + ", "
            + wholeNumber(point.z) + "], rebuilt_z: " + wholeNumber(point.rebuiltZ) + ", yaw: "
            + formatNumber(rounded(point.worstYaw, 4)) + ", score: " + formatNumber(rounded(point.score, 3))
            + "}\n";
    }

    return text;
}

namespace
{
void writePoint(const ComparePoint &point, JsonWriter &writer)
{
    writer.beginObject();
    writer.key("at");
    writer.beginArray();
    writer.value(rounded(point.x, 0));
    writer.value(rounded(point.y, 0));
    writer.value(rounded(point.z, 0));
    writer.endArray();
    writer.field("sector", point.sector);
    writer.field("score", rounded(point.score, 3));
    writer.field("distance_agreement", rounded(point.distanceShare, 3));
    writer.field("mean_distance_error", rounded(point.meanError, 0));
    writer.field("texture_agreement", rounded(point.textureShare, 3));
    writer.field("floor_difference", rounded(point.floorDelta, 0));

    if (point.hasCeilingDelta)
    {
        writer.field("ceiling_difference", rounded(point.ceilingDelta, 0));
    }

    writer.field("look_yaw", rounded(point.worstYaw, 4));
    writer.field("differs", point.sentence);
    writer.endObject();
}
}

void writeComparePointsJson(const CompareResult &result, JsonWriter &writer)
{
    // By sector, the worst first; a point without a floor in the rebuild is the worst there is.
    std::map<int, std::vector<size_t>> bySector;
    size_t differing = 0;

    for (size_t index = 0; index < result.points.size(); ++index)
    {
        const ComparePoint &point = result.points[index];

        if (!point.hasFloor || !point.differences.empty())
        {
            bySector[point.sector].push_back(index);
            ++differing;
        }
    }

    writer.beginObject();
    writer.field("original", result.originalName);
    writer.field("rebuilt", result.rebuiltName);
    writer.field("step", result.step);
    writer.field("vertical_offset", result.verticalOffset);
    writer.field("points", static_cast<uint64_t>(result.points.size()));
    writer.field("differing_points", static_cast<uint64_t>(differing));
    writer.field("points_moved_clear_of_edges", static_cast<uint64_t>(result.movedPoints));
    writer.field("points_left_on_edges", static_cast<uint64_t>(result.edgePoints));
    writer.field("about", "every stand point of the original at which the rebuild differs, by sector, the worst first. "
        "at: x, y and the original's floor height; rebuilt_floor: the rebuild's floor height there; differences are "
        "the rebuild minus the original; differs: everything that differs, the largest first; on_edge: no place "
        "near the point stands clear of floor edges and walls, so its reading is less sure");
    writer.key("sectors");
    writer.beginArray();

    for (const CompareSector &sector : result.sectors)
    {
        std::vector<size_t> indices = bySector[sector.sector];
        std::stable_sort(indices.begin(), indices.end(), [&result](size_t left, size_t right)
        {
            const ComparePoint &leftPoint = result.points[left];
            const ComparePoint &rightPoint = result.points[right];
            return std::tie(leftPoint.hasFloor, leftPoint.score, rightPoint.meanError)
                < std::tie(rightPoint.hasFloor, rightPoint.score, leftPoint.meanError);
        });
        writer.beginObject();
        writer.field("sector", sector.sector);
        writer.field("points", static_cast<uint64_t>(sector.points));
        writer.field("differing_points", static_cast<uint64_t>(indices.size()));
        writer.field("without_floor", static_cast<uint64_t>(sector.missingFloor));
        writer.field("score", rounded(sector.score, 3));
        writer.key("differing");
        writer.beginArray();

        for (const size_t index : indices)
        {
            const ComparePoint &point = result.points[index];
            writer.beginObject();
            writer.key("at");
            writer.beginArray();
            writer.value(rounded(point.x, 0));
            writer.value(rounded(point.y, 0));
            writer.value(rounded(point.z, 0));
            writer.endArray();

            if (point.onEdge)
            {
                writer.field("on_edge", true);
            }

            if (!point.hasFloor)
            {
                writer.field("floor", "missing in the rebuild");
                writer.field("score", 0.0);
            }
            else
            {
                writer.field("rebuilt_floor", rounded(point.rebuiltZ, 0));
                writer.field("score", rounded(point.score, 3));
                writer.field("distance_agreement", rounded(point.distanceShare, 3));
                writer.field("mean_distance_error", rounded(point.meanError, 0));
                writer.field("texture_agreement", rounded(point.textureShare, 3));
                writer.field("floor_difference", rounded(point.floorDelta, 0));

                if (point.hasCeilingDelta)
                {
                    writer.field("ceiling_difference", rounded(point.ceilingDelta, 0));
                }

                writer.field("look_yaw", rounded(point.worstYaw, 4));
            }

            writer.key("differs");
            writer.beginArray();

            for (const std::string &difference : point.differences)
            {
                writer.value(difference);
            }

            writer.endArray();
            writer.endObject();
        }

        writer.endArray();
        writer.endObject();
    }

    writer.endArray();
    writer.key("floor_only_in_rebuild");
    writer.beginArray();

    for (const std::array<double, 3> &extra : result.extraFloor)
    {
        writer.beginArray();
        writer.value(rounded(extra[0], 0));
        writer.value(rounded(extra[1], 0));
        writer.value(rounded(extra[2], 0));
        writer.endArray();
    }

    writer.endArray();
    writer.endObject();
}

void writeCompareJson(const CompareResult &result, JsonWriter &writer)
{
    writer.beginObject();
    writer.field("original", result.originalName);
    writer.field("rebuilt", result.rebuiltName);
    writer.key("method");
    writer.beginObject();
    writer.field("step", result.step);
    writer.field("eye_height", EyeHeight);
    writer.field("rays_per_point", static_cast<uint64_t>(rayDirections().size()));
    writer.field("ray_cap", RayCap);
    writer.field("distances_agree", "within 64 units or 12 % of the original's distance, whichever is larger");
    writer.field("score", "0.7 of the distance agreement and 0.3 of the texture agreement; differences are the "
        "rebuild minus the original, after the vertical offset; texture pairs are the original's name against "
        "the rebuild's");
    writer.endObject();
    writer.key("totals");
    writer.beginObject();
    writer.field("score", rounded(result.score, 3));
    writer.field("vertical_offset", result.verticalOffset);
    writer.field("points", static_cast<uint64_t>(result.points.size()));
    writer.field("points_without_floor_in_rebuild", static_cast<uint64_t>(result.missingFloor.size()));
    writer.field("rebuild_points", static_cast<uint64_t>(result.rebuiltPoints));
    writer.field("rebuild_points_without_floor_in_original", static_cast<uint64_t>(result.extraFloor.size()));
    writer.field("rays", static_cast<uint64_t>(result.rays));
    writer.field("distance_agreement", rounded(result.distanceShare, 3));
    writer.field("mean_distance_error_of_others", rounded(result.meanError, 0));
    writer.field("texture_agreement", rounded(result.textureShare, 3));
    writer.field("texture_agreement_where_distances_agree", rounded(result.textureShareWhereSeen, 3));
    // Of the rays on the same texture in both maps (distances agreeing), the share whose pictures lie alike.
    writer.field("offset_agreement", rounded(result.sameTextureRays == 0 ? 1.0
        : 1.0 - static_cast<double>(result.offsetRays) / static_cast<double>(result.sameTextureRays), 3));
    writer.field("mean_floor_difference", rounded(result.meanFloorDelta, 1));
    writer.field("mean_ceiling_difference", rounded(result.meanCeilingDelta, 1));
    writer.field("original_faces", static_cast<uint64_t>(result.originalFaces));
    writer.field("rebuilt_faces", static_cast<uint64_t>(result.rebuiltFaces));
    writer.endObject();
    writer.key("notes");
    writer.beginArray();

    if (result.verticalOffset != 0.0)
    {
        writer.value("the whole rebuild lies " + wholeNumber(std::fabs(result.verticalOffset))
            + (result.verticalOffset > 0.0 ? " higher" : " lower")
            + " than the original; floors are matched and floor and ceiling differences given with that taken out");
    }

    writer.endArray();
    writer.key("sectors");
    writer.beginArray();

    for (const CompareSector &sector : result.sectors)
    {
        writer.beginObject();
        writer.field("sector", sector.sector);
        writer.field("points", static_cast<uint64_t>(sector.points));
        writer.field("without_floor", static_cast<uint64_t>(sector.missingFloor));
        writer.field("score", rounded(sector.score, 3));
        writer.field("distance_agreement", rounded(sector.distanceShare, 3));
        writer.field("mean_distance_error", rounded(sector.meanError, 0));
        writer.field("texture_agreement", rounded(sector.textureShare, 3));
        writer.field("mean_floor_difference", rounded(sector.meanFloorDelta, 1));
        writer.field("mean_ceiling_difference", rounded(sector.meanCeilingDelta, 1));
        writer.endObject();
    }

    writer.endArray();
    writer.key("worst_points");
    writer.beginArray();

    for (size_t index = 0; index < result.worst.size() && index < WorstPointCount; ++index)
    {
        writePoint(result.points[result.worst[index]], writer);
    }

    writer.endArray();
    writer.key("texture_pairs");
    writer.beginArray();

    for (size_t index = 0; index < result.texturePairs.size() && index < 30; ++index)
    {
        const CompareTexturePair &pair = result.texturePairs[index];
        writer.beginObject();
        writer.field("original", pair.original);
        writer.field("rebuilt", pair.rebuilt);
        writer.field("surface", surfaceKindName(pair.kind));
        writer.field("rays", static_cast<uint64_t>(pair.rays));
        writer.endObject();
    }

    writer.endArray();
    // Rays on one texture whose pictures lie apart: the offset the rebuild's surface needs (to 8 texels).
    writer.key("offsets");
    writer.beginArray();

    for (size_t index = 0; index < result.offsets.size() && index < 30; ++index)
    {
        const CompareOffset &offset = result.offsets[index];
        writer.beginObject();
        writer.field("texture", offset.texture);
        writer.field("surface", surfaceKindName(offset.kind));
        writer.key("offset");
        writer.beginArray();
        writer.value(static_cast<int64_t>(std::llround(offset.offset[0])));
        writer.value(static_cast<int64_t>(std::llround(offset.offset[1])));
        writer.endArray();
        writer.field("rays", static_cast<uint64_t>(offset.rays));
        writer.endObject();
    }

    writer.endArray();
    writer.key("floor_missing_in_rebuild");
    writer.beginArray();

    for (size_t index = 0; index < result.missingFloor.size() && index < ListedFloorPoints; ++index)
    {
        const ComparePoint &point = result.points[result.missingFloor[index]];
        writer.beginObject();
        writer.key("at");
        writer.beginArray();
        writer.value(rounded(point.x, 0));
        writer.value(rounded(point.y, 0));
        writer.value(rounded(point.z, 0));
        writer.endArray();
        writer.field("sector", point.sector);
        writer.endObject();
    }

    writer.endArray();
    writer.key("floor_only_in_rebuild");
    writer.beginArray();

    for (size_t index = 0; index < result.extraFloor.size() && index < ListedFloorPoints; ++index)
    {
        writer.beginArray();
        writer.value(rounded(result.extraFloor[index][0], 0));
        writer.value(rounded(result.extraFloor[index][1], 0));
        writer.value(rounded(result.extraFloor[index][2], 0));
        writer.endArray();
    }

    writer.endArray();
    writer.endObject();
}
}
