#pragma once

#include "game/gameplay/GameplayInputFrame.h"

#include <array>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class IScreen;
class ScreenshotCaptureService;

// Optional native UI review script. Coordinates use the menu's 1600 x 900 design canvas.
class MenuInputTour
{
  public:
    using ConsoleLineRunner = std::function<void(const std::string &line)>;

    // Held keys also hold the gameplay actions bound to them in bindings; console steps go through runConsoleLine.
    // nowNanoseconds is the tour's clock (the frames' summed steps), so waits follow a video capture's fixed step.
    void update(const std::string &path, uint64_t nowNanoseconds, GameplayInputFrame &input, IScreen *pScreen,
                ScreenshotCaptureService &captures, const std::array<InputBinding, KeyboardActionCount> &bindings,
                const ConsoleLineRunner &runConsoleLine);

  private:
    struct Step
    {
        std::string kind;
        std::string text;
        float x = 0;
        float y = 0;
        float seconds = 0;
    };
    std::vector<Step> m_steps;
    std::filesystem::path m_output;
    size_t m_index = 0;
    uint64_t m_nextTicks = 0;
    uint64_t m_lastInputTicks = 0;
    bool m_loaded = false;
    bool m_exit = false;
    bool m_release = false;
    bool m_pointerHeld = false;
    bool m_rightPointerHeld = false;
    std::array<bool, SDL_SCANCODE_COUNT> m_heldKeys = {};
    std::array<bool, KeyboardActionCount> m_heldActions = {};
    SDL_Scancode m_releaseKey = SDL_SCANCODE_UNKNOWN;
    float m_x = 0;
    float m_y = 0;
    float m_lookRateX = 0;
    float m_lookRateY = 0;
};
} // namespace OpenYAMM::Game
