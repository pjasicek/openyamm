#include "game/ui/GameplayUiController.h"

#include <array>
#include <algorithm>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
const std::array<std::string, 21> GameplayLayoutFiles = {
    "Data/ui/gameplay/gameplay.yml",
    "Data/ui/gameplay/chest.yml",
    "Data/ui/gameplay/dialogue.yml",
    "Data/ui/gameplay/character.yml",
    "Data/ui/gameplay/adventurers_inn.yml",
    "Data/ui/gameplay/spellbook.yml",
    "Data/ui/gameplay/rest.yml",
    "Data/ui/gameplay/menu.yml",
    "Data/ui/gameplay/controls.yml",
    "Data/ui/gameplay/keyboard.yml",
    "Data/ui/gameplay/video_options.yml",
    "Data/ui/gameplay/save_game.yml",
    "Data/ui/gameplay/load_game.yml",
    "Data/ui/gameplay/journal.yml",
    "Data/ui/gameplay/town_portal.yml",
    "Data/ui/gameplay/item_inspect.yml",
    "Data/ui/gameplay/character_inspect.yml",
    "Data/ui/gameplay/buff_inspect.yml",
    "Data/ui/gameplay/character_detail.yml",
    "Data/ui/gameplay/actor_inspect.yml",
    "Data/ui/gameplay/spell_inspect.yml"
};
}

bool GameplayUiController::loadGameplayLayouts(
    const Engine::AssetFileSystem &assetFileSystem,
    const LayoutLoader &loader) const
{
    bool loadedAnyLayout = false;

    for (const std::string &layoutFile : GameplayLayoutFiles)
    {
        const std::optional<std::string> fileContents = assetFileSystem.readTextFile(layoutFile);

        if (!fileContents)
        {
            if (layoutFile == GameplayLayoutFiles.front())
            {
                return false;
            }

            continue;
        }

        if (!loader(layoutFile))
        {
            return false;
        }

        loadedAnyLayout = true;
    }

    return loadedAnyLayout;
}

void GameplayUiController::clearRuntimeState()
{
    resolvedState() = {};
}

GameplayUiController::State &GameplayUiController::state()
{
    return resolvedState();
}

const GameplayUiController::State &GameplayUiController::state() const
{
    return resolvedState();
}

void GameplayUiController::bindExternalState(State *pState)
{
    m_pExternalState = pState;
}

void GameplayUiController::clearExternalStateBinding()
{
    m_pExternalState = nullptr;
}

GameplayUiController::State &GameplayUiController::resolvedState()
{
    return m_pExternalState != nullptr ? *m_pExternalState : m_state;
}

const GameplayUiController::State &GameplayUiController::resolvedState() const
{
    return m_pExternalState != nullptr ? *m_pExternalState : m_state;
}

GameplayUiController::CharacterScreenState &GameplayUiController::characterScreen()
{
    return resolvedState().characterScreen;
}

const GameplayUiController::CharacterScreenState &GameplayUiController::characterScreen() const
{
    return resolvedState().characterScreen;
}

GameplayUiController::HeldInventoryItemState &GameplayUiController::heldInventoryItem()
{
    return resolvedState().heldInventoryItem;
}

const GameplayUiController::HeldInventoryItemState &GameplayUiController::heldInventoryItem() const
{
    return resolvedState().heldInventoryItem;
}

GameplayUiController::ItemInspectOverlayState &GameplayUiController::itemInspectOverlay()
{
    return resolvedState().itemInspectOverlay;
}

const GameplayUiController::ItemInspectOverlayState &GameplayUiController::itemInspectOverlay() const
{
    return resolvedState().itemInspectOverlay;
}

GameplayUiController::CharacterInspectOverlayState &GameplayUiController::characterInspectOverlay()
{
    return resolvedState().characterInspectOverlay;
}

const GameplayUiController::CharacterInspectOverlayState &GameplayUiController::characterInspectOverlay() const
{
    return resolvedState().characterInspectOverlay;
}

GameplayUiController::BuffInspectOverlayState &GameplayUiController::buffInspectOverlay()
{
    return resolvedState().buffInspectOverlay;
}

const GameplayUiController::BuffInspectOverlayState &GameplayUiController::buffInspectOverlay() const
{
    return resolvedState().buffInspectOverlay;
}

GameplayUiController::CharacterDetailOverlayState &GameplayUiController::characterDetailOverlay()
{
    return resolvedState().characterDetailOverlay;
}

const GameplayUiController::CharacterDetailOverlayState &GameplayUiController::characterDetailOverlay() const
{
    return resolvedState().characterDetailOverlay;
}

GameplayUiController::ActorInspectOverlayState &GameplayUiController::actorInspectOverlay()
{
    return resolvedState().actorInspectOverlay;
}

const GameplayUiController::ActorInspectOverlayState &GameplayUiController::actorInspectOverlay() const
{
    return resolvedState().actorInspectOverlay;
}

GameplayUiController::SpellInspectOverlayState &GameplayUiController::spellInspectOverlay()
{
    return resolvedState().spellInspectOverlay;
}

const GameplayUiController::SpellInspectOverlayState &GameplayUiController::spellInspectOverlay() const
{
    return resolvedState().spellInspectOverlay;
}

GameplayUiController::ReadableScrollOverlayState &GameplayUiController::readableScrollOverlay()
{
    return resolvedState().readableScrollOverlay;
}

const GameplayUiController::ReadableScrollOverlayState &GameplayUiController::readableScrollOverlay() const
{
    return resolvedState().readableScrollOverlay;
}

GameplayUiController::SpellbookState &GameplayUiController::spellbook()
{
    return resolvedState().spellbook;
}

const GameplayUiController::SpellbookState &GameplayUiController::spellbook() const
{
    return resolvedState().spellbook;
}

GameplayUiController::RestScreenState &GameplayUiController::restScreen()
{
    return resolvedState().restScreen;
}

const GameplayUiController::RestScreenState &GameplayUiController::restScreen() const
{
    return resolvedState().restScreen;
}

GameplayUiController::MenuScreenState &GameplayUiController::menuScreen()
{
    return resolvedState().menuScreen;
}

const GameplayUiController::MenuScreenState &GameplayUiController::menuScreen() const
{
    return resolvedState().menuScreen;
}

GameplayUiController::ControlsScreenState &GameplayUiController::controlsScreen()
{
    return resolvedState().controlsScreen;
}

const GameplayUiController::ControlsScreenState &GameplayUiController::controlsScreen() const
{
    return resolvedState().controlsScreen;
}

GameplayUiController::KeyboardScreenState &GameplayUiController::keyboardScreen()
{
    return resolvedState().keyboardScreen;
}

const GameplayUiController::KeyboardScreenState &GameplayUiController::keyboardScreen() const
{
    return resolvedState().keyboardScreen;
}

GameplayUiController::VideoOptionsScreenState &GameplayUiController::videoOptionsScreen()
{
    return resolvedState().videoOptionsScreen;
}

const GameplayUiController::VideoOptionsScreenState &GameplayUiController::videoOptionsScreen() const
{
    return resolvedState().videoOptionsScreen;
}

GameplayUiController::SaveGameScreenState &GameplayUiController::saveGameScreen()
{
    return resolvedState().saveGameScreen;
}

const GameplayUiController::SaveGameScreenState &GameplayUiController::saveGameScreen() const
{
    return resolvedState().saveGameScreen;
}

GameplayUiController::LoadGameScreenState &GameplayUiController::loadGameScreen()
{
    return resolvedState().loadGameScreen;
}

const GameplayUiController::LoadGameScreenState &GameplayUiController::loadGameScreen() const
{
    return resolvedState().loadGameScreen;
}

GameplayUiController::JournalScreenState &GameplayUiController::journalScreen()
{
    return resolvedState().journalScreen;
}

const GameplayUiController::JournalScreenState &GameplayUiController::journalScreen() const
{
    return resolvedState().journalScreen;
}

GameplayUiController::InventoryNestedOverlayState &GameplayUiController::inventoryNestedOverlay()
{
    return resolvedState().inventoryNestedOverlay;
}

const GameplayUiController::InventoryNestedOverlayState &GameplayUiController::inventoryNestedOverlay() const
{
    return resolvedState().inventoryNestedOverlay;
}

GameplayUiController::HouseShopOverlayState &GameplayUiController::houseShopOverlay()
{
    return resolvedState().houseShopOverlay;
}

const GameplayUiController::HouseShopOverlayState &GameplayUiController::houseShopOverlay() const
{
    return resolvedState().houseShopOverlay;
}

GameplayUiController::HouseBankState &GameplayUiController::houseBankState()
{
    return resolvedState().houseBankState;
}

const GameplayUiController::HouseBankState &GameplayUiController::houseBankState() const
{
    return resolvedState().houseBankState;
}

GameplayUiController::UtilitySpellOverlayState &GameplayUiController::utilitySpellOverlay()
{
    return resolvedState().utilitySpellOverlay;
}

const GameplayUiController::UtilitySpellOverlayState &GameplayUiController::utilitySpellOverlay() const
{
    return resolvedState().utilitySpellOverlay;
}

GameplayUiController::StatusBarState &GameplayUiController::statusBar()
{
    return resolvedState().statusBar;
}

const GameplayUiController::StatusBarState &GameplayUiController::statusBar() const
{
    return resolvedState().statusBar;
}

GameplayUiController::EventDialogState &GameplayUiController::eventDialog()
{
    return resolvedState().eventDialog;
}

const GameplayUiController::EventDialogState &GameplayUiController::eventDialog() const
{
    return resolvedState().eventDialog;
}

void GameplayUiController::openSpellbook(SpellbookSchool school)
{
    State &state = resolvedState();
    state.spellbook = {};
    state.spellInspectOverlay = {};
    state.spellbook.active = true;
    state.spellbook.school = school;
}

void GameplayUiController::closeSpellbook()
{
    State &state = resolvedState();
    state.spellbook = {};
    state.spellInspectOverlay = {};
}

void GameplayUiController::closeReadableScrollOverlay()
{
    resolvedState().readableScrollOverlay = {};
}

void GameplayUiController::openInventoryNestedOverlay(InventoryNestedOverlayMode mode, uint32_t houseId)
{
    if (mode == InventoryNestedOverlayMode::None)
    {
        closeInventoryNestedOverlay();
        return;
    }

    State &state = resolvedState();
    closeHouseShopOverlay();
    state.inventoryNestedOverlay.active = true;
    state.inventoryNestedOverlay.mode = mode;
    state.inventoryNestedOverlay.houseId = houseId;
}

void GameplayUiController::closeInventoryNestedOverlay()
{
    resolvedState().inventoryNestedOverlay = {};
}

void GameplayUiController::openHouseShopOverlay(uint32_t houseId, HouseShopMode mode)
{
    if (mode == HouseShopMode::None || houseId == 0)
    {
        closeHouseShopOverlay();
        return;
    }

    State &state = resolvedState();
    closeInventoryNestedOverlay();
    state.houseShopOverlay.active = true;
    state.houseShopOverlay.houseId = houseId;
    state.houseShopOverlay.mode = mode;
}

void GameplayUiController::closeHouseShopOverlay()
{
    resolvedState().houseShopOverlay = {};
}

void GameplayUiController::openUtilitySpellOverlay(
    UtilitySpellOverlayMode mode,
    uint32_t spellId,
    size_t casterMemberIndex,
    bool lloydRecallMode)
{
    State &state = resolvedState();
    state.utilitySpellOverlay.active = true;
    state.utilitySpellOverlay.mode = mode;
    state.utilitySpellOverlay.spellId = spellId;
    state.utilitySpellOverlay.casterMemberIndex = casterMemberIndex;
    state.utilitySpellOverlay.lloydRecallMode = lloydRecallMode;
}

void GameplayUiController::closeUtilitySpellOverlay()
{
    resolvedState().utilitySpellOverlay = {};
}

void GameplayUiController::beginHouseBankInput(uint32_t houseId, HouseBankInputMode mode)
{
    if (houseId == 0 || mode == HouseBankInputMode::None)
    {
        clearHouseBankState();
        return;
    }

    State &state = resolvedState();
    closeHouseShopOverlay();
    closeInventoryNestedOverlay();
    state.houseBankState.houseId = houseId;
    state.houseBankState.inputMode = mode;
    state.houseBankState.inputText.clear();
}

void GameplayUiController::clearHouseBankState()
{
    resolvedState().houseBankState = {};
}

void GameplayUiController::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    if (text.empty())
    {
        return;
    }

    State &state = resolvedState();
    state.statusBar.eventText = text;
    state.statusBar.eventRemainingSeconds = std::max(0.0f, durationSeconds);
}

void GameplayUiController::updateStatusBarEvent(float deltaSeconds)
{
    State &state = resolvedState();

    if (state.statusBar.eventRemainingSeconds <= 0.0f)
    {
        return;
    }

    state.statusBar.eventRemainingSeconds =
        std::max(0.0f, state.statusBar.eventRemainingSeconds - deltaSeconds);

    if (state.statusBar.eventRemainingSeconds <= 0.0f)
    {
        state.statusBar.eventText.clear();
    }
}

void GameplayUiController::clearEventDialog()
{
    resolvedState().eventDialog = {};
}

void GameplayUiController::setEventDialogContent(const EventDialogContent &content)
{
    resolvedState().eventDialog.content = content;
}
}
