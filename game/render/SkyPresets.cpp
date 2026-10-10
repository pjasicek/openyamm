#include "game/render/SkyPresets.h"

#include "game/StringUtils.h"
#include "game/render/SkyClock.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <exception>
#include <functional>
#include <set>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<SkyValueInfo, SkyValueCount> SkyValueInfos = {{
    {"zenith", 3},
    {"horizon", 3},
    {"horizon_exponent", 1},
    {"sun_glow", 3},
    {"sun_glow_exponent", 1},
    {"sun_glow_strength", 1},
    {"fog", 3},
    {"sun_disc", 3},
    {"sun_disc_visibility", 1},
    {"cloud_lit", 3},
    {"cloud_shadow", 3},
    {"ambient_tint", 3},
    {"water_sun", 3},
    {"water_sky", 3},
    {"stars", 1},
    {"moon_visibility", 1},
    {"aerial_haze", 1},
}};

constexpr float MaxSkyValue = 4.0f;

float smoothStep(float value)
{
    return value * value * (3.0f - 2.0f * value);
}

class Parser
{
public:
    explicit Parser(std::string &errorMessage)
        : m_errorMessage(errorMessage)
    {
    }

    bool fail(const std::string &message)
    {
        if (m_errorMessage.empty())
        {
            m_errorMessage = message;
        }

        return false;
    }

    bool checkKeys(const YAML::Node &node, std::initializer_list<const char *> allowed, const std::string &where)
    {
        if (!node.IsMap())
        {
            return fail(where + " must be a map");
        }

        for (const auto &entry : node)
        {
            const std::string key = entry.first.as<std::string>();

            if (std::none_of(allowed.begin(), allowed.end(), [&key](const char *pName) { return key == pName; }))
            {
                return fail(where + " has unknown key '" + key + "'");
            }
        }

        return true;
    }

    bool readFloat(const YAML::Node &node, float &value, float minimum, float maximum, const std::string &where)
    {
        try
        {
            const float parsed = node.as<float>();

            if (!std::isfinite(parsed) || parsed < minimum || parsed > maximum)
            {
                return fail(where + " must be within [" + std::to_string(minimum) + ", "
                    + std::to_string(maximum) + "]");
            }

            value = parsed;
            return true;
        }
        catch (const std::exception &)
        {
            return fail(where + " must be a number");
        }
    }

    bool readOptionalFloat(const YAML::Node &parent, const char *pKey, float &value, float minimum, float maximum,
        const std::string &where)
    {
        const YAML::Node node = parent[pKey];
        return !node || readFloat(node, value, minimum, maximum, where + "." + pKey);
    }

    bool readOptionalString(const YAML::Node &parent, const char *pKey, std::string &value, const std::string &where)
    {
        const YAML::Node node = parent[pKey];

        if (!node)
        {
            return true;
        }

        if (!node.IsScalar())
        {
            return fail(where + "." + pKey + " must be text");
        }

        value = toLowerCopy(node.as<std::string>());
        return true;
    }

    bool readValue(const YAML::Node &node, SkyValue valueId, SkyColor &value, const std::string &where)
    {
        const SkyValueInfo &info = skyValueInfo(valueId);

        if (info.components == 1)
        {
            if (!readFloat(node, value[0], 0.0f, valueId == SkyValue::HorizonExponent
                    || valueId == SkyValue::SunGlowExponent ? 512.0f : MaxSkyValue, where))
            {
                return false;
            }

            value[1] = value[0];
            value[2] = value[0];
            return true;
        }

        if (!node.IsSequence() || node.size() != 3)
        {
            return fail(where + " must be [r, g, b]");
        }

        for (size_t component = 0; component < 3; ++component)
        {
            if (!readFloat(node[component], value[component], 0.0f, MaxSkyValue, where))
            {
                return false;
            }
        }

        return true;
    }

    bool applyKeys(const YAML::Node &keysNode, SkyPreset &preset, const std::string &where)
    {
        if (!keysNode.IsSequence() || keysNode.size() == 0)
        {
            return fail(where + ".keys must be a non-empty list");
        }

        std::array<SkyTrack, SkyValueCount> tracks;

        for (const YAML::Node &keyNode : keysNode)
        {
            if (!keyNode.IsMap())
            {
                return fail(where + ".keys entries must be maps");
            }

            const YAML::Node timeNode = keyNode["time"];
            const std::optional<int> minute =
                timeNode && timeNode.IsScalar() ? parseClockMinutes(timeNode.as<std::string>()) : std::nullopt;

            if (!minute)
            {
                return fail(where + ".keys entry requires time: \"HH:MM\"");
            }

            const std::string keyWhere = where + ".keys[" + timeNode.as<std::string>() + "]";

            for (const auto &entry : keyNode)
            {
                const std::string field = entry.first.as<std::string>();

                if (field == "time")
                {
                    continue;
                }

                const auto infoIt = std::find_if(SkyValueInfos.begin(), SkyValueInfos.end(),
                    [&field](const SkyValueInfo &info) { return field == info.pName; });

                if (infoIt == SkyValueInfos.end())
                {
                    return fail(keyWhere + " has unknown value '" + field + "'");
                }

                const SkyValue valueId = static_cast<SkyValue>(infoIt - SkyValueInfos.begin());
                SkyTrackKey key = {*minute, {}};

                if (!readValue(entry.second, valueId, key.value, keyWhere + "." + field))
                {
                    return false;
                }

                SkyTrack &track = tracks[static_cast<size_t>(valueId)];

                if (std::any_of(track.begin(), track.end(),
                        [&key](const SkyTrackKey &existing) { return existing.minute == key.minute; }))
                {
                    return fail(keyWhere + " repeats " + field + " at the same time");
                }

                track.push_back(key);
            }
        }

        for (size_t index = 0; index < SkyValueCount; ++index)
        {
            if (tracks[index].empty())
            {
                continue;
            }

            std::sort(tracks[index].begin(), tracks[index].end(),
                [](const SkyTrackKey &left, const SkyTrackKey &right) { return left.minute < right.minute; });
            preset.tracks[index] = std::move(tracks[index]);
        }

        return true;
    }

    bool applyCloudLayer(const YAML::Node &node, SkyCloudLayer &layer, const std::string &where)
    {
        if (const YAML::Node modeNode = node["mode"]; modeNode)
        {
            const std::string mode = modeNode.IsScalar() ? toLowerCopy(modeNode.as<std::string>()) : "";

            if (mode != "color" && mode != "density")
            {
                return fail(where + ".mode must be color or density");
            }

            layer.color = mode == "color";
        }

        return checkKeys(node, {"texture", "mode", "scale", "speed", "direction_deg", "coverage", "softness", "opacity",
                   "curvature"}, where)
            && readOptionalString(node, "texture", layer.texture, where)
            && readOptionalFloat(node, "scale", layer.scale, 0.001f, 64.0f, where)
            && readOptionalFloat(node, "speed", layer.speed, 0.0f, 1.0f, where)
            && readOptionalFloat(node, "direction_deg", layer.directionDegrees, -360.0f, 360.0f, where)
            && readOptionalFloat(node, "coverage", layer.coverage, 0.0f, 1.0f, where)
            && readOptionalFloat(node, "softness", layer.softness, 0.001f, 1.0f, where)
            && readOptionalFloat(node, "opacity", layer.opacity, 0.0f, 1.0f, where)
            && readOptionalFloat(node, "curvature", layer.curvature, 0.01f, 2.0f, where)
            && (!layer.texture.empty() || fail(where + " requires a texture"));
    }

    bool readOptionalTint(const YAML::Node &parent, const char *pKey, SkyColor &value, const std::string &where)
    {
        const YAML::Node node = parent[pKey];

        if (!node)
        {
            return true;
        }

        if (!node.IsSequence() || node.size() != 3)
        {
            return fail(where + "." + pKey + " must be [r, g, b]");
        }

        for (size_t component = 0; component < 3; ++component)
        {
            if (!readFloat(node[component], value[component], 0.0f, MaxSkyValue, where + "." + pKey))
            {
                return false;
            }
        }

        return true;
    }

    bool applyTheme(const YAML::Node &node, SkyTheme &theme, const std::string &where)
    {
        return checkKeys(node, {"preset", "sky_tint", "sun_tint", "cloud_tint", "saturation", "haze", "stars"}, where)
            && readOptionalString(node, "preset", theme.preset, where)
            && readOptionalTint(node, "sky_tint", theme.skyTint, where)
            && readOptionalTint(node, "sun_tint", theme.sunTint, where)
            && readOptionalTint(node, "cloud_tint", theme.cloudTint, where)
            && readOptionalFloat(node, "saturation", theme.saturation, 0.0f, 2.0f, where)
            && readOptionalFloat(node, "haze", theme.haze, 0.0f, 1.0f, where)
            && readOptionalFloat(node, "stars", theme.starScale, 0.0f, 2.0f, where);
    }

    bool applyPreset(const YAML::Node &node, SkyPreset &preset, const std::string &where)
    {
        if (!checkKeys(node, {"inherits", "keys", "sun_disc_degrees", "moon_disc_degrees", "below_horizon",
                "fog_tint_sky_mix", "horizon_ring", "stars", "clouds", "storm", "draw_sky"}, where))
        {
            return false;
        }

        if (const YAML::Node keysNode = node["keys"]; keysNode && !applyKeys(keysNode, preset, where))
        {
            return false;
        }

        if (!readOptionalFloat(node, "sun_disc_degrees", preset.sunDiscDegrees, 0.0f, 20.0f, where)
            || !readOptionalFloat(node, "moon_disc_degrees", preset.moonDiscDegrees, 0.0f, 20.0f, where)
            || !readOptionalFloat(node, "fog_tint_sky_mix", preset.fogTintSkyMix, 0.0f, 1.0f, where))
        {
            return false;
        }

        if (const YAML::Node belowNode = node["below_horizon"]; belowNode)
        {
            const std::string mode = belowNode.IsScalar() ? toLowerCopy(belowNode.as<std::string>()) : "";

            if (mode == "fog")
            {
                preset.belowHorizon = SkyBelowHorizon::Fog;
            }
            else if (mode == "sky")
            {
                preset.belowHorizon = SkyBelowHorizon::Sky;
            }
            else if (mode == "flat")
            {
                preset.belowHorizon = SkyBelowHorizon::Flat;
            }
            else
            {
                return fail(where + ".below_horizon must be fog, sky or flat");
            }
        }

        if (const YAML::Node drawNode = node["draw_sky"]; drawNode)
        {
            try
            {
                preset.drawSky = drawNode.as<bool>();
            }
            catch (const std::exception &)
            {
                return fail(where + ".draw_sky must be a boolean");
            }
        }

        if (const YAML::Node ringNode = node["horizon_ring"]; ringNode)
        {
            const std::string ringWhere = where + ".horizon_ring";

            if (!checkKeys(ringNode, {"texture", "opacity", "height"}, ringWhere)
                || !readOptionalString(ringNode, "texture", preset.horizonRing.texture, ringWhere)
                || !readOptionalFloat(ringNode, "opacity", preset.horizonRing.opacity, 0.0f, 1.0f, ringWhere)
                || !readOptionalFloat(ringNode, "height", preset.horizonRing.height, 0.0f, 1.0f, ringWhere))
            {
                return false;
            }
        }

        if (const YAML::Node starsNode = node["stars"]; starsNode)
        {
            const std::string starsWhere = where + ".stars";

            if (!checkKeys(starsNode, {"texture", "density", "brightness", "pole_elevation_deg"}, starsWhere)
                || !readOptionalString(starsNode, "texture", preset.stars.texture, starsWhere)
                || !readOptionalFloat(starsNode, "density", preset.stars.density, 0.0f, 1.0f, starsWhere)
                || !readOptionalFloat(starsNode, "brightness", preset.stars.brightness, 0.0f, 4.0f, starsWhere)
                || !readOptionalFloat(starsNode, "pole_elevation_deg", preset.stars.poleElevationDegrees, 0.0f,
                    90.0f, starsWhere))
            {
                return false;
            }
        }

        if (const YAML::Node stormNode = node["storm"]; stormNode)
        {
            try
            {
                preset.storm = stormNode.as<bool>();
            }
            catch (const std::exception &)
            {
                return fail(where + ".storm must be a boolean");
            }
        }

        if (const YAML::Node cloudsNode = node["clouds"]; cloudsNode)
        {
            if (!cloudsNode.IsSequence() || cloudsNode.size() > 2)
            {
                return fail(where + ".clouds must be a list of at most two layers");
            }

            preset.clouds.clear();

            for (size_t index = 0; index < cloudsNode.size(); ++index)
            {
                SkyCloudLayer layer = {};

                if (!applyCloudLayer(cloudsNode[index], layer, where + ".clouds[" + std::to_string(index) + "]"))
                {
                    return false;
                }

                preset.clouds.push_back(std::move(layer));
            }
        }

        return true;
    }

private:
    std::string &m_errorMessage;
};
}

const SkyValueInfo &skyValueInfo(SkyValue value)
{
    return SkyValueInfos[static_cast<size_t>(value)];
}

SkyColor evaluateSkyTrack(const SkyTrack &track, float minuteOfDay)
{
    if (track.empty())
    {
        return {};
    }

    if (track.size() == 1)
    {
        return track.front().value;
    }

    const float dayMinutes = static_cast<float>(SkyMinutesPerDay);
    const float minute = std::fmod(std::fmod(minuteOfDay, dayMinutes) + dayMinutes, dayMinutes);
    size_t nextIndex = 0;

    while (nextIndex < track.size() && static_cast<float>(track[nextIndex].minute) <= minute)
    {
        ++nextIndex;
    }

    const SkyTrackKey &next = track[nextIndex % track.size()];
    const SkyTrackKey &previous = track[(nextIndex + track.size() - 1) % track.size()];
    float span = static_cast<float>(next.minute - previous.minute);
    float elapsed = minute - static_cast<float>(previous.minute);

    if (span <= 0.0f)
    {
        span += dayMinutes;
    }

    if (elapsed < 0.0f)
    {
        elapsed += dayMinutes;
    }

    const float blend = smoothStep(std::clamp(elapsed / span, 0.0f, 1.0f));
    SkyColor result = {};

    for (size_t component = 0; component < 3; ++component)
    {
        result[component] = previous.value[component] + (next.value[component] - previous.value[component]) * blend;
    }

    return result;
}

bool SkyPresetLibrary::loadFromYaml(const std::string &yamlText, std::string &errorMessage)
{
    *this = {};
    errorMessage.clear();
    Parser parser(errorMessage);
    YAML::Node root;

    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    if (!parser.checkKeys(root, {"version", "transition_seconds", "fallback", "special", "weather_ladder",
            "aliases", "presets", "themes", "maps"}, "sky library"))
    {
        return false;
    }

    if (!root["version"] || root["version"].as<int>(0) != 1)
    {
        return parser.fail("sky library version must be 1");
    }

    SkyPresetLibrary library;

    if (!parser.readOptionalFloat(root, "transition_seconds", library.m_transitionSeconds, 0.0f, 600.0f, "sky"))
    {
        return false;
    }

    const YAML::Node presetsNode = root["presets"];

    if (!presetsNode || !presetsNode.IsMap() || presetsNode.size() == 0)
    {
        return parser.fail("sky library requires presets");
    }

    std::unordered_map<std::string, YAML::Node> presetNodes;

    for (const auto &entry : presetsNode)
    {
        presetNodes[toLowerCopy(entry.first.as<std::string>())] = entry.second;
    }

    std::set<std::string> resolving;
    std::function<bool(const std::string &)> resolve = [&](const std::string &name) -> bool
    {
        if (library.m_presets.contains(name))
        {
            return true;
        }

        const auto nodeIt = presetNodes.find(name);

        if (nodeIt == presetNodes.end())
        {
            return parser.fail("sky preset '" + name + "' is not defined");
        }

        if (!resolving.insert(name).second)
        {
            return parser.fail("sky preset '" + name + "' inherits from itself");
        }

        SkyPreset preset = {};
        const YAML::Node &node = nodeIt->second;

        if (const YAML::Node inheritsNode = node["inherits"]; inheritsNode)
        {
            const std::string parent = inheritsNode.IsScalar() ? toLowerCopy(inheritsNode.as<std::string>()) : "";

            if (parent.empty() || !resolve(parent))
            {
                return parser.fail("sky preset '" + name + "' has an invalid parent");
            }

            preset = library.m_presets.at(parent);
        }

        if (!parser.applyPreset(node, preset, "sky preset '" + name + "'"))
        {
            return false;
        }

        for (size_t index = 0; index < SkyValueCount; ++index)
        {
            if (preset.tracks[index].empty())
            {
                return parser.fail("sky preset '" + name + "' has no keys for "
                    + SkyValueInfos[index].pName + " (define it here or in a parent)");
            }
        }

        preset.name = name;
        resolving.erase(name);
        library.m_presets.emplace(name, std::move(preset));
        return true;
    };

    for (const auto &entry : presetNodes)
    {
        if (!resolve(entry.first))
        {
            return false;
        }
    }

    const auto requirePreset = [&](const std::string &name, const std::string &where) -> bool
    {
        return library.m_presets.contains(name) || parser.fail(where + " names unknown preset '" + name + "'");
    };

    library.m_fallback = root["fallback"] && root["fallback"].IsScalar()
        ? toLowerCopy(root["fallback"].as<std::string>()) : std::string();

    if (library.m_fallback.empty() || !requirePreset(library.m_fallback, "fallback"))
    {
        return parser.fail("sky library requires a valid fallback preset");
    }

    if (const YAML::Node specialNode = root["special"]; specialNode)
    {
        SkySpecialPresets &specials = library.m_specials;

        if (!parser.checkKeys(specialNode, {"underwater", "red_fog", "always_light", "always_dark", "rain", "snow"},
                "special")
            || !parser.readOptionalString(specialNode, "underwater", specials.underwater, "special")
            || !parser.readOptionalString(specialNode, "red_fog", specials.redFog, "special")
            || !parser.readOptionalString(specialNode, "always_light", specials.alwaysLight, "special")
            || !parser.readOptionalString(specialNode, "always_dark", specials.alwaysDark, "special")
            || !parser.readOptionalString(specialNode, "rain", specials.rain, "special")
            || !parser.readOptionalString(specialNode, "snow", specials.snow, "special"))
        {
            return false;
        }

        for (const std::string *pName : {&specials.underwater, &specials.redFog, &specials.alwaysLight,
                 &specials.alwaysDark, &specials.rain, &specials.snow})
        {
            if (!pName->empty() && !requirePreset(*pName, "special"))
            {
                return false;
            }
        }
    }

    if (const YAML::Node ladderNode = root["weather_ladder"]; ladderNode)
    {
        if (!ladderNode.IsSequence() || ladderNode.size() < 2)
        {
            return parser.fail("weather_ladder must list at least two presets from clear to storm");
        }

        for (const YAML::Node &entry : ladderNode)
        {
            const std::string name = entry.IsScalar() ? toLowerCopy(entry.as<std::string>()) : "";

            if (!requirePreset(name, "weather_ladder"))
            {
                return false;
            }

            library.m_weatherLadder.push_back(name);
        }
    }

    if (const YAML::Node aliasesNode = root["aliases"]; aliasesNode)
    {
        if (!aliasesNode.IsMap())
        {
            return parser.fail("aliases must map sky texture names to presets");
        }

        for (const auto &entry : aliasesNode)
        {
            const std::string skyName = toLowerCopy(entry.first.as<std::string>());
            const std::string presetName = entry.second.IsScalar() ? toLowerCopy(entry.second.as<std::string>()) : "";

            if (!requirePreset(presetName, "alias '" + skyName + "'"))
            {
                return false;
            }

            library.m_aliases[skyName] = presetName;
        }
    }

    if (const YAML::Node themesNode = root["themes"]; themesNode)
    {
        if (!themesNode.IsMap())
        {
            return parser.fail("themes must map theme names to settings");
        }

        for (const auto &entry : themesNode)
        {
            SkyTheme theme = {};
            theme.name = toLowerCopy(entry.first.as<std::string>());

            if (!parser.applyTheme(entry.second, theme, "sky theme '" + theme.name + "'")
                || (!theme.preset.empty() && !requirePreset(theme.preset, "sky theme '" + theme.name + "'")))
            {
                return false;
            }

            library.m_themes[theme.name] = std::move(theme);
        }
    }

    if (const YAML::Node mapsNode = root["maps"]; mapsNode)
    {
        if (!mapsNode.IsMap())
        {
            return parser.fail("maps must map map file names to themes");
        }

        for (const auto &entry : mapsNode)
        {
            const std::string mapName = toLowerCopy(entry.first.as<std::string>());
            const std::string themeName = entry.second.IsScalar() ? toLowerCopy(entry.second.as<std::string>()) : "";

            if (!library.m_themes.contains(themeName))
            {
                return parser.fail("map '" + mapName + "' names unknown sky theme '" + themeName + "'");
            }

            library.m_mapThemes[mapName] = themeName;
        }
    }

    *this = std::move(library);
    return true;
}

const SkyPreset *SkyPresetLibrary::find(const std::string &name) const
{
    const auto presetIt = m_presets.find(name);
    return presetIt != m_presets.end() ? &presetIt->second : nullptr;
}

const SkyPreset *SkyPresetLibrary::fallback() const
{
    return find(m_fallback);
}

std::string SkyPresetLibrary::presetForSkyName(const std::string &skyTextureName) const
{
    const auto aliasIt = m_aliases.find(toLowerCopy(skyTextureName));
    return aliasIt != m_aliases.end() ? aliasIt->second : std::string();
}

std::string SkyPresetLibrary::presetForWeatherState(int state, int stateCount) const
{
    if (m_weatherLadder.empty() || state < 0)
    {
        return {};
    }

    const int lastLadderIndex = static_cast<int>(m_weatherLadder.size()) - 1;
    const int lastState = std::max(stateCount - 1, 1);
    const int ladderIndex = static_cast<int>(
        std::lround(static_cast<float>(std::clamp(state, 0, lastState)) * lastLadderIndex / lastState));
    return m_weatherLadder[static_cast<size_t>(std::clamp(ladderIndex, 0, lastLadderIndex))];
}

const SkySpecialPresets &SkyPresetLibrary::specials() const
{
    return m_specials;
}

const SkyTheme *SkyPresetLibrary::themeForMap(const std::string &mapFileName) const
{
    const auto mapIt = m_mapThemes.find(toLowerCopy(mapFileName));
    return mapIt != m_mapThemes.end() ? findTheme(mapIt->second) : nullptr;
}

const SkyTheme *SkyPresetLibrary::findTheme(const std::string &name) const
{
    const auto themeIt = m_themes.find(name);
    return themeIt != m_themes.end() ? &themeIt->second : nullptr;
}

float SkyPresetLibrary::transitionSeconds() const
{
    return m_transitionSeconds;
}

std::vector<std::string> SkyPresetLibrary::textureNames() const
{
    std::set<std::string> names;

    for (const auto &entry : m_presets)
    {
        const SkyPreset &preset = entry.second;

        for (const SkyCloudLayer &layer : preset.clouds)
        {
            names.insert(layer.texture);
        }

        if (!preset.horizonRing.texture.empty())
        {
            names.insert(preset.horizonRing.texture);
        }

        if (!preset.stars.texture.empty())
        {
            names.insert(preset.stars.texture);
        }
    }

    return {names.begin(), names.end()};
}

bool SkyPresetLibrary::empty() const
{
    return m_presets.empty();
}
}
