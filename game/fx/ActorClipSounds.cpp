#include "game/fx/ActorClipSounds.h"

#include "engine/models/ModelAsset.h"

#include <algorithm>
#include <cmath>
#include <functional>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
constexpr float InnerRadiusFraction = 0.25f;

float positiveRadius(const YAML::Node &value, const std::string &descriptor, const char *pName)
{
    const float radius = value.as<float>();
    if (!std::isfinite(radius) || radius <= 0.0f)
    {
        throw std::runtime_error(std::string("actor sounds ") + pName + " must be positive: " + descriptor);
    }
    return radius;
}

uint32_t nextRandom(uint32_t &state)
{
    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    return state;
}

float randomUnit(uint32_t &state)
{
    return float(nextRandom(state) >> 8) / float(1u << 24);
}
}

std::shared_ptr<const ActorClipSounds> parseActorClipSounds(
    const YAML::Node &entry, const Engine::ModelAsset &asset, const std::string &descriptor)
{
    std::shared_ptr<ActorClipSounds> sounds = std::make_shared<ActorClipSounds>();
    sounds->clipEvents.resize(asset.clips.size());
    sounds->radius = positiveRadius(entry["radius"], descriptor, "radius");
    if (const YAML::Node footsteps = entry["footsteps"])
    {
        sounds->footsteps = footsteps.as<std::vector<std::string>>();
        sounds->footstepRadius = positiveRadius(entry["footstep_radius"], descriptor, "footstep_radius");
    }
    for (const auto &key : entry)
    {
        const std::string name = key.first.as<std::string>();
        if (name != "descriptor" && name != "radius" && name != "footsteps" && name != "footstep_radius"
            && name != "clips")
        {
            throw std::runtime_error("unknown actor sounds key: " + descriptor + " " + name);
        }
    }
    for (const auto &clipEntry : entry["clips"])
    {
        const std::string clipName = clipEntry.first.as<std::string>();
        const std::optional<uint32_t> clip = asset.findClip(clipName);
        if (!clip)
        {
            throw std::runtime_error("actor sounds clip is not the model's: " + descriptor + " " + clipName);
        }
        std::vector<ActorClipSoundEvent> &events = sounds->clipEvents[*clip];
        for (const YAML::Node &item : clipEntry.second)
        {
            for (const auto &key : item)
            {
                const std::string name = key.first.as<std::string>();
                if (name != "at" && name != "sound" && name != "sounds" && name != "footstep" && name != "voice"
                    && name != "chance" && name != "gate" && name != "miss_gate" && name != "volume"
                    && name != "radius" && name != "inner" && name != "shake")
                {
                    throw std::runtime_error("unknown actor sound event key: " + descriptor + " " + clipName + " "
                        + name);
                }
            }
            ActorClipSoundEvent event;
            event.atSeconds = item["at"].as<float>();
            if (!std::isfinite(event.atSeconds) || event.atSeconds < 0.0f
                || event.atSeconds > asset.clips[*clip].durationSeconds + 0.001f)
            {
                throw std::runtime_error("actor sound event outside its clip: " + descriptor + " " + clipName);
            }
            if (item["sound"])
            {
                event.sounds.push_back(item["sound"].as<std::string>());
            }
            if (item["sounds"])
            {
                const std::vector<std::string> names = item["sounds"].as<std::vector<std::string>>();
                event.sounds.insert(event.sounds.end(), names.begin(), names.end());
            }
            event.footstep = item["footstep"].as<bool>(false);
            if (const YAML::Node shake = item["shake"])
            {
                for (const auto &key : shake)
                {
                    const std::string name = key.first.as<std::string>();
                    if (name != "near" && name != "edge" && name != "seconds" && name != "radius")
                    {
                        throw std::runtime_error("unknown actor sound shake key: " + descriptor + " " + clipName + " "
                            + name);
                    }
                }
                event.shake.intensity = shake["near"].as<float>();
                event.shake.edgeIntensity = shake["edge"].as<float>(0.0f);
                event.shake.seconds = shake["seconds"].as<float>();
                event.shake.radius = positiveRadius(shake["radius"], descriptor, "shake radius");
                const ActorClipSoundShake &read = event.shake;
                if (!(read.intensity > 0.0f && read.intensity <= 10.0f) || !(read.edgeIntensity >= 0.0f)
                    || !(read.edgeIntensity <= read.intensity) || !(read.seconds > 0.0f))
                {
                    throw std::runtime_error("actor sound shake out of range: " + descriptor + " " + clipName);
                }
            }
            const bool shakeOnly = event.shake.radius > 0.0f && !event.footstep && event.sounds.empty();
            if ((!shakeOnly && event.footstep == !event.sounds.empty())
                || (event.footstep && sounds->footsteps.empty()))
            {
                throw std::runtime_error("actor sound event needs sounds, a footstep (with footsteps) or a shake: "
                    + descriptor + " " + clipName);
            }
            event.voice = item["voice"].as<bool>(false);
            event.chance = item["chance"].as<float>(1.0f);
            event.gateSeconds = item["gate"].as<float>(0.0f);
            event.missGateSeconds = item["miss_gate"].as<float>(0.0f);
            event.volume = item["volume"].as<float>(1.0f);
            if (item["radius"])
            {
                event.outerRadius = positiveRadius(item["radius"], descriptor, "event radius");
                event.innerRadius = item["inner"] ? positiveRadius(item["inner"], descriptor, "event inner")
                                                  : event.outerRadius * InnerRadiusFraction;
            }
            if (!(event.chance > 0.0f && event.chance <= 1.0f) || !(event.gateSeconds >= 0.0f)
                || !(event.missGateSeconds >= 0.0f) || !(event.volume > 0.0f && event.volume <= 1.0f))
            {
                throw std::runtime_error("actor sound event chance, gates or volume out of range: " + descriptor
                    + " " + clipName);
            }
            events.push_back(std::move(event));
        }
        std::stable_sort(events.begin(), events.end(),
            [](const ActorClipSoundEvent &left, const ActorClipSoundEvent &right)
            {
                return left.atSeconds < right.atSeconds;
            });
    }
    return sounds;
}

void advanceActorClipSounds(const ActorClipSounds &sounds, ActorClipSoundState &state, size_t track, uint32_t clip,
    float timeSeconds, float durationSeconds, float deltaSeconds, std::vector<ActorClipSoundCue> &cues)
{
    ActorClipSoundState::Track &previous = state.tracks[track];
    const ActorClipSoundState::Track last = previous;
    previous = {clip, timeSeconds};
    if (clip == UINT32_MAX || clip >= sounds.clipEvents.size() || sounds.clipEvents[clip].empty())
    {
        return;
    }
    const std::vector<ActorClipSoundEvent> &events = sounds.clipEvents[clip];
    // Events in (from, to]; a window starting before the clip also takes the events at its first frame.
    const auto pass = [&](float from, float to)
    {
        for (size_t index = 0; index < events.size(); ++index)
        {
            const ActorClipSoundEvent &event = events[index];
            const bool inside = (event.atSeconds > from || (from < 0.0f && event.atSeconds <= 0.0f))
                && event.atSeconds <= to;
            if (!inside)
            {
                continue;
            }
            // Events of one sound set share their gate (MM9's script waits are per script, not per key).
            const uint32_t gateKey = event.sounds.empty() ? (clip << 16) | uint32_t(index)
                                                          : uint32_t(std::hash<std::string>{}(event.sounds.front()));
            const auto gate = state.gateUntil.find(gateKey);
            if (gate != state.gateUntil.end() && state.clockSeconds < gate->second)
            {
                continue;
            }
            if (event.chance < 1.0f && randomUnit(state.randomState) >= event.chance)
            {
                if (event.missGateSeconds > 0.0f)
                {
                    state.gateUntil[gateKey] = state.clockSeconds + event.missGateSeconds;
                }
                continue;
            }
            if (event.gateSeconds > 0.0f)
            {
                state.gateUntil[gateKey] = state.clockSeconds + event.gateSeconds;
            }
            ActorClipSoundCue cue;
            cue.shake = event.shake;
            cue.voice = event.voice;
            cue.volume = event.volume;
            if (event.footstep)
            {
                cue.sound = sounds.footsteps[state.footstepIndex % sounds.footsteps.size()];
                ++state.footstepIndex;
            }
            else if (!event.sounds.empty())
            {
                cue.sound = event.sounds.size() == 1 ? event.sounds.front()
                    : event.sounds[nextRandom(state.randomState) % event.sounds.size()];
            }
            cue.outerRadius = event.outerRadius > 0.0f ? event.outerRadius
                : event.footstep ? sounds.footstepRadius : sounds.radius;
            cue.innerRadius = event.innerRadius >= 0.0f ? event.innerRadius : cue.outerRadius * InnerRadiusFraction;
            cues.push_back(std::move(cue));
        }
    };
    if (last.clip != clip)
    {
        // Entered this frame: as if the clip had played the frame's time up to here.
        pass(timeSeconds - deltaSeconds, timeSeconds);
    }
    else if (timeSeconds >= last.timeSeconds)
    {
        pass(last.timeSeconds, timeSeconds);
    }
    else
    {
        // Back in time: a loop that wrapped plays its tail first; an action that restarted does not.
        if (durationSeconds - last.timeSeconds <= 2.0f * deltaSeconds + 0.001f)
        {
            pass(last.timeSeconds, durationSeconds);
        }
        pass(-1.0f, timeSeconds);
    }
}
}
