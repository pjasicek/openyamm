#pragma once

#include "engine/AudioSystem.h"
#include "game/tables/CharacterDollTable.h"
#include "game/party/Party.h"
#include "game/audio/SoundCatalog.h"
#include "game/audio/SoundIds.h"
#include "game/tables/SpellTable.h"
#include "game/party/SpeechIds.h"
#include "game/tables/SpeechReactionTable.h"

#include <optional>
#include <string>
#include <unordered_map>

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
        const SpellTable &spellTable);
    void shutdown();
    void update(float listenerX, float listenerY, float listenerZ, float deltaSeconds);
    void setBackgroundMusicTrack(int redbookTrack);
    void stopBackgroundMusic();
    int currentBackgroundMusicTrack() const;

    bool playSound(
        uint32_t soundId,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position = std::nullopt);
    bool playLoopingSound(
        uint32_t soundId,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position = std::nullopt);
    bool playCommonSound(SoundId soundId, PlaybackGroup group, const std::optional<WorldPosition> &position = std::nullopt);
    bool playSpeech(const Character &character, SpeechId speechId, uint32_t seed = 0, uint32_t speakerKey = 0);
    const SpeechReactionEntry *findSpeechReaction(SpeechId speechId) const;
    void stopGroup(PlaybackGroup group);

private:
    static bool isExclusiveGroup(PlaybackGroup group);
    void preloadSpellBuffSounds(const SpellTable &spellTable);
    void preloadArcomageUiSounds();
    bool ensureBackgroundMusicTrackLoaded(int redbookTrack);
    bool startBackgroundMusicTrack(int redbookTrack);
    uint64_t playResolvedSound(
        const std::string &virtualPath,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position,
        bool loop);
    std::optional<uint32_t> resolveCharacterVoiceId(const Character &character) const;

    const CharacterDollTable *m_pCharacterDollTable = nullptr;
    const Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    SoundCatalog m_soundCatalog;
    SpeechReactionTable m_speechReactionTable;
    Engine::AudioSystem m_audioSystem;
    std::unordered_map<PlaybackGroup, uint64_t> m_activeGroupInstanceIds;
    std::unordered_map<uint32_t, uint64_t> m_activeSpeechInstanceIds;
    std::unordered_map<int, std::string> m_loadedMusicClipKeys;
    int m_activeMusicTrack = 0;
    int m_pendingMusicTrack = 0;
    uint64_t m_activeMusicInstanceId = 0;
    float m_activeMusicVolume = 0.0f;
    float m_musicFadeVelocity = 0.0f;
};
}
