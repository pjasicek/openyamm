#include "game/gameplay/GameplayPartyOverlayInputController.h"

#include "game/tables/CharacterDollTable.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/app/KeyboardBindings.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/SpellIds.h"
#include "game/party/SkillData.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
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
};

struct CharacterSkillUiData
{
    std::vector<CharacterSkillUiRow> weaponRows;
    std::vector<CharacterSkillUiRow> magicRows;
    std::vector<CharacterSkillUiRow> armorRows;
    std::vector<CharacterSkillUiRow> miscRows;
};

constexpr const char *WeaponSkillNames[] = {
    "Axe", "Bow", "Dagger", "Mace", "Spear", "Staff", "Sword", "Unarmed", "Blaster",
};

constexpr const char *MagicSkillNames[] = {
    "FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic",
    "MindMagic", "BodyMagic", "LightMagic", "DarkMagic",
};

constexpr const char *ArmorSkillNames[] = {
    "LeatherArmor", "ChainArmor", "PlateArmor", "Shield", "Dodging",
};

constexpr const char *MiscSkillNames[] = {
    "Alchemy", "Armsmaster", "Bodybuilding", "IdentifyItem", "IdentifyMonster", "Learning",
    "DisarmTraps", "Meditation", "Merchant", "Perception", "RepairItem", "Stealing",
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
    const float scale = std::clamp(std::min(width / 640.0f, height / 480.0f), 0.8f, 2.0f);

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
    const std::string displayName = masteryDisplayName(mastery);

    if (displayName == "Grandmaster")
    {
        return "Grand";
    }

    return displayName;
}

void appendCharacterSkillUiRows(
    const Character &character,
    std::vector<CharacterSkillUiRow> &rows,
    std::unordered_set<std::string> &shownSkillNames,
    const char *const *pSkillNames,
    size_t skillCount,
    bool allowUpgradeInteraction)
{
    for (size_t skillIndex = 0; skillIndex < skillCount; ++skillIndex)
    {
        const std::string canonicalName = pSkillNames[skillIndex];
        const CharacterSkill *pSkill = character.findSkillByCanonicalName(canonicalName);

        if (pSkill == nullptr)
        {
            continue;
        }

        CharacterSkillUiRow row = {};
        row.canonicalName = canonicalName;
        row.label = displaySkillName(pSkill->name);

        if (pSkill->mastery != SkillMastery::None && pSkill->mastery != SkillMastery::Normal)
        {
            row.label += " " + skillPageMasteryDisplayName(pSkill->mastery);
        }

        row.level = std::to_string(pSkill->level);
        row.upgradeable = character.skillPoints > pSkill->level;
        row.interactive = row.upgradeable && allowUpgradeInteraction;
        rows.push_back(std::move(row));
        shownSkillNames.insert(canonicalName);
    }
}

CharacterSkillUiData buildCharacterSkillUiData(const Character *pCharacter, bool allowUpgradeInteraction)
{
    CharacterSkillUiData data = {};

    if (pCharacter == nullptr)
    {
        return data;
    }

    std::unordered_set<std::string> shownSkillNames;
    appendCharacterSkillUiRows(
        *pCharacter,
        data.weaponRows,
        shownSkillNames,
        WeaponSkillNames,
        std::size(WeaponSkillNames),
        allowUpgradeInteraction);
    appendCharacterSkillUiRows(
        *pCharacter,
        data.magicRows,
        shownSkillNames,
        MagicSkillNames,
        std::size(MagicSkillNames),
        allowUpgradeInteraction);
    appendCharacterSkillUiRows(
        *pCharacter,
        data.armorRows,
        shownSkillNames,
        ArmorSkillNames,
        std::size(ArmorSkillNames),
        allowUpgradeInteraction);
    appendCharacterSkillUiRows(
        *pCharacter,
        data.miscRows,
        shownSkillNames,
        MiscSkillNames,
        std::size(MiscSkillNames),
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
        row.label = displaySkillName(skill.name);

        if (skill.mastery != SkillMastery::None && skill.mastery != SkillMastery::Normal)
        {
            row.label += " " + skillPageMasteryDisplayName(skill.mastery);
        }

        row.level = std::to_string(skill.level);
        row.upgradeable = pCharacter->skillPoints > skill.level;
        row.interactive = row.upgradeable && allowUpgradeInteraction;
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

const char *equipmentSlotName(EquipmentSlot slot)
{
    switch (slot)
    {
    case EquipmentSlot::OffHand:
        return "OffHand";
    case EquipmentSlot::MainHand:
        return "MainHand";
    case EquipmentSlot::Bow:
        return "Bow";
    case EquipmentSlot::Armor:
        return "Armor";
    case EquipmentSlot::Helm:
        return "Helm";
    case EquipmentSlot::Belt:
        return "Belt";
    case EquipmentSlot::Cloak:
        return "Cloak";
    case EquipmentSlot::Gauntlets:
        return "Gauntlets";
    case EquipmentSlot::Boots:
        return "Boots";
    case EquipmentSlot::Amulet:
        return "Amulet";
    case EquipmentSlot::Ring1:
        return "Ring1";
    case EquipmentSlot::Ring2:
        return "Ring2";
    case EquipmentSlot::Ring3:
        return "Ring3";
    case EquipmentSlot::Ring4:
        return "Ring4";
    case EquipmentSlot::Ring5:
        return "Ring5";
    case EquipmentSlot::Ring6:
        return "Ring6";
    }

    return "Unknown";
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

    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!context.interactionState().closeOverlayLatch)
        {
            context.utilitySpellOverlay() = {};
            context.resetUtilitySpellOverlayInteractionState();
            context.setStatusBarEvent("Spell cancelled", 2.0f);
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
            if (context.spellTable() == nullptr)
            {
                return "Spell";
            }

            const SpellEntry *pEntry =
                context.spellTable()->findById(static_cast<int>(context.utilitySpellOverlayReadOnly().spellId));
            return pEntry != nullptr && !pEntry->name.empty() ? pEntry->name : "Spell";
        };

    if (context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::TownPortal)
    {
        if (!context.ensureTownPortalDestinationsLoaded())
        {
            context.utilitySpellOverlay() = {};
            context.resetUtilitySpellOverlayInteractionState();
            context.setStatusBarEvent("Town Portal destinations unavailable");
            return;
        }

        const Party *pParty = context.partyReadOnly();
        const auto findDestinationIndexByLayoutId =
            [&context](const std::string &layoutId) -> std::optional<size_t>
            {
                const std::string normalizedLayoutId = toLowerCopy(layoutId);

                for (size_t index = 0; index < context.townPortalDestinations().size(); ++index)
                {
                    if (toLowerCopy(context.townPortalDestinations()[index].buttonLayoutId) == normalizedLayoutId)
                    {
                        return index;
                    }
                }

                return std::nullopt;
            };
        const auto findTownPortalTarget =
            [&context, screenWidth, screenHeight, pParty, &findDestinationIndexByLayoutId](
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

                for (const std::string &layoutId : context.sortedHudLayoutIdsForScreen("TownPortal"))
                {
                    const std::optional<size_t> destinationIndex = findDestinationIndexByLayoutId(layoutId);

                    if (!destinationIndex.has_value())
                    {
                        continue;
                    }

                    if (*destinationIndex >= context.townPortalDestinations().size())
                    {
                        continue;
                    }

                    const GameplayTownPortalDestination &destination = context.townPortalDestinations()[*destinationIndex];

                    if (!isTownPortalDestinationUnlocked(pParty, destination))
                    {
                        continue;
                    }

                    const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(layoutId);

                    if (pLayout == nullptr || !pLayout->visible)
                    {
                        continue;
                    }

                    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved = context.resolveHudLayoutElement(
                        layoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                    if (!resolved.has_value() || !context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        continue;
                    }

                    return {GameplayUtilitySpellPointerTargetType::TownPortalDestination, *destinationIndex};
                }

                return {};
            };

        const GameplayUtilitySpellPointerTarget hoveredTarget =
            findTownPortalTarget(pointerState.x, pointerState.y);

        if (hoveredTarget.type == GameplayUtilitySpellPointerTargetType::TownPortalDestination
            && hoveredTarget.index < context.townPortalDestinations().size())
        {
            context.mutableStatusBarHoverText() =
                "Town Portal to " + context.townPortalDestinations()[hoveredTarget.index].label;
        }
        else
        {
            context.mutableStatusBarHoverText().clear();
        }

        handlePointerClickRelease(
            pointerState,
            context.interactionState().utilitySpellClickLatch,
            context.interactionState().utilitySpellPressedTarget,
            noneTarget,
            findTownPortalTarget,
            [&context, &resolveSpellName](const GameplayUtilitySpellPointerTarget &target)
            {
                if (target.type == GameplayUtilitySpellPointerTargetType::Close)
                {
                    context.utilitySpellOverlay() = {};
                    context.resetUtilitySpellOverlayInteractionState();
                    context.setStatusBarEvent("Spell cancelled", 2.0f);
                    return;
                }

                if (target.type != GameplayUtilitySpellPointerTargetType::TownPortalDestination
                    || target.index >= context.townPortalDestinations().size())
                {
                    return;
                }

                const GameplayTownPortalDestination &destination = context.townPortalDestinations()[target.index];
                PartySpellCastRequest request = {};
                request.casterMemberIndex = context.utilitySpellOverlayReadOnly().casterMemberIndex;
                request.spellId = context.utilitySpellOverlayReadOnly().spellId;
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
            });
        return;
    }

    context.mutableStatusBarHoverText().clear();

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
                context.setStatusBarEvent("Spell cancelled", 2.0f);
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

            PartySpellCastRequest request = {};
            request.casterMemberIndex = context.utilitySpellOverlayReadOnly().casterMemberIndex;
            request.spellId = context.utilitySpellOverlayReadOnly().spellId;

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
                    request.utilityStatusText = context.resolveMapLocationName(context.worldRuntime()->mapName());
                    request.utilityMapMoveDirectionDegrees =
                        static_cast<int32_t>(std::lround(context.gameplayCameraYawRadians() * 180.0f / 3.14159265358979323846f));
                }

                context.tryCastSpellRequest(request, resolveSpellName());
            }
        });
}

void GameplayPartyOverlayInputController::handleSpellbookOverlayInput(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input)
{
    const bool *pKeyboardState = input.keyboardState();
    const int screenWidth = input.screenWidth;
    const int screenHeight = input.screenHeight;
    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!context.interactionState().closeOverlayLatch)
        {
            context.closeSpellbookOverlay();
            context.interactionState().closeOverlayLatch = true;
        }
    }
    else
    {
        context.interactionState().closeOverlayLatch = false;
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
            for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
            {
                if (!context.activeMemberHasSpellbookSchool(definition.school))
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

            const GameplaySpellbookPointerTarget attackCastTarget =
                resolveSimpleButtonTarget(
                    "SpellbookAttackCastButton",
                    GameplaySpellbookPointerTargetType::AttackCastButton);

            if (attackCastTarget.type != GameplaySpellbookPointerTargetType::None)
            {
                return attackCastTarget;
            }

            const SpellbookSchoolUiDefinition *pDefinition =
                findSpellbookSchoolUiDefinition(context.spellbook().school);

            if (pDefinition == nullptr)
            {
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

                    context.spellbook().school = target.school;
                    context.spellbook().selectedSpellId = 0;
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
                        context.setStatusBarEvent("Spell not learned");
                        return;
                    }

                    const SpellEntry *pSpellEntry =
                        context.spellTable() != nullptr
                            ? context.spellTable()->findById(static_cast<int>(target.spellId))
                            : nullptr;
                    const std::string spellName =
                        pSpellEntry != nullptr && !pSpellEntry->name.empty()
                            ? pSpellEntry->name
                            : ("Spell " + std::to_string(target.spellId));
                    const size_t casterMemberIndex =
                        context.partyReadOnly() != nullptr ? context.partyReadOnly()->activeMemberIndex() : 0;

                    if (context.tryCastSpellFromMember(casterMemberIndex, target.spellId, spellName))
                    {
                        context.closeSpellbookOverlay();
                    }
                }

                return;
            }

            if (target.type == GameplaySpellbookPointerTargetType::CloseButton)
            {
                context.closeSpellbookOverlay();
                return;
            }

            if (target.type == GameplaySpellbookPointerTargetType::QuickCastButton)
            {
                if (context.party() == nullptr || context.spellTable() == nullptr)
                {
                    context.setStatusBarEvent("Can't set quick spell");
                    return;
                }

                Character *pActiveMember = context.party()->activeMember();

                if (pActiveMember == nullptr)
                {
                    context.setStatusBarEvent("Can't set quick spell");
                    return;
                }

                if (context.spellbook().selectedSpellId == 0)
                {
                    pActiveMember->quickSpellName.clear();
                    context.spellbook().selectedSpellId = 0;

                    if (context.audioSystem() != nullptr)
                    {
                        context.audioSystem()->playCommonSound(SoundId::Fizzle, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    context.setStatusBarEvent("Quick spell cleared");
                    return;
                }

                const SpellEntry *pSpellEntry =
                    context.spellTable()->findById(static_cast<int>(context.spellbook().selectedSpellId));

                if (pSpellEntry == nullptr)
                {
                    context.setStatusBarEvent("Can't set quick spell");
                    return;
                }

                if (!pActiveMember->knowsSpell(context.spellbook().selectedSpellId))
                {
                    context.setStatusBarEvent("Spell not learned");
                    return;
                }

                if (pActiveMember->quickSpellName == pSpellEntry->name)
                {
                    pActiveMember->quickSpellName.clear();
                    context.spellbook().selectedSpellId = 0;

                    if (context.audioSystem() != nullptr)
                    {
                        context.audioSystem()->playCommonSound(SoundId::Fizzle, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    context.setStatusBarEvent("Quick spell cleared");
                    return;
                }

                pActiveMember->quickSpellName = pSpellEntry->name;

                if (context.audioSystem() != nullptr)
                {
                    context.audioSystem()->playCommonSound(SoundId::ClickSkill, GameAudioSystem::PlaybackGroup::Ui);
                }

                context.playSpeechReaction(
                    context.partyReadOnly()->activeMemberIndex(),
                    SpeechId::SetQuickSpell,
                    true);
                context.setStatusBarEvent("Quick spell set to " + pSpellEntry->name);
                return;
            }

            if (target.type == GameplaySpellbookPointerTargetType::AttackCastButton)
            {
                if (context.party() == nullptr || context.spellTable() == nullptr)
                {
                    context.setStatusBarEvent("Can't set attack spell");
                    return;
                }

                Character *pActiveMember = context.party()->activeMember();

                if (pActiveMember == nullptr)
                {
                    context.setStatusBarEvent("Can't set attack spell");
                    return;
                }

                if (context.spellbook().selectedSpellId == 0)
                {
                    pActiveMember->attackSpellName.clear();
                    context.spellbook().selectedSpellId = 0;

                    if (context.audioSystem() != nullptr)
                    {
                        context.audioSystem()->playCommonSound(SoundId::Fizzle, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    context.setStatusBarEvent("Attack spell cleared");
                    return;
                }

                const SpellEntry *pSpellEntry =
                    context.spellTable()->findById(static_cast<int>(context.spellbook().selectedSpellId));

                if (pSpellEntry == nullptr)
                {
                    context.setStatusBarEvent("Can't set attack spell");
                    return;
                }

                if (!pActiveMember->knowsSpell(context.spellbook().selectedSpellId))
                {
                    context.setStatusBarEvent("Spell not learned");
                    return;
                }

                if (pActiveMember->attackSpellName == pSpellEntry->name)
                {
                    pActiveMember->attackSpellName.clear();
                    context.spellbook().selectedSpellId = 0;

                    if (context.audioSystem() != nullptr)
                    {
                        context.audioSystem()->playCommonSound(SoundId::Fizzle, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    context.setStatusBarEvent("Attack spell cleared");
                    return;
                }

                pActiveMember->attackSpellName = pSpellEntry->name;

                if (context.audioSystem() != nullptr)
                {
                    context.audioSystem()->playCommonSound(SoundId::ClickSkill, GameAudioSystem::PlaybackGroup::Ui);
                }

                context.playSpeechReaction(
                    context.partyReadOnly()->activeMemberIndex(),
                    SpeechId::SetQuickSpell,
                    true);
                context.setStatusBarEvent("Attack spell set to " + pSpellEntry->name);
            }
        });
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
                || *context.interactionState().pendingCharacterDismissMemberIndex != pParty->activeMemberIndex())))
    {
        clearPendingCharacterDismiss();
    }

    const CharacterDollTable *pCharacterDollTable = context.characterDollTable();
    const CharacterDollEntry *pActiveCharacterDollEntry =
        resolveCharacterDollEntry(pCharacterDollTable, pActiveCharacter);
    const CharacterDollTypeEntry *pActiveCharacterDollType =
        pActiveCharacterDollEntry != nullptr && pCharacterDollTable != nullptr
            ? pCharacterDollTable->getDollType(pActiveCharacterDollEntry->dollTypeId)
            : nullptr;
    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pActiveCharacter, !isReadOnlyAdventurersInnView);
    const std::optional<GameplayHudFontHandle> skillRowFont = context.findHudFont("Lucida");
    const float skillRowHeight =
        skillRowFont.has_value() ? static_cast<float>(std::max(1, skillRowFont->fontHeight - 3)) : 11.0f;
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

    const bool closePressed =
        pKeyboardState != nullptr && (pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E]);
    const bool isInventorySpellTargetMode =
        context.utilitySpellOverlayReadOnly().active
        && context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;

    if (closePressed)
    {
        if (!context.interactionState().closeOverlayLatch)
        {
            if (isInventorySpellTargetMode)
            {
                context.utilitySpellOverlay() = {};
            }

            context.characterScreen().open = false;
            context.characterScreen().dollJewelryOverlayOpen = false;
            context.characterScreen().adventurersInnRosterOverlayOpen = false;
            clearPendingCharacterDismiss();
            context.interactionState().closeOverlayLatch = true;
        }
    }
    else
    {
        context.interactionState().closeOverlayLatch = false;
    }

    const bool charCycleNewlyPressed = input.action(KeyboardAction::CharCycle).pressed;

    if (charCycleNewlyPressed)
    {
        if (pParty != nullptr && !pParty->members().empty())
        {
            const size_t nextMemberIndex = (pParty->activeMemberIndex() + 1) % pParty->members().size();
            context.trySelectPartyMember(nextMemberIndex, false);
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
                    const float baseScale =
                        std::min(uiViewport.width / 640.0f, uiViewport.height / 480.0f);

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
                        context.gameplayUiRuntime().ensureHudTextureLoaded(dynamicTextureName);

                    if (texture.has_value())
                    {
                        dynamicRect = context.resolveCharacterEquipmentRenderRect(
                            *pLayout,
                            *pItemDefinition,
                            *texture,
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

                    if (!isReadOnlyAdventurersInnView && context.heldInventoryItem().active)
                    {
                        GameplayCharacterPointerTarget target = {};
                        target.type = GameplayCharacterPointerTargetType::InventoryCell;
                        target.page = GameplayUiController::CharacterPage::Inventory;
                        target.gridX = gridX;
                        target.gridY = gridY;
                        return target;
                    }

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
                }
            }

            if (context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Skills)
            {
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
                        const float rowWidth = resolvedLevelHeader->x + resolvedLevelHeader->width - resolvedRegion->x;

                        for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
                        {
                            const CharacterSkillUiRow &row = rows[rowIndex];

                            if (!row.interactive)
                            {
                                continue;
                            }

                            const float rowY = resolvedRegion->y + static_cast<float>(rowIndex) * rowHeightPixels;

                            if (pointerX >= resolvedRegion->x
                                && pointerX < resolvedRegion->x + rowWidth
                                && pointerY >= rowY
                                && pointerY < rowY + rowHeightPixels)
                            {
                                GameplayCharacterPointerTarget target = {};
                                target.type = GameplayCharacterPointerTargetType::SkillRow;
                                target.page = GameplayUiController::CharacterPage::Skills;
                                target.skillName = row.canonicalName;
                                return target;
                            }
                        }

                        return {};
                    };

                const GameplayCharacterPointerTarget weaponTarget = findSkillRowTarget(
                    "CharacterSkillsWeaponsListRegion",
                    "CharacterSkillsWeaponsLevelHeader",
                    skillUiData.weaponRows);

                if (weaponTarget.type == GameplayCharacterPointerTargetType::SkillRow)
                {
                    return weaponTarget;
                }

                const GameplayCharacterPointerTarget magicTarget = findSkillRowTarget(
                    "CharacterSkillsMagicListRegion",
                    "CharacterSkillsMagicLevelHeader",
                    skillUiData.magicRows);

                if (magicTarget.type == GameplayCharacterPointerTargetType::SkillRow)
                {
                    return magicTarget;
                }

                const GameplayCharacterPointerTarget armorTarget = findSkillRowTarget(
                    "CharacterSkillsArmorListRegion",
                    "CharacterSkillsArmorLevelHeader",
                    skillUiData.armorRows);

                if (armorTarget.type == GameplayCharacterPointerTargetType::SkillRow)
                {
                    return armorTarget;
                }

                const GameplayCharacterPointerTarget miscTarget = findSkillRowTarget(
                    "CharacterSkillsMiscListRegion",
                    "CharacterSkillsMiscLevelHeader",
                    skillUiData.miscRows);

                if (miscTarget.type == GameplayCharacterPointerTargetType::SkillRow)
                {
                    return miscTarget;
                }
            }

            return {};
        };

    const HudPointerState pointerState = {mouseX, mouseY, isLeftMousePressed};
    const GameplayCharacterPointerTarget noneCharacterTarget = {};
    const GameplayCharacterPointerTarget hoveredCharacterTarget = findCharacterPointerTarget(mouseX, mouseY);

    if (pParty != nullptr)
    {
        context.itemService().updateReadableScrollOverlayForHeldItem(
            pParty->activeMemberIndex(),
            hoveredCharacterTarget,
            isLeftMousePressed);
    }
    else
    {
        context.itemService().closeReadableScrollOverlay();
    }

    handlePointerClickRelease(
        pointerState,
        context.interactionState().characterClickLatch,
        context.interactionState().characterPressedTarget,
        noneCharacterTarget,
        findCharacterPointerTarget,
        [&context,
         pActiveCharacterDollType,
         pActiveCharacter,
         pParty,
         screenWidth,
         screenHeight,
         mouseX,
         mouseY,
         &clearPendingCharacterDismiss,
         &resolveCharacterInventoryGrid,
         isReadOnlyAdventurersInnView](const GameplayCharacterPointerTarget &target)
        {
            const bool isInventorySpellTargetMode =
                context.utilitySpellOverlayReadOnly().active
                && context.utilitySpellOverlayReadOnly().mode == GameplayUiController::UtilitySpellOverlayMode::InventoryTarget;
            const auto setHeldItem =
                [&context](const InventoryItem &item)
                {
                    context.heldInventoryItem() = {};
                    context.heldInventoryItem().active = true;
                    context.heldInventoryItem().item = item;
                    context.heldInventoryItem().grabCellOffsetX = 0;
                    context.heldInventoryItem().grabCellOffsetY = 0;
                    context.heldInventoryItem().grabOffsetX = 0.0f;
                    context.heldInventoryItem().grabOffsetY = 0.0f;
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
                    PartySpellCastRequest request = {};
                    request.casterMemberIndex = context.utilitySpellOverlayReadOnly().casterMemberIndex;
                    request.spellId = context.utilitySpellOverlayReadOnly().spellId;
                    request.targetItemMemberIndex =
                        pParty != nullptr ? std::optional<size_t>(pParty->activeMemberIndex()) : std::nullopt;
                    request.targetInventoryGridX = target.gridX;
                    request.targetInventoryGridY = target.gridY;
                    context.tryCastSpellRequest(request, resolveSpellName(request.spellId));
                    return;
                }

                if (target.type == GameplayCharacterPointerTargetType::EquipmentSlot)
                {
                    PartySpellCastRequest request = {};
                    request.casterMemberIndex = context.utilitySpellOverlayReadOnly().casterMemberIndex;
                    request.spellId = context.utilitySpellOverlayReadOnly().spellId;
                    request.targetItemMemberIndex =
                        pParty != nullptr ? std::optional<size_t>(pParty->activeMemberIndex()) : std::nullopt;
                    request.targetEquipmentSlot = target.equipmentSlot;
                    context.tryCastSpellRequest(request, resolveSpellName(request.spellId));
                    return;
                }
            }

            if (target.type == GameplayCharacterPointerTargetType::PageButton)
            {
                if (isInventorySpellTargetMode && target.page != GameplayUiController::CharacterPage::Inventory)
                {
                    context.setStatusBarEvent("Select an item");
                    return;
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
                    context.characterScreen().open = false;
                    context.characterScreen().dollJewelryOverlayOpen = false;
                    context.characterScreen().adventurersInnRosterOverlayOpen = false;
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
                    pInnMember != nullptr ? pInnMember->character.name : "Adventurer";

                if (pParty->hireAdventurersInnMember(innIndex))
                {
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

                    context.setStatusBarEvent(memberName + " joined the party.");
                }
                else
                {
                    context.setStatusBarEvent(
                        pParty->lastStatus().empty() ? "Can't hire adventurer." : pParty->lastStatus());
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::DismissButton && pParty != nullptr)
            {
                const size_t memberIndex = pParty->activeMemberIndex();
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
                        "To confirm " + pMember->name + " dismissal press the button again...",
                        2.0f);
                }
                else
                {
                    const std::string dismissedName = pMember->name;
                    clearPendingCharacterDismiss();

                    if (pParty->dismissMemberToAdventurersInn(memberIndex))
                    {
                        context.characterScreen().dollJewelryOverlayOpen = false;
                        context.setStatusBarEvent(dismissedName + " dismissed.");
                    }
                    else
                    {
                        context.setStatusBarEvent("Dismissal failed.");
                    }
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::MagnifyButton)
            {
                context.characterScreen().dollJewelryOverlayOpen = !context.characterScreenReadOnly().dollJewelryOverlayOpen;
                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::SkillRow && pParty != nullptr)
            {
                if (pParty->increaseActiveMemberSkillLevel(target.skillName))
                {
                    if (context.audioSystem() != nullptr)
                    {
                        context.audioSystem()->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    context.playSpeechReaction(pParty->activeMemberIndex(), SpeechId::SkillIncreased, true);
                }

                return;
            }

            if (pParty == nullptr || context.itemTable() == nullptr)
            {
                return;
            }

            Character *pCharacter = pParty->activeMember();

            if (pCharacter == nullptr)
            {
                return;
            }

            const size_t memberIndex = pParty->activeMemberIndex();

            if (target.type == GameplayCharacterPointerTargetType::EquipmentSlot)
            {
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
                    InventoryItemUseRuntime::classifyItemUse(context.heldInventoryItem().item, *context.itemTable());

                if (useAction != InventoryItemUseAction::None
                    && useAction != InventoryItemUseAction::Equip
                    && useAction != InventoryItemUseAction::ReadMessageScroll)
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
                    context.setStatusBarEvent("Can't equip that item there");
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
                    context.setStatusBarEvent(
                        pParty->lastStatus().empty() ? "Can't equip that item" : pParty->lastStatus());
                    return;
                }

                if (heldReplacement.has_value())
                {
                    setHeldItem(*heldReplacement);
                }
                else
                {
                    context.heldInventoryItem() = {};
                }

                return;
            }

            if (target.type == GameplayCharacterPointerTargetType::DollPanel && context.heldInventoryItem().active)
            {
                const InventoryItemUseAction useAction =
                    InventoryItemUseRuntime::classifyItemUse(context.heldInventoryItem().item, *context.itemTable());

                if (useAction != InventoryItemUseAction::None
                    && useAction != InventoryItemUseAction::Equip
                    && useAction != InventoryItemUseAction::ReadMessageScroll)
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
                    resolvedDoll.has_value() && mouseX >= resolvedDoll->x + resolvedDoll->width * 0.5f;
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
                    context.setStatusBarEvent("Can't equip that item");
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
                    context.setStatusBarEvent(
                        pParty->lastStatus().empty() ? "Can't equip that item" : pParty->lastStatus());
                    return;
                }

                if (heldReplacement.has_value())
                {
                    setHeldItem(*heldReplacement);
                }
                else
                {
                    context.heldInventoryItem() = {};
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
                    context.gameplayUiRuntime().ensureHudTextureLoaded(pItemDefinition->iconName);

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
                const float itemWidth = static_cast<float>(itemTexture->width) * gridMetrics.scale;
                const float itemHeight = static_cast<float>(itemTexture->height) * gridMetrics.scale;
                const float drawX = mouseX - context.heldInventoryItem().grabOffsetX;
                const float drawY = mouseY - context.heldInventoryItem().grabOffsetY;
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
                    context.setStatusBarEvent(
                        pParty->lastStatus().empty() ? "Can't place item" : pParty->lastStatus());
                    return;
                }

                if (replacedItem.has_value())
                {
                    context.heldInventoryItem().item = *replacedItem;
                    context.heldInventoryItem().grabCellOffsetX = 0;
                    context.heldInventoryItem().grabCellOffsetY = 0;
                    context.heldInventoryItem().grabOffsetX = 0.0f;
                    context.heldInventoryItem().grabOffsetY = 0.0f;
                }
                else
                {
                    context.heldInventoryItem() = {};
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
                context.gameplayUiRuntime().ensureHudTextureLoaded(pItemDefinition->iconName);

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
                static_cast<int>((mouseX - resolvedInventoryGrid->x) / gridMetrics.cellWidth),
                0,
                Character::InventoryWidth - 1));
            const uint8_t hoveredGridY = static_cast<uint8_t>(std::clamp(
                static_cast<int>((mouseY - resolvedInventoryGrid->y) / gridMetrics.cellHeight),
                0,
                Character::InventoryHeight - 1));
            context.heldInventoryItem().grabCellOffsetX = hoveredGridX - heldItem.gridX;
            context.heldInventoryItem().grabCellOffsetY = hoveredGridY - heldItem.gridY;
            const float itemWidth = static_cast<float>(itemTexture->width) * gridMetrics.scale;
            const float itemHeight = static_cast<float>(itemTexture->height) * gridMetrics.scale;
            const InventoryItemScreenRect itemRect =
                computeInventoryItemScreenRect(gridMetrics, heldItem, itemWidth, itemHeight);
            context.heldInventoryItem().grabOffsetX = mouseX - itemRect.x;
            context.heldInventoryItem().grabOffsetY = mouseY - itemRect.y;
        });
}

} // namespace OpenYAMM::Game
