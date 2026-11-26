#include "core/Audit.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/outdoor/OutdoorGeometryUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <map>
#include <optional>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
// The numbers of the door checks, measured on the shipped MM6-MM8 maps (devdocs/xeen/formats/DOORS.md, the
// calibration in output/xeen_a1/doors_mm678.txt).
namespace DoorLimits
{
// A door picture shows more than once across a leaf when the leaf is this many times the picture's width (the
// shipped leaves that repeat a door picture by accident show it 1.5 times or more; a picture laid at a slightly
// other scale than its leaf stays under).
constexpr double TiledCopies = 1.3;
// A leaf this wide (or wider) is a wide opening: a gate, great hall doors.
constexpr double WideLeaf = 192.0;
// Two leaves are a pair when their fronts lie within this of one plane and of each other along the wall.
constexpr double PlaneSlack = 8.0;
constexpr double PairGap = 16.0;
// F2 (tools/xeen/door_check.py): a wing alone on a leaf this wide or wider is a door's half (narrower: a shutter or
// a strip of trim); a door picture shows at least this share of itself across its leaf; a pair of leaves is at least
// this wide together; a door stands within StepsOffset of the middle of steps reaching within StepsReach of its wall.
constexpr double LoneWing = 96.0;
constexpr double LeastCopies = 0.75;
constexpr double LeastPair = 192.0;
constexpr double StepsReach = 128.0;
constexpr double StepsOffset = 32.0;
// F27 (tools/xeen/town_fit_check.py `houses.buried_door`): the land before an outdoor door (32, 96 and 160 in front
// of it; at its middle and 0.6 of its half width each side) standing more than this over its sill: the door is dug
// into a slope.
constexpr double DoorBury = 48.0;
}

double dot3(const std::array<double, 3> &a, const std::array<double, 3> &b)
{
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

std::string lowerName(std::string name)
{
    std::transform(name.begin(), name.end(), name.begin(),
        [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
    return name;
}

std::string rounded(double value, double step = 0.01)
{
    std::ostringstream text;
    text << std::round(value / step) * step;
    return text.str();
}

// One face as it lays its picture on an upright plane: its extent along the wall (`along`, the horizontal axis of
// the plane with the face's front to the left of it seen from above... any fixed choice per normal) and in height,
// and the texels per unit along those two ways (signed: a picture laid mirrored has the other sign of `uRate`).
struct UprightLayout
{
    std::array<double, 3> normal = {};
    std::array<double, 3> along = {};
    double planeDistance = 0.0;
    double low = 0.0;
    double high = 0.0;
    double bottom = 0.0;
    double top = 0.0;
    double uRate = 0.0;
    double vRate = 0.0;
};

// The plane of an upright face and how its texels change along it; nothing for a face that is not upright, has no
// area or whose texels do not fit a plane.
std::optional<UprightLayout> uprightLayout(
    const std::vector<std::array<double, 3>> &points, const std::vector<std::array<double, 2>> &texels)
{
    if (points.size() < 3 || texels.size() != points.size())
    {
        return std::nullopt;
    }

    std::array<double, 3> normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const std::array<double, 3> &a = points[index];
        const std::array<double, 3> &b = points[(index + 1) % points.size()];
        normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
        normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
        normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }

    const double length = std::sqrt(dot3(normal, normal));

    if (length < 1.0)
    {
        return std::nullopt;
    }

    for (double &component : normal)
    {
        component /= length;
    }

    if (std::abs(normal[2]) > 0.2)
    {
        return std::nullopt;
    }

    UprightLayout layout;
    // Along the wall: up crossed with the normal, so a wall seen from its front runs to the right.
    const double horizontal = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1]);
    layout.normal = {normal[0] / horizontal, normal[1] / horizontal, 0.0};
    layout.along = {-layout.normal[1], layout.normal[0], 0.0};
    layout.planeDistance = dot3(layout.normal, points[0]);
    layout.low = 1e18;
    layout.high = -1e18;
    layout.bottom = 1e18;
    layout.top = -1e18;
    // Least squares of u and v over (along, height, 1).
    std::array<std::array<double, 3>, 3> normalMatrix = {};
    std::array<double, 3> uRight = {};
    std::array<double, 3> vRight = {};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const double s = dot3(layout.along, points[index]);
        const double z = points[index][2];
        layout.low = std::min(layout.low, s);
        layout.high = std::max(layout.high, s);
        layout.bottom = std::min(layout.bottom, z);
        layout.top = std::max(layout.top, z);
        const std::array<double, 3> row = {s, z, 1.0};

        for (size_t i = 0; i < 3; ++i)
        {
            for (size_t j = 0; j < 3; ++j)
            {
                normalMatrix[i][j] += row[i] * row[j];
            }

            uRight[i] += row[i] * texels[index][0];
            vRight[i] += row[i] * texels[index][1];
        }
    }

    if (layout.high - layout.low < 1.0 || layout.top - layout.bottom < 1.0)
    {
        return std::nullopt;
    }

    // Solve by Cramer's rule.
    const auto determinant = [](const std::array<std::array<double, 3>, 3> &m)
    {
        return m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
    };
    const double whole = determinant(normalMatrix);

    if (std::abs(whole) < 1e-6)
    {
        return std::nullopt;
    }

    const auto solveFor = [&](const std::array<double, 3> &right, size_t column)
    {
        std::array<std::array<double, 3>, 3> replaced = normalMatrix;

        for (size_t row = 0; row < 3; ++row)
        {
            replaced[row][column] = right[row];
        }

        return determinant(replaced) / whole;
    };

    layout.uRate = solveFor(uRight, 0);
    // v runs down the picture: texels per unit downward.
    layout.vRate = -solveFor(vRight, 1);
    return layout;
}

// What texture_classes.yml (tools/xeen/texture_classes.py) says of a texture.
struct TextureClass
{
    // tile, trim_u (seamless along its width only), trim_v (along its height only) or feature.
    std::string kind;
    // Door pictures: single (one leaf), wing (one wing of a double door: two leaves, the other mirrored), pair (both
    // wings in one picture), tile (planks or bars that repeat). Empty: no door picture.
    std::string door;
    // How alike the picture is to its mirror image, 0 (unlike) to 1 (the same).
    double mirror = 0.0;
    std::array<int, 2> size = {0, 0};
    std::optional<std::array<int, 3>> border;
    std::string material;
    // Whether it repeats cleanly across and down: its edges meet that way, or the shipped maps repeat it so.
    std::array<bool, 2> tiles = {true, true};
    // Stacked whole once per storey up a wall (decision D-41, the overrides' `storey_stack`): edge (a footing or eaves
    // band meant once per wall: an error), module (made to repeat once per storey: no finding); empty: a warning.
    std::string storeyStack;
};

std::map<std::string, TextureClass> readTextureClasses(const std::vector<std::string> &texts)
{
    std::map<std::string, TextureClass> classes;

    for (const std::string &text : texts)
    {
        YAML::Node root;

        try
        {
            root = YAML::Load(text);
        }
        catch (const YAML::Exception &)
        {
            continue;
        }

        for (const YAML::detail::iterator_value &entry : root["textures"])
        {
            const YAML::Node &node = entry.second;
            TextureClass &texture = classes[lowerName(entry.first.as<std::string>())];
            texture.kind = node["class"] ? node["class"].as<std::string>() : std::string();
            texture.door = node["door"] ? node["door"].as<std::string>() : std::string();
            texture.mirror = node["mirror"] ? node["mirror"].as<double>() : 0.0;
            texture.material = node["material"] ? node["material"].as<std::string>() : std::string();
            texture.storeyStack = node["storey_stack"] ? node["storey_stack"].as<std::string>() : std::string();

            if (node["size"] && node["size"].size() == 2)
            {
                texture.size = {node["size"][0].as<int>(), node["size"][1].as<int>()};
            }

            if (node["tiles"] && node["tiles"].size() == 2)
            {
                texture.tiles = {node["tiles"][0].as<bool>(), node["tiles"][1].as<bool>()};
            }

            if (node["border"] && node["border"].size() == 3)
            {
                texture.border = std::array<int, 3>{node["border"][0].as<int>(), node["border"][1].as<int>(),
                    node["border"][2].as<int>()};
            }
        }
    }

    return classes;
}

// One door leaf, or outdoors one door face: its front as one upright layout over all its front faces.
struct Leaf
{
    // Indoors the door record's number; outdoors the model and face.
    std::string name;
    std::string texture;
    UprightLayout front;
    // Texels per unit along the wall and down, weighted by the faces' areas.
    double uRate = 0.0;
    double vRate = 0.0;
    std::optional<size_t> partner;
    // An outdoor model face (the F2 rules judge these only: an indoor leaf's texels are measured off its stored
    // pose, which on the shipped maps reads a slice for whole pictures).
    bool outdoor = false;
};

double copiesAcross(const Leaf &leaf, const std::array<int, 2> &size)
{
    return size[0] > 0 ? (leaf.front.high - leaf.front.low) * std::abs(leaf.uRate) / size[0] : 0.0;
}

double copiesDown(const Leaf &leaf, const std::array<int, 2> &size)
{
    return size[1] > 0 ? (leaf.front.top - leaf.front.bottom) * std::abs(leaf.vRate) / size[1] : 0.0;
}

// The leaves next to each other in one plane: each gets the nearest such leaf as its partner.
void pairLeaves(std::vector<Leaf> &leaves)
{
    for (size_t first = 0; first < leaves.size(); ++first)
    {
        double best = DoorLimits::PairGap;

        for (size_t second = 0; second < leaves.size(); ++second)
        {
            const UprightLayout &a = leaves[first].front;
            const UprightLayout &b = leaves[second].front;

            if (second == first || dot3(a.normal, b.normal) < 0.98
                || std::abs(a.planeDistance - b.planeDistance) > DoorLimits::PlaneSlack)
            {
                continue;
            }

            const double overlap = std::min(a.top, b.top) - std::max(a.bottom, b.bottom);
            const double gap = std::max(a.low, b.low) - std::min(a.high, b.high);

            if (overlap < 0.5 * std::min(a.top - a.bottom, b.top - b.bottom) || gap > best || gap < -4.0)
            {
                continue;
            }

            best = gap;
            leaves[first].partner = second;
        }
    }
}

// The leaves of a map's doors: indoors every door record's faces that move whole and stand upright, grouped by the
// side they face, the side with the most area its front; outdoors every upright model face with a door picture (by
// texture_classes.yml) or with an event and a name that says door or gate.
std::vector<Leaf> leavesOf(const LoadedMap &map, const std::map<std::string, TextureClass> &classes)
{
    std::vector<Leaf> leaves;
    // Upright faces of one door (or outdoor face) gathered into a leaf: the texture with the most area, its faces'
    // united extent and their area-weighted texel rates.
    struct Part
    {
        UprightLayout layout;
        std::string texture;
    };
    const auto addLeaf = [&leaves](const std::string &name, const std::vector<Part> &parts)
    {
        if (parts.empty())
        {
            return;
        }

        // The side with the most area is the front.
        std::vector<std::pair<std::array<double, 3>, double>> sides;

        for (const Part &part : parts)
        {
            const double area = (part.layout.high - part.layout.low) * (part.layout.top - part.layout.bottom);
            bool found = false;

            for (std::pair<std::array<double, 3>, double> &side : sides)
            {
                if (dot3(side.first, part.layout.normal) > 0.98)
                {
                    side.second += area;
                    found = true;
                    break;
                }
            }

            if (!found)
            {
                sides.push_back({part.layout.normal, area});
            }
        }

        const std::array<double, 3> front = std::max_element(sides.begin(), sides.end(),
            [](const auto &a, const auto &b) { return a.second < b.second; })->first;
        // The front's picture is the texture with the most area on it; the leaf is the faces bearing it (a reveal or
        // a wall corner that moves with the leaf is no part of its picture).
        std::map<std::string, double> textureAreas;

        for (const Part &part : parts)
        {
            if (dot3(front, part.layout.normal) >= 0.98)
            {
                textureAreas[part.texture] +=
                    (part.layout.high - part.layout.low) * (part.layout.top - part.layout.bottom);
            }
        }

        Leaf leaf;
        leaf.name = name;
        leaf.texture = std::max_element(textureAreas.begin(), textureAreas.end(),
            [](const auto &a, const auto &b) { return a.second < b.second; })->first;
        bool first = true;
        double weight = 0.0;

        for (const Part &part : parts)
        {
            if (dot3(front, part.layout.normal) < 0.98 || part.texture != leaf.texture)
            {
                continue;
            }

            const double area = (part.layout.high - part.layout.low) * (part.layout.top - part.layout.bottom);

            if (first)
            {
                leaf.front = part.layout;
                first = false;
            }
            else
            {
                leaf.front.low = std::min(leaf.front.low, part.layout.low);
                leaf.front.high = std::max(leaf.front.high, part.layout.high);
                leaf.front.bottom = std::min(leaf.front.bottom, part.layout.bottom);
                leaf.front.top = std::max(leaf.front.top, part.layout.top);
            }

            leaf.uRate += part.layout.uRate * area;
            leaf.vRate += part.layout.vRate * area;
            weight += area;
        }

        leaf.uRate /= weight;
        leaf.vRate /= weight;
        leaves.push_back(leaf);
    };

    if (map.indoor && map.state)
    {
        const Game::IndoorMapData &indoor = *map.indoor;

        for (const Game::MapDeltaDoor &door : map.state->doors)
        {
            // The leaf shut (the original engines' doors are stored open or shut; a folding leaf open is a stub).
            std::vector<Game::IndoorVertex> closed = indoor.vertices;
            Game::applyIndoorMechanismDoorToVertices(door, nullptr, static_cast<float>(door.moveLength), 0, closed);
            const std::set<uint16_t> moved(door.vertexIds.begin(), door.vertexIds.end());
            const std::array<double, 3> direction = {Game::fixedIndoorDoorDirectionComponentToFloat(door.directionX),
                Game::fixedIndoorDoorDirectionComponentToFloat(door.directionY),
                Game::fixedIndoorDoorDirectionComponentToFloat(door.directionZ)};
            std::vector<Part> parts;

            for (const uint16_t faceId : door.faceIds)
            {
                if (faceId >= indoor.faces.size())
                {
                    continue;
                }

                const Game::IndoorFace &face = indoor.faces[faceId];

                // A leaf's faces: at least one corner moves (a folding leaf's front stretches; its jamb end stays).
                if (face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal)
                    || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
                    || std::none_of(face.vertexIndices.begin(), face.vertexIndices.end(),
                        [&moved](uint16_t vertex) { return moved.contains(vertex); }))
                {
                    continue;
                }

                std::vector<std::array<double, 3>> stored;
                std::vector<std::array<double, 3>> shut;
                std::vector<std::array<double, 2>> texels;

                for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
                {
                    const Game::IndoorVertex &vertex = indoor.vertices[face.vertexIndices[corner]];
                    const Game::IndoorVertex &shutVertex = closed[face.vertexIndices[corner]];
                    stored.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
                    shut.push_back({double(shutVertex.x), double(shutVertex.y), double(shutVertex.z)});

                    if (corner < face.textureUs.size() && corner < face.textureVs.size())
                    {
                        texels.push_back({double(face.textureUs[corner]), double(face.textureVs[corner])});
                    }
                }

                std::optional<UprightLayout> layout = uprightLayout(shut, texels);

                // A front moves in its own plane (a leaf's end or a jamb faces the way it moves).
                if (!layout || std::abs(dot3(layout->normal, direction)) > 0.2
                    || layout->high - layout->low < 32.0 || layout->top - layout->bottom < 32.0)
                {
                    continue;
                }

                // The texels are the stored pose's: their rates from it where it has width (shut, a leaf stored
                // open is then laid as it is stored).
                if (const std::optional<UprightLayout> asStored = uprightLayout(stored, texels);
                    asStored && asStored->high - asStored->low >= 16.0 && dot3(asStored->normal, layout->normal) > 0.9)
                {
                    layout->uRate = asStored->uRate;
                    layout->vRate = asStored->vRate;
                }

                parts.push_back({*layout, lowerName(face.textureName)});
            }

            addLeaf("door " + std::to_string(door.doorId), parts);
        }
    }

    if (map.outdoor)
    {
        for (size_t modelIndex = 0; modelIndex < map.outdoor->bmodels.size(); ++modelIndex)
        {
            const Game::OutdoorBModel &model = map.outdoor->bmodels[modelIndex];

            for (size_t faceIndex = 0; faceIndex < model.faces.size(); ++faceIndex)
            {
                const Game::OutdoorBModelFace &face = model.faces[faceIndex];
                const std::string texture = lowerName(face.textureName);
                const std::map<std::string, TextureClass>::const_iterator known = classes.find(texture);
                const bool doorPicture = known != classes.end() && !known->second.door.empty();
                const bool namedDoor = face.cogTriggeredNumber != 0
                    && (texture.find("door") != std::string::npos || texture.find("gate") != std::string::npos);

                // A face hidden at load is measured too: an event may show it (D1's restored stable gate, A6).
                if (!doorPicture && !namedDoor)
                {
                    continue;
                }

                std::vector<std::array<double, 3>> points;
                std::vector<std::array<double, 2>> texels;

                for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
                {
                    if (face.vertexIndices[corner] >= model.vertices.size())
                    {
                        break;
                    }

                    const Game::OutdoorBModelVertex &vertex = model.vertices[face.vertexIndices[corner]];
                    points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});

                    if (corner < face.textureUs.size() && corner < face.textureVs.size())
                    {
                        texels.push_back({double(face.textureUs[corner]), double(face.textureVs[corner])});
                    }
                }

                if (const std::optional<UprightLayout> layout = uprightLayout(points, texels))
                {
                    if (layout->high - layout->low >= 32.0 && layout->top - layout->bottom >= 32.0)
                    {
                        addLeaf("model " + std::to_string(modelIndex) + " (" + model.name + ") face "
                                + std::to_string(faceIndex),
                            {Part{*layout, texture}});
                        leaves.back().outdoor = true;
                    }
                }
            }
        }
    }

    pairLeaves(leaves);
    return leaves;
}

std::array<int, 2> sizeOf(const std::string &texture, const TextureFitData &data,
    const std::map<std::string, TextureClass> &classes)
{
    if (const auto known = data.sizes.find(texture); known != data.sizes.end())
    {
        return known->second;
    }

    if (const auto known = classes.find(texture); known != classes.end())
    {
        return known->second.size;
    }

    return {0, 0};
}
// The numbers of the texture-fit checks, measured on the shipped MM6-MM8 maps (devdocs/xeen/formats/TEXTURE_FIT.md,
// the calibration in output/xeen_a1/fit/).
namespace FitLimits
{
// A picture meant once shows more than once across (down) its surface past this many copies (as a door picture).
constexpr double RepeatedCopies = 1.3;
// A picture meant once is cut off when no unbroken stretch of its surface shows this share of it across (down).
constexpr double WholeShare = 0.7;
// A surface smaller than this either way (a reveal, a sill, a sliver beside a window) is not judged for a cut.
constexpr double CutMinimum = 48.0;
// A surface narrower than this (a jamb's edge, a frame's side) is not judged at all.
constexpr double MinimumSide = 16.0;
// A repeating texture whose edges do not meet is judged on a surface showing it at least this many times that way.
constexpr double LargeCopies = 2.0;
// Two faces lie in one plane within this, and touch when their extents are this close.
constexpr double PlaneSlack = 2.0;
constexpr double TouchGap = 4.0;
// Faces that meet along an edge this long are neighbours (a window and the wall round it, two stretches of a wall).
constexpr double SharedEdge = 32.0;
// Border colours this far apart (mean of |R|, |G|, |B| differences, 0 to 255) clearly differ.
constexpr double BorderDifference = 60.0;
// Two wall textures side by side this far apart in colour are of different families.
constexpr double FamilyDifference = 80.0;
// A storey panel: a picture one row of the studio's walls high (256), stacked whole up a wall once per storey.
constexpr int StoreyHeight = 256;
}

// One drawn face: its corners, its texels (with the face's texture offset) and whether it is a door's.
struct FitFace
{
    std::string name;
    std::string texture;
    std::vector<std::array<double, 3>> points;
    std::vector<std::array<double, 2>> texels;
};

std::vector<FitFace> facesOf(const LoadedMap &map)
{
    std::vector<FitFace> faces;

    if (map.indoor)
    {
        const Game::IndoorMapData &indoor = *map.indoor;

        for (size_t faceIndex = 0; faceIndex < indoor.faces.size(); ++faceIndex)
        {
            const Game::IndoorFace &face = indoor.faces[faceIndex];

            // A sky face (an open sky's opening) shows the sky, not its texture (A8: no family_switch on it).
            if (face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IsPortal)
                || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
                || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::IndoorSky)
                || face.vertexIndices.size() < 3 || face.textureUs.size() != face.vertexIndices.size()
                || face.textureVs.size() != face.vertexIndices.size())
            {
                continue;
            }

            FitFace use;
            use.name = std::to_string(faceIndex);
            use.texture = lowerName(face.textureName);

            for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
            {
                const Game::IndoorVertex &vertex = indoor.vertices[face.vertexIndices[corner]];
                use.points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
                use.texels.push_back({double(face.textureUs[corner]) + face.textureDeltaU,
                    double(face.textureVs[corner]) + face.textureDeltaV});
            }

            faces.push_back(std::move(use));
        }
    }

    if (map.outdoor)
    {
        for (size_t modelIndex = 0; modelIndex < map.outdoor->bmodels.size(); ++modelIndex)
        {
            const Game::OutdoorBModel &model = map.outdoor->bmodels[modelIndex];

            for (size_t faceIndex = 0; faceIndex < model.faces.size(); ++faceIndex)
            {
                const Game::OutdoorBModelFace &face = model.faces[faceIndex];

                if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
                    || face.vertexIndices.size() < 3 || face.textureUs.size() != face.vertexIndices.size()
                    || face.textureVs.size() != face.vertexIndices.size())
                {
                    continue;
                }

                FitFace use;
                use.name = std::to_string(modelIndex) + "/" + std::to_string(faceIndex);
                use.texture = lowerName(face.textureName);
                bool whole = true;

                for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
                {
                    if (face.vertexIndices[corner] >= model.vertices.size())
                    {
                        whole = false;
                        break;
                    }

                    const Game::OutdoorBModelVertex &vertex = model.vertices[face.vertexIndices[corner]];
                    use.points.push_back({double(vertex.x), double(vertex.y), double(vertex.z)});
                    use.texels.push_back({double(face.textureUs[corner]) + face.textureDeltaU,
                        double(face.textureVs[corner]) + face.textureDeltaV});
                }

                if (whole)
                {
                    faces.push_back(std::move(use));
                }
            }
        }
    }

    return faces;
}

// A face on its plane: two axes in it (upright: along the wall seen from its front and up; else any two), its extent
// on them and its texels as an affine map of them (u = mapU . (a, b, 1)).
struct PlacedFace
{
    size_t face = 0;
    bool upright = false;
    std::array<double, 3> normal = {};
    double distance = 0.0;
    std::array<double, 3> axisA = {};
    std::array<double, 3> axisB = {};
    std::array<double, 4> box = {};
    std::array<double, 3> mapU = {};
    std::array<double, 3> mapV = {};
    std::vector<std::array<double, 2>> corners;
};

std::optional<PlacedFace> placeFace(const FitFace &face)
{
    const std::vector<std::array<double, 3>> &points = face.points;
    std::array<double, 3> normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const std::array<double, 3> &a = points[index];
        const std::array<double, 3> &b = points[(index + 1) % points.size()];
        normal[0] += (a[1] - b[1]) * (a[2] + b[2]);
        normal[1] += (a[2] - b[2]) * (a[0] + b[0]);
        normal[2] += (a[0] - b[0]) * (a[1] + b[1]);
    }

    const double length = std::sqrt(dot3(normal, normal));

    if (length < 1.0)
    {
        return std::nullopt;
    }

    PlacedFace placed;

    for (size_t axis = 0; axis < 3; ++axis)
    {
        placed.normal[axis] = normal[axis] / length;
    }

    placed.upright = std::abs(placed.normal[2]) <= 0.2;

    if (placed.upright)
    {
        const double horizontal = std::sqrt(placed.normal[0] * placed.normal[0] + placed.normal[1] * placed.normal[1]);
        placed.axisA = {-placed.normal[1] / horizontal, placed.normal[0] / horizontal, 0.0};
        placed.axisB = {0.0, 0.0, 1.0};
    }
    else
    {
        // East projected into the plane, and the normal crossed with it.
        const std::array<double, 3> &n = placed.normal;
        std::array<double, 3> east = {1.0 - n[0] * n[0], -n[0] * n[1], -n[0] * n[2]};
        const double eastLength = std::sqrt(dot3(east, east));

        if (eastLength < 0.1)
        {
            east = {-n[1] * n[0], 1.0 - n[1] * n[1], -n[1] * n[2]};
        }

        const double size = std::sqrt(dot3(east, east));
        placed.axisA = {east[0] / size, east[1] / size, east[2] / size};
        placed.axisB = {n[1] * placed.axisA[2] - n[2] * placed.axisA[1], n[2] * placed.axisA[0] - n[0] * placed.axisA[2],
            n[0] * placed.axisA[1] - n[1] * placed.axisA[0]};
    }

    placed.distance = dot3(placed.normal, points[0]);
    placed.box = {1e18, -1e18, 1e18, -1e18};
    std::array<std::array<double, 3>, 3> normalMatrix = {};
    std::array<double, 3> uRight = {};
    std::array<double, 3> vRight = {};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const double a = dot3(placed.axisA, points[index]);
        const double b = dot3(placed.axisB, points[index]);
        placed.corners.push_back({a, b});
        placed.box = {std::min(placed.box[0], a), std::max(placed.box[1], a), std::min(placed.box[2], b),
            std::max(placed.box[3], b)};
        const std::array<double, 3> row = {a, b, 1.0};

        for (size_t i = 0; i < 3; ++i)
        {
            for (size_t j = 0; j < 3; ++j)
            {
                normalMatrix[i][j] += row[i] * row[j];
            }

            uRight[i] += row[i] * face.texels[index][0];
            vRight[i] += row[i] * face.texels[index][1];
        }
    }

    if (placed.box[1] - placed.box[0] < 1.0 || placed.box[3] - placed.box[2] < 1.0)
    {
        return std::nullopt;
    }

    const auto determinant = [](const std::array<std::array<double, 3>, 3> &m)
    {
        return m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
    };
    const double whole = determinant(normalMatrix);

    if (std::abs(whole) < 1e-6)
    {
        return std::nullopt;
    }

    for (size_t column = 0; column < 3; ++column)
    {
        std::array<std::array<double, 3>, 3> forU = normalMatrix;
        std::array<std::array<double, 3>, 3> forV = normalMatrix;

        for (size_t row = 0; row < 3; ++row)
        {
            forU[row][column] = uRight[row];
            forV[row][column] = vRight[row];
        }

        placed.mapU[column] = determinant(forU) / whole;
        placed.mapV[column] = determinant(forV) / whole;
    }

    return placed;
}

double mapAt(const std::array<double, 3> &map, const std::array<double, 2> &point)
{
    return map[0] * point[0] + map[1] * point[1] + map[2];
}

// How far apart two extents are along one axis: below zero they overlap by that much.
double gapOf(double lowA, double highA, double lowB, double highB)
{
    return std::max(lowA - highB, lowB - highA);
}

// Faces of one texture in one plane, touching, whose pictures continue each other (the same texels per unit, offset by
// whole pictures): one surface showing the picture, as the eye reads it.
struct Surface
{
    std::string texture;
    std::vector<size_t> faces;
    bool upright = false;
    std::array<double, 4> box = {};
    // The texels shown, in the first face's frame.
    double uLow = 1e18;
    double uHigh = -1e18;
    double vLow = 1e18;
    double vHigh = -1e18;
    double across = 0.0;
    double down = 0.0;
    // The longest unbroken share of the picture shown across and down (1: whole; a picture's edge inside the
    // surface breaks it).
    double wholeAcross = 0.0;
    double wholeDown = 0.0;
};

// The longest stretch of [low, high] between multiples of `size`, over `size`.
double wholeShare(double low, double high, double size)
{
    double best = 0.0;
    double from = low;

    while (from < high - 1e-6)
    {
        const double next = std::min(high, (std::floor(from / size + 1e-6) + 1.0) * size);
        best = std::max(best, next - from);
        from = next;
    }

    return best / size;
}

// Whether a surface shows its picture whole once per storey up the wall: a picture one row high, the copies down a
// whole number (two or more) and the first starting at the picture's edge.
bool storeyStacked(const Surface &surface, const std::array<int, 2> &size)
{
    const double start = surface.vLow / size[1];
    return size[1] == FitLimits::StoreyHeight && surface.down >= 1.95
        && std::abs(surface.down - std::round(surface.down)) <= 0.05
        && std::abs(start - std::round(start)) * size[1] <= 2.0;
}

double colourDifference(const std::array<int, 3> &a, const std::array<int, 3> &b)
{
    return (std::abs(a[0] - b[0]) + std::abs(a[1] - b[1]) + std::abs(a[2] - b[2])) / 3.0;
}

std::string surfaceName(const Surface &surface, const std::vector<FitFace> &faces)
{
    std::string name = "face " + faces[surface.faces.front()].name;

    if (surface.faces.size() > 1)
    {
        name += " (+" + std::to_string(surface.faces.size() - 1) + ")";
    }

    return name;
}
}

std::vector<AuditFinding> auditTextureFit(const LoadedMap &map, const TextureFitData &data, bool measure)
{
    std::vector<AuditFinding> findings;
    const std::map<std::string, TextureClass> classes = readTextureClasses(data.classTexts);
    const std::vector<FitFace> faces = facesOf(map);
    std::vector<std::optional<PlacedFace>> placed;
    // Faces by their plane (normal and distance rounded), for the surfaces and the neighbours.
    std::map<std::array<long, 4>, std::vector<size_t>> planes;

    for (size_t index = 0; index < faces.size(); ++index)
    {
        placed.push_back(placeFace(faces[index]));

        if (placed.back())
        {
            const PlacedFace &face = *placed.back();
            planes[{std::lround(face.normal[0] * 20.0), std::lround(face.normal[1] * 20.0),
                std::lround(face.normal[2] * 20.0), std::lround(face.distance / 8.0)}].push_back(index);
        }
    }

    // The surfaces: union of touching faces of one texture whose pictures continue each other.
    std::vector<size_t> parent(faces.size());

    for (size_t index = 0; index < parent.size(); ++index)
    {
        parent[index] = index;
    }

    const std::function<size_t(size_t)> rootOf = [&](size_t index)
    {
        while (parent[index] != index)
        {
            parent[index] = parent[parent[index]];
            index = parent[index];
        }

        return index;
    };

    for (const auto &[key, members] : planes)
    {
        for (size_t first = 0; first < members.size(); ++first)
        {
            for (size_t second = first + 1; second < members.size(); ++second)
            {
                const FitFace &faceA = faces[members[first]];
                const FitFace &faceB = faces[members[second]];

                if (faceA.texture != faceB.texture)
                {
                    continue;
                }

                const PlacedFace &a = *placed[members[first]];
                const PlacedFace &b = *placed[members[second]];
                const std::array<int, 2> size = sizeOf(faceA.texture, data, classes);

                if (dot3(a.normal, b.normal) < 0.995 || std::abs(a.distance - b.distance) > FitLimits::PlaneSlack
                    || gapOf(a.box[0], a.box[1], b.box[0], b.box[1]) > FitLimits::TouchGap
                    || gapOf(a.box[2], a.box[3], b.box[2], b.box[3]) > FitLimits::TouchGap || size[0] <= 0
                    || size[1] <= 0)
                {
                    continue;
                }

                bool same = true;

                for (size_t axis = 0; axis < 2; ++axis)
                {
                    same = same && std::abs(a.mapU[axis] - b.mapU[axis]) <= 0.01 + 0.01 * std::abs(a.mapU[axis])
                        && std::abs(a.mapV[axis] - b.mapV[axis]) <= 0.01 + 0.01 * std::abs(a.mapV[axis]);
                }

                // The same picture at a point of both: offset by whole pictures.
                const std::array<double, 2> middle = {(b.box[0] + b.box[1]) * 0.5, (b.box[2] + b.box[3]) * 0.5};
                const double du = (mapAt(a.mapU, middle) - mapAt(b.mapU, middle)) / size[0];
                const double dv = (mapAt(a.mapV, middle) - mapAt(b.mapV, middle)) / size[1];

                if (same && std::abs(du - std::round(du)) * size[0] <= 2.0
                    && std::abs(dv - std::round(dv)) * size[1] <= 2.0)
                {
                    parent[rootOf(members[second])] = rootOf(members[first]);
                }
            }
        }
    }

    std::map<size_t, size_t> surfaceOfRoot;
    std::vector<Surface> surfaces;
    std::vector<std::optional<size_t>> surfaceOfFace(faces.size());

    for (size_t index = 0; index < faces.size(); ++index)
    {
        if (!placed[index])
        {
            continue;
        }

        const size_t root = rootOf(index);
        const auto [found, added] = surfaceOfRoot.emplace(root, surfaces.size());

        if (added)
        {
            Surface surface;
            surface.texture = faces[index].texture;
            surface.upright = placed[index]->upright;
            surface.box = placed[index]->box;
            surfaces.push_back(surface);
        }

        Surface &surface = surfaces[found->second];
        const PlacedFace &rootFace = *placed[root];
        const PlacedFace &face = *placed[index];
        surface.faces.push_back(index);
        surface.box = {std::min(surface.box[0], face.box[0]), std::max(surface.box[1], face.box[1]),
            std::min(surface.box[2], face.box[2]), std::max(surface.box[3], face.box[3])};

        for (const std::array<double, 2> &corner : face.corners)
        {
            const double u = mapAt(rootFace.mapU, corner);
            const double v = mapAt(rootFace.mapV, corner);
            surface.uLow = std::min(surface.uLow, u);
            surface.uHigh = std::max(surface.uHigh, u);
            surface.vLow = std::min(surface.vLow, v);
            surface.vHigh = std::max(surface.vHigh, v);
        }

        surfaceOfFace[index] = found->second;
    }

    for (Surface &surface : surfaces)
    {
        const std::array<int, 2> size = sizeOf(surface.texture, data, classes);

        if (size[0] > 0 && size[1] > 0)
        {
            surface.across = (surface.uHigh - surface.uLow) / size[0];
            surface.down = (surface.vHigh - surface.vLow) / size[1];
            surface.wholeAcross = wholeShare(surface.uLow + 0.5, surface.uHigh - 0.5, size[0]);
            surface.wholeDown = wholeShare(surface.vLow + 0.5, surface.vHigh - 0.5, size[1]);
        }
    }

    // Neighbours: upright surfaces of different textures in one plane whose faces meet along an edge; `along`
    // side by side along the wall, else one over the other.
    struct Meeting
    {
        double along = 0.0;
        double up = 0.0;
    };
    std::map<std::pair<size_t, size_t>, Meeting> meetings;

    for (const auto &[key, members] : planes)
    {
        for (size_t first = 0; first < members.size(); ++first)
        {
            for (size_t second = first + 1; second < members.size(); ++second)
            {
                const PlacedFace &a = *placed[members[first]];
                const PlacedFace &b = *placed[members[second]];
                const std::optional<size_t> surfaceA = surfaceOfFace[members[first]];
                const std::optional<size_t> surfaceB = surfaceOfFace[members[second]];

                if (!a.upright || !surfaceA || !surfaceB || *surfaceA == *surfaceB
                    || faces[members[first]].texture == faces[members[second]].texture
                    || dot3(a.normal, b.normal) < 0.995 || std::abs(a.distance - b.distance) > FitLimits::PlaneSlack)
                {
                    continue;
                }

                const double gapAlong = gapOf(a.box[0], a.box[1], b.box[0], b.box[1]);
                const double gapUp = gapOf(a.box[2], a.box[3], b.box[2], b.box[3]);
                Meeting &meeting = meetings[{std::min(*surfaceA, *surfaceB), std::max(*surfaceA, *surfaceB)}];

                if (std::abs(gapAlong) <= FitLimits::TouchGap && gapUp < -FitLimits::TouchGap)
                {
                    meeting.along += -gapUp;
                }
                else if (std::abs(gapUp) <= FitLimits::TouchGap && gapAlong < -FitLimits::TouchGap)
                {
                    meeting.up += -gapAlong;
                }
            }
        }
    }

    const auto classOf = [&classes](const std::string &texture) -> const TextureClass *
    {
        const std::map<std::string, TextureClass>::const_iterator known = classes.find(texture);
        return known != classes.end() ? &known->second : nullptr;
    };

    for (const Surface &surface : surfaces)
    {
        const TextureClass *pClass = classOf(surface.texture);
        const std::string name = surfaceName(surface, faces);
        const double width = surface.box[1] - surface.box[0];
        const double height = surface.box[3] - surface.box[2];

        if (measure)
        {
            findings.push_back({"textures.measure", "info", name + " tex " + surface.texture + " "
                    + std::to_string(sizeOf(surface.texture, data, classes)[0]) + "x"
                    + std::to_string(sizeOf(surface.texture, data, classes)[1]) + " width " + rounded(width, 1.0)
                    + " height " + rounded(height, 1.0) + " copies " + rounded(surface.across) + " x "
                    + rounded(surface.down) + " whole " + rounded(surface.wholeAcross) + " x "
                    + rounded(surface.wholeDown) + " upright " + (surface.upright ? "1" : "0") + " class "
                    + (pClass ? pClass->kind : "-") + " door " + (pClass && !pClass->door.empty() ? pClass->door : "-"),
                ""});
        }

        // Door pictures are the door check's (DOORS.md); a texture with no class, or a sliver, is not judged.
        if (pClass == nullptr || !pClass->door.empty() || surface.across <= 0.0
            || std::min(width, height) < FitLimits::MinimumSide)
        {
            continue;
        }

        const std::string where = name + " (" + surface.texture + ", " + rounded(width, 1.0) + " x "
            + rounded(height, 1.0) + ")";

        const std::array<int, 2> size = sizeOf(surface.texture, data, classes);
        const bool stacked = storeyStacked(surface, size);
        // D-41: by the texture's `storey_stack`: a module stacks rightly, an edge panel never, the rest are looked at.
        const auto stackedFinding = [&]()
        {
            if (pClass->storeyStack == "module")
            {
                return;
            }

            const bool edge = pClass->storeyStack == "edge";
            findings.push_back({"textures.storey_stacked", edge ? "error" : "warning", where + " stacks "
                    + surface.texture + ", one storey high, whole " + rounded(surface.down, 1.0) + " times up the wall"
                    + (edge ? ", but it is a footing or eaves panel meant once per wall" : ""),
                edge ? "Lay the rows above with a plain wall of the same kit and this panel once at the foot or the "
                       "eaves (`upper_walls`)."
                     : "Right for a storey panel when each storey reads as its own (a band between them, `band`); a "
                       "frieze, a window row or an end post repeated up the wall is wrong: lay the rows above with a "
                       "plain wall (`upper_walls`), or keep it with a line in the map's NOTES.md."});
        };

        if (pClass->kind == "feature")
        {
            if (surface.across <= FitLimits::RepeatedCopies && stacked && surface.wholeAcross >= FitLimits::WholeShare)
            {
                stackedFinding();
            }
            else if (surface.across > FitLimits::RepeatedCopies || surface.down > FitLimits::RepeatedCopies)
            {
                findings.push_back({"textures.feature_repeated", "error", where + " shows " + surface.texture
                        + ", a picture meant once, " + rounded(surface.across, 0.1) + " times across and "
                        + rounded(surface.down, 0.1) + " down",
                    "Lay it once over the face (a studio surface `fit: true`, or a face cut to the picture's size with "
                    "the wall's own texture round it), or choose a texture that repeats."});
            }
            else if ((width >= FitLimits::CutMinimum && surface.wholeAcross < FitLimits::WholeShare)
                || (height >= FitLimits::CutMinimum && surface.wholeDown < FitLimits::WholeShare))
            {
                findings.push_back({"textures.feature_cut", "error", where + " shows at most "
                        + rounded(std::min(surface.wholeAcross, surface.wholeDown) * 100.0, 1.0) + " % of "
                        + surface.texture + ", a picture meant once, unbroken: it is cut off or split by its own edge",
                    "Lay the whole picture once over the face (its texels from 0 to the picture's size), or "
                    "choose a texture that fits the face."});
            }
        }
        else if (pClass->kind == "trim_u" && surface.down > FitLimits::RepeatedCopies && stacked)
        {
            stackedFinding();
        }
        else if ((pClass->kind == "trim_u" && surface.down > FitLimits::RepeatedCopies)
            || (pClass->kind == "trim_v" && surface.across > FitLimits::RepeatedCopies))
        {
            const bool band = pClass->kind == "trim_u";
            findings.push_back({"textures.trim_tiled", "error", where + " repeats " + surface.texture + ", a "
                    + (band ? "band that repeats only along its width, " : "strip that repeats only up its height, ")
                    + rounded(band ? surface.down : surface.across, 0.1) + (band ? " times up the face" :
                        " times across the face"),
                band ? "Lay the band one picture high (a face of its own along the wall, the wall's texture above "
                       "and below), or choose a texture that repeats both ways."
                     : "Lay the strip one picture wide, or choose a texture that repeats both ways."});
        }
        else if ((!pClass->tiles[0] && surface.across >= FitLimits::LargeCopies)
            || (!pClass->tiles[1] && surface.down >= FitLimits::LargeCopies))
        {
            if ((pClass->tiles[0] || surface.across < FitLimits::LargeCopies) && stacked)
            {
                stackedFinding();
                continue;
            }

            findings.push_back({"textures.tile_seams", "warning", where + " repeats " + surface.texture + " "
                    + rounded(surface.across, 0.1) + " x " + rounded(surface.down, 0.1)
                    + " times, but its edges do not meet " + (!pClass->tiles[0] && !pClass->tiles[1] ? "either way"
                        : !pClass->tiles[0] ? "across" : "up and down") + ": a line shows at every repeat",
                "Choose a seamless texture for a face this large, or lay this one once."});
        }
    }

    // A picture set into a wall whose border is unlike the wall round it, and a wall switching texture family.
    std::set<size_t> borderReported;

    for (const auto &[pair, meeting] : meetings)
    {
        for (const auto &[featureIndex, wallIndex] : {pair, std::pair<size_t, size_t>{pair.second, pair.first}})
        {
            const Surface &feature = surfaces[featureIndex];
            const Surface &wall = surfaces[wallIndex];
            const TextureClass *pFeature = classOf(feature.texture);
            const TextureClass *pWall = classOf(wall.texture);

            if (pFeature == nullptr || pWall == nullptr || !pFeature->border || !pWall->border)
            {
                continue;
            }

            const double difference = colourDifference(*pFeature->border, *pWall->border);

            if (measure && featureIndex < wallIndex)
            {
                findings.push_back({"textures.measure", "info", "pair " + surfaceName(feature, faces) + " tex "
                        + feature.texture + " class " + pFeature->kind + " | " + surfaceName(wall, faces) + " tex "
                        + wall.texture + " class " + pWall->kind + " along " + rounded(meeting.along, 1.0) + " up "
                        + rounded(meeting.up, 1.0) + " diff " + rounded(difference, 1.0),
                    ""});
            }

            if (pFeature->kind == "feature" && pFeature->door.empty() && pWall->kind == "tile"
                && meeting.along + meeting.up >= FitLimits::SharedEdge && difference > FitLimits::BorderDifference
                && !borderReported.contains(featureIndex))
            {
                borderReported.insert(featureIndex);
                findings.push_back({"textures.feature_border", "warning", surfaceName(feature, faces) + " ("
                        + feature.texture + ") is set into " + wall.texture + " but its border is unlike the wall's "
                        "(colour " + rounded(difference, 1.0) + " apart)",
                    "Choose a picture painted on the wall's own stone, or frame it with a trim between them."});
            }

            if (featureIndex < wallIndex && pFeature->kind == "tile" && pWall->kind == "tile"
                && meeting.along >= 2.0 * FitLimits::SharedEdge && difference > FitLimits::FamilyDifference)
            {
                findings.push_back({"textures.family_switch", "warning", surfaceName(feature, faces) + " ("
                        + feature.texture + ") and " + surfaceName(wall, faces) + " (" + wall.texture
                        + ") meet side by side in one wall but are unlike walls (colour " + rounded(difference, 1.0)
                        + " apart)",
                    "Keep one wall texture along the wall, or put a pillar, a trim strip or a corner where it "
                    "changes."});
            }
        }
    }

    return findings;
}

std::vector<AuditFinding> auditDoorTextures(const LoadedMap &map, const TextureFitData &data, bool measure)
{
    std::vector<AuditFinding> findings;
    const std::map<std::string, TextureClass> classes = readTextureClasses(data.classTexts);
    std::vector<Leaf> leaves = leavesOf(map, classes);
    // The F2 rules (outdoor leaves) hold Xeen's maps (errors); on the shipped maps, audited with --doors, they are
    // warnings (2026-11-22: 5 lone wings, 2 parts of a picture, 3 narrow pairs over the 203 shipped maps).
    const std::string severity = map.world == "xeen" ? "error" : "warning";

    for (size_t index = 0; index < leaves.size(); ++index)
    {
        const Leaf &leaf = leaves[index];
        const std::array<int, 2> size = sizeOf(leaf.texture, data, classes);
        const std::map<std::string, TextureClass>::const_iterator known = classes.find(leaf.texture);
        const TextureClass *pClass = known != classes.end() ? &known->second : nullptr;
        const double width = leaf.front.high - leaf.front.low;
        const double height = leaf.front.top - leaf.front.bottom;
        const double across = copiesAcross(leaf, size);
        const double down = copiesDown(leaf, size);
        const Leaf *pPartner = leaf.partner ? &leaves[*leaf.partner] : nullptr;
        const bool mirrored = pPartner != nullptr && pPartner->texture == leaf.texture
            && (pPartner->uRate > 0.0) != (leaf.uRate > 0.0);

        if (measure)
        {
            findings.push_back({"doors.measure", "info", leaf.name + " tex " + leaf.texture + " "
                    + std::to_string(size[0]) + "x" + std::to_string(size[1]) + " width " + rounded(width, 1.0)
                    + " height " + rounded(height, 1.0) + " copies " + rounded(across) + " x " + rounded(down)
                    + " u " + (leaf.uRate >= 0.0 ? "+" : "-") + " class " + (pClass ? pClass->kind : "-")
                    + " door " + (pClass && !pClass->door.empty() ? pClass->door : "-") + " partner "
                    + (pPartner ? pPartner->name + " tex " + pPartner->texture + (mirrored ? " mirrored" : "")
                        : "-"),
                ""});
        }

        if (pClass == nullptr || pClass->door.empty() || size[0] <= 0)
        {
            continue;
        }

        const std::string where = leaf.name + " (" + leaf.texture + ", " + rounded(width, 1.0) + " wide)";

        // A door picture repeated across its leaf.
        if (pClass->door != "tile" && across > DoorLimits::TiledCopies)
        {
            findings.push_back({"doors.tiled", "error", where + " shows its door picture " + rounded(across, 0.1)
                    + " times across: a door picture is laid once over its leaf",
                pClass->door == "wing" || width >= DoorLimits::WideLeaf
                    ? "Make the opening two leaves (a hinged pair, or `leaves: 2`), each with one wing, the other "
                      "mirrored; or choose a door picture made for the opening's width."
                    : "Stretch the picture once over the leaf (no `tile`), or choose a picture made for its width."});
            continue;
        }

        // One wing of a double door over a wide opening on a leaf of its own.
        if (pClass->door == "wing" && pPartner == nullptr && width >= DoorLimits::WideLeaf)
        {
            findings.push_back({"doors.half_wing", "error", where + " is one leaf showing " + leaf.texture
                    + ", one wing of a double door, over the whole opening",
                "Build the door as two leaves (`kind: hinged, leaves: 2`, or a sliding `leaves: 2` with the picture "
                "mirrored on the second), or choose a door picture made for one leaf."});
            continue;
        }

        // Both leaves of a pair showing one wing the same way round.
        if (pPartner != nullptr && pPartner->texture == leaf.texture && !mirrored && pClass->door == "wing"
            && pClass->mirror < 0.85 && index < *leaf.partner)
        {
            findings.push_back({"doors.wing_unmirrored", "error", where + " and " + pPartner->name
                    + " show the wing " + leaf.texture + " the same way round: the pair reads as two left (or "
                    "two right) wings",
                "Mirror the picture on one leaf (`mirror: true` in its `pictures`; a hinged pair's `surface` does "
                "it), or give each leaf its own wing."});
        }

        // F2 (tools/xeen/door_check.py's rules): one wing hung alone on a door's leaf (the other half blank wall).
        if (leaf.outdoor && pClass->door == "wing" && pPartner == nullptr && width >= DoorLimits::LoneWing)
        {
            findings.push_back({"doors.lone_wing", severity, where + " hangs " + leaf.texture + ", one wing of a "
                    "double door, alone: the other half of the door is blank wall",
                "Make it a double door (outdoors a building door whose picture is a wing is one unless it says "
                "`leaves: 1`; `leaves: 2` on a bay 256 wide), or give it a single door's picture."});
        }

        // D-91: a door picture shows whole across its leaf: no slice of it, no half of one picture on each leaf.
        if (leaf.outdoor && (pClass->door == "single" || pClass->door == "wing") && across < DoorLimits::LeastCopies)
        {
            findings.push_back({"doors.part_picture", severity, where + " shows " + rounded(across) + " of its door "
                    "picture across: a door picture is laid whole over its leaf",
                "Each leaf of a pair shows its picture at its own width (the studio does it for a picture the "
                "texture classes know); or widen the leaf to the picture, or choose a picture made for the leaf."});
        }

        // Two leaves squeezed into one door's bay.
        if (leaf.outdoor && pPartner != nullptr && index < *leaf.partner)
        {
            const double pairWidth = std::max(leaf.front.high, pPartner->front.high)
                - std::min(leaf.front.low, pPartner->front.low);

            if (pairWidth < DoorLimits::LeastPair)
            {
                findings.push_back({"doors.narrow_pair", severity, where + " and " + pPartner->name + " are a pair "
                        "of leaves " + rounded(pairWidth, 1.0) + " wide together: a double door squeezed into one "
                        "door's bay",
                    "A double door is 256 wide (two leaves of 128): list its bay `[door, 256]`."});
            }
        }
    }

    // F2: an outdoor door centred on the steps before it (a model named `..._steps` or `..._stairs` that reaches the
    // door's wall and lies before it).
    if (map.outdoor)
    {
        std::vector<std::pair<std::string, std::array<double, 4>>> steps;

        for (const Game::OutdoorBModel &model : map.outdoor->bmodels)
        {
            const std::string name = lowerName(model.name);
            const bool named = (name.size() >= 6 && name.compare(name.size() - 6, 6, "_steps") == 0)
                || (name.size() >= 7 && name.compare(name.size() - 7, 7, "_stairs") == 0);

            if (!named || model.vertices.empty())
            {
                continue;
            }

            std::array<double, 4> box = {1e18, 1e18, -1e18, -1e18};

            for (const Game::OutdoorBModelVertex &vertex : model.vertices)
            {
                box = {std::min(box[0], double(vertex.x)), std::min(box[1], double(vertex.y)),
                    std::max(box[2], double(vertex.x)), std::max(box[3], double(vertex.y))};
            }

            steps.push_back({model.name, box});
        }

        for (size_t index = 0; index < leaves.size() && !steps.empty(); ++index)
        {
            const Leaf &leaf = leaves[index];
            const std::map<std::string, TextureClass>::const_iterator known = classes.find(leaf.texture);

            if (known == classes.end() || known->second.door.empty() || (leaf.partner && *leaf.partner < index))
            {
                continue;
            }

            const Leaf *pPartner = leaf.partner ? &leaves[*leaf.partner] : nullptr;
            const double left = std::min(leaf.front.low, pPartner ? pPartner->front.low : leaf.front.low);
            const double right = std::max(leaf.front.high, pPartner ? pPartner->front.high : leaf.front.high);
            const double middle = (left + right) * 0.5;

            for (const std::pair<std::string, std::array<double, 4>> &step : steps)
            {
                const std::array<double, 4> &box = step.second;
                double outLow = 1e18;
                double outHigh = -1e18;
                double sideLow = 1e18;
                double sideHigh = -1e18;

                for (const std::array<double, 2> &corner : std::vector<std::array<double, 2>>{{box[0], box[1]},
                         {box[2], box[1]}, {box[2], box[3]}, {box[0], box[3]}})
                {
                    const std::array<double, 3> point = {corner[0], corner[1], 0.0};
                    const double out = dot3(leaf.front.normal, point) - leaf.front.planeDistance;
                    const double side = dot3(leaf.front.along, point);
                    outLow = std::min(outLow, out);
                    outHigh = std::max(outHigh, out);
                    sideLow = std::min(sideLow, side);
                    sideHigh = std::max(sideHigh, side);
                }

                if (outLow > DoorLimits::StepsReach || outHigh < 32.0 || sideHigh < left || sideLow > right)
                {
                    continue;
                }

                const double off = middle - (sideLow + sideHigh) * 0.5;

                if (std::abs(off) > DoorLimits::StepsOffset)
                {
                    findings.push_back({"doors.off_steps", severity, leaf.name + " (" + leaf.texture + ") stands "
                            + rounded(off, 1.0) + " along its wall from the middle of " + step.first + " before it",
                        "Centre the door on its steps (the door's bay, or the steps' place)."});
                }
            }
        }
    }

    // F27: an outdoor door whose land before it rises over its sill (the game's terrain triangles), as
    // tools/xeen/town_fit_check.py `houses.buried_door` has it (pin p14 on X1: a house dug into a slope).
    if (map.outdoor && map.outdoor->heightMap.size() == map.outdoor->terrainSampleCount())
    {
        for (const Leaf &leaf : leaves)
        {
            const std::map<std::string, TextureClass>::const_iterator known = classes.find(leaf.texture);

            if (!leaf.outdoor || known == classes.end() || known->second.door.empty()
                || std::abs(leaf.front.normal[2]) > 0.1)
            {
                continue;
            }

            const double middle = (leaf.front.low + leaf.front.high) * 0.5;
            const double half = (leaf.front.high - leaf.front.low) * 0.5;
            double worst = -1.0e18;
            std::array<double, 2> place = {};

            for (const double out : {32.0, 96.0, 160.0})
            {
                for (const double side : {-0.6, 0.0, 0.6})
                {
                    const double x = leaf.front.normal[0] * (leaf.front.planeDistance + out)
                        + leaf.front.along[0] * (middle + half * side);
                    const double y = leaf.front.normal[1] * (leaf.front.planeDistance + out)
                        + leaf.front.along[1] * (middle + half * side);
                    const double rise = Game::sampleOutdoorTerrainHeight(*map.outdoor, static_cast<float>(x),
                        static_cast<float>(y)) - leaf.front.bottom;

                    if (rise > worst)
                    {
                        worst = rise;
                        place = {x, y};
                    }
                }
            }

            if (worst > DoorLimits::DoorBury)
            {
                findings.push_back({"houses.buried_door", "warning", leaf.name + " (" + leaf.texture + "): the land "
                        "before it rises " + rounded(worst, 1.0) + " over its sill at [" + rounded(place[0], 1.0)
                        + ", " + rounded(place[1], 1.0) + "]: the door is dug into a slope",
                    "Lower the land before the door to its sill (an apron, `heights` in the sketch), or raise the "
                    "house's floor; or turn the door away from the slope."});
            }
        }
    }

    return findings;
}
}
