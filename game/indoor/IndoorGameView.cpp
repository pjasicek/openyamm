#include "game/indoor/IndoorGameView.h"

#include "game/app/GameSession.h"
#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayPartyOverlayInputController.h"
#include "game/gameplay/GameplayDialogUiFlow.h"
#include "game/gameplay/GameplayScreenHotkeyController.h"
#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/indoor/IndoorDebugRenderer.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/render/TextureFiltering.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/ui/GameplayDebugOverlayRenderer.h"
#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayHudRenderer.h"
#include "game/ui/GameplayHudOverlayRenderer.h"
#include "game/ui/HudUiService.h"
#include "game/ui/GameplayOverlayContext.h"
#include "game/ui/GameplayPartyOverlayRenderer.h"
#include "game/ui/GameplayUiOverlayOrchestrator.h"
#include "game/ui/SpellbookUiLayout.h"
#include "game/StringUtils.h"

#include <SDL3/SDL.h>
#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <functional>
#include <iostream>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
IndoorGameView::IndoorGameView(GameSession &gameSession)
    : m_gameSession(gameSession)
    , m_gameplayUiRuntime(gameSession.gameplayUiRuntime())
    , m_gameplayUiController(gameSession.gameplayUiController())
    , m_gameplayDialogController(gameSession.gameplayDialogController())
    , m_overlayInteractionState(gameSession.overlayInteractionState())
    , m_hudAssetLoadCache(m_gameplayUiRuntime.assetLoadCache())
    , m_uiLayoutManager(m_gameplayUiRuntime.layoutManager())
    , m_hudTextureHandles(m_gameplayUiRuntime.hudTextureHandles())
    , m_hudTextureIndexByName(m_gameplayUiRuntime.hudTextureIndexByName())
    , m_hudFontHandles(m_gameplayUiRuntime.hudFontHandles())
    , m_hudFontColorTextureHandles(m_gameplayUiRuntime.hudFontColorTextureHandles())
    , m_hudTextureColorTextureHandles(m_gameplayUiRuntime.hudTextureColorTextureHandles())
    , m_hudLayoutRuntimeHeightOverrides(m_gameplayUiRuntime.hudLayoutRuntimeHeightOverrides())
    , m_renderedInspectableHudItems(m_gameplayUiRuntime.renderedInspectableHudItems())
{
}

namespace
{
constexpr float HudReferenceWidth = 640.0f;
constexpr float HudReferenceHeight = 480.0f;
constexpr float HudFontIntegerSnapThreshold = 0.1f;
constexpr float MaxUiViewportAspect = 4.0f / 3.0f;
constexpr uint16_t HudViewId = 2;
constexpr uint64_t PartyPortraitDoubleClickWindowMs = 500;

enum class GameplayHudPointerTarget
{
    None = 0,
    MenuButton = 1,
    RestButton = 2,
    BooksButton = 3
};

using SpellbookPointerTargetType = IndoorSpellbookPointerTargetType;
using SpellbookPointerTarget = IndoorSpellbookPointerTarget;
using CharacterPointerTargetType = IndoorCharacterPointerTargetType;
using CharacterPointerTarget = IndoorCharacterPointerTarget;

struct UiViewportRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;
};

struct ParsedHudFontGlyphMetrics
{
    int leftSpacing = 0;
    int width = 0;
    int rightSpacing = 0;
};

struct ParsedHudBitmapFont
{
    int firstChar = 0;
    int lastChar = 0;
    int fontHeight = 0;
    std::array<ParsedHudFontGlyphMetrics, 256> glyphMetrics = {{}};
    std::array<uint32_t, 256> glyphOffsets = {{}};
    std::vector<uint8_t> pixels;
};

struct HudPointerState
{
    float x = 0.0f;
    float y = 0.0f;
    bool leftButtonPressed = false;
};

struct CharacterInventoryGridMetrics
{
    float x = 0.0f;
    float y = 0.0f;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
    float scale = 1.0f;
};

struct CharacterInventoryItemRect
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

struct SplitCharacterStatValue
{
    std::string actualText = "0";
    std::string baseText = "0";
    uint32_t actualColorAbgr = 0xffffffffu;
    bool active = false;
};

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
    else
    {
        pressedTarget = noneTarget;
    }
}

CharacterInventoryGridMetrics computeCharacterInventoryGridMetrics(
    const GameplayResolvedHudLayoutElement &resolved)
{
    CharacterInventoryGridMetrics metrics = {};
    metrics.x = resolved.x;
    metrics.y = resolved.y;
    metrics.scale = resolved.scale;
    metrics.cellWidth = resolved.width / static_cast<float>(std::max(1, Character::InventoryWidth));
    metrics.cellHeight = resolved.height / static_cast<float>(std::max(1, Character::InventoryHeight));
    return metrics;
}

CharacterInventoryItemRect computeCharacterInventoryItemRect(
    const CharacterInventoryGridMetrics &gridMetrics,
    const InventoryItem &item,
    float textureWidth,
    float textureHeight)
{
    const float slotSpanWidth = static_cast<float>(item.width) * gridMetrics.cellWidth;
    const float slotSpanHeight = static_cast<float>(item.height) * gridMetrics.cellHeight;
    const float offsetX = (slotSpanWidth - textureWidth) * 0.5f;
    const float offsetY = (slotSpanHeight - textureHeight) * 0.5f;

    CharacterInventoryItemRect rect = {};
    rect.x = std::round(gridMetrics.x + static_cast<float>(item.gridX) * gridMetrics.cellWidth + offsetX);
    rect.y = std::round(gridMetrics.y + static_cast<float>(item.gridY) * gridMetrics.cellHeight + offsetY);
    rect.width = textureWidth;
    rect.height = textureHeight;
    return rect;
}

constexpr const char *WeaponSkillNames[] = {
    "Axe",
    "Bow",
    "Dagger",
    "Mace",
    "Spear",
    "Staff",
    "Sword",
    "Unarmed",
    "Blaster",
};

constexpr const char *MagicSkillNames[] = {
    "FireMagic",
    "AirMagic",
    "WaterMagic",
    "EarthMagic",
    "SpiritMagic",
    "MindMagic",
    "BodyMagic",
    "LightMagic",
    "DarkMagic",
};

constexpr const char *ArmorSkillNames[] = {
    "LeatherArmor",
    "ChainArmor",
    "PlateArmor",
    "Shield",
    "Dodging",
};

constexpr const char *MiscSkillNames[] = {
    "Alchemy",
    "Armsmaster",
    "Bodybuilding",
    "IdentifyItem",
    "IdentifyMonster",
    "Learning",
    "DisarmTraps",
    "Meditation",
    "Merchant",
    "Perception",
    "RepairItem",
    "Stealing",
};

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

    for (const auto &[canonicalName, skill] : pCharacter->skills)
    {
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

SplitCharacterStatValue makeSplitCharacterStatValue(const CharacterSheetValue &value)
{
    SplitCharacterStatValue result = {};
    result.active = true;
    result.baseText = std::to_string(value.base);
    result.actualText = value.infinite ? "INF" : std::to_string(value.actual);

    if (!value.infinite)
    {
        if (value.actual > value.base)
        {
            result.actualColorAbgr = 0xff00ff00u;
        }
        else if (value.actual < value.base)
        {
            result.actualColorAbgr = 0xff0000ffu;
        }
    }

    return result;
}

SplitCharacterStatValue makeSplitCharacterResourceValue(int currentValue, int maximumValue)
{
    SplitCharacterStatValue result = {};
    result.active = true;
    result.actualText = std::to_string(currentValue);
    result.baseText = std::to_string(maximumValue);

    if (currentValue <= 0)
    {
        result.actualColorAbgr = 0xff0000ffu;
    }
    else if (maximumValue > 0 && currentValue * 2 < maximumValue)
    {
        result.actualColorAbgr = 0xff00ffffu;
    }

    return result;
}

bool tryGetSplitCharacterStatValue(
    const std::string &normalizedLayoutId,
    const CharacterSheetSummary &summary,
    SplitCharacterStatValue &value)
{
    if (normalizedLayoutId == "characterstatmightvalue")
    {
        value = makeSplitCharacterStatValue(summary.might);
        return true;
    }

    if (normalizedLayoutId == "characterstatintellectvalue")
    {
        value = makeSplitCharacterStatValue(summary.intellect);
        return true;
    }

    if (normalizedLayoutId == "characterstatpersonalityvalue")
    {
        value = makeSplitCharacterStatValue(summary.personality);
        return true;
    }

    if (normalizedLayoutId == "characterstatendurancevalue")
    {
        value = makeSplitCharacterStatValue(summary.endurance);
        return true;
    }

    if (normalizedLayoutId == "characterstataccuracyvalue")
    {
        value = makeSplitCharacterStatValue(summary.accuracy);
        return true;
    }

    if (normalizedLayoutId == "characterstatspeedvalue")
    {
        value = makeSplitCharacterStatValue(summary.speed);
        return true;
    }

    if (normalizedLayoutId == "characterstatluckvalue")
    {
        value = makeSplitCharacterStatValue(summary.luck);
        return true;
    }

    if (normalizedLayoutId == "characterstathitpointsvalue")
    {
        value = makeSplitCharacterResourceValue(summary.health.current, summary.health.maximum);
        return true;
    }

    if (normalizedLayoutId == "characterstatlevelvalue")
    {
        value = makeSplitCharacterStatValue(summary.level);
        return true;
    }

    if (normalizedLayoutId == "characterstatfireresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.fireResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatairresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.airResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatwaterresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.waterResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatearthresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.earthResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatmindresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.mindResistance);
        return true;
    }

    if (normalizedLayoutId == "characterstatbodyresistancevalue")
    {
        value = makeSplitCharacterStatValue(summary.bodyResistance);
        return true;
    }

    return false;
}

bool isBodyEquipmentVisualSlot(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
        case EquipmentSlot::MainHand:
        case EquipmentSlot::Bow:
        case EquipmentSlot::Armor:
        case EquipmentSlot::Helm:
        case EquipmentSlot::Belt:
        case EquipmentSlot::Cloak:
        case EquipmentSlot::Gauntlets:
        case EquipmentSlot::Boots:
            return true;

        case EquipmentSlot::Amulet:
        case EquipmentSlot::Ring1:
        case EquipmentSlot::Ring2:
        case EquipmentSlot::Ring3:
        case EquipmentSlot::Ring4:
        case EquipmentSlot::Ring5:
        case EquipmentSlot::Ring6:
            return false;
    }

    return false;
}

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

bool usesAlternateCloakBeltEquippedVariant(EquipmentSlot slot)
{
    return slot == EquipmentSlot::Cloak || slot == EquipmentSlot::Belt;
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

std::optional<EquipmentSlot> characterEquipmentSlotForLayoutId(const std::string &layoutId)
{
    const std::string normalized = toLowerCopy(layoutId);

    if (normalized == "characterdollbowslot")
    {
        return EquipmentSlot::Bow;
    }

    if (normalized == "characterdollrighthandslot")
    {
        return EquipmentSlot::MainHand;
    }

    if (normalized == "characterdolllefthandslot")
    {
        return EquipmentSlot::OffHand;
    }

    if (normalized == "characterdollarmorslot")
    {
        return EquipmentSlot::Armor;
    }

    if (normalized == "characterdollhelmetslot")
    {
        return EquipmentSlot::Helm;
    }

    if (normalized == "characterdollbeltslot")
    {
        return EquipmentSlot::Belt;
    }

    if (normalized == "characterdollcloakslot")
    {
        return EquipmentSlot::Cloak;
    }

    if (normalized == "characterdollbootsslot")
    {
        return EquipmentSlot::Boots;
    }

    if (normalized == "characterdollamuletslot")
    {
        return EquipmentSlot::Amulet;
    }

    if (normalized == "characterdollgauntletsslot")
    {
        return EquipmentSlot::Gauntlets;
    }

    if (normalized == "characterdollring1slot")
    {
        return EquipmentSlot::Ring1;
    }

    if (normalized == "characterdollring2slot")
    {
        return EquipmentSlot::Ring2;
    }

    if (normalized == "characterdollring3slot")
    {
        return EquipmentSlot::Ring3;
    }

    if (normalized == "characterdollring4slot")
    {
        return EquipmentSlot::Ring4;
    }

    if (normalized == "characterdollring5slot")
    {
        return EquipmentSlot::Ring5;
    }

    if (normalized == "characterdollring6slot")
    {
        return EquipmentSlot::Ring6;
    }

    return std::nullopt;
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

const CharacterDollEntry *resolveCharacterDollEntry(
    const CharacterDollTable *pCharacterDollTable,
    const Character *pCharacter)
{
    if (pCharacterDollTable == nullptr || pCharacter == nullptr)
    {
        return nullptr;
    }

    const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(pCharacter->characterDataId);

    if (pEntry != nullptr)
    {
        return pEntry;
    }

    return pCharacterDollTable->getCharacter(1);
}

int32_t readInt32Le(const uint8_t *pBytes)
{
    return static_cast<int32_t>(
        static_cast<uint32_t>(pBytes[0])
        | (static_cast<uint32_t>(pBytes[1]) << 8)
        | (static_cast<uint32_t>(pBytes[2]) << 16)
        | (static_cast<uint32_t>(pBytes[3]) << 24));
}

uint32_t readUint32Le(const uint8_t *pBytes)
{
    return static_cast<uint32_t>(
        static_cast<uint32_t>(pBytes[0])
        | (static_cast<uint32_t>(pBytes[1]) << 8)
        | (static_cast<uint32_t>(pBytes[2]) << 16)
        | (static_cast<uint32_t>(pBytes[3]) << 24));
}

bool validateParsedHudBitmapFont(
    const ParsedHudBitmapFont &font,
    const std::vector<uint8_t> &pixels)
{
    if (font.firstChar < 0
        || font.firstChar > 255
        || font.lastChar < 0
        || font.lastChar > 255
        || font.firstChar > font.lastChar
        || font.fontHeight <= 0)
    {
        return false;
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const ParsedHudFontGlyphMetrics &metrics = font.glyphMetrics[glyphIndex];

        if (glyphIndex < font.firstChar || glyphIndex > font.lastChar)
        {
            continue;
        }

        if (metrics.width < 0 || metrics.width > 1024 || metrics.leftSpacing < -512 || metrics.leftSpacing > 512
            || metrics.rightSpacing < -512 || metrics.rightSpacing > 512)
        {
            return false;
        }

        const uint64_t glyphSize = static_cast<uint64_t>(font.fontHeight) * static_cast<uint64_t>(metrics.width);
        const uint64_t glyphEnd = static_cast<uint64_t>(font.glyphOffsets[glyphIndex]) + glyphSize;

        if (glyphEnd > pixels.size())
        {
            return false;
        }
    }

    return true;
}

std::optional<ParsedHudBitmapFont> parseHudBitmapFont(const std::vector<uint8_t> &bytes)
{
    constexpr size_t FontHeaderSize = 32;
    constexpr size_t Mm7AtlasSize = 4096;
    constexpr size_t MmxAtlasSize = 1280;

    if (bytes.size() < FontHeaderSize + MmxAtlasSize)
    {
        return std::nullopt;
    }

    const uint8_t *pBytes = bytes.data();

    if (pBytes[2] != 8 || pBytes[3] != 0 || pBytes[4] != 0 || pBytes[6] != 0 || pBytes[7] != 0)
    {
        return std::nullopt;
    }

    ParsedHudBitmapFont mm7Font = {};
    mm7Font.firstChar = pBytes[0];
    mm7Font.lastChar = pBytes[1];
    mm7Font.fontHeight = pBytes[5];

    if (bytes.size() >= FontHeaderSize + Mm7AtlasSize)
    {
        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t metricOffset = FontHeaderSize + static_cast<size_t>(glyphIndex) * 12;
            mm7Font.glyphMetrics[glyphIndex].leftSpacing = readInt32Le(&pBytes[metricOffset]);
            mm7Font.glyphMetrics[glyphIndex].width = readInt32Le(&pBytes[metricOffset + 4]);
            mm7Font.glyphMetrics[glyphIndex].rightSpacing = readInt32Le(&pBytes[metricOffset + 8]);
        }

        for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
        {
            const size_t offsetPosition = FontHeaderSize + 256 * 12 + static_cast<size_t>(glyphIndex) * 4;
            mm7Font.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
        }

        mm7Font.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + Mm7AtlasSize), bytes.end());

        if (validateParsedHudBitmapFont(mm7Font, mm7Font.pixels))
        {
            return mm7Font;
        }
    }

    ParsedHudBitmapFont mmxFont = {};
    mmxFont.firstChar = pBytes[0];
    mmxFont.lastChar = pBytes[1];
    mmxFont.fontHeight = pBytes[5];

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        mmxFont.glyphMetrics[glyphIndex].width = pBytes[FontHeaderSize + glyphIndex];
    }

    for (int glyphIndex = 0; glyphIndex < 256; ++glyphIndex)
    {
        const size_t offsetPosition = FontHeaderSize + 256 + static_cast<size_t>(glyphIndex) * 4;
        mmxFont.glyphOffsets[glyphIndex] = readUint32Le(&pBytes[offsetPosition]);
    }

    mmxFont.pixels.assign(bytes.begin() + static_cast<ptrdiff_t>(FontHeaderSize + MmxAtlasSize), bytes.end());

    if (!validateParsedHudBitmapFont(mmxFont, mmxFont.pixels))
    {
        return std::nullopt;
    }

    return mmxFont;
}

bool usesBlackTransparencyKey(std::string_view textureName)
{
    const std::string normalizedName = toLowerCopy(std::string(textureName));
    return normalizedName.rfind("mapdir", 0) == 0 || normalizedName.rfind("micon", 0) == 0;
}

float snappedHudFontScale(float scale)
{
    const float roundedScale = std::round(scale);

    if (std::abs(scale - roundedScale) <= HudFontIntegerSnapThreshold)
    {
        return std::max(1.0f, roundedScale);
    }

    return std::max(1.0f, scale);
}

UiViewportRect computeUiViewportRect(int screenWidth, int screenHeight)
{
    UiViewportRect viewport = {};
    viewport.width = static_cast<float>(screenWidth);
    viewport.height = static_cast<float>(screenHeight);

    if (screenHeight > 0)
    {
        const float maxWidthForHeight = viewport.height * MaxUiViewportAspect;

        if (viewport.width > maxWidthForHeight)
        {
            viewport.width = maxWidthForHeight;
            viewport.x = (static_cast<float>(screenWidth) - viewport.width) * 0.5f;
        }
    }

    return viewport;
}

UiViewportRect computeAnchorRect(
    UiLayoutManager::LayoutAnchorSpace anchorSpace,
    int screenWidth,
    int screenHeight)
{
    if (anchorSpace == UiLayoutManager::LayoutAnchorSpace::Screen)
    {
        UiViewportRect rect = {};
        rect.width = static_cast<float>(screenWidth);
        rect.height = static_cast<float>(screenHeight);
        return rect;
    }

    return computeUiViewportRect(screenWidth, screenHeight);
}

const char *activeGameplayButtonLayoutId(
    GameplayUiLayout layout,
    const char *pWidescreenLayoutId,
    const char *pStandardLayoutId)
{
    return layout == GameplayUiLayout::Standard ? pStandardLayoutId : pWidescreenLayoutId;
}

uint32_t packHudColorAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u | (static_cast<uint32_t>(blue) << 16) | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

GameplayResolvedHudLayoutElement resolveAttachedHudLayoutRect(
    UiLayoutManager::LayoutAttachMode attachTo,
    const GameplayResolvedHudLayoutElement &parent,
    float width,
    float height,
    float gapX,
    float gapY,
    float scale)
{
    GameplayResolvedHudLayoutElement resolved = {};
    resolved.width = width;
    resolved.height = height;
    resolved.scale = scale;

    switch (attachTo)
    {
    case UiLayoutManager::LayoutAttachMode::None:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::RightOf:
        resolved.x = parent.x + parent.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::LeftOf:
        resolved.x = parent.x - resolved.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::Above:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::Below:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + parent.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterAbove:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterBelow:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + parent.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopCenter:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideTopRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomLeft:
        resolved.x = parent.x + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomCenter:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::InsideBottomRight:
        resolved.x = parent.x + parent.width - resolved.width + gapX * scale;
        resolved.y = parent.y + parent.height - resolved.height + gapY * scale;
        break;

    case UiLayoutManager::LayoutAttachMode::CenterIn:
        resolved.x = parent.x + (parent.width - resolved.width) * 0.5f + gapX * scale;
        resolved.y = parent.y + (parent.height - resolved.height) * 0.5f + gapY * scale;
        break;
    }

    return resolved;
}

bool isResidentSelectionMode(const EventDialogContent &dialog)
{
    return !dialog.actions.empty()
        && std::all_of(
            dialog.actions.begin(),
            dialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseResident;
            });
}

uint32_t currentDialogueHostHouseId(const EventRuntimeState *pEventRuntimeState)
{
    return pEventRuntimeState != nullptr ? pEventRuntimeState->dialogueState.hostHouseId : 0;
}
}

bool IndoorGameView::initialize(
    const Engine::AssetFileSystem &assetFileSystem,
    const MapStatsEntry &map,
    IndoorDebugRenderer &indoorRenderer,
    IndoorSceneRuntime &sceneRuntime,
    GameAudioSystem *pGameAudioSystem)
{
    shutdown();
    const GameDataRepository &data = m_gameSession.data();

    m_pAssetFileSystem = &assetFileSystem;
    m_pIndoorRenderer = &indoorRenderer;
    m_pIndoorSceneRuntime = &sceneRuntime;
    m_pGameAudioSystem = pGameAudioSystem;
    m_map = map;
    m_gameplayUiRuntime.bindAssetFileSystem(&assetFileSystem);
    m_gameplayUiController.clearRuntimeState();

    if (!m_gameplayUiRuntime.ensureGameplayLayoutsLoaded(m_gameplayUiController))
    {
        return false;
    }

    m_gameplayUiRuntime.preloadReferencedAssets();
    return true;
}

void IndoorGameView::setSettingsSnapshot(const GameSettings &settings)
{
    m_settings = settings;

    IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime != nullptr)
    {
        Party &party = pRuntime->party();
        party.setDebugDamageImmune(settings.immortal);
        party.setDebugUnlimitedMana(settings.unlimitedMana);
    }
}

void IndoorGameView::render(int width, int height, float mouseWheelDelta, float deltaSeconds)
{
    EventRuntimeState *pEventRuntimeState =
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr;

    if (!activeEventDialog().isActive
        && pEventRuntimeState != nullptr
        && pEventRuntimeState->pendingDialogueContext.has_value()
        && pEventRuntimeState->pendingDialogueContext->kind != DialogueContextKind::None)
    {
        presentPendingEventDialog(pEventRuntimeState->messages.size(), true);
    }

    SDL_Window *pWindow = SDL_GetMouseFocus();

    if (pWindow == nullptr)
    {
        pWindow = SDL_GetKeyboardFocus();
    }

    float gameplayMouseX = 0.0f;
    float gameplayMouseY = 0.0f;
    const SDL_MouseButtonFlags gameplayMouseButtons = SDL_GetMouseState(&gameplayMouseX, &gameplayMouseY);
    const bool gameplayMouseLookAllowed = shouldEnableGameplayMouseLook();
    const bool gameplayCursorModeActive =
        gameplayMouseLookAllowed && (gameplayMouseButtons & SDL_BUTTON_RMASK) != 0;
    const bool gameplayMouseLookActive = gameplayMouseLookAllowed && !gameplayCursorModeActive;

    m_gameplayCursorModeActive = gameplayCursorModeActive;
    m_gameplayMouseLookActive = gameplayMouseLookActive;
    syncGameplayMouseLookMode(pWindow, gameplayMouseLookActive);

    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->setGameplayMouseLookMode(gameplayMouseLookActive, gameplayCursorModeActive);
    }

    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->render(width, height, mouseWheelDelta, deltaSeconds);
    }

    if (!activeEventDialog().isActive
        && pEventRuntimeState != nullptr
        && pEventRuntimeState->pendingDialogueContext.has_value()
        && pEventRuntimeState->pendingDialogueContext->kind != DialogueContextKind::None)
    {
        presentPendingEventDialog(pEventRuntimeState->messages.size(), true);
    }

    m_gameplayUiController.updateStatusBarEvent(deltaSeconds);
    updateItemInspectOverlayState(width, height);

    GameplayUiController::RestScreenState &restScreen = m_gameplayUiController.restScreen();

    if (restScreen.active)
    {
        const float safeDeltaSeconds = std::max(0.0f, deltaSeconds);
        restScreen.hourglassElapsedSeconds += safeDeltaSeconds;

        if (restScreen.mode != GameplayUiController::RestMode::None && worldRuntime() != nullptr)
        {
            constexpr float ShortestRestAnimationSeconds = 0.25f;
            constexpr float LongestRestAnimationSeconds = 2.0f;
            constexpr float RestMinutesPerAnimationSecond = 360.0f;
            const float animationDurationSeconds = std::clamp(
                restScreen.totalMinutes / RestMinutesPerAnimationSecond,
                ShortestRestAnimationSeconds,
                LongestRestAnimationSeconds);
            const float gameMinutesPerSecond = animationDurationSeconds > 0.0f
                ? restScreen.totalMinutes / animationDurationSeconds
                : restScreen.totalMinutes;
            const float advancedMinutes =
                std::min(restScreen.remainingMinutes, gameMinutesPerSecond * safeDeltaSeconds);

            if (advancedMinutes > 0.0f)
            {
                worldRuntime()->advanceGameMinutes(advancedMinutes);
                restScreen.remainingMinutes = std::max(0.0f, restScreen.remainingMinutes - advancedMinutes);
            }

            if (restScreen.remainingMinutes <= 0.0f)
            {
                if (partyRuntime() != nullptr && restScreen.mode == GameplayUiController::RestMode::Heal)
                {
                    partyRuntime()->party().restAndHealAll();
                }

                const bool closeRestScreenAfterCompletion = restScreen.mode == GameplayUiController::RestMode::Heal;
                restScreen.mode = GameplayUiController::RestMode::None;
                restScreen.totalMinutes = 0.0f;
                restScreen.remainingMinutes = 0.0f;

                if (closeRestScreenAfterCompletion)
                {
                    createGameplayOverlayContext().closeRestOverlay();
                }
            }
        }
    }

    GameplayOverlayContext overlayContext = createGameplayOverlayContext();
    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);
    struct KeyboardStateSnapshotUpdater
    {
        std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState;
        const bool *pKeyboardState = nullptr;

        ~KeyboardStateSnapshotUpdater()
        {
            if (pKeyboardState == nullptr)
            {
                previousKeyboardState.fill(0);
                return;
            }

            for (size_t scancode = 0; scancode < SDL_SCANCODE_COUNT; ++scancode)
            {
                previousKeyboardState[scancode] = pKeyboardState[scancode] ? 1u : 0u;
            }
        }
    } keyboardStateSnapshotUpdater = {m_gameSession.previousKeyboardState(), pKeyboardState};
    IGameplayWorldRuntime *pWorldRuntime = worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);
    bool hasSharedScreenOverlay =
        m_gameplayUiController.restScreen().active
        || m_gameplayUiController.menuScreen().active
        || m_gameplayUiController.controlsScreen().active
        || m_gameplayUiController.keyboardScreen().active
        || m_gameplayUiController.videoOptionsScreen().active
        || m_gameplayUiController.saveGameScreen().active
        || m_gameplayUiController.loadGameScreen().active
        || m_gameplayUiController.journalScreen().active;

    const bool canOpenMenu =
        !activeEventDialog().isActive
        && !hasActiveLootView
        && !hasSharedScreenOverlay
        && !m_gameplayUiController.inventoryNestedOverlay().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();
    const bool allowGameplayPointerInput = !gameplayMouseLookAllowed || gameplayCursorModeActive;

    const bool escapePressed = pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (canOpenMenu)
    {
        if (escapePressed && m_gameSession.previousKeyboardState()[SDL_SCANCODE_ESCAPE] == 0)
        {
            createGameplayOverlayContext().openMenuOverlay();
            interactionState().menuToggleLatch = true;
            hasSharedScreenOverlay = true;
        }
        else if (!escapePressed)
        {
            interactionState().menuToggleLatch = false;
        }
    }

    const bool gameplayReadyForPortraitClicks =
        allowGameplayPointerInput
        && width > 0
        && height > 0
        && !activeEventDialog().isActive
        && !m_gameplayUiController.spellbook().active
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    if (gameplayReadyForPortraitClicks)
    {
        const HudPointerState portraitPointerState = {
            gameplayMouseX,
            gameplayMouseY,
            (gameplayMouseButtons & SDL_BUTTON_LMASK) != 0
        };
        const bool requireGameplayReady = !hasActiveLootView;

        handlePointerClickRelease(
            portraitPointerState,
            m_partyPortraitClickLatch,
            m_partyPortraitPressedIndex,
            std::optional<size_t>{},
            [this, width, height](float x, float y) -> std::optional<size_t>
            {
                return resolvePartyPortraitIndexAtPoint(width, height, x, y);
            },
            [this, requireGameplayReady, hasActiveLootView](const std::optional<size_t> &memberIndex)
            {
                if (!memberIndex)
                {
                    return;
                }

                if (m_gameplayUiController.heldInventoryItem().active)
                {
                    const bool switchCharacterOnFailedPlacement =
                        m_gameplayUiController.characterScreen().open
                        && m_gameplayUiController.characterScreen().page
                            == GameplayUiController::CharacterPage::Inventory;

                    if (tryAutoPlaceHeldItemOnPartyMember(*memberIndex, !switchCharacterOnFailedPlacement))
                    {
                        m_lastPartyPortraitClickedIndex = std::nullopt;
                    }
                    else if (switchCharacterOnFailedPlacement)
                    {
                        trySelectPartyMember(*memberIndex, requireGameplayReady);
                    }

                    return;
                }

                const uint64_t nowTicks = SDL_GetTicks();
                const bool isGameplayInventoryDoubleClick =
                    requireGameplayReady
                    && m_lastPartyPortraitClickedIndex.has_value()
                    && *m_lastPartyPortraitClickedIndex == *memberIndex
                    && nowTicks >= m_lastPartyPortraitClickTicks
                    && nowTicks - m_lastPartyPortraitClickTicks <= PartyPortraitDoubleClickWindowMs;
                const bool isChestInventoryDoubleClick =
                    hasActiveLootView
                    && m_lastPartyPortraitClickedIndex.has_value()
                    && *m_lastPartyPortraitClickedIndex == *memberIndex
                    && nowTicks >= m_lastPartyPortraitClickTicks
                    && nowTicks - m_lastPartyPortraitClickTicks <= PartyPortraitDoubleClickWindowMs;

                if (!trySelectPartyMember(*memberIndex, requireGameplayReady))
                {
                    return;
                }

                if (isGameplayInventoryDoubleClick)
                {
                    GameplayUiController::CharacterScreenState &characterScreen = m_gameplayUiController.characterScreen();
                    characterScreen = {};
                    characterScreen.open = true;
                    characterScreen.page = GameplayUiController::CharacterPage::Inventory;
                    characterScreen.source = GameplayUiController::CharacterScreenSource::Party;
                    characterScreen.sourceIndex = 0;
                }
                else if (isChestInventoryDoubleClick)
                {
                    m_gameplayUiController.openInventoryNestedOverlay(
                        GameplayUiController::InventoryNestedOverlayMode::ChestTransfer);
                }

                m_lastPartyPortraitClickTicks = nowTicks;
                m_lastPartyPortraitClickedIndex = *memberIndex;
            });
    }
    else
    {
        m_partyPortraitClickLatch = false;
        m_partyPortraitPressedIndex = std::nullopt;
    }

    const bool canToggleGameplaySpellbook =
        !activeEventDialog().isActive
        && !m_gameplayUiController.characterScreen().open
        && !hasActiveLootView
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    const bool canToggleInventory =
        !activeEventDialog().isActive
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active;

    const bool canCyclePartyMember =
        !activeEventDialog().isActive
        && !hasActiveLootView
        && !m_gameplayUiController.spellbook().active
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    GameplayScreenHotkeyController::handleGameplayScreenHotkeys(
        overlayContext,
        pKeyboardState,
        GameplayScreenHotkeyConfig{
            .canToggleSpellbook = canToggleGameplaySpellbook,
            .canToggleInventory = canToggleInventory,
            .canCyclePartyMember = canCyclePartyMember,
            .hasActiveLootView = hasActiveLootView,
        });

    const bool canClickGameplayHudButtons =
        allowGameplayPointerInput
        && width > 0
        && height > 0
        && !activeEventDialog().isActive
        && !m_gameplayUiController.characterScreen().open
        && !m_gameplayUiController.spellbook().active
        && !hasActiveLootView
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.journalScreen().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    if (canClickGameplayHudButtons)
    {
        const HudPointerState buttonPointerState = {
            gameplayMouseX,
            gameplayMouseY,
            (gameplayMouseButtons & SDL_BUTTON_LMASK) != 0
        };

        handlePointerClickRelease(
            buttonPointerState,
            m_gameplayHudButtonClickLatch,
            m_gameplayHudPressedButton,
            0,
            [this, width, height](float pointerX, float pointerY) -> int
            {
                const std::array<std::pair<const char *, GameplayHudPointerTarget>, 3> targets = {{
                    {
                        activeGameplayButtonLayoutId(
                            m_settings.gameplayUiLayout,
                            "OutdoorButtonOptions",
                            "OutdoorStandardButtonOptions"),
                        GameplayHudPointerTarget::MenuButton
                    },
                    {
                        activeGameplayButtonLayoutId(
                            m_settings.gameplayUiLayout,
                            "OutdoorButtonRest",
                            "OutdoorStandardButtonRest"),
                        GameplayHudPointerTarget::RestButton
                    },
                    {
                        activeGameplayButtonLayoutId(
                            m_settings.gameplayUiLayout,
                            "OutdoorButtonBooks",
                            "OutdoorStandardButtonBooks"),
                        GameplayHudPointerTarget::BooksButton
                    }
                }};

                for (const auto &[layoutId, target] : targets)
                {
                    const UiLayoutManager::LayoutElement *pLayout = findHudLayoutElement(layoutId);

                    if (pLayout == nullptr)
                    {
                        continue;
                    }

                    const std::optional<GameplayResolvedHudLayoutElement> resolved =
                        resolveHudLayoutElement(layoutId, width, height, pLayout->width, pLayout->height);

                    if (resolved && isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                    {
                        return static_cast<int>(target);
                    }
                }

                return 0;
            },
            [this](int target)
            {
                if (target == static_cast<int>(GameplayHudPointerTarget::MenuButton))
                {
                    createGameplayOverlayContext().openMenuOverlay();
                }
                else if (target == static_cast<int>(GameplayHudPointerTarget::RestButton))
                {
                    m_gameplayUiController.closeSpellbook();
                    m_gameplayUiController.characterScreen() = {};
                    m_gameplayUiController.restScreen() = {};
                    m_gameplayUiController.restScreen().active = true;
                    interactionState().restClickLatch = false;
                    interactionState().restPressedTarget = {};
                }
                else if (target == static_cast<int>(GameplayHudPointerTarget::BooksButton))
                {
                    createGameplayOverlayContext().openJournalOverlay();
                }
            });
    }
    else
    {
        m_gameplayHudButtonClickLatch = false;
        m_gameplayHudPressedButton = 0;
    }

    const bool canToggleJournal =
        !activeEventDialog().isActive
        && !hasActiveLootView
        && !m_gameplayUiController.restScreen().active
        && !m_gameplayUiController.menuScreen().active
        && !m_gameplayUiController.controlsScreen().active
        && !m_gameplayUiController.keyboardScreen().active
        && !m_gameplayUiController.videoOptionsScreen().active
        && !m_gameplayUiController.saveGameScreen().active
        && !m_gameplayUiController.loadGameScreen().active
        && !m_gameplayUiController.inventoryNestedOverlay().active
        && !m_gameplayUiController.houseShopOverlay().active
        && !m_gameplayUiController.houseBankState().inputActive();

    const GameplayUiOverlayInputResult inputResult = GameplayUiOverlayOrchestrator::handleStandardOverlayInput(
        overlayContext,
        pKeyboardState,
        width,
        height,
        GameplayUiOverlayInputConfig{
            .hasActiveLootView = hasActiveLootView,
            .canToggleJournal = canToggleJournal,
            .mapShortcutPressed =
                pKeyboardState != nullptr
                && (pKeyboardState[SDL_SCANCODE_M]
                    || m_settings.keyboard.isPressed(KeyboardAction::MapBook, pKeyboardState)),
            .storyShortcutPressed =
                pKeyboardState != nullptr && m_settings.keyboard.isPressed(KeyboardAction::History, pKeyboardState),
            .notesShortcutPressed =
                pKeyboardState != nullptr && m_settings.keyboard.isPressed(KeyboardAction::AutoNotes, pKeyboardState),
            .zoomInPressed =
                pKeyboardState != nullptr && m_settings.keyboard.isPressed(KeyboardAction::ZoomIn, pKeyboardState),
            .zoomOutPressed =
                pKeyboardState != nullptr && m_settings.keyboard.isPressed(KeyboardAction::ZoomOut, pKeyboardState),
            .mouseWheelDelta = mouseWheelDelta,
            .activeEventDialog = activeEventDialog().isActive,
            .residentSelectionMode = isResidentSelectionMode(activeEventDialog()),
            .restActive = m_gameplayUiController.restScreen().active,
            .menuActive = m_gameplayUiController.menuScreen().active,
            .controlsActive = m_gameplayUiController.controlsScreen().active,
            .keyboardActive = m_gameplayUiController.keyboardScreen().active,
            .videoOptionsActive = m_gameplayUiController.videoOptionsScreen().active,
            .saveGameActive = m_gameplayUiController.saveGameScreen().active,
            .spellbookActive = m_gameplayUiController.spellbook().active,
            .characterScreenOpen = m_gameplayUiController.characterScreen().open,
        },
        GameplayUiOverlayInputCallbacks{
            .resetDialogueInteractionState =
                [this]()
                {
                    interactionState().eventDialogSelectUpLatch = false;
                    interactionState().eventDialogSelectDownLatch = false;
                    interactionState().eventDialogAcceptLatch = false;
                    interactionState().eventDialogPartySelectLatches.fill(false);
                    interactionState().dialogueClickLatch = false;
                    interactionState().dialoguePressedTarget = {};
                },
            .handleSpellbookOverlayInput =
                [this](const bool *pState, int screenWidth, int screenHeight)
                {
                    handleSpellbookOverlayInput(pState, screenWidth, screenHeight);
                },
            .handleCharacterOverlayInput =
                [this](const bool *pState, int screenWidth, int screenHeight)
                {
                    handleCharacterOverlayInput(pState, screenWidth, screenHeight);
                }});

    if (inputResult.journalInputConsumed && !activeEventDialog().isActive)
    {
        interactionState().eventDialogSelectUpLatch = false;
        interactionState().eventDialogSelectDownLatch = false;
        interactionState().eventDialogAcceptLatch = false;
        interactionState().eventDialogPartySelectLatches.fill(false);
    }

    m_renderedInspectableHudItems.clear();
    m_renderedInspectableHudState = currentGameplayHudScreenState();
    const bool canRenderHudOverlays =
        m_pIndoorRenderer != nullptr
        && m_pIndoorRenderer->hasHudRenderResources()
        && width > 0
        && height > 0;

    const bool renderChestUi =
        hasActiveLootView && pWorldRuntime != nullptr && pWorldRuntime->activeChestView() != nullptr;
    GameplayUiOverlayOrchestrator::renderStandardOverlays(
        overlayContext,
        width,
        height,
        GameplayUiOverlayRenderConfig{
            .canRenderHudOverlays = canRenderHudOverlays,
            .hasActiveLootView = hasActiveLootView,
            .activeEventDialog = activeEventDialog().isActive,
            .renderChestBelowHud = renderChestUi,
            .renderChestAboveHud = renderChestUi,
            .renderInventoryBelowHud = renderChestUi,
            .renderInventoryAboveHud = renderChestUi,
            .renderDialogueAboveHud = activeEventDialog().isActive,
            .renderCharacterBelowHud = true,
            .renderCharacterAboveHud = true,
            .renderDebugLootFallback = hasActiveLootView,
            .renderDebugDialogueFallback = activeEventDialog().isActive,
        },
        GameplayUiOverlayRenderCallbacks{
            .renderCharacterOverlay =
                [this, width, height](bool renderAboveHud)
                {
                    renderCharacterOverlay(width, height, renderAboveHud);
                },
            .renderDialogueOverlay =
                [this, width, height](bool renderAboveHud)
                {
                    renderDialogueOverlay(width, height, renderAboveHud);
                },
            .renderChestOverlay =
                [&overlayContext, width, height](bool renderAboveHud)
                {
                    GameplayHudOverlayRenderer::renderChestPanel(overlayContext, width, height, renderAboveHud);
                },
            .renderInventoryNestedOverlay =
                [&overlayContext, width, height](bool renderAboveHud)
                {
                    GameplayHudOverlayRenderer::renderInventoryNestedOverlay(
                        overlayContext,
                        width,
                        height,
                        renderAboveHud);
                },
            .renderGameplayMouseLookOverlay =
                [this, width, height]()
                {
                    renderGameplayMouseLookOverlay(width, height);
                }});
}

void IndoorGameView::handleSpellbookOverlayInput(const bool *pKeyboardState, int width, int height)
{
    if (!m_gameplayUiController.spellbook().active || width <= 0 || height <= 0)
    {
        interactionState().spellbookClickLatch = false;
        return;
    }

    GameplayOverlayContext overlayContext = createGameplayOverlayContext();
    GameplayPartyOverlayInputController::handleSpellbookOverlayInput(
        overlayContext,
        pKeyboardState,
        width,
        height);
}

void IndoorGameView::handleCharacterOverlayInput(const bool *pKeyboardState, int width, int height)
{
    if (!m_gameplayUiController.characterScreen().open || width <= 0 || height <= 0)
    {
        interactionState().characterClickLatch = false;
        return;
    }

    GameplayOverlayContext overlayContext = createGameplayOverlayContext();
    GameplayPartyOverlayInputController::handleCharacterOverlayInput(
        overlayContext,
        pKeyboardState,
        width,
        height);
}

void IndoorGameView::renderCharacterOverlay(int width, int height, bool renderAboveHud)
{
    if (!m_gameplayUiController.characterScreen().open
        || m_pIndoorRenderer == nullptr
        || !m_pIndoorRenderer->hasHudRenderResources()
        || width <= 0
        || height <= 0)
    {
        return;
    }

    GameplayOverlayContext overlayContext = createGameplayOverlayContext();
    GameplayPartyOverlayRenderer::renderCharacterOverlay(overlayContext, width, height, renderAboveHud);
}

void IndoorGameView::shutdown()
{
    syncGameplayMouseLookMode(SDL_GetMouseFocus(), false);

    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->setGameplayMouseLookMode(false, false);
    }

    clearHudResources();
    m_pAssetFileSystem = nullptr;
    m_pIndoorRenderer = nullptr;
    m_pIndoorSceneRuntime = nullptr;
    m_pGameAudioSystem = nullptr;
    m_map.reset();
    m_gameplayUiRuntime.clear();
    m_gameplayUiController.clearRuntimeState();
    interactionState().closeOverlayLatch = false;
    interactionState().restClickLatch = false;
    interactionState().restPressedTarget = {};
    interactionState().menuToggleLatch = false;
    interactionState().menuClickLatch = false;
    interactionState().menuPressedTarget = {};
    interactionState().controlsToggleLatch = false;
    interactionState().controlsClickLatch = false;
    interactionState().controlsPressedTarget = {};
    interactionState().controlsSliderDragActive = false;
    interactionState().controlsDraggedSlider = GameplayControlsPointerTargetType::None;
    interactionState().keyboardToggleLatch = false;
    interactionState().keyboardClickLatch = false;
    interactionState().keyboardPressedTarget = {};
    interactionState().videoOptionsToggleLatch = false;
    interactionState().videoOptionsClickLatch = false;
    interactionState().videoOptionsPressedTarget = {};
    interactionState().saveGameToggleLatch = false;
    interactionState().saveGameClickLatch = false;
    interactionState().saveGamePressedTarget = {};
    interactionState().saveGameEditKeyLatches.fill(false);
    interactionState().saveGameEditBackspaceLatch = false;
    interactionState().lastSaveGameSlotClickTicks = 0;
    interactionState().lastSaveGameClickedSlotIndex.reset();
    interactionState().journalToggleLatch = false;
    interactionState().journalClickLatch = false;
    interactionState().journalPressedTarget = {};
    interactionState().journalMapKeyZoomLatch = false;
    interactionState().dialogueClickLatch = false;
    interactionState().dialoguePressedTarget = {};
    interactionState().houseShopClickLatch = false;
    interactionState().houseShopPressedSlotIndex = 0;
    interactionState().chestClickLatch = false;
    interactionState().chestItemClickLatch = false;
    interactionState().chestPressedTarget = {};
    interactionState().inventoryNestedOverlayItemClickLatch = false;
    interactionState().houseBankDigitLatches.fill(false);
    interactionState().houseBankBackspaceLatch = false;
    interactionState().houseBankConfirmLatch = false;
    interactionState().lootChestItemLatch = false;
    interactionState().chestSelectUpLatch = false;
    interactionState().chestSelectDownLatch = false;
    interactionState().eventDialogSelectUpLatch = false;
    interactionState().eventDialogSelectDownLatch = false;
    interactionState().eventDialogAcceptLatch = false;
    interactionState().eventDialogPartySelectLatches.fill(false);
    interactionState().activateInspectLatch = false;
    interactionState().chestSelectionIndex = 0;
    interactionState().spellbookClickLatch = false;
    interactionState().spellbookPressedTarget = {};
    m_partyPortraitClickLatch = false;
    m_partyPortraitPressedIndex = std::nullopt;
    m_lastPartyPortraitClickTicks = 0;
    m_lastPartyPortraitClickedIndex = std::nullopt;
    interactionState().pendingCharacterDismissMemberIndex = std::nullopt;
    interactionState().pendingCharacterDismissExpiresTicks = 0;
    interactionState().characterClickLatch = false;
    interactionState().characterPressedTarget = {};
    m_gameplayHudButtonClickLatch = false;
    m_gameplayHudPressedButton = 0;
    m_gameplayMouseLookActive = false;
    m_gameplayCursorModeActive = false;
    m_gameSession.previousKeyboardState().fill(0);
    m_renderedInspectableHudItems.clear();
    m_hudLayoutRuntimeHeightOverrides.clear();
}

void IndoorGameView::reopenMenuScreen()
{
    createGameplayOverlayContext().openMenuOverlay();
}

IndoorPartyRuntime *IndoorGameView::partyRuntime() const
{
    return m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->partyRuntime() : nullptr;
}

GameplayOverlayContext IndoorGameView::createGameplayOverlayContext()
{
    return GameplayOverlayContext(m_gameSession, m_pGameAudioSystem, &m_settings, *this, *this);
}

GameplayOverlayContext IndoorGameView::createGameplayOverlayContext() const
{
    return GameplayOverlayContext(
        const_cast<GameSession &>(m_gameSession),
        m_pGameAudioSystem,
        const_cast<GameSettings *>(&m_settings),
        const_cast<IndoorGameView &>(*this),
        const_cast<IndoorGameView &>(*this));
}

IGameplayWorldRuntime *IndoorGameView::worldRuntime() const
{
    return m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->worldRuntime() : nullptr;
}

GameAudioSystem *IndoorGameView::audioSystem() const
{
    return m_pGameAudioSystem;
}

const ItemTable *IndoorGameView::itemTable() const
{
    return &m_gameSession.data().itemTable();
}

const StandardItemEnchantTable *IndoorGameView::standardItemEnchantTable() const
{
    return &m_gameSession.data().standardItemEnchantTable();
}

const SpecialItemEnchantTable *IndoorGameView::specialItemEnchantTable() const
{
    return &m_gameSession.data().specialItemEnchantTable();
}

const ClassSkillTable *IndoorGameView::classSkillTable() const
{
    return &m_gameSession.data().classSkillTable();
}

const CharacterDollTable *IndoorGameView::characterDollTable() const
{
    return &m_gameSession.data().characterDollTable();
}

const CharacterInspectTable *IndoorGameView::characterInspectTable() const
{
    return &m_gameSession.data().characterInspectTable();
}

const RosterTable *IndoorGameView::rosterTable() const
{
    return &m_gameSession.data().rosterTable();
}

const ReadableScrollTable *IndoorGameView::readableScrollTable() const
{
    return &m_gameSession.data().readableScrollTable();
}

const ItemEquipPosTable *IndoorGameView::itemEquipPosTable() const
{
    return &m_gameSession.data().itemEquipPosTable();
}

const SpellTable *IndoorGameView::spellTable() const
{
    return &m_gameSession.data().spellTable();
}

const HouseTable *IndoorGameView::houseTable() const
{
    return &m_gameSession.data().houseTable();
}

const ChestTable *IndoorGameView::chestTable() const
{
    return &m_gameSession.data().chestTable();
}

const NpcDialogTable *IndoorGameView::npcDialogTable() const
{
    return &m_gameSession.data().npcDialogTable();
}

const JournalQuestTable *IndoorGameView::journalQuestTable() const
{
    return &m_gameSession.data().journalQuestTable();
}

const JournalHistoryTable *IndoorGameView::journalHistoryTable() const
{
    return &m_gameSession.data().journalHistoryTable();
}

const JournalAutonoteTable *IndoorGameView::journalAutonoteTable() const
{
    return &m_gameSession.data().journalAutonoteTable();
}

const std::string &IndoorGameView::currentMapFileName() const
{
    static const std::string kEmptyMapFileName;
    return m_map ? m_map->fileName : kEmptyMapFileName;
}

float IndoorGameView::gameplayCameraYawRadians() const
{
    return 0.0f;
}

const std::vector<uint8_t> *IndoorGameView::journalMapFullyRevealedCells() const
{
    return nullptr;
}

const std::vector<uint8_t> *IndoorGameView::journalMapPartiallyRevealedCells() const
{
    return nullptr;
}

bool IndoorGameView::trySelectPartyMember(size_t memberIndex, bool requireGameplayReady)
{
    (void)requireGameplayReady;
    IndoorPartyRuntime *pRuntime = partyRuntime();
    return pRuntime != nullptr && pRuntime->party().setActiveMemberIndex(memberIndex);
}

bool IndoorGameView::tryAutoPlaceHeldItemOnPartyMember(size_t memberIndex, bool showFailureStatus)
{
    if (partyRuntime() == nullptr || !m_gameplayUiController.heldInventoryItem().active)
    {
        return false;
    }

    Party &party = partyRuntime()->party();

    if (!party.tryAutoPlaceItemInMemberInventory(memberIndex, m_gameplayUiController.heldInventoryItem().item))
    {
        if (showFailureStatus)
        {
            setStatusBarEvent(party.lastStatus().empty() ? "Inventory full" : party.lastStatus());
        }

        return false;
    }

    m_gameplayUiController.heldInventoryItem() = {};
    return true;
}

bool IndoorGameView::isOpaqueHudPixelAtPoint(const GameplayRenderedInspectableHudItem &item, float x, float y) const
{
    if (item.textureName.empty()
        || item.width <= 0.0f
        || item.height <= 0.0f
        || x < item.x
        || x >= item.x + item.width
        || y < item.y
        || y >= item.y + item.height)
    {
        return false;
    }

    int textureWidth = 0;
    int textureHeight = 0;
    const std::optional<std::vector<uint8_t>> pixels =
        const_cast<IndoorGameView *>(this)->loadHudBitmapPixelsBgraCached(item.textureName, textureWidth, textureHeight);

    if (!pixels.has_value() || textureWidth <= 0 || textureHeight <= 0)
    {
        return true;
    }

    const float normalizedX = std::clamp((x - item.x) / item.width, 0.0f, 0.999999f);
    const float normalizedY = std::clamp((y - item.y) / item.height, 0.0f, 0.999999f);
    const int pixelX = std::clamp(static_cast<int>(normalizedX * textureWidth), 0, textureWidth - 1);
    const int pixelY = std::clamp(static_cast<int>(normalizedY * textureHeight), 0, textureHeight - 1);
    const size_t pixelOffset =
        (static_cast<size_t>(pixelY) * static_cast<size_t>(textureWidth) + static_cast<size_t>(pixelX)) * 4;

    if (pixelOffset + 3 >= pixels->size())
    {
        return false;
    }

    return (*pixels)[pixelOffset + 3] > 0;
}

bool IndoorGameView::activeMemberKnowsSpell(uint32_t spellId) const
{
    const IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime == nullptr)
    {
        return false;
    }

    const Character *pMember = pRuntime->party().activeMember();
    return pMember != nullptr && pMember->knowsSpell(spellId);
}

bool IndoorGameView::activeMemberHasSpellbookSchool(GameplayUiController::SpellbookSchool school) const
{
    const IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime == nullptr)
    {
        return false;
    }

    const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(school);
    const Character *pMember = pRuntime->party().activeMember();

    if (pDefinition == nullptr || pMember == nullptr)
    {
        return false;
    }

    const std::optional<std::string> skillName = resolveMagicSkillName(pDefinition->firstSpellId);

    if (!skillName)
    {
        return false;
    }

    const CharacterSkill *pSkill = pMember->findSkill(*skillName);
    return pSkill != nullptr && pSkill->level > 0 && pSkill->mastery != SkillMastery::None;
}

void IndoorGameView::setStatusBarEvent(const std::string &text, float durationSeconds)
{
    m_gameplayUiController.setStatusBarEvent(text, durationSeconds);
}

void IndoorGameView::executeActiveDialogAction()
{
    EventRuntimeState *pEventRuntimeState =
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    GameplayDialogController::Context context = buildDialogContext(*pEventRuntimeState);
    const GameplayDialogController::Result result = m_gameplayDialogController.executeActiveDialogAction(context);

    if (result.shouldCloseActiveDialog)
    {
        closeActiveEventDialog();
    }

    if (result.shouldOpenPendingEventDialog)
    {
        presentPendingEventDialog(result.previousMessageCount, result.allowNpcFallbackContent);
    }
}


void IndoorGameView::closeInventoryNestedOverlay()
{
    m_gameplayUiController.closeInventoryNestedOverlay();
}

bool IndoorGameView::tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen)
{
    GameplayUiController::HeldInventoryItemState &heldItem = m_gameplayUiController.heldInventoryItem();

    if (!heldItem.active || itemTable() == nullptr || partyRuntime() == nullptr || worldRuntime() == nullptr)
    {
        return false;
    }

    Party &party = partyRuntime()->party();
    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            party,
            memberIndex,
            heldItem.item,
            *itemTable(),
            readableScrollTable());

    if (!useResult.handled)
    {
        return false;
    }

    if (useResult.action == InventoryItemUseAction::CastScroll)
    {
        if (spellTable() == nullptr)
        {
            return false;
        }

        const SpellEntry *pSpellEntry = spellTable()->findById(static_cast<int>(useResult.spellId));

        if (pSpellEntry == nullptr)
        {
            setStatusBarEvent("Unknown scroll spell");
            return true;
        }

        PartySpellCastRequest request = {};
        request.casterMemberIndex = memberIndex;
        request.spellId = useResult.spellId;
        request.skillLevelOverride = useResult.spellSkillLevelOverride;
        request.skillMasteryOverride = useResult.spellSkillMasteryOverride;
        request.spendMana = false;
        request.applyRecovery = true;
        const PartySpellCastResult result =
            PartySpellSystem::castSpell(party, *worldRuntime(), *spellTable(), request);

        if (!result.succeeded())
        {
            setStatusBarEvent(result.statusText.empty() ? "Spell failed" : result.statusText);
            return true;
        }

        if (useResult.consumed)
        {
            heldItem = {};
        }
    }
    else if (useResult.action == InventoryItemUseAction::ReadMessageScroll)
    {
        GameplayUiController::ReadableScrollOverlayState &overlay = m_gameplayUiController.readableScrollOverlay();
        overlay.active = true;
        overlay.title = useResult.readableTitle;
        overlay.body = useResult.readableBody;
    }
    else
    {
        if (useResult.consumed)
        {
            heldItem = {};
        }

        if (useResult.action == InventoryItemUseAction::ConsumePotion
            && useResult.consumed
            && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Drink, GameAudioSystem::PlaybackGroup::Ui);
        }
        else if (useResult.action == InventoryItemUseAction::LearnSpell
                 && !useResult.consumed
                 && useResult.alreadyKnown
                 && m_pGameAudioSystem != nullptr)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Error, GameAudioSystem::PlaybackGroup::Ui);
        }

        if (useResult.speechId.has_value())
        {
            playSpeechReaction(memberIndex, *useResult.speechId, true);
        }
    }

    if (!useResult.statusText.empty())
    {
        setStatusBarEvent(useResult.statusText);
    }

    const bool closeCharacterScreen = !keepCharacterScreenOpen || useResult.action == InventoryItemUseAction::CastScroll;

    if (closeCharacterScreen)
    {
        GameplayUiController::CharacterScreenState &screen = m_gameplayUiController.characterScreen();
        screen.open = false;
        screen.dollJewelryOverlayOpen = false;
    }

    return true;
}

void IndoorGameView::updateReadableScrollOverlayForHeldItem(
    size_t memberIndex,
    const GameplayCharacterPointerTarget &pointerTarget,
    bool isLeftMousePressed)
{
    GameplayUiController::ReadableScrollOverlayState &overlay = m_gameplayUiController.readableScrollOverlay();
    overlay = {};

    if (!isLeftMousePressed
        || !m_gameplayUiController.heldInventoryItem().active
        || itemTable() == nullptr
        || partyRuntime() == nullptr
        || (pointerTarget.type != GameplayCharacterPointerTargetType::EquipmentSlot
            && pointerTarget.type != GameplayCharacterPointerTargetType::DollPanel))
    {
        return;
    }

    const InventoryItemUseAction useAction =
        InventoryItemUseRuntime::classifyItemUse(m_gameplayUiController.heldInventoryItem().item, *itemTable());

    if (useAction != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    Party &party = partyRuntime()->party();
    const InventoryItemUseResult useResult =
        InventoryItemUseRuntime::useItemOnMember(
            party,
            memberIndex,
            m_gameplayUiController.heldInventoryItem().item,
            *itemTable(),
            readableScrollTable());

    if (!useResult.handled || useResult.action != InventoryItemUseAction::ReadMessageScroll)
    {
        return;
    }

    overlay.active = true;
    overlay.title = useResult.readableTitle;
    overlay.body = useResult.readableBody;
}

void IndoorGameView::closeReadableScrollOverlay()
{
    m_gameplayUiController.closeReadableScrollOverlay();
}

void IndoorGameView::playSpeechReaction(size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
{
    (void)memberIndex;
    (void)speechId;
    (void)triggerFaceAnimation;
}

bool IndoorGameView::tryCastSpellFromMember(
    size_t casterMemberIndex,
    uint32_t spellId,
    const std::string &spellName)
{
    if (spellTable() == nullptr || partyRuntime() == nullptr || worldRuntime() == nullptr)
    {
        return false;
    }

    PartySpellCastRequest request = {};
    request.casterMemberIndex = casterMemberIndex;
    request.spellId = spellId;

    Party &party = partyRuntime()->party();
    const PartySpellCastResult result =
        PartySpellSystem::castSpell(party, *worldRuntime(), *spellTable(), request);

    if (!result.succeeded())
    {
        if (result.status == PartySpellCastStatus::NeedActorTarget
            || result.status == PartySpellCastStatus::NeedCharacterTarget
            || result.status == PartySpellCastStatus::NeedActorOrCharacterTarget
            || result.status == PartySpellCastStatus::NeedGroundPoint
            || result.status == PartySpellCastStatus::NeedInventoryItemTarget
            || result.status == PartySpellCastStatus::NeedUtilityUi)
        {
            setStatusBarEvent("Spell targeting is not wired indoors yet");
            return false;
        }

        if (!result.statusText.empty())
        {
            setStatusBarEvent(result.statusText);
        }

        return false;
    }

    if (m_pGameAudioSystem != nullptr)
    {
        const SpellEntry *pSpellEntry = spellTable()->findById(static_cast<int>(spellId));

        if (result.effectKind == PartySpellCastEffectKind::CharacterRestore
            || result.effectKind == PartySpellCastEffectKind::PartyRestore)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Heal, GameAudioSystem::PlaybackGroup::Ui);
        }
        else if (pSpellEntry != nullptr
            && pSpellEntry->effectSoundId > 0
            && result.effectKind != PartySpellCastEffectKind::Projectile
            && result.effectKind != PartySpellCastEffectKind::MultiProjectile)
        {
            m_pGameAudioSystem->playSound(
                static_cast<uint32_t>(pSpellEntry->effectSoundId),
                GameAudioSystem::PlaybackGroup::Ui);
        }
    }

    setStatusBarEvent("Cast " + spellName);
    return true;
}

bool IndoorGameView::tryCastSpellRequest(
    const PartySpellCastRequest &request,
    const std::string &spellName)
{
    if (spellTable() == nullptr || partyRuntime() == nullptr || worldRuntime() == nullptr)
    {
        return false;
    }

    Party &party = partyRuntime()->party();
    const PartySpellCastResult result =
        PartySpellSystem::castSpell(party, *worldRuntime(), *spellTable(), request);

    if (!result.succeeded())
    {
        if (!result.statusText.empty())
        {
            setStatusBarEvent(result.statusText);
        }

        return false;
    }

    if (m_pGameAudioSystem != nullptr)
    {
        const SpellEntry *pSpellEntry = spellTable()->findById(static_cast<int>(request.spellId));

        if (result.effectKind == PartySpellCastEffectKind::CharacterRestore
            || result.effectKind == PartySpellCastEffectKind::PartyRestore)
        {
            m_pGameAudioSystem->playCommonSound(SoundId::Heal, GameAudioSystem::PlaybackGroup::Ui);
        }
        else if (pSpellEntry != nullptr
            && pSpellEntry->effectSoundId > 0
            && result.effectKind != PartySpellCastEffectKind::Projectile
            && result.effectKind != PartySpellCastEffectKind::MultiProjectile)
        {
            m_pGameAudioSystem->playSound(
                static_cast<uint32_t>(pSpellEntry->effectSoundId),
                GameAudioSystem::PlaybackGroup::Ui);
        }
    }

    if (!spellName.empty())
    {
        setStatusBarEvent("Cast " + spellName);
    }

    return true;
}

GameSettings &IndoorGameView::mutableSettings()
{
    return m_settings;
}

std::array<uint8_t, SDL_SCANCODE_COUNT> &IndoorGameView::previousKeyboardState()
{
    return m_gameSession.previousKeyboardState();
}

const std::array<uint8_t, SDL_SCANCODE_COUNT> &IndoorGameView::previousKeyboardState() const
{
    return m_gameSession.previousKeyboardState();
}

bool IndoorGameView::trySaveToSelectedGameSlot()
{
    GameplayUiController::SaveGameScreenState &saveGameScreen = m_gameplayUiController.saveGameScreen();

    if (!saveGameScreen.active
        || saveGameScreen.slots.empty()
        || saveGameScreen.selectedIndex >= saveGameScreen.slots.size()
        || !m_gameSession.canSaveGameToPath())
    {
        return false;
    }

    std::string saveName;

    if (saveGameScreen.editActive)
    {
        saveName = saveGameScreen.editBuffer;
    }
    else
    {
        const GameplayUiController::SaveSlotSummary &slot = saveGameScreen.slots[saveGameScreen.selectedIndex];
        saveName = slot.fileLabel == "Empty" ? std::string() : slot.fileLabel;
    }

    if (saveName.empty())
    {
        saveName = m_map.has_value() ? m_map->name : "Save Game";
    }

    std::string error;
    const bool saved = m_gameSession.saveGameToPath(
        saveGameScreen.slots[saveGameScreen.selectedIndex].path,
        saveName,
        {},
        error);

    if (saved)
    {
        createGameplayOverlayContext().closeSaveGameOverlay();
    }

    return saved;
}

int IndoorGameView::restFoodRequired() const
{
    int foodRequired = 2;
    const IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime == nullptr)
    {
        return foodRequired;
    }

    constexpr uint32_t DragonRaceId = 5;
    const Party &party = pRuntime->party();

    for (const Character &member : party.members())
    {
        if (member.raceId == DragonRaceId)
        {
            ++foodRequired;
            break;
        }
    }

    return std::max(1, foodRequired);
}

const GameSettings &IndoorGameView::settingsSnapshot() const
{
    return m_settings;
}

bool IndoorGameView::isControlsRenderButtonPressed(GameplayControlsRenderButton button) const
{
    if (!interactionState().controlsClickLatch)
    {
        return false;
    }

    switch (button)
    {
    case GameplayControlsRenderButton::TurnRate16:
        return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::TurnRate16Button;
    case GameplayControlsRenderButton::TurnRate32:
        return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::TurnRate32Button;
    case GameplayControlsRenderButton::TurnRateSmooth:
        return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::TurnRateSmoothButton;
    case GameplayControlsRenderButton::WalkSound:
        return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::WalkSoundButton;
    case GameplayControlsRenderButton::ShowHits:
        return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::ShowHitsButton;
    case GameplayControlsRenderButton::AlwaysRun:
        return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::AlwaysRunButton;
    case GameplayControlsRenderButton::FlipOnExit:
        return interactionState().controlsPressedTarget.type == GameplayControlsPointerTargetType::FlipOnExitButton;
    }

    return false;
}

bool IndoorGameView::isVideoOptionsRenderButtonPressed(GameplayVideoOptionsRenderButton button) const
{
    if (!interactionState().videoOptionsClickLatch)
    {
        return false;
    }

    switch (button)
    {
    case GameplayVideoOptionsRenderButton::BloodSplats:
        return interactionState().videoOptionsPressedTarget.type == GameplayVideoOptionsPointerTargetType::BloodSplatsButton;
    case GameplayVideoOptionsRenderButton::ColoredLights:
        return interactionState().videoOptionsPressedTarget.type == GameplayVideoOptionsPointerTargetType::ColoredLightsButton;
    case GameplayVideoOptionsRenderButton::Tinting:
        return interactionState().videoOptionsPressedTarget.type == GameplayVideoOptionsPointerTargetType::TintingButton;
    }

    return false;
}

void IndoorGameView::clearHudLayoutRuntimeHeightOverrides()
{
    m_hudLayoutRuntimeHeightOverrides.clear();
}

void IndoorGameView::setHudLayoutRuntimeHeightOverride(const std::string &layoutId, float height)
{
    m_hudLayoutRuntimeHeightOverrides[layoutId] = height;
}

const HouseEntry *IndoorGameView::findHouseEntry(uint32_t houseId) const
{
    return houseTable() != nullptr ? houseTable()->get(houseId) : nullptr;
}

const UiLayoutManager::LayoutElement *IndoorGameView::findHudLayoutElement(const std::string &layoutId) const
{
    return m_uiLayoutManager.findElement(layoutId);
}

int IndoorGameView::defaultHudLayoutZIndexForScreen(const std::string &screen) const
{
    return UiLayoutManager::defaultZIndexForScreen(screen);
}

GameplayHudScreenState IndoorGameView::currentGameplayHudScreenState() const
{
    if (m_gameplayUiController.eventDialog().content.isActive)
    {
        return GameplayHudScreenState::Dialogue;
    }

    if (m_gameplayUiController.journalScreen().active)
    {
        return GameplayHudScreenState::Journal;
    }

    if (m_gameplayUiController.restScreen().active)
    {
        return GameplayHudScreenState::Rest;
    }

    if (m_gameplayUiController.videoOptionsScreen().active)
    {
        return GameplayHudScreenState::VideoOptions;
    }

    if (m_gameplayUiController.keyboardScreen().active)
    {
        return GameplayHudScreenState::Keyboard;
    }

    if (m_gameplayUiController.controlsScreen().active)
    {
        return GameplayHudScreenState::Controls;
    }

    if (m_gameplayUiController.menuScreen().active)
    {
        return GameplayHudScreenState::Menu;
    }

    if (m_gameplayUiController.saveGameScreen().active)
    {
        return GameplayHudScreenState::SaveGame;
    }

    if (m_gameplayUiController.loadGameScreen().active)
    {
        return GameplayHudScreenState::LoadGame;
    }

    if (m_gameplayUiController.utilitySpellOverlay().active
        && m_gameplayUiController.utilitySpellOverlay().mode == GameplayUiController::UtilitySpellOverlayMode::TownPortal)
    {
        return GameplayHudScreenState::TownPortal;
    }

    if (m_gameplayUiController.utilitySpellOverlay().active
        && m_gameplayUiController.utilitySpellOverlay().mode == GameplayUiController::UtilitySpellOverlayMode::LloydsBeacon)
    {
        return GameplayHudScreenState::LloydsBeacon;
    }

    if (m_gameplayUiController.characterScreen().open)
    {
        return GameplayHudScreenState::Character;
    }

    if (m_gameplayUiController.spellbook().active)
    {
        return GameplayHudScreenState::Spellbook;
    }

    const IGameplayWorldRuntime *pRuntime = worldRuntime();

    if (pRuntime != nullptr
        && (pRuntime->activeChestView() != nullptr || pRuntime->activeCorpseView() != nullptr))
    {
        return GameplayHudScreenState::Chest;
    }

    return GameplayHudScreenState::Gameplay;
}

bool IndoorGameView::shouldEnableGameplayMouseLook() const
{
    return currentGameplayHudScreenState() == GameplayHudScreenState::Gameplay;
}

void IndoorGameView::syncGameplayMouseLookMode(SDL_Window *pWindow, bool enabled)
{
    if (pWindow != nullptr && SDL_GetWindowRelativeMouseMode(pWindow) != enabled)
    {
        if (!enabled)
        {
            int windowWidth = 0;
            int windowHeight = 0;
            SDL_GetWindowSizeInPixels(pWindow, &windowWidth, &windowHeight);

            if (windowWidth > 0 && windowHeight > 0)
            {
                SDL_WarpMouseInWindow(
                    pWindow,
                    static_cast<float>(windowWidth) * 0.5f,
                    static_cast<float>(windowHeight) * 0.5f);
            }
        }

        SDL_SetWindowRelativeMouseMode(pWindow, enabled);
        SDL_GetRelativeMouseState(nullptr, nullptr);
    }

    if (enabled)
    {
        SDL_HideCursor();
    }
    else
    {
        SDL_ShowCursor();
    }
}

void IndoorGameView::updateItemInspectOverlayState(int width, int height)
{
    GameplayUiController::ItemInspectOverlayState &overlay = m_gameplayUiController.itemInspectOverlay();
    overlay = {};

    if (width <= 0
        || height <= 0
        || itemTable() == nullptr
        || m_gameplayUiController.spellbook().active
        || m_gameplayUiController.controlsScreen().active
        || m_gameplayUiController.keyboardScreen().active
        || m_gameplayUiController.menuScreen().active
        || m_gameplayUiController.saveGameScreen().active
        || m_gameplayUiController.loadGameScreen().active)
    {
        return;
    }

    float mouseX = 0.0f;
    float mouseY = 0.0f;
    const SDL_MouseButtonFlags mouseButtons = SDL_GetMouseState(&mouseX, &mouseY);

    if ((mouseButtons & SDL_BUTTON_RMASK) == 0)
    {
        return;
    }

    if (currentGameplayHudScreenState() != m_renderedInspectableHudState)
    {
        return;
    }

    for (auto it = m_renderedInspectableHudItems.rbegin(); it != m_renderedInspectableHudItems.rend(); ++it)
    {
        if (mouseX < it->x
            || mouseX >= it->x + it->width
            || mouseY < it->y
            || mouseY >= it->y + it->height)
        {
            continue;
        }

        overlay.active = true;
        overlay.objectDescriptionId = it->objectDescriptionId;
        overlay.hasItemState = it->hasItemState;
        overlay.itemState = it->itemState;
        overlay.sourceType = it->sourceType;
        overlay.sourceMemberIndex = it->sourceMemberIndex;
        overlay.sourceGridX = it->sourceGridX;
        overlay.sourceGridY = it->sourceGridY;
        overlay.sourceEquipmentSlot = it->equipmentSlot;
        overlay.sourceLootItemIndex = it->sourceLootItemIndex;
        overlay.hasValueOverride = it->hasValueOverride;
        overlay.valueOverride = it->valueOverride;
        overlay.sourceX = it->x;
        overlay.sourceY = it->y;
        overlay.sourceWidth = it->width;
        overlay.sourceHeight = it->height;
        return;
    }
}

std::optional<GameplayResolvedHudLayoutElement> IndoorGameView::resolvePartyPortraitRect(
    int width,
    int height,
    size_t memberIndex) const
{
    const IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime == nullptr || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const GameplayHudScreenState hudScreenState = currentGameplayHudScreenState();
    const bool isLimitedOverlayHud =
        hudScreenState == GameplayHudScreenState::Dialogue
        || hudScreenState == GameplayHudScreenState::Character
        || hudScreenState == GameplayHudScreenState::Chest
        || hudScreenState == GameplayHudScreenState::Spellbook
        || hudScreenState == GameplayHudScreenState::Rest
        || hudScreenState == GameplayHudScreenState::Menu
        || hudScreenState == GameplayHudScreenState::SaveGame
        || hudScreenState == GameplayHudScreenState::LoadGame
        || hudScreenState == GameplayHudScreenState::Journal;
    const bool useGameplayWideHud =
        !isLimitedOverlayHud && m_settings.gameplayUiLayout == GameplayUiLayout::Widescreen;
    const std::string basebarLayoutId = isLimitedOverlayHud
        ? "OutdoorBasebar"
        : (m_settings.gameplayUiLayout == GameplayUiLayout::Standard
            ? "OutdoorStandardBasebar"
            : "OutdoorGameplayBasebar");
    const std::string partyStripLayoutId = isLimitedOverlayHud
        ? "OutdoorPartyStrip"
        : (m_settings.gameplayUiLayout == GameplayUiLayout::Standard
            ? "OutdoorStandardPartyStrip"
            : "OutdoorGameplayPartyStrip");
    const UiLayoutManager::LayoutElement *pBasebarLayout = findHudLayoutElement(basebarLayoutId);
    const UiLayoutManager::LayoutElement *pPartyStripLayout = findHudLayoutElement(partyStripLayoutId);

    if (pBasebarLayout == nullptr || pPartyStripLayout == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<GameplayHudTextureHandle> basebarTexture =
        const_cast<IndoorGameView *>(this)->ensureHudTextureLoaded(pBasebarLayout->primaryAsset);
    const std::optional<GameplayHudTextureHandle> faceMaskTexture =
        const_cast<IndoorGameView *>(this)->ensureHudTextureLoaded(pPartyStripLayout->primaryAsset);

    if (!basebarTexture || !faceMaskTexture)
    {
        return std::nullopt;
    }

    const std::optional<GameplayResolvedHudLayoutElement> resolvedBasebar =
        resolveHudLayoutElement(basebarLayoutId, width, height, basebarTexture->width, basebarTexture->height);
    const std::optional<GameplayResolvedHudLayoutElement> resolvedPartyStrip =
        resolveHudLayoutElement(partyStripLayoutId, width, height, basebarTexture->width, basebarTexture->height);

    if (!resolvedBasebar || !resolvedPartyStrip)
    {
        return std::nullopt;
    }

    const std::vector<Character> &members = pRuntime->party().members();

    if (memberIndex >= members.size())
    {
        return std::nullopt;
    }

    const float portraitWidth = static_cast<float>(faceMaskTexture->width) * resolvedBasebar->scale;
    const float portraitHeight = static_cast<float>(faceMaskTexture->height) * resolvedBasebar->scale;
    float portraitStartX = resolvedPartyStrip->x + resolvedPartyStrip->width * (20.0f / 471.0f);
    float portraitY = resolvedPartyStrip->y + resolvedPartyStrip->height * (23.0f / 92.0f);
    const float portraitDeltaX = resolvedPartyStrip->width * (94.0f / 471.0f);

    if (useGameplayWideHud)
    {
        const float basebarCenterX = resolvedBasebar->x + resolvedBasebar->width * 0.5f;
        const float portraitGroupWidth =
            portraitWidth + static_cast<float>(members.size() - 1) * portraitDeltaX;
        portraitStartX = basebarCenterX - portraitGroupWidth * 0.5f;
        portraitY -= 15.0f * resolvedBasebar->scale;
    }

    return GameplayResolvedHudLayoutElement{
        portraitStartX + static_cast<float>(memberIndex) * portraitDeltaX,
        portraitY,
        portraitWidth,
        portraitHeight,
        resolvedBasebar->scale
    };
}

std::optional<size_t> IndoorGameView::resolvePartyPortraitIndexAtPoint(int width, int height, float x, float y) const
{
    const IndoorPartyRuntime *pRuntime = partyRuntime();

    if (pRuntime == nullptr || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const std::vector<Character> &members = pRuntime->party().members();

    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        const std::optional<GameplayResolvedHudLayoutElement> portraitRect =
            resolvePartyPortraitRect(width, height, memberIndex);

        if (!portraitRect)
        {
            continue;
        }

        if (x >= portraitRect->x
            && x < portraitRect->x + portraitRect->width
            && y >= portraitRect->y
            && y < portraitRect->y + portraitRect->height)
        {
            return memberIndex;
        }
    }

    return std::nullopt;
}

void IndoorGameView::renderGameplayMouseLookOverlay(int width, int height) const
{
    if (!m_gameplayMouseLookActive || m_gameplayCursorModeActive || width <= 0 || height <= 0)
    {
        return;
    }

    float projectionMatrix[16] = {};
    bx::mtxOrtho(
        projectionMatrix,
        0.0f,
        static_cast<float>(width),
        static_cast<float>(height),
        0.0f,
        0.0f,
        1000.0f,
        0.0f,
        bgfx::getCaps()->homogeneousDepth);
    bgfx::setViewRect(HudViewId, 0, 0, static_cast<uint16_t>(width), static_cast<uint16_t>(height));
    bgfx::setViewTransform(HudViewId, nullptr, projectionMatrix);
    bgfx::touch(HudViewId);

    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    const float baseScale = std::min(uiViewport.width / HudReferenceWidth, uiViewport.height / HudReferenceHeight);
    const float overlayScale = std::clamp(baseScale, 0.75f, 2.0f);
    const float centerX = std::round(static_cast<float>(width) * 0.5f);
    const float centerY = std::round(static_cast<float>(height) * 0.5f);
    const float armLength = std::round(3.0f * overlayScale);
    const float armGap = std::round(1.0f * overlayScale);
    const float stroke = std::max(1.0f, std::round(1.0f * overlayScale));
    const uint32_t dotColor = packHudColorAbgr(255, 255, 180);
    const uint32_t shadowColor = 0xc0000000u;
    const std::optional<GameplayHudTextureHandle> dotTexture =
        const_cast<IndoorGameView *>(this)->ensureSolidHudTextureLoaded("__indoor_gameplay_mouse_look_marker__", dotColor);
    const std::optional<GameplayHudTextureHandle> shadowTexture =
        const_cast<IndoorGameView *>(this)->ensureSolidHudTextureLoaded(
            "__indoor_gameplay_mouse_look_marker_shadow__",
            shadowColor);

    if (!dotTexture || !shadowTexture)
    {
        return;
    }

    const auto submitMarkerLayer =
        [this, centerX, centerY, armLength, armGap, stroke](
            const GameplayHudTextureHandle &texture,
            float offsetX,
            float offsetY)
        {
            submitHudTexturedQuad(
                texture,
                centerX - stroke * 0.5f + offsetX,
                centerY - stroke * 0.5f - armLength - armGap + offsetY,
                stroke,
                armLength);
            submitHudTexturedQuad(
                texture,
                centerX - stroke * 0.5f + offsetX,
                centerY + armGap + offsetY,
                stroke,
                armLength);
            submitHudTexturedQuad(
                texture,
                centerX - stroke * 0.5f - armLength - armGap + offsetX,
                centerY - stroke * 0.5f + offsetY,
                armLength,
                stroke);
            submitHudTexturedQuad(
                texture,
                centerX + armGap + offsetX,
                centerY - stroke * 0.5f + offsetY,
                armLength,
                stroke);
            submitHudTexturedQuad(
                texture,
                centerX - stroke * 0.5f + offsetX,
                centerY - stroke * 0.5f + offsetY,
                stroke,
                stroke);
        };

    submitMarkerLayer(*shadowTexture, 1.0f, 1.0f);
    submitMarkerLayer(*dotTexture, 0.0f, 0.0f);
}

std::vector<std::string> IndoorGameView::sortedHudLayoutIdsForScreen(const std::string &screen) const
{
    return m_uiLayoutManager.sortedLayoutIdsForScreen(screen);
}

std::optional<GameplayResolvedHudLayoutElement> IndoorGameView::resolveHudLayoutElement(
    const std::string &layoutId,
    int screenWidth,
    int screenHeight,
    float fallbackWidth,
    float fallbackHeight) const
{
    return GameplayHudCommon::resolveHudLayoutElement(
        m_uiLayoutManager,
        m_hudLayoutRuntimeHeightOverrides,
        layoutId,
        screenWidth,
        screenHeight,
        fallbackWidth,
        fallbackHeight);
}

std::optional<GameplayResolvedHudLayoutElement> IndoorGameView::resolveGameplayChestGridArea(int width, int height) const
{
    const IGameplayWorldRuntime *pRuntime = worldRuntime();

    if (pRuntime == nullptr || chestTable() == nullptr || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const GameplayChestViewState *pChestView = pRuntime->activeChestView();

    if (pChestView == nullptr)
    {
        return std::nullopt;
    }

    const ChestEntry *pChestEntry = chestTable()->get(pChestView->chestTypeId);
    const UiLayoutManager::LayoutElement *pChestBackgroundLayout = findHudLayoutElement("ChestBackground");

    if (pChestEntry == nullptr
        || pChestBackgroundLayout == nullptr
        || pChestView->gridWidth == 0
        || pChestView->gridHeight == 0)
    {
        return std::nullopt;
    }

    const std::optional<GameplayResolvedHudLayoutElement> resolvedBackground = resolveHudLayoutElement(
        "ChestBackground",
        width,
        height,
        pChestBackgroundLayout->width,
        pChestBackgroundLayout->height);

    if (!resolvedBackground)
    {
        return std::nullopt;
    }

    GameplayResolvedHudLayoutElement resolved = {};
    resolved.x = std::round(
        resolvedBackground->x + static_cast<float>(pChestEntry->gridOffsetX) * resolvedBackground->scale);
    resolved.y = std::round(
        resolvedBackground->y + static_cast<float>(pChestEntry->gridOffsetY) * resolvedBackground->scale);
    resolved.width = 32.0f * static_cast<float>(pChestView->gridWidth) * resolvedBackground->scale;
    resolved.height = 32.0f * static_cast<float>(pChestView->gridHeight) * resolvedBackground->scale;
    resolved.scale = resolvedBackground->scale;
    return resolved;
}

std::optional<GameplayResolvedHudLayoutElement> IndoorGameView::resolveGameplayInventoryNestedOverlayGridArea(
    int width,
    int height) const
{
    if (!m_gameplayUiController.inventoryNestedOverlay().active || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const UiLayoutManager::LayoutElement *pGridLayout = findHudLayoutElement("ChestNestedInventoryGrid");

    if (pGridLayout == nullptr)
    {
        return std::nullopt;
    }

    return resolveHudLayoutElement(
        "ChestNestedInventoryGrid",
        width,
        height,
        pGridLayout->width,
        pGridLayout->height);
}

std::optional<GameplayResolvedHudLayoutElement> IndoorGameView::resolveGameplayHouseShopOverlayFrame(
    int width,
    int height) const
{
    if (!m_gameplayUiController.houseShopOverlay().active || width <= 0 || height <= 0)
    {
        return std::nullopt;
    }

    const UiLayoutManager::LayoutElement *pFrameLayout = findHudLayoutElement("DialogueShopOverlayFrame");

    if (pFrameLayout == nullptr)
    {
        return std::nullopt;
    }

    return resolveHudLayoutElement(
        "DialogueShopOverlayFrame",
        width,
        height,
        pFrameLayout->width,
        pFrameLayout->height);
}

bool IndoorGameView::isPointerInsideResolvedElement(
    const GameplayResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY) const
{
    return GameplayHudCommon::isPointerInsideResolvedElement(resolved, pointerX, pointerY);
}

std::optional<std::string> IndoorGameView::resolveInteractiveAssetName(
    const UiLayoutManager::LayoutElement &layout,
    const GameplayResolvedHudLayoutElement &resolved,
    float pointerX,
    float pointerY,
    bool isLeftMousePressed) const
{
    const std::string *pAssetName =
        GameplayHudCommon::resolveInteractiveAssetName(layout, resolved, pointerX, pointerY, isLeftMousePressed);
    return pAssetName != nullptr ? std::optional<std::string>(*pAssetName) : std::nullopt;
}

std::optional<GameplayHudTextureHandle> IndoorGameView::ensureHudTextureLoaded(const std::string &textureName)
{
    if (textureName.empty())
    {
        return std::nullopt;
    }

    if (!loadHudTexture(textureName))
    {
        return std::nullopt;
    }

    const HudTextureHandleInternal *pTexture =
        GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);

    if (pTexture == nullptr)
    {
        return std::nullopt;
    }

    GameplayHudTextureHandle result = {};
    result.textureName = pTexture->textureName;
    result.width = pTexture->width;
    result.height = pTexture->height;
    result.textureHandle = pTexture->textureHandle;
    return result;
}

std::optional<GameplayHudTextureHandle> IndoorGameView::ensureSolidHudTextureLoaded(
    const std::string &textureName,
    uint32_t abgrColor)
{
    if (textureName.empty())
    {
        return std::nullopt;
    }

    const std::string cacheTextureName =
        toLowerCopy(textureName)
        + "_"
        + std::to_string((abgrColor >> 24) & 0xffu)
        + "_"
        + std::to_string((abgrColor >> 16) & 0xffu)
        + "_"
        + std::to_string((abgrColor >> 8) & 0xffu)
        + "_"
        + std::to_string(abgrColor & 0xffu);
    const auto existingIterator = m_hudTextureIndexByName.find(cacheTextureName);

    if (existingIterator != m_hudTextureIndexByName.end() && existingIterator->second < m_hudTextureHandles.size())
    {
        const HudTextureHandleInternal &existing = m_hudTextureHandles[existingIterator->second];
        GameplayHudTextureHandle result = {};
        result.textureName = existing.textureName;
        result.width = existing.width;
        result.height = existing.height;
        result.textureHandle = existing.textureHandle;
        return result;
    }

    const std::array<uint8_t, 4> pixel = {
        static_cast<uint8_t>((abgrColor >> 16) & 0xff),
        static_cast<uint8_t>((abgrColor >> 8) & 0xff),
        static_cast<uint8_t>(abgrColor & 0xff),
        static_cast<uint8_t>((abgrColor >> 24) & 0xff)
    };

    HudTextureHandleInternal textureHandle = {};
    textureHandle.textureName = cacheTextureName;
    textureHandle.width = 1;
    textureHandle.height = 1;
    textureHandle.physicalWidth = 1;
    textureHandle.physicalHeight = 1;
    textureHandle.bgraPixels.assign(pixel.begin(), pixel.end());
    textureHandle.textureHandle = createBgraTexture2D(
        1,
        1,
        pixel.data(),
        static_cast<uint32_t>(pixel.size()),
        TextureFilterProfile::Ui,
        BGFX_SAMPLER_U_CLAMP | BGFX_SAMPLER_V_CLAMP);

    if (!bgfx::isValid(textureHandle.textureHandle))
    {
        return std::nullopt;
    }

    const size_t index = m_hudTextureHandles.size();
    m_hudTextureHandles.push_back(std::move(textureHandle));
    m_hudTextureIndexByName[m_hudTextureHandles.back().textureName] = index;

    GameplayHudTextureHandle result = {};
    result.textureName = m_hudTextureHandles.back().textureName;
    result.width = m_hudTextureHandles.back().width;
    result.height = m_hudTextureHandles.back().height;
    result.textureHandle = m_hudTextureHandles.back().textureHandle;
    return result;
}

std::optional<GameplayHudTextureHandle> IndoorGameView::ensureDynamicHudTexture(
    const std::string &textureName,
    int width,
    int height,
    const std::vector<uint8_t> &bgraPixels)
{
    return GameplayHudCommon::ensureDynamicHudTexture(
        textureName,
        width,
        height,
        bgraPixels,
        m_hudTextureHandles,
        m_hudTextureIndexByName);
}

const std::vector<uint8_t> *IndoorGameView::hudTexturePixels(
    const std::string &textureName,
    int &width,
    int &height)
{
    const std::optional<GameplayHudTextureHandle> texture = ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        width = 0;
        height = 0;
        return nullptr;
    }

    const auto textureIt = m_hudTextureIndexByName.find(textureName);

    if (textureIt == m_hudTextureIndexByName.end() || textureIt->second >= m_hudTextureHandles.size())
    {
        width = 0;
        height = 0;
        return nullptr;
    }

    const HudTextureHandleInternal &sourceTexture = m_hudTextureHandles[textureIt->second];
    width = sourceTexture.width;
    height = sourceTexture.height;
    return &sourceTexture.bgraPixels;
}

bool IndoorGameView::ensureHudTextureDimensions(const std::string &textureName, int &width, int &height)
{
    const std::optional<GameplayHudTextureHandle> texture = ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        width = 0;
        height = 0;
        return false;
    }

    width = texture->width;
    height = texture->height;
    return true;
}

bool IndoorGameView::tryGetOpaqueHudTextureBounds(
    const std::string &textureName,
    int &width,
    int &height,
    int &opaqueMinX,
    int &opaqueMinY,
    int &opaqueMaxX,
    int &opaqueMaxY)
{
    const std::optional<GameplayHudTextureHandle> texture = ensureHudTextureLoaded(textureName);

    if (!texture)
    {
        width = 0;
        height = 0;
        opaqueMinX = -1;
        opaqueMinY = -1;
        opaqueMaxX = -1;
        opaqueMaxY = -1;
        return false;
    }

    const HudTextureHandleInternal *pTexture =
        GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, textureName);

    if (pTexture == nullptr)
    {
        return false;
    }

    const Engine::AssetScaleTier assetScaleTier =
        m_pAssetFileSystem != nullptr ? m_pAssetFileSystem->getAssetScaleTier() : Engine::AssetScaleTier::X1;
    return GameplayHudCommon::tryGetOpaqueHudTextureBounds(
        *pTexture,
        assetScaleTier,
        width,
        height,
        opaqueMinX,
        opaqueMinY,
        opaqueMaxX,
        opaqueMaxY);
}

void IndoorGameView::submitHudTexturedQuad(
    const GameplayHudTextureHandle &texture,
    float x,
    float y,
    float quadWidth,
    float quadHeight) const
{
    if (m_pIndoorRenderer == nullptr)
    {
        return;
    }

    m_pIndoorRenderer->submitHudTextureQuad(
        texture.textureHandle,
        x,
        y,
        quadWidth,
        quadHeight,
        0.0f,
        0.0f,
        1.0f,
        1.0f,
        TextureFilterProfile::Ui);
}

bgfx::TextureHandle IndoorGameView::ensureHudTextureColor(
    const GameplayHudTextureHandle &texture,
    uint32_t colorAbgr) const
{
    const HudTextureHandleInternal *pTexture =
        GameplayHudCommon::findHudTexture(m_hudTextureHandles, m_hudTextureIndexByName, texture.textureName);
    if (pTexture == nullptr)
    {
        bgfx::TextureHandle invalidHandle = BGFX_INVALID_HANDLE;
        return invalidHandle;
    }

    return GameplayHudCommon::ensureHudTextureColor(*pTexture, colorAbgr, m_hudTextureColorTextureHandles);
}

void IndoorGameView::renderLayoutLabel(
    const UiLayoutManager::LayoutElement &layout,
    const GameplayResolvedHudLayoutElement &resolved,
    const std::string &label) const
{
    GameplayHudCommon::renderLayoutLabel(
        layout,
        resolved,
        label,
        [this](const std::string &fontName) -> const GameplayHudFontData *
        {
            IndoorGameView *pMutableView = const_cast<IndoorGameView *>(this);

            if (!pMutableView->loadHudFont(fontName))
            {
                return nullptr;
            }

            return GameplayHudCommon::findHudFont(m_hudFontHandles, fontName);
        },
        [this](const GameplayHudFontData &font, uint32_t colorAbgr) -> bgfx::TextureHandle
        {
            return GameplayHudCommon::ensureHudFontMainTextureColor(font, colorAbgr, m_hudFontColorTextureHandles);
        },
        [this](const GameplayHudFontData &font,
               bgfx::TextureHandle textureHandle,
               const std::string &text,
               float textX,
               float textY,
               float fontScale)
        {
            GameplayHudFontHandle gameplayFont = {};
            gameplayFont.fontName = font.fontName;
            gameplayFont.fontHeight = font.fontHeight;
            gameplayFont.mainTextureHandle = font.mainTextureHandle;
            gameplayFont.shadowTextureHandle = font.shadowTextureHandle;
            renderHudFontLayer(gameplayFont, textureHandle, text, textX, textY, fontScale);
        });
}

std::optional<GameplayHudFontHandle> IndoorGameView::findHudFont(const std::string &fontName) const
{
    if (fontName.empty())
    {
        return std::nullopt;
    }

    IndoorGameView *pMutableView = const_cast<IndoorGameView *>(this);

    if (!pMutableView->loadHudFont(fontName))
    {
        return std::nullopt;
    }

    const HudFontHandleInternal *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, fontName);

    if (pFont == nullptr)
    {
        return std::nullopt;
    }

    GameplayHudFontHandle result = {};
    result.fontName = pFont->fontName;
    result.fontHeight = pFont->fontHeight;
    result.mainTextureHandle = pFont->mainTextureHandle;
    result.shadowTextureHandle = pFont->shadowTextureHandle;
    return result;
}

float IndoorGameView::measureHudTextWidth(const GameplayHudFontHandle &font, const std::string &text) const
{
    const HudFontHandleInternal *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, font.fontName);
    return pFont != nullptr ? GameplayHudCommon::measureHudTextWidth(*pFont, text) : 0.0f;
}

std::vector<std::string> IndoorGameView::wrapHudTextToWidth(
    const GameplayHudFontHandle &font,
    const std::string &text,
    float maxWidth) const
{
    const HudFontHandleInternal *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, font.fontName);
    return pFont != nullptr ? GameplayHudCommon::wrapHudTextToWidth(*pFont, text, maxWidth)
                            : std::vector<std::string>{text};
}

bgfx::TextureHandle IndoorGameView::ensureHudFontMainTextureColor(
    const GameplayHudFontHandle &font,
    uint32_t colorAbgr) const
{
    const HudFontHandleInternal *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, font.fontName);
    if (pFont == nullptr)
    {
        bgfx::TextureHandle invalidHandle = BGFX_INVALID_HANDLE;
        return invalidHandle;
    }

    return GameplayHudCommon::ensureHudFontMainTextureColor(*pFont, colorAbgr, m_hudFontColorTextureHandles);
}

void IndoorGameView::renderHudFontLayer(
    const GameplayHudFontHandle &font,
    bgfx::TextureHandle textureHandle,
    const std::string &text,
    float textX,
    float textY,
    float fontScale) const
{
    if (m_pIndoorRenderer == nullptr)
    {
        return;
    }

    const HudFontHandleInternal *pFont = GameplayHudCommon::findHudFont(m_hudFontHandles, font.fontName);

    if (pFont == nullptr)
    {
        return;
    }

    GameplayHudCommon::renderHudFontLayer(
        *pFont,
        textureHandle,
        text,
        textX,
        textY,
        fontScale,
        [this](bgfx::TextureHandle submittedTextureHandle,
               float x,
               float y,
               float quadWidth,
               float quadHeight,
               float u0,
               float v0,
               float u1,
               float v1,
               TextureFilterProfile filterProfile)
        {
            m_pIndoorRenderer->submitHudTextureQuad(
                submittedTextureHandle,
                x,
                y,
                quadWidth,
                quadHeight,
                u0,
                v0,
                u1,
                v1,
                filterProfile);
        });
}

bool IndoorGameView::hasHudRenderResources() const
{
    return m_pIndoorRenderer != nullptr && m_pIndoorRenderer->hasHudRenderResources();
}

void IndoorGameView::prepareHudView(int width, int height) const
{
    if (m_pIndoorRenderer != nullptr)
    {
        m_pIndoorRenderer->prepareHudView(width, height);
    }
}

void IndoorGameView::submitHudQuadBatch(
    const std::vector<GameplayHudBatchQuad> &quads,
    int screenWidth,
    int screenHeight) const
{
    (void)screenWidth;
    (void)screenHeight;

    if (m_pIndoorRenderer == nullptr)
    {
        return;
    }

    for (const GameplayHudBatchQuad &quad : quads)
    {
        m_pIndoorRenderer->submitHudTextureQuad(
            quad.textureHandle,
            quad.x,
            quad.y,
            quad.width,
            quad.height,
            quad.u0,
            quad.v0,
            quad.u1,
            quad.v1,
            TextureFilterProfile::Ui);
    }
}

std::string IndoorGameView::resolvePortraitTextureName(const Character &character) const
{
    if (character.portraitState == PortraitId::Eradicated)
    {
        return "ERADCATE";
    }

    if (character.portraitState == PortraitId::Dead)
    {
        return "DEAD";
    }

    return character.portraitTextureName;
}

void IndoorGameView::consumePendingPortraitEventFxRequests()
{
}

void IndoorGameView::renderPortraitFx(
    size_t memberIndex,
    float portraitX,
    float portraitY,
    float portraitWidth,
    float portraitHeight) const
{
    (void)memberIndex;
    (void)portraitX;
    (void)portraitY;
    (void)portraitWidth;
    (void)portraitHeight;
}

bool IndoorGameView::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    state = {};
    return false;
}

void IndoorGameView::collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const
{
    markers.clear();
}

void IndoorGameView::addRenderedInspectableHudItem(const GameplayRenderedInspectableHudItem &item)
{
    m_renderedInspectableHudItems.push_back(item);
}

const std::vector<GameplayRenderedInspectableHudItem> &IndoorGameView::renderedInspectableHudItems() const
{
    return m_renderedInspectableHudItems;
}

void IndoorGameView::submitWorldTextureQuad(
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    float u0,
    float v0,
    float u1,
    float v1) const
{
    if (m_pIndoorRenderer == nullptr)
    {
        return;
    }

    m_pIndoorRenderer->submitHudTextureQuad(
        textureHandle,
        x,
        y,
        quadWidth,
        quadHeight,
        u0,
        v0,
        u1,
        v1,
        TextureFilterProfile::Ui);
}

bool IndoorGameView::renderHouseVideoFrame(float x, float y, float quadWidth, float quadHeight) const
{
    (void)x;
    (void)y;
    (void)quadWidth;
    (void)quadHeight;
    return false;
}

void IndoorGameView::renderDialogueOverlay(int width, int height, bool renderAboveHud)
{
    if (currentGameplayHudScreenState() != GameplayHudScreenState::Dialogue
        || !activeEventDialog().isActive
        || m_pIndoorRenderer == nullptr
        || !m_pIndoorRenderer->hasHudRenderResources()
        || width <= 0
        || height <= 0)
    {
        return;
    }

    m_hudLayoutRuntimeHeightOverrides.clear();
    float dialogMouseX = 0.0f;
    float dialogMouseY = 0.0f;
    SDL_GetMouseState(&dialogMouseX, &dialogMouseY);
    const UiViewportRect uiViewport = computeUiViewportRect(width, height);
    GameplayOverlayContext overlayContext = createGameplayOverlayContext();

    if (!renderAboveHud && uiViewport.x > 0.5f)
    {
        GameplayDialogueRenderer::renderBlackoutBackdrop(overlayContext, width, height, uiViewport.x, uiViewport.width);
    }

    const bool residentSelectionMode = isResidentSelectionMode(activeEventDialog());
    const EventRuntimeState *pEventRuntimeState =
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr;
    const HouseEntry *pHostHouseEntry =
        (currentDialogueHostHouseId(pEventRuntimeState) != 0 && houseTable() != nullptr)
        ? houseTable()->get(currentDialogueHostHouseId(pEventRuntimeState))
        : nullptr;
    const bool showDialogueVideoArea = pHostHouseEntry != nullptr;
    const bool hasDialogueParticipantIdentity =
        !activeEventDialog().title.empty()
        || activeEventDialog().participantPictureId != 0
        || activeEventDialog().sourceId != 0;
    const bool showEventDialogPanel =
        residentSelectionMode
        || !activeEventDialog().actions.empty()
        || pHostHouseEntry != nullptr
        || hasDialogueParticipantIdentity;
    const std::vector<std::string> &dialogueBodyLines = activeEventDialog().lines;
    const bool showDialogueTextFrame = !dialogueBodyLines.empty();
    std::optional<std::string> hoveredHouseServiceTopicText;
    const bool suppressServiceTopicsForShopOverlay =
        (m_gameplayUiController.houseShopOverlay().active
         && (m_gameplayUiController.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuyStandard
             || m_gameplayUiController.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpecial
             || m_gameplayUiController.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks))
        || (m_gameplayUiController.inventoryNestedOverlay().active
            && (m_gameplayUiController.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
                || m_gameplayUiController.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
                || m_gameplayUiController.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair));
    const Party *pParty = partyRuntime() != nullptr ? &partyRuntime()->party() : nullptr;

    GameplayDialogueRenderer::updateHouseShopHoverTopicText(
        overlayContext,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        hoveredHouseServiceTopicText);

    const UiLayoutManager::LayoutElement *pDialogueFrameLayout = findHudLayoutElement("DialogueFrame");
    const UiLayoutManager::LayoutElement *pDialogueTextLayout = findHudLayoutElement("DialogueText");
    const UiLayoutManager::LayoutElement *pBasebarLayout = findHudLayoutElement("OutdoorBasebar");

    if (showDialogueTextFrame
        && pDialogueFrameLayout != nullptr
        && pDialogueTextLayout != nullptr
        && pBasebarLayout != nullptr
        && toLowerCopy(pDialogueFrameLayout->screen) == "dialogue"
        && toLowerCopy(pDialogueTextLayout->screen) == "dialogue")
    {
        const std::optional<GameplayHudFontHandle> font = findHudFont(pDialogueTextLayout->fontName);

        if (font)
        {
            constexpr float DialogueTextTopInset = 2.0f;
            constexpr float DialogueTextBottomInset = 5.0f;
            constexpr float DialogueTextRightInset = 6.0f;
            const float lineHeight = static_cast<float>(font->fontHeight);
            const float textPadY = std::abs(pDialogueTextLayout->textPadY);
            const float textWrapWidth = std::max(
                0.0f,
                pDialogueTextLayout->width
                    - std::abs(pDialogueTextLayout->textPadX) * 2.0f
                    - DialogueTextRightInset);
            size_t wrappedLineCount = 0;

            for (const std::string &line : dialogueBodyLines)
            {
                const std::vector<std::string> wrappedLines = wrapHudTextToWidth(*font, line, textWrapWidth);
                wrappedLineCount += std::max<size_t>(1, wrappedLines.size());
            }

            const float rawComputedTextHeight =
                static_cast<float>(wrappedLineCount) * lineHeight
                + textPadY * 2.0f
                + DialogueTextTopInset
                + DialogueTextBottomInset;
            const float authoritativeFrameHeight = pBasebarLayout->height + rawComputedTextHeight;
            m_hudLayoutRuntimeHeightOverrides[toLowerCopy("DialogueFrame")] = authoritativeFrameHeight;
            m_hudLayoutRuntimeHeightOverrides[toLowerCopy("DialogueText")] = rawComputedTextHeight;
        }
    }

    std::string dialogueResponseHintText =
        activeEventDialog().actions.empty()
            ? "Enter/Space/E/Esc close"
            : "Up/Down select  Enter/Space accept  E/Esc close";

    if (m_gameplayUiController.houseBankState().inputActive())
    {
        dialogueResponseHintText = "Type amount  Enter accept  E/Esc cancel";
    }

    if (statusBarEventRemainingSeconds() > 0.0f && !statusBarEventText().empty())
    {
        dialogueResponseHintText = statusBarEventText();
    }

    if (m_gameplayUiController.inventoryNestedOverlay().active
        && (m_gameplayUiController.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
            || m_gameplayUiController.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
            || m_gameplayUiController.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair))
    {
        if (statusBarEventRemainingSeconds() <= 0.0f || statusBarEventText().empty())
        {
            if (m_gameplayUiController.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell)
            {
                dialogueResponseHintText = "Select the Item to Sell";
            }
            else if (m_gameplayUiController.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify)
            {
                dialogueResponseHintText = "Select the Item to Identify";
            }
            else if (m_gameplayUiController.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
            {
                dialogueResponseHintText = "Select the Item to Repair";
            }
        }
    }

    const std::vector<std::string> orderedDialogueLayoutIds = sortedHudLayoutIdsForScreen("Dialogue");

    for (const std::string &layoutId : orderedDialogueLayoutIds)
    {
        const UiLayoutManager::LayoutElement *pLayout = findHudLayoutElement(layoutId);

        if (pLayout == nullptr || toLowerCopy(pLayout->screen) != "dialogue")
        {
            continue;
        }

        GameplayDialogueRenderer::renderDialogueTextureElement(
            overlayContext,
            layoutId,
            width,
            height,
            dialogMouseX,
            dialogMouseY,
            showDialogueTextFrame,
            showDialogueVideoArea,
            showEventDialogPanel,
            renderAboveHud);
    }

    GameplayDialogueRenderer::renderHouseShopOverlay(
        overlayContext,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        dialogueResponseHintText,
        renderAboveHud);

    GameplayDialogueRenderer::renderDialogueLabelById(
        overlayContext,
        "DialogueGoodbyeButton",
        (activeEventDialog().presentation == EventDialogPresentation::Transition
            && activeEventDialog().actions.size() > 1)
            ? activeEventDialog().actions[1].label
            : "Close",
        width,
        height,
        renderAboveHud);

    if (activeEventDialog().presentation == EventDialogPresentation::Transition
        && !activeEventDialog().actions.empty())
    {
        GameplayDialogueRenderer::renderDialogueLabelById(
            overlayContext,
            "DialogueOkButton",
            activeEventDialog().actions[0].label,
            width,
            height,
            renderAboveHud);
    }

    GameplayDialogueRenderer::renderDialogueLabelById(
        overlayContext,
        "DialogueGoldLabel",
        pParty != nullptr ? std::to_string(pParty->gold()) : "",
        width,
        height,
        renderAboveHud);
    GameplayDialogueRenderer::renderDialogueLabelById(
        overlayContext,
        "DialogueFoodLabel",
        pParty != nullptr ? std::to_string(pParty->food()) : "",
        width,
        height,
        renderAboveHud);
    GameplayDialogueRenderer::renderDialogueLabelById(
        overlayContext,
        "DialogueResponseHint",
        dialogueResponseHintText,
        width,
        height,
        renderAboveHud);
    GameplayDialogueRenderer::renderDialogueEventPanel(
        overlayContext,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        renderAboveHud,
        showEventDialogPanel,
        residentSelectionMode,
        pHostHouseEntry,
        hoveredHouseServiceTopicText,
        suppressServiceTopicsForShopOverlay);
    GameplayDialogueRenderer::renderDialogueBodyText(
        overlayContext,
        width,
        height,
        renderAboveHud,
        dialogueBodyLines);

    m_hudLayoutRuntimeHeightOverrides.clear();
}

std::optional<std::string> IndoorGameView::findCachedAssetPath(
    const std::string &directoryPath,
    const std::string &fileName) const
{
    return GameplayHudCommon::findCachedAssetPath(
        m_pAssetFileSystem,
        m_hudAssetLoadCache,
        directoryPath,
        fileName);
}

std::optional<std::vector<uint8_t>> IndoorGameView::readCachedBinaryFile(const std::string &assetPath) const
{
    return GameplayHudCommon::readCachedBinaryFile(
        m_pAssetFileSystem,
        m_hudAssetLoadCache,
        assetPath);
}

std::optional<std::vector<uint8_t>> IndoorGameView::loadHudBitmapPixelsBgraCached(
    const std::string &textureName,
    int &width,
    int &height) const
{
    return GameplayHudCommon::loadHudBitmapPixelsBgraCached(
        m_pAssetFileSystem,
        m_hudAssetLoadCache,
        textureName,
        width,
        height);
}

bool IndoorGameView::loadHudTexture(const std::string &textureName)
{
    return GameplayHudCommon::loadHudTexture(
        m_pAssetFileSystem,
        m_hudAssetLoadCache,
        textureName,
        m_hudTextureHandles,
        m_hudTextureIndexByName);
}

bool IndoorGameView::loadHudFont(const std::string &fontName)
{
    return GameplayHudCommon::loadHudFont(
        m_pAssetFileSystem,
        m_hudAssetLoadCache,
        fontName,
        m_hudFontHandles);
}

void IndoorGameView::clearHudResources()
{
    for (HudTextureHandleInternal &textureHandle : m_hudTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    for (HudFontHandleInternal &fontHandle : m_hudFontHandles)
    {
        if (bgfx::isValid(fontHandle.mainTextureHandle))
        {
            bgfx::destroy(fontHandle.mainTextureHandle);
            fontHandle.mainTextureHandle = BGFX_INVALID_HANDLE;
        }

        if (bgfx::isValid(fontHandle.shadowTextureHandle))
        {
            bgfx::destroy(fontHandle.shadowTextureHandle);
            fontHandle.shadowTextureHandle = BGFX_INVALID_HANDLE;
        }
    }

    for (HudFontColorTextureHandleInternal &textureHandle : m_hudFontColorTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    for (HudTextureColorTextureHandleInternal &textureHandle : m_hudTextureColorTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }

    m_hudTextureHandles.clear();
    m_hudTextureIndexByName.clear();
    m_hudFontHandles.clear();
    m_hudFontColorTextureHandles.clear();
    m_hudTextureColorTextureHandles.clear();
    m_hudAssetLoadCache = {};
}

GameplayDialogController::Context IndoorGameView::buildDialogContext(EventRuntimeState &eventRuntimeState)
{
    GameplayDialogController::Callbacks callbacks = {};
    callbacks.playSpeechReaction =
        [this](size_t memberIndex, SpeechId speechId, bool triggerFaceAnimation)
        {
            playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
        };
    callbacks.playHouseSound =
        [this](uint32_t soundId)
        {
            if (m_pGameAudioSystem != nullptr)
            {
                m_pGameAudioSystem->playSound(soundId, GameAudioSystem::PlaybackGroup::HouseSpeech);
            }
        };
    callbacks.playCommonSound =
        [this](SoundId soundId)
        {
            if (m_pGameAudioSystem != nullptr)
            {
                m_pGameAudioSystem->playCommonSound(soundId, GameAudioSystem::PlaybackGroup::Ui);
            }
        };

    Party *pParty = partyRuntime() != nullptr ? &partyRuntime()->party() : nullptr;

    return buildGameplayDialogContext(
        m_gameplayUiController,
        eventRuntimeState,
        activeEventDialog(),
        eventDialogSelectionIndex(),
        pParty,
        worldRuntime(),
        m_pIndoorSceneRuntime != nullptr ? &m_pIndoorSceneRuntime->globalEventProgram() : nullptr,
        houseTable(),
        classSkillTable(),
        npcDialogTable(),
        m_map ? &*m_map : nullptr,
        &m_gameSession.data().mapEntries(),
        rosterTable(),
        &m_gameSession.data().arcomageLibrary(),
        currentGameplayHudScreenState() == GameplayHudScreenState::Dialogue,
        std::move(callbacks));
}

void IndoorGameView::presentPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent)
{
    GameplayDialogUiFlowState state = {
        m_gameplayUiController,
        interactionState(),
        m_gameplayDialogController,
        eventDialogSelectionIndex()
    };
    ::OpenYAMM::Game::presentPendingEventDialog(
        state,
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr,
        [this](EventRuntimeState &eventRuntimeState)
        {
            return buildDialogContext(eventRuntimeState);
        },
        previousMessageCount,
        allowNpcFallbackContent);
}

void IndoorGameView::closeActiveEventDialog()
{
    GameplayDialogUiFlowState state = {
        m_gameplayUiController,
        interactionState(),
        m_gameplayDialogController,
        eventDialogSelectionIndex()
    };
    ::OpenYAMM::Game::closeActiveEventDialog(
        state,
        m_pIndoorSceneRuntime != nullptr ? m_pIndoorSceneRuntime->eventRuntimeState() : nullptr);
}
} // namespace OpenYAMM::Game
