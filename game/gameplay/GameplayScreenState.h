#pragma once

#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/party/PartySpellSystem.h"
#include "game/ui/GameplayUiController.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenState
{
public:
    using UiState = GameplayUiController::State;
    using CharacterScreenState = GameplayUiController::CharacterScreenState;
    using SpellbookState = GameplayUiController::SpellbookState;
    using RestScreenState = GameplayUiController::RestScreenState;
    using MenuScreenState = GameplayUiController::MenuScreenState;
    using ControlsScreenState = GameplayUiController::ControlsScreenState;
    using KeyboardScreenState = GameplayUiController::KeyboardScreenState;
    using VideoOptionsScreenState = GameplayUiController::VideoOptionsScreenState;
    using SaveGameScreenState = GameplayUiController::SaveGameScreenState;
    using LoadGameScreenState = GameplayUiController::LoadGameScreenState;
    using JournalScreenState = GameplayUiController::JournalScreenState;
    using QuickReferenceScreenState = GameplayUiController::QuickReferenceScreenState;
    using InventoryNestedOverlayState = GameplayUiController::InventoryNestedOverlayState;
    using HouseShopOverlayState = GameplayUiController::HouseShopOverlayState;
    using HouseShopVisitState = GameplayUiController::HouseShopVisitState;
    using HouseBankState = GameplayUiController::HouseBankState;

    struct PendingSpellTargetState
    {
        bool active = false;
        size_t casterMemberIndex = 0;
        uint32_t spellId = 0;
        uint32_t skillLevelOverride = 0;
        SkillMastery skillMasteryOverride = SkillMastery::None;
        bool bypassRequiredMastery = false;
        bool spendMana = true;
        bool applyRecovery = true;
        PartySpellCastTargetKind targetKind = PartySpellCastTargetKind::None;
        std::string spellName;
        bool clickLatch = false;
        bool cancelLatch = false;
        bool hasSelectedGroundTargetPoint = false;
        float selectedGroundTargetX = 0.0f;
        float selectedGroundTargetY = 0.0f;
        float selectedGroundTargetZ = 0.0f;

        void clear();
    };

    struct QuickSpellState
    {
        float castRepeatCooldownSeconds = 0.0f;
        bool castLatch = false;
        // The held key has passed its first-repeat delay and repeats at the short interval.
        bool castRepeating = false;
        bool readyMemberAvailableWhileHeld = false;
        bool attackFallbackRequested = false;
        // The extra quick spell slot whose key began the held cast (Quick Spell 1-4); none for the quick spell.
        std::optional<size_t> extraSlot;

        void clear();
    };

    struct AttackActionState
    {
        bool inspectLatch = false;
        // The held key has passed its first-repeat delay and repeats at the short interval.
        bool inspectRepeating = false;
        bool readyMemberAvailableWhileHeld = false;
        bool suppressAttackUntilRelease = false;
        float inspectRepeatCooldownSeconds = 0.0f;

        bool blocksAttackInput(bool attackPressed);
        void clear();
    };

    // The Upkeep key's hold (GameplayActionController::updateUpkeepAction).
    struct UpkeepActionState
    {
        bool latch = false;
        float repeatCooldownSeconds = 0.0f;
    };

    struct WorldInteractionInputState
    {
        bool keyboardUseLatch = false;
        bool inspectKeyboardActivateLatch = false;
        uint64_t keyboardUseNextRepeatTickNanoseconds = 0;
        uint64_t inspectKeyboardActivateNextRepeatTickNanoseconds = 0;
        bool heldInventoryDropLatch = false;
        bool inspectMouseActivateLatch = false;
        // A Ctrl click held after the steal: the left button is the attack too, and must not attack until released.
        bool stealClickLatch = false;
        // The smart left click's choice for this press, kept until the button is released.
        enum class SmartClick : uint8_t
        {
            None,
            Use,
            Attack
        };
        SmartClick smartClick = SmartClick::None;
        GameplayWorldHit pressedWorldHit;

        void clear();
    };

    struct GameplayMouseLookState
    {
        bool mouseLookActive = false;
        bool cursorModeActive = false;

        void clear();
    };

    void clear();

    UiState &uiState();
    const UiState &uiState() const;

    CharacterScreenState &characterScreen();
    const CharacterScreenState &characterScreen() const;

    SpellbookState &spellbook();
    const SpellbookState &spellbook() const;

    RestScreenState &restScreen();
    const RestScreenState &restScreen() const;

    MenuScreenState &menuScreen();
    const MenuScreenState &menuScreen() const;

    ControlsScreenState &controlsScreen();
    const ControlsScreenState &controlsScreen() const;

    KeyboardScreenState &keyboardScreen();
    const KeyboardScreenState &keyboardScreen() const;

    VideoOptionsScreenState &videoOptionsScreen();
    const VideoOptionsScreenState &videoOptionsScreen() const;

    SaveGameScreenState &saveGameScreen();
    const SaveGameScreenState &saveGameScreen() const;

    LoadGameScreenState &loadGameScreen();
    const LoadGameScreenState &loadGameScreen() const;

    JournalScreenState &journalScreen();
    const JournalScreenState &journalScreen() const;

    QuickReferenceScreenState &quickReferenceScreen();
    const QuickReferenceScreenState &quickReferenceScreen() const;

    InventoryNestedOverlayState &inventoryNestedOverlay();
    const InventoryNestedOverlayState &inventoryNestedOverlay() const;

    HouseShopOverlayState &houseShopOverlay();
    const HouseShopOverlayState &houseShopOverlay() const;

    HouseShopVisitState &houseShopVisit();
    const HouseShopVisitState &houseShopVisit() const;

    HouseBankState &houseBankState();
    const HouseBankState &houseBankState() const;

    PendingSpellTargetState &pendingSpellTarget();
    const PendingSpellTargetState &pendingSpellTarget() const;

    QuickSpellState &quickSpellState();
    const QuickSpellState &quickSpellState() const;

    AttackActionState &attackActionState();
    const AttackActionState &attackActionState() const;

    UpkeepActionState &upkeepActionState();

    WorldInteractionInputState &worldInteractionInputState();
    const WorldInteractionInputState &worldInteractionInputState() const;

    GameplayMouseLookState &gameplayMouseLookState();
    const GameplayMouseLookState &gameplayMouseLookState() const;

    void requestOpenNewGameScreen();
    void requestOpenLoadGameScreen();
    bool consumePendingOpenNewGameScreenRequest();
    bool consumePendingOpenLoadGameScreenRequest();

private:
    UiState m_uiState = {};
    PendingSpellTargetState m_pendingSpellTarget = {};
    QuickSpellState m_quickSpellState = {};
    AttackActionState m_attackActionState = {};
    UpkeepActionState m_upkeepActionState = {};
    WorldInteractionInputState m_worldInteractionInputState = {};
    GameplayMouseLookState m_gameplayMouseLookState = {};
    bool m_pendingOpenNewGameScreen = false;
    bool m_pendingOpenLoadGameScreen = false;
};
}
