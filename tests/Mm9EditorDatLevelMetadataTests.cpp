#include "doctest/doctest.h"

#include "editor/document/Mm9DatLevelMetadata.h"

#include <chrono>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <algorithm>
#include <vector>

namespace
{
std::filesystem::path sourceRoot()
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR);
}

std::string lowerAscii(std::string value)
{
    for (char &character : value)
    {
        if (character >= 'A' && character <= 'Z')
        {
            character = static_cast<char>(character - 'A' + 'a');
        }
    }

    return value;
}

std::string minimalMm9LevelYaml()
{
    return R"(
format_version: 1
kind: mm9_level
map_id: testmap
display_name: Test Map
source:
  dat: ../source/worlds/TESTMAP.dat
  manifest: ../source/manifest.yml
  original_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
  source_game: mm9
  dat_version: 66
  content_hash: abc123
runtime:
  world_backend: dat_world
  classification: dat_bsp_like
  classification_confidence: high
  visibility: dat_portal_bsp
  collision: dat_physics_bsp
  render: dat_render_world
  sky: false
sidecars:
  dat_world: testmap.dat_world.yml
  raw_objects: testmap.raw_objects.yml
  materials: testmap.material_aliases.yml
  events: testmap.events.yml
  scene_compat: testmap.scene.yml
  source_metadata_compat: testmap.mm9.yml
  bsp_compat: null
  geometry_compat: null
  model_assets_compat: testmap.model_assets.yml
  odm_compat: null
  blv_compat: testmap.blv
scripts:
  level: ../events/testmap.lua
  script_ir: ../events/testmap.script_ir.yml
compatibility:
  legacy_target_format: blv
  generated_odm_blv_are_derived: true
)";
}

std::string minimalDatWorldSidecarYaml()
{
    return R"(
format_version: 1
kind: mm9_dat_world
map_id: testmap
source_dat: ../source/worlds/TESTMAP.dat
source_hash: 947d5a35ff2fe522fda5b431af955e3b27955ebc18c9e3684b07b51ae112461f
dat_version: 66
coordinate_system:
  source: lithtech_mm9
  openyamm_mapping: [x, z, y]
  scale: 2.56
world_info:
  property_string: PBlockSize 8096
  light_map_grid_size: 64.0
  extents_min_lt: [-10.0, -20.0, -30.0]
  extents_max_lt: [10.0, 20.0, 30.0]
classification:
  recommendation: dat_bsp_like
  confidence: high
  reason: test reason
totals:
  world_model_count: 1
  object_count: 1
  source_poly_count: 2
  surface_count: 2
  user_portal_count: 0
  leaf_count: 1
  leaf_reference_count: 2
  invalid_leaf_reference_count: 0
world_models:
  - source_model_index: 0
    source_name: TestModel
    world_info_flags: 8
    kind: terrain
    point_count: 4
    plane_count: 2
    surface_count: 2
    poly_count: 2
    leaf_count: 1
    node_count: 1
    user_portal_count: 0
    pblock_table:
      preserved_in_source_dat: true
      decoded_summary: false
      record_count: null
    bounds_lt:
      min: [-1.0, -2.0, -3.0]
      max: [1.0, 2.0, 3.0]
    world_translation_lt: [4.0, 5.0, 6.0]
    textures:
      - texture_index: 0
        source_texture: TEXTURES\Test\test.dtx
    surface_flag_histogram:
      4: 2
    texture_user_flag_histogram:
      12: 2
    roles:
      visible: true
      terrain: true
      physics_bsp: false
      vis_bsp: false
      sky: false
      water: false
      trigger_or_volume: false
      movable: false
user_portals: []
leaf_references:
  decode: world_model_index_low16_poly_index_high16
  total_refs: 2
  invalid_refs: 0
validation:
  parse_status: ok
  unknown_field_policy: preserved_in_source_dat
  pblock_summary_status: not_yet_decoded
)";
}

std::string minimalMaterialAliasesSidecarYaml()
{
    return R"(
format_version: 1
kind: mm9_material_aliases
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
stats:
  source_models: 1
  source_polies: 2
  emitted_faces: 2
  skipped_polies: 0
  triangulated_polies: 0
  skipped_degenerate_triangles: 0
  model_instances: 1
  unique_model_assets: 1
textures:
  - alias: TEST
    source_texture: TEXTURES\Test\test.dtx
    width: 128
    height: 64
    physical_path: mm9/extracted/TEXTURES/TEXTURES/TEST/TEST.dtx
    emitted_bitmap: testmap.bitmaps/TEST.bmp
    emitted_bitmap_mode: dxt1
    dtx_surface_flag: 12
    dtx_texture_group: 2
    dtx_bpp: 4
    dtx_mipmap_count: 4
    dtx_mipmaps_used: 4
    dtx_flags: 8
    dtx_detail_scale: 5.0
    dtx_detail_angle: 0
    dtx_command_string: DetailTex Textures\detailtextures\det_01.dtx
)";
}

std::string minimalRawObjectsSidecarYaml()
{
    return R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 0
    name: TestObject
    property_count: 1
    data_length: 4
    trailing_hex: ""
    properties:
      - name: Name
        code: 0
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "02005400"
        value_json: "\"T\""
)";
}

std::string minimalEventsSidecarYaml()
{
    return R"(
format_version: 1
kind: mm9_events
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
source_raw_objects: testmap.raw_objects.yml
generated:
  lua: ../events/testmap.lua
objects:
  - object_id: mm9:testmap:object:0
    source_object_index: 0
    source_class: TestClass
    source_name: TestObject
    classifications: []
    raw_property_count: 1
    raw_object_ref: testmap.raw_objects.yml#objects[0]
    raw_properties: []
    normalized_properties: {}
mechanisms:
  - mechanism_id: mm9:testmap:object:0:mechanism
    object_id: mm9:testmap:object:0
    source_object_index: 0
    source_class: TestClass
    source_name: TestObject
    mechanism:
      kind: moving_world_model
      source_units: lithtech_mm9
      linear:
        move_dir_lt: [0.0, 1.0, 0.0]
        move_dist_lt: 64.0
        open_speed_lt_per_sec: 32.0
        close_speed_lt_per_sec: 16.0
    activation:
      start_open: false
      locked: false
bindings:
  - object_id: mm9:testmap:object:0
    source_object_index: 0
    targets:
      - target_kind: odm_bmodel
        target_id: testmap.dat_world.yml#world_models[0]
        confidence: high
        bmodel_index: 0
        bmodel_name: TestModel
scripts: []
)";
}

std::string minimalSourceAssetManifestYaml(size_t worldsFileCount = 1, bool includeTextures = true)
{
    std::string textureFamily = includeTextures ? R"(
  - id: textures
    source: TEXTURES/TEXTURES
    package: textures
    file_count: 1
)" : std::string();

    return R"(
format_version: 1
kind: mm9_source_asset_manifest
source_root: mm9/extracted
package_root: assets_dev/worlds/mm9/source
policy:
  source_truth: true
  generated_cache: false
  preserve_rez_relative_names: true
  duplicate_rez_family_folder_removed: true
  sync_command: rsync -a
families:
  - id: worlds
    source: WORLDS/WORLDS
    package: worlds
    file_count: )" + std::to_string(worldsFileCount) + textureFamily + R"(
  - id: skins
    source: SKINS/SKINS
    package: skins
    file_count: 0
  - id: models
    source: MODELS/MODELS
    package: models
    file_count: 0
  - id: scripts
    source: SCRIPTS/SCRIPTS
    package: scripts
    file_count: 0
  - id: rude
    source: RUDE/RUDE
    package: rude
    file_count: 0
  - id: data
    source: DATA/DATA
    package: data
    file_count: 0
  - id: sounds
    source: SOUNDS/SOUNDS
    package: sounds
    file_count: 0
  - id: voices
    source: VOICES/VOICES
    package: voices
    file_count: 0
  - id: sprites
    source: SPRITES/SPRITES
    package: sprites
    file_count: 0
  - id: sprite_textures
    source: SPRITETEXTURES/SPRITETEXTURES
    package: sprite_textures
    file_count: 0
  - id: art
    source: ART/ART
    package: art
    file_count: 0
  - id: localart
    source: LOCALART/LOCALART
    package: localart
    file_count: 0
  - id: clientfx
    source: CLIENTFX/CLIENTFX
    package: clientfx
    file_count: 0
notes:
  - Test manifest.
)";
}

std::string mm9LevelYamlWithContentHash(const std::string &contentHash)
{
    std::string yamlText = minimalMm9LevelYaml();
    const std::string oldHash = "content_hash: abc123";
    const size_t oldHashPosition = yamlText.find(oldHash);
    REQUIRE(oldHashPosition != std::string::npos);
    yamlText.replace(oldHashPosition, oldHash.size(), "content_hash: " + contentHash);
    return yamlText;
}

void writeTextFile(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream output(path);
    REQUIRE(output.good());
    output << text;
}

void writeBinaryFile(const std::filesystem::path &path, const std::vector<uint8_t> &bytes)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream output(path, std::ios::binary);
    REQUIRE(output.good());
    output.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
}

void writeBgra32BmpFile(
    const std::filesystem::path &path,
    int width,
    int height,
    const std::vector<uint8_t> &pixelsBgra)
{
    REQUIRE(width > 0);
    REQUIRE(height > 0);
    REQUIRE(pixelsBgra.size() == static_cast<size_t>(width) * static_cast<size_t>(height) * 4u);

    std::filesystem::create_directories(path.parent_path());
    std::ofstream output(path, std::ios::binary);
    REQUIRE(output.good());

    const uint32_t fileHeaderSize = 14;
    const uint32_t dibHeaderSize = 40;
    const uint32_t pixelOffset = fileHeaderSize + dibHeaderSize;
    const uint32_t pixelBytes = static_cast<uint32_t>(pixelsBgra.size());
    const uint32_t fileSize = pixelOffset + pixelBytes;
    const uint16_t reserved = 0;
    const uint16_t planes = 1;
    const uint16_t bpp = 32;
    const uint32_t compression = 0;
    const uint32_t ppm = 0;
    const uint32_t colors = 0;

    output.write("BM", 2);
    output.write(reinterpret_cast<const char *>(&fileSize), sizeof(fileSize));
    output.write(reinterpret_cast<const char *>(&reserved), sizeof(reserved));
    output.write(reinterpret_cast<const char *>(&reserved), sizeof(reserved));
    output.write(reinterpret_cast<const char *>(&pixelOffset), sizeof(pixelOffset));
    output.write(reinterpret_cast<const char *>(&dibHeaderSize), sizeof(dibHeaderSize));
    output.write(reinterpret_cast<const char *>(&width), sizeof(width));
    output.write(reinterpret_cast<const char *>(&height), sizeof(height));
    output.write(reinterpret_cast<const char *>(&planes), sizeof(planes));
    output.write(reinterpret_cast<const char *>(&bpp), sizeof(bpp));
    output.write(reinterpret_cast<const char *>(&compression), sizeof(compression));
    output.write(reinterpret_cast<const char *>(&pixelBytes), sizeof(pixelBytes));
    output.write(reinterpret_cast<const char *>(&ppm), sizeof(ppm));
    output.write(reinterpret_cast<const char *>(&ppm), sizeof(ppm));
    output.write(reinterpret_cast<const char *>(&colors), sizeof(colors));
    output.write(reinterpret_cast<const char *>(&colors), sizeof(colors));

    for (int row = height - 1; row >= 0; --row)
    {
        const size_t rowOffset = static_cast<size_t>(row) * static_cast<size_t>(width) * 4u;
        output.write(
            reinterpret_cast<const char *>(pixelsBgra.data() + rowOffset),
            static_cast<std::streamsize>(static_cast<size_t>(width) * 4u));
    }
}

template <typename ValueType>
void writeLittleEndianValue(std::vector<uint8_t> &bytes, size_t offset, ValueType value)
{
    std::memcpy(bytes.data() + offset, &value, sizeof(ValueType));
}

std::vector<uint8_t> makeDtxHeaderBytes()
{
    const size_t dxt1MipPayloadSize = 4096u + 1024u + 256u + 64u;
    std::vector<uint8_t> bytes(164u + dxt1MipPayloadSize, 0);
    writeLittleEndianValue<int32_t>(bytes, 0, 0);
    writeLittleEndianValue<int32_t>(bytes, 4, -5);
    writeLittleEndianValue<uint16_t>(bytes, 8, 128);
    writeLittleEndianValue<uint16_t>(bytes, 10, 64);
    writeLittleEndianValue<uint16_t>(bytes, 12, 4);
    writeLittleEndianValue<uint16_t>(bytes, 14, 0);
    writeLittleEndianValue<uint16_t>(bytes, 16, 8);
    writeLittleEndianValue<uint16_t>(bytes, 18, 0);
    writeLittleEndianValue<int32_t>(bytes, 20, 12);
    bytes[24] = 2;
    bytes[25] = 4;
    bytes[26] = 4;
    bytes[27] = 0;
    bytes[28] = 0;
    writeLittleEndianValue<int8_t>(bytes, 29, 0);
    writeLittleEndianValue<float>(bytes, 30, 5.0f);
    writeLittleEndianValue<int16_t>(bytes, 34, 0);

    const std::string command = "DetailTex Textures\\detailtextures\\det_01.dtx";
    std::memcpy(bytes.data() + 36, command.data(), command.size());
    return bytes;
}

std::vector<uint8_t> makeDecodedDxt1ZeroPixelsBgra()
{
    std::vector<uint8_t> pixels(static_cast<size_t>(128) * static_cast<size_t>(64) * 4u, 0);

    for (size_t offset = 3; offset < pixels.size(); offset += 4)
    {
        pixels[offset] = 255;
    }

    return pixels;
}

void writeMatchingDecodedDtxCacheBmp(const std::filesystem::path &path)
{
    writeBgra32BmpFile(path, 128, 64, makeDecodedDxt1ZeroPixelsBgra());
}

std::vector<uint8_t> makeSprBytes(const std::vector<std::string> &textureRefs)
{
    std::vector<uint8_t> bytes(20, 0);
    writeLittleEndianValue<uint32_t>(bytes, 0, static_cast<uint32_t>(textureRefs.size()));
    writeLittleEndianValue<uint32_t>(bytes, 4, 15);

    for (const std::string &textureRef : textureRefs)
    {
        const size_t offset = bytes.size();
        bytes.resize(bytes.size() + 2 + textureRef.size());
        writeLittleEndianValue<uint16_t>(bytes, offset, static_cast<uint16_t>(textureRef.size()));
        std::memcpy(bytes.data() + offset + 2, textureRef.data(), textureRef.size());
    }

    return bytes;
}
}

TEST_CASE("MM9 DAT level metadata loader reads native editor entrypoint")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(minimalMm9LevelYaml(), errorMessage);

    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());
    CHECK(metadata->formatVersion == 1);
    CHECK(metadata->kind == "mm9_level");
    CHECK(metadata->mapId == "testmap");
    CHECK(metadata->displayName == "Test Map");
    CHECK(metadata->source.dat == "../source/worlds/TESTMAP.dat");
    CHECK(metadata->source.datVersion == 66);
    CHECK(metadata->runtime.worldBackend == "dat_world");
    CHECK(metadata->runtime.classification == "dat_bsp_like");
    CHECK(metadata->sidecars.datWorld == "testmap.dat_world.yml");
    CHECK(metadata->sidecars.blvCompat == "testmap.blv");
    CHECK(!metadata->sidecars.odmCompat.has_value());
    CHECK(metadata->scripts.level == "../events/testmap.lua");
    CHECK(metadata->compatibility.generatedOdmBlvAreDerived);
    CHECK(OpenYAMM::Editor::isMm9DatLevelText(minimalMm9LevelYaml()));
}

TEST_CASE("MM9 DAT level sidecar loaders read generated editor summaries")
{
    std::string errorMessage;

    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());
    CHECK(datWorld->totals.worldModelCount == 1);
    CHECK(datWorld->coordinateSystem.source == "lithtech_mm9");
    CHECK(datWorld->coordinateSystem.scale == doctest::Approx(2.56f));
    CHECK(datWorld->worldInfo.lightMapGridSize == doctest::Approx(64.0f));
    CHECK(datWorld->worldInfo.extentsMinLt.x == doctest::Approx(-10.0f));
    CHECK(datWorld->classificationReason == "test reason");
    CHECK(datWorld->leafReferences.decode == "world_model_index_low16_poly_index_high16");
    CHECK(datWorld->leafReferences.totalRefs == 2);
    CHECK(datWorld->validation.parseStatus == "ok");
    REQUIRE(datWorld->worldModels.size() == 1);
    CHECK(datWorld->worldModels[0].sourceName == "TestModel");
    CHECK(datWorld->worldModels[0].roles.terrain);
    CHECK(datWorld->worldModels[0].textureCount == 1);
    CHECK(datWorld->worldModels[0].textures.size() == 1);
    CHECK(datWorld->worldModels[0].textures[0].sourceTexture == "TEXTURES\\Test\\test.dtx");
    CHECK(datWorld->worldModels[0].boundsMinLt.x == doctest::Approx(-1.0f));
    CHECK(datWorld->worldModels[0].worldTranslationLt.z == doctest::Approx(6.0f));
    REQUIRE(datWorld->worldModels[0].surfaceFlagHistogram.size() == 1);
    CHECK(datWorld->worldModels[0].surfaceFlagHistogram[0].key == 4);
    CHECK(datWorld->worldModels[0].surfaceFlagHistogram[0].count == 2);

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(minimalMaterialAliasesSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());
    CHECK(materials->stats.sourceModels == 1);
    REQUIRE(materials->textures.size() == 1);
    CHECK(materials->textures[0].alias == "TEST");
    CHECK(materials->textures[0].dtxSurfaceFlag == 12);
    CHECK(materials->textures[0].dtxDetailScale == doctest::Approx(5.0f));

    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(minimalRawObjectsSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());
    CHECK(rawObjects->objectCount == 1);
    REQUIRE(rawObjects->objects.size() == 1);
    CHECK(rawObjects->objects[0].name == "TestObject");
    REQUIRE(rawObjects->objects[0].properties.size() == 1);
    CHECK(rawObjects->objects[0].properties[0].valueJson == "\"T\"");
}

TEST_CASE("MM9 raw objects sidecar validation checks source indexes and raw lengths")
{
    std::string errorMessage;
    std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(minimalRawObjectsSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    CHECK(OpenYAMM::Editor::validateMm9RawObjectsSidecarReferences(*rawObjects).empty());

    rawObjects->unknownPropertyCount = 1;
    rawObjects->objects[0].objectIndex = 4;
    rawObjects->objects[0].propertyCount = 2;
    rawObjects->objects[0].dataLength = 3;
    rawObjects->objects[0].trailingHex = "xz";
    rawObjects->objects[0].properties[0].consumedDataLength = 5;

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9RawObjectsSidecarReferences(*rawObjects);

    bool foundObjectIndexMismatch = false;
    bool foundPropertyCountMismatch = false;
    bool foundRawLengthMismatch = false;
    bool foundTrailingHexIssue = false;
    bool foundDataLengthMismatch = false;
    bool foundUnknownCountMismatch = false;

    for (const std::string &issue : issues)
    {
        foundObjectIndexMismatch =
            foundObjectIndexMismatch || issue.find("object_index=4") != std::string::npos;
        foundPropertyCountMismatch =
            foundPropertyCountMismatch || issue.find("property_count mismatch") != std::string::npos;
        foundRawLengthMismatch =
            foundRawLengthMismatch || issue.find("raw hex length") != std::string::npos;
        foundTrailingHexIssue =
            foundTrailingHexIssue || issue.find("trailing hex contains non-hex") != std::string::npos;
        foundDataLengthMismatch =
            foundDataLengthMismatch || issue.find("decoded payload exceeds data_length") != std::string::npos;
        foundUnknownCountMismatch =
            foundUnknownCountMismatch || issue.find("unknown_property_count mismatch") != std::string::npos;
    }

    CHECK(foundObjectIndexMismatch);
    CHECK(foundPropertyCountMismatch);
    CHECK(foundRawLengthMismatch);
    CHECK(foundTrailingHexIssue);
    CHECK(foundDataLengthMismatch);
    CHECK(foundUnknownCountMismatch);
}

TEST_CASE("MM9 raw objects can be projected into source-preserving light objects")
{
    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 12
    name: Light
    property_count: 10
    data_length: 96
    trailing_hex: ""
    properties:
      - name: Name
        code: 0
        flags: 0
        declared_data_length: 8
        consumed_data_length: 8
        decoded: true
        raw_hex: "00"
        value_json: "\"Light72\""
      - name: Pos
        code: 1
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[10.0, 20.0, 30.0]"
      - name: Rotation
        code: 7
        flags: 0
        declared_data_length: 16
        consumed_data_length: 16
        decoded: true
        raw_hex: "00"
        value_json: "[0.0, 90.0, 0.0, 1.0]"
      - name: LightRadius
        code: 3
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "00"
        value_json: "300.0"
      - name: LightColor
        code: 2
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[255.0, 128.0, 64.0]"
      - name: LightObjects
        code: 5
        flags: 0
        declared_data_length: 1
        consumed_data_length: 1
        decoded: true
        raw_hex: "01"
        value_json: "1"
      - name: FastLightObjects
        code: 5
        flags: 0
        declared_data_length: 1
        consumed_data_length: 1
        decoded: true
        raw_hex: "00"
        value_json: "0"
      - name: ConvertToAmbient
        code: 3
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "00"
        value_json: "0.5"
      - name: Attenuation
        code: 0
        flags: 0
        declared_data_length: 8
        consumed_data_length: 8
        decoded: true
        raw_hex: "00"
        value_json: "\"Linear\""
      - name: AttCoefs
        code: 2
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[1.0, 0.0, 19.0]"
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Game::Mm9LightSourceObject> sourceObjects =
        OpenYAMM::Editor::buildMm9LightSourceObjects(*rawObjects);
    REQUIRE(sourceObjects.size() == 1);
    CHECK(sourceObjects[0].sourceObjectIndex == 12);
    CHECK(sourceObjects[0].sourceClass == "Light");
    CHECK(sourceObjects[0].properties.size() == 10);

    OpenYAMM::Game::Mm9DatWorldInfo worldInfo = {};
    worldInfo.propertyString = "AmbientLight 10 20 30";
    const OpenYAMM::Game::Mm9LightLayer lightLayer =
        OpenYAMM::Game::buildMm9LightLayer(worldInfo, sourceObjects);

    REQUIRE(lightLayer.lights.size() == 1);
    const OpenYAMM::Game::Mm9LightObject &light = lightLayer.lights[0];
    CHECK(light.sourceName == "Light72");
    CHECK(light.hasPosition);
    CHECK(light.positionLt.x == doctest::Approx(10.0f));
    CHECK(light.hasRotation);
    CHECK(light.hasLightRadius);
    CHECK(light.lightRadius == doctest::Approx(300.0f));
    CHECK(light.hasLightColor);
    CHECK(light.lightColor.g == doctest::Approx(128.0f));
    CHECK(light.hasLightObjects);
    CHECK(light.lightObjects);
    CHECK(light.hasFastLightObjects);
    CHECK(!light.fastLightObjects);
    CHECK(light.staticObjectLightEligible);
    CHECK(light.hasConvertToAmbient);
    CHECK(light.convertToAmbient == doctest::Approx(0.5f));
    CHECK(light.hasAttenuation);
    CHECK(light.attenuation == "Linear");
    REQUIRE(light.attCoefs.size() == 3);
    CHECK(light.attCoefs[2] == doctest::Approx(19.0f));
}

TEST_CASE("MM9 raw objects and asset statuses can be projected into sound objects")
{
    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 7
    name: AmbientSound
    property_count: 5
    data_length: 64
    trailing_hex: ""
    properties:
      - name: Name
        code: 0
        flags: 0
        declared_data_length: 8
        consumed_data_length: 8
        decoded: true
        raw_hex: "00"
        value_json: "\"OceanWaves\""
      - name: Pos
        code: 1
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[10.0, 20.0, 30.0]"
      - name: SoundPos
        code: 1
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[11.0, 22.0, 33.0]"
      - name: SoundRadius
        code: 3
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "00"
        value_json: "512.0"
      - name: SoundFile
        code: 0
        flags: 0
        declared_data_length: 32
        consumed_data_length: 32
        decoded: true
        raw_hex: "00"
        value_json: "\"Sounds\\\\Ambient\\\\Water\\\\waves-ocean02.wav\""
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus soundStatus = {};
    soundStatus.sourceObjectIndex = 7;
    soundStatus.sourceClass = "AmbientSound";
    soundStatus.objectName = "OceanWaves";
    soundStatus.propertyIndex = 4;
    soundStatus.propertyName = "SoundFile";
    soundStatus.sourceFamily = "sounds";
    soundStatus.sourceValue = "Sounds\\Ambient\\Water\\waves-ocean02.wav";
    soundStatus.normalizedKey = "ambient/water/waves-ocean02.wav";
    soundStatus.resolvedSourcePath = "source/sounds/AMBIENT/WATER/WAVES-OCEAN02.WAV";
    soundStatus.required = true;
    soundStatus.resolved = true;

    const std::vector<OpenYAMM::Game::Mm9SoundSourceObject> sourceObjects =
        OpenYAMM::Editor::buildMm9SoundSourceObjects(*rawObjects, {soundStatus});
    REQUIRE(sourceObjects.size() == 1);
    CHECK(sourceObjects[0].sourceObjectIndex == 7);
    CHECK(sourceObjects[0].sourceName == "OceanWaves");
    CHECK(sourceObjects[0].hasPosition);
    CHECK(sourceObjects[0].positionLt.z == doctest::Approx(30.0f));
    CHECK(sourceObjects[0].hasSoundPosition);
    CHECK(sourceObjects[0].soundPositionLt.y == doctest::Approx(22.0f));
    CHECK(sourceObjects[0].hasSoundRadius);
    CHECK(sourceObjects[0].soundRadius == doctest::Approx(512.0f));
    REQUIRE(sourceObjects[0].references.size() == 1);
    CHECK(sourceObjects[0].references[0].resolved);
    CHECK(sourceObjects[0].references[0].sourceFamily == "sounds");

    const OpenYAMM::Game::Mm9SoundLayer soundLayer =
        OpenYAMM::Game::buildMm9SoundLayer(sourceObjects);
    REQUIRE(soundLayer.objects.size() == 1);
    CHECK(soundLayer.referenceCount == 1);
    CHECK(soundLayer.resolvedReferenceCount == 1);
    CHECK(soundLayer.unresolvedRequiredReferenceCount == 0);
    CHECK(soundLayer.soundReferenceCount == 1);
    CHECK(soundLayer.voiceReferenceCount == 0);
}

TEST_CASE("MM9 raw objects can be projected into source-preserving spawn objects")
{
    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 42
    name: TownHuman2MaleA
    property_count: 8
    data_length: 96
    trailing_hex: ""
    properties:
      - name: Name
        code: 0
        flags: 0
        declared_data_length: 10
        consumed_data_length: 10
        decoded: true
        raw_hex: "00"
        value_json: "\"Guard01\""
      - name: Pos
        code: 1
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[100.0, 200.0, 300.0]"
      - name: Rotation
        code: 7
        flags: 0
        declared_data_length: 16
        consumed_data_length: 16
        decoded: true
        raw_hex: "00"
        value_json: "[0.0, 90.0, 0.0, 1.0]"
      - name: SpawnLevel
        code: 6
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "00"
        value_json: "3"
      - name: SpawnObject
        code: 0
        flags: 0
        declared_data_length: 14
        consumed_data_length: 14
        decoded: true
        raw_hex: "00"
        value_json: "\"spawnloc.scr\""
      - name: SpawnObjectVel
        code: 1
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[1.0, 2.0, 3.0]"
      - name: NPCProps
        code: 6
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "00"
        value_json: "5"
      - name: NPCNbr
        code: 6
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "00"
        value_json: "378"
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Game::Mm9SpawnSourceObject> sourceObjects =
        OpenYAMM::Editor::buildMm9SpawnSourceObjects(*rawObjects);
    REQUIRE(sourceObjects.size() == 1);
    CHECK(sourceObjects[0].sourceObjectIndex == 42);
    CHECK(sourceObjects[0].sourceClass == "TownHuman2MaleA");
    CHECK(sourceObjects[0].sourceName == "Guard01");
    CHECK(sourceObjects[0].hasPosition);
    CHECK(sourceObjects[0].positionLt.z == doctest::Approx(300.0f));
    CHECK(sourceObjects[0].hasRotation);
    REQUIRE(sourceObjects[0].spawnLevel.has_value());
    CHECK(*sourceObjects[0].spawnLevel == 3);
    REQUIRE(sourceObjects[0].spawnObject.has_value());
    CHECK(*sourceObjects[0].spawnObject == "spawnloc.scr");
    CHECK(sourceObjects[0].hasSpawnObjectVelocity);
    CHECK(sourceObjects[0].spawnObjectVelocityLt.y == doctest::Approx(2.0f));
    REQUIRE(sourceObjects[0].npcProps.has_value());
    CHECK(*sourceObjects[0].npcProps == 5);
    REQUIRE(sourceObjects[0].npcNumber.has_value());
    CHECK(*sourceObjects[0].npcNumber == 378);

    const OpenYAMM::Game::Mm9SpawnLayer spawnLayer =
        OpenYAMM::Game::buildMm9SpawnLayer(sourceObjects);
    REQUIRE(spawnLayer.objects.size() == 1);
    CHECK(spawnLayer.spawnLevelCount == 1);
    CHECK(spawnLayer.spawnObjectCount == 1);
    CHECK(spawnLayer.spawnObjectVelocityCount == 1);
    CHECK(spawnLayer.npcPropertyCount == 1);
    CHECK(spawnLayer.npcNumberCount == 1);
}

TEST_CASE("MM9 raw objects can be projected into source-preserving object transforms")
{
    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 9
    name: Trigger
    property_count: 9
    data_length: 96
    trailing_hex: ""
    properties:
      - name: Name
        code: 0
        flags: 0
        declared_data_length: 16
        consumed_data_length: 16
        decoded: true
        raw_hex: "00"
        value_json: "\"DoorTrigger\""
      - name: Pos
        code: 1
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[10.0, 20.0, 30.0]"
      - name: Rotation
        code: 7
        flags: 0
        declared_data_length: 16
        consumed_data_length: 16
        decoded: true
        raw_hex: "00"
        value_json: "[0.0, 90.0, 0.0, 1.0]"
      - name: Scale
        code: 3
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "00"
        value_json: "1.5"
      - name: Dims
        code: 1
        flags: 0
        declared_data_length: 12
        consumed_data_length: 12
        decoded: true
        raw_hex: "00"
        value_json: "[100.0, 200.0, 300.0]"
      - name: Radius
        code: 3
        flags: 0
        declared_data_length: 4
        consumed_data_length: 4
        decoded: true
        raw_hex: "00"
        value_json: "256.0"
      - name: Visible
        code: 5
        flags: 0
        declared_data_length: 1
        consumed_data_length: 1
        decoded: true
        raw_hex: "01"
        value_json: "1"
      - name: Solid
        code: 5
        flags: 0
        declared_data_length: 1
        consumed_data_length: 1
        decoded: true
        raw_hex: "00"
        value_json: "0"
      - name: Trigger
        code: 5
        flags: 0
        declared_data_length: 1
        consumed_data_length: 1
        decoded: true
        raw_hex: "01"
        value_json: "1"
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Game::Mm9ObjectSourceObject> sourceObjects =
        OpenYAMM::Editor::buildMm9ObjectSourceObjects(*rawObjects);
    REQUIRE(sourceObjects.size() == 1);
    CHECK(sourceObjects[0].sourceObjectIndex == 9);
    CHECK(sourceObjects[0].sourceClass == "Trigger");
    CHECK(sourceObjects[0].sourceName == "DoorTrigger");
    CHECK(sourceObjects[0].hasPosition);
    CHECK(sourceObjects[0].positionLt.y == doctest::Approx(20.0f));
    CHECK(sourceObjects[0].hasRotation);
    CHECK(sourceObjects[0].hasScale);
    CHECK(sourceObjects[0].scale == doctest::Approx(1.5f));
    CHECK(sourceObjects[0].hasDims);
    CHECK(sourceObjects[0].dimsLt.z == doctest::Approx(300.0f));
    CHECK(sourceObjects[0].hasRadius);
    CHECK(sourceObjects[0].radius == doctest::Approx(256.0f));
    REQUIRE(sourceObjects[0].visible.has_value());
    CHECK(*sourceObjects[0].visible);
    REQUIRE(sourceObjects[0].solid.has_value());
    CHECK_FALSE(*sourceObjects[0].solid);
    REQUIRE(sourceObjects[0].trigger.has_value());
    CHECK(*sourceObjects[0].trigger);

    const OpenYAMM::Game::Mm9ObjectLayer objectLayer =
        OpenYAMM::Game::buildMm9ObjectLayer(sourceObjects);
    REQUIRE(objectLayer.objects.size() == 1);
    CHECK(objectLayer.positionedObjectCount == 1);
    CHECK(objectLayer.boundsEvidenceObjectCount == 1);
    CHECK(objectLayer.triggerObjectCount == 1);
    CHECK(objectLayer.triggerVolumeCount == 1);
    CHECK(objectLayer.visibleObjectCount == 1);
    CHECK(objectLayer.solidObjectCount == 0);
}

TEST_CASE("MM9 events validation checks raw object and binding references")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(
            mm9LevelYamlWithContentHash("947d5a35ff2fe522fda5b431af955e3b27955ebc18c9e3684b07b51ae112461f"),
            errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());

    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(minimalRawObjectsSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    OpenYAMM::Game::Mm9EventsYmlLoader eventsLoader = {};
    std::optional<OpenYAMM::Game::Mm9EventsData> events =
        eventsLoader.loadFromText(minimalEventsSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(events.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_events_validation_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeTextFile(tempRoot / "events/testmap.lua", "-- generated test lua\n");

    CHECK(OpenYAMM::Editor::validateMm9EventsReferences(
        levelPath,
        *metadata,
        *datWorld,
        *rawObjects,
        *events).empty());

    OpenYAMM::Game::Mm9EventsData luaDriftEvents = *events;
    luaDriftEvents.generatedLua = "../events/authored_override.lua";
    const std::vector<std::string> luaDriftIssues =
        OpenYAMM::Editor::validateMm9EventsReferences(
            levelPath,
            *metadata,
            *datWorld,
            *rawObjects,
            luaDriftEvents);

    bool foundLuaDrift = false;

    for (const std::string &issue : luaDriftIssues)
    {
        foundLuaDrift =
            foundLuaDrift || issue.find("generated Lua path does not match level script path") != std::string::npos;
    }

    CHECK(foundLuaDrift);

    events->objects[0].sourceObjectIndex = 99;
    events->bindings.push_back({});
    events->bindings.back().objectId = "missing";
    events->bindings.back().sourceObjectIndex = 99;

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9EventsReferences(levelPath, *metadata, *datWorld, *rawObjects, *events);

    bool foundInvalidObjectIndex = false;
    bool foundMissingBindingObject = false;
    bool foundInvalidBindingIndex = false;

    for (const std::string &issue : issues)
    {
        foundInvalidObjectIndex =
            foundInvalidObjectIndex || issue.find("invalid source_object_index 99") != std::string::npos;
        foundMissingBindingObject =
            foundMissingBindingObject || issue.find("binding references missing event object") != std::string::npos;
        foundInvalidBindingIndex =
            foundInvalidBindingIndex || issue.find("binding missing references invalid") != std::string::npos;
    }

    CHECK(foundInvalidObjectIndex);
    CHECK(foundMissingBindingObject);
    CHECK(foundInvalidBindingIndex);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 DAT world sidecar validation checks source-index and total consistency")
{
    std::string errorMessage;
    std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    CHECK(OpenYAMM::Editor::validateMm9DatWorldSidecarReferences(*datWorld).empty());

    datWorld->totals.invalidLeafReferenceCount = 1;
    datWorld->worldModels[0].sourceModelIndex = 4;
    datWorld->worldModels[0].textures[0].textureIndex = 3;
    datWorld->worldModels[0].textures[0].sourceTexture.clear();
    datWorld->worldModels[0].referenceValidation.invalidSurfaceTextureRefs = 1;
    datWorld->worldModels[0].referenceValidation.invalidPolySurfaceRefs = 2;
    datWorld->worldModels[0].referenceValidation.invalidPolyPlaneRefs = 3;
    datWorld->worldModels[0].referenceValidation.invalidPolyVertexRefs = 4;
    datWorld->worldModels[0].referenceValidation.invalidNodePolyRefs = 5;
    datWorld->worldModels[0].referenceValidation.invalidRootNodeRefs = 6;

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9DatWorldSidecarReferences(*datWorld);

    bool foundInvalidLeafRef = false;
    bool foundModelIndexMismatch = false;
    bool foundTextureIndexMismatch = false;
    bool foundEmptyTexture = false;
    bool foundSurfaceTextureRef = false;
    bool foundPolySurfaceRef = false;
    bool foundPolyPlaneRef = false;
    bool foundPolyVertexRef = false;
    bool foundNodePolyRef = false;
    bool foundRootNodeRef = false;

    for (const std::string &issue : issues)
    {
        foundInvalidLeafRef =
            foundInvalidLeafRef || issue.find("invalid leaf polygon references") != std::string::npos;
        foundModelIndexMismatch =
            foundModelIndexMismatch || issue.find("source_model_index=4") != std::string::npos;
        foundTextureIndexMismatch =
            foundTextureIndexMismatch || issue.find("texture index mismatch") != std::string::npos;
        foundEmptyTexture =
            foundEmptyTexture || issue.find("source texture path is empty") != std::string::npos;
        foundSurfaceTextureRef =
            foundSurfaceTextureRef || issue.find("invalid surface texture references") != std::string::npos;
        foundPolySurfaceRef =
            foundPolySurfaceRef || issue.find("invalid polygon surface references") != std::string::npos;
        foundPolyPlaneRef =
            foundPolyPlaneRef || issue.find("invalid polygon plane references") != std::string::npos;
        foundPolyVertexRef =
            foundPolyVertexRef || issue.find("invalid polygon vertex references") != std::string::npos;
        foundNodePolyRef =
            foundNodePolyRef || issue.find("invalid node polygon references") != std::string::npos;
        foundRootNodeRef =
            foundRootNodeRef || issue.find("invalid root node references") != std::string::npos;
    }

    CHECK(foundInvalidLeafRef);
    CHECK(foundModelIndexMismatch);
    CHECK(foundTextureIndexMismatch);
    CHECK(foundEmptyTexture);
    CHECK(foundSurfaceTextureRef);
    CHECK(foundPolySurfaceRef);
    CHECK(foundPolyPlaneRef);
    CHECK(foundPolyVertexRef);
    CHECK(foundNodePolyRef);
    CHECK(foundRootNodeRef);
}

TEST_CASE("MM9 material texture inspection resolves source DTX headers and generated caches")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(minimalMaterialAliasesSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_texture_status_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    const std::filesystem::path sourceDtxPath = tempRoot / "source/textures/TEST/TEST.dtx";
    const std::filesystem::path cacheBitmapPath = tempRoot / "maps/testmap.bitmaps/TEST.bmp";
    writeBinaryFile(sourceDtxPath, makeDtxHeaderBytes());
    writeMatchingDecodedDtxCacheBmp(cacheBitmapPath);

    const std::filesystem::file_time_type sourceTime =
        std::filesystem::file_time_type::clock::now() - std::chrono::hours(1);
    const std::filesystem::file_time_type cacheTime =
        std::filesystem::file_time_type::clock::now();
    std::filesystem::last_write_time(sourceDtxPath, sourceTime);
    std::filesystem::last_write_time(cacheBitmapPath, cacheTime);

    OpenYAMM::Editor::EditorMm9MaterialInspectionCache inspectionCache;
    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(
            levelPath,
            *datWorld,
            *materials,
            &inspectionCache);

    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].alias == "TEST");
    CHECK(statuses[0].datReferenceCount == 1);
    CHECK(statuses[0].materialAliasCountForSource == 1);
    CHECK(statuses[0].sourceDtxCandidateCount == 1);
    CHECK(statuses[0].sourceDtxResolved);
    CHECK(!statuses[0].sourceDtxAmbiguous);
    REQUIRE(statuses[0].sourceDtxCandidates.size() == 1);
    CHECK(statuses[0].sourceDtxCandidates[0].find("source/textures/TEST/TEST.dtx") != std::string::npos);
    CHECK(statuses[0].sourcePathExists);
    CHECK(statuses[0].cachePathExists);
    CHECK(statuses[0].sourceDtxHashLoaded);
    CHECK(statuses[0].sourceDtxSha256.size() == 64);
    CHECK(statuses[0].sourceDtxSizeBytes == makeDtxHeaderBytes().size());
    CHECK(statuses[0].cacheHashLoaded);
    CHECK(statuses[0].cacheSha256.size() == 64);
    CHECK(statuses[0].cacheSizeBytes > 0);
    CHECK(statuses[0].cacheFreshnessKnown);
    CHECK(statuses[0].cacheNewerThanSource);
    CHECK(!statuses[0].cacheOlderThanSource);
    CHECK(statuses[0].cacheDeterminismChecked);
    CHECK(statuses[0].sourceDtxDecodedForCache);
    CHECK(statuses[0].cacheImageDecoded);
    CHECK(statuses[0].cacheMatchesDecodedSource);
    CHECK(statuses[0].dtxHeaderLoaded);
    CHECK(statuses[0].dtxHeaderMatchesSidecar);
    REQUIRE(statuses[0].dtxHeader.has_value());
    CHECK(statuses[0].dtxHeader->version == -5);
    CHECK(statuses[0].dtxHeader->sectionCount == 0);
    CHECK(statuses[0].dtxHeader->flags == 8);
    CHECK(statuses[0].dtxHeader->userFlags == 12);
    CHECK(statuses[0].dtxHeader->surfaceFlag == 12);
    CHECK(statuses[0].dtxHeader->extraBytes[0] == 2);
    CHECK(statuses[0].dtxHeader->extraBytes[1] == 4);
    CHECK(statuses[0].dtxHeader->extraBytes[2] == 4);

    CHECK(OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses).empty());

    const size_t indexBuildCountAfterFirstRead = inspectionCache.sourceDtxIndexBuildCount;
    const size_t hashReadCountAfterFirstRead = inspectionCache.fileHashReadCount;
    const size_t headerReadCountAfterFirstRead = inspectionCache.dtxHeaderReadCount;
    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> cachedStatuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(
            levelPath,
            *datWorld,
            *materials,
            &inspectionCache);

    REQUIRE(cachedStatuses.size() == 1);
    CHECK(cachedStatuses[0].sourceDtxSha256 == statuses[0].sourceDtxSha256);
    CHECK(cachedStatuses[0].cacheSha256 == statuses[0].cacheSha256);
    CHECK(inspectionCache.sourceDtxIndexBuildCount == indexBuildCountAfterFirstRead);
    CHECK(inspectionCache.fileHashReadCount == hashReadCountAfterFirstRead);
    CHECK(inspectionCache.dtxHeaderReadCount == headerReadCountAfterFirstRead);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 material texture validation reports material alias mapping data loss")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::string materialAliasesYaml = R"(
format_version: 1
kind: mm9_material_aliases
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
textures:
  - alias: TEST
    width: 128
    height: 64
)";

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(materialAliasesYaml, errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path levelPath =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_alias_data_loss_test/maps/testmap.level.yml";
    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(levelPath, *datWorld, *materials);

    REQUIRE(statuses.size() == 2);
    CHECK(statuses[0].materialAliasEntry);
    CHECK(statuses[0].aliasFieldPresent);
    CHECK(!statuses[0].sourceTextureFieldPresent);
    CHECK(!statuses[0].emittedBitmapFieldPresent);
    CHECK(!statuses[0].emittedBitmapModeFieldPresent);

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses);

    bool foundMissingSourceTexture = false;
    bool foundMissingEmittedBitmap = false;
    bool foundMissingEmittedBitmapMode = false;

    for (const std::string &issue : issues)
    {
        foundMissingSourceTexture =
            foundMissingSourceTexture || issue.find("missing source_texture") != std::string::npos;
        foundMissingEmittedBitmap =
            foundMissingEmittedBitmap || issue.find("missing emitted_bitmap:") != std::string::npos;
        foundMissingEmittedBitmapMode =
            foundMissingEmittedBitmapMode || issue.find("missing emitted_bitmap_mode") != std::string::npos;
    }

    CHECK(foundMissingSourceTexture);
    CHECK(foundMissingEmittedBitmap);
    CHECK(foundMissingEmittedBitmapMode);
}

TEST_CASE("MM9 material texture validation rejects decoded caches that drift from source DTX pixels")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(minimalMaterialAliasesSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_cache_drift_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeBinaryFile(tempRoot / "source/textures/TEST/TEST.dtx", makeDtxHeaderBytes());

    std::vector<uint8_t> driftedPixels = makeDecodedDxt1ZeroPixelsBgra();
    driftedPixels[0] = 17;
    writeBgra32BmpFile(tempRoot / "maps/testmap.bitmaps/TEST.bmp", 128, 64, driftedPixels);

    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(levelPath, *datWorld, *materials);
    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].cacheDeterminismChecked);
    CHECK(statuses[0].sourceDtxDecodedForCache);
    CHECK(statuses[0].cacheImageDecoded);
    CHECK(!statuses[0].cacheMatchesDecodedSource);

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses);

    bool foundCacheDrift = false;

    for (const std::string &issue : issues)
    {
        foundCacheDrift =
            foundCacheDrift || issue.find("generated cache is not deterministic") != std::string::npos;
    }

    CHECK(foundCacheDrift);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 material texture inspection resolves source SPR frame DTX references")
{
    std::string errorMessage;
    std::string datWorldYaml = minimalDatWorldSidecarYaml();
    const std::string dtxReference = "TEXTURES\\Test\\test.dtx";
    const size_t dtxReferencePosition = datWorldYaml.find(dtxReference);
    REQUIRE(dtxReferencePosition != std::string::npos);
    datWorldYaml.replace(
        dtxReferencePosition,
        dtxReference.size(),
        "Sprites\\Water\\Water115.spr");

    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(datWorldYaml, errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::string materialYaml = R"(
format_version: 1
kind: mm9_material_aliases
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
stats: {}
textures:
  - alias: WATER115
    source_texture: Sprites\Water\Water115.spr
    width: 256
    height: 256
    physical_path: ""
    emitted_bitmap: testmap.bitmaps/WATER115.bmp
    emitted_bitmap_mode: sprite
)";

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(materialYaml, errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_sprite_status_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeBinaryFile(
        tempRoot / "source/sprites/WATER/WATER115.spr",
        makeSprBytes({
            "SpriteTextures\\Water\\Water115\\Water115_0000.dtx",
            "SpriteTextures\\Water\\Water115\\Water115_0001.dtx"
        }));
    writeBinaryFile(tempRoot / "source/sprite_textures/WATER/WATER115/WATER115_0000.dtx", makeDtxHeaderBytes());
    writeBinaryFile(tempRoot / "source/sprite_textures/WATER/WATER115/WATER115_0001.dtx", makeDtxHeaderBytes());
    writeTextFile(tempRoot / "maps/testmap.bitmaps/WATER115.bmp", "bmp");

    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(levelPath, *datWorld, *materials);
    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].sourceAssetFamily == "sprites");
    CHECK(statuses[0].sourceSpriteResolved);
    CHECK(!statuses[0].sourceSpriteAmbiguous);
    CHECK(statuses[0].sourceSpritePathExists);
    CHECK(statuses[0].sourceSpriteParsed);
    CHECK(statuses[0].spriteFrameTextureCount == 2);
    CHECK(statuses[0].resolvedSpriteFrameTextureCount == 2);
    CHECK(statuses[0].resolvedSpriteFrameTexturePaths.size() == 2);
    CHECK(statuses[0].resolvedSpriteFrameTexturePaths[0].find("WATER115_0000.dtx") != std::string::npos);
    CHECK(statuses[0].resolvedSpriteFrameTexturePaths[1].find("WATER115_0001.dtx") != std::string::npos);
    CHECK(statuses[0].unresolvedSpriteFrameTextureCount == 0);
    CHECK(statuses[0].ambiguousSpriteFrameTextureCount == 0);
    CHECK(OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses).empty());

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 material texture validation rejects ambiguous case-folded source DTX paths")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(minimalMaterialAliasesSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_texture_ambiguous_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeBinaryFile(tempRoot / "source/textures/TEST/TEST.dtx", makeDtxHeaderBytes());
    writeBinaryFile(tempRoot / "source/textures/test/test.DTX", makeDtxHeaderBytes());
    writeTextFile(tempRoot / "maps/testmap.bitmaps/TEST.bmp", "bmp");

    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(levelPath, *datWorld, *materials);
    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].sourceDtxCandidateCount == 2);
    CHECK(!statuses[0].sourceDtxResolved);
    CHECK(statuses[0].sourceDtxAmbiguous);

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses);

    bool foundAmbiguousSource = false;
    bool foundFirstCandidate = false;
    bool foundSecondCandidate = false;

    for (const std::string &issue : issues)
    {
        foundAmbiguousSource =
            foundAmbiguousSource || issue.find("ambiguous source DTX files") != std::string::npos;
        foundFirstCandidate =
            foundFirstCandidate || issue.find("source/textures/TEST/TEST.dtx") != std::string::npos;
        foundSecondCandidate =
            foundSecondCandidate || issue.find("source/textures/test/test.DTX") != std::string::npos;
    }

    CHECK(foundAmbiguousSource);
    CHECK(foundFirstCandidate);
    CHECK(foundSecondCandidate);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 material texture validation reports missing required source DTX paths")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(minimalMaterialAliasesSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_texture_missing_dtx_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeTextFile(tempRoot / "maps/testmap.bitmaps/TEST.bmp", "bmp");

    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(levelPath, *datWorld, *materials);
    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].datReferenceCount > 0);
    CHECK(statuses[0].sourceDtxCandidateCount == 0);
    CHECK(!statuses[0].sourceDtxResolved);
    CHECK(!statuses[0].placeholderMissingSource);

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses);

    bool foundMissingSourceDtx = false;

    for (const std::string &issue : issues)
    {
        foundMissingSourceDtx =
            foundMissingSourceDtx || issue.find("resolves to no source DTX") != std::string::npos;
    }

    CHECK(foundMissingSourceDtx);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 material texture inspection treats hidden Default helper material as built-in")
{
    std::string errorMessage;
    std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    datWorld->worldModels[0].textures[0].sourceTexture = "Default";
    datWorld->worldModels[0].roles.visible = false;
    datWorld->worldModels[0].roles.terrain = false;
    datWorld->worldModels[0].roles.triggerOrVolume = true;
    datWorld->worldModels[0].roles.movable = true;

    const std::string materialYaml = R"(
format_version: 1
kind: mm9_material_aliases
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
stats: {}
textures:
  - alias: DEFAULT
    source_texture: Default
    width: 256
    height: 256
    physical_path: ""
    emitted_bitmap: testmap.bitmaps/DEFAULT.bmp
    emitted_bitmap_mode: placeholder_missing_source
)";

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(materialYaml, errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path levelPath =
        std::filesystem::temp_directory_path() / "openyamm_mm9_default_helper_material_test/maps/testmap.level.yml";
    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(levelPath, *datWorld, *materials);

    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].sourceTexture == "Default");
    CHECK(statuses[0].sourceAssetFamily == "builtin");
    CHECK(statuses[0].resolutionSource == "lithtech_default_helper_material");
    CHECK(statuses[0].defaultHelperMaterial);
    CHECK(statuses[0].placeholderMissingSource);
    CHECK(statuses[0].datReferenceCount == 1);
    CHECK(statuses[0].defaultRenderableDatReferenceCount == 0);
    CHECK(statuses[0].helperOnlyDatReferenceCount == 1);
    CHECK(statuses[0].sourceDtxCandidateCount == 0);
    CHECK(!statuses[0].sourceDtxResolved);
    CHECK(OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses).empty());
}

TEST_CASE("MM9 material texture inspection resolves unique basename fallback")
{
    std::string errorMessage;
    std::string datWorldYaml = minimalDatWorldSidecarYaml();
    const std::string originalReference = "TEXTURES\\Test\\test.dtx";
    const size_t referencePosition = datWorldYaml.find(originalReference);
    REQUIRE(referencePosition != std::string::npos);
    datWorldYaml.replace(referencePosition, originalReference.size(), "TEXTURES\\LevelTextures\\Invisible.dtx");

    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(datWorldYaml, errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::string materialYaml = R"(
format_version: 1
kind: mm9_material_aliases
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
stats: {}
textures:
  - alias: INVISIBLE
    source_texture: TEXTURES\LevelTextures\Invisible.dtx
    width: 128
    height: 64
    physical_path: ""
    emitted_bitmap: testmap.bitmaps/INVISIBLE.bmp
    emitted_bitmap_mode: placeholder_missing_source
    dtx_surface_flag: 12
    dtx_texture_group: 2
    dtx_bpp: 4
    dtx_mipmap_count: 4
    dtx_mipmaps_used: 4
    dtx_flags: 8
    dtx_detail_scale: 5.0
    dtx_detail_angle: 0
    dtx_command_string: DetailTex Textures\detailtextures\det_01.dtx
)";

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(materialYaml, errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_basename_fallback_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeBinaryFile(
        tempRoot / "source/textures/LEVELTEXTURES/MISC/INVISIBLE.dtx",
        makeDtxHeaderBytes());
    writeTextFile(tempRoot / "maps/testmap.bitmaps/INVISIBLE.bmp", "bmp");

    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(levelPath, *datWorld, *materials);
    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].sourceDtxResolved);
    CHECK(!statuses[0].sourceDtxAmbiguous);
    REQUIRE(statuses[0].sourceDtxCandidates.size() == 1);
    CHECK(statuses[0].sourceDtxCandidates[0].find("LEVELTEXTURES/MISC/INVISIBLE.dtx") != std::string::npos);
    CHECK(statuses[0].sourcePathExists);
    CHECK(statuses[0].dtxHeaderLoaded);
    CHECK(statuses[0].dtxHeaderMatchesSidecar);
    CHECK(OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses).empty());

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 material texture inspection applies scoped source asset aliases")
{
    std::string errorMessage;
    std::string datWorldYaml = minimalDatWorldSidecarYaml();
    const std::string originalReference = "TEXTURES\\Test\\test.dtx";
    const std::string missingReference = "TEXTURES\\ENVIRONMENTMAPS\\MountainSky\\MTN_Down.dtx";
    const size_t referencePosition = datWorldYaml.find(originalReference);
    REQUIRE(referencePosition != std::string::npos);
    datWorldYaml.replace(referencePosition, originalReference.size(), missingReference);

    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(datWorldYaml, errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    const std::string materialYaml = R"(
format_version: 1
kind: mm9_material_aliases
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
stats: {}
textures:
  - alias: MTNDOWN
    source_texture: TEXTURES\ENVIRONMENTMAPS\MountainSky\MTN_Down.dtx
    width: 256
    height: 256
    physical_path: ""
    emitted_bitmap: testmap.bitmaps/MTNDOWN.bmp
    emitted_bitmap_mode: placeholder_missing_source
)";

    const std::string levelText = R"(
format_version: 1
kind: mm9_level
map_id: testmap
display_name: Test Map
source:
  dat: ../source/worlds/TESTMAP.dat
  manifest: ../source/manifest.yml
  original_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
  source_game: mm9
  dat_version: 66
  content_hash: abc123
runtime:
  world_backend: dat_world
  classification: dat_bsp_like
  classification_confidence: high
  visibility: dat_portal_bsp
  collision: dat_physics_bsp
  render: dat_render_world
  sky: true
sidecars:
  dat_world: testmap.dat_world.yml
  raw_objects: testmap.raw_objects.yml
  materials: testmap.material_aliases.yml
  events: testmap.events.yml
  source_asset_aliases: ../import/overrides/testmap.source_asset_aliases.yml
scripts:
  level: ../events/testmap.lua
  script_ir: ../events/testmap.script_ir.yml
compatibility:
  legacy_target_format: odm
  generated_odm_blv_are_derived: true
)";

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(materialYaml, errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(levelText, errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_source_alias_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeBinaryFile(tempRoot / "source/textures/SKYBOX/SNOWMTNS_DOWN.dtx", makeDtxHeaderBytes());
    writeTextFile(tempRoot / "import/overrides/testmap.source_asset_aliases.yml", R"(
format_version: 1
kind: mm9_source_asset_aliases
aliases:
  - source_family: textures
    requested: TEXTURES\ENVIRONMENTMAPS\MountainSky\MTN_Down.dtx
    resolved: TEXTURES\Skybox\SnowMtns_Down.dtx
    scope:
      maps: [testmap]
    reason: "test scoped skybox material alias"
)");

    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(
            levelPath,
            *datWorld,
            *materials,
            nullptr,
            &*metadata);

    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].sourceDtxResolved);
    CHECK(!statuses[0].sourceDtxAmbiguous);
    CHECK(statuses[0].aliasApplied);
    CHECK(statuses[0].aliasTargetKey == "skybox/snowmtns_down.dtx");
    CHECK(statuses[0].resolutionSource == "source_asset_alias");
    CHECK(statuses[0].sourceDtxCandidates.size() == 1);
    CHECK(statuses[0].sourceDtxCandidates[0].find("SKYBOX/SNOWMTNS_DOWN.dtx") != std::string::npos);
    CHECK(statuses[0].sourcePathExists);
    CHECK(statuses[0].dtxHeaderLoaded);
    CHECK(OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses).empty());

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 material texture validation reports ambiguous aliases and stale DTX metadata")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
        OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(minimalDatWorldSidecarYaml(), errorMessage);
    REQUIRE_MESSAGE(datWorld.has_value(), errorMessage.c_str());

    std::string materialYaml = minimalMaterialAliasesSidecarYaml();
    materialYaml += R"(
  - alias: TESTCOPY
    source_texture: TEXTURES\Test\test.dtx
    width: 128
    height: 64
    physical_path: mm9/extracted/TEXTURES/TEXTURES/TEST/TEST.dtx
    emitted_bitmap: testmap.bitmaps/TESTCOPY.bmp
    emitted_bitmap_mode: dxt1
    dtx_surface_flag: 13
    dtx_texture_group: 2
    dtx_bpp: 4
    dtx_mipmap_count: 4
    dtx_mipmaps_used: 4
    dtx_flags: 8
    dtx_detail_scale: 5.0
    dtx_detail_angle: 0
    dtx_command_string: DetailTex Textures\detailtextures\det_01.dtx
)";

    const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
        OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(materialYaml, errorMessage);
    REQUIRE_MESSAGE(materials.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_material_texture_stale_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeBinaryFile(tempRoot / "source/textures/TEST/TEST.dtx", makeDtxHeaderBytes());
    writeTextFile(tempRoot / "maps/testmap.bitmaps/TEST.bmp", "bmp");
    writeTextFile(tempRoot / "maps/testmap.bitmaps/TESTCOPY.bmp", "bmp");

    const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
        OpenYAMM::Editor::inspectMm9MaterialTextureReferences(levelPath, *datWorld, *materials);
    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses);

    bool foundAmbiguousAlias = false;
    bool foundHeaderMismatch = false;

    for (const std::string &issue : issues)
    {
        foundAmbiguousAlias =
            foundAmbiguousAlias || issue.find("ambiguous material aliases") != std::string::npos;
        foundHeaderMismatch =
            foundHeaderMismatch || issue.find("header differs from material sidecar") != std::string::npos;
    }

    CHECK(foundAmbiguousAlias);
    CHECK(foundHeaderMismatch);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 source asset manifest loader reads family mappings")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9SourceAssetManifest> manifest =
        OpenYAMM::Editor::loadMm9SourceAssetManifestFromText(minimalSourceAssetManifestYaml(), errorMessage);

    REQUIRE_MESSAGE(manifest.has_value(), errorMessage.c_str());
    CHECK(manifest->kind == "mm9_source_asset_manifest");
    CHECK(manifest->formatVersion == 1);
    CHECK(manifest->sourceRoot == "mm9/extracted");
    CHECK(manifest->packageRoot == "assets_dev/worlds/mm9/source");
    CHECK(manifest->policy.sourceTruth);
    CHECK(!manifest->policy.generatedCache);
    REQUIRE(manifest->families.size() == 14);
    CHECK(manifest->families[0].id == "worlds");
    CHECK(manifest->families[0].package == "worlds");
    CHECK(manifest->families[0].fileCount == 1);
}

TEST_CASE("MM9 source asset manifest validation reports missing families and count drift")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9SourceAssetManifest> manifest =
        OpenYAMM::Editor::loadMm9SourceAssetManifestFromText(
            minimalSourceAssetManifestYaml(2, false),
            errorMessage);

    REQUIRE_MESSAGE(manifest.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_source_manifest_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path manifestPath = tempRoot / "source/manifest.yml";
    writeTextFile(tempRoot / "source/worlds/TESTMAP.dat", "dat");

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9SourceAssetManifestFiles(manifestPath, *manifest);

    bool foundWorldCountMismatch = false;
    bool foundMissingTextures = false;
    bool foundMissingSkinsDirectory = false;

    for (const std::string &issue : issues)
    {
        foundWorldCountMismatch =
            foundWorldCountMismatch || issue.find("file count mismatch for family worlds") != std::string::npos;
        foundMissingTextures =
            foundMissingTextures || issue.find("required family: textures") != std::string::npos;
        foundMissingSkinsDirectory =
            foundMissingSkinsDirectory || issue.find("package directory is missing for family skins")
                != std::string::npos;
    }

    CHECK(foundWorldCountMismatch);
    CHECK(foundMissingTextures);
    CHECK(foundMissingSkinsDirectory);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 DAT document path inventory separates read-only source from generated state")
{
    std::string errorMessage;
    std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(minimalMm9LevelYaml(), errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_document_path_roles_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";
    writeTextFile(levelPath, minimalMm9LevelYaml());
    writeTextFile(tempRoot / "source/worlds/TESTMAP.dat", "dat");
    writeTextFile(tempRoot / "source/manifest.yml", minimalSourceAssetManifestYaml());
    writeTextFile(tempRoot / "maps/testmap.dat_world.yml", minimalDatWorldSidecarYaml());
    writeTextFile(tempRoot / "maps/testmap.raw_objects.yml", minimalRawObjectsSidecarYaml());
    writeTextFile(tempRoot / "maps/testmap.material_aliases.yml", minimalMaterialAliasesSidecarYaml());
    writeTextFile(tempRoot / "maps/testmap.events.yml", minimalEventsSidecarYaml());
    metadata->sidecars.sourceAssetAliases = "../import/overrides/testmap.source_asset_aliases.yml";
    writeTextFile(
        tempRoot / "import/overrides/testmap.source_asset_aliases.yml",
        "kind: mm9_source_asset_aliases\nformat_version: 1\naliases: []\n");
    writeTextFile(tempRoot / "events/testmap.lua", "-- generated test lua\n");
    writeTextFile(tempRoot / "events/testmap.script_ir.yml", "kind: mm9_script_ir\n");
    writeTextFile(tempRoot / "maps/testmap.scene.yml", "kind: outdoor_scene\n");
    writeTextFile(tempRoot / "maps/testmap.mm9.yml", "kind: mm9_source_metadata\n");
    writeTextFile(tempRoot / "maps/testmap.model_assets.yml", "kind: mm9_model_assets\n");
    writeTextFile(tempRoot / "maps/testmap.blv", "blv");

    OpenYAMM::Editor::EditorMm9MaterialTextureStatus cacheStatus = {};
    cacheStatus.emittedBitmap = "testmap.bitmaps/TEST.bmp";
    writeTextFile(tempRoot / "maps/testmap.bitmaps/TEST.bmp", "bmp");

    const std::vector<OpenYAMM::Editor::EditorMm9DocumentPathStatus> statuses =
        OpenYAMM::Editor::inspectMm9DatLevelDocumentPaths(levelPath, *metadata, {cacheStatus});

    size_t sourceReadOnlyCount = 0;
    size_t generatedCount = 0;
    size_t authoredOverrideCount = 0;
    size_t compatibilityCount = 0;
    bool foundSourceDat = false;
    bool foundLevelEntrypoint = false;
    bool foundSourceAssetAliases = false;
    bool foundMaterialCache = false;
    bool compatibilityRolesAreDerived = true;
    bool foundBlvCompat = false;

    for (const OpenYAMM::Editor::EditorMm9DocumentPathStatus &status : statuses)
    {
        if (status.sourceReadOnly)
        {
            ++sourceReadOnlyCount;
        }

        if (status.generated)
        {
            ++generatedCount;
        }

        if (status.role == "authored_override")
        {
            ++authoredOverrideCount;
        }

        if (status.compatibilityDerived)
        {
            ++compatibilityCount;
            compatibilityRolesAreDerived =
                compatibilityRolesAreDerived && status.generated && status.role == "derived_compatibility_artifact";
        }

        foundSourceDat =
            foundSourceDat || (status.label == "source_dat" && status.sourceReadOnly && status.exists);
        foundLevelEntrypoint =
            foundLevelEntrypoint || (status.label == "level" && status.authored && status.generated);
        foundSourceAssetAliases =
            foundSourceAssetAliases || (status.label == "source_asset_aliases" && status.authored
                && !status.generated && status.role == "authored_override" && status.exists);
        foundMaterialCache =
            foundMaterialCache || (status.label == "material_cache" && status.role == "generated_cache"
                && !OpenYAMM::Editor::isMm9DocumentPathRequired(status));
        foundBlvCompat =
            foundBlvCompat || (status.label == "blv_compat" && status.generated && status.compatibilityDerived
                && status.role == "derived_compatibility_artifact" && status.exists);
    }

    CHECK(sourceReadOnlyCount == 2);
    CHECK(generatedCount >= 10);
    CHECK(authoredOverrideCount == 1);
    CHECK(compatibilityCount == 4);
    CHECK(foundSourceDat);
    CHECK(foundLevelEntrypoint);
    CHECK(foundSourceAssetAliases);
    CHECK(foundMaterialCache);
    CHECK(compatibilityRolesAreDerived);
    CHECK(foundBlvCompat);
    CHECK(OpenYAMM::Editor::validateMm9DatLevelDocumentPathRoles(statuses).empty());

    metadata->source.dat = "TESTMAP.dat";
    const std::vector<OpenYAMM::Editor::EditorMm9DocumentPathStatus> badSourceStatuses =
        OpenYAMM::Editor::inspectMm9DatLevelDocumentPaths(levelPath, *metadata);
    const std::vector<std::string> badSourceIssues =
        OpenYAMM::Editor::validateMm9DatLevelDocumentPathRoles(badSourceStatuses);

    bool foundBadSourcePath = false;

    for (const std::string &issue : badSourceIssues)
    {
        foundBadSourcePath =
            foundBadSourcePath || issue.find("read-only source path is outside source/*") != std::string::npos;
    }

    CHECK(foundBadSourcePath);

    metadata->source.dat = "../source/worlds/TESTMAP.dat";
    metadata->sidecars.datWorld = "../source/generated.dat_world.yml";
    const std::vector<OpenYAMM::Editor::EditorMm9DocumentPathStatus> badGeneratedStatuses =
        OpenYAMM::Editor::inspectMm9DatLevelDocumentPaths(levelPath, *metadata);
    const std::vector<std::string> badGeneratedIssues =
        OpenYAMM::Editor::validateMm9DatLevelDocumentPathRoles(badGeneratedStatuses);

    bool foundBadGeneratedPath = false;

    for (const std::string &issue : badGeneratedIssues)
    {
        foundBadGeneratedPath =
            foundBadGeneratedPath || issue.find("writable/generated path must not be under source/*")
                != std::string::npos;
    }

    CHECK(foundBadGeneratedPath);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 DAT level sidecar bundle loader reads all declared native sidecars")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(
            mm9LevelYamlWithContentHash("947d5a35ff2fe522fda5b431af955e3b27955ebc18c9e3684b07b51ae112461f"),
            errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_dat_level_sidecars_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path mapsRoot = tempRoot / "maps";
    const std::filesystem::path sourceWorldRoot = tempRoot / "source/worlds";
    const std::filesystem::path eventsRoot = tempRoot / "events";
    const std::filesystem::path levelPath = mapsRoot / "testmap.level.yml";

    writeTextFile(sourceWorldRoot / "TESTMAP.dat", "dat");
    writeTextFile(mapsRoot / "testmap.dat_world.yml", minimalDatWorldSidecarYaml());
    writeTextFile(mapsRoot / "testmap.raw_objects.yml", minimalRawObjectsSidecarYaml());
    writeTextFile(mapsRoot / "testmap.material_aliases.yml", minimalMaterialAliasesSidecarYaml());
    writeTextFile(mapsRoot / "testmap.events.yml", minimalEventsSidecarYaml());
    writeTextFile(eventsRoot / "testmap.lua", "-- generated test lua\n");

    OpenYAMM::Editor::EditorMm9LoadedSidecars sidecars = {};
    CHECK(OpenYAMM::Editor::loadMm9DatLevelSidecars(levelPath, *metadata, sidecars, errorMessage));
    CHECK(sidecars.datWorld.worldModels.size() == 1);
    CHECK(sidecars.materialAliases.textures.size() == 1);
    CHECK(sidecars.rawObjects.objects.size() == 1);
    CHECK(sidecars.events.objects.size() == 1);
    CHECK(sidecars.events.mechanisms.size() == 1);
    CHECK(sidecars.events.mechanisms[0].mechanismId == "mm9:testmap:object:0:mechanism");
    CHECK(sidecars.events.mechanisms[0].linear.hasMoveDir);
    CHECK(sidecars.events.mechanisms[0].linear.moveDirLt.size() == 3);
    CHECK(sidecars.events.bindings.size() == 1);
    CHECK(sidecars.events.generatedLua == "../events/testmap.lua");

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 DAT level metadata rejects legacy scene documents")
{
    const std::string sceneYaml = R"(
kind: outdoor_scene
source:
  geometry_file: out01.odm
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(sceneYaml, errorMessage);

    CHECK(!metadata.has_value());
    CHECK(!OpenYAMM::Editor::isMm9DatLevelText(sceneYaml));
    CHECK(errorMessage.find("unsupported level kind") != std::string::npos);
}

TEST_CASE("MM9 DAT level file validation reports missing required native assets")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(minimalMm9LevelYaml(), errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());

    const std::filesystem::path levelPath = sourceRoot() / "assets_dev/worlds/mm9/maps/testmap.level.yml";
    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9DatLevelMetadataFiles(levelPath, *metadata);

    CHECK(issues.size() == 6);
    CHECK(issues[0].find("source DAT is missing") != std::string::npos);
    CHECK(issues[1].find("DAT world sidecar is missing") != std::string::npos);
    CHECK(issues[2].find("raw objects sidecar is missing") != std::string::npos);
    CHECK(issues[3].find("material aliases sidecar is missing") != std::string::npos);
    CHECK(issues[4].find("events sidecar is missing") != std::string::npos);
    CHECK(issues[5].find("level Lua script is missing") != std::string::npos);
}

TEST_CASE("MM9 DAT level file validation rejects wrong sidecar kind")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(
            mm9LevelYamlWithContentHash("947d5a35ff2fe522fda5b431af955e3b27955ebc18c9e3684b07b51ae112461f"),
            errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_dat_level_metadata_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path mapsRoot = tempRoot / "maps";
    const std::filesystem::path sourceWorldRoot = tempRoot / "source/worlds";
    const std::filesystem::path eventsRoot = tempRoot / "events";
    const std::filesystem::path levelPath = mapsRoot / "testmap.level.yml";

    writeTextFile(tempRoot / "source/manifest.yml", minimalSourceAssetManifestYaml());
    writeTextFile(sourceWorldRoot / "TESTMAP.dat", "dat");
    writeTextFile(mapsRoot / "testmap.dat_world.yml", "kind: outdoor_scene\n");
    writeTextFile(mapsRoot / "testmap.raw_objects.yml", "kind: mm9_raw_world_objects\n");
    writeTextFile(mapsRoot / "testmap.material_aliases.yml", "kind: mm9_material_aliases\n");
    writeTextFile(mapsRoot / "testmap.events.yml", "kind: mm9_events\n");
    writeTextFile(eventsRoot / "testmap.lua", "-- generated test lua\n");

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9DatLevelMetadataFiles(levelPath, *metadata);

    REQUIRE(issues.size() == 1);
    CHECK(issues[0].find("DAT world sidecar has kind 'outdoor_scene'") != std::string::npos);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 DAT level file validation rejects stale source DAT hash")
{
    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(minimalMm9LevelYaml(), errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());

    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_dat_level_hash_test";
    std::filesystem::remove_all(tempRoot);

    const std::filesystem::path mapsRoot = tempRoot / "maps";
    const std::filesystem::path sourceWorldRoot = tempRoot / "source/worlds";
    const std::filesystem::path eventsRoot = tempRoot / "events";
    const std::filesystem::path levelPath = mapsRoot / "testmap.level.yml";

    writeTextFile(tempRoot / "source/manifest.yml", minimalSourceAssetManifestYaml());
    writeTextFile(sourceWorldRoot / "TESTMAP.dat", "dat");
    writeTextFile(mapsRoot / "testmap.dat_world.yml", "kind: mm9_dat_world\n");
    writeTextFile(mapsRoot / "testmap.raw_objects.yml", "kind: mm9_raw_world_objects\n");
    writeTextFile(mapsRoot / "testmap.material_aliases.yml", "kind: mm9_material_aliases\n");
    writeTextFile(mapsRoot / "testmap.events.yml", "kind: mm9_events\n");
    writeTextFile(eventsRoot / "testmap.lua", "-- generated test lua\n");

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9DatLevelMetadataFiles(levelPath, *metadata);

    REQUIRE(issues.size() == 1);
    CHECK(issues[0].find("source DAT hash mismatch") != std::string::npos);
    CHECK(issues[0].find("stored=abc123") != std::string::npos);
    CHECK(issues[0].find("actual=947d5a35ff2fe522fda5b431af955e3b27955ebc18c9e3684b07b51ae112461f")
        != std::string::npos);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 DAT level file validation accepts generated active-slice entrypoints")
{
    const std::array<std::pair<const char *, const char *>, 2> activeLevels = {{
        {"thjorgard.level.yml", "../source/worlds/THJORGARD.dat"},
        {"thjorgardcity.level.yml", "../source/worlds/THJORGARDCITY.dat"}
    }};

    for (const std::pair<const char *, const char *> &activeLevel : activeLevels)
    {
        const std::filesystem::path levelPath = sourceRoot() / "assets_dev/worlds/mm9/maps" / activeLevel.first;
        REQUIRE(std::filesystem::exists(levelPath));

        std::ifstream input(levelPath);
        REQUIRE(input.good());
        const std::string levelText((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());

        std::string errorMessage;
        const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
            OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(levelText, errorMessage);

        REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());
        CHECK(metadata->kind == "mm9_level");
        CHECK(metadata->runtime.worldBackend == "dat_world");
        CHECK(metadata->source.dat == activeLevel.second);
        CHECK(metadata->source.manifest == "../source/manifest.yml");
        REQUIRE(metadata->sidecars.sourceAssetAliases.has_value());
        CHECK(*metadata->sidecars.sourceAssetAliases == "../import/overrides/mm9_active_slice.source_asset_aliases.yml");

        const std::vector<std::string> issues =
            OpenYAMM::Editor::validateMm9DatLevelMetadataFiles(levelPath, *metadata);
        CHECK(issues.empty());
    }
}

TEST_CASE("MM9 DAT world sidecar validation accepts all generated map sidecars")
{
    const std::filesystem::path mapsRoot = sourceRoot() / "assets_dev/worlds/mm9/maps";
    REQUIRE(std::filesystem::exists(mapsRoot));

    size_t sidecarCount = 0;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(mapsRoot))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".yml")
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();

        if (fileName.find(".dat_world.yml") == std::string::npos)
        {
            continue;
        }

        ++sidecarCount;

        std::ifstream input(entry.path());
        REQUIRE(input.good());
        const std::string sidecarText((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());

        std::string errorMessage;
        const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> sidecar =
            OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(sidecarText, errorMessage);

        REQUIRE_MESSAGE(sidecar.has_value(), (entry.path().string() + ": " + errorMessage).c_str());

        const std::vector<std::string> issues =
            OpenYAMM::Editor::validateMm9DatWorldSidecarReferences(*sidecar);
        CHECK_MESSAGE(issues.empty(), entry.path().filename().string().c_str());
    }

    CHECK(sidecarCount == 45);
}

TEST_CASE("MM9 DAT world sidecars have zero invalid decoded leaf polygon references")
{
    const std::filesystem::path mapsRoot = sourceRoot() / "assets_dev/worlds/mm9/maps";
    REQUIRE(std::filesystem::exists(mapsRoot));

    size_t sidecarCount = 0;
    size_t leafReferenceTotal = 0;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(mapsRoot))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".yml")
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();

        if (fileName.find(".dat_world.yml") == std::string::npos)
        {
            continue;
        }

        ++sidecarCount;

        std::ifstream input(entry.path());
        REQUIRE(input.good());
        const std::string sidecarText((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());

        std::string errorMessage;
        const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> sidecar =
            OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(sidecarText, errorMessage);
        REQUIRE_MESSAGE(sidecar.has_value(), (entry.path().string() + ": " + errorMessage).c_str());

        leafReferenceTotal += sidecar->leafReferences.totalRefs;
        CHECK_MESSAGE(sidecar->totals.invalidLeafReferenceCount == 0, fileName.c_str());
        CHECK_MESSAGE(sidecar->leafReferences.invalidRefs == 0, fileName.c_str());
    }

    CHECK(sidecarCount == 45);
    CHECK(leafReferenceTotal > 0);
}

TEST_CASE("MM9 DAT helper world models are classified consistently")
{
    const std::filesystem::path mapsRoot = sourceRoot() / "assets_dev/worlds/mm9/maps";
    REQUIRE(std::filesystem::exists(mapsRoot));

    size_t sidecarCount = 0;
    size_t physicsBspCount = 0;
    size_t visBspCount = 0;
    size_t decodedPBlockCount = 0;
    size_t checkedBspMetadataCount = 0;
    size_t checkedReferenceValidationCount = 0;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(mapsRoot))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".yml")
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();

        if (fileName.find(".dat_world.yml") == std::string::npos)
        {
            continue;
        }

        ++sidecarCount;

        std::ifstream input(entry.path());
        REQUIRE(input.good());
        const std::string sidecarText((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());

        std::string errorMessage;
        const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> sidecar =
            OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(sidecarText, errorMessage);
        REQUIRE_MESSAGE(sidecar.has_value(), (entry.path().string() + ": " + errorMessage).c_str());

        for (const OpenYAMM::Editor::EditorMm9DatWorldModelSummary &model : sidecar->worldModels)
        {
            CHECK_MESSAGE(model.pblockTable.decodedSummary, model.sourceName.c_str());
            REQUIRE_MESSAGE(model.pblockTable.recordCount.has_value(), model.sourceName.c_str());
            CHECK_MESSAGE(
                *model.pblockTable.recordCount
                    == model.pblockTable.dimA * model.pblockTable.dimB * model.pblockTable.dimC,
                model.sourceName.c_str());
            CHECK_MESSAGE(model.bspCounts.textureCount == model.textures.size(), model.sourceName.c_str());
            CHECK_MESSAGE(model.referenceValidation.invalidSurfaceTextureRefs == 0, model.sourceName.c_str());
            CHECK_MESSAGE(model.referenceValidation.invalidPolySurfaceRefs == 0, model.sourceName.c_str());
            CHECK_MESSAGE(model.referenceValidation.invalidPolyPlaneRefs == 0, model.sourceName.c_str());
            CHECK_MESSAGE(model.referenceValidation.invalidPolyVertexRefs == 0, model.sourceName.c_str());
            CHECK_MESSAGE(model.referenceValidation.invalidNodePolyRefs == 0, model.sourceName.c_str());
            CHECK_MESSAGE(model.referenceValidation.invalidRootNodeRefs == 0, model.sourceName.c_str());
            ++decodedPBlockCount;
            ++checkedBspMetadataCount;
            ++checkedReferenceValidationCount;

            const std::string lowerName = lowerAscii(model.sourceName);
            const bool namedPhysicsBsp = lowerName == "physicsbsp";
            const bool namedVisBsp = lowerName == "visbsp";

            if (namedPhysicsBsp || model.roles.physicsBsp)
            {
                ++physicsBspCount;
                CHECK_MESSAGE(namedPhysicsBsp, model.sourceName.c_str());
                CHECK_MESSAGE(model.kind == "physics_bsp", model.sourceName.c_str());
                CHECK_MESSAGE(model.roles.physicsBsp, model.sourceName.c_str());
                CHECK_MESSAGE(!model.roles.visBsp, model.sourceName.c_str());
            }

            if (namedVisBsp || model.roles.visBsp)
            {
                ++visBspCount;
                CHECK_MESSAGE(namedVisBsp, model.sourceName.c_str());
                CHECK_MESSAGE(model.kind == "vis_bsp", model.sourceName.c_str());
                CHECK_MESSAGE(model.roles.visBsp, model.sourceName.c_str());
                CHECK_MESSAGE(!model.roles.physicsBsp, model.sourceName.c_str());
            }
        }
    }

    CHECK(sidecarCount == 45);
    CHECK(physicsBspCount > 0);
    CHECK(visBspCount > 0);
    CHECK(decodedPBlockCount > 10000);
    CHECK(checkedBspMetadataCount == decodedPBlockCount);
    CHECK(checkedReferenceValidationCount == decodedPBlockCount);
}

TEST_CASE("MM9 material texture validation accepts all generated map aliases")
{
    const std::filesystem::path mapsRoot = sourceRoot() / "assets_dev/worlds/mm9/maps";
    REQUIRE(std::filesystem::exists(mapsRoot));

    size_t materialSidecarCount = 0;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(mapsRoot))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();

        if (fileName.find(".material_aliases.yml") == std::string::npos)
        {
            continue;
        }

        const std::string mapId = fileName.substr(0, fileName.find(".material_aliases.yml"));
        const std::filesystem::path datWorldPath = mapsRoot / (mapId + ".dat_world.yml");
        REQUIRE(std::filesystem::exists(datWorldPath));
        ++materialSidecarCount;

        std::ifstream datWorldInput(datWorldPath);
        REQUIRE(datWorldInput.good());
        const std::string datWorldText(
            (std::istreambuf_iterator<char>(datWorldInput)),
            std::istreambuf_iterator<char>());

        std::ifstream materialInput(entry.path());
        REQUIRE(materialInput.good());
        const std::string materialText(
            (std::istreambuf_iterator<char>(materialInput)),
            std::istreambuf_iterator<char>());

        std::string errorMessage;
        const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
            OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(datWorldText, errorMessage);
        REQUIRE_MESSAGE(datWorld.has_value(), (datWorldPath.string() + ": " + errorMessage).c_str());

        const std::optional<OpenYAMM::Editor::EditorMm9MaterialAliasesSidecar> materials =
            OpenYAMM::Editor::loadMm9MaterialAliasesSidecarFromText(materialText, errorMessage);
        REQUIRE_MESSAGE(materials.has_value(), (entry.path().string() + ": " + errorMessage).c_str());

        const std::vector<OpenYAMM::Editor::EditorMm9MaterialTextureStatus> statuses =
            OpenYAMM::Editor::inspectMm9MaterialTextureReferences(
                mapsRoot / (mapId + ".level.yml"),
                *datWorld,
                *materials);
        const std::vector<std::string> issues =
            OpenYAMM::Editor::validateMm9MaterialTextureReferences(statuses);
        std::string issueSummary = entry.path().filename().string();

        for (const std::string &issue : issues)
        {
            issueSummary += "\n  " + issue;
        }

        INFO(issueSummary);
        CHECK(issues.empty());
    }

    CHECK(materialSidecarCount == 45);
}

TEST_CASE("MM9 raw objects sidecar validation accepts all generated map sidecars")
{
    const std::filesystem::path mapsRoot = sourceRoot() / "assets_dev/worlds/mm9/maps";
    REQUIRE(std::filesystem::exists(mapsRoot));

    size_t rawSidecarCount = 0;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(mapsRoot))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();

        if (fileName.find(".raw_objects.yml") == std::string::npos)
        {
            continue;
        }

        ++rawSidecarCount;

        std::ifstream input(entry.path());
        REQUIRE(input.good());
        const std::string rawObjectsText(
            (std::istreambuf_iterator<char>(input)),
            std::istreambuf_iterator<char>());

        std::string errorMessage;
        const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
            OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
        REQUIRE_MESSAGE(rawObjects.has_value(), (entry.path().string() + ": " + errorMessage).c_str());

        const std::vector<std::string> issues =
            OpenYAMM::Editor::validateMm9RawObjectsSidecarReferences(*rawObjects);
        std::string issueSummary = entry.path().filename().string();

        for (const std::string &issue : issues)
        {
            issueSummary += "\n  " + issue;
        }

        CHECK_MESSAGE(issues.empty(), issueSummary);
    }

    CHECK(rawSidecarCount == 45);
}

TEST_CASE("MM9 raw object asset inspection resolves source-family references")
{
    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_raw_object_asset_refs_test";
    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";

    writeTextFile(tempRoot / "source/models/PEASANTMALE.abc", "model");
    writeTextFile(tempRoot / "source/models/PROPS/MAYPOLE.ABC", "model");
    writeTextFile(tempRoot / "source/skins/PROPS/TREEBARK3.dtx", "skin");
    writeTextFile(tempRoot / "source/skins/PROPS/TREEBRANCH5.dtx", "skin");
    writeTextFile(tempRoot / "source/skins/PROPS/MAYPOLE.dtx", "skin");
    writeTextFile(tempRoot / "source/scripts/SHOPKEEPER.scr", "script");
    writeTextFile(tempRoot / "source/voices/NPC/NPC_017.wav", "voice");
    writeTextFile(tempRoot / "source/voices/NPC/NPC_018.wav", "voice");
    writeTextFile(tempRoot / "source/voices/NPC/NPC_125.wav", "voice");
    writeTextFile(tempRoot / "source/sprites/WATER/WATER115FLOWING.spr", "sprite");
    writeTextFile(tempRoot / "source/sounds/AMBIENT/BIRDS/OWL01.wav", "sound");
    writeTextFile(tempRoot / "source/sounds/AMBIENT/BIRDS/BIRDS01.wav", "sound");

    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 0
    name: TestActor
    property_count: 10
    data_length: 4
    trailing_hex: ""
    properties:
      - name: Name
        code: 0
        flags: 0
        declared_data_length: 10
        consumed_data_length: 10
        decoded: true
        raw_hex: "0800546573744e616d65"
        value_json: "\"TestName\""
      - name: Filename
        code: 0
        flags: 0
        declared_data_length: 24
        consumed_data_length: 24
        decoded: true
        raw_hex: ""
        value_json: "\"models\\\\PeasantMale.abc\""
      - name: Skin
        code: 0
        flags: 0
        declared_data_length: 72
        consumed_data_length: 72
        decoded: true
        raw_hex: ""
        value_json: "\"skins/props/TREEBARK3.dtx;Skins\\\\Props\\\\TreeBranch5.dtx\""
      - name: ScriptName
        code: 0
        flags: 0
        declared_data_length: 16
        consumed_data_length: 16
        decoded: true
        raw_hex: ""
        value_json: "\"shopkeeper.scr\""
      - name: ScriptParams
        code: 0
        flags: 0
        declared_data_length: 25
        consumed_data_length: 25
        decoded: true
        raw_hex: ""
        value_json: "\"voices\\\\npc\\\\NPC_018.wav \""
      - name: GreetingSound
        code: 0
        flags: 0
        declared_data_length: 25
        consumed_data_length: 25
        decoded: true
        raw_hex: ""
        value_json: "\"\\\\voices\\\\npc\\\\NPC_017.wav\""
      - name: SpriteSurfaceName
        code: 0
        flags: 0
        declared_data_length: 34
        consumed_data_length: 34
        decoded: true
        raw_hex: ""
        value_json: "\"Sprites\\\\water\\\\Water115flowing.spr\""
      - name: ScriptParams
        code: 0
        flags: 0
        declared_data_length: 80
        consumed_data_length: 80
        decoded: true
        raw_hex: ""
        value_json: "\"268 models\\\\Props\\\\Maypole.ABC skins\\\\Props\\\\Maypole.dtx \\\\voices\\\\npc\\\\NPC_125.wav 455\""
      - name: Filename
        code: 0
        flags: 0
        declared_data_length: 25
        consumed_data_length: 25
        decoded: true
        raw_hex: ""
        value_json: "\"Sounds\\\\Ambient\\\\owl01.wav\""
      - name: Filename
        code: 0
        flags: 0
        declared_data_length: 25
        consumed_data_length: 25
        decoded: true
        raw_hex: ""
        value_json: "\"Sounds\\\\Ambient\\\\bird01.wav\""
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus> statuses =
        OpenYAMM::Editor::inspectMm9RawObjectAssetReferences(levelPath, *rawObjects);

    REQUIRE(statuses.size() == 12);

    for (const OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus &status : statuses)
    {
        CHECK(status.sourceObjectIndex == 0);
        CHECK(status.objectName == "TestName");
        CHECK(status.resolved);
        CHECK(!status.ambiguous);
        CHECK(!status.resolvedSourcePath.empty());
    }

    CHECK(OpenYAMM::Editor::validateMm9RawObjectAssetReferences(statuses).empty());
}

TEST_CASE("MM9 raw object asset inspection reports ambiguous basename fallback")
{
    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_raw_object_asset_ambiguous_basename_test";
    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";

    writeTextFile(tempRoot / "source/sounds/AMBIENT/BIRDS/BIRD01.wav", "sound");
    writeTextFile(tempRoot / "source/sounds/AMBIENT/FOREST/BIRD01.wav", "sound");

    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 0
    name: TestSound
    property_count: 1
    data_length: 4
    trailing_hex: ""
    properties:
      - name: Filename
        code: 0
        flags: 0
        declared_data_length: 25
        consumed_data_length: 25
        decoded: true
        raw_hex: ""
        value_json: "\"Sounds\\\\Ambient\\\\bird01.wav\""
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus> statuses =
        OpenYAMM::Editor::inspectMm9RawObjectAssetReferences(levelPath, *rawObjects);
    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9RawObjectAssetReferences(statuses);

    REQUIRE(statuses.size() == 1);
    CHECK(!statuses[0].resolved);
    CHECK(statuses[0].ambiguous);
    CHECK(statuses[0].sourceCandidates.size() == 2);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].find("ambiguous") != std::string::npos);
}

TEST_CASE("MM9 raw object asset inspection applies scoped source asset aliases")
{
    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_raw_object_asset_alias_test";
    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";

    writeTextFile(tempRoot / "source/models/PROPS/BARREL.abc", "model");
    writeTextFile(tempRoot / "import/overrides/testmap.source_asset_aliases.yml", R"(
format_version: 1
kind: mm9_source_asset_aliases
map_id: testmap
aliases:
  - source_family: models
    requested: models\Props\Barrel02.ABC
    resolved: models\Props\Barrel.ABC
    scope:
      maps: [testmap]
      object_indexes: [7]
      properties: [Filename]
    reason: "test scoped missing source alias"
)");

    const std::string levelText = R"(
format_version: 1
kind: mm9_level
map_id: testmap
display_name: Test Map
source:
  dat: ../source/worlds/TESTMAP.dat
  manifest: ../source/manifest.yml
  original_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
  source_game: mm9
  dat_version: 66
  content_hash: abc123
runtime:
  world_backend: dat_world
  classification: dat_bsp_like
  classification_confidence: high
  visibility: dat_portal_bsp
  collision: dat_physics_bsp
  render: dat_render_world
  sky: false
sidecars:
  dat_world: testmap.dat_world.yml
  raw_objects: testmap.raw_objects.yml
  materials: testmap.material_aliases.yml
  events: testmap.events.yml
  source_asset_aliases: ../import/overrides/testmap.source_asset_aliases.yml
scripts:
  level: ../events/testmap.lua
  script_ir: ../events/testmap.script_ir.yml
compatibility:
  legacy_target_format: blv
  generated_odm_blv_are_derived: true
)";
    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 7
    name: Prop
    property_count: 2
    data_length: 4
    trailing_hex: ""
    properties:
      - name: Name
        code: 0
        flags: 0
        declared_data_length: 8
        consumed_data_length: 8
        decoded: true
        raw_hex: ""
        value_json: "\"Prop74\""
      - name: Filename
        code: 0
        flags: 0
        declared_data_length: 27
        consumed_data_length: 27
        decoded: true
        raw_hex: ""
        value_json: "\"models\\\\Props\\\\Barrel02.ABC\""
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(levelText, errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus> statuses =
        OpenYAMM::Editor::inspectMm9RawObjectAssetReferences(levelPath, *rawObjects, &*metadata);
    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9RawObjectAssetReferences(statuses);

    REQUIRE(statuses.size() == 1);
    CHECK(statuses[0].resolved);
    CHECK(!statuses[0].ambiguous);
    CHECK(statuses[0].aliasApplied);
    CHECK(statuses[0].aliasTargetKey == "props/barrel.abc");
    CHECK(statuses[0].resolutionSource == "source_asset_alias");
    CHECK(statuses[0].resolvedSourcePath.find("BARREL.abc") != std::string::npos);
    CHECK(issues.empty());
}

TEST_CASE("MM9 raw object asset validation reports unresolved required source references")
{
    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_raw_object_asset_missing_test";
    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";

    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 0
    name: TestActor
    property_count: 1
    data_length: 4
    trailing_hex: ""
    properties:
      - name: Filename
        code: 0
        flags: 0
        declared_data_length: 18
        consumed_data_length: 18
        decoded: true
        raw_hex: ""
        value_json: "\"models\\\\Missing.abc\""
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus> statuses =
        OpenYAMM::Editor::inspectMm9RawObjectAssetReferences(levelPath, *rawObjects);
    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9RawObjectAssetReferences(statuses);

    REQUIRE(statuses.size() == 1);
    CHECK(!statuses[0].resolved);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].find("unresolved") != std::string::npos);
    CHECK(issues[0].find("models\\Missing.abc") != std::string::npos);
}

TEST_CASE("MM9 raw object asset validation reports missing script and sound source references")
{
    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_raw_object_asset_missing_script_sound_test";
    std::filesystem::remove_all(tempRoot);
    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";

    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 12
    name: TestScriptedObject
    property_count: 2
    data_length: 4
    trailing_hex: ""
    properties:
      - name: ScriptName
        code: 0
        flags: 0
        declared_data_length: 24
        consumed_data_length: 24
        decoded: true
        raw_hex: ""
        value_json: "\"Scripts\\\\Missing.scr\""
      - name: ActivationSound
        code: 0
        flags: 0
        declared_data_length: 24
        consumed_data_length: 24
        decoded: true
        raw_hex: ""
        value_json: "\"Sounds\\\\Missing.wav\""
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus> statuses =
        OpenYAMM::Editor::inspectMm9RawObjectAssetReferences(levelPath, *rawObjects);
    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9RawObjectAssetReferences(statuses);

    REQUIRE(statuses.size() == 2);
    REQUIRE(issues.size() == 2);

    bool foundMissingScript = false;
    bool foundMissingSound = false;
    bool foundMissingScriptIssue = false;
    bool foundMissingSoundIssue = false;

    for (const OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus &status : statuses)
    {
        foundMissingScript =
            foundMissingScript || (status.sourceFamily == "scripts" && !status.resolved && status.required);
        foundMissingSound =
            foundMissingSound || (status.sourceFamily == "sounds" && !status.resolved && status.required);
    }

    for (const std::string &issue : issues)
    {
        foundMissingScriptIssue =
            foundMissingScriptIssue || issue.find("Scripts\\Missing.scr") != std::string::npos;
        foundMissingSoundIssue =
            foundMissingSoundIssue || issue.find("Sounds\\Missing.wav") != std::string::npos;
    }

    CHECK(foundMissingScript);
    CHECK(foundMissingSound);
    CHECK(foundMissingScriptIssue);
    CHECK(foundMissingSoundIssue);

    std::filesystem::remove_all(tempRoot);
}

TEST_CASE("MM9 raw object asset validation keeps WorldProperties sky refs optional")
{
    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_raw_object_optional_sky_asset_test";
    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";

    const std::string rawObjectsText = R"(
format_version: 1
kind: mm9_raw_world_objects
source_dat: mm9/extracted/WORLDS/WORLDS/TESTMAP.dat
object_count: 1
unknown_property_count: 0
unknown_property_codes: []
objects:
  - object_index: 0
    name: WorldProperties
    property_count: 2
    data_length: 4
    trailing_hex: ""
    properties:
      - name: Name
        code: 0
        flags: 0
        declared_data_length: 18
        consumed_data_length: 18
        decoded: true
        raw_hex: ""
        value_json: "\"WorldProperties0\""
      - name: PanSkyTexture
        code: 0
        flags: 0
        declared_data_length: 22
        consumed_data_length: 22
        decoded: true
        raw_hex: ""
        value_json: "\"Textures\\\\SkyPan.dtx\""
)";

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
        OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
    REQUIRE_MESSAGE(rawObjects.has_value(), errorMessage.c_str());

    const std::vector<OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus> statuses =
        OpenYAMM::Editor::inspectMm9RawObjectAssetReferences(levelPath, *rawObjects);
    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9RawObjectAssetReferences(statuses);

    REQUIRE(statuses.size() == 1);
    CHECK(!statuses[0].required);
    CHECK(statuses[0].resolved);
    CHECK(statuses[0].builtinReference);
    CHECK(statuses[0].resolutionSource == "lithtech_world_properties_sky_builtin");
    CHECK(issues.empty());
}

TEST_CASE("MM9 asset dependency summary groups source and generated families")
{
    const std::filesystem::path tempRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_asset_dependency_summary_test";
    const std::filesystem::path levelPath = tempRoot / "maps/testmap.level.yml";

    writeTextFile(tempRoot / "source/worlds/TESTMAP.dat", "dat");
    writeTextFile(tempRoot / "maps/testmap.dat_world.yml", "sidecar");
    writeTextFile(tempRoot / "maps/testmap.raw_objects.yml", "sidecar");
    writeTextFile(tempRoot / "maps/testmap.material_aliases.yml", "sidecar");
    writeTextFile(tempRoot / "maps/testmap.events.yml", "sidecar");
    writeTextFile(tempRoot / "events/testmap.lua", "-- lua\n");
    writeTextFile(tempRoot / "events/testmap.script_ir.yml", "kind: script_ir\n");
    writeTextFile(tempRoot / "source/data/ACTOR.txt", "actor table\n");
    writeTextFile(tempRoot / "source/rude/NPC001.txt", "rude table\n");

    OpenYAMM::Editor::EditorMm9MaterialTextureStatus materialStatus = {};
    materialStatus.sourceTexture = "TEXTURES\\TEST\\TEST.dtx";
    materialStatus.emittedBitmap = "testmap.bitmaps/TEST.bmp";
    materialStatus.datReferenceCount = 1;
    materialStatus.sourceDtxResolved = true;
    materialStatus.sourcePathExists = true;
    materialStatus.dtxHeaderLoaded = true;
    materialStatus.dtxHeaderMatchesSidecar = true;
    materialStatus.cachePathExists = true;

    std::vector<OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus> rawStatuses;
    OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus modelStatus = {};
    modelStatus.sourceFamily = "models";
    modelStatus.resolved = true;
    modelStatus.required = true;
    rawStatuses.push_back(modelStatus);

    OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus missingSoundStatus = {};
    missingSoundStatus.sourceFamily = "sounds";
    missingSoundStatus.resolved = false;
    missingSoundStatus.required = true;
    rawStatuses.push_back(missingSoundStatus);

    OpenYAMM::Editor::EditorMm9RawObjectAssetReferenceStatus optionalMissingTextureStatus = {};
    optionalMissingTextureStatus.sourceFamily = "textures";
    optionalMissingTextureStatus.resolved = false;
    optionalMissingTextureStatus.required = false;
    rawStatuses.push_back(optionalMissingTextureStatus);

    std::vector<OpenYAMM::Editor::EditorMm9SourceAssetFamilyStatus> sourceFamilyStatuses;
    OpenYAMM::Editor::EditorMm9SourceAssetFamilyStatus dataFamilyStatus = {};
    dataFamilyStatus.id = "data";
    dataFamilyStatus.declared = true;
    dataFamilyStatus.actualFileCount = 2;
    sourceFamilyStatuses.push_back(dataFamilyStatus);

    OpenYAMM::Editor::EditorMm9SourceAssetFamilyStatus rudeFamilyStatus = {};
    rudeFamilyStatus.id = "rude";
    rudeFamilyStatus.declared = true;
    rudeFamilyStatus.actualFileCount = 1;
    sourceFamilyStatuses.push_back(rudeFamilyStatus);

    OpenYAMM::Editor::EditorMm9SourceAssetFamilyStatus soundsFamilyStatus = {};
    soundsFamilyStatus.id = "sounds";
    soundsFamilyStatus.declared = true;
    soundsFamilyStatus.actualFileCount = 5;
    sourceFamilyStatuses.push_back(soundsFamilyStatus);

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
        OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(minimalMm9LevelYaml(), errorMessage);
    REQUIRE_MESSAGE(metadata.has_value(), errorMessage.c_str());

    const OpenYAMM::Editor::EditorMm9AssetDependencySummary summary =
        OpenYAMM::Editor::summarizeMm9AssetDependencies(
            levelPath,
            *metadata,
            {materialStatus},
            rawStatuses,
            sourceFamilyStatuses);

    CHECK(summary.total == 14);
    CHECK(summary.resolved == 12);
    CHECK(summary.unresolved == 2);
    CHECK(summary.ambiguous == 0);
    CHECK(summary.stale == 0);
    CHECK(summary.requiredTotal == 12);
    CHECK(summary.requiredResolved == 11);
    CHECK(summary.requiredUnresolved == 1);
    CHECK(summary.requiredAmbiguous == 0);
    CHECK(summary.optionalTotal == 2);
    CHECK(summary.optionalResolved == 1);
    CHECK(summary.optionalUnresolved == 1);
    CHECK(summary.optionalAmbiguous == 0);
    CHECK(summary.sourceOnly == 8);
    CHECK(summary.unusedSource == 5);

    const auto findFamily =
        [&summary](const std::string &family)
        {
            return std::find_if(
                summary.families.begin(),
                summary.families.end(),
                [&family](const OpenYAMM::Editor::EditorMm9AssetDependencyFamilySummary &entry)
                {
                    return entry.family == family;
                });
        };

    REQUIRE(findFamily("sidecars") != summary.families.end());
    CHECK(findFamily("sidecars")->total == 4);
    CHECK(findFamily("sidecars")->resolved == 4);
    REQUIRE(findFamily("generated_events") != summary.families.end());
    CHECK(findFamily("generated_events")->total == 2);
    CHECK(findFamily("generated_events")->resolved == 2);
    REQUIRE(findFamily("data") != summary.families.end());
    CHECK(findFamily("data")->total == 1);
    CHECK(findFamily("data")->resolved == 1);
    CHECK(findFamily("data")->sourceOnly == 2);
    CHECK(findFamily("data")->unusedSource == 1);
    REQUIRE(findFamily("rude") != summary.families.end());
    CHECK(findFamily("rude")->total == 1);
    CHECK(findFamily("rude")->resolved == 1);
    CHECK(findFamily("rude")->sourceOnly == 1);
    CHECK(findFamily("rude")->unusedSource == 0);
    REQUIRE(findFamily("generated_caches") != summary.families.end());
    CHECK(findFamily("generated_caches")->total == 1);
    CHECK(findFamily("generated_caches")->resolved == 1);
    CHECK(findFamily("generated_caches")->requiredTotal == 0);
    CHECK(findFamily("generated_caches")->optionalResolved == 1);
    REQUIRE(findFamily("sounds") != summary.families.end());
    CHECK(findFamily("sounds")->unresolved == 1);
    CHECK(findFamily("sounds")->requiredUnresolved == 1);
    CHECK(findFamily("sounds")->sourceOnly == 5);
    CHECK(findFamily("sounds")->unusedSource == 4);
    REQUIRE(findFamily("textures") != summary.families.end());
    CHECK(findFamily("textures")->optionalUnresolved == 1);
}

TEST_CASE("MM9 diagnostic severity policy marks only errors as clean blockers")
{
    const std::vector<OpenYAMM::Editor::EditorMm9DiagnosticSeverityRule> &rules =
        OpenYAMM::Editor::mm9DiagnosticSeverityRules();

    REQUIRE(rules.size() == 3);

    const auto findRule =
        [&rules](const std::string &severity)
        {
            return std::find_if(
                rules.begin(),
                rules.end(),
                [&severity](const OpenYAMM::Editor::EditorMm9DiagnosticSeverityRule &rule)
                {
                    return rule.severity == severity;
                });
        };

    const auto errorRule = findRule("error");
    const auto warningRule = findRule("warning");
    const auto infoRule = findRule("info");

    REQUIRE(errorRule != rules.end());
    REQUIRE(warningRule != rules.end());
    REQUIRE(infoRule != rules.end());

    CHECK(errorRule->blocksCleanValidation);
    CHECK(!warningRule->blocksCleanValidation);
    CHECK(!infoRule->blocksCleanValidation);
    CHECK(errorRule->category.find("unresolved required asset") != std::string::npos);
    CHECK(errorRule->category.find("source mutation") != std::string::npos);
    CHECK(warningRule->category.find("placeholder preview material") != std::string::npos);
    CHECK(warningRule->category.find("unresolved optional asset") != std::string::npos);
    CHECK(infoRule->category.find("derived compatibility artifact missing") != std::string::npos);
    CHECK(infoRule->category.find("cache regenerated") != std::string::npos);
}

TEST_CASE("MM9 events validation accepts all generated map sidecars")
{
    const std::filesystem::path mapsRoot = sourceRoot() / "assets_dev/worlds/mm9/maps";
    REQUIRE(std::filesystem::exists(mapsRoot));

    size_t eventSidecarCount = 0;
    size_t mechanismCount = 0;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(mapsRoot))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();

        if (fileName.find(".events.yml") == std::string::npos)
        {
            continue;
        }

        const std::string mapId = fileName.substr(0, fileName.find(".events.yml"));
        const std::filesystem::path levelPath = mapsRoot / (mapId + ".level.yml");
        const std::filesystem::path datWorldPath = mapsRoot / (mapId + ".dat_world.yml");
        const std::filesystem::path rawObjectsPath = mapsRoot / (mapId + ".raw_objects.yml");
        REQUIRE(std::filesystem::exists(levelPath));
        REQUIRE(std::filesystem::exists(datWorldPath));
        REQUIRE(std::filesystem::exists(rawObjectsPath));
        ++eventSidecarCount;

        std::ifstream levelInput(levelPath);
        std::ifstream datWorldInput(datWorldPath);
        std::ifstream rawObjectsInput(rawObjectsPath);
        std::ifstream eventsInput(entry.path());
        REQUIRE(levelInput.good());
        REQUIRE(datWorldInput.good());
        REQUIRE(rawObjectsInput.good());
        REQUIRE(eventsInput.good());

        const std::string levelText(
            (std::istreambuf_iterator<char>(levelInput)),
            std::istreambuf_iterator<char>());
        const std::string datWorldText(
            (std::istreambuf_iterator<char>(datWorldInput)),
            std::istreambuf_iterator<char>());
        const std::string rawObjectsText(
            (std::istreambuf_iterator<char>(rawObjectsInput)),
            std::istreambuf_iterator<char>());
        const std::string eventsText(
            (std::istreambuf_iterator<char>(eventsInput)),
            std::istreambuf_iterator<char>());

        std::string errorMessage;
        const std::optional<OpenYAMM::Editor::EditorMm9DatLevelMetadata> metadata =
            OpenYAMM::Editor::loadMm9DatLevelMetadataFromText(levelText, errorMessage);
        REQUIRE_MESSAGE(metadata.has_value(), (levelPath.string() + ": " + errorMessage).c_str());

        const std::optional<OpenYAMM::Editor::EditorMm9DatWorldSidecar> datWorld =
            OpenYAMM::Editor::loadMm9DatWorldSidecarFromText(datWorldText, errorMessage);
        REQUIRE_MESSAGE(datWorld.has_value(), (datWorldPath.string() + ": " + errorMessage).c_str());

        const std::optional<OpenYAMM::Editor::EditorMm9RawObjectsSidecar> rawObjects =
            OpenYAMM::Editor::loadMm9RawObjectsSidecarFromText(rawObjectsText, errorMessage);
        REQUIRE_MESSAGE(rawObjects.has_value(), (rawObjectsPath.string() + ": " + errorMessage).c_str());

        OpenYAMM::Game::Mm9EventsYmlLoader eventsLoader = {};
        const std::optional<OpenYAMM::Game::Mm9EventsData> events =
            eventsLoader.loadFromText(eventsText, errorMessage);
        REQUIRE_MESSAGE(events.has_value(), (entry.path().string() + ": " + errorMessage).c_str());

        const std::vector<std::string> issues =
            OpenYAMM::Editor::validateMm9EventsReferences(levelPath, *metadata, *datWorld, *rawObjects, *events);

        std::string issueSummary = entry.path().filename().string();

        for (const std::string &issue : issues)
        {
            issueSummary += "\n  " + issue;
        }

        CHECK_MESSAGE(issues.empty(), issueSummary);

        for (const OpenYAMM::Game::Mm9EventMechanism &mechanism : events->mechanisms)
        {
            ++mechanismCount;
            CHECK_MESSAGE(mechanism.mechanismId.rfind("mm9:", 0) == 0, entry.path().filename().string().c_str());
            CHECK_MESSAGE(mechanism.objectId.rfind("mm9:", 0) == 0, entry.path().filename().string().c_str());
            CHECK_MESSAGE(mechanism.mechanismId.find(".odm") == std::string::npos, mechanism.mechanismId.c_str());
            CHECK_MESSAGE(mechanism.mechanismId.find(".blv") == std::string::npos, mechanism.mechanismId.c_str());

            if (mechanism.linear.hasMoveDir)
            {
                CHECK_MESSAGE(mechanism.linear.moveDirLt.size() == 3, mechanism.mechanismId.c_str());
            }
            if (mechanism.rotation.hasRotationPoint)
            {
                CHECK_MESSAGE(mechanism.rotation.rotationPointLt.size() == 3, mechanism.mechanismId.c_str());
            }
            if (mechanism.rotation.hasRotationAngles)
            {
                CHECK_MESSAGE(mechanism.rotation.rotationAnglesDeg.size() == 3, mechanism.mechanismId.c_str());
            }
        }

        for (const OpenYAMM::Game::Mm9EventBinding &binding : events->bindings)
        {
            for (const OpenYAMM::Game::Mm9EventBindingTarget &target : binding.targets)
            {
                CHECK_MESSAGE(target.targetKind != "odm_face", binding.objectId.c_str());
                CHECK_MESSAGE(target.targetKind != "blv_face", binding.objectId.c_str());
                CHECK_MESSAGE(target.targetId.find("#faces") == std::string::npos, target.targetId.c_str());
            }
        }
    }

    CHECK(eventSidecarCount == 45);
    CHECK(mechanismCount > 0);
}

TEST_CASE("MM9 source asset manifest validation accepts mirrored source tree")
{
    const std::filesystem::path manifestPath = sourceRoot() / "assets_dev/worlds/mm9/source/manifest.yml";
    REQUIRE(std::filesystem::exists(manifestPath));

    std::ifstream input(manifestPath);
    REQUIRE(input.good());
    const std::string manifestText((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());

    std::string errorMessage;
    const std::optional<OpenYAMM::Editor::EditorMm9SourceAssetManifest> manifest =
        OpenYAMM::Editor::loadMm9SourceAssetManifestFromText(manifestText, errorMessage);

    REQUIRE_MESSAGE(manifest.has_value(), errorMessage.c_str());

    const std::vector<std::string> issues =
        OpenYAMM::Editor::validateMm9SourceAssetManifestFiles(manifestPath, *manifest);
    CHECK(issues.empty());
}
