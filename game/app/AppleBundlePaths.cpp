#include "game/app/AppleBundlePaths.h"

#include <SDL3/SDL.h>

#include <filesystem>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
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

    char *pPreferencesPath = SDL_GetPrefPath(nullptr, "OpenYAMM");

    if (pPreferencesPath == nullptr)
    {
        std::cerr << "Could not locate the application data folder: " << SDL_GetError() << '\n';
        return std::nullopt;
    }

    const std::filesystem::path path = pPreferencesPath;
    SDL_free(pPreferencesPath);
    return path;
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
}
