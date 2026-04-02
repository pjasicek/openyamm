#pragma once

#include "engine/AssetFileSystem.h"
#include "game/party/CharacterState.h"
#include "game/events/EventDialogContent.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>

namespace OpenYAMM::Game
{
class GameplayUiController
{
public:
    enum class CharacterPage
    {
        Stats,
        Skills,
        Inventory,
        Awards
    };

    enum class SpellbookSchool
    {
        Fire,
        Air,
        Water,
        Earth,
        Spirit,
        Mind,
        Body,
        Light,
        Dark,
        DarkElf,
        Vampire,
        Dragon
    };

    enum class ItemInspectSourceType
    {
        None,
        Inventory,
        Equipment,
        WorldItem
    };

    enum class HouseShopMode
    {
        None,
        BuyStandard,
        BuySpecial,
        BuySpellbooks
    };

    enum class InventoryNestedOverlayMode
    {
        None,
        ChestTransfer,
        ShopSell,
        ShopIdentify,
        ShopRepair
    };

    enum class HouseBankInputMode : uint8_t
    {
        None = 0,
        Deposit,
        Withdraw,
    };

    struct HeldInventoryItemState
    {
        bool active = false;
        InventoryItem item = {};
        uint8_t grabCellOffsetX = 0;
        uint8_t grabCellOffsetY = 0;
        float grabOffsetX = 0.0f;
        float grabOffsetY = 0.0f;
    };

    struct ItemInspectOverlayState
    {
        bool active = false;
        uint32_t objectDescriptionId = 0;
        bool hasItemState = false;
        InventoryItem itemState = {};
        ItemInspectSourceType sourceType = ItemInspectSourceType::None;
        size_t sourceMemberIndex = 0;
        uint8_t sourceGridX = 0;
        uint8_t sourceGridY = 0;
        EquipmentSlot sourceEquipmentSlot = EquipmentSlot::MainHand;
        size_t sourceWorldItemIndex = 0;
        bool hasValueOverride = false;
        int valueOverride = 0;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceWidth = 0.0f;
        float sourceHeight = 0.0f;
    };

    struct CharacterInspectMasteryLine
    {
        std::string text;
        int availability = 0;
        bool visible = false;
    };

    struct CharacterInspectOverlayState
    {
        bool active = false;
        std::string title;
        std::string body;
        CharacterInspectMasteryLine expert = {};
        CharacterInspectMasteryLine master = {};
        CharacterInspectMasteryLine grandmaster = {};
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceWidth = 0.0f;
        float sourceHeight = 0.0f;
    };

    struct BuffInspectOverlayState
    {
        bool active = false;
        std::string title;
        std::string body;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceWidth = 0.0f;
        float sourceHeight = 0.0f;
    };

    struct CharacterDetailOverlayState
    {
        bool active = false;
        std::string title;
        std::string body;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceWidth = 0.0f;
        float sourceHeight = 0.0f;
    };

    struct ActorInspectOverlayState
    {
        bool active = false;
        size_t runtimeActorIndex = static_cast<size_t>(-1);
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceWidth = 0.0f;
        float sourceHeight = 0.0f;
    };

    struct SpellInspectOverlayState
    {
        bool active = false;
        uint32_t spellId = 0;
        std::string title;
        std::string body;
        std::string normal;
        std::string expert;
        std::string master;
        std::string grandmaster;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceWidth = 0.0f;
        float sourceHeight = 0.0f;
    };

    struct ReadableScrollOverlayState
    {
        bool active = false;
        std::string title;
        std::string body;
    };

    struct SpellbookState
    {
        bool active = false;
        SpellbookSchool school = SpellbookSchool::Fire;
        uint32_t selectedSpellId = 0;
    };

    struct CharacterScreenState
    {
        bool open = false;
        bool dollJewelryOverlayOpen = false;
        CharacterPage page = CharacterPage::Inventory;
    };

    struct InventoryNestedOverlayState
    {
        bool active = false;
        InventoryNestedOverlayMode mode = InventoryNestedOverlayMode::None;
        uint32_t houseId = 0;
    };

    struct HouseShopOverlayState
    {
        bool active = false;
        uint32_t houseId = 0;
        HouseShopMode mode = HouseShopMode::None;
    };

    struct HouseBankState
    {
        uint32_t houseId = 0;
        HouseBankInputMode inputMode = HouseBankInputMode::None;
        std::string inputText;
        bool transactionPerformed = false;

        bool inputActive() const
        {
            return inputMode != HouseBankInputMode::None;
        }
    };

    struct StatusBarState
    {
        std::string hoverText;
        std::string eventText;
        float eventRemainingSeconds = 0.0f;
    };

    struct EventDialogState
    {
        size_t selectionIndex = 0;
        EventDialogContent content = {};
    };

    struct State
    {
        CharacterScreenState characterScreen = {};
        HeldInventoryItemState heldInventoryItem = {};
        ItemInspectOverlayState itemInspectOverlay = {};
        CharacterInspectOverlayState characterInspectOverlay = {};
        BuffInspectOverlayState buffInspectOverlay = {};
        CharacterDetailOverlayState characterDetailOverlay = {};
        ActorInspectOverlayState actorInspectOverlay = {};
        SpellInspectOverlayState spellInspectOverlay = {};
        ReadableScrollOverlayState readableScrollOverlay = {};
        SpellbookState spellbook = {};
        InventoryNestedOverlayState inventoryNestedOverlay = {};
        HouseShopOverlayState houseShopOverlay = {};
        HouseBankState houseBankState = {};
        StatusBarState statusBar = {};
        EventDialogState eventDialog = {};
    };

    using LayoutLoader = std::function<bool(const std::string &)>;

    bool loadGameplayLayouts(const Engine::AssetFileSystem &assetFileSystem, const LayoutLoader &loader) const;
    void clearRuntimeState();

    State &state();
    const State &state() const;

    CharacterScreenState &characterScreen();
    const CharacterScreenState &characterScreen() const;

    HeldInventoryItemState &heldInventoryItem();
    const HeldInventoryItemState &heldInventoryItem() const;

    ItemInspectOverlayState &itemInspectOverlay();
    const ItemInspectOverlayState &itemInspectOverlay() const;

    CharacterInspectOverlayState &characterInspectOverlay();
    const CharacterInspectOverlayState &characterInspectOverlay() const;

    BuffInspectOverlayState &buffInspectOverlay();
    const BuffInspectOverlayState &buffInspectOverlay() const;

    CharacterDetailOverlayState &characterDetailOverlay();
    const CharacterDetailOverlayState &characterDetailOverlay() const;

    ActorInspectOverlayState &actorInspectOverlay();
    const ActorInspectOverlayState &actorInspectOverlay() const;

    SpellInspectOverlayState &spellInspectOverlay();
    const SpellInspectOverlayState &spellInspectOverlay() const;

    ReadableScrollOverlayState &readableScrollOverlay();
    const ReadableScrollOverlayState &readableScrollOverlay() const;

    SpellbookState &spellbook();
    const SpellbookState &spellbook() const;

    InventoryNestedOverlayState &inventoryNestedOverlay();
    const InventoryNestedOverlayState &inventoryNestedOverlay() const;

    HouseShopOverlayState &houseShopOverlay();
    const HouseShopOverlayState &houseShopOverlay() const;

    HouseBankState &houseBankState();
    const HouseBankState &houseBankState() const;

    StatusBarState &statusBar();
    const StatusBarState &statusBar() const;

    EventDialogState &eventDialog();
    const EventDialogState &eventDialog() const;

    void openSpellbook(SpellbookSchool school = SpellbookSchool::Fire);
    void closeSpellbook();
    void closeReadableScrollOverlay();
    void openInventoryNestedOverlay(InventoryNestedOverlayMode mode, uint32_t houseId = 0);
    void closeInventoryNestedOverlay();
    void openHouseShopOverlay(uint32_t houseId, HouseShopMode mode);
    void closeHouseShopOverlay();
    void beginHouseBankInput(uint32_t houseId, HouseBankInputMode mode);
    void clearHouseBankState();
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void updateStatusBarEvent(float deltaSeconds);
    void clearEventDialog();
    void setEventDialogContent(const EventDialogContent &content);

private:
    State m_state;
};
}
