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
    // The actors whose sounds come from their 3D model's clips (WorldFxSystem::actorPlaysClipSounds): playActorSound
    // drops their descriptor sounds, which the clips replace. Keyed by the world presenting them (pOwner): clearing
    // with another owner keeps the current one.
    void setActorClipSoundOwner(const void *pOwner, std::function<bool(size_t)> owner);
    void clearActorClipSoundOwner(const void *pOwner);
    // A sound of an actor's clip (actors' actor_sounds.yml), by name in the world's audio, heard within outerRadius.
    uint64_t playActorClipSound(
        const std::string &soundName,
        const WorldPosition &position,
        float volume,
        float innerRadius,
        float outerRadius);
    void updateActorVoices(
        const WorldPosition &listenerFeet,
        const std::function<std::optional<WorldPosition>(size_t)> &sourcePosition);
    void stopActorVoices();
    bool isSoundInstancePlaying(uint64_t instanceId) const;
    // The asset path of a sound by its name in the scope (a world's audio folder for SoundScope::World).
    std::optional<std::string> soundVirtualPathByName(SoundScope scope, const std::string &soundName) const;
    // True while the speaker's latest speech line is this speech and has not finished.
    bool isSpeechPlaying(uint32_t speakerKey, SpeechId speechId) const;
    // repeatGapSeconds: the silence between two plays of the track (world.yml music; 0 loops it seamlessly).
    void setBackgroundMusicTrack(int redbookTrack, float repeatGapSeconds = 0.0f);
    // Battle music (world.yml music battleTrack; MM9): while active, the track plays in place of the map's, which waits
    // paused; once inactive it fades out over fadeSeconds and the map's track resumes where it stopped, fading in as
    // fast. Called every frame; track 0 or inactive with no battle music playing does nothing.
    void setBattleMusic(int track, bool active, float fadeSeconds);
    bool isBattleMusicPlaying() const;
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
        float outerRadius = -1.0f,
        bool pan = true);
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
    // A map's ambience bed (world.yml ambience): one looping sound by name under the music, in the World group at
    // volume (0-1); another name replaces it, an empty one stops it. Restarted on every call with a name.
    void setAmbience(const std::string &soundName, float volume);
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

    static bool isExclusiveGroup(PlaybackGroup group);
    bool initializeSoundCatalog(const Engine::AssetFileSystem &assetFileSystem);
    void preloadSpellEffectSounds(const SpellTable &spellTable);
    // The encoded track, read once and kept while it is active or pending; MusicStream decodes it as it plays.
    std::shared_ptr<const std::vector<uint8_t>> loadBackgroundMusicTrack(int redbookTrack);
    bool startBackgroundMusicTrack(int redbookTrack);
    void updateBattleMusic(float deltaSeconds);
    void stopBattleMusicImmediate();
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
    const void *m_pActorClipSoundOwnerKey = nullptr;
    std::function<bool(size_t)> m_actorClipSoundOwner;
    SoundCatalog m_soundCatalog;
    SpeechReactionTable m_speechReactionTable;
    Engine::AudioSystem m_audioSystem;
    std::array<ActorVoice, 4> m_actorVoices = {};
    WorldPosition m_actorListenerFeet = {};
    std::unordered_map<PlaybackGroup, uint64_t> m_activeGroupInstanceIds;
    struct ActiveSpeech
    {
        uint64_t instanceId = 0;
        SpeechId speechId = SpeechId::None;
    };

    std::unordered_map<uint32_t, ActiveSpeech> m_activeSpeeches;
    std::unordered_map<uint32_t, uint64_t> m_activeNonResettableSoundInstanceIds;
    std::unordered_set<std::string> m_persistentPreloadedClipKeys;
    std::unordered_set<std::string> m_mapPreloadedClipKeys;
    std::unordered_set<std::string> m_previousMapPreloadedClipKeys;
    std::unordered_map<int, std::shared_ptr<const std::vector<uint8_t>>> m_loadedMusicTracks;
    int m_activeMusicTrack = 0;
    int m_pendingMusicTrack = 0;
    float m_musicRepeatGapSeconds = 0.0f;   // of the latest setBackgroundMusicTrack: tracks start with it
    // Battle music over the map's track (setBattleMusic): the map's instance stays paused under it (suspended).
    int m_battleMusicTrack = 0;
    uint64_t m_battleMusicInstanceId = 0;
    float m_battleMusicVolume = 0.0f;
    float m_battleMusicFadeVelocity = 0.0f;
    float m_battleMusicFadeSeconds = 2.5f;
    bool m_mapMusicSuspended = false;
    uint64_t m_activeMusicInstanceId = 0;
    uint64_t m_ambienceInstanceId = 0;
    float m_activeMusicVolume = 0.0f;
    float m_musicFadeVelocity = 0.0f;
    bool m_backgroundMusicPaused = false;
    bool m_recordingMapSoundPreloads = false;
    float m_soundVolume = 1.0f;
    float m_musicVolume = 1.0f;
    float m_voiceVolume = 1.0f;
};
}
