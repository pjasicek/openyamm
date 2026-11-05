#pragma once

#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/Party.h"
#include "game/party/QuickItemSlot.h"
#include "game/ui/GameplayUiController.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class GameplayHudScreenState
{
    Gameplay,
    Dialogue,
    Character,
    TownPortal,
    LloydsBeacon,
    Chest,
    Spellbook,
    Rest,
    Menu,
    Controls,
    Keyboard,
    VideoOptions,
    SaveGame,
    LoadGame,
    Journal,
    QuickReference
};

inline bool activeEventDialogPreservesGameplayHud(const EventDialogContent &activeEventDialog)
{
    return activeEventDialog.isActive
        && activeEventDialog.presentation == EventDialogPresentation::Mm9Rude;
}

inline bool gameplayHudScreenFullyOccludesWorld(
    GameplayHudScreenState state,
    const EventDialogContent &activeEventDialog)
{
    // The native pause panel leaves the game visible, including its first capture frame.
    if (state == GameplayHudScreenState::Gameplay || state == GameplayHudScreenState::Menu)
    {
        return false;
    }

    if (state == GameplayHudScreenState::Dialogue)
    {
        return activeEventDialog.isActive
            && activeEventDialog.isHouseDialog
            && activeEventDialog.scenePolicy != DialogueScenePolicy::LiveGameplay;
    }

    return true;
}

inline bool activeEventDialogShowsVideoArea(
    const EventDialogContent &activeEventDialog,
    bool hasHostHouseEntry)
{
    return activeEventDialog.scenePolicy != DialogueScenePolicy::LiveGameplay
        && (hasHostHouseEntry || !activeEventDialog.videoName.empty());
}

inline bool activeEventDialogAllowsHouseVideoPlayback(const EventDialogContent &activeEventDialog)
{
    return activeEventDialog.scenePolicy != DialogueScenePolicy::LiveGameplay;
}

inline GameplayHudScreenState resolveGameplayHudScreenState(
    const GameplayUiController &uiController,
    const EventDialogContent &activeEventDialog,
    const IGameplayWorldRuntime *pWorldRuntime)
{
    if (activeEventDialog.isActive)
    {
        return GameplayHudScreenState::Dialogue;
    }

    if (uiController.journalScreen().active)
    {
        return GameplayHudScreenState::Journal;
    }

    if (uiController.quickReferenceScreen().active)
    {
        return GameplayHudScreenState::QuickReference;
    }

    if (uiController.restScreen().active)
    {
        return GameplayHudScreenState::Rest;
    }

    if (uiController.videoOptionsScreen().active)
    {
        return GameplayHudScreenState::VideoOptions;
    }

    if (uiController.keyboardScreen().active)
    {
        return GameplayHudScreenState::Keyboard;
    }

    if (uiController.controlsScreen().active)
    {
        return GameplayHudScreenState::Controls;
    }

    if (uiController.menuScreen().active)
    {
        return GameplayHudScreenState::Menu;
    }

    if (uiController.saveGameScreen().active)
    {
        return GameplayHudScreenState::SaveGame;
    }

    if (uiController.loadGameScreen().active)
    {
        return GameplayHudScreenState::LoadGame;
    }

    if (uiController.utilitySpellOverlay().active)
    {
        switch (uiController.utilitySpellOverlay().mode)
        {
            case GameplayUiController::UtilitySpellOverlayMode::TownPortal:
            case GameplayUiController::UtilitySpellOverlayMode::DimensionDoor:
                return GameplayHudScreenState::TownPortal;
            case GameplayUiController::UtilitySpellOverlayMode::LloydsBeacon:
                return GameplayHudScreenState::LloydsBeacon;
            default:
                break;
        }
    }

    if (uiController.characterScreen().open)
    {
        return GameplayHudScreenState::Character;
    }

    if (uiController.spellbook().active)
    {
        return GameplayHudScreenState::Spellbook;
    }

    if (pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr))
    {
        return GameplayHudScreenState::Chest;
    }

    return GameplayHudScreenState::Gameplay;
}

struct GameplayResolvedHudLayoutElement
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float scale = 1.0f;
};

struct GameplayHudTextureHandle
{
    std::string textureName;
    int width = 0;
    int height = 0;
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
};

struct GameplayHudFontHandle
{
    std::string fontName;
    int fontHeight = 0;
    bgfx::TextureHandle mainTextureHandle = BGFX_INVALID_HANDLE;
    bgfx::TextureHandle shadowTextureHandle = BGFX_INVALID_HANDLE;
};

struct GameplayHudBatchQuad
{
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    float x2 = 0.0f;
    float y2 = 0.0f;
    bool line = false;
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 1.0f;
    float v1 = 1.0f;
    bool clipped = false;
    uint16_t scissorX = 0;
    uint16_t scissorY = 0;
    uint16_t scissorWidth = 0;
    uint16_t scissorHeight = 0;
    // Multiplies the texture; runs of quads with a tint draw with the HUD tint program.
    uint32_t tintAbgr = 0xffffffffu;
};

// One layer of HUD text: a font atlas and the colour its glyphs are multiplied by at draw time.
struct GameplayHudFontLayer
{
    bgfx::TextureHandle textureHandle = BGFX_INVALID_HANDLE;
    uint32_t tintAbgr = 0xffffffffu;

    GameplayHudFontLayer() = default;

    // An atlas drawn in its own colours, such as a font's shadow layer.
    GameplayHudFontLayer(bgfx::TextureHandle handle, uint32_t tint = 0xffffffffu)
        : textureHandle(handle)
        , tintAbgr(tint)
    {
    }
};

enum class GameplayMinimapMarkerType
{
    FriendlyActor,
    HostileActor,
    CorpseActor,
    WorldItem,
    Projectile,
    Decoration
};

struct GameplayMinimapState
{
    std::string textureName;
    bool vectorBackground = false;
    uint32_t backgroundColorAbgr = 0xff780000u;
    float zoom = 512.0f;
    float zoomWidth = 0.0f;
    float zoomHeight = 0.0f;
    float u0 = 0.0f;
    float v0 = 0.0f;
    float uSpan = 1.0f;
    float vSpan = 1.0f;
    float partyU = 0.5f;
    float partyV = 0.5f;
    float worldMinX = -32768.0f;
    float worldMaxX = 32768.0f;
    float worldMinY = -32768.0f;
    float worldMaxY = 32768.0f;
    bool flipU = false;
    bool flipV = true;
    bool revealEntireMap = false;
    bool wizardEyeActive = false;
    bool wizardEyeShowsExpertObjects = false;
    bool wizardEyeShowsDecorations = false;
};

struct GameplayMinimapLineState
{
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 0.0f;
    float v1 = 0.0f;
    uint32_t colorAbgr = 0xffffffffu;
};

struct GameplayMinimapMarkerState
{
    GameplayMinimapMarkerType type = GameplayMinimapMarkerType::FriendlyActor;
    float u = 0.0f;
    float v = 0.0f;
};

enum class GameplayDialoguePointerTargetType
{
    None,
    Action,
    CloseButton
};

struct GameplayDialoguePointerTarget
{
    GameplayDialoguePointerTargetType type = GameplayDialoguePointerTargetType::None;
    size_t index = 0;

    bool operator==(const GameplayDialoguePointerTarget &other) const = default;
};

enum class GameplayChestPointerTargetType
{
    None,
    TakeAllButton,
    TakeGoldButton,
    InventoryButton,
    CloseButton
};

struct GameplayChestPointerTarget
{
    GameplayChestPointerTargetType type = GameplayChestPointerTargetType::None;

    bool operator==(const GameplayChestPointerTarget &other) const = default;
};

enum class GameplaySpellbookPointerTargetType
{
    None,
    SchoolButton,
    SpellButton,
    CloseButton,
    QuickCastButton,
    AttackCastButton,
    // One of MMMerge's four extra quick spell slots (ExtraQuickSpells.lua); `slot` says which.
    QuickSpellSlotButton
};

struct GameplaySpellbookPointerTarget
{
    GameplaySpellbookPointerTargetType type = GameplaySpellbookPointerTargetType::None;
    GameplayUiController::SpellbookSchool school = GameplayUiController::SpellbookSchool::Fire;
    uint32_t spellId = 0;
    size_t slot = 0;

    bool operator==(const GameplaySpellbookPointerTarget &other) const = default;
};

struct GameplayTownPortalDestination
{
    std::string id;
    std::string label;
    std::string iconTextureName;
    std::string mapName;
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
    std::optional<int32_t> directionDegrees;
    bool useMapStartPosition = false;
    uint32_t unlockQBitId = 0;
    int32_t iconX = 0;
    int32_t iconY = 0;
    uint32_t iconWidth = 0;
    uint32_t iconHeight = 0;
    int32_t hitX = 0;
    int32_t hitY = 0;
    uint32_t hitWidth = 0;
    uint32_t hitHeight = 0;
};

enum class GameplayUtilitySpellPointerTargetType
{
    None,
    Close,
    TownPortalDestination,
    LloydSetTab,
    LloydRecallTab,
    LloydSlot,
};

struct GameplayUtilitySpellPointerTarget
{
    GameplayUtilitySpellPointerTargetType type = GameplayUtilitySpellPointerTargetType::None;
    size_t index = 0;

    bool operator==(const GameplayUtilitySpellPointerTarget &other) const = default;
};

enum class GameplayCharacterPointerTargetType
{
    None,
    PageButton,
    StatsButton,
    SkillsButton,
    InventoryButton,
    AwardsButton,
    ExitButton,
    DismissButton,
    AlchemyButton,
    InventorySortButton,
    InventoryDropButton,
    InventoryBagButton,
    // The bag overview: its button, an item in a bag and a free cell under a held item.
    InventoryBagOverviewButton,
    // A bag tag's toggle (bagButton: BagTag) for the open bag.
    InventoryBagTagButton,
    // A party of one's tab button (bagButton: the tab, 0-based).
    InventoryTabButton,
    BagOverviewItem,
    BagOverviewCell,
    MagnifyButton,
    AdventurersInnHireButton,
    AdventurersInnScrollUpButton,
    AdventurersInnScrollDownButton,
    AdventurersInnPortrait,
    StatRow,
    SkillRow,
    InventoryItem,
    InventoryCell,
    EquipmentSlot,
    DollPanel,
    // An implant socket of the Augment row (implantSocket).
    ImplantSocket
};

struct GameplayCharacterPointerTarget
{
    GameplayCharacterPointerTargetType type = GameplayCharacterPointerTargetType::None;
    GameplayUiController::CharacterPage page = GameplayUiController::CharacterPage::Inventory;
    std::string statName;
    std::string skillName;
    // A skill row that a click raises; other skill rows are targets only for their hover text.
    bool skillRaisable = false;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
    EquipmentSlot equipmentSlot = EquipmentSlot::MainHand;
    size_t innIndex = 0;
    // The bag a multibag button zooms (0-3, in the open bag's tab), a tag button's BagTag or a tab button's tab.
    uint8_t bagButton = 0;
    // The bag (0-based) of an overview target; gridX and gridY are its cell.
    uint8_t bag = 0;
    uint8_t implantSocket = 0;

    bool operator==(const GameplayCharacterPointerTarget &other) const = default;
};

enum class GameplayAlchemyBenchPointerTargetType
{
    None,
    CloseButton,
    MixButton,
    MixAllButton,
    ClearButton,
    TargetSlot,
    HeldSlot,
    RecipeFilterBrewable,
    RecipeFilterAll,
    IngredientFilterAll,
    IngredientFilterPotions,
    IngredientFilterReagents,
    RecipeRow,
    RecipeSearch,
    Ingredient,
    // The Workbench's tab strip and its Crafting tab.
    AlchemyTab,
    CraftingTab,
    CraftApplyButton,
    CraftApplyManyButton,
    CraftClearButton,
    CraftItemSlot,
    CraftMaterialSlot,
    CraftItemFilterAll,
    CraftItemFilterWorn,
    CraftItemFilterPacks,
    CraftSearch,
    CraftMaterialFilterAll,
    CraftMaterialFilterGems,
    CraftMaterialFilterSpecial,
    CraftMaterialFilterPotions,
    CraftCheapestGems,
    CraftItemRow,
    CraftMaterial,
    CraftChoice
};

struct GameplayAlchemyBenchPointerTarget
{
    GameplayAlchemyBenchPointerTargetType type = GameplayAlchemyBenchPointerTargetType::None;
    uint32_t itemId = 0;
    // Crafting rows, cells and options: the item's, material's or option's index in the frame's model.
    size_t index = 0;

    bool operator==(const GameplayAlchemyBenchPointerTarget &other) const = default;
};

enum class GameplayJournalPointerTargetType
{
    None,
    MainMapView,
    MainQuestsView,
    MainStoryView,
    MainNotesView,
    // MAW's Progress tab and, on it, a continent card, a map filter and a map row (their index in noteId), and the
    // ruleset's player's guide link.
    MainProgressView,
    ProgressContinent,
    ProgressFilter,
    ProgressMap,
    ProgressGuide,
    // The aura panel's targets (GameplayJournalAuras.h), packed into noteId.
    AuraPanel,
    // The Trainers notes' finder targets (GameplayJournalTrainers.h), packed into noteId.
    TrainerFinder,
    PrevPageButton,
    NextPageButton,
    NotesPotionButton,
    NotesFountainButton,
    NotesObeliskButton,
    NotesSeerButton,
    NotesMiscButton,
    NotesTrainerButton,
    NotesArcomageButton,
    NotesSearchField,
    MapZoomInButton,
    MapZoomOutButton,
    MapNote,
    CloseButton
};

struct GameplayJournalPointerTarget
{
    GameplayJournalPointerTargetType type = GameplayJournalPointerTargetType::None;
    uint32_t noteId = 0;

    bool operator==(const GameplayJournalPointerTarget &other) const = default;
};

enum class GameplayRestPointerTargetType
{
    None,
    OpenButton,
    Rest8HoursButton,
    WaitUntilDawnButton,
    Wait1HourButton,
    Wait5MinutesButton,
    ExitButton
};

struct GameplayRestPointerTarget
{
    GameplayRestPointerTargetType type = GameplayRestPointerTargetType::None;

    bool operator==(const GameplayRestPointerTarget &other) const = default;
};

enum class GameplayHudPointerTargetType
{
    None,
    MenuButton,
    RestButton,
    BooksButton,
    InventoryButton,
    DimensionDoorButton,
    QuickReferenceButton,
    QuickCastButton,
    AttackButton,
    TriggerButton,
    CastButton,
    TurnBasedToggleButton,
    PassTurnButton,
    ContextActionButton,
    MinimapZoomInButton,
    MinimapZoomOutButton,
    FollowerPanelToggleButton,
    // The combat log's button, one of its lines (index: the entry id) and the rest of its panel.
    CombatLogToggleButton,
    CombatLogEntry,
    CombatLogFilter,
    CombatLogPanel,
    FollowerPanelPortrait,
    FollowerPanelScrollUpButton,
    FollowerPanelScrollDownButton,
    BuffOverflow,
    PersonalBuffs,
    PartyBuff,
    PartyBuffPanel,
    DismissBuffs,
    MinimapOpen
};

struct GameplayHudPointerTarget
{
    GameplayHudPointerTargetType type = GameplayHudPointerTargetType::None;
    size_t index = 0;

    bool operator==(const GameplayHudPointerTarget &other) const = default;
};

enum class GameplayControlsPointerTargetType
{
    None,
    ConfigureKeyboardButton,
    VideoOptionsButton,
    TurnRate16Button,
    TurnRate32Button,
    TurnRateSmoothButton,
    WalkSoundButton,
    ShowHitsButton,
    AlwaysRunButton,
    FlipOnExitButton,
    SoundLeftButton,
    SoundTrack,
    SoundRightButton,
    MusicLeftButton,
    MusicTrack,
    MusicRightButton,
    VoiceLeftButton,
    VoiceTrack,
    VoiceRightButton,
    ReturnButton
};

enum class GameplayQuickReferencePointerTargetType
{
    None,
    ExitButton
};

struct GameplayQuickReferencePointerTarget
{
    GameplayQuickReferencePointerTargetType type = GameplayQuickReferencePointerTargetType::None;

    bool operator==(const GameplayQuickReferencePointerTarget &other) const = default;
};

struct GameplayControlsPointerTarget
{
    GameplayControlsPointerTargetType type = GameplayControlsPointerTargetType::None;
    int sliderValue = 0;

    bool operator==(const GameplayControlsPointerTarget &other) const = default;
};

enum class GameplayKeyboardPointerTargetType
{
    None,
    BindingRow,
    Page1Button,
    Page2Button,
    DefaultButton,
    BackButton,
    ReturnButton
};

struct GameplayKeyboardPointerTarget
{
    GameplayKeyboardPointerTargetType type = GameplayKeyboardPointerTargetType::None;
    KeyboardAction action = KeyboardAction::Forward;

    bool operator==(const GameplayKeyboardPointerTarget &other) const = default;
};

enum class GameplayVideoOptionsPointerTargetType
{
    None,
    BloodSplatsButton,
    ColoredLightsButton,
    TintingButton,
    CinematicButton,
    CinematicStrengthTrack,
    ReturnButton
};

struct GameplayVideoOptionsPointerTarget
{
    GameplayVideoOptionsPointerTargetType type = GameplayVideoOptionsPointerTargetType::None;

    bool operator==(const GameplayVideoOptionsPointerTarget &other) const = default;
};

enum class GameplayControlsRenderButton
{
    TurnRate16,
    TurnRate32,
    TurnRateSmooth,
    WalkSound,
    ShowHits,
    AlwaysRun,
    FlipOnExit
};

enum class GameplayVideoOptionsRenderButton
{
    BloodSplats,
    ColoredLights,
    Tinting
};

enum class GameplayMenuPointerTargetType
{
    None,
    NewGameButton,
    SaveGameButton,
    LoadGameButton,
    ControlsButton,
    QuitButton,
    ReturnButton
};

struct GameplayMenuPointerTarget
{
    GameplayMenuPointerTargetType type = GameplayMenuPointerTargetType::None;

    bool operator==(const GameplayMenuPointerTarget &other) const = default;
};

enum class GameplaySaveLoadPointerTargetType
{
    None,
    Slot,
    ScrollUpButton,
    ScrollDownButton,
    ConfirmButton,
    CancelButton
};

struct GameplaySaveLoadPointerTarget
{
    GameplaySaveLoadPointerTargetType type = GameplaySaveLoadPointerTargetType::None;
    size_t slotIndex = 0;

    bool operator==(const GameplaySaveLoadPointerTarget &other) const = default;
};

enum class GameplayInventoryNestedOverlayPointerTargetType
{
    None,
    CloseButton
};

struct GameplayInventoryNestedOverlayPointerTarget
{
    GameplayInventoryNestedOverlayPointerTargetType type = GameplayInventoryNestedOverlayPointerTargetType::None;

    bool operator==(const GameplayInventoryNestedOverlayPointerTarget &other) const = default;
};

// The basebar popup open over play: the party's potions or its scrolls.
enum class QuickItemPopupKind : uint8_t
{
    None,
    Potions,
    Scrolls,
};

struct GameplayOverlayInteractionState
{
    int dialogueBodyScrollLines = 0;
    std::string dialogueBodyText;
    std::string dialogueStatusHint;
    int itemInspectScrollLines = 0;
    uint32_t itemInspectScrollItem = 0;
    bool closeOverlayLatch = false;
    bool restToggleLatch = false;
    bool restClickLatch = false;
    bool alwaysRunToggleLatch = false;
    bool yellLatch = false;
    bool turnBasedToggleLatch = false;
    bool adventurersInnToggleLatch = false;
    GameplayRestPointerTarget restPressedTarget = {};
    bool gameplayHudClickLatch = false;
    GameplayHudPointerTarget gameplayHudPressedTarget = {};
    bool gameplayHudPressedContextActionActive = false;
    GameplayWorldHit gameplayHudPressedContextActionHit = {};
    bool gameplayHudQuickCastRequested = false;
    bool gameplayHudAttackRequested = false;
    bool gameplayHudTriggerRequested = false;
    bool gameplayHudSpellTargetConfirmRequested = false;
    bool gameplayHudSpellTargetCancelRequested = false;
    bool gameplayHudDropHeldItemRequested = false;
    bool partyBuffPopupOpen = false;
    std::optional<size_t> personalBuffPopupMember;
    bool overlayPersonalBuffClickLatch = false;
    std::optional<size_t> overlayPersonalBuffPressedIndex;
    bool followerPanelOpen = false;
    size_t followerPanelScrollOffset = 0;
    // The quick item ring (the potion radial, devdocs/maw/GAPS.md H.6): open at a member's portrait, the slot under
    // the pointer, the wheel key's press (a tap leaves the ring open, a hold uses the slot it is released over), and
    // the picker beside it filling one slot, with its list's scroll.
    bool quickItemRingOpen = false;
    size_t quickItemRingMember = 0;
    std::optional<size_t> quickItemHoveredSlot;
    uint64_t quickItemWheelPressedTicks = 0;
    bool quickItemWheelHeld = false;
    bool quickItemClickLatch = false;
    std::optional<size_t> quickItemPickerSlot;
    size_t quickItemPickerScroll = 0;
    bool quickItemEscapeHeld = false;
    // The basebar's potion and scroll popups (level_generation/ui/potion_scroll_popups_20261102): which one is open
    // (the game pauses), who drinks or reads, the list's scroll in rows, the entry under the pointer and the entry
    // whose quick-slot chooser is open.
    QuickItemPopupKind quickItemPopup = QuickItemPopupKind::None;
    size_t quickItemPopupMember = 0;
    size_t quickItemPopupScroll = 0;
    std::optional<size_t> quickItemPopupHovered;
    std::optional<size_t> quickItemPopupKeyEntry;
    bool menuToggleLatch = false;
    bool menuClickLatch = false;
    GameplayMenuPointerTarget menuPressedTarget = {};
    bool controlsToggleLatch = false;
    bool controlsClickLatch = false;
    GameplayControlsPointerTarget controlsPressedTarget = {};
    bool controlsSliderDragActive = false;
    GameplayControlsPointerTargetType controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    bool keyboardToggleLatch = false;
    bool keyboardClickLatch = false;
    GameplayKeyboardPointerTarget keyboardPressedTarget = {};
    bool videoOptionsToggleLatch = false;
    bool videoOptionsClickLatch = false;
    GameplayVideoOptionsPointerTarget videoOptionsPressedTarget = {};
    bool saveGameToggleLatch = false;
    bool saveGameClickLatch = false;
    GameplaySaveLoadPointerTarget saveGamePressedTarget = {};
    bool characterClickLatch = false;
    GameplayCharacterPointerTarget characterPressedTarget = {};
    bool characterTouchItemDragActive = false;
    bool characterMemberCycleLatch = false;
    std::optional<size_t> pendingCharacterDismissMemberIndex = std::nullopt;
    bool alchemyBenchClickLatch = false;
    bool alchemyBenchEscapeLatch = false;
    // An ingredient or slot item follows the pointer once a press moves far enough.
    bool alchemyBenchDragging = false;
    float alchemyBenchPressX = 0.0f;
    float alchemyBenchPressY = 0.0f;
    // 0: none, 1: recipe list, 2: ingredient grid. The grab keeps the thumb under the pointer.
    uint8_t alchemyBenchScrollDrag = 0;
    float alchemyBenchScrollGrab = 0.0f;
    GameplayAlchemyBenchPointerTarget alchemyBenchPressedTarget = {};
    uint64_t pendingCharacterDismissExpiresTicks = 0;
    bool spellbookClickLatch = false;
    GameplaySpellbookPointerTarget spellbookPressedTarget = {};
    uint64_t lastSpellbookSpellClickTicks = 0;
    uint32_t lastSpellbookClickedSpellId = 0;
    bool utilitySpellClickLatch = false;
    GameplayUtilitySpellPointerTarget utilitySpellPressedTarget = {};
    std::array<bool, 39> saveGameEditKeyLatches = {};
    bool saveGameEditBackspaceLatch = false;
    bool saveGameEditEraseHeld = false;
    uint64_t saveGameEditEraseNextRepeatTicks = 0;
    uint64_t lastSaveGameSlotClickTicks = 0;
    std::optional<size_t> lastSaveGameClickedSlotIndex = std::nullopt;
    bool journalToggleLatch = false;
    bool journalClickLatch = false;
    GameplayJournalPointerTarget journalPressedTarget = {};
    bool journalMapKeyZoomLatch = false;
    bool quickReferenceToggleLatch = false;
    bool quickReferenceClickLatch = false;
    GameplayQuickReferencePointerTarget quickReferencePressedTarget = {};
    bool dialogueClickLatch = false;
    GameplayDialoguePointerTarget dialoguePressedTarget = {};
    bool houseShopClickLatch = false;
    size_t houseShopPressedSlotIndex = static_cast<size_t>(-1);
    bool chestClickLatch = false;
    bool chestItemClickLatch = false;
    GameplayChestPointerTarget chestPressedTarget = {};
    bool inventoryNestedOverlayClickLatch = false;
    GameplayInventoryNestedOverlayPointerTarget inventoryNestedOverlayPressedTarget = {};
    bool inventoryNestedOverlayItemClickLatch = false;
    std::array<bool, 10> houseBankDigitLatches = {};
    bool houseBankBackspaceLatch = false;
    bool houseBankConfirmLatch = false;
    bool lootChestItemLatch = false;
    bool chestSelectUpLatch = false;
    bool chestSelectDownLatch = false;
    bool eventDialogSelectUpLatch = false;
    bool eventDialogSelectDownLatch = false;
    bool eventDialogAcceptLatch = false;
    std::array<bool, 5> eventDialogPartySelectLatches = {};
    // The MM9 conversation bar's number keys, 0-9.
    std::array<bool, 10> eventDialogNumberLatches = {};
    bool activateInspectLatch = false;
    bool itemInspectInteractionLatch = false;
    uint64_t itemInspectInteractionKey = 0;
    bool inventoryOpenHookExecuted = false;
    size_t chestSelectionIndex = 0;
    bool partyPortraitClickLatch = false;
    bool partyPortraitRightClickItemUseLatch = false;
    std::optional<size_t> partyPortraitPressedIndex = std::nullopt;
    uint64_t lastPartyPortraitClickTicks = 0;
    std::optional<size_t> lastPartyPortraitClickedIndex = std::nullopt;
    uint64_t lastAdventurersInnPortraitClickTicks = 0;
    std::optional<size_t> lastAdventurersInnPortraitClickedIndex = std::nullopt;
};

struct GameplayRenderedInspectableHudItem
{
    uint32_t objectDescriptionId = 0;
    bool hasItemState = false;
    InventoryItem itemState = {};
    GameplayUiController::ItemInspectSourceType sourceType = GameplayUiController::ItemInspectSourceType::None;
    size_t sourceMemberIndex = 0;
    uint8_t sourceGridX = 0;
    uint8_t sourceGridY = 0;
    // The bag the inventory item lies in (MAW's bag overview shows every bag, not only the open one).
    uint8_t sourceBag = 0;
    EquipmentSlot equipmentSlot = EquipmentSlot::MainHand;
    size_t sourceLootItemIndex = 0;
    std::string textureName;
    bool textureUsesItemIconTransparency = false;
    bool hasValueOverride = false;
    int valueOverride = 0;
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
    bool rotatedCounterClockwise = false;
    // The whole rectangle answers, not only the texture's opaque pixels (a list row: icon and name).
    bool wholeAreaHits = false;
};
} // namespace OpenYAMM::Game
