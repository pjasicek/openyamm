#pragma once

#include "engine/AssetFileSystem.h"

#include <SDL3/SDL.h>

#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Engine
{
// Frames produced while they play (long music tracks), instead of a decoded clip held in memory: interleaved stereo
// float frames at the output rate. The mixer reads them on the main thread, so a source decodes ahead on its own
// thread and read() never waits.
class AudioStreamSource
{
public:
    virtual ~AudioStreamSource() = default;
    // Fills up to frameCount frames and returns how many it wrote; the mixer plays silence for the rest.
    virtual uint32_t read(float *pSamples, uint32_t frameCount) = 0;
    // No frame will come any more (a decoding error, or the end of a source that does not loop).
    virtual bool finished() const = 0;
};

class AudioSystem
{
public:
    struct CacheStats
    {
        size_t clipCount = 0;
        size_t sampleBytes = 0;
    };

    struct ListenerState
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float yawRadians = 0.0f;
    };

    struct PlaybackOptions
    {
        float volume = 1.0f;
        bool positional = false;
        bool attenuate = true;
        // false: a positional sound keeps its distance falloff but plays centred (MM9's ambient sounds)
        bool pan = true;
        bool loop = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float pitch = 1.0f;
        float innerRadius = -1.0f;
        float outerRadius = -1.0f;
    };

    AudioSystem();
    ~AudioSystem();

    AudioSystem(const AudioSystem &) = delete;
    AudioSystem &operator=(const AudioSystem &) = delete;

    bool initialize(const AssetFileSystem &assetFileSystem);
    void shutdown();

    bool preloadClip(const std::string &virtualPath);
    bool registerClip(const std::string &virtualPath, std::vector<float> samples, uint32_t frameCount = 0);
    bool releaseClip(const std::string &virtualPath);
    CacheStats cacheStats() const;
    uint64_t playClip(const std::string &virtualPath, const PlaybackOptions &options);
    // The source supplies the looping, so loop and pitch are ignored; the other options apply as for a clip.
    uint64_t playStream(std::shared_ptr<AudioStreamSource> pSource, const PlaybackOptions &options);
    void stopClip(uint64_t instanceId);
    void pauseClip(uint64_t instanceId);
    void resumeClip(uint64_t instanceId);
    void setClipVolume(uint64_t instanceId, float volume);
    void setClipPosition(uint64_t instanceId, float x, float y, float z);
    bool isClipPlaying(uint64_t instanceId) const;
    void clearQueuedAudio();
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
        std::shared_ptr<AudioStreamSource> pStream;
        double frameOffset = 0.0;
        float volume = 1.0f;
        bool positional = false;
        bool attenuate = true;
        bool pan = true;
        bool loop = false;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float pitch = 1.0f;
        float innerRadius = -1.0f;
        float outerRadius = -1.0f;
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
    std::unordered_set<std::string> m_playbackCacheMissWarningPaths;
    std::vector<PlayingInstance> m_playingInstances;
    std::vector<float> m_streamSamples;
};
}
