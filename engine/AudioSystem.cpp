#include "engine/AudioSystem.h"
#include "engine/AudioSpatialization.h"

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

SDL_AudioStream *openPlaybackStream(const SDL_AudioSpec &spec)
{
    SDL_AudioStream *pStream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &spec, nullptr, nullptr);

    if (pStream == nullptr)
    {
        std::cerr << "AudioSystem: SDL_OpenAudioDeviceStream failed: " << SDL_GetError() << '\n';
        return nullptr;
    }

    if (!SDL_ResumeAudioStreamDevice(pStream))
    {
        std::cerr << "AudioSystem: SDL_ResumeAudioStreamDevice failed: " << SDL_GetError() << '\n';
        SDL_DestroyAudioStream(pStream);
        return nullptr;
    }

    return pStream;
}

// Restarts the audio subsystem on SDL's silent dummy driver, which consumes audio in real time, so clips and video
// soundtracks still finish on schedule. The hint stays set, so every later stream (house videos, cutscenes) opens on
// it too.
bool switchToDummyAudioDriver()
{
    const char *pCurrentDriver = SDL_GetCurrentAudioDriver();

    if (pCurrentDriver != nullptr && std::strcmp(pCurrentDriver, "dummy") == 0)
    {
        return false;
    }

    std::cerr << "AudioSystem: no usable playback device on audio driver '"
              << (pCurrentDriver != nullptr ? pCurrentDriver : "none") << "', continuing without sound\n";
    SDL_SetHintWithPriority(SDL_HINT_AUDIO_DRIVER, "dummy", SDL_HINT_OVERRIDE);

    if (isAudioSubsystemInitialized())
    {
        SDL_QuitSubSystem(SDL_INIT_AUDIO);
    }

    if (!SDL_InitSubSystem(SDL_INIT_AUDIO))
    {
        std::cerr << "AudioSystem: SDL_InitSubSystem(SDL_INIT_AUDIO) with the dummy driver failed: "
                  << SDL_GetError() << '\n';
        return false;
    }

    return true;
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

    if (!isAudioSubsystemInitialized() && !SDL_InitSubSystem(SDL_INIT_AUDIO))
    {
        std::cerr << "AudioSystem: SDL_InitSubSystem(SDL_INIT_AUDIO) failed: " << SDL_GetError() << '\n';
    }
    else
    {
        m_pAudioStream = openPlaybackStream(m_outputSpec);
    }

    // A machine without a playback device (none attached, or all disabled) still runs the game, silently.
    if (m_pAudioStream == nullptr && switchToDummyAudioDriver())
    {
        m_pAudioStream = openPlaybackStream(m_outputSpec);
    }

    if (m_pAudioStream == nullptr)
    {
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

bool AudioSystem::releaseClip(const std::string &virtualPath)
{
    return m_clipCache.erase(virtualPath) != 0;
}

AudioSystem::CacheStats AudioSystem::cacheStats() const
{
    CacheStats stats = {};
    stats.clipCount = m_clipCache.size();

    for (const std::pair<const std::string, std::shared_ptr<AudioClip>> &entry : m_clipCache)
    {
        const std::shared_ptr<AudioClip> &pClip = entry.second;

        if (pClip != nullptr)
        {
            stats.sampleBytes += pClip->samples.size() * sizeof(float);
        }
    }

    return stats;
}

void AudioSystem::shutdown()
{
    stopAll();
    m_clipCache.clear();
    m_playbackCacheMissWarningPaths.clear();

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
    const bool playbackCacheMiss =
        m_pAssetFileSystem != nullptr && !virtualPath.empty() && !m_clipCache.contains(virtualPath);
    const uint64_t loadBeginTickNanoseconds = playbackCacheMiss ? SDL_GetTicksNS() : 0;
    std::shared_ptr<AudioClip> pClip = loadClip(virtualPath);

    if (playbackCacheMiss && m_playbackCacheMissWarningPaths.insert(virtualPath).second)
    {
        std::cerr << "[AssetLoadWarning] kind=audio phase=play"
                  << " path=\"" << virtualPath << "\""
                  << " result=" << (pClip != nullptr ? "loaded" : "failed")
                  << " load_us=" << (SDL_GetTicksNS() - loadBeginTickNanoseconds) / 1000
                  << " frames=" << (pClip != nullptr ? pClip->frameCount : 0)
                  << '\n';
    }

    if (pClip == nullptr || pClip->frameCount == 0)
    {
        return 0;
    }

    PlayingInstance instance = {};
    instance.instanceId = m_nextInstanceId++;
    instance.pClip = std::move(pClip);
    instance.volume = std::clamp(options.volume * GlobalSoundGain, 0.0f, 2.0f);
    instance.positional = options.positional;
    instance.attenuate = options.attenuate;
    instance.pan = options.pan;
    instance.loop = options.loop;
    instance.x = options.x;
    instance.y = options.y;
    instance.z = options.z;
    instance.pitch = std::clamp(options.pitch, 0.125f, 8.0f);
    instance.innerRadius = options.innerRadius;
    instance.outerRadius = options.outerRadius;
    m_playingInstances.push_back(std::move(instance));
    return m_playingInstances.back().instanceId;
}

uint64_t AudioSystem::playStream(std::shared_ptr<AudioStreamSource> pSource, const PlaybackOptions &options)
{
    if (pSource == nullptr)
    {
        return 0;
    }

    PlayingInstance instance = {};
    instance.instanceId = m_nextInstanceId++;
    instance.pStream = std::move(pSource);
    instance.volume = std::clamp(options.volume * GlobalSoundGain, 0.0f, 2.0f);
    instance.positional = options.positional;
    instance.attenuate = options.attenuate;
    instance.pan = options.pan;
    instance.x = options.x;
    instance.y = options.y;
    instance.z = options.z;
    instance.innerRadius = options.innerRadius;
    instance.outerRadius = options.outerRadius;
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

void AudioSystem::pauseClip(uint64_t instanceId)
{
    for (PlayingInstance &instance : m_playingInstances)
    {
        if (instance.instanceId == instanceId)
        {
            instance.paused = true;
            return;
        }
    }
}

void AudioSystem::resumeClip(uint64_t instanceId)
{
    for (PlayingInstance &instance : m_playingInstances)
    {
        if (instance.instanceId == instanceId)
        {
            instance.paused = false;
            return;
        }
    }
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

void AudioSystem::setClipPosition(uint64_t instanceId, float x, float y, float z)
{
    for (PlayingInstance &instance : m_playingInstances)
    {
        if (instance.instanceId == instanceId)
        {
            instance.x = x;
            instance.y = y;
            instance.z = z;
            return;
        }
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

void AudioSystem::clearQueuedAudio()
{
    if (m_pAudioStream != nullptr && isAudioSubsystemInitialized())
    {
        SDL_ClearAudioStream(m_pAudioStream);
    }
}

void AudioSystem::stopAll()
{
    m_playingInstances.clear();
    clearQueuedAudio();
}

void AudioSystem::update(const ListenerState &listenerState)
{
    if (m_pAudioStream == nullptr)
    {
        return;
    }

    while (SDL_GetAudioStreamQueued(m_pAudioStream) < TargetQueuedBytes)
    {
        if (!hasMixableInstances())
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

bool AudioSystem::hasMixableInstances() const
{
    return std::any_of(
        m_playingInstances.begin(),
        m_playingInstances.end(),
        [](const PlayingInstance &instance)
        {
            return !instance.paused
                && (instance.pStream != nullptr || (instance.pClip != nullptr && instance.pClip->frameCount > 0));
        });
}

void AudioSystem::mixNextChunk(const ListenerState &listenerState)
{
    std::vector<float> mixedSamples(static_cast<size_t>(MixChunkFrames * OutputChannels), 0.0f);

    for (PlayingInstance &instance : m_playingInstances)
    {
        if (instance.paused)
        {
            continue;
        }

        if (instance.pStream != nullptr)
        {
            float leftGain = 0.0f;
            float rightGain = 0.0f;
            calculateStereoGains(listenerState, instance, leftGain, rightGain);
            m_streamSamples.resize(static_cast<size_t>(MixChunkFrames * OutputChannels));
            const uint32_t frameCount = instance.pStream->read(m_streamSamples.data(), MixChunkFrames);

            for (uint32_t frameIndex = 0; frameIndex < frameCount; ++frameIndex)
            {
                const size_t index = static_cast<size_t>(frameIndex) * OutputChannels;
                mixedSamples[index] += m_streamSamples[index] * leftGain;
                mixedSamples[index + 1] += m_streamSamples[index + 1] * rightGain;
            }

            continue;
        }

        if (instance.pClip == nullptr || instance.pClip->frameCount == 0)
        {
            continue;
        }

        float leftGain = 0.0f;
        float rightGain = 0.0f;
        calculateStereoGains(listenerState, instance, leftGain, rightGain);

        for (int frameIndex = 0; frameIndex < MixChunkFrames; ++frameIndex)
        {
            if (instance.frameOffset >= static_cast<double>(instance.pClip->frameCount))
            {
                if (!instance.loop)
                {
                    break;
                }

                instance.frameOffset = std::fmod(
                    instance.frameOffset,
                    static_cast<double>(instance.pClip->frameCount));
            }

            const uint32_t sourceFrame = static_cast<uint32_t>(instance.frameOffset);
            const uint32_t nextFrame = sourceFrame + 1 < instance.pClip->frameCount
                ? sourceFrame + 1 : (instance.loop ? 0 : sourceFrame);
            const float interpolation = static_cast<float>(instance.frameOffset - sourceFrame);
            const size_t sourceIndex = static_cast<size_t>(sourceFrame) * OutputChannels;
            const size_t nextSourceIndex = static_cast<size_t>(nextFrame) * OutputChannels;
            const size_t destinationIndex = static_cast<size_t>(frameIndex) * OutputChannels;
            const float leftSample = instance.pClip->samples[sourceIndex] +
                (instance.pClip->samples[nextSourceIndex] - instance.pClip->samples[sourceIndex]) * interpolation;
            const float rightSample = instance.pClip->samples[sourceIndex + 1] +
                (instance.pClip->samples[nextSourceIndex + 1] - instance.pClip->samples[sourceIndex + 1]) *
                    interpolation;
            mixedSamples[destinationIndex] += leftSample * leftGain;
            mixedSamples[destinationIndex + 1] += rightSample * rightGain;
            instance.frameOffset += instance.pitch;
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
                if (instance.pStream != nullptr)
                {
                    return instance.pStream->finished();
                }

                return instance.pClip == nullptr
                    || (!instance.loop && instance.frameOffset >= static_cast<double>(instance.pClip->frameCount));
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
    const bool usesExplicitRadii = instance.innerRadius >= 0.0f && instance.outerRadius > instance.innerRadius;
    const float maxAudibleDistance = usesExplicitRadii ? instance.outerRadius : 12000.0f;

    if (instance.attenuate && distance >= maxAudibleDistance)
    {
        leftGain = 0.0f;
        rightGain = 0.0f;
        return;
    }

    float attenuation = 1.0f;
    if (!instance.attenuate)
    {
        attenuation = 1.0f;
    }
    else if (usesExplicitRadii)
    {
        attenuation = distance <= instance.innerRadius
            ? 1.0f
            : 1.0f - (distance - instance.innerRadius) / (instance.outerRadius - instance.innerRadius);
    }
    else
    {
        const float normalizedDistance = distance / 768.0f;
        attenuation = 1.0f / (1.0f + normalizedDistance * normalizedDistance);
    }
    const float pan = instance.pan ? positionalAudioPan(deltaX, deltaY, listenerState.yawRadians) : 0.0f;
    leftGain = instance.volume * attenuation * (pan <= 0.0f ? 1.0f : (1.0f - pan));
    rightGain = instance.volume * attenuation * (pan >= 0.0f ? 1.0f : (1.0f + pan));
}
}
