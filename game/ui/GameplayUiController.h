#pragma once

#include "engine/AssetFileSystem.h"
#include "game/app/KeyboardBindings.h"
#include "game/party/CharacterState.h"
#include "game/events/EventDialogContent.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

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

    enum class CharacterScreenSource
    {
        Party,
        AdventurersInn
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
        WorldItem,
        Chest,
        Corpse
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

    enum class RestMode
    {
        None,
        Wait,
        Heal
    };

    enum class JournalView : uint8_t
    {
        Map = 0,
        Quests,
        Story,
        Notes
    };

    enum class JournalNotesCategory : uint8_t
    {
        Potion = 0,
        Fountain,
        Obelisk,
        Seer,
        Misc,
        Trainer
    };

    enum class HouseBankInputMode : uint8_t
    {
        None = 0,
        Deposit,
        Withdraw,
    };

    enum class UtilitySpellOverlayMode : uint8_t
    {
        None = 0,
        InventoryTarget,
        TownPortal,
        LloydsBeacon,
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
        size_t sourceLootItemIndex = 0;
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
        struct ActiveSpellLine
        {
            std::string name;
            std::string duration;
        };

        bool active = false;
        std::string title;
        std::string body;
        std::string portraitTextureName;
        std::string hitPointsText;
        std::string spellPointsText;
        std::string conditionText;
        std::string quickSpellText;
        std::vector<ActiveSpellLine> activeSpells;
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

    struct RestScreenState
    {
        bool active = false;
        RestMode mode = RestMode::None;
        float totalMinutes = 0.0f;
        float remainingMinutes = 0.0f;
        float hourglassElapsedSeconds = 0.0f;
    };

    struct MenuScreenState
    {
        bool active = false;
        bool newGameConfirmationArmed = false;
        bool quitConfirmationArmed = false;
        bool bottomBarTextUseWhite = false;
        std::string bottomBarText;
    };

    struct ControlsScreenState
    {
        bool active = false;
    };

    struct KeyboardScreenState
    {
        bool active = false;
        KeyboardBindingPage page = KeyboardBindingPage::Page1;
        bool waitingForBinding = false;
        KeyboardAction pendingAction = KeyboardAction::Forward;
    };

    struct VideoOptionsScreenState
    {
        bool active = false;
    };

    struct SaveSlotSummary
    {
        std::filesystem::path path;
        std::string fileLabel;
        std::string locationName;
        std::string weekdayClockText;
        std::string dateText;
        bool populated = false;
        int previewWidth = 0;
        int previewHeight = 0;
        std::vector<uint8_t> previewPixelsBgra;
    };

    struct SaveGameScreenState
    {
        bool active = false;
        size_t selectedIndex = 0;
        size_t scrollOffset = 0;
        bool editActive = false;
        size_t editSlotIndex = 0;
        std::string editBuffer;
        std::vector<SaveSlotSummary> slots;
    };

    struct LoadGameScreenState
    {
        bool active = false;
        size_t selectedIndex = 0;
        size_t scrollOffset = 0;
        std::vector<SaveSlotSummary> slots;
    };

    struct JournalScreenState
    {
        bool active = false;
        JournalView view = JournalView::Map;
        JournalNotesCategory notesCategory = JournalNotesCategory::Potion;
        size_t questPage = 0;
        size_t storyPage = 0;
        size_t notesPage = 0;
        float mapCenterX = 0.0f;
        float mapCenterY = 0.0f;
        int mapZoomStep = 0;
        bool mapDragActive = false;
        float mapDragStartMouseX = 0.0f;
        float mapDragStartMouseY = 0.0f;
        float mapDragStartCenterX = 0.0f;
        float mapDragStartCenterY = 0.0f;
        float hoverAnimationElapsedSeconds = 0.0f;
        bool cachedMapValid = false;
        int cachedMapWidth = 0;
        int cachedMapHeight = 0;
        int cachedMapZoomStep = 0;
        float cachedMapCenterX = 0.0f;
        float cachedMapCenterY = 0.0f;
    };

    struct CharacterScreenState
    {
        bool open = false;
        bool dollJewelryOverlayOpen = false;
        bool adventurersInnRosterOverlayOpen = false;
        CharacterPage page = CharacterPage::Inventory;
        CharacterScreenSource source = CharacterScreenSource::Party;
        size_t sourceIndex = 0;
        size_t adventurersInnScrollOffset = 0;
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

    struct UtilitySpellOverlayState
    {
        bool active = false;
        UtilitySpellOverlayMode mode = UtilitySpellOverlayMode::None;
        uint32_t spellId = 0;
        size_t casterMemberIndex = 0;
        bool lloydRecallMode = false;
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
        RestScreenState restScreen = {};
        MenuScreenState menuScreen = {};
        ControlsScreenState controlsScreen = {};
        KeyboardScreenState keyboardScreen = {};
        VideoOptionsScreenState videoOptionsScreen = {};
        SaveGameScreenState saveGameScreen = {};
        LoadGameScreenState loadGameScreen = {};
        JournalScreenState journalScreen = {};
        InventoryNestedOverlayState inventoryNestedOverlay = {};
        HouseShopOverlayState houseShopOverlay = {};
        HouseBankState houseBankState = {};
        UtilitySpellOverlayState utilitySpellOverlay = {};
        StatusBarState statusBar = {};
        EventDialogState eventDialog = {};
    };

    using LayoutLoader = std::function<bool(const std::string &)>;

    bool loadGameplayLayouts(const Engine::AssetFileSystem &assetFileSystem, const LayoutLoader &loader) const;
    void bindExternalState(State *pState);
    void clearExternalStateBinding();
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

    UtilitySpellOverlayState &utilitySpellOverlay();
    const UtilitySpellOverlayState &utilitySpellOverlay() const;

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
    void openUtilitySpellOverlay(
        UtilitySpellOverlayMode mode,
        uint32_t spellId,
        size_t casterMemberIndex,
        bool lloydRecallMode = false);
    void closeUtilitySpellOverlay();
    void beginHouseBankInput(uint32_t houseId, HouseBankInputMode mode);
    void clearHouseBankState();
    void setStatusBarEvent(const std::string &text, float durationSeconds = 2.0f);
    void updateStatusBarEvent(float deltaSeconds);
    void clearEventDialog();
    void setEventDialogContent(const EventDialogContent &content);

private:
    State &resolvedState();
    const State &resolvedState() const;

    State m_state;
    State *m_pExternalState = nullptr;
};
}
