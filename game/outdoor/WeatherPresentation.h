#pragma once

#include "game/outdoor/WeatherModel.h"

#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
enum class LightningDistance : uint8_t
{
    Near = 0,
    Middle = 1,
    Far = 2,
};

// A lightning strike for the audio side: thunder follows after the sound travel delay.
struct LightningStrike
{
    LightningDistance distance = LightningDistance::Far;
    float thunderDelaySeconds = 0.0f;
    float loudness = 1.0f;
};

// What the weather shows this frame, smoothed in real time from the game-time weather sample: precipitation fades
// in and out (rain and snow never overlap), wind gusts, and storms throw lightning.
class WeatherPresentation
{
public:
    void snap();
    void update(const WeatherRules &rules, const WeatherSample &target, float realDeltaSeconds);
    void forceStrike(LightningDistance distance);
    // Strikes since the last call, oldest first.
    std::vector<LightningStrike> takeStrikes();

    float rainLevel() const;
    float snowLevel() const;
    float cloudCover() const;
    float wetness() const;
    float windX() const;
    float windY() const;
    // 0-1 lightning brightness this frame.
    float lightningFlash() const;
    bool storm() const;

private:
    float nextRandom();
    void startStrike(LightningDistance distance);

    float m_rainLevel = 0.0f;
    float m_snowLevel = 0.0f;
    float m_cloudCover = 0.0f;
    float m_wetness = 0.0f;
    float m_baseWindX = 0.0f;
    float m_baseWindY = 0.0f;
    float m_gust = 1.0f;
    float m_gustTarget = 1.0f;
    float m_gustCountdown = 0.0f;
    float m_gustAngle = 0.0f;
    float m_gustAngleTarget = 0.0f;
    bool m_storm = false;
    bool m_snapPending = true;
    float m_strikeCountdown = 4.0f;
    float m_flashAge = -1.0f;
    float m_flashDuration = 0.3f;
    float m_flashStrength = 0.0f;
    float m_lightningFlash = 0.0f;
    uint64_t m_randomState = 0x6c696768746e696eull;
    std::vector<LightningStrike> m_strikes;
};
}
