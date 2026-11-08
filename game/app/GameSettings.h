#pragma once

#include "engine/AssetScaleTier.h"
#include "game/app/KeyboardBindings.h"
#include "game/gameplay/CharacterAttackTuning.h"

#include <SDL3/SDL.h>

#include <array>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <vector>

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

// The combat log's button, docked panel and recording (gameplay.combat_log: auto, on, off). Auto shows it in a ruleset
// other than Standard, in worlds that show it (world.yml combatLog; not MM9): the user, 2026-11-06. INI files from
// before the choice read true as auto and false as off.
enum class CombatLogMode
{
    Auto,
    On,
    Off
};

inline const char *combatLogModeValue(CombatLogMode mode)
{
    return mode == CombatLogMode::On ? "on" : mode == CombatLogMode::Off ? "off" : "auto";
}

inline std::optional<CombatLogMode> parseCombatLogModeValue(std::string_view value)
{
    if (value == "auto" || value == "true")
    {
        return CombatLogMode::Auto;
    }
    if (value == "on")
    {
        return CombatLogMode::On;
    }
    if (value == "off" || value == "false")
    {
        return CombatLogMode::Off;
    }
    return std::nullopt;
}

// "off", "hold" or "always" (gameplay.rarity_glow).
inline bool validRarityGlowValue(std::string_view value)
{
    return value == "off" || value == "hold" || value == "always";
}

// "member" or "bag" (controls.bag_number_keys).
inline bool validBagNumberKeysValue(std::string_view value)
{
    return value == "member" || value == "bag";
}

bool parseLightGridQualityValue(const std::string &value, LightGridQuality &result);
std::string lightGridQualityValue(LightGridQuality quality);

// Multisample anti-aliasing of the 3D view: "off", "2x" or "4x" as samples 0, 2 or 4.
bool parseAntialiasingValue(const std::string &value, int &samples);
std::string antialiasingValue(int samples);

// A turn-based speed factor: one of "1", "1.5", "2", "3" or "4".
bool parseTurnBasedSpeedValue(const std::string &value, float &speed);
std::string turnBasedSpeedValue(float speed);

// The repeated voice line interval in milliseconds: one of "0", "500", "1000", "2000", "3000", "5000" or "10000".
bool parseRepeatedVoiceLineIntervalValue(const std::string &value, int &intervalMs);
std::string repeatedVoiceLineIntervalValue(int intervalMs);

// One key of settings.ini, in the writer's section order.
struct SettingsEntry
{
    std::string section;
    std::string key;
    std::string value;

    bool operator==(const SettingsEntry &other) const = default;
};

// The player's settings.ini holds only the player's own choices; defaults come from GameSettings::createDefault().
// A key that was in the file stays there (an earlier choice stays a choice, even when it equals today's default); any
// other key is written only while it differs from the default. A changed default therefore reaches every player who
// never touched that setting.
struct SettingsFileState
{
    // "section.key" of every key the file held when it was loaded, or that a save wrote.
    std::set<std::string> storedKeys;
    // Keys this version does not know (from a newer version or a mod), written back unchanged.
    std::vector<SettingsEntry> unknownEntries;
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

    std::string settingsProfileName;
    uint32_t settingsProfileVersion = 0;

    int soundVolume = 3;
    int musicVolume = 2;
    int voiceVolume = 3;

    TurnRateMode turnRate = TurnRateMode::Smooth;
    bool walksound = true;
    // A party member does not say the same voice line again within this many milliseconds; 0 keeps every repeat.
    int repeatedVoiceLineIntervalMs = 0;
    bool showHits = true;
    bool alwaysRun = true;
    // What the number keys do on the inventory page and in shops and chests when a ruleset gives bags (MAW):
    // "member" selects a party member, as in MAW and the original games, and Shift with the Bag keys opens a bag;
    // "bag" swaps them. A party of one opens bags either way.
    std::string bagNumberKeys = "member";
    bool flipOnExit = false;
    int mouseSensitivity = 100;
    bool invertMouseY = false;
    // The left button's Attack or Use (by the control preset) uses what is under the cursor when it can be used, and
    // attacks otherwise.
    bool smartClick = false;
    ControlScheme controlScheme = ControlScheme::Modern;
    bool bloodSplats = true;
    bool coloredLights = true;
    // Torch Light glows firelight orange instead of the original neutral grey.
    bool warmTorchLight = false;
    bool tinting = false;
    bool shadows = false;
    int modelShadowQuality = 2;
    bool modelLods = true;
    // Dark contour shell around 3D creatures (ModelRenderer::setCreatureContour).
    bool creatureOutlines = false;
    int modelLodOverride = -1; // Debug review only; native AI/picking always use the original model.
    bool spriteOutline = false;
    bool textureFiltering = true;
    bool lightmaps = true;
    // Linear multipliers of the separate baked sun/sky sources; identity preserves the authored bake.
    float bakedSunStrength = 1.0f;
    float bakedSkyStrength = 2.0f;
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
    // Building and dungeon faces drawn with their material maps (relief, roughness, metal, glow;
    // devdocs/SURFACE_MATERIALS_PLAN.md), and the parallax depth of their height maps up close. Experimental,
    // off by default and outside the graphics presets; off, map loads read none of the maps.
    bool surfaceMaterials = false;
    bool surfaceParallax = false;
    // Screen-space reflections in smooth surface materials (marble, glass, metal, puddles); experimental.
    bool surfaceReflections = false;
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
    bool verticalSync = true;
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

    bool startInMainMenu = true;
    std::string startupSaveFile;
    bool bolsterMonsters = false;
    bool indoorPathfinding = true;
    bool outdoorPathfinding = true;
    BlasterSkillScalingMode blasterSkillScaling = BlasterSkillScalingMode::ScalingDamage;
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
    float hitchThresholdMilliseconds = 40.0f;
    KeyboardSettings keyboard = {};
    bool preseedParty = false;
    uint32_t partySeedRosterId = 0;
    std::string assetRoot;
    // [updates]: whether the self-updating releases (Windows, Android) look for updates: "ask" until the player
    // answered the first-start question, then "auto" or "off". The URL is the channel's base (packaging/UPDATER_PLAN.md 7.3).
    std::string updateCheck = "ask";
    std::string updateUrl = "https://jasicek.net/openyamm/updates/";
    // [updates] keep_modified_packs, only in the file (packaging/MODDING.md): content packs the player edited load as
    // they are, and the game neither restores nor updates them, so it does not update at all.
    bool keepModifiedPacks = false;
    std::string startWorldId = "mm8";
    std::string startMapFile;
    bool overrideStartPosition = false;
    float startX = 0.0f;
    float startY = 0.0f;
    float startZ = 0.0f;
    bool startFlying = false;
    float movementSpeedMultiplier = 1.0f;
    bool turboMovementEnabled = false;
    bool immortal = false;
    bool unlimitedMana = false;
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
    // A burst from screenshot_path: this many captures (1: the single capture), one every screenshotBurstIntervalMs
    // of real time from the delay, written as <stem>_000<ext>, <stem>_001<ext> ... (tools/RUN_GAME.md).
    uint32_t screenshotBurstCount = 1;
    float screenshotBurstIntervalMs = 100.0f;
    std::string screenshotTourPath;
    // An AI arena (tests/scenarios/mm9/ai/README.md) set up once gameplay starts.
    std::string aiArenaPath;
    // Indoor hole view (tools/indoor_hole_sweep.py): the main view clears to magenta, an open sky's faces draw as faces
    // (no sky pass), no fog and no view distance limit, so every pixel no face covers shows magenta.
    bool indoorHoleView = false;
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
    // Turn-based combat plays faster by these factors: the monsters' turns, and the party's attacks in flight
    // (GrayFace MM8Patch TurnBasedSpeed and TurnBasedPartySpeed). The party's own movement stage stays at 1.
    float turnBasedMonsterSpeed = 1.0f;
    float turnBasedPartySpeed = 1.0f;
    // The combat log button and its docked log of hits (MAW GAPS H.3); hidden, nothing is recorded
    // (GameplayScreenRuntime::combatLogShown).
    CombatLogMode combatLog = CombatLogMode::Auto;
    // The interface language (devdocs/LOCALIZATION.md): "en", the pseudo-language "qps" or a language pack's id.
    // It takes effect at the next start, when its fonts mount.
    std::string language = "en";
    std::string enemyHealthBarMode = "combat";
    std::string enemyHealthBarValues = "target";
    bool enemyHealthBarDamageTrail = true;
    bool questMarkers = false;
    // The load and save lists: false keeps Quicksave, Autosave, then the rest by name; true puts the newest first.
    bool saveListNewestFirst = false;
    // Obsidian basebar frame behind the gameplay party portraits; fullscreen overlays always draw their own strip.
    bool partyFrame = true;
    // The quick item rings: the round button at each gameplay portrait opening its ring of six quick slots, and the
    // Potion Wheel key opening the active member's ring. Off by default (user, 2026-11-02): the basebar's potion and
    // scroll buttons replace them, and the Potions key opens the potion popup instead.
    bool quickItemRings = false;
    // The potion and scroll buttons on the party basebar's end ornaments, opening the paused popups.
    bool basebarItemButtons = true;
    bool meleeHitBloodEffects = true;
    // Melee hit impact sound by struck material and a brief hitstop on the target (GameplayActorHitFeedback).
    bool meleeHitFeedback = true;
    // Slash, thrust or crush effect at the contact point of a landed melee blow.
    bool meleeHitEffects = true;
    // Brief flash over the struck creature.
    bool meleeHitFlash = false;
    // Small camera turn along the blow on critical hits and kills.
    bool meleeCameraKick = false;
    // A held Attack or Quick Cast key repeats after 0.14 s, as before 2026-11-07, instead of the original's key-repeat
    // pause of 0.5 s that lets an ordinary tap act once (OY-189).
    bool fastAttackRepeat = false;
    // A glow in the item's rarity colour around its icon in the inventory, chest and shop grids (rulesets with item
    // rarities, such as MAW; Common items have none; artifacts, relics and special items glow teal): "off", "hold"
    // (while the Show Item Rarity key, Left Alt, is held) or "always".
    std::string rarityGlow = "always";
    // HUD state the game remembers across map loads and saves: the follower panel beside the minimap (shown when the
    // party has followers) and the minimap zoom step (0 zoomed out, 1 default, 2 zoomed in).
    bool followerPanel = true;
    int minimapZoom = 1;
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    bool contextActionPopup = true;
#else
    bool contextActionPopup = false;
#endif
    SettingsFileState fileState;

    static GameSettings createDefault();
};

// The settings profile version the current code writes. Desktop (up to 2) and Android (up to 4) had separate
// sequences; from 5 on, both share one.
inline constexpr uint32_t CurrentSettingsProfileVersion = 5;

std::optional<GameSettings> loadGameSettings(const std::filesystem::path &path, std::string &error);
std::optional<std::string> getBakedLightingSetting(const GameSettings &settings, const std::string &name);
bool setBakedLightingSetting(
    GameSettings &settings, const std::string &name, const std::string &value, std::string &error);
std::optional<GameSettings> loadGameSettingsFromText(const std::string &text, std::string &error);
// Writes the player's choices (SettingsFileState) to settings.ini.tmp, keeps the previous file as settings.ini.bak and
// renames the new file into place, so an interrupted write never truncates the player's settings.
bool saveGameSettings(const std::filesystem::path &path, const GameSettings &settings, std::string &error);
// Every key the writer knows, with its current value, in section order.
std::vector<SettingsEntry> serializeGameSettings(const GameSettings &settings);
// The entries a save writes: the profile, the remembered state, the stored keys and the keys that differ from their
// defaults, followed by the unknown entries.
std::vector<SettingsEntry> settingsEntriesToSave(const GameSettings &settings);
// Forgets the player's choice for keys so they follow the defaults again. A name matches that key in any section;
// "section." matches every key of the section.
void releaseStoredSettings(GameSettings &settings, const std::vector<std::string> &names);
// Runs every migration the loaded file needs and returns whether one ran. A file written by a newer version is left
// alone, so returning to an older build after an update loses nothing.
bool migrateGameSettings(GameSettings &settings);
bool migrateLegacyAndroidSettings(GameSettings &settings);
bool migrateLegacyDesktopSettings(GameSettings &settings);
CharacterAttackTuning characterAttackTuningFromSettings(const GameSettings &settings);
uint8_t textureAnisotropyLevel(const GameSettings &settings);
float resolveViewDistanceSetting(const std::string &value, float defaultDistance);
}
