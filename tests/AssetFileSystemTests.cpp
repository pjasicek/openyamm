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

TEST_CASE("AssetFileSystem reads aliased package files case-insensitively")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "worlds" / "mm8" / "videos" / "Houses" / "Ntrhall.ogv", "house-video");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1));

        const std::optional<std::string> videoText =
            assetFileSystem.readTextFile("Videos/Houses/ntrhall.ogv");
        REQUIRE(videoText.has_value());
        CHECK_EQ(*videoText, "house-video");

        CHECK(assetFileSystem.exists("Videos/Houses/ntrhall.ogv"));

        const std::optional<std::filesystem::path> physicalPath =
            assetFileSystem.resolvePhysicalPath("Videos/Houses/ntrhall.ogv");
        REQUIRE(physicalPath.has_value());
        CHECK(physicalPath->generic_string().ends_with("assets_dev/worlds/mm8/videos/Houses/Ntrhall.ogv"));
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

TEST_CASE("AssetFileSystem merges inactive world icon roots")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "icons" / "engine_only.bmp", "engine-icon");
    writeTextFile(assetRoot / "engine" / "icons" / "shared.bmp", "same-icon");
    writeTextFile(assetRoot / "worlds" / "mm6" / "icons" / "mm6_only.bmp", "mm6-icon");
    writeTextFile(assetRoot / "worlds" / "mm6" / "icons" / "shared.bmp", "same-icon");
    writeTextFile(assetRoot / "worlds" / "mm7" / "icons" / "mm7_only.bmp", "mm7-icon");
    writeTextFile(assetRoot / "worlds" / "mm8" / "icons" / "mm8_only.bmp", "mm8-icon");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        const std::optional<std::string> mm6IconText =
            assetFileSystem.readTextFile("Data/icons/mm6_only.bmp");
        REQUIRE(mm6IconText.has_value());
        CHECK_EQ(*mm6IconText, "mm6-icon");

        const std::optional<std::string> mm7IconText =
            assetFileSystem.readTextFile("Data/icons/mm7_only.bmp");
        REQUIRE(mm7IconText.has_value());
        CHECK_EQ(*mm7IconText, "mm7-icon");

        const std::optional<std::string> mm8IconText =
            assetFileSystem.readTextFile("Data/icons/mm8_only.bmp");
        REQUIRE(mm8IconText.has_value());
        CHECK_EQ(*mm8IconText, "mm8-icon");

        const std::optional<std::string> sharedIconText =
            assetFileSystem.readTextFile("Data/icons/shared.bmp");
        REQUIRE(sharedIconText.has_value());
        CHECK_EQ(*sharedIconText, "same-icon");

        const std::vector<std::string> entries = assetFileSystem.enumerate("Data/icons");
        CHECK(containsEntry(entries, "engine_only.bmp"));
        CHECK(containsEntry(entries, "mm6_only.bmp"));
        CHECK(containsEntry(entries, "mm7_only.bmp"));
        CHECK(containsEntry(entries, "mm8_only.bmp"));

        const std::optional<std::filesystem::path> mm7PhysicalPath =
            assetFileSystem.resolvePhysicalPath("Data/icons/mm7_only.bmp");
        REQUIRE(mm7PhysicalPath.has_value());
        CHECK(mm7PhysicalPath->generic_string().ends_with("assets_dev/worlds/mm7/icons/mm7_only.bmp"));
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem rejects conflicting merged world icons")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "icons" / "shared.bmp", "engine-icon");
    writeTextFile(assetRoot / "worlds" / "mm6" / "icons" / "shared.bmp", "mm6-icon");
    writeTextFile(assetRoot / "worlds" / "mm8" / "maps" / "out01.scene.yml", "active-world-map");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        CHECK_FALSE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem merges inactive world audio roots")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "audio" / "engine_only.wav", "engine-audio");
    writeTextFile(assetRoot / "engine" / "audio" / "shared.wav", "same-audio");
    writeTextFile(assetRoot / "worlds" / "mm6" / "audio" / "mm6_only.wav", "mm6-audio");
    writeTextFile(assetRoot / "worlds" / "mm6" / "audio" / "shared.wav", "same-audio");
    writeTextFile(assetRoot / "worlds" / "mm7" / "audio" / "mm7_only.wav", "mm7-audio");
    writeTextFile(assetRoot / "worlds" / "mm8" / "audio" / "mm8_only.wav", "mm8-audio");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        const std::optional<std::string> mm6AudioText =
            assetFileSystem.readTextFile("Data/EnglishD/mm6_only.wav");
        REQUIRE(mm6AudioText.has_value());
        CHECK_EQ(*mm6AudioText, "mm6-audio");

        const std::optional<std::string> mm7AudioText =
            assetFileSystem.readTextFile("Data/EnglishD/mm7_only.wav");
        REQUIRE(mm7AudioText.has_value());
        CHECK_EQ(*mm7AudioText, "mm7-audio");

        const std::optional<std::string> mm8AudioText =
            assetFileSystem.readTextFile("Data/EnglishD/mm8_only.wav");
        REQUIRE(mm8AudioText.has_value());
        CHECK_EQ(*mm8AudioText, "mm8-audio");

        const std::optional<std::string> sharedAudioText =
            assetFileSystem.readTextFile("Data/EnglishD/shared.wav");
        REQUIRE(sharedAudioText.has_value());
        CHECK_EQ(*sharedAudioText, "same-audio");

        const std::vector<std::string> entries = assetFileSystem.enumerate("Data/EnglishD");
        CHECK(containsEntry(entries, "engine_only.wav"));
        CHECK(containsEntry(entries, "mm6_only.wav"));
        CHECK(containsEntry(entries, "mm7_only.wav"));
        CHECK(containsEntry(entries, "mm8_only.wav"));

        const std::optional<std::filesystem::path> mm7PhysicalPath =
            assetFileSystem.resolvePhysicalPath("Data/EnglishD/mm7_only.wav");
        REQUIRE(mm7PhysicalPath.has_value());
        CHECK(mm7PhysicalPath->generic_string().ends_with("assets_dev/worlds/mm7/audio/mm7_only.wav"));
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem rejects conflicting merged world audio")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "audio" / "shared.wav", "engine-audio");
    writeTextFile(assetRoot / "worlds" / "mm6" / "audio" / "shared.wav", "mm6-audio");
    writeTextFile(assetRoot / "worlds" / "mm8" / "maps" / "out01.scene.yml", "active-world-map");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        CHECK_FALSE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));
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

TEST_CASE("AssetFileSystem resolves English data tables through engine data tables")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "data_tables" / "english" / "stats.txt", "shared-stats");
    writeTextFile(assetRoot / "engine" / "data_tables" / "english" / "quest.txt", "engine-quest");

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
        CHECK_EQ(*questText, "engine-quest");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem resolves engine tables through data_tables")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "data_tables" / "items.txt", "engine-items");
    writeTextFile(assetRoot / "engine" / "data_tables" / "map_stats.txt", "engine-map-stats");

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
        CHECK_EQ(*mapStatsText, "engine-map-stats");
    }

    std::filesystem::remove_all(temporaryRoot);
}
