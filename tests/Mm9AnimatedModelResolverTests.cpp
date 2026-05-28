#include "doctest/doctest.h"

#include "game/mm9/Mm9AnimatedModelResolver.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

namespace
{
std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_mm9_model_resolver_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

std::filesystem::path sourceRoot()
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR);
}
}

TEST_CASE("MM9 animated model resolver maps Filename and Skin through model registry")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path worldRoot = temporaryRoot / "assets_dev" / "worlds" / "mm9";
    const std::filesystem::path registryPath = worldRoot / "models" / "model_registry.yml";

    writeTextFile(
        registryPath,
        R"(
schema: openyamm.mm9.model_registry.v2
world: mm9
models:
- model_id: bigfoot
  roles: [actor_model]
  source_model: models/bigfoot.abc
  model_asset: models/bigfoot.glb
  model_sidecar: models/bigfoot.model.yml
  source_skins: [skins/bigfoot1.dtx]
  skin_bindings:
  - id: bigfoot_bigfoot1
    source_skins: [skins/bigfoot1.dtx]
  - id: bigfoot_bigfoot2
    source_skins: [skins/bigfoot2.dtx]
- model_id: clansoldier
  roles: [actor_model]
  source_model: models/clansoldier.abc
  model_asset: models/clansoldier.glb
  model_sidecar: models/clansoldier.model.yml
  source_skins: [skins/beldonian1.dtx, skins/beldsword.dtx, skins/beldshield1.dtx]
  skin_bindings:
  - id: clansoldier_beldonian1
    source_skins: [skins/beldonian1.dtx, skins/beldsword.dtx, skins/beldshield1.dtx]
- model_id: butterfly
  roles: [static_model]
  source_model: models/butterfly.abc
  model_asset: models/butterfly.glb
  model_sidecar: models/butterfly.model.yml
- model_id: peasantm2
  roles: [actor_model]
  source_model: models/peasantm2.abc
  model_asset: models/peasantm2.glb
  model_sidecar: models/peasantm2.model.yml
  source_skins: [skins/peasantm2a.dtx]
  skin_bindings:
  - id: peasantm2_a
    source_skins: [skins/peasantm2a.dtx]
  - id: peasantm2_b
    source_skins: [skins/peasantm2b.dtx]
)");

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(resolver.loadRegistry(registryPath, errorMessage), errorMessage);
    CHECK(resolver.entries().size() == 4);

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> bigfoot =
        resolver.resolve("MODELS\\BIGFOOT.ABC", "BIGFOOT2", diagnostics);
    REQUIRE(bigfoot.has_value());
    CHECK(diagnostics.empty());
    CHECK(bigfoot->requestedSourceModel == "MODELS\\BIGFOOT.ABC");
    CHECK(bigfoot->requestedSourceSkin == "BIGFOOT2");
    CHECK(bigfoot->normalizedSourceModel == "models/bigfoot.abc");
    REQUIRE(bigfoot->normalizedSourceSkins.size() == 1);
    CHECK(bigfoot->normalizedSourceSkins[0] == "skins/bigfoot2.dtx");
    CHECK(bigfoot->modelId == "bigfoot");
    CHECK(bigfoot->skinBindingId == "bigfoot_bigfoot2");
    CHECK(bigfoot->modelAssetPath == worldRoot / "models" / "bigfoot.glb");
    CHECK(bigfoot->modelSidecarPath == worldRoot / "models" / "bigfoot.model.yml");
    REQUIRE(bigfoot->materialOverrides.size() == 1);
    CHECK(bigfoot->materialOverrides[0].materialIndex == 0);
    CHECK(bigfoot->materialOverrides[0].runtimeTexture == "skins/bigfoot2.dtx");

    diagnostics.clear();
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> defaultSkin =
        resolver.resolve("bigfoot", "", diagnostics);
    REQUIRE(defaultSkin.has_value());
    CHECK(defaultSkin->skinBindingId == "bigfoot_bigfoot1");
    REQUIRE(defaultSkin->materialOverrides.size() == 1);
    CHECK(defaultSkin->materialOverrides[0].runtimeTexture == "skins/bigfoot1.dtx");

    diagnostics.clear();
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> multiMaterial =
        resolver.resolve(
            "models/clansoldier.abc",
            "skins/beldonian1.dtx;skins/beldsword.dtx;skins/beldshield1.dtx",
            diagnostics);
    REQUIRE(multiMaterial.has_value());
    CHECK(multiMaterial->skinBindingId == "clansoldier_beldonian1");
    REQUIRE(multiMaterial->materialOverrides.size() == 3);
    CHECK(multiMaterial->materialOverrides[0].runtimeTexture == "skins/beldonian1.dtx");
    CHECK(multiMaterial->materialOverrides[1].runtimeTexture == "skins/beldsword.dtx");
    CHECK(multiMaterial->materialOverrides[2].runtimeTexture == "skins/beldshield1.dtx");

    diagnostics.clear();
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> staticModel =
        resolver.resolve("butterfly", "", diagnostics);
    REQUIRE(staticModel.has_value());
    CHECK(staticModel->materialOverrides.empty());
    CHECK(staticModel->skinBindingId.empty());

    diagnostics.clear();
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> sidecarMapped =
        resolver.resolveModelAsset(
            "MODELS\\PEASANTM2.GLB",
            "peasantm2_b",
            "models/props/PlantsandTrees/Tree04.abc",
            "",
            diagnostics);
    REQUIRE(sidecarMapped.has_value());
    CHECK(diagnostics.empty());
    CHECK(sidecarMapped->requestedSourceModel == "models/props/PlantsandTrees/Tree04.abc");
    CHECK(sidecarMapped->normalizedSourceModel == "models/peasantm2.abc");
    CHECK(sidecarMapped->modelId == "peasantm2");
    CHECK(sidecarMapped->skinBindingId == "peasantm2_b");
    CHECK(sidecarMapped->modelAssetPath == worldRoot / "models" / "peasantm2.glb");
    REQUIRE(sidecarMapped->materialOverrides.size() == 1);
    CHECK(sidecarMapped->materialOverrides[0].runtimeTexture == "skins/peasantm2b.dtx");

    diagnostics.clear();
    CHECK(!resolver.resolveModelAsset(
        "models/peasantm2.glb",
        "missing_binding",
        "models/peasantm2.abc",
        "",
        diagnostics).has_value());
    REQUIRE(diagnostics.size() == 1);
    CHECK(diagnostics[0].error);
    CHECK(diagnostics[0].message.find("model_skin_binding") != std::string::npos);

    diagnostics.clear();
    CHECK(!resolver.resolve("models/missing.abc", "", diagnostics).has_value());
    REQUIRE(diagnostics.size() == 1);
    CHECK(diagnostics[0].error);
    CHECK(diagnostics[0].message.find("Filename") != std::string::npos);

    diagnostics.clear();
    CHECK(!resolver.resolve("models/bigfoot.abc", "skins/unknown.dtx", diagnostics).has_value());
    REQUIRE(diagnostics.size() == 1);
    CHECK(diagnostics[0].error);
    CHECK(diagnostics[0].message.find("Skin") != std::string::npos);

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("MM9 animated model resolver loads current generated registry when present")
{
    const std::filesystem::path registryPath =
        sourceRoot() / "assets_dev" / "worlds" / "mm9" / "models" / "model_registry.yml";
    if (!std::filesystem::exists(registryPath))
    {
        WARN("MM9 generated model registry is not present; skipping real registry resolver validation");
        return;
    }

    OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
    std::string errorMessage;
    REQUIRE_MESSAGE(resolver.loadRegistry(registryPath, errorMessage), errorMessage);

    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> diagnostics;
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> resolution =
        resolver.resolve("MODELS\\BIGFOOT.ABC", "SKINS\\BIGFOOT3.DTX", diagnostics);
    REQUIRE(resolution.has_value());
    CHECK(diagnostics.empty());
    CHECK(resolution->modelId == "bigfoot");
    CHECK(resolution->skinBindingId == "bigfoot_bigfoot3");
    CHECK(resolution->modelAssetPath == registryPath.parent_path().parent_path() / "models" / "bigfoot.glb");
    REQUIRE(resolution->materialOverrides.size() == 1);
    CHECK(resolution->materialOverrides[0].runtimeTexture == "skins/bigfoot3.dtx");
}
