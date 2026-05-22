#pragma once

#include "engine/AssetScaleTier.h"
#include "game/app/KeyboardBindings.h"
#include "game/gameplay/CharacterAttackTuning.h"

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

enum class ControlScheme
{
    Modern,
    Classic
};

struct GameSettings
{
    struct KeyboardSettings
    {
        std::array<InputBinding, KeyboardActionCount> bindings = createDefaultKeyboardBindings();

        InputBinding binding(KeyboardAction action) const
        {
            return bindings[keyboardActionIndex(action)];
        }

        SDL_Scancode keyboardBinding(KeyboardAction action) const
        {
            const InputBinding inputBinding = binding(action);
            return inputBinding.kind == InputBindingKind::Keyboard ? inputBinding.scancode : SDL_SCANCODE_UNKNOWN;
        }

        bool isPressed(KeyboardAction action, const bool *pKeyboardState) const
        {
            const SDL_Scancode scancode = keyboardBinding(action);

            return pKeyboardState != nullptr
                && scancode > SDL_SCANCODE_UNKNOWN
                && scancode < SDL_SCANCODE_COUNT
                && pKeyboardState[scancode];
        }

        void setBinding(KeyboardAction action, InputBinding binding)
        {
            bindings[keyboardActionIndex(action)] = binding;
        }

        void setBinding(KeyboardAction action, SDL_Scancode scancode)
        {
            bindings[keyboardActionIndex(action)] = keyboardInputBinding(scancode);
        }

        void restoreDefaults(ControlScheme scheme = ControlScheme::Modern)
        {
            bindings = createDefaultKeyboardBindings();

            if (scheme == ControlScheme::Modern)
            {
                setBinding(KeyboardAction::Attack, mouseButtonInputBinding(SDL_BUTTON_LEFT));
                setBinding(KeyboardAction::Use, keyboardInputBinding(SDL_SCANCODE_E));
            }
            else
            {
                setBinding(KeyboardAction::Forward, keyboardInputBinding(SDL_SCANCODE_UP));
                setBinding(KeyboardAction::Backward, keyboardInputBinding(SDL_SCANCODE_DOWN));
                setBinding(KeyboardAction::Left, keyboardInputBinding(SDL_SCANCODE_LEFT));
                setBinding(KeyboardAction::Right, keyboardInputBinding(SDL_SCANCODE_RIGHT));
                setBinding(KeyboardAction::Attack, keyboardInputBinding(SDL_SCANCODE_A));
                setBinding(KeyboardAction::Use, mouseButtonInputBinding(SDL_BUTTON_LEFT));
            }
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
    int mouseSensitivity = 100;
    ControlScheme controlScheme = ControlScheme::Modern;
    bool bloodSplats = true;
    bool coloredLights = true;
    bool tinting = true;
    bool shadows = false;
    bool spriteOutline = false;
    bool textureFiltering = true;
    std::string terrainFiltering = "anisotropic";
    std::string terrainAnisotropy = "8x";
    std::string bmodelFiltering = "anisotropic";
    std::string billboardFiltering = "linear";
    std::string uiFiltering = "linear";
    std::string textFiltering = "nearest";
    std::string minimapFiltering = "linear";
    std::string viewDistance = "default";
    float outdoorBillboardDepthSlice = 256.0f;
    bool skipEventCutscenes = false;
    Engine::AssetScaleProfile assetScaleProfile = Engine::createUniformAssetScaleProfile(Engine::AssetScaleTier::X1);
    GameplayUiLayout gameplayUiLayout = GameplayUiLayout::Widescreen;
    WindowMode windowMode = WindowMode::Windowed;
    int resolutionWidth = 1600;
    int resolutionHeight = 900;
    bool verticalSync = false;

    bool startInMainMenu = false;
    bool bolsterMonsters = false;
    bool indoorPathfinding = true;
    BlasterSkillScalingMode blasterSkillScaling = BlasterSkillScalingMode::Default;
    int blasterMinimumRecoveryTicks = 0;
    bool logIndoorVisibility = false;
    bool logIndoorPathfinding = false;
    bool fpsTrace = false;
    bool performanceTrace = false;
    bool hitchTrace = false;
    bool collisionTrace = false;
    bool gameplayTrace = false;
    bool gameplayTraceAppend = true;
    std::string gameplayTraceFile = "logs/gameplay_trace.log";
    bool combatTrace = false;
    bool combatTraceAppend = true;
    std::string combatTraceFile = "logs/combat_trace.log";
    float hitchThresholdMilliseconds = 8.0f;
    KeyboardSettings keyboard = {};
    bool preseedParty = true;
    uint32_t partySeedRosterId = 0;
    std::string assetRoot;
    std::string startWorldId = "mm8";
    std::string startMapFile;
    bool overrideStartPosition = false;
    float startX = 0.0f;
    float startY = 0.0f;
    float startZ = 0.0f;
    bool startFlying = false;
    float movementSpeedMultiplier = 1.0f;
    bool immortal = true;
    bool unlimitedMana = true;
    bool newGameGodLich = false;
    bool allowIncompleteCharacterCreation = false;
    bool debugConsole = true;
    bool arpgModeEnabled = false;
    std::string arpgModePlayerMonsterDescriptor = "m270";
    float arpgModeCameraYawDegrees = 135.0f;
    float arpgModeCameraPitchDegrees = -55.0f;
    float arpgModeCameraDistance = 2600.0f;
    float arpgModeCameraTargetHeight = 120.0f;
    float arpgModeCameraFovDegrees = 45.0f;
    float arpgModeCameraFollowLerp = 18.0f;
    float arpgModeClickStopRadius = 48.0f;
    float arpgModeMoveSpeedMultiplier = 1.0f;
    float arpgModeSpellAnimationSeconds = 0.35f;
    float arpgModeSpellReleaseSeconds = 0.12f;
    float arpgModeAttackAnimationMinSeconds = 0.25f;
    float arpgModeAttackAnimationMaxSeconds = 0.5f;
    float arpgModeAttackAnimationRecoveryScale = 0.35f;
    int keyboardInteractionDepth = 512;
    int mouseInteractionDepth = 512;
#if defined(__ANDROID__)
    bool contextActionPopup = true;
#else
    bool contextActionPopup = false;
#endif

    static GameSettings createDefault();
};

std::optional<GameSettings> loadGameSettings(const std::filesystem::path &path, std::string &error);
bool saveGameSettings(const std::filesystem::path &path, const GameSettings &settings, std::string &error);
CharacterAttackTuning characterAttackTuningFromSettings(const GameSettings &settings);
float resolveViewDistanceSetting(const std::string &value, float defaultDistance);
}
