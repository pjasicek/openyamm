#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <random>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class GameAudioSystem;
struct EventRuntimeState;

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
    bool dayOnly = false;               // within the world's day hours (WorldAmbientSoundRules)
    bool nightOnly = false;
    bool startOn = true;                // off: silent until its map script switches it on
    // Not 0: on while the decoration of this cog is shown, as evt.SetSprite switches it (a fire's crackle); before
    // any SetSprite of it, startOn.
    uint32_t spriteCog = 0;
};

// The world's rules for its ambient sounds (world.yml ambientSounds): the day's hours and whether they pan.
struct WorldAmbientSoundRules
{
    float dayStartHour = 6.0f;
    float dayEndHour = 20.0f;
    bool pan = true;
};

// Whether the game time is day under the rules (dayStartHour inclusive, dayEndHour exclusive).
bool worldAmbientSoundDaytime(float gameMinutes, const WorldAmbientSoundRules &rules);

// Whether the sound should be heard: switched on (its map script's switch, else StartOn), in its time of day and
// within its outer radius (a playing one keeps going to AmbientSoundStopMargin x that, so it does not flicker at the
// edge).
bool worldAmbientSoundAudible(
    const WorldAmbientSound &source,
    const std::array<float, 3> &listener,
    float gameMinutes,
    bool playing,
    std::optional<bool> switchedOn = std::nullopt,
    const WorldAmbientSoundRules &rules = {});

// A map script switches a sound on or off through the named map variable AmbientSound<key> (1 on, 2 off, unset: its
// StartOn; MM9's triggers turn AmbientSounds on and off): saved with the map's variables.
std::optional<bool> worldAmbientSoundSwitch(
    const WorldAmbientSound &source,
    const std::unordered_map<std::string, int32_t> *pNamedMapVars);

// Its switch from the map's events: AmbientSound<key> first, else its decoration's evt.SetSprite (spriteCog).
std::optional<bool> worldAmbientSoundEventSwitch(const WorldAmbientSound &source, const EventRuntimeState *pEvents);

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
        float deltaSeconds,
        const EventRuntimeState *pEvents = nullptr,
        const WorldAmbientSoundRules &rules = {});
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
