#include "core/ChestKinds.h"

#include "core/CoreMath.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <tuple>

namespace OpenYAMM::Studio
{
std::optional<ChestKind> chestKindOf(const std::string &name)
{
    ChestKind kind;

    if (name == "ch1" || name == "ch2" || name == "ch3" || name == "ch4" || name == "ch5")
    {
        kind.frontLeft = name + "frle";
        kind.frontMiddle = name + (name == "ch5" ? "frnt" : "frntb");
        kind.frontRight = name + "frre";
        kind.side = name + "side";
        kind.topLeft = name + (name == "ch5" ? "toplb" : "tople");
        kind.topMiddle = name + (name == "ch4" ? "top" : "topb");
        kind.topRight = name + (name == "ch5" ? "toprb" : "topre");
        return kind;
    }

    const bool gt = name == "7gt002" || name == "gt002";
    const bool numbered = name.size() == 5 && name.starts_with("ch00") && name[4] >= '1' && name[4] <= '6';

    if (!gt && !numbered)
    {
        return std::nullopt;
    }

    // 7gt002 and gt002 by the letters a (middle), b (ends), c (short ends), e (front slope), g (short ends' upper
    // strip); the ch001 to ch006 families each one letter on (b, c, d, f, h).
    const auto letter = [&name, gt](char gtLetter)
    {
        return name + std::string(1, static_cast<char>(gt ? gtLetter : gtLetter + 1));
    };

    kind.frontLeft = letter('b');
    kind.frontMiddle = letter('a');
    kind.frontRight = kind.frontLeft;
    kind.side = letter('c');
    kind.topLeft = kind.frontLeft;
    kind.topMiddle = kind.frontMiddle;
    kind.topRight = kind.frontLeft;
    kind.sloped = true;
    kind.slopeMiddle = letter('e');
    kind.sideTop = letter('g');
    kind.size = {96.0, 64.0, 80.0};
    return kind;
}

std::string chestKindList()
{
    return "the kinds are ch1, ch2, ch3, ch4 and ch5 (MM6's flat-lidded chests), 7gt002 (MM7's), gt002 (MM8's) and "
        "ch001 to ch006 (chests with a sloping lid)";
}

std::string chestFamilyOfMiddle(const std::string &texture)
{
    std::string lower = texture;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c)
    {
        return static_cast<char>(std::tolower(c));
    });

    for (const char *pName : {"ch1", "ch2", "ch3", "ch4", "ch5", "7gt002", "gt002", "ch001", "ch002", "ch003",
             "ch004", "ch005", "ch006"})
    {
        const std::optional<ChestKind> kind = chestKindOf(pName);

        if (kind && (lower == kind->frontMiddle || (!kind->sloped && lower == std::string(pName) + "frnt")))
        {
            return pName;
        }
    }

    return {};
}

bool isChestTexture(const std::string &texture)
{
    std::string lower = texture;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c)
    {
        return static_cast<char>(std::tolower(c));
    });

    // The kinds' own pictures (chestKindOf), and MM6's lid and back variants (ch3tpbv, ch1bkre).
    for (const char *pName : {"ch1", "ch2", "ch3", "ch4", "ch5", "7gt002", "gt002", "ch001", "ch002", "ch003",
             "ch004", "ch005", "ch006"})
    {
        const std::optional<ChestKind> kind = chestKindOf(pName);

        for (const std::string &picture : {kind->frontLeft, kind->frontMiddle, kind->frontRight, kind->side,
                 kind->topLeft, kind->topMiddle, kind->topRight, kind->slopeMiddle, kind->sideTop})
        {
            if (!picture.empty() && lower == picture)
            {
                return true;
            }
        }

        const std::string family = pName;

        const std::string rest = lower.size() > 3 ? lower.substr(3) : std::string();

        if (family.size() == 3 && lower.starts_with(family)
            && (rest.starts_with("fr") || rest.starts_with("tp") || rest.starts_with("top") || rest.starts_with("bk")
                || rest.starts_with("side")))
        {
            return true;
        }
    }

    return false;
}

std::string defaultChestKind(const std::string &styleWorld)
{
    return styleWorld == "mm8" ? "gt002" : styleWorld == "mm7" || styleWorld == "xeen" ? "7gt002" : "ch1";
}

std::vector<ChestFace> chestKindFaces(const ChestKind &kind, const std::array<double, 3> &size, double bottom,
    double top)
{
    using Corner = std::array<double, 3>;
    std::vector<ChestFace> faces;
    const double halfWidth = size[0] / 2.0;
    const double halfDepth = size[1] / 2.0;
    const double body = kind.sloped ? top - 16.0 : top;
    // MM6's ends are textures 16 wide of their own; MM7's and MM8's the first and last 16 columns of one 64 wide.
    const int endWidth = kind.sloped ? 64 : 16;
    const auto add = [&faces](ChestPart part, double sign, const std::string &texture, int width,
                         std::vector<Corner> corners, std::vector<std::array<double, 2>> texels, const Corner &normal)
    {
        ChestFace face;
        face.part = part;
        face.sign = sign;
        face.texture = texture;
        face.width = width;
        face.corners = std::move(corners);
        face.texels = std::move(texels);
        face.normal = normal;
        faces.push_back(std::move(face));
    };
    // A strip across the chest's width: left end, middle and right end, from `leftAcross` (where the viewer of this
    // face has the left end) to the other side. `corner(across, 0)` is on the strip's edge where the picture's rows
    // are `vFrom`, `corner(across, 1)` on the other edge (`vTo`).
    const auto addStrip = [&](ChestPart part, double sign, const auto &corner, double leftAcross, const Corner &normal,
                              const std::string &left, const std::string &middle, const std::string &right,
                              double vFrom, double vTo)
    {
        const double direction = leftAcross > 0.0 ? -1.0 : 1.0;
        const double full = size[0];
        const std::array<std::tuple<double, double, std::string, double, int>, 3> pieces = {{
            {0.0, 16.0, left, 0.0, endWidth},
            {16.0, full - 16.0, middle, 0.0, 64},
            {full - 16.0, full, right, kind.sloped ? 48.0 : 0.0, endWidth}}};

        for (const std::tuple<double, double, std::string, double, int> &piece : pieces)
        {
            const double from = leftAcross + direction * std::get<0>(piece);
            const double to = leftAcross + direction * std::get<1>(piece);
            const double uFrom = std::get<3>(piece);
            const double uTo = uFrom + std::get<1>(piece) - std::get<0>(piece);
            add(part, sign, std::get<2>(piece), std::get<4>(piece),
                {corner(from, 0), corner(to, 0), corner(to, 1), corner(from, 1)},
                {{uFrom, vFrom}, {uTo, vFrom}, {uTo, vTo}, {uFrom, vTo}}, normal);
        }
    };

    // The front (+depth) and the back.
    for (const double sign : {1.0, -1.0})
    {
        addStrip(ChestPart::Side, sign, [sign, halfDepth, body, bottom](double across, int edge)
            {
                return Corner{across, sign * halfDepth, edge == 0 ? body : bottom};
            }, sign * halfWidth, {0.0, sign, 0.0}, kind.frontLeft, kind.frontMiddle, kind.frontRight, 0.0,
            body - bottom);
    }

    // The short ends (+width and -width), and under a sloping lid the strip above each.
    for (const double sign : {1.0, -1.0})
    {
        // Seen from outside this end, its left is toward -depth at the +width end.
        const double across = sign * halfWidth;
        add(ChestPart::End, sign, kind.side, 64,
            {{across, -sign * halfDepth, body}, {across, sign * halfDepth, body}, {across, sign * halfDepth, bottom},
                {across, -sign * halfDepth, bottom}},
            {{0.0, 0.0}, {size[1], 0.0}, {size[1], body - bottom}, {0.0, body - bottom}}, {sign, 0.0, 0.0});

        if (kind.sloped)
        {
            add(ChestPart::EndTop, sign, kind.sideTop, 64,
                {{across, -sign * halfDepth, body}, {across, sign * halfDepth, body},
                    {across, sign * (halfDepth - 16.0), top}, {across, -sign * (halfDepth - 16.0), top}},
                {{0.0, 64.0}, {size[1], 64.0}, {size[1] - 16.0, 48.0}, {16.0, 48.0}}, {sign, 0.0, 0.0});
        }
    }

    // The lid.
    const double topDepth = kind.sloped ? halfDepth - 16.0 : halfDepth;

    if (kind.sloped)
    {
        for (const double sign : {1.0, -1.0})
        {
            addStrip(ChestPart::Slope, sign, [sign, halfDepth, body, top](double across, int edge)
                {
                    return edge == 0 ? Corner{across, sign * (halfDepth - 16.0), top}
                                     : Corner{across, sign * halfDepth, body};
                }, sign * halfWidth, {0.0, sign, 1.0}, kind.frontLeft,
                sign > 0.0 ? kind.slopeMiddle : kind.frontMiddle, kind.frontRight, 48.0, 64.0);
        }
    }

    if (kind.lidAcross)
    {
        // From the +width end: left end, middle, right end; u from the front (+depth) to the back, v along.
        const std::array<std::tuple<double, double, std::string>, 3> pieces = {{
            {halfWidth, halfWidth - 16.0, kind.topLeft},
            {halfWidth - 16.0, 16.0 - halfWidth, kind.topMiddle},
            {16.0 - halfWidth, -halfWidth, kind.topRight}}};

        for (const std::tuple<double, double, std::string> &piece : pieces)
        {
            const double from = std::get<0>(piece);
            const double to = std::get<1>(piece);
            const double along = from - to;
            add(ChestPart::Top, 0.0, std::get<2>(piece), 64,
                {{from, topDepth, top}, {from, -topDepth, top}, {to, -topDepth, top}, {to, topDepth, top}},
                {{0.0, 0.0}, {2.0 * topDepth, 0.0}, {2.0 * topDepth, along}, {0.0, along}}, {0.0, 0.0, 1.0});
        }
    }
    else
    {
        addStrip(ChestPart::Top, 0.0, [topDepth, top](double across, int edge)
            {
                return Corner{across, edge == 0 ? topDepth : -topDepth, top};
            }, -halfWidth, {0.0, 0.0, 1.0}, kind.topLeft, kind.topMiddle, kind.topRight,
            kind.sloped ? 64.0 - 2.0 * topDepth : 0.0, kind.sloped ? 64.0 : 2.0 * topDepth);
    }

    return faces;
}

double ChestGaps::nearest() const
{
    return std::min({front, back, endLeft, endRight});
}

ChestGaps chestGaps(const std::vector<ChestWall> &walls, const std::array<double, 2> &centre, double frontRadians,
    double width, double depth)
{
    // From the middle straight out to the nearest wall, less the chest's own half.
    const auto reach = [&walls, &centre](double radians, double half)
    {
        const double dx = oy::cos(radians);
        const double dy = oy::sin(radians);
        double best = 1.0e9;

        for (const ChestWall &wall : walls)
        {
            const double ex = wall.to[0] - wall.from[0];
            const double ey = wall.to[1] - wall.from[1];
            const double denominator = dx * ey - dy * ex;

            if (std::abs(denominator) < 1.0e-9)
            {
                continue;
            }

            const double t = ((wall.from[0] - centre[0]) * ey - (wall.from[1] - centre[1]) * ex) / denominator;
            const double s = ((wall.from[0] - centre[0]) * dy - (wall.from[1] - centre[1]) * dx) / denominator;

            if (t > 0.0 && s >= -1.0e-6 && s <= 1.0 + 1.0e-6)
            {
                best = std::min(best, t - half);
            }
        }

        return best;
    };

    constexpr double Quarter = 1.57079632679489661923;
    ChestGaps gaps;
    gaps.front = reach(frontRadians, depth / 2.0);
    gaps.back = reach(frontRadians + 2.0 * Quarter, depth / 2.0);
    gaps.endLeft = reach(frontRadians + Quarter, width / 2.0);
    gaps.endRight = reach(frontRadians - Quarter, width / 2.0);
    return gaps;
}

std::string chestFacingFault(const ChestGaps &gaps, bool frontKnown, std::optional<double> entranceDegrees)
{
    const auto units = [](double value)
    {
        return std::to_string(static_cast<long>(std::lround(std::max(value, 0.0))));
    };
    const double ends = std::min(gaps.endLeft, gaps.endRight);

    if (!frontKnown)
    {
        // Either long side may be the back: only an end to the wall with both long sides clear is wrong.
        if (ends <= ChestFacing::Reach && std::min(gaps.front, gaps.back) > ChestFacing::Reach)
        {
            return "it stands end-on to a wall " + units(ends) + " away, a long side to the room";
        }

        return {};
    }

    if (gaps.front < ChestFacing::Reach && gaps.front < gaps.back)
    {
        return "its front faces a wall " + units(gaps.front) + " away";
    }

    if (gaps.back > ChestFacing::Reach && ends <= ChestFacing::Reach)
    {
        return "it stands end-on to a wall " + units(ends) + " away, its back to the room";
    }

    if (gaps.nearest() > ChestFacing::Reach && entranceDegrees && *entranceDegrees > ChestFacing::EntranceDegrees)
    {
        return "it stands free with its back to its room's entrance (" + units(*entranceDegrees)
            + " degrees from its front)";
    }

    return {};
}

std::array<std::array<double, 2>, 4> chestFootprint(const std::array<double, 2> &centre, double frontRadians,
    double width, double depth)
{
    const std::array<double, 2> front = {oy::cos(frontRadians), oy::sin(frontRadians)};
    const std::array<double, 2> across = {-front[1], front[0]};
    std::array<std::array<double, 2>, 4> corners;
    size_t index = 0;

    for (const std::array<double, 2> &unit :
         std::array<std::array<double, 2>, 4>{{{-1.0, -1.0}, {1.0, -1.0}, {1.0, 1.0}, {-1.0, 1.0}}})
    {
        corners[index++] = {centre[0] + across[0] * unit[0] * width / 2.0 + front[0] * unit[1] * depth / 2.0,
            centre[1] + across[1] * unit[0] * width / 2.0 + front[1] * unit[1] * depth / 2.0};
    }

    return corners;
}

namespace
{
double pointToSegment(const std::array<double, 2> &point, const std::array<double, 2> &from,
    const std::array<double, 2> &to)
{
    const double dx = to[0] - from[0];
    const double dy = to[1] - from[1];
    const double lengthSquared = dx * dx + dy * dy;
    const double t = lengthSquared <= 0.0 ? 0.0
        : std::clamp(((point[0] - from[0]) * dx + (point[1] - from[1]) * dy) / lengthSquared, 0.0, 1.0);
    return std::sqrt((point[0] - from[0] - dx * t) * (point[0] - from[0] - dx * t)
        + (point[1] - from[1] - dy * t) * (point[1] - from[1] - dy * t));
}

bool insideFootprint(const std::array<std::array<double, 2>, 4> &footprint, const std::array<double, 2> &point)
{
    bool inside = false;

    for (size_t index = 0, previous = 3; index < 4; previous = index++)
    {
        const std::array<double, 2> &a = footprint[index];
        const std::array<double, 2> &b = footprint[previous];

        if ((a[1] > point[1]) != (b[1] > point[1])
            && point[0] < (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0])
        {
            inside = !inside;
        }
    }

    return inside;
}

// From a footprint to a segment: 0 when they touch, else the least distance (its sides sampled every 4).
double footprintToSegment(const std::array<std::array<double, 2>, 4> &footprint, const std::array<double, 2> &from,
    const std::array<double, 2> &to)
{
    if (insideFootprint(footprint, from) || insideFootprint(footprint, to))
    {
        return 0.0;
    }

    double best = 1.0e18;

    for (size_t side = 0; side < 4; ++side)
    {
        const std::array<double, 2> &a = footprint[side];
        const std::array<double, 2> &b = footprint[(side + 1) % 4];
        const double length = std::sqrt((b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1]));
        const int steps = std::max(1, static_cast<int>(std::ceil(length / 4.0)));

        for (int step = 0; step <= steps; ++step)
        {
            const double t = static_cast<double>(step) / steps;
            best = std::min(best, pointToSegment({a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t}, from, to));
        }

        best = std::min({best, pointToSegment(from, a, b), pointToSegment(to, a, b)});
    }

    return best;
}

std::string wholeUnits(double value)
{
    return std::to_string(static_cast<long>(std::lround(std::max(value, 0.0))));
}
}

std::string chestPlacementFault(const std::array<std::array<double, 2>, 4> &footprint,
    const std::vector<ChestDoorway> &doorways, bool lines)
{
    const std::array<double, 2> centre = {(footprint[0][0] + footprint[2][0]) / 2.0,
        (footprint[0][1] + footprint[2][1]) / 2.0};

    for (const ChestDoorway &doorway : doorways)
    {
        const double dx = doorway.to[0] - doorway.from[0];
        const double dy = doorway.to[1] - doorway.from[1];
        const double width = std::sqrt(dx * dx + dy * dy);
        // Whether the chest's middle lies in front of the opening (its foot within it and 64 past its ends).
        const double along = width <= 0.0 ? 0.0
            : ((centre[0] - doorway.from[0]) * dx + (centre[1] - doorway.from[1]) * dy) / width;
        const bool inFront = along >= -ChestPlacement::SideMargin && along <= width + ChestPlacement::SideMargin;
        const double gap = footprintToSegment(footprint, doorway.from, doorway.to);
        const double clearance = inFront ? ChestPlacement::DoorwayFront : ChestPlacement::DoorwayBeside;

        if (gap < clearance)
        {
            return "it stands " + wholeUnits(gap) + (inFront ? " in front of " : " beside ") + doorway.name
                + " (a chest keeps " + wholeUnits(std::min(ChestPlacement::DoorwayFront, ChestPlacement::DoorwayBeside))
                + " clear of a way in)";
        }
    }

    for (size_t first = 0; lines && first < doorways.size(); ++first)
    {
        for (size_t second = first + 1; second < doorways.size(); ++second)
        {
            const ChestDoorway &a = doorways[first];
            const ChestDoorway &b = doorways[second];
            const std::array<double, 2> from = {(a.from[0] + a.to[0]) / 2.0, (a.from[1] + a.to[1]) / 2.0};
            const std::array<double, 2> to = {(b.from[0] + b.to[0]) / 2.0, (b.from[1] + b.to[1]) / 2.0};
            const double gap = footprintToSegment(footprint, from, to);

            if (gap < ChestPlacement::WalkingLine)
            {
                return "it stands " + wholeUnits(gap) + " from the walking line between " + a.name + " and " + b.name
                    + " (a chest keeps " + wholeUnits(ChestPlacement::WalkingLine) + " clear of it)";
            }
        }
    }

    return {};
}
}
