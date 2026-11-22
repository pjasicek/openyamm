#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/data/MapScriptSources.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <vector>

namespace
{
bool hasCandidate(const std::vector<std::string> &candidates, const std::string &path)
{
    return std::find(candidates.begin(), candidates.end(), path) != candidates.end();
}
}

TEST_CASE("a map's common scripts are its own world's: never another world's world_common.lua")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));

    for (const char *pWorldId : {"mm6", "mm7", "mm8"})
    {
        const std::vector<std::string> candidates =
            OpenYAMM::Game::buildLuaWorldCommonPathCandidates(assetFileSystem, pWorldId);
        const std::string own = std::string("worlds/") + pWorldId + "/events/common/" + pWorldId + "_common.lua";
        CHECK(hasCandidate(candidates, own));
        std::string resolved;
        const std::optional<std::string> text =
            OpenYAMM::Game::readExistingTexts(assetFileSystem, candidates, resolved);
        REQUIRE(text.has_value());
        CHECK(resolved == own);
        CHECK(text->find("MM9.ItemIds") == std::string::npos);
    }

    if (assetFileSystem.exists("worlds/mm9/events/common/world_common.lua"))
    {
        std::string resolved;
        OpenYAMM::Game::readExistingTexts(
            assetFileSystem, OpenYAMM::Game::buildLuaWorldCommonPathCandidates(assetFileSystem, "mm9"), resolved);
        CHECK(resolved == "worlds/mm9/events/common/world_common.lua; worlds/mm9/events/common/mm9_common.lua");
    }
}

TEST_CASE("a world's other <world>_*.lua scripts follow its <world>_common.lua, by name")
{
    const std::filesystem::path root =
        std::filesystem::temp_directory_path() / "openyamm_world_script_sources_test";
    std::filesystem::remove_all(root);
    const std::filesystem::path common = root / "assets" / "worlds" / "demo" / "events" / "common";
    std::filesystem::create_directories(common);
    std::filesystem::create_directories(root / "assets" / "engine");

    for (const char *pName : {"demo_quests.lua", "demo_common.lua", "demo_aaa.lua", "other.lua"})
    {
        std::ofstream(common / pName) << "-- " << pName << '\n';
    }

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(root, root / "assets", OpenYAMM::Engine::AssetScaleTier::X1, "demo"));
    std::string resolved;
    OpenYAMM::Game::readExistingTexts(
        assetFileSystem, OpenYAMM::Game::buildLuaWorldCommonPathCandidates(assetFileSystem, "demo"), resolved);
    CHECK(resolved
        == "worlds/demo/events/common/demo_common.lua; worlds/demo/events/common/demo_aaa.lua; "
           "worlds/demo/events/common/demo_quests.lua");
    std::filesystem::remove_all(root);
}
