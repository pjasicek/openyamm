#include "game/gameplay/GameplayPartyOverlayInputController.h"

#include "game/CharacterDollTable.h"
#include "game/GameMechanics.h"
#include "game/InventoryItemUseRuntime.h"
#include "game/OutdoorGameView.h"
#include "game/OutdoorPartyRuntime.h"
#include "game/SkillData.h"
#include "game/SpellbookUiLayout.h"
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

struct CharacterSkillUiRow
{
    std::string canonicalName;
    std::string label;
    std::string level;
    bool upgradeable = false;
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
    size_t skillCount)
{
    for (size_t skillIndex = 0; skillIndex < skillCount; ++skillIndex)
    {
        const std::string canonicalName = canonicalSkillName(pSkillNames[skillIndex]);
        const CharacterSkill *pSkill = character.findSkill(canonicalName);

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
        rows.push_back(std::move(row));
        shownSkillNames.insert(canonicalName);
    }
}

CharacterSkillUiData buildCharacterSkillUiData(const Character *pCharacter)
{
    CharacterSkillUiData data = {};

    if (pCharacter == nullptr)
    {
        return data;
    }

    std::unordered_set<std::string> shownSkillNames;
    appendCharacterSkillUiRows(*pCharacter, data.weaponRows, shownSkillNames, WeaponSkillNames, std::size(WeaponSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.magicRows, shownSkillNames, MagicSkillNames, std::size(MagicSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.armorRows, shownSkillNames, ArmorSkillNames, std::size(ArmorSkillNames));
    appendCharacterSkillUiRows(*pCharacter, data.miscRows, shownSkillNames, MiscSkillNames, std::size(MiscSkillNames));

    std::vector<CharacterSkillUiRow> extraMiscRows;

    for (const auto &[ignoredSkillName, skill] : pCharacter->skills)
    {
        static_cast<void>(ignoredSkillName);
        const std::string canonicalName = canonicalSkillName(skill.name);

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

                const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(definition.pButtonLayoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
                    definition.pButtonLayoutId,
                    screenWidth,
                    screenHeight,
                    pLayout->width,
                    pLayout->height);

                if (resolved && view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
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
                    const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(pLayoutId);

                    if (pLayout == nullptr)
                    {
                        return {};
                    }

                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
                        pLayoutId,
                        screenWidth,
                        screenHeight,
                        pLayout->width,
                        pLayout->height);

                    if (!resolved || !view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
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
                const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
                    layoutId,
                    screenWidth,
                    screenHeight,
                    pLayout->width,
                    pLayout->height);

                if (resolved && view.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
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
    Character *pActiveCharacter =
        view.m_pOutdoorPartyRuntime != nullptr ? view.m_pOutdoorPartyRuntime->party().activeMember() : nullptr;
    const CharacterDollEntry *pActiveCharacterDollEntry =
        resolveCharacterDollEntry(view.m_pCharacterDollTable, pActiveCharacter);
    const CharacterDollTypeEntry *pActiveCharacterDollType =
        pActiveCharacterDollEntry != nullptr && view.m_pCharacterDollTable != nullptr
            ? view.m_pCharacterDollTable->getDollType(pActiveCharacterDollEntry->dollTypeId)
            : nullptr;
    const CharacterSkillUiData skillUiData = buildCharacterSkillUiData(pActiveCharacter);
    const OutdoorGameView::HudFontHandle *pSkillRowFont = view.findHudFont("Lucida");
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

    if (closePressed)
    {
        if (!view.m_closeOverlayLatch)
        {
            view.m_characterScreenOpen = false;
            view.m_characterDollJewelryOverlayOpen = false;
            view.m_closeOverlayLatch = true;
        }
    }
    else
    {
        view.m_closeOverlayLatch = false;
    }

    if (pKeyboardState[SDL_SCANCODE_TAB])
    {
        if (!view.m_characterMemberCycleLatch && view.m_pOutdoorPartyRuntime != nullptr)
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
            const OutdoorGameView::HudLayoutElement *pInventoryGridLayout = view.findHudLayoutElement("CharacterInventoryGrid");

            if (pInventoryGridLayout == nullptr)
            {
                return std::nullopt;
            }

            return view.resolveHudLayoutElement(
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
                const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(target.layoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
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

            const OutdoorGameView::HudLayoutElement *pExitLayout = view.findHudLayoutElement("CharacterExitButton");

            if (pExitLayout != nullptr)
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
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

            const OutdoorGameView::HudLayoutElement *pMagnifyLayout = view.findHudLayoutElement("CharacterMagnifyButton");

            if (pMagnifyLayout != nullptr)
            {
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
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

                const OutdoorGameView::HudLayoutElement *pLayout = view.findHudLayoutElement(target.layoutId);

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
                    const OutdoorGameView::HudTextureHandle *pTexture = view.ensureHudTextureLoaded(dynamicTextureName);

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
                        ? view.resolveHudLayoutElement(
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

                if (view.m_heldInventoryItem.active
                    || (pActiveCharacter != nullptr && equippedItemId(pActiveCharacter->equipment, target.slot) != 0))
                {
                    OutdoorGameView::CharacterPointerTarget pointerTarget = {};
                    pointerTarget.type = OutdoorGameView::CharacterPointerTargetType::EquipmentSlot;
                    pointerTarget.page = view.m_characterPage;
                    pointerTarget.equipmentSlot = target.slot;
                    return pointerTarget;
                }
            }

            if (view.m_heldInventoryItem.active)
            {
                const OutdoorGameView::HudLayoutElement *pDollLayout = view.findHudLayoutElement("CharacterDollPanel");

                if (pDollLayout != nullptr)
                {
                    const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedDoll = view.resolveHudLayoutElement(
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

                    if (view.m_heldInventoryItem.active)
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

                        const OutdoorGameView::HudLayoutElement *pRegionLayout = view.findHudLayoutElement(pRegionId);
                        const OutdoorGameView::HudLayoutElement *pLevelLayout = view.findHudLayoutElement(pLevelHeaderId);

                        if (pRegionLayout == nullptr || pLevelLayout == nullptr)
                        {
                            return {};
                        }

                        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedRegion = view.resolveHudLayoutElement(
                            pRegionId,
                            screenWidth,
                            screenHeight,
                            pRegionLayout->width,
                            pRegionLayout->height);
                        const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedLevelHeader = view.resolveHudLayoutElement(
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

                            if (!row.upgradeable)
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
        [&view, screenWidth, screenHeight, mouseX, mouseY, &resolveCharacterInventoryGrid, pActiveCharacterDollType](
            const OutdoorGameView::CharacterPointerTarget &target)
        {
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

            if (target.type == OutdoorGameView::CharacterPointerTargetType::PageButton)
            {
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
                view.m_characterScreenOpen = false;
                view.m_characterDollJewelryOverlayOpen = false;
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
                                view.ensureHudTextureLoaded(pItemDefinition->iconName);

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

                const OutdoorGameView::HudTextureHandle *pItemTexture = view.ensureHudTextureLoaded(pItemDefinition->iconName);

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

                const OutdoorGameView::HudLayoutElement *pDollLayout = view.findHudLayoutElement("CharacterDollPanel");
                const std::optional<OutdoorGameView::ResolvedHudLayoutElement> resolvedDoll = pDollLayout != nullptr
                    ? view.resolveHudLayoutElement(
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
