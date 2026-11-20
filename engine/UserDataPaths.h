#pragma once

#include <cstddef>
#include <filesystem>
#include <optional>
#include <string>

namespace OpenYAMM::Engine
{
// The folder players extract or install: the executable's folder, or the folder above app/ for a versioned
// installation (app/<version>/openyamm.exe, packaging/UPDATER_PLAN.md 9.1).
std::filesystem::path installationRoot(const std::filesystem::path &executableDirectory);
// A release installation carries packaged assets (assets/index.json, or app/current for a versioned installation);
// development builds do not.
bool isReleaseInstallation(const std::filesystem::path &installRoot);
// The folder holding the running version's index.json: its own folder in a versioned installation, else assets/.
std::filesystem::path installedAssetRoot(const std::filesystem::path &executableDirectory);

// Where saves, settings.ini, screenshots and logs live. The game makes this folder its working directory, so the
// relative paths it uses for user data ("saves", "settings.ini", "output/screenshots") resolve inside it.
// Resolution order: an explicit --user-data folder; the installation folder of a release installation (players keep
// everything in the folder they extracted, and updates never touch the user data there); otherwise the working
// directory (development runs).
std::filesystem::path resolveUserDataRoot(
    const std::optional<std::filesystem::path> &explicitRoot,
    const std::filesystem::path &installRoot,
    const std::filesystem::path &workingDirectory);

struct SaveImportResult
{
    size_t imported = 0;
    // Saves whose file name already exists in the target folder; they are never overwritten.
    size_t skipped = 0;
    size_t failed = 0;
};

// Copies the saves of a folder the player picked: a saves folder itself, or an old installation that has one.
SaveImportResult importSaveFiles(const std::filesystem::path &sourceFolder, const std::filesystem::path &savesFolder);

// A file:// URL that opens the folder in the platform's file manager.
std::string folderUrl(const std::filesystem::path &folder);
}
