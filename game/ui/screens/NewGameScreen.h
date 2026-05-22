#pragma once

#include "game/data/GameDataRepository.h"
#include "game/party/Party.h"
#include "game/ui/MenuScreenBase.h"
#include "game/ui/UiLayoutManager.h"

#include <SDL3/SDL.h>

#include <array>
#include <functional>
#include <optional>
#include <random>
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

    struct CreationCandidate
    {
        uint32_t characterDataId = 0;
        uint32_t classId = 0;
        uint32_t raceId = 0;
        std::string defaultName;
        std::string className;
        std::string raceName;
        std::vector<uint32_t> availableClassIds;
        bool hasCustomDefaultStats = false;
        std::array<int, static_cast<size_t>(StatId::Count)> defaultStats = {};
        std::array<std::string, 2> defaultOptionalSkills = {};
    };

    using ContinueAction = std::function<void(const std::vector<Character> &, uint32_t)>;
    using BackAction = std::function<void()>;

    NewGameScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        GameAudioSystem *pGameAudioSystem,
        const GameDataRepository &gameData,
        bool debugGodLichRoster,
        bool allowIncompleteCharacterCreation,
        ContinueAction continueAction,
        BackAction backAction);

    AppMode mode() const override;
    void prepareForFirstFrame();
    void onEnter() override;
    void onExit() override;
    void handleSdlEvent(const SDL_Event &event) override;
    bool textInputActive() const;

private:
    enum class FlowStage
    {
        ContinentSelection,
        CharacterCreation
    };

    struct SelectedContinent
    {
        uint32_t id = 1;
        std::string key = "jadame";
        std::string name = "Jadam";
    };

    struct CreationState
    {
        size_t selectedCandidateIndex = 0;
        uint32_t selectedClassId = 0;
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
    void drawContinentSelection(float deltaSeconds);
    void selectContinent(const std::string &continentKey);
    void initializeCharacterCreationForSelectedContinent();
    void ensurePartyStates();
    void saveActivePartyState();
    void switchActivePartySlot(size_t slotIndex);
    void addPartySlot();
    void removePartySlot();
    void resetStateForCandidate(size_t candidateIndex);
    void rebuildCandidates();
    void refreshSkillChoices(bool applyCandidateDefaults);
    size_t candidateCount() const;
    const CreationCandidate &candidateAt(size_t candidateIndex) const;
    void beginNameEditing();
    void endNameEditing(bool commitEdit);
    void deleteNameEditCharacter();
    void resetNameBackspaceRepeat();
    void updateNameBackspaceRepeat(float deltaSeconds);
    void ensurePcNamesLoaded();
    std::string generateDefaultNameForState(const CreationState &state);
    bool partyNameAlreadyUsed(const std::string &name) const;
    size_t pcNameColumnForState(const CreationState &state) const;
    bool tryIncreaseStat(StatId statId);
    bool tryDecreaseStat(StatId statId);
    bool tryToggleOptionalSkill(const std::string &skillName);
    int currentBonusPool() const;
    int bonusPoolForState(const CreationState &state) const;
    Character buildCharacter() const;
    Character buildCharacterFromState(const CreationState &state) const;
    std::vector<Character> buildPartyCharacters() const;
    std::string selectedClassName() const;
    std::string classNameForState(const CreationState &state) const;
    std::vector<int> availableVoiceIdsForSelectedCandidate() const;
    std::vector<std::string> wrapTextToWidth(const std::string &fontName, const std::string &text, float maxWidth, float scale);
    const CharacterDollEntry *selectedCharacterEntry() const;
    const CharacterDollEntry *characterEntryForState(const CreationState &state) const;
    const CreationCandidate &selectedCandidate() const;
    const CreationCandidate &candidateForState(const CreationState &state) const;
    std::array<int, static_cast<size_t>(StatId::Count)> statsForRace(const std::string &raceName) const;
    void cycleCandidate(int direction);
    void cycleClass(int direction);
    void cycleVoice(int direction);
    void resetCurrentState(bool applyCandidateDefaults = false);
    void confirmCreation();
    void cancelCreation();
    bool ensureLayoutLoaded();
    bool ensureContinentLayoutLoaded();
    std::optional<MenuScreenBase::Rect> resolveLayoutRect(
        const std::string &layoutId,
        float fallbackWidth = 0.0f,
        float fallbackHeight = 0.0f) const;
    std::optional<MenuScreenBase::Rect> resolveContinentLayoutRect(
        const std::string &layoutId,
        float fallbackWidth = 0.0f,
        float fallbackHeight = 0.0f) const;
    ButtonVisualSet resolveButtonVisuals(
        const std::string &layoutId,
        const ButtonVisualSet &fallbackVisuals) const;
    ButtonVisualSet resolveContinentButtonVisuals(
        const std::string &layoutId,
        const ButtonVisualSet &fallbackVisuals) const;
    std::string resolveAssetName(const std::string &layoutId, const std::string &fallbackAssetName) const;
    std::string resolveContinentAssetName(const std::string &layoutId, const std::string &fallbackAssetName) const;
    ButtonState drawEllipseButton(const ButtonVisualSet &visuals, const Rect &rect);
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
    void renderClassInspectPopup(
        const ClassInspectEntry &entry,
        const MenuScreenBase::Rect &sourceRect,
        float scale);
    void showCreationCompletionError();
    void renderCreationCompletionErrorMessageBox(
        const MenuScreenBase::Rect &rootRect,
        float scale);
    std::optional<TexturePixelsBgra> buildCreationPreviewDollPixels(
        const CharacterDollEntry &entry,
        const CharacterDollTypeEntry *pDollType);
    void playUiClickSound(SoundId soundId) const;
    void playVoicePreview();

    GameAudioSystem *m_pGameAudioSystem = nullptr;
    const GameDataRepository *m_pGameData = nullptr;
    bool m_debugGodLichRoster = false;
    bool m_allowIncompleteCharacterCreation = false;
    ContinueAction m_continueAction;
    BackAction m_backAction;
    UiLayoutManager m_layoutManager;
    UiLayoutManager m_continentLayoutManager;
    FlowStage m_stage = FlowStage::ContinentSelection;
    SelectedContinent m_selectedContinent = {};
    std::vector<CreationCandidate> m_candidates;
    std::vector<CreationState> m_partyStates;
    std::array<std::vector<std::string>, 8> m_pcNameColumns;
    CreationState m_state = {};
    size_t m_partySize = 1;
    size_t m_activePartySlot = 0;
    std::mt19937 m_nameRng;
    bool m_pcNamesLoaded = false;
    bool m_nameBackspaceHeld = false;
    float m_nameBackspaceRepeatTimer = 0.0f;
    float m_creationCompletionErrorSeconds = 0.0f;
    std::string m_creationPreviewDollCacheKey;
    std::optional<TexturePixelsBgra> m_creationPreviewDollPixels;
    bool m_layoutLoaded = false;
    bool m_continentLayoutLoaded = false;
    bool m_characterCreationInitialized = false;
    bool m_escapePressed = false;
    bool m_returnPressed = false;
};
}
