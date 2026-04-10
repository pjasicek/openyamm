#pragma once

#include "engine/AssetFileSystem.h"

#include <SDL3/SDL.h>

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AudioSystem
{
public:
    struct ListenerState
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
    };

    struct PlaybackOptions
    {
        float volume = 1.0f;
        bool positional = false;
        bool loop = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
    };

    AudioSystem();
    ~AudioSystem();

    AudioSystem(const AudioSystem &) = delete;
    AudioSystem &operator=(const AudioSystem &) = delete;

    bool initialize(const AssetFileSystem &assetFileSystem);
    void shutdown();

    bool preloadClip(const std::string &virtualPath);
    bool registerClip(const std::string &virtualPath, std::vector<float> samples, uint32_t frameCount = 0);
    uint64_t playClip(const std::string &virtualPath, const PlaybackOptions &options);
    void stopClip(uint64_t instanceId);
    void pauseClip(uint64_t instanceId);
    void resumeClip(uint64_t instanceId);
    void setClipVolume(uint64_t instanceId, float volume);
    bool isClipPlaying(uint64_t instanceId) const;
    void stopAll();
    void update(const ListenerState &listenerState);

private:
    struct AudioClip
    {
        std::string virtualPath;
        std::vector<float> samples;
        uint32_t frameCount = 0;
    };

    struct PlayingInstance
    {
        uint64_t instanceId = 0;
        std::shared_ptr<AudioClip> pClip;
        uint32_t frameOffset = 0;
        float volume = 1.0f;
        bool positional = false;
        bool loop = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        bool paused = false;
    };

    static constexpr int OutputSampleRate = 48000;
    static constexpr int OutputChannels = 2;
    static constexpr SDL_AudioFormat OutputFormat = SDL_AUDIO_F32LE;
    static constexpr int MixChunkFrames = 1024;
    static constexpr int TargetQueuedBytes = MixChunkFrames * OutputChannels * sizeof(float) * 3;

    std::shared_ptr<AudioClip> loadClip(const std::string &virtualPath);
    bool hasMixableInstances() const;
    void mixNextChunk(const ListenerState &listenerState);
    static void calculateStereoGains(
        const ListenerState &listenerState,
        const PlayingInstance &instance,
        float &leftGain,
        float &rightGain);

    const AssetFileSystem *m_pAssetFileSystem = nullptr;
    SDL_AudioStream *m_pAudioStream = nullptr;
    SDL_AudioSpec m_outputSpec = {};
    uint64_t m_nextInstanceId = 1;
    std::unordered_map<std::string, std::shared_ptr<AudioClip>> m_clipCache;
    std::vector<PlayingInstance> m_playingInstances;
};
}
