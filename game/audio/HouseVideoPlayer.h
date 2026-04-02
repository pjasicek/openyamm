#pragma once

#include "engine/AssetFileSystem.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <cstddef>
#include <cstdint>
#include <future>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class HouseVideoPlayer
{
public:
    HouseVideoPlayer();
    ~HouseVideoPlayer();

    HouseVideoPlayer(const HouseVideoPlayer &) = delete;
    HouseVideoPlayer &operator=(const HouseVideoPlayer &) = delete;

    bool initialize();
    void shutdown();
    void stop();
    bool play(const Engine::AssetFileSystem &assetFileSystem, const std::string &videoStem);
    bool preload(const Engine::AssetFileSystem &assetFileSystem, const std::string &videoStem);
    void queueBackgroundPreload(const std::string &videoStem);
    void updateBackgroundPreloads(const Engine::AssetFileSystem &assetFileSystem);
    void update(float deltaSeconds);
    bool hasActiveFrame() const;
    bgfx::TextureHandle textureHandle() const;

private:
    struct DecodedClip
    {
        std::string videoStem;
        int width = 0;
        int height = 0;
        float framesPerSecond = 0.0f;
        float durationSeconds = 0.0f;
        size_t frameCount = 0;
        size_t frameSizeBytes = 0;
        std::vector<uint8_t> videoPixels;
        int audioSampleRate = 0;
        int audioChannels = 0;
        std::vector<float> audioSamples;
    };

    struct BackgroundPreloadJob
    {
        std::string videoStem;
        std::future<std::shared_ptr<DecodedClip>> future;
    };

    bool ensureAudioStream();
    void ensureVideoTexture(int width, int height);
    void uploadVideoFrame(size_t frameIndex);
    void updateAudioQueue();
    void advancePlaybackWithoutAudio(float deltaSeconds);
    std::optional<float> playbackSecondsFromAudioQueue() const;
    void warmUpPlaybackPath();
    void finishCompletedBackgroundPreload();
    void clearBackgroundPreloads();
    std::shared_ptr<DecodedClip> getOrDecodeClip(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &videoStem);
    static std::shared_ptr<DecodedClip> decodeClip(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::string &videoStem);

    bool m_isInitialized;
    bool m_initializedAudioSubsystem;
    bgfx::TextureHandle m_videoTextureHandle;
    int m_videoTextureWidth;
    int m_videoTextureHeight;
    SDL_AudioStream *m_pAudioStream;
    std::shared_ptr<DecodedClip> m_pActiveClip;
    std::string m_activeStem;
    float m_playbackSeconds;
    size_t m_uploadedFrameIndex;
    size_t m_nextAudioSampleIndex;
    uint64_t m_totalQueuedAudioFrames;
    std::unordered_map<std::string, std::shared_ptr<DecodedClip>> m_cachedClipsByStem;
    std::vector<std::string> m_pendingBackgroundPreloadStems;
    std::optional<BackgroundPreloadJob> m_backgroundPreloadJob;
};
}
