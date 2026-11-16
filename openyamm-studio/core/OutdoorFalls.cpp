#include "core/OutdoorFalls.h"

#include "core/CoreMath.h"
#include "core/SketchRead.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <limits>

// How a waterfall is built, as the shipped falls are (measured 2026-11-14).
//
// Alvar (out03): the lake on the mesa is the land's water at 2880. Three models make the falls: two sheets of 51 and
// 47 triangles in WtrTyl (FlowDown, rows every ~540 of drop), standing a little out from the land's cliff and leaning
// about 430 out over 2,880 (the foot fans to about 1.7 times the lip's width and curves round like a horseshoe), each
// edged by a strip in the ground tile; and the top water: a level WtrTyl face 2 over the lake (Fluid, flowing) from
// up the lake to the lip, its downstream edge the sheet's top edge point for point, so the lake's water, the top
// water and the sheet meet with nothing between. Under the top water the land falls away (the cliff cell); the sheet
// stands in front of it. The foot is the river at 0, where the sheets end.
// Emerald Island (7out01, the Temple of the Moon's falls): the same as a channel: leaning chutes of 7wtrtyl (684 to
// 516 over 124 out) between banks of the ground tile, pools as level water faces, the foot at the sea's 0.
//
// Measured again 2026-11-15 (S8e): Alvar's sheets are triangles in rows at 486, 1078, 1618, 2158, 2518 and 2880,
// their foot about 380 out from the lip, their v the height (v = -z - 4) and their u each face's own across (u jumps
// from face to face): the game draws a water face by its liquid and moves the picture by the way the texels run over
// each triangle, so those texels give every triangle the same flow. Alvar's top water (WaterfallC4) is a hexagon 2
// over the lake reaching about 1,000 up it, ringed by low mounds of DIRTtyl 50 to 100 over the lake. Emerald's chutes
// are planar (each chute one plane in several faces, FlowDown and Fluid) between banks of 7dirttyl. No shipped fall
// has a decoration at its foot (Emerald has the brook sound Snd_Brook at each pool).
//
// So here: the land is cut where the sheet stands (every node whose cell the sheet crosses, and the last row of the
// stream before the lip, lowered to the sheet one cell further down: the foot's level for an upright sheet), so no
// land stands in front of it. The top water lies from `back` up the stream to the lip, a little wider than the sheet:
// its first 256 rise out of the stream from under the stream's water (the game draws a model's water opaque and with
// finer waves than the land's, so an edge over the stream would show as a line), then 2 over the stream across its
// end and the cut to the lip (level over at least the last 768, or a strip of the land shows); its downstream edge is
// the sheet's top edge. The sheet is one plane from the lip down to the foot (upright, or its foot `lean` out and
// `spread` wider), its texels in its own plane; it moves down (FlowDown) and the party passes through it. The foot
// water lies 2 over the pool from the sheet's foot out `pool`. The rock sides: one crag at each edge of the sheet,
// leaning with it, rings of corners moved by a seed and narrowing upward to a peaked top, every face a triangle: rock
// that hides the cut's sides. The banks: a low bank of the dirt tile along each side of the top water, as Emerald's
// and Alvar's, over the water's sides and the stream's shallows.

namespace OpenYAMM::Studio
{
namespace
{
constexpr int Nodes = 128;
constexpr double Cell = 512.0;
// How far the top water reaches beyond the sheet's edges each side.
constexpr double TopMargin = 32.0;
// The top water rises from this far under the stream's water at its upstream end to 2 over it this far downstream,
// and lies level at least this far before the lip.
constexpr double TopSink = 12.0;
constexpr double TopRamp = 256.0;
constexpr double TopLevelReach = 768.0;
// The banks along the top water: the crest's height over the stream, how far each slope reaches in from the water's
// edge and out into the land, and how long the bank takes to rise from the water at its upstream end.
constexpr double BankRise = 32.0;
constexpr double BankInside = 48.0;
constexpr double BankOutside = 160.0;
constexpr double BankTaper = 256.0;
constexpr double BankStep = 128.0;
const char *SketchFile = "sketch.yml";

using Point2 = std::array<double, 2>;
using Point3 = std::array<double, 3>;



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

bool cellOf(const YAML::Node &node, Point2 &cell)
{
    return node.IsDefined() && node.IsSequence() && node.size() == 2 && numberOfNode(node[0], cell[0])
        && numberOfNode(node[1], cell[1]) && cell[0] >= 0.0 && cell[1] >= 0.0 && cell[0] <= Nodes - 1
        && cell[1] <= Nodes - 1;
}

Point2 toWorld(const Point2 &cell)
{
    return {(cell[0] - Nodes / 2) * Cell, (Nodes / 2 - cell[1]) * Cell};
}

// The distance from a point to a polyline, in the same units.
double distanceToLine(const Point2 &point, const std::vector<Point2> &line)
{
    double best = std::numeric_limits<double>::infinity();

    for (size_t index = 0; index + 1 < line.size(); ++index)
    {
        const Point2 &from = line[index];
        const Point2 &to = line[index + 1];
        const double dx = to[0] - from[0];
        const double dy = to[1] - from[1];
        const double lengthSquared = dx * dx + dy * dy;
        double share = lengthSquared > 0.0 ? ((point[0] - from[0]) * dx + (point[1] - from[1]) * dy) / lengthSquared
            : 0.0;
        share = std::clamp(share, 0.0, 1.0);
        best = std::min(best, oy::hypot(point[0] - from[0] - dx * share, point[1] - from[1] - dy * share));
    }

    return best;
}

// A repeatable number in [0, 1) from a seed and three counters.
double noise(uint32_t seed, uint32_t a, uint32_t b, uint32_t c)
{
    uint32_t value = seed * 0x9E3779B1u ^ (a + 0x7F4A7C15u) * 0x85EBCA77u ^ (b + 0x165667B1u) * 0xC2B2AE3Du
        ^ (c + 0x27D4EB2Fu) * 0x2545F491u;
    value ^= value >> 15;
    value *= 0x2C1B3C6Du;
    value ^= value >> 12;
    value *= 0x297A2D39u;
    value ^= value >> 15;
    return static_cast<double>(value) / 4294967296.0;
}

// The sheet's shape at a share of the drop (0 at the lip, 1 at the foot): how far out it stands and its half width.
// One plane from the lip's edge to the foot's, as Emerald's chutes are: the game draws a water face by its liquid
// and samples the waves by the face's place (game/shaders/fs_water.sc), and where two faces of a sheet meet at an
// angle that sampling breaks into a hairline (Alvar's curved sheets show it along their rows and diagonals).
double outAt(const OutdoorFallPlan &fall, double share)
{
    return fall.lean * std::clamp(share, 0.0, 1.0);
}

double halfWidthAt(const OutdoorFallPlan &fall, double share)
{
    return fall.width * 0.5 * (1.0 + (fall.spread - 1.0) * std::clamp(share, 0.0, 1.0));
}

// A place of the fall's frame (out along the fall, across to its right as it falls) in world units.
Point3 placeOf(const OutdoorFallPlan &fall, double out, double across, double z)
{
    const Point2 right = {fall.along[1], -fall.along[0]};
    return {fall.lip[0] + fall.along[0] * out + right[0] * across, fall.lip[1] + fall.along[1] * out
        + right[1] * across, z};
}

// The sheet's height `out` beyond the lip: the top at and before the lip, the foot beyond the foot's line.
double sheetHeightAt(const OutdoorFallPlan &fall, double out)
{
    if (out <= 0.0)
    {
        return fall.top;
    }

    if (fall.lean <= 0.0 || out >= fall.lean)
    {
        return fall.foot;
    }

    return fall.top - (fall.top - fall.foot) * out / fall.lean;
}

Point3 normalOf(const std::vector<OutdoorModelPoint> &points)
{
    Point3 normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const OutdoorModelPoint &a = points[index];
        const OutdoorModelPoint &b = points[(index + 1) % points.size()];
        normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
        normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
        normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }

    return normal;
}

// The texels of a sheet face as the shipped falls have them (Alvar's: across along the face's level line, down its
// slope): the game draws a flowing water face by its liquid and moves the picture by the way its texels run over the
// face, triangle by triangle (game/render/WaterGeometry.h waterFaceFlow), so texels that bend from one triangle to the
// next move each triangle's water its own way and the picture tears along the diagonals. Texels in each face's own
// plane give every face of the sheet the same flow. They are moved, face by face, to lie as near as they can to
// `near` (the sheet's running texels), which keeps them small and keeps a picture drawn by its texels nearly whole.
std::vector<std::array<double, 2>> planarTexels(const std::vector<OutdoorModelPoint> &points,
    const std::vector<std::array<double, 2>> &near)
{
    std::vector<OutdoorModelPoint> stored;

    for (const OutdoorModelPoint &point : points)
    {
        stored.push_back({std::round(point[0]), std::round(point[1]), std::round(point[2])});
    }

    Point3 normal = normalOf(stored);
    const double length = oy::hypot(normal[0], normal[1], normal[2]);

    if (length <= 1.0e-9)
    {
        return near;
    }

    normal = {normal[0] / length, normal[1] / length, normal[2] / length};
    // As the game takes them: across level in the face (x on a level face), up the face's slope.
    Point3 across = {1.0, 0.0, 0.0};

    if (std::fabs(normal[2]) <= 0.99)
    {
        const double level = oy::hypot(normal[0], normal[1]);
        across = {-normal[1] / level, normal[0] / level, 0.0};
    }

    const Point3 up = {normal[1] * across[2] - normal[2] * across[1], normal[2] * across[0] - normal[0] * across[2],
        normal[0] * across[1] - normal[1] * across[0]};
    std::vector<std::array<double, 2>> texels;
    std::array<double, 2> shift = {0.0, 0.0};

    for (size_t index = 0; index < stored.size(); ++index)
    {
        const OutdoorModelPoint &point = stored[index];
        texels.push_back({point[0] * across[0] + point[1] * across[1] + point[2] * across[2],
            -(point[0] * up[0] + point[1] * up[1] + point[2] * up[2])});
        shift[0] += near[index][0] - texels.back()[0];
        shift[1] += near[index][1] - texels.back()[1];
    }

    for (std::array<double, 2> &texel : texels)
    {
        texel = {texel[0] + std::round(shift[0] / stored.size()), texel[1] + std::round(shift[1] / stored.size())};
    }

    return texels;
}

// A triangle with its texels, turned to face `toward`.
int addTriangle(OutdoorModelBuilder &builder, std::vector<OutdoorModelPoint> points,
    std::vector<std::array<double, 2>> texels, const Point3 &toward, const std::string &texture, uint16_t event)
{
    const Point3 normal = normalOf(points);

    if (normal[0] * toward[0] + normal[1] * toward[1] + normal[2] * toward[2] < 0.0)
    {
        std::reverse(points.begin(), points.end());
        std::reverse(texels.begin(), texels.end());
    }

    return builder.addFace(points, texture, texels, event);
}

// A face in the builder's own texels, turned to face `toward`.
void addSurfaceFacing(OutdoorModelBuilder &builder, std::vector<OutdoorModelPoint> points, const Point3 &toward,
    const std::string &texture, uint16_t event)
{
    const Point3 normal = normalOf(points);

    if (normal[0] * toward[0] + normal[1] * toward[1] + normal[2] * toward[2] < 0.0)
    {
        std::reverse(points.begin(), points.end());
    }

    builder.addSurface(points, texture, event);
}

void addSurfaceFacingUp(OutdoorModelBuilder &builder, std::vector<OutdoorModelPoint> points,
    const std::string &texture, uint16_t event)
{
    addSurfaceFacing(builder, std::move(points), {0.0, 0.0, 1.0}, texture, event);
}

// A face whose texels are given as [across, along the flow] per point, turned to face up.
int addLevelFace(OutdoorModelBuilder &builder, std::vector<OutdoorModelPoint> points,
    std::vector<std::array<double, 2>> texels, const std::string &texture, uint16_t event)
{
    return addTriangle(builder, std::move(points), std::move(texels), {0.0, 0.0, 1.0}, texture, event);
}
}

std::vector<OutdoorFallPlan> readOutdoorFalls(
    const Project &project,
    const std::string &world,
    std::vector<ProjectIssue> &issues)
{
    const std::string waterTexture = world == "mm6" ? "6wtrtyl" : world == "mm7" ? "7wtrtyl" : "wtrtyl";
    std::vector<OutdoorFallPlan> falls;
    const YAML::Node sketch = project.document(SketchFile);
    const YAML::Node structures = childOf(sketch, "structures");
    const YAML::Node rivers = childOf(childOf(sketch, "water"), "rivers");
    const std::string rock = world == "mm6" ? "6dirttyl" : world == "mm7" ? "cwb1" : "dirttyl";
    // The banks in the world's dirt tile, as Emerald's (7dirttyl) and Alvar's (DIRTtyl).
    const std::string bank = world == "mm6" ? "6dirttyl" : world == "mm7" ? "7dirttyl" : "dirttyl";

    for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size(); ++index)
    {
        const YAML::Node node = structures[index];

        if (textOf(node, "kind") != "waterfall")
        {
            continue;
        }

        OutdoorFallPlan fall;
        fall.id = textOf(node, "id");
        fall.path = "structures[" + std::to_string(index) + "]";
        const auto add = [&](const std::string &where, const std::string &message)
        {
            issues.push_back({SketchFile, fall.path + where, message, "structure"});
        };
        const YAML::Node line = childOf(node, "line");
        Point2 lipCell = {0.0, 0.0};
        Point2 towardCell = {0.0, 0.0};

        if (!line.IsDefined() || !line.IsSequence() || line.size() != 2 || !cellOf(line[0], lipCell)
            || !cellOf(line[1], towardCell))
        {
            add(".line", "a waterfall's `line` is two points in cells: the lip's middle, then any point the water "
                "falls toward (it gives the way only)");
            continue;
        }

        fall.lip = toWorld(lipCell);
        const Point2 toward = toWorld(towardCell);
        const double length = oy::hypot(toward[0] - fall.lip[0], toward[1] - fall.lip[1]);

        if (length < 16.0)
        {
            add(".line", "a waterfall's two points lie on one place: the second gives the way the water falls");
            continue;
        }

        fall.along = {(toward[0] - fall.lip[0]) / length, (toward[1] - fall.lip[1]) / length};

        if (!numberOfNode(childOf(node, "top"), fall.top) || !numberOfNode(childOf(node, "foot"), fall.foot))
        {
            add("", "a waterfall needs `top` (the stream's water level at the lip) and `foot` (the pool's water "
                "level), map units against the plan's datum");
            continue;
        }

        if (fall.top - fall.foot < 64.0)
        {
            add(".top", "a waterfall falls: its top (" + std::to_string(static_cast<int>(fall.top))
                + ") stands at least 64 over its foot (" + std::to_string(static_cast<int>(fall.foot)) + ")");
            continue;
        }

        // The width: given, or the stream's at the lip (the river whose line passes within two cells of it).
        double width = 0.0;

        if (!numberOfNode(childOf(node, "width"), width))
        {
            double nearest = 2.0;

            for (size_t river = 0; rivers.IsDefined() && rivers.IsSequence() && river < rivers.size(); ++river)
            {
                std::vector<Point2> points;
                const YAML::Node riverLine = childOf(rivers[river], "line");

                for (size_t point = 0; riverLine.IsDefined() && riverLine.IsSequence() && point < riverLine.size();
                     ++point)
                {
                    Point2 cell = {0.0, 0.0};

                    if (cellOf(riverLine[point], cell))
                    {
                        points.push_back(cell);
                    }
                }

                const double distance = points.size() >= 2 ? distanceToLine(lipCell, points)
                    : std::numeric_limits<double>::infinity();

                if (distance <= nearest)
                {
                    double cells = 1.0;
                    numberOfNode(childOf(rivers[river], "width_cells"), cells);
                    nearest = distance;
                    // The open water between the shore tiles, which take a quarter cell each side.
                    width = std::max(Cell * 0.5, cells * Cell - Cell * 0.5);
                }
            }

            if (width <= 0.0)
            {
                add(".width", "a waterfall away from any river (none passes within two cells of its lip) needs a "
                    "`width`");
                continue;
            }
        }

        fall.width = width;
        double number = 0.0;

        if (numberOfNode(childOf(node, "lean"), number))
        {
            fall.lean = number;
        }

        if (numberOfNode(childOf(node, "spread"), number))
        {
            fall.spread = number;
        }

        if (numberOfNode(childOf(node, "back"), number))
        {
            fall.back = number;
        }

        if (numberOfNode(childOf(node, "pool"), number))
        {
            fall.pool = number;
        }

        if (numberOfNode(childOf(node, "rise"), number))
        {
            fall.rise = number;
        }

        if (numberOfNode(childOf(node, "seed"), number))
        {
            fall.seed = static_cast<uint32_t>(std::max(0.0, number));
        }

        fall.rocks = textOf(node, "rocks", "true") != "false";
        fall.banks = textOf(node, "banks", "true") != "false";
        fall.rockSize = std::clamp(fall.width * 0.45, 256.0, 640.0);

        if (numberOfNode(childOf(node, "rock_size"), number))
        {
            fall.rockSize = number;
        }

        if (fall.width < 64.0 || fall.width > 4096.0 || fall.lean < 0.0 || fall.lean > 4096.0 || fall.spread < 1.0
            || fall.spread > 3.0 || fall.back < 64.0 || fall.back > 4096.0 || fall.pool < 0.0 || fall.pool > 4096.0
            || fall.rise < 0.0 || fall.rise > 2048.0 || fall.rockSize < 64.0 || fall.rockSize > 2048.0)
        {
            add("", "a waterfall's `width` is 64 to 4096, `lean` 0 to 4096, `spread` 1 to 3, `back` 64 to 4096, "
                "`pool` 0 to 4096, `rise` 0 to 2048 and `rock_size` 64 to 2048");
            continue;
        }

        const YAML::Node textures = childOf(node, "textures");
        fall.waterTexture = waterTexture;
        fall.rockTexture = rock;
        fall.bankTexture = bank;

        for (const auto &[pRole, pTarget] : {std::pair<const char *, std::string *>{"water", &fall.waterTexture},
                 std::pair<const char *, std::string *>{"rock", &fall.rockTexture},
                 std::pair<const char *, std::string *>{"bank", &fall.bankTexture}})
        {
            const YAML::Node entry = childOf(textures, pRole);

            if (entry.IsDefined() && entry.IsScalar())
            {
                *pTarget = entry.Scalar();
            }
            else if (entry.IsDefined() && entry.IsMap())
            {
                add(".textures." + std::string(pRole), "a waterfall's textures are names: its water takes the "
                    "shipped falls' bits itself");
            }
        }

        falls.push_back(fall);
    }

    return falls;
}

void shapeOutdoorFallLand(
    const std::vector<OutdoorFallPlan> &falls,
    std::vector<double> &ground,
    std::vector<double> &waterNode,
    std::vector<size_t> &driedNodes,
    std::vector<std::string> &warnings)
{
    for (const OutdoorFallPlan &fall : falls)
    {
        const Point2 right = {fall.along[1], -fall.along[0]};
        const double reach = std::max(fall.lean, 0.0) + Cell;
        size_t lowered = 0;
        size_t dried = 0;
        std::vector<size_t> cut;

        for (int y = 0; y < Nodes; ++y)
        {
            for (int x = 0; x < Nodes; ++x)
            {
                const Point2 place = toWorld({static_cast<double>(x), static_cast<double>(y)});
                const double dx = place[0] - fall.lip[0];
                const double dy = place[1] - fall.lip[1];
                const double out = dx * fall.along[0] + dy * fall.along[1];
                const double across = dx * right[0] + dy * right[1];

                // From the stream's last row before the lip to a cell beyond the foot, every node whose cell the
                // sheet's width crosses.
                if (out <= -Cell || out >= reach)
                {
                    continue;
                }

                const double share = fall.lean > 0.0 ? std::clamp(out / fall.lean, 0.0, 1.0)
                    : (out > 0.0 ? 1.0 : 0.0);

                // Beyond the lip, every node whose cell the sheet crosses; before it, only under the top water (a
                // node beside it lowered would open a cleft between the water and the bank).
                if (std::abs(across) >= (out >= 0.0 ? halfWidthAt(fall, share) + Cell
                    : fall.width * 0.5 + TopMargin))
                {
                    continue;
                }

                // No higher than the sheet one cell further down, so the land in that cell lies under it.
                const double limit = std::max(fall.foot, sheetHeightAt(fall, out + Cell) - 32.0);
                const size_t node = static_cast<size_t>(y) * Nodes + x;
                double &wet = waterNode[node];

                if (!std::isnan(wet) && wet > limit + 0.5)
                {
                    wet = std::numeric_limits<double>::quiet_NaN();
                    driedNodes.push_back(node);
                    ++dried;
                }

                if (std::isnan(wet) && ground[node] > limit)
                {
                    ground[node] = limit;
                    cut.push_back(node);
                    ++lowered;
                }
            }
        }

        // The cells round a lowered node are land: a water tile there would slope down the cut beside the top
        // water. Their water corners above the cut become dry land at the water's level (the stream's bank at the
        // lip); the pool's stay, and so does the stream under the top water (`back` reaches past those cells).
        for (const size_t node : cut)
        {
            const int x = static_cast<int>(node % Nodes);
            const int y = static_cast<int>(node / Nodes);

            for (int cornerY = std::max(0, y - 1); cornerY <= std::min(Nodes - 1, y + 1); ++cornerY)
            {
                for (int cornerX = std::max(0, x - 1); cornerX <= std::min(Nodes - 1, x + 1); ++cornerX)
                {
                    const size_t corner = static_cast<size_t>(cornerY) * Nodes + cornerX;

                    const Point2 place = toWorld({static_cast<double>(cornerX), static_cast<double>(cornerY)});
                    const double out = (place[0] - fall.lip[0]) * fall.along[0]
                        + (place[1] - fall.lip[1]) * fall.along[1];
                    const double across = (place[0] - fall.lip[0]) * right[0] + (place[1] - fall.lip[1]) * right[1];
                    // Up the stream on the fall's middle line the water stays, so the stream runs on into the top
                    // water. One node of a row at most: a cell with two water corners beside the cut is drawn as water
                    // spread over the cut (a lip between two nodes kept both and drowned the sheet).
                    const bool underTop = out < -Cell * 0.5 && std::abs(across) < std::min(Cell * 0.5,
                        fall.width * 0.5 + TopMargin);

                    if (!underTop && !std::isnan(waterNode[corner]) && waterNode[corner] > ground[node] + 32.0)
                    {
                        ground[corner] = std::min(ground[corner], waterNode[corner]);
                        waterNode[corner] = std::numeric_limits<double>::quiet_NaN();
                        driedNodes.push_back(corner);
                        ++dried;
                    }
                }
            }
        }

        if (lowered == 0 && dried == 0)
        {
            continue;
        }

        warnings.push_back(fall.path + ": the land is cut for the waterfall " + fall.id + ": "
            + std::to_string(lowered) + " nodes lowered, " + std::to_string(dried)
            + " of the stream's made its bank, so no land stands in front of the sheet");
    }
}

void raiseOutdoorFall(
    const OutdoorFallPlan &fall,
    OutdoorModelBuilder &builder,
    uint16_t event,
    std::vector<int> &sheetFaces,
    std::vector<int> &waterFaces)
{
    const double lipLevel = fall.top + 2.0;
    const double halfTop = fall.width * 0.5;
    const double halfFoot = halfWidthAt(fall, 1.0);
    const double footOut = outAt(fall, 1.0);
    const Point3 down = {fall.along[0], fall.along[1], 0.0};
    const double slant = oy::hypot(footOut, lipLevel - fall.foot);
    const double wide = halfTop + TopMargin;

    // The top water: from `back` up the stream to the lip, a little wider than the sheet each side, its downstream
    // edge on the sheet's top edge. Its first `TopRamp` rises out of the stream from under the stream's water (the
    // game draws a model's water face opaque and with finer waves than the land's, so an edge lying over the stream
    // shows as a line of another shade), where `back` leaves room for it; from there it lies 2 over the stream, over
    // the stream's end and the cut land to the lip. One mapping for the whole of it (across, along the stream).
    {
        // Level over at least the last cell and a half (the stream's water ends there, in shore tiles before the
        // stream's nodes the cut made its bank): a ramp under the land there would bare a strip of it.
        const double levelFrom = std::max(-fall.back, std::min(-fall.back + TopRamp, -TopLevelReach));
        const std::array<double, 3> stations = {-fall.back, levelFrom, 0.0};
        const std::array<double, 3> levels = {fall.top - TopSink, lipLevel, lipLevel};

        for (size_t station = 0; station + 1 < stations.size(); ++station)
        {
            if (stations[station + 1] - stations[station] < 1.0)
            {
                continue;
            }

            const std::vector<OutdoorModelPoint> face = {placeOf(fall, stations[station], -wide, levels[station]),
                placeOf(fall, stations[station], wide, levels[station]),
                placeOf(fall, stations[station + 1], wide, levels[station + 1]),
                placeOf(fall, stations[station + 1], -wide, levels[station + 1])};
            const std::vector<std::array<double, 2>> faceTexels = {{halfTop - wide, stations[station]},
                {halfTop + wide, stations[station]}, {halfTop + wide, stations[station + 1]},
                {halfTop - wide, stations[station + 1]}};
            waterFaces.push_back(addLevelFace(builder, face, faceTexels, fall.waterTexture, event));
        }
    }

    // The sheet: one face from the lip's edge down to the foot's, facing out along the fall.
    {
        const std::vector<OutdoorModelPoint> face = {placeOf(fall, 0.0, -halfTop, lipLevel),
            placeOf(fall, footOut, -halfFoot, fall.foot), placeOf(fall, footOut, halfFoot, fall.foot),
            placeOf(fall, 0.0, halfTop, lipLevel)};
        const std::vector<std::array<double, 2>> near = {{0.0, 0.0}, {halfTop - halfFoot, slant},
            {halfTop + halfFoot, slant}, {fall.width, 0.0}};
        sheetFaces.push_back(addTriangle(builder, face, planarTexels(face, near), down, fall.waterTexture, event));
    }

    // The foot water: from just behind the sheet's foot out into the pool.
    if (fall.pool > 0.0)
    {
        const double footWide = halfFoot + 128.0;
        const double z = fall.foot + 2.0;
        const std::vector<OutdoorModelPoint> face = {placeOf(fall, footOut - 64.0, -footWide, z),
            placeOf(fall, footOut - 64.0, footWide, z), placeOf(fall, footOut + fall.pool, footWide, z),
            placeOf(fall, footOut + fall.pool, -footWide, z)};
        const std::vector<std::array<double, 2>> faceTexels = {{halfTop - footWide, slant - 64.0},
            {halfTop + footWide, slant - 64.0}, {halfTop + footWide, slant + fall.pool},
            {halfTop - footWide, slant + fall.pool}};
        waterFaces.push_back(addLevelFace(builder, face, faceTexels, fall.waterTexture, event));
    }

    // The banks: a low bank along each side of the top water (Emerald's chutes run between banks of the ground
    // tile, Alvar's top water between low mounds of it), its inner foot under the water's edge and its outer foot in
    // the land, so neither the water's sides nor the stream's shallows beside them show. It rises from the water over
    // its first `BankTaper` and its crest goes up and down a little (the seed), in triangles.
    if (fall.banks)
    {
        std::vector<double> stations;
        const int steps = std::max(2, static_cast<int>(std::ceil(fall.back / BankStep)));

        for (int step = 0; step <= steps; ++step)
        {
            stations.push_back(-fall.back + fall.back * step / steps);
        }

        for (int side = 0; side < 2; ++side)
        {
            const double sign = side == 0 ? -1.0 : 1.0;
            std::vector<std::array<OutdoorModelPoint, 3>> sections;

            for (size_t station = 0; station < stations.size(); ++station)
            {
                const double rising = std::clamp((stations[station] + fall.back) / BankTaper, 0.0, 1.0);
                const double height = BankRise * (0.7 + 0.5 * noise(fall.seed, side, static_cast<uint32_t>(station),
                    300));
                const double crest = lipLevel - 6.0 + (fall.top + height - lipLevel + 6.0) * rising;
                const double crestAcross = wide + BankInside + (noise(fall.seed, side,
                    static_cast<uint32_t>(station), 301) - 0.5) * BankInside;
                sections.push_back({placeOf(fall, stations[station], sign * (wide - BankInside), lipLevel - 6.0),
                    placeOf(fall, stations[station], sign * crestAcross, crest),
                    placeOf(fall, stations[station], sign * (wide + BankInside + BankOutside), fall.top - 48.0)});
            }

            for (size_t station = 0; station + 1 < sections.size(); ++station)
            {
                const std::array<OutdoorModelPoint, 3> &near = sections[station];
                const std::array<OutdoorModelPoint, 3> &far = sections[station + 1];

                for (size_t slope = 0; slope < 2; ++slope)
                {
                    addSurfaceFacingUp(builder, {near[slope], near[slope + 1], far[slope + 1]}, fall.bankTexture,
                        event);
                    addSurfaceFacingUp(builder, {near[slope], far[slope + 1], far[slope]}, fall.bankTexture, event);
                }
            }

            // The end at the lip, where the rock sides take over (or the fall's edge when there are none).
            const std::array<OutdoorModelPoint, 3> &last = sections.back();
            addSurfaceFacing(builder, {last[0], last[1], last[2]}, down, fall.bankTexture, event);
        }
    }

    if (!fall.rocks)
    {
        return;
    }

    // The rock sides: a crag at each edge, its rings following the sheet's edge as it leans and fans, standing
    // mostly beside the fall (not in the stream), each ring moved, turned and tilted by the seed.
    const int corners = 9;
    const double radius = fall.rockSize;
    const double low = fall.foot - 32.0;
    const double high = fall.top + fall.rise;
    const int rings = std::clamp(static_cast<int>(std::ceil((high - low) / 320.0)), 3, 20);
    const double pi = 3.14159265358979323846;

    for (int side = 0; side < 2; ++side)
    {
        const double sign = side == 0 ? -1.0 : 1.0;
        std::vector<std::vector<OutdoorModelPoint>> ring(static_cast<size_t>(rings) + 1);
        std::vector<Point3> middles;
        // Each crag's own lumps: a reach per corner that holds through the rings, varied ring by ring.
        std::vector<double> lumps;

        for (int corner = 0; corner < corners; ++corner)
        {
            lumps.push_back(0.7 + 0.5 * noise(fall.seed, side, 200, static_cast<uint32_t>(corner)));
        }

        for (int level = 0; level <= rings; ++level)
        {
            const double z = low + (high - low) * level / rings;
            const double share = std::clamp((fall.top - z) / (fall.top - fall.foot), 0.0, 1.0);
            // Narrowing to the top, with ledges: a ring now and then steps in.
            const double narrow = (1.0 - 0.45 * level / rings) * (0.85 + 0.25 * noise(fall.seed, side, level, 96));
            const double out = outAt(fall, share) + radius * 0.55;
            const double across = sign * (halfWidthAt(fall, share) + radius * 0.8);
            const Point3 middle = placeOf(fall, out + (noise(fall.seed, side, level, 99) - 0.5) * radius * 0.35,
                across + (noise(fall.seed, side, level, 98) - 0.5) * radius * 0.3, z);
            middles.push_back(middle);
            const double turn = (noise(fall.seed, side, level, 97) - 0.5) * 0.6;

            for (int corner = 0; corner < corners; ++corner)
            {
                const double angle = turn + 2.0 * pi * (corner
                    + (noise(fall.seed, side, level, static_cast<uint32_t>(corner)) - 0.5) * 0.45) / corners;
                const double reach = radius * narrow * lumps[static_cast<size_t>(corner)] * (0.85 + 0.3
                    * noise(fall.seed, side, level, static_cast<uint32_t>(corner) + 50));
                const double lift = level == 0 ? 0.0
                    : (noise(fall.seed, side, level, static_cast<uint32_t>(corner) + 100) - 0.5) * 160.0;
                ring[static_cast<size_t>(level)].push_back({middle[0] + oy::cos(angle) * reach,
                    middle[1] + oy::sin(angle) * reach, z + lift});
            }
        }

        for (int level = 0; level < rings; ++level)
        {
            const std::vector<OutdoorModelPoint> &lower = ring[static_cast<size_t>(level)];
            const std::vector<OutdoorModelPoint> &upper = ring[static_cast<size_t>(level) + 1];
            const Point3 &middle = middles[static_cast<size_t>(level)];

            for (int corner = 0; corner < corners; ++corner)
            {
                const size_t a = static_cast<size_t>(corner);
                const size_t b = static_cast<size_t>((corner + 1) % corners);
                const Point3 outward = {(lower[a][0] + lower[b][0]) * 0.5 - middle[0],
                    (lower[a][1] + lower[b][1]) * 0.5 - middle[1], 0.0};
                const std::vector<std::vector<OutdoorModelPoint>> triangles = {{lower[a], lower[b], upper[b]},
                    {lower[a], upper[b], upper[a]}};

                for (const std::vector<OutdoorModelPoint> &triangle : triangles)
                {
                    std::vector<OutdoorModelPoint> turned = triangle;
                    const Point3 normal = normalOf(turned);

                    if (normal[0] * outward[0] + normal[1] * outward[1] + normal[2] * outward[2] < 0.0)
                    {
                        std::reverse(turned.begin(), turned.end());
                    }

                    builder.addSurface(turned, fall.rockTexture, event);
                }
            }
        }

        // The top: a low peak over the last ring.
        const std::vector<OutdoorModelPoint> &last = ring[static_cast<size_t>(rings)];
        const Point3 &middle = middles[static_cast<size_t>(rings)];
        const OutdoorModelPoint peak = {middle[0], middle[1], middle[2] + radius * 0.25};

        for (int corner = 0; corner < corners; ++corner)
        {
            std::vector<OutdoorModelPoint> triangle = {last[static_cast<size_t>(corner)],
                last[static_cast<size_t>((corner + 1) % corners)], peak};

            if (normalOf(triangle)[2] < 0.0)
            {
                std::reverse(triangle.begin(), triangle.end());
            }

            builder.addSurface(triangle, fall.rockTexture, event);
        }
    }
}
}
