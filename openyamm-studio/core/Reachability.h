#pragma once

#include "core/Audit.h"
#include "core/MapLoad.h"

#include <array>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The walk's steps over one map kept from one call to the next (checkReachability, then solveMap on the same map):
// the later walks take the steps of the earlier ones where the faces near them are the same, and walk only the rest.
// The results are the same with or without it; it holds about 150 bytes per grid cell walked.
class WalkSteps
{
public:
    WalkSteps();
    ~WalkSteps();
    WalkSteps(const WalkSteps &) = delete;
    WalkSteps &operator=(const WalkSteps &) = delete;

    struct Kept;
    Kept &kept();

private:
    std::unique_ptr<Kept> m_pKept;
};

// Where a walk ends: an opening with a reached sector on one side and an unreached one on the other, and why the
// body does not pass it.
struct WalkStop
{
    size_t fromSector = 0;
    size_t toSector = 0;
    // The opening's portal face and its middle, at its foot.
    int32_t face = -1;
    std::array<float, 3> at = {};
    // "blocked by face 4522 (invisible; event 58)", "a step 90 high", "door 7 stands in it (event 12 moves it)".
    std::string reason;
    // The body does pass it, from a place stood on: the sector beyond is entered though no grid point of the walk
    // falls on its floor (a rim round a hole, a sill). Such a sector counts as reached and the stop is not reported.
    bool passes = false;
};

struct ReachabilityResult
{
    bool ran = false;
    // Why it did not run (an outdoor map, no party start).
    std::string skipped;
    size_t sectorsWithFloor = 0;
    // Reached on foot from the party start with every door as the map starts.
    size_t reachedAtStart = 0;
    // Reached with every door out of the way.
    size_t reachedDoorsOpen = 0;
    std::vector<size_t> unreachableSectors;
    // Not reached, and lower from floor to top than the party is tall (a slot under a grating): no place to stand,
    // so not among unreachableSectors.
    std::vector<size_t> tooLowNotReached;
    // Grid cells the flood stood on with every door out of the way (a measure of walkable area: one cell is 32 by 32).
    size_t cellsWalked = 0;
    size_t spawnsTotal = 0;
    std::vector<size_t> unreachableSpawns;
    // With every door out of the way: the openings the walk does not pass into an unreached sector.
    std::vector<WalkStop> stops;
};

// Walks the map as the game's monsters and the scenario walker do (the game's path map and planner): from the party
// start to a floor point of every sector and to every spawn point, with the doors as the map starts and with every
// door out of the way (floors that move up or down carry the party between their two poses, level slides only with
// `carry` in their mover block, as in the game; a floor that has moved away lets the party down to what is under
// it; a gap narrower than the body is stood across, not fallen into). What stays unreached with every door out of
// the way is reached only by a teleport, a jump or not at all. `eventFlowJson` (core/EventFlow's result, or empty):
// faces an event makes untouchable (evt.SetFacetBit: a forcefield switched off) count as out of the way too.
// `pSteps`: steps kept for a solveMap of the same map after it (WalkSteps).
ReachabilityResult checkReachability(
    const LoadedMap &map, const std::string &eventFlowJson = std::string(), WalkSteps *pSteps = nullptr);

std::vector<AuditFinding> reachabilityFindings(const ReachabilityResult &result);

// One step of a map opening up (core/Reachability's solve): what became reachable and what did it.
struct SolveWave
{
    // Sectors first reached in this wave.
    std::vector<size_t> sectors;
    // What opened the way: "event 3 (Lever) in sector 4: door 1 open", "event 31 teleports to sector 12".
    std::vector<std::string> causes;
    // What the events used need: "item 2177", "qbit 1035".
    std::vector<std::string> needs;
    // Sectors reached before of which this wave walks clearly more (a gate inside one room): the sector and how
    // many more grid cells (32 by 32 each).
    std::vector<std::pair<size_t, size_t>> extended;
};

struct SolveResult
{
    bool ran = false;
    std::string skipped;
    std::vector<SolveWave> waves;
    size_t sectorsWithFloor = 0;
    std::vector<size_t> neverReached;
    // Unreached sectors too small to stand in (alcoves, key slots): listed apart, they are rarely a fault.
    std::vector<size_t> nichesNotReached;
    // Faults of the lock-and-key order: a key found only behind the door it opens.
    std::vector<std::string> issues;
    // Things worth knowing that are no fault: a key that comes from another map.
    std::vector<std::string> notes;
    // Maps the party can leave to from reached sectors.
    std::vector<std::string> exits;
    // Where the walk ends at the last step: the openings into sectors never reached, and why.
    std::vector<WalkStop> stops;
    // Branches of usable events that would open something and were not taken, with the map variable or bit they
    // wait for: "event 9 does not do this for want of map_var 2 >= 1 (no event of the map sets it): door 4 open".
    std::vector<std::string> waiting;
    // Placed monsters and monster spawn points standing in a sector the solve never reaches: the party cannot get to
    // them, nor they (fliers too: the game's monsters keep to their place) out toward the party (the user's walk
    // through XD-02: bats spawned in an ore chute 384 up a wall hung there for good).
    struct Stranded
    {
        // "monster" (`index` its actor number) or "spawn point" (its number in the map's spawn list).
        std::string kind;
        size_t index = 0;
        std::string name;
        std::array<int, 3> at = {};
        size_t sector = 0;
    };

    std::vector<Stranded> stranded;
};

// The lock-and-key solve (PLAN.md section 6): walk from the party start, use every event bound in the reached
// part (and the map's load and timer events), let the doors those events move stand out of the way, the faces they
// make untouchable (evt.SetFacetBit) let the party through and their teleports carry the party, walk again, until
// nothing new opens. `eventFlowJson` is core/EventFlow's result. A branch
// of a handler is taken once its tests can be met by then: an item the map gives must have been found, a map
// variable raised and a quest bit, award or autonote set by an event the party could use (a bit or item nothing on
// the map gives comes from elsewhere and is listed as what the step needs). An event is used from a sector it is
// bound in, or from a place stood on in front of one of its faces. Other tests are taken both ways. `pSteps`: steps
// kept from a checkReachability of the same map before it (WalkSteps).
SolveResult solveMap(const LoadedMap &map, const std::string &eventFlowJson, WalkSteps *pSteps = nullptr);

// Faces the game never meets: those of a sector with no floor and no portal (nothing enters it, so its faces are in no
// sector the game collides with or draws from; the Lab's sector 23, two stray faces in the plane of the portal from
// 22 to 25, which the party walks through in the game). The walks of `solve`, `audit --reach`, `probe` and `compare`
// leave them out.
std::set<uint32_t> facesTheGameIgnores(const Game::IndoorMapData &indoor);

// One "reach.stranded" warning for each monster and spawn point of `solved.stranded`, with the room of its sector where
// `sectorRooms` names it (a project's).
std::vector<AuditFinding> strandedFindings(const SolveResult &solved, const std::map<int, std::string> &sectorRooms);

// Why the body can or cannot walk straight from one point to another on an indoor map: the path map's own account
// of the segment (which sample failed, for which reason, at which face) and whether the game's planner finds a route
// at all. For finding out what blocks a way. `doorsOpen`: every door open instead of as the map starts.
std::string probeWalk(
    const LoadedMap &map,
    const std::array<float, 3> &from,
    const std::array<float, 3> &to,
    bool doorsOpen);
}
