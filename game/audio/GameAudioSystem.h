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

#include <future>
#include <optional>
#include <string>
#include <unordered_map>
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
        const MergedCharacterVoiceTable &characterVoiceTable,
        const SpellTable &spellTable);
    bool initializeMenuAudio(const Engine::AssetFileSystem &assetFileSystem);
    void bindGameplayTables(
        const CharacterDollTable &characterDollTable,
        const MergedCharacterVoiceTable &characterVoiceTable,
        const SpellTable &spellTable);
    void shutdown();
    void update(float listenerX, float listenerY, float listenerZ, float deltaSeconds);
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
    bool playSpeech(const Character &character, SpeechId speechId, uint32_t seed = 0, uint32_t speakerKey = 0);
    const SpeechReactionEntry *findSpeechReaction(SpeechId speechId) const;
    void stopSoundInstance(uint64_t instanceId);
    void stopGroup(PlaybackGroup group);
    void stopAllPlayback();

private:
    struct PendingMusicDecodeJob
    {
        int redbookTrack = 0;
        std::string clipKey;
        std::future<std::vector<float>> samplesFuture;
    };

    static bool isExclusiveGroup(PlaybackGroup group);
    bool initializeSoundCatalog(const Engine::AssetFileSystem &assetFileSystem);
    void preloadSpellEffectSounds(const SpellTable &spellTable);
    void preloadArcomageUiSounds();
    bool isBackgroundMusicTrackLoaded(int redbookTrack) const;
    bool queueBackgroundMusicTrackDecode(int redbookTrack);
    void updatePendingBackgroundMusicDecode();
    bool ensureBackgroundMusicTrackLoaded(int redbookTrack);
    bool startBackgroundMusicTrack(int redbookTrack);
    void clearPendingBackgroundMusicTrack(int redbookTrack);
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
    std::unordered_map<PlaybackGroup, uint64_t> m_activeGroupInstanceIds;
    std::unordered_map<uint32_t, uint64_t> m_activeSpeechInstanceIds;
    std::unordered_map<uint32_t, uint64_t> m_activeNonResettableSoundInstanceIds;
    std::unordered_map<int, std::string> m_loadedMusicClipKeys;
    std::optional<PendingMusicDecodeJob> m_pendingMusicDecodeJob;
    int m_activeMusicTrack = 0;
    int m_pendingMusicTrack = 0;
    uint64_t m_activeMusicInstanceId = 0;
    float m_activeMusicVolume = 0.0f;
    float m_musicFadeVelocity = 0.0f;
    float m_pendingMusicDecodeDelaySeconds = 0.0f;
    bool m_backgroundMusicPaused = false;
    float m_soundVolume = 1.0f;
    float m_musicVolume = 1.0f;
    float m_voiceVolume = 1.0f;
};
}
