#pragma once

#include <array>
#include <cstdint>
#include <random>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameAudioSystem;

// A placed ambient sound (devdocs/AMBIENT_SOUNDS.md; scene `ambient_sounds`, MM9's AmbientSound): a world sound heard
// within its outer radius, at full volume inside its inner one.
struct WorldAmbientSound
{
    uint32_t key = 0;
    std::string sound;                  // a world sound name (worlds/<world>/audio/...)
    std::array<float, 3> position = {};
    float innerRadius = 0.0f;
    float outerRadius = 0.0f;
    float volume = 1.0f;
    bool loop = true;                   // false: once each time the party comes within reach
    float waitMinSeconds = 0.0f;        // a looping sound with a wait plays once, then waits a random time between
    float waitMaxSeconds = 0.0f;
    bool dayOnly = false;               // 06:00-20:00
    bool nightOnly = false;
    bool startOn = true;                // off: never plays (MM9 starts these from triggers)
};

// Whether the sound should be heard: in its time of day and within its outer radius (a playing one keeps going to
// AmbientSoundStopMargin x that, so it does not flicker at the edge).
bool worldAmbientSoundAudible(
    const WorldAmbientSound &source,
    const std::array<float, 3> &listener,
    float gameMinutes,
    bool playing);

inline constexpr float AmbientSoundStopMargin = 1.1f;
// The listener's height over the party's feet (its ears).
inline constexpr float AmbientSoundListenerHeight = 160.0f;

// Plays a map's ambient sounds around the listener: each frame, starts those come into reach and stops those left
// behind (devdocs/AMBIENT_SOUNDS.md). A new source list (another map) stops every sound of the old one.
class WorldAmbientSoundRuntime
{
public:
    void update(
        GameAudioSystem &audio,
        const std::vector<WorldAmbientSound> *pSources,
        const std::array<float, 3> &listener,
        float gameMinutes,
        float deltaSeconds);
    void stopAll(GameAudioSystem &audio);

private:
    struct Voice
    {
        uint64_t instanceId = 0;
        bool audible = false;
        bool playedOnce = false;
        bool failed = false;            // no such sound: not tried again until it is out of reach
        float waitSeconds = 0.0f;
    };

    const std::vector<WorldAmbientSound> *m_pSources = nullptr;
    size_t m_sourceCount = 0;
    std::vector<Voice> m_voices;
    std::mt19937 m_rng{0x616d6273u};
};
}
