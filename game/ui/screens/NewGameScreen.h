#pragma once

#include "game/data/GameDataRepository.h"
#include "game/party/Party.h"
#include "game/ui/MenuScreenBase.h"
#include "game/ui/UiLayoutManager.h"

#include <SDL3/SDL.h>

#include <array>
#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameAudioSystem;

class NewGameScreen : public MenuScreenBase
{
public:
    enum class StatId
    {
        Might = 0,
        Intellect,
        Personality,
        Endurance,
        Accuracy,
        Speed,
        Luck,
        Count,
    };

    enum class CreationRace
    {
        Human,
        Vampire,
        DarkElf,
        Minotaur,
        Troll,
    };

    struct CreationCandidate
    {
        uint32_t characterDataId = 0;
        const char *pDefaultName = "";
        const char *pClassName = "";
        CreationRace race = CreationRace::Human;
        bool hasCustomDefaultStats = false;
        std::array<int, static_cast<size_t>(StatId::Count)> defaultStats = {};
        std::array<const char *, 2> defaultOptionalSkills = {{"", ""}};
    };

    using ContinueAction = std::function<void(const Character &)>;
    using BackAction = std::function<void()>;

    NewGameScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        GameAudioSystem *pGameAudioSystem,
        const GameDataRepository &gameData,
        ContinueAction continueAction,
        BackAction backAction);

    AppMode mode() const override;
    void onEnter() override;
    void onExit() override;
    void handleSdlEvent(const SDL_Event &event) override;

private:
    struct CreationState
    {
        size_t selectedCandidateIndex = 0;
        int selectedVoiceId = 0;
        std::string name;
        std::array<int, static_cast<size_t>(StatId::Count)> baseStats = {};
        std::array<int, static_cast<size_t>(StatId::Count)> currentStats = {};
        std::vector<std::string> defaultSkills;
        std::vector<std::string> optionalSkills;
        std::vector<std::string> selectedOptionalSkills;
        bool nameEditing = false;
        std::string nameEditBuffer;
        std::string statusMessage;
    };

    void drawScreen(float deltaSeconds) override;
    void resetStateForCandidate(size_t candidateIndex);
    void beginNameEditing();
    void endNameEditing(bool commitEdit);
    bool tryIncreaseStat(StatId statId);
    bool tryDecreaseStat(StatId statId);
    bool tryToggleOptionalSkill(const std::string &skillName);
    int currentBonusPool() const;
    Character buildCharacter() const;
    std::vector<int> availableVoiceIdsForSelectedCandidate() const;
    std::vector<std::string> wrapTextToWidth(const std::string &fontName, const std::string &text, float maxWidth, float scale);
    const CharacterDollEntry *selectedCharacterEntry() const;
    const CreationCandidate &selectedCandidate() const;
    std::array<int, static_cast<size_t>(StatId::Count)> statsForRace(CreationRace race) const;
    void cycleCandidate(int direction);
    void cycleVoice(int direction);
    void resetCurrentState(bool applyCandidateDefaults = false);
    void confirmCreation();
    void cancelCreation();
    bool ensureLayoutLoaded();
    std::optional<MenuScreenBase::Rect> resolveLayoutRect(
        const std::string &layoutId,
        float fallbackWidth = 0.0f,
        float fallbackHeight = 0.0f) const;
    ButtonVisualSet resolveButtonVisuals(
        const std::string &layoutId,
        const ButtonVisualSet &fallbackVisuals) const;
    std::string resolveAssetName(const std::string &layoutId, const std::string &fallbackAssetName) const;
    Character buildVoicePreviewCharacter() const;
    void renderSkillInspectPopup(
        const SkillInspectEntry &entry,
        const std::string &skillName,
        const MenuScreenBase::Rect &sourceRect,
        const Character &character,
        float scale);
    void renderStatInspectPopup(
        const StatInspectEntry &entry,
        const MenuScreenBase::Rect &sourceRect,
        float scale);
    void playUiClickSound(SoundId soundId) const;
    void playVoicePreview();

    GameAudioSystem *m_pGameAudioSystem = nullptr;
    const GameDataRepository *m_pGameData = nullptr;
    ContinueAction m_continueAction;
    BackAction m_backAction;
    UiLayoutManager m_layoutManager;
    CreationState m_state = {};
    bool m_layoutLoaded = false;
    bool m_escapePressed = false;
    bool m_returnPressed = false;
};
}
