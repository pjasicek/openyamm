#include "game/gameplay/GameplayPartyOverlayInputController.h"

#include "game/tables/CharacterDollTable.h"
#include "game/gameplay/GameMechanics.h"
#include "game/app/KeyboardBindings.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/party/SpellIds.h"
#include "game/party/SkillData.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/StringUtils.h"
#include "game/ui/HudUiService.h"

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
    const OutdoorGameView::TownPortalDestination &destination)
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
    OutdoorGameView &view,
    const bool *pKeyboardState,
    int screenWidth,
    int screenHeight)
{
    if (!view.m_utilitySpellOverlay.active)
    {
        return;
    }

    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!view.m_closeOverlayLatch)
        {
            view.m_gameplayUiController.closeUtilitySpellOverlay();
            view.setStatusBarEvent("Spell cancelled", 2.0f);
            view.m_closeOverlayLatch = true;
        }

        return;
    }

    view.m_closeOverlayLatch = false;

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const HudPointerState pointerState = {
        mouseX,
        mouseY,
        (mouseButtons & SDL_BUTTON_LMASK) != 0
    };
    const OutdoorGameView::UtilitySpellPointerTarget noneTarget = {};
    const auto resolveSpellName =
        [&view]() -> std::string
        {
            if (view.m_pSpellTable == nullptr)
            {
                return "Spell";
            }

            const SpellEntry *pEntry =
                view.m_pSpellTable->findById(static_cast<int>(view.m_utilitySpellOverlay.spellId));
            return pEntry != nullptr && !pEntry->name.empty() ? pEntry->name : "Spell";
        };

    if (view.m_utilitySpellOverlay.mode == OutdoorGameView::UtilitySpellOverlayMode::TownPortal)
    {
        const Party *pParty = view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->party() : nullptr;
        const auto findDestinationIndexByLayoutId =
            [&view](const std::string &layoutId) -> std::optional<size_t>
            {
                const std::string normalizedLayoutId = toLowerCopy(layoutId);

                for (size_t index = 0; index < view.m_townPortalDestinations.size(); ++index)
                {
                    if (toLowerCopy(view.m_townPortalDestinations[index].buttonLayoutId) == normalizedLayoutId)
                    {
                        return index;
                    }
                }

                return std::nullopt;
            };
        const auto findTownPortalTarget =
            [&view, screenWidth, screenHeight, pParty, &findDestinationIndexByLayoutId](
                float pointerX,
                float pointerY) -> OutdoorGameView::UtilitySpellPointerTarget
            {
                const OutdoorGameView::HudLayoutElement *pCloseLayout =
                    HudUiService::findHudLayoutElement(view, "TownPortalCloseButton");

                if (pCloseLayout != nullptr && pCloseLayout->visible)
                {
                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> closeResolved =
                        HudUiService::resolveHudLayoutElement(
                            view,
                            "TownPortalCloseButton",
                            screenWidth,
                            screenHeight,
                            pCloseLayout->width,
                            pCloseLayout->height);

                    if (closeResolved.has_value()
                        && HudUiService::isPointerInsideResolvedElement(*closeResolved, pointerX, pointerY))
                    {
                        return {OutdoorGameView::UtilitySpellPointerTargetType::Close, 0};
                    }
                }

                for (const std::string &layoutId : HudUiService::sortedHudLayoutIdsForScreen(view, "TownPortal"))
                {
                    const std::optional<size_t> destinationIndex = findDestinationIndexByLayoutId(layoutId);

                    if (!destinationIndex.has_value())
                    {
                        continue;
                    }

                    if (*destinationIndex >= view.m_townPortalDestinations.size())
                    {
                        continue;
                    }

                    const OutdoorGameView::TownPortalDestination &destination = view.m_townPortalDestinations[*destinationIndex];

                    if (!isTownPortalDestinationUnlocked(pParty, destination))
                    {
                        continue;
                    }

                    const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

                    if (pLayout == nullptr || !pLayout->visible)
                    {
                        continue;
                    }

                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(
                        view,
                        layoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                    if (!resolved.has_value() || !HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        continue;
                    }

                    return {OutdoorGameView::UtilitySpellPointerTargetType::TownPortalDestination, *destinationIndex};
                }

                return {};
            };

        const OutdoorGameView::UtilitySpellPointerTarget hoveredTarget = findTownPortalTarget(mouseX, mouseY);

        if (hoveredTarget.type == OutdoorGameView::UtilitySpellPointerTargetType::TownPortalDestination
            && hoveredTarget.index < view.m_townPortalDestinations.size())
        {
            view.m_statusBarHoverText = "Town Portal to " + view.m_townPortalDestinations[hoveredTarget.index].label;
        }
        else
        {
            view.m_statusBarHoverText.clear();
        }

        handlePointerClickRelease(
            pointerState,
            view.m_utilitySpellClickLatch,
            view.m_utilitySpellPressedTarget,
            noneTarget,
            findTownPortalTarget,
            [&view, &resolveSpellName](const OutdoorGameView::UtilitySpellPointerTarget &target)
            {
                if (target.type == OutdoorGameView::UtilitySpellPointerTargetType::Close)
                {
                    view.m_gameplayUiController.closeUtilitySpellOverlay();
                    view.setStatusBarEvent("Spell cancelled", 2.0f);
                    return;
                }

                if (target.type != OutdoorGameView::UtilitySpellPointerTargetType::TownPortalDestination
                    || target.index >= view.m_townPortalDestinations.size())
                {
                    return;
                }

                const OutdoorGameView::TownPortalDestination &destination = view.m_townPortalDestinations[target.index];
                PartySpellCastRequest request = {};
                request.casterMemberIndex = view.m_utilitySpellOverlay.casterMemberIndex;
                request.spellId = view.m_utilitySpellOverlay.spellId;
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
                view.tryCastSpellRequest(request, resolveSpellName());
            });
        return;
    }

    view.m_statusBarHoverText.clear();

    const UtilityOverlayLayout layout = computeUtilityOverlayLayout(screenWidth, screenHeight);
    const auto findPointerTarget =
        [&view, &layout](float pointerX, float pointerY) -> OutdoorGameView::UtilitySpellPointerTarget
        {
            if (pointInsideRect(pointerX, pointerY, layout.closeX, layout.closeY, layout.closeSize, layout.closeSize))
            {
                return {OutdoorGameView::UtilitySpellPointerTargetType::Close, 0};
            }

            if (view.m_utilitySpellOverlay.mode == OutdoorGameView::UtilitySpellOverlayMode::LloydsBeacon)
            {
                const float tabY = layout.panelY + 24.0f;
                const float setTabX = layout.contentX;
                const float recallTabX = setTabX + layout.tabWidth + layout.tabGap;

                if (pointInsideRect(pointerX, pointerY, setTabX, tabY, layout.tabWidth, layout.tabHeight))
                {
                    return {OutdoorGameView::UtilitySpellPointerTargetType::LloydSetTab, 0};
                }

                if (pointInsideRect(pointerX, pointerY, recallTabX, tabY, layout.tabWidth, layout.tabHeight))
                {
                    return {OutdoorGameView::UtilitySpellPointerTargetType::LloydRecallTab, 0};
                }

                const Character *pCaster =
                    view.m_pOutdoorPartyRuntime != nullptr
                        ? view.m_pOutdoorPartyRuntime->party().member(view.m_utilitySpellOverlay.casterMemberIndex)
                        : nullptr;
                const size_t slotCount = maxLloydBeaconSlots(pCaster);

                for (size_t index = 0; index < slotCount; ++index)
                {
                    const float rowY = layout.contentY + static_cast<float>(index) * (layout.rowHeight + 6.0f);

                    if (!pointInsideRect(pointerX, pointerY, layout.contentX, rowY, layout.contentWidth, layout.rowHeight))
                    {
                        continue;
                    }

                    return {OutdoorGameView::UtilitySpellPointerTargetType::LloydSlot, index};
                }
            }

            return {};
        };

    handlePointerClickRelease(
        pointerState,
        view.m_utilitySpellClickLatch,
        view.m_utilitySpellPressedTarget,
        noneTarget,
        findPointerTarget,
        [&view, &resolveSpellName](const OutdoorGameView::UtilitySpellPointerTarget &target)
        {
            if (target.type == OutdoorGameView::UtilitySpellPointerTargetType::Close)
            {
                view.m_gameplayUiController.closeUtilitySpellOverlay();
                view.setStatusBarEvent("Spell cancelled", 2.0f);
                return;
            }

            if (target.type == OutdoorGameView::UtilitySpellPointerTargetType::LloydSetTab)
            {
                view.m_utilitySpellOverlay.lloydRecallMode = false;
                return;
            }

            if (target.type == OutdoorGameView::UtilitySpellPointerTargetType::LloydRecallTab)
            {
                view.m_utilitySpellOverlay.lloydRecallMode = true;
                return;
            }

            PartySpellCastRequest request = {};
            request.casterMemberIndex = view.m_utilitySpellOverlay.casterMemberIndex;
            request.spellId = view.m_utilitySpellOverlay.spellId;

            if (target.type == OutdoorGameView::UtilitySpellPointerTargetType::TownPortalDestination)
            {
                if (target.index >= view.m_townPortalDestinations.size())
                {
                    return;
                }

                const OutdoorGameView::TownPortalDestination &destination = view.m_townPortalDestinations[target.index];
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
                view.tryCastSpellRequest(request, resolveSpellName());
                return;
            }

            if (target.type == OutdoorGameView::UtilitySpellPointerTargetType::LloydSlot)
            {
                if (view.m_pOutdoorPartyRuntime == nullptr || view.m_pOutdoorWorldRuntime == nullptr)
                {
                    return;
                }

                const Character *pCaster =
                    view.m_pOutdoorPartyRuntime->party().member(view.m_utilitySpellOverlay.casterMemberIndex);

                if (pCaster == nullptr || target.index >= pCaster->lloydsBeacons.size())
                {
                    return;
                }

                request.utilitySlotIndex = static_cast<uint8_t>(target.index);

                if (view.m_utilitySpellOverlay.lloydRecallMode)
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
                    request.utilityStatusText =
                        view.resolveSaveLocationName(view.m_pOutdoorWorldRuntime->mapName());
                    request.utilityMapMoveDirectionDegrees =
                        static_cast<int32_t>(std::lround(view.cameraYawRadians() * 180.0f / 3.14159265358979323846f));
                }

                view.tryCastSpellRequest(request, resolveSpellName());
            }
        });
}

void GameplayPartyOverlayInputController::handleSpellbookOverlayInput(
    OutdoorGameView &view,
    const bool *pKeyboardState,
    int screenWidth,
    int screenHeight)
{
    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (closePressed)
    {
        if (!view.m_closeOverlayLatch)
        {
            view.closeSpellbook();
            view.m_closeOverlayLatch = true;
        }
    }
    else
    {
        view.m_closeOverlayLatch = false;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
    const HudPointerState pointerState = {
        mouseX,
        mouseY,
        isLeftMousePressed
    };
    const OutdoorGameView::SpellbookPointerTarget noneSpellbookTarget = {};
    const auto findSpellbookPointerTarget =
        [&view, screenWidth, screenHeight](float pointerX, float pointerY) -> OutdoorGameView::SpellbookPointerTarget
        {
            for (const SpellbookSchoolUiDefinition &definition : spellbookSchoolUiDefinitions())
            {
                if (!view.activeMemberHasSpellbookSchool(definition.school))
                {
                    continue;
                }

                const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, definition.pButtonLayoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
                    definition.pButtonLayoutId,
                    screenWidth,
                    screenHeight,
                    pLayout->width,
                    pLayout->height);

                if (resolved && HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    OutdoorGameView::SpellbookPointerTarget target = {};
                    target.type = OutdoorGameView::SpellbookPointerTargetType::SchoolButton;
                    target.school = definition.school;
                    return target;
                }
            }

            const auto resolveSimpleButtonTarget =
                [&view, screenWidth, screenHeight, pointerX, pointerY](
                    const char *pLayoutId,
                    OutdoorGameView::SpellbookPointerTargetType type) -> OutdoorGameView::SpellbookPointerTarget
                {
                    const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);

                    if (pLayout == nullptr)
                    {
                        return {};
                    }

                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
                        pLayoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                    if (!resolved || !HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        return {};
                    }

                    OutdoorGameView::SpellbookPointerTarget target = {};
                    target.type = type;
                    return target;
                };

            const OutdoorGameView::SpellbookPointerTarget closeTarget =
                resolveSimpleButtonTarget("SpellbookCloseButton", OutdoorGameView::SpellbookPointerTargetType::CloseButton);

            if (closeTarget.type != OutdoorGameView::SpellbookPointerTargetType::None)
            {
                return closeTarget;
            }

            const OutdoorGameView::SpellbookPointerTarget quickCastTarget =
                resolveSimpleButtonTarget("SpellbookQuickCastButton", OutdoorGameView::SpellbookPointerTargetType::QuickCastButton);

            if (quickCastTarget.type != OutdoorGameView::SpellbookPointerTargetType::None)
            {
                return quickCastTarget;
            }

            const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(view.m_spellbook.school);

            if (pDefinition == nullptr)
            {
                return {};
            }

            for (uint32_t spellOffset = 0; spellOffset < pDefinition->spellCount; ++spellOffset)
            {
                const uint32_t spellId = pDefinition->firstSpellId + spellOffset;

                if (!view.activeMemberKnowsSpell(spellId))
                {
                    continue;
                }

                const uint32_t spellOrdinal = spellOffset + 1;
                const std::string layoutId = spellbookSpellLayoutId(view.m_spellbook.school, spellOrdinal);
                const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, layoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
                    layoutId,
                    screenWidth,
                    screenHeight,
                    pLayout->width,
                    pLayout->height);

                if (resolved && HudUiService::isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    OutdoorGameView::SpellbookPointerTarget target = {};
                    target.type = OutdoorGameView::SpellbookPointerTargetType::SpellButton;
                    target.school = view.m_spellbook.school;
                    target.spellId = spellId;
                    return target;
                }
            }

            return {};
        };

    handlePointerClickRelease(
        pointerState,
        view.m_spellbookClickLatch,
        view.m_spellbookPressedTarget,
        noneSpellbookTarget,
        findSpellbookPointerTarget,
        [&view](const OutdoorGameView::SpellbookPointerTarget &target)
        {
            if (target.type == OutdoorGameView::SpellbookPointerTargetType::SchoolButton)
            {
                const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(target.school);

                if (pDefinition != nullptr)
                {
                    if (view.m_pGameAudioSystem != nullptr && view.m_spellbook.school != target.school)
                    {
                        view.m_pGameAudioSystem->playCommonSound(
                            SoundId::TurnPageDown,
                            GameAudioSystem::PlaybackGroup::Ui);
                    }

                    view.m_spellbook.school = target.school;
                    view.m_spellbook.selectedSpellId = 0;
                }

                return;
            }

            if (target.type == OutdoorGameView::SpellbookPointerTargetType::SpellButton)
            {
                const uint64_t nowTicks = SDL_GetTicks();
                const bool isDoubleClick =
                    target.spellId != 0
                    && target.spellId == view.m_lastSpellbookClickedSpellId
                    && nowTicks >= view.m_lastSpellbookSpellClickTicks
                    && nowTicks - view.m_lastSpellbookSpellClickTicks <= PartyPortraitDoubleClickWindowMs;
                view.m_spellbook.selectedSpellId = target.spellId;
                view.m_lastSpellbookSpellClickTicks = nowTicks;
                view.m_lastSpellbookClickedSpellId = target.spellId;

                if (isDoubleClick)
                {
                    if (!view.activeMemberKnowsSpell(target.spellId))
                    {
                        view.setStatusBarEvent("Spell not learned");
                        return;
                    }

                    const SpellEntry *pSpellEntry =
                        view.m_pSpellTable != nullptr ? view.m_pSpellTable->findById(static_cast<int>(target.spellId)) : nullptr;
                    const std::string spellName =
                        pSpellEntry != nullptr && !pSpellEntry->name.empty()
                            ? pSpellEntry->name
                            : ("Spell " + std::to_string(target.spellId));
                    const size_t casterMemberIndex =
                        view.m_pOutdoorPartyRuntime != nullptr ? view.m_pOutdoorPartyRuntime->party().activeMemberIndex() : 0;

                    if (view.tryCastSpellFromMember(casterMemberIndex, target.spellId, spellName))
                    {
                        view.closeSpellbook();
                    }
                }

                return;
            }

            if (target.type == OutdoorGameView::SpellbookPointerTargetType::CloseButton)
            {
                view.closeSpellbook();
                return;
            }

            if (target.type == OutdoorGameView::SpellbookPointerTargetType::QuickCastButton)
            {
                if (view.m_spellbook.selectedSpellId == 0
                    || view.m_pOutdoorPartyRuntime == nullptr
                    || view.m_pSpellTable == nullptr)
                {
                    view.setStatusBarEvent("Select spell");
                    return;
                }

                Character *pActiveMember = view.m_pOutdoorPartyRuntime->party().activeMember();
                const SpellEntry *pSpellEntry =
                    view.m_pSpellTable->findById(static_cast<int>(view.m_spellbook.selectedSpellId));

                if (pActiveMember == nullptr || pSpellEntry == nullptr)
                {
                    view.setStatusBarEvent("Can't set quick spell");
                    return;
                }

                if (!pActiveMember->knowsSpell(view.m_spellbook.selectedSpellId))
                {
                    view.setStatusBarEvent("Spell not learned");
                    return;
                }

                pActiveMember->quickSpellName = pSpellEntry->name;

                if (view.m_pGameAudioSystem != nullptr)
                {
                    view.m_pGameAudioSystem->playCommonSound(SoundId::ClickSkill, GameAudioSystem::PlaybackGroup::Ui);
                }

                view.playSpeechReaction(
                    view.m_pOutdoorPartyRuntime->party().activeMemberIndex(),
                    SpeechId::SetQuickSpell,
                    true);
                view.setStatusBarEvent("Quick spell set to " + pSpellEntry->name);
            }
        });
}

void GameplayPartyOverlayInputController::handleCharacterOverlayInput(
    OutdoorGameView &view,
    const bool *pKeyboardState,
    int screenWidth,
    int screenHeight)
{
    Character *pActiveCharacter = view.selectedCharacterScreenCharacter();
    Party *pParty = view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->party() : nullptr;
    const bool isAdventurersInnMode = view.isAdventurersInnScreenActive();
    const bool isReadOnlyAdventurersInnView = view.isReadOnlyAdventurersInnCharacterViewActive();
    const auto clearPendingCharacterDismiss =
        [&view]()
        {
            view.m_pendingCharacterDismissMemberIndex = std::nullopt;
            view.m_pendingCharacterDismissExpiresTicks = 0;
        };
    const uint64_t nowTicks = SDL_GetTicks();

    if (pParty == nullptr
        || view.isAdventurersInnCharacterSourceActive()
        || (view.m_pendingCharacterDismissMemberIndex.has_value()
            && (nowTicks > view.m_pendingCharacterDismissExpiresTicks
                || *view.m_pendingCharacterDismissMemberIndex >= pParty->members().size()
                || *view.m_pendingCharacterDismissMemberIndex != pParty->activeMemberIndex())))
    {
        clearPendingCharacterDismiss();
    }

    const CharacterDollEntry *pActiveCharacterDollEntry =
        resolveCharacterDollEntry(view.m_pCharacterDollTable, pActiveCharacter);
    const CharacterDollTypeEntry *pActiveCharacterDollType =
        pActiveCharacterDollEntry != nullptr && view.m_pCharacterDollTable != nullptr
            ? view.m_pCharacterDollTable->getDollType(pActiveCharacterDollEntry->dollTypeId)
            : nullptr;
    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pActiveCharacter, !isReadOnlyAdventurersInnView);
    const OutdoorGameView::HudFontHandle *pSkillRowFont = HudUiService::findHudFont(view, "Lucida");
    const float skillRowHeight = pSkillRowFont != nullptr
        ? static_cast<float>(std::max(1, pSkillRowFont->fontHeight - 3))
        : 11.0f;
    setCharacterSkillRegionHeight(
        view.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsWeaponsListRegion",
        skillUiData.weaponRows.size());
    setCharacterSkillRegionHeight(
        view.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsMagicListRegion",
        skillUiData.magicRows.size());
    setCharacterSkillRegionHeight(
        view.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsArmorListRegion",
        skillUiData.armorRows.size());
    setCharacterSkillRegionHeight(
        view.m_hudLayoutRuntimeHeightOverrides,
        skillRowHeight,
        "CharacterSkillsMiscListRegion",
        skillUiData.miscRows.size());

    const bool closePressed = pKeyboardState[SDL_SCANCODE_ESCAPE] || pKeyboardState[SDL_SCANCODE_E];
    const bool isInventorySpellTargetMode =
        view.m_utilitySpellOverlay.active
        && view.m_utilitySpellOverlay.mode == OutdoorGameView::UtilitySpellOverlayMode::InventoryTarget;

    if (closePressed)
    {
        if (!view.m_closeOverlayLatch)
        {
            if (isInventorySpellTargetMode)
            {
                view.m_gameplayUiController.closeUtilitySpellOverlay();
            }

            view.m_characterScreenOpen = false;
            view.m_characterDollJewelryOverlayOpen = false;
            view.m_adventurersInnRosterOverlayOpen = false;
            clearPendingCharacterDismiss();
            view.m_closeOverlayLatch = true;
        }
    }
    else
    {
        view.m_closeOverlayLatch = false;
    }

    if (isAdventurersInnMode)
    {
        constexpr size_t AdventurersInnVisibleColumns = 2;
        constexpr size_t AdventurersInnVisibleRows = 4;
        constexpr size_t AdventurersInnVisibleCount = AdventurersInnVisibleColumns * AdventurersInnVisibleRows;
        constexpr float HudReferenceWidth = 640.0f;
        constexpr float HudReferenceHeight = 480.0f;
        constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
        constexpr float PortraitX = 34.0f;
        constexpr float PortraitY = 47.0f;
        constexpr float PortraitWidth = 62.0f;
        constexpr float PortraitHeight = 72.0f;
        constexpr float PortraitGapX = 3.0f;
        constexpr float PortraitGapY = 3.0f;

        auto computeUiViewportRect = [](int width, int height) -> OutdoorGameView::ResolvedHudLayoutElement
        {
            OutdoorGameView::ResolvedHudLayoutElement viewport = {};
            viewport.width = static_cast<float>(width);
            viewport.height = static_cast<float>(height);
            viewport.scale = 1.0f;

            if (height > 0)
            {
                const float maxWidthForHeight = viewport.height * MaxUiViewportAspect;

                if (viewport.width > maxWidthForHeight)
                {
                    viewport.width = maxWidthForHeight;
                    viewport.x = (static_cast<float>(width) - viewport.width) * 0.5f;
                }
            }

            return viewport;
        };

        float mouseX = 0.0f;
        float mouseY = 0.0f;
        const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
        const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;
        const OutdoorGameView::ResolvedHudLayoutElement uiViewport = computeUiViewportRect(screenWidth, screenHeight);
        const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
        const Party *pParty = view.m_pOutdoorPartyRuntime != nullptr ? &view.m_pOutdoorPartyRuntime->party() : nullptr;
        const auto resolveLayoutRect =
            [&view, screenWidth, screenHeight](const char *pLayoutId)
                -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
            {
                const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, pLayoutId);

                if (pLayout == nullptr)
                {
                    return std::nullopt;
                }

                return HudUiService::resolveHudLayoutElement(
                    view,
                    pLayoutId,
                    screenWidth,
                    screenHeight,
                    pLayout->width,
                    pLayout->height);
            };
        const auto findInnPointerTarget =
            [&view,
             pParty,
             baseScale,
             uiViewport,
             &resolveLayoutRect](float pointerX, float pointerY) -> OutdoorGameView::CharacterPointerTarget
            {
                if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> exitRect =
                        resolveLayoutRect("AdventurersInnExitButton"))
                {
                    if (HudUiService::isPointerInsideResolvedElement(*exitRect, pointerX, pointerY))
                    {
                        return {OutdoorGameView::CharacterPointerTargetType::ExitButton};
                    }
                }

                if (pParty != nullptr && !pParty->isFull())
                {
                    if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> hireRect =
                            resolveLayoutRect("AdventurersInnHireButton"))
                    {
                        if (HudUiService::isPointerInsideResolvedElement(*hireRect, pointerX, pointerY))
                        {
                            return {OutdoorGameView::CharacterPointerTargetType::AdventurersInnHireButton};
                        }
                    }
                }

                if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> upRect =
                        resolveLayoutRect("AdventurersInnScrollUpButton"))
                {
                    if (HudUiService::isPointerInsideResolvedElement(*upRect, pointerX, pointerY))
                    {
                        return {OutdoorGameView::CharacterPointerTargetType::AdventurersInnScrollUpButton};
                    }
                }

                if (const std::optional<OutdoorGameView::ResolvedHudLayoutElement> downRect =
                        resolveLayoutRect("AdventurersInnScrollDownButton"))
                {
                    if (HudUiService::isPointerInsideResolvedElement(*downRect, pointerX, pointerY))
                    {
                        return {OutdoorGameView::CharacterPointerTargetType::AdventurersInnScrollDownButton};
                    }
                }

                if (pParty == nullptr)
                {
                    return {};
                }

                const std::vector<AdventurersInnMember> &innMembers = pParty->adventurersInnMembers();
                const size_t maximumScrollOffset =
                    innMembers.size() > AdventurersInnVisibleCount ? innMembers.size() - AdventurersInnVisibleCount : 0;
                const size_t scrollOffset = std::min(view.m_adventurersInnScrollOffset, maximumScrollOffset);

                for (size_t visibleIndex = 0; visibleIndex < AdventurersInnVisibleCount; ++visibleIndex)
                {
                    const size_t innIndex = scrollOffset + visibleIndex;

                    if (innIndex >= innMembers.size())
                    {
                        continue;
                    }

                    const size_t column = visibleIndex % AdventurersInnVisibleColumns;
                    const size_t row = visibleIndex / AdventurersInnVisibleColumns;
                    const float x =
                        uiViewport.x
                        + (PortraitX + static_cast<float>(column) * (PortraitWidth + PortraitGapX)) * baseScale;
                    const float y =
                        uiViewport.y
                        + (PortraitY + static_cast<float>(row) * (PortraitHeight + PortraitGapY)) * baseScale;
                    const float width = PortraitWidth * baseScale;
                    const float height = PortraitHeight * baseScale;

                    if (pointerX >= x && pointerX < x + width && pointerY >= y && pointerY < y + height)
                    {
                        OutdoorGameView::CharacterPointerTarget target = {};
                        target.type = OutdoorGameView::CharacterPointerTargetType::AdventurersInnPortrait;
                        target.innIndex = innIndex;
                        return target;
                    }
                }

                return {};
            };

        const HudPointerState pointerState = {mouseX, mouseY, isLeftMousePressed};
        const OutdoorGameView::CharacterPointerTarget noneCharacterTarget = {};
        handlePointerClickRelease(
            pointerState,
            view.m_characterClickLatch,
            view.m_characterPressedTarget,
            noneCharacterTarget,
            findInnPointerTarget,
            [&view](const OutdoorGameView::CharacterPointerTarget &target)
            {
                if (view.m_pOutdoorPartyRuntime == nullptr)
                {
                    return;
                }

                Party &party = view.m_pOutdoorPartyRuntime->party();
                const size_t innMemberCount = party.adventurersInnMembers().size();

                switch (target.type)
                {
                    case OutdoorGameView::CharacterPointerTargetType::ExitButton:
                        view.m_characterScreenOpen = false;
                        view.m_characterDollJewelryOverlayOpen = false;
                        view.m_adventurersInnRosterOverlayOpen = false;
                        break;

                    case OutdoorGameView::CharacterPointerTargetType::AdventurersInnPortrait:
                        if (target.innIndex < innMemberCount)
                        {
                            const uint64_t nowTicks = SDL_GetTicks();
                            const bool isDoubleClick =
                                view.m_lastAdventurersInnPortraitClickedIndex.has_value()
                                && *view.m_lastAdventurersInnPortraitClickedIndex == target.innIndex
                                && nowTicks >= view.m_lastAdventurersInnPortraitClickTicks
                                && nowTicks - view.m_lastAdventurersInnPortraitClickTicks <= PartyPortraitDoubleClickWindowMs;
                            view.m_characterScreenSourceIndex = target.innIndex;
                            view.m_lastAdventurersInnPortraitClickTicks = nowTicks;
                            view.m_lastAdventurersInnPortraitClickedIndex = target.innIndex;

                            if (isDoubleClick)
                            {
                                view.m_adventurersInnRosterOverlayOpen = false;
                                view.m_characterPage = OutdoorGameView::CharacterPage::Inventory;
                                view.m_characterDollJewelryOverlayOpen = false;
                            }
                        }

                        break;

                    case OutdoorGameView::CharacterPointerTargetType::AdventurersInnScrollUpButton:
                        if (view.m_adventurersInnScrollOffset > 0)
                        {
                            --view.m_adventurersInnScrollOffset;
                        }

                        break;

                    case OutdoorGameView::CharacterPointerTargetType::AdventurersInnScrollDownButton:
                    {
                        const size_t maximumScrollOffset =
                            innMemberCount > AdventurersInnVisibleCount ? innMemberCount - AdventurersInnVisibleCount : 0;

                        if (view.m_adventurersInnScrollOffset < maximumScrollOffset)
                        {
                            ++view.m_adventurersInnScrollOffset;
                        }

                        break;
                    }

                    case OutdoorGameView::CharacterPointerTargetType::AdventurersInnHireButton:
                    {
                        const AdventurersInnMember *pInnMember = party.adventurersInnMember(view.m_characterScreenSourceIndex);
                        const std::string memberName =
                            pInnMember != nullptr ? pInnMember->character.name : "Adventurer";

                        if (!party.hireAdventurersInnMember(view.m_characterScreenSourceIndex))
                        {
                            view.setStatusBarEvent("The party is full.");
                            break;
                        }

                        const size_t remainingCount = party.adventurersInnMembers().size();

                        if (remainingCount == 0)
                        {
                            view.m_characterScreenOpen = false;
                            view.m_characterDollJewelryOverlayOpen = false;
                            view.m_adventurersInnRosterOverlayOpen = false;
                        }
                        else
                        {
                            view.m_characterScreenSourceIndex = std::min(view.m_characterScreenSourceIndex, remainingCount - 1);
                            const size_t maximumScrollOffset =
                                remainingCount > AdventurersInnVisibleCount ? remainingCount - AdventurersInnVisibleCount : 0;
                            view.m_adventurersInnScrollOffset =
                                std::min(view.m_adventurersInnScrollOffset, maximumScrollOffset);
                        }

                        view.setStatusBarEvent(memberName + " joined the party.");

                        if (view.m_pGameAudioSystem != nullptr && view.m_pSpellTable != nullptr)
                        {
                            const SpellEntry *pSpellEntry =
                                view.m_pSpellTable->findById(spellIdValue(SpellId::Heroism));

                            if (pSpellEntry != nullptr && pSpellEntry->effectSoundId > 0)
                            {
                                view.m_pGameAudioSystem->playSound(
                                    static_cast<uint32_t>(pSpellEntry->effectSoundId),
                                    GameAudioSystem::PlaybackGroup::Ui);
                            }
                        }

                        break;
                    }

                    default:
                        break;
                }
            });
        return;
    }

    const SDL_Scancode charCycleScancode = view.m_gameSettings.keyboard.binding(KeyboardAction::CharCycle);
    const bool charCyclePressed =
        pKeyboardState != nullptr
        && charCycleScancode > SDL_SCANCODE_UNKNOWN
        && charCycleScancode < SDL_SCANCODE_COUNT
        && pKeyboardState[charCycleScancode];
    const bool charCycleNewlyPressed =
        charCyclePressed && view.m_previousKeyboardState[charCycleScancode] == 0;

    if (charCycleNewlyPressed)
    {
        if (view.m_pOutdoorPartyRuntime != nullptr)
        {
            const std::vector<Character> &members = view.m_pOutdoorPartyRuntime->party().members();

            if (!members.empty())
            {
                const size_t nextMemberIndex =
                    (view.m_pOutdoorPartyRuntime->party().activeMemberIndex() + 1) % members.size();
                view.trySelectPartyMember(nextMemberIndex, false);
            }

            view.m_characterMemberCycleLatch = true;
        }
    }
    else
    {
        view.m_characterMemberCycleLatch = false;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);
    const bool isLeftMousePressed = (mouseButtons & SDL_BUTTON_LMASK) != 0;

    const auto resolveCharacterInventoryGrid =
        [&view, screenWidth, screenHeight]() -> std::optional<OutdoorGameView::ResolvedHudLayoutElement>
        {
            const OutdoorGameView::HudLayoutElement *pInventoryGridLayout = HudUiService::findHudLayoutElement(view, "CharacterInventoryGrid");

            if (pInventoryGridLayout == nullptr)
            {
                return std::nullopt;
            }

            return HudUiService::resolveHudLayoutElement(view, 
                "CharacterInventoryGrid",
                screenWidth,
                screenHeight,
                pInventoryGridLayout->width,
                pInventoryGridLayout->height);
        };

    const auto findCharacterPointerTarget =
        [&view,
         screenWidth,
         screenHeight,
         skillRowHeight,
         &skillUiData,
         isReadOnlyAdventurersInnView,
         pActiveCharacter,
         pActiveCharacterDollType,
         &resolveCharacterInventoryGrid](
            float pointerX,
            float pointerY) -> OutdoorGameView::CharacterPointerTarget
        {
            if (screenWidth <= 0 || screenHeight <= 0)
            {
                return {};
            }

            struct CharacterTabTarget
            {
                const char *layoutId;
                OutdoorGameView::CharacterPage page;
            };

            static constexpr CharacterTabTarget TabTargets[] = {
                {"CharacterStatsButton", OutdoorGameView::CharacterPage::Stats},
                {"CharacterSkillsButton", OutdoorGameView::CharacterPage::Skills},
                {"CharacterInventoryButton", OutdoorGameView::CharacterPage::Inventory},
                {"CharacterAwardsButton", OutdoorGameView::CharacterPage::Awards},
            };

            for (const CharacterTabTarget &target : TabTargets)
            {
                const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, target.layoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
                    target.layoutId,
                    screenWidth,
                    screenHeight,
                    pLayout->width,
                    pLayout->height);

                if (resolved
                    && pointerX >= resolved->x
                    && pointerX < resolved->x + resolved->width
                    && pointerY >= resolved->y
                    && pointerY < resolved->y + resolved->height)
                {
                    return {OutdoorGameView::CharacterPointerTargetType::PageButton, target.page};
                }
            }

            if (!view.isAdventurersInnCharacterSourceActive() && view.m_pOutdoorPartyRuntime != nullptr)
            {
                const size_t activeMemberIndex = view.m_pOutdoorPartyRuntime->party().activeMemberIndex();

                if (activeMemberIndex > 0)
                {
                    const OutdoorGameView::HudLayoutElement *pDismissLayout =
                        HudUiService::findHudLayoutElement(view, "CharacterDismissButton");

                    if (pDismissLayout != nullptr)
                    {
                        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                            HudUiService::resolveHudLayoutElement(
                                view,
                                "CharacterDismissButton",
                                screenWidth,
                                screenHeight,
                                pDismissLayout->width,
                                pDismissLayout->height);

                        if (resolved
                            && pointerX >= resolved->x
                            && pointerX < resolved->x + resolved->width
                            && pointerY >= resolved->y
                            && pointerY < resolved->y + resolved->height)
                        {
                            return {
                                OutdoorGameView::CharacterPointerTargetType::DismissButton,
                                OutdoorGameView::CharacterPage::Inventory
                            };
                        }
                    }
                }
            }

            const OutdoorGameView::HudLayoutElement *pExitLayout = HudUiService::findHudLayoutElement(view, "CharacterExitButton");

            if (pExitLayout != nullptr)
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
                    "CharacterExitButton",
                    screenWidth,
                    screenHeight,
                    pExitLayout->width,
                    pExitLayout->height);

                if (resolved
                    && pointerX >= resolved->x
                    && pointerX < resolved->x + resolved->width
                    && pointerY >= resolved->y
                    && pointerY < resolved->y + resolved->height)
                {
                    return {OutdoorGameView::CharacterPointerTargetType::ExitButton, OutdoorGameView::CharacterPage::Inventory};
                }
            }

            const OutdoorGameView::HudLayoutElement *pMagnifyLayout = HudUiService::findHudLayoutElement(view, "CharacterMagnifyButton");

            if (pMagnifyLayout != nullptr)
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = HudUiService::resolveHudLayoutElement(view, 
                    "CharacterMagnifyButton",
                    screenWidth,
                    screenHeight,
                    pMagnifyLayout->width,
                    pMagnifyLayout->height);

                if (resolved
                    && pointerX >= resolved->x
                    && pointerX < resolved->x + resolved->width
                    && pointerY >= resolved->y
                    && pointerY < resolved->y + resolved->height)
                {
                    return {OutdoorGameView::CharacterPointerTargetType::MagnifyButton, OutdoorGameView::CharacterPage::Inventory};
                }
            }

            if (!view.m_heldInventoryItem.active)
            {
                for (auto it = view.m_renderedInspectableHudItems.rbegin(); it != view.m_renderedInspectableHudItems.rend(); ++it)
                {
                    if (it->sourceType != OutdoorGameView::ItemInspectSourceType::Equipment
                        || !isVisibleInCharacterDollOverlay(it->equipmentSlot, view.m_characterDollJewelryOverlayOpen))
                    {
                        continue;
                    }

                    if (!view.isOpaqueHudPixelAtPoint(*it, pointerX, pointerY))
                    {
                        continue;
                    }

                    OutdoorGameView::CharacterPointerTarget pointerTarget = {};
                    pointerTarget.type = OutdoorGameView::CharacterPointerTargetType::EquipmentSlot;
                    pointerTarget.page = view.m_characterPage;
                    pointerTarget.equipmentSlot = it->equipmentSlot;
                    return pointerTarget;
                }
            }

            struct CharacterEquipmentSlotTarget
            {
                const char *layoutId;
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
                if (!isVisibleInCharacterDollOverlay(target.slot, view.m_characterDollJewelryOverlayOpen))
                {
                    continue;
                }

                if (view.m_heldInventoryItem.active && !target.jewelryOverlayOnly)
                {
                    continue;
                }

                const OutdoorGameView::HudLayoutElement *pLayout = HudUiService::findHudLayoutElement(view, target.layoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const uint32_t equippedId =
                    pActiveCharacter != nullptr ? equippedItemId(pActiveCharacter->equipment, target.slot) : 0;
                const ItemDefinition *pItemDefinition =
                    equippedId != 0 && view.m_pItemTable != nullptr ? view.m_pItemTable->get(equippedId) : nullptr;
                std::optional<OutdoorGameView::ResolvedHudLayoutElement> dynamicRect;
                std::string dynamicTextureName;

                if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
                {
                    const bool hasRightHandWeapon =
                        pActiveCharacter != nullptr && pActiveCharacter->equipment.mainHand != 0;
                    const uint32_t dollTypeId =
                        pActiveCharacterDollType != nullptr ? pActiveCharacterDollType->id : 0;
                    dynamicTextureName = view.resolveEquippedItemHudTextureName(
                        *pItemDefinition,
                        dollTypeId,
                        hasRightHandWeapon,
                        target.slot);
                    const OutdoorGameView::HudTextureHandle *pTexture = HudUiService::ensureHudTextureLoaded(view, dynamicTextureName);

                    if (pTexture != nullptr)
                    {
                        dynamicRect = view.resolveCharacterEquipmentRenderRect(
                            *pLayout,
                            *pItemDefinition,
                            *pTexture,
                            pActiveCharacterDollType,
                            target.slot,
                            screenWidth,
                            screenHeight);
                    }
                }

                bool pointerInsideDynamicRect = false;

                if (dynamicRect)
                {
                    if (view.m_heldInventoryItem.active)
                    {
                        pointerInsideDynamicRect =
                            pointerX >= dynamicRect->x
                            && pointerX < dynamicRect->x + dynamicRect->width
                            && pointerY >= dynamicRect->y
                            && pointerY < dynamicRect->y + dynamicRect->height;
                    }
                    else if (!dynamicTextureName.empty() && pItemDefinition != nullptr)
                    {
                        OutdoorGameView::RenderedInspectableHudItem renderedItem = {};
                        renderedItem.objectDescriptionId = pItemDefinition->itemId;
                        renderedItem.textureName = dynamicTextureName;
                        renderedItem.x = dynamicRect->x;
                        renderedItem.y = dynamicRect->y;
                        renderedItem.width = dynamicRect->width;
                        renderedItem.height = dynamicRect->height;
                        pointerInsideDynamicRect = view.isOpaqueHudPixelAtPoint(renderedItem, pointerX, pointerY);
                    }
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved =
                    view.m_heldInventoryItem.active && !dynamicRect
                        ? HudUiService::resolveHudLayoutElement(view, 
                            target.layoutId,
                            screenWidth,
                            screenHeight,
                            pLayout->width,
                            pLayout->height)
                        : std::nullopt;
                const bool pointerInsideLayoutRect =
                    resolved
                    && pointerX >= resolved->x
                    && pointerX < resolved->x + resolved->width
                    && pointerY >= resolved->y
                    && pointerY < resolved->y + resolved->height;

                if (!pointerInsideDynamicRect && !pointerInsideLayoutRect)
                {
                    continue;
                }

                if ((!isReadOnlyAdventurersInnView && view.m_heldInventoryItem.active)
                    || (pActiveCharacter != nullptr && equippedItemId(pActiveCharacter->equipment, target.slot) != 0))
                {
                    if (isReadOnlyAdventurersInnView)
                    {
                        continue;
                    }

                    OutdoorGameView::CharacterPointerTarget pointerTarget = {};
                    pointerTarget.type = OutdoorGameView::CharacterPointerTargetType::EquipmentSlot;
                    pointerTarget.page = view.m_characterPage;
                    pointerTarget.equipmentSlot = target.slot;
                    return pointerTarget;
                }
            }

            if (!isReadOnlyAdventurersInnView && view.m_heldInventoryItem.active)
            {
                const OutdoorGameView::HudLayoutElement *pDollLayout = HudUiService::findHudLayoutElement(view, "CharacterDollPanel");

                if (pDollLayout != nullptr)
                {
                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedDoll = HudUiService::resolveHudLayoutElement(view, 
                        "CharacterDollPanel",
                        screenWidth,
                        screenHeight,
                        pDollLayout->width,
                        pDollLayout->height);

                    if (resolvedDoll
                        && pointerX >= resolvedDoll->x
                        && pointerX < resolvedDoll->x + resolvedDoll->width
                        && pointerY >= resolvedDoll->y
                        && pointerY < resolvedDoll->y + resolvedDoll->height)
                    {
                        return {OutdoorGameView::CharacterPointerTargetType::DollPanel, view.m_characterPage};
                    }
                }
            }

            if (view.m_characterPage == OutdoorGameView::CharacterPage::Inventory)
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedInventoryGrid =
                    resolveCharacterInventoryGrid();

                if (resolvedInventoryGrid
                    && pointerX >= resolvedInventoryGrid->x
                    && pointerX < resolvedInventoryGrid->x + resolvedInventoryGrid->width
                    && pointerY >= resolvedInventoryGrid->y
                    && pointerY < resolvedInventoryGrid->y + resolvedInventoryGrid->height)
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

                    if (!isReadOnlyAdventurersInnView && view.m_heldInventoryItem.active)
                    {
                        OutdoorGameView::CharacterPointerTarget target = {};
                        target.type = OutdoorGameView::CharacterPointerTargetType::InventoryCell;
                        target.page = OutdoorGameView::CharacterPage::Inventory;
                        target.gridX = gridX;
                        target.gridY = gridY;
                        return target;
                    }

                    if (pActiveCharacter != nullptr)
                    {
                        const InventoryItem *pItem = pActiveCharacter->inventoryItemAt(gridX, gridY);

                        if (pItem != nullptr)
                        {
                            if (!isReadOnlyAdventurersInnView)
                            {
                                OutdoorGameView::CharacterPointerTarget target = {};
                                target.type = OutdoorGameView::CharacterPointerTargetType::InventoryItem;
                                target.page = OutdoorGameView::CharacterPage::Inventory;
                                target.gridX = pItem->gridX;
                                target.gridY = pItem->gridY;
                                return target;
                            }
                        }
                    }
                }
            }

            if (view.m_characterPage == OutdoorGameView::CharacterPage::Skills)
            {
                const auto findSkillRowTarget =
                    [&view, screenWidth, screenHeight, pointerX, pointerY, skillRowHeight](
                        const char *pRegionId,
                        const char *pLevelHeaderId,
                        const std::vector<CharacterSkillUiRow> &rows) -> OutdoorGameView::CharacterPointerTarget
                    {
                        if (rows.empty())
                        {
                            return {};
                        }

                        const OutdoorGameView::HudLayoutElement *pRegionLayout = HudUiService::findHudLayoutElement(view, pRegionId);
                        const OutdoorGameView::HudLayoutElement *pLevelLayout = HudUiService::findHudLayoutElement(view, pLevelHeaderId);

                        if (pRegionLayout == nullptr || pLevelLayout == nullptr)
                        {
                            return {};
                        }

                        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedRegion = HudUiService::resolveHudLayoutElement(view, 
                            pRegionId,
                            screenWidth,
                            screenHeight,
                            pRegionLayout->width,
                            pRegionLayout->height);
                        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedLevelHeader = HudUiService::resolveHudLayoutElement(view, 
                            pLevelHeaderId,
                            screenWidth,
                            screenHeight,
                            pLevelLayout->width,
                            pLevelLayout->height);

                        if (!resolvedRegion || !resolvedLevelHeader)
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
                                OutdoorGameView::CharacterPointerTarget target = {};
                                target.type = OutdoorGameView::CharacterPointerTargetType::SkillRow;
                                target.page = OutdoorGameView::CharacterPage::Skills;
                                target.skillName = row.canonicalName;
                                return target;
                            }
                        }

                        return {};
                    };

                const OutdoorGameView::CharacterPointerTarget weaponTarget =
                    findSkillRowTarget("CharacterSkillsWeaponsListRegion", "CharacterSkillsWeaponsLevelHeader", skillUiData.weaponRows);

                if (weaponTarget.type == OutdoorGameView::CharacterPointerTargetType::SkillRow)
                {
                    return weaponTarget;
                }

                const OutdoorGameView::CharacterPointerTarget magicTarget =
                    findSkillRowTarget("CharacterSkillsMagicListRegion", "CharacterSkillsMagicLevelHeader", skillUiData.magicRows);

                if (magicTarget.type == OutdoorGameView::CharacterPointerTargetType::SkillRow)
                {
                    return magicTarget;
                }

                const OutdoorGameView::CharacterPointerTarget armorTarget =
                    findSkillRowTarget("CharacterSkillsArmorListRegion", "CharacterSkillsArmorLevelHeader", skillUiData.armorRows);

                if (armorTarget.type == OutdoorGameView::CharacterPointerTargetType::SkillRow)
                {
                    return armorTarget;
                }

                const OutdoorGameView::CharacterPointerTarget miscTarget =
                    findSkillRowTarget("CharacterSkillsMiscListRegion", "CharacterSkillsMiscLevelHeader", skillUiData.miscRows);

                if (miscTarget.type == OutdoorGameView::CharacterPointerTargetType::SkillRow)
                {
                    return miscTarget;
                }
            }

            return {};
        };

    const HudPointerState pointerState = {
        mouseX,
        mouseY,
        isLeftMousePressed
    };
    const OutdoorGameView::CharacterPointerTarget noneCharacterTarget = {};
    const OutdoorGameView::CharacterPointerTarget hoveredCharacterTarget = findCharacterPointerTarget(mouseX, mouseY);

    if (view.m_pOutdoorPartyRuntime != nullptr)
    {
        view.updateReadableScrollOverlayForHeldItem(
            view.m_pOutdoorPartyRuntime->party().activeMemberIndex(),
            hoveredCharacterTarget,
            isLeftMousePressed);
    }
    else
    {
        view.closeReadableScrollOverlay();
    }

    handlePointerClickRelease(
        pointerState,
        view.m_characterClickLatch,
        view.m_characterPressedTarget,
        noneCharacterTarget,
        findCharacterPointerTarget,
        [&view,
         screenWidth,
         screenHeight,
         mouseX,
         mouseY,
         &clearPendingCharacterDismiss,
         &resolveCharacterInventoryGrid,
         pActiveCharacterDollType,
         isReadOnlyAdventurersInnView](
            const OutdoorGameView::CharacterPointerTarget &target)
        {
            const bool isInventorySpellTargetMode =
                view.m_utilitySpellOverlay.active
                && view.m_utilitySpellOverlay.mode == OutdoorGameView::UtilitySpellOverlayMode::InventoryTarget;
            const auto resolveItemLogName =
                [&view](uint32_t objectDescriptionId) -> std::string
                {
                    const ItemDefinition *pItemDefinition =
                        view.m_pItemTable != nullptr ? view.m_pItemTable->get(objectDescriptionId) : nullptr;

                    if (pItemDefinition == nullptr || pItemDefinition->name.empty())
                    {
                        return std::to_string(objectDescriptionId);
                    }

                    return pItemDefinition->name;
                };

            const auto logCharacterItemAction =
                [&view, &resolveItemLogName](const char *pAction, uint32_t objectDescriptionId, const std::string &detail)
                {
                    const size_t memberIndex =
                        view.m_pOutdoorPartyRuntime != nullptr ? view.m_pOutdoorPartyRuntime->party().activeMemberIndex() : 0;
                    std::cout << "Character item " << pAction
                              << ": member=" << memberIndex
                              << " item=\"" << resolveItemLogName(objectDescriptionId) << "\"";

                    if (!detail.empty())
                    {
                        std::cout << " " << detail;
                    }

                    std::cout << '\n';
                };

            const auto setHeldItem =
                [&view](const InventoryItem &item)
                {
                    view.m_heldInventoryItem.active = true;
                    view.m_heldInventoryItem.item = item;
                    view.m_heldInventoryItem.grabCellOffsetX = 0;
                    view.m_heldInventoryItem.grabCellOffsetY = 0;
                    view.m_heldInventoryItem.grabOffsetX = 0.0f;
                    view.m_heldInventoryItem.grabOffsetY = 0.0f;
                };

            if (target.type != OutdoorGameView::CharacterPointerTargetType::DismissButton)
            {
                clearPendingCharacterDismiss();
            }

            if (isInventorySpellTargetMode)
            {
                if (target.type == OutdoorGameView::CharacterPointerTargetType::InventoryItem)
                {
                    PartySpellCastRequest request = {};
                    request.casterMemberIndex = view.m_utilitySpellOverlay.casterMemberIndex;
                    request.spellId = view.m_utilitySpellOverlay.spellId;
                    request.targetItemMemberIndex =
                        view.m_pOutdoorPartyRuntime != nullptr
                            ? std::optional<size_t>(view.m_pOutdoorPartyRuntime->party().activeMemberIndex())
                            : std::nullopt;
                    request.targetInventoryGridX = target.gridX;
                    request.targetInventoryGridY = target.gridY;

                    const SpellEntry *pSpellEntry =
                        view.m_pSpellTable != nullptr
                            ? view.m_pSpellTable->findById(static_cast<int>(request.spellId))
                            : nullptr;
                    const std::string spellName =
                        pSpellEntry != nullptr && !pSpellEntry->name.empty()
                            ? pSpellEntry->name
                            : "Spell";
                    view.tryCastSpellRequest(request, spellName);
                    return;
                }

                if (target.type == OutdoorGameView::CharacterPointerTargetType::EquipmentSlot)
                {
                    PartySpellCastRequest request = {};
                    request.casterMemberIndex = view.m_utilitySpellOverlay.casterMemberIndex;
                    request.spellId = view.m_utilitySpellOverlay.spellId;
                    request.targetItemMemberIndex =
                        view.m_pOutdoorPartyRuntime != nullptr
                            ? std::optional<size_t>(view.m_pOutdoorPartyRuntime->party().activeMemberIndex())
                            : std::nullopt;
                    request.targetEquipmentSlot = target.equipmentSlot;

                    const SpellEntry *pSpellEntry =
                        view.m_pSpellTable != nullptr
                            ? view.m_pSpellTable->findById(static_cast<int>(request.spellId))
                            : nullptr;
                    const std::string spellName =
                        pSpellEntry != nullptr && !pSpellEntry->name.empty()
                            ? pSpellEntry->name
                            : "Spell";
                    view.tryCastSpellRequest(request, spellName);
                    return;
                }
            }

            if (target.type == OutdoorGameView::CharacterPointerTargetType::PageButton)
            {
                if (isInventorySpellTargetMode && target.page != OutdoorGameView::CharacterPage::Inventory)
                {
                    view.setStatusBarEvent("Select an item");
                    return;
                }

                if (view.m_characterPage != target.page)
                {
                    view.m_characterPage = target.page;

                    if (view.m_pGameAudioSystem != nullptr)
                    {
                        view.m_pGameAudioSystem->playCommonSound(SoundId::ClickIn, GameAudioSystem::PlaybackGroup::Ui);
                    }
                }
            }
            else if (target.type == OutdoorGameView::CharacterPointerTargetType::ExitButton)
            {
                if (isInventorySpellTargetMode)
                {
                    view.m_gameplayUiController.closeUtilitySpellOverlay();
                }

                if (isReadOnlyAdventurersInnView)
                {
                    view.m_characterDollJewelryOverlayOpen = false;
                    view.m_adventurersInnRosterOverlayOpen = true;
                }
                else
                {
                    view.m_characterScreenOpen = false;
                    view.m_characterDollJewelryOverlayOpen = false;
                    view.m_adventurersInnRosterOverlayOpen = false;
                }
            }
            else if (target.type == OutdoorGameView::CharacterPointerTargetType::DismissButton
                && view.m_pOutdoorPartyRuntime != nullptr)
            {
                Party &party = view.m_pOutdoorPartyRuntime->party();
                const size_t memberIndex = party.activeMemberIndex();
                const Character *pMember = party.member(memberIndex);

                if (pMember == nullptr || memberIndex == 0)
                {
                    clearPendingCharacterDismiss();
                    return;
                }

                const bool confirmed =
                    view.m_pendingCharacterDismissMemberIndex.has_value()
                    && *view.m_pendingCharacterDismissMemberIndex == memberIndex
                    && SDL_GetTicks() <= view.m_pendingCharacterDismissExpiresTicks;

                if (!confirmed)
                {
                    const uint64_t dismissClickTicks = SDL_GetTicks();
                    view.m_pendingCharacterDismissMemberIndex = memberIndex;
                    view.m_pendingCharacterDismissExpiresTicks = dismissClickTicks + CharacterDismissConfirmWindowMs;
                    view.setStatusBarEvent(
                        "To confirm " + pMember->name + " dismissal press the button again...",
                        2.0f);

                    if (view.m_pGameAudioSystem != nullptr)
                    {
                        view.m_pGameAudioSystem->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                    }
                }
                else
                {
                    const std::string dismissedName = pMember->name;
                    clearPendingCharacterDismiss();

                    if (party.dismissMemberToAdventurersInn(memberIndex))
                    {
                        view.m_characterDollJewelryOverlayOpen = false;
                        view.setStatusBarEvent(dismissedName + " dismissed.");
                    }
                    else
                    {
                        view.setStatusBarEvent("Dismissal failed.");
                    }
                }
            }
            else if (target.type == OutdoorGameView::CharacterPointerTargetType::MagnifyButton)
            {
                view.m_characterDollJewelryOverlayOpen = !view.m_characterDollJewelryOverlayOpen;
            }
            else if (target.type == OutdoorGameView::CharacterPointerTargetType::SkillRow
                && view.m_pOutdoorPartyRuntime != nullptr)
            {
                if (view.m_pOutdoorPartyRuntime->party().increaseActiveMemberSkillLevel(target.skillName))
                {
                    if (view.m_pGameAudioSystem != nullptr)
                    {
                        view.m_pGameAudioSystem->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
                    }

                    view.playSpeechReaction(
                        view.m_pOutdoorPartyRuntime->party().activeMemberIndex(),
                        SpeechId::SkillIncreased,
                        true);
                }
            }
            else if (target.type == OutdoorGameView::CharacterPointerTargetType::InventoryItem
                && view.m_pOutdoorPartyRuntime != nullptr)
            {
                Party &party = view.m_pOutdoorPartyRuntime->party();
                InventoryItem heldItem = {};

                if (party.takeItemFromMemberInventoryCell(party.activeMemberIndex(), target.gridX, target.gridY, heldItem))
                {
                    setHeldItem(heldItem);
                    logCharacterItemAction(
                        "picked_up",
                        heldItem.objectDescriptionId,
                        "source=inventory cell=(" + std::to_string(target.gridX) + "," + std::to_string(target.gridY) + ")");

                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedInventoryGrid =
                        resolveCharacterInventoryGrid();

                    if (resolvedInventoryGrid)
                    {
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
                        view.m_heldInventoryItem.grabCellOffsetX = hoveredGridX - heldItem.gridX;
                        view.m_heldInventoryItem.grabCellOffsetY = hoveredGridY - heldItem.gridY;
                        const ItemDefinition *pItemDefinition =
                            view.m_pItemTable != nullptr ? view.m_pItemTable->get(heldItem.objectDescriptionId) : nullptr;

                        if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
                        {
                            const OutdoorGameView::HudTextureHandle *pItemTexture =
                                HudUiService::ensureHudTextureLoaded(view, pItemDefinition->iconName);

                            if (pItemTexture != nullptr)
                            {
                                const float itemWidth = static_cast<float>(pItemTexture->width) * gridMetrics.scale;
                                const float itemHeight = static_cast<float>(pItemTexture->height) * gridMetrics.scale;
                                const InventoryItemScreenRect itemRect =
                                    computeInventoryItemScreenRect(gridMetrics, heldItem, itemWidth, itemHeight);
                                view.m_heldInventoryItem.grabOffsetX = mouseX - itemRect.x;
                                view.m_heldInventoryItem.grabOffsetY = mouseY - itemRect.y;
                            }
                        }
                    }
                }
            }
            else if (target.type == OutdoorGameView::CharacterPointerTargetType::EquipmentSlot
                && view.m_pOutdoorPartyRuntime != nullptr)
            {
                Party &party = view.m_pOutdoorPartyRuntime->party();

                if (!view.m_heldInventoryItem.active)
                {
                    InventoryItem unequippedItem = {};

                    if (party.takeEquippedItemFromMember(party.activeMemberIndex(), target.equipmentSlot, unequippedItem))
                    {
                        setHeldItem(unequippedItem);
                        logCharacterItemAction(
                            "removed_from_doll",
                            unequippedItem.objectDescriptionId,
                            "slot=" + std::string(equipmentSlotName(target.equipmentSlot)));
                    }

                    return;
                }

                if (view.m_pItemTable != nullptr)
                {
                    const InventoryItemUseAction useAction =
                        InventoryItemUseRuntime::classifyItemUse(view.m_heldInventoryItem.item, *view.m_pItemTable);

                    if (useAction == InventoryItemUseAction::ReadMessageScroll)
                    {
                        return;
                    }

                    if (useAction != InventoryItemUseAction::None && useAction != InventoryItemUseAction::Equip)
                    {
                        view.tryUseHeldItemOnPartyMember(party.activeMemberIndex(), true);
                        return;
                    }
                }

                const ItemDefinition *pItemDefinition =
                    view.m_pItemTable != nullptr
                        ? view.m_pItemTable->get(view.m_heldInventoryItem.item.objectDescriptionId)
                        : nullptr;

                if (pItemDefinition == nullptr)
                {
                    return;
                }

                const std::optional<CharacterEquipPlan> plan =
                    GameMechanics::resolveCharacterEquipPlan(
                        *party.activeMember(),
                        *pItemDefinition,
                        view.m_pItemTable,
                        pActiveCharacterDollType,
                        target.equipmentSlot,
                        false);

                if (!plan)
                {
                    logCharacterItemAction(
                        "equip_rejected",
                        view.m_heldInventoryItem.item.objectDescriptionId,
                        "target=" + std::string(equipmentSlotName(target.equipmentSlot)));
                    view.setStatusBarEvent("Can't equip that item there");
                    return;
                }

                std::optional<InventoryItem> heldReplacement;

                if (!party.tryEquipItemOnMember(
                        party.activeMemberIndex(),
                        plan->targetSlot,
                        view.m_heldInventoryItem.item,
                        plan->displacedSlot,
                        plan->autoStoreDisplacedItem,
                        heldReplacement))
                {
                    logCharacterItemAction(
                        "equip_failed",
                        view.m_heldInventoryItem.item.objectDescriptionId,
                        "target=" + std::string(equipmentSlotName(plan->targetSlot)) + " reason=\"" + party.lastStatus() + "\"");
                    view.setStatusBarEvent(party.lastStatus().empty() ? "Can't equip that item" : party.lastStatus());
                    return;
                }

                logCharacterItemAction(
                    "placed_on_doll",
                    view.m_heldInventoryItem.item.objectDescriptionId,
                    "slot=" + std::string(equipmentSlotName(plan->targetSlot)));

                if (heldReplacement)
                {
                    setHeldItem(*heldReplacement);
                }
                else
                {
                    view.m_heldInventoryItem = {};
                }
            }
            else if (target.type == OutdoorGameView::CharacterPointerTargetType::InventoryCell
                && view.m_pOutdoorPartyRuntime != nullptr
                && view.m_heldInventoryItem.active)
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedInventoryGrid =
                    resolveCharacterInventoryGrid();

                if (!resolvedInventoryGrid)
                {
                    return;
                }

                const ItemDefinition *pItemDefinition =
                    view.m_pItemTable != nullptr
                        ? view.m_pItemTable->get(view.m_heldInventoryItem.item.objectDescriptionId)
                        : nullptr;

                if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
                {
                    return;
                }

                const OutdoorGameView::HudTextureHandle *pItemTexture = HudUiService::ensureHudTextureLoaded(view, pItemDefinition->iconName);

                if (pItemTexture == nullptr)
                {
                    return;
                }

                const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                    resolvedInventoryGrid->x,
                    resolvedInventoryGrid->y,
                    resolvedInventoryGrid->width,
                    resolvedInventoryGrid->height,
                    resolvedInventoryGrid->scale);
                const float itemWidth = static_cast<float>(pItemTexture->width) * gridMetrics.scale;
                const float itemHeight = static_cast<float>(pItemTexture->height) * gridMetrics.scale;
                const float drawX = mouseX - view.m_heldInventoryItem.grabOffsetX;
                const float drawY = mouseY - view.m_heldInventoryItem.grabOffsetY;
                const std::optional<std::pair<int, int>> placement =
                    computeHeldInventoryPlacement(
                        gridMetrics,
                        view.m_heldInventoryItem.item.width,
                        view.m_heldInventoryItem.item.height,
                        itemWidth,
                        itemHeight,
                        drawX,
                        drawY);

                if (!placement)
                {
                    return;
                }

                const int destinationGridX = placement->first;
                const int destinationGridY = placement->second;

                if (destinationGridX < 0
                    || destinationGridY < 0
                    || destinationGridX >= Character::InventoryWidth
                    || destinationGridY >= Character::InventoryHeight)
                {
                    return;
                }

                Party &party = view.m_pOutdoorPartyRuntime->party();
                std::optional<InventoryItem> replacedItem;

                if (party.tryPlaceItemInMemberInventoryCell(
                        party.activeMemberIndex(),
                        view.m_heldInventoryItem.item,
                        static_cast<uint8_t>(destinationGridX),
                        static_cast<uint8_t>(destinationGridY),
                        replacedItem))
                {
                    if (replacedItem)
                    {
                        view.m_heldInventoryItem.item = *replacedItem;
                        view.m_heldInventoryItem.grabCellOffsetX = 0;
                        view.m_heldInventoryItem.grabCellOffsetY = 0;
                        view.m_heldInventoryItem.grabOffsetX = 0.0f;
                        view.m_heldInventoryItem.grabOffsetY = 0.0f;
                    }
                    else
                    {
                        view.m_heldInventoryItem = {};
                    }
                }
            }
            else if (target.type == OutdoorGameView::CharacterPointerTargetType::DollPanel
                && view.m_heldInventoryItem.active)
            {
                if (view.m_pOutdoorPartyRuntime == nullptr)
                {
                    return;
                }

                Party &party = view.m_pOutdoorPartyRuntime->party();

                if (view.m_pItemTable != nullptr)
                {
                    const InventoryItemUseAction useAction =
                        InventoryItemUseRuntime::classifyItemUse(view.m_heldInventoryItem.item, *view.m_pItemTable);

                    if (useAction == InventoryItemUseAction::ReadMessageScroll)
                    {
                        return;
                    }

                    if (useAction != InventoryItemUseAction::None && useAction != InventoryItemUseAction::Equip)
                    {
                        view.tryUseHeldItemOnPartyMember(party.activeMemberIndex(), true);
                        return;
                    }
                }

                const ItemDefinition *pItemDefinition =
                    view.m_pItemTable != nullptr
                        ? view.m_pItemTable->get(view.m_heldInventoryItem.item.objectDescriptionId)
                        : nullptr;

                if (pItemDefinition == nullptr)
                {
                    return;
                }

                const OutdoorGameView::HudLayoutElement *pDollLayout = HudUiService::findHudLayoutElement(view, "CharacterDollPanel");
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedDoll = pDollLayout != nullptr
                    ? HudUiService::resolveHudLayoutElement(view, 
                        "CharacterDollPanel",
                        screenWidth,
                        screenHeight,
                        pDollLayout->width,
                        pDollLayout->height)
                    : std::nullopt;
                const bool preferOffHand =
                    resolvedDoll && mouseX >= resolvedDoll->x + resolvedDoll->width * 0.5f;
                const std::optional<CharacterEquipPlan> plan =
                    GameMechanics::resolveCharacterEquipPlan(
                        *party.activeMember(),
                        *pItemDefinition,
                        view.m_pItemTable,
                        pActiveCharacterDollType,
                        std::nullopt,
                        preferOffHand);

                if (!plan)
                {
                    logCharacterItemAction(
                        "equip_rejected",
                        view.m_heldInventoryItem.item.objectDescriptionId,
                        "target=auto");
                    view.setStatusBarEvent("Can't equip that item");
                    return;
                }

                std::optional<InventoryItem> heldReplacement;

                if (!party.tryEquipItemOnMember(
                        party.activeMemberIndex(),
                        plan->targetSlot,
                        view.m_heldInventoryItem.item,
                        plan->displacedSlot,
                        plan->autoStoreDisplacedItem,
                        heldReplacement))
                {
                    logCharacterItemAction(
                        "equip_failed",
                        view.m_heldInventoryItem.item.objectDescriptionId,
                        "target=" + std::string(equipmentSlotName(plan->targetSlot)) + " reason=\"" + party.lastStatus() + "\"");
                    view.setStatusBarEvent(party.lastStatus().empty() ? "Can't equip that item" : party.lastStatus());
                    return;
                }

                logCharacterItemAction(
                    "placed_on_doll",
                    view.m_heldInventoryItem.item.objectDescriptionId,
                    "slot=" + std::string(equipmentSlotName(plan->targetSlot)));

                if (heldReplacement)
                {
                    setHeldItem(*heldReplacement);
                }
                else
                {
                    view.m_heldInventoryItem = {};
                }
            }
        });
}
} // namespace OpenYAMM::Game
