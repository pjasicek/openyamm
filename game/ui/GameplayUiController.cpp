#include "game/ui/GameplayUiController.h"

#include <array>
#include <algorithm>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
const std::array<std::string, 14> GameplayLayoutFiles = {
    "Data/ui/gameplay/gameplay.yml",
    "Data/ui/gameplay/chest.yml",
    "Data/ui/gameplay/dialogue.yml",
    "Data/ui/gameplay/character.yml",
    "Data/ui/gameplay/adventurers_inn.yml",
    "Data/ui/gameplay/spellbook.yml",
    "Data/ui/gameplay/rest.yml",
    "Data/ui/gameplay/journal.yml",
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
    m_state = {};
}

GameplayUiController::State &GameplayUiController::state()
{
    return m_state;
}

const GameplayUiController::State &GameplayUiController::state() const
{
    return m_state;
}

GameplayUiController::CharacterScreenState &GameplayUiController::characterScreen()
{
    return m_state.characterScreen;
}

const GameplayUiController::CharacterScreenState &GameplayUiController::characterScreen() const
{
    return m_state.characterScreen;
}

GameplayUiController::HeldInventoryItemState &GameplayUiController::heldInventoryItem()
{
    return m_state.heldInventoryItem;
}

const GameplayUiController::HeldInventoryItemState &GameplayUiController::heldInventoryItem() const
{
    return m_state.heldInventoryItem;
}

GameplayUiController::ItemInspectOverlayState &GameplayUiController::itemInspectOverlay()
{
    return m_state.itemInspectOverlay;
}

const GameplayUiController::ItemInspectOverlayState &GameplayUiController::itemInspectOverlay() const
{
    return m_state.itemInspectOverlay;
}

GameplayUiController::CharacterInspectOverlayState &GameplayUiController::characterInspectOverlay()
{
    return m_state.characterInspectOverlay;
}

const GameplayUiController::CharacterInspectOverlayState &GameplayUiController::characterInspectOverlay() const
{
    return m_state.characterInspectOverlay;
}

GameplayUiController::BuffInspectOverlayState &GameplayUiController::buffInspectOverlay()
{
    return m_state.buffInspectOverlay;
}

const GameplayUiController::BuffInspectOverlayState &GameplayUiController::buffInspectOverlay() const
{
    return m_state.buffInspectOverlay;
}

GameplayUiController::CharacterDetailOverlayState &GameplayUiController::characterDetailOverlay()
{
    return m_state.characterDetailOverlay;
}

const GameplayUiController::CharacterDetailOverlayState &GameplayUiController::characterDetailOverlay() const
{
    return m_state.characterDetailOverlay;
}

GameplayUiController::ActorInspectOverlayState &GameplayUiController::actorInspectOverlay()
{
    return m_state.actorInspectOverlay;
}

const GameplayUiController::ActorInspectOverlayState &GameplayUiController::actorInspectOverlay() const
{
    return m_state.actorInspectOverlay;
}

GameplayUiController::SpellInspectOverlayState &GameplayUiController::spellInspectOverlay()
{
    return m_state.spellInspectOverlay;
}

const GameplayUiController::SpellInspectOverlayState &GameplayUiController::spellInspectOverlay() const
{
    return m_state.spellInspectOverlay;
}

GameplayUiController::ReadableScrollOverlayState &GameplayUiController::readableScrollOverlay()
{
    return m_state.readableScrollOverlay;
}

const GameplayUiController::ReadableScrollOverlayState &GameplayUiController::readableScrollOverlay() const
{
    return m_state.readableScrollOverlay;
}

GameplayUiController::SpellbookState &GameplayUiController::spellbook()
{
    return m_state.spellbook;
}

const GameplayUiController::SpellbookState &GameplayUiController::spellbook() const
{
    return m_state.spellbook;
}

GameplayUiController::RestScreenState &GameplayUiController::restScreen()
{
    return m_state.restScreen;
}

const GameplayUiController::RestScreenState &GameplayUiController::restScreen() const
{
    return m_state.restScreen;
}

GameplayUiController::JournalScreenState &GameplayUiController::journalScreen()
{
    return m_state.journalScreen;
}

const GameplayUiController::JournalScreenState &GameplayUiController::journalScreen() const
{
    return m_state.journalScreen;
}

GameplayUiController::InventoryNestedOverlayState &GameplayUiController::inventoryNestedOverlay()
{
    return m_state.inventoryNestedOverlay;
}

const GameplayUiController::InventoryNestedOverlayState &GameplayUiController::inventoryNestedOverlay() const
{
    return m_state.inventoryNestedOverlay;
}

GameplayUiController::HouseShopOverlayState &GameplayUiController::houseShopOverlay()
{
    return m_state.houseShopOverlay;
}

const GameplayUiController::HouseShopOverlayState &GameplayUiController::houseShopOverlay() const
{
    return m_state.houseShopOverlay;
}

GameplayUiController::HouseBankState &GameplayUiController::houseBankState()
{
    return m_state.houseBankState;
}

const GameplayUiController::HouseBankState &GameplayUiController::houseBankState() const
{
    return m_state.houseBankState;
}

GameplayUiController::StatusBarState &GameplayUiController::statusBar()
{
    return m_state.statusBar;
}

const GameplayUiController::StatusBarState &GameplayUiController::statusBar() const
{
    return m_state.statusBar;
}

GameplayUiController::EventDialogState &GameplayUiController::eventDialog()
{
    return m_state.eventDialog;
}

const GameplayUiController::EventDialogState &GameplayUiController::eventDialog() const
{
    return m_state.eventDialog;
}

void GameplayUiController::openSpellbook(SpellbookSchool school)
{
    m_state.spellbook = {};
    m_state.spellInspectOverlay = {};
    m_state.spellbook.active = true;
    m_state.spellbook.school = school;
}

void GameplayUiController::closeSpellbook()
{
    m_state.spellbook = {};
    m_state.spellInspectOverlay = {};
}

void GameplayUiController::closeReadableScrollOverlay()
{
    m_state.readableScrollOverlay = {};
}

void GameplayUiController::openInventoryNestedOverlay(InventoryNestedOverlayMode mode, uint32_t houseId)
{
    if (mode == InventoryNestedOverlayMode::None)
    {
        closeInventoryNestedOverlay();
        return;
    }

    closeHouseShopOverlay();
    m_state.inventoryNestedOverlay.active = true;
    m_state.inventoryNestedOverlay.mode = mode;
    m_state.inventoryNestedOverlay.houseId = houseId;
}

void GameplayUiController::closeInventoryNestedOverlay()
{
    m_state.inventoryNestedOverlay = {};
}

void GameplayUiController::openHouseShopOverlay(uint32_t houseId, HouseShopMode mode)
{
    if (mode == HouseShopMode::None || houseId == 0)
    {
        closeHouseShopOverlay();
        return;
    }

    closeInventoryNestedOverlay();
    m_state.houseShopOverlay.active = true;
    m_state.houseShopOverlay.houseId = houseId;
    m_state.houseShopOverlay.mode = mode;
}

void GameplayUiController::closeHouseShopOverlay()
{
    m_state.houseShopOverlay = {};
}

void GameplayUiController::beginHouseBankInput(uint32_t houseId, HouseBankInputMode mode)
{
    if (houseId == 0 || mode == HouseBankInputMode::None)
    {
        clearHouseBankState();
        return;
    }

    closeHouseShopOverlay();
    closeInventoryNestedOverlay();
    m_state.houseBankState.houseId = houseId;
    m_state.houseBankState.inputMode = mode;
    m_state.houseBankState.inputText.clear();
}

void GameplayUiController::clearHouseBankState()
{
    m_state.houseBankState = {};
}

void GameplayUiController::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    if (text.empty())
    {
        return;
    }

    m_state.statusBar.eventText = text;
    m_state.statusBar.eventRemainingSeconds = std::max(0.0f, durationSeconds);
}

void GameplayUiController::updateStatusBarEvent(float deltaSeconds)
{
    if (m_state.statusBar.eventRemainingSeconds <= 0.0f)
    {
        return;
    }

    m_state.statusBar.eventRemainingSeconds =
        std::max(0.0f, m_state.statusBar.eventRemainingSeconds - deltaSeconds);

    if (m_state.statusBar.eventRemainingSeconds <= 0.0f)
    {
        m_state.statusBar.eventText.clear();
    }
}

void GameplayUiController::clearEventDialog()
{
    m_state.eventDialog = {};
}

void GameplayUiController::setEventDialogContent(const EventDialogContent &content)
{
    m_state.eventDialog.content = content;
}
}
