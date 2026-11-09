#include "game/outdoor/WeatherModel.h"

#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <exception>
#include <initializer_list>

namespace OpenYAMM::Game
{
namespace
{
constexpr double MinutesPerDay = 1440.0;
constexpr int DaysPerMonth = 28;
constexpr float TwoPi = 6.28318530717958647692f;
// Day-to-day calm wind blends over the first hours after midnight instead of turning at once.
constexpr float WindBlendMinutes = 120.0f;
constexpr float WetnessStepMinutes = 5.0f;
// Rain below this reads as the last drops: the sky stays overcast rather than switching to the rain ladder entry.
constexpr float LadderRainIntensity = 0.12f;
// MMerge fog: weak and strong distances are these divided by the ladder position (Scripts/General/Weather.lua).
constexpr float LadderFogWeakNumerator = 8192.0f;
constexpr float LadderFogStrongNumerator = 16192.0f;
// Where ladder fog starts, it fades in from these distances.
constexpr float LadderFogFadeWeak = 16384.0f;
constexpr float LadderFogFadeStrong = 32768.0f;
// A fog day starts at 3 am (as an outdoor map's daily fog) and the new day's fog blends in over the hour after.
constexpr double FogDayStartMinutes = 180.0;
constexpr float FogBlendMinutes = 60.0f;
// A clear day's fog for blending into and out of a fog level: out of sight.
constexpr float ClearFogNear = 65536.0f;
constexpr float ClearFogFar = 131072.0f;

// splitmix64: identical on every platform, unlike std:: distributions.
class WeatherRandom
{
public:
    explicit WeatherRandom(uint64_t seed)
        : m_state(seed)
    {
    }

    uint64_t next()
    {
        uint64_t value = (m_state += 0x9e3779b97f4a7c15ull);
        value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ull;
        value = (value ^ (value >> 27)) * 0x94d049bb133111ebull;
        return value ^ (value >> 31);
    }

    float unit()
    {
        return static_cast<float>(next() >> 40) / static_cast<float>(1ull << 24);
    }

    float range(float minimum, float maximum)
    {
        return minimum + (maximum - minimum) * unit();
    }

private:
    uint64_t m_state;
};

float smoothStep(float edge0, float edge1, float value)
{
    if (edge1 <= edge0)
    {
        return value >= edge1 ? 1.0f : 0.0f;
    }

    const float t = std::clamp((value - edge0) / (edge1 - edge0), 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
}

int ladderIndex(float fraction, int stateCount)
{
    return static_cast<int>(std::lround(fraction * static_cast<float>(std::max(stateCount - 1, 1))));
}

float spellIntensity(const WeatherDayPlan &plan, float minute, float variationAmount)
{
    if (plan.kind == PrecipitationKind::None)
    {
        return 0.0f;
    }

    const float t = minute - plan.startMinute;

    if (t <= 0.0f || t >= plan.durationMinutes)
    {
        return 0.0f;
    }

    const float envelope = smoothStep(0.0f, plan.rampUpMinutes, t)
        * (1.0f - smoothStep(plan.durationMinutes - plan.rampDownMinutes, plan.durationMinutes, t));
    const float variation = 1.0f + variationAmount
        * std::sin(TwoPi * t / std::max(plan.variationPeriodMinutes, 1.0f) + plan.variationPhase);
    return std::clamp(plan.peak * envelope * variation, 0.0f, 1.0f);
}

float spellCloudCover(const WeatherDayPlan &plan, float minute, float leadMinutes, float lingerMinutes)
{
    if (plan.kind == PrecipitationKind::None)
    {
        return 0.0f;
    }

    const float end = plan.startMinute + plan.durationMinutes;
    const float gathered = smoothStep(plan.startMinute - leadMinutes, plan.startMinute, minute)
        * (1.0f - smoothStep(end, end + lingerMinutes, minute));
    return gathered * (0.6f + 0.4f * plan.peak);
}

class RulesParser
{
public:
    explicit RulesParser(std::string &errorMessage)
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

    template <size_t Count>
    bool readFloats(const YAML::Node &node, std::array<float, Count> &values, float minimum, float maximum,
        const std::string &where)
    {
        if (!node.IsSequence() || node.size() != Count)
        {
            return fail(where + " must be a list of " + std::to_string(Count) + " numbers");
        }

        for (size_t index = 0; index < Count; ++index)
        {
            if (!readFloat(node[index], values[index], minimum, maximum, where + "[" + std::to_string(index) + "]"))
            {
                return false;
            }
        }

        return true;
    }

    template <size_t Count>
    bool readOptionalFloats(const YAML::Node &parent, const char *pKey, std::array<float, Count> &values,
        float minimum, float maximum, const std::string &where)
    {
        const YAML::Node node = parent[pKey];
        return !node || readFloats(node, values, minimum, maximum, where + "." + pKey);
    }

    bool readRange(const YAML::Node &parent, const char *pKey, std::array<float, 2> &values, float minimum,
        float maximum, const std::string &where)
    {
        if (!readOptionalFloats(parent, pKey, values, minimum, maximum, where))
        {
            return false;
        }

        return values[0] <= values[1] || fail(where + "." + pKey + " must be [minimum, maximum]");
    }

    bool readShape(const YAML::Node &parent, const char *pKey, WeatherSpellShape &shape)
    {
        const YAML::Node node = parent[pKey];

        if (!node)
        {
            return true;
        }

        const std::string where = pKey;
        std::array<float, 2> length = {shape.minMinutes, shape.maxMinutes};

        if (!checkKeys(node, {"min_minutes", "max_minutes", "ramp_up", "ramp_down"}, where)
            || !readOptionalFloat(node, "min_minutes", length[0], 10.0f, 1380.0f, where)
            || !readOptionalFloat(node, "max_minutes", length[1], 10.0f, 1380.0f, where)
            || !readRange(node, "ramp_up", shape.rampUpMinutes, 1.0f, 600.0f, where)
            || !readRange(node, "ramp_down", shape.rampDownMinutes, 1.0f, 600.0f, where))
        {
            return false;
        }

        if (length[0] > length[1])
        {
            return fail(where + ".min_minutes must not exceed max_minutes");
        }

        shape.minMinutes = length[0];
        shape.maxMinutes = length[1];
        return true;
    }

    bool readFlakes(const YAML::Node &parent, const char *pKey, WeatherFlakeLook &look)
    {
        const YAML::Node node = parent[pKey];

        if (!node)
        {
            return true;
        }

        const std::string where = std::string("flakes.") + pKey;

        if (!checkKeys(node, {"color", "fall_speed", "size", "alpha", "sway", "sway_rate", "haze"}, where)
            || !readOptionalFloats(node, "color", look.color, 0.0f, 4.0f, where)
            || !readOptionalFloat(node, "fall_speed", look.fallSpeed, 1.0f, 2000.0f, where)
            || !readOptionalFloats(node, "size", look.size, 0.1f, 100.0f, where)
            || !readOptionalFloats(node, "alpha", look.alpha, 0.0f, 1.0f, where)
            || !readOptionalFloat(node, "sway", look.sway, 0.0f, 500.0f, where)
            || !readOptionalFloat(node, "sway_rate", look.swayRate, 0.0f, 20.0f, where))
        {
            return false;
        }

        if (const YAML::Node haze = node["haze"]; haze && haze.IsScalar() && haze.as<std::string>() == "none")
        {
            look.haze = {0.0f, 0.0f};
            return true;
        }

        return readRange(node, "haze", look.haze, 0.0f, 65536.0f, where);
    }

private:
    std::string &m_errorMessage;
};
}

bool WeatherRules::loadFromYaml(const std::string &yamlText, std::string &errorMessage)
{
    errorMessage.clear();
    RulesParser parser(errorMessage);
    WeatherRules rules;

    try
    {
        const YAML::Node root = YAML::Load(yamlText);

        if (!parser.checkKeys(root, {"version", "chances", "month_multipliers", "maps", "intensities", "rain",
                "snow", "cloud_lead", "cloud_linger", "variation", "event_intensity", "storm_threshold",
                "strike_interval_seconds", "wet_minutes", "dry_minutes", "wind", "fade_seconds", "sounds", "ash",
                "flakes", "open_sky_fog"}, "weather"))
        {
            return false;
        }

        if (!root["version"] || root["version"].as<int>() != 1)
        {
            return parser.fail("weather.version must be 1");
        }

        if (const YAML::Node chances = root["chances"]; chances)
        {
            if (!parser.checkKeys(chances, {"rain", "snow"}, "chances")
                || !parser.readOptionalFloat(chances, "rain", rules.rainChancePercent, 0.0f, 100.0f, "chances")
                || !parser.readOptionalFloat(chances, "snow", rules.snowChancePercent, 0.0f, 100.0f, "chances"))
            {
                return false;
            }
        }

        if (const YAML::Node months = root["month_multipliers"]; months)
        {
            if (!parser.checkKeys(months, {"rain", "snow"}, "month_multipliers")
                || !parser.readOptionalFloats(months, "rain", rules.rainMonthMultipliers, 0.0f, 10.0f,
                    "month_multipliers")
                || !parser.readOptionalFloats(months, "snow", rules.snowMonthMultipliers, 0.0f, 10.0f,
                    "month_multipliers"))
            {
                return false;
            }
        }

        if (const YAML::Node maps = root["maps"]; maps)
        {
            if (!maps.IsMap())
            {
                return parser.fail("maps must be a map");
            }

            for (const auto &entry : maps)
            {
                const std::string mapName = toLowerCopy(entry.first.as<std::string>());
                const std::string where = "maps." + mapName;
                WeatherMapChances chances;
                float value = 0.0f;

                if (!parser.checkKeys(entry.second,
                        {"rain", "snow", "ash", "ash_look", "dry_lightning", "rain_color", "always", "peak", "fog"},
                        where))
                {
                    return false;
                }

                if (entry.second["always"])
                {
                    const std::string kind = toLowerCopy(entry.second["always"].as<std::string>());

                    if (kind != "rain" && kind != "snow")
                    {
                        return parser.fail(where + ".always must be rain or snow");
                    }

                    chances.always = kind == "rain" ? PrecipitationKind::Rain : PrecipitationKind::Snow;
                }

                if (entry.second["peak"])
                {
                    if (!parser.readFloat(entry.second["peak"], value, 0.05f, 1.0f, where + ".peak"))
                    {
                        return false;
                    }

                    chances.alwaysPeak = value;
                }

                if (entry.second["ash_look"])
                {
                    chances.ashLook = entry.second["ash_look"].as<std::string>();
                }

                if (entry.second["dry_lightning"])
                {
                    if (!parser.readFloat(entry.second["dry_lightning"], value, 0.0f, 100.0f, where + ".dry_lightning"))
                    {
                        return false;
                    }

                    chances.dryLightningPercent = value;
                }

                if (entry.second["rain_color"])
                {
                    std::array<float, 3> color = DefaultRainColor;

                    if (!parser.readOptionalFloats(entry.second, "rain_color", color, 0.0f, 4.0f, where))
                    {
                        return false;
                    }

                    chances.rainColor = color;
                }

                if (entry.second["rain"])
                {
                    if (!parser.readFloat(entry.second["rain"], value, 0.0f, 100.0f, where + ".rain"))
                    {
                        return false;
                    }

                    chances.rainPercent = value;
                }

                if (entry.second["snow"])
                {
                    if (!parser.readFloat(entry.second["snow"], value, 0.0f, 100.0f, where + ".snow"))
                    {
                        return false;
                    }

                    chances.snowPercent = value;
                }

                if (entry.second["ash"])
                {
                    if (!parser.readFloat(entry.second["ash"], value, 0.0f, 100.0f, where + ".ash"))
                    {
                        return false;
                    }

                    chances.ashPercent = value;
                }

                if (entry.second["fog"])
                {
                    std::array<float, 3> fog = {};

                    if (!parser.readFloats(entry.second["fog"], fog, 0.0f, 100.0f, where + ".fog"))
                    {
                        return false;
                    }

                    if (fog[0] + fog[1] + fog[2] > 100.0f)
                    {
                        return parser.fail(where + ".fog chances add up to more than 100");
                    }

                    chances.fogPercent = fog;
                }

                rules.maps[mapName] = chances;
            }
        }

        if (const YAML::Node fog = root["open_sky_fog"]; fog)
        {
            if (!parser.checkKeys(fog, {"small", "average", "dense"}, "open_sky_fog")
                || !parser.readRange(fog, "small", rules.openSkyFog[0], 0.0f, 100000.0f, "open_sky_fog")
                || !parser.readRange(fog, "average", rules.openSkyFog[1], 0.0f, 100000.0f, "open_sky_fog")
                || !parser.readRange(fog, "dense", rules.openSkyFog[2], 0.0f, 100000.0f, "open_sky_fog"))
            {
                return false;
            }
        }

        if (const YAML::Node intensities = root["intensities"]; intensities)
        {
            if (!intensities.IsSequence() || intensities.size() == 0)
            {
                return parser.fail("intensities must be a non-empty list");
            }

            rules.intensities.clear();

            for (size_t index = 0; index < intensities.size(); ++index)
            {
                const YAML::Node node = intensities[index];
                const std::string where = "intensities[" + std::to_string(index) + "]";
                WeatherIntensityLevel level;

                if (!parser.checkKeys(node, {"name", "value", "weight"}, where)
                    || !node["name"] || !node["value"]
                    || !parser.readFloat(node["value"], level.value, 0.01f, 1.0f, where + ".value")
                    || !parser.readOptionalFloat(node, "weight", level.weight, 0.0f, 1000.0f, where))
                {
                    return parser.fail(where + " needs a name and a value within [0.01, 1]");
                }

                level.name = toLowerCopy(node["name"].as<std::string>());
                rules.intensities.push_back(std::move(level));
            }
        }

        if (!parser.readShape(root, "rain", rules.rain)
            || !parser.readShape(root, "snow", rules.snow)
            || !parser.readShape(root, "ash", rules.ash)
            || !parser.readOptionalFloat(root, "cloud_lead", rules.cloudLeadMinutes, 0.0f, 600.0f, "weather")
            || !parser.readOptionalFloat(root, "cloud_linger", rules.cloudLingerMinutes, 0.0f, 600.0f, "weather")
            || !parser.readOptionalFloat(root, "event_intensity", rules.eventIntensity, 0.0f, 1.0f, "weather")
            || !parser.readOptionalFloat(root, "storm_threshold", rules.stormThreshold, 0.05f, 1.01f, "weather")
            || !parser.readRange(root, "strike_interval_seconds", rules.strikeIntervalSeconds, 0.5f, 600.0f,
                "weather")
            || !parser.readOptionalFloat(root, "wet_minutes", rules.wetMinutes, 1.0f, 1440.0f, "weather")
            || !parser.readOptionalFloat(root, "dry_minutes", rules.dryMinutes, 1.0f, 1440.0f, "weather")
            || !parser.readOptionalFloat(root, "fade_seconds", rules.fadeSeconds, 0.0f, 600.0f, "weather"))
        {
            return false;
        }

        if (const YAML::Node variation = root["variation"]; variation)
        {
            if (!parser.checkKeys(variation, {"amount", "period_minutes"}, "variation")
                || !parser.readOptionalFloat(variation, "amount", rules.variationAmount, 0.0f, 1.0f, "variation")
                || !parser.readRange(variation, "period_minutes", rules.variationPeriodMinutes, 1.0f, 1440.0f,
                    "variation"))
            {
                return false;
            }
        }

        if (const YAML::Node flakes = root["flakes"]; flakes)
        {
            if (!flakes.IsMap() || !parser.readFlakes(flakes, "snow", rules.snowFlakes)
                || !parser.readFlakes(flakes, "ash", rules.ashFlakes))
            {
                return flakes.IsMap() ? false : parser.fail("flakes must be a map");
            }

            // Any other key is a named look (ember) built on the ash look.
            for (const auto &entry : flakes)
            {
                const std::string name = entry.first.as<std::string>();

                if (name == "snow" || name == "ash")
                {
                    continue;
                }

                WeatherFlakeLook look = rules.ashFlakes;

                if (!parser.readFlakes(flakes, name.c_str(), look))
                {
                    return false;
                }

                rules.namedFlakes[toLowerCopy(name)] = look;
            }
        }

        if (const YAML::Node sounds = root["sounds"]; sounds)
        {
            const std::array<std::pair<const char *, WeatherSound *>, 6> entries = {{
                {"rain_light", &rules.sounds.rainLight}, {"rain_heavy", &rules.sounds.rainHeavy},
                {"wind", &rules.sounds.wind}, {"thunder_near", &rules.sounds.thunderNear},
                {"thunder_middle", &rules.sounds.thunderMiddle}, {"thunder_far", &rules.sounds.thunderFar}}};

            if (!parser.checkKeys(sounds, {"rain_light", "rain_heavy", "wind", "thunder_near", "thunder_middle",
                    "thunder_far"}, "sounds"))
            {
                return false;
            }

            for (const auto &[pKey, pSound] : entries)
            {
                const YAML::Node node = sounds[pKey];
                const std::string where = std::string("sounds.") + pKey;

                if (!node)
                {
                    continue;
                }

                if (!parser.checkKeys(node, {"files", "volume"}, where)
                    || !parser.readOptionalFloat(node, "volume", pSound->volume, 0.0f, 4.0f, where))
                {
                    return false;
                }

                const YAML::Node files = node["files"];

                if (!files || !files.IsSequence() || files.size() == 0)
                {
                    return parser.fail(where + ".files must be a non-empty list of asset paths");
                }

                for (const YAML::Node &file : files)
                {
                    if (!file.IsScalar())
                    {
                        return parser.fail(where + ".files must hold asset paths");
                    }

                    pSound->files.push_back(file.as<std::string>());
                }
            }
        }

        if (const YAML::Node wind = root["wind"]; wind)
        {
            if (!parser.checkKeys(wind, {"calm", "rain", "snow", "ash", "gust_range"}, "wind")
                || !parser.readRange(wind, "calm", rules.calmWind, 0.0f, 2000.0f, "wind")
                || !parser.readOptionalFloat(wind, "rain", rules.rainWind, 0.0f, 2000.0f, "wind")
                || !parser.readOptionalFloat(wind, "snow", rules.snowWind, 0.0f, 2000.0f, "wind")
                || !parser.readOptionalFloat(wind, "ash", rules.ashWind, 0.0f, 2000.0f, "wind")
                || !parser.readRange(wind, "gust_range", rules.gustRange, 0.0f, 4.0f, "wind"))
            {
                return false;
            }
        }
    }
    catch (const std::exception &exception)
    {
        return parser.fail(std::string("weather: ") + exception.what());
    }

    for (const auto &[mapName, chances] : rules.maps)
    {
        if (chances.ashLook && *chances.ashLook != "ash" && !rules.namedFlakes.contains(toLowerCopy(*chances.ashLook)))
        {
            return parser.fail("maps." + mapName + ".ash_look names no flakes entry: " + *chances.ashLook);
        }
    }

    *this = std::move(rules);
    return true;
}

std::optional<float> WeatherRules::namedIntensity(const std::string &name) const
{
    const std::string lowered = toLowerCopy(name);

    for (const WeatherIntensityLevel &level : intensities)
    {
        if (level.name == lowered)
        {
            return level.value;
        }
    }

    return std::nullopt;
}

WeatherMapSettings resolveWeatherMapSettings(const WeatherRules &rules, uint32_t mapId,
    const std::string &mapFileName, bool rainEnabled, bool snowEnabled)
{
    WeatherMapSettings settings;
    settings.mapId = mapId;
    settings.rainEnabled = rainEnabled;
    settings.snowEnabled = snowEnabled;
    settings.rainChancePercent = rules.rainChancePercent;
    settings.snowChancePercent = rules.snowChancePercent;

    if (const auto it = rules.maps.find(toLowerCopy(mapFileName)); it != rules.maps.end())
    {
        settings.rainChancePercent = it->second.rainPercent.value_or(settings.rainChancePercent);
        settings.snowChancePercent = it->second.snowPercent.value_or(settings.snowChancePercent);
        settings.ashChancePercent = it->second.ashPercent.value_or(0.0f);
        settings.ashEnabled = settings.ashChancePercent > 0.0f;
        settings.dryLightningPercent = it->second.dryLightningPercent.value_or(0.0f);
        settings.rainColor = it->second.rainColor.value_or(DefaultRainColor);
        settings.fogChancePercent = it->second.fogPercent.value_or(std::array<float, 3>{});

        // Only a kind the map can have (the scene's or bolster row's rain and snow).
        if ((it->second.always == PrecipitationKind::Rain && rainEnabled)
            || (it->second.always == PrecipitationKind::Snow && snowEnabled))
        {
            settings.always = it->second.always;
            settings.alwaysPeak = it->second.alwaysPeak;
        }

        if (it->second.ashLook)
        {
            if (const auto look = rules.namedFlakes.find(toLowerCopy(*it->second.ashLook)); look != rules.namedFlakes.end())
            {
                settings.ashLook = look->second;
            }
        }
    }

    return settings;
}

int weatherDayIndex(double gameMinutes)
{
    return static_cast<int>(std::floor(std::max(gameMinutes, 0.0) / MinutesPerDay));
}

int weatherMonthForDay(int dayIndex)
{
    return 1 + (std::max(dayIndex, 0) / DaysPerMonth) % 12;
}

WeatherDayPlan planWeatherDay(const WeatherRules &rules, const WeatherMapSettings &settings, int dayIndex)
{
    const uint64_t seed = 0x5752454154484552ull
        ^ (static_cast<uint64_t>(settings.mapId) * 0x9e3779b97f4a7c15ull)
        ^ (static_cast<uint64_t>(static_cast<uint32_t>(std::max(dayIndex, 0))) * 0xc2b2ae3d27d4eb4full);
    WeatherRandom random(seed);
    WeatherDayPlan plan;
    plan.windDirectionRadians = random.range(0.0f, TwoPi);
    plan.calmWindSpeed = random.range(rules.calmWind[0], rules.calmWind[1]);

    // Every roll is drawn even when unused, so changing one chance never reshuffles the other rolls.
    const float snowRoll = random.unit() * 100.0f;
    const float rainRoll = random.unit() * 100.0f;
    const float intensityRoll = random.unit();
    const float startRoll = random.unit();
    const float lengthRoll = random.unit();
    const float rampUpRoll = random.unit();
    const float rampDownRoll = random.unit();
    const float periodRoll = random.unit();
    const float phaseRoll = random.unit();
    // Drawn after every older roll, so maps without ash roll exactly the weather they always did.
    const float ashRoll = random.unit() * 100.0f;
    const float dryLightningRoll = random.unit() * 100.0f;
    plan.dryLightning = dryLightningRoll < settings.dryLightningPercent;
    const size_t monthIndex = static_cast<size_t>(weatherMonthForDay(dayIndex) - 1);
    const float snowChance = settings.snowEnabled
        ? settings.snowChancePercent * rules.snowMonthMultipliers[monthIndex] : 0.0f;
    const float rainChance = settings.rainEnabled
        ? settings.rainChancePercent * rules.rainMonthMultipliers[monthIndex] : 0.0f;

    if (settings.always != PrecipitationKind::None)
    {
        // A spell from each midnight past the next day's ramp up: the days overlap, so it never stops.
        const WeatherSpellShape &shape = settings.always == PrecipitationKind::Snow ? rules.snow : rules.rain;
        plan.kind = settings.always;
        plan.peak = settings.alwaysPeak;
        plan.startMinute = 0.0f;
        plan.rampUpMinutes = shape.rampUpMinutes[0];
        plan.rampDownMinutes = shape.rampDownMinutes[0];
        plan.durationMinutes = static_cast<float>(MinutesPerDay) + 2.0f * (plan.rampUpMinutes + plan.rampDownMinutes);
        plan.variationPeriodMinutes = rules.variationPeriodMinutes[0]
            + (rules.variationPeriodMinutes[1] - rules.variationPeriodMinutes[0]) * periodRoll;
        plan.variationPhase = phaseRoll * TwoPi;
        return plan;
    }

    if (snowRoll < snowChance)
    {
        plan.kind = PrecipitationKind::Snow;
    }
    else if (rainRoll < rainChance)
    {
        plan.kind = PrecipitationKind::Rain;
    }
    else if (settings.ashEnabled && ashRoll < settings.ashChancePercent)
    {
        // Ash is not seasonal: no month multiplier.
        plan.kind = PrecipitationKind::Ash;
    }
    else
    {
        return plan;
    }

    float totalWeight = 0.0f;

    for (const WeatherIntensityLevel &level : rules.intensities)
    {
        totalWeight += std::max(level.weight, 0.0f);
    }

    plan.peak = rules.intensities.empty() ? 0.5f : rules.intensities.back().value;
    float cursor = intensityRoll * totalWeight;

    for (const WeatherIntensityLevel &level : rules.intensities)
    {
        cursor -= std::max(level.weight, 0.0f);

        if (cursor < 0.0f)
        {
            plan.peak = level.value;
            break;
        }
    }

    const WeatherSpellShape &shape = plan.kind == PrecipitationKind::Snow ? rules.snow
        : plan.kind == PrecipitationKind::Ash ? rules.ash : rules.rain;
    plan.startMinute = startRoll * static_cast<float>(MinutesPerDay);
    plan.durationMinutes = shape.minMinutes + (shape.maxMinutes - shape.minMinutes) * lengthRoll;
    plan.rampUpMinutes = shape.rampUpMinutes[0] + (shape.rampUpMinutes[1] - shape.rampUpMinutes[0]) * rampUpRoll;
    plan.rampDownMinutes =
        shape.rampDownMinutes[0] + (shape.rampDownMinutes[1] - shape.rampDownMinutes[0]) * rampDownRoll;
    const float rampScale = std::min(1.0f, plan.durationMinutes / (plan.rampUpMinutes + plan.rampDownMinutes));
    plan.rampUpMinutes *= rampScale;
    plan.rampDownMinutes *= rampScale;
    plan.variationPeriodMinutes = rules.variationPeriodMinutes[0]
        + (rules.variationPeriodMinutes[1] - rules.variationPeriodMinutes[0]) * periodRoll;
    plan.variationPhase = phaseRoll * TwoPi;
    return plan;
}

WeatherSample sampleRolledWeather(const WeatherRules &rules, const WeatherMapSettings &settings, double gameMinutes)
{
    const double minutes = std::max(gameMinutes, 0.0);
    const int day = weatherDayIndex(minutes);
    const float minuteOfDay = static_cast<float>(minutes - static_cast<double>(day) * MinutesPerDay);
    WeatherSample sample;
    WeatherDayPlan previousDay;
    WeatherDayPlan currentDay;

    // A spell starts on its own day but may run past midnight; the next day's clouds may gather before midnight.
    for (int offset = -1; offset <= 1; ++offset)
    {
        if (day + offset < 0)
        {
            continue;
        }

        const WeatherDayPlan plan = planWeatherDay(rules, settings, day + offset);
        const float minute = minuteOfDay - static_cast<float>(offset) * static_cast<float>(MinutesPerDay);
        const float intensity = spellIntensity(plan, minute, rules.variationAmount);

        if (intensity > sample.intensity)
        {
            sample.intensity = intensity;
            sample.precipitation = plan.kind;
        }

        sample.cloudCover = std::max(sample.cloudCover,
            spellCloudCover(plan, minute, rules.cloudLeadMinutes, rules.cloudLingerMinutes));

        if (offset == -1)
        {
            previousDay = plan;
        }
        else if (offset == 0)
        {
            currentDay = plan;
        }
    }

    if (day == 0)
    {
        previousDay = currentDay;
    }

    const float dayBlend = smoothStep(0.0f, WindBlendMinutes, minuteOfDay);
    const float calmX = std::cos(previousDay.windDirectionRadians) * previousDay.calmWindSpeed * (1.0f - dayBlend)
        + std::cos(currentDay.windDirectionRadians) * currentDay.calmWindSpeed * dayBlend;
    const float calmY = std::sin(previousDay.windDirectionRadians) * previousDay.calmWindSpeed * (1.0f - dayBlend)
        + std::sin(currentDay.windDirectionRadians) * currentDay.calmWindSpeed * dayBlend;
    const float calmSpeed = std::sqrt(calmX * calmX + calmY * calmY);
    const float extraSpeed = sample.precipitation == PrecipitationKind::Snow ? rules.snowWind * sample.intensity
        : sample.precipitation == PrecipitationKind::Rain ? rules.rainWind * sample.intensity
        : sample.precipitation == PrecipitationKind::Ash ? rules.ashWind * sample.intensity : 0.0f;
    const float scale = calmSpeed > 0.001f ? (calmSpeed + extraSpeed) / calmSpeed : 0.0f;
    sample.windX = calmX * scale;
    sample.windY = calmY * scale;
    sample.storm = sample.precipitation == PrecipitationKind::Rain && sample.intensity >= rules.stormThreshold;

    if (sample.intensity <= 0.0f)
    {
        sample.precipitation = PrecipitationKind::None;
    }

    sample.dryLightning = currentDay.dryLightning && sample.precipitation != PrecipitationKind::Rain;
    return sample;
}

float sampleWetness(const WeatherRules &rules, const WeatherMapSettings &settings, double gameMinutes)
{
    if (!settings.rainEnabled)
    {
        return 0.0f;
    }

    // Long enough to soak from dry and dry out from soaked; older rain cannot matter.
    const double window = rules.dryMinutes + 2.0 * rules.wetMinutes + WetnessStepMinutes;
    const double end = std::max(gameMinutes, 0.0);
    double time = std::floor(std::max(end - window, 0.0) / WetnessStepMinutes) * WetnessStepMinutes;
    float wetness = 0.0f;

    while (time < end)
    {
        const double step = std::min<double>(WetnessStepMinutes, end - time);
        const WeatherSample sample = sampleRolledWeather(rules, settings, time + step);

        if (sample.precipitation == PrecipitationKind::Rain)
        {
            // Medium rain (0.5) soaks surfaces through in wet_minutes; heavier rain sooner.
            wetness += static_cast<float>(step) * sample.intensity / (0.5f * rules.wetMinutes);
        }
        else
        {
            wetness -= static_cast<float>(step) / rules.dryMinutes;
        }

        wetness = std::clamp(wetness, 0.0f, 1.0f);
        time += step;
    }

    return wetness;
}

WeatherSample sampleWeather(const WeatherRules &rules, const WeatherMapSettings &settings, double gameMinutes)
{
    WeatherSample sample = sampleRolledWeather(rules, settings, gameMinutes);
    sample.wetness = sampleWetness(rules, settings, gameMinutes);
    return sample;
}

int weatherLadderState(int dryState, int stateCount, const WeatherSample &sample, float stormThreshold)
{
    if (stateCount <= 0)
    {
        return 0;
    }

    const int overcast = ladderIndex(0.5f, stateCount);
    const int rain = ladderIndex(0.67f, stateCount);
    const int storm = ladderIndex(0.83f, stateCount);
    // Dry days stop at overcast: the ladder's rain and storm skies belong to actual rain.
    int state = std::clamp(dryState, 0, overcast);

    if (sample.cloudCover >= 0.6f)
    {
        state = std::max(state, overcast);
    }
    else if (sample.cloudCover >= 0.3f)
    {
        state = std::max(state, overcast - 1);
    }

    // Ash darkens the sky only through its clouds; the ladder's rain skies belong to rain and snow.
    const bool wet = sample.precipitation == PrecipitationKind::Rain || sample.precipitation == PrecipitationKind::Snow;

    if (wet && sample.intensity >= LadderRainIntensity)
    {
        state = std::max(state, rain);
    }

    if (sample.storm || (sample.precipitation == PrecipitationKind::Rain && sample.intensity >= stormThreshold))
    {
        state = std::max(state, storm);
    }

    return std::clamp(state, 0, stateCount - 1);
}

float weatherFogLadderPosition(int dryState, int stateCount, const WeatherSample &sample, float stormThreshold)
{
    if (stateCount <= 0)
    {
        return 0.0f;
    }

    const float overcast = static_cast<float>(ladderIndex(0.5f, stateCount));
    const float storm = static_cast<float>(ladderIndex(0.83f, stateCount));
    const float dry = static_cast<float>(std::clamp(dryState, 0, static_cast<int>(overcast)));
    const bool wet = sample.precipitation == PrecipitationKind::Rain || sample.precipitation == PrecipitationKind::Snow;
    const float precipitation = wet
        ? std::clamp(sample.intensity / std::max(stormThreshold, 0.05f), 0.0f, 1.0f) : 0.0f;
    const float position = sample.cloudCover * overcast + precipitation * (storm - overcast);
    return std::max(dry, position);
}

int weatherFogDayIndex(double gameMinutes)
{
    return static_cast<int>(std::floor(std::max(gameMinutes - FogDayStartMinutes, 0.0) / MinutesPerDay));
}

WeatherFogLevel rollDailyFog(const WeatherMapSettings &settings, int fogDayIndex)
{
    const std::array<float, 3> &chances = settings.fogChancePercent;

    if (chances[0] + chances[1] + chances[2] <= 0.0f)
    {
        return WeatherFogLevel::None;
    }

    // Its own stream, so the fog never changes the rain, snow and wind a day rolls.
    const uint64_t seed = 0x464f47464f474647ull
        ^ (static_cast<uint64_t>(settings.mapId) * 0x9e3779b97f4a7c15ull)
        ^ (static_cast<uint64_t>(static_cast<uint32_t>(std::max(fogDayIndex, 0))) * 0xc2b2ae3d27d4eb4full);
    WeatherRandom random(seed);
    const float roll = random.unit() * 100.0f;

    if (roll < chances[0])
    {
        return WeatherFogLevel::Small;
    }

    if (roll < chances[0] + chances[1])
    {
        return WeatherFogLevel::Average;
    }

    return roll < chances[0] + chances[1] + chances[2] ? WeatherFogLevel::Dense : WeatherFogLevel::None;
}

WeatherOpenSkyFog sampleOpenSkyFog(const WeatherRules &rules, const WeatherMapSettings &settings, double gameMinutes,
    std::optional<WeatherFogLevel> forcedLevel)
{
    const auto distances = [&rules](WeatherFogLevel level) -> std::array<float, 2>
    {
        return level == WeatherFogLevel::None ? std::array<float, 2>{ClearFogNear, ClearFogFar}
                                              : rules.openSkyFog[static_cast<size_t>(level) - 1];
    };

    WeatherOpenSkyFog fog;
    std::array<float, 2> shown = {};

    if (forcedLevel)
    {
        shown = distances(*forcedLevel);
    }
    else
    {
        const int day = weatherFogDayIndex(gameMinutes);
        const std::array<float, 2> today = distances(rollDailyFog(settings, day));
        const float sinceStart = static_cast<float>(
            std::max(gameMinutes - FogDayStartMinutes, 0.0) - static_cast<double>(day) * MinutesPerDay);
        const float blend = day > 0 ? std::clamp(sinceStart / FogBlendMinutes, 0.0f, 1.0f) : 1.0f;
        const std::array<float, 2> before = blend < 1.0f ? distances(rollDailyFog(settings, day - 1)) : today;
        shown = {before[0] + (today[0] - before[0]) * blend, before[1] + (today[1] - before[1]) * blend};
    }

    if (shown[1] >= ClearFogFar)
    {
        return fog;
    }

    fog.foggy = true;
    fog.nearDistance = shown[0];
    fog.farDistance = std::max(shown[1], shown[0] + 1.0f);
    return fog;
}

WeatherFogDistances weatherLadderFog(float position, int stateCount)
{
    WeatherFogDistances fog;
    const float threshold = static_cast<float>(std::max(stateCount, 0) / 3);

    if (stateCount <= 0 || position <= threshold)
    {
        return fog;
    }

    const float fade = std::clamp(position - threshold, 0.0f, 1.0f);
    fog.foggy = true;
    fog.weakDistance = static_cast<int32_t>(std::lround(
        LadderFogFadeWeak + (LadderFogWeakNumerator / position - LadderFogFadeWeak) * fade));
    fog.strongDistance = static_cast<int32_t>(std::lround(
        LadderFogFadeStrong + (LadderFogStrongNumerator / position - LadderFogFadeStrong) * fade));
    return fog;
}

const WeatherFlakeLook *weatherFlakeLook(
    const WeatherRules &rules, PrecipitationKind kind, const WeatherMapSettings *pSettings)
{
    switch (kind)
    {
        case PrecipitationKind::Snow:
            return &rules.snowFlakes;
        case PrecipitationKind::Ash:
            return pSettings != nullptr && pSettings->ashLook ? &*pSettings->ashLook : &rules.ashFlakes;
        case PrecipitationKind::None:
        case PrecipitationKind::Rain:
        default:
            return nullptr;
    }
}

WeatherFogDistances weatherPrecipitationHaze(
    const WeatherRules &rules, const WeatherSample &sample, const WeatherMapSettings *pSettings)
{
    WeatherFogDistances fog;
    const WeatherFlakeLook *pLook = weatherFlakeLook(rules, sample.precipitation, pSettings);

    if (pLook == nullptr || pLook->haze[1] <= 0.0f || sample.intensity <= 0.0f)
    {
        return fog;
    }

    const float strength = std::clamp(sample.intensity, 0.0f, 1.0f);
    fog.foggy = true;
    fog.weakDistance = static_cast<int32_t>(std::lround(
        LadderFogFadeWeak + (pLook->haze[0] - LadderFogFadeWeak) * strength));
    fog.strongDistance = static_cast<int32_t>(std::lround(
        LadderFogFadeStrong + (pLook->haze[1] - LadderFogFadeStrong) * strength));
    return fog;
}
}
