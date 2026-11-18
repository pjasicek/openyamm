#include "game/app/OpenYammMain.h"

#if defined(__APPLE__)
#include "game/app/AppleBundlePaths.h"

#include <optional>
#include <vector>
#endif

#if defined(__APPLE__) && !defined(OPENYAMM_IOS)
#include <sys/resource.h>

#include <algorithm>
#include <climits>
#endif

#include <SDL3/SDL.h>
#if defined(OPENYAMM_IOS)
#include <SDL3/SDL_main.h>
#endif

#if defined(__APPLE__) && !defined(OPENYAMM_IOS)
namespace
{
// PhysicsFS keeps every mounted content pack open, and a release mounts more of them than the 256 files macOS lets a
// process open by default, so later opens (settings.ini, saves) fail. macOS refuses a soft limit above OPEN_MAX even
// when the hard limit is unlimited. On failure the default limit stays.
void raiseOpenFileLimit()
{
    rlimit limit = {};

    if (getrlimit(RLIMIT_NOFILE, &limit) != 0)
    {
        return;
    }

    const rlim_t target = std::min<rlim_t>(limit.rlim_max, OPEN_MAX);

    if (limit.rlim_cur < target)
    {
        limit.rlim_cur = target;
        setrlimit(RLIMIT_NOFILE, &limit);
    }
}
}
#endif

int main(int argc, char **argv)
{
#if defined(__APPLE__) && !defined(OPENYAMM_IOS)
    // First, so the installed release that startInstalledApplePackage starts with execv inherits the raised limit.
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
