#include "core/OutdoorBuildings.h"

#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/OutdoorLowering.h"
#include "core/OutdoorModel.h"
#include "core/OutdoorRoofCover.h"
#include "core/OutdoorWaysIn.h"
#include "core/Sketch.h"
#include "core/SketchRead.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <map>

// How a plot becomes a building, as the buildings of the shipped maps are made (measured on Ravenshore, Harmondale,
// New Sorpigal and Dagger Wound; the scripts are in output/studio_s4c/analysis).
//
// Walls. The shipped houses are walls of panels 128 wide and 256 high, one bitmap each: a plain panel, a panel
// with a window, a door, and a post panel for each end of a wall. A storey is 256; taller buildings stack rows.
// So a wall here is divided into bays (as many as fit at 128; the bitmap is fitted to the bay when the wall is no
// multiple of 128) and into rows of 256 from the floor. Each bay names a role (wall, window, door, post_left,
// post_right or any other the plot's `textures` give); neighbouring plain bays are one face. The door is a bay of
// the lowest row and carries the door's event; every other face carries the event that only says the building's
// name, as on the shipped maps.
//
// Parts. A building is one or more parts: a box, a convex outline or a many-sided round (a tower), each a prism
// from `bottom` above the building's floor up `wall_height`, with its own roof. The floor lies at the plot's base:
// the lowering makes the ground under the plot level. Parts that stand on the ground go `foundation` further down,
// so ground that falls away beside the plot shows no gap. There is no floor face: the ground is the floor.
//
// Roofs. `eaves` is how far the roof reaches out past the walls (Ravenshore 16, with the soffit under it),
// `fascia` the upright band between wall and roof (Ravenshore 32). flat: a level top one can stand on, with a
// `parapet` or battlements when asked. hip: four slopes to a ridge drawn in by `hip` from each end (half the
// shorter side when left out: a pyramid over a square). gable: two slopes, the end walls running up to the ridge
// in the `gable` texture. lean_to: one slope up from the low wall. cone: slopes from every wall to a tip (a
// tower's cap, a tent). A `ridge` beam lies on a hip or gable roof's ridge.
//
// Forms counted on the 42 shipped MM6-MM8 outdoor maps (output/studio_s4h/scripts/forms.py, 2026-11-13; heuristics,
// so the counts are of their order, not exact): doors with a face over the ground in front of them, 109 under a
// canopy, 96 under a porch, 59 recessed under the roof (Harmondale's fire guild: three bays set back 128); about 300
// models open under a roof (pavilions, roofed wells, gates); 91 many-sided halls and huts, 34 of them with roofs of
// two or more slopes (Harmondale's training hall: rings in 144 up 192, in 128 up 64, in 80 up 32 and a flat top;
// the hermits' huts: in 64 up 112, then to a tip); 22 signs hung on walls (Ravenshore: 9 boards flat on a wall, 4
// hanging across it under an arm); front steps before a door only 3. So a part may stand open on `posts`, have
// `porches` (a roof on posts, a canopy, or `recess`), roof `tiers`, `signs`, a `railing` (posts and a rail with an
// undrawn barrier between, Ravenshore's terrace), `holes` with a pit (Harmondale's hatch), and a door a `step`.
//
// Every face is flat and convex, wound counter-clockwise seen from outside, with its plane, its polygon type and
// its texels stored as the game's own maps have them (core/OutdoorModel).

namespace OpenYAMM::Studio
{
namespace
{
constexpr double BayWidth = 128.0;
constexpr double RowHeight = 256.0;
constexpr double LeastBay = 96.0;
constexpr double WidestBay = 192.0;
constexpr double ParapetThickness = 32.0;
constexpr double MerlonWidth = 64.0;
constexpr double Pi = 3.14159265358979323846;
const char *SketchFile = "sketch.yml";

struct KitRole
{
    const char *pRole;
    const char *pTexture;
};

struct Kit
{
    const char *pWorld;
    const char *pName;
    std::vector<KitRole> roles;
};

// The kits: for each world the sets of panels its towns are built of. The first of a world is its ordinary house
// and what a plot gets that names nothing. Which bitmap stands at a wall's left end, its right end, inside it and
// on its door was counted on the shipped maps (output/studio_s4c/analysis/roles.py).
const std::vector<Kit> &kits()
{
    static const std::vector<Kit> all = {
        {"mm8", "thatch", {{"wall", "t14a01"}, {"window", "t14a04a"}, {"door", "t14a03"}, {"post_left", "t14a07"},
            {"post_right", "t14a06"}, {"roof", "t14a05"}, {"trim", "t14a05b"}, {"ridge", "t14abcd11"}}},
        {"mm8", "stone", {{"wall", "t14c01"}, {"window", "t14c04b"}, {"door", "t14c03"}, {"post_left", "t14c07"},
            {"post_right", "t14c06"}, {"roof", "t14b05"}, {"trim", "t14a05b"}, {"ridge", "t14abcd11"}}},
        {"mm8", "shingle", {{"wall", "t14b01"}, {"window", "t14b04b"}, {"door", "t14b03"}, {"post_left", "t14b07"},
            {"post_right", "t14b06"}, {"roof", "t14b05"}, {"trim", "t14a05b"}, {"ridge", "t14abcd11"}}},
        {"mm8", "plaster", {{"wall", "t14d01"}, {"window", "t14d04c"}, {"door", "t14d03"}, {"post_left", "t14d07"},
            {"post_right", "t14d06"}, {"roof", "t14b05"}, {"trim", "t14a05b"}, {"ridge", "t14abcd11"}}},
        {"mm8", "boulder", {{"wall", "t06a01"}, {"window", "t06d04"}, {"door", "t06a03"}, {"post_left", "t06a09"},
            {"post_right", "t06a08"}, {"roof", "t14b05"}, {"trim", "t14a05b"}, {"ridge", "t14abcd11"}}},
        {"mm8", "tower", {{"wall", "t14c01b"}, {"window", "t14c01b"}, {"door", "t14c03"}, {"roof", "t14b05"},
            {"trim", "t14a05b"}, {"ridge", "t14abcd11"}}},
        {"mm7", "plaster", {{"wall", "hhm2b2"}, {"window", "hhm2bw"}, {"door", "hhm2d"}, {"post_left", "hhm2el"},
            {"post_right", "hhm2er"}, {"roof", "hhm2rf"}, {"trim", "trim2_32a"}, {"gable", "hhm3ch"},
            {"ridge", "trim2_32"}}},
        {"mm7", "timber", {{"wall", "hhm1b1"}, {"window", "hhm1bw"}, {"door", "hhm1d"}, {"post_left", "hhm1b2le"},
            {"post_right", "hhm1b2re"}, {"roof", "hhm1rf"}, {"trim", "trim2_32a"}, {"gable", "hhm3ch"},
            {"ridge", "trim2_32"}}},
        {"mm7", "grey", {{"wall", "hhm3b"}, {"window", "hhm3bw2"}, {"door", "hhm3d"}, {"post_left", "hhm3el2"},
            {"post_right", "hhm3er2a"}, {"roof", "hhm3rf"}, {"trim", "trim2_32a"}, {"gable", "hhm3ch"},
            {"ridge", "trim2_32"}}},
        {"mm7", "poor", {{"wall", "hhp1b"}, {"window", "hhp1bw"}, {"door", "hhp1d"}, {"post_left", "hhp1el"},
            {"post_right", "hhp1er"}, {"roof", "hhp2rf"}, {"trim", "trim2_32a"}, {"gable", "hhm3ch"},
            {"ridge", "trim2_32"}}},
        {"mm7", "rich", {{"wall", "7hhr1b"}, {"window", "7hhr1bw"}, {"door", "7hhr1d2"}, {"post_left", "7hhr1el3"},
            {"post_right", "7hhr1erb"}, {"roof", "7hhr1rf"}, {"trim", "trim2_32a"}, {"gable", "7hhr1b"},
            {"ridge", "trim2_32"}}},
        {"mm7", "stone", {{"wall", "chb1"}, {"window", "chbw"}, {"door", "hhm1d"}, {"post_left", "chb1el"},
            {"post_right", "chb1er"}, {"roof", "7hhr1rf"}, {"trim", "trim2_32a"}, {"gable", "chb1"},
            {"ridge", "trim2_32"}}},
        {"mm7", "castle", {{"wall", "ch1b1"}, {"window", "ch1b1"}, {"door", "hhm1d"}, {"roof", "ch1b1"},
            {"trim", "ch1b1"}, {"ridge", "ch1b1"}}},
        {"mm6", "plaster", {{"wall", "pxstrst"}, {"window", "pxstrwb"}, {"door", "pxstrdr"},
            {"post_left", "pxstrle"}, {"post_right", "pxstrre"}, {"roof", "pbtrm"}, {"trim", "cbeam5"},
            {"ridge", "cbeam5"}}},
        {"mm6", "brick", {{"wall", "pbrst"}, {"window", "pbrwn"}, {"door", "pbrdr"}, {"post_left", "pbrle"},
            {"post_right", "pbrre"}, {"roof", "pbtrm"}, {"trim", "cbeam5"}, {"ridge", "cbeam5"}}},
        {"mm6", "stone", {{"wall", "t1wl5ct"}, {"window", "t1wl4w"}, {"door", "pxstrdr"}, {"post_left", "t1wl5lea"},
            {"post_right", "t1wl5rea"}, {"roof", "plruf01"}, {"trim", "cbeam5"}, {"ridge", "cbeam5"}}},
        {"mm6", "red", {{"wall", "thctr"}, {"window", "thctrw2"}, {"door", "pxstrdr"}, {"post_left", "thle"},
            {"post_right", "thre"}, {"roof", "pxshings"}, {"trim", "cbeam5"}, {"ridge", "cbeam5"}}},
        {"mm6", "tavern", {{"wall", "tav128wl"}, {"window", "tavwctr"}, {"door", "tavsmdr"}, {"post_left", "tavle"},
            {"post_right", "tavre"}, {"roof", "tavrf"}, {"trim", "cbeam5"}, {"ridge", "cbeam5"}}},
        {"mm6", "dark", {{"wall", "tews"}, {"window", "tewsw"}, {"door", "tewd"}, {"post_left", "tewls"},
            {"post_right", "tewrs"}, {"roof", "pxshings"}, {"trim", "cbeam5"}, {"ridge", "cbeam5"}}},
        {"mm6", "rubble", {{"wall", "rblbw"}, {"window", "rblbw"}, {"door", "tewd"}, {"roof", "rblbw"},
            {"trim", "rblbw"}, {"ridge", "rblbw"}}},
    };
    return all;
}

// The roof of an ordinary house of each world, for what a plot leaves out. Ravenshore's houses: a hip roof rising
// 96 with eaves of 16, a fascia of 32, the ridge drawn in 112 and a ridge beam of 32. Harmondale's: gables at
// about 50 degrees. New Sorpigal's: a pyramid rising 128 without eaves.
struct WorldRoof
{
    const char *pWorld;
    const char *pForm;
    double rise;
    double pitch;
    double eaves;
    double fascia;
    double hipRun;
    double ridge;
};

constexpr WorldRoof WorldRoofs[] = {
    {"mm8", "hip", 96.0, 0.0, 16.0, 32.0, 112.0, 32.0},
    {"mm7", "gable", 0.0, 50.0, 0.0, 0.0, 0.0, 0.0},
    {"mm6", "hip", 128.0, 0.0, 0.0, 0.0, 0.0, 0.0},
};

using Point2 = std::array<double, 2>;



bool numberOfNode(const YAML::Node &value, double &number)
{
    if (!value.IsDefined() || !value.IsScalar())
    {
        return false;
    }

    const std::string &text = value.Scalar();
    const std::from_chars_result result = std::from_chars(text.data(), text.data() + text.size(), number);
    return result.ec == std::errc() && result.ptr == text.data() + text.size() && std::isfinite(number);
}

bool numberOf(const YAML::Node &node, const char *pKey, double &number)
{
    return numberOfNode(childOf(node, pKey), number);
}

double numberOr(const YAML::Node &node, const char *pKey, double fallback)
{
    double number = fallback;
    return numberOf(node, pKey, number) ? number : fallback;
}

// A field of the part, else of the plot.
YAML::Node fieldOf(const YAML::Node &part, const YAML::Node &plot, const char *pKey)
{
    const YAML::Node own = childOf(part, pKey);
    return own.IsDefined() ? own : childOf(plot, pKey);
}

bool pointOf(const YAML::Node &node, Point2 &point)
{
    return node.IsDefined() && node.IsSequence() && node.size() == 2 && numberOfNode(node[0], point[0])
        && numberOfNode(node[1], point[1]);
}

const Kit *findKit(const std::string &world, const std::string &name)
{
    const Kit *pFirst = nullptr;

    for (const Kit &kit : kits())
    {
        if (world != kit.pWorld)
        {
            continue;
        }

        pFirst = pFirst == nullptr ? &kit : pFirst;

        if (name == kit.pName)
        {
            return &kit;
        }
    }

    return name.empty() ? pFirst : nullptr;
}

std::string joined(const std::vector<std::string> &names)
{
    std::string text;

    for (const std::string &name : names)
    {
        text += (text.empty() ? "" : ", ") + name;
    }

    return text;
}

double signedArea(const std::vector<Point2> &points)
{
    double area = 0.0;

    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point2 &from = points[index];
        const Point2 &to = points[(index + 1) % points.size()];
        area += from[0] * to[1] - to[0] * from[1];
    }

    return area * 0.5;
}

bool convex(const std::vector<Point2> &points)
{
    for (size_t index = 0; index < points.size(); ++index)
    {
        const Point2 &a = points[index];
        const Point2 &b = points[(index + 1) % points.size()];
        const Point2 &c = points[(index + 2) % points.size()];

        if ((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) < -1.0e-6)
        {
            return false;
        }
    }

    return true;
}

double lengthOf(const Point2 &from, const Point2 &to)
{
    return oy::hypot(to[0] - from[0], to[1] - from[1]);
}

// A convex outline (counter-clockwise) moved out by `distance` on every side (in, when negative).
std::vector<Point2> grown(const std::vector<Point2> &outline, double distance)
{
    const size_t count = outline.size();
    std::vector<Point2> result(count);

    for (size_t index = 0; index < count; ++index)
    {
        const Point2 &before = outline[(index + count - 1) % count];
        const Point2 &here = outline[index];
        const Point2 &after = outline[(index + 1) % count];
        const double inLength = std::max(lengthOf(before, here), 1.0e-9);
        const double outLength = std::max(lengthOf(here, after), 1.0e-9);
        const Point2 inDirection = {(here[0] - before[0]) / inLength, (here[1] - before[1]) / inLength};
        const Point2 outDirection = {(after[0] - here[0]) / outLength, (after[1] - here[1]) / outLength};
        // The outward normals of the two sides, and the corner where the moved sides meet.
        const Point2 inNormal = {inDirection[1], -inDirection[0]};
        const Point2 outNormal = {outDirection[1], -outDirection[0]};
        const double cross = inDirection[0] * outDirection[1] - inDirection[1] * outDirection[0];

        if (std::fabs(cross) < 1.0e-6)
        {
            result[index] = {here[0] + inNormal[0] * distance, here[1] + inNormal[1] * distance};
            continue;
        }

        const Point2 onIn = {here[0] + inNormal[0] * distance, here[1] + inNormal[1] * distance};
        const Point2 onOut = {here[0] + outNormal[0] * distance, here[1] + outNormal[1] * distance};
        const double along = ((onOut[0] - onIn[0]) * outDirection[1] - (onOut[1] - onIn[1]) * outDirection[0])
            / cross;
        result[index] = {onIn[0] + inDirection[0] * along, onIn[1] + inDirection[1] * along};
    }

    return result;
}

// A convex outline (counter-clockwise) with each side moved in by its own distance (out, when negative): side i
// (from point i to point i + 1) by `insets[i]`; each corner where its two sides' moved lines meet.
std::vector<Point2> outdoorOffsetOutline(const std::vector<Point2> &outline, const std::vector<double> &insets)
{
    const size_t count = outline.size();
    std::vector<Point2> result(count);

    for (size_t index = 0; index < count; ++index)
    {
        const size_t previous = (index + count - 1) % count;
        const Point2 &before = outline[previous];
        const Point2 &here = outline[index];
        const Point2 &after = outline[(index + 1) % count];
        const double inLength = std::max(lengthOf(before, here), 1.0e-9);
        const double outLength = std::max(lengthOf(here, after), 1.0e-9);
        const Point2 inDirection = {(here[0] - before[0]) / inLength, (here[1] - before[1]) / inLength};
        const Point2 outDirection = {(after[0] - here[0]) / outLength, (after[1] - here[1]) / outLength};
        // The outward normals of the two sides, each moved by minus its inset.
        const Point2 inNormal = {inDirection[1], -inDirection[0]};
        const Point2 outNormal = {outDirection[1], -outDirection[0]};
        const double inMove = -insets[previous];
        const double outMove = -insets[index];
        const double cross = inDirection[0] * outDirection[1] - inDirection[1] * outDirection[0];
        const Point2 onIn = {here[0] + inNormal[0] * inMove, here[1] + inNormal[1] * inMove};
        const Point2 onOut = {here[0] + outNormal[0] * outMove, here[1] + outNormal[1] * outMove};

        if (std::fabs(cross) < 1.0e-6)
        {
            result[index] = onOut;
            continue;
        }

        const double along = ((onOut[0] - onIn[0]) * outDirection[1] - (onOut[1] - onIn[1]) * outDirection[0])
            / cross;
        result[index] = {onIn[0] + inDirection[0] * along, onIn[1] + inDirection[1] * along};
    }

    return result;
}

// How far a convex outline may move in before its first side shrinks to nothing, up to `limit`: `step`, and true
// when a side is gone there. A side shrinks by the cotangents of half the inner angles at its two ends for each unit
// the outline moves in.
bool firstCollapse(const std::vector<Point2> &outline, double limit, double &step)
{
    const size_t count = outline.size();
    step = limit;
    bool collapses = false;

    for (size_t index = 0; index < count; ++index)
    {
        const Point2 &before = outline[(index + count - 1) % count];
        const Point2 &from = outline[index];
        const Point2 &to = outline[(index + 1) % count];
        const Point2 &after = outline[(index + 2) % count];
        const auto halfTurnCot = [](const Point2 &a, const Point2 &b, const Point2 &c)
        {
            const double ux = a[0] - b[0];
            const double uy = a[1] - b[1];
            const double vx = c[0] - b[0];
            const double vy = c[1] - b[1];
            const double angle = oy::atan2(std::fabs(ux * vy - uy * vx), ux * vx + uy * vy);
            return 1.0 / oy::tan(std::max(angle, 1.0e-9) * 0.5);
        };
        const double rate = halfTurnCot(before, from, to) + halfTurnCot(from, to, after);
        const double length = lengthOf(from, to);

        if (rate > 1.0e-9 && length / rate <= step)
        {
            step = length / rate;
            collapses = true;
        }
    }

    return collapses;
}

// An outline with the sides that have shrunk to nothing dropped (their corners become one).
std::vector<Point2> withoutGoneSides(const std::vector<Point2> &outline, double scale)
{
    std::vector<Point2> kept;

    for (size_t index = 0; index < outline.size(); ++index)
    {
        if (lengthOf(outline[index], outline[(index + 1) % outline.size()]) > 1.0e-6 * std::max(1.0, scale))
        {
            kept.push_back(outline[index]);
        }
    }

    return kept;
}

// A convex outline drawn in by `in` on every side, as a roof's ring is: every side moves in alike, and a side that
// shrinks to nothing on the way is dropped (its two corners become one) and the rest go on in (a twelve-sided hall's
// short sides vanish and its ring comes out rounder). False when nothing is left: the inset reaches the middle.
bool drawnIn(const std::vector<Point2> &outline, double in, std::vector<Point2> &result)
{
    result = outline;
    double remaining = in;

    for (int round = 0; remaining > 1.0e-9 && round < 64; ++round)
    {
        if (result.size() < 3)
        {
            return false;
        }

        double step = 0.0;
        const bool collapses = firstCollapse(result, remaining, step);
        result = grown(result, -step);
        remaining -= step;

        if (collapses)
        {
            result = withoutGoneSides(result, in);
        }
    }

    return result.size() >= 3 && signedArea(result) >= 1.0;
}

// Where the bays of a wall begin and end, map units from its left end: bays with a width of their own take it, the
// rest share what is left alike (all alike when none has one).
std::vector<double> bayEdgesOf(const OutdoorPartPlan &part, size_t wall, bool upper)
{
    const std::vector<std::vector<std::string>> &rows = upper ? part.upperBays : part.bays;
    const std::vector<std::vector<double>> &widthRows = upper ? part.upperBayWidths : part.bayWidths;
    const size_t count = std::max<size_t>(1, wall < rows.size() ? rows[wall].size() : 1);
    const double length = lengthOf(part.outline[wall], part.outline[(wall + 1) % part.outline.size()]);
    const std::vector<double> none;
    const std::vector<double> &widths = wall < widthRows.size() ? widthRows[wall] : none;
    double given = 0.0;
    size_t shared = 0;

    for (size_t bay = 0; bay < count; ++bay)
    {
        const double width = bay < widths.size() ? widths[bay] : 0.0;
        given += width;
        shared += width > 0.0 ? 0 : 1;
    }

    std::vector<double> edges = {0.0};

    if (given <= 0.0)
    {
        const double width = length / count;

        for (size_t bay = 1; bay <= count; ++bay)
        {
            edges.push_back(bay * width);
        }

        return edges;
    }

    const double share = shared > 0 ? std::max(0.0, length - given) / shared : 0.0;

    for (size_t bay = 0; bay < count; ++bay)
    {
        const double width = bay < widths.size() ? widths[bay] : 0.0;
        edges.push_back(edges.back() + (width > 0.0 ? width : share));
    }

    return edges;
}

// S8d: the stretches of a wall left open by a recess of the wall beside it that is open at their shared corner
// (`open_corner`): [from, to] along it, map units from its left end. Empty for every wall of a part without one.
std::vector<std::array<double, 2>> openStretchesOf(const OutdoorPartPlan &part, size_t wall)
{
    std::vector<std::array<double, 2>> found;
    const size_t count = part.outline.size();

    for (const OutdoorPorchPlan &porch : part.porches)
    {
        if (!porch.recess || count < 3)
        {
            continue;
        }

        // Open at the recess's left end: the wall before it on the outline is open at its right end.
        if (porch.openLeft && (porch.wall + count - 1) % count == wall)
        {
            const double length = lengthOf(part.outline[wall], part.outline[(wall + 1) % count]);
            found.push_back({length - porch.depth, length});
        }

        if (porch.openRight && (porch.wall + 1) % count == wall)
        {
            found.push_back({0.0, porch.depth});
        }
    }

    return found;
}

// The roles a wall's bays get when the plot does not list them: posts at the ends where the kit has them, the
// door in the middle of the door's wall with a window on each side, windows in every second bay elsewhere.
std::vector<std::string> defaultBays(size_t count, bool posts, const std::string &windows, int doorBay)
{
    std::vector<std::string> bays(count, "wall");

    if (posts && count >= 2)
    {
        bays.front() = "post_left";
        bays.back() = "post_right";
    }

    const size_t first = posts && count >= 2 ? 1 : 0;
    const size_t last = posts && count >= 2 ? count - 1 : count;

    for (size_t bay = first; bay < last; ++bay)
    {
        const size_t offset = doorBay >= 0 ? static_cast<size_t>(std::abs(static_cast<int>(bay) - doorBay)) + 1
            : bay - first;

        if (windows == "all" || (windows == "alternate" && offset % 2 == 0))
        {
            bays[bay] = "window";
        }
    }

    if (doorBay >= 0 && static_cast<size_t>(doorBay) < count)
    {
        bays[doorBay] = "door";
    }

    return bays;
}

class BuildingReader
{
public:
    BuildingReader(
        const std::string &world,
        const YAML::Node &plot,
        const std::string &path,
        const std::array<double, 4> &rectangle,
        std::vector<ProjectIssue> &issues)
        : m_world(world)
        , m_plot(plot)
        , m_path(path)
        , m_rectangle(rectangle)
        , m_issues(issues)
    {
        for (const WorldRoof &roof : WorldRoofs)
        {
            if (world == roof.pWorld)
            {
                m_pWorldRoof = &roof;
            }
        }
    }

    // The texture classes' door pictures (F2: a wing becomes a double door) and where its notes go.
    void useDoorPictures(const OutdoorDoorPictures *pDoorPictures, std::vector<std::string> &warnings)
    {
        m_pDoorPictures = pDoorPictures;
        m_pWarnings = &warnings;
    }

    bool read(OutdoorBuildingPlan &building)
    {
        const size_t before = m_issues.size();
        building.west = m_rectangle[0];
        building.north = m_rectangle[1];
        building.east = m_rectangle[2];
        building.south = m_rectangle[3];
        const std::string facing = textOf(m_plot, "facing", "s");
        building.facing = facing.empty() ? 's' : facing[0];
        numberOf(m_plot, "foundation", building.foundation);
        numberOf(m_plot, "turn", m_turn);
        building.title = textOf(m_plot, "title");
        building.hint = textOf(m_plot, "hint");
        building.hintShared = textOf(m_plot, "hint_shared") == "true";

        if (building.hint.empty() && childOf(m_plot, "hint_shared").IsDefined())
        {
            add(m_path + ".hint_shared", "`hint_shared` shares the building's `hint`: give it one");
        }
        building.path = m_path;
        building.floorGiven = numberOf(m_plot, "floor", building.floor);
        building.onDeck = textOf(m_plot, "on");

        if (!building.onDeck.empty() && (childOf(m_plot, "floor").IsDefined() || childOf(m_plot, "plinth").IsDefined()
            || childOf(m_plot, "skirt").IsDefined() || childOf(m_plot, "against").IsDefined()))
        {
            add(".on", "a building `on` a deck stands at the deck's top: it takes no `floor`, `plinth`, `skirt` or "
                "`against`");
        }

        if (childOf(m_plot, "floor").IsDefined() && (!building.floorGiven || building.floor < 0.0
            || building.floor > 8160.0))
        {
            add(".floor", "floor is the height of the building's floor against the plan's datum, 0 to 8160 map "
                "units (the terrain stores heights in steps of 32 up to 8160)");
        }

        if (building.foundation < 0.0 || building.foundation > 1024.0)
        {
            add("", "the foundation of " + building.id + " must be 0 to 1024");
        }

        // A base course over the street: the walls' `base` course shows `plinth` high over the land round it.
        if (childOf(m_plot, "plinth").IsDefined() && (!numberOf(m_plot, "plinth", building.plinth)
            || building.plinth < 0.0 || building.plinth > 256.0 || std::fmod(building.plinth, 32.0) != 0.0
            || building.plinth + 32.0 > building.foundation))
        {
            add(".plinth", "plinth is how far the floor stands over the land under the plot, 0 to 256 in steps of "
                "32 as the terrain stores heights (Ravenshore's poor lanes: 32), and the walls' `foundation` ("
                + formatNumber(building.foundation) + ") must reach at least 32 further down: raise `foundation` with it");
        }

        const YAML::Node against = childOf(m_plot, "against");

        if (against.IsDefined() && textOf(m_plot, "against") != "slope")
        {
            add(".against", "against is slope: the building stands against a slope or cliff behind it (its back "
                "walls left out, the land under it not made level)");
        }

        building.against = against.IsDefined();
        {
            const double width = (m_rectangle[2] - m_rectangle[0]) * OutdoorCellSize;
            const double depth = (m_rectangle[3] - m_rectangle[1]) * OutdoorCellSize;
            const Point2 middle = {width * 0.5, depth * 0.5};
            // The plot's own frame runs east and south: the back is opposite the front.
            const Point2 backLocal = building.facing == 'n' ? Point2{0.0, 1.0} : building.facing == 'e'
                ? Point2{-1.0, 0.0} : building.facing == 'w' ? Point2{1.0, 0.0} : Point2{0.0, -1.0};
            const Point2 from = toWorld(middle);
            const Point2 to = toWorld({middle[0] + backLocal[0], middle[1] + backLocal[1]});
            const double length = oy::hypot(to[0] - from[0], to[1] - from[1]);
            building.back = {(to[0] - from[0]) / length, (to[1] - from[1]) / length};
        }

        if (childOf(m_plot, "skirt").IsDefined())
        {
            building.skirt = textOf(m_plot, "skirt");

            if (building.skirt == "ground")
            {
                building.skirt = m_world == "mm6" ? "6dirttyl" : m_world == "mm7" ? "7dirttyl" : "dirttyl";
            }

            if (building.skirt.empty())
            {
                add(".skirt", "skirt is ground (the world's dirt tile) or a texture's name: the walls carried down "
                    "into the land in it");
            }

            if (building.foundation <= 0.0)
            {
                add(".skirt", "a skirt is the base course carried down into the land: it needs a `foundation` above "
                    "0 (left out: 128)");
            }
        }

        const YAML::Node parts = childOf(m_plot, "parts");

        if (parts.IsDefined() && parts.IsSequence() && parts.size() != 0)
        {
            for (size_t index = 0; index < parts.size(); ++index)
            {
                OutdoorPartPlan part;

                if (readPart(parts[index], ".parts[" + std::to_string(index) + "]", building, part))
                {
                    building.parts.push_back(part);
                    m_partNodes.push_back(parts[index]);
                }
            }
        }
        else
        {
            OutdoorPartPlan part;

            if (readPart(YAML::Node(YAML::NodeType::Undefined), "", building, part))
            {
                building.parts.push_back(part);
                m_partNodes.push_back(YAML::Node(YAML::NodeType::Undefined));
            }
        }

        if (m_issues.size() != before || building.parts.empty())
        {
            return false;
        }

        readClimbs(building);
        readDoors(building);

        if (m_issues.size() != before)
        {
            return false;
        }

        // The bays, now that the doors are known; then what stands on the walls by their bays.
        for (size_t index = 0; index < building.parts.size(); ++index)
        {
            readBays(building, index);
        }

        for (size_t index = 0; index < building.parts.size() && m_issues.size() == before; ++index)
        {
            readWallThings(building, index);
        }

        // S8d: no door in a stretch that a recess open at its corner (`open_corner`) leaves open.
        for (const OutdoorDoorPlan &door : building.doors)
        {
            if (door.part >= building.parts.size())
            {
                continue;
            }

            const OutdoorPartPlan &part = building.parts[door.part];
            const std::vector<double> edges = bayEdgesOf(part, door.wall, door.storey > 0);

            for (const std::array<double, 2> &open : openStretchesOf(part, door.wall))
            {
                if (door.bay + 1 < edges.size() && edges[door.bay] < open[1] - 0.5
                    && edges[door.bay + 1] > open[0] + 0.5)
                {
                    add(door.path.substr(std::min(m_path.size(), door.path.size())), "the door's bay lies in the "
                        "stretch a recess open at its corner (`open_corner`) "
                        "leaves open: put it on the recess's back or elsewhere");
                    return false;
                }
            }
        }

        std::array<double, 4> covered = {1.0e18, 1.0e18, -1.0e18, -1.0e18};

        for (const OutdoorPartPlan &part : building.parts)
        {
            std::vector<Point2> reach = grown(part.outline, part.roof.eaves);

            // A porch's front corners, and a step's.
            for (const OutdoorPorchPlan &porch : part.porches)
            {
                const std::vector<double> edges = bayEdgesOf(part, porch.wall, false);
                const Point2 &left = part.outline[porch.wall];
                const Point2 &right = part.outline[(porch.wall + 1) % part.outline.size()];
                const double length = std::max(lengthOf(left, right), 1.0e-9);

                for (const double along : {edges[porch.fromBay] - porch.overhang, edges[porch.toBay + 1]
                         + porch.overhang})
                {
                    const double out = porch.recess ? 0.0 : porch.depth;
                    reach.push_back({left[0] + (right[0] - left[0]) * along / length + (right[1] - left[1]) / length
                        * out, left[1] + (right[1] - left[1]) * along / length - (right[0] - left[0]) / length * out});
                }
            }

            for (const Point2 &point : reach)
            {
                const double x = point[0] / OutdoorCellSize + outdoorNodeCount() / 2;
                const double y = outdoorNodeCount() / 2 - point[1] / OutdoorCellSize;
                covered = {std::min(covered[0], x), std::min(covered[1], y), std::max(covered[2], x),
                    std::max(covered[3], y)};
            }
        }

        building.covered = covered;

        if (covered[0] < building.west - 2.0 || covered[1] < building.north - 2.0 || covered[2] > building.east + 2.0
            || covered[3] > building.south + 2.0)
        {
            add(".parts", "the parts of " + building.id + " cover x " + formatNumber(covered[0]) + " to "
                + formatNumber(covered[2]) + ", y " + formatNumber(covered[1]) + " to " + formatNumber(covered[3])
                + " (cells), more than two cells outside its plot (x " + formatNumber(building.west) + " to "
                + formatNumber(building.east) + ", y " + formatNumber(building.north) + " to "
                + formatNumber(building.south) + "): move the parts (their `at` is in map units from the plot's "
                "north-west corner), or give the building a larger `footprint_cells` in plan.yml");
        }

        return m_issues.size() == before;
    }

private:
    void add(const std::string &at, const std::string &message)
    {
        m_issues.push_back({SketchFile, m_path + at, message, "building"});
    }

    // From the plot's own frame (map units east and south of its north-west corner) to the world, turned about
    // the plot's middle.
    Point2 toWorld(const Point2 &local) const
    {
        const double width = (m_rectangle[2] - m_rectangle[0]) * OutdoorCellSize;
        const double depth = (m_rectangle[3] - m_rectangle[1]) * OutdoorCellSize;
        const double east = local[0] - width * 0.5;
        const double north = depth * 0.5 - local[1];
        const double angle = -m_turn * Pi / 180.0;
        const double middleX = ((m_rectangle[0] + m_rectangle[2]) * 0.5 - outdoorNodeCount() / 2) * OutdoorCellSize;
        const double middleY = (outdoorNodeCount() / 2 - (m_rectangle[1] + m_rectangle[3]) * 0.5) * OutdoorCellSize;
        return {middleX + east * oy::cos(angle) - north * oy::sin(angle),
            middleY + east * oy::sin(angle) + north * oy::cos(angle)};
    }

    bool readPart(const YAML::Node &node, const std::string &at, const OutdoorBuildingPlan &building,
        OutdoorPartPlan &part)
    {
        const size_t before = m_issues.size();
        part.id = textOf(node, "id");
        part.title = textOf(node, "title");
        part.path = m_path + at;
        part.shape = textOf(node, "shape", "box");
        const double width = (m_rectangle[2] - m_rectangle[0]) * OutdoorCellSize;
        const double depth = (m_rectangle[3] - m_rectangle[1]) * OutdoorCellSize;
        std::vector<Point2> local;
        // The walls as the sketch counts them, to the outline's sides: empty where they are the same.
        m_wallOrder.emplace_back();

        // A word of another shape is refused, not ignored: an `outline` without `shape: outline` was built as a box
        // over the whole plot.
        for (const std::pair<const char *, const char *> &word : {std::pair<const char *, const char *>{"outline",
                 "outline"}, {"radius", "round"}, {"sides", "round"}, {"size", "box"}})
        {
            if (childOf(node, word.first).IsDefined() && part.shape != word.second)
            {
                add(at + "." + word.first, std::string("`") + word.first + "` belongs to a part of `shape: "
                    + word.second + "`; this part's shape is " + part.shape
                    + (childOf(node, "shape").IsDefined() ? std::string() : " (left out: a box)") + ": write `shape: "
                    + word.second + "`, or leave `" + word.first + "` out");
                return false;
            }
        }

        if (part.shape == "box")
        {
            Point2 corner = {0.0, 0.0};
            Point2 size = {width, depth};
            const YAML::Node atNode = childOf(node, "at");
            const YAML::Node sizeNode = childOf(node, "size");

            if ((atNode.IsDefined() && !pointOf(atNode, corner)) || (sizeNode.IsDefined() && !pointOf(sizeNode, size))
                || size[0] < 32.0 || size[1] < 32.0)
            {
                add(at, "a box part has `at: [x, y]` (its north-west corner, map units east and south of the "
                    "plot's north-west corner) and `size: [width, depth]` of at least 32 each");
                return false;
            }

            // South-west, south-east, north-east, north-west: walls s, e, n, w.
            local = {{corner[0], corner[1] + size[1]}, {corner[0] + size[0], corner[1] + size[1]},
                {corner[0] + size[0], corner[1]}, {corner[0], corner[1]}};
        }
        else if (part.shape == "outline")
        {
            const YAML::Node outline = childOf(node, "outline");

            for (size_t index = 0; outline.IsDefined() && outline.IsSequence() && index < outline.size(); ++index)
            {
                Point2 point = {0.0, 0.0};

                if (pointOf(outline[index], point))
                {
                    local.push_back(point);
                }
            }

            if (local.size() < 3 || local.size() != outline.size() || local.size() > 24)
            {
                add(at + ".outline", "an outline part has `outline`: 3 to 24 points [x, y] in map units east and "
                    "south of the plot's north-west corner");
                return false;
            }
        }
        else if (part.shape == "round")
        {
            Point2 centre = {width * 0.5, depth * 0.5};
            double radius = 0.0;
            double sides = 8.0;
            const YAML::Node atNode = childOf(node, "at");
            numberOf(node, "sides", sides);

            if ((atNode.IsDefined() && !pointOf(atNode, centre)) || !numberOf(node, "radius", radius) || radius < 32.0
                || sides < 5.0 || sides > 16.0 || sides != std::floor(sides))
            {
                add(at, "a round part has `at: [x, y]` (its middle), a `radius` of at least 32 and 5 to 16 `sides` "
                    "(8 when left out)");
                return false;
            }

            // The first wall looks south; the corners lie on the radius.
            for (int side = 0; side < static_cast<int>(sides); ++side)
            {
                const double angle = (side - 0.5) * 2.0 * Pi / sides - Pi * 0.5;
                local.push_back({centre[0] + radius * oy::cos(angle), centre[1] - radius * oy::sin(angle)});
            }
        }
        else
        {
            add(at + ".shape", "a part's shape is box, outline or round; `" + part.shape + "` is none of them");
            return false;
        }

        for (const Point2 &point : local)
        {
            part.outline.push_back(toWorld(point));
        }

        if (signedArea(part.outline) < 0.0)
        {
            // Drawn clockwise: turned round, with the walls counted as the sketch counts them.
            std::reverse(part.outline.begin(), part.outline.end());
            const size_t count = part.outline.size();

            for (size_t wall = 0; wall < count; ++wall)
            {
                m_wallOrder.back().push_back((2 * count - 2 - wall) % count);
            }
        }

        // Batch S4R: an outline part may bend in (an L, a notched front), under one roof.
        part.concave = part.shape == "outline" && !convex(part.outline) && polygonIsSimple(part.outline);

        if ((!convex(part.outline) && !part.concave) || std::fabs(signedArea(part.outline)) < 1024.0)
        {
            add(at + ".outline", part.shape == "outline" ? "the outline of a part must not cross itself and must "
                "enclose ground (it may bend in: an L, a notched front)" : "the outline of a part must be convex "
                "(every corner bends the same way) and enclose ground: make a building that bends of several parts, "
                "each convex");
            return false;
        }

        numberOf(node, "bottom", part.bottom);

        if (childOf(node, "taper").IsDefined() && (!numberOf(node, "taper", part.taper) || part.taper < 0.05
            || part.taper > 4.0))
        {
            add(at + ".taper", "taper is how wide the top of the part's walls is against their foot: 0.05 to 4 (1 "
                "upright walls, 0.5 a spire that draws in to half, 1.5 a cap that flares)");
            part.taper = 1.0;
        }

        const YAML::Node heightNode = fieldOf(node, m_plot, "wall_height");

        if (heightNode.IsDefined() && !numberOfNode(heightNode, part.wallHeight))
        {
            add(at + ".wall_height", "wall_height is a number");
        }

        const YAML::Node bandNode = fieldOf(node, m_plot, "band");

        if (bandNode.IsDefined() && (!numberOfNode(bandNode, part.band) || part.band < 0.0 || part.band > 128.0))
        {
            add(at + ".band", "band is the height of the band between the lowest row of panels and the rows above, "
                "0 to 128 (Ravenshore's houses: 32)");
            part.band = 0.0;
        }

        if (part.wallHeight < 0.0 || part.wallHeight > 4096.0 || part.bottom < -1024.0 || part.bottom > 4096.0)
        {
            add(at, "the walls of a part of " + building.id + " are 16 to 4096 high and begin -1024 to 4096 above "
                "the building's floor");
        }

        readTextures(node, at, part);
        readRoof(node, at, part);

        // Lower walls than 16 (down to none) only under a roof that reaches the ground: a tent, an A-frame, a hut.
        if (part.wallHeight < 16.0 && part.wallHeight >= 0.0 && !reachesGround(part))
        {
            add(at + ".wall_height", "walls lower than 16 (down to 0) stand under a roof that reaches the ground: "
                "gable, hip, cone, dome or lean_to with no eaves or fascia (a tent, an A-frame, a cone hut); this "
                "part's roof is " + part.roof.form + (part.roof.eaves > 0.0 || part.roof.fascia > 0.0
                ? " with eaves or a fascia" : ""));
        }

        if (childOf(node, "climb").IsDefined() && (!numberOf(node, "climb", part.climb) || part.climb < 16.0
            || part.climb > 512.0))
        {
            add(at + ".climb", "climb is how far in from a wall the hidden slope the party walks up reaches the "
                "part's top: 16 to 512 map units (the depth of a tread: Harmondale's fort 40)");
            part.climb = 0.0;
        }

        readOpenPart(node, at, part);
        readHoles(node, at, part);
        readMasses(node, at, part);
        readCourt(node, at, part);
        checkBendingIn(at, part);
        return m_issues.size() == before;
    }

    // Batch S4R: what a part whose outline bends in can carry. Its walls are any part's; its roof is flat (with a
    // parapet), hip or gable over the whole outline, with eaves and a fascia.
    void checkBendingIn(const std::string &at, const OutdoorPartPlan &part)
    {
        if (!part.concave)
        {
            return;
        }

        const OutdoorRoofPlan &roof = part.roof;
        std::vector<std::string> words;
        const auto refuse = [&words](bool given, const char *pWord)
        {
            if (given)
            {
                words.push_back(pWord);
            }
        };
        refuse(roof.form != "flat" && roof.form != "hip" && roof.form != "gable" && roof.form != "none",
            "roof: cone, dome or lean_to");
        refuse(!roof.tiers.empty(), "tiers");
        refuse(roof.cap > 0.0, "cap");
        refuse(roof.ridge > 0.0, "ridge");
        refuse(part.taper != 1.0, "taper");
        refuse(part.posts > 0.0, "posts");
        refuse(!part.holes.empty(), "holes");
        refuse(part.batter != 0.0, "batter");
        refuse(!part.steps.empty(), "steps");
        refuse(part.ruin.given, "ruin");
        refuse(part.climb > 0.0, "climb");

        if (!words.empty())
        {
            add(at + ".outline", "an outline that bends in takes a flat (or parapet), hip or gable roof over the whole "
                "outline with eaves and a fascia; not " + joined(words) + ": make the part of convex parts for those");
        }
    }

    // Whether a part's roof reaches down to its foot when its walls are low or none.
    static bool reachesGround(const OutdoorPartPlan &part)
    {
        const std::string &form = part.roof.form;
        return (form == "gable" || form == "hip" || form == "cone" || form == "dome" || form == "lean_to")
            && part.roof.eaves <= 0.0 && part.roof.fascia <= 0.0 && part.roof.parapet <= 0.0;
    }

    // Batch O-D's words on a part that need no wall names: batter, buttresses' sizes, a door's height, terraces,
    // a ruin.
    // S8d: `roof: vault` on a box (Castle Ironfist's temples TempleW, TempleS: Pxshings falling 256 in five slopes
    // to the two ends of their axis, a flat crown 864 between). A gable whose two slopes are a curved section across
    // the ridge: `tiers` from each eaves side ([in, up], each slope no steeper than the one below it), the rest a
    // flat crown; or, without tiers, a half ellipse `roof_height` high (half the span when left out: a half circle)
    // in `vault_segments` segments to each side. Its end walls close up to it in the `gable` texture.
    void readVault(const YAML::Node &node, const std::string &at, OutdoorPartPlan &part, bool ownHeight,
        bool ownPitch)
    {
        OutdoorRoofPlan &roof = part.roof;
        roof.ridge = 0.0;
        roof.hipRun = 0.0;
        double segments = 4.0;
        const YAML::Node segmentNode = fieldOf(node, m_plot, "vault_segments");

        if (segmentNode.IsDefined() && (!roof.tiers.empty() || !numberOfNode(segmentNode, segments) || segments < 2.0
            || segments > 8.0 || segments != std::floor(segments)))
        {
            add(at + ".vault_segments", "vault_segments is how many segments each half of a vault's half ellipse "
                "has, a whole number 2 to 8 (4 when left out); a vault drawn by `tiers` takes none");
            segments = 4.0;
        }

        roof.vaultSegments = static_cast<int>(segments);

        if (ownPitch || childOf(node, "eaves_walls").IsDefined() || childOf(node, "cap").IsDefined()
            || part.concave || part.taper != 1.0 || childOf(node, "posts").IsDefined())
        {
            add(at + ".roof", "a vault is said by its section (`tiers`, or `roof_height` and `vault_segments`), on a "
                "box with upright walls: no `roof_pitch`, `cap`, `eaves_walls`, `taper` or `posts`");
            return;
        }

        const double first = lengthOf(part.outline[0], part.outline[1]) + 2.0 * roof.eaves;
        const double second = lengthOf(part.outline[1], part.outline[2]) + 2.0 * roof.eaves;
        const bool alongFirst = roof.along == 'x' || (roof.along == 0 && first >= second);
        const double half = (alongFirst ? second : first) * 0.5;

        if (roof.tiers.empty())
        {
            roof.rise = ownHeight ? roof.rise : std::round(half);

            if (roof.rise <= 0.0 || roof.rise > 2048.0)
            {
                add(at + ".roof_height", "a vault rises more than 0 and at most 2048 over its foot");
            }

            return;
        }

        double in = 0.0;
        double slope = 1.0e18;

        for (const std::array<double, 2> &tier : roof.tiers)
        {
            const double own = tier[0] > 0.0 ? tier[1] / tier[0] : 1.0e18;

            if (tier[0] <= 0.0 || own > slope + 1.0e-9)
            {
                add(at + ".tiers", "a vault's section rises from its eaves side, each tier [in, up] reaching in "
                    "(in above 0) and no steeper than the one below it: a curve that flattens toward its crown "
                    "(Castle Ironfist's temples: [[24, 32], [56, 48], [96, 64], [176, 96], [48, 16]])");
                roof.tiers.clear();
                return;
            }

            slope = own;
            in += tier[0];
        }

        if (in > half + 0.5)
        {
            add(at + ".tiers", "a vault's tiers reach " + formatNumber(in) + " in from each eaves side, past the "
                "middle of the span (" + formatNumber(half) + " from each side): draw them in less");
            roof.tiers.clear();
        }
    }

    void readMasses(const YAML::Node &node, const std::string &at, OutdoorPartPlan &part)
    {
        if (childOf(node, "batter").IsDefined() && (!numberOf(node, "batter", part.batter) || part.batter <= 0.0
            || part.batter > 1024.0))
        {
            add(at + ".batter", "batter is how far the walls draw in from their foot to their top (or to "
                "`batter_height`): more than 0, up to 1024 map units (the Plane of Fire's guard towers: 64 over 768)");
            part.batter = 0.0;
        }

        // S8d: `flare`, walls that lean out from their foot to their top by this much (Erathia's Castle
        // Gryphonheart: the bailey 150 over 512, its towers about 40): a batter the other way, kept as a negative
        // batter. No door on a flaring wall.
        if (childOf(node, "flare").IsDefined())
        {
            double flare = 0.0;

            if (childOf(node, "batter").IsDefined() || !numberOf(node, "flare", flare) || flare <= 0.0
                || flare > 1024.0)
            {
                add(at + ".flare", "flare is how far the walls lean out from their foot to their top (or to "
                    "`batter_height`): more than 0, up to 1024 map units (Erathia's castle bailey: 150 over 512); not "
                    "with `batter`");
            }
            else
            {
                part.batter = -flare;
            }
        }

        if (childOf(node, "batter_height").IsDefined() && (part.batter == 0.0 || !numberOf(node, "batter_height",
            part.batterHeight) || part.batterHeight < 16.0 || part.batterHeight > part.wallHeight))
        {
            add(at + ".batter_height", "batter_height is how high the sloping foot of a battered part rises (the "
                "walls stand upright above it): 16 up to the walls' height (" + formatNumber(part.wallHeight)
                + "), with `batter` or `flare`");
            part.batterHeight = 0.0;
        }

        if (part.batter != 0.0 && (part.taper != 1.0 || part.posts > 0.0 || part.climb > 0.0 || !part.holes.empty()
            || part.wallHeight < 16.0))
        {
            add(at + (part.batter > 0.0 ? ".batter" : ".flare"), "a battered part has walls (16 or more high) that "
                "lean in at their foot (or out, with `flare`): no `taper`, `posts`, `climb` or `holes` with it");
            part.batter = 0.0;
        }

        if (part.batter != 0.0 && !part.windowArch.empty())
        {
            add(at + ".window_arch", "arched windows stand on upright walls; this part is battered");
        }

        // S8d: `pent: {height, out, rise, thickness}`, a skirt roof round the walls.
        const YAML::Node pent = childOf(node, "pent");

        if (pent.IsDefined())
        {
            const bool readable = pent.IsMap() && numberOf(pent, "height", part.pentHeight)
                && (!childOf(pent, "out").IsDefined() || numberOf(pent, "out", part.pentOut))
                && (!childOf(pent, "rise").IsDefined() || numberOf(pent, "rise", part.pentRise))
                && (!childOf(pent, "thickness").IsDefined() || numberOf(pent, "thickness", part.pentThickness));

            if (!readable || part.pentHeight < 64.0 || part.pentHeight + part.pentRise > part.wallHeight - 16.0
                || part.pentOut < 16.0 || part.pentOut > 512.0 || part.pentRise < 0.0 || part.pentRise > 512.0
                || part.pentThickness < 4.0 || part.pentThickness > 64.0 || part.concave || part.taper != 1.0
                || part.batter != 0.0 || childOf(node, "posts").IsDefined())
            {
                add(at + ".pent", "a pent is {height: where its edge is over the part's foot, 64 up, its top at the "
                    "wall (height + rise) 16 under the walls' top (" + formatNumber(part.wallHeight) + "); out: 16 "
                    "to 512 (128); rise: 0 to 512 (64); thickness: its edge, 4 to 64 (16)}, round the upright walls "
                    "of a part that does not bend in (no taper, batter, flare or posts)");
                part.pentHeight = 0.0;
            }
        }

        const YAML::Node buttresses = childOf(node, "buttresses");

        if (buttresses.IsDefined())
        {
            OutdoorButtressPlan &plan = part.buttresses;
            double count = 0.0;
            const bool readable = buttresses.IsMap() && numberOf(buttresses, "count", count)
                && (!childOf(buttresses, "width").IsDefined() || numberOf(buttresses, "width", plan.width))
                && (!childOf(buttresses, "depth").IsDefined() || numberOf(buttresses, "depth", plan.depth))
                && (!childOf(buttresses, "height").IsDefined() || numberOf(buttresses, "height", plan.height));
            plan.count = static_cast<int>(count);

            if (!readable || count < 1.0 || count > 16.0 || count != std::floor(count) || plan.width < 16.0
                || plan.width > 512.0 || plan.depth < 16.0 || plan.depth > 512.0 || plan.height < 0.0
                || plan.height > part.wallHeight || (plan.height > 0.0 && plan.height <= plan.depth))
            {
                add(at + ".buttresses", "buttresses are {count (1 to 16 on each wall named), width (16 to 512; 64), "
                    "depth (how far they stand out, 16 to 512; 64), height (at the wall, more than their depth and "
                    "up to the walls' height; left out: the walls' height), walls (all when left out)}: each top "
                    "slopes down to the front by its depth");
                plan.count = 0;
            }
            else if (part.posts > 0.0 || part.taper != 1.0)
            {
                add(at + ".buttresses", "buttresses stand against upright walls: no `posts` or `taper`");
                plan.count = 0;
            }
            else if (plan.height <= 0.0)
            {
                plan.height = part.wallHeight;
            }
        }

        if (childOf(node, "door_height").IsDefined() && (!numberOf(node, "door_height", part.doorHeight)
            || part.doorHeight < 128.0 || part.doorHeight > 1024.0))
        {
            add(at + ".door_height", "door_height is how high a door of the part stands, 128 to 1024 (256 when left "
                "out); a door higher than the walls is cut into the roof over them");
            part.doorHeight = 0.0;
        }

        const YAML::Node steps = childOf(node, "steps");

        if (steps.IsDefined())
        {
            std::vector<Point2> ring = part.outline;
            bool good = steps.IsSequence() && steps.size() >= 1 && steps.size() <= 16 && part.posts <= 0.0
                && part.taper == 1.0 && part.roof.parapet <= 0.0;

            for (size_t index = 0; good && index < steps.size(); ++index)
            {
                Point2 step = {0.0, 0.0};
                std::vector<Point2> next;
                good = pointOf(steps[index], step) && step[0] >= 0.0 && step[0] <= 2048.0 && step[1] > 0.0
                    && step[1] <= 2048.0;

                if (good)
                {
                    next = grown(ring, -step[0]);
                    good = keepsShape(ring, next);
                }

                if (good)
                {
                    part.steps.push_back(step);
                    ring = next;
                }
            }

            if (!good)
            {
                add(at + ".steps", "steps are 1 to 16 terraces over the walls' top, each [in, up] in map units (in 0 "
                    "to 2048: how far the next is drawn in; up above 0 to 2048: its upright riser), each keeping the "
                    "outline's shape (not drawn in past its middle), on upright walls or a battered part without "
                    "`posts` or a parapet: Dragonsand's pyramid [[256, 256], [256, 256], [256, 256], [256, 256]]");
                part.steps.clear();
            }
        }

        const YAML::Node ruin = fieldOf(node, m_plot, "ruin");

        if (ruin.IsDefined())
        {
            OutdoorRuinPlan &plan = part.ruin;
            plan.given = true;
            plan.low = part.wallHeight * 0.5;
            plan.high = part.wallHeight;
            Point2 heights = {plan.low, plan.high};
            double seed = 1.0;
            const YAML::Node heightNode = childOf(ruin, "height");
            const bool readable = ruin.IsMap() && (!heightNode.IsDefined() || pointOf(heightNode, heights))
                && (!childOf(ruin, "gaps").IsDefined() || numberOf(ruin, "gaps", plan.gaps))
                && (!childOf(ruin, "thickness").IsDefined() || numberOf(ruin, "thickness", plan.thickness))
                && (!childOf(ruin, "every").IsDefined() || numberOf(ruin, "every", plan.every))
                && (!childOf(ruin, "rafter").IsDefined() || numberOf(ruin, "rafter", plan.rafter))
                && (!childOf(ruin, "seed").IsDefined() || numberOf(ruin, "seed", seed));
            plan.roof = textOf(ruin, "roof", "none");
            plan.low = heights[0];
            plan.high = heights[1];
            plan.seed = static_cast<uint32_t>(std::max(0.0, seed));

            if (!readable || plan.low < 0.0 || plan.high < plan.low || plan.high > part.wallHeight + 0.5
                || plan.gaps < 0.0 || plan.gaps > 0.9 || plan.thickness < 0.0 || plan.thickness > 128.0
                || (plan.roof != "none" && plan.roof != "frame") || plan.every < 0.0 || plan.every > 2048.0
                || plan.rafter < 4.0 || plan.rafter > 64.0)
            {
                add(at + ".ruin", "a ruin is {height: [low, high] (each bay's wall stands to its own height between "
                    "them over the floor, up to the walls' " + formatNumber(part.wallHeight) + "; left out: half to "
                    "whole), gaps (the share of bays gone, 0 to 0.9), thickness (the walls' thickness, 0 to 128; 8), "
                    "roof: none | frame (bare rafters and a ridge beam), every (rafters between the ends this far "
                    "apart; 0: at the ends only), rafter (their width, 4 to 64; 16), seed}");
                plan.given = false;
            }
            else if (part.posts > 0.0 || part.taper != 1.0 || part.batter != 0.0 || !part.steps.empty())
            {
                add(at + ".ruin", "a ruin is a part of upright walls: no `posts`, `taper`, `batter` or `steps`");
                plan.given = false;
            }
        }
    }

    // Whether an outline drawn in (`next`) keeps the shape of the one it comes from: convex, every side running
    // the same way and some left of it.
    static bool keepsShape(const std::vector<Point2> &ring, const std::vector<Point2> &next)
    {
        if (next.size() != ring.size() || !convex(next) || signedArea(next) < 64.0)
        {
            return false;
        }

        for (size_t index = 0; index < ring.size(); ++index)
        {
            const Point2 &from = ring[index];
            const Point2 &to = ring[(index + 1) % ring.size()];
            const Point2 &nextFrom = next[index];
            const Point2 &nextTo = next[(index + 1) % next.size()];

            if ((to[0] - from[0]) * (nextTo[0] - nextFrom[0]) + (to[1] - from[1]) * (nextTo[1] - nextFrom[1]) <= 0.0)
            {
                return false;
            }
        }

        return true;
    }

    // An open part: posts at its corners in place of walls, a low wall between them where asked.
    void readOpenPart(const YAML::Node &node, const std::string &at, OutdoorPartPlan &part)
    {
        const bool posted = childOf(node, "posts").IsDefined();

        if (posted && (!numberOf(node, "posts", part.posts) || part.posts < 8.0 || part.posts > 256.0))
        {
            add(at + ".posts", "posts is how wide the posts of an open part are (a pavilion, a shrine on pillars): "
                "8 to 256 map units (Harmondale's shrines: 32)");
            part.posts = 0.0;
            return;
        }

        const std::string postsShape = textOf(node, "posts_shape", "square");
        part.roundPosts = postsShape == "round";

        if (postsShape != "square" && postsShape != "round")
        {
            add(at + ".posts_shape", "posts_shape is square (the default) or round (a column on a base under a "
                "capital: Evenmorn's Temple of the Sun, the Haunted Mansion's portico)");
            return;
        }

        for (const char *pKey : {"post_every", "sill", "sill_walls", "post_walls", "posts_shape"})
        {
            if (!posted && childOf(node, pKey).IsDefined())
            {
                add(at + "." + pKey, std::string("`") + pKey + "` belongs to an open part: give it `posts`");
                return;
            }
        }

        if (!posted)
        {
            return;
        }

        if ((childOf(node, "post_every").IsDefined() && (!numberOf(node, "post_every", part.postEvery)
            || part.postEvery < part.posts * 2.0 || part.postEvery > 4096.0))
            || (childOf(node, "sill").IsDefined() && (!numberOf(node, "sill", part.sill) || part.sill < 8.0
            || part.sill > part.wallHeight - 32.0)))
        {
            add(at, "an open part's `post_every` is the widest gap between two posts along a wall (at least twice "
                "the posts' width, up to 4096; left out: posts at the corners only), and its `sill` the height of "
                "a low wall between the posts, 8 up to 32 under the top of its posts");
            part.postEvery = 0.0;
            part.sill = 0.0;
        }

        if (part.taper != 1.0 || part.climb > 0.0)
        {
            add(at + ".posts", "an open part stands on upright posts: it takes no `taper` or `climb`");
        }
    }

    // Holes in a flat top (a hatch's pit in a dais): `holes: [{at: [x, y], size: [w, d], depth: 64}]`, in the
    // plot's frame as a box part's corner and size.
    void readHoles(const YAML::Node &node, const std::string &at, OutdoorPartPlan &part)
    {
        const YAML::Node holes = childOf(node, "holes");

        for (size_t index = 0; holes.IsDefined() && index < (holes.IsSequence() ? holes.size() : 1); ++index)
        {
            const std::string where = at + ".holes[" + std::to_string(index) + "]";
            const YAML::Node hole = holes.IsSequence() ? holes[index] : holes;
            Point2 corner = {0.0, 0.0};
            Point2 size = {0.0, 0.0};
            OutdoorHolePlan plan;

            if (!holes.IsSequence() || !pointOf(childOf(hole, "at"), corner) || !pointOf(childOf(hole, "size"), size)
                || size[0] < 16.0 || size[1] < 16.0 || (childOf(hole, "depth").IsDefined()
                && (!numberOf(hole, "depth", plan.depth) || plan.depth < 8.0 || plan.depth > 1024.0)))
            {
                add(where, "a hole is {at: [x, y] (its north-west corner, map units east and south of the plot's "
                    "north-west corner), size: [width, depth] (16 or more each), depth: <how deep its pit goes, 8 "
                    "to 1024; 64 when left out>}");
                return;
            }

            if (part.roof.form != "flat" || part.roof.parapet > 0.0 || part.taper != 1.0)
            {
                add(where, "a hole is cut in a flat top: the part has `roof: flat` without a parapet, on upright "
                    "walls");
                return;
            }

            for (const Point2 &local : {Point2{corner[0], corner[1] + size[1]}, Point2{corner[0] + size[0],
                     corner[1] + size[1]}, Point2{corner[0] + size[0], corner[1]}, corner})
            {
                plan.outline.push_back(toWorld(local));
            }

            for (const Point2 &point : plan.outline)
            {
                if (!insideConvex(grown(part.outline, -8.0), point))
                {
                    add(where, "the hole reaches to within 8 of the part's walls or past them: it is cut in the "
                        "part's top, inside its outline");
                    return;
                }
            }

            for (const OutdoorHolePlan &other : part.holes)
            {
                if (convexOverlap(other.outline, plan.outline))
                {
                    add(where, "the hole overlaps another of the part's holes: make them one");
                    return;
                }
            }

            part.holes.push_back(plan);
        }
    }

    // An open court through a box part (batch O-H): `court: {at: [x, y], size: [width, depth], eaves}`, in the plot's
    // frame as a box part's corner and size.
    void readCourt(const YAML::Node &node, const std::string &at, OutdoorPartPlan &part)
    {
        const YAML::Node court = childOf(node, "court");

        if (!court.IsDefined())
        {
            return;
        }

        Point2 corner = {0.0, 0.0};
        Point2 size = {0.0, 0.0};
        const std::string where = at + ".court";

        if (!court.IsMap() || !pointOf(childOf(court, "at"), corner) || !pointOf(childOf(court, "size"), size)
            || size[0] < 64.0 || size[1] < 64.0 || (childOf(court, "eaves").IsDefined()
            && (!numberOf(court, "eaves", part.courtEaves) || part.courtEaves < 0.0 || part.courtEaves > 512.0)))
        {
            add(where, "a court is {at: [x, y] (its north-west corner, map units east and south of the plot's "
                "north-west corner), size: [width, depth] (64 or more each), eaves: <how far the roof reaches out "
                "over the court's walls, 0 to 512; 0>}");
            return;
        }

        const OutdoorRoofPlan &roof = part.roof;

        if (part.shape != "box" || (roof.form != "hip" && roof.form != "flat") || roof.parapet > 0.0
            || part.posts > 0.0 || part.taper != 1.0 || part.batter != 0.0 || !part.steps.empty() || part.ruin.given
            || !part.holes.empty() || part.stair.given || !roof.eavesWalls.empty() || !roof.tiers.empty()
            || roof.cap > 0.0 || part.concave)
        {
            add(where, "a court goes through a box part with upright walls under a hip or a flat roof (no parapet, "
                "posts, taper, batter, steps, ruin, holes, stair, eaves_walls, tiers or cap)");
            return;
        }

        std::vector<Point2> outline;

        for (const Point2 &local : {Point2{corner[0], corner[1] + size[1]}, Point2{corner[0] + size[0],
                 corner[1] + size[1]}, Point2{corner[0] + size[0], corner[1]}, corner})
        {
            outline.push_back(toWorld(local));
        }

        for (const Point2 &point : outline)
        {
            if (!insideConvex(grown(part.outline, -64.0), point))
            {
                add(where, "the court reaches to within 64 of the part's walls or past them: it lies inside the "
                    "part's outline, a wing at least 64 wide on every side");
                return;
            }
        }

        // Each corner of the court paired with the part's corner nearest it.
        size_t first = 0;
        double nearest = 1.0e18;

        for (size_t index = 0; index < outline.size(); ++index)
        {
            const double distance = lengthOf(outline[index], part.outline[0]);

            if (distance < nearest)
            {
                nearest = distance;
                first = index;
            }
        }

        std::rotate(outline.begin(), outline.begin() + static_cast<std::ptrdiff_t>(first), outline.end());
        part.court = outline;
    }

    // Whether two convex outlines (counter-clockwise) share area: no side of either separates them.
    static bool convexOverlap(const std::vector<Point2> &first, const std::vector<Point2> &second)
    {
        for (const std::vector<Point2> *pOutline : {&first, &second})
        {
            const std::vector<Point2> &outline = *pOutline;
            const std::vector<Point2> &other = pOutline == &first ? second : first;

            for (size_t index = 0; index < outline.size(); ++index)
            {
                const Point2 &from = outline[index];
                const Point2 &to = outline[(index + 1) % outline.size()];
                const bool apart = std::all_of(other.begin(), other.end(), [&from, &to](const Point2 &point)
                {
                    return (to[0] - from[0]) * (point[1] - from[1]) - (to[1] - from[1]) * (point[0] - from[0])
                        <= 0.5;
                });

                if (apart)
                {
                    return false;
                }
            }
        }

        return true;
    }

    // Which walls of the parts that are climbed stand over a lower floor, and how far: the floor in front of a wall
    // is the highest flat top of the building's other parts there that is lower than the part's own top, or the
    // building's floor; a wall that faces a part as high as its own top is not climbed.
    void readClimbs(OutdoorBuildingPlan &building)
    {
        for (size_t index = 0; index < building.parts.size(); ++index)
        {
            OutdoorPartPlan &part = building.parts[index];
            const std::string at = (m_partNodes[index].IsDefined() ? ".parts[" + std::to_string(index) + "]" : "")
                + ".climb";

            if (part.climb <= 0.0)
            {
                continue;
            }

            const OutdoorRoofPlan &roof = part.roof;

            if (roof.form != "flat" || roof.eaves > 0.0 || roof.fascia > 0.0 || roof.parapet > 0.0
                || part.taper != 1.0)
            {
                add(at, "a part the party climbs is a step: a flat top to stand on (`roof: flat` with `eaves: 0`, "
                    "`fascia: 0` and no parapet) on upright walls (no taper)");
                continue;
            }

            const std::vector<Point2> inner = grown(part.outline, -part.climb);
            bool fits = convex(inner) && signedArea(inner) > 0.0;

            for (size_t wall = 0; fits && wall < inner.size(); ++wall)
            {
                const Point2 &from = part.outline[wall];
                const Point2 &to = part.outline[(wall + 1) % inner.size()];
                const Point2 &innerFrom = inner[wall];
                const Point2 &innerTo = inner[(wall + 1) % inner.size()];
                fits = (to[0] - from[0]) * (innerTo[0] - innerFrom[0]) + (to[1] - from[1]) * (innerTo[1] - innerFrom[1])
                    > 0.0;
            }

            if (!fits)
            {
                add(at, "the hidden slope reaches " + formatNumber(part.climb) + " in from the walls, past the "
                    "middle of the part: make `climb` shorter");
                continue;
            }

            const double top = part.bottom + part.wallHeight;
            part.climbFrom.assign(part.outline.size(), std::nullopt);
            size_t climbed = 0;

            for (size_t wall = 0; wall < part.outline.size(); ++wall)
            {
                const Point2 &left = part.outline[wall];
                const Point2 &right = part.outline[(wall + 1) % part.outline.size()];
                const double length = std::max(lengthOf(left, right), 1.0e-9);
                // A little way out from the wall's middle.
                const Point2 probe = {(left[0] + right[0]) * 0.5 + (right[1] - left[1]) / length * 8.0,
                    (left[1] + right[1]) * 0.5 - (right[0] - left[0]) / length * 8.0};
                double floor = 0.0;
                bool faced = false;

                for (size_t other = 0; other < building.parts.size(); ++other)
                {
                    const OutdoorPartPlan &otherPart = building.parts[other];
                    const double otherTop = otherPart.bottom + otherPart.wallHeight;

                    if (other == index || otherPart.bottom >= top || !insideConvex(otherPart.outline, probe))
                    {
                        continue;
                    }

                    if (otherTop >= top - 0.5)
                    {
                        faced = true;
                    }
                    else if (otherPart.roof.form == "flat" && otherPart.roof.parapet <= 0.0)
                    {
                        floor = std::max(floor, otherTop + otherPart.roof.fascia);
                    }
                }

                const double riser = top - floor;

                if (faced || riser <= 0.5)
                {
                    continue;
                }

                if (floor < part.bottom - 0.5 || riser > 64.0)
                {
                    add(at, "wall " + std::to_string(wall + 1) + " of the part stands from " + formatNumber(part.bottom)
                        + " to " + formatNumber(top) + " over a floor at " + formatNumber(floor) + " (above the "
                        "building's floor): a step the party walks up reaches down to the floor in front of it and "
                        "is at most 64 high (the shipped maps' steps: 16 to 32); make it parts of 32, or `stairs`");
                    continue;
                }

                part.climbFrom[wall] = floor;
                ++climbed;
            }

            if (climbed == 0)
            {
                add(at, "no wall of the part stands over a lower floor, so there is nothing to climb: leave `climb` "
                    "out");
            }
        }
    }

    static bool insideConvex(const std::vector<Point2> &outline, const Point2 &point)
    {
        for (size_t index = 0; index < outline.size(); ++index)
        {
            const Point2 &from = outline[index];
            const Point2 &to = outline[(index + 1) % outline.size()];

            if ((to[0] - from[0]) * (point[1] - from[1]) - (to[1] - from[1]) * (point[0] - from[0]) < 0.0)
            {
                return false;
            }
        }

        return true;
    }

    void readTextures(const YAML::Node &node, const std::string &at, OutdoorPartPlan &part)
    {
        const std::string kitName = textField(node, "kit");
        const Kit *pKit = findKit(m_world, kitName);

        // A part of a world without kits names its textures (checked below); only a kit it names must exist.
        if (pKit == nullptr && !kitName.empty())
        {
            add(at + ".kit", "the world " + m_world + " has no kit `" + kitName + "`; its kits are "
                + joined(outdoorKitNames(m_world)) + ", or name the textures one by one in `textures`");
            pKit = findKit(m_world, "");
        }

        if (pKit != nullptr)
        {
            for (const KitRole &role : pKit->roles)
            {
                part.textures[role.pRole] = role.pTexture;
            }
        }

        for (const YAML::Node &source : {childOf(m_plot, "textures"), childOf(node, "textures")})
        {
            if (!source.IsDefined() || !source.IsMap())
            {
                continue;
            }

            for (YAML::const_iterator entry = source.begin(); entry != source.end(); ++entry)
            {
                noteRead(entry->second);

                if (entry->second.IsScalar())
                {
                    part.textures[entry->first.Scalar()] = entry->second.Scalar();
                }
                else if (entry->second.IsMap())
                {
                    // A liquid: {texture, liquid: water | lava, flow} (Hermit's Isle's lava temple, the Plane of
                    // Fire's lava streams down the homes' tiers).
                    const auto word = [&entry](const char *pKey)
                    {
                        return textOf(entry->second, pKey);
                    };
                    const std::string name = word("texture");
                    const uint32_t bits = outdoorLiquidBits(word("liquid"), word("flow"), m_world);
                    // A picture laid once per bay: {texture, fit: true, size: [w, h]} (A6, the texture-fit rule).
                    const bool fit = word("fit") == "true";
                    const YAML::Node size = childOf(entry->second, "size");
                    const bool sized = size.IsDefined() && size.IsSequence() && size.size() == 2
                        && size[0].IsScalar() && size[1].IsScalar();
                    const std::array<double, 2> picture = sized
                        ? std::array<double, 2>{std::atof(size[0].Scalar().c_str()), std::atof(size[1].Scalar().c_str())}
                        : std::array<double, 2>{0.0, 0.0};

                    if (name.empty() || bits == UINT32_MAX || (!word("fit").empty() && word("fit") != "true"
                            && word("fit") != "false")
                        || (fit && (bits != 0 || picture[0] < 8.0 || picture[1] < 8.0))
                        || (!fit && size.IsDefined()))
                    {
                        add(at + ".textures." + entry->first.Scalar(), "a texture is a name, or {texture: <name>, "
                            "liquid: water | lava, flow: up | down | left | right}, or a picture laid once per bay "
                            "{texture: <name>, fit: true, size: [width, height] (the picture's texels)}");
                        continue;
                    }

                    part.textures[entry->first.Scalar()] = name;

                    if (fit)
                    {
                        part.fitted[entry->first.Scalar()] = picture;
                    }
                    else if (bits != 0)
                    {
                        part.liquids[name] |= bits;
                    }
                }
            }
        }

        // What a kit or a plot leaves out: the gable and the base course are wall, the trim and the ridge roof.
        const auto fallback = [&part](const char *pRole, const char *pFrom)
        {
            if (!part.textures.contains(pRole) && part.textures.contains(pFrom))
            {
                part.textures[pRole] = part.textures[pFrom];
            }
        };
        fallback("gable", "wall");
        fallback("base", "wall");
        fallback("trim", "roof");
        fallback("ridge", "trim");
        fallback("parapet", "wall");

        for (const char *pRole : {"wall", "roof", "door"})
        {
            if (!part.textures.contains(pRole))
            {
                add(at + ".textures", std::string("no texture for `") + pRole + "`: the world " + m_world
                    + " has no kits, so name wall, roof and door in `textures`");
            }
        }
    }

    void readRoof(const YAML::Node &node, const std::string &at, OutdoorPartPlan &part)
    {
        OutdoorRoofPlan &roof = part.roof;
        const bool box = part.shape == "box";
        const YAML::Node formNode = fieldOf(node, m_plot, "roof");
        // What the world's ordinary house has; a part that is no box gets the tip its form allows.
        roof.form = m_pWorldRoof != nullptr ? m_pWorldRoof->pForm : "hip";
        double pitch = 0.0;

        if (m_pWorldRoof != nullptr)
        {
            roof.rise = m_pWorldRoof->rise;
            pitch = m_pWorldRoof->pitch;
            roof.eaves = m_pWorldRoof->eaves;
            roof.fascia = m_pWorldRoof->fascia;
            roof.hipRun = m_pWorldRoof->hipRun;
            roof.ridge = m_pWorldRoof->ridge;
        }

        if (!box)
        {
            roof.form = "cone";
        }

        if (formNode.IsDefined() && formNode.IsScalar())
        {
            if (formNode.Scalar() != roof.form)
            {
                // Another form than the world's ordinary one: nothing of that one's trimmings is assumed.
                roof.hipRun = 0.0;
                roof.ridge = 0.0;
            }

            roof.form = formNode.Scalar();
        }

        const std::vector<std::string> forms = box
            ? std::vector<std::string>{"flat", "hip", "gable", "lean_to", "cone", "dome", "none", "vault"}
            : std::vector<std::string>{"flat", "hip", "gable", "cone", "dome", "none"};

        if (std::find(forms.begin(), forms.end(), roof.form) == forms.end())
        {
            add(at + ".roof", "the roof of a " + part.shape + " part is " + joined(forms) + "; `" + roof.form
                + "` is none of them" + (box ? "" : " (a lean_to needs a box; so does a vault)"));
            return;
        }

        if (!box)
        {
            // A ridge beam is a box's. Without `hip` a hip roof on any other outline slopes alike from every
            // wall; with it the end walls' slopes reach the ridge after that run (the ridge drawn in).
            double beam = 0.0;

            if (numberOf(node, "ridge", beam) && beam > 0.0)
            {
                add(at, "`ridge` (the beam along the ridge) is for a box: leave it out on an outline or round "
                    "part");
            }

            roof.hipRun = 0.0;
            roof.ridge = 0.0;
        }

        const bool ownHeight = numberOfNode(fieldOf(node, m_plot, "roof_height"), roof.rise);
        const bool ownPitch = numberOfNode(fieldOf(node, m_plot, "roof_pitch"), pitch);
        numberOfNode(fieldOf(node, m_plot, "eaves"), roof.eaves);
        numberOfNode(fieldOf(node, m_plot, "fascia"), roof.fascia);
        numberOfNode(fieldOf(node, m_plot, "hip"), roof.hipRun);
        numberOfNode(fieldOf(node, m_plot, "ridge"), roof.ridge);
        numberOfNode(fieldOf(node, m_plot, "parapet"), roof.parapet);
        const bool capped = numberOfNode(fieldOf(node, m_plot, "cap"), roof.cap);

        if (capped && roof.form != "hip")
        {
            add(at + ".cap", "`cap` cuts a hip roof flat on top: it is for `roof: hip`, not " + roof.form);
            roof.cap = 0.0;
        }

        if (roof.cap > 0.0)
        {
            // A flat top has no ridge to carry a beam.
            roof.ridge = 0.0;
        }

        const YAML::Node tiers = fieldOf(node, m_plot, "tiers");

        if (tiers.IsDefined())
        {
            double total = 0.0;

            for (size_t index = 0; tiers.IsSequence() && index < tiers.size(); ++index)
            {
                Point2 tier = {0.0, 0.0};

                if (!pointOf(tiers[index], tier) || tier[0] < 0.0 || tier[0] > 2048.0 || tier[1] <= 0.0
                    || tier[1] > 2048.0)
                {
                    roof.tiers.clear();
                    break;
                }

                roof.tiers.push_back(tier);
                total += tier[1];
            }

            if (roof.tiers.empty() || roof.tiers.size() > 8
                || (roof.form != "cone" && roof.form != "hip" && roof.form != "vault")
                || roof.cap > 0.0 || childOf(node, "roof_height").IsDefined() || childOf(node, "roof_pitch").IsDefined())
            {
                add(at + ".tiers", "tiers is a cone or hip roof in 1 to 8 rings from its foot, each [in, up] in map "
                    "units (in 0 to 2048, up above 0 to 2048): Harmondale's training hall [[144, 192], [128, 64], "
                    "[80, 32]]; or a vault's section from each eaves side. Its height is the sum of the ups: leave "
                    "out `roof_height`, `roof_pitch` and `cap`");
                roof.tiers.clear();
            }
            else if (roof.form == "vault")
            {
                // A vault's section (checked with the span below, once the ridge's way is read).
                roof.rise = total;
            }
            else
            {
                roof.rise = total;
                roof.ridge = 0.0;
                roof.hipRun = 0.0;
                // Each ring must keep the outline's shape, but a cone's last may reach the middle (its tip).
                Point2 middle = {0.0, 0.0};

                for (const Point2 &point : part.outline)
                {
                    middle = {middle[0] + point[0] / part.outline.size(), middle[1] + point[1] / part.outline.size()};
                }

                std::vector<Point2> ring;

                for (const Point2 &point : part.outline)
                {
                    ring.push_back({middle[0] + (point[0] - middle[0]) * part.taper,
                        middle[1] + (point[1] - middle[1]) * part.taper});
                }

                ring = grown(ring, roof.eaves);

                for (size_t index = 0; index < roof.tiers.size(); ++index)
                {
                    std::vector<Point2> next;

                    if (!drawnIn(ring, roof.tiers[index][0], next)
                        && (index + 1 < roof.tiers.size() || roof.form != "cone"))
                    {
                        add(at + ".tiers", "ring " + std::to_string(index + 1) + " of the roof draws in past the "
                            "middle of the part: only a cone's last ring may reach it (its tip); a hip's rings end in "
                            "a flat top. Draw the rings in less");
                        roof.tiers.clear();
                        break;
                    }

                    ring = next;
                }
            }
        }

        if (roof.form == "dome")
        {
            roof.ridge = 0.0;
            roof.hipRun = 0.0;
            double rings = 4.0;
            const YAML::Node ringNode = fieldOf(node, m_plot, "dome_rings");

            if (ringNode.IsDefined() && (!numberOfNode(ringNode, rings) || rings < 2.0 || rings > 8.0
                || rings != std::floor(rings)))
            {
                add(at + ".dome_rings", "dome_rings is how many rings the dome's quarter circle has from its foot to "
                    "its tip: a whole number, 2 to 8 (4 when left out)");
                rings = 4.0;
            }

            roof.domeRings = static_cast<int>(rings);

            if (!roof.tiers.empty())
            {
                add(at + ".tiers", "a dome is a quarter circle in rings (`dome_rings`), not `tiers`");
                roof.tiers.clear();
            }
        }
        else if (fieldOf(node, m_plot, "dome_rings").IsDefined())
        {
            add(at + ".dome_rings", "`dome_rings` belongs to `roof: dome`");
        }

        const YAML::Node battlements = fieldOf(node, m_plot, "battlements");
        roof.battlements = battlements.IsDefined() && battlements.IsScalar() && battlements.Scalar() == "true";
        const std::string along = textField(node, "ridge_along");
        const std::string low = textField(node, "roof_low", textOf(m_plot, "facing", "s"));

        if (roof.form == "lean_to")
        {
            // The low wall: s, e, n or w are the box's walls 0 to 3; the ridge code is the wall's number.
            const size_t wall = std::string("senw").find(low.empty() ? 's' : low[0]);
            roof.along = static_cast<char>('0' + (wall == std::string::npos ? 0 : wall));
            roof.eaves = 0.0;
        }
        else if (!along.empty())
        {
            // East-west is the box's first side.
            roof.along = along == "ew" ? 'x' : (along == "ns" ? 'y' : 0);

            if (roof.along == 0)
            {
                add(at + ".ridge_along", "ridge_along is ew (the ridge runs east-west, before the plot is turned) "
                    "or ns");
            }
        }

        if (roof.form == "vault")
        {
            readVault(node, at, part, ownHeight, ownPitch);
        }
        else if (fieldOf(node, m_plot, "vault_segments").IsDefined())
        {
            add(at + ".vault_segments", "`vault_segments` belongs to `roof: vault`");
        }

        if ((!box && (roof.form == "gable" || roof.form == "hip")) || roof.cap > 0.0)
        {
            // The ridge of a gable (and of a hip with `hip`, and of a capped hip on a box) on any outline: as said
            // (east-west or north-south of the plot before it is turned), else along the outline's longest wall.
            Point2 from = part.outline[0];
            Point2 to = part.outline[1];

            if (roof.along != 0)
            {
                from = toWorld({0.0, 0.0});
                to = roof.along == 'x' ? toWorld({1.0, 0.0}) : toWorld({0.0, 1.0});
            }
            else
            {
                for (size_t index = 0; index < part.outline.size(); ++index)
                {
                    const Point2 &start = part.outline[index];
                    const Point2 &end = part.outline[(index + 1) % part.outline.size()];

                    if (lengthOf(start, end) > lengthOf(from, to) + 1.0e-6)
                    {
                        from = start;
                        to = end;
                    }
                }
            }

            const double length = std::max(lengthOf(from, to), 1.0e-9);
            roof.ridgeDirection = {(to[0] - from[0]) / length, (to[1] - from[1]) / length};
        }

        if (roof.form == "flat" || roof.form == "none")
        {
            roof.rise = 0.0;
            roof.ridge = 0.0;
        }
        else if (roof.form == "dome" && !ownHeight && !ownPitch)
        {
            // A half sphere: as high as the outline (with its eaves) is wide from its middle, on the average.
            Point2 middle = {0.0, 0.0};

            for (const Point2 &point : part.outline)
            {
                middle = {middle[0] + point[0] / part.outline.size(), middle[1] + point[1] / part.outline.size()};
            }

            double radius = 0.0;

            for (const Point2 &point : part.outline)
            {
                radius += lengthOf(middle, point) * part.taper / part.outline.size();
            }

            roof.rise = std::round(radius + roof.eaves);
        }
        else if (roof.form != "vault" && roof.tiers.empty()
            && (ownPitch || (!ownHeight && pitch > 0.0 && roof.form != "dome")))
        {
            if (pitch <= 0.0 || pitch >= 85.0)
            {
                add(at + ".roof_pitch", "roof_pitch is more than 0 and less than 85 degrees");
                return;
            }

            // The run the pitch is over: half the span under the ridge, the whole depth of a lean-to, the least
            // distance from the middle to a side under a cone.
            double run = 0.0;

            if (box)
            {
                const double first = lengthOf(part.outline[0], part.outline[1]) + 2.0 * roof.eaves;
                const double second = lengthOf(part.outline[1], part.outline[2]) + 2.0 * roof.eaves;
                const bool alongFirst = roof.along == 'x' || (roof.along == 0 && first >= second);

                if (roof.form == "lean_to")
                {
                    run = (roof.along - '0') % 2 == 0 ? second : first;
                }
                else if (roof.form == "cone")
                {
                    run = std::min(first, second) * 0.5;
                }
                else
                {
                    run = (alongFirst ? second : first) * 0.5;
                }
            }
            else
            {
                Point2 middle = {0.0, 0.0};

                for (const Point2 &point : part.outline)
                {
                    middle = {middle[0] + point[0] / part.outline.size(), middle[1] + point[1] / part.outline.size()};
                }

                run = 1.0e18;

                for (size_t index = 0; index < part.outline.size(); ++index)
                {
                    const Point2 &from = part.outline[index];
                    const Point2 &to = part.outline[(index + 1) % part.outline.size()];
                    const double length = std::max(lengthOf(from, to), 1.0e-9);
                    run = std::min(run, std::fabs((to[0] - from[0]) * (middle[1] - from[1])
                        - (to[1] - from[1]) * (middle[0] - from[0])) / length + roof.eaves);
                }

                if (roof.form == "gable")
                {
                    // Under a gable: half the outline's width across the ridge.
                    double least = 1.0e18;
                    double most = -1.0e18;

                    for (const Point2 &point : part.outline)
                    {
                        const double side = -point[0] * roof.ridgeDirection[1] + point[1] * roof.ridgeDirection[0];
                        least = std::min(least, side);
                        most = std::max(most, side);
                    }

                    run = (most - least) * 0.5 + roof.eaves;
                }
            }

            roof.rise = std::round(run * oy::tan(pitch * Pi / 180.0));
            roof.slope = oy::tan(pitch * Pi / 180.0);
        }

        if (roof.rise < 0.0 || roof.rise > 4096.0 || roof.eaves < 0.0 || roof.eaves > 256.0 || roof.fascia < 0.0
            || roof.fascia > 256.0 || roof.hipRun < 0.0 || roof.ridge < 0.0 || roof.ridge > 128.0
            || roof.parapet < 0.0 || roof.parapet > 512.0)
        {
            add(at, "a roof rises 0 to 4096 (roof_height), with eaves and a fascia of 0 to 256 each, a ridge beam "
                "of 0 to 128 and a parapet of 0 to 512");
        }

        if ((roof.parapet > 0.0 || roof.battlements) && roof.form != "flat")
        {
            add(at + ".parapet", "a parapet and battlements stand round a flat roof; this part's roof is "
                + roof.form + ": say roof: flat, or leave them out");
        }

        if (roof.battlements && roof.parapet <= 0.0)
        {
            roof.parapet = 64.0;
        }

        if (roof.parapet > 0.0)
        {
            roof.eaves = 0.0;
            roof.fascia = 0.0;
        }

        // S8d: `half_hip` on a box's gable: each end hipped from its eaves up to this height over the roof's foot,
        // gabled above it (Erathia's House 10E/W: hipped to 992, a small gable over), the hip reaching `hip` in from
        // each end (left out: as far as the slopes rise to it, so the hip falls as steeply as they do).
        const YAML::Node halfHip = fieldOf(node, m_plot, "half_hip");

        if (halfHip.IsDefined())
        {
            const double first = lengthOf(part.outline[0], part.outline[1]);
            const double second = lengthOf(part.outline[1], part.outline[2]);
            const bool alongFirst = roof.along == 'x' || (roof.along == 0 && first >= second);
            const double half = ((alongFirst ? second : first) + 2.0 * roof.eaves) * 0.5;
            const double ridgeLength = alongFirst ? first : second;
            const bool readable = numberOfNode(halfHip, roof.halfHip);
            const bool ownRun = fieldOf(node, m_plot, "hip").IsDefined();
            roof.halfHipRun = ownRun ? roof.hipRun : (roof.rise > 0.0 ? half * roof.halfHip / roof.rise : 0.0);

            if (!readable || !box || roof.form != "gable" || roof.halfHip < 16.0 || roof.halfHip > roof.rise - 16.0
                || roof.fascia > 0.0 || roof.ridge > 0.0 || !roof.tiers.empty() || part.concave
                || roof.halfHipRun < 16.0 || roof.halfHipRun > ridgeLength * 0.5 - 16.0
                || childOf(node, "eaves_walls").IsDefined())
            {
                add(at + ".half_hip", "half_hip hips a box's gable at each end from its eaves up to this height over "
                    "the roof's foot (16 up to 16 under the ridge, " + formatNumber(roof.rise) + "), gabled above; "
                    "its hip reaches `hip` in from each end (16 up to 16 short of half the ridge); not with a "
                    "`fascia`, a ridge beam (`ridge`), `tiers` or `eaves_walls`");
                roof.halfHip = 0.0;
            }
        }

        // `verge` (2026-11-24, the Xeen Clouds towns' classic kit): a box's gable runs its slopes on past each gable
        // end, so the roof shows its edge over the gable, with a barge board under that edge.
        const YAML::Node verge = fieldOf(node, m_plot, "verge");
        const YAML::Node barge = fieldOf(node, m_plot, "barge");
        const YAML::Node vergeWalls = fieldOf(node, m_plot, "verge_walls");

        if (verge.IsDefined() || barge.IsDefined() || vergeWalls.IsDefined())
        {
            const bool readable = numberOfNode(verge, roof.verge);
            roof.barge = roof.fascia > 0.0 ? roof.fascia : 24.0;
            const bool bargeReadable = !barge.IsDefined() || numberOfNode(barge, roof.barge);
            // `verge_walls`: the gable ends that take it, by their walls (s, e, n, w).
            bool wallsReadable = true;

            if (vergeWalls.IsDefined())
            {
                roof.vergeWalls = {false, false, false, false};
                wallsReadable = vergeWalls.IsSequence() && vergeWalls.size() > 0;

                for (size_t index = 0; wallsReadable && index < vergeWalls.size(); ++index)
                {
                    const size_t wall = vergeWalls[index].IsScalar() && vergeWalls[index].Scalar().size() == 1
                        ? std::string("senw").find(vergeWalls[index].Scalar()[0]) : std::string::npos;
                    wallsReadable = wall != std::string::npos;

                    if (wallsReadable)
                    {
                        roof.vergeWalls[wall] = true;
                    }
                }
            }

            if (!readable || !bargeReadable || !wallsReadable || !box || roof.form != "gable" || roof.halfHip > 0.0
                || part.concave || roof.verge < 1.0 || roof.verge > 256.0 || roof.barge < 0.0 || roof.barge > 128.0
                || childOf(node, "eaves_walls").IsDefined())
            {
                add(at + ".verge", "verge runs a box's gable roof on past each gable end, 1 to 256 map units, with a "
                    "barge board `barge` high under the roof's edge there (0 to 128; left out: the fascia, else 24), "
                    "at the ends `verge_walls` names (s, e, n, w; left out: both); not with `half_hip` or "
                    "`eaves_walls`");
                roof.verge = 0.0;
                roof.barge = 0.0;
                roof.vergeWalls = {true, true, true, true};
            }
        }
    }

    // A text field of the part, else of the plot.
    std::string textField(const YAML::Node &part, const char *pKey, const std::string &fallback = {}) const
    {
        const YAML::Node value = fieldOf(part, m_plot, pKey);
        return value.IsDefined() && value.IsScalar() ? value.Scalar() : fallback;
    }

    // A wall of a part by the name the sketch gives it: s, e, n, w on a box, a number on any part. The outline's
    // side, or -1.
    int wallOf(const OutdoorBuildingPlan &building, size_t part, const std::string &name) const
    {
        const size_t count = building.parts[part].outline.size();
        int wall = -1;

        if (building.parts[part].shape == "box" && name.size() == 1 && std::string("senw").find(name[0])
            != std::string::npos)
        {
            wall = static_cast<int>(std::string("senw").find(name[0]));
        }
        else
        {
            int number = -1;
            const std::from_chars_result result = std::from_chars(name.data(), name.data() + name.size(), number);

            if (result.ec == std::errc() && result.ptr == name.data() + name.size() && number >= 0
                && static_cast<size_t>(number) < count)
            {
                wall = number;
            }
        }

        if (wall >= 0 && !m_wallOrder[part].empty())
        {
            wall = static_cast<int>(std::find(m_wallOrder[part].begin(), m_wallOrder[part].end(),
                static_cast<size_t>(wall)) - m_wallOrder[part].begin());
        }

        return wall;
    }

    static size_t bayCountOf(const OutdoorPartPlan &part, size_t wall)
    {
        const double length = lengthOf(part.outline[wall], part.outline[(wall + 1) % part.outline.size()]);
        return static_cast<size_t>(std::max(1.0, std::round(length / BayWidth)));
    }

    void readDoor(const YAML::Node &node, const YAML::Node &place, const std::string &at,
        OutdoorBuildingPlan &building)
    {
        OutdoorDoorPlan door;
        double house = 0.0;

        if (numberOf(node, "house", house))
        {
            door.house = static_cast<int>(house);
        }

        const YAML::Node into = childOf(node, "into");

        if (into.IsDefined() && into.IsMap())
        {
            door.toMap = textOf(into, "map");
            const YAML::Node arrival = childOf(into, "at");

            for (size_t axis = 0; arrival.IsDefined() && arrival.IsSequence() && axis < 3 && axis < arrival.size();
                 ++axis)
            {
                door.arrival[axis] = arrival[axis].as<int>(0);
            }

            double arrivalFacing = 0.0;
            door.arrivalFacingGiven = numberOf(into, "facing", arrivalFacing);
            door.arrivalFacing = static_cast<int>(arrivalFacing);
            door.arrivalName = textOf(into, "arrival");

            if (!door.arrivalName.empty() && arrival.IsDefined())
            {
                add(at + ".into", "into takes `at` or `arrival`, not both");
                return;
            }
            std::string screenError;

            if (!readMoveScreen(childOf(into, "screen"), door.toMap, door.screen, screenError))
            {
                add(at + ".into.screen", screenError);
                return;
            }
        }

        // A door says the building's title, or nothing: the original's nameless entrances have no name, and an id is
        // no name a player should read.
        door.title = textOf(node, "title", building.title);
        door.path = m_path + at;
        const YAML::Node same = at.empty() ? YAML::Node(YAML::NodeType::Undefined) : childOf(node, "same_event_as");

        if (same.IsDefined())
        {
            const std::string own = "building:" + (building.id.rfind("building:", 0) == 0 ? building.id.substr(9)
                : building.id);
            double number = -1.0;

            if (same.IsScalar() && same.Scalar().rfind("building:", 0) == 0)
            {
                door.sameEventAs = same.Scalar();
            }
            else if (same.IsScalar() && numberOfNode(same, number) && number >= 0.0 && number == std::floor(number))
            {
                door.sameEventAs = own + "/door:" + std::to_string(static_cast<int>(number));
            }
            else if (same.IsMap() && !textOf(same, "building").empty() && numberOf(same, "door", number)
                && number >= 0.0 && number == std::floor(number))
            {
                door.sameEventAs = textOf(same, "building") + "/door:" + std::to_string(static_cast<int>(number));
            }
            else
            {
                add(at + ".same_event_as", "a door's same_event_as names the door whose event it carries: n (the "
                    "n-th entry of this building's `doors`, 0 its own `door`), building:<id> (that building's own "
                    "door), or {building: building:<id>, door: n}");
                return;
            }

            for (const char *pKey : {"house", "into", "effects", "lua", "condition", "locked_text", "else_effects",
                     "once", "title"})
            {
                if (childOf(node, pKey).IsDefined())
                {
                    add(at + ".same_event_as", std::string("a door that carries another door's event says and does "
                        "what that event does: leave out its own `") + pKey + "`");
                    return;
                }
            }
        }

        if (door.house != 0 && !door.toMap.empty())
        {
            add(at, "the plot's door has both `house` and `into`: a door enters a house's dialogue or leads into "
                "a map, not both");
            return;
        }

        // The part: by id or number; the first when left out.
        const std::string partName = textOf(place, "part");
        bool found = partName.empty();

        for (size_t part = 0; part < building.parts.size(); ++part)
        {
            if (!partName.empty() && (building.parts[part].id == partName || std::to_string(part) == partName))
            {
                door.part = part;
                found = true;
            }
        }

        if (!found)
        {
            add(at + ".part", "the door names the part `" + partName + "`, which " + building.id
                + " does not have; name a part's id, or its number from 0");
            return;
        }

        const OutdoorPartPlan &part = building.parts[door.part];

        if (!part.title.empty() && (at.empty() || !childOf(node, "title").IsDefined()))
        {
            // A door of a part with a name of its own says that name (a shop of a joined block).
            door.title = part.title;
        }

        const std::string wallName = textOf(place, "wall", part.shape == "box" ? std::string(1, building.facing)
            : std::string("0"));
        const int wall = wallOf(building, door.part, wallName);

        if (wall < 0)
        {
            add(at + ".wall", "the door's wall `" + wallName + "` is none of the part's: a box has the walls s, e, "
                "n and w, any part the walls 0 to " + std::to_string(part.outline.size() - 1)
                + " in the order of its outline");
            return;
        }

        door.wall = static_cast<size_t>(wall);
        // A wall whose bays the part lists has at least that many (a short outline face listed as [wall, 16],
        // [door, 128], [wall, 16] has three where its length holds one); a bay past a listed wall's last is still
        // taken as its last, as before.
        size_t count = bayCountOf(part, door.wall);
        const YAML::Node listedWall = door.part < m_partNodes.size()
            ? childOf(childOf(m_partNodes[door.part], "walls"), wallName.c_str()) : YAML::Node();

        if (listedWall.IsDefined() && listedWall.IsSequence() && listedWall.size() > 0)
        {
            count = std::max(count, static_cast<size_t>(listedWall.size()));
        }

        const double length = lengthOf(part.outline[door.wall], part.outline[(door.wall + 1) % part.outline.size()]);
        double bay = -1.0;

        if (numberOf(place, "bay", bay) && (bay < 0.0 || bay >= count || bay != std::floor(bay)))
        {
            add(at + ".bay", "the door's wall is " + formatNumber(length) + " long and has " + std::to_string(count)
                + " bays, counted from 0 at its left end seen from outside; bay " + formatNumber(bay)
                + " is none of them");
            return;
        }

        door.bay = bay >= 0.0 ? static_cast<size_t>(bay) : (count - 1) / 2;

        if (part.taper != 1.0)
        {
            add(at, "the door of " + building.id + " is on a part with `taper`: leaning walls are plain, without "
                "bays: put the door on an upright part (`door: {part: ...}`), or say `door: none`");
            return;
        }

        if (length < LeastBay)
        {
            add(at, "the wall with the door of " + building.id + " is " + formatNumber(length)
                + " units long; a door is " + formatNumber(BayWidth) + " wide (a bay of at least "
                + formatNumber(LeastBay) + "): widen the part, put the door on another wall with `door: {wall: "
                "...}`, or say `form: none` for a thing that is no house");
            return;
        }

        if (part.wallHeight < RowHeight * 0.5 && !reachesGround(part))
        {
            add(at, "the part with the door of " + building.id + " has walls " + formatNumber(part.wallHeight)
                + " high; a door is " + formatNumber(RowHeight) + " high and at least half of it must fit: raise "
                "`wall_height`, put the door on another part with `door: {part: ...}`, or say `door: none`");
            return;
        }

        double storey = 1.0;

        if (childOf(place, "storey").IsDefined()
            && (!numberOf(place, "storey", storey) || storey < 1.0 || storey != std::floor(storey)))
        {
            add(at + ".storey", "a door's `storey` is a whole number from 1 (the ground floor) up");
            return;
        }

        door.storey = static_cast<size_t>(storey) - 1;

        // The rows above the lowest begin over the part's band.
        const double sill = door.storey * RowHeight + (door.storey > 0 ? part.band : 0.0);

        if (door.storey > 0 && part.wallHeight < sill + RowHeight * 0.5)
        {
            add(at + ".storey", "the door of " + building.id + " is in storey " + formatNumber(storey) + ", from "
                + formatNumber(sill) + " to " + formatNumber(sill + RowHeight)
                + " above the floor, and the part's walls are " + formatNumber(part.wallHeight) + " high: at least "
                "half of the door must fit. Raise `wall_height` to " + formatNumber(sill + RowHeight * 0.5)
                + " or more, or lower the storey");
            return;
        }

        if (part.posts > 0.0)
        {
            add(at, "the door of " + building.id + " is on an open part (`posts`): it has no walls to hold one; put "
                "the door on another part, or say `door: none`");
            return;
        }

        // Batch O-H: `recess: <depth>`: the door set back into the part in a recess as wide as its bay (Erathia's
        // town hall, 256 into the hall; Castle Ironfist's gate door): a porch recess over the door's bay.
        if (childOf(place, "recess").IsDefined())
        {
            double depth = 0.0;
            std::vector<double> edges = bayEdgesOf(part, door.wall, false);

            if (edges.size() < door.bay + 2)
            {
                edges.clear();

                for (size_t edge = 0; edge <= count; ++edge)
                {
                    edges.push_back(length * static_cast<double>(edge) / static_cast<double>(count));
                }
            }

            const Point2 &left = part.outline[door.wall];
            const Point2 &right = part.outline[(door.wall + 1) % part.outline.size()];
            const Point2 inward = {-(right[1] - left[1]) / length, (right[0] - left[0]) / length};
            bool inside = numberOf(place, "recess", depth) && depth >= 16.0 && depth <= 1024.0;

            for (const double along : {edges[door.bay], edges[door.bay + 1]})
            {
                inside = inside && along >= 16.0 && along <= length - 16.0
                    && insideConvex(grown(part.outline, -16.0), {left[0] + (right[0] - left[0]) * along / length
                    + inward[0] * depth, left[1] + (right[1] - left[1]) * along / length + inward[1] * depth});
            }

            if (!inside || door.storey > 0 || part.climb > 0.0 || part.concave)
            {
                add(at + ".recess", "a door's `recess` is how far it stands back in the part, 16 to 1024, on the "
                    "ground floor of a part with upright walls; the recess's corners stay 16 inside the part and its "
                    "bay 16 from the wall's ends");
                return;
            }

            for (const OutdoorPorchPlan &other : part.porches)
            {
                if (other.wall == door.wall && other.fromBay <= door.bay && other.toBay >= door.bay)
                {
                    add(at + ".recess", "the door's bay lies under a porch of its wall already: give the porch "
                        "`recess: true` instead");
                    return;
                }
            }

            OutdoorPorchPlan recess;
            recess.wall = door.wall;
            recess.fromBay = door.bay;
            recess.toBay = door.bay;
            recess.depth = depth;
            recess.recess = true;
            recess.rise = 0.0;
            recess.height = std::min(part.wallHeight, RowHeight);
            building.parts[door.part].porches.push_back(recess);
        }

        // A slab before the door (the front steps of Ravenshore's lanes and Harmondale's houses).
        const YAML::Node step = childOf(place, "step");

        if (step.IsDefined())
        {
            door.stepDepth = 64.0;
            const bool readable = step.IsMap() && (!childOf(step, "depth").IsDefined()
                || numberOf(step, "depth", door.stepDepth)) && (!childOf(step, "height").IsDefined()
                || numberOf(step, "height", door.stepHeight)) && (!childOf(step, "overhang").IsDefined()
                || numberOf(step, "overhang", door.stepOverhang)) && (!childOf(step, "front").IsDefined()
                || numberOf(step, "front", door.stepFront));

            if (!readable || door.stepDepth < 16.0 || door.stepDepth > 512.0 || door.stepHeight < 0.0
                || (door.stepHeight < 4.0 && !childOf(step, "front").IsDefined()) || door.stepHeight > 128.0 || door.stepOverhang < 0.0 || door.stepOverhang > 256.0
                || (childOf(step, "front").IsDefined() && (door.stepFront < -256.0 || door.stepFront > door.stepHeight)))
            {
                add(at + ".step", "a door's `step` is {depth: 16 to 512 (64 when left out), height: its top at the wall over the "
                    "floor, 4 to 128 (16; 0 for a stoop that meets the sill), "
                    "overhang: how far it reaches past the door at each side, 0 to 256 (32), front: its height at "
                    "its front edge over the floor, -256 up to `height`, for a stoop whose top slopes up to the door "
                    "from a street that may lie lower than the house (flat when left out)}");
                return;
            }

            door.stepFront = childOf(step, "front").IsDefined() ? door.stepFront : door.stepHeight;

            if (door.storey > 0 || part.bottom != 0.0)
            {
                add(at + ".step", "a step lies on the ground before a door of the ground floor of a part that "
                    "stands on the ground");
                return;
            }
        }

        // Door dressing.
        door.arch = textOf(place, "arch");
        double number = 0.0;
        door.archSides = numberOf(place, "sides", number) ? static_cast<int>(number) : 6;
        door.leaves = numberOf(place, "leaves", number) ? static_cast<int>(number) : 1;
        door.leavesGiven = childOf(place, "leaves").IsDefined();
        door.hood = numberOf(place, "hood", number) ? number : 0.0;
        const YAML::Node frame = childOf(place, "frame");

        if (!door.arch.empty() && door.arch != "round" && door.arch != "pointed" && door.arch != "segment")
        {
            add(at + ".arch", "a door's `arch` is round, pointed or segment (its head; square when left out)");
            return;
        }

        if (door.archSides < 2 || door.archSides > 16 || (door.leaves != 1 && door.leaves != 2) || door.hood < 0.0
            || door.hood > 512.0)
        {
            add(at, "a door's arch has 2 to 16 `sides` (6), `leaves` is 1 or 2, a `hood` reaches 0 to 512 out");
            return;
        }

        // S8d: `sill`: the door stands over its row's foot, the wall's own panel under it.
        if (childOf(place, "sill").IsDefined())
        {
            const double rowHigh = std::min(RowHeight, part.wallHeight - door.storey * RowHeight
                - (door.storey > 0 ? part.band : 0.0));

            if (!numberOf(place, "sill", door.sill) || door.sill < 0.0 || door.sill > rowHigh - 96.0
                || door.hood > 0.0 || frame.IsDefined() || part.batter != 0.0 || part.ruin.given
                || (part.doorHeight > 0.0 && part.wallHeight < part.doorHeight - 0.5))
            {
                add(at + ".sill", "a door's `sill` is how high it stands over its row's foot, 0 up to 96 under the "
                    "row's top (here " + formatNumber(std::max(0.0, rowHigh - 96.0)) + "), the wall under it; not "
                    "with a `hood` or `frame`, on a battered or ruined wall or a door cut into the roof");
                door.sill = 0.0;
                return;
            }
        }

        if (frame.IsDefined())
        {
            door.frameSteps = 1;
            const bool readable = frame.IsMap() && (!childOf(frame, "steps").IsDefined()
                || numberOf(frame, "steps", number));
            door.frameSteps = childOf(frame, "steps").IsDefined() ? static_cast<int>(number) : 1;
            door.frameStep = numberOr(frame, "step", 32.0);
            door.frameTexture = textOf(frame, "texture");
            door.portcullis = textOf(frame, "portcullis") == "true";

            if (!readable || door.frameSteps < 1 || door.frameSteps > 4 || door.frameStep < 8.0
                || door.frameStep > 128.0)
            {
                add(at + ".frame", "a door's `frame` is {steps: 1 to 4 (1), step: each ring's width, 8 to 128 (32), "
                    "texture: <name> (the part's trim), portcullis: true for bars before the door}");
                return;
            }
        }

        m_doorBayGiven.push_back(bay >= 0.0);
        building.doors.push_back(door);
    }

    void readDoors(OutdoorBuildingPlan &building)
    {
        // The plot's own door, also when it opens nothing: a house has a door. `door: none` is a building without
        // one (a tower on a wall, a gate's frame, a monument).
        const YAML::Node ownDoor = childOf(m_plot, "door");

        if (!(ownDoor.IsDefined() && ownDoor.IsScalar() && ownDoor.Scalar() == "none"))
        {
            readDoor(m_plot, ownDoor, "", building);
        }
        else if (childOf(m_plot, "house").IsDefined() || childOf(m_plot, "into").IsDefined())
        {
            add(".door", "`door: none` and `house` or `into` do not go together: a building without a door opens "
                "nothing");
        }

        const YAML::Node doors = childOf(m_plot, "doors");

        for (size_t index = 0; doors.IsDefined() && doors.IsSequence() && index < doors.size(); ++index)
        {
            readDoor(doors[index], doors[index], ".doors[" + std::to_string(index) + "]", building);
        }
    }

    // How many letters must change to turn one word into the other (a misspelt role: `windw` for `window`).
    static size_t editDistance(const std::string &from, const std::string &to)
    {
        std::vector<size_t> row(to.size() + 1);

        for (size_t column = 0; column <= to.size(); ++column)
        {
            row[column] = column;
        }

        for (size_t line = 1; line <= from.size(); ++line)
        {
            size_t diagonal = row[0];
            row[0] = line;

            for (size_t column = 1; column <= to.size(); ++column)
            {
                const size_t above = row[column];
                row[column] = std::min({row[column] + 1, row[column - 1] + 1,
                    diagonal + (from[line - 1] == to[column - 1] ? 0 : 1)});
                diagonal = above;
            }
        }

        return row[to.size()];
    }

    // A bay's word that is no role is a texture's own name (many hold no digit: Harmondale's `chbw` window); here
    // only the form is checked, one word of letters, digits, _ and - (the build checks the name against the
    // world's textures and names the bay's building when the world has no such texture).
    static bool isTextureName(const std::string &word)
    {
        return !word.empty() && word.size() <= 32 && std::all_of(word.begin(), word.end(), [](unsigned char character)
        {
            return std::isalnum(character) != 0 || character == '_' || character == '-';
        });
    }

    // One row of bays of one wall as the sketch lists it, checked.
    bool listedBays(const YAML::Node &list, const std::string &at, const OutdoorPartPlan &part, size_t wall,
        std::vector<std::string> &bays, std::vector<double> &widths)
    {
        const double length = lengthOf(part.outline[wall], part.outline[(wall + 1) % part.outline.size()]);
        double given = 0.0;
        size_t shared = 0;

        for (size_t index = 0; index < list.size(); ++index)
        {
            // A word, or [word, width]: a bay of its own width.
            const YAML::Node entry = list[index];
            const bool sized = entry.IsSequence() && entry.size() == 2 && entry[0].IsScalar();
            const std::string role = entry.IsScalar() ? entry.Scalar() : (sized ? entry[0].Scalar() : std::string());
            double width = 0.0;

            if (role.empty() || (sized && (!numberOfNode(entry[1], width) || width < 16.0 || width > 512.0)))
            {
                add(at, "a bay is a word: a role of the part's `textures` (wall, window, door, post_left, "
                    "post_right) or a texture's own name; or [word, width] for a bay of its own width, 16 to 512 "
                    "(the 64-wide panels beside a door)");
                return false;
            }

            widths.push_back(width);
            given += width;
            shared += sized ? 0 : 1;

            // A word without a digit a letter from a role of the part (two from a long one: post_left) is taken for a
            // misspelt role.
            std::string nearRole;

            for (const std::pair<const std::string, std::string> &entry : part.textures)
            {
                const bool digit = std::any_of(role.begin(), role.end(), [](unsigned char character)
                {
                    return std::isdigit(character) != 0;
                });

                if (!digit && nearRole.empty() && role.size() >= 4
                    && editDistance(role, entry.first) <= (entry.first.size() >= 7 ? 2u : 1u))
                {
                    nearRole = entry.first;
                }
            }

            if (!part.textures.contains(role) && isTextureName(role) && !nearRole.empty())
            {
                add(at, "a bay names `" + role + "`, which is no role of the part; it is so near the role `"
                    + nearRole + "` that it is taken for it misspelt: write `" + nearRole + "`, or give the texture "
                    "a role of its own in `textures` (" + role + "_bay: " + role + ") and name that");
                return false;
            }

            if (!part.textures.contains(role) && !isTextureName(role))
            {
                std::vector<std::string> roles;

                for (const std::pair<const std::string, std::string> &entry : part.textures)
                {
                    roles.push_back(entry.first);
                }

                add(at, "a bay names `" + role + "`, which is no role of the part and cannot be a texture's name "
                    "(one word of letters, digits, _ and -, up to 32); the part's roles are "
                    + joined(roles) + ": use one of them, add `" + role + ": <texture>` to `textures`, or write "
                    "the texture's own name");
                return false;
            }

            bays.push_back(role);
        }

        if (length < LeastBay)
        {
            // No number of bays fits a wall shorter than the narrowest bay.
            add(at, "the wall is " + formatNumber(length) + " long, shorter than the narrowest bay ("
                + formatNumber(LeastBay) + "): it takes no list of bays. Leave it out of `walls` (it is laid as "
                "one plain piece of the `wall` texture), or make the part at least " + formatNumber(LeastBay)
                + " wide there");
            return false;
        }

        if (given > 0.0)
        {
            // Bays of their own width: the others share what is left, each 96 to 192; with none left to share the
            // widths make up the wall.
            const double share = shared > 0 ? (length - given) / shared : 0.0;

            if ((shared > 0 && (share < LeastBay || share > WidestBay))
                || (shared == 0 && std::fabs(given - length) > 0.5))
            {
                add(at, "the wall is " + formatNumber(length) + " long and its bays with a width of their own take "
                    + formatNumber(given) + (shared > 0 ? ", which leaves " + formatNumber(length - given) + " to "
                        + std::to_string(shared) + " bays (each must be " + formatNumber(LeastBay) + " to "
                        + formatNumber(WidestBay) + ")" : std::string(" and no bay is left to take the rest"))
                    + ": change the widths, the number of bays or the part's size");
                return false;
            }

            return true;
        }

        if (bays.empty() || length / bays.size() < LeastBay || length / bays.size() > WidestBay)
        {
            const size_t fewest = static_cast<size_t>(std::max(1.0, std::ceil(length / WidestBay)));
            const size_t most = static_cast<size_t>(std::max(1.0, std::floor(length / LeastBay)));
            add(at, "the wall is " + formatNumber(length) + " long and lists " + std::to_string(bays.size())
                + " bays; a bay is " + formatNumber(LeastBay) + " to " + formatNumber(WidestBay) + " wide ("
                + formatNumber(BayWidth) + " as the panels are drawn): list " + std::to_string(fewest)
                + (most > fewest ? " to " + std::to_string(most) : std::string()) + " bays, or change the part's "
                "size");
            return false;
        }

        return true;
    }

    void readBays(OutdoorBuildingPlan &building, size_t partIndex)
    {
        OutdoorPartPlan &part = building.parts[partIndex];
        const YAML::Node &node = m_partNodes[partIndex];
        const size_t count = part.outline.size();
        part.bays.assign(count, {});
        part.upperBays.assign(count, {});
        part.bayWidths.assign(count, {});
        part.upperBayWidths.assign(count, {});
        const bool posts = part.textures.contains("post_left") && part.textures.contains("post_right")
            && part.shape != "round";
        const std::string windows = textField(node, "windows",
            part.textures.contains("window") && part.shape != "round" ? "alternate" : "none");
        const std::string at = m_partNodes.size() == 1 && !node.IsDefined() ? std::string()
            : ".parts[" + std::to_string(partIndex) + "]";

        if (windows != "alternate" && windows != "all" && windows != "none")
        {
            add(at + ".windows", "windows is alternate (every second bay), all or none");
            return;
        }

        part.windowArch = textField(node, "window_arch");

        if (!part.windowArch.empty() && part.windowArch != "round" && part.windowArch != "pointed"
            && part.windowArch != "segment")
        {
            add(at + ".window_arch", "window_arch is round, pointed or segment: the window bays' heads arched");
            return;
        }

        const YAML::Node walls = fieldOf(node, m_plot, "walls");
        const YAML::Node upperWalls = fieldOf(node, m_plot, "upper_walls");
        std::vector<bool> listed(count, false);
        std::vector<bool> upperListed(count, false);

        for (const bool upper : {false, true})
        {
            const YAML::Node &source = upper ? upperWalls : walls;

            if (!source.IsDefined() || !source.IsMap())
            {
                continue;
            }

            for (YAML::const_iterator entry = source.begin(); entry != source.end(); ++entry)
            {
                noteRead(entry->second);
                const std::string name = entry->first.Scalar();
                const std::string where = at + (upper ? ".upper_walls." : ".walls.") + name;
                const int wall = wallOf(building, partIndex, name);

                if (wall < 0 || !entry->second.IsSequence())
                {
                    add(where, "walls are named s, e, n and w on a box and 0 to " + std::to_string(count - 1)
                        + " in the order of the outline on any part, each with a list of bays; `" + name
                        + "` is no wall of this part");
                    continue;
                }

                std::vector<std::string> bays;
                std::vector<double> widths;

                if (listedBays(entry->second, where, part, static_cast<size_t>(wall), bays, widths))
                {
                    (upper ? part.upperBays : part.bays)[wall] = bays;
                    (upper ? part.upperBayWidths : part.bayWidths)[wall] = widths;
                    (upper ? upperListed : listed)[wall] = true;
                }
            }
        }

        for (size_t wall = 0; wall < count; ++wall)
        {
            if (!listed[wall])
            {
                part.bays[wall] = defaultBays(bayCountOf(part, wall), posts, windows, -1);
            }
        }

        // The doors of this part: a listed wall keeps its bays and the door takes the bay written `door` (the
        // first, unless the door names its bay); a wall that is not listed is laid out round the door. `pairLaid`:
        // one more than the bay of a double door the wall was laid out round (F2), 0 for none.
        std::vector<size_t> pairLaid(count, 0);

        for (size_t index = 0; index < building.doors.size(); ++index)
        {
            OutdoorDoorPlan &door = building.doors[index];

            if (door.part != partIndex || door.storey > 0)
            {
                continue;
            }

            std::vector<std::string> &bays = part.bays[door.wall];

            if (listed[door.wall])
            {
                const std::vector<std::string>::iterator written = std::find(bays.begin(), bays.end(), "door");

                if (!m_doorBayGiven[index] && written != bays.end())
                {
                    door.bay = static_cast<size_t>(written - bays.begin());
                }

                door.bay = std::min(door.bay, bays.size() - 1);
                door.texture = doorTextureOf(part, bays[door.bay]);
                bays[door.bay] = "door";
                const std::vector<double> edges = bayEdgesOf(part, door.wall, false);
                pairWingDoor(part, door, edges[door.bay + 1] - edges[door.bay]);
            }
            else
            {
                door.bay = std::min(door.bay, bays.size() - 1);
                pairWingDoor(part, door, 2.0 * BayWidth);

                if (door.leaves > 1 && layPairBay(part, door, posts, windows))
                {
                    pairLaid[door.wall] = door.bay + 1;
                }
                else
                {
                    bays = defaultBays(bays.size(), posts, windows, static_cast<int>(door.bay));
                }
            }

            door.pictureWidth = door.leaves > 1 ? doorPictureWidth(part, door) : 0.0;
        }

        // The rows above: as listed, else the lowest row with a window where its door is.
        for (size_t wall = 0; wall < count; ++wall)
        {
            if (!upperListed[wall])
            {
                part.upperBays[wall] = part.bays[wall];
                part.upperBayWidths[wall] = part.bayWidths[wall];

                for (std::string &role : part.upperBays[wall])
                {
                    role = role == "door" ? (part.textures.contains("window") ? "window" : "wall") : role;
                    // A picture laid once per bay stands in the lowest row only (A6: no window or frieze repeated
                    // up a wall taller than one row); `upper_walls` puts it higher.
                    role = part.fitted.contains(role) ? "wall" : role;
                }

                // Over a double door's bay of 256 one window in the middle, the wall beside it (F2).
                if (pairLaid[wall] > 0 && part.upperBays[wall][pairLaid[wall] - 1] == "window")
                {
                    const size_t bay = pairLaid[wall] - 1;
                    std::vector<std::string> &roles = part.upperBays[wall];
                    std::vector<double> &widths = part.upperBayWidths[wall];
                    const double side = (widths[bay] - BayWidth) * 0.5;
                    roles[bay] = "wall";
                    widths[bay] = side;
                    roles.insert(roles.begin() + static_cast<std::ptrdiff_t>(bay) + 1, {"window", "wall"});
                    widths.insert(widths.begin() + static_cast<std::ptrdiff_t>(bay) + 1, {BayWidth, side});
                }
            }
        }

        // Doors up a storey take their bay in the rows above (the bay written `door` there, else the one they
        // name); the rows they are not in show a window or the wall there (PartRaiser::raiseWall).
        for (size_t index = 0; index < building.doors.size(); ++index)
        {
            OutdoorDoorPlan &door = building.doors[index];

            if (door.part != partIndex || door.storey == 0)
            {
                continue;
            }

            std::vector<std::string> &bays = part.upperBays[door.wall];
            const std::vector<std::string>::iterator written = std::find(bays.begin(), bays.end(), "door");

            if (upperListed[door.wall] && !m_doorBayGiven[index] && written != bays.end())
            {
                door.bay = static_cast<size_t>(written - bays.begin());
            }

            door.bay = std::min(door.bay, bays.size() - 1);
            door.texture = upperListed[door.wall] ? doorTextureOf(part, bays[door.bay]) : std::string();
            bays[door.bay] = "door";
            door.pictureWidth = door.leaves > 1 ? doorPictureWidth(part, door) : 0.0;
        }
    }

    // A list of wall names (`sill_walls`, a railing's `walls`) as a mark per wall; every wall when left out.
    bool wallsNamed(const OutdoorBuildingPlan &building, size_t partIndex, const YAML::Node &list,
        const std::string &where, std::vector<bool> &marks)
    {
        const size_t count = building.parts[partIndex].outline.size();
        marks.assign(count, !list.IsDefined());

        for (size_t index = 0; list.IsDefined() && index < (list.IsSequence() ? list.size() : 1); ++index)
        {
            const int wall = list.IsSequence() && list[index].IsScalar()
                ? wallOf(building, partIndex, list[index].Scalar()) : -1;

            if (wall < 0)
            {
                add(where, "a list of the part's walls: s, e, n and w on a box, 0 to " + std::to_string(count - 1)
                    + " in the order of the outline on any part");
                return false;
            }

            marks[static_cast<size_t>(wall)] = true;
        }

        return true;
    }

    // Batch S4R: a list of walls whose entries may each be a stretch of a wall: `n` (all of it) or {wall: n, from:
    // 128, to: 512} (map units along the wall from its left end seen from outside; `from` left out 0, `to` its end).
    // `stretches` per wall, joined where they meet; `partial` when one stops short of its wall's ends.
    bool stretchesNamed(const OutdoorBuildingPlan &building, size_t partIndex, const YAML::Node &list,
        const std::string &where, std::vector<bool> &marks, std::vector<std::vector<std::array<double, 2>>> &stretches,
        bool &partial, std::vector<double> *pAmounts = nullptr)
    {
        const OutdoorPartPlan &part = building.parts[partIndex];
        const size_t count = part.outline.size();
        marks.assign(count, false);
        stretches.assign(count, {});
        partial = false;

        if (pAmounts != nullptr)
        {
            pAmounts->assign(count, -1.0);
        }

        const std::string what = "a list of the part's walls: s, e, n and w on a box, 0 to " + std::to_string(count - 1)
            + " in the order of the outline on any part; an entry may be a stretch {wall, from, to} (map units along "
            "the wall from its left end seen from outside, at least 16 long; from 0 and to its end when left out)";

        if (!list.IsSequence())
        {
            add(where, what);
            return false;
        }

        for (size_t index = 0; index < list.size(); ++index)
        {
            const YAML::Node entry = list[index];
            const int wall = entry.IsScalar() ? wallOf(building, partIndex, entry.Scalar())
                : entry.IsMap() ? wallOf(building, partIndex, textOf(entry, "wall")) : -1;

            if (wall < 0)
            {
                add(where, what);
                return false;
            }

            const double length = lengthOf(part.outline[static_cast<size_t>(wall)],
                part.outline[(static_cast<size_t>(wall) + 1) % count]);
            std::array<double, 2> stretch = {0.0, length};

            if (entry.IsMap() && ((childOf(entry, "from").IsDefined() && !numberOf(entry, "from", stretch[0]))
                || (childOf(entry, "to").IsDefined() && !numberOf(entry, "to", stretch[1]))
                || stretch[0] < 0.0 || stretch[1] > length + 0.5 || stretch[1] - stretch[0] < 16.0))
            {
                add(where, "the stretch of wall " + std::to_string(wall) + " runs from " + formatNumber(stretch[0])
                    + " to " + formatNumber(stretch[1]) + ": it must lie on the wall (0 to " + formatNumber(length)
                    + ") and be at least 16 long");
                return false;
            }

            stretch[1] = std::min(stretch[1], length);

            if (entry.IsMap() && childOf(entry, "eaves").IsDefined())
            {
                double amount = -1.0;

                if (pAmounts == nullptr || !numberOf(entry, "eaves", amount) || amount < 0.0 || amount > 512.0)
                {
                    add(where, pAmounts == nullptr ? "`eaves` in an entry is for `eaves_walls`"
                        : "an entry's `eaves` is how far the roof reaches out over that wall: 0 to 512");
                    return false;
                }

                (*pAmounts)[static_cast<size_t>(wall)] = amount;
            }

            marks[static_cast<size_t>(wall)] = true;
            stretches[static_cast<size_t>(wall)].push_back(stretch);
        }

        for (size_t wall = 0; wall < count; ++wall)
        {
            std::vector<std::array<double, 2>> &own = stretches[wall];
            std::sort(own.begin(), own.end());
            std::vector<std::array<double, 2>> joinedStretches;

            for (const std::array<double, 2> &stretch : own)
            {
                if (!joinedStretches.empty() && stretch[0] <= joinedStretches.back()[1] + 0.5)
                {
                    joinedStretches.back()[1] = std::max(joinedStretches.back()[1], stretch[1]);
                }
                else
                {
                    joinedStretches.push_back(stretch);
                }
            }

            own = joinedStretches;
            const double length = lengthOf(part.outline[wall], part.outline[(wall + 1) % count]);
            partial = partial || (!own.empty() && (own.size() > 1 || own[0][0] > 0.5 || own[0][1] < length - 0.5));
        }

        return true;
    }

    // What stands on a part's walls by their bays, read once the bays are known: an open part's low walls, porches
    // and recesses, signs, a railing.
    void readWallThings(OutdoorBuildingPlan &building, size_t partIndex)
    {
        OutdoorPartPlan &part = building.parts[partIndex];
        const YAML::Node &node = m_partNodes[partIndex];
        const std::string at = node.IsDefined() ? ".parts[" + std::to_string(partIndex) + "]" : std::string();
        const size_t count = part.outline.size();

        if (part.posts > 0.0 && part.sill > 0.0
            && !wallsNamed(building, partIndex, childOf(node, "sill_walls"), at + ".sill_walls", part.sillWalls))
        {
            return;
        }

        if (part.posts > 0.0
            && !wallsNamed(building, partIndex, childOf(node, "post_walls"), at + ".post_walls", part.postWalls))
        {
            return;
        }

        if (!readMassWalls(building, partIndex, node, at))
        {
            return;
        }

        // A low wall runs between posts: on a wall that has them (every such wall when `sill_walls` is left out).
        for (size_t wall = 0; wall < part.sillWalls.size() && wall < part.postWalls.size(); ++wall)
        {
            if (!childOf(node, "sill_walls").IsDefined())
            {
                part.sillWalls[wall] = part.sillWalls[wall] && part.postWalls[wall];
            }

            if (part.sill > 0.0 && part.sillWalls[wall] && !part.postWalls[wall])
            {
                add(at + ".sill_walls", "a low wall (`sill`) stands between posts: wall " + std::to_string(wall)
                    + " has none (`post_walls`)");
                return;
            }
        }

        const YAML::Node porches = childOf(node, "porches");

        for (size_t index = 0; porches.IsDefined() && index < (porches.IsSequence() ? porches.size() : 1); ++index)
        {
            const std::string where = at + ".porches[" + std::to_string(index) + "]";
            const YAML::Node entry = porches.IsSequence() ? porches[index] : porches;
            OutdoorPorchPlan porch;
            const int wall = porches.IsSequence() ? wallOf(building, partIndex, textOf(entry, "wall")) : -1;

            if (wall < 0)
            {
                add(where + ".wall", "a porch names its `wall`: s, e, n or w on a box, 0 to "
                    + std::to_string(count - 1) + " in the order of the outline on any part");
                return;
            }

            porch.wall = static_cast<size_t>(wall);
            const size_t bays = std::max<size_t>(1, part.bays[porch.wall].size());
            porch.fromBay = 0;
            porch.toBay = bays - 1;
            const YAML::Node span = childOf(entry, "bays");
            Point2 range = {0.0, static_cast<double>(bays - 1)};
            porch.recess = textOf(entry, "recess") == "true";
            porch.rise = porch.recess ? 0.0 : -1.0;
            porch.height = -1.0;
            const bool readable = (!span.IsDefined() || pointOf(span, range))
                && (!childOf(entry, "depth").IsDefined() || numberOf(entry, "depth", porch.depth))
                && (!childOf(entry, "height").IsDefined() || numberOf(entry, "height", porch.height))
                && (!childOf(entry, "rise").IsDefined() || numberOf(entry, "rise", porch.rise))
                && (!childOf(entry, "thickness").IsDefined() || numberOf(entry, "thickness", porch.thickness))
                && (!childOf(entry, "overhang").IsDefined() || numberOf(entry, "overhang", porch.overhang))
                && (!childOf(entry, "posts").IsDefined() || numberOf(entry, "posts", porch.posts))
                && (!childOf(entry, "floor").IsDefined() || numberOf(entry, "floor", porch.floor));

            if (!readable || range[0] < 0.0 || range[1] >= bays || range[0] > range[1]
                || range[0] != std::floor(range[0]) || range[1] != std::floor(range[1]))
            {
                add(where, "a porch spans `bays: [first, last]` of its wall's lowest row (0 to "
                    + std::to_string(bays - 1) + ", from the wall's left end seen from outside; the whole wall when "
                    "left out), with numbers for depth, height, rise, thickness, overhang, posts and floor");
                return;
            }

            porch.fromBay = static_cast<size_t>(range[0]);
            porch.toBay = static_cast<size_t>(range[1]);
            // Batch O-H: an arched recess (Castle Ironfist's gate passage under its round soffit).
            porch.arch = textOf(entry, "arch");
            porch.archSides = static_cast<int>(numberOr(entry, "sides", 6.0));

            if (!porch.arch.empty() && (!porch.recess || (porch.arch != "round" && porch.arch != "pointed"
                && porch.arch != "segment") || porch.archSides < 2 || porch.archSides > 16))
            {
                add(where + ".arch", "a recess's `arch` is round, pointed or segment with 2 to 16 `sides` (6), its "
                    "top at the recess's `height` over the floor (the walls' top when left out); a porch that stands "
                    "out has no arch");
                return;
            }

            porch.archHeight = porch.recess && !porch.arch.empty() && childOf(entry, "height").IsDefined()
                ? porch.height : 0.0;
            const std::string floorFrom = textOf(entry, "floor_from", "foot");

            if (floorFrom != "foot" && floorFrom != "land")
            {
                add(where + ".floor_from", "floor_from is `foot` (the porch's `floor` over the part's foot, as when "
                    "left out) or `land` (over the land round the building, under its `plinth`: a slab level with "
                    "the floor of a house on a plinth 32 is `floor: 32, floor_from: land`)");
                return;
            }

            porch.floorFromLand = floorFrom == "land";

            if (porch.floorFromLand && part.bottom != 0.0)
            {
                add(where + ".floor_from", "a porch's floor from the land is for a part that stands on the ground "
                    "(`bottom` 0)");
                return;
            }

            // Batch O-F: a portico (Kriegspire's Temple of Baa, outb1 PT07: round columns on bases under capitals,
            // a flat ceiling, an entablature band, a gable pediment over the front).
            const std::string form = textOf(entry, "form", "porch");
            const std::string postsShape = textOf(entry, "posts_shape", "square");
            porch.portico = form == "portico";
            porch.roundPosts = postsShape == "round" || porch.portico;
            const std::string pediment = textOf(entry, "pediment", "none");

            if ((form != "porch" && form != "portico") || (postsShape != "square" && postsShape != "round")
                || (pediment != "none" && pediment != "gable") || (porch.recess && porch.portico)
                || (!porch.portico && (childOf(entry, "columns").IsDefined() || childOf(entry, "rows").IsDefined()
                || pediment != "none")))
            {
                add(where, "a porch's `form` is porch or portico (not on a recess), its `posts_shape` square or "
                    "round; `columns` and `pediment: gable` belong to a portico");
                return;
            }

            if (porch.portico)
            {
                porch.rise = 0.0;
                porch.posts = childOf(entry, "posts").IsDefined() ? porch.posts : 48.0;
                porch.thickness = childOf(entry, "thickness").IsDefined() ? porch.thickness : 32.0;
                double columns = 0.0;
                const bool counted = !childOf(entry, "columns").IsDefined() || numberOf(entry, "columns", columns);
                porch.columns = columns > 0.0 ? static_cast<size_t>(columns) : 2;
                porch.pediment = pediment == "gable" ? numberOr(entry, "pediment_height", porch.depth * 0.5) : 0.0;
                const double rows = numberOr(entry, "rows", 1.0);
                porch.rows = rows == 2.0 ? 2 : 1;

                if (rows != 1.0 && rows != 2.0)
                {
                    add(where + ".rows", "a portico has 1 or 2 `rows` of columns (the second against the wall)");
                    return;
                }

                if (!counted || (columns != 0.0 && (columns < 2.0 || columns > 16.0 || columns != std::floor(columns)))
                    || porch.posts <= 0.0 || porch.pediment < 0.0 || porch.pediment > 1024.0)
                {
                    add(where, "a portico stands on 2 to 16 `columns` (2) `posts` wide (48), its `pediment_height` 0 "
                        "to 1024 (half its depth)");
                    return;
                }
            }

            if (porch.rise < 0.0)
            {
                porch.rise = std::round(porch.depth * 0.25);
            }

            if (porch.height < 0.0)
            {
                porch.height = std::min(part.wallHeight, RowHeight) - porch.rise;
            }

            if (porch.depth < 16.0 || porch.depth > 1024.0 || porch.thickness < 0.0 || porch.thickness > 128.0
                || porch.overhang < 0.0 || porch.overhang > 256.0 || (porch.posts != 0.0 && (porch.posts < 8.0
                || porch.posts > 128.0)) || porch.floor < 0.0 || porch.floor > 256.0 || porch.rise < 0.0
                || porch.rise > 1024.0)
            {
                add(where, "a porch is 16 to 1024 deep, its roof's front edge 0 to 128 thick (`thickness`, 16 when "
                    "left out), reaching 0 to 256 past its bays at each end (`overhang`), rising 0 to 1024 to the "
                    "wall (`rise`), on posts 8 to 128 wide or none (`posts: 0`, the default: a canopy), over a "
                    "floor 0 to 256 high");
                return;
            }

            if (part.posts > 0.0 || part.taper != 1.0)
            {
                add(where, "a porch stands against a wall: the part needs upright walls (no `posts`, no `taper`)");
                return;
            }

            if (porch.recess)
            {
                // Set back into the part: the stretch's corners `depth` in must lie inside the part, clear of the
                // walls across.
                const std::vector<double> edges = bayEdgesOf(part, porch.wall, false);
                const Point2 &left = part.outline[porch.wall];
                const Point2 &right = part.outline[(porch.wall + 1) % count];
                const double length = lengthOf(left, right);
                const Point2 inward = {-(right[1] - left[1]) / length, (right[0] - left[0]) / length};
                const bool openCorner = textOf(entry, "open_corner") == "true";

                if (childOf(entry, "open_corner").IsDefined() && (!openCorner || !porch.arch.empty()
                    || (edges[porch.fromBay] > 0.5 && edges[porch.toBay + 1] < length - 0.5)))
                {
                    add(where + ".open_corner", "`open_corner: true` opens a recess (no `arch`) at the end of its wall "
                        "it runs to: its bays reach the wall's left or right end");
                    return;
                }

                for (const double along : {edges[porch.fromBay], edges[porch.toBay + 1]})
                {
                    const Point2 corner = {left[0] + (right[0] - left[0]) * along / length + inward[0] * porch.depth,
                        left[1] + (right[1] - left[1]) * along / length + inward[1] * porch.depth};
                    const bool atLeft = along < 0.5;

                    if (openCorner && (atLeft || along > length - 0.5))
                    {
                        // S8d: open at this corner. The wall across (the outline's wall before this one at the
                        // left end, after it at the right) meets this one square and is longer than the depth by
                        // 16 or more: it stands back from the corner by the depth, the recess's back meeting it.
                        const size_t across = atLeft ? (porch.wall + count - 1) % count : (porch.wall + 1) % count;
                        const Point2 &acrossFrom = part.outline[across];
                        const Point2 &acrossTo = part.outline[(across + 1) % count];
                        const double acrossLength = lengthOf(acrossFrom, acrossTo);
                        const double square = std::fabs((acrossTo[0] - acrossFrom[0]) * (right[0] - left[0])
                            + (acrossTo[1] - acrossFrom[1]) * (right[1] - left[1])) / std::max(acrossLength * length,
                            1.0e-9);

                        if (part.concave || square > 0.01 || porch.depth > acrossLength - 16.0)
                        {
                            add(where + ".open_corner", "a recess open at a corner needs the wall across to meet its "
                                "wall square (a box's corner, or an outline's right angle; not a part that bends "
                                "in) and to be at least 16 longer than the recess is deep (" + formatNumber(porch.depth)
                                + " against " + formatNumber(acrossLength) + ")");
                            return;
                        }

                        (atLeft ? porch.openLeft : porch.openRight) = true;
                        continue;
                    }

                    if (!insideConvex(grown(part.outline, -16.0), corner))
                    {
                        // A stretch that runs to the wall's end has its corner on the wall across at any depth:
                        // say so, not that the recess is too deep (when its middle at that depth is inside).
                        const double half = (edges[porch.fromBay] + edges[porch.toBay + 1]) * 0.5;
                        const Point2 deepest = {left[0] + (right[0] - left[0]) * half / length + inward[0]
                            * porch.depth, left[1] + (right[1] - left[1]) * half / length + inward[1] * porch.depth};

                        if ((along < 16.0 || along > length - 16.0) && insideConvex(grown(part.outline, -16.0),
                            deepest))
                        {
                            add(where + ".bays", "the recess's bays [" + std::to_string(porch.fromBay) + ", "
                                + std::to_string(porch.toBay) + "] run to within 16 of the wall's "
                                + (along < 16.0 ? "left" : "right") + " end, where the wall across stands: a recess "
                                "open at a corner says `open_corner: true` (its bays to the wall's very end); else "
                                "end it a bay short of the corner (that bay a wall or a post_left/post_right bay)");
                            return;
                        }

                        add(where + ".depth", "the recess reaches " + formatNumber(porch.depth) + " into the part, "
                            "through it or to within 16 of another wall: make it shallower");
                        return;
                    }
                }

                if (part.climb > 0.0 || porch.overhang > 0.0 || porch.floor > 0.0)
                {
                    add(where, "a recess is the wall's stretch set back under the part's own roof: it takes no "
                        "`overhang` or `floor`, and a climbed part takes none");
                    return;
                }
            }
            else if (porch.height <= 0.0 || porch.height + porch.rise > part.wallHeight + 0.5)
            {
                add(where + ".height", "the porch's roof runs from " + formatNumber(porch.height) + " at its front "
                    "edge up to " + formatNumber(porch.height + porch.rise) + " at the wall (over the part's foot), "
                    "and must meet the wall, which is " + formatNumber(part.wallHeight) + " high: lower `height` "
                    "or `rise`");
                return;
            }

            for (const OutdoorPorchPlan &other : part.porches)
            {
                if (other.wall == porch.wall && other.fromBay <= porch.toBay && porch.fromBay <= other.toBay)
                {
                    add(where + ".bays", "the porch spans bays another porch of that wall spans: make them one");
                    return;
                }
            }

            part.porches.push_back(porch);
        }

        // S8d: a stretch a recess open at a corner leaves open holds no porch of its own wall.
        for (const OutdoorPorchPlan &porch : part.porches)
        {
            const std::vector<double> edges = bayEdgesOf(part, porch.wall, false);

            for (const std::array<double, 2> &open : openStretchesOf(part, porch.wall))
            {
                if (edges[porch.fromBay] < open[1] - 0.5 && edges[porch.toBay + 1] > open[0] + 0.5)
                {
                    add(at + ".porches", "a porch of wall " + std::to_string(porch.wall) + " lies in the stretch a "
                        "recess open at its corner (`open_corner`) leaves open: keep it out of the corner");
                    return;
                }
            }
        }

        const YAML::Node signs = childOf(node, "signs");

        for (size_t index = 0; signs.IsDefined() && index < (signs.IsSequence() ? signs.size() : 1); ++index)
        {
            const std::string where = at + ".signs[" + std::to_string(index) + "]";
            const YAML::Node entry = signs.IsSequence() ? signs[index] : signs;
            OutdoorWallSignPlan sign;
            const int wall = signs.IsSequence() ? wallOf(building, partIndex, textOf(entry, "wall")) : -1;
            double bay = -1.0;
            double offset = 0.0;
            Point2 size = {sign.width, sign.height};
            sign.texture = textOf(entry, "texture");
            sign.hang = textOf(entry, "hang") == "true";
            sign.out = sign.hang ? 16.0 : sign.out;
            sign.bottom = std::min(RowHeight + 16.0, part.wallHeight - sign.height);
            const bool readable = wall >= 0 && !sign.texture.empty() && numberOf(entry, "bay", bay)
                && (!childOf(entry, "size").IsDefined() || pointOf(childOf(entry, "size"), size))
                && (!childOf(entry, "bottom").IsDefined() || numberOf(entry, "bottom", sign.bottom))
                && (!childOf(entry, "out").IsDefined() || numberOf(entry, "out", sign.out))
                && (!childOf(entry, "offset").IsDefined() || numberOf(entry, "offset", offset));

            if (!readable || bay < 0.0 || bay >= part.bays[static_cast<size_t>(wall)].size() || bay != std::floor(bay)
                || size[0] < 16.0 || size[0] > 512.0 || size[1] < 16.0 || size[1] > 512.0 || sign.out < 2.0
                || sign.out > 128.0 || (sign.hang && sign.bottom + size[1] + 32.0 > part.wallHeight + 0.5))
            {
                add(where, "a sign on a wall is {wall, bay (of the wall's lowest row, from 0 at its left end seen "
                    "from outside: the board stands over its middle), texture (the board's picture, fitted once), "
                    "size: [width, height] (16 to 512; [128, 64] when left out: give the picture's own size), bottom "
                    "(over the part's foot; 272 when left out), out (how far its face stands from the wall, 2 to "
                    "128; 8), hang (the board stands across the wall, `out` from it, under an arm 32 over it that "
                    "must still meet the wall), offset (the board's middle this far from the bay's middle along the "
                    "wall, toward its right end seen from outside; 0)}");
                return;
            }

            sign.wall = static_cast<size_t>(wall);
            sign.width = size[0];
            sign.height = size[1];
            const std::vector<double> edges = bayEdgesOf(part, sign.wall, false);
            sign.along = (edges[static_cast<size_t>(bay)] + edges[static_cast<size_t>(bay) + 1]) * 0.5 + offset;
            const double length = edges.back();

            if ((!sign.hang && (sign.along - sign.width * 0.5 < -0.5 || sign.along + sign.width * 0.5 > length + 0.5))
                || (sign.hang && (sign.along < 8.0 || sign.along > length - 8.0))
                || sign.bottom < 0.0 || sign.bottom + sign.height > part.wallHeight + 0.5 || part.posts > 0.0
                || part.taper != 1.0)
            {
                add(where, "the sign stands from " + formatNumber(sign.bottom) + " to "
                    + formatNumber(sign.bottom + sign.height) + " over bay " + formatNumber(bay)
                    + (offset != 0.0 ? " (offset " + formatNumber(offset) + ")" : std::string()) + ", "
                    + formatNumber(sign.width) + " wide: it must lie on the wall (" + formatNumber(length) + " long, "
                    + formatNumber(part.wallHeight) + " high; an upright wall, not an open part's)");
                return;
            }

            sign.title = textOf(entry, "title");
            sign.path = m_path + where;
            double house = 0.0;

            if (childOf(entry, "house").IsDefined() && (!numberOf(entry, "house", house) || house < 1.0
                || house != std::floor(house) || sign.title.empty()))
            {
                add(where + ".house", "a sign's `house` is the number of a row of the house table, with a `title`");
                return;
            }

            sign.house = static_cast<int>(house);
            part.signs.push_back(sign);
        }

        const YAML::Node railing = childOf(node, "railing");

        if (railing.IsDefined())
        {
            OutdoorRailingPlan &plan = part.railing;
            const bool readable = railing.IsMap() && numberOf(railing, "height", plan.height)
                && (!childOf(railing, "posts").IsDefined() || numberOf(railing, "posts", plan.posts))
                && (!childOf(railing, "rail").IsDefined() || numberOf(railing, "rail", plan.rail))
                && (!childOf(railing, "every").IsDefined() || numberOf(railing, "every", plan.every))
                && (!childOf(railing, "depth").IsDefined() || numberOf(railing, "depth", plan.depth));

            if (!readable || plan.height < 16.0 || plan.height > 512.0 || plan.posts < 4.0 || plan.posts > 64.0
                || plan.rail < 4.0 || plan.rail > plan.height || plan.every < plan.posts * 2.0 || plan.every > 1024.0
                || plan.depth < 4.0 || plan.depth > 128.0)
            {
                add(at + ".railing", "a railing is {height (16 to 512: Ravenshore's terrace 208), posts (their "
                    "width along the wall, 4 to 64; 16), depth (the posts' and the rail's depth across it, 4 to 128; 32), "
                    "rail (the rail's height, 4 up to the railing's; 16), every (the widest gap between posts, at "
                    "least twice their width, up to 1024; 128), walls (the walls it runs along; all when left out)}");
                plan.height = 0.0;
                return;
            }

            if (part.roof.form != "flat" || part.roof.parapet > 0.0 || part.taper != 1.0)
            {
                add(at + ".railing", "a railing runs round a flat top: the part has `roof: flat` without a parapet "
                    "(a railing is the open kind) on upright walls");
                plan.height = 0.0;
                return;
            }

            if (!wallsNamed(building, partIndex, childOf(railing, "walls"), at + ".railing.walls", plan.walls))
            {
                plan.height = 0.0;
            }
        }
    }

    // Batch O-D's words that name walls: `batter_walls`, `eaves_walls`, the buttresses' walls, the stair's wall;
    // and what they need of the part's shape. False when the part is refused.
    bool readMassWalls(OutdoorBuildingPlan &building, size_t partIndex, const YAML::Node &node, const std::string &at)
    {
        OutdoorPartPlan &part = building.parts[partIndex];

        if (childOf(node, "batter_walls").IsDefined() && part.batter == 0.0)
        {
            add(at + ".batter_walls", "`batter_walls` names the walls of a battered part: give it `batter`");
            return false;
        }

        if (part.batter != 0.0)
        {
            if (!wallsNamed(building, partIndex, childOf(node, "batter_walls"), at + ".batter_walls",
                part.batterWalls))
            {
                return false;
            }

            std::vector<double> insets(part.outline.size(), 0.0);

            for (size_t wall = 0; wall < insets.size(); ++wall)
            {
                insets[wall] = part.batterWalls[wall] ? part.batter : 0.0;
            }

            if (!keepsShape(part.outline, outdoorOffsetOutline(part.outline, insets)))
            {
                add(at + ".batter", "the walls draw in " + formatNumber(part.batter) + " past the middle of the "
                    "part: make `batter` smaller");
                return false;
            }

            for (const OutdoorPorchPlan &porch : part.porches)
            {
                if (porch.recess && part.batterWalls[porch.wall])
                {
                    add(at + ".porches", "a recess stands in an upright wall; this wall is battered");
                    return false;
                }
            }
        }

        if (childOf(node, "eaves_walls").IsDefined())
        {
            if (part.roof.eaves <= 0.0)
            {
                add(at + ".eaves_walls", "`eaves_walls` names the walls the eaves reach out over: give the part "
                    "`eaves`");
                return false;
            }

            std::vector<std::vector<std::array<double, 2>>> stretches;
            bool partial = false;

            std::vector<double> amounts;

            if (!stretchesNamed(building, partIndex, childOf(node, "eaves_walls"), at + ".eaves_walls",
                part.roof.eavesWalls, stretches, partial, &amounts))
            {
                return false;
            }

            if (std::any_of(amounts.begin(), amounts.end(), [](double amount) { return amount >= 0.0; }))
            {
                part.roof.eavesAmounts = amounts;
            }

            if (partial)
            {
                const std::string &form = part.roof.form;

                if ((form != "flat" && form != "hip" && form != "gable") || !part.roof.tiers.empty()
                    || part.roof.cap > 0.0 || part.roof.ridge > 0.0 || part.taper != 1.0 || part.batter != 0.0
                    || !part.steps.empty() || part.ruin.given || !part.holes.empty())
                {
                    add(at + ".eaves_walls", "eaves along part of a wall go with a flat, hip or gable roof on upright "
                        "walls (no tiers, cap, ridge beam (`ridge: 0`), taper, batter, steps, ruin or holes)");
                    return false;
                }

                part.roof.eavesStretches = stretches;
                part.roof.eavesPartial = true;
            }
        }

        if (childOf(node, "parapet_walls").IsDefined())
        {
            std::vector<bool> marks;
            bool partial = false;

            if (part.roof.parapet <= 0.0)
            {
                add(at + ".parapet_walls", "`parapet_walls` names the walls a parapet stands on: give the part "
                    "`parapet` (and `roof: flat`)");
                return false;
            }

            if (!stretchesNamed(building, partIndex, childOf(node, "parapet_walls"), at + ".parapet_walls", marks,
                part.roof.parapetStretches, partial))
            {
                return false;
            }
        }

        const YAML::Node buttresses = childOf(node, "buttresses");

        if (part.buttresses.count > 0)
        {
            if (!wallsNamed(building, partIndex, childOf(buttresses, "walls"), at + ".buttresses.walls",
                part.buttresses.walls))
            {
                return false;
            }

            for (size_t wall = 0; wall < part.buttresses.walls.size(); ++wall)
            {
                if (part.buttresses.walls[wall] && part.batter != 0.0 && part.batterWalls[wall])
                {
                    add(at + ".buttresses", "buttresses stand against upright walls; wall " + std::to_string(wall)
                        + " is battered");
                    return false;
                }
            }
        }

        const YAML::Node stair = childOf(node, "stair");

        if (!stair.IsDefined())
        {
            return true;
        }

        OutdoorStairPlan &plan = part.stair;
        Point2 cheek = {plan.cheek, plan.cheekHeight};
        const int wall = stair.IsMap() ? wallOf(building, partIndex, textOf(stair, "wall", "s")) : -1;
        const bool readable = stair.IsMap() && wall >= 0
            && (!childOf(stair, "along").IsDefined() || numberOf(stair, "along", plan.along))
            && (!childOf(stair, "width").IsDefined() || numberOf(stair, "width", plan.width))
            && (!childOf(stair, "cheek").IsDefined() || pointOf(childOf(stair, "cheek"), cheek))
            && (!childOf(stair, "run").IsDefined() || numberOf(stair, "run", plan.run))
            && (!childOf(stair, "rise").IsDefined() || numberOf(stair, "rise", plan.rise));
        plan.cheek = cheek[0];
        plan.cheekHeight = cheek[1];
        plan.ramp = textOf(stair, "ramp") == "true";

        if (!readable || plan.width < 64.0 || plan.width > 2048.0 || plan.cheek < 0.0 || plan.cheek > 256.0
            || plan.cheekHeight < 0.0 || plan.cheekHeight > 512.0 || plan.run < 0.0 || plan.run > 8192.0
            || plan.rise < 8.0 || plan.rise > 64.0 || (!plan.ramp && plan.cheek > 0.0 && plan.cheekHeight <= plan.rise))
        {
            add(at + ".stair", "a stair is {wall (s, e, n, w or a number; s), along (its middle along the wall from "
                "its left end; the middle), width (64 to 2048; 256), cheek: [width, height] (the walls each side, "
                "0 to 256 wide, standing 0 to 512 over the steps' nosing, higher than a step; [64, 64]), run (how far "
                "it runs from its foot to the top, 0 to 8192; left out: from the wall's foot), rise (each step's "
                "height, 8 to 64; 32), ramp: true (one sloping face)}");
            return false;
        }

        plan.wall = static_cast<size_t>(wall);
        const double length = lengthOf(part.outline[plan.wall], part.outline[(plan.wall + 1) % part.outline.size()]);

        if (plan.along < 0.0)
        {
            plan.along = length * 0.5;
        }

        // Batch O-H: a flight inside an upright part up to its flat roof (Castle Ironfist's ramp to the King's
        // Library on the castle's top): cut `run` into the part from the wall's foot.
        const bool upright = part.steps.empty() && !(part.batter != 0.0 && part.batterWalls[plan.wall]);

        if (upright && (plan.run <= 0.0 || part.roof.form != "flat" || part.posts > 0.0))
        {
            add(at + ".stair", "a stair climbs a stepped or battered part (give the part `steps`, or `batter` on "
                "the stair's wall), or runs inside an upright part with a flat roof up to that roof: give it `run`, "
                "how far into the part it climbs");
            return false;
        }

        if (upright)
        {
            const double across = lengthOf(part.outline[(plan.wall + 1) % part.outline.size()],
                part.outline[(plan.wall + 2) % part.outline.size()]);

            if (plan.run > across - 1.0)
            {
                add(at + ".stair", "the stair's `run` (" + formatNumber(plan.run) + ") reaches through the part ("
                    + formatNumber(across) + " deep from its wall)");
                return false;
            }
        }

        if (plan.along - plan.width * 0.5 - plan.cheek < 0.0 || plan.along + plan.width * 0.5 + plan.cheek > length)
        {
            add(at + ".stair", "the stair with its cheeks (" + formatNumber(plan.width + 2.0 * plan.cheek)
                + " wide) does not fit on its wall (" + formatNumber(length) + " long) there");
            return false;
        }

        plan.given = true;
        return true;
    }

    // The texture a listed bay gives the door that takes it: its own name when the word is no role of the part
    // (`t14a03` in a row of thatch panels on a stone house); empty: the part's `door` role.
    static std::string doorTextureOf(const OutdoorPartPlan &part, const std::string &word)
    {
        return word != "door" && !part.textures.contains(word) ? word : std::string();
    }

    // The picture a door shows, in lower case: its bay's own texture, else its part's `door`.
    static std::string doorPictureOf(const OutdoorPartPlan &part, const OutdoorDoorPlan &door)
    {
        const std::map<std::string, std::string>::const_iterator role = part.textures.find("door");
        std::string name = !door.texture.empty() ? door.texture
            : role != part.textures.end() ? role->second : std::string();
        std::transform(name.begin(), name.end(), name.begin(),
            [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
        return name;
    }

    // The texels across of a door's picture as the texture classes know it; 0 when they do not.
    double doorPictureWidth(const OutdoorPartPlan &part, const OutdoorDoorPlan &door) const
    {
        if (m_pDoorPictures == nullptr)
        {
            return 0.0;
        }

        const OutdoorDoorPictures::const_iterator known = m_pDoorPictures->find(doorPictureOf(part, door));
        return known != m_pDoorPictures->end() && known->second.size[0] >= 32 ? known->second.size[0] : 0.0;
    }

    // F2: a door that says no `leaves` and whose picture is one wing of a double door (the texture classes: MM7's
    // 7hhr1d2, MM8's t06a03, t09a03a ...) becomes a pair, its first leaf the left wing (of the twins the first by
    // name: 7hhr1d1, t06a03, chb1dl), the second it mirrored, as tools/xeen/house_doors.py did for each sketch. On a
    // listed bay under 192 wide it stays one leaf, with a warning.
    void pairWingDoor(const OutdoorPartPlan &part, OutdoorDoorPlan &door, double bayWidth)
    {
        if (m_pDoorPictures == nullptr || door.leavesGiven)
        {
            return;
        }

        const std::string picture = doorPictureOf(part, door);
        const OutdoorDoorPictures::const_iterator known = m_pDoorPictures->find(picture);

        if (known == m_pDoorPictures->end() || known->second.door != "wing")
        {
            return;
        }

        if (bayWidth < 192.0 - 0.5)
        {
            if (m_pWarnings != nullptr)
            {
                m_pWarnings->push_back(m_path + ": the door's picture " + picture + " is one wing of a double door, "
                    "on a listed bay " + formatNumber(bayWidth) + " wide: list the door's bay 256 wide (`[door, "
                    "256]`) to make it a pair, or give it a single door's picture (`leaves: 1` keeps the wing alone)");
            }

            return;
        }

        door.leaves = 2;

        if (!known->second.twin.empty() && known->second.twin < picture)
        {
            door.texture = known->second.twin;
        }
    }

    // F2: a double door on a wall whose bays are not listed: the wall laid out round one bay 256 wide (each leaf
    // 128, a wing's width) centred where the door's bay was, the stretches beside it in bays of about 128 (a window
    // next to the door, every second bay out from it, the posts at the ends). A recess of the door moves with it.
    // False, nothing changed, on a wall too short for it.
    bool layPairBay(OutdoorPartPlan &part, OutdoorDoorPlan &door, bool posts, const std::string &windows)
    {
        const size_t wall = door.wall;
        const double length = lengthOf(part.outline[wall], part.outline[(wall + 1) % part.outline.size()]);
        const size_t count = part.bays[wall].size();
        const double pair = 2.0 * BayWidth;

        if (count == 0 || length < pair - 0.5 || (length > pair + 0.5 && length < pair + 32.0))
        {
            return false;
        }

        const double middle = (static_cast<double>(door.bay) + 0.5) * length / static_cast<double>(count);
        double from = std::clamp(middle - BayWidth, 0.0, std::max(0.0, length - pair));

        // No sliver beside the door: a stretch under 16 goes to the door's other side.
        from = from < 16.0 ? 0.0 : length - pair - from < 16.0 ? std::max(0.0, length - pair) : from;
        const double rest = std::max(0.0, length - pair - from);
        const auto pieces = [](double stretch)
        {
            return stretch < 0.5 ? size_t(0) : std::max<size_t>(1, static_cast<size_t>(std::round(stretch / BayWidth)));
        };
        const size_t left = pieces(from);
        const size_t right = pieces(rest);
        std::vector<double> widths(left, left > 0 ? from / static_cast<double>(left) : 0.0);
        widths.push_back(std::min(pair, length));
        widths.insert(widths.end(), right, right > 0 ? rest / static_cast<double>(right) : 0.0);
        const size_t oldBay = door.bay;
        door.bay = left;
        part.bays[wall] = defaultBays(widths.size(), posts, windows, static_cast<int>(door.bay));

        if (wall >= part.bayWidths.size())
        {
            part.bayWidths.resize(wall + 1);
        }

        part.bayWidths[wall] = widths;

        for (OutdoorPorchPlan &porch : part.porches)
        {
            if (porch.recess && porch.wall == wall && porch.fromBay == oldBay && porch.toBay == oldBay)
            {
                porch.fromBay = door.bay;
                porch.toBay = door.bay;
            }
        }

        return true;
    }

    const std::string &m_world;
    const YAML::Node m_plot;
    const std::string m_path;
    const std::array<double, 4> m_rectangle;
    std::vector<ProjectIssue> &m_issues;
    const WorldRoof *m_pWorldRoof = nullptr;
    const OutdoorDoorPictures *m_pDoorPictures = nullptr;
    std::vector<std::string> *m_pWarnings = nullptr;
    double m_turn = 0.0;
    std::vector<YAML::Node> m_partNodes;
    std::vector<std::vector<size_t>> m_wallOrder;
    std::vector<bool> m_doorBayGiven;
};

// Raises one part into the model.
class PartRaiser
{
public:
    PartRaiser(OutdoorModelBuilder &builder, OutdoorBuildingPlan &building, size_t partIndex,
        const LoweredOutdoorMap *pLand)
        : m_builder(builder)
        , m_pLand(pLand)
        , m_building(building)
        , m_partIndex(partIndex)
        , m_part(building.parts[partIndex])
        , m_count(m_part.outline.size())
        , m_floor(building.base + m_part.bottom)
        , m_top(m_floor + m_part.wallHeight)
        , m_foot(m_top + m_part.roof.fascia)
        , m_nameEvent(m_part.event != 0 ? m_part.event : building.nameEvent)
        , m_topOutline(m_part.outline)
    {
        if (m_part.taper != 1.0)
        {
            // The top of leaning walls: the outline drawn in (or out) about its middle.
            Point2 middle = {0.0, 0.0};

            for (const Point2 &point : m_part.outline)
            {
                middle = {middle[0] + point[0] / m_count, middle[1] + point[1] / m_count};
            }

            for (Point2 &point : m_topOutline)
            {
                point = {middle[0] + (point[0] - middle[0]) * m_part.taper,
                    middle[1] + (point[1] - middle[1]) * m_part.taper};
            }
        }

        if (m_part.batter != 0.0)
        {
            m_topOutline = ringAt(m_top);
        }
    }

    void raise()
    {
        // Doors cut into a roof and a stair cut into the part change faces already made: the part's faces are kept
        // aside until both are cut out of them.
        m_capturing = m_part.stair.given || notchDoors();

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            if (m_part.ruin.given)
            {
                raiseRuinWall(wall);
            }
            else
            {
                raiseWall(wall);
            }
        }

        if (m_part.bottom > 0.0)
        {
            raiseUnderside();
        }

        raiseOpen();
        raiseCourtWalls();
        const double wallTop = m_top;
        const double wallFoot = m_foot;
        const std::vector<Point2> wallOutline = m_topOutline;
        raiseTerraces();

        if (m_part.ruin.given)
        {
            raiseRuinRoof();
        }
        else
        {
            raiseRoof();
        }

        const double terraceTop = m_top;
        m_top = wallTop;
        m_foot = wallFoot;
        m_topOutline = wallOutline;

        if (m_capturing)
        {
            m_capturing = false;
            finishCaptured(terraceTop);
        }

        raiseButtresses();
        raiseClimbs();
        raiseRecesses();
        raisePorches();
        raisePent();
        raiseSigns();
        raiseRailing();
        raiseSteps();
        raiseDoorDressing();
    }

private:
    static OutdoorModelPoint at(const Point2 &point, double z)
    {
        return {point[0], point[1], z};
    }

    // Faces kept aside (`m_capturing`) to be cut by doors in the roof and a stair before they go into the model.
    struct Captured
    {
        std::vector<OutdoorModelPoint> points;
        std::string texture;
        std::vector<std::array<double, 2>> texels;
        bool given = false;
        uint16_t event = 0;
        bool through = false;
    };

    // ---- Batch O-D: masses and roofs (domes, batter and buttresses, roofs to the ground, terraces and stairs,
    // ruins, eaves per wall). Members of PartRaiser. ----

    // The faces of the part go through these: into the model, or aside while `m_capturing` (the number returned is
    // then the face's place among those kept aside).
    int surface(const std::vector<OutdoorModelPoint> &points, const std::string &textureName, uint16_t event)
    {
        if (!m_capturing)
        {
            return m_builder.addSurface(points, textureName, event);
        }

        m_captured.push_back({points, textureName, {}, false, event, false});
        return static_cast<int>(m_captured.size()) - 1;
    }

    int texelFace(const std::vector<OutdoorModelPoint> &points, const std::string &textureName,
        const std::vector<std::array<double, 2>> &texels, uint16_t event)
    {
        if (!m_capturing)
        {
            return m_builder.addFace(points, textureName, texels, event);
        }

        m_captured.push_back({points, textureName, texels, true, event, false});
        return static_cast<int>(m_captured.size()) - 1;
    }

    void through(int index)
    {
        if (!m_capturing)
        {
            m_builder.letThrough(index);
        }
        else if (index >= 0)
        {
            m_captured[static_cast<size_t>(index)].through = true;
        }
    }

    // A face turned to look along `normal` (its corners reversed if they ran the other way).
    static std::vector<OutdoorModelPoint> facing(std::vector<OutdoorModelPoint> points,
        const std::array<double, 3> &normal)
    {
        std::array<double, 3> newell = {0.0, 0.0, 0.0};

        for (size_t index = 0; index < points.size(); ++index)
        {
            const OutdoorModelPoint &a = points[index];
            const OutdoorModelPoint &b = points[(index + 1) % points.size()];
            newell[0] += (a[1] - b[1]) * (a[2] + b[2]);
            newell[1] += (a[2] - b[2]) * (a[0] + b[0]);
            newell[2] += (a[0] - b[0]) * (a[1] + b[1]);
        }

        if (newell[0] * normal[0] + newell[1] * normal[1] + newell[2] * normal[2] < 0.0)
        {
            std::reverse(points.begin(), points.end());
        }

        return points;
    }

    // ---- Doors higher than the walls, cut into the roof ----

    bool notchDoor(const OutdoorDoorPlan &door) const
    {
        // A door's own height when the part gives one; else a door is cut into the roof only where the walls are
        // too low to hold half of one (before batch O-D such a door was refused).
        return door.part == m_partIndex && door.storey == 0 && m_part.posts <= 0.0
            && (m_part.doorHeight > 0.0 ? m_part.wallHeight < m_part.doorHeight - 0.5
            : m_part.wallHeight < RowHeight * 0.5);
    }

    bool notchDoors() const
    {
        return std::any_of(m_building.doors.begin(), m_building.doors.end(), [this](const OutdoorDoorPlan &door)
        {
            return notchDoor(door);
        });
    }

    // ---- Batter ----

    // How far a wall stands in at a height: its batter's share of the way up the sloping foot.
    double insetOf(size_t wall, double z) const
    {
        if (m_part.batter == 0.0 || (!m_part.batterWalls.empty() && !m_part.batterWalls[wall]))
        {
            return 0.0;
        }

        const double height = m_part.batterHeight > 0.0 ? m_part.batterHeight : m_part.wallHeight;
        return m_part.batter * std::clamp((z - m_floor) / std::max(height, 1.0), 0.0, 1.0);
    }

    // The outline of a battered part at a height.
    std::vector<Point2> ringAt(double z) const
    {
        std::vector<double> insets(m_count, 0.0);

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            insets[wall] = insetOf(wall, z);
        }

        return outdoorOffsetOutline(m_part.outline, insets);
    }

    // A point of a battered part's wall: `share` of the way along it at height z.
    OutdoorModelPoint onSlope(size_t wall, double share, double z) const
    {
        const std::vector<Point2> ring = ringAt(z);
        const Point2 &left = ring[wall];
        const Point2 &right = ring[(wall + 1) % m_count];
        return {left[0] + (right[0] - left[0]) * share, left[1] + (right[1] - left[1]) * share, z};
    }

    // A piece of a battered part's wall (`wallPiece`): from its foot's [from, to] to the same shares of the wall at
    // each height, cut where the sloping foot ends.
    int slopedPiece(size_t wall, double from, double to, double low, double high, const std::string &textureName,
        double uFrom, double uTo, double vTop, double vBottom, uint16_t event)
    {
        const double length = std::max(lengthOf(m_part.outline[wall], m_part.outline[(wall + 1) % m_count]), 1.0e-9);
        const double knee = m_floor + (m_part.batterHeight > 0.0 ? m_part.batterHeight : m_part.wallHeight);
        std::vector<double> heights = {low};

        if (knee > low + 0.5 && knee < high - 0.5)
        {
            heights.push_back(knee);
        }

        heights.push_back(high);
        int first = -1;

        for (size_t index = 0; index + 1 < heights.size(); ++index)
        {
            const double z0 = heights[index];
            const double z1 = heights[index + 1];
            const auto v = [&](double z)
            {
                return vBottom + (vTop - vBottom) * (z - low) / std::max(high - low, 1.0e-9);
            };
            const int made = texelFace({onSlope(wall, from / length, z0), onSlope(wall, to / length, z0),
                onSlope(wall, to / length, z1), onSlope(wall, from / length, z1)}, textureName,
                {{uFrom, v(z0)}, {uTo, v(z0)}, {uTo, v(z1)}, {uFrom, v(z1)}}, event);
            first = first < 0 ? made : first;
        }

        return first;
    }

    // The wedge round a door standing upright at the foot of a battered wall: its two cheeks from the door's plane
    // back to the slope, and a level top over the door's head.
    void raiseWedge(size_t wall, double from, double to, double low, double high)
    {
        const double depth = insetOf(wall, high);

        if (depth < 0.5)
        {
            return;
        }

        const std::string &wallTexture = texture("wall");
        const Point2 &left = m_part.outline[wall];
        const Point2 &right = m_part.outline[(wall + 1) % m_count];
        const double length = std::max(lengthOf(left, right), 1.0e-9);
        const std::array<double, 3> along = {(right[0] - left[0]) / length, (right[1] - left[1]) / length, 0.0};
        const double knee = m_floor + (m_part.batterHeight > 0.0 ? m_part.batterHeight : m_part.wallHeight);

        for (const bool end : {false, true})
        {
            const double place = end ? to : from;
            std::vector<OutdoorModelPoint> points = {at(onWall(wall, place), low)};

            if (knee > low + 0.5 && knee < high - 0.5)
            {
                points.push_back(at(onWall(wall, place, insetOf(wall, knee)), knee));
            }

            points.push_back(at(onWall(wall, place, depth), high));
            points.push_back(at(onWall(wall, place), high));
            surface(facing(points, end ? along : std::array<double, 3>{-along[0], -along[1], 0.0}), wallTexture,
                m_nameEvent);
        }

        surface(facing({at(onWall(wall, from), high), at(onWall(wall, to), high), at(onWall(wall, to, depth), high),
            at(onWall(wall, from, depth), high)}, {0.0, 0.0, 1.0}), textureOr("lintel", "trim"), m_nameEvent);
    }

    // Buttresses: piers against the walls named, their tops sloping down to the front.
    void raiseButtresses()
    {
        const OutdoorButtressPlan &plan = m_part.buttresses;

        if (plan.count <= 0)
        {
            return;
        }

        const std::string &stone = textureOr("buttress", "wall");

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            if (wall < plan.walls.size() && !plan.walls[wall])
            {
                continue;
            }

            const Point2 &left = m_part.outline[wall];
            const Point2 &right = m_part.outline[(wall + 1) % m_count];
            const double length = lengthOf(left, right);
            const std::array<double, 3> along = {(right[0] - left[0]) / length, (right[1] - left[1]) / length, 0.0};
            const std::array<double, 3> out = {along[1], -along[0], 0.0};
            const double foot = groundFoot();
            const double back = m_floor + plan.height;
            const double front = back - plan.depth;

            for (int index = 0; index < plan.count; ++index)
            {
                const double middle = length * (index + 0.5) / plan.count;
                const double from = std::max(0.0, middle - plan.width * 0.5);
                const double to = std::min(length, middle + plan.width * 0.5);
                const Point2 wallFrom = onWall(wall, from);
                const Point2 wallTo = onWall(wall, to);
                const Point2 frontFrom = onWall(wall, from, -plan.depth);
                const Point2 frontTo = onWall(wall, to, -plan.depth);
                surface(facing({at(frontFrom, foot), at(frontTo, foot), at(frontTo, front), at(frontFrom, front)}, out),
                    stone, m_nameEvent);
                surface(facing({at(wallFrom, foot), at(frontFrom, foot), at(frontFrom, front), at(wallFrom, back)},
                    {-along[0], -along[1], 0.0}), stone, m_nameEvent);
                surface(facing({at(frontTo, foot), at(wallTo, foot), at(wallTo, back), at(frontTo, front)}, along),
                    stone, m_nameEvent);
                surface(facing({at(wallFrom, back), at(wallTo, back), at(frontTo, front), at(frontFrom, front)},
                    {0.0, 0.0, 1.0}), stone, m_nameEvent);
            }
        }
    }

    // ---- The underside of a part that hangs ----

    // Under the walls' outline, less the recesses' floors (a recess under a hanging part opens to the street: its
    // underside would lie across it, on the plinth, facing the other way).
    void raiseUnderside()
    {
        std::vector<std::vector<Point2>> pieces;
        bool cut = false;

        if (m_part.concave)
        {
            pieces = convexPartsOf(m_part.outline);
        }
        else
        {
            pieces.push_back(m_part.outline);
        }

        for (const OutdoorPorchPlan &porch : m_part.porches)
        {
            if (!porch.recess)
            {
                continue;
            }

            cut = true;
            const std::vector<double> edges = bayEdgesOf(m_part, porch.wall, false);
            // The recess's floor, counter-clockwise: the wall's stretch and the same set back.
            const std::vector<Point2> hole = {onWall(porch.wall, edges[porch.fromBay]),
                onWall(porch.wall, edges[porch.toBay + 1]), onWall(porch.wall, edges[porch.toBay + 1], porch.depth),
                onWall(porch.wall, edges[porch.fromBay], porch.depth)};
            std::vector<std::vector<Point2>> left;

            for (const std::vector<Point2> &piece : pieces)
            {
                std::vector<Point2> rest = piece;

                for (size_t side = 0; side < hole.size() && rest.size() >= 3; ++side)
                {
                    const Point2 &from = hole[side];
                    const Point2 &to = hole[(side + 1) % hole.size()];
                    const Point2 normal = {to[1] - from[1], from[0] - to[0]};
                    const std::vector<Point2> outside = clipped(rest, from, {-normal[0], -normal[1]});

                    if (outside.size() >= 3 && std::fabs(signedArea(outside)) > 1.0)
                    {
                        left.push_back(outside);
                    }

                    rest = clipped(rest, from, normal);
                }
            }

            pieces = left;
        }

        for (const std::vector<Point2> &piece : pieces)
        {
            std::vector<OutdoorModelPoint> points;

            for (size_t index = piece.size(); index-- > 0;)
            {
                points.push_back(at(piece[index], m_floor));
            }

            if (!cut || points.size() >= 3)
            {
                surface(points, texture("trim"), m_nameEvent);
            }
        }
    }

    // ---- Terraces ----

    // Over the walls' top: each terrace's tread (the ring between the outline and the next drawn in) and the next's
    // upright riser; the roof is then raised on the last.
    void raiseTerraces()
    {
        if (m_part.steps.empty())
        {
            return;
        }

        const std::string &tread = textureOr("tread", "roof");
        const std::string &riser = textureOr("riser", "wall");
        std::vector<Point2> outline = m_topOutline;
        double z = m_top;

        for (const std::array<double, 2> &step : m_part.steps)
        {
            const std::vector<Point2> next = grown(outline, -step[0]);

            if (step[0] > 0.5)
            {
                ring(next, outline, z, false, tread);
            }

            band(next, z, z + step[1], false, riser);
            outline = next;
            z += step[1];
        }

        m_topOutline = outline;
        m_top = z;
        m_foot = z + m_part.roof.fascia;
    }

    // ---- Domes ----

    // A dome over the roof's foot: `domeRings` rings of the outline drawn in toward its middle along a quarter
    // circle, the last to a tip.
    void raiseDome(const std::vector<Point2> &outer, double tip)
    {
        const std::string &roofTexture = texture("roof");
        const int rings = m_part.roof.domeRings;
        Point2 middle = {0.0, 0.0};

        for (const Point2 &point : outer)
        {
            middle = {middle[0] + point[0] / outer.size(), middle[1] + point[1] / outer.size()};
        }

        const auto ringOf = [&](int index)
        {
            const double angle = index * Pi * 0.5 / rings;
            std::vector<Point2> result;

            for (const Point2 &point : outer)
            {
                result.push_back({middle[0] + (point[0] - middle[0]) * oy::cos(angle),
                    middle[1] + (point[1] - middle[1]) * oy::cos(angle)});
            }

            return std::make_pair(result, m_foot + (tip - m_foot) * oy::sin(angle));
        };

        for (int index = 0; index < rings; ++index)
        {
            const std::pair<std::vector<Point2>, double> low = ringOf(index);
            const std::pair<std::vector<Point2>, double> high = ringOf(index + 1);

            for (size_t side = 0; side < outer.size(); ++side)
            {
                const size_t next = (side + 1) % outer.size();

                if (index + 1 == rings)
                {
                    surface({at(low.first[side], low.second), at(low.first[next], low.second), at(middle, tip)},
                        roofTexture, m_nameEvent);
                }
                else
                {
                    surface({at(low.first[side], low.second), at(low.first[next], low.second),
                        at(high.first[next], high.second), at(high.first[side], high.second)}, roofTexture,
                        m_nameEvent);
                }
            }
        }
    }

    // ---- Eaves per wall ----

    double eavesOf(size_t wall) const
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        const double own = wall < roof.eavesAmounts.size() && roof.eavesAmounts[wall] >= 0.0 ? roof.eavesAmounts[wall]
            : roof.eaves;
        return roof.eavesWalls.empty() || (wall < roof.eavesWalls.size() && roof.eavesWalls[wall]) ? own : 0.0;
    }

    // The roof's foot with eaves over the walls `eaves_walls` names only; `ends` (0 or 1) marks the gable ends of a
    // box's gable roof, which take none.
    std::vector<Point2> eavesOutline(int ends) const
    {
        std::vector<double> insets(m_count, 0.0);

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            insets[wall] = ends >= 0 && static_cast<int>(wall % 2) == ends ? 0.0 : -eavesOf(wall);
        }

        return outdoorOffsetOutline(m_topOutline, insets);
    }

    // ---- Ruins ----

    // A number in [0, 1) from the ruin's seed and three more.
    double chance(uint32_t a, uint32_t b, uint32_t c) const
    {
        uint32_t value = m_part.ruin.seed * 2654435761u ^ (a + 0x9e3779b9u) * 2246822519u ^ (b + 17u) * 3266489917u
            ^ (c + 31u) * 668265263u ^ static_cast<uint32_t>(m_partIndex) * 374761393u;
        value ^= value >> 15;
        value *= 2246822519u;
        value ^= value >> 13;
        value *= 3266489917u;
        value ^= value >> 16;
        return (value & 0xffffff) / 16777216.0;
    }

    // A piece of a ruined wall: a stretch of one row between two bay edges of any row (so the pieces of the rows,
    // the tops and the foundation meet corner to corner: a long edge past another face's corner leaves a crack where
    // the corners are rounded to whole units), its foot and top, its role, its door (an index into the building's
    // doors, or -1; a door is one piece) and where its picture starts along it (plain bays side by side that stand as
    // high run on as one picture, as on a whole wall).
    struct RuinPiece
    {
        double from = 0.0;
        double to = 0.0;
        double low = 0.0;
        double high = 0.0;
        std::string role;
        int door = -1;
        double u = 0.0;
    };

    // The pieces of a ruined wall: the bays of its lowest row each to its own height (a door's bay stands whole),
    // some gone; the rows above over the bays under them. `cuts`: every bay edge of every row, in order.
    std::vector<RuinPiece> ruinPieces(size_t wall, std::vector<double> &cuts) const
    {
        const OutdoorRuinPlan &ruin = m_part.ruin;
        // The lowest row's bays: their heights (0, or one course over a foundation: gone).
        const std::vector<double> lowEdges = bayEdgesOf(m_part, wall, false);
        std::vector<double> standing(lowEdges.size() - 1, 0.0);
        const auto doorAt = [&](int row, size_t bay)
        {
            for (size_t index = 0; index < m_building.doors.size(); ++index)
            {
                const OutdoorDoorPlan &door = m_building.doors[index];

                if (row == 0 && door.part == m_partIndex && door.wall == wall && door.bay == bay && door.storey == 0)
                {
                    return static_cast<int>(index);
                }
            }

            return -1;
        };

        // A gone bay over a foundation keeps one stone course: a cap at the floor itself would lie on the levelled
        // land and flicker (P4 feedback F58, the ruins' footings).
        constexpr double RuinCourse = 8.0;
        const double goneHeight = m_building.foundation > 0.0 && m_part.bottom == 0.0 ? RuinCourse : 0.0;

        for (size_t bay = 0; bay < standing.size(); ++bay)
        {
            const bool door = doorAt(0, bay) >= 0;
            const double height = ruin.low + (ruin.high - ruin.low) * chance(static_cast<uint32_t>(wall),
                static_cast<uint32_t>(bay), 1);
            standing[bay] = door ? std::max(height, std::min(m_part.wallHeight, RowHeight))
                : chance(static_cast<uint32_t>(wall), static_cast<uint32_t>(bay), 2) < ruin.gaps ? goneHeight : height;

            // D-170: the course's cap stands 4 over the land under it where the land beyond the levelled plot
            // rises to it (D3's roadside ruin), never lower than the course.
            if (goneHeight > 0.0 && standing[bay] == goneHeight && ruin.thickness > 0.0)
            {
                standing[bay] = std::max(goneHeight, clearOfLand({onWall(wall, lowEdges[bay]),
                    onWall(wall, lowEdges[bay + 1]), onWall(wall, lowEdges[bay + 1], ruin.thickness),
                    onWall(wall, lowEdges[bay], ruin.thickness)}, m_floor + goneHeight) - m_floor);
            }
        }

        // How high the wall stands over a stretch: the least of the lowest row's bays it covers.
        const auto standsOver = [&](double from, double to)
        {
            double least = 1.0e18;

            for (size_t bay = 0; bay < standing.size(); ++bay)
            {
                if (lowEdges[bay + 1] > from + 0.5 && lowEdges[bay] < to - 0.5)
                {
                    least = std::min(least, standing[bay]);
                }
            }

            return least > 1.0e17 ? 0.0 : least;
        };
        std::vector<RuinPiece> pieces;
        const auto rowLow = [&](int row)
        {
            return m_floor + row * RowHeight + (row > 0 ? m_part.band : 0.0);
        };
        cuts = lowEdges;

        for (int row = 1; rowLow(row) < m_top - 0.5; ++row)
        {
            const std::vector<double> edges = bayEdgesOf(m_part, wall, true);
            cuts.insert(cuts.end(), edges.begin(), edges.end());
        }

        std::sort(cuts.begin(), cuts.end());
        cuts.erase(std::unique(cuts.begin(), cuts.end(), [](double a, double b)
        {
            return std::fabs(a - b) < 0.5;
        }), cuts.end());

        for (int row = 0; rowLow(row) < m_top - 0.5; ++row)
        {
            const double low = rowLow(row);
            const double rowHigh = std::min(m_top, low + RowHeight);
            const std::vector<std::string> &bays = row == 0 ? m_part.bays[wall] : m_part.upperBays[wall];
            const std::vector<double> edges = bayEdgesOf(m_part, wall, row > 0);
            const size_t count = std::max<size_t>(1, bays.size());

            for (size_t bay = 0, end = 1; bay < count; bay = end)
            {
                const double from = edges[bay];
                const int door = doorAt(row, bay);
                const std::string role = bays.empty() ? "wall" : bays[bay];
                const double high = std::min(rowHigh, m_floor + standsOver(from, edges[bay + 1]));
                end = bay + 1;

                // Plain bays side by side that stand as high are one face, as on a whole wall.
                while (door < 0 && end < count && tiles(role) && bays[end] == role && doorAt(row, end) < 0
                    && std::fabs(std::min(rowHigh, m_floor + standsOver(edges[end], edges[end + 1])) - high) < 0.5)
                {
                    ++end;
                }

                if (high < low + 1.0)
                {
                    continue;
                }

                if (door >= 0)
                {
                    pieces.push_back({from, edges[end], low, high, role, door, 0.0});
                    continue;
                }

                // Cut at every bay edge of the other rows within it.
                double start = from;

                for (const double cut : cuts)
                {
                    if (cut > start + 0.5 && cut < edges[end] - 0.5)
                    {
                        pieces.push_back({start, cut, low, high, role, -1, start - from});
                        start = cut;
                    }
                }

                pieces.push_back({start, edges[end], low, high, role, -1, start - from});
            }
        }

        return pieces;
    }

    // The wall's top over each stretch between the bays' edges (`cuts`, in order): [from, to, height], the highest
    // piece over it, the part's floor where none stands.
    std::vector<std::array<double, 3>> ruinTops(const std::vector<RuinPiece> &pieces,
        const std::vector<double> &cuts) const
    {
        std::vector<std::array<double, 3>> tops;

        for (size_t index = 0; index + 1 < cuts.size(); ++index)
        {
            double high = m_floor;

            for (const RuinPiece &piece : pieces)
            {
                if (piece.from < cuts[index] + 0.5 && piece.to > cuts[index + 1] - 0.5)
                {
                    high = std::max(high, piece.high);
                }
            }

            tops.push_back({cuts[index], cuts[index + 1], high});
        }

        return tops;
    }

    // How high a ruined wall stands at its start (`atEnd` false) or its end: the part's floor where it is gone or not
    // raised (a back wall).
    double ruinStandsAt(size_t wall, bool atEnd) const
    {
        if (backWall(wall))
        {
            return m_floor;
        }

        std::vector<double> cuts;
        const std::vector<RuinPiece> pieces = ruinPieces(wall, cuts);
        const std::vector<std::array<double, 3>> tops = ruinTops(pieces, cuts);

        return tops.empty() ? m_floor : atEnd ? tops.back()[2] : tops.front()[2];
    }

    // Where the inner faces of a wall and the next meet at their corner (the two lines `in` inside the outline
    // crossing): how far along each wall from its own start, the first for `wall` (its length less a convex
    // corner's share), the second for the next wall.
    std::array<double, 2> ruinMitre(size_t wall, double in) const
    {
        const Point2 &left = m_part.outline[wall];
        const Point2 &corner = m_part.outline[(wall + 1) % m_count];
        const Point2 &right = m_part.outline[(wall + 2) % m_count];
        const double firstLength = std::max(lengthOf(left, corner), 1.0e-9);
        const double secondLength = std::max(lengthOf(corner, right), 1.0e-9);
        const Point2 first = {(corner[0] - left[0]) / firstLength, (corner[1] - left[1]) / firstLength};
        const Point2 second = {(right[0] - corner[0]) / secondLength, (right[1] - corner[1]) / secondLength};
        const double turn = first[0] * second[1] - first[1] * second[0];

        if (std::fabs(turn) < 1.0e-6)
        {
            // Straight on (or folded back): the inner faces meet over the corner.
            return {firstLength, 0.0};
        }

        // Each wall's inside is to its left: (-y, x).
        const Point2 shift = {(-second[1] + first[1]) * in, (second[0] - first[0]) * in};
        const double along = (shift[0] * second[1] - shift[1] * second[0]) / turn;
        const Point2 meet = {-first[1] * in + first[0] * along, first[0] * in + first[1] * along};
        const double onSecond = (meet[0] + second[1] * in) * second[0] + (meet[1] - second[0] * in) * second[1];
        // Never past the far end of either wall (a corner sharper than the walls are long).
        return {std::clamp(firstLength + along, 0.0, firstLength * 2.0),
            std::clamp(onSecond, -secondLength, secondLength)};
    }

    // A ruined wall (ruinPieces): the wall `thickness` thick with its inner face, its tops and its ends where a
    // stretch is lower or gone. At each corner of the outline the inner faces of the two walls meet where their
    // lines cross (mitred) and the higher wall's end closes it down to the lower's top along that mitre, so a ruin is
    // a closed shell (P2 feedback F30, the Ruined watchtower on X1).
    void raiseRuinWall(size_t wall)
    {
        if (backWall(wall))
        {
            return;
        }

        const OutdoorRuinPlan &ruin = m_part.ruin;
        const double length = lengthOf(m_part.outline[wall], m_part.outline[(wall + 1) % m_count]);
        std::vector<double> cuts;
        const std::vector<RuinPiece> pieces = ruinPieces(wall, cuts);
        const double in = ruin.thickness;
        // The foundation: under the whole wall, in stretches between the bay edges; with a thickness its inside too
        // and a sill at the floor where the wall is gone (below), so the land lying a little under the floor shows
        // no gap.
        const double foundation = m_part.bottom == 0.0 ? m_building.foundation : 0.0;

        for (size_t index = 0; foundation > 0.0 && index + 1 < cuts.size(); ++index)
        {
            wallPiece(wall, cuts[index], cuts[index + 1], m_floor - foundation, m_floor, texture("base"), cuts[index],
                cuts[index + 1], 0.0, foundation, m_nameEvent);
        }
        const size_t previous = (wall + m_count - 1) % m_count;
        // How far along this wall its inner face starts and ends: where the inside lines of the walls before and
        // after cross it.
        const double innerStart = in > 0.0 ? ruinMitre(previous, in)[1] : 0.0;
        const double innerEnd = in > 0.0 ? ruinMitre(wall, in)[0] : length;

        // The inside of a stretch from `low` to `high` (to the mitre at a corner).
        const auto innerFace = [&](double from, double to, double low, double high, const std::string &textureName,
            double vTop, double vBottom)
        {
            const double innerFrom = from < 0.5 ? innerStart : std::max(from, innerStart);
            const double innerTo = to > length - 0.5 ? innerEnd : std::min(to, innerEnd);

            if (innerTo > innerFrom + 0.5)
            {
                texelFace({at(onWall(wall, innerTo, in), low), at(onWall(wall, innerFrom, in), low),
                    at(onWall(wall, innerFrom, in), high), at(onWall(wall, innerTo, in), high)}, textureName,
                    {{length - innerTo, vBottom}, {length - innerFrom, vBottom}, {length - innerFrom, vTop},
                    {length - innerTo, vTop}}, m_nameEvent);
            }
        };

        for (size_t index = 0; foundation > 0.0 && in > 0.0 && index + 1 < cuts.size(); ++index)
        {
            innerFace(cuts[index], cuts[index + 1], m_floor - foundation, m_floor, texture("base"), 0.0, foundation);
        }

        for (const RuinPiece &piece : pieces)
        {
            OutdoorDoorPlan *pDoor = piece.door >= 0 ? &m_building.doors[static_cast<size_t>(piece.door)] : nullptr;
            const std::string &faceTexture = pDoor != nullptr && !pDoor->texture.empty() ? pDoor->texture
                : texture(piece.role);
            const double across = piece.to - piece.from;
            const double tall = piece.high - piece.low;
            const int face = wallPiece(wall, piece.from, piece.to, piece.low, piece.high, faceTexture, piece.u,
                piece.u + across, RowHeight - tall, RowHeight,
                pDoor != nullptr && pDoor->event != 0 ? pDoor->event : m_nameEvent);

            if (pDoor != nullptr)
            {
                const Point2 middle = onWall(wall, (piece.from + piece.to) * 0.5);
                const Point2 &left = m_part.outline[wall];
                const Point2 &right = m_part.outline[(wall + 1) % m_count];
                pDoor->face = face;
                pDoor->x = middle[0];
                pDoor->y = middle[1];
                pDoor->z = piece.low;
                pDoor->normalX = (right[1] - left[1]) / length;
                pDoor->normalY = -(right[0] - left[0]) / length;
            }

            if (in > 0.0)
            {
                innerFace(piece.from, piece.to, piece.low, piece.high, textureOr("inside", "wall"), RowHeight - tall,
                    RowHeight);
            }
        }

        if (in <= 0.0)
        {
            return;
        }

        const std::vector<std::array<double, 3>> tops = ruinTops(pieces, cuts);
        const std::string &capTexture = textureOr("wall_top", "trim");
        const Point2 &left = m_part.outline[wall];
        const Point2 &right = m_part.outline[(wall + 1) % m_count];
        const std::array<double, 3> along = {(right[0] - left[0]) / length, (right[1] - left[1]) / length, 0.0};
        // The inner point over a place along the wall: at a corner the mitre's.
        const auto inside = [&](double place)
        {
            return onWall(wall, place < 0.5 ? innerStart : place > length - 0.5 ? innerEnd : place, in);
        };

        for (size_t index = 0; index < tops.size(); ++index)
        {
            const std::array<double, 3> &top = tops[index];

            // Where the wall is gone: the foundation's sill, or nothing.
            if (top[2] < m_floor + 0.5 && foundation <= 0.0)
            {
                continue;
            }

            surface(facing({at(onWall(wall, top[0]), top[2]), at(onWall(wall, top[1]), top[2]),
                at(inside(top[1]), top[2]), at(inside(top[0]), top[2])}, {0.0, 0.0, 1.0}), capTexture, m_nameEvent);

            for (const bool end : {false, true})
            {
                const double place = end ? top[1] : top[0];
                // Beside it: the next stretch of this wall, or at a corner the wall round it.
                const bool corner = place < 0.5 || place > length - 0.5;
                const double beside = corner ? ruinStandsAt(end ? (wall + 1) % m_count : previous, !end)
                    : end ? (index + 1 < tops.size() ? tops[index + 1][2] : m_floor)
                    : (index > 0 ? tops[index - 1][2] : m_floor);
                const double foot = std::max(beside, m_floor);

                if (top[2] > foot + 0.5)
                {
                    surface(facing({at(onWall(wall, place), foot), at(inside(place), foot),
                        at(inside(place), top[2]), at(onWall(wall, place), top[2])},
                        end ? along : std::array<double, 3>{-along[0], -along[1], 0.0}), texture("wall"),
                        m_nameEvent);
                }
            }
        }
    }

    // A square beam `width` thick from one point to another (a rafter, a ridge beam).
    void beam(const OutdoorModelPoint &from, const OutdoorModelPoint &to, double width, const std::string &textureName)
    {
        std::array<double, 3> axis = {to[0] - from[0], to[1] - from[1], to[2] - from[2]};
        const double length = std::sqrt(axis[0] * axis[0] + axis[1] * axis[1] + axis[2] * axis[2]);

        if (length < 1.0)
        {
            return;
        }

        axis = {axis[0] / length, axis[1] / length, axis[2] / length};
        std::array<double, 3> side = {axis[1], -axis[0], 0.0};
        const double sideLength = oy::hypot(side[0], side[1]);
        side = sideLength < 1.0e-6 ? std::array<double, 3>{1.0, 0.0, 0.0}
            : std::array<double, 3>{side[0] / sideLength, side[1] / sideLength, 0.0};
        const std::array<double, 3> up = {side[1] * axis[2] - side[2] * axis[1], side[2] * axis[0] - side[0] * axis[2],
            side[0] * axis[1] - side[1] * axis[0]};
        const double half = width * 0.5;
        const auto corner = [&](const OutdoorModelPoint &place, double s, double u)
        {
            return OutdoorModelPoint{place[0] + (side[0] * s + up[0] * u) * half,
                place[1] + (side[1] * s + up[1] * u) * half, place[2] + (side[2] * s + up[2] * u) * half};
        };
        const std::array<std::array<double, 2>, 4> around = {{{1.0, 1.0}, {-1.0, 1.0}, {-1.0, -1.0}, {1.0, -1.0}}};

        for (size_t index = 0; index < 4; ++index)
        {
            const std::array<double, 2> &a = around[index];
            const std::array<double, 2> &b = around[(index + 1) % 4];
            const std::array<double, 3> normal = {side[0] * (a[0] + b[0]) + up[0] * (a[1] + b[1]),
                side[1] * (a[0] + b[0]) + up[1] * (a[1] + b[1]), side[2] * (a[0] + b[0]) + up[2] * (a[1] + b[1])};
            surface(facing({corner(from, a[0], a[1]), corner(to, a[0], a[1]), corner(to, b[0], b[1]),
                corner(from, b[0], b[1])}, normal), textureName, m_nameEvent);
        }

        for (const bool end : {false, true})
        {
            const OutdoorModelPoint &place = end ? to : from;
            std::vector<OutdoorModelPoint> points;

            for (const std::array<double, 2> &a : around)
            {
                points.push_back(corner(place, a[0], a[1]));
            }

            surface(facing(points, end ? axis : std::array<double, 3>{-axis[0], -axis[1], -axis[2]}), textureName,
                m_nameEvent);
        }
    }

    // A ruin's roof: none, or bare rafters (`frame`): on a box's gable, hip or lean-to roof a ridge beam and pairs of
    // rafters from the eaves to it at both ends and every `every` between; on any other a rafter from each corner to
    // the tip.
    void raiseRuinRoof()
    {
        const OutdoorRuinPlan &ruin = m_part.ruin;
        const OutdoorRoofPlan &roof = m_part.roof;

        if (ruin.roof != "frame" || roof.form == "none" || roof.form == "flat" || roof.rise <= 0.0)
        {
            return;
        }

        const std::string &wood = textureOr("rafter", "trim");
        const double width = ruin.rafter;
        const double half = width * 0.5;
        const std::vector<Point2> outer = grown(m_topOutline, roof.eaves);
        const double low = m_foot + half;
        const double tip = m_foot + roof.rise - half;

        if (m_part.shape != "box" || (roof.form != "gable" && roof.form != "hip" && roof.form != "lean_to"))
        {
            Point2 middle = {0.0, 0.0};

            for (const Point2 &point : outer)
            {
                middle = {middle[0] + point[0] / outer.size(), middle[1] + point[1] / outer.size()};
            }

            for (const Point2 &point : outer)
            {
                beam(at(point, low), at(middle, tip), width, wood);
            }

            return;
        }

        const double first = lengthOf(m_topOutline[0], m_topOutline[1]);
        const double second = lengthOf(m_topOutline[1], m_topOutline[2]);
        const bool alongFirst = roof.along == 'x' || (roof.along != 'y' && first >= second);
        size_t start = alongFirst ? 0 : 1;

        if (roof.form == "lean_to")
        {
            start = static_cast<size_t>(roof.along - '0') % 4;
        }

        const Point2 &a = outer[start];
        const Point2 &b = outer[(start + 1) % 4];
        const Point2 &c = outer[(start + 2) % 4];
        const Point2 &d = outer[(start + 3) % 4];
        const double ridgeLength = std::max(lengthOf(a, b), 1.0);
        // Rafters along the ridge: at both ends (half a rafter in) and every `every` between.
        std::vector<double> places = {half};
        const int between = ruin.every > 0.0 ? static_cast<int>(std::floor((ridgeLength - width) / ruin.every)) : 0;

        for (int index = 1; index <= between; ++index)
        {
            const double place = half + (ridgeLength - width) * index / (between + 1);
            places.push_back(place);
        }

        places.push_back(ridgeLength - half);
        const auto onSide = [&](const Point2 &from, const Point2 &to, double along)
        {
            return Point2{from[0] + (to[0] - from[0]) * along / ridgeLength,
                from[1] + (to[1] - from[1]) * along / ridgeLength};
        };

        if (roof.form == "lean_to")
        {
            // From the low eaves (a to b) up to the high wall's (d to c).
            for (const double place : places)
            {
                beam(at(onSide(a, b, place), low), at(onSide(d, c, place), tip), width, wood);
            }

            return;
        }

        const auto onRidge = [&](double along)
        {
            return Point2{(a[0] + d[0]) * 0.5 + (b[0] - a[0]) * along / ridgeLength,
                (a[1] + d[1]) * 0.5 + (b[1] - a[1]) * along / ridgeLength};
        };
        const double span = lengthOf(b, c);
        const double run = roof.form == "gable" ? 0.0
            : std::min(roof.hipRun > 0.0 ? roof.hipRun : span * 0.5, ridgeLength * 0.5);

        // Each rafter ends against the ridge beam's side; the beam stands half a rafter past the end ones, so no
        // two faces lie in one plane.
        const double spanLength = std::max(lengthOf(a, d), 1.0);
        const Point2 across = {(d[0] - a[0]) / spanLength, (d[1] - a[1]) / spanLength};

        for (const double place : places)
        {
            const Point2 ridge = onRidge(std::clamp(place, run, ridgeLength - run));
            beam(at(onSide(a, b, place), low), at({ridge[0] - across[0] * half, ridge[1] - across[1] * half}, tip),
                width, wood);
            beam(at(onSide(d, c, place), low), at({ridge[0] + across[0] * half, ridge[1] + across[1] * half}, tip),
                width, wood);
        }

        beam(at(onRidge(std::max(run, 0.0) - half), tip + half), at(onRidge(ridgeLength - std::max(run, 0.0) + half),
            tip + half), width, wood);
    }

    // ---- Cutting kept faces: doors in the roof, a stair ----

    // A wall's frame: its foot's left end, the way along it, the way in.
    struct WallFrame
    {
        Point2 origin = {0.0, 0.0};
        Point2 along = {1.0, 0.0};
        Point2 in = {0.0, 1.0};
        double length = 0.0;
    };

    WallFrame frameOf(size_t wall) const
    {
        WallFrame frame;
        const Point2 &left = m_part.outline[wall];
        const Point2 &right = m_part.outline[(wall + 1) % m_count];
        frame.length = std::max(lengthOf(left, right), 1.0e-9);
        frame.origin = left;
        frame.along = {(right[0] - left[0]) / frame.length, (right[1] - left[1]) / frame.length};
        frame.in = {-frame.along[1], frame.along[0]};
        return frame;
    }

    static OutdoorModelPoint inFrame(const WallFrame &frame, double along, double in, double z)
    {
        return {frame.origin[0] + frame.along[0] * along + frame.in[0] * in,
            frame.origin[1] + frame.along[1] * along + frame.in[1] * in, z};
    }

    // A box in a wall's frame cut out of faces: from < along < to, in < depth, z < top.
    struct Cut
    {
        size_t wall = 0;
        double from = 0.0;
        double to = 0.0;
        double depth = 0.0;
        double top = 0.0;
    };

    // The part of a convex face where a . p <= limit.
    static std::vector<OutdoorModelPoint> keptBy(const std::vector<OutdoorModelPoint> &points,
        const std::array<double, 3> &a, double limit)
    {
        std::vector<OutdoorModelPoint> result;

        for (size_t index = 0; index < points.size(); ++index)
        {
            const OutdoorModelPoint &from = points[index];
            const OutdoorModelPoint &to = points[(index + 1) % points.size()];
            const double fromSide = a[0] * from[0] + a[1] * from[1] + a[2] * from[2] - limit;
            const double toSide = a[0] * to[0] + a[1] * to[1] + a[2] * to[2] - limit;

            if (fromSide <= 1.0e-6)
            {
                result.push_back(from);
            }

            if ((fromSide < -1.0e-6 && toSide > 1.0e-6) || (fromSide > 1.0e-6 && toSide < -1.0e-6))
            {
                const double share = fromSide / (fromSide - toSide);
                result.push_back({from[0] + (to[0] - from[0]) * share, from[1] + (to[1] - from[1]) * share,
                    from[2] + (to[2] - from[2]) * share});
            }
        }

        return result;
    }

    static double areaOf(const std::vector<OutdoorModelPoint> &points)
    {
        std::array<double, 3> sum = {0.0, 0.0, 0.0};

        for (size_t index = 1; index + 1 < points.size(); ++index)
        {
            const OutdoorModelPoint &a = points[0];
            const OutdoorModelPoint &b = points[index];
            const OutdoorModelPoint &c = points[index + 1];
            const std::array<double, 3> u = {b[0] - a[0], b[1] - a[1], b[2] - a[2]};
            const std::array<double, 3> v = {c[0] - a[0], c[1] - a[1], c[2] - a[2]};
            sum = {sum[0] + u[1] * v[2] - u[2] * v[1], sum[1] + u[2] * v[0] - u[0] * v[2],
                sum[2] + u[0] * v[1] - u[1] * v[0]};
        }

        return 0.5 * std::sqrt(sum[0] * sum[0] + sum[1] * sum[1] + sum[2] * sum[2]);
    }

    // The pieces of a face outside a cut, each convex; the face itself when the cut misses it.
    std::vector<std::vector<OutdoorModelPoint>> outsideOf(const std::vector<OutdoorModelPoint> &points,
        const Cut &cut) const
    {
        const WallFrame frame = frameOf(cut.wall);
        const double originAlong = frame.along[0] * frame.origin[0] + frame.along[1] * frame.origin[1];
        const double originIn = frame.in[0] * frame.origin[0] + frame.in[1] * frame.origin[1];
        // The box's sides as "outside": a . p >= limit, written as -a . p <= -limit for keptBy.
        const std::array<std::pair<std::array<double, 3>, double>, 4> sides = {{
            {{-frame.along[0], -frame.along[1], 0.0}, -(originAlong + cut.from)},
            {{frame.along[0], frame.along[1], 0.0}, originAlong + cut.to},
            {{frame.in[0], frame.in[1], 0.0}, originIn + cut.depth},
            {{0.0, 0.0, 1.0}, cut.top}}};
        std::vector<std::vector<OutdoorModelPoint>> pieces;
        std::vector<OutdoorModelPoint> rest = points;

        for (const std::pair<std::array<double, 3>, double> &side : sides)
        {
            // Outside this side: a . p >= limit.
            const std::array<double, 3> &a = side.first;
            const std::vector<OutdoorModelPoint> outside = keptBy(rest, {-a[0], -a[1], -a[2]}, -side.second);

            if (outside.size() == rest.size() && areaOf(outside) >= areaOf(rest) - 0.5 && pieces.empty())
            {
                // Wholly outside the box: untouched.
                return {points};
            }

            if (outside.size() >= 3 && areaOf(outside) > 1.0)
            {
                pieces.push_back(outside);
            }

            rest = keptBy(rest, a, side.second);

            if (rest.size() < 3 || areaOf(rest) < 16.0)
            {
                // What lay in the box is a sliver along its side (a face that only touches it): untouched.
                return {points};
            }
        }

        return pieces;
    }

    // The texels of a point on a kept face, carried over from its corners (they are an affine map on its plane).
    static std::array<double, 2> texelAt(const Captured &face, const OutdoorModelPoint &point)
    {
        size_t best = 1;
        double bestArea = -1.0;
        const std::vector<OutdoorModelPoint> &corners = face.points;

        for (size_t index = 1; index + 1 < corners.size(); ++index)
        {
            const double area = areaOf({corners[0], corners[index], corners[index + 1]});

            if (area > bestArea)
            {
                bestArea = area;
                best = index;
            }
        }

        const OutdoorModelPoint &p0 = corners[0];
        const OutdoorModelPoint &p1 = corners[best];
        const OutdoorModelPoint &p2 = corners[best + 1];
        const std::array<double, 3> e1 = {p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]};
        const std::array<double, 3> e2 = {p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]};
        const std::array<double, 3> q = {point[0] - p0[0], point[1] - p0[1], point[2] - p0[2]};
        const auto dot = [](const std::array<double, 3> &u, const std::array<double, 3> &v)
        {
            return u[0] * v[0] + u[1] * v[1] + u[2] * v[2];
        };
        const double a11 = dot(e1, e1);
        const double a12 = dot(e1, e2);
        const double a22 = dot(e2, e2);
        const double b1 = dot(e1, q);
        const double b2 = dot(e2, q);
        const double det = std::max(a11 * a22 - a12 * a12, 1.0e-12);
        const double alpha = (b1 * a22 - b2 * a12) / det;
        const double beta = (b2 * a11 - b1 * a12) / det;
        const std::array<double, 2> &t0 = face.texels[0];
        const std::array<double, 2> &t1 = face.texels[best];
        const std::array<double, 2> &t2 = face.texels[best + 1];
        return {t0[0] + alpha * (t1[0] - t0[0]) + beta * (t2[0] - t0[0]),
            t0[1] + alpha * (t1[1] - t0[1]) + beta * (t2[1] - t0[1])};
    }

    // The highest kept face that looks up over a point: the roof's (or the terraces') height there.
    double keptHeightAt(const Point2 &point) const
    {
        double best = -1.0e18;

        for (const Captured &kept : m_captured)
        {
            const std::vector<OutdoorModelPoint> &p = kept.points;
            std::array<double, 3> normal = {0.0, 0.0, 0.0};

            for (size_t index = 0; index < p.size(); ++index)
            {
                const OutdoorModelPoint &a = p[index];
                const OutdoorModelPoint &b = p[(index + 1) % p.size()];
                normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
                normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
                normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
            }

            if (p.size() < 3 || normal[2] <= 1.0e-6 * std::fabs(normal[0]) + 1.0e-6 * std::fabs(normal[1]) + 1.0e-9)
            {
                continue;
            }

            bool inside = true;

            for (size_t index = 0; index < p.size() && inside; ++index)
            {
                const OutdoorModelPoint &a = p[index];
                const OutdoorModelPoint &b = p[(index + 1) % p.size()];
                inside = (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0]) >= -1.0e-6;
            }

            if (inside)
            {
                const double z = p[0][2] - (normal[0] * (point[0] - p[0][0]) + normal[1] * (point[1] - p[0][1]))
                    / normal[2];
                best = std::max(best, z);
            }
        }

        return best;
    }

    // Puts the kept faces into the model, cut by the doors in the roof and the stair, and adds what fills the cuts.
    void finishCaptured(double terraceTop)
    {
        std::vector<Cut> cuts;
        // The doors in the roof: each stands upright on its wall's foot up to its height, in a box that reaches in
        // to where the roof is that high, with cheeks and a level top over its head.
        struct Notch
        {
            OutdoorDoorPlan *pDoor = nullptr;
            Cut cut;
            // The roof's height on the wall's line at the door's two sides, before the cut.
            std::array<double, 2> low = {0.0, 0.0};
        };
        std::vector<Notch> notches;

        for (OutdoorDoorPlan &door : m_building.doors)
        {
            if (!notchDoor(door))
            {
                continue;
            }

            const std::vector<double> edges = bayEdgesOf(m_part, door.wall, false);
            const WallFrame frame = frameOf(door.wall);
            const double from = edges[door.bay];
            const double to = edges[door.bay + 1];
            const double top = m_floor + (m_part.doorHeight > 0.0 ? m_part.doorHeight : RowHeight);
            const auto heightIn = [&](double in)
            {
                const OutdoorModelPoint point = inFrame(frame, (from + to) * 0.5, in, 0.0);
                return keptHeightAt({point[0], point[1]});
            };
            double depth = 0.0;

            if (heightIn(0.01) < top)
            {
                double low = 0.0;
                double high = 8.0;

                while (high < 8192.0 && heightIn(high) < top)
                {
                    low = high;
                    high += 8.0;
                }

                for (int round = 0; round < 24; ++round)
                {
                    const double middle = (low + high) * 0.5;
                    (heightIn(middle) < top ? low : high) = middle;
                }

                depth = high;
            }

            std::array<double, 2> low = {m_top, m_top};

            for (size_t end = 0; end < 2; ++end)
            {
                const OutdoorModelPoint point = inFrame(frame, end == 0 ? from : to, 0.01, 0.0);
                low[end] = std::clamp(keptHeightAt({point[0], point[1]}), m_floor, top);
            }

            notches.push_back({&door, {door.wall, from, to, depth, top}, low});
            cuts.push_back(notches.back().cut);
            // Batch O-H: a door in a gable end (the roof over the door's middle higher than the door: no notch into
            // the roof) still takes the gable's face off the door (Erathia's A-frame: they lay on each other).
            cuts.back().depth = std::max(cuts.back().depth, 0.5);
        }

        // The stair: its span with its cheeks, from the foot in to where the part's top begins.
        const OutdoorStairPlan &stair = m_part.stair;
        std::vector<std::array<double, 2>> profile;
        double stairDepth = 0.0;

        if (stair.given)
        {
            profile = stairProfile(terraceTop);
            stairDepth = profile.back()[0];
            cuts.push_back({stair.wall, stair.along - stair.width * 0.5 - stair.cheek,
                stair.along + stair.width * 0.5 + stair.cheek, stairDepth + 0.01, terraceTop + 0.5});
        }

        // The kept faces, cut; door faces made while kept get their place in the model.
        std::vector<int> placed(m_captured.size(), -1);

        for (size_t index = 0; index < m_captured.size(); ++index)
        {
            const Captured &kept = m_captured[index];
            std::vector<std::vector<OutdoorModelPoint>> pieces = {kept.points};

            for (const Cut &cut : cuts)
            {
                std::vector<std::vector<OutdoorModelPoint>> next;

                for (const std::vector<OutdoorModelPoint> &piece : pieces)
                {
                    for (const std::vector<OutdoorModelPoint> &outside : outsideOf(piece, cut))
                    {
                        next.push_back(outside);
                    }
                }

                pieces = next;
            }

            for (const std::vector<OutdoorModelPoint> &piece : pieces)
            {
                int made = -1;

                if (piece == kept.points)
                {
                    made = kept.given ? m_builder.addFace(piece, kept.texture, kept.texels, kept.event)
                        : m_builder.addSurface(piece, kept.texture, kept.event);
                }
                else if (kept.given)
                {
                    std::vector<std::array<double, 2>> texels;

                    for (const OutdoorModelPoint &point : piece)
                    {
                        texels.push_back(texelAt(kept, point));
                    }

                    made = m_builder.addFace(piece, kept.texture, texels, kept.event);
                }
                else
                {
                    made = m_builder.addSurface(piece, kept.texture, kept.event);
                }

                if (made >= 0 && kept.through)
                {
                    m_builder.letThrough(made);
                }

                placed[index] = placed[index] < 0 ? made : placed[index];
            }
        }

        for (OutdoorDoorPlan &door : m_building.doors)
        {
            if (door.part == m_partIndex && !notchDoor(door) && door.face >= 0
                && static_cast<size_t>(door.face) < placed.size())
            {
                door.face = placed[static_cast<size_t>(door.face)];
            }
        }

        m_captured.clear();

        for (const Notch &notch : notches)
        {
            raiseNotch(*notch.pDoor, notch.cut, notch.low);
        }

        if (stair.given)
        {
            raiseStair(profile, terraceTop);
        }
    }

    // A door cut into the roof: its face upright on the wall's foot, the cheeks from the roof up to its head and the
    // level top over it back to where the roof is that high.
    void raiseNotch(OutdoorDoorPlan &door, const Cut &cut, const std::array<double, 2> &low)
    {
        const WallFrame frame = frameOf(cut.wall);
        const std::string &doorTexture = door.texture.empty() ? texture("door") : door.texture;
        const double width = cut.to - cut.from;
        const uint16_t event = door.event != 0 ? door.event : m_nameEvent;
        // Two leaves (the second mirrored) or an arched head as on a door under the walls' top (A5's castle gates on
        // X6, `door_height` 384: one plain face before).
        const int made = door.leaves > 1 || !door.arch.empty()
            ? dressedPiece(cut.wall, cut.from, cut.to, m_floor, cut.top, doorTexture, width, 0.0, event, door.arch,
                door.archSides, door.leaves, RowHeight, false, door.pictureWidth)
            : m_builder.addFace({inFrame(frame, cut.from, 0.0, m_floor), inFrame(frame, cut.to, 0.0, m_floor),
                inFrame(frame, cut.to, 0.0, cut.top), inFrame(frame, cut.from, 0.0, cut.top)}, doorTexture,
                {{0.0, RowHeight}, {width, RowHeight}, {width, 0.0}, {0.0, 0.0}}, event);
        const OutdoorModelPoint middle = inFrame(frame, (cut.from + cut.to) * 0.5, 0.0, m_floor);
        door.face = made;
        door.x = middle[0];
        door.y = middle[1];
        door.z = m_floor;
        door.normalX = -frame.in[0];
        door.normalY = -frame.in[1];

        if (cut.depth < 0.5)
        {
            return;
        }

        const std::string &wallTexture = textureOr("cheek", "roof");

        for (const bool end : {false, true})
        {
            const double place = end ? cut.to : cut.from;
            std::vector<OutdoorModelPoint> points = {inFrame(frame, place, 0.0, low[end ? 1 : 0]),
                inFrame(frame, place, cut.depth, cut.top), inFrame(frame, place, 0.0, cut.top)};
            m_builder.addSurface(facing(points, end ? std::array<double, 3>{frame.along[0], frame.along[1], 0.0}
                : std::array<double, 3>{-frame.along[0], -frame.along[1], 0.0}), wallTexture, m_nameEvent);
        }

        m_builder.addSurface(facing({inFrame(frame, cut.from, 0.0, cut.top), inFrame(frame, cut.to, 0.0, cut.top),
            inFrame(frame, cut.to, cut.depth, cut.top), inFrame(frame, cut.from, cut.depth, cut.top)},
            {0.0, 0.0, 1.0}), textureOr("cheek", "roof"), m_nameEvent);
    }

    bool uprightStair() const
    {
        return m_part.steps.empty() && insetOf(m_part.stair.wall, m_top) <= 0.0;
    }

    // The height of the part's mass in from the stair's wall: [in, z] from the foot (0, floor) up the batter and
    // the terraces to where the top begins (the last point).
    std::vector<std::array<double, 2>> stairProfile(double terraceTop) const
    {
        const size_t wall = m_part.stair.wall;
        std::vector<std::array<double, 2>> points = {{0.0, m_floor}};
        const double knee = m_floor + (m_part.batterHeight > 0.0 ? m_part.batterHeight : m_part.wallHeight);
        const double inset = insetOf(wall, m_top);

        if (inset > 0.0)
        {
            points.push_back({inset, knee});
        }

        if (knee < m_top - 0.5 || inset <= 0.0)
        {
            points.push_back({inset, m_top});
        }

        double in = inset;
        double z = m_top;

        for (const std::array<double, 2> &step : m_part.steps)
        {
            in += step[0];
            points.push_back({in, z});
            z += step[1];
            points.push_back({in, z});
        }

        points.back()[1] = terraceTop;

        // An upright part: the flight runs `run` in under the flat roof, the mass at full height from the wall in.
        if (uprightStair())
        {
            points.push_back({m_part.stair.run, terraceTop});
        }

        return points;
    }

    // The stair: its steps (or a ramp) over its width, the cheeks each side with their tops, ends and faces, and the
    // part's mass closed where the cheeks cut it.
    void raiseStair(const std::vector<std::array<double, 2>> &profile, double top)
    {
        const OutdoorStairPlan &stair = m_part.stair;
        const WallFrame frame = frameOf(stair.wall);
        const double depth = profile.back()[0];
        const double run = stair.run > 0.0 ? stair.run : depth;
        const double start = depth - run;
        const double rise = top - m_floor;
        const int count = stair.ramp ? 1 : std::max(1, static_cast<int>(std::lround(rise / stair.rise)));
        const double stepRise = rise / count;
        const double tread = run / count;
        const double from = stair.along - stair.width * 0.5;
        const double to = stair.along + stair.width * 0.5;
        const std::string &stepTexture = textureOr("stair", "roof");
        const std::string &cheekTexture = textureOr("cheek", "wall");
        const std::array<double, 3> out = {-frame.in[0], -frame.in[1], 0.0};
        const std::array<double, 3> along = {frame.along[0], frame.along[1], 0.0};
        const std::array<double, 3> back = {-along[0], -along[1], 0.0};

        if (stair.ramp)
        {
            m_builder.addSurface(facing({inFrame(frame, from, start, m_floor), inFrame(frame, to, start, m_floor),
                inFrame(frame, to, depth, top), inFrame(frame, from, depth, top)}, {0.0, 0.0, 1.0}), stepTexture,
                m_nameEvent);
        }
        else
        {
            for (int index = 0; index < count; ++index)
            {
                const double in = start + tread * index;
                const double low = m_floor + stepRise * index;
                const double high = low + stepRise;
                const int riser = m_builder.addSurface(facing({inFrame(frame, from, in, low), inFrame(frame, to, in, low),
                    inFrame(frame, to, in, high), inFrame(frame, from, in, high)}, out), stepTexture, m_nameEvent);

                if (riser >= 0)
                {
                    m_builder.letThrough(riser);
                }

                m_builder.addSurface(facing({inFrame(frame, from, in, high), inFrame(frame, to, in, high),
                    inFrame(frame, to, in + tread, high), inFrame(frame, from, in + tread, high)}, {0.0, 0.0, 1.0}),
                    stepTexture, m_nameEvent);
            }
        }

        if (stair.cheek <= 0.0)
        {
            return;
        }

        // The flight's nosing line and the cheeks' top over it.
        const double nosing = stair.ramp ? 0.0 : stepRise;
        // The cheeks' top over the nosing line, level with the part's top where it would stand over it.
        const auto cheekTop = [&](double in)
        {
            return std::min(m_floor + (in - start) * rise / run + nosing + stair.cheekHeight, top);
        };
        const double level = std::clamp(start + (top - m_floor - nosing - stair.cheekHeight) * run / rise, start, depth);
        const double foot = groundFoot();

        for (const bool right : {false, true})
        {
            const double inner = right ? to : from;
            const double outer = right ? to + stair.cheek : from - stair.cheek;
            const std::array<double, 3> toFlight = right ? back : along;
            const std::array<double, 3> away = right ? along : back;
            // Its top (sloping, then level with the part's top), its foot's end, its face to the flight from a line
            // under the treads; an end over the top where it stands higher.
            for (const std::array<double, 2> &span : {std::array<double, 2>{start, level},
                     std::array<double, 2>{level, depth}})
            {
                if (span[1] - span[0] < 0.5)
                {
                    continue;
                }

                m_builder.addSurface(facing({inFrame(frame, outer, span[0], cheekTop(span[0])),
                    inFrame(frame, inner, span[0], cheekTop(span[0])), inFrame(frame, inner, span[1], cheekTop(span[1])),
                    inFrame(frame, outer, span[1], cheekTop(span[1]))}, {0.0, 0.0, 1.0}), cheekTexture, m_nameEvent);
                const double under = m_floor + (span[1] - start) * (rise - stepRise) / run;
                m_builder.addSurface(facing({inFrame(frame, inner, span[0], m_floor + (span[0] - start) * (rise
                    - stepRise) / run), inFrame(frame, inner, span[1], under), inFrame(frame, inner, span[1],
                    cheekTop(span[1])), inFrame(frame, inner, span[0], cheekTop(span[0]))}, toFlight), cheekTexture,
                    m_nameEvent);
            }

            m_builder.addSurface(facing({inFrame(frame, outer, start, foot), inFrame(frame, inner, start, foot),
                inFrame(frame, inner, start, cheekTop(start)), inFrame(frame, outer, start, cheekTop(start))}, out),
                cheekTexture, m_nameEvent);

            if (cheekTop(depth) > top + 0.5)
            {
                m_builder.addSurface(facing({inFrame(frame, outer, depth, top), inFrame(frame, inner, depth, top),
                    inFrame(frame, inner, depth, cheekTop(depth)), inFrame(frame, outer, depth, cheekTop(depth))},
                    {frame.in[0], frame.in[1], 0.0}), cheekTexture, m_nameEvent);
            }

            // Its outer face where it stands over the part's mass; the mass's cut face where that stands higher.
            std::vector<std::array<double, 2>> mass;

            if (start < 0.0)
            {
                mass.push_back({start, foot});
                mass.push_back({0.0, foot});
            }

            for (const std::array<double, 2> &point : profile)
            {
                mass.push_back(point);
            }

            for (size_t index = 0; index + 1 < mass.size(); ++index)
            {
                double a = std::max(mass[index][0], start);
                double b = std::min(mass[index + 1][0], depth);

                if (b - a < 0.5)
                {
                    continue;
                }

                const auto massAt = [&](double in)
                {
                    const double span = mass[index + 1][0] - mass[index][0];
                    return mass[index][1] + (mass[index + 1][1] - mass[index][1]) * (in - mass[index][0]) / span;
                };
                // Cut where the cheek's top turns level and where it crosses the mass's line.
                std::vector<double> places = {a};
                std::vector<std::array<double, 2>> spans = {{a, b}};

                if (level > a + 0.5 && level < b - 0.5)
                {
                    spans = {{a, level}, {level, b}};
                }

                for (const std::array<double, 2> &span : spans)
                {
                    const double ea = cheekTop(span[0]) - massAt(span[0]);
                    const double eb = cheekTop(span[1]) - massAt(span[1]);

                    if ((ea > 0.5 && eb < -0.5) || (ea < -0.5 && eb > 0.5))
                    {
                        places.push_back(span[0] + (span[1] - span[0]) * ea / (ea - eb));
                    }

                    places.push_back(span[1]);
                }

                for (size_t piece = 0; piece + 1 < places.size(); ++piece)
                {
                    const double p = places[piece];
                    const double q = places[piece + 1];
                    const double middle = (p + q) * 0.5;
                    const bool cheekHigher = cheekTop(middle) > massAt(middle);
                    std::vector<OutdoorModelPoint> points = {inFrame(frame, outer, p, massAt(p)),
                        inFrame(frame, outer, q, massAt(q)), inFrame(frame, outer, q, cheekTop(q)),
                        inFrame(frame, outer, p, cheekTop(p))};

                    if (areaOf(points) > 4.0)
                    {
                        m_builder.addSurface(facing(points, cheekHigher ? away : toFlight),
                            cheekHigher ? cheekTexture : texture("wall"), m_nameEvent);
                    }
                }
            }
        }
    }

    // The hidden slopes over the walls the party climbs: from the wall's foot on the floor in front of it to the
    // top, `climb` in, as the shipped maps' flights (core/OutdoorModel `addStepSlope`).
    void raiseClimbs()
    {
        if (m_part.climb <= 0.0)
        {
            return;
        }

        const std::vector<Point2> inner = grown(m_part.outline, -m_part.climb);

        for (size_t wall = 0; wall < m_count && wall < m_part.climbFrom.size(); ++wall)
        {
            if (!m_part.climbFrom[wall])
            {
                continue;
            }

            const size_t next = (wall + 1) % m_count;
            const double foot = m_building.base + *m_part.climbFrom[wall];
            m_builder.addStepSlope({at(m_part.outline[wall], foot), at(m_part.outline[next], foot),
                at(inner[next], m_top), at(inner[wall], m_top)}, texture("roof"), m_nameEvent);
        }
    }

    // A role's texture, or another role's where the part names none for it.
    const std::string &textureOr(const std::string &role, const std::string &fallback) const
    {
        return m_part.textures.contains(role) ? m_part.textures.at(role) : texture(fallback);
    }

    // D-170: the height a level top over `outline` stands at so that it does not lie on the land (outdoorClearOfLand,
    // never sunk: a porch's slab is walked on, a ruin's course is its footing).
    double clearOfLand(const std::vector<Point2> &outline, double top) const
    {
        return m_pLand == nullptr ? top : outdoorClearOfLand(*m_pLand, outline, top);
    }

    // The foot of what stands on the ground: down into it by the foundation, as the walls' base course.
    double groundFoot() const
    {
        return m_part.bottom == 0.0 ? m_floor - m_building.foundation : m_floor;
    }

    // Batch O-F: a round column `width` across about a middle, from `low` to `high`, on a base and under a capital
    // a third wider and `block` high (Kriegspire's PT07: 64 square blocks 32 high round shafts of eight sides 48
    // across).
    void roundColumn(size_t wall, const Point2 &middle, double width, double low, double high, double block)
    {
        const std::string &shaft = textureOr("post", "trim");
        const std::string &blockTexture = textureOr("capital", "trim");
        const double wide = width * 4.0 / 3.0;
        // Squared to the wall.
        const Point2 &left = m_part.outline[wall];
        const Point2 &right = m_part.outline[(wall + 1) % m_count];
        const double length = std::max(lengthOf(left, right), 1.0e-9);
        const Point2 u = {(right[0] - left[0]) / length, (right[1] - left[1]) / length};
        const Point2 v = {-u[1], u[0]};
        const auto square = [&middle, &u, &v](double size)
        {
            const double h = size * 0.5;
            return std::vector<Point2>{{middle[0] - u[0] * h - v[0] * h, middle[1] - u[1] * h - v[1] * h},
                {middle[0] + u[0] * h - v[0] * h, middle[1] + u[1] * h - v[1] * h},
                {middle[0] + u[0] * h + v[0] * h, middle[1] + u[1] * h + v[1] * h},
                {middle[0] - u[0] * h + v[0] * h, middle[1] - u[1] * h + v[1] * h}};
        };
        std::vector<Point2> ring;
        const double first = oy::atan2(u[1], u[0]);

        for (int side = 0; side < 8; ++side)
        {
            const double angle = first + (side + 0.5) * Pi / 4.0;
            const double radius = width * 0.5 / oy::cos(Pi / 8.0);
            ring.push_back({middle[0] + radius * oy::cos(angle), middle[1] + radius * oy::sin(angle)});
        }

        if (block > 0.0 && high - low > block * 3.0)
        {
            m_builder.addPrism(square(wide), low, low + block, blockTexture, blockTexture, "", m_nameEvent);
            m_builder.addPrism(ring, low + block, high - block, shaft, "", "", m_nameEvent);
            m_builder.addPrism(square(wide), high - block, high, blockTexture, "", blockTexture, m_nameEvent);
            return;
        }

        m_builder.addPrism(ring, low, high, shaft, "", "", m_nameEvent);
    }

    // A square post `width` wide on a wall's line: `along` its first side, reaching `in` its second.
    void post(size_t wall, double from, double width, double low, double high, const std::string &textureName)
    {
        if (m_part.roundPosts)
        {
            // `posts_shape: round` on an open part: a round column in the square's place.
            const double length = std::max(lengthOf(m_part.outline[wall], m_part.outline[(wall + 1) % m_count]),
                1.0e-9);
            roundColumn(wall, onWall(wall, std::min(from + width * 0.5, length), width * 0.5), width, low, high,
                std::min(32.0, (high - low) / 6.0));
            return;
        }

        const std::vector<Point2> outline = {onWall(wall, from, 0.0), onWall(wall, from + width, 0.0),
            onWall(wall, from + width, width), onWall(wall, from, width)};

        if (m_part.textures.contains("post"))
        {
            m_builder.addPrism(outline, low, high, textureName, textureName, "", m_nameEvent);
            return;
        }

        // The trim (a band: it repeats along its width only) stands on its end up the post, so that it runs along
        // the post instead of repeating up it (the texture-fit check, TEXTURE_FIT.md).
        for (size_t side = 0; side < outline.size(); ++side)
        {
            const Point2 &a = outline[side];
            const Point2 &b = outline[(side + 1) % outline.size()];
            const double across = lengthOf(a, b);
            m_builder.addFace({{a[0], a[1], low}, {b[0], b[1], low}, {b[0], b[1], high}, {a[0], a[1], high}},
                textureName, {{0.0, 0.0}, {0.0, across}, {high - low, across}, {high - low, 0.0}}, m_nameEvent);
        }

        std::vector<OutdoorModelPoint> top;

        for (const Point2 &corner : outline)
        {
            top.push_back({corner[0], corner[1], high});
        }

        m_builder.addSurface(top, textureName, m_nameEvent);
    }

    // An open part (`posts`): a post at each corner and every `post_every` along the walls, low walls between them
    // where asked, and a ceiling under the roof (the roof's faces look up only).
    void raiseOpen()
    {
        if (m_part.posts <= 0.0)
        {
            return;
        }

        const double width = m_part.posts;
        const std::string &postTexture = textureOr("post", "trim");

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            const double length = lengthOf(m_part.outline[wall], m_part.outline[(wall + 1) % m_count]);
            // The posts of this wall: one at its left corner and the ones between; the right corner is the next
            // wall's.
            const int gaps = m_part.postEvery > 0.0 ? std::max(1, static_cast<int>(std::ceil(length
                / m_part.postEvery))) : 1;
            std::vector<double> starts = {0.0};

            for (int gap = 1; gap < gaps; ++gap)
            {
                starts.push_back(length * gap / gaps - width * 0.5);
            }

            // `post_walls`: a wall without posts has none along it; its corners keep the posts of a wall beside it
            // that has them.
            const size_t previous = (wall + m_count - 1) % m_count;
            const bool posted = wall >= m_part.postWalls.size() || m_part.postWalls[wall];
            const bool postedBefore = previous >= m_part.postWalls.size() || m_part.postWalls[previous];

            for (size_t index = 0; index < starts.size(); ++index)
            {
                if (posted || (index == 0 && postedBefore))
                {
                    post(wall, starts[index], width, groundFoot(), m_top, postTexture);
                }
            }

            if (m_part.sill > 0.0 && wall < m_part.sillWalls.size() && m_part.sillWalls[wall])
            {
                // Between each two posts, thinner than they by 2 on each side so no face lies on a post's; the last
                // ends at the next wall's corner post (run on to the corner, its end lay on that post's face).
                starts.push_back(length - width);
                const double thick = std::max(4.0, width - 4.0);

                for (size_t index = 0; index + 1 < starts.size(); ++index)
                {
                    const double from = starts[index] + width;
                    const double to = starts[index + 1];

                    if (to - from < 1.0)
                    {
                        continue;
                    }

                    m_builder.addPrism({onWall(wall, from, 2.0), onWall(wall, to, 2.0), onWall(wall, to, 2.0 + thick),
                        onWall(wall, from, 2.0 + thick)}, groundFoot(), m_floor + m_part.sill,
                        textureOr("sill", "wall"), textureOr("sill", "trim"), "", m_nameEvent);
                }
            }
        }

        std::vector<OutdoorModelPoint> ceiling;

        for (size_t index = m_count; index-- > 0;)
        {
            ceiling.push_back(at(m_part.outline[index], m_top));
        }

        if (m_part.roof.form != "none")
        {
            surface(ceiling, texture("trim"), m_nameEvent);
        }
    }

    // The recesses: the wall's stretch stands back (raiseWall); here its two cheeks, the ceiling over it at the
    // walls' top, and posts at its front corners where asked.
    void raiseRecesses()
    {
        for (const OutdoorPorchPlan &porch : m_part.porches)
        {
            if (!porch.recess)
            {
                continue;
            }

            const std::vector<double> edges = bayEdgesOf(m_part, porch.wall, false);
            const double from = edges[porch.fromBay];
            const double to = edges[porch.toBay + 1];
            const double low = groundFoot();
            const std::string &wallTexture = texture("wall");
            const std::string &trim = texture("trim");
            const Point2 outerFrom = onWall(porch.wall, from);
            const Point2 innerFrom = onWall(porch.wall, from, porch.depth);
            const Point2 outerTo = onWall(porch.wall, to);
            const Point2 innerTo = onWall(porch.wall, to, porch.depth);

            if (from > 0.5)
            {
                // The cheek at the stretch's left end looks along the wall into the recess.
                surface({at(outerFrom, low), at(innerFrom, low), at(innerFrom, m_top),
                    at(outerFrom, m_top)}, wallTexture, m_nameEvent);
            }

            if (to < edges.back() - 0.5)
            {
                surface({at(innerTo, low), at(outerTo, low), at(outerTo, m_top), at(innerTo, m_top)},
                    wallTexture, m_nameEvent);
            }

            if (!porch.arch.empty())
            {
                raiseRecessArch(porch, from, to);
            }
            else
            {
                surface({at(innerFrom, m_top), at(innerTo, m_top), at(outerTo, m_top), at(outerFrom, m_top)},
                    trim, m_nameEvent);
            }

            if (porch.posts > 0.0)
            {
                post(porch.wall, from, porch.posts, low, m_top, textureOr("post", "trim"));
                post(porch.wall, to - porch.posts, porch.posts, low, m_top, textureOr("post", "trim"));
            }
        }
    }

    // Batch O-H: an arched recess's head: the wall over the arch on the front (each segment's spandrel up to the
    // walls' top), a soffit under each segment through the recess's depth, and the wall over it at the back.
    void raiseRecessArch(const OutdoorPorchPlan &porch, double from, double to)
    {
        const double span = to - from;
        const double top = porch.archHeight > 0.0 ? std::min(m_floor + porch.archHeight, m_top) : m_top;
        const std::vector<std::array<double, 2>> head = outdoorArchHead(span, top - m_floor, porch.arch,
            porch.archSides);
        const std::string &wallTexture = texture("wall");
        const std::string &soffit = textureOr("soffit", "trim");
        const Point2 outerMiddle = onWall(porch.wall, (from + to) * 0.5);
        const Point2 innerMiddle = onWall(porch.wall, (from + to) * 0.5, porch.depth);
        const std::array<double, 3> outward = {outerMiddle[0] - innerMiddle[0], outerMiddle[1] - innerMiddle[1], 0.0};
        // The arch's axis: the middle of the opening at the springing's height.
        const double spring = m_floor + head.front()[1];

        for (size_t segment = 0; segment + 1 < head.size(); ++segment)
        {
            const double a = from + span * 0.5 + head[segment][0];
            const double b = from + span * 0.5 + head[segment + 1][0];
            const double za = m_floor + head[segment][1];
            const double zb = m_floor + head[segment + 1][1];

            // The wall over the segment on the front, up to the walls' top (the back wall stands whole behind).
            if (m_top - std::min(za, zb) > 0.5)
            {
                surface(facing({at(onWall(porch.wall, a), za), at(onWall(porch.wall, b), zb),
                    at(onWall(porch.wall, b), m_top), at(onWall(porch.wall, a), m_top)}, outward), wallTexture,
                    m_nameEvent);
            }

            // The soffit through the depth, looking in toward the arch's axis.
            const Point2 segmentMiddle = onWall(porch.wall, (a + b) * 0.5);
            const Point2 axis = onWall(porch.wall, from + span * 0.5);
            surface(facing({at(onWall(porch.wall, a), za), at(onWall(porch.wall, b), zb),
                at(onWall(porch.wall, b, porch.depth), zb), at(onWall(porch.wall, a, porch.depth), za)},
                {axis[0] - segmentMiddle[0], axis[1] - segmentMiddle[1], spring - (za + zb) * 0.5}), soffit,
                m_nameEvent);
        }
    }

    // The porches that stand out from a wall: a sloping roof from the wall down to its front edge, with its
    // underside, front band and ends; posts at its front corners; a floor under it.
    void raisePorches()
    {
        for (const OutdoorPorchPlan &porch : m_part.porches)
        {
            if (porch.recess)
            {
                continue;
            }

            const std::vector<double> edges = bayEdgesOf(m_part, porch.wall, false);
            const double from = edges[porch.fromBay] - porch.overhang;
            const double to = edges[porch.toBay + 1] + porch.overhang;
            const double front = m_floor + porch.height;
            const double back = front + porch.rise;
            const double thick = porch.thickness;
            const Point2 wallFrom = onWall(porch.wall, from);
            const Point2 wallTo = onWall(porch.wall, to);
            const Point2 frontFrom = onWall(porch.wall, from, -porch.depth);
            const Point2 frontTo = onWall(porch.wall, to, -porch.depth);
            const std::string &roofTexture = textureOr("porch", "roof");
            const std::string &trim = texture("trim");

            if (porch.pediment > 0.0)
            {
                // A portico's gable: two slopes up to a ridge running out from the wall over the porch's middle, the
                // pediment's triangle over the band at the front.
                const double middle = (from + to) * 0.5;
                const Point2 wallMiddle = onWall(porch.wall, middle);
                const Point2 frontMiddle = onWall(porch.wall, middle, -porch.depth);
                const double eave = front + thick;
                const double ridge = eave + porch.pediment;
                const Point2 outward = {frontMiddle[0] - wallMiddle[0], frontMiddle[1] - wallMiddle[1]};
                const Point2 sideways = {frontTo[0] - frontFrom[0], frontTo[1] - frontFrom[1]};
                const double run = std::max(lengthOf(frontFrom, frontTo) * 0.5, 1.0);
                const double sideLength = std::max(oy::hypot(sideways[0], sideways[1]), 1.0e-9);

                for (const double way : {-1.0, 1.0})
                {
                    const Point2 &wallEnd = way < 0.0 ? wallFrom : wallTo;
                    const Point2 &frontEnd = way < 0.0 ? frontFrom : frontTo;
                    surface(facing({at(wallEnd, eave), at(frontEnd, eave), at(frontMiddle, ridge), at(wallMiddle, ridge)},
                        {way * sideways[0] / sideLength * porch.pediment, way * sideways[1] / sideLength
                        * porch.pediment, run}), roofTexture, m_nameEvent);
                }

                surface(facing({at(frontFrom, eave), at(frontTo, eave), at(frontMiddle, ridge)}, {outward[0],
                    outward[1], 0.0}), textureOr("pediment", "trim"), m_nameEvent);
            }
            else
            {
                surface({at(wallFrom, back + thick), at(frontFrom, front + thick), at(frontTo, front + thick),
                    at(wallTo, back + thick)}, roofTexture, m_nameEvent);
            }

            surface({at(wallTo, back), at(frontTo, front), at(frontFrom, front), at(wallFrom, back)}, trim,
                m_nameEvent);

            if (thick > 0.0)
            {
                surface({at(frontFrom, front), at(frontTo, front), at(frontTo, front + thick),
                    at(frontFrom, front + thick)}, trim, m_nameEvent);
                surface({at(wallFrom, back), at(frontFrom, front), at(frontFrom, front + thick),
                    at(wallFrom, back + thick)}, trim, m_nameEvent);
                surface({at(frontTo, front), at(wallTo, back), at(wallTo, back + thick),
                    at(frontTo, front + thick)}, trim, m_nameEvent);
            }

            // The slab's top: over the part's foot, or over the land under the building's plinth; and 4 over the
            // land under it where that rises to it beyond the plot (D-170: X3's temple, D3's Guild of Light).
            const double slab = clearOfLand({wallFrom, frontFrom, frontTo, wallTo},
                (porch.floorFromLand ? m_floor - m_building.plinth : m_floor) + porch.floor);

            if (porch.floor > 0.0)
            {
                m_builder.addPrism({wallFrom, frontFrom, frontTo, wallTo}, groundFoot(), slab,
                    textureOr("step", "trim"), textureOr("step", "trim"), "", m_nameEvent);
            }

            if (porch.posts > 0.0 && (porch.portico || porch.roundPosts))
            {
                // Round columns along the front under the band (a portico's `columns`, else the two corners): a
                // base and a capital a third wider than the shaft, 32 high or less.
                const double foot = porch.floor > 0.0 ? slab : groundFoot();
                const size_t count = std::max<size_t>(2, porch.portico ? porch.columns : 2);
                const double block = std::min(32.0, (front - foot) / 6.0);

                for (size_t row = 0; row < porch.rows; ++row)
                {
                    // The front row under the band's front; a second against the wall (Kriegspire's PT07BackW).
                    const double out = row == 0 ? -porch.depth + porch.posts * 2.0 / 3.0
                        : -porch.posts * 2.0 / 3.0 - 8.0;

                    for (size_t column = 0; column < count; ++column)
                    {
                        const double along = from + porch.posts * 0.5 + (to - from - porch.posts) * column
                            / (count - 1);
                        roundColumn(porch.wall, onWall(porch.wall, along, out), porch.posts, foot, front, block);
                    }
                }
            }
            else if (porch.posts > 0.0)
            {
                // At the front corners, under the roof's front edge.
                const double foot = porch.floor > 0.0 ? slab : groundFoot();

                for (const double start : {from, to - porch.posts})
                {
                    m_builder.addPrism({onWall(porch.wall, start, -porch.depth),
                        onWall(porch.wall, start + porch.posts, -porch.depth),
                        onWall(porch.wall, start + porch.posts, -porch.depth + porch.posts),
                        onWall(porch.wall, start, -porch.depth + porch.posts)}, foot, front,
                        textureOr("post", "trim"), "", "", m_nameEvent);
                }
            }
        }
    }

    // Boards on the walls: a slab standing out from the wall with the picture on its face, fitted once when the
    // board is the picture's size.
    void raiseSigns()
    {
        for (const OutdoorWallSignPlan &sign : m_part.signs)
        {
            if (sign.hang)
            {
                raiseHangingSign(sign);
                continue;
            }

            const double from = sign.along - sign.width * 0.5;
            const double to = sign.along + sign.width * 0.5;
            const double in = insetAt(sign.wall, sign.along);
            const double low = m_floor + sign.bottom;
            const double high = low + sign.height;
            const double back = std::max(0.0, sign.out - 6.0);
            const std::string &edge = textureOr("sign_edge", "trim");

            // The board reaches the picture's plane; its own face there is not drawn (it would flicker with the
            // picture).
            const size_t boardFrom = m_builder.faceCount();

            if (sign.out > back)
            {
                m_builder.addPrism({onWall(sign.wall, from, in - back), onWall(sign.wall, from, in - sign.out),
                    onWall(sign.wall, to, in - sign.out), onWall(sign.wall, to, in - back)}, low, high, edge,
                    edge, edge, sign.event != 0 ? sign.event : m_nameEvent);
            }

            const size_t boardTo = m_builder.faceCount();
            texelFace({at(onWall(sign.wall, from, in - sign.out), low), at(onWall(sign.wall, to, in - sign.out),
                low), at(onWall(sign.wall, to, in - sign.out), high), at(onWall(sign.wall, from, in - sign.out), high)},
                sign.texture, {{0.0, sign.height}, {sign.width, sign.height}, {sign.width, 0.0}, {0.0, 0.0}},
                sign.event != 0 ? sign.event : m_nameEvent);
            m_builder.hideUnder(boardFrom, boardTo, boardTo, m_builder.faceCount());
        }
    }

    // A board that hangs across the wall: an arm 16 square from the wall out past the board, 16 over it, and under
    // it the board 6 thick with the picture on both faces (fitted once: `size` is the picture's), `out` from the
    // wall to its near edge. Ravenshore's sgMAGIC: 64 by 64, 56 out, under an arm 32 thick.
    void raiseHangingSign(const OutdoorWallSignPlan &sign)
    {
        const double in = insetAt(sign.wall, sign.along);
        const double low = m_floor + sign.bottom;
        const double high = low + sign.height;
        const double near = in - sign.out;
        const double far = in - sign.out - sign.width;
        const std::string &edge = textureOr("sign_edge", "trim");
        m_builder.addPrism({onWall(sign.wall, sign.along - 8.0, in), onWall(sign.wall, sign.along - 8.0, far - 8.0),
            onWall(sign.wall, sign.along + 8.0, far - 8.0), onWall(sign.wall, sign.along + 8.0, in)}, high + 16.0,
            high + 32.0, edge, edge, edge, sign.event != 0 ? sign.event : m_nameEvent);
        // The board reaches the planes of its two pictures; its own faces there are not drawn.
        const size_t boardFrom = m_builder.faceCount();
        m_builder.addPrism({onWall(sign.wall, sign.along - 3.0, near), onWall(sign.wall, sign.along - 3.0, far),
            onWall(sign.wall, sign.along + 3.0, far), onWall(sign.wall, sign.along + 3.0, near)}, low, high, edge,
            edge, edge, sign.event != 0 ? sign.event : m_nameEvent);
        const size_t boardTo = m_builder.faceCount();
        // The hangers: two straps from the board's top up to the arm.
        for (const double out : {near - 8.0, far + 8.0})
        {
            m_builder.addPrism({onWall(sign.wall, sign.along - 2.0, out + 2.0), onWall(sign.wall, sign.along - 2.0,
                out - 2.0), onWall(sign.wall, sign.along + 2.0, out - 2.0), onWall(sign.wall, sign.along + 2.0,
                out + 2.0)}, high, high + 16.0, edge, "", "", sign.event != 0 ? sign.event : m_nameEvent);
        }

        const std::vector<std::array<double, 2>> texels = {{0.0, sign.height}, {sign.width, sign.height},
            {sign.width, 0.0}, {0.0, 0.0}};
        // Each face read from its own side: from the far end to the wall on the one looking along the wall's
        // direction, from the wall out on the other.
        texelFace({at(onWall(sign.wall, sign.along + 3.0, far), low), at(onWall(sign.wall, sign.along + 3.0,
            near), low), at(onWall(sign.wall, sign.along + 3.0, near), high), at(onWall(sign.wall, sign.along + 3.0,
            far), high)}, sign.texture, texels, sign.event != 0 ? sign.event : m_nameEvent);
        texelFace({at(onWall(sign.wall, sign.along - 3.0, near), low), at(onWall(sign.wall, sign.along - 3.0,
            far), low), at(onWall(sign.wall, sign.along - 3.0, far), high), at(onWall(sign.wall, sign.along - 3.0,
            near), high)}, sign.texture, texels, sign.event != 0 ? sign.event : m_nameEvent);
        m_builder.hideUnder(boardFrom, boardTo, boardTo, m_builder.faceCount());
    }

    // At the outline's corner `vertex`: the tangent of half the turn there, so that a band `depth` wide along both
    // walls is mitred by cutting its inner edge `depth` times this short (1 at a right angle).
    double mitreAt(size_t vertex) const
    {
        const Point2 &before = m_part.outline[(vertex + m_count - 1) % m_count];
        const Point2 &here = m_part.outline[vertex];
        const Point2 &after = m_part.outline[(vertex + 1) % m_count];
        const double turn = oy::atan2(after[1] - here[1], after[0] - here[0])
            - oy::atan2(here[1] - before[1], here[0] - before[0]);
        const double wrapped = std::remainder(turn, 2.0 * Pi);
        return oy::tan(std::clamp(std::abs(wrapped), 0.0, Pi * 0.95) * 0.5);
    }

    // A railing round a flat top: posts at the corners and every `every` along the walls named, a rail on them, and
    // between the posts a barrier that is not drawn, as Ravenshore's terrace has (02nw_corner_ 59 and 60: invisible
    // faces from the terrace to the rail), so the party does not walk through the gaps.
    void raiseRailing()
    {
        const OutdoorRailingPlan &railing = m_part.railing;

        if (railing.height <= 0.0)
        {
            return;
        }

        const double top = m_foot;
        const std::string &postTexture = textureOr("railing", "trim");
        const std::string &railTexture = textureOr("rail", "railing");
        const std::string &railFallback = m_part.textures.contains("rail") ? railTexture : postTexture;
        const double width = railing.posts;
        const double depth = railing.depth;
        const double railFoot = top + railing.height - railing.rail;

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            if (wall >= railing.walls.size() || !railing.walls[wall])
            {
                continue;
            }

            const double length = lengthOf(m_part.outline[wall], m_part.outline[(wall + 1) % m_count]);
            const int gaps = std::max(1, static_cast<int>(std::ceil((length - width) / railing.every)));
            const size_t previous = (wall + m_count - 1) % m_count;

            for (int gap = 0; gap <= gaps; ++gap)
            {
                // The left corner's post belongs to the wall before when that one has a railing too.
                if (gap == 0 && previous < railing.walls.size() && railing.walls[previous])
                {
                    continue;
                }

                const double start = (length - width) * gap / gaps;
                m_builder.addPrism({onWall(wall, start, 0.0), onWall(wall, start + width, 0.0),
                    onWall(wall, start + width, depth), onWall(wall, start, depth)}, top, railFoot, postTexture,
                    postTexture, "", m_nameEvent);
            }

            // The rail, mitred at a corner where the next or last wall's rail meets it (two rails each running to
            // the corner lay over each other there and flickered).
            const size_t next = (wall + 1) % m_count;
            const bool railedBefore = previous != wall && previous < railing.walls.size() && railing.walls[previous];
            const bool railedAfter = next != wall && next < railing.walls.size() && railing.walls[next];
            const double startCut = railedBefore ? depth * mitreAt(wall) : 0.0;
            const double endCut = railedAfter ? depth * mitreAt(next) : 0.0;
            m_builder.addPrism({onWall(wall, 0.0, 0.0), onWall(wall, length, 0.0), onWall(wall, length - endCut,
                depth), onWall(wall, startCut, depth)}, railFoot, top + railing.height, railFallback, railFallback,
                railFallback, m_nameEvent);
            // The barrier, both ways, in the middle of the posts.
            const double middle = depth * 0.5;
            m_builder.hide(surface({at(onWall(wall, 0.0, middle), top), at(onWall(wall, length, middle),
                top), at(onWall(wall, length, middle), railFoot), at(onWall(wall, 0.0, middle), railFoot)},
                postTexture, m_nameEvent));
            m_builder.hide(surface({at(onWall(wall, length, middle), top), at(onWall(wall, 0.0, middle),
                top), at(onWall(wall, 0.0, middle), railFoot), at(onWall(wall, length, middle), railFoot)},
                postTexture, m_nameEvent));
        }
    }

    // A slab before each door that asks for one (`step`).
    void raiseSteps()
    {
        for (const OutdoorDoorPlan &door : m_building.doors)
        {
            if (door.part != m_partIndex || door.stepDepth <= 0.0 || door.storey > 0)
            {
                continue;
            }

            const std::vector<double> edges = bayEdgesOf(m_part, door.wall, false);
            const double from = edges[door.bay] - door.stepOverhang;
            const double to = edges[door.bay + 1] + door.stepOverhang;
            const double in = insetAt(door.wall, (edges[door.bay] + edges[door.bay + 1]) * 0.5);
            const std::string &stepTexture = textureOr("step", "trim");
            const Point2 wallFrom = onWall(door.wall, from, in);
            const Point2 frontFrom = onWall(door.wall, from, in - door.stepDepth);
            const Point2 frontTo = onWall(door.wall, to, in - door.stepDepth);
            const Point2 wallTo = onWall(door.wall, to, in);

            if (door.stepFront >= door.stepHeight)
            {
                m_builder.addPrism({wallFrom, frontFrom, frontTo, wallTo}, groundFoot(), m_floor + door.stepHeight,
                    stepTexture, stepTexture, "", m_nameEvent);
                continue;
            }

            // A stoop: its top slopes from its front edge up to the door.
            const double low = groundFoot();
            const double back = m_floor + door.stepHeight;
            const double front = m_floor + door.stepFront;
            surface({at(wallFrom, back), at(frontFrom, front), at(frontTo, front), at(wallTo, back)},
                stepTexture, m_nameEvent);
            surface({at(frontFrom, low), at(frontTo, low), at(frontTo, front), at(frontFrom, front)},
                stepTexture, m_nameEvent);
            surface({at(wallFrom, low), at(frontFrom, low), at(frontFrom, front), at(wallFrom, back)},
                stepTexture, m_nameEvent);
            surface({at(frontTo, low), at(wallTo, low), at(wallTo, back), at(frontTo, front)},
                stepTexture, m_nameEvent);
        }
    }

    const std::string &texture(const std::string &role) const
    {
        // A word that is no role is a texture's own name.
        const std::map<std::string, std::string>::const_iterator found = m_part.textures.find(role);
        return found != m_part.textures.end() ? found->second : role;
    }

    // A point on a wall's line `along` from its left end, moved `in` toward the part's inside.
    Point2 onWall(size_t wall, double along, double in = 0.0) const
    {
        const Point2 &left = m_part.outline[wall];
        const Point2 &right = m_part.outline[(wall + 1) % m_count];
        const double length = std::max(lengthOf(left, right), 1.0e-9);
        // Computed as before recesses were known, so walls without one keep their bytes.
        const Point2 point = {left[0] + (right[0] - left[0]) * along / length,
            left[1] + (right[1] - left[1]) * along / length};

        if (in == 0.0)
        {
            return point;
        }

        return {point[0] - (right[1] - left[1]) / length * in, point[1] + (right[0] - left[0]) / length * in};
    }

    // The stretches of a wall that are recessed: [from, to] along it and how deep.
    std::vector<std::array<double, 3>> recessesOf(size_t wall) const
    {
        std::vector<std::array<double, 3>> found;

        for (const OutdoorPorchPlan &porch : m_part.porches)
        {
            if (porch.recess && porch.wall == wall)
            {
                const std::vector<double> edges = bayEdgesOf(m_part, wall, false);
                found.push_back({edges[porch.fromBay], edges[porch.toBay + 1], porch.depth});
            }
        }

        return found;
    }

    // How far in the wall stands at a place along it: a recess's depth inside one, else 0.
    double insetAt(size_t wall, double along) const
    {
        for (const std::array<double, 3> &recess : recessesOf(wall))
        {
            if (along > recess[0] && along < recess[1])
            {
                return recess[2];
            }
        }

        return 0.0;
    }

    // A piece of a wall between two distances along it and two heights, its texels given at its corners. Where the
    // piece crosses the end of a recess it is cut there and each piece stands at its own depth. The first face.
    int wallPiece(size_t wall, double from, double to, double low, double high, const std::string &textureName,
        double uFrom, double uTo, double vTop, double vBottom, uint16_t event)
    {
        if (m_part.batter != 0.0 && !m_upright && high > m_floor + 0.5)
        {
            return slopedPiece(wall, from, to, low, high, textureName, uFrom, uTo, vTop, vBottom, event);
        }

        std::vector<double> cuts = {from};
        // S8d: the stretches a recess of the wall beside this one leaves open at their corner are not drawn.
        const std::vector<std::array<double, 2>> open = openStretchesOf(m_part, wall);

        for (const std::array<double, 3> &recess : recessesOf(wall))
        {
            for (const double end : {recess[0], recess[1]})
            {
                if (end > from + 0.5 && end < to - 0.5)
                {
                    cuts.push_back(end);
                }
            }
        }

        for (const std::array<double, 2> &stretch : open)
        {
            for (const double end : stretch)
            {
                if (end > from + 0.5 && end < to - 0.5)
                {
                    cuts.push_back(end);
                }
            }
        }

        // S8d: where a door on a sill reaches up past its row, a piece over it begins at the door's top.
        for (const std::array<double, 4> &hole : m_doorHoles)
        {
            for (const double end : {hole[0], hole[1]})
            {
                if (hole[2] < high - 0.5 && hole[3] > low + 0.5 && end > from + 0.5 && end < to - 0.5)
                {
                    cuts.push_back(end);
                }
            }
        }

        std::sort(cuts.begin(), cuts.end());
        cuts.push_back(to);
        int first = -1;

        for (size_t index = 0; index + 1 < cuts.size(); ++index)
        {
            const double start = cuts[index];
            const double end = cuts[index + 1];

            if (std::any_of(open.begin(), open.end(), [start, end](const std::array<double, 2> &stretch)
                {
                    return (start + end) * 0.5 > stretch[0] && (start + end) * 0.5 < stretch[1];
                }))
            {
                continue;
            }

            double pieceLow = low;

            for (const std::array<double, 4> &hole : m_doorHoles)
            {
                if ((start + end) * 0.5 > hole[0] && (start + end) * 0.5 < hole[1] && hole[2] <= low + 0.5
                    && hole[3] > low + 0.5)
                {
                    pieceLow = std::max(pieceLow, hole[3]);
                }
            }

            if (pieceLow >= high - 0.5)
            {
                continue;
            }

            // The texels at the piece's foot as on the whole piece (unchanged without a door's hole).
            const double vLow = pieceLow == low ? vBottom
                : vBottom + (vTop - vBottom) * (pieceLow - low) / std::max(high - low, 1.0e-9);
            const double in = insetAt(wall, (start + end) * 0.5);
            const double uStart = uFrom + (uTo - uFrom) * (start - from) / std::max(to - from, 1.0e-9);
            const double uEnd = uFrom + (uTo - uFrom) * (end - from) / std::max(to - from, 1.0e-9);
            const int face = texelFace({at(onWall(wall, start, in), pieceLow), at(onWall(wall, end, in), pieceLow),
                at(onWall(wall, end, in), high), at(onWall(wall, start, in), high)}, textureName,
                {{uStart, vLow}, {uEnd, vLow}, {uEnd, vTop}, {uStart, vTop}}, event);
            first = first < 0 ? face : first;
        }

        return first;
    }

    // A door or window bay with an arched head or two leaves: the opening's picture on one face per leaf (the
    // second mirrored), cut to the head; the panel's corners over the head in the wall's own texture. The first face.
    // `fitted`: the picture is `across` by `vBottom - vTop` texels, laid once over each leaf (`fit`). `leafWidth`:
    // the texels across each leaf of two shows (the picture's own width, F2/D-91); 0: 128, a wing's width.
    int dressedPiece(size_t wall, double from, double to, double low, double high, const std::string &textureName,
        double across, double vTop, uint16_t event, const std::string &arch, int sides, int leaves,
        double vBottom = RowHeight, bool fitted = false, double leafWidth = 0.0)
    {
        for (const std::array<double, 2> &open : openStretchesOf(m_part, wall))
        {
            if (from < open[1] - 0.5 && to > open[0] + 0.5)
            {
                // S8d: a bay that reaches into a stretch left open at a corner is a plain piece, cut there.
                return wallPiece(wall, from, to, low, high, textureName, 0.0, across, vTop, vBottom, event);
            }
        }

        const double width = to - from;
        const double height = high - low;
        const double in = insetAt(wall, (from + to) * 0.5);
        // The opening as [along from the bay's left, up from its foot], counter-clockwise seen from outside.
        std::vector<std::array<double, 2>> opening = {{0.0, 0.0}, {width, 0.0}};
        std::vector<std::array<double, 2>> head;

        if (arch.empty())
        {
            opening.push_back({width, height});
            opening.push_back({0.0, height});
        }
        else
        {
            head = outdoorArchHead(width, height, arch, sides);

            for (size_t index = head.size(); index-- > 0;)
            {
                opening.push_back({head[index][0] + width * 0.5, head[index][1]});
            }
        }

        // Each leaf of two shows its picture once, stretched over the leaf (a wing, 128 texels across, as a doorway
        // lays its door; a picture the texture classes know at its own width: a 256-wide door whole on each leaf);
        // one leaf as many texels as the bay is wide, as the wall's panels.
        const double leafAcross = leaves > 1 && !fitted ? (leafWidth > 0.0 ? leafWidth : BayWidth) : across;
        // One leaf: the opening clipped to [left, right] along, its picture spread over the leaf.
        const auto leaf = [&](double left, double right, bool mirrored)
        {
            std::vector<std::array<double, 2>> kept;

            for (size_t index = 0; index < opening.size(); ++index)
            {
                const std::array<double, 2> &a = opening[index];
                const std::array<double, 2> &b = opening[(index + 1) % opening.size()];

                const auto inside = [&](const std::array<double, 2> &point)
                {
                    return point[0] >= left - 1.0e-6 && point[0] <= right + 1.0e-6;
                };

                if (inside(a))
                {
                    kept.push_back(a);
                }

                std::vector<std::array<double, 3>> crossings;

                for (const double edge : {left, right})
                {
                    if ((a[0] - edge) * (b[0] - edge) < 0.0)
                    {
                        const double share = (edge - a[0]) / (b[0] - a[0]);
                        crossings.push_back({share, edge, a[1] + (b[1] - a[1]) * share});
                    }
                }

                std::sort(crossings.begin(), crossings.end());

                for (const std::array<double, 3> &crossing : crossings)
                {
                    kept.push_back({crossing[1], crossing[2]});
                }
            }

            std::vector<OutdoorModelPoint> points;
            std::vector<std::array<double, 2>> texels;

            for (const std::array<double, 2> &point : kept)
            {
                const double share = (point[0] - left) / std::max(right - left, 1.0e-9);
                points.push_back(at(onWall(wall, from + point[0], in), low + point[1]));
                texels.push_back({leafAcross * (mirrored ? 1.0 - share : share),
                    vBottom - (vBottom - vTop) * point[1] / std::max(height, 1.0e-9)});
            }

            return texelFace(points, textureName, texels, event);
        };
        const int first = leaves > 1 ? leaf(0.0, width * 0.5, false) : leaf(0.0, width, false);

        if (leaves > 1)
        {
            leaf(width * 0.5, width, true);
        }

        // The wall over the head.
        for (size_t index = 0; index + 1 < head.size(); ++index)
        {
            const double a = head[index][0] + width * 0.5;
            const double b = head[index + 1][0] + width * 0.5;
            surface({at(onWall(wall, from + a, in), low + head[index][1]),
                at(onWall(wall, from + b, in), low + head[index + 1][1]), at(onWall(wall, from + b, in), high),
                at(onWall(wall, from + a, in), high)}, texture("wall"), m_nameEvent);
        }

        return first;
    }

    // Door dressing: a hood over the door on a cheek at each side, nested frames round it, a portcullis.
    void raiseDoorDressing()
    {
        for (const OutdoorDoorPlan &door : m_building.doors)
        {
            if (door.part != m_partIndex || (door.hood <= 0.0 && door.frameSteps == 0))
            {
                continue;
            }

            const std::vector<double> edges = bayEdgesOf(m_part, door.wall, door.storey > 0);
            const double from = edges[door.bay];
            const double to = edges[door.bay + 1];
            const double in = insetAt(door.wall, (from + to) * 0.5);
            const double low = m_floor + door.storey * RowHeight + (door.storey > 0 ? m_part.band : 0.0);
            const double high = std::min(m_top, low + RowHeight);
            const std::string &trim = door.frameTexture.empty() ? texture("trim") : door.frameTexture;
            // A block on the wall from `a` to `b` along it, standing `out` from it, between two heights.
            const auto block = [&](double a, double b, double out, double z0, double z1, uint16_t event)
            {
                std::vector<Point2> outline = {onWall(door.wall, a, in), onWall(door.wall, b, in),
                    onWall(door.wall, b, in - out), onWall(door.wall, a, in - out)};

                if (signedArea(outline) < 0.0)
                {
                    std::reverse(outline.begin(), outline.end());
                }

                m_builder.addPrism(outline, z0, z1, trim, trim, "", event);
            };
            double outside = 0.0;

            for (int ring = 0; ring < door.frameSteps; ++ring)
            {
                const double inner = ring * door.frameStep;
                const double outer = inner + door.frameStep;
                const double out = (ring + 1) * door.frameStep * 0.5;

                if (high + outer > m_top + 0.5)
                {
                    break;
                }

                block(from - outer, from - inner, out, low, high + inner, m_nameEvent);
                block(to + inner, to + outer, out, low, high + inner, m_nameEvent);
                block(from - outer, to + outer, out, high + inner, high + outer, m_nameEvent);
                outside = out;
            }

            if (door.portcullis)
            {
                const uint16_t event = door.event != 0 ? door.event : m_nameEvent;
                const int bars = std::max(2, static_cast<int>((to - from) / 32.0));

                for (int bar = 1; bar < bars; ++bar)
                {
                    const double middle = from + (to - from) * bar / bars;
                    block(middle - 4.0, middle + 4.0, 12.0, low, high, event);
                }

                for (const double z : {low + (high - low) * 0.35, low + (high - low) * 0.7})
                {
                    block(from + 2.0, to - 2.0, 10.0, z - 4.0, z + 4.0, event);
                }
            }

            if (door.hood > 0.0)
            {
                // Over the frames, if any: the hood reaches out past them.
                const double reach = door.hood + outside;
                const double side = 32.0;
                const double clear = 16.0 + door.frameSteps * door.frameStep;
                const double hoodLow = high + door.frameSteps * door.frameStep;
                block(from - side - clear, to + side + clear, reach, hoodLow, hoodLow + 32.0, m_nameEvent);
                block(from - side - clear, from - clear, reach, low, hoodLow, m_nameEvent);
                block(to + clear, to + side + clear, reach, low, hoodLow, m_nameEvent);
            }
        }
    }

    // Whether a role's texture repeats from bay to bay (plain wall) or is a panel of its own (a window, a post).
    bool tiles(const std::string &role) const
    {
        return role == "wall" || role == "base" || role == "gable" || role == "parapet";
    }

    bool sameEvent(size_t wall, int row, size_t bay, size_t other) const
    {
        for (const OutdoorDoorPlan &door : m_building.doors)
        {
            if (row == 0 && door.part == m_partIndex && door.wall == wall && (door.bay == bay || door.bay == other))
            {
                return false;
            }
        }

        return true;
    }

    // A wall at the back of a building against a slope: its outward side faces the back.
    bool backWall(size_t wall) const
    {
        if (!m_building.against)
        {
            return false;
        }

        const Point2 &left = m_part.outline[wall];
        const Point2 &right = m_part.outline[(wall + 1) % m_count];
        const double length = lengthOf(left, right);
        return length > 0.0 && ((right[1] - left[1]) * m_building.back[0] - (right[0] - left[0])
            * m_building.back[1]) / length > 0.7;
    }

    void raiseWall(size_t wall)
    {
        const double length = lengthOf(m_part.outline[wall], m_part.outline[(wall + 1) % m_count]);

        if (m_part.posts > 0.0)
        {
            // An open part: posts and low walls instead (raiseOpen).
            return;
        }

        if (backWall(wall))
        {
            // Against a slope: the wall at the back stands in the rock.
            return;
        }

        if (m_part.bottom == 0.0 && m_building.foundation > 0.0)
        {
            // The base course: down into the ground (a skirt in the ground's texture).
            wallPiece(wall, 0.0, length, m_floor - m_building.foundation, m_floor,
                m_building.skirt.empty() ? texture("base") : m_building.skirt, 0.0, length, 0.0,
                m_building.foundation, m_nameEvent);
        }

        if (m_part.taper != 1.0)
        {
            // A leaning wall is one plain face from the foot to the drawn-in top.
            const Point2 &left = m_part.outline[wall];
            const Point2 &right = m_part.outline[(wall + 1) % m_count];
            surface({at(left, m_floor), at(right, m_floor), at(m_topOutline[(wall + 1) % m_count], m_top),
                at(m_topOutline[wall], m_top)}, texture("wall"), m_nameEvent);
            return;
        }

        // The rows above the lowest begin over the band.
        const auto rowFoot = [this](int row)
        {
            return m_floor + row * RowHeight + (row > 0 ? m_part.band : 0.0);
        };
        // S8d: a door on a `sill` stands a whole door high from it, up into the rows (and band) above its own.
        m_doorHoles.clear();

        for (const OutdoorDoorPlan &door : m_building.doors)
        {
            if (door.sill > 0.0 && door.part == m_partIndex && door.wall == wall)
            {
                const std::vector<double> edges = bayEdgesOf(m_part, wall, door.storey > 0);
                const double foot = rowFoot(static_cast<int>(door.storey));
                const double rowTop = std::min(m_top, foot + RowHeight);
                const double doorTop = std::min(m_top, foot + door.sill + RowHeight);

                if (door.bay + 1 < edges.size() && doorTop > rowTop + 0.5)
                {
                    m_doorHoles.push_back({edges[door.bay], edges[door.bay + 1], rowTop, doorTop});
                }
            }
        }

        if (m_part.band > 0.0 && m_floor + RowHeight < m_top - 0.5)
        {
            const double bandTop = std::min(m_top, m_floor + RowHeight + m_part.band);
            const int face = wallPiece(wall, 0.0, length, m_floor + RowHeight, bandTop,
                texture(m_part.textures.contains("band") ? "band" : "trim"), 0.0, length, 0.0,
                bandTop - m_floor - RowHeight, m_nameEvent);

            if (wall < m_part.climbFrom.size() && m_part.climbFrom[wall])
            {
                through(face);
            }
        }

        for (int row = 0; rowFoot(row) < m_top - 0.5; ++row)
        {
            const double low = rowFoot(row);
            const double high = std::min(m_top, low + RowHeight);
            std::vector<std::string> bays = row == 0 ? m_part.bays[wall] : m_part.upperBays[wall];

            // A door up a storey is in its own row only; in the other rows above its bay is a window or wall.
            for (size_t bay = 0; row > 0 && bay < bays.size(); ++bay)
            {
                const bool here = std::any_of(m_building.doors.begin(), m_building.doors.end(),
                    [this, wall, bay, row](const OutdoorDoorPlan &door)
                    {
                        return door.part == m_partIndex && door.wall == wall && door.bay == bay
                            && door.storey == static_cast<size_t>(row);
                    });

                if (bays[bay] == "door" && !here)
                {
                    bays[bay] = m_part.textures.contains("window") ? "window" : "wall";
                }
            }

            const size_t count = std::max<size_t>(1, bays.size());
            const std::vector<double> edges = bayEdgesOf(m_part, wall, row > 0);
            const std::vector<std::vector<double>> &widthRows = row > 0 ? m_part.upperBayWidths : m_part.bayWidths;
            const std::vector<double> widths = wall < widthRows.size() ? widthRows[wall] : std::vector<double>();
            // A row is 256 of texture; a top row that is lower shows the texture's lower part.
            const double vTop = RowHeight - (high - low);

            for (size_t bay = 0; bay < count;)
            {
                const std::string role = bays.empty() ? "wall" : bays[bay];
                size_t end = bay + 1;

                // Plain bays side by side are one face: the texture repeats (not a picture laid once per bay).
                while (role != "door" && end < count && bays[end] == role && sameEvent(wall, row, bay, end)
                    && tiles(role) && !m_part.fitted.contains(role))
                {
                    ++end;
                }

                OutdoorDoorPlan *pDoor = nullptr;

                for (OutdoorDoorPlan &door : m_building.doors)
                {
                    if (door.storey == static_cast<size_t>(row) && door.part == m_partIndex && door.wall == wall
                        && door.bay == bay)
                    {
                        pDoor = &door;
                    }
                }

                const std::string &faceTexture = pDoor != nullptr && !pDoor->texture.empty() ? pDoor->texture
                    : texture(role);
                // A panel to every bay, or as much of it as a bay of its own width shows.
                double across = 0.0;

                for (size_t piece = bay; piece < end; ++piece)
                {
                    across += piece < widths.size() && widths[piece] > 0.0 ? widths[piece] : BayWidth;
                }

                if (pDoor != nullptr && notchDoor(*pDoor))
                {
                    // Higher than the walls: cut into the roof once it is raised (finishCaptured).
                    bay = end;
                    continue;
                }

                const uint16_t pieceEvent = pDoor != nullptr && pDoor->event != 0 ? pDoor->event : m_nameEvent;
                const std::string arch = pDoor != nullptr ? pDoor->arch : role == "window" ? m_part.windowArch
                    : std::string();
                const int leaves = pDoor != nullptr ? pDoor->leaves : 1;
                // A door in a battered wall stands upright at its foot, the slope's wedge round its head.
                m_upright = pDoor != nullptr && m_part.batter > 0.0;
                // S8d: a door on a `sill`: the wall's panel under it, the door a whole door high from it (the rows
                // above begin over it: m_doorHoles).
                const double sill = pDoor != nullptr ? pDoor->sill : 0.0;
                const double pieceLow = low + sill;
                const double pieceHigh = sill > 0.0 ? std::min(m_top, pieceLow + RowHeight) : high;
                const double pieceTop = sill > 0.0 ? RowHeight - (pieceHigh - pieceLow) : vTop;

                if (sill > 0.0)
                {
                    wallPiece(wall, edges[bay], edges[end], low, pieceLow, texture("wall"), 0.0, across,
                        RowHeight - sill, RowHeight, m_nameEvent);
                }

                // A picture laid once per bay (`fit`): its own texels stretched over the bay's piece.
                const std::map<std::string, std::array<double, 2>>::const_iterator fitted =
                    pDoor != nullptr && !pDoor->texture.empty() ? m_part.fitted.end() : m_part.fitted.find(role);
                const bool fit = fitted != m_part.fitted.end();
                const double faceAcross = fit ? fitted->second[0] : across;
                const double faceTop = fit ? 0.0 : pieceTop;
                const double faceBottom = fit ? fitted->second[1] : RowHeight;
                const int face = (!arch.empty() || leaves > 1) && end == bay + 1
                    ? dressedPiece(wall, edges[bay], edges[end], pieceLow, pieceHigh, faceTexture, faceAcross,
                        faceTop, pieceEvent, arch, pDoor != nullptr ? pDoor->archSides : 6, leaves, faceBottom, fit,
                        pDoor != nullptr ? pDoor->pictureWidth : 0.0)
                    : wallPiece(wall, edges[bay], edges[end], pieceLow, pieceHigh, faceTexture, 0.0, faceAcross,
                        faceTop, faceBottom, pieceEvent);

                if (m_upright)
                {
                    m_upright = false;
                    raiseWedge(wall, edges[bay], edges[end], low, high);
                }

                if (wall < m_part.climbFrom.size() && m_part.climbFrom[wall])
                {
                    // A riser under the hidden slope.
                    through(face);
                }

                if (pDoor != nullptr)
                {
                    const Point2 &left = m_part.outline[wall];
                    const Point2 &right = m_part.outline[(wall + 1) % m_count];
                    const double middle = (edges[bay] + edges[bay + 1]) * 0.5 / length;
                    // A door in a recess stands at the recess's back.
                    const double in = insetAt(wall, middle * length);
                    pDoor->face = face;
                    pDoor->x = left[0] + (right[0] - left[0]) * middle - (right[1] - left[1]) / length * in;
                    pDoor->y = left[1] + (right[1] - left[1]) * middle + (right[0] - left[0]) / length * in;
                    pDoor->z = pieceLow;
                    pDoor->normalX = (right[1] - left[1]) / length;
                    pDoor->normalY = -(right[0] - left[0]) / length;
                }

                bay = end;
            }
        }
    }

    // The band between two outlines at one height: looks down when `down` (a soffit), else up.
    void ring(const std::vector<Point2> &inner, const std::vector<Point2> &outer, double z, bool down,
        const std::string &textureName)
    {
        for (size_t index = 0; index < m_count; ++index)
        {
            const size_t next = (index + 1) % m_count;
            std::vector<OutdoorModelPoint> points = {at(inner[index], z), at(inner[next], z), at(outer[next], z),
                at(outer[index], z)};

            if (!down)
            {
                points = {at(outer[index], z), at(outer[next], z), at(inner[next], z), at(inner[index], z)};
            }

            surface(points, textureName, m_nameEvent);
        }
    }

    // An upright band along every side of an outline; `inward` turns it to look to the middle.
    void band(const std::vector<Point2> &outline, double low, double high, bool inward, const std::string &textureName)
    {
        for (size_t index = 0; index < m_count; ++index)
        {
            const size_t next = (index + 1) % m_count;
            const Point2 &from = inward ? outline[next] : outline[index];
            const Point2 &to = inward ? outline[index] : outline[next];
            const double length = lengthOf(from, to);
            texelFace({at(from, low), at(to, low), at(to, high), at(from, high)}, textureName,
                {{0.0, high - low}, {length, high - low}, {length, 0.0}, {0.0, 0.0}}, m_nameEvent);
        }
    }

    void raiseRoof()
    {
        const OutdoorRoofPlan &roof = m_part.roof;

        if (roof.form == "none")
        {
            return;
        }

        if (!m_part.court.empty())
        {
            raiseCourtRoof();
            return;
        }

        const std::string &roofTexture = texture("roof");
        const std::string &trim = texture("trim");
        const uint16_t event = m_nameEvent;

        if (roof.parapet > 0.0)
        {
            if (m_part.concave || !roof.parapetStretches.empty())
            {
                raiseParapetStretches();
            }
            else
            {
                raiseParapet();
            }

            return;
        }

        if (m_part.concave || roof.eavesPartial)
        {
            raiseCoverRoof();
            return;
        }

        const bool box = m_part.shape == "box";
        const bool ridged = box && (roof.form == "hip" || roof.form == "gable");
        const double first = box ? lengthOf(m_topOutline[0], m_topOutline[1]) : 0.0;
        const double second = box ? lengthOf(m_topOutline[1], m_topOutline[2]) : 0.0;
        const bool alongFirst = roof.along == 'x' || (roof.along != 'y' && first >= second);
        // A vault (S8d) has a gable's eaves, fascia and end walls.
        const bool gabled = roof.form == "gable" || roof.form == "vault";
        // How far a gable runs on past its end on the box's wall `wall` (`verge`, `verge_walls`).
        const auto vergeAt = [&roof](size_t wall)
        {
            return roof.form == "gable" && roof.vergeWalls[wall % 4] ? roof.verge : 0.0;
        };
        // The roof's foot: the walls' outline moved out by the eaves; a gable roof only at its eaves sides.
        std::vector<Point2> outer = roof.eavesWalls.empty() ? grown(m_topOutline, roof.eaves)
            : eavesOutline(box && gabled ? (alongFirst ? 1 : 0) : -1);

        if (box && gabled && roof.eaves > 0.0 && roof.eavesWalls.empty())
        {
            const std::vector<Point2> &inner = m_topOutline;

            // Out across the ridge only: each corner away from the corner across the building from it.
            for (size_t corner = 0; corner < 4; ++corner)
            {
                const Point2 &own = inner[corner];
                const Point2 &across = inner[alongFirst ? 3 - corner : (corner ^ 1)];
                const double length = std::max(lengthOf(across, own), 1.0e-9);
                outer[corner] = {own[0] + (own[0] - across[0]) / length * roof.eaves,
                    own[1] + (own[1] - across[1]) / length * roof.eaves};
            }
        }

        if (roof.eaves > 0.0)
        {
            ring(m_topOutline, outer, m_top, true, trim);
        }

        if (roof.fascia > 0.0)
        {
            if (box && gabled)
            {
                // Only along the eaves: the gable ends take the band into their own face.
                for (const size_t wall : alongFirst ? std::array<size_t, 2>{0, 2} : std::array<size_t, 2>{1, 3})
                {
                    // With a verge the band runs on with the slopes past the gable ends, to the barge boards. The
                    // ridge's first corner (the near end, its wall before it) starts the first eaves wall.
                    const Point2 &start = outer[wall];
                    const Point2 &end = outer[(wall + 1) % 4];
                    const double wallLength = std::max(lengthOf(start, end), 1.0e-9);
                    const size_t first = alongFirst ? 0 : 1;
                    const double vergeNear = vergeAt((first + 3) % 4);
                    const double vergeFar = vergeAt((first + 1) % 4);
                    const double fromBy = wall == first ? vergeNear : vergeFar;
                    const double toBy = wall == first ? vergeFar : vergeNear;
                    const Point2 way = {(end[0] - start[0]) / wallLength, (end[1] - start[1]) / wallLength};
                    const Point2 from = {start[0] - way[0] * fromBy, start[1] - way[1] * fromBy};
                    const Point2 to = {end[0] + way[0] * toBy, end[1] + way[1] * toBy};
                    const double length = lengthOf(from, to);
                    texelFace({at(from, m_top), at(to, m_top), at(to, m_foot), at(from, m_foot)}, trim,
                        {{0.0, roof.fascia}, {length, roof.fascia}, {length, 0.0}, {0.0, 0.0}}, event);
                }
            }
            else
            {
                band(outer, m_top, m_foot, false, trim);
            }
        }

        if (roof.form == "flat" || roof.rise <= 0.0)
        {
            if (!m_part.holes.empty())
            {
                raiseHoledTop(outer);
                return;
            }

            std::vector<OutdoorModelPoint> points;

            for (const Point2 &point : outer)
            {
                points.push_back(at(point, m_foot));
            }

            surface(points, roofTexture, event);
            return;
        }

        if (roof.form == "vault")
        {
            raiseVault(outer, alongFirst, event);
            return;
        }

        if (!roof.tiers.empty())
        {
            raiseTiers(outer);
            return;
        }

        const double tip = m_foot + roof.rise;

        if ((!box && (roof.form == "hip" || roof.form == "gable")) || (roof.form == "hip" && roof.cap > 0.0))
        {
            raiseOutlineRoof(outer, tip);
            return;
        }

        if (roof.form == "dome")
        {
            raiseDome(outer, tip);
            return;
        }

        if (roof.form == "cone" || !box)
        {
            Point2 middle = {0.0, 0.0};

            for (const Point2 &point : outer)
            {
                middle = {middle[0] + point[0] / m_count, middle[1] + point[1] / m_count};
            }

            for (size_t index = 0; index < m_count; ++index)
            {
                surface({at(outer[index], m_foot), at(outer[(index + 1) % m_count], m_foot),
                    at(middle, tip)}, roofTexture, event);
            }

            return;
        }

        if (roof.form == "lean_to")
        {
            // The low wall is `low`; the slope rises to the wall across.
            const size_t low = static_cast<size_t>(roof.along - '0') % 4;
            const Point2 &lowLeft = outer[low];
            const Point2 &lowRight = outer[(low + 1) % 4];
            const Point2 &highRight = outer[(low + 2) % 4];
            const Point2 &highLeft = outer[(low + 3) % 4];
            const std::string &gable = texture("gable");
            surface({at(lowLeft, m_foot), at(lowRight, m_foot), at(highRight, tip), at(highLeft, tip)},
                roofTexture, event);
            // The back wall above the eaves, and the two cheeks.
            const double back = lengthOf(highRight, highLeft);
            texelFace({at(highRight, m_foot), at(highLeft, m_foot), at(highLeft, tip), at(highRight, tip)},
                gable, {{0.0, roof.rise}, {back, roof.rise}, {back, 0.0}, {0.0, 0.0}}, event);
            const double depth = lengthOf(lowRight, highRight);
            texelFace({at(lowRight, m_foot), at(highRight, m_foot), at(highRight, tip)}, gable,
                {{0.0, roof.rise}, {depth, roof.rise}, {depth, 0.0}}, event);
            texelFace({at(highLeft, m_foot), at(lowLeft, m_foot), at(highLeft, tip)}, gable,
                {{0.0, roof.rise}, {depth, roof.rise}, {0.0, 0.0}}, event);
            return;
        }

        if (roof.form == "gable" && roof.halfHip > 0.0)
        {
            raiseHalfHip(outer, alongFirst, event);
            return;
        }

        // Hip and gable: in a frame along the ridge. `a` to `b` is the eaves side on the right of the ridge's
        // direction, `c` to `d` the other, so a, b, c, d run counter-clockwise.
        const size_t start = alongFirst ? 0 : 1;
        const Point2 &a = outer[start];
        const Point2 &b = outer[(start + 1) % 4];
        const Point2 &c = outer[(start + 2) % 4];
        const Point2 &d = outer[(start + 3) % 4];
        const double ridgeLength = lengthOf(a, b);
        const double span = lengthOf(b, c);
        const double run = roof.form == "gable" ? 0.0
            : std::min(roof.hipRun > 0.0 ? roof.hipRun : span * 0.5, ridgeLength * 0.5);
        const auto onRidge = [&](double along)
        {
            return Point2{(a[0] + d[0]) * 0.5 + (b[0] - a[0]) * along / ridgeLength,
                (a[1] + d[1]) * 0.5 + (b[1] - a[1]) * along / ridgeLength};
        };
        const Point2 ridgeFrom = onRidge(run);
        const Point2 ridgeTo = onRidge(ridgeLength - run);
        const bool point = ridgeLength - 2.0 * run < 1.0;
        // A gable's verge: the slopes run on along the ridge past each gable end that takes it (the gable faces stay
        // in the walls' planes, up to the ridge there). The near end (a, d) is on the wall before `start`.
        const double vergeNear = vergeAt(start + 3);
        const double vergeFar = vergeAt(start + 1);
        const Point2 ridgeWay = {(b[0] - a[0]) / ridgeLength, (b[1] - a[1]) / ridgeLength};
        const auto onward = [&ridgeWay](const Point2 &place, double by)
        {
            return Point2{place[0] + ridgeWay[0] * by, place[1] + ridgeWay[1] * by};
        };
        const Point2 slopeA = onward(a, -vergeNear);
        const Point2 slopeB = onward(b, vergeFar);
        const Point2 slopeC = onward(c, vergeFar);
        const Point2 slopeD = onward(d, -vergeNear);
        const Point2 slopeFrom = onward(ridgeFrom, -vergeNear);
        const Point2 slopeTo = onward(ridgeTo, vergeFar);

        if (point)
        {
            surface({at(a, m_foot), at(b, m_foot), at(ridgeFrom, tip)}, roofTexture, event);
            surface({at(c, m_foot), at(d, m_foot), at(ridgeFrom, tip)}, roofTexture, event);
        }
        else
        {
            surface({at(slopeA, m_foot), at(slopeB, m_foot), at(slopeTo, tip), at(slopeFrom, tip)}, roofTexture,
                event);
            surface({at(slopeC, m_foot), at(slopeD, m_foot), at(slopeFrom, tip), at(slopeTo, tip)}, roofTexture,
                event);
        }

        if (roof.form == "hip")
        {
            surface({at(b, m_foot), at(c, m_foot), at(ridgeTo, tip)}, roofTexture, event);
            surface({at(d, m_foot), at(a, m_foot), at(ridgeFrom, tip)}, roofTexture, event);
        }
        else
        {
            // The gable ends: on the wall, from its top up to the ridge, with the fascia's height at the eaves.
            const std::string &gable = texture("gable");
            const std::vector<Point2> &inner = m_topOutline;

            for (const bool far : {false, true})
            {
                const Point2 &left = far ? inner[(start + 1) % 4] : inner[(start + 3) % 4];
                const Point2 &right = far ? inner[(start + 2) % 4] : inner[start];
                const Point2 &top = far ? ridgeTo : ridgeFrom;
                const double width = lengthOf(left, right);
                // The roof's height over the wall's ends: the eaves reach out past them.
                // On the eaves side of each end the roof's height over the wall's end (`eaves_walls` may leave one
                // side flush).
                const double rightShoulder = m_foot + roof.rise * (eavesOf(far ? (start + 2) % 4 : start)
                    / (span * 0.5));
                const double leftShoulder = m_foot + roof.rise * (eavesOf(far ? start : (start + 2) % 4)
                    / (span * 0.5));
                std::vector<OutdoorModelPoint> points = {at(left, m_top), at(right, m_top)};
                std::vector<std::array<double, 2>> texels = {{0.0, tip - m_top}, {width, tip - m_top}};

                if (rightShoulder - m_top > 0.5)
                {
                    points.push_back(at(right, rightShoulder));
                    texels.push_back({width, tip - rightShoulder});
                }

                points.push_back(at(top, tip));
                texels.push_back({width * 0.5, 0.0});

                if (leftShoulder - m_top > 0.5)
                {
                    points.push_back(at(left, leftShoulder));
                    texels.push_back({0.0, tip - leftShoulder});
                }

                texelFace(points, gable, texels, event);
            }

            // The barge boards: at each end, under the roof's edge from each eaves corner up to the ridge, in the
            // end's plane out at the verge, wound to face out from the gable.
            if (roof.barge > 0.0)
            {
                const double slopeLength = std::hypot(span * 0.5, roof.rise);

                for (const bool far : {false, true})
                {
                    if ((far ? vergeFar : vergeNear) <= 0.0)
                    {
                        continue;
                    }

                    const Point2 &apex = far ? slopeTo : slopeFrom;
                    const Point2 out = far ? ridgeWay : Point2{-ridgeWay[0], -ridgeWay[1]};

                    for (const Point2 &corner : far ? std::array<Point2, 2>{slopeB, slopeC}
                                                    : std::array<Point2, 2>{slopeA, slopeD})
                    {
                        std::vector<OutdoorModelPoint> points = {at(corner, m_foot), at(apex, tip),
                            at(apex, tip - roof.barge), at(corner, m_foot - roof.barge)};
                        std::vector<std::array<double, 2>> texels = {{0.0, 0.0}, {slopeLength, 0.0},
                            {slopeLength, roof.barge}, {0.0, roof.barge}};
                        // Counter-clockwise seen from outside: the normal of (1 - 0) x (2 - 0) points out.
                        const double ax = points[1][0] - points[0][0];
                        const double ay = points[1][1] - points[0][1];
                        const double az = points[1][2] - points[0][2];
                        const double bx = points[2][0] - points[0][0];
                        const double by = points[2][1] - points[0][1];
                        const double bz = points[2][2] - points[0][2];
                        const double normalX = ay * bz - az * by;
                        const double normalY = az * bx - ax * bz;

                        if (normalX * out[0] + normalY * out[1] < 0.0)
                        {
                            std::reverse(points.begin(), points.end());
                            std::reverse(texels.begin(), texels.end());
                        }

                        texelFace(points, trim, texels, event);
                    }
                }
            }
        }

        if (roof.ridge > 0.0 && !point)
        {
            // The ridge beam: a bar on the ridge, half sunk into it.
            const double half = roof.ridge * 0.5;
            const double acrossX = (d[0] - a[0]) / span;
            const double acrossY = (d[1] - a[1]) / span;
            const auto beam = [&](const Point2 &place, double side, double z)
            {
                return OutdoorModelPoint{place[0] + acrossX * half * side, place[1] + acrossY * half * side, z};
            };
            const std::string &ridgeTexture = texture("ridge");
            const double low = tip - half;
            const double high = tip + half;
            // On a gable the beam's ends stand out past the gable walls by half its width: ended in their planes,
            // they would flicker with the walls' tips.
            // With a verge they run on to its ends.
            const double pastFrom = roof.form == "gable" ? half + vergeNear : 0.0;
            const double pastTo = roof.form == "gable" ? half + vergeFar : 0.0;
            const Point2 beamFrom = {ridgeFrom[0] - (b[0] - a[0]) / ridgeLength * pastFrom,
                ridgeFrom[1] - (b[1] - a[1]) / ridgeLength * pastFrom};
            const Point2 beamTo = {ridgeTo[0] + (b[0] - a[0]) / ridgeLength * pastTo,
                ridgeTo[1] + (b[1] - a[1]) / ridgeLength * pastTo};
            const double length = lengthOf(beamFrom, beamTo);
            surface({beam(beamFrom, -1.0, high), beam(beamTo, -1.0, high), beam(beamTo, 1.0, high),
                beam(beamFrom, 1.0, high)}, ridgeTexture, event);
            texelFace({beam(beamFrom, -1.0, low), beam(beamTo, -1.0, low), beam(beamTo, -1.0, high),
                beam(beamFrom, -1.0, high)}, ridgeTexture, {{0.0, roof.ridge}, {length, roof.ridge}, {length, 0.0},
                {0.0, 0.0}}, event);
            texelFace({beam(beamTo, 1.0, low), beam(beamFrom, 1.0, low), beam(beamFrom, 1.0, high),
                beam(beamTo, 1.0, high)}, ridgeTexture, {{0.0, roof.ridge}, {length, roof.ridge}, {length, 0.0},
                {0.0, 0.0}}, event);
            texelFace({beam(beamTo, -1.0, low), beam(beamTo, 1.0, low), beam(beamTo, 1.0, high),
                beam(beamTo, -1.0, high)}, ridgeTexture, {{0.0, roof.ridge}, {roof.ridge, roof.ridge},
                {roof.ridge, 0.0}, {0.0, 0.0}}, event);
            texelFace({beam(beamFrom, 1.0, low), beam(beamFrom, -1.0, low), beam(beamFrom, -1.0, high),
                beam(beamFrom, 1.0, high)}, ridgeTexture, {{0.0, roof.ridge}, {roof.ridge, roof.ridge},
                {roof.ridge, 0.0}, {0.0, 0.0}}, event);
        }
    }

    // A convex outline cut by the line through `point` with the normal `normal`: the side where
    // (p - point) . normal <= 0.
    static std::vector<Point2> clipped(const std::vector<Point2> &polygon, const Point2 &point, const Point2 &normal)
    {
        std::vector<Point2> result;

        for (size_t index = 0; index < polygon.size(); ++index)
        {
            const Point2 &from = polygon[index];
            const Point2 &to = polygon[(index + 1) % polygon.size()];
            const double fromSide = (from[0] - point[0]) * normal[0] + (from[1] - point[1]) * normal[1];
            const double toSide = (to[0] - point[0]) * normal[0] + (to[1] - point[1]) * normal[1];

            if (fromSide <= 1.0e-9)
            {
                result.push_back(from);
            }

            if ((fromSide < -1.0e-9 && toSide > 1.0e-9) || (fromSide > 1.0e-9 && toSide < -1.0e-9))
            {
                const double share = fromSide / (fromSide - toSide);
                result.push_back({from[0] + (to[0] - from[0]) * share, from[1] + (to[1] - from[1]) * share});
            }
        }

        return result;
    }

    // A roof in rings (`tiers`): from the roof's foot each ring is the outline drawn in and raised, its slope one
    // face over each side; a ring that reaches the middle is a cone's tip, else a flat top closes the last.
    // S8d: a pent roof round the walls (`pent`): a sloping slab from the walls down and out to its edge, its top in
    // the `pent` texture role (the roof's), its underside and edge in the trim, the corners mitred as eaves are.
    void raisePent()
    {
        if (m_part.pentHeight <= 0.0)
        {
            return;
        }

        const std::vector<Point2> &inner = m_part.outline;
        const std::vector<Point2> outer = grown(inner, m_part.pentOut);
        const double edge = m_floor + m_part.pentHeight;
        const double wall = edge + m_part.pentRise;
        const double thick = m_part.pentThickness;
        const std::string &top = textureOr("pent", "roof");
        const std::string &trim = texture("trim");

        for (size_t index = 0; index < m_count; ++index)
        {
            const size_t next = (index + 1) % m_count;
            const double length = std::max(lengthOf(inner[index], inner[next]), 1.0e-9);
            const Point2 out = {(inner[next][1] - inner[index][1]) / length,
                -(inner[next][0] - inner[index][0]) / length};
            const double rise = m_part.pentRise;
            const double reach = m_part.pentOut;
            surface(facing({at(inner[index], wall + thick), at(outer[index], edge + thick),
                at(outer[next], edge + thick), at(inner[next], wall + thick)}, {out[0] * rise, out[1] * rise, reach}),
                top, m_nameEvent);
            surface(facing({at(inner[index], wall), at(inner[next], wall), at(outer[next], edge),
                at(outer[index], edge)}, {-out[0] * rise, -out[1] * rise, -reach}), trim, m_nameEvent);
            surface(facing({at(outer[index], edge), at(outer[next], edge), at(outer[next], edge + thick),
                at(outer[index], edge + thick)}, {out[0], out[1], 0.0}), trim, m_nameEvent);
        }
    }

    // S8d: a gable hipped at its ends up to `half_hip` (a jerkinhead): in a frame along the ridge as the gable's,
    // each eaves slope cut at its ends where the hips rise, a hip from each end's eaves to the half-hip's height
    // `halfHipRun` in, and a small upright gable over it up to the ridge in the `gable` texture.
    void raiseHalfHip(const std::vector<Point2> &outer, bool alongFirst, uint16_t event)
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        const size_t start = alongFirst ? 0 : 1;
        const Point2 &a = outer[start];
        const Point2 &b = outer[(start + 1) % 4];
        const Point2 &d = outer[(start + 3) % 4];
        const double length = std::max(lengthOf(a, b), 1.0);
        const double span = std::max(lengthOf(a, d), 1.0);
        const double half = span * 0.5;
        const double run = std::min(roof.halfHipRun, length * 0.5);
        const double shoulder = std::min(half * roof.halfHip / std::max(roof.rise, 1.0), half);
        const double knee = m_foot + roof.halfHip;
        const double tip = m_foot + roof.rise;
        const auto place = [&](double across, double along, double z)
        {
            return at(Point2{a[0] + (d[0] - a[0]) * across / span + (b[0] - a[0]) * along / length,
                a[1] + (d[1] - a[1]) * across / span + (b[1] - a[1]) * along / length}, z);
        };
        const std::string &roofTexture = texture("roof");
        // The eaves slopes, cut at both ends where the hips rise to the knee.
        surface({place(0.0, 0.0, m_foot), place(0.0, length, m_foot), place(shoulder, length - run, knee),
            place(half, length - run, tip), place(half, run, tip), place(shoulder, run, knee)}, roofTexture, event);
        surface({place(span, length, m_foot), place(span, 0.0, m_foot), place(span - shoulder, run, knee),
            place(half, run, tip), place(half, length - run, tip), place(span - shoulder, length - run, knee)},
            roofTexture, event);
        // The hips over the two ends, and the small gables over them.
        surface({place(span, 0.0, m_foot), place(0.0, 0.0, m_foot), place(shoulder, run, knee),
            place(span - shoulder, run, knee)}, roofTexture, event);
        surface({place(0.0, length, m_foot), place(span, length, m_foot), place(span - shoulder, length - run, knee),
            place(shoulder, length - run, knee)}, roofTexture, event);
        const std::string &gable = texture("gable");
        const std::array<double, 3> outward = {(a[0] - b[0]) / length, (a[1] - b[1]) / length, 0.0};

        for (const bool far : {false, true})
        {
            const double along = far ? length - run : run;
            const double width = span - 2.0 * shoulder;
            std::vector<OutdoorModelPoint> points = {place(shoulder, along, knee), place(span - shoulder, along, knee),
                place(half, along, tip)};
            std::vector<std::array<double, 2>> texels = {{0.0, tip - knee}, {width, tip - knee},
                {width * 0.5, 0.0}};
            const std::array<double, 3> way = far ? std::array<double, 3>{-outward[0], -outward[1], 0.0} : outward;
            const std::vector<OutdoorModelPoint> turnedPoints = facing(points, way);

            if (turnedPoints.front() != points.front() || turnedPoints[1] != points[1])
            {
                std::reverse(texels.begin(), texels.end());
            }

            texelFace(turnedPoints, gable, texels, event);
        }
    }

    // S8d: a vault over a box (`roof: vault`): in a frame along the ridge as a gable's, the section across it from
    // one eaves side to the other (`tiers`, mirrored, with a flat crown between; or a half ellipse), one face per
    // segment along the whole ridge, the two end walls closed up to the section in the `gable` texture.
    void raiseVault(const std::vector<Point2> &outer, bool alongFirst, uint16_t event)
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        const size_t start = alongFirst ? 0 : 1;
        const Point2 &a = outer[start];
        const Point2 &b = outer[(start + 1) % 4];
        const Point2 &d = outer[(start + 3) % 4];
        const double span = std::max(lengthOf(a, d), 1.0);
        const double half = span * 0.5;
        // The section's points [across from a's side, up from the roof's foot], from one eaves edge to the other.
        std::vector<std::array<double, 2>> section = {{0.0, 0.0}};

        if (!roof.tiers.empty())
        {
            for (const std::array<double, 2> &tier : roof.tiers)
            {
                section.push_back({std::min(section.back()[0] + tier[0], half), section.back()[1] + tier[1]});
            }
        }
        else
        {
            const int segments = std::max(2, roof.vaultSegments);

            for (int segment = 1; segment <= segments; ++segment)
            {
                const double angle = segment * Pi * 0.5 / segments;
                section.push_back({half * (1.0 - oy::cos(angle)), roof.rise * oy::sin(angle)});
            }
        }

        const size_t rising = section.size();

        for (size_t index = rising; index-- > 0;)
        {
            const std::array<double, 2> mirrored = {span - section[index][0], section[index][1]};

            if (mirrored[0] - section.back()[0] > 0.5)
            {
                section.push_back(mirrored);
            }
        }

        const auto place = [&](double across, double share)
        {
            return Point2{a[0] + (d[0] - a[0]) * across / span + (b[0] - a[0]) * share,
                a[1] + (d[1] - a[1]) * across / span + (b[1] - a[1]) * share};
        };
        const auto heightAt = [&](double across)
        {
            for (size_t index = 0; index + 1 < section.size(); ++index)
            {
                const std::array<double, 2> &from = section[index];
                const std::array<double, 2> &to = section[index + 1];

                if (across <= to[0] + 1.0e-9)
                {
                    const double share = to[0] - from[0] > 1.0e-9 ? (across - from[0]) / (to[0] - from[0]) : 1.0;
                    return m_foot + from[1] + (to[1] - from[1]) * std::clamp(share, 0.0, 1.0);
                }
            }

            return m_foot;
        };
        const std::string &roofTexture = texture("roof");

        for (size_t index = 0; index + 1 < section.size(); ++index)
        {
            const std::array<double, 2> &from = section[index];
            const std::array<double, 2> &to = section[index + 1];
            surface({at(place(from[0], 0.0), m_foot + from[1]), at(place(from[0], 1.0), m_foot + from[1]),
                at(place(to[0], 1.0), m_foot + to[1]), at(place(to[0], 0.0), m_foot + to[1])}, roofTexture, event);
        }

        // The end walls: on the wall from its top up to the section, the eaves' shoulders included.
        const std::string &gable = texture("gable");
        const std::vector<Point2> &inner = m_topOutline;
        const double tip = m_foot + roof.rise;
        const double eaves = std::clamp(roof.eaves, 0.0, half);

        for (const bool far : {false, true})
        {
            const Point2 &left = far ? inner[(start + 1) % 4] : inner[(start + 3) % 4];
            const Point2 &right = far ? inner[(start + 2) % 4] : inner[start];
            const double share = far ? 1.0 : 0.0;
            // Across from a's side: the near end's right corner is on a's side, the far end's on the other.
            const double rightAcross = far ? span - eaves : eaves;
            const double leftAcross = far ? eaves : span - eaves;
            const auto texel = [&](double across, double z)
            {
                return std::array<double, 2>{std::fabs(across - leftAcross), tip - z};
            };
            std::vector<OutdoorModelPoint> points = {at(left, m_top), at(right, m_top)};
            std::vector<std::array<double, 2>> texels = {texel(leftAcross, m_top), texel(rightAcross, m_top)};
            const auto corner = [&](double across)
            {
                const double z = heightAt(across);
                points.push_back(at(place(across, share), z));
                texels.push_back(texel(across, z));
            };

            if (heightAt(rightAcross) - m_top > 0.5)
            {
                corner(rightAcross);
            }

            for (size_t step = 0; step < section.size(); ++step)
            {
                const std::array<double, 2> &point = section[far ? section.size() - 1 - step : step];

                if (point[0] > eaves + 0.5 && point[0] < span - eaves - 0.5)
                {
                    corner(point[0]);
                }
            }

            if (heightAt(leftAcross) - m_top > 0.5)
            {
                corner(leftAcross);
            }

            texelFace(points, gable, texels, event);
        }
    }

    void raiseTiers(const std::vector<Point2> &outer)
    {
        const std::string &roofTexture = texture("roof");
        std::vector<Point2> ring = outer;
        double z = m_foot;

        for (const std::array<double, 2> &tier : m_part.roof.tiers)
        {
            std::vector<Point2> probe;
            const double in = tier[0];
            const double high = z + tier[1];

            if (!drawnIn(ring, in, probe))
            {
                // The last ring of a cone: to a tip over the ring's middle.
                Point2 middle = {0.0, 0.0};

                for (const Point2 &point : ring)
                {
                    middle = {middle[0] + point[0] / ring.size(), middle[1] + point[1] / ring.size()};
                }

                for (size_t index = 0; index < ring.size(); ++index)
                {
                    surface({at(ring[index], z), at(ring[(index + 1) % ring.size()], z),
                        at(middle, high)}, roofTexture, m_nameEvent);
                }

                return;
            }

            if (in <= 1.0e-9)
            {
                // A ring that only rises: an upright step in the roof.
                for (size_t index = 0; index < ring.size(); ++index)
                {
                    const size_t following = (index + 1) % ring.size();
                    surface({at(ring[index], z), at(ring[following], z), at(ring[following], high),
                        at(ring[index], high)}, roofTexture, m_nameEvent);
                }
            }

            // In steps between the moments a side shrinks to nothing, so each slope's corners follow the outline's
            // corners as they move in and meet; the height grows with the distance moved in.
            double done = 0.0;

            for (int round = 0; in - done > 1.0e-9 && round < 64; ++round)
            {
                double step = 0.0;
                const bool collapses = firstCollapse(ring, in - done, step);
                const std::vector<Point2> moved = grown(ring, -step);
                const double low = z + tier[1] * done / in;
                const double up = z + tier[1] * (done + step) / in;

                for (size_t index = 0; index < ring.size(); ++index)
                {
                    const size_t following = (index + 1) % ring.size();

                    if (lengthOf(moved[index], moved[following]) < 0.5)
                    {
                        surface({at(ring[index], low), at(ring[following], low), at(moved[index], up)},
                            roofTexture, m_nameEvent);
                    }
                    else
                    {
                        surface({at(ring[index], low), at(ring[following], low),
                            at(moved[following], up), at(moved[index], up)}, roofTexture, m_nameEvent);
                    }
                }

                ring = collapses ? withoutGoneSides(moved, in) : moved;
                done += step;
            }

            z = high;
        }

        std::vector<OutdoorModelPoint> top;

        for (const Point2 &point : ring)
        {
            top.push_back(at(point, z));
        }

        // The flat top that closes the last ring: `textures.top` when said (the Plane of Fire's huts: a cone of
        // rock with a lava mouth, ElemFhouse1S), else the roof's.
        surface(top, m_part.textures.count("top") != 0 ? texture("top") : roofTexture, m_nameEvent);
    }

    // ---- Batch O-H: a court through the part ----

    // The court's walls, from the floor to the walls' top, looking into the court.
    void raiseCourtWalls()
    {
        const std::vector<Point2> &court = m_part.court;

        for (size_t index = 0; index < court.size(); ++index)
        {
            const Point2 &from = court[index];
            const Point2 &to = court[(index + 1) % court.size()];
            // The court runs counter-clockwise: its inside lies to the left of each side.
            const double length = std::max(lengthOf(from, to), 1.0e-9);
            const std::array<double, 3> in = {-(to[1] - from[1]) / length, (to[0] - from[0]) / length, 0.0};
            const std::vector<OutdoorModelPoint> points = facing({at(to, m_floor), at(from, m_floor),
                at(from, m_top), at(to, m_top)}, in);
            texelFace(points, texture("wall"), {{0.0, m_top - m_floor}, {length, m_top - m_floor}, {length, 0.0},
                {0.0, 0.0}}, m_nameEvent);
        }
    }

    // The roof round the court: a hip's ridge ring midway between the outer walls and the court's (each ridge
    // corner the middle of a part corner and its court corner), a slope from each side of the ring down to the
    // outer eaves and one into the court; a flat roof one level ring. Eaves out over both walls, with soffits; a
    // fascia round both.
    void raiseCourtRoof()
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        const std::vector<Point2> &court = m_part.court;
        const std::vector<Point2> outer = grown(m_topOutline, roof.eaves);
        const std::vector<Point2> inner = m_part.courtEaves > 0.0 ? grown(court, -m_part.courtEaves) : court;
        const std::string &roofTexture = texture("roof");
        const std::string &trim = texture("trim");
        const bool hip = roof.form == "hip" && roof.rise > 0.0;
        const double ridgeZ = hip ? m_foot + roof.rise : m_foot;

        for (size_t index = 0; index < 4; ++index)
        {
            const size_t next = (index + 1) % 4;
            const Point2 ridgeA = {(m_topOutline[index][0] + court[index][0]) * 0.5,
                (m_topOutline[index][1] + court[index][1]) * 0.5};
            const Point2 ridgeB = {(m_topOutline[next][0] + court[next][0]) * 0.5,
                (m_topOutline[next][1] + court[next][1]) * 0.5};
            surface(facing({at(outer[index], m_foot), at(outer[next], m_foot), at(ridgeB, ridgeZ), at(ridgeA, ridgeZ)},
                {0.0, 0.0, 1.0}), roofTexture, m_nameEvent);
            surface(facing({at(inner[index], m_foot), at(inner[next], m_foot), at(ridgeB, ridgeZ), at(ridgeA, ridgeZ)},
                {0.0, 0.0, 1.0}), roofTexture, m_nameEvent);

            // Soffits under the eaves, and the fascia's bands.
            if (roof.eaves > 0.0)
            {
                surface(facing({at(m_topOutline[index], m_top), at(m_topOutline[next], m_top), at(outer[next], m_top),
                    at(outer[index], m_top)}, {0.0, 0.0, -1.0}), trim, m_nameEvent);
            }

            if (m_part.courtEaves > 0.0)
            {
                surface(facing({at(court[index], m_top), at(court[next], m_top), at(inner[next], m_top),
                    at(inner[index], m_top)}, {0.0, 0.0, -1.0}), trim, m_nameEvent);
            }

            if (m_foot > m_top + 0.5)
            {
                for (const bool courtSide : {false, true})
                {
                    const std::vector<Point2> &ring = courtSide ? inner : outer;
                    const Point2 &from = ring[index];
                    const Point2 &to = ring[next];
                    const double length = std::max(lengthOf(from, to), 1.0e-9);
                    const std::array<double, 3> left = {-(to[1] - from[1]) / length, (to[0] - from[0]) / length, 0.0};
                    surface(facing({at(from, m_top), at(to, m_top), at(to, m_foot), at(from, m_foot)}, courtSide
                        ? left : std::array<double, 3>{-left[0], -left[1], 0.0}), trim, m_nameEvent);
                }
            }
        }
    }

    // A flat top with holes cut in it (`holes`): the top in convex pieces round the holes, and under each hole a pit
    // of its `depth` with upright sides and a floor.
    void raiseHoledTop(const std::vector<Point2> &outer)
    {
        std::vector<std::vector<Point2>> pieces = {outer};

        for (const OutdoorHolePlan &hole : m_part.holes)
        {
            std::vector<std::vector<Point2>> left;

            for (const std::vector<Point2> &piece : pieces)
            {
                // What lies outside the hole: outside its first side; else inside that one and outside the next;
                // and so on, each a convex piece.
                std::vector<Point2> rest = piece;

                for (size_t side = 0; side < hole.outline.size() && rest.size() >= 3; ++side)
                {
                    const Point2 &from = hole.outline[side];
                    const Point2 &to = hole.outline[(side + 1) % hole.outline.size()];
                    // The side's outward normal (the hole is counter-clockwise).
                    const Point2 normal = {to[1] - from[1], from[0] - to[0]};
                    const std::vector<Point2> outside = clipped(rest, from, {-normal[0], -normal[1]});

                    if (outside.size() >= 3 && std::fabs(signedArea(outside)) > 1.0)
                    {
                        left.push_back(outside);
                    }

                    rest = clipped(rest, from, normal);
                }
            }

            pieces = left;
        }

        // The pieces' texels from the whole top's west and north edges, as one face over it would have them, so
        // the boards run on across the seams.
        double west = 1.0e18;
        double north = -1.0e18;

        for (const Point2 &point : outer)
        {
            west = std::min(west, point[0]);
            north = std::max(north, point[1]);
        }

        for (const std::vector<Point2> &piece : pieces)
        {
            std::vector<OutdoorModelPoint> points;
            std::vector<std::array<double, 2>> texels;

            for (const Point2 &point : piece)
            {
                points.push_back(at(point, m_foot));
                texels.push_back({point[0] - west, north - point[1]});
            }

            texelFace(points, texture("roof"), texels, m_nameEvent);
        }

        for (const OutdoorHolePlan &hole : m_part.holes)
        {
            const double floor = m_foot - hole.depth;
            const std::string &sides = textureOr("pit", "wall");
            std::vector<OutdoorModelPoint> bottom;

            for (size_t side = 0; side < hole.outline.size(); ++side)
            {
                // Seen from inside the pit: its sides look in.
                const Point2 &from = hole.outline[side];
                const Point2 &to = hole.outline[(side + 1) % hole.outline.size()];
                surface({at(to, floor), at(from, floor), at(from, m_foot), at(to, m_foot)}, sides,
                    m_nameEvent);
                bottom.push_back(at(from, floor));
            }

            surface(bottom, textureOr("pit", "trim"), m_nameEvent);
        }
    }

    // A hip or a gable roof over any convex outline (a house with cut corners, an eight-sided hall).
    // hip: the roof slopes alike from every side; over each side lies the piece of the outline that is nearer to
    // that side than to any other, rising with its distance from the side to the tip's height where the outline
    // is deepest. gable: two slopes from a ridge through the outline's middle along `ridgeDirection`; the ends
    // are closed by upright faces from the roof's foot up to the slopes.
    void raiseOutlineRoof(const std::vector<Point2> &outer, double tip)
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        const std::string &roofTexture = texture("roof");
        const size_t count = outer.size();

        if (roof.form == "gable")
        {
            const Point2 along = roof.ridgeDirection;
            const Point2 across = {-along[1], along[0]};
            double least = 1.0e18;
            double most = -1.0e18;

            for (const Point2 &point : outer)
            {
                const double side = point[0] * across[0] + point[1] * across[1];
                least = std::min(least, side);
                most = std::max(most, side);
            }

            const double half = std::max((most - least) * 0.5, 1.0);
            const double middle = (most + least) * 0.5;
            const Point2 onRidge = {across[0] * middle, across[1] * middle};
            const auto heightAt = [&](const Point2 &point)
            {
                const double side = point[0] * across[0] + point[1] * across[1] - middle;
                return m_foot + roof.rise * (1.0 - std::min(std::fabs(side) / half, 1.0));
            };

            for (const double sign : {1.0, -1.0})
            {
                // The slope on one side of the ridge.
                const std::vector<Point2> piece = clipped(outer, onRidge, {across[0] * sign, across[1] * sign});
                std::vector<OutdoorModelPoint> points;

                for (const Point2 &point : piece)
                {
                    points.push_back(at(point, heightAt(point)));
                }

                if (points.size() >= 3)
                {
                    surface(points, roofTexture, m_nameEvent);
                }
            }

            // The ends: over every side of the outline that the slopes rise above, an upright face up to them.
            const std::string &gable = texture("gable");

            for (size_t index = 0; index < count; ++index)
            {
                const Point2 &from = outer[index];
                const Point2 &to = outer[(index + 1) % count];
                const double fromSide = from[0] * across[0] + from[1] * across[1] - middle;
                const double toSide = to[0] * across[0] + to[1] * across[1] - middle;
                std::vector<OutdoorModelPoint> points = {at(from, m_foot), at(to, m_foot)};

                if (heightAt(to) - m_foot > 0.5)
                {
                    points.push_back(at(to, heightAt(to)));
                }

                if ((fromSide < -1.0e-6 && toSide > 1.0e-6) || (fromSide > 1.0e-6 && toSide < -1.0e-6))
                {
                    const double share = fromSide / (fromSide - toSide);
                    points.push_back(at({from[0] + (to[0] - from[0]) * share, from[1] + (to[1] - from[1]) * share},
                        tip));
                }

                if (heightAt(from) - m_foot > 0.5)
                {
                    points.push_back(at(from, heightAt(from)));
                }

                if (points.size() >= 3)
                {
                    surface(points, gable, m_nameEvent);
                }
            }

            return;
        }

        // Hip: the inward normal of every side, the piece of the outline nearest to each, and how deep the
        // outline is (the greatest distance any point keeps from its nearest side).
        std::vector<Point2> normals(count);

        for (size_t index = 0; index < count; ++index)
        {
            const Point2 &from = outer[index];
            const Point2 &to = outer[(index + 1) % count];
            const double length = std::max(lengthOf(from, to), 1.0e-9);
            normals[index] = {-(to[1] - from[1]) / length, (to[0] - from[0]) / length};
        }

        // With `hip` the ridge is drawn in: the slope over a side that looks along the ridge reaches the roof's
        // height after that run, the slope over a side that looks across it after half the width across the
        // ridge, and a side between them (a cut corner) after a run between the two. Without it every side
        // slopes alike. The normals are divided by their side's run, so "nearer" below is "lower on its slope".
        if (roof.hipRun > 0.0)
        {
            const Point2 across = {-roof.ridgeDirection[1], roof.ridgeDirection[0]};
            double least = 1.0e18;
            double most = -1.0e18;

            for (const Point2 &point : outer)
            {
                const double side = point[0] * across[0] + point[1] * across[1];
                least = std::min(least, side);
                most = std::max(most, side);
            }

            const double half = std::max((most - least) * 0.5, 1.0);

            for (Point2 &normal : normals)
            {
                const double alongRidge = normal[0] * roof.ridgeDirection[0] + normal[1] * roof.ridgeDirection[1];
                const double run = half + (std::min(roof.hipRun, half) - half) * alongRidge * alongRidge;
                normal = {normal[0] / run, normal[1] / run};
            }
        }

        std::vector<std::vector<Point2>> pieces(count);
        double deepest = 1.0e-9;

        for (size_t index = 0; index < count; ++index)
        {
            std::vector<Point2> piece = outer;

            for (size_t other = 0; other < count && piece.size() >= 3; ++other)
            {
                // Lower on the slope of side `index` than on that of side `other`:
                // (n_i - n_j) . p <= n_i . p_i - n_j . p_j.
                const Point2 difference = {normals[index][0] - normals[other][0],
                    normals[index][1] - normals[other][1]};
                const double length = oy::hypot(difference[0], difference[1]);

                if (other == index || length < 1.0e-12)
                {
                    continue;
                }

                const double offset = normals[index][0] * outer[index][0] + normals[index][1] * outer[index][1]
                    - normals[other][0] * outer[other][0] - normals[other][1] * outer[other][1];
                // A point of the dividing line: the one nearest the origin.
                const Point2 onLine = {difference[0] * offset / (length * length),
                    difference[1] * offset / (length * length)};
                piece = clipped(piece, onLine, difference);
            }

            for (const Point2 &point : piece)
            {
                deepest = std::max(deepest, (point[0] - outer[index][0]) * normals[index][0]
                    + (point[1] - outer[index][1]) * normals[index][1]);
            }

            pieces[index] = piece;
        }

        // With `cap` every slope stops at that height (the depth its own normal reaches there) and a flat top
        // closes the roof over what lies deeper than that on every side.
        const double capDepth = roof.cap > 0.0 && roof.cap < roof.rise ? deepest * roof.cap / roof.rise : 0.0;
        std::vector<Point2> top = outer;

        for (size_t index = 0; index < count; ++index)
        {
            const double squared = std::max(normals[index][0] * normals[index][0]
                + normals[index][1] * normals[index][1], 1.0e-18);
            const Point2 onCut = {outer[index][0] + normals[index][0] * capDepth / squared,
                outer[index][1] + normals[index][1] * capDepth / squared};

            if (capDepth > 0.0)
            {
                pieces[index] = clipped(pieces[index], onCut, normals[index]);
                top = clipped(top, onCut, {-normals[index][0], -normals[index][1]});
            }

            std::vector<OutdoorModelPoint> points;

            for (const Point2 &point : pieces[index])
            {
                const double depth = (point[0] - outer[index][0]) * normals[index][0]
                    + (point[1] - outer[index][1]) * normals[index][1];
                points.push_back(at(point, m_foot + roof.rise * std::max(depth, 0.0) / deepest));
            }

            if (points.size() >= 3)
            {
                surface(points, roofTexture, m_nameEvent);
            }
        }

        if (capDepth > 0.0 && top.size() >= 3)
        {
            std::vector<OutdoorModelPoint> points;

            for (const Point2 &point : top)
            {
                points.push_back(at(point, m_foot + roof.cap));
            }

            surface(points, roofTexture, m_nameEvent);
        }
    }

    // ---- Batch S4R: one roof over an outline that bends in, eaves along part of a wall, a parapet on chosen walls ----

    // Where the line of wall `first` moved out by `firstOut` meets that of wall `second` moved out by `secondOut`.
    Point2 meeting(size_t first, double firstOut, size_t second, double secondOut) const
    {
        const auto lineOf = [this](size_t wall, double out, Point2 &point, Point2 &direction)
        {
            const Point2 &left = m_topOutline[wall];
            const Point2 &right = m_topOutline[(wall + 1) % m_count];
            const double length = std::max(lengthOf(left, right), 1.0e-9);
            direction = {(right[0] - left[0]) / length, (right[1] - left[1]) / length};
            point = {left[0] + direction[1] * out, left[1] - direction[0] * out};
        };
        Point2 a = {0.0, 0.0};
        Point2 u = {0.0, 0.0};
        Point2 b = {0.0, 0.0};
        Point2 v = {0.0, 0.0};
        lineOf(first, firstOut, a, u);
        lineOf(second, secondOut, b, v);
        const double cross = u[0] * v[1] - u[1] * v[0];

        if (std::fabs(cross) < 1.0e-6)
        {
            return b;
        }

        const double along = ((b[0] - a[0]) * v[1] - (b[1] - a[1]) * v[0]) / cross;
        return {a[0] + u[0] * along, a[1] + u[1] * along};
    }

    // The roof's foot with the eaves only over the stretches `eaves_walls` names: along each wall the eaves line
    // where a stretch has eaves, the wall's own line elsewhere, joined by short sides square to the wall.
    std::vector<Point2> eavesRegion() const
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        // Per wall: the offsets out from it along its length, as [from, out] runs.
        std::vector<std::vector<std::array<double, 2>>> runs(m_count);

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            const double length = lengthOf(m_topOutline[wall], m_topOutline[(wall + 1) % m_count]);
            std::vector<std::array<double, 2>> stretches;

            if (wall < roof.eavesStretches.size() && !roof.eavesStretches[wall].empty())
            {
                stretches = roof.eavesStretches[wall];
            }
            else if (eavesOf(wall) > 0.0)
            {
                stretches = {{0.0, length}};
            }

            double place = 0.0;

            for (const std::array<double, 2> &stretch : stretches)
            {
                if (stretch[0] > place + 0.5)
                {
                    runs[wall].push_back({place, 0.0});
                }

                runs[wall].push_back({std::max(stretch[0], place), eavesOf(wall)});
                place = stretch[1];
            }

            if (place < length - 0.5)
            {
                runs[wall].push_back({place, 0.0});
            }
        }

        std::vector<Point2> points;

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            const size_t previous = (wall + m_count - 1) % m_count;
            points.push_back(meeting(previous, runs[previous].back()[1], wall, runs[wall].front()[1]));

            for (size_t run = 1; run < runs[wall].size(); ++run)
            {
                const Point2 &left = m_topOutline[wall];
                const Point2 &right = m_topOutline[(wall + 1) % m_count];
                const double length = std::max(lengthOf(left, right), 1.0e-9);
                const Point2 u = {(right[0] - left[0]) / length, (right[1] - left[1]) / length};
                const double along = runs[wall][run][0];

                for (const double out : {runs[wall][run - 1][1], runs[wall][run][1]})
                {
                    points.push_back({left[0] + u[0] * along + u[1] * out, left[1] + u[1] * along - u[0] * out});
                }
            }
        }

        return points;
    }

    // One roof over the whole outline (core/OutdoorRoofCover): flat, or hip or gable slopes from the walls' lines
    // moved out by their eaves, cut to the stretches that have eaves; the soffit under the eaves, the fascia round
    // the roof's foot, and upright faces where the roof stands over its foot at the outline (gable ends, the sides
    // of a stretch without eaves).
    void raiseCoverRoof()
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        const std::string &roofTexture = texture("roof");
        const std::string &trim = texture("trim");
        std::vector<double> insets(m_count, 0.0);

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            insets[wall] = -eavesOf(wall);
        }

        const std::vector<Point2> walls = outdoorOffsetOutline(m_topOutline, insets);
        const std::vector<Point2> region = roof.eavesPartial ? eavesRegion() : walls;

        if (roof.eaves > 0.0)
        {
            for (const std::vector<Point2> &piece : areaBetween(region, m_topOutline))
            {
                std::vector<OutdoorModelPoint> points;

                for (const Point2 &point : piece)
                {
                    points.push_back(at(point, m_top));
                }

                surface(facing(points, {0.0, 0.0, -1.0}), trim, m_nameEvent);
            }
        }

        if (roof.fascia > 0.0)
        {
            for (size_t index = 0; index < region.size(); ++index)
            {
                const Point2 &from = region[index];
                const Point2 &to = region[(index + 1) % region.size()];
                const double length = lengthOf(from, to);

                if (length >= 1.0)
                {
                    texelFace({at(from, m_top), at(to, m_top), at(to, m_foot), at(from, m_foot)}, trim,
                        {{0.0, roof.fascia}, {length, roof.fascia}, {length, 0.0}, {0.0, 0.0}}, m_nameEvent);
                }
            }
        }

        if (roof.form == "flat" || roof.rise <= 0.0)
        {
            for (const std::vector<Point2> &piece : convexPartsOf(region))
            {
                std::vector<OutdoorModelPoint> points;

                for (const Point2 &point : piece)
                {
                    points.push_back(at(point, m_foot));
                }

                surface(points, roofTexture, m_nameEvent);
            }

            return;
        }

        // The ridge's way: a box's as its own roof has it, an outline's as said; else each piece's longest side.
        const bool gable = roof.form == "gable";
        std::optional<Point2> ridge;

        if (m_part.shape == "box")
        {
            const double first = lengthOf(m_topOutline[0], m_topOutline[1]);
            const double second = lengthOf(m_topOutline[1], m_topOutline[2]);
            const bool alongFirst = roof.along == 'x' || (roof.along != 'y' && first >= second);
            const Point2 &from = m_topOutline[alongFirst ? 0 : 1];
            const Point2 &to = m_topOutline[alongFirst ? 1 : 2];
            const double length = std::max(lengthOf(from, to), 1.0e-9);
            ridge = Point2{(to[0] - from[0]) / length, (to[1] - from[1]) / length};
        }
        else if (roof.along != 0)
        {
            ridge = roof.ridgeDirection;
        }

        const RoofCover cover(walls, gable, ridge, gable ? 0.0 : roof.hipRun, roof.slope > 0.0);
        const double slope = roof.slope > 0.0 ? roof.slope : roof.rise / std::max(cover.deepest(), 1.0e-9);

        for (const RoofCoverFace &face : cover.faces(region))
        {
            std::vector<OutdoorModelPoint> points;

            for (const Point2 &point : face.points)
            {
                points.push_back(at(point, m_foot + slope * std::max(cover.runOf(face, point), 0.0)));
            }

            surface(points, roofTexture, m_nameEvent);
        }

        for (const RoofProfileFace &profile : cover.profiles(region))
        {
            std::vector<OutdoorModelPoint> points;

            for (const std::array<double, 3> &point : profile)
            {
                points.push_back({point[0], point[1], m_foot + slope * point[2]});
            }

            if (points.size() >= 3 && slope * cover.deepest() > 0.5)
            {
                surface(points, texture("gable"), m_nameEvent);
            }
        }
    }

    // A parapet on the stretches `parapet_walls` names (round every wall when left out, on an outline that bends
    // in): each stretch a low wall `ParapetThickness` thick standing on the flat top, mitred where two meet at a
    // corner, its ends closed where it stops, its top in the `parapet_top` texture (else `parapet`: Ravenshore's
    // roof walks t14a05b over t14d01); merlons on it with `battlements`. The top is the whole outline.
    void raiseParapetStretches()
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        const std::string &wallTexture = texture("parapet");
        const double high = m_top + roof.parapet;
        const double kerb = roof.battlements ? m_top + roof.parapet * 0.25 : high;

        for (const std::vector<Point2> &piece : convexPartsOf(m_topOutline))
        {
            std::vector<OutdoorModelPoint> floor;

            for (const Point2 &point : piece)
            {
                floor.push_back(at(point, m_top));
            }

            surface(floor, texture("roof"), m_nameEvent);
        }

        std::vector<std::vector<std::array<double, 2>>> stretches = roof.parapetStretches;

        if (stretches.empty())
        {
            stretches.resize(m_count);

            for (size_t wall = 0; wall < m_count; ++wall)
            {
                stretches[wall] = {{0.0, lengthOf(m_topOutline[wall], m_topOutline[(wall + 1) % m_count])}};
            }
        }

        const auto lengthOfWall = [this](size_t wall)
        {
            return lengthOf(m_topOutline[wall], m_topOutline[(wall + 1) % m_count]);
        };
        const auto reachesEnd = [&](size_t wall)
        {
            return !stretches[wall].empty() && stretches[wall].back()[1] >= lengthOfWall(wall) - 0.5;
        };
        const auto reachesStart = [&](size_t wall)
        {
            return !stretches[wall].empty() && stretches[wall].front()[0] <= 0.5;
        };

        for (size_t wall = 0; wall < m_count; ++wall)
        {
            const size_t previous = (wall + m_count - 1) % m_count;
            const size_t next = (wall + 1) % m_count;
            const double length = lengthOfWall(wall);

            for (size_t index = 0; index < stretches[wall].size(); ++index)
            {
                const std::array<double, 2> &stretch = stretches[wall][index];
                // Mitred into the parapet of the wall before or after where both reach their shared corner.
                const bool mitreStart = index == 0 && stretch[0] <= 0.5 && reachesEnd(previous);
                const bool mitreEnd = index + 1 == stretches[wall].size() && stretch[1] >= length - 0.5
                    && reachesStart(next);
                const Point2 outFrom = onWall(wall, stretch[0]);
                const Point2 outTo = onWall(wall, stretch[1]);
                const Point2 inFrom = mitreStart ? meeting(previous, -ParapetThickness, wall, -ParapetThickness)
                    : stretch[0] <= 0.5 ? meeting(previous, 0.0, wall, -ParapetThickness)
                    : onWall(wall, stretch[0], ParapetThickness);
                const Point2 inTo = mitreEnd ? meeting(wall, -ParapetThickness, next, -ParapetThickness)
                    : stretch[1] >= length - 0.5 ? meeting(wall, -ParapetThickness, next, 0.0)
                    : onWall(wall, stretch[1], ParapetThickness);
                parapetBlock(outFrom, outTo, inFrom, inTo, m_top, kerb, !mitreStart, !mitreEnd, wallTexture);

                if (!roof.battlements)
                {
                    continue;
                }

                // Merlons along the stretch, a block at each end, gaps as wide between them.
                const double run = lengthOf(outFrom, outTo);
                const int merlons = std::max(1, static_cast<int>(std::floor((run / MerlonWidth + 1.0) * 0.5)));
                const double pitch = merlons > 1 ? (run - MerlonWidth) / (merlons - 1) : 0.0;
                const auto along = [](const Point2 &from, const Point2 &to, double share)
                {
                    return Point2{from[0] + (to[0] - from[0]) * share, from[1] + (to[1] - from[1]) * share};
                };

                for (int merlon = 0; merlon < merlons; ++merlon)
                {
                    const double from = (merlons > 1 ? merlon * pitch : (run - MerlonWidth) * 0.5) / run;
                    const double to = from + std::min(MerlonWidth, run) / run;
                    parapetBlock(along(outFrom, outTo, from), along(outFrom, outTo, to), along(inFrom, inTo, from),
                        along(inFrom, inTo, to), kerb, high, true, true, wallTexture);
                }
            }
        }
    }

    // A block of parapet from `low` to `high`: its outer and inner faces, its top and the ends asked for.
    void parapetBlock(const Point2 &outFrom, const Point2 &outTo, const Point2 &inFrom, const Point2 &inTo, double low,
        double high, bool startEnd, bool endEnd, const std::string &textureName)
    {
        const double height = high - low;
        const auto upright = [&](const Point2 &from, const Point2 &to)
        {
            const double width = lengthOf(from, to);

            if (width >= 0.5)
            {
                texelFace({at(from, low), at(to, low), at(to, high), at(from, high)}, textureName,
                    {{0.0, height}, {width, height}, {width, 0.0}, {0.0, 0.0}}, m_nameEvent);
            }
        };
        upright(outFrom, outTo);
        upright(inTo, inFrom);

        if (startEnd)
        {
            upright(inFrom, outFrom);
        }

        if (endEnd)
        {
            upright(outTo, inTo);
        }

        surface({at(outFrom, high), at(outTo, high), at(inTo, high), at(inFrom, high)},
            textureOr("parapet_top", "parapet"), m_nameEvent);
    }

    // A flat roof behind a parapet: the walls go on up as a low wall round the roof, with merlons when asked.
    void raiseParapet()
    {
        const OutdoorRoofPlan &roof = m_part.roof;
        const std::string &wallTexture = texture("parapet");
        const uint16_t event = m_nameEvent;
        const std::vector<Point2> &outer = m_topOutline;
        const std::vector<Point2> inner = grown(outer, -ParapetThickness);
        const double high = m_top + roof.parapet;
        std::vector<OutdoorModelPoint> floor;

        for (const Point2 &point : inner)
        {
            floor.push_back(at(point, m_top));
        }

        surface(floor, texture("roof"), event);

        if (!roof.battlements)
        {
            band(outer, m_top, high, false, wallTexture);
            band(inner, m_top, high, true, wallTexture);
            ring(inner, outer, high, false, wallTexture);
            return;
        }

        // Merlons: blocks of the parapet's height with gaps as wide between them, a block at each end of a side;
        // under the gaps the parapet is a kerb of a quarter of its height.
        const double kerb = m_top + roof.parapet * 0.25;
        band(outer, m_top, kerb, false, wallTexture);
        band(inner, m_top, kerb, true, wallTexture);
        ring(inner, outer, kerb, false, wallTexture);

        for (size_t index = 0; index < m_count; ++index)
        {
            const size_t next = (index + 1) % m_count;
            const double outerLength = lengthOf(outer[index], outer[next]);
            const int merlons = std::max(1, static_cast<int>(std::floor((outerLength / MerlonWidth + 1.0) * 0.5)));
            const double pitch = merlons > 1 ? (outerLength - MerlonWidth) / (merlons - 1) : 0.0;

            for (int merlon = 0; merlon < merlons; ++merlon)
            {
                const double from = (merlons > 1 ? merlon * pitch : (outerLength - MerlonWidth) * 0.5) / outerLength;
                const double to = from + std::min(MerlonWidth, outerLength) / outerLength;
                const auto along = [&](const std::vector<Point2> &outline, double share)
                {
                    return Point2{outline[index][0] + (outline[next][0] - outline[index][0]) * share,
                        outline[index][1] + (outline[next][1] - outline[index][1]) * share};
                };
                const Point2 outFrom = along(outer, from);
                const Point2 outTo = along(outer, to);
                const Point2 inFrom = along(inner, from);
                const Point2 inTo = along(inner, to);
                const double height = high - kerb;
                const double width = lengthOf(outFrom, outTo);
                const std::vector<std::array<double, 2>> texels = {{0.0, height}, {width, height}, {width, 0.0},
                    {0.0, 0.0}};
                const std::vector<std::array<double, 2>> sideTexels = {{0.0, height}, {ParapetThickness, height},
                    {ParapetThickness, 0.0}, {0.0, 0.0}};
                texelFace({at(outFrom, kerb), at(outTo, kerb), at(outTo, high), at(outFrom, high)},
                    wallTexture, texels, event);
                texelFace({at(inTo, kerb), at(inFrom, kerb), at(inFrom, high), at(inTo, high)}, wallTexture,
                    texels, event);
                texelFace({at(outTo, kerb), at(inTo, kerb), at(inTo, high), at(outTo, high)}, wallTexture,
                    sideTexels, event);
                texelFace({at(inFrom, kerb), at(outFrom, kerb), at(outFrom, high), at(inFrom, high)},
                    wallTexture, sideTexels, event);
                surface({at(outFrom, high), at(outTo, high), at(inTo, high), at(inFrom, high)},
                    wallTexture, event);
            }
        }
    }

    OutdoorModelBuilder &m_builder;
    const LoweredOutdoorMap *m_pLand;
    OutdoorBuildingPlan &m_building;
    const size_t m_partIndex;
    const OutdoorPartPlan &m_part;
    const size_t m_count;
    const double m_floor;
    // The walls' top and the roof's foot over it; while the roof is raised over terraces, the last terrace's.
    double m_top;
    double m_foot;
    // The event of this part's faces that are no door: the part's own, else the building's name.
    const uint16_t m_nameEvent;
    // The outline at the top of the walls: the part's own, drawn in or out by its `taper` or `batter`.
    std::vector<Point2> m_topOutline;
    bool m_capturing = false;
    std::vector<Captured> m_captured;
    // A door on a battered wall being raised: its piece stands upright at the wall's foot.
    bool m_upright = false;
    // S8d: on the wall being raised, where doors on a `sill` reach up past their row: [from, to] along it and
    // [low, high]; the rows' pieces there begin over them.
    std::vector<std::array<double, 4>> m_doorHoles;
};
}

std::vector<std::string> outdoorKitNames(const std::string &world)
{
    std::vector<std::string> names;

    for (const Kit &kit : kits())
    {
        if (world == kit.pWorld)
        {
            names.push_back(kit.pName);
        }
    }

    return names;
}

std::vector<OutdoorBuildingPlan> readOutdoorBuildings(
    const Project &project,
    const std::string &world,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings,
    const OutdoorDoorPictures *pDoorPictures)
{
    const OutdoorGridScope gridScope(project);
    std::vector<OutdoorBuildingPlan> buildings;
    const YAML::Node sketch = project.document(SketchFile);
    const YAML::Node plan = project.document("plan.yml");
    const YAML::Node districts = childOf(sketch, "districts");
    size_t withoutFootprint = 0;
    size_t noForm = 0;

    for (size_t district = 0; districts.IsDefined() && districts.IsSequence() && district < districts.size();
         ++district)
    {
        const YAML::Node districtNode = districts[district];
        const YAML::Node plots = childOf(districtNode, "plots");

        for (size_t index = 0; plots.IsDefined() && plots.IsSequence() && index < plots.size(); ++index)
        {
            const YAML::Node plot = plots[index];
            const std::string path = "districts[" + std::to_string(district) + "].plots[" + std::to_string(index)
                + "]";
            const std::string form = textOf(plot, "form", "house");

            if (form == "none")
            {
                ++noForm;
                continue;
            }

            std::array<double, 4> rectangle = {};

            if (!sketchPlotRectangle(plan, plot, rectangle))
            {
                ++withoutFootprint;
                continue;
            }

            OutdoorBuildingPlan building;
            building.id = textOf(plot, "building")
                + (childOf(plot, "index").IsDefined() ? "#" + textOf(plot, "index") : std::string());
            BuildingReader reader(world, plot, path, rectangle, issues);
            reader.useDoorPictures(pDoorPictures, warnings);

            if (reader.read(building))
            {
                buildings.push_back(building);
            }
        }
    }

    // Buildings the plan does not list, drawn among the sketch's structures: the same words as a plot, standing on
    // their own rectangle.
    const YAML::Node structures = childOf(sketch, "structures");

    for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size(); ++index)
    {
        const YAML::Node structure = structures[index];

        if (textOf(structure, "kind") != "building")
        {
            continue;
        }

        const std::string path = "structures[" + std::to_string(index) + "]";
        Point2 corner = {0.0, 0.0};
        Point2 size = {0.0, 0.0};

        if (!pointOf(childOf(structure, "at"), corner) || !pointOf(childOf(structure, "size"), size) || size[0] <= 0.0
            || size[1] <= 0.0 || corner[0] < 0.0 || corner[1] < 0.0 || corner[0] + size[0] > outdoorNodeCount()
            || corner[1] + size[1] > outdoorNodeCount())
        {
            issues.push_back({SketchFile, path, "a structure of kind building has `at: [x, y]` (the north-west "
                "corner of the ground it stands on, in cells) and `size: [width, depth]` in cells, inside the map",
                "building"});
            continue;
        }

        OutdoorBuildingPlan building;
        building.id = textOf(structure, "id");
        BuildingReader reader(world, structure, path, {corner[0], corner[1], corner[0] + size[0],
            corner[1] + size[1]}, issues);
        reader.useDoorPictures(pDoorPictures, warnings);

        if (reader.read(building))
        {
            buildings.push_back(building);
        }
    }

    if (withoutFootprint != 0)
    {
        warnings.push_back("buildings: " + std::to_string(withoutFootprint) + " plots are not raised: their "
            "building has no `footprint_cells` in plan.yml");
    }

    if (noForm != 0)
    {
        warnings.push_back("buildings: " + std::to_string(noForm) + " plots with `form: none` raise nothing (what "
            "stands there is drawn in `structures`, or not at all)");
    }

    return buildings;
}

std::vector<double> outdoorBayEdges(const OutdoorPartPlan &part, size_t wall, bool upper)
{
    std::vector<double> edges = bayEdgesOf(part, wall, upper);
    const double length = std::max(edges.back(), 1.0e-9);

    for (double &edge : edges)
    {
        edge /= length;
    }

    return edges;
}

Game::OutdoorBModel raiseOutdoorBuilding(OutdoorBuildingPlan &plan, const OutdoorWallTiles *pWallTiles,
    const LoweredOutdoorMap *pLand)
{
    Game::OutdoorBModel model;
    model.name = plan.id;
    model.secondaryName = plan.id;
    OutdoorModelBuilder builder(model, pWallTiles);

    plan.faceParts.clear();

    for (size_t part = 0; part < plan.parts.size(); ++part)
    {
        const size_t from = model.faces.size();
        PartRaiser(builder, plan, part, pLand).raise();

        for (size_t face = from; face < model.faces.size(); ++face)
        {
            const std::map<std::string, uint32_t>::const_iterator liquid =
                plan.parts[part].liquids.find(model.faces[face].textureName);

            if (liquid != plan.parts[part].liquids.end())
            {
                model.faces[face].attributes |= liquid->second;
            }
        }

        plan.faceParts.resize(model.faces.size(),
            "part:" + (plan.parts[part].id.empty() ? std::to_string(part) : plan.parts[part].id));
    }

    builder.finish();
    return model;
}

OutdoorDoorPictures parseOutdoorDoorPictures(const std::vector<std::string> &texts)
{
    OutdoorDoorPictures pictures;

    for (const std::string &text : texts)
    {
        // One row a line (tools/xeen/texture_classes.py): only the rows with a door role are read, so a build reads
        // a few hundred of the thousands.
        std::string rows = "textures:\n";
        size_t start = 0;

        while (start < text.size())
        {
            const size_t end = std::min(text.find('\n', start), text.size());
            const std::string line = text.substr(start, end - start);

            if (line.find(" door: ") != std::string::npos || line.find("{door: ") != std::string::npos)
            {
                rows += line + "\n";
            }

            start = end + 1;
        }

        YAML::Node root;

        try
        {
            root = YAML::Load(rows);
        }
        catch (const YAML::Exception &)
        {
            continue;
        }

        const YAML::Node textures = root["textures"];

        for (YAML::const_iterator entry = textures.begin(); textures.IsMap() && entry != textures.end(); ++entry)
        {
            const YAML::Node &row = entry->second;

            if (!row.IsMap() || !row["door"] || !row["door"].IsScalar())
            {
                continue;
            }

            std::string name = entry->first.Scalar();
            std::transform(name.begin(), name.end(), name.begin(),
                [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
            OutdoorDoorPicture picture;
            picture.door = row["door"].Scalar();
            const YAML::Node size = row["size"];
            double number = 0.0;

            if (size.IsSequence() && size.size() == 2 && numberOfNode(size[0], number))
            {
                picture.size[0] = static_cast<int>(number);
                picture.size[1] = numberOfNode(size[1], number) ? static_cast<int>(number) : 0;
            }

            if (row["twin"] && row["twin"].IsScalar())
            {
                picture.twin = row["twin"].Scalar();
                std::transform(picture.twin.begin(), picture.twin.end(), picture.twin.begin(),
                    [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
            }

            pictures[name] = picture;
        }
    }

    return pictures;
}

OutdoorDoorPictures readOutdoorDoorPictures(const std::filesystem::path &assetRoot, const std::string &world)
{
    std::vector<std::string> texts;

    for (const std::filesystem::path &folder : {assetRoot / "engine" / "models",
             assetRoot / "worlds" / world / "models"})
    {
        std::string text;

        if (!assetRoot.empty() && readTextFile(folder / "texture_classes.yml", text))
        {
            texts.push_back(text);
        }
    }

    return parseOutdoorDoorPictures(texts);
}

std::set<std::string> outdoorTextureNames(const std::filesystem::path &assetRoot, const std::string &world,
    const std::filesystem::path &mountRoot)
{
    std::set<std::string> names;
    std::error_code error;
    std::vector<std::filesystem::path> parents = {assetRoot / "worlds" / world, assetRoot / "engine"};

    if (!mountRoot.empty())
    {
        parents.insert(parents.end(), {mountRoot, mountRoot / "engine", mountRoot / "worlds" / world});
    }

    for (const std::filesystem::path &parent : parents)
    {
        for (std::filesystem::directory_iterator folder(parent, error), end; !error && folder != end;
             folder.increment(error))
        {
            const std::string folderName = folder->path().filename().string();

            if (!folder->is_directory(error) || folderName.rfind("textures", 0) != 0)
            {
                continue;
            }

            std::error_code inner;

            for (std::filesystem::directory_iterator file(folder->path(), inner), last; !inner && file != last;
                 file.increment(inner))
            {
                std::string extension = file->path().extension().string();
                std::string name = file->path().stem().string();
                std::transform(extension.begin(), extension.end(), extension.begin(), [](unsigned char character)
                {
                    return static_cast<char>(std::tolower(character));
                });
                std::transform(name.begin(), name.end(), name.begin(), [](unsigned char character)
                {
                    return static_cast<char>(std::tolower(character));
                });

                if (extension == ".oytex" || extension == ".png" || extension == ".bmp" || extension == ".pcx")
                {
                    names.insert(name);
                }
            }
        }

        error.clear();
    }

    // Liquids (engine/liquids/liquids.yml): a face that names one has no picture, the game draws the liquid.
    std::string liquids;

    if (!names.empty() && readTextFile(assetRoot / "engine" / "liquids" / "liquids.yml", liquids))
    {
        size_t at = 0;

        while ((at = liquids.find("texture_names:", at)) != std::string::npos)
        {
            const size_t open = liquids.find('[', at);
            const size_t close = liquids.find(']', at);
            at += 14;

            if (open == std::string::npos || close == std::string::npos || close < open)
            {
                continue;
            }

            std::string name;

            for (size_t index = open + 1; index <= close; ++index)
            {
                const char character = liquids[index];

                if (character == ',' || character == ']')
                {
                    if (!name.empty())
                    {
                        names.insert(name);
                    }

                    name.clear();
                }
                else if (character != ' ')
                {
                    name.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
                }
            }
        }
    }

    return names;
}

void checkOutdoorBuildingTextures(
    const std::vector<OutdoorBuildingPlan> &buildings,
    const std::set<std::string> &known,
    const std::string &world,
    std::vector<ProjectIssue> &issues)
{
    if (known.empty())
    {
        return;
    }

    // Each missing texture once, with the buildings that name it.
    std::map<std::string, std::vector<std::string>> missing;

    for (const OutdoorBuildingPlan &building : buildings)
    {
        for (const OutdoorPartPlan &part : building.parts)
        {
            std::set<std::string> used = {"base", "roof", "trim"};

            for (const std::vector<std::vector<std::string>> *pRows : {&part.bays, &part.upperBays})
            {
                for (const std::vector<std::string> &bays : *pRows)
                {
                    used.insert(bays.begin(), bays.end());
                }
            }

            if (part.roof.form == "gable" || part.roof.form == "lean_to" || part.roof.form == "vault")
            {
                used.insert("gable");
            }

            if (part.roof.ridge > 0.0)
            {
                used.insert("ridge");
            }

            if (part.roof.parapet > 0.0)
            {
                used.insert("parapet");
            }

            // The roles of this batch's forms, each where the part names it (else another role stands in).
            for (const char *pRole : {"post", "sill", "porch", "step", "railing", "rail", "sign_edge", "pit", "pent"})
            {
                if (part.textures.contains(pRole))
                {
                    used.insert(pRole);
                }
            }

            for (const OutdoorWallSignPlan &sign : part.signs)
            {
                used.insert(sign.texture);
            }

            for (const std::string &role : used)
            {
                const std::map<std::string, std::string>::const_iterator found = part.textures.find(role);

                if (found == part.textures.end() && (role == "base" || role == "roof" || role == "trim"
                    || role == "gable" || role == "ridge" || role == "parapet"))
                {
                    continue;
                }

                // A bay's word that is no role is a texture's own name.
                const std::string &written = found == part.textures.end() ? role : found->second;
                std::string name = written;
                std::transform(name.begin(), name.end(), name.begin(), [](unsigned char character)
                {
                    return static_cast<char>(std::tolower(character));
                });

                if (!known.contains(name))
                {
                    std::vector<std::string> &where = missing[written + (written == role ? "" : " (" + role + ")")];

                    if (std::find(where.begin(), where.end(), building.id) == where.end())
                    {
                        where.push_back(building.id);
                    }
                }
            }
        }
    }

    for (const std::pair<const std::string, std::vector<std::string>> &entry : missing)
    {
        std::string where = joined(std::vector<std::string>(entry.second.begin(),
            entry.second.begin() + std::min<size_t>(entry.second.size(), 4)));

        if (entry.second.size() > 4)
        {
            where += " and " + std::to_string(entry.second.size() - 4) + " more";
        }

        issues.push_back({SketchFile, "districts", "the world " + world + " has no texture " + entry.first
            + ", named by " + where + ": `oymap assets <text> --kind texture --world " + world
            + "` lists the textures it has; the kits of this world are " + joined(outdoorKitNames(world)),
            "texture"});
    }
}
void checkOutdoorModelTextures(
    const std::vector<Game::OutdoorBModel> &models,
    const std::set<std::string> &known,
    const std::string &world,
    std::vector<ProjectIssue> &issues)
{
    if (known.empty())
    {
        return;
    }

    std::map<std::string, std::string> missing;

    for (const Game::OutdoorBModel &model : models)
    {
        for (const Game::OutdoorBModelFace &face : model.faces)
        {
            std::string name = face.textureName;
            std::transform(name.begin(), name.end(), name.begin(), [](unsigned char character)
            {
                return static_cast<char>(std::tolower(character));
            });
            if (!known.contains(name) && !missing.contains(face.textureName))
            {
                missing[face.textureName] = model.name;
            }
        }
    }

    for (const std::pair<const std::string, std::string> &entry : missing)
    {
        issues.push_back({SketchFile, "structures", "the world " + world + " has no texture `" + entry.first
            + "`, named by " + entry.second + ": `oymap assets <text> --kind texture --world " + world
            + "` lists the textures it has", "texture"});
    }
}
}
