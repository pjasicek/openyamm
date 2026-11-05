#include "doctest/doctest.h"

#include "editor/document/IndoorGeometryMetadata.h"
#include "editor/import/IndoorSourceGeometryCompiler.h"
#include "editor/import/IndoorDerivedGeometry.h"
#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/FaceEnums.h"

#include <chrono>
#include <array>
#include <filesystem>
#include <fstream>
#include <string>

using namespace OpenYAMM::Editor;

namespace
{
struct SourceFixture
{
    std::filesystem::path directory;
    std::filesystem::path source;
    EditorIndoorGeometryMetadata metadata;

    explicit SourceFixture(const std::string &extra = {})
    {
        const int64_t stamp = std::chrono::steady_clock::now().time_since_epoch().count();
        directory = std::filesystem::temp_directory_path() / ("openyamm_source_test_" + std::to_string(stamp));
        std::filesystem::create_directories(directory);
        source = directory / "fixture.obj";
        std::ofstream stream(source);
        stream << "o ROOM_entry\n"
               << "v 0 0 0\nv 256 0 0\nv 0 256 0\n"
               << "vt 0 1\nvt 1 1\nvt 0 0\n"
               << "usemtl stone\nf 1/1 2/2 3/3\n" << extra;
        metadata.source.unitScale = 1.0f;
        EditorIndoorGeometryMaterialMetadata material;
        material.id = "stone";
        material.sourceMaterial = "stone";
        material.texture = "GSton1WL";
        material.textureWidth = 64;
        material.textureHeight = 128;
        metadata.materials.push_back(material);
    }

    ~SourceFixture()
    {
        std::filesystem::remove_all(directory);
    }

    void useGltfNodes(const std::string &nodes, const std::string &sceneNodes = "[0,1]")
    {
        source = directory / "fixture.gltf";
        const std::array<float, 15> buffer = {0, 0, 0, 256, 0, 0, 0, 256, 0, 0, 0, 1, 0, 0, 1};
        std::ofstream binary(directory / "fixture.bin", std::ios::binary);
        binary.write(reinterpret_cast<const char *>(buffer.data()), sizeof(buffer));
        binary.close();
        std::ofstream stream(source);
        stream << R"({"asset":{"version":"2.0"},"buffers":[{"uri":"fixture.bin","byteLength":60}],)"
               << R"("bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":36},)"
               << R"({"buffer":0,"byteOffset":36,"byteLength":24}],)"
               << R"("accessors":[{"bufferView":0,"componentType":5126,"count":3,"type":"VEC3"},)"
               << R"({"bufferView":1,"componentType":5126,"count":3,"type":"VEC2"}],)"
               << R"("materials":[{"name":"stone"}],)"
               << R"("meshes":[{"primitives":[{"attributes":{"POSITION":0,"TEXCOORD_0":1},"material":0}]}],)"
               << "\"nodes\":" << nodes << ",\"scenes\":[{\"nodes\":" << sceneNodes << "}],\"scene\":0}";
    }
};
}

TEST_CASE("indoor derived data removes floor triangulation seams and excludes moving faces from BSP")
{
    OpenYAMM::Game::IndoorMapData geometry;
    geometry.version = 8;
    geometry.vertices = {{0,0,0}, {256,0,0}, {256,256,0}, {0,256,0}, {0,0,256}, {256,0,256}};
    for (const std::vector<uint16_t> &vertices : std::vector<std::vector<uint16_t>>{{0,1,2}, {0,2,3}, {0,4,5,1}})
    {
        OpenYAMM::Game::IndoorFace face;
        face.vertexIndices = vertices;
        face.facetType = vertices.size() == 3 ? 3 : 1;
        geometry.faces.push_back(face);
    }
    OpenYAMM::Game::IndoorSector sector;
    sector.faceIds = {0,1,2};
    geometry.sectors.push_back(sector);
    std::string error;
    REQUIRE_MESSAGE(generateIndoorDerivedGeometry(geometry, {2}, true, true, error), error);
    REQUIRE(geometry.bspNodes.size() == 1);
    CHECK(geometry.bspNodes[0].faceCount == 2);
    CHECK(geometry.bspNodes[0].front == -1);
    CHECK(geometry.bspNodes[0].back == -1);
    CHECK(geometry.sectors[0].firstBspNode == 0);
    CHECK((geometry.sectors[0].flags & 0x10) != 0);
    CHECK(geometry.sectors[0].nonBspFaceIds == std::vector<uint16_t>{2});
    REQUIRE(geometry.outlines.size() == 4);
    for (const OpenYAMM::Game::IndoorOutline &outline : geometry.outlines)
    {
        CHECK_FALSE((outline.vertex1Id == 0 && outline.vertex2Id == 2));
        CHECK(outline.face1Id < 2);
        CHECK(outline.face2Id < 2);
    }
    const OpenYAMM::Game::IndoorMapDataWriter writer;
    const std::optional<std::vector<uint8_t>> first = writer.buildBytes(geometry);
    REQUIRE(first.has_value());
    REQUIRE_MESSAGE(generateIndoorDerivedGeometry(geometry, {2}, true, true, error), error);
    CHECK(writer.buildBytes(geometry) == first);
    const OpenYAMM::Game::IndoorMapDataLoader loader;
    const std::optional<OpenYAMM::Game::IndoorMapData> loaded = loader.loadFromBytes(*first);
    REQUIRE(loaded.has_value());
    CHECK(loaded->bspNodes.size() == 1);
    CHECK(loaded->outlines.size() == 4);
    CHECK(loaded->sectors[0].nonBspFaceIds == std::vector<uint16_t>{2});
    geometry.vertices[5].y = 32;
    CHECK_FALSE(generateIndoorDerivedGeometry(geometry, {2}, true, true, error));
    CHECK(error.find("non-planar") != std::string::npos);
}

TEST_CASE("indoor outlines merge an edge's collinear pieces and drop near-coplanar seams")
{
    // A floor and the wall standing on its south edge, both carrying a vertex inserted on that edge (a T-junction
    // repair): one outline along it, as without the vertex.
    OpenYAMM::Game::IndoorMapData geometry;
    geometry.version = 8;
    geometry.vertices = {{0,0,0}, {128,0,0}, {256,0,0}, {256,256,0}, {0,256,0}, {0,0,256}, {256,0,256}};
    const auto addFace = [&geometry](std::vector<uint16_t> vertices, uint8_t facetType)
    {
        OpenYAMM::Game::IndoorFace face;
        face.vertexIndices = std::move(vertices);
        face.facetType = facetType;
        geometry.faces.push_back(face);
    };
    addFace({0, 1, 2, 3, 4}, 3);
    addFace({0, 5, 6, 2, 1}, 1);
    OpenYAMM::Game::IndoorSector sector;
    sector.faceIds = {0, 1};
    geometry.sectors.push_back(sector);
    std::string error;
    REQUIRE_MESSAGE(generateIndoorDerivedGeometry(geometry, {}, false, true, error), error);
    // The south edge (one line, though the inserted vertex splits it) and the floor's three others.
    CHECK(geometry.outlines.size() == 4);

    // A floor cut into two triangles a unit off one plane (a quarter of a degree): no line along the cut.
    OpenYAMM::Game::IndoorMapData bent;
    bent.version = 8;
    bent.vertices = {{0,0,0}, {256,0,0}, {256,256,1}, {0,256,0}};
    for (const std::vector<uint16_t> &vertices : std::vector<std::vector<uint16_t>>{{0,1,2}, {0,2,3}})
    {
        OpenYAMM::Game::IndoorFace face;
        face.vertexIndices = vertices;
        face.facetType = 3;
        bent.faces.push_back(face);
    }
    OpenYAMM::Game::IndoorSector bentSector;
    bentSector.faceIds = {0, 1};
    bent.sectors.push_back(bentSector);
    REQUIRE_MESSAGE(generateIndoorDerivedGeometry(bent, {}, false, true, error), error);
    CHECK(bent.outlines.size() == 4);
}

TEST_CASE("indoor BSP keeps crossing polygons native and uses the back sector portal orientation")
{
    OpenYAMM::Game::IndoorMapData geometry;
    const std::vector<int> xPlanes = {0,256,128};
    for (int x : xPlanes)
    {
        const uint16_t start = uint16_t(geometry.vertices.size());
        geometry.vertices.insert(geometry.vertices.end(), {{x,0,0}, {x,256,0}, {x,256,256}, {x,0,256}});
        OpenYAMM::Game::IndoorFace face;
        face.vertexIndices = {start, uint16_t(start+1), uint16_t(start+2), uint16_t(start+3)};
        face.facetType = 1;
        geometry.faces.push_back(face);
    }
    geometry.vertices.insert(geometry.vertices.end(), {{0,128,0}, {256,128,0}, {256,128,256}, {0,128,256}});
    OpenYAMM::Game::IndoorFace crossing;
    crossing.vertexIndices = {12,13,14,15};
    crossing.facetType = 1;
    geometry.faces.push_back(crossing);
    OpenYAMM::Game::IndoorSector sector;
    sector.faceIds = {0,1,2,3};
    geometry.sectors.push_back(sector);
    std::string error;
    REQUIRE_MESSAGE(generateIndoorDerivedGeometry(geometry, {}, true, false, error), error);
    REQUIRE(geometry.bspNodes.size() == 3);
    CHECK(geometry.sectors[0].nonBspFaceIds == std::vector<uint16_t>{3});
    CHECK(geometry.bspNodes[0].front == 1);
    CHECK(geometry.bspNodes[1].back == 2);
    CHECK(geometry.faces.size() == 4);

    geometry.sectors = {{}, {}};
    geometry.sectors[1].faceIds = {0,1};
    geometry.faces[0].isPortal = true;
    geometry.faces[0].roomNumber = 0;
    geometry.faces[0].roomBehindNumber = 1;
    REQUIRE_MESSAGE(generateIndoorDerivedGeometry(geometry, {}, true, false, error), error);
    REQUIRE(geometry.bspNodes.size() == 2);
    CHECK(geometry.sectors[0].firstBspNode == -1);
    CHECK(geometry.sectors[1].firstBspNode == 0);
    CHECK(geometry.bspNodes[0].front == -1);
    CHECK(geometry.bspNodes[0].back == 1);
}

TEST_CASE("indoor moving surfaces retain secret flags and event binding")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},{"name":"MECH_secret","mesh":0}])");
    EditorIndoorGeometryMechanismMetadata mechanism;
    mechanism.id = "secret";
    mechanism.sourceNodeNames = {"MECH_secret"};
    mechanism.doorId = 4;
    mechanism.moveAxis = {0,0,1};
    mechanism.moveLength = 512;
    fixture.metadata.mechanisms.push_back(mechanism);
    EditorIndoorGeometrySurfaceMetadata surface;
    surface.id = "secret";
    surface.sourceNodeName = "MECH_secret";
    surface.flags = {"secret", "texture_move_by_door"};
    surface.trigger = EditorIndoorGeometrySurfaceTriggerMetadata{103, "click"};
    fixture.metadata.surfaces.push_back(surface);
    IndoorSourceGeometryCompileResult result;
    std::string error;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    REQUIRE(result.generatedDoors.size() == 1);
    const uint16_t faceId = result.generatedDoors.front().door.faceIds.front();
    const OpenYAMM::Game::IndoorMapDataWriter writer;
    const std::optional<std::vector<uint8_t>> bytes = writer.buildBytes(result.indoorGeometry);
    REQUIRE(bytes.has_value());
    const OpenYAMM::Game::IndoorMapDataLoader loader;
    const std::optional<OpenYAMM::Game::IndoorMapData> loaded = loader.loadFromBytes(*bytes);
    REQUIRE(loaded.has_value());
    const OpenYAMM::Game::IndoorFace &face = loaded->faces[faceId];
    CHECK(face.cogTriggered == 103);
    CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::IsSecret));
    CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Clickable));
    CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::TextureMoveByDoor));
}

TEST_CASE("indoor flag-only surfaces keep their cog number, lose the click and keep lava")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},{"name":"TRIGGER_water","mesh":0}])");
    EditorIndoorGeometrySurfaceMetadata surface;
    surface.id = "water";
    surface.sourceNodeName = "TRIGGER_water";
    surface.flags = {"lava"};
    surface.cogNumber = 201;
    fixture.metadata.surfaces.push_back(surface);
    std::string error;
    const std::optional<EditorIndoorGeometryMetadata> metadata = loadIndoorGeometryMetadataFromText(
        serializeIndoorGeometryMetadata(fixture.metadata), error);
    REQUIRE_MESSAGE(metadata.has_value(), error);
    CHECK(metadata->surfaces.front().cogNumber == 201);
    IndoorSourceGeometryCompileResult result;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, *metadata, result, error), error);
    bool found = false;
    for (const OpenYAMM::Game::IndoorFace &face : result.indoorGeometry.faces)
    {
        if (face.cogNumber == 201)
        {
            found = true;
            CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Lava));
            CHECK_FALSE(OpenYAMM::Game::hasFaceAttribute(face.attributes, OpenYAMM::Game::FaceAttribute::Clickable));
        }
    }
    CHECK(found);
}

TEST_CASE("indoor light metadata group round-trips")
{
    EditorIndoorGeometryMetadata source;
    EditorIndoorGeometryLightMetadata light;
    light.id = "L1";
    light.sourceNodeName = "LIGHT_L1";
    light.radius = 512;
    light.brightness = 31;
    light.group = 3;
    source.lights.push_back(light);
    std::string error;
    const std::optional<EditorIndoorGeometryMetadata> loaded =
        loadIndoorGeometryMetadataFromText(serializeIndoorGeometryMetadata(source), error);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    CHECK(loaded->lights.front().group == 3);
}

TEST_CASE("indoor authored closed lift retains its floor and opens upward through native motion")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},)"
                         R"({"name":"MECH_lift","mesh":0,"translation":[0,0,384]}])");
    EditorIndoorGeometryMechanismMetadata mechanism;
    mechanism.id = "lift";
    mechanism.sourceNodeNames = {"MECH_lift"};
    mechanism.doorId = 6;
    mechanism.sourcePose = "closed";
    mechanism.initialState = "closed";
    mechanism.moveAxis = {0,0,-1};
    mechanism.moveLength = 384;
    fixture.metadata.mechanisms.push_back(mechanism);
    std::string error;
    const std::optional<EditorIndoorGeometryMetadata> metadata = loadIndoorGeometryMetadataFromText(
        serializeIndoorGeometryMetadata(fixture.metadata), error);
    REQUIRE_MESSAGE(metadata.has_value(), error);
    CHECK(metadata->mechanisms.front().sourcePose == "closed");
    IndoorSourceGeometryCompileResult result;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, *metadata, result, error), error);
    REQUIRE(result.generatedDoors.size() == 1);
    const OpenYAMM::Game::MapDeltaDoor &door = result.generatedDoors.front().door;
    std::vector<OpenYAMM::Game::IndoorVertex> vertices = result.indoorGeometry.vertices;
    for (uint16_t vertexId : door.vertexIds)
    {
        CHECK(vertices[vertexId].z == 384);
    }
    const std::array<std::array<float, 2>, 3> samples = {{{384,384}, {192,576}, {0,768}}};
    for (const std::array<float, 2> &sample : samples)
    {
        OpenYAMM::Game::applyIndoorMechanismDoorToVertices(door, nullptr, sample[0], 1, vertices);
        for (uint16_t vertexId : door.vertexIds)
        {
            CHECK(vertices[vertexId].z == sample[1]);
            CHECK(vertices[vertexId].x == result.indoorGeometry.vertices[vertexId].x);
            CHECK(vertices[vertexId].y == result.indoorGeometry.vertices[vertexId].y);
        }
        CHECK(vertices.front().z == 0);
    }
}

TEST_CASE("indoor mechanism default source pose is the native open baseline")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},{"name":"MECH_door","mesh":0}])");
    EditorIndoorGeometryMechanismMetadata mechanism;
    mechanism.id = "door";
    mechanism.sourceNodeNames = {"MECH_door"};
    mechanism.moveAxis = {1,0,0};
    mechanism.moveLength = 256;
    fixture.metadata.mechanisms.push_back(mechanism);
    IndoorSourceGeometryCompileResult result;
    std::string error;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    const OpenYAMM::Game::MapDeltaDoor &door = result.generatedDoors.front().door;
    std::vector<OpenYAMM::Game::IndoorVertex> vertices = result.indoorGeometry.vertices;
    OpenYAMM::Game::applyIndoorMechanismDoorToVertices(door, nullptr, 256, 1, vertices);
    for (uint16_t vertexId : door.vertexIds)
    {
        CHECK(vertices[vertexId].x == result.indoorGeometry.vertices[vertexId].x + 256);
    }
    OpenYAMM::Game::applyIndoorMechanismDoorToVertices(door, nullptr, 0, 1, vertices);
    for (uint16_t vertexId : door.vertexIds)
    {
        CHECK(vertices[vertexId].x == result.indoorGeometry.vertices[vertexId].x);
    }
}

TEST_CASE("indoor mechanism rejects unknown source poses and overflowing endpoints")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},{"name":"MECH_door","mesh":0}])");
    EditorIndoorGeometryMechanismMetadata mechanism;
    mechanism.id = "door";
    mechanism.sourceNodeNames = {"MECH_door"};
    mechanism.moveAxis = {0,0,-1};
    mechanism.moveLength = 384;
    SUBCASE("unknown pose")
    {
        mechanism.sourcePose = "halfway";
    }
    SUBCASE("closed source would open beyond native range")
    {
        mechanism.sourcePose = "closed";
        mechanism.moveLength = 40000;
    }
    SUBCASE("open source would close beyond native range")
    {
        mechanism.moveLength = 40000;
    }
    fixture.metadata.mechanisms.push_back(mechanism);
    IndoorSourceGeometryCompileResult result;
    std::string error;
    CHECK_FALSE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error));
    CHECK(error.find("Mechanism") != std::string::npos);
}

TEST_CASE("indoor source rejects stale room membership instead of guessing an owner")
{
    SourceFixture fixture;
    EditorIndoorGeometryRoomMetadata room;
    room.id = "room_missing";
    room.sourceNodeNames = {"ROOM_entry"};
    fixture.metadata.rooms = {room};
    IndoorSourceGeometryCompileResult result;
    std::string error;
    CHECK_FALSE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error));
    CHECK(error.find("unknown room") != std::string::npos);
    fixture.metadata.rooms.front().id = "room_entry";
    fixture.metadata.rooms.front().sourceNodeNames = {"LIGHT_missing"};
    CHECK_FALSE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error));
    CHECK(error.find("missing node") != std::string::npos);
}

TEST_CASE("indoor source preserves pixel UVs and reserved sector through native serialization")
{
    SourceFixture fixture;
    fixture.metadata.importSettings.reserveSectorZero = true;
    IndoorSourceGeometryCompileResult result;
    std::string error;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    REQUIRE(result.indoorGeometry.sectors.size() == 2);
    CHECK(result.indoorGeometry.sectors[0].faceIds.empty());
    REQUIRE(result.indoorGeometry.faces.size() == 1);
    CHECK(result.indoorGeometry.faces[0].roomNumber == 1);
    CHECK(result.indoorGeometry.faces[0].textureUs == std::vector<int16_t>{0, 64, 0});
    CHECK(result.indoorGeometry.faces[0].textureVs == std::vector<int16_t>{0, 0, 128});

    const OpenYAMM::Game::IndoorMapDataWriter writer;
    const std::optional<std::vector<uint8_t>> bytes = writer.buildBytes(result.indoorGeometry);
    REQUIRE(bytes.has_value());
    const OpenYAMM::Game::IndoorMapDataLoader loader;
    const std::optional<OpenYAMM::Game::IndoorMapData> loaded = loader.loadFromBytes(*bytes);
    REQUIRE(loaded.has_value());
    REQUIRE(loaded->sectors.size() == 2);
    CHECK(loaded->sectors[0].faceIds.empty());
    CHECK(loaded->sectors[1].floorFaceIds == std::vector<uint16_t>{0});
    CHECK(loaded->faces[0].textureUs == result.indoorGeometry.faces[0].textureUs);
    CHECK(loaded->faces[0].textureVs == result.indoorGeometry.faces[0].textureVs);
    CHECK(loaded->faces[0].textureName == "GSton1WL");
}

TEST_CASE("indoor source keeps glTF fan polygons whole when n-gons are not triangulated")
{
    SourceFixture fixture;
    fixture.source = fixture.directory / "fan.gltf";
    // One square room floor as a five-vertex fan with a collinear vertex on its east edge.
    const std::array<float, 25> buffer = {0, 0, 0, 256, 0, 0, 256, 128, 0, 256, 256, 0, 0, 256, 0,
                                          0, 1, 1, 1, 1, 0.5f, 1, 0, 0, 0};
    std::ofstream binary(fixture.directory / "fan.bin", std::ios::binary);
    binary.write(reinterpret_cast<const char *>(buffer.data()), sizeof(buffer));
    binary.close();
    std::ofstream stream(fixture.source);
    stream << R"({"asset":{"version":"2.0"},"buffers":[{"uri":"fan.bin","byteLength":100}],)"
           << R"("bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":60},)"
           << R"({"buffer":0,"byteOffset":60,"byteLength":40}],)"
           << R"("accessors":[{"bufferView":0,"componentType":5126,"count":5,"type":"VEC3"},)"
           << R"({"bufferView":1,"componentType":5126,"count":5,"type":"VEC2"}],)"
           << R"("materials":[{"name":"stone"}],)"
           << R"("meshes":[{"primitives":[{"attributes":{"POSITION":0,"TEXCOORD_0":1},"material":0,"mode":6}]}],)"
           << R"("nodes":[{"name":"ROOM_entry","mesh":0}],"scenes":[{"nodes":[0]}],"scene":0})";
    stream.close();

    IndoorSourceGeometryCompileResult result;
    std::string error;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    CHECK(result.indoorGeometry.faces.size() == 3);

    fixture.metadata.importSettings.triangulateNgons = false;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    REQUIRE(result.indoorGeometry.faces.size() == 1);
    const OpenYAMM::Game::IndoorFace &face = result.indoorGeometry.faces[0];
    CHECK(face.vertexIndices.size() == 5);
    CHECK(face.facetType == 3);
    CHECK(face.textureUs == std::vector<int16_t>{0, 64, 64, 64, 0});
    CHECK(face.textureVs == std::vector<int16_t>{128, 128, 64, 0, 0});
    REQUIRE(result.indoorGeometry.sectors.size() == 1);
    CHECK(result.indoorGeometry.sectors[0].floorFaceIds == std::vector<uint16_t>{0});
}

TEST_CASE("indoor room ambient survives metadata and native serialization with bounded values")
{
    SourceFixture fixture;
    fixture.metadata.importSettings.reserveSectorZero = true;
    EditorIndoorGeometryRoomMetadata room;
    room.id = "room_entry";
    room.sourceNodeNames = {"ROOM_entry"};
    room.minAmbientLightLevel = 22;
    fixture.metadata.rooms.push_back(room);
    std::string error;
    const std::optional<EditorIndoorGeometryMetadata> metadata = loadIndoorGeometryMetadataFromText(
        serializeIndoorGeometryMetadata(fixture.metadata), error);
    REQUIRE_MESSAGE(metadata.has_value(), error);
    REQUIRE(metadata->rooms.size() == 1);
    CHECK(metadata->rooms[0].minAmbientLightLevel == 22);
    IndoorSourceGeometryCompileResult result;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, *metadata, result, error), error);
    const OpenYAMM::Game::IndoorMapDataWriter writer;
    const std::optional<std::vector<uint8_t>> bytes = writer.buildBytes(result.indoorGeometry);
    REQUIRE(bytes.has_value());
    const OpenYAMM::Game::IndoorMapDataLoader loader;
    const std::optional<OpenYAMM::Game::IndoorMapData> loaded = loader.loadFromBytes(*bytes);
    REQUIRE(loaded.has_value());
    REQUIRE(loaded->sectors.size() == 2);
    CHECK(loaded->sectors[0].minAmbientLightLevel == 0);
    CHECK(loaded->sectors[1].minAmbientLightLevel == 22);
    for (const int16_t invalid : {-1, 32})
    {
        fixture.metadata.rooms[0].minAmbientLightLevel = invalid;
        CHECK_FALSE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error));
        CHECK_FALSE(loadIndoorGeometryMetadataFromText(serializeIndoorGeometryMetadata(fixture.metadata), error));
    }
}

TEST_CASE("indoor source old metadata retains its sector and texture coordinate convention")
{
    SourceFixture fixture;
    std::string error;
    const std::optional<EditorIndoorGeometryMetadata> metadata = loadIndoorGeometryMetadataFromText(
        "format_version: 2\nsource:\n  unit_scale: 1\n"
        "materials:\n  - id: stone\n    source_material: stone\n    texture: GSton1WL\n", error);
    REQUIRE_MESSAGE(metadata.has_value(), error);
    IndoorSourceGeometryCompileResult result;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, *metadata, result, error), error);
    REQUIRE(result.indoorGeometry.sectors.size() == 1);
    CHECK(result.indoorGeometry.sectors[0].minAmbientLightLevel == 0);
    CHECK(result.indoorGeometry.faces[0].roomNumber == 0);
    CHECK(result.indoorGeometry.faces[0].textureUs == std::vector<int16_t>{0, 256, 0});
    CHECK(result.indoorGeometry.faces[0].textureVs == std::vector<int16_t>{0, 0, 256});
}

TEST_CASE("indoor source metadata round trip preserves material dimensions and reserved sector choice")
{
    SourceFixture fixture;
    fixture.metadata.importSettings.reserveSectorZero = true;
    std::string error;
    const std::optional<EditorIndoorGeometryMetadata> loaded = loadIndoorGeometryMetadataFromText(
        serializeIndoorGeometryMetadata(fixture.metadata), error);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    CHECK(loaded->importSettings.reserveSectorZero);
    REQUIRE(loaded->materials.size() == 1);
    CHECK(loaded->materials[0].textureWidth == 64);
    CHECK(loaded->materials[0].textureHeight == 128);
}

TEST_CASE("indoor source does not attach a marker at the origin to reserved sector zero")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},)"
                         R"({"name":"LIGHT_origin","mesh":0,"translation":[-85.333333,-85.333333,0]}])");
    fixture.metadata.importSettings.reserveSectorZero = true;
    EditorIndoorGeometryLightMetadata light;
    light.id = "origin";
    light.sourceNodeName = "LIGHT_origin";
    light.radius = 512;
    light.brightness = 31;
    fixture.metadata.lights.push_back(light);
    IndoorSourceGeometryCompileResult result;
    std::string error;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    CHECK(result.indoorGeometry.sectors[0].lightIds.empty());
    CHECK(result.indoorGeometry.sectors[1].lightIds == std::vector<uint16_t>{0});
}

TEST_CASE("indoor source rejects native range overflow and invalid texture dimensions")
{
    SourceFixture fixture;
    SUBCASE("coordinates")
    {
        fixture.metadata.source.unitScale = 1000.0f;
    }
    SUBCASE("UV coordinates")
    {
        fixture.metadata.materials[0].textureWidth = 65536;
    }
    SUBCASE("zero dimension")
    {
        fixture.metadata.materials[0].textureHeight = 0;
    }
    IndoorSourceGeometryCompileResult result;
    std::string error;
    CHECK_FALSE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error));
    CHECK_FALSE(error.empty());
}

TEST_CASE("indoor source rejects duplicate room identities")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry-a","mesh":0},{"name":"ROOM_entry a","mesh":0}])");
    IndoorSourceGeometryCompileResult result;
    std::string error;
    CHECK_FALSE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error));
    CHECK(error.find("duplicate") != std::string::npos);
}

TEST_CASE("indoor source explicit ownership and plate detection flags survive native serialization")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},{"name":"ROOM_upper","mesh":0},)"
                         R"({"name":"TRIGGER_plate","mesh":0}])", "[0,1,2]");
    fixture.metadata.importSettings.reserveSectorZero = true;
    EditorIndoorGeometryRoomMetadata room;
    room.id = "room_upper";
    room.sourceNodeNames = {"ROOM_upper", "TRIGGER_plate"};
    fixture.metadata.rooms.push_back(room);
    EditorIndoorGeometrySurfaceMetadata surface;
    surface.id = "plate";
    surface.sourceNodeName = "TRIGGER_plate";
    surface.flags = {"secret", "trigger_monster", "trigger_object"};
    surface.trigger = EditorIndoorGeometrySurfaceTriggerMetadata{301, "pressure_plate"};
    fixture.metadata.surfaces.push_back(surface);
    IndoorSourceGeometryCompileResult result;
    std::string error;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    const OpenYAMM::Game::IndoorMapDataWriter writer;
    const std::optional<std::vector<uint8_t>> bytes = writer.buildBytes(result.indoorGeometry);
    REQUIRE(bytes.has_value());
    const OpenYAMM::Game::IndoorMapDataLoader loader;
    const std::optional<OpenYAMM::Game::IndoorMapData> loaded = loader.loadFromBytes(*bytes);
    REQUIRE(loaded.has_value());
    REQUIRE(loaded->faces.size() == 3);
    const OpenYAMM::Game::IndoorFace &face = loaded->faces.back();
    CHECK(face.roomNumber == 2);
    CHECK(face.cogTriggered == 301);
    using OpenYAMM::Game::FaceAttribute;
    CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, FaceAttribute::PressurePlate));
    CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, FaceAttribute::TriggerByTouch));
    CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, FaceAttribute::IsSecret));
    CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, FaceAttribute::TriggerByMonster));
    CHECK(OpenYAMM::Game::hasFaceAttribute(face.attributes, FaceAttribute::TriggerByObject));
    CHECK_FALSE(OpenYAMM::Game::hasFaceAttribute(face.attributes, FaceAttribute::Clickable));
    CHECK(loaded->sectors[1].faceIds == std::vector<uint16_t>{0});
    CHECK(loaded->sectors[2].faceIds == std::vector<uint16_t>{1, 2});

    fixture.metadata.rooms[0].id = "room_entry";
    fixture.metadata.rooms.push_back(room);
    CHECK_FALSE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error));
    CHECK(error.find("multiple rooms") != std::string::npos);
}

TEST_CASE("indoor source marks the room above a floor portal, as a native BLV does")
{
    // All three nodes share the fixture's triangle, whose normal points up: a portal in a floor.
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},{"name":"ROOM_lower","mesh":0},)"
                         R"({"name":"PORTAL_mouth","mesh":0}])", "[0,1,2]");
    for (const char *pId : {"entry", "lower"})
    {
        EditorIndoorGeometryRoomMetadata room;
        room.id = std::string("room_") + pId;
        room.sourceNodeNames = {std::string("ROOM_") + pId};
        fixture.metadata.rooms.push_back(room);
    }
    EditorIndoorGeometryPortalMetadata portal;
    portal.id = "mouth";
    portal.sourceNodeName = "PORTAL_mouth";
    portal.frontRoom = "room_entry";
    portal.backRoom = "room_lower";
    fixture.metadata.portals.push_back(portal);
    IndoorSourceGeometryCompileResult result;
    std::string error;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    const OpenYAMM::Game::IndoorFace &face = result.indoorGeometry.faces.back();
    REQUIRE(face.isPortal);
    CHECK((result.indoorGeometry.sectors[face.roomNumber].flags & 0x8) != 0);
    CHECK((result.indoorGeometry.sectors[face.roomBehindNumber].flags & 0x8) == 0);
}

TEST_CASE("Static indoor furnishings retain explicit ownership in overlapping sectors")
{
    SourceFixture fixture;
    fixture.useGltfNodes(R"([{"name":"ROOM_entry","mesh":0},{"name":"ROOM_upper","mesh":0},)"
                         R"({"name":"STATIC_bench","mesh":0}])", "[0,1,2]");
    fixture.metadata.importSettings.reserveSectorZero = true;
    EditorIndoorGeometryRoomMetadata room;
    room.id = "room_upper";
    room.sourceNodeNames = {"ROOM_upper", "STATIC_bench"};
    fixture.metadata.rooms.push_back(room);
    IndoorSourceGeometryCompileResult result;
    std::string error;
    REQUIRE_MESSAGE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error), error);
    const OpenYAMM::Game::IndoorMapDataWriter writer;
    const std::optional<std::vector<uint8_t>> bytes = writer.buildBytes(result.indoorGeometry);
    REQUIRE(bytes.has_value());
    const OpenYAMM::Game::IndoorMapDataLoader loader;
    const std::optional<OpenYAMM::Game::IndoorMapData> loaded = loader.loadFromBytes(*bytes);
    REQUIRE(loaded.has_value());
    REQUIRE(loaded->faces.size() == 3);
    CHECK(loaded->faces.back().roomNumber == 2);
    CHECK(loaded->faces.back().cogTriggered == 0);
    CHECK(loaded->faces.back().attributes == 0);
    CHECK(loaded->sectors[1].faceIds == std::vector<uint16_t>{0});
    CHECK(loaded->sectors[2].faceIds == std::vector<uint16_t>{1, 2});
    fixture.metadata.rooms.clear();
    CHECK_FALSE(compileIndoorSourceGeometry(fixture.source, fixture.metadata, result, error));
    CHECK(error.find("requires explicit room ownership") != std::string::npos);
}

TEST_CASE("indoor derived data keeps long thin triangles far from the origin planar")
{
    // A sliver of MM9 Lich Lab's diagonal stair: off its own single-precision Newell plane by 0.3 units.
    OpenYAMM::Game::IndoorMapData geometry;
    geometry.version = 8;
    geometry.vertices = {{-2642, 7967, -635}, {-3707, 7946, -102}, {-3625, 7946, -143}};
    OpenYAMM::Game::IndoorFace face;
    face.vertexIndices = {0, 1, 2};
    face.facetType = 3;
    geometry.faces.push_back(face);
    OpenYAMM::Game::IndoorSector sector;
    sector.faceIds = {0};
    geometry.sectors.push_back(sector);
    std::string error;
    CHECK_MESSAGE(generateIndoorDerivedGeometry(geometry, {}, true, true, error), error);
}
