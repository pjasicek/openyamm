#pragma once

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
// File names of a versioned installation's executables (OpenYAMM.exe and openyamm.exe on Windows).
#if defined(_WIN32)
constexpr const char *LauncherExecutableName = "OpenYAMM.exe";
constexpr const char *GameExecutableName = "openyamm.exe";
// Each version folder carries its launcher; the game installs it as the launcher after its first healthy start.
constexpr const char *LauncherCopyName = "OpenYAMM-launcher.exe";
#elif defined(__APPLE__)
constexpr const char *LauncherExecutableName = "OpenYAMM";
// The game is an app bundle, so macOS shows its name and icon; its shaders are bundle resources.
constexpr const char *GameExecutableName = "OpenYAMM.app/Contents/MacOS/OpenYAMM";
constexpr const char *LauncherCopyName = "OpenYAMM-launcher";
#else
constexpr const char *LauncherExecutableName = "OpenYAMM";
constexpr const char *GameExecutableName = "openyamm";
constexpr const char *LauncherCopyName = "OpenYAMM-launcher";
#endif

// A self-updating installation that keeps each version in its own folder (packaging/UPDATER_PLAN.md 9.1):
//
//   OpenYAMM[.exe]                  launcher: starts app/<current>/openyamm[.exe] and exits
//   app/current, app/previous       one version name each
//   app/<version>/                  the game, its runtime files and index.json (store ../../assets/packs)
//   app/<version>/starts, healthy   start counter until the version first reached the main menu, then the marker
//   assets/packs/                   content packs shared by the versions
//   update/                         downloads in progress
//   saves/, settings.ini, ...       the player's data, which updates never touch
//
// The running game's files are never replaced: an update stages a new version folder and switches app/current.
// Only the standard library is used, because the launcher builds this file too.
class AppInstallation
{
public:
    explicit AppInstallation(std::filesystem::path root);

    // The installation an executable in app/<version>/ belongs to.
    static std::optional<AppInstallation> containing(const std::filesystem::path &executableDirectory);

    const std::filesystem::path &root() const;
    std::filesystem::path appDirectory(const std::string &version) const;
    std::filesystem::path gameExecutable(const std::string &version) const;
    std::filesystem::path packStore() const;
    std::filesystem::path updateDirectory() const;
    std::filesystem::path launcherPath() const;

    std::optional<std::string> currentVersion() const;
    std::optional<std::string> previousVersion() const;
    bool isHealthy(const std::string &version) const;

    // The launcher's choice: the current version, unless it never became healthy and failed to start twice in a row;
    // then the previous version becomes current again and rolledBackFrom names the failed one. Counts this start.
    std::optional<std::string> chooseVersionToStart(std::string &rolledBackFrom);

    // Makes a staged version current (atomic rename of app/current); the old current version becomes previous.
    bool switchTo(const std::string &version, std::string &error);

    // The game reached its main menu (or a headless run succeeded): no rollback from now on.
    bool markHealthy(const std::string &version);

    // Once the current version is healthy, a rollback target is no longer needed.
    void forgetPreviousVersion();

    // The version a failed update rolled back from, once; the launcher records it for the game to report.
    std::optional<std::string> takeRollbackNotice();

    // Version folders other than the current one, oldest first.
    std::vector<std::string> otherVersions() const;

private:
    std::filesystem::path m_root;
};

// The folder of the running version's files from SDL_GetBasePath(): the executable's folder, or for a macOS app bundle,
// whose base path is OpenYAMM.app/Contents/Resources, the folder that holds the bundle (app/<version>/).
std::filesystem::path programDirectory(const std::filesystem::path &basePath);

// Version folder names are plain release names; never a path.
bool isValidAppVersionName(const std::string &version);

std::optional<std::string> readSmallTextFile(const std::filesystem::path &path);
// Writes through a temporary file and a rename, so readers see the old or the new content.
bool writeTextFileAtomically(const std::filesystem::path &path, const std::string &text);
}
