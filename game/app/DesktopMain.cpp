#include "game/app/OpenYammMain.h"

#if defined(__APPLE__)
#include "game/app/AppleBundlePaths.h"

#include <vector>
#endif

#include <SDL3/SDL.h>
#if defined(OPENYAMM_IOS)
#include <SDL3/SDL_main.h>
#endif

int main(int argc, char **argv)
{
    SDL_SetAppMetadata("OpenYAMM", nullptr, "io.github.openyamm.OpenYAMM");
#if defined(OPENYAMM_IOS)
    // Finger events drive the touch interface, as on Android; SDL's synthesized mouse events would repeat them.
    SDL_SetHint(SDL_HINT_TOUCH_MOUSE_EVENTS, "0");
    SDL_SetHint(SDL_HINT_MOUSE_TOUCH_EVENTS, "0");
#endif
#if defined(__APPLE__)
    std::vector<char *> arguments = OpenYAMM::Game::appleBundleArguments(argc, argv);
    return OpenYAMM::Game::runApplication(static_cast<int>(arguments.size()) - 1, arguments.data());
#else
    return OpenYAMM::Game::runApplication(argc, argv);
#endif
}
