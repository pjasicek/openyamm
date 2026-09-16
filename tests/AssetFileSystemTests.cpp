#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
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

TEST_CASE("AssetFileSystem mounts generated runtime zip package sets")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets";

    writeZipFile(
        assetRoot / "engine.zip",
        {
            {"ui/layout.yml", "engine-ui"},
            {"data_tables/english/Global.txt", "engine-global"},
            {"data_tables/map_stats.txt", "engine-map-stats"}
        });
    writeZipFile(
        assetRoot / "worlds" / "mm6.zip",
        {
            {"maps/shared.odm", "active-map"},
            {"textures/shared.bmp", "active-texture"},
            {"videos/Houses/sample.ogv", "0123456789"}
        });
    writeZipFile(
        assetRoot / "worlds" / "mm8.zip",
        {
            {"maps/out01.odm", "inactive-map"},
            {"textures/shared.bmp", "inactive-texture"}
        });

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

        REQUIRE(assetFileSystem.switchActiveWorld("mm8"));

        const std::optional<std::string> switchedTextureText =
            assetFileSystem.readTextFile("Data/bitmaps/shared.bmp");
        REQUIRE(switchedTextureText.has_value());
        CHECK_EQ(*switchedTextureText, "inactive-texture");
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
    writeTextFile(assetRoot / "engine" / "terrain" / "grass.bmp", "base-grass");
    writeTextFile(assetRoot / "engine" / "terrain_x4" / "grass.bmp", "scaled-grass");
    writeTextFile(assetRoot / "engine" / "sprites" / "tree.bmp", "base-tree");

    {
        OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
            OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
        assetScaleProfile.textures = OpenYAMM::Engine::AssetScaleTier::X4;
        assetScaleProfile.terrain = OpenYAMM::Engine::AssetScaleTier::X4;

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

        const std::optional<std::string> terrainText =
            assetFileSystem.readTextFile("terrain/grass.bmp");
        REQUIRE(terrainText.has_value());
        CHECK_EQ(*terrainText, "scaled-grass");

        const std::optional<std::string> spriteText =
            assetFileSystem.readTextFile("Data/sprites/tree.bmp");
        REQUIRE(spriteText.has_value());
        CHECK_EQ(*spriteText, "base-tree");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem lets terrain fall back to base textures independently of texture scale")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "textures" / "grass.bmp", "base-grass");
    writeTextFile(assetRoot / "engine" / "textures_x4" / "wall.bmp", "scaled-wall");

    {
        OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
            OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
        assetScaleProfile.textures = OpenYAMM::Engine::AssetScaleTier::X4;
        assetScaleProfile.terrain = OpenYAMM::Engine::AssetScaleTier::X1;

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

        const std::optional<std::string> terrainFallbackText =
            assetFileSystem.readTextFile("terrain_textures/grass.bmp");
        REQUIRE(terrainFallbackText.has_value());
        CHECK_EQ(*terrainFallbackText, "base-grass");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem does not use scaled geometry textures as terrain fallback")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "textures" / "water.bmp", "base-water");
    writeTextFile(assetRoot / "engine" / "textures_x4" / "water.bmp", "scaled-geometry-water");
    writeTextFile(assetRoot / "engine" / "terrain_x4" / "grass.bmp", "scaled-grass");

    {
        OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
            OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
        assetScaleProfile.textures = OpenYAMM::Engine::AssetScaleTier::X4;
        assetScaleProfile.terrain = OpenYAMM::Engine::AssetScaleTier::X4;

        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(
            temporaryRoot,
            assetRoot,
            OpenYAMM::Engine::AssetScaleTier::X1,
            assetScaleProfile,
            "mm8"));

        const std::optional<std::string> terrainFallbackText =
            assetFileSystem.readTextFile("terrain_textures/water.bmp");
        REQUIRE(terrainFallbackText.has_value());
        CHECK_EQ(*terrainFallbackText, "base-water");
    }

    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("AssetFileSystem requires explicit scaled terrain directory for scaled terrain")
{
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";

    writeTextFile(assetRoot / "engine" / "textures" / "water.bmp", "base-water");
    writeTextFile(assetRoot / "engine" / "textures_x4" / "water.bmp", "scaled-geometry-water");

    OpenYAMM::Engine::AssetScaleProfile assetScaleProfile =
        OpenYAMM::Engine::createUniformAssetScaleProfile(OpenYAMM::Engine::AssetScaleTier::X1);
    assetScaleProfile.textures = OpenYAMM::Engine::AssetScaleTier::X4;
    assetScaleProfile.terrain = OpenYAMM::Engine::AssetScaleTier::X4;

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
    writeZipFile(assetRoot / "engine.zip", {
        {"icons/kept.bmp", "original"},
        {"icons/mixed.bmp", "original"},
        {"icons_x2/mixed.bmp", "restored"}
    });
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
