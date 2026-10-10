#include "game/outdoor/WeatherPresentation.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
// Wind follows the weather's wind over a few seconds; gusts pick a new strength every few seconds.
constexpr float WindFollowSeconds = 3.0f;
constexpr float GustFollowSeconds = 1.6f;
constexpr float GustMinSeconds = 2.0f;
constexpr float GustMaxSeconds = 6.0f;
constexpr float GustMaxTurnRadians = 0.2f;
constexpr float WetnessFollowSeconds = 20.0f;
constexpr float CloudFollowSeconds = 15.0f;
// Strike distances are in metres; thunder arrives at the speed of sound.
constexpr float SpeedOfSoundMetres = 343.0f;

float approach(float value, float target, float maxStep)
{
    return value < target ? std::min(value + maxStep, target) : std::max(value - maxStep, target);
}

float follow(float value, float target, float deltaSeconds, float seconds)
{
    return value + (target - value) * (1.0f - std::exp(-deltaSeconds / std::max(seconds, 0.001f)));
}
}

void WeatherPresentation::snap()
{
    m_snapPending = true;
}

float WeatherPresentation::nextRandom()
{
    uint64_t value = (m_randomState += 0x9e3779b97f4a7c15ull);
    value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ull;
    value = (value ^ (value >> 27)) * 0x94d049bb133111ebull;
    value ^= value >> 31;
    return static_cast<float>(value >> 40) / static_cast<float>(1ull << 24);
}

void WeatherPresentation::startStrike(LightningDistance distance)
{
    float metres = 0.0f;

    switch (distance)
    {
        case LightningDistance::Near:
            metres = 250.0f + 550.0f * nextRandom();
            m_flashStrength = 1.0f;
            break;
        case LightningDistance::Middle:
            metres = 800.0f + 1700.0f * nextRandom();
            m_flashStrength = 0.65f;
            break;
        case LightningDistance::Far:
        default:
            metres = 2500.0f + 4000.0f * nextRandom();
            m_flashStrength = 0.35f;
            break;
    }

    m_flashAge = 0.0f;
    m_flashDuration = 0.15f + 0.25f * nextRandom();
    m_strikes.push_back({distance, metres / SpeedOfSoundMetres, m_flashStrength});
}

void WeatherPresentation::forceStrike(LightningDistance distance)
{
    startStrike(distance);
}

void WeatherPresentation::update(const WeatherRules &rules, const WeatherSample &target, float realDeltaSeconds)
{
    const float dt = std::max(realDeltaSeconds, 0.0f);
    const float rainTarget = target.precipitation == PrecipitationKind::Rain ? target.intensity : 0.0f;
    const float snowTarget = target.precipitation == PrecipitationKind::Snow ? target.intensity : 0.0f;

    if (m_snapPending)
    {
        m_rainLevel = rainTarget;
        m_snowLevel = snowTarget;
        m_cloudCover = target.cloudCover;
        m_wetness = target.wetness;
        m_baseWindX = target.windX;
        m_baseWindY = target.windY;
        m_gust = 1.0f;
        m_gustTarget = 1.0f;
        m_gustAngle = 0.0f;
        m_gustAngleTarget = 0.0f;
        m_snapPending = false;
    }
    else
    {
        // Rain and snow never overlap: the old kind fades out completely before the new one starts.
        const float step = rules.fadeSeconds > 0.0f ? dt / rules.fadeSeconds : 1.0f;

        if (snowTarget > 0.0f && m_rainLevel > 0.0f)
        {
            m_rainLevel = approach(m_rainLevel, 0.0f, step);
        }
        else if (rainTarget > 0.0f && m_snowLevel > 0.0f)
        {
            m_snowLevel = approach(m_snowLevel, 0.0f, step);
        }
        else
        {
            m_rainLevel = approach(m_rainLevel, rainTarget, step);
            m_snowLevel = approach(m_snowLevel, snowTarget, step);
        }

        m_cloudCover = follow(m_cloudCover, target.cloudCover, dt, CloudFollowSeconds);
        m_wetness = follow(m_wetness, target.wetness, dt, WetnessFollowSeconds);
        m_baseWindX = follow(m_baseWindX, target.windX, dt, WindFollowSeconds);
        m_baseWindY = follow(m_baseWindY, target.windY, dt, WindFollowSeconds);
    }

    m_gustCountdown -= dt;

    if (m_gustCountdown <= 0.0f)
    {
        m_gustCountdown = GustMinSeconds + (GustMaxSeconds - GustMinSeconds) * nextRandom();
        m_gustTarget = rules.gustRange[0] + (rules.gustRange[1] - rules.gustRange[0]) * nextRandom();
        m_gustAngleTarget = (nextRandom() * 2.0f - 1.0f) * GustMaxTurnRadians;
    }

    m_gust = follow(m_gust, m_gustTarget, dt, GustFollowSeconds);
    m_gustAngle = follow(m_gustAngle, m_gustAngleTarget, dt, GustFollowSeconds);

    // Storms build and fade with the shown rain, not the instant game-time target.
    m_storm = target.storm && m_rainLevel >= rules.stormThreshold * 0.9f;

    if (m_storm)
    {
        const float strength = std::clamp(
            (m_rainLevel - rules.stormThreshold) / std::max(1.0f - rules.stormThreshold, 0.05f), 0.0f, 1.0f);
        m_strikeCountdown -= dt;

        if (m_strikeCountdown <= 0.0f)
        {
            const float roll = nextRandom();
            const LightningDistance distance = roll < 0.15f + 0.15f * strength ? LightningDistance::Near
                : roll < 0.5f + 0.1f * strength ? LightningDistance::Middle : LightningDistance::Far;
            startStrike(distance);
            const float meanInterval = rules.strikeIntervalSeconds[1]
                + (rules.strikeIntervalSeconds[0] - rules.strikeIntervalSeconds[1]) * strength;
            m_strikeCountdown = meanInterval * (0.4f + 1.2f * nextRandom());
        }
    }
    else
    {
        m_strikeCountdown = std::max(m_strikeCountdown, rules.strikeIntervalSeconds[0] * 0.5f);
    }

    m_lightningFlash = 0.0f;

    if (m_flashAge >= 0.0f)
    {
        // A bright strike with a dimmer second pulse, as with most visible lightning.
        const float t = m_flashAge / std::max(m_flashDuration, 0.01f);
        const float first = std::exp(-t * 18.0f);
        const float second = t > 0.35f ? 0.6f * std::exp(-(t - 0.35f) * 14.0f) : 0.0f;
        m_lightningFlash = std::clamp((first + second) * m_flashStrength, 0.0f, 1.0f);
        m_flashAge += dt;

        if (m_flashAge >= m_flashDuration)
        {
            m_flashAge = -1.0f;
        }
    }
}

std::vector<LightningStrike> WeatherPresentation::takeStrikes()
{
    std::vector<LightningStrike> strikes;
    strikes.swap(m_strikes);
    return strikes;
}

float WeatherPresentation::rainLevel() const
{
    return m_rainLevel;
}

float WeatherPresentation::snowLevel() const
{
    return m_snowLevel;
}

float WeatherPresentation::cloudCover() const
{
    return m_cloudCover;
}

float WeatherPresentation::wetness() const
{
    return m_wetness;
}

float WeatherPresentation::windX() const
{
    const float cosine = std::cos(m_gustAngle);
    const float sine = std::sin(m_gustAngle);
    return (m_baseWindX * cosine - m_baseWindY * sine) * m_gust;
}

float WeatherPresentation::windY() const
{
    const float cosine = std::cos(m_gustAngle);
    const float sine = std::sin(m_gustAngle);
    return (m_baseWindX * sine + m_baseWindY * cosine) * m_gust;
}

float WeatherPresentation::lightningFlash() const
{
    return m_lightningFlash;
}

bool WeatherPresentation::storm() const
{
    return m_storm;
}
}
