#include "core/Reachability.h"

#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorPathfindingBuilder.h"
#include "game/pathfinding/PathPlanner.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cstdio>
#include <limits>
#include <map>
#include <array>
#include <bit>
#include <cmath>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Studio
{
namespace
{
// The party's body, as the scenario walker plans with it (game/scenario/ScenarioRuntimeDriver.cpp).
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

// What a walk is taken over. `pAll`: every face that can be stood on or stands in the way. Doors that are out of the
// way have their floors in it in both of their poses (a lift up and down, a bridge slid out and back), and
// `pMovingFloors` names those faces; `pSolid` is the same map without them: what is left when such a floor has
// moved away (null: the same as `pAll`).
struct WalkMaps
{
    const Game::PathMap *pAll = nullptr;
    const Game::PathMap *pSolid = nullptr;
    const std::set<int32_t> *pMovingFloors = nullptr;

    const Game::PathMap &solid() const
    {
        return pSolid != nullptr ? *pSolid : *pAll;
    }
};

// A grid cell the walk stood on, and the face of its floor.
struct WalkCell
{
    Game::PathPoint point;
    int32_t face = -1;
};

// How the game's party meets a gap between two floors, from its movement code (game/indoor/
// IndoorMovementController.cpp and IndoorPartyRuntime.cpp, read on 2026-11-12; none of it measured in the game):
// - The floor is the one under the body's centre. Past an edge the party falls (gravity 1280) and keeps its speed
//   across; it gets onto the far floor while its feet have dropped less than MaximumRise (50), and its body reaches
//   that floor's edge a radius (37) before its centre does. At a walk (384 a second) that is a gap of
//   384 * sqrt(2 * 50 / 1280) + 37 = 144; running (768, the default, and the scenario walker's walk_to) about 250.
//   The walk here crosses what is crossed at a walk.
// - It falls into a gap only where its body fits: its lower sphere rests on the edges of a gap narrower than the
//   body is wide (74).
constexpr float WidestGapCrossed = 144.0f;

// Whether a floor lies at the height walked on (`z`, within a step either way) at a place.
bool supportAt(const Game::PathMap &solid, float x, float y, float z, const Game::PathObject &body, float &height)
{
    const Game::PathFloorSample floor = solid.floorAt({x, y, z + body.stepHeight});

    if (!floor.hasFloor || floor.inVoid || z - floor.z > body.stepHeight)
    {
        return false;
    }

    height = floor.z;
    return true;
}

// Whether a place lies in a gap narrower than the body: floors at the height walked on lie on two opposite sides
// of it, less than the body's width apart (a grating's slots, the slot between a balcony and a bridge's end). The
// party does not fall into such a gap.
bool overNarrowGap(const Game::PathMap &solid, float x, float y, float z, const Game::PathObject &body)
{
    constexpr float Sample = 4.0f;
    const float width = 2.0f * body.radius;
    static const std::array<std::array<float, 2>, 4> axes = {{
        {1.0f, 0.0f}, {0.0f, 1.0f}, {0.70710678f, 0.70710678f}, {0.70710678f, -0.70710678f}}};

    for (const std::array<float, 2> &axis : axes)
    {
        float ahead = 0.0f;
        float height = 0.0f;
        bool foundAhead = false;

        for (float distance = Sample; distance <= width && !foundAhead; distance += Sample)
        {
            foundAhead = supportAt(solid, x + axis[0] * distance, y + axis[1] * distance, z, body, height);
            ahead = distance;
        }

        if (!foundAhead)
        {
            continue;
        }

        for (float distance = Sample; distance + ahead <= width + Sample; distance += Sample)
        {
            if (supportAt(solid, x - axis[0] * distance, y - axis[1] * distance, z, body, height))
            {
                return true;
            }
        }
    }

    return false;
}

// Whether the body passes straight from one stand to the next at its own height, whatever the floor between them
// does: no face in the way of its low or its high part, and headroom on the way and at the end. For a stride over
// a gap, which the path map's own walk (a point's floor every two units) falls into.
bool strideIsClear(
    const Game::PathMap &pathMap, const Game::PathPoint &from, const Game::PathPoint &to,
    const Game::PathObject &body)
{
    const float high = std::max(body.radius, body.height - body.radius);

    for (const float offset : {body.radius, high})
    {
        if (pathMap.traceLine({from.x, from.y, from.z + offset}, {to.x, to.y, to.z + offset}, body.radius, true)
                .blocked)
        {
            return false;
        }
    }

    const Game::PathPoint middle = {(from.x + to.x) * 0.5f, (from.y + to.y) * 0.5f, std::max(from.z, to.z)};

    for (const Game::PathPoint &foot : {middle, to})
    {
        if (pathMap.traceLine({foot.x, foot.y, foot.z + body.stepHeight + 1.0f},
                    {foot.x, foot.y, foot.z + body.height}, 0.0f, false)
                .blocked)
        {
            return false;
        }
    }

    return true;
}

// Whether a step that the path map's walk stops on the face of the very floor it steps onto or off is one the game's
// party takes: that floor is walkable (a slope the party stands on), the two floors lie within a step of each other,
// and the body passes above the step with headroom. The path map's walk takes the slope's face beside the body's lower
// sphere for a wall (a step at a ramp's foot, or at its top end over a lower floor); the game's movement steps up
// onto it and down off it.
bool stepOntoSlopeIsClear(
    const Game::PathMap &pathMap, const Game::PathPoint &from, const Game::PathPoint &to,
    const Game::PathObject &body, size_t blockedFacet, size_t fromFacet, size_t targetFacet)
{
    if ((blockedFacet != targetFacet && blockedFacet != fromFacet) || blockedFacet >= pathMap.facets().size()
        || !pathMap.facets()[blockedFacet].walkableFloor || std::abs(to.z - from.z) > body.stepHeight)
    {
        return false;
    }

    const float high = std::max(body.radius, body.height - body.radius);

    if (pathMap.traceLine({from.x, from.y, from.z + body.stepHeight + body.radius},
            {to.x, to.y, to.z + body.stepHeight + body.radius}, body.radius, true).blocked
        || pathMap.traceLine({from.x, from.y, from.z + high}, {to.x, to.y, to.z + high}, body.radius, true).blocked)
    {
        return false;
    }

    for (const Game::PathPoint &foot : {from, to})
    {
        if (pathMap.traceLine({foot.x, foot.y, foot.z + body.stepHeight + 1.0f},
                {foot.x, foot.y, foot.z + body.height}, 0.0f, false).blocked)
        {
            return false;
        }
    }

    return true;
}

// How far from a place the path map's queries for the flood's steps from it look for faces, seen from above (along
// either axis): the farthest place they name lies 192 away (a landing six grid points across a gap), and the body's
// probes reach twice its radius (74) beyond the places they name. The walk step moves its end by at most half a step
// (16) to clear a wall, the narrow-gap test samples 78 around a grid point next to the place: both lie well within.
constexpr float StepQueryReach = 320.0f;

// The grid point next to a place in one of the eight directions of the flood, at the place's height. Aimed at the grid
// point, so neighbouring cells agree on where they are; `steps` grid points away for a landing across a gap.
Game::PathPoint gridPointAhead(const Game::PathPoint &point, const std::array<float, 2> &direction, float steps)
{
    constexpr float Step = 32.0f;
    return {(std::round(point.x / Step) + direction[0] * steps) * Step,
        (std::round(point.y / Step) + direction[1] * steps) * Step, point.z};
}

const std::array<std::array<float, 2>, 8> &floodDirections()
{
    static const std::array<std::array<float, 2>, 8> directions = {{
        {1.0f, 0.0f}, {-1.0f, 0.0f}, {0.0f, 1.0f}, {0.0f, -1.0f},
        {1.0f, 1.0f}, {1.0f, -1.0f}, {-1.0f, 1.0f}, {-1.0f, -1.0f}}};
    return directions;
}

// A walk of the flood not tried yet, one that walks, one that does not.
constexpr uint8_t NotTried = 0;
constexpr uint8_t Walks = 1;
constexpr uint8_t Fails = 2;

// What lies at the grid point ahead: a floor more than a step up (nothing to walk to), a floor within a step either
// way, no floor at the height walked on (a wall, a ledge's edge, a pit or a gap).
constexpr uint8_t RiseAhead = 0;
constexpr uint8_t LevelAhead = 1;
constexpr uint8_t OffAhead = 2;

// What the flood finds from a place in one direction: the floor at the grid point ahead and the ways to it.
struct StepAhead
{
    uint8_t kind : 2 = RiseAhead;
    // Off: a face in the way at the height of the body's lower sphere.
    uint8_t wall : 1 = 0;
    // Off: a floor below within a drop where the body fits, at `floorZ`.
    uint8_t drops : 1 = 0;
    // Off: a floor `landingSteps` grid points away beyond a gap, at `landingZ`.
    uint8_t lands : 1 = 0;
    // The walk's end lies off its grid point (StepsFrom::pMovedEnds).
    uint8_t moved : 1 = 0;
    // Level: the walk to the floor ahead; Off: the walk down to the floor below.
    uint8_t walk : 2 = NotTried;
    // Off: the stride to the landing.
    uint8_t stride : 2 = NotTried;
    uint8_t landingSteps : 4 = 0;
    // Level: the floor ahead; Off: the floor below.
    float floorZ = 0.0f;
    float landingZ = 0.0f;
};

// What the flood finds from one place it stands on (WalkCache). The walks themselves, the costly part, are tried only
// when the flood needs them (the place they lead to was not stood on yet) and kept once tried.
struct StepsFrom
{
    // lookAround has filled them.
    bool looked = false;
    // The floor under it, by face (`onFloor`: the path map has one).
    bool onFloor = false;
    // On a floor of a door out of the way: the fall through it to what lies under it, at `fallZ`.
    uint8_t fall = NotTried;
    int32_t floorFace = -1;
    float fallZ = 0.0f;
    std::array<StepAhead, 8> ahead;
    // The ends of the walks that the path map's walk step moved off the grid point to clear a wall, by direction.
    std::unique_ptr<std::array<Game::PathPoint, 8>> pMovedEnds;
};

// A face of a path map as a key (every member of Game::PathFacet, byte by byte) and its box seen from above.
struct FacetSet
{
    std::vector<std::string> keys;
    std::vector<std::array<float, 4>> boxes;
    // No face the path map keeps out of its spatial grid (too large for it) and no coordinate that is not a number:
    // with such a face its queries may test faces in another order.
    bool gridded = true;
};

// The facet key below names every member: a member added to Game::PathFacet must be added there too.
static_assert(sizeof(Game::PathFacet) == sizeof(std::vector<Game::PathPoint>) + 16);

FacetSet facetSetOf(const Game::PathMap &pathMap)
{
    // As the path map's grid (game/pathfinding/PathMap.cpp: MaxPathGridCellSpan, MaxSpatialCellsPerFacet), with the
    // cell of 512 that every path map walked here has.
    constexpr float GridCell = 512.0f;
    constexpr double MaxCellSpan = 4096.0;
    constexpr double MaxCells = 4096.0;
    FacetSet set;
    set.keys.reserve(pathMap.facets().size());
    set.boxes.reserve(pathMap.facets().size());

    for (const Game::PathFacet &facet : pathMap.facets())
    {
        std::string key;
        key.reserve(facet.vertices.size() * 3 * sizeof(float) + 11);
        std::array<float, 6> bounds = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};

        for (size_t index = 0; index < facet.vertices.size(); ++index)
        {
            const Game::PathPoint &vertex = facet.vertices[index];

            for (const float value : {vertex.x, vertex.y, vertex.z})
            {
                set.gridded = set.gridded && std::isfinite(value);
                key.append(reinterpret_cast<const char *>(&value), sizeof(float));
            }

            bounds = index == 0 ? std::array<float, 6>{vertex.x, vertex.x, vertex.y, vertex.y, vertex.z, vertex.z}
                : std::array<float, 6>{std::min(bounds[0], vertex.x), std::max(bounds[1], vertex.x),
                    std::min(bounds[2], vertex.y), std::max(bounds[3], vertex.y), std::min(bounds[4], vertex.z),
                    std::max(bounds[5], vertex.z)};
        }

        const char flags[7] = {static_cast<char>(facet.kind), facet.attributes.portal, facet.attributes.invisible,
            facet.attributes.untouchable, facet.blocking, facet.walkableFloor, facet.dynamic};
        key.append(flags, sizeof(flags));
        key.append(reinterpret_cast<const char *>(&facet.sourceId), sizeof(facet.sourceId));
        double cells = 1.0;

        for (size_t axis = 0; axis < 3; ++axis)
        {
            const double span = static_cast<double>(std::floor(bounds[axis * 2 + 1] / GridCell))
                - static_cast<double>(std::floor(bounds[axis * 2] / GridCell));
            set.gridded = set.gridded && span <= MaxCellSpan;
            cells *= span + 1.0;
        }

        set.gridded = set.gridded && cells <= MaxCells;
        set.keys.push_back(std::move(key));
        set.boxes.push_back({bounds[0], bounds[1], bounds[2], bounds[3]});
    }

    return set;
}

// The boxes (seen from above) of the faces of one facet list not matched in the other, where the faces matched keep
// their order: each face of `after` is matched to the first face equal to it in `before` past the last one matched
// (a door's floor taken out of the list and put back at its end is not matched there, and counts as changed). False
// when the two cannot be compared so (a face out of the path map's grid).
bool changedFacetBoxes(const FacetSet &before, const FacetSet &after, std::vector<std::array<float, 4>> &changed)
{
    if (!before.gridded || !after.gridded)
    {
        return false;
    }

    std::unordered_map<std::string_view, std::vector<size_t>> positions;
    positions.reserve(before.keys.size());

    for (size_t index = 0; index < before.keys.size(); ++index)
    {
        positions[before.keys[index]].push_back(index);
    }

    std::vector<bool> matched(before.keys.size(), false);
    size_t next = 0;

    for (size_t index = 0; index < after.keys.size(); ++index)
    {
        const std::unordered_map<std::string_view, std::vector<size_t>>::const_iterator found =
            positions.find(after.keys[index]);
        const std::vector<size_t>::const_iterator position = found == positions.end()
            ? std::vector<size_t>::const_iterator()
            : std::lower_bound(found->second.begin(), found->second.end(), next);

        if (found == positions.end() || position == found->second.end())
        {
            changed.push_back(after.boxes[index]);
            continue;
        }

        matched[*position] = true;
        next = *position + 1;
    }

    for (size_t index = 0; index < before.keys.size(); ++index)
    {
        if (!matched[index])
        {
            changed.push_back(before.boxes[index]);
        }
    }

    return true;
}

// The flood's steps from the places it stood on, kept from one walk to the next (the solve walks the map again each
// round with a door or two moved out of the way or a face made untouchable; the reach check walks it with the doors
// as the map starts, then with all of them out of the way). A step's results are those of the path maps' queries, and
// those depend only on the faces near the places they name (StepQueryReach) and on the order of those faces (a first
// hit, the first of two floors at one height), never on a face's number or on faces elsewhere (game/pathfinding/
// PathMap.cpp; every path map walked here has the grid of 512 that orders its faces). So steps found over one pair of
// path maps hold over the next where no face near them differs between the two and the faces both have keep their
// order: `follow` forgets the steps near a changed face, and all of them when that order cannot be vouched for. The
// flood keeps its own record of where it stood and takes its steps in the same order, so it stands on the same
// places in the same order as without them.
class WalkCache
{
public:
    // Before walking over `maps`, after walking over others (or none) with this cache.
    void follow(const WalkMaps &maps)
    {
        FacetSet all = facetSetOf(*maps.pAll);
        FacetSet solid = facetSetOf(maps.solid());

        if (m_following)
        {
            std::vector<std::array<float, 4>> changed;

            if (!changedFacetBoxes(m_all, all, changed) || !changedFacetBoxes(m_solid, solid, changed))
            {
                m_steps.clear();
            }
            else if (!changed.empty())
            {
                std::erase_if(m_steps, [&changed](const std::pair<const PlaceKey, StepsFrom> &entry)
                {
                    const float x = std::bit_cast<float>(entry.first.x);
                    const float y = std::bit_cast<float>(entry.first.y);
                    // A place whose coordinates are not numbers is never near anything: forget it all the same.
                    return !std::isfinite(x) || !std::isfinite(y)
                        || std::any_of(changed.begin(), changed.end(), [x, y](const std::array<float, 4> &box)
                        {
                            return x - StepQueryReach <= box[1] && x + StepQueryReach >= box[0]
                                && y - StepQueryReach <= box[3] && y + StepQueryReach >= box[2];
                        });
                });
            }
        }

        m_all = std::move(all);
        m_solid = std::move(solid);
        m_following = true;
    }

    // The steps from a place (by its exact coordinates); new ones not looked at yet.
    StepsFrom &stepsFrom(const Game::PathPoint &point)
    {
        return m_steps.try_emplace({std::bit_cast<uint32_t>(point.x), std::bit_cast<uint32_t>(point.y),
            std::bit_cast<uint32_t>(point.z)}).first->second;
    }

private:
    struct PlaceKey
    {
        uint32_t x = 0;
        uint32_t y = 0;
        uint32_t z = 0;

        bool operator==(const PlaceKey &other) const = default;
    };

    struct PlaceKeyHash
    {
        size_t operator()(const PlaceKey &key) const
        {
            uint64_t hash = ((static_cast<uint64_t>(key.x) << 32) | key.y) * 0x9E3779B97F4A7C15ull;
            hash ^= (static_cast<uint64_t>(key.z) + (hash >> 31)) * 0xC2B2AE3D27D4EB4Full;
            return static_cast<size_t>(hash ^ (hash >> 29));
        }
    };

    std::unordered_map<PlaceKey, StepsFrom, PlaceKeyHash> m_steps;
    FacetSet m_all;
    FacetSet m_solid;
    bool m_following = false;
};

// Fills a place's steps but for the walks themselves: the floor under it, and in each direction the floor ahead, a
// wall, a drop, a landing across a gap.
void lookAround(const WalkMaps &maps, const Game::PathPoint &point, const Game::PathObject &body, StepsFrom &steps)
{
    constexpr float Step = 32.0f;
    constexpr float GapSample = 4.0f;
    const Game::PathMap &pathMap = *maps.pAll;
    const Game::PathMap &solid = maps.solid();
    const Game::PathFloorSample under = pathMap.floorAt(point);

    if (under.hasFloor && under.facetIndex < pathMap.facets().size())
    {
        steps.onFloor = true;
        steps.floorFace = pathMap.facets()[under.facetIndex].sourceId;
    }

    for (size_t directionIndex = 0; directionIndex < floodDirections().size(); ++directionIndex)
    {
        const std::array<float, 2> &direction = floodDirections()[directionIndex];
        StepAhead &ahead = steps.ahead[directionIndex];
        const Game::PathPoint target = gridPointAhead(point, direction, 1.0f);

        // As the game's planner takes a step: the floor under the target (reached up a step or down a drop), then
        // the walk to it.
        const Game::PathFloorSample targetFloor = pathMap.floorAt({target.x, target.y, point.z + body.stepHeight});
        const bool hasFloor = targetFloor.hasFloor && !targetFloor.inVoid;

        if (hasFloor && targetFloor.z - point.z > body.stepHeight)
        {
            continue;
        }

        if (hasFloor && point.z - targetFloor.z <= body.stepHeight)
        {
            ahead.kind = LevelAhead;
            ahead.floorZ = targetFloor.z;
            continue;
        }

        // Nothing at this height under the target: a ledge's edge, a pit, a gap, or the far side of a wall.
        // A wall is the common case and the cheapest to tell.
        ahead.kind = OffAhead;
        const float length = std::sqrt(direction[0] * direction[0] + direction[1] * direction[1]);
        const float alongX = direction[0] / length;
        const float alongY = direction[1] / length;

        if (pathMap.traceLine({point.x, point.y, point.z + body.radius},
                    {target.x, target.y, point.z + body.radius}, 0.0f, false)
                .blocked)
        {
            ahead.wall = 1;
            continue;
        }

        // Down, where the body fits.
        if (hasFloor && point.z - targetFloor.z <= body.dropHeight
            && !overNarrowGap(solid, target.x, target.y, point.z, body))
        {
            ahead.drops = 1;
            ahead.floorZ = targetFloor.z;
        }

        // Across, where the far side is near enough: from the last floor behind the gap to the first beyond.
        const float reach = Step * length;
        float nearEdge = 0.0f;
        float height = 0.0f;

        for (float distance = GapSample; distance < reach; distance += GapSample)
        {
            if (supportAt(solid, point.x + alongX * distance, point.y + alongY * distance, point.z, body, height))
            {
                nearEdge = distance;
            }
            else
            {
                break;
            }
        }

        for (float distance = reach + GapSample; distance <= nearEdge + WidestGapCrossed + GapSample;
             distance += GapSample)
        {
            if (!supportAt(solid, point.x + alongX * distance, point.y + alongY * distance, point.z, body, height))
            {
                continue;
            }

            // The first grid point on the far floor (at most six away: the gap ends within a step and the widest
            // gap crossed of the place).
            const float landingSteps = std::ceil(distance / reach);
            Game::PathPoint landing = gridPointAhead(point, direction, landingSteps);

            if (supportAt(pathMap, landing.x, landing.y, point.z, body, landing.z))
            {
                ahead.lands = 1;
                ahead.landingSteps = static_cast<uint8_t>(landingSteps);
                ahead.landingZ = landing.z;
            }

            break;
        }
    }
}

// The point the walk in a direction leads to (Level: the floor ahead; Off: the floor below), and where it ends.
Game::PathPoint walkTarget(const StepsFrom &steps, const Game::PathPoint &point, size_t directionIndex)
{
    const Game::PathPoint target = gridPointAhead(point, floodDirections()[directionIndex], 1.0f);
    return {target.x, target.y, steps.ahead[directionIndex].floorZ};
}

Game::PathPoint walkEnd(const StepsFrom &steps, const Game::PathPoint &point, size_t directionIndex)
{
    return steps.ahead[directionIndex].moved != 0 ? (*steps.pMovedEnds)[directionIndex]
        : walkTarget(steps, point, directionIndex);
}

Game::PathPoint landingPoint(const StepsFrom &steps, const Game::PathPoint &point, size_t directionIndex)
{
    const StepAhead &ahead = steps.ahead[directionIndex];
    const Game::PathPoint landing = gridPointAhead(point, floodDirections()[directionIndex], ahead.landingSteps);
    return {landing.x, landing.y, ahead.landingZ};
}

// Tries the walk in a direction (Level or a drop): the path map's walk step, which may move its end to clear a wall.
// A walk on the level that the step refuses may still be taken: the walk fell into a crack or a slot between the two
// floors, which the party strides over; or one of the two floors slopes and the step between them meets the slope's
// face, which the path map takes for a wall and the game's party steps onto or off (a step at a ramp's foot or top).
void tryWalk(
    const WalkMaps &maps, const Game::PathPoint &point, const Game::PathObject &body, size_t directionIndex,
    StepsFrom &steps)
{
    const Game::PathMap &pathMap = *maps.pAll;
    StepAhead &ahead = steps.ahead[directionIndex];
    const Game::PathPoint target = walkTarget(steps, point, directionIndex);
    Game::PathPoint end = target;
    bool walks = pathMap.resolveWalkStep(point, end, body);

    if (!walks && ahead.kind == LevelAhead)
    {
        const Game::PathWalkSegmentDebug trace = pathMap.debugTraceWalkSegment(point, end, body);
        const Game::PathWalkRejectReason reason = trace.rejectReason;
        walks = (reason == Game::PathWalkRejectReason::SampleNoFloor
                || reason == Game::PathWalkRejectReason::SampleVoid
                || reason == Game::PathWalkRejectReason::StepHeight)
            && strideIsClear(pathMap, point, end, body);

        if (!walks && reason == Game::PathWalkRejectReason::Blocked)
        {
            // The floors under the two ends, as lookAround found them (by their numbers in this path map).
            const Game::PathFloorSample under = pathMap.floorAt(point);
            const Game::PathFloorSample targetFloor =
                pathMap.floorAt({target.x, target.y, point.z + body.stepHeight});
            walks = stepOntoSlopeIsClear(pathMap, point, end, body, trace.blockedFacet,
                under.hasFloor ? under.facetIndex : pathMap.facets().size(), targetFloor.facetIndex);
        }
    }

    ahead.walk = walks ? Walks : Fails;

    if (std::bit_cast<std::array<uint32_t, 3>>(end) != std::bit_cast<std::array<uint32_t, 3>>(target))
    {
        if (steps.pMovedEnds == nullptr)
        {
            steps.pMovedEnds = std::make_unique<std::array<Game::PathPoint, 8>>();
        }

        (*steps.pMovedEnds)[directionIndex] = end;
        ahead.moved = 1;
    }
}

// Tries the stride across a gap to the landing in a direction.
void tryStride(
    const WalkMaps &maps, const Game::PathPoint &point, const Game::PathObject &body, size_t directionIndex,
    StepsFrom &steps)
{
    steps.ahead[directionIndex].stride =
        strideIsClear(*maps.pAll, point, landingPoint(steps, point, directionIndex), body) ? Walks : Fails;
}

// Tries the fall through a moving floor stood on.
void tryFall(const WalkMaps &maps, const Game::PathPoint &point, const Game::PathObject &body, StepsFrom &steps)
{
    const Game::PathMap &solid = maps.solid();
    const Game::PathFloorSample below = solid.floorAt({point.x, point.y, point.z + body.stepHeight});
    const bool falls = below.hasFloor && !below.inVoid && point.z - below.z > body.stepHeight
        && point.z - below.z <= body.dropHeight && !overNarrowGap(solid, point.x, point.y, point.z, body);
    steps.fall = falls ? Walks : Fails;
    steps.fallZ = falls ? below.z : 0.0f;
}

bool onMovingFloor(const WalkMaps &maps, const StepsFrom &steps)
{
    return maps.pMovingFloors != nullptr && steps.onFloor && steps.floorFace >= 0
        && maps.pMovingFloors->contains(steps.floorFace);
}

// The cells a flood has stood on, by floodWalk's key of a cell (21 bits each of x, y and level, x highest): eight by
// eight cells of one level to a word, so that the cells next to one are mostly found in a word just used.
class CellSet
{
public:
    bool contains(uint64_t key)
    {
        const uint64_t *pWord = find(tileOf(key));
        return pWord != nullptr && (*pWord & bitOf(key)) != 0;
    }

    // Whether the cell was not in the set.
    bool insert(uint64_t key)
    {
        const uint64_t tile = tileOf(key);
        uint64_t *pWord = find(tile);

        if (pWord == nullptr)
        {
            pWord = &m_words.try_emplace(tile, 0).first->second;
            m_recent[slotOf(tile)].pWord = pWord;
        }

        const uint64_t bit = bitOf(key);
        const bool added = (*pWord & bit) == 0;
        *pWord |= bit;
        return added;
    }

private:
    // A key without the lowest three bits of its x and y.
    static uint64_t tileOf(uint64_t key)
    {
        return key & ~((uint64_t(7) << 42) | (uint64_t(7) << 21));
    }

    static uint64_t bitOf(uint64_t key)
    {
        return uint64_t(1) << (((key >> 42) & 7) | (((key >> 21) & 7) << 3));
    }

    // Neighbouring tiles take different slots of the words just used.
    static size_t slotOf(uint64_t tile)
    {
        return static_cast<size_t>(((tile >> 45) & 1) | (((tile >> 24) & 1) << 1));
    }

    // The word of a tile, or null when none of its cells is in the set.
    uint64_t *find(uint64_t tile)
    {
        Recent &recent = m_recent[slotOf(tile)];

        if (recent.tile != tile)
        {
            const std::unordered_map<uint64_t, uint64_t>::iterator found = m_words.find(tile);
            recent.tile = tile;
            recent.pWord = found == m_words.end() ? nullptr : &found->second;
        }

        return recent.pWord;
    }

    struct Recent
    {
        // No tile: a tile has the low bits of its x and y clear.
        uint64_t tile = ~uint64_t(0);
        uint64_t *pWord = nullptr;
    };

    std::unordered_map<uint64_t, uint64_t> m_words;
    std::array<Recent, 4> m_recent;
};

// Everything the body can walk to from the seeds: a flood over a grid of steps, each taken with the path map's own
// walk step (floors, step heights, drops, blocking faces), and across gaps as the game's party crosses them (see
// WidestGapCrossed). A floor of a door that is out of the way is stood on and also fallen through, to what lies
// under it. Returns the faces whose floor was stood on. `pCache`: steps kept from earlier walks with it (WalkCache;
// its `follow` called for these maps), and kept for later ones.
std::set<int32_t> floodWalk(
    const WalkMaps &maps,
    const std::vector<Game::PathPoint> &seeds,
    size_t &cellCount,
    std::vector<WalkCell> *pCells = nullptr,
    WalkCache *pCache = nullptr)
{
    constexpr float Step = 32.0f;
    constexpr float LevelHeight = 64.0f;
    const Game::PathObject body = partyBody();
    const Game::PathMap &pathMap = *maps.pAll;
    WalkCache ownCache;
    WalkCache &cache = pCache != nullptr ? *pCache : ownCache;
    std::set<int32_t> floorFaces;
    cellCount = 0;

    // One number per cell: 21 bits for each of x, y and the level.
    const auto keyOf = [](const Game::PathPoint &point)
    {
        const uint64_t x = static_cast<uint64_t>(std::lround(point.x / Step) + (1 << 20)) & 0x1fffff;
        const uint64_t y = static_cast<uint64_t>(std::lround(point.y / Step) + (1 << 20)) & 0x1fffff;
        const uint64_t z = static_cast<uint64_t>(std::lround(point.z / LevelHeight) + (1 << 20)) & 0x1fffff;
        return (x << 42) | (y << 21) | z;
    };

    CellSet visited;
    // The places to stand on yet, each with its steps.
    std::vector<std::pair<Game::PathPoint, StepsFrom *>> frontier;
    const auto stand = [&frontier, &cache](const Game::PathPoint &point)
    {
        frontier.push_back({point, &cache.stepsFrom(point)});
    };

    for (const Game::PathPoint &seed : seeds)
    {
        // Where the seed stands on a floor it starts there. The engine's snap looks from the nearest floor edge
        // inward at the seed's own height, which misses a sloped floor: a party that arrives on a ramp would
        // otherwise reach nothing.
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

        if (valid && visited.insert(keyOf(start)))
        {
            stand(start);
        }
    }

    // The face last added to floorFaces: the cells of one floor mostly follow each other.
    std::optional<int32_t> lastFloorFace;

    while (!frontier.empty())
    {
        const Game::PathPoint point = frontier.back().first;
        StepsFrom &steps = *frontier.back().second;
        frontier.pop_back();
        ++cellCount;

        if (!steps.looked)
        {
            lookAround(maps, point, body, steps);
            steps.looked = true;
        }

        int32_t floorFace = -1;

        if (steps.onFloor)
        {
            floorFace = steps.floorFace;

            if (lastFloorFace != floorFace)
            {
                floorFaces.insert(floorFace);
                lastFloorFace = floorFace;
            }
        }

        if (pCells != nullptr)
        {
            pCells->push_back({point, floorFace});
        }

        // On the floor of a door that is out of the way: with the door in its other pose the floor is gone and the
        // party stands on what lies under it (the shaft under a hatch's cover, the pit under a lift).
        if (onMovingFloor(maps, steps))
        {
            if (steps.fall == NotTried)
            {
                tryFall(maps, point, body, steps);
            }

            const Game::PathPoint fallen = {point.x, point.y, steps.fallZ};

            if (steps.fall == Walks && visited.insert(keyOf(fallen)))
            {
                stand(fallen);
            }
        }

        for (size_t directionIndex = 0; directionIndex < steps.ahead.size(); ++directionIndex)
        {
            const StepAhead &ahead = steps.ahead[directionIndex];

            if (ahead.kind == RiseAhead || (ahead.kind == OffAhead && ahead.wall != 0))
            {
                continue;
            }

            // On the level, or down where the body fits. Already stood on: the walk to it need not be tried again
            // from here.
            if ((ahead.kind == LevelAhead || ahead.drops != 0)
                && !visited.contains(keyOf(walkTarget(steps, point, directionIndex))))
            {
                if (ahead.walk == NotTried)
                {
                    tryWalk(maps, point, body, directionIndex, steps);
                }

                if (ahead.walk == Walks && visited.insert(keyOf(walkEnd(steps, point, directionIndex))))
                {
                    stand(walkEnd(steps, point, directionIndex));
                }
            }

            // Across, to the first grid point on the far floor.
            if (ahead.kind == OffAhead && ahead.lands != 0)
            {
                const Game::PathPoint landing = landingPoint(steps, point, directionIndex);

                if (!visited.contains(keyOf(landing)))
                {
                    if (ahead.stride == NotTried)
                    {
                        tryStride(maps, point, body, directionIndex, steps);
                    }

                    if (ahead.stride == Walks && visited.insert(keyOf(landing)))
                    {
                        stand(landing);
                    }
                }
            }
        }
    }

    return floorFaces;
}

std::set<size_t> sectorsOf(const Game::IndoorMapData &map, const std::set<int32_t> &floorFaces)
{
    std::set<size_t> sectors;

    for (const int32_t faceId : floorFaces)
    {
        if (faceId >= 0 && static_cast<size_t>(faceId) < map.faces.size())
        {
            sectors.insert(map.faces[static_cast<size_t>(faceId)].roomNumber);
        }
    }

    return sectors;
}

// The path maps of a walk with doors out of the way. A door has two poses and which of them clears its passage
// differs from door to door, so "open" cannot be had by setting a state: the doors' faces are taken out as
// obstacles, and kept, in both poses, where they are floors to stand on (lifts, bridges, trapdoors).
struct ClearedMaps
{
    Game::PathMap all;
    // Without the cleared doors' floors.
    Game::PathMap solid;
    std::set<int32_t> movingFloors;
    // For every floor face of a cleared door that carries what stands on it, where it stands in each pose. A party
    // on such a floor in one pose is carried to the other (a lift), which no walk finds.
    std::map<int32_t, std::vector<Game::PathPoint>> rideStops;
    // The scene's ladders: a party that stands at `from` (a ladder's foot, or its top exit when it is taken hold of
    // from above) climbs to `to`.
    struct LadderLink
    {
        Game::PathPoint from;
        Game::PathPoint to;
        float reach = 0.0f;
    };
    std::vector<LadderLink> ladders;

    WalkMaps walk() const
    {
        return {&all, movingFloors.empty() ? nullptr : &solid, movingFloors.empty() ? nullptr : &movingFloors};
    }
};

// `pClearedDoors`: only these doors stand out of the way, the others stay as the map starts (null: every door).
// `pPassableFaces`: faces an event has made untouchable (evt.SetFacetBit: an unseen barrier switched off), which
// no longer block.
// The path map without the faces the game never meets (facesTheGameIgnores); the same map when there are none.
Game::PathMap withoutIgnoredFaces(const Game::PathMap &pathMap, const std::set<uint32_t> &ignored)
{
    if (ignored.empty())
    {
        return pathMap;
    }

    std::vector<Game::PathFacet> facets;

    for (const Game::PathFacet &facet : pathMap.facets())
    {
        if (!ignored.contains(facet.sourceId))
        {
            facets.push_back(facet);
        }
    }

    Game::PathMap kept;
    kept.setFacets(std::move(facets));
    kept.buildSpatialGrid(512.0f);
    return kept;
}

void buildClearedMaps(
    const LoadedMap &map,
    const std::set<uint32_t> *pClearedDoors,
    const std::set<uint32_t> *pPassableFaces,
    ClearedMaps &maps)
{
    const Game::IndoorMapData &indoor = *map.indoor;
    Game::MapDeltaData state = *map.state;
    const std::set<uint32_t> ignored = facesTheGameIgnores(indoor);

    // Ladders: up from the foot to the top exit, and down from the top exit where the ladder says `grab_at_top` (the
    // game lets a party there take hold and climb down).
    for (const Game::IndoorLadder &ladder :
        map.indoorScene && !map.indoorScene->ladders.empty() ? map.indoorScene->ladders : indoor.ladders)
    {
        const Game::PathPoint foot = {ladder.bottom[0], ladder.bottom[1], ladder.bottom[2]};
        const Game::PathPoint exit = {ladder.topExit[0], ladder.topExit[1], ladder.topExit[2]};
        maps.ladders.push_back({foot, exit, ladder.reach});

        if (ladder.grabAtTop)
        {
            maps.ladders.push_back({exit, foot, ladder.reach});
        }
    }

    if (pPassableFaces != nullptr && !pPassableFaces->empty())
    {
        // The state's attributes stand in front of the map's own, face by face: give it all of them.
        for (size_t faceIndex = state.faceAttributes.size(); faceIndex < indoor.faces.size(); ++faceIndex)
        {
            state.faceAttributes.push_back(indoor.faces[faceIndex].attributes);
        }

        for (const uint32_t faceIndex : *pPassableFaces)
        {
            if (faceIndex < state.faceAttributes.size())
            {
                state.faceAttributes[faceIndex] |= Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
            }
        }
    }

    std::set<int32_t> doorFaces;
    std::set<int32_t> carriedFaces;
    Game::EventRuntimeState atOpen;
    Game::EventRuntimeState atClosed;

    for (const Game::MapDeltaDoor &door : state.doors)
    {
        if (pClearedDoors != nullptr && !pClearedDoors->contains(door.doorId))
        {
            continue;
        }

        // As the game carries: a door that moves up or down, or a level slide whose mover block says `carry`.
        const bool carries =
            Game::indoorDoorCarriesPartySupport(door, Game::findIndoorMoverDefinition(indoor, door.doorId));

        for (const uint16_t faceId : door.faceIds)
        {
            doorFaces.insert(faceId);

            if (carries)
            {
                carriedFaces.insert(faceId);
            }
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

    std::vector<Game::PathFacet> solidFacets;
    std::vector<Game::PathFacet> movingFacets;
    bool first = true;

    // The first pass is the map as it starts (every face that is not a cleared door's); the two others add the
    // cleared doors' floors in each of their poses.
    for (const Game::EventRuntimeState *pState :
         std::initializer_list<const Game::EventRuntimeState *>{nullptr, &atOpen, &atClosed})
    {
        if (!first && doorFaces.empty())
        {
            break;
        }

        const std::vector<Game::IndoorVertex> vertices =
            Game::buildIndoorMechanismAdjustedVertices(indoor, &state, pState);
        const Game::IndoorPathMapBuildResult built =
            Game::IndoorPathfindingBuilder::buildPathMap(indoor, vertices, &state);

        for (const Game::PathFacet &facet : built.pathMap.facets())
        {
            if (ignored.contains(facet.sourceId))
            {
                continue;
            }

            const bool isDoorFace = doorFaces.contains(facet.sourceId);

            if (!isDoorFace && first)
            {
                solidFacets.push_back(facet);
            }
            else if (isDoorFace && !first && facet.walkableFloor)
            {
                movingFacets.push_back(facet);
                maps.movingFloors.insert(facet.sourceId);

                if (carriedFaces.contains(facet.sourceId) && !facet.vertices.empty())
                {
                    Game::PathPoint middle = {0.0f, 0.0f, 0.0f};

                    for (const Game::PathPoint &vertex : facet.vertices)
                    {
                        middle.x += vertex.x;
                        middle.y += vertex.y;
                        middle.z += vertex.z;
                    }

                    const float count = static_cast<float>(facet.vertices.size());
                    maps.rideStops[facet.sourceId].push_back({middle.x / count, middle.y / count, middle.z / count});
                }
            }
        }

        first = false;
    }

    std::vector<Game::PathFacet> allFacets = solidFacets;
    allFacets.insert(allFacets.end(), movingFacets.begin(), movingFacets.end());
    maps.all.setFacets(std::move(allFacets));
    maps.all.buildSpatialGrid(512.0f);

    if (!maps.movingFloors.empty())
    {
        maps.solid.setFacets(std::move(solidFacets));
        maps.solid.buildSpatialGrid(512.0f);
    }
}

// The flood, with the party carried by every moving floor it steps on that carries: from a lift's floor in one pose
// to where that floor stands in the other, until nothing new is reached. Each flood after the first takes the steps
// of those before it from `cache`, which also keeps them for a later call over other maps (WalkCache).
std::set<int32_t> floodWalkWithRides(
    const ClearedMaps &maps,
    std::vector<Game::PathPoint> seeds,
    size_t &cellCount,
    std::vector<WalkCell> *pCells,
    WalkCache &cache)
{
    std::set<int32_t> ridden;
    std::set<size_t> climbed;
    std::set<int32_t> faces;
    std::vector<WalkCell> cells;
    const Game::PathObject body = partyBody();
    cache.follow(maps.walk());

    for (;;)
    {
        cells.clear();
        faces = floodWalk(maps.walk(), seeds, cellCount, &cells, &cache);
        bool added = false;

        for (const std::pair<const int32_t, std::vector<Game::PathPoint>> &ride : maps.rideStops)
        {
            if (faces.contains(ride.first) && ridden.insert(ride.first).second)
            {
                seeds.insert(seeds.end(), ride.second.begin(), ride.second.end());
                added = true;
            }
        }

        // A ladder is climbed from a place the walk stood on within reach of its end (a grid cell's centre is up
        // to half a cell's diagonal from where the body could stand).
        for (size_t index = 0; index < maps.ladders.size(); ++index)
        {
            const ClearedMaps::LadderLink &ladder = maps.ladders[index];
            const float within = ladder.reach + body.radius + 23.0f;
            const bool atFoot = std::any_of(cells.begin(), cells.end(), [&ladder, &body, within](const WalkCell &cell)
            {
                const float dx = cell.point.x - ladder.from.x;
                const float dy = cell.point.y - ladder.from.y;
                return dx * dx + dy * dy <= within * within && std::abs(cell.point.z - ladder.from.z) <= body.stepHeight;
            });

            if (atFoot && climbed.insert(index).second)
            {
                seeds.push_back(ladder.to);
                added = true;
            }
        }

        if (pCells != nullptr)
        {
            *pCells = cells;
        }

        if (!added)
        {
            return faces;
        }
    }
}

// Floor area of a sector's floor faces, seen from above.
double sectorFloorArea(const Game::IndoorMapData &map, const Game::IndoorSector &sector)
{
    double total = 0.0;

    for (const uint16_t faceId : sector.floorFaceIds)
    {
        if (faceId >= map.faces.size() || map.faces[faceId].isPortal)
        {
            continue;
        }

        const Game::IndoorFace &face = map.faces[faceId];
        double doubleArea = 0.0;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const Game::IndoorVertex &current = map.vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &next = map.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            doubleArea += static_cast<double>(current.x) * next.y - static_cast<double>(next.x) * current.y;
        }

        total += std::abs(doubleArea) / 2.0;
    }

    return total;
}

// A sector whose floor is smaller than a body can stand in with room to spare: an alcove, a key slot, a ledge.
constexpr double NicheFloorArea = 40000.0;

// A sector lower from its lowest floor to its highest point than the party is tall (partyBody): a slot of lava
// under a grating, a crawl space. The party never stands in it.
bool sectorTooLow(const Game::IndoorMapData &map, const Game::IndoorSector &sector)
{
    float lowestFloor = std::numeric_limits<float>::max();
    float highest = std::numeric_limits<float>::lowest();

    for (const uint16_t faceId : sector.faceIds)
    {
        if (faceId >= map.faces.size())
        {
            continue;
        }

        const bool floor = std::find(sector.floorFaceIds.begin(), sector.floorFaceIds.end(), faceId)
            != sector.floorFaceIds.end();

        for (const uint16_t vertex : map.faces[faceId].vertexIndices)
        {
            if (vertex < map.vertices.size())
            {
                highest = std::max(highest, static_cast<float>(map.vertices[vertex].z));
                lowestFloor = floor ? std::min(lowestFloor, static_cast<float>(map.vertices[vertex].z)) : lowestFloor;
            }
        }
    }

    return lowestFloor < highest && highest - lowestFloor < partyBody().height;
}

// A sector the party cannot stand in: too small or too low.
bool sectorIsNiche(const Game::IndoorMapData &map, const Game::IndoorSector &sector)
{
    return sectorFloorArea(map, sector) < NicheFloorArea || sectorTooLow(map, sector);
}

// A point on the sector's largest floor face.
bool sectorFloorPoint(
    const Game::IndoorMapData &map,
    const std::vector<Game::IndoorVertex> &vertices,
    const Game::IndoorSector &sector,
    Game::PathPoint &point)
{
    double bestArea = 0.0;

    for (const uint16_t faceId : sector.floorFaceIds)
    {
        if (faceId >= map.faces.size())
        {
            continue;
        }

        const Game::IndoorFace &face = map.faces[faceId];

        if (face.isPortal || face.vertexIndices.size() < 3)
        {
            continue;
        }

        double sumX = 0.0;
        double sumY = 0.0;
        double sumZ = 0.0;
        double doubleArea = 0.0;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const Game::IndoorVertex &current = vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &next = vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            sumX += current.x;
            sumY += current.y;
            sumZ += current.z;
            doubleArea += static_cast<double>(current.x) * next.y - static_cast<double>(next.x) * current.y;
        }

        const double area = std::abs(doubleArea);

        if (area > bestArea)
        {
            bestArea = area;
            const double count = static_cast<double>(face.vertexIndices.size());
            point = {static_cast<float>(sumX / count), static_cast<float>(sumY / count),
                static_cast<float>(sumZ / count)};
        }
    }

    return bestArea > 0.0;
}
}

struct WalkSteps::Kept
{
    WalkCache cache;
};

WalkSteps::WalkSteps()
    : m_pKept(std::make_unique<Kept>())
{
}

WalkSteps::~WalkSteps() = default;

WalkSteps::Kept &WalkSteps::kept()
{
    return *m_pKept;
}

// The faces an effect of core/EventFlow makes passable: "SetFacetBit(-4522, 536870912, 1)" with the untouchable
// bit switched on. A negative reference is one face by its number, a positive one every face of that cog number
// (game/events/EventRuntime.cpp, eventFaceReferenceKey).
std::vector<uint32_t> facesMadePassable(const Game::IndoorMapData &indoor, const std::string &effect)
{
    std::vector<uint32_t> faces;
    long long reference = 0;
    long long bits = 0;
    char on[16] = {};

    if (std::sscanf(effect.c_str(), "SetFacetBit(%lld, %lld, %15[^)])", &reference, &bits, on) != 3
        || (static_cast<uint32_t>(bits) & Game::faceAttributeBit(Game::FaceAttribute::Untouchable)) == 0
        || std::string(on) == "0" || std::string(on) == "false" || std::string(on) == "nil")
    {
        return faces;
    }

    if (reference < 0)
    {
        if (static_cast<size_t>(-reference) < indoor.faces.size())
        {
            faces.push_back(static_cast<uint32_t>(-reference));
        }

        return faces;
    }

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        if (reference != 0 && indoor.faces[faceIndex].cogNumber == reference)
        {
            faces.push_back(static_cast<uint32_t>(faceIndex));
        }
    }

    return faces;
}

std::string pointText(float x, float y, float z)
{
    return "(" + std::to_string(std::lround(x)) + ", " + std::to_string(std::lround(y)) + ", "
        + std::to_string(std::lround(z)) + ")";
}

// The events of a flow that move each door.
std::map<uint32_t, std::set<int>> eventsMovingDoors(const YAML::Node &events)
{
    std::map<uint32_t, std::set<int>> eventsByDoor;

    for (const YAML::Node &event : events)
    {
        for (const YAML::Node &path : event["paths"])
        {
            for (const YAML::Node &effect : path["effects"])
            {
                if (effect.Scalar().starts_with("door "))
                {
                    eventsByDoor[static_cast<uint32_t>(std::stoul(effect.Scalar().substr(5)))].insert(
                        event["event"].as<int>());
                }
            }
        }
    }

    return eventsByDoor;
}

// Where a walk ends: every opening (portal) between a reached sector and one of `unreached`, with the path map's
// account of why the body does not pass through its middle.
std::vector<WalkStop> findWalkStops(
    const LoadedMap &map,
    const ClearedMaps &maps,
    const std::vector<WalkCell> &cells,
    const std::set<size_t> &reached,
    const std::set<size_t> &unreached,
    const std::map<uint32_t, std::set<int>> &eventsByDoor)
{
    const Game::IndoorMapData &indoor = *map.indoor;
    const Game::PathMap &pathMap = maps.all;
    const Game::PathObject body = partyBody();
    const std::vector<Game::IndoorVertex> vertices =
        Game::buildIndoorMechanismAdjustedVertices(indoor, &*map.state, nullptr);
    std::map<int32_t, uint32_t> doorOfFace;

    for (const Game::MapDeltaDoor &door : map.state->doors)
    {
        for (const uint16_t faceId : door.faceIds)
        {
            doorOfFace[faceId] = door.doorId;
        }
    }

    // The place stood on nearest to a point, and how far it is.
    const auto nearestCell = [&cells](const Game::PathPoint &point, Game::PathPoint &nearest)
    {
        float best = 1.0e30f;

        for (const WalkCell &cell : cells)
        {
            const float distance = std::sqrt((cell.point.x - point.x) * (cell.point.x - point.x)
                + (cell.point.y - point.y) * (cell.point.y - point.y)
                + (cell.point.z - point.z) * (cell.point.z - point.z));

            if (distance < best)
            {
                best = distance;
                nearest = cell.point;
            }
        }

        return best;
    };
    const auto sectorOfFloor = [&pathMap, &indoor](const Game::PathFloorSample &floor) -> int
    {
        if (!floor.hasFloor || floor.facetIndex >= pathMap.facets().size())
        {
            return -1;
        }

        const int32_t faceId = pathMap.facets()[floor.facetIndex].sourceId;
        return faceId >= 0 && static_cast<size_t>(faceId) < indoor.faces.size()
            ? static_cast<int>(indoor.faces[static_cast<size_t>(faceId)].roomNumber) : -1;
    };
    const auto describeDoor = [&eventsByDoor](uint32_t doorId)
    {
        std::string text = "door " + std::to_string(doorId) + " stands in it";
        const std::map<uint32_t, std::set<int>>::const_iterator moved = eventsByDoor.find(doorId);

        if (moved == eventsByDoor.end())
        {
            return text + " (no event of the map moves it)";
        }

        text += " (moved by event";

        for (const int eventId : moved->second)
        {
            text += " " + std::to_string(eventId);
        }

        return text + ")";
    };
    std::vector<WalkStop> stops;
    std::set<std::tuple<size_t, size_t, long, long, long>> seen;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];

        if (!face.isPortal || face.vertexIndices.size() < 3)
        {
            continue;
        }

        size_t fromSector = face.roomNumber;
        size_t toSector = face.roomBehindNumber;

        if (reached.contains(toSector) && unreached.contains(fromSector))
        {
            std::swap(fromSector, toSector);
        }
        else if (!reached.contains(fromSector) || !unreached.contains(toSector))
        {
            continue;
        }

        // The opening's middle, its foot and the direction through it (Newell's sum for the plane).
        Game::PathPoint middle = {0.0f, 0.0f, 0.0f};
        std::array<double, 3> normal = {0.0, 0.0, 0.0};
        float lowest = 1.0e30f;
        bool whole = true;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            if (face.vertexIndices[index] >= vertices.size()
                || face.vertexIndices[(index + 1) % face.vertexIndices.size()] >= vertices.size())
            {
                whole = false;
                break;
            }

            const Game::IndoorVertex &current = vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &next = vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            normal[0] += static_cast<double>(current.y - next.y) * (current.z + next.z);
            normal[1] += static_cast<double>(current.z - next.z) * (current.x + next.x);
            normal[2] += static_cast<double>(current.x - next.x) * (current.y + next.y);
            const float count = static_cast<float>(face.vertexIndices.size());
            middle.x += current.x / count;
            middle.y += current.y / count;
            middle.z += current.z / count;
            lowest = std::min(lowest, static_cast<float>(current.z));
        }

        const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

        if (!whole || length < 1.0e-6
            || !seen.insert({fromSector, toSector, std::lround(middle.x / 64.0f), std::lround(middle.y / 64.0f),
                    std::lround(middle.z / 64.0f)})
                    .second)
        {
            continue;
        }

        WalkStop stop;
        stop.fromSector = fromSector;
        stop.toSector = toSector;
        stop.face = static_cast<int32_t>(faceIndex);
        Game::PathPoint nearest = {0.0f, 0.0f, 0.0f};

        if (std::abs(normal[2]) / length > 0.7)
        {
            // An opening in a floor or ceiling.
            stop.at = {middle.x, middle.y, middle.z};
            const float distance = nearestCell(middle, nearest);
            const Game::PathMap &solid = maps.walk().solid();
            const Game::PathFloorSample under = solid.floorAt({middle.x, middle.y, middle.z + 1.0f});

            if (nearest.z < middle.z - body.stepHeight)
            {
                stop.reason = "a hole in the ceiling: no walk leads up through it (the floor stood on nearest to it is "
                    + std::to_string(std::lround(middle.z - nearest.z)) + " under it)";
            }
            else if (overNarrowGap(solid, middle.x, middle.y, middle.z, body))
            {
                stop.reason = "a hole in the floor narrower than the body, or covered: the party does not fall into it";
            }
            else if (under.hasFloor && !under.inVoid && middle.z - under.z > body.dropHeight)
            {
                stop.reason = "a hole in the floor with a drop of " + std::to_string(std::lround(middle.z - under.z))
                    + ", more than the walk takes (" + std::to_string(std::lround(body.dropHeight)) + ")";
            }
            else
            {
                stop.reason = "a hole in the floor the walk does not come to: the nearest place stood on is "
                    + pointText(nearest.x, nearest.y, nearest.z) + ", " + std::to_string(std::lround(distance))
                    + " away";
            }

            stops.push_back(stop);
            continue;
        }

        const float alongX = static_cast<float>(normal[0] / std::sqrt(normal[0] * normal[0] + normal[1] * normal[1]));
        const float alongY = static_cast<float>(normal[1] / std::sqrt(normal[0] * normal[0] + normal[1] * normal[1]));
        stop.at = {middle.x, middle.y, lowest};
        // A stand on each side of the opening, on the floor under its foot.
        Game::PathPoint sides[2];
        bool stands[2] = {false, false};
        int sectors[2] = {-1, -1};

        for (int side = 0; side < 2; ++side)
        {
            for (const float reach : {48.0f, 80.0f, 24.0f})
            {
                const float sign = side == 0 ? 1.0f : -1.0f;
                const Game::PathPoint probe = {middle.x + sign * alongX * reach, middle.y + sign * alongY * reach,
                    lowest + body.stepHeight + 1.0f};
                const Game::PathFloorSample floor = pathMap.floorAt(probe);

                if (floor.hasFloor && !floor.inVoid)
                {
                    sides[side] = {probe.x, probe.y, floor.z};
                    stands[side] = true;
                    sectors[side] = sectorOfFloor(floor);
                    break;
                }
            }
        }

        if (!stands[0] || !stands[1])
        {
            stop.reason = "no floor to stand on under its foot on the side of sector "
                + std::to_string(!stands[0] && sectors[1] == static_cast<int>(fromSector) ? toSector
                        : !stands[1] && sectors[0] == static_cast<int>(fromSector) ? toSector : fromSector);
            stops.push_back(stop);
            continue;
        }

        // Which side the walk comes from: the one whose floor belongs to the reached sector, else the one nearer to
        // a place stood on.
        int from = 0;

        if (sectors[1] == static_cast<int>(fromSector) && sectors[0] != static_cast<int>(fromSector))
        {
            from = 1;
        }
        else if (sectors[0] == sectors[1] || sectors[0] != static_cast<int>(fromSector))
        {
            from = nearestCell(sides[1], nearest) < nearestCell(sides[0], nearest) ? 1 : 0;
        }

        const Game::PathPoint &source = sides[from];
        const Game::PathPoint &target = sides[1 - from];
        const Game::PathWalkSegmentDebug why = pathMap.debugTraceWalkSegment(source, target, body);
        const bool floorFault = why.rejectReason == Game::PathWalkRejectReason::SampleNoFloor
            || why.rejectReason == Game::PathWalkRejectReason::SampleVoid
            || why.rejectReason == Game::PathWalkRejectReason::StepHeight;
        const float distance = nearestCell(source, nearest);

        if (why.success
            || (floorFault && std::abs(target.z - source.z) <= body.stepHeight
                && strideIsClear(pathMap, source, target, body)))
        {
            stop.passes = distance <= 96.0f;
            stop.reason = distance > 96.0f
                ? "the walk does not come to this opening: sector " + std::to_string(fromSector)
                    + " is reached only in part (the nearest place stood on is "
                    + pointText(nearest.x, nearest.y, nearest.z) + ", " + std::to_string(std::lround(distance))
                    + " away)"
                : "the body passes its middle: what stops the walk lies beside it (oymap probe from "
                    + pointText(source.x, source.y, source.z) + " to " + pointText(target.x, target.y, target.z)
                    + ")";
        }
        else if (why.rejectReason == Game::PathWalkRejectReason::Blocked && why.blockedFacet < pathMap.facets().size())
        {
            const int32_t blocking = pathMap.facets()[why.blockedFacet].sourceId;
            const std::map<int32_t, uint32_t>::const_iterator door = doorOfFace.find(blocking);

            if (door != doorOfFace.end())
            {
                stop.reason = describeDoor(door->second);
            }
            else
            {
                stop.reason = "blocked by face " + std::to_string(blocking);

                if (blocking >= 0 && static_cast<size_t>(blocking) < indoor.faces.size())
                {
                    const Game::IndoorFace &wall = indoor.faces[static_cast<size_t>(blocking)];
                    const uint32_t attributes = static_cast<size_t>(blocking) < map.state->faceAttributes.size()
                        ? map.state->faceAttributes[static_cast<size_t>(blocking)] : wall.attributes;
                    stop.reason += std::string(" (")
                        + (Game::hasFaceAttribute(attributes, Game::FaceAttribute::Invisible) ? "not drawn, " : "")
                        + "texture " + wall.textureName
                        + (wall.cogTriggered != 0 ? ", event " + std::to_string(wall.cogTriggered) : std::string())
                        + ")";
                }
            }

            stop.reason += " at " + pointText(why.blockedPoint.x, why.blockedPoint.y, why.blockedPoint.z);
        }
        else if (why.rejectReason == Game::PathWalkRejectReason::StepHeight)
        {
            stop.reason = "a step " + std::to_string(std::lround(why.stepDeltaZ)) + " high at "
                + pointText(why.probe.x, why.probe.y, why.failedFloor.z) + " (the walk climbs "
                + std::to_string(std::lround(body.stepHeight)) + ")";
        }
        else
        {
            stop.reason = "no floor at " + pointText(why.probe.x, why.probe.y, why.probe.z);
        }

        stops.push_back(stop);
    }

    // Openings into the larger sectors first: a niche is rarely the fault.
    std::stable_sort(stops.begin(), stops.end(), [&indoor](const WalkStop &left, const WalkStop &right)
    {
        const bool leftNiche = sectorIsNiche(indoor, indoor.sectors[left.toSector]);
        const bool rightNiche = sectorIsNiche(indoor, indoor.sectors[right.toSector]);
        return std::tie(leftNiche, left.toSector, left.fromSector)
            < std::tie(rightNiche, right.toSector, right.fromSector);
    });
    return stops;
}

ReachabilityResult checkReachability(const LoadedMap &map, const std::string &eventFlowJson, WalkSteps *pSteps)
{
    ReachabilityResult result;

    if (!map.indoor)
    {
        result.skipped = "outdoor maps are not walked yet";
        return result;
    }

    // The scene's start, or the BLV's own "Party Start" marker on maps that have no scene start.
    std::optional<Game::IndoorPartyStartPoint> start = map.indoor->partyStartPoint;

    if (map.indoorScene && !map.indoorScene->partyStartPoints.empty())
    {
        start = map.indoorScene->partyStartPoints.front().startPoint;
    }

    if (!start || !map.state)
    {
        result.skipped = "the map has no party start";
        return result;
    }

    const Game::IndoorMapData &indoor = *map.indoor;
    const Game::PathPoint from = {
        static_cast<float>(start->x), static_cast<float>(start->y), static_cast<float>(start->z)};

    // The doors as the map starts, and every door out of the way.
    const std::vector<Game::IndoorVertex> startVertices =
        Game::buildIndoorMechanismAdjustedVertices(indoor, &*map.state, nullptr);
    const std::vector<Game::IndoorVertex> &openVertices = startVertices;
    const Game::IndoorPathMapBuildResult startMap =
        Game::IndoorPathfindingBuilder::buildPathMap(indoor, startVertices, &*map.state);
    const Game::PathMap startPath = withoutIgnoredFaces(startMap.pathMap, facesTheGameIgnores(indoor));
    // With every door out of the way, and every face an event can switch off.
    std::set<uint32_t> passableFaces;
    std::map<uint32_t, std::set<int>> eventsByDoor;

    if (!eventFlowJson.empty())
    {
        const YAML::Node events = YAML::Load(eventFlowJson);
        eventsByDoor = eventsMovingDoors(events);

        for (const YAML::Node &event : events)
        {
            for (const YAML::Node &path : event["paths"])
            {
                for (const YAML::Node &effect : path["effects"])
                {
                    for (const uint32_t faceIndex : facesMadePassable(indoor, effect.Scalar()))
                    {
                        passableFaces.insert(faceIndex);
                    }
                }
            }
        }
    }

    ClearedMaps clearMaps;
    buildClearedMaps(map, nullptr, &passableFaces, clearMaps);
    const Game::PathMap &clearMap = clearMaps.all;
    result.ran = true;
    size_t cells = 0;
    std::vector<WalkCell> walked;
    // The walk with every door out of the way takes the steps of the walk with the doors as the map starts where
    // the faces near them are the same.
    WalkSteps ownSteps;
    WalkCache &cache = (pSteps != nullptr ? *pSteps : ownSteps).kept().cache;
    const WalkMaps startWalk = {&startPath, nullptr, nullptr};
    cache.follow(startWalk);
    const std::set<size_t> reachedAtStart = sectorsOf(indoor, floodWalk(startWalk, {from}, cells, nullptr, &cache));
    std::set<size_t> reachedOpen = sectorsOf(indoor, floodWalkWithRides(clearMaps, {from}, cells, &walked, cache));
    result.cellsWalked = cells;

    for (size_t sectorIndex = 0; sectorIndex < indoor.sectors.size(); ++sectorIndex)
    {
        Game::PathPoint point;

        if (!sectorFloorPoint(indoor, openVertices, indoor.sectors[sectorIndex], point))
        {
            continue;
        }

        ++result.sectorsWithFloor;
        result.reachedAtStart += reachedAtStart.contains(sectorIndex) ? 1 : 0;

        if (reachedOpen.contains(sectorIndex))
        {
            ++result.reachedDoorsOpen;
        }
        else if (sectorTooLow(indoor, indoor.sectors[sectorIndex]))
        {
            result.tooLowNotReached.push_back(sectorIndex);
        }
        else
        {
            result.unreachableSectors.push_back(sectorIndex);
        }
    }

    result.stops = findWalkStops(map, clearMaps, walked, reachedOpen,
        std::set<size_t>(result.unreachableSectors.begin(), result.unreachableSectors.end()), eventsByDoor);
    // A sector the body walks into though no grid point of the walk falls on its floor is reached.
    std::set<size_t> entered;

    for (const WalkStop &stop : result.stops)
    {
        if (stop.passes)
        {
            entered.insert(stop.toSector);
        }
    }

    std::erase_if(result.stops, [&entered](const WalkStop &stop)
    {
        return entered.contains(stop.toSector);
    });
    std::erase_if(result.unreachableSectors, [&entered](size_t sector)
    {
        return entered.contains(sector);
    });
    result.reachedDoorsOpen += entered.size();
    reachedOpen.insert(entered.begin(), entered.end());

    // A spawn point is reached when the floor under it belongs to a reached sector.
    result.spawnsTotal = indoor.spawns.size();

    for (size_t spawnIndex = 0; spawnIndex < indoor.spawns.size(); ++spawnIndex)
    {
        const Game::IndoorSpawn &spawn = indoor.spawns[spawnIndex];
        const Game::PathFloorSample under = clearMap.floorAt(
            {static_cast<float>(spawn.x), static_cast<float>(spawn.y), static_cast<float>(spawn.z) + 32.0f});
        const bool reached = under.hasFloor && under.facetIndex < clearMap.facets().size()
            && !sectorsOf(indoor, {clearMap.facets()[under.facetIndex].sourceId}).empty()
            && reachedOpen.contains(*sectorsOf(indoor, {clearMap.facets()[under.facetIndex].sourceId}).begin());

        if (!reached)
        {
            result.unreachableSpawns.push_back(spawnIndex);
        }
    }

    return result;
}

std::vector<AuditFinding> reachabilityFindings(const ReachabilityResult &result)
{
    std::vector<AuditFinding> findings;

    if (!result.ran)
    {
        return findings;
    }

    const auto list = [](const std::vector<size_t> &numbers)
    {
        std::string text;

        for (size_t index = 0; index < numbers.size() && index < 12; ++index)
        {
            text += (index == 0 ? "" : ", ") + std::to_string(numbers[index]);
        }

        return numbers.size() > 12 ? text + " and " + std::to_string(numbers.size() - 12) + " more" : text;
    };

    if (!result.unreachableSectors.empty())
    {
        findings.push_back({
            "reach.sector",
            "info",
            std::to_string(result.unreachableSectors.size()) + " of " + std::to_string(result.sectorsWithFloor)
                + " sectors with a floor are not reached on foot from the party start even with every door out of the "
                  "way: "
                + list(result.unreachableSectors)
                + (result.tooLowNotReached.empty() ? std::string()
                    : " (and " + std::to_string(result.tooLowNotReached.size()) + " lower than the party is tall, "
                        "not counted: " + list(result.tooLowNotReached) + ")"),
            "they need a teleport, a jump, a lift or flight; if none is meant, the way in is missing"});
    }

    for (size_t index = 0; index < result.stops.size() && index < 12; ++index)
    {
        const WalkStop &stop = result.stops[index];
        findings.push_back({
            "reach.stop",
            "info",
            "the walk stops at the opening from sector " + std::to_string(stop.fromSector) + " into sector "
                + std::to_string(stop.toSector) + " at " + pointText(stop.at[0], stop.at[1], stop.at[2]) + " (face "
                + std::to_string(stop.face) + "): " + stop.reason,
            result.stops.size() > 12 && index == 11
                ? "and " + std::to_string(result.stops.size() - 12) + " more openings (oymap solve --json lists them)"
                : "oymap probe between two points on either side says more"});
    }

    if (!result.unreachableSpawns.empty())
    {
        findings.push_back({
            "reach.spawn",
            "info",
            std::to_string(result.unreachableSpawns.size()) + " of " + std::to_string(result.spawnsTotal)
                + " spawn points are not reached on foot from the party start even with every door out of the way: "
                + list(result.unreachableSpawns),
            "monsters there cannot be fought on foot unless something else leads in"});
    }

    return findings;
}

std::set<uint32_t> facesTheGameIgnores(const Game::IndoorMapData &indoor)
{
    std::vector<bool> shut(indoor.sectors.size(), false);

    for (size_t sector = 1; sector < indoor.sectors.size(); ++sector)
    {
        shut[sector] = indoor.sectors[sector].floorFaceIds.empty() && indoor.sectors[sector].portalFaceIds.empty();
    }

    std::set<uint32_t> faces;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];
        const bool front = face.roomNumber < shut.size() && shut[face.roomNumber];
        const bool back = face.roomBehindNumber == 0
            || (face.roomBehindNumber < shut.size() && shut[face.roomBehindNumber]);

        if (!face.isPortal && front && back)
        {
            faces.insert(static_cast<uint32_t>(faceIndex));
        }
    }

    return faces;
}

std::vector<AuditFinding> strandedFindings(const SolveResult &solved, const std::map<int, std::string> &sectorRooms)
{
    std::vector<AuditFinding> findings;

    for (const SolveResult::Stranded &thing : solved.stranded)
    {
        const std::map<int, std::string>::const_iterator room = sectorRooms.find(static_cast<int>(thing.sector));
        findings.push_back({"reach.stranded", "warning",
            thing.kind + " " + std::to_string(thing.index) + (thing.name.empty() ? "" : " (" + thing.name + ")")
                + " at " + pointText(thing.at[0], thing.at[1], thing.at[2]) + " stands in sector "
                + std::to_string(thing.sector) + (room == sectorRooms.end() ? "" : " (" + room->second + ")")
                + ", which the solve never reaches: the party cannot get to it, nor it out to the party",
            "Put it on a floor the party walks (never in a shaft, chute, shelf or niche, where fliers stay too), or "
            "open a way in"});
    }

    return findings;
}

std::string probeWalk(
    const LoadedMap &map,
    const std::array<float, 3> &from,
    const std::array<float, 3> &to,
    bool doorsOpen)
{
    if (!map.indoor || !map.state)
    {
        return "the probe walks indoor maps with a scene\n";
    }

    const std::vector<Game::IndoorVertex> vertices =
        Game::buildIndoorMechanismAdjustedVertices(*map.indoor, &*map.state, nullptr);
    const Game::IndoorPathMapBuildResult built =
        Game::IndoorPathfindingBuilder::buildPathMap(*map.indoor, vertices, &*map.state);
    const Game::PathMap builtPath = withoutIgnoredFaces(built.pathMap, facesTheGameIgnores(*map.indoor));
    ClearedMaps clearMaps;

    if (doorsOpen)
    {
        buildClearedMaps(map, nullptr, nullptr, clearMaps);
    }

    const Game::PathMap &pathMap = doorsOpen ? clearMaps.all : builtPath;
    const Game::PathPoint source = {from[0], from[1], from[2]};
    const Game::PathPoint target = {to[0], to[1], to[2]};
    const Game::PathObject body = partyBody();
    static const char *const reasons[] = {
        "none", "invalid input", "no floor at the start", "the start is in the void", "no floor under a sample",
        "a sample is in the void", "a step is too high", "blocked by a face"};
    const auto describeFloor = [&pathMap, &map](const Game::PathFloorSample &floor)
    {
        if (!floor.hasFloor)
        {
            return std::string("no floor");
        }

        const int32_t faceId = floor.facetIndex < pathMap.facets().size()
            ? pathMap.facets()[floor.facetIndex].sourceId : -1;
        std::string text = "floor z " + std::to_string(static_cast<int>(std::lround(floor.z))) + ", face "
            + std::to_string(faceId);

        if (faceId >= 0 && static_cast<size_t>(faceId) < map.indoor->faces.size())
        {
            text += ", sector " + std::to_string(map.indoor->faces[static_cast<size_t>(faceId)].roomNumber);
        }

        return text;
    };

    std::string text;
    text += "path map: " + std::to_string(built.pathFacetCount) + " facets from "
        + std::to_string(built.sourceFaceCount) + " faces (" + std::to_string(built.skippedFaceCount)
        + " skipped), doors " + (doorsOpen ? "out of the way" : "as the map starts") + "\n";
    text += "from: " + describeFloor(pathMap.floorAt({source.x, source.y, source.z + body.stepHeight})) + "\n";
    text += "to:   " + describeFloor(pathMap.floorAt({target.x, target.y, target.z + body.stepHeight})) + "\n";
    const Game::PathWalkSegmentDebug segment = pathMap.debugTraceWalkSegment(source, target, body);
    text += std::string("straight walk: ") + (segment.success ? "possible" : "not possible: ")
        + (segment.success ? "" : reasons[static_cast<size_t>(segment.rejectReason)]) + "\n";

    if (!segment.success)
    {
        text += "  at sample " + std::to_string(segment.sampleIndex) + " of " + std::to_string(segment.sampleCount)
            + ", point (" + std::to_string(static_cast<int>(std::lround(segment.probe.x))) + ", "
            + std::to_string(static_cast<int>(std::lround(segment.probe.y))) + ", "
            + std::to_string(static_cast<int>(std::lround(segment.probe.z))) + "), step "
            + std::to_string(static_cast<int>(std::lround(segment.stepDeltaZ))) + "\n";

        if (segment.blockedFacet < pathMap.facets().size())
        {
            const Game::PathFacet &facet = pathMap.facets()[segment.blockedFacet];
            text += "  blocking face " + std::to_string(facet.sourceId) + (facet.dynamic ? " (a door's)" : "");

            if (facet.sourceId >= 0 && static_cast<size_t>(facet.sourceId) < map.indoor->faces.size())
            {
                const Game::IndoorFace &face = map.indoor->faces[static_cast<size_t>(facet.sourceId)];
                text += ", texture " + face.textureName + ", attributes " + std::to_string(face.attributes)
                    + (face.isPortal ? ", a portal" : "") + ", sector " + std::to_string(face.roomNumber)
                    + ", event " + std::to_string(face.cogTriggered);
            }

            text += "\n";

            // A floor the body stands on, beside its lower sphere: a step at a ramp's foot or off its top end.
            if (facet.walkableFloor)
            {
                text += "  that face is a floor the party stands on (a slope): the game's party steps onto it and off "
                    "it where the floors lie within a step (" + std::to_string(static_cast<int>(body.stepHeight))
                    + ") of each other, and solve and audit --reach take such a step; this straight walk and the "
                    "planner below do not\n";
            }
        }
    }

    // The path map's walk takes the floor under a point every two units and so falls into every slot; the game's
    // party strides over a gap (WidestGapCrossed), and solve and audit --reach with it. Say so where that is the
    // difference: the widest stretch of the line without a floor at the height walked on.
    if (!segment.success && (segment.rejectReason == Game::PathWalkRejectReason::StepHeight
            || segment.rejectReason == Game::PathWalkRejectReason::SampleNoFloor
            || segment.rejectReason == Game::PathWalkRejectReason::SampleVoid))
    {
        const float length = std::sqrt((target.x - source.x) * (target.x - source.x)
            + (target.y - source.y) * (target.y - source.y));
        float walkedZ = source.z;
        float gapStart = -1.0f;
        float widest = 0.0f;
        bool endsOnFloor = false;

        for (float distance = 0.0f; length > 0.0f && distance <= length; distance += 2.0f)
        {
            float height = 0.0f;
            endsOnFloor = supportAt(pathMap, source.x + (target.x - source.x) * distance / length,
                source.y + (target.y - source.y) * distance / length, walkedZ, body, height);

            if (endsOnFloor)
            {
                // From the last sample with a floor to this one.
                widest = gapStart >= 0.0f ? std::max(widest, distance - gapStart + 2.0f) : widest;
                gapStart = -1.0f;
                walkedZ = height;
            }
            else if (gapStart < 0.0f)
            {
                gapStart = distance;
            }
        }

        if (widest > 0.0f && endsOnFloor && gapStart < 0.0f)
        {
            text += "  the floor along the line has a gap " + std::to_string(static_cast<int>(std::lround(widest)))
                + " wide at most: " + (widest <= WidestGapCrossed
                    ? "the game's party strides over it at a walk (up to "
                        + std::to_string(static_cast<int>(WidestGapCrossed))
                        + "), and solve and audit --reach cross it; this walk and the planner below do not"
                    : "too wide to stride over at a walk ("
                        + std::to_string(static_cast<int>(WidestGapCrossed)) + ")")
                + "\n";
        }
    }

    Game::PathPlanRequest request;
    request.source = source;
    request.target = target;
    request.object = body;
    request.nodeLimit = 40000;
    request.sourceSnapDistance = 96.0f;
    request.goalDistance = 96.0f;
    request.allowPartialPath = true;
    request.mapRevision = static_cast<uint32_t>(pathMap.revision());
    Game::PathPlanner planner;
    const Game::PathPlanResult plan = planner.plan(pathMap, request);
    static const char *const statuses[] = {"not requested", "route found", "partial route", "no route",
        "node limit reached", "stale"};
    text += std::string("planner: ") + statuses[static_cast<size_t>(plan.status)] + ", "
        + std::to_string(plan.waypoints.size()) + " waypoints, " + std::to_string(plan.analyzedNodeCount) + " nodes";

    if (!plan.waypoints.empty())
    {
        const Game::PathPoint &last = plan.waypoints.back();
        text += ", ends at (" + std::to_string(static_cast<int>(std::lround(last.x))) + ", "
            + std::to_string(static_cast<int>(std::lround(last.y))) + ", "
            + std::to_string(static_cast<int>(std::lround(last.z))) + ")";
    }

    text += "\n";

    // The planner calls a route found when it ends within its goal distance of the target (96, as the scenario
    // walker asks): a route that stops short of a step or a wall in front of the target is "found" all the same.
    // Say where it ends and whether the rest is walked.
    if (plan.waypoints.empty())
    {
        text += "target reached: no\n";
    }
    else
    {
        const Game::PathPoint &last = plan.waypoints.back();
        const Game::PathFloorSample targetFloor = pathMap.floorAt({target.x, target.y, target.z + body.stepHeight});
        const float short2d = std::sqrt((last.x - target.x) * (last.x - target.x)
            + (last.y - target.y) * (last.y - target.y));
        const float targetZ = targetFloor.hasFloor && !targetFloor.inVoid ? targetFloor.z : target.z;
        const bool there = short2d <= 1.0f && std::abs(last.z - targetZ) <= body.stepHeight;

        if (plan.status == Game::PathPlanStatus::Success && there)
        {
            text += "target reached: yes\n";
        }
        else
        {
            const Game::PathWalkSegmentDebug rest =
                pathMap.debugTraceWalkSegment(last, {target.x, target.y, targetZ}, body);
            const std::string shortText = std::to_string(static_cast<int>(std::lround(short2d)));
            text += rest.success
                ? "target reached: yes, by a straight walk over the last " + shortText
                    + " from where the route ends\n"
                : "target reached: no: the route ends " + shortText + " short of it"
                    + (std::abs(last.z - targetZ) > 1.0f
                            ? " and " + std::to_string(static_cast<int>(std::lround(std::abs(last.z - targetZ))))
                                + (last.z > targetZ ? " above" : " below") + " its floor"
                            : std::string())
                    + ", and the rest is not walked: " + reasons[static_cast<size_t>(rest.rejectReason)]
                    + (rest.rejectReason == Game::PathWalkRejectReason::StepHeight
                            ? " (" + std::to_string(static_cast<int>(std::lround(rest.stepDeltaZ))) + ")"
                            : std::string())
                    + (rest.rejectReason == Game::PathWalkRejectReason::Blocked
                                && rest.blockedFacet < pathMap.facets().size()
                            ? " (face " + std::to_string(pathMap.facets()[rest.blockedFacet].sourceId) + ")"
                            : std::string())
                    + " at (" + std::to_string(static_cast<int>(std::lround(rest.probe.x))) + ", "
                    + std::to_string(static_cast<int>(std::lround(rest.probe.y))) + ", "
                    + std::to_string(static_cast<int>(std::lround(rest.probe.z))) + ")\n";
        }
    }

    return text;
}

SolveResult solveMap(const LoadedMap &map, const std::string &eventFlowJson, WalkSteps *pSteps)
{
    SolveResult result;

    if (!map.indoor || !map.state)
    {
        result.skipped = "the solve walks indoor maps with a scene";
        return result;
    }

    std::optional<Game::IndoorPartyStartPoint> start = map.indoor->partyStartPoint;

    if (map.indoorScene && !map.indoorScene->partyStartPoints.empty())
    {
        start = map.indoorScene->partyStartPoints.front().startPoint;
    }

    if (!start)
    {
        result.skipped = "the map has no party start";
        return result;
    }

    const Game::IndoorMapData &indoor = *map.indoor;
    const YAML::Node events = YAML::Load(eventFlowJson);
    // Event number to the sectors it can be used from.
    std::map<int, std::set<size_t>> sectorsByEvent;

    for (const Game::IndoorFace &face : indoor.faces)
    {
        if (face.cogTriggered == 0)
        {
            continue;
        }

        // Used from the sector in front of it: a door's leaf belongs to the sector its doorway is filed in, and a
        // leaf whose events are bound to one side each (wiring `side`) is used from that side's room only (the
        // Hive's door 4 was listed as used from the crossing, where the use key finds nothing on that face).
        std::optional<int16_t> front;

        if (face.vertexIndices.size() >= 3)
        {
            std::array<double, 3> normal = {0.0, 0.0, 0.0};
            std::array<double, 3> middle = {0.0, 0.0, 0.0};
            const size_t count = face.vertexIndices.size();

            for (size_t index = 0; index < count; ++index)
            {
                const Game::IndoorVertex &current = indoor.vertices[face.vertexIndices[index]];
                const Game::IndoorVertex &next = indoor.vertices[face.vertexIndices[(index + 1) % count]];
                normal[0] += (double(current.y) - next.y) * (double(current.z) + next.z);
                normal[1] += (double(current.z) - next.z) * (double(current.x) + next.x);
                normal[2] += (double(current.x) - next.x) * (double(current.y) + next.y);
                middle[0] += double(current.x) / double(count);
                middle[1] += double(current.y) / double(count);
                middle[2] += double(current.z) / double(count);
            }

            const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

            if (length > 1.0e-6 && std::fabs(normal[2]) < 0.7 * length)
            {
                front = Game::findIndoorSectorForPoint(indoor, indoor.vertices,
                    {float(middle[0] + normal[0] / length * 24.0), float(middle[1] + normal[1] / length * 24.0),
                        float(middle[2])}, nullptr, false);
            }
        }

        sectorsByEvent[face.cogTriggered].insert(
            front && *front > 0 ? static_cast<size_t>(*front) : static_cast<size_t>(face.roomNumber));

        if (face.roomBehindNumber != 0)
        {
            sectorsByEvent[face.cogTriggered].insert(face.roomBehindNumber);
        }
    }

    // The faces each event is bound to, for a face that is clicked from a sector it does not belong to (a door's
    // leaf belongs to the room its doorway is part of, and is clicked from the other room too).
    std::map<int, std::vector<size_t>> facesByEvent;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        if (indoor.faces[faceIndex].cogTriggered != 0)
        {
            facesByEvent[indoor.faces[faceIndex].cogTriggered].push_back(faceIndex);
        }
    }

    const std::vector<Game::IndoorVertex> startVertices =
        Game::buildIndoorMechanismAdjustedVertices(indoor, &*map.state, nullptr);
    const std::set<uint32_t> noDoors;
    ClearedMaps startMaps;
    buildClearedMaps(map, &noDoors, nullptr, startMaps);
    const Game::PathMap &startMap = startMaps.all;
    // A decoration is used from the sector whose floor it stands on.
    for (const Game::IndoorEntity &entity : indoor.entities)
    {
        if (entity.scriptEventId() == 0)
        {
            continue;
        }

        const Game::PathFloorSample under = startMap.floorAt(
            {static_cast<float>(entity.x), static_cast<float>(entity.y), static_cast<float>(entity.z) + 32.0f});

        if (under.hasFloor && under.facetIndex < startMap.facets().size())
        {
            const std::set<size_t> sectors = sectorsOf(indoor, {startMap.facets()[under.facetIndex].sourceId});
            sectorsByEvent[entity.scriptEventId()].insert(sectors.begin(), sectors.end());
        }
    }

    // A destructible's `on_destroyed` runs when the party breaks it (a blow or a missile): from the sector whose floor
    // lies under its centre.
    for (const Game::IndoorDestructible &thing :
        map.indoorScene ? map.indoorScene->destructibles : std::vector<Game::IndoorDestructible>())
    {
        if (thing.destroyedEvent == 0)
        {
            continue;
        }

        const Game::PathFloorSample under = startMap.floorAt({thing.center[0], thing.center[1], thing.center[2]});

        if (under.hasFloor && under.facetIndex < startMap.facets().size())
        {
            const std::set<size_t> sectors = sectorsOf(indoor, {startMap.facets()[under.facetIndex].sourceId});
            sectorsByEvent[thing.destroyedEvent].insert(sectors.begin(), sectors.end());
        }
    }
    // Events the engine runs by itself.
    std::set<int> always;

    if (map.events)
    {
        always.insert(map.events->onLoadEventIds().begin(), map.events->onLoadEventIds().end());

        for (const Game::ScriptedEventProgram::TimerTrigger &timer : map.events->timerTriggers())
        {
            always.insert(timer.eventId);
        }
    }

    std::set<size_t> withFloor;

    for (size_t sectorIndex = 0; sectorIndex < indoor.sectors.size(); ++sectorIndex)
    {
        Game::PathPoint point;

        if (sectorFloorPoint(indoor, indoor.vertices, indoor.sectors[sectorIndex], point))
        {
            withFloor.insert(sectorIndex);
        }
    }

    result.sectorsWithFloor = withFloor.size();
    result.ran = true;
    std::set<uint32_t> clearedDoors;
    std::vector<Game::PathPoint> seeds = {
        {static_cast<float>(start->x), static_cast<float>(start->y), static_cast<float>(start->z)}};
    std::set<size_t> reached;
    std::set<std::string> exits;
    SolveWave pending;
    std::map<uint32_t, std::vector<int>> itemsByContainer;

    if (map.indoorScene)
    {
        for (const Game::MapLootContainerSource &container : map.indoorScene->itemSources.lootContainers)
        {
            for (const Game::MapFixedContainerItem &item : container.fixedItems)
            {
                itemsByContainer[container.containerId].push_back(static_cast<int>(item.itemId));
            }
        }
    }

    // What one path through a handler gives the party in items.
    const auto itemsGivenBy = [&itemsByContainer](const YAML::Node &path)
    {
        std::vector<int> items;

        for (const YAML::Node &effectNode : path["effects"])
        {
            const std::string &effect = effectNode.Scalar();

            if (effect.starts_with("give item "))
            {
                items.push_back(std::stoi(effect.substr(10)));
            }
            else if (effect.starts_with("open chest "))
            {
                const std::map<uint32_t, std::vector<int>>::const_iterator held =
                    itemsByContainer.find(static_cast<uint32_t>(std::stoul(effect.substr(11))));

                if (held != itemsByContainer.end())
                {
                    items.insert(items.end(), held->second.begin(), held->second.end());
                }
            }
        }

        return items;
    };

    // Items the map itself can give: a test on one of them waits until the party has it. Any other item is
    // taken to come from elsewhere.
    std::set<int> mapItems;

    for (const YAML::Node &event : events)
    {
        for (const YAML::Node &path : event["paths"])
        {
            for (const int itemId : itemsGivenBy(path))
            {
                mapItems.insert(itemId);
            }
        }
    }

    // And what placed monsters carry (objects.yml `monsters[].carries`).
    for (const Game::MapDeltaActor &actor : map.state->actors)
    {
        if (actor.carriedItemId != 0)
        {
            mapItems.insert(static_cast<int>(actor.carriedItemId));
        }
    }

    // And items lying on the map (objects.yml `items`; the shipped maps' sprite objects holding an item): each with
    // the sector of the floor under it, the party's once it reaches that sector (XD-04's Alacorn on its pedestal).
    std::vector<std::pair<int, size_t>> lyingItems;

    for (const Game::MapDeltaSpriteObject &object : map.state->spriteObjects)
    {
        if (object.rawContainingItem.size() < 4)
        {
            continue;
        }

        const int itemId = static_cast<int>(object.rawContainingItem[0] | (object.rawContainingItem[1] << 8)
            | (object.rawContainingItem[2] << 16) | (static_cast<uint32_t>(object.rawContainingItem[3]) << 24));

        if (itemId <= 0)
        {
            continue;
        }

        size_t sector = static_cast<size_t>(std::max<int16_t>(0, object.sectorId));
        const Game::PathFloorSample under = startMap.floorAt(
            {static_cast<float>(object.x), static_cast<float>(object.y), static_cast<float>(object.z) + 32.0f});

        if (under.hasFloor && under.facetIndex < startMap.facets().size())
        {
            const std::set<size_t> sectors = sectorsOf(indoor, {startMap.facets()[under.facetIndex].sourceId});
            sector = sectors.empty() ? sector : *sectors.begin();
        }

        mapItems.insert(itemId);
        lyingItems.push_back({itemId, sector});
    }

    std::set<int> haveItems;
    std::set<std::pair<int, size_t>> usedPaths;
    std::set<std::string> said;
    // What the events used so far have made of the map's variables and of the party's quest bits, awards and
    // autonotes. A branch of a handler that tests one of these is taken only once an event the party can use has
    // set it: a map variable must have been raised to the value tested; a bit some event of this map sets must have
    // been set (a bit no event of the map sets comes from elsewhere, and the step lists it as needed).
    std::map<std::string, double> variableReached;
    std::set<std::string> variablesSetByMap;
    std::set<std::string> bitsSet;
    std::set<std::string> bitsSetByMap;

    for (size_t index = 0; index < map.state->eventVariables.mapVars.size(); ++index)
    {
        if (map.state->eventVariables.mapVars[index] != 0)
        {
            variableReached["map_var " + std::to_string(index)] = map.state->eventVariables.mapVars[index];
        }
    }

    // "set map_var 3 = 1", "add map_var 3 + 1", "set qbit 12": what an effect does to them. Gives the name, and for a
    // variable the value set (`adds`: added).
    const auto stateEffect = [](const std::string &effect, std::string &name, double &value, bool &adds)
    {
        const bool sets = effect.starts_with("set ");
        adds = effect.starts_with("add ");

        if (!sets && !adds)
        {
            return false;
        }

        const std::string rest = effect.substr(4);

        if (rest.starts_with("map_var "))
        {
            const size_t mark = rest.find(adds ? " + " : " = ");

            if (mark == std::string::npos)
            {
                return false;
            }

            name = rest.substr(0, mark);
            value = std::atof(rest.c_str() + mark + 3);
            return true;
        }

        if (sets && (rest.starts_with("qbit ") || rest.starts_with("award ") || rest.starts_with("autonote ")))
        {
            name = rest;
            value = 1.0;
            return true;
        }

        return false;
    };

    for (const YAML::Node &event : events)
    {
        for (const YAML::Node &path : event["paths"])
        {
            for (const YAML::Node &effectNode : path["effects"])
            {
                std::string name;
                double value = 0.0;
                bool adds = false;

                if (stateEffect(effectNode.Scalar(), name, value, adds))
                {
                    (name.starts_with("map_var ") ? variablesSetByMap : bitsSetByMap).insert(name);
                }
            }
        }
    }

    // The sector each actor of the starting state stands in (by the floor under it, else its record's sector), and
    // the sector of each monster spawn point: a test that monsters are dead waits until the party reaches them.
    std::vector<size_t> actorSectors;

    for (const Game::MapDeltaActor &actor : map.state->actors)
    {
        const Game::PathFloorSample under = startMap.floorAt(
            {static_cast<float>(actor.x), static_cast<float>(actor.y), static_cast<float>(actor.z) + 32.0f});
        size_t sector = static_cast<size_t>(std::max<int16_t>(0, actor.sectorId));

        if (under.hasFloor && under.facetIndex < startMap.facets().size())
        {
            const std::set<size_t> sectors = sectorsOf(indoor, {startMap.facets()[under.facetIndex].sourceId});
            sector = sectors.empty() ? sector : *sectors.begin();
        }

        actorSectors.push_back(sector);
    }

    std::vector<size_t> spawnSectors;

    for (const Game::IndoorSpawn &spawn : indoor.spawns)
    {
        const Game::PathFloorSample under = startMap.floorAt(
            {static_cast<float>(spawn.x), static_cast<float>(spawn.y), static_cast<float>(spawn.z) + 32.0f});

        if (spawn.typeId == 3 && under.hasFloor && under.facetIndex < startMap.facets().size())
        {
            const std::set<size_t> sectors = sectorsOf(indoor, {startMap.facets()[under.facetIndex].sourceId});
            spawnSectors.insert(spawnSectors.end(), sectors.begin(), sectors.end());
        }
    }

    // "CheckMonstersKilled(1, 56, 0, false)" (game/events: ActorKillCheck Any 0, Group 1, MonsterId 2, ActorIdOe 3,
    // UniqueNameId 4, Hostile 5): the sectors of the monsters it counts that the party has not reached.
    const auto killsWaitFor = [&](const std::string &what) -> std::string
    {
        int kind = 0;
        int id = 0;

        if (std::sscanf(what.c_str(), "CheckMonstersKilled(%d, %d", &kind, &id) != 2)
        {
            return {};
        }

        std::set<size_t> missing;

        for (size_t index = 0; index < map.state->actors.size(); ++index)
        {
            const Game::MapDeltaActor &actor = map.state->actors[index];
            const bool counted = kind == 0 || kind == 5 || (kind == 1 && static_cast<int>(actor.group) == id)
                || (kind == 2 && actor.monsterInfoId == id) || (kind == 3 && static_cast<int>(index) == id)
                || (kind == 4 && actor.uniqueNameIndex == id);

            if (counted && !reached.contains(actorSectors[index]))
            {
                missing.insert(actorSectors[index]);
            }
        }

        if (kind == 0 || kind == 5)
        {
            for (const size_t sector : spawnSectors)
            {
                if (!reached.contains(sector))
                {
                    missing.insert(sector);
                }
            }
        }

        if (missing.empty())
        {
            return {};
        }

        std::string sectors;

        for (const size_t sector : missing)
        {
            sectors += (sectors.empty() ? "" : ", ") + std::to_string(sector);
        }

        return "the monsters it counts dead (" + what + ") stand in sector" + (missing.size() > 1 ? "s " : " ")
            + sectors + ", not reached yet";
    };

    // What a test that came out "yes" on a path still waits for; empty when it can be met.
    const auto testWaitsFor = [&](const std::string &what) -> std::string
    {
        if (what.starts_with("CheckMonstersKilled("))
        {
            return killsWaitFor(what);
        }

        if (what.starts_with("map_var "))
        {
            const size_t mark = what.find(" >= ");

            if (mark == std::string::npos)
            {
                return {};
            }

            const std::string name = what.substr(0, mark);
            const std::map<std::string, double>::const_iterator reachedValue = variableReached.find(name);

            const double reachedSoFar = reachedValue == variableReached.end() ? 0.0 : reachedValue->second;

            if (reachedSoFar >= std::atof(what.c_str() + mark + 4))
            {
                return {};
            }

            return what + (variablesSetByMap.contains(name) ? " (set only by events not used yet)"
                : " (no event of the map sets it)");
        }

        if ((what.starts_with("qbit ") || what.starts_with("award ") || what.starts_with("autonote "))
            && bitsSetByMap.contains(what) && !bitsSet.contains(what))
        {
            return what + " (set only by events not used yet)";
        }

        return {};
    };
    // Faces an event has switched off (evt.SetFacetBit with the untouchable bit): they no longer block.
    std::set<uint32_t> passableFaces;
    // How much of each sector the walk has stood on so far, in grid cells: a wave that opens no new sector may
    // still open more of one (a gate across a room).
    constexpr size_t ClearlyMoreCells = 24;
    std::map<size_t, size_t> cellsOfSector;
    ClearedMaps lastMaps;
    std::vector<WalkCell> lastCells;
    // Events used from in front of one of their faces, from a sector they are not bound in.
    std::set<int> usedFromInFront;
    // The walk's steps, kept from round to round where the faces near them stay as they were.
    WalkSteps ownSteps;
    WalkCache &walkCache = (pSteps != nullptr ? *pSteps : ownSteps).kept().cache;

    for (int round = 0; round < 64; ++round)
    {
        ClearedMaps maps;
        buildClearedMaps(map, &clearedDoors, &passableFaces, maps);
        size_t cells = 0;
        std::vector<WalkCell> walked;
        std::set<size_t> now = sectorsOf(indoor, floodWalkWithRides(maps, seeds, cells, &walked, walkCache));
        // A sector the body walks into though no grid point of the walk falls on its floor (a rim round a hole) is
        // reached too.
        std::set<size_t> stoodOrReached = reached;
        stoodOrReached.insert(now.begin(), now.end());
        std::set<size_t> notStood;

        for (const size_t sector : withFloor)
        {
            if (!stoodOrReached.contains(sector))
            {
                notStood.insert(sector);
            }
        }

        for (const WalkStop &stop : findWalkStops(map, maps, walked, stoodOrReached, notStood, {}))
        {
            if (stop.passes)
            {
                now.insert(stop.toSector);
            }
        }

        SolveWave wave = pending;
        pending = {};
        std::map<size_t, size_t> cellsNow;

        for (const WalkCell &cell : walked)
        {
            if (cell.face >= 0 && static_cast<size_t>(cell.face) < indoor.faces.size())
            {
                ++cellsNow[indoor.faces[static_cast<size_t>(cell.face)].roomNumber];
            }
        }

        for (const size_t sector : now)
        {
            if (!withFloor.contains(sector))
            {
                continue;
            }

            if (reached.insert(sector).second)
            {
                wave.sectors.push_back(sector);
            }
            else if (cellsNow[sector] >= cellsOfSector[sector] + ClearlyMoreCells)
            {
                wave.extended.push_back({sector, cellsNow[sector] - cellsOfSector[sector]});
            }

            cellsOfSector[sector] = std::max(cellsOfSector[sector], cellsNow[sector]);
        }

        if (!wave.sectors.empty() || !wave.extended.empty() || round == 0)
        {
            result.waves.push_back(wave);
        }

        lastMaps = std::move(maps);
        lastCells = std::move(walked);
        // The places stood on, by squares of 128, to find those in front of a face.
        std::map<std::pair<long, long>, std::vector<size_t>> cellsBySquare;

        for (size_t cellIndex = 0; cellIndex < lastCells.size(); ++cellIndex)
        {
            cellsBySquare[{std::lround(std::floor(lastCells[cellIndex].point.x / 128.0f)),
                std::lround(std::floor(lastCells[cellIndex].point.y / 128.0f))}].push_back(cellIndex);
        }

        // Whether the party can stand in front of a face of an event and use it: a place stood on within reach of
        // the face, on its seen side, nothing between. The reach is that of a party standing at the face (the
        // game's own click distance was not looked up: this errs on the near side). Gives the sector stood in.
        std::map<int, int> standingSectorOfEvent;
        const auto standsAtEvent = [&](int eventId) -> int
        {
            constexpr float ClickReach = 160.0f;
            constexpr float EyeHeight = 96.0f;
            const std::map<int, int>::const_iterator known = standingSectorOfEvent.find(eventId);

            if (known != standingSectorOfEvent.end())
            {
                return known->second;
            }

            int standing = -1;
            const std::map<int, std::vector<size_t>>::const_iterator bound = facesByEvent.find(eventId);

            for (size_t boundIndex = 0; bound != facesByEvent.end() && boundIndex < bound->second.size()
                 && standing < 0; ++boundIndex)
            {
                const Game::IndoorFace &face = indoor.faces[bound->second[boundIndex]];
                std::array<float, 3> normal = {0.0f, 0.0f, 0.0f};
                Game::PathPoint middle = {0.0f, 0.0f, 0.0f};
                std::vector<Game::PathPoint> corners;

                for (size_t index = 0; index < face.vertexIndices.size(); ++index)
                {
                    const Game::IndoorVertex &current = startVertices[face.vertexIndices[index]];
                    const Game::IndoorVertex &next =
                        startVertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
                    normal[0] += static_cast<float>(current.y - next.y) * static_cast<float>(current.z + next.z);
                    normal[1] += static_cast<float>(current.z - next.z) * static_cast<float>(current.x + next.x);
                    normal[2] += static_cast<float>(current.x - next.x) * static_cast<float>(current.y + next.y);
                    corners.push_back({static_cast<float>(current.x), static_cast<float>(current.y),
                        static_cast<float>(current.z)});
                    const float count = static_cast<float>(face.vertexIndices.size());
                    middle.x += current.x / count;
                    middle.y += current.y / count;
                    middle.z += current.z / count;
                }

                const float length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

                if (corners.size() < 3 || length < 1.0e-3f)
                {
                    continue;
                }

                // The face's middle and the points half way to its corners.
                std::vector<Game::PathPoint> samples = {middle};

                for (const Game::PathPoint &corner : corners)
                {
                    samples.push_back({(middle.x + corner.x) * 0.5f, (middle.y + corner.y) * 0.5f,
                        (middle.z + corner.z) * 0.5f});
                }

                for (size_t sampleIndex = 0; sampleIndex < samples.size() && standing < 0; ++sampleIndex)
                {
                    const Game::PathPoint &sample = samples[sampleIndex];
                    const Game::PathPoint front = {sample.x + normal[0] / length * 2.0f,
                        sample.y + normal[1] / length * 2.0f, sample.z + normal[2] / length * 2.0f};
                    const long squareX = std::lround(std::floor(sample.x / 128.0f));
                    const long squareY = std::lround(std::floor(sample.y / 128.0f));

                    for (long offsetY = -2; offsetY <= 2 && standing < 0; ++offsetY)
                    {
                        for (long offsetX = -2; offsetX <= 2 && standing < 0; ++offsetX)
                        {
                            const std::map<std::pair<long, long>, std::vector<size_t>>::const_iterator square =
                                cellsBySquare.find({squareX + offsetX, squareY + offsetY});

                            if (square == cellsBySquare.end())
                            {
                                continue;
                            }

                            for (const size_t cellIndex : square->second)
                            {
                                const WalkCell &cell = lastCells[cellIndex];
                                const Game::PathPoint eye = {cell.point.x, cell.point.y, cell.point.z + EyeHeight};
                                const float toX = eye.x - sample.x;
                                const float toY = eye.y - sample.y;
                                const float toZ = eye.z - sample.z;

                                if (cell.face < 0 || toX * toX + toY * toY + toZ * toZ > ClickReach * ClickReach
                                    || (toX * normal[0] + toY * normal[1] + toZ * normal[2]) / length < 1.0f
                                    || lastMaps.all.traceLine(eye, front, 0.0f, false).blocked)
                                {
                                    continue;
                                }

                                standing = static_cast<int>(indoor.faces[static_cast<size_t>(cell.face)].roomNumber);
                                break;
                            }
                        }
                    }
                }
            }

            standingSectorOfEvent[eventId] = standing;
            return standing;
        };

        // Use every path of every usable event whose item tests the party can meet; what a path gives may let
        // another be used in the same round.
        bool opened = false;
        bool progressed = true;

        // An item a placed monster carries is the party's once it reaches the monster's sector (it drops it or
        // leaves it in its corpse: XD-03's King and his key).
        for (const Game::MapDeltaActor &actor : map.state->actors)
        {
            if (actor.carriedItemId != 0 && actor.sectorId >= 0 && reached.contains(static_cast<size_t>(actor.sectorId))
                && haveItems.insert(static_cast<int>(actor.carriedItemId)).second)
            {
                result.notes.push_back("item " + std::to_string(actor.carriedItemId) + " is carried by the monster "
                    + actor.name + " in sector " + std::to_string(actor.sectorId) + ", reached: the party has it");
            }
        }

        for (const std::pair<int, size_t> &item : lyingItems)
        {
            if (reached.contains(item.second) && haveItems.insert(item.first).second)
            {
                result.notes.push_back("item " + std::to_string(item.first) + " lies on the floor in sector "
                    + std::to_string(item.second) + ", reached: the party has it");
            }
        }

        while (progressed)
        {
            progressed = false;

            for (const YAML::Node &event : events)
            {
                const int eventId = event["event"].as<int>();
                size_t fromSector = 0;
                bool usable = always.contains(eventId);
                const std::map<int, std::set<size_t>>::const_iterator bound = sectorsByEvent.find(eventId);

                if (bound != sectorsByEvent.end())
                {
                    for (const size_t sector : bound->second)
                    {
                        if (reached.contains(sector))
                        {
                            usable = true;
                            fromSector = sector;
                            break;
                        }
                    }
                }

                // Not from a sector it is bound in: from in front of one of its faces, then.
                int clickedFrom = -1;

                if (!usable)
                {
                    clickedFrom = standsAtEvent(eventId);

                    if (clickedFrom < 0)
                    {
                        continue;
                    }

                    usedFromInFront.insert(eventId);

                    fromSector = bound != sectorsByEvent.end() && !bound->second.empty() ? *bound->second.begin() : 0;
                }

                const std::string label = "event " + std::to_string(eventId)
                    + (event["title"].Scalar().empty() ? std::string() : " (" + event["title"].Scalar() + ")")
                    + (clickedFrom >= 0
                            ? " in sector " + std::to_string(fromSector) + ", used from sector "
                                + std::to_string(clickedFrom)
                            : fromSector != 0 ? " in sector " + std::to_string(fromSector) : " (run by the map)");
                size_t pathIndex = 0;

                for (const YAML::Node &path : event["paths"])
                {
                    const std::pair<int, size_t> pathKey = {eventId, pathIndex++};

                    if (usedPaths.contains(pathKey))
                    {
                        continue;
                    }

                    std::vector<std::string> needs;
                    bool waits = false;

                    for (const YAML::Node &test : path["tests"])
                    {
                        const std::string &what = test["what"].Scalar();

                        if (test["taken"].Scalar() != "true")
                        {
                            continue;
                        }

                        if (what.starts_with("item "))
                        {
                            const int itemId = std::stoi(what.substr(5));
                            needs.push_back(what);

                            if (mapItems.contains(itemId) && !haveItems.contains(itemId))
                            {
                                waits = true;
                            }
                            else if (!mapItems.contains(itemId))
                            {
                                const std::string note = what + " (needed by " + label
                                    + ") is not given or held in a chest on this map: it comes from elsewhere";

                                if (said.insert(note).second)
                                {
                                    result.notes.push_back(note);
                                }
                            }
                        }
                        else if (what.starts_with("qbit ") || what.starts_with("award "))
                        {
                            needs.push_back(what);
                        }

                        waits = waits || !testWaitsFor(what).empty();
                    }

                    if (waits)
                    {
                        continue;
                    }

                    usedPaths.insert(pathKey);

                    for (const int itemId : itemsGivenBy(path))
                    {
                        progressed = haveItems.insert(itemId).second || progressed;
                    }

                    for (const YAML::Node &effectNode : path["effects"])
                    {
                        std::string name;
                        double value = 0.0;
                        bool adds = false;

                        if (!stateEffect(effectNode.Scalar(), name, value, adds))
                        {
                            continue;
                        }

                        if (!name.starts_with("map_var "))
                        {
                            progressed = bitsSet.insert(name).second || progressed;
                        }
                        else if (adds ? value > 0.0 : value > variableReached[name])
                        {
                            variableReached[name] = adds ? variableReached[name] + value : value;
                            progressed = true;
                        }
                    }

                    for (const YAML::Node &effectNode : path["effects"])
                    {
                        const std::string &effect = effectNode.Scalar();
                        bool opens = false;

                        if (effect.starts_with("door "))
                        {
                            const uint32_t doorId = static_cast<uint32_t>(std::stoul(effect.substr(5)));

                            if (clearedDoors.insert(doorId).second)
                            {
                                pending.causes.push_back(label + ": " + effect);
                                opens = true;
                            }
                        }
                        else if (effect.starts_with("teleport to "))
                        {
                            float x = 0.0f;
                            float y = 0.0f;
                            float z = 0.0f;

                            if (std::sscanf(effect.c_str(), "teleport to %f, %f, %f", &x, &y, &z) == 3)
                            {
                                seeds.push_back({x, y, z});
                                pending.causes.push_back(label + ": " + effect);
                                opens = true;
                            }
                        }
                        else if (effect.starts_with("leave to "))
                        {
                            exits.insert(effect.substr(9));
                        }
                        else if (effect.starts_with("SetFacetBit("))
                        {
                            std::string switched;

                            for (const uint32_t faceIndex : facesMadePassable(indoor, effect))
                            {
                                if (passableFaces.insert(faceIndex).second)
                                {
                                    switched += (switched.empty() ? "" : ", ") + std::to_string(faceIndex);
                                }
                            }

                            if (!switched.empty())
                            {
                                pending.causes.push_back(label + ": " + effect + " (face " + switched
                                    + " no longer blocks)");
                                opens = true;
                            }
                        }

                        if (opens)
                        {
                            opened = true;

                            for (const std::string &need : needs)
                            {
                                if (std::find(pending.needs.begin(), pending.needs.end(), need)
                                    == pending.needs.end())
                                {
                                    pending.needs.push_back(need);
                                }
                            }
                        }
                    }
                }
            }
        }

        if (!opened)
        {
            break;
        }
    }

    std::set<size_t> unreached;

    for (const size_t sector : withFloor)
    {
        if (reached.contains(sector))
        {
            continue;
        }

        unreached.insert(sector);

        if (sectorIsNiche(indoor, indoor.sectors[sector]))
        {
            result.nichesNotReached.push_back(sector);
        }
        else
        {
            result.neverReached.push_back(sector);
        }
    }

    // Monsters and spawn points in sectors never reached (in a niche too: nothing walks out of one).
    for (size_t index = 0; index < map.state->actors.size(); ++index)
    {
        const Game::MapDeltaActor &actor = map.state->actors[index];

        if (!reached.contains(actorSectors[index]))
        {
            result.stranded.push_back({"monster", index, actor.name, {actor.x, actor.y, actor.z}, actorSectors[index]});
        }
    }

    for (size_t index = 0; index < indoor.spawns.size(); ++index)
    {
        const Game::IndoorSpawn &spawn = indoor.spawns[index];
        const Game::PathFloorSample under = startMap.floorAt(
            {static_cast<float>(spawn.x), static_cast<float>(spawn.y), static_cast<float>(spawn.z) + 32.0f});

        if (spawn.typeId != 3 || !under.hasFloor || under.facetIndex >= startMap.facets().size())
        {
            continue;
        }

        const std::set<size_t> sectors = sectorsOf(indoor, {startMap.facets()[under.facetIndex].sourceId});

        if (!sectors.empty() && !reached.contains(*sectors.begin()))
        {
            result.stranded.push_back({"spawn point", index, std::string(), {spawn.x, spawn.y, spawn.z},
                *sectors.begin()});
        }
    }

    // A path still waiting for an item the map gives, though its event can be used: the key lies behind its lock
    // (or behind another lock that waits in the same way).
    for (const YAML::Node &event : events)
    {
        const int eventId = event["event"].as<int>();
        const std::map<int, std::set<size_t>>::const_iterator bound = sectorsByEvent.find(eventId);
        bool usable = always.contains(eventId) || usedFromInFront.contains(eventId);

        if (bound != sectorsByEvent.end())
        {
            for (const size_t sector : bound->second)
            {
                usable = usable || reached.contains(sector);
            }
        }

        if (!usable)
        {
            continue;
        }

        size_t pathIndex = 0;

        for (const YAML::Node &path : event["paths"])
        {
            if (usedPaths.contains({eventId, pathIndex++}))
            {
                continue;
            }

            bool movesSomething = false;
            std::string moves;

            for (const YAML::Node &effectNode : path["effects"])
            {
                const std::string &effect = effectNode.Scalar();
                const bool opening = (effect.starts_with("door ") && !clearedDoors.contains(
                        static_cast<uint32_t>(std::stoul(effect.substr(5))))) || effect.starts_with("teleport to ")
                    || !facesMadePassable(indoor, effect).empty();
                movesSomething = movesSomething || effect.starts_with("door ") || effect.starts_with("teleport to ");

                if (opening && moves.size() < 120)
                {
                    moves += (moves.empty() ? "" : "; ") + effect.substr(0, effect.find(" (direction"));
                }
            }

            // A branch that would open something and waits for a variable or a bit: say for what.
            for (const YAML::Node &test : path["tests"])
            {
                const std::string waitsFor =
                    test["taken"].Scalar() == "true" && !moves.empty() ? testWaitsFor(test["what"].Scalar())
                        : std::string();

                if (!waitsFor.empty())
                {
                    const std::string note = "event " + std::to_string(eventId)
                        + (event["title"].Scalar().empty() ? std::string() : " (" + event["title"].Scalar() + ")")
                        + " does not do this for want of " + waitsFor + ": " + moves;

                    if (said.insert(note).second)
                    {
                        result.waiting.push_back(note);
                    }
                }
            }

            for (const YAML::Node &test : path["tests"])
            {
                const std::string &what = test["what"].Scalar();

                if (movesSomething && test["taken"].Scalar() == "true" && what.starts_with("item ")
                    && mapItems.contains(std::stoi(what.substr(5))) && !haveItems.contains(std::stoi(what.substr(5))))
                {
                    const std::string issue = what + " is needed by event " + std::to_string(eventId)
                        + (event["title"].Scalar().empty() ? std::string() : " (" + event["title"].Scalar() + ")")
                        + ", which the party can reach, but the item is found only in parts of the map that stay "
                          "closed without it";

                    if (said.insert(issue).second)
                    {
                        result.issues.push_back(issue);
                    }
                }
            }
        }
    }

    result.stops = findWalkStops(map, lastMaps, lastCells, reached, unreached, eventsMovingDoors(events));
    result.exits.assign(exits.begin(), exits.end());
    return result;
}
}
