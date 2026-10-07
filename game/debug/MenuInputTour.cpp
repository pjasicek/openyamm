#include "game/debug/MenuInputTour.h"

#include "game/debug/ScreenshotCaptureService.h"
#include "game/ui/IScreen.h"

#include <yaml-cpp/yaml.h>
#include <algorithm>
#include <iostream>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
SDL_Window *tourWindow()
{
    // A scripted review can run while the desktop focus remains on another application.
    int count = 0;
    SDL_Window **ppWindows = SDL_GetWindows(&count);
    SDL_Window *pWindow = count == 1 ? ppWindows[0] : nullptr;
    SDL_free(ppWindows);
    return pWindow;
}
} // namespace

void MenuInputTour::update(const std::string &path, GameplayInputFrame &input, IScreen *pScreen,
                           ScreenshotCaptureService &captures)
{
    if (path.empty() ||
        (m_loaded && m_index == m_steps.size() && !m_release && !m_exit && m_releaseKey == SDL_SCANCODE_UNKNOWN))
    {
        return;
    }
    if (m_releaseKey != SDL_SCANCODE_UNKNOWN)
    {
        SDL_Event event{};
        event.type = SDL_EVENT_KEY_UP;
        event.key.scancode = m_releaseKey;
        event.key.key = SDL_GetKeyFromScancode(m_releaseKey, SDL_KMOD_NONE, false);
        if (SDL_Window *pWindow = tourWindow())
        {
            event.key.windowID = SDL_GetWindowID(pWindow);
        }
        if (pScreen != nullptr)
        {
            pScreen->handleSdlEvent(event);
        }
        else
        {
            SDL_PushEvent(&event);
        }
        m_releaseKey = SDL_SCANCODE_UNKNOWN;
    }
    if (!m_loaded)
    {
        const YAML::Node script = YAML::LoadFile(path);
        m_output = script["output_dir"].as<std::string>();
        if (m_output.is_relative())
        {
            m_output = std::filesystem::path(path).parent_path() / m_output;
        }
        m_exit = script["exit"].as<bool>(true);
        for (const YAML::Node &node : script["steps"])
        {
            if (!node.IsMap() || node.size() != 1)
            {
                throw std::runtime_error("Invalid menu tour step");
            }
            const std::string kind = node.begin()->first.as<std::string>();
            const YAML::Node value = node.begin()->second;
            Step step;
            step.kind = kind;
            if (kind == "click" || kind == "pointer_down" || kind == "pointer_move" || kind == "pointer_up"
                || kind == "right_down" || kind == "right_up" || kind == "look_rate")
            {
                step.x = value[0].as<float>();
                step.y = value[1].as<float>();
            }
            else if (kind == "wait" || kind == "wheel")
            {
                step.seconds = value.as<float>();
            }
            else if (kind == "key" || kind == "key_down" || kind == "key_up" || kind == "text" || kind == "capture" ||
                     kind == "expect" || kind == "action" || kind == "action_down" || kind == "action_up")
            {
                step.text = value.as<std::string>();
            }
            else
            {
                throw std::runtime_error("Unknown menu tour step: " + kind);
            }
            m_steps.push_back(std::move(step));
        }
        m_loaded = true;
        m_nextTicks = SDL_GetTicks() + 2000;
    }
    const float scale = std::min(input.screenWidth / 1600.0f, input.screenHeight / 900.0f);
    input.pointerX = (input.screenWidth - 1600 * scale) / 2 + m_x * scale;
    input.pointerY = (input.screenHeight - 900 * scale) / 2 + m_y * scale;
    input.leftMouseButton = {m_release || m_pointerHeld, false, false};
    input.rightMouseButton = {m_rightPointerHeld, false, false};
    for (size_t key = 0; key < m_heldKeys.size(); ++key)
    {
        input.keyboardHeld[key] = input.keyboardHeld[key] || m_heldKeys[key];
    }
    for (size_t actionIndex = 0; actionIndex < m_heldActions.size(); ++actionIndex)
    {
        input.actions[actionIndex].held = input.actions[actionIndex].held || m_heldActions[actionIndex];
    }
    const uint64_t inputTicks = SDL_GetTicksNS();
    const float inputSeconds = m_lastInputTicks == 0 ? 0.0f : float(inputTicks - m_lastInputTicks) * 1.0e-9f;
    m_lastInputTicks = inputTicks;
    input.relativeMouseX += m_lookRateX * inputSeconds;
    input.relativeMouseY += m_lookRateY * inputSeconds;
    if (SDL_GetTicks() < m_nextTicks)
    {
        return;
    }
    if (m_release)
    {
        input.leftMouseButton = {false, false, true};
        m_release = false;
        m_nextTicks = SDL_GetTicks() + 250;
        return;
    }
    if (m_index == m_steps.size())
    {
        if (m_exit && !captures.hasPendingCaptures())
        {
            m_exit = false;
            SDL_Event event{};
            event.type = SDL_EVENT_QUIT;
            SDL_PushEvent(&event);
        }
        return;
    }
    const Step &step = m_steps[m_index++];
    std::cout << "Menu tour: " << m_index << ' ' << step.kind << ' ' << step.text << '\n';
    m_nextTicks = SDL_GetTicks() + 350;
    if (step.kind == "wait")
    {
        m_nextTicks = SDL_GetTicks() + uint64_t(std::max(0.0f, step.seconds) * 1000);
    }
    else if (step.kind == "look_rate")
    {
        m_lookRateX = step.x;
        m_lookRateY = step.y;
    }
    else if (step.kind == "click" || step.kind == "pointer_down" || step.kind == "pointer_move" ||
             step.kind == "pointer_up")
    {
        m_x = step.x;
        m_y = step.y;
        input.pointerX = (input.screenWidth - 1600 * scale) / 2 + m_x * scale;
        input.pointerY = (input.screenHeight - 900 * scale) / 2 + m_y * scale;
        if (step.kind != "pointer_move")
        {
            const bool down = step.kind != "pointer_up";
            input.leftMouseButton = {down, down, !down};
            m_pointerHeld = step.kind == "pointer_down";
            m_release = step.kind == "click";
            m_nextTicks = SDL_GetTicks() + 90;
        }
    }
    else if (step.kind == "right_down" || step.kind == "right_up")
    {
        m_x = step.x;
        m_y = step.y;
        input.pointerX = (input.screenWidth - 1600 * scale) / 2 + m_x * scale;
        input.pointerY = (input.screenHeight - 900 * scale) / 2 + m_y * scale;
        m_rightPointerHeld = step.kind == "right_down";
        input.rightMouseButton = {m_rightPointerHeld, m_rightPointerHeld, !m_rightPointerHeld};
    }
    else if (step.kind == "action" || step.kind == "action_down" || step.kind == "action_up")
    {
        const auto found = std::find_if(keyboardBindingDefinitions().begin(), keyboardBindingDefinitions().end(),
            [&](const KeyboardBindingDefinition &definition) { return definition.iniKey == step.text; });
        if (found == keyboardBindingDefinitions().end())
        {
            throw std::runtime_error("Unknown gameplay tour action: " + step.text);
        }
        const size_t actionIndex = keyboardActionIndex(found->action);
        const bool down = step.kind != "action_up";
        if (step.kind != "action")
        {
            m_heldActions[actionIndex] = down;
        }
        input.actions[actionIndex] = {down, down, !down};
    }
    else if (step.kind == "wheel")
    {
        SDL_Event event = {};
        event.type = SDL_EVENT_MOUSE_WHEEL;
        event.wheel.y = step.seconds;
        SDL_PushEvent(&event);
    }
    else if (step.kind == "capture")
    {
        captures.requestCapture(m_output / (step.text + ".png"),
                                [](bool success, const std::string &message)
                                {
                                    if (!success)
                                    {
                                        throw std::runtime_error(message);
                                    }
                                    std::cout << "Menu tour: " << message << '\n';
                                });
    }
    else if (step.kind == "expect")
    {
        SDL_Window *pWindow = tourWindow();
        const bool matched = (step.text == "gameplay" && pScreen == nullptr) ||
                             (step.text == "pause" && pScreen != nullptr && pScreen->mode() == AppMode::PauseMenu) ||
                             (step.text == "text_input" && pWindow != nullptr && SDL_TextInputActive(pWindow)) ||
                             (step.text == "menu_cursor" && pWindow != nullptr &&
                              !SDL_GetWindowRelativeMouseMode(pWindow) && SDL_CursorVisible());
        if (!matched)
        {
            throw std::runtime_error("Menu tour expectation failed: " + step.text);
        }
    }
    else
    {
        SDL_Event event{};
        if (step.kind == "text")
        {
            SDL_Window *pWindow = tourWindow();
            if (pWindow == nullptr || !SDL_TextInputActive(pWindow))
            {
                throw std::runtime_error("Menu tour text entry requires active SDL text input");
            }
            event.type = SDL_EVENT_TEXT_INPUT;
            event.text.windowID = SDL_GetWindowID(pWindow);
            event.text.text = step.text.c_str();
            SDL_PushEvent(&event);
            return;
        }
        else
        {
            const SDL_Scancode code = SDL_GetScancodeFromName(step.text.c_str());
            if (code == SDL_SCANCODE_UNKNOWN)
            {
                throw std::runtime_error("Unknown menu tour key: " + step.text);
            }
            const bool down = step.kind != "key_up";
            input.keyboardHeld[code] = down;
            input.keyboardPressCounts[code] = down ? 1 : 0;
            m_heldKeys[code] = step.kind == "key_down";
            if (step.kind == "key")
            {
                m_releaseKey = code;
            }
            event.type = down ? SDL_EVENT_KEY_DOWN : SDL_EVENT_KEY_UP;
            event.key.scancode = code;
            event.key.key = SDL_GetKeyFromScancode(code, SDL_KMOD_NONE, false);
            if (SDL_Window *pWindow = tourWindow())
            {
                event.key.windowID = SDL_GetWindowID(pWindow);
            }
        }
        if (pScreen != nullptr)
        {
            pScreen->handleSdlEvent(event);
        }
        else
        {
            // Gameplay/debug-console keys belong to the normal SDL event path when there is no UI screen.
            SDL_PushEvent(&event);
        }
    }
}
} // namespace OpenYAMM::Game
