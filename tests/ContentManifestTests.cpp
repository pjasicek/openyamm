#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/content/ContentManifest.h"

#include <doctest/doctest.h>

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>

namespace
{
std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_manifest_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}
}

TEST_CASE("content manifests default when package files are absent")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    std::filesystem::create_directories(assetRoot);

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        std::string error;
        const OpenYAMM::Game::CampaignManifest campaign =
            OpenYAMM::Game::loadCampaignManifestOrDefault(assetFileSystem, "default", "mm8", error);
        CHECK(error.empty());
        CHECK_FALSE(campaign.loadedFromFile);
        REQUIRE_EQ(campaign.worlds.size(), 1);
        CHECK_EQ(campaign.worlds.front(), "mm8");

        const OpenYAMM::Game::WorldManifest world =
            OpenYAMM::Game::loadActiveWorldManifestOrDefault(assetFileSystem, "mm8", error);
        CHECK(error.empty());
        CHECK_FALSE(world.loadedFromFile);
        CHECK_EQ(world.id, "mm8");
        CHECK_EQ(world.start.mapFileName, "out01.odm");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("content manifests parse mounted world and campaign definitions")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(
        assetRoot / "worlds" / "custom" / "world.yml",
        "id: custom\n"
        "name: Custom World\n"
        "sourceGame: custom\n"
        "start:\n"
        "  map: custom01.odm\n"
        "  introMovie: custom_intro\n");
    writeTextFile(
        assetRoot / "campaigns" / "test" / "campaign.yml",
        "id: test\n"
        "name: Test Campaign\n"
        "worlds:\n"
        "  - mm8\n"
        "  - custom\n"
        "startWorlds:\n"
        "  - custom\n");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "custom"));

        std::string error;
        const OpenYAMM::Game::CampaignManifest campaign =
            OpenYAMM::Game::loadCampaignManifestOrDefault(assetFileSystem, "test", "custom", error);
        CHECK(error.empty());
        REQUIRE(campaign.loadedFromFile);
        CHECK_EQ(campaign.id, "test");
        REQUIRE_EQ(campaign.worlds.size(), 2);
        CHECK_EQ(campaign.worlds[1], "custom");
        REQUIRE_EQ(campaign.startWorlds.size(), 1);
        CHECK_EQ(campaign.startWorlds.front(), "custom");

        const OpenYAMM::Game::WorldManifest world =
            OpenYAMM::Game::loadActiveWorldManifestOrDefault(assetFileSystem, "custom", error);
        CHECK(error.empty());
        REQUIRE(world.loadedFromFile);
        CHECK_EQ(world.id, "custom");
        CHECK_EQ(world.name, "Custom World");
        CHECK_EQ(world.start.mapFileName, "custom01.odm");
        CHECK_EQ(world.start.introMovie, "custom_intro");
    }

    std::filesystem::remove_all(temporaryRoot);
}

