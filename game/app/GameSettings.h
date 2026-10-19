#pragma once

#include "engine/AssetScaleTier.h"
#include "game/app/KeyboardBindings.h"
#include "game/gameplay/CharacterAttackTuning.h"

#include <SDL3/SDL.h>

#include <array>
#include <cstdint>
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

// Rain and snow particle density; Off hides precipitation (weather, sound and gameplay are unchanged).
enum class WeatherQuality
{
    Off,
    Low,
    Medium,
    High
};

bool parseWeatherQualityValue(const std::string &value, WeatherQuality &result);
std::string weatherQualityValue(WeatherQuality quality);

// Size of the clustered light grid (engine/render/LightGrid.h): High 16x9x24 cells of up to 32 lights, Low 8x5x16 of
// up to 16 (the Android default).
enum class LightGridQuality
{
    Low,
    High
};

bool parseLightGridQualityValue(const std::string &value, LightGridQuality &result);
std::string lightGridQualityValue(LightGridQuality quality);

// Multisample anti-aliasing of the 3D view: "off", "2x" or "4x" as samples 0, 2 or 4.
bool parseAntialiasingValue(const std::string &value, int &samples);
std::string antialiasingValue(int samples);

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

    std::string settingsProfileName;
    uint32_t settingsProfileVersion = 0;
    std::string language = "ru";

    int soundVolume = 9;
    int musicVolume = 9;
    int voiceVolume = 9;

    TurnRateMode turnRate = TurnRateMode::X32;
    bool walksound = true;
    bool showHits = true;
    bool alwaysRun = true;
    bool flipOnExit = false;
    int mouseSensitivity = 100;
    bool invertMouseY = false;
    ControlScheme controlScheme = ControlScheme::Modern;
    bool bloodSplats = true;
    bool coloredLights = true;
    bool tinting = true;
    bool shadows = false;
    int modelShadowQuality = 2;
    bool modelLods = true;
    // Optional ground-item models under engine/world_items; takes effect when loading a map.
    bool itemModels = false;
    // Dark contour shell around 3D creatures (ModelRenderer::setCreatureContour).
    bool creatureOutlines = false;
    int modelLodOverride = -1; // Debug review only; native AI/picking always use the original model.
    bool spriteOutline = false;
    bool textureFiltering = true;
    bool lightmaps = true;
    // Linear multipliers of the separate baked sun/sky sources; identity preserves the authored bake.
    float bakedSunStrength = 1.0f;
    float bakedSkyStrength = 3.0f;
    std::array<float, 3> bakedSunColor = {1.0f, 1.0f, 1.0f};
    std::array<float, 3> bakedSkyColor = {0.8f, 0.9f, 1.0f};
    bool terrainDecorations = false;
    bool waterReflections = true;
    bool waterSpriteReflections = false;
    // Rendered terrain subdivisions per native cell: 1, 2 or 4.
    int terrainSubdivision = 4;
    // A second, rotated sample per ground material hides its repeat (two more texture reads each).
    bool terrainAntiTiling = true;
    // Enhanced sky render resolution relative to the view (0.25-1); the Android profile uses 0.5.
    float skyResolutionScale = 1.0f;
    bool waterMovementRipples = true;
    WeatherQuality weatherQuality = WeatherQuality::High;
    LightGridQuality lightGrid = LightGridQuality::High;
    bool lightGridEnabled = true; // Profiling switch (`render light_grid`); not in the INI.
    // Rain rings on water (with the water shader) and darker, glossier surfaces while wet.
    bool rainRipples = true;
    bool wetSurfaces = true;
    // Sun and point-light highlights on smooth and wet ground (the materials terrain).
    bool terrainSpecular = true;
    int waterReflectionSize = 512;
    std::string terrainFiltering = "anisotropic";
    // Level of every anisotropic sampler (terrain when enabled, buildings, models). 4x: at 16x the materials terrain
    // cost up to 0.2 ms more per frame.
    std::string terrainAnisotropy = "4x";
    std::string bmodelFiltering = "anisotropic";
    std::string billboardFiltering = "linear";
    std::string uiFiltering = "linear";
    std::string textFiltering = "nearest";
    std::string minimapFiltering = "linear";
    std::string viewDistance = "default";
    float outdoorBillboardDepthSlice = 256.0f;
    bool skipEventCutscenes = false;
    bool waitForLevelSprites = true;
    Engine::AssetScaleProfile assetScaleProfile = Engine::createUniformAssetScaleProfile(Engine::AssetScaleTier::X1);
    WindowMode windowMode = WindowMode::Windowed;
    int resolutionWidth = 1600;
    int resolutionHeight = 900;
    bool verticalSync = false;
    bool ambientOcclusion = false;
    int ambientOcclusionStrength = 35;
    // Glow around flames, glow cards, emissive surfaces and spell effects (display-space bloom).
    bool bloom = true;
    int bloomStrength = 65;
    bool cinematicGrading = true;
    int cinematicStrength = 60;
    // Contrast-adaptive sharpening of the 3D view, 0 (off) to 100; the interface is unaffected.
    int sharpening = 0;
    // Multisample anti-aliasing of the 3D view (samples: 0 off, 2 or 4); off costs nothing.
    int antialiasing = 0;

    bool startInMainMenu = false;
    std::string startupSaveFile;
    bool bolsterMonsters = false;
    bool indoorPathfinding = true;
    bool outdoorPathfinding = false;
    BlasterSkillScalingMode blasterSkillScaling = BlasterSkillScalingMode::Default;
    int blasterMinimumRecoveryTicks = 0;
    bool logIndoorVisibility = false;
    bool logIndoorPathfinding = false;
    bool logOutdoorPathfinding = false;
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
    bool turboMovementEnabled = true;
    bool immortal = true;
    bool unlimitedMana = true;
    bool newGameGodLich = false;
    bool allowIncompleteCharacterCreation = false;
    bool debugConsole = true;
    // 3D actor models instead of sprites ([debug] actor_models); persisted like the other debug toggles. Monsters
    // with a model ship no sprites, so turning it off leaves them without a presentation.
    bool actorModels = true;
    // Launch-only directives: never persisted by saveGameSettings.
    std::string actorModelsManifest;
    std::string screenshotPath;
    std::string menuInputTourPath;
    float screenshotDelaySeconds = 0.0f;
    std::string screenshotTourPath;
    // Game time per real second (slow motion below 1), for capturing fast effects such as projectiles.
    float timeScale = 1.0f;
    std::string effectSpawnId;
    std::array<float, 3> effectSpawnPosition = {};
    float effectSpawnScale = 1.0f;
    float effectSpawnYawRadians = 0.0f;
    uint32_t effectSpawnCount = 1;
    float effectStatsDelaySeconds = -1.0f;
    int16_t actorSpawnId = 0;
    uint32_t actorSpawnCount = 1;
    std::array<float, 3> actorSpawnPosition = {};
    std::string modelSpawnPath;
    std::string modelSpawnClip;
    std::array<float, 3> modelSpawnPosition = {};
    float modelSpawnScale = 1.0f;
    float modelSpawnYawRadians = 0.0f;
    bool modelSpawnMarkers = false;
    int keyboardInteractionDepth = 512;
    int mouseInteractionDepth = 512;
    bool combatText = true;
    std::string enemyHealthBarMode = "combat";
    std::string enemyHealthBarValues = "target";
    bool enemyHealthBarDamageTrail = true;
    bool questMarkers = true;
    bool meleeHitBloodEffects = false;
    // Melee hit impact sound by struck material and a brief hitstop on the target (GameplayActorHitFeedback).
    bool meleeHitFeedback = true;
    // Slash, thrust or crush effect at the contact point of a landed melee blow.
    bool meleeHitEffects = true;
    // Brief flash over the struck creature.
    bool meleeHitFlash = false;
    // Small camera turn along the blow on critical hits and kills.
    bool meleeCameraKick = false;
#if defined(__ANDROID__)
    bool contextActionPopup = true;
#else
    bool contextActionPopup = false;
#endif

    static GameSettings createDefault();
};

std::optional<GameSettings> loadGameSettings(const std::filesystem::path &path, std::string &error);
std::optional<std::string> getBakedLightingSetting(const GameSettings &settings, const std::string &name);
bool setBakedLightingSetting(
    GameSettings &settings, const std::string &name, const std::string &value, std::string &error);
bool saveGameSettings(const std::filesystem::path &path, const GameSettings &settings, std::string &error);
bool migrateLegacyAndroidSettings(GameSettings &settings);
bool migrateLegacyDesktopSettings(GameSettings &settings);
CharacterAttackTuning characterAttackTuningFromSettings(const GameSettings &settings);
uint8_t textureAnisotropyLevel(const GameSettings &settings);
float resolveViewDistanceSetting(const std::string &value, float defaultDistance);
}
