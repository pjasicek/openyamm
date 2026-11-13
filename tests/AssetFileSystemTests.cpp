#include "engine/AssetFileSystem.h"
#include "tests/ContentPackTestSupport.h"
#include "engine/AssetScaleTier.h"
#include "engine/Localization.h"
#include "game/gameplay/ActorNameText.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <future>
#include <optional>
#include <string>
#include <utility>
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

uint32_t crc32ForString(const std::string &contents)
{
    uint32_t crc = 0xffffffffu;

    for (const unsigned char byte : contents)
    {
        crc ^= byte;

        for (int bitIndex = 0; bitIndex < 8; ++bitIndex)
        {
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
        }
    }

    return crc ^ 0xffffffffu;
}

void writeUInt16(std::ofstream &file, uint16_t value)
{
    file.put(static_cast<char>(value & 0xffu));
    file.put(static_cast<char>((value >> 8) & 0xffu));
}

void writeUInt32(std::ofstream &file, uint32_t value)
{
    file.put(static_cast<char>(value & 0xffu));
    file.put(static_cast<char>((value >> 8) & 0xffu));
    file.put(static_cast<char>((value >> 16) & 0xffu));
    file.put(static_cast<char>((value >> 24) & 0xffu));
}

void writeZipFile(
    const std::filesystem::path &path,
    const std::vector<std::pair<std::string, std::string>> &files)
{
    struct CentralDirectoryEntry
    {
        std::string name;
        uint32_t crc = 0;
        uint32_t size = 0;
        uint32_t localHeaderOffset = 0;
    };

    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    std::vector<CentralDirectoryEntry> centralDirectoryEntries;

    for (const std::pair<std::string, std::string> &entry : files)
    {
        CentralDirectoryEntry centralDirectoryEntry = {};
        centralDirectoryEntry.name = entry.first;
        centralDirectoryEntry.crc = crc32ForString(entry.second);
        centralDirectoryEntry.size = static_cast<uint32_t>(entry.second.size());
        centralDirectoryEntry.localHeaderOffset = static_cast<uint32_t>(file.tellp());
        centralDirectoryEntries.push_back(centralDirectoryEntry);

        writeUInt32(file, 0x04034b50u);
        writeUInt16(file, 20);
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt32(file, centralDirectoryEntry.crc);
        writeUInt32(file, centralDirectoryEntry.size);
        writeUInt32(file, centralDirectoryEntry.size);
        writeUInt16(file, static_cast<uint16_t>(centralDirectoryEntry.name.size()));
        writeUInt16(file, 0);
        file.write(centralDirectoryEntry.name.data(), static_cast<std::streamsize>(centralDirectoryEntry.name.size()));
        file.write(entry.second.data(), static_cast<std::streamsize>(entry.second.size()));
    }

    const uint32_t centralDirectoryOffset = static_cast<uint32_t>(file.tellp());

    for (const CentralDirectoryEntry &entry : centralDirectoryEntries)
    {
        writeUInt32(file, 0x02014b50u);
        writeUInt16(file, 20);
        writeUInt16(file, 20);
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt32(file, entry.crc);
        writeUInt32(file, entry.size);
        writeUInt32(file, entry.size);
        writeUInt16(file, static_cast<uint16_t>(entry.name.size()));
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt16(file, 0);
        writeUInt32(file, 0);
        writeUInt32(file, entry.localHeaderOffset);
        file.write(entry.name.data(), static_cast<std::streamsize>(entry.name.size()));
    }

    const uint32_t centralDirectorySize = static_cast<uint32_t>(file.tellp()) - centralDirectoryOffset;

    writeUInt32(file, 0x06054b50u);
    writeUInt16(file, 0);
    writeUInt16(file, 0);
    writeUInt16(file, static_cast<uint16_t>(centralDirectoryEntries.size()));
    writeUInt16(file, static_cast<uint16_t>(centralDirectoryEntries.size()));
    writeUInt32(file, centralDirectorySize);
    writeUInt32(file, centralDirectoryOffset);
    writeUInt16(file, 0);
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
    writeTextFile(editorAssetRoot / "worlds" / "mm8" / "maps" / "out01.scene.yml", "editor-world-map");
    writeTextFile(editorAssetRoot / "worlds" / "mm8" / "maps" / "editor.scene.yml", "editor-only-map");

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

        const std::optional<std::string> editorOverrideMapText =
            assetFileSystem.readTextFile("Data/games/out01.scene.yml");
        REQUIRE(editorOverrideMapText.has_value());
        CHECK_EQ(*editorOverrideMapText, "world-map");

        const std::optional<std::string> editorOnlyMapText =
            assetFileSystem.readTextFile("Data/games/editor.scene.yml");
        CHECK_FALSE(editorOnlyMapText.has_value());
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem streams and seeks through resolved package aliases")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "videos" / "Houses" / "Sample.ogv", "0123456789");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1));

        std::unique_ptr<OpenYAMM::Engine::AssetReadStream> pStream =
            assetFileSystem.openReadStream("Videos/Houses/sample.ogv");
        REQUIRE(pStream != nullptr);
        CHECK(pStream->isOpen());
        CHECK_EQ(pStream->length(), 10);

        std::array<char, 4> firstBytes = {};
        CHECK_EQ(pStream->read(firstBytes.data(), firstBytes.size()), 4);
        CHECK_EQ(std::string(firstBytes.data(), firstBytes.size()), "0123");
        CHECK_EQ(pStream->tell(), 4);

        REQUIRE(pStream->seek(7));
        std::array<char, 3> lastBytes = {};
        CHECK_EQ(pStream->read(lastBytes.data(), lastBytes.size()), 3);
        CHECK_EQ(std::string(lastBytes.data(), lastBytes.size()), "789");
        CHECK_EQ(pStream->tell(), 10);
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

TEST_CASE("AssetFileSystem mounts the content packs of an index")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets";
    struct Pack
    {
        const char *pId;
        const char *pPackage;
        const char *pMount;
        std::vector<std::pair<std::string, std::string>> entries;
    };
    // Core packs mount at the package root, domain packs at their folder; a domain may span several packs.
    const std::vector<Pack> packs = {
        {"engine.core",
         "engine",
         "/engine",
         {{"ui/layout.yml", "engine-ui"}, {"data_tables/map_stats.txt", "engine-map-stats"}}},
        {"engine.data_tables.0", "engine", "/engine/data_tables", {{"english/Global.txt", "engine-global"}}},
        {"mm6.core", "mm6", "/worlds/mm6", {{"textures/shared.bmp", "active-texture"}}},
        {"mm6.maps.0", "mm6", "/worlds/mm6/maps", {{"shared.odm", "active-map"}}},
        {"mm6.maps.lighting.0", "mm6", "/worlds/mm6/maps", {{"shared.lighting", "active-lighting"}}},
        {"mm6.videos.0", "mm6", "/worlds/mm6/videos", {{"Houses/sample.ogv", "0123456789"}}},
        {"mm8.core", "mm8", "/worlds/mm8", {{"textures/shared.bmp", "inactive-texture"}}},
        {"mm8.maps.1", "mm8", "/worlds/mm8/maps", {{"out01.odm", "inactive-map"}}},
        {"engine.rulesets", "engine", "/engine/rulesets", {{"maw/ruleset.yml", "id: maw"}}},
    };
    std::string index = "{\"schema\": 1, \"release\": \"test\", \"build\": \"test\", \"profile\": \"desktop\", "
                        "\"content_format\": 1, \"store\": \"packs\", \"packs\": [";

    for (const Pack &pack : packs)
    {
        const std::string file = std::string(pack.pId) + "-0123456789abcdef.zip";
        writeZipFile(assetRoot / "packs" / file, pack.entries);
        index += std::string(&pack == &packs.front() ? "" : ", ") + "{\"id\": \"" + pack.pId + "\", \"package\": \""
            + pack.pPackage + "\", \"mount\": \"" + pack.pMount + "\", \"file\": \"" + file + "\", \"size\": "
            + std::to_string(std::filesystem::file_size(assetRoot / "packs" / file))
            + ", \"content_id\": \"c\", \"sha256\": \"s\"}";
    }

    writeTextFile(assetRoot / "index.json", index + "]}");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm6"));

        const std::optional<std::string> uiText = assetFileSystem.readTextFile("Data/ui/layout.yml");
        REQUIRE(uiText.has_value());
        CHECK_EQ(*uiText, "engine-ui");

        const std::optional<std::string> devStyleTableText =
            assetFileSystem.readTextFile("engine/data_tables/map_stats.txt");
        REQUIRE(devStyleTableText.has_value());
        CHECK_EQ(*devStyleTableText, "engine-map-stats");

        CHECK(assetFileSystem.readTextFile("worlds/mm6/maps/shared.odm")
            == std::optional<std::string>("active-map"));
        CHECK(assetFileSystem.readTextFile("worlds/mm8/textures/shared.bmp")
            == std::optional<std::string>("inactive-texture"));

        const std::optional<std::string> sharedMapText = assetFileSystem.readTextFile("Data/games/shared.odm");
        REQUIRE(sharedMapText.has_value());
        CHECK_EQ(*sharedMapText, "active-map");

        const std::optional<std::string> inactiveMapText = assetFileSystem.readTextFile("Data/games/out01.odm");
        REQUIRE(inactiveMapText.has_value());
        CHECK_EQ(*inactiveMapText, "inactive-map");

        const std::optional<std::string> sharedTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/shared.bmp");
        REQUIRE(sharedTextureText.has_value());
        CHECK_EQ(*sharedTextureText, "active-texture");

        std::unique_ptr<OpenYAMM::Engine::AssetReadStream> pVideoStream =
            assetFileSystem.openReadStream("Videos/Houses/sample.ogv");
        REQUIRE(pVideoStream != nullptr);
        REQUIRE(pVideoStream->seek(4));
        std::array<char, 3> streamedBytes = {};
        CHECK_EQ(pVideoStream->read(streamedBytes.data(), streamedBytes.size()), 3);
        CHECK_EQ(std::string(streamedBytes.data(), streamedBytes.size()), "456");
        pVideoStream.reset();

        CHECK_FALSE(assetFileSystem.resolvePhysicalPath("Data/games/shared.odm").has_value());

        CHECK(assetFileSystem.readTextFile("worlds/mm6/maps/shared.lighting")
            == std::optional<std::string>("active-lighting"));
        CHECK(assetFileSystem.readTextFile("engine/data_tables/english/Global.txt")
            == std::optional<std::string>("engine-global"));
        const std::vector<std::string> maps = assetFileSystem.enumerate("worlds/mm6/maps");
        CHECK(std::find(maps.begin(), maps.end(), "shared.odm") != maps.end());
        CHECK(std::find(maps.begin(), maps.end(), "shared.lighting") != maps.end());

        // The rulesets' pack lists under engine/rulesets/, as the development tree does.
        CHECK(assetFileSystem.readTextFile("engine/rulesets/maw/ruleset.yml") == std::optional<std::string>("id: maw"));
        const std::vector<std::string> rulesets = assetFileSystem.enumerate("engine/rulesets");
        CHECK(std::find(rulesets.begin(), rulesets.end(), "maw") != rulesets.end());

        REQUIRE(assetFileSystem.switchActiveWorld("mm8"));

        const std::optional<std::string> switchedTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/shared.bmp");
        REQUIRE(switchedTextureText.has_value());
        CHECK_EQ(*switchedTextureText, "inactive-texture");
    }

    // A missing or truncated pack makes the installation unusable instead of silently losing content.
    std::filesystem::resize_file(assetRoot / "packs" / "mm8.maps.1-0123456789abcdef.zip", 10);
    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        CHECK_FALSE(assetFileSystem.initialize(temporaryRoot, assetRoot, OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem mounts mods in front of the packs only when mods/ holds files")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets";
    const std::filesystem::path modsRoot = temporaryRoot / "mods";
    writeZipFile(assetRoot / "packs/engine.core.zip", {
        {"data_tables/house_data.txt", "game-houses"},
        {"data_tables/spells.txt", "game-spells"}
    });
    writeZipFile(assetRoot / "packs/mm6.core.zip", {{"textures/shared.bmp", "game-texture"}});
    writeZipFile(assetRoot / "packs/mm8.core.zip", {{"textures/shared.bmp", "game-mm8-texture"}});
    writeCorePackIndex(assetRoot, {"engine", "mm6", "mm8"});
    const AssetScaleProfile profile = createUniformAssetScaleProfile(AssetScaleTier::X1);
    InstalledContentOptions options;
    options.modsRoot = modsRoot;

    const auto searchPaths = [&](const InstalledContentOptions &contentOptions)
    {
        AssetFileSystem fs;
        REQUIRE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6", contentOptions));
        CHECK(fs.readTextFile("engine/data_tables/house_data.txt") == std::optional<std::string>("game-houses"));
        return fs.getSearchPaths();
    };

    // No mods folder, or one without files, mounts exactly what no options mount.
    const std::vector<std::string> gameOnly = searchPaths({});
    CHECK(searchPaths(options) == gameOnly);
    std::filesystem::create_directories(modsRoot / "engine" / "data_tables");
    std::filesystem::create_directories(modsRoot / "worlds" / "mm6");
    CHECK(searchPaths(options) == gameOnly);

    writeTextFile(modsRoot / "engine" / "data_tables" / "house_data.txt", "mod-houses");
    writeTextFile(modsRoot / "engine" / "data_tables" / "new_table.txt", "mod-new");
    writeTextFile(modsRoot / "worlds" / "mm6" / "textures" / "shared.bmp", "mod-texture");
    // Neither a package root nor a world folder: ignored.
    writeTextFile(modsRoot / "data_tables" / "spells.txt", "misplaced");
    writeTextFile(modsRoot / "readme.txt", "notes");
    {
        AssetFileSystem fs;
        REQUIRE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6", options));
        CHECK(fs.readTextFile("engine/data_tables/house_data.txt") == std::optional<std::string>("mod-houses"));
        CHECK(fs.readTextFile("data_tables/house_data.txt") == std::optional<std::string>("mod-houses"));
        CHECK(fs.readTextFile("engine/data_tables/new_table.txt") == std::optional<std::string>("mod-new"));
        CHECK(fs.readTextFile("engine/data_tables/spells.txt") == std::optional<std::string>("game-spells"));
        CHECK(fs.readTextFile("Data/bitmaps/shared.bmp") == std::optional<std::string>("mod-texture"));
        CHECK(fs.readTextFile("worlds/mm8/textures/shared.bmp")
            == std::optional<std::string>("game-mm8-texture"));
        CHECK_FALSE(fs.exists("readme.txt"));

        // A world switch mounts again with the same mods.
        REQUIRE(fs.switchActiveWorld("mm8"));
        CHECK(fs.readTextFile("engine/data_tables/house_data.txt") == std::optional<std::string>("mod-houses"));
        CHECK(fs.readTextFile("Data/bitmaps/shared.bmp") == std::optional<std::string>("game-mm8-texture"));
    }

    // Only a release's packs take mods, not a development tree.
    writeTextFile(temporaryRoot / "assets_dev" / "engine" / "data_tables" / "house_data.txt", "dev-houses");
    writeTextFile(temporaryRoot / "assets_dev" / "engine" / "textures" / "dev.bmp", "dev-texture");
    writeTextFile(temporaryRoot / "assets_dev" / "engine" / "icons" / "dev.bmp", "dev-icon");
    {
        AssetFileSystem fs;
        REQUIRE(fs.initialize(temporaryRoot, temporaryRoot / "assets_dev", AssetScaleTier::X1, profile, "mm6",
                              options));
        CHECK(fs.readTextFile("engine/data_tables/house_data.txt") == std::optional<std::string>("dev-houses"));
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem reads an extra development mount in front of a development root")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    const std::filesystem::path extraRoot = temporaryRoot / "build_mount";
    writeTextFile(assetRoot / "engine" / "data_tables" / "map_stats.txt", "game-stats");
    writeTextFile(assetRoot / "engine" / "data_tables" / "spells.txt", "game-spells");
    writeTextFile(assetRoot / "worlds" / "mm6" / "maps" / "d01.blv", "game-map");
    writeTextFile(assetRoot / "worlds" / "mm6" / "events" / "maps" / "d01.lua", "game-script");
    writeTextFile(assetRoot / "worlds" / "mm8" / "maps" / "d05.blv", "game-mm8-map");
    writeTextFile(extraRoot / "engine" / "data_tables" / "map_stats.txt", "build-stats");
    writeTextFile(extraRoot / "worlds" / "mm6" / "maps" / "new01.blv", "build-map");
    writeTextFile(extraRoot / "worlds" / "mm6" / "events" / "maps" / "d01_rewire.lua", "build-overlay");
    writeTextFile(extraRoot / "worlds" / "mm8" / "maps" / "d05.blv", "build-mm8-map");
    const AssetScaleProfile profile = createUniformAssetScaleProfile(AssetScaleTier::X1);
    InstalledContentOptions options;
    options.extraMountRoot = extraRoot;

    {
        AssetFileSystem fs;
        REQUIRE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6", options));
        CHECK(fs.readTextFile("engine/data_tables/map_stats.txt") == std::optional<std::string>("build-stats"));
        CHECK(fs.readTextFile("data_tables/map_stats.txt") == std::optional<std::string>("build-stats"));
        CHECK(fs.readTextFile("engine/data_tables/spells.txt") == std::optional<std::string>("game-spells"));
        CHECK(fs.readTextFile("Data/games/new01.blv") == std::optional<std::string>("build-map"));
        CHECK(fs.readTextFile("Data/games/d01.blv") == std::optional<std::string>("game-map"));
        CHECK(fs.readTextFile("worlds/mm6/events/maps/d01_rewire.lua") == std::optional<std::string>("build-overlay"));
        CHECK(fs.readTextFile("Data/games/d05.blv") == std::optional<std::string>("build-mm8-map"));
        const std::vector<std::string> scripts = fs.enumerate("events/maps");
        CHECK(std::find(scripts.begin(), scripts.end(), "d01_rewire.lua") != scripts.end());
        CHECK(std::find(scripts.begin(), scripts.end(), "d01.lua") != scripts.end());

        // A world switch mounts again with the same folder.
        REQUIRE(fs.switchActiveWorld("mm8"));
        CHECK(fs.readTextFile("Data/games/d05.blv") == std::optional<std::string>("build-mm8-map"));
        CHECK(fs.readTextFile("Data/games/new01.blv") == std::optional<std::string>("build-map"));
    }

    // Without the option nothing of the folder is read.
    {
        AssetFileSystem fs;
        REQUIRE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6", {}));
        CHECK(fs.readTextFile("engine/data_tables/map_stats.txt") == std::optional<std::string>("game-stats"));
        CHECK_FALSE(fs.exists("Data/games/new01.blv"));
    }

    // A folder that does not exist is an error, not silence.
    options.extraMountRoot = temporaryRoot / "missing";
    AssetFileSystem missing;
    CHECK_FALSE(missing.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6", options));
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem mounts a language pack's fonts, sounds, videos and icons over the game's, and nothing else")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const AssetScaleProfile profile = createUniformAssetScaleProfile(AssetScaleTier::X1);

    const auto writePack = [](const std::filesystem::path &pack)
    {
        writeTextFile(pack / "language.yml", "name: Test\n");
        writeTextFile(pack / "engine" / "fonts" / "truetype" / "lucida.yml", "pack-font");
        writeTextFile(pack / "engine" / "audio" / "zm1.wav", "pack-sound");
        writeTextFile(pack / "worlds" / "mm7" / "audio" / "w7.wav", "pack-world-sound");
        writeTextFile(pack / "worlds" / "mm7" / "videos" / "Cutscenes" / "7intro.ogv", "pack-video");
        // Images with text in them (OY-579): the Arcomage card sheet.
        writeTextFile(pack / "engine" / "icons_x2" / "sprites.pcx", "pack-cards");
        // Text goes through translation files: a pack's data table never replaces the game's.
        writeTextFile(pack / "engine" / "data_tables" / "items.txt", "pack-items");
    };

    // A development root: the pack in assets_dev/languages.
    const std::filesystem::path developmentRoot = temporaryRoot / "assets_dev";
    writeTextFile(developmentRoot / "engine" / "fonts" / "truetype" / "lucida.yml", "game-font");
    writeTextFile(developmentRoot / "engine" / "audio" / "zm1.wav", "game-sound");
    writeTextFile(developmentRoot / "engine" / "data_tables" / "items.txt", "game-items");
    writeTextFile(developmentRoot / "worlds" / "mm7" / "audio" / "w7.wav", "game-world-sound");
    writeTextFile(developmentRoot / "worlds" / "mm7" / "videos" / "Cutscenes" / "7intro.ogv", "game-video");
    writeTextFile(developmentRoot / "engine" / "icons_x2" / "sprites.pcx", "game-cards");
    writePack(developmentRoot / "languages" / "ts");

    InstalledContentOptions english;
    InstalledContentOptions language;
    language.languageId = "ts";
    const auto check = [&](const std::filesystem::path &assetRoot, const InstalledContentOptions &options,
                           const std::string &prefix)
    {
        AssetFileSystem fs;
        REQUIRE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm7", options));
        CHECK(fs.readTextFile("fonts/truetype/lucida.yml") == std::optional<std::string>(prefix + "-font"));
        CHECK(fs.readTextFile("Data/EnglishD/zm1.wav") == std::optional<std::string>(prefix + "-sound"));
        CHECK(fs.readTextFile("Data/EnglishD/w7.wav") == std::optional<std::string>(prefix + "-world-sound"));
        CHECK(fs.readTextFile("Videos/Cutscenes/7intro.ogv") == std::optional<std::string>(prefix + "-video"));
        CHECK(fs.readTextFile("data_tables/items.txt") == std::optional<std::string>("game-items"));
        CHECK(fs.readTextFile("engine/icons_x2/sprites.pcx") == std::optional<std::string>(prefix + "-cards"));
        CHECK(fs.exists("languages/ts/language.yml"));
        // A world switch mounts the pack again.
        REQUIRE(fs.switchActiveWorld("mm7"));
        CHECK(fs.readTextFile("Data/EnglishD/zm1.wav") == std::optional<std::string>(prefix + "-sound"));
    };
    check(developmentRoot, english, "game");
    check(developmentRoot, language, "pack");

    // A release: the packs, with the player's own pack in <user data>/languages.
    const std::filesystem::path releaseRoot = temporaryRoot / "assets";
    writeZipFile(releaseRoot / "packs/engine.core.zip", {
        {"fonts/truetype/lucida.yml", "game-font"},
        {"audio/zm1.wav", "game-sound"},
        {"data_tables/items.txt", "game-items"},
        {"icons_x2/sprites.pcx", "game-cards"}
    });
    writeZipFile(releaseRoot / "packs/mm7.core.zip", {
        {"audio/w7.wav", "game-world-sound"},
        {"videos/Cutscenes/7intro.ogv", "game-video"}
    });
    writeCorePackIndex(releaseRoot, {"engine", "mm7"});
    writePack(temporaryRoot / "languages" / "ts");
    english.userLanguagesRoot = temporaryRoot / "languages";
    language.userLanguagesRoot = temporaryRoot / "languages";
    check(releaseRoot, english, "game");
    check(releaseRoot, language, "pack");

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("A language's translation is found for a table cell with spaces or line breaks around its text")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const AssetScaleProfile profile = createUniformAssetScaleProfile(AssetScaleTier::X1);
    const std::filesystem::path developmentRoot = temporaryRoot / "assets_dev";
    writeTextFile(developmentRoot / "engine" / "data_tables" / "items.txt", "game-items");
    writeTextFile(developmentRoot / "languages" / "ts" / "language.yml", "name: Test\n");
    writeTextFile(developmentRoot / "languages" / "ts" / "text" / "engine.po",
                  "msgid \"Elvis\"\nmsgstr \"Elvisz\"\n\n"
                  "msgid \"Hello.\\nGoodbye.\"\nmsgstr \"Ahoj.\\nNashle.\"\n");

    InstalledContentOptions options;
    options.languageId = "ts";
    AssetFileSystem fs;
    REQUIRE(fs.initialize(temporaryRoot, developmentRoot, AssetScaleTier::X1, profile, "mm7", options));
    REQUIRE(activateLanguage(fs, "ts"));
    CHECK(localize("Elvis") == "Elvisz");
    CHECK(localize("Elvis ") == "Elvisz ");
    CHECK(localize("Hello.\nGoodbye.\n") == "Ahoj.\nNashle.\n");
    CHECK(localizeKnown("  Elvis") == "  Elvisz");
    CHECK(localize(" Elvis Presley ") == " Elvis Presley ");
    CHECK(localize("   ") == "   ");
    REQUIRE(activateLanguage(fs, EnglishLanguageId));

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("A composed boss name takes the affix's own translation and the language's word order")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const AssetScaleProfile profile = createUniformAssetScaleProfile(AssetScaleTier::X1);
    const std::filesystem::path developmentRoot = temporaryRoot / "assets_dev";
    writeTextFile(developmentRoot / "engine" / "data_tables" / "items.txt", "game-items");
    writeTextFile(developmentRoot / "languages" / "ts" / "language.yml", "name: Test\n");
    // "Swift" alone is an item suffix ("of Swiftness"); the affix has its own entry.
    writeTextFile(developmentRoot / "languages" / "ts" / "text" / "engine.po",
                  "msgid \"Swift\"\nmsgstr \"of Speed\"\n\n"
                  "msgctxt \"monster affix\"\nmsgid \"Swift\"\nmsgstr \"speed\"\n\n"
                  "msgid \"{affix} {monster}\"\nmsgstr \"{monster} ({affix})\"\n\n"
                  "msgid \"Resurrected {monster}\"\nmsgstr \"{monster} from the dead\"\n\n"
                  "msgid \"Goblin\"\nmsgstr \"Gobline\"\n");

    InstalledContentOptions options;
    options.languageId = "ts";
    AssetFileSystem fs;
    REQUIRE(fs.initialize(temporaryRoot, developmentRoot, AssetScaleTier::X1, profile, "mm7", options));
    REQUIRE(activateLanguage(fs, "ts"));
    CHECK(OpenYAMM::Game::localizedActorName("Swift Goblin") == "Gobline (speed)");
    CHECK(OpenYAMM::Game::localizedActorName("Resurrected Swift Goblin") == "Gobline (speed) from the dead");
    REQUIRE(activateLanguage(fs, EnglishLanguageId));
    CHECK(OpenYAMM::Game::localizedActorName("Swift Goblin") == "Swift Goblin");

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem mounts a release's optional language packs only for their language, when installed")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets";
    const AssetScaleProfile profile = createUniformAssetScaleProfile(AssetScaleTier::X1);
    struct Pack
    {
        std::string id;
        std::string package;
        std::string mount;
        std::string language;
        std::vector<std::pair<std::string, std::string>> files;
    };
    const std::vector<Pack> packs = {
        {"engine.core", "engine", "/engine", "",
         {{"fonts/truetype/lucida.yml", "game-font"}, {"audio/zm1.wav", "game-sound"}}},
        // Every language's text is always installed.
        {"engine.languages", "engine", "/engine/languages", "", {{"ts/language.yml", "name: Test\n"},
                                                                 {"tz/language.yml", "name: Other\n"}}},
        {"mm7.core", "mm7", "/worlds/mm7", "",
         {{"videos/Cutscenes/7intro.ogv", "game-video"}, {"world.yml", "id: mm7\n"}}},
        {"mm8.core", "mm8", "/worlds/mm8", "",
         {{"videos/Cutscenes/8intro.ogv", "game-video"}, {"world.yml", "id: mm8\n"}}},
        {"lang-ts.engine.fonts", "engine", "/engine/fonts", "ts", {{"truetype/lucida.yml", "ts-font"}}},
        {"lang-ts.engine.audio", "engine", "/engine/audio", "ts", {{"zm1.wav", "ts-sound"}}},
        {"lang-ts.mm7.videos", "mm7", "/worlds/mm7/videos", "ts", {{"Cutscenes/7intro.ogv", "ts-video"}}},
        // Another world's pack last: it must not put that world in front of the active one (2.0 read MM8's
        // world.yml in an MM7 game once Russian was downloaded).
        {"lang-ts.mm8.videos", "mm8", "/worlds/mm8/videos", "ts", {{"Cutscenes/8intro.ogv", "ts-video"}}},
        {"lang-tz.engine.audio", "engine", "/engine/audio", "tz", {{"zm1.wav", "tz-sound"}}},
    };
    std::string index = "{\"schema\": 1, \"release\": \"test\", \"build\": \"test\", \"profile\": \"desktop\", "
                        "\"content_format\": 1, \"store\": \"packs\", \"packs\": [";

    for (const Pack &pack : packs)
    {
        // The language tz was never downloaded: its pack is in the index only.
        if (pack.language != "tz")
        {
            writeZipFile(assetRoot / "packs" / (pack.id + ".zip"), pack.files);
        }

        const uint64_t size =
            pack.language == "tz" ? 1234 : std::filesystem::file_size(assetRoot / "packs" / (pack.id + ".zip"));
        index += std::string(&pack == packs.data() ? "" : ", ") + "{\"id\": \"" + pack.id + "\", \"package\": \""
            + pack.package + "\", \"mount\": \"" + pack.mount + "\", \"file\": \"" + pack.id + ".zip\", \"size\": "
            + std::to_string(size) + ", \"content_id\": \"c" + pack.id + "\", \"sha256\": \"s\""
            + (pack.language.empty() ? "" : ", \"language\": \"" + pack.language + "\"") + "}";
    }

    writeTextFile(assetRoot / "index.json", index + "]}");
    std::string error;
    const std::optional<AssetPackIndex> parsed = loadAssetPackIndex(assetRoot / "index.json", error);
    REQUIRE_MESSAGE(parsed.has_value(), error);
    CHECK(assetPackLanguages(*parsed) == std::vector<std::string>{"ts", "tz"});
    CHECK_EQ(missingLanguagePackBytes(*parsed, assetRoot / "packs", "ts"), 0u);
    CHECK_EQ(missingLanguagePackBytes(*parsed, assetRoot / "packs", "tz"), 1234u);
    // A language's packs are optional: a missing one leaves the content usable.
    CHECK(validateAssetPackFiles(*parsed, assetRoot / "packs", error));

    const auto check = [&](const std::string &languageId, const std::string &prefix)
    {
        InstalledContentOptions options;
        options.languageId = languageId;
        AssetFileSystem fs;
        REQUIRE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm7", options));
        CHECK(fs.readTextFile("fonts/truetype/lucida.yml") == std::optional<std::string>(prefix + "-font"));
        CHECK(fs.readTextFile("Data/EnglishD/zm1.wav") == std::optional<std::string>(prefix + "-sound"));
        CHECK(fs.readTextFile("Videos/Cutscenes/7intro.ogv") == std::optional<std::string>(prefix + "-video"));
        CHECK(fs.readTextFile("worlds/mm8/videos/Cutscenes/8intro.ogv")
              == std::optional<std::string>(prefix + "-video"));
        // Unqualified requests still search the active world first, then the engine, then the other worlds.
        CHECK(fs.readTextFile("world.yml") == std::optional<std::string>("id: mm7\n"));
        CHECK(fs.exists("languages/ts/language.yml"));
        CHECK(fs.exists("languages/tz/language.yml"));
        CHECK(fs.languagePacksMissing() == (languageId == "tz"));
    };
    check("", "game");
    check("ts", "ts");
    // Chosen but not downloaded yet: the game's own files.
    check("tz", "game");

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem mounts changed packs only when they are kept on purpose")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets";
    writeZipFile(assetRoot / "packs/engine.core.zip", {{"data_tables/house_data.txt", "game-houses"}});
    writeCorePackIndex(assetRoot, {"engine"});
    // The player rebuilt the pack with an edited table, so it no longer has the size of the index.
    writeZipFile(assetRoot / "packs/engine.core.zip", {{"data_tables/house_data.txt", "edited houses, longer"}});
    const AssetScaleProfile profile = createUniformAssetScaleProfile(AssetScaleTier::X1);
    InstalledContentOptions kept;
    kept.acceptModifiedPacks = true;

    {
        AssetFileSystem fs;
        CHECK_FALSE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6", {}));
    }

    {
        AssetFileSystem fs;
        REQUIRE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6", kept));
        CHECK(fs.readTextFile("engine/data_tables/house_data.txt")
            == std::optional<std::string>("edited houses, longer"));
    }

    // A missing pack still makes the content unusable.
    std::filesystem::remove(assetRoot / "packs/engine.core.zip");
    {
        AssetFileSystem fs;
        CHECK_FALSE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6", kept));
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

TEST_CASE("AssetFileSystem merges inactive world video roots")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "worlds" / "mm6" / "videos" / "Houses" / "temprich.ogv", "mm6-house-video");
    writeTextFile(assetRoot / "worlds" / "mm7" / "videos" / "Houses" / "elf weapon smith.ogv", "mm7-house-video");
    writeTextFile(assetRoot / "worlds" / "mm8" / "videos" / "Houses" / "ltemple.ogv", "mm8-house-video");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        const std::optional<std::string> mm6HouseVideoText =
            assetFileSystem.readTextFile("Videos/Houses/temprich.ogv");
        REQUIRE(mm6HouseVideoText.has_value());
        CHECK_EQ(*mm6HouseVideoText, "mm6-house-video");

        const std::optional<std::string> mm7HouseVideoText =
            assetFileSystem.readTextFile("Videos/Houses/elf weapon smith.ogv");
        REQUIRE(mm7HouseVideoText.has_value());
        CHECK_EQ(*mm7HouseVideoText, "mm7-house-video");

        const std::optional<std::string> mm8HouseVideoText =
            assetFileSystem.readTextFile("Videos/Houses/ltemple.ogv");
        REQUIRE(mm8HouseVideoText.has_value());
        CHECK_EQ(*mm8HouseVideoText, "mm8-house-video");

        const std::optional<std::filesystem::path> mm6PhysicalPath =
            assetFileSystem.resolvePhysicalPath("Videos/Houses/temprich.ogv");
        REQUIRE(mm6PhysicalPath.has_value());
        CHECK(mm6PhysicalPath->generic_string().ends_with("assets_dev/worlds/mm6/videos/Houses/temprich.ogv"));
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem merges inactive world music roots")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "worlds" / "mm6" / "music" / "37.mp3", "mm6-music");
    writeTextFile(assetRoot / "worlds" / "mm7" / "music" / "19.mp3", "mm7-music");
    writeTextFile(assetRoot / "worlds" / "mm8" / "music" / "5.mp3", "mm8-music");
    writeTextFile(assetRoot / "worlds" / "mm9" / "music" / "90007.mp3", "mm9-music");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm8"));

        const std::optional<std::string> mm6MusicText =
            assetFileSystem.readTextFile("Music/37.mp3");
        REQUIRE(mm6MusicText.has_value());
        CHECK_EQ(*mm6MusicText, "mm6-music");

        const std::optional<std::string> mm7MusicText =
            assetFileSystem.readTextFile("Music/19.mp3");
        REQUIRE(mm7MusicText.has_value());
        CHECK_EQ(*mm7MusicText, "mm7-music");

        const std::optional<std::string> mm8MusicText =
            assetFileSystem.readTextFile("Music/5.mp3");
        REQUIRE(mm8MusicText.has_value());
        CHECK_EQ(*mm8MusicText, "mm8-music");

        const std::optional<std::string> mm9MusicText =
            assetFileSystem.readTextFile("Music/90007.mp3");
        REQUIRE(mm9MusicText.has_value());
        CHECK_EQ(*mm9MusicText, "mm9-music");

        const std::optional<std::filesystem::path> mm6PhysicalPath =
            assetFileSystem.resolvePhysicalPath("Music/37.mp3");
        REQUIRE(mm6PhysicalPath.has_value());
        CHECK(mm6PhysicalPath->generic_string().ends_with("assets_dev/worlds/mm6/music/37.mp3"));

        const std::optional<std::filesystem::path> mm9PhysicalPath =
            assetFileSystem.resolvePhysicalPath("Music/90007.mp3");
        REQUIRE(mm9PhysicalPath.has_value());
        CHECK(mm9PhysicalPath->generic_string().ends_with("assets_dev/worlds/mm9/music/90007.mp3"));
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem merges inactive world map runtime roots")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "worlds" / "mm6" / "maps" / "shared.odm", "active-map");
    writeTextFile(assetRoot / "worlds" / "mm6" / "events" / "maps" / "shared.lua", "active-script");
    writeTextFile(assetRoot / "worlds" / "mm6" / "textures" / "shared.bmp", "active-texture");
    writeTextFile(assetRoot / "worlds" / "mm6" / "sprites" / "shared.bmp", "active-sprite");
    writeTextFile(assetRoot / "worlds" / "mm6" / "_legacy" / "map_delta" / "shared.odm", "active-delta");
    writeTextFile(assetRoot / "worlds" / "mm8" / "maps" / "out01.odm", "inactive-map");
    writeTextFile(assetRoot / "worlds" / "mm8" / "maps" / "shared.odm", "inactive-map");
    writeTextFile(assetRoot / "worlds" / "mm8" / "events" / "maps" / "out01.lua", "inactive-script");
    writeTextFile(assetRoot / "worlds" / "mm8" / "events" / "maps" / "shared.lua", "inactive-script");
    writeTextFile(assetRoot / "worlds" / "mm8" / "textures" / "sky01.bmp", "inactive-texture");
    writeTextFile(assetRoot / "worlds" / "mm8" / "textures" / "shared.bmp", "inactive-texture");
    writeTextFile(assetRoot / "worlds" / "mm8" / "sprites" / "m390sa0.bmp", "inactive-sprite");
    writeTextFile(assetRoot / "worlds" / "mm8" / "sprites" / "shared.bmp", "inactive-sprite");
    writeTextFile(assetRoot / "worlds" / "mm8" / "_legacy" / "map_delta" / "out01.odm", "inactive-delta");
    writeTextFile(assetRoot / "worlds" / "mm8" / "_legacy" / "map_delta" / "shared.odm", "inactive-delta");

    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            "mm6"));

        const std::optional<std::string> inactiveMapText =
            assetFileSystem.readTextFile("Data/games/out01.odm");
        REQUIRE(inactiveMapText.has_value());
        CHECK_EQ(*inactiveMapText, "inactive-map");

        const std::optional<std::string> inactiveScriptText =
            assetFileSystem.readTextFile("Data/scripts/maps/out01.lua");
        REQUIRE(inactiveScriptText.has_value());
        CHECK_EQ(*inactiveScriptText, "inactive-script");

        const std::optional<std::string> inactiveTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/sky01.bmp");
        REQUIRE(inactiveTextureText.has_value());
        CHECK_EQ(*inactiveTextureText, "inactive-texture");

        const std::optional<std::string> inactiveSpriteText =
            assetFileSystem.readTextFile("Data/sprites/m390sa0.bmp");
        REQUIRE(inactiveSpriteText.has_value());
        CHECK_EQ(*inactiveSpriteText, "inactive-sprite");

        const std::optional<std::string> inactiveDeltaText =
            assetFileSystem.readTextFile("_legacy/map_delta/out01.odm");
        REQUIRE(inactiveDeltaText.has_value());
        CHECK_EQ(*inactiveDeltaText, "inactive-delta");

        const std::optional<std::string> sharedMapText =
            assetFileSystem.readTextFile("Data/games/shared.odm");
        REQUIRE(sharedMapText.has_value());
        CHECK_EQ(*sharedMapText, "active-map");

        const std::vector<std::string> mapEntries = assetFileSystem.enumerate("Data/games");
        CHECK(containsEntry(mapEntries, "out01.odm"));
        CHECK(containsEntry(mapEntries, "shared.odm"));

        const std::optional<std::filesystem::path> inactiveMapPhysicalPath =
            assetFileSystem.resolvePhysicalPath("Data/games/out01.odm");
        REQUIRE(inactiveMapPhysicalPath.has_value());
        CHECK(inactiveMapPhysicalPath->generic_string().ends_with("assets_dev/worlds/mm8/maps/out01.odm"));

        const std::optional<std::string> sharedTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/shared.bmp");
        REQUIRE(sharedTextureText.has_value());
        CHECK_EQ(*sharedTextureText, "active-texture");

        const std::optional<std::string> sharedSpriteText =
            assetFileSystem.readTextFile("Data/sprites/shared.bmp");
        REQUIRE(sharedSpriteText.has_value());
        CHECK_EQ(*sharedSpriteText, "active-sprite");

        REQUIRE(assetFileSystem.switchActiveWorld("mm8"));
        CHECK_EQ(assetFileSystem.getActiveWorldId(), "mm8");

        const std::optional<std::string> switchedSharedTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/shared.bmp");
        REQUIRE(switchedSharedTextureText.has_value());
        CHECK_EQ(*switchedSharedTextureText, "inactive-texture");

        const std::optional<std::filesystem::path> switchedSharedTexturePhysicalPath =
            assetFileSystem.resolvePhysicalPath("Data/bitmaps/shared.bmp");
        REQUIRE(switchedSharedTexturePhysicalPath.has_value());
        CHECK(switchedSharedTexturePhysicalPath->generic_string().ends_with("assets_dev/worlds/mm8/textures/shared.bmp"));

        const std::optional<std::string> switchedSharedSpriteText =
            assetFileSystem.readTextFile("Data/sprites/shared.bmp");
        REQUIRE(switchedSharedSpriteText.has_value());
        CHECK_EQ(*switchedSharedSpriteText, "inactive-sprite");
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

TEST_CASE("AssetFileSystem applies asset scale by package category")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "textures" / "wall.bmp", "base-wall");
    writeTextFile(assetRoot / "engine" / "textures_x4" / "wall.bmp", "scaled-wall");
    writeTextFile(assetRoot / "engine" / "sprites" / "tree.bmp", "base-tree");

    {
        OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
            OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
        assetScaleProfile.textures = OpenYAMM::Engine::AssetScaleTier::X4;

        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            assetScaleProfile,
            "mm8"));

        const std::optional<std::string> textureText =
            assetFileSystem.readTextFile("Data/bitmaps/wall.bmp");
        REQUIRE(textureText.has_value());
        CHECK_EQ(*textureText, "scaled-wall");

        const std::optional<std::string> spriteText =
            assetFileSystem.readTextFile("Data/sprites/tree.bmp");
        REQUIRE(spriteText.has_value());
        CHECK_EQ(*spriteText, "base-tree");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem requires the scaled directory of a scaled required category")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "textures" / "water.bmp", "base-water");
    writeTextFile(assetRoot / "engine" / "textures_x2" / "water.bmp", "scaled-geometry-water");

    OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
        OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
    assetScaleProfile.textures = OpenYAMM::Engine::AssetScaleTier::X4;

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    CHECK_FALSE(assetFileSystem.initialize(
        temporaryRoot,
        assetRoot,
        OpenYAMM::Engine::AssetScaleTier::X1,
        assetScaleProfile,
        "mm8"));

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem falls back to base files when a scaled texture file is absent")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "textures" / "wall.bmp", "base-wall");
    writeTextFile(assetRoot / "engine" / "textures" / "water.bmp", "base-water");
    writeTextFile(assetRoot / "engine" / "textures" / "pal123.act", "base-palette");
    writeTextFile(assetRoot / "engine" / "textures_x4" / "wall.bmp", "scaled-wall");

    {
        OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
            OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
        assetScaleProfile.textures = OpenYAMM::Engine::AssetScaleTier::X4;

        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            assetScaleProfile,
            "mm8"));

        const std::optional<std::string> scaledTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/wall.bmp");
        REQUIRE(scaledTextureText.has_value());
        CHECK_EQ(*scaledTextureText, "scaled-wall");

        const std::optional<std::string> fallbackTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/water.bmp");
        REQUIRE(fallbackTextureText.has_value());
        CHECK_EQ(*fallbackTextureText, "base-water");

        const std::optional<std::string> fallbackPaletteText =
            assetFileSystem.readTextFile("Data/bitmaps/pal123.act");
        REQUIRE(fallbackPaletteText.has_value());
        CHECK_EQ(*fallbackPaletteText, "base-palette");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem resolves sky textures independently of geometry texture scale")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "textures" / "sky01.bmp", "base-sky");
    writeTextFile(assetRoot / "engine" / "textures_x4" / "sky01.bmp", "scaled-sky");
    writeTextFile(assetRoot / "engine" / "textures_x4" / "wall.bmp", "scaled-wall");

    {
        OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
            OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
        assetScaleProfile.textures = OpenYAMM::Engine::AssetScaleTier::X4;
        assetScaleProfile.sky = OpenYAMM::Engine::AssetScaleTier::X1;

        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            assetScaleProfile,
            "mm8"));

        const std::optional<std::string> bmodelTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/wall.bmp");
        REQUIRE(bmodelTextureText.has_value());
        CHECK_EQ(*bmodelTextureText, "scaled-wall");

        const std::optional<std::string> baseSkyText =
            assetFileSystem.readTextFile("sky_textures/sky01.bmp");
        REQUIRE(baseSkyText.has_value());
        CHECK_EQ(*baseSkyText, "base-sky");
    }

    {
        OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
            OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
        assetScaleProfile.sky = OpenYAMM::Engine::AssetScaleTier::X4;

        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            assetScaleProfile,
            "mm8"));

        const std::optional<std::string> scaledSkyText =
            assetFileSystem.readTextFile("sky_textures/sky01.bmp");
        REQUIRE(scaledSkyText.has_value());
        CHECK_EQ(*scaledSkyText, "scaled-sky");
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

TEST_CASE("AssetFileSystem restored icons resolve archive tiers and original fallback")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets";
    writeZipFile(assetRoot / "packs/engine.core.zip", {
        {"icons/kept.bmp", "original"},
        {"icons/mixed.bmp", "original"},
        {"icons_x2/mixed.bmp", "restored"}
    });
    writeCorePackIndex(assetRoot, {"engine"});
    {
        AssetFileSystem fs;
        AssetScaleProfile profile;
        profile.preferRestoredIcons = true;
        REQUIRE(fs.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, profile, "mm6"));
        for (const std::string &prefix : {"Data/icons/", "engine/icons/"})
        {
            const std::optional<std::string> restored = fs.resolveExistingFilePath(prefix + "mixed.bmp");
            const std::optional<std::string> original = fs.resolveExistingFilePath(prefix + "kept.bmp");
            REQUIRE(restored);
            REQUIRE(original);
            CHECK(assetScaleTierFromResolvedPath(*restored) == AssetScaleTier::X2);
            CHECK(assetScaleTierFromResolvedPath(*original) == AssetScaleTier::X1);
            CHECK(fs.readTextFile(*restored) == std::optional<std::string>("restored"));
            CHECK(fs.readTextFile(*original) == std::optional<std::string>("original"));
        }
        CHECK_FALSE(fs.resolveExistingFilePath("Data/icons/missing.bmp"));
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem authoritative icon packages isolate restored and retained native roots")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assets = temporaryRoot / "assets";
    writeZipFile(assets / "packs/engine.core.zip", {
        {"icon_packages.txt", "engine x2\nworlds/mm6 x2\nworlds/mm7 x2\nworlds/mm9 x1\n"},
        {"icons/retired.bmp", "must not load"},
        {"icons/same.png", "native"},
        {"icons_x2/same.bmp", "restored"}
    });
    writeZipFile(assets / "packs/mm6.core.zip", {{"icons_x2/npc1.png", "mm6 portrait"}});
    writeZipFile(assets / "packs/mm7.core.zip", {{"icons_x2/npc1.png", "mm7 portrait"}});
    writeZipFile(assets / "packs/mm9.core.zip", {{"icons/mm9_item.png", "retained native"}});
    writeCorePackIndex(assets, {"engine", "mm6", "mm7", "mm9"});
    {
        AssetFileSystem fs;
        // Content ownership applies even when an old settings file still selects x1.
        REQUIRE(fs.initialize(temporaryRoot, assets, AssetScaleTier::X1, AssetScaleProfile{}, "mm6"));
        for (const std::string &prefix : {"Data/icons/", "icons/", "engine/icons/", "engine/icons_x2/"})
        {
            CHECK_FALSE(fs.readTextFile(prefix + "retired.bmp"));
            CHECK_FALSE(fs.readTextFile(prefix + "same.png"));
            CHECK(fs.readTextFile(prefix + "same.bmp") == std::optional<std::string>("restored"));
        }
        CHECK(fs.readTextFile("Data/icons/npc1.png") == std::optional<std::string>("mm6 portrait"));
        CHECK(fs.readTextFile("worlds/mm7/icons/npc1.png") == std::optional<std::string>("mm7 portrait"));
        CHECK_FALSE(fs.readTextFile("engine/icons/npc1.png"));
        CHECK(fs.getAssetScaleTierForVirtualPath("engine/icons/same.bmp") == AssetScaleTier::X2);
        CHECK(fs.getAssetScaleTierForVirtualPath("worlds/mm9/icons/mm9_item.png") == AssetScaleTier::X1);
        CHECK(fs.readTextFile("Data/icons/mm9_item.png") == std::optional<std::string>("retained native"));
        REQUIRE(fs.switchActiveWorld("mm7"));
        CHECK(fs.readTextFile("Data/icons/npc1.png") == std::optional<std::string>("mm7 portrait"));
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem cached lookups refresh and follow changed mounts")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeTextFile(assetRoot / "engine/ui/Mixed.txt", "original");
    writeTextFile(assetRoot / "worlds/mm6/maps/shared.txt", "six");
    writeTextFile(assetRoot / "worlds/mm8/maps/shared.txt", "eight");
    {
        AssetFileSystem assets;
        REQUIRE(assets.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, "mm6"));
        CHECK(assets.readTextFile("Data/ui/mixed.txt") == "original");
        CHECK_FALSE(assets.resolveExistingFilePath("Data/ui/new.txt"));
        writeTextFile(assetRoot / "engine/ui/New.txt", "new");
        const uint64_t generation = assets.contentGeneration();
        assets.refreshLookupCache();
        CHECK(assets.contentGeneration() > generation);
        CHECK(assets.readTextFile("Data/ui/new.txt") == "new");
        CHECK(assets.readTextFile("Data/games/shared.txt") == "six");
        REQUIRE(assets.switchActiveWorld("mm8"));
        CHECK(assets.readTextFile("Data/games/shared.txt") == "eight");
        CHECK(assets.readTextFile("Data/ui/mixed.txt") == "original");
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem rejects ambiguous case fallback while preserving exact names")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeTextFile(assetRoot / "engine/ui/Icon.txt", "first");
    writeTextFile(assetRoot / "engine/ui/iCon.txt", "second");
    {
        AssetFileSystem assets;
        REQUIRE(assets.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1));
        CHECK_FALSE(assets.resolveExistingFilePath("engine/ui/ICON.txt"));
        CHECK(assets.readTextFile("engine/ui/Icon.txt") == "first");
        CHECK(assets.readTextFile("engine/ui/iCon.txt") == "second");
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem case index preserves world precedence across differently cased packages")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeTextFile(assetRoot / "worlds/mm6/textures/Mixed.bmp", "six");
    writeTextFile(assetRoot / "worlds/mm7/textures/mixed.bmp", "seven");
    {
        AssetFileSystem assets;
        REQUIRE(assets.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1, "mm6"));
        CHECK(assets.readTextFile("textures/MIXED.bmp") == "six");
        REQUIRE(assets.switchActiveWorld("mm7"));
        CHECK(assets.readTextFile("textures/MIXED.bmp") == "seven");
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem shares indexed and missing lookups safely between preparation workers")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeTextFile(assetRoot / "engine/ui/Mixed.txt", "payload");
    {
        AssetFileSystem assets;
        REQUIRE(assets.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1));
        std::vector<std::future<bool>> workers;
        for (int worker = 0; worker < 4; ++worker)
        {
            workers.push_back(std::async(std::launch::async, [&assets]()
            {
                for (int i = 0; i < 100; ++i)
                {
                    if (assets.readTextFile("Data/ui/mIXed.txt") != "payload"
                        || assets.resolveExistingFilePath("Data/ui/missing.txt"))
                    {
                        return false;
                    }
                }
                return true;
            }));
        }
        for (std::future<bool> &worker : workers)
        {
            CHECK(worker.get());
        }
    }
    std::filesystem::remove_all(temporaryRoot);
}
TEST_CASE("menu HUD textures retain physical x2 resolution and logical half size")
{
    using namespace OpenYAMM::Engine;
    const AssetScaleTier tier = assetScaleTierFromResolvedPath("engine/hud_x2/menus/omenu_button_default.png");
    CHECK(tier == AssetScaleTier::X2);
    CHECK(scalePhysicalPixelsToLogical(256, tier) == 128);
    CHECK(assetScaleTierFromResolvedPath("engine/hud/menus/button.png") == AssetScaleTier::X1);
}
