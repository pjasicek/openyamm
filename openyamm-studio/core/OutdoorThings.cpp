#include "core/OutdoorThings.h"

#include "core/ChestKinds.h"

#include "core/Coplanar.h"
#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/MapLoad.h"
#include "core/MonsterRelations.h"
#include "core/OutdoorModel.h"
#include "core/OutdoorWaysIn.h"
#include "core/Polygon.h"
#include "core/SketchRead.h"
#include "core/TableNames.h"

#include "engine/ImageAssetLoader.h"
#include "game/FaceEnums.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <functional>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>

// What stands on an outdoor map and is no house, and what the shipped maps use for which (measured on Ravenshore,
// Harmondale, New Sorpigal and Dagger Wound; output/studio_s4c/analysis):
//
//   building models, each with its event on all of its faces:
//     chests (19 faces, 96 x 64 x 80, `evt.OpenChest`), crates (a cube of 64), wells (a ring of six or eight sides
//     256 across with water in it, Harmondale's under a small roof), fountains (a low basin 512 to 800 across with
//     water and a middle piece), obelisks (a shaft 128 to 416 wide and 960 to 1280 high), signposts and shop
//     signs (a post and a board), bridges and piers (a deck on the banks or on posts, with or without kerbs),
//     walls and forts (wall rings with walkable tops), stairs and platforms;
//   decorations (sprites or 3D decoration models from decoration_data.txt), placed one by one:
//     trees, rocks, plants, barrels, sacks, torches, camp fires, statues, buoys, and in Might and Magic 6 the
//     fountains' water jets, chests on the ground and street signs;
//   actors of the scene's starting state: townsfolk and guards, by their rows of the monster table.
//
// So a sketch's `structures` are the small library of the first group (`kind`), `kind: decoration` places one of
// the second by name, and `actors` are the third.
//
// What has no form (measured on the same maps, output/studio_s4d/orig): Ravenshore's two ships are ten models of
// 45 to 64 faces each (hull, deck, two masts, sails, rails, a gangway whose one face is the door of the boat
// service), 574 faces in all; Harmondale's six wagons 63 or 64 faces each (a box on spoked wheels, a shaft); the
// crystal four models of leaning shards up to 2048 high; cannons, tents and the crane are of the same kind: a
// shape of its own, drawn by hand, that no rule of parts makes. For these the honest word is an import by name:
// `kind: model` takes models of a shipped outdoor map of the asset root (`from: {map, models}`), as they are, to
// the place the sketch says, and puts the structure's event on their faces. It is the smallest building import:
// one world's maps, no turning, the whole thing clicked.
//
// A structure stands on the land at `at` (the stored height there, plus `raise`). Its event (a title, and what a
// click does: a house, another map, a chest, preset effects or Lua) is on all its faces.
//
// More than one event on a thing, as measured on the same maps (output/studio_s4d/orig): Ravenshore's fountain
// carries its drink on the 23 faces of its water and a name on the other 73; the Vault of Time's hatch is one
// face of 87, the rest say its name; a cave mouth's door is one face of 48. So `hint` is a second event that only
// says a name, on the faces that are not the thing's used part (a doorway's door, a basin's water, a sign's
// board, a platform's top). Harmondale's signposts are a post with three boards, each board's two faces with a
// title of their own (`arms`). Its hill fort has four floor faces with the face bit PressurePlate and an event
// that nobody clicks (`trigger: step`).

namespace OpenYAMM::Studio
{
namespace
{
constexpr double Pi = 3.14159265358979323846;
const char *SketchFile = "sketch.yml";

using Point2 = std::array<double, 2>;

struct WorldLook
{
    const char *pWorld;
    const char *pStone;
    const char *pWood;
    const char *pWater;
    const char *pChestSide;
    const char *pChestLid;
    const char *pCrate;
    const char *pSign;
    const char *pDoor;
};

// The textures a structure gets that names none: what the shipped maps of each world put on such things most.
constexpr WorldLook WorldLooks[] = {
    {"mm8", "t06b01", "bwooda1", "wtrtyl", "gt002a", "gt002b", "cr_w128b", "trim1_16", "t14c03"},
    {"mm7", "chb1", "7trimd", "7wtrtyl", "7gt002a", "7gt002b", "7gt001a", "trim2_32", "hhm1d"},
    {"mm6", "rblbw", "cedvwal1", "6wtrtyl", "cr64", "crside", "cr64", "cbeam5", "tewd"},
};



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

double numberOr(const YAML::Node &node, const char *pKey, double fallback)
{
    double number = fallback;
    return numberOfNode(childOf(node, pKey), number) ? number : fallback;
}

bool pointOf(const YAML::Node &node, Point2 &point)
{
    return node.IsDefined() && node.IsSequence() && node.size() == 2 && numberOfNode(node[0], point[0])
        && numberOfNode(node[1], point[1]);
}

bool flagOf(const YAML::Node &node, const char *pKey)
{
    return textOf(node, pKey) == "true";
}

std::string lowerCase(const std::string &text)
{
    std::string result = text;
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return result;
}

std::string luaQuote(const std::string &text)
{
    std::string result = "\"";

    for (const char character : text)
    {
        if (character == '"' || character == '\\')
        {
            result.push_back('\\');
        }

        result.push_back(character == '\n' ? ' ' : character);
    }

    return result + "\"";
}

std::vector<std::vector<std::string>> tableRows(const std::string &text)
{
    std::vector<std::vector<std::string>> rows;
    std::istringstream lines(text);
    std::string line;

    while (std::getline(lines, line))
    {
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        std::vector<std::string> cells;
        size_t start = 0;

        while (true)
        {
            const size_t tab = line.find('\t', start);
            cells.push_back(line.substr(start, tab == std::string::npos ? std::string::npos : tab - start));

            if (tab == std::string::npos)
            {
                break;
            }

            start = tab + 1;
        }

        rows.push_back(cells);
    }

    return rows;
}

bool wholeNumber(const std::string &text, int &number)
{
    const std::from_chars_result result = std::from_chars(text.data(), text.data() + text.size(), number);
    return !text.empty() && result.ec == std::errc() && result.ptr == text.data() + text.size();
}

double lengthOf(const Point2 &from, const Point2 &to)
{
    return oy::hypot(to[0] - from[0], to[1] - from[1]);
}

// The four corners of a strip along a stretch: counter-clockwise seen from above when `left` is on the left of
// the way from `from` to `to`.
std::vector<Point2> strip(const Point2 &fromRight, const Point2 &toRight, const Point2 &toLeft, const Point2 &fromLeft)
{
    return {fromRight, toRight, toLeft, fromLeft};
}

// A face turned to look along `normal` (its corners reversed if they ran the other way).
std::vector<OutdoorModelPoint> outdoorFacing(std::vector<OutdoorModelPoint> points, const std::array<double, 3> &normal)
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

class ThingRaiser
{
public:
    void setMountRoot(const std::filesystem::path &mountRoot)
    {
        m_mountRoot = mountRoot;
    }

    ThingRaiser(
        const Project &project,
        const LoweredOutdoorMap &loweredMap,
        const std::filesystem::path &assetRoot,
        IdsLock &ids,
        OutdoorEventWords &words,
        OutdoorThings &things,
        std::vector<ProjectIssue> &issues,
        std::vector<std::string> &warnings)
        : m_project(project)
        , m_lowered(loweredMap)
        , m_assetRoot(assetRoot)
        , m_ids(ids)
        , m_words(words)
        , m_things(things)
        , m_issues(issues)
        , m_warnings(warnings)
    {
        for (const WorldLook &look : WorldLooks)
        {
            if (m_lowered.styleWorld == look.pWorld)
            {
                m_pLook = &look;
            }
        }
    }

    bool raise()
    {
        const size_t before = m_issues.size();
        const YAML::Node sketch = m_project.document(SketchFile);
        const YAML::Node structures = childOf(sketch, "structures");
        // Every id its number first, so that a new one never takes the number of one further down.
        std::set<std::string> seen;

        for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size();
             ++index)
        {
            const YAML::Node node = structures[index];
            const std::string id = textOf(node, "id");
            const std::string path = "structures[" + std::to_string(index) + "]";

            if (id.empty() || !seen.insert(id).second)
            {
                add(path + ".id", id.empty() ? "a structure needs an `id` of its own (thing:market_well)"
                    : "two structures have the id " + id + "; give each its own");
                continue;
            }

            if (textOf(node, "kind") != "building" && carriesEvent(node))
            {
                IdsLock::number(m_ids.events, "evt:" + id, 1);
            }

            // Below zero the thing stands in the land: right for a chest in a pit under a hole, buried otherwise.
            const double lift = numberOr(node, "raise", 0.0);

            if (lift < 0.0 && textOf(node, "kind") != "model")
            {
                m_warnings.push_back("structures: " + id + " stands " + formatNumber(-lift) + " under the land "
                    "(`raise: " + formatNumber(lift) + "`): it is buried unless a pit or a hole is over it");
            }
        }

        if (m_issues.size() != before)
        {
            return false;
        }

        size_t unbuilt = 0;

        for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size();
             ++index)
        {
            const YAML::Node node = structures[index];
            const std::string kind = textOf(node, "kind");
            m_path = "structures[" + std::to_string(index) + "]";
            m_id = textOf(node, "id");

            if (kind == "building")
            {
                // Read with the plots (core/OutdoorBuildings).
                continue;
            }

            m_event = eventOf(node);

            if (kind == "decoration")
            {
                placeDecoration(node);
                continue;
            }

            Game::OutdoorBModel model;
            model.name = m_id;
            model.secondaryName = m_id;
            OutdoorModelBuilder builder(model, &m_lowered.wallTiles);
            bool known = true;
            m_pModel = &model;
            m_usedFaces.clear();
            m_liquidTextures.clear();

            if (kind == "wall")
            {
                raiseWall(node, builder);
            }
            else if (kind == "bridge")
            {
                raiseBridge(node, builder);
            }
            else if (kind == "well" || kind == "fountain")
            {
                raiseBasin(node, builder, kind == "fountain");
            }
            else if (kind == "obelisk")
            {
                raiseObelisk(node, builder);
            }
            else if (kind == "chest" || kind == "crate")
            {
                raiseChest(node, builder, kind == "crate");
            }
            else if (kind == "sign")
            {
                raiseSign(node, builder);
            }
            else if (kind == "platform")
            {
                raisePlatform(node, builder);
            }
            else if (kind == "stairs")
            {
                raiseStairs(node, builder);
            }
            else if (kind == "doorway")
            {
                raiseDoorway(node, builder);
            }
            else if (kind == "fence")
            {
                raiseFence(node, builder);
            }
            else if (kind == "waterfall")
            {
                raiseWaterfall(builder);
            }
            else if (kind == "barrier")
            {
                raiseBarrier(node, builder);
            }
            else if (kind == "culvert")
            {
                raiseCulvert(node, builder);
            }
            else if (kind == "cave_mouth" || kind == "hatch")
            {
                raiseCave(builder);
            }
            else if (kind == "portal")
            {
                raisePortal(node, builder);
            }
            else if (kind == "arch")
            {
                raiseArch(node, builder);
            }
            else if (kind == "stone_ring" || kind == "trilithon")
            {
                raiseStoneRing(node, builder, kind == "trilithon");
            }
            else if (kind == "walkway")
            {
                raiseWalkway(node, builder);
            }
            else if (kind == "deck")
            {
                raiseDeck(node, builder);
            }
            else if (kind == "tent")
            {
                raiseTent(node, builder);
            }
            else if (kind == "arcade")
            {
                raiseArcade(node, builder);
            }
            else if (kind == "model")
            {
                raiseImport(node, model);
            }
            else
            {
                known = false;
                add(m_path + ".kind", "a structure's kind is building, wall, fence, barrier, waterfall, bridge, well, fountain, obelisk, "
                    "chest, crate, sign, platform, stairs, doorway, cave_mouth, hatch, culvert, portal, arch, stone_ring, trilithon, walkway, deck, tent, arcade, decoration or model; `" + kind + "` is none of them (a "
                    "ship, a wagon or a statue needs a model of its own: import one of a shipped map with `kind: "
                    "model` and `from: {map: out02.odm, models: [...]}`, or leave it out)");
            }

            if (known && !model.faces.empty())
            {
                for (Game::OutdoorBModelFace &face : model.faces)
                {
                    const std::map<std::string, uint32_t>::const_iterator liquid =
                        m_liquidTextures.find(face.textureName);

                    if (liquid != m_liquidTextures.end())
                    {
                        face.attributes |= liquid->second;
                    }
                }

                if (flagOf(node, "ethereal"))
                {
                    // Drawn, but walked through (the game's Untouchable bit: outb1's DunEntB1 front).
                    for (Game::OutdoorBModelFace &face : model.faces)
                    {
                        face.attributes |= Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
                    }
                }

                applyHintAndTrigger(node, kind, model);
                builder.finish();
                m_things.covered.push_back({model.minX / OutdoorCellSize + OutdoorNodeCount / 2,
                    OutdoorNodeCount / 2 - model.maxY / OutdoorCellSize,
                    model.maxX / OutdoorCellSize + OutdoorNodeCount / 2,
                    OutdoorNodeCount / 2 - model.minY / OutdoorCellSize});
                m_things.models.push_back(model);
            }
            else if (known)
            {
                ++unbuilt;
            }
        }

        m_pModel = nullptr;
        raiseActors(childOf(sketch, "actors"));
        raiseItems(childOf(sketch, "items"));
        raiseSounds(childOf(sketch, "sounds"));
        raiseEvents(childOf(sketch, "events"));

        if (unbuilt != 0)
        {
            m_warnings.push_back("structures: " + std::to_string(unbuilt) + " raised no face");
        }

        if (!m_peacefulGroups.empty())
        {
            // The scene cannot say a group is peaceful; an event on entering the map does, once per fill
            // (peacefulGroupsBody), before the project's own load events, which may change it.
            OutdoorEventPlan event;
            event.id = "evt:studio_peaceful_groups";
            event.number = static_cast<uint16_t>(IdsLock::number(m_ids.events, event.id, 1));
            event.body = peacefulGroupsBody(std::vector<int>(m_peacefulGroups.begin(), m_peacefulGroups.end()));
            m_things.events.push_back(event);
            m_things.onLoad.insert(m_things.onLoad.begin(), event.number);
        }

        m_things.peacefulGroups = m_peacefulGroups;
        raiseRelations(childOf(sketch, "relations"));
        return m_issues.size() == before;
    }

private:
    void add(const std::string &path, const std::string &message)
    {
        m_issues.push_back({SketchFile, path, message, "structure"});
    }

    // sketch.yml `relations`, as objects.yml's indoors (core/MonsterRelations.h): one event of the build's own on
    // entering the map sets them.
    void raiseRelations(const YAML::Node &relations)
    {
        if (!relations.IsDefined() || !relations.IsSequence() || relations.size() == 0)
        {
            return;
        }

        std::string monsterText;

        if (!readWorldTable(m_assetRoot, m_lowered.world, "monster_data.txt", "monster_data", monsterText))
        {
            m_warnings.push_back("relations: " + std::to_string(relations.size()) + " entries are left out: naming "
                "monsters needs the monster tables of an asset root (--assets)");
            return;
        }

        OutdoorEventPlan event;
        event.id = "evt:studio_relations";

        if (std::any_of(m_things.events.begin(), m_things.events.end(),
                [&event](const OutdoorEventPlan &other) { return other.id == event.id; }))
        {
            m_issues.push_back({SketchFile, "events", "the id " + event.id + " is the build's own (the event that "
                "sets sketch.yml `relations`): give the event another id", "reference"});
            return;
        }

        const std::vector<std::vector<std::string>> monsterRows = parseTableRows(monsterText);
        m_things.relations = readMonsterRelations(relations, SketchFile,
            [this, &monsterRows](const YAML::Node &value, const std::string &path) -> std::optional<int>
            {
                const std::vector<std::string> *pRow = namedTableRow(monsterRows, value, {1, 2}, std::nullopt,
                    nullptr, "monster", "monster_data.txt", SketchFile, path, m_issues);
                return pRow != nullptr ? std::optional<int>(cellNumber(*pRow, 0).value_or(0)) : std::nullopt;
            },
            m_issues);
        event.body = monsterRelationLines(m_things.relations);

        if (event.body.empty())
        {
            return;
        }

        event.number = static_cast<uint16_t>(IdsLock::number(m_ids.events, event.id, 1));
        m_things.events.push_back(event);
        m_things.onLoad.push_back(event.number);
    }

    static bool carriesEvent(const YAML::Node &node)
    {
        const std::string kind = textOf(node, "kind");

        for (const char *pKey : {"title", "house", "into", "effects", "lua", "chest"})
        {
            if (childOf(node, pKey).IsDefined())
            {
                return true;
            }
        }

        return kind == "chest" || kind == "crate";
    }

    // The place of a thing in world units: `at` in cells.
    bool placeOf(const YAML::Node &node, Point2 &world, double &ground, const char *pKey = "at")
    {
        Point2 cell = {0.0, 0.0};

        if (!pointOf(childOf(node, pKey), cell) || cell[0] < 0.0 || cell[1] < 0.0 || cell[0] > OutdoorNodeCount - 1
            || cell[1] > OutdoorNodeCount - 1)
        {
            add(m_path + "." + pKey, std::string("`") + pKey + "` is the place [x, y] in cells (fractions allowed), "
                "inside the map (0 to 127)");
            return false;
        }

        world = toWorld(cell);
        ground = m_lowered.storedHeightAt(cell[0], cell[1]) + numberOr(node, "raise", 0.0);
        return true;
    }

    static Point2 toWorld(const Point2 &cell)
    {
        return {(cell[0] - OutdoorNodeCount / 2) * OutdoorCellSize,
            (OutdoorNodeCount / 2 - cell[1]) * OutdoorCellSize};
    }

    double groundAt(const Point2 &world) const
    {
        return m_lowered.storedHeightAt(world[0] / OutdoorCellSize + OutdoorNodeCount / 2,
            OutdoorNodeCount / 2 - world[1] / OutdoorCellSize);
    }

    // The game's ground at a place in world units (its cells' two triangles: `groundHeightAt`), what things stood
    // on the land stand on.
    double nativeGroundAt(const Point2 &world) const
    {
        return m_lowered.groundHeightAt(world[0] / OutdoorCellSize + OutdoorNodeCount / 2,
            OutdoorNodeCount / 2 - world[1] / OutdoorCellSize);
    }

    // The lowest of the game's ground under an outline's corners: where a chest or a crate stands, so no corner
    // floats (the higher side sinks into the slope).
    double lowestGroundUnder(const std::vector<Point2> &outline) const
    {
        double lowest = 1.0e30;

        for (const Point2 &corner : outline)
        {
            lowest = std::min(lowest, nativeGroundAt(corner));
        }

        return lowest;
    }

    // A flat bridge footing covers pieces of the native terrain triangles. Their lowest point is at a footprint
    // corner, a grid vertex inside it, or where its outline crosses a grid edge (including the NW-SE diagonals).
    double bridgeFootHeight(std::vector<Point2> footprint) const
    {
        for (Point2 &point : footprint)
        {
            for (double &coordinate : point)
            {
                coordinate = std::clamp(std::round(coordinate), -32768.0, 32767.0);
            }
        }
        double lowest = lowestGroundUnder(footprint);
        Point2 low = footprint.front(), high = low;
        for (size_t i = 0; i < footprint.size(); ++i)
        {
            const Point2 &a = footprint[i], &b = footprint[(i + 1) % footprint.size()];
            for (size_t axis = 0; axis < 2; ++axis)
            {
                low[axis] = std::min(low[axis], a[axis]);
                high[axis] = std::max(high[axis], a[axis]);
            }
            const auto crossGrid = [&](double start, double end)
            {
                const double first = (std::floor(std::min(start, end) / OutdoorCellSize) + 1) * OutdoorCellSize;
                for (double line = first; line < std::max(start, end); line += OutdoorCellSize)
                {
                    const double t = (line - start) / (end - start);
                    lowest = std::min(lowest, nativeGroundAt({a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])}));
                }
            };
            crossGrid(a[0], b[0]);
            crossGrid(a[1], b[1]);
            crossGrid(a[0] + a[1], b[0] + b[1]);
        }
        for (double y = std::ceil(low[1] / OutdoorCellSize) * OutdoorCellSize; y <= high[1]; y += OutdoorCellSize)
        {
            for (double x = std::ceil(low[0] / OutdoorCellSize) * OutdoorCellSize; x <= high[0]; x += OutdoorCellSize)
            {
                if (pointInOrOnPolygon(footprint, {x, y}))
                {
                    lowest = std::min(lowest, nativeGroundAt({x, y}));
                }
            }
        }
        return lowest - OutdoorWaterBedDepth - 32.0;
    }

    // A role's texture: a name, or {texture, liquid: water | lava, flow: up | down | left | right} for a liquid
    // face (core/OutdoorModel `outdoorLiquidBits`: Hermit's Isle's lava temple, the Plane of Fire's lava streams).
    // The liquid's bits are laid on the thing's faces of that texture once it stands.
    std::string textureOf(const YAML::Node &node, const char *pRole, const char *pFallback)
    {
        const YAML::Node entry = childOf(childOf(node, "textures"), pRole);

        if (!entry.IsDefined() || !entry.IsMap())
        {
            return textOf(childOf(node, "textures"), pRole, pFallback == nullptr ? "" : pFallback);
        }

        const std::string name = textOf(entry, "texture", textOf(entry, "name", pFallback == nullptr ? ""
            : pFallback));
        const uint32_t bits = outdoorLiquidBits(textOf(entry, "liquid"), textOf(entry, "flow"), m_lowered.styleWorld);

        if (name.empty() || bits == UINT32_MAX)
        {
            add(m_path + ".textures." + pRole, "a texture is a name, or {texture: <name>, liquid: water | lava, "
                "flow: up | down | left | right} (either of liquid and flow may be left out)");
            return name;
        }

        m_liquidTextures[name] |= bits;
        return name;
    }

    // A point turned about a middle by the thing's `turn` (degrees clockwise seen from above).
    static Point2 turned(const Point2 &middle, double east, double north, double turn)
    {
        const double angle = -turn * Pi / 180.0;
        return {middle[0] + east * oy::cos(angle) - north * oy::sin(angle),
            middle[1] + east * oy::sin(angle) + north * oy::cos(angle)};
    }

    static std::vector<Point2> turnedBox(const Point2 &middle, double width, double depth, double turn,
        double east = 0.0, double north = 0.0)
    {
        return {turned(middle, east - width * 0.5, north - depth * 0.5, turn),
            turned(middle, east + width * 0.5, north - depth * 0.5, turn),
            turned(middle, east + width * 0.5, north + depth * 0.5, turn),
            turned(middle, east - width * 0.5, north + depth * 0.5, turn)};
    }

    static std::vector<Point2> ringOf(const Point2 &middle, double radius, int sides, double turn = 0.0)
    {
        std::vector<Point2> ring;

        for (int side = 0; side < sides; ++side)
        {
            const double angle = (side + 0.5) * 2.0 * Pi / sides - turn * Pi / 180.0;
            ring.push_back({middle[0] + radius * oy::cos(angle), middle[1] + radius * oy::sin(angle)});
        }

        return ring;
    }

    // ---- Events ----

    // `same_event_as`: the structure's faces carry the event of another thing (a step trap of several plates, a
    // sign carrying its shop's door): a structure's id, or a building's (its own door, else its name), or
    // {building, door: n} (the n-th of its `doors`, 0 its own door) or {building, part} (a part's own event).
    uint16_t sharedEventOf(const YAML::Node &node)
    {
        const YAML::Node same = childOf(node, "same_event_as");
        const std::string where = m_path + ".same_event_as";

        if (carriesEvent(node) || flagOf(node, "blank"))
        {
            add(where, "a thing that carries another's event says and does what that event does: leave out its "
                "own `title`, `house`, `into`, `chest`, `effects`, `lua` and `blank` (a chest or crate has its own)");
            return 0;
        }

        for (const char *pKey : {"condition", "locked_text", "else_effects", "once"})
        {
            if (childOf(node, pKey).IsDefined())
            {
                add(where, std::string("`") + pKey + "` belongs to the event, which is the other thing's: write it "
                    "there");
                return 0;
            }
        }

        std::string key;

        if (same.IsScalar())
        {
            const std::string named = same.Scalar();

            if (named.rfind("building:", 0) == 0)
            {
                key = named;
            }
            else
            {
                const YAML::Node structures = childOf(m_project.document(SketchFile), "structures");

                for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size();
                     ++index)
                {
                    const YAML::Node other = structures[index];

                    if (textOf(other, "id") != named || textOf(other, "kind") == "building")
                    {
                        continue;
                    }

                    if (named == m_id || !carriesEvent(other))
                    {
                        add(where, named == m_id ? "a thing cannot carry its own event"
                            : "the structure " + named + " carries no event of its own (it says and does nothing, "
                            "or carries another's): name the thing whose `title`, `effects` or `lua` it is");
                        return 0;
                    }

                    return static_cast<uint16_t>(IdsLock::number(m_ids.events, "evt:" + named, 1));
                }

                add(where, "no structure has the id " + named + " (a building is named building:<id>; a building "
                    "drawn in `structures` by its structure id as building:<id> too)");
                return 0;
            }
        }
        else if (same.IsMap() && !textOf(same, "building").empty())
        {
            const bool door = childOf(same, "door").IsDefined();
            const bool part = childOf(same, "part").IsDefined();
            double number = 0.0;

            if (door == part || (door && (!numberOfNode(childOf(same, "door"), number) || number < 0.0
                || number != std::floor(number))))
            {
                add(where, "{building: building:<id>, door: n} names the n-th of the building's `doors` (0 its own "
                    "`door`), {building: building:<id>, part: <part id>} a part's own event: one of them");
                return 0;
            }

            key = textOf(same, "building") + (door ? "/door:" + std::to_string(static_cast<int>(number))
                : "/part:" + textOf(same, "part"));
        }
        else
        {
            add(where, "same_event_as names a structure (thing:plate_1), a building (building:inn: its door, else "
                "its name) or {building: building:<id>, door: n | part: <id>}");
            return 0;
        }

        const std::map<std::string, uint16_t>::const_iterator found = m_things.buildingEvents.find(key);

        if (found == m_things.buildingEvents.end() || found->second == 0)
        {
            add(where, key + " carries no event: a building's door event is there when the door opens something "
                "(`house`, `into`, `effects`), its name event when it has a `title`, a part's when the part has a "
                "`title` or `effects`");
            return 0;
        }

        return found->second;
    }

    // The event of a structure: what its faces run. 0 when the structure says nothing and does nothing.
    uint16_t eventOf(const YAML::Node &node)
    {
        if (childOf(node, "same_event_as").IsDefined())
        {
            return sharedEventOf(node);
        }

        if (flagOf(node, "blank"))
        {
            // An event of its own that has no title and no handler: a click says and does nothing, as Harmondale's
            // gate sign (event 1 of 7out02.odm).
            if (carriesEvent(node) || childOf(node, "hint").IsDefined() || textOf(node, "trigger") == "step")
            {
                add(m_path + ".blank", "`blank` is a thing whose event has no title and does nothing: leave out "
                    "`title`, `hint`, `house`, `into`, `chest`, `effects`, `lua` and `trigger: step`, or `blank`");
                return 0;
            }

            return static_cast<uint16_t>(IdsLock::number(m_ids.events, "evt:" + m_id, 1));
        }

        if (!carriesEvent(node))
        {
            for (const char *pKey : {"condition", "locked_text", "else_effects", "once"})
            {
                if (childOf(node, pKey).IsDefined())
                {
                    add(m_path + "." + pKey, std::string("`") + pKey + "` belongs to what a click does, and this "
                        "structure does nothing: give it `house`, `into`, `chest`, `effects` or `lua`, or leave `"
                        + pKey + "` out");
                }
            }

            return 0;
        }

        OutdoorEventPlan event;
        event.id = "evt:" + m_id;
        event.number = static_cast<uint16_t>(IdsLock::number(m_ids.events, event.id, 1));
        const std::string kind = textOf(node, "kind");
        event.title = textOf(node, "title", kind == "chest" || kind == "crate" ? "Chest" : "");
        const YAML::Node house = childOf(node, "house");
        const YAML::Node into = childOf(node, "into");
        const bool chest = kind == "chest" || kind == "crate" || childOf(node, "chest").IsDefined();
        const int ways = (house.IsDefined() ? 1 : 0) + (into.IsDefined() ? 1 : 0) + (chest ? 1 : 0);

        if (ways > 1)
        {
            add(m_path, "a structure's click enters a `house`, leads `into` a map or opens a `chest`: one of them "
                "(more is `effects` or `lua`)");
            return 0;
        }

        // `once`, then the lock: unless the condition holds, else_effects, locked_text and no more.
        m_words.lock(node, m_path, "once." + m_id, event.body);

        if (house.IsDefined())
        {
            double number = 0.0;

            if (!numberOfNode(house, number) || number < 1.0)
            {
                add(m_path + ".house", "house is the number of a row of the house table");
                return 0;
            }

            event.body.push_back("evt.EnterHouse(" + std::to_string(static_cast<int>(number)) + ")");
        }

        if (into.IsDefined())
        {
            const std::string map = textOf(into, "map");
            const YAML::Node at = childOf(into, "at");
            int arrival[3] = {0, 0, 0};
            int facing = static_cast<int>(numberOr(into, "facing", 0.0));

            for (size_t axis = 0; at.IsDefined() && at.IsSequence() && axis < 3 && axis < at.size(); ++axis)
            {
                arrival[axis] = at[axis].as<int>(0);
            }

            if (map.empty())
            {
                add(m_path + ".into", "into names the map: {map: d07.blv, at: [x, y, z], facing: 512}");
                return 0;
            }

            // A named arrival of the map (D-4): its place and facing from the installed map's <stem>.studio.yml.
            if (const std::string named = textOf(into, "arrival"); !named.empty())
            {
                MapArrival found;
                std::string warning;

                if (at.IsDefined())
                {
                    add(m_path + ".into", "into takes `at` or `arrival`, not both");
                    return 0;
                }

                if (!resolveMapArrival(m_assetRoot, m_mountRoot, m_lowered.world, map, named, found, warning))
                {
                    add(m_path + ".into.arrival", warning);
                    return 0;
                }

                if (!warning.empty())
                {
                    m_warnings.push_back(m_path + ".into.arrival: " + warning);
                }

                std::copy(std::begin(found.at), std::end(found.at), arrival);
                facing = childOf(into, "facing").IsDefined() ? facing : found.facing;
            }

            MoveScreen screen;
            std::string screenError;

            if (!readMoveScreen(childOf(into, "screen"), map, screen, screenError))
            {
                add(m_path + ".into.screen", screenError);
                return 0;
            }

            event.body.push_back("evt.MoveToMap(" + std::to_string(arrival[0]) + ", " + std::to_string(arrival[1])
                + ", " + std::to_string(arrival[2]) + ", "
                + std::to_string(facing) + ", 0, 0, " + std::to_string(screen.text) + ", "
                + std::to_string(screen.picture) + ", " + luaQuote(map) + moveScreenOptions(screen) + ")");
        }

        if (chest)
        {
            const int number = readChest(childOf(node, "chest"));
            event.body.push_back("evt.OpenChest(" + std::to_string(number) + ")");
            m_things.chestOfEvent[event.number] = number;
        }

        m_words.actions(node, m_path, event.body);
        m_things.events.push_back(event);
        return event.number;
    }

    // `hint` and `trigger: step`, once the model stands. A hint is a second event that only says a name: the
    // faces that are not the thing's used part carry it. A thing that is stepped on runs its event from its
    // faces one can stand on, which nobody clicks; its other faces say the hint or nothing.
    void applyHintAndTrigger(const YAML::Node &node, const std::string &kind, Game::OutdoorBModel &model)
    {
        const std::string hint = textOf(node, "hint");
        const std::string trigger = textOf(node, "trigger", "click");
        const bool step = trigger == "step";

        if (trigger != "click" && !step)
        {
            add(m_path + ".trigger", "trigger is click (the default: the thing is used) or step (the party walks "
                "onto it); what runs on entering the map or by the clock is an entry of the sketch's `events`");
            return;
        }

        if (hint.empty() && childOf(node, "hint_shared").IsDefined())
        {
            add(m_path + ".hint_shared", "`hint_shared` shares the thing's `hint`: give it one");
            return;
        }

        if (hint.empty() && !step)
        {
            return;
        }

        uint16_t hintEvent = 0;

        if (!hint.empty())
        {
            // `hint_shared` (batch O-H): one event for every thing of the map whose shared hint says the same, as
            // the originals have it (Erathia's "Well", 201, on its five wells).
            const bool shared = textOf(node, "hint_shared") == "true";
            OutdoorEventPlan event;
            event.id = shared ? outdoorSharedHintId(hint) : "evt:hint:" + m_id;
            event.number = static_cast<uint16_t>(IdsLock::number(m_ids.events, event.id, 1));
            event.title = hint;

            if (!shared || std::none_of(m_things.events.begin(), m_things.events.end(),
                    [&](const OutdoorEventPlan &other) { return other.id == event.id; }))
            {
                m_things.events.push_back(event);
            }

            hintEvent = event.number;
        }


        const uint32_t clickable = Game::faceAttributeBit(Game::FaceAttribute::Clickable);
        const uint32_t plate = Game::faceAttributeBit(Game::FaceAttribute::PressurePlate);

        if (step)
        {
            if (m_event == 0 || childOf(node, "house").IsDefined() || childOf(node, "into").IsDefined()
                || kind == "chest" || kind == "crate" || childOf(node, "chest").IsDefined())
            {
                add(m_path + ".trigger", "a thing that is stepped on runs `effects` and `lua` (with `condition` and "
                    "`once`): give it those; a house, a map or a chest is entered by a click");
                return;
            }

            // The faces one can stand on: those that look up more than sideways (level, or sloping up to 45
            // degrees).
            m_usedFaces.clear();

            for (size_t face = 0; face < model.faces.size(); ++face)
            {
                if (model.faces[face].planeNormalZ > 46340)
                {
                    m_usedFaces.insert(face);
                }
            }

            if (m_usedFaces.empty())
            {
                add(m_path + ".trigger", "this " + kind + " has no face one can stand on, so nothing steps on it: "
                    "use a platform, a wall, a bridge or stairs");
                return;
            }
        }
        else if (m_usedFaces.empty() || m_usedFaces.size() == model.faces.size())
        {
            add(m_path + ".hint", kind == "model"
                ? "a model taken whole runs its click from every face, so no face is left for a second name: say "
                  "which of its models run the click with `click: [<model>]`, and the others say the `hint`"
                : "a " + kind + " is used as a whole, so it has no faces left for a second name: `hint` is for a "
                  "doorway (its frame), a cave mouth or a hatch (all but its door), a well or a fountain (all but the water), a sign (its post), a platform (its "
                  "sides) and a model with `click`; say the one name with `title`");
            return;
        }

        for (size_t face = 0; face < model.faces.size(); ++face)
        {
            Game::OutdoorBModelFace &modelFace = model.faces[face];

            if (m_usedFaces.contains(face))
            {
                if (step)
                {
                    modelFace.attributes = (modelFace.attributes & ~clickable) | plate;
                }

                continue;
            }

            modelFace.cogTriggeredNumber = hintEvent;

            if (hintEvent == 0)
            {
                modelFace.attributes &= ~clickable;
            }
            else
            {
                modelFace.attributes |= clickable;
            }
        }
    }

    // Marks the faces added since `from` as the thing's used part.
    void markUsed(size_t from)
    {
        for (size_t face = from; m_pModel != nullptr && face < m_pModel->faces.size(); ++face)
        {
            m_usedFaces.insert(face);
        }
    }

    size_t faceCount() const
    {
        return m_pModel != nullptr ? m_pModel->faces.size() : 0;
    }

    // The sketch's `events`: what runs on entering the map or by the clock, with the words of a click.
    void raiseEvents(const YAML::Node &events)
    {
        std::set<std::string> seen;

        for (size_t index = 0; events.IsDefined() && events.IsSequence() && index < events.size(); ++index)
        {
            const YAML::Node node = events[index];
            m_path = "events[" + std::to_string(index) + "]";
            const std::string id = textOf(node, "id");
            const std::string trigger = textOf(node, "trigger");

            if (id.empty() || !seen.insert(id).second || m_words.targets().contains(id))
            {
                add(m_path + ".id", id.empty() ? "an event needs an `id` of its own (evt:fort_fire)"
                    : "the id " + id + " is used twice: give each event and structure its own");
                continue;
            }

            if (trigger != "load" && trigger != "leave" && trigger != "timer" && trigger != "daily"
                && trigger != "weekly")
            {
                add(m_path + ".trigger", "an entry of `events` runs on entering the map (trigger: load), on leaving "
                    "it (trigger: leave), by the clock (trigger: timer, with `every`) or by the calendar (trigger: daily or weekly); a click or a "
                    "step belongs to the thing that is clicked or stepped on (a plot's door, a structure with "
                    "`effects`, a structure with `trigger: step`)");
                continue;
            }

            const bool calendar = trigger == "daily" || trigger == "weekly";
            double hour = -1.0;
            const YAML::Node hourNode = childOf(node, "hour");

            if (hourNode.IsDefined() && (trigger != "daily" || !numberOfNode(hourNode, hour) || hour < 0.0
                || hour > 23.0 || hour != std::floor(hour)))
            {
                add(m_path + ".hour", trigger != "daily"
                    ? "`hour` is for `trigger: daily` (it runs at that hour of every day the party spends in the map); "
                      "a weekly timer runs a week after the last run, at no hour of its own"
                    : "`hour` is the hour of the day, a whole number from 0 to 23");
                continue;
            }

            double every = 0.0;
            const bool timed = numberOfNode(childOf(node, "every"), every);

            if ((trigger == "timer") != timed || (timed && (every < 1.0 || every > 65535.0
                || every != std::floor(every))))
            {
                add(m_path + ".every", "a timer event has `every`: the seconds of play between two runs, a whole "
                    "number from 1 to 65535 (the map's clock counts half minutes of game time, one second of play "
                    "each); a load event has none");
                continue;
            }

            const bool whenFlying = flagOf(node, "when_flying");

            if (childOf(node, "when_flying").IsDefined() && whenFlying && trigger != "timer")
            {
                add(m_path + ".when_flying", "`when_flying` is for `trigger: timer`: the clock runs the event and it "
                    "acts only while the party flies (the dragon towers' fireballs)");
                continue;
            }

            if (!OutdoorEventWords::hasActions(node))
            {
                add(m_path, "the event does nothing: give it `effects` or `lua`");
                continue;
            }

            OutdoorEventPlan event;
            event.id = id.rfind("evt:", 0) == 0 ? id : "evt:" + id;
            event.number = static_cast<uint16_t>(IdsLock::number(m_ids.events, event.id, 1));

            if (whenFlying)
            {
                // As the originals' levitate traps: the timer runs always and its handler acts only on a flying
                // party; the event is listed in the script's levitateTrapEvents as the exported scripts list it.
                event.body.push_back("if not IsAtLeast(IsFlying, 0) then return end");
                m_things.levitateTraps.push_back(event.number);
            }

            m_words.lock(node, m_path, "once." + id, event.body);
            m_words.actions(node, m_path, event.body);
            m_things.events.push_back(event);

            if (calendar)
            {
                // As the scripts exported from the original maps declare calendar timers: a refill ("long") runs
                // on the first visit and once the period has passed since; a daily timer with an hour runs then.
                m_things.calendarTimers[event.number] = hour >= 0.0
                    ? "triggerKind = \"timer\", scheduleKind = \"daily\", startHour = "
                        + std::to_string(static_cast<int>(hour)) + ", startMinute = 0, startSecond = 0"
                    : "triggerKind = \"long\", scheduleKind = \"" + trigger + "\"";
            }
            else if (timed)
            {
                m_things.timers[event.number] = static_cast<int>(every);
            }
            else if (trigger == "leave")
            {
                m_things.onLeave.push_back(event.number);
            }
            else
            {
                m_things.onLoad.push_back(event.number);
            }
        }
    }

    // The chest record of a structure; its number.
    int readChest(const YAML::Node &node)
    {
        OutdoorChestPlan chest;
        chest.id = "chest:" + m_id;
        const int number = IdsLock::number(m_ids.containers, chest.id, 0);
        chest.picture = static_cast<int>(numberOr(node, "picture", 0.0));
        chest.level = static_cast<int>(numberOr(node, "level", 1.0));
        chest.randomItems = static_cast<int>(numberOr(node, "random_items", node.IsDefined() ? 0.0 : 3.0));
        chest.gold = static_cast<int>(numberOr(node, "gold", 0.0));
        chest.trapped = flagOf(node, "trapped");
        const YAML::Node items = childOf(node, "items");

        for (size_t index = 0; items.IsDefined() && items.IsSequence() && index < items.size(); ++index)
        {
            chest.items.push_back(items[index].as<int>(0));
        }

        const YAML::Node levels = childOf(node, "random_levels");
        bool levelsRight = !levels.IsDefined() || levels.IsSequence();

        for (size_t index = 0; levels.IsDefined() && levels.IsSequence() && index < levels.size(); ++index)
        {
            const int level = levels[index].as<int>(0);
            levelsRight = levelsRight && level >= 1 && level <= 7;
            chest.randomLevels.push_back(level);
        }

        if (!levelsRight || chest.randomItems + chest.items.size() + chest.randomLevels.size() > 140)
        {
            add(m_path + ".chest.random_levels", "random_levels is a list of treasure levels, 1 to 7, one for each "
                "more thing the game puts in ([7, 3, 3, 3]: one thing of level 7 and three of level 3); a chest "
                "holds at most 140 things");
        }

        if (chest.level < 1 || chest.level > 7 || chest.randomItems < 0 || chest.randomItems + chest.items.size() > 140
            || chest.picture < 0 || chest.picture > 7)
        {
            add(m_path + ".chest", "a chest has `level` 1 to 7 (the treasure level of what the game puts in), "
                "`random_items` (how many of that level), `items` (item numbers that are in it for certain), at most "
                "140 things in all, and `picture` 0 to 7 (the chest table's row)");
        }

        if (static_cast<size_t>(number) >= m_things.chests.size())
        {
            m_things.chests.resize(number + 1);
        }

        m_things.chests[number] = chest;
        return number;
    }

    // ---- The forms ----

    void placeDecoration(const YAML::Node &node)
    {
        Point2 world = {0.0, 0.0};
        double ground = 0.0;
        const std::string name = lowerCase(textOf(node, "decoration"));

        if (!placeOf(node, world, ground))
        {
            return;
        }

        if (!loadDecorations())
        {
            m_warnings.push_back("structures: the decoration " + m_id + " is left out: naming decorations needs an "
                "asset root (--assets)");
            return;
        }

        const std::map<std::string, int>::const_iterator found = m_decorations.find(name);

        if (found == m_decorations.end())
        {
            add(m_path + ".decoration", "there is no decoration named " + (name.empty() ? "(nothing)" : name)
                + " in engine/data_tables/decoration_data.txt; `oymap assets <text> --kind decoration` lists them");
            return;
        }

        OutdoorPlacedDecoration decoration;
        decoration.name = name;
        decoration.listId = found->second;
        decoration.x = static_cast<int>(std::lround(world[0]));
        decoration.y = static_cast<int>(std::lround(world[1]));
        // `turn`: degrees clockwise seen from above; the ODM keeps degrees counter-clockwise.
        decoration.facing = ((static_cast<int>(std::lround(0.0 - numberOr(node, "turn", 0.0))) % 360) + 360) % 360;
        const double feet = m_lowered.decorationGroundAt(name, world[0] / OutdoorCellSize + OutdoorNodeCount / 2,
            OutdoorNodeCount / 2 - world[1] / OutdoorCellSize, decoration.facing);
        decoration.z = static_cast<int>(std::lround(feet + numberOr(node, "raise", 0.0)));
        m_things.decorations.push_back(decoration);
        m_things.decorationEvents.push_back(m_event);
        m_things.decorationIds.push_back(m_id);

        for (const char *pKey : {"hint", "trigger"})
        {
            if (childOf(node, pKey).IsDefined())
            {
                add(m_path + "." + pKey, std::string("a decoration has one event, run by a click: `") + pKey
                    + "` is for structures that are models");
            }
        }
    }

    bool loadDecorations()
    {
        if (m_decorationsLoaded)
        {
            return !m_decorations.empty();
        }

        m_decorationsLoaded = true;
        std::string text;

        if (!readWorldTable(m_assetRoot, m_lowered.world, "decoration_data.txt", "decorations", text))
        {
            return false;
        }

        for (const std::vector<std::string> &row : tableRows(text))
        {
            int number = 0;

            if (row.size() >= 2 && wholeNumber(row[0], number) && !row[1].empty())
            {
                // An ODM stores a decoration as its row's number less 1.
                m_decorations.emplace(lowerCase(row[1]), number - 1);
            }
        }

        return !m_decorations.empty();
    }

    // The centre line of a wall or a bridge, in world units.
    bool lineOf(const YAML::Node &node, std::vector<Point2> &line)
    {
        const YAML::Node points = childOf(node, "line");

        for (size_t index = 0; points.IsDefined() && points.IsSequence() && index < points.size(); ++index)
        {
            Point2 cell = {0.0, 0.0};

            if (!pointOf(points[index], cell) || cell[0] < 0.0 || cell[1] < 0.0 || cell[0] > OutdoorNodeCount - 1
                || cell[1] > OutdoorNodeCount - 1)
            {
                line.clear();
                break;
            }

            line.push_back(toWorld(cell));
        }

        for (size_t index = 0; index + 1 < line.size(); ++index)
        {
            if (lengthOf(line[index], line[index + 1]) < 16.0)
            {
                line.clear();
            }
        }

        if (line.size() < 2)
        {
            add(m_path + ".line", "`line` is the centre line: two or more points [x, y] in cells (fractions "
                "allowed), inside the map, no two the same");
            return false;
        }

        return true;
    }

    // The two sides of a line moved out by half a width: at every point the corner where the moved stretches meet.
    static void sidesOf(const std::vector<Point2> &line, bool closed, double halfWidth, std::vector<Point2> &left,
        std::vector<Point2> &right)
    {
        const size_t count = line.size();

        for (size_t index = 0; index < count; ++index)
        {
            const bool first = index == 0 && !closed;
            const bool last = index + 1 == count && !closed;
            const Point2 &before = line[first ? index : (index + count - 1) % count];
            const Point2 &here = line[index];
            const Point2 &after = line[last ? index : (index + 1) % count];
            Point2 inDirection = {here[0] - before[0], here[1] - before[1]};
            Point2 outDirection = {after[0] - here[0], after[1] - here[1]};
            const double inLength = oy::hypot(inDirection[0], inDirection[1]);
            const double outLength = oy::hypot(outDirection[0], outDirection[1]);
            inDirection = inLength > 1.0e-9 ? Point2{inDirection[0] / inLength, inDirection[1] / inLength}
                : Point2{outDirection[0] / outLength, outDirection[1] / outLength};
            outDirection = outLength > 1.0e-9 ? Point2{outDirection[0] / outLength, outDirection[1] / outLength}
                : inDirection;
            // The mitre: along the bisector, longer where the line bends (never more than three widths).
            Point2 normal = {-(inDirection[1] + outDirection[1]), inDirection[0] + outDirection[0]};
            const double normalLength = oy::hypot(normal[0], normal[1]);
            normal = normalLength > 1.0e-6 ? Point2{normal[0] / normalLength, normal[1] / normalLength}
                : Point2{-inDirection[1], inDirection[0]};
            const double cosine = normal[0] * -inDirection[1] + normal[1] * inDirection[0];
            const double reach = halfWidth / std::max(cosine, 1.0 / 3.0);
            left.push_back({here[0] + normal[0] * reach, here[1] + normal[1] * reach});
            right.push_back({here[0] - normal[0] * reach, here[1] - normal[1] * reach});
        }
    }

    // A wall along a line: its top is level, `height` above the highest ground under it, and can be walked.
    void raiseWall(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        std::vector<Point2> line;

        if (!lineOf(node, line))
        {
            return;
        }

        const bool closed = flagOf(node, "closed");
        const double height = numberOr(node, "height", 384.0);
        const double thickness = numberOr(node, "thickness", 128.0);
        const double parapet = numberOr(node, "parapet", flagOf(node, "battlements") ? 64.0 : 0.0);
        const bool battlements = flagOf(node, "battlements");
        const std::string wallTexture = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string topTexture = textureOf(node, "top", wallTexture.c_str());

        // Batch O-H: up to 4096 thick (Erathia's Fort Riverstride, a block 1920 thick over the river; Castle
        // Ironfist's gate block, its passage 1152 long).
        if (height < 32.0 || height > 4096.0 || thickness < 32.0 || thickness > 4096.0 || parapet < 0.0
            || parapet > 256.0 || (closed && line.size() < 3))
        {
            add(m_path, "a wall is 32 to 4096 high and 32 to 4096 thick, with a parapet of 0 to 256; a closed wall "
                "(a ring) has three points or more");
            return;
        }

        // Batch O-D: a battered foot (each face drawn in by `batter` from the land up to `batter_height` over it, or
        // the whole wall) and a top that follows the land (`top: follow`: `height` over the land everywhere).
        const double batter = numberOr(node, "batter", 0.0);
        const double batterHeight = numberOr(node, "batter_height", height);
        const bool follow = textOf(node, "top") == "follow";

        if (batter < 0.0 || batter > thickness * 0.5 - 8.0 || batterHeight < 16.0 || batterHeight > height
            || (childOf(node, "batter_height").IsDefined() && batter <= 0.0)
            || (childOf(node, "top").IsDefined() && !follow))
        {
            add(m_path, "a wall's `batter` draws each face in from the land, 0 up to 8 under half its thickness ("
                + formatNumber(thickness * 0.5 - 8.0) + "), over `batter_height` (16 up to its height; the whole "
                "wall when left out); `top: follow` lays its top `height` over the land everywhere");
            return;
        }

        if (follow && parapet > 0.0)
        {
            add(m_path + ".top", "a wall whose top follows the land takes no parapet or battlements (they stand on a "
                "level top)");
            return;
        }

        const YAML::Node gateList = childOf(node, "gates");

        for (size_t index = 0; batter > 0.0 && gateList.IsDefined() && gateList.IsSequence()
             && index < gateList.size(); ++index)
        {
            if (!textOf(gateList[index], "arch").empty())
            {
                add(m_path + ".gates[" + std::to_string(index) + "].arch", "an arched gate stands in an upright "
                    "wall; this wall is battered: leave out `arch` or `batter`");
                return;
            }
        }

        // `raise`: the whole wall stands that much higher (on a deck, a terrace's rim) or lower than the land: its
        // foot, top, batter and gates alike.
        const double lift = numberOr(node, "raise", 0.0);
        const auto landAt = [this, lift](const Point2 &point)
        {
            return groundAt(point) + lift;
        };
        std::vector<Point2> left;
        std::vector<Point2> right;
        sidesOf(line, closed, thickness * 0.5, left, right);
        double highest = -1.0e18;
        double lowest = 1.0e18;
        const size_t stretches = closed ? line.size() : line.size() - 1;

        for (size_t index = 0; index < stretches; ++index)
        {
            const Point2 &from = line[index];
            const Point2 &to = line[(index + 1) % line.size()];
            const int steps = std::max(1, static_cast<int>(lengthOf(from, to) / 256.0));

            for (int step = 0; step <= steps; ++step)
            {
                const double ground = landAt({from[0] + (to[0] - from[0]) * step / steps,
                    from[1] + (to[1] - from[1]) * step / steps});
                highest = std::max(highest, ground);
                lowest = std::min(lowest, ground);
            }
        }

        const double top = highest + height;
        const double foot = lowest - 64.0;
        // Batch O-H: `passage_along`: a way through the wall along its line from end to end, its floor at `floor`
        // (map units), `width` across, `height` to a flat ceiling (Erathia's Fort Riverstride: the road at 1088 east
        // to west through the block over the river's gate).
        struct Passage
        {
            bool given = false;
            double floor = 0.0;
            double width = 256.0;
            double height = 320.0;
        };
        Passage passage;
        const YAML::Node passageNode = childOf(node, "passage_along");

        if (passageNode.IsDefined())
        {
            passage.given = true;
            passage.floor = numberOr(passageNode, "floor", -1.0e18);
            passage.width = numberOr(passageNode, "width", 256.0);
            passage.height = numberOr(passageNode, "height", 320.0);

            if (!passageNode.IsMap() || !childOf(passageNode, "floor").IsDefined() || closed
                || line.size() != 2 || batter > 0.0 || follow || passage.width < 64.0
                || passage.width > thickness - 64.0 || passage.height < 128.0 || passage.floor < foot + 32.0
                || passage.floor + passage.height > top - 16.0)
            {
                add(m_path + ".passage_along", "a passage along a wall runs through a straight wall (two points, not "
                    "closed, upright, its top level) from end to end: {floor (map units, over the wall's foot "
                    + formatNumber(foot) + "), width (64 up to the wall's thickness less 64; 256), height (128 up; "
                    "320), its ceiling at least 16 under the wall's top (" + formatNumber(top) + ")}");
                return;
            }
        }

        // The gates: openings from the ground up, by where along the wall they stand.
        struct Gate
        {
            size_t stretch = 0;
            double from = 0.0;
            double to = 0.0;
            double height = 0.0;
            // `arch`: round or pointed, the head's top at `height`; empty for a flat lintel.
            std::string arch;
            int sides = 6;
        };
        std::vector<Gate> gates;
        const YAML::Node gateNodes = childOf(node, "gates");

        for (size_t index = 0; gateNodes.IsDefined() && gateNodes.IsSequence() && index < gateNodes.size(); ++index)
        {
            Point2 cell = {0.0, 0.0};
            const double width = numberOr(gateNodes[index], "width", 384.0);
            const double gateHeight = numberOr(gateNodes[index], "height", 320.0);

            if (!pointOf(childOf(gateNodes[index], "at"), cell) || width < 64.0 || gateHeight < 64.0)
            {
                add(m_path + ".gates[" + std::to_string(index) + "]", "a gate has `at: [x, y]` (cells; the nearest "
                    "place on the wall's line is taken), a `width` of at least 64 and a `height` of 64 up to the "
                    "wall's top over the ground at the gate");
                continue;
            }

            const Point2 place = toWorld(cell);
            Gate gate;
            double nearest = 1.0e18;

            for (size_t stretch = 0; stretch < stretches; ++stretch)
            {
                const Point2 &from = line[stretch];
                const Point2 &to = line[(stretch + 1) % line.size()];
                const double length = lengthOf(from, to);
                const double along = std::clamp(((place[0] - from[0]) * (to[0] - from[0]) + (place[1] - from[1])
                    * (to[1] - from[1])) / length, 0.0, length);
                const double distance = oy::hypot(from[0] + (to[0] - from[0]) * along / length - place[0],
                    from[1] + (to[1] - from[1]) * along / length - place[1]);

                if (distance < nearest)
                {
                    nearest = distance;
                    // A gate keeps the wall's thickness clear of a corner; of a free end of the wall, a cheek of 32
                    // (batch O-H: Castle Ironfist's gate block, 1024 wide round its arch of 768).
                    const double startClear = !closed && stretch == 0 ? 32.0 : thickness;
                    const double endClear = !closed && stretch + 1 == stretches ? 32.0 : thickness;
                    gate = {stretch, std::max(startClear, along - width * 0.5),
                        std::min(length - endClear, along + width * 0.5), gateHeight,
                        textOf(gateNodes[index], "arch"), static_cast<int>(numberOr(gateNodes[index], "sides", 6.0))};
                }
            }

            if (!gate.arch.empty() && gate.arch != "round" && gate.arch != "pointed" && gate.arch != "segment")
            {
                add(m_path + ".gates[" + std::to_string(index) + "].arch", "a gate's `arch` is round, pointed or segment (a flat arc)");
                continue;
            }

            if (gate.to - gate.from < width - 1.0)
            {
                add(m_path + ".gates[" + std::to_string(index) + "]", "the gate stands too near a corner of the wall "
                    "to fit: a gate keeps the wall's thickness (" + formatNumber(thickness) + ") clear of a corner "
                    "and 32 of a free end of the wall; move it, or make it narrower");
                continue;
            }

            // Batch O-H: a gate may rise over `height` where the ground at it lies lower than the wall's highest
            // ground (Erathia's fort: the arch over the riverbed about 1000, the wall 576 over the banks), up to
            // the wall's top; under a passage along the wall, 32 under its floor.
            const Point2 &stretchFrom = line[gate.stretch];
            const Point2 &stretchTo = line[(gate.stretch + 1) % line.size()];
            const double middle = (gate.from + gate.to) * 0.5 / lengthOf(stretchFrom, stretchTo);
            const double sill = landAt({stretchFrom[0] + (stretchTo[0] - stretchFrom[0]) * middle,
                stretchFrom[1] + (stretchTo[1] - stretchFrom[1]) * middle});
            const double ceiling = passage.given ? passage.floor - 32.0 : top;

            if (sill + gateHeight > ceiling + 0.5)
            {
                add(m_path + ".gates[" + std::to_string(index) + "].height", "the gate's head (" + formatNumber(sill
                    + gateHeight) + ": the ground at it, " + formatNumber(sill) + ", and its height) stands over "
                    + (passage.given ? "the passage along the wall (32 under its floor, " : "the wall's top (")
                    + formatNumber(ceiling) + ")");
                continue;
            }

            gates.push_back(gate);
        }

        for (size_t index = 0; index < stretches; ++index)
        {
            const size_t next = (index + 1) % line.size();
            const double length = lengthOf(line[index], line[next]);
            // Pieces of the stretch between its gates.
            std::vector<Gate> own;

            for (const Gate &gate : gates)
            {
                if (gate.stretch == index)
                {
                    own.push_back(gate);
                }
            }

            std::sort(own.begin(), own.end(), [](const Gate &a, const Gate &b)
            {
                return a.from < b.from;
            });
            const auto across = [&](double along)
            {
                const double share = along / length;
                return std::array<Point2, 2>{Point2{right[index][0] + (right[next][0] - right[index][0]) * share,
                    right[index][1] + (right[next][1] - right[index][1]) * share},
                    Point2{left[index][0] + (left[next][0] - left[index][0]) * share,
                    left[index][1] + (left[next][1] - left[index][1]) * share}};
            };
            // A battered wall or one whose top follows the land: the piece in stretches of 256 at most, each face a
            // plane between the land's line under it (the batter grows from there) and its top.
            const auto ground = [&](double along)
            {
                const double share = along / length;
                return landAt({line[index][0] + (line[next][0] - line[index][0]) * share,
                    line[index][1] + (line[next][1] - line[index][1]) * share});
            };
            const auto topAt = [&](double along)
            {
                return follow ? ground(along) + height : top;
            };
            // A side's point (0 right, 1 left) at a height, drawn in by the batter there.
            const auto sideAt = [&](double along, int side, double z)
            {
                const std::array<Point2, 2> pair = across(along);
                const double width = std::max(lengthOf(pair[0], pair[1]), 1.0e-9);
                const double in = batter > 0.0 ? batter * std::min((z - ground(along)) / batterHeight, 1.0) : 0.0;
                const Point2 &own = pair[side];
                const Point2 &other = pair[1 - side];
                return OutdoorModelPoint{own[0] + (other[0] - own[0]) * in / width,
                    own[1] + (other[1] - own[1]) * in / width, z};
            };
            const auto shaped = [&](double from, double to, double low, bool openStart, bool openEnd, bool underside)
            {
                const int chunks = std::max(1, static_cast<int>(std::ceil((to - from) / 256.0 - 1.0e-9)));
                const std::array<Point2, 2> first = across(from);
                const std::array<double, 3> way = {line[next][0] - line[index][0], line[next][1] - line[index][1], 0.0};
                const std::array<double, 3> right = {first[0][0] - first[1][0], first[0][1] - first[1][1], 0.0};

                for (int chunk = 0; chunk < chunks; ++chunk)
                {
                    const double a = from + (to - from) * chunk / chunks;
                    const double b = from + (to - from) * (chunk + 1) / chunks;
                    // A stretch from the foot goes down into the land under it; a lintel's starts at its own low (a
                    // lintel over an arch has no underside of its own, the arch's soffits close it: it is known by
                    // its low over the foot, else it filled the arched gate from the land up, Burlock's village wall
                    // on Xeen's X4, Discord 2026-11-24).
                    const double base = follow && low <= foot + 0.5 ? std::min(ground(a), ground(b)) - 64.0 : low;
                    const auto knee = [&](double along)
                    {
                        return std::min(batter > 0.0 ? ground(along) + batterHeight : topAt(along), topAt(along));
                    };

                    for (int side = 0; side < 2; ++side)
                    {
                        const std::array<double, 3> out = side == 0 ? right
                            : std::array<double, 3>{-right[0], -right[1], 0.0};
                        builder.addSurface(outdoorFacing({sideAt(a, side, base), sideAt(b, side, base),
                            sideAt(b, side, std::max(knee(b), base)), sideAt(a, side, std::max(knee(a), base))}, out),
                            wallTexture, m_event);

                        if (knee(a) < topAt(a) - 0.5 || knee(b) < topAt(b) - 0.5)
                        {
                            builder.addSurface(outdoorFacing({sideAt(a, side, std::max(knee(a), base)),
                                sideAt(b, side, std::max(knee(b), base)), sideAt(b, side, topAt(b)),
                                sideAt(a, side, topAt(a))}, out), wallTexture, m_event);
                        }
                    }

                    builder.addSurface(outdoorFacing({sideAt(a, 0, topAt(a)), sideAt(b, 0, topAt(b)),
                        sideAt(b, 1, topAt(b)), sideAt(a, 1, topAt(a))}, {0.0, 0.0, 1.0}), topTexture, m_event);

                    if (underside)
                    {
                        builder.addSurface(outdoorFacing({sideAt(a, 0, base), sideAt(b, 0, base), sideAt(b, 1, base),
                            sideAt(a, 1, base)}, {0.0, 0.0, -1.0}), wallTexture, m_event);
                    }

                    for (const bool end : {false, true})
                    {
                        if (!(end ? openEnd && chunk + 1 == chunks : openStart && chunk == 0))
                        {
                            continue;
                        }

                        const double place = end ? b : a;
                        std::vector<OutdoorModelPoint> points = {sideAt(place, 0, base)};

                        if (knee(place) > base + 0.5 && knee(place) < topAt(place) - 0.5)
                        {
                            points.push_back(sideAt(place, 0, knee(place)));
                        }

                        points.push_back(sideAt(place, 0, topAt(place)));
                        points.push_back(sideAt(place, 1, topAt(place)));

                        if (knee(place) > base + 0.5 && knee(place) < topAt(place) - 0.5)
                        {
                            points.push_back(sideAt(place, 1, knee(place)));
                        }

                        points.push_back(sideAt(place, 1, base));
                        builder.addSurface(outdoorFacing(points, end ? way
                            : std::array<double, 3>{-way[0], -way[1], 0.0}), wallTexture, m_event);
                    }
                }
            };
            // `open`: the piece's end is a free end of the wall or a gate's cheek, and gets a face.
            // A box along the stretch between `from` and `to`, `z0` to `z1` high, between `in0` and `in1` in from
            // the right side; the faces `draw` names: 0 right, 1 left, 2 top, 3 underside, 4 start, 5 end.
            const auto slab = [&](double from, double to, double z0, double z1, double in0, double in1,
                std::array<bool, 6> draw)
            {
                const std::array<Point2, 2> start = across(from);
                const std::array<Point2, 2> end = across(to);
                const auto point = [&](const std::array<Point2, 2> &pair, double in, double z)
                {
                    const double share = in / std::max(lengthOf(pair[0], pair[1]), 1.0e-9);
                    return OutdoorModelPoint{pair[0][0] + (pair[1][0] - pair[0][0]) * share,
                        pair[0][1] + (pair[1][1] - pair[0][1]) * share, z};
                };
                const std::array<double, 3> rightWay = {start[0][0] - start[1][0], start[0][1] - start[1][1], 0.0};
                const std::array<double, 3> way = {end[0][0] - start[0][0], end[0][1] - start[0][1], 0.0};
                const std::array<std::vector<OutdoorModelPoint>, 6> faces = {
                    std::vector<OutdoorModelPoint>{point(start, in0, z0), point(end, in0, z0), point(end, in0, z1),
                        point(start, in0, z1)},
                    std::vector<OutdoorModelPoint>{point(start, in1, z0), point(end, in1, z0), point(end, in1, z1),
                        point(start, in1, z1)},
                    std::vector<OutdoorModelPoint>{point(start, in0, z1), point(end, in0, z1), point(end, in1, z1),
                        point(start, in1, z1)},
                    std::vector<OutdoorModelPoint>{point(start, in0, z0), point(end, in0, z0), point(end, in1, z0),
                        point(start, in1, z0)},
                    std::vector<OutdoorModelPoint>{point(start, in0, z0), point(start, in1, z0), point(start, in1, z1),
                        point(start, in0, z1)},
                    std::vector<OutdoorModelPoint>{point(end, in0, z0), point(end, in1, z0), point(end, in1, z1),
                        point(end, in0, z1)}};
                const std::array<std::array<double, 3>, 6> normals = {rightWay,
                    std::array<double, 3>{-rightWay[0], -rightWay[1], 0.0}, std::array<double, 3>{0.0, 0.0, 1.0},
                    std::array<double, 3>{0.0, 0.0, -1.0}, std::array<double, 3>{-way[0], -way[1], 0.0}, way};

                for (size_t index = 0; index < faces.size(); ++index)
                {
                    if (draw[index])
                    {
                        builder.addSurface(outdoorFacing(faces[index], normals[index]),
                            index == 2 ? topTexture : wallTexture, m_event);
                    }
                }
            };
            const auto piece = [&](double from, double to, double low, bool openStart, bool openEnd, bool underside)
            {
                if (batter > 0.0 || follow)
                {
                    shaped(from, to, low, openStart, openEnd, underside);
                    return;
                }

                // The passage along the wall: the piece under its floor, its two sides and the piece over it.
                if (passage.given && low < passage.floor - 0.5)
                {
                    const double side = (thickness - passage.width) * 0.5;
                    const double ceiling = passage.floor + passage.height;
                    slab(from, to, low, passage.floor, 0.0, thickness, {true, true, true, underside, openStart,
                        openEnd});
                    slab(from, to, passage.floor, ceiling, 0.0, side, {true, true, false, false, openStart, openEnd});
                    slab(from, to, passage.floor, ceiling, thickness - side, thickness, {true, true, false, false,
                        openStart, openEnd});
                    slab(from, to, ceiling, top, 0.0, thickness, {true, true, true, true, openStart, openEnd});
                    return;
                }

                const std::array<Point2, 2> start = across(from);
                const std::array<Point2, 2> end = across(to);
                const auto face = [&](const Point2 &a, const Point2 &b, double z0, double z1,
                    const std::string &textureName)
                {
                    builder.addSurface({{a[0], a[1], z0}, {b[0], b[1], z0}, {b[0], b[1], z1}, {a[0], a[1], z1}},
                        textureName, m_event);
                };
                face(start[0], end[0], low, top, wallTexture);
                face(end[1], start[1], low, top, wallTexture);

                if (openStart)
                {
                    face(start[1], start[0], low, top, wallTexture);
                }

                if (openEnd)
                {
                    face(end[0], end[1], low, top, wallTexture);
                }

                builder.addSurface({{start[0][0], start[0][1], top}, {end[0][0], end[0][1], top},
                    {end[1][0], end[1][1], top}, {start[1][0], start[1][1], top}}, topTexture, m_event);

                if (underside)
                {
                    builder.addSurface({{start[1][0], start[1][1], low}, {end[1][0], end[1][1], low},
                        {end[0][0], end[0][1], low}, {start[0][0], start[0][1], low}}, wallTexture, m_event);
                }
            };
            double cursor = 0.0;

            for (size_t gate = 0; gate <= own.size(); ++gate)
            {
                const double until = gate < own.size() ? own[gate].from : length;

                if (until - cursor > 1.0)
                {
                    piece(cursor, until, foot, (index == 0 && !closed && gate == 0) || gate > 0,
                        (index + 1 == stretches && !closed && gate == own.size()) || gate < own.size(), false);
                }

                if (gate < own.size())
                {
                    // The lintel over the gate.
                    const double sill = landAt({(across(own[gate].from)[0][0] + across(own[gate].to)[1][0]) * 0.5,
                        (across(own[gate].from)[0][1] + across(own[gate].to)[1][1]) * 0.5});

                    const double apex = sill + own[gate].height;

                    if (top - apex > 1.0)
                    {
                        piece(own[gate].from, own[gate].to, apex, false, false, own[gate].arch.empty());
                    }

                    if (!own[gate].arch.empty())
                    {
                        // The arch: under the lintel, the spandrels on both sides and the soffit of each segment.
                        const double span = own[gate].to - own[gate].from;
                        const std::vector<std::array<double, 2>> head =
                            outdoorArchHead(span, own[gate].height, own[gate].arch, own[gate].sides);
                        const auto wallFace = [&](const std::vector<OutdoorModelPoint> &points)
                        {
                            builder.addSurface(points, wallTexture, m_event);
                        };

                        for (size_t segment = 0; segment + 1 < head.size(); ++segment)
                        {
                            const double a = own[gate].from + span * 0.5 + head[segment][0];
                            const double b = own[gate].from + span * 0.5 + head[segment + 1][0];
                            const double za = sill + head[segment][1];
                            const double zb = sill + head[segment + 1][1];
                            const std::array<Point2, 2> pa = across(a);
                            const std::array<Point2, 2> pb = across(b);
                            wallFace({{pa[0][0], pa[0][1], za}, {pb[0][0], pb[0][1], zb}, {pb[0][0], pb[0][1], apex},
                                {pa[0][0], pa[0][1], apex}});
                            wallFace({{pb[1][0], pb[1][1], zb}, {pa[1][0], pa[1][1], za}, {pa[1][0], pa[1][1], apex},
                                {pb[1][0], pb[1][1], apex}});
                            wallFace({{pa[1][0], pa[1][1], za}, {pb[1][0], pb[1][1], zb}, {pb[0][0], pb[0][1], zb},
                                {pa[0][0], pa[0][1], za}});
                        }
                    }

                    cursor = own[gate].to;
                }
            }

            if (parapet > 0.0)
            {
                // Along the outer side (the right of the line's way): a low wall, or merlons.
                const double inset = std::min(32.0, thickness * 0.5);
                const int merlons = battlements ? std::max(1, static_cast<int>(length / 128.0)) : 1;

                for (int merlon = 0; merlon < merlons; ++merlon)
                {
                    const double from = battlements ? length * merlon / merlons : 0.0;
                    const double to = battlements ? from + length / merlons * 0.5 : length;
                    // On a battered wall the parapet stands on the drawn-in top.
                    const auto topAcross = [&](double along)
                    {
                        if (batter <= 0.0)
                        {
                            return across(along);
                        }

                        const OutdoorModelPoint r = sideAt(along, 0, top);
                        const OutdoorModelPoint l = sideAt(along, 1, top);
                        return std::array<Point2, 2>{Point2{r[0], r[1]}, Point2{l[0], l[1]}};
                    };
                    const std::array<Point2, 2> start = topAcross(from);
                    const std::array<Point2, 2> end = topAcross(to);
                    const auto inner = [&](const std::array<Point2, 2> &pair)
                    {
                        const double width = lengthOf(pair[0], pair[1]);
                        return Point2{pair[0][0] + (pair[1][0] - pair[0][0]) * inset / width,
                            pair[0][1] + (pair[1][1] - pair[0][1]) * inset / width};
                    };
                    builder.addPrism(strip(start[0], end[0], inner(end), inner(start)), top, top + parapet,
                        wallTexture, topTexture, "", m_event);
                }
            }
        }
    }

    // A culvert's headwall: beside the mouth, over its head in strips, its top and its ends.
    template<typename Place>
    void raiseHeadwall(OutdoorModelBuilder &builder, const Place &place, const std::array<double, 3> &front,
        const std::vector<std::array<double, 2>> &mouth, double halfWall, double half, double top, double low,
        double thickness, double turn, const std::string &stone)
    {
        addFacing(builder, {place(-halfWall, 0.0, low), place(-half, 0.0, low), place(-half, 0.0, top),
            place(-halfWall, 0.0, top)}, front, stone);
        addFacing(builder, {place(half, 0.0, low), place(halfWall, 0.0, low), place(halfWall, 0.0, top),
            place(half, 0.0, top)}, front, stone);

        for (size_t index = 1; index + 2 < mouth.size(); ++index)
        {
            addFacing(builder, {place(mouth[index][0], 0.0, mouth[index][1]),
                place(mouth[index + 1][0], 0.0, mouth[index + 1][1]), place(mouth[index + 1][0], 0.0, top),
                place(mouth[index][0], 0.0, top)}, front, stone);
        }

        addFacing(builder, {place(-halfWall, 0.0, top), place(halfWall, 0.0, top), place(halfWall, thickness, top),
            place(-halfWall, thickness, top)}, {0.0, 0.0, 1.0}, stone);

        for (const double end : {-1.0, 1.0})
        {
            const Point2 outward = turned({0.0, 0.0}, end, 0.0, turn);
            addFacing(builder, {place(end * halfWall, 0.0, low), place(end * halfWall, thickness, low),
                place(end * halfWall, thickness, top), place(end * halfWall, 0.0, top)},
                {outward[0], outward[1], 0.0}, stone);
        }

    }

    // A culvert: a round pipe mouth in a stone headwall set into a bank, a short tunnel with water on its floor to a
    // dark face (the way in: Erathia's sewers, Sewer_S/_S_1: a CWB headwall 576 wide and 552 high round a mouth 288
    // wide with a round head, water 12 over the floor running out of it; Avlee's Outlet_W), and the outflow: a strip
    // of water from the mouth out over the land toward the river. It looks south when not turned; `at` is the middle
    // of the headwall's front at the floor.
    void raiseCulvert(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        Point2 middle = {0.0, 0.0};
        double floor = 0.0;

        if (!placeOf(node, middle, floor))
        {
            return;
        }

        const double turn = numberOr(node, "turn", 0.0);
        const double width = numberOr(node, "width", 288.0);
        const double height = numberOr(node, "height", 384.0);
        const int sides = static_cast<int>(numberOr(node, "sides", 6.0));
        const std::string arch = textOf(node, "arch", "round");
        Point2 headwall = {width + 288.0, height + 168.0};
        const YAML::Node wallNode = childOf(node, "wall");
        const double thickness = numberOr(node, "thickness", 64.0);
        const double depth = numberOr(node, "depth", 256.0);
        const double outflow = numberOr(node, "outflow", 512.0);
        const double waterLevel = numberOr(node, "water_level", 12.0);
        // `pipe`: no headwall; the pipe itself stands out of the bank, this thick round its mouth, its outer shell
        // running back to the dark face (Erathia's Sewer_S/_S_1: CWB 24 to 48 thick round a mouth 488 wide).
        const double pipe = numberOr(node, "pipe", 0.0);

        if ((wallNode.IsDefined() && !pointOf(wallNode, headwall)) || width < 64.0 || width > 1024.0
            || height < 64.0 || height > 1024.0 || sides < 2 || sides > 16 || (arch != "round" && arch != "segment")
            || headwall[0] < width + 32.0 || headwall[0] > 4096.0 || headwall[1] < height + 16.0
            || headwall[1] > 2048.0 || thickness < 16.0 || thickness > 512.0 || depth < 16.0 || depth > 2048.0
            || outflow < 0.0 || outflow > 4096.0 || waterLevel < 0.0 || waterLevel > height * 0.5 || pipe < 0.0
            || pipe > 256.0 || (pipe > 0.0 && wallNode.IsDefined()))
        {
            add(m_path, "a culvert's mouth is 64 to 1024 wide and high (`width` 288, `height` 384 to the top of its "
                "head), its head `arch` round or segment with 2 to 16 `sides` (6), in a headwall `wall: [width, "
                "height]` at least 32 wider and 16 higher than the mouth, 16 to 512 thick (`thickness` 64); the dark "
                "face lies `depth` 16 to 2048 behind the headwall (256), the water `water_level` 0 to half the "
                "mouth's height over the floor (12), and runs out `outflow` 0 to 4096 over the land (512); or, "
                "with `pipe` (0 to 256 thick) and no `wall`, the pipe's end standing out of the bank");
            return;
        }

        const std::string stone = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string water = textureOf(node, "water", m_pLook != nullptr ? m_pLook->pWater : nullptr);
        const std::string dark = textureOf(node, "door", m_lowered.styleWorld == "mm6" ? "solid10"
            : m_lowered.styleWorld == "mm7" ? "7solid01" : "solid01");
        const auto place = [&](double across, double back, double up)
        {
            const Point2 point = turned(middle, across, back, turn);
            return OutdoorModelPoint{point[0], point[1], floor + up};
        };
        const std::array<double, 3> front = [&]()
        {
            const Point2 a = turned(middle, 0.0, -1.0, turn);
            return std::array<double, 3>{a[0] - middle[0], a[1] - middle[1], 0.0};
        }();
        const double halfWall = headwall[0] * 0.5;
        const double half = width * 0.5;
        const double top = headwall[1];
        const double low = -64.0;
        // The mouth's outline: the left foot, the head, the right foot.
        std::vector<std::array<double, 2>> mouth = {{-half, 0.0}};

        for (const std::array<double, 2> &point : outdoorArchHead(width, height, arch, sides))
        {
            mouth.push_back(point);
        }

        mouth.push_back({half, 0.0});

        if (pipe > 0.0)
        {
            // The pipe's end: a ring round the mouth, and its outer shell back to the dark face.
            std::vector<std::array<double, 2>> shell = {{-half - pipe, 0.0}};

            for (const std::array<double, 2> &point : outdoorArchHead(width + pipe * 2.0, height + pipe, arch, sides))
            {
                shell.push_back(point);
            }

            shell.push_back({half + pipe, 0.0});

            for (size_t index = 0; index + 1 < mouth.size(); ++index)
            {
                addFacing(builder, {place(mouth[index][0], 0.0, mouth[index][1]),
                    place(mouth[index + 1][0], 0.0, mouth[index + 1][1]),
                    place(shell[index + 1][0], 0.0, shell[index + 1][1]), place(shell[index][0], 0.0, shell[index][1])},
                    front, stone);
                const Point2 out = turned({0.0, 0.0}, (shell[index][0] + shell[index + 1][0]) * 0.5, 0.0, turn);
                addFacing(builder, {place(shell[index][0], 0.0, shell[index][1]),
                    place(shell[index + 1][0], 0.0, shell[index + 1][1]),
                    place(shell[index + 1][0], thickness + depth, shell[index + 1][1]),
                    place(shell[index][0], thickness + depth, shell[index][1])},
                    {out[0], out[1], (shell[index][1] + shell[index + 1][1]) * 0.5 - height * 0.4}, stone);
            }
        }
        else
        {
            raiseHeadwall(builder, place, front, mouth, halfWall, half, top, low, thickness, turn, stone);
        }

        // The tunnel: walls and roof looking in, the water on its floor, the dark face at its end.
        const double back = thickness + depth;

        for (size_t index = 0; index + 1 < mouth.size(); ++index)
        {
            const double z0 = std::max(mouth[index][1], waterLevel);
            const double z1 = std::max(mouth[index + 1][1], waterLevel);
            const Point2 in = turned({0.0, 0.0}, -(mouth[index][0] + mouth[index + 1][0]) * 0.5, 0.0, turn);
            addFacing(builder, {place(mouth[index][0], 0.0, z0), place(mouth[index + 1][0], 0.0, z1),
                place(mouth[index + 1][0], back, z1), place(mouth[index][0], back, z0)},
                {in[0], in[1], height * 0.4 - (z0 + z1) * 0.5}, stone);
        }

        const size_t waterFrom = faceCount();
        addFacing(builder, {place(-half, 0.0, waterLevel), place(half, 0.0, waterLevel),
            place(half, back, waterLevel), place(-half, back, waterLevel)}, {0.0, 0.0, 1.0}, water);

        if (outflow > 0.0)
        {
            // Out over the land, a step of 128 at a time, never under it.
            const int steps = std::max(1, static_cast<int>(std::ceil(outflow / 128.0)));
            double nearZ = waterLevel;

            for (int step = 0; step < steps; ++step)
            {
                const double far = -outflow * (step + 1) / steps;
                const OutdoorModelPoint ground = place(0.0, far, 0.0);
                const double farZ = std::max(groundAt({ground[0], ground[1]}) + 8.0 - floor, std::min(nearZ, 8.0));
                const double near = -outflow * step / steps;
                addFacing(builder, {place(-half, near, nearZ), place(half, near, nearZ), place(half, far, farZ),
                    place(-half, far, farZ)}, {0.0, 0.0, 1.0}, water);
                nearZ = farZ;
            }
        }

        for (size_t face = waterFrom; face < faceCount(); ++face)
        {
            // As Sewer_S's: liquid, running out (0x2001138: fluid, flow up).
            m_pModel->faces[face].attributes |= Game::faceAttributeBit(Game::FaceAttribute::Fluid)
                | Game::faceAttributeBit(Game::FaceAttribute::FlowUp);

            if (face > waterFrom)
            {
                // The outflow lies over the land, which the party walks.
                builder.letThrough(static_cast<int>(face));
            }
        }

        std::vector<OutdoorModelPoint> door;

        for (const std::array<double, 2> &point : mouth)
        {
            door.push_back(place(point[0], back, std::max(point[1], waterLevel)));
        }

        const size_t doorFrom = faceCount();
        addFacing(builder, door, front, dark);
        markUsed(doorFrom);
        raiseCulvertGrating(node, builder, middle, floor, turn, mouth, waterLevel, depth + thickness);
    }

    // S8d: `grating` on a culvert: bars across its mouth before the dark face, carrying its event (Erathia's town
    // outfall MTSewer_N_1: 7t1butts bars 18 wide and 8 deep, two upright and three across, clipped to the round
    // mouth). `{bars: [upright, across], width, back}`: upright bars evenly across the mouth from the water to the
    // head (their feet 2 under the water), bars across evenly up it from side to side (2 behind the upright ones, so
    // no two faces lie in one plane), `width` thick (16), `back` behind the mouth's front (16); in the `grating`
    // texture role (the wall's).
    void raiseCulvertGrating(const YAML::Node &node, OutdoorModelBuilder &builder, const Point2 &middle, double floor,
        double turn, const std::vector<std::array<double, 2>> &mouth, double waterLevel, double back)
    {
        const YAML::Node grating = childOf(node, "grating");

        if (!grating.IsDefined())
        {
            return;
        }

        Point2 bars = {0.0, 0.0};
        const double width = numberOr(grating, "width", 16.0);
        const double behind = numberOr(grating, "back", 16.0);

        if (!grating.IsMap() || !pointOf(childOf(grating, "bars"), bars) || bars[0] < 0.0 || bars[1] < 0.0
            || bars[0] > 16.0 || bars[1] > 16.0 || bars[0] != std::floor(bars[0]) || bars[1] != std::floor(bars[1])
            || bars[0] + bars[1] < 1.0 || width < 4.0 || width > 64.0 || behind < 0.0 || behind > back - 16.0)
        {
            add(m_path + ".grating", "a culvert's grating is {bars: [upright, across] (0 to 16 each, at least one "
                "bar), width: 4 to 64 (16), back: how far behind the mouth's front, 0 to 16 short of the dark face "
                "(16)}");
            return;
        }

        const std::string metal = textureOf(node, "grating", textureOf(node, "wall", m_pLook != nullptr
            ? m_pLook->pStone : nullptr).c_str());
        // The mouth's head over a place across it, and the mouth's sides at a height.
        const auto headAt = [&](double across)
        {
            for (size_t index = 1; index + 2 < mouth.size(); ++index)
            {
                const std::array<double, 2> &a = mouth[index];
                const std::array<double, 2> &b = mouth[index + 1];

                if (across >= std::min(a[0], b[0]) - 1.0e-9 && across <= std::max(a[0], b[0]) + 1.0e-9)
                {
                    const double share = std::fabs(b[0] - a[0]) > 1.0e-9 ? (across - a[0]) / (b[0] - a[0]) : 0.0;
                    return a[1] + (b[1] - a[1]) * share;
                }
            }

            return mouth.size() > 2 ? mouth[1][1] : 0.0;
        };
        const double half = mouth.back()[0];
        const double foot = std::max(waterLevel, 0.0);
        const double crown = headAt(0.0);
        const size_t from = faceCount();
        const auto bar = [&](double left, double right, double near, double far, double low, double high)
        {
            const std::vector<Point2> plan = {turned(middle, left, near, turn), turned(middle, right, near, turn),
                turned(middle, right, far, turn), turned(middle, left, far, turn)};
            builder.addPrism(plan, floor + low, floor + high, metal, metal, metal, m_event);
        };

        for (int index = 0; index < static_cast<int>(bars[0]); ++index)
        {
            const double across = -half + 2.0 * half * (index + 1) / (bars[0] + 1.0);
            const double top = std::min(headAt(across - width * 0.5), headAt(across + width * 0.5));

            if (top > foot + 8.0)
            {
                // From 2 under the water, so the bar's foot does not lie in the water's plane (back to back with
                // it: X1's outfall, P3 2026-11-24); with no water it is hidden 2 into the tunnel's floor.
                bar(across - width * 0.5, across + width * 0.5, behind, behind + 8.0, waterLevel - 2.0, top);
            }
        }

        for (int index = 0; index < static_cast<int>(bars[1]); ++index)
        {
            const double up = foot + (crown - foot) * (index + 1) / (bars[1] + 1.0);
            // From side to side at the bar's top: where the head comes down to it, else the mouth's sides.
            double left = -half;
            double right = half;

            for (size_t step = 1; step + 2 < mouth.size(); ++step)
            {
                const std::array<double, 2> &a = mouth[step];
                const std::array<double, 2> &b = mouth[step + 1];
                const double high = up + width * 0.5;

                if ((a[1] - high) * (b[1] - high) <= 0.0 && std::fabs(b[1] - a[1]) > 1.0e-9)
                {
                    const double x = a[0] + (b[0] - a[0]) * (high - a[1]) / (b[1] - a[1]);
                    (x < 0.0 ? left : right) = x < 0.0 ? std::max(left, x) : std::min(right, x);
                }
            }

            if (right - left > 16.0)
            {
                bar(left, right, behind + 2.0, behind + 6.0, up - width * 0.5, up + width * 0.5);
            }
        }

        markUsed(from);
    }

    // A face wound to look along `toward` (counter-clockwise seen from that side).
    int addFacing(OutdoorModelBuilder &builder, std::vector<OutdoorModelPoint> points,
        const std::array<double, 3> &toward, const std::string &texture)
    {
        std::array<double, 3> normal = {0.0, 0.0, 0.0};

        for (size_t index = 0; index < points.size(); ++index)
        {
            const OutdoorModelPoint &a = points[index];
            const OutdoorModelPoint &b = points[(index + 1) % points.size()];
            normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
            normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
            normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
        }

        if (normal[0] * toward[0] + normal[1] * toward[1] + normal[2] * toward[2] < 0.0)
        {
            std::reverse(points.begin(), points.end());
        }

        return builder.addSurface(points, texture, m_event);
    }

    // `arches` on a bridge: the deck carried on arched openings with piers between them standing to the land or the
    // water's bed (Tularean Forest's sea viaduct LongTest_E*: arches about 1100 wide on piers 256 to 288 wide, the
    // soffit 352 from spring to crown, 64 under the deck; Erathia's viaduct Bridge_E_1, Evenmorn's causeway).
    struct BridgeArches
    {
        int count = 0;
        double rise = 0.0;
        double pierWidth = 256.0;
        std::string form = "round";
        int sides = 6;
        // S8d: `spans`, each opening's own width in order from the line's first point (Erathia's viaduct: 384, 576,
        // 384), the piers `pierWidth` between them and the end abutments taking what is left alike; empty: `count`
        // openings alike. `riseGiven`: one `rise` for all, else each opening's half span.
        std::vector<double> spans;
        bool riseGiven = false;
    };

    bool readBridgeArches(const YAML::Node &node, const std::vector<Point2> &line, BridgeArches &arches)
    {
        const YAML::Node words = childOf(node, "arches");

        if (!words.IsDefined())
        {
            return true;
        }

        const YAML::Node spanNodes = childOf(words, "spans");
        double least = 1.0e18;
        double spanned = 0.0;

        for (size_t index = 0; spanNodes.IsDefined() && spanNodes.IsSequence() && index < spanNodes.size(); ++index)
        {
            double width = 0.0;

            if (!numberOfNode(spanNodes[index], width))
            {
                arches.spans.clear();
                break;
            }

            arches.spans.push_back(width);
            least = std::min(least, width);
            spanned += width;
        }

        const double count = spanNodes.IsDefined() && !childOf(words, "count").IsDefined()
            ? static_cast<double>(arches.spans.size()) : numberOr(words, "count", 0.0);
        arches.form = textOf(words, "form", "round");
        arches.pierWidth = numberOr(words, "pier_width", 256.0);
        arches.sides = static_cast<int>(numberOr(words, "sides", arches.form == "segment" ? 4.0 : 6.0));
        const double length = line.size() == 2 ? lengthOf(line[0], line[1]) : 0.0;
        const double span = count >= 1.0 ? length / count - arches.pierWidth : 0.0;
        arches.riseGiven = childOf(words, "rise").IsDefined();
        arches.rise = numberOr(words, "rise", std::max(span * 0.5, 0.0));

        if (spanNodes.IsDefined() && (arches.spans.empty() || arches.spans.size() > 32
            || static_cast<double>(arches.spans.size()) != count || least < 64.0
            || spanned + count * arches.pierWidth > length + 0.5
            || (!arches.riseGiven && least * 0.5 < 16.0)))
        {
            add(m_path + ".arches.spans", "`spans` is each opening's width in order from the line's first point, 1 "
                "to 32 of them (as many as `count`, when given), each at least 64; with the piers between they fit "
                "the line (" + formatNumber(length) + " long), the end abutments taking what is left (Erathia's "
                "viaduct: [384, 576, 384] on piers 128)");
            return false;
        }

        if (!arches.spans.empty() && !arches.riseGiven)
        {
            arches.rise = least * 0.5;
        }

        if (!words.IsMap() || line.size() != 2 || count < 1.0 || count > 32.0 || count != std::floor(count)
            || (arches.form != "round" && arches.form != "segment") || arches.pierWidth < 0.0
            || arches.pierWidth > 1024.0 || arches.sides < 2 || arches.sides > 16
            || (arches.spans.empty() && span < 64.0)
            || arches.rise < 16.0 || arches.rise > 2048.0 || childOf(node, "piers").IsDefined())
        {
            add(m_path + ".arches", "a bridge on arches has a straight `line` of two points and `arches: {count, "
                "rise, form: round | segment, pier_width, sides}`: 1 to 32 arches each at least 64 wide between "
                "piers 0 to 1024 wide (256; half a pier at each end), a soffit rising 16 to 2048 from its springs "
                "(half the span: a half circle), 2 to 16 segments; no `piers` (the arches' piers are its own)");
            return false;
        }

        arches.count = static_cast<int>(count);
        return true;
    }

    struct BridgeFooting
    {
        double from, to, bottom;
    };

    std::vector<BridgeFooting> bridgeArchFootings(const BridgeArches &arches, const std::vector<Point2> &left,
        const std::vector<Point2> &right, double length) const
    {
        std::vector<BridgeFooting> footings;
        const double span = length / arches.count - arches.pierWidth;
        // Explicit spans leave the rest of the line to the two end abutments in equal shares.
        double from = 0.0, to = arches.pierWidth * 0.5;
        if (!arches.spans.empty())
        {
            to += (length - std::accumulate(arches.spans.begin(), arches.spans.end(), 0.0)
                - arches.count * arches.pierWidth) * 0.5;
        }
        const auto point = [length](const std::vector<Point2> &edge, double distance) -> Point2
        {
            const double share = distance / length;
            return {std::lerp(edge.front()[0], edge.back()[0], share), std::lerp(edge.front()[1], edge.back()[1], share)};
        };
        for (int i = 0; i <= arches.count; ++i)
        {
            footings.push_back({from, to, bridgeFootHeight({point(left, from), point(right, from),
                point(right, to), point(left, to)})});
            if (i < arches.count)
            {
                from = to + (arches.spans.empty() ? span : arches.spans[size_t(i)]);
                to = i + 1 == arches.count ? length : from + arches.pierWidth;
            }
        }
        return footings;
    }

    // The arches under a deck along a straight line: per arch a soffit of `sides` segments, the spandrels on both
    // sides up to the deck's underside, and the piers between them down to the land.
    void raiseBridgeArches(OutdoorModelBuilder &builder, const std::vector<Point2> &line,
        const std::vector<Point2> &left, const std::vector<Point2> &right, const BridgeArches &arches,
        const std::vector<BridgeFooting> &footings, double thickness, const std::function<double(double)> &deckZ,
        const std::string &texture)
    {
        const double length = lengthOf(line[0], line[1]);
        const Point2 along = {(line[1][0] - line[0][0]) / length, (line[1][1] - line[0][1]) / length};
        const auto side = [&](const std::vector<Point2> &edge, double s, double z)
        {
            return OutdoorModelPoint{edge[0][0] + along[0] * s, edge[0][1] + along[1] * s, z};
        };
        const auto crown = [&](double s)
        {
            return deckZ(s) - thickness;
        };
        const Point2 rightward = {right[0][0] - left[0][0], right[0][1] - left[0][1]};
        for (int arch = 0; arch < arches.count; ++arch)
        {
            const BridgeFooting &near = footings[size_t(arch)], &far = footings[size_t(arch + 1)];
            const double from = near.to, to = far.from;
            const double width = to - from;
            const double middle = (from + to) * 0.5;
            const double rise = !arches.spans.empty() && !arches.riseGiven ? width * 0.5 : arches.rise;
            const double spring = crown(middle) - rise;
            const std::vector<std::array<double, 2>> head =
                outdoorArchHead(width, rise, arches.form, arches.sides, rise);

            for (size_t segment = 0; segment + 1 < head.size(); ++segment)
            {
                const double a = middle + head[segment][0];
                const double b = middle + head[segment + 1][0];
                const double za = spring + head[segment][1];
                const double zb = spring + head[segment + 1][1];
                addFacing(builder, {side(right, a, za), side(left, a, za), side(left, b, zb), side(right, b, zb)},
                    {0.0, 0.0, -1.0}, texture);

                for (const bool onRight : {false, true})
                {
                    const std::vector<Point2> &edge = onRight ? right : left;
                    addFacing(builder, {side(edge, a, za), side(edge, b, zb), side(edge, b, crown(b)),
                        side(edge, a, crown(a))}, {onRight ? rightward[0] : -rightward[0],
                        onRight ? rightward[1] : -rightward[1], 0.0}, texture);
                }
            }

            // The piers' faces under the springs, looking into the opening.
            for (const bool atEnd : {false, true})
            {
                const double s = atEnd ? to : from;
                const double sign = atEnd ? -1.0 : 1.0;
                const double jamb = spring + head.front()[1];
                const double bottom = atEnd ? far.bottom : near.bottom;
                addFacing(builder, {side(left, s, bottom), side(right, s, bottom), side(right, s, jamb),
                    side(left, s, jamb)}, {along[0] * sign, along[1] * sign, 0.0}, texture);
            }
        }

        for (const BridgeFooting &footing : footings)
        {
            const double from = footing.from, to = footing.to;

            if (to - from < 1.0)
            {
                continue;
            }

            for (const bool onRight : {false, true})
            {
                const std::vector<Point2> &edge = onRight ? right : left;
                const std::array<double, 3> out = {onRight ? rightward[0] : -rightward[0],
                    onRight ? rightward[1] : -rightward[1], 0.0};
                // From the land to the deck's underside; the arch's spring at the side next to an opening.
                addFacing(builder, {side(edge, from, footing.bottom), side(edge, to, footing.bottom),
                    side(edge, to, crown(to)), side(edge, from, crown(from))}, out, texture);
            }
        }

    }

    // A bridge or a pier: a deck along a line, resting on the land at its ends (or level at `height`), on piers.
    void raiseBridge(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        std::vector<Point2> line;

        if (!lineOf(node, line))
        {
            return;
        }

        const double width = numberOr(node, "width", 384.0);
        const double thickness = numberOr(node, "thickness", 32.0);
        const double rise = numberOr(node, "rise", 0.0);
        const double kerb = numberOr(node, "kerb", 0.0);
        const double invisibleKerb = numberOr(node, "kerb_invisible", 0.0);
        const double lift = numberOr(node, "raise", 16.0);
        const std::string deckTexture = textureOf(node, "deck", m_pLook != nullptr ? m_pLook->pWood : nullptr);
        const std::string sideTexture = textureOf(node, "side", deckTexture.c_str());
        const std::string pierTexture = textureOf(node, "pier", sideTexture.c_str());
        // The end posts' (`towers`) own texture: outa1's bridge2ns has dark timber posts (BdkSV32c) on stone.
        const std::string towerTexture = textureOf(node, "tower", pierTexture.c_str());
        double level = 0.0;
        const bool flat = numberOfNode(childOf(node, "height"), level);

        if (width < 64.0 || width > 2048.0 || thickness < 8.0 || thickness > 512.0 || rise < -1024.0 || rise > 1024.0
            || kerb < 0.0 || kerb > 512.0 || invisibleKerb < 0.0 || invisibleKerb > 1024.0)
        {
            add(m_path, "a bridge is 64 to 2048 wide and 8 to 512 thick, rises -1024 to 1024 in its middle (below 0 "
                "it sags) and has kerbs of 0 to 512 and invisible kerbs (`kerb_invisible`) of 0 to 1024");
            return;
        }

        // S8d: `kerb_width`, each kerb's width across (32, or a quarter of the deck when that is less; Erathia's
        // viaduct Bridge_E: 64), as a walkway's.
        const double kerbWidth = numberOr(node, "kerb_width", std::min(32.0, width * 0.25));

        if (childOf(node, "kerb_width").IsDefined() && (kerb <= 0.0 || kerbWidth < 4.0 || kerbWidth * 4.0 > width))
        {
            add(m_path + ".kerb_width", "a bridge's `kerb_width` is each kerb's width, 4 to a quarter of the deck's "
                "`width` (32 when left out), on a bridge with a `kerb`");
            return;
        }

        BridgeArches arches;

        if (!readBridgeArches(node, line, arches))
        {
            return;
        }

        // `railing: rope`: a rope (a bar `rope` thick) along each edge of the deck, `railing_height` over it,
        // following its sag (Harmondale's footbridge NewOut2Bridge_: TRIM2_16a bars 96 wide and 48 high, 224 over
        // the deck, slung between its end posts). `towers: [along, across, height]`: a post on each edge at each
        // end, standing to `height` over the deck's end (the footbridge's: 96 x 96, 352 over).
        const std::string railing = textOf(node, "railing");
        const double railingHeight = numberOr(node, "railing_height", 224.0);
        const double rope = numberOr(node, "rope", 48.0);
        std::array<double, 3> towers = {0.0, 0.0, 0.0};
        const YAML::Node towerNode = childOf(node, "towers");
        bool towersRight = !towerNode.IsDefined();

        if (towerNode.IsDefined() && towerNode.IsSequence() && towerNode.size() == 3)
        {
            towersRight = numberOfNode(towerNode[0], towers[0]) && numberOfNode(towerNode[1], towers[1])
                && numberOfNode(towerNode[2], towers[2]) && towers[0] >= 16.0 && towers[1] >= 16.0
                && towers[2] >= 32.0 && towers[0] <= 1024.0 && towers[1] <= 1024.0 && towers[2] <= 2048.0;
        }

        if ((!railing.empty() && railing != "rope") || railingHeight < 32.0 || railingHeight > 512.0 || rope < 8.0
            || rope > 128.0 || !towersRight)
        {
            add(m_path, "a bridge's `railing` is rope (a bar `rope` 8 to 128 thick along each edge, `railing_height` "
                "32 to 512 over the deck: 224), its `towers` [along, across, height] (16 to 1024 each way, 32 to "
                "2048 over the deck's end)");
            return;
        }

        std::vector<Point2> left;
        std::vector<Point2> right;
        sidesOf(line, false, width * 0.5, left, right);
        // The deck's height along the whole line: from the land at one end to the land at the other, humped by
        // `rise`, or level at `height`.
        std::vector<double> lengths = {0.0};

        for (size_t index = 0; index + 1 < line.size(); ++index)
        {
            lengths.push_back(lengths.back() + lengthOf(line[index], line[index + 1]));
        }

        const double total = lengths.back();
        // An end on the land meets it across the deck's width (P3 2026-11-24, D4's Snow River bridge: the land
        // falling 30 across its end left a step of 33 and 43 at a kerb): the land is read across the end and 32
        // beyond it (in the middle, at a quarter and at two fifths of the width each side; not over open water: a
        // shore cell is walked on) and the end stands `raise` over the lowest of it, or halfway between the lowest
        // and the highest where the land falls more than twice `raise` across it, so no side meets a step of more
        // than half the fall. Only the land's middle when all of it is water.
        const auto landEnd = [&](const Point2 &head, const Point2 &before)
        {
            const double length = std::max(lengthOf(before, head), 1.0e-9);
            const Point2 out = {(head[0] - before[0]) / length, (head[1] - before[1]) / length};
            double lowest = 1.0e30;
            double highest = -1.0e30;

            for (const double beyond : {0.0, 32.0})
            {
                for (const double share : {0.0, -0.25, 0.25, -0.4, 0.4})
                {
                    const Point2 at = {head[0] + out[0] * beyond - out[1] * width * share,
                        head[1] + out[1] * beyond + out[0] * width * share};
                    const double column = at[0] / OutdoorCellSize + OutdoorNodeCount / 2.0;
                    const double row = OutdoorNodeCount / 2.0 - at[1] / OutdoorCellSize;

                    if (column < 0.0 || row < 0.0 || column >= OutdoorNodeCount || row >= OutdoorNodeCount)
                    {
                        continue;
                    }

                    const size_t cell = static_cast<size_t>(row) * OutdoorNodeCount + static_cast<size_t>(column);

                    if (cell < m_lowered.water.size() && m_lowered.water[cell] != 0)
                    {
                        continue;
                    }

                    const double ground = nativeGroundAt(at);
                    lowest = std::min(lowest, ground);
                    highest = std::max(highest, ground);
                }
            }

            return lowest > highest ? groundAt(head) + lift : std::max(lowest + lift, (lowest + highest) * 0.5);
        };
        const double startZ = flat ? level : landEnd(line.front(), line[1]);
        const double endZ = flat ? level : landEnd(line.back(), line[line.size() - 2]);
        const auto deckZ = [&](double along)
        {
            const double share = along / total;
            return startZ + (endZ - startZ) * share + rise * 4.0 * share * (1.0 - share);
        };
        const int piers = arches.count > 0 ? 0 : static_cast<int>(numberOr(node, "piers", std::floor(total / 1024.0)));

        for (size_t index = 0; index + 1 < line.size(); ++index)
        {
            const double length = lengths[index + 1] - lengths[index];
            // A humped deck in four pieces to a stretch; a straight one in one.
            const int pieces = rise != 0.0 ? std::max(1, static_cast<int>(std::ceil(4.0 * length / total))) : 1;

            for (int pieceIndex = 0; pieceIndex < pieces; ++pieceIndex)
            {
                const double from = static_cast<double>(pieceIndex) / pieces;
                const double to = static_cast<double>(pieceIndex + 1) / pieces;
                const auto at = [&](const std::vector<Point2> &side, double share, double z)
                {
                    return OutdoorModelPoint{side[index][0] + (side[index + 1][0] - side[index][0]) * share,
                        side[index][1] + (side[index + 1][1] - side[index][1]) * share, z};
                };
                const double z0 = deckZ(lengths[index] + length * from);
                const double z1 = deckZ(lengths[index] + length * to);
                builder.addSurface({at(right, from, z0), at(right, to, z1), at(left, to, z1), at(left, from, z0)},
                    deckTexture, m_event);
                if (arches.count == 0)
                {
                    builder.addSurface({at(left, from, z0 - thickness), at(left, to, z1 - thickness),
                        at(right, to, z1 - thickness), at(right, from, z0 - thickness)}, sideTexture, m_event);
                }

                builder.addSurface({at(right, from, z0 - thickness), at(right, to, z1 - thickness), at(right, to, z1),
                    at(right, from, z0)}, sideTexture, m_event);
                builder.addSurface({at(left, to, z1 - thickness), at(left, from, z0 - thickness), at(left, from, z0),
                    at(left, to, z1)}, sideTexture, m_event);

                if (invisibleKerb > 0.0)
                {
                    // An upright face on each edge of the deck facing out, not drawn, that stops the party walking
                    // off (Harmondale's footbridge NewOut2Bridge_: 352 high over its landings, beside its rails).
                    builder.hide(builder.addSurface({at(right, from, z0), at(right, to, z1),
                        at(right, to, z1 + invisibleKerb), at(right, from, z0 + invisibleKerb)}, sideTexture, 0));
                    builder.hide(builder.addSurface({at(left, to, z1), at(left, from, z0),
                        at(left, from, z0 + invisibleKerb), at(left, to, z1 + invisibleKerb)}, sideTexture, 0));
                }

                if (railing == "rope")
                {
                    // The rope: a bar centred on each edge of the deck, its top `railing_height` over the deck.
                    for (const bool onLeft : {false, true})
                    {
                        const std::vector<Point2> &edgeSide = onLeft ? left : right;
                        const std::vector<Point2> &otherSide = onLeft ? right : left;
                        const auto bar = [&](double share, double out, double z)
                        {
                            const OutdoorModelPoint edge = at(edgeSide, share, z);
                            const OutdoorModelPoint other = at(otherSide, share, z);
                            const double across = std::max(oy::hypot(other[0] - edge[0], other[1] - edge[1]), 1.0);
                            return OutdoorModelPoint{edge[0] - (other[0] - edge[0]) / across * out,
                                edge[1] - (other[1] - edge[1]) / across * out, z};
                        };
                        const double half = rope * 0.5;
                        const double t0 = z0 + railingHeight;
                        const double t1 = z1 + railingHeight;
                        const OutdoorModelPoint outerTop0 = bar(from, half, t0);
                        const OutdoorModelPoint outerTop1 = bar(to, half, t1);
                        const OutdoorModelPoint innerTop0 = bar(from, -half, t0);
                        const OutdoorModelPoint innerTop1 = bar(to, -half, t1);
                        const auto low = [rope](OutdoorModelPoint point)
                        {
                            point[2] -= rope;
                            return point;
                        };
                        const Point2 outward = {outerTop0[0] - innerTop0[0], outerTop0[1] - innerTop0[1]};
                        addFacing(builder, {outerTop0, outerTop1, innerTop1, innerTop0}, {0.0, 0.0, 1.0},
                            sideTexture);
                        addFacing(builder, {low(outerTop0), low(outerTop1), low(innerTop1), low(innerTop0)},
                            {0.0, 0.0, -1.0}, sideTexture);
                        addFacing(builder, {low(outerTop0), low(outerTop1), outerTop1, outerTop0},
                            {outward[0], outward[1], 0.0}, sideTexture);
                        addFacing(builder, {low(innerTop0), low(innerTop1), innerTop1, innerTop0},
                            {-outward[0], -outward[1], 0.0}, sideTexture);
                    }
                }

                if (kerb > 0.0)
                {
                    // A kerb on each side, `kerb_width` thick (32), standing on the deck's edge.
                    const double inset = kerbWidth / width;

                    for (const bool onLeft : {false, true})
                    {
                        const auto edge = [&](double share, double inward, double z)
                        {
                            const OutdoorModelPoint outer = at(onLeft ? left : right, share, z);
                            const OutdoorModelPoint other = at(onLeft ? right : left, share, z);
                            return OutdoorModelPoint{outer[0] + (other[0] - outer[0]) * inward,
                                outer[1] + (other[1] - outer[1]) * inward, z};
                        };
                        std::vector<OutdoorModelPoint> outerFace = {edge(from, 0.0, z0), edge(to, 0.0, z1),
                            edge(to, 0.0, z1 + kerb), edge(from, 0.0, z0 + kerb)};
                        std::vector<OutdoorModelPoint> innerFace = {edge(to, inset, z1), edge(from, inset, z0),
                            edge(from, inset, z0 + kerb), edge(to, inset, z1 + kerb)};
                        std::vector<OutdoorModelPoint> topFace = {edge(from, 0.0, z0 + kerb), edge(to, 0.0, z1 + kerb),
                            edge(to, inset, z1 + kerb), edge(from, inset, z0 + kerb)};

                        if (onLeft)
                        {
                            std::reverse(outerFace.begin(), outerFace.end());
                            std::reverse(innerFace.begin(), innerFace.end());
                            std::reverse(topFace.begin(), topFace.end());
                        }

                        builder.addSurface(outerFace, sideTexture, m_event);
                        builder.addSurface(innerFace, sideTexture, m_event);
                        builder.addSurface(topFace, sideTexture, m_event);
                    }
                }
            }
        }

        // The ends, and the piers: square posts under the deck down into the ground or the water's bed. On arches
        // the ends are the abutments, down to the land.
        const std::vector<BridgeFooting> footings = arches.count > 0 ? bridgeArchFootings(arches, left, right, total)
            : std::vector<BridgeFooting>{};
        const double startLow = footings.empty() ? startZ - thickness : std::min(footings.front().bottom, startZ - thickness);
        const double endLow = footings.empty() ? endZ - thickness : std::min(footings.back().bottom, endZ - thickness);
        builder.addSurface({{left.front()[0], left.front()[1], startLow},
            {right.front()[0], right.front()[1], startLow}, {right.front()[0], right.front()[1], startZ},
            {left.front()[0], left.front()[1], startZ}}, sideTexture, m_event);
        builder.addSurface({{right.back()[0], right.back()[1], endLow},
            {left.back()[0], left.back()[1], endLow}, {left.back()[0], left.back()[1], endZ},
            {right.back()[0], right.back()[1], endZ}}, sideTexture, m_event);

        if (arches.count > 0)
        {
            raiseBridgeArches(builder, line, left, right, arches, footings, thickness, deckZ, pierTexture);
        }

        if (towers[0] > 0.0)
        {
            for (const bool atEnd : {false, true})
            {
                const Point2 &middle = atEnd ? line.back() : line.front();
                const Point2 &before = atEnd ? line[line.size() - 2] : line[1];
                const double z = atEnd ? endZ : startZ;
                const double angle = oy::atan2(middle[0] - before[0], middle[1] - before[1]) * 180.0 / Pi;

                for (const std::vector<Point2> *pSide : {&left, &right})
                {
                    const Point2 &edge = atEnd ? pSide->back() : pSide->front();
                    // Its middle on the deck's edge, just beyond the deck's end.
                    const Point2 out = {(middle[0] - before[0]) / lengthOf(middle, before) * towers[0] * 0.5,
                        (middle[1] - before[1]) / lengthOf(middle, before) * towers[0] * 0.5};
                    const Point2 place = {edge[0] + out[0], edge[1] + out[1]};
                    builder.addPrism(turnedBox(place, towers[1], towers[0], angle), groundAt(place) - 32.0,
                        z + towers[2], towerTexture, towerTexture, "", m_event);
                }
            }
        }

        for (int pier = 1; pier <= piers; ++pier)
        {
            const double along = total * pier / (piers + 1);
            size_t index = 0;

            while (index + 2 < lengths.size() && lengths[index + 1] < along)
            {
                ++index;
            }

            const double share = (along - lengths[index]) / (lengths[index + 1] - lengths[index]);

            for (const std::vector<Point2> *pSide : {&left, &right})
            {
                const Point2 edge = {(*pSide)[index][0] + ((*pSide)[index + 1][0] - (*pSide)[index][0]) * share,
                    (*pSide)[index][1] + ((*pSide)[index + 1][1] - (*pSide)[index][1]) * share};
                const Point2 middle = {line[index][0] + (line[index + 1][0] - line[index][0]) * share,
                    line[index][1] + (line[index + 1][1] - line[index][1]) * share};
                // A post 48 square, its middle 32 in from the deck's edge.
                const double inward = 32.0 / std::max(lengthOf(edge, middle), 1.0);
                const Point2 post = {edge[0] + (middle[0] - edge[0]) * inward,
                    edge[1] + (middle[1] - edge[1]) * inward};
                const std::vector<Point2> footprint = turnedBox(post, 48.0, 48.0, 0.0);
                builder.addPrism(footprint, bridgeFootHeight(footprint), deckZ(along) - thickness, pierTexture, "", "", m_event);
            }
        }
    }

    // A fountain's `outline` ([east, north] points in map units about `at`, before `turn`) or `size: [width,
    // depth]` (a rectangle), in world units, counter-clockwise. Empty (and true) when it has neither: a ring.
    bool readBasinOutline(const YAML::Node &node, const Point2 &middle, double turn, std::vector<Point2> &outline)
    {
        const YAML::Node points = childOf(node, "outline");
        const YAML::Node size = childOf(node, "size");

        if (points.IsDefined() && size.IsDefined())
        {
            add(m_path, "a fountain's basin is an `outline` or a rectangle (`size`), not both");
            return false;
        }

        if (size.IsDefined())
        {
            Point2 extent = {0.0, 0.0};

            if (!pointOf(size, extent) || extent[0] < 96.0 || extent[1] < 96.0 || extent[0] > 4096.0
                || extent[1] > 4096.0)
            {
                add(m_path + ".size", "a rectangular basin's `size` is [width, depth] in map units, 96 to 4096 each "
                    "(outd1's ponds: [640, 128])");
                return false;
            }

            outline = turnedBox(middle, extent[0], extent[1], turn);
            return true;
        }

        for (size_t index = 0; points.IsDefined() && points.IsSequence() && index < points.size(); ++index)
        {
            Point2 point = {0.0, 0.0};

            if (!pointOf(points[index], point) || std::fabs(point[0]) > 4096.0 || std::fabs(point[1]) > 4096.0)
            {
                outline.clear();
                break;
            }

            outline.push_back(turned(middle, point[0], point[1], turn));
        }

        if (points.IsDefined() && (outline.size() < 3 || outline.size() > 64 || !polygonIsSimple(outline)
            || std::fabs(polygonDoubleArea(outline)) < 2.0 * 96.0 * 96.0))
        {
            add(m_path + ".outline", "a basin's `outline` is 3 to 64 points [east, north] in map units about `at` "
                "(before `turn`), within 4096 of it, its sides crossing nowhere and enclosing water (MM6's "
                "pointed Heroes' fountain: [[288, 0], [224, 64], [96, 160], [-64, 192], [-224, 224], [-192, 128], "
                "...])");
            outline.clear();
            return false;
        }

        if (polygonDoubleArea(outline) < 0.0)
        {
            std::reverse(outline.begin(), outline.end());
        }

        return true;
    }

    // A well or a fountain: a ring wall with water in it; a fountain has a pillar in its middle, a well may have
    // a roof on four posts.
    void raiseBasin(const YAML::Node &node, OutdoorModelBuilder &builder, bool fountain)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        double radius = numberOr(node, "radius", fountain ? 256.0 : 112.0);
        const double wall = numberOr(node, "height", fountain ? 64.0 : 96.0);
        const int sides = static_cast<int>(numberOr(node, "sides", 8.0));
        const double turn = numberOr(node, "turn", 0.0);
        const std::string stone = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string water = textureOf(node, "water", m_pLook != nullptr ? m_pLook->pWater : nullptr);
        const std::string wood = textureOf(node, "roof", m_pLook != nullptr ? m_pLook->pWood : nullptr);

        if (radius < 48.0 || radius > 1024.0 || wall < 16.0 || wall > 512.0 || sides < 3 || sides > 16)
        {
            add(m_path, std::string(fountain ? "a fountain" : "a well") + " has a `radius` of 48 to 1024, a wall "
                "16 to 512 high (`height`) and 3 to 16 `sides`");
            return;
        }

        // A fountain's basin drawn as a polygon (`outline`, map units about `at` before `turn`: MM6's pointed
        // Heroes' fountains, oute2's ponds) or a rectangle (`size`: outd1's ponds, troughs) instead of a ring.
        std::vector<Point2> outline;

        if (fountain && !readBasinOutline(node, middle, turn, outline))
        {
            return;
        }

        const bool ring = outline.empty();
        const double rim = numberOr(node, "rim", ring ? std::min(24.0, radius * 0.25) : 32.0);
        const double below = numberOr(node, "water_below", wall * 0.25);
        // `tiers`: steps under the basin, from the basin outward, each [out, up]: `out` beyond the one above
        // (oute2's town fountain: a square step 96 out and 64 high), the basin on the topmost.
        std::vector<Point2> tiers;
        const YAML::Node tierNodes = fountain ? childOf(node, "tiers") : YAML::Node();
        const std::string tierShape = textOf(node, "tier_shape", "outline");

        for (size_t index = 0; tierNodes.IsDefined() && tierNodes.IsSequence() && index < tierNodes.size(); ++index)
        {
            Point2 tier = {0.0, 0.0};

            if (!pointOf(tierNodes[index], tier) || tier[0] < 0.0 || tier[0] > 1024.0 || tier[1] < 8.0
                || tier[1] > 512.0)
            {
                add(m_path + ".tiers", "a fountain's tiers are steps under its basin, from the basin outward, each "
                    "[out, up]: 0 to 1024 beyond the one above and 8 to 512 high");
                return;
            }

            tiers.push_back(tier);
        }

        if ((ring ? rim < 4.0 || rim >= radius - 16.0 : rim < 4.0 || rim > 256.0) || below < 0.0 || below >= wall
            || (tierShape != "outline" && tierShape != "box"))
        {
            add(m_path, "the rim is 4 thick or more (`rim`) and leaves water at least 32 across, the water lies 0 "
                "to less than the wall's height under the rim's top (`water_below`), and `tier_shape` is outline "
                "or box");
            return;
        }

        if (!ring)
        {
            // The pillar of an outlined basin is as thick as a ring's of the basin's mean size.
            double far = 0.0;

            for (const Point2 &point : outline)
            {
                far = std::max(far, lengthOf(point, middle));
            }

            radius = far;
        }

        std::vector<Point2> outer = ring ? ringOf(middle, radius, sides, turn) : outline;
        std::vector<Point2> inner;

        if (ring)
        {
            inner = ringOf(middle, radius - rim, sides, turn);
        }
        else
        {
            std::vector<Point2> unused;
            sidesOf(outline, true, rim, inner, unused);

            if (polygonDoubleArea(inner) < 2048.0 || !polygonIsSimple(inner))
            {
                add(m_path + ".outline", "the rim (" + formatNumber(rim) + " thick) leaves no water inside this "
                    "outline: make the outline wider or the rim thinner");
                return;
            }
        }

        double base = ground;

        if (!tiers.empty())
        {
            // From the outermost step in: each stands on the one below it.
            std::vector<std::vector<Point2>> steps;
            double reach = 0.0;

            for (const Point2 &tier : tiers)
            {
                reach += tier[0];
                std::vector<Point2> grown;
                std::vector<Point2> unused;
                sidesOf(outer, true, reach, unused, grown);

                if (tierShape == "box")
                {
                    // The step's turned bounding box about the middle.
                    double east = 0.0;
                    double north = 0.0;

                    for (const Point2 &point : grown)
                    {
                        const double angle = turn * Pi / 180.0;
                        const double dx = point[0] - middle[0];
                        const double dy = point[1] - middle[1];
                        east = std::max(east, std::fabs(dx * oy::cos(angle) - dy * oy::sin(angle)));
                        north = std::max(north, std::fabs(dx * oy::sin(angle) + dy * oy::cos(angle)));
                    }

                    grown = turnedBox(middle, east * 2.0, north * 2.0, turn);
                }

                steps.push_back(grown);
            }

            double low = ground - 64.0;
            double level = ground;

            for (size_t step = steps.size(); step-- > 0;)
            {
                level += tiers[step][1];
                const std::vector<Point2> &ringPoints = steps[step];
                const std::vector<Point2> &within = step == 0 ? outer : steps[step - 1];

                for (size_t side = 0; side < ringPoints.size(); ++side)
                {
                    const Point2 &a = ringPoints[side];
                    const Point2 &b = ringPoints[(side + 1) % ringPoints.size()];
                    builder.addSurface({{a[0], a[1], low}, {b[0], b[1], low}, {b[0], b[1], level},
                        {a[0], a[1], level}}, stone, m_event);
                }

                // Its top: the step's outline round the next one in, in convex pieces.
                const std::vector<Point2> holed = cutHole(ringPoints, within);

                for (const std::vector<size_t> &piece : convexPieces(holed, 8))
                {
                    std::vector<OutdoorModelPoint> points;

                    for (const size_t index : piece)
                    {
                        points.push_back({holed[index][0], holed[index][1], level});
                    }

                    builder.addSurface(points, stone, m_event);
                }

                low = level - 16.0;
            }

            base = level;
        }

        const double top = base + wall;
        const double foot = tiers.empty() ? ground - 64.0 : base - 16.0;
        const double surfaceZ = top - below;
        const size_t count = outer.size();

        for (size_t side = 0; side < count; ++side)
        {
            const size_t next = (side + 1) % count;
            builder.addSurface({{outer[side][0], outer[side][1], foot}, {outer[next][0], outer[next][1], foot},
                {outer[next][0], outer[next][1], top}, {outer[side][0], outer[side][1], top}}, stone, m_event);
            builder.addSurface({{outer[side][0], outer[side][1], top}, {outer[next][0], outer[next][1], top},
                {inner[next][0], inner[next][1], top}, {inner[side][0], inner[side][1], top}}, stone, m_event);
            builder.addSurface({{inner[next][0], inner[next][1], surfaceZ},
                {inner[side][0], inner[side][1], surfaceZ}, {inner[side][0], inner[side][1], top},
                {inner[next][0], inner[next][1], top}}, stone, m_event);
        }

        const size_t waterFrom = faceCount();

        if (ring)
        {
            std::vector<OutdoorModelPoint> surface;

            for (const Point2 &point : inner)
            {
                surface.push_back({point[0], point[1], surfaceZ});
            }

            builder.addSurface(surface, water, m_event);
        }
        else
        {
            // One water face per convex piece, as HF's six.
            for (const std::vector<size_t> &piece : convexPieces(inner, 8))
            {
                std::vector<OutdoorModelPoint> surface;

                for (const size_t index : piece)
                {
                    surface.push_back({inner[index][0], inner[index][1], surfaceZ});
                }

                builder.addSurface(surface, water, m_event);
            }
        }

        {
            // The shipped wells' and fountains' water is liquid (the fluid bit on every one of them: MM6's HF and
            // wells 0x2000110, MM7's and MM8's 0x2001118): it ripples.
            for (size_t face = waterFrom; face < faceCount(); ++face)
            {
                m_pModel->faces[face].attributes |= Game::faceAttributeBit(Game::FaceAttribute::Fluid);
            }
        }

        markUsed(waterFrom);

        if (fountain)
        {
            const double pillar = numberOr(node, "pillar", 192.0);
            const std::string shape = textOf(node, "pillar_shape", "round");
            const std::string flow = textOf(node, "flow");
            const double pillarWidth = numberOr(node, "pillar_width", radius * 0.36);

            if ((shape != "round" && shape != "box") || (!flow.empty() && flow != "down") || pillarWidth < 16.0
                || pillarWidth > radius * 1.5 || (pillar > 0.0 && ground + pillar <= surfaceZ))
            {
                add(m_path, "a fountain's pillar is round (the default) or a box (`pillar_shape`), 16 or more wide "
                    "(`pillar_width`) and higher than its water (`pillar` over the ground); `flow: down` runs "
                    "water down its faces");
                return;
            }

            if (pillar > 0.0)
            {
                const size_t pillarFrom = faceCount();
                const bool running = flow == "down";
                const std::vector<Point2> section = shape == "box"
                    ? turnedBox(middle, pillarWidth, pillarWidth, turn)
                    : ringOf(middle, radius * 0.18, sides, turn);
                builder.addPrism(section, surfaceZ, ground + pillar, running ? water : stone,
                    running ? water : stone, "", m_event);

                if (running)
                {
                    // Water running down the block's faces and over its top (MM8's Fountain: WtrTyl with the face
                    // bit FlowDown on the middle block); drunk as the basin's water.
                    for (size_t face = pillarFrom; face < faceCount(); ++face)
                    {
                        m_pModel->faces[face].attributes |= Game::faceAttributeBit(Game::FaceAttribute::FlowDown);
                    }

                    markUsed(pillarFrom);
                }
            }
        }
        else if (childOf(node, "frame").IsDefined())
        {
            raiseWellFrame(node, builder, middle, ground, radius, rim, top, sides, turn, wood);
        }
        else if (childOf(node, "post").IsDefined())
        {
            // A single post up from the middle of the water (Ravenshore's wells: a stone ring 256 across and 80
            // high, a post 64 wide up to 216).
            const double post = numberOr(node, "post", 0.0);

            if (post <= wall || post > 1024.0 || flagOf(node, "roofed"))
            {
                add(m_path + ".post", "a well's `post` is the height of a single pole standing up from its water, "
                    "higher than its wall and up to 1024; a well has a post or a roof (`roofed`), not both");
                return;
            }

            // Half the ring's radius wide (Ravenshore's: 64 in a ring of 128, from the water to 216).
            builder.addPrism(turnedBox(middle, radius * 0.5, radius * 0.5, turn), top - wall * 0.25, ground + post,
                wood, wood, "", m_event);
        }
        else if (flagOf(node, "roofed"))
        {
            // Four posts and a small pyramid over them.
            const double eaves = top + 160.0;

            for (const Point2 &corner : turnedBox(middle, radius * 1.6, radius * 1.6, turn))
            {
                builder.addPrism(turnedBox(corner, 16.0, 16.0, turn), ground, eaves, wood, "", "", m_event);
            }

            const std::vector<Point2> roof = turnedBox(middle, radius * 2.0, radius * 2.0, turn);

            for (size_t side = 0; side < 4; ++side)
            {
                builder.addSurface({{roof[side][0], roof[side][1], eaves},
                    {roof[(side + 1) % 4][0], roof[(side + 1) % 4][1], eaves}, {middle[0], middle[1], eaves + radius}},
                    wood, m_event);
            }

            builder.addSurface({{roof[3][0], roof[3][1], eaves}, {roof[2][0], roof[2][1], eaves},
                {roof[1][0], roof[1][1], eaves}, {roof[0][0], roof[0][1], eaves}}, wood, m_event);
        }
    }

    // A well's windlass frame, as every one of the 72 wells of the 42 shipped outdoor maps has it (MM8 16, MM7 38,
    // MM6 18): two uprights on the ring's rim at its north and south ends (before `turn`) up to `height` over the
    // ground, drawing in from `posts[0]` wide at the ring's top to `posts[1]` (Ravenshore's: 64 to 24, as deep as
    // the rim), a beam `beam` high across them, and over it, when asked, a cone over the ring (Harmondale's, 96 high) or a gable
    // whose ridge runs along the beam (New Sorpigal's, 32 high over a square as wide as the ring).
    void raiseWellFrame(const YAML::Node &node, OutdoorModelBuilder &builder, const Point2 &middle, double ground,
        double radius, double rim, double ringTop, int sides, double turn, const std::string &wood)
    {
        const YAML::Node frame = childOf(node, "frame");
        const std::string where = m_path + ".frame";
        Point2 posts = {64.0, 24.0};
        const double height = numberOr(frame, "height", 184.0);
        const double beam = numberOr(frame, "beam", 32.0);
        const std::string roof = textOf(frame, "roof", "none");
        const double roofHeight = numberOr(frame, "roof_height", roof == "cone" ? 96.0 : 32.0);

        if (!frame.IsMap() || childOf(node, "post").IsDefined() || flagOf(node, "roofed")
            || (childOf(frame, "posts").IsDefined() && !pointOf(childOf(frame, "posts"), posts)))
        {
            add(where, "a well's frame is {height, posts: [width at the ring's top, width at the frame's top], beam, "
                "roof: none|cone|gable, roof_height}; a well has a `frame`, a `post` or `roofed`, one of them");
            return;
        }

        if (posts[0] < 8.0 || posts[1] < 8.0 || posts[0] > radius || posts[1] > posts[0] || height < ringTop - ground
            + 32.0 || height > 1024.0 || beam < 0.0 || beam > 128.0 || (roof != "none" && roof != "cone"
            && roof != "gable") || roofHeight <= 0.0 || roofHeight > 1024.0)
        {
            add(where, "the frame's uprights are 8 wide or more, at most the ring's radius at the foot and no wider "
                "at the top than at the foot (posts [64, 24] when left out), stand at least 32 over the ring "
                "(`height` over the ground, up to 1024; 184 when left out) under a beam 0 to 128 high (32), and the "
                "roof is none (the default), cone or gable, 0 to 1024 high (`roof_height`; cone 96, gable 32)");
            return;
        }

        const std::string post = textureOf(node, "post", wood.c_str());
        const std::string beamTexture = textureOf(node, "beam", post.c_str());
        const std::string under = textureOf(node, "trim", wood.c_str());
        const double frameTop = ground + height;

        // The uprights: as deep as the rim, on it, drawing in along the rim.
        for (const double end : {1.0, -1.0})
        {
            const double along = end * (radius - rim * 0.5);
            const std::vector<Point2> low = turnedBox(middle, posts[0], rim, turn, 0.0, along);
            const std::vector<Point2> high = turnedBox(middle, posts[1], rim, turn, 0.0, along);

            for (size_t side = 0; side < 4; ++side)
            {
                const size_t next = (side + 1) % 4;
                builder.addSurface({{low[side][0], low[side][1], ringTop}, {low[next][0], low[next][1], ringTop},
                    {high[next][0], high[next][1], frameTop}, {high[side][0], high[side][1], frameTop}}, post,
                    m_event);
            }

            if (beam == 0.0 && roof == "none")
            {
                builder.addSurface({{high[0][0], high[0][1], frameTop}, {high[1][0], high[1][1], frameTop},
                    {high[2][0], high[2][1], frameTop}, {high[3][0], high[3][1], frameTop}}, post, m_event);
            }
        }

        if (beam > 0.0)
        {
            builder.addPrism(turnedBox(middle, posts[1], radius * 2.0, turn), frameTop, frameTop + beam, beamTexture,
                roof == "none" ? beamTexture : "", beamTexture, m_event);
        }

        const double eaves = frameTop + beam;

        if (roof == "cone")
        {
            const std::vector<Point2> ring = ringOf(middle, radius, sides, turn);
            std::vector<OutdoorModelPoint> underside;

            for (int side = 0; side < sides; ++side)
            {
                const int next = (side + 1) % sides;
                builder.addSurface({{ring[side][0], ring[side][1], eaves}, {ring[next][0], ring[next][1], eaves},
                    {middle[0], middle[1], eaves + roofHeight}}, wood, m_event);
                underside.push_back({ring[sides - 1 - side][0], ring[sides - 1 - side][1], eaves});
            }

            builder.addSurface(underside, under, m_event);
        }
        else if (roof == "gable")
        {
            // The ridge runs along the beam (north-south before `turn`), the slopes fall east and west.
            const std::vector<Point2> square = turnedBox(middle, radius * 2.0, radius * 2.0, turn);
            const Point2 south = turned(middle, 0.0, -radius, turn);
            const Point2 north = turned(middle, 0.0, radius, turn);
            const double ridge = eaves + roofHeight;
            builder.addSurface({{square[1][0], square[1][1], eaves}, {square[2][0], square[2][1], eaves},
                {north[0], north[1], ridge}, {south[0], south[1], ridge}}, wood, m_event);
            builder.addSurface({{square[3][0], square[3][1], eaves}, {square[0][0], square[0][1], eaves},
                {south[0], south[1], ridge}, {north[0], north[1], ridge}}, wood, m_event);
            builder.addSurface({{square[0][0], square[0][1], eaves}, {square[1][0], square[1][1], eaves},
                {south[0], south[1], ridge}}, wood, m_event);
            builder.addSurface({{square[2][0], square[2][1], eaves}, {square[3][0], square[3][1], eaves},
                {north[0], north[1], ridge}}, wood, m_event);
            builder.addSurface({{square[3][0], square[3][1], eaves}, {square[2][0], square[2][1], eaves},
                {square[1][0], square[1][1], eaves}, {square[0][0], square[0][1], eaves}}, under, m_event);
        }
    }

    void raiseObelisk(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        const double width = numberOr(node, "width", 128.0);
        const double height = numberOr(node, "height", 1024.0);
        const double turn = numberOr(node, "turn", 0.0);
        const std::string stone = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);

        if (width < 32.0 || width > 1024.0 || height < width || height > 4096.0)
        {
            add(m_path, "an obelisk is 32 to 1024 wide and at least as high as wide, up to 4096");
            return;
        }

        // The shipped obelisks (40 on 34 of the 42 outdoor maps): Harmondale's is a white shaft of eight sides 128
        // wide drawing in to 80 under a tip 128 high, on a plinth 416 square. `sides` 4 or 8, `taper` the shaft's
        // width at its top against its foot, `tip` the tip's height, `plinth: [width, height]` a block under it.
        const double sidesNumber = numberOr(node, "sides", 4.0);
        const double taper = numberOr(node, "taper", 0.75);
        const double tip = numberOr(node, "tip", width * taper);
        Point2 plinth = {0.0, 0.0};
        const bool plinthed = childOf(node, "plinth").IsDefined();

        if ((sidesNumber != 4.0 && sidesNumber != 8.0) || taper < 0.1 || taper > 1.0 || tip <= 0.0
            || tip >= height || (plinthed && (!pointOf(childOf(node, "plinth"), plinth) || plinth[0] < width
            || plinth[0] > 4096.0 || plinth[1] < 8.0 || plinth[1] > height - tip)))
        {
            add(m_path, "an obelisk's shaft has 4 or 8 `sides`, draws in to `taper` (0.1 to 1; 0.75) of its width at "
                "its top under a `tip` lower than the whole (the top's width when left out), and stands on a "
                "`plinth: [width, height]` at least as wide as the shaft and lower than the shaft's top, when asked");
            return;
        }

        const int sides = static_cast<int>(sidesNumber);
        const double base = plinthed ? ground + plinth[1] : ground - 64.0;
        const std::string plinthTexture = textureOf(node, "plinth", stone.c_str());

        if (plinthed)
        {
            builder.addPrism(turnedBox(middle, plinth[0], plinth[0], turn), ground - 64.0, ground + plinth[1],
                plinthTexture, plinthTexture, "", m_event);
        }

        // An eight-sided shaft has its flats `width` apart, as a square one does.
        const auto outline = [&](double across)
        {
            return sides == 4 ? turnedBox(middle, across, across, turn)
                : ringOf(middle, across * 0.5 / oy::cos(Pi / 8.0), 8, turn);
        };
        const std::vector<Point2> foot = outline(width);
        const std::vector<Point2> neck = outline(width * taper);
        const double shoulder = ground + height - tip;

        for (int side = 0; side < sides; ++side)
        {
            const int next = (side + 1) % sides;
            builder.addSurface({{foot[side][0], foot[side][1], base}, {foot[next][0], foot[next][1], base},
                {neck[next][0], neck[next][1], shoulder}, {neck[side][0], neck[side][1], shoulder}}, stone, m_event);
            builder.addSurface({{neck[side][0], neck[side][1], shoulder}, {neck[next][0], neck[next][1], shoulder},
                {middle[0], middle[1], ground + height}}, stone, m_event);
        }
    }

    // A chest as the shipped maps' chest models are (F6-R1, 2026-11-22): the faces of a chest kind (core/ChestKinds,
    // as indoors), `chest_kind` or the style world's (mm8 gt002, mm7 and Xeen 7gt002: MM7's 7out01 `chest_N`, 19
    // faces; mm6 ch1), its front (the sloping lid's own picture) to the north before `turn`. A chest given its own
    // `textures` (wall, top) is the plain box of before, with a warning. A crate is a box `size` on a side. Both stand
    // at the lowest of the game's ground under their corners (F6-R2), so no corner floats; `raise` lifts them.
    void raiseChest(const YAML::Node &node, OutdoorModelBuilder &builder, bool crate)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        const double turn = numberOr(node, "turn", 0.0);
        const double raise = numberOr(node, "raise", 0.0);
        const std::string side = textureOf(node, "wall", m_pLook == nullptr ? nullptr
            : (crate ? m_pLook->pCrate : m_pLook->pChestSide));
        const std::string lid = textureOf(node, "top", m_pLook == nullptr ? nullptr
            : (crate ? m_pLook->pCrate : m_pLook->pChestLid));

        if (crate)
        {
            const double size = numberOr(node, "size", 64.0);
            const std::vector<Point2> outline = turnedBox(middle, size, size, turn);
            ground = lowestGroundUnder(outline) + raise;
            builder.addPrism(outline, ground, ground + size, side, lid, "", m_event);
            return;
        }

        const std::vector<Point2> body = turnedBox(middle, 96.0, 64.0, turn);
        ground = lowestGroundUnder(body) + raise;
        const YAML::Node own = childOf(node, "textures");

        if (own.IsDefined() && (childOf(own, "wall").IsDefined() || childOf(own, "top").IsDefined()))
        {
            if (childOf(node, "chest_kind").IsDefined())
            {
                add(m_path + ".chest_kind", "a chest is either a shipped chest (`chest_kind`) or a box of its own "
                    "`textures` (wall, top): leave out one of them");
                return;
            }

            m_warnings.push_back(m_path + (m_id.empty() ? "" : " (" + m_id + ")") + ": a chest with its own "
                "`textures` is a plain box, not a shipped chest (leave them out for the world's own chest, or say "
                "`chest_kind`)");
            raisePlainChest(body, middle, turn, ground, side, lid, builder);
            return;
        }

        const std::string kindName = textOf(node, "chest_kind", defaultChestKind(m_lowered.styleWorld));
        const std::optional<ChestKind> kind = chestKindOf(kindName);

        if (!kind)
        {
            add(m_path + ".chest_kind", "there is no chest kind " + kindName + ": " + chestKindList());
            return;
        }

        for (const ChestFace &face : chestKindFaces(*kind, kind->size, ground, ground + kind->size[2]))
        {
            std::vector<OutdoorModelPoint> points;
            std::vector<std::array<double, 2>> texels = face.texels;

            for (const std::array<double, 3> &corner : face.corners)
            {
                const Point2 at = turned(middle, corner[0], corner[1], turn);
                points.push_back({at[0], at[1], corner[2]});
            }

            // Counter-clockwise seen from outside, as the builder stores faces: turned round when the kind's corner
            // order runs the other way about its outward normal.
            const Point2 normalAt = turned({0.0, 0.0}, face.normal[0], face.normal[1], turn);
            const std::array<double, 3> first = {points[1][0] - points[0][0], points[1][1] - points[0][1],
                points[1][2] - points[0][2]};
            const std::array<double, 3> second = {points[2][0] - points[0][0], points[2][1] - points[0][1],
                points[2][2] - points[0][2]};
            const double facing = (first[1] * second[2] - first[2] * second[1]) * normalAt[0]
                + (first[2] * second[0] - first[0] * second[2]) * normalAt[1]
                + (first[0] * second[1] - first[1] * second[0]) * face.normal[2];

            if (facing < 0.0)
            {
                std::reverse(points.begin(), points.end());
                std::reverse(texels.begin(), texels.end());
            }

            builder.addFace(points, face.texture, texels, m_event);
        }
    }

    // The plain chest of a chest with its own textures: a box 96 by 64 with a lid that slopes to a flat top, 80 high.
    void raisePlainChest(const std::vector<Point2> &body, const Point2 &middle, double turn, double ground,
        const std::string &side, const std::string &lid, OutdoorModelBuilder &builder)
    {
        const std::vector<Point2> crown = turnedBox(middle, 96.0, 32.0, turn);
        builder.addPrism(body, ground, ground + 64.0, side, "", "", m_event);

        // The lid: two slopes along the long sides, upright ends, a flat top.
        for (const size_t first : {size_t{0}, size_t{2}})
        {
            const size_t second = first + 1;
            builder.addSurface({{body[first][0], body[first][1], ground + 64.0},
                {body[second][0], body[second][1], ground + 64.0}, {crown[second][0], crown[second][1], ground + 80.0},
                {crown[first][0], crown[first][1], ground + 80.0}}, lid, m_event);
        }

        builder.addSurface({{body[1][0], body[1][1], ground + 64.0}, {body[2][0], body[2][1], ground + 64.0},
            {crown[2][0], crown[2][1], ground + 80.0}, {crown[1][0], crown[1][1], ground + 80.0}}, side, m_event);
        builder.addSurface({{body[3][0], body[3][1], ground + 64.0}, {body[0][0], body[0][1], ground + 64.0},
            {crown[0][0], crown[0][1], ground + 80.0}, {crown[3][0], crown[3][1], ground + 80.0}}, side, m_event);
        builder.addSurface({{crown[0][0], crown[0][1], ground + 80.0}, {crown[1][0], crown[1][1], ground + 80.0},
            {crown[2][0], crown[2][1], ground + 80.0}, {crown[3][0], crown[3][1], ground + 80.0}}, lid, m_event);
    }

    // A signpost: a post with a board at its top that looks the way the thing is turned (south when not turned).
    void raiseSign(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        const double turn = numberOr(node, "turn", 0.0);
        const double height = numberOr(node, "height", 224.0);
        const double width = numberOr(node, "width", 128.0);
        const std::string wood = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pSign : nullptr);
        const std::string board = textureOf(node, "board", wood.c_str());

        if (height < 64.0 || height > 1024.0 || width < 32.0 || width > 512.0)
        {
            add(m_path, "a sign is 64 to 1024 high with a board 32 to 512 wide");
            return;
        }

        double boardHeight = std::min(96.0, height * 0.4);
        const YAML::Node arms = childOf(node, "arms");
        const bool hung = flagOf(node, "hang");

        if (childOf(node, "board_height").IsDefined() && (!numberOfNode(childOf(node, "board_height"), boardHeight)
            || boardHeight < 16.0 || boardHeight > 256.0 || boardHeight > height))
        {
            add(m_path + ".board_height", "board_height is the board's height, 16 to 256 and no more than the "
                "sign's `height` (the shipped gate sign's board: 80)");
            return;
        }

        if (hung && arms.IsDefined())
        {
            add(m_path + ".hang", "a sign that hangs is one board without a post; a signpost's `arms` stand on a "
                "post: leave out one of them");
            return;
        }

        if (arms.IsDefined())
        {
            raiseSignArms(node, arms, builder, middle, ground, height, width, boardHeight, wood, board);
            return;
        }

        // A sign that hangs (under an arch or a beam the sketch draws) has no post: the board alone, its top at
        // `height` over the ground.
        if (!hung)
        {
            builder.addPrism(turnedBox(middle, 16.0, 16.0, turn), ground, ground + height - boardHeight, wood, "",
                "", m_event);
        }
        const size_t boardFrom = faceCount();
        // With a picture the board reaches the picture's plane, and its own face there is not drawn (it would
        // flicker with the picture).
        const std::vector<Point2> outline = turnedBox(middle, width, board != wood ? 18.0 : 16.0, turn);
        builder.addPrism(outline, ground + height - boardHeight, ground + height, wood, wood, wood, m_event);
        const size_t boardTo = faceCount();
        // The two faces of the board wear the board's own picture, fitted once at its own size.
        const auto picture = [&](const Point2 &left, const Point2 &right)
        {
            const std::array<double, 2> size = pictureSizeOf(board);
            builder.addFace({{left[0], left[1], ground + height - boardHeight},
                {right[0], right[1], ground + height - boardHeight}, {right[0], right[1], ground + height},
                {left[0], left[1], ground + height}}, board,
                {{0.0, size[1]}, {size[0], size[1]}, {size[0], 0.0}, {0.0, 0.0}}, m_event);
        };
        const std::vector<Point2> front = turnedBox(middle, width, 18.0, turn);

        if (board != wood)
        {
            picture(front[0], front[1]);
            picture(front[2], front[3]);
            builder.hideUnder(boardFrom, boardTo, boardTo, faceCount());
        }

        markUsed(boardFrom);
    }

    // A signpost with several arms, as Harmondale's: the post to the full height, and for each arm a board that
    // reaches out from the post the way the arm points, with a title of its own on its faces.
    void raiseSignArms(const YAML::Node &node, const YAML::Node &arms, OutdoorModelBuilder &builder,
        const Point2 &middle, double ground, double height, double width, double boardHeight,
        const std::string &wood, const std::string &board)
    {
        static const std::pair<const char *, double> Compass[] = {{"n", 0.0}, {"ne", 45.0}, {"e", 90.0},
            {"se", 135.0}, {"s", 180.0}, {"sw", 225.0}, {"w", 270.0}, {"nw", 315.0}};

        if (!arms.IsSequence() || arms.size() == 0 || arms.size() > 8)
        {
            add(m_path + ".arms", "arms is a list of 1 to 8 boards: [{title: West to Erathia, toward: w}, {title: "
                "South to Barrow Downs, toward: s}]");
            return;
        }

        // The post (`post`: its width; 16 when left out, Harmondale's signposts 32) and the arms from its sides.
        const double post = numberOr(node, "post", 16.0);
        const double half = post * 0.5;

        if (post < 8.0 || post > 128.0)
        {
            add(m_path + ".post", "a signpost's `post` is its width, 8 to 128 (16 when left out)");
            return;
        }

        builder.addPrism(turnedBox(middle, post, post, numberOr(node, "turn", 0.0)), ground, ground + height, wood,
            wood, "", m_event);
        std::set<std::string> taken;

        for (size_t index = 0; index < arms.size(); ++index)
        {
            const YAML::Node arm = arms[index];
            const std::string at = m_path + ".arms[" + std::to_string(index) + "]";
            const std::string toward = textOf(arm, "toward");
            const std::string title = textOf(arm, "title");
            double bearing = -1.0;

            for (const std::pair<const char *, double> &entry : Compass)
            {
                bearing = toward == entry.first ? entry.second : bearing;
            }

            // S8d: a bearing in degrees clockwise from north, for boards that point between the compass's eight
            // ways (Castle Ironfist's guild sign GuildsignW: three boards at 90, 205 and 335).
            double degrees = 0.0;

            if (bearing < 0.0 && numberOfNode(childOf(arm, "toward"), degrees) && degrees >= 0.0 && degrees < 360.0)
            {
                bearing = degrees;
            }

            // On a sign that carries another's event (`same_event_as`: Caori's Curios' sign) an arm has no title
            // of its own: its faces carry that event too.
            const bool shared = childOf(node, "same_event_as").IsDefined();

            if (bearing < 0.0 || title.empty() != shared || !taken.insert(toward).second)
            {
                add(at, shared ? "an arm of a sign that carries another's event (`same_event_as`) has no `title` (its "
                    "faces say what that event says) and a `toward`: n, ne, e, se, s, sw, w or nw, each way once"
                    : "an arm has a `title` (what the board says) and `toward`: the way it points, n, ne, e, se, s, "
                    "sw, w or nw, or degrees clockwise from north (0 up to 360), each way once");
                continue;
            }

            OutdoorEventPlan event;
            event.number = m_event;

            if (!shared)
            {
                event.id = "evt:" + m_id + ".arm" + std::to_string(index + 1);
                event.number = static_cast<uint16_t>(IdsLock::number(m_ids.events, event.id, 1));
                event.title = title;
                m_things.events.push_back(event);
            }
            // The board: from the post out along the bearing (clockwise from north), its faces looking to both
            // sides of that way.
            const double angle = bearing * Pi / 180.0;
            const Point2 along = {oy::sin(angle), oy::cos(angle)};
            const Point2 across = {along[1], -along[0]};
            const auto corner = [&](double out, double side)
            {
                return Point2{middle[0] + along[0] * out + across[0] * side,
                    middle[1] + along[1] * out + across[1] * side};
            };
            const double low = ground + height - boardHeight;
            const double high = ground + height;
            // Batch O-H: the board begins where its way leaves the post, so an arm across the post's corner (ne on a
            // square post) does not lie in it (its top in the post's top: Erathia's two-way signs).
            double start = half;

            for (const Point2 &postCorner : turnedBox(middle, post, post, numberOr(node, "turn", 0.0)))
            {
                start = std::max(start, (postCorner[0] - middle[0]) * along[0] + (postCorner[1] - middle[1])
                    * along[1]);
            }

            start = start < half + 0.01 ? half : start;
            const double reach = start + width;
            // The arm's own picture (Harmondale's S_West, S_South, S_East), else the sign's `board`; with a picture
            // the board reaches its plane and its own faces there are not drawn.
            const std::string armBoard = textOf(arm, "board", board);
            const double thick = armBoard != wood ? 9.0 : 8.0;
            const size_t boardFrom = faceCount();
            builder.addPrism({corner(start, thick), corner(reach, thick), corner(reach, -thick),
                corner(start, -thick)}, low, high, wood, wood, wood, event.number);
            const size_t boardTo = faceCount();

            if (armBoard != wood)
            {
                for (const double side : {9.0, -9.0})
                {
                    // Left then right as seen from outside the face.
                    const Point2 left = side > 0.0 ? corner(start, side) : corner(reach, side);
                    const Point2 right = side > 0.0 ? corner(reach, side) : corner(start, side);
                    const std::array<double, 2> size = pictureSizeOf(armBoard);
                    builder.addFace({{left[0], left[1], low}, {right[0], right[1], low}, {right[0], right[1], high},
                        {left[0], left[1], high}}, armBoard,
                        {{0.0, size[1]}, {size[0], size[1]}, {size[0], 0.0}, {0.0, 0.0}}, event.number);
                }

                builder.hideUnder(boardFrom, boardTo, boardTo, faceCount());
            }
        }
    }

    // A platform: a block one can stand on.
    void raisePlatform(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;
        Point2 size = {0.0, 0.0};

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        const bool invisible = flagOf(node, "invisible");
        const double height = numberOr(node, "height", invisible ? 0.0 : 32.0);

        if (!invisible && (childOf(node, "sides").IsDefined() || childOf(node, "tiers").IsDefined()))
        {
            raiseShapedPlatform(node, builder, middle, ground, height);
            return;
        }

        if (!pointOf(childOf(node, "size"), size) || size[0] < 16.0 || size[1] < 16.0
            || height < (invisible ? 0.0 : 8.0) || height > 4096.0)
        {
            add(m_path, "a platform has `size: [width, depth]` in map units (at least 16 each) and a `height` of 8 "
                "to 4096 (an invisible one 0 to 4096: 0 lies on the land)");
            return;
        }

        const std::string stone = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string top = textureOf(node, "top", stone.c_str());
        const size_t from = faceCount();
        // S8d: `chamfer`, the corners cut off this far along each side (Erathia's alchemist's octagonal deck).
        const double chamfer = numberOr(node, "chamfer", 0.0);

        if (childOf(node, "chamfer").IsDefined() && (chamfer < 8.0 || chamfer > std::min(size[0], size[1]) * 0.5 - 8.0))
        {
            add(m_path + ".chamfer", "a platform's `chamfer` cuts its four corners off this far along each side: 8 up "
                "to 8 under half its shorter side (" + formatNumber(std::max(8.0, std::min(size[0], size[1]) * 0.5
                - 8.0)) + "); a regular octagon cuts about 0.29 of its width");
            return;
        }

        const auto boxOutline = [&]()
        {
            const double turn = numberOr(node, "turn", 0.0);

            if (chamfer <= 0.0)
            {
                return turnedBox(middle, size[0], size[1], turn);
            }

            const double x = size[0] * 0.5;
            const double y = size[1] * 0.5;
            return std::vector<Point2>{turned(middle, -x + chamfer, -y, turn), turned(middle, x - chamfer, -y, turn),
                turned(middle, x, -y + chamfer, turn), turned(middle, x, y - chamfer, turn),
                turned(middle, x - chamfer, y, turn), turned(middle, -x + chamfer, y, turn),
                turned(middle, -x, y - chamfer, turn), turned(middle, -x, -y + chamfer, turn)};
        };

        if (invisible)
        {
            // Only its top, not drawn, as the originals' one-face plates and lids (Emerald Island's Tut02 step
            // plates, Deyja's 512plate: attributes 0x3108, with a step event also PressurePlate).
            std::vector<OutdoorModelPoint> face;

            for (const Point2 &corner : boxOutline())
            {
                face.push_back({corner[0], corner[1], ground + height});
            }

            const int index = builder.addSurface(face, top, m_event);
            builder.hide(index);

            if (index >= 0)
            {
                m_usedFaces.insert(static_cast<size_t>(index));
            }

            return;
        }

        // Batch O-H: `holes` in its top: [{at: [x, y] (cells, the hole's middle), size: [width, depth], turn,
        // depth}], each a box cut out of the top with upright sides `depth` down and a floor (Erathia's plaza: the
        // troughs and the pool sunk 64 into the court); `depth: 0` leaves an opening for a plate flush in the slab
        // (Castle Ironfist's pads: the plate's own top fills it).
        std::vector<std::vector<Point2>> holes;
        std::vector<double> holeDepths;
        const YAML::Node holeNodes = childOf(node, "holes");
        const std::vector<Point2> outline = boxOutline();

        for (size_t index = 0; holeNodes.IsDefined() && index < (holeNodes.IsSequence() ? holeNodes.size() : 1);
             ++index)
        {
            const YAML::Node hole = holeNodes.IsSequence() ? holeNodes[index] : holeNodes;
            Point2 cell = {0.0, 0.0};
            Point2 holeSize = {0.0, 0.0};
            const double depth = numberOr(hole, "depth", 64.0);

            if (!holeNodes.IsSequence() || !pointOf(childOf(hole, "at"), cell)
                || !pointOf(childOf(hole, "size"), holeSize) || holeSize[0] < 16.0 || holeSize[1] < 16.0
                || depth < 0.0 || depth > height + 1024.0)
            {
                add(m_path + ".holes", "a platform's holes are [{at: [x, y] (cells: the hole's middle), size: [width, "
                    "depth] (16 or more each), turn (degrees), depth (how far its pit goes down, 0 up to the "
                    "platform's height and 1024 more; 64)}]");
                return;
            }

            const std::vector<Point2> box = turnedBox(toWorld(cell), holeSize[0], holeSize[1],
                numberOr(hole, "turn", 0.0));

            for (const Point2 &corner : box)
            {
                if (!pointInPolygon(outline, corner, 8.0))
                {
                    add(m_path + ".holes[" + std::to_string(index) + "]", "the hole reaches to within 8 of the "
                        "platform's edge or past it: it is cut in the platform's top");
                    return;
                }
            }

            holes.push_back(box);
            holeDepths.push_back(depth);
        }

        builder.addPrism(outline, ground - 64.0, ground + height, stone, holes.empty() ? top : std::string(), "",
            m_event);

        if (!holes.empty())
        {
            // The top in convex pieces round the holes; under each hole its pit.
            std::vector<std::vector<Point2>> pieces = {outline};

            for (const std::vector<Point2> &hole : holes)
            {
                std::vector<std::vector<Point2>> left;
                const double orientation = polygonDoubleArea(hole) >= 0.0 ? 1.0 : -1.0;

                for (const std::vector<Point2> &piece : pieces)
                {
                    std::vector<Point2> rest = piece;

                    for (size_t side = 0; side < hole.size() && rest.size() >= 3; ++side)
                    {
                        const Point2 &a = hole[side];
                        const Point2 &b = hole[(side + 1) % hole.size()];
                        // The side's outward normal.
                        const Point2 normal = {(b[1] - a[1]) * orientation, (a[0] - b[0]) * orientation};
                        const double offset = normal[0] * a[0] + normal[1] * a[1];
                        const std::vector<Point2> outside = clipConvex(rest, {-normal[0], -normal[1]}, -offset);

                        if (outside.size() >= 3 && std::fabs(polygonDoubleArea(outside)) > 2.0)
                        {
                            left.push_back(outside);
                        }

                        rest = clipConvex(rest, normal, offset);
                    }
                }

                pieces = left;
            }

            for (const std::vector<Point2> &piece : pieces)
            {
                std::vector<OutdoorModelPoint> points;

                for (const Point2 &point : piece)
                {
                    points.push_back({point[0], point[1], ground + height});
                }

                outdoorFacingAdd(builder, points, {0.0, 0.0, 1.0}, top);
            }

            for (size_t index = 0; index < holes.size(); ++index)
            {
                const std::vector<Point2> &hole = holes[index];
                const double floor = ground + height - holeDepths[index];

                if (holeDepths[index] <= 0.5)
                {
                    continue;
                }

                std::vector<OutdoorModelPoint> bottom;
                Point2 centre = {0.0, 0.0};

                for (const Point2 &point : hole)
                {
                    centre = {centre[0] + point[0] / hole.size(), centre[1] + point[1] / hole.size()};
                }

                for (size_t side = 0; side < hole.size(); ++side)
                {
                    const Point2 &a = hole[side];
                    const Point2 &b = hole[(side + 1) % hole.size()];
                    const Point2 mid = {(a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5};
                    // Seen from inside the pit: its sides look in.
                    outdoorFacingAdd(builder, {{a[0], a[1], floor}, {b[0], b[1], floor}, {b[0], b[1], ground + height},
                        {a[0], a[1], ground + height}}, {centre[0] - mid[0], centre[1] - mid[1], 0.0}, stone);
                    bottom.push_back({a[0], a[1], floor});
                }

                outdoorFacingAdd(builder, bottom, {0.0, 0.0, 1.0}, top);
            }
        }

        // Its used part is its top.
        for (size_t face = from; face < faceCount(); ++face)
        {
            if (m_pModel->faces[face].polygonType == 3)
            {
                m_usedFaces.insert(face);
            }
        }
    }

    void outdoorFacingAdd(OutdoorModelBuilder &builder, const std::vector<OutdoorModelPoint> &points,
        const std::array<double, 3> &normal, const std::string &textureName)
    {
        builder.addSurface(outdoorFacing(points, normal), textureName, m_event);
    }

    // Batch O-D: a round or many-sided platform (`sides` with `radius`; a box of `size` without) and a stepped one
    // (`tiers`: each [in, up], the outline drawn in and raised, a level tread round each): Dagger Wound's teleport
    // pads, the Plane between Planes' shield, Bracada's stepped pads.
    void raiseShapedPlatform(const YAML::Node &node, OutdoorModelBuilder &builder, const Point2 &middle, double ground,
        double height)
    {
        std::vector<Point2> outline;
        const double turn = numberOr(node, "turn", 0.0);
        const double sides = numberOr(node, "sides", 0.0);
        const double radius = numberOr(node, "radius", 0.0);
        Point2 size = {0.0, 0.0};

        if (childOf(node, "sides").IsDefined())
        {
            if (sides < 3.0 || sides > 16.0 || sides != std::floor(sides) || radius < 16.0 || radius > 4096.0)
            {
                add(m_path, "a round platform has `sides` (3 to 16) and a `radius` (16 to 4096) to its corners");
                return;
            }

            for (int side = 0; side < static_cast<int>(sides); ++side)
            {
                // The first side looks south before the turn, as a round part's first wall.
                const double angle = (side - 0.5) * 2.0 * Pi / sides - Pi * 0.5 - turn * Pi / 180.0;
                outline.push_back({middle[0] + radius * oy::cos(angle), middle[1] + radius * oy::sin(angle)});
            }
        }
        else if (!pointOf(childOf(node, "size"), size) || size[0] < 16.0 || size[1] < 16.0)
        {
            add(m_path, "a platform has `size: [width, depth]` in map units (at least 16 each), or `sides` and a "
                "`radius`");
            return;
        }
        else
        {
            outline = turnedBox(middle, size[0], size[1], turn);
        }

        if (height < 8.0 || height > 4096.0)
        {
            add(m_path, "a platform's `height` is 8 to 4096");
            return;
        }

        std::vector<std::array<double, 2>> tiers;
        const YAML::Node tierNodes = childOf(node, "tiers");

        for (size_t index = 0; tierNodes.IsDefined() && index < (tierNodes.IsSequence() ? tierNodes.size() : 1);
             ++index)
        {
            Point2 tier = {0.0, 0.0};

            if (!tierNodes.IsSequence() || !pointOf(tierNodes[index], tier) || tier[0] < 0.0 || tier[0] > 2048.0
                || tier[1] <= 0.0 || tier[1] > 2048.0 || index >= 16)
            {
                add(m_path + ".tiers", "a stepped platform's `tiers` are 1 to 16 steps over its `height`, each [in, "
                    "up] in map units (in 0 to 2048, up above 0 to 2048)");
                return;
            }

            tiers.push_back(tier);
        }

        const std::string stone = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string top = textureOf(node, "top", stone.c_str());
        const size_t from = faceCount();
        double area = 0.0;

        for (size_t index = 0; index < outline.size(); ++index)
        {
            const Point2 &a = outline[index];
            const Point2 &b = outline[(index + 1) % outline.size()];
            area += a[0] * b[1] - b[0] * a[1];
        }

        if (area < 0.0)
        {
            std::reverse(outline.begin(), outline.end());
        }

        std::vector<Point2> ring = outline;
        double z = ground + height;
        builder.addPrism(ring, ground - 64.0, z, stone, tiers.empty() ? top : "", "", m_event);

        for (size_t index = 0; index < tiers.size(); ++index)
        {
            std::vector<Point2> next = ring;
            Point2 centre = {0.0, 0.0};

            for (const Point2 &point : ring)
            {
                centre = {centre[0] + point[0] / ring.size(), centre[1] + point[1] / ring.size()};
            }

            // Drawn in by `in` on every side: the corners move toward the middle by in / cos(half the corner).
            for (size_t corner = 0; corner < ring.size(); ++corner)
            {
                const Point2 &before = ring[(corner + ring.size() - 1) % ring.size()];
                const Point2 &here = ring[corner];
                const Point2 &after = ring[(corner + 1) % ring.size()];
                const double inLength = std::max(lengthOf(before, here), 1.0e-9);
                const double outLength = std::max(lengthOf(here, after), 1.0e-9);
                const Point2 a = {-(here[1] - before[1]) / inLength, (here[0] - before[0]) / inLength};
                const Point2 b = {-(after[1] - here[1]) / outLength, (after[0] - here[0]) / outLength};
                const double cosine = std::max(0.2, (1.0 + a[0] * b[0] + a[1] * b[1]) * 0.5);
                const Point2 bisector = {(a[0] + b[0]) * 0.5 / cosine, (a[1] + b[1]) * 0.5 / cosine};
                next[corner] = {here[0] + bisector[0] * tiers[index][0], here[1] + bisector[1] * tiers[index][0]};
            }

            for (size_t corner = 0; corner < ring.size() && tiers[index][0] > 0.5; ++corner)
            {
                const size_t following = (corner + 1) % ring.size();
                builder.addSurface({{ring[corner][0], ring[corner][1], z}, {ring[following][0], ring[following][1], z},
                    {next[following][0], next[following][1], z}, {next[corner][0], next[corner][1], z}}, top, m_event);
            }

            builder.addPrism(next, z, z + tiers[index][1], stone, index + 1 == tiers.size() ? top : "", "", m_event);
            ring = next;
            z += tiers[index][1];
        }

        for (size_t face = from; face < faceCount(); ++face)
        {
            if (m_pModel->faces[face].polygonType == 3)
            {
                m_usedFaces.insert(face);
            }
        }
    }

    // A fence along a line: square posts standing on the ground at every point and every `every` between, rails
    // from post to post that follow the ground, and between the posts a face that is not drawn, so the party does
    // not walk through (as a railing's). Vertigo's gardens and pens; the shipped towns draw theirs as models of
    // posts and planks (Harmondale's paddock).
    void raiseFence(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        std::vector<Point2> line;

        if (!lineOf(node, line))
        {
            return;
        }

        const bool closed = flagOf(node, "closed");
        const double height = numberOr(node, "height", 112.0);
        const double post = numberOr(node, "post", 16.0);
        const double every = numberOr(node, "every", 192.0);
        const double rails = numberOr(node, "rails", 2.0);
        const double rail = numberOr(node, "thickness", 8.0);

        if (height < 32.0 || height > 512.0 || post < 8.0 || post > 64.0 || every < post * 2.0 || every > 1024.0
            || rails < 1.0 || rails > 4.0 || rails != std::floor(rails) || rail < 4.0 || rail > 32.0
            || rail * rails * 2.0 > height || (closed && line.size() < 3))
        {
            add(m_path, "a fence is 32 to 512 high (`height`, 112), on posts 8 to 64 wide (`post`, 16) at most "
                "`every` apart (twice the post's width to 1024; 192), with 1 to 4 `rails` (2) `thickness` 4 to 32 "
                "thick (8) that fit in its height; a closed fence has three points or more");
            return;
        }

        const std::string postTexture = textureOf(node, "post", m_pLook != nullptr ? m_pLook->pWood : nullptr);
        const std::string railTexture = textureOf(node, "rail", postTexture.c_str());
        const size_t stretches = closed ? line.size() : line.size() - 1;
        // The posts: at each point and along each stretch.
        std::vector<Point2> places;

        for (size_t index = 0; index < stretches; ++index)
        {
            const Point2 &from = line[index];
            const Point2 &to = line[(index + 1) % line.size()];
            const int gaps = std::max(1, static_cast<int>(std::ceil(lengthOf(from, to) / every)));

            for (int gap = 0; gap < gaps; ++gap)
            {
                places.push_back({from[0] + (to[0] - from[0]) * gap / gaps, from[1] + (to[1] - from[1]) * gap / gaps});
            }
        }

        if (!closed)
        {
            places.push_back(line.back());
        }

        const double half = post * 0.5;
        std::vector<double> grounds;

        for (const Point2 &place : places)
        {
            grounds.push_back(groundAt(place));
            builder.addPrism({{place[0] - half, place[1] - half}, {place[0] + half, place[1] - half},
                {place[0] + half, place[1] + half}, {place[0] - half, place[1] + half}}, grounds.back() - 32.0,
                grounds.back() + height, postTexture, postTexture, "", m_event);
        }

        const size_t spans = closed ? places.size() : places.size() - 1;

        for (size_t index = 0; index < spans; ++index)
        {
            const Point2 &from = places[index];
            const Point2 &to = places[(index + 1) % places.size()];
            const double length = lengthOf(from, to);
            const Point2 along = {(to[0] - from[0]) / length, (to[1] - from[1]) / length};
            // A rail is `thickness` high and as deep, half a post's width at most.
            const double depth = std::min(rail, half) * 0.5;
            const Point2 side = {along[1] * depth, -along[0] * depth};
            // From the near post's face to the far post's, its ends inside the posts.
            const Point2 start = {from[0] + along[0] * half * 0.5, from[1] + along[1] * half * 0.5};
            const Point2 end = {to[0] - along[0] * half * 0.5, to[1] - along[1] * half * 0.5};
            const double rise = grounds[(index + 1) % places.size()] - grounds[index];
            const double startShare = half * 0.5 / length;
            const double startGround = grounds[index] + rise * startShare;
            const double endGround = grounds[index] + rise * (1.0 - startShare);

            for (int number = 0; number < static_cast<int>(rails); ++number)
            {
                // The rails share the height evenly; the top one ends `rail` under the posts' tops.
                const double top = height - rail - (height - 2.0 * rail) * number / rails;
                const double bottom = top - rail;
                const auto at = [&](const Point2 &place, double sign, double ground, double z)
                {
                    return OutdoorModelPoint{place[0] + side[0] * sign, place[1] + side[1] * sign, ground + z};
                };
                builder.addSurface({at(start, 1.0, startGround, top), at(end, 1.0, endGround, top),
                    at(end, -1.0, endGround, top), at(start, -1.0, startGround, top)}, railTexture, m_event);
                builder.addSurface({at(start, -1.0, startGround, bottom), at(end, -1.0, endGround, bottom),
                    at(end, 1.0, endGround, bottom), at(start, 1.0, startGround, bottom)}, railTexture, m_event);
                builder.addSurface({at(start, 1.0, startGround, bottom), at(end, 1.0, endGround, bottom),
                    at(end, 1.0, endGround, top), at(start, 1.0, startGround, top)}, railTexture, m_event);
                builder.addSurface({at(end, -1.0, endGround, bottom), at(start, -1.0, startGround, bottom),
                    at(start, -1.0, startGround, top), at(end, -1.0, endGround, top)}, railTexture, m_event);
            }

            // The barrier, both ways, on the line from the ground to the top rail.
            const double barrier = height - rail;
            builder.hide(builder.addSurface({{start[0], start[1], startGround}, {end[0], end[1], endGround},
                {end[0], end[1], endGround + barrier}, {start[0], start[1], startGround + barrier}}, postTexture,
                m_event));
            builder.hide(builder.addSurface({{end[0], end[1], endGround}, {start[0], start[1], startGround},
                {start[0], start[1], startGround + barrier}, {end[0], end[1], endGround + barrier}}, postTexture,
                m_event));
        }
    }

    // An invisible barrier along a line (`kind: barrier`): per stretch one upright face each way that is not
    // drawn and blocks, from `bottom` over the land to `height` over it, following the land under each point (as
    // the originals' Invis models: outc3's 896 x 384 wall, outa2's InvisN/S). No event.
    void raiseBarrier(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        std::vector<Point2> line;

        if (!lineOf(node, line))
        {
            return;
        }

        const bool closed = flagOf(node, "closed");
        const double height = numberOr(node, "height", 512.0);
        const double bottom = numberOr(node, "bottom", 0.0);

        if (height < 32.0 || height > 8192.0 || bottom < -512.0 || bottom > height - 32.0
            || (closed && line.size() < 3))
        {
            add(m_path, "a barrier stands from `bottom` (-512 to 32 under its height; 0) to `height` (32 to 8192; "
                "512) over the land; a closed barrier has three points or more");
            return;
        }

        if (m_event != 0)
        {
            add(m_path, "a barrier is never used: it has no event (a pressure plate is an invisible platform with "
                "`trigger: step`)");
            return;
        }

        const std::string texture = textureOf(node, "texture", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const size_t stretches = closed ? line.size() : line.size() - 1;

        for (size_t index = 0; index < stretches; ++index)
        {
            const Point2 &from = line[index];
            const Point2 &to = line[(index + 1) % line.size()];
            const double fromGround = groundAt(from);
            const double toGround = groundAt(to);
            builder.hide(builder.addSurface({{from[0], from[1], fromGround + bottom}, {to[0], to[1], toGround + bottom},
                {to[0], to[1], toGround + height}, {from[0], from[1], fromGround + height}}, texture, 0));
            builder.hide(builder.addSurface({{to[0], to[1], toGround + bottom}, {from[0], from[1], fromGround + bottom},
                {from[0], from[1], fromGround + height}, {to[0], to[1], toGround + height}}, texture, 0));
        }
    }

    // A waterfall (core/OutdoorFalls): the top water joining the stream's at the lip, the sheet down to the pool
    // (FlowDown, let through: out03's WaterfallC1test), the foot water and rock sides; the land under it was cut by
    // the lowering. The level water flows along the fall (Fluid and FlowDown, its picture running on into the
    // sheet's).
    void raiseWaterfall(OutdoorModelBuilder &builder)
    {
        for (const OutdoorFallPlan &fall : m_lowered.falls)
        {
            if (fall.path != m_path)
            {
                continue;
            }

            std::vector<int> sheetFaces;
            std::vector<int> waterFaces;
            raiseOutdoorFall(fall, builder, m_event, sheetFaces, waterFaces);

            for (const int face : sheetFaces)
            {
                if (face >= 0)
                {
                    m_pModel->faces[static_cast<size_t>(face)].attributes |=
                        Game::faceAttributeBit(Game::FaceAttribute::FlowDown);
                    builder.letThrough(face);
                }
            }

            for (const int face : waterFaces)
            {
                if (face >= 0)
                {
                    m_pModel->faces[static_cast<size_t>(face)].attributes |=
                        Game::faceAttributeBit(Game::FaceAttribute::Fluid)
                        | Game::faceAttributeBit(Game::FaceAttribute::FlowDown);
                }
            }
        }
    }

    // Stairs: steps along a line from its first point up to its last, each a block down to the ground.
    void raiseStairs(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        std::vector<Point2> line;

        if (!lineOf(node, line))
        {
            return;
        }

        const double width = numberOr(node, "width", 256.0);
        const double rise = numberOr(node, "rise", 256.0);
        const double tread = numberOr(node, "tread", 32.0);
        const double length = lengthOf(line.front(), line.back());
        const int steps = std::max(1, static_cast<int>(std::lround(rise / tread)));

        if (line.size() != 2 || width < 32.0 || rise < 8.0 || rise > 4096.0 || tread < 8.0 || tread > 64.0
            || steps > 128)
        {
            add(m_path, "stairs have a `line` of two points (the foot, then the top), a `width` of at least 32, a "
                "`rise` of 8 to 4096 and steps (`tread`) 8 to 64 high, at most 128 of them");
            return;
        }

        const std::string stone = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const double ground = groundAt(line.front()) + numberOr(node, "raise", 0.0);
        const Point2 along = {(line.back()[0] - line.front()[0]) / length, (line.back()[1] - line.front()[1]) / length};
        const Point2 side = {along[1] * width * 0.5, -along[0] * width * 0.5};

        if (flagOf(node, "ramp"))
        {
            // One sloping slab from the foot up to the top (a pier's ramp, a terrace's): its top, two cheeks and
            // the upright end under the top.
            if (rise > length)
            {
                add(m_path, "a ramp steeper than 45 degrees cannot be walked: it climbs " + formatNumber(rise)
                    + " over " + formatNumber(std::round(length)) + "; make the line longer, the rise lower, or "
                    "leave `ramp` out for steps");
                return;
            }

            const std::string top = textureOf(node, "top", stone.c_str());
            const Point2 &foot = line.front();
            const Point2 &head = line.back();
            const OutdoorModelPoint footRight = {foot[0] + side[0], foot[1] + side[1], ground};
            const OutdoorModelPoint footLeft = {foot[0] - side[0], foot[1] - side[1], ground};
            const OutdoorModelPoint headRight = {head[0] + side[0], head[1] + side[1], ground + rise};
            const OutdoorModelPoint headLeft = {head[0] - side[0], head[1] - side[1], ground + rise};
            const double base = ground - 64.0;
            builder.addSurface({footRight, headRight, headLeft, footLeft}, top, m_event);
            builder.addSurface({{footLeft[0], footLeft[1], base}, {headLeft[0], headLeft[1], base}, headLeft,
                footLeft}, stone, m_event);
            builder.addSurface({{headRight[0], headRight[1], base}, {footRight[0], footRight[1], base}, footRight,
                headRight}, stone, m_event);
            builder.addSurface({{headLeft[0], headLeft[1], base}, {headRight[0], headRight[1], base}, headRight,
                headLeft}, stone, m_event);
            builder.addSurface({{footRight[0], footRight[1], base}, {footLeft[0], footLeft[1], base}, footLeft,
                footRight}, stone, m_event);
            return;
        }

        if (!outdoorSlopeWalkable(rise, length))
        {
            add(m_path, "the party cannot walk up a flight that climbs " + formatNumber(rise) + " over "
                + formatNumber(std::round(length)) + ": the game slides it down a slope steeper than 45 degrees "
                "that is 128 or more high; make the line longer (at least " + formatNumber(std::ceil(rise * 1.0016))
                + ") or the rise lower");
            return;
        }

        // The treads in `top` (the wall texture when left out), as a ramp's.
        const std::string treads = textureOf(node, "top", stone.c_str());

        for (int step = 0; step < steps; ++step)
        {
            const double from = length * step / steps;
            const double to = length * (step + 1) / steps;
            const Point2 near = {line.front()[0] + along[0] * from, line.front()[1] + along[1] * from};
            const Point2 far = {line.front()[0] + along[0] * to, line.front()[1] + along[1] * to};
            const size_t first = faceCount();
            builder.addPrism({{near[0] + side[0], near[1] + side[1]}, {far[0] + side[0], far[1] + side[1]},
                {far[0] - side[0], far[1] - side[1]}, {near[0] - side[0], near[1] - side[1]}}, ground - 64.0,
                ground + rise * (step + 1) / steps, stone, treads, "", m_event);

            // The riser: the step's wall that looks down the flight.
            for (size_t face = first; face < faceCount(); ++face)
            {
                const Game::OutdoorBModelFace &stepFace = m_pModel->faces[face];

                if (stepFace.polygonType == 1
                    && stepFace.planeNormalX * along[0] + stepFace.planeNormalY * along[1] < -0.99 * 65536.0)
                {
                    builder.letThrough(static_cast<int>(face));
                }
            }
        }

        // Over the steps the slope the party walks up, as the shipped maps lay it: from the foot of the first
        // riser through the foot of every riser to the top's far edge, under the treads' front edges.
        builder.addStepSlope({{line.front()[0] + side[0], line.front()[1] + side[1], ground},
            {line.back()[0] + side[0], line.back()[1] + side[1], ground + rise},
            {line.back()[0] - side[0], line.back()[1] - side[1], ground + rise},
            {line.front()[0] - side[0], line.front()[1] - side[1], ground}}, stone, m_event);
    }

    // A doorway: a door in a stone frame that stands against a slope or a rock, the way into a cave or a dungeon
    // that has no house round it. It looks south when not turned.
    void raiseDoorway(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        // S8g: `floor`, the sill's height against the plan's datum (X1's and X2's quay doors: the land's height at the
        // middle lies below a quay wall's top); left out, the land's there (with `raise`).
        if (childOf(node, "floor").IsDefined())
        {
            ground = numberOr(node, "floor", ground) + numberOr(node, "raise", 0.0);
        }

        // S8d: `facing` (n, e, s or w, as a building's) is the way the door looks before `turn` turns it on: s, the
        // default, looks south (it was read nowhere before: mm6_outd3's Shadow Guild Hideout says `facing: s` with
        // `turn: -45`, south-east).
        const std::string facing = textOf(node, "facing", "s");
        const double base = facing == "s" ? 0.0 : facing == "w" ? 90.0 : facing == "n" ? 180.0
            : facing == "e" ? -90.0 : std::nan("");

        if (std::isnan(base))
        {
            add(m_path + ".facing", "a doorway's `facing` is n, e, s or w: the way its door looks before `turn` turns "
                "it on (s when left out)");
            return;
        }

        const double turn = base + numberOr(node, "turn", 0.0);
        const double width = numberOr(node, "width", 128.0);
        const double height = numberOr(node, "height", 256.0);
        const std::string stone = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string door = textureOf(node, "door", m_pLook != nullptr ? m_pLook->pDoor : nullptr);

        const double depth = numberOr(node, "depth", 64.0);
        const double hood = numberOr(node, "hood", 0.0);

        if (width < 64.0 || width > 1024.0 || height < 64.0 || height > 1024.0)
        {
            add(m_path, "a doorway's door is 64 to 1024 wide and high (128 by 256 when left out)");
            return;
        }

        if (depth < 16.0 || depth > 2048.0 || hood < 0.0 || hood > 2048.0)
        {
            add(m_path, "a doorway's frame is 16 to 2048 deep (`depth`, 64 when left out: how far it reaches back "
                "into the slope) and its `hood` reaches 0 to 2048 forward over the way in");
            return;
        }

        // The frame: a block half again as wide and an eighth higher than the door unless `frame_width` and
        // `frame_height` say (outc3's DunEntC3: 512 by 448 round a door 128 by 296), `depth` deep behind its
        // front, its top `textures.top` (the stone's when left out); the door lies on its front, a finger's
        // breadth before it.
        const double frameWidth = numberOr(node, "frame_width", width * 1.5);
        const double frameHeight = numberOr(node, "frame_height", height * 1.125);
        const double passage = numberOr(node, "passage", width);
        const std::string top = textureOf(node, "top", stone.c_str());

        if (frameWidth < width + 32.0 || frameWidth > 4096.0 || frameHeight < height + 16.0
            || frameHeight > 4096.0 || passage < width || passage > frameWidth - 32.0)
        {
            add(m_path, "a doorway's frame is at least 32 wider (`frame_width`) and 16 higher (`frame_height`) than "
                "its door, at most 4096, and the way in under its `hood` (`passage`) is the door's width up to the "
                "frame's less 32");
            return;
        }

        // A named door uses its texture class's width and the native 256-texel door row.
        // A fitted painting supplies both dimensions in logical texels.
        std::string doorName = door;
        std::transform(doorName.begin(), doorName.end(), doorName.begin(),
            [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
        const auto known = m_lowered.doorPictures.find(doorName);
        Point2 picture = {known != m_lowered.doorPictures.end() && known->second.size[0] >= 32
            ? static_cast<double>(known->second.size[0]) : 128.0, 256.0};
        const YAML::Node surface = childOf(childOf(node, "textures"), "door");
        const YAML::Node fit = childOf(surface, "fit");
        const YAML::Node size = childOf(surface, "size");
        const bool fitted = fit.IsDefined() && fit.IsScalar() && fit.Scalar() == "true";
        const bool validSize = fitted ? pointOf(size, picture) && std::min(picture[0], picture[1]) >= 8.0
            && std::max(picture[0], picture[1]) <= 32767.0 && !childOf(surface, "liquid").IsDefined()
            && !childOf(surface, "flow").IsDefined() : !size.IsDefined();

        if (!validSize || (fit.IsDefined() && !fitted && (!fit.IsScalar() || fit.Scalar() != "false")))
        {
            add(m_path + ".textures.door", "a fitted door picture uses {texture: <name>, fit: true, "
                "size: [width, height]} with each dimension 8 to 32767 texels");
            return;
        }

        builder.addPrism(turnedBox(middle, frameWidth, depth, turn, 0.0, depth * 0.5 - 32.0), ground - 64.0,
            ground + frameHeight, stone, top, "", m_event);

        if (hood > 0.0)
        {
            // The hood: the frame drawn forward over the way in, open below: a roof at the door's height and a
            // cheek on each side, so the door stands at the back of a mouth (a cave's, a den's) `passage` wide.
            // Their backs (the box's third side) lie on the frame's front and are left out: drawn back to back with
            // it they flickered (X1's Witch Tower door, P3 2026-11-24).
            const double cheek = (frameWidth - passage) * 0.5;
            const double forward = -32.0 - hood * 0.5;
            builder.addPrism(turnedBox(middle, frameWidth, hood, turn, 0.0, forward), ground + height,
                ground + frameHeight, stone, top, stone, m_event, 2);

            for (const double sideways : {-(passage + cheek) * 0.5, (passage + cheek) * 0.5})
            {
                builder.addPrism(turnedBox(middle, cheek, hood, turn, sideways, forward), ground - 64.0,
                    ground + height, stone, "", "", m_event, 2);
            }
        }
        if (textOf(node, "roof") == "gable")
        {
            // A gabled portico over the way in (New Sorpigal's Abandoned Temple): two slopes over the frame's
            // width from the frame's top to a ridge running out over the hood, the gable closed at the front.
            const double reach = hood > 0.0 ? hood + 32.0 : 160.0;
            const double rise = frameWidth * 0.35;
            const double eaves = ground + frameHeight;
            const double forward = -32.0 - reach;
            const Point2 backLeft = turned(middle, -frameWidth * 0.5 - 16.0, -32.0, turn);
            const Point2 backRight = turned(middle, frameWidth * 0.5 + 16.0, -32.0, turn);
            const Point2 frontLeft = turned(middle, -frameWidth * 0.5 - 16.0, forward, turn);
            const Point2 frontRight = turned(middle, frameWidth * 0.5 + 16.0, forward, turn);
            const Point2 backRidge = turned(middle, 0.0, -32.0, turn);
            const Point2 frontRidge = turned(middle, 0.0, forward, turn);
            // S8d: the slopes and the gable in `textures.roof` (the frame's stone when left out): a turf hood in the
            // ground's grass (Erathia's bandit caves Bandit_: Grass over a CWB frame).
            const std::string roofTexture = textureOf(node, "roof", stone.c_str());
            builder.addSurface({{frontLeft[0], frontLeft[1], eaves}, {frontRidge[0], frontRidge[1], eaves + rise},
                {backRidge[0], backRidge[1], eaves + rise}, {backLeft[0], backLeft[1], eaves}}, roofTexture, m_event);
            builder.addSurface({{frontRidge[0], frontRidge[1], eaves + rise}, {frontRight[0], frontRight[1], eaves},
                {backRight[0], backRight[1], eaves}, {backRidge[0], backRidge[1], eaves + rise}}, roofTexture,
                m_event);
            builder.addSurface({{frontLeft[0], frontLeft[1], eaves}, {frontRight[0], frontRight[1], eaves},
                {frontRidge[0], frontRidge[1], eaves + rise}}, roofTexture, m_event);
            builder.addSurface({{backLeft[0], backLeft[1], eaves}, {backRight[0], backRight[1], eaves},
                {frontRight[0], frontRight[1], eaves}, {frontLeft[0], frontLeft[1], eaves}}, stone, m_event);
        }

        const std::string arch = textOf(node, "arch");
        const size_t doorFrom = faceCount();
        // The door's outline as [across from its middle, up], counter-clockwise seen from outside; with an arched
        // head the picture's top corners are cut away and the frame shows there.
        std::vector<std::array<double, 2>> outline = {{-width * 0.5, 0.0}, {width * 0.5, 0.0}};

        if (arch == "round" || arch == "pointed" || arch == "segment")
        {
            const std::vector<std::array<double, 2>> head =
                outdoorArchHead(width, height, arch, static_cast<int>(numberOr(node, "sides", 6.0)));

            for (size_t index = head.size(); index-- > 0;)
            {
                outline.push_back(head[index]);
            }
        }
        else
        {
            outline.push_back({width * 0.5, height});
            outline.push_back({-width * 0.5, height});
        }

        // The part of the outline between `low` and `high` across, its picture stretched over [low, high] once
        // (mirrored from `high` back to `low` for the second leaf).
        const auto leafFace = [&](double low, double high, bool mirrored)
        {
            std::vector<std::array<double, 2>> kept;

            for (size_t index = 0; index < outline.size(); ++index)
            {
                const std::array<double, 2> &a = outline[index];
                const std::array<double, 2> &b = outline[(index + 1) % outline.size()];

                if (a[0] >= low - 1.0e-6 && a[0] <= high + 1.0e-6)
                {
                    kept.push_back(a);
                }

                for (const double edge : {low, high})
                {
                    if ((a[0] - edge) * (b[0] - edge) < 0.0)
                    {
                        const double share = (edge - a[0]) / (b[0] - a[0]);
                        kept.push_back({edge, a[1] + (b[1] - a[1]) * share});
                    }
                }
            }

            std::vector<OutdoorModelPoint> points;
            std::vector<std::array<double, 2>> texels;

            for (const std::array<double, 2> &corner : kept)
            {
                const Point2 place = turned(middle, corner[0], -34.0, turn);
                const double share = (corner[0] - low) / (high - low);
                points.push_back({place[0], place[1], ground + corner[1]});
                texels.push_back({picture[0] * (mirrored ? 1.0 - share : share),
                    picture[1] - corner[1] * picture[1] / height});
            }

            builder.addFace(points, door, texels, m_event);
        };

        // `leaves: 2`: a double door, the picture once on each half, mirrored on the right (a castle gate's wings).
        if (numberOr(node, "leaves", 1.0) >= 2.0)
        {
            leafFace(-width * 0.5, 0.0, false);
            leafFace(0.0, width * 0.5, true);
        }
        else
        {
            leafFace(-width * 0.5, width * 0.5, false);
        }

        markUsed(doorFrom);
    }

    // ---- Batch O-F: landmarks (portals, free-standing arches, stone rings, walkways, decks, tents, arcades) ----

    // A face turned to look along `normal`, its event the thing's.
    int facing(OutdoorModelBuilder &builder, const std::vector<OutdoorModelPoint> &points,
        const std::array<double, 3> &normal, const std::string &texture, uint16_t event)
    {
        return builder.addSurface(outdoorFacing(points, normal), texture, event);
    }

    // Four corners as one face when they lie in a plane, else as two triangles (a sloping deck's piece at a bend, a
    // skirt's corner): each looks along `normal`.
    void quad(OutdoorModelBuilder &builder, const OutdoorModelPoint &a, const OutdoorModelPoint &b,
        const OutdoorModelPoint &c, const OutdoorModelPoint &d, const std::array<double, 3> &normal,
        const std::string &texture, uint16_t event)
    {
        const std::array<double, 3> u = {b[0] - a[0], b[1] - a[1], b[2] - a[2]};
        const std::array<double, 3> v = {c[0] - a[0], c[1] - a[1], c[2] - a[2]};
        const std::array<double, 3> n = {u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]};
        const double length = oy::hypot(n[0], n[1], n[2]);
        const double off = length > 1.0e-9 ? std::fabs((d[0] - a[0]) * n[0] + (d[1] - a[1]) * n[1]
            + (d[2] - a[2]) * n[2]) / length : 0.0;

        if (off < 0.5)
        {
            facing(builder, {a, b, c, d}, normal, texture, event);
            return;
        }

        facing(builder, {a, b, c}, normal, texture, event);
        facing(builder, {a, c, d}, normal, texture, event);
    }

    // A round column: a square base block, a shaft of `sides` faces, a square capital (Kriegspire's Temple of Baa
    // portico, outb1 PT07: bases and capitals 64 square and 32 high, shafts of eight sides 48 across, 256 high).
    void addColumn(OutdoorModelBuilder &builder, const Point2 &middle, double radius, int sides, double low,
        double high, const Point2 &base, const Point2 &capital, const std::string &shaft, const std::string &block,
        uint16_t event, double turn)
    {
        double shaftLow = low;
        double shaftHigh = high;

        if (base[0] > 0.0 && base[1] > 0.0)
        {
            builder.addPrism(turnedBox(middle, base[0], base[0], turn), low, low + base[1], block, block, "", event);
            shaftLow = low + base[1];
        }

        if (capital[0] > 0.0 && capital[1] > 0.0)
        {
            builder.addPrism(turnedBox(middle, capital[0], capital[0], turn), high - capital[1], high, block, block,
                block, event);
            shaftHigh = high - capital[1];
        }

        builder.addPrism(ringOf(middle, radius, sides, turn), shaftLow, shaftHigh, shaft, "", "", event);
    }

    // `angles`: the places round a middle in degrees clockwise from south (a stone ring's trilithons, an arch's
    // ribs), in place of `count` (or `ribs`) evenly spaced from `turn`. Empty when left out; false when not 1 to 32
    // numbers.
    bool anglesOf(const YAML::Node &node, std::vector<double> &angles)
    {
        const YAML::Node list = childOf(node, "angles");

        for (size_t index = 0; list.IsDefined() && list.IsSequence() && index < list.size(); ++index)
        {
            double angle = 0.0;

            if (!numberOfNode(list[index], angle) || angle < -360.0 || angle > 360.0)
            {
                return false;
            }

            angles.push_back(angle);
        }

        return !list.IsDefined() || (list.IsSequence() && list.size() >= 1 && list.size() <= 32);
    }

    // `[a, b]` of two numbers, or a default when left out; false when given and not two numbers.
    bool pairOr(const YAML::Node &node, const char *pKey, Point2 &pair)
    {
        const YAML::Node value = childOf(node, pKey);
        return !value.IsDefined() || pointOf(value, pair);
    }

    // `kind: portal`: the Planes' gates (gw_fire_N, gw_water_N, gw_air_S, gw_earth_N: 58 faces each): an upright
    // ring of `sides` round a membrane, `radius` to the ring's inside, `ring` wide and `depth` thick, standing on an
    // eight-sided dais (`dais: {size, height, cut, skirt}`, or `false`) with an upright rim and a skirt sloping to
    // the land. The membrane's picture moves (`flow`, right as the originals: the FlowRight bit); every face runs the
    // event (`into`), the membrane is its used part (`hint` on the rest). It spans east to west, looking south, when
    // not turned.
    void raisePortal(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        const double turn = numberOr(node, "turn", 0.0);
        const double radius = numberOr(node, "radius", 128.0);
        const double ring = numberOr(node, "ring", 32.0);
        const double depth = numberOr(node, "depth", 32.0);
        const double sidesNumber = numberOr(node, "sides", 12.0);
        const std::string flow = textOf(node, "flow", "right");

        if (radius < 32.0 || radius > 2048.0 || ring < 8.0 || ring > 512.0 || depth < 16.0 || depth > 512.0
            || sidesNumber < 6.0 || sidesNumber > 16.0 || sidesNumber != std::floor(sidesNumber)
            || (flow != "none" && outdoorLiquidBits("", flow, m_lowered.styleWorld) == UINT32_MAX))
        {
            add(m_path, "a portal is a ring of 6 to 16 `sides` (12) round a membrane: `radius` to its inside 32 to "
                "2048 (128), `ring` 8 to 512 wide (32), `depth` 16 to 512 thick (32); its membrane's `flow` is none, "
                "up, down, left or right (right, as the Planes' gates)");
            return;
        }

        // The dais: Plane of Fire's gw_fire_N is 384 by 256 with corners cut 128 by 64, 48 high, a rim 16 high over
        // a skirt 64 wide.
        const YAML::Node daisNode = childOf(node, "dais");
        const bool dais = !(daisNode.IsDefined() && daisNode.IsScalar() && daisNode.Scalar() == "false");
        Point2 size = {radius * 3.0, radius * 2.0};
        Point2 cut = {0.0, 0.0};
        double daisHeight = 48.0;
        double skirt = 64.0;

        if (dais)
        {
            if (daisNode.IsDefined() && !daisNode.IsMap())
            {
                add(m_path + ".dais", "a portal's dais is {size: [width, depth], height, cut: [x, y], skirt}, or "
                    "false for none");
                return;
            }

            const bool sized = pairOr(daisNode, "size", size);
            cut = {size[0] / 3.0, size[1] / 4.0};
            daisHeight = numberOr(daisNode, "height", 48.0);
            skirt = numberOr(daisNode, "skirt", 64.0);

            if (!sized || !pairOr(daisNode, "cut", cut) || size[0] < 64.0 || size[1] < 64.0 || size[0] > 8192.0
                || size[1] > 8192.0 || cut[0] < 0.0 || cut[1] < 0.0 || cut[0] * 2.0 >= size[0]
                || cut[1] * 2.0 >= size[1] || daisHeight < 16.0 || daisHeight > 1024.0 || skirt < 0.0
                || skirt > 1024.0)
            {
                add(m_path + ".dais", "a portal's dais is `size: [width, depth]` 64 to 8192 each (three and two "
                    "radii), its corners `cut: [x, y]` (less than half each), 16 to 1024 high (48), a sloping "
                    "`skirt` 0 to 1024 wide round it (64)");
                return;
            }
        }

        const std::string frame = textureOf(node, "frame", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string top = textureOf(node, "dais", frame.c_str());
        const std::string membrane = textureOf(node, "membrane", m_pLook != nullptr ? m_pLook->pWater : nullptr);

        // A membrane named plainly (or left out) moves by `flow`; one given as a liquid entry says its own flow.
        const YAML::Node membraneNode = childOf(childOf(node, "textures"), "membrane");

        if (flow != "none" && (!membraneNode.IsDefined() || membraneNode.IsScalar()))
        {
            m_liquidTextures[membrane] |= outdoorLiquidBits("", flow, m_lowered.styleWorld);
        }

        const auto at = [&](double east, double north, double z) -> OutdoorModelPoint
        {
            const Point2 point = turned(middle, east, north, turn);
            return {point[0], point[1], z};
        };
        const auto direction = [&](double east, double north, double up) -> std::array<double, 3>
        {
            const Point2 point = turned({0.0, 0.0}, east, north, turn);
            return {point[0], point[1], up};
        };
        double floor = ground;

        if (dais)
        {
            const double w = size[0] * 0.5;
            const double d = size[1] * 0.5;
            const std::vector<Point2> local = {{w, -(d - cut[1])}, {w, d - cut[1]}, {w - cut[0], d}, {-(w - cut[0]), d},
                {-w, d - cut[1]}, {-w, -(d - cut[1])}, {-(w - cut[0]), -d}, {w - cut[0], -d}};
            std::vector<Point2> outline;

            for (const Point2 &point : local)
            {
                outline.push_back(turned(middle, point[0], point[1], turn));
            }

            const double rim = std::min(16.0, daisHeight);
            const double shoulder = ground + daisHeight - rim;
            builder.addPrism(outline, shoulder, ground + daisHeight, frame, top, "", m_event);

            if (skirt > 0.0 && shoulder > ground)
            {
                // Each side moved out by the skirt: a quad where it stays parallel, else two triangles.
                for (size_t index = 0; index < local.size(); ++index)
                {
                    const Point2 &a = local[index];
                    const Point2 &b = local[(index + 1) % local.size()];
                    const double length = lengthOf(a, b);
                    const Point2 out = {(b[1] - a[1]) / length, -(b[0] - a[0]) / length};
                    const OutdoorModelPoint lowA = at(a[0] + out[0] * skirt, a[1] + out[1] * skirt, ground);
                    const OutdoorModelPoint lowB = at(b[0] + out[0] * skirt, b[1] + out[1] * skirt, ground);
                    const std::array<double, 3> normal = direction(out[0] * (shoulder - ground), out[1]
                        * (shoulder - ground), skirt);
                    facing(builder, {at(a[0], a[1], shoulder), lowA, lowB, at(b[0], b[1], shoulder)}, normal, top,
                        m_event);
                    // The corner to the next side's skirt.
                    const Point2 &c = local[(index + 2) % local.size()];
                    const double nextLength = lengthOf(b, c);
                    const Point2 nextOut = {(c[1] - b[1]) / nextLength, -(c[0] - b[0]) / nextLength};
                    const OutdoorModelPoint nextLow = at(b[0] + nextOut[0] * skirt, b[1] + nextOut[1] * skirt,
                        ground);
                    const Point2 between = {out[0] + nextOut[0], out[1] + nextOut[1]};
                    facing(builder, {at(b[0], b[1], shoulder), lowB, nextLow}, direction(between[0], between[1],
                        1.0), top, m_event);
                }
            }

            floor = ground + daisHeight;
        }

        // The ring: inside and outside `sides`-gons about the membrane's middle, the outside cut level where it
        // would go below the dais (the ring's foot stands on it).
        const int sides = static_cast<int>(sidesNumber);
        const double centre = floor + ring * 0.5 + radius;
        const double half = depth * 0.5;
        std::vector<Point2> inner;
        std::vector<Point2> outer;
        std::vector<bool> cutLevel;

        for (int side = 0; side < sides; ++side)
        {
            const double angle = 2.0 * Pi * side / sides;
            inner.push_back({radius * oy::cos(angle), centre + radius * oy::sin(angle)});
            const double z = centre + (radius + ring) * oy::sin(angle);
            outer.push_back({(radius + ring) * oy::cos(angle), std::max(z, floor)});
            cutLevel.push_back(z < floor);
        }

        const std::array<double, 3> north = direction(0.0, 1.0, 0.0);
        const std::array<double, 3> south = direction(0.0, -1.0, 0.0);

        for (int side = 0; side < sides; ++side)
        {
            const int next = (side + 1) % sides;

            for (const double y : {half, -half})
            {
                facing(builder, {at(inner[side][0], y, inner[side][1]), at(inner[next][0], y, inner[next][1]),
                    at(outer[next][0], y, outer[next][1]), at(outer[side][0], y, outer[side][1])},
                    y > 0.0 ? north : south, frame, m_event);
            }

            if (cutLevel[side] && cutLevel[next])
            {
                // Standing on the dais: no face under it.
                continue;
            }

            const double middleAngle = 2.0 * Pi * (side + 0.5) / sides;
            facing(builder, {at(outer[side][0], half, outer[side][1]), at(outer[next][0], half, outer[next][1]),
                at(outer[next][0], -half, outer[next][1]), at(outer[side][0], -half, outer[side][1])},
                direction(oy::cos(middleAngle), 0.0, oy::sin(middleAngle)), frame, m_event);
        }

        // The membrane: both sides, its used part.
        for (const double y : {half, -half})
        {
            std::vector<OutdoorModelPoint> points;

            for (const Point2 &point : inner)
            {
                points.push_back(at(point[0], y, point[1]));
            }

            const int face = facing(builder, points, y > 0.0 ? north : south, membrane, m_event);

            if (face >= 0)
            {
                m_usedFaces.insert(static_cast<size_t>(face));
            }
        }
    }

    // A beam of `width` across and `depth` deep swept along a curve in an upright plane: points along the beam's
    // middle (plane position, height) and the plane's direction; each step four faces, the ends left open (they
    // stand in the land or in a hub).
    void sweepBeam(OutdoorModelBuilder &builder, const Point2 &origin, const Point2 &along,
        const std::vector<Point2> &curve, double width, double depth, const std::string &texture,
        const std::string &under, uint16_t event, bool upright = false)
    {
        const Point2 side = {-along[1], along[0]};
        const auto world = [&](double s, double z, double across) -> OutdoorModelPoint
        {
            return {origin[0] + along[0] * s + side[0] * across, origin[1] + along[1] * s + side[1] * across, z};
        };
        std::vector<Point2> normals;

        for (size_t index = 0; index < curve.size(); ++index)
        {
            const Point2 &before = curve[index == 0 ? 0 : index - 1];
            const Point2 &after = curve[index + 1 == curve.size() ? index : index + 1];
            const double ds = after[0] - before[0];
            const double dz = after[1] - before[1];
            const double length = std::max(oy::hypot(ds, dz), 1.0e-9);
            // The beam's outside: up and away from the curve's inside (to the left of its way); an `upright`
            // beam's section stands plumb (its depth measured straight up, as Bracada's ribs).
            normals.push_back(upright ? Point2{0.0, 1.0} : Point2{-dz / length, ds / length});
        }

        for (size_t index = 0; index + 1 < curve.size(); ++index)
        {
            const Point2 &a = curve[index];
            const Point2 &b = curve[index + 1];
            const Point2 &na = normals[index];
            const Point2 &nb = normals[index + 1];
            const double h = depth * 0.5;
            const double w = width * 0.5;
            const Point2 oa = {a[0] + na[0] * h, a[1] + na[1] * h};
            const Point2 ob = {b[0] + nb[0] * h, b[1] + nb[1] * h};
            const Point2 ia = {a[0] - na[0] * h, a[1] - na[1] * h};
            const Point2 ib = {b[0] - nb[0] * h, b[1] - nb[1] * h};
            const Point2 n = {(na[0] + nb[0]) * 0.5, (na[1] + nb[1]) * 0.5};
            const Point2 slope = {b[0] - a[0], b[1] - a[1]};
            // Square to the beam's way, on the outside of the curve.
            const Point2 square = {-slope[1], slope[0]};
            const Point2 out = square[0] * n[0] + square[1] * n[1] >= 0.0 ? square : Point2{-square[0], -square[1]};
            const std::array<double, 3> outward = {along[0] * out[0], along[1] * out[0], out[1]};
            const std::array<double, 3> inward = {-outward[0], -outward[1], -outward[2]};
            quad(builder, world(oa[0], oa[1], -w), world(ob[0], ob[1], -w), world(ob[0], ob[1], w),
                world(oa[0], oa[1], w), outward, texture, event);
            quad(builder, world(ia[0], ia[1], -w), world(ib[0], ib[1], -w), world(ib[0], ib[1], w),
                world(ia[0], ia[1], w), inward, under, event);

            for (const double across : {-w, w})
            {
                facing(builder, {world(oa[0], oa[1], across), world(ob[0], ob[1], across),
                    world(ib[0], ib[1], across), world(ia[0], ia[1], across)},
                    {side[0] * across, side[1] * across, 0.0}, texture, event);
            }
        }
    }

    // `kind: arch`: a free-standing arch, a curved beam `width` across and `depth` deep from foot to foot along
    // `line` (two points) rising to `height` (the beam's top) in `segments` steps; or with `ribs: n` (and `at`,
    // `radius` to the feet, `turn` the first rib's way, south when 0) n half arches rising from feet round a middle
    // to a hub at the top: Bracada's Celeste teleporter (7out06 heavenTele_S: three ribs 45 across meeting 360 up).
    void raiseArch(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        const double height = numberOr(node, "height", 512.0);
        const double width = numberOr(node, "width", 48.0);
        const double depth = numberOr(node, "depth", 32.0);
        const double segmentsNumber = numberOr(node, "segments", 8.0);
        const double ribsNumber = numberOr(node, "ribs", 0.0);
        const std::string texture = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string under = textureOf(node, "under", texture.c_str());

        if (height < 64.0 || height > 8192.0 || width < 8.0 || width > 1024.0 || depth < 8.0
            || depth > height * 0.5 || segmentsNumber < 2.0 || segmentsNumber > 24.0
            || segmentsNumber != std::floor(segmentsNumber) || ribsNumber < 0.0 || ribsNumber > 12.0
            || ribsNumber != std::floor(ribsNumber) || ribsNumber == 1.0 || ribsNumber == 2.0)
        {
            add(m_path, "an arch rises to `height` 64 to 8192 (512), a beam `width` 8 to 1024 across (48) and "
                "`depth` deep (8 to half the height; 32), in 2 to 24 `segments` (8); `ribs` 3 to 12 for half arches "
                "round a middle (two ribs are one arch: give `line`)");
            return;
        }

        const int segments = static_cast<int>(segmentsNumber);
        std::vector<double> ribAngles;

        if (!anglesOf(node, ribAngles) || (!ribAngles.empty() && (ribAngles.size() < 3 || ribsNumber != 0.0)))
        {
            add(m_path + ".angles", "an arch's `angles` are its ribs' ways, 3 to 12 numbers in degrees clockwise from "
                "south, in place of `ribs`");
            return;
        }

        const int ribs = ribAngles.empty() ? static_cast<int>(ribsNumber) : static_cast<int>(ribAngles.size());

        if (ribs == 0)
        {
            std::vector<Point2> line;

            if (!lineOf(node, line))
            {
                return;
            }

            if (line.size() != 2)
            {
                add(m_path + ".line", "an arch's `line` is its two feet");
                return;
            }

            const double span = lengthOf(line[0], line[1]);
            const Point2 along = {(line[1][0] - line[0][0]) / span, (line[1][1] - line[0][1]) / span};
            const double ground = std::min(groundAt(line[0]), groundAt(line[1])) + numberOr(node, "raise", 0.0);
            // Half an ellipse through the beam's middle: the feet `span` apart, its top `height - depth / 2` up.
            std::vector<Point2> curve;

            for (int step = 0; step <= segments; ++step)
            {
                const double angle = Pi * step / segments;
                curve.push_back({span * 0.5 * (1.0 - oy::cos(angle)), ground + (height - depth * 0.5)
                    * oy::sin(angle)});
            }

            sweepBeam(builder, line[0], along, curve, width, depth, texture, under, m_event);
            return;
        }

        Point2 middle = {0.0, 0.0};
        double ground = 0.0;

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        const double radius = numberOr(node, "radius", 512.0);
        const double turn = numberOr(node, "turn", 0.0);
        // The hub: a block round the middle at the top that the ribs end in.
        const int hubSides = std::max(6, ribs * 2);
        const double hub = numberOr(node, "hub", width * 1.5);
        const double bow = numberOr(node, "curve", 2.0);

        if (radius < hub + width || radius > 8192.0 || hub < width * 0.5 || hub > 1024.0 || bow < 1.0 || bow > 4.0)
        {
            add(m_path, "an arch of ribs has its feet `radius` (more than the `hub` and a width; 512) from its "
                "middle, a `hub` at the top (half a width to 1024; one and a half widths), and rises as 1 - (1 - u) "
                "to the `curve` (1 straight to 4; 2 a parabola)");
            return;
        }

        for (int rib = 0; rib < ribs; ++rib)
        {
            // The first rib runs south from the middle when not turned.
            const double angle = ribAngles.empty() ? -Pi * 0.5 - turn * Pi / 180.0 + 2.0 * Pi * rib / ribs
                : -Pi * 0.5 - ribAngles[static_cast<size_t>(rib)] * Pi / 180.0;
            const Point2 out = {oy::cos(angle), oy::sin(angle)};
            const Point2 foot = {middle[0] + out[0] * radius, middle[1] + out[1] * radius};
            const double footGround = groundAt(foot) + numberOr(node, "raise", 0.0);
            std::vector<Point2> curve;

            for (int step = 0; step <= segments; ++step)
            {
                // Rising from the foot as 1 - (1 - u)^curve (2: a parabola; Bracada's ribs 1.6), level at the hub.
                const double u = static_cast<double>(step) / segments;
                curve.push_back({(radius - hub) * u, footGround + depth * 0.5 + (ground + height - depth
                    - footGround) * (1.0 - oy::pow(1.0 - u, bow))});
            }

            sweepBeam(builder, foot, {-out[0], -out[1]}, curve, width, depth, texture, under, m_event, true);
        }

        builder.addPrism(ringOf(middle, (hub + width) / oy::cos(Pi / hubSides), hubSides, turn),
            ground + height - depth, ground + height, texture, texture, under, m_event);
    }

    // `kind: stone_ring` and `kind: trilithon`: Avlee's and Evenmorn's stonehenges (out14 Stone_ and Stone__1, out09
    // Stone_: uprights 96 to 128 by 64 to 96, 256 high, lintels 64 to 80 thick over pairs, an altar with water in the
    // middle). `count` trilithons round a circle of `radius` (each two uprights `gap` apart under a lintel; `lintel:
    // false` for standing stones alone: Evenmorn's CircleRocks_), the stones `stone: [width, depth, height]`, an
    // `altar: [width, depth, height]` in the middle (its used part); `seed` turns and sizes each stone a little.
    // A trilithon is one of them at `at`, its opening looking south when not turned.
    void raiseStoneRing(const YAML::Node &node, OutdoorModelBuilder &builder, bool single)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        std::vector<double> places;

        if (!anglesOf(node, places) || (single && !places.empty()))
        {
            add(m_path + ".angles", "a stone ring's `angles` are its trilithons' (or stones') places round it, 1 to 32 "
                "numbers in degrees clockwise from south, in place of `count`");
            return;
        }

        const double count = single ? 1.0 : places.empty() ? numberOr(node, "count", 5.0)
            : static_cast<double>(places.size());
        const double radius = single ? 0.0 : numberOr(node, "radius", 384.0);
        const double turn = numberOr(node, "turn", 0.0);
        const YAML::Node stoneNode = childOf(node, "stone");
        const YAML::Node lintelNode = childOf(node, "lintel");
        const bool lintels = !(lintelNode.IsDefined() && lintelNode.IsScalar() && lintelNode.Scalar() == "false");
        std::array<double, 3> stone = {112.0, 80.0, 256.0};
        Point2 lintel = {72.0, 32.0};
        bool good = count >= 1.0 && count <= 32.0 && count == std::floor(count) && (single || (radius >= 64.0
            && radius <= 8192.0));

        if (stoneNode.IsDefined())
        {
            good = good && stoneNode.IsSequence() && stoneNode.size() == 3 && numberOfNode(stoneNode[0], stone[0])
                && numberOfNode(stoneNode[1], stone[1]) && numberOfNode(stoneNode[2], stone[2]);
        }

        if (lintels && lintelNode.IsDefined())
        {
            good = good && pointOf(lintelNode, lintel);
        }

        const double gap = numberOr(node, "gap", stone[0]);
        good = good && stone[0] >= 16.0 && stone[1] >= 16.0 && stone[2] >= 32.0 && stone[0] <= 1024.0
            && stone[1] <= 1024.0 && stone[2] <= 4096.0 && lintel[0] >= 8.0 && lintel[0] <= 512.0 && lintel[1] >= 0.0
            && lintel[1] <= 256.0 && gap >= 0.0 && gap <= 2048.0;

        if (!good)
        {
            add(m_path, std::string(single ? "a trilithon" : "a stone ring") + " has `stone: [width, depth, "
                "height]` (16 to 1024, 16 to 1024, 32 to 4096; [112, 80, 256]), uprights `gap` apart (0 to 2048; a "
                "stone's width), `lintel: [height, overhang]` (8 to 512, 0 to 256; [72, 32]) or `lintel: false`"
                + std::string(single ? "" : ", `count` 1 to 32 of them (5) round a `radius` of 64 to 8192 (384)"));
            return;
        }

        const std::string texture = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string topTexture = textureOf(node, "top", texture.c_str());
        const std::string lintelTexture = textureOf(node, "lintel", texture.c_str());
        // A stone's own small turn and height from the seed (none without one).
        uint32_t state = static_cast<uint32_t>(numberOr(node, "seed", 0.0));
        const bool rough = childOf(node, "seed").IsDefined();
        const auto next = [&state]()
        {
            state = state * 1664525u + 1013904223u;
            return static_cast<double>((state >> 8) & 0xffff) / 65535.0;
        };
        const int pieces = static_cast<int>(count);

        for (int piece = 0; piece < pieces; ++piece)
        {
            // The piece's place round the ring; it faces the middle (its opening looks out). The first stands south
            // of the middle when not turned.
            const double angle = places.empty() ? turn + 360.0 * piece / pieces
                : places[static_cast<size_t>(piece)];
            const Point2 place = turned(middle, 0.0, -radius, angle);
            const double placeGround = single ? ground : groundAt(place) + numberOr(node, "raise", 0.0);
            const double tilt = rough ? (next() - 0.5) * 12.0 : 0.0;
            const double taller = rough ? std::round((next() - 0.5) * 0.12 * stone[2]) : 0.0;
            const double high = placeGround + stone[2] + (lintels ? 0.0 : taller);

            if (!lintels)
            {
                builder.addPrism(turnedBox(place, stone[0], stone[1], angle + tilt), placeGround - 32.0, high,
                    texture, topTexture, "", m_event);
                continue;
            }

            const double offset = (gap + stone[0]) * 0.5;

            for (const double side : {-offset, offset})
            {
                builder.addPrism(turnedBox(turned(place, side, 0.0, angle), stone[0], stone[1], angle),
                    placeGround - 32.0, high, texture, "", "", m_event);
            }

            builder.addPrism(turnedBox(place, gap + stone[0] * 2.0 + lintel[1] * 2.0, stone[1], angle), high,
                high + lintel[0], lintelTexture, topTexture, lintelTexture, m_event);
        }

        const YAML::Node altarNode = childOf(node, "altar");

        if (!single && altarNode.IsDefined())
        {
            std::array<double, 3> altar = {160.0, 160.0, 112.0};

            if (!altarNode.IsSequence() || altarNode.size() != 3 || !numberOfNode(altarNode[0], altar[0])
                || !numberOfNode(altarNode[1], altar[1]) || !numberOfNode(altarNode[2], altar[2]) || altar[0] < 16.0
                || altar[1] < 16.0 || altar[2] < 8.0 || altar[0] > 2048.0 || altar[1] > 2048.0 || altar[2] > 1024.0
                || std::max(altar[0], altar[1]) > radius * 1.5)
            {
                add(m_path + ".altar", "a stone ring's altar is [width, depth, height] in its middle (16 to 2048, 16 "
                    "to 2048, 8 to 1024; inside the ring)");
                return;
            }

            const size_t from = faceCount();
            const std::string altarTexture = textureOf(node, "altar", texture.c_str());
            builder.addPrism(turnedBox(middle, altar[0], altar[1], turn), ground - 32.0, ground + altar[2],
                altarTexture, textureOf(node, "altar_top", altarTexture.c_str()), "", m_event);
            markUsed(from);
        }
    }

    // A raised way's points: [x, y] in cells with the deck's top `height` over the land there, or [x, y, z] with
    // the deck's top at z (map units).
    bool deckLineOf(const YAML::Node &node, double height, std::vector<Point2> &line, std::vector<double> &tops)
    {
        const YAML::Node points = childOf(node, "line");

        for (size_t index = 0; points.IsDefined() && points.IsSequence() && index < points.size(); ++index)
        {
            const YAML::Node point = points[index];
            Point2 cell = {0.0, 0.0};
            double z = 0.0;

            if (!point.IsSequence() || (point.size() != 2 && point.size() != 3) || !numberOfNode(point[0], cell[0])
                || !numberOfNode(point[1], cell[1]) || (point.size() == 3 && !numberOfNode(point[2], z))
                || cell[0] < 0.0 || cell[1] < 0.0 || cell[0] > OutdoorNodeCount - 1 || cell[1] > OutdoorNodeCount - 1)
            {
                line.clear();
                break;
            }

            line.push_back(toWorld(cell));
            tops.push_back(point.size() == 3 ? z : groundAt(line.back()) + height);
        }

        for (size_t index = 0; index + 1 < line.size(); ++index)
        {
            if (lengthOf(line[index], line[index + 1]) < 64.0
                || std::fabs(tops[index + 1] - tops[index]) > lengthOf(line[index], line[index + 1]))
            {
                line.clear();
            }
        }

        if (line.size() < 2)
        {
            add(m_path + ".line", "a walkway's `line` is two or more points [x, y] in cells (the deck `height` over "
                "the land there) or [x, y, z] (the deck's top at z), at least 64 apart, rising at most 45 degrees");
            return false;
        }

        return true;
    }

    // `kind: walkway`: Barrow Downs' raised timber walkways (out11 BS-1712/BP-1712/BC-*: a deck 512 wide, its floor
    // 32 over its underside, kerbs 16 wide rising 80 over the floor; piers of two eight-sided posts beside the deck
    // every 1536 and at the bends, reaching 128 over the kerbs, down to the valley floor). Along `line` with a
    // height per point; `width`, `thickness`, `kerb` (its height, 0 none) and `kerb_width`, `pier_every`, `pier_radius`,
    // `pier_above` (`piers: 0` none), `ends: frame` a timber gate frame `frame_height` high over each end (the walkways'
    // TestendPiece frames).
    void raiseWalkway(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        std::vector<Point2> line;
        std::vector<double> tops;

        if (!deckLineOf(node, numberOr(node, "height", 256.0), line, tops))
        {
            return;
        }

        const double width = numberOr(node, "width", 512.0);
        const double thickness = numberOr(node, "thickness", 32.0);
        const Point2 kerb = {numberOr(node, "kerb_width", 16.0), numberOr(node, "kerb", 80.0)};
        const bool kerbed = kerb[1] != 0.0;
        const bool piered = numberOr(node, "piers", 1.0) != 0.0;
        const double every = numberOr(node, "pier_every", 1536.0);
        const double postRadius = numberOr(node, "pier_radius", 56.0);
        const double above = numberOr(node, "pier_above", 128.0);
        // `ends`: open or frame for both ends, or [first, last].
        const YAML::Node endsNode = childOf(node, "ends");
        std::string ends = textOf(node, "ends", "open");
        std::string lastEnd = ends;

        if (endsNode.IsDefined() && endsNode.IsSequence())
        {
            const bool pair = endsNode.size() == 2 && endsNode[0].IsScalar() && endsNode[1].IsScalar();
            ends = pair ? endsNode[0].Scalar() : "?";
            lastEnd = pair ? endsNode[1].Scalar() : "?";
        }

        if ((kerbed && (kerb[0] < 4.0 || kerb[0] * 4.0 > width || kerb[1] < 8.0 || kerb[1] > 512.0)) || width < 64.0 || width > 2048.0 || thickness < 8.0 || thickness > 256.0
            || every < 256.0
            || every > 16384.0 || postRadius < 8.0 || postRadius > 256.0 || above < 0.0 || above > 1024.0
            || (ends != "open" && ends != "frame") || (lastEnd != "open" && lastEnd != "frame"))
        {
            add(m_path, "a walkway is `width` 64 to 2048 (512) and `thickness` 8 to 256 (32), with kerbs `kerb` 8 to "
                "512 high (80; 0 for none) and `kerb_width` 4 to a quarter of the width (16), piers every `pier_every` "
                "256 to 16384 (1536) of two posts `pier_radius` 8 to 256 (56) reaching `pier_above` 0 to 1024 over the "
                "kerbs (128) or `piers: 0`, and `ends` open or frame (or [first, last])");
            return;
        }

        const std::string deck = textureOf(node, "top", m_pLook != nullptr ? m_pLook->pWood : nullptr);
        const std::string side = textureOf(node, "wall", deck.c_str());
        const std::string under = textureOf(node, "under", deck.c_str());
        const std::string post = textureOf(node, "post", side.c_str());
        const double kerbWidth = kerbed ? kerb[0] : 0.0;
        const double kerbHeight = kerbed ? kerb[1] : 0.0;
        std::vector<Point2> outerLeft;
        std::vector<Point2> outerRight;
        std::vector<Point2> innerLeft;
        std::vector<Point2> innerRight;
        sidesOf(line, false, width * 0.5, outerLeft, outerRight);
        sidesOf(line, false, width * 0.5 - kerbWidth, innerLeft, innerRight);
        const auto p = [](const Point2 &point, double z) -> OutdoorModelPoint
        {
            return {point[0], point[1], z};
        };
        const size_t from = faceCount();

        for (size_t index = 0; index + 1 < line.size(); ++index)
        {
            const size_t next = index + 1;
            const double a = tops[index];
            const double b = tops[next];
            const double length = lengthOf(line[index], line[next]);
            const Point2 along = {(line[next][0] - line[index][0]) / length, (line[next][1] - line[index][1]) / length};
            const std::array<double, 3> left = {-along[1], along[0], 0.0};
            const std::array<double, 3> right = {along[1], -along[0], 0.0};
            const std::array<double, 3> up = {0.0, 0.0, 1.0};
            const std::array<double, 3> down = {0.0, 0.0, -1.0};
            // The floor between the kerbs (the used part), the underside, the outer sides up to the kerbs' top,
            // the kerbs' inner sides and tops.
            quad(builder, p(innerRight[index], a), p(innerRight[next], b), p(innerLeft[next], b),
                p(innerLeft[index], a), up, deck, m_event);
            quad(builder, p(outerRight[index], a - thickness), p(outerRight[next], b - thickness),
                p(outerLeft[next], b - thickness), p(outerLeft[index], a - thickness), down, under, m_event);
            quad(builder, p(outerLeft[index], a - thickness), p(outerLeft[next], b - thickness),
                p(outerLeft[next], b + kerbHeight), p(outerLeft[index], a + kerbHeight), left, side, m_event);
            quad(builder, p(outerRight[index], a - thickness), p(outerRight[next], b - thickness),
                p(outerRight[next], b + kerbHeight), p(outerRight[index], a + kerbHeight), right, side, m_event);

            if (kerbed)
            {
                quad(builder, p(innerLeft[index], a), p(innerLeft[next], b), p(innerLeft[next], b + kerbHeight),
                    p(innerLeft[index], a + kerbHeight), right, side, m_event);
                quad(builder, p(innerRight[index], a), p(innerRight[next], b), p(innerRight[next], b + kerbHeight),
                    p(innerRight[index], a + kerbHeight), left, side, m_event);
                quad(builder, p(outerLeft[index], a + kerbHeight), p(outerLeft[next], b + kerbHeight),
                    p(innerLeft[next], b + kerbHeight), p(innerLeft[index], a + kerbHeight), up, side, m_event);
                quad(builder, p(innerRight[index], a + kerbHeight), p(innerRight[next], b + kerbHeight),
                    p(outerRight[next], b + kerbHeight), p(outerRight[index], a + kerbHeight), up, side, m_event);
            }
        }

        // The ends: the deck's edge, and the kerbs' ends.
        for (const size_t end : {size_t{0}, line.size() - 1})
        {
            const size_t other = end == 0 ? 1 : line.size() - 2;
            const double length = lengthOf(line[other], line[end]);
            const std::array<double, 3> out = {(line[end][0] - line[other][0]) / length,
                (line[end][1] - line[other][1]) / length, 0.0};
            const double z = tops[end];
            const int endFace = facing(builder, {p(outerLeft[end], z - thickness), p(outerRight[end], z - thickness),
                p(outerRight[end], z), p(outerLeft[end], z)}, out, side, m_event);

            if (kerbed)
            {
                facing(builder, {p(outerLeft[end], z), p(innerLeft[end], z), p(innerLeft[end], z + kerbHeight),
                    p(outerLeft[end], z + kerbHeight)}, out, side, m_event);
                facing(builder, {p(innerRight[end], z), p(outerRight[end], z), p(outerRight[end], z + kerbHeight),
                    p(innerRight[end], z + kerbHeight)}, out, side, m_event);
            }

            if ((end == 0 ? ends : lastEnd) == "frame")
            {
                // Barrow Downs' end pieces (out11 TestendPiece*): two eight-sided posts on the deck's edges at its
                // end, `frame_height` over the deck, a beam across their tops, and steps down to the land beyond
                // when it lies up to 256 under the deck (rises of at most 32, treads 48 deep; a hidden slope over
                // them is walked, as the shipped stairs').
                const double frameHeight = numberOr(node, "frame_height", 512.0);
                const double radius = postRadius;
                const Point2 inward = {-out[0], -out[1]};
                const double angle = oy::atan2(out[0], out[1]) * 180.0 / Pi;
                std::vector<Point2> postCentres;

                for (const bool leftSide : {true, false})
                {
                    const Point2 &corner = leftSide ? outerLeft[end] : outerRight[end];
                    const Point2 centre = {corner[0] + inward[0] * radius, corner[1] + inward[1] * radius};
                    builder.addPrism(ringOf(centre, radius, 8), std::min(groundAt(centre), z - thickness) - 32.0,
                        z + frameHeight, post, "", "", m_event);
                    postCentres.push_back(centre);
                }

                const Point2 beamMiddle = {(postCentres[0][0] + postCentres[1][0]) * 0.5,
                    (postCentres[0][1] + postCentres[1][1]) * 0.5};
                builder.addPrism(turnedBox(beamMiddle, lengthOf(postCentres[0], postCentres[1]) + radius * 4.0,
                    radius * 2.0, -angle), z + frameHeight, z + frameHeight + 64.0, post, post, post, m_event);
                const double tread = 48.0;
                const Point2 beyond = {line[end][0] + out[0] * tread * 2.0, line[end][1] + out[1] * tread * 2.0};
                const double drop = z - groundAt(beyond);

                if (drop > 16.0 && drop <= 256.0)
                {
                    const int steps = static_cast<int>(std::ceil(drop / 32.0));
                    const double rise = drop / steps;
                    const Point2 &left = innerLeft[end];
                    const Point2 &right = innerRight[end];
                    const auto ahead = [&out](const Point2 &point, double distance)
                    {
                        return Point2{point[0] + out[0] * distance, point[1] + out[1] * distance};
                    };
                    const std::array<double, 3> outward = {out[0], out[1], 0.0};
                    const std::array<double, 3> sideLeft = {-out[1], out[0], 0.0};

                    for (int step = 1; step <= steps; ++step)
                    {
                        const double top = z - rise * step;
                        const double near = tread * (step - 1);
                        const double far = tread * step;
                        const double foot = groundAt(ahead(line[end], far)) - 32.0;
                        facing(builder, {p(ahead(left, near), top), p(ahead(right, near), top), p(ahead(right, far), top),
                            p(ahead(left, far), top)}, {0.0, 0.0, 1.0}, deck, m_event);
                        // Its riser from the step above (under the deck's own end for the first), let through.
                        const double riserTop = step == 1 ? std::min(top + rise, z - thickness) : top + rise;

                        if (riserTop > top + 0.5)
                        {
                            builder.letThrough(facing(builder, {p(ahead(left, near), top), p(ahead(right, near), top),
                                p(ahead(right, near), riserTop), p(ahead(left, near), riserTop)}, outward, side,
                                m_event));
                        }

                        for (const bool leftSide : {true, false})
                        {
                            const Point2 &edge = leftSide ? left : right;
                            facing(builder, {p(ahead(edge, near), foot), p(ahead(edge, far), foot),
                                p(ahead(edge, far), top), p(ahead(edge, near), top)}, leftSide ? sideLeft
                                : std::array<double, 3>{-sideLeft[0], -sideLeft[1], 0.0}, side, m_event);
                        }

                        if (step == steps)
                        {
                            facing(builder, {p(ahead(left, far), foot), p(ahead(right, far), foot), p(ahead(right, far),
                                top), p(ahead(left, far), top)}, outward, side, m_event);
                        }
                    }

                    builder.letThrough(endFace);
                    builder.addStepSlope({p(left, z), p(right, z), p(ahead(right, tread * steps), z - drop),
                        p(ahead(left, tread * steps), z - drop)}, deck, m_event);
                }
            }
        }

        markUsed(from);

        if (!piered)
        {
            return;
        }

        // Piers: at every point, and every `every` along each stretch between.
        std::vector<std::pair<Point2, double>> places;
        std::vector<Point2> normals;

        for (size_t index = 0; index < line.size(); ++index)
        {
            const Point2 normal = {(outerLeft[index][0] - line[index][0]) / (width * 0.5),
                (outerLeft[index][1] - line[index][1]) / (width * 0.5)};
            places.push_back({line[index], tops[index]});
            normals.push_back(normal);

            if (index + 1 < line.size())
            {
                const double length = lengthOf(line[index], line[index + 1]);
                const int gaps = static_cast<int>(std::ceil(length / every - 1.0e-6));
                const Point2 along = {(line[index + 1][0] - line[index][0]) / length,
                    (line[index + 1][1] - line[index][1]) / length};

                for (int gap = 1; gap < gaps; ++gap)
                {
                    const double share = static_cast<double>(gap) / gaps;
                    places.push_back({{line[index][0] + (line[index + 1][0] - line[index][0]) * share,
                        line[index][1] + (line[index + 1][1] - line[index][1]) * share},
                        tops[index] + (tops[index + 1] - tops[index]) * share});
                    normals.push_back({-along[1], along[0]});
                }
            }
        }

        for (size_t index = 0; index < places.size(); ++index)
        {
            const double reach = width * 0.5 + postRadius;

            for (const double way : {-1.0, 1.0})
            {
                const Point2 centre = {places[index].first[0] + normals[index][0] * reach * way,
                    places[index].first[1] + normals[index][1] * reach * way};
                builder.addPrism(ringOf(centre, postRadius, 8), groundAt(centre) - 32.0,
                    places[index].second + kerbHeight + above, post, post, "", m_event);
            }
        }
    }

    // `kind: deck`: a level timber deck on posts over the land or water (Pierpont's decks, 7out04 Dock*: planks
    // about 100 over the land, outlines that bend in): `outline` points in cells (counter-clockwise or not, bending
    // in allowed), its top at `level` (map units) or `height` over the land at its first point, `thickness`, square
    // `posts` (their width) at the corners and every `post_every` along the edges. Plots stand on it with `on:
    // <its id>`.
    void raiseDeck(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        std::vector<Point2> outline;
        const YAML::Node points = childOf(node, "outline");

        for (size_t index = 0; points.IsDefined() && points.IsSequence() && index < points.size(); ++index)
        {
            Point2 cell = {0.0, 0.0};

            if (!pointOf(points[index], cell) || cell[0] < 0.0 || cell[1] < 0.0 || cell[0] > OutdoorNodeCount - 1
                || cell[1] > OutdoorNodeCount - 1)
            {
                outline.clear();
                break;
            }

            outline.push_back(toWorld(cell));
        }

        if (outline.size() >= 3 && polygonDoubleArea(outline) < 0.0)
        {
            std::reverse(outline.begin(), outline.end());
        }

        if (outline.size() < 3 || !polygonIsSimple(outline))
        {
            add(m_path + ".outline", "a deck's `outline` is three or more points [x, y] in cells inside the map, its "
                "edges crossing nowhere");
            return;
        }

        const bool levelled = childOf(node, "level").IsDefined();
        const double top = levelled ? numberOr(node, "level", 0.0) : groundAt(outline[0]) + numberOr(node, "height",
            96.0);
        const double thickness = numberOr(node, "thickness", 32.0);
        const double postWidth = numberOr(node, "posts", 32.0);
        const double postEvery = numberOr(node, "post_every", 768.0);
        const std::vector<std::vector<size_t>> pieces = convexPieces(outline, 8);

        if (pieces.empty() || thickness < 8.0 || thickness > 256.0 || (postWidth != 0.0 && (postWidth < 8.0
            || postWidth > 256.0)) || postEvery < 128.0 || postEvery > 8192.0 || top < -1024.0 || top > 16384.0)
        {
            add(m_path, "a deck is `thickness` 8 to 256 thick (32), on square `posts` 8 to 256 wide (32; 0 for "
                "none) at its corners and every `post_every` 128 to 8192 (768) along its edges, its top at `level` "
                "(map units) or `height` over the land at its first point (96)");
            return;
        }

        const std::string planks = textureOf(node, "top", m_pLook != nullptr ? m_pLook->pWood : nullptr);
        const std::string side = textureOf(node, "wall", planks.c_str());
        const std::string under = textureOf(node, "under", planks.c_str());
        const std::string post = textureOf(node, "post", side.c_str());
        const size_t from = faceCount();

        for (const std::vector<size_t> &piece : pieces)
        {
            std::vector<OutdoorModelPoint> upper;
            std::vector<OutdoorModelPoint> lower;

            for (const size_t index : piece)
            {
                upper.push_back({outline[index][0], outline[index][1], top});
                lower.push_back({outline[index][0], outline[index][1], top - thickness});
            }

            facing(builder, upper, {0.0, 0.0, 1.0}, planks, m_event);
            facing(builder, lower, {0.0, 0.0, -1.0}, under, m_event);
        }

        markUsed(from);

        for (size_t index = 0; index < outline.size(); ++index)
        {
            const Point2 &a = outline[index];
            const Point2 &b = outline[(index + 1) % outline.size()];
            const double length = lengthOf(a, b);
            facing(builder, {{a[0], a[1], top - thickness}, {b[0], b[1], top - thickness}, {b[0], b[1], top},
                {a[0], a[1], top}}, {(b[1] - a[1]) / length, -(b[0] - a[0]) / length, 0.0}, side, m_event);
        }

        if (postWidth == 0.0)
        {
            return;
        }

        // Posts inside the edge by half their width: at each corner that turns out and along each edge. Batch O-H:
        // a post that would stand in one already placed is left out (a chamfered corner's two short edges: Erathia's
        // quay heads).
        std::vector<Point2> placed;

        for (size_t index = 0; index < outline.size(); ++index)
        {
            const Point2 &a = outline[index];
            const Point2 &b = outline[(index + 1) % outline.size()];
            const double length = lengthOf(a, b);
            const Point2 along = {(b[0] - a[0]) / length, (b[1] - a[1]) / length};
            const Point2 inward = {-along[1], along[0]};
            const int gaps = std::max(1, static_cast<int>(std::ceil(length / postEvery - 1.0e-6)));
            const double angle = oy::atan2(along[1], along[0]) * 180.0 / Pi;

            for (int gap = 0; gap < gaps; ++gap)
            {
                // Not std::clamp: on an edge shorter than a post (Erathia's quay heads) the bounds cross, which
                // std::clamp leaves undefined (libstdc++ answered the upper, libc++ the lower). The rule: such a
                // post stands at the edge's length less half a post, min(max(v, lo), hi), libstdc++'s answer, which
                // keeps the bytes built before.
                const double s = std::min(std::max(length * gap / gaps, postWidth * 0.5), length - postWidth * 0.5);
                const Point2 centre = {a[0] + along[0] * s + inward[0] * postWidth * 0.5,
                    a[1] + along[1] * s + inward[1] * postWidth * 0.5};

                if (!pointInPolygon(outline, centre, postWidth * 0.25)
                    || std::any_of(placed.begin(), placed.end(), [&](const Point2 &other)
                    { return lengthOf(other, centre) < postWidth * std::sqrt(2.0) + 1.0; }))
                {
                    continue;
                }

                placed.push_back(centre);
                const double foot = groundAt(centre) - 32.0;

                if (foot < top - thickness)
                {
                    builder.addPrism(turnedBox(centre, postWidth, postWidth, -angle), foot, top - thickness, post, "",
                        "", m_event);
                }
            }
        }
    }

    // `kind: tent`: a canvas tent (Alvar's adventurers' camp out03 AdvTents and Ravage Roaming's out05 Tents5and6:
    // canvas walls 288 high leaning in 96 under a low gable rising 96; with `wall_height: 0` an A-frame whose roof
    // comes to the ground): `size: [length, width]` (the ridge runs along the length, south to north when not
    // turned), the walls' `wall_height` and how far they `lean` in at their top, the ridge `height`; the front (south)
    // `open` or closed, an `awning` (its depth) carrying the roof on past the open front on two poles, a pole under
    // each end of the ridge. The canvas is seen both ways (`canvas` out, `inner` in: one face drawn from both sides
    // when they are one picture, else the inner face 2 inward), so the open tent is seen into.
    void raiseTent(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        Point2 middle = {0.0, 0.0};
        double ground = 0.0;
        Point2 size = {512.0, 384.0};

        if (!placeOf(node, middle, ground))
        {
            return;
        }

        const double turn = numberOr(node, "turn", 0.0);
        const double height = numberOr(node, "height", 320.0);
        const double walls = numberOr(node, "wall_height", 0.0);
        const double lean = numberOr(node, "lean", 0.0);
        const double awning = numberOr(node, "awning", 0.0);
        const bool open = textOf(node, "open", "true") != "false";

        if (!pairOr(node, "size", size) || size[0] < 128.0 || size[1] < 128.0 || size[0] > 4096.0
            || size[1] > 4096.0 || walls < 0.0 || walls > 512.0 || height < walls + 32.0 || height > 2048.0
            || lean < 0.0 || lean > std::min(size[0], size[1]) * 0.5 - 32.0 || (walls == 0.0 && lean > 0.0)
            || awning < 0.0 || awning > size[0] || (awning > 0.0 && !open))
        {
            add(m_path, "a tent is `size: [length, width]` 128 to 4096 each ([512, 384]), its walls `wall_height` 0 "
                "to 512 high (0: the roof comes to the ground) leaning in by `lean` at their top (up to half the "
                "width less 32), its ridge `height` 32 over the walls up to 2048 (320), its front `open` (true) with "
                "an `awning` 0 to its length deep on poles (an awning needs the open front)");
            return;
        }

        const std::string canvas = textureOf(node, "canvas", m_pLook != nullptr ? m_pLook->pWood : nullptr);
        const std::string inner = textureOf(node, "inner", canvas.c_str());
        const std::string pole = textureOf(node, "pole", m_pLook != nullptr ? m_pLook->pWood : nullptr);
        const double footLength = size[0] * 0.5;
        const double footWidth = size[1] * 0.5;
        const double topLength = footLength - lean;
        const double topWidth = footWidth - lean;
        // S8d: `roof: hip` (a pavilion: Erathia's healers' tents HealerTent_*, a low hip over leaning canvas, here
        // its ends sloping in `hip` from each end, the width's half when left out); `gable` the default. A closed
        // tent's front may carry a door (`textures.door`, `door_width` 128 by `door_height` 256 or the walls'),
        // cut into the canvas, the click on it (their wooden Hhm3d door).
        const std::string roof = textOf(node, "roof", "gable");
        const double hipRun = std::min(numberOr(node, "hip", topWidth), topLength);
        const std::string doorTexture = textureOf(node, "door", "");
        const double doorWidth = numberOr(node, "door_width", 128.0);
        const double doorTop = ground + std::min(numberOr(node, "door_height", 256.0), walls);

        if ((roof != "gable" && roof != "hip") || (roof == "hip" && (awning > 0.0 || hipRun < 16.0))
            || (childOf(node, "hip").IsDefined() && roof != "hip"))
        {
            add(m_path + ".roof", "a tent's `roof` is gable (the default) or hip (its ends slope in too, `hip` from "
                "each end: 16 up to half its length; no `awning`)");
            return;
        }

        if ((!doorTexture.empty() || childOf(node, "door_width").IsDefined()
            || childOf(node, "door_height").IsDefined()) && (doorTexture.empty() || open || walls < 128.0
            || doorWidth < 64.0 || doorWidth > topWidth * 2.0 - 32.0 || doorTop < ground + 128.0))
        {
            add(m_path + ".textures.door", "a tent's door is on its closed front (`open: false`, walls 128 or more "
                "high), its picture `textures.door`, `door_width` 64 up to the walls' top width less 32 (128) and "
                "`door_height` 128 up to the walls' height (256)");
            return;
        }
        const auto at = [&](double east, double north, double z) -> OutdoorModelPoint
        {
            const Point2 point = turned(middle, east, north, turn);
            return {point[0], point[1], z};
        };
        const auto direction = [&](double east, double north, double up) -> std::array<double, 3>
        {
            const Point2 point = turned({0.0, 0.0}, east, north, turn);
            return {point[0], point[1], up};
        };
        const double foot = ground - 16.0;
        const double eave = ground + walls;
        const double ridge = ground + height;
        const double front = -topLength - awning;
        // Both ways: the canvas outside, the inner side within. The game draws an outdoor model's faces from both
        // sides, so two faces on the same points flicker (P2 feedback F31, the Hunters' tent on X1): with the inner
        // side in the canvas's own picture the canvas is drawn once and the inner face is kept, not drawn, so the
        // party inside still meets the canvas; in another picture it lies 2 inward of the canvas.
        // With a `hint` (batch O-H: Erathia's healers' "Tent"), the canvas says it and the click is the open
        // front's inside, or a closed tent's front end; a canvas drawn once is the open front's inside too.
        const auto sheet = [&](const std::vector<OutdoorModelPoint> &points, const std::array<double, 3> &out,
            const std::string &outside, const std::string &inside, bool used)
        {
            const int outerFace = facing(builder, points, out, outside, m_event);
            const size_t innerFace = faceCount();
            const std::array<double, 3> in = {-out[0], -out[1], -out[2]};

            if (inside == outside)
            {
                builder.hide(facing(builder, points, in, inside, m_event));

                if (used && open && outerFace >= 0)
                {
                    m_usedFaces.insert(static_cast<size_t>(outerFace));
                }

                return;
            }

            const double length = std::max(oy::hypot(out[0], out[1], out[2]), 1.0e-9);
            std::vector<OutdoorModelPoint> moved = points;

            for (OutdoorModelPoint &point : moved)
            {
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    point[axis] += in[axis] / length * 2.0;
                }
            }

            facing(builder, moved, in, inside, m_event);

            if (used && open)
            {
                markUsed(innerFace);
            }
        };
        const auto both = [&](const std::vector<OutdoorModelPoint> &points, const std::array<double, 3> &out)
        {
            sheet(points, out, canvas, inner, true);
        };

        for (const double way : {-1.0, 1.0})
        {
            // The roof's slope from the walls' top up to the ridge (on over the awning); a hip's ridge drawn in.
            const double ridgeEnd = roof == "hip" ? topLength - hipRun : topLength;

            if (roof == "hip" && ridgeEnd < 0.5)
            {
                both({at(way * topWidth, -topLength, eave), at(way * topWidth, topLength, eave),
                    at(0.0, 0.0, ridge)}, direction(way * (height - walls), 0.0, topWidth));
            }
            else
            {
                both({at(way * topWidth, roof == "hip" ? -topLength : front, eave), at(way * topWidth, topLength, eave),
                    at(0.0, ridgeEnd, ridge), at(0.0, roof == "hip" ? -ridgeEnd : front, ridge)},
                    direction(way * (height - walls), 0.0, topWidth));
            }

            if (roof == "hip")
            {
                // The hip's slope over each end.
                both({at(-topWidth, way * topLength, eave), at(topWidth, way * topLength, eave),
                    at(0.0, way * std::max(ridgeEnd, 0.0), ridge)}, direction(0.0, way * (height - walls), hipRun));
            }

            if (walls > 0.0)
            {
                // The side wall leaning in, its foot the tent's length, its top drawn in at the ends too.
                both({at(way * footWidth, -footLength, foot), at(way * footWidth, footLength, foot),
                    at(way * topWidth, topLength, eave), at(way * topWidth, -topLength, eave)},
                    direction(way * (walls + 16.0), 0.0, lean));
            }
        }

        // The ends: the back closed, the front closed unless open: the end wall leaning in, the gable over it.
        for (const double way : {1.0, -1.0})
        {
            if (way < 0.0 && open)
            {
                continue;
            }

            const size_t endFrom = faceCount();

            if (walls > 0.0 && way < 0.0 && !doorTexture.empty())
            {
                // The front with its door: the canvas either side and over it, in the end wall's leaning plane.
                const auto end = [&](double across, double z)
                {
                    const double share = (z - foot) / std::max(eave - foot, 1.0);
                    return at(across, way * (footLength - (footLength - topLength) * share), z);
                };
                const auto halfAt = [&](double z)
                {
                    return footWidth - (footWidth - topWidth) * (z - foot) / std::max(eave - foot, 1.0);
                };
                const double door = doorWidth * 0.5;
                const std::array<double, 3> out = direction(0.0, way * (walls + 16.0), lean);
                both({end(-halfAt(foot), foot), end(-door, foot), end(-door, eave), end(-halfAt(eave), eave)}, out);
                both({end(door, foot), end(halfAt(foot), foot), end(halfAt(eave), eave), end(door, eave)}, out);

                if (doorTop < eave - 0.5)
                {
                    both({end(-door, doorTop), end(door, doorTop), end(door, eave), end(-door, eave)}, out);
                }

                const std::vector<OutdoorModelPoint> doorFace = {end(-door, foot), end(door, foot),
                    end(door, doorTop), end(-door, doorTop)};
                const size_t doorFrom = faceCount();
                sheet(doorFace, out, doorTexture, inner, false);
                m_usedFaces.insert(doorFrom);
            }
            else if (walls > 0.0)
            {
                both({at(-footWidth, way * footLength, foot), at(footWidth, way * footLength, foot),
                    at(topWidth, way * topLength, eave), at(-topWidth, way * topLength, eave)},
                    direction(0.0, way * (walls + 16.0), lean));
            }

            if (roof != "hip")
            {
                both({at(-topWidth, way * topLength, eave), at(topWidth, way * topLength, eave),
                    at(0.0, way * topLength, ridge)}, direction(0.0, way, 0.0));
            }

            if (way < 0.0 && doorTexture.empty())
            {
                markUsed(endFrom);
            }
        }

        // Poles: one under each end of the ridge (inside the canvas), and the awning's two at its front corners.
        const double poleWidth = 16.0;

        // Under a hip the ridge is drawn in: the poles at its ends, one in the middle when it is a point.
        const double poleAt = roof == "hip" ? topLength - hipRun - poleWidth : topLength - poleWidth;

        const bool onePole = roof == "hip" && poleAt < 0.5;

        for (int index = 0; index < (onePole ? 1 : 2); ++index)
        {
            const double end = onePole ? 0.0 : index == 0 ? poleAt : -poleAt;
            builder.addPrism(turnedBox(turned(middle, 0.0, end, turn), poleWidth, poleWidth, turn), foot,
                ridge - poleWidth, pole, "", "", m_event);
        }

        if (awning > 0.0)
        {
            for (const double way : {-1.0, 1.0})
            {
                // Under the awning's edge, in from it by the pole's width (the canvas there is overhead).
                const double across = way * (topWidth - poleWidth);
                const double z = eave + (ridge - eave) * poleWidth / topWidth;
                builder.addPrism(turnedBox(turned(middle, across, front + poleWidth, turn), poleWidth, poleWidth,
                    turn), foot, z - 1.0, pole, pole, "", m_event);
            }
        }
    }

    // `kind: arcade`: a wall of arches along a front (Castle Navan's arcade, 7out04 ECastle_E: a wall 96 deep with
    // openings 256 wide between piers 128 wide, the arches springing 256 over its foot and rising 128 in four
    // steps): along `line` (two points), its foot `bottom` and top `height` over the land at its first point,
    // `depth`, `bays` openings (or as many as fit `span` wide between `pier`s), their arches `arch: round |
    // pointed | segment` (with `rise` for a segment) springing at `spring` over the foot; the top can be walked.
    void raiseArcade(const YAML::Node &node, OutdoorModelBuilder &builder)
    {
        std::vector<Point2> line;

        if (!lineOf(node, line))
        {
            return;
        }

        const double length = lengthOf(line.front(), line.back());
        const double ground = groundAt(line.front()) + numberOr(node, "raise", 0.0);
        const double bottom = numberOr(node, "bottom", 0.0);
        const double height = numberOr(node, "height", 512.0);
        const double depth = numberOr(node, "depth", 96.0);
        const double pier = numberOr(node, "pier", 128.0);
        const double spring = numberOr(node, "spring", 256.0);
        const std::string arch = textOf(node, "arch", "round");
        const double sidesNumber = numberOr(node, "sides", 4.0);
        double bays = numberOr(node, "bays", 0.0);

        if (bays == 0.0)
        {
            bays = std::max(1.0, std::floor((length - pier) / (numberOr(node, "span", 256.0) + pier)));
        }

        const double span = (length - pier * (bays + 1.0)) / bays;
        const double rise = arch == "segment" ? numberOr(node, "rise", span * 0.25) : arch == "pointed"
            ? span * 0.8660254 : span * 0.5;

        if (line.size() != 2 || bays < 1.0 || bays > 64.0 || bays != std::floor(bays) || pier < 16.0 || span < 32.0
            || depth < 16.0 || depth > 1024.0 || bottom < 0.0 || spring < 32.0 || height > 8192.0
            || bottom + spring + rise + 16.0 > height || (arch != "round" && arch != "pointed" && arch != "segment")
            || sidesNumber < 2.0 || sidesNumber > 16.0 || sidesNumber != std::floor(sidesNumber) || rise <= 0.0
            || rise > span * 0.5 + 0.5 * (arch == "pointed" ? span : 0.0))
        {
            add(m_path, "an arcade stands along `line` (two points), `depth` 16 to 1024 deep (96), `bays` openings "
                "(1 to 64, or as many as fit `span` wide (256) between `pier`s at least 16 wide (128)), their `arch` "
                "round, pointed or segment (`rise` up to half the span) in `sides` 2 to 16 steps (4), springing at "
                "`spring` (256) over the foot (`bottom`), all under its top `height` with 16 to spare");
            return;
        }

        const Point2 along = {(line[1][0] - line[0][0]) / length, (line[1][1] - line[0][1]) / length};
        const Point2 across = {-along[1], along[0]};
        const double foot = ground + bottom - (bottom == 0.0 ? 32.0 : 0.0);
        const double base = ground + bottom;
        const double top = ground + height;
        const std::string wall = textureOf(node, "wall", m_pLook != nullptr ? m_pLook->pStone : nullptr);
        const std::string soffit = textureOf(node, "under", wall.c_str());
        const std::string topTexture = textureOf(node, "top", wall.c_str());
        const auto at = [&](double s, double side, double z) -> OutdoorModelPoint
        {
            return {line[0][0] + along[0] * s + across[0] * side, line[0][1] + along[1] * s + across[1] * side, z};
        };
        const std::array<double, 3> front = {-across[0], -across[1], 0.0};
        const std::array<double, 3> backward = {across[0], across[1], 0.0};
        const double half = depth * 0.5;
        const int sides = static_cast<int>(sidesNumber);

        // An opening's head from its left to its right springing, as points (along, height).
        const auto head = [&](double from) -> std::vector<Point2>
        {
            std::vector<Point2> points;
            const double middle = from + span * 0.5;
            const double springZ = base + spring;

            for (int step = 0; step <= sides; ++step)
            {
                const double t = static_cast<double>(step) / sides;

                if (arch == "round")
                {
                    const double angle = Pi * (1.0 - t);
                    points.push_back({middle + span * 0.5 * oy::cos(angle), springZ + span * 0.5 * oy::sin(angle)});
                }
                else if (arch == "segment")
                {
                    // A circle's arc through the springings and the crown `rise` over them.
                    const double r = (span * span * 0.25 + rise * rise) / (2.0 * rise);
                    const double halfAngle = oy::asin(std::min(1.0, span * 0.5 / r));
                    const double angle = Pi * 0.5 + halfAngle - 2.0 * halfAngle * t;
                    points.push_back({middle + r * oy::cos(angle), springZ + rise - r + r * oy::sin(angle)});
                }
                else
                {
                    // Two arcs of radius `span` meeting at the crown, each centred on the far springing.
                    const bool leftArc = t <= 0.5;
                    const double u = leftArc ? t * 2.0 : (t - 0.5) * 2.0;
                    const double angle = leftArc ? Pi - u * Pi / 3.0 : Pi / 3.0 * (1.0 - u);
                    const double centre = leftArc ? from + span : from;
                    points.push_back({centre + span * oy::cos(angle), springZ + span * oy::sin(angle)});
                }
            }

            points.front()[0] = from;
            points.back()[0] = from + span;
            points.front()[1] = base + spring;
            points.back()[1] = base + spring;
            return points;
        };

        const size_t from = faceCount();

        for (int bay = 0; bay <= static_cast<int>(bays); ++bay)
        {
            // The pier at this bay's left (the last: the right end), front and back, foot to top.
            const double s = bay * (span + pier);

            for (const double side : {-half, half})
            {
                facing(builder, {at(s, side, foot), at(s + pier, side, foot), at(s + pier, side, top),
                    at(s, side, top)}, side < 0.0 ? front : backward, wall, m_event);
            }

            if (bay == static_cast<int>(bays))
            {
                break;
            }

            const double open = s + pier;
            const std::vector<Point2> curve = head(open);

            // The jambs (the piers' sides in the opening) and the soffit.
            facing(builder, {at(open, -half, foot), at(open, half, foot), at(open, half, base + spring),
                at(open, -half, base + spring)}, {along[0], along[1], 0.0}, soffit, m_event);
            facing(builder, {at(open + span, -half, foot), at(open + span, half, foot),
                at(open + span, half, base + spring), at(open + span, -half, base + spring)},
                {-along[0], -along[1], 0.0}, soffit, m_event);

            for (size_t index = 0; index + 1 < curve.size(); ++index)
            {
                const Point2 &a = curve[index];
                const Point2 &b = curve[index + 1];
                const double middle = open + span * 0.5;
                const std::array<double, 3> inward = {along[0] * (middle - (a[0] + b[0]) * 0.5),
                    along[1] * (middle - (a[0] + b[0]) * 0.5), base + spring - (a[1] + b[1]) * 0.5};
                facing(builder, {at(a[0], -half, a[1]), at(b[0], -half, b[1]), at(b[0], half, b[1]),
                    at(a[0], half, a[1])}, inward, soffit, m_event);

                // Over each step of the head, front and back, up to the top.
                for (const double side : {-half, half})
                {
                    facing(builder, {at(a[0], side, a[1]), at(b[0], side, b[1]), at(b[0], side, top),
                        at(a[0], side, top)}, side < 0.0 ? front : backward, wall, m_event);
                }
            }

            if (bottom > 0.0)
            {
                // A raised arcade's floor under the opening.
                facing(builder, {at(open, -half, base), at(open + span, -half, base), at(open + span, half, base),
                    at(open, half, base)}, {0.0, 0.0, 1.0}, topTexture, m_event);
            }
        }

        // The top, the two ends, the underside of a raised one.
        facing(builder, {at(0.0, -half, top), at(length, -half, top), at(length, half, top), at(0.0, half, top)},
            {0.0, 0.0, 1.0}, topTexture, m_event);

        for (const double s : {0.0, length})
        {
            facing(builder, {at(s, -half, foot), at(s, half, foot), at(s, half, top), at(s, -half, top)},
                {s == 0.0 ? -along[0] : along[0], s == 0.0 ? -along[1] : along[1], 0.0}, wall, m_event);
        }

        markUsed(from);
    }

    // A cave mouth or a hatch: its plan was read and its land set by the lowering (core/OutdoorWaysIn); its door
    // (the dark face, or the door slab) runs the click, the rest says the `hint`.
    void raiseCave(OutdoorModelBuilder &builder)
    {
        for (const OutdoorCavePlan &cave : m_lowered.caves)
        {
            if (cave.path == m_path)
            {
                std::vector<int> doorFaces;
                raiseOutdoorCave(cave, builder, m_event, doorFaces);

                for (const int face : doorFaces)
                {
                    if (face >= 0)
                    {
                        m_usedFaces.insert(static_cast<size_t>(face));
                    }
                }
            }
        }
    }

    // A shipped outdoor map of a world (the project's, or `from.world`), read once: where `kind: model` takes its
    // models from. Null when the asset root has no such map.
    const Game::OutdoorMapData *sourceMap(const std::string &world, const std::string &file)
    {
        const std::string key = world + "/" + file;
        const std::map<std::string, std::optional<Game::OutdoorMapData>>::const_iterator known =
            m_sourceMaps.find(key);

        if (known != m_sourceMaps.end())
        {
            return known->second ? &*known->second : nullptr;
        }

        std::string bytes;
        std::optional<Game::OutdoorMapData> map;

        if (file.find('/') == std::string::npos && file.find("..") == std::string::npos
            && readTextFile(m_assetRoot / "worlds" / world / "maps" / file, bytes))
        {
            map = Game::OutdoorMapDataLoader().loadFromBytes(std::vector<uint8_t>(bytes.begin(), bytes.end()));
        }

        const std::optional<Game::OutdoorMapData> &kept = m_sourceMaps.emplace(key, std::move(map)).first->second;
        return kept ? &*kept : nullptr;
    }

    // An imported model: models of a shipped map as they are, moved to the structure's place.
    void raiseImport(const YAML::Node &node, Game::OutdoorBModel &model)
    {
        const YAML::Node from = childOf(node, "from");
        const std::string file = lowerCase(textOf(from, "map"));
        const YAML::Node names = childOf(from, "models");
        const std::string world = textOf(from, "world").empty() ? m_lowered.world : textOf(from, "world");

        if (file.empty() || !names.IsDefined() || !names.IsSequence() || names.size() == 0)
        {
            add(m_path + ".from", "a model is taken `from: {map: <an outdoor map of this world, as out02.odm>, models: "
                "[<a model's name there, or its number from 0>, ...]}`; `oymap export <map> --summary` and the "
                "export's `bmodels` list them");
            return;
        }

        if (m_assetRoot.empty())
        {
            m_warnings.push_back("structures: the model " + m_id + " is left out: taking a model from a shipped "
                "map needs an asset root (--assets)");
            return;
        }

        if (world.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_") != std::string::npos)
        {
            add(m_path + ".from.world", "a world is named by its folder under worlds/ (mm7)");
            return;
        }

        const Game::OutdoorMapData *pSource = sourceMap(world, file);

        if (pSource == nullptr)
        {
            add(m_path + ".from.map", "there is no outdoor map " + file + " in worlds/" + world
                + "/maps of the asset root (a model is taken from a map of the project's own world, or of "
                "`from.world`)");
            return;
        }

        std::vector<size_t> picked;

        for (size_t index = 0; index < names.size(); ++index)
        {
            const std::string name = names[index].IsScalar() ? names[index].Scalar() : std::string();
            int number = -1;
            const size_t before = picked.size();

            if (wholeNumber(name, number))
            {
                if (number >= 0 && static_cast<size_t>(number) < pSource->bmodels.size())
                {
                    picked.push_back(static_cast<size_t>(number));
                }
            }
            else
            {
                for (size_t other = 0; other < pSource->bmodels.size(); ++other)
                {
                    if (!name.empty() && lowerCase(pSource->bmodels[other].name) == lowerCase(name))
                    {
                        picked.push_back(other);
                    }
                }
            }

            if (picked.size() == before)
            {
                std::string some;

                for (size_t other = 0; other < pSource->bmodels.size() && other < 12; ++other)
                {
                    some += (some.empty() ? "" : ", ") + pSource->bmodels[other].name;
                }

                add(m_path + ".from.models[" + std::to_string(index) + "]", file + " has no model `" + name
                    + "`: it has " + std::to_string(pSource->bmodels.size()) + " models, numbered from 0 (" + some
                    + " ...); name one, or give its number");
                return;
            }
        }

        // The middle of what is taken, in plan; the thing keeps its heights unless `raise` moves it.
        double west = 1.0e18;
        double south = 1.0e18;
        double east = -1.0e18;
        double north = -1.0e18;

        for (const size_t index : picked)
        {
            for (const Game::OutdoorBModelVertex &vertex : pSource->bmodels[index].vertices)
            {
                west = std::min(west, static_cast<double>(vertex.x));
                east = std::max(east, static_cast<double>(vertex.x));
                south = std::min(south, static_cast<double>(vertex.y));
                north = std::max(north, static_cast<double>(vertex.y));
            }
        }

        Point2 cell = {0.0, 0.0};
        int moveX = 0;
        int moveY = 0;

        if (childOf(node, "at").IsDefined())
        {
            if (!pointOf(childOf(node, "at"), cell) || cell[0] < 0.0 || cell[1] < 0.0
                || cell[0] > OutdoorNodeCount - 1 || cell[1] > OutdoorNodeCount - 1)
            {
                add(m_path + ".at", "`at` is where the model's middle goes, [x, y] in cells, inside the map; left "
                    "out: where it stands in the map it is taken from");
                return;
            }

            const Point2 world = toWorld(cell);
            moveX = static_cast<int>(std::lround(world[0] - (west + east) * 0.5));
            moveY = static_cast<int>(std::lround(world[1] - (south + north) * 0.5));
        }

        const int moveZ = static_cast<int>(std::lround(numberOr(node, "raise", 0.0)));
        // S8g: `turn`, degrees clockwise seen from above, about the middle of what is taken (X2's ship along an
        // east-west river: MM7's ships lie north to south). The faces' planes turn with them; their pictures stay
        // on them (the texture coordinates are the corners').
        const double turn = numberOr(node, "turn", 0.0);
        const double turnAngle = -turn * Pi / 180.0;
        const double middleX = (west + east) * 0.5 + moveX;
        const double middleY = (south + north) * 0.5 + moveY;
        const auto turnVertex = [turn, turnAngle, middleX, middleY](Game::OutdoorBModelVertex &vertex)
        {
            if (turn == 0.0)
            {
                return;
            }

            const double alongEast = vertex.x - middleX;
            const double alongNorth = vertex.y - middleY;
            vertex.x = static_cast<int>(std::lround(
                middleX + alongEast * oy::cos(turnAngle) - alongNorth * oy::sin(turnAngle)));
            vertex.y = static_cast<int>(std::lround(
                middleY + alongEast * oy::sin(turnAngle) + alongNorth * oy::cos(turnAngle)));
        };
        // `click`: the models taken that run the structure's click (the crystal's door, a ship's gangway); the
        // others say the `hint` or nothing. Left out: every face runs it.
        std::set<size_t> clicked;
        const YAML::Node click = childOf(node, "click");

        for (size_t index = 0; click.IsDefined() && click.IsSequence() && index < click.size(); ++index)
        {
            const std::string name = click[index].IsScalar() ? lowerCase(click[index].Scalar()) : std::string();
            const size_t before = clicked.size();

            for (const size_t candidate : picked)
            {
                int number = -1;

                if ((wholeNumber(name, number) && static_cast<size_t>(number) == candidate)
                    || (!name.empty() && lowerCase(pSource->bmodels[candidate].name) == name))
                {
                    clicked.insert(candidate);
                }
            }

            if (clicked.size() == before)
            {
                add(m_path + ".click[" + std::to_string(index) + "]", "`click` names models of `from.models` (by "
                    "name or number) whose faces run the click; `" + name + "` is none of those taken");
                return;
            }
        }

        if (click.IsDefined() && (!click.IsSequence() || click.size() == 0))
        {
            add(m_path + ".click", "`click` is a list of the models taken that run the click: [Crystal_Door]");
            return;
        }

        const uint32_t clickable = Game::faceAttributeBit(Game::FaceAttribute::Clickable);
        const uint32_t triggers = clickable | Game::faceAttributeBit(Game::FaceAttribute::PressurePlate)
            | Game::faceAttributeBit(Game::FaceAttribute::TriggerByTouch);

        for (const size_t index : picked)
        {
            const Game::OutdoorBModel &source = pSource->bmodels[index];
            const size_t firstVertex = model.vertices.size();

            if (firstVertex + source.vertices.size() > 65535)
            {
                add(m_path + ".from.models", "the models taken have more than 65535 corners together: take them as "
                    "several structures");
                return;
            }

            for (Game::OutdoorBModelVertex vertex : source.vertices)
            {
                vertex.x += moveX;
                vertex.y += moveY;
                vertex.z += moveZ;
                turnVertex(vertex);
                model.vertices.push_back(vertex);
            }

            for (Game::OutdoorBModelFace face : source.faces)
            {
                if (face.vertexIndices.empty())
                {
                    continue;
                }

                for (uint16_t &vertexIndex : face.vertexIndices)
                {
                    vertexIndex = static_cast<uint16_t>(vertexIndex + firstVertex);
                }

                // The face's plane goes with it; its own events and numbers stay behind.
                if (turn != 0.0)
                {
                    const double normalX = face.planeNormalX;
                    const double normalY = face.planeNormalY;
                    face.planeNormalX = static_cast<int32_t>(
                        std::lround(normalX * oy::cos(turnAngle) - normalY * oy::sin(turnAngle)));
                    face.planeNormalY = static_cast<int32_t>(
                        std::lround(normalX * oy::sin(turnAngle) + normalY * oy::cos(turnAngle)));
                }

                const Game::OutdoorBModelVertex &corner = model.vertices[face.vertexIndices[0]];
                face.planeDistance = static_cast<int32_t>(-(static_cast<int64_t>(face.planeNormalX) * corner.x
                    + static_cast<int64_t>(face.planeNormalY) * corner.y
                    + static_cast<int64_t>(face.planeNormalZ) * corner.z));
                face.cogNumber = 0;
                face.cogTrigger = 0;
                const bool runs = clicked.empty() || clicked.contains(index);
                face.cogTriggeredNumber = runs ? m_event : 0;
                face.attributes = (face.attributes & ~triggers) | (runs && m_event != 0 ? clickable : 0);

                if (!clicked.empty() && runs)
                {
                    m_usedFaces.insert(model.faces.size());
                }

                model.faces.push_back(face);
            }
        }

        const YAML::Node drop = childOf(node, "drop_overlaps");

        if (drop.IsDefined() && (!drop.IsScalar() || (drop.Scalar() != "true" && drop.Scalar() != "false")))
        {
            add(m_path + ".drop_overlaps", "`drop_overlaps: true` drops, of each two faces of the models taken that "
                "lie in one plane over each other (facing the same way or back to back), the smaller");
            return;
        }

        if (drop.IsDefined() && drop.Scalar() == "true")
        {
            dropOverlappingFaces(model);
        }
    }

    // `drop_overlaps` on a model taken (P3 2026-11-24, Nystor's ship: MM7's Lady Catherine, whose hull boards and
    // trim lie back to back and two trims on each other in the original): of each two drawn faces in one plane that
    // overlap, facing the same way (findOutdoorCoplanarFaces) or back to back where that is seen
    // (findOutdoorBackToBackFaces), the smaller face is dropped (the later one of two alike), so each pair keeps one
    // face, drawn from both sides as the game draws every outdoor face.
    void dropOverlappingFaces(Game::OutdoorBModel &model)
    {
        const auto areaOf = [&model](const Game::OutdoorBModelFace &face)
        {
            std::array<double, 3> sum = {0.0, 0.0, 0.0};
            const size_t count = face.vertexIndices.size();

            for (size_t index = 0; index < count; ++index)
            {
                const Game::OutdoorBModelVertex &a = model.vertices[face.vertexIndices[index]];
                const Game::OutdoorBModelVertex &b = model.vertices[face.vertexIndices[(index + 1) % count]];
                sum[0] += static_cast<double>(a.y) * b.z - static_cast<double>(a.z) * b.y;
                sum[1] += static_cast<double>(a.z) * b.x - static_cast<double>(a.x) * b.z;
                sum[2] += static_cast<double>(a.x) * b.y - static_cast<double>(a.y) * b.x;
            }

            return 0.5 * std::sqrt(sum[0] * sum[0] + sum[1] * sum[1] + sum[2] * sum[2]);
        };
        std::vector<OutdoorCoplanarPair> pairs = findOutdoorCoplanarFaces({model});
        const std::vector<OutdoorCoplanarPair> backToBack = findOutdoorBackToBackFaces({model});
        pairs.insert(pairs.end(), backToBack.begin(), backToBack.end());
        std::set<size_t> dropped;

        for (const OutdoorCoplanarPair &pair : pairs)
        {
            if (dropped.contains(pair.firstFace) || dropped.contains(pair.secondFace))
            {
                continue;
            }

            const double first = areaOf(model.faces[pair.firstFace]);
            const double second = areaOf(model.faces[pair.secondFace]);
            dropped.insert(first < second ? pair.firstFace
                : second < first ? pair.secondFace : std::max(pair.firstFace, pair.secondFace));
        }

        if (dropped.empty())
        {
            return;
        }

        std::vector<Game::OutdoorBModelFace> kept;
        std::set<size_t> used;

        for (size_t face = 0; face < model.faces.size(); ++face)
        {
            if (dropped.contains(face))
            {
                continue;
            }

            if (m_usedFaces.contains(face))
            {
                used.insert(kept.size());
            }

            kept.push_back(model.faces[face]);
        }

        model.faces = std::move(kept);
        m_usedFaces = std::move(used);
    }

    // ---- Actors ----

    void raiseActors(const YAML::Node &actors)
    {
        if (!actors.IsDefined() || !actors.IsSequence() || actors.size() == 0)
        {
            return;
        }

        std::string monsterText;
        std::string descriptorText;

        if (!readWorldTable(m_assetRoot, m_lowered.world, "monster_data.txt", "monster_data", monsterText)
            || !readWorldTable(
                m_assetRoot, m_lowered.world, "monster_descriptors.txt", "monster_descriptors", descriptorText))
        {
            m_warnings.push_back("actors: " + std::to_string(actors.size()) + " entries are left out: placing "
                "people needs the monster tables of an asset root (--assets)");
            return;
        }

        const std::vector<std::vector<std::string>> monsterRows = tableRows(monsterText);
        const std::vector<std::vector<std::string>> descriptorRows = tableRows(descriptorText);

        for (size_t index = 0; index < actors.size(); ++index)
        {
            const YAML::Node node = actors[index];
            m_path = "actors[" + std::to_string(index) + "]";
            const std::string monster = textOf(node, "monster");
            const std::vector<std::string> *pRow = nullptr;

            // By name (the table's second column, or the picture's name in its third) or by number.
            for (const std::vector<std::string> &row : monsterRows)
            {
                int number = 0;

                if (row.size() > 13 && wholeNumber(row[0], number) && (row[0] == monster
                    || lowerCase(row[1]) == lowerCase(monster) || lowerCase(row[2]) == lowerCase(monster)))
                {
                    pRow = pRow == nullptr ? &row : pRow;
                }
            }

            Point2 cell = {0.0, 0.0};

            if (pRow == nullptr)
            {
                add(m_path + ".monster", "there is no monster `" + monster + "` in engine/data_tables/"
                    "monster_data.txt: name a row by its name (Peasant), its picture's name or its number");
                continue;
            }

            if (!pointOf(childOf(node, "at"), cell) || cell[0] < 0.0 || cell[1] < 0.0 || cell[0] > OutdoorNodeCount - 1
                || cell[1] > OutdoorNodeCount - 1)
            {
                add(m_path + ".at", "`at` is where the actor stands, [x, y] in cells (fractions allowed), inside "
                    "the map");
                continue;
            }

            OutdoorActorPlan actor;
            actor.id = textOf(node, "id");
            actor.monster = (*pRow)[1];
            wholeNumber((*pRow)[0], actor.monsterId);
            int hitPoints = 0;
            int speed = 0;
            int height = 0;
            int radius = 0;
            std::string hitPointsText = (*pRow)[4];
            hitPointsText.erase(std::remove(hitPointsText.begin(), hitPointsText.end(), ' '), hitPointsText.end());
            wholeNumber(hitPointsText, hitPoints);
            wholeNumber((*pRow)[13], speed);

            for (const std::vector<std::string> &row : descriptorRows)
            {
                int number = 0;

                if (row.size() > 3 && wholeNumber(row[0], number) && number == actor.monsterId)
                {
                    wholeNumber(row[2], height);
                    wholeNumber(row[3], radius);
                }
            }

            if (hitPoints <= 0 || height <= 0 || radius <= 0)
            {
                add(m_path + ".monster", "the monster tables give " + actor.monster + " no hit points, height or "
                    "radius (monster_data.txt, monster_descriptors.txt row " + std::to_string(actor.monsterId) + ")");
                continue;
            }

            if (const YAML::Node carries = childOf(node, "carries"); carries.IsDefined())
            {
                const double item = numberOr(node, "carries", 0.0);

                if (!carries.IsScalar() || item < 1.0 || item != std::floor(item))
                {
                    add(m_path + ".carries", "`carries` is the number of the item the actor carries (a row of "
                        "items.txt): the game leaves it in the corpse");
                    continue;
                }

                actor.carriedItem = static_cast<int>(item);
            }

            const int count = static_cast<int>(numberOr(node, "count", 1.0));
            const double spread = numberOr(node, "spread", 1.0);

            if (count < 1 || count > 64 || spread < 0.0 || spread > 16.0)
            {
                add(m_path, "an actors entry places `count` 1 to 64 of the monster within `spread` cells (0 to 16) "
                    "of `at`");
                continue;
            }

            if (textOf(node, "hostile") == "false")
            {
                const int group = static_cast<int>(numberOr(node, "group", 0.0));

                if (group <= 0)
                {
                    add(m_path + ".hostile", "`hostile: false` makes a whole group peaceful: give the entry a `group` "
                        "number of its own (and the others that are to be peaceful with it the same)");
                    continue;
                }

                m_peacefulGroups.insert(group);
            }

            for (int member = 0; member < count; ++member)
            {
                // Round the place on a spiral that fills the spread evenly, the same every time.
                const double share = count == 1 ? 0.0 : std::sqrt((member + 0.5) / count);
                const double angle = member * 2.399963229728653;
                const Point2 at = {std::clamp(cell[0] + spread * share * oy::cos(angle), 0.0, OutdoorNodeCount - 1.0),
                    std::clamp(cell[1] + spread * share * oy::sin(angle), 0.0, OutdoorNodeCount - 1.0)};
                const Point2 world = toWorld(at);
                OutdoorActorPlan placed = actor;
                placed.x = static_cast<int>(std::lround(world[0]));
                placed.y = static_cast<int>(std::lround(world[1]));
                placed.z = static_cast<int>(std::lround(m_lowered.groundHeightAt(at[0], at[1])));
                placed.npc = static_cast<int>(numberOr(node, "npc", 0.0));
                placed.group = static_cast<int>(numberOr(node, "group", 0.0));
                placed.hostile = flagOf(node, "hostile");
                placed.hidden = flagOf(node, "hidden");
                placed.leash = static_cast<int>(std::lround(numberOr(node, "leash", 0.0)));
                placed.hitPoints = hitPoints;
                placed.height = height;
                placed.radius = radius;
                placed.moveSpeed = speed;
                m_things.actors.push_back(placed);
            }
        }
    }

    // sketch.yml `items` (D-90's bare finds, 2026-11-22): items that lie on the ground from the start, as objects.yml's
    // `items` indoors and the shipped outdoor maps' sprite objects (MM7 out11 holds 63): `item` by number or name,
    // `at` in cells, `height` over the game's ground there (default 0: on the ground; a key on a barrel's lid stands
    // the lid's height up), `gold` for a heap of gold.
    void raiseItems(const YAML::Node &items)
    {
        if (!items.IsDefined() || !items.IsSequence() || items.size() == 0)
        {
            return;
        }

        std::string itemText;
        std::string objectText;

        if (!readWorldTable(m_assetRoot, m_lowered.world, "items.txt", "items", itemText)
            || !readWorldTable(m_assetRoot, m_lowered.world, "object_list.txt", "object_list", objectText))
        {
            m_warnings.push_back("items: " + std::to_string(items.size()) + " entries are left out: an item on the "
                "ground needs the item tables of an asset root (--assets)");
            return;
        }

        const std::vector<std::vector<std::string>> itemRows = parseTableRows(itemText);
        const std::vector<std::vector<std::string>> objectRows = parseTableRows(objectText);
        std::set<std::string> ids;

        for (size_t index = 0; index < items.size(); ++index)
        {
            const YAML::Node node = items[index];
            m_path = "items[" + std::to_string(index) + "]";
            const std::string id = textOf(node, "id");
            Point2 cell = {0.0, 0.0};

            if (id.empty() || !ids.insert(id).second)
            {
                add(m_path + ".id", "an item on the ground has an `id` of its own (item:<name>)");
                continue;
            }

            if (!pointOf(childOf(node, "at"), cell) || cell[0] < 0.0 || cell[1] < 0.0 || cell[0] > OutdoorNodeCount - 1
                || cell[1] > OutdoorNodeCount - 1)
            {
                add(m_path + ".at", "`at` is where the item lies, [x, y] in cells (fractions allowed), inside the map");
                continue;
            }

            const std::vector<std::string> *pRow = namedTableRow(itemRows, childOf(node, "item"), {2}, std::nullopt,
                nullptr, "item", "items.txt", SketchFile, m_path + ".item", m_issues);

            if (pRow == nullptr)
            {
                continue;
            }

            LoweredItem item;
            item.id = id;

            if (!groundItemObjectOf(*pRow, objectRows, item))
            {
                add(m_path + ".item", "the item " + (*pRow)[0] + " (" + ((*pRow).size() > 2 ? (*pRow)[2] : "")
                    + ") cannot lie on the ground: no row of object_list.txt draws its sprite index (items.txt column "
                    "12). Choose another item, or put it in a chest");
                continue;
            }

            const bool goldHeap = pRow->size() > 4 && lowerCase((*pRow)[4]) == "gold";

            if (childOf(node, "gold").IsDefined() != goldHeap || (goldHeap && numberOr(node, "gold", 0.0) < 1.0))
            {
                add(m_path + ".gold", goldHeap ? "a heap of gold needs `gold`, the amount the party picks up (1 or "
                    "more)" : "`gold` is the amount of a heap of gold; the item " + (*pRow)[0]
                    + " is no heap of gold (items.txt Equip Stat Gold)");
                continue;
            }

            item.gold = goldHeap ? static_cast<int>(numberOr(node, "gold", 0.0)) : 0;
            const double height = numberOr(node, "height", 0.0);

            if (height < 0.0 || height > 2048.0)
            {
                add(m_path + ".height", "`height` is how far above the ground the item lies (0 to 2048: on a "
                    "barrel's lid, a table, a ledge)");
                continue;
            }

            const Point2 world = toWorld(cell);
            item.position = {std::round(world[0]), std::round(world[1]),
                std::round(m_lowered.groundHeightAt(cell[0], cell[1]) + height)};

            // The game settles a resting item onto the ground or onto a model's top under it
            // (OutdoorWorldRuntime::settleRestingWorldItems); a decoration (a barrel, a table sprite) is no floor.
            if (height > 0.0 && !structureTopAt(world, item.position[2]))
            {
                m_warnings.push_back(m_path + " (" + id + "): no structure's top lies " + std::to_string(
                    static_cast<int>(height)) + " over the ground here, so the game lets the item down onto the "
                    "ground (a decoration such as a barrel is no floor for items): lay it on the ground, or on a "
                    "structure (a crate, a platform, a deck)");
            }

            m_things.items.push_back(item);
        }
    }

    // Whether a top of a structure raised so far (a face that looks up) lies under `at` within 24 of `z`.
    bool structureTopAt(const Point2 &at, double z) const
    {
        for (const Game::OutdoorBModel &model : m_things.models)
        {
            if (at[0] < model.minX || at[0] > model.maxX || at[1] < model.minY || at[1] > model.maxY)
            {
                continue;
            }

            for (const Game::OutdoorBModelFace &face : model.faces)
            {
                if (face.planeNormalZ < 39322 || face.vertexIndices.size() < 3)
                {
                    continue;
                }

                std::vector<Point2> outline;

                for (const uint16_t vertex : face.vertexIndices)
                {
                    if (vertex < model.vertices.size())
                    {
                        outline.push_back({double(model.vertices[vertex].x), double(model.vertices[vertex].y)});
                    }
                }

                if (!pointInOrOnPolygon(outline, at))
                {
                    continue;
                }

                const double top = -(double(face.planeNormalX) * at[0] + double(face.planeNormalY) * at[1]
                    + double(face.planeDistance)) / double(face.planeNormalZ);

                if (std::abs(top - z) <= 24.0)
                {
                    return true;
                }
            }
        }

        return false;
    }

    // sketch.yml `sounds` (E9: the beds of wind, sea and birds, X6's sand-falls): the scene's ambient sounds, read as
    // objects.yml's indoors (devdocs/AMBIENT_SOUNDS.md): `at` in cells, `height` over the ground (default 64),
    // `radius` and `inner_radius` in game units, `volume`, `loop`, `wait`, `day_only`, `night_only`, `on`.
    void raiseSounds(const YAML::Node &sounds)
    {
        if (!sounds.IsDefined() || !sounds.IsSequence())
        {
            return;
        }

        const std::set<std::string> known = knownWorldSoundNames(m_assetRoot, m_mountRoot, m_lowered.world);

        for (size_t index = 0; index < sounds.size(); ++index)
        {
            const YAML::Node node = sounds[index];
            m_path = "sounds[" + std::to_string(index) + "]";
            const std::string id = textOf(node, "id");
            Point2 cell = {0.0, 0.0};

            if (id.empty())
            {
                add(m_path + ".id", "a sound has an `id` (sound:<name>): a script switches it by its number");
                continue;
            }

            if (!pointOf(childOf(node, "at"), cell) || cell[0] < 0.0 || cell[1] < 0.0 || cell[0] > OutdoorNodeCount - 1
                || cell[1] > OutdoorNodeCount - 1)
            {
                add(m_path + ".at", "`at` is where the sound is, [x, y] in cells (fractions allowed), inside the map");
                continue;
            }

            LoweredAmbientSound sound;
            sound.sound = textOf(node, "sound");
            sound.outerRadius = numberOr(node, "radius", 0.0);
            sound.innerRadius = numberOr(node, "inner_radius", std::floor(sound.outerRadius / 4.0));
            sound.volume = numberOr(node, "volume", 1.0);
            sound.loop = textOf(node, "loop") != "false";
            sound.startOn = textOf(node, "on") != "false";
            sound.dayOnly = flagOf(node, "day_only");
            sound.nightOnly = flagOf(node, "night_only");
            sound.pan = textOf(node, "pan") != "false";

            if (const YAML::Node wait = childOf(node, "wait"); wait.IsDefined())
            {
                sound.wait = {wait.IsSequence() && wait.size() == 2 ? wait[0].as<double>(-1.0) : -1.0,
                    wait.IsSequence() && wait.size() == 2 ? wait[1].as<double>(-1.0) : -1.0};
            }

            if (sound.sound.empty() || sound.outerRadius <= sound.innerRadius || sound.innerRadius < 0.0
                || sound.volume < 0.0 || sound.volume > 1.0
                || (sound.wait && ((*sound.wait)[0] < 0.0 || (*sound.wait)[1] < (*sound.wait)[0])))
            {
                add(m_path, "a sound needs `sound` (a sound file of the world) and `radius` (how far it is heard, "
                    "game units); `inner_radius` (full volume within it, default a quarter of `radius`) is smaller "
                    "than `radius`, `volume` lies between 0 and 1, and `wait` is [shortest, longest] seconds between "
                    "two plays");
                continue;
            }

            std::string soundName = lowerCase(sound.sound);

            if (!known.empty() && !known.contains(soundName))
            {
                add(m_path + ".sound", "the world " + m_lowered.world + " has no sound file " + sound.sound
                    + " (looked in worlds/" + m_lowered.world + "/audio and engine/audio of the asset root"
                    + (m_mountRoot.empty() ? std::string() : " and of the mount") + ", with and without .wav): name a "
                    ".wav file of those folders");
                continue;
            }

            const Point2 world = toWorld(cell);
            sound.position = {world[0], world[1], m_lowered.storedHeightAt(cell[0], cell[1])
                + numberOr(node, "height", 64.0)};
            sound.key = IdsLock::number(m_ids.sounds, id, 1);
            m_things.sounds.push_back(sound);
        }
    }

    const Project &m_project;
    const LoweredOutdoorMap &m_lowered;
    const std::filesystem::path m_assetRoot;
    std::filesystem::path m_mountRoot;
    IdsLock &m_ids;
    OutdoorEventWords &m_words;
    OutdoorThings &m_things;
    std::vector<ProjectIssue> &m_issues;
    std::vector<std::string> &m_warnings;
    const WorldLook *m_pLook = nullptr;
    std::string m_path;
    std::string m_id;
    uint16_t m_event = 0;
    // The model being raised, and its faces that are the thing's used part (a doorway's door, a basin's water, a
    // sign's board): what keeps the click when the rest only says a `hint`.
    Game::OutdoorBModel *m_pModel = nullptr;
    std::set<size_t> m_usedFaces;
    // Textures of the thing being raised that are liquids: their face bits.
    std::map<std::string, uint32_t> m_liquidTextures;
    std::set<int> m_peacefulGroups;
    std::map<std::string, std::optional<Game::OutdoorMapData>> m_sourceMaps;
    bool m_decorationsLoaded = false;
    std::map<std::string, int> m_decorations;
    // Pictures' sizes in texels as the game resolves them (a sign's board laid once at its own size), read through
    // an asset session opened on the first sign with a picture.
    std::optional<AssetSession> m_pictureSession;
    std::map<std::string, std::array<double, 2>> m_pictureSizes;

    // A picture's size in texels, or 64 x 64 (the shipped sign boards) with a warning when the game has none.
    std::array<double, 2> pictureSizeOf(const std::string &texture)
    {
        if (const auto known = m_pictureSizes.find(texture); known != m_pictureSizes.end())
        {
            return known->second;
        }

        std::array<double, 2> size = {64.0, 64.0};
        std::string error;

        if (!m_pictureSession)
        {
            m_pictureSession.emplace();

            if (!m_pictureSession->open(m_assetRoot, m_lowered.world, error))
            {
                m_warnings.push_back("sign pictures are laid at 64 x 64: " + error);
            }
        }

        Engine::DirectoryAssetPathCache directoryCache;
        Engine::AssetPathLookupCache pathCache;

        if (const std::optional<std::array<int, 2>> found = !m_pictureSession->world().empty()
                ? Engine::findSurfaceTextureLogicalSize(m_pictureSession->files(), lowerCase(texture), directoryCache,
                      pathCache)
                : std::nullopt)
        {
            size = {double((*found)[0]), double((*found)[1])};
        }
        else
        {
            m_warnings.push_back(m_path + ": the game has no texture " + texture + "; its picture is laid at 64 x 64");
        }

        m_pictureSizes.emplace(texture, size);
        return size;
    }
};
}

bool raiseOutdoorThings(
    const Project &project,
    const LoweredOutdoorMap &lowered,
    const std::filesystem::path &assetRoot,
    IdsLock &ids,
    OutdoorEventWords &words,
    OutdoorThings &things,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings,
    const std::filesystem::path &mountRoot)
{
    if (!project.has("sketch.yml"))
    {
        return true;
    }

    ThingRaiser raiser(project, lowered, assetRoot, ids, words, things, issues, warnings);
    raiser.setMountRoot(mountRoot);
    return raiser.raise();
}
}
