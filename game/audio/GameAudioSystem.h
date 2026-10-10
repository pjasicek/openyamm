#pragma once

#include "engine/AudioSystem.h"
#include "game/tables/CharacterDollTable.h"
#include "game/party/Party.h"
#include "game/audio/SoundCatalog.h"
#include "game/audio/SoundIds.h"
#include "game/tables/SpellTable.h"
#include "game/party/SpeechIds.h"
#include "game/tables/SpeechReactionTable.h"
#include "game/tables/MergedBaseTables.h"

#include <array>
#include <functional>
#include <future>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class GameAudioSystem
{
public:
    enum class PlaybackGroup
    {
        Ui,
        World,
        Speech,
        Music,
        Walking,
        HouseDoor,
        HouseSpeech,
    };

    struct WorldPosition
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
    };

    bool initialize(
        const Engine::AssetFileSystem &assetFileSystem,
        const CharacterDollTable &characterDollTable,
        const MergedCharacterVoiceTable &characterVoiceTable);
    bool initializeMenuAudio(const Engine::AssetFileSystem &assetFileSystem);
    void bindGameplayTables(
        const CharacterDollTable &characterDollTable,
        const MergedCharacterVoiceTable &characterVoiceTable);
    void shutdown();
    void update(float listenerX, float listenerY, float listenerZ, float deltaSeconds, float listenerYawRadians = 0.0f);
    uint64_t playActorSound(size_t actorIndex, SoundRef sound, const WorldPosition &position, float pitch = 1.0f);
    void updateActorVoices(
        const WorldPosition &listenerFeet,
        const std::function<std::optional<WorldPosition>(size_t)> &sourcePosition);
    void stopActorVoices();
    bool isSoundInstancePlaying(uint64_t instanceId) const;
    void setBackgroundMusicTrack(int redbookTrack);
    void stopBackgroundMusic();
    void stopBackgroundMusicImmediate();
    void pauseBackgroundMusic();
    void resumeBackgroundMusic();
    int currentBackgroundMusicTrack() const;
    bool isBackgroundMusicPaused() const;
    void setSoundVolume(float volume);
    void setMusicVolume(float volume);
    void setVoiceVolume(float volume);
    float soundVolume() const;

    bool playSound(
        uint32_t soundId,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position = std::nullopt);
    bool playSound(
        SoundRef sound,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position = std::nullopt);
    bool playSoundByName(
        const std::string &soundName,
        PlaybackGroup group,
        SoundScope scope = SoundScope::World,
        const std::optional<WorldPosition> &position = std::nullopt);
    uint64_t playSoundInstance(
        uint32_t soundId,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position,
        bool loop);
    uint64_t playSoundInstance(
        SoundRef sound,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position,
        bool loop);
    uint64_t playSoundInstanceByName(
        const std::string &soundName,
        PlaybackGroup group,
        SoundScope scope,
        const std::optional<WorldPosition> &position,
        bool loop);
    uint64_t playAssetInstance(
        const std::string &virtualPath,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position,
        bool loop,
        float volume = 1.0f,
        float pitch = 1.0f,
        float innerRadius = -1.0f,
        float outerRadius = -1.0f);
    bool playLoopingSound(
        uint32_t soundId,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position = std::nullopt);
    bool playLoopingSound(
        SoundRef sound,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position = std::nullopt);
    bool playCommonSound(
        SoundId soundId,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position = std::nullopt);
    bool playCommonSoundNonResettable(
        SoundId soundId,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position = std::nullopt);
    bool preloadSound(SoundRef sound);
    bool preloadCommonSound(SoundId soundId);
    void beginMapSoundPreload();
    void endMapSoundPreload();
    Engine::AudioSystem::CacheStats cacheStats() const;
    bool playSpeech(const Character &character, SpeechId speechId, uint32_t seed = 0, uint32_t speakerKey = 0);
    const SpeechReactionEntry *findSpeechReaction(SpeechId speechId) const;
    void stopSoundInstance(uint64_t instanceId);
    // Volume of a playing instance relative to its group, so sound-volume changes still apply.
    void setSoundInstanceVolume(uint64_t instanceId, PlaybackGroup group, float volume);
    void setSoundInstancePosition(uint64_t instanceId, const WorldPosition &position);
    void stopGroup(PlaybackGroup group);
    void stopAllPlayback();

private:
    struct ActorVoice
    {
        size_t actorIndex = 0;
        SoundRef sound = {};
        uint64_t instanceId = 0;
        int volume = 0;
    };

    struct PendingMusicDecodeJob
    {
        int redbookTrack = 0;
        std::string clipKey;
        std::future<std::vector<float>> samplesFuture;
    };

    static bool isExclusiveGroup(PlaybackGroup group);
    bool initializeSoundCatalog(const Engine::AssetFileSystem &assetFileSystem);
    void preloadSpellEffectSounds(const SpellTable &spellTable);
    bool isBackgroundMusicTrackLoaded(int redbookTrack) const;
    bool queueBackgroundMusicTrackDecode(int redbookTrack);
    void updatePendingBackgroundMusicDecode();
    bool ensureBackgroundMusicTrackLoaded(int redbookTrack);
    bool startBackgroundMusicTrack(int redbookTrack);
    void clearPendingBackgroundMusicTrack(int redbookTrack);
    void evictUnusedMusicClips();
    float targetMusicVolume() const;
    float playbackGroupVolume(PlaybackGroup group) const;
    uint64_t playResolvedSound(
        const std::string &virtualPath,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position,
        bool loop,
        uint32_t soundId = 0,
        const char *pSource = "resolved");
    std::optional<uint32_t> resolveCharacterVoiceId(const Character &character) const;

    const CharacterDollTable *m_pCharacterDollTable = nullptr;
    const MergedCharacterVoiceTable *m_pCharacterVoiceTable = nullptr;
    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    SoundCatalog m_soundCatalog;
    SpeechReactionTable m_speechReactionTable;
    Engine::AudioSystem m_audioSystem;
    std::array<ActorVoice, 4> m_actorVoices = {};
    WorldPosition m_actorListenerFeet = {};
    std::unordered_map<PlaybackGroup, uint64_t> m_activeGroupInstanceIds;
    std::unordered_map<uint32_t, uint64_t> m_activeSpeechInstanceIds;
    std::unordered_map<uint32_t, uint64_t> m_activeNonResettableSoundInstanceIds;
    std::unordered_set<std::string> m_persistentPreloadedClipKeys;
    std::unordered_set<std::string> m_mapPreloadedClipKeys;
    std::unordered_set<std::string> m_previousMapPreloadedClipKeys;
    std::unordered_map<int, std::string> m_loadedMusicClipKeys;
    std::optional<PendingMusicDecodeJob> m_pendingMusicDecodeJob;
    int m_activeMusicTrack = 0;
    int m_pendingMusicTrack = 0;
    uint64_t m_activeMusicInstanceId = 0;
    float m_activeMusicVolume = 0.0f;
    float m_musicFadeVelocity = 0.0f;
    float m_pendingMusicDecodeDelaySeconds = 0.0f;
    bool m_backgroundMusicPaused = false;
    bool m_recordingMapSoundPreloads = false;
    float m_soundVolume = 1.0f;
    float m_musicVolume = 1.0f;
    float m_voiceVolume = 1.0f;
};
}
