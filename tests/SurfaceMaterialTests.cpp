#include "doctest/doctest.h"

#include "game/render/SurfaceMaterialRuntime.h"
#include "game/tables/SurfaceMaterialTable.h"

#include <cmath>
#include <limits>
#include <string>

namespace
{
const char *TwoRowYaml = R"yaml(
materials:
  - id: castle_stone
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castle01]
    shading:
      roughness: 0.82
      specular: 0.04
      receives_wetness: true
      wetness_response: 0.8
      wet_roughness: 0.10
      wet_darkening: 0.06
      fresnel_strength: 0.25
      emissive_strength: 1.5
      emissive_color: [0.25, 0.5, 0.75]
  - id: castle_floor
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castle02]
)yaml";

bool loadYaml(const char *yamlText, OpenYAMM::Game::SurfaceMaterialTable &table, std::string &errorMessage)
{
    return table.loadFromYaml(std::string(yamlText), errorMessage);
}
}

TEST_CASE("surface material shading block parses authored values and applies defaults")
{
    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(TwoRowYaml, table, errorMessage));

    const OpenYAMM::Game::SurfaceMaterialDefinition *pStone = table.findMatch("castle01", 0, false);
    REQUIRE(pStone != nullptr);
    REQUIRE(pStone->shading.has_value());
    CHECK(pStone->shading->roughness == doctest::Approx(0.82f));
    CHECK(pStone->shading->specular == doctest::Approx(0.04f));
    CHECK(pStone->shading->receivesWetness);
    CHECK(pStone->shading->wetnessResponse == doctest::Approx(0.8f));
    CHECK(pStone->shading->wetRoughness == doctest::Approx(0.10f));
    CHECK(pStone->shading->wetDarkening == doctest::Approx(0.06f));
    CHECK(pStone->shading->fresnelStrength == doctest::Approx(0.25f));
    CHECK(pStone->shading->emissiveStrength == doctest::Approx(1.5f));
    CHECK(pStone->shading->emissiveColor[0] == doctest::Approx(0.25f));
    CHECK(pStone->shading->emissiveColor[1] == doctest::Approx(0.5f));
    CHECK(pStone->shading->emissiveColor[2] == doctest::Approx(0.75f));

    const OpenYAMM::Game::SurfaceMaterialDefinition *pFloor = table.findMatch("castle02", 0, false);
    REQUIRE(pFloor != nullptr);
    // A missing shading block stays absent at the authoring level; the neutral
    // defaults materialize in the resolved runtime record.
    CHECK(!pFloor->shading.has_value());
}

TEST_CASE("surface material rows without shading resolve to neutral runtime shading")
{
    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(TwoRowYaml, table, errorMessage));

    OpenYAMM::Game::SurfaceMaterialRuntimeSet runtimeSet;
    std::string setErrorMessage;
    REQUIRE(runtimeSet.buildFromTable(table, setErrorMessage));

    const uint16_t stoneId = runtimeSet.resolveMaterialId("castle01", 0, false);
    const uint16_t floorId = runtimeSet.resolveMaterialId("castle02", 0, false);
    CHECK(stoneId != OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId);
    CHECK(floorId != OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId);

    const OpenYAMM::Game::ResolvedSurfaceMaterial &floorMaterial = runtimeSet.material(floorId);
    CHECK(floorMaterial.roughness == doctest::Approx(0.90f));
    CHECK(floorMaterial.specular == doctest::Approx(0.0f));
    CHECK(floorMaterial.effectiveWetnessResponse == doctest::Approx(0.0f));
    CHECK(!floorMaterial.receivesPuddles);

    CHECK(runtimeSet.material(OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId).specular
        == doctest::Approx(0.0f));
    CHECK(runtimeSet
            .material(std::numeric_limits<uint16_t>::max())
            .emissiveStrength
        == doctest::Approx(0.0f));
}

TEST_CASE("surface material wetness response is baked to zero when receives_wetness is false")
{
    const char *yamlText = R"yaml(
materials:
  - id: sealed_wall
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [wall01]
    shading:
      wetness_response: 0.9
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(yamlText, table, errorMessage));

    OpenYAMM::Game::SurfaceMaterialRuntimeSet runtimeSet;
    std::string setErrorMessage;
    REQUIRE(runtimeSet.buildFromTable(table, setErrorMessage));

    const uint16_t materialId = runtimeSet.resolveMaterialId("wall01", 0, false);
    const OpenYAMM::Game::ResolvedSurfaceMaterial &resolvedMaterial = runtimeSet.material(materialId);
    CHECK(resolvedMaterial.effectiveWetnessResponse == doctest::Approx(0.0f));
    CHECK(resolvedMaterial.roughness == doctest::Approx(0.90f));
}

TEST_CASE("surface material resolution preserves first-match precedence and scope")
{
    const char *yamlText = R"yaml(
materials:
  - id: first_rule
    semantic: generic
    applies_to: [face]
    match:
      texture_prefixes: [castle]
    shading:
      roughness: 0.30
  - id: second_rule
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castle01]
    shading:
      roughness: 0.70
  - id: terrain_only_rule
    semantic: generic
    applies_to: [terrain]
    match:
      texture_names: [castle01]
    shading:
      roughness: 0.50
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(yamlText, table, errorMessage));

    OpenYAMM::Game::SurfaceMaterialRuntimeSet runtimeSet;
    std::string setErrorMessage;
    REQUIRE(runtimeSet.buildFromTable(table, setErrorMessage));

    const uint16_t faceMaterialId = runtimeSet.resolveMaterialId("castle01", 0, false);
    const OpenYAMM::Game::ResolvedSurfaceMaterial &faceMaterial = runtimeSet.material(faceMaterialId);
    CHECK(faceMaterial.sourceId == "first_rule");
    CHECK(faceMaterial.roughness == doctest::Approx(0.30f));

    const uint16_t terrainMaterialId = runtimeSet.resolveMaterialId("castle01", 0, true);
    const OpenYAMM::Game::ResolvedSurfaceMaterial &terrainMaterial = runtimeSet.material(terrainMaterialId);
    CHECK(terrainMaterial.sourceId == "terrain_only_rule");

    CHECK(runtimeSet.resolveMaterialId("unknown_texture", 0, false)
        == OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId);
}

TEST_CASE("surface material binding is attribute sensitive")
{
    const char *yamlText = R"yaml(
materials:
  - id: flowing_water
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [water01]
      required_face_attributes: [fluid]
    shading:
      roughness: 0.20
  - id: still_water
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [water01]
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(yamlText, table, errorMessage));

    OpenYAMM::Game::SurfaceMaterialRuntimeSet runtimeSet;
    std::string setErrorMessage;
    REQUIRE(runtimeSet.buildFromTable(table, setErrorMessage));

    const uint16_t dryId = runtimeSet.resolveMaterialId("water01", 0, false);
    const uint16_t fluidId = runtimeSet.resolveMaterialId("water01", 0x10u, false);

    CHECK(runtimeSet.material(dryId).sourceId == "still_water");
    CHECK(runtimeSet.material(fluidId).sourceId == "flowing_water");

    // The same binding key resolves consistently through the cache.
    CHECK(runtimeSet.resolveMaterialId("water01", 0x10u, false) == fluidId);
    CHECK(runtimeSet.resolveMaterialId("water01", 0, false) == dryId);
}

TEST_CASE("surface material table rejects duplicate ids")
{
    const char *yamlText = R"yaml(
materials:
  - id: same_id
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castle01]
  - id: SAME_ID
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castle02]
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(!loadYaml(yamlText, table, errorMessage));
    CHECK(errorMessage.find("same_id") != std::string::npos);
    CHECK(errorMessage.find("duplicate") != std::string::npos);
}

TEST_CASE("surface material table rejects invalid shading values with named errors")
{
    struct InvalidShadingCase
    {
        const char *name;
        const char *yamlText;
        const char *expectedFragment;
    };

    const InvalidShadingCase cases[] = {
        {"roughness below range",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      roughness: 0.01\n",
         "roughness"},
        {"roughness above range",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      roughness: 1.5\n",
         "roughness"},
        {"specular negative",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      specular: -0.1\n",
         "specular"},
        {"not a number",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      specular: not_a_number\n",
         "specular"},
        {"boolean as number",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      roughness: true\n",
         "roughness"},
        {"emissive strength above range",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      emissive_strength: 4.5\n",
         "emissive_strength"},
        {"emissive color wrong arity",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      emissive_color: [0.5, 0.5]\n",
         "emissive_color"},
        {"unknown property",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      facade_mask_texture: masks/stone.png\n",
         "facade_mask_texture"},
        {"puddles without wetness",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [terrain]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      receives_puddles: true\n",
         "receives_puddles"},
        {"puddles on face-only material",
         "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
         "texture_names: [t]\n    shading:\n      receives_wetness: true\n      receives_puddles: true\n",
         "receives_puddles"},
    };

    for (const InvalidShadingCase &invalidCase : cases)
    {
        CAPTURE(invalidCase.name);
        OpenYAMM::Game::SurfaceMaterialTable table;
        std::string errorMessage;
        CHECK(!loadYaml(invalidCase.yamlText, table, errorMessage));
        CHECK(errorMessage.find("m") != std::string::npos);
        CHECK(errorMessage.find(invalidCase.expectedFragment) != std::string::npos);
    }
}

TEST_CASE("surface material table rejects non-finite shading values")
{
    const char *nanYaml =
        "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
        "texture_names: [t]\n    shading:\n      roughness: .nan\n";
    const char *infYaml =
        "materials:\n  - id: m\n    semantic: generic\n    applies_to: [face]\n    match:\n      "
        "texture_names: [t]\n    shading:\n      specular: -.inf\n";

    OpenYAMM::Game::SurfaceMaterialTable nanTable;
    std::string nanError;
    CHECK(!loadYaml(nanYaml, nanTable, nanError));
    CHECK(nanError.find("roughness") != std::string::npos);
    CHECK(nanError.find("finite") != std::string::npos);

    OpenYAMM::Game::SurfaceMaterialTable infTable;
    std::string infError;
    CHECK(!loadYaml(infYaml, infTable, infError));
    CHECK(infError.find("specular") != std::string::npos);
    CHECK(infError.find("finite") != std::string::npos);
}

TEST_CASE("surface material runtime sets are map-owned and independent")
{
    const char *firstYaml = R"yaml(
materials:
  - id: stone
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [shared01]
    shading:
      roughness: 0.30
)yaml";
    const char *secondYaml = R"yaml(
materials:
  - id: wood
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [shared01]
    shading:
      roughness: 0.85
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable firstTable;
    OpenYAMM::Game::SurfaceMaterialTable secondTable;
    std::string errorMessage;
    REQUIRE(loadYaml(firstYaml, firstTable, errorMessage));
    REQUIRE(loadYaml(secondYaml, secondTable, errorMessage));

    OpenYAMM::Game::SurfaceMaterialRuntimeSet firstSet;
    OpenYAMM::Game::SurfaceMaterialRuntimeSet secondSet;
    std::string setErrorMessage;
    REQUIRE(firstSet.buildFromTable(firstTable, setErrorMessage));
    REQUIRE(secondSet.buildFromTable(secondTable, setErrorMessage));

    // Both maps own their resolved bindings; ids are runtime-only and may repeat
    // across maps while pointing at independent shading records.
    const uint16_t firstId = firstSet.resolveMaterialId("shared01", 0, false);
    const uint16_t secondId = secondSet.resolveMaterialId("shared01", 0, false);
    CHECK(firstId == secondId);
    CHECK(firstSet.material(firstId).sourceId == "stone");
    CHECK(secondSet.material(secondId).sourceId == "wood");
    CHECK(firstSet.material(firstId).roughness == doctest::Approx(0.30f));
    CHECK(secondSet.material(secondId).roughness == doctest::Approx(0.85f));

    // A default-constructed set (no table mounted) resolves everything to neutral.
    OpenYAMM::Game::SurfaceMaterialRuntimeSet emptySet;
    CHECK(emptySet.empty());
    CHECK(emptySet.resolveMaterialId("shared01", 0, false)
        == OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId);
    CHECK(emptySet.resolveMaterialId("anything", 0x10u, true)
        == OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId);
    const OpenYAMM::Game::ResolvedSurfaceMaterial &neutralMaterial =
        emptySet.material(OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId);
    CHECK(neutralMaterial.sourceId.empty());
    CHECK(neutralMaterial.specular == 0.0f);
    CHECK(neutralMaterial.emissiveStrength == 0.0f);

    // Invalid runtime IDs are also required to fall back to the materialized neutral row.
    CHECK(&emptySet.material(0xffff) == &neutralMaterial);
}

TEST_CASE("generic semantic rows coexist with liquid animation rows")
{
    const char *yamlText = R"yaml(
materials:
  - id: castle_stone
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castle01]
    shading:
      specular: 0.05
  - id: mm8_water
    semantic: water
    applies_to: [terrain, face]
    match:
      texture_names: [wtrtyl]
    animation:
      animation_length_ticks: 210
      frames: [hdwtr000, hdwtr001]
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(yamlText, table, errorMessage));

    const OpenYAMM::Game::SurfaceMaterialDefinition *pStone = table.findMatch("castle01", 0, false);
    REQUIRE(pStone != nullptr);
    CHECK(pStone->semantic == OpenYAMM::Game::SurfaceMaterialSemantic::Generic);
    REQUIRE(pStone->shading.has_value());
    CHECK(pStone->shading->specular == doctest::Approx(0.05f));

    const OpenYAMM::Game::SurfaceMaterialDefinition *pWater = table.findMatch("wtrtyl", 0, true);
    REQUIRE(pWater != nullptr);
    CHECK(pWater->semantic == OpenYAMM::Game::SurfaceMaterialSemantic::Water);
    CHECK(!pWater->shading.has_value());
    CHECK(pWater->animation.frames.size() == 2);
}

TEST_CASE("terrain material LUT packs the per-layer scalar contract")
{
    const char *yamlText = R"yaml(
materials:
  - id: terrain_gloss
    semantic: generic
    applies_to: [terrain]
    match:
      texture_names: [glosstyl]
    shading:
      roughness: 0.25
      specular: 0.5
      fresnel_strength: 0.75
      receives_wetness: true
      wetness_response: 0.6
      wet_roughness: 0.1
      wet_darkening: 0.2
      receives_puddles: true
      emissive_strength: 2.0
      emissive_color: [0.25, 0.5, 1.0]
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(yamlText, table, errorMessage));

    OpenYAMM::Game::SurfaceMaterialRuntimeSet set;
    std::string setErrorMessage;
    REQUIRE(set.buildFromTable(table, setErrorMessage));

    std::array<uint16_t, 256> layerIds = {};
    std::array<uint8_t, 256> transitionFlags = {};
    layerIds[7] = set.resolveMaterialId("glosstyl", 0, true);
    layerIds[8] = set.resolveMaterialId("glosstyl", 0, true);
    layerIds[9] = set.resolveMaterialId("glosstyl", 0, true);
    transitionFlags[9] = 1; // composited shore stays neutral

    const OpenYAMM::Game::TerrainMaterialLookup lookup =
        OpenYAMM::Game::buildTerrainMaterialLookup(set, layerIds, transitionFlags);

    REQUIRE(lookup.anyMaterialLayer);
    REQUIRE(lookup.anyEmissiveLayer);

    const auto byteOf = [&](size_t layer, size_t row, size_t channel) {
        // This is the byte address bgfx/OpenGL use for texel (layer, row) in a
        // tightly packed 256x3 RGBA8 upload.
        return lookup.bytes[(row * 256 + layer) * 4 + channel];
    };
    const auto approxByte = [](float value) {
        return doctest::Approx(static_cast<int>(std::lround(value * 255.0f))).epsilon(0.01);
    };

    // Layer 7 carries the authored material: rows 0/1/2 follow the packed contract.
    CHECK(OpenYAMM::Game::TerrainMaterialLookup::texelByteOffset(7, 0) == 28);
    CHECK(OpenYAMM::Game::TerrainMaterialLookup::texelByteOffset(7, 1) == 1052);
    CHECK(OpenYAMM::Game::TerrainMaterialLookup::texelByteOffset(7, 2) == 2076);
    CHECK(byteOf(7, 0, 0) == approxByte(0.25f));   // roughness
    CHECK(byteOf(7, 0, 1) == approxByte(0.5f));    // specular
    CHECK(byteOf(7, 0, 2) == approxByte(0.6f));    // wetness response
    CHECK(byteOf(7, 0, 3) == approxByte(0.1f));    // wet roughness
    CHECK(byteOf(7, 1, 0) == approxByte(0.2f));    // wet darkening
    CHECK(byteOf(7, 1, 1) == approxByte(0.75f));   // fresnel
    CHECK(byteOf(7, 1, 2) == 255);                 // puddles allowed
    CHECK(byteOf(7, 1, 3) == approxByte(2.0f * 0.25f)); // emissive strength / 4
    CHECK(byteOf(7, 2, 0) == approxByte(0.25f));   // emissive R
    CHECK(byteOf(7, 2, 1) == approxByte(0.5f));    // emissive G
    CHECK(byteOf(7, 2, 2) == approxByte(1.0f));    // emissive B
    CHECK(byteOf(7, 2, 3) == 0);                  // reserved

    // Layer 9 is a composited transition: neutral regardless of the resolved id.
    for (size_t row = 0; row < 3; ++row)
    {
        for (size_t channel = 0; channel < 4; ++channel)
        {
            CHECK(byteOf(9, row, channel) == byteOf(0, row, channel));
        }
    }

    // Untouched layers are neutral and identical to layer 0.
    for (size_t row = 0; row < 3; ++row)
    {
        for (size_t channel = 0; channel < 4; ++channel)
        {
            CHECK(byteOf(100, row, channel) == byteOf(0, row, channel));
        }
    }
}

TEST_CASE("terrain material LUT stays neutral without authored terrain materials")
{
    OpenYAMM::Game::SurfaceMaterialRuntimeSet set;
    std::array<uint16_t, 256> layerIds = {};
    std::array<uint8_t, 256> transitionFlags = {};

    const OpenYAMM::Game::TerrainMaterialLookup lookup =
        OpenYAMM::Game::buildTerrainMaterialLookup(set, layerIds, transitionFlags);

    CHECK(!lookup.anyMaterialLayer);
    CHECK(!lookup.anyEmissiveLayer);

    // Neutral rows carry the neutral defaults (roughness 0.9, specular 0, ...).
    const uint8_t roughnessNeutral = lookup.bytes[
        OpenYAMM::Game::TerrainMaterialLookup::texelByteOffset(0, 0, 0)];
    CHECK(roughnessNeutral == doctest::Approx(static_cast<int>(std::lround(0.9f * 255.0f))).epsilon(0.01));
    CHECK(lookup.bytes[OpenYAMM::Game::TerrainMaterialLookup::texelByteOffset(0, 0, 1)] == 0); // specular

    // These are the four consecutive bytes sampled by the GPU at layer 0, row 0.
    CHECK(lookup.bytes[0] == 230);
    CHECK(lookup.bytes[1] == 0);
    CHECK(lookup.bytes[2] == 0);
    CHECK(lookup.bytes[3] == 31);
}

TEST_CASE("terrain material LUT ignores animation-only material ids")
{
    const char *yamlText = R"yaml(
materials:
  - id: animated_water
    semantic: water
    applies_to: [terrain]
    match:
      texture_names: [watertyl]
    animation:
      frames: [wtrtyl1, wtrtyl2]
      frame_length_ticks: 4
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(yamlText, table, errorMessage));

    OpenYAMM::Game::SurfaceMaterialRuntimeSet set;
    REQUIRE(set.buildFromTable(table, errorMessage));

    std::array<uint16_t, 256> layerIds = {};
    std::array<uint8_t, 256> transitionFlags = {};
    layerIds[12] = set.resolveMaterialId("watertyl", 0, true);
    REQUIRE(layerIds[12] != OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId);

    const OpenYAMM::Game::TerrainMaterialLookup lookup =
        OpenYAMM::Game::buildTerrainMaterialLookup(set, layerIds, transitionFlags);

    CHECK(!lookup.anyMaterialLayer);
    CHECK(!lookup.anyEmissiveLayer);
}

TEST_CASE("surface material facade mask texture parses and resolves to the material")
{
    const char *yamlText = R"yaml(
materials:
  - id: castle_facade
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castlefacade]
    shading:
      roughness: 0.8
      specular: 0.2
      material_mask_texture: worlds/mm6/rendering/masks/castlefacade.png
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable table;
    std::string errorMessage;
    REQUIRE(loadYaml(yamlText, table, errorMessage));

    const OpenYAMM::Game::SurfaceMaterialDefinition *pFacade = table.findMatch("castlefacade", 0, false);
    REQUIRE(pFacade != nullptr);
    REQUIRE(pFacade->shading.has_value());
    CHECK(pFacade->shading->materialMaskTexture == "worlds/mm6/rendering/masks/castlefacade.png");

    OpenYAMM::Game::SurfaceMaterialRuntimeSet set;
    std::string setErrorMessage;
    REQUIRE(set.buildFromTable(table, setErrorMessage));
    const uint16_t materialId = set.resolveMaterialId("castlefacade", 0, false);
    REQUIRE(materialId != OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId);
    CHECK(set.material(materialId).materialMaskTexture == "worlds/mm6/rendering/masks/castlefacade.png");

    // Materials without the key stay unmasked, including the neutral record.
    CHECK(set.material(OpenYAMM::Game::SurfaceMaterialRuntimeSet::NeutralMaterialId)
              .materialMaskTexture
          .empty());
}

TEST_CASE("surface material facade mask texture rejects invalid authoring")
{
    const char *emptyPathYaml = R"yaml(
materials:
  - id: castle_facade
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castlefacade]
    shading:
      material_mask_texture: ""
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable emptyTable;
    std::string errorMessage;
    CHECK(!loadYaml(emptyPathYaml, emptyTable, errorMessage));
    CHECK(errorMessage.find("material_mask_texture") != std::string::npos);

    const char *whitespacePathYaml = R"yaml(
materials:
  - id: castle_facade
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castlefacade]
    shading:
      material_mask_texture: "has space.png"
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable whitespaceTable;
    CHECK(!loadYaml(whitespacePathYaml, whitespaceTable, errorMessage));

    const char *terrainOnlyYaml = R"yaml(
materials:
  - id: terrain_masked
    semantic: generic
    applies_to: [terrain]
    match:
      texture_names: [grasstyl]
    shading:
      material_mask_texture: worlds/mm6/rendering/masks/grass.png
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable terrainTable;
    CHECK(!loadYaml(terrainOnlyYaml, terrainTable, errorMessage));
    CHECK(errorMessage.find("face-only") != std::string::npos);

    const char *nonScalarYaml = R"yaml(
materials:
  - id: castle_facade
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castlefacade]
    shading:
      material_mask_texture: [a, b]
)yaml";

    OpenYAMM::Game::SurfaceMaterialTable nonScalarTable;
    CHECK(!loadYaml(nonScalarYaml, nonScalarTable, errorMessage));
}
