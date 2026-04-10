#include "game/audio/GameAudioSystem.h"

#include "engine/TextTable.h"
#include "game/party/SpellIds.h"

#include <SDL3/SDL.h>

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

#include <array>
#include <algorithm>
#include <cstring>
#include <iostream>
#include <memory>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MusicVolume = 0.34f;
constexpr float MusicFadeInSeconds = 1.25f;
constexpr float MusicFadeOutSeconds = 0.6f;

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

bool decodeAudioSamplesFromBytes(const std::vector<uint8_t> &bytes, std::vector<float> &samples)
{
    samples.clear();

    if (bytes.empty())
    {
        return false;
    }

    MemoryAudioReader reader = {};
    reader.pBytes = &bytes;
    uint8_t *pIoBuffer = static_cast<uint8_t *>(av_malloc(4096));

    if (pIoBuffer == nullptr)
    {
        return false;
    }

    AVIOContext *pRawIoContext = avio_alloc_context(
        pIoBuffer,
        4096,
        0,
        &reader,
        &readAudioBytes,
        nullptr,
        &seekAudioBytes);

    if (pRawIoContext == nullptr)
    {
        return false;
    }

    AvioContextPtr pIoContext(pRawIoContext);
    AVFormatContext *pRawFormatContext = avformat_alloc_context();

    if (pRawFormatContext == nullptr)
    {
        return false;
    }

    pRawFormatContext->pb = pIoContext.get();
    pRawFormatContext->flags |= AVFMT_FLAG_CUSTOM_IO;
    const int openResult = avformat_open_input(&pRawFormatContext, nullptr, nullptr, nullptr);

    if (openResult < 0)
    {
        avformat_free_context(pRawFormatContext);
        std::cerr << "GameAudioSystem: avformat_open_input failed: " << ffmpegErrorString(openResult) << '\n';
        return false;
    }

    AvFormatContextPtr pFormatContext(pRawFormatContext);

    const int streamInfoResult = avformat_find_stream_info(pFormatContext.get(), nullptr);

    if (streamInfoResult < 0)
    {
        std::cerr << "GameAudioSystem: avformat_find_stream_info failed: "
                  << ffmpegErrorString(streamInfoResult) << '\n';
        return false;
    }

    const int audioStreamIndex = av_find_best_stream(pFormatContext.get(), AVMEDIA_TYPE_AUDIO, -1, -1, nullptr, 0);

    if (audioStreamIndex < 0)
    {
        std::cerr << "GameAudioSystem: no decodable audio stream found\n";
        return false;
    }

    AVStream *pStream = pFormatContext->streams[audioStreamIndex];
    const AVCodec *pCodec = avcodec_find_decoder(pStream->codecpar->codec_id);

    if (pCodec == nullptr)
    {
        std::cerr << "GameAudioSystem: decoder not available for codec id " << pStream->codecpar->codec_id << '\n';
        return false;
    }

    AvCodecContextPtr pCodecContext(avcodec_alloc_context3(pCodec));

    if (pCodecContext == nullptr)
    {
        return false;
    }

    int result = avcodec_parameters_to_context(pCodecContext.get(), pStream->codecpar);

    if (result < 0)
    {
        std::cerr << "GameAudioSystem: avcodec_parameters_to_context failed: "
                  << ffmpegErrorString(result) << '\n';
        return false;
    }

    result = avcodec_open2(pCodecContext.get(), pCodec, nullptr);

    if (result < 0)
    {
        std::cerr << "GameAudioSystem: avcodec_open2 failed: " << ffmpegErrorString(result) << '\n';
        return false;
    }

    SwrContextPtr pResampler(swr_alloc());

    if (pResampler == nullptr)
    {
        return false;
    }

    AVChannelLayout outputLayout = AV_CHANNEL_LAYOUT_STEREO;
    av_opt_set_chlayout(pResampler.get(), "in_chlayout", &pCodecContext->ch_layout, 0);
    av_opt_set_chlayout(pResampler.get(), "out_chlayout", &outputLayout, 0);
    av_opt_set_int(pResampler.get(), "in_sample_rate", pCodecContext->sample_rate, 0);
    av_opt_set_int(pResampler.get(), "out_sample_rate", 48000, 0);
    av_opt_set_sample_fmt(pResampler.get(), "in_sample_fmt", pCodecContext->sample_fmt, 0);
    av_opt_set_sample_fmt(pResampler.get(), "out_sample_fmt", AV_SAMPLE_FMT_FLT, 0);

    result = swr_init(pResampler.get());

    if (result < 0)
    {
        std::cerr << "GameAudioSystem: swr_init failed: " << ffmpegErrorString(result) << '\n';
        return false;
    }

    AvPacketPtr pPacket(av_packet_alloc());
    AvFramePtr pFrame(av_frame_alloc());

    if (pPacket == nullptr || pFrame == nullptr)
    {
        return false;
    }

    const auto appendFrame =
        [&samples, &pResampler](AVCodecContext &codecContext, const AVFrame &frame) -> bool
        {
            const int outputCapacity = av_rescale_rnd(
                swr_get_delay(pResampler.get(), codecContext.sample_rate) + frame.nb_samples,
                48000,
                codecContext.sample_rate,
                AV_ROUND_UP);

            if (outputCapacity <= 0)
            {
                return true;
            }

            std::vector<float> convertedSamples(static_cast<size_t>(outputCapacity) * 2);
            uint8_t *pOutputData[1] = {reinterpret_cast<uint8_t *>(convertedSamples.data())};
            const int convertedFrames = swr_convert(
                pResampler.get(),
                pOutputData,
                outputCapacity,
                const_cast<const uint8_t **>(frame.extended_data),
                frame.nb_samples);

            if (convertedFrames < 0)
            {
                return false;
            }

            convertedSamples.resize(static_cast<size_t>(convertedFrames) * 2);
            samples.insert(samples.end(), convertedSamples.begin(), convertedSamples.end());
            return true;
        };

    const auto drainDecoder =
        [&](bool flushing) -> bool
        {
            while (true)
            {
                result = avcodec_receive_frame(pCodecContext.get(), pFrame.get());

                if (result == AVERROR(EAGAIN))
                {
                    return true;
                }

                if (result == AVERROR_EOF)
                {
                    return true;
                }

                if (result < 0)
                {
                    std::cerr << "GameAudioSystem: avcodec_receive_frame failed: "
                              << ffmpegErrorString(result) << '\n';
                    return false;
                }

                if (!appendFrame(*pCodecContext, *pFrame))
                {
                    std::cerr << "GameAudioSystem: failed to resample decoded audio frame\n";
                    return false;
                }

                av_frame_unref(pFrame.get());

                if (!flushing)
                {
                    break;
                }
            }

            return true;
        };

    while ((result = av_read_frame(pFormatContext.get(), pPacket.get())) >= 0)
    {
        if (pPacket->stream_index != audioStreamIndex)
        {
            av_packet_unref(pPacket.get());
            continue;
        }

        result = avcodec_send_packet(pCodecContext.get(), pPacket.get());
        av_packet_unref(pPacket.get());

        if (result < 0)
        {
            std::cerr << "GameAudioSystem: avcodec_send_packet failed: "
                      << ffmpegErrorString(result) << '\n';
            return false;
        }

        if (!drainDecoder(false))
        {
            return false;
        }
    }

    if (result != AVERROR_EOF)
    {
        std::cerr << "GameAudioSystem: av_read_frame failed: " << ffmpegErrorString(result) << '\n';
        return false;
    }

    result = avcodec_send_packet(pCodecContext.get(), nullptr);

    if (result < 0)
    {
        std::cerr << "GameAudioSystem: avcodec_send_packet(flush) failed: "
                  << ffmpegErrorString(result) << '\n';
        return false;
    }

    return drainDecoder(true) && !samples.empty();
}
}

bool GameAudioSystem::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const CharacterDollTable &characterDollTable,
    const SpellTable &spellTable)
{
    shutdown();
    m_pCharacterDollTable = &characterDollTable;
    m_pAssetFileSystem = &assetFileSystem;

    const std::optional<std::string> soundCatalogText = assetFileSystem.readTextFile("Data/EnglishT/sounds.txt");
    const std::optional<std::string> speechReactionText = assetFileSystem.readTextFile("Data/SPEECH_REACTIONS.txt");

    if (!soundCatalogText || !speechReactionText)
    {
        return false;
    }

    const std::optional<Engine::TextTable> parsedSoundCatalog = Engine::TextTable::parseTabSeparated(*soundCatalogText);
    const std::optional<Engine::TextTable> parsedSpeechReactions =
        Engine::TextTable::parseTabSeparated(*speechReactionText);

    if (!parsedSoundCatalog || !parsedSpeechReactions)
    {
        return false;
    }

    std::vector<std::vector<std::string>> soundRows;
    soundRows.reserve(parsedSoundCatalog->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedSoundCatalog->getRowCount(); ++rowIndex)
    {
        soundRows.push_back(parsedSoundCatalog->getRow(rowIndex));
    }

    std::vector<std::vector<std::string>> speechRows;
    speechRows.reserve(parsedSpeechReactions->getRowCount());

    for (size_t rowIndex = 0; rowIndex < parsedSpeechReactions->getRowCount(); ++rowIndex)
    {
        speechRows.push_back(parsedSpeechReactions->getRow(rowIndex));
    }

    if (!m_soundCatalog.loadFromRows(soundRows)
        || !m_speechReactionTable.loadFromRows(speechRows)
        || !m_audioSystem.initialize(assetFileSystem))
    {
        shutdown();
        return false;
    }

    m_soundCatalog.initializeVirtualPathIndex(assetFileSystem);
    preloadSpellBuffSounds(spellTable);
    preloadArcomageUiSounds();
    return true;
}

void GameAudioSystem::shutdown()
{
    m_activeGroupInstanceIds.clear();
    m_activeSpeechInstanceIds.clear();
    m_activeNonResettableSoundInstanceIds.clear();
    m_loadedMusicClipKeys.clear();
    m_activeMusicTrack = 0;
    m_pendingMusicTrack = 0;
    m_activeMusicInstanceId = 0;
    m_activeMusicVolume = 0.0f;
    m_musicFadeVelocity = 0.0f;
    m_soundVolume = 1.0f;
    m_musicVolume = 1.0f;
    m_voiceVolume = 1.0f;
    m_audioSystem.shutdown();
    m_soundCatalog = {};
    m_speechReactionTable = {};
    m_pCharacterDollTable = nullptr;
    m_pAssetFileSystem = nullptr;
}

void GameAudioSystem::update(float listenerX, float listenerY, float listenerZ, float deltaSeconds)
{
    const float musicTargetVolume = targetMusicVolume();

    if (m_activeMusicInstanceId != 0 && !m_audioSystem.isClipPlaying(m_activeMusicInstanceId))
    {
        m_activeMusicInstanceId = 0;
        m_activeMusicTrack = 0;
        m_activeMusicVolume = 0.0f;
    }

    if (m_activeMusicInstanceId != 0 && m_musicFadeVelocity != 0.0f)
    {
        m_activeMusicVolume =
            std::clamp(m_activeMusicVolume + m_musicFadeVelocity * deltaSeconds, 0.0f, musicTargetVolume);
        m_audioSystem.setClipVolume(m_activeMusicInstanceId, m_activeMusicVolume);

        if (m_activeMusicVolume <= 0.0f && m_musicFadeVelocity < 0.0f)
        {
            m_audioSystem.stopClip(m_activeMusicInstanceId);
            m_activeMusicInstanceId = 0;
            m_activeMusicTrack = 0;
            m_musicFadeVelocity = 0.0f;

            if (m_pendingMusicTrack > 0)
            {
                const int nextTrack = m_pendingMusicTrack;
                m_pendingMusicTrack = 0;
                startBackgroundMusicTrack(nextTrack);
            }
        }
        else if (m_activeMusicVolume >= musicTargetVolume && m_musicFadeVelocity > 0.0f)
        {
            m_activeMusicVolume = musicTargetVolume;
            m_musicFadeVelocity = 0.0f;
        }
    }

    Engine::AudioSystem::ListenerState listenerState = {};
    listenerState.x = listenerX;
    listenerState.y = listenerY;
    listenerState.z = listenerZ;
    m_audioSystem.update(listenerState);
}

void GameAudioSystem::setSoundVolume(float volume)
{
    m_soundVolume = std::clamp(volume, 0.0f, 1.0f);
}

void GameAudioSystem::setMusicVolume(float volume)
{
    m_musicVolume = std::clamp(volume, 0.0f, 1.0f);

    if (m_activeMusicInstanceId == 0)
    {
        return;
    }

    if (m_musicFadeVelocity == 0.0f)
    {
        m_activeMusicVolume = targetMusicVolume();
        m_audioSystem.setClipVolume(m_activeMusicInstanceId, m_activeMusicVolume);
        return;
    }

    m_activeMusicVolume = std::clamp(m_activeMusicVolume, 0.0f, targetMusicVolume());
    m_audioSystem.setClipVolume(m_activeMusicInstanceId, m_activeMusicVolume);
}

void GameAudioSystem::setVoiceVolume(float volume)
{
    m_voiceVolume = std::clamp(volume, 0.0f, 1.0f);
}

void GameAudioSystem::preloadSpellBuffSounds(const SpellTable &spellTable)
{
    const std::array<SpellId, 24> preloadSpellIds = {
        SpellId::TorchLight,
        SpellId::FireResistance,
        SpellId::Haste,
        SpellId::WizardEye,
        SpellId::FeatherFall,
        SpellId::AirResistance,
        SpellId::Shield,
        SpellId::Invisibility,
        SpellId::Fly,
        SpellId::WaterResistance,
        SpellId::WaterWalk,
        SpellId::EarthResistance,
        SpellId::StoneSkin,
        SpellId::DetectLife,
        SpellId::Bless,
        SpellId::Preservation,
        SpellId::Heroism,
        SpellId::MindResistance,
        SpellId::BodyResistance,
        SpellId::Regeneration,
        SpellId::ProtectionFromMagic,
        SpellId::DayOfGods,
        SpellId::DayOfProtection,
        SpellId::HourOfPower
    };

    for (SpellId spellId : preloadSpellIds)
    {
        const SpellEntry *pSpellEntry = spellTable.findById(static_cast<int>(spellIdValue(spellId)));

        if (pSpellEntry == nullptr || pSpellEntry->effectSoundId <= 0)
        {
            continue;
        }

        const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(pSpellEntry->effectSoundId);

        if (!virtualPath)
        {
            continue;
        }

        m_audioSystem.preloadClip(*virtualPath);
    }
}

void GameAudioSystem::preloadArcomageUiSounds()
{
    if (m_pAssetFileSystem == nullptr)
    {
        return;
    }

    const std::array<SoundId, 11> arcomageSounds = {
        SoundId::ArcomageBricksDown,
        SoundId::ArcomageBricksUp,
        SoundId::ArcomageDamage,
        SoundId::ArcomageDeal,
        SoundId::ArcomageDefeat,
        SoundId::ArcomageQuarryUp,
        SoundId::ArcomageQuarryDown,
        SoundId::ArcomageShuffle,
        SoundId::ArcomageTowerUp,
        SoundId::ArcomageVictory,
        SoundId::ArcomageWallUp
    };

    for (SoundId soundId : arcomageSounds)
    {
        const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(static_cast<uint32_t>(soundId));

        if (!virtualPath)
        {
            continue;
        }

        const std::optional<std::vector<uint8_t>> soundBytes = m_pAssetFileSystem->readBinaryFile(*virtualPath);

        if (!soundBytes || soundBytes->empty())
        {
            continue;
        }

        std::vector<float> decodedSamples;

        if (!decodeAudioSamplesFromBytes(*soundBytes, decodedSamples) || decodedSamples.empty())
        {
            continue;
        }

        m_audioSystem.registerClip(*virtualPath, std::move(decodedSamples));
    }
}

bool GameAudioSystem::playSound(
    uint32_t soundId,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(soundId);

    if (!virtualPath)
    {
        return false;
    }

    return playResolvedSound(*virtualPath, group, position, false) != 0;
}

bool GameAudioSystem::playLoopingSound(
    uint32_t soundId,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(soundId);

    if (!virtualPath)
    {
        return false;
    }

    return playResolvedSound(*virtualPath, group, position, true) != 0;
}

uint64_t GameAudioSystem::playResolvedSound(
    const std::string &virtualPath,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position,
    bool loop)
{
    if (isExclusiveGroup(group))
    {
        const std::unordered_map<PlaybackGroup, uint64_t>::const_iterator activeIt = m_activeGroupInstanceIds.find(group);

        if (activeIt != m_activeGroupInstanceIds.end())
        {
            m_audioSystem.stopClip(activeIt->second);
        }
    }

    Engine::AudioSystem::PlaybackOptions options = {};
    options.positional = position.has_value();
    options.loop = loop;
    options.volume = playbackGroupVolume(group);

    if (position)
    {
        options.x = position->x;
        options.y = position->y;
        options.z = position->z;
    }

    const uint64_t instanceId = m_audioSystem.playClip(virtualPath, options);

    if (instanceId == 0)
    {
        return 0;
    }

    if (isExclusiveGroup(group))
    {
        m_activeGroupInstanceIds[group] = instanceId;
    }

    return instanceId;
}

float GameAudioSystem::targetMusicVolume() const
{
    return MusicVolume * m_musicVolume;
}

float GameAudioSystem::playbackGroupVolume(PlaybackGroup group) const
{
    switch (group)
    {
    case PlaybackGroup::Music:
        return targetMusicVolume();

    case PlaybackGroup::Speech:
    case PlaybackGroup::HouseSpeech:
        return m_voiceVolume;

    case PlaybackGroup::Ui:
    case PlaybackGroup::World:
    case PlaybackGroup::Walking:
    case PlaybackGroup::HouseDoor:
        return m_soundVolume;
    }

    return 1.0f;
}

bool GameAudioSystem::playCommonSound(
    SoundId soundId,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    return playSound(static_cast<uint32_t>(soundId), group, position);
}

bool GameAudioSystem::playCommonSoundNonResettable(
    SoundId soundId,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    const uint32_t soundKey = static_cast<uint32_t>(soundId);
    const std::unordered_map<uint32_t, uint64_t>::const_iterator activeIt =
        m_activeNonResettableSoundInstanceIds.find(soundKey);

    if (activeIt != m_activeNonResettableSoundInstanceIds.end() && m_audioSystem.isClipPlaying(activeIt->second))
    {
        return false;
    }

    m_activeNonResettableSoundInstanceIds.erase(soundKey);
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(soundKey);

    if (!virtualPath)
    {
        return false;
    }

    const uint64_t instanceId = playResolvedSound(*virtualPath, group, position, false);

    if (instanceId == 0)
    {
        return false;
    }

    m_activeNonResettableSoundInstanceIds[soundKey] = instanceId;
    return true;
}

bool GameAudioSystem::playSpeech(const Character &character, SpeechId speechId, uint32_t seed, uint32_t speakerKey)
{
    const SpeechReactionEntry *pReaction = m_speechReactionTable.find(speechId);

    if (pReaction == nullptr)
    {
        return false;
    }

    if (pReaction->commentKey.empty())
    {
        return false;
    }

    const std::optional<uint32_t> voiceId = resolveCharacterVoiceId(character);

    if (!voiceId)
    {
        return false;
    }

    const std::optional<uint32_t> soundId = m_soundCatalog.pickSpeechSoundId(
        *voiceId,
        pReaction->commentKey,
        seed == 0 ? SDL_GetTicks() : seed);

    if (!soundId)
    {
        return false;
    }

    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(*soundId);

    if (!virtualPath)
    {
        return false;
    }

    if (speakerKey != 0)
    {
        const std::unordered_map<uint32_t, uint64_t>::const_iterator activeIt = m_activeSpeechInstanceIds.find(speakerKey);

        if (activeIt != m_activeSpeechInstanceIds.end())
        {
            m_audioSystem.stopClip(activeIt->second);
        }
    }

    const uint64_t instanceId = playResolvedSound(*virtualPath, PlaybackGroup::Speech, std::nullopt, false);

    if (instanceId == 0)
    {
        return false;
    }

    if (speakerKey != 0)
    {
        m_activeSpeechInstanceIds[speakerKey] = instanceId;
    }

    return true;
}

const SpeechReactionEntry *GameAudioSystem::findSpeechReaction(SpeechId speechId) const
{
    return m_speechReactionTable.find(speechId);
}

bool GameAudioSystem::isExclusiveGroup(PlaybackGroup group)
{
    if (group == PlaybackGroup::Music)
    {
        return false;
    }

    return group == PlaybackGroup::Walking
        || group == PlaybackGroup::HouseDoor
        || group == PlaybackGroup::HouseSpeech;
}

void GameAudioSystem::stopGroup(PlaybackGroup group)
{
    const std::unordered_map<PlaybackGroup, uint64_t>::iterator activeIt = m_activeGroupInstanceIds.find(group);

    if (activeIt == m_activeGroupInstanceIds.end())
    {
        return;
    }

    m_audioSystem.stopClip(activeIt->second);
    m_activeGroupInstanceIds.erase(activeIt);
}

void GameAudioSystem::stopAllPlayback()
{
    m_audioSystem.stopAll();
    m_activeGroupInstanceIds.clear();
    m_activeSpeechInstanceIds.clear();
    m_activeNonResettableSoundInstanceIds.clear();
    m_activeMusicTrack = 0;
    m_pendingMusicTrack = 0;
    m_activeMusicInstanceId = 0;
    m_activeMusicVolume = 0.0f;
    m_musicFadeVelocity = 0.0f;
}

std::optional<uint32_t> GameAudioSystem::resolveCharacterVoiceId(const Character &character) const
{
    if (character.voiceId >= 0)
    {
        return static_cast<uint32_t>(character.voiceId);
    }

    if (m_pCharacterDollTable == nullptr)
    {
        return std::nullopt;
    }

    const CharacterDollEntry *pCharacterEntry = m_pCharacterDollTable->getCharacter(character.characterDataId);

    if (pCharacterEntry != nullptr)
    {
        return pCharacterEntry->defaultVoiceId;
    }

    return std::nullopt;
}

void GameAudioSystem::setBackgroundMusicTrack(int redbookTrack)
{
    const int normalizedTrack = std::max(redbookTrack, 0);

    if (normalizedTrack == 0)
    {
        stopBackgroundMusic();
        return;
    }

    if (m_activeMusicTrack == normalizedTrack && m_activeMusicInstanceId != 0)
    {
        m_pendingMusicTrack = 0;
        m_musicFadeVelocity = MusicFadeInSeconds > 0.0f ? (MusicVolume / MusicFadeInSeconds) : 0.0f;
        return;
    }

    if (m_activeMusicInstanceId == 0)
    {
        startBackgroundMusicTrack(normalizedTrack);
        return;
    }

    m_pendingMusicTrack = normalizedTrack;
    m_musicFadeVelocity = MusicFadeOutSeconds > 0.0f ? (-MusicVolume / MusicFadeOutSeconds) : -MusicVolume;
}

void GameAudioSystem::stopBackgroundMusic()
{
    m_pendingMusicTrack = 0;

    if (m_activeMusicInstanceId == 0)
    {
        m_activeMusicTrack = 0;
        m_activeMusicVolume = 0.0f;
        m_musicFadeVelocity = 0.0f;
        return;
    }

    m_musicFadeVelocity = MusicFadeOutSeconds > 0.0f ? (-MusicVolume / MusicFadeOutSeconds) : -MusicVolume;
}

void GameAudioSystem::stopBackgroundMusicImmediate()
{
    m_pendingMusicTrack = 0;

    if (m_activeMusicInstanceId != 0)
    {
        m_audioSystem.stopClip(m_activeMusicInstanceId);
    }

    m_activeMusicTrack = 0;
    m_activeMusicInstanceId = 0;
    m_activeMusicVolume = 0.0f;
    m_musicFadeVelocity = 0.0f;
}

int GameAudioSystem::currentBackgroundMusicTrack() const
{
    return m_activeMusicTrack;
}

bool GameAudioSystem::ensureBackgroundMusicTrackLoaded(int redbookTrack)
{
    if (m_pAssetFileSystem == nullptr || redbookTrack <= 0)
    {
        return false;
    }

    const auto loadedIt = m_loadedMusicClipKeys.find(redbookTrack);

    if (loadedIt != m_loadedMusicClipKeys.end())
    {
        return true;
    }

    const std::string virtualPath = "Music/" + std::to_string(redbookTrack) + ".mp3";
    const std::optional<std::vector<uint8_t>> musicBytes = m_pAssetFileSystem->readBinaryFile(virtualPath);

    if (!musicBytes || musicBytes->empty())
    {
        std::cerr << "GameAudioSystem: missing music track " << virtualPath << '\n';
        return false;
    }

    std::vector<float> decodedSamples;

    if (!decodeAudioSamplesFromBytes(*musicBytes, decodedSamples))
    {
        std::cerr << "GameAudioSystem: failed to decode music track " << virtualPath << '\n';
        return false;
    }

    const std::string clipKey = "music_track_" + std::to_string(redbookTrack);

    if (!m_audioSystem.registerClip(clipKey, std::move(decodedSamples)))
    {
        std::cerr << "GameAudioSystem: failed to register decoded music clip " << clipKey << '\n';
        return false;
    }

    m_loadedMusicClipKeys[redbookTrack] = clipKey;
    return true;
}

bool GameAudioSystem::startBackgroundMusicTrack(int redbookTrack)
{
    if (redbookTrack <= 0 || !ensureBackgroundMusicTrackLoaded(redbookTrack))
    {
        return false;
    }

    const std::string &clipKey = m_loadedMusicClipKeys[redbookTrack];
    Engine::AudioSystem::PlaybackOptions options = {};
    options.loop = true;
    options.volume = 0.0f;
    const uint64_t instanceId = m_audioSystem.playClip(clipKey, options);

    if (instanceId == 0)
    {
        return false;
    }

    m_activeMusicTrack = redbookTrack;
    m_activeMusicInstanceId = instanceId;
    m_activeMusicVolume = 0.0f;
    m_musicFadeVelocity = MusicFadeInSeconds > 0.0f ? (MusicVolume / MusicFadeInSeconds) : MusicVolume;
    m_audioSystem.setClipVolume(m_activeMusicInstanceId, m_activeMusicVolume);
    return true;
}
}
