#include "doctest/doctest.h"

#include "game/render/SurfaceMaterialRuntime.h"
#include "game/tables/SurfaceMaterialTable.h"

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
         "texture_names: [t]\n    shading:\n      material_mask_texture: masks/stone.png\n",
         "material_mask_texture"},
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
