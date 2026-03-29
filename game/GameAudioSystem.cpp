#include "game/GameAudioSystem.h"

#include "engine/TextTable.h"
#include "game/SpellIds.h"

#include <SDL3/SDL.h>

namespace OpenYAMM::Game
{
bool GameAudioSystem::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const CharacterDollTable &characterDollTable,
    const SpellTable &spellTable)
{
    shutdown();
    m_pCharacterDollTable = &characterDollTable;

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
    return true;
}

void GameAudioSystem::shutdown()
{
    m_activeGroupInstanceIds.clear();
    m_activeSpeechInstanceIds.clear();
    m_audioSystem.shutdown();
    m_soundCatalog = {};
    m_speechReactionTable = {};
    m_pCharacterDollTable = nullptr;
}

void GameAudioSystem::update(float listenerX, float listenerY, float listenerZ)
{
    Engine::AudioSystem::ListenerState listenerState = {};
    listenerState.x = listenerX;
    listenerState.y = listenerY;
    listenerState.z = listenerZ;
    m_audioSystem.update(listenerState);
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

bool GameAudioSystem::playCommonSound(
    SoundId soundId,
    PlaybackGroup group,
    const std::optional<WorldPosition> &position)
{
    return playSound(static_cast<uint32_t>(soundId), group, position);
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

std::optional<uint32_t> GameAudioSystem::resolveCharacterVoiceId(const Character &character) const
{
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
}
