#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "editor/model/Mm9ModelInstanceActorResolver.h"

#include <chrono>
#include <filesystem>
#include <fstream>

namespace
{
std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_mm9_actor_resolver_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}
}

TEST_CASE("MM9 model instance actor resolver preserves official actor row evidence")
{
    OpenYAMM::Editor::Mm9ModelInstanceActorSourceLookup lookup = {};

    OpenYAMM::Editor::Mm9ModelInstanceActorSourceLookup::Candidate candidate = {};
    candidate.id = "bandit_highwayman3";
    candidate.source.variantId = candidate.id;
    candidate.source.sourceModel = "models/highwayman.abc";
    candidate.source.sourceSkin = "skins/highwayman3.dtx";
    candidate.source.inferredFromActorClass = true;
    candidate.source.actorRow.table = "ACTOR";
    candidate.source.actorRow.row = "12";
    candidate.source.actorRow.number = "20";
    candidate.source.actorRow.monsterName = "Bandit";
    candidate.source.actorRow.typePicture = "Highwayman C";
    candidate.source.actorRow.baseName = "Highwayman";
    lookup.sourceByActorKey["bandit"].push_back(candidate);

    OpenYAMM::Game::OutdoorSceneModelInstance modelInstance = {};
    modelInstance.sourceClass = "Bandit";
    modelInstance.sourceName = "Bandit0";
    modelInstance.sourceModel = "models/highwayman.abc";

    const OpenYAMM::Editor::Mm9ResolvedModelInstanceActorSource resolved =
        OpenYAMM::Editor::resolveMm9ModelInstanceActorSource(modelInstance, &lookup);

    CHECK(resolved.variantId == "bandit_highwayman3");
    CHECK(resolved.sourceModel == "models/highwayman.abc");
    CHECK(resolved.sourceSkin == "skins/highwayman3.dtx");
    CHECK(resolved.inferredFromActorClass);
    CHECK(resolved.actorRow.table == "ACTOR");
    CHECK(resolved.actorRow.row == "12");
    CHECK(resolved.actorRow.number == "20");
    CHECK(resolved.actorRow.monsterName == "Bandit");
    CHECK(resolved.actorRow.typePicture == "Highwayman C");
    CHECK(resolved.actorRow.baseName == "Highwayman");
}

TEST_CASE("MM9 model instance actor resolver enriches actor rows from official gameplay table")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds/mm9/models/model_registry.yml",
        R"(
schema: openyamm.mm9.model_registry.v2
world: mm9
models:
- model_id: highwayman
  roles:
  - actor_model
  source_model: models/highwayman.abc
  model_asset: models/highwayman.glb
  model_sidecar: models/highwayman.model.yml
  skin_bindings:
  - id: highwayman_bandit
    source_skins:
    - skins/highwayman3.dtx
    actor_rows:
    - table: ACTOR
      row: 12
      number: '20'
      monster_name: Bandit
      type_picture: Highwayman C
      base_name: Highwayman
)");
    writeTextFile(
        assetRoot / "worlds/mm9/source/data/ACTOR.txt",
        "Number\tMonster Name\tType/Picture\tLVL\tHP\tAC\tEXP\tSPD\tScriptName\tFootSound\t"
        "IsMonster\tHostility Group\tVoice Radius\n"
        "20\tBandit Captain\tHighwayman C\t7\t45\t12\t300\t9\tBANDIT.scr\tdirt\t1\t3\t1440\n");

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        temporaryRoot,
        assetRoot,
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    const std::optional<OpenYAMM::Editor::Mm9ModelInstanceActorSourceLookup> lookup =
        OpenYAMM::Editor::loadMm9ModelInstanceActorSourceLookup(assetFileSystem);
    REQUIRE(lookup.has_value());

    OpenYAMM::Game::OutdoorSceneModelInstance modelInstance = {};
    modelInstance.sourceClass = "Bandit";
    modelInstance.sourceName = "Bandit0";
    modelInstance.sourceModel = "models/highwayman.abc";

    const OpenYAMM::Editor::Mm9ResolvedModelInstanceActorSource resolved =
        OpenYAMM::Editor::resolveMm9ModelInstanceActorSource(modelInstance, &*lookup);

    CHECK(resolved.variantId == "highwayman_bandit");
    CHECK(resolved.actorRow.level == "7");
    CHECK(resolved.actorRow.hitPoints == "45");
    CHECK(resolved.actorRow.armorClass == "12");
    CHECK(resolved.actorRow.experience == "300");
    CHECK(resolved.actorRow.speed == "9");
    CHECK(resolved.actorRow.scriptName == "BANDIT.scr");
    CHECK(resolved.actorRow.footSound == "dirt");
    CHECK(resolved.actorRow.isMonster == "1");
    CHECK(resolved.actorRow.hostilityGroup == "3");
    CHECK(resolved.actorRow.voiceRadius == "1440");

    std::filesystem::remove_all(temporaryRoot);
}
