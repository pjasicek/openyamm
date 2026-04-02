#include "game/audio/HouseVideoPlayer.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

extern "C"
{
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/channel_layout.h>
#include <libavutil/error.h>
#include <libavutil/imgutils.h>
#include <libavutil/samplefmt.h>
#include <libswresample/swresample.h>
#include <libswscale/swscale.h>
}

#include <algorithm>
#include <array>
#include <cerrno>
#include <cctype>
#include <chrono>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr int HouseVideoAudioFrequency = 48000;
constexpr int HouseVideoAudioChannels = 2;
constexpr int HouseVideoAudioQueueTargetMilliseconds = 100;
constexpr size_t InvalidFrameIndex = std::numeric_limits<size_t>::max();

bool isAudioSubsystemInitialized()
{
    return (SDL_WasInit(SDL_INIT_AUDIO) & SDL_INIT_AUDIO) != 0;
}

struct AvFormatContextCloser
{
    void operator()(AVFormatContext *pFormatContext) const
    {
        if (pFormatContext != nullptr)
        {
            avformat_close_input(&pFormatContext);
        }
    }
};

struct AvCodecContextCloser
{
    void operator()(AVCodecContext *pCodecContext) const
    {
        if (pCodecContext != nullptr)
        {
            avcodec_free_context(&pCodecContext);
        }
    }
};

struct AvFrameCloser
{
    void operator()(AVFrame *pFrame) const
    {
        if (pFrame != nullptr)
        {
            av_frame_free(&pFrame);
        }
    }
};

struct AvPacketCloser
{
    void operator()(AVPacket *pPacket) const
    {
        if (pPacket != nullptr)
        {
            av_packet_free(&pPacket);
        }
    }
};

struct SwsContextCloser
{
    void operator()(SwsContext *pSwsContext) const
    {
        if (pSwsContext != nullptr)
        {
            sws_freeContext(pSwsContext);
        }
    }
};

struct SwrContextCloser
{
    void operator()(SwrContext *pSwrContext) const
    {
        if (pSwrContext != nullptr)
        {
            swr_free(&pSwrContext);
        }
    }
};

struct AvioContextCloser
{
    void operator()(AVIOContext *pAvioContext) const
    {
        if (pAvioContext != nullptr)
        {
            av_freep(&pAvioContext->buffer);
            avio_context_free(&pAvioContext);
        }
    }
};

using AvFormatContextPtr = std::unique_ptr<AVFormatContext, AvFormatContextCloser>;
using AvCodecContextPtr = std::unique_ptr<AVCodecContext, AvCodecContextCloser>;
using AvFramePtr = std::unique_ptr<AVFrame, AvFrameCloser>;
using AvPacketPtr = std::unique_ptr<AVPacket, AvPacketCloser>;
using SwsContextPtr = std::unique_ptr<SwsContext, SwsContextCloser>;
using SwrContextPtr = std::unique_ptr<SwrContext, SwrContextCloser>;
using AvioContextPtr = std::unique_ptr<AVIOContext, AvioContextCloser>;

struct MemoryClipReader
{
    const std::vector<uint8_t> *pBytes = nullptr;
    size_t position = 0;
};

std::string ffmpegErrorString(int errorCode)
{
    std::array<char, AV_ERROR_MAX_STRING_SIZE> buffer = {};
    av_strerror(errorCode, buffer.data(), buffer.size());
    return std::string(buffer.data());
}

std::optional<float> parseFrameRate(const AVRational &frameRate)
{
    if (frameRate.num <= 0 || frameRate.den <= 0)
    {
        return std::nullopt;
    }

    return static_cast<float>(frameRate.num) / static_cast<float>(frameRate.den);
}

std::optional<float> streamDurationSeconds(const AVStream &stream, const AVFormatContext &formatContext)
{
    if (stream.duration > 0 && stream.time_base.num > 0 && stream.time_base.den > 0)
    {
        return static_cast<float>(stream.duration) * av_q2d(stream.time_base);
    }

    if (formatContext.duration > 0)
    {
        return static_cast<float>(formatContext.duration) / static_cast<float>(AV_TIME_BASE);
    }

    return std::nullopt;
}

AvCodecContextPtr createDecoderContext(const AVStream &stream)
{
    const AVCodec *pCodec = avcodec_find_decoder(stream.codecpar->codec_id);

    if (pCodec == nullptr)
    {
        return nullptr;
    }

    AVCodecContext *pRawCodecContext = avcodec_alloc_context3(pCodec);

    if (pRawCodecContext == nullptr)
    {
        return nullptr;
    }

    AvCodecContextPtr pCodecContext(pRawCodecContext);

    int result = avcodec_parameters_to_context(pCodecContext.get(), stream.codecpar);

    if (result < 0)
    {
        std::cerr << "HouseVideoPlayer: avcodec_parameters_to_context failed: "
                  << ffmpegErrorString(result) << '\n';
        return nullptr;
    }

    result = avcodec_open2(pCodecContext.get(), pCodec, nullptr);

    if (result < 0)
    {
        std::cerr << "HouseVideoPlayer: avcodec_open2 failed: " << ffmpegErrorString(result) << '\n';
        return nullptr;
    }

    return pCodecContext;
}

bool appendVideoFrame(
    const AVFrame &frame,
    SwsContext &swsContext,
    int width,
    int height,
    std::vector<uint8_t> &videoPixels)
{
    if (frame.width != width || frame.height != height)
    {
        return false;
    }

    const size_t frameSizeBytes = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;
    const size_t previousSize = videoPixels.size();
    videoPixels.resize(previousSize + frameSizeBytes);
    uint8_t *pDestinationData[4] = {};
    int destinationLinesize[4] = {};
    const int fillResult = av_image_fill_arrays(
        pDestinationData,
        destinationLinesize,
        videoPixels.data() + previousSize,
        AV_PIX_FMT_BGRA,
        width,
        height,
        1);

    if (fillResult < 0)
    {
        return false;
    }

    sws_scale(
        &swsContext,
        frame.data,
        frame.linesize,
        0,
        height,
        pDestinationData,
        destinationLinesize);
    return true;
}

bool appendAudioFrame(
    const AVFrame &frame,
    SwrContext &swrContext,
    int outputSampleRate,
    int outputChannels,
    std::vector<float> &audioSamples)
{
    const int outputSampleCapacity = av_rescale_rnd(
        swr_get_delay(&swrContext, frame.sample_rate) + frame.nb_samples,
        outputSampleRate,
        frame.sample_rate,
        AV_ROUND_UP);

    if (outputSampleCapacity <= 0)
    {
        return true;
    }

    std::vector<float> convertedSamples(static_cast<size_t>(outputSampleCapacity) * static_cast<size_t>(outputChannels));
    uint8_t *pOutputData[1] = {reinterpret_cast<uint8_t *>(convertedSamples.data())};
    const int convertedSampleCount = swr_convert(
        &swrContext,
        pOutputData,
        outputSampleCapacity,
        const_cast<const uint8_t **>(frame.extended_data),
        frame.nb_samples);

    if (convertedSampleCount < 0)
    {
        std::cerr << "HouseVideoPlayer: swr_convert failed: " << ffmpegErrorString(convertedSampleCount) << '\n';
        return false;
    }

    convertedSamples.resize(static_cast<size_t>(convertedSampleCount) * static_cast<size_t>(outputChannels));
    audioSamples.insert(audioSamples.end(), convertedSamples.begin(), convertedSamples.end());
    return true;
}

int readMemoryClip(void *pOpaque, uint8_t *pBuffer, int bufferSize)
{
    MemoryClipReader *pReader = static_cast<MemoryClipReader *>(pOpaque);

    if (pReader == nullptr || pReader->pBytes == nullptr || bufferSize <= 0)
    {
        return AVERROR(EINVAL);
    }

    if (pReader->position >= pReader->pBytes->size())
    {
        return AVERROR_EOF;
    }

    const size_t remainingBytes = pReader->pBytes->size() - pReader->position;
    const size_t copySize = std::min(remainingBytes, static_cast<size_t>(bufferSize));
    std::memcpy(pBuffer, pReader->pBytes->data() + pReader->position, copySize);
    pReader->position += copySize;
    return static_cast<int>(copySize);
}

int64_t seekMemoryClip(void *pOpaque, int64_t offset, int whence)
{
    MemoryClipReader *pReader = static_cast<MemoryClipReader *>(pOpaque);

    if (pReader == nullptr || pReader->pBytes == nullptr)
    {
        return AVERROR(EINVAL);
    }

    if (whence == AVSEEK_SIZE)
    {
        return static_cast<int64_t>(pReader->pBytes->size());
    }

    const int seekMode = whence & ~AVSEEK_FORCE;
    int64_t baseOffset = 0;

    switch (seekMode)
    {
        case SEEK_SET:
            baseOffset = 0;
            break;

        case SEEK_CUR:
            baseOffset = static_cast<int64_t>(pReader->position);
            break;

        case SEEK_END:
            baseOffset = static_cast<int64_t>(pReader->pBytes->size());
            break;

        default:
            return AVERROR(EINVAL);
    }

    const int64_t targetOffset = baseOffset + offset;

    if (targetOffset < 0 || static_cast<uint64_t>(targetOffset) > pReader->pBytes->size())
    {
        return AVERROR(EINVAL);
    }

    pReader->position = static_cast<size_t>(targetOffset);
    return targetOffset;
}
}

HouseVideoPlayer::HouseVideoPlayer()
    : m_isInitialized(false)
    , m_initializedAudioSubsystem(false)
    , m_videoTextureHandle(BGFX_INVALID_HANDLE)
    , m_videoTextureWidth(0)
    , m_videoTextureHeight(0)
    , m_pAudioStream(nullptr)
    , m_pActiveClip(nullptr)
    , m_playbackSeconds(0.0f)
    , m_uploadedFrameIndex(InvalidFrameIndex)
    , m_nextAudioSampleIndex(0)
    , m_totalQueuedAudioFrames(0)
{
}

HouseVideoPlayer::~HouseVideoPlayer()
{
    shutdown();
}

bool HouseVideoPlayer::initialize()
{
    if (m_isInitialized)
    {
        return true;
    }

    if (!isAudioSubsystemInitialized())
    {
        if (!SDL_InitSubSystem(SDL_INIT_AUDIO))
        {
            std::cerr << "HouseVideoPlayer: SDL_InitSubSystem(SDL_INIT_AUDIO) failed: " << SDL_GetError() << '\n';
            m_isInitialized = true;
            return false;
        }

        m_initializedAudioSubsystem = true;
    }

    m_isInitialized = true;
    return true;
}

void HouseVideoPlayer::shutdown()
{
    stop();
    clearBackgroundPreloads();
    m_cachedClipsByStem.clear();

    if (m_pAudioStream != nullptr)
    {
        if (isAudioSubsystemInitialized())
        {
            SDL_DestroyAudioStream(m_pAudioStream);
        }

        m_pAudioStream = nullptr;
    }

    if (bgfx::isValid(m_videoTextureHandle))
    {
        bgfx::destroy(m_videoTextureHandle);
        m_videoTextureHandle = BGFX_INVALID_HANDLE;
    }

    m_videoTextureWidth = 0;
    m_videoTextureHeight = 0;

    if (m_initializedAudioSubsystem)
    {
        if (isAudioSubsystemInitialized())
        {
            SDL_QuitSubSystem(SDL_INIT_AUDIO);
        }

        m_initializedAudioSubsystem = false;
    }

    m_isInitialized = false;
}

void HouseVideoPlayer::stop()
{
    m_pActiveClip.reset();
    m_activeStem.clear();
    m_playbackSeconds = 0.0f;
    m_uploadedFrameIndex = InvalidFrameIndex;
    m_nextAudioSampleIndex = 0;
    m_totalQueuedAudioFrames = 0;

    if (m_pAudioStream != nullptr && isAudioSubsystemInitialized())
    {
        SDL_ClearAudioStream(m_pAudioStream);
    }
}

bool HouseVideoPlayer::play(const Engine::AssetFileSystem &assetFileSystem, const std::string &videoStem)
{
    if (videoStem.empty())
    {
        stop();
        return false;
    }

    if (!m_isInitialized)
    {
        initialize();
    }

    finishCompletedBackgroundPreload();

    if (m_pActiveClip != nullptr && m_activeStem == videoStem)
    {
        return true;
    }

    const std::shared_ptr<DecodedClip> pClip = getOrDecodeClip(assetFileSystem, videoStem);

    if (pClip == nullptr)
    {
        stop();
        return false;
    }

    m_pActiveClip = pClip;
    m_activeStem = videoStem;
    m_playbackSeconds = 0.0f;
    m_uploadedFrameIndex = InvalidFrameIndex;
    m_nextAudioSampleIndex = 0;
    m_totalQueuedAudioFrames = 0;
    ensureVideoTexture(pClip->width, pClip->height);
    uploadVideoFrame(0);

    if (m_pAudioStream != nullptr)
    {
        SDL_ClearAudioStream(m_pAudioStream);
    }

    updateAudioQueue();
    return true;
}

bool HouseVideoPlayer::preload(const Engine::AssetFileSystem &assetFileSystem, const std::string &videoStem)
{
    if (videoStem.empty())
    {
        return false;
    }

    if (!m_isInitialized)
    {
        initialize();
    }

    finishCompletedBackgroundPreload();

    return getOrDecodeClip(assetFileSystem, videoStem) != nullptr;
}

void HouseVideoPlayer::queueBackgroundPreload(const std::string &videoStem)
{
    if (videoStem.empty()
        || m_cachedClipsByStem.contains(videoStem)
        || std::find(m_pendingBackgroundPreloadStems.begin(), m_pendingBackgroundPreloadStems.end(), videoStem)
            != m_pendingBackgroundPreloadStems.end()
        || (m_backgroundPreloadJob.has_value() && m_backgroundPreloadJob->videoStem == videoStem))
    {
        return;
    }

    m_pendingBackgroundPreloadStems.push_back(videoStem);
}

void HouseVideoPlayer::updateBackgroundPreloads(const Engine::AssetFileSystem &assetFileSystem)
{
    warmUpPlaybackPath();
    finishCompletedBackgroundPreload();

    if (m_backgroundPreloadJob.has_value())
    {
        return;
    }

    while (!m_pendingBackgroundPreloadStems.empty())
    {
        const std::string videoStem = m_pendingBackgroundPreloadStems.front();
        m_pendingBackgroundPreloadStems.erase(m_pendingBackgroundPreloadStems.begin());

        if (videoStem.empty() || m_cachedClipsByStem.contains(videoStem))
        {
            continue;
        }

        m_backgroundPreloadJob = BackgroundPreloadJob{
            videoStem,
            std::async(
                std::launch::async,
                [&assetFileSystem, videoStem]()
                {
                    return decodeClip(assetFileSystem, videoStem);
                })};
        break;
    }
}

void HouseVideoPlayer::warmUpPlaybackPath()
{
    if (!m_isInitialized)
    {
        initialize();
    }

    if (m_pAudioStream == nullptr)
    {
        ensureAudioStream();
    }
}

void HouseVideoPlayer::update(float deltaSeconds)
{
    if (m_pActiveClip == nullptr || m_pActiveClip->frameCount == 0 || m_pActiveClip->durationSeconds <= 0.0f)
    {
        return;
    }

    updateAudioQueue();

    const std::optional<float> audioPlaybackSeconds = playbackSecondsFromAudioQueue();

    if (audioPlaybackSeconds)
    {
        m_playbackSeconds = *audioPlaybackSeconds;
    }
    else
    {
        advancePlaybackWithoutAudio(deltaSeconds);
    }

    size_t frameIndex = static_cast<size_t>(m_playbackSeconds * m_pActiveClip->framesPerSecond);

    if (frameIndex >= m_pActiveClip->frameCount)
    {
        frameIndex = m_pActiveClip->frameCount - 1;
    }

    uploadVideoFrame(frameIndex);
}

bool HouseVideoPlayer::hasActiveFrame() const
{
    return m_pActiveClip != nullptr && bgfx::isValid(m_videoTextureHandle);
}

bgfx::TextureHandle HouseVideoPlayer::textureHandle() const
{
    return m_videoTextureHandle;
}

bool HouseVideoPlayer::ensureAudioStream()
{
    if (m_pAudioStream != nullptr)
    {
        return true;
    }

    SDL_AudioSpec desiredSpec = {};
    desiredSpec.format = SDL_AUDIO_F32;
    desiredSpec.channels = HouseVideoAudioChannels;
    desiredSpec.freq = HouseVideoAudioFrequency;
    m_pAudioStream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &desiredSpec, nullptr, nullptr);

    if (m_pAudioStream == nullptr)
    {
        std::cerr << "HouseVideoPlayer: SDL_OpenAudioDeviceStream failed: " << SDL_GetError() << '\n';
        return false;
    }

    if (!SDL_ResumeAudioStreamDevice(m_pAudioStream))
    {
        std::cerr << "HouseVideoPlayer: SDL_ResumeAudioStreamDevice failed: " << SDL_GetError() << '\n';
        SDL_DestroyAudioStream(m_pAudioStream);
        m_pAudioStream = nullptr;
        return false;
    }

    return true;
}

void HouseVideoPlayer::ensureVideoTexture(int width, int height)
{
    if (width <= 0 || height <= 0)
    {
        return;
    }

    if (bgfx::isValid(m_videoTextureHandle) && m_videoTextureWidth == width && m_videoTextureHeight == height)
    {
        return;
    }

    if (bgfx::isValid(m_videoTextureHandle))
    {
        bgfx::destroy(m_videoTextureHandle);
        m_videoTextureHandle = BGFX_INVALID_HANDLE;
    }

    m_videoTextureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP | BGFX_TEXTURE_BLIT_DST);
    m_videoTextureWidth = width;
    m_videoTextureHeight = height;
}

void HouseVideoPlayer::uploadVideoFrame(size_t frameIndex)
{
    if (m_pActiveClip == nullptr
        || !bgfx::isValid(m_videoTextureHandle)
        || frameIndex >= m_pActiveClip->frameCount
        || frameIndex == m_uploadedFrameIndex)
    {
        return;
    }

    const size_t frameOffset = frameIndex * m_pActiveClip->frameSizeBytes;

    if (frameOffset + m_pActiveClip->frameSizeBytes > m_pActiveClip->videoPixels.size())
    {
        return;
    }

    const bgfx::Memory *pMemory = bgfx::copy(
        m_pActiveClip->videoPixels.data() + frameOffset,
        static_cast<uint32_t>(m_pActiveClip->frameSizeBytes));
    bgfx::updateTexture2D(
        m_videoTextureHandle,
        0,
        0,
        0,
        0,
        static_cast<uint16_t>(m_pActiveClip->width),
        static_cast<uint16_t>(m_pActiveClip->height),
        pMemory);
    m_uploadedFrameIndex = frameIndex;
}

void HouseVideoPlayer::updateAudioQueue()
{
    if (m_pActiveClip == nullptr || m_pActiveClip->audioSamples.empty())
    {
        return;
    }

    if (!ensureAudioStream())
    {
        return;
    }

    const size_t clipAudioFrameCount =
        m_pActiveClip->audioChannels > 0 ? (m_pActiveClip->audioSamples.size() / m_pActiveClip->audioChannels) : 0;

    if (clipAudioFrameCount == 0)
    {
        return;
    }

    const int bytesPerAudioFrame = m_pActiveClip->audioChannels * static_cast<int>(sizeof(float));
    const int targetQueuedBytes =
        (m_pActiveClip->audioSampleRate * bytesPerAudioFrame * HouseVideoAudioQueueTargetMilliseconds) / 1000;
    int queuedBytes = SDL_GetAudioStreamQueued(m_pAudioStream);

    while (queuedBytes >= 0 && queuedBytes < targetQueuedBytes)
    {
        if (m_nextAudioSampleIndex >= m_pActiveClip->audioSamples.size())
        {
            m_nextAudioSampleIndex = 0;
        }

        const size_t remainingSamples = m_pActiveClip->audioSamples.size() - m_nextAudioSampleIndex;

        if (remainingSamples == 0)
        {
            break;
        }

        const int remainingTargetBytes = targetQueuedBytes - queuedBytes;

        if (remainingTargetBytes <= 0)
        {
            break;
        }

        const size_t availableFrames = remainingSamples / m_pActiveClip->audioChannels;
        const size_t requestedFrames = static_cast<size_t>(remainingTargetBytes / bytesPerAudioFrame);
        const size_t chunkFrames = std::min(availableFrames, std::max<size_t>(1, requestedFrames));

        if (chunkFrames == 0)
        {
            break;
        }

        const size_t chunkSampleCount = chunkFrames * m_pActiveClip->audioChannels;
        const size_t chunkBytes = chunkSampleCount * sizeof(float);

        if (!SDL_PutAudioStreamData(
                m_pAudioStream,
                m_pActiveClip->audioSamples.data() + m_nextAudioSampleIndex,
                static_cast<int>(chunkBytes)))
        {
            std::cerr << "HouseVideoPlayer: SDL_PutAudioStreamData failed: " << SDL_GetError() << '\n';
            break;
        }

        queuedBytes += static_cast<int>(chunkBytes);
        m_nextAudioSampleIndex += chunkSampleCount;
        m_totalQueuedAudioFrames += chunkFrames;
    }
}

void HouseVideoPlayer::advancePlaybackWithoutAudio(float deltaSeconds)
{
    if (m_pActiveClip == nullptr || m_pActiveClip->durationSeconds <= 0.0f)
    {
        return;
    }

    m_playbackSeconds += std::max(0.0f, deltaSeconds);

    while (m_playbackSeconds >= m_pActiveClip->durationSeconds)
    {
        m_playbackSeconds -= m_pActiveClip->durationSeconds;
    }
}

std::optional<float> HouseVideoPlayer::playbackSecondsFromAudioQueue() const
{
    if (m_pActiveClip == nullptr
        || m_pAudioStream == nullptr
        || m_pActiveClip->audioSamples.empty()
        || m_pActiveClip->audioSampleRate <= 0
        || m_pActiveClip->audioChannels <= 0)
    {
        return std::nullopt;
    }

    const int queuedBytes = SDL_GetAudioStreamQueued(m_pAudioStream);

    if (queuedBytes < 0)
    {
        return std::nullopt;
    }

    const size_t bytesPerAudioFrame = static_cast<size_t>(m_pActiveClip->audioChannels) * sizeof(float);

    if (bytesPerAudioFrame == 0)
    {
        return std::nullopt;
    }

    const uint64_t queuedAudioFrames = static_cast<uint64_t>(queuedBytes) / bytesPerAudioFrame;
    const uint64_t playedAudioFrames =
        m_totalQueuedAudioFrames > queuedAudioFrames ? (m_totalQueuedAudioFrames - queuedAudioFrames) : 0;
    const size_t clipAudioFrameCount = m_pActiveClip->audioSamples.size() / m_pActiveClip->audioChannels;

    if (clipAudioFrameCount == 0)
    {
        return std::nullopt;
    }

    const uint64_t loopedAudioFrame = playedAudioFrames % clipAudioFrameCount;
    return static_cast<float>(loopedAudioFrame) / static_cast<float>(m_pActiveClip->audioSampleRate);
}

void HouseVideoPlayer::finishCompletedBackgroundPreload()
{
    if (!m_backgroundPreloadJob.has_value())
    {
        return;
    }

    if (m_backgroundPreloadJob->future.wait_for(std::chrono::seconds(0)) != std::future_status::ready)
    {
        return;
    }

    const std::shared_ptr<DecodedClip> pClip = m_backgroundPreloadJob->future.get();

    if (pClip != nullptr)
    {
        m_cachedClipsByStem[m_backgroundPreloadJob->videoStem] = pClip;
    }

    m_backgroundPreloadJob.reset();
}

void HouseVideoPlayer::clearBackgroundPreloads()
{
    m_pendingBackgroundPreloadStems.clear();

    if (!m_backgroundPreloadJob.has_value())
    {
        return;
    }

    const std::shared_ptr<DecodedClip> pClip = m_backgroundPreloadJob->future.get();

    if (pClip != nullptr)
    {
        m_cachedClipsByStem[m_backgroundPreloadJob->videoStem] = pClip;
    }

    m_backgroundPreloadJob.reset();
}

std::shared_ptr<HouseVideoPlayer::DecodedClip> HouseVideoPlayer::getOrDecodeClip(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &videoStem)
{
    finishCompletedBackgroundPreload();

    const std::unordered_map<std::string, std::shared_ptr<DecodedClip>>::const_iterator cachedIt =
        m_cachedClipsByStem.find(videoStem);

    if (cachedIt != m_cachedClipsByStem.end())
    {
        return cachedIt->second;
    }

    if (m_backgroundPreloadJob.has_value() && m_backgroundPreloadJob->videoStem == videoStem)
    {
        const std::shared_ptr<DecodedClip> pClip = m_backgroundPreloadJob->future.get();

        if (pClip != nullptr)
        {
            m_cachedClipsByStem.emplace(videoStem, pClip);
        }

        m_backgroundPreloadJob.reset();
        return pClip;
    }

    const std::shared_ptr<DecodedClip> pClip = decodeClip(assetFileSystem, videoStem);

    if (pClip != nullptr)
    {
        m_cachedClipsByStem.emplace(videoStem, pClip);
    }

    return pClip;
}

std::shared_ptr<HouseVideoPlayer::DecodedClip> HouseVideoPlayer::decodeClip(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &videoStem)
{
    const std::string virtualPath = "Videos/Houses/" + videoStem + ".ogv";
    const std::optional<std::vector<uint8_t>> clipBytes = assetFileSystem.readBinaryFile(virtualPath);

    if (!clipBytes || clipBytes->empty())
    {
        std::cerr << "HouseVideoPlayer: missing clip bytes for stem " << videoStem << '\n';
        return nullptr;
    }

    MemoryClipReader memoryClipReader = {};
    memoryClipReader.pBytes = &*clipBytes;
    constexpr int AvioBufferSize = 4096;
    uint8_t *pAvioBuffer = static_cast<uint8_t *>(av_malloc(AvioBufferSize));

    if (pAvioBuffer == nullptr)
    {
        std::cerr << "HouseVideoPlayer: av_malloc failed for " << virtualPath << '\n';
        return nullptr;
    }

    AVIOContext *pRawAvioContext = avio_alloc_context(
        pAvioBuffer,
        AvioBufferSize,
        0,
        &memoryClipReader,
        &readMemoryClip,
        nullptr,
        &seekMemoryClip);

    if (pRawAvioContext == nullptr)
    {
        av_free(pAvioBuffer);
        std::cerr << "HouseVideoPlayer: avio_alloc_context failed for " << virtualPath << '\n';
        return nullptr;
    }

    AvioContextPtr pAvioContext(pRawAvioContext);
    AVFormatContext *pRawFormatContext = avformat_alloc_context();

    if (pRawFormatContext == nullptr)
    {
        std::cerr << "HouseVideoPlayer: avformat_alloc_context failed for " << virtualPath << '\n';
        return nullptr;
    }

    pRawFormatContext->pb = pAvioContext.get();
    pRawFormatContext->flags |= AVFMT_FLAG_CUSTOM_IO;

    int result = avformat_open_input(&pRawFormatContext, virtualPath.c_str(), nullptr, nullptr);

    if (result < 0 || pRawFormatContext == nullptr)
    {
        if (pRawFormatContext != nullptr)
        {
            avformat_free_context(pRawFormatContext);
        }

        std::cerr << "HouseVideoPlayer: avformat_open_input failed for " << virtualPath
                  << ": " << ffmpegErrorString(result) << '\n';
        return nullptr;
    }

    AvFormatContextPtr pFormatContext(pRawFormatContext);
    result = avformat_find_stream_info(pFormatContext.get(), nullptr);

    if (result < 0)
    {
        std::cerr << "HouseVideoPlayer: avformat_find_stream_info failed for " << virtualPath
                  << ": " << ffmpegErrorString(result) << '\n';
        return nullptr;
    }

    const int videoStreamIndex = av_find_best_stream(pFormatContext.get(), AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);

    if (videoStreamIndex < 0)
    {
        std::cerr << "HouseVideoPlayer: no video stream found for " << virtualPath << '\n';
        return nullptr;
    }

    const AVStream &videoStream = *pFormatContext->streams[videoStreamIndex];
    AvCodecContextPtr pVideoCodecContext = createDecoderContext(videoStream);

    if (pVideoCodecContext == nullptr)
    {
        std::cerr << "HouseVideoPlayer: failed to create video decoder for " << virtualPath << '\n';
        return nullptr;
    }

    const int width = pVideoCodecContext->width;
    const int height = pVideoCodecContext->height;

    if (width <= 0 || height <= 0)
    {
        std::cerr << "HouseVideoPlayer: invalid video dimensions for " << virtualPath << '\n';
        return nullptr;
    }

    SwsContext *pRawSwsContext = sws_getContext(
        width,
        height,
        pVideoCodecContext->pix_fmt,
        width,
        height,
        AV_PIX_FMT_BGRA,
        SWS_BILINEAR,
        nullptr,
        nullptr,
        nullptr);

    if (pRawSwsContext == nullptr)
    {
        std::cerr << "HouseVideoPlayer: sws_getContext failed for " << virtualPath << '\n';
        return nullptr;
    }

    SwsContextPtr pSwsContext(pRawSwsContext);
    const int audioStreamIndex = av_find_best_stream(pFormatContext.get(), AVMEDIA_TYPE_AUDIO, -1, -1, nullptr, 0);
    AvCodecContextPtr pAudioCodecContext;
    SwrContextPtr pSwrContext;

    if (audioStreamIndex >= 0)
    {
        pAudioCodecContext = createDecoderContext(*pFormatContext->streams[audioStreamIndex]);

        if (pAudioCodecContext != nullptr && pAudioCodecContext->sample_rate > 0)
        {
            AVChannelLayout inputChannelLayout = {};

            if (av_channel_layout_check(&pAudioCodecContext->ch_layout) > 0)
            {
                result = av_channel_layout_copy(&inputChannelLayout, &pAudioCodecContext->ch_layout);
            }
            else
            {
                av_channel_layout_default(
                    &inputChannelLayout,
                    std::max(1, pAudioCodecContext->ch_layout.nb_channels));
                result = 0;
            }

            if (result >= 0)
            {
                AVChannelLayout outputChannelLayout = AV_CHANNEL_LAYOUT_STEREO;
                SwrContext *pRawSwrContext = nullptr;
                result = swr_alloc_set_opts2(
                    &pRawSwrContext,
                    &outputChannelLayout,
                    AV_SAMPLE_FMT_FLT,
                    HouseVideoAudioFrequency,
                    &inputChannelLayout,
                    pAudioCodecContext->sample_fmt,
                    pAudioCodecContext->sample_rate,
                    0,
                    nullptr);

                if (result >= 0 && pRawSwrContext != nullptr)
                {
                    result = swr_init(pRawSwrContext);

                    if (result >= 0)
                    {
                        pSwrContext.reset(pRawSwrContext);
                    }
                    else
                    {
                        swr_free(&pRawSwrContext);
                    }
                }

                av_channel_layout_uninit(&inputChannelLayout);
            }

            if (result < 0)
            {
                std::cerr << "HouseVideoPlayer: audio resampler setup failed for " << virtualPath
                          << ": " << ffmpegErrorString(result) << '\n';
                pAudioCodecContext.reset();
                pSwrContext.reset();
            }
        }
        else
        {
            pAudioCodecContext.reset();
        }
    }

    AvPacketPtr pPacket(av_packet_alloc());
    AvFramePtr pFrame(av_frame_alloc());

    if (pPacket == nullptr || pFrame == nullptr)
    {
        std::cerr << "HouseVideoPlayer: failed to allocate decode buffers for " << virtualPath << '\n';
        return nullptr;
    }

    std::vector<uint8_t> videoPixels;
    std::vector<float> audioSamples;
    const size_t frameSizeBytes = static_cast<size_t>(width) * static_cast<size_t>(height) * 4;

    while ((result = av_read_frame(pFormatContext.get(), pPacket.get())) >= 0)
    {
        AVCodecContext *pTargetCodecContext = nullptr;
        const bool isVideoPacket = pPacket->stream_index == videoStreamIndex;
        const bool isAudioPacket = pAudioCodecContext != nullptr && pPacket->stream_index == audioStreamIndex;

        if (isVideoPacket)
        {
            pTargetCodecContext = pVideoCodecContext.get();
        }
        else if (isAudioPacket)
        {
            pTargetCodecContext = pAudioCodecContext.get();
        }

        if (pTargetCodecContext == nullptr)
        {
            av_packet_unref(pPacket.get());
            continue;
        }

        result = avcodec_send_packet(pTargetCodecContext, pPacket.get());
        av_packet_unref(pPacket.get());

        if (result < 0)
        {
            std::cerr << "HouseVideoPlayer: avcodec_send_packet failed for " << virtualPath
                      << ": " << ffmpegErrorString(result) << '\n';
            return nullptr;
        }

        while (true)
        {
            result = avcodec_receive_frame(pTargetCodecContext, pFrame.get());

            if (result == AVERROR(EAGAIN) || result == AVERROR_EOF)
            {
                break;
            }

            if (result < 0)
            {
                std::cerr << "HouseVideoPlayer: avcodec_receive_frame failed for " << virtualPath
                          << ": " << ffmpegErrorString(result) << '\n';
                return nullptr;
            }

            const bool appendResult = isVideoPacket
                ? appendVideoFrame(*pFrame, *pSwsContext, width, height, videoPixels)
                : (pSwrContext != nullptr
                    ? appendAudioFrame(
                        *pFrame,
                        *pSwrContext,
                        HouseVideoAudioFrequency,
                        HouseVideoAudioChannels,
                        audioSamples)
                    : true);

            av_frame_unref(pFrame.get());

            if (!appendResult)
            {
                std::cerr << "HouseVideoPlayer: failed to append decoded frame for " << virtualPath << '\n';
                return nullptr;
            }
        }
    }

    if (result != AVERROR_EOF)
    {
        std::cerr << "HouseVideoPlayer: av_read_frame failed for " << virtualPath
                  << ": " << ffmpegErrorString(result) << '\n';
        return nullptr;
    }

    const std::array<AVCodecContext *, 2> codecContexts = {pVideoCodecContext.get(), pAudioCodecContext.get()};

    for (AVCodecContext *pCodecContext : codecContexts)
    {
        if (pCodecContext == nullptr)
        {
            continue;
        }

        result = avcodec_send_packet(pCodecContext, nullptr);

        if (result < 0 && result != AVERROR_EOF)
        {
            std::cerr << "HouseVideoPlayer: decoder flush failed for " << virtualPath
                      << ": " << ffmpegErrorString(result) << '\n';
            return nullptr;
        }

        while (true)
        {
            result = avcodec_receive_frame(pCodecContext, pFrame.get());

            if (result == AVERROR(EAGAIN) || result == AVERROR_EOF)
            {
                break;
            }

            if (result < 0)
            {
                std::cerr << "HouseVideoPlayer: decoder flush receive failed for " << virtualPath
                          << ": " << ffmpegErrorString(result) << '\n';
                return nullptr;
            }

            const bool isVideoFrame = pCodecContext == pVideoCodecContext.get();
            const bool appendResult = isVideoFrame
                ? appendVideoFrame(*pFrame, *pSwsContext, width, height, videoPixels)
                : (pSwrContext != nullptr
                    ? appendAudioFrame(
                        *pFrame,
                        *pSwrContext,
                        HouseVideoAudioFrequency,
                        HouseVideoAudioChannels,
                        audioSamples)
                    : true);

            av_frame_unref(pFrame.get());

            if (!appendResult)
            {
                std::cerr << "HouseVideoPlayer: failed to append flushed frame for " << virtualPath << '\n';
                return nullptr;
            }
        }
    }

    if (videoPixels.size() < frameSizeBytes)
    {
        std::cerr << "HouseVideoPlayer: decoded video too small for " << virtualPath << '\n';
        return nullptr;
    }

    const size_t frameCount = videoPixels.size() / frameSizeBytes;

    if (frameCount == 0)
    {
        std::cerr << "HouseVideoPlayer: zero decoded frames for " << virtualPath << '\n';
        return nullptr;
    }

    std::optional<float> frameRate = parseFrameRate(videoStream.avg_frame_rate);

    if ((!frameRate || *frameRate <= 0.0f))
    {
        frameRate = parseFrameRate(videoStream.r_frame_rate);
    }

    if ((!frameRate || *frameRate <= 0.0f))
    {
        const std::optional<float> durationSeconds = streamDurationSeconds(videoStream, *pFormatContext);

        if (durationSeconds && *durationSeconds > 0.0f)
        {
            frameRate = static_cast<float>(frameCount) / *durationSeconds;
        }
    }

    if (!frameRate || *frameRate <= 0.0f)
    {
        std::cerr << "HouseVideoPlayer: invalid frame rate for " << virtualPath << '\n';
        return nullptr;
    }

    std::shared_ptr<DecodedClip> pClip = std::make_shared<DecodedClip>();
    pClip->videoStem = videoStem;
    pClip->width = width;
    pClip->height = height;
    pClip->framesPerSecond = *frameRate;
    pClip->durationSeconds = static_cast<float>(frameCount) / *frameRate;
    pClip->frameCount = frameCount;
    pClip->frameSizeBytes = frameSizeBytes;
    pClip->videoPixels = std::move(videoPixels);
    pClip->audioSampleRate = HouseVideoAudioFrequency;
    pClip->audioChannels = HouseVideoAudioChannels;
    pClip->audioSamples = std::move(audioSamples);
    return pClip;
}

}
