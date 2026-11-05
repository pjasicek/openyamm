#pragma once

#include "game/app/NewGameOptions.h"
#include "game/content/RulesetDefinition.h"
#include "game/data/GameDataRepository.h"
#include "game/party/Party.h"
#include "game/party/SpeechIds.h"
#include "game/ui/MenuDesignScreen.h"
#include "game/ui/screens/PartyCreationSheet.h"
#include "game/ui/UiLayoutManager.h"

#include <SDL3/SDL.h>

#include <array>
#include <functional>
#include <memory>
#include <optional>
#include <random>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class GameAudioSystem;
class MawRules;
struct GameRules;

class NewGameScreen : public MenuDesignScreen
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

    using ContinueAction = std::function<void(const std::vector<Character> &, const NewGameOptions &)>;
    // Loads the common data under the chosen ruleset's tables before party creation reads them.
    using ActivateRulesetAction = std::function<bool(const std::string &rulesetId, std::string &error)>;
    using BackAction = std::function<void()>;

    NewGameScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        GameAudioSystem *pGameAudioSystem,
        const GameDataRepository &gameData,
        bool debugGodLichRoster,
        bool includeGodLichCandidate,
        bool allowIncompleteCharacterCreation,
        ContinueAction continueAction,
        ActivateRulesetAction activateRulesetAction,
        BackAction backAction);
    ~NewGameScreen() override;

    AppMode mode() const override;
    void prepareForFirstFrame();
    void onEnter() override;
    void onExit() override;
    void handleSdlEvent(const SDL_Event &event) override;
    bool textInputActive() const override;

  private:
    friend struct NewGameScreenTestAccess;

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
        // The player typed the name: a new portrait or Default keeps it.
        bool nameTyped = false;
        std::string nameEditBuffer;
        std::string statusMessage;
    };

    // The party creation sheet's popups (approach C2, level_generation/ui/party_creation_study_20261101).
    enum class SheetPopup
    {
        None,
        Portrait,
        Voice,
        Class,
        MasteryTable,
        PartyBoard,
    };

    // A right-button explanation (attributes, the class) drawn over the sheet.
    struct CreationHelp
    {
        std::string title;
        std::string body;
        std::vector<std::pair<std::string, uint32_t>> lines;
        Rect anchor;
    };

    void drawScreen(float deltaSeconds) override;
    void drawContinentSelection(float deltaSeconds);
    void drawCharacterCreation(float deltaSeconds);
    void drawCreationHeader();
    void drawCreationRoster(bool input);
    void drawCreationIdentity(bool input);
    void drawCreationAttributes(bool input);
    void drawCreationRaceCard(bool input);
    void drawCreationSkills(bool input, float deltaSeconds);
    void drawCreationDoll(bool input);
    // Returns false when Cancel left the screen.
    bool drawCreationFooter(bool input);
    void drawCreationSkillCard(size_t slotIndex, const std::string &skill, const Rect &anchor);
    void drawCreationHelp();
    void drawPortraitPicker();
    void drawVoicePicker();
    void drawClassPicker();
    void drawMasteryTablePopup();
    void drawPartyBoard();
    // The veil and frame of a popup over the sheet (mockup pixels); returns false when its Close button or Escape
    // closed it. The content area starts below the title row.
    bool drawPopupFrame(const std::string &title, float x, float y, float width, float height);
    // A class line's skill table for a race: rows the line learns, columns the class and its promotions; returns its
    // height in mockup pixels.
    float drawClassLineTable(float x, float y, float width, uint32_t raceId, const std::string &className,
                             uint32_t startingClassId);
    // Mockup pixels (1600x900) to screen pixels, and a mockup rect on screen.
    float sheetPx(float browserPixels) const;
    Rect sheetRect(float x, float y, float width, float height) const;
    // Text in a screen rect at the mockup's CSS size; align -1 left, 0 centre, 1 right.
    void sheetText(const Rect &rect, const std::string &text, const std::string &font, float cssPixels,
                   uint32_t color, int align = -1);
    float sheetTextWidth(const std::string &text, const std::string &font, float cssPixels);
    void glyph(const std::string &name, const Rect &rect, uint32_t color);
    void horizontalGradient(const Rect &rect, uint32_t left, uint32_t right);
    void verticalGradient(const Rect &rect, uint32_t top, uint32_t bottom);
    void playCreationVoiceLine(int voiceId, SpeechId speech);
    // The voice's number as players see it: the lowest portrait whose own voice it is (portrait #N speaks with
    // Voice N), or the voice id plus one for a voice no portrait owns.
    int voiceDisplayNumber(int voiceId) const;
    void openSheetPopup(SheetPopup popup);
    void chooseCandidateForActiveSlot(size_t candidateIndex);
    void removePartySlotAt(size_t slotIndex);
    bool toggleOptionalSkillForSlot(size_t slotIndex, const std::string &skillName);
    bool stateComplete(const CreationState &state) const;
    size_t requiredSkillCount(const CreationState &state) const;
    std::array<RaceStatLine, CreationStatCount> raceStatLinesForState(const CreationState &state) const;
    CreationPartyMember creationPartyMember(const CreationState &state) const;
    std::vector<CreationPartyMember> creationPartyMembers() const;
    void drawRulesetSwitch();
    void drawRulesPanel();
    // One rule setting: name and control on a line, description below; returns the y after it.
    float drawRulesSetting(const std::string &id, const std::string &name, const std::string &description,
                           bool select, const std::string &value, bool enabled, bool last, float y, bool &activated);
    // Text of a Rules panel element at content position y (logical units), word-wrapped; returns its height.
    float drawRulesText(const std::string &id, const std::string &text, float y, uint32_t color = 0);
    Rect rulesRect(const std::string &id, float y) const;
    // A row of tabs inside a brass outline; returns the clicked tab.
    std::optional<size_t> drawSegmentedSwitch(const std::string &id, const Rect &frame,
                                              const std::vector<std::string> &labels, size_t selected, bool enabled);
    const RulesetDefinition &chosenRulesetDefinition() const;
    void loadRulesets();
    void selectContinent(const std::string &continentKey);
    void initializeCharacterCreationForSelectedContinent();
    void ensurePartyStates();
    void saveActivePartyState();
    void switchActivePartySlot(size_t slotIndex);
    void addPartySlot();
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
    bool isGodLichState(const CreationState &state) const;
    bool isGodLichSelected() const;
    std::array<int, static_cast<size_t>(StatId::Count)> statsForRace(const std::string &raceName) const;
    void resetCurrentState(bool applyCandidateDefaults = false);
    void confirmCreation();
    void cancelCreation();
    Character buildVoicePreviewCharacter() const;
    void showCreationCompletionError();
    // The rules the creation popups read (a ruleset's skill texts, race card and skill matrix): a throwaway copy of the
    // chosen ruleset's rules, never given to the party the game starts with; Standard's for Standard.
    const GameRules &creationRules();
    // The class/skill matrix of a character's class line with its race: the best cap of each skill, best first; a skill
    // that needs a promotion for it carries a "*".
    std::vector<std::pair<std::string, uint32_t>> creationSkillMatrixLines(const Character &character) const;
    std::optional<TexturePixelsBgra> buildCreationPreviewDollPixels(
        const CharacterDollEntry &entry,
        const CharacterDollTypeEntry *pDollType);

    GameAudioSystem *m_pGameAudioSystem = nullptr;
    const GameDataRepository *m_pGameData = nullptr;
    bool m_debugGodLichRoster = false;
    bool m_includeGodLichCandidate = false;
    bool m_allowIncompleteCharacterCreation = false;
    ContinueAction m_continueAction;
    ActivateRulesetAction m_activateRulesetAction;
    BackAction m_backAction;
    FlowStage m_stage = FlowStage::ContinentSelection;
    SelectedContinent m_selectedContinent = {};
    RulesetSelection m_ruleset;
    std::unique_ptr<MawRules> m_pCreationRules;
    RulesetSelection m_creationRulesSelection;
    // Standard first, then the installed ruleset packages.
    std::vector<RulesetDefinition> m_rulesets;
    // The options last chosen for each ruleset in this run, so switching rulesets back and forth keeps them.
    std::unordered_map<std::string, RulesetOptions> m_rulesetOptions;
    bool m_rulesPanelOpen = false;
    RulesetOptions m_rulesDraft;
    // The difficulty and progression chosen before a challenge mode forced others, restored when it no longer does.
    std::optional<RulesetDifficulty> m_unforcedDifficulty;
    std::optional<RulesetProgression> m_unforcedProgression;
    float m_rulesScroll = 0;
    float m_rulesContentHeight = 0;
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
    std::string m_creationPreviewDollCacheKey;
    std::optional<TexturePixelsBgra> m_creationPreviewDollPixels;
    bool m_characterCreationInitialized = false;
    SheetPopup m_sheetPopup = SheetPopup::None;
    float m_popupScroll = 0;
    float m_popupContentHeight = 0;
    // The class picker's mastery table scrolls on its own.
    float m_tableScroll = 0;
    // The race card scrolls when a race has more rules than fit; a new race starts at the top.
    float m_raceCardScroll = 0;
    uint32_t m_raceCardRaceId = 0;
    float m_tableContentHeight = 0;
    // The portrait grid's filter: 0 everyone, 1 men, 2 women.
    int m_portraitFilter = 0;
    uint32_t m_classPreviewId = 0;
    // The skill under the pointer and for how long, for the skill card.
    std::string m_hoverSkill;
    size_t m_hoverSkillSlot = 0;
    Rect m_hoverSkillAnchor;
    float m_hoverSkillSeconds = 0;
    float m_frameSeconds = 0;
    CreationHelp m_help;
    bool m_escapePressed = false;
    bool m_returnPressed = false;
};
}
