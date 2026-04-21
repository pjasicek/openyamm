#include "game/gameplay/GameplayScreenState.h"

namespace OpenYAMM::Game
{
void GameplayScreenState::PendingSpellTargetState::clear()
{
    *this = {};
}

void GameplayScreenState::QuickSpellState::clear()
{
    *this = {};
}

void GameplayScreenState::AttackActionState::clear()
{
    *this = {};
}

void GameplayScreenState::WorldInteractionInputState::clear()
{
    *this = {};
}

void GameplayScreenState::GameplayMouseLookState::clear()
{
    *this = {};
}

void GameplayScreenState::clear()
{
    m_uiState = {};
    m_pendingSpellTarget.clear();
    m_quickSpellState.clear();
    m_attackActionState.clear();
    m_worldInteractionInputState.clear();
    m_gameplayMouseLookState.clear();
    m_pendingOpenNewGameScreen = false;
    m_pendingOpenLoadGameScreen = false;
}

GameplayScreenState::UiState &GameplayScreenState::uiState()
{
    return m_uiState;
}

const GameplayScreenState::UiState &GameplayScreenState::uiState() const
{
    return m_uiState;
}

GameplayScreenState::CharacterScreenState &GameplayScreenState::characterScreen()
{
    return m_uiState.characterScreen;
}

const GameplayScreenState::CharacterScreenState &GameplayScreenState::characterScreen() const
{
    return m_uiState.characterScreen;
}

GameplayScreenState::SpellbookState &GameplayScreenState::spellbook()
{
    return m_uiState.spellbook;
}

const GameplayScreenState::SpellbookState &GameplayScreenState::spellbook() const
{
    return m_uiState.spellbook;
}

GameplayScreenState::RestScreenState &GameplayScreenState::restScreen()
{
    return m_uiState.restScreen;
}

const GameplayScreenState::RestScreenState &GameplayScreenState::restScreen() const
{
    return m_uiState.restScreen;
}

GameplayScreenState::MenuScreenState &GameplayScreenState::menuScreen()
{
    return m_uiState.menuScreen;
}

const GameplayScreenState::MenuScreenState &GameplayScreenState::menuScreen() const
{
    return m_uiState.menuScreen;
}

GameplayScreenState::ControlsScreenState &GameplayScreenState::controlsScreen()
{
    return m_uiState.controlsScreen;
}

const GameplayScreenState::ControlsScreenState &GameplayScreenState::controlsScreen() const
{
    return m_uiState.controlsScreen;
}

GameplayScreenState::KeyboardScreenState &GameplayScreenState::keyboardScreen()
{
    return m_uiState.keyboardScreen;
}

const GameplayScreenState::KeyboardScreenState &GameplayScreenState::keyboardScreen() const
{
    return m_uiState.keyboardScreen;
}

GameplayScreenState::VideoOptionsScreenState &GameplayScreenState::videoOptionsScreen()
{
    return m_uiState.videoOptionsScreen;
}

const GameplayScreenState::VideoOptionsScreenState &GameplayScreenState::videoOptionsScreen() const
{
    return m_uiState.videoOptionsScreen;
}

GameplayScreenState::SaveGameScreenState &GameplayScreenState::saveGameScreen()
{
    return m_uiState.saveGameScreen;
}

const GameplayScreenState::SaveGameScreenState &GameplayScreenState::saveGameScreen() const
{
    return m_uiState.saveGameScreen;
}

GameplayScreenState::LoadGameScreenState &GameplayScreenState::loadGameScreen()
{
    return m_uiState.loadGameScreen;
}

const GameplayScreenState::LoadGameScreenState &GameplayScreenState::loadGameScreen() const
{
    return m_uiState.loadGameScreen;
}

GameplayScreenState::JournalScreenState &GameplayScreenState::journalScreen()
{
    return m_uiState.journalScreen;
}

const GameplayScreenState::JournalScreenState &GameplayScreenState::journalScreen() const
{
    return m_uiState.journalScreen;
}

GameplayScreenState::InventoryNestedOverlayState &GameplayScreenState::inventoryNestedOverlay()
{
    return m_uiState.inventoryNestedOverlay;
}

const GameplayScreenState::InventoryNestedOverlayState &GameplayScreenState::inventoryNestedOverlay() const
{
    return m_uiState.inventoryNestedOverlay;
}

GameplayScreenState::HouseShopOverlayState &GameplayScreenState::houseShopOverlay()
{
    return m_uiState.houseShopOverlay;
}

const GameplayScreenState::HouseShopOverlayState &GameplayScreenState::houseShopOverlay() const
{
    return m_uiState.houseShopOverlay;
}

GameplayScreenState::HouseBankState &GameplayScreenState::houseBankState()
{
    return m_uiState.houseBankState;
}

const GameplayScreenState::HouseBankState &GameplayScreenState::houseBankState() const
{
    return m_uiState.houseBankState;
}

GameplayScreenState::PendingSpellTargetState &GameplayScreenState::pendingSpellTarget()
{
    return m_pendingSpellTarget;
}

const GameplayScreenState::PendingSpellTargetState &GameplayScreenState::pendingSpellTarget() const
{
    return m_pendingSpellTarget;
}

GameplayScreenState::QuickSpellState &GameplayScreenState::quickSpellState()
{
    return m_quickSpellState;
}

const GameplayScreenState::QuickSpellState &GameplayScreenState::quickSpellState() const
{
    return m_quickSpellState;
}

GameplayScreenState::AttackActionState &GameplayScreenState::attackActionState()
{
    return m_attackActionState;
}

const GameplayScreenState::AttackActionState &GameplayScreenState::attackActionState() const
{
    return m_attackActionState;
}

GameplayScreenState::WorldInteractionInputState &GameplayScreenState::worldInteractionInputState()
{
    return m_worldInteractionInputState;
}

const GameplayScreenState::WorldInteractionInputState &GameplayScreenState::worldInteractionInputState() const
{
    return m_worldInteractionInputState;
}

GameplayScreenState::GameplayMouseLookState &GameplayScreenState::gameplayMouseLookState()
{
    return m_gameplayMouseLookState;
}

const GameplayScreenState::GameplayMouseLookState &GameplayScreenState::gameplayMouseLookState() const
{
    return m_gameplayMouseLookState;
}

void GameplayScreenState::requestOpenNewGameScreen()
{
    m_pendingOpenNewGameScreen = true;
}

void GameplayScreenState::requestOpenLoadGameScreen()
{
    m_pendingOpenLoadGameScreen = true;
}

bool GameplayScreenState::consumePendingOpenNewGameScreenRequest()
{
    const bool pending = m_pendingOpenNewGameScreen;
    m_pendingOpenNewGameScreen = false;
    return pending;
}

bool GameplayScreenState::consumePendingOpenLoadGameScreenRequest()
{
    const bool pending = m_pendingOpenLoadGameScreen;
    m_pendingOpenLoadGameScreen = false;
    return pending;
}
}
