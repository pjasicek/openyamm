#pragma once

#include <yaml-cpp/yaml.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
struct ModelAsset;
}

namespace OpenYAMM::Game
{
// Sounds keyed to the clips of an actor's 3D model (a world's models/actor_sounds.yml, next to its actors.yml). Might
// and Magic IX keys every creature sound to an animation of its model (devdocs/mm9_rework/MM9_MONSTER_SOUNDS.md): the
// attack grunt and weapon swish, the wince, the death scream and the body's fall, footsteps, wing flaps, idle chatter.
// An event may also shake the camera (MM9's BigEQ, SmallEQ and SmallerEQ keys: a giant's step, a dragon landing).
struct ActorClipSoundShake
{
    // Camera shake intensity (CameraShake: 1 a strong quake) at the actor, falling linearly to edgeIntensity at radius
    // (world units) and none beyond; seconds as CameraShake::start.
    float intensity = 0.0f;
    float edgeIntensity = 0.0f;
    float seconds = 0.0f;
    float radius = 0.0f;
};

struct ActorClipSoundEvent
{
    float atSeconds = 0.0f;
    // Sound names in the world's audio; one is picked at random. Empty for a footstep.
    std::vector<std::string> sounds;
    // The next of ActorClipSounds::footsteps, in turn.
    bool footstep = false;
    // The actor's voice: it replaces the actor's previous voice line.
    bool voice = false;
    // Chance of a play; after a play the event stays silent gateSeconds, after a miss missGateSeconds.
    float chance = 1.0f;
    float gateSeconds = 0.0f;
    float missGateSeconds = 0.0f;
    float volume = 1.0f;
    // Audible radii (world units); negative: the binding's radius (footstep_radius for steps), full within a quarter.
    float innerRadius = -1.0f;
    float outerRadius = -1.0f;
    // A camera shake with it (radius 0: none). An event may be a shake alone.
    ActorClipSoundShake shake;
};

struct ActorClipSounds
{
    // By clip index of the model, sorted by time.
    std::vector<std::vector<ActorClipSoundEvent>> clipEvents;
    std::vector<std::string> footsteps;
    float radius = 0.0f;
    float footstepRadius = 0.0f;
};

// Reads one actor_sounds.yml entry for its model; throws std::runtime_error naming the descriptor when a clip is not the
// model's, an event lies outside its clip or a key is unknown.
std::shared_ptr<const ActorClipSounds> parseActorClipSounds(
    const YAML::Node &entry, const Engine::ModelAsset &asset, const std::string &descriptor);

// A sound to play at the actor now (empty: none), and a camera shake (radius 0: none).
struct ActorClipSoundCue
{
    std::string sound;
    ActorClipSoundShake shake;
    bool voice = false;
    float volume = 1.0f;
    float innerRadius = 0.0f;
    float outerRadius = 0.0f;
};

// Per actor: the clip and time each track showed last frame (0 the full-body clip, 1 an upper-body layer), the
// footstep turn, the events' gates and a random state.
struct ActorClipSoundState
{
    struct Track
    {
        uint32_t clip = UINT32_MAX;
        float timeSeconds = 0.0f;
    };
    std::array<Track, 2> tracks;
    uint32_t footstepIndex = 0;
    float clockSeconds = 0.0f;
    // Clock time until which an event stays silent: keyed by its first sound (events of one sound set share it), or
    // clip << 16 | event index.
    std::unordered_map<uint32_t, float> gateUntil;
    uint32_t randomState = 1;
};

// Moves one track to (clip, timeSeconds) (UINT32_MAX: the track shows nothing) and appends the cues of the events it
// passed since last frame: from the clip's start when the clip changed or restarted, across the end when a loop
// wrapped. The caller advances state.clockSeconds once per frame before its tracks.
void advanceActorClipSounds(const ActorClipSounds &sounds, ActorClipSoundState &state, size_t track, uint32_t clip,
    float timeSeconds, float durationSeconds, float deltaSeconds, std::vector<ActorClipSoundCue> &cues);
}
