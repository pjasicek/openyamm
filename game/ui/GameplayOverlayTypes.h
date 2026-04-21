#pragma once

#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/Party.h"
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
    Journal
};

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
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 1.0f;
    float v1 = 1.0f;
    bool clipped = false;
    uint16_t scissorX = 0;
    uint16_t scissorY = 0;
    uint16_t scissorWidth = 0;
    uint16_t scissorHeight = 0;
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
    float u0 = 0.0f;
    float v0 = 0.0f;
    float uSpan = 1.0f;
    float vSpan = 1.0f;
    float partyU = 0.5f;
    float partyV = 0.5f;
    bool wizardEyeActive = false;
    bool wizardEyeShowsExpertObjects = false;
    bool wizardEyeShowsMasterDecorations = false;
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
    AttackCastButton
};

struct GameplaySpellbookPointerTarget
{
    GameplaySpellbookPointerTargetType type = GameplaySpellbookPointerTargetType::None;
    GameplayUiController::SpellbookSchool school = GameplayUiController::SpellbookSchool::Fire;
    uint32_t spellId = 0;

    bool operator==(const GameplaySpellbookPointerTarget &other) const = default;
};

struct GameplayTownPortalDestination
{
    std::string id;
    std::string label;
    std::string buttonLayoutId;
    std::string mapName;
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
    std::optional<int32_t> directionDegrees;
    bool useMapStartPosition = false;
    uint32_t unlockQBitId = 0;
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
    DollPanel
};

struct GameplayCharacterPointerTarget
{
    GameplayCharacterPointerTargetType type = GameplayCharacterPointerTargetType::None;
    GameplayUiController::CharacterPage page = GameplayUiController::CharacterPage::Inventory;
    std::string statName;
    std::string skillName;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
    EquipmentSlot equipmentSlot = EquipmentSlot::MainHand;
    size_t innIndex = 0;

    bool operator==(const GameplayCharacterPointerTarget &other) const = default;
};

enum class GameplayJournalPointerTargetType
{
    None,
    MainMapView,
    MainQuestsView,
    MainStoryView,
    MainNotesView,
    PrevPageButton,
    NextPageButton,
    NotesPotionButton,
    NotesFountainButton,
    NotesObeliskButton,
    NotesSeerButton,
    NotesMiscButton,
    NotesTrainerButton,
    MapZoomInButton,
    MapZoomOutButton,
    CloseButton
};

struct GameplayJournalPointerTarget
{
    GameplayJournalPointerTargetType type = GameplayJournalPointerTargetType::None;

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
    BooksButton
};

struct GameplayHudPointerTarget
{
    GameplayHudPointerTargetType type = GameplayHudPointerTargetType::None;

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

struct GameplayOverlayInteractionState
{
    bool closeOverlayLatch = false;
    bool restToggleLatch = false;
    bool restClickLatch = false;
    GameplayRestPointerTarget restPressedTarget = {};
    bool gameplayHudClickLatch = false;
    GameplayHudPointerTarget gameplayHudPressedTarget = {};
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
    bool characterMemberCycleLatch = false;
    std::optional<size_t> pendingCharacterDismissMemberIndex = std::nullopt;
    uint64_t pendingCharacterDismissExpiresTicks = 0;
    bool spellbookClickLatch = false;
    GameplaySpellbookPointerTarget spellbookPressedTarget = {};
    uint64_t lastSpellbookSpellClickTicks = 0;
    uint32_t lastSpellbookClickedSpellId = 0;
    bool utilitySpellClickLatch = false;
    GameplayUtilitySpellPointerTarget utilitySpellPressedTarget = {};
    std::array<bool, 39> saveGameEditKeyLatches = {};
    bool saveGameEditBackspaceLatch = false;
    uint64_t lastSaveGameSlotClickTicks = 0;
    std::optional<size_t> lastSaveGameClickedSlotIndex = std::nullopt;
    bool journalToggleLatch = false;
    bool journalClickLatch = false;
    GameplayJournalPointerTarget journalPressedTarget = {};
    bool journalMapKeyZoomLatch = false;
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
    bool activateInspectLatch = false;
    bool itemInspectInteractionLatch = false;
    uint64_t itemInspectInteractionKey = 0;
    size_t chestSelectionIndex = 0;
    bool partyPortraitClickLatch = false;
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
    EquipmentSlot equipmentSlot = EquipmentSlot::MainHand;
    size_t sourceLootItemIndex = 0;
    std::string textureName;
    bool hasValueOverride = false;
    int valueOverride = 0;
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};
} // namespace OpenYAMM::Game
