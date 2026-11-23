#include "core/MapExport.h"

#include "game/indoor/IndoorMapData.h"
#include "game/outdoor/OutdoorMapData.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <fstream>

namespace OpenYAMM::Studio
{
namespace
{
std::string lowerExtension(const std::filesystem::path &path)
{
    std::string extension = path.extension().string();
    std::transform(
        extension.begin(),
        extension.end(),
        extension.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    return extension;
}

template <typename Number>
void numberArray(JsonWriter &writer, std::string_view name, const std::vector<Number> &values)
{
    writer.key(name);
    writer.beginArray();

    for (const Number number : values)
    {
        writer.value(static_cast<int64_t>(number));
    }

    writer.endArray();
}

void triple(JsonWriter &writer, std::string_view name, int64_t x, int64_t y, int64_t z)
{
    writer.key(name);
    writer.beginArray();
    writer.value(x);
    writer.value(y);
    writer.value(z);
    writer.endArray();
}

template <typename Entity>
void writeEntity(JsonWriter &writer, const Entity &entity)
{
    writer.beginObject();
    writer.field("name", entity.name);
    writer.field("decoration_list_id", entity.decorationListId);
    writer.field("ai_attributes", entity.aiAttributes);
    triple(writer, "position", entity.x, entity.y, entity.z);
    writer.field("facing", entity.facing);
    writer.field("event_id_primary", entity.eventIdPrimary);
    writer.field("event_id_secondary", entity.eventIdSecondary);
    writer.field("variable_primary", entity.variablePrimary);
    writer.field("variable_secondary", entity.variableSecondary);
    writer.field("special_trigger", entity.specialTrigger);
    writer.endObject();
}

template <typename Spawn>
void writeSpawn(JsonWriter &writer, const Spawn &spawn)
{
    writer.beginObject();
    triple(writer, "position", spawn.x, spawn.y, spawn.z);
    writer.field("radius", spawn.radius);
    writer.field("type_id", spawn.typeId);
    writer.field("index", spawn.index);
    writer.field("attributes", spawn.attributes);
    writer.field("group", spawn.group);
    writer.endObject();
}

template <typename Node>
void writeBspNodes(JsonWriter &writer, const std::vector<Node> &nodes)
{
    writer.key("bsp_nodes");
    writer.beginArray();

    for (const Node &node : nodes)
    {
        writer.beginArray();
        writer.value(node.front);
        writer.value(node.back);
        writer.value(node.faceIdOffset);
        writer.value(node.faceCount);
        writer.endArray();
    }

    writer.endArray();
}

void exportOutdoor(const Game::OutdoorMapData &map, const MapExportOptions &options, JsonWriter &writer)
{
    writer.beginObject();
    writer.field("kind", "outdoor");
    writer.field("version", map.version);
    writer.field("name", map.name);
    writer.field("file_name", map.fileName);
    writer.field("description", map.description);
    writer.field("sky_texture", map.skyTexture);
    writer.field("ground_tileset", map.groundTilesetName);
    writer.field("master_tile", map.masterTile);
    writer.key("tile_set_lookup");
    writer.beginArray();

    for (const uint16_t index : map.tileSetLookupIndices)
    {
        writer.value(index);
    }

    writer.endArray();
    writer.key("terrain");
    writer.beginObject();
    writer.field("width", Game::OutdoorMapData::TerrainWidth);
    writer.field("height", Game::OutdoorMapData::TerrainHeight);
    writer.field("tile_size", Game::OutdoorMapData::TerrainTileSize);
    writer.field("height_scale", Game::OutdoorMapData::TerrainHeightScale);
    writer.field("min_height_sample", map.minHeightSample);
    writer.field("max_height_sample", map.maxHeightSample);
    writer.field("unique_tile_count", static_cast<uint64_t>(map.uniqueTileCount));

    if (!options.summaryOnly)
    {
        numberArray(writer, "height_map", map.heightMap);
        numberArray(writer, "tile_map", map.tileMap);
        numberArray(writer, "attribute_map", map.attributeMap);
    }

    if (!options.voidRects.empty())
    {
        // Where the world ends (U-12): the scene's cell rectangles, inclusive.
        writer.key("void");
        writer.beginArray();

        for (const std::array<int, 4> &rect : options.voidRects)
        {
            writer.beginArray();

            for (const int64_t value : rect)
            {
                writer.value(value);
            }

            writer.endArray();
        }

        writer.endArray();
    }

    writer.endObject();
    writer.key("counts");
    writer.beginObject();
    writer.field("bmodels", static_cast<uint64_t>(map.bmodels.size()));
    writer.field("entities", static_cast<uint64_t>(map.entities.size()));
    writer.field("spawns", static_cast<uint64_t>(map.spawns.size()));
    uint64_t faceCount = 0;
    uint64_t vertexCount = 0;

    for (const Game::OutdoorBModel &bmodel : map.bmodels)
    {
        faceCount += bmodel.faces.size();
        vertexCount += bmodel.vertices.size();
    }

    writer.field("bmodel_faces", faceCount);
    writer.field("bmodel_vertices", vertexCount);
    writer.endObject();

    writer.key("bmodels");
    writer.beginArray();

    for (const Game::OutdoorBModel &bmodel : map.bmodels)
    {
        writer.beginObject();
        writer.field("name", bmodel.name);
        writer.field("secondary_name", bmodel.secondaryName);
        triple(writer, "position", bmodel.positionX, bmodel.positionY, bmodel.positionZ);
        triple(writer, "min", bmodel.minX, bmodel.minY, bmodel.minZ);
        triple(writer, "max", bmodel.maxX, bmodel.maxY, bmodel.maxZ);
        triple(writer, "bounding_center", bmodel.boundingCenterX, bmodel.boundingCenterY, bmodel.boundingCenterZ);
        writer.field("bounding_radius", bmodel.boundingRadius);
        writer.field("vertex_count", static_cast<uint64_t>(bmodel.vertices.size()));
        writer.field("face_count", static_cast<uint64_t>(bmodel.faces.size()));

        if (!options.summaryOnly)
        {
            writer.key("vertices");
            writer.beginArray();

            for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
            {
                writer.beginArray();
                writer.value(vertex.x);
                writer.value(vertex.y);
                writer.value(vertex.z);
                writer.endArray();
            }

            writer.endArray();
            writer.key("faces");
            writer.beginArray();

            for (const Game::OutdoorBModelFace &face : bmodel.faces)
            {
                writer.beginObject();
                writer.field("texture", face.textureName);
                writer.field("attributes", face.attributes);
                numberArray(writer, "vertices", face.vertexIndices);
                numberArray(writer, "texture_us", face.textureUs);
                numberArray(writer, "texture_vs", face.textureVs);
                triple(writer, "plane_normal", face.planeNormalX, face.planeNormalY, face.planeNormalZ);
                writer.field("plane_distance", face.planeDistance);
                writer.field("bitmap_index", face.bitmapIndex);
                writer.field("texture_delta_u", face.textureDeltaU);
                writer.field("texture_delta_v", face.textureDeltaV);
                writer.field("cog_number", face.cogNumber);
                writer.field("cog_triggered", face.cogTriggeredNumber);
                writer.field("cog_trigger", face.cogTrigger);
                writer.field("polygon_type", face.polygonType);
                writer.field("shade", face.shade);
                writer.field("visibility", face.visibility);
                writer.endObject();
            }

            writer.endArray();
            writeBspNodes(writer, bmodel.bspNodes);
        }

        writer.endObject();
    }

    writer.endArray();
    writer.key("entities");
    writer.beginArray();

    for (const Game::OutdoorEntity &entity : map.entities)
    {
        writeEntity(writer, entity);
    }

    writer.endArray();
    writer.key("spawns");
    writer.beginArray();

    for (const Game::OutdoorSpawn &spawn : map.spawns)
    {
        writeSpawn(writer, spawn);
    }

    writer.endArray();

    if (!options.summaryOnly)
    {
        numberArray(writer, "decoration_pid_list", map.decorationPidList);
        numberArray(writer, "decoration_map", map.decorationMap);
    }

    writer.endObject();
}

void exportIndoor(const Game::IndoorMapData &map, const MapExportOptions &options, JsonWriter &writer)
{
    writer.beginObject();
    writer.field("kind", "indoor");
    writer.field("version", map.version);
    writer.key("counts");
    writer.beginObject();
    writer.field("vertices", static_cast<uint64_t>(map.vertices.size()));
    writer.field("faces", static_cast<uint64_t>(map.faces.size()));
    writer.field("sectors", static_cast<uint64_t>(map.sectors.size()));
    writer.field("entities", static_cast<uint64_t>(map.entities.size()));
    writer.field("lights", static_cast<uint64_t>(map.lights.size()));
    writer.field("spawns", static_cast<uint64_t>(map.spawns.size()));
    writer.field("bsp_nodes", static_cast<uint64_t>(map.bspNodes.size()));
    writer.field("outlines", static_cast<uint64_t>(map.outlines.size()));
    writer.field("doors", map.doorCount);
    uint64_t portalCount = 0;

    for (const Game::IndoorFace &face : map.faces)
    {
        portalCount += face.isPortal ? 1 : 0;
    }

    writer.field("portal_faces", portalCount);
    writer.endObject();

    if (!map.vertices.empty())
    {
        Game::IndoorVertex minimum = map.vertices.front();
        Game::IndoorVertex maximum = map.vertices.front();

        for (const Game::IndoorVertex &vertex : map.vertices)
        {
            minimum.x = std::min(minimum.x, vertex.x);
            minimum.y = std::min(minimum.y, vertex.y);
            minimum.z = std::min(minimum.z, vertex.z);
            maximum.x = std::max(maximum.x, vertex.x);
            maximum.y = std::max(maximum.y, vertex.y);
            maximum.z = std::max(maximum.z, vertex.z);
        }

        writer.key("bounds");
        writer.beginObject();
        triple(writer, "min", minimum.x, minimum.y, minimum.z);
        triple(writer, "max", maximum.x, maximum.y, maximum.z);
        writer.endObject();
    }

    if (!options.summaryOnly)
    {
        writer.key("vertices");
        writer.beginArray();

        for (const Game::IndoorVertex &vertex : map.vertices)
        {
            writer.beginArray();
            writer.value(vertex.x);
            writer.value(vertex.y);
            writer.value(vertex.z);
            writer.endArray();
        }

        writer.endArray();
        writer.key("faces");
        writer.beginArray();

        for (const Game::IndoorFace &face : map.faces)
        {
            writer.beginObject();
            writer.field("texture", face.textureName);
            writer.field("attributes", face.attributes);
            writer.field("is_portal", face.isPortal);
            numberArray(writer, "vertices", face.vertexIndices);
            numberArray(writer, "texture_us", face.textureUs);
            numberArray(writer, "texture_vs", face.textureVs);

            if (face.planeNormal)
            {
                triple(writer, "plane_normal", (*face.planeNormal)[0], (*face.planeNormal)[1], (*face.planeNormal)[2]);
            }

            writer.field("texture_delta_u", face.textureDeltaU);
            writer.field("texture_delta_v", face.textureDeltaV);
            writer.field("texture_frame_table_index", face.textureFrameTableIndex);
            writer.field("cog_number", face.cogNumber);
            writer.field("cog_triggered", face.cogTriggered);
            writer.field("cog_trigger_type", face.cogTriggerType);
            writer.field("light_level", face.lightLevel);
            writer.field("room", face.roomNumber);
            writer.field("room_behind", face.roomBehindNumber);
            writer.field("facet_type", face.facetType);
            writer.endObject();
        }

        writer.endArray();
    }

    writer.key("sectors");
    writer.beginArray();

    for (const Game::IndoorSector &sector : map.sectors)
    {
        writer.beginObject();
        writer.field("flags", sector.flags);
        triple(writer, "min", sector.minX, sector.minY, sector.minZ);
        triple(writer, "max", sector.maxX, sector.maxY, sector.maxZ);
        writer.field("water_level", sector.waterLevel);
        writer.field("mist_level", sector.mistLevel);
        writer.field("light_distance_multiplier", sector.lightDistanceMultiplier);
        writer.field("min_ambient_light_level", sector.minAmbientLightLevel);
        writer.field("first_bsp_node", sector.firstBspNode);
        writer.field("exit_tag", sector.exitTag);
        writer.field("face_count", static_cast<uint64_t>(sector.faceIds.size()));

        if (!options.summaryOnly)
        {
            numberArray(writer, "floor_faces", sector.floorFaceIds);
            numberArray(writer, "wall_faces", sector.wallFaceIds);
            numberArray(writer, "ceiling_faces", sector.ceilingFaceIds);
            numberArray(writer, "portal_faces", sector.portalFaceIds);
            numberArray(writer, "faces", sector.faceIds);
            numberArray(writer, "non_bsp_faces", sector.nonBspFaceIds);
            numberArray(writer, "cylinder_faces", sector.cylinderFaceIds);
            numberArray(writer, "lights", sector.lightIds);
            numberArray(writer, "decorations", sector.decorationIds);
        }

        writer.endObject();
    }

    writer.endArray();
    writer.key("entities");
    writer.beginArray();

    for (const Game::IndoorEntity &entity : map.entities)
    {
        writeEntity(writer, entity);
    }

    writer.endArray();
    writer.key("lights");
    writer.beginArray();

    for (const Game::IndoorLight &light : map.lights)
    {
        writer.beginObject();
        triple(writer, "position", light.x, light.y, light.z);
        writer.field("radius", light.radius);
        triple(writer, "color", light.red, light.green, light.blue);
        writer.field("type", light.type);
        writer.field("attributes", light.attributes);
        writer.field("brightness", light.brightness);
        writer.field("id", light.id);
        writer.endObject();
    }

    writer.endArray();
    writer.key("spawns");
    writer.beginArray();

    for (const Game::IndoorSpawn &spawn : map.spawns)
    {
        writeSpawn(writer, spawn);
    }

    writer.endArray();

    if (!options.summaryOnly)
    {
        writeBspNodes(writer, map.bspNodes);
        writer.key("outlines");
        writer.beginArray();

        for (const Game::IndoorOutline &outline : map.outlines)
        {
            writer.beginArray();
            writer.value(outline.vertex1Id);
            writer.value(outline.vertex2Id);
            writer.value(outline.face1Id);
            writer.value(outline.face2Id);
            writer.value(outline.z);
            writer.value(outline.flags);
            writer.endArray();
        }

        writer.endArray();
    }

    writer.endObject();
}
}

MapKind mapKindFromPath(const std::filesystem::path &path)
{
    const std::string extension = lowerExtension(path);

    if (extension == ".odm")
    {
        return MapKind::Outdoor;
    }

    if (extension == ".blv")
    {
        return MapKind::Indoor;
    }

    return MapKind::Unknown;
}

bool readFileBytes(const std::filesystem::path &path, std::vector<uint8_t> &bytes, std::string &errorMessage)
{
    std::ifstream stream(path, std::ios::binary);

    if (!stream)
    {
        errorMessage = "could not open " + path.string();
        return false;
    }

    bytes.assign(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
    return true;
}

std::vector<std::array<int, 4>> sceneVoidRectangles(const std::string &sceneText)
{
    std::vector<std::array<int, 4>> rects;

    try
    {
        const YAML::Node voids = YAML::Load(sceneText)["terrain"]["void"];

        for (size_t index = 0; voids && voids.IsSequence() && index < voids.size(); ++index)
        {
            const YAML::Node rect = voids[index];

            if (rect.IsSequence() && rect.size() == 4)
            {
                rects.push_back({rect[0].as<int>(), rect[1].as<int>(), rect[2].as<int>(), rect[3].as<int>()});
            }
        }
    }
    catch (const std::exception &)
    {
        rects.clear();
    }

    return rects;
}

bool exportMapJson(
    MapKind kind,
    const std::vector<uint8_t> &bytes,
    const MapExportOptions &options,
    JsonWriter &writer,
    std::string &errorMessage)
{
    if (kind == MapKind::Outdoor)
    {
        const std::optional<Game::OutdoorMapData> map = Game::OutdoorMapDataLoader().loadFromBytes(bytes);

        if (!map)
        {
            errorMessage = "not a readable ODM map";
            return false;
        }

        exportOutdoor(*map, options, writer);
        return true;
    }

    if (kind == MapKind::Indoor)
    {
        const std::optional<Game::IndoorMapData> map = Game::IndoorMapDataLoader().loadFromBytes(bytes);

        if (!map)
        {
            errorMessage = "not a readable BLV map";
            return false;
        }

        exportIndoor(*map, options, writer);
        return true;
    }

    errorMessage = "unknown map kind (expected .odm or .blv)";
    return false;
}
}
