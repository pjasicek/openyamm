#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "engine/Localization.h"

#include "engine/Utf8Text.h"
#include "game/gameplay/GameplayAlchemyBenchInputController.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/tables/CharacterDollTable.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayInteractionController.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/AwardRuntime.h"
#include "game/app/KeyboardBindings.h"
#include "game/items/InventoryBags.h"
#include "game/ui/GameplayBattleOrders.h"
#include "game/ui/GameplayHudOverlaySupport.h"
#include "game/ui/InventoryBagOverview.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/LloydsBeaconRuntime.h"
#include "game/party/SpellIds.h"
#include "game/party/SkillData.h"
#include "game/rules/GameRules.h"
#include "game/tables/MergedBaseTables.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cctype>
#include <functional>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <optional>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint64_t PartyPortraitDoubleClickWindowMs = 500;
constexpr uint64_t CharacterDismissConfirmWindowMs = 2000;
constexpr float MaxUiScale = 8.0f;
constexpr uint32_t DaderossLetterDeliveredQBit = 4;
constexpr uint32_t EmeraldIslandFinishedQBit = 519;
// MM9 key 28 (raw key + 90000): the Isle of Ashes cinema has sailed the party to Sturmford.
constexpr uint32_t IsleOfAshesLeftQBit = 90028;

void latchGameplayMenuEscape(GameplayScreenRuntime &context)
{
    context.interactionState().menuToggleLatch = true;
}

bool isScancodeNewlyPressed(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input,
    SDL_Scancode scancode)
{
    return input.scancodePressCount(scancode) > 0
        || (input.isScancodeHeld(scancode) && context.previousKeyboardState()[scancode] == 0);
}

// The inventory's item search box (CharacterInventorySearch): a click on it types into it, a click elsewhere stops
// typing and keeps the search, a right click clears it. Typed text, Backspace and Enter edit it; Escape clears it, also
// while not typing, and leaves the screen open. True when the keyboard went to the search this frame.
bool handleInventorySearch(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    constexpr size_t MaxSearchLength = 48;
    GameplayUiController::CharacterScreenState &screen = context.characterScreen();

    if (screen.page != GameplayUiController::CharacterPage::Inventory
        || context.isAdventurersInnCharacterSourceActive()
        || !gameRulesFor(context.party()).items.inventorySearch())
    {
        screen.inventorySearchActive = false;
        return false;
    }

    const std::optional<GameplayResolvedHudLayoutElement> box =
        GameplayHudOverlaySupport::inventorySearchBox(context, input.screenWidth, input.screenHeight);
    const bool overBox = box && context.isPointerInsideResolvedElement(*box, input.pointerX, input.pointerY);

    if (input.leftMouseButton.pressed)
    {
        screen.inventorySearchActive = overBox;
    }

    if (input.rightMouseButton.pressed && overBox)
    {
        screen.inventorySearch.clear();
    }

    if (isScancodeNewlyPressed(context, input, SDL_SCANCODE_ESCAPE)
        && (screen.inventorySearchActive || !screen.inventorySearch.empty()))
    {
        screen.inventorySearch.clear();
        screen.inventorySearchActive = false;
        context.interactionState().alchemyBenchEscapeLatch = true;
        return true;
    }

    if (!screen.inventorySearchActive)
    {
        return false;
    }

    Engine::Utf8::appendPrintable(screen.inventorySearch, input.textInput, MaxSearchLength);

    for (uint16_t count = input.scancodePressCount(SDL_SCANCODE_BACKSPACE); count > 0; --count)
    {
        if (!screen.inventorySearch.empty())
        {
            Engine::Utf8::popBack(screen.inventorySearch);
        }
    }

    if (input.scancodePressCount(SDL_SCANCODE_RETURN) > 0 || input.scancodePressCount(SDL_SCANCODE_KP_ENTER) > 0)
    {
        screen.inventorySearchActive = false;
    }

    return true;
}

struct HudPointerState
{
    float x = 0.0f;
    float y = 0.0f;
    bool leftButtonPressed = false;
};

struct InventoryGridMetrics
{
    float x = 0.0f;
    float y = 0.0f;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
    float scale = 1.0f;
};

struct InventoryItemScreenRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

struct UtilityOverlayLayout
{
    float panelX = 0.0f;
    float panelY = 0.0f;
    float panelWidth = 0.0f;
    float panelHeight = 0.0f;
    float closeX = 0.0f;
    float closeY = 0.0f;
    float closeSize = 0.0f;
    float contentX = 0.0f;
    float contentY = 0.0f;
    float contentWidth = 0.0f;
    float rowHeight = 0.0f;
    float tabWidth = 0.0f;
    float tabHeight = 0.0f;
    float tabGap = 0.0f;
};

struct CharacterSkillUiRow
{
    std::string canonicalName;
    std::string label;
    std::string level;
    bool upgradeable = false;
    bool interactive = false;
    // The row's on/off switch when the rules give the skill one: whether it is on.
    std::optional<bool> switchOn;
};

struct CharacterSkillUiData
{
    std::vector<CharacterSkillUiRow> weaponRows;
    std::vector<CharacterSkillUiRow> magicRows;
    std::vector<CharacterSkillUiRow> armorRows;
    std::vector<CharacterSkillUiRow> miscRows;
    std::vector<CharacterSkillUiRow> techRows;
};

struct DimensionDoorLanding
{
    std::string mapName;
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
    std::optional<int32_t> directionDegrees;
    bool useMapStartPosition = false;
};

bool isJewelryOverlayEquipmentSlot(EquipmentSlot slot)
{
    switch (slot)
    {
    case EquipmentSlot::Gauntlets:
    case EquipmentSlot::Amulet:
    case EquipmentSlot::Ring1:
    case EquipmentSlot::Ring2:
    case EquipmentSlot::Ring3:
    case EquipmentSlot::Ring4:
    case EquipmentSlot::Ring5:
    case EquipmentSlot::Ring6:
        return true;

    case EquipmentSlot::OffHand:
    case EquipmentSlot::MainHand:
    case EquipmentSlot::Bow:
    case EquipmentSlot::Armor:
    case EquipmentSlot::Helm:
    case EquipmentSlot::Belt:
    case EquipmentSlot::Cloak:
    case EquipmentSlot::Boots:
        return false;
    }

    return false;
}

bool isVisibleInCharacterDollOverlay(EquipmentSlot slot, bool jewelryOverlayOpen)
{
    return jewelryOverlayOpen ? isJewelryOverlayEquipmentSlot(slot) : !isJewelryOverlayEquipmentSlot(slot);
}

InventoryGridMetrics computeInventoryGridMetrics(float x, float y, float width, float height, float scale)
{
    InventoryGridMetrics metrics = {};
    metrics.x = x;
    metrics.y = y;
    metrics.cellWidth = width / static_cast<float>(std::max(1, Character::InventoryWidth));
    metrics.cellHeight = height / static_cast<float>(std::max(1, Character::InventoryHeight));
    metrics.scale = scale;
    return metrics;
}

InventoryItemScreenRect computeInventoryItemScreenRect(
    const InventoryGridMetrics &gridMetrics,
    const InventoryItem &item,
    float textureWidth,
    float textureHeight)
{
    const float slotSpanWidth = static_cast<float>(item.width) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(item.height) * gridMetrics.cellHeight;
    const float offsetX = (slotSpanWidth - textureWidth) * 0.5f;
    const float offsetY = (slotSpanHeight - textureHeight) * 0.5f;

    InventoryItemScreenRect rect = {};
    rect.x = std::round(gridMetrics.x + static_cast<float>(item.gridX) * gridMetrics.cellWidth + offsetX);
    rect.y = std::round(gridMetrics.y + static_cast<float>(item.gridY) * gridMetrics.cellHeight + offsetY);
    rect.width = textureWidth;
    rect.height = textureHeight;
    return rect;
}

UtilityOverlayLayout computeUtilityOverlayLayout(int screenWidth, int screenHeight)
{
    const float width = static_cast<float>(std::max(screenWidth, 1));
    const float height = static_cast<float>(std::max(screenHeight, 1));
    const float scale = std::clamp(std::min(width / 640.0f, height / 480.0f), 0.8f, MaxUiScale);

    UtilityOverlayLayout layout = {};
    layout.panelWidth = std::round(360.0f * scale);
    layout.panelHeight = std::round(300.0f * scale);
    layout.panelX = std::round((width - layout.panelWidth) * 0.5f);
    layout.panelY = std::round((height - layout.panelHeight) * 0.5f);
    layout.closeSize = std::round(24.0f * scale);
    layout.closeX = std::round(layout.panelX + layout.panelWidth - layout.closeSize - 12.0f * scale);
    layout.closeY = std::round(layout.panelY + 12.0f * scale);
    layout.contentX = std::round(layout.panelX + 24.0f * scale);
    layout.contentY = std::round(layout.panelY + 68.0f * scale);
    layout.contentWidth = std::round(layout.panelWidth - 48.0f * scale);
    layout.rowHeight = std::round(36.0f * scale);
    layout.tabWidth = std::round(120.0f * scale);
    layout.tabHeight = std::round(28.0f * scale);
    layout.tabGap = std::round(10.0f * scale);
    return layout;
}

bool pointInsideRect(float x, float y, float rectX, float rectY, float rectWidth, float rectHeight)
{
    return x >= rectX && x < rectX + rectWidth && y >= rectY && y < rectY + rectHeight;
}

size_t maxLloydBeaconSlots(const Character *pCharacter)
{
    if (pCharacter == nullptr)
    {
        return 1;
    }

    const CharacterSkill *pWaterSkill = pCharacter->findSkill("WaterMagic");

    if (pWaterSkill == nullptr)
    {
        return 1;
    }

    switch (pWaterSkill->mastery)
    {
        case SkillMastery::Grandmaster:
        case SkillMastery::Master:
            return 5;

        case SkillMastery::Expert:
            return 3;

        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return 1;
    }
}

bool isTownPortalDestinationUnlocked(
    const Party *pParty,
    const GameplayTownPortalDestination &destination)
{
    if (destination.unlockQBitId == 0)
    {
        return true;
    }

    if (pParty == nullptr)
    {
        return false;
    }

    return pParty->hasQuestBit(destination.unlockQBitId);
}

bool isTownPortalOverlayMode(GameplayUiController::UtilitySpellOverlayMode mode)
{
    return mode == GameplayUiController::UtilitySpellOverlayMode::TownPortal
        || mode == GameplayUiController::UtilitySpellOverlayMode::DimensionDoor;
}

bool isDimensionDoorOverlayMode(GameplayUiController::UtilitySpellOverlayMode mode)
{
    return mode == GameplayUiController::UtilitySpellOverlayMode::DimensionDoor;
}

void applyDimensionDoorCastOverrides(PartySpellCastRequest &request)
{
    request.skillLevelOverride = 10;
    request.skillMasteryOverride = SkillMastery::Grandmaster;
    request.spendMana = false;
    request.applyRecovery = false;
    request.utilityMapMoveUseFullscreenLoading = true;
}

std::optional<DimensionDoorLanding> resolveDimensionDoorLanding(
    const Party *pParty,
    const GameplayTownPortalDestination &destination)
{
    if (destination.id == "TPGlobal:0")
    {
        if (pParty != nullptr && pParty->hasQuestBit(DaderossLetterDeliveredQBit))
        {
            return DimensionDoorLanding{
                "out02.odm",
                10296,
                -12283,
                1,
                0,
                false};
        }

        return DimensionDoorLanding{
            "out01.odm",
            0,
            0,
            0,
            std::nullopt,
            true};
    }

    if (destination.id == "TPGlobal:2")
    {
        if (pParty != nullptr && pParty->hasQuestBit(EmeraldIslandFinishedQBit))
        {
            return DimensionDoorLanding{
                "7out02.odm",
                -16832,
                12512,
                372,
                0,
                false};
        }

        return DimensionDoorLanding{
            "7out01.odm",
            12552,
            800,
            193,
            90,
            false};
    }

    if (destination.id == "TPGlobal:4")
    {
        return DimensionDoorLanding{
            "oute3.odm",
            -9728,
            -11319,
            160,
            90,
            false};
    }

    // Chedian: once the party has left the Isle of Ashes, beside Sturmford City's dimensional travel pedestal
    // (level_generation/projects/mm9r_sturmfordcity), facing it; before that, Ravensford's new-game start
    // (continent_settings.txt, Chedian's start map).
    if (destination.id == "TPGlobal:6")
    {
        if (pParty != nullptr && pParty->hasQuestBit(IsleOfAshesLeftQBit))
        {
            return DimensionDoorLanding{
                "sturmfordcity.blv",
                1752,
                54,
                19703,
                180,
                false};
        }

        return DimensionDoorLanding{
            "bootcamp.blv",
            323,
            -8494,
            1291,
            269,
            false};
    }

    return std::nullopt;
}

void applyDimensionDoorLandingOverride(
    PartySpellCastRequest &request,
    const Party *pParty,
    const GameplayTownPortalDestination &destination)
{
    const std::optional<DimensionDoorLanding> landing = resolveDimensionDoorLanding(pParty, destination);

    if (!landing.has_value())
    {
        return;
    }

    request.utilityMapMoveMapName = landing->mapName;
    request.utilityMapMoveX = landing->x;
    request.utilityMapMoveY = landing->y;
    request.utilityMapMoveZ = landing->z;
    request.utilityMapMoveDirectionDegrees = landing->directionDegrees;
    request.utilityMapMoveUseMapStartPosition = landing->useMapStartPosition;
}

std::optional<std::pair<int, int>> computeHeldInventoryPlacement(
    const InventoryGridMetrics &gridMetrics,
    uint8_t itemWidthCells,
    uint8_t itemHeightCells,
    float textureWidth,
    float textureHeight,
    float drawX,
    float drawY)
{
    if (gridMetrics.cellWidth <= 0.0f || gridMetrics.cellHeight <= 0.0f)
    {
        return std::nullopt;
    }

    const float slotSpanWidth = static_cast<float>(itemWidthCells) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(itemHeightCells) * gridMetrics.cellHeight;
    const float itemCenterX = drawX + textureWidth * 0.5f;
    const float itemCenterY = drawY + textureHeight * 0.5f;
    const int gridX = static_cast<int>(std::floor(
        (itemCenterX - gridMetrics.x - slotSpanWidth * 0.5f + gridMetrics.cellWidth * 0.5f)
        / gridMetrics.cellWidth));
    const int gridY = static_cast<int>(std::floor(
        (itemCenterY - gridMetrics.y - slotSpanHeight * 0.5f + gridMetrics.cellHeight * 0.5f)
        / gridMetrics.cellHeight));
    return std::pair<int, int>(gridX, gridY);
}

std::optional<uint32_t> parseCharacterDataIdFromPortraitTextureName(const std::string &portraitTextureName)
{
    const std::string normalized = toLowerCopy(portraitTextureName);

    if (normalized.size() < 4 || !normalized.starts_with("pc"))
    {
        return std::nullopt;
    }

    std::string digits;

    for (size_t index = 2; index < normalized.size(); ++index)
    {
        const unsigned char character = static_cast<unsigned char>(normalized[index]);

        if (!std::isdigit(character))
        {
            break;
        }

        digits.push_back(normalized[index]);
    }

    if (digits.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const unsigned long parsed = std::strtoul(digits.c_str(), &pEnd, 10);

    if (pEnd == digits.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return static_cast<uint32_t>(parsed);
}

const CharacterDollEntry *resolveCharacterDollEntry(
    const CharacterDollTable *pCharacterDollTable,
    const Character *pCharacter)
{
    if (pCharacterDollTable == nullptr || pCharacter == nullptr)
    {
        return nullptr;
    }

    if (pCharacter->characterDataId != 0)
    {
        const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(pCharacter->characterDataId);

        if (pEntry != nullptr)
        {
            return pEntry;
        }
    }

    const std::optional<uint32_t> portraitCharacterDataId =
        parseCharacterDataIdFromPortraitTextureName(pCharacter->portraitTextureName);

    if (portraitCharacterDataId)
    {
        const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(*portraitCharacterDataId);

        if (pEntry != nullptr)
        {
            return pEntry;
        }
    }

    return pCharacterDollTable->getCharacter(1);
}

std::string skillPageMasteryDisplayName(SkillMastery mastery)
{
    if (mastery == SkillMastery::Grandmaster)
    {
        return Engine::tr("Grand");
    }

    return Engine::localize(masteryDisplayName(mastery), "mastery");
}

// A skill page row's name as the renderer shows it (GameplayPartyOverlayRenderer), so the rows sort alike.
std::string characterSkillRowLabel(const std::string &skillName, SkillMastery mastery)
{
    std::string label = Engine::localizeKnown(skillName, "skill");

    if (mastery != SkillMastery::None && mastery != SkillMastery::Normal)
    {
        label = Engine::tr("{skill} {mastery}", {{"skill", label}, {"mastery", skillPageMasteryDisplayName(mastery)}});
    }

    return label;
}

void appendCharacterSkillUiRows(
    const Character &character,
    const SkillRules &skillRules,
    std::vector<CharacterSkillUiRow> &rows,
    std::unordered_set<std::string> &shownSkillNames,
    const std::vector<std::string> &skillNames,
    bool allowUpgradeInteraction)
{
    for (const std::string &canonicalName : skillNames)
    {
        const CharacterSkill *pSkill = character.findSkillByCanonicalName(canonicalName);

        if (pSkill == nullptr)
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = canonicalName;
        row.label = characterSkillRowLabel(skillRules.skillDisplayName(character, canonicalName), pSkill->mastery);
        row.level = std::to_string(pSkill->level);
        row.upgradeable = skillRules.canRaiseSkill(character, canonicalName);
        row.interactive = row.upgradeable && allowUpgradeInteraction;
        row.switchOn = skillRules.skillSwitch(character, canonicalName);
        rows.push_back(std::move(row));
        shownSkillNames.insert(canonicalName);
    }
}

// "Water Magic 7 to 8: 3 skill points (8, shared with Fire Magic and Air Magic)" when the rules show raise costs.
// What a bag tag's button would do: the bag it acts on (the zoomed one, or in the overview the one opened last).
std::string bagTagHoverText(const Character &member, BagTag tag, int bagCount)
{
    const uint8_t bag = member.rulesetState.currentBag;
    const bool tagged = InventoryBags::hasTag(member, bag, tag);
    const std::string name = InventoryBagOverview::bagName(bag, bagCount);

    if (tagged)
    {
        const std::string bagText = Engine::Utf8::capitalizedFirst(name);
        return tag == BagTag::Crafting
            ? Engine::tr("{bag} is a crafting bag (Shift+B): click to untag", {{"bag", bagText}})
            : Engine::tr("{bag} is an alchemy bag: click to untag", {{"bag", bagText}});
    }

    return tag == BagTag::Crafting ? Engine::tr("Make {bag} a crafting bag (Shift+B)", {{"bag", name}})
                                   : Engine::tr("Make {bag} an alchemy bag", {{"bag", name}});
}

std::string skillRaiseCostHoverText(
    const Character &character,
    const std::string &canonicalSkill,
    const SkillRules &skillRules)
{
    const std::optional<SkillRaiseCost> cost = skillRules.skillRaiseCostDetail(character, canonicalSkill);
    const CharacterSkill *pSkill = character.findSkill(canonicalSkill);

    if (!cost || pSkill == nullptr)
    {
        return {};
    }

    std::string text = Engine::trn("{skill} {level} to {next}: {cost} skill point",
        "{skill} {level} to {next}: {cost} skill points", cost->cost,
        {{"skill", Engine::localizeKnown(skillRules.skillDisplayName(character, canonicalSkill), "skill")},
            {"level", pSkill->level},
            {"next", pSkill->level + 1},
            {"cost", cost->cost}});

    if (!cost->sharedWith.empty())
    {
        std::string skills = Engine::localizeKnown(cost->sharedWith.front(), "skill");

        for (size_t index = 1; index < cost->sharedWith.size(); ++index)
        {
            const std::string other = Engine::localizeKnown(cost->sharedWith[index], "skill");
            skills = index + 1 == cost->sharedWith.size()
                ? Engine::tr("{skills} and {skill}", {{"skills", skills}, {"skill", other}})
                : skills + ", " + other;
        }

        text = Engine::tr("{text} ({cost}, shared with {skills})",
            {{"text", text}, {"cost", cost->fullCost}, {"skills", skills}});
    }

    const uint32_t points = character.pointsForRaisingSkill(canonicalSkill);

    if (points < cost->cost)
    {
        text = Engine::tr("{text}, you have {points}", {{"text", text}, {"points", points}});
    }

    return text;
}

// "Cover is on: click to switch it off (P)" for a skills page switch.
std::string skillSwitchHoverText(GameplayScreenRuntime &context, const std::string &name, bool on, KeyboardAction action)
{
    const InputBinding &binding = context.settingsSnapshot().keyboard.bindings[keyboardActionIndex(action)];
    const std::string text = on ? Engine::tr("{name} is on: click to switch it off", {{"name", name}})
                                : Engine::tr("{name} is off: click to switch it on", {{"name", name}});
    return binding.kind == InputBindingKind::None
        ? text
        : Engine::tr("{text} ({key})", {{"text", text}, {"key", inputBindingDisplayName(binding)}});
}

CharacterSkillUiData buildCharacterSkillUiData(
    const Character *pCharacter,
    bool allowUpgradeInteraction,
    const SkillRules &skillRules)
{
    CharacterSkillUiData data = {};

    if (pCharacter == nullptr)
    {
        return data;
    }

    std::unordered_set<std::string> shownSkillNames;
    appendCharacterSkillUiRows(
        *pCharacter,
        skillRules,
        data.weaponRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Weapons),
        allowUpgradeInteraction);
    appendCharacterSkillUiRows(
        *pCharacter,
        skillRules,
        data.magicRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Magic),
        allowUpgradeInteraction);
    appendCharacterSkillUiRows(
        *pCharacter,
        skillRules,
        data.armorRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Armor),
        allowUpgradeInteraction);
    appendCharacterSkillUiRows(
        *pCharacter,
        skillRules,
        data.miscRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Misc),
        allowUpgradeInteraction);
    appendCharacterSkillUiRows(
        *pCharacter,
        skillRules,
        data.techRows,
        shownSkillNames,
        skillSheetGroupSkillNames(SkillSheetGroup::Technology),
        allowUpgradeInteraction);

    std::vector<CharacterSkillUiRow> extraMiscRows;

    for (const auto &[ignoredSkillName, skill] : pCharacter->skills)
    {
        const std::string &canonicalName = ignoredSkillName;

        if (shownSkillNames.contains(canonicalName))
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = canonicalName;
        row.label = characterSkillRowLabel(skillRules.skillDisplayName(*pCharacter, canonicalName), skill.mastery);
        row.level = std::to_string(skill.level);
        row.upgradeable = skillRules.canRaiseSkill(*pCharacter, canonicalName);
        row.interactive = row.upgradeable && allowUpgradeInteraction;
        row.switchOn = skillRules.skillSwitch(*pCharacter, canonicalName);
        extraMiscRows.push_back(std::move(row));
    }

    std::sort(
        extraMiscRows.begin(),
        extraMiscRows.end(),
        [](const CharacterSkillUiRow &left, const CharacterSkillUiRow &right)
        {
            return left.label < right.label;
        });

    data.miscRows.insert(data.miscRows.end(), extraMiscRows.begin(), extraMiscRows.end());
    return data;
}

void setCharacterSkillRegionHeight(
    std::unordered_map<std::string, float> &runtimeHeightOverrides,
    float skillRowHeight,
    const char *pLayoutId,
    size_t rowCount)
{
    runtimeHeightOverrides[toLowerCopy(pLayoutId)] =
        skillRowHeight * static_cast<float>(std::max<size_t>(1, rowCount));
}

uint32_t equippedItemId(const CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
    case EquipmentSlot::OffHand:
        return equipment.offHand;
    case EquipmentSlot::MainHand:
        return equipment.mainHand;
    case EquipmentSlot::Bow:
        return equipment.bow;
    case EquipmentSlot::Armor:
        return equipment.armor;
    case EquipmentSlot::Helm:
        return equipment.helm;
    case EquipmentSlot::Belt:
        return equipment.belt;
    case EquipmentSlot::Cloak:
        return equipment.cloak;
    case EquipmentSlot::Gauntlets:
        return equipment.gauntlets;
    case EquipmentSlot::Boots:
        return equipment.boots;
    case EquipmentSlot::Amulet:
        return equipment.amulet;
    case EquipmentSlot::Ring1:
        return equipment.ring1;
    case EquipmentSlot::Ring2:
        return equipment.ring2;
    case EquipmentSlot::Ring3:
        return equipment.ring3;
    case EquipmentSlot::Ring4:
        return equipment.ring4;
    case EquipmentSlot::Ring5:
        return equipment.ring5;
    case EquipmentSlot::Ring6:
        return equipment.ring6;
    }

    return 0;
}

template <typename Target, typename ResolveTargetFn, typename ActivateTargetFn>
void handlePointerClickRelease(
    const HudPointerState &pointerState,
    bool &clickLatch,
    Target &pressedTarget,
    const Target &noneTarget,
    ResolveTargetFn resolveTargetFn,
    ActivateTargetFn activateTargetFn)
{
    if (pointerState.leftButtonPressed)
    {
        if (!clickLatch)
        {
            pressedTarget = resolveTargetFn(pointerState.x, pointerState.y);
            clickLatch = true;
        }
    }
    else if (clickLatch)
    {
        const Target currentTarget = resolveTargetFn(pointerState.x, pointerState.y);

        if (currentTarget == pressedTarget)
        {
            activateTargetFn(currentTarget);
        }

        clickLatch = false;
        pressedTarget = noneTarget;
    }
}

} // namespace

void GameplayPartyOverlayInputController::handleUtilitySpellOverlayInput(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;

    if (!context.utilitySpellOverlayReadOnly().active)
    {
        return;
    }

    if (context.utilitySpellOverlayReadOnly().lloydSetPreviewCapturePending)
    {
        return;
    }

    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!context.interactionState().closeOverlayLatch)
        {
            context.utilitySpellOverlay() = {};
            context.resetUtilitySpellOverlayInteractionState();
            context.setStatusBarEvent(Engine::tr("Spell cancelled"), 2.0f);
            latchGameplayMenuEscape(context);
            context.interactionState().closeOverlayLatch = true;
        }

        return;
    }

    context.interactionState().closeOverlayLatch = false;

    const HudPointerState pointerState = {
        input.pointerX,
        input.pointerY,
        input.leftMouseButton.held
    };
    const GameplayUtilitySpellPointerTarget noneTarget = {};
    const auto resolveSpellName =
        [&context]() -> std::string
        {
            if (isDimensionDoorOverlayMode(context.utilitySpellOverlayReadOnly().mode))
            {
                return std::string(Engine::trNoop("Dimension Door"));
            }

            if (context.spellTable() == nullptr)
            {
                return std::string(Engine::trNoop("Spell"));
            }

            const SpellEntry *pEntry =
                context.spellTable()->findById(static_cast<int>(context.utilitySpellOverlayReadOnly().spellId));
            return pEntry != nullptr && !pEntry->name.empty() ? pEntry->name : "Spell";
        };

    if (isTownPortalOverlayMode(context.utilitySpellOverlayReadOnly().mode))
    {
        if (!context.ensureTownPortalDestinationsLoaded())
        {
            context.utilitySpellOverlay() = {};
            context.resetUtilitySpellOverlayInteractionState();
            context.setStatusBarEvent(Engine::tr("Town Portal destinations unavailable"));
            return;
        }

        const Party *pParty = context.partyReadOnly();
        const auto findTownPortalTarget =
            [&context, screenWidth, screenHeight, pParty](
                float pointerX,
                float pointerY) -> GameplayUtilitySpellPointerTarget
            {
                const GameplayScreenRuntime::HudLayoutElement *pCloseLayout =
                    context.findHudLayoutElement("TownPortalCloseButton");

                if (pCloseLayout != nullptr && pCloseLayout->visible)
                {
                    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> closeResolved =
                        context.resolveHudLayoutElement(
                            "TownPortalCloseButton",
                            screenWidth,
                            screenHeight,
                            pCloseLayout->width,
                            pCloseLayout->height);

                    if (closeResolved.has_value()
                        && context.isPointerInsideResolvedElement(*closeResolved, pointerX, pointerY))
                    {
                        return {GameplayUtilitySpellPointerTargetType::Close, 0};
                    }
                }

                const size_t continentCount = context.townPortalContinents().size();

                for (size_t index = 0; continentCount > 1 && index < continentCount
                     && index < TownPortalContinentButtonCount; ++index)
                {
                    const std::string buttonId = townPortalContinentButtonId(index);
                    const GameplayScreenRuntime::HudLayoutElement *pButtonLayout =
                        context.findHudLayoutElement(buttonId);

                    if (pButtonLayout == nullptr || !pButtonLayout->visible)
                    {
                        continue;
                    }

                    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> buttonResolved =
                        context.resolveHudLayoutElement(
                            buttonId,
                            screenWidth,
                            screenHeight,
                            pButtonLayout->width,
                            pButtonLayout->height);

                    if (buttonResolved.has_value()
                        && context.isPointerInsideResolvedElement(*buttonResolved, pointerX, pointerY))
                    {
                        return {GameplayUtilitySpellPointerTargetType::TownPortalContinent, index};
                    }
                }

                const GameplayScreenRuntime::HudLayoutElement *pBackgroundLayout =
                    context.findHudLayoutElement("TownPortalBackground");

                if (pBackgroundLayout == nullptr || !pBackgroundLayout->visible)
                {
                    return {};
                }

                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> backgroundResolved =
                    context.resolveHudLayoutElement(
                        "TownPortalBackground",
                        screenWidth,
                        screenHeight,
                        pBackgroundLayout->width,
                        pBackgroundLayout->height);

                if (!backgroundResolved.has_value())
                {
                    return {};
                }

                const float townPortalScale = backgroundResolved->width / 640.0f;

                for (size_t destinationIndex = 0;
                     destinationIndex < context.townPortalDestinations().size();
                     ++destinationIndex)
                {
                    const GameplayTownPortalDestination &destination =
                        context.townPortalDestinations()[destinationIndex];

                    if (!isTownPortalDestinationUnlocked(pParty, destination))
                    {
                        continue;
                    }

                    const int32_t hitX = destination.hitWidth != 0 ? destination.hitX : destination.iconX;
                    const int32_t hitY = destination.hitHeight != 0 ? destination.hitY : destination.iconY;
                    uint32_t hitWidth = destination.hitWidth != 0 ? destination.hitWidth : destination.iconWidth;
                    uint32_t hitHeight = destination.hitHeight != 0 ? destination.hitHeight : destination.iconHeight;

                    if (hitWidth == 0 || hitHeight == 0)
                    {
                        int textureWidth = 0;
                        int textureHeight = 0;

                        if (!context.gameplayUiRuntime().ensureHudTextureDimensions(
                                destination.iconTextureName,
                                textureWidth,
                                textureHeight))
                        {
                            continue;
                        }

                        hitWidth = static_cast<uint32_t>(textureWidth);
                        hitHeight = static_cast<uint32_t>(textureHeight);
                    }

                    const GameplayScreenRuntime::ResolvedHudLayoutElement resolved = {
                        backgroundResolved->x + static_cast<float>(hitX) * townPortalScale,
                        backgroundResolved->y + static_cast<float>(hitY) * townPortalScale,
                        static_cast<float>(hitWidth) * townPortalScale,
                        static_cast<float>(hitHeight) * townPortalScale,
                        townPortalScale};

                    if (!context.isPointerInsideResolvedElement(resolved, pointerX, pointerY))
                    {
                        continue;
                    }

                    return {GameplayUtilitySpellPointerTargetType::TownPortalDestination, destinationIndex};
                }

                return {};
            };

        const GameplayUtilitySpellPointerTarget hoveredTarget =
            findTownPortalTarget(pointerState.x, pointerState.y);

        if (hoveredTarget.type == GameplayUtilitySpellPointerTargetType::TownPortalDestination
            && hoveredTarget.index < context.townPortalDestinations().size())
        {
            const std::string destination =
                Engine::localize(context.townPortalDestinations()[hoveredTarget.index].label);
            context.setStatusBarHoverText(isDimensionDoorOverlayMode(context.utilitySpellOverlayReadOnly().mode)
                    ? Engine::tr("Dimension Door to {destination}", {{"destination", destination}})
                    : Engine::tr("Town Portal to {destination}", {{"destination", destination}}));
        }
        else
        {
            context.clearStatusBarHoverText();
        }

        handlePointerClickRelease(
            pointerState,
            context.interactionState().utilitySpellClickLatch,
            context.interactionState().utilitySpellPressedTarget,
            noneTarget,
            findTownPortalTarget,
            [&context, &resolveSpellName, pParty](const GameplayUtilitySpellPointerTarget &target)
            {
                if (target.type == GameplayUtilitySpellPointerTargetType::Close)
                {
                    context.utilitySpellOverlay() = {};
                    context.resetUtilitySpellOverlayInteractionState();
                    context.setStatusBarEvent(Engine::tr("Spell cancelled"), 2.0f);
                    return;
                }

                if (target.type == GameplayUtilitySpellPointerTargetType::TownPortalContinent)
                {
                    context.selectTownPortalContinent(target.index);
                    return;
                }

                if (target.type != GameplayUtilitySpellPointerTargetType::TownPortalDestination
                    || target.index >= context.townPortalDestinations().size())
                {
                    return;
                }

                const GameplayTownPortalDestination &destination = context.townPortalDestinations()[target.index];
                PartySpellCastRequest request = context.utilitySpellOverlayReadOnly().castRequest();
                request.utilityAction = PartySpellUtilityActionKind::TownPortalDestination;
                request.hasUtilityMapMove = true;
                request.utilityActionId = destination.id;
                request.utilityMapMoveMapName = destination.mapName;
                request.utilityMapMoveX = destination.x;
                request.utilityMapMoveY = destination.y;
                request.utilityMapMoveZ = destination.z;
                request.utilityMapMoveDirectionDegrees = destination.directionDegrees;
                request.utilityMapMoveUseMapStartPosition = destination.useMapStartPosition;
                request.utilityStatusText = destination.label;
                if (isDimensionDoorOverlayMode(context.utilitySpellOverlayReadOnly().mode))
                {
                    applyDimensionDoorCastOverrides(request);
                    applyDimensionDoorLandingOverride(request, pParty, destination);
                }
                context.tryCastSpellRequest(request, resolveSpellName());
            });
        return;
    }

    context.clearStatusBarHoverText();

    if (context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::LloydsBeacon)
    {
        const auto resolveLayout =
            [&context, screenWidth, screenHeight](
                const std::string &layoutId) -> std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement>
            {
                const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

                if (pLayout == nullptr)
                {
                    return std::nullopt;
                }

                return context.resolveHudLayoutElement(
                    layoutId,
                    screenWidth,
                    screenHeight,
                    pLayout->width,
                    pLayout->height);
            };
        const auto pointInsideLayout =
            [&resolveLayout](float pointerX, float pointerY, const std::string &layoutId) -> bool
            {
                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved = resolveLayout(layoutId);

                return resolved.has_value()
                    && pointInsideRect(pointerX, pointerY, resolved->x, resolved->y, resolved->width, resolved->height);
            };
        const auto slotLayoutId =
            [](size_t index) -> std::string
            {
                return "LloydsBeaconSlot" + std::to_string(index + 1);
            };
        const auto findLloydTarget =
            [&context, &pointInsideLayout, &slotLayoutId](
                float pointerX,
                float pointerY) -> GameplayUtilitySpellPointerTarget
            {
                if (pointInsideLayout(pointerX, pointerY, "LloydsBeaconCloseButton"))
                {
                    return {GameplayUtilitySpellPointerTargetType::Close, 0};
                }

                if (pointInsideLayout(pointerX, pointerY, "LloydsBeaconSetBeacon"))
                {
                    return {GameplayUtilitySpellPointerTargetType::LloydSetTab, 0};
                }

                if (pointInsideLayout(pointerX, pointerY, "LloydsBeaconRecallBeacon"))
                {
                    return {GameplayUtilitySpellPointerTargetType::LloydRecallTab, 0};
                }

                const Character *pCaster =
                    context.partyReadOnly() != nullptr
                        ? context.partyReadOnly()->member(context.utilitySpellOverlayReadOnly().casterMemberIndex)
                        : nullptr;
                const size_t slotCount = lloydsBeaconMaxSlotsForCharacter(pCaster);

                for (size_t index = 0; index < slotCount; ++index)
                {
                    if (pointInsideLayout(pointerX, pointerY, slotLayoutId(index)))
                    {
                        return {GameplayUtilitySpellPointerTargetType::LloydSlot, index};
                    }
                }

                return {};
            };

        const GameplayUtilitySpellPointerTarget hoveredTarget =
            findLloydTarget(pointerState.x, pointerState.y);

        if (hoveredTarget.type == GameplayUtilitySpellPointerTargetType::LloydSlot)
        {
            const Character *pCaster =
                context.partyReadOnly() != nullptr
                    ? context.partyReadOnly()->member(context.utilitySpellOverlayReadOnly().casterMemberIndex)
                    : nullptr;

            if (pCaster != nullptr && hoveredTarget.index < pCaster->lloydsBeacons.size())
            {
                if (context.utilitySpellOverlayReadOnly().lloydRecallMode)
                {
                    const std::optional<LloydBeacon> &beacon = pCaster->lloydsBeacons[hoveredTarget.index];

                    if (beacon.has_value())
                    {
                        const std::string locationName =
                            beacon->locationName.empty() ? beacon->mapName : beacon->locationName;
                        context.setStatusBarHoverText(Engine::tr("Recall to {location}", {{"location", locationName}}));
                    }
                }
                else
                {
                    const std::string currentLocationName =
                        context.worldRuntime() != nullptr
                            ? context.resolveMapLocationName(context.worldRuntime()->mapName())
                            : Engine::tr("current location");
                    const std::optional<LloydBeacon> &beacon = pCaster->lloydsBeacons[hoveredTarget.index];

                    if (beacon.has_value())
                    {
                        const std::string locationName =
                            beacon->locationName.empty() ? beacon->mapName : beacon->locationName;
                        context.setStatusBarHoverText(
                            Engine::tr("Set {location} over {previous}",
                                {{"location", currentLocationName}, {"previous", locationName}}));
                    }
                    else
                    {
                        context.setStatusBarHoverText(Engine::tr("Set beacon to {location}",
                            {{"location", currentLocationName}}));
                    }
                }
            }
        }

        handlePointerClickRelease(
            pointerState,
            context.interactionState().utilitySpellClickLatch,
            context.interactionState().utilitySpellPressedTarget,
            noneTarget,
            findLloydTarget,
            [&context, &resolveSpellName](const GameplayUtilitySpellPointerTarget &target)
            {
                if (target.type == GameplayUtilitySpellPointerTargetType::Close)
                {
                    context.utilitySpellOverlay() = {};
                    context.resetUtilitySpellOverlayInteractionState();
                    context.setStatusBarEvent(Engine::tr("Spell cancelled"), 2.0f);
                    return;
                }

                if (target.type == GameplayUtilitySpellPointerTargetType::LloydSetTab)
                {
                    context.utilitySpellOverlay().lloydRecallMode = false;
                    return;
                }

                if (target.type == GameplayUtilitySpellPointerTargetType::LloydRecallTab)
                {
                    context.utilitySpellOverlay().lloydRecallMode = true;
                    return;
                }

                if (target.type != GameplayUtilitySpellPointerTargetType::LloydSlot
                    || context.partyReadOnly() == nullptr
                    || context.worldRuntime() == nullptr)
                {
                    return;
                }

                const Character *pCaster =
                    context.partyReadOnly()->member(context.utilitySpellOverlayReadOnly().casterMemberIndex);

                if (pCaster == nullptr || target.index >= pCaster->lloydsBeacons.size())
                {
                    return;
                }

                PartySpellCastRequest request = context.utilitySpellOverlayReadOnly().castRequest();
                request.utilitySlotIndex = static_cast<uint8_t>(target.index);

                if (context.utilitySpellOverlayReadOnly().lloydRecallMode)
                {
                    if (!pCaster->lloydsBeacons[target.index].has_value())
                    {
                        return;
                    }

                    request.utilityAction = PartySpellUtilityActionKind::LloydsBeaconRecall;
                    context.tryCastSpellRequest(request, resolveSpellName());
                    return;
                }

                request.utilityAction = PartySpellUtilityActionKind::LloydsBeaconSet;
                request.utilityMapMoveMapName = context.currentMapFileName();
                request.utilityStatusText = context.resolveMapLocationName(context.worldRuntime()->mapName());
                request.utilityMapMoveDirectionDegrees =
                    static_cast<int32_t>(std::lround(
                        context.gameplayCameraYawRadians() * 180.0f / 3.14159265358979323846f));

                GameplayUiController::UtilitySpellOverlayState &overlay = context.utilitySpellOverlay();
                overlay.lloydSetPreviewCapturePending = true;
                overlay.lloydSetPreviewScreenshotRequested = false;
                overlay.lloydSetPreviewStartedTicks = SDL_GetTicks();
                overlay.lloydSetPreviewRequestId =
                    "lloyds_beacon_" + std::to_string(overlay.lloydSetPreviewStartedTicks)
                    + "_" + std::to_string(target.index);
                overlay.lloydSetPreviewSpellName = resolveSpellName();
                overlay.lloydSetPreviewRequest = request;
                context.setStatusBarEvent(Engine::tr("Setting beacon"), 2.0f);
            });
        return;
    }

    const UtilityOverlayLayout layout = computeUtilityOverlayLayout(screenWidth, screenHeight);
    const auto findPointerTarget =
        [&context, &layout](float pointerX, float pointerY) -> GameplayUtilitySpellPointerTarget
        {
            if (pointInsideRect(pointerX, pointerY, layout.closeX, layout.closeY, layout.closeSize, layout.closeSize))
            {
                return {GameplayUtilitySpellPointerTargetType::Close, 0};
            }

            if (context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::LloydsBeacon)
            {
                const float tabY = layout.panelY + 24.0f;
                const float setTabX = layout.contentX;
                const float recallTabX = setTabX + layout.tabWidth + layout.tabGap;

                if (pointInsideRect(pointerX, pointerY, setTabX, tabY, layout.tabWidth, layout.tabHeight))
                {
                    return {GameplayUtilitySpellPointerTargetType::LloydSetTab, 0};
                }

                if (pointInsideRect(pointerX, pointerY, recallTabX, tabY, layout.tabWidth, layout.tabHeight))
                {
                    return {GameplayUtilitySpellPointerTargetType::LloydRecallTab, 0};
                }

                const Character *pCaster =
                    context.partyReadOnly() != nullptr
                        ? context.partyReadOnly()->member(context.utilitySpellOverlayReadOnly().casterMemberIndex)
                        : nullptr;
                const size_t slotCount = maxLloydBeaconSlots(pCaster);

                for (size_t index = 0; index < slotCount; ++index)
                {
                    const float rowY = layout.contentY + static_cast<float>(index) * (layout.rowHeight + 6.0f);

                    if (!pointInsideRect(pointerX, pointerY, layout.contentX, rowY, layout.contentWidth, layout.rowHeight))
                    {
                        continue;
                    }

                    return {GameplayUtilitySpellPointerTargetType::LloydSlot, index};
                }
            }

            return {};
        };

    handlePointerClickRelease(
        pointerState,
        context.interactionState().utilitySpellClickLatch,
        context.interactionState().utilitySpellPressedTarget,
        noneTarget,
        findPointerTarget,
        [&context, &resolveSpellName](const GameplayUtilitySpellPointerTarget &target)
        {
            if (target.type == GameplayUtilitySpellPointerTargetType::Close)
            {
                context.utilitySpellOverlay() = {};
                context.resetUtilitySpellOverlayInteractionState();
                context.setStatusBarEvent(Engine::tr("Spell cancelled"), 2.0f);
                return;
            }

            if (target.type == GameplayUtilitySpellPointerTargetType::LloydSetTab)
            {
                context.utilitySpellOverlay().lloydRecallMode = false;
                return;
            }

            if (target.type == GameplayUtilitySpellPointerTargetType::LloydRecallTab)
            {
                context.utilitySpellOverlay().lloydRecallMode = true;
                return;
            }

            PartySpellCastRequest request = context.utilitySpellOverlayReadOnly().castRequest();

            if (target.type == GameplayUtilitySpellPointerTargetType::TownPortalDestination)
            {
                if (target.index >= context.townPortalDestinations().size())
                {
                    return;
                }

                const GameplayTownPortalDestination &destination = context.townPortalDestinations()[target.index];
                request.utilityAction = PartySpellUtilityActionKind::TownPortalDestination;
                request.hasUtilityMapMove = true;
                request.utilityActionId = destination.id;
                request.utilityMapMoveMapName = destination.mapName;
                request.utilityMapMoveX = destination.x;
                request.utilityMapMoveY = destination.y;
                request.utilityMapMoveZ = destination.z;
                request.utilityMapMoveDirectionDegrees = destination.directionDegrees;
                request.utilityMapMoveUseMapStartPosition = destination.useMapStartPosition;
                request.utilityStatusText = destination.label;
                context.tryCastSpellRequest(request, resolveSpellName());
                return;
            }

            if (target.type == GameplayUtilitySpellPointerTargetType::LloydSlot)
            {
                if (context.partyReadOnly() == nullptr || context.worldRuntime() == nullptr)
                {
                    return;
                }

                const Character *pCaster =
                    context.partyReadOnly()->member(context.utilitySpellOverlayReadOnly().casterMemberIndex);

                if (pCaster == nullptr || target.index >= pCaster->lloydsBeacons.size())
                {
                    return;
                }

                request.utilitySlotIndex = static_cast<uint8_t>(target.index);

                if (context.utilitySpellOverlayReadOnly().lloydRecallMode)
                {
                    if (!pCaster->lloydsBeacons[target.index].has_value())
                    {
                        return;
                    }

                    request.utilityAction = PartySpellUtilityActionKind::LloydsBeaconRecall;
                }
                else
                {
                    request.utilityAction = PartySpellUtilityActionKind::LloydsBeaconSet;
                    request.utilityMapMoveMapName = context.currentMapFileName();
                    request.utilityStatusText = context.resolveMapLocationName(context.worldRuntime()->mapName());
                    request.utilityMapMoveDirectionDegrees =
                        static_cast<int32_t>(std::lround(
                            context.gameplayCameraYawRadians() * 180.0f / 3.14159265358979323846f));
                }

                context.tryCastSpellRequest(request, resolveSpellName());
            }
        });
}

void GameplayPartyOverlayInputController::handleSpellbookOverlayInput(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input)
{
    // The Battle Orders window and the spell menu take the pointer and Escape over the book.
    if (GameplayBattleOrders::isOpen(context))
    {
        GameplayBattleOrders::handleInput(context, input);
        context.interactionState().closeOverlayLatch = true;
        context.interactionState().spellbookClickLatch = input.leftMouseButton.held;
        return;
    }

    if (GameplayBattleOrders::spellMenuOpen(context))
    {
        GameplayBattleOrders::handleSpellMenuInput(context, input);
        context.interactionState().closeOverlayLatch = true;
        context.interactionState().spellbookClickLatch = input.leftMouseButton.held;
        return;
    }

    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!context.interactionState().closeOverlayLatch)
        {
            context.closeSpellbookOverlay();
            latchGameplayMenuEscape(context);
            context.interactionState().closeOverlayLatch = true;
        }
    }
    else
    {
        context.interactionState().closeOverlayLatch = false;
    }

    // MAW's spellbook keys: R ends every buff, Tab turns to the member's next school.
    if (Party *pParty = context.party(); pParty != nullptr)
    {
        const SpellRules &spells = gameRulesFor(pParty).spells;

        if (input.scancodePressCount(SDL_SCANCODE_R) > 0)
        {
            const std::optional<std::string> status = spells.removeAllBuffs(*pParty);

            if (status)
            {
                context.setStatusBarEvent(*status);
            }
        }

        if (input.scancodePressCount(SDL_SCANCODE_TAB) > 0 && spells.tabCyclesSpellbookSchools())
        {
            const std::array<SpellbookSchoolUiDefinition, 12> &definitions = spellbookSchoolUiDefinitions();
            const auto current = std::find_if(definitions.begin(), definitions.end(),
                [&context](const SpellbookSchoolUiDefinition &definition)
                {
                    return definition.school == context.spellbook().school;
                });
            const size_t start = current != definitions.end() ? size_t(current - definitions.begin()) : 0;

            for (size_t step = 1; step <= definitions.size(); ++step)
            {
                const SpellbookSchoolUiDefinition &next = definitions[(start + step) % definitions.size()];

                if (context.activeMemberHasSpellbookSchool(next.school))
                {
                    if (next.school != context.spellbook().school && context.audioSystem() != nullptr)
                    {
                        context.audioSystem()->playCommonSound(
                            SoundId::TurnPageDown,
                            GameAudioSystem::PlaybackGroup::Ui);
                    }

                    context.setSpellbookSchool(next.school);
                    break;
                }
            }
        }
    }

    const bool isLeftMousePressed = input.leftMouseButton.held;
    const HudPointerState pointerState = {
        input.pointerX,
        input.pointerY,
        isLeftMousePressed
    };
    const GameplaySpellbookPointerTarget noneSpellbookTarget = {};
    const auto findSpellbookPointerTarget =
        [&context, screenWidth, screenHeight](float pointerX, float pointerY) -> GameplaySpellbookPointerTarget
        {
            // A class with its own spellbook look (MAW's Death Knight and Thief lines) has its tabs and spell pictures
            // elsewhere on the page; the schools and spells they stand for are the same.
            const SpellbookSkin *pSkin = activeSpellbookSkin(context.party());
            const SpellbookSkinPage *pSkinPage = activeSpellbookSkinPage(context.party(), context.spellbook().school);
            const GameplayScreenRuntime::HudLayoutElement *pRootLayout =
                pSkin != nullptr ? context.findHudLayoutElement(SpellbookRootLayoutId) : nullptr;
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> skinRoot = pRootLayout != nullptr
                ? context.resolveHudLayoutElement(
                    SpellbookRootLayoutId, screenWidth, screenHeight, pRootLayout->width, pRootLayout->height)
                : std::nullopt;
            const std::vector<SpellbookSkinTab> skinTabs = skinRoot
                ? spellbookSkinTabs(*pSkin, [&context](SpellbookSchool school)
                    {
                        return context.activeMemberHasSpellbookSchool(school);
                    })
                : std::vector<SpellbookSkinTab>();

            for (const SpellbookSkinTab &tab : skinTabs)
            {
                if (context.isPointerInsideResolvedElement(
                        spellbookSkinScreenRect(*skinRoot, tab.rect), pointerX, pointerY))
                {
                    GameplaySpellbookPointerTarget target = {};
                    target.type = GameplaySpellbookPointerTargetType::SchoolButton;
                    target.school = tab.school;
                    return target;
                }
            }

            for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
            {
                if (!skinTabs.empty() || !context.activeMemberHasSpellbookSchool(definition.school))
                {
                    continue;
                }

                const GameplayScreenRuntime::HudLayoutElement *pLayout =
                    context.findHudLayoutElement(definition.pButtonLayoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(
                        definition.pButtonLayoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                if (resolved && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    GameplaySpellbookPointerTarget target = {};
                    target.type = GameplaySpellbookPointerTargetType::SchoolButton;
                    target.school = definition.school;
                    return target;
                }
            }

            const auto resolveSimpleButtonTarget =
                [&context, screenWidth, screenHeight, pointerX, pointerY](
                    const char *pLayoutId,
                    GameplaySpellbookPointerTargetType type) -> GameplaySpellbookPointerTarget
                {
                    const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);

                    if (pLayout == nullptr)
                    {
                        return {};
                    }

                    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                        context.resolveHudLayoutElement(
                            pLayoutId,
                            screenWidth,
                            screenHeight,
                            pLayout->width,
                            pLayout->height);

                    if (!resolved || !context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        return {};
                    }

                    GameplaySpellbookPointerTarget target = {};
                    target.type = type;
                    return target;
                };

            const GameplaySpellbookPointerTarget closeTarget =
                resolveSimpleButtonTarget("SpellbookCloseButton", GameplaySpellbookPointerTargetType::CloseButton);

            if (closeTarget.type != GameplaySpellbookPointerTargetType::None)
            {
                return closeTarget;
            }

            const GameplaySpellbookPointerTarget quickCastTarget =
                resolveSimpleButtonTarget("SpellbookQuickCastButton", GameplaySpellbookPointerTargetType::QuickCastButton);

            if (quickCastTarget.type != GameplaySpellbookPointerTargetType::None)
            {
                return quickCastTarget;
            }

            const GameplaySpellbookPointerTarget attackCastTarget = resolveSimpleButtonTarget(
                "SpellbookAttackCastButton", GameplaySpellbookPointerTargetType::AttackCastButton);

            if (attackCastTarget.type != GameplaySpellbookPointerTargetType::None)
            {
                return attackCastTarget;
            }

            const GameplaySpellbookPointerTarget ordersTarget = resolveSimpleButtonTarget(
                "SpellbookBattleOrdersButton", GameplaySpellbookPointerTargetType::BattleOrdersButton);

            if (ordersTarget.type != GameplaySpellbookPointerTargetType::None)
            {
                return ordersTarget;
            }

            const SpellbookSchoolUiDefinition *pDefinition =
                findSpellbookSchoolUiDefinition(context.spellbook().school);

            if (pDefinition == nullptr)
            {
                return {};
            }

            if (pSkinPage != nullptr && skinRoot)
            {
                for (const SpellbookSkinSpell &spell : pSkinPage->spells)
                {
                    if (context.activeMemberKnowsSpell(spell.spellId)
                        && context.isPointerInsideResolvedElement(
                            spellbookSkinScreenRect(*skinRoot, spell.rect), pointerX, pointerY))
                    {
                        GameplaySpellbookPointerTarget target = {};
                        target.type = GameplaySpellbookPointerTargetType::SpellButton;
                        target.school = context.spellbook().school;
                        target.spellId = spell.spellId;
                        return target;
                    }
                }

                return {};
            }

            for (uint32_t spellOffset = 0; spellOffset < pDefinition->spellCount; ++spellOffset)
            {
                const uint32_t spellId = pDefinition->firstSpellId + spellOffset;

                if (!context.activeMemberKnowsSpell(spellId))
                {
                    continue;
                }

                const uint32_t spellOrdinal = spellOffset + 1;
                const std::string layoutId = spellbookSpellLayoutId(context.spellbook().school, spellOrdinal);
                const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(
                        layoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                if (resolved && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    GameplaySpellbookPointerTarget target = {};
                    target.type = GameplaySpellbookPointerTargetType::SpellButton;
                    target.school = context.spellbook().school;
                    target.spellId = spellId;
                    return target;
                }
            }

            return {};
        };

    handlePointerClickRelease(
        pointerState,
        context.interactionState().spellbookClickLatch,
        context.interactionState().spellbookPressedTarget,
        noneSpellbookTarget,
        findSpellbookPointerTarget,
        [&context](const GameplaySpellbookPointerTarget &target)
        {
            if (target.type == GameplaySpellbookPointerTargetType::SchoolButton)
            {
                const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(target.school);

                if (pDefinition != nullptr)
                {
                    if (context.audioSystem() != nullptr && context.spellbook().school != target.school)
                    {
                        context.audioSystem()->playCommonSound(
                            SoundId::TurnPageDown,
                            GameAudioSystem::PlaybackGroup::Ui);
                    }

                    context.setSpellbookSchool(target.school);
                }

                return;
            }

            if (target.type == GameplaySpellbookPointerTargetType::SpellButton)
            {
                const uint64_t nowTicks = SDL_GetTicks();
                const bool isDoubleClick =
                    target.spellId != 0
                    && target.spellId == context.interactionState().lastSpellbookClickedSpellId
                    && nowTicks >= context.interactionState().lastSpellbookSpellClickTicks
                    && nowTicks - context.interactionState().lastSpellbookSpellClickTicks <= PartyPortraitDoubleClickWindowMs;
                context.spellbook().selectedSpellId = target.spellId;
                context.interactionState().lastSpellbookSpellClickTicks = nowTicks;
                context.interactionState().lastSpellbookClickedSpellId = target.spellId;

                if (isDoubleClick)
                {
                    if (!context.activeMemberKnowsSpell(target.spellId))
                    {
                        context.setStatusBarEvent(Engine::tr("Spell not learned"));
                        return;
                    }

                    const SpellEntry *pSpellEntry =
                        context.spellTable() != nullptr
                            ? context.spellTable()->findById(static_cast<int>(target.spellId))
                            : nullptr;
                    const std::string spellName =
                        pSpellEntry != nullptr && !pSpellEntry->name.empty()
                            ? pSpellEntry->name
                            : Engine::tr("Spell {id}", {{"id", int64_t(target.spellId)}});
                    const size_t casterMemberIndex =
                        context.partyReadOnly() != nullptr ? context.partyReadOnly()->activeMemberIndex() : 0;

                    context.tryCastSpellFromMember(casterMemberIndex, target.spellId, spellName);
                    context.closeSpellbookOverlay();
                }

                return;
            }

            if (target.type == GameplaySpellbookPointerTargetType::CloseButton)
            {
                context.closeSpellbookOverlay();
                return;
            }

            if (target.type == GameplaySpellbookPointerTargetType::BattleOrdersButton)
            {
                GameplayBattleOrders::open(context, false);
                return;
            }

            // Quick Cast and Attack Spell, the quick setup without the Battle Orders window: the selected spell is
            // set; the same spell again, or no spell selected, clears it.
            if (target.type == GameplaySpellbookPointerTargetType::QuickCastButton
                || target.type == GameplaySpellbookPointerTargetType::AttackCastButton)
            {
                Party *pParty = context.party();
                Character *pActiveMember = pParty != nullptr ? pParty->activeMember() : nullptr;
                const bool quickCast = target.type == GameplaySpellbookPointerTargetType::QuickCastButton;

                if (pActiveMember == nullptr || context.spellTable() == nullptr)
                {
                    context.setStatusBarEvent(
                        quickCast ? Engine::tr("Can't set quick spell") : Engine::tr("Can't set attack spell"));
                    return;
                }

                const uint32_t selectedSpellId = context.spellbook().selectedSpellId;
                const SpellEntry *pSpellEntry =
                    selectedSpellId != 0 ? context.spellTable()->findById(int(selectedSpellId)) : nullptr;

                if (pSpellEntry != nullptr && !pActiveMember->knowsSpell(selectedSpellId))
                {
                    context.setStatusBarEvent(Engine::tr("Spell not learned"));
                    return;
                }

                const size_t memberIndex = pParty->activeMemberIndex();
                const bool alreadySet = pSpellEntry != nullptr
                    && (quickCast ? pActiveMember->quickSpellName == pSpellEntry->name
                                  : isAttackSpell(pSpellEntry->name, pActiveMember->battleOrders,
                                      pActiveMember->battleOrderFallback));
                const SpellEntry *pAssigned = alreadySet ? nullptr : pSpellEntry;

                if (pAssigned == nullptr)
                {
                    context.spellbook().selectedSpellId = 0;
                }

                if (quickCast)
                {
                    GameplayBattleOrders::assignQuickSlot(context, memberIndex, 0, pAssigned);
                }
                else
                {
                    GameplayBattleOrders::assignAttackSpell(context, memberIndex, pAssigned);
                }
            }
        });

    // A quick right click on a known spell opens its menu (Quick Cast, the quick spells, the orders); a held one only
    // inspects it (GameplayHudOverlaySupport::updateSpellInspectOverlay).
    GameplayUiController::SpellbookSpellMenuState &spellMenu = context.spellbook().spellMenu;

    // Followed by the button's held state, so a press or release on a frame this handler misses still counts.
    if (input.rightMouseButton.held && !spellMenu.rightHeld)
    {
        spellMenu.rightHeld = true;
        const GameplaySpellbookPointerTarget pressed = findSpellbookPointerTarget(input.pointerX, input.pointerY);
        spellMenu.rightPressSpellId =
            pressed.type == GameplaySpellbookPointerTargetType::SpellButton ? pressed.spellId : 0;
        spellMenu.rightPressTicks = SDL_GetTicks();
    }
    else if (!input.rightMouseButton.held && spellMenu.rightHeld)
    {
        spellMenu.rightHeld = false;
        const GameplaySpellbookPointerTarget released = findSpellbookPointerTarget(input.pointerX, input.pointerY);

        if (spellMenu.rightPressSpellId != 0
            && released.type == GameplaySpellbookPointerTargetType::SpellButton
            && released.spellId == spellMenu.rightPressSpellId
            && SDL_GetTicks() - spellMenu.rightPressTicks <= GameplayBattleOrders::SpellMenuClickMilliseconds)
        {
            GameplayBattleOrders::openSpellMenu(context, released.spellId, input.pointerX, input.pointerY);
        }

        spellMenu.rightPressSpellId = 0;
    }
}

namespace
{
// Opens a member's bag (MAW's multibag) and says which one is open.
bool openInventoryBag(GameplayScreenRuntime &context, Party &party, size_t memberIndex, int bag)
{
    Character *pMember = party.member(memberIndex);
    const int bagCount = gameRulesFor(&party).items.bagCount(party);

    if (pMember == nullptr || bag < 0 || !InventoryBags::openBag(*pMember, uint8_t(bag), bagCount))
    {
        return false;
    }

    const std::string name = InventoryBagOverview::bagName(bag, bagCount);
    context.setStatusBarEvent(Engine::Utf8::capitalizedFirst(name));
    return true;
}

// A bag's button or key: the bag at full size; on the bag already zoomed, back to the overview.
void zoomInventoryBag(GameplayScreenRuntime &context, Party &party, size_t memberIndex, int bag)
{
    GameplayUiController::CharacterScreenState &screen = context.characterScreen();
    const Character *pMember = party.member(memberIndex);

    if (pMember == nullptr)
    {
        return;
    }

    if (screen.inventoryBagZoomed && pMember->rulesetState.currentBag == bag)
    {
        screen.inventoryBagZoomed = false;
        return;
    }

    if (pMember->rulesetState.currentBag != bag && !openInventoryBag(context, party, memberIndex, bag))
    {
        return;
    }

    screen.inventoryBagZoomed = true;
}

// A click on a bag of the overview (InventoryBagOverview): a held item goes into the bag at the cell under it, as on
// the full-size grid (the one item in the way comes out held); with nothing held, the item there is taken. The open
// bag stays open.
void activateBagOverviewTarget(
    GameplayScreenRuntime &context,
    Party &party,
    size_t memberIndex,
    const GameplayCharacterPointerTarget &target,
    const std::optional<GameplayResolvedHudLayoutElement> &grid,
    float pointerX,
    float pointerY,
    const std::function<void(const InventoryItem &)> &setHeldItem,
    const std::function<void()> &clearHeldItem)
{
    if (!grid || party.member(memberIndex) == nullptr || context.itemTable() == nullptr)
    {
        return;
    }

    const int bagCount = gameRulesFor(&party).items.bagCount(party);
    const InventoryBagOverview::Slot slot = InventoryBagOverview::slot(*grid, target.bag);
    const InventoryGridMetrics metrics =
        computeInventoryGridMetrics(slot.x, slot.y, slot.width, slot.height, grid->scale * slot.fraction);
    GameplayUiController::HeldInventoryItemState &held = context.heldInventoryItem();
    // The item's icon size on this bag's grid.
    const auto iconSize = [&context, &metrics](const InventoryItem &item) -> std::optional<std::pair<float, float>>
    {
        const ItemDefinition *pDefinition = context.itemTable()->get(item.objectDescriptionId);
        const std::optional<GameplayHudTextureHandle> texture = pDefinition != nullptr && !pDefinition->iconName.empty()
            ? context.gameplayUiRuntime().ensureItemIconTextureLoaded(pDefinition->iconName)
            : std::nullopt;

        if (!texture)
        {
            return std::nullopt;
        }

        return std::pair(float(texture->width) * metrics.scale * pDefinition->inventoryDrawScale,
            float(texture->height) * metrics.scale * pDefinition->inventoryDrawScale);
    };

    if (held.active)
    {
        // The drop cell the renderer's placement preview shows too.
        const std::optional<std::pair<float, float>> size = iconSize(held.item);

        if (!size)
        {
            return;
        }

        const auto [gridX, gridY] = InventoryBagOverview::dropCell(slot, *party.member(memberIndex), target.bag,
            held.item, size->first, size->second, pointerX, pointerY, held.grabOffsetX, held.grabOffsetY);

        if (gridX < 0 || gridY < 0)
        {
            return;
        }

        std::optional<InventoryItem> replacedItem;

        if (!InventoryBags::placeInBag(
                party, memberIndex, target.bag, bagCount, held.item, uint8_t(gridX), uint8_t(gridY), replacedItem))
        {
            const std::string &partyStatus = party.lastStatus();
            context.setStatusBarEvent(
                partyStatus.empty() || partyStatus == "inventory full" ? Engine::tr("Pack is Full!") : partyStatus);
            return;
        }

        if (replacedItem)
        {
            setHeldItem(*replacedItem);
        }
        else
        {
            clearHeldItem();
        }

        return;
    }

    InventoryItem item = {};

    if (!InventoryBags::takeFromBag(party, memberIndex, target.bag, bagCount, target.gridX, target.gridY, item))
    {
        return;
    }

    setHeldItem(item);
    const auto [cellX, cellY] = InventoryBagOverview::cellAt(slot, pointerX, pointerY);
    held.grabCellOffsetX = cellX - item.gridX;
    held.grabCellOffsetY = cellY - item.gridY;

    // The grab offsets stay in full-size units, as the full-size grid keeps them; the held item shrinks over a bag.
    if (const std::optional<std::pair<float, float>> size = iconSize(item))
    {
        const InventoryItemScreenRect rect = computeInventoryItemScreenRect(metrics, item, size->first, size->second);
        held.grabOffsetX = (pointerX - rect.x) / slot.fraction;
        held.grabOffsetY = (pointerY - rect.y) / slot.fraction;
    }
}
}

bool GameplayPartyOverlayInputController::partyBagButtonsShown(const GameplayScreenRuntime &context)
{
    const IGameplayWorldRuntime *pWorldRuntime = context.worldRuntime();
    return context.inventoryNestedOverlay().active
        || (pWorldRuntime != nullptr && pWorldRuntime->activeChestView() != nullptr
            && context.currentHudScreenState() == GameplayHudScreenState::Chest);
}

bool GameplayPartyOverlayInputController::bagKeysActive(const GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr && gameRulesFor(pParty).items.bagCount(*pParty) > 1
        && (partyBagButtonsShown(context)
            || (context.characterScreenReadOnly().open
                && context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory
                && !context.isAdventurersInnCharacterSourceActive()));
}

bool GameplayPartyOverlayInputController::bagKeysNeedShift(const GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();
    return context.settingsSnapshot().bagNumberKeys != "bag" && pParty != nullptr && pParty->memberCount() > 1;
}

bool GameplayPartyOverlayInputController::openBagForKey(GameplayScreenRuntime &context, int bag)
{
    Party *pParty = context.party();
    const int bagCount = pParty != nullptr ? gameRulesFor(pParty).items.bagCount(*pParty) : 1;

    if (pParty == nullptr || bagCount <= 1 || bag < 0 || bag >= InventoryBagOverview::Bags)
    {
        return false;
    }

    if (partyBagButtonsShown(context))
    {
        const Character *pMember = pParty->activeMember();
        const int tabBag = pMember != nullptr ? InventoryBagOverview::firstBag(*pMember) + bag : bag;

        if (tabBag < bagCount)
        {
            openNestedInventoryBag(context, tabBag);
        }

        return true;
    }

    if (!context.characterScreenReadOnly().open
        || context.characterScreenReadOnly().page != GameplayUiController::CharacterPage::Inventory
        || context.isAdventurersInnCharacterSourceActive())
    {
        return false;
    }

    const size_t memberIndex = context.selectedCharacterScreenSourceIndex();
    const Character *pMember = pParty->member(memberIndex);
    const int tabBag = pMember != nullptr ? InventoryBagOverview::firstBag(*pMember) + bag : bag;

    if (tabBag < bagCount)
    {
        zoomInventoryBag(context, *pParty, memberIndex, tabBag);
    }

    return true;
}

bool GameplayPartyOverlayInputController::bagTabsShown(const GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr && InventoryBags::tabCount(gameRulesFor(pParty).items.bagCount(*pParty)) > 1
        && bagKeysActive(context);
}

bool GameplayPartyOverlayInputController::openBagTab(GameplayScreenRuntime &context, int tab)
{
    Party *pParty = context.party();

    if (pParty == nullptr || !bagTabsShown(context))
    {
        return false;
    }

    const int bagCount = gameRulesFor(pParty).items.bagCount(*pParty);
    const size_t memberIndex =
        partyBagButtonsShown(context) ? pParty->activeMemberIndex() : context.selectedCharacterScreenSourceIndex();
    Character *pMember = pParty->member(memberIndex);

    if (pMember == nullptr || tab < 0 || tab >= InventoryBags::tabCount(bagCount))
    {
        return false;
    }

    // The same bag of the other tab, as MAW keeps it (zzMaw-MultiBag.lua:153-157); the overview shows the whole tab.
    const int bag = std::min(tab * InventoryBags::TabBags + pMember->rulesetState.currentBag % InventoryBags::TabBags,
        bagCount - 1);

    if (InventoryBags::openBag(*pMember, uint8_t(bag), bagCount))
    {
        const std::string name = InventoryBagOverview::bagName(bag, bagCount);
        context.setStatusBarEvent(Engine::Utf8::capitalizedFirst(name));
    }

    return true;
}

void GameplayPartyOverlayInputController::openNestedInventoryBag(GameplayScreenRuntime &context, int bag)
{
    Party *pParty = context.party();
    Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;
    const int bagCount = pParty != nullptr ? gameRulesFor(pParty).items.bagCount(*pParty) : 1;
    GameplayUiController::InventoryNestedOverlayState &overlay = context.inventoryNestedOverlay();
    const bool shopOverview = GameplayHudOverlaySupport::shopBagOverviewActive(context);

    if (pMember == nullptr || bagCount <= 1 || bag < 0 || bag >= bagCount)
    {
        return;
    }

    if (overlay.bagZoomed && pMember->rulesetState.currentBag == bag)
    {
        overlay.bagZoomed = false;
        return;
    }

    if (InventoryBags::openBag(*pMember, uint8_t(bag), bagCount) || shopOverview)
    {
        const std::string name = InventoryBagOverview::bagName(bag, bagCount);
        context.setStatusBarEvent(Engine::Utf8::capitalizedFirst(name));
    }

    if (shopOverview)
    {
        overlay.bagZoomed = true;
    }
}

void GameplayPartyOverlayInputController::openFirstBagsInOverview(GameplayScreenRuntime &context)
{
    Party *pParty = context.party();

    if (pParty == nullptr
        || !((context.characterScreenReadOnly().open && GameplayHudOverlaySupport::bagOverviewActive(context))
            || GameplayHudOverlaySupport::shopBagOverviewActive(context)))
    {
        return;
    }

    const int bagCount = gameRulesFor(pParty).items.bagCount(*pParty);

    for (size_t memberIndex = 0; memberIndex < pParty->memberCount(); ++memberIndex)
    {
        Character &member = *pParty->member(memberIndex);
        InventoryBags::openBag(member, InventoryBagOverview::firstBag(member), bagCount);
    }
}

bool GameplayPartyOverlayInputController::toggleBagTag(GameplayScreenRuntime &context, BagTag tag)
{
    Party *pParty = context.party();
    const int bagCount = pParty != nullptr ? gameRulesFor(pParty).items.bagCount(*pParty) : 1;
    Character *pMember = pParty != nullptr ? pParty->member(context.selectedCharacterScreenSourceIndex()) : nullptr;

    if (pMember == nullptr || bagCount <= 1 || !context.characterScreenReadOnly().open
        || context.characterScreenReadOnly().page != GameplayUiController::CharacterPage::Inventory
        || context.isAdventurersInnCharacterSourceActive())
    {
        return false;
    }

    const uint8_t bag = pMember->rulesetState.currentBag;
    const bool tagged = InventoryBags::toggleTag(*pMember, bag, tag);
    const std::string bagName = InventoryBagOverview::bagName(bag, bagCount);
    const bool crafting = tag == BagTag::Crafting;
    const std::initializer_list<Engine::TextArgument> arguments = {{"name", pMember->name}, {"bag", bagName}};
    context.setStatusBarEvent(tagged
            ? (crafting ? Engine::tr("{name}'s {bag} is now a crafting bag", arguments)
                        : Engine::tr("{name}'s {bag} is now an alchemy bag", arguments))
            : (crafting ? Engine::tr("{name}'s {bag} is no longer a crafting bag", arguments)
                        : Engine::tr("{name}'s {bag} is no longer an alchemy bag", arguments)));
    return true;
}

bool GameplayPartyOverlayInputController::openWorkbench(GameplayScreenRuntime &context)
{
    if (context.heldInventoryItem().active)
    {
        context.setStatusBarEvent(Engine::tr("Put the item down first."));
        return false;
    }

    // Every visit starts with empty slots; filters and the search stay as the player left them.
    GameplayUiController::CharacterScreenState &screen = context.characterScreen();
    GameplayUiController::AlchemyBenchState &bench = screen.alchemyBench;
    screen.page = GameplayUiController::CharacterPage::Inventory;
    bench.active = true;
    bench.targetItemId = 0;
    bench.heldItemId = 0;
    bench.selectedResultItemId = 0;
    bench.recipeSearchActive = false;
    bench.clearBrewResult();
    bench.newRecipeResultIds.clear();
    bench.crafting.target.reset();
    bench.crafting.material.reset();
    bench.crafting.choice = 0;
    bench.crafting.searchActive = false;
    bench.crafting.clearResult();
    screen.dollJewelryOverlayOpen = false;
    return true;
}

std::optional<std::string> GameplayPartyOverlayInputController::skillSwitchForAction(
    GameplayScreenRuntime &context,
    KeyboardAction action)
{
    const std::string skillName = action == KeyboardAction::SkillCover ? "Cover"
        : action == KeyboardAction::SkillManaShield                      ? "ManaShield"
                                                                         : "";
    const Character *pCharacter = context.selectedCharacterScreenCharacter();

    if (skillName.empty() || !context.characterScreenReadOnly().open
        || context.characterScreenReadOnly().page != GameplayUiController::CharacterPage::Skills
        || context.isAdventurersInnCharacterSourceActive() || pCharacter == nullptr
        || !gameRulesFor(context.partyReadOnly()).skills.skillSwitch(*pCharacter, skillName))
    {
        return std::nullopt;
    }

    return skillName;
}

bool GameplayPartyOverlayInputController::toggleSkillSwitch(GameplayScreenRuntime &context, const std::string &skill)
{
    Character *pCharacter = const_cast<Character *>(context.selectedCharacterScreenCharacter());

    if (pCharacter == nullptr || context.isAdventurersInnCharacterSourceActive())
    {
        return false;
    }

    const std::optional<bool> on = gameRulesFor(context.partyReadOnly()).skills.toggleSkillSwitch(*pCharacter, skill);

    if (!on)
    {
        return false;
    }

    const std::string name = Engine::localize(displaySkillName(skill), "skill");
    context.setStatusBarEvent(
        *on ? Engine::tr("{skill} enabled", {{"skill", name}}) : Engine::tr("{skill} disabled", {{"skill", name}}));
    return true;
}

bool GameplayPartyOverlayInputController::toggleSkillRotation(GameplayScreenRuntime &context)
{
    Character *pCharacter = const_cast<Character *>(context.selectedCharacterScreenCharacter());

    if (pCharacter == nullptr || context.isAdventurersInnCharacterSourceActive())
    {
        return false;
    }

    const std::optional<bool> on = gameRulesFor(context.partyReadOnly()).spells.toggleSpellRotation(*pCharacter);

    if (!on)
    {
        return false;
    }

    context.setStatusBarEvent(
        *on ? Engine::tr("Elementalist rotation enabled") : Engine::tr("Elementalist rotation disabled"));
    return true;
}

void GameplayPartyOverlayInputController::handleCharacterOverlayInput(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    Character *pActiveCharacter = const_cast<Character *>(context.selectedCharacterScreenCharacter());
    Party *pParty = context.party();
    const bool isReadOnlyAdventurersInnView = context.isReadOnlyAdventurersInnCharacterViewActive();
    const size_t selectedPartyMemberIndex =
        pParty != nullptr && !context.isAdventurersInnCharacterSourceActive()
            ? context.selectedCharacterScreenSourceIndex()
            : (pParty != nullptr ? pParty->activeMemberIndex() : 0);
    const Character *pSelectedPartyMember =
        pParty != nullptr && !context.isAdventurersInnCharacterSourceActive()
            ? pParty->member(selectedPartyMemberIndex)
            : nullptr;
    const bool selectedPartyMemberCanAct =
        pSelectedPartyMember != nullptr && GameMechanics::canAct(*pSelectedPartyMember);
    const auto clearPendingCharacterDismiss =
        [&context]()
        {
            context.interactionState().pendingCharacterDismissMemberIndex = std::nullopt;
            context.interactionState().pendingCharacterDismissExpiresTicks = 0;
        };
    const uint64_t nowTicks = SDL_GetTicks();

    if (pParty == nullptr
        || context.isAdventurersInnCharacterSourceActive()
        || (context.interactionState().pendingCharacterDismissMemberIndex.has_value()
            && (nowTicks > context.interactionState().pendingCharacterDismissExpiresTicks
                || *context.interactionState().pendingCharacterDismissMemberIndex >= pParty->members().size()
                || *context.interactionState().pendingCharacterDismissMemberIndex != selectedPartyMemberIndex)))
    {
        clearPendingCharacterDismiss();
    }

    if (!input.isScancodeHeld(SDL_SCANCODE_ESCAPE))
    {
        context.interactionState().alchemyBenchEscapeLatch = false;
    }

    if (context.characterScreenReadOnly().alchemyBench.active)
    {
        GameplayAlchemyBenchInputController::handleInput(context, input);
        return;
    }

    const CharacterDollTable *pCharacterDollTable = context.characterDollTable();
    const CharacterDollEntry *pActiveCharacterDollEntry =
        resolveCharacterDollEntry(pCharacterDollTable, pActiveCharacter);
    const CharacterDollTypeEntry *pActiveCharacterDollType =
        pActiveCharacterDollEntry != nullptr && pCharacterDollTable != nullptr
            ? pCharacterDollTable->getDollType(pActiveCharacterDollEntry->dollTypeId)
            : nullptr;
    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(
        pActiveCharacter, !isReadOnlyAdventurersInnView, gameRulesFor(context.partyReadOnly()).skills);
    const float skillRowHeight = context.characterSkillRowHeight();
    context.clearHudLayoutRuntimeHeightOverrides();
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsWeaponsListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.weaponRows.size())));
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsMagicListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.magicRows.size())));
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsArmorListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.armorRows.size())));
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsMiscListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.miscRows.size())));
    context.setHudLayoutRuntimeHeightOverride(
        "CharacterSkillsTechListRegion",
        skillRowHeight * static_cast<float>(std::max<size_t>(1, skillUiData.techRows.size())));

    GameplayUiController::CharacterScreenState &screen = context.characterScreen();
    const bool skillsPage = screen.page == GameplayUiController::CharacterPage::Skills;
    const bool awardsPage = screen.page == GameplayUiController::CharacterPage::Awards;
    // Keys typed into the item search are text, not the screen's keys.
    const bool searchTyping = handleInventorySearch(context, input);

    for (const KeyboardAction action : {KeyboardAction::SkillCover, KeyboardAction::SkillManaShield})
    {
        const std::optional<std::string> switchedSkill = skillSwitchForAction(context, action);

        if (switchedSkill && !isReadOnlyAdventurersInnView && !searchTyping && input.action(action).pressed)
        {
            toggleSkillSwitch(context, *switchedSkill);
        }
    }

    // The alchemist key on the inventory picks the member who takes the alchemy items when sorting (MAW's E).
    if (screen.page == GameplayUiController::CharacterPage::Inventory && pParty != nullptr && !searchTyping
        && !context.isAdventurersInnCharacterSourceActive() && input.action(KeyboardAction::AlchemistPick).pressed)
    {
        if (const std::optional<std::string> status =
                gameRulesFor(pParty).items.pickAlchemist(*pParty, selectedPartyMemberIndex))
        {
            context.setStatusBarEvent(*status);
        }
    }

    // R on the skills page switches an Elementalist's spell rotation (MAW).
    if (skillsPage && !isReadOnlyAdventurersInnView && !searchTyping
        && input.action(KeyboardAction::SkillRotation).pressed)
    {
        toggleSkillRotation(context);
    }
    if (!input.leftMouseButton.held)
    {
        screen.scrollDragOffset.reset();
    }
    if (skillsPage || awardsPage)
    {
        const std::optional<GameplayResolvedHudLayoutElement> viewport = context.resolveHudLayoutElement(
            skillsPage ? "CharacterSkillsViewport" : "CharacterAwardsList", screenWidth, screenHeight, 0, 0);
        if (viewport)
        {
            const float contentHeight = skillsPage ? context.characterSkillsContentHeight(screenWidth, screenHeight) : 0;
            const float maximum = skillsPage ? std::max(0.0f, contentHeight - viewport->height / viewport->scale)
                : float(screen.awardMaximumScrollOffset);
            const float visible = skillsPage
                ? std::min(1.0f, viewport->height / std::max(1.0f, contentHeight * viewport->scale))
                : screen.awardVisibleFraction;
            float offset = skillsPage ? screen.skillScrollOffset : float(screen.awardScrollOffset);
            const bool inside = context.isPointerInsideResolvedElement(*viewport, input.pointerX, input.pointerY);
            if (inside)
            {
                offset -= input.mouseWheelDelta * (skillsPage ? skillRowHeight * 3 : 1);
            }
            offset = std::clamp(offset, 0.0f, maximum);
            GameplayResolvedHudLayoutElement thumb = GameplayUiSkin::scrollbarThumb(
                *viewport, maximum > 0 ? offset / maximum : 0, visible);
            const bool trackHit = inside && input.pointerX >= viewport->x + viewport->width - 8 * viewport->scale;
            bool consumed = false;
            if (maximum > 0 && trackHit && input.leftMouseButton.pressed)
            {
                consumed = true;
                if (input.pointerY >= thumb.y && input.pointerY <= thumb.y + thumb.height)
                {
                    screen.scrollDragOffset = input.pointerY - thumb.y;
                }
                else
                {
                    const float page = skillsPage ? viewport->height / viewport->scale
                        : std::max(1.0f, maximum * visible / std::max(0.01f, 1 - visible));
                    offset += input.pointerY < thumb.y ? -page : page;
                }
            }
            if (screen.scrollDragOffset && maximum > 0 && viewport->height > thumb.height)
            {
                offset = (input.pointerY - viewport->y - *screen.scrollDragOffset)
                    / (viewport->height - thumb.height) * maximum;
                consumed = true;
            }
            offset = std::clamp(offset, 0.0f, maximum);
            if (skillsPage)
            {
                screen.skillScrollOffset = offset;
            }
            else
            {
                screen.awardScrollOffset = size_t(std::round(offset));
            }
            if (consumed)
            {
                return;
            }
        }
    }

    // The Use key on a pack item uses or equips it (below); only a keyboard key, not the classic scheme's left button.
    const InputBinding useBinding = context.settingsSnapshot().keyboard.binding(KeyboardAction::Use);
    const bool useKeyBound = !searchTyping && useBinding.kind == InputBindingKind::Keyboard;
    const bool useKeyPressed = useKeyBound && isScancodeNewlyPressed(context, input, useBinding.scancode);
    const bool useKeyHeld = useKeyBound && input.isScancodeHeld(useBinding.scancode);
    // Only Escape closes the screen (a missed Use press must not). The Escape that closed the alchemy bench or
    // cleared the item search keeps the screen open until it is released.
    const bool closePressed = !searchTyping
        && pKeyboardState != nullptr
        && pKeyboardState[SDL_SCANCODE_ESCAPE]
        && !context.interactionState().alchemyBenchEscapeLatch;
    const bool isInventorySpellTargetMode =
        context.utilitySpellOverlayReadOnly().active
        && context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;
    const auto closeScreen =
        [&context, &clearPendingCharacterDismiss, isInventorySpellTargetMode]()
        {
            if (isInventorySpellTargetMode)
            {
                context.utilitySpellOverlay() = {};
            }

            context.closeCharacterScreen();
            clearPendingCharacterDismiss();
            latchGameplayMenuEscape(context);
            context.interactionState().closeOverlayLatch = true;
        };

    if (closePressed)
    {
        if (!context.interactionState().closeOverlayLatch)
        {
            closeScreen();
        }
        return;
    }
    else
    {
        context.interactionState().closeOverlayLatch = false;
    }

    const bool charCycleNewlyPressed = !searchTyping && input.action(KeyboardAction::CharCycle).pressed;

    if (charCycleNewlyPressed)
    {
        if (pParty != nullptr && !pParty->members().empty())
        {
            const size_t nextMemberIndex = (selectedPartyMemberIndex + 1) % pParty->members().size();
            context.characterScreen().source = GameplayUiController::CharacterScreenSource::Party;
            context.characterScreen().sourceIndex = nextMemberIndex;

            if (pParty->canSelectMemberInGameplay(nextMemberIndex))
            {
                context.trySelectPartyMember(nextMemberIndex, true);
            }
        }

        context.interactionState().characterMemberCycleLatch = true;
    }
    else
    {
        context.interactionState().characterMemberCycleLatch = false;
    }

    const float mouseX = input.pointerX;
    const float mouseY = input.pointerY;
    const bool isLeftMousePressed = input.leftMouseButton.held;
    const bool rightMousePressed = input.rightMouseButton.pressed;

    const auto resolveCharacterInventoryGrid =
        [&context, screenWidth, screenHeight]() -> std::optional<GameplayResolvedHudLayoutElement>
        {
            const UiLayoutManager::LayoutElement *pInventoryGridLayout =
                context.findHudLayoutElement("CharacterInventoryGrid");

            if (pInventoryGridLayout == nullptr)
            {
                return std::nullopt;
            }

            return context.resolveHudLayoutElement(
                "CharacterInventoryGrid",
                screenWidth,
                screenHeight,
                pInventoryGridLayout->width,
                pInventoryGridLayout->height);
        };

    const auto findCharacterPointerTarget =
        [&context,
         screenWidth,
         screenHeight,
         skillRowHeight,
         &skillUiData,
         pParty,
         isReadOnlyAdventurersInnView,
         pActiveCharacter,
         pActiveCharacterDollEntry,
         pActiveCharacterDollType,
         &resolveCharacterInventoryGrid](float pointerX, float pointerY) -> GameplayCharacterPointerTarget
        {
            if (screenWidth <= 0 || screenHeight <= 0)
            {
                return {};
            }

            if (context.isAdventurersInnScreenActive())
            {
                const auto resolveButtonTarget =
                    [&context, screenWidth, screenHeight, pointerX, pointerY](
                        const char *pLayoutId,
                        GameplayCharacterPointerTargetType targetType) -> GameplayCharacterPointerTarget
                    {
                        const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);

                        if (pLayout == nullptr)
                        {
                            return {};
                        }

                        const std::optional<GameplayResolvedHudLayoutElement> resolved =
                            context.resolveHudLayoutElement(
                                pLayoutId,
                                screenWidth,
                                screenHeight,
                                pLayout->width,
                                pLayout->height);

                        if (resolved.has_value()
                            && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                        {
                            return {targetType};
                        }

                        return {};
                    };

                GameplayCharacterPointerTarget target = resolveButtonTarget(
                    "AdventurersInnExitButton",
                    GameplayCharacterPointerTargetType::ExitButton);

                if (target.type != GameplayCharacterPointerTargetType::None)
                {
                    return target;
                }

                if (pParty != nullptr && !pParty->isFull())
                {
                    target = resolveButtonTarget(
                        "AdventurersInnHireButton",
                        GameplayCharacterPointerTargetType::AdventurersInnHireButton);

                    if (target.type != GameplayCharacterPointerTargetType::None)
                    {
                        return target;
                    }
                }

                target = resolveButtonTarget(
                    "AdventurersInnScrollUpButton",
                    GameplayCharacterPointerTargetType::AdventurersInnScrollUpButton);

                if (target.type != GameplayCharacterPointerTargetType::None)
                {
                    return target;
                }

                target = resolveButtonTarget(
                    "AdventurersInnScrollDownButton",
                    GameplayCharacterPointerTargetType::AdventurersInnScrollDownButton);

                if (target.type != GameplayCharacterPointerTargetType::None)
                {
                    return target;
                }

                if (pParty != nullptr)
                {
                    constexpr size_t VisibleRows = 4;
                    constexpr size_t VisibleColumns = 2;
                    constexpr size_t VisibleCount = VisibleRows * VisibleColumns;
                    constexpr float PortraitX = 34.0f;
                    constexpr float PortraitY = 47.0f;
                    constexpr float PortraitWidth = 62.0f;
                    constexpr float PortraitHeight = 72.0f;
                    constexpr float PortraitGapX = 3.0f;
                    constexpr float PortraitGapY = 3.0f;
                    const GameplayUiViewportRect uiViewport =
                        GameplayHudCommon::computeUiViewportRect(screenWidth, screenHeight);
                    const float baseScale = std::min(
                        std::min(uiViewport.width / 640.0f, uiViewport.height / 480.0f),
                        MaxUiScale);

                    const size_t scrollOffset = std::min(
                        context.characterScreenReadOnly().adventurersInnScrollOffset,
                        pParty->adventurersInnMembers().size());
                    const size_t visibleCount =
                        std::min(VisibleCount, pParty->adventurersInnMembers().size() - scrollOffset);

                    for (size_t visibleIndex = 0; visibleIndex < visibleCount; ++visibleIndex)
                    {
                        const size_t column = visibleIndex % VisibleColumns;
                        const size_t row = visibleIndex / VisibleColumns;
                        const float x =
                            uiViewport.x
                            + (PortraitX + static_cast<float>(column) * (PortraitWidth + PortraitGapX))
                                * baseScale;
                        const float y =
                            uiViewport.y
                            + (PortraitY + static_cast<float>(row) * (PortraitHeight + PortraitGapY))
                                * baseScale;
                        const float w = PortraitWidth * baseScale;
                        const float h = PortraitHeight * baseScale;

                        if (pointerX >= x && pointerX < x + w && pointerY >= y && pointerY < y + h)
                        {
                            target.type = GameplayCharacterPointerTargetType::AdventurersInnPortrait;
                            target.innIndex = scrollOffset + visibleIndex;
                            return target;
                        }
                    }
                }

                return {};
            }

            struct CharacterTabTarget
            {
                const char *pLayoutId;
                GameplayUiController::CharacterPage page;
            };

            static constexpr CharacterTabTarget TabTargets[] = {
                {"CharacterStatsButton", GameplayUiController::CharacterPage::Stats},
                {"CharacterSkillsButton", GameplayUiController::CharacterPage::Skills},
                {"CharacterInventoryButton", GameplayUiController::CharacterPage::Inventory},
                {"CharacterAwardsButton", GameplayUiController::CharacterPage::Awards},
            };

            for (const CharacterTabTarget &target : TabTargets)
            {
                const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(target.pLayoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<GameplayResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(
                        target.pLayoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                if (resolved.has_value() && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    GameplayCharacterPointerTarget pointerTarget = {};
                    pointerTarget.type = GameplayCharacterPointerTargetType::PageButton;
                    pointerTarget.page = target.page;
                    return pointerTarget;
                }
            }

            const auto resolveCharacterButtonTarget =
                [&context, screenWidth, screenHeight, pointerX, pointerY](
                    const char *pLayoutId,
                    GameplayCharacterPointerTargetType targetType) -> GameplayCharacterPointerTarget
                {
                    const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);

                    if (pLayout == nullptr)
                    {
                        return {};
                    }

                    const std::optional<GameplayResolvedHudLayoutElement> resolved =
                        context.resolveHudLayoutElement(
                            pLayoutId,
                            screenWidth,
                            screenHeight,
                            pLayout->width,
                            pLayout->height);

                    if (!resolved.has_value() || !context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        return {};
                    }

                    GameplayCharacterPointerTarget target = {};
                    target.type = targetType;
                    return target;
                };

            if (!context.isAdventurersInnCharacterSourceActive() && pParty != nullptr && pParty->activeMemberIndex() > 0)
            {
                const UiLayoutManager::LayoutElement *pDismissLayout =
                    context.findHudLayoutElement("CharacterDismissButton");

                if (pDismissLayout != nullptr)
                {
                    const std::optional<GameplayResolvedHudLayoutElement> resolved =
                        context.resolveHudLayoutElement(
                            "CharacterDismissButton",
                            screenWidth,
                            screenHeight,
                            pDismissLayout->width,
                            pDismissLayout->height);

                    if (resolved.has_value() && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        return {GameplayCharacterPointerTargetType::DismissButton};
                    }
                }
            }

            if (!context.isAdventurersInnCharacterSourceActive())
            {
                const GameplayCharacterPointerTarget alchemyTarget = resolveCharacterButtonTarget(
                    "CharacterAlchemyButton",
                    GameplayCharacterPointerTargetType::AlchemyButton);

                if (alchemyTarget.type != GameplayCharacterPointerTargetType::None)
                {
                    return alchemyTarget;
                }
            }

            if (!context.isAdventurersInnCharacterSourceActive()
                && context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory)
            {
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
                // Touch has no world under the cursor to drop on, so the held item turns Sort into Drop.
                const GameplayCharacterPointerTargetType sortTargetType = context.heldInventoryItem().active
                    ? GameplayCharacterPointerTargetType::InventoryDropButton
                    : GameplayCharacterPointerTargetType::InventorySortButton;
#else
                const GameplayCharacterPointerTargetType sortTargetType =
                    GameplayCharacterPointerTargetType::InventorySortButton;
#endif
                const GameplayCharacterPointerTarget sortTarget =
                    resolveCharacterButtonTarget("CharacterInventorySortButton", sortTargetType);

                if (sortTarget.type != GameplayCharacterPointerTargetType::None)
                {
                    return sortTarget;
                }

                // MAW's multibag: the overview's button and a button per bag.
                const int bagCount = pParty != nullptr ? gameRulesFor(pParty).items.bagCount(*pParty) : 1;
#if !defined(__ANDROID__)
                if (bagCount > 1)
                {
                    const GameplayCharacterPointerTarget overviewTarget = resolveCharacterButtonTarget(
                        "CharacterInventoryBagOverview", GameplayCharacterPointerTargetType::InventoryBagOverviewButton);

                    if (overviewTarget.type != GameplayCharacterPointerTargetType::None)
                    {
                        return overviewTarget;
                    }
                }
#endif

                for (const auto &[pTagId, tag] : {std::pair("CharacterInventoryCraftingTag", BagTag::Crafting),
                         std::pair("CharacterInventoryAlchemyTag", BagTag::Alchemy)})
                {
                    GameplayCharacterPointerTarget tagTarget = bagCount > 1
                        ? resolveCharacterButtonTarget(
                              pTagId, GameplayCharacterPointerTargetType::InventoryBagTagButton)
                        : GameplayCharacterPointerTarget{};

                    if (tagTarget.type != GameplayCharacterPointerTargetType::None)
                    {
                        tagTarget.bagButton = uint8_t(tag);
                        return tagTarget;
                    }
                }

                for (uint8_t button = 0; int(button) < std::min(bagCount, InventoryBagOverview::Bags) && bagCount > 1;
                     ++button)
                {
                    const std::string bagId = "CharacterInventoryBag" + std::to_string(button + 1);
                    GameplayCharacterPointerTarget bagTarget =
                        resolveCharacterButtonTarget(bagId.c_str(), GameplayCharacterPointerTargetType::InventoryBagButton);

                    if (bagTarget.type != GameplayCharacterPointerTargetType::None)
                    {
                        bagTarget.bagButton = button;
                        return bagTarget;
                    }
                }

                // A party of one's tab buttons.
                for (uint8_t tab = 0; GameplayHudOverlaySupport::inventoryTabsShown(context)
                         && int(tab) < InventoryBags::tabCount(bagCount); ++tab)
                {
                    const std::string tabId = "CharacterInventoryTab" + std::to_string(tab + 1);
                    GameplayCharacterPointerTarget tabTarget = resolveCharacterButtonTarget(
                        tabId.c_str(), GameplayCharacterPointerTargetType::InventoryTabButton);

                    if (tabTarget.type != GameplayCharacterPointerTargetType::None)
                    {
                        tabTarget.bagButton = tab;
                        return tabTarget;
                    }
                }
            }

            const UiLayoutManager::LayoutElement *pExitLayout = context.findHudLayoutElement("CharacterExitButton");

            if (pExitLayout != nullptr)
            {
                const std::optional<GameplayResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(
                        "CharacterExitButton",
                        screenWidth,
                        screenHeight,
                        pExitLayout->width,
                        pExitLayout->height);

                if (resolved.has_value() && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    return {GameplayCharacterPointerTargetType::ExitButton};
                }
            }

            const UiLayoutManager::LayoutElement *pMagnifyLayout = context.findHudLayoutElement("CharacterMagnifyButton");

            if (pMagnifyLayout != nullptr)
            {
                const std::optional<GameplayResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(
                        "CharacterMagnifyButton",
                        screenWidth,
                        screenHeight,
                        pMagnifyLayout->width,
                        pMagnifyLayout->height);

                if (resolved.has_value() && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    return {GameplayCharacterPointerTargetType::MagnifyButton};
                }
            }

            if (!context.heldInventoryItem().active)
            {
                for (auto it = context.renderedInspectableHudItems().rbegin();
                     it != context.renderedInspectableHudItems().rend();
                     ++it)
                {
                    if (it->sourceType != GameplayUiController::ItemInspectSourceType::Equipment
                        || !isVisibleInCharacterDollOverlay(
                            it->equipmentSlot,
                            context.characterScreenReadOnly().dollJewelryOverlayOpen))
                    {
                        continue;
                    }

                    if (!context.isOpaqueHudPixelAtPoint(*it, pointerX, pointerY))
                    {
                        continue;
                    }

                    GameplayCharacterPointerTarget pointerTarget = {};
                    pointerTarget.type = GameplayCharacterPointerTargetType::EquipmentSlot;
                    pointerTarget.page = context.characterScreenReadOnly().page;
                    pointerTarget.equipmentSlot = it->equipmentSlot;
                    return pointerTarget;
                }
            }

            struct CharacterEquipmentSlotTarget
            {
                const char *pLayoutId;
                EquipmentSlot slot;
                bool jewelryOverlayOnly;
            };

            static constexpr CharacterEquipmentSlotTarget EquipmentSlotTargets[] = {
                {"CharacterDollBowSlot", EquipmentSlot::Bow, false},
                {"CharacterDollRightHandSlot", EquipmentSlot::MainHand, false},
                {"CharacterDollLeftHandSlot", EquipmentSlot::OffHand, false},
                {"CharacterDollArmorSlot", EquipmentSlot::Armor, false},
                {"CharacterDollHelmetSlot", EquipmentSlot::Helm, false},
                {"CharacterDollBeltSlot", EquipmentSlot::Belt, false},
                {"CharacterDollCloakSlot", EquipmentSlot::Cloak, false},
                {"CharacterDollBootsSlot", EquipmentSlot::Boots, false},
                {"CharacterDollAmuletSlot", EquipmentSlot::Amulet, true},
                {"CharacterDollGauntletsSlot", EquipmentSlot::Gauntlets, true},
                {"CharacterDollRing1Slot", EquipmentSlot::Ring1, true},
                {"CharacterDollRing2Slot", EquipmentSlot::Ring2, true},
                {"CharacterDollRing3Slot", EquipmentSlot::Ring3, true},
                {"CharacterDollRing4Slot", EquipmentSlot::Ring4, true},
                {"CharacterDollRing5Slot", EquipmentSlot::Ring5, true},
                {"CharacterDollRing6Slot", EquipmentSlot::Ring6, true},
            };

            // The Augment row's implant sockets (jewellery overlay, a character with Cybernetics or an implant).
            if (!isReadOnlyAdventurersInnView && context.characterScreenReadOnly().dollJewelryOverlayOpen
                && pActiveCharacter != nullptr && pActiveCharacter->showsImplantSockets())
            {
                for (uint8_t socket = 0; socket < pActiveCharacter->implants.size(); ++socket)
                {
                    const std::string socketId = "CharacterDollImplant" + std::to_string(socket + 1) + "Slot";
                    const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(socketId);
                    const std::optional<GameplayResolvedHudLayoutElement> resolved = pLayout != nullptr
                        ? context.resolveHudLayoutElement(socketId, screenWidth, screenHeight, pLayout->width,
                            pLayout->height)
                        : std::nullopt;

                    if (resolved && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        GameplayCharacterPointerTarget pointerTarget = {};
                        pointerTarget.type = GameplayCharacterPointerTargetType::ImplantSocket;
                        pointerTarget.page = context.characterScreenReadOnly().page;
                        pointerTarget.implantSocket = socket;
                        return pointerTarget;
                    }
                }
            }

            for (const CharacterEquipmentSlotTarget &target : EquipmentSlotTargets)
            {
                if (!isVisibleInCharacterDollOverlay(target.slot, context.characterScreenReadOnly().dollJewelryOverlayOpen))
                {
                    continue;
                }

                if (context.heldInventoryItem().active && !target.jewelryOverlayOnly)
                {
                    continue;
                }

                const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(target.pLayoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const uint32_t equippedId =
                    pActiveCharacter != nullptr ? equippedItemId(pActiveCharacter->equipment, target.slot) : 0;
                const ItemDefinition *pItemDefinition =
                    equippedId != 0 && context.itemTable() != nullptr ? context.itemTable()->get(equippedId) : nullptr;
                std::optional<GameplayResolvedHudLayoutElement> dynamicRect;
                std::string dynamicTextureName;

                if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
                {
                    const bool hasRightHandWeapon =
                        pActiveCharacter != nullptr && pActiveCharacter->equipment.mainHand != 0;
                    const uint32_t dollTypeId =
                        pActiveCharacterDollType != nullptr ? pActiveCharacterDollType->id : 0;
                    dynamicTextureName = context.resolveEquippedItemHudTextureName(
                        *pItemDefinition,
                        dollTypeId,
                        hasRightHandWeapon,
                        target.slot);
                    const std::optional<GameplayHudTextureHandle> texture =
                        context.gameplayUiRuntime().ensureItemIconTextureLoaded(dynamicTextureName);

                    if (texture.has_value())
                    {
                        dynamicRect = context.resolveCharacterEquipmentRenderRect(
                            *pLayout,
                            *pItemDefinition,
                            *texture,
                            pActiveCharacterDollEntry,
                            pActiveCharacterDollType,
                            target.slot,
                            screenWidth,
                            screenHeight);
                    }
                }

                bool pointerInsideDynamicRect = false;

                if (dynamicRect.has_value())
                {
                    if (context.heldInventoryItem().active)
                    {
                        pointerInsideDynamicRect = context.isPointerInsideResolvedElement(*dynamicRect, pointerX, pointerY);
                    }
                    else if (!dynamicTextureName.empty() && pItemDefinition != nullptr)
                    {
                        GameplayRenderedInspectableHudItem renderedItem = {};
                        renderedItem.objectDescriptionId = pItemDefinition->itemId;
                        renderedItem.textureName = dynamicTextureName;
                        renderedItem.x = dynamicRect->x;
                        renderedItem.y = dynamicRect->y;
                        renderedItem.width = dynamicRect->width;
                        renderedItem.height = dynamicRect->height;
                        pointerInsideDynamicRect = context.isOpaqueHudPixelAtPoint(renderedItem, pointerX, pointerY);
                    }
                }

                const std::optional<GameplayResolvedHudLayoutElement> resolved =
                    context.heldInventoryItem().active && !dynamicRect.has_value()
                        ? context.resolveHudLayoutElement(
                            target.pLayoutId,
                            screenWidth,
                            screenHeight,
                            pLayout->width,
                            pLayout->height)
                        : std::nullopt;
                const bool pointerInsideLayoutRect =
                    resolved.has_value() && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY);

                if (!pointerInsideDynamicRect && !pointerInsideLayoutRect)
                {
                    continue;
                }

                if ((!isReadOnlyAdventurersInnView && context.heldInventoryItem().active)
                    || (pActiveCharacter != nullptr && equippedId != 0))
                {
                    if (isReadOnlyAdventurersInnView)
                    {
                        continue;
                    }

                    GameplayCharacterPointerTarget pointerTarget = {};
                    pointerTarget.type = GameplayCharacterPointerTargetType::EquipmentSlot;
                    pointerTarget.page = context.characterScreenReadOnly().page;
                    pointerTarget.equipmentSlot = target.slot;
                    return pointerTarget;
                }
            }

            if (!isReadOnlyAdventurersInnView && context.heldInventoryItem().active)
            {
                const UiLayoutManager::LayoutElement *pDollLayout = context.findHudLayoutElement("CharacterDollPanel");

                if (pDollLayout != nullptr)
                {
                    const std::optional<GameplayResolvedHudLayoutElement> resolvedDoll =
                        context.resolveHudLayoutElement(
                            "CharacterDollPanel",
                            screenWidth,
                            screenHeight,
                            pDollLayout->width,
                            pDollLayout->height);

                    if (resolvedDoll.has_value() && context.isPointerInsideResolvedElement(*resolvedDoll, pointerX, pointerY))
                    {
                        GameplayCharacterPointerTarget pointerTarget = {};
                        pointerTarget.type = GameplayCharacterPointerTargetType::DollPanel;
                        pointerTarget.page = context.characterScreenReadOnly().page;
                        return pointerTarget;
                    }
                }
            }

            if (context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory
                && GameplayHudOverlaySupport::bagOverviewActive(context) && pActiveCharacter != nullptr)
            {
                const std::optional<GameplayResolvedHudLayoutElement> resolvedInventoryGrid =
                    resolveCharacterInventoryGrid();

                if (resolvedInventoryGrid.has_value()
                    && context.isPointerInsideResolvedElement(*resolvedInventoryGrid, pointerX, pointerY))
                {
                    const int firstBag = InventoryBagOverview::firstBag(*pActiveCharacter);

                    for (int bag = firstBag; bag < firstBag + InventoryBagOverview::Bags; ++bag)
                    {
                        const InventoryBagOverview::Slot slot =
                            InventoryBagOverview::slot(*resolvedInventoryGrid, bag);
                        GameplayCharacterPointerTarget target = {};
                        target.page = GameplayUiController::CharacterPage::Inventory;
                        target.bag = uint8_t(bag);

                        if (!InventoryBagOverview::insideGrid(slot, pointerX, pointerY))
                        {
                            continue;
                        }

                        const auto [gridX, gridY] = InventoryBagOverview::cellAt(slot, pointerX, pointerY);
                        const InventoryItem *pItem =
                            InventoryBags::itemInBagAt(*pActiveCharacter, target.bag, gridX, gridY);

                        if (pItem != nullptr)
                        {
                            target.type = GameplayCharacterPointerTargetType::BagOverviewItem;
                            target.gridX = pItem->gridX;
                            target.gridY = pItem->gridY;
                            return target;
                        }

                        if (context.heldInventoryItem().active)
                        {
                            target.type = GameplayCharacterPointerTargetType::BagOverviewCell;
                            target.gridX = gridX;
                            target.gridY = gridY;
                            return target;
                        }
                    }

                    return {};
                }
            }

            if (context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory)
            {
                const std::optional<GameplayResolvedHudLayoutElement> resolvedInventoryGrid =
                    resolveCharacterInventoryGrid();

                if (resolvedInventoryGrid.has_value()
                    && context.isPointerInsideResolvedElement(*resolvedInventoryGrid, pointerX, pointerY))
                {
                    const float cellWidth =
                        resolvedInventoryGrid->width / static_cast<float>(Character::InventoryWidth);
                    const float cellHeight =
                        resolvedInventoryGrid->height / static_cast<float>(Character::InventoryHeight);
                    const uint8_t gridX = static_cast<uint8_t>(std::clamp(
                        static_cast<int>((pointerX - resolvedInventoryGrid->x) / cellWidth),
                        0,
                        Character::InventoryWidth - 1));
                    const uint8_t gridY = static_cast<uint8_t>(std::clamp(
                        static_cast<int>((pointerY - resolvedInventoryGrid->y) / cellHeight),
                        0,
                        Character::InventoryHeight - 1));

                    if (pActiveCharacter != nullptr)
                    {
                        const InventoryItem *pItem = pActiveCharacter->inventoryItemAt(gridX, gridY);

                        if (pItem != nullptr && !isReadOnlyAdventurersInnView)
                        {
                            GameplayCharacterPointerTarget target = {};
                            target.type = GameplayCharacterPointerTargetType::InventoryItem;
                            target.page = GameplayUiController::CharacterPage::Inventory;
                            target.gridX = pItem->gridX;
                            target.gridY = pItem->gridY;
                            return target;
                        }
                    }

                    if (!isReadOnlyAdventurersInnView && context.heldInventoryItem().active)
                    {
                        GameplayCharacterPointerTarget target = {};
                        target.type = GameplayCharacterPointerTargetType::InventoryCell;
                        target.page = GameplayUiController::CharacterPage::Inventory;
                        target.gridX = gridX;
                        target.gridY = gridY;
                        return target;
                    }
                }
            }

            if (context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Skills)
            {
                const std::optional<GameplayResolvedHudLayoutElement> viewport =
                    context.resolveHudLayoutElement("CharacterSkillsViewport", screenWidth, screenHeight, 0, 0);
                if (!viewport || !context.isPointerInsideResolvedElement(*viewport, pointerX, pointerY))
                {
                    return {};
                }

                // The Magic heading's rotation switch: its label and gem, a little past the gem on the right.
                if (pActiveCharacter != nullptr
                    && gameRulesFor(context.partyReadOnly()).spells.spellRotation(*pActiveCharacter))
                {
                    if (const std::optional<GameplayHudOverlaySupport::SkillRotationSwitchRect> rotationSwitch =
                            GameplayHudOverlaySupport::skillRotationSwitchRect(context, screenWidth, screenHeight))
                    {
                        const float reach = GameplayHudOverlaySupport::SkillSwitchReach * rotationSwitch->scale;

                        if (pointerX >= rotationSwitch->labelLeft - reach && pointerX < rotationSwitch->right + reach
                            && pointerY >= rotationSwitch->y && pointerY < rotationSwitch->y + rotationSwitch->height)
                        {
                            GameplayCharacterPointerTarget target = {};
                            target.type = GameplayCharacterPointerTargetType::SkillRotationSwitch;
                            target.page = GameplayUiController::CharacterPage::Skills;
                            return target;
                        }
                    }
                }

                const auto findSkillRowTarget =
                    [&context, screenWidth, screenHeight, pointerX, pointerY, skillRowHeight](
                        const char *pRegionId,
                        const char *pLevelHeaderId,
                        const std::vector<CharacterSkillUiRow> &rows) -> GameplayCharacterPointerTarget
                    {
                        if (rows.empty())
                        {
                            return {};
                        }

                        const UiLayoutManager::LayoutElement *pRegionLayout = context.findHudLayoutElement(pRegionId);
                        const UiLayoutManager::LayoutElement *pLevelLayout = context.findHudLayoutElement(pLevelHeaderId);

                        if (pRegionLayout == nullptr || pLevelLayout == nullptr)
                        {
                            return {};
                        }

                        const std::optional<GameplayResolvedHudLayoutElement> resolvedRegion =
                            context.resolveHudLayoutElement(
                                pRegionId,
                                screenWidth,
                                screenHeight,
                                pRegionLayout->width,
                                pRegionLayout->height);
                        const std::optional<GameplayResolvedHudLayoutElement> resolvedLevelHeader =
                            context.resolveHudLayoutElement(
                                pLevelHeaderId,
                                screenWidth,
                                screenHeight,
                                pLevelLayout->width,
                                pLevelLayout->height);

                        if (!resolvedRegion.has_value() || !resolvedLevelHeader.has_value())
                        {
                            return {};
                        }

                        const float rowHeightPixels = skillRowHeight * resolvedRegion->scale;
                        const float rowRight = resolvedLevelHeader->x + resolvedLevelHeader->width;
                        const float scale = resolvedRegion->scale;

                        for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
                        {
                            const CharacterSkillUiRow &row = rows[rowIndex];
                            const float rowY = resolvedRegion->y + static_cast<float>(rowIndex) * rowHeightPixels;

                            if (pointerY < rowY || pointerY >= rowY + rowHeightPixels)
                            {
                                continue;
                            }

                            // A switch row: its gem flips the switch, the strip up to the name takes no clicks and
                            // only the rest of the row raises the skill.
                            float rowLeft = resolvedRegion->x;

                            if (row.switchOn)
                            {
                                const float gemRight =
                                    resolvedRegion->x + GameplayHudOverlaySupport::SkillSwitchGemWidth * scale;

                                if (pointerX >= resolvedRegion->x - GameplayHudOverlaySupport::SkillSwitchReach * scale
                                    && pointerX < gemRight)
                                {
                                    GameplayCharacterPointerTarget target = {};
                                    target.type = GameplayCharacterPointerTargetType::SkillSwitch;
                                    target.page = GameplayUiController::CharacterPage::Skills;
                                    target.skillName = row.canonicalName;
                                    return target;
                                }

                                rowLeft = resolvedRegion->x + GameplayHudOverlaySupport::SkillSwitchIndent * scale;
                            }

                            if (pointerX >= rowLeft && pointerX < rowRight)
                            {
                                GameplayCharacterPointerTarget target = {};
                                target.type = GameplayCharacterPointerTargetType::SkillRow;
                                target.page = GameplayUiController::CharacterPage::Skills;
                                target.skillName = row.canonicalName;
                                target.skillRaisable = row.interactive;
                                return target;
                            }
                        }

                        return {};
                    };

                const GameplayCharacterPointerTarget weaponTarget = findSkillRowTarget(
                    "CharacterSkillsWeaponsListRegion",
                    "CharacterSkillsWeaponsLevelHeader",
                    skillUiData.weaponRows);

                if (weaponTarget.type != GameplayCharacterPointerTargetType::None)
                {
                    return weaponTarget;
                }

                const GameplayCharacterPointerTarget magicTarget = findSkillRowTarget(
                    "CharacterSkillsMagicListRegion",
                    "CharacterSkillsMagicLevelHeader",
                    skillUiData.magicRows);

                if (magicTarget.type != GameplayCharacterPointerTargetType::None)
                {
                    return magicTarget;
                }

                const GameplayCharacterPointerTarget armorTarget = findSkillRowTarget(
                    "CharacterSkillsArmorListRegion",
                    "CharacterSkillsArmorLevelHeader",
                    skillUiData.armorRows);

                if (armorTarget.type != GameplayCharacterPointerTargetType::None)
                {
                    return armorTarget;
                }

                const GameplayCharacterPointerTarget miscTarget = findSkillRowTarget(
                    "CharacterSkillsMiscListRegion",
                    "CharacterSkillsMiscLevelHeader",
                    skillUiData.miscRows);

                if (miscTarget.type != GameplayCharacterPointerTargetType::None)
                {
                    return miscTarget;
                }

                const GameplayCharacterPointerTarget techTarget = findSkillRowTarget(
                    "CharacterSkillsTechListRegion",
                    "CharacterSkillsTechLevelHeader",
                    skillUiData.techRows);

                if (techTarget.type != GameplayCharacterPointerTargetType::None)
                {
                    return techTarget;
                }
            }

            return {};
        };

    const HudPointerState pointerState = {mouseX, mouseY, isLeftMousePressed};
    const GameplayCharacterPointerTarget noneCharacterTarget = {};
    const GameplayCharacterPointerTarget hoveredCharacterTarget = findCharacterPointerTarget(mouseX, mouseY);

    // The skills page names a hovered skill's raise cost when the rules show it; a bag tag's button names the bag it
    // acts on.
    const Character *pShownCharacter = pParty != nullptr ? pParty->member(selectedPartyMemberIndex) : nullptr;
    context.setStatusBarHoverText(
        hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::SkillRow && pActiveCharacter != nullptr
            ? skillRaiseCostHoverText(
                  *pActiveCharacter, hoveredCharacterTarget.skillName, gameRulesFor(context.partyReadOnly()).skills)
        : hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::SkillSwitch && pActiveCharacter != nullptr
            ? skillSwitchHoverText(context,
                  Engine::localize(displaySkillName(hoveredCharacterTarget.skillName), "skill"),
                  gameRulesFor(context.partyReadOnly())
                      .skills.skillSwitch(*pActiveCharacter, hoveredCharacterTarget.skillName)
                      .value_or(false),
                  hoveredCharacterTarget.skillName == "Cover" ? KeyboardAction::SkillCover
                                                              : KeyboardAction::SkillManaShield)
        : hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::SkillRotationSwitch
                && pActiveCharacter != nullptr
            ? skillSwitchHoverText(context, Engine::tr("Elementalist rotation"),
                  gameRulesFor(context.partyReadOnly()).spells.spellRotation(*pActiveCharacter).value_or(false),
                  KeyboardAction::SkillRotation)
        : hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::InventoryTabButton
            ? Engine::tr("Tab {tab} (Shift+{key})",
                {{"tab", InventoryBagOverview::tabNumeral(hoveredCharacterTarget.bagButton)},
                  {"key", int64_t(hoveredCharacterTarget.bagButton + 1)}})
        : hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::InventoryBagTagButton
                && pShownCharacter != nullptr
            ? bagTagHoverText(*pShownCharacter, BagTag(hoveredCharacterTarget.bagButton),
                  gameRulesFor(pParty).items.bagCount(*pParty))
            : std::string());

    if (pParty != nullptr)
    {
        context.itemService().updateReadableScrollOverlayForHeldItem(
            context,
            selectedPartyMemberIndex,
            hoveredCharacterTarget,
            isLeftMousePressed,
            input.rightMouseButton.held);

        if (rightMousePressed
            && context.heldInventoryItem().active
            && !isInventorySpellTargetMode
            && (hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::InventoryItem
                || hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::InventoryCell
                || hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::BagOverviewItem))
        {
            // An item of the bag overview is mixed with its bag open, as on that bag's full-size grid.
            const bool overviewItem =
                hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::BagOverviewItem;
            const Character *pHoveredCharacter = pParty->member(selectedPartyMemberIndex);
            const uint8_t targetBag = overviewItem || pHoveredCharacter == nullptr
                ? hoveredCharacterTarget.bag
                : pHoveredCharacter->rulesetState.currentBag;
            const InventoryItem *pTargetItem =
                pHoveredCharacter != nullptr
                    ? InventoryBags::itemInBagAt(
                        *pHoveredCharacter, targetBag, hoveredCharacterTarget.gridX, hoveredCharacterTarget.gridY)
                    : nullptr;

            if (pTargetItem != nullptr)
            {
                const uint8_t targetGridX = pTargetItem->gridX;
                const uint8_t targetGridY = pTargetItem->gridY;

                const auto mixItem =
                    [&]() -> bool
                    {
                        return context.itemService().tryUseHeldItemOnInventoryItem(
                            context, selectedPartyMemberIndex, targetGridX, targetGridY);
                    };

                if (overviewItem
                        ? InventoryBags::withBagOpen(*pParty, selectedPartyMemberIndex, targetBag,
                              gameRulesFor(pParty).items.bagCount(*pParty), mixItem)
                        : mixItem())
                {
                    return;
                }
            }
        }

        // A crafting material held over a worn item opens the Workbench with both in place, as over a pack item.
        if (rightMousePressed
            && context.heldInventoryItem().active
            && !isInventorySpellTargetMode
            && hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::EquipmentSlot)
        {
            CraftItemRef wornTarget;
            wornTarget.memberIndex = selectedPartyMemberIndex;
            wornTarget.worn = true;
            wornTarget.slot = hoveredCharacterTarget.equipmentSlot;

            if (context.itemService().openWorkbenchForHeldMaterial(context, wornTarget))
            {
                return;
            }
        }
    }
    else
    {
        context.itemService().closeReadableScrollOverlay();
    }

    const auto activateCharacterTarget =
        [&context,
         pActiveCharacterDollEntry,
         pActiveCharacterDollType,
         pActiveCharacter,
         pParty,
         screenWidth,
         screenHeight,
         &clearPendingCharacterDismiss,
         &resolveCharacterInventoryGrid,
         isReadOnlyAdventurersInnView,
         selectedPartyMemberIndex,
         selectedPartyMemberCanAct,
         pKeyboardState](
            const GameplayCharacterPointerTarget &target,
            float activationX,
            float activationY)
        {
            const bool isInventorySpellTargetMode =
                context.utilitySpellOverlayReadOnly().active
                && context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;
            const auto setHeldItem =
                [&context, pParty](const InventoryItem &item)
                {
                    GAMEPLAY_DEBUG_TRACE(
                        "held_item_changed active=true item_id=" + std::to_string(item.objectDescriptionId)
                        + " quantity=" + std::to_string(item.quantity)
                        + " grid=(" + std::to_string(item.gridX) + "," + std::to_string(item.gridY) + ")"
                        + " source=party_overlay");
                    context.heldInventoryItem() = {};
                    context.heldInventoryItem().active = true;
                    context.heldInventoryItem().item = item;
                    context.heldInventoryItem().grabCellOffsetX = 0;
                    context.heldInventoryItem().grabCellOffsetY = 0;
                    context.heldInventoryItem().grabOffsetX = 0.0f;
                    context.heldInventoryItem().grabOffsetY = 0.0f;

                    if (pParty != nullptr)
                    {
                        pParty->setHeldItemForQueries(item);
                    }
                };
            const auto clearHeldItem =
                [&context, pParty]()
                {
                    if (context.heldInventoryItem().active)
                    {
                        GAMEPLAY_DEBUG_TRACE(
                            "held_item_changed active=false item_id="
                            + std::to_string(context.heldInventoryItem().item.objectDescriptionId)
                            + " source=party_overlay");
                    }

                    context.heldInventoryItem() = {};

                    if (pParty != nullptr)
                    {
                        pParty->clearHeldItemForQueries();
                    }
                };
            const auto resolveSpellName =
                [&context](uint32_t spellId) -> std::string
                {
                    const SpellEntry *pSpellEntry =
                        context.spellTable() != nullptr ? context.spellTable()->findById(static_cast<int>(spellId)) : nullptr;
                    return pSpellEntry != nullptr && !pSpellEntry->name.empty() ? pSpellEntry->name : "Spell";
                };

            if (target.type != GameplayCharacterPointerTargetType::DismissButton)
            {
                clearPendingCharacterDismiss();
            }

            if (isInventorySpellTargetMode)
            {
                if (target.type == GameplayCharacterPointerTargetType::InventoryItem)
                {
                    PartySpellCastRequest request = context.utilitySpellOverlayReadOnly().castRequest();
                    request.targetItemMemberIndex =
                        pParty != nullptr ? std::optional<size_t>(selectedPartyMemberIndex) : std::nullopt;
                    request.targetInventoryGridX = target.gridX;
                    request.targetInventoryGridY = target.gridY;
                    context.tryCastSpellRequest(request, resolveSpellName(request.spellId));
                    return;
                }

                if (target.type == GameplayCharacterPointerTargetType::EquipmentSlot)
                {
                    PartySpellCastRequest request = context.utilitySpellOverlayReadOnly().castRequest();
                    request.targetItemMemberIndex =
                        pParty != nullptr ? std::optional<size_t>(selectedPartyMemberIndex) : std::nullopt;
                    request.targetEquipmentSlot = target.equipmentSlot;
                    context.tryCastSpellRequest(request, resolveSpellName(request.spellId));
                    return;
                }
            }

            if (target.type == GameplayCharacterPointerTargetType::PageButton)
            {
                if (isInventorySpellTargetMode && target.page != GameplayUiController::CharacterPage::Inventory)
                {
                    context.setStatusBarEvent(Engine::tr("Select an item"));
                    return;
                }

                if (context.characterScreenReadOnly().page != target.page)
                {
                    context.characterScreen().awardScrollOffset = 0;
                    context.characterScreen().skillScrollOffset = 0;
                    context.characterScreen().scrollDragOffset.reset();
                }

                context.characterScreen().page = target.page;
                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::ExitButton)
            {
                if (isInventorySpellTargetMode)
                {
                    context.utilitySpellOverlay() = {};
                }

                if (isReadOnlyAdventurersInnView)
                {
                    context.characterScreen().dollJewelryOverlayOpen = false;
                    context.characterScreen().adventurersInnRosterOverlayOpen = true;
                }
                else
                {
                    context.closeCharacterScreen();
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::AdventurersInnPortrait)
            {
                const uint64_t nowTicks = SDL_GetTicks();
                const bool isDoubleClick =
                    context.interactionState().lastAdventurersInnPortraitClickedIndex.has_value()
                    && *context.interactionState().lastAdventurersInnPortraitClickedIndex == target.innIndex
                    && nowTicks >= context.interactionState().lastAdventurersInnPortraitClickTicks
                    && nowTicks - context.interactionState().lastAdventurersInnPortraitClickTicks
                        <= PartyPortraitDoubleClickWindowMs;
                context.characterScreen().sourceIndex = target.innIndex;
                context.interactionState().lastAdventurersInnPortraitClickTicks = nowTicks;
                context.interactionState().lastAdventurersInnPortraitClickedIndex = target.innIndex;

                if (isDoubleClick)
                {
                    context.characterScreen().adventurersInnRosterOverlayOpen = false;
                    context.characterScreen().dollJewelryOverlayOpen = false;
                    context.characterScreen().page = GameplayUiController::CharacterPage::Inventory;
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::AdventurersInnScrollUpButton)
            {
                if (context.characterScreenReadOnly().adventurersInnScrollOffset > 0)
                {
                    --context.characterScreen().adventurersInnScrollOffset;
                }

                return;
            }

            constexpr size_t AdventurersInnVisibleCount = 8;

            if (target.type == GameplayCharacterPointerTargetType::AdventurersInnScrollDownButton && pParty != nullptr)
            {
                const size_t innCount = pParty->adventurersInnMembers().size();

                if (context.characterScreenReadOnly().adventurersInnScrollOffset + AdventurersInnVisibleCount < innCount)
                {
                    ++context.characterScreen().adventurersInnScrollOffset;
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::AdventurersInnHireButton && pParty != nullptr)
            {
                const size_t innIndex = context.characterScreenReadOnly().sourceIndex;
                const AdventurersInnMember *pInnMember = pParty->adventurersInnMember(innIndex);
                const std::string memberName =
                    pInnMember != nullptr ? pInnMember->character.name : Engine::tr("Adventurer");

                if (pParty->hireAdventurersInnMember(innIndex))
                {
                    if (context.audioSystem() != nullptr)
                    {
                        context.audioSystem()->playCommonSound(SoundId::Heroism, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    if (pParty->adventurersInnMembers().empty())
                    {
                        context.characterScreen().open = false;
                        context.characterScreen().adventurersInnRosterOverlayOpen = false;
                    }
                    else
                    {
                        context.characterScreen().sourceIndex =
                            std::min(innIndex, pParty->adventurersInnMembers().size() - 1);
                        const size_t maximumScrollOffset =
                            pParty->adventurersInnMembers().size() > AdventurersInnVisibleCount
                                ? pParty->adventurersInnMembers().size() - AdventurersInnVisibleCount
                                : 0;
                        context.characterScreen().adventurersInnScrollOffset =
                            std::min(context.characterScreenReadOnly().adventurersInnScrollOffset, maximumScrollOffset);
                        context.characterScreen().adventurersInnRosterOverlayOpen = true;
                    }

                    context.setStatusBarEvent(Engine::tr("{name} joined the party.", {{"name", memberName}}));
                }
                else
                {
                    context.setStatusBarEvent(
                        pParty->lastStatus().empty() ? Engine::tr("Can't hire adventurer.") : pParty->lastStatus());
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::DismissButton && pParty != nullptr)
            {
                const size_t memberIndex = selectedPartyMemberIndex;
                const Character *pMember = pParty->member(memberIndex);

                if (pMember == nullptr || memberIndex == 0)
                {
                    clearPendingCharacterDismiss();
                    return;
                }

                const bool confirmed =
                    context.interactionState().pendingCharacterDismissMemberIndex.has_value()
                    && *context.interactionState().pendingCharacterDismissMemberIndex == memberIndex
                    && SDL_GetTicks() <= context.interactionState().pendingCharacterDismissExpiresTicks;

                if (!confirmed)
                {
                    const uint64_t dismissClickTicks = SDL_GetTicks();
                    context.interactionState().pendingCharacterDismissMemberIndex = memberIndex;
                    context.interactionState().pendingCharacterDismissExpiresTicks = dismissClickTicks + CharacterDismissConfirmWindowMs;
                    context.setStatusBarEvent(
                        Engine::tr("To confirm {name} dismissal press the button again...", {{"name", pMember->name}}),
                        2.0f);
                }
                else
                {
                    const std::string dismissedName = pMember->name;
                    clearPendingCharacterDismiss();

                    if (pParty->dismissMemberToAdventurersInn(memberIndex))
                    {
                        context.characterScreen().dollJewelryOverlayOpen = false;
                        context.setStatusBarEvent(Engine::tr("{name} dismissed.", {{"name", dismissedName}}));
                    }
                    else
                    {
                        context.setStatusBarEvent(Engine::tr("Dismissal failed."));
                    }
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::AlchemyButton)
            {
                openWorkbench(context);
                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::InventoryDropButton)
            {
                GameplayInteractionController::dropHeldItemInFrontOfParty(context);
                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::InventorySortButton && pParty != nullptr)
            {
                // With several bags (MAW) every sort is MAW's: the open bag, Shift its tab's bags as one, Ctrl the
                // whole party's (MAW's T and G); a picked alchemist takes the alchemy items of any of these sorts
                // (audit TXT-2-B2).
                const ItemRules &itemRules = gameRulesFor(pParty).items;
                const int bagCount = itemRules.bagCount(*pParty);
                // The overview shows every bag, so its Sort sorts every bag, as Shift does on one bag.
                const bool shiftHeld = pKeyboardState[SDL_SCANCODE_LSHIFT] || pKeyboardState[SDL_SCANCODE_RSHIFT]
                    || GameplayHudOverlaySupport::bagOverviewActive(context);
                const bool ctrlHeld = pKeyboardState[SDL_SCANCODE_LCTRL] || pKeyboardState[SDL_SCANCODE_RCTRL];
                const std::optional<size_t> alchemist = itemRules.alchemist(*pParty);
                const Character *pMember = pParty->member(selectedPartyMemberIndex);

                if (bagCount > 1 && pMember != nullptr)
                {
                    std::vector<size_t> members = {selectedPartyMemberIndex};

                    if (ctrlHeld)
                    {
                        members.clear();

                        for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
                        {
                            members.push_back(memberIndex);
                        }
                    }

                    const ItemTable *pItemTable = pParty->itemTable();
                    const bool sorted = InventoryBags::sortPartyBags(*pParty, members, shiftHeld, bagCount, alchemist,
                        [&itemRules](const InventoryItem &item)
                        {
                            return itemRules.alchemySortRank(item);
                        },
                        [&itemRules, pItemTable](const InventoryItem &item) -> std::optional<BagTag>
                        {
                            const ItemDefinition *pDefinition =
                                pItemTable != nullptr ? pItemTable->get(item.objectDescriptionId) : nullptr;
                            return pDefinition != nullptr ? itemRules.bagTag(*pDefinition) : std::nullopt;
                        });
                    context.setStatusBarEvent(!sorted ? Engine::tr("Not enough room to sort.")
                            : ctrlHeld && shiftHeld ? Engine::tr("All bags of the party sorted")
                            : ctrlHeld              ? Engine::tr("All inventories have been sorted")
                            : shiftHeld             ? Engine::tr("All of {name}'s bags sorted",
                                {{"name", pMember->name}})
                                                    : Engine::tr("Inventory sorted"));
                    return;
                }

                if (!pParty->sortMemberInventory(selectedPartyMemberIndex))
                {
                    context.setStatusBarEvent(Engine::tr("Not enough room to sort."));
                }

                return;
            }

            // A bag button zooms that bag of the open bag's tab.
            if (target.type == GameplayCharacterPointerTargetType::InventoryBagButton && pParty != nullptr
                && pParty->member(selectedPartyMemberIndex) != nullptr)
            {
                zoomInventoryBag(context, *pParty, selectedPartyMemberIndex,
                    InventoryBagOverview::firstBag(*pParty->member(selectedPartyMemberIndex)) + target.bagButton);
                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::InventoryTabButton)
            {
                openBagTab(context, target.bagButton);
                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::MagnifyButton)
            {
                context.characterScreen().dollJewelryOverlayOpen = !context.characterScreenReadOnly().dollJewelryOverlayOpen;
                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::InventoryBagTagButton)
            {
                toggleBagTag(context, BagTag(target.bagButton));
                return;
            }

            // The bag overview's button: the four bags again.
            if (target.type == GameplayCharacterPointerTargetType::InventoryBagOverviewButton)
            {
                context.characterScreen().inventoryBagZoomed = false;
                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::SkillSwitch)
            {
                if (!isReadOnlyAdventurersInnView)
                {
                    toggleSkillSwitch(context, target.skillName);
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::SkillRotationSwitch)
            {
                if (!isReadOnlyAdventurersInnView)
                {
                    toggleSkillRotation(context);
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::SkillRow && pParty != nullptr)
            {
                if (!target.skillRaisable)
                {
                    return;
                }

                if (pParty->activeMemberIndex() != selectedPartyMemberIndex
                    && !context.trySelectPartyMember(selectedPartyMemberIndex, true))
                {
                    return;
                }

                if (pParty->increaseActiveMemberSkillLevel(target.skillName))
                {
                    if (context.audioSystem() != nullptr)
                    {
                        context.audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    context.playSpeechReaction(pParty->activeMemberIndex(), SpeechId::SkillIncreased, true);

                    // A mastery the rules granted on the raise.
                    if (!pParty->lastStatus().empty())
                    {
                        context.setStatusBarEvent(pParty->lastStatus());
                    }
                }

                return;
            }

            if (pParty == nullptr || context.itemTable() == nullptr)
            {
                return;
            }

            Character *pCharacter = pParty->member(selectedPartyMemberIndex);

            if (pCharacter == nullptr)
            {
                return;
            }

            const size_t memberIndex = selectedPartyMemberIndex;

            // The bag overview: items go into and come out of any bag; the open bag stays open.
            if (target.type == GameplayCharacterPointerTargetType::BagOverviewItem
                || target.type == GameplayCharacterPointerTargetType::BagOverviewCell)
            {
                activateBagOverviewTarget(
                    context, *pParty, memberIndex, target, resolveCharacterInventoryGrid(), activationX, activationY,
                    setHeldItem, clearHeldItem);
                return;
            }

            // An implant socket: take its implant into the hand, or fit the held implant (the one it replaces into
            // the hand).
            if (target.type == GameplayCharacterPointerTargetType::ImplantSocket)
            {
                if (!selectedPartyMemberCanAct)
                {
                    context.setStatusBarEvent(Engine::tr("Can't do that"));
                    return;
                }

                if (!context.heldInventoryItem().active)
                {
                    InventoryItem implant = {};

                    if (pParty->takeImplant(memberIndex, target.implantSocket, implant))
                    {
                        setHeldItem(implant);
                    }

                    return;
                }

                std::optional<InventoryItem> replaced;

                if (!pParty->fitImplant(memberIndex, target.implantSocket, context.heldInventoryItem().item, replaced))
                {
                    const ItemDefinition *pHeld =
                        context.itemTable()->get(context.heldInventoryItem().item.objectDescriptionId);
                    context.setStatusBarEvent(pHeld == nullptr || pHeld->equipStat != "Implant"
                            ? Engine::tr("Only an implant fits there")
                            : Engine::tr("Cybernetics has not opened that socket"));
                    return;
                }

                if (replaced)
                {
                    setHeldItem(*replaced);
                }
                else
                {
                    clearHeldItem();
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::EquipmentSlot)
            {
                if (!selectedPartyMemberCanAct)
                {
                    context.setStatusBarEvent(Engine::tr("Can't do that"));
                    return;
                }

                if (!context.heldInventoryItem().active)
                {
                    InventoryItem unequippedItem = {};

                    if (pParty->takeEquippedItemFromMember(memberIndex, target.equipmentSlot, unequippedItem))
                    {
                        setHeldItem(unequippedItem);
                    }

                    return;
                }

                const InventoryItemUseAction useAction =
                    InventoryItemUseRuntime::classifyItemUse(
                        context.heldInventoryItem().item,
                        *context.itemTable(),
                        context.mergedPotionSettingTable(),
                        context.mergedReagentSettingTable());

                if (useAction != InventoryItemUseAction::None && useAction != InventoryItemUseAction::Equip)
                {
                    context.itemService().tryUseHeldItemOnPartyMember(context, memberIndex, true);
                    return;
                }

                const ItemDefinition *pItemDefinition =
                    context.itemTable()->get(context.heldInventoryItem().item.objectDescriptionId);

                if (pItemDefinition == nullptr)
                {
                    return;
                }

                const std::optional<CharacterEquipPlan> plan =
                    GameMechanics::resolveCharacterEquipPlan(
                        *pCharacter,
                        *pItemDefinition,
                        context.itemTable(),
                        pActiveCharacterDollType,
                        target.equipmentSlot,
                        false);

                if (!plan.has_value())
                {
                    context.setStatusBarEvent(
                        GameMechanics::equipRefusalReason(*pCharacter, *pItemDefinition, pActiveCharacterDollType)
                            .value_or(Engine::tr("Can't equip that item there")));
                    context.playSpeechReaction(memberIndex, SpeechId::CantEquip, true);
                    return;
                }

                std::optional<InventoryItem> heldReplacement;

                if (!pParty->tryEquipItemOnMember(
                        memberIndex,
                        plan->targetSlot,
                        context.heldInventoryItem().item,
                        plan->displacedSlot,
                        plan->autoStoreDisplacedItem,
                        heldReplacement))
                {
                    const std::string &partyStatus = pParty->lastStatus();
                    context.setStatusBarEvent(
                        partyStatus.empty() || partyStatus == "inventory full" ? Engine::tr("Pack is Full!")
                                                                               : partyStatus);
                    context.playSpeechReaction(
                        memberIndex,
                        partyStatus == "inventory full" ? SpeechId::InventoryRoom : SpeechId::CantEquip,
                        true);
                    return;
                }

                if (heldReplacement.has_value())
                {
                    setHeldItem(*heldReplacement);
                }
                else
                {
                    clearHeldItem();
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::DollPanel && context.heldInventoryItem().active)
            {
                if (!selectedPartyMemberCanAct)
                {
                    context.setStatusBarEvent(Engine::tr("Can't do that"));
                    return;
                }

                const InventoryItemUseAction useAction =
                    InventoryItemUseRuntime::classifyItemUse(
                        context.heldInventoryItem().item,
                        *context.itemTable(),
                        context.mergedPotionSettingTable(),
                        context.mergedReagentSettingTable());

                if (useAction != InventoryItemUseAction::None && useAction != InventoryItemUseAction::Equip)
                {
                    context.itemService().tryUseHeldItemOnPartyMember(context, memberIndex, true);
                    return;
                }

                const ItemDefinition *pItemDefinition =
                    context.itemTable()->get(context.heldInventoryItem().item.objectDescriptionId);

                if (pItemDefinition == nullptr)
                {
                    return;
                }

                const UiLayoutManager::LayoutElement *pDollLayout = context.findHudLayoutElement("CharacterDollPanel");
                const std::optional<GameplayResolvedHudLayoutElement> resolvedDoll =
                    pDollLayout != nullptr
                        ? context.resolveHudLayoutElement(
                            "CharacterDollPanel",
                            screenWidth,
                            screenHeight,
                            pDollLayout->width,
                            pDollLayout->height)
                        : std::nullopt;
                const bool preferOffHand =
                    resolvedDoll.has_value()
                    && activationX >= resolvedDoll->x + resolvedDoll->width * 0.5f;
                const std::optional<CharacterEquipPlan> plan =
                    GameMechanics::resolveCharacterEquipPlan(
                        *pCharacter,
                        *pItemDefinition,
                        context.itemTable(),
                        pActiveCharacterDollType,
                        std::nullopt,
                        preferOffHand);

                if (!plan.has_value())
                {
                    context.setStatusBarEvent(GameMechanics::equipRefusalReason(
                        *pCharacter, *pItemDefinition, pActiveCharacterDollType)
                            .value_or(Engine::tr("Can't equip that item")));
                    context.playSpeechReaction(memberIndex, SpeechId::CantEquip, true);
                    return;
                }

                std::optional<InventoryItem> heldReplacement;

                if (!pParty->tryEquipItemOnMember(
                        memberIndex,
                        plan->targetSlot,
                        context.heldInventoryItem().item,
                        plan->displacedSlot,
                        plan->autoStoreDisplacedItem,
                        heldReplacement))
                {
                    const std::string &partyStatus = pParty->lastStatus();
                    context.setStatusBarEvent(
                        partyStatus.empty() || partyStatus == "inventory full" ? Engine::tr("Pack is Full!")
                                                                               : partyStatus);
                    context.playSpeechReaction(
                        memberIndex,
                        partyStatus == "inventory full" ? SpeechId::InventoryRoom : SpeechId::CantEquip,
                        true);
                    return;
                }

                if (heldReplacement.has_value())
                {
                    setHeldItem(*heldReplacement);
                }
                else
                {
                    clearHeldItem();
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::InventoryItem && context.heldInventoryItem().active)
            {
                std::optional<InventoryItem> replacedItem;

                if (!pParty->tryPlaceItemInMemberInventoryCell(
                        memberIndex,
                        context.heldInventoryItem().item,
                        target.gridX,
                        target.gridY,
                        replacedItem))
                {
                    const std::string &partyStatus = pParty->lastStatus();
                    context.setStatusBarEvent(
                        partyStatus.empty() || partyStatus == "inventory full" ? Engine::tr("Pack is Full!")
                                                                               : partyStatus);
                    return;
                }

                if (replacedItem.has_value())
                {
                    setHeldItem(*replacedItem);
                }
                else
                {
                    clearHeldItem();
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::InventoryCell && context.heldInventoryItem().active)
            {
                const std::optional<GameplayResolvedHudLayoutElement> resolvedInventoryGrid =
                    resolveCharacterInventoryGrid();
                const ItemDefinition *pItemDefinition =
                    context.itemTable()->get(context.heldInventoryItem().item.objectDescriptionId);

                if (!resolvedInventoryGrid.has_value() || pItemDefinition == nullptr || pItemDefinition->iconName.empty())
                {
                    return;
                }

                const std::optional<GameplayHudTextureHandle> itemTexture =
                    context.gameplayUiRuntime().ensureItemIconTextureLoaded(pItemDefinition->iconName);

                if (!itemTexture.has_value())
                {
                    return;
                }

                const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                    resolvedInventoryGrid->x,
                    resolvedInventoryGrid->y,
                    resolvedInventoryGrid->width,
                    resolvedInventoryGrid->height,
                    resolvedInventoryGrid->scale);
                const float itemWidth =
                    static_cast<float>(itemTexture->width) * gridMetrics.scale * pItemDefinition->inventoryDrawScale;
                const float itemHeight =
                    static_cast<float>(itemTexture->height) * gridMetrics.scale * pItemDefinition->inventoryDrawScale;
                const float drawX = activationX - context.heldInventoryItem().grabOffsetX;
                const float drawY = activationY - context.heldInventoryItem().grabOffsetY;
                const std::optional<std::pair<int, int>> placement =
                    computeHeldInventoryPlacement(
                        gridMetrics,
                        context.heldInventoryItem().item.width,
                        context.heldInventoryItem().item.height,
                        itemWidth,
                        itemHeight,
                        drawX,
                        drawY);

                if (!placement.has_value())
                {
                    return;
                }

                std::optional<InventoryItem> replacedItem;

                if (!pParty->tryPlaceItemInMemberInventoryCell(
                        memberIndex,
                        context.heldInventoryItem().item,
                        static_cast<uint8_t>(placement->first),
                        static_cast<uint8_t>(placement->second),
                        replacedItem))
                {
                    const std::string &partyStatus = pParty->lastStatus();
                    context.setStatusBarEvent(
                        partyStatus.empty() || partyStatus == "inventory full" ? Engine::tr("Pack is Full!")
                                                                               : partyStatus);
                    return;
                }

                if (replacedItem.has_value())
                {
                    setHeldItem(*replacedItem);
                }
                else
                {
                    clearHeldItem();
                }

                return;
            }

            if (target.type != GameplayCharacterPointerTargetType::InventoryItem)
            {
                return;
            }

            const InventoryItem *pItem = pCharacter->inventoryItemAt(target.gridX, target.gridY);

            if (pItem == nullptr)
            {
                return;
            }

            InventoryItem heldItem = {};

            if (!pParty->takeItemFromMemberInventoryCell(memberIndex, pItem->gridX, pItem->gridY, heldItem))
            {
                return;
            }

            setHeldItem(heldItem);

            const ItemDefinition *pItemDefinition = context.itemTable()->get(heldItem.objectDescriptionId);
            const std::optional<GameplayResolvedHudLayoutElement> resolvedInventoryGrid =
                resolveCharacterInventoryGrid();

            if (pItemDefinition == nullptr || pItemDefinition->iconName.empty() || !resolvedInventoryGrid.has_value())
            {
                return;
            }

            const std::optional<GameplayHudTextureHandle> itemTexture =
                context.gameplayUiRuntime().ensureItemIconTextureLoaded(pItemDefinition->iconName);

            if (!itemTexture.has_value())
            {
                return;
            }

            const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                resolvedInventoryGrid->x,
                resolvedInventoryGrid->y,
                resolvedInventoryGrid->width,
                resolvedInventoryGrid->height,
                resolvedInventoryGrid->scale);
            const uint8_t hoveredGridX = static_cast<uint8_t>(std::clamp(
                static_cast<int>((activationX - resolvedInventoryGrid->x) / gridMetrics.cellWidth),
                0,
                Character::InventoryWidth - 1));
            const uint8_t hoveredGridY = static_cast<uint8_t>(std::clamp(
                static_cast<int>((activationY - resolvedInventoryGrid->y) / gridMetrics.cellHeight),
                0,
                Character::InventoryHeight - 1));
            context.heldInventoryItem().grabCellOffsetX = hoveredGridX - heldItem.gridX;
            context.heldInventoryItem().grabCellOffsetY = hoveredGridY - heldItem.gridY;
            const float itemWidth =
                static_cast<float>(itemTexture->width) * gridMetrics.scale * pItemDefinition->inventoryDrawScale;
            const float itemHeight =
                static_cast<float>(itemTexture->height) * gridMetrics.scale * pItemDefinition->inventoryDrawScale;
            const InventoryItemScreenRect itemRect =
                computeInventoryItemScreenRect(gridMetrics, heldItem, itemWidth, itemHeight);
            context.heldInventoryItem().grabOffsetX = activationX - itemRect.x;
            context.heldInventoryItem().grabOffsetY = activationY - itemRect.y;
        };

    // The Use key over a pack item does what dropping it on the paperdoll does: drinks, learns, casts or equips it; a
    // message scroll shows while the key is held. Whatever is left in hand (a refused item, a potion with drinks left,
    // the equipment it replaced) goes back where the item lay, else anywhere in the pack. An item of the bag overview
    // (MAW's multibag) is used with its bag open, as on that bag's full-size grid.
    const Character *pHoveredOwner = pParty != nullptr ? pParty->member(selectedPartyMemberIndex) : nullptr;
    const bool hoveredOverviewItem = hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::BagOverviewItem;
    const bool canUseHoveredItem = pHoveredOwner != nullptr
        && (hoveredCharacterTarget.type == GameplayCharacterPointerTargetType::InventoryItem || hoveredOverviewItem)
        && !context.heldInventoryItem().active
        && !isReadOnlyAdventurersInnView
        && !isInventorySpellTargetMode;
    const InventoryItem *pHoveredPackItem = nullptr;

    if (canUseHoveredItem)
    {
        pHoveredPackItem = hoveredOverviewItem
            ? InventoryBags::itemInBagAt(
                *pHoveredOwner, hoveredCharacterTarget.bag, hoveredCharacterTarget.gridX, hoveredCharacterTarget.gridY)
            : pHoveredOwner->inventoryItemAt(hoveredCharacterTarget.gridX, hoveredCharacterTarget.gridY);
    }

    if (useKeyHeld && pHoveredPackItem != nullptr)
    {
        context.itemService().showReadableScroll(context, selectedPartyMemberIndex, *pHoveredPackItem);
    }

    if (useKeyPressed)
    {
        const bool messageScroll = pHoveredPackItem != nullptr && context.itemTable() != nullptr
            && InventoryItemUseRuntime::classifyItemUse(*pHoveredPackItem, *context.itemTable(),
                   context.mergedPotionSettingTable(), context.mergedReagentSettingTable())
                == InventoryItemUseAction::ReadMessageScroll;

        if (pHoveredPackItem != nullptr && !messageScroll)
        {
            if (!selectedPartyMemberCanAct)
            {
                context.setStatusBarEvent(Engine::tr("Can't do that"));
                return;
            }

            const uint8_t originX = pHoveredPackItem->gridX;
            const uint8_t originY = pHoveredPackItem->gridY;
            // The item as the open bag's grid shows it: an overview item's bag is open while it is used.
            GameplayCharacterPointerTarget itemTarget = hoveredCharacterTarget;
            itemTarget.type = GameplayCharacterPointerTargetType::InventoryItem;
            itemTarget.gridX = originX;
            itemTarget.gridY = originY;
            const auto useItem =
                [&]() -> bool
                {
                    activateCharacterTarget(itemTarget, mouseX, mouseY);

                    if (context.heldInventoryItem().active)
                    {
                        GameplayCharacterPointerTarget dollTarget = {};
                        dollTarget.type = GameplayCharacterPointerTargetType::DollPanel;
                        // Left of the paperdoll's middle: a weapon goes to the main hand first.
                        activateCharacterTarget(dollTarget, 0.0f, mouseY);
                    }

                    Character *pOwner = pParty->member(selectedPartyMemberIndex);

                    if (context.heldInventoryItem().active && pOwner != nullptr)
                    {
                        const InventoryItem leftover = context.heldInventoryItem().item;

                        if (pOwner->addInventoryItemAt(leftover, originX, originY)
                            || pParty->tryAutoPlaceItemInMemberInventory(selectedPartyMemberIndex, leftover))
                        {
                            context.heldInventoryItem() = {};
                            pParty->clearHeldItemForQueries();
                        }
                    }

                    return true;
                };

            if (hoveredOverviewItem)
            {
                InventoryBags::withBagOpen(*pParty, selectedPartyMemberIndex, hoveredCharacterTarget.bag,
                    gameRulesFor(pParty).items.bagCount(*pParty), useItem);
            }
            else
            {
                useItem();
            }

            return;
        }
    }

    GameplayOverlayInteractionState &interactionState = context.interactionState();

    if (input.mobileTouchDragStarted)
    {
        const GameplayCharacterPointerTarget dragStartTarget =
            findCharacterPointerTarget(input.mobileTouchDragStartX, input.mobileTouchDragStartY);
        const bool startsWithHeldItem = context.heldInventoryItem().active;
        const bool startsOnMovableItem =
            dragStartTarget.type == GameplayCharacterPointerTargetType::InventoryItem
            || dragStartTarget.type == GameplayCharacterPointerTargetType::EquipmentSlot;

        if (!startsWithHeldItem && startsOnMovableItem)
        {
            activateCharacterTarget(
                dragStartTarget,
                input.mobileTouchDragStartX,
                input.mobileTouchDragStartY);
        }

        interactionState.characterTouchItemDragActive =
            (startsWithHeldItem || startsOnMovableItem) && context.heldInventoryItem().active;
        interactionState.characterClickLatch = false;
        interactionState.characterPressedTarget = {};
    }

    if (input.mobileTouchDragReleased)
    {
        if (interactionState.characterTouchItemDragActive && context.heldInventoryItem().active)
        {
            activateCharacterTarget(findCharacterPointerTarget(mouseX, mouseY), mouseX, mouseY);
        }

        interactionState.characterTouchItemDragActive = false;
        interactionState.characterClickLatch = false;
        interactionState.characterPressedTarget = {};
        return;
    }

    if (input.mobileTouchDragActive)
    {
        interactionState.characterClickLatch = false;
        interactionState.characterPressedTarget = {};
        return;
    }

    handlePointerClickRelease(
        pointerState,
        interactionState.characterClickLatch,
        interactionState.characterPressedTarget,
        noneCharacterTarget,
        findCharacterPointerTarget,
        [&activateCharacterTarget, mouseX, mouseY](const GameplayCharacterPointerTarget &target)
        {
            activateCharacterTarget(target, mouseX, mouseY);
        });
}

} // namespace OpenYAMM::Game
