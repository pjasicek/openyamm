#include "game/render/SkyState.h"

#include "game/render/SkyClock.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
// A game-clock jump larger than this (rest, travel, debug time set) snaps instead of fading.
constexpr float SnapGameMinutes = 30.0f;
// Fog strong distance at which the sky is fully hazed; denser fog hazes more.
constexpr float FullHazeFogDistance = 12288.0f;
constexpr float MinimumFogHaze = 0.25f;
constexpr float PrecipitationHaze = 0.4f;
// Share of the original neutral fog colour in untinted fog weather; the rest keeps the preset's time-of-day colour.
constexpr float WeatherFogOriginalShare = 0.65f;
constexpr int MoonCycleDays = 28;
// Night cloud brightness without moonlight, relative to the preset's night cloud colours (which assume a bright moon).
constexpr float MoonlessCloudLight = 0.3f;

float smoothStep(float value)
{
    const float clamped = std::clamp(value, 0.0f, 1.0f);
    return clamped * clamped * (3.0f - 2.0f * clamped);
}

float lerp(float from, float to, float blend)
{
    return from + (to - from) * blend;
}

SkyColor lerpColor(const SkyColor &from, const SkyColor &to, float blend)
{
    return {lerp(from[0], to[0], blend), lerp(from[1], to[1], blend), lerp(from[2], to[2], blend)};
}

float displayToLinear(float value)
{
    return std::pow(std::clamp(value, 0.0f, 1.0f), 2.2f);
}

float linearToDisplay(float value)
{
    return std::pow(std::clamp(value, 0.0f, 1.0f), 1.0f / 2.2f);
}

float minuteOfDay(float gameMinutes)
{
    const float dayMinutes = static_cast<float>(SkyMinutesPerDay);
    return std::fmod(std::fmod(gameMinutes, dayMinutes) + dayMinutes, dayMinutes);
}

std::array<SkyColor, SkyValueCount> evaluatePreset(const SkyPreset &preset, float minute)
{
    std::array<SkyColor, SkyValueCount> values = {};

    for (size_t index = 0; index < SkyValueCount; ++index)
    {
        values[index] = evaluateSkyTrack(preset.tracks[index], minute);
    }

    return values;
}

SkyColor &valueRef(std::array<SkyColor, SkyValueCount> &values, SkyValue id)
{
    return values[static_cast<size_t>(id)];
}

std::string resolvedName(const SkyPresetLibrary &library, const std::string &name)
{
    return !name.empty() && library.find(name) != nullptr ? name : std::string();
}

void tintColor(SkyColor &color, const SkyColor &tint, float saturation)
{
    const float luminance = 0.2126f * color[0] + 0.7152f * color[1] + 0.0722f * color[2];

    for (size_t component = 0; component < 3; ++component)
    {
        color[component] = std::max(lerp(luminance, color[component], saturation), 0.0f) * tint[component];
    }
}

void tintValue(std::array<SkyColor, SkyValueCount> &values, SkyValue id, const SkyColor &tint, float saturation)
{
    tintColor(valueRef(values, id), tint, saturation);
}

void applySkyTheme(const SkyTheme &theme, SkyFrameState &frame)
{
    std::array<SkyColor, SkyValueCount> &values = frame.values;

    for (const SkyValue id : {SkyValue::Zenith, SkyValue::Horizon, SkyValue::Fog, SkyValue::WaterSky})
    {
        tintValue(values, id, theme.skyTint, theme.saturation);
    }

    tintValue(values, SkyValue::SunGlow, theme.sunTint, theme.saturation);

    for (const SkyValue id : {SkyValue::SunDisc, SkyValue::WaterSun})
    {
        tintValue(values, id, theme.sunTint, 1.0f);
    }

    for (const SkyValue id : {SkyValue::CloudLit, SkyValue::CloudShadow})
    {
        tintValue(values, id, theme.cloudTint, theme.saturation);
    }

    valueRef(values, SkyValue::Stars)[0] *= theme.starScale;
    frame.themeName = theme.name;
}
}

std::array<float, 3> skySunDirection(float gameMinutes)
{
    const float angle = (minuteOfDay(gameMinutes) - 300.0f) * Pi / 960.0f;
    return {std::cos(angle), 0.0f, std::sin(angle)};
}

std::array<float, 3> skyMoonDirection(float gameMinutes)
{
    const float angle = (minuteOfDay(gameMinutes) - 300.0f) * Pi / 960.0f + Pi;
    // A slight southern tilt keeps the moon off the sun's exact path.
    const float tilt = 0.28f;
    const float length = std::sqrt(1.0f + tilt * tilt);
    return {std::cos(angle) / length, -tilt / length, std::sin(angle) / length};
}

float skyMoonPhase(float gameMinutes)
{
    const float days = std::max(gameMinutes, 0.0f) / static_cast<float>(SkyMinutesPerDay);
    return std::fmod(days, static_cast<float>(MoonCycleDays)) / static_cast<float>(MoonCycleDays);
}

bool isPaintedSkyPreset(const SkyPreset &preset)
{
    return std::any_of(preset.clouds.begin(), preset.clouds.end(),
        [](const SkyCloudLayer &layer) { return layer.color; });
}

std::string selectSkyPreset(const SkyPresetLibrary &library, const SkyInputs &inputs)
{
    const SkySpecialPresets &specials = library.specials();

    if (inputs.underwater && !specials.underwater.empty())
    {
        return specials.underwater;
    }

    if (const std::string forced = resolvedName(library, inputs.forcedPreset); !forced.empty())
    {
        return forced;
    }

    if (inputs.redFog && !specials.redFog.empty())
    {
        return specials.redFog;
    }

    if (inputs.alwaysLight && !specials.alwaysLight.empty())
    {
        return specials.alwaysLight;
    }

    if (inputs.alwaysDark && !specials.alwaysDark.empty())
    {
        return specials.alwaysDark;
    }

    if (const SkyTheme *pTheme = selectSkyTheme(library, inputs); pTheme != nullptr && !pTheme->preset.empty())
    {
        return pTheme->preset;
    }

    // The sky texture the data resolved (a continent's weather ladder entry, a custom sky or an event override) keeps
    // its own derived look; the generic weather ladder only covers names without a preset.
    std::string selected = library.presetForSkyName(inputs.weatherSkyName);

    if (selected.empty())
    {
        selected = library.presetForWeatherState(inputs.mergedWeatherState, inputs.mergedWeatherStateCount);
    }

    if (selected.empty())
    {
        selected = library.fallback() != nullptr ? library.fallback()->name : std::string();
    }

    // Precipitation darkens a generic fair-weather sky. Storm skies and painted original skies keep their
    // own look (rain over a painted sky only adds haze, see SkyStateModel::update).
    const SkyPreset *pSelected = library.find(selected);
    const bool stormy = pSelected != nullptr && (pSelected->storm || isPaintedSkyPreset(*pSelected));

    if (inputs.snowing && !specials.snow.empty() && !stormy)
    {
        return specials.snow;
    }

    if (inputs.raining && !specials.rain.empty() && !stormy)
    {
        return specials.rain;
    }

    return selected;
}

const SkyTheme *selectSkyTheme(const SkyPresetLibrary &library, const SkyInputs &inputs)
{
    return inputs.forcedTheme ? library.findTheme(*inputs.forcedTheme) : library.themeForMap(inputs.mapFileName);
}

void SkyStateModel::setLibrary(const SkyPresetLibrary *pLibrary)
{
    m_pLibrary = pLibrary;
    m_fromPreset.clear();
    m_toPreset.clear();
    m_cloudOffsets.clear();
    m_snapPending = true;
}

void SkyStateModel::snap()
{
    m_snapPending = true;
}

const SkyFrameState &SkyStateModel::frame() const
{
    return m_frame;
}

const SkyFrameState &SkyStateModel::update(const SkyInputs &inputs, float realDeltaSeconds)
{
    if (m_pLibrary == nullptr || m_pLibrary->empty())
    {
        m_frame = {};
        m_frame.drawSky = false;
        return m_frame;
    }

    const std::string target = selectSkyPreset(*m_pLibrary, inputs);
    const bool clockJumped = std::fabs(inputs.gameMinutes - m_lastGameMinutes) > SnapGameMinutes;
    const bool forcedChanged = inputs.forcedPreset != m_lastForcedPreset;
    m_lastGameMinutes = inputs.gameMinutes;
    m_lastForcedPreset = inputs.forcedPreset;

    if (m_snapPending || clockJumped || forcedChanged || m_toPreset.empty())
    {
        m_fromPreset = target;
        m_toPreset = target;
        m_blend = 1.0f;
        m_snapPending = false;
    }
    else if (target != m_toPreset)
    {
        // Restart from whatever currently dominates so a reversal mid-fade does not pop.
        m_fromPreset = m_blend >= 0.5f ? m_toPreset : m_fromPreset;
        m_toPreset = target;
        m_blend = 0.0f;
    }

    const float transitionSeconds = m_pLibrary->transitionSeconds();
    m_blend = transitionSeconds > 0.0f
        ? std::min(1.0f, m_blend + std::max(realDeltaSeconds, 0.0f) / transitionSeconds)
        : 1.0f;

    if (m_blend >= 1.0f)
    {
        m_fromPreset = m_toPreset;
    }

    const SkyPreset *pFrom = m_pLibrary->find(m_fromPreset);
    const SkyPreset *pTo = m_pLibrary->find(m_toPreset);

    if (pFrom == nullptr || pTo == nullptr)
    {
        m_frame = {};
        m_frame.drawSky = false;
        return m_frame;
    }

    const float minute = minuteOfDay(inputs.gameMinutes);
    const float blend = smoothStep(m_blend);
    const std::array<SkyColor, SkyValueCount> fromValues = evaluatePreset(*pFrom, minute);
    const std::array<SkyColor, SkyValueCount> toValues = evaluatePreset(*pTo, minute);
    SkyFrameState frame = {};
    frame.presetName = pTo->name;

    for (size_t index = 0; index < SkyValueCount; ++index)
    {
        frame.values[index] = lerpColor(fromValues[index], toValues[index], blend);
    }

    frame.sunDiscDegrees = lerp(pFrom->sunDiscDegrees, pTo->sunDiscDegrees, blend);
    frame.moonDiscDegrees = lerp(pFrom->moonDiscDegrees, pTo->moonDiscDegrees, blend);
    const SkyPreset &dominant = blend >= 0.5f ? *pTo : *pFrom;
    frame.belowHorizon = dominant.belowHorizon;
    frame.drawSky = dominant.drawSky;
    frame.stars = dominant.stars;
    frame.stars.brightness = lerp(pFrom->stars.brightness, pTo->stars.brightness, blend);
    frame.horizonRing = dominant.horizonRing;
    frame.horizonRing.opacity = lerp(
        pFrom->horizonRing.texture == dominant.horizonRing.texture ? pFrom->horizonRing.opacity : 0.0f,
        pTo->horizonRing.texture == dominant.horizonRing.texture ? pTo->horizonRing.opacity : 0.0f,
        blend);
    frame.sunDirection = skySunDirection(inputs.gameMinutes);
    frame.moonDirection = skyMoonDirection(inputs.gameMinutes);
    frame.moonPhase = skyMoonPhase(inputs.gameMinutes);
    frame.starRotationRadians = 2.0f * Pi * minute / static_cast<float>(SkyMinutesPerDay);

    // At night clouds are lit only by the moon: dark shapes over the stars on moonless nights, grey under a bright
    // moon high in the sky.
    const float night = smoothStep((0.02f - frame.sunDirection[2]) / 0.14f);
    const float moonIllumination = 0.5f - 0.5f * std::cos(2.0f * Pi * frame.moonPhase);
    const float moonlight = std::clamp(valueRef(frame.values, SkyValue::MoonVisibility)[0], 0.0f, 1.0f)
        * smoothStep((frame.moonDirection[2] + 0.02f) / 0.25f) * moonIllumination;
    const float cloudNightLight = lerp(1.0f, lerp(MoonlessCloudLight, 1.0f, moonlight), night);

    for (const SkyValue id : {SkyValue::CloudLit, SkyValue::CloudShadow})
    {
        for (float &component : valueRef(frame.values, id))
        {
            component *= cloudNightLight;
        }
    }

    const bool foggy = inputs.foggy && inputs.fogStrongDistance > 0.0f;

    if (foggy && inputs.weatherFogDisplay && !inputs.authoredFogDisplay)
    {
        // Fog weather reads as the original grey fog rather than the painting's own colour.
        const SkyColor &original = *inputs.weatherFogDisplay;
        valueRef(frame.values, SkyValue::Fog) = lerpColor(valueRef(frame.values, SkyValue::Fog),
            {displayToLinear(original[0]), displayToLinear(original[1]), displayToLinear(original[2])},
            WeatherFogOriginalShare);
    }

    // The map theme recolours whichever preset the weather picked; underwater keeps its flat fog colour.
    const SkyTheme *pTheme = selectSkyTheme(*m_pLibrary, inputs);

    if (pTheme != nullptr && !inputs.underwater)
    {
        applySkyTheme(*pTheme, frame);
        frame.fogAmount = pTheme->haze;
    }

    // Fog weather hazes the whole sky toward the fog colour; dense fog leaves only the fog colour.
    std::array<SkyColor, SkyValueCount> &values = frame.values;

    if (foggy)
    {
        frame.fogAmount = std::max(frame.fogAmount,
            std::clamp(1.0f - inputs.fogStrongDistance / FullHazeFogDistance, MinimumFogHaze, 1.0f));
    }

    if ((inputs.raining || inputs.snowing) && isPaintedSkyPreset(*pTo))
    {
        // A painted sky keeps its picture during rain or snow, washed by haze that grows with the precipitation.
        frame.fogAmount = std::max(frame.fogAmount,
            PrecipitationHaze * std::clamp(inputs.precipitation * 2.0f, 0.0f, 1.0f));
    }

    SkyColor hazeColor = values[static_cast<size_t>(SkyValue::Fog)];

    if ((inputs.raining || inputs.snowing) && !foggy && isPaintedSkyPreset(*pTo))
    {
        // Precipitation over a painted sky hazes it toward the rain or snow fog (snow reads near-white, as the
        // original snow fog did), recoloured by the map theme.
        const std::string &precipitation = inputs.snowing ? m_pLibrary->specials().snow : m_pLibrary->specials().rain;

        if (const SkyPreset *pPrecipitation = m_pLibrary->find(precipitation); pPrecipitation != nullptr)
        {
            hazeColor = evaluateSkyTrack(pPrecipitation->tracks[static_cast<size_t>(SkyValue::Fog)], minute);

            if (pTheme != nullptr && !inputs.underwater)
            {
                tintColor(hazeColor, pTheme->skyTint, pTheme->saturation);
            }

            valueRef(values, SkyValue::Fog) = hazeColor;
        }
    }

    if (inputs.authoredFogDisplay)
    {
        const SkyColor &authored = *inputs.authoredFogDisplay;
        hazeColor = {displayToLinear(authored[0]), displayToLinear(authored[1]), displayToLinear(authored[2])};
        frame.fogFlatDisplay = authored;
        frame.skyMix = lerp(pFrom->fogTintSkyMix, pTo->fogTintSkyMix, blend);
        frame.fogAmount = std::max(frame.fogAmount, MinimumFogHaze);
    }

    if (frame.fogAmount > 0.0f)
    {
        const float haze = frame.fogAmount;
        valueRef(values, SkyValue::Zenith) = lerpColor(valueRef(values, SkyValue::Zenith), hazeColor, haze * 0.75f);
        valueRef(values, SkyValue::Horizon) = lerpColor(valueRef(values, SkyValue::Horizon), hazeColor, haze);
        valueRef(values, SkyValue::SunGlowStrength)[0] *= 1.0f - haze;
        valueRef(values, SkyValue::SunDiscVisibility)[0] *= 1.0f - haze * 0.85f;
        valueRef(values, SkyValue::Stars)[0] *= 1.0f - haze;
        valueRef(values, SkyValue::MoonVisibility)[0] *= 1.0f - haze;
        valueRef(values, SkyValue::CloudLit) = lerpColor(valueRef(values, SkyValue::CloudLit), hazeColor, haze * 0.5f);
        valueRef(values, SkyValue::CloudShadow) =
            lerpColor(valueRef(values, SkyValue::CloudShadow), hazeColor, haze * 0.5f);
    }

    if (!inputs.authoredFogDisplay)
    {
        const SkyColor &horizon = frame.value(SkyValue::Horizon);
        frame.fogFlatDisplay = {linearToDisplay(horizon[0]), linearToDisplay(horizon[1]), linearToDisplay(horizon[2])};
        frame.skyMix = 1.0f;
    }

    if (!frame.drawSky)
    {
        // No sky to match (underwater): the world keeps its flat fog colour.
        frame.skyMix = 0.0f;
    }

    m_frame = std::move(frame);
    buildCloudLayers(*pFrom, *pTo, blend, realDeltaSeconds);

    for (SkyCloudLayerState &layer : m_frame.clouds)
    {
        layer.opacity *= 1.0f - m_frame.fogAmount * 0.5f;
    }

    m_frame.lightningFlash = std::clamp(inputs.lightningFlash, 0.0f, 1.0f);
    return m_frame;
}

void SkyStateModel::buildCloudLayers(const SkyPreset &from, const SkyPreset &to, float blend, float realDeltaSeconds)
{
    const auto advance = [this, realDeltaSeconds](const std::string &key, float speed, float directionDegrees)
    {
        std::array<float, 2> &offset = m_cloudOffsets[key];
        const float radians = directionDegrees * Pi / 180.0f;
        const float delta = speed * std::max(realDeltaSeconds, 0.0f);
        // Wrap to keep float precision over long sessions; textures repeat every unit.
        offset[0] = std::fmod(offset[0] + std::cos(radians) * delta, 64.0f);
        offset[1] = std::fmod(offset[1] + std::sin(radians) * delta, 64.0f);
        return offset;
    };
    const auto makeLayer = [](const SkyCloudLayer &layer, float opacity, const std::array<float, 2> &offset)
    {
        return SkyCloudLayerState{layer.texture, layer.scale, layer.coverage, layer.softness, opacity,
            layer.curvature, offset, layer.color};
    };

    m_frame.clouds.clear();
    const size_t slotCount = std::max(from.clouds.size(), to.clouds.size());

    for (size_t slot = 0; slot < slotCount; ++slot)
    {
        const SkyCloudLayer *pFrom = slot < from.clouds.size() ? &from.clouds[slot] : nullptr;
        const SkyCloudLayer *pTo = slot < to.clouds.size() ? &to.clouds[slot] : nullptr;
        const std::string slotSuffix = "#" + std::to_string(slot);

        if (pFrom != nullptr && pTo != nullptr && pFrom->texture == pTo->texture)
        {
            const float speed = lerp(pFrom->speed, pTo->speed, blend);
            const float direction = lerp(pFrom->directionDegrees, pTo->directionDegrees, blend);
            SkyCloudLayerState layer = makeLayer(*pTo, lerp(pFrom->opacity, pTo->opacity, blend),
                advance(pTo->texture + slotSuffix, speed, direction));
            layer.scale = lerp(pFrom->scale, pTo->scale, blend);
            layer.coverage = lerp(pFrom->coverage, pTo->coverage, blend);
            layer.softness = lerp(pFrom->softness, pTo->softness, blend);
            layer.curvature = lerp(pFrom->curvature, pTo->curvature, blend);
            m_frame.clouds.push_back(std::move(layer));
            continue;
        }

        if (pFrom != nullptr && blend < 1.0f)
        {
            m_frame.clouds.push_back(makeLayer(*pFrom, pFrom->opacity * (1.0f - blend),
                advance(pFrom->texture + slotSuffix, pFrom->speed, pFrom->directionDegrees)));
        }

        if (pTo != nullptr)
        {
            m_frame.clouds.push_back(makeLayer(*pTo, pTo->opacity * blend,
                advance(pTo->texture + slotSuffix, pTo->speed, pTo->directionDegrees)));
        }
    }

    std::stable_sort(m_frame.clouds.begin(), m_frame.clouds.end(),
        [](const SkyCloudLayerState &left, const SkyCloudLayerState &right) { return left.opacity > right.opacity; });

    if (m_frame.clouds.size() > MaxSkyCloudLayers)
    {
        m_frame.clouds.resize(MaxSkyCloudLayers);
    }
}
}
