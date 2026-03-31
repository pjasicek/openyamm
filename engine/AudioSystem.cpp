#include "engine/AudioSystem.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>

namespace OpenYAMM::Engine
{
namespace
{
constexpr float GlobalSoundGain = 1.0f / 3.0f;

bool isAudioSubsystemInitialized()
{
    return (SDL_WasInit(SDL_INIT_AUDIO) & SDL_INIT_AUDIO) != 0;
}

SDL_AudioSpec buildOutputSpec()
{
    SDL_AudioSpec spec = {};
    spec.format = SDL_AUDIO_F32LE;
    spec.channels = 2;
    spec.freq = 48000;
    return spec;
}
}

AudioSystem::AudioSystem()
    : m_outputSpec(buildOutputSpec())
{
}

AudioSystem::~AudioSystem()
{
    shutdown();
}

bool AudioSystem::initialize(const AssetFileSystem &assetFileSystem)
{
    shutdown();
    m_pAssetFileSystem = &assetFileSystem;

    if (!isAudioSubsystemInitialized())
    {
        if (!SDL_InitSubSystem(SDL_INIT_AUDIO))
        {
            std::cerr << "AudioSystem: SDL_InitSubSystem(SDL_INIT_AUDIO) failed: " << SDL_GetError() << '\n';
            return false;
        }
    }

    m_pAudioStream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &m_outputSpec, nullptr, nullptr);

    if (m_pAudioStream == nullptr)
    {
        std::cerr << "AudioSystem: SDL_OpenAudioDeviceStream failed: " << SDL_GetError() << '\n';
        m_pAssetFileSystem = nullptr;
        return false;
    }

    if (!SDL_ResumeAudioStreamDevice(m_pAudioStream))
    {
        std::cerr << "AudioSystem: SDL_ResumeAudioStreamDevice failed: " << SDL_GetError() << '\n';
        SDL_DestroyAudioStream(m_pAudioStream);
        m_pAudioStream = nullptr;
        m_pAssetFileSystem = nullptr;
        return false;
    }

    return true;
}

bool AudioSystem::preloadClip(const std::string &virtualPath)
{
    const std::shared_ptr<AudioClip> pClip = loadClip(virtualPath);
    return pClip != nullptr && pClip->frameCount > 0;
}

bool AudioSystem::registerClip(const std::string &virtualPath, std::vector<float> samples, uint32_t frameCount)
{
    if (virtualPath.empty() || samples.empty())
    {
        return false;
    }

    std::shared_ptr<AudioClip> pClip = std::make_shared<AudioClip>();
    pClip->virtualPath = virtualPath;
    pClip->samples = std::move(samples);
    pClip->frameCount = frameCount != 0
        ? frameCount
        : static_cast<uint32_t>(pClip->samples.size() / OutputChannels);

    if (pClip->frameCount == 0)
    {
        return false;
    }

    m_clipCache[virtualPath] = pClip;
    return true;
}

void AudioSystem::shutdown()
{
    stopAll();
    m_clipCache.clear();

    if (m_pAudioStream != nullptr)
    {
        if (isAudioSubsystemInitialized())
        {
            SDL_DestroyAudioStream(m_pAudioStream);
        }

        m_pAudioStream = nullptr;
    }

    m_pAssetFileSystem = nullptr;
    m_nextInstanceId = 1;
}

uint64_t AudioSystem::playClip(const std::string &virtualPath, const PlaybackOptions &options)
{
    std::shared_ptr<AudioClip> pClip = loadClip(virtualPath);

    if (pClip == nullptr || pClip->frameCount == 0)
    {
        return 0;
    }

    PlayingInstance instance = {};
    instance.instanceId = m_nextInstanceId++;
    instance.pClip = std::move(pClip);
    instance.volume = std::clamp(options.volume * GlobalSoundGain, 0.0f, 2.0f);
    instance.positional = options.positional;
    instance.loop = options.loop;
    instance.x = options.x;
    instance.y = options.y;
    instance.z = options.z;
    m_playingInstances.push_back(std::move(instance));
    return m_playingInstances.back().instanceId;
}

void AudioSystem::stopClip(uint64_t instanceId)
{
    m_playingInstances.erase(
        std::remove_if(
            m_playingInstances.begin(),
            m_playingInstances.end(),
            [instanceId](const PlayingInstance &instance)
            {
                return instance.instanceId == instanceId;
            }),
        m_playingInstances.end());
}

void AudioSystem::setClipVolume(uint64_t instanceId, float volume)
{
    for (PlayingInstance &instance : m_playingInstances)
    {
        if (instance.instanceId != instanceId)
        {
            continue;
        }

        instance.volume = std::clamp(volume * GlobalSoundGain, 0.0f, 2.0f);
        return;
    }
}

bool AudioSystem::isClipPlaying(uint64_t instanceId) const
{
    return std::any_of(
        m_playingInstances.begin(),
        m_playingInstances.end(),
        [instanceId](const PlayingInstance &instance)
        {
            return instance.instanceId == instanceId;
        });
}

void AudioSystem::stopAll()
{
    m_playingInstances.clear();

    if (m_pAudioStream != nullptr && isAudioSubsystemInitialized())
    {
        SDL_ClearAudioStream(m_pAudioStream);
    }
}

void AudioSystem::update(const ListenerState &listenerState)
{
    if (m_pAudioStream == nullptr)
    {
        return;
    }

    while (SDL_GetAudioStreamQueued(m_pAudioStream) < TargetQueuedBytes)
    {
        if (m_playingInstances.empty())
        {
            break;
        }

        mixNextChunk(listenerState);
    }
}

std::shared_ptr<AudioSystem::AudioClip> AudioSystem::loadClip(const std::string &virtualPath)
{
    if (m_pAssetFileSystem == nullptr || virtualPath.empty())
    {
        return nullptr;
    }

    const std::unordered_map<std::string, std::shared_ptr<AudioClip>>::const_iterator existingClipIt =
        m_clipCache.find(virtualPath);

    if (existingClipIt != m_clipCache.end())
    {
        return existingClipIt->second;
    }

    const std::optional<std::vector<uint8_t>> clipBytes = m_pAssetFileSystem->readBinaryFile(virtualPath);

    if (!clipBytes || clipBytes->empty())
    {
        return nullptr;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(clipBytes->data(), clipBytes->size());

    if (pIoStream == nullptr)
    {
        std::cerr << "AudioSystem: SDL_IOFromConstMem failed for " << virtualPath << ": " << SDL_GetError() << '\n';
        return nullptr;
    }

    SDL_AudioSpec clipSpec = {};
    Uint8 *pClipData = nullptr;
    Uint32 clipDataLength = 0;

    if (!SDL_LoadWAV_IO(pIoStream, true, &clipSpec, &pClipData, &clipDataLength))
    {
        std::cerr << "AudioSystem: SDL_LoadWAV_IO failed for " << virtualPath << ": " << SDL_GetError() << '\n';
        return nullptr;
    }

    SDL_AudioStream *pConversionStream = SDL_CreateAudioStream(&clipSpec, &m_outputSpec);

    if (pConversionStream == nullptr)
    {
        std::cerr << "AudioSystem: SDL_CreateAudioStream failed for " << virtualPath << ": " << SDL_GetError() << '\n';
        SDL_free(pClipData);
        return nullptr;
    }

    if (!SDL_PutAudioStreamData(pConversionStream, pClipData, static_cast<int>(clipDataLength))
        || !SDL_FlushAudioStream(pConversionStream))
    {
        std::cerr << "AudioSystem: audio conversion queue failed for " << virtualPath << ": " << SDL_GetError()
                  << '\n';
        SDL_DestroyAudioStream(pConversionStream);
        SDL_free(pClipData);
        return nullptr;
    }

    const int convertedBytes = SDL_GetAudioStreamAvailable(pConversionStream);

    if (convertedBytes <= 0)
    {
        SDL_DestroyAudioStream(pConversionStream);
        SDL_free(pClipData);
        return nullptr;
    }

    std::vector<float> convertedSamples(static_cast<size_t>(convertedBytes) / sizeof(float));
    const int bytesRead = SDL_GetAudioStreamData(pConversionStream, convertedSamples.data(), convertedBytes);
    SDL_DestroyAudioStream(pConversionStream);
    SDL_free(pClipData);

    if (bytesRead != convertedBytes)
    {
        std::cerr << "AudioSystem: SDL_GetAudioStreamData failed for " << virtualPath << ": " << SDL_GetError()
                  << '\n';
        return nullptr;
    }

    std::shared_ptr<AudioClip> pClip = std::make_shared<AudioClip>();
    pClip->virtualPath = virtualPath;
    pClip->samples = std::move(convertedSamples);
    pClip->frameCount = static_cast<uint32_t>(pClip->samples.size() / OutputChannels);
    m_clipCache[virtualPath] = pClip;
    return pClip;
}

void AudioSystem::mixNextChunk(const ListenerState &listenerState)
{
    std::vector<float> mixedSamples(static_cast<size_t>(MixChunkFrames * OutputChannels), 0.0f);

    for (PlayingInstance &instance : m_playingInstances)
    {
        if (instance.pClip == nullptr || instance.pClip->frameCount == 0)
        {
            continue;
        }

        float leftGain = 0.0f;
        float rightGain = 0.0f;
        calculateStereoGains(listenerState, instance, leftGain, rightGain);

        for (int frameIndex = 0; frameIndex < MixChunkFrames; ++frameIndex)
        {
            if (instance.frameOffset >= instance.pClip->frameCount)
            {
                if (!instance.loop)
                {
                    break;
                }

                instance.frameOffset = 0;
            }

            const size_t sourceIndex = static_cast<size_t>(instance.frameOffset) * OutputChannels;
            const size_t destinationIndex = static_cast<size_t>(frameIndex) * OutputChannels;
            mixedSamples[destinationIndex] += instance.pClip->samples[sourceIndex] * leftGain;
            mixedSamples[destinationIndex + 1] += instance.pClip->samples[sourceIndex + 1] * rightGain;
            ++instance.frameOffset;
        }
    }

    for (float &sample : mixedSamples)
    {
        sample = std::clamp(sample, -1.0f, 1.0f);
    }

    m_playingInstances.erase(
        std::remove_if(
            m_playingInstances.begin(),
            m_playingInstances.end(),
            [](const PlayingInstance &instance)
            {
                return instance.pClip == nullptr
                    || (!instance.loop && instance.frameOffset >= instance.pClip->frameCount);
            }),
        m_playingInstances.end());

    if (!SDL_PutAudioStreamData(
            m_pAudioStream,
            mixedSamples.data(),
            static_cast<int>(mixedSamples.size() * sizeof(float))))
    {
        std::cerr << "AudioSystem: SDL_PutAudioStreamData failed: " << SDL_GetError() << '\n';
    }
}

void AudioSystem::calculateStereoGains(
    const ListenerState &listenerState,
    const PlayingInstance &instance,
    float &leftGain,
    float &rightGain)
{
    if (!instance.positional)
    {
        leftGain = instance.volume;
        rightGain = instance.volume;
        return;
    }

    const float deltaX = instance.x - listenerState.x;
    const float deltaY = instance.y - listenerState.y;
    const float deltaZ = instance.z - listenerState.z;
    const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    constexpr float MaxAudibleDistance = 12000.0f;

    if (distance >= MaxAudibleDistance)
    {
        leftGain = 0.0f;
        rightGain = 0.0f;
        return;
    }

    const float normalizedDistance = distance / 768.0f;
    const float attenuation = 1.0f / (1.0f + normalizedDistance * normalizedDistance);
    const float pan = std::clamp(deltaX / 2048.0f, -1.0f, 1.0f);
    leftGain = instance.volume * attenuation * (pan <= 0.0f ? 1.0f : (1.0f - pan));
    rightGain = instance.volume * attenuation * (pan >= 0.0f ? 1.0f : (1.0f + pan));
}
}
