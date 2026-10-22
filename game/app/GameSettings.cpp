#include "game/app/GameSettings.h"
#include "game/render/CombatActorHealthBarPolicy.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string_view>
#include <system_error>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
#include "game/app/SettingsShippedDefaults.inc"

constexpr float MinimumViewDistance = 1024.0f;
constexpr float UnlimitedViewDistance = 200000.0f;

using IniSection = std::unordered_map<std::string, std::string>;

struct IniDocument
{
    std::unordered_map<std::string, IniSection> sections;
    // Every key in file order, for the keys the loader never asks for.
    std::vector<SettingsEntry> entries;
    // "section.key" of every key the loader asked for, present or not.
    mutable std::unordered_set<std::string> consulted;
};

// Values the game remembers rather than choices with a default: always written, never compared with defaults.
bool isRememberedState(const std::string &name)
{
    return name == "debug.start_world";
}

const char *boolValue(bool value)
{
    return value ? "true" : "false";
}

class SettingsSerializer
{
  public:
    void section(const char *pName)
    {
        m_section = pName;
    }

    template <typename... Values>
    void add(std::string_view key, const Values &...values)
    {
        std::ostringstream value;
        (value << ... << values);
        m_entries.push_back({m_section, std::string(key), value.str()});
    }

    std::vector<SettingsEntry> takeEntries()
    {
        return std::move(m_entries);
    }

  private:
    std::string m_section;
    std::vector<SettingsEntry> m_entries;
};

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
    document.consulted.insert(section + '.' + key);
    const auto sectionIt = document.sections.find(section);

    if (sectionIt == document.sections.end())
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
            document.sections[currentSection][key] = value;
            document.entries.push_back({currentSection, key, value});
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
#if defined(__ANDROID__)
    settings.settingsProfileName = "android";
#else
    settings.settingsProfileName = "desktop";
#endif
    settings.settingsProfileVersion = CurrentSettingsProfileVersion;
    settings.keyboard.restoreDefaults(settings.controlScheme);
    settings.assetScaleProfile.decorations = Engine::AssetScaleTier::X2;
    settings.assetScaleProfile.preferRestoredIcons = true;
    // These are the only defaults: release packages ship no settings file, and a player's settings.ini holds only
    // their own choices. The surface texture tier is the one cooked tier the packages carry per platform
    // (tools/cook_surface_textures.py), x4 on desktop and x2 on Android. iOS GPUs have no BC formats, so iOS uses the
    // Android packages (ASTC/ETC2, x2 surfaces) and the Android defaults.
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
    settings.assetScaleProfile.textures = Engine::AssetScaleTier::X2;
    settings.soundVolume = 2;
    settings.voiceVolume = 2;
    settings.bolsterMonsters = true;
    settings.resolutionWidth = 1280;
    settings.resolutionHeight = 720;
    settings.lightGrid = LightGridQuality::Low;
    settings.weatherQuality = WeatherQuality::Medium;
    settings.terrainSpecular = false;
    settings.terrainSubdivision = 2;
    settings.terrainAntiTiling = false;
    settings.terrainAnisotropy = "2x";
    settings.skyResolutionScale = 0.5f;
    settings.waterReflectionSize = 256;
    settings.bloom = false;
    settings.cinematicGrading = false;
#else
    settings.assetScaleProfile.textures = Engine::AssetScaleTier::X4;
    settings.windowMode = WindowMode::WindowedFullscreen;
    settings.terrainAnisotropy = "8x";
    settings.terrainDecorations = true;
    settings.waterSpriteReflections = true;
    settings.shadows = true;
    settings.ambientOcclusion = true;
    settings.ambientOcclusionStrength = 50;
    settings.antialiasing = 4;
    settings.sharpening = 50;
    settings.debugConsole = false;
    settings.startWorldId = "mm6";
#endif
    return settings;
}

bool migrateGameSettings(GameSettings &settings)
{
    constexpr uint32_t PlayerChoicesSettingsProfileVersion = 5;
    static_assert(CurrentSettingsProfileVersion == PlayerChoicesSettingsProfileVersion);

    if (settings.settingsProfileVersion > CurrentSettingsProfileVersion)
    {
        return false;
    }

#if defined(__ANDROID__)
    bool migrated = migrateLegacyAndroidSettings(settings);
#else
    bool migrated = migrateLegacyDesktopSettings(settings);
#endif

    // loadGameSettingsFromText already dropped the shipped defaults of an older full file.
    if (settings.settingsProfileVersion < PlayerChoicesSettingsProfileVersion)
    {
        settings.settingsProfileVersion = PlayerChoicesSettingsProfileVersion;
        migrated = true;
    }

    return migrated;
}

bool migrateLegacyAndroidSettings(GameSettings &settings)
{
    constexpr uint32_t InitialAndroidSettingsProfileVersion = 1;
    constexpr uint32_t CharacterCreationAndroidSettingsProfileVersion = 2;
    constexpr uint32_t PhoneTerrainAndroidSettingsProfileVersion = 3;
    constexpr uint32_t CurrentAndroidSettingsProfileVersion = 4;

    if (settings.settingsProfileName == "android"
        && settings.settingsProfileVersion >= CurrentAndroidSettingsProfileVersion)
    {
        return false;
    }

    if (settings.settingsProfileName != "android"
        || settings.settingsProfileVersion < InitialAndroidSettingsProfileVersion)
    {
        settings.settingsProfileName = "android";
        settings.settingsProfileVersion = InitialAndroidSettingsProfileVersion;
        settings.contextActionPopup = true;
        settings.startInMainMenu = true;
        settings.verticalSync = true;

        settings.logIndoorVisibility = false;
        settings.logIndoorPathfinding = false;
        settings.logOutdoorPathfinding = false;
        settings.fpsTrace = false;
        settings.performanceTrace = false;
        settings.hitchTrace = false;
        settings.collisionTrace = false;
        settings.gameplayTrace = false;
        settings.combatTrace = false;

        settings.partySeedRosterId = 0;
        settings.startWorldId = "mm8";
        settings.startMapFile.clear();
        settings.overrideStartPosition = false;
        settings.startFlying = false;
        settings.movementSpeedMultiplier = 1.0f;
        settings.immortal = false;
        settings.unlimitedMana = false;
        settings.debugConsole = true;
    }

    if (settings.settingsProfileVersion < CharacterCreationAndroidSettingsProfileVersion)
    {
        settings.preseedParty = false;
        settings.newGameGodLich = false;
        settings.allowIncompleteCharacterCreation = false;
        settings.settingsProfileVersion = CharacterCreationAndroidSettingsProfileVersion;
    }

    if (settings.settingsProfileVersion < PhoneTerrainAndroidSettingsProfileVersion)
    {
        // The ground materials terrain is the only one: on phones it takes lighter anisotropic filtering and smaller
        // water reflections (which redraw it). Values a player changed from the earlier defaults stay.
        if (settings.terrainAnisotropy == "4x")
        {
            settings.terrainAnisotropy = "2x";
        }
        if (settings.waterReflectionSize == 512)
        {
            settings.waterReflectionSize = 256;
        }
        settings.settingsProfileVersion = PhoneTerrainAndroidSettingsProfileVersion;
    }

    if (settings.settingsProfileVersion < CurrentAndroidSettingsProfileVersion)
    {
        // Releases up to 1.3 wrote actor_models=false; MM6 creatures exist only as models since then.
        settings.actorModels = true;
        settings.settingsProfileVersion = CurrentAndroidSettingsProfileVersion;
    }

    return true;
}

bool migrateLegacyDesktopSettings(GameSettings &settings)
{
    constexpr uint32_t InitialDesktopSettingsProfileVersion = 1;
    constexpr uint32_t UserDataDesktopSettingsProfileVersion = 2;
    constexpr uint32_t CurrentDesktopSettingsProfileVersion = UserDataDesktopSettingsProfileVersion;

    if (settings.settingsProfileName == "desktop"
        && settings.settingsProfileVersion >= CurrentDesktopSettingsProfileVersion)
    {
        return false;
    }

    if (settings.settingsProfileName != "desktop"
        || settings.settingsProfileVersion < InitialDesktopSettingsProfileVersion)
    {
        // Desktop settings carried no profile before version 1. Releases up to 1.3 wrote actor_models=false, which
        // the old Flatpak package kept across updates; MM6 creatures exist only as models since then.
        settings.settingsProfileName = "desktop";
        settings.actorModels = true;
        settings.settingsProfileVersion = InitialDesktopSettingsProfileVersion;
    }

    if (settings.settingsProfileVersion < UserDataDesktopSettingsProfileVersion)
    {
        // Release packages wrote their installation's asset root into the player's file. The game now finds the
        // installed assets itself (app/<version>/index.json), where the relative "assets" no longer points. A
        // developer's own asset root stays.
        if (settings.assetRoot == "assets" || settings.assetRoot == "/app/share/openyamm/assets")
        {
            settings.assetRoot.clear();
        }

        settings.settingsProfileVersion = UserDataDesktopSettingsProfileVersion;
    }

    return true;
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

uint8_t textureAnisotropyLevel(const GameSettings &settings)
{
    for (const uint8_t level : {2, 8, 16})
    {
        if (settings.terrainAnisotropy == std::to_string(level) + "x")
        {
            return level;
        }
    }
    return 4;
}

CharacterAttackTuning characterAttackTuningFromSettings(const GameSettings &settings)
{
    CharacterAttackTuning tuning = {};
    tuning.blasterSkillScaling = settings.blasterSkillScaling;
    tuning.blasterMinimumRecoveryTicks = std::clamp(settings.blasterMinimumRecoveryTicks, 0, 300);
    return tuning;
}

std::optional<std::string> getBakedLightingSetting(const GameSettings &settings, const std::string &name)
{
    std::ostringstream output;
    output.precision(9);
    if (name == "baked_sun_strength" || name == "baked_sky_strength")
    {
        output << (name == "baked_sun_strength" ? settings.bakedSunStrength : settings.bakedSkyStrength);
    }
    else if (name == "baked_sun_color" || name == "baked_sky_color")
    {
        const std::array<float, 3> &color = name == "baked_sun_color" ? settings.bakedSunColor : settings.bakedSkyColor;
        output << color[0] << ',' << color[1] << ',' << color[2];
    }
    else
    {
        return std::nullopt;
    }
    return output.str();
}

bool setBakedLightingSetting(
    GameSettings &settings, const std::string &name, const std::string &value, std::string &error)
{
    error.clear();
    if (name == "baked_sun_strength" || name == "baked_sky_strength")
    {
        float strength = 0.0f;
        if (!parseFloatValue(value, strength) || !std::isfinite(strength) || strength < 0.0f || strength > 16.0f)
        {
            error = name + " requires a finite strength in [0, 16].";
            return false;
        }
        (name == "baked_sun_strength" ? settings.bakedSunStrength : settings.bakedSkyStrength) = strength;
        return true;
    }
    if (name == "baked_sun_color" || name == "baked_sky_color")
    {
        std::array<float, 3> color = {};
        size_t begin = 0;
        for (size_t channel = 0; channel < color.size(); ++channel)
        {
            const size_t end = value.find(',', begin);
            if ((channel < 2) != (end != std::string::npos)
                || !parseFloatValue(value.substr(begin, end - begin), color[channel])
                || !std::isfinite(color[channel]) || color[channel] < 0.0f || color[channel] > 1.0f)
            {
                error = name + " requires three comma-separated linear RGB components in [0, 1].";
                return false;
            }
            begin = end == std::string::npos ? value.size() : end + 1;
        }
        (name == "baked_sun_color" ? settings.bakedSunColor : settings.bakedSkyColor) = color;
        return true;
    }
    error = "Unknown baked lighting setting: " + name;
    return false;
}

bool parseWeatherQualityValue(const std::string &value, WeatherQuality &result)
{
    static const std::array<std::pair<const char *, WeatherQuality>, 4> Values = {{
        {"off", WeatherQuality::Off}, {"low", WeatherQuality::Low}, {"medium", WeatherQuality::Medium},
        {"high", WeatherQuality::High}}};
    const std::string lowered = toLowerCopy(trimCopy(value));

    for (const auto &[pName, quality] : Values)
    {
        if (lowered == pName)
        {
            result = quality;
            return true;
        }
    }

    return false;
}

std::string weatherQualityValue(WeatherQuality quality)
{
    switch (quality)
    {
        case WeatherQuality::Off:
            return "off";
        case WeatherQuality::Low:
            return "low";
        case WeatherQuality::Medium:
            return "medium";
        case WeatherQuality::High:
        default:
            return "high";
    }
}

bool parseLightGridQualityValue(const std::string &value, LightGridQuality &result)
{
    const std::string lowered = toLowerCopy(trimCopy(value));
    if (lowered == "low" || lowered == "high")
    {
        result = lowered == "low" ? LightGridQuality::Low : LightGridQuality::High;
        return true;
    }
    return false;
}

std::string lightGridQualityValue(LightGridQuality quality)
{
    return quality == LightGridQuality::Low ? "low" : "high";
}

bool parseAntialiasingValue(const std::string &value, int &samples)
{
    const std::string lowered = toLowerCopy(trimCopy(value));
    if (lowered == "off" || lowered == "2x" || lowered == "4x")
    {
        samples = lowered == "off" ? 0 : lowered[0] - '0';
        return true;
    }
    return false;
}

std::string antialiasingValue(int samples)
{
    return samples >= 4 ? "4x" : samples >= 2 ? "2x" : "off";
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
    return loadGameSettingsFromText(buffer.str(), error);
}

namespace
{
std::optional<GameSettings> parseGameSettingsDocument(const IniDocument &document, std::string &error)
{
    GameSettings settings = GameSettings::createDefault();
    // A file without a profile predates profiles; the migrations decide what it needs.
    settings.settingsProfileName.clear();
    settings.settingsProfileVersion = 0;
    for (const char *pName : {"baked_sun_strength", "baked_sky_strength", "baked_sun_color", "baked_sky_color"})
    {
        if (const std::optional<std::string> value = getIniValue(document, "video", pName))
        {
            if (!setBakedLightingSetting(settings, pName, *value, error))
            {
                return std::nullopt;
            }
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "profile", "name"))
    {
        settings.settingsProfileName = toLowerCopy(trimCopy(*value));
    }

    if (const std::optional<std::string> value = getIniValue(document, "profile", "version"))
    {
        uint32_t parsed = settings.settingsProfileVersion;

        if (parseUInt32Value(*value, parsed))
        {
            settings.settingsProfileVersion = parsed;
        }
    }

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

    if (const std::optional<std::string> value = getIniValue(document, "controls", "invert_mouse_y"))
    {
        bool parsed = settings.invertMouseY;

        if (parseBoolValue(*value, parsed))
        {
            settings.invertMouseY = parsed;
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

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "combat_text"))
    {
        bool parsed = settings.combatText;

        if (parseBoolValue(*value, parsed))
        {
            settings.combatText = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "enemy_health_bars"))
    {
        if (validEnemyHealthBarMode(*value))
        {
            settings.enemyHealthBarMode = *value;
        }
    }
    else
    {
        // Explicit migration from the retired world-bar and top-centered panel settings.
        const std::optional<std::string> bars = getIniValue(document, "gameplay", "combat_actor_hp_bars");
        const std::optional<std::string> panel = getIniValue(document, "gameplay", "combat_target_panel");
        bool enabled = true;
        bool targetEnabled = false;
        if (bars && parseBoolValue(*bars, enabled) && !enabled)
        {
            if (panel)
            {
                parseBoolValue(*panel, targetEnabled);
            }
            settings.enemyHealthBarMode = targetEnabled ? "target" : "off";
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "enemy_health_bar_values"))
    {
        if (validEnemyHealthBarValues(*value))
        {
            settings.enemyHealthBarValues = *value;
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "enemy_health_bar_damage_trail"))
    {
        parseBoolValue(*value, settings.enemyHealthBarDamageTrail);
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "quest_markers"))
    {
        bool parsed = settings.questMarkers;

        if (parseBoolValue(*value, parsed))
        {
            settings.questMarkers = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "party_frame"))
    {
        parseBoolValue(*value, settings.partyFrame);
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "melee_hit_blood_effects"))
    {
        bool parsed = settings.meleeHitBloodEffects;

        if (parseBoolValue(*value, parsed))
        {
            settings.meleeHitBloodEffects = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "melee_hit_feedback"))
    {
        bool parsed = settings.meleeHitFeedback;

        if (parseBoolValue(*value, parsed))
        {
            settings.meleeHitFeedback = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "melee_hit_effects"))
    {
        bool parsed = settings.meleeHitEffects;

        if (parseBoolValue(*value, parsed))
        {
            settings.meleeHitEffects = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "melee_hit_flash"))
    {
        bool parsed = settings.meleeHitFlash;

        if (parseBoolValue(*value, parsed))
        {
            settings.meleeHitFlash = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "gameplay", "melee_camera_kick"))
    {
        bool parsed = settings.meleeCameraKick;

        if (parseBoolValue(*value, parsed))
        {
            settings.meleeCameraKick = parsed;
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

    if (const std::optional<std::string> value = getIniValue(document, "video", "warm_torch_light"))
    {
        parseBoolValue(*value, settings.warmTorchLight);
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

    if (const std::optional<std::string> value = getIniValue(document, "video", "model_shadow_quality"))
    {
        int parsed = settings.modelShadowQuality;
        if (parseIntValue(*value, parsed) && parsed >= 0 && parsed <= 3)
        {
            settings.modelShadowQuality = parsed;
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "model_lods"))
    {
        bool parsed = settings.modelLods;
        if (parseBoolValue(*value, parsed))
        {
            settings.modelLods = parsed;
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "creature_outlines"))
    {
        bool parsed = settings.creatureOutlines;
        if (parseBoolValue(*value, parsed))
        {
            settings.creatureOutlines = parsed;
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "model_lod"))
    {
        int parsed = settings.modelLodOverride;
        if (parseIntValue(*value, parsed) && parsed >= -1 && parsed <= 3)
        {
            settings.modelLodOverride = parsed;
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

    if (const std::optional<std::string> value = getIniValue(document, "video", "ambient_occlusion"))
    {
        parseBoolValue(*value, settings.ambientOcclusion);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "ambient_occlusion_strength"))
    {
        int parsed = settings.ambientOcclusionStrength;
        if (parseIntValue(*value, parsed))
        {
            settings.ambientOcclusionStrength = std::clamp(parsed, 0, 100);
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "bloom"))
    {
        parseBoolValue(*value, settings.bloom);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "bloom_strength"))
    {
        int parsed = settings.bloomStrength;
        if (parseIntValue(*value, parsed))
        {
            settings.bloomStrength = std::clamp(parsed, 0, 100);
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "cinematic_grading"))
    {
        parseBoolValue(*value, settings.cinematicGrading);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "water_reflections"))
    {
        parseBoolValue(*value, settings.waterReflections);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "water_reflection_size"))
    {
        int parsed = settings.waterReflectionSize;
        if (parseIntValue(*value, parsed))
        {
            settings.waterReflectionSize = std::clamp(parsed, 128, 2048);
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "water_movement_ripples"))
    {
        parseBoolValue(*value, settings.waterMovementRipples);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "water_sprite_reflections"))
    {
        parseBoolValue(*value, settings.waterSpriteReflections);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "terrain_subdivision"))
    {
        int parsed = settings.terrainSubdivision;
        if (parseIntValue(*value, parsed) && (parsed == 1 || parsed == 2 || parsed == 4))
        {
            settings.terrainSubdivision = parsed;
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "terrain_antitiling"))
    {
        parseBoolValue(*value, settings.terrainAntiTiling);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "light_grid"))
    {
        parseLightGridQualityValue(*value, settings.lightGrid);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "weather_quality"))
    {
        parseWeatherQualityValue(*value, settings.weatherQuality);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "rain_ripples"))
    {
        parseBoolValue(*value, settings.rainRipples);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "terrain_specular"))
    {
        parseBoolValue(*value, settings.terrainSpecular);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "wet_surfaces"))
    {
        parseBoolValue(*value, settings.wetSurfaces);
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "sky_resolution_scale"))
    {
        float parsed = settings.skyResolutionScale;
        if (parseFloatValue(*value, parsed) && std::isfinite(parsed))
        {
            settings.skyResolutionScale = std::clamp(parsed, 0.25f, 1.0f);
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "cinematic_strength"))
    {
        int parsed = settings.cinematicStrength;
        if (parseIntValue(*value, parsed))
        {
            settings.cinematicStrength = std::clamp(parsed, 0, 100);
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "sharpening"))
    {
        int parsed = settings.sharpening;
        if (parseIntValue(*value, parsed))
        {
            settings.sharpening = std::clamp(parsed, 0, 100);
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "video", "antialiasing"))
    {
        parseAntialiasingValue(*value, settings.antialiasing);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "lightmaps"))
    {
        parseBoolValue(*value, settings.lightmaps);
    }

    if (const std::optional<std::string> value = getIniValue(document, "video", "terrain_decorations"))
    {
        parseBoolValue(*value, settings.terrainDecorations);
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

    if (const std::optional<std::string> value = getIniValue(document, "video", "wait_for_level_sprites"))
    {
        bool parsed = settings.waitForLevelSprites;

        if (parseBoolValue(*value, parsed))
        {
            settings.waitForLevelSprites = parsed;
        }
    }

    // Retired by the shared Obsidian HUD. Legacy INI values are omitted on the next save.

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

    if (const std::optional<std::string> value = getIniValue(document, "video_quality", "prefer_restored_icons"))
    {
        parseBoolValue(*value, settings.assetScaleProfile.preferRestoredIcons);
    }

    parseAssetScaleProfileValue(
        document,
        "sky",
        settings.assetScaleProfile,
        Engine::AssetScaleCategory::Sky);
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

    if (const std::optional<std::string> value = getIniValue(document, "startup", "save_file"))
    {
        settings.startupSaveFile = trimCopy(*value);
    }

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

    if (const std::optional<std::string> value = getIniValue(document, "features", "outdoor_pathfinding"))
    {
        bool parsed = settings.outdoorPathfinding;

        if (parseBoolValue(*value, parsed))
        {
            settings.outdoorPathfinding = parsed;
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

    if (const std::optional<std::string> value = getIniValue(document, "logging", "outdoor_pathfinding"))
    {
        bool parsed = settings.logOutdoorPathfinding;

        if (parseBoolValue(*value, parsed))
        {
            settings.logOutdoorPathfinding = parsed;
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

    if (const std::optional<std::string> value = getIniValue(document, "updates", "check_for_updates"))
    {
        const std::string mode = toLowerCopy(trimCopy(*value));

        if (mode == "ask" || mode == "auto" || mode == "off")
        {
            settings.updateCheck = mode;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "updates", "url"))
    {
        const std::string url = trimCopy(*value);

        if (url.starts_with("https://") || url.starts_with("http://"))
        {
            settings.updateUrl = url;
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

    if (const std::optional<std::string> value = getIniValue(document, "debug", "turbo_movement"))
    {
        bool parsed = settings.turboMovementEnabled;

        if (parseBoolValue(*value, parsed))
        {
            settings.turboMovementEnabled = parsed;
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

    if (const std::optional<std::string> value = getIniValue(document, "debug", "menu_input_tour_path"))
    {
        settings.menuInputTourPath = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "screenshot_path"))
    {
        settings.screenshotPath = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "screenshot_delay_seconds"))
    {
        float parsed = 0.0f;
        if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed) || parsed < 0.0f || parsed > 600.0f)
        {
            error = "screenshot_delay_seconds must be finite in [0, 600].";
            return std::nullopt;
        }
        settings.screenshotDelaySeconds = parsed;
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "screenshot_tour_path"))
    {
        settings.screenshotTourPath = trimCopy(*value);
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "time_scale"))
    {
        float parsed = 1.0f;
        if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed) || parsed < 0.05f || parsed > 4.0f)
        {
            error = "time_scale must be finite in [0.05, 4].";
            return std::nullopt;
        }
        settings.timeScale = parsed;
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "effect_spawn_id"))
    {
        settings.effectSpawnId = trimCopy(*value);
    }

    constexpr std::array<const char *, 3> EffectPositionNames = {
        "effect_spawn_x", "effect_spawn_y", "effect_spawn_z"};
    for (size_t axis = 0; axis < EffectPositionNames.size(); ++axis)
    {
        if (const std::optional<std::string> value = getIniValue(document, "debug", EffectPositionNames[axis]))
        {
            float parsed = 0.0f;
            if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed))
            {
                error = std::string(EffectPositionNames[axis]) + " must be finite.";
                return std::nullopt;
            }
            settings.effectSpawnPosition[axis] = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "effect_spawn_scale"))
    {
        float parsed = 0.0f;
        if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed) || parsed <= 0.0f)
        {
            error = "effect_spawn_scale must be finite and positive.";
            return std::nullopt;
        }
        settings.effectSpawnScale = parsed;
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "effect_spawn_yaw_radians"))
    {
        float parsed = 0.0f;
        if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed))
        {
            error = "effect_spawn_yaw_radians must be finite.";
            return std::nullopt;
        }
        settings.effectSpawnYawRadians = parsed;
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "effect_spawn_count"))
    {
        int parsed = 0;
        if (!parseIntValue(*value, parsed) || parsed < 1 || parsed > 256)
        {
            error = "effect_spawn_count must be between 1 and 256.";
            return std::nullopt;
        }
        settings.effectSpawnCount = static_cast<uint32_t>(parsed);
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "effect_stats_delay_seconds"))
    {
        float parsed = 0.0f;
        if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed) || parsed < 0.0f || parsed > 600.0f)
        {
            error = "effect_stats_delay_seconds must be finite and between 0 and 600.";
            return std::nullopt;
        }
        settings.effectStatsDelaySeconds = parsed;
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "actor_models"))
    {
        if (!parseBoolValue(*value, settings.actorModels))
        {
            error = "actor_models must be a boolean.";
            return std::nullopt;
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "actor_models_manifest"))
    {
        settings.actorModelsManifest = trimCopy(*value);
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "actor_spawn_id"))
    {
        int parsed = 0;
        if (!parseIntValue(*value, parsed) || parsed <= 0 || parsed > 32767)
        {
            error = "actor_spawn_id must be between 1 and 32767.";
            return std::nullopt;
        }
        settings.actorSpawnId = int16_t(parsed);
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "actor_spawn_count"))
    {
        int parsed = 0;
        if (!parseIntValue(*value, parsed) || parsed < 1 || parsed > 128)
        {
            error = "actor_spawn_count must be between 1 and 128.";
            return std::nullopt;
        }
        settings.actorSpawnCount = uint32_t(parsed);
    }
    const std::array<const char *, 3> actorPositionKeys = {"actor_spawn_x", "actor_spawn_y", "actor_spawn_z"};
    for (size_t axis = 0; axis < actorPositionKeys.size(); ++axis)
    {
        if (const std::optional<std::string> value = getIniValue(document, "debug", actorPositionKeys[axis]))
        {
            if (!parseFloatValue(*value, settings.actorSpawnPosition[axis])
                || !std::isfinite(settings.actorSpawnPosition[axis]))
            {
                error = std::string(actorPositionKeys[axis]) + " must be finite.";
                return std::nullopt;
            }
        }
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "model_spawn_path"))
    {
        settings.modelSpawnPath = trimCopy(*value);
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "model_spawn_clip"))
    {
        settings.modelSpawnClip = trimCopy(*value);
    }

    constexpr std::array<const char *, 3> ModelPositionNames = {
        "model_spawn_x", "model_spawn_y", "model_spawn_z"};
    for (size_t axis = 0; axis < ModelPositionNames.size(); ++axis)
    {
        if (const std::optional<std::string> value = getIniValue(document, "debug", ModelPositionNames[axis]))
        {
            float parsed = 0.0f;
            if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed))
            {
                error = std::string(ModelPositionNames[axis]) + " must be finite.";
                return std::nullopt;
            }
            settings.modelSpawnPosition[axis] = parsed;
        }
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "model_spawn_scale"))
    {
        float parsed = 0.0f;
        if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed) || parsed <= 0.0f)
        {
            error = "model_spawn_scale must be finite and positive.";
            return std::nullopt;
        }
        settings.modelSpawnScale = parsed;
    }

    if (const std::optional<std::string> value = getIniValue(document, "debug", "model_spawn_yaw_radians"))
    {
        float parsed = 0.0f;
        if (!parseFloatValue(*value, parsed) || !std::isfinite(parsed))
        {
            error = "model_spawn_yaw_radians must be finite.";
            return std::nullopt;
        }
        settings.modelSpawnYawRadians = parsed;
    }
    if (const std::optional<std::string> value = getIniValue(document, "debug", "model_spawn_markers"))
    {
        if (!parseBoolValue(*value, settings.modelSpawnMarkers))
        {
            error = "model_spawn_markers must be a boolean.";
            return std::nullopt;
        }
    }

    // Keys the loader asked for are the player's stored choices; the writer drops the ones it no longer writes
    // (retired keys and launch-only directives). Everything else is kept verbatim for a newer version or a mod.
    for (const SettingsEntry &entry : document.entries)
    {
        const std::string name = entry.section + '.' + entry.key;

        if (document.consulted.contains(name))
        {
            settings.fileState.storedKeys.insert(name);
        }
        else
        {
            settings.fileState.unknownEntries.push_back(entry);
        }
    }

    error.clear();
    return settings;
}

IniDocument documentWithEntries(const std::vector<SettingsEntry> &entries)
{
    IniDocument document;

    for (const SettingsEntry &entry : entries)
    {
        document.sections[entry.section][entry.key] = entry.value;
        document.entries.push_back(entry);
    }

    return document;
}

// The value a key takes once this version has loaded and written it, or nothing for a key it does not write.
std::optional<std::string> normalizedSettingsValue(const SettingsEntry &entry)
{
    std::string error;
    const std::optional<GameSettings> loaded = parseGameSettingsDocument(documentWithEntries({entry}), error);

    if (!loaded)
    {
        return std::nullopt;
    }

    for (SettingsEntry &serialized : serializeGameSettings(*loaded))
    {
        if (serialized.section == entry.section && serialized.key == entry.key)
        {
            return std::move(serialized.value);
        }
    }

    return std::nullopt;
}

uint32_t documentProfileVersion(const IniDocument &document)
{
    uint32_t version = 0;
    const std::optional<std::string> value = getIniValue(document, "profile", "version");
    return value && parseUInt32Value(*value, version) ? version : 0;
}

// The one-time conversion of a full settings file, written before files held only choices (profile version 5), into
// the player's choices. A key whose value equals a default its platform shipped (a current default or a value of
// a release's settings template) is dropped, so it follows the defaults from now on; so is a key our releases wrote
// that this version no longer reads. A player who deliberately picked a value equal to an old default gets the new
// default once.
IniDocument withoutShippedDefaults(const IniDocument &document)
{
#if defined(__ANDROID__)
    const std::string_view platform = "android";
#else
    const std::string_view platform = "desktop";
#endif
    std::unordered_map<std::string, std::unordered_set<std::string>> shippedValues;

    for (const ShippedSettingsValue &shipped : ShippedSettingsValues)
    {
        if (shipped.pPlatform == platform)
        {
            const SettingsEntry entry = {shipped.pSection, shipped.pKey, shipped.pValue};
            std::unordered_set<std::string> &values = shippedValues[entry.section + '.' + entry.key];

            if (std::optional<std::string> value = normalizedSettingsValue(entry))
            {
                values.insert(std::move(*value));
            }
        }
    }

    GameSettings presetDefaults = GameSettings::createDefault();

    if (const std::optional<std::string> scheme = getIniValue(document, "controls", "control_scheme"))
    {
        presetDefaults.keyboard.restoreDefaults(parseControlScheme(*scheme));
    }

    for (const GameSettings &defaults : {GameSettings::createDefault(), presetDefaults})
    {
        for (const SettingsEntry &entry : serializeGameSettings(defaults))
        {
            shippedValues[entry.section + '.' + entry.key].insert(entry.value);
        }
    }

    // Which keys this version reads at all.
    std::string error;
    parseGameSettingsDocument(document, error);
    std::vector<SettingsEntry> kept;

    for (const SettingsEntry &entry : document.entries)
    {
        const std::string name = entry.section + '.' + entry.key;
        const auto shipped = shippedValues.find(name);

        // Release packages wrote their installation's asset root; the game now finds installed assets itself.
        if (name == "assets.root")
        {
            if (!entry.value.empty() && entry.value != "assets" && entry.value != "/app/share/openyamm/assets")
            {
                kept.push_back(entry);
            }
            continue;
        }

        if (entry.section == "profile" || isRememberedState(name) || shipped == shippedValues.end())
        {
            kept.push_back(entry);
            continue;
        }

        if (!document.consulted.contains(name))
        {
            continue;
        }

        const std::optional<std::string> value = normalizedSettingsValue(entry);

        if (!value || !shipped->second.contains(*value))
        {
            kept.push_back(entry);
        }
    }

    return documentWithEntries(kept);
}
}

std::optional<GameSettings> loadGameSettingsFromText(const std::string &text, std::string &error)
{
    constexpr uint32_t PlayerChoicesSettingsProfileVersion = 5;
    const IniDocument document = parseIniDocument(text);

    if (documentProfileVersion(document) < PlayerChoicesSettingsProfileVersion)
    {
        return parseGameSettingsDocument(withoutShippedDefaults(document), error);
    }

    return parseGameSettingsDocument(document, error);
}

std::vector<SettingsEntry> serializeGameSettings(const GameSettings &settings)
{
    SettingsSerializer serializer;
    serializer.section("assets");
    serializer.add("root", settings.assetRoot);
    serializer.section("audio");
    serializer.add("sound_volume", std::clamp(settings.soundVolume, 0, 9));
    serializer.add("music_volume", std::clamp(settings.musicVolume, 0, 9));
    serializer.add("voice_volume", std::clamp(settings.voiceVolume, 0, 9));
    serializer.section("controls");
    serializer.add("turn_rate", turnRateModeString(settings.turnRate));
    serializer.add("control_scheme", controlSchemeString(settings.controlScheme));
    serializer.add("walksound", boolValue(settings.walksound));
    serializer.add("show_hits", boolValue(settings.showHits));
    serializer.add("always_run", boolValue(settings.alwaysRun));
    serializer.add("flip_on_exit", boolValue(settings.flipOnExit));
    serializer.add("mouse_sensitivity", std::clamp(settings.mouseSensitivity, 0, 100));
    serializer.add("invert_mouse_y", boolValue(settings.invertMouseY));
    serializer.section("gameplay");
    serializer.add("keyboard_interaction_depth", std::clamp(settings.keyboardInteractionDepth, 32, 4096));
    serializer.add("mouse_interaction_depth", std::clamp(settings.mouseInteractionDepth, 32, 4096));
    serializer.add("combat_text", boolValue(settings.combatText));
    serializer.add("enemy_health_bars", settings.enemyHealthBarMode);
    serializer.add("enemy_health_bar_values", settings.enemyHealthBarValues);
    serializer.add("enemy_health_bar_damage_trail", boolValue(settings.enemyHealthBarDamageTrail));
    serializer.add("quest_markers", boolValue(settings.questMarkers));
    serializer.add("party_frame", boolValue(settings.partyFrame));
    serializer.add("melee_hit_blood_effects", boolValue(settings.meleeHitBloodEffects));
    serializer.add("melee_hit_feedback", boolValue(settings.meleeHitFeedback));
    serializer.add("melee_hit_effects", boolValue(settings.meleeHitEffects));
    serializer.add("melee_hit_flash", boolValue(settings.meleeHitFlash));
    serializer.add("melee_camera_kick", boolValue(settings.meleeCameraKick));
    serializer.add("context_action_popup", boolValue(settings.contextActionPopup));
    serializer.section("startup");
    serializer.add("start_in_main_menu", boolValue(settings.startInMainMenu));
    serializer.add("save_file", settings.startupSaveFile);
    serializer.section("features");
    serializer.add("bolster_monsters", boolValue(settings.bolsterMonsters));
    serializer.add("indoor_pathfinding", boolValue(settings.indoorPathfinding));
    serializer.add("outdoor_pathfinding", boolValue(settings.outdoorPathfinding));
    serializer.add("blaster_skill_scaling", blasterSkillScalingValue(settings.blasterSkillScaling));
    serializer.add("blaster_min_recovery", blasterMinimumRecoveryTicksValue(settings.blasterMinimumRecoveryTicks));
    serializer.section("logging");
    serializer.add("indoor_visibility", boolValue(settings.logIndoorVisibility));
    serializer.add("indoor_pathfinding", boolValue(settings.logIndoorPathfinding));
    serializer.add("outdoor_pathfinding", boolValue(settings.logOutdoorPathfinding));
    serializer.add("fps_trace", boolValue(settings.fpsTrace));
    serializer.add("performance_trace", boolValue(settings.performanceTrace));
    serializer.add("hitch_trace", boolValue(settings.hitchTrace));
    serializer.add("collision_trace", boolValue(settings.collisionTrace));
    serializer.add("gameplay_trace", boolValue(settings.gameplayTrace));
    serializer.add("gameplay_trace_file", settings.gameplayTraceFile);
    serializer.add("gameplay_trace_append", boolValue(settings.gameplayTraceAppend));
    serializer.add("combat_trace", boolValue(settings.combatTrace));
    serializer.add("combat_trace_file", settings.combatTraceFile);
    serializer.add("combat_trace_append", boolValue(settings.combatTraceAppend));
    serializer.add("hitch_threshold_ms", std::clamp(settings.hitchThresholdMilliseconds, 0.1f, 1000.0f));
    serializer.section("input");

    for (const KeyboardBindingDefinition &definition : keyboardBindingDefinitions())
    {
        serializer.add(definition.iniKey, inputBindingName(settings.keyboard.binding(definition.action)));
    }

    serializer.section("video");
    serializer.add("blood_splats", boolValue(settings.bloodSplats));
    serializer.add("colored_lights", boolValue(settings.coloredLights));
    serializer.add("warm_torch_light", boolValue(settings.warmTorchLight));
    serializer.add("tinting", boolValue(settings.tinting));
    serializer.add("shadows", boolValue(settings.shadows));
    serializer.add("model_shadow_quality", std::clamp(settings.modelShadowQuality, 0, 3));
    serializer.add("model_lods", boolValue(settings.modelLods));
    serializer.add("creature_outlines", boolValue(settings.creatureOutlines));
    serializer.add("sprite_outline", boolValue(settings.spriteOutline));
    serializer.add("texture_filtering", boolValue(settings.textureFiltering));
    serializer.add("ambient_occlusion", boolValue(settings.ambientOcclusion));
    serializer.add("ambient_occlusion_strength", settings.ambientOcclusionStrength);
    serializer.add("bloom", boolValue(settings.bloom));
    serializer.add("bloom_strength", settings.bloomStrength);
    serializer.add("cinematic_grading", boolValue(settings.cinematicGrading));
    serializer.add("cinematic_strength", settings.cinematicStrength);
    serializer.add("sharpening", settings.sharpening);
    serializer.add("antialiasing", antialiasingValue(settings.antialiasing));
    serializer.add("lightmaps", boolValue(settings.lightmaps));
    serializer.add("baked_sun_strength", *getBakedLightingSetting(settings, "baked_sun_strength"));
    serializer.add("baked_sky_strength", *getBakedLightingSetting(settings, "baked_sky_strength"));
    serializer.add("baked_sun_color", *getBakedLightingSetting(settings, "baked_sun_color"));
    serializer.add("baked_sky_color", *getBakedLightingSetting(settings, "baked_sky_color"));
    serializer.add("terrain_decorations", boolValue(settings.terrainDecorations));
    serializer.add("water_reflections", boolValue(settings.waterReflections));
    serializer.add("water_movement_ripples", boolValue(settings.waterMovementRipples));
    serializer.add("water_sprite_reflections", boolValue(settings.waterSpriteReflections));
    serializer.add("water_reflection_size", std::clamp(settings.waterReflectionSize, 128, 2048));
    serializer.add("terrain_subdivision", settings.terrainSubdivision);
    serializer.add("terrain_antitiling", boolValue(settings.terrainAntiTiling));
    serializer.add("sky_resolution_scale", std::clamp(settings.skyResolutionScale, 0.25f, 1.0f));
    serializer.add("weather_quality", weatherQualityValue(settings.weatherQuality));
    serializer.add("light_grid", lightGridQualityValue(settings.lightGrid));
    serializer.add("rain_ripples", boolValue(settings.rainRipples));
    serializer.add("wet_surfaces", boolValue(settings.wetSurfaces));
    serializer.add("terrain_specular", boolValue(settings.terrainSpecular));
    serializer.add("terrain_filtering", settings.terrainFiltering);
    serializer.add("terrain_anisotropy", settings.terrainAnisotropy);
    serializer.add("bmodel_filtering", settings.bmodelFiltering);
    serializer.add("billboard_filtering", settings.billboardFiltering);
    serializer.add("ui_filtering", settings.uiFiltering);
    serializer.add("text_filtering", settings.textFiltering);
    serializer.add("minimap_filtering", settings.minimapFiltering);
    serializer.add("view_distance", settings.viewDistance);
    serializer.add("outdoor_billboard_depth_slice", std::clamp(settings.outdoorBillboardDepthSlice, 0.0f, 8192.0f));
    serializer.add("skip_event_cutscenes", boolValue(settings.skipEventCutscenes));
    serializer.add("wait_for_level_sprites", boolValue(settings.waitForLevelSprites));
    serializer.add("window_mode", windowModeString(settings.windowMode));
    serializer.add(
        "resolution",
        std::clamp(settings.resolutionWidth, 320, 16384),
        'x',
        std::clamp(settings.resolutionHeight, 200, 16384));
    serializer.add("vsync", boolValue(settings.verticalSync));
    serializer.section("video_quality");
    serializer.add("sky", Engine::assetScaleTierToString(settings.assetScaleProfile.sky));
    serializer.add("decorations", Engine::assetScaleTierToString(settings.assetScaleProfile.decorations));
    serializer.add("prefer_restored_icons", boolValue(settings.assetScaleProfile.preferRestoredIcons));
    serializer.add("icons", Engine::assetScaleTierToString(settings.assetScaleProfile.icons));
    serializer.section("updates");
    serializer.add("check_for_updates", settings.updateCheck);
    serializer.add("url", settings.updateUrl);
    serializer.section("debug");
    serializer.add("preseed_party", boolValue(settings.preseedParty));
    serializer.add("party_seed_roster_id", settings.partySeedRosterId);
    serializer.add("start_world", settings.startWorldId);
    serializer.add("start_map_file", settings.startMapFile);
    serializer.add("override_start_position", boolValue(settings.overrideStartPosition));
    serializer.add("start_x", settings.startX);
    serializer.add("start_y", settings.startY);
    serializer.add("start_z", settings.startZ);
    serializer.add("start_flying", boolValue(settings.startFlying));
    serializer.add("movement_speed_multiplier", settings.movementSpeedMultiplier);
    serializer.add("turbo_movement", boolValue(settings.turboMovementEnabled));
    serializer.add("immortal", boolValue(settings.immortal));
    serializer.add("unlimited_mana", boolValue(settings.unlimitedMana));
    serializer.add("new_game_god_lich", boolValue(settings.newGameGodLich));
    serializer.add("allow_incomplete_character_creation", boolValue(settings.allowIncompleteCharacterCreation));
    serializer.add("console", boolValue(settings.debugConsole));
    serializer.add("actor_models", boolValue(settings.actorModels));
    return serializer.takeEntries();
}

std::vector<SettingsEntry> settingsEntriesToSave(const GameSettings &settings)
{
    const std::vector<SettingsEntry> entries = serializeGameSettings(settings);
    const std::vector<SettingsEntry> defaults = serializeGameSettings(GameSettings::createDefault());
    // Key bindings follow the defaults of the player's control preset, as the loader restores them.
    GameSettings presetDefaults = GameSettings::createDefault();
    presetDefaults.controlScheme = settings.controlScheme;
    presetDefaults.keyboard.restoreDefaults(settings.controlScheme);
    const std::vector<SettingsEntry> presetDefaultEntries = serializeGameSettings(presetDefaults);
    std::vector<SettingsEntry> selected;

    // The writer only writes the current format; a newer file keeps its version.
    const GameSettings platformDefaults = GameSettings::createDefault();
    selected.push_back({"profile", "name",
                        settings.settingsProfileName.empty() ? platformDefaults.settingsProfileName
                                                             : settings.settingsProfileName});
    selected.push_back(
        {"profile", "version",
         std::to_string(std::max(settings.settingsProfileVersion, CurrentSettingsProfileVersion))});

    for (size_t index = 0; index < entries.size(); ++index)
    {
        const SettingsEntry &entry = entries[index];
        const SettingsEntry &defaultEntry = entry.section == "input" ? presetDefaultEntries[index] : defaults[index];
        const std::string name = entry.section + '.' + entry.key;

        if (isRememberedState(name) || settings.fileState.storedKeys.contains(name)
            || entry.value != defaultEntry.value)
        {
            selected.push_back(entry);
        }
    }

    // Unknown keys go after the known keys of their section; unknown sections follow at the end.
    for (const SettingsEntry &unknown : settings.fileState.unknownEntries)
    {
        auto insertAt = selected.end();

        for (auto it = selected.begin(); it != selected.end(); ++it)
        {
            if (it->section == unknown.section)
            {
                insertAt = std::next(it);
            }
        }

        selected.insert(insertAt, unknown);
    }

    return selected;
}

bool saveGameSettings(const std::filesystem::path &path, const GameSettings &settings, std::string &error)
{
    std::ostringstream output;
    output
        << "; OpenYAMM settings: only the values you changed. Everything else follows the game's defaults.\n"
        << "; Volumes use the original-style 0..9 scale.\n";
    std::string currentSection;

    for (const SettingsEntry &entry : settingsEntriesToSave(settings))
    {
        if (entry.section != currentSection)
        {
            output << "\n[" << entry.section << "]\n";
            currentSection = entry.section;
        }

        output << entry.key << '=' << entry.value << '\n';
    }

    const std::filesystem::path temporaryPath = path.string() + ".tmp";
    const std::filesystem::path backupPath = path.string() + ".bak";
    {
        std::ofstream file(temporaryPath, std::ios::binary | std::ios::trunc);
        file << output.str();
        file.close();

        if (!file)
        {
            std::error_code removeError;
            std::filesystem::remove(temporaryPath, removeError);
            error = "Unable to write settings file";
            return false;
        }
    }

    std::error_code fileError;

    if (std::filesystem::exists(path, fileError))
    {
        std::filesystem::copy_file(path, backupPath, std::filesystem::copy_options::overwrite_existing, fileError);
    }

    std::filesystem::rename(temporaryPath, path, fileError);

    if (fileError)
    {
        error = "Unable to replace settings file: " + fileError.message();
        return false;
    }

    error.clear();
    return true;
}

void releaseStoredSettings(GameSettings &settings, const std::vector<std::string> &names)
{
    std::erase_if(
        settings.fileState.storedKeys,
        [&names](const std::string &storedKey)
        {
            const size_t separator = storedKey.find('.');
            const std::string section = storedKey.substr(0, separator + 1);
            const std::string key = storedKey.substr(separator + 1);
            return std::find_if(
                       names.begin(),
                       names.end(),
                       [&](const std::string &name) { return name == key || name == section; })
                != names.end();
        });
}
}
