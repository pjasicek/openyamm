#include "game/app/AppleBundlePaths.h"

#include <SDL3/SDL.h>

#include <unistd.h>

#include <cerrno>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
#if !defined(OPENYAMM_IOS)
// ~/Library/Application Support/OpenYAMM: the player's data, and the installation of a downloaded release.
std::optional<std::filesystem::path> applicationSupportDirectory()
{
    char *pPreferencesPath = SDL_GetPrefPath(nullptr, "OpenYAMM");

    if (pPreferencesPath == nullptr)
    {
        std::cerr << "Could not locate the application data folder: " << SDL_GetError() << '\n';
        return std::nullopt;
    }

    const std::filesystem::path path = pPreferencesPath;
    SDL_free(pPreferencesPath);
    return path;
}
#endif

// Finder and the iOS home screen start apps in "/", and a signed bundle must stay unmodified, so settings.ini, saves/
// and the log live in a per-user folder: ~/Library/Application Support/OpenYAMM on macOS. Empty when there is none to
// choose: a launch from a directory with its own settings.ini, such as a development checkout, keeps using it.
std::optional<std::filesystem::path> userDataDirectory()
{
#if defined(OPENYAMM_IOS)
    // Finder and the Files app reach the Documents folder (UIFileSharingEnabled), so it also takes the packaged
    // assets copied onto a device.
    const char *pDocumentsPath = SDL_GetUserFolder(SDL_FOLDER_DOCUMENTS);

    if (pDocumentsPath == nullptr)
    {
        std::cerr << "Could not locate the Documents folder: " << SDL_GetError() << '\n';
        return std::nullopt;
    }

    return std::filesystem::path(pDocumentsPath);
#else
    std::error_code error;

    if (std::filesystem::is_regular_file("settings.ini", error))
    {
        return std::nullopt;
    }

    return applicationSupportDirectory();
#endif
}
}

std::vector<char *> appleBundleArguments(int argc, char **argv)
{
    static char userDataOption[] = "--user-data";
    static std::string userDataPath;
    std::vector<char *> arguments(argv, argv + argc);
    bool userDataNamed = false;

    for (int argumentIndex = 1; argumentIndex < argc; ++argumentIndex)
    {
        userDataNamed = userDataNamed || std::string_view(argv[argumentIndex]) == userDataOption;
    }

    if (!userDataNamed)
    {
        if (const std::optional<std::filesystem::path> path = userDataDirectory())
        {
            // The same as passing --user-data: it also takes precedence over a release installation's own folder,
            // which for a bundle with packaged assets would be the bundle itself.
            userDataPath = path->string();
            arguments.push_back(userDataOption);
            arguments.push_back(userDataPath.data());
        }
    }

    arguments.push_back(nullptr);
    return arguments;
}

std::optional<Engine::AppInstallation> applePackageInstallation()
{
#if defined(OPENYAMM_APPLE_PACKAGE_VERSION)
    const char *pBasePath = SDL_GetBasePath();

    if (pBasePath == nullptr)
    {
        return std::nullopt;
    }

    std::filesystem::path basePath = std::filesystem::path(pBasePath).lexically_normal();

    if (!basePath.has_filename())
    {
        basePath = basePath.parent_path();
    }

    // Not an app bundle, or one in an installation's version folder.
    const std::filesystem::path program = Engine::programDirectory(basePath);

    if (program == basePath || Engine::AppInstallation::containing(program))
    {
        return std::nullopt;
    }

    const std::optional<std::filesystem::path> root = applicationSupportDirectory();
    return root ? std::optional<Engine::AppInstallation>(Engine::AppInstallation(*root)) : std::nullopt;
#else
    return std::nullopt;
#endif
}

std::string applePackageVersion()
{
#if defined(OPENYAMM_APPLE_PACKAGE_VERSION)
    return OPENYAMM_APPLE_PACKAGE_VERSION;
#else
    return {};
#endif
}

std::optional<int> startInstalledApplePackage(int argc, char **argv)
{
    std::optional<Engine::AppInstallation> installation = applePackageInstallation();

    if (!installation || !installation->currentVersion())
    {
        return std::nullopt;
    }

    // As the launcher does: counts the start, so a version that never reaches its menu is rolled back.
    std::string rolledBackFrom;
    const std::optional<std::string> version = installation->chooseVersionToStart(rolledBackFrom);
    const std::string game = installation->gameExecutable(version.value_or("")).string();
    std::vector<char *> arguments = {const_cast<char *>(game.c_str())};
    arguments.insert(arguments.end(), argv + 1, argv + argc);
    arguments.push_back(nullptr);
    execv(game.c_str(), arguments.data());

    const std::string message = "OpenYAMM could not start " + game + ": " + std::strerror(errno)
        + ". Delete " + installation->root().string() + "/app and start OpenYAMM again.";
    std::cerr << message << '\n';
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "OpenYAMM", message.c_str(), nullptr);
    return 1;
}
}
