#include "game/app/OpenYammMain.h"

#if defined(__APPLE__)
#include "game/app/AppleBundlePaths.h"

#include <optional>
#include <vector>
#endif

#include <SDL3/SDL.h>
#if defined(OPENYAMM_IOS)
#include <SDL3/SDL_main.h>
#endif

#if !defined(_WIN32)
#include <sys/resource.h>

#include <algorithm>
#include <cerrno>
#include <cstring>
#include <iostream>
#endif

namespace
{
#if !defined(_WIN32)
// The game keeps every mounted content pack open (252 in release 2.7, more with a language), and macOS starts an app
// with a limit of 256 open files, so the game ran out of them while starting. A started program inherits the limit:
// the downloaded macOS app passes it to the installed version it starts, also to one released before this.
void raiseOpenFileLimit()
{
    // macOS refuses more than OPEN_MAX (10240), whatever the hard limit says.
    constexpr rlim_t WantedOpenFiles = 8192;
    struct rlimit limit = {};

    if (getrlimit(RLIMIT_NOFILE, &limit) != 0 || limit.rlim_cur >= WantedOpenFiles)
    {
        return;
    }

    limit.rlim_cur = std::min(limit.rlim_max, WantedOpenFiles);

    if (setrlimit(RLIMIT_NOFILE, &limit) != 0)
    {
        std::cerr << "Could not raise the limit of open files: " << std::strerror(errno) << '\n';
    }
}
#endif
}

int main(int argc, char **argv)
{
#if !defined(_WIN32)
    raiseOpenFileLimit();
#endif
    SDL_SetAppMetadata("OpenYAMM", nullptr, "io.github.openyamm.OpenYAMM");
#if defined(OPENYAMM_IOS)
    // Finger events drive the touch interface, as on Android; SDL's synthesized mouse events would repeat them.
    SDL_SetHint(SDL_HINT_TOUCH_MOUSE_EVENTS, "0");
    SDL_SetHint(SDL_HINT_MOUSE_TOUCH_EVENTS, "0");
#endif
#if defined(__APPLE__)
    if (const std::optional<int> exitCode = OpenYAMM::Game::startInstalledApplePackage(argc, argv))
    {
        return *exitCode;
    }

    std::vector<char *> arguments = OpenYAMM::Game::appleBundleArguments(argc, argv);
    return OpenYAMM::Game::runApplication(static_cast<int>(arguments.size()) - 1, arguments.data());
#else
    return OpenYAMM::Game::runApplication(argc, argv);
#endif
}
