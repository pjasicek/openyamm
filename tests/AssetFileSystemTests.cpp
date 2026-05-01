#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <vector>

namespace
{
std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_assetfs_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

bool containsEntry(const std::vector<std::string> &entries, const std::string &entry)
{
    return std::find(entries.begin(), entries.end(), entry) != entries.end();
}
}

TEST_CASE("AssetFileSystem resolves package aliases before legacy asset paths")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    const std::filesystem::path editorAssetRoot = temporaryRoot / "assets_editor_dev";

    writeTextFile(assetRoot / "Data" / "ui" / "layout.yml", "legacy-ui");
    writeTextFile(assetRoot / "engine" / "ui" / "layout.yml", "engine-ui");
    writeTextFile(assetRoot / "Data" / "games" / "out01.scene.yml", "legacy-map");
    writeTextFile(assetRoot / "worlds" / "mm8" / "maps" / "out01.scene.yml", "world-map");
    writeTextFile(editorAssetRoot / "worlds" / "mm8" / "maps" / "editor.scene.yml", "editor-world-map");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1));

        const std::optional<std::string> uiText = assetFileSystem.readTextFile("Data/ui/layout.yml");
        REQUIRE(uiText.has_value());
        CHECK_EQ(*uiText, "engine-ui");

        const std::optional<std::filesystem::path> uiPhysicalPath =
            assetFileSystem.resolvePhysicalPath("Data/ui/layout.yml");
        REQUIRE(uiPhysicalPath.has_value());
        CHECK(uiPhysicalPath->generic_string().ends_with("assets_dev/engine/ui/layout.yml"));

        const std::optional<std::string> mapText =
            assetFileSystem.readTextFile("Data/games/out01.scene.yml");
        REQUIRE(mapText.has_value());
        CHECK_EQ(*mapText, "world-map");

        const std::optional<std::string> editorMapText =
            assetFileSystem.readTextFile("Data/games/editor.scene.yml");
        REQUIRE(editorMapText.has_value());
        CHECK_EQ(*editorMapText, "editor-world-map");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem keeps legacy fallback and enumerates package aliases")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "Data" / "ui" / "legacy_only.yml", "legacy-only");
    writeTextFile(assetRoot / "Data" / "ui" / "shared.yml", "legacy-shared");
    writeTextFile(assetRoot / "engine" / "ui" / "engine_only.yml", "engine-only");
    writeTextFile(assetRoot / "engine" / "ui" / "shared.yml", "engine-shared");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1));

        const std::optional<std::string> legacyText =
            assetFileSystem.readTextFile("Data/ui/legacy_only.yml");
        REQUIRE(legacyText.has_value());
        CHECK_EQ(*legacyText, "legacy-only");

        const std::optional<std::string> sharedText = assetFileSystem.readTextFile("Data/ui/shared.yml");
        REQUIRE(sharedText.has_value());
        CHECK_EQ(*sharedText, "engine-shared");

        const std::vector<std::string> entries = assetFileSystem.enumerate("Data/ui");
        CHECK(containsEntry(entries, "legacy_only.yml"));
        CHECK(containsEntry(entries, "engine_only.yml"));
        CHECK(containsEntry(entries, "shared.yml"));
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem keeps EnglishT and icon font aliases distinct")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "fonts" / "english_text" / "LEGAL.FNT", "english-legal");
    writeTextFile(assetRoot / "engine" / "fonts" / "icons" / "LEGAL.FNT", "icon-legal");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1));

        const std::optional<std::string> englishFontText =
            assetFileSystem.readTextFile("Data/EnglishT/LEGAL.FNT");
        REQUIRE(englishFontText.has_value());
        CHECK_EQ(*englishFontText, "english-legal");

        const std::optional<std::string> iconFontText =
            assetFileSystem.readTextFile("Data/icons/LEGAL.FNT");
        REQUIRE(iconFontText.has_value());
        CHECK_EQ(*iconFontText, "icon-legal");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem resolves EnglishT text through shared English data tables")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "data_tables" / "english" / "Global.txt", "shared-global");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1));

        const std::optional<std::string> globalText =
            assetFileSystem.readTextFile("Data/EnglishT/Global.txt");
        REQUIRE(globalText.has_value());
        CHECK_EQ(*globalText, "shared-global");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem resolves English data tables through shared and world data tables")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "data_tables" / "english" / "stats.txt", "shared-stats");
    writeTextFile(assetRoot / "worlds" / "mm8" / "data_tables" / "english" / "quest.txt", "world-quest");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1));

        const std::optional<std::string> statsText =
            assetFileSystem.readTextFile("Data/data_tables/english/stats.txt");
        REQUIRE(statsText.has_value());
        CHECK_EQ(*statsText, "shared-stats");

        const std::optional<std::string> questText =
            assetFileSystem.readTextFile("Data/data_tables/english/quest.txt");
        REQUIRE(questText.has_value());
        CHECK_EQ(*questText, "world-quest");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem resolves shared and world tables through data_tables")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "data_tables" / "items.txt", "engine-items");
    writeTextFile(assetRoot / "worlds" / "mm8" / "data_tables" / "map_stats.txt", "world-map-stats");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1));

        const std::optional<std::string> itemText =
            assetFileSystem.readTextFile("Data/data_tables/items.txt");
        REQUIRE(itemText.has_value());
        CHECK_EQ(*itemText, "engine-items");

        const std::optional<std::string> mapStatsText =
            assetFileSystem.readTextFile("Data/data_tables/map_stats.txt");
        REQUIRE(mapStatsText.has_value());
        CHECK_EQ(*mapStatsText, "world-map-stats");
    }

    std::filesystem::remove_all(temporaryRoot);
}
