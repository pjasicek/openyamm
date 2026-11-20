#include "engine/UserDataPaths.h"
#include "game/app/GameSettings.h"

#include <doctest/doctest.h>

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

namespace
{
std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_userdata_" + std::to_string(tickCount));
}

void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

std::string readTextFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
}

void makeReleaseInstallation(const std::filesystem::path &installRoot)
{
    writeTextFile(installRoot / "assets" / "index.json", "{}");
}
}

TEST_CASE("user data stays in the working directory for development runs")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path install = root / "build" / "game";
    std::filesystem::create_directories(install);

    CHECK(OpenYAMM::Engine::resolveUserDataRoot(std::nullopt, install, root / "repo")
          == (root / "repo").lexically_normal());
    std::filesystem::remove_all(root);
}

TEST_CASE("a release installation keeps user data in its own folder")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path install = root / "OpenYAMM";
    makeReleaseInstallation(install);

    // Also when a shortcut starts the game from another folder.
    CHECK(OpenYAMM::Engine::resolveUserDataRoot(std::nullopt, install, root / "shortcut")
          == install.lexically_normal());
    std::filesystem::remove_all(root);
}

TEST_CASE("an explicit user data folder overrides the installation folder")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path install = root / "OpenYAMM";
    makeReleaseInstallation(install);

    CHECK(OpenYAMM::Engine::resolveUserDataRoot(std::filesystem::path("custom"), install, root / "cwd")
          == (root / "cwd" / "custom").lexically_normal());
    CHECK(OpenYAMM::Engine::resolveUserDataRoot(root / "absolute", install, root / "cwd")
          == (root / "absolute").lexically_normal());
    std::filesystem::remove_all(root);
}

TEST_CASE("desktop settings migration drops asset roots written by release packages")
{
    for (const char *pShippedRoot : {"assets", "/app/share/openyamm/assets"})
    {
        OpenYAMM::Game::GameSettings settings = OpenYAMM::Game::GameSettings::createDefault();
        settings.settingsProfileName = "desktop";
        settings.settingsProfileVersion = 1;
        settings.assetRoot = pShippedRoot;
        CHECK(OpenYAMM::Game::migrateLegacyDesktopSettings(settings));
        CHECK(settings.assetRoot.empty());
    }

    OpenYAMM::Game::GameSettings developer = OpenYAMM::Game::GameSettings::createDefault();
    developer.settingsProfileName = "desktop";
    developer.settingsProfileVersion = 1;
    developer.assetRoot = "/home/developer/assets_dev";
    CHECK(OpenYAMM::Game::migrateLegacyDesktopSettings(developer));
    CHECK(developer.assetRoot == "/home/developer/assets_dev");
    CHECK_FALSE(OpenYAMM::Game::migrateLegacyDesktopSettings(developer));
}

TEST_CASE("picked save folders import without overwriting existing saves")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path oldInstall = root / "OpenYAMM-1.4";
    const std::filesystem::path saves = root / "appdata" / "saves";
    writeTextFile(oldInstall / "saves" / "save1.oysav", "old");
    writeTextFile(oldInstall / "saves" / "save2.oysav", "two");
    writeTextFile(saves / "save1.oysav", "current");

    // The installation folder itself and its saves folder both work.
    const OpenYAMM::Engine::SaveImportResult fromInstall = OpenYAMM::Engine::importSaveFiles(oldInstall, saves);
    CHECK(fromInstall.imported == 1);
    CHECK(fromInstall.skipped == 1);
    CHECK(fromInstall.failed == 0);
    CHECK(readTextFile(saves / "save1.oysav") == "current");
    CHECK(readTextFile(saves / "save2.oysav") == "two");

    const OpenYAMM::Engine::SaveImportResult again =
        OpenYAMM::Engine::importSaveFiles(oldInstall / "saves", saves);
    CHECK(again.imported == 0);
    CHECK(again.skipped == 2);

    const OpenYAMM::Engine::SaveImportResult empty = OpenYAMM::Engine::importSaveFiles(root / "nothing", saves);
    CHECK(empty.imported + empty.skipped + empty.failed == 0);
    std::filesystem::remove_all(root);
}

TEST_CASE("user data folder URLs use the file scheme")
{
    CHECK(OpenYAMM::Engine::folderUrl("/home/player/.local/share/openyamm")
          == "file:///home/player/.local/share/openyamm");
}
