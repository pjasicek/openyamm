#include "game/ui/MenuSettingsModel.h"
#include "game/render/CombatActorHealthBarPolicy.h"
#include <algorithm>
#include <array>
#include <charconv>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
// Low is the Android default, High the desktop default and the best quality, Medium in between. Presets own these menu
// options and three INI-only terrain and sky fields; display, taste and gameplay-feel options stay the player's.
constexpr std::array<std::string_view, 3> GraphicsQualityPresets = {"low", "medium", "high"};

struct GraphicsQualityOption
{
    std::string_view id;
    std::array<std::string_view, 3> values;
};

constexpr GraphicsQualityOption GraphicsQualityOptions[] = {
    {"antialiasing", {"off", "off", "4x"}},
    {"ambient_occlusion", {"false", "false", "true"}},
    {"bloom", {"false", "true", "true"}},
    {"model_shadow_quality", {"0", "0", "2"}},
    {"terrain_decorations", {"false", "true", "true"}},
    {"terrain_anisotropy", {"2x", "4x", "8x"}},
    {"terrain_specular", {"false", "true", "true"}},
    {"wet_surfaces", {"true", "true", "true"}},
    {"weather_quality", {"medium", "high", "high"}},
    {"light_grid", {"low", "high", "high"}},
    {"water_reflections", {"true", "true", "true"}},
    {"water_reflection_size", {"256", "512", "512"}},
    {"water_sprite_reflections", {"false", "false", "true"}},
    {"water_movement_ripples", {"true", "true", "true"}},
    {"rain_ripples", {"true", "true", "true"}},
    {"view_distance", {"default", "default", "default"}},
};
constexpr std::array<int, 3> GraphicsQualityTerrainSubdivisions = {2, 4, 4};
// Anti-tiling costs about 0.1 ms of GPU time at ground level (Harmondale, 1600x900), so only High keeps it.
constexpr std::array<bool, 3> GraphicsQualityTerrainAntiTiling = {false, false, true};
constexpr std::array<float, 3> GraphicsQualitySkyResolutionScales = {0.5f, 1.0f, 1.0f};
}

std::string menuSettingValue(const GameSettings &settings, std::string_view id)
{
    if (id == "graphics_quality")
    {
        return graphicsQualityPreset(settings);
    }
    if (id == "bolster_monsters")
    {
        return settings.bolsterMonsters ? "true" : "false";
    }
    if (id == "quest_markers")
    {
        return settings.questMarkers ? "true" : "false";
    }
    if (id == "party_frame")
    {
        return settings.partyFrame ? "true" : "false";
    }
    if (id == "quick_item_rings")
    {
        return settings.quickItemRings ? "true" : "false";
    }
    if (id == "item_buttons")
    {
        return settings.basebarItemButtons ? "true" : "false";
    }
    if (id == "combat_text")
    {
        return settings.combatText ? "true" : "false";
    }
    if (id == "combat_log")
    {
        return settings.combatLog ? "true" : "false";
    }
    if (id == "turn_based_monster_speed")
    {
        return turnBasedSpeedValue(settings.turnBasedMonsterSpeed);
    }
    if (id == "turn_based_party_speed")
    {
        return turnBasedSpeedValue(settings.turnBasedPartySpeed);
    }
    if (id == "enemy_health_bars")
    {
        return settings.enemyHealthBarMode;
    }
    if (id == "enemy_health_bar_values")
    {
        return settings.enemyHealthBarValues;
    }
    if (id == "enemy_health_bar_damage_trail")
    {
        return settings.enemyHealthBarDamageTrail ? "true" : "false";
    }
    if (id == "show_hits")
    {
        return settings.showHits ? "true" : "false";
    }
    if (id == "context_action_popup")
    {
        return settings.contextActionPopup ? "true" : "false";
    }
    if (id == "rarity_glow")
    {
        return settings.rarityGlow;
    }
    if (id == "skip_event_cutscenes")
    {
        return settings.skipEventCutscenes ? "true" : "false";
    }
    if (id == "vsync")
    {
        return settings.verticalSync ? "true" : "false";
    }
    if (id == "check_for_updates")
    {
        return settings.updateCheck;
    }
    if (id == "antialiasing")
    {
        return antialiasingValue(settings.antialiasing);
    }
    if (id == "view_distance")
    {
        return settings.viewDistance;
    }
    if (id == "model_shadow_quality")
    {
        return std::to_string(settings.shadows ? settings.modelShadowQuality : 0);
    }
    if (id == "model_lods")
    {
        return settings.modelLods ? "true" : "false";
    }
    if (id == "texture_filtering")
    {
        return settings.textureFiltering ? "true" : "false";
    }
    if (id == "terrain_anisotropy")
    {
        return settings.terrainFiltering == "anisotropic" ? settings.terrainAnisotropy : "off";
    }
    if (id == "terrain_decorations")
    {
        return settings.terrainDecorations ? "true" : "false";
    }
    if (id == "water_reflections")
    {
        return settings.waterReflections ? "true" : "false";
    }
    if (id == "water_reflection_size")
    {
        return std::to_string(settings.waterReflectionSize);
    }
    if (id == "water_movement_ripples")
    {
        return settings.waterMovementRipples ? "true" : "false";
    }
    if (id == "water_sprite_reflections")
    {
        return settings.waterSpriteReflections ? "true" : "false";
    }
    if (id == "weather_quality")
    {
        return weatherQualityValue(settings.weatherQuality);
    }
    if (id == "light_grid")
    {
        return lightGridQualityValue(settings.lightGrid);
    }
    if (id == "wet_surfaces")
    {
        return settings.wetSurfaces ? "true" : "false";
    }
    if (id == "terrain_specular")
    {
        return settings.terrainSpecular ? "true" : "false";
    }
    if (id == "surface_materials")
    {
        return settings.surfaceMaterials ? "true" : "false";
    }
    if (id == "surface_parallax")
    {
        return settings.surfaceParallax ? "true" : "false";
    }
    if (id == "surface_reflections")
    {
        return settings.surfaceReflections ? "true" : "false";
    }
    if (id == "rain_ripples")
    {
        return settings.rainRipples ? "true" : "false";
    }
    if (id == "ambient_occlusion")
    {
        return settings.ambientOcclusion ? "true" : "false";
    }
    if (id == "ambient_occlusion_strength")
    {
        return std::to_string(settings.ambientOcclusionStrength);
    }
    if (id == "bloom")
    {
        return settings.bloom ? "true" : "false";
    }
    if (id == "bloom_strength")
    {
        return std::to_string(settings.bloomStrength);
    }
    if (id == "cinematic_grading")
    {
        return settings.cinematicGrading ? "true" : "false";
    }
    if (id == "cinematic_strength")
    {
        return std::to_string(settings.cinematicStrength);
    }
    if (id == "sharpening")
    {
        return std::to_string(settings.sharpening);
    }
    if (id == "colored_lights")
    {
        return settings.coloredLights ? "true" : "false";
    }
    if (id == "warm_torch_light")
    {
        return settings.warmTorchLight ? "true" : "false";
    }
    if (id == "tinting")
    {
        return settings.tinting ? "true" : "false";
    }
    if (id == "blood_splats")
    {
        return settings.bloodSplats ? "true" : "false";
    }
    if (id == "melee_hit_blood_effects")
    {
        return settings.meleeHitBloodEffects ? "true" : "false";
    }
    if (id == "melee_hit_effects")
    {
        return settings.meleeHitEffects ? "true" : "false";
    }
    if (id == "melee_hit_feedback")
    {
        return settings.meleeHitFeedback ? "true" : "false";
    }
    if (id == "melee_hit_flash")
    {
        return settings.meleeHitFlash ? "true" : "false";
    }
    if (id == "melee_camera_kick")
    {
        return settings.meleeCameraKick ? "true" : "false";
    }
    if (id == "sound_volume")
    {
        return std::to_string(settings.soundVolume);
    }
    if (id == "music_volume")
    {
        return std::to_string(settings.musicVolume);
    }
    if (id == "voice_volume")
    {
        return std::to_string(settings.voiceVolume);
    }
    if (id == "walksound")
    {
        return settings.walksound ? "true" : "false";
    }
    if (id == "repeated_voice_lines")
    {
        return repeatedVoiceLineIntervalValue(settings.repeatedVoiceLineIntervalMs);
    }
    if (id == "mouse_sensitivity")
    {
        return std::to_string(settings.mouseSensitivity);
    }
    if (id == "invert_mouse_y")
    {
        return settings.invertMouseY ? "true" : "false";
    }
    if (id == "smart_click")
    {
        return settings.smartClick ? "true" : "false";
    }
    if (id == "always_run")
    {
        return settings.alwaysRun ? "true" : "false";
    }
    if (id == "bag_number_keys")
    {
        return settings.bagNumberKeys;
    }
    if (id == "flip_on_exit")
    {
        return settings.flipOnExit ? "true" : "false";
    }
    if (id == "window_mode")
    {
        if (settings.windowMode == WindowMode::Windowed)
        {
            return "windowed";
        }
        if (settings.windowMode == WindowMode::WindowedFullscreen)
        {
            return "windowed_fullscreen";
        }
        if (settings.windowMode == WindowMode::Fullscreen)
        {
            return "fullscreen";
        }
    }
    if (id == "turn_rate")
    {
        if (settings.turnRate == TurnRateMode::X16)
        {
            return "16x";
        }
        if (settings.turnRate == TurnRateMode::X32)
        {
            return "32x";
        }
        if (settings.turnRate == TurnRateMode::Smooth)
        {
            return "smooth";
        }
    }
    if (id == "control_scheme")
    {
        if (settings.controlScheme == ControlScheme::Modern)
        {
            return "modern";
        }
        if (settings.controlScheme == ControlScheme::Classic)
        {
            return "classic";
        }
    }
    if (id == "resolution")
    {
        return std::to_string(settings.resolutionWidth) + "x" + std::to_string(settings.resolutionHeight);
    }
    throw std::invalid_argument("Unknown menu setting: " + std::string(id));
}

bool setMenuSettingValue(GameSettings &settings, std::string_view id, const std::string &value)
{
    if (id == "graphics_quality")
    {
        // Custom only names a mix of presets, so choosing it keeps the current options.
        return value == "custom" || applyGraphicsQualityPreset(settings, value);
    }
    if (id == "bolster_monsters")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.bolsterMonsters = value == "true";
        return true;
    }
    if (id == "quest_markers")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.questMarkers = value == "true";
        return true;
    }
    if (id == "party_frame")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.partyFrame = value == "true";
        return true;
    }
    if (id == "quick_item_rings" || id == "item_buttons")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        (id == "quick_item_rings" ? settings.quickItemRings : settings.basebarItemButtons) = value == "true";
        return true;
    }
    if (id == "combat_text")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.combatText = value == "true";
        return true;
    }
    if (id == "combat_log")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.combatLog = value == "true";
        return true;
    }
    if (id == "turn_based_monster_speed")
    {
        return parseTurnBasedSpeedValue(value, settings.turnBasedMonsterSpeed);
    }
    if (id == "turn_based_party_speed")
    {
        return parseTurnBasedSpeedValue(value, settings.turnBasedPartySpeed);
    }
    if (id == "enemy_health_bars")
    {
        if (!validEnemyHealthBarMode(value))
        {
            return false;
        }
        settings.enemyHealthBarMode = value;
        return true;
    }
    if (id == "enemy_health_bar_values")
    {
        if (!validEnemyHealthBarValues(value))
        {
            return false;
        }
        settings.enemyHealthBarValues = value;
        return true;
    }
    if (id == "enemy_health_bar_damage_trail")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.enemyHealthBarDamageTrail = value == "true";
        return true;
    }
    if (id == "show_hits")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.showHits = value == "true";
        return true;
    }
    if (id == "context_action_popup")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.contextActionPopup = value == "true";
        return true;
    }
    if (id == "rarity_glow")
    {
        if (!validRarityGlowValue(value))
        {
            return false;
        }
        settings.rarityGlow = value;
        return true;
    }
    if (id == "skip_event_cutscenes")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.skipEventCutscenes = value == "true";
        return true;
    }
    if (id == "vsync")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.verticalSync = value == "true";
        return true;
    }
    if (id == "check_for_updates")
    {
        if (value != "ask" && value != "auto" && value != "off")
        {
            return false;
        }
        settings.updateCheck = value;
        return true;
    }
    if (id == "antialiasing")
    {
        if (value != "off" && value != "2x" && value != "4x")
        {
            return false;
        }
        return parseAntialiasingValue(value, settings.antialiasing);
    }
    if (id == "view_distance")
    {
        if (value != "default" && value != "32768" && value != "unlimited")
        {
            return false;
        }
        settings.viewDistance = value;
        return true;
    }
    if (id == "model_shadow_quality")
    {
        if (value != "0" && value != "1" && value != "2" && value != "3")
        {
            return false;
        }
        settings.modelShadowQuality = value[0] - '0';
        settings.shadows = settings.modelShadowQuality != 0;
        return true;
    }
    if (id == "model_lods")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.modelLods = value == "true";
        return true;
    }
    if (id == "texture_filtering")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.textureFiltering = value == "true";
        return true;
    }
    if (id == "terrain_anisotropy")
    {
        if (value == "off")
        {
            settings.terrainFiltering = "linear";
            return true;
        }
        if (value != "2x" && value != "4x" && value != "8x" && value != "16x")
        {
            return false;
        }
        settings.terrainAnisotropy = value;
        settings.terrainFiltering = "anisotropic";
        return true;
    }
    if (id == "terrain_decorations")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.terrainDecorations = value == "true";
        return true;
    }
    if (id == "water_reflections" || id == "water_sprite_reflections" || id == "water_movement_ripples")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        if (id == "water_reflections")
        {
            settings.waterReflections = value == "true";
        }
        else if (id == "water_movement_ripples")
        {
            settings.waterMovementRipples = value == "true";
        }
        else
        {
            settings.waterSpriteReflections = value == "true";
        }
        return true;
    }
    if (id == "weather_quality")
    {
        return parseWeatherQualityValue(value, settings.weatherQuality);
    }
    if (id == "light_grid")
    {
        return parseLightGridQualityValue(value, settings.lightGrid);
    }
    if (id == "wet_surfaces" || id == "rain_ripples" || id == "terrain_specular" || id == "surface_materials"
        || id == "surface_parallax" || id == "surface_reflections")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        (id == "wet_surfaces" ? settings.wetSurfaces
            : id == "rain_ripples" ? settings.rainRipples
            : id == "terrain_specular" ? settings.terrainSpecular
            : id == "surface_materials" ? settings.surfaceMaterials
            : id == "surface_parallax" ? settings.surfaceParallax : settings.surfaceReflections) = value == "true";
        return true;
    }
    if (id == "water_reflection_size")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size()
            || (number != 128 && number != 256 && number != 512 && number != 1024 && number != 2048))
        {
            return false;
        }
        settings.waterReflectionSize = number;
        return true;
    }
    if (id == "ambient_occlusion")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.ambientOcclusion = value == "true";
        return true;
    }
    if (id == "ambient_occlusion_strength")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || number < 0 || number > 100)
        {
            return false;
        }
        settings.ambientOcclusionStrength = number;
        return true;
    }
    if (id == "bloom")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.bloom = value == "true";
        return true;
    }
    if (id == "bloom_strength")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || number < 0 || number > 100)
        {
            return false;
        }
        settings.bloomStrength = number;
        return true;
    }
    if (id == "cinematic_grading")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.cinematicGrading = value == "true";
        return true;
    }
    if (id == "cinematic_strength")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || number < 0 || number > 100)
        {
            return false;
        }
        settings.cinematicStrength = number;
        return true;
    }
    if (id == "sharpening")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || number < 0 || number > 100)
        {
            return false;
        }
        settings.sharpening = number;
        return true;
    }
    if (id == "colored_lights")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.coloredLights = value == "true";
        return true;
    }
    if (id == "warm_torch_light")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.warmTorchLight = value == "true";
        return true;
    }
    if (id == "tinting")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.tinting = value == "true";
        return true;
    }
    if (id == "blood_splats")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.bloodSplats = value == "true";
        return true;
    }
    if (id == "melee_hit_blood_effects")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.meleeHitBloodEffects = value == "true";
        return true;
    }
    if (id == "melee_hit_effects")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.meleeHitEffects = value == "true";
        return true;
    }
    if (id == "melee_hit_feedback")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.meleeHitFeedback = value == "true";
        return true;
    }
    if (id == "melee_hit_flash")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.meleeHitFlash = value == "true";
        return true;
    }
    if (id == "melee_camera_kick")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.meleeCameraKick = value == "true";
        return true;
    }
    if (id == "sound_volume")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || number < 0 || number > 9)
        {
            return false;
        }
        settings.soundVolume = number;
        return true;
    }
    if (id == "music_volume")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || number < 0 || number > 9)
        {
            return false;
        }
        settings.musicVolume = number;
        return true;
    }
    if (id == "voice_volume")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || number < 0 || number > 9)
        {
            return false;
        }
        settings.voiceVolume = number;
        return true;
    }
    if (id == "walksound")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.walksound = value == "true";
        return true;
    }
    if (id == "repeated_voice_lines")
    {
        return parseRepeatedVoiceLineIntervalValue(value, settings.repeatedVoiceLineIntervalMs);
    }
    if (id == "mouse_sensitivity")
    {
        int number = 0;
        const auto result = std::from_chars(value.data(), value.data() + value.size(), number);
        if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || number < 0 || number > 100)
        {
            return false;
        }
        settings.mouseSensitivity = number;
        return true;
    }
    if (id == "invert_mouse_y")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.invertMouseY = value == "true";
        return true;
    }
    if (id == "smart_click")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.smartClick = value == "true";
        return true;
    }
    if (id == "always_run")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.alwaysRun = value == "true";
        return true;
    }
    if (id == "bag_number_keys")
    {
        if (!validBagNumberKeysValue(value))
        {
            return false;
        }
        settings.bagNumberKeys = value;
        return true;
    }
    if (id == "flip_on_exit")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.flipOnExit = value == "true";
        return true;
    }
    if (id == "window_mode")
    {
        if (value == "windowed")
        {
            settings.windowMode = WindowMode::Windowed;
        }
        else if (value == "windowed_fullscreen")
        {
            settings.windowMode = WindowMode::WindowedFullscreen;
        }
        else if (value == "fullscreen")
        {
            settings.windowMode = WindowMode::Fullscreen;
        }
        else
        {
            return false;
        }
        return true;
    }
    if (id == "turn_rate")
    {
        if (value == "16x")
        {
            settings.turnRate = TurnRateMode::X16;
        }
        else if (value == "32x")
        {
            settings.turnRate = TurnRateMode::X32;
        }
        else if (value == "smooth")
        {
            settings.turnRate = TurnRateMode::Smooth;
        }
        else
        {
            return false;
        }
        return true;
    }
    if (id == "control_scheme")
    {
        if (value == "modern")
        {
            settings.controlScheme = ControlScheme::Modern;
        }
        else if (value == "classic")
        {
            settings.controlScheme = ControlScheme::Classic;
        }
        else
        {
            return false;
        }
        return true;
    }
    if (id == "resolution")
    {
        const size_t separator = value.find('x');
        if (separator == std::string::npos)
        {
            return false;
        }
        int width = 0, height = 0;
        const auto x = std::from_chars(value.data(), value.data() + separator, width);
        const auto y = std::from_chars(value.data() + separator + 1, value.data() + value.size(), height);
        if (x.ec != std::errc{} || y.ec != std::errc{} || x.ptr != value.data() + separator ||
            y.ptr != value.data() + value.size() || width < 640 || height < 480 || width > 16384 || height > 16384)
        {
            return false;
        }
        settings.resolutionWidth = width;
        settings.resolutionHeight = height;
        return true;
    }
    return false;
}

std::string graphicsQualityPreset(const GameSettings &settings)
{
    for (size_t preset = 0; preset < GraphicsQualityPresets.size(); ++preset)
    {
        bool matches = settings.terrainSubdivision == GraphicsQualityTerrainSubdivisions[preset]
            && settings.terrainAntiTiling == GraphicsQualityTerrainAntiTiling[preset]
            && settings.skyResolutionScale == GraphicsQualitySkyResolutionScales[preset];
        for (const GraphicsQualityOption &option : GraphicsQualityOptions)
        {
            matches = matches && menuSettingValue(settings, option.id) == option.values[preset];
        }
        if (matches)
        {
            return std::string(GraphicsQualityPresets[preset]);
        }
    }
    return "custom";
}

bool applyGraphicsQualityPreset(GameSettings &settings, std::string_view preset)
{
    const auto found = std::find(GraphicsQualityPresets.begin(), GraphicsQualityPresets.end(), preset);
    if (found == GraphicsQualityPresets.end())
    {
        return false;
    }
    const size_t index = size_t(found - GraphicsQualityPresets.begin());
    for (const GraphicsQualityOption &option : GraphicsQualityOptions)
    {
        if (!setMenuSettingValue(settings, option.id, std::string(option.values[index])))
        {
            throw std::logic_error("Invalid graphics quality value for " + std::string(option.id));
        }
    }
    settings.terrainSubdivision = GraphicsQualityTerrainSubdivisions[index];
    settings.terrainAntiTiling = GraphicsQualityTerrainAntiTiling[index];
    settings.skyResolutionScale = GraphicsQualitySkyResolutionScales[index];
    return true;
}

bool sameMenuBinding(const InputBinding &left, const InputBinding &right)
{
    return left.kind == right.kind &&
           (left.kind == InputBindingKind::Keyboard      ? left.scancode == right.scancode
            : left.kind == InputBindingKind::MouseButton ? left.mouseButton == right.mouseButton
                                                         : true);
}

bool reservedMenuBinding(const InputBinding &binding, KeyboardAction action)
{
    if (binding.kind != InputBindingKind::Keyboard)
    {
        return false;
    }
    const bool bagKey = action >= KeyboardAction::Bag1 && action <= KeyboardAction::Bag4;
    return binding.scancode == SDL_SCANCODE_ESCAPE || binding.scancode == SDL_SCANCODE_GRAVE ||
           (!bagKey && binding.scancode >= SDL_SCANCODE_1 && binding.scancode <= SDL_SCANCODE_5);
}
} // namespace OpenYAMM::Game
