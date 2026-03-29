#pragma once

#include "engine/AudioSystem.h"
#include "game/CharacterDollTable.h"
#include "game/Party.h"
#include "game/SoundCatalog.h"
#include "game/SoundIds.h"
#include "game/SpellTable.h"
#include "game/SpeechIds.h"
#include "game/SpeechReactionTable.h"

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
    void update(float listenerX, float listenerY, float listenerZ);

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
    uint64_t playResolvedSound(
        const std::string &virtualPath,
        PlaybackGroup group,
        const std::optional<WorldPosition> &position,
        bool loop);
    std::optional<uint32_t> resolveCharacterVoiceId(const Character &character) const;

    const CharacterDollTable *m_pCharacterDollTable = nullptr;
    SoundCatalog m_soundCatalog;
    SpeechReactionTable m_speechReactionTable;
    Engine::AudioSystem m_audioSystem;
    std::unordered_map<PlaybackGroup, uint64_t> m_activeGroupInstanceIds;
    std::unordered_map<uint32_t, uint64_t> m_activeSpeechInstanceIds;
};
}
