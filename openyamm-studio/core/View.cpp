#include "core/View.h"

#include "game/FaceEnums.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/MapIdentity.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <cstring>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <tuple>

namespace OpenYAMM::Studio
{
namespace
{
std::string lowerText(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

int64_t whole(double value)
{
    return static_cast<int64_t>(std::llround(value));
}

// One face on its way into the mesh: corners, texture coordinates (texels or 0 to 1), its normal and owner.
struct PendingFace
{
    std::vector<std::array<double, 3>> positions;
    std::vector<std::array<double, 2>> uvs;
    std::array<double, 3> normal = {0.0, 0.0, 1.0};
    uint32_t owner = 0;
};

// Groups faces by texture and kind, then writes the file of view.rpc.json in a fixed order: by kind (surface, moving,
// liquid, terrain), then by texture name, the faces of a group in the order they came.
class MeshBuilder
{
public:
    MeshBuilder()
    {
        m_mesh.owners.push_back({});
    }

    uint32_t owner(const std::string &id, const std::string &file)
    {
        if (id.empty())
        {
            return 0;
        }

        const std::string key = file + "\n" + id;
        const std::map<std::string, uint32_t>::const_iterator found = m_ownerIndex.find(key);

        if (found != m_ownerIndex.end())
        {
            return found->second;
        }

        const uint32_t index = static_cast<uint32_t>(m_mesh.owners.size());
        m_mesh.owners.push_back({id, file});
        m_ownerIndex.emplace(key, index);
        return index;
    }

    void add(const std::string &texture, const std::string &kind, bool unitUv, PendingFace face)
    {
        if (face.positions.size() < 3)
        {
            return;
        }

        // Faces come in runs of one texture (a terrain row, a model's walls): the group is looked up when it changes.
        if (m_pLastGroup == nullptr || unitUv != m_lastUnitUv || texture != m_lastTexture || kind != m_lastKind)
        {
            m_pLastGroup = &m_groups[{kindRank(kind), lowerText(texture), kind, unitUv}];
            m_lastTexture = texture;
            m_lastKind = kind;
            m_lastUnitUv = unitUv;
        }

        m_pLastGroup->push_back(std::move(face));
    }

    ViewMesh finish()
    {
        std::vector<float> positions;
        std::vector<float> normals;
        std::vector<float> uvs;
        std::vector<uint32_t> indices;
        std::vector<uint32_t> triangleFaces;
        std::vector<uint32_t> faceOwners;
        bool first = true;
        size_t corners = 0;
        size_t triangles = 0;
        size_t faces = 0;

        for (const std::pair<const GroupKey, std::vector<PendingFace>> &group : m_groups)
        {
            for (const PendingFace &face : group.second)
            {
                corners += face.positions.size();
                triangles += face.positions.size() - 2;
            }

            faces += group.second.size();
        }

        positions.reserve(corners * 3);
        normals.reserve(corners * 3);
        uvs.reserve(corners * 2);
        indices.reserve(triangles * 3);
        triangleFaces.reserve(triangles);
        faceOwners.reserve(faces);

        for (const std::pair<const GroupKey, std::vector<PendingFace>> &group : m_groups)
        {
            ViewMesh::Group written;
            written.texture = std::get<1>(group.first);
            written.kind = std::get<2>(group.first);
            written.unitUv = std::get<3>(group.first);
            written.first = indices.size();

            for (const PendingFace &face : group.second)
            {
                const uint32_t base = static_cast<uint32_t>(positions.size() / 3);
                const uint32_t faceIndex = static_cast<uint32_t>(faceOwners.size());
                faceOwners.push_back(face.owner);

                for (size_t corner = 0; corner < face.positions.size(); ++corner)
                {
                    for (int axis = 0; axis < 3; ++axis)
                    {
                        const double value = face.positions[corner][static_cast<size_t>(axis)];
                        positions.push_back(static_cast<float>(value));
                        normals.push_back(static_cast<float>(face.normal[static_cast<size_t>(axis)]));
                        const int64_t rounded = whole(value);

                        if (first || rounded < m_mesh.min[static_cast<size_t>(axis)])
                        {
                            m_mesh.min[static_cast<size_t>(axis)] = rounded;
                        }

                        if (first || rounded > m_mesh.max[static_cast<size_t>(axis)])
                        {
                            m_mesh.max[static_cast<size_t>(axis)] = rounded;
                        }
                    }

                    first = false;
                    uvs.push_back(static_cast<float>(face.uvs[corner][0]));
                    uvs.push_back(static_cast<float>(face.uvs[corner][1]));
                }

                // A fan, front counter-clockwise as the corners run.
                for (uint32_t corner = 1; corner + 1 < face.positions.size(); ++corner)
                {
                    indices.push_back(base);
                    indices.push_back(base + corner);
                    indices.push_back(base + corner + 1);
                    triangleFaces.push_back(faceIndex);
                }
            }

            written.count = indices.size() - written.first;
            m_mesh.groups.push_back(written);
        }

        m_mesh.vertices = positions.size() / 3;
        m_mesh.triangles = triangleFaces.size();
        m_mesh.faces = faceOwners.size();
        appendSection(m_mesh.positions, positions);
        appendSection(m_mesh.normals, normals);
        appendSection(m_mesh.uvs, uvs);
        appendSection(m_mesh.indices, indices);
        appendSection(m_mesh.triangleFaces, triangleFaces);
        appendSection(m_mesh.faceOwners, faceOwners);
        return std::move(m_mesh);
    }

private:
    using GroupKey = std::tuple<int, std::string, std::string, bool>;

    static int kindRank(const std::string &kind)
    {
        return kind == "surface" ? 0 : kind == "moving" ? 1 : kind == "liquid" ? 2 : 3;
    }

    // Little-endian on every target the studio builds for (x86-64, arm64, wasm32).
    template <typename Value>
    void appendSection(ViewMesh::Section &section, const std::vector<Value> &values)
    {
        while (m_mesh.bytes.size() % 4 != 0)
        {
            m_mesh.bytes.push_back(0);
        }

        section.offset = m_mesh.bytes.size();
        section.count = values.size();
        const size_t size = values.size() * sizeof(Value);
        m_mesh.bytes.resize(m_mesh.bytes.size() + size);

        if (size != 0)
        {
            std::memcpy(m_mesh.bytes.data() + section.offset, values.data(), size);
        }
    }

    ViewMesh m_mesh;
    std::map<GroupKey, std::vector<PendingFace>> m_groups;
    std::map<std::string, uint32_t> m_ownerIndex;
    // The group the last face went to, by what add() was given (map entries stay where they are).
    std::vector<PendingFace> *m_pLastGroup = nullptr;
    std::string m_lastTexture;
    std::string m_lastKind;
    bool m_lastUnitUv = false;
};

// Newell's normal of a polygon, unit length (up when the polygon has no area).
std::array<double, 3> polygonNormal(const std::vector<std::array<double, 3>> &points)
{
    std::array<double, 3> normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < points.size(); ++index)
    {
        const std::array<double, 3> &current = points[index];
        const std::array<double, 3> &next = points[(index + 1) % points.size()];
        normal[0] += (current[1] - next[1]) * (current[2] + next[2]);
        normal[1] += (current[2] - next[2]) * (current[0] + next[0]);
        normal[2] += (current[0] - next[0]) * (current[1] + next[1]);
    }

    const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

    if (length <= 0.0)
    {
        return {0.0, 0.0, 1.0};
    }

    return {normal[0] / length, normal[1] / length, normal[2] / length};
}

void writePoint2(JsonWriter &writer, double x, double y)
{
    writer.beginArray();
    writer.value(whole(x));
    writer.value(whole(y));
    writer.endArray();
}

void writePoint3(JsonWriter &writer, const std::string &name, double x, double y, double z)
{
    writer.key(name);
    writer.beginArray();
    writer.value(whole(x));
    writer.value(whole(y));
    writer.value(whole(z));
    writer.endArray();
}

void writeOutline(JsonWriter &writer, const std::string &name, const std::vector<std::array<double, 2>> &outline)
{
    writer.key(name);
    writer.beginArray();

    for (const std::array<double, 2> &point : outline)
    {
        writePoint2(writer, point[0], point[1]);
    }

    writer.endArray();
}

void writeBox(JsonWriter &writer, const std::string &name, const std::array<int64_t, 3> &min,
    const std::array<int64_t, 3> &max)
{
    writer.key(name);
    writer.beginObject();
    writer.key("min");
    writer.beginArray();

    for (const int64_t value : min)
    {
        writer.value(value);
    }

    writer.endArray();
    writer.key("max");
    writer.beginArray();

    for (const int64_t value : max)
    {
        writer.value(value);
    }

    writer.endArray();
    writer.endObject();
}

// Degrees from the engine's 2048 units to a turn, whole.
int64_t degreesOfUnits(int units)
{
    return whole(static_cast<double>(units) * 360.0 / 2048.0);
}
}

void resolveOutdoorTileTextures(OutdoorView &view, const std::string &tileTableText)
{
    // The table's rows by their number (first column): texture (second) and flags (seventh).
    std::map<int, std::pair<std::string, unsigned>> rows;
    std::istringstream lines(tileTableText);

    for (std::string line; std::getline(lines, line);)
    {
        std::vector<std::string> columns;
        size_t begin = 0;

        while (begin <= line.size())
        {
            const size_t tab = line.find('\t', begin);
            columns.push_back(line.substr(begin, tab == std::string::npos ? tab : tab - begin));

            if (tab == std::string::npos)
            {
                break;
            }

            begin = tab + 1;
        }

        int row = -1;

        if (columns.size() < 7
            || std::from_chars(columns[0].data(), columns[0].data() + columns[0].size(), row).ec != std::errc())
        {
            continue;
        }

        std::string texture = columns[1];
        texture.erase(std::remove_if(texture.begin(), texture.end(), [](unsigned char character)
        {
            return std::isspace(character) != 0;
        }), texture.end());
        std::string flagsText = columns[6];
        flagsText.erase(std::remove_if(flagsText.begin(), flagsText.end(), [](unsigned char character)
        {
            return std::isspace(character) != 0;
        }), flagsText.end());
        unsigned flags = 0;
        const bool hex = flagsText.starts_with("0x") || flagsText.starts_with("0X");
        std::from_chars(flagsText.data() + (hex ? 2 : 0), flagsText.data() + flagsText.size(), flags, hex ? 16 : 10);
        rows.emplace(row, std::make_pair(lowerText(texture), flags));
    }

    // As the game resolves a cell's tile number (game/maps/TerrainTileData.cpp): below 90 a row of its own (moved
    // by the master tile's base in the default world), 90 to 233 the four tile sets of 36, the rest nothing.
    static constexpr std::array<int, 3> DirectTileLookupBases = {0, 450, 630};
    const bool remapDirect = Game::normalizeWorldId(view.world) == Game::DefaultWorldId;
    const Game::OutdoorMapData &map = view.map;

    for (int tile = 0; tile < 256; ++tile)
    {
        int row = -1;

        if (tile < 90)
        {
            row = !remapDirect || tile == 0 || map.masterTile >= DirectTileLookupBases.size() ? tile
                : DirectTileLookupBases[static_cast<size_t>(map.masterTile)] + tile;
        }
        else if (tile < 234)
        {
            const size_t set = static_cast<size_t>((tile - 90) / 36);
            row = map.masterTile >= DirectTileLookupBases.size() || set >= map.tileSetLookupIndices.size() ? tile
                : static_cast<int>(map.tileSetLookupIndices[set]) + (tile - 90) % 36;
        }

        const std::map<int, std::pair<std::string, unsigned>>::const_iterator found = rows.find(row);

        if (found != rows.end())
        {
            view.tileTextures[static_cast<size_t>(tile)] = found->second.first;
            view.tileWater[static_cast<size_t>(tile)] = (found->second.second & 0x0002u) != 0;
        }
    }
}

// The source file of an indoor face's owner: rooms and openings are rooms.yml's (a room's id is also its plan space's,
// so the file is named), the rest objects.yml's (doors, lifts, movers, switches, chests, plates, ...).
static std::string ownerFile(const std::string &owner)
{
    if (owner.empty())
    {
        return {};
    }

    return owner.rfind("room:", 0) == 0 || owner.rfind("open:", 0) == 0 ? "rooms.yml" : "objects.yml";
}

ViewMesh indoorViewMesh(const LoweredIndoorMap &lowered, const LiquidTextures &liquids)
{
    MeshBuilder builder;
    // The texture's size the compiler turns the lowering's 0-to-1 coordinates into texels with: its material's
    // (the first surface that used the texture).
    std::map<std::string, std::array<double, 2>> materialSizes;

    for (const Editor::EditorIndoorGeometryMaterialMetadata &material : lowered.metadata.materials)
    {
        materialSizes.emplace(lowerText(material.texture),
            std::array<double, 2>{static_cast<double>(material.textureWidth),
                static_cast<double>(material.textureHeight)});
    }

    std::set<std::string> invisibleNodes;

    for (const Editor::EditorIndoorGeometrySurfaceMetadata &surface : lowered.metadata.surfaces)
    {
        if (std::find(surface.flags.begin(), surface.flags.end(), "invisible") != surface.flags.end())
        {
            invisibleNodes.insert(surface.sourceNodeName);
        }
    }

    for (const GlbNode &node : lowered.nodes)
    {
        // Portals are not drawn; markers stand for things the views draw as glyphs.
        if (node.name.rfind("PORTAL_", 0) == 0 || node.name.rfind("DECOR_", 0) == 0
            || node.name.rfind("LIGHT_", 0) == 0 || node.name.rfind("SPAWN_", 0) == 0
            || invisibleNodes.contains(node.name))
        {
            continue;
        }

        const bool moving = node.name.rfind("MECH_", 0) == 0;

        for (const GlbFace &face : node.faces)
        {
            PendingFace pending;
            const std::string texture = lowerText(face.material);
            const std::map<std::string, std::array<double, 2>>::const_iterator size = materialSizes.find(texture);
            const std::array<double, 2> scale = size != materialSizes.end() ? size->second
                : std::array<double, 2>{128.0, 128.0};

            for (size_t corner = 0; corner < face.positions.size(); ++corner)
            {
                // Whole units, as the compiler stores the corners.
                pending.positions.push_back({
                    static_cast<double>(std::lround(face.positions[corner][0])),
                    static_cast<double>(std::lround(face.positions[corner][1])),
                    static_cast<double>(std::lround(face.positions[corner][2]))});
                pending.uvs.push_back({face.uvs[corner][0] * scale[0], face.uvs[corner][1] * scale[1]});
            }

            pending.normal = polygonNormal(pending.positions);
            pending.owner = builder.owner(face.owner, ownerFile(face.owner));
            const std::string kind = liquids.matches(texture) ? "liquid" : moving ? "moving" : "surface";
            builder.add(texture, kind, false, std::move(pending));
        }
    }

    return builder.finish();
}

ViewMesh shippedIndoorViewMesh(const Game::IndoorMapData &map, const LiquidTextures &liquids)
{
    MeshBuilder builder;

    for (const Game::IndoorFace &face : map.faces)
    {
        if (face.isPortal || Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
            || face.vertexIndices.size() < 3)
        {
            continue;
        }

        PendingFace pending;
        bool complete = true;

        for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
        {
            const uint16_t index = face.vertexIndices[corner];

            if (index >= map.vertices.size())
            {
                complete = false;
                break;
            }

            const Game::IndoorVertex &vertex = map.vertices[index];
            pending.positions.push_back({static_cast<double>(vertex.x), static_cast<double>(vertex.y),
                static_cast<double>(vertex.z)});
            const double u = corner < face.textureUs.size() ? face.textureUs[corner] : 0.0;
            const double v = corner < face.textureVs.size() ? face.textureVs[corner] : 0.0;
            pending.uvs.push_back({u + face.textureDeltaU, v + face.textureDeltaV});
        }

        if (!complete)
        {
            continue;
        }

        // The stored plane says where the front is (a face without one runs counter-clockwise from its front).
        const std::array<double, 3> wound = polygonNormal(pending.positions);

        if (face.planeNormal)
        {
            const std::array<double, 3> plane = {(*face.planeNormal)[0] / 65536.0, (*face.planeNormal)[1] / 65536.0,
                (*face.planeNormal)[2] / 65536.0};

            if (wound[0] * plane[0] + wound[1] * plane[1] + wound[2] * plane[2] < 0.0)
            {
                std::reverse(pending.positions.begin(), pending.positions.end());
                std::reverse(pending.uvs.begin(), pending.uvs.end());
            }
        }

        pending.normal = polygonNormal(pending.positions);
        pending.owner = builder.owner("sector:" + std::to_string(face.roomNumber), "");
        const std::string texture = lowerText(face.textureName);
        builder.add(texture, liquids.matches(texture) ? "liquid" : "surface", false, std::move(pending));
    }

    return builder.finish();
}

ViewMesh outdoorViewMesh(const OutdoorView &view, const LiquidTextures &liquids)
{
    MeshBuilder builder;
    const Game::OutdoorMapData &map = view.map;
    const int width = Game::OutdoorMapData::TerrainWidth;
    const int height = Game::OutdoorMapData::TerrainHeight;
    const double tile = Game::OutdoorMapData::TerrainTileSize;

    if (map.heightMap.size() >= static_cast<size_t>(width * height)
        && map.tileMap.size() >= static_cast<size_t>(width * height))
    {
        // Liquid or terrain by tile number (the liquids table asked once per tile, not once per cell).
        std::array<std::string, 256> tileKinds;

        for (size_t tileNumber = 0; tileNumber < tileKinds.size(); ++tileNumber)
        {
            tileKinds[tileNumber] = liquids.matches(view.tileTextures[tileNumber]) ? "liquid" : "terrain";
        }

        const auto corner = [&map, width, tile](int gridX, int gridY)
        {
            return std::array<double, 3>{(gridX - 64) * tile, (64 - gridY) * tile,
                static_cast<double>(map.heightMap[static_cast<size_t>(gridY * width + gridX)])
                    * Game::OutdoorMapData::TerrainHeightScale};
        };

        // Each cell between four grid points, cut along its diagonal from the north-west to the south-east corner
        // as the game samples it; both halves face up.
        for (int gridY = 0; gridY + 1 < height; ++gridY)
        {
            for (int gridX = 0; gridX + 1 < width; ++gridX)
            {
                const uint8_t tileNumber = map.tileMap[static_cast<size_t>(gridY * width + gridX)];
                const std::string &texture = view.tileTextures[tileNumber];
                const std::array<double, 3> northWest = corner(gridX, gridY);
                const std::array<double, 3> northEast = corner(gridX + 1, gridY);
                const std::array<double, 3> southWest = corner(gridX, gridY + 1);
                const std::array<double, 3> southEast = corner(gridX + 1, gridY + 1);
                const std::string &kind = tileKinds[tileNumber];

                for (const std::array<std::array<double, 3>, 3> &triangle :
                     {std::array<std::array<double, 3>, 3>{northWest, southEast, northEast},
                         std::array<std::array<double, 3>, 3>{northWest, southWest, southEast}})
                {
                    PendingFace face;
                    face.positions.reserve(3);
                    face.uvs.reserve(3);

                    for (const std::array<double, 3> &point : triangle)
                    {
                        face.positions.push_back(point);
                        face.uvs.push_back({(point[0] - northWest[0]) / tile, (northWest[1] - point[1]) / tile});
                    }

                    face.normal = polygonNormal(face.positions);
                    builder.add(texture, kind, true, std::move(face));
                }
            }
        }
    }

    for (const Game::OutdoorBModel &model : map.bmodels)
    {
        const uint32_t owner = builder.owner(model.name, model.name.empty() ? "" : "sketch.yml");

        for (const Game::OutdoorBModelFace &face : model.faces)
        {
            if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
                || face.vertexIndices.size() < 3)
            {
                continue;
            }

            PendingFace pending;
            bool complete = true;

            for (size_t corner = 0; corner < face.vertexIndices.size(); ++corner)
            {
                const uint16_t index = face.vertexIndices[corner];

                if (index >= model.vertices.size())
                {
                    complete = false;
                    break;
                }

                const Game::OutdoorBModelVertex &vertex = model.vertices[index];
                pending.positions.push_back({static_cast<double>(vertex.x), static_cast<double>(vertex.y),
                    static_cast<double>(vertex.z)});
                const double u = corner < face.textureUs.size() ? face.textureUs[corner] : 0.0;
                const double v = corner < face.textureVs.size() ? face.textureVs[corner] : 0.0;
                pending.uvs.push_back({u + face.textureDeltaU, v + face.textureDeltaV});
            }

            if (!complete)
            {
                continue;
            }

            // The face's plane says where its front is: the corners are turned to run counter-clockwise from it.
            std::array<double, 3> plane = {face.planeNormalX / 65536.0, face.planeNormalY / 65536.0,
                face.planeNormalZ / 65536.0};
            const std::array<double, 3> wound = polygonNormal(pending.positions);

            if (wound[0] * plane[0] + wound[1] * plane[1] + wound[2] * plane[2] < 0.0)
            {
                std::reverse(pending.positions.begin(), pending.positions.end());
                std::reverse(pending.uvs.begin(), pending.uvs.end());
            }

            const double length = std::sqrt(plane[0] * plane[0] + plane[1] * plane[1] + plane[2] * plane[2]);
            pending.normal = length > 0.0 ? std::array<double, 3>{plane[0] / length, plane[1] / length,
                plane[2] / length} : polygonNormal(pending.positions);
            pending.owner = owner;
            const std::string texture = lowerText(face.textureName);
            builder.add(texture, liquids.matches(texture) ? "liquid" : "surface", false, std::move(pending));
        }
    }

    return builder.finish();
}

namespace
{
// How a door's, lift's or mover's faces move (S5b2: the 3D view's travel scrubber), one per mechanism of the object:
// the middle of its faces as the view mesh draws them (closed, at its start) and the shift from there to open (to its
// end). Whether the map starts it open.
struct LayoutMove
{
    std::array<double, 3> at = {};
    std::array<double, 3> by = {};
    bool startsOpen = false;
};

std::map<std::string, std::vector<LayoutMove>> layoutMoves(const LoweredIndoorMap &lowered)
{
    std::map<std::string, const GlbNode *> nodes;

    for (const GlbNode &node : lowered.nodes)
    {
        nodes.emplace(node.name, &node);
    }

    std::map<std::string, std::vector<LayoutMove>> moves;

    for (const Editor::EditorIndoorGeometryMechanismMetadata &mechanism : lowered.metadata.mechanisms)
    {
        std::string owner;
        std::array<double, 3> sum = {};
        size_t corners = 0;

        for (const std::string &name : mechanism.sourceNodeNames)
        {
            const std::map<std::string, const GlbNode *>::const_iterator node = nodes.find(name);

            if (node == nodes.end())
            {
                continue;
            }

            for (const GlbFace &face : node->second->faces)
            {
                if (owner.empty() && !face.owner.empty())
                {
                    owner = face.owner.substr(0, face.owner.find('/'));
                }

                for (const std::array<float, 3> &position : face.positions)
                {
                    sum = {sum[0] + position[0], sum[1] + position[1], sum[2] + position[2]};
                    ++corners;
                }
            }
        }

        if (owner.empty() || corners == 0 || !mechanism.moveAxis)
        {
            continue;
        }

        // The axis points from open to closed (the source pose is closed): open lies against it.
        const double length = mechanism.moveLength ? static_cast<double>(*mechanism.moveLength)
            : mechanism.moveDistance ? static_cast<double>(*mechanism.moveDistance) : 0.0;
        const std::array<float, 3> &axis = *mechanism.moveAxis;
        LayoutMove move;
        move.at = {sum[0] / static_cast<double>(corners), sum[1] / static_cast<double>(corners),
            sum[2] / static_cast<double>(corners)};
        move.by = {-axis[0] * length, -axis[1] * length, -axis[2] * length};
        move.startsOpen = mechanism.initialState == "open";
        moves[owner].push_back(move);
    }

    return moves;
}

void writeMoves(JsonWriter &writer, const std::vector<LayoutMove> &moves, const LoweredDoor *pHinged)
{
    if (moves.empty())
    {
        return;
    }

    writer.field("starts_open", moves.front().startsOpen);
    writer.key("moves");
    writer.beginArray();

    for (const LayoutMove &move : moves)
    {
        writer.beginObject();
        writePoint3(writer, "at", move.at[0], move.at[1], move.at[2]);

        if (pHinged != nullptr)
        {
            writePoint3(writer, "pivot", pHinged->pivot[0], pHinged->pivot[1], pHinged->pivot[2]);
            writer.field("degrees", whole(pHinged->openDegrees));
        }
        else
        {
            writePoint3(writer, "by", move.by[0], move.by[1], move.by[2]);
        }

        writer.endObject();
    }

    writer.endArray();
}
}

void writeIndoorLayout(JsonWriter &writer, const LoweredIndoorMap &lowered)
{
    const std::map<std::string, std::vector<LayoutMove>> moves = layoutMoves(lowered);
    const std::vector<LayoutMove> none;
    const auto movesOf = [&moves, &none](const std::string &id) -> const std::vector<LayoutMove> &
    {
        const std::map<std::string, std::vector<LayoutMove>>::const_iterator found = moves.find(id);
        return found == moves.end() ? none : found->second;
    };

    std::array<int64_t, 3> min = {0, 0, 0};
    std::array<int64_t, 3> max = {0, 0, 0};
    bool first = true;
    const auto widen = [&min, &max, &first](double x, double y, double z)
    {
        const std::array<int64_t, 3> point = {whole(x), whole(y), whole(z)};

        for (size_t axis = 0; axis < 3; ++axis)
        {
            min[axis] = first ? point[axis] : std::min(min[axis], point[axis]);
            max[axis] = first ? point[axis] : std::max(max[axis], point[axis]);
        }

        first = false;
    };

    for (const LoweredRoom &room : lowered.rooms)
    {
        for (const std::array<double, 2> &point : room.outline)
        {
            widen(point[0], point[1], std::min(room.floor, room.sloped ? room.floorTo : room.floor));
            widen(point[0], point[1], std::max(room.ceiling, room.ceilingSloped ? room.ceilingTo : room.ceiling));
        }
    }

    writeBox(writer, "bounds", min, max);
    writer.key("rooms");
    writer.beginArray();

    for (const LoweredRoom &room : lowered.rooms)
    {
        writer.beginObject();
        writer.field("id", room.id);
        writer.field("sector", static_cast<int64_t>(room.sector));
        writeOutline(writer, "outline", room.outline);
        writer.field("floor", whole(room.floor));
        writer.field("ceiling", whole(room.ceiling));

        if (room.sloped && room.climb.empty() && room.floorMesh.points.empty())
        {
            writer.field("floor_to", whole(room.floorTo));
        }

        if (room.ceilingSloped && room.climb.empty() && room.ceilingMesh.points.empty())
        {
            writer.field("ceiling_to", whole(room.ceilingTo));
        }

        if (!room.floorRegions.empty())
        {
            writer.key("levels");
            writer.beginArray();

            for (const std::pair<std::vector<std::array<double, 2>>, double> &region : room.floorRegions)
            {
                writer.beginObject();
                writeOutline(writer, "outline", region.first);
                writer.field("height", whole(region.second));
                writer.endObject();
            }

            writer.endArray();
        }

        writer.endObject();
    }

    writer.endArray();
    writer.key("openings");
    writer.beginArray();

    for (const LoweredOpening &opening : lowered.openings)
    {
        if (opening.fromRoom >= lowered.rooms.size() || opening.toRoom >= lowered.rooms.size())
        {
            continue;
        }

        const LoweredRoom &from = lowered.rooms[opening.fromRoom];
        writer.beginObject();
        writer.field("id", opening.id);
        writer.field("from", from.id);
        writer.field("to", lowered.rooms[opening.toRoom].id);

        if (opening.inFloor)
        {
            writeOutline(writer, "outline", opening.outline);
        }
        else if (opening.fromEdge < from.outline.size())
        {
            const std::array<double, 2> &start = from.outline[opening.fromEdge];
            const std::array<double, 2> &end = from.outline[(opening.fromEdge + 1) % from.outline.size()];
            const double length = std::hypot(end[0] - start[0], end[1] - start[1]);
            const double dx = length > 0.0 ? (end[0] - start[0]) / length : 0.0;
            const double dy = length > 0.0 ? (end[1] - start[1]) / length : 0.0;
            writer.key("a");
            writePoint2(writer, start[0] + dx * opening.fromLow, start[1] + dy * opening.fromLow);
            writer.key("b");
            writePoint2(writer, start[0] + dx * opening.fromHigh, start[1] + dy * opening.fromHigh);
        }

        writer.field("bottom", whole(opening.bottom));
        writer.field("top", whole(opening.top));
        writer.endObject();
    }

    writer.endArray();
    writer.key("doors");
    writer.beginArray();

    for (const LoweredDoor &door : lowered.doors)
    {
        writer.beginObject();
        writer.field("id", door.id);
        writer.field("opening", door.opening < lowered.openings.size() ? lowered.openings[door.opening].id
            : std::string());
        writer.field("hinged", door.hinged);
        writer.field("leaves", static_cast<int64_t>(door.secondDoorId > 0 ? 2 : 1));
        writeMoves(writer, movesOf(door.id), door.hinged ? &door : nullptr);
        writer.endObject();
    }

    writer.endArray();
    writer.key("lifts");
    writer.beginArray();

    for (const LoweredLift &lift : lowered.lifts)
    {
        writer.beginObject();
        writer.field("id", lift.id);
        writer.field("mover", lift.mover);
        writeMoves(writer, movesOf(lift.id), nullptr);
        writer.endObject();
    }

    writer.endArray();
    writer.key("things");
    writer.beginArray();
    const auto thing = [&writer](const std::string &id, const char *pKind, const std::array<double, 3> &at,
        const std::string &name)
    {
        writer.beginObject();
        writer.field("id", id);
        writer.field("kind", pKind);
        writePoint3(writer, "at", at[0], at[1], at[2]);

        if (!name.empty())
        {
            writer.field("name", name);
        }
    };

    for (const LoweredChest &chest : lowered.chests)
    {
        thing(chest.id, "chest", chest.position, "");
        writer.endObject();
    }

    for (const LoweredMonster &monster : lowered.monsters)
    {
        thing(monster.id, "monster", monster.position, monster.displayName.empty() ? monster.name
            : monster.displayName);
        writer.field("radius", static_cast<int64_t>(std::max(monster.radius, 0)));
        writer.field("height", static_cast<int64_t>(std::max(monster.height, 0)));
        writer.field("facing", degreesOfUnits(monster.yawUnits));
        writer.endObject();
    }

    for (const LoweredItem &item : lowered.items)
    {
        thing(item.id, "item", item.position, "");
        writer.endObject();
    }

    for (const LoweredPlaced &placed : lowered.placed)
    {
        thing(placed.id, placed.kind == "decoration" ? "decoration" : placed.kind == "light" ? "light"
            : placed.kind == "switch" ? "switch" : placed.kind == "exit" ? "exit" : "spawn", placed.position, placed.name);

        if (placed.facing)
        {
            writer.field("facing", static_cast<int64_t>(*placed.facing));
        }

        writer.endObject();
    }

    for (const LoweredAmbientSound &sound : lowered.ambientSounds)
    {
        thing("sound:" + std::to_string(sound.key), "sound", sound.position, sound.sound);
        writer.endObject();
    }

    for (const LoweredLadder &ladder : lowered.ladders)
    {
        thing(ladder.name, "ladder", ladder.bottom, "");
        writer.field("facing", whole(ladder.facingDegrees));
        writer.endObject();
    }

    writer.endArray();

    if (lowered.start)
    {
        writer.key("start");
        writer.beginObject();
        writePoint3(writer, "at", lowered.start->position[0], lowered.start->position[1], lowered.start->position[2]);
        writer.field("facing", static_cast<int64_t>(lowered.start->directionDegrees));
        writer.endObject();
    }
}

void writeOutdoorLayout(JsonWriter &writer, const OutdoorView &view)
{
    const Game::OutdoorMapData &map = view.map;
    const int width = Game::OutdoorMapData::TerrainWidth;
    const int height = Game::OutdoorMapData::TerrainHeight;
    const int64_t half = static_cast<int64_t>(64) * Game::OutdoorMapData::TerrainTileSize;
    int64_t lowest = 0;
    int64_t highest = 0;

    for (size_t index = 0; index < map.heightMap.size(); ++index)
    {
        const int64_t value = static_cast<int64_t>(map.heightMap[index]) * Game::OutdoorMapData::TerrainHeightScale;
        lowest = index == 0 ? value : std::min(lowest, value);
        highest = index == 0 ? value : std::max(highest, value);
    }

    for (const Game::OutdoorBModel &model : map.bmodels)
    {
        highest = std::max<int64_t>(highest, model.maxZ);
        lowest = std::min<int64_t>(lowest, model.minZ);
    }

    writeBox(writer, "bounds", {-half, -half, lowest}, {half, half, highest});
    writer.key("rooms");
    writer.beginArray();
    writer.endArray();
    writer.key("openings");
    writer.beginArray();
    writer.endArray();
    writer.key("doors");
    writer.beginArray();
    writer.endArray();
    writer.key("lifts");
    writer.beginArray();
    writer.endArray();
    writer.key("things");
    writer.beginArray();

    for (size_t index = 0; index < map.entities.size(); ++index)
    {
        const Game::OutdoorEntity &entity = map.entities[index];
        writer.beginObject();
        writer.field("id", "entity:" + std::to_string(index));
        writer.field("kind", "decoration");
        writePoint3(writer, "at", entity.x, entity.y, entity.z);

        if (!entity.name.empty())
        {
            writer.field("name", lowerText(entity.name));
        }

        writer.field("facing", static_cast<int64_t>(entity.facing));
        writer.endObject();
    }

    for (size_t index = 0; index < map.spawns.size(); ++index)
    {
        const Game::OutdoorSpawn &spawn = map.spawns[index];
        writer.beginObject();
        writer.field("id", "spawn:" + std::to_string(index));
        writer.field("kind", "spawn");
        writePoint3(writer, "at", spawn.x, spawn.y, spawn.z);
        writer.field("radius", static_cast<int64_t>(spawn.radius));
        writer.endObject();
    }

    writer.endArray();
    writer.key("land");
    writer.beginObject();
    writer.field("size", static_cast<int64_t>(width));
    writer.field("cell", static_cast<int64_t>(Game::OutdoorMapData::TerrainTileSize));
    writer.field("height_unit", static_cast<int64_t>(Game::OutdoorMapData::TerrainHeightScale));
    writer.key("heights");
    writer.beginArray();

    for (int index = 0; index < width * height; ++index)
    {
        writer.value(static_cast<int64_t>(
            static_cast<size_t>(index) < map.heightMap.size() ? map.heightMap[static_cast<size_t>(index)] : 0));
    }

    writer.endArray();
    writer.key("water");
    writer.beginArray();

    for (int index = 0; index < width * height; ++index)
    {
        const bool water = static_cast<size_t>(index) < map.tileMap.size()
            && view.tileWater[map.tileMap[static_cast<size_t>(index)]];
        writer.value(static_cast<int64_t>(water ? 1 : 0));
    }

    writer.endArray();
    writer.endObject();
    writer.key("models");
    writer.beginArray();

    for (const Game::OutdoorBModel &model : map.bmodels)
    {
        writer.beginObject();
        writer.field("id", model.name);
        writePoint3(writer, "min", model.minX, model.minY, model.minZ);
        writePoint3(writer, "max", model.maxX, model.maxY, model.maxZ);
        writer.endObject();
    }

    writer.endArray();

    if (view.hasStart)
    {
        writer.key("start");
        writer.beginObject();
        writePoint3(writer, "at", view.start[0], view.start[1], view.start[2]);
        writer.field("facing", degreesOfUnits(view.startFacing));
        writer.endObject();
    }
}
}
