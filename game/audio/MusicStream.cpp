#include "game/audio/MusicStream.h"

extern "C"
{
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/channel_layout.h>
#include <libavutil/error.h>
#include <libavutil/opt.h>
#include <libavutil/samplefmt.h>
#include <libswresample/swresample.h>
}

#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
constexpr int OutputSampleRate = 48000;
constexpr int OutputChannels = 2;

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
    void operator()(AVIOContext *pIoContext) const
    {
        if (pIoContext != nullptr)
        {
            av_freep(&pIoContext->buffer);
            avio_context_free(&pIoContext);
        }
    }
};

using AvFormatContextPtr = std::unique_ptr<AVFormatContext, AvFormatContextCloser>;
using AvCodecContextPtr = std::unique_ptr<AVCodecContext, AvCodecContextCloser>;
using AvFramePtr = std::unique_ptr<AVFrame, AvFrameCloser>;
using AvPacketPtr = std::unique_ptr<AVPacket, AvPacketCloser>;
using SwrContextPtr = std::unique_ptr<SwrContext, SwrContextCloser>;
using AvioContextPtr = std::unique_ptr<AVIOContext, AvioContextCloser>;

struct MemoryAudioReader
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

int readAudioBytes(void *pOpaque, uint8_t *pBuffer, int bufferSize)
{
    if (pOpaque == nullptr || pBuffer == nullptr || bufferSize <= 0)
    {
        return AVERROR_EOF;
    }

    MemoryAudioReader &reader = *static_cast<MemoryAudioReader *>(pOpaque);

    if (reader.pBytes == nullptr || reader.position >= reader.pBytes->size())
    {
        return AVERROR_EOF;
    }

    const size_t remainingBytes = reader.pBytes->size() - reader.position;
    const size_t copySize = std::min(static_cast<size_t>(bufferSize), remainingBytes);
    std::memcpy(pBuffer, reader.pBytes->data() + reader.position, copySize);
    reader.position += copySize;
    return static_cast<int>(copySize);
}

int64_t seekAudioBytes(void *pOpaque, int64_t offset, int whence)
{
    if (pOpaque == nullptr)
    {
        return -1;
    }

    MemoryAudioReader &reader = *static_cast<MemoryAudioReader *>(pOpaque);

    if (reader.pBytes == nullptr)
    {
        return -1;
    }

    if (whence == AVSEEK_SIZE)
    {
        return static_cast<int64_t>(reader.pBytes->size());
    }

    int64_t targetPosition = 0;

    switch (whence)
    {
        case SEEK_SET:
            targetPosition = offset;
            break;

        case SEEK_CUR:
            targetPosition = static_cast<int64_t>(reader.position) + offset;
            break;

        case SEEK_END:
            targetPosition = static_cast<int64_t>(reader.pBytes->size()) + offset;
            break;

        default:
            return -1;
    }

    if (targetPosition < 0 || targetPosition > static_cast<int64_t>(reader.pBytes->size()))
    {
        return -1;
    }

    reader.position = static_cast<size_t>(targetPosition);
    return targetPosition;
}



enum class DecodeStep
{
    Samples,
    End,
    Error
};

// One pass over an encoded track, a packet at a time, resampled to the mixer's stereo float format.
class TrackDecoder
{
public:
    bool open(const std::vector<uint8_t> &bytes)
    {
        m_reader.pBytes = &bytes;
        uint8_t *pIoBuffer = static_cast<uint8_t *>(av_malloc(4096));

        if (pIoBuffer == nullptr)
        {
            return false;
        }

        m_pIoContext.reset(
            avio_alloc_context(pIoBuffer, 4096, 0, &m_reader, &readAudioBytes, nullptr, &seekAudioBytes));

        if (m_pIoContext == nullptr)
        {
            av_free(pIoBuffer);
            return false;
        }

        AVFormatContext *pRawFormatContext = avformat_alloc_context();

        if (pRawFormatContext == nullptr)
        {
            return false;
        }

        pRawFormatContext->pb = m_pIoContext.get();
        pRawFormatContext->flags |= AVFMT_FLAG_CUSTOM_IO;
        int result = avformat_open_input(&pRawFormatContext, nullptr, nullptr, nullptr);

        if (result < 0)
        {
            avformat_free_context(pRawFormatContext);
            std::cerr << "MusicStream: avformat_open_input failed: " << ffmpegErrorString(result) << '\n';
            return false;
        }

        m_pFormatContext.reset(pRawFormatContext);
        result = avformat_find_stream_info(m_pFormatContext.get(), nullptr);

        if (result < 0)
        {
            std::cerr << "MusicStream: avformat_find_stream_info failed: " << ffmpegErrorString(result) << '\n';
            return false;
        }

        m_streamIndex = av_find_best_stream(m_pFormatContext.get(), AVMEDIA_TYPE_AUDIO, -1, -1, nullptr, 0);

        if (m_streamIndex < 0)
        {
            std::cerr << "MusicStream: no decodable audio stream found\n";
            return false;
        }

        const AVStream *pStream = m_pFormatContext->streams[m_streamIndex];
        const AVCodec *pCodec = avcodec_find_decoder(pStream->codecpar->codec_id);

        if (pCodec == nullptr)
        {
            std::cerr << "MusicStream: decoder not available for codec id " << pStream->codecpar->codec_id << '\n';
            return false;
        }

        m_pCodecContext.reset(avcodec_alloc_context3(pCodec));

        if (m_pCodecContext == nullptr)
        {
            return false;
        }

        result = avcodec_parameters_to_context(m_pCodecContext.get(), pStream->codecpar);

        if (result < 0)
        {
            std::cerr << "MusicStream: avcodec_parameters_to_context failed: " << ffmpegErrorString(result) << '\n';
            return false;
        }

        result = avcodec_open2(m_pCodecContext.get(), pCodec, nullptr);

        if (result < 0)
        {
            std::cerr << "MusicStream: avcodec_open2 failed: " << ffmpegErrorString(result) << '\n';
            return false;
        }

        m_pResampler.reset(swr_alloc());

        if (m_pResampler == nullptr)
        {
            return false;
        }

        AVChannelLayout outputLayout = AV_CHANNEL_LAYOUT_STEREO;
        av_opt_set_chlayout(m_pResampler.get(), "in_chlayout", &m_pCodecContext->ch_layout, 0);
        av_opt_set_chlayout(m_pResampler.get(), "out_chlayout", &outputLayout, 0);
        av_opt_set_int(m_pResampler.get(), "in_sample_rate", m_pCodecContext->sample_rate, 0);
        av_opt_set_int(m_pResampler.get(), "out_sample_rate", OutputSampleRate, 0);
        av_opt_set_sample_fmt(m_pResampler.get(), "in_sample_fmt", m_pCodecContext->sample_fmt, 0);
        av_opt_set_sample_fmt(m_pResampler.get(), "out_sample_fmt", AV_SAMPLE_FMT_FLT, 0);
        result = swr_init(m_pResampler.get());

        if (result < 0)
        {
            std::cerr << "MusicStream: swr_init failed: " << ffmpegErrorString(result) << '\n';
            return false;
        }

        m_pPacket.reset(av_packet_alloc());
        m_pFrame.reset(av_frame_alloc());
        return m_pPacket != nullptr && m_pFrame != nullptr;
    }

    // Appends the samples of the next packet; End once the last packet and the decoder's delay are out.
    DecodeStep decodeNext(std::vector<float> &samples)
    {
        while (true)
        {
            int result = av_read_frame(m_pFormatContext.get(), m_pPacket.get());

            if (result == AVERROR_EOF)
            {
                result = avcodec_send_packet(m_pCodecContext.get(), nullptr);

                if (result < 0)
                {
                    std::cerr << "MusicStream: avcodec_send_packet(flush) failed: " << ffmpegErrorString(result)
                              << '\n';
                    return DecodeStep::Error;
                }

                return receiveFrames(samples) ? DecodeStep::End : DecodeStep::Error;
            }

            if (result < 0)
            {
                std::cerr << "MusicStream: av_read_frame failed: " << ffmpegErrorString(result) << '\n';
                return DecodeStep::Error;
            }

            if (m_pPacket->stream_index != m_streamIndex)
            {
                av_packet_unref(m_pPacket.get());
                continue;
            }

            result = avcodec_send_packet(m_pCodecContext.get(), m_pPacket.get());
            av_packet_unref(m_pPacket.get());

            if (result < 0)
            {
                std::cerr << "MusicStream: avcodec_send_packet failed: " << ffmpegErrorString(result) << '\n';
                return DecodeStep::Error;
            }

            return receiveFrames(samples) ? DecodeStep::Samples : DecodeStep::Error;
        }
    }

private:
    bool receiveFrames(std::vector<float> &samples)
    {
        while (true)
        {
            const int result = avcodec_receive_frame(m_pCodecContext.get(), m_pFrame.get());

            if (result == AVERROR(EAGAIN) || result == AVERROR_EOF)
            {
                return true;
            }

            if (result < 0)
            {
                std::cerr << "MusicStream: avcodec_receive_frame failed: " << ffmpegErrorString(result) << '\n';
                return false;
            }

            const bool appended = appendFrame(samples);
            av_frame_unref(m_pFrame.get());

            if (!appended)
            {
                std::cerr << "MusicStream: failed to resample decoded audio frame\n";
                return false;
            }
        }
    }

    bool appendFrame(std::vector<float> &samples)
    {
        const int sourceRate = m_pCodecContext->sample_rate;
        const int outputCapacity = int(av_rescale_rnd(swr_get_delay(m_pResampler.get(), sourceRate)
            + m_pFrame->nb_samples, OutputSampleRate, sourceRate, AV_ROUND_UP));

        if (outputCapacity <= 0)
        {
            return true;
        }

        const size_t start = samples.size();
        samples.resize(start + size_t(outputCapacity) * OutputChannels);
        uint8_t *pOutputData[1] = {reinterpret_cast<uint8_t *>(samples.data() + start)};
        const int convertedFrames = swr_convert(m_pResampler.get(), pOutputData, outputCapacity,
            const_cast<const uint8_t **>(m_pFrame->extended_data), m_pFrame->nb_samples);

        if (convertedFrames < 0)
        {
            samples.resize(start);
            return false;
        }

        samples.resize(start + size_t(convertedFrames) * OutputChannels);
        return true;
    }

    MemoryAudioReader m_reader;
    AvioContextPtr m_pIoContext;
    AvFormatContextPtr m_pFormatContext;
    AvCodecContextPtr m_pCodecContext;
    SwrContextPtr m_pResampler;
    AvPacketPtr m_pPacket;
    AvFramePtr m_pFrame;
    int m_streamIndex = -1;
};
}

MusicStream::MusicStream(std::shared_ptr<const std::vector<uint8_t>> pEncodedTrack, float loopGapSeconds)
    : m_pEncodedTrack(std::move(pEncodedTrack))
    , m_loopGapFrames(uint32_t(std::clamp(loopGapSeconds, 0.0f, 600.0f) * float(OutputSampleRate)))
    , m_buffer(size_t(BufferFrames) * OutputChannels)
{
    m_worker = std::thread([this]()
    {
        decodeTrack();
    });
}

MusicStream::~MusicStream()
{
    {
        const std::lock_guard<std::mutex> lock(m_mutex);
        m_stopRequested = true;
    }

    m_spaceAvailable.notify_all();
    m_worker.join();
}

uint32_t MusicStream::read(float *pSamples, uint32_t frameCount)
{
    uint32_t count = 0;

    {
        const std::lock_guard<std::mutex> lock(m_mutex);
        count = uint32_t(std::min<uint64_t>(frameCount, m_framesWritten - m_framesRead));
        const uint32_t start = uint32_t(m_framesRead % BufferFrames);
        const uint32_t firstCount = std::min(count, BufferFrames - start);
        std::memcpy(pSamples, m_buffer.data() + size_t(start) * OutputChannels,
            size_t(firstCount) * OutputChannels * sizeof(float));
        std::memcpy(pSamples + size_t(firstCount) * OutputChannels, m_buffer.data(),
            size_t(count - firstCount) * OutputChannels * sizeof(float));
        m_framesRead += count;
    }

    if (count > 0)
    {
        m_spaceAvailable.notify_one();
    }

    return count;
}

bool MusicStream::finished() const
{
    const std::lock_guard<std::mutex> lock(m_mutex);
    return m_failed && m_framesWritten == m_framesRead;
}

void MusicStream::decodeTrack()
{
    std::vector<float> samples;

    // Each pass decodes the track from its start, so every loop repeats the first pass's samples exactly.
    while (true)
    {
        TrackDecoder decoder;
        uint64_t passFrames = 0;
        DecodeStep step = decoder.open(*m_pEncodedTrack) ? DecodeStep::Samples : DecodeStep::Error;

        while (step == DecodeStep::Samples)
        {
            samples.clear();
            step = decoder.decodeNext(samples);
            const uint32_t frameCount = uint32_t(samples.size() / OutputChannels);

            if (step != DecodeStep::Error && !writeFrames(samples.data(), frameCount))
            {
                return;
            }

            passFrames += frameCount;
        }

        if (step == DecodeStep::Error || passFrames == 0)
        {
            std::cerr << "MusicStream: failed to decode the music track\n";
            const std::lock_guard<std::mutex> lock(m_mutex);
            m_failed = true;
            return;
        }

        // The silence before the next pass.
        constexpr uint32_t SilenceChunkFrames = 4096;
        samples.assign(size_t(SilenceChunkFrames) * OutputChannels, 0.0f);

        for (uint32_t gapFrames = m_loopGapFrames; gapFrames > 0;)
        {
            const uint32_t frameCount = std::min(gapFrames, SilenceChunkFrames);

            if (!writeFrames(samples.data(), frameCount))
            {
                return;
            }

            gapFrames -= frameCount;
        }
    }
}

bool MusicStream::writeFrames(const float *pSamples, uint32_t frameCount)
{
    while (frameCount > 0)
    {
        std::unique_lock<std::mutex> lock(m_mutex);
        m_spaceAvailable.wait(lock, [this]()
        {
            return m_stopRequested || m_framesWritten - m_framesRead < BufferFrames;
        });

        if (m_stopRequested)
        {
            return false;
        }

        const uint32_t count = std::min(frameCount, BufferFrames - uint32_t(m_framesWritten - m_framesRead));
        const uint32_t start = uint32_t(m_framesWritten % BufferFrames);
        const uint32_t firstCount = std::min(count, BufferFrames - start);
        std::memcpy(m_buffer.data() + size_t(start) * OutputChannels, pSamples,
            size_t(firstCount) * OutputChannels * sizeof(float));
        std::memcpy(m_buffer.data(), pSamples + size_t(firstCount) * OutputChannels,
            size_t(count - firstCount) * OutputChannels * sizeof(float));
        m_framesWritten += count;
        pSamples += size_t(count) * OutputChannels;
        frameCount -= count;
    }

    return true;
}
}
