#include "game/ui/MenuSettingsModel.h"
#include "game/render/CombatActorHealthBarPolicy.h"
#include <charconv>
#include <stdexcept>

namespace OpenYAMM::Game
{
std::string menuSettingValue(const GameSettings &settings, std::string_view id)
{
    if (id == "bolster_monsters")
    {
        return settings.bolsterMonsters ? "true" : "false";
    }
    if (id == "quest_markers")
    {
        return settings.questMarkers ? "true" : "false";
    }
    if (id == "combat_text")
    {
        return settings.combatText ? "true" : "false";
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
    if (id == "skip_event_cutscenes")
    {
        return settings.skipEventCutscenes ? "true" : "false";
    }
    if (id == "vsync")
    {
        return settings.verticalSync ? "true" : "false";
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
    if (id == "water_shader")
    {
        return settings.waterShader ? "true" : "false";
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
    if (id == "cinematic_grading")
    {
        return settings.cinematicGrading ? "true" : "false";
    }
    if (id == "cinematic_strength")
    {
        return std::to_string(settings.cinematicStrength);
    }
    if (id == "colored_lights")
    {
        return settings.coloredLights ? "true" : "false";
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
    if (id == "mouse_sensitivity")
    {
        return std::to_string(settings.mouseSensitivity);
    }
    if (id == "invert_mouse_y")
    {
        return settings.invertMouseY ? "true" : "false";
    }
    if (id == "always_run")
    {
        return settings.alwaysRun ? "true" : "false";
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
    if (id == "combat_text")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.combatText = value == "true";
        return true;
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
    if (id == "water_shader" || id == "water_reflections" || id == "water_sprite_reflections"
        || id == "water_movement_ripples")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        if (id == "water_shader")
        {
            settings.waterShader = value == "true";
        }
        else if (id == "water_reflections")
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
    if (id == "colored_lights")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.coloredLights = value == "true";
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
    if (id == "always_run")
    {
        if (value != "true" && value != "false")
        {
            return false;
        }
        settings.alwaysRun = value == "true";
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

bool sameMenuBinding(const InputBinding &left, const InputBinding &right)
{
    return left.kind == right.kind &&
           (left.kind == InputBindingKind::Keyboard      ? left.scancode == right.scancode
            : left.kind == InputBindingKind::MouseButton ? left.mouseButton == right.mouseButton
                                                         : true);
}

bool reservedMenuBinding(const InputBinding &binding)
{
    if (binding.kind != InputBindingKind::Keyboard)
    {
        return false;
    }
    return binding.scancode == SDL_SCANCODE_ESCAPE || binding.scancode == SDL_SCANCODE_F9 ||
           binding.scancode == SDL_SCANCODE_F10 || binding.scancode == SDL_SCANCODE_GRAVE ||
           (binding.scancode >= SDL_SCANCODE_1 && binding.scancode <= SDL_SCANCODE_5);
}
} // namespace OpenYAMM::Game
