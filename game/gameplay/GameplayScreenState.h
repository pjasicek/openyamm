#pragma once

#include "game/party/PartySpellSystem.h"
#include "game/ui/GameplayUiController.h"

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
    using InventoryNestedOverlayState = GameplayUiController::InventoryNestedOverlayState;
    using HouseShopOverlayState = GameplayUiController::HouseShopOverlayState;
    using HouseBankState = GameplayUiController::HouseBankState;

    struct PendingSpellTargetState
    {
        bool active = false;
        size_t casterMemberIndex = 0;
        uint32_t spellId = 0;
        uint32_t skillLevelOverride = 0;
        SkillMastery skillMasteryOverride = SkillMastery::None;
        bool spendMana = true;
        bool applyRecovery = true;
        PartySpellCastTargetKind targetKind = PartySpellCastTargetKind::None;
        std::string spellName;
        bool clickLatch = false;

        void clear();
    };

    struct QuickSpellState
    {
        float castRepeatCooldownSeconds = 0.0f;
        bool castLatch = false;
        bool readyMemberAvailableWhileHeld = false;
        bool attackFallbackRequested = false;

        void clear();
    };

    struct AttackActionState
    {
        bool inspectLatch = false;
        bool readyMemberAvailableWhileHeld = false;
        float inspectRepeatCooldownSeconds = 0.0f;

        void clear();
    };

    struct WorldInteractionInputState
    {
        bool keyboardUseLatch = false;
        bool heldInventoryDropLatch = false;
        bool inspectMouseActivateLatch = false;

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

    InventoryNestedOverlayState &inventoryNestedOverlay();
    const InventoryNestedOverlayState &inventoryNestedOverlay() const;

    HouseShopOverlayState &houseShopOverlay();
    const HouseShopOverlayState &houseShopOverlay() const;

    HouseBankState &houseBankState();
    const HouseBankState &houseBankState() const;

    PendingSpellTargetState &pendingSpellTarget();
    const PendingSpellTargetState &pendingSpellTarget() const;

    QuickSpellState &quickSpellState();
    const QuickSpellState &quickSpellState() const;

    AttackActionState &attackActionState();
    const AttackActionState &attackActionState() const;

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
    WorldInteractionInputState m_worldInteractionInputState = {};
    GameplayMouseLookState m_gameplayMouseLookState = {};
    bool m_pendingOpenNewGameScreen = false;
    bool m_pendingOpenLoadGameScreen = false;
};
}
