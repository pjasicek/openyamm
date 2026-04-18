#pragma once

#include "game/app/KeyboardBindings.h"

#include <SDL3/SDL.h>

#include <array>
#include <filesystem>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
enum class TurnRateMode
{
    X16,
    X32,
    Smooth
};

enum class GameplayUiLayout
{
    Standard,
    Widescreen
};

enum class WindowMode
{
    Windowed,
    WindowedFullscreen,
    Fullscreen
};

struct GameSettings
{
    struct KeyboardSettings
    {
        std::array<SDL_Scancode, KeyboardActionCount> bindings = createDefaultKeyboardBindings();

        SDL_Scancode binding(KeyboardAction action) const
        {
            return bindings[keyboardActionIndex(action)];
        }

        bool isPressed(KeyboardAction action, const bool *pKeyboardState) const
        {
            const SDL_Scancode scancode = binding(action);

            return pKeyboardState != nullptr
                && scancode > SDL_SCANCODE_UNKNOWN
                && scancode < SDL_SCANCODE_COUNT
                && pKeyboardState[scancode];
        }

        void setBinding(KeyboardAction action, SDL_Scancode scancode)
        {
            bindings[keyboardActionIndex(action)] = scancode;
        }

        void restoreDefaults()
        {
            bindings = createDefaultKeyboardBindings();
        }
    };

    int soundVolume = 9;
    int musicVolume = 9;
    int voiceVolume = 9;

    TurnRateMode turnRate = TurnRateMode::X32;
    bool walksound = true;
    bool showHits = true;
    bool alwaysRun = true;
    bool flipOnExit = false;
    bool bloodSplats = true;
    bool coloredLights = true;
    bool tinting = true;
    bool textureFiltering = true;
    std::string terrainFiltering = "anisotropic";
    std::string terrainAnisotropy = "8x";
    std::string bmodelFiltering = "linear";
    std::string billboardFiltering = "linear";
    std::string uiFiltering = "linear";
    std::string textFiltering = "nearest";
    std::string minimapFiltering = "linear";
    GameplayUiLayout gameplayUiLayout = GameplayUiLayout::Widescreen;
    WindowMode windowMode = WindowMode::Windowed;
    int resolutionWidth = 1600;
    int resolutionHeight = 900;

    bool startInMainMenu = false;
    KeyboardSettings keyboard = {};
    bool preseedParty = true;
    uint32_t partySeedRosterId = 0;
    std::string startMapFile = "out01.odm";
    bool overrideStartPosition = false;
    float startX = 0.0f;
    float startY = 0.0f;
    float startZ = 0.0f;
    bool startFlying = false;
    float movementSpeedMultiplier = 1.0f;
    bool immortal = true;
    bool unlimitedMana = true;
    int keyboardInteractionDepth = 512;
    int mouseInteractionDepth = 512;

    static GameSettings createDefault();
};

std::optional<GameSettings> loadGameSettings(const std::filesystem::path &path, std::string &error);
bool saveGameSettings(const std::filesystem::path &path, const GameSettings &settings, std::string &error);
}
