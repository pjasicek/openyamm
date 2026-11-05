#include "game/audio/GameAudioSystem.h"
#include "game/audio/ActorAudioRules.h"
#include "game/audio/MusicStream.h"

#include "engine/TextTable.h"

#include <SDL3/SDL.h>

#include <array>
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <memory>
#include <string_view>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MusicVolume = 0.34f;
constexpr float MusicFadeInSeconds = 1.25f;
constexpr float MusicFadeOutSeconds = 0.6f;

bool audioTraceEnabled()
{
    static const bool enabled = []()
    {
        const char *pValue = std::getenv("OPENYAMM_AUDIO_TRACE");

        if (pValue == nullptr || pValue[0] == '\0')
        {
            return false;
        }

        return std::string_view(pValue) != "0";
    }();
    return enabled;
}

const char *playbackGroupName(GameAudioSystem::PlaybackGroup group)
{
    switch (group)
    {
    case GameAudioSystem::PlaybackGroup::Ui:
        return "Ui";

    case GameAudioSystem::PlaybackGroup::World:
        return "World";

    case GameAudioSystem::PlaybackGroup::Speech:
        return "Speech";

    case GameAudioSystem::PlaybackGroup::Music:
        return "Music";

    case GameAudioSystem::PlaybackGroup::Walking:
        return "Walking";

    case GameAudioSystem::PlaybackGroup::HouseDoor:
        return "HouseDoor";

    case GameAudioSystem::PlaybackGroup::HouseSpeech:
        return "HouseSpeech";
    }

    return "Unknown";
}

void logAudioTracePrefix(const char *pEvent, const char *pSource)
{
    std::cerr << "[AudioTrace t=" << SDL_GetTicks() << "] " << pEvent << " source=" << pSource;
}

void logAudioTracePosition(const std::optional<GameAudioSystem::WorldPosition> &position)
{
    if (!position)
    {
        std::cerr << " positional=0";
        return;
    }

    std::cerr << " positional=1 pos=(" << position->x << ',' << position->y << ',' << position->z << ')';
}

void logAudioTraceResolvedSound(
    const char *pEvent,
    const char *pSource,
    uint32_t soundId,
    const std::string &virtualPath,
    GameAudioSystem::PlaybackGroup group,
    const std::optional<GameAudioSystem::WorldPosition> &position,
    bool loop,
    uint64_t instanceId,
    const char *pResult)
{
    if (!audioTraceEnabled())
    {
        return;
    }

    logAudioTracePrefix(pEvent, pSource);
    std::cerr << " soundId=" << soundId
              << " group=" << playbackGroupName(group)
              << " loop=" << (loop ? 1 : 0)
              << " path=\"" << virtualPath << "\""
              << " result=" << pResult
              << " instance=" << instanceId;
    logAudioTracePosition(position);
    std::cerr << '\n';
}

void logAudioTraceUnresolvedSound(
    const char *pSource,
    uint32_t soundId,
    GameAudioSystem::PlaybackGroup group,
    const std::optional<GameAudioSystem::WorldPosition> &position,
    bool loop)
{
    if (!audioTraceEnabled())
    {
        return;
    }

    logAudioTracePrefix("request", pSource);
    std::cerr << " soundId=" << soundId
              << " group=" << playbackGroupName(group)
              << " loop=" << (loop ? 1 : 0)
              << " result=unresolved";
    logAudioTracePosition(position);
    std::cerr << '\n';
}

std::vector<std::vector<std::string>> rowsFromTextTable(const Engine::TextTable &textTable)
{
    std::vector<std::vector<std::string>> rows;
    rows.reserve(textTable.getRowCount());

    for (size_t rowIndex = 0; rowIndex < textTable.getRowCount(); ++rowIndex)
    {
        rows.push_back(textTable.getRow(rowIndex));
    }

    return rows;
}

}

bool GameAudioSystem::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const CharacterDollTable &characterDollTable,
    const MergedCharacterVoiceTable &characterVoiceTable)
{
    shutdown();
    if (!initializeSoundCatalog(assetFileSystem))
    {
        return false;
    }

    bindGameplayTables(characterDollTable, characterVoiceTable);
    return true;
}

bool GameAudioSystem::initializeMenuAudio(const Engine::AssetFileSystem &assetFileSystem)
{
    shutdown();
    return initializeSoundCatalog(assetFileSystem);
}

void GameAudioSystem::bindGameplayTables(
    const CharacterDollTable &characterDollTable,
    const MergedCharacterVoiceTable &characterVoiceTable)
{
    m_pCharacterDollTable = &characterDollTable;
    m_pCharacterVoiceTable = &characterVoiceTable;
}

bool GameAudioSystem::initializeSoundCatalog(const Engine::AssetFileSystem &assetFileSystem)
{
    m_pAssetFileSystem = &assetFileSystem;

    const std::optional<std::string> engineSoundCatalogText =
        assetFileSystem.readTextFile("engine/data_tables/sounds.txt");
    const std::optional<std::string> speechReactionText =
        assetFileSystem.readTextFile("engine/data_tables/character_speech_events.txt");

    if (!engineSoundCatalogText || !speechReactionText)
    {
        return false;
    }

    const std::optional<Engine::TextTable> parsedEngineSoundCatalog =
        Engine::TextTable::parseTabSeparated(*engineSoundCatalogText);
    const std::optional<Engine::TextTable> parsedSpeechReactions =
        Engine::TextTable::parseTabSeparated(*speechReactionText);

    if (!parsedEngineSoundCatalog || !parsedSpeechReactions)
    {
        return false;
    }

    const std::vector<std::vector<std::string>> engineSoundRows = rowsFromTextTable(*parsedEngineSoundCatalog);
    const std::vector<std::vector<std::string>> worldSoundRows;
    const std::vector<std::vector<std::string>> speechRows = rowsFromTextTable(*parsedSpeechReactions);

    std::string soundCatalogError;
    if (!m_soundCatalog.loadFromScopedRows(engineSoundRows, worldSoundRows, soundCatalogError)
        || !m_speechReactionTable.loadFromRows(speechRows)
        || !m_audioSystem.initialize(assetFileSystem))
    {
        if (!soundCatalogError.empty())
        {
            std::cerr << "Failed to load sound catalog: " << soundCatalogError << '\n';
        }

        shutdown();
        return false;
    }

    m_soundCatalog.initializeVirtualPathIndex(assetFileSystem);
    return true;
}

void GameAudioSystem::shutdown()
{
    m_actorVoices = {};
    m_actorListenerFeet = {};
    m_activeGroupInstanceIds.clear();
    m_activeSpeeches.clear();
    m_activeNonResettableSoundInstanceIds.clear();
    m_persistentPreloadedClipKeys.clear();
    m_mapPreloadedClipKeys.clear();
    m_previousMapPreloadedClipKeys.clear();
    m_loadedMusicTracks.clear();
    m_activeMusicTrack = 0;
    m_pendingMusicTrack = 0;
    m_activeMusicInstanceId = 0;
    m_activeMusicVolume = 0.0f;
    m_musicFadeVelocity = 0.0f;
    m_backgroundMusicPaused = false;
    m_recordingMapSoundPreloads = false;
    m_soundVolume = 1.0f;
    m_musicVolume = 1.0f;
    m_voiceVolume = 1.0f;
    m_audioSystem.shutdown();
    m_soundCatalog = {};
    m_speechReactionTable = {};
    m_pCharacterDollTable = nullptr;
    m_pCharacterVoiceTable = nullptr;
    m_pAssetFileSystem = nullptr;
}

void GameAudioSystem::update(
    float listenerX, float listenerY, float listenerZ, float deltaSeconds, float listenerYawRadians)
{
    const float musicTargetVolume = targetMusicVolume();

    if (m_activeMusicInstanceId != 0 && !m_audioSystem.isClipPlaying(m_activeMusicInstanceId))
    {
        m_activeMusicInstanceId = 0;
        m_activeMusicTrack = 0;
        m_activeMusicVolume = 0.0f;
        m_backgroundMusicPaused = false;
    }

    if (!m_backgroundMusicPaused && m_activeMusicInstanceId == 0 && m_pendingMusicTrack > 0)
    {
        const int nextTrack = m_pendingMusicTrack;
        m_pendingMusicTrack = 0;
        startBackgroundMusicTrack(nextTrack);
    }

    if (!m_backgroundMusicPaused && m_activeMusicInstanceId != 0 && m_musicFadeVelocity != 0.0f)
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
            m_backgroundMusicPaused = false;

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

    evictUnusedMusicClips();

    Engine::AudioSystem::ListenerState listenerState = {};
    listenerState.x = listenerX;
    listenerState.y = listenerY;
    listenerState.z = listenerZ;
    listenerState.yawRadians = listenerYawRadians;
    m_audioSystem.update(listenerState);
}

uint64_t GameAudioSystem::playActorSound(
    size_t actorIndex, SoundRef sound, const WorldPosition &position, float pitch)
{
    if (sound.id == 0)
    {
        return 0;
    }

    ActorVoice *pSlot = nullptr;
    for (ActorVoice &voice : m_actorVoices)
    {
        if (!m_audioSystem.isClipPlaying(voice.instanceId))
        {
            voice = {};
        }
        if (voice.instanceId != 0 && voice.actorIndex == actorIndex)
        {
            if (voice.sound.scope == sound.scope && voice.sound.id == sound.id)
            {
                return voice.instanceId;
            }
            m_audioSystem.stopClip(voice.instanceId);
            voice = {};
        }
        if (voice.instanceId == 0 && pSlot == nullptr)
        {
            pSlot = &voice;
        }
    }

    const int volume = actorVoiceVolume(
        position.x - m_actorListenerFeet.x,
        position.y - m_actorListenerFeet.y,
        position.z - m_actorListenerFeet.z);
    if (volume == 0 || m_soundVolume <= 0.0f)
    {
        return 0;
    }

    if (pSlot == nullptr)
    {
        for (ActorVoice &voice : m_actorVoices)
        {
            if (voice.volume < volume && (pSlot == nullptr || voice.volume < pSlot->volume))
            {
                pSlot = &voice;
            }
        }
    }
    if (pSlot == nullptr)
    {
        return 0;
    }

    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(sound);
    if (!virtualPath)
    {
        return 0;
    }

    Engine::AudioSystem::PlaybackOptions options = {};
    options.positional = true;
    options.attenuate = false;
    options.volume = m_soundVolume * float(volume) / 127.0f;
    options.pitch = pitch;
    options.x = position.x;
    options.y = position.y;
    options.z = position.z;
    const uint64_t instanceId = m_audioSystem.playClip(*virtualPath, options);
    if (instanceId == 0)
    {
        return 0;
    }

    m_audioSystem.stopClip(pSlot->instanceId);
    *pSlot = {actorIndex, sound, instanceId, volume};
    return instanceId;
}

void GameAudioSystem::updateActorVoices(
    const WorldPosition &listenerFeet,
    const std::function<std::optional<WorldPosition>(size_t)> &sourcePosition)
{
    m_actorListenerFeet = listenerFeet;
    for (ActorVoice &voice : m_actorVoices)
    {
        if (!m_audioSystem.isClipPlaying(voice.instanceId))
        {
            voice = {};
            continue;
        }

        const std::optional<WorldPosition> position = sourcePosition(voice.actorIndex);
        voice.volume = position ? actorVoiceVolume(
            position->x - listenerFeet.x, position->y - listenerFeet.y, position->z - listenerFeet.z) : 0;
        if (voice.volume == 0)
        {
            m_audioSystem.stopClip(voice.instanceId);
            voice = {};
            continue;
        }

        m_audioSystem.setClipPosition(voice.instanceId, position->x, position->y, position->z);
        m_audioSystem.setClipVolume(voice.instanceId, m_soundVolume * float(voice.volume) / 127.0f);
    }
}

void GameAudioSystem::stopActorVoices()
{
    for (ActorVoice &voice : m_actorVoices)
    {
        m_audioSystem.stopClip(voice.instanceId);
        voice = {};
    }
}

bool GameAudioSystem::isSoundInstancePlaying(uint64_t instanceId) const
{
    return m_audioSystem.isClipPlaying(instanceId);
}

bool GameAudioSystem::isSpeechPlaying(uint32_t speakerKey, SpeechId speechId) const
{
    const std::unordered_map<uint32_t, ActiveSpeech>::const_iterator activeIt = m_activeSpeeches.find(speakerKey);

    return activeIt != m_activeSpeeches.end()
        && activeIt->second.speechId == speechId
        && m_audioSystem.isClipPlaying(activeIt->second.instanceId);
}

void GameAudioSystem::setSoundVolume(float volume)
{
    m_soundVolume = std::clamp(volume, 0.0f, 1.0f);
}

float GameAudioSystem::soundVolume() const
{
    return m_soundVolume;
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

bool GameAudioSystem::preloadSound(SoundRef sound)
{
    if (sound.id == 0)
    {
        return false;
    }

    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(sound);

    if (!virtualPath)
    {
        return false;
    }

    if (!m_audioSystem.preloadClip(*virtualPath))
    {
        return false;
    }

    if (m_recordingMapSoundPreloads)
    {
        m_mapPreloadedClipKeys.insert(*virtualPath);
    }
    else
    {
        m_persistentPreloadedClipKeys.insert(*virtualPath);
    }

    return true;
}

bool GameAudioSystem::preloadCommonSound(SoundId soundId)
{
    return preloadSound(engineSound(static_cast<uint32_t>(soundId)));
}

void GameAudioSystem::beginMapSoundPreload()
{
    stopActorVoices();
    m_previousMapPreloadedClipKeys = std::move(m_mapPreloadedClipKeys);
    m_mapPreloadedClipKeys.clear();
    m_recordingMapSoundPreloads = true;
}

void GameAudioSystem::endMapSoundPreload()
{
    m_recordingMapSoundPreloads = false;

    for (const std::string &clipKey : m_previousMapPreloadedClipKeys)
    {
        if (!m_mapPreloadedClipKeys.contains(clipKey) && !m_persistentPreloadedClipKeys.contains(clipKey))
        {
            m_audioSystem.releaseClip(clipKey);
        }
    }

    m_previousMapPreloadedClipKeys.clear();
}

Engine::AudioSystem::CacheStats GameAudioSystem::cacheStats() const
{
    return m_audioSystem.cacheStats();
}

void GameAudioSystem::preloadSpellEffectSounds(const SpellTable &spellTable)
{
    std::unordered_set<int> preloadedSoundIds;

    for (const SpellEntry &spellEntry : spellTable.entries())
    {
        if (spellEntry.effectSoundId <= 0 || !preloadedSoundIds.insert(spellEntry.effectSoundId).second)
        {
            continue;
        }

        preloadSound(engineSound(static_cast<uint32_t>(spellEntry.effectSoundId)));
    }
}

bool GameAudioSystem::playSound(
    uint32_t soundId,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    return playSound(engineSound(soundId), group, position);
}

bool GameAudioSystem::playSound(
    SoundRef sound,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(sound);

    if (!virtualPath)
    {
        logAudioTraceUnresolvedSound("playSound", sound.id, group, position, false);
        return false;
    }

    return playResolvedSound(*virtualPath, group, position, false, sound.id, "playSound") != 0;
}

bool GameAudioSystem::playSoundByName(
    const std::string &soundName,
    PlaybackGroup group,
    SoundScope scope,
    const std::optional<WorldPosition> &position)
{
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPathByName(scope, soundName);
    if (!virtualPath)
    {
        if (audioTraceEnabled())
        {
            logAudioTracePrefix("request", "playSoundByName");
            std::cerr << " name=\"" << soundName << "\" group=" << playbackGroupName(group)
                      << " loop=0 result=unresolved";
            logAudioTracePosition(position);
            std::cerr << '\n';
        }
        return false;
    }

    return playResolvedSound(*virtualPath, group, position, false, 0, "playSoundByName") != 0;
}

uint64_t GameAudioSystem::playSoundInstance(
    uint32_t soundId,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position,
    bool loop)
{
    return playSoundInstance(engineSound(soundId), group, position, loop);
}

uint64_t GameAudioSystem::playSoundInstance(
    SoundRef sound,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position,
    bool loop)
{
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(sound);

    if (!virtualPath)
    {
        logAudioTraceUnresolvedSound("playSoundInstance", sound.id, group, position, loop);
        return 0;
    }

    return playResolvedSound(*virtualPath, group, position, loop, sound.id, "playSoundInstance");
}

uint64_t GameAudioSystem::playSoundInstanceByName(
    const std::string &soundName,
    PlaybackGroup group,
    SoundScope scope,
    const std::optional<WorldPosition> &position,
    bool loop)
{
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPathByName(scope, soundName);

    if (!virtualPath)
    {
        if (audioTraceEnabled())
        {
            logAudioTracePrefix("request", "playSoundInstanceByName");
            std::cerr << " name=\"" << soundName << "\" group=" << playbackGroupName(group)
                      << " loop=" << (loop ? 1 : 0) << " result=unresolved";
            logAudioTracePosition(position);
            std::cerr << '\n';
        }

        return 0;
    }

    return playResolvedSound(*virtualPath, group, position, loop, 0, "playSoundInstanceByName");
}

std::optional<std::string> GameAudioSystem::soundVirtualPathByName(
    SoundScope scope,
    const std::string &soundName) const
{
    return m_soundCatalog.buildVirtualPathByName(scope, soundName);
}

uint64_t GameAudioSystem::playAssetInstance(
    const std::string &virtualPath,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position,
    bool loop,
    float volume,
    float pitch,
    float innerRadius,
    float outerRadius)
{
    Engine::AudioSystem::PlaybackOptions options = {};
    options.volume = playbackGroupVolume(group) * volume;
    options.positional = position.has_value();
    options.loop = loop;
    options.pitch = pitch;
    options.innerRadius = innerRadius;
    options.outerRadius = outerRadius;
    if (position)
    {
        options.x = position->x;
        options.y = position->y;
        options.z = position->z;
    }
    return m_audioSystem.playClip(virtualPath, options);
}

bool GameAudioSystem::playLoopingSound(
    uint32_t soundId,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    return playLoopingSound(engineSound(soundId), group, position);
}

bool GameAudioSystem::playLoopingSound(
    SoundRef sound,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(sound);

    if (!virtualPath)
    {
        logAudioTraceUnresolvedSound("playLoopingSound", sound.id, group, position, true);
        return false;
    }

    return playResolvedSound(*virtualPath, group, position, true, sound.id, "playLoopingSound") != 0;
}

uint64_t GameAudioSystem::playResolvedSound(
    const std::string &virtualPath,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position,
    bool loop,
    uint32_t soundId,
    const char *pSource)
{
    if (isExclusiveGroup(group))
    {
        const std::unordered_map<PlaybackGroup, uint64_t>::const_iterator activeIt =
            m_activeGroupInstanceIds.find(group);

        if (activeIt != m_activeGroupInstanceIds.end())
        {
            if (audioTraceEnabled())
            {
                logAudioTracePrefix("stop-exclusive", pSource);
                std::cerr << " soundId=" << soundId
                          << " group=" << playbackGroupName(group)
                          << " stoppedInstance=" << activeIt->second << '\n';
            }

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
        logAudioTraceResolvedSound(
            "request",
            pSource,
            soundId,
            virtualPath,
            group,
            position,
            loop,
            instanceId,
            "failed");
        return 0;
    }

    logAudioTraceResolvedSound(
        "request",
        pSource,
        soundId,
        virtualPath,
        group,
        position,
        loop,
        instanceId,
        "queued");

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
        if (audioTraceEnabled())
        {
            logAudioTracePrefix("request", "playCommonSoundNonResettable");
            std::cerr << " soundId=" << soundKey
                      << " group=" << playbackGroupName(group)
                      << " loop=0 result=skipped-active instance=" << activeIt->second;
            logAudioTracePosition(position);
            std::cerr << '\n';
        }

        return false;
    }

    m_activeNonResettableSoundInstanceIds.erase(soundKey);
    const std::optional<std::string> virtualPath = m_soundCatalog.buildVirtualPath(soundKey);

    if (!virtualPath)
    {
        logAudioTraceUnresolvedSound("playCommonSoundNonResettable", soundKey, group, position, false);
        return false;
    }

    const uint64_t instanceId =
        playResolvedSound(*virtualPath, group, position, false, soundKey, "playCommonSoundNonResettable");

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

    if (pReaction->soundTypes.empty() || m_pCharacterVoiceTable == nullptr || m_pAssetFileSystem == nullptr)
    {
        return false;
    }

    const std::optional<uint32_t> voiceId = resolveCharacterVoiceId(character);

    if (!voiceId)
    {
        return false;
    }

    const std::vector<uint32_t> soundIds = m_pCharacterVoiceTable->soundIdsForTypes(*voiceId, pReaction->soundTypes);

    if (soundIds.empty())
    {
        return false;
    }

    const uint32_t pickSeed = seed == 0 ? SDL_GetTicks() : seed;
    std::optional<uint32_t> selectedSoundId;
    std::optional<std::string> selectedVirtualPath;

    for (size_t offset = 0; offset < soundIds.size(); ++offset)
    {
        const uint32_t candidateSoundId = soundIds[(pickSeed + offset) % soundIds.size()];
        const std::optional<std::string> candidateVirtualPath = m_soundCatalog.buildVirtualPath(candidateSoundId);

        if (!candidateVirtualPath || !m_pAssetFileSystem->exists(*candidateVirtualPath))
        {
            continue;
        }

        selectedSoundId = candidateSoundId;
        selectedVirtualPath = candidateVirtualPath;
        break;
    }

    if (!selectedSoundId || !selectedVirtualPath)
    {
        logAudioTraceUnresolvedSound("playSpeech", soundIds.front(), PlaybackGroup::Speech, std::nullopt, false);
        return false;
    }

    if (speakerKey != 0)
    {
        const std::unordered_map<uint32_t, ActiveSpeech>::const_iterator activeIt =
            m_activeSpeeches.find(speakerKey);

        if (activeIt != m_activeSpeeches.end())
        {
            if (audioTraceEnabled())
            {
                logAudioTracePrefix("stop-speech", "playSpeech");
                std::cerr << " soundId=" << *selectedSoundId
                          << " speechId=" << static_cast<uint32_t>(speechId)
                          << " speakerKey=" << speakerKey
                          << " stoppedInstance=" << activeIt->second.instanceId << '\n';
            }

            m_audioSystem.stopClip(activeIt->second.instanceId);
        }
    }

    const uint64_t instanceId =
        playResolvedSound(
            *selectedVirtualPath,
            PlaybackGroup::Speech,
            std::nullopt,
            false,
            *selectedSoundId,
            "playSpeech");

    if (instanceId == 0)
    {
        return false;
    }

    if (speakerKey != 0)
    {
        m_activeSpeeches[speakerKey] = ActiveSpeech{instanceId, speechId};
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

void GameAudioSystem::setSoundInstanceVolume(uint64_t instanceId, PlaybackGroup group, float volume)
{
    m_audioSystem.setClipVolume(instanceId, playbackGroupVolume(group) * volume);
}

void GameAudioSystem::stopSoundInstance(uint64_t instanceId)
{
    if (instanceId == 0)
    {
        return;
    }

    if (audioTraceEnabled())
    {
        logAudioTracePrefix("stop-instance", "stopSoundInstance");
        std::cerr << " instance=" << instanceId << '\n';
    }

    m_audioSystem.stopClip(instanceId);
}

void GameAudioSystem::setSoundInstancePosition(uint64_t instanceId, const WorldPosition &position)
{
    if (instanceId != 0)
    {
        m_audioSystem.setClipPosition(instanceId, position.x, position.y, position.z);
    }
}

void GameAudioSystem::stopGroup(PlaybackGroup group)
{
    const std::unordered_map<PlaybackGroup, uint64_t>::iterator activeIt = m_activeGroupInstanceIds.find(group);

    if (activeIt == m_activeGroupInstanceIds.end())
    {
        return;
    }

    if (audioTraceEnabled())
    {
        logAudioTracePrefix("stop-group", "stopGroup");
        std::cerr << " group=" << playbackGroupName(group)
                  << " instance=" << activeIt->second << '\n';
    }

    m_audioSystem.stopClip(activeIt->second);
    m_activeGroupInstanceIds.erase(activeIt);
}

void GameAudioSystem::stopAllPlayback()
{
    if (audioTraceEnabled())
    {
        logAudioTracePrefix("stop-all", "stopAllPlayback");
        std::cerr << " activeMusicTrack=" << m_activeMusicTrack
                  << " activeMusicInstance=" << m_activeMusicInstanceId
                  << " exclusiveGroups=" << m_activeGroupInstanceIds.size()
                  << " speechInstances=" << m_activeSpeeches.size() << '\n';
    }

    m_audioSystem.stopAll();
    m_actorVoices = {};
    m_activeGroupInstanceIds.clear();
    m_activeSpeeches.clear();
    m_activeNonResettableSoundInstanceIds.clear();
    m_activeMusicTrack = 0;
    m_pendingMusicTrack = 0;
    m_activeMusicInstanceId = 0;
    m_ambienceInstanceId = 0;
    m_activeMusicVolume = 0.0f;
    m_musicFadeVelocity = 0.0f;
    m_backgroundMusicPaused = false;
    evictUnusedMusicClips();
}

void GameAudioSystem::setAmbience(const std::string &soundName, float volume)
{
    if (m_ambienceInstanceId != 0)
    {
        stopSoundInstance(m_ambienceInstanceId);
        m_ambienceInstanceId = 0;
    }

    if (soundName.empty())
    {
        return;
    }

    m_ambienceInstanceId = playSoundInstanceByName(soundName, PlaybackGroup::World, SoundScope::World, std::nullopt,
        true);

    if (m_ambienceInstanceId != 0)
    {
        setSoundInstanceVolume(m_ambienceInstanceId, PlaybackGroup::World, std::clamp(volume, 0.0f, 1.0f));
    }
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

    if (audioTraceEnabled())
    {
        logAudioTracePrefix("music-set", "setBackgroundMusicTrack");
        std::cerr << " track=" << normalizedTrack
                  << " activeTrack=" << m_activeMusicTrack
                  << " activeInstance=" << m_activeMusicInstanceId
                  << " paused=" << (m_backgroundMusicPaused ? 1 : 0) << '\n';
    }

    if (normalizedTrack == 0)
    {
        stopBackgroundMusic();
        return;
    }

    if (m_backgroundMusicPaused)
    {
        m_pendingMusicTrack =
            m_activeMusicTrack == normalizedTrack && m_activeMusicInstanceId != 0 ? 0 : normalizedTrack;
        return;
    }

    if (m_activeMusicTrack == normalizedTrack && m_activeMusicInstanceId != 0)
    {
        m_pendingMusicTrack = 0;
        m_musicFadeVelocity = MusicFadeInSeconds > 0.0f ? (MusicVolume / MusicFadeInSeconds) : 0.0f;
        m_backgroundMusicPaused = false;
        return;
    }

    if (m_activeMusicInstanceId == 0)
    {
        m_pendingMusicTrack = 0;
        startBackgroundMusicTrack(normalizedTrack);
        return;
    }

    m_pendingMusicTrack = normalizedTrack;
    m_musicFadeVelocity = MusicFadeOutSeconds > 0.0f ? (-MusicVolume / MusicFadeOutSeconds) : -MusicVolume;
}

void GameAudioSystem::stopBackgroundMusic()
{
    if (audioTraceEnabled())
    {
        logAudioTracePrefix("music-stop", "stopBackgroundMusic");
        std::cerr << " activeTrack=" << m_activeMusicTrack
                  << " activeInstance=" << m_activeMusicInstanceId << '\n';
    }

    m_pendingMusicTrack = 0;
    m_backgroundMusicPaused = false;

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
    if (audioTraceEnabled())
    {
        logAudioTracePrefix("music-stop-immediate", "stopBackgroundMusicImmediate");
        std::cerr << " activeTrack=" << m_activeMusicTrack
                  << " activeInstance=" << m_activeMusicInstanceId << '\n';
    }

    m_pendingMusicTrack = 0;
    m_backgroundMusicPaused = false;

    if (m_activeMusicInstanceId != 0)
    {
        m_audioSystem.stopClip(m_activeMusicInstanceId);
        m_audioSystem.clearQueuedAudio();
    }

    m_activeMusicTrack = 0;
    m_activeMusicInstanceId = 0;
    m_activeMusicVolume = 0.0f;
    m_musicFadeVelocity = 0.0f;
    evictUnusedMusicClips();
}

void GameAudioSystem::pauseBackgroundMusic()
{
    if (m_backgroundMusicPaused)
    {
        return;
    }

    if (audioTraceEnabled())
    {
        logAudioTracePrefix("music-pause", "pauseBackgroundMusic");
        std::cerr << " activeTrack=" << m_activeMusicTrack
                  << " activeInstance=" << m_activeMusicInstanceId << '\n';
    }

    m_backgroundMusicPaused = true;

    if (m_activeMusicInstanceId != 0)
    {
        m_audioSystem.pauseClip(m_activeMusicInstanceId);
    }
}

void GameAudioSystem::resumeBackgroundMusic()
{
    if (!m_backgroundMusicPaused)
    {
        return;
    }

    if (audioTraceEnabled())
    {
        logAudioTracePrefix("music-resume", "resumeBackgroundMusic");
        std::cerr << " activeTrack=" << m_activeMusicTrack
                  << " activeInstance=" << m_activeMusicInstanceId << '\n';
    }

    m_backgroundMusicPaused = false;

    if (m_activeMusicInstanceId != 0)
    {
        m_audioSystem.resumeClip(m_activeMusicInstanceId);
    }
}

int GameAudioSystem::currentBackgroundMusicTrack() const
{
    return m_activeMusicTrack;
}

bool GameAudioSystem::isBackgroundMusicPaused() const
{
    return m_backgroundMusicPaused;
}

std::shared_ptr<const std::vector<uint8_t>> GameAudioSystem::loadBackgroundMusicTrack(int redbookTrack)
{
    if (m_pAssetFileSystem == nullptr || redbookTrack <= 0)
    {
        return nullptr;
    }

    const auto loadedIt = m_loadedMusicTracks.find(redbookTrack);

    if (loadedIt != m_loadedMusicTracks.end())
    {
        return loadedIt->second;
    }

    const std::string virtualPath = "Music/" + std::to_string(redbookTrack) + ".mp3";
    std::optional<std::vector<uint8_t>> musicBytes = m_pAssetFileSystem->readBinaryFile(virtualPath);

    if (!musicBytes || musicBytes->empty())
    {
        std::cerr << "GameAudioSystem: missing music track " << virtualPath << '\n';
        return nullptr;
    }

    std::shared_ptr<const std::vector<uint8_t>> pTrack =
        std::make_shared<const std::vector<uint8_t>>(std::move(*musicBytes));
    m_loadedMusicTracks[redbookTrack] = pTrack;
    return pTrack;
}

bool GameAudioSystem::startBackgroundMusicTrack(int redbookTrack)
{
    const std::shared_ptr<const std::vector<uint8_t>> pTrack = loadBackgroundMusicTrack(redbookTrack);

    if (pTrack == nullptr)
    {
        return false;
    }

    const std::string clipKey = "Music/" + std::to_string(redbookTrack) + ".mp3";
    Engine::AudioSystem::PlaybackOptions options = {};
    options.volume = 0.0f;
    const uint64_t instanceId = m_audioSystem.playStream(std::make_shared<MusicStream>(pTrack), options);

    if (instanceId == 0)
    {
        if (audioTraceEnabled())
        {
            logAudioTracePrefix("music-start", "startBackgroundMusicTrack");
            std::cerr << " track=" << redbookTrack
                      << " path=\"" << clipKey << "\" result=failed instance=0\n";
        }

        return false;
    }

    if (audioTraceEnabled())
    {
        logAudioTracePrefix("music-start", "startBackgroundMusicTrack");
        std::cerr << " track=" << redbookTrack
                  << " path=\"" << clipKey << "\" result=queued instance=" << instanceId << '\n';
    }

    m_activeMusicTrack = redbookTrack;
    m_activeMusicInstanceId = instanceId;
    m_activeMusicVolume = 0.0f;
    m_musicFadeVelocity = MusicFadeInSeconds > 0.0f ? (MusicVolume / MusicFadeInSeconds) : MusicVolume;
    m_backgroundMusicPaused = false;
    m_audioSystem.setClipVolume(m_activeMusicInstanceId, m_activeMusicVolume);
    evictUnusedMusicClips();
    return true;
}

void GameAudioSystem::evictUnusedMusicClips()
{
    for (auto iterator = m_loadedMusicTracks.begin(); iterator != m_loadedMusicTracks.end();)
    {
        const int track = iterator->first;

        if (track == m_activeMusicTrack || track == m_pendingMusicTrack)
        {
            ++iterator;
            continue;
        }

        iterator = m_loadedMusicTracks.erase(iterator);
    }
}
}
