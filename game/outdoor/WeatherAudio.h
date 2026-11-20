#pragma once

#include "game/audio/GameAudioSystem.h"
#include "game/outdoor/WeatherPresentation.h"

#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
// Weather sound for the outdoor view: light and heavy rain loops cross-faded by the shown rain, a wind loop that
// rises with strong wind, and thunder after each lightning strike once the sound has travelled.
class WeatherAudio
{
public:
    // New strikes join the thunder queue. Audibility 1 is in the open, 0 inaudible (underwater: nothing plays, but
    // loops keep their state), and between is under cover (an open-sky indoor map's houses and tunnels): the rain
    // and wind loops at that share, thunder at its square root (it carries through walls).
    void update(GameAudioSystem &audio, const WeatherSounds &sounds, const WeatherPresentation &weather,
        const std::vector<LightningStrike> &strikes, float audibility, float deltaSeconds);
    void stop(GameAudioSystem &audio);
    // Clears loop handles without touching the audio system (it was shut down or reset).
    void forget();

private:
    struct Loop
    {
        uint64_t instanceId = 0;
        float silentSeconds = 0.0f;
    };

    struct PendingThunder
    {
        LightningStrike strike;
        float remainingSeconds = 0.0f;
    };

    void updateLoop(GameAudioSystem &audio, Loop &loop, const WeatherSound &sound, float volume, float deltaSeconds);
    float nextRandom();

    Loop m_rainLight;
    Loop m_rainHeavy;
    Loop m_wind;
    std::vector<PendingThunder> m_pendingThunder;
    uint64_t m_randomState = 0x7468756e646572ull;
};
}
