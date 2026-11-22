#include "core/Audit.h"

#include "core/Compare.h"
#include "core/Looks.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <optional>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
// The numbers of the light checks, measured on the shipped MM6-MM8 dungeons (devdocs/xeen/formats/LIGHTS.md, the
// calibration in output/xeen_a1/lights_mm678.txt).
namespace Limits
{
// A hung fixture's top lies within this of the ceiling over it (its chain or hook reaches it); further is a warning,
// and a hung fixture whose foot is within FloorTouch of the floor with its top further than this from the ceiling is
// an error (a ceiling lamp standing on the floor).
constexpr double HungTopGap = 48.0;
constexpr double HungTopGapError = 160.0;
constexpr double FloorTouch = 8.0;
// The game hangs a wall fixture's model on the nearest wall within 64 of its middle (findIndoorDecorationWall);
// without one it stands free: in the air.
constexpr double WallReach = 64.0;
// A wall fixture's foot over the floor under it: below this it stands on the floor (a warning; over pits and
// shafts the shipped maps hang torches thousands over the floor, so there is no upper bound).
constexpr double WallLow = 16.0;
// A standing fixture's foot over the floor under it: more is floating (an error past FloatError), and sunk deeper
// than SunkDepth into the floor.
constexpr double FloatWarning = 8.0;
constexpr double FloatError = 32.0;
constexpr double SunkDepth = 8.0;
// The slab of an opening (a portal a party wide, at most 512): this far either side of its plane.
constexpr double DoorwayDepth = 24.0;
constexpr double PartyRadius = 37.0;
constexpr double WidestDoorway = 512.0;
// How high a hung fixture's foot must stay over an opening's floor to hang in the opening (the party's height and a
// margin).
constexpr double HungDoorwayClearance = 224.0;
// How far behind the faces round it a point may lie and still count as on them: the shipped maps put 228 of their
// 9128 lights within 4 behind a wall and their torches' middles up to 16 into it (the game hangs the model on the
// wall all the same). Deeper is a warning to RockError, an error past it.
constexpr double RockSlack = 16.0;
constexpr double RockError = 32.0;
// A standing fixture rests on another decoration (a brazier on a pedestal) when its foot is within this of the
// other's top and its middle within the other's radius (at least 32).
constexpr double RestsOn = 24.0;
}

enum class Mount
{
    None,
    Ceiling,
    Wall,
    Floor,
    Free,
};

const char *mountName(Mount mount)
{
    switch (mount)
    {
    case Mount::Ceiling:
        return "ceiling";
    case Mount::Wall:
        return "wall";
    case Mount::Floor:
        return "floor";
    case Mount::Free:
        return "free";
    case Mount::None:
        break;
    }

    return "none";
}

std::optional<Mount> mountOf(const std::string &text)
{
    if (text == "ceiling")
    {
        return Mount::Ceiling;
    }

    if (text == "wall")
    {
        return Mount::Wall;
    }

    if (text == "floor")
    {
        return Mount::Floor;
    }

    if (text == "free")
    {
        return Mount::Free;
    }

    if (text == "none")
    {
        return Mount::None;
    }

    return std::nullopt;
}

std::string lowerText(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

bool hasWord(const std::string &text, std::initializer_list<const char *> words)
{
    return std::any_of(words.begin(), words.end(), [&text](const char *pWord)
    {
        return text.find(pWord) != std::string::npos;
    });
}

struct DecorationRow
{
    std::string name;
    std::string hint;
    double height = 0.0;
    double lightRadius = 0.0;
};

struct Binding
{
    double height = 0.0;
    double zOffset = 0.0;
    bool wall = false;
    bool swing = false;
    std::set<std::string> maps;
};

// What the tables say of the decorations: rows by list id (the row's number less one), the model bindings and the
// fixture list by lower-case name.
struct FixtureTables
{
    std::map<int, DecorationRow> rows;
    std::map<std::string, std::vector<Binding>> bindings;
    std::map<std::string, Mount> listed;
};

FixtureTables readTables(const LightFixtureData &data, std::vector<AuditFinding> &findings)
{
    FixtureTables tables;
    std::istringstream table(data.decorationTableText);

    for (std::string line; std::getline(table, line);)
    {
        std::vector<std::string> cells;
        std::istringstream row(line);

        for (std::string cell; std::getline(row, cell, '\t');)
        {
            cells.push_back(cell);
        }

        if (cells.size() >= 7 && !cells[0].empty() && std::isdigit(static_cast<unsigned char>(cells[0][0])))
        {
            DecorationRow decoration;
            decoration.name = lowerText(cells[1]);
            decoration.hint = lowerText(cells[2]);
            decoration.height = std::atof(cells[5].c_str());
            decoration.lightRadius = std::atof(cells[6].c_str());
            tables.rows[std::atoi(cells[0].c_str()) - 1] = decoration;
        }
    }

    for (const std::string &text : data.bindingTexts)
    {
        try
        {
            const YAML::Node document = YAML::Load(text);

            for (const YAML::Node &entry : document["decorations"] ? document["decorations"] : YAML::Node())
            {
                if (!entry.IsMap() || !entry["name"])
                {
                    continue;
                }

                Binding binding;
                binding.height = entry["height"] ? entry["height"].as<double>(0.0) : 0.0;
                binding.zOffset = entry["z_offset"] ? entry["z_offset"].as<double>(0.0) : 0.0;
                binding.wall = entry["mount"] && entry["mount"].as<std::string>("") == "wall";
                binding.swing = static_cast<bool>(entry["swing"]);

                for (const YAML::Node &map : entry["maps"] ? entry["maps"] : YAML::Node())
                {
                    binding.maps.insert(lowerText(map.as<std::string>("")));
                }

                tables.bindings[lowerText(entry["name"].as<std::string>(""))].push_back(binding);
            }
        }
        catch (const YAML::Exception &exception)
        {
            findings.push_back({"lights.tables", "warning", std::string("a decoration binding file does not read: ")
                + exception.what(), "Fix the YAML."});
        }
    }

    for (const std::string &text : data.fixtureTexts)
    {
        try
        {
            const YAML::Node fixtures = YAML::Load(text)["fixtures"];

            for (YAML::const_iterator entry = fixtures && fixtures.IsMap() ? fixtures.begin() : YAML::const_iterator();
                 fixtures && fixtures.IsMap() && entry != fixtures.end(); ++entry)
            {
                const std::optional<Mount> mount = mountOf(entry->second.as<std::string>(""));

                if (!mount)
                {
                    findings.push_back({"lights.tables", "warning", "light_fixtures.yml: " + entry->first.Scalar()
                        + " has no mount (ceiling, wall, floor, free or none)", "Give it one of the five."});
                    continue;
                }

                tables.listed[lowerText(entry->first.Scalar())] = *mount;
            }
        }
        catch (const YAML::Exception &exception)
        {
            findings.push_back({"lights.tables", "warning", std::string("light_fixtures.yml does not read: ")
                + exception.what(), "Fix the YAML."});
        }
    }

    return tables;
}

// The binding the game draws a decoration of this map with: one naming the map, else one naming none.
const Binding *bindingOf(const FixtureTables &tables, const std::string &name, const std::string &mapFile)
{
    const auto found = tables.bindings.find(name);

    if (found == tables.bindings.end())
    {
        return nullptr;
    }

    const Binding *pGeneral = nullptr;

    for (const Binding &binding : found->second)
    {
        if (binding.maps.contains(lowerText(mapFile)))
        {
            return &binding;
        }

        if (binding.maps.empty() && pGeneral == nullptr)
        {
            pGeneral = &binding;
        }
    }

    return pGeneral;
}

// A decoration's mount: the fixture list's word, else its binding's (a swinging model hangs, a wall-mounted one is
// on a wall), else its row's hint and name; Mount::None for what is no light fixture. `unclassified`: a decoration
// that gives light but none of these says how it is held.
Mount classify(const FixtureTables &tables, const DecorationRow &row, const Binding *pBinding, bool &unclassified)
{
    unclassified = false;
    const auto listed = tables.listed.find(row.name);

    if (listed != tables.listed.end())
    {
        return listed->second;
    }

    if (pBinding != nullptr && pBinding->swing && hasWord(row.hint, {"chandelier", "lamp", "lantern", "censer"}))
    {
        return Mount::Ceiling;
    }

    if (pBinding != nullptr && pBinding->wall)
    {
        return Mount::Wall;
    }

    const std::string words = row.hint + " " + row.name;

    if (hasWord(words, {"chandelier", "hanging lamp", "hanging lantern", "censer"}))
    {
        return Mount::Ceiling;
    }

    if (hasWord(words, {"sconce", "torch", "wall lamp", "bracket"}))
    {
        return Mount::Wall;
    }

    if (hasWord(words, {"brazier", "candle", "candelabr", "campfire", "fire", "beacon", "lamp post", "lamppost",
            "firebowl", "fire bowl"}))
    {
        return Mount::Floor;
    }

    if (hasWord(words, {"glow", "wisp", "will o", "light orb"}))
    {
        return Mount::Free;
    }

    unclassified = row.lightRadius > 0.0;
    return Mount::None;
}

// An opening of the map: a portal a party wide and at most WidestDoorway, upright.
struct Opening
{
    size_t face = 0;
    std::array<double, 3> middle = {};
    std::array<double, 2> way = {};
    std::array<double, 2> across = {};
    double least = 0.0;
    double most = 0.0;
    double low = 0.0;
    double high = 0.0;
};

std::vector<Opening> openingsOf(const Game::IndoorMapData &indoor)
{
    std::vector<Opening> openings;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];
        const size_t count = face.vertexIndices.size();

        if ((!face.isPortal && !Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal)) || count < 3)
        {
            continue;
        }

        Opening opening;
        opening.face = faceIndex;
        std::array<double, 3> normal = {0.0, 0.0, 0.0};
        bool inside = true;

        for (size_t index = 0; index < count && inside; ++index)
        {
            const uint16_t first = face.vertexIndices[index];
            const uint16_t second = face.vertexIndices[(index + 1) % count];
            inside = first < indoor.vertices.size() && second < indoor.vertices.size();

            if (!inside)
            {
                break;
            }

            const Game::IndoorVertex &a = indoor.vertices[first];
            const Game::IndoorVertex &b = indoor.vertices[second];
            opening.middle = {opening.middle[0] + a.x / double(count), opening.middle[1] + a.y / double(count),
                opening.middle[2] + a.z / double(count)};
            normal[0] += double(a.y - b.y) * (a.z + b.z);
            normal[1] += double(a.z - b.z) * (a.x + b.x);
            normal[2] += double(a.x - b.x) * (a.y + b.y);
        }

        const double horizontal = std::hypot(normal[0], normal[1]);

        if (!inside || horizontal <= 0.0 || horizontal < 0.7 * std::hypot(horizontal, normal[2]))
        {
            continue;
        }

        opening.way = {normal[0] / horizontal, normal[1] / horizontal};
        opening.across = {-opening.way[1], opening.way[0]};
        opening.least = 1.0e18;
        opening.most = -1.0e18;
        opening.low = 1.0e18;
        opening.high = -1.0e18;

        for (const uint16_t vertexIndex : face.vertexIndices)
        {
            const Game::IndoorVertex &vertex = indoor.vertices[vertexIndex];
            const double side = (vertex.x - opening.middle[0]) * opening.across[0]
                + (vertex.y - opening.middle[1]) * opening.across[1];
            opening.least = std::min(opening.least, side);
            opening.most = std::max(opening.most, side);
            opening.low = std::min(opening.low, double(vertex.z));
            opening.high = std::max(opening.high, double(vertex.z));
        }

        if (opening.most - opening.least >= 2.0 * Limits::PartyRadius
            && opening.most - opening.least <= Limits::WidestDoorway && opening.high - opening.low >= 128.0)
        {
            openings.push_back(opening);
        }
    }

    return openings;
}

// The opening whose slab holds the point (x, y) between heights `low` and `high`: within DoorwayDepth and `radius`
// of its plane, between its sides (less `inset`), overlapping its height.
const Opening *openingAt(const std::vector<Opening> &openings, double x, double y, double low, double high,
    double radius, double inset)
{
    for (const Opening &opening : openings)
    {
        const double dx = x - opening.middle[0];
        const double dy = y - opening.middle[1];
        const double out = dx * opening.way[0] + dy * opening.way[1];
        const double side = dx * opening.across[0] + dy * opening.across[1];

        if (std::fabs(out) <= Limits::DoorwayDepth + radius && side > opening.least + inset
            && side < opening.most - inset && high > opening.low && low < opening.high)
        {
            return &opening;
        }
    }

    return nullptr;
}

// The solid faces both ways round: a ray from open space meets a face's front, from inside the rock its back.
struct Solid
{
    RayScene scene;

    struct Hit
    {
        bool hit = false;
        bool back = false;
        double distance = 0.0;
        size_t face = 0;
    };

    Hit cast(const std::array<double, 3> &origin, const std::array<double, 3> &direction, double cap) const
    {
        const RayHit hit = scene.cast(origin, direction, cap);
        Hit result;
        result.hit = hit.hit;
        result.distance = hit.distance;

        if (hit.hit)
        {
            result.back = (hit.sourceId & 1) != 0;
            result.face = static_cast<size_t>(hit.sourceId / 2);
        }

        return result;
    }

    // Whether the point lies inside the rock: the first face up or down is seen from behind, or most of the ways
    // round meet a back first.
    bool inside(const std::array<double, 3> &point) const
    {
        const Hit up = cast(point, {0.0, 0.0, 1.0}, 65536.0);
        const Hit down = cast(point, {0.0, 0.0, -1.0}, 65536.0);

        if ((up.hit && up.back) || (down.hit && down.back) || !down.hit)
        {
            return true;
        }

        size_t backs = 0;
        size_t hits = 0;

        for (int step = 0; step < 8; ++step)
        {
            const double angle = step * 3.14159265358979323846 / 4.0;
            const Hit hit = cast(point, {std::cos(angle), std::sin(angle), 0.0}, 65536.0);
            hits += hit.hit ? 1 : 0;
            backs += hit.hit && hit.back ? 1 : 0;
        }

        return hits > 0 && backs * 2 > hits;
    }

    // How deep the point lies behind the faces round it: the nearest back met first, up, down and 16 ways level
    // (0 when every first face is a front).
    double depth(const std::array<double, 3> &point) const
    {
        double nearest = 0.0;
        const auto take = [&nearest](const Hit &hit)
        {
            if (hit.hit && hit.back && (nearest == 0.0 || hit.distance < nearest))
            {
                nearest = std::max(hit.distance, 0.01);
            }
        };
        take(cast(point, {0.0, 0.0, 1.0}, 65536.0));
        take(cast(point, {0.0, 0.0, -1.0}, 65536.0));

        for (int step = 0; step < 16; ++step)
        {
            const double angle = step * 3.14159265358979323846 / 8.0;
            take(cast(point, {std::cos(angle), std::sin(angle), 0.0}, 65536.0));
        }

        return nearest;
    }

    // The nearest face round the point, level: its distance and number (16 ways); nothing within `cap`: no hit.
    Hit nearestLevel(const std::array<double, 3> &point, double cap) const
    {
        Hit best;
        best.distance = cap;

        for (int step = 0; step < 16; ++step)
        {
            const double angle = step * 3.14159265358979323846 / 8.0;
            const Hit hit = cast(point, {std::cos(angle), std::sin(angle), 0.0}, best.distance);

            if (hit.hit && !hit.back && hit.distance < best.distance)
            {
                best = hit;
            }
        }

        return best;
    }
};

std::string place(double x, double y, double z)
{
    return "[" + std::to_string(std::lround(x)) + ", " + std::to_string(std::lround(y)) + ", "
        + std::to_string(std::lround(z)) + "]";
}

std::string units(double value)
{
    return std::to_string(std::lround(value));
}
}

std::vector<AuditFinding> auditLightFixtures(
    const LoadedMap &map, const LightFixtureData &data, const std::set<int> &hanging, bool measure)
{
    std::vector<AuditFinding> findings;

    if (!map.indoor)
    {
        return findings;
    }

    const Game::IndoorMapData &indoor = *map.indoor;
    const FixtureTables tables = readTables(data, findings);
    Solid solid;

    for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = indoor.faces[faceIndex];

        if (face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal)
            || face.vertexIndices.size() < 3)
        {
            continue;
        }

        std::vector<std::array<double, 3>> points;

        for (const uint16_t vertexIndex : face.vertexIndices)
        {
            if (vertexIndex < indoor.vertices.size())
            {
                const Game::IndoorVertex &vertex = indoor.vertices[vertexIndex];
                points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
            }
        }

        // The side the face is seen from (the order of its corners, as the eye-sector check takes it), and its back.
        std::array<double, 3> normal = {0.0, 0.0, 0.0};

        for (size_t index = 0; index < points.size(); ++index)
        {
            const std::array<double, 3> &current = points[index];
            const std::array<double, 3> &next = points[(index + 1) % points.size()];
            normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
            normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
            normal[2] += (current[0] - next[0]) * (current[1] + next[1]);
        }

        solid.scene.addFace(points, normal, static_cast<int32_t>(faceIndex * 2), face.textureName);
        solid.scene.addFace(points, {-normal[0], -normal[1], -normal[2]}, static_cast<int32_t>(faceIndex * 2 + 1),
            face.textureName);
    }

    solid.scene.setSeamTolerance(0.5);
    solid.scene.build();
    const std::vector<Opening> openings = openingsOf(indoor);
    // The faces that move whole (door leaves, lifts, movers: every corner is the door's): a fixture on one stays
    // where the face was. (A face that only stretches, a wall with a corner on a door's edge, keeps its other part.)
    std::map<size_t, uint32_t> movingFaces;

    if (map.state)
    {
        for (const Game::MapDeltaDoor &door : map.state->doors)
        {
            const std::set<uint16_t> moved(door.vertexIds.begin(), door.vertexIds.end());

            for (const uint16_t faceId : door.faceIds)
            {
                if (faceId < indoor.faces.size() && door.moveLength > 0
                    && std::all_of(indoor.faces[faceId].vertexIndices.begin(),
                        indoor.faces[faceId].vertexIndices.end(),
                        [&moved](uint16_t vertex) { return moved.contains(vertex); }))
                {
                    movingFaces.emplace(faceId, door.doorId);
                }
            }
        }
    }

    // How deep a point lies in the rock: behind the faces round it (Solid::inside) and in no sector as the game finds
    // one (an open shaft's air or a sky map's has faces seen from behind round it); 0 in a room.
    Game::IndoorFaceGeometryCache geometryCache(indoor.faces.size());
    const auto rockDepth = [&](const std::array<double, 3> &point)
    {
        if (!solid.inside(point))
        {
            return 0.0;
        }

        const std::optional<int16_t> sector = Game::findIndoorSectorForPoint(indoor, indoor.vertices,
            {float(point[0]), float(point[1]), float(point[2])}, &geometryCache, false);
        return sector && *sector > 0 ? 0.0 : solid.depth(point);
    };
    std::set<std::string> unclassifiedNames;

    for (size_t entityIndex = 0; entityIndex < indoor.entities.size(); ++entityIndex)
    {
        const Game::IndoorEntity &entity = indoor.entities[entityIndex];
        const auto rowFound = tables.rows.find(entity.decorationListId);

        if (rowFound == tables.rows.end())
        {
            continue;
        }

        const DecorationRow &row = rowFound->second;
        const Binding *pBinding = bindingOf(tables, row.name, map.fileName);
        bool unclassified = false;
        Mount mount = classify(tables, row, pBinding, unclassified);

        if (unclassified)
        {
            unclassifiedNames.insert(row.name + " (" + row.hint + ")");
        }

        // A light-giving decoration's light: at its middle (the game's decoration light, half the row's height
        // up), not inside the rock.
        if (row.lightRadius > 0.0)
        {
            const std::array<double, 3> light = {
                double(entity.x), double(entity.y), entity.z + std::max(row.height, 1.0) * 0.5};

            const double depth = rockDepth(light);

            if (measure)
            {
                findings.push_back({"lights.measure", "info", "map=" + map.fileName + " decolight=" + std::to_string(
                        entityIndex) + " name=" + row.name + " in_rock=" + (depth > 0.0 ? "1" : "0") + " depth="
                        + units(depth), ""});
            }

            if (depth > Limits::RockSlack)
            {
                findings.push_back({"lights.light_in_solid", depth > Limits::RockError ? "error" : "warning",
                    "decoration " + std::to_string(entityIndex)
                        + " (" + row.name + ", " + row.hint + ") gives its light at " + place(light[0], light[1],
                        light[2]) + ", inside the rock: it lights nothing, or the room behind the wall",
                    "Move the decoration out of the wall, into its room."});
            }
        }

        if (mount == Mount::None)
        {
            continue;
        }

        const double height = pBinding != nullptr && pBinding->height > 0.0 ? pBinding->height
            : std::max(row.height, 16.0);
        const double base = entity.z + (pBinding != nullptr ? pBinding->zOffset : 0.0);
        const double top = base + height;
        const std::array<double, 3> middle = {double(entity.x), double(entity.y), base + height * 0.5};
        const std::string who = "decoration " + std::to_string(entityIndex) + " (" + row.name + ", " + row.hint
            + ", " + mountName(mount) + ") at " + place(entity.x, entity.y, entity.z);
        // The floor under its foot and the ceiling over its top, as rays from its middle meet them.
        const Solid::Hit down = solid.cast(middle, {0.0, 0.0, -1.0}, 65536.0);
        const Solid::Hit up = solid.cast(middle, {0.0, 0.0, 1.0}, 65536.0);
        const bool floorSeen = down.hit && !down.back;
        const bool ceilingSeen = up.hit && !up.back;
        const double floorGap = floorSeen ? base - (middle[2] - down.distance) : 0.0;
        const double ceilingGap = ceilingSeen ? (middle[2] + up.distance) - top : 0.0;
        const Solid::Hit wall = solid.nearestLevel(middle, 512.0);
        const double depth = rockDepth(middle);
        const bool inRock = depth > Limits::RockSlack;
        const bool hangs = hanging.contains(static_cast<int>(entityIndex));

        if (measure)
        {
            findings.push_back({"lights.measure", "info", "map=" + map.fileName + " entity=" + std::to_string(entityIndex)
                    + " name=" + row.name + " mount=" + mountName(mount) + " bound=" + (pBinding != nullptr ? "1" : "0")
                    + " height=" + units(height) + " floor_gap=" + (floorSeen ? units(floorGap) : "none")
                    + " ceiling_gap=" + (ceilingSeen ? units(ceilingGap) : "none") + " wall="
                    + (wall.hit ? units(wall.distance) : "none") + " in_rock=" + (inRock ? "1" : "0")
                    + " depth=" + units(depth) + " moving_wall=" + (wall.hit && movingFaces.contains(wall.face) ? "1" : "0")
                    + " doorway=" + (openingAt(openings, entity.x, entity.y, base, top, 0.0, 0.0) ? "1" : "0")
                    + " hangs=" + (hangs ? "1" : "0"),
                ""});
        }

        if (inRock)
        {
            findings.push_back({"lights.in_solid", depth > Limits::RockError ? "error" : "warning", who + " stands "
                    "inside the rock (its middle " + place(middle[0], middle[1], middle[2]) + " lies " + units(depth)
                    + " behind the faces round it)",
                "Move it into its room."});
            continue;
        }

        if (mount == Mount::Ceiling)
        {
            if (floorSeen && floorGap <= Limits::FloorTouch && (!ceilingSeen || ceilingGap > Limits::HungTopGapError))
            {
                findings.push_back({"lights.ceiling_on_floor", "error", who + " hangs from a ceiling but stands on "
                        "the floor (its foot " + units(floorGap) + " over it, its top " + (ceilingSeen
                        ? units(ceilingGap) + " under the ceiling" : std::string("under no ceiling")) + ")",
                    "Raise it until its top is within " + units(Limits::HungTopGap) + " of the ceiling (z "
                        + (ceilingSeen ? units(middle[2] + up.distance - height) : std::string("?")) + ")."});
            }
            else if (!ceilingSeen || ceilingGap > Limits::HungTopGap)
            {
                findings.push_back({"lights.ceiling_gap", ceilingSeen && ceilingGap <= Limits::HungTopGapError
                        ? "warning" : "error", who + (ceilingSeen ? " hangs with its top " + units(ceilingGap)
                        + " under the ceiling: its chain does not reach it" : std::string(" has no ceiling over it")),
                    "Raise it until its top is within " + units(Limits::HungTopGap) + " of the ceiling"
                        + (ceilingSeen ? " (z " + units(middle[2] + up.distance - height) + ")" : std::string())
                        + ", or bind a model with a longer chain."});
            }
            else if (ceilingGap < -Limits::HungTopGap)
            {
                findings.push_back({"lights.ceiling_gap", "warning", who + " reaches " + units(-ceilingGap)
                        + " into the ceiling", "Lower it until its top meets the ceiling (z "
                        + units(middle[2] + up.distance - height) + ")."});
            }

            if (const Opening *pOpening = openingAt(openings, entity.x, entity.y, base, top, 0.0, 0.0);
                pOpening != nullptr && base < pOpening->low + Limits::HungDoorwayClearance)
            {
                findings.push_back({"lights.in_doorway", "error", who + " hangs in the opening of face "
                        + std::to_string(pOpening->face) + " with its foot " + units(base - pOpening->low)
                        + " over the opening's floor: the party walks into it",
                    "Hang it in the room, clear of the opening, or with its foot "
                        + units(Limits::HungDoorwayClearance) + " or more over the floor."});
            }
        }
        else if (mount == Mount::Wall)
        {
            // The game hangs the model on the nearest wall within reach of its middle; none: it stands in the air.
            // The game's own search (findIndoorDecorationWall: any face as steep as a wall, either side, within 64
            // of the middle); a middle a little inside the rock is on its wall too.
            const std::optional<Game::DecorationWallContact> contact = Game::findIndoorDecorationWall(
                indoor, entity.x, entity.y, entity.z, static_cast<float>(height));

            if (!contact)
            {
                findings.push_back({"lights.wall_missing", "error", who + " has no wall within "
                        + units(Limits::WallReach) + " of its middle (the nearest " + (wall.hit
                        ? units(wall.distance) + " away" : std::string("further than 512")) + "): it hangs in the air",
                    "Put it against a wall (its middle within " + units(Limits::WallReach) + " of the face)."});
            }
            else if (depth == 0.0 && movingFaces.contains(wall.face))
            {
                findings.push_back({"lights.on_moving_face", "error", who + " hangs on face "
                        + std::to_string(wall.face) + ", which door " + std::to_string(movingFaces.at(wall.face))
                        + " moves: the fixture stays in the air when it opens",
                    "Hang it on a wall that does not move."});
            }

            if (const Opening *pOpening = openingAt(openings, entity.x, entity.y, base, top, 0.0, 32.0))
            {
                findings.push_back({"lights.in_doorway", "error", who + " hangs inside the opening of face "
                        + std::to_string(pOpening->face) + " (sectors " + std::to_string(indoor.faces[pOpening->face]
                        .roomNumber) + " and " + std::to_string(indoor.faces[pOpening->face].roomBehindNumber) + ")",
                    "Hang it on the wall beside the opening."});
            }

            if (floorSeen && floorGap < Limits::WallLow)
            {
                findings.push_back({"lights.wall_height", "warning", who + " hangs with its foot " + units(floorGap)
                        + " over the floor: it stands on the floor (wall fixtures hang " + units(Limits::WallLow)
                        + " or more over it)",
                    "Hang it at about the shipped maps' height (its foot 100 to 200 over the floor)."});
            }
        }
        else if (mount == Mount::Floor && !hangs)
        {
            // On another decoration (a pedestal, a table) or hung with its top at the ceiling (6d02's braziers on
            // chains), it stands where it should.
            const bool restsOnDecoration = std::any_of(indoor.entities.begin(), indoor.entities.end(),
                [&](const Game::IndoorEntity &other)
                {
                    const auto otherRow = tables.rows.find(other.decorationListId);

                    if (&other == &entity || otherRow == tables.rows.end())
                    {
                        return false;
                    }

                    const Binding *pOther = bindingOf(tables, otherRow->second.name, map.fileName);
                    const double otherTop = other.z + (pOther != nullptr ? pOther->zOffset + pOther->height
                        : otherRow->second.height);
                    return std::hypot(double(other.x - entity.x), double(other.y - entity.y)) <= 32.0
                        && std::fabs(otherTop - base) <= Limits::RestsOn;
                });
            const bool hungAtCeiling = ceilingSeen && ceilingGap <= Limits::HungTopGap;

            if (floorSeen && floorGap > Limits::FloatWarning && !restsOnDecoration && !hungAtCeiling)
            {
                findings.push_back({"lights.floating", floorGap > Limits::FloatError ? "error" : "warning", who
                        + " stands " + units(floorGap) + " over the floor or top under it",
                    "Stand it on the floor (z " + units(middle[2] - down.distance - (base - entity.z)) + ")."});
            }

            const Solid::Hit sunk = solid.cast({double(entity.x), double(entity.y), base + 1.0}, {0.0, 0.0, 1.0},
                height);

            if (sunk.hit && sunk.back && sunk.distance + 1.0 > Limits::SunkDepth
                && indoor.faces[sunk.face].vertexIndices.size() >= 3)
            {
                findings.push_back({"lights.sunk", "warning", who + " is sunk " + units(sunk.distance + 1.0)
                        + " into the floor (face " + std::to_string(sunk.face) + ")",
                    "Stand it on the floor's surface."});
            }

            if (const Opening *pOpening = openingAt(openings, entity.x, entity.y, base, top, 0.0, 0.0))
            {
                findings.push_back({"lights.in_doorway", "error", who + " stands in the opening of face "
                        + std::to_string(pOpening->face), "Stand it in the room, clear of the opening."});
            }
        }
    }

    for (const std::string &name : unclassifiedNames)
    {
        findings.push_back({"lights.unclassified", "info", "decoration " + name + " gives light, and neither its "
                "row, its binding nor engine/models/light_fixtures.yml says how it is held",
            "Add it to light_fixtures.yml (ceiling, wall, floor, free or none)."});
    }

    // The map's own lights: inside a room and off its faces.
    for (size_t lightIndex = 0; lightIndex < indoor.lights.size(); ++lightIndex)
    {
        const Game::IndoorLight &light = indoor.lights[lightIndex];
        const std::array<double, 3> point = {double(light.x), double(light.y), double(light.z)};
        const Solid::Hit wall = solid.nearestLevel(point, 512.0);
        const Solid::Hit down = solid.cast(point, {0.0, 0.0, -1.0}, 65536.0);
        const Solid::Hit up = solid.cast(point, {0.0, 0.0, 1.0}, 65536.0);
        const double depth = rockDepth(point);

        if (measure)
        {
            findings.push_back({"lights.measure", "info", "map=" + map.fileName + " light=" + std::to_string(lightIndex)
                    + " radius=" + std::to_string(light.radius) + " wall=" + (wall.hit ? units(wall.distance) : "none")
                    + " floor=" + (down.hit && !down.back ? units(down.distance) : "none") + " ceiling="
                    + (up.hit && !up.back ? units(up.distance) : "none") + " in_rock=" + (depth > 0.0 ? "1" : "0")
                    + " depth=" + units(depth),
                ""});
        }

        const std::string who = "light " + std::to_string(lightIndex) + " (radius " + std::to_string(light.radius)
            + ") at " + place(point[0], point[1], point[2]);

        if (depth > Limits::RockSlack)
        {
            findings.push_back({"lights.light_in_solid", depth > Limits::RockError ? "error" : "warning", who
                    + " lies " + units(depth) + " inside the rock: it lights the faces round it from behind",
                "Move it into the room it lights."});
        }
    }

    return findings;
}
}
