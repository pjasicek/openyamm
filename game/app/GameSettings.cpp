#include "game/app/GameSettings.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MinimumViewDistance = 1024.0f;
constexpr float UnlimitedViewDistance = 200000.0f;

using IniSection = std::unordered_map<std::string, std::string>;
using IniDocument = std::unordered_map<std::string, IniSection>;

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;
    size_t end = value.size();

    while (begin < end && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

bool parseBoolValue(const std::string &value, bool &result)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "1" || normalized == "true" || normalized == "yes" || normalized == "on")
    {
        result = true;
        return true;
    }

    if (normalized == "0" || normalized == "false" || normalized == "no" || normalized == "off")
    {
        result = false;
        return true;
    }

    return false;
}

bool parseBlasterSkillScalingValue(const std::string &value, BlasterSkillScalingMode &result)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "default")
    {
        result = BlasterSkillScalingMode::Default;
        return true;
    }

    if (normalized == "scaling_damage")
    {
        result = BlasterSkillScalingMode::ScalingDamage;
        return true;
    }

    return false;
}

std::string blasterSkillScalingValue(BlasterSkillScalingMode mode)
{
    switch (mode)
    {
        case BlasterSkillScalingMode::ScalingDamage:
            return "scaling_damage";

        case BlasterSkillScalingMode::Default:
        default:
            return "default";
    }
}

bool parseIntValue(const std::string &value, int &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const long parsed = std::strtol(trimmed.c_str(), &pEnd, 10);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    result = static_cast<int>(parsed);
    return true;
}

bool parseBlasterMinimumRecoveryTicksValue(const std::string &value, int &result)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "default")
    {
        result = 0;
        return true;
    }

    int parsed = result;

    if (!parseIntValue(value, parsed))
    {
        return false;
    }

    result = std::clamp(parsed, 0, 300);
    return true;
}

std::string blasterMinimumRecoveryTicksValue(int ticks)
{
    const int clampedTicks = std::clamp(ticks, 0, 300);
    return clampedTicks == 0 ? std::string("default") : std::to_string(clampedTicks);
}

bool parseUInt32Value(const std::string &value, uint32_t &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(trimmed.c_str(), &pEnd, 10);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    result = static_cast<uint32_t>(parsed);
    return true;
}

bool parseFloatValue(const std::string &value, float &result)
{
    const std::string trimmed = trimCopy(value);

    if (trimmed.empty())
    {
        return false;
    }

    char *pEnd = nullptr;
    const float parsed = std::strtof(trimmed.c_str(), &pEnd);

    if (pEnd == nullptr || *pEnd != '\0')
    {
        return false;
    }

    result = parsed;
    return true;
}

std::optional<std::string> getIniValue(const IniDocument &document, const std::string &section, const std::string &key)
{
    const auto sectionIt = document.find(section);

    if (sectionIt == document.end())
    {
        return std::nullopt;
    }

    const auto valueIt = sectionIt->second.find(key);

    if (valueIt == sectionIt->second.end())
    {
        return std::nullopt;
    }

    return valueIt->second;
}

IniDocument parseIniDocument(const std::string &text)
{
    IniDocument document;
    std::string currentSection = "global";
    std::istringstream stream(text);
    std::string line;

    while (std::getline(stream, line))
    {
        const std::string trimmed = trimCopy(line);

        if (trimmed.empty() || trimmed[0] == ';' || trimmed[0] == '#')
        {
            continue;
        }

        if (trimmed.size() >= 3 && trimmed.front() == '[' && trimmed.back() == ']')
        {
            currentSection = toLowerCopy(trimCopy(trimmed.substr(1, trimmed.size() - 2)));
            continue;
        }

        const size_t separatorPos = trimmed.find('=');

        if (separatorPos == std::string::npos)
        {
            continue;
        }

        const std::string key = toLowerCopy(trimCopy(trimmed.substr(0, separatorPos)));
        const std::string value = trimCopy(trimmed.substr(separatorPos + 1));

        if (!key.empty())
        {
            document[currentSection][key] = value;
        }
    }

    return document;
}

std::string turnRateModeString(TurnRateMode mode)
{
    switch (mode)
    {
    case TurnRateMode::X16:
        return "16x";

    case TurnRateMode::X32:
        return "32x";

    case TurnRateMode::Smooth:
        return "smooth";
    }

    return "32x";
}

std::string gameplayUiLayoutString(GameplayUiLayout layout)
{
    switch (layout)
    {
    case GameplayUiLayout::Standard:
        return "standard";

    case GameplayUiLayout::Widescreen:
        return "widescreen";
    }

    return "widescreen";
}

std::string windowModeString(WindowMode mode)
{
    switch (mode)
    {
    case WindowMode::Windowed:
        return "windowed";

    case WindowMode::WindowedFullscreen:
        return "windowed_fullscreen";

    case WindowMode::Fullscreen:
        return "fullscreen";
    }

    return "windowed";
}

std::string controlSchemeString(ControlScheme scheme)
{
    switch (scheme)
    {
    case ControlScheme::Classic:
        return "classic";

    case ControlScheme::Modern:
    default:
        return "modern";
    }
}

TurnRateMode parseTurnRateMode(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "16x")
    {
        return TurnRateMode::X16;
    }

    if (normalized == "smooth")
    {
        return TurnRateMode::Smooth;
    }

    return TurnRateMode::X32;
}

ControlScheme parseControlScheme(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "classic" || normalized == "oe" || normalized == "standard")
    {
        return ControlScheme::Classic;
    }

    return ControlScheme::Modern;
}

GameplayUiLayout parseGameplayUiLayout(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "standard")
    {
        return GameplayUiLayout::Standard;
    }

    return GameplayUiLayout::Widescreen;
}

WindowMode parseWindowMode(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "fullscreen")
    {
        return WindowMode::Fullscreen;
    }

    if (normalized == "windowed_fullscreen"
        || normalized == "windowed-fullscreen"
        || normalized == "borderless")
    {
        return WindowMode::WindowedFullscreen;
    }

    return WindowMode::Windowed;
}

bool parseResolutionValue(const std::string &value, int &width, int &height)
{
    const std::string normalized = toLowerCopy(trimCopy(value));
    const size_t separatorPos = normalized.find('x');

    if (separatorPos == std::string::npos)
    {
        return false;
    }

    int parsedWidth = 0;
    int parsedHeight = 0;

    if (!parseIntValue(normalized.substr(0, separatorPos), parsedWidth)
        || !parseIntValue(normalized.substr(separatorPos + 1), parsedHeight))
    {
        return false;
    }

    if (parsedWidth <= 0 || parsedHeight <= 0)
    {
        return false;
    }

    width = parsedWidth;
    height = parsedHeight;
    return true;
}

void parseAssetScaleProfileValue(
    const IniDocument &document,
    const std::string &key,
    Engine::AssetScaleProfile &assetScaleProfile,
    Engine::AssetScaleCategory assetScaleCategory)
{
    const std::optional<std::string> value = getIniValue(document, "video_quality", key);

    if (!value)
    {
        return;
    }

    const std::optional<Engine::AssetScaleTier> assetScaleTier = Engine::parseAssetScaleTier(*value);

    if (assetScaleTier)
    {
        Engine::setAssetScaleTierForCategory(assetScaleProfile, assetScaleCategory, *assetScaleTier);
    }
}
}

GameSettings GameSettings::createDefault()
{
    GameSettings settings;
    settings.keyboard.restoreDefaults(settings.controlScheme);
    return settings;
}

float resolveViewDistanceSetting(const std::string &value, float defaultDistance)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized.empty() || normalized == "default")
    {
        return defaultDistance;
    }

    if (normalized == "unlimited")
    {
        return UnlimitedViewDistance;
    }

    float parsed = defaultDistance;

    if (!parseFloatValue(normalized, parsed) || parsed <= 0.0f)
    {
        return defaultDistance;
    }

    return std::clamp(parsed, MinimumViewDistance, UnlimitedViewDistance);
}

CharacterAttackTuning characterAttackTuningFromSettings(const GameSettings &settings)
{
    CharacterAttackTuning tuning = {};
    tuning.blasterSkillScaling = settings.blasterSkillScaling;
    tuning.blasterMinimumRecoveryTicks = std::clamp(settings.blasterMinimumRecoveryTicks, 0, 300);
    return tuning;
}

std::optional<GameSettings> loadGameSettings(const std::filesystem::path &path, std::string &error)
{
    std::ifstream input(path);

    if (!input)
    {
        error = "Unable to open settings file";
        return std::nullopt;
    }

    std::ostringstream buffer;
    buffer << input.rdbuf();
    const IniDocument document = parseIniDocument(buffer.str());
    GameSettings settings = GameSettings::createDefault();

    if (const std::optional<std::string> value = getIniValue(document, "assets", "root"))
    {
        settings.assetRoot = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "audio", "sound_volume"))
    {
        int parsed = settings.soundVolume;

        if (parseIntValue(*value, parsed))
        {
            settings.soundVolume = std::clamp(parsed, 0, 9);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "audio", "music_volume"))
    {
        int parsed = settings.musicVolume;

        if (parseIntValue(*value, parsed))
        {
            settings.musicVolume = std::clamp(parsed, 0, 9);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "audio", "voice_volume"))
    {
        int parsed = settings.voiceVolume;

        if (parseIntValue(*value, parsed))
        {
            settings.voiceVolume = std::clamp(parsed, 0, 9);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "turn_rate"))
    {
        settings.turnRate = parseTurnRateMode(*value);
    }

    const std::optional<std::string> controlSchemeValue = getIniValue(document, "controls", "control_scheme");

    if (controlSchemeValue)
    {
        settings.controlScheme = parseControlScheme(*controlSchemeValue);
        settings.keyboard.restoreDefaults(settings.controlScheme);
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "walksound"))
    {
        bool parsed = settings.walksound;

        if (parseBoolValue(*value, parsed))
        {
            settings.walksound = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "walk_sound"))
    {
        bool parsed = settings.walksound;

        if (parseBoolValue(*value, parsed))
        {
            settings.walksound = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "show_hits"))
    {
        bool parsed = settings.showHits;

        if (parseBoolValue(*value, parsed))
        {
            settings.showHits = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "always_run"))
    {
        bool parsed = settings.alwaysRun;

        if (parseBoolValue(*value, parsed))
        {
            settings.alwaysRun = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "flip_on_exit"))
    {
        bool parsed = settings.flipOnExit;

        if (parseBoolValue(*value, parsed))
        {
            settings.flipOnExit = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "controls", "mouse_sensitivity"))
    {
        int parsed = settings.mouseSensitivity;

        if (parseIntValue(*value, parsed))
        {
            settings.mouseSensitivity = std::clamp(parsed, 0, 100);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "keyboard_interaction_depth"))
    {
        int parsed = settings.keyboardInteractionDepth;

        if (parseIntValue(*value, parsed))
        {
            settings.keyboardInteractionDepth = std::clamp(parsed, 32, 4096);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "mouse_interaction_depth"))
    {
        int parsed = settings.mouseInteractionDepth;

        if (parseIntValue(*value, parsed))
        {
            settings.mouseInteractionDepth = std::clamp(parsed, 32, 4096);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "context_action_popup"))
    {
        bool parsed = settings.contextActionPopup;

        if (parseBoolValue(*value, parsed))
        {
            settings.contextActionPopup = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "blood_splats"))
    {
        bool parsed = settings.bloodSplats;

        if (parseBoolValue(*value, parsed))
        {
            settings.bloodSplats = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "colored_lights"))
    {
        bool parsed = settings.coloredLights;

        if (parseBoolValue(*value, parsed))
        {
            settings.coloredLights = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "tinting"))
    {
        bool parsed = settings.tinting;

        if (parseBoolValue(*value, parsed))
        {
            settings.tinting = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "shadows"))
    {
        bool parsed = settings.shadows;

        if (parseBoolValue(*value, parsed))
        {
            settings.shadows = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "sprite_outline"))
    {
        bool parsed = settings.spriteOutline;

        if (parseBoolValue(*value, parsed))
        {
            settings.spriteOutline = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "texture_filtering"))
    {
        bool parsed = settings.textureFiltering;

        if (parseBoolValue(*value, parsed))
        {
            settings.textureFiltering = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "terrain_filtering"))
    {
        settings.terrainFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "terrain_anisotropy"))
    {
        settings.terrainAnisotropy = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "bmodel_filtering"))
    {
        settings.bmodelFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "billboard_filtering"))
    {
        settings.billboardFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "ui_filtering"))
    {
        settings.uiFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "text_filtering"))
    {
        settings.textFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "minimap_filtering"))
    {
        settings.minimapFiltering = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "view_distance"))
    {
        settings.viewDistance = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "outdoor_billboard_depth_slice"))
    {
        float parsed = settings.outdoorBillboardDepthSlice;

        if (parseFloatValue(*value, parsed))
        {
            settings.outdoorBillboardDepthSlice = std::clamp(parsed, 0.0f, 8192.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "skip_event_cutscenes"))
    {
        bool parsed = settings.skipEventCutscenes;

        if (parseBoolValue(*value, parsed))
        {
            settings.skipEventCutscenes = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "gameplay_ui_layout"))
    {
        settings.gameplayUiLayout = parseGameplayUiLayout(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "window_mode"))
    {
        settings.windowMode = parseWindowMode(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "resolution"))
    {
        int parsedWidth = settings.resolutionWidth;
        int parsedHeight = settings.resolutionHeight;

        if (parseResolutionValue(*value, parsedWidth, parsedHeight))
        {
            settings.resolutionWidth = std::clamp(parsedWidth, 320, 16384);
            settings.resolutionHeight = std::clamp(parsedHeight, 200, 16384);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "vsync"))
    {
        bool parsed = settings.verticalSync;

        if (parseBoolValue(*value, parsed))
        {
            settings.verticalSync = parsed;
        }
    }

    parseAssetScaleProfileValue(
        document,
        "texture",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Textures);
    parseAssetScaleProfileValue(
        document,
        "textures",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Textures);
    parseAssetScaleProfileValue(
        document,
        "terrain",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Terrain);
    parseAssetScaleProfileValue(
        document,
        "sky",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Sky);
    parseAssetScaleProfileValue(
        document,
        "sprites",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Sprites);
    parseAssetScaleProfileValue(
        document,
        "decorations",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Decorations);
    parseAssetScaleProfileValue(
        document,
        "icons",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Icons);
    parseAssetScaleProfileValue(
        document,
        "ui",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Ui);
    parseAssetScaleProfileValue(
        document,
        "effects",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Effects);
    parseAssetScaleProfileValue(
        document,
        "fonts",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Fonts);

    if (const std::optional<std::string> value = getIniValue(document, "startup", "start_in_main_menu"))
    {
        bool parsed = settings.startInMainMenu;

        if (parseBoolValue(*value, parsed))
        {
            settings.startInMainMenu = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "features", "bolster_monsters"))
    {
        bool parsed = settings.bolsterMonsters;

        if (parseBoolValue(*value, parsed))
        {
            settings.bolsterMonsters = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "features", "indoor_pathfinding"))
    {
        bool parsed = settings.indoorPathfinding;

        if (parseBoolValue(*value, parsed))
        {
            settings.indoorPathfinding = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "features", "blaster_skill_scaling"))
    {
        BlasterSkillScalingMode parsed = settings.blasterSkillScaling;

        if (parseBlasterSkillScalingValue(*value, parsed))
        {
            settings.blasterSkillScaling = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "features", "blaster_min_recovery"))
    {
        int parsed = settings.blasterMinimumRecoveryTicks;

        if (parseBlasterMinimumRecoveryTicksValue(*value, parsed))
        {
            settings.blasterMinimumRecoveryTicks = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "indoor_visibility"))
    {
        bool parsed = settings.logIndoorVisibility;

        if (parseBoolValue(*value, parsed))
        {
            settings.logIndoorVisibility = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "indoor_pathfinding"))
    {
        bool parsed = settings.logIndoorPathfinding;

        if (parseBoolValue(*value, parsed))
        {
            settings.logIndoorPathfinding = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "fps_trace"))
    {
        bool parsed = settings.fpsTrace;

        if (parseBoolValue(*value, parsed))
        {
            settings.fpsTrace = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "performance_trace"))
    {
        bool parsed = settings.performanceTrace;

        if (parseBoolValue(*value, parsed))
        {
            settings.performanceTrace = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "hitch_trace"))
    {
        bool parsed = settings.hitchTrace;

        if (parseBoolValue(*value, parsed))
        {
            settings.hitchTrace = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "collision_trace"))
    {
        bool parsed = settings.collisionTrace;

        if (parseBoolValue(*value, parsed))
        {
            settings.collisionTrace = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "gameplay_trace"))
    {
        bool parsed = settings.gameplayTrace;

        if (parseBoolValue(*value, parsed))
        {
            settings.gameplayTrace = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "gameplay_trace_file"))
    {
        settings.gameplayTraceFile = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "gameplay_trace_append"))
    {
        bool parsed = settings.gameplayTraceAppend;

        if (parseBoolValue(*value, parsed))
        {
            settings.gameplayTraceAppend = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "combat_trace"))
    {
        bool parsed = settings.combatTrace;

        if (parseBoolValue(*value, parsed))
        {
            settings.combatTrace = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "combat_trace_file"))
    {
        settings.combatTraceFile = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "combat_trace_append"))
    {
        bool parsed = settings.combatTraceAppend;

        if (parseBoolValue(*value, parsed))
        {
            settings.combatTraceAppend = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "logging", "hitch_threshold_ms"))
    {
        float parsed = settings.hitchThresholdMilliseconds;

        if (parseFloatValue(*value, parsed))
        {
            settings.hitchThresholdMilliseconds = std::clamp(parsed, 0.1f, 1000.0f);
        }
    }

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        std::optional<std::string> value = getIniValue(document, "input", std::string(definition.iniKey));

        if (!value.has_value() && !controlSchemeValue.has_value())
        {
            value = getIniValue(document, "keyboard", std::string(definition.iniKey));
        }

        if (!value.has_value())
        {
            continue;
        }

        const InputBinding binding = parseInputBindingName(trimCopy(*value));

        if (binding.kind != InputBindingKind::None)
        {
            settings.keyboard.setBinding(definition.action, binding);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "preseed_party"))
    {
        bool parsed = settings.preseedParty;

        if (parseBoolValue(*value, parsed))
        {
            settings.preseedParty = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "party_seed_roster_id"))
    {
        uint32_t parsed = settings.partySeedRosterId;

        if (parseUInt32Value(*value, parsed))
        {
            settings.partySeedRosterId = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_world"))
    {
        const std::string trimmed = toLowerCopy(trimCopy(*value));

        if (!trimmed.empty())
        {
            settings.startWorldId = trimmed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_map_file"))
    {
        const std::string trimmed = trimCopy(*value);
        settings.startMapFile = trimmed;
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "override_start_position"))
    {
        bool parsed = settings.overrideStartPosition;

        if (parseBoolValue(*value, parsed))
        {
            settings.overrideStartPosition = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_x"))
    {
        float parsed = settings.startX;

        if (parseFloatValue(*value, parsed))
        {
            settings.startX = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_y"))
    {
        float parsed = settings.startY;

        if (parseFloatValue(*value, parsed))
        {
            settings.startY = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_z"))
    {
        float parsed = settings.startZ;

        if (parseFloatValue(*value, parsed))
        {
            settings.startZ = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "start_flying"))
    {
        bool parsed = settings.startFlying;

        if (parseBoolValue(*value, parsed))
        {
            settings.startFlying = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "movement_speed_multiplier"))
    {
        float parsed = settings.movementSpeedMultiplier;

        if (parseFloatValue(*value, parsed))
        {
            settings.movementSpeedMultiplier = std::clamp(parsed, 0.1f, 20.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "immortal"))
    {
        bool parsed = settings.immortal;

        if (parseBoolValue(*value, parsed))
        {
            settings.immortal = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "unlimited_mana"))
    {
        bool parsed = settings.unlimitedMana;

        if (parseBoolValue(*value, parsed))
        {
            settings.unlimitedMana = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "new_game_god_lich"))
    {
        bool parsed = settings.newGameGodLich;

        if (parseBoolValue(*value, parsed))
        {
            settings.newGameGodLich = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "allow_incomplete_character_creation"))
    {
        bool parsed = settings.allowIncompleteCharacterCreation;

        if (parseBoolValue(*value, parsed))
        {
            settings.allowIncompleteCharacterCreation = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "console"))
    {
        bool parsed = settings.debugConsole;

        if (parseBoolValue(*value, parsed))
        {
            settings.debugConsole = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "enabled"))
    {
        bool parsed = settings.arpgModeEnabled;

        if (parseBoolValue(*value, parsed))
        {
            settings.arpgModeEnabled = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "player_monster_descriptor"))
    {
        const std::string trimmed = trimCopy(*value);

        if (!trimmed.empty())
        {
            settings.arpgModePlayerMonsterDescriptor = trimmed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "camera_yaw_degrees"))
    {
        float parsed = settings.arpgModeCameraYawDegrees;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeCameraYawDegrees = std::clamp(parsed, -360.0f, 360.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "camera_pitch_degrees"))
    {
        float parsed = settings.arpgModeCameraPitchDegrees;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeCameraPitchDegrees = std::clamp(parsed, -85.0f, -5.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "camera_distance"))
    {
        float parsed = settings.arpgModeCameraDistance;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeCameraDistance = std::clamp(parsed, 256.0f, 20000.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "camera_target_height"))
    {
        float parsed = settings.arpgModeCameraTargetHeight;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeCameraTargetHeight = std::clamp(parsed, -512.0f, 2048.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "camera_fov_degrees"))
    {
        float parsed = settings.arpgModeCameraFovDegrees;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeCameraFovDegrees = std::clamp(parsed, 20.0f, 90.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "camera_follow_lerp"))
    {
        float parsed = settings.arpgModeCameraFollowLerp;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeCameraFollowLerp = std::clamp(parsed, 0.1f, 60.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "click_stop_radius"))
    {
        float parsed = settings.arpgModeClickStopRadius;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeClickStopRadius = std::clamp(parsed, 4.0f, 512.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "move_speed_multiplier"))
    {
        float parsed = settings.arpgModeMoveSpeedMultiplier;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeMoveSpeedMultiplier = std::clamp(parsed, 0.1f, 10.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "spell_animation_seconds"))
    {
        float parsed = settings.arpgModeSpellAnimationSeconds;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeSpellAnimationSeconds = std::clamp(parsed, 0.05f, 10.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "spell_release_seconds"))
    {
        float parsed = settings.arpgModeSpellReleaseSeconds;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeSpellReleaseSeconds = std::clamp(parsed, 0.0f, 10.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "attack_animation_min_seconds"))
    {
        float parsed = settings.arpgModeAttackAnimationMinSeconds;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeAttackAnimationMinSeconds = std::clamp(parsed, 0.05f, 10.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "attack_animation_max_seconds"))
    {
        float parsed = settings.arpgModeAttackAnimationMaxSeconds;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeAttackAnimationMaxSeconds = std::clamp(parsed, 0.05f, 10.0f);
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "arpg_mode", "attack_animation_recovery_scale"))
    {
        float parsed = settings.arpgModeAttackAnimationRecoveryScale;

        if (parseFloatValue(*value, parsed))
        {
            settings.arpgModeAttackAnimationRecoveryScale = std::clamp(parsed, 0.0f, 10.0f);
        }
    }

    if (settings.arpgModeAttackAnimationMaxSeconds < settings.arpgModeAttackAnimationMinSeconds)
    {
        settings.arpgModeAttackAnimationMaxSeconds = settings.arpgModeAttackAnimationMinSeconds;
    }

    if (settings.arpgModeEnabled)
    {
        settings.newGameGodLich = true;
    }

    error.clear();
    return settings;
}

bool saveGameSettings(const std::filesystem::path &path, const GameSettings &settings, std::string &error)
{
    std::ofstream output(path);

    if (!output)
    {
        error = "Unable to write settings file";
        return false;
    }

    output
        << "; OpenYAMM settings\n"
        << "; Volumes use the original-style 0..9 scale.\n\n"
        << "[assets]\n"
        << "root=" << settings.assetRoot << "\n\n"
        << "[audio]\n"
        << "sound_volume=" << std::clamp(settings.soundVolume, 0, 9) << '\n'
        << "music_volume=" << std::clamp(settings.musicVolume, 0, 9) << '\n'
        << "voice_volume=" << std::clamp(settings.voiceVolume, 0, 9) << "\n\n"
        << "[controls]\n"
        << "turn_rate=" << turnRateModeString(settings.turnRate) << '\n'
        << "control_scheme=" << controlSchemeString(settings.controlScheme) << '\n'
        << "walksound=" << (settings.walksound ? "true" : "false") << '\n'
        << "show_hits=" << (settings.showHits ? "true" : "false") << '\n'
        << "always_run=" << (settings.alwaysRun ? "true" : "false") << '\n'
        << "flip_on_exit=" << (settings.flipOnExit ? "true" : "false") << '\n'
        << "mouse_sensitivity=" << std::clamp(settings.mouseSensitivity, 0, 100) << "\n\n"
        << "[gameplay]\n"
        << "keyboard_interaction_depth=" << std::clamp(settings.keyboardInteractionDepth, 32, 4096) << '\n'
        << "mouse_interaction_depth=" << std::clamp(settings.mouseInteractionDepth, 32, 4096) << '\n'
        << "context_action_popup=" << (settings.contextActionPopup ? "true" : "false") << "\n\n"
        << "[startup]\n"
        << "start_in_main_menu=" << (settings.startInMainMenu ? "true" : "false") << "\n\n"
        << "[features]\n"
        << "bolster_monsters=" << (settings.bolsterMonsters ? "true" : "false") << '\n'
        << "indoor_pathfinding=" << (settings.indoorPathfinding ? "true" : "false") << '\n'
        << "blaster_skill_scaling=" << blasterSkillScalingValue(settings.blasterSkillScaling) << '\n'
        << "blaster_min_recovery=" << blasterMinimumRecoveryTicksValue(settings.blasterMinimumRecoveryTicks) << "\n\n"
        << "[logging]\n"
        << "indoor_visibility=" << (settings.logIndoorVisibility ? "true" : "false") << '\n'
        << "indoor_pathfinding=" << (settings.logIndoorPathfinding ? "true" : "false") << '\n'
        << "fps_trace=" << (settings.fpsTrace ? "true" : "false") << '\n'
        << "performance_trace=" << (settings.performanceTrace ? "true" : "false") << '\n'
        << "hitch_trace=" << (settings.hitchTrace ? "true" : "false") << '\n'
        << "collision_trace=" << (settings.collisionTrace ? "true" : "false") << '\n'
        << "gameplay_trace=" << (settings.gameplayTrace ? "true" : "false") << '\n'
        << "gameplay_trace_file=" << settings.gameplayTraceFile << '\n'
        << "gameplay_trace_append=" << (settings.gameplayTraceAppend ? "true" : "false") << '\n'
        << "combat_trace=" << (settings.combatTrace ? "true" : "false") << '\n'
        << "combat_trace_file=" << settings.combatTraceFile << '\n'
        << "combat_trace_append=" << (settings.combatTraceAppend ? "true" : "false") << '\n'
        << "hitch_threshold_ms=" << std::clamp(settings.hitchThresholdMilliseconds, 0.1f, 1000.0f) << "\n\n"
        << "[input]\n";

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        output << definition.iniKey << '=' << inputBindingName(settings.keyboard.binding(definition.action)) << '\n';
    }

    output
        << '\n'
        << "[video]\n"
        << "blood_splats=" << (settings.bloodSplats ? "true" : "false") << '\n'
        << "colored_lights=" << (settings.coloredLights ? "true" : "false") << '\n'
        << "tinting=" << (settings.tinting ? "true" : "false") << '\n'
        << "shadows=" << (settings.shadows ? "true" : "false") << '\n'
        << "sprite_outline=" << (settings.spriteOutline ? "true" : "false") << '\n'
        << "texture_filtering=" << (settings.textureFiltering ? "true" : "false") << '\n'
        << "terrain_filtering=" << settings.terrainFiltering << '\n'
        << "terrain_anisotropy=" << settings.terrainAnisotropy << '\n'
        << "bmodel_filtering=" << settings.bmodelFiltering << '\n'
        << "billboard_filtering=" << settings.billboardFiltering << '\n'
        << "ui_filtering=" << settings.uiFiltering << '\n'
        << "text_filtering=" << settings.textFiltering << '\n'
        << "minimap_filtering=" << settings.minimapFiltering << '\n'
        << "view_distance=" << settings.viewDistance << '\n'
        << "outdoor_billboard_depth_slice="
        << std::clamp(settings.outdoorBillboardDepthSlice, 0.0f, 8192.0f) << '\n'
        << "skip_event_cutscenes=" << (settings.skipEventCutscenes ? "true" : "false") << '\n'
        << "window_mode=" << windowModeString(settings.windowMode) << '\n'
        << "resolution=" << std::clamp(settings.resolutionWidth, 320, 16384)
        << 'x' << std::clamp(settings.resolutionHeight, 200, 16384) << '\n'
        << "vsync=" << (settings.verticalSync ? "true" : "false") << '\n'
        << "gameplay_ui_layout=" << gameplayUiLayoutString(settings.gameplayUiLayout) << "\n\n"
        << "[video_quality]\n"
        << "texture=" << Engine::assetScaleTierToString(settings.assetScaleProfile.textures) << '\n'
        << "terrain=" << Engine::assetScaleTierToString(settings.assetScaleProfile.terrain) << '\n'
        << "sky=" << Engine::assetScaleTierToString(settings.assetScaleProfile.sky) << '\n'
        << "sprites=" << Engine::assetScaleTierToString(settings.assetScaleProfile.sprites) << '\n'
        << "decorations=" << Engine::assetScaleTierToString(settings.assetScaleProfile.decorations) << '\n'
        << "icons=" << Engine::assetScaleTierToString(settings.assetScaleProfile.icons) << '\n'
        << "ui=" << Engine::assetScaleTierToString(settings.assetScaleProfile.ui) << '\n'
        << "effects=" << Engine::assetScaleTierToString(settings.assetScaleProfile.effects) << '\n'
        << "fonts=" << Engine::assetScaleTierToString(settings.assetScaleProfile.fonts) << "\n\n"
        << "[debug]\n"
        << "preseed_party=" << (settings.preseedParty ? "true" : "false") << '\n'
        << "party_seed_roster_id=" << settings.partySeedRosterId << '\n'
        << "start_world=" << settings.startWorldId << '\n'
        << "start_map_file=" << settings.startMapFile << '\n'
        << "override_start_position=" << (settings.overrideStartPosition ? "true" : "false") << '\n'
        << "start_x=" << settings.startX << '\n'
        << "start_y=" << settings.startY << '\n'
        << "start_z=" << settings.startZ << '\n'
        << "start_flying=" << (settings.startFlying ? "true" : "false") << '\n'
        << "movement_speed_multiplier=" << settings.movementSpeedMultiplier << '\n'
        << "immortal=" << (settings.immortal ? "true" : "false") << '\n'
        << "unlimited_mana=" << (settings.unlimitedMana ? "true" : "false") << '\n'
        << "new_game_god_lich=" << (settings.newGameGodLich ? "true" : "false") << '\n'
        << "allow_incomplete_character_creation="
        << (settings.allowIncompleteCharacterCreation ? "true" : "false") << '\n'
        << "console=" << (settings.debugConsole ? "true" : "false") << "\n\n"
        << "[arpg_mode]\n"
        << "enabled=" << (settings.arpgModeEnabled ? "true" : "false") << '\n'
        << "player_monster_descriptor=" << settings.arpgModePlayerMonsterDescriptor << '\n'
        << "camera_yaw_degrees=" << settings.arpgModeCameraYawDegrees << '\n'
        << "camera_pitch_degrees=" << settings.arpgModeCameraPitchDegrees << '\n'
        << "camera_distance=" << settings.arpgModeCameraDistance << '\n'
        << "camera_target_height=" << settings.arpgModeCameraTargetHeight << '\n'
        << "camera_fov_degrees=" << settings.arpgModeCameraFovDegrees << '\n'
        << "camera_follow_lerp=" << settings.arpgModeCameraFollowLerp << '\n'
        << "click_stop_radius=" << settings.arpgModeClickStopRadius << '\n'
        << "move_speed_multiplier=" << settings.arpgModeMoveSpeedMultiplier << '\n'
        << "spell_animation_seconds=" << settings.arpgModeSpellAnimationSeconds << '\n'
        << "spell_release_seconds=" << settings.arpgModeSpellReleaseSeconds << '\n'
        << "attack_animation_min_seconds=" << settings.arpgModeAttackAnimationMinSeconds << '\n'
        << "attack_animation_max_seconds=" << settings.arpgModeAttackAnimationMaxSeconds << '\n'
        << "attack_animation_recovery_scale=" << settings.arpgModeAttackAnimationRecoveryScale << '\n';

    if (!output.good())
    {
        error = "Failed while writing settings file";
        return false;
    }

    error.clear();
    return true;
}
}
